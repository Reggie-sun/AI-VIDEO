"""Canonical offline HyperFrames seam shared by Ecommerce Job integration tests."""

from __future__ import annotations

from pathlib import Path

from ai_video.production.ecommerce_job_assembly import (
    EcommerceCompositionExecutionPlan,
    EcommerceHyperFramesInvocation,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from test_production_hyperframes import (
    FakeRunner,
    _CountingRenderCommitter,
    _Manifest25RenderFixture,
    _write_executable,
)


def prepare_offline_ecommerce_render(
    root: Path,
    monkeypatch,
    runtime_handoff,
    plan,
    compiled_handoff,
    *,
    attempt_id: str,
    media_path: Path,
):
    tools = root / "ecommerce-offline-render-tools"
    binary = tools / "node_modules/.bin/hyperframes"
    binary.parent.mkdir(parents=True, exist_ok=True)
    browser = _write_executable(tools / "chrome")
    unshare = _write_executable(tools / "unshare")
    ip_path = _write_executable(tools / "ip")
    bash = _write_executable(tools / "bash")
    ffmpeg = _write_executable(tools / "ffmpeg")
    ffprobe = _write_executable(tools / "ffprobe")
    committer = _CountingRenderCommitter(root)
    fixture_ref = {}
    composition = EcommerceCompositionExecutionPlan(
        handoff=compiled_handoff,
        plan=plan,
        renderer_version="0.7.103",
        hyperframes=EcommerceHyperFramesInvocation(
            committer=committer,
            attempt_id=attempt_id,
            selection_receipt_id=f"{attempt_id}-selection",
            binary_path=binary,
            browser_path=browser,
            unshare_path=unshare,
            ip_path=ip_path,
            bash_path=bash,
            ffmpeg_path=ffmpeg,
            ffprobe_path=ffprobe,
            dependency_transition_preparer=lambda activation: fixture_ref[
                "fixture"
            ].prepare_transition(activation),
        ),
    )
    prepared = composition.prepare(runtime_handoff, project_root=root)
    loaded = load_production_project(root / "project.yaml")
    fixture = _Manifest25RenderFixture(
        root=root,
        committer=committer,
        begin_request=prepared.begin_request,
        timeline=prepared.timeline,
        asset_sources=dict(prepared.asset_sources),
        browser=browser,
        ip_path=ip_path,
        runner=FakeRunner(),
        dependency_graph=loaded.dependency_graph,
        candidate_dependency_states=loaded.manifest.dependency_states,
        changed_nodes=[],
    )
    fixture_ref["fixture"] = fixture
    original_run = fixture.runner.run

    def render_fixture_media(command, args, *, cwd, env, timeout_seconds):
        result = original_run(
            command, args, cwd=cwd, env=env, timeout_seconds=timeout_seconds
        )
        if command == "render" and result.returncode == 0:
            Path(args[args.index("-o") + 1]).write_bytes(media_path.read_bytes())
        return result

    monkeypatch.setattr(fixture.runner, "run", render_fixture_media)
    monkeypatch.setattr(
        "ai_video.production.hyperframes._NetworkIsolatedHyperFramesRunner",
        lambda **_kwargs: fixture.runner,
    )
    monkeypatch.setattr(
        "ai_video.production.hyperframes.probe_clip_fd_with_executable",
        lambda _fd, _path: {
            "streams": [
                {
                    "codec_type": "video",
                    "width": prepared.timeline.delivery_profile.width,
                    "height": prepared.timeline.delivery_profile.height,
                    "r_frame_rate": f"{prepared.timeline.delivery_profile.fps}/1",
                    "nb_frames": str(prepared.timeline.total_frames),
                    "codec_name": "h264",
                },
                {
                    "codec_type": "audio",
                    "index": 1,
                    "codec_name": "aac",
                    "sample_rate": str(prepared.timeline.sample_rate),
                    "channels": 2,
                    "channel_layout": "stereo",
                },
            ],
            "packets": [
                {
                    "stream_index": 1,
                    "pts": "-1024",
                    "duration": "1024",
                    "side_data_list": [
                        {
                            "side_data_type": "Skip Samples",
                            "skip_samples": 1024,
                            "discard_padding": 0,
                        }
                    ],
                },
                {"stream_index": 1, "pts": "0", "duration": "768"},
            ],
        },
    )
    monkeypatch.setattr(
        "ai_video.production.hyperframes.decoded_audio_sha256_fd_with_executable",
        lambda _fd, _rate, _channels, _path: (
            prepared.timeline.total_samples + 256,
            "a" * 64,
        ),
    )
    monkeypatch.setattr(
        "ai_video.production.hyperframes.decoded_frame_sha256_fd",
        lambda _fd: "b" * 64,
    )
    return composition, prepared, fixture
