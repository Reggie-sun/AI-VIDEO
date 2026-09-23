# Claude Code Harness Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Claude Code 成为 AI-VIDEO 现有 Harness 的一等执行 runtime，与 Codex 共用同一 source of truth，只新增薄 adapter。

**Architecture:** 共享契约（AGENTS.md 新增 Agent Workflow Routing 章节 + playbook 操作细节）保持 runtime-agnostic；Claude 侧只新增/修改薄 adapter：CLAUDE.md 瘦身为 `@AGENTS.md` import、`.claude/settings.json` 接线同一 `session_record_hook.py`、`.claude/agents/harness-reviewer.md` 只读 reviewer、`.claude/skills/` symlink 可见性接缝。Hook 脚本做最小扩展以识别 Claude 的 Edit/Write/MultiEdit/NotebookEdit 工具。

**Tech Stack:** Python 3 hook 脚本（零依赖）、Claude Code settings hooks、Claude Code subagents/skills、pytest、agent_harness policy。

**Spec:** `docs/superpowers/specs/2026-09-20-claude-code-harness-adapter.md`

## Scope and Authority

- 只允许修改/创建本 plan 列出的文件；不得触碰 `src/**`、`runs/**`、`.workflow/**`、`.codex/**`、用户既有未提交改动的其他部分。
- policy.yaml 当前有用户未提交改动：只允许追加本 plan 指定的行，不得 revert 或重排既有内容。
- 显式授权的例外（spec Adapter Design 表 policy.yaml 行已记录）：为消除 HEAD 遗留 unmapped paths（`minimax_speech_batch` / `voice_candidate` 共 5 个 b7affb4 引入的已提交文件），Task 6 追加一个最小 `minimax_speech_batch` category + `minimax_speech_batch_tests` check + `full_tests.covers_check_ids` 接线；不补则 policy-audit 对任何 scope 失败，本 plan 无法取得 fresh receipt。
- 不 commit；最终只 `git add <specific-files>` 形成 staged snapshot 供 harness 验证，commit 由用户决定。
- 不触发任何 Provider/network/paid 调用。

## Global Constraints

- 回复与文档叙述用中文；`command`、`path`、frontmatter key、skill 名保持原文。
- Codex 路径零行为变化：`.codex/hooks.json` 不动；`session_record_hook.py` 对 `apply_patch`/`Bash` 的既有行为逐字节保持（既有测试全绿）。
- AGENTS.md 改动为 additive（新增一个章节），不改既有章节文字。
- CLAUDE.md 不得复制规则正文；规则由 `@AGENTS.md` import 承载。
- 新增文件必须在 policy.yaml 获得 category coverage（audit_patterns + control_plane），否则 policy-audit fail safe。
- 每个 task 的 verification 命令必须实际运行并记录结果。

---

### Task 1: Hook 脚本识别 Claude 写工具（TDD）

**Files:**
- Modify: `.agents/skills/record-ai-video-session/scripts/session_record_hook.py`（`_task_owned_paths` 附近，约 line 298-325）
- Test: `tests/test_record_ai_video_session_hook.py`

**Interfaces:**
- Consumes: 既有 `_normalize_owned_path(project_root, raw_path, base_dir=event_cwd)`、`_tool_succeeded(...)`。
- Produces: `CLAUDE_WRITE_TOOL_PATH_KEYS: dict[str, str]` 模块级常量；`_task_owned_paths` 新增对 `Edit`/`Write`/`MultiEdit`/`NotebookEdit` 的支持。后续 Task 6 的 adapter 完整性测试会断言该常量存在。

- [ ] **Step 1: 写失败测试**（追加到 `tests/test_record_ai_video_session_hook.py` 末尾）

