# AI-VIDEO Agentic Production Harness P0 Product Reframe Implementation Plan

> **For agentic workers:** 实施本 plan 时，REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans。按 Task 顺序执行，并使用 checkbox (`- [ ]`) 跟踪进度。

**Goal:** 在不修改 runtime code、schema、CLI、dependency 或外部 integration 的前提下，把 v0.2 的 product contract 从 provider-centric video runtime 迁移为 Codex-driven AI Video / AI Comic Production Harness，并保留 Legacy/P1 provenance。

**Architecture:** P0 只迁移文档 control plane：new spec 拥有 product target，roadmap 拥有 phase dependency，runtime baseline 拥有 current truth，`AGENTS.md` 与 contract matrix 拥有执行 gate，`README.md` 只链接并区分当前行为与未来方向。旧 spec 和 P1 plan 不删除；前者标记 superseded，后者标记 local implementation record。

**Tech Stack:** Markdown、Git、`rg`、`pytest`；不修改 `src/**`、`tests/**`、`pyproject.toml`、workflow、config、`runs/**`，不安装 plugin/runtime dependency，不调用 network Provider。

Status: Executed under the user's 2026-08-09 documentation-only reframe authorization. Checkbox state records the completed P0 migration; it does not authorize P2+ runtime work.

---

## Scope and Authority

P0 owns only these files：

- `AGENTS.md`
- `README.md`
- `docs/agent-primary-contract-matrix.md`
- `docs/v0.2-runtime-baseline.md`
- `docs/v0.2-agentic-production-roadmap.md`
- `docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md`
- `docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md`
- `docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md`
- `docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p0-product-reframe.md`

P0 明确禁止：

- 修改 `src/**` 或 `tests/**`；
- 修改 package version、dependency、CLI、Manifest schema 或 artifact layout；
- 安装 HyperFrames/Remotion/ElevenLabs/Captions；
- 创建 renderer project；
- 调用真实 ComfyUI 或任何 remote/paid API；
- 实现 ProductionProject、Asset Registry、Timeline、Audio、Caption 或 dependency graph；
- 删除 Legacy Wan path、旧 spec 或旧 P1 test design。

## File Ownership and Old-Path Decisions

| File | P0 Responsibility | Old-Path Decision |
| --- | --- | --- |
| `docs/v0.2-runtime-baseline.md` | 记录 current local main runtime truth 和 remaining debt | Replace stale pre-P1 gap claims; keep path as canonical current audit |
| New v0.2 spec | 定义 Agent-first product/domain/owner/acceptance | Create; becomes target contract |
| Old v0.2 spec | 保存 provider-centric historical design | Mark superseded; do not rewrite or delete body |
| `docs/v0.2-agentic-production-roadmap.md` | 定义 phase dependencies、parallel/gates | Create; no implementation details beyond slice boundary |
| Old P1 plan | 保存 exact tests/patch design 和 commit provenance | Mark implemented local Legacy stabilization record |
| `AGENTS.md` | Durable current/planned boundary and decision gates | Replace old product identity only; preserve Legacy module rules |
| Contract matrix | Operational gates and single-owner rules | Replace old phase ordering; preserve current validation matrix |
| `README.md` | Current runtime truth and roadmap pointers | Do not describe planned integrations as implemented |

### Task 1: Verify Git and Runtime Truth

**Files:**
- Read: `AGENTS.md`
- Read: `README.md`
- Read: `docs/agent-primary-contract-matrix.md`
- Read: `docs/v0.2-runtime-baseline.md`
- Read: `src/ai_video/models.py`
- Read: `src/ai_video/pipeline.py`
- Read: `src/ai_video/manifest.py`
- Read: `src/ai_video/workflow_renderer.py`
- Read: `src/ai_video/ffmpeg_tools.py`
- Read: `src/ai_video_mcp/**`
- Read: `tests/test_manifest.py`
- Read: `tests/test_pipeline.py`
- Read: `tests/test_resume_e2e.py`

