from __future__ import annotations

from decimal import Decimal, ROUND_CEILING
from pathlib import Path

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.captions import (
    _canonical_track_bytes,
    caption_style_fingerprint,
    caption_timing_fingerprint,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    AUDIO_KIND_PRIORITY,
    AUDIO_KIND_TO_ASSET_TYPE,
    AssetRecord,
    AssetType,
    AudioKind,
    AudioTrackSpec,
    CaptionAssetMetadata,
    CaptionStyleReference,
    CaptionStyleBindingContract,
    CaptionTrack,
    CaptionTrackBinding,
    CompositionLayerSpec,
    CompositionSpec,
    LoadedProductionProject,
    RendererIdentity,
    RendererKind,
    ResolvedAudioSpan,
    ResolvedCaptionCue,
    ResolvedDuckingSpec,
    ResolvedTimeline,
    ResolvedVisualSpan,
    TransitionKind,
    TransitionSpec,
    VisualStrategy,
)
from ai_video.production.paths import NoFollowFile, _read_regular_file_nofollow
from ai_video.production.visual_media import (
    VisualMediaValidationError,
    resolved_video_trim_duration,
    validated_visual_suffix,
)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.COMPOSITION_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _audio_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.AUDIO_TIMELINE_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _caption_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.CAPTION_TRACK_INVALID,
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
    return frame * sample_rate // fps


def _floor_frame_at_sample(sample: int, *, fps: int, sample_rate: int) -> int:
    return sample * fps // sample_rate


def _ceil_frame_at_sample(sample: int, *, fps: int, sample_rate: int) -> int:
    return (sample * fps + sample_rate - 1) // sample_rate


def _validated_visual_suffix(
    snapshot: NoFollowFile,
    *,
    suffix: str,
    mime_type: str,
) -> str:
    try:
        return validated_visual_suffix(
            snapshot.data, suffix=suffix, mime_type=mime_type
        )
    except VisualMediaValidationError as exc:
        raise _invalid(str(exc)) from exc


def timeline_fingerprint(timeline: ResolvedTimeline) -> str:
    excluded = {"content_hash", "composition_fingerprint", "source_provenance"}
    if timeline.schema_version == "2.1":
        # P4 fingerprints resolved behavior, not authoring tuple order. The exact
        # input artifact hash remains durable on the timeline itself.
        excluded.update({"composition_spec_hash", "creation_receipt_id"})
    payload = timeline.model_dump(mode="json", exclude=excluded)
    return canonical_sha256(payload)


def _verified_registry_asset(
    project: LoadedProductionProject,
    asset: AssetRecord,
    *,
    invalid,
):
    source_path = project.asset_paths.get(asset.asset_id)
    if source_path is None:
        raise invalid(f"Asset {asset.asset_id} has no verified loaded path.")
    if asset.artifact_path.is_absolute() or ".." in asset.artifact_path.parts:
        raise invalid(f"Asset path is not clean: {asset.asset_id}.")
    registered_path = project.root / asset.artifact_path
    if Path(source_path) != registered_path:
        raise invalid(
            f"Loaded asset path does not match registry path: {asset.asset_id}."
        )
    try:
        snapshot = _read_regular_file_nofollow(
            registered_path,
            contained_by=project.root,
        )
    except (OSError, ValueError) as exc:
        raise invalid(f"Asset {asset.asset_id} could not be read safely.", str(exc)) from exc
    if (
        snapshot.file_sha256 != asset.sha256
        or snapshot.size_bytes != asset.size_bytes
    ):
        raise invalid(f"Asset bytes changed before timeline resolution: {asset.asset_id}.")
    return snapshot


def _resolved_source_duration(
    track: AudioTrackSpec,
    asset: AssetRecord,
    *,
    sample_rate: int,
) -> int:
    metadata = asset.audio_metadata
    if metadata is None:
        raise _audio_invalid(f"Audio asset {asset.asset_id} has no P4 metadata.")
    if metadata.sample_rate_hz != sample_rate:
        raise _audio_invalid(
            f"Audio asset {asset.asset_id} sample rate does not match composition."
        )
    if asset.asset_type is not AUDIO_KIND_TO_ASSET_TYPE[track.audio_kind]:
        raise _audio_invalid(
            f"Audio track {track.track_id} has the wrong registry asset type."
        )
    if metadata.audio_kind is not track.audio_kind:
        raise _audio_invalid(
            f"Audio track {track.track_id} kind does not match asset metadata."
        )
    if not asset.mime_type.startswith("audio/"):
        raise _audio_invalid(f"Audio asset {asset.asset_id} has a non-audio MIME type.")
    if track.trim_start_sample >= metadata.duration_samples:
        raise _audio_invalid(f"Audio track {track.track_id} trim starts past its source.")
    available = metadata.duration_samples - track.trim_start_sample
    duration = track.trim_duration_samples or available
    if duration > available:
        raise _audio_invalid(f"Audio track {track.track_id} trim exceeds its source.")
    if track.fade_in_samples + track.fade_out_samples > duration:
        raise _audio_invalid(f"Audio track {track.track_id} fades exceed its duration.")
    return duration


