"""Router-facing capability family for local T8 H3 video adapters."""

from __future__ import annotations

from collections.abc import Iterable
from typing import BinaryIO, Protocol

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.local_video import (
    DurableLocalVideoSubmitPermit,
    LocalVideoFetchReceipt,
    LocalVideoSubmission,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
    LocalVideoTaskObservation,
)
from ai_video.production.shot_router import ProviderBoundVideoRequest
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoCapabilityVariant,
    VideoGenerationPreview,
    VideoGenerationRequest,
    VideoProviderCapabilities,
)
from ai_video.production.video_compiler import ProviderRequestCompilationResult
from ai_video.production.video_requirement import ProviderNeutralVideoRequirement


_PROVIDER_NAME = "comfy-local-h3-t8"


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class _ChildProvider(Protocol):
    def capabilities(self) -> VideoProviderCapabilities: ...

    def compile_request(
        self,
        provider_bound: ProviderBoundVideoRequest,
        requirement: ProviderNeutralVideoRequirement,
    ) -> ProviderRequestCompilationResult: ...

    def resolve(
        self, request: VideoGenerationRequest
    ) -> ResolvedVideoGenerationRequest: ...

    def preview(
        self, request: ResolvedVideoGenerationRequest
    ) -> VideoGenerationPreview: ...

    def preflight(self, request: ResolvedVideoGenerationRequest) -> None: ...

    def submit_local(
        self,
        request: ResolvedVideoGenerationRequest,
        preview: VideoGenerationPreview,
        intent: LocalVideoSubmitIntent,
        permit: DurableLocalVideoSubmitPermit,
    ) -> LocalVideoSubmitResult: ...

    def get_local_status(
        self,
        request: ResolvedVideoGenerationRequest,
        submission: LocalVideoSubmission,
    ) -> LocalVideoTaskObservation: ...

    def fetch_local(
        self,
        request: ResolvedVideoGenerationRequest,
        submission: LocalVideoSubmission,
        observation: LocalVideoTaskObservation,
        sink: BinaryIO,
    ) -> LocalVideoFetchReceipt: ...


def _identity(variant: VideoCapabilityVariant) -> tuple[object, ...]:
    return (
        variant.provider_kind,
        variant.model_id,
        variant.profile_version,
        variant.mode,
    )


def _resolved_identity(request: ResolvedVideoGenerationRequest) -> tuple[object, ...]:
    return (
        request.provider_kind,
        request.model_id,
        request.provider_profile.profile_version,
        request.mode,
    )


