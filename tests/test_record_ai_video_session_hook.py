from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest


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


def _post_patch(hook, repo: Path, state_root: Path, *paths: str) -> None:
    patch_lines = ["*** Begin Patch"]
    for path in paths:
        patch_lines.extend((f"*** Update File: {path}", "@@"))
    patch_lines.append("*** End Patch")
    result = hook.process_event(
        _event(
            "PostToolUse",
            repo,
            tool_name="apply_patch",
            tool_input={"patch": "\n".join(patch_lines)},
        ),
        project_root=repo,
        state_root=state_root,
    )
    assert result == {"continue": True}


def _capture_request_id(message: str) -> str:
    marker = "capture_request_id="
    return message.split(marker, 1)[1].split(")", 1)[0]


def test_hook_files_register_session_lifecycle_and_apply_patch_tracking() -> None:
    assert HOOK_PATH.is_file()
    config = json.loads(HOOK_CONFIG_PATH.read_text(encoding="utf-8"))

    assert set(config["hooks"]) == {
        "SessionStart",
        "PostToolUse",
        "PreCompact",
        "Stop",
    }
    assert config["hooks"]["PostToolUse"][0]["matcher"] == "^(apply_patch|Bash)$"
    commands = {
        hook["command"]
        for registrations in config["hooks"].values()
        for registration in registrations
        for hook in registration["hooks"]
        if "session_record_hook.py" in hook["command"]
    }
    assert len(commands) == 1
    command = commands.pop()
    assert command.startswith('python3 "')
    assert command.endswith(
        '/.agents/skills/record-ai-video-session/scripts/session_record_hook.py"'
    )


def test_session_start_initializes_an_acked_empty_scope_without_prompting(
    tmp_path: Path,
) -> None:
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
    assert state["schema"] == "ai-video-session-record-hook/2"
    assert state["status"] == "ACKED"
    assert state["owned_paths"] == []
    assert state["pending_request_id"] is None