```python
def test_claude_edit_tool_marks_file_path_as_session_owned(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    result = hook.process_event(
        _event(
            "PostToolUse",
            repo,
            tool_name="Edit",
            tool_input={"file_path": str(tracked)},
            tool_response={"isError": False},
        ),
        project_root=repo,
        state_root=state_root,
    )
    assert result == {"continue": True}
    stop = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    # owned path 登记后 fingerprint 即偏离空 acked 基线，Stop 必须 block
    # （与既有 _post_patch -> Stop 行为一致）。
    assert stop.get("decision") == "block"


def test_claude_write_and_multiedit_tools_claim_exact_paths(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, _tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    for tool_name, key in (("Write", "file_path"), ("MultiEdit", "file_path"), ("NotebookEdit", "notebook_path")):
        target = repo / f"{tool_name.lower()}-target.txt"
        target.write_text("payload\n", encoding="utf-8")
        result = hook.process_event(
            _event(
                "PostToolUse",
                repo,
                tool_name=tool_name,
                tool_input={key: str(target)},
            ),
            project_root=repo,
            state_root=state_root,
        )
        assert result == {"continue": True}
    stop = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    assert stop.get("decision") == "block"


def test_claude_edit_outside_project_and_failed_tool_are_ignored(tmp_path: Path) -> None:
    hook = _load_hook_module()
    repo, _tracked = _repository(tmp_path)
    state_root = tmp_path / "state"
    outside = tmp_path / "outside.txt"
    outside.write_text("nope\n", encoding="utf-8")
    result = hook.process_event(
        _event(
            "PostToolUse",
            repo,
            tool_name="Edit",
            tool_input={"file_path": str(outside)},
        ),
        project_root=repo,
        state_root=state_root,
    )
    assert result == {"continue": True}
    failed = hook.process_event(
        _event(
            "PostToolUse",
            repo,
            tool_name="Write",
            tool_input={"file_path": str(repo / "failed.txt")},
            tool_response={"isError": True},
        ),
        project_root=repo,
        state_root=state_root,
    )
    assert failed == {"continue": True}
    stop = hook.process_event(
        _event("Stop", repo), project_root=repo, state_root=state_root
    )
    assert stop == {"continue": True}
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest -p no:cacheprovider tests/test_record_ai_video_session_hook.py -q -k claude`
Expected: FAIL（Edit/Write 路径未被跟踪，stop 不 block）

- [ ] **Step 3: 最小实现**（在 `session_record_hook.py` 中）

常量区（`PATCH_MOVE_PATTERN` 之后）新增：

```python
CLAUDE_WRITE_TOOL_PATH_KEYS = {
    "Edit": "file_path",
    "MultiEdit": "file_path",
    "Write": "file_path",
    "NotebookEdit": "notebook_path",
}
```

`_task_owned_paths` 中 `if tool_name != "apply_patch": return []` 替换为：

```python
    if tool_name == "apply_patch":
        patch = _patch_text(tool_input=payload.get("tool_input"))
        ...
```

注意：保持 `apply_patch` 分支原逻辑不动；实际改动是把末尾的 `if tool_name != "apply_patch": return []` 改为先查 `CLAUDE_WRITE_TOOL_PATH_KEYS`：

```python
    path_key = CLAUDE_WRITE_TOOL_PATH_KEYS.get(str(tool_name))
    if path_key is None:
        return []
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, Mapping):
        return []
    relative = _normalize_owned_path(
        project_root, tool_input.get(path_key), base_dir=event_cwd
    )
    return [relative] if relative is not None else []
```

- [ ] **Step 4: 运行确认通过 + 全量回归**

Run: `python -m pytest -p no:cacheprovider tests/test_record_ai_video_session_hook.py -q`
Expected: 全部 PASS（含 3 个新测试与全部既有测试）

---

### Task 2: `.claude/settings.json` 接线 session-record hooks

**Files:**
- Modify: `.claude/settings.json`
- Test: `tests/test_claude_code_adapter.py`（Task 6 创建；本 task 先改配置，测试在 Task 6 补齐并统一运行）

**Interfaces:**
- Consumes: Task 1 的 hook 脚本（路径不变）。
- Produces: 四个 hook 事件接线，供 Claude Code runtime 与 Task 6 的完整性断言使用。

