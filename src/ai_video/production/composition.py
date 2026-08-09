from __future__ import annotations

from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    AssetType,
    CompositionLayerSpec,
    CompositionSpec,
    LoadedProductionProject,
    RendererIdentity,
    RendererKind,
    ResolvedTimeline,
    ResolvedVisualSpan,
    TransitionKind,
    TransitionSpec,
    VisualStrategy,
)
from ai_video.production.paths import NoFollowFile, _read_regular_file_nofollow


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.COMPOSITION_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _frames_for_fixed_seconds(seconds: float, fps: int) -> int:
    decimal_seconds = Decimal(str(seconds))
    if not decimal_seconds.is_finite():
        raise _invalid("Fixed Shot duration must be finite.")
    value = (decimal_seconds * Decimal(fps)).to_integral_value(
        rounding=ROUND_CEILING
    )
    if value <= 0:
        raise _invalid("Fixed Shot duration must resolve to at least one frame.")
    return int(value)


def _sample_at_frame(frame: int, *, fps: int, sample_rate: int) -> int:
    return int(
        (Decimal(frame) * Decimal(sample_rate) / Decimal(fps)).to_integral_value(
            rounding=ROUND_FLOOR
        )
    )


def _validated_raster_suffix(
    snapshot: NoFollowFile,
    *,
    suffix: str,
    mime_type: str,
) -> str:
    head = snapshot.data[:16]
    suffix = suffix.lower()
    if (
        mime_type == "image/png"
        and suffix == ".png"
        and head.startswith(b"\x89PNG\r\n\x1a\n")
    ):
        return ".png"
    if (
        mime_type == "image/jpeg"
        and suffix in {".jpg", ".jpeg"}
        and head.startswith(b"\xff\xd8\xff")
    ):
        return ".jpg"
    if (
        mime_type == "image/webp"
        and suffix == ".webp"
        and head[:4] == b"RIFF"
        and head[8:12] == b"WEBP"
    ):
        return ".webp"
    raise _invalid("P3 asset MIME, magic bytes and raster suffix do not agree.")


def timeline_fingerprint(timeline: ResolvedTimeline) -> str:
    payload = timeline.model_dump(
        mode="json",
        exclude={"content_hash", "composition_fingerprint", "source_provenance"},
    )
    return canonical_sha256(payload)


