from __future__ import annotations

import importlib
import json
import os
import stat
import threading
from pathlib import Path

import pytest

from ai_video_mcp.tools.analyze import video_analyze

from conftest import skip_no_ffmpeg


ROOT = Path(__file__).resolve().parents[1]
HOOK_CONFIG_PATH = ROOT / ".codex" / "hooks.json"
CLAUDE_HOOK_CONFIG_PATH = ROOT / ".claude" / "settings.json"
CLAUDE_MCP_CONFIG_PATH = ROOT / ".mcp.json"


def _analysis_hook():
    return importlib.import_module("ai_video_mcp.analysis_hook")


def _generated_event(video: Path, *, tool_name: str = "Bash") -> dict[str, object]:
    return {
        "hook_event_name": "PostToolUse",
        "session_id": "analysis-hook-test",
        "tool_name": tool_name,
        "tool_use_id": "tool-1",
        "cwd": str(video.parent),
        "tool_response": {
            "output": json.dumps(
                {
                    "status": "succeeded",
                    "output_path": str(video),
                }
            )
        },
    }


@skip_no_ffmpeg
class TestVideoAnalyze:
    def test_analyze_full(self, tiny_video, mcp_config, mcp_cache):
        result = video_analyze(
            str(tiny_video), mcp_config, mcp_cache,
            extract_frames=True,
            transcribe_audio=False,
            detect_scenes=True,
        )
        assert "probe" in result
        assert "frames" in result
        assert "scenes" in result
        assert result["transcription"] is None
        assert "analysis_summary" in result
        assert result["analysis_summary"]["resolution"] == "320x240"

    def test_analyze_no_frames(self, tiny_video, mcp_config, mcp_cache):
        result = video_analyze(
            str(tiny_video), mcp_config, mcp_cache,
            extract_frames=False,
            transcribe_audio=False,
            detect_scenes=False,
        )
        assert result["frames"] is None
        assert result["scenes"] is None

    def test_analyze_summary_fields(self, tiny_video, mcp_config, mcp_cache):
        result = video_analyze(
            str(tiny_video), mcp_config, mcp_cache,
            extract_frames=True,
            transcribe_audio=False,
            detect_scenes=True,
        )
        s = result["analysis_summary"]
        assert "duration_hms" in s
        assert "resolution" in s
        assert "has_audio" in s
        assert "scene_count" in s
        assert "frames_extracted" in s


def test_generated_local_mp4_is_queued_once_without_blocking(tmp_path: Path) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    video = project_root / "runs" / "candidate.mp4"
    video.parent.mkdir()
    video.write_bytes(b"bounded-mp4-fixture")
    state_root = tmp_path / "state"
    spawned: list[Path] = []

    first = hook.process_post_tool_event(
        _generated_event(video),
        project_root=project_root,
        state_root=state_root,
        spawn_worker=spawned.append,
    )
    second = hook.process_post_tool_event(
        _generated_event(video),
        project_root=project_root,
        state_root=state_root,
        spawn_worker=spawned.append,
    )

    assert first["continue"] is True
    assert first["systemMessage"].startswith("Queued background video analysis")
    assert second == {"continue": True}
    assert len(spawned) == 1
    job_path = spawned[0]
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "ai-video-analysis-hook/1"
    assert payload["source_path"] == str(video.resolve())
    assert payload["source_size"] == video.stat().st_size
    assert stat.S_IMODE(job_path.stat().st_mode) == 0o600
    assert not any(state_root.rglob("*.mp4"))


def test_only_successful_fresh_repo_local_mp4_outputs_are_accepted(
    tmp_path: Path,
) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    valid = project_root / "valid.mp4"
    valid.write_bytes(b"video")
    outside = tmp_path / "outside.mp4"
    outside.write_bytes(b"outside")
    not_video = project_root / "frame.png"
    not_video.write_bytes(b"png")
    state_root = tmp_path / "state"
    spawned: list[Path] = []

    events = [
        {
            **_generated_event(valid),
            "tool_response": {
                "output": json.dumps(
                    {"status": "failed", "output_path": str(valid)}
                )
            },
        },
        _generated_event(outside),
        _generated_event(not_video),
        {
            **_generated_event(valid),
            "tool_response": {"output": f"generated {valid}"},
        },
    ]
    old = 1_600_000_000
    os.utime(valid, (old, old))
    events.append(_generated_event(valid))

    for event in events:
        assert hook.process_post_tool_event(
            event,
            project_root=project_root,
            state_root=state_root,
            spawn_worker=spawned.append,
        ) == {"continue": True}

    assert spawned == []


