"""Local (loopback ComfyUI) video lifecycle: submit intent/result, status and fetch.

Split from ``_state_commit_video`` without behavior change; the canonical writer
remains ``ProductionStateCommitter``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from ai_video.errors import ErrorCode
from ai_video.production._lifecycle_schema import (
    LocalVideoFetchReceiptPointer,
    LocalVideoStatusReceiptPointer,
    LocalVideoSubmitIntentPointer,
    LocalVideoSubmitReceiptPointer,
)
from ai_video.production.local_video import (
    LocalVideoFetchReceipt,
    LocalVideoSubmission,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
    LocalVideoTaskObservation,
)
from ai_video.production.models import ProductionManifest, StateCommitStatus, VideoAttemptPhase
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_local_video_fetch_receipt_path,
    canonical_local_video_status_receipt_path,
    canonical_local_video_submit_intent_path,
    canonical_local_video_submit_receipt_path,
    canonical_video_fetch_artifact_path,
)
from ai_video.production.video import ResolvedVideoGenerationRequest, VideoTaskState

from ._state_commit_common import _state_invalid, _timestamp, _validated_transition
from ._state_commit_contracts import (
    PreparedArtifact,
    _DurableLocalVideoSubmitPermit,
    _LOCAL_VIDEO_PERMIT_TOKEN,
)
from ._state_commit_video import _artifact


class _StateCommitLocalVideoMixin:
    def record_local_video_submit_intent(
        self,
        *,
        attempt_id: str,
        preview,
        pre_submit_guard: (
            Callable[[ResolvedVideoGenerationRequest], None] | None
        ) = None,
    ) -> tuple[LocalVideoSubmitIntent, _DurableLocalVideoSubmitPermit]:
        """Persist intent; the optional in-lock guard must be read-only/non-reentrant."""

        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._video_attempt(manifest, attempt_id)
            state = attempt.video_generation_state
            if (
                attempt.status is not StateCommitStatus.RUNNING
                or state is None
                or state.phase is not VideoAttemptPhase.REQUEST
                or attempt.paid_provider_state is not None
            ):
                raise _state_invalid("Local video submit is not the next durable action.")
            request = self._reopen_video_request(state.request)
            _binding, runtime_repair = self._require_submit_execution_binding(
                manifest, state, request
            )
            if state.qualification_binding is not None and pre_submit_guard is None:
                raise _state_invalid(
                    "Qualification local submit requires its exact closure guard."
                )
            if request.execution_stack_hash is not None and pre_submit_guard is None:
                raise _state_invalid(
                    "Stack-bound local video submit requires a pre-submit guard."
                )
            if pre_submit_guard is not None:
                pre_submit_guard(request)
            try:
                intent = LocalVideoSubmitIntent.create(
                    attempt_id=attempt_id,
                    request=request,
                    preview=preview,
                    recorded_at=self._paid_provider_clock(),
                )
            except ValueError as exc:
                raise _state_invalid("Local video preview is invalid.", str(exc)) from exc
            artifact = _artifact(
                canonical_local_video_submit_intent_path(intent.intent_fingerprint),
                intent,
            )
            pointer = LocalVideoSubmitIntentPointer(
                path=artifact.relative_path,
                intent_fingerprint=intent.intent_fingerprint,
                request_fingerprint=request.resolved_generation_hash,
                file_sha256=artifact.file_sha256,
            )
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            next_state = state.model_copy(
                update={
                    "phase": VideoAttemptPhase.SUBMIT_INTENT,
                    "local_submit_intent": pointer,
                }
            )
            next_attempt = _validated_transition(
                attempt, {"video_generation_state": next_state}
            )
            from ._state_commit_video_runtime_repair import submit_attempts_with_consumed_repair

            attempts = submit_attempts_with_consumed_repair(manifest, next_attempt, runtime_repair)
            next_manifest = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(attempts),
                },
            )
            self._write_manifest_atomic(next_manifest)
            self._reopen_local_video_submit_intent(pointer)

        def durable() -> bool:
            try:
                current = self._read_manifest()
                current_attempt = self._video_attempt(current, attempt_id)
                current_state = current_attempt.video_generation_state
                if (
                    current_attempt.status is not StateCommitStatus.RUNNING
                    or current_state is None
                    or current_state.phase is not VideoAttemptPhase.SUBMIT_INTENT
                    or current_state.local_submit_intent != pointer
                    or current_attempt.paid_provider_state is not None
                ):
                    return False
                return (
                    self._reopen_local_video_submit_intent(pointer).intent_fingerprint
                    == intent.intent_fingerprint
                )
            except Exception:
                return False

        permit = _DurableLocalVideoSubmitPermit(
            _LOCAL_VIDEO_PERMIT_TOKEN,
            binding={
                "intent_fingerprint": intent.intent_fingerprint,
                "request_fingerprint": request.resolved_generation_hash,
            },
            durability_validator=durable,
        )
        return intent, permit

    def record_local_video_submit_result(
        self,
        *,
        attempt_id: str,
        result: LocalVideoSubmitResult,
    ) -> ProductionManifest:
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._video_attempt(manifest, attempt_id)
            state = attempt.video_generation_state
            if (
                attempt.status is not StateCommitStatus.RUNNING
                or state is None
                or state.phase is not VideoAttemptPhase.SUBMIT_INTENT
                or state.local_submit_intent is None
                or attempt.paid_provider_state is not None
            ):
                raise _state_invalid("Local video submit result has no durable intent.")
            request = self._reopen_video_request(state.request)
            intent = self._reopen_local_video_submit_intent(
                state.local_submit_intent
            )
            if (
                result.generation_id != request.generation_id
                or result.resolved_generation_hash != request.resolved_generation_hash
                or intent.request_fingerprint != result.resolved_generation_hash
            ):
                raise _state_invalid("Local video submit result identity is invalid.")
            try:
                LocalVideoSubmission.from_submit_result(
                    resolved=request, result=result
                )
            except ValueError as exc:
                raise _state_invalid("Local video submission is invalid.", str(exc)) from exc
            artifact = _artifact(
                canonical_local_video_submit_receipt_path(result.result_fingerprint),
                result,
            )
            pointer = LocalVideoSubmitReceiptPointer(
                path=artifact.relative_path,
                result_fingerprint=result.result_fingerprint,
                request_fingerprint=result.resolved_generation_hash,
                provider_request_id=result.provider_request_id,
                file_sha256=artifact.file_sha256,
            )
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            next_state = state.model_copy(
                update={
                    "phase": VideoAttemptPhase.SUBMITTED,
                    "local_submit_receipt": pointer,
                }
            )
            next_attempt = _validated_transition(
                attempt, {"video_generation_state": next_state}
            )
            next_manifest = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        next_attempt if item.attempt_id == attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(next_manifest)
            self._reopen_local_video_submit(pointer)
            return self._read_manifest()

    def record_local_video_status_observation(
        self,
        *,
        attempt_id: str,
        observation: LocalVideoTaskObservation,
    ) -> ProductionManifest:
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._video_attempt(manifest, attempt_id)
            state = attempt.video_generation_state
            if (
                attempt.status is not StateCommitStatus.RUNNING
                or state is None
                or state.phase
                not in {VideoAttemptPhase.SUBMITTED, VideoAttemptPhase.POLLING}
                or state.local_submit_receipt is None
                or attempt.paid_provider_state is not None
            ):
                raise _state_invalid("Local video status requires a durable submission.")
            request = self._reopen_video_request(state.request)
            result = self._reopen_local_video_submit(state.local_submit_receipt)
            submission = LocalVideoSubmission.from_submit_result(
                resolved=request, result=result
            )
            if (
                observation.submission_fingerprint
                != submission.submission_fingerprint
                or observation.submit_result_fingerprint != result.result_fingerprint
            ):
                raise _state_invalid("Local video observation identity is invalid.")
            artifact = _artifact(
                canonical_local_video_status_receipt_path(
                    observation.observation_fingerprint
                ),
                observation,
            )
            pointer = LocalVideoStatusReceiptPointer(
                path=artifact.relative_path,
                observation_fingerprint=observation.observation_fingerprint,
                request_receipt_fingerprint=state.request.request_receipt_fingerprint,
                submit_result_fingerprint=result.result_fingerprint,
                file_sha256=artifact.file_sha256,
            )
            if state.local_latest_observation == pointer:
                return manifest
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            terminal_failure = observation.state is VideoTaskState.FAILED
            next_state = state.model_copy(
                update={
                    "phase": (
                        VideoAttemptPhase.FETCH
                        if observation.state is VideoTaskState.SUCCEEDED
                        else VideoAttemptPhase.POLLING
                    ),
                    "local_latest_observation": pointer,
                    "provider_file_id": observation.provider_file_id,
                }
            )
            attempt_update: dict[str, object] = {
                "video_generation_state": next_state
            }
            if terminal_failure:
                attempt_update.update(
                    status=StateCommitStatus.FAILED,
                    finished_at=_timestamp(),
                    error_code=ErrorCode.VIDEO_PROVIDER_FAILED.value,
                    error_message="Local video runtime reported terminal failure.",
                )
            next_attempt = _validated_transition(attempt, attempt_update)
            next_manifest = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        next_attempt if item.attempt_id == attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(next_manifest)
            self._reopen_local_video_status(pointer)
            return self._read_manifest()

    def record_local_video_fetch_result(
        self,
        *,
        attempt_id: str,
        temporary_path: Path,
        receipt: LocalVideoFetchReceipt,
    ) -> LocalVideoFetchReceiptPointer:
        """Promote exact local bytes and receipt before shared validation."""

        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._video_attempt(manifest, attempt_id)
            state = attempt.video_generation_state
            if (
                attempt.status is not StateCommitStatus.RUNNING
                or state is None
                or state.phase is not VideoAttemptPhase.FETCH
                or state.local_latest_observation is None
                or state.local_submit_receipt is None
                or attempt.paid_provider_state is not None
            ):
                raise _state_invalid(
                    "Local video fetch result requires the exact durable fetch phase."
                )
            observation = self._reopen_local_video_status(
                state.local_latest_observation
            )
            if (
                observation.state is not VideoTaskState.SUCCEEDED
                or receipt.observation_fingerprint
                != observation.observation_fingerprint
                or receipt.submit_result_fingerprint
                != state.local_submit_receipt.result_fingerprint
                or receipt.provider_file_id != observation.provider_file_id
            ):
                raise _state_invalid(
                    "Local video fetch receipt does not match the durable task."
                )
            try:
                snapshot = _read_regular_file_nofollow(
                    self._project_root / temporary_path,
                    contained_by=(
                        self._project_root / "state" / "video-generation" / "fetch"
                    ),
                )
            except (OSError, ValueError) as exc:
                raise _state_invalid("Fetched local video path is unsafe.", str(exc)) from exc
            if (
                snapshot.file_sha256 != receipt.artifact_sha256
                or snapshot.size_bytes != receipt.size_bytes
            ):
                raise _state_invalid("Fetched local video bytes do not match receipt.")
            artifact_path = canonical_video_fetch_artifact_path(
                receipt.artifact_sha256
            )
            artifact = PreparedArtifact(
                relative_path=artifact_path,
                payload=snapshot.data,
                file_sha256=snapshot.file_sha256,
            )
            receipt_artifact = _artifact(
                canonical_local_video_fetch_receipt_path(
                    receipt.fetch_fingerprint
                ),
                receipt,
            )
            for prepared in (artifact, receipt_artifact):
                self._write_immutable_artifact(prepared, attempt_id=attempt_id)
            pointer = LocalVideoFetchReceiptPointer(
                path=receipt_artifact.relative_path,
                fetch_fingerprint=receipt.fetch_fingerprint,
                artifact_path=artifact_path,
                artifact_sha256=receipt.artifact_sha256,
                artifact_size_bytes=receipt.size_bytes,
                file_sha256=receipt_artifact.file_sha256,
            )
            self._reopen_local_video_fetch(pointer)
            next_state = state.model_copy(
                update={
                    "phase": VideoAttemptPhase.VALIDATE,
                    "local_fetch_receipt": pointer,
                }
            )
            next_attempt = _validated_transition(
                attempt, {"video_generation_state": next_state}
            )
            next_manifest = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        next_attempt if item.attempt_id == attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(next_manifest)
            try:
                (self._project_root / temporary_path).unlink(missing_ok=True)
            except OSError:
                pass
            return pointer
