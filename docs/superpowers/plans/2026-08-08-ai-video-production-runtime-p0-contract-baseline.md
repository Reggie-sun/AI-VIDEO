# AI-VIDEO Production Runtime P0 Contract and Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 批准 v0.2 的分阶段演进边界并固化当前 runtime baseline，同时保持现有代码、CLI、Manifest schema、产物布局和纯本地默认行为完全不变。

**Architecture:** P0 只调整契约和事实文档：`AGENTS.md` 继续拥有当前可执行规则，contract matrix 定义后续 slice 的 decision gates，`README.md` 只描述真实已实现行为，runtime baseline 记录当前能力与已知缺口，v0.2 spec 仅升级为“允许分阶段规划”。P0 不修改 `src/`、`tests/`、`pyproject.toml`、workflow、config 或生成产物；P1 才处理 terminal failure persistence、stale propagation 和 source/delivery media semantics。

**Tech Stack:** Markdown、Git、Python 3.11+、pytest；不新增依赖，不调用真实 ComfyUI、云 Provider 或 ffmpeg 生产流程。

---

## Scope and Approval Gate

执行本 plan 前必须有用户对 **P0 plan 本身** 的明确实施授权。仅“写 plan”不等于授权执行。

P0 允许改动：

- `AGENTS.md`
- `docs/agent-primary-contract-matrix.md`
- `README.md`
- `docs/v0.2-runtime-baseline.md`
- `docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p0-contract-baseline.md`
- `docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md`

P0 禁止改动：

- `src/ai_video/**`
- `src/ai_video_mcp/**`
- `tests/**`
- `pyproject.toml`
- `configs/**`
- `workflows/**`
- `.workflow/**`
- `runs/**`

P0 不批准：

- Manifest v2 或 artifact layout v2。
- 新 CLI command / flag / exit-code semantics。
- Provider abstraction 或 Seedance integration。
- Audio、Reference v2、Take、Human Review、Budget 或 Cloud Egress runtime。
- 新 runtime dependency。

执行过程用 session/task 状态跟踪 checkbox，不要为了勾选进度而修改本 plan 文件。Task 1 只在本 plan 尚未被 Git 跟踪时将它纳入 baseline commit。

---

## File Ownership and Old-Path Decision

| File | P0 Responsibility | Old Path Decision |
| --- | --- | --- |
| `AGENTS.md` | 当前 runtime 与未来 v0.2 planning 的最高仓库规则 | 保留当前规则；增加 versioned boundary，不把 proposed feature 写成已实现能力 |
| `docs/agent-primary-contract-matrix.md` | 各变更面的 gate、owner 和最低验证 | 保留现有 matrix；增加 v0.2 slice gate，不建立第二套 contract matrix |
| `README.md` | 用户可见的当前 runtime truth | 保留现有 CLI/layout 说明；修正 attempt 和 stale/resume 的过度表述 |
| `docs/v0.2-runtime-baseline.md` | P0 当前事实、缺口和验证命令 | 新建；只做 evidence index，不成为代码之外的第二事实源 |
| `docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md` | v0.2 目标契约 | 从 Proposed 升级为 phased-planning approval；仍不授权任何 slice 实施 |

唯一 owner 规则：当前 runtime truth 始终由代码、测试和已验证行为拥有；`AGENTS.md` 约束执行；spec 定义目标；plan 定义一次 slice 的执行方式；baseline 只索引证据。

---

### Task 1: Verify the P0 Gate and Create the Runtime Baseline

