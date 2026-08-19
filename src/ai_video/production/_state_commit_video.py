from __future__ import annotations

import hashlib
import os
import re
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO

from ai_video.errors import ErrorCode
from ai_video.production._video_project_reader import (
    load_video_fetch_receipt,
    load_video_request_receipt,
    load_video_status_receipt,
    load_terminal_frame_evidence,
    load_terminal_frame_extraction,
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
    canonical_video_fetch_artifact_path,
    canonical_video_fetch_receipt_path,
    canonical_video_request_receipt_path,
    canonical_video_status_receipt_path,
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
from ._state_commit_contracts import PreparedArtifact


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

    def _reopen_terminal_frame_evidence(
        self, pointer: TerminalFrameEvidencePointer
    ):
        return load_terminal_frame_evidence(self._project_root, pointer)

    def _reopen_terminal_frame_extraction(
        self, pointer: TerminalFrameExtractionReceiptPointer
    ):
        return load_terminal_frame_extraction(self._project_root, pointer)

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
            if manifest.schema_version not in {"2.7", "2.8"}:
                raise _state_invalid(
                    "Video generation requires Production Manifest 2.7 or 2.8."
                )
            if (
                request.activation_scope is not None
                and (
                    request.activation_scope.request.seal_terminal_frame
                    or request.continuity_binding is not None
                )
                and manifest.schema_version != "2.8"
            ):
                raise _state_invalid(
                    "Shot continuity requires Production Manifest 2.8."
                )
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

    @contextmanager
    def prepare_video_fetch_sink(
        self, *, attempt_id: str
    ) -> Iterator[tuple[Path, BinaryIO]]:
        """Open a held-FD task-owned temporary MP4 for one bounded fetch."""

        manifest = self._read_manifest()
        attempt = self._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if (
            attempt.status is not StateCommitStatus.RUNNING
            or state is None
            or state.phase is not VideoAttemptPhase.FETCH
            or state.latest_observation is None
            or self._reopen_video_status(state.latest_observation).state
            is not VideoTaskState.SUCCEEDED
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
