"""Public Canvas uses the canonical production planner before quality regeneration."""
import pytest

from ai_video.canvas_authoring import direction_reference
from ai_video.canvas_production import CanvasProductionService
from ai_video.errors import AiVideoError
from ai_video.production.hashing import seal_artifact
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import prepare_project_registry_commit
from production_strategy_factory import make_persisted_strategy_fixture


def strategy_canvas(tmp_path, *, with_cut_requirements=False, reverse_order=False):
    fixture = make_persisted_strategy_fixture(tmp_path)
    loaded = load_production_project(tmp_path / "project.yaml")
    packet = {"fixture": "canvas-strategy"}
    direction = {"project_id": loaded.project.project_id, "shots": [
        {"occurrence_id": shot_id, "shot": {"shot_id": shot_id}}
        for beat in loaded.storyboard.beats for shot_id in beat.shot_ids]}
    if with_cut_requirements:
        assets = {asset.asset_id: asset for asset in loaded.registry.assets}
        for row, shot in zip(direction["shots"], loaded.shots):
            if shot.production_intent is None:
                role, asset_id = next((role, asset_id) for role in shot.required_asset_roles
                    for asset_id in role.asset_ids if assets[asset_id].asset_type.value in {"image", "video"})
                row["composition"] = {"asset_role": role.role, "asset_id": asset_id}
        ordered = list(reversed(direction["shots"])) if reverse_order else direction["shots"]
        if reverse_order:
            direction["composition_order"] = [row["occurrence_id"] for row in ordered]
        direction["cut_requirements"] = [
            {"from_occurrence_id": left["occurrence_id"], "to_occurrence_id": right["occurrence_id"],
             "kind": "scene_reset", "checks": {"action": "Verify the authored occurrence boundary."}}
            for left, right in zip(ordered, ordered[1:])]
    project = seal_artifact(loaded.project.model_copy(update={
        "revision": loaded.project.revision + 1, "content_hash": "0" * 64,
        "source_provenance": (*loaded.project.source_provenance, direction_reference(packet, direction))}))
    request = prepare_project_registry_commit(manifest=loaded.manifest, project=project,
        registry=loaded.registry, attempt_id="canvas-binding")
    from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
    request = prepare_strategy_dependency_transition(base_loaded=loaded,
        candidate_loaded=loaded.model_copy(update={"project": project}), request=request)
    fixture.committer.commit(request)
    return fixture, CanvasProductionService(committer=fixture.committer, packet=packet, direction=direction)


def test_canvas_plans_materializes_and_reopens_existing_owner_without_generation(tmp_path):
    fixture, service = strategy_canvas(tmp_path)
    before = (tmp_path / "state/manifest.json").read_bytes()
    assert service.position().next_action == "prepare_production"
    decision = service.prepare_production(parent_shot_id=fixture.parent_shot_id)
    assert decision.selected is not None and decision.selected.new_generation_count == 0
    assert (tmp_path / "state/manifest.json").read_bytes() == before
    service.materialize_production(decision=decision.model_dump(mode="json"), attempt_id="canvas-means")
    assert service._load().shots[0].shot_id == fixture.child_shot_id
    spec, timeline = service.compose_production(decision=decision.model_dump(mode="json"))
    assert spec.shot_ids == (fixture.child_shot_id,)
    assert timeline.visual_spans[0].asset_id == decision.selected.units[0].source.asset_id
    assert not any(a.video_generation_state for a in service._load().manifest.attempts)


@pytest.mark.parametrize("action", ["prepare_repair", "start_repair"])
@pytest.mark.parametrize("include_generation_intervention", [True, False])
def test_closed_quality_cannot_skip_editing_authoring_and_regenerate(tmp_path, action, include_generation_intervention):
    from test_canvas_recovery import failed_canvas, close_failure
    service, provider, limits, old, _, intervention = failed_canvas(tmp_path)
    close_failure(service, old)
    before = (service.committer.project_root / "state/manifest.json").read_bytes()
    history = service.committer.read_generation_experiences()
    with pytest.raises(AiVideoError, match="ProductionIntent.*existing-source/edit"):
        getattr(service, action)(limits=limits, interventions=(intervention,) if include_generation_intervention else ())
    assert (service.committer.project_root / "state/manifest.json").read_bytes() == before
    assert service.committer.read_generation_experiences() == history
    assert provider.call_counts.submit == 1  # Only the scripted predecessor.