- [x] **Step 1: Record the exact Git state**

运行：

```bash
git status --short --branch
git log --oneline -20
```

预期：审计开始时 working tree clean；local `main` 显示 `ahead 4`，top four commits 是 `abe029c`、`aad2687`、`ed938f2`、`6eb895a` 对应的 P1 implementation。

- [x] **Step 2: Run the complete no-network baseline**

运行：

```bash
python -m pytest -q
```

预期：`92 passed, 1 skipped`；不调用真实 ComfyUI 或 external Provider。

- [x] **Step 3: Reconcile the three named P1 defects against source**

运行：

```bash
rg -n "_persist_terminal_failure|_shot_is_current|_all_resume_shots_current|_ArtifactPromotion|delivery_fps" src/ai_video/pipeline.py
rg -n "ShotRecord.failed|successful_shot_is_valid|mark_shots_stale" src/ai_video/manifest.py
rg -n "generation_fps" src/ai_video/workflow_renderer.py
```

预期：terminal failure persistence、direct chain invalidation、Legacy FPS semantics 和 artifact rollback 均存在；不得继续把它们列为 current gaps。

- [x] **Step 4: Record remaining real debt**

把以下 evidence 写入 baseline，而不是扩大 P1：

```text
resume fast path does not validate normalized/final artifacts
config/template/binding and several input hashes are not resume validity inputs
in-flight job handle is not crash-safe persisted
final output has no hash or power-loss journal
word timestamp output contract is incomplete
QA is not visual-strategy-aware
```

### Task 2: Replace the Stale Runtime Baseline

**Files:**
- Modify: `docs/v0.2-runtime-baseline.md`

- [x] **Step 1: Separate implemented, planned and debt sections**

文档必须包含 exact headings：

```markdown
## Current Product Contract
## Verified Implemented Behavior
## Planned but Not Implemented
## Remaining Runtime Defects and Debt
## Retained Legacy Design
## Superseded Product Assumptions
## Evidence Commands
## Non-Authorization
```

- [x] **Step 2: Correct local-only wording**

使用以下 contract：

```text
local-first and default-local ComfyUI
non-local ComfyUI requires allow_non_local: true
no cloud Provider exists
```

不得写成“代码绝对禁止 non-local ComfyUI”。

- [x] **Step 3: Add current no-network evidence**

写入：

```text
Current no-network result: 92 passed, 1 skipped.
```

并明确 skipped test 是 optional Whisper surface，不代表 core test failure。

### Task 3: Preserve Historical Specs and Plans

**Files:**
- Modify: `docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md`
- Modify: `docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md`

- [x] **Step 1: Mark the old spec superseded without deleting it**

旧 spec header 必须包含：

```markdown
Status: Superseded on 2026-08-09 after local P1 legacy-runtime stabilization; retained as a historical provider-centric design and safety-contract source.
Successor Spec: `docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md`
```

并说明 old Current State 是 2026-08-08 snapshot，P1 已在 local main 实现，P2+ 仍未实现。

- [x] **Step 2: Reclassify the old P1 plan precisely**

P1 header 必须包含：

```markdown
Status: Implemented on local `main` in commits `abe029c`, `aad2687`, `ed938f2`, and `6eb895a`; retained as a reusable Legacy stabilization record. Local `main` is ahead of `origin/main`, so GitHub release/integration is not implied.
```

保留 P1 的 test design、acceptance 和 rollback 内容；不得把 plan 删除或误写为 unimplemented parked work。

- [x] **Step 3: Verify provenance links**

运行：

```bash
rg -n "Superseded|Successor Spec|Implemented on local|origin/main" \
  docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md \
  docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md
```

预期：四个 provenance terms 都出现，且旧文件 body 仍存在。

### Task 4: Write the Agentic Production Harness Spec

**Files:**
- Create: `docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md`

- [x] **Step 1: Define the product and non-goals**

Spec 必须把 product decision 写成：

