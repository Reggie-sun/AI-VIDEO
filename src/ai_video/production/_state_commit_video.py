from __future__ import annotations

import hashlib
import os
import re
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._lifecycle_schema import (
    LocalVideoFetchReceiptPointer,
    LocalVideoStatusReceiptPointer,
    LocalVideoSubmitIntentPointer,
    LocalVideoSubmitReceiptPointer,
)
from ai_video.production._image_project_reader import (
    verify_hard_cut_keyframe_evidence,
)
from ai_video.production._video_project_reader import (
    load_local_video_fetch_receipt,
    load_local_video_status_receipt,
    load_local_video_submit_intent,
    load_local_video_submit_receipt,
    load_video_fetch_receipt,
    load_video_request_receipt,
    load_video_status_receipt,
    load_terminal_frame_evidence,
    load_terminal_frame_extraction,
    load_continuity_evaluation_intent,
    load_generated_shot_continuity_evidence,
    load_video_probe_receipt,
    load_video_provenance_receipt,
)
from ai_video.production.models import (
    PaidProviderAttemptPhase,
    ProductionManifest,
    StateCommitAttempt,
    StateCommitStatus,
    VideoAttemptPhase,
    VideoFetchReceiptPointer,
    VideoGenerationAttemptState,
    VideoRequestReceiptPointer,
    VideoStatusReceiptPointer,
    TerminalFrameEvidencePointer,
    TerminalFrameExtractionReceiptPointer,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_local_video_fetch_receipt_path,
    canonical_local_video_status_receipt_path,
    canonical_local_video_submit_intent_path,
    canonical_local_video_submit_receipt_path,
    canonical_video_fetch_artifact_path,
    canonical_video_fetch_receipt_path,
    canonical_video_request_receipt_path,
    canonical_video_status_receipt_path,
)
from ai_video.production.local_video import (
    LocalVideoFetchReceipt,
    LocalVideoSubmission,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
    LocalVideoTaskObservation,
)
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoFetchReceipt,
    VideoSubmission,
    VideoTaskObservation,
    VideoTaskState,
)

from ._state_commit_common import (
    _candidate_artifacts_hash,
    _canonical_json_bytes,
    _state_invalid,
    _timestamp,
    _validated_transition,
)
from ._state_commit_contracts import (
    PreparedArtifact,
    _DurableLocalVideoSubmitPermit,
    _LOCAL_VIDEO_PERMIT_TOKEN,
)


_SAFE_ATTEMPT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _artifact(path: Path, model: object) -> PreparedArtifact:
    payload = _canonical_json_bytes(model)  # type: ignore[arg-type]
    return PreparedArtifact(
        relative_path=path,
        payload=payload,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )


class _StateCommitVideoMixin:
    def _video_attempt(
        self, manifest: ProductionManifest, attempt_id: str
    ) -> StateCommitAttempt:
        attempt = next(
            (item for item in manifest.attempts if item.attempt_id == attempt_id),
            None,
        )
        if attempt is None or attempt.operation != "video_generation":
            raise _state_invalid("Video generation attempt does not exist.")
        return attempt

    def _reopen_video_request(
        self, pointer: VideoRequestReceiptPointer
    ) -> ResolvedVideoGenerationRequest:
        return load_video_request_receipt(self._project_root, pointer)

    def _reopen_video_status(
        self, pointer: VideoStatusReceiptPointer
    ) -> VideoTaskObservation:
        return load_video_status_receipt(self._project_root, pointer)

    def _reopen_video_fetch(
        self, pointer: VideoFetchReceiptPointer
    ) -> VideoFetchReceipt:
        return load_video_fetch_receipt(self._project_root, pointer)

    def _reopen_local_video_submit_intent(self, pointer):
        return load_local_video_submit_intent(self._project_root, pointer)

    def _reopen_local_video_submit(self, pointer):
        return load_local_video_submit_receipt(self._project_root, pointer)

    def _reopen_local_video_status(self, pointer):
        return load_local_video_status_receipt(self._project_root, pointer)

    def _reopen_local_video_fetch(self, pointer):
        return load_local_video_fetch_receipt(self._project_root, pointer)

    def _reopen_terminal_frame_evidence(
        self, pointer: TerminalFrameEvidencePointer
    ):
        return load_terminal_frame_evidence(self._project_root, pointer)

    def _reopen_terminal_frame_extraction(
        self, pointer: TerminalFrameExtractionReceiptPointer
    ):
        return load_terminal_frame_extraction(self._project_root, pointer)

    def _reopen_continuity_evaluation_intent(self, pointer):
        return load_continuity_evaluation_intent(self._project_root, pointer)

    def _reopen_generated_shot_continuity_evidence(self, pointer):
        return load_generated_shot_continuity_evidence(self._project_root, pointer)

    def _reopen_video_probe_receipt(self, pointer):
        return load_video_probe_receipt(self._project_root, pointer)

    def _reopen_video_provenance_receipt(self, pointer):
        return load_video_provenance_receipt(self._project_root, pointer)

    def _reopen_terminal_frame_chain(
        self,
        state: VideoGenerationAttemptState,
        request: ResolvedVideoGenerationRequest,
        *,
        source_registry,
    ):
        scope = request.activation_scope
        if scope is None:
            raise _state_invalid("Video request has no durable authoring scope.")
        expected_ids = (
            (f"{request.output_asset_id}:terminal-frame",)
            if scope.request.seal_terminal_frame
            else ()
        )
        if not expected_ids:
            if (
                state.terminal_frame_extraction is not None
                or state.terminal_frame_evidence is not None
                or state.candidate_continuity_asset_ids
            ):
                raise _state_invalid("Unexpected terminal frame state is present.")
            return None
        if (
            state.terminal_frame_extraction is None
            or state.terminal_frame_evidence is None
            or state.candidate_continuity_asset_ids != expected_ids
        ):
            raise _state_invalid("Terminal frame evidence chain is incomplete.")
        _, extraction = self._reopen_terminal_frame_extraction(
            state.terminal_frame_extraction
        )
        evidence = self._reopen_terminal_frame_evidence(
            state.terminal_frame_evidence
        )
        if (
            evidence.extraction_receipt_id != extraction.content_hash
            or evidence.source_registry != source_registry
            or evidence.source_shot_id != scope.request.target_shot_id
            or evidence.source_shot_revision != scope.request.target_shot_revision
            or evidence.source_shot_content_hash
            != scope.request.target_shot_content_hash
            or evidence.source_video_asset_id != request.output_asset_id
            or evidence.source_generation_id != request.generation_id
            or evidence.source_request_input_hash != request.request_input_hash
            or evidence.source_resolved_generation_hash
            != request.resolved_generation_hash
            or evidence.extracted_asset_id not in expected_ids
        ):
            raise _state_invalid(
                "Terminal frame evidence does not bind the exact candidate."
            )
        return evidence

    def begin_video_generation(
        self,
        *,
        attempt_id: str,
        request: ResolvedVideoGenerationRequest,
    ) -> ProductionManifest:
        """Persist the exact resolved request before any Paid Gate action."""

        if _SAFE_ATTEMPT_ID.fullmatch(attempt_id) is None:
            raise _state_invalid("Video generation attempt ID is invalid.")
        artifact = _artifact(
            canonical_video_request_receipt_path(
                request.desired_generation_fingerprint
            ),
            request,
        )
        pointer = VideoRequestReceiptPointer(
            path=artifact.relative_path,
            request_receipt_fingerprint=request.desired_generation_fingerprint,
            generation_id=request.generation_id,
            request_input_hash=request.request_input_hash,
            resolved_generation_hash=request.resolved_generation_hash,
            output_asset_id=request.output_asset_id,
            file_sha256=artifact.file_sha256,
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if manifest.schema_version not in {"2.7", "2.8", "2.9", "2.10"}:
                raise _state_invalid(
                    "Video generation requires Production Manifest 2.7 or later."
                )
            if (
                request.activation_scope is not None
                and (
                    request.activation_scope.request.seal_terminal_frame
                    or request.continuity_binding is not None
                    or request.hard_cut_keyframe_binding is not None
                )
                and request.continuity_binding is not None
                and manifest.schema_version not in {"2.9", "2.10"}
            ):
                raise _state_invalid(
                    "Evaluated Shot continuity requires Production Manifest 2.9 or later."
                )
            if (
                request.activation_scope is not None
                and (
                    request.activation_scope.request.seal_terminal_frame
                    or request.hard_cut_keyframe_binding is not None
                )
                and request.continuity_binding is None
                and manifest.schema_version not in {"2.8", "2.9", "2.10"}
            ):
                raise _state_invalid("Shot continuity artifacts require Manifest 2.8 or later.")
            if request.hard_cut_keyframe_binding is not None:
                try:
                    loaded = self._load_production_project(
                        self._project_root / "project.yaml"
                    )
                    if loaded.manifest != manifest or request.activation_scope is None:
                        raise ValueError(
                            "active project changed during hard-cut validation"
                        )
                    verify_hard_cut_keyframe_evidence(
                        loaded,
                        request,
                        require_active_base=True,
                    )
                except (AiVideoError, OSError, ValueError) as exc:
                    raise _state_invalid(
                        "Hard-cut keyframe lineage is not active or exact.", str(exc)
                    ) from exc
            if manifest.active_dependency_graph is None:
                raise _state_invalid(
                    "Video generation requires an active dependency graph."
                )
            if any(
                item.attempt_id == attempt_id
                or (
                    item.video_generation_state is not None
                    and item.video_generation_state.generation_id
                    == request.generation_id
                )
                for item in manifest.attempts
            ):
                raise _state_invalid("Video generation identity is already owned.")
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            attempt = StateCommitAttempt(
                attempt_id=attempt_id,
                operation="video_generation",
                status=StateCommitStatus.RUNNING,
                base_manifest_revision=manifest.manifest_revision,
                base_project=manifest.active_project,
                base_registry=manifest.active_registry,
                base_dependency_graph=manifest.active_dependency_graph,
                candidate_artifacts_hash=_candidate_artifacts_hash((artifact,)),
                video_generation_state=VideoGenerationAttemptState(
                    request=pointer,
                    generation_id=request.generation_id,
                    resolved_generation_hash=request.resolved_generation_hash,
                    phase=VideoAttemptPhase.REQUEST,
                ),
                started_at=_timestamp(),
            )
            next_manifest = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": (*manifest.attempts, attempt),
                },
            )
            self._write_manifest_atomic(next_manifest)
            self._reopen_video_request(pointer)
            return self._read_manifest()

    def record_local_video_submit_intent(
        self,
        *,
        attempt_id: str,
        preview,
    ) -> tuple[LocalVideoSubmitIntent, _DurableLocalVideoSubmitPermit]:
        """Persist the exact local call intent before submitting to ComfyUI."""

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

    def record_video_status_observation(
        self,
        *,
        attempt_id: str,
        observation: VideoTaskObservation,
    ) -> ProductionManifest:
        """Persist one normalized poll result without exposing a submit path."""

        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._video_attempt(manifest, attempt_id)
            state = attempt.video_generation_state
            paid_state = attempt.paid_provider_state
            if (
                attempt.status is not StateCommitStatus.RUNNING
                or state is None
                or paid_state is None
                or paid_state.phase
                not in {
                    PaidProviderAttemptPhase.ACCEPTED,
                    PaidProviderAttemptPhase.SETTLED,
                }
                or paid_state.submit_receipt is None
            ):
                raise _state_invalid(
                    "Video status requires an exact accepted Paid Provider task."
                )
            request = self._reopen_video_request(state.request)
            submit_receipt = self._reopen_paid_submit(paid_state.submit_receipt)
            try:
                submission = VideoSubmission.from_paid_submit_receipt(
                    resolved=request,
                    receipt=submit_receipt,
                )
            except Exception as exc:
                raise _state_invalid(
                    "Video submission could not be reconstructed.", str(exc)
                ) from exc
            if (
                observation.submission_fingerprint
                != submission.submission_fingerprint
                or observation.paid_submit_receipt_fingerprint
                != submit_receipt.submit_receipt_fingerprint
            ):
                raise _state_invalid(
                    "Video observation does not match the durable submission."
                )
            artifact = _artifact(
                canonical_video_status_receipt_path(
                    observation.observation_fingerprint
                ),
                observation,
            )
            pointer = VideoStatusReceiptPointer(
                path=artifact.relative_path,
                observation_fingerprint=observation.observation_fingerprint,
                request_receipt_fingerprint=state.request.request_receipt_fingerprint,
                paid_submit_receipt_fingerprint=(
                    submit_receipt.submit_receipt_fingerprint
                ),
                file_sha256=artifact.file_sha256,
            )
            if state.latest_observation == pointer:
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
                    "latest_observation": pointer,
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
                    error_message="Video Provider reported terminal generation failure.",
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
            self._reopen_video_status(pointer)
            return self._read_manifest()

    def record_video_provider_failure(
        self,
        *,
        attempt_id: str,
        error_code: ErrorCode,
        message: str,
    ) -> ProductionManifest:
        if error_code not in {
            ErrorCode.VIDEO_PROVIDER_FAILED,
            ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
        }:
            raise _state_invalid("Video failure requires a video Provider error code.")
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._video_attempt(manifest, attempt_id)
            if attempt.status is not StateCommitStatus.RUNNING:
                raise _state_invalid("Video attempt is not running.")
            next_attempt = _validated_transition(
                attempt,
                {
                    "status": (
                        StateCommitStatus.OUTCOME_UNKNOWN
                        if error_code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
                        else StateCommitStatus.FAILED
                    ),
                    "finished_at": _timestamp(),
                    "error_code": error_code.value,
                    "error_message": message,
                },
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
            return self._read_manifest()

    def video_resume_next_action(self, *, attempt_id: str) -> str:
        manifest = self._read_manifest()
        attempt = self._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if state is None:
            raise _state_invalid("Video generation state is missing.")
        if attempt.status in {
            StateCommitStatus.FAILED,
            StateCommitStatus.OUTCOME_UNKNOWN,
            StateCommitStatus.INTERRUPTED,
        }:
            return "stop"
        return {
            VideoAttemptPhase.REQUEST: "submit",
            VideoAttemptPhase.SUBMIT_INTENT: "stop",
            VideoAttemptPhase.SUBMITTED: "poll",
            VideoAttemptPhase.POLLING: "poll",
            VideoAttemptPhase.FETCH: "fetch",
            VideoAttemptPhase.VALIDATE: "validate",
            VideoAttemptPhase.CANDIDATE: "activate",
            VideoAttemptPhase.ACTIVATE: "done",
        }[state.phase]

    def record_video_fetch_result(
        self,
        *,
        attempt_id: str,
        temporary_path: Path,
        receipt: VideoFetchReceipt,
    ) -> VideoFetchReceiptPointer:
        """Promote exact fetched bytes and receipt before local validation."""

        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._video_attempt(manifest, attempt_id)
            state = attempt.video_generation_state
            if (
                attempt.status is not StateCommitStatus.RUNNING
                or state is None
                or state.phase is not VideoAttemptPhase.FETCH
                or state.latest_observation is None
                or state.paid_submit_receipt is None
            ):
                raise _state_invalid(
                    "Video fetch result requires the exact durable fetch phase."
                )
            observation = self._reopen_video_status(state.latest_observation)
            if (
                observation.state is not VideoTaskState.SUCCEEDED
                or receipt.observation_fingerprint
                != observation.observation_fingerprint
                or receipt.paid_submit_receipt_fingerprint
                != state.paid_submit_receipt.submit_receipt_fingerprint
                or receipt.provider_file_id != observation.provider_file_id
            ):
                raise _state_invalid(
                    "Video fetch receipt does not match the durable succeeded task."
                )
            try:
                snapshot = _read_regular_file_nofollow(
                    self._project_root / temporary_path,
                    contained_by=(
                        self._project_root / "state" / "video-generation" / "fetch"
                    ),
                )
            except (OSError, ValueError) as exc:
                raise _state_invalid("Fetched video path is unsafe.", str(exc)) from exc
            if (
                snapshot.file_sha256 != receipt.artifact_sha256
                or snapshot.size_bytes != receipt.size_bytes
            ):
                raise _state_invalid(
                    "Fetched video bytes do not match the Provider receipt."
                )
            artifact_path = canonical_video_fetch_artifact_path(
                receipt.artifact_sha256
            )
            artifact = PreparedArtifact(
                relative_path=artifact_path,
                payload=snapshot.data,
                file_sha256=snapshot.file_sha256,
            )
            receipt_artifact = _artifact(
                canonical_video_fetch_receipt_path(receipt.fetch_fingerprint),
                receipt,
            )
            for prepared in (artifact, receipt_artifact):
                self._write_immutable_artifact(prepared, attempt_id=attempt_id)
            pointer = VideoFetchReceiptPointer(
                path=receipt_artifact.relative_path,
                fetch_fingerprint=receipt.fetch_fingerprint,
                artifact_path=artifact_path,
                artifact_sha256=receipt.artifact_sha256,
                artifact_size_bytes=receipt.size_bytes,
                file_sha256=receipt_artifact.file_sha256,
            )
            self._reopen_video_fetch(pointer)
            next_state = state.model_copy(
                update={
                    "phase": VideoAttemptPhase.VALIDATE,
                    "fetch_receipt": pointer,
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

    @contextmanager
    def prepare_video_fetch_sink(
        self, *, attempt_id: str
    ) -> Iterator[tuple[Path, BinaryIO]]:
        """Open a held-FD task-owned temporary MP4 for one bounded fetch."""

        manifest = self._read_manifest()
        attempt = self._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        observation = None
        if state is not None:
            pointer = state.local_latest_observation or state.latest_observation
            if pointer is not None:
                observation = (
                    self._reopen_local_video_status(pointer)
                    if state.local_latest_observation is not None
                    else self._reopen_video_status(pointer)
                )
        if (
            attempt.status is not StateCommitStatus.RUNNING
            or state is None
            or state.phase is not VideoAttemptPhase.FETCH
            or observation is None
            or observation.state is not VideoTaskState.SUCCEEDED
        ):
            raise _state_invalid("Video fetch requires a durable succeeded observation.")
        fetch_root = self._project_root / "state" / "video-generation" / "fetch"
        current = self._project_root / "state"
        for part in ("video-generation", "fetch"):
            current = current / part
            if current.exists() and current.is_symlink():
                raise _state_invalid("Video fetch directory cannot be a symlink.")
            current.mkdir(mode=0o700, exist_ok=True)
        fd, raw_path = tempfile.mkstemp(
            prefix=f"{attempt_id}.",
            suffix=".mp4.part",
            dir=fetch_root,
        )
        temporary_path = Path(raw_path)
        final_path = temporary_path.with_suffix("")
        handle = os.fdopen(fd, "w+b")
        try:
            yield final_path.relative_to(self._project_root), handle
            handle.flush()
            os.fsync(handle.fileno())
            handle.close()
            self._ops.replace(temporary_path, final_path)
            self._ops.fsync_directory(fetch_root)
        except BaseException:
            if not handle.closed:
                handle.close()
            temporary_path.unlink(missing_ok=True)
            final_path.unlink(missing_ok=True)
            raise
        finally:
            if not handle.closed:
                handle.close()