class LocalH3VideoProviderFamily:
    """Expose additive local H3 capabilities without owning execution state.

    Shot Router consumes the combined capability snapshot. Provider-neutral
    compilation and request resolution are delegated to exactly one child.
    Preview, preflight, submit, status, and fetch are delegated to that
    selected child adapter. Durable lifecycle and recovery remain committer-
    owned; the family never creates a second registry or persists action state.
    """

    def __init__(self, children: Iterable[_ChildProvider]) -> None:
        child_items = tuple(children)
        if not child_items:
            raise _invalid("Local H3 provider family requires at least one child.")

        by_capability_id: dict[str, _ChildProvider] = {}
        by_identity: dict[tuple[object, ...], _ChildProvider] = {}
        variants: list[VideoCapabilityVariant] = []
        for child in child_items:
            capabilities = child.capabilities()
            if capabilities.provider_name != _PROVIDER_NAME:
                raise _invalid(
                    "Local H3 family children must use the canonical provider name.",
                    capabilities.provider_name,
                )
            for variant in capabilities.variants:
                if variant.capability_id in by_capability_id:
                    raise _invalid(
                        "Local H3 family capability IDs must be disjoint.",
                        variant.capability_id,
                    )
                identity = _identity(variant)
                if identity in by_identity:
                    raise _invalid(
                        "Local H3 family variant identities must be unambiguous.",
                        variant.capability_id,
                    )
                by_capability_id[variant.capability_id] = child
                by_identity[identity] = child
                variants.append(variant)

        self._by_capability_id = by_capability_id
        self._by_identity = by_identity
        self._capabilities = VideoProviderCapabilities.create(
            provider_name=_PROVIDER_NAME,
            variants=tuple(sorted(variants, key=lambda item: item.capability_id)),
        )

    def capabilities(self) -> VideoProviderCapabilities:
        return self._capabilities

    def _resolve_child(
        self, request: ResolvedVideoGenerationRequest
    ) -> _ChildProvider:
        if request.provider_name != _PROVIDER_NAME:
            raise _invalid(
                "Local H3 family received a request for another provider.",
                request.provider_name,
            )
        child = self._by_identity.get(_resolved_identity(request))
        if child is None:
            raise _invalid(
                "Local H3 family has no exact adapter for the request identity."
            )
        return child

    def compile_request(
        self,
        provider_bound: ProviderBoundVideoRequest,
        requirement: ProviderNeutralVideoRequirement,
    ) -> ProviderRequestCompilationResult:
        if provider_bound.provider_name != _PROVIDER_NAME:
            raise _invalid(
                "Local H3 family received a request for another provider.",
                provider_bound.provider_name,
            )
        child = self._by_capability_id.get(provider_bound.capability_id)
        if child is None:
            raise _invalid(
                "Local H3 family does not own the selected capability.",
                provider_bound.capability_id,
            )
        return child.compile_request(provider_bound, requirement)

    def resolve(
        self, request: VideoGenerationRequest
    ) -> ResolvedVideoGenerationRequest:
        if request.provider_name != _PROVIDER_NAME:
            raise _invalid(
                "Local H3 family received a request for another provider.",
                request.provider_name,
            )
        identity = (
            request.provider_kind,
            request.model_id,
            request.provider_profile.profile_version,
            request.mode,
        )
        child = self._by_identity.get(identity)
        if child is None:
            raise _invalid(
                "Local H3 family has no exact adapter for the request identity."
            )
        return child.resolve(request)

    def preview(
        self, request: ResolvedVideoGenerationRequest
    ) -> VideoGenerationPreview:
        return self._resolve_child(request).preview(request)

    def preflight(self, request: ResolvedVideoGenerationRequest) -> None:
        self._resolve_child(request).preflight(request)

    def submit_local(
        self,
        request: ResolvedVideoGenerationRequest,
        preview: VideoGenerationPreview,
        intent: LocalVideoSubmitIntent,
        permit: DurableLocalVideoSubmitPermit,
    ) -> LocalVideoSubmitResult:
        return self._resolve_child(request).submit_local(
            request, preview, intent, permit
        )

    def get_local_status(
        self,
        request: ResolvedVideoGenerationRequest,
        submission: LocalVideoSubmission,
    ) -> LocalVideoTaskObservation:
        child = self._resolve_child(request)
        if submission.resolved_generation_hash != request.resolved_generation_hash:
            raise _invalid(
                "Local H3 submission does not match the reopened request."
            )
        return child.get_local_status(request, submission)

    def fetch_local(
        self,
        request: ResolvedVideoGenerationRequest,
        submission: LocalVideoSubmission,
        observation: LocalVideoTaskObservation,
        sink: BinaryIO,
    ) -> LocalVideoFetchReceipt:
        child = self._resolve_child(request)
        if submission.resolved_generation_hash != request.resolved_generation_hash:
            raise _invalid(
                "Local H3 submission does not match the reopened request."
            )
        if (
            observation.submission_fingerprint != submission.submission_fingerprint
            or observation.submit_result_fingerprint
            != submission.submit_result_fingerprint
        ):
            raise _invalid(
                "Local H3 observation does not match the durable submission."
            )
        return child.fetch_local(request, submission, observation, sink)


__all__ = ["LocalH3VideoProviderFamily"]
