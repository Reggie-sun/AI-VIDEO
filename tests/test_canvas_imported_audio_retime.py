from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.canvas_project_data import open_canvas_project
from ai_video.production.composition_contracts import AudioKind
from ai_video.production.hyperframes import materialize_hyperframes_source
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from scripts.canvas_production_source import inspect_canvas_source
from test_canvas_project_data import _video_project_data
from test_hyperframes_native_audio_retime import _make_mp4, _tool_paths


def _author_imported_video(tmp_path: Path, *, with_audio: bool, extra_audio: bool = False):
    ffmpeg, ffprobe = _tool_paths()
    source, definition, selected_path = _video_project_data(tmp_path)
    synthetic_mp4 = _make_mp4(tmp_path, with_audio=with_audio)
    if extra_audio:
        multi = tmp_path / "two-audio-streams.mp4"
        subprocess.run([str(ffmpeg), "-v", "error", "-i", str(synthetic_mp4),
                        "-map", "0:v:0", "-map", "0:a:0", "-map", "0:a:0",
                        "-c", "copy", str(multi)], check=True, capture_output=True, timeout=30)
        synthetic_mp4 = multi
    selected_path.write_bytes(synthetic_mp4.read_bytes())

    definition["direction"]["delivery_profile"] = {
        "width": 32,
        "height": 32,
        "fps": 24,
    }
    for index, row in enumerate(definition["direction"]["shots"]):
        row["shot"]["visual_strategy"] = "existing_video"
        row["shot"].pop("generated_video_rationale", None)
        primary_visual = next(
            role
            for role in row["shot"]["required_asset_roles"]
            if role["role"] == "primary_visual"
        )
        primary_visual["asset_ids"] = ["motion-guide"]
        trim_start = 0 if index == 0 else 24
        source_duration = 24 if index == 0 else 36
        output_duration = 24
        row["composition"] = {
            "asset_role": "primary_visual",
            "asset_id": "motion-guide",
            "trim_start_frame": trim_start,
            "trim_duration_frames": source_duration,
            "source_time_map": {
                "contract_version": "video-time-map/2",
                "points": [
                    {"source_frame": 0, "output_frame": 0},
                    {
                        "source_frame": source_duration,
                        "output_frame": output_duration,
                    },
                ],
                "audio_policy": "retime_preserve_pitch",
            },
            "muted": False,
        }

    (tmp_path / "source.json").write_text(json.dumps(source), encoding="utf-8")
    project_root = tmp_path / "project"
    project_root.mkdir()
    committer = ProductionStateCommitter(project_root)
    service, registry, artifacts = open_canvas_project(
        inspection=inspect_canvas_source(source, definition["selection"]),
        definition=definition,
        data_root=tmp_path,
        committer=committer,
        resume=False,
        ffprobe_executable=ffprobe,
    )
    bundle = service.author(registry=registry, asset_artifacts=artifacts)
    bundle.bootstrap(committer=committer, attempt_id="imported-retime-author")
    loaded = load_production_project(project_root / "project.yaml")
    video = next(item for item in loaded.registry.assets if item.asset_id == "motion-guide")
    return service, loaded, video, project_root, ffmpeg, ffprobe


def _materialize(service, loaded, project_root, *, ffmpeg, ffprobe):
    _spec, timeline = service.compose()
    asset_ids = {span.asset_id for span in timeline.visual_spans}
    asset_ids.update(span.asset_id for span in timeline.audio_spans)
    materialized = materialize_hyperframes_source(
        timeline,
        asset_sources={asset_id: loaded.asset_paths[asset_id] for asset_id in asset_ids},
        allowed_asset_root=loaded.root / "assets",
        staging_root=project_root.parent / "materialized-source",
        allowed_staging_parent=project_root.parent,
        native_audio_ffmpeg_path=ffmpeg,
        native_audio_ffprobe_path=ffprobe,
    )
    return timeline, materialized


def _renderer_toolchain(tmp_path, *, ffmpeg, ffprobe):
    from test_canvas_render import _executable

    tool_root = tmp_path / "renderer-tools"
    return {
        "binary_path": tool_root / "node_modules/.bin/hyperframes",
        "browser_path": _executable(tool_root / "chrome"),
        "unshare_path": _executable(tool_root / "unshare"),
        "ip_path": _executable(tool_root / "ip"),
        "bash_path": _executable(tool_root / "bash"),
        "ffmpeg_path": ffmpeg,
        "ffprobe_path": ffprobe,
    }