def _load_audio_assets(
    project: LoadedProductionProject,
    spec: CompositionSpec,
) -> dict[str, tuple[AudioTrackSpec, AssetRecord, int]]:
    assets = {item.asset_id: item for item in project.registry.assets}
    track_ids = [item.track_id for item in spec.audio_tracks]
    if len(track_ids) != len(set(track_ids)):
        raise _audio_invalid("Audio track IDs must be unique.")
    known_track_ids = set(track_ids)
    result: dict[str, tuple[AudioTrackSpec, AssetRecord, int]] = {}
    for track in spec.audio_tracks:
        asset = assets.get(track.asset_id)
        if asset is None:
            raise _audio_invalid(f"Audio track {track.track_id} has an unknown asset.")
        duration = _resolved_source_duration(
            track,
            asset,
            sample_rate=spec.sample_rate,
        )
        _verified_registry_asset(project, asset, invalid=_audio_invalid)
        if track.ducking is not None:
            sidechains = track.ducking.sidechain_track_ids
            if (
                track.track_id in sidechains
                or len(sidechains) != len(set(sidechains))
                or not set(sidechains).issubset(known_track_ids)
            ):
                raise _audio_invalid(
                    f"Audio track {track.track_id} has invalid ducking sidechains."
                )
        result[track.track_id] = (track, asset, duration)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(track_id: str) -> None:
        if track_id in visiting:
            raise _audio_invalid("Audio ducking sidechains must be acyclic.")
        if track_id in visited:
            return
        visiting.add(track_id)
        ducking = result[track_id][0].ducking
        if ducking is not None:
            for sidechain_id in ducking.sidechain_track_ids:
                visit(sidechain_id)
        visiting.remove(track_id)
        visited.add(track_id)

    for track_id in result:
        visit(track_id)
    return result


def _voice_driven_frames(
    shot_id: str,
    duration_policy,
    audio_assets: dict[str, tuple[AudioTrackSpec, AssetRecord, int]],
    *,
    fps: int,
    sample_rate: int,
) -> int:
    drivers = [
        item
        for item in audio_assets.values()
        if item[0].shot_id == shot_id
        and item[0].audio_kind in {AudioKind.DIALOGUE, AudioKind.NARRATION}
    ]
    if len(drivers) != 1:
        raise _audio_invalid(
            f"Voice-driven Shot {shot_id} requires exactly one speech driver."
        )
    track, _asset, duration_samples = drivers[0]
    if track.start_sample is not None:
        raise _audio_invalid(
            f"Voice-driven Shot {shot_id} driver must use shot-relative placement."
        )
    duration_seconds = Decimal(duration_samples) / Decimal(sample_rate)
    if (
        duration_policy.minimum_seconds is not None
        and duration_seconds < Decimal(str(duration_policy.minimum_seconds))
    ):
        raise _audio_invalid(f"Voice-driven Shot {shot_id} is below its minimum duration.")
    if (
        duration_policy.maximum_seconds is not None
        and duration_seconds > Decimal(str(duration_policy.maximum_seconds))
    ):
        raise _audio_invalid(f"Voice-driven Shot {shot_id} exceeds its maximum duration.")
    frame_numerator = duration_samples * fps
    if frame_numerator % sample_rate:
        raise _audio_invalid(
            f"Voice-driven Shot {shot_id} duration cannot snap exactly to a frame."
        )
    frames = frame_numerator // sample_rate
    if frames <= 0:
        raise _audio_invalid(
            f"Voice-driven Shot {shot_id} must resolve to at least one frame."
        )
    return frames


