"""Canvas selections to existing CompositionSpec; no source-tick timeline engine."""
from ai_video.production.composition import resolve_composition
from ai_video.production.composition_contracts import (
    AudioTrackSpec, CompositionLayerSpec, CompositionSpec, TransitionSpec,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import SourceReference


def compose_canvas(*, loaded, direction, renderer_version, audio_tracks=(), caption_tracks=(), voice_sources=()):
    layers = []
    tracks = tuple(AudioTrackSpec.model_validate(t) if isinstance(t, dict) else t for t in audio_tracks)
    assets = {a.asset_id: a for a in loaded.registry.assets}
    for row in direction["shots"]:
        shot = next(s for s in loaded.shots if s.shot_id == row["shot"]["shot_id"])
        settings = dict(row.get("composition", {}))
        if set(settings) - {"asset_role", "asset_id", "trim_start_frame", "trim_duration_frames",
                            "transform", "speed", "muted", "volume"}:
            raise ValueError("unsupported source composition settings")
        if settings.pop("speed", 1) != 1 or settings.pop("volume", 1) != 1:
            raise ValueError("source speed/gain requires explicit existing composition authoring")
        muted = settings.pop("muted", False)
        if type(muted) is not bool:
            raise ValueError("muted must be an explicit boolean")
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
            if not any(assets[t.asset_id].audio_metadata is not None and
                       assets[t.asset_id].creation_receipt_id.startswith("generated-video-audio-") and
                       assets[t.asset_id].audio_metadata.source.input_fingerprint == asset.sha256
                       for t in bound_tracks):
                raise ValueError("native video audio needs its exact registered WAV track or explicit mute")
        if (shot.dialogue or shot.narration) and not any(t.shot_id == shot.shot_id and
                t.audio_kind.value in {"dialogue", "narration"} for t in tracks):
            raise ValueError("authored dialogue/narration must remain present in the final audio tracks")
        layers.append(CompositionLayerSpec(layer_id=f"canvas-{shot.shot_id}", shot_id=shot.shot_id,
            asset_role=role, asset_id=asset_id, **settings))
    order = tuple(row["shot"]["shot_id"] for row in direction["shots"])
    p4 = {"schema_version": "2.1", "audio_tracks": tracks, "caption_tracks": tuple(caption_tracks),
          "voice_sources": tuple(voice_sources)} if tracks or caption_tracks or voice_sources else {}
    spec = seal_artifact(CompositionSpec(artifact_id="canvas-composition", composition_id="canvas-composition",
        revision=1, content_hash="0" * 64, creation_receipt_id="canvas-composition-authoring",
        source_provenance=(SourceReference(kind="derived", reference=loaded.project.artifact_id,
                                         content_hash=loaded.project.content_hash),),
        shot_ids=order, layers=tuple(layers), delivery_profile=loaded.project.delivery_profile,
        transitions=tuple(TransitionSpec(from_shot_id=a, to_shot_id=b, kind="cut", duration_frames=0)
                          for a, b in zip(order, order[1:])),
        **p4))
    return spec, resolve_composition(loaded, spec, renderer_version)