def test_canvas_time_map_requires_explicit_mute_and_preserves_resolved_segments(tmp_path):
    from ai_video.canvas_composition import compose_canvas
    from production_project_factory import make_loaded_project_and_spec
    from test_production_video_retime import _with_video_layer, _time_map
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    mapping = _time_map((0, 0), (24, 12), (60, 48))
    rows = [{"occurrence_id": layer.shot_id, "shot": {"shot_id": layer.shot_id},
             "composition": {"asset_role": layer.asset_role, "asset_id": layer.asset_id}}
            for layer in spec.layers]
    rows[0]["composition"].update(trim_start_frame=12, trim_duration_frames=60,
        source_time_map=mapping.model_dump(mode="json"))
    with pytest.raises(ValueError, match="explicit muted"):
        compose_canvas(loaded=loaded, direction={"shots": rows}, renderer_version="0.7.103")
    rows[0]["composition"]["muted"] = True
    authored, timeline = compose_canvas(loaded=loaded, direction={"shots": rows}, renderer_version="0.7.103")
    assert authored.schema_version == timeline.schema_version == "2.3"
    pieces = [s for s in timeline.visual_spans if s.shot_id == rows[0]["shot"]["shot_id"]]
    assert [(s.trim_start_frame, s.trim_duration_frames, s.duration_frames) for s in pieces[:12]] == [
        (12 + 2 * n, 1, 1) for n in range(12)]
    assert (pieces[-1].trim_start_frame, pieces[-1].trim_duration_frames, pieces[-1].duration_frames) == (36, 36, 36)