def test_stop_requests_record_once_after_repository_change(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("changed\n", encoding="utf-8")
    _post_patch(hook, repo, state_root, "tracked.txt")

    first = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    recursive = hook.process_event(
        _event("Stop", repo, stop_hook_active=True),
        project_root=repo,
        state_root=state_root,
    )
    request_id = _capture_request_id(str(first["reason"]))
    assert hook.acknowledge_request(
        request_id,
        outcome="no_record",
        project_root=repo,
        state_root=state_root,
    )
    repeated = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert first["decision"] == "block"
    assert "expected checkpoint continuation, not a hook execution failure" in first[
        "reason"
    ]
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
    _post_patch(hook, repo, state_root, "tracked.txt")

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
    _post_patch(hook, repo, state_root, "tracked.txt")

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
    _post_patch(hook, repo, state_root, "untracked.txt")

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
    _post_patch(hook, repo, state_root, "tracked.txt")
    first = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("second change\n", encoding="utf-8")
    _post_patch(hook, repo, state_root, "tracked.txt")

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
    _post_patch(hook, repo, state_root, "tracked.txt")

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
    _post_patch(hook, repo, state_root, "tracked.txt")

    precompact = hook.process_event(
        _event("PreCompact", repo), project_root=repo, state_root=state_root
    )
    stop = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert "$record-ai-video-session" in precompact["systemMessage"]
    assert stop["decision"] == "block"
    assert _capture_request_id(str(precompact["systemMessage"])) == (
        _capture_request_id(str(stop["reason"]))
    )


def test_missing_baseline_dirty_stop_without_session_owned_paths_continues(
    tmp_path: Path,
) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    tracked.write_text("changed\n", encoding="utf-8")

    result = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert result == {"continue": True}


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


def test_read_only_session_ignores_unrelated_head_index_and_untracked_changes(
    tmp_path: Path,
) -> None:
    hook = _load_hook_module()
    repo, _ = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    unrelated = repo / "unrelated.txt"
    unrelated.write_text("other agent\n", encoding="utf-8")
    _git(repo, "add", "unrelated.txt")
    _git(repo, "commit", "-qm", "unrelated work")
    (repo / "other-untracked.txt").write_text("untracked\n", encoding="utf-8")

    result = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert result == {"continue": True}


def test_exact_git_add_attributes_bounded_writer_paths_to_the_session(
    tmp_path: Path,
) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("bounded writer\n", encoding="utf-8")
    unrelated = repo / "unrelated.txt"
    unrelated.write_text("other agent\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")

    tracked_event = hook.process_event(
        _event(
            "PostToolUse",
            repo,
            tool_name="Bash",
            tool_input={"command": "git add tracked.txt"},
        ),
        project_root=repo,
        state_root=state_root,
    )
    requested = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert tracked_event == {"continue": True}
    assert requested["decision"] == "block"
    state = json.loads(next(state_root.glob("*.json")).read_text(encoding="utf-8"))
    assert state["owned_paths"] == ["tracked.txt"]


def test_exact_git_add_paths_are_resolved_from_the_event_cwd(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, _ = _repository(tmp_path)
    state_root = tmp_path / "state"
    nested = repo / "nested"
    nested.mkdir()
    nested_file = nested / "owned.txt"
    nested_file.write_text("owned\n", encoding="utf-8")
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    _git(repo, "add", "nested/owned.txt")

    hook.process_event(
        _event(
            "PostToolUse",
            nested,
            tool_name="Bash",
            tool_input={"command": "git add owned.txt"},
        ),
        project_root=repo,
        state_root=state_root,
    )
    state = json.loads(next(state_root.glob("*.json")).read_text(encoding="utf-8"))

    assert state["owned_paths"] == ["nested/owned.txt"]


@pytest.mark.parametrize(
    "command",
    [
        "git add .",
        "git add -A",
        "git add '*.txt'",
        "git add tracked.txt && git add unrelated.txt",
    ],
)
def test_broad_chained_or_glob_git_add_does_not_claim_session_ownership(
    tmp_path: Path, command: str
) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("changed\n", encoding="utf-8")

    hook.process_event(
        _event(
            "PostToolUse",
            repo,
            tool_name="Bash",
            tool_input={"command": command},
        ),
        project_root=repo,
        state_root=state_root,
    )
    result = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert result == {"continue": True}


def test_legacy_global_fingerprint_state_resets_without_phantom_request(
    tmp_path: Path,
) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    state_root.mkdir()
    state_path = hook._state_path(state_root, "session-record-hook-test")
    state_path.write_text(
        json.dumps(
            {
                "schema": "ai-video-session-record-hook/1",
                "baseline": {"fingerprint": "old"},
                "last_handled_fingerprint": "old",
                "last_requested_fingerprint": "other-agent",
            }
        ),
        encoding="utf-8",
    )
    tracked.write_text("unattributed existing change\n", encoding="utf-8")

    stop = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    migrated = json.loads(state_path.read_text(encoding="utf-8"))

    assert stop == {"continue": True}
    assert migrated["schema"] == "ai-video-session-record-hook/2"
    assert migrated["status"] == "ACKED"
    assert migrated["owned_paths"] == []


@pytest.mark.parametrize("outcome", ["recorded", "no_record"])
def test_record_evaluation_outcomes_acknowledge_the_current_checkpoint(
    tmp_path: Path, outcome: str
) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("session-owned\n", encoding="utf-8")
    _post_patch(hook, repo, state_root, "tracked.txt")
    requested = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    request_id = _capture_request_id(str(requested["reason"]))

    acknowledged = hook.acknowledge_request(
        request_id,
        outcome=outcome,
        project_root=repo,
        state_root=state_root,
    )
    repeated = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert acknowledged is True
    assert repeated == {"continue": True}


def test_unrelated_changes_do_not_reopen_an_acknowledged_checkpoint(
    tmp_path: Path,
) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("session-owned\n", encoding="utf-8")
    _post_patch(hook, repo, state_root, "tracked.txt")
    requested = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    request_id = _capture_request_id(str(requested["reason"]))
    assert hook.acknowledge_request(
        request_id,
        outcome="no_record",
        project_root=repo,
        state_root=state_root,
    )
    unrelated = repo / "unrelated.txt"
    unrelated.write_text("other agent\n", encoding="utf-8")
    _git(repo, "add", "unrelated.txt")
    _git(repo, "commit", "-qm", "unrelated work")
    (repo / "other-untracked.txt").write_text("untracked\n", encoding="utf-8")

    result = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert result == {"continue": True}


def test_new_session_owned_edit_reopens_an_acknowledged_checkpoint(
    tmp_path: Path,
) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("first\n", encoding="utf-8")
    _post_patch(hook, repo, state_root, "tracked.txt")
    first = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    first_request_id = _capture_request_id(str(first["reason"]))
    assert hook.acknowledge_request(
        first_request_id,
        outcome="recorded",
        project_root=repo,
        state_root=state_root,
    )
    tracked.write_text("second\n", encoding="utf-8")
    _post_patch(hook, repo, state_root, "tracked.txt")

    second = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert second["decision"] == "block"
    assert _capture_request_id(str(second["reason"])) != first_request_id


def test_stale_request_cannot_acknowledge_new_bytes_on_an_owned_path(
    tmp_path: Path,
) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("first\n", encoding="utf-8")
    _post_patch(hook, repo, state_root, "tracked.txt")
    first = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    first_request_id = _capture_request_id(str(first["reason"]))
    tracked.write_text("second without attribution event\n", encoding="utf-8")

    acknowledged = hook.acknowledge_request(
        first_request_id,
        outcome="recorded",
        project_root=repo,
        state_root=state_root,
    )
    second = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert acknowledged is False
    assert second["decision"] == "block"
    assert _capture_request_id(str(second["reason"])) != first_request_id


def test_recursive_stop_does_not_acknowledge_pending_checkpoint(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("changed\n", encoding="utf-8")
    _post_patch(hook, repo, state_root, "tracked.txt")
    first = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    recursive = hook.process_event(
        _event("Stop", repo, stop_hook_active=True),
        project_root=repo,
        state_root=state_root,
    )
    later = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert first["decision"] == "block"
    assert recursive == {"continue": True}
    assert later["decision"] == "block"
    assert later["reason"] == first["reason"]


def test_precompact_strong_reminder_and_stop_share_one_checkpoint_id(
    tmp_path: Path,
) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    tracked.write_text("changed\n", encoding="utf-8")
    _post_patch(hook, repo, state_root, "tracked.txt")

    precompact = hook.process_event(
        _event("PreCompact", repo), project_root=repo, state_root=state_root
    )
    repeated = hook.process_event(
        _event("PreCompact", repo), project_root=repo, state_root=state_root
    )
    stop = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert precompact["continue"] is True
    assert "STRONG CHECKPOINT REMINDER" in str(precompact["systemMessage"])
    assert repeated == {"continue": True}
    assert stop["decision"] == "block"
    assert _capture_request_id(str(precompact["systemMessage"])) == (
        _capture_request_id(str(stop["reason"]))
    )


def test_session_record_artifact_does_not_open_its_own_checkpoint(
    tmp_path: Path,
) -> None:
    hook = _load_hook_module()
    repo, _ = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    record_path = repo / "docs" / "record_for_agent" / "checkpoint.md"
    record_path.parent.mkdir(parents=True)
    record_path.write_text("record\n", encoding="utf-8")
    _post_patch(
        hook,
        repo,
        state_root,
        "docs/record_for_agent/checkpoint.md",
    )

    result = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert result == {"continue": True}


def test_failed_apply_patch_does_not_claim_session_ownership(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )

    hook.process_event(
        _event(
            "PostToolUse",
            repo,
            tool_name="apply_patch",
            tool_input={
                "patch": "*** Begin Patch\n*** Update File: tracked.txt\n*** End Patch"
            },
            tool_response={"isError": True, "output": "patch did not apply"},
        ),
        project_root=repo,
        state_root=state_root,
    )
    tracked.write_text("other agent\n", encoding="utf-8")
    result = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )

    assert result == {"continue": True}


def test_concurrent_post_tool_callbacks_preserve_both_owned_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hook = _load_hook_module()
    repo, _ = _repository(tmp_path)
    state_root = tmp_path / "state"
    for name in ("one.txt", "two.txt"):
        (repo / name).write_text(f"{name}\n", encoding="utf-8")
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    original_load_state = hook._load_state
    simultaneous_load = threading.Barrier(2)

    def load_state_together(path: Path, project_root: Path):
        state = original_load_state(path, project_root)
        if state is not None and state.get("owned_paths") == []:
            try:
                simultaneous_load.wait(timeout=0.2)
            except threading.BrokenBarrierError:
                pass
        return state

    monkeypatch.setattr(hook, "_load_state", load_state_together)
    errors: list[BaseException] = []

    def track(path: str) -> None:
        try:
            _post_patch(hook, repo, state_root, path)
        except BaseException as error:  # noqa: BLE001 - preserve thread failure
            errors.append(error)

    first = threading.Thread(target=track, args=("one.txt",))
    second = threading.Thread(target=track, args=("two.txt",))
    first.start()
    second.start()
    first.join()
    second.join()
    state = json.loads(next(state_root.glob("*.json")).read_text(encoding="utf-8"))

    assert errors == []
    assert state["owned_paths"] == ["one.txt", "two.txt"]


def test_owned_path_overflow_reopens_via_bounded_event_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hook = _load_hook_module()
    monkeypatch.setattr(hook, "MAXIMUM_OWNED_PATHS", 1)
    repo, _ = _repository(tmp_path)
    state_root = tmp_path / "state"
    first_path = repo / "one.txt"
    overflow_path = repo / "two.txt"
    first_path.write_text("one\n", encoding="utf-8")
    overflow_path.write_text("two\n", encoding="utf-8")
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )
    _post_patch(hook, repo, state_root, "one.txt", "two.txt")
    first = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    first_request_id = _capture_request_id(str(first["reason"]))
    assert hook.acknowledge_request(
        first_request_id,
        outcome="no_record",
        project_root=repo,
        state_root=state_root,
    )
    overflow_path.write_text("two changed\n", encoding="utf-8")
    _post_patch(hook, repo, state_root, "two.txt")

    second = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    state = json.loads(next(state_root.glob("*.json")).read_text(encoding="utf-8"))

    assert state["owned_paths"] == ["one.txt"]
    assert state["tracking_overflow"] is True
    assert second["decision"] == "block"
    assert _capture_request_id(str(second["reason"])) != first_request_id


def test_long_owned_path_list_overflows_before_state_size_limit(
    tmp_path: Path,
) -> None:
    hook = _load_hook_module()
    repo, _ = _repository(tmp_path)
    state_root = tmp_path / "state"
    paths = [f"{index:03d}-{'x' * 150}.txt" for index in range(100)]
    for path in paths:
        (repo / path).write_text(f"{path}\n", encoding="utf-8")
    hook.process_event(
        _event("SessionStart", repo), project_root=repo, state_root=state_root
    )

    _post_patch(hook, repo, state_root, *paths)
    state_path = next(state_root.glob("*.json"))
    state = json.loads(state_path.read_text(encoding="utf-8"))

    assert state_path.stat().st_size <= hook.MAXIMUM_STATE_BYTES
    assert state["tracking_overflow"] is True
    assert len(state["owned_paths"]) < len(paths)


def test_acknowledge_rejects_unknown_capture_request_id(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, _ = _repository(tmp_path)

    assert hook.acknowledge_request(
        "ai-video-record-0000000000000000",
        outcome="no_record",
        project_root=repo,
        state_root=tmp_path / "state",
    ) is False
