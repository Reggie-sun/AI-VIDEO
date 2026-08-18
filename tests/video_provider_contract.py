from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Callable

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderSubmitReceipt,
)
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoGenerationPreview,
    VideoGenerationRequest,
    VideoSubmission,
    VideoSubmitResult,
    VideoTaskState,
    build_video_paid_permit_binding,
)


@dataclass
class PaidProviderPermitDouble:
    binding: dict[str, str]
    consumed: bool = False

    def _validate_paid_provider_operation_permit(self, **binding: str) -> bool:
        return not self.consumed and binding == self.binding

    def _consume_paid_provider_operation_permit(self, **binding: str) -> bool:
        if not self._validate_paid_provider_operation_permit(**binding):
            return False
        self.consumed = True
        return True


@dataclass(frozen=True)
class VideoProviderContractCase:
    request: VideoGenerationRequest
    unsupported_request: VideoGenerationRequest
    paid_preview_factory: Callable[
        [ResolvedVideoGenerationRequest, VideoGenerationPreview],
        PaidProviderCallPreview,
    ]
    authorization_factory: Callable[
        [PaidProviderCallPreview], PaidProviderAuthorizationDecision
    ]
    submit_receipt_factory: Callable[
        [ResolvedVideoGenerationRequest, PaidProviderCallPreview, VideoSubmitResult],
        PaidProviderSubmitReceipt,
    ]
    expected_artifact_sha256: str


def assert_video_provider_contract(
    provider_factory: Callable[[], object],
    capability_cases: tuple[VideoProviderContractCase, ...],
) -> None:
    """Run the shared resolve/submit/status/fetch contract against a Provider."""

    assert capability_cases
    for case in capability_cases:
        provider = provider_factory()
        capabilities = provider.capabilities()
        assert capabilities.variants

        resolved = provider.resolve(case.request)
        video_preview = provider.preview(resolved)
        paid_preview = case.paid_preview_factory(resolved, video_preview)
        authorization = case.authorization_factory(paid_preview)
        binding = build_video_paid_permit_binding(
            resolved,
            video_preview,
            paid_preview,
            authorization,
        )

        bad_permit = PaidProviderPermitDouble(
            {**binding, "request_fingerprint": "f" * 64}
        )
        with pytest.raises(AiVideoError) as exc_info:
            provider.submit(
                resolved,
                video_preview,
                paid_preview,
                authorization,
                bad_permit,
            )
        assert exc_info.value.code is ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED
        assert provider.call_counts.submit == 0

        result = provider.submit(
            resolved,
            video_preview,
            paid_preview,
            authorization,
            PaidProviderPermitDouble(binding),
        )
        submit_receipt = case.submit_receipt_factory(
            resolved,
            paid_preview,
            result,
        )
        submission = VideoSubmission.from_paid_submit_receipt(
            resolved=resolved,
            receipt=submit_receipt,
        )
        observations = []
        for _ in range(16):
            observation = provider.get_status(submission, submit_receipt)
            observations.append(observation)
            if observation.state in {VideoTaskState.SUCCEEDED, VideoTaskState.FAILED}:
                break
        assert observations[-1].state is VideoTaskState.SUCCEEDED
        sink = BytesIO()
        fetch_receipt = provider.fetch(
            submission,
            submit_receipt,
            observations[-1],
            sink,
        )

        assert result.resolved_generation_hash == resolved.resolved_generation_hash
        assert submission.paid_submit_receipt_fingerprint == (
            submit_receipt.submit_receipt_fingerprint
        )
        assert observations[-1].paid_submit_receipt_fingerprint == (
            submit_receipt.submit_receipt_fingerprint
        )
        assert fetch_receipt.submission_fingerprint == submission.submission_fingerprint
        assert fetch_receipt.artifact_sha256 == case.expected_artifact_sha256
        assert provider.call_counts.capabilities == 1
        assert provider.call_counts.resolve == 1
        assert provider.call_counts.preview == 1
        assert provider.call_counts.submit == 1
        assert provider.call_counts.status == len(observations)
        assert provider.call_counts.fetch == 1

        unsupported_provider = provider_factory()
        with pytest.raises(AiVideoError) as exc_info:
            unsupported_provider.resolve(case.unsupported_request)
        assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED
        assert unsupported_provider.call_counts.resolve == 1
        assert unsupported_provider.call_counts.submit == 0
