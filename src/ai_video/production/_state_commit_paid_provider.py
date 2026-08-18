from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

from ai_video.errors import ErrorCode
from ai_video.production.models import (
    PaidProviderAttemptPhase,
    PaidProviderAttemptState,
    PaidProviderBudgetSnapshotPointer,
    PaidProviderGateReceiptPointer,
    PaidProviderSubmitReceiptPointer,
    ProductionManifest,
    StateCommitAttempt,
    StateCommitStatus,
    VideoAttemptPhase,
)
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderBudgetSnapshot,
    PaidProviderCallPreview,
    PaidProviderGateReceipt,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
    apply_paid_provider_submit_receipt,
    reserve_paid_provider_budget,
    settle_paid_provider_budget,
    validate_paid_provider_authorization,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_paid_provider_budget_path,
    canonical_paid_provider_gate_path,
    canonical_paid_provider_submit_path,
)

from ._state_commit_common import (
    _canonical_json_bytes,
    _state_invalid,
    _timestamp,
    _validated_transition,
)
from ._state_commit_contracts import (
    PreparedArtifact,
    _PAID_PROVIDER_PERMIT_TOKEN,
    _DurablePaidProviderSubmitPermit,
)


PaidProviderAuthorizer = Callable[
    [PaidProviderCallPreview], PaidProviderAuthorizationDecision | None
]


def _artifact(path: Path, model: object) -> PreparedArtifact:
    payload = _canonical_json_bytes(model)  # type: ignore[arg-type]
    return PreparedArtifact(
        relative_path=path,
        payload=payload,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )


class _StateCommitPaidProviderMixin:
    def _reopen_paid_budget(
        self, pointer: PaidProviderBudgetSnapshotPointer
    ) -> PaidProviderBudgetSnapshot:
        try:
            raw = _read_regular_file_nofollow(
                self._project_root / pointer.path,
                contained_by=self._project_root / "state",
            )
            snapshot = PaidProviderBudgetSnapshot.model_validate_json(raw.data)
        except (OSError, ValidationError, ValueError) as exc:
            raise _state_invalid("Paid Provider budget could not be reopened.", str(exc)) from exc
        if (
            raw.file_sha256 != pointer.file_sha256
            or snapshot.revision != pointer.revision
            or snapshot.content_hash != pointer.content_hash
        ):
            raise _state_invalid("Paid Provider budget pointer identity is invalid.")
        return snapshot

    def _reopen_paid_gate(
        self, pointer: PaidProviderGateReceiptPointer
    ) -> PaidProviderGateReceipt:
        try:
            raw = _read_regular_file_nofollow(
                self._project_root / pointer.path,
                contained_by=self._project_root / "state",
            )
            receipt = PaidProviderGateReceipt.model_validate_json(raw.data)
        except (OSError, ValidationError, ValueError) as exc:
            raise _state_invalid("Paid Provider Gate receipt could not be reopened.", str(exc)) from exc
        if (
            raw.file_sha256 != pointer.file_sha256
            or receipt.gate_receipt_fingerprint != pointer.gate_receipt_fingerprint
        ):
            raise _state_invalid("Paid Provider Gate receipt identity is invalid.")
        return receipt

    def _reopen_paid_submit(
        self, pointer: PaidProviderSubmitReceiptPointer
    ) -> PaidProviderSubmitReceipt:
        try:
            raw = _read_regular_file_nofollow(
                self._project_root / pointer.path,
                contained_by=self._project_root / "state",
            )
            receipt = PaidProviderSubmitReceipt.model_validate_json(raw.data)
        except (OSError, ValidationError, ValueError) as exc:
            raise _state_invalid("Paid Provider submit receipt could not be reopened.", str(exc)) from exc
        if (
            raw.file_sha256 != pointer.file_sha256
            or receipt.submit_receipt_fingerprint != pointer.submit_receipt_fingerprint
        ):
            raise _state_invalid("Paid Provider submit receipt identity is invalid.")
        return receipt

    @staticmethod
    def _paid_attempt(manifest: ProductionManifest, attempt_id: str) -> StateCommitAttempt:
        attempt = next(
            (item for item in manifest.attempts if item.attempt_id == attempt_id), None
        )
        if attempt is None:
            raise _state_invalid("Paid Provider attempt does not exist.")
        return attempt

    def record_paid_provider_submit_intent(
        self,
        preview: PaidProviderCallPreview,
        *,
        reservation_id: str,
    ) -> _DurablePaidProviderSubmitPermit:
        """Atomically select the exact reservation/Gate evidence and mint one permit."""

        authorizer: PaidProviderAuthorizer | None = self._paid_provider_authorizer
        if authorizer is None:
            raise _state_invalid("Paid Provider authorizer is not configured.")
        authorization = authorizer(preview)
        if authorization is None:
            raise _state_invalid("Paid Provider authorization was denied.")
        with self._exclusive_lock():
            validate_paid_provider_authorization(
                preview, authorization, now=self._paid_provider_clock()
            )
            manifest = self._read_manifest()
            if manifest.schema_version not in {
                "2.2",
                "2.3",
                "2.4",
                "2.5",
                "2.6",
                "2.7",
            }:
                raise _state_invalid("Paid Provider submit intent requires a provider-aware Manifest.")
            attempt = self._paid_attempt(manifest, preview.attempt_id)
            if (
                attempt.status is not StateCommitStatus.RUNNING
                or attempt.paid_provider_state is not None
                or attempt.base_manifest_revision > manifest.manifest_revision
            ):
                raise _state_invalid("Paid Provider intent requires an exact current running attempt.")
            if preview.operation == "voice_generation":
                request = attempt.voice_request
                if (
                    attempt.operation != "voice_generation"
                    or attempt.voice_phase != "submit_intent"
                    or request is None
                    or request.attempt_id != preview.attempt_id
                    or request.request_fingerprint != preview.request_fingerprint
                    or request.provider_kind != preview.provider_kind
                    or request.model_id != preview.model_id
                    or request.destination != preview.destination
                ):
                    raise _state_invalid(
                        "Paid Provider preview does not match the durable operation request."
                    )
            elif preview.operation == "video_generation":
                video_state = attempt.video_generation_state
                if video_state is None:
                    raise _state_invalid(
                        "Paid Provider video intent requires durable video state."
                    )
                request = self._reopen_video_request(video_state.request)
                if (
                    manifest.schema_version != "2.7"
                    or attempt.operation != "video_generation"
                    or video_state.phase is not VideoAttemptPhase.REQUEST
                    or request.resolved_generation_hash
                    != preview.request_fingerprint
                    or request.provider_kind != preview.provider_kind
                    or request.model_id != preview.model_id
                ):
                    raise _state_invalid(
                        "Paid Provider preview does not match the durable video request."
                    )
            else:
                raise _state_invalid(
                    "Paid Provider preview has no supported durable operation request."
                )
            current_budget = (
                self._reopen_paid_budget(manifest.active_paid_provider_budget)
                if manifest.active_paid_provider_budget is not None
                else None
            )
            next_budget, reservation = reserve_paid_provider_budget(
                current_budget,
                preview=preview,
                authorization=authorization,
                reservation_id=reservation_id,
            )
            budget_artifact = _artifact(
                canonical_paid_provider_budget_path(next_budget.content_hash), next_budget
            )
            gate = PaidProviderGateReceipt.create(
                preview=preview,
                authorization=authorization,
                reservation_id=reservation.reservation_id,
                budget_snapshot_revision=next_budget.revision,
                budget_snapshot_content_hash=next_budget.content_hash,
                budget_snapshot_file_sha256=budget_artifact.file_sha256,
            )
            gate_artifact = _artifact(
                canonical_paid_provider_gate_path(gate.gate_receipt_fingerprint), gate
            )
            self._write_immutable_artifact(budget_artifact, attempt_id=preview.attempt_id)
            self._write_immutable_artifact(gate_artifact, attempt_id=preview.attempt_id)
            budget_pointer = PaidProviderBudgetSnapshotPointer(
                path=budget_artifact.relative_path,
                revision=next_budget.revision,
                content_hash=next_budget.content_hash,
                file_sha256=budget_artifact.file_sha256,
            )
            gate_pointer = PaidProviderGateReceiptPointer(
                path=gate_artifact.relative_path,
                gate_receipt_fingerprint=gate.gate_receipt_fingerprint,
                file_sha256=gate_artifact.file_sha256,
            )
            paid_state = PaidProviderAttemptState(
                gate_receipt=gate_pointer,
                reservation_id=reservation.reservation_id,
                phase=PaidProviderAttemptPhase.SUBMIT_INTENT,
            )
            attempt_update: dict[str, object] = {
                "paid_provider_state": paid_state
            }
            if preview.operation == "video_generation":
                assert attempt.video_generation_state is not None
                attempt_update["video_generation_state"] = (
                    attempt.video_generation_state.model_copy(
                        update={"phase": VideoAttemptPhase.SUBMIT_INTENT}
                    )
                )
            next_attempt = _validated_transition(attempt, attempt_update)
            next_manifest = _validated_transition(
                manifest,
                {
                    "schema_version": (
                        "2.7" if manifest.schema_version == "2.7" else "2.6"
                    ),
                    "manifest_revision": manifest.manifest_revision + 1,
                    "active_paid_provider_budget": budget_pointer,
                    "attempts": tuple(
                        next_attempt if item.attempt_id == attempt.attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(next_manifest)
            reopened = self._read_manifest()
            self._reopen_paid_budget(budget_pointer)
            self._reopen_paid_gate(gate_pointer)
            manifest_raw = _read_regular_file_nofollow(
                self._project_root / "state/manifest.json",
                contained_by=self._project_root / "state",
            )
            binding = {
                "attempt_id": preview.attempt_id,
                "operation": preview.operation,
                "request_fingerprint": preview.request_fingerprint,
                "preview_fingerprint": preview.preview_fingerprint,
                "gate_receipt_fingerprint": gate.gate_receipt_fingerprint,
                "reservation_id": reservation.reservation_id,
                "destination": preview.destination,
                "provider_kind": preview.provider_kind,
                "model_id": preview.model_id,
                "currency": preview.currency,
                "estimated_cost_upper_bound_microunits": str(
                    preview.estimated_cost_upper_bound_microunits
                ),
                "provider_policy_snapshot_id": preview.provider_policy_snapshot_id,
                "retention_mode": preview.retention_mode,
                "secret_reference_kind": preview.secret_reference.kind,
                "secret_reference_id": preview.secret_reference.reference_id,
            }
            return _DurablePaidProviderSubmitPermit(
                _PAID_PROVIDER_PERMIT_TOKEN,
                binding=binding,
                durability_validator=lambda: self._paid_intent_is_current(
                    reopened.manifest_revision,
                    manifest_raw.file_sha256,
                    binding,
                ),
            )

    def _paid_intent_is_current(
        self,
        manifest_revision: int,
        manifest_file_sha256: str,
        binding: dict[str, str],
    ) -> bool:
        try:
            raw = _read_regular_file_nofollow(
                self._project_root / "state/manifest.json",
                contained_by=self._project_root / "state",
            )
            manifest = ProductionManifest.model_validate_json(raw.data)
            attempt = self._paid_attempt(manifest, binding["attempt_id"])
            state = attempt.paid_provider_state
            return bool(
                raw.file_sha256 == manifest_file_sha256
                and manifest.manifest_revision == manifest_revision
                and state is not None
                and state.phase is PaidProviderAttemptPhase.SUBMIT_INTENT
                and state.reservation_id == binding["reservation_id"]
                and state.gate_receipt.gate_receipt_fingerprint
                == binding["gate_receipt_fingerprint"]
                and (
                    gate := self._reopen_paid_gate(state.gate_receipt)
                ).preview.preview_fingerprint
                == binding["preview_fingerprint"]
                and gate.reservation_id == binding["reservation_id"]
            )
        except Exception:
            return False

    def record_paid_provider_submit_receipt(
        self, receipt: PaidProviderSubmitReceipt
    ) -> ProductionManifest:
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._paid_attempt(manifest, receipt.attempt_id)
            state = attempt.paid_provider_state
            if (
                manifest.schema_version not in {"2.6", "2.7"}
                or state is None
                or state.phase is not PaidProviderAttemptPhase.SUBMIT_INTENT
                or manifest.active_paid_provider_budget is None
            ):
                raise _state_invalid("Paid Provider submit receipt requires exact current intent.")
            gate = self._reopen_paid_gate(state.gate_receipt)
            if (
                receipt.request_fingerprint != gate.preview.request_fingerprint
                or receipt.preview_fingerprint != gate.preview.preview_fingerprint
                or receipt.gate_receipt_fingerprint != gate.gate_receipt_fingerprint
                or receipt.reservation_id != state.reservation_id
            ):
                raise _state_invalid("Paid Provider submit receipt identity does not match intent.")
            if receipt.external_effect_id is not None:
                for existing_attempt in manifest.attempts:
                    existing_state = existing_attempt.paid_provider_state
                    if existing_state is None or existing_state.submit_receipt is None:
                        continue
                    existing = self._reopen_paid_submit(existing_state.submit_receipt)
                    if existing.external_effect_id == receipt.external_effect_id:
                        raise _state_invalid(
                            "Paid Provider external effect identity is already owned."
                        )
            budget = apply_paid_provider_submit_receipt(
                self._reopen_paid_budget(manifest.active_paid_provider_budget), receipt
            )
            budget_artifact = _artifact(
                canonical_paid_provider_budget_path(budget.content_hash), budget
            )
            submit_artifact = _artifact(
                canonical_paid_provider_submit_path(receipt.submit_receipt_fingerprint),
                receipt,
            )
            self._write_immutable_artifact(budget_artifact, attempt_id=receipt.attempt_id)
            self._write_immutable_artifact(submit_artifact, attempt_id=receipt.attempt_id)
            budget_pointer = PaidProviderBudgetSnapshotPointer(
                path=budget_artifact.relative_path,
                revision=budget.revision,
                content_hash=budget.content_hash,
                file_sha256=budget_artifact.file_sha256,
            )
            submit_pointer = PaidProviderSubmitReceiptPointer(
                path=submit_artifact.relative_path,
                submit_receipt_fingerprint=receipt.submit_receipt_fingerprint,
                file_sha256=submit_artifact.file_sha256,
            )
            phase = PaidProviderAttemptPhase(receipt.outcome.value)
            attempt_update: dict[str, object] = {
                "paid_provider_state": state.model_copy(
                    update={"phase": phase, "submit_receipt": submit_pointer}
                )
            }
            if (
                attempt.operation == "video_generation"
                and receipt.outcome is PaidProviderSubmitOutcome.ACCEPTED
            ):
                video_state = attempt.video_generation_state
                if (
                    video_state is None
                    or video_state.phase is not VideoAttemptPhase.SUBMIT_INTENT
                    or video_state.resolved_generation_hash
                    != receipt.request_fingerprint
                ):
                    raise _state_invalid(
                        "Paid Provider submit receipt does not match video intent."
                    )
                attempt_update["video_generation_state"] = video_state.model_copy(
                    update={
                        "phase": VideoAttemptPhase.SUBMITTED,
                        "paid_submit_receipt": submit_pointer,
                    }
                )
            if receipt.outcome is PaidProviderSubmitOutcome.OUTCOME_UNKNOWN:
                attempt_update.update(
                    status=StateCommitStatus.OUTCOME_UNKNOWN,
                    finished_at=_timestamp(),
                    error_code=ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN.value,
                    error_message="Paid Provider submit outcome is unknown; blind retry is forbidden.",
                )
            elif receipt.outcome is PaidProviderSubmitOutcome.KNOWN_NO_EFFECT:
                attempt_update.update(
                    status=StateCommitStatus.FAILED,
                    finished_at=_timestamp(),
                    error_code=ErrorCode.PAID_PROVIDER_KNOWN_NO_EFFECT.value,
                    error_message="Paid Provider confirmed that no billable effect occurred.",
                )
            next_attempt = _validated_transition(attempt, attempt_update)
            next_manifest = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "active_paid_provider_budget": budget_pointer,
                    "attempts": tuple(
                        next_attempt if item.attempt_id == attempt.attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(next_manifest)
            reopened = self._read_manifest()
            self._reopen_paid_budget(budget_pointer)
            self._reopen_paid_submit(submit_pointer)
            return reopened

    def settle_paid_provider_reservation(
        self,
        *,
        attempt_id: str,
        actual_cost_microunits: int,
    ) -> ProductionManifest:
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._paid_attempt(manifest, attempt_id)
            state = attempt.paid_provider_state
            if (
                state is None
                or state.phase is not PaidProviderAttemptPhase.ACCEPTED
                or manifest.active_paid_provider_budget is None
            ):
                raise _state_invalid("Paid Provider settlement requires exact active evidence.")
            budget = settle_paid_provider_budget(
                self._reopen_paid_budget(manifest.active_paid_provider_budget),
                reservation_id=state.reservation_id,
                actual_cost_microunits=actual_cost_microunits,
            )
            artifact = _artifact(
                canonical_paid_provider_budget_path(budget.content_hash), budget
            )
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            pointer = PaidProviderBudgetSnapshotPointer(
                path=artifact.relative_path,
                revision=budget.revision,
                content_hash=budget.content_hash,
                file_sha256=artifact.file_sha256,
            )
            next_attempt = _validated_transition(
                attempt,
                {
                    "paid_provider_state": state.model_copy(
                        update={"phase": PaidProviderAttemptPhase.SETTLED}
                    )
                },
            )
            next_manifest = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "active_paid_provider_budget": pointer,
                    "attempts": tuple(
                        next_attempt if item.attempt_id == attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(next_manifest)
            self._reopen_paid_budget(pointer)
            return self._read_manifest()

    def _recover_paid_provider_intents(
        self, manifest: ProductionManifest
    ) -> tuple[ProductionManifest, tuple[object, ...]]:
        """Seal an interrupted submit intent as outcome_unknown without reminting."""

        from ai_video.production.models import RecoveryDisposition, RecoveryItem

        if manifest.active_paid_provider_budget is None:
            return manifest, ()
        attempts = list(manifest.attempts)
        items: list[RecoveryItem] = []
        changed = False
        budget = self._reopen_paid_budget(manifest.active_paid_provider_budget)
        for index, attempt in enumerate(attempts):
            state = attempt.paid_provider_state
            if (
                attempt.status is not StateCommitStatus.RUNNING
                or state is None
                or state.phase is not PaidProviderAttemptPhase.SUBMIT_INTENT
            ):
                continue
            gate = self._reopen_paid_gate(state.gate_receipt)
            receipt = PaidProviderSubmitReceipt.create(
                attempt_id=attempt.attempt_id,
                request_fingerprint=gate.preview.request_fingerprint,
                preview_fingerprint=gate.preview.preview_fingerprint,
                gate_receipt_fingerprint=gate.gate_receipt_fingerprint,
                reservation_id=state.reservation_id,
                outcome=PaidProviderSubmitOutcome.OUTCOME_UNKNOWN,
                external_effect_id=None,
                recorded_at=datetime.fromisoformat(_timestamp()),
            )
            budget = apply_paid_provider_submit_receipt(budget, receipt)
            submit_artifact = _artifact(
                canonical_paid_provider_submit_path(receipt.submit_receipt_fingerprint),
                receipt,
            )
            self._write_immutable_artifact(
                submit_artifact, attempt_id=attempt.attempt_id
            )
            submit_pointer = PaidProviderSubmitReceiptPointer(
                path=submit_artifact.relative_path,
                submit_receipt_fingerprint=receipt.submit_receipt_fingerprint,
                file_sha256=submit_artifact.file_sha256,
            )
            attempts[index] = _validated_transition(
                attempt,
                {
                    "status": StateCommitStatus.OUTCOME_UNKNOWN,
                    "paid_provider_state": state.model_copy(
                        update={
                            "phase": PaidProviderAttemptPhase.OUTCOME_UNKNOWN,
                            "submit_receipt": submit_pointer,
                        }
                    ),
                    "finished_at": _timestamp(),
                    "error_code": ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN.value,
                    "error_message": "Paid Provider submit outcome is unknown; blind retry is forbidden.",
                },
            )
            items.append(
                RecoveryItem(
                    path=submit_pointer.path,
                    disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                    sha256=submit_pointer.file_sha256,
                )
            )
            changed = True
        if not changed:
            return manifest, ()
        budget_artifact = _artifact(
            canonical_paid_provider_budget_path(budget.content_hash), budget
        )
        self._write_immutable_artifact(
            budget_artifact, attempt_id="paid-provider-recovery"
        )
        budget_pointer = PaidProviderBudgetSnapshotPointer(
            path=budget_artifact.relative_path,
            revision=budget.revision,
            content_hash=budget.content_hash,
            file_sha256=budget_artifact.file_sha256,
        )
        recovered = _validated_transition(
            manifest,
            {
                "manifest_revision": manifest.manifest_revision + 1,
                "active_paid_provider_budget": budget_pointer,
                "attempts": tuple(attempts),
            },
        )
        self._write_manifest_atomic(recovered)
        return self._read_manifest(), tuple(items)
