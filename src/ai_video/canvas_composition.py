"""Canvas selections to existing CompositionSpec; no source-tick timeline engine."""
from ai_video.production.composition import resolve_composition
from ai_video.production.composition_contracts import (
    AudioTrackSpec, CompositionLayerSpec, CompositionSpec, TransitionSpec,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import SourceReference


def _native_audio_matches(loaded, audio, video, shot):
    if (audio.audio_metadata is None or not audio.creation_receipt_id.startswith("generated-video-audio-")
            or audio.audio_metadata.source.input_fingerprint != video.sha256):
        return False
    import json
    from ai_video.production._generated_video_audio_contracts import (
        GeneratedVideoAudioReceipt, canonical_generated_video_audio_receipt_path,
    )
    from ai_video.production.paths import _read_regular_file_nofollow
    from ai_video.production._sequence_source import accepted_sequence_source
    digest = audio.creation_receipt_id.removeprefix("generated-video-audio-")
    raw = _read_regular_file_nofollow(loaded.root / canonical_generated_video_audio_receipt_path(digest),
                                    contained_by=loaded.root)
    if raw.file_sha256 != digest:
        raise ValueError("native audio receipt bytes changed")
    receipt = GeneratedVideoAudioReceipt.model_validate(json.loads(raw.data))
    _, request, _, _, _ = accepted_sequence_source(loaded, shot)
    return (receipt.target_asset_id == audio.asset_id and receipt.probe.file_sha256 == audio.sha256
            and receipt.source_request.request_input_hash == request.request_input_hash
            and receipt.source_fetch.artifact_sha256 == video.sha256)


def compose_canvas(*, loaded, direction, renderer_version, audio_tracks=(), caption_tracks=(), voice_sources=()):
    layers = []
    tracks = [AudioTrackSpec.model_validate(t) if isinstance(t, dict) else t for t in audio_tracks]
    native = []
    assets = {a.asset_id: a for a in loaded.registry.assets}
    by_occurrence = {row["occurrence_id"]: row for row in direction["shots"]}
    selected_order = direction.get("composition_order", list(by_occurrence))
    if (not isinstance(selected_order, list) or len(selected_order) != len(by_occurrence)
            or set(selected_order) != set(by_occurrence)):
        raise ValueError("composition_order must contain every selected occurrence exactly once")
    rows = [by_occurrence[identity] for identity in selected_order]
    for row in rows:
        shot = next(s for s in loaded.shots if s.shot_id == row["shot"]["shot_id"])
        settings = dict(row.get("composition", {}))
        if set(settings) - {"asset_role", "asset_id", "trim_start_frame", "trim_duration_frames",
                            "transform", "speed", "muted", "volume", "source_time_map"}:
            raise ValueError("unsupported source composition settings")
        if settings.pop("speed", 1) != 1 or settings.pop("volume", 1) != 1:
            raise ValueError("source speed/gain requires explicit existing composition authoring")
        muted = settings.pop("muted", False)
        if type(muted) is not bool:
            raise ValueError("muted must be an explicit boolean")
        if settings.get("source_time_map") is not None and not muted:
            raise ValueError("retimed video requires explicit muted=true; source audio has no sample time map")
        role = settings.pop("asset_role", "primary_visual")
        candidates = [i for r in shot.required_asset_roles if r.role == role for i in r.asset_ids]
        asset_id = settings.pop("asset_id", None)
        if asset_id is None:
            if len(candidates) != 1:
                raise ValueError("choose one actual adopted asset for the composition role")
            asset_id = candidates[0]
        if asset_id not in candidates:
            raise ValueError("composition selects a version not adopted by this Shot")
        asset = assets[asset_id]
        if asset.asset_type.value == "video" and not muted:
            # Registered audio carries a canonical derivation identity. Do not
            # count arbitrary per-Shot BGM as preserved source dialogue/sound.
            bound_tracks = [t for t in tracks if t.shot_id == shot.shot_id]
            matches = [a for a in assets.values() if _native_audio_matches(loaded, a, asset, shot)]
            if not bound_tracks and len(matches) == 1:
                native.append((shot, matches[0]))
            elif not any(_native_audio_matches(loaded, assets[t.asset_id], asset, shot) for t in bound_tracks):
                raise ValueError("native video audio needs its exact registered WAV track or explicit mute")
        layers.append(CompositionLayerSpec(layer_id=f"canvas-{shot.shot_id}", shot_id=shot.shot_id,
            asset_role=role, asset_id=asset_id, **settings))
    order = tuple(row["shot"]["shot_id"] for row in rows)
    spec = CompositionSpec(artifact_id="canvas-composition", composition_id="canvas-composition",
        schema_version="2.3" if any(layer.source_time_map is not None for layer in layers) else "2.0",
        revision=1, content_hash="0" * 64, creation_receipt_id="canvas-composition-authoring",
        source_provenance=(SourceReference(kind="derived", reference=loaded.project.artifact_id,
                                         content_hash=loaded.project.content_hash),),
        shot_ids=order, layers=tuple(layers), delivery_profile=loaded.project.delivery_profile,
        transitions=tuple(TransitionSpec(from_shot_id=a, to_shot_id=b, kind="cut", duration_frames=0)
                          for a, b in zip(order, order[1:])),
        )
    if native:
        from ai_video.production.composition import _sample_at_frame
        visual = resolve_composition(loaded, seal_artifact(spec), renderer_version)
        for shot, audio in native:
            span = next(s for s in visual.visual_spans if s.shot_id == shot.shot_id)
            start = _sample_at_frame(span.trim_start_frame, fps=visual.delivery_profile.fps, sample_rate=spec.sample_rate)
            stop = _sample_at_frame(span.trim_start_frame + span.duration_frames,
                fps=visual.delivery_profile.fps, sample_rate=spec.sample_rate)
            tracks.append(AudioTrackSpec(track_id=f"canvas-native-{shot.shot_id}", shot_id=shot.shot_id,
                asset_id=audio.asset_id, audio_kind=audio.audio_metadata.audio_kind,
                trim_start_sample=start, trim_duration_samples=stop - start))
    for row in rows:
        shot = next(s for s in loaded.shots if s.shot_id == row["shot"]["shot_id"])
        if (shot.dialogue or shot.narration) and not any(t.shot_id == shot.shot_id and
                t.audio_kind.value in {"dialogue", "narration"} for t in tracks):
            raise ValueError("authored dialogue/narration must remain present in the final audio tracks")
    if tracks or caption_tracks or voice_sources:
        spec = spec.model_copy(update={"schema_version": "2.3" if spec.schema_version == "2.3" else "2.1", "audio_tracks": tuple(tracks),
            "caption_tracks": tuple(caption_tracks), "voice_sources": tuple(voice_sources)})
    spec = seal_artifact(spec)
    return spec, resolve_composition(loaded, spec, renderer_version)
