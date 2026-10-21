"""Jimeng-specific durable paid evidence and UNKNOWN recovery transactions."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ai_video.production.models import (
    PaidProviderAttemptPhase, PaidProviderBudgetSnapshotPointer,
    PaidProviderSubmitReceiptPointer, ProductionManifest, StateCommitStatus,
    VideoAttemptPhase,
)
from ai_video.production.paid_provider import (
    JimengAcceptedArtifacts, JimengAcceptedEffectProof,
    PaidProviderSubmitOutcome, PaidProviderSubmitReceipt,
    reconcile_jimeng_unknown_as_accepted,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow, canonical_paid_provider_budget_path,
    canonical_paid_provider_submit_path,
)

from ._state_commit_common import (
    _canonical_json_bytes, _state_invalid, _validated_transition,
)
from ._state_commit_contracts import PreparedArtifact


def _artifact(path: Path, model: object) -> PreparedArtifact:
    payload = _canonical_json_bytes(model)  # type: ignore[arg-type]
    return PreparedArtifact(
        relative_path=path, payload=payload,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )


class _StateCommitJimengMixin:
    def _jimeng_unknown_evidence_hashes(self, attempt, gate) -> tuple[str | None, str | None]:
        """Seal the existing dispatch and saved canvas on either recovery entry point."""

        from ai_video.production.jimeng_contracts import dispatch_matches_request

        if gate.preview.provider_kind != "jimeng":
            return None, None
        video = attempt.video_generation_state
        if video is None or attempt.operation != "video_generation":
            raise _state_invalid("Jimeng recovery requires one video paid intent.")
        dispatch = self.read_jimeng_dispatch(attempt.attempt_id, required=False)
        canvas = self.read_jimeng_canvas_snapshot(attempt.attempt_id, required=False)
        if canvas is not None and dispatch is None:
            raise _state_invalid("Jimeng saved canvas has no durable dispatch.")
        if dispatch is not None and (
            dispatch.request_fingerprint != gate.preview.request_fingerprint
            or dispatch.preview_fingerprint != gate.preview.preview_fingerprint
            or not dispatch_matches_request(dispatch, self._reopen_video_request(video.request))
        ):
            raise _state_invalid("Jimeng dispatch differs from the paid video intent.")
        if canvas is not None and (
            canvas.dispatch_hash != dispatch.content_hash
            or canvas.project_id != dispatch.project_id
            or canvas.node_id != dispatch.node_id
            or canvas.resource_id != dispatch.resource_id
        ):
            raise _state_invalid("Jimeng saved canvas differs from its dispatch.")
        return (
            dispatch.content_hash if dispatch is not None else None,
            canvas.content_hash if canvas is not None else None,
        )

    def latch_jimeng_abandoned_intent(self, attempt_id: str) -> ProductionManifest:
        """Turn a crashed in-flight Jimeng submit into a query-only UNKNOWN."""

        from ai_video.production.project import load_production_project

        manifest = load_production_project(self._project_root / "project.yaml").manifest
        attempt = self._paid_attempt(manifest, attempt_id)
        state = attempt.paid_provider_state
        video = attempt.video_generation_state
        if (state is None or video is None
                or attempt.operation != "video_generation"):
            raise _state_invalid("Jimeng recovery requires one video paid intent.")
        if (attempt.status is StateCommitStatus.OUTCOME_UNKNOWN
                and state.phase is PaidProviderAttemptPhase.OUTCOME_UNKNOWN):
            return manifest
        if (attempt.status is not StateCommitStatus.RUNNING
                or state.phase is not PaidProviderAttemptPhase.SUBMIT_INTENT
                or video.phase is not VideoAttemptPhase.SUBMIT_INTENT
                or state.submit_receipt is not None):
            raise _state_invalid("Jimeng recovery has no abandoned submit intent.")
        gate = self._reopen_paid_gate(state.gate_receipt)
        if gate.preview.provider_kind != "jimeng":
            raise _state_invalid("Jimeng recovery selected another Provider.")
        dispatch_hash, canvas_hash = self._jimeng_unknown_evidence_hashes(attempt, gate)
        receipt = PaidProviderSubmitReceipt.create(
            attempt_id=attempt_id,
            request_fingerprint=gate.preview.request_fingerprint,
            preview_fingerprint=gate.preview.preview_fingerprint,
            gate_receipt_fingerprint=gate.gate_receipt_fingerprint,
            reservation_id=state.reservation_id,
            outcome=PaidProviderSubmitOutcome.OUTCOME_UNKNOWN,
            external_effect_id=None,
            jimeng_unknown_dispatch_hash=dispatch_hash,
            jimeng_unknown_canvas_hash=canvas_hash,
            recorded_at=self._paid_provider_clock(),
        )
        return self.record_paid_provider_submit_receipt(receipt)

    def record_jimeng_canvas_snapshot(self, snapshot):
        """Persist the exact server-saved draft before accepting a paid task."""

        from ai_video.production.jimeng_contracts import (
            JimengCanvasSnapshot, canvas_snapshot_path,
        )

        if not isinstance(snapshot, JimengCanvasSnapshot):
            raise _state_invalid("Jimeng canvas snapshot is invalid.")
        snapshot = JimengCanvasSnapshot.model_validate_json(snapshot.model_dump_json())
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._paid_attempt(manifest, snapshot.attempt_id)
            dispatch = self.read_jimeng_dispatch(snapshot.attempt_id)
            if (attempt.paid_provider_state is None
                    or attempt.paid_provider_state.phase not in {
                        PaidProviderAttemptPhase.SUBMIT_INTENT,
                        PaidProviderAttemptPhase.OUTCOME_UNKNOWN,
                    }
                    or dispatch.content_hash != snapshot.dispatch_hash
                    or dispatch.project_id != snapshot.project_id
                    or dispatch.node_id != snapshot.node_id
                    or dispatch.resource_id != snapshot.resource_id):
                raise _state_invalid("Jimeng canvas snapshot differs from its paid dispatch.")
            existing = self.read_jimeng_canvas_snapshot(snapshot.attempt_id, required=False)
            if existing is not None:
                if existing != snapshot:
                    raise _state_invalid("Jimeng canvas snapshot already has different bytes.")
                return existing
            self._write_immutable_artifact(
                _artifact(canvas_snapshot_path(snapshot.content_hash), snapshot),
                attempt_id=snapshot.attempt_id,
            )
            return snapshot

    def read_jimeng_canvas_snapshot(self, attempt_id: str, *, required: bool = True):
        from ai_video.production.jimeng_contracts import (
            JimengCanvasSnapshot, canvas_snapshot_path,
        )

        directory = self._project_root / "artifacts/provider-canvas/jimeng"
        if not directory.exists():
            if required:
                raise _state_invalid("Jimeng saved canvas snapshot is missing.")
            return None
        self._reject_symlink(directory)
        matches = []
        try:
            paths = sorted(directory.iterdir())
        except OSError as exc:
            raise _state_invalid("Jimeng canvas snapshot directory is unreadable.", str(exc)) from exc
        for path in paths:
            if path.suffix != ".json":
                raise _state_invalid("Jimeng canvas snapshot directory has an unexpected entry.")
            raw = _read_regular_file_nofollow(path, contained_by=directory)
            try:
                item = JimengCanvasSnapshot.model_validate_json(raw.data)
            except ValueError as exc:
                raise _state_invalid("Jimeng canvas snapshot is invalid.", str(exc)) from exc
            if path != self._project_root / canvas_snapshot_path(item.content_hash):
                raise _state_invalid("Jimeng canvas snapshot path differs from its content hash.")
            if item.attempt_id == attempt_id:
                matches.append(item)
        if len(matches) != 1:
            if not required and not matches:
                return None
            raise _state_invalid("Jimeng canvas snapshot identity is missing or ambiguous.")
        return matches[0]

    def reconcile_jimeng_unknown(self, proof: JimengAcceptedEffectProof) -> ProductionManifest:
        """Accept only an exact existing resource; this never mints a permit."""

        if not isinstance(proof, JimengAcceptedEffectProof):
            raise _state_invalid("Jimeng recovery proof is invalid.")
        proof = JimengAcceptedEffectProof.model_validate_json(proof.model_dump_json())
        with self._exclusive_lock():
            from ai_video.production.project import load_production_project

            manifest = self._read_manifest()
            if load_production_project(self._project_root / "project.yaml").manifest != manifest:
                raise _state_invalid("Jimeng recovery requires one exact standard project reopen.")
            attempt = next((item for item in manifest.attempts
                if item.paid_provider_state is not None
                and item.paid_provider_state.submit_receipt is not None
                and item.paid_provider_state.submit_receipt.submit_receipt_fingerprint
                    == proof.prior_unknown_receipt_fingerprint), None)
            if attempt is None:
                raise _state_invalid("Jimeng unknown submit receipt is not selected.")
            state = attempt.paid_provider_state
            video = attempt.video_generation_state
            if (attempt.operation != "video_generation"
                    or attempt.status is not StateCommitStatus.OUTCOME_UNKNOWN
                    or state.phase is not PaidProviderAttemptPhase.OUTCOME_UNKNOWN
                    or video is None or video.phase is not VideoAttemptPhase.SUBMIT_INTENT
                    or video.paid_submit_receipt is not None
                    or manifest.active_paid_provider_budget is None):
                raise _state_invalid("Jimeng recovery requires a frozen unknown video attempt.")
            prior = self._reopen_paid_submit(state.submit_receipt)
            gate = self._reopen_paid_gate(state.gate_receipt)
            dispatch = self.read_jimeng_dispatch(attempt.attempt_id)
            canvas = self.read_jimeng_canvas_snapshot(attempt.attempt_id)
            from ai_video.production.jimeng_contracts import JIMENG_MODELS, dispatch_matches_request
            if (gate.preview.provider_kind != "jimeng"
                    or gate.preview.model_id not in JIMENG_MODELS
                    or prior.outcome is not PaidProviderSubmitOutcome.OUTCOME_UNKNOWN
                    or prior.external_effect_id is not None
                    or proof.request_fingerprint != prior.request_fingerprint
                    or proof.preview_fingerprint != prior.preview_fingerprint
                    or proof.dispatch_hash != dispatch.content_hash
                    or prior.jimeng_unknown_dispatch_hash != dispatch.content_hash
                    or (prior.jimeng_unknown_canvas_hash is not None
                        and prior.jimeng_unknown_canvas_hash != canvas.content_hash)
                    or not dispatch_matches_request(
                        dispatch, self._reopen_video_request(video.request))
                    or proof.base_budget_hash
                        != manifest.active_paid_provider_budget.content_hash
                    or proof.account_sha256 != dispatch.account_sha256
                    or proof.project_id != dispatch.project_id
                    or proof.node_id != dispatch.node_id
                    or proof.submit_id != dispatch.submit_id
                    or proof.resource_id != dispatch.resource_id
                    or proof.params_sha256 != dispatch.params_sha256
                    or canvas.dispatch_hash != dispatch.content_hash
                    or canvas.project_id != dispatch.project_id
                    or canvas.node_id != dispatch.node_id
                    or canvas.resource_id != dispatch.resource_id
                    or canvas.recorded_at < dispatch.recorded_at
                    or canvas.recorded_at > proof.observed_at
                    or proof.observed_at < dispatch.recorded_at
                    or proof.observed_at > self._paid_provider_clock()):
                raise _state_invalid("Jimeng resource readback does not match the sealed dispatch.")
            effect = f"{proof.resource_id}:{proof.task_id}"
            for other in manifest.attempts:
                if other.attempt_id == attempt.attempt_id or other.paid_provider_state is None:
                    continue
                pointer = other.paid_provider_state.submit_receipt
                if pointer is not None and self._reopen_paid_submit(pointer).external_effect_id == effect:
                    raise _state_invalid("Jimeng recovered effect identity is already owned.")
            corrective = PaidProviderSubmitReceipt.create(
                attempt_id=prior.attempt_id,
                request_fingerprint=prior.request_fingerprint,
                preview_fingerprint=prior.preview_fingerprint,
                gate_receipt_fingerprint=prior.gate_receipt_fingerprint,
                reservation_id=prior.reservation_id,
                outcome=PaidProviderSubmitOutcome.ACCEPTED,
                external_effect_id=effect,
                jimeng_accepted_effect=proof,
                jimeng_accepted_artifacts=JimengAcceptedArtifacts(
                    dispatch_hash=dispatch.content_hash,
                    canvas_hash=canvas.content_hash,
                ),
                recorded_at=proof.observed_at,
            )
            budget = reconcile_jimeng_unknown_as_accepted(
                self._reopen_paid_budget(manifest.active_paid_provider_budget),
                prior=prior, accepted=corrective,
            )
            budget_artifact = _artifact(canonical_paid_provider_budget_path(budget.content_hash), budget)
            submit_artifact = _artifact(
                canonical_paid_provider_submit_path(corrective.submit_receipt_fingerprint),
                corrective,
            )
            self._write_immutable_artifact(budget_artifact, attempt_id=attempt.attempt_id)
            self._write_immutable_artifact(submit_artifact, attempt_id=attempt.attempt_id)
            budget_pointer = PaidProviderBudgetSnapshotPointer(
                path=budget_artifact.relative_path, revision=budget.revision,
                content_hash=budget.content_hash, file_sha256=budget_artifact.file_sha256,
            )
            submit_pointer = PaidProviderSubmitReceiptPointer(
                path=submit_artifact.relative_path,
                submit_receipt_fingerprint=corrective.submit_receipt_fingerprint,
                file_sha256=submit_artifact.file_sha256,
            )
            next_attempt = _validated_transition(attempt, {
                "status": StateCommitStatus.RUNNING,
                "finished_at": None, "error_code": None, "error_message": None,
                "paid_provider_state": state.model_copy(update={
                    "phase": PaidProviderAttemptPhase.ACCEPTED,
                    "submit_receipt": submit_pointer,
                }),
                "video_generation_state": video.model_copy(update={
                    "phase": VideoAttemptPhase.SUBMITTED,
                    "paid_submit_receipt": submit_pointer,
                }),
            })
            next_manifest = _validated_transition(manifest, {
                "manifest_revision": manifest.manifest_revision + 1,
                "active_paid_provider_budget": budget_pointer,
                "attempts": tuple(next_attempt if item.attempt_id == attempt.attempt_id else item
                    for item in manifest.attempts),
            })
            self._write_manifest_atomic(next_manifest)
            self._reopen_paid_budget(budget_pointer)
            self._reopen_paid_submit(submit_pointer)
            return self._read_manifest()

    def record_jimeng_dispatch(self, dispatch):
        """Seal native IDs and ordered material provenance before any generate POST.

        This is immutable technical evidence. The existing paid state and
        Manifest remain the sole lifecycle and authorization owners.
        """

        from ai_video.production.jimeng_contracts import (
            JimengDispatchIntent, dispatch_path,
        )

        if not isinstance(dispatch, JimengDispatchIntent):
            raise _state_invalid("Jimeng dispatch intent is invalid.")
        dispatch = JimengDispatchIntent.model_validate_json(dispatch.model_dump_json())
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._paid_attempt(manifest, dispatch.attempt_id)
            state = attempt.paid_provider_state
            if (attempt.operation != "video_generation"
                    or attempt.status is not StateCommitStatus.RUNNING
                    or state is None
                    or state.phase is not PaidProviderAttemptPhase.SUBMIT_INTENT):
                raise _state_invalid("Jimeng dispatch requires one current paid submit intent.")
            gate = self._reopen_paid_gate(state.gate_receipt)
            if (gate.preview.provider_kind != "jimeng"
                    or gate.preview.request_fingerprint != dispatch.request_fingerprint
                    or gate.preview.preview_fingerprint != dispatch.preview_fingerprint):
                raise _state_invalid("Jimeng dispatch differs from the paid Gate.")
            if self.read_jimeng_dispatch(dispatch.attempt_id, required=False) is not None:
                raise _state_invalid("Jimeng dispatch identity already exists; no second POST is allowed.")
            artifact = _artifact(dispatch_path(dispatch.content_hash), dispatch)
            self._write_immutable_artifact(artifact, attempt_id=dispatch.attempt_id)
            return dispatch

    def read_jimeng_dispatch(self, attempt_id: str, *, required: bool = True):
        """Reopen one immutable intent by attempt; do not infer its outcome."""

        from ai_video.production.jimeng_contracts import (
            JimengDispatchIntent, dispatch_path,
        )

        directory = self._project_root / "artifacts/provider-dispatch/jimeng"
        if not directory.exists():
            if required:
                raise _state_invalid("Jimeng dispatch intent is missing.")
            return None
        self._reject_symlink(directory)
        matches = []
        try:
            paths = sorted(directory.iterdir())
        except OSError as exc:
            raise _state_invalid("Jimeng dispatch directory is unreadable.", str(exc)) from exc
        for path in paths:
            if path.suffix != ".json":
                raise _state_invalid("Jimeng dispatch directory has an unexpected entry.")
            snapshot = _read_regular_file_nofollow(path, contained_by=directory)
            try:
                entry = JimengDispatchIntent.model_validate_json(snapshot.data)
            except ValueError as exc:
                raise _state_invalid("Jimeng dispatch evidence is invalid.", str(exc)) from exc
            if path != self._project_root / dispatch_path(entry.content_hash):
                raise _state_invalid("Jimeng dispatch evidence path is not content-addressed.")
            if entry.attempt_id == attempt_id:
                matches.append(entry)
        if len(matches) != 1:
            if not required and not matches:
                return None
            raise _state_invalid("Jimeng dispatch identity is missing or ambiguous.")
        return matches[0]
