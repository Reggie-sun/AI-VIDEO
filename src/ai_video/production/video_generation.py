"""One-action orchestration for durable P8 generated-video attempts."""

from __future__ import annotations

import errno
import fcntl
import hashlib
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterator

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
from ai_video.production.remote_media import (
    _REMOTE_REFERENCE_REFRESH_PERMIT_TOKEN,
    _RemoteReferenceRefreshPermit,
)
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoFetchReceipt,
    VideoFlexibleOutputRequirement,
    VideoProvider,
    VideoSubmission,
    VideoTaskObservation,
)
from ai_video.production.video_compiler import CompiledProviderVideoRequest

if TYPE_CHECKING:
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_artifact import (
        GeneratedCommercialShotReviewer,
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

    @property
    def project_root(self) -> Path:
        """Return the canonical Production state root owned by this service."""

        return self._committer.project_root

    def start(
        self,
        *,
        attempt_id: str,
        request: ResolvedVideoGenerationRequest,
        execution_binding,
    ):
        return self._committer.begin_video_generation(
            attempt_id=attempt_id,
            request=request,
            execution_binding=execution_binding,
        )

    def _start_qualification(
        self,
        *,
        attempt_id: str,
        request: ResolvedVideoGenerationRequest,
        qualification_binding,
    ):
        """Dedicated callers only; their closure guard remains mandatory at submit."""

        return self._committer._begin_qualification_video_generation(
            attempt_id=attempt_id,
            request=request,
            qualification_binding=qualification_binding,
        )

    def _validate_generation_execution_binding(self, state, request) -> None:
        """Reopen and recompute the decision before any Provider access."""

        pointer = getattr(state, "execution_binding", None)
        if pointer is None:
            qualification = getattr(state, "qualification_binding", None)
            if qualification is None:
                raise AiVideoError(
                    code=ErrorCode.PRODUCTION_STATE_INVALID,
                    user_message=(
                        "Video submit requires a persisted generation or qualification binding."
                    ),
                    retryable=False,
                )
            try:
                self._committer._reopen_qualification_execution_binding(
                    qualification
                ).validate_request(request)
            except (AiVideoError, AttributeError, ValueError) as exc:
                if isinstance(exc, AiVideoError):
                    raise
                raise AiVideoError(
                    code=ErrorCode.PRODUCTION_STATE_INVALID,
                    user_message="Qualification execution binding is stale or invalid.",
                    technical_detail=str(exc),
                    retryable=False,
                ) from exc
            return
        try:
            binding = self._committer._reopen_generation_execution_binding(pointer)
            binding.validate_request(request)
            routing = binding.decision.routing
            if routing is None or routing.provider_bound_request is None:
                raise ValueError("submit decision has no bound request")
            result = self._provider.compile_request(
                routing.provider_bound_request,
                binding.projection.requirement,
            )
            if not isinstance(result, CompiledProviderVideoRequest):
                raise ValueError("current Provider compiler cannot express the bound recipe")
            sealed = request.activation_scope.request if request.activation_scope else None
            if sealed is None or result.request != sealed:
                raise ValueError("current Provider compilation differs from sealed request")
            if self._provider.resolve(result.request) != request:
                raise ValueError("current Provider resolution differs from sealed request")
        except (AiVideoError, AttributeError, ValueError) as exc:
            if isinstance(exc, AiVideoError):
                raise
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Generation decision binding is stale or no longer executable.",
                technical_detail=str(exc),
                retryable=False,
            ) from exc

    @contextmanager
    def commercial_execution_guard(self, *, attempt_id: str) -> Iterator[None]:
        """Serialize one commercial Shot coordinator across service instances."""

        digest = hashlib.sha256(attempt_id.encode("utf-8")).hexdigest()
        lock_path = (
            self._committer._state_directory()
            / f".ecommerce-video-execution-{digest}.lock"
        )
        self._committer._reject_symlink(lock_path)
        try:
            handle = lock_path.open("a+b")
        except OSError as exc:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_COMMIT_FAILED,
                user_message="Could not open Ecommerce video execution lock.",
                technical_detail=str(exc),
                retryable=False,
            ) from exc
        acquired = False
        primary: BaseException | None = None
        try:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                primary = AiVideoError(
                    code=ErrorCode.PRODUCTION_STATE_BUSY,
                    user_message=(
                        "Ecommerce video Shot execution is already in progress."
                    ),
                    technical_detail=str(exc),
                    retryable=False,
                )
                raise primary from exc
            except OSError as exc:
                code = (
                    ErrorCode.PRODUCTION_STATE_BUSY
                    if exc.errno in {errno.EACCES, errno.EAGAIN}
                    else ErrorCode.PRODUCTION_STATE_UNSUPPORTED
                )
                primary = AiVideoError(
                    code=code,
                    user_message=(
                        "Ecommerce video Shot execution is already in progress."
                        if code is ErrorCode.PRODUCTION_STATE_BUSY
                        else "POSIX Ecommerce video execution locking failed."
                    ),
                    technical_detail=str(exc),
                    retryable=False,
                )
                raise primary from exc
            acquired = True
            try:
                yield
            except BaseException as exc:
                primary = exc
                raise
        finally:
            cleanup_errors: list[BaseException] = []
            if acquired:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                except BaseException as exc:
                    cleanup_errors.append(exc)
            try:
                handle.close()
            except BaseException as exc:
                cleanup_errors.append(exc)
            if cleanup_errors:
                detail = "; ".join(str(item) for item in cleanup_errors)
                if primary is not None:
                    primary.add_note(
                        f"Ecommerce video execution lock cleanup failed: {detail}"
                    )
                else:
                    raise AiVideoError(
                        code=ErrorCode.PRODUCTION_STATE_COMMIT_FAILED,
                        user_message=(
                            "Ecommerce video execution lock cleanup failed."
                        ),
                        technical_detail=detail,
                        retryable=False,
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
        self._validate_generation_execution_binding(state, request)
        if getattr(state, "qualification_binding", None) is not None:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Qualification execution cannot use a paid Provider submit path.",
                retryable=False,
            )
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

    def submit_local_once(
        self,
        *,
        attempt_id: str,
        pre_submit_guard: (
            Callable[[ResolvedVideoGenerationRequest], None] | None
        ) = None,
    ) -> LocalVideoSubmission:
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
        self._validate_generation_execution_binding(state, request)
        if (
            getattr(state, "qualification_binding", None) is not None
            and pre_submit_guard is None
        ):
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Qualification local submit requires its exact closure guard.",
                retryable=False,
            )
        if request.execution_stack_hash is not None and pre_submit_guard is None:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message=(
                    "Stack-bound local video submit requires a pre-submit guard."
                ),
                retryable=False,
            )
        if pre_submit_guard is not None:
            pre_submit_guard(request)
        preview = self._provider.preview(request)
        if pre_submit_guard is None:
            intent, permit = self._committer.record_local_video_submit_intent(
                attempt_id=attempt_id,
                preview=preview,
            )
        else:
            intent, permit = self._committer.record_local_video_submit_intent(
                attempt_id=attempt_id,
                preview=preview,
                pre_submit_guard=pre_submit_guard,
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

    def refresh_remote_reference_lease_once(self, *, attempt_id: str):
        """Reopen one accepted remote Shot and refresh its transient input lease."""

        self._committer.replay_active_video_generation(attempt_id=attempt_id)
        attempt, state = self._state(attempt_id)
        paid_state = attempt.paid_provider_state
        refresh = getattr(
            self._provider,
            "refresh_provider_output_reference_lease",
            None,
        )
        if (
            attempt.status is not StateCommitStatus.SUCCEEDED
            or state.phase is not VideoAttemptPhase.ACTIVATE
            or state.latest_observation is None
            or state.fetch_receipt is None
            or paid_state is None
            or paid_state.submit_receipt is None
            or not callable(refresh)
        ):
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message=(
                    "Remote reference lease requires one activated remote video attempt."
                ),
                retryable=False,
            )
        request = self._committer._reopen_video_request(state.request)
        submit_receipt = self._committer._reopen_paid_submit(
            paid_state.submit_receipt
        )
        submission = VideoSubmission.from_paid_submit_receipt(
            resolved=request,
            receipt=submit_receipt,
        )
        observation = self._committer._reopen_video_status(
            state.latest_observation
        )
        fetch_receipt = self._committer._reopen_video_fetch(state.fetch_receipt)
        materialization = fetch_receipt.remote_materialization
        if materialization is None:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Active remote video has no materialization evidence.",
                retryable=False,
            )
        refresh_permit = _RemoteReferenceRefreshPermit(
            _REMOTE_REFERENCE_REFRESH_PERMIT_TOKEN,
            submission_fingerprint=submission.submission_fingerprint,
            observation_fingerprint=observation.observation_fingerprint,
            fetch_fingerprint=fetch_receipt.fetch_fingerprint,
            materialization_receipt_id=materialization.content_hash,
            durability_validator=lambda: self._remote_reference_source_is_active(
                attempt_id
            ),
            source_nominal_duration_millis=(
                request.effective_output.duration_seconds * 1_000
                if isinstance(
                    request.effective_output, VideoFlexibleOutputRequirement
                )
                and request.effective_output.timing_mode == "nominal_seconds"
                else None
            ),
        )
        return refresh(
            submission,
            submit_receipt,
            observation,
            fetch_receipt,
            refresh_permit,
        )

    def _remote_reference_source_is_active(self, attempt_id: str) -> bool:
        try:
            self._committer.replay_active_video_generation(attempt_id=attempt_id)
        except Exception:
            return False
        return True

    def resume_next_action(self, *, attempt_id: str) -> str:
        return self._committer.video_resume_next_action(attempt_id=attempt_id)

    def current_bound_commercial_request_identity(
        self,
        *,
        attempt_id: str,
    ) -> tuple[str, str, str, str] | None:
        """Reopen an existing attempt's exact commercial request identity."""

        manifest = self._committer._read_manifest()
        existing = next(
            (item for item in manifest.attempts if item.attempt_id == attempt_id),
            None,
        )
        if existing is None:
            return None
        attempt = self._committer._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if state is None:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Video generation state is missing.",
                retryable=False,
            )
        request = self._committer._reopen_video_request(state.request)
        binding = request.commercial_binding
        if binding is None:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Commercial video request binding is missing.",
                retryable=False,
            )
        return (
            request.resolved_generation_hash,
            binding.ad_creative_plan_hash,
            binding.commercial_execution_projection_hash,
            binding.target_shot_id,
        )

    def current_commercial_validation_verdict(self, *, attempt_id: str):
        """Reopen current commercial PASS evidence without running its evaluator."""

        from ai_video.production._state_commit_video_commercial import (
            validate_current_commercial_video_state,
        )

        manifest = self._committer._read_manifest()
        attempt = self._committer._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if (
            state is None
            or state.phase
            not in {VideoAttemptPhase.CANDIDATE, VideoAttemptPhase.ACTIVATE}
        ):
            return None
        request = self._committer._reopen_video_request(state.request)
        evidence = validate_current_commercial_video_state(
            self._committer,
            manifest=manifest,
            state=state,
            request=request,
        )
        from ai_video.production.models import QaVerdict

        return None if evidence is None else QaVerdict.PASS

    def current_activated_commercial_checkpoint(self, *, attempt_id: str):
        """Project one exact active Manifest checkpoint for the Ecommerce barrier."""

        from ai_video.production._state_commit_video_commercial import (
            validate_current_commercial_video_state,
        )
        from ai_video.production.ecommerce_ad_coordinator import (
            ActivatedCommercialShotCheckpoint,
        )

        manifest = self._committer._read_manifest()
        attempt = self._committer._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if (
            attempt.status is not StateCommitStatus.SUCCEEDED
            or state is None
            or state.phase is not VideoAttemptPhase.ACTIVATE
        ):
            return None
        request = self._committer._reopen_video_request(state.request)
        evidence = validate_current_commercial_video_state(
            self._committer,
            manifest=manifest,
            state=state,
            request=request,
        )
        binding = request.commercial_binding
        if evidence is None or binding is None:
            return None
        from ai_video.production.models import QaVerdict

        return ActivatedCommercialShotCheckpoint.create(
            ad_creative_plan_hash=binding.ad_creative_plan_hash,
            commercial_execution_projection_hash=(
                binding.commercial_execution_projection_hash
            ),
            shot_id=binding.target_shot_id,
            resolved_generation_hash=request.resolved_generation_hash,
            artifact_sha256=evidence.artifact_sha256,
            commercial_evidence_content_hash=evidence.content_hash,
            verdict=QaVerdict.PASS,
            activated=True,
        )

    def fetch_and_activate(
        self,
        *,
        attempt_id: str,
        probe: Callable[[int], dict] | None = None,
        terminal_frame_extractor: TerminalFrameExtractor | None = None,
        continuity_reviewer: GeneratedShotContinuityReviewer | None = None,
        commercial_reviewer: GeneratedCommercialShotReviewer | None = None,
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
                commercial_reviewer=commercial_reviewer,
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

    def validate_once(
        self,
        *,
        attempt_id: str,
        probe: Callable[[int], dict] | None = None,
        terminal_frame_extractor: TerminalFrameExtractor | None = None,
        continuity_reviewer: GeneratedShotContinuityReviewer | None = None,
        commercial_reviewer: GeneratedCommercialShotReviewer | None = None,
    ):
        """Perform exactly one canonical prepare action without any activation."""

        attempt, state = self._state(attempt_id)
        if (
            attempt.status is not StateCommitStatus.RUNNING
            or state.phase is not VideoAttemptPhase.VALIDATE
        ):
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message=(
                    "Video validation requires a running VALIDATE attempt."
                ),
                retryable=False,
            )
        return self._committer.prepare_video_activation_candidate(
            attempt_id=attempt_id,
            probe=probe,
            terminal_frame_extractor=terminal_frame_extractor,
            continuity_reviewer=continuity_reviewer,
            commercial_reviewer=commercial_reviewer,
        )

    def activate_once(self, *, attempt_id: str):
        """Perform exactly one canonical activation action without re-validating."""

        attempt, state = self._state(attempt_id)
        if (
            attempt.status
            not in {StateCommitStatus.RUNNING, StateCommitStatus.INTERRUPTED}
            or state.phase is not VideoAttemptPhase.CANDIDATE
        ):
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message=(
                    "Video activation requires a recoverable CANDIDATE attempt."
                ),
                retryable=False,
            )
        return self._committer.activate_video_candidate(attempt_id=attempt_id)