**Files:**
- Create: `docs/v0.2-runtime-baseline.md`
- Track/Modify: `docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p0-contract-baseline.md`
- Read: `src/ai_video/manifest.py`
- Read: `src/ai_video/pipeline.py`
- Read: `src/ai_video/models.py`
- Test: `tests/test_manifest.py`
- Test: `tests/test_pipeline.py`
- Test: `tests/test_resume_e2e.py`
- Test: `tests/test_config.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Confirm execution authority and protect existing work**

Read the user execution request and confirm it explicitly authorizes this P0 plan. Then run:

```bash
git status --short
git diff --name-only
```

Expected: existing user changes are identified before editing. The v0.2 spec and this plan may already be untracked or modified; no unrelated file may be reset, overwritten, staged, or committed.

- [ ] **Step 2: Re-verify the current runtime gaps from source**

Run:

```bash
rg -n "successful_shot_is_valid|mark_downstream_stale|chain_input_hash|character_ref_hashes" src/ai_video/manifest.py src/ai_video/pipeline.py
rg -n "attempts.append|atomic_write_manifest|raise$|isinstance\(self.comfy, ComfyClient\)" src/ai_video/pipeline.py
rg -n "defaults\.fps|normalize_clip" src/ai_video/pipeline.py src/ai_video/models.py
```

Expected evidence:

- `successful_shot_is_valid()` requires `succeeded` status, populated clip/last-frame paths and hashes, and existing files; it then validates only clip and last-frame content hashes, not input dependency hashes.
- `mark_downstream_stale()` exists but is not wired into the real resume path.
- `chain_input_hash` and `character_ref_hashes` are recorded but not part of validity.
- Attempts are accumulated inside `_run_shot()`, while the completed `ShotRecord` is persisted only after `_run_shot()` returns successfully.
- `PipelineRunner` still branches on concrete `ComfyClient` behavior.
- `defaults.fps` is the generation fallback/default (`shot.fps` may override generation) and the unconditional delivery-normalization FPS.

- [ ] **Step 3: Run the no-network baseline tests**

Run:

```bash
python -m pytest tests/test_config.py tests/test_cli.py tests/test_manifest.py tests/test_pipeline.py tests/test_resume_e2e.py -q
```

Expected: command exits `0`. These tests characterize the current supported path; they do not prove the known P0 gaps are fixed.

- [ ] **Step 4: Create the baseline document with exact current-truth wording**

Create `docs/v0.2-runtime-baseline.md` with:

````markdown
# AI-VIDEO v0.2 P0 Runtime Baseline

Status: Verified planning baseline; code and tests remain the source of truth.
Scope: Current local CLI runtime only. No v0.2 runtime feature is implied by this document.

## Current Contract

- The implemented product is a pure-local Python CLI around local ComfyUI.
- Public commands are `ai-video validate`, `ai-video run`, and `ai-video resume`.
- `validate` is side-effect free.
- Manifest v1 and the flat `runs/<run_id>/` layout remain active.
- Local Wan + ComfyUI is the only production generation path.

## Verified Implemented Behavior

- YAML + Pydantic config loading with clean absolute resolved paths.
- API-format and UI-graph workflow loading through the production loader.
- Template + binding rendering without hard-coded node IDs in the pipeline.
- Sequential shot execution and optional last-frame chaining.
- Bounded typed-error retry.
- Atomic Manifest writes.
- Clip, normalized clip, last-frame, final output and relevant hashes on successful runs.
- Manifest-driven resume that skips shots whose currently checked artifacts remain valid.
- ffmpeg/ffprobe validation, extraction, normalization and stitching helpers.

## Verified Runtime Gaps

- `successful_shot_is_valid()` requires `succeeded` status, populated clip/last-frame paths and hashes, and existing files; it then validates only clip and last-frame content hashes, not input dependency hashes.
- `chain_input_hash` and `character_ref_hashes` are recorded but do not participate in validity.
- `mark_downstream_stale()` is not connected to the real resume path.
- An upstream rerun can therefore leave a downstream shot incorrectly skippable when its own clip and last-frame hashes still match.
- A terminally failed shot does not persist its complete Attempt history before `_run_shot()` raises.
- The pipeline is coupled to one ComfyUI transport/template path and contains concrete `ComfyClient` branching.
- `defaults.fps` is the generation fallback/default (`shot.fps` may override generation) and the unconditional delivery-normalization FPS.
- Existing video analysis is technical/heuristic and is not an identity, continuity or prompt-adherence evaluator.

## Evidence Commands

```bash
python -m pytest tests/test_config.py tests/test_cli.py tests/test_manifest.py tests/test_pipeline.py tests/test_resume_e2e.py -q
rg -n "successful_shot_is_valid|mark_downstream_stale|chain_input_hash|character_ref_hashes" src/ai_video/manifest.py src/ai_video/pipeline.py
rg -n "attempts.append|atomic_write_manifest|raise$|isinstance\(self.comfy, ComfyClient\)" src/ai_video/pipeline.py
```

The baseline is valid only when the pytest command exits `0` and source evidence still matches the statements above. Every later plan must re-run its affected checks instead of treating this file as runtime truth.

## P0 Non-Authorization

P0 does not authorize or implement Provider abstraction, Manifest v2, Take, Human Review, new CLI commands, cloud access, Budget Guard, Reference v2, Semantic Evaluation or Audio.
````

- [ ] **Step 5: Verify the baseline has no future capability stated as current**

Run:

```bash
rg -n "Current Contract|Verified Implemented Behavior|Verified Runtime Gaps|P0 Non-Authorization" docs/v0.2-runtime-baseline.md
rg -n "Seedance|Manifest v2|Audio|Budget Guard|Human Review" docs/v0.2-runtime-baseline.md
```

Expected: the first command finds all four sections. The second command finds those terms only in `P0 Non-Authorization`, not under implemented behavior.

- [ ] **Step 6: Commit the baseline document**

```bash
git add docs/v0.2-runtime-baseline.md docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p0-contract-baseline.md
git commit -m "docs: record v0.2 runtime baseline"
```

Expected: commit always contains `docs/v0.2-runtime-baseline.md`; it also begins tracking this approved plan when the plan was not already tracked. No other file is included.

---

### Task 2: Add the Versioned Product Boundary to AGENTS.md

**Files:**
- Modify: `AGENTS.md:5-15`
- Modify: `AGENTS.md:43-54`
- Modify: `AGENTS.md:122-130`

- [ ] **Step 1: Insert the versioned boundary after `Purpose`**

Insert after the current product-commitment bullets:

```markdown
## Versioned Product Boundary

