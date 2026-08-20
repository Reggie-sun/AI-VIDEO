"""Deterministic no-network generated-video Provider used by offline acceptance."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import BinaryIO, Literal

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.paid_provider import (
    DurablePaidProviderSubmitPermit,
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
)
from ai_video.production.video import (
    BillingKind,
    ResolvedVideoGenerationRequest,
    VideoGenerationPreview,
    VideoGenerationRequest,
    VideoProviderCapabilities,
    VideoSubmitResult,
    VideoSubmission,
    VideoTaskObservation,
    VideoTaskState,
    VideoFetchReceipt,
    build_video_paid_permit_binding,
)
from ai_video.production.shot_router import ProviderBoundVideoRequest
from ai_video.production.video_compiler import (
    ProviderRequestCompilationResult,
    compile_provider_video_request,
)
from ai_video.production.video_requirement import ProviderNeutralVideoRequirement


@dataclass(frozen=True)
class FakeVideoScenario:
    submit_outcome: Literal["accepted", "rejected", "outcome_unknown"] = "accepted"
    status_events: tuple[
        VideoTaskState | Literal["transient_error"], ...
    ] = (
        VideoTaskState.QUEUED,
        VideoTaskState.RUNNING,
        VideoTaskState.SUCCEEDED,
    )
    fetch_outcome: Literal["success", "failure", "tampered"] = "success"
    external_effect_id: str = "fake-task-1"
    provider_file_id: str = "fake-file-1"


@dataclass(frozen=True)
class VideoProviderCallCounts:
    capabilities: int
    resolve: int
    preview: int
    submit: int
    status: int
    fetch: int


class ScriptedFakeVideoProvider:
    """Scripted adapter with exact call counters and injected immutable bytes."""

    def __init__(
        self,
        *,
        capabilities: VideoProviderCapabilities,
        artifact_bytes: bytes,
        scenario: FakeVideoScenario | None = None,
    ) -> None:
        if not artifact_bytes:
            raise ValueError("fake video artifact bytes must not be empty")
        self._capabilities = capabilities
        self._artifact_bytes = bytes(artifact_bytes)
        self._scenario = scenario or FakeVideoScenario()
        self._capabilities_calls = 0
        self._resolve_calls = 0
        self._preview_calls = 0
        self._submit_calls = 0
        self._status_calls = 0
        self._fetch_calls = 0

    @property
    def call_counts(self) -> VideoProviderCallCounts:
        return VideoProviderCallCounts(
            capabilities=self._capabilities_calls,
            resolve=self._resolve_calls,
            preview=self._preview_calls,
            submit=self._submit_calls,
            status=self._status_calls,
            fetch=self._fetch_calls,
        )

    def capabilities(self) -> VideoProviderCapabilities:
        self._capabilities_calls += 1
        return self._capabilities

    def compile_request(
        self,
        provider_bound: ProviderBoundVideoRequest,
        requirement: ProviderNeutralVideoRequirement,
    ) -> ProviderRequestCompilationResult:
        return compile_provider_video_request(
            provider_bound=provider_bound,
            requirement=requirement,
            compiler_id="fake-video-compiler",
            compiler_version="1",
            capabilities=self._capabilities,
        )

    def resolve(self, request: VideoGenerationRequest) -> ResolvedVideoGenerationRequest:
        self._resolve_calls += 1
        matching = tuple(
            variant
            for variant in self._capabilities.variants
            if (
                variant.provider_kind == request.provider_kind
                and variant.model_id == request.model_id
                and variant.profile_version == request.provider_profile.profile_version
                and variant.mode is request.mode
                and variant.output == request.output_requirement
            )
        )
        if len(matching) != 1:
            raise AiVideoError(
                code=ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                user_message="Fake video Provider found no unique capability variant.",
                retryable=False,
            )
        return ResolvedVideoGenerationRequest.create(
            request=request,
            capability=matching[0],
            effective_output=request.output_requirement,
            effective_seed=request.seed,
            effective_negative_prompt_text=request.negative_prompt_text,
        )

    def preview(
        self, request: ResolvedVideoGenerationRequest
    ) -> VideoGenerationPreview:
        self._preview_calls += 1
        return self._build_preview(request)

    @staticmethod
    def _build_preview(
        request: ResolvedVideoGenerationRequest,
    ) -> VideoGenerationPreview:
        if request.billing_kind is BillingKind.METERED:
            return VideoGenerationPreview.create(
                resolved=request,
                estimated_cost_upper_bound_microunits=1_000_000,
                currency="USD",
                destination="https://fake-video.invalid",
                egress_item_ids=("prompt",),
            )
        return VideoGenerationPreview.create(
            resolved=request,
            estimated_cost_upper_bound_microunits=None,
            currency=None,
            destination=None,
            egress_item_ids=(),
        )

    def submit(
        self,
        request: ResolvedVideoGenerationRequest,
        video_preview: VideoGenerationPreview,
        paid_preview: PaidProviderCallPreview | None,
        authorization: PaidProviderAuthorizationDecision | None,
        permit: DurablePaidProviderSubmitPermit | None,
    ) -> VideoSubmitResult:
        if video_preview != self._build_preview(request):
            raise AiVideoError(
                code=ErrorCode.VIDEO_REQUEST_INVALID,
                user_message=(
                    "Fake video submit preview does not match its resolved Provider preview."
                ),
                retryable=False,
            )
        if request.billing_kind is BillingKind.METERED:
            if paid_preview is None or authorization is None or permit is None:
                raise AiVideoError(
                    code=ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                    user_message="Fake metered video submit requires Paid Provider authority.",
                    retryable=False,
                )
            binding = build_video_paid_permit_binding(
                request,
                video_preview,
                paid_preview,
                authorization,
            )
            try:
                valid = permit._validate_paid_provider_operation_permit(**binding)
            except Exception:
                valid = False
            if valid is not True:
                raise AiVideoError(
                    code=ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                    user_message="Fake metered video submit permit is invalid.",
                    retryable=False,
                )
            try:
                consumed = permit._consume_paid_provider_operation_permit(**binding)
            except Exception:
                consumed = False
            if consumed is not True:
                raise AiVideoError(
                    code=ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                    user_message="Fake metered video submit permit could not be consumed.",
                    retryable=False,
                )
        elif paid_preview is not None or authorization is not None or permit is not None:
            raise AiVideoError(
                code=ErrorCode.VIDEO_REQUEST_INVALID,
                user_message="Fake local video submit cannot claim Paid Provider authority.",
                retryable=False,
            )
        self._submit_calls += 1
        if self._scenario.submit_outcome == "rejected":
            raise AiVideoError(
                code=ErrorCode.VIDEO_PROVIDER_FAILED,
                user_message="Fake video submit was rejected with known no effect.",
                retryable=False,
            )
        if self._scenario.submit_outcome == "outcome_unknown":
            raise AiVideoError(
                code=ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                user_message="Fake video submit outcome is unknown.",
                retryable=False,
            )
        return VideoSubmitResult.create(
            resolved=request,
            external_effect_id=self._scenario.external_effect_id,
            submitted_at=datetime(2026, 8, 18, tzinfo=UTC),
        )

    def get_status(
        self,
        submission: VideoSubmission,
        submit_receipt: PaidProviderSubmitReceipt,
    ) -> VideoTaskObservation:
        if (
            submit_receipt.outcome is not PaidProviderSubmitOutcome.ACCEPTED
            or submit_receipt.submit_receipt_fingerprint
            != submission.paid_submit_receipt_fingerprint
            or submit_receipt.external_effect_id != self._scenario.external_effect_id
        ):
            raise AiVideoError(
                code=ErrorCode.VIDEO_REQUEST_INVALID,
                user_message="Fake video status receipt does not match the submission.",
                retryable=False,
            )
        index = self._status_calls
        self._status_calls += 1
        events = self._scenario.status_events
        event = events[min(index, len(events) - 1)]
        if event == "transient_error":
            raise AiVideoError(
                code=ErrorCode.VIDEO_PROVIDER_FAILED,
                user_message="Fake video status transport failed transiently.",
                retryable=True,
            )
        return VideoTaskObservation.create(
            submission=submission,
            state=event,
            observed_at=datetime(2026, 8, 18, 0, index + 1, tzinfo=UTC),
            progress_milli={
                VideoTaskState.QUEUED: 0,
                VideoTaskState.RUNNING: 500,
                VideoTaskState.SUCCEEDED: 1000,
                VideoTaskState.FAILED: 1000,
            }[event],
            provider_file_id=(
                self._scenario.provider_file_id
                if event is VideoTaskState.SUCCEEDED
                else None
            ),
        )

    def fetch(
        self,
        submission: VideoSubmission,
        submit_receipt: PaidProviderSubmitReceipt,
        observation: VideoTaskObservation,
        sink: BinaryIO,
    ) -> VideoFetchReceipt:
        if (
            submit_receipt.submit_receipt_fingerprint
            != submission.paid_submit_receipt_fingerprint
            or observation.paid_submit_receipt_fingerprint
            != submission.paid_submit_receipt_fingerprint
        ):
            raise AiVideoError(
                code=ErrorCode.VIDEO_REQUEST_INVALID,
                user_message="Fake video fetch evidence does not match the submission.",
                retryable=False,
            )
        self._fetch_calls += 1
        if self._scenario.fetch_outcome == "failure":
            raise AiVideoError(
                code=ErrorCode.VIDEO_PROVIDER_FAILED,
                user_message="Fake video fetch failed.",
                retryable=True,
            )
        output = self._artifact_bytes
        claimed = self._artifact_bytes
        if self._scenario.fetch_outcome == "tampered":
            output = self._artifact_bytes + b"tampered"
        sink.write(output)
        return VideoFetchReceipt.create(
            submission=submission,
            observation=observation,
            content_type="video/mp4",
            size_bytes=len(claimed),
            artifact_sha256=hashlib.sha256(claimed).hexdigest(),
            fetched_at=datetime(2026, 8, 18, 0, 10, tzinfo=UTC),
        )


__all__ = [
    "FakeVideoScenario",
    "ScriptedFakeVideoProvider",
    "VideoProviderCallCounts",
]