```text
Codex = Production Agent
AI-VIDEO = durable Production Harness
Video Provider = optional visual asset generator
ResolvedTimeline = canonical composition state
```

明确禁止 `Shot = video prompt`、无 durable state 的 plugin chain 和 double renderer。

- [x] **Step 2: Define the core domains**

Spec 必须定义：

```text
ProductionProject
Story
Characters
Scenes
Storyboard
Shots
AssetRegistry
DependencyGraph
CompositionSpec
ResolvedTimeline
Reviews
Repairs
Renders
```

Shot strategies 必须完整列出：

```text
static_image
image_motion
motion_graphics
generated_video
existing_video
hybrid
```

- [x] **Step 3: Lock renderer ownership**

写入 single-owner decision：

```text
AI-VIDEO ResolvedTimeline owns order and timing.
HyperFrames is the default renderer target.
Remotion is an optional exclusive adapter.
HyperFrames and Remotion must never render the same attempt in sequence.
```

- [x] **Step 4: Lock Audio and Caption boundaries**

写入：

```text
ElevenLabs is an opt-in Voice Asset Provider candidate, not a core dependency.
CaptionTrack owns text and timing.
The selected renderer owns caption layout and drawing.
Captions.ai burned-in video is not the default caption data/render path.
```

- [x] **Step 5: Define dependency and repair contracts**

Spec 必须提供 mutation matrix，至少覆盖 caption style、voice script、character reference、one image、Hero video、BGM、delivery profile、renderer version 和 QA policy。

- [x] **Step 6: Define acceptance and Definition of Done**

Acceptance 必须要求 no-Video-Provider end-to-end path、selective rebuild、final hash、fresh review receipt、Legacy compatibility 和 paid-call submit-count-zero safety gate。

### Task 5: Create the Phase Dependency Map

**Files:**
- Create: `docs/v0.2-agentic-production-roadmap.md`

- [x] **Step 1: Define phase order**

使用以下 phase ownership：

```text
P0 Product Reframe and Contract Migration
P1 Legacy Runtime Stabilization
P2 Production Project Core
P3 Deterministic Composition and HyperFrames Adapter
P4 Voice and Captions
P5 Dependency Graph and Selective Rebuild
P6 Codex Review and Repair Harness
P7 Image Asset Generation
P8 Optional Generated-Video Providers
P9 Episode and Production Hardening
```

- [x] **Step 2: Record parallel work**

P3、P4、P7 在 P2 contract 稳定后可并行；P5 必须消费 P2/P3/P4 contracts；P6 依赖 P3/P5；P8 不得阻塞 Base AI Comic E2E。

- [x] **Step 3: Add mandatory gates**

Roadmap 必须包含：

```text
Integration Base Gate
Renderer Gate
Paid Provider Gate
Base AI Comic Gate
```

Integration Base Gate 必须明确 local `main` ahead 4 的 P1 disposition，避免 P2 从错误 base 开始。

### Task 6: Synchronize Durable Contracts and README

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/agent-primary-contract-matrix.md`
- Modify: `README.md`

- [x] **Step 1: Update AGENTS.md product boundary**

保留 Legacy module boundaries、CLI、Manifest 和 test rules；只增加：

```text
Codex is the Production Agent.
The repository does not implement another general Agent runtime.
The base v0.2 path works without a Video Provider.
Wan remains an optional generated_video capability.
```

- [x] **Step 2: Update the contract matrix gates**

增加 `Agent Boundary` 和 `Renderer Ownership`，并把 old provider-first phase gates 替换成 new P2-P8 order。不得改变 current CLI/config/pipeline validation commands。

- [x] **Step 3: Keep README honest**

README 只允许声明：

```text
current local-first 0.1.x runtime
P1 fixes exist on local main
new v0.2 direction is planning-only
HyperFrames/Remotion/ElevenLabs/Captions are not implemented
```

更新 new spec、roadmap、P0 plan、historical spec 和 P1 record links。

### Task 7: Verify Scope, Consistency and Commit

**Files:**
- Verify: all P0-owned files

- [x] **Step 1: Verify required spec sections**

运行：

```bash
rg -n "^# (1\. Problem|2\. Product Decision|4\. Goals|5\. Non-Goals|7\. Architecture|9\. Production Domain Model|10\. Asset Model|11\. Shot Visual Strategy|12\. Audio Model|13\. Caption Model|14\. Timeline and Composition|15\. Manifest and Provenance|16\. Dependency and Invalidation|17\. Codex Agent Operating Contract|18\. QA and Repair|19\. Cost, Security and Egress Boundaries|20\. Legacy Compatibility and Migration|21\. Open-Source Reuse Policy|22\. Phased Rollout|23\. Acceptance Criteria|24\. Definition of Done)" \
  docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md