def test_canvas_imported_video_reuses_distinct_native_audio_maps(tmp_path):
    service, loaded, video, project_root, ffmpeg, ffprobe = _author_imported_video(
        tmp_path, with_audio=True
    )
    assert video.source_kind.value == "imported"
    assert video.video_metadata is not None
    assert video.video_metadata.probe_receipt_id.startswith(
        "canvas-local-video-measurement:"
    )
    manifest_path = project_root / "state" / "manifest.json"
    before = manifest_path.read_bytes()

    timeline, materialized = _materialize(
        service, loaded, project_root, ffmpeg=ffmpeg, ffprobe=ffprobe
    )

    native = tuple(
        span for span in timeline.audio_spans if span.audio_kind is AudioKind.NATIVE_VIDEO
    )
    assert len(native) == 2
    assert tuple(span.track_id for span in native) == (
        "native-video-audio::canvas-one",
        "native-video-audio::canvas-two",
    )
    assert tuple((span.start_sample, span.duration_samples) for span in native) == (
        (0, 48_000),
        (48_000, 48_000),
    )
    assert tuple(
        (span.source_start_sample, span.source_duration_samples) for span in native
    ) == ((0, 48_000), (48_000, 72_000))
    assert all(span.asset_id == video.asset_id for span in native)
    assert len({span.native_audio_retime.time_map_sha256 for span in native}) == 2

    assert len(materialized.audio_bindings) == 1
    binding = materialized.audio_bindings[0]
    assert binding.resolved_track_ids == tuple(span.track_id for span in native)
    proofs = binding.native_audio_derivations
    assert tuple(proof.track_id for proof in proofs) == tuple(
        span.track_id for span in native
    )
    assert tuple(proof.mapped_samples for proof in proofs) == (48_000, 48_000)
    assert proofs[0].mapped_pcm_sha256 != proofs[1].mapped_pcm_sha256
    assert manifest_path.read_bytes() == before


@pytest.mark.parametrize("with_audio", [False, True], ids=["missing-audio", "multiple-audio"])
def test_canvas_imported_video_without_unique_audio_fails_without_state_change(
    tmp_path, with_audio,
):
    service, loaded, video, project_root, ffmpeg, ffprobe = _author_imported_video(
        tmp_path, with_audio=with_audio, extra_audio=with_audio
    )
    assert video.source_kind.value == "imported"
    manifest_path = project_root / "state" / "manifest.json"
    before = manifest_path.read_bytes()

    _spec, timeline = service.compose()
    assert len(
        tuple(
            span
            for span in timeline.audio_spans
            if span.audio_kind is AudioKind.NATIVE_VIDEO
        )
    ) == 2
    assert manifest_path.read_bytes() == before

    asset_ids = {span.asset_id for span in timeline.visual_spans}
    asset_ids.update(span.asset_id for span in timeline.audio_spans)
    with pytest.raises(AiVideoError) as caught:
        materialize_hyperframes_source(
            timeline,
            asset_sources={asset_id: loaded.asset_paths[asset_id] for asset_id in asset_ids},
            allowed_asset_root=loaded.root / "assets",
            staging_root=project_root.parent / "no-audio-staging",
            allowed_staging_parent=project_root.parent,
            native_audio_ffmpeg_path=ffmpeg,
            native_audio_ffprobe_path=ffprobe,
        )

    assert caught.value.code is ErrorCode.RENDERER_SOURCE_INVALID
    assert manifest_path.read_bytes() == before