def test_video_analysis_tool_results_do_not_recursively_enqueue(tmp_path: Path) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    video = project_root / "candidate.mp4"
    video.write_bytes(b"video")
    spawned: list[Path] = []

    result = hook.process_post_tool_event(
        _generated_event(video, tool_name="mcp__video-analysis__video_analyze"),
        project_root=project_root,
        state_root=tmp_path / "state",
        spawn_worker=spawned.append,
    )

    assert result == {"continue": True}
    assert spawned == []


def test_structured_video_generator_result_is_queued(tmp_path: Path) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    video = project_root / "candidate.mp4"
    video.write_bytes(b"video")
    spawned: list[Path] = []
    event = {
        **_generated_event(video, tool_name="mcp__open_video__generate_video"),
        "tool_response": {"status": "succeeded", "local_path": str(video)},
    }

    result = hook.process_post_tool_event(
        event,
        project_root=project_root,
        state_root=tmp_path / "state",
        spawn_worker=spawned.append,
    )

    assert result["continue"] is True
    assert len(spawned) == 1


def test_claude_mcp_content_response_is_queued(tmp_path: Path) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    video = project_root / "candidate.mp4"
    video.write_bytes(b"video")
    event = {
        **_generated_event(video, tool_name="mcp__open_video__generate_video"),
        "tool_response": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {"status": "succeeded", "local_path": str(video)}
                    ),
                }
            ]
        },
    }
    spawned: list[Path] = []

    result = hook.process_post_tool_event(
        event,
        project_root=project_root,
        state_root=tmp_path / "state",
        spawn_worker=spawned.append,
    )

    assert result["continue"] is True
    assert len(spawned) == 1


def test_relative_output_path_is_resolved_from_event_cwd(tmp_path: Path) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    output_root = project_root / "runs" / "attempt"
    output_root.mkdir(parents=True)
    video = output_root / "candidate.mp4"
    video.write_bytes(b"video")
    event = {
        **_generated_event(video),
        "cwd": str(output_root),
        "tool_response": {
            "output": json.dumps(
                {"status": "succeeded", "output_path": "candidate.mp4"}
            )
        },
    }
    spawned: list[Path] = []

    result = hook.process_post_tool_event(
        event,
        project_root=project_root,
        state_root=tmp_path / "state",
        spawn_worker=spawned.append,
    )

    assert result["continue"] is True
    assert len(spawned) == 1
    payload = json.loads(spawned[0].read_text(encoding="utf-8"))
    assert payload["source_path"] == str(video.resolve())


def test_one_tool_result_has_a_bounded_worker_fanout(tmp_path: Path) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    videos = []
    for index in range(7):
        video = project_root / f"candidate-{index}.mp4"
        video.write_bytes(f"video-{index}".encode())
        videos.append(video)
    event = {
        **_generated_event(videos[0]),
        "tool_response": {
            "status": "succeeded",
            "artifacts": [{"video_path": str(video)} for video in videos],
        },
    }
    spawned: list[Path] = []

    result = hook.process_post_tool_event(
        event,
        project_root=project_root,
        state_root=tmp_path / "state",
        spawn_worker=spawned.append,
    )

    assert result["continue"] is True
    assert len(spawned) == 1
    batch = json.loads(spawned[0].read_text(encoding="utf-8"))
    assert len(batch["batch_job_paths"]) == len(videos)
    assert len(list((tmp_path / "state" / "queue").glob("*.json"))) == len(videos)

    replayed: list[Path] = []
    assert hook.process_post_tool_event(
        event,
        project_root=project_root,
        state_root=tmp_path / "state",
        spawn_worker=replayed.append,
    ) == {"continue": True}
    assert replayed == []

    analyzed: list[bytes] = []
    receipts = hook.process_job_batch(
        spawned[0],
        analyze=lambda path: analyzed.append(Path(path).read_bytes()) or {},
        analysis_profile_fingerprint="batch-test-profile",
    )
    assert len(receipts) == len(videos)
    assert analyzed == [f"video-{index}".encode() for index in range(len(videos))]
    assert all(
        json.loads(receipt.read_text(encoding="utf-8"))["status"] == "succeeded"
        for receipt in receipts
    )