def _resolve_composition(
    project: LoadedProductionProject,
    spec: CompositionSpec,
    renderer_version: str,
) -> ResolvedTimeline:
    if not renderer_version:
        raise _invalid("Renderer version must not be empty.")
    if spec.requested_renderer is not RendererKind.HYPERFRAMES:
        raise _invalid("P3 supports only the hyperframes renderer.")
    if "hyperframes" not in project.project.renderer_policy.allowed:
        raise _invalid("ProductionProject does not allow the hyperframes renderer.")
    if not spec.shot_ids:
        raise _invalid("CompositionSpec must contain at least one ordered Shot.")
    if not spec.layers:
        raise _invalid("CompositionSpec must contain at least one visual layer.")
    if len(spec.shot_ids) != len(set(spec.shot_ids)):
        raise _invalid("CompositionSpec shot_ids must be unique.")
    layer_ids = [item.layer_id for item in spec.layers]
    if len(layer_ids) != len(set(layer_ids)):
        raise _invalid("CompositionSpec layer_id values must be unique.")

    shots_by_id = {item.shot_id: item for item in project.shots}
    assets_by_id = {item.asset_id: item for item in project.registry.assets}
    layers_by_shot: dict[str, list[CompositionLayerSpec]] = {
        shot_id: [] for shot_id in spec.shot_ids
    }
    for layer in spec.layers:
        if layer.shot_id not in layers_by_shot:
            raise _invalid(f"Layer {layer.layer_id} references an unordered Shot.")
        layers_by_shot[layer.shot_id].append(layer)

    transition_by_target: dict[str, TransitionSpec] = {}
    adjacent_pairs = set(zip(spec.shot_ids, spec.shot_ids[1:]))
    for transition in spec.transitions:
        pair = (transition.from_shot_id, transition.to_shot_id)
        if pair not in adjacent_pairs or transition.to_shot_id in transition_by_target:
            raise _invalid("Transitions must uniquely join adjacent ordered Shots.")
        if (
            transition.kind is not TransitionKind.CUT
            or transition.duration_frames != 0
        ):
            raise _invalid("P3 accepts only zero-duration cut transitions.")
        transition_by_target[transition.to_shot_id] = transition

    spans: list[ResolvedVisualSpan] = []
    cursor = 0
    for shot_id in spec.shot_ids:
        shot = shots_by_id.get(shot_id)
        if shot is None:
            raise _invalid(f"CompositionSpec references unknown Shot {shot_id}.")
        if shot.visual_strategy is not VisualStrategy.STATIC_IMAGE:
            raise _invalid(f"Shot {shot_id} must use static_image in P3.")
        if shot.motion_directives:
            raise _invalid(f"Shot {shot_id} must not use motion_directives in P3.")
        if shot.duration_policy.mode != "fixed" or shot.duration_policy.seconds is None:
            raise _invalid(f"Shot {shot_id} requires a fixed duration in P3.")
        duration_frames = _frames_for_fixed_seconds(
            shot.duration_policy.seconds, spec.delivery_profile.fps
        )
        incoming = transition_by_target.get(shot_id)
        start_frame = cursor
        shot_layers = layers_by_shot[shot_id]
        if not shot_layers:
            raise _invalid(f"Shot {shot_id} has no CompositionSpec layer.")
        z_values = [item.z_index for item in shot_layers]
        if len(z_values) != len(set(z_values)):
            raise _invalid(f"Shot {shot_id} has duplicate z_index values.")

        start_sample = _sample_at_frame(
            start_frame,
            fps=spec.delivery_profile.fps,
            sample_rate=spec.sample_rate,
        )
        end_sample = _sample_at_frame(
            start_frame + duration_frames,
            fps=spec.delivery_profile.fps,
            sample_rate=spec.sample_rate,
        )
        roles = {item.role: item for item in shot.required_asset_roles}
        for layer in sorted(shot_layers, key=lambda item: (item.z_index, item.layer_id)):
            if layer.trim_start_frame != 0 or layer.trim_duration_frames is not None:
                raise _invalid("P3 static raster layers do not implement trim.")
            asset = assets_by_id.get(layer.asset_id)
            source_path = project.asset_paths.get(layer.asset_id)
            if asset is None or source_path is None:
                raise _invalid(
                    f"Layer {layer.layer_id} references an unregistered asset."
                )
            role = roles.get(layer.asset_role)
            if role is None or layer.asset_id not in role.asset_ids:
                raise _invalid(
                    f"Layer {layer.layer_id} is not bound to its declared Shot asset role."
                )
            if (
                AssetType.IMAGE not in role.allowed_asset_types
                or asset.asset_type is not AssetType.IMAGE
            ):
                raise _invalid(
                    f"Layer {layer.layer_id} must bind a registry image asset."
                )
            if asset.artifact_path.is_absolute() or ".." in asset.artifact_path.parts:
                raise _invalid(f"Asset path is not clean: {asset.asset_id}.")
            registered_path = project.root / asset.artifact_path
            if Path(source_path) != registered_path:
                raise _invalid(
                    f"Loaded asset path does not match registry path: {asset.asset_id}."
                )
            source_snapshot = _read_regular_file_nofollow(
                registered_path,
                contained_by=project.root,
            )
            if (
                source_snapshot.file_sha256 != asset.sha256
                or source_snapshot.size_bytes != asset.size_bytes
            ):
                raise _invalid(
                    f"Asset bytes changed before timeline resolution: {asset.asset_id}."
                )
            suffix = _validated_raster_suffix(
                source_snapshot,
                suffix=registered_path.suffix,
                mime_type=asset.mime_type,
            )
            logical_path = Path("assets") / f"{asset.sha256}{suffix}"
            spans.append(
                ResolvedVisualSpan(
                    layer_id=layer.layer_id,
                    shot_id=shot_id,
                    asset_role=layer.asset_role,
                    asset_id=asset.asset_id,
                    asset_sha256=asset.sha256,
                    asset_mime_type=asset.mime_type,
                    materialized_path=logical_path,
                    start_frame=start_frame,
                    duration_frames=duration_frames,
                    start_sample=start_sample,
                    duration_samples=end_sample - start_sample,
                    trim_start_frame=layer.trim_start_frame,
                    trim_duration_frames=layer.trim_duration_frames,
                    transform=layer.transform,
                    opacity_milli=layer.opacity_milli,
                    z_index=layer.z_index,
                    incoming_transition=incoming,
                )
            )
        cursor = start_frame + duration_frames

    provisional = ResolvedTimeline(
        artifact_id=f"timeline-{spec.composition_id}",
        revision=spec.revision,
        content_hash="0" * 64,
        creation_receipt_id=f"resolve-{spec.content_hash}",
        source_provenance=spec.source_provenance,
        timeline_id=f"timeline-{spec.composition_id}-r{spec.revision}",
        composition_spec_id=spec.artifact_id,
        composition_spec_revision=spec.revision,
        composition_spec_hash=spec.content_hash,
        delivery_profile=spec.delivery_profile,
        sample_rate=spec.sample_rate,
        renderer=RendererIdentity(
            kind=RendererKind.HYPERFRAMES,
            version=renderer_version,
        ),
        visual_spans=tuple(spans),
        total_frames=cursor,
        total_samples=_sample_at_frame(
            cursor,
            fps=spec.delivery_profile.fps,
            sample_rate=spec.sample_rate,
        ),
        composition_fingerprint="0" * 64,
    )
    fingerprint = timeline_fingerprint(provisional)
    return seal_artifact(
        provisional.model_copy(update={"composition_fingerprint": fingerprint})
    )


def resolve_composition(
    project: LoadedProductionProject,
    spec: CompositionSpec,
    renderer_version: str,
) -> ResolvedTimeline:
    try:
        return _resolve_composition(project, spec, renderer_version)
    except AiVideoError:
        raise
    except (OSError, ValueError) as exc:
        raise _invalid("Composition inputs could not be resolved safely.", str(exc)) from exc