- [ ] **Step 1: 改写 `.claude/settings.json`**（保留既有 video-analysis PostToolUse hook，新增三条 registrations；不写 `statusMessage`——那是 Codex 字段）

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"/home/reggie/vscode_folder/AI-VIDEO/.agents/skills/record-ai-video-session/scripts/session_record_hook.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "^(Edit|Write|MultiEdit|NotebookEdit|Bash)$",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"/home/reggie/vscode_folder/AI-VIDEO/.agents/skills/record-ai-video-session/scripts/session_record_hook.py\"",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "^(Bash|.*[Vv]ideo.*)$",
        "hooks": [
          {
            "type": "command",
            "command": "env PYTHONPATH=\"/home/reggie/vscode_folder/AI-VIDEO/src\" \"/home/reggie/.local/share/ai-video/video-analysis-mcp/bin/python\" -m ai_video_mcp.analysis_hook post-tool-use",
            "timeout": 2
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "manual|auto",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"/home/reggie/vscode_folder/AI-VIDEO/.agents/skills/record-ai-video-session/scripts/session_record_hook.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"/home/reggie/vscode_folder/AI-VIDEO/.agents/skills/record-ai-video-session/scripts/session_record_hook.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: 冒烟验证 hook 可执行**

Run: `echo '{"hook_event_name":"SessionStart","session_id":"claude-adapter-smoke","cwd":"/home/reggie/vscode_folder/AI-VIDEO"}' | python3 /home/reggie/vscode_folder/AI-VIDEO/.agents/skills/record-ai-video-session/scripts/session_record_hook.py`
Expected: 输出 `{"continue": true}`，exit 0

---

### Task 3: CLAUDE.md 瘦身为薄 adapter

**Files:**
- Modify: `CLAUDE.md`（全量重写为以下内容）
- Test: `tests/test_claude_code_adapter.py`（Task 6 断言 `@AGENTS.md` import 存在）

**Interfaces:**
- Produces: Claude Code 启动时经 `@AGENTS.md` import 加载全部 canonical 规则。

- [ ] **Step 1: 重写 `CLAUDE.md`**

```markdown
# AI-VIDEO Claude Code Adapter

本文件是 Claude Code runtime 的薄 adapter，不是规则正文。Canonical source of truth 是 AGENTS.md，经下方 import 全量加载。

禁止在本文件复制或改写规则正文；任何规则修改只改 AGENTS.md 及其委托文档（`docs/agent-primary-contract-matrix.md`、`.agent/harness/policy.yaml`、`.agent/context/control-plane-playbook.md`）。本文件若与 AGENTS.md 冲突，以 AGENTS.md 为准。

@AGENTS.md

## Claude Runtime Notes

- Session-record hooks 接线在 `.claude/settings.json`，与 `.codex/hooks.json` 共用同一 `.agents/skills/record-ai-video-session/scripts/session_record_hook.py`。
- 项目 skill 唯一实体在 `.agents/skills/`；`.claude/skills/` 只是指向它们的可见性接缝（symlink），不得在 `.claude/skills/` 维护第二份正文。
- 独立 reviewer subagent 定义在 `.claude/agents/harness-reviewer.md`；dual review 的触发边界与裁决规则见 AGENTS.md `Agent Workflow Routing`。
- Specs / plans 约定：`docs/superpowers/specs|plans/YYYY-MM-DD-<slug>.md`；plan 编写复用 `superpowers:writing-plans`。
```

- [ ] **Step 2: 验证 import 目标存在且文件瘦身后 < 60 行**

Run: `wc -l CLAUDE.md && grep -c '@AGENTS.md' CLAUDE.md`
Expected: 行数 < 60；import 计数 = 1

---

### Task 4: `.claude/skills/` 可见性接缝（symlink）

**Files:**
- Create: `.claude/skills/open-video` → `../../.agents/skills/open-video`（symlink）
- Create: `.claude/skills/h3-video` → `../../.agents/skills/h3-video`
- Create: `.claude/skills/seedance-authoring` → `../../.agents/skills/seedance-authoring`
- Create: `.claude/skills/ecommerce-ad-workflow` → `../../.agents/skills/ecommerce-ad-workflow`
- Create: `.claude/skills/retrieve-ai-video-memory` → `../../.agents/skills/retrieve-ai-video-memory`
- Create: `.claude/skills/record-ai-video-session` → `../../.agents/skills/record-ai-video-session`
- Create: `.claude/skills/distill-ai-video-learning` → `../../.agents/skills/distill-ai-video-learning`

**Interfaces:**
- Consumes: `.agents/skills/*/SKILL.md`（唯一实体，不复制）。
- Produces: Claude Code 可发现的项目 skill；Task 6 断言 symlink 目标解析到含 `description` frontmatter 的 SKILL.md。

- [ ] **Step 1: 确认每个 SKILL.md 有 Claude 兼容 frontmatter（`name` + `description`）**

Run: `for d in open-video h3-video seedance-authoring ecommerce-ad-workflow retrieve-ai-video-memory record-ai-video-session distill-ai-video-learning; do echo "== $d"; head -5 ".agents/skills/$d/SKILL.md"; done`
Expected: 每个都有 `name:` 与 `description:`；若有缺失，先补齐 `.agents/skills/` 侧 frontmatter（那是唯一实体，补齐它也利于 Codex 侧一致性），不得只在接缝侧修补。

- [ ] **Step 2: 创建 symlink**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/.claude/skills
for d in open-video h3-video seedance-authoring ecommerce-ad-workflow retrieve-ai-video-memory record-ai-video-session distill-ai-video-learning; do
  ln -s "../../.agents/skills/$d" "$d"
done
ls -la
```

- [ ] **Step 3: 验证目标解析**

Run: `for d in /home/reggie/vscode_folder/AI-VIDEO/.claude/skills/*/; do test -f "$d/SKILL.md" && echo "OK $d" || echo "BROKEN $d"; done`
Expected: 7 个 OK

- [ ] **Step 4（条件性 fallback）:** 若 Claude Code 实际会话不发现 symlink skill（在新的 Claude 会话中确认 skill 列表），把 symlink 替换为目录 + 薄 `SKILL.md` wrapper：frontmatter 从实体复制（标注 `canonical: ../../.agents/skills/<name>/SKILL.md`），正文只有一行指令"读取并遵循 canonical 文件"。是否触发 fallback 记录在交付报告的 NOT_EVALUATED / fallback 小节。

---

### Task 5: `.claude/agents/harness-reviewer.md` 只读 reviewer subagent

**Files:**
- Create: `.claude/agents/harness-reviewer.md`
- Test: `tests/test_claude_code_adapter.py`（Task 6 断言文件存在、frontmatter 工具集不含写工具）

**Interfaces:**
- Produces: 名为 `harness-reviewer` 的 subagent，供 parent 在 review boundary 派发两个独立实例（不同视角 prompt）。

- [ ] **Step 1: 创建文件**

```markdown
---
name: harness-reviewer
description: Independent read-only reviewer for AI-VIDEO Harness review boundaries (spec review, plan review, implementation review, final dual review). Use proactively when AGENTS.md "Agent Workflow Routing" triggers a review; two isolated instances review the same immutable target without seeing each other's conclusions.
tools: Read, Grep, Glob, Bash
model: inherit
---

You are an independent reviewer inside the AI-VIDEO Harness. You do not edit, create, or delete anything. You do not inherit the main session's history or conclusions.

## Authority

- Canonical rules: `AGENTS.md`, `docs/agent-primary-contract-matrix.md`, `.agent/harness/policy.yaml`, `.agent/context/control-plane-playbook.md`.
- The review target (spec, plan, diff, or stated snapshot) is identified in your dispatch message together with an immutable target ID (exact commit or exact staged-snapshot description). Review exactly that state, nothing else.
- `superpowers:requesting-code-review` 的 reviewer 模板思想适用于证据组织，但本 reviewer 的判定标准以 AI-VIDEO canonical 文档为准。

## Rules

1. Read-only. You may run only read-only shell commands (`git status`, `git diff`, `git log`, `rg`, pytest collection, `python scripts/agent_harness.py inspect …`, `python scripts/agent_harness.py verify-receipt …`). Never run anything that mutates the working tree, index, manifests, runs/, or provider state.
2. Judge against the acceptance criteria and contracts named in your dispatch. Do not loosen acceptance criteria. Do not review outside the stated scope.
3. Every finding carries: severity (`blocking` / `major` / `minor`), evidence (file:line or command output), and the contract clause violated.
4. Distinguish verification levels: execution success, structural validity, functional correctness, acceptance criteria, final review acceptance. Flag any completion claim that substitutes a lower level for a higher one (metric substitution).
5. Unverifiable items are `NOT_EVALUATED`, never assumed PASS.
6. `PARSED` / `review executed` is not `accepted`.

## Output

End with exactly one verdict line:

- `VERDICT: NO_BLOCKING_ISSUES` — when no blocking/major finding remains, followed by a residual-risk list; or
- `VERDICT: BLOCKING_ISSUES` — followed by the numbered blocking findings.
```

- [ ] **Step 2: 静态验证 frontmatter**

Run: `head -8 .claude/agents/harness-reviewer.md`
Expected: `name: harness-reviewer`、`tools: Read, Grep, Glob, Bash`（无 Edit/Write/NotebookEdit）

---

### Task 6: Adapter 完整性测试 + policy.yaml coverage

**Files:**
- Create: `tests/test_claude_code_adapter.py`
- Modify: `.agent/harness/policy.yaml`（audit_patterns 与 control_plane category 追加；harness_tests argv 追加新测试文件）

**Interfaces:**
- Consumes: Task 2 的 `.claude/settings.json`、Task 3 的 `CLAUDE.md`、Task 4 的 `.claude/skills/`、Task 5 的 `.claude/agents/harness-reviewer.md`、Task 1 的 `CLAUDE_WRITE_TOOL_PATH_KEYS`。
- Produces: `harness_tests` check 覆盖 adapter 完整性；policy 对 `.claude/agents/**`、`.claude/skills/**`、`CLAUDE.md` 有 category coverage。

- [ ] **Step 1: 创建 `tests/test_claude_code_adapter.py`**

```python
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = ROOT / "CLAUDE.md"
CLAUDE_SETTINGS = ROOT / ".claude" / "settings.json"
REVIEWER_AGENT = ROOT / ".claude" / "agents" / "harness-reviewer.md"
CLAUDE_SKILLS_DIR = ROOT / ".claude" / "skills"
CANONICAL_SKILLS_DIR = ROOT / ".agents" / "skills"
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
        if any("session_record_hook.py" in hook["command"] for hook in registration["hooks"])
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
    visible = {entry.name for entry in CLAUDE_SKILLS_DIR.iterdir()}
    assert EXPECTED_PROJECT_SKILLS <= visible
    for name in EXPECTED_PROJECT_SKILLS:
        skill_md = (CLAUDE_SKILLS_DIR / name / "SKILL.md").resolve()
        assert skill_md.is_file()
        assert CANONICAL_SKILLS_DIR in skill_md.parents  # 实体唯一，无第二份正文
        head = skill_md.read_text(encoding="utf-8")[:2000]
        assert "description:" in head
```

- [ ] **Step 2: policy.yaml 追加 coverage（只追加，不动既有行）**

`audit_patterns:` 段（`.claude/settings/*.json` 行附近）追加：

```yaml
  - CLAUDE.md
  - .claude/agents/**
  - .claude/skills/**
```

`control_plane` category 的 `patterns:` 追加同样三行，并追加 `tests/test_claude_code_adapter.py`。

`harness_tests` check 的 argv 追加 `tests/test_claude_code_adapter.py`：

```yaml
    argv: [python, -m, pytest, -p, no:cacheprovider, tests/test_docs_contract_gate.py, tests/test_agent_harness.py, tests/test_record_ai_video_session_hook.py, tests/test_claude_code_adapter.py, -q]
```

- [ ] **Step 3: 运行新测试**

Run: `python -m pytest -p no:cacheprovider tests/test_claude_code_adapter.py -q`
Expected: 5 个测试全部 PASS

- [ ] **Step 4: policy 自检**

Run: `python scripts/agent_harness.py policy-audit`
Expected: exit 0，无 unmapped/unverified paths

---

### Task 7: AGENTS.md 新增 Agent Workflow Routing 章节 + playbook 操作细节

**Files:**
- Modify: `AGENTS.md`（在 `## Creative Skill Routing` 之后、`## Module Boundaries` 之前插入新章节）
- Modify: `.agent/context/control-plane-playbook.md`（追加一节操作细节；该文件有用户未提交改动，只追加不改动既有内容）

**Interfaces:**
- Produces: runtime-agnostic 共享契约（instruction hierarchy、tier 路由、trigger、review boundary、dual review、verification 五级、evidence、角色、context control）。CLAUDE.md 经 import 自动承载，无需二次维护。

- [ ] **Step 1: AGENTS.md 插入以下章节**

```markdown
## Agent Workflow Routing

Canonical contract for how any agent runtime (Codex, Claude Code, future runtimes) selects skills, specs, plans, review, and verification depth. Runtime adapters (`.codex/`, `CLAUDE.md`, `.claude/`) only wire this contract and must not carry a second copy. Operational detail lives in `.agent/context/control-plane-playbook.md`; the original design spec is `docs/superpowers/specs/2026-09-20-claude-code-harness-adapter.md`.

### Instruction Hierarchy

确定性优先级（高到低），冲突时低位阶不得推翻高位阶：

1. 用户当前明确指令。
2. 当前代码、测试与已验证 runtime evidence。
3. 本 `AGENTS.md` 及其委托的 contract matrix、policy.yaml、playbook。
4. 当前 slice 的 accepted spec 与 approved plan。
5. Skill instructions（含 superpowers 与 `.agents/skills/`）。
6. Reviewer feedback（advisory，由 parent 裁决后落地）。
7. Runtime 默认行为（含插件 skill 的默认触发门控）。

Skill 默认门控与本节 routing 冲突时，以本节为准。

### Task Tiers And Skill Routing

按 semantic risk / blast radius 分级，不按代码行数：

| Tier | 判据 | 必需流程 |
| --- | --- | --- |
| T0 局部低风险 | 单文件、可逆、无契约面变化 | implement + targeted validation |
| T1 中等 | 多文件、边界清晰、无 shared contract 变化 | （必要时 research）→ plan → implement → verify |
| T2 高风险 | architecture / workflow state machine / Provider contract / Harness 行为 / shared schema / acceptance criteria / cross-module 变化 | research → specs → plan → implement → verification → implementation review |
| T3 关键契约 | canonical ownership、verification contract、paid/credential/recovery/QA acceptance 语义变化 | T2 全部 + final dual independent review |
| Bug | 任意 tier 的 bug | 先 systematic-debugging 做 root-cause，再按 tier 走流程，末做 regression validation |

Skill 命中即触发、不预载全部：设计不清 → brainstorming；写 plan → writing-plans（落 `docs/superpowers/plans/`）；执行已批准 plan → executing-plans / subagent-driven-development；bug → systematic-debugging；声称完成前 → verification-before-completion；到达 review 边界 → 本节 reviewer 机制；项目 skill 与 creative skill 按本文件既有 routing 表。

### Specs / Plan / Review Triggers

- Specs 触发：architecture contract、workflow state machine、Provider contract、Harness 行为、acceptance criteria、Shot generation/regeneration policy、shared schema、persistent project rule、cross-module 行为变化，或用户明确要求。普通小修复不触发。
- Plan 触发：多文件且顺序非显而易见、多阶段、T2/T3、architecture/Provider/workflow 修改、涉及迁移/回滚/兼容性。复用 writing-plans，不重新实现。T0/T1 简单任务不产 plan artifact。
- Review 只在完整稳定 target 的边界触发：T2/T3 的 spec 完成后、plan 完成后、implementation 到达完整 checkpoint 后；T3 在声明完成前做 final dual review。T0/T1 不触发独立 review。禁止碎片化 reviewer loop；`review executed` / `PARSED` 不等于 `accepted`。

### Dual Independent Review

T3（及 parent 判定的高风险 spec/plan）必须双独立审查：两个 reviewer 针对同一 immutable review target（exact commit 或 exact staged snapshot，target ID 记入证据）独立审查；互不先看对方结论；双方都无 blocking issue 才允许 acceptance；不用多数票；冲突由 parent 调查具体 evidence 裁决；reviewer 不修改 acceptance criteria；修复后生成新 target，两个 reviewer 基于同一新状态重审。两个 reviewer 可以是同一 runtime 上两个隔离 context 的独立 subagent 实例，也可以是跨 runtime；后者独立性更强，优先在可用时使用。

### Verification Levels And Evidence

声称完成前区分五级，不得以下位替代上位：execution success、structural validity、functional correctness、acceptance criteria、final review acceptance。局部机器指标不能替代最终成片目标（禁止 metric substitution）。所有 PASS / DONE / ACCEPTED 必须附 evidence；无法验证的项明确标 `NOT_EVALUATED`。

### Roles

- Parent（主会话）：理解最终目标、按本节决定 routing、分派任务、裁决 reviewer disagreement、唯一执行最终 acceptance 判断。
- Worker：实施具体任务，不得自行降低 acceptance criteria。
- Reviewer：独立、read-only 优先、输出 evidence + severity、不继承主会话历史、不负责让任务通过。

### Context Control

常驻 context 仅限用户全局规则、runtime adapter 文件与 canonical 规则正文；skill 正文、spec、plan、provider/workflow 文档按需加载（progressive disclosure），降低 context pollution 与 stale context。
```

- [ ] **Step 2: playbook 追加操作细节节**（追加到 `.agent/context/control-plane-playbook.md` 末尾）

```markdown
## Agent Workflow Operations

### Constructing An Immutable Review Target

1. 确认工作树中 target 相关文件完整：`git status --short`。
2. 选择 target 形式：exact commit（`git rev-parse HEAD`）或 exact staged snapshot（`git add <specific-files>` 后记录 `git diff --staged --stat` 与涉及文件列表）。
3. 把 target ID（commit SHA 或 staged 文件清单 + 时间）写进派发消息；两个 reviewer 必须使用同一 ID。

### Dispatching Dual Reviewers

- Reviewer A 视角：correctness / risk / failure path。
- Reviewer B 视角：contract compliance / acceptance criteria / metric-substitution 检查。
- 两次派发使用独立 subagent context；不得把 A 的结论放进 B 的 prompt，反之亦然。
- Claude Code 实现：`.claude/agents/harness-reviewer.md`（name: `harness-reviewer`）。

### Adjudication

- 双方都 `VERDICT: NO_BLOCKING_ISSUES` → parent 可做 acceptance 判断。
- 任一 `BLOCKING_ISSUES` → parent 逐条调查 evidence；成立的修复，不成立的记录驳回理由。
- 修复产生新 target → 两个 reviewer 对新 target 全量重审（不是增量确认）。
- reviewer 间的结论冲突不投票、不迁就，由 parent 以 evidence 裁决。
```

- [ ] **Step 3: 静态验证**

Run: `grep -c "Agent Workflow Routing" AGENTS.md && grep -c "Agent Workflow Operations" .agent/context/control-plane-playbook.md`
Expected: 各 = 1（AGENTS.md 中章节标题一次；正文引用次数另计但标题唯一）

---

### Task 8: 最终 Harness 验证（staged snapshot）

**Files:**
- 无新文件；对 Task 1–7 的全部 changed files 做 staged 验证。

**Interfaces:**
- Consumes: Task 1–7 的全部产出。

- [ ] **Step 1: 精确 stage task-owned files**

```bash
git add CLAUDE.md AGENTS.md .claude/settings.json .claude/agents/harness-reviewer.md \
  .agents/skills/record-ai-video-session/scripts/session_record_hook.py \
  tests/test_record_ai_video_session_hook.py tests/test_claude_code_adapter.py \
  .agent/harness/policy.yaml .agent/context/control-plane-playbook.md \
  docs/superpowers/specs/2026-09-20-claude-code-harness-adapter.md \
  docs/superpowers/plans/2026-09-20-claude-code-harness-adapter.md
```

注意：`.claude/skills/*` symlink 是否入库取决于用户偏好——symlink 进 git 会让其他 checkout 生效；若用户不希望入库，加入 `.gitignore` 说明并在交付报告中标注。默认 stage：`git add .claude/skills`（7 个 symlink）。policy.yaml 与 playbook 含有用户未提交改动——stage 前用 `git diff --staged -- <file>` 与 `git diff -- <file>` 确认用户的改动一并被 stage 是可接受的（它们属于同一 control-plane 变更面）；如有疑问停下报告。

- [ ] **Step 2: harness staged 验证**

Run: `make harness-verify`
Expected: receipt 生成且 PASS（control_plane scope → harness_tests，含新 adapter 测试）

- [ ] **Step 3: receipt 校验**

Run: `python scripts/agent_harness.py verify-receipt <最新 receipt 路径>`
Expected: PASS，scope 与 artifact hashes 匹配

- [ ] **Step 4: docs contract gate**

Run: `python scripts/docs_contract_gate.py`
Expected: exit 0

- [ ] **Step 5: policy-audit 终检**

Run: `python scripts/agent_harness.py policy-audit`
Expected: exit 0

---

## Self-Review 记录

- Spec coverage：spec 的 10 项契约 → Task 7 承载（AGENTS.md/playbook）；adapter 六项文件改动 → Task 1–6；验证契约 → Task 8。KFC 遗留按 spec 仅报告，无 task（符合 REPORT ONLY）。
- Placeholder scan：无 TBD/TODO；fallback 分支（Task 4 Step 4）是条件性且带判定方法与记录要求。
- Type/name 一致性：`CLAUDE_WRITE_TOOL_PATH_KEYS`（Task 1 定义，Task 6 断言）；`harness-reviewer`（Task 5 定义，Task 6/Task 7 引用）；`tests/test_claude_code_adapter.py`（Task 6 创建并加入 harness_tests argv）一致。
