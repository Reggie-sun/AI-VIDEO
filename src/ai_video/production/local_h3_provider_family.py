"""Router-facing capability family for local T8 H3 video adapters."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.shot_router import ProviderBoundVideoRequest
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoCapabilityVariant,
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


def _identity(variant: VideoCapabilityVariant) -> tuple[object, ...]:
    return (
        variant.provider_kind,
        variant.model_id,
        variant.profile_version,
        variant.mode,
    )


class LocalH3VideoProviderFamily:
    """Expose additive local H3 capabilities without owning execution state.

    Shot Router consumes the combined capability snapshot. Provider-neutral
    compilation and request resolution are delegated to exactly one child.
    Preview, submit, status, fetch, and recovery remain owned by that selected
    child adapter; the family never creates a second lifecycle registry.
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


__all__ = ["LocalH3VideoProviderFamily"]