def _duration_frames_by_shot(
    project: LoadedProductionProject,
    spec: CompositionSpec,
    audio_assets: dict[str, tuple[AudioTrackSpec, AssetRecord, int]],
) -> dict[str, int]:
    result: dict[str, int] = {}
    for shot in project.shots:
        if shot.shot_id not in spec.shot_ids:
            continue
        policy = shot.duration_policy
        if policy.mode == "fixed" and policy.seconds is not None:
            result[shot.shot_id] = _frames_for_fixed_seconds(
                policy.seconds, spec.delivery_profile.fps
            )
        elif spec.schema_version == "2.0":
            raise _invalid(f"Shot {shot.shot_id} requires a fixed duration in P3.")
        elif policy.mode == "voice_driven":
            result[shot.shot_id] = _voice_driven_frames(
                shot.shot_id,
                policy,
                audio_assets,
                fps=spec.delivery_profile.fps,
                sample_rate=spec.sample_rate,
            )
        else:
            raise _invalid(f"Shot {shot.shot_id} content_driven duration is unsupported.")
    return result


def _resolve_audio_spans(
    spec: CompositionSpec,
    audio_assets: dict[str, tuple[AudioTrackSpec, AssetRecord, int]],
    *,
    shot_start_samples: dict[str, int],
    total_samples: int,
) -> tuple[ResolvedAudioSpan, ...]:
    spans: list[ResolvedAudioSpan] = []
    for track, asset, duration in audio_assets.values():
        if track.shot_id is not None and track.shot_id not in shot_start_samples:
            raise _audio_invalid(
                f"Audio track {track.track_id} references an unordered Shot."
            )
        start_sample = (
            track.start_sample
            if track.start_sample is not None
            else shot_start_samples[track.shot_id]
        )
        if start_sample + duration > total_samples:
            raise _audio_invalid(
                f"Audio track {track.track_id} exceeds the fixed visual timeline."
            )
        ducking = None
        if track.ducking is not None:
            ducking = ResolvedDuckingSpec(
                sidechain_track_ids=tuple(sorted(track.ducking.sidechain_track_ids)),
                attenuation_millidb=track.ducking.attenuation_millidb,
                attack_samples=track.ducking.attack_samples,
                release_samples=track.ducking.release_samples,
            )
        spans.append(
            ResolvedAudioSpan(
                track_id=track.track_id,
                audio_kind=track.audio_kind,
                asset_id=asset.asset_id,
                asset_sha256=asset.sha256,
                start_sample=start_sample,
                duration_samples=duration,
                source_start_sample=track.trim_start_sample,
                source_duration_samples=duration,
                gain_millidb=track.gain_millidb,
                fade_in_samples=track.fade_in_samples,
                fade_out_samples=track.fade_out_samples,
                ducking=ducking,
            )
        )
    return tuple(
        sorted(
            spans,
            key=lambda item: (
                AUDIO_KIND_PRIORITY[item.audio_kind],
                item.track_id,
                item.start_sample,
                item.asset_id,
            ),
        )
    )


def _parse_caption_track(data: bytes) -> CaptionTrack | None:
    try:
        return CaptionTrack.model_validate_json(data)
    except ValidationError:
        return None


def _caption_style_binding_is_valid(
    track: CaptionTrack,
    metadata: CaptionAssetMetadata,
    binding: CaptionTrackBinding,
) -> bool:
    try:
        CaptionStyleBindingContract(
            caption_track=track,
            caption_metadata=metadata,
            binding=binding,
        )
    except ValidationError:
        return False
    return True


def _caption_style_bytes_are_valid(
    style: CaptionStyleReference,
    data: bytes,
) -> bool:
    try:
        caption_style_fingerprint(style, data)
    except (AiVideoError, UnicodeError):
        return False
    return True


