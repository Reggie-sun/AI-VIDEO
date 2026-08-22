from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "record-ai-video-session"
    / "scripts"
    / "session_record_hook.py"
)
HOOK_CONFIG_PATH = ROOT / ".codex" / "hooks.json"


def _load_hook_module():
    spec = importlib.util.spec_from_file_location("ai_video_session_record_hook", HOOK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "hook@example.invalid")
    _git(repo, "config", "user.name", "Hook Test")
    tracked = repo / "tracked.txt"
    tracked.write_text("baseline\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-qm", "baseline")
    return repo, tracked


def _event(name: str, repo: Path, **updates: object) -> dict[str, object]:
    event: dict[str, object] = {
        "hook_event_name": name,
        "session_id": "session-record-hook-test",
        "turn_id": "turn-1",
        "cwd": str(repo),
    }
    event.update(updates)
    return event


def test_hook_files_are_registered_without_post_tool_use() -> None:
    assert HOOK_PATH.is_file()
    config = json.loads(HOOK_CONFIG_PATH.read_text(encoding="utf-8"))

    assert set(config["hooks"]) == {"SessionStart", "PreCompact", "Stop"}
    assert "PostToolUse" not in config["hooks"]
    commands = {
        hook["command"]
        for registrations in config["hooks"].values()
        for registration in registrations
        for hook in registration["hooks"]
    }
    assert commands == {
        'python3 "$(git rev-parse --show-toplevel)/.agents/skills/'
        'record-ai-video-session/scripts/session_record_hook.py"'
    }


def test_session_start_baselines_clean_repository_without_prompting(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, _ = _repository(tmp_path)
    state_root = tmp_path / "state"

    result = hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )

    assert result == {"continue": True}
    state_files = list(state_root.glob("*.json"))
    assert len(state_files) == 1
    state = json.loads(state_files[0].read_text(encoding="utf-8"))
    assert state["baseline"]["dirty"] is False
    assert state["last_handled_fingerprint"] == state["baseline"]["fingerprint"]


def test_stop_requests_record_once_after_repository_change(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("changed\n", encoding="utf-8")

    first = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    recursive = hook.process_event(
        _event("Stop", repo, stop_hook_active=True),
        project_root=repo,
        state_root=state_root,
    )
    repeated = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert first["decision"] == "block"
    assert "$record-ai-video-session" in first["reason"]
    assert "capture_request_id=ai-video-record-" in first["reason"]
    assert recursive == {"continue": True}
    assert repeated == {"continue": True}


def test_stop_detects_same_dirty_path_content_change(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    tracked.write_text("dirty-before-session\n", encoding="utf-8")
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("dirty-during-session\n", encoding="utf-8")

    result = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert result["decision"] == "block"


def test_stop_detects_same_staged_path_content_change(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    tracked.write_text("staged-before-session\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("staged-during-session\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")

    result = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert result["decision"] == "block"


def test_stop_detects_same_untracked_path_content_change(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, _ = _repository(tmp_path)
    state_root = tmp_path / "state"
    untracked = repo / "untracked.txt"
    untracked.write_text("untracked-before-session\n", encoding="utf-8")
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    untracked.write_text("untracked-during-session\n", encoding="utf-8")

    result = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert result["decision"] == "block"


def test_stop_detects_new_content_after_prior_request(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("first change\n", encoding="utf-8")
    first = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("second change\n", encoding="utf-8")

    second = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert first["decision"] == "block"
    assert second["decision"] == "block"
    assert first["reason"] != second["reason"]


def test_stop_without_repository_change_does_not_request_record(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, _ = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )

    result = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert result == {"continue": True}


def test_precompact_adds_context_only_for_unhandled_change(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    unchanged = hook.process_event(
        _event("PreCompact", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("changed\n", encoding="utf-8")

    changed = hook.process_event(
        _event("PreCompact", repo), project_root=repo, state_root=state_root
    )
    repeated = hook.process_event(
        _event("PreCompact", repo), project_root=repo, state_root=state_root
    )

    assert unchanged == {"continue": True}
    assert changed["continue"] is True
    assert "$record-ai-video-session" in changed["systemMessage"]
    assert repeated == {"continue": True}


def test_precompact_and_stop_share_one_request_per_fingerprint(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("changed\n", encoding="utf-8")

    precompact = hook.process_event(
        _event("PreCompact", repo), project_root=repo, state_root=state_root
    )
    stop = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert "$record-ai-video-session" in precompact["systemMessage"]
    assert stop == {"continue": True}


def test_missing_baseline_dirty_stop_still_requests_record(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    tracked.write_text("changed\n", encoding="utf-8")

    result = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert result["decision"] == "block"


def test_event_outside_project_root_fails_open(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, _ = _repository(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()

    result = hook.process_event(
        _event("Stop", outside),
        project_root=repo,
        state_root=tmp_path / "state",
    )

    assert result == {"continue": True}
    assert not (tmp_path / "state").exists()


def test_default_state_root_is_git_internal(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, _ = _repository(tmp_path)

    state_root = hook.default_state_root(repo)

    assert state_root == repo / ".git" / "ai-video-session-record-hook"