@pytest.mark.parametrize("audio_shot_id", ["shot-1", None, "shot-2"])
def test_canvas_retime_validates_appended_audio_at_public_boundary(tmp_path, audio_shot_id):
    from ai_video.canvas_composition import compose_canvas
    from ai_video.production.composition_contracts import AudioTrackSpec
    from production_project_factory import make_p4_composition_fixture
    from test_production_video_retime import _with_video_layer, _time_map
    loaded, spec = make_p4_composition_fixture(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    rows = [{"occurrence_id": layer.shot_id, "shot": {"shot_id": layer.shot_id},
             "composition": {"asset_role": layer.asset_role, "asset_id": layer.asset_id}}
            for layer in spec.layers]
    rows[0]["composition"].update(trim_start_frame=12, trim_duration_frames=60,
        source_time_map=_time_map((0, 0), (24, 12), (60, 48)).model_dump(mode="json"), muted=True)
    track = AudioTrackSpec(track_id="ambience", asset_id="ambience-room", audio_kind="ambience",
                           shot_id=audio_shot_id, trim_duration_samples=96_000,
                           **({"start_sample": 0} if audio_shot_id is None else {}))
    if audio_shot_id != "shot-2":
        with pytest.raises(ValueError, match="muted|audio|caption|voice"):
            compose_canvas(loaded=loaded, direction={"shots": rows}, renderer_version="0.7.103",
                           audio_tracks=(track,))
    else:
        _, timeline = compose_canvas(loaded=loaded, direction={"shots": rows}, renderer_version="0.7.103",
                                     audio_tracks=(track,))
        assert timeline.audio_spans[0].track_id == "ambience"
        assert timeline.audio_spans[0].start_sample == 96_000


@pytest.mark.parametrize("caption_shot_id", [None, "shot-2"])
def test_canvas_retime_validates_appended_captions_at_public_boundary(tmp_path, caption_shot_id):
    from ai_video.canvas_composition import compose_canvas
    from ai_video.production.composition_contracts import AudioTrackSpec
    from production_project_factory import make_p4_composition_fixture
    from test_production_video_retime import _with_video_layer, _time_map
    loaded, spec = make_p4_composition_fixture(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    rows = [{"occurrence_id": layer.shot_id, "shot": {"shot_id": layer.shot_id},
             "composition": {"asset_role": layer.asset_role, "asset_id": layer.asset_id}}
            for layer in spec.layers]
    rows[0]["composition"].update(trim_start_frame=12, trim_duration_frames=60,
        source_time_map=_time_map((0, 0), (24, 12), (60, 48)).model_dump(mode="json"), muted=True)
    track = AudioTrackSpec(track_id="dialogue-second", asset_id="voice-dialogue", audio_kind="dialogue",
                           shot_id="shot-2", trim_duration_samples=96_000)
    caption = spec.caption_tracks[0].model_copy(update={
        "shot_id": caption_shot_id, "source_audio_track_id": track.track_id})
    if caption_shot_id is None:
        with pytest.raises(ValueError, match="muted|audio|caption|voice"):
            compose_canvas(loaded=loaded, direction={"shots": rows}, renderer_version="0.7.103",
                           audio_tracks=(track,), caption_tracks=(caption,))
    else:
        _, timeline = compose_canvas(loaded=loaded, direction={"shots": rows}, renderer_version="0.7.103",
                                     audio_tracks=(track,), caption_tracks=(caption,))
        assert timeline.caption_cues[0].start_sample == 97_000


@pytest.mark.parametrize("reverse_order", [False, True])
def test_materialized_canvas_render_keeps_canonical_external_cut_evidence(tmp_path, monkeypatch, reverse_order):
    import subprocess
    from pathlib import Path
    from ai_video.production.captions import caption_style_fingerprint
    from ai_video.production.hyperframes import RendererCommandResult
    from production_e2e_support import DeterministicHyperFramesRunner, require_audio_toolchain
    from test_canvas_render import _executable
    import ai_video.production.hyperframes as hyperframes
    fixture, service = strategy_canvas(tmp_path, with_cut_requirements=True, reverse_order=reverse_order)
    decision = service.prepare_production(parent_shot_id=fixture.parent_shot_id)
    service.materialize_production(decision=decision.model_dump(mode="json"), attempt_id="cut-means")
    audio_tools = require_audio_toolchain()
    class Renderer(DeterministicHyperFramesRunner):
        def run(self, command, args, **kwargs):
            if command != "render":
                return super().run(command, args, **kwargs)
            mixed = next((Path(kwargs["cwd"]) / "assets").glob("*.wav"))
            result = subprocess.run([str(self.ffmpeg_path), "-nostdin", "-v", "error", "-y", "-f", "lavfi",
                "-i", "color=c=blue:s=1280x720:r=24:d=5", "-i", str(mixed), "-t", "5", "-c:v", "libx264",
                "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-threads", "1", "-c:a", "aac", "-ar", "48000",
                "-ac", "2", args[args.index("-o") + 1]], capture_output=True, timeout=30)
            return RendererCommandResult(returncode=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode())
    runner = Renderer(audio_tools.ffmpeg_path)
    monkeypatch.setattr(hyperframes, "_NetworkIsolatedHyperFramesRunner", lambda **_kwargs: runner)
    tools = tmp_path / "renderer-tools"
    toolchain = {"binary_path": tools / "node_modules/.bin/hyperframes",
        "browser_path": _executable(tools / "chrome"), "unshare_path": _executable(tools / "unshare"),
        "ip_path": _executable(tools / "ip"), "bash_path": _executable(tools / "bash"),
        "ffmpeg_path": audio_tools.ffmpeg_path, "ffprobe_path": audio_tools.ffprobe_path}
    spec, _ = service.compose()
    styles = tuple((binding.style_reference.artifact_id, caption_style_fingerprint(
        binding.style_reference, (tmp_path / binding.style_reference.path).read_bytes()))
        for binding in spec.caption_tracks)
    service.render(attempt_id="cut-render", toolchain=toolchain, caption_style_fingerprints=styles)
    packet = service.cut_packet()
    boundary = packet["cuts"][0]["evidence"]["to" if reverse_order else "from"]
    assert boundary["shot_id"] == fixture.child_shot_id
    assert boundary["source_start_frame"] == 4
    assert boundary["source_last_frame"] == 75
    assert boundary["production_family_shot_ids"] == [fixture.child_shot_id]
    assert packet["cuts"][0]["evidence"]["to"]["start_frame"] == (48 if reverse_order else 72)
    assert packet["production_acceptance"] == "NOT_EVALUATED"


def test_family_audio_is_present_during_other_shot_native_audio_projection(tmp_path, monkeypatch):
    """Pure adapter boundary: the native-audio owner is scripted, never qualified here."""
    from ai_video.canvas_composition import compose_canvas
    from ai_video.production.models import AssetRoleRequirement, VisualStrategy
    fixture, service = strategy_canvas(tmp_path)
    decision = service.prepare_production(parent_shot_id=fixture.parent_shot_id)
    service.materialize_production(decision=decision.model_dump(mode="json"), attempt_id="mixed-means")
    loaded = service._load()
    video = next(a for a in loaded.registry.assets if a.asset_id == "strategy-imported-video")
    ordinary = loaded.shots[1].model_copy(update={"visual_strategy": VisualStrategy.EXISTING_VIDEO, "required_asset_roles": (
        AssetRoleRequirement(role="primary_visual", asset_ids=(video.asset_id,), allowed_asset_types=("video",)),)})
    loaded = loaded.model_copy(update={"shots": (loaded.shots[0], ordinary)})
    monkeypatch.setattr("ai_video.canvas_composition._native_audio_matches",
                        lambda _loaded, audio, _video, _shot: audio.asset_id == "voice-dialogue")
    spec, timeline = compose_canvas(loaded=loaded, direction=service.direction, renderer_version="0.7.103")
    assert {track.track_id for track in spec.audio_tracks} == {"strategy-dialogue", "canvas-native-shot-2"}
    assert timeline.total_frames == 120
