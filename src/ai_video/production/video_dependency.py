"""Pure generated-video projections consumed by the P5 dependency graph."""

from __future__ import annotations

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import AssetRecord, AssetSourceKind, DependencyReason


def generated_video_semantic_fingerprint(asset: AssetRecord) -> str | None:
    """Return the stable generation identity for a generated video asset."""

    metadata = asset.video_metadata
    if metadata is None or asset.source_kind is not AssetSourceKind.GENERATED:
        return None
    if asset.input_fingerprint != metadata.resolved_generation_hash:
        raise AiVideoError(
            code=ErrorCode.PRODUCTION_GRAPH_INVALID,
            user_message=(
                "generated video asset input identity does not match its "
                "resolved generation"
            ),
            retryable=False,
        )
    return metadata.resolved_generation_hash


def visual_asset_dependency_reason(asset: AssetRecord) -> DependencyReason:
    """Classify generated visual assets without coupling the DAG to providers."""

    if asset.source_kind is AssetSourceKind.GENERATED:
        return DependencyReason.GENERATION_INPUT
    return DependencyReason.ASSET_BINDING


__all__ = [
    "generated_video_semantic_fingerprint",
    "visual_asset_dependency_reason",
]
