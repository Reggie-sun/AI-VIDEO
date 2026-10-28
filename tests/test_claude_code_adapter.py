from __future__ import annotations

import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = ROOT / "CLAUDE.md"
CLAUDE_SETTINGS = ROOT / ".claude" / "settings.json"
REVIEWER_AGENT = ROOT / ".claude" / "agents" / "harness-reviewer.md"
CLAUDE_SKILLS_DIR = ROOT / ".claude" / "skills"
CANONICAL_SKILLS_DIR = ROOT / ".agents" / "skills"
CLAUDE_MCP_CONFIG = ROOT / ".mcp.json"
CODEX_CONFIG = ROOT / ".codex" / "config.toml"
HOOK_SCRIPT = (
    CANONICAL_SKILLS_DIR
    / "record-ai-video-session"
    / "scripts"
    / "session_record_hook.py"
)

EXPECTED_PROJECT_SKILLS = {
    "open-video",
    "h3-video",
    "seedance-authoring",
    "ecommerce-ad-workflow",
    "retrieve-ai-video-memory",
    "record-ai-video-session",
    "distill-ai-video-learning",
}
WRITE_TOOL_NAMES = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def test_claude_md_is_thin_adapter_importing_agents_md() -> None:
    text = CLAUDE_MD.read_text(encoding="utf-8")
    assert "@AGENTS.md" in text
    assert (ROOT / "AGENTS.md").is_file()
    assert len(text.splitlines()) < 60
    # 漂移防线：薄 adapter 不得复制 canonical 章节正文标题
    assert "## Product Invariants" not in text
    assert "## Canonical Ownership" not in text
    assert "## Verification Contract" not in text


def test_claude_settings_wire_session_record_hooks_on_shared_script() -> None:
    settings = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
    hooks = settings["hooks"]
    assert set(hooks) >= {"SessionStart", "PostToolUse", "PreCompact", "Stop"}

    def session_hook_commands() -> list[str]:
        commands: list[str] = []
        for registrations in hooks.values():
            for registration in registrations:
                for hook in registration["hooks"]:
                    if "session_record_hook.py" in hook["command"]:
                        commands.append(hook["command"])
        return commands

    commands = session_hook_commands()
    assert len(commands) == 4  # SessionStart/PostToolUse/PreCompact/Stop 各一条
    assert len(set(commands)) == 1  # 同一脚本同一命令
    # settings.json 记录的是宿主绝对路径；断言仓库相对后缀以便在
    # detached harness worktree 中同样成立。
    assert commands[0].endswith(
        "/.agents/skills/record-ai-video-session/scripts/session_record_hook.py\""
    )

    post_tool = hooks["PostToolUse"]
    session_registration = next(
        registration
        for registration in post_tool
        if any(
            "session_record_hook.py" in hook["command"]
            for hook in registration["hooks"]
        )
    )
    for tool_name in WRITE_TOOL_NAMES:
        assert tool_name in session_registration["matcher"]
    # 既有 video-analysis hook 仍然保留
    assert any(
        "ai_video_mcp.analysis_hook" in hook["command"]
        for registration in post_tool
        for hook in registration["hooks"]
    )


def test_hook_script_recognizes_claude_write_tools() -> None:
    source = HOOK_SCRIPT.read_text(encoding="utf-8")
    assert "CLAUDE_WRITE_TOOL_PATH_KEYS" in source
    for tool_name in WRITE_TOOL_NAMES:
        assert f'"{tool_name}"' in source


def test_reviewer_agent_exists_and_is_read_only() -> None:
    text = REVIEWER_AGENT.read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)[1]
    assert "name: harness-reviewer" in frontmatter
    tools_line = next(
        line for line in frontmatter.splitlines() if line.startswith("tools:")
    )
    for write_tool in WRITE_TOOL_NAMES:
        assert write_tool not in tools_line
    assert "Read" in tools_line and "Grep" in tools_line


def test_project_skills_visible_through_claude_skills_junction() -> None:
    # 隐藏目录（如 runtime 在 cwd 下生成的 .omc/ 状态）不是 skill 入口。
    visible = {
        entry.name
        for entry in CLAUDE_SKILLS_DIR.iterdir()
        if not entry.name.startswith(".")
    }
    canonical = {
        entry.name
        for entry in CANONICAL_SKILLS_DIR.iterdir()
        if (entry / "SKILL.md").is_file()
    }
    assert EXPECTED_PROJECT_SKILLS <= canonical
    # 双 runtime 对齐：每个 canonical skill 都经 symlink 对 Claude 可见，
    # .claude/skills 不得保留指向已删除 skill 的悬空入口。
    assert visible == canonical
    for name in sorted(visible):
        entry = CLAUDE_SKILLS_DIR / name
        assert entry.is_symlink(), f"{name} must be a symlink, not a second copy"
        skill_md = (CLAUDE_SKILLS_DIR / name / "SKILL.md").resolve()
        assert skill_md.is_file()
        assert CANONICAL_SKILLS_DIR in skill_md.parents  # 实体唯一，无第二份正文
        head = skill_md.read_text(encoding="utf-8")[:2000]
        assert "description:" in head