def test_event_job_cap_is_applied_after_existing_queue_identities(
    tmp_path: Path,
) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    videos = []
    for index in range(hook.MAXIMUM_JOBS_PER_EVENT + 3):
        video = project_root / f"candidate-{index}.mp4"
        video.write_bytes(f"video-{index}".encode())
        videos.append(video)
    event = {
        **_generated_event(videos[0]),
        "tool_response": {
            "status": "succeeded",
            "artifacts": [{"video_path": str(video)} for video in videos],
        },
    }
    state_root = tmp_path / "state"
    first_spawns: list[Path] = []
    second_spawns: list[Path] = []

    first = hook.process_post_tool_event(
        event,
        project_root=project_root,
        state_root=state_root,
        spawn_worker=first_spawns.append,
    )
    second = hook.process_post_tool_event(
        event,
        project_root=project_root,
        state_root=state_root,
        spawn_worker=second_spawns.append,
    )

    assert "3 additional generated MP4 file(s) were deferred" in first["systemMessage"]
    assert second["continue"] is True
    assert len(first_spawns) == 1
    assert len(second_spawns) == 1
    assert len(list((state_root / "queue").glob("*.json"))) == len(videos)


def test_spawn_failure_does_not_leave_an_unretryable_job(tmp_path: Path) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    video = project_root / "candidate.mp4"
    video.write_bytes(b"video")
    state_root = tmp_path / "state"

    def fail_to_spawn(_job: Path) -> None:
        raise OSError("worker unavailable")

    failed = hook.process_post_tool_event(
        _generated_event(video),
        project_root=project_root,
        state_root=state_root,
        spawn_worker=fail_to_spawn,
    )
    spawned: list[Path] = []
    retried = hook.process_post_tool_event(
        _generated_event(video),
        project_root=project_root,
        state_root=state_root,
        spawn_worker=spawned.append,
    )

    assert failed == {"continue": True}
    assert retried["continue"] is True
    assert len(spawned) == 1


def test_worker_uses_content_identity_and_writes_advisory_result(
    tmp_path: Path,
) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    video = project_root / "candidate.mp4"
    video.write_bytes(b"same-content")
    state_root = tmp_path / "state"
    jobs: list[Path] = []
    hook.process_post_tool_event(
        _generated_event(video),
        project_root=project_root,
        state_root=state_root,
        spawn_worker=jobs.append,
    )
    calls: list[tuple[str, bytes, int]] = []

    def analyze_snapshot(path: str) -> dict:
        snapshot = Path(path)
        calls.append((path, snapshot.read_bytes(), stat.S_IMODE(snapshot.stat().st_mode)))
        return {
            "video_path": path,
            "analysis_summary": {"scene_count": 1},
        }

    first = hook.process_job(
        jobs[0],
        analyze=analyze_snapshot,
    )
    second = hook.process_job(
        jobs[0],
        analyze=lambda path: calls.append(path) or {"unexpected": True},
    )

    assert first == second
    receipt = json.loads(first.read_text(encoding="utf-8"))
    assert receipt["schema"] == "ai-video-analysis-hook-result/1"
    assert receipt["advisory_only"] is True
    assert receipt["production_verdict"] is None
    assert receipt["analysis"]["analysis_summary"]["scene_count"] == 1
    assert receipt["analysis"]["video_path"] == str(video.resolve())
    assert receipt["source_sha256"] == hook._sha256_file(video)
    assert len(calls) == 1
    snapshot_path, snapshot_bytes, snapshot_mode = calls[0]
    assert snapshot_path != str(video.resolve())
    assert snapshot_bytes == b"same-content"
    assert snapshot_mode == 0o400
    assert not Path(snapshot_path).exists()
    assert stat.S_IMODE(first.stat().st_mode) == 0o600


