"""Single owner for Production Manifest versions and named capabilities."""

from __future__ import annotations

from enum import Enum
from typing import Literal, TypeAlias


ManifestVersion: TypeAlias = Literal[
    "2.0",
    "2.1",
    "2.2",
    "2.3",
    "2.4",
    "2.5",
    "2.6",
    "2.7",
    "2.8",
    "2.9",
    "2.10",
    "2.11",
    "2.12",
    "2.13",
    "2.14",
    "2.15",
]


class ManifestCapability(str, Enum):
    VOICE_STATE = "voice_state"
    DEPENDENCY_GRAPH = "dependency_graph"
    P6_REVIEW = "p6_review"
    IMAGE_STATE = "image_state"
    PAID_PROVIDER = "paid_provider"
    VIDEO_GENERATION = "video_generation"
    VIDEO_RECOVERY = "video_recovery"
    CONTINUITY_REVIEW = "continuity_review"
    P0_QUALIFICATION = "p0_qualification"
    COMMERCIAL_SOURCE = "commercial_source"
    COMMERCIAL_VIDEO = "commercial_video"
    SOURCE_BOUNDARY = "source_boundary"
    CAPTION_REVIEW = "caption_review_v1"


_VERSIONS: tuple[ManifestVersion, ...] = (
    "2.0",
    "2.1",
    "2.2",
    "2.3",
    "2.4",
    "2.5",
    "2.6",
    "2.7",
    "2.8",
    "2.9",
    "2.10",
    "2.11",
    "2.12",
    "2.13",
    "2.14",
    "2.15",
)

MANIFEST_SCHEMA_ORDER: tuple[ManifestVersion, ...] = _VERSIONS

_INTRODUCED_IN: dict[ManifestCapability, ManifestVersion] = {
    ManifestCapability.VOICE_STATE: "2.2",
    ManifestCapability.DEPENDENCY_GRAPH: "2.3",
    ManifestCapability.P6_REVIEW: "2.4",
    ManifestCapability.IMAGE_STATE: "2.5",
    ManifestCapability.PAID_PROVIDER: "2.6",
    ManifestCapability.VIDEO_GENERATION: "2.7",
    ManifestCapability.VIDEO_RECOVERY: "2.8",
    ManifestCapability.CONTINUITY_REVIEW: "2.10",
    ManifestCapability.P0_QUALIFICATION: "2.11",
    ManifestCapability.COMMERCIAL_SOURCE: "2.12",
    ManifestCapability.COMMERCIAL_VIDEO: "2.13",
    ManifestCapability.SOURCE_BOUNDARY: "2.14",
    ManifestCapability.CAPTION_REVIEW: "2.15",
}


def manifest_supports(
    version: str, capability: ManifestCapability
) -> bool:
    """Return capability support without callers comparing version strings."""
    try:
        version_index = _VERSIONS.index(version)  # type: ignore[arg-type]
        minimum_index = _VERSIONS.index(_INTRODUCED_IN[capability])
    except ValueError:
        return False
    return version_index >= minimum_index


def require_manifest_version_for(
    current: str, capability: ManifestCapability
) -> ManifestVersion:
    """Select the smallest non-downgrading version with the capability."""
    if current not in _VERSIONS:
        raise ValueError("unsupported Production Manifest version")
    if manifest_supports(current, capability):
        return current  # type: ignore[return-value]
    return _INTRODUCED_IN[capability]


def is_supported_manifest_version(version: str) -> bool:
    return version in _VERSIONS