# Codex `enabled_tools` 白名单在 Claude 侧以 settings deny 表达；deny 需枚举，
# 故绑定 pinned 版本的完整工具清单，升级版本时必须重新盘点。
PINNED_MCP_TOOL_INVENTORIES = {
    "blender": (
        "blender-mcp==1.8.7",
        {
            "disable_telemetry", "download_polyhaven_asset",
            "download_sketchfab_model", "execute_blender_code",
            "generate_hunyuan3d_model", "generate_hyper3d_model_via_images",
            "generate_hyper3d_model_via_text", "get_addon_status",
            "get_hunyuan3d_status", "get_hyper3d_status", "get_object_info",
            "get_polyhaven_categories", "get_polyhaven_status", "get_scene_info",
            "get_sketchfab_model_preview", "get_sketchfab_status",
            "get_viewport_screenshot", "import_generated_asset",
            "import_generated_asset_hunyuan", "poll_hunyuan_job_status",
            "poll_rodin_job_status", "record_trajectory_feedback",
            "search_polyhaven_assets", "search_sketchfab_models", "set_texture",
        },
    ),
}


def _claude_launch(server: dict) -> tuple[str | None, str, list[str]]:
    """Return (cwd, command, args), unwrapping `/usr/bin/env --chdir=<cwd>`."""
    command, args = server["command"], list(server.get("args", []))
    if command == "/usr/bin/env" and args and args[0].startswith("--chdir="):
        return args[0].removeprefix("--chdir="), args[1], args[2:]
    return server.get("cwd"), command, args


def test_claude_mcp_servers_mirror_codex_project_servers() -> None:
    codex = tomllib.loads(CODEX_CONFIG.read_text(encoding="utf-8"))["mcp_servers"]
    claude = json.loads(CLAUDE_MCP_CONFIG.read_text(encoding="utf-8"))["mcpServers"]
    settings = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
    denied = set(settings.get("permissions", {}).get("deny", []))
    repo_root = "/home/reggie/vscode_folder/AI-VIDEO"

    # Agent 切换 runtime 不得丢失 CodeGraph/AOCI/Blender 等项目工具面。
    assert set(codex) <= set(claude)
    for name, expected in codex.items():
        cwd, command, args = _claude_launch(claude[name])
        if Path(expected["command"]).is_absolute():
            assert command == expected["command"], name
        else:  # Codex 依赖 PATH，Claude 侧须钉死同名绝对路径
            assert Path(command).is_absolute(), name
            assert Path(command).name == expected["command"], name
        assert args == expected.get("args", []), name
        assert claude[name].get("env", {}) == expected.get("env", {}), name
        if expected.get("cwd") not in (None, repo_root):
            assert cwd == expected["cwd"], name

        enabled = expected.get("enabled_tools")
        prefix = f"mcp__{name}__"
        server_denied = {rule.removeprefix(prefix) for rule in denied if rule.startswith(prefix)}
        if enabled is None:
            assert not server_denied, name
            continue
        assert name in PINNED_MCP_TOOL_INVENTORIES, f"{name} needs a pinned tool inventory"
        pin, inventory = PINNED_MCP_TOOL_INVENTORIES[name]
        assert pin in args, f"{name} version changed; re-inventory its tools"
        assert set(enabled) <= inventory
        # Claude 可见工具不得超出 Codex 白名单（防止云端生成/下载类工具旁路）。
        assert server_denied == inventory - set(enabled), name


def test_claude_mcp_config_carries_no_inline_secrets() -> None:
    claude = json.loads(CLAUDE_MCP_CONFIG.read_text(encoding="utf-8"))["mcpServers"]
    secret_markers = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")
    for name, server in claude.items():
        assert server["command"].startswith("/"), f"{name} must pin an absolute command"
        for key in server.get("env", {}):
            assert not any(m in key.upper() for m in secret_markers), f"{name}: {key}"
        for arg in server.get("args", []):
            flag = arg.split("=", 1)[0].upper() if arg.startswith("--") else ""
            assert not any(m in flag for m in secret_markers), f"{name}: {arg}"


def test_claude_md_maps_codex_workflow_terms_to_claude_runtime() -> None:
    text = CLAUDE_MD.read_text(encoding="utf-8")
    for term in ("OMX", "OMC", "apply_patch", "$<skill>", "oh-my-claudecode:verifier", "image_gen.imagegen"):
        assert term in text
    # 已退役路由不得在 adapter 中复活。
    for retired in ("Kimi", "SUBAGENTS.md", "superpowers:writing-plans"):
        assert retired not in text