```

预期：每个 required section 恰有对应 heading。

- [x] **Step 2: Scan for false implementation claims**

运行：

```bash
rg -n "implemented|已实现|available today|当前支持" \
  README.md AGENTS.md docs/v0.2-runtime-baseline.md \
  docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md
```

逐条确认每个 claim 指向 current Legacy/P1 evidence；HyperFrames、Remotion、ElevenLabs、Captions、Audio、v2 schema 和 cloud Provider 只出现在 planned/not-implemented context。

- [x] **Step 3: Verify no runtime file changed**

运行：

```bash
git diff --name-only
git status --short
git diff --check
```

预期：`git diff --name-only` 与 `git status --short` 合并后的 changed paths 只属于 P0 file list；`git diff --check` 无输出并退出 `0`。

- [x] **Step 4: Re-run the no-network suite**

运行：

```bash
python -m pytest -q
```

预期：`92 passed, 1 skipped`。

- [x] **Step 5: Commit the documentation migration**

运行：

```bash
git add AGENTS.md README.md docs/agent-primary-contract-matrix.md \
  docs/v0.2-runtime-baseline.md docs/v0.2-agentic-production-roadmap.md \
  docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md \
  docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md \
  docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md \
  docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p0-product-reframe.md
git diff --cached --check
git diff --cached --name-only
git commit -m "docs: reframe v0.2 as agentic production harness"
```

预期：cached diff check 无输出，cached names 只包含以上九个 files；commit 后 local `main` 相对 `origin/main` 的 ahead count 从 4 增加为 5。

## Acceptance Criteria

P0 只有在以下全部成立时完成：

1. New v0.2 spec 成为唯一 active product target。
2. Old v0.2 spec 保留并清楚标记 superseded。
3. Old P1 plan 保留 exact test design，并准确标记 local implementation/GitHub state。
4. Current baseline 不再重复已经修复的 P1 defects。
5. Spec 明确 HyperFrames default、Remotion optional-exclusive、CaptionTrack owner 和 ElevenLabs candidate role。
6. Spec 明确 base path 不需要 Video Provider。
7. Roadmap 明确 phase dependency、parallel work 和 mandatory gates。
8. `AGENTS.md`、contract matrix 和 README 指向同一 product direction。
9. README 没有把 planned capability 写成 runtime truth。
10. `src/**`、`tests/**`、dependency、CLI、Manifest schema 和 artifact layout 没有变化。
11. Full no-network suite 通过。
12. Documentation migration 已作为单一 scoped commit 保存。

## Rollback

P0 没有 runtime/data migration。Rollback 是一个 documentation-only Git revert：

```bash
git revert <p0-documentation-commit>
```

Rollback 不影响 local P1 的四个 runtime commits。若只撤销某个文档会让 active/superseded pointers 不一致，因此必须整体 revert P0 commit，不做 partial rollback。

## Next Plan Boundary

P0 完成后，先决定 local P1 commits 如何进入 shared Git base。随后创建独立 `P2 Production Project Core Implementation Plan`；P2 不得包含 renderer、Audio Provider、Caption Provider、dependency graph、QA repair 或 cloud Provider implementation。