@pytest.mark.parametrize(
    ("with_audio", "extra_audio"),
    [(False, False), (True, True)],
    ids=["missing-audio", "multiple-audio"],
)
def test_canvas_render_rejects_nonunique_native_audio_before_begin(
    tmp_path,
    monkeypatch,
    with_audio,
    extra_audio,
):
    from ai_video.production import hyperframes
    from test_production_hyperframes import FakeRunner

    service, _loaded, _video, project_root, ffmpeg, ffprobe = _author_imported_video(
        tmp_path, with_audio=with_audio, extra_audio=extra_audio
    )
    manifest_path = project_root / "state" / "manifest.json"
    before = manifest_path.read_bytes()
    runner_factory_calls = []
    runner = FakeRunner()

    def runner_factory(**_kwargs):
        runner_factory_calls.append(True)
        return runner

    monkeypatch.setattr(
        hyperframes, "_NetworkIsolatedHyperFramesRunner", runner_factory
    )
    toolchain = _renderer_toolchain(tmp_path, ffmpeg=ffmpeg, ffprobe=ffprobe)

    with pytest.raises(AiVideoError) as caught:
        service.render(
            attempt_id="invalid-imported-native-audio-render",
            toolchain=toolchain,
        )

    assert caught.value.code is ErrorCode.RENDERER_SOURCE_INVALID
    assert manifest_path.read_bytes() == before
    assert runner_factory_calls == []


def test_canvas_native_audio_failed_render_replay_skips_stream_probe(
    tmp_path,
    monkeypatch,
):
    from ai_video.production import hyperframes
    from ai_video.production import _hyperframes_native_audio as native_audio
    from test_production_hyperframes import FakeRunner

    service, _loaded, _video, project_root, ffmpeg, ffprobe = _author_imported_video(
        tmp_path, with_audio=True
    )
    runner = FakeRunner(fail_at="doctor")
    runner_factory_calls = []

    def runner_factory(**_kwargs):
        runner_factory_calls.append(True)
        return runner

    monkeypatch.setattr(
        hyperframes, "_NetworkIsolatedHyperFramesRunner", runner_factory
    )
    original_probe = native_audio._probe_source
    probe_calls = []

    def count_probe(*args, **kwargs):
        probe_calls.append(True)
        return original_probe(*args, **kwargs)

    monkeypatch.setattr(native_audio, "_probe_source", count_probe)
    toolchain = _renderer_toolchain(tmp_path, ffmpeg=ffmpeg, ffprobe=ffprobe)
    attempt_id = "native-audio-failed-render-replay"
    with pytest.raises(AiVideoError):
        service.render(attempt_id=attempt_id, toolchain=toolchain)

    failed = service._load().manifest
    manifest_path = project_root / "state" / "manifest.json"
    before_replay = manifest_path.read_bytes()
    assert len(probe_calls) == 1
    assert runner_factory_calls == [True]

    replayed = service.render(attempt_id=attempt_id, toolchain=toolchain)

    assert replayed == failed
    assert manifest_path.read_bytes() == before_replay
    assert len(probe_calls) == 1
    assert runner_factory_calls == [True]


@pytest.mark.parametrize("capture_version", [2, 3])
def test_imported_capture_keeps_its_native_audio_admission_boundary(tmp_path, capture_version):
    from ai_video.production._composition_native_audio import _native_audio_probe
    from ai_video.production.video_retime import VideoTimeMap, VideoTimePoint
    from test_repair_input_admission import _inputs, _preview_arguments

    source, target, writer, arguments = _inputs(tmp_path, close=True, abandon=True)
    preview_use, preview_probe, _shot = _preview_arguments(source, arguments)
    if capture_version == 3:
        preview_use.update(
            scope="retimed_av_preview",
            source_time_map=VideoTimeMap(
                contract_version="video-time-map/2",
                points=(VideoTimePoint(source_frame=0, output_frame=0),
                        VideoTimePoint(source_frame=48, output_frame=40)),
                audio_policy="retime_preserve_pitch",
            ),
        )
    writer.bootstrap_repair_input(
        **arguments, preview_use=preview_use, preview_probe=preview_probe,
    )
    loaded = load_production_project(target / "project.yaml")
    asset = next(item for item in loaded.registry.assets if item.asset_id == "failed-source")
    assert asset.source_kind.value == "imported"
    manifest_path = target / "state" / "manifest.json"
    before = manifest_path.read_bytes()

    def invalid(message, detail=None):
        return AiVideoError(code=ErrorCode.RENDERER_SOURCE_INVALID,
                            user_message=message, technical_detail=detail, retryable=False)

    if capture_version == 2:
        with pytest.raises(AiVideoError, match="development-repair-input/3"):
            _native_audio_probe(loaded, asset, invalid=invalid)
    else:
        probe = _native_audio_probe(loaded, asset, invalid=invalid)
        assert probe is not None
        assert probe == preview_probe
        assert probe.measured.audio_stream_count == 1
    assert manifest_path.read_bytes() == before