def _load_caption_track(
    project: LoadedProductionProject,
    binding: CaptionTrackBinding,
    asset: AssetRecord,
) -> CaptionTrack:
    if asset.asset_type is not AssetType.CAPTION or asset.caption_metadata is None:
        raise _caption_invalid(
            f"Caption binding {binding.binding_id} requires a typed caption asset."
        )
    if asset.mime_type != "application/json":
        raise _caption_invalid(
            f"Caption asset {asset.asset_id} must use application/json."
        )
    snapshot = _verified_registry_asset(project, asset, invalid=_caption_invalid)
    track = _parse_caption_track(snapshot.data)
    if track is None:
        raise _caption_invalid(
            "Caption asset is not a canonical CaptionTrack.",
            "caption_schema_validation_failed",
        )
    if snapshot.data != _canonical_track_bytes(track):
        raise _caption_invalid(
            f"Caption asset {asset.asset_id} bytes are not canonical."
        )
    metadata = asset.caption_metadata
    word_count = sum(len(segment.words or ()) for segment in track.segments)
    metadata_identity = (
        metadata.caption_track_id,
        metadata.language,
        metadata.source_audio_asset_id,
        metadata.source_audio_sha256,
        metadata.script_hash,
        metadata.transcript_hash,
        metadata.segment_count,
        metadata.word_count,
        metadata.segmentation_policy_id,
        metadata.segmentation_policy_version,
        metadata.alignment_receipt_id,
        metadata.timing_fingerprint,
    )
    track_identity = (
        track.caption_track_id,
        track.language,
        track.source_audio_asset_id,
        track.source_audio_sha256,
        track.script_hash,
        track.transcript_hash,
        len(track.segments),
        word_count,
        track.segmentation_policy.policy_id,
        track.segmentation_policy.policy_version,
        track.alignment_receipt_id,
        track.timing_fingerprint,
    )
    if (
        track.content_hash != canonical_sha256(track)
        or track.timing_fingerprint != caption_timing_fingerprint(track)
        or metadata_identity != track_identity
    ):
        raise _caption_invalid(
            f"Caption asset {asset.asset_id} identity or timing fingerprint does not match."
        )
    if not _caption_style_binding_is_valid(track, metadata, binding):
        raise _caption_invalid(
            "Caption style identity does not match.",
            "caption_style_identity_validation_failed",
        )
    style = binding.style_reference
    if style is None:
        raise _caption_invalid(f"Caption binding {binding.binding_id} requires style.")
    try:
        style_snapshot = _read_regular_file_nofollow(
            project.root / style.path,
            contained_by=project.root,
        )
    except (OSError, ValueError) as exc:
        raise _caption_invalid(
            f"Caption binding {binding.binding_id} style path is unsafe.", str(exc)
        ) from exc
    if style_snapshot.file_sha256 != style.content_hash:
        raise _caption_invalid(
            f"Caption binding {binding.binding_id} style bytes changed."
        )
    if not _caption_style_bytes_are_valid(style, style_snapshot.data):
        raise _caption_invalid(
            "Caption style bytes are invalid.",
            "caption_style_bytes_validation_failed",
        )
    if not track.segments:
        raise _caption_invalid(f"Caption binding {binding.binding_id} is empty.")
    return track


