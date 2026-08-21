"""One-action orchestration for durable P8 generated-video attempts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import StateCommitStatus, VideoAttemptPhase
from ai_video.production.local_video import (
    LocalVideoFetchReceipt,
    LocalVideoProvider,
    LocalVideoSubmission,
    LocalVideoSubmitResult,
    LocalVideoTaskObservation,
)
from ai_video.production.paid_provider import (
    PaidProviderCallPreview,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
)
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoFetchReceipt,
    VideoProvider,
    VideoSubmission,
    VideoTaskObservation,
)

if TYPE_CHECKING:
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_artifact import (
        GeneratedShotContinuityReviewer,
        TerminalFrameExtractor,
    )


@dataclass(frozen=True)
class FetchedVideoCandidate:
    relative_path: Path
    receipt: VideoFetchReceipt | LocalVideoFetchReceipt


class VideoGenerationService:
    """Orchestrate exactly one Provider action around committer-owned state."""

    def __init__(
        self,
        *,
        committer: ProductionStateCommitter,
        provider: VideoProvider | LocalVideoProvider,
    ) -> None:
        self._committer = committer
        self._provider = provider

    def start(
        self,
        *,
        attempt_id: str,
        request: ResolvedVideoGenerationRequest,
    ):
        return self._committer.begin_video_generation(
            attempt_id=attempt_id,
            request=request,
        )

    def _state(self, attempt_id: str):
        manifest = self._committer._read_manifest()
        attempt = self._committer._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if state is None:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Video generation state is missing.",
                retryable=False,
            )
        return attempt, state

    def submit_once(
        self,
        *,
        attempt_id: str,
        paid_preview: PaidProviderCallPreview,
        reservation_id: str,
    ) -> VideoSubmission:
        attempt, state = self._state(attempt_id)
        if state.phase is not VideoAttemptPhase.REQUEST:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Video submit is not the next durable action.",
                retryable=False,
            )
        request = self._committer._reopen_video_request(state.request)
        video_preview = self._provider.preview(request)
        permit = self._committer.record_paid_provider_submit_intent(
            paid_preview,
            reservation_id=reservation_id,
        )
        intent = self._committer._read_manifest()
        intent_attempt = self._committer._video_attempt(intent, attempt_id)
        paid_state = intent_attempt.paid_provider_state
        if paid_state is None:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Paid Provider intent was not persisted.",
                retryable=False,
            )
        gate = self._committer._reopen_paid_gate(paid_state.gate_receipt)
        try:
            result = self._provider.submit(
                request,
                video_preview,
                paid_preview,
                gate.authorization,
                permit,
            )
        except AiVideoError as exc:
            if exc.code in {
                ErrorCode.VIDEO_PROVIDER_FAILED,
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
            }:
                outcome = (
                    PaidProviderSubmitOutcome.KNOWN_NO_EFFECT
                    if exc.code is ErrorCode.VIDEO_PROVIDER_FAILED
                    else PaidProviderSubmitOutcome.OUTCOME_UNKNOWN
                )
                receipt = PaidProviderSubmitReceipt.create(
                    attempt_id=attempt_id,
                    request_fingerprint=request.resolved_generation_hash,
                    preview_fingerprint=gate.preview.preview_fingerprint,
                    gate_receipt_fingerprint=gate.gate_receipt_fingerprint,
                    reservation_id=paid_state.reservation_id,
                    outcome=outcome,
                    external_effect_id=None,
                    recorded_at=self._committer._paid_provider_clock(),
                )
                self._committer.record_paid_provider_submit_receipt(receipt)
            raise
        receipt = PaidProviderSubmitReceipt.create(
            attempt_id=attempt_id,
            request_fingerprint=request.resolved_generation_hash,
            preview_fingerprint=gate.preview.preview_fingerprint,
            gate_receipt_fingerprint=gate.gate_receipt_fingerprint,
            reservation_id=paid_state.reservation_id,
            outcome=PaidProviderSubmitOutcome.ACCEPTED,
            external_effect_id=result.external_effect_id,
            recorded_at=result.submitted_at,
        )
        self._committer.record_paid_provider_submit_receipt(receipt)
        return VideoSubmission.from_paid_submit_receipt(
            resolved=request,
            receipt=receipt,
        )

    def submit_local_once(self, *, attempt_id: str) -> LocalVideoSubmission:
        """Submit exactly once after the committer persists a local intent."""

        attempt, state = self._state(attempt_id)
        if (
            attempt.status is not StateCommitStatus.RUNNING
            or state.phase is not VideoAttemptPhase.REQUEST
            or attempt.paid_provider_state is not None
        ):
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Local video submit is not the next durable action.",
                retryable=False,
            )
        request = self._committer._reopen_video_request(state.request)
        preview = self._provider.preview(request)
        intent, permit = self._committer.record_local_video_submit_intent(
            attempt_id=attempt_id,
            preview=preview,
        )
        try:
            result = self._provider.submit_local(
                request,
                preview,
                intent,
                permit,
            )
        except AiVideoError as exc:
            if exc.code in {
                ErrorCode.VIDEO_PROVIDER_FAILED,
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
            }:
                self._committer.record_video_provider_failure(
                    attempt_id=attempt_id,
                    error_code=exc.code,
                    message=exc.user_message,
                )
            raise
        if not isinstance(result, LocalVideoSubmitResult):
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Local video Provider returned an invalid submit result.",
                retryable=False,
            )
        self._committer.record_local_video_submit_result(
            attempt_id=attempt_id,
            result=result,
        )
        return LocalVideoSubmission.from_submit_result(
            resolved=request,
            result=result,
        )

    def refresh_local_once(self, *, attempt_id: str) -> LocalVideoTaskObservation:
        attempt, state = self._state(attempt_id)
        if (
            attempt.status is not StateCommitStatus.RUNNING
            or state.phase
            not in {VideoAttemptPhase.SUBMITTED, VideoAttemptPhase.POLLING}
            or state.local_submit_receipt is None
            or attempt.paid_provider_state is not None
        ):
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Local video poll is not the next durable action.",
                retryable=False,
            )
        request = self._committer._reopen_video_request(state.request)
        result = self._committer._reopen_local_video_submit(
            state.local_submit_receipt
        )
        submission = LocalVideoSubmission.from_submit_result(
            resolved=request, result=result
        )
        try:
            observation = self._provider.get_local_status(request, submission)
        except AiVideoError as exc:
            if exc.code in {
                ErrorCode.VIDEO_PROVIDER_FAILED,
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
            }:
                self._committer.record_video_provider_failure(
                    attempt_id=attempt_id,
                    error_code=exc.code,
                    message=exc.user_message,
                )
            raise
        self._committer.record_local_video_status_observation(
            attempt_id=attempt_id,
            observation=observation,
        )
        return observation

    def fetch_local_once(self, *, attempt_id: str) -> FetchedVideoCandidate:
        attempt, state = self._state(attempt_id)
        if (
            attempt.status is not StateCommitStatus.RUNNING
            or state.phase is not VideoAttemptPhase.FETCH
            or state.local_latest_observation is None
            or state.local_submit_receipt is None
            or attempt.paid_provider_state is not None
        ):
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Local video fetch is not the next durable action.",
                retryable=False,
            )
        request = self._committer._reopen_video_request(state.request)
        result = self._committer._reopen_local_video_submit(
            state.local_submit_receipt
        )
        submission = LocalVideoSubmission.from_submit_result(
            resolved=request, result=result
        )
        observation = self._committer._reopen_local_video_status(
            state.local_latest_observation
        )
        with self._committer.prepare_video_fetch_sink(
            attempt_id=attempt_id
        ) as (path, sink):
            fetch_receipt = self._provider.fetch_local(
                request,
                submission,
                observation,
                sink,
            )
        pointer = self._committer.record_local_video_fetch_result(
            attempt_id=attempt_id,
            temporary_path=path,
            receipt=fetch_receipt,
        )
        return FetchedVideoCandidate(
            relative_path=pointer.artifact_path,
            receipt=fetch_receipt,
        )

    def refresh_once(self, *, attempt_id: str) -> VideoTaskObservation:
        attempt, state = self._state(attempt_id)
        if state.phase not in {
            VideoAttemptPhase.SUBMITTED,
            VideoAttemptPhase.POLLING,
        }:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Video poll is not the next durable action.",
                retryable=False,
            )
        paid_state = attempt.paid_provider_state
        if paid_state is None or paid_state.submit_receipt is None:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Video poll requires a durable submit receipt.",
                retryable=False,
            )
        request = self._committer._reopen_video_request(state.request)
        receipt = self._committer._reopen_paid_submit(paid_state.submit_receipt)
        submission = VideoSubmission.from_paid_submit_receipt(
            resolved=request,
            receipt=receipt,
        )
        observation = self._provider.get_status(submission, receipt)
        self._committer.record_video_status_observation(
            attempt_id=attempt_id,
            observation=observation,
        )
        return observation

    def fetch_once(self, *, attempt_id: str) -> FetchedVideoCandidate:
        attempt, state = self._state(attempt_id)
        paid_state = attempt.paid_provider_state
        if (
            state.phase is not VideoAttemptPhase.FETCH
            or state.latest_observation is None
            or paid_state is None
            or paid_state.submit_receipt is None
        ):
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Video fetch is not the next durable action.",
                retryable=False,
            )
        request = self._committer._reopen_video_request(state.request)
        receipt = self._committer._reopen_paid_submit(paid_state.submit_receipt)
        submission = VideoSubmission.from_paid_submit_receipt(
            resolved=request,
            receipt=receipt,
        )
        observation = self._committer._reopen_video_status(
            state.latest_observation
        )
        with self._committer.prepare_video_fetch_sink(
            attempt_id=attempt_id
        ) as (path, sink):
            fetch_receipt = self._provider.fetch(
                submission,
                receipt,
                observation,
                sink,
            )
        pointer = self._committer.record_video_fetch_result(
            attempt_id=attempt_id,
            temporary_path=path,
            receipt=fetch_receipt,
        )
        return FetchedVideoCandidate(
            relative_path=pointer.artifact_path,
            receipt=fetch_receipt,
        )

    def resume_next_action(self, *, attempt_id: str) -> str:
        return self._committer.video_resume_next_action(attempt_id=attempt_id)

    def fetch_and_activate(
        self,
        *,
        attempt_id: str,
        probe: Callable[[int], dict] | None = None,
        terminal_frame_extractor: TerminalFrameExtractor | None = None,
        continuity_reviewer: GeneratedShotContinuityReviewer | None = None,
    ):
        """Finish only the durable next post-submit phases, replaying no effect."""

        attempt, state = self._state(attempt_id)
        if (
            attempt.status.value == "succeeded"
            and state.phase is VideoAttemptPhase.ACTIVATE
        ):
            return self._committer.replay_active_video_generation(
                attempt_id=attempt_id
            )
        if state.phase is VideoAttemptPhase.FETCH:
            if state.local_submit_receipt is not None:
                self.fetch_local_once(attempt_id=attempt_id)
            else:
                self.fetch_once(attempt_id=attempt_id)
            _, state = self._state(attempt_id)
        if state.phase is VideoAttemptPhase.VALIDATE:
            self._committer.prepare_video_activation_candidate(
                attempt_id=attempt_id,
                probe=probe,
                terminal_frame_extractor=terminal_frame_extractor,
                continuity_reviewer=continuity_reviewer,
            )
            _, state = self._state(attempt_id)
        if state.phase is VideoAttemptPhase.CANDIDATE:
            return self._committer.activate_video_candidate(
                attempt_id=attempt_id
            )
        raise AiVideoError(
            code=ErrorCode.PRODUCTION_STATE_INVALID,
            user_message="Video post-fetch activation is not the next durable action.",
            retryable=False,
        )