- 当前已实现的 `0.1.x` / legacy runtime 仍是纯本地 Python CLI，只支持本地 ComfyUI、三个公共命令和当前 flat artifact layout。
- `docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md` 是已批准的分阶段 planning target，不是已实现行为，也不是一次性实施授权。
- v0.2 的 P0-P9 每个 slice 都必须拥有独立 plan、明确验收、回滚路径和用户实施授权。
- 某个 slice 落地前，与该 slice 冲突的当前契约继续有效；不得通过只改文档把 proposed behavior 描述成 runtime truth。
- Local Wan + ComfyUI 始终保持默认路径。任何远程 Provider 都必须在后续独立 slice 中满足 explicit opt-in、Budget Guard、Cloud Egress 和 crash-safe persistence gate。
```

- [ ] **Step 2: Make the Stable Product Contract explicitly current-version scoped**

Replace the first three bullets under `Stable Product Contract` with:

```markdown
- 当前 legacy runtime 保持纯本地形态；v0.2 远程 Provider 只有在对应 slice 获批并完成安全前置后才允许以 opt-in 方式加入，且永不成为默认 fallback。
- 当前公共 CLI 面保持为 `ai-video validate`、`ai-video run`、`ai-video resume`；任何 v0.2 新命令必须在独立 plan 中同步 CLI tests、README 和退出码契约。
- `validate` 必须保持无副作用；默认不得联网、上传素材、创建 run 目录或触发付费调用。
```

Keep all remaining stable-contract bullets unchanged.

- [ ] **Step 3: Add the per-slice gate to `Decision Gates`**

Append this bullet to the existing gate list:

```markdown
- 执行 v0.2 P1-P9 任一 slice，或把 spec 中的 proposed contract 写成当前行为。
```

- [ ] **Step 4: Verify AGENTS.md remains a durable rule file**

Run:

```bash
rg -n "Versioned Product Boundary|0\.1\.x|P0-P9|Local Wan|P1-P9" AGENTS.md
git diff --check -- AGENTS.md
```

Expected: all version-boundary rules are present; no task-specific command transcript, implementation checklist or whitespace error was added.

- [ ] **Step 5: Commit the repository-rule amendment**

```bash
git add AGENTS.md
git commit -m "docs: define phased v0.2 product boundary"
```

Expected: commit contains only `AGENTS.md`.

---

### Task 3: Extend the Primary Contract Matrix Without Creating a Second Control Plane

**Files:**
- Modify: `docs/agent-primary-contract-matrix.md:7-31`
- Modify: `docs/agent-primary-contract-matrix.md:67-89`

- [ ] **Step 1: Replace the global scope rows with version-aware wording**

Replace `Product Scope` and `Output Policy`, and add `Version Gate`, so the global table contains:

```markdown
| Product Scope | 当前 `0.1.x` runtime 是纯本地 Python CLI + 本地 ComfyUI；v0.2 是 local-first、provider-agnostic 的分阶段目标，未落地的 slice 不属于当前行为。 |
| Truth Source | 用户请求 > 代码/测试/运行时证据 > 仓库契约 > plans/specs > `.workflow/` 草稿记录。 |
| Change Style | 小步、可测试、低漂移，并保持模块边界稳定。 |
| Error Model | 跨模块统一使用 `AiVideoError` 与 `ErrorCode`。 |
| Dependency Policy | 除非有明确理由且获得请求，否则不新增运行时依赖。 |
| Output Policy | Legacy run 保持当前 flat `runs/<run_id>/` layout；v2 layout 只能由显式 v2 config 和已批准的 Manifest v2 slice 创建。 |
| Version Gate | v0.2 P0-P9 每个 slice 必须有独立 plan、实施授权、验收、rollback 和对应 contract/docs/tests 更新。 |
```

- [ ] **Step 2: Add a single v0.2 planning gate after `Local-Only Contract`**

Insert:

```markdown
### v0.2 Planning Gate