def _resolve_caption_cues(
    project: LoadedProductionProject,
    spec: CompositionSpec,
    audio_assets: dict[str, tuple[AudioTrackSpec, AssetRecord, int]],
    audio_spans: tuple[ResolvedAudioSpan, ...],
    *,
    total_frames: int,
    total_samples: int,
) -> tuple[ResolvedCaptionCue, ...]:
    assets = {item.asset_id: item for item in project.registry.assets}
    spans = {item.track_id: item for item in audio_spans}
    cues: list[ResolvedCaptionCue] = []
    for binding in spec.caption_tracks:
        asset = assets.get(binding.caption_asset_id)
        if asset is None:
            raise _caption_invalid(
                f"Caption binding {binding.binding_id} has an unknown asset."
            )
        track = _load_caption_track(project, binding, asset)
        source = audio_assets.get(binding.source_audio_track_id)
        span = spans.get(binding.source_audio_track_id)
        if source is None or span is None:
            raise _caption_invalid(
                f"Caption binding {binding.binding_id} has an unknown source audio track."
            )
        source_spec, source_asset, _duration = source
        if binding.shot_id is not None and binding.shot_id != source_spec.shot_id:
            raise _caption_invalid(
                f"Caption binding {binding.binding_id} Shot does not match source audio."
            )
        if (
            track.source_sample_rate_hz != spec.sample_rate
            or track.source_audio_asset_id != source_asset.asset_id
            or track.source_audio_sha256 != source_asset.sha256
        ):
            raise _caption_invalid(
                f"Caption binding {binding.binding_id} source audio identity does not match."
            )
        source_end = span.source_start_sample + span.source_duration_samples
        style = binding.style_reference
        assert style is not None
        for segment in track.segments:
            if (
                segment.start_sample < span.source_start_sample
                or segment.end_sample > source_end
            ):
                raise _caption_invalid(
                    f"Caption segment {segment.segment_id} falls outside trimmed audio."
                )
            start_sample = span.start_sample + (
                segment.start_sample - span.source_start_sample
            )
            end_sample = span.start_sample + (
                segment.end_sample - span.source_start_sample
            )
            start_frame = _floor_frame_at_sample(
                start_sample,
                fps=spec.delivery_profile.fps,
                sample_rate=spec.sample_rate,
            )
            end_frame = _ceil_frame_at_sample(
                end_sample,
                fps=spec.delivery_profile.fps,
                sample_rate=spec.sample_rate,
            )
            if (
                end_sample > total_samples
                or start_frame >= end_frame
                or end_frame > total_frames
            ):
                raise _caption_invalid(
                    f"Caption segment {segment.segment_id} exceeds the resolved timeline."
                )
            cues.append(
                ResolvedCaptionCue(
                    caption_asset_id=asset.asset_id,
                    caption_asset_sha256=asset.sha256,
                    caption_track_id=track.caption_track_id,
                    caption_timing_fingerprint=track.timing_fingerprint,
                    segment_id=segment.segment_id,
                    text=segment.text,
                    speaker_id=segment.speaker_id,
                    start_sample=start_sample,
                    end_sample=end_sample,
                    start_frame=start_frame,
                    end_frame_exclusive=end_frame,
                    style_reference_id=style.artifact_id,
                    style_content_hash=style.content_hash,
                )
            )
    cues.sort(
        key=lambda cue: (
            cue.start_sample,
            cue.end_sample,
            cue.caption_track_id,
            cue.segment_id,
            cue.caption_asset_id,
        )
    )
    return tuple(cues)


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

    audio_assets = _load_audio_assets(project, spec)
    duration_frames_by_shot = _duration_frames_by_shot(project, spec, audio_assets)

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
        if shot.visual_strategy not in {
            VisualStrategy.STATIC_IMAGE,
            VisualStrategy.GENERATED_VIDEO,
            VisualStrategy.EXISTING_VIDEO,
        }:
            raise _invalid(
                f"Shot {shot_id} uses a visual strategy unsupported by composition."
            )
        if shot.motion_directives:
            raise _invalid(f"Shot {shot_id} must not use motion_directives in P3.")
        duration_frames = duration_frames_by_shot[shot_id]
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
            is_video = shot.visual_strategy in {
                VisualStrategy.GENERATED_VIDEO,
                VisualStrategy.EXISTING_VIDEO,
            }
            expected_type = AssetType.VIDEO if is_video else AssetType.IMAGE
            if (
                expected_type not in role.allowed_asset_types
                or asset.asset_type is not expected_type
            ):
                raise _invalid(
                    f"Layer {layer.layer_id} must bind a registry "
                    f"{expected_type.value} asset."
                )
            if is_video:
                try:
                    trim_duration_frames = resolved_video_trim_duration(
                        asset,
                        layer,
                        duration_frames=duration_frames,
                        delivery_profile=spec.delivery_profile,
                    )
                except VisualMediaValidationError as exc:
                    raise _invalid(str(exc)) from exc
            else:
                if (
                    layer.trim_start_frame != 0
                    or layer.trim_duration_frames is not None
                ):
                    raise _invalid("P3 static raster layers do not implement trim.")
                trim_duration_frames = None
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
            suffix = _validated_visual_suffix(
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
                    trim_duration_frames=trim_duration_frames,
                    transform=layer.transform,
                    opacity_milli=layer.opacity_milli,
                    z_index=layer.z_index,
                    incoming_transition=incoming,
                )
            )
        cursor = start_frame + duration_frames

    shot_start_samples = {
        span.shot_id: span.start_sample
        for span in spans
    }
    total_samples = _sample_at_frame(
        cursor,
        fps=spec.delivery_profile.fps,
        sample_rate=spec.sample_rate,
    )
    audio_spans = _resolve_audio_spans(
        spec,
        audio_assets,
        shot_start_samples=shot_start_samples,
        total_samples=total_samples,
    )
    caption_cues = _resolve_caption_cues(
        project,
        spec,
        audio_assets,
        audio_spans,
        total_frames=cursor,
        total_samples=total_samples,
    )

    timeline_fields = dict(
        artifact_id=f"timeline-{spec.composition_id}",
        schema_version=spec.schema_version,
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
        total_samples=total_samples,
        composition_fingerprint="0" * 64,
    )
    if spec.schema_version == "2.1":
        timeline_fields.update(audio_spans=audio_spans, caption_cues=caption_cues)
    provisional = ResolvedTimeline(**timeline_fields)
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
