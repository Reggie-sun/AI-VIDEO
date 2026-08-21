from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import (
    VoiceCallAuthorization,
    VoiceGenerationPreview,
    VoiceGenerationRequest,
    VoiceProviderResult,
)
from ai_video.production.models import (
    ProductionManifest,
    StateCommitAttempt,
    StateCommitStatus,
    VoiceRequestReceipt,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_voice_attempt_artifact_path,
    canonical_voice_attempt_root,
    canonical_voice_audio_candidate_path,
)

from ._state_commit_common import (
    _candidate_artifacts_hash,
    _canonical_json_bytes,
    _stable_voice_terminal_message,
    _state_commit_failed,
    _state_invalid,
    _timestamp,
    _validated_transition,
)
from ._state_commit_contracts import (
    CommitPhase,
    PreparedArtifact,
    VoiceAttemptPaths,
    _VOICE_PERMIT_TOKEN,
    _DurableVoiceSubmitPermit,
)


class _StateCommitVoiceIntentMixin:
    def voice_attempt_paths(self, attempt_id: str) -> VoiceAttemptPaths:
        try:
            root = canonical_voice_attempt_root(self._project_root, attempt_id)
            return VoiceAttemptPaths(
                attempt_root=root,
                request_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "request.json"
                ),
                preview_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "preview.json"
                ),
                authorization_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "authorization.json"
                ),
                submit_intent_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "submit-intent.json"
                ),
                audio_candidate_path=canonical_voice_audio_candidate_path(
                    self._project_root, attempt_id
                ),
                alignment_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "alignment.json"
                ),
                cost_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "cost.json"
                ),
                provenance_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "provenance.json"
                ),
                outcome_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "outcome.json"
                ),
            )
        except ValueError as exc:
            raise _state_invalid("Voice attempt ID is unsafe.", str(exc)) from exc

    @staticmethod
    def _voice_receipt(
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
    ) -> VoiceRequestReceipt:
        if (
            preview.request_fingerprint != request.voice_request_fingerprint
            or authorization.request_fingerprint != request.voice_request_fingerprint
            or authorization.preview_fingerprint != preview.preview_fingerprint
            or authorization.destination != preview.destination
            or authorization.budget_reservation_receipt_id
            != request.budget_reservation_receipt_id
            or authorization.egress_authorization_receipt_id
            != request.egress_authorization_receipt_id
            or preview.pricing_snapshot_id != request.pricing_snapshot_id
            or authorization.pricing_snapshot_id != request.pricing_snapshot_id
            or authorization.payload_categories != preview.payload_categories
            or authorization.cost_ceiling_microunits
            < preview.estimated_cost_upper_bound_microunits
            or not preview.timing_supported
            or not preview.output_supported
            or not authorization.provider_enabled
        ):
            raise _state_invalid(
                "Voice preview or authorization does not match the immutable request."
            )
        return VoiceRequestReceipt(
            request_id=request.request_id,
            attempt_id=request.attempt_id,
            request_fingerprint=request.voice_request_fingerprint,
            script_hash=request.script_hash,
            provider_kind=request.provider_kind,
            model_id=request.model_id,
            voice_id=request.voice_id,
            language=request.language,
            pricing_snapshot_id=request.pricing_snapshot_id,
            budget_reservation_receipt_id=request.budget_reservation_receipt_id,
            egress_authorization_receipt_id=request.egress_authorization_receipt_id,
            destination=authorization.destination,
        )

    def _voice_prepared_artifact(
        self, attempt_id: str, absolute_path: Path, payload: bytes
    ) -> PreparedArtifact:
        return self.prepare_artifact(
            attempt_id, absolute_path.relative_to(self._project_root), payload
        )

    def begin_voice_generation(
        self,
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
        *,
        dependency_transition_preparer_available: bool = False,
    ) -> ProductionManifest:
        """Persist R+1 request, preview, and authorization evidence without transport."""

        receipt = self._voice_receipt(request, preview, authorization)
        paths = self.voice_attempt_paths(request.attempt_id)
        evidence = (
            self._voice_prepared_artifact(
                request.attempt_id, paths.request_path, _canonical_json_bytes(request)
            ),
            self._voice_prepared_artifact(
                request.attempt_id, paths.preview_path, _canonical_json_bytes(preview)
            ),
            self._voice_prepared_artifact(
                request.attempt_id,
                paths.authorization_path,
                _canonical_json_bytes(authorization),
            ),
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if (
                manifest.schema_version in {"2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"}
                and not dependency_transition_preparer_available
            ):
                raise _state_invalid(
                    "Graph-aware Manifest voice generation requires a dependency transition preparer."
                )
            existing = next(
                (item for item in manifest.attempts if item.attempt_id == request.attempt_id),
                None,
            )
            if existing is not None:
                if (
                    existing.operation == "voice_generation"
                    and existing.voice_request == receipt
                    and existing.base_project == request.base_project
                    and existing.base_registry == request.base_registry
                    and existing.voice_phase == "request"
                    and existing.status is StateCommitStatus.RUNNING
                ):
                    reopened = self._reopen_voice_evidence(
                        request.attempt_id, include_intent=False
                    )
                    if reopened != evidence or (
                        _candidate_artifacts_hash(reopened)
                        != existing.candidate_artifacts_hash
                    ):
                        raise _state_invalid("Voice R+1 replay evidence is not exact.")
                    return manifest
                raise _state_invalid("Voice attempt ID was already used by another request.")
            if (
                request.base_project != manifest.active_project
                or request.base_registry != manifest.active_registry
            ):
                raise _state_invalid("Voice request base project or registry is stale.")
            if any(
                item.status in {StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN}
                for item in manifest.attempts
            ):
                raise _state_invalid(
                    "Production state has an unresolved attempt; explicit recovery is required."
                )
            for artifact in evidence:
                self._write_immutable_artifact(artifact, attempt_id=request.attempt_id)
            attempt = StateCommitAttempt(
                attempt_id=request.attempt_id,
                operation="voice_generation",
                status=StateCommitStatus.RUNNING,
                base_manifest_revision=manifest.manifest_revision,
                base_project=manifest.active_project,
                base_registry=manifest.active_registry,
                candidate_artifacts_hash=_candidate_artifacts_hash(evidence),
                voice_request=receipt,
                voice_phase="request",
                started_at=_timestamp(),
            )
            r1 = _validated_transition(
                manifest,
                {
                    "schema_version": (
                        manifest.schema_version
                        if manifest.schema_version in {"2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"}
                        else "2.2"
                    ),
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": manifest.attempts + (attempt,),
                },
            )
            self._write_manifest_atomic(r1)
            return self._read_manifest()

    def record_voice_submit_intent(
        self,
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
    ) -> _DurableVoiceSubmitPermit:
        """Persist R+2, reopen it, and mint exactly one process-local permit."""

        receipt = self._voice_receipt(request, preview, authorization)
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = next(
                (item for item in manifest.attempts if item.attempt_id == request.attempt_id),
                None,
            )
            if (
                attempt is None
                or attempt.operation != "voice_generation"
                or attempt.voice_request != receipt
                or attempt.status is not StateCommitStatus.RUNNING
                or attempt.voice_phase != "request"
                or manifest.active_project != request.base_project
                or manifest.active_registry != request.base_registry
            ):
                raise _state_invalid(
                    "Voice submit intent requires the exact current R+1 attempt."
                )
            self._crash_injector.checkpoint(CommitPhase.BEFORE_VOICE_SUBMIT_INTENT)
            paths = self.voice_attempt_paths(request.attempt_id)
            intent_payload = (
                json.dumps(
                    {
                        "attempt_id": request.attempt_id,
                        "request_fingerprint": request.voice_request_fingerprint,
                        "authorization_fingerprint": authorization.authorization_fingerprint,
                        "destination": authorization.destination,
                        "budget_reservation_receipt_id": authorization.budget_reservation_receipt_id,
                        "egress_authorization_receipt_id": authorization.egress_authorization_receipt_id,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            ).encode()
            artifact = self._voice_prepared_artifact(
                request.attempt_id, paths.submit_intent_path, intent_payload
            )
            r1_artifacts = self._reopen_voice_evidence(request.attempt_id, include_intent=False)
            expected_r1 = (
                self._voice_prepared_artifact(
                    request.attempt_id, paths.request_path, _canonical_json_bytes(request)
                ),
                self._voice_prepared_artifact(
                    request.attempt_id, paths.preview_path, _canonical_json_bytes(preview)
                ),
                self._voice_prepared_artifact(
                    request.attempt_id,
                    paths.authorization_path,
                    _canonical_json_bytes(authorization),
                ),
            )
            if (
                r1_artifacts != expected_r1
                or _candidate_artifacts_hash(r1_artifacts)
                != attempt.candidate_artifacts_hash
            ):
                raise _state_invalid("Voice R+1 evidence changed before submit intent.")
            self._write_immutable_artifact(artifact, attempt_id=request.attempt_id)
            aggregate = _candidate_artifacts_hash((*r1_artifacts, artifact))
            r2_attempt = _validated_transition(
                attempt,
                {
                    "voice_phase": "submit_intent",
                    "candidate_artifacts_hash": aggregate,
                },
            )
            r2 = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        r2_attempt if item.attempt_id == request.attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(r2)
            reopened = self._read_manifest()
            reopened_attempt = next(
                item for item in reopened.attempts if item.attempt_id == request.attempt_id
            )
            if (
                reopened_attempt.voice_phase != "submit_intent"
                or reopened_attempt.candidate_artifacts_hash != aggregate
            ):
                raise _state_commit_failed("Voice submit intent reopen verification failed.")
            intent_snapshot = _read_regular_file_nofollow(
                paths.submit_intent_path,
                contained_by=self._project_root,
            )
            if (
                intent_snapshot.data != intent_payload
                or intent_snapshot.file_sha256 != artifact.file_sha256
            ):
                raise _state_commit_failed("Voice submit intent exact-byte verification failed.")
            manifest_snapshot = _read_regular_file_nofollow(
                self._project_root / "state/manifest.json",
                contained_by=self._project_root,
            )
            self._crash_injector.checkpoint(CommitPhase.AFTER_VOICE_SUBMIT_INTENT)
            binding = {
                "attempt_id": request.attempt_id,
                "request_fingerprint": request.voice_request_fingerprint,
                "authorization_fingerprint": authorization.authorization_fingerprint,
                "destination": authorization.destination,
                "budget_reservation_receipt_id": authorization.budget_reservation_receipt_id,
                "egress_authorization_receipt_id": authorization.egress_authorization_receipt_id,
            }
            return _DurableVoiceSubmitPermit(
                _VOICE_PERMIT_TOKEN,
                binding=binding,
                manifest_revision=reopened.manifest_revision,
                manifest_file_sha256=manifest_snapshot.file_sha256,
                durability_validator=lambda: self._voice_submit_intent_is_current(
                    reopened.manifest_revision,
                    manifest_snapshot.file_sha256,
                    request.attempt_id,
                    aggregate,
                    artifact.file_sha256,
                    intent_payload,
                ),
            )

    def _reopen_voice_evidence(
        self, attempt_id: str, *, include_intent: bool
    ) -> tuple[PreparedArtifact, ...]:
        paths = self.voice_attempt_paths(attempt_id)
        selected = [paths.request_path, paths.preview_path, paths.authorization_path]
        if include_intent:
            selected.append(paths.submit_intent_path)
        artifacts = []
        for path in selected:
            snapshot = _read_regular_file_nofollow(path, contained_by=self._project_root)
            artifacts.append(
                PreparedArtifact(
                    relative_path=path.relative_to(self._project_root),
                    payload=snapshot.data,
                    file_sha256=snapshot.file_sha256,
                )
            )
        return tuple(artifacts)

    def _voice_submit_intent_is_current(
        self,
        manifest_revision: int,
        manifest_file_sha256: str,
        attempt_id: str,
        aggregate_hash: str,
        intent_sha256: str,
        intent_payload: bytes,
    ) -> bool:
        try:
            snapshot = _read_regular_file_nofollow(
                self._project_root / "state/manifest.json",
                contained_by=self._project_root,
            )
            if snapshot.file_sha256 != manifest_file_sha256:
                return False
            manifest = ProductionManifest.model_validate_json(snapshot.data)
            evidence = self._reopen_voice_evidence(attempt_id, include_intent=True)
        except (AiVideoError, OSError, ValidationError, ValueError):
            return False
        attempt = next(
            (item for item in manifest.attempts if item.attempt_id == attempt_id), None
        )
        return (
            manifest.manifest_revision == manifest_revision
            and attempt is not None
            and attempt.operation == "voice_generation"
            and attempt.status is StateCommitStatus.RUNNING
            and attempt.voice_phase == "submit_intent"
            and attempt.candidate_artifacts_hash == aggregate_hash
            and _candidate_artifacts_hash(evidence) == aggregate_hash
            and evidence[-1].file_sha256 == intent_sha256
            and evidence[-1].payload == intent_payload
        )

    def _record_voice_terminal(
        self,
        attempt_id: str,
        *,
        status: StateCommitStatus,
        phase: Literal[
            "request",
            "submit_intent",
            "provider_call",
            "materialize",
            "probe",
            "align",
            "candidate",
            "activate",
        ],
        error_code: str,
        error_message: str,
    ) -> ProductionManifest:
        if status not in {StateCommitStatus.FAILED, StateCommitStatus.OUTCOME_UNKNOWN}:
            raise _state_invalid("Voice terminal transition status is invalid.")
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = next(
                (item for item in manifest.attempts if item.attempt_id == attempt_id), None
            )
            stable_message = _stable_voice_terminal_message(status, phase)
            if attempt is None or attempt.operation != "voice_generation":
                raise _state_invalid("Voice terminal transition has no matching attempt.")
            if attempt.status is status:
                if (
                    attempt.voice_phase == phase
                    and attempt.error_code == error_code
                    and attempt.error_message == stable_message
                ):
                    return manifest
                raise _state_invalid("Voice terminal replay does not match durable state.")
            if attempt.status is not StateCommitStatus.RUNNING:
                raise _state_invalid("Voice terminal transition is stale.")
            terminal_attempt = _validated_transition(
                attempt,
                {
                    "status": status,
                    "voice_phase": phase,
                    "finished_at": _timestamp(),
                    "error_code": error_code,
                    "error_message": stable_message,
                },
            )
            terminal = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        terminal_attempt if item.attempt_id == attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(terminal)
            return self._read_manifest()

    def record_voice_failure(
        self,
        attempt_id: str,
        *,
        phase: Literal[
            "request", "submit_intent", "provider_call", "materialize", "probe", "align", "candidate", "activate"
        ],
        error_code: str,
        error_message: str,
    ) -> ProductionManifest:
        return self._record_voice_terminal(
            attempt_id,
            status=StateCommitStatus.FAILED,
            phase=phase,
            error_code=error_code,
            error_message=error_message,
        )

    def record_voice_outcome_unknown(
        self,
        attempt_id: str,
        *,
        phase: Literal[
            "submit_intent", "provider_call", "materialize", "probe", "align", "candidate", "activate"
        ],
        error_code: str = ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN.value,
        error_message: str = "Voice provider outcome is unknown; blind retry is forbidden.",
    ) -> ProductionManifest:
        return self._record_voice_terminal(
            attempt_id,
            status=StateCommitStatus.OUTCOME_UNKNOWN,
            phase=phase,
            error_code=error_code,
            error_message=error_message,
        )

    @staticmethod
    def _validate_voice_provider_result(
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
        result: VoiceProviderResult,
    ) -> None:
        if not isinstance(result, VoiceProviderResult):
            raise _state_invalid("Voice provider returned an untyped result.")
        if (
            result.request_id != request.request_id
            or result.request_fingerprint != request.voice_request_fingerprint
            or result.preview_fingerprint != preview.preview_fingerprint
            or result.authorization_fingerprint
            != authorization.authorization_fingerprint
            or result.content_type not in {"audio/wav", "audio/x-wav"}
            or result.cost_receipt.pricing_snapshot_id
            != request.pricing_snapshot_id
            or result.cost_receipt.estimated_cost_upper_bound_microunits
            != preview.estimated_cost_upper_bound_microunits
            or (
                result.cost_receipt.provider_reported_cost_microunits is not None
                and result.cost_receipt.provider_reported_cost_microunits
                > authorization.cost_ceiling_microunits
            )
            or result.provenance_receipt.provider_kind != request.provider_kind
            or result.provenance_receipt.model_id != request.model_id
            or result.provenance_receipt.voice_id != request.voice_id
            or result.provenance_receipt.language != request.language
            or result.provenance_receipt.script_hash != request.script_hash
            or result.provenance_receipt.egress_authorization_receipt_id
            != request.egress_authorization_receipt_id
        ):
            raise _state_invalid(
                "Voice provider result contradicts request, preview, authorization, or receipts."
            )