- 当前 code/tests 仍是 runtime truth；spec 和 plan 不能覆盖未实现行为。
- P1/P2 不得改变 Legacy CLI、Manifest v1 或 flat artifact layout。
- P3 之前不得接入真实异步付费 Provider。
- P6 完成前不得真实提交云任务。
- P7 Seedance、P8 Semantic Evaluation 和 P9 Audio 必须分别规划和验收。
- 新 CLI、Manifest schema、artifact layout、远程行为、Audio 或 dependency 仍命中下方 Change Escalation Matrix。
```

Do not add another matrix file or duplicate module ownership tables from `AGENTS.md`.

- [ ] **Step 3: Verify the existing current-runtime rows remain intact**

Run:

```bash
rg -n "CLI Contract|Config Loading|Workflow Loading|Workflow Rendering|ComfyUI Transport|Pipeline Orchestration|Manifest Persistence|ffmpeg Boundary|Output Layout" docs/agent-primary-contract-matrix.md
rg -n "v0.2 Planning Gate|P1/P2|P3|P6|P7 Seedance|P9 Audio" docs/agent-primary-contract-matrix.md
git diff --check -- docs/agent-primary-contract-matrix.md
```

Expected: all existing surface rows remain; the new text adds gates without changing their current validation commands.

- [ ] **Step 4: Commit the matrix amendment**

```bash
git add docs/agent-primary-contract-matrix.md
git commit -m "docs: add v0.2 slice gates to contract matrix"
```

Expected: commit contains only `docs/agent-primary-contract-matrix.md`.

---

### Task 4: Correct README Runtime Truth and Link the Roadmap

**Files:**
- Modify: `README.md:1-20`
- Modify: `README.md:72-88`

- [ ] **Step 1: Add a roadmap-status section after the introduction**

Insert after the opening MVP description:

```markdown
## Roadmap Status