def test_worker_result_identity_includes_the_automatic_analysis_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    video = project_root / "candidate.mp4"
    video.write_bytes(b"same-content")
    jobs: list[Path] = []
    hook.process_post_tool_event(
        _generated_event(video),
        project_root=project_root,
        state_root=tmp_path / "state",
        spawn_worker=jobs.append,
    )
    calls: list[str] = []

    first = hook.process_job(
        jobs[0],
        analyze=lambda path: calls.append(path) or {"profile": "first"},
    )
    monkeypatch.setenv("VIDEO_MCP_FRAME_WIDTH", "320")
    second = hook.process_job(
        jobs[0],
        analyze=lambda path: calls.append(path) or {"profile": "second"},
    )

    assert first != second
    assert len(calls) == 2
    first_receipt = json.loads(first.read_text(encoding="utf-8"))
    second_receipt = json.loads(second.read_text(encoding="utf-8"))
    assert (
        first_receipt["analysis_profile_fingerprint"]
        != second_receipt["analysis_profile_fingerprint"]
    )


def test_worker_fails_closed_when_queued_file_identity_changes(tmp_path: Path) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    video = project_root / "candidate.mp4"
    video.write_bytes(b"before")
    state_root = tmp_path / "state"
    jobs: list[Path] = []
    hook.process_post_tool_event(
        _generated_event(video),
        project_root=project_root,
        state_root=state_root,
        spawn_worker=jobs.append,
    )
    video.write_bytes(b"after-change")

    result = hook.process_job(jobs[0], analyze=lambda _path: {"must": "not run"})

    receipt = json.loads(result.read_text(encoding="utf-8"))
    assert receipt["status"] == "stale_source"
    assert receipt["analysis"] is None
    assert not list((state_root / "results").glob("*.json"))


def test_worker_rehashes_after_analysis_before_writing_success(tmp_path: Path) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    video = project_root / "candidate.mp4"
    video.write_bytes(b"before")
    state_root = tmp_path / "state"
    jobs: list[Path] = []
    hook.process_post_tool_event(
        _generated_event(video),
        project_root=project_root,
        state_root=state_root,
        spawn_worker=jobs.append,
    )
    queued_stat = video.stat()

    def replace_bytes_and_restore_metadata(_path: str) -> dict:
        video.write_bytes(b"after!")
        os.utime(video, ns=(queued_stat.st_atime_ns, queued_stat.st_mtime_ns))
        return {"analysis_summary": {"scene_count": 1}}

    result = hook.process_job(jobs[0], analyze=replace_bytes_and_restore_metadata)

    receipt = json.loads(result.read_text(encoding="utf-8"))
    assert receipt["status"] == "stale_source"
    assert receipt["analysis"] is None
    assert not list((state_root / "results").glob("*.json"))


def test_worker_analysis_is_bound_to_an_immutable_snapshot_when_source_is_restored(
    tmp_path: Path,
) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    video = project_root / "candidate.mp4"
    video.write_bytes(b"before")
    state_root = tmp_path / "state"
    jobs: list[Path] = []
    hook.process_post_tool_event(
        _generated_event(video),
        project_root=project_root,
        state_root=state_root,
        spawn_worker=jobs.append,
    )
    queued_stat = video.stat()
    analyzed_bytes: list[bytes] = []

    def mutate_source_then_restore(analyze_path: str) -> dict:
        video.write_bytes(b"after!")
        os.utime(video, ns=(queued_stat.st_atime_ns, queued_stat.st_mtime_ns))
        analyzed_bytes.append(Path(analyze_path).read_bytes())
        video.write_bytes(b"before")
        os.utime(video, ns=(queued_stat.st_atime_ns, queued_stat.st_mtime_ns))
        return {"video_path": analyze_path}

    result = hook.process_job(jobs[0], analyze=mutate_source_then_restore)

    receipt = json.loads(result.read_text(encoding="utf-8"))
    assert receipt["status"] == "succeeded"
    assert receipt["source_sha256"] == hook._sha256_file(video)
    assert receipt["analysis"]["video_path"] == str(video.resolve())
    assert analyzed_bytes == [b"before"]
    assert not list((state_root / "snapshots").glob("*.mp4"))


