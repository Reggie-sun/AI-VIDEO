"""Pure generated-video projections consumed by the P5 dependency graph."""

from __future__ import annotations

from ai_video.errors import AiVideoError, ErrorCode
from collections.abc import Iterable, Mapping

from ai_video.production.models import (
    AssetRecord,
    AssetSourceKind,
    AssetType,
    DependencyReason,
)


VideoContinuityEdgeArgs = tuple[
    str,
    str,
    DependencyReason,
    str,
    Mapping[str, str],
]


def generated_video_semantic_fingerprint(asset: AssetRecord) -> str | None:
    """Return the stable generation identity for a generated video asset."""

    metadata = asset.video_metadata
    if metadata is None or asset.source_kind is not AssetSourceKind.GENERATED:
        return None
    if asset.input_fingerprint != metadata.resolved_generation_hash:
        raise AiVideoError(
            code=ErrorCode.DEPENDENCY_GRAPH_INVALID,
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


def generated_video_continuity_edge_args(
    assets: Iterable[AssetRecord],
) -> tuple[VideoContinuityEdgeArgs, ...]:
    """Project only explicit generated-video terminal-frame lineage into P5."""

    ordered_assets = tuple(assets)
    assets_by_id = {asset.asset_id: asset for asset in ordered_assets}
    terminal_assets = {
        asset.asset_id: asset
        for asset in ordered_assets
        if asset.asset_type is AssetType.IMAGE
        and asset.source_kind is AssetSourceKind.DERIVED
        and asset.asset_id.endswith(":terminal-frame")
        and asset.input_artifact_ids
        == (asset.asset_id.removesuffix(":terminal-frame"),)
    }
    edges: list[VideoContinuityEdgeArgs] = []
    for terminal in terminal_assets.values():
        source_asset_id = terminal.input_artifact_ids[0]
        source = assets_by_id.get(source_asset_id)
        if source is None or generated_video_semantic_fingerprint(source) is None:
            continue
        edges.append(
            (
                f"asset:{source_asset_id}",
                f"asset:{terminal.asset_id}",
                DependencyReason.GENERATION_INPUT,
                "video.terminal_frame",
                {
                    "source_asset_id": source_asset_id,
                    "source_generation_fingerprint": source.input_fingerprint,
                    "terminal_asset_id": terminal.asset_id,
                    "terminal_evidence_fingerprint": terminal.input_fingerprint,
                },
            )
        )
    hard_cut_keyframe_ids: set[str] = set()
    for keyframe in ordered_assets:
        if (
            keyframe.asset_type is not AssetType.IMAGE
            or keyframe.source_kind is not AssetSourceKind.GENERATED
        ):
            continue
        for input_asset_id in keyframe.input_artifact_ids:
            terminal = terminal_assets.get(input_asset_id)
            if terminal is None:
                continue
            hard_cut_keyframe_ids.add(keyframe.asset_id)
            edges.append(
                (
                    f"asset:{terminal.asset_id}",
                    f"asset:{keyframe.asset_id}",
                    DependencyReason.GENERATION_INPUT,
                    "image.continuity_terminal",
                    {
                        "terminal_asset_id": terminal.asset_id,
                        "terminal_asset_sha256": terminal.sha256,
                        "keyframe_asset_id": keyframe.asset_id,
                        "keyframe_request_fingerprint": keyframe.input_fingerprint,
                    },
                )
            )
    for keyframe in ordered_assets:
        if keyframe.asset_id not in hard_cut_keyframe_ids:
            continue
        for input_asset_id in keyframe.input_artifact_ids:
            source = assets_by_id.get(input_asset_id)
            if source is None or input_asset_id in terminal_assets:
                continue
            edges.append(
                (
                    f"asset:{source.asset_id}",
                    f"asset:{keyframe.asset_id}",
                    DependencyReason.GENERATION_INPUT,
                    "image.reference_input",
                    {
                        "source_asset_id": source.asset_id,
                        "source_asset_sha256": source.sha256,
                        "keyframe_asset_id": keyframe.asset_id,
                        "keyframe_request_fingerprint": keyframe.input_fingerprint,
                    },
                )
            )
    for target in ordered_assets:
        if generated_video_semantic_fingerprint(target) is None:
            continue
        for input_asset_id in target.input_artifact_ids:
            source_image = assets_by_id.get(input_asset_id)
            if (
                source_image is None
                or source_image.asset_type is not AssetType.IMAGE
                or source_image.asset_id not in terminal_assets
                and source_image.asset_id not in hard_cut_keyframe_ids
            ):
                continue
            edges.append(
                (
                    f"asset:{source_image.asset_id}",
                    f"asset:{target.asset_id}",
                    DependencyReason.GENERATION_INPUT,
                    "video.reference_input",
                    {
                        "source_asset_id": source_image.asset_id,
                        "source_asset_sha256": source_image.sha256,
                        "target_asset_id": target.asset_id,
                        "target_generation_fingerprint": target.input_fingerprint,
                    },
                )
            )
    return tuple(edges)


__all__ = [
    "generated_video_continuity_edge_args",
    "generated_video_semantic_fingerprint",
    "visual_asset_dependency_reason",
]