The currently implemented runtime is the pure-local `0.1.x` CLI described in this README. The proposed v0.2 direction is a local-first, provider-agnostic production runtime, but it is delivered through separately approved P0-P9 slices; the specification does not make those features available today.

- Current evidence: [`docs/v0.2-runtime-baseline.md`](docs/v0.2-runtime-baseline.md)
- Target contract: [`docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md`](docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md)
- First gate plan: [`docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p0-contract-baseline.md`](docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p0-contract-baseline.md)

Until a later slice is implemented and documented, the public commands remain `validate`, `run`, and `resume`; generation remains local ComfyUI; Manifest v1 and the current artifact layout remain active.
```

- [ ] **Step 2: Correct the failed-attempt retention claim**

Replace:

```markdown
The MVP keeps failed attempts and rendered workflow snapshots for debugging. Delete old `runs/<run_id>` directories manually when you no longer need them.
```

with:

```markdown
The MVP keeps rendered workflow snapshots and the Attempt history attached to a Shot that eventually succeeds. A terminally failed Shot does not yet persist its complete Attempt history; that gap is assigned to the v0.2 P1 plan. Delete old `runs/<run_id>` directories manually when you no longer need them.
```

- [ ] **Step 3: Correct the resume/stale claim**

Replace the paragraph after the resume command with:

```markdown
Resume currently reloads the existing Manifest and validates the persisted clip and last-frame hashes before deciding whether to skip a successful Shot. `chain_input_hash` and character-reference hashes are recorded but are not yet part of validity, and downstream stale propagation is not wired into the real resume path. Until the P1 fix lands, an upstream rerun can therefore leave a downstream Shot incorrectly skippable when that Shot's own checked hashes still match.
```

- [ ] **Step 4: Verify README describes only current commands and layout as available**

Run:

```bash
rg -n "Roadmap Status|currently implemented runtime|terminally failed Shot|downstream stale propagation|validate.*run.*resume" README.md
rg -n "ai-video (inspect|review|regenerate|compose|cost)" README.md
git diff --check -- README.md
```

Expected: current-vs-target wording and both known gaps are present. The proposed v2 commands are absent from user instructions.

- [ ] **Step 5: Commit the README correction**

```bash
git add README.md
git commit -m "docs: align README with current runtime truth"
```

Expected: commit contains only `README.md`.

---

### Task 5: Ratify the Spec for Phased Planning Only

**Files:**
- Modify: `docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md:1-32`

- [ ] **Step 1: Change only the spec status metadata**

Replace:

```markdown
Status: Proposed
```

with:

```markdown
Status: Approved for phased planning; implementation requires separate per-slice authorization.
```

Add directly below `Document Role`:

```markdown
P0 Baseline: `docs/v0.2-runtime-baseline.md`
P0 Plan: `docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p0-contract-baseline.md`
```

Do not alter P1-P9 scope, Provider schemas, CLI proposals, acceptance criteria or implementation ordering in this task.

- [ ] **Step 2: Verify approval language does not become implementation authorization**

Run:

```bash
sed -n '1,40p' docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md
rg -n "Approved for phased planning|implementation requires separate|不授权|每个 plan 只能覆盖" docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md
```

Expected: metadata approves phased planning while the authority section still rejects direct coding, one-shot implementation and automatic cloud enablement.

- [ ] **Step 3: Commit the spec ratification**

```bash
git add docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md
git commit -m "docs: approve v0.2 for phased planning"
```

Expected: commit contains only the v0.2 spec. If the spec was untracked before P0 execution, this commit intentionally begins tracking the reviewed spec; no other untracked file is staged.

---

### Task 6: Verify P0 Has No Runtime or Contract Leakage

**Files:**
- Verify: `AGENTS.md`
- Verify: `docs/agent-primary-contract-matrix.md`
- Verify: `README.md`
- Verify: `docs/v0.2-runtime-baseline.md`
- Verify: `docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md`
- Must remain unchanged: `src/**`, `tests/**`, `pyproject.toml`, `configs/**`, `workflows/**`

- [ ] **Step 1: Run focused and full no-network tests**

Run:

```bash
python -m pytest tests/test_config.py tests/test_workflow_loader.py tests/test_workflow_renderer.py tests/test_comfy_client.py tests/test_pipeline.py tests/test_manifest.py tests/test_resume_e2e.py tests/test_ffmpeg_tools.py tests/test_cli.py -q
python -m pytest -q
```

Expected: both commands exit `0`; no real ComfyUI, cloud Provider or live ffmpeg generation is invoked.

- [ ] **Step 2: Prove implementation surfaces did not change**

Run:

```bash
git diff --name-only HEAD~5..HEAD -- src tests pyproject.toml configs workflows
```

Expected: no output. P0 commits contain documentation and contract files only.

- [ ] **Step 3: Check current-vs-proposed wording across all P0 documents**

Run:

```bash
rg -n "current|当前|implemented|已实现|proposed|规划|planning|未落地" AGENTS.md docs/agent-primary-contract-matrix.md README.md docs/v0.2-runtime-baseline.md docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md
rg -n "default fallback|默认 fallback|silent fallback" AGENTS.md docs/agent-primary-contract-matrix.md README.md docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md
```

Expected: current runtime and proposed v0.2 target are consistently separated; remote Provider is never described as default or silently enabled.

- [ ] **Step 4: Run document integrity and placeholder checks**

Run:

```bash
git diff --check HEAD~5..HEAD
rg -n "T[B]D|T[O]DO|F[I]XME|impl[e]ment later|fill in detail[s]" docs/v0.2-runtime-baseline.md docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p0-contract-baseline.md
```

Expected: `git diff --check` exits `0`; the placeholder scan produces no output.

- [ ] **Step 5: Inspect final scope and commit history**

Run:

```bash
git status --short
git log -5 --oneline --decorate
git show --stat --oneline HEAD~5..HEAD
```

Expected: no P0-owned file remains unstaged; unrelated pre-existing user changes remain untouched. The five P0 commits are baseline/plan tracking, repository rule, contract matrix, README correction and spec ratification.

---

## Acceptance Criteria

P0 is complete only when all statements are true:

1. v0.2 is approved for phased planning, not direct implementation.
2. Current `0.1.x` runtime remains pure-local and defaults to local Wan + ComfyUI.
3. Public CLI remains `validate`、`run`、`resume`.
4. Manifest v1 and current flat artifact layout remain active and unchanged.
5. README no longer claims terminal failed Attempt history or real downstream stale propagation already works.
6. Baseline names all verified current gaps without describing a fix.
7. `AGENTS.md` and contract matrix require a separate authorized plan for every P1-P9 slice.
8. No runtime dependency、source file、test file、config、workflow or generated artifact changed.
9. Focused and full pytest commands exit `0`.
10. P1 remains the next and only authorized implementation-planning boundary after P0.

## Rollback

P0 has no data or runtime migration. Rollback is documentation-only:

1. Revert the P0 commits in reverse order with normal `git revert` commits.
2. Restore spec status to `Proposed`.
3. Remove `docs/v0.2-runtime-baseline.md` and versioned-boundary additions through those reverts.
4. Re-run `python -m pytest -q` to demonstrate runtime remained unchanged.

Do not use `git reset --hard`, delete user work, or rewrite published history.

## Next Plan Boundary

After P0 is explicitly executed and accepted, create a separate P1 plan covering only:

- terminal failed Attempt persistence before exception escape;
- real downstream stale propagation from current last-frame dependencies;
- explicit source-generation versus delivery-normalization FPS semantics;
- tests in `tests/test_manifest.py`、`tests/test_pipeline.py`、`tests/test_resume_e2e.py` and the nearest user-facing README update.

P1 must not introduce Provider abstraction, Manifest v2, new CLI commands, cloud behavior, Audio or artifact layout changes.