def test_background_analysis_is_globally_serialized_per_repository(
    tmp_path: Path,
) -> None:
    hook = _analysis_hook()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    state_root = tmp_path / "state"
    jobs: list[Path] = []
    for name in ("one.mp4", "two.mp4"):
        video = project_root / name
        video.write_bytes(name.encode())
        hook.process_post_tool_event(
            _generated_event(video),
            project_root=project_root,
            state_root=state_root,
            spawn_worker=jobs.append,
        )
    first_started = threading.Event()
    release_first = threading.Event()
    second_started = threading.Event()

    def first_analyze(_path: str) -> dict:
        first_started.set()
        assert release_first.wait(1)
        return {"analysis_summary": {"scene_count": 1}}

    def second_analyze(_path: str) -> dict:
        second_started.set()
        return {"analysis_summary": {"scene_count": 1}}

    first = threading.Thread(
        target=hook.process_job,
        args=(jobs[0],),
        kwargs={"analyze": first_analyze},
    )
    second = threading.Thread(
        target=hook.process_job,
        args=(jobs[1],),
        kwargs={"analyze": second_analyze},
    )
    first.start()
    assert first_started.wait(1)
    second.start()

    assert not second_started.wait(0.05)
    release_first.set()
    first.join(1)
    second.join(1)
    assert not first.is_alive()
    assert not second.is_alive()
    assert second_started.is_set()
    assert stat.S_IMODE((state_root / "worker.lock").stat().st_mode) == 0o600


def test_worker_rejects_a_job_without_the_hook_schema(tmp_path: Path) -> None:
    hook = _analysis_hook()
    queue_root = tmp_path / "state" / "queue"
    queue_root.mkdir(parents=True)
    job = queue_root / "invalid.json"
    job.write_text(json.dumps({"schema": "unexpected"}), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid analysis hook job"):
        hook.process_job(job)


def test_project_hook_registers_generated_video_analysis_after_tool_use() -> None:
    config = json.loads(HOOK_CONFIG_PATH.read_text(encoding="utf-8"))
    registrations = config["hooks"]["PostToolUse"]
    analysis_registrations = [
        registration
        for registration in registrations
        if any(
            "ai_video_mcp.analysis_hook post-tool-use" in hook["command"]
            for hook in registration["hooks"]
        )
    ]

    assert len(analysis_registrations) == 1
    registration = analysis_registrations[0]
    assert registration["matcher"] == "^(Bash|.*[Vv]ideo.*)$"
    hook_config = registration["hooks"][0]
    assert hook_config["timeout"] == 2
    assert "PYTHONPATH=" in hook_config["command"]


def test_claude_project_hook_reuses_the_local_analysis_queue() -> None:
    config = json.loads(CLAUDE_HOOK_CONFIG_PATH.read_text(encoding="utf-8"))
    registrations = config["hooks"]["PostToolUse"]

    assert len(registrations) == 1
    registration = registrations[0]
    assert registration["matcher"] == "^(Bash|.*[Vv]ideo.*)$"
    hook_config = registration["hooks"][0]
    assert hook_config["timeout"] == 2
    assert "ai_video_mcp.analysis_hook post-tool-use" in hook_config["command"]
    assert "API_KEY" not in hook_config["command"]
    assert "base_url" not in hook_config["command"]
    assert "model" not in hook_config["command"]


def test_claude_mcp_uses_the_same_isolated_video_analysis_runtime() -> None:
    config = json.loads(CLAUDE_MCP_CONFIG_PATH.read_text(encoding="utf-8"))
    server = config["mcpServers"]["video-analysis"]

    assert server["command"] == (
        "/home/reggie/.local/share/ai-video/video-analysis-mcp/bin/python"
    )
    assert server["args"] == ["-m", "ai_video_mcp"]
    assert server["env"] == {
        "PYTHONPATH": "/home/reggie/vscode_folder/AI-VIDEO/src"
    }
