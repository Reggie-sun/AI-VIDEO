# AI-VIDEO Agentic Production Harness P3 Deterministic Composition and HyperFrames Adapter Implementation Plan

> **For agentic workers:** 实施本 plan 时，REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans。按 Task 顺序执行，并使用 checkbox (`- [ ]`) 跟踪进度。

**Goal:** 在 accepted P2A state commit protocol 之上，实现 renderer-neutral `CompositionSpec`、唯一 order/timing owner `ResolvedTimeline`、exclusive HyperFrames adapter、renderer source receipt 和 render receipt，并以 image-only silent fixture 证明 deterministic composition。

**Architecture:** `src/ai_video/production/models.py` 继续拥有 v2 schema，新的 `composition.py` 只负责从显式 Shot/asset bindings 解析整数 frame/sample boundaries 和 composition fingerprint，新的 `hyperframes.py` 只把已解析 timeline materialize 成受审计的 local source 并通过单一 HyperFrames CLI 执行。所有 durable write、active pointer switch、failed/succeeded attempt commit 都必须委托 accepted P2A canonical state committer；P3 不新建第二套 Manifest、timeline、renderer control plane，也不触碰 Legacy runtime。

**Tech Stack:** Python 3.11+、Pydantic v2、`Decimal`、`hashlib`、现有 `AiVideoError`/`ErrorCode`、现有 `probe_clip()`、pytest fake runner、exact `hyperframes@0.7.103`、Node.js `>=22`、FFmpeg 和经 Renderer Gate 验证的 exact Chromium revision。默认 CI 不调用 Node、Chrome、network 或真实 render。

---

Status: P3 runtime execution and the full Renderer Gate were explicitly authorized by the user on 2026-08-09. The authorization covers the versioned render-state snapshot approach, exact `hyperframes@0.7.103` install, the matching Chromium install required by the verified package source, and an OS-egress-contained lint/check/preview/render spike. It does not authorize Remotion, Audio/Caption, P5+, Provider, new CLI, Legacy schema/layout changes or push/release.

## Problem Boundary

P3 的唯一 production path 是：

```text
accepted P2 LoadedProductionProject
+ explicit CompositionSpec
+ exact Asset Registry IDs, hashes and resolved contained paths
+ accepted P2A `PreparedArtifact` durable bytes owner
+ authorized `RenderStateSnapshot` lifecycle inside `ProductionStateCommitter`
        |
        v
pure resolve_composition()
        |
        v
ResolvedTimeline (only order/timing truth)
        |
        v
exclusive renderer selection receipt: hyperframes
        |
        v
deterministic local HyperFrames source + source receipt
        |
        v
lint -> check -> render through one pinned tool
        |
        v
measured output + render receipt
        |
        v
P2A-owned atomic activation of one `RenderStateSnapshotPointer`
```

本 slice 只验收已有 registered local image/composition assets 的 silent composition。它不生成素材，不引入 voice/caption/audio tracks，不实现 dependency invalidation，也不通过新 CLI 暴露 v2 runtime。

## Hard Prerequisites

P3 runtime implementation 的三个前置/gate 均已在 2026-08-09 获得本 plan 所需的明确决策；Task 0 仍必须重新验证实际 package/source/runtime 事实：

1. **Accepted P2A (satisfied):** local `main` at `a42583f` 已包含 independently accepted P2A plan/implementation/tests。真实 public surface 是 `ProductionManifest`、`ProductionStateCommitter`、`PreparedArtifact`、`StateCommitRequest`、`prepare_project_registry_commit()` 和 explicit `recover_production_state()`；`state_commit.py` 是唯一 v2 writer/recovery owner。
2. **Renderer Gate (authorized, verify before install):** 用户授权 exact `hyperframes@0.7.103`，npm integrity 必须等于 `sha512-+E+CXuBiHgd6Rae/BltrErJGr0PtC/AL5uHXm6ZN77ziERtIFJvqaJveWDmJ4PH6UEJ/lf3Cqxuv8GpATt4Ljw==`。如 exact published source 仍确认 Chrome Headless Shell `152.0.7928.2`，则在 live spike 前预安装该 exact revision 并通过 `HYPERFRAMES_BROWSER_PATH` 显式指定；dependency/browser 安装是唯一允许 external network 的阶段。
3. **Render State Contract (authorized):** 采用一个 versioned immutable `RenderStateSnapshot`，并由 `ProductionManifest.active_render_state` 单指针选择。`ProductionStateCommitter` 增加真实 `begin_render_attempt()`、`record_render_failure()`、`activate_render_state()` 和纯 path API `render_attempt_paths()`，仍是唯一 writer/activation/recovery owner。精确 schema、layout、request、replay 和 crash contract 在 Task 1 与 dedicated Task 5 中定义。

执行前还需确认没有其他 writer 拥有这些目标文件。若 current tree 有 unrelated uncommitted changes，使用独立 branch/worktree；不要在 dirty tree 上写入。

## Current Renderer Gate Evidence

2026-08-09 的只读核对结论：

| Surface | Verified Current Fact | Planning Consequence |
| --- | --- | --- |
| Codex plugin | `codex plugin list` 显示 `hyperframes@openai-curated` 为 `not installed`，因此也未 enabled | marketplace materialization 不是 runtime readiness 证据；本次使用已授权的 project-local exact npm pin，不依赖 plugin installed state |
| Cached skill bundle | 本机 marketplace materialized bundle 是 plugin `0.1.2`，包含 skills/CLI guidance | bundle 可用于了解能力，但不能作为 CLI installed/version proof；其 `npx` 和 `inspect` guidance 不是本 plan 的 pinned runtime contract |
| PATH/global npm | `command -v hyperframes` 无结果；`npm list -g --depth=0 hyperframes` 为空 | adapter 不得假设 PATH binary |
| Published CLI | official npm metadata 的 `hyperframes` latest 为 `0.7.103`，`gitHead=adb13ce125a3ed1d71919ce98c7306ad18ce6677`，Apache-2.0，Node `>=22` | Renderer Gate 通过时只允许 exact pin `0.7.103`；禁止 `latest`/caret/range；GitHub `main` 和 npm publish 一度存在 `0.7.102`/`0.7.103` 版本漂移，实施必须以 exact published package + integrity 为准 |
| Local Node/npm | Node `v22.21.0`，npm `11.6.3` | 满足 current Node lower bound，但 implementation day 仍需重跑 |
| Local FFmpeg | PATH 存在 `/home/reggie/miniconda3/bin/ffmpeg` | 只证明 binary 存在；codec、Chrome 和 render parity 未验证 |
| Local Chrome/cache | system Chrome `149.0.7827.53` 和 Puppeteer Chrome for Testing `146.0.7680.153` 存在；没有 HyperFrames-managed browser cache | published `0.7.103` source pins Chrome Headless Shell `152.0.7928.2`；当前本机证据不满足 pinned-browser parity，不能据此运行 live spike |
| CLI surface | exact published source 注册 `lint`、`check`、deprecated `inspect`、`preview` 和 `render`；official docs 将 `check --json` 定义为新 browser gate | automated adapter 使用 `lint --json` + `check --json`；`inspect` 只作为 deprecated compatibility fact 记录，不成为新 receipt contract；preview/render 只在 live spike gate 执行 |
| Offline/network behavior | `HYPERFRAMES_NO_TELEMETRY=1`/`DO_NOT_TRACK=1` 可禁 telemetry，`HYPERFRAMES_NO_AUTO_INSTALL=1` 可禁 package background installer，但 `HYPERFRAMES_NO_UPDATE_CHECK=1` 不会阻止 `checkForUpdate()` 本身访问 npm registry；只有 root `--json` path 跳过该 background block。browser manager 仍可 auto-download Chrome，Linux ARM64 路径还可尝试 `apt-get` | 不得声称现有 env 已使 CLI offline-safe。live spike 必须使用 OS-level egress denial/observability 和经授权、预先安装、显式指定的 `HYPERFRAMES_BROWSER_PATH`，并记录 CLI/Node/FFmpeg/browser exact versions；source audit 还必须拒绝 remote URLs/fetch |

Primary sources：

- [HyperFrames repository and runtime overview](https://github.com/heygen-com/hyperframes)
- [HyperFrames 0.7.103 release commit](https://github.com/heygen-com/hyperframes/commit/adb13ce125a3ed1d71919ce98c7306ad18ce6677)
- [HyperFrames 0.7.103 CLI package metadata](https://github.com/heygen-com/hyperframes/blob/adb13ce125a3ed1d71919ce98c7306ad18ce6677/packages/cli/package.json)
- [HyperFrames CLI commands](https://github.com/heygen-com/hyperframes/blob/main/packages/cli/README.md)
- [HyperFrames official CLI documentation](https://hyperframes.heygen.com/packages/cli)
- [HyperFrames Apache-2.0 license](https://github.com/heygen-com/hyperframes/blob/main/LICENSE)
- [HyperFrames command registration and executable-boundary error handling](https://github.com/heygen-com/hyperframes/blob/adb13ce125a3ed1d71919ce98c7306ad18ce6677/packages/cli/src/cli.ts)
- [HyperFrames telemetry opt-out](https://github.com/heygen-com/hyperframes/blob/adb13ce125a3ed1d71919ce98c7306ad18ce6677/packages/cli/src/commands/telemetry.ts)
- [HyperFrames update-check behavior](https://github.com/heygen-com/hyperframes/blob/adb13ce125a3ed1d71919ce98c7306ad18ce6677/packages/cli/src/utils/updateCheck.ts)
- [HyperFrames browser resolution and download behavior](https://github.com/heygen-com/hyperframes/blob/adb13ce125a3ed1d71919ce98c7306ad18ce6677/packages/cli/src/browser/manager.ts)

不得把 cached skill 中的 `--docker` 描述升级为本项目的 byte-identical guarantee。P3 只要求在相同 `ResolvedTimeline`、renderer source、asset hashes 和 pinned tool/runtime 下得到 frame-equivalent output；container metadata/encoder behavior 没有独立契约时，不承诺 byte-identical MP4。

## Open-Source Fusion Decision

本 plan 依照 `github-oss-fusion` 只融合最小结构、测试和错误处理思想，不复制 external implementation：

| Repository | Inspected | Fused | Rejected or Deferred |
| --- | --- | --- | --- |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | README、CLI metadata、license、CLI source、CLI tests | exact published version/integrity pin、machine-readable lint/check、single executable failure boundary、source-first renderer adapter、phase-focused tests | 不复制 TypeScript renderer internals；不假设未验证的 auto-install opt-out；不采用 auto-update、telemetry、cloud/Lambda、TTS/transcribe |
| [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) | README、AGPL license、`lib/hyperframes_style_bridge.py`、tests tree | 一个 production decision 锁定一个 `render_runtime`、同一 upstream production contract 由 adapter 消费而不是 fork | AGPL code 不复制；不引入其 tool registry、pipelines、provider graph 或 dual renderer runtime |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | README、special license、renderer source/tests tree | 只保留“renderer 是可替换 adapter，而不是 timeline owner”的负面边界 | P3 不安装、不实现、不调用 Remotion；special license 也不进入 HyperFrames license judgment |

## Canonical Ownership

| Contract | Single Owner | Adapter or Non-Owner Rule |
| --- | --- | --- |
| v2 P3 schema | `src/ai_video/production/models.py` | HyperFrames HTML/JSON 不拥有 schema |
| semantic edit intent | `CompositionSpec` | renderer 不补 Shot order、asset selection 或 transition intent |
| order/timing/layers | `ResolvedTimeline` produced by `composition.py` | HyperFrames source、directory order、mtime、filename、ffmpeg concat list 都不是 truth source |
| deterministic composition fingerprint | `composition.py::timeline_fingerprint()` | receipt 只引用 fingerprint，不重新计算另一种 desired hash |
| renderer selection | one immutable `RendererSelectionReceipt` per attempt | `RendererPolicy.default_preference` 只是 policy input，不是 mutable attempt state |
| renderer source | `hyperframes.py::materialize_hyperframes_source()` output + `RendererSourceReceipt` | source 必须完全由 timeline/assets materialize，不能 scan filesystem 决策 |
| render execution | `HyperFramesAdapter` | 一个 attempt 只能调用一个 renderer，禁止 fallback 或 double render |
| durable project/registry transaction | `state_commit.py::ProductionStateCommitter.commit(StateCommitRequest)` | 现有 P2A project/registry pair、request 与 replay 语义保持不变；P3 render operation 不借用或改写该 pair |
| render attempt lifecycle | `ProductionStateCommitter.begin_render_attempt()` / `record_render_failure()` / `activate_render_state()` | `record_render_failure()` 只拥有 R+1 begun、candidate-prepared 之前的 ordinary failure；`activate_render_state()` 从 R+2 candidate-prepared durable authority 开始独占 final activation/failure ownership。它们不是 `commit()` alias wrapper；不得增加第二 writer 或 Manifest |
| timeline/source/render activation | immutable `RenderStateSnapshot` selected by `ProductionManifest.active_render_state` | Manifest 只额外切换这一个 render pointer；snapshot 固定 exact timeline/source receipt/render receipt/output identities |
| render scratch allocation | pure validated `ProductionStateCommitter.render_attempt_paths()` | 只返回 `state/render/attempts/<safe-attempt-id>/` 内的 attempt-owned source/output staging path，不创建目录、不切指针 |
| measured render evidence | `RenderReceipt` built from output hash + `probe_clip()` | console text 不是 final status |

## Old Path Decisions

- 不修改或复用 `src/ai_video/workflow_renderer.py` 作为 composition renderer；它继续只拥有 Legacy Comfy workflow template/binding pure render。
- 不修改 `src/ai_video/pipeline.py` 作为 v2 timeline owner；Legacy ordered Shot chaining 保持原状。
- 不把 `src/ai_video/ffmpeg_tools.py::stitch_clips()` 当作 canonical renderer；P3 只复用 `probe_clip()` 验证 HyperFrames output。
- 不修改 `src/ai_video/manifest.py` 或 Legacy `RunManifest`。
- 不让 `ProductionProject.renderer_policy.default_preference` 静默选择未实现 adapter；requested/default 为 `remotion` 时必须 typed-fail。
- 不在 HyperFrames failure 后调用 Remotion、ffmpeg stitch 或任何 alternate final-render path。
- 不扫描 project directories、glob、mtime 或 lexicographic filename 来决定 Shot/layer order。
- 不把 arbitrary Codex-authored HTML 直接视为 accepted source；source 必须通过 timeline materialization、static audit、hash、lint 和 `check`。

## Unchanged Contracts

- Legacy public CLI 仍只有 `ai-video validate`、`ai-video run`、`ai-video resume`。
- Legacy default-local ComfyUI、Manifest v1、resume、flat `runs/<run_id>/` layout 和 current workflow loader/renderer 均不变。
- P2 `ProductionProject`、creative artifact、Asset Registry、path containment、read-only loading 和 content hashes 不被重定义。
- `validate` 保持无副作用，不安装 tool、不创建 v2 state、不联网或 render。
- P3 不实现 Audio/Caption domain、P5 dependency graph/desired-applied lifecycle、QA/repair、Provider、cloud、paid API、new CLI 或 Legacy schema/layout migration。
- 本次授权仅允许 P3 `ProductionManifest` 2.0 -> 2.1 兼容扩展、`state/render/` canonical layout、exact dependency/browser install 和 egress-contained Renderer Gate；不扩展到其他 manifest/layout/runtime surface。

## Contract Details

P3 contract 必须显式包含：

- `CompositionSpec`: ordered `shot_ids`、exact asset bindings、visual layer/edit intent、trim、fixed-point transform、fixed-point opacity、z-order、transition、delivery profile 和 requested renderer。
- `ResolvedTimeline`: width/height/FPS/codec profile、sample rate、integer `start_frame`/`duration_frames`、integer `start_sample`/`duration_samples`、asset ID/hash/materialized path、trim、transform、opacity、z-order、transition、total frames/samples、renderer kind/version 和 `composition_fingerprint`。
- duration resolution: P3 silent fixture 只接受 `DurationPolicy.mode == "fixed"`；使用 `Decimal(str(seconds))`，`ROUND_CEILING` 到整数 frame，绝不使用 binary float 累加。
- sample boundaries: `start_sample = floor(start_frame * sample_rate / fps)`，`end_sample = floor(end_frame * sample_rate / fps)`，duration 是两者之差。P3 只建立 timebase，不创建 audio track。
- transition resolution: `cut` 为 0 frame；`crossfade` 使用 explicit integer `duration_frames`，后一个 Shot 的 `start_frame = previous_end_frame - duration_frames`，并验证 overlap 小于两个相邻 Shot duration。
- composition fingerprint: 对 fully resolved timeline projection 做 stable JSON + SHA-256，排除 self hash、receipt timestamp、absolute staging path 和 wall-clock data。
- source receipt: renderer kind/version、timeline fingerprint、source SHA-256、exact asset bindings/hashes、lint/check command identity、exit status 和 output evidence hashes。
- render receipt: attempt ID、renderer/tool version、timeline fingerprint、source hash、asset hashes、output hash/size、measured width/height/FPS/duration/codec 和 result status。

### Manifest and Render-State Migration

- `ProductionManifest.schema_version` 接受 `"2.0"` 和 `"2.1"`。`2.0` 只允许 `active_render_state=None` 且 `attempts` 中不得有 render operation；首次 `begin_render_attempt()` 用一次 durable Manifest replace 迁移为 `2.1`。迁移不 backfill、rewrite 或 reseal 任何 immutable P2/P2A project/registry snapshot。
- `2.1` 增加 `active_render_state: RenderStateSnapshotPointer | None = None`。P2 `load_production_project()` 保持 read-only/no-network，同时接受 2.0/2.1；当 pointer 不为 `None` 时必须校验其 contained canonical path、file hash、snapshot semantic identity 与 cross references，不激活、不修复。
- `RenderStateSnapshotPointer` 含 `path`、`revision`、`content_hash`、`file_sha256`；canonical path 是 `state/render/states/<full-content-hash>.json`，禁止 alias、`current` symlink 和 truncated hash filename。
- `RenderArtifactPointer` 含 `path`、`revision`、`content_hash`、`file_sha256`，用于 exact `ResolvedTimeline`、`RendererSourceReceipt` 和 `RenderReceipt`。`RenderOutputPointer` 含 exact `path`、`file_sha256`、`size_bytes`。
- immutable sealed `RenderStateSnapshot(VersionedArtifact)` 含 `attempt_id`、exact `RendererSelectionReceipt`、duplicated renderer/timeline/source/asset identities、`timeline`、`source_receipt`、`render_receipt`、`output`。model validator 校验 embedded selection，reader/committer 加载 exact pointers 后 cross-validate 同一 attempt ID、renderer kind/version、timeline fingerprint、source hash、ordered asset hashes 和 output path/hash/size；任一 mixed/tampered identity 失败。

### Canonical Durable Layout

```text
state/render/timelines/<full-content-hash>.json
state/render/source-receipts/<full-content-hash>.json
state/render/render-receipts/<full-content-hash>.json
state/render/states/<full-content-hash>.json
state/render/outputs/<full-file-sha256>.mp4
state/render/attempts/<safe-attempt-id>/source/
state/render/attempts/<safe-attempt-id>/output/render.mp4
```

`production/paths.py` 是上述 canonical immutable paths 与 attempt scratch containment 的唯一 validator/constructor。immutable filenames 使用 full hash；source/output staging 只能在该 attempt directory 内。不使用 `runs/<run_id>/`、Legacy Manifest、symlink、alias、directory scan 或 mutable `current` path。

## Exact File Map

P3 implementation may create or modify only the following runtime files after every prerequisite is accepted:

Create:

- `src/ai_video/production/composition.py`
- `src/ai_video/production/hyperframes.py`
- `tests/test_production_composition.py`
- `tests/test_production_hyperframes.py`
- `tests/fixtures/hyperframes/silent_image/timeline.json`
- `tests/fixtures/hyperframes/silent_image/source/index.html`
- `tests/fixtures/hyperframes/silent_image/assets/hero.svg`
- `package.json`
- `package-lock.json`

Modify:

- `src/ai_video/production/models.py`
- `src/ai_video/production/paths.py`
- `src/ai_video/production/project.py`
- `src/ai_video/production/state_commit.py`
- `src/ai_video/production/__init__.py`
- `src/ai_video/errors.py`
- `tests/test_production_models.py`
- `tests/test_production_project.py`
- `tests/test_production_state_commit.py`
- `tests/test_production_state_recovery.py`
- `tests/helpers/p2a_crash_worker.py`
- `tests/production_project_factory.py`
- `.gitignore` only to add `node_modules/` and local HyperFrames scratch output
- `README.md`
- `docs/v0.2-runtime-baseline.md`
- `docs/v0.2-agentic-production-roadmap.md`
- `docs/agent-primary-contract-matrix.md`

`state_commit.py` 仍是 P2A/P3 唯一 writer/recovery owner；`paths.py` 只构造和验证 path，`project.py` 只读并验证 2.0/2.1 Manifest-selected state。不创建 `RenderAttemptCommitter`、alias wrapper、第二 Manifest 或 renderer-owned activation helper。runtime file count 仅增加 `composition.py` 和 `hyperframes.py`。

Do not modify:

- `src/ai_video/{cli,config,models,manifest,pipeline,workflow_loader,workflow_renderer,comfy_client}.py`
- `src/ai_video/ffmpeg_tools.py`
- `tests/test_{cli,config,manifest,pipeline,resume_e2e,workflow_loader,workflow_renderer}.py`
- `configs/**`、`workflows/**`、`runs/**`、`.workflow/**`

## Test and Commit Map

| Task | RED Focus | Owner | Commit |
| --- | --- | --- | --- |
| 0 | accepted P2A fact check + authorized pinned Renderer Gate | prerequisites/dependency/browser lock | `build: pin hyperframes renderer tool` |
| 1 | strict composition/timeline/receipt/render-state schema + 2.0/2.1 model compatibility | `models.py` | `feat: add composition and render contracts` |
| 2 | exact frame/sample resolution and fingerprint | `composition.py` | `feat: resolve deterministic production timelines` |
| 3 | timeline-only source materialization into validated attempt paths | `hyperframes.py` source layer | `feat: materialize audited hyperframes sources` |
| 4 | fake lint/check/render and typed receipts | `HyperFramesAdapter` orchestration boundary | `feat: add hyperframes renderer adapter` |
| 5 | 2.0/2.1 read + orchestration + begin/failure/candidate-prepared/final activation/replay/recovery | `project.py` + `hyperframes.py` + `ProductionStateCommitter` + P2A tests | `feat: commit production render state` |
| 6 | authorized live spike + focused/P2A/Legacy/full regression proof | verification | no commit unless correction is required |
| 7 | docs from completed verification evidence | docs | `docs: document p3 composition runtime` |
| 8 | final independent review + branch truth | review/verification | no commit unless correction is required |

### Task 0: Pass P2A and Renderer Gates

**Files:**
- Verify: accepted P2A plan/source/tests/docs
- Create under the recorded authorization: `package.json`
- Create under the recorded authorization: `package-lock.json`
- Modify under the recorded authorization: `.gitignore`

- [ ] **Step 1: Verify accepted P2A exists**

Run:

```bash
git rev-parse HEAD
rg -n "ProductionStateCommitter|PreparedArtifact|StateCommitRequest|prepare_project_registry_commit|recover_production_state" \
  src/ai_video/production/__init__.py src/ai_video/production/state_commit.py \
  tests/test_production_state_commit.py tests/test_production_state_recovery.py
test -f src/ai_video/production/state_commit.py
test -f tests/test_production_state_commit.py
test -f tests/test_production_state_recovery.py
python -m pytest \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
python -m pytest \
  tests/test_production_models.py \
  tests/test_production_validation.py \
  tests/test_production_registry.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
```

Expected on reconciled local `main`: HEAD includes `a42583f`; accepted P2A plan and canonical owner exist at the listed paths; focused state commit/recovery result is `136 passed` and focused P2/P2A result is `286 passed`. `ProductionStateCommitter.prepare_artifact()` and `StateCommitRequest.artifacts` prove generic contained-byte carriage, while `ProductionManifest` and `StateCommitRequest.next_project`/`next_registry` prove that active selection remains project/registry-only. If these real symbols or invariants drift, revise and re-review this P3 plan; do not create aliases merely to satisfy old checks.

- [ ] **Step 2: Recheck official renderer facts**

Run read-only commands:

```bash
codex plugin list | rg '^hyperframes@'
command -v hyperframes || true
npm view hyperframes version engines license dist-tags repository gitHead dist.integrity --json
node --version
npm --version
ffmpeg -version | sed -n '1,3p'
google-chrome --version || true
```

Expected: evidence is recorded with date. Current planning evidence is `hyperframes@0.7.103` with `gitHead=adb13ce125a3ed1d71919ce98c7306ad18ce6677`, Apache-2.0 and Node `>=22`. If latest package, integrity, license, required Node version, pinned browser version or `lint`/`check`/`preview`/`render` CLI surface differs, stop and revise the pin and compatibility tests before installing anything. Deprecated `inspect` remains an audit fact, not the new adapter contract.

- [ ] **Step 3: Record the explicit authorization and verify exact pins**

Record the user's 2026-08-09 authorization for `package.json`/`package-lock.json`, exact `hyperframes@0.7.103`, its required matching Chromium, the versioned `RenderStateSnapshot` contract and the OS-egress-contained lint/check/preview/render spike. Before installation require:

```text
hyperframes version = 0.7.103
npm integrity = sha512-+E+CXuBiHgd6Rae/BltrErJGr0PtC/AL5uHXm6ZN77ziERtIFJvqaJveWDmJ4PH6UEJ/lf3Cqxuv8GpATt4Ljw==
published gitHead = adb13ce125a3ed1d71919ce98c7306ad18ce6677
license = Apache-2.0
Node engine = >=22
```

If registry metadata or exact package/source bytes disagree, stop as a supply-chain mismatch; do not silently choose a newer version or integrity.

- [ ] **Step 4: Pin the approved local dependency**

After authorization, create:

```json
{
  "name": "ai-video-renderer-tools",
  "private": true,
  "engines": {
    "node": ">=22"
  },
  "dependencies": {
    "hyperframes": "0.7.103"
  }
}
```

Then run exactly:

```bash
npm install --save-exact hyperframes@0.7.103
./node_modules/.bin/hyperframes --version
npm ls hyperframes --depth=0
node -e 'const l=require("./package-lock.json"); const p=l.packages["node_modules/hyperframes"]; if (p.version!=="0.7.103" || p.integrity!=="sha512-+E+CXuBiHgd6Rae/BltrErJGr0PtC/AL5uHXm6ZN77ziERtIFJvqaJveWDmJ4PH6UEJ/lf3Cqxuv8GpATt4Ljw==") process.exit(1)'
```

Expected: version is exactly `0.7.103`; `package-lock.json` contains one exact top-level pin and matches the recorded registry integrity. Do not use `npx hyperframes`, `@latest`, caret or range resolution in runtime commands.

- [ ] **Step 5: Preinstall the exact required browser and pin its executable path**

Inspect the installed `0.7.103` source before any browser download. If it confirms Chrome Headless Shell `152.0.7928.2`, run the locked installer exactly:

```bash
./node_modules/.bin/browsers install chrome-headless-shell@152.0.7928.2 \
  --path .hyperframes/browser-cache
./node_modules/.bin/browsers list --path .hyperframes/browser-cache
```

Record the listed executable as `P3_HYPERFRAMES_BROWSER_PATH`, require `test -x`, and verify the binary reports `152.0.7928.2`. If the source-required revision differs, the locked installer binary is absent, or the resolved binary reports another version, stop and revise this plan before download/render. Network is allowed for this dependency/browser installation step only; no render source or user asset may be present.

Do not rely on HyperFrames auto-download. Every live `check`/`preview`/`render` command must set `HYPERFRAMES_BROWSER_PATH` to the verified executable and set `HYPERFRAMES_NO_AUTO_INSTALL=1`.

- [ ] **Step 6: Ignore only local install/scratch output**

Append to `.gitignore`:

```gitignore
node_modules/
.hyperframes/
```

- [ ] **Step 7: Commit the dependency lock**

```bash
git add package.json package-lock.json .gitignore
git commit -m "build: pin hyperframes renderer tool"
```

Expected: commit contains only the three listed files. If install creates any other tracked file, stop and inspect it instead of staging broadly.

### Task 1: Add Composition and Receipt Schemas

**Files:**
- Modify: `src/ai_video/production/models.py`
- Modify: `src/ai_video/errors.py`
- Modify: `src/ai_video/production/__init__.py`
- Test: `tests/test_production_models.py`

- [ ] **Step 1: Write failing strict-model tests**

Add tests that instantiate the exact P3 contracts and verify frozen/extra-forbid behavior:

```python
def test_resolved_timeline_requires_integer_boundaries():
    timeline = make_resolved_timeline()
    assert timeline.visual_spans[0].start_frame == 0
    assert timeline.visual_spans[0].duration_frames == 48
    assert timeline.visual_spans[0].start_sample == 0
    assert timeline.visual_spans[0].duration_samples == 96_000


def test_render_receipt_rejects_unknown_fields():
    data = make_render_receipt().model_dump(mode="json")
    data["renderer_fallback"] = "remotion"
    with pytest.raises(ValidationError):
        RenderReceipt.model_validate(data)


def test_renderer_selection_allows_one_selected_renderer():
    with pytest.raises(ValidationError):
        RendererSelectionReceipt(
            receipt_id="select-1",
            attempt_id="attempt-1",
            requested_kind="hyperframes",
            selected_kinds=("hyperframes", "remotion"),
            renderer_version="0.7.103",
        )


def test_manifest_20_rejects_render_state_and_render_attempts(): ...


def test_manifest_20_preserves_historical_custom_nonempty_operation_without_rewrite(): ...


def test_manifest_21_accepts_none_or_one_render_state_pointer(): ...


def test_render_state_snapshot_rejects_mixed_attempt_renderer_timeline_source_asset_or_output_identity(): ...


```

- [ ] **Step 2: Run schema RED**

```bash
python -m pytest tests/test_production_models.py -q
```

Expected: collection fails because `CompositionSpec`, `ResolvedTimeline` and receipt models are not defined/exported.

- [ ] **Step 3: Add typed error codes**

Add to `ErrorCode`:

```python
    COMPOSITION_INVALID = "composition_invalid"
    RENDERER_UNAVAILABLE = "renderer_unavailable"
    RENDERER_SOURCE_INVALID = "renderer_source_invalid"
    RENDER_FAILED = "render_failed"
```

Do not reuse `WORKFLOW_INVALID`, `FFMPEG_FAILED` or string matching for renderer failures.

- [ ] **Step 4: Add exact immutable composition models**

Add these model families to `production/models.py`, reusing `StrictModel`, `VersionedArtifact`, `DeliveryProfile`, `ToolIdentity` and `AssetType`:

```python
class RendererKind(str, Enum):
    HYPERFRAMES = "hyperframes"
    REMOTION = "remotion"


class TransitionKind(str, Enum):
    CUT = "cut"
    CROSSFADE = "crossfade"


class FixedTransform(StrictModel):
    translate_x_px: int = 0
    translate_y_px: int = 0
    scale_x_milli: int = Field(default=1000, gt=0)
    scale_y_milli: int = Field(default=1000, gt=0)
    rotation_millidegrees: int = 0


class CompositionLayerSpec(StrictModel):
    layer_id: str = Field(min_length=1)
    shot_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    trim_start_frame: int = Field(default=0, ge=0)
    trim_duration_frames: int | None = Field(default=None, gt=0)
    transform: FixedTransform = Field(default_factory=FixedTransform)
    opacity_milli: int = Field(default=1000, ge=0, le=1000)
    z_index: int = 0


class TransitionSpec(StrictModel):
    from_shot_id: str
    to_shot_id: str
    kind: TransitionKind
    duration_frames: int = Field(ge=0)


class CompositionSpec(VersionedArtifact):
    composition_id: str
    shot_ids: tuple[str, ...] = Field(min_length=1)
    layers: tuple[CompositionLayerSpec, ...] = Field(min_length=1)
    transitions: tuple[TransitionSpec, ...] = ()
    delivery_profile: DeliveryProfile
    sample_rate: int = Field(default=48_000, gt=0)
    requested_renderer: RendererKind = RendererKind.HYPERFRAMES


class RendererIdentity(StrictModel):
    kind: RendererKind
    version: str = Field(min_length=1)


class ResolvedVisualSpan(StrictModel):
    layer_id: str
    shot_id: str
    asset_id: str
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    materialized_path: Path
    start_frame: int = Field(ge=0)
    duration_frames: int = Field(gt=0)
    start_sample: int = Field(ge=0)
    duration_samples: int = Field(ge=0)
    trim_start_frame: int = Field(ge=0)
    trim_duration_frames: int | None = Field(default=None, gt=0)
    transform: FixedTransform
    opacity_milli: int = Field(ge=0, le=1000)
    z_index: int
    incoming_transition: TransitionSpec | None = None


class ResolvedTimeline(VersionedArtifact):
    timeline_id: str
    composition_spec_id: str
    composition_spec_revision: int = Field(ge=1)
    composition_spec_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    delivery_profile: DeliveryProfile
    sample_rate: int = Field(gt=0)
    renderer: RendererIdentity
    visual_spans: tuple[ResolvedVisualSpan, ...] = Field(min_length=1)
    total_frames: int = Field(gt=0)
    total_samples: int = Field(ge=0)
    composition_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
```

Add immutable receipt models with these required fields:

```python
class RendererSelectionReceipt(StrictModel):
    receipt_id: str
    attempt_id: str
    requested_kind: RendererKind
    selected_kinds: tuple[RendererKind, ...] = Field(min_length=1, max_length=1)
    renderer_version: str


class RendererCheckReceipt(StrictModel):
    command: Literal["lint", "check"]
    tool_version: str
    exit_code: int
    stdout_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stderr_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    error_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)


class RendererAssetBinding(StrictModel):
    asset_id: str
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    materialized_path: Path


class RendererSourceReceipt(VersionedArtifact):
    attempt_id: str
    renderer: RendererIdentity
    timeline_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_path: Path
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_bindings: tuple[RendererAssetBinding, ...] = Field(min_length=1)
    checks: tuple[RendererCheckReceipt, RendererCheckReceipt]


class MeasuredRenderMetadata(StrictModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps_num: int = Field(gt=0)
    fps_den: int = Field(gt=0)
    duration_frames: int = Field(gt=0)
    codec_name: str


class RenderReceipt(VersionedArtifact):
    attempt_id: str
    renderer: RendererIdentity
    timeline_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_hashes: tuple[str, ...] = Field(min_length=1)
    output_path: Path
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_size_bytes: int = Field(gt=0)
    measured: MeasuredRenderMetadata
    decoded_frame_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
```

Add the render-state pointer/snapshot family exactly once in `production/models.py`:

```python
class RenderArtifactPointer(StrictModel):
    path: Path
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class RenderOutputPointer(StrictModel):
    path: Path
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0)


class RenderStateSnapshot(VersionedArtifact):
    attempt_id: str = Field(min_length=1)
    renderer_selection: RendererSelectionReceipt
    renderer: RendererIdentity
    timeline_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_hashes: tuple[str, ...] = Field(min_length=1)
    timeline: RenderArtifactPointer
    source_receipt: RenderArtifactPointer
    render_receipt: RenderArtifactPointer
    output: RenderOutputPointer


class RenderStateSnapshotPointer(StrictModel):
    path: Path
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
```

`RenderStateSnapshot` model validator loads no files; it cross-validates selection attempt ID and renderer kind/version against the duplicated snapshot identities. `project.py`/`state_commit.py` load the exact pointed timeline/source/render receipt/output and cross-validate them against the snapshot's one `attempt_id`, renderer, timeline fingerprint, source hash, ordered asset hashes and output path/hash/size. No field is inferred from directory contents.

Extend `ProductionManifest` and `StateCommitAttempt`:

```python
class StateCommitAttempt(StrictModel):
    # existing P2A fields remain
    operation: str = Field(min_length=1)
    base_render_state: RenderStateSnapshotPointer | None = None
    candidate_render_state: RenderStateSnapshotPointer | None = None
    renderer_selection: RendererSelectionReceipt | None = None
    render_phase: Literal["selection", "source", "lint", "check", "render", "verify", "activate"] | None = None


class ProductionManifest(StrictModel):
    schema_version: Literal["2.0", "2.1"] = "2.0"
    # existing project_id/revision/project/registry/attempt fields remain
    active_render_state: RenderStateSnapshotPointer | None = None
```

Preserve P2A compatibility: persisted `StateCommitAttempt.operation` remains the historical non-empty `str`, not a new `Literal`. Existing `commit(StateCommitRequest)` keeps accepting/persisting its already accepted non-empty operation values and must load a valid 2.0 Manifest containing a historical/custom operation unchanged. Only the new P3 lifecycle methods write and require exact `operation="render_state"`; attempts with that operation must satisfy `base_project == candidate_project == manifest.active_project` and `base_registry == candidate_registry == manifest.active_registry`. `base_render_state` is the pointer observed at begin and `candidate_render_state` appears only after candidate preparation. At begin and failure before candidate preparation, `candidate_artifacts_hash` is the canonical SHA-256 of the empty prepared-artifact set; candidate preparation replaces it with the exact sorted five-artifact identity hash, which any later terminal failure retains. Reject render fields on any non-render operation and reject mixed candidate state. A 2.0 Manifest rejects render fields/`render_state` attempts but continues accepting historical non-render operation strings; a 2.1 Manifest allows no active render yet. Reading does not rewrite either version or immutable P2/P2A snapshots.

Receipt timestamps are intentionally absent from semantic fingerprints. If P2A adds lifecycle timestamps, they remain Manifest/receipt-envelope metadata and are excluded from `composition_fingerprint`.

- [ ] **Step 5: Export only stable P3 schema contracts**

Export these stable schema types from `production/__init__.py`: `CompositionSpec`, `ResolvedTimeline`, `RendererSelectionReceipt`, `RendererSourceReceipt`, `RenderReceipt`, `RenderArtifactPointer`, `RenderOutputPointer`, `RenderStateSnapshot` and `RenderStateSnapshotPointer`. Task 5 later adds the stable lifecycle request/path exports. Keep validators, canonical serialization helpers, path constructors and cross-validation helpers module-private; do not export a second writer or CLI command.

- [ ] **Step 6: Run GREEN and commit**

```bash
python -m pytest tests/test_production_models.py tests/test_errors.py -q
git add src/ai_video/production/models.py src/ai_video/production/__init__.py \
  src/ai_video/errors.py tests/test_production_models.py
git commit -m "feat: add composition and render contracts"
```

Expected: all listed tests pass; existing P2 models remain strict/frozen and no Manifest v1 file changes.

### Task 2: Resolve the Canonical Timeline

**Files:**
- Create: `src/ai_video/production/composition.py`
- Create: `tests/test_production_composition.py`
- Modify: `tests/production_project_factory.py`

- [ ] **Step 1: Write exact RED cases**

Cover:

```python
def test_resolver_uses_explicit_shot_order_not_filename_or_mtime(tmp_path):
    loaded = write_and_load_two_shot_project(tmp_path, filenames=("z.png", "a.png"))
    spec = make_composition_spec(shot_ids=("shot-2", "shot-1"))
    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")
    assert [span.shot_id for span in timeline.visual_spans] == ["shot-2", "shot-1"]


def test_fixed_seconds_round_up_once_at_shot_boundary(tmp_path):
    loaded = write_and_load_two_shot_project(tmp_path, seconds=(1.001, 2.0), fps=24)
    timeline = resolve_composition(loaded, make_composition_spec(), "0.7.103")
    assert [(span.start_frame, span.duration_frames) for span in timeline.visual_spans] == [
        (0, 25),
        (25, 48),
    ]


def test_crossfade_uses_integer_overlap_and_sample_boundaries(tmp_path):
    timeline = resolve_composition(
        write_and_load_two_shot_project(tmp_path, seconds=(2.0, 2.0), fps=24),
        make_composition_spec(crossfade_frames=12, sample_rate=48_000),
        "0.7.103",
    )
    assert timeline.visual_spans[1].start_frame == 36
    assert timeline.visual_spans[1].start_sample == 72_000
    assert timeline.total_frames == 84
    assert timeline.total_samples == 168_000


def test_same_resolved_inputs_have_same_fingerprint_after_mtime_change(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    first = resolve_composition(loaded, spec, "0.7.103")
    os.utime(loaded.asset_paths[spec.layers[0].asset_id], (1_900_000_000, 1_900_000_000))
    second = resolve_composition(loaded, spec, "0.7.103")
    assert second.composition_fingerprint == first.composition_fingerprint
```

Also add negative tests for duplicate/missing Shot IDs, missing/unregistered asset, wrong asset hash, asset path outside loaded registry mapping, non-fixed duration, duplicate layer ID, layer/Shot mismatch, invalid transition adjacency, overlap greater than either duration, duplicate z-order within an overlapping Shot, unsupported `remotion`, and empty timeline.

- [ ] **Step 2: Run resolver RED**

```bash
python -m pytest tests/test_production_composition.py -q
```

Expected: collection fails because `production.composition` does not exist.

- [ ] **Step 3: Implement deterministic arithmetic helpers**

```python
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR


def _frames_for_fixed_seconds(seconds: float, fps: int) -> int:
    value = (Decimal(str(seconds)) * Decimal(fps)).to_integral_value(
        rounding=ROUND_CEILING
    )
    if value <= 0:
        raise _invalid("Fixed Shot duration must resolve to at least one frame.")
    return int(value)


def _sample_at_frame(frame: int, *, fps: int, sample_rate: int) -> int:
    return int(
        (Decimal(frame) * Decimal(sample_rate) / Decimal(fps)).to_integral_value(
            rounding=ROUND_FLOOR
        )
    )
```

No function may add float seconds across Shots.

- [ ] **Step 4: Implement one resolver and one fingerprint owner**

Provide exactly these public functions:

```python
def timeline_fingerprint(timeline: ResolvedTimeline) -> str:
    payload = timeline.model_dump(
        mode="json",
        exclude={"content_hash", "composition_fingerprint", "source_provenance"},
    )
    return canonical_sha256(payload)


def resolve_composition(
    project: LoadedProductionProject,
    spec: CompositionSpec,
    renderer_version: str,
) -> ResolvedTimeline:
    if spec.requested_renderer is not RendererKind.HYPERFRAMES:
        raise _invalid("P3 supports only the hyperframes renderer.")
    if "hyperframes" not in project.project.renderer_policy.allowed:
        raise _invalid("ProductionProject does not allow the hyperframes renderer.")
    if len(spec.shot_ids) != len(set(spec.shot_ids)):
        raise _invalid("CompositionSpec shot_ids must be unique.")
    if len([item.layer_id for item in spec.layers]) != len(
        {item.layer_id for item in spec.layers}
    ):
        raise _invalid("CompositionSpec layer_id values must be unique.")

    shots_by_id = {item.shot_id: item for item in project.shots}
    assets_by_id = {item.asset_id: item for item in project.registry.assets}
    layers_by_shot: dict[str, list[CompositionLayerSpec]] = {
        shot_id: [] for shot_id in spec.shot_ids
    }
    for layer in spec.layers:
        if layer.shot_id not in layers_by_shot:
            raise _invalid(f"Layer {layer.layer_id} references an unordered Shot.")
        layers_by_shot[layer.shot_id].append(layer)

    transition_by_target: dict[str, TransitionSpec] = {}
    adjacent_pairs = set(zip(spec.shot_ids, spec.shot_ids[1:]))
    for transition in spec.transitions:
        pair = (transition.from_shot_id, transition.to_shot_id)
        if pair not in adjacent_pairs or transition.to_shot_id in transition_by_target:
            raise _invalid("Transitions must uniquely join adjacent ordered Shots.")
        if transition.kind is TransitionKind.CUT and transition.duration_frames != 0:
            raise _invalid("A cut transition must have zero duration_frames.")
        if transition.kind is TransitionKind.CROSSFADE and transition.duration_frames <= 0:
            raise _invalid("A crossfade requires positive duration_frames.")
        transition_by_target[transition.to_shot_id] = transition

    spans: list[ResolvedVisualSpan] = []
    cursor = 0
    previous_duration: int | None = None
    supported = {
        VisualStrategy.STATIC_IMAGE,
        VisualStrategy.IMAGE_MOTION,
        VisualStrategy.MOTION_GRAPHICS,
    }
    for shot_id in spec.shot_ids:
        shot = shots_by_id.get(shot_id)
        if shot is None:
            raise _invalid(f"CompositionSpec references unknown Shot {shot_id}.")
        if shot.visual_strategy not in supported:
            raise _invalid(f"Shot {shot_id} strategy is outside the P3 silent-image slice.")
        if shot.duration_policy.mode != "fixed" or shot.duration_policy.seconds is None:
            raise _invalid(f"Shot {shot_id} requires a fixed duration in P3.")
        duration_frames = _frames_for_fixed_seconds(
            shot.duration_policy.seconds, spec.delivery_profile.fps
        )
        incoming = transition_by_target.get(shot_id)
        overlap = incoming.duration_frames if incoming is not None else 0
        if previous_duration is not None and overlap >= min(previous_duration, duration_frames):
            raise _invalid(f"Transition into Shot {shot_id} exceeds an adjacent duration.")
        start_frame = cursor - overlap
        shot_layers = layers_by_shot[shot_id]
        if not shot_layers:
            raise _invalid(f"Shot {shot_id} has no CompositionSpec layer.")
        z_values = [item.z_index for item in shot_layers]
        if len(z_values) != len(set(z_values)):
            raise _invalid(f"Shot {shot_id} has duplicate z_index values.")

        start_sample = _sample_at_frame(
            start_frame,
            fps=spec.delivery_profile.fps,
            sample_rate=spec.sample_rate,
        )
        end_sample = _sample_at_frame(
            start_frame + duration_frames,
            fps=spec.delivery_profile.fps,
            sample_rate=spec.sample_rate,
        )
        for layer in sorted(shot_layers, key=lambda item: (item.z_index, item.layer_id)):
            asset = assets_by_id.get(layer.asset_id)
            source_path = project.asset_paths.get(layer.asset_id)
            if asset is None or source_path is None:
                raise _invalid(f"Layer {layer.layer_id} references an unregistered asset.")
            if sha256_file(source_path) != asset.sha256:
                raise _invalid(f"Asset hash changed before timeline resolution: {asset.asset_id}.")
            logical_path = Path("assets") / (
                f"{asset.asset_id}-{asset.sha256[:12]}{source_path.suffix.lower()}"
            )
            spans.append(
                ResolvedVisualSpan(
                    layer_id=layer.layer_id,
                    shot_id=shot_id,
                    asset_id=asset.asset_id,
                    asset_sha256=asset.sha256,
                    materialized_path=logical_path,
                    start_frame=start_frame,
                    duration_frames=duration_frames,
                    start_sample=start_sample,
                    duration_samples=end_sample - start_sample,
                    trim_start_frame=layer.trim_start_frame,
                    trim_duration_frames=layer.trim_duration_frames,
                    transform=layer.transform,
                    opacity_milli=layer.opacity_milli,
                    z_index=layer.z_index,
                    incoming_transition=incoming,
                )
            )
        cursor = max(cursor, start_frame + duration_frames)
        previous_duration = duration_frames

    provisional = ResolvedTimeline(
        artifact_id=f"timeline-{spec.composition_id}",
        revision=spec.revision,
        content_hash="0" * 64,
        creation_receipt_id=f"resolve-{spec.content_hash}",
        source_provenance=spec.source_provenance,
        timeline_id=f"timeline-{spec.composition_id}-r{spec.revision}",
        composition_spec_id=spec.artifact_id,
        composition_spec_revision=spec.revision,
        composition_spec_hash=spec.content_hash,
        delivery_profile=spec.delivery_profile,
        sample_rate=spec.sample_rate,
        renderer=RendererIdentity(
            kind=RendererKind.HYPERFRAMES,
            version=renderer_version,
        ),
        visual_spans=tuple(spans),
        total_frames=cursor,
        total_samples=_sample_at_frame(
            cursor,
            fps=spec.delivery_profile.fps,
            sample_rate=spec.sample_rate,
        ),
        composition_fingerprint="0" * 64,
    )
    fingerprint = timeline_fingerprint(provisional)
    return seal_artifact(
        provisional.model_copy(update={"composition_fingerprint": fingerprint})
    )
```

`resolve_composition()` must:

1. require `spec.requested_renderer is RendererKind.HYPERFRAMES` and `hyperframes` is allowed by `project.project.renderer_policy`;
2. build `shots_by_id` and `assets_by_id` from the already loaded bundle without scanning directories;
3. validate each ordered `shot_id` appears exactly once and each layer binds the declared Shot plus one exact registry asset/path/hash;
4. accept only fixed-duration `static_image`, `image_motion` and `motion_graphics` Shots in this slice; other strategies fail with `COMPOSITION_INVALID` rather than silently degrading;
5. compute integer frame/sample boundaries and explicit transition overlaps;
6. sort only same-Shot layers by explicit `(z_index, layer_id)` after rejecting conflicting duplicate z-order; never sort Shots by ID or path;
7. construct a provisional `ResolvedTimeline`, calculate one `composition_fingerprint`, then `seal_artifact()` the final immutable timeline.

Keep this as the single resolver; do not add a second resolver or renderer-specific timing function.

- [ ] **Step 5: Run GREEN and commit**

```bash
python -m pytest tests/test_production_models.py tests/test_production_composition.py -q
git add src/ai_video/production/composition.py tests/test_production_composition.py \
  tests/production_project_factory.py
git commit -m "feat: resolve deterministic production timelines"
```

Expected: exact boundary/fingerprint assertions pass and mtime/filename changes do not affect order or fingerprint.

### Task 3: Materialize and Audit HyperFrames Source

**Files:**
- Create: `src/ai_video/production/hyperframes.py`
- Create: `tests/test_production_hyperframes.py`
- Create: `tests/fixtures/hyperframes/silent_image/timeline.json`
- Create: `tests/fixtures/hyperframes/silent_image/source/index.html`
- Create: `tests/fixtures/hyperframes/silent_image/assets/hero.svg`

- [ ] **Step 1: Write source RED tests**

```python
def test_source_is_materialized_only_from_timeline_and_bound_assets(tmp_path):
    timeline = make_resolved_timeline(order=("shot-2", "shot-1"))
    result = materialize_hyperframes_source(
        timeline,
        asset_sources=make_asset_sources(tmp_path, timeline),
        staging_root=tmp_path / "staging",
    )
    assert result.source_sha256 == sha256_file(result.index_path)
    html = result.index_path.read_text(encoding="utf-8")
    assert html.index('data-shot-id="shot-2"') < html.index('data-shot-id="shot-1"')
    assert 'asset-id="image-hero-1"' in html


@pytest.mark.parametrize(
    "forbidden",
    ["https://", "http://", "//cdn.", "fetch(", "XMLHttpRequest", "WebSocket(",
     "Math.random(", "Date.now(", "new Date(", "performance.now("],
)
def test_source_audit_rejects_network_and_wall_clock_inputs(tmp_path, forbidden):
    source = write_source(tmp_path, extra_script=forbidden)
    with pytest.raises(AiVideoError) as exc:
        audit_hyperframes_source(source, expected_assets=())
    assert exc.value.code is ErrorCode.RENDERER_SOURCE_INVALID
```

Also assert source audit rejects absolute asset paths, undeclared files, `..`, asset hash mismatch, missing `data-composition-id`, missing timeline fingerprint, external stylesheet/font/script, and a source asset binding not present in the timeline.

- [ ] **Step 2: Run source RED**

```bash
python -m pytest tests/test_production_hyperframes.py -q -k 'source or audit'
```

Expected: collection fails because source materialization functions do not exist.

- [ ] **Step 3: Implement immutable materialization result**

```python
@dataclass(frozen=True)
class MaterializedHyperFramesSource:
    root: Path
    index_path: Path
    source_sha256: str
    asset_bindings: tuple[RendererAssetBinding, ...]
```

Implement:

```python
def materialize_hyperframes_source(
    timeline: ResolvedTimeline,
    *,
    asset_sources: Mapping[str, Path],
    staging_root: Path,
) -> MaterializedHyperFramesSource:
    expected_ids = {item.asset_id for item in timeline.visual_spans}
    if set(asset_sources) != expected_ids:
        raise _source_invalid("Asset sources must exactly match timeline asset IDs.")
    staging_root.mkdir(parents=True, exist_ok=False)
    assets_root = staging_root / "assets"
    assets_root.mkdir()

    bindings_by_id: dict[str, RendererAssetBinding] = {}
    for span in timeline.visual_spans:
        if span.asset_id in bindings_by_id:
            continue
        source = asset_sources[span.asset_id]
        if not source.is_file() or sha256_file(source) != span.asset_sha256:
            raise _source_invalid(f"Asset bytes do not match timeline: {span.asset_id}.")
        target = staging_root / span.materialized_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha256_file(target) != span.asset_sha256:
            raise _source_invalid(f"Copied asset hash mismatch: {span.asset_id}.")
        bindings_by_id[span.asset_id] = RendererAssetBinding(
            asset_id=span.asset_id,
            asset_sha256=span.asset_sha256,
            materialized_path=span.materialized_path,
        )

    fps = timeline.delivery_profile.fps
    clips: list[str] = []
    for span in timeline.visual_spans:
        transition = span.incoming_transition
        transition_attrs = (
            ' data-transition-kind="cut" data-transition-frames="0"'
            if transition is None
            else (
                f' data-transition-kind="{transition.kind.value}"'
                f' data-transition-frames="{transition.duration_frames}"'
            )
        )
        clips.append(
            "\n".join(
                [
                    (
                        f'<div class="clip" data-layer-id="{escape(span.layer_id)}"'
                        f' data-shot-id="{escape(span.shot_id)}"'
                        f' asset-id="{escape(span.asset_id)}"'
                        f' data-asset-sha256="{span.asset_sha256}"'
                        f' data-start="{_seconds(span.start_frame, fps)}"'
                        f' data-duration="{_seconds(span.duration_frames, fps)}"'
                        f' data-start-frame="{span.start_frame}"'
                        f' data-duration-frames="{span.duration_frames}"'
                        f' data-start-sample="{span.start_sample}"'
                        f' data-duration-samples="{span.duration_samples}"'
                        f' data-z-index="{span.z_index}"'
                        f' data-opacity-milli="{span.opacity_milli}"'
                        f'{transition_attrs}>'
                    ),
                    (
                        f'  <img src="{span.materialized_path.as_posix()}"'
                        f' data-trim-start-frame="{span.trim_start_frame}"'
                        f' data-trim-duration-frames="{span.trim_duration_frames or 0}"'
                        f' data-transform="{escape(_transform_json(span.transform))}" alt="" />'
                    ),
                    "</div>",
                ]
            )
        )

    source = "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8" />',
            "  <style>",
            "    html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#000}",
            "    #stage{position:relative;overflow:hidden}",
            "    .clip{position:absolute;inset:0}",
            "    .clip img{width:100%;height:100%;object-fit:cover}",
            "  </style>",
            "</head>",
            "<body>",
            (
                f'<div id="stage" data-composition-id="{escape(timeline.timeline_id)}"'
                f' data-timeline-fingerprint="{timeline.composition_fingerprint}"'
                f' data-renderer-version="{escape(timeline.renderer.version)}"'
                f' data-start="0" data-duration="{_seconds(timeline.total_frames, fps)}"'
                f' data-width="{timeline.delivery_profile.width}"'
                f' data-height="{timeline.delivery_profile.height}"'
                f' data-fps="{fps}">'
            ),
            *clips,
            "</div>",
            "</body>",
            "</html>",
            "",
        ]
    )
    index_path = staging_root / "index.html"
    index_path.write_text(source, encoding="utf-8", newline="\n")
    bindings = tuple(bindings_by_id[key] for key in sorted(bindings_by_id))
    audit_hyperframes_source(index_path, expected_assets=bindings)
    return MaterializedHyperFramesSource(
        root=staging_root,
        index_path=index_path,
        source_sha256=sha256_file(index_path),
        asset_bindings=bindings,
    )


def audit_hyperframes_source(
    index_path: Path,
    *,
    expected_assets: tuple[RendererAssetBinding, ...],
) -> None:
    source = index_path.read_text(encoding="utf-8")
    forbidden = (
        "https://", "http://", "//cdn.", "fetch(", "XMLHttpRequest",
        "WebSocket(", "Math.random(", "Date.now(", "new Date(",
        "performance.now(", "@import", "<link ",
    )
    hit = next((token for token in forbidden if token in source), None)
    if hit is not None:
        raise _source_invalid(f"HyperFrames source contains forbidden token: {hit}")
    if "data-composition-id=" not in source or "data-timeline-fingerprint=" not in source:
        raise _source_invalid("HyperFrames source is missing composition identity.")
    for binding in expected_assets:
        relative = binding.materialized_path
        if relative.is_absolute() or ".." in relative.parts:
            raise _source_invalid(f"Unsafe materialized asset path: {relative}")
        resolved = (index_path.parent / relative).resolve()
        try:
            resolved.relative_to(index_path.parent.resolve())
        except ValueError as exc:
            raise _source_invalid(f"Asset escapes staging root: {relative}") from exc
        if not resolved.is_file() or sha256_file(resolved) != binding.asset_sha256:
            raise _source_invalid(f"Untracked or changed source asset: {binding.asset_id}")
        if f'src="{relative.as_posix()}"' not in source:
            raise _source_invalid(f"Source does not bind asset: {binding.asset_id}")
    expected_files = {Path("index.html"), *(item.materialized_path for item in expected_assets)}
    actual_files = {
        item.relative_to(index_path.parent)
        for item in index_path.parent.rglob("*")
        if item.is_file()
    }
    if actual_files != expected_files:
        raise _source_invalid("HyperFrames staging contains an untracked file.")


def _seconds(frame_count: int, fps: int) -> str:
    value = Decimal(frame_count) / Decimal(fps)
    rendered = format(value.quantize(Decimal("0.000000001")), "f")
    return rendered.rstrip("0").rstrip(".") or "0"


def _transform_json(transform: FixedTransform) -> str:
    return json.dumps(
        transform.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
```

Import `Mapping`, `dataclass`, `Decimal`, `escape` from `html`, `json`, `shutil`, the existing `sha256_file()`, and the named production models. After Task 4 introduces `RendererAttemptError`, `_source_invalid()` must return a non-retryable instance with `code=ErrorCode.RENDERER_SOURCE_INVALID` and `phase="source"`.

Materialization rules:

- `staging_root` must equal the validated `RenderAttemptPaths.source_root` returned by `ProductionStateCommitter.render_attempt_paths(attempt_id)`; this pure materializer never invents layout or switches a pointer. Unit tests may pass an equivalent `tmp_path` fixture only through the same pure path validator. The staged output is `RenderAttemptPaths.staged_output_path`; neither path is a durable artifact identity.
- Copy each timeline asset to `assets/<asset_id>-<first12sha><suffix>` after verifying the source bytes still match registry SHA-256; no symlink and no directory scan.
- Generate `index.html` in exact `timeline.visual_spans` order. Convert frame boundaries to decimal seconds only at source materialization with `Decimal(frame) / Decimal(fps)` and a stable string formatter.
- Embed timeline fingerprint, renderer version, asset ID/hash, trim, fixed transform, opacity, z-order and transition as explicit local data attributes/JSON.
- Use only local HTML/CSS/HyperFrames runtime features proven by the live spike. Do not reference CDN GSAP, Google Fonts, remote media, `.env`, current time or randomness.
- Write source once into the caller-supplied staging root, hash it, run `audit_hyperframes_source()`, and return the result. No source rewrite is allowed after hashing.

Keep these as straight-line materialization/audit functions; no template discovery, glob or alternate renderer branch is permitted.

- [ ] **Step 4: Seal the deterministic fixture**

Commit a human-readable `timeline.json`, its exact expected `index.html` and a minimal local `assets/hero.svg`. The unit test must regenerate source in `tmp_path` and assert exact text and SHA-256 equality with the fixture. Fixture files contain only local relative assets and no generated binary output.

- [ ] **Step 5: Run GREEN and commit**

```bash
python -m pytest tests/test_production_hyperframes.py -q -k 'source or audit'
git add src/ai_video/production/hyperframes.py tests/test_production_hyperframes.py \
  tests/fixtures/hyperframes/silent_image/timeline.json \
  tests/fixtures/hyperframes/silent_image/source/index.html \
  tests/fixtures/hyperframes/silent_image/assets/hero.svg
git commit -m "feat: materialize audited hyperframes sources"
```

Expected: fixture/source hash tests pass without Node, Chrome or network.

### Task 4: Add the Exclusive HyperFrames Adapter

**Files:**
- Modify: `src/ai_video/production/hyperframes.py`
- Modify: `src/ai_video/production/__init__.py`
- Test: `tests/test_production_hyperframes.py`

- [ ] **Step 1: Write fake-runner RED tests**

Use an injected runner; default tests must never execute the real binary:

```python
def test_adapter_runs_one_pinned_renderer_in_order(tmp_path):
    runner = FakeRunner(
        version="0.7.103",
        results={"lint": clean_lint_json(), "check": clean_check_json(), "render": ""},
    )
    result = HyperFramesAdapter(runner=runner, expected_version="0.7.103").render(
        attempt=make_render_attempt(tmp_path),
    )
    assert [call.command for call in runner.calls] == ["lint", "check", "render"]
    assert {call.env["HYPERFRAMES_NO_UPDATE_CHECK"] for call in runner.calls} == {"1"}
    assert result.render.renderer.kind is RendererKind.HYPERFRAMES


def test_adapter_rejects_remotion_without_fallback(tmp_path):
    runner = FakeRunner()
    with pytest.raises(AiVideoError) as exc:
        HyperFramesAdapter(runner, "0.7.103").render(
            attempt=make_render_attempt(tmp_path, renderer_kind="remotion")
        )
    assert exc.value.code is ErrorCode.RENDERER_UNAVAILABLE
    assert runner.calls == []


@pytest.mark.parametrize("failed_phase", ["lint", "check", "render"])
def test_adapter_reports_typed_phase_failure_without_next_command(tmp_path, failed_phase):
    runner = FakeRunner(fail_at=failed_phase)
    with pytest.raises(RendererAttemptError) as exc:
        HyperFramesAdapter(runner, "0.7.103").render(make_render_attempt(tmp_path))
    assert exc.value.phase == failed_phase
    assert all(call.command != "render" for call in runner.calls) if failed_phase != "render" else True
```

Also cover wrong tool version, malformed JSON, lint errors, check errors, warnings policy, missing/empty output, output hash mismatch, measured width/height/FPS/duration mismatch, timeout, stderr truncation/redaction, no source mutation after lint, and only one selected renderer.

- [ ] **Step 2: Run adapter RED**

```bash
python -m pytest tests/test_production_hyperframes.py -q -k 'adapter or receipt or failure'
```

Expected: tests fail because runner/adapter/receipt construction is not implemented.

- [ ] **Step 3: Implement the injected executable boundary**

```python
@dataclass
class RendererAttemptError(AiVideoError):
    phase: Literal["source", "lint", "check", "render", "verify"] = "render"


@dataclass(frozen=True)
class RendererCommandResult:
    returncode: int
    stdout: str
    stderr: str


class RendererRunner(Protocol):
    def version(self) -> str:
        pass

    def run(
        self,
        command: str,
        args: tuple[str, ...],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout_seconds: int,
    ) -> RendererCommandResult:
        pass


@dataclass(frozen=True)
class HyperFramesRenderAttempt:
    attempt_id: str
    selection: RendererSelectionReceipt
    timeline: ResolvedTimeline
    asset_sources: Mapping[str, Path]
    staging_root: Path
    output_path: Path


@dataclass(frozen=True)
class HyperFramesRenderResult:
    source: RendererSourceReceipt
    render: RenderReceipt


OFFLINE_ENV = {
    "CI": "1",
    "HYPERFRAMES_NO_TELEMETRY": "1",
    "DO_NOT_TRACK": "1",
    "HYPERFRAMES_NO_UPDATE_CHECK": "1",
    "HYPERFRAMES_NO_AUTO_INSTALL": "1",
}
```

Task 4 implements only the injected renderer executor and typed receipt construction. Task 5 adds the named `render_with_hyperframes()` orchestration after the real lifecycle request/API types exist; do not create a temporary alias or duplicate request model here.

`OFFLINE_ENV` 是必要但不充分的 process policy：它不阻止 npm update fetch 或 browser download。默认 unit tests 只使用 fake runner；real runner/live spike 还必须在 OS-level egress denial/observability 下运行，并用经 Renderer Gate 验收的 `HYPERFRAMES_BROWSER_PATH` 显式指向预先安装的 browser。

The production runner must call only the approved local binary path `node_modules/.bin/hyperframes`, pass argv as a list without `shell=True`, enforce timeout, capture bounded stdout/stderr, redact secrets and never invoke `npx`, `upgrade`, `browser`, `cloud`, `lambda`, `tts` or `transcribe`.

- [ ] **Step 4: Implement strict phase parsing and receipts**

`HyperFramesAdapter.render()` must run exactly:

```text
node_modules/.bin/hyperframes lint "$STAGING_ROOT" --json
node_modules/.bin/hyperframes check "$STAGING_ROOT" --json
node_modules/.bin/hyperframes render "$STAGING_ROOT" -o "$ATTEMPT_STAGED_OUTPUT_PATH"
```

Implement one `HyperFramesAdapter.render(attempt) -> HyperFramesRenderResult` method with this direct phase boundary:

```python
class HyperFramesAdapter:
    def __init__(
        self,
        runner: RendererRunner,
        expected_version: str,
        *,
        probe: Callable[[Path], dict] = probe_clip,
        decoded_frames: Callable[[Path], str] = decoded_frame_sha256,
    ) -> None:
        self._runner = runner
        self._expected_version = expected_version
        self._probe = probe
        self._decoded_frames = decoded_frames

    def _check(
        self,
        command: Literal["lint", "check"],
        root: Path,
    ) -> RendererCheckReceipt:
        result = self._runner.run(
            command,
            (str(root), "--json"),
            cwd=root,
            env=dict(OFFLINE_ENV),
            timeout_seconds=120,
        )
        if result.returncode != 0:
            raise _render_error(command, result)
        try:
            payload = json.loads(result.stdout)
            if command == "lint":
                error_count = int(payload["errorCount"])
                warning_count = int(payload["warningCount"])
            else:
                sections = ("lint", "runtime", "layout", "motion", "contrast")
                if payload["ok"] is not True:
                    raise ValueError("HyperFrames check did not report ok=true")
                error_count = sum(int(payload[name]["errorCount"]) for name in sections)
                warning_count = sum(
                    int(payload[name]["warningCount"]) for name in sections
                )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise _source_invalid(f"Malformed HyperFrames {command} JSON.") from exc
        if error_count:
            raise _source_invalid(f"HyperFrames {command} reported {error_count} error(s).")
        return RendererCheckReceipt(
            command=command,
            tool_version=self._expected_version,
            exit_code=result.returncode,
            stdout_sha256=_text_sha256(result.stdout),
            stderr_sha256=_text_sha256(_redact(result.stderr)),
            error_count=error_count,
            warning_count=warning_count,
        )

    def render(self, attempt: HyperFramesRenderAttempt) -> HyperFramesRenderResult:
        if attempt.selection.selected_kinds != (RendererKind.HYPERFRAMES,):
            raise _renderer_unavailable("P3 render attempt must select only hyperframes.")
        if attempt.timeline.renderer.kind is not RendererKind.HYPERFRAMES:
            raise _renderer_unavailable("ResolvedTimeline does not select hyperframes.")
        if self._runner.version() != self._expected_version:
            raise _renderer_unavailable("Installed HyperFrames version does not match the pin.")
        materialized = materialize_hyperframes_source(
            attempt.timeline,
            asset_sources=attempt.asset_sources,
            staging_root=attempt.staging_root,
        )
        lint_receipt = self._check("lint", materialized.root)
        _verify_materialized_unchanged(materialized)
        check_receipt = self._check("check", materialized.root)
        _verify_materialized_unchanged(materialized)
        source_receipt = seal_artifact(
            RendererSourceReceipt(
                artifact_id=f"renderer-source-{attempt.attempt_id}",
                revision=1,
                content_hash="0" * 64,
                creation_receipt_id=attempt.selection.receipt_id,
                source_provenance=attempt.timeline.source_provenance,
                attempt_id=attempt.attempt_id,
                renderer=attempt.timeline.renderer,
                timeline_fingerprint=attempt.timeline.composition_fingerprint,
                source_path=materialized.index_path.relative_to(materialized.root),
                source_sha256=materialized.source_sha256,
                asset_bindings=materialized.asset_bindings,
                checks=(lint_receipt, check_receipt),
            )
        )
        command_result = self._runner.run(
            "render",
            (str(materialized.root), "-o", str(attempt.output_path)),
            cwd=materialized.root,
            env=dict(OFFLINE_ENV),
            timeout_seconds=1800,
        )
        if command_result.returncode != 0:
            raise _render_error("render", command_result)
        _verify_materialized_unchanged(materialized)
        if not attempt.output_path.is_file() or attempt.output_path.stat().st_size == 0:
            raise _render_failed("HyperFrames output is missing or empty.")
        measured = _measured_metadata(self._probe(attempt.output_path))
        _validate_measured_timeline(measured, attempt.timeline)
        render_receipt = seal_artifact(
            RenderReceipt(
                artifact_id=f"render-{attempt.attempt_id}",
                revision=1,
                content_hash="0" * 64,
                creation_receipt_id=source_receipt.artifact_id,
                source_provenance=attempt.timeline.source_provenance,
                attempt_id=attempt.attempt_id,
                renderer=attempt.timeline.renderer,
                timeline_fingerprint=attempt.timeline.composition_fingerprint,
                source_sha256=source_receipt.source_sha256,
                asset_hashes=tuple(
                    item.asset_sha256 for item in source_receipt.asset_bindings
                ),
                output_path=attempt.output_path.relative_to(materialized.root),
                output_sha256=sha256_file(attempt.output_path),
                output_size_bytes=attempt.output_path.stat().st_size,
                measured=measured,
                decoded_frame_fingerprint=self._decoded_frames(attempt.output_path),
            )
        )
        return HyperFramesRenderResult(source=source_receipt, render=render_receipt)


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _redact(value: str) -> str:
    return re.sub(
        r"(?i)(authorization|api[_-]?key|token|secret)(\s*[:=]\s*)\S+",
        r"\1\2[REDACTED]",
        value,
    )[-8_192:]


def _render_error(phase: str, result: RendererCommandResult) -> RendererAttemptError:
    return RendererAttemptError(
        code=(
            ErrorCode.RENDERER_SOURCE_INVALID
            if phase in {"lint", "check"}
            else ErrorCode.RENDER_FAILED
        ),
        user_message=f"HyperFrames {phase} failed.",
        technical_detail=_redact(result.stderr or result.stdout),
        retryable=False,
        phase=cast(Literal["lint", "check", "render"], phase),
    )


def _verify_materialized_unchanged(value: MaterializedHyperFramesSource) -> None:
    if sha256_file(value.index_path) != value.source_sha256:
        raise _source_invalid("HyperFrames source changed after hashing.")
    audit_hyperframes_source(value.index_path, expected_assets=value.asset_bindings)


def decoded_frame_sha256(path: Path) -> str:
    result = run_command(
        [
            "ffmpeg", "-v", "error", "-i", str(path),
            "-map", "0:v:0", "-f", "framemd5", "-",
        ]
    )
    rows = [
        line.strip()
        for line in result.stdout.replace("\r\n", "\n").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if not rows:
        raise _render_failed("Could not derive decoded frame evidence.")
    return _text_sha256("\n".join(rows) + "\n")


def _measured_metadata(probe: dict) -> MeasuredRenderMetadata:
    streams = [item for item in probe.get("streams", []) if item.get("codec_type") == "video"]
    if len(streams) != 1:
        raise _render_failed("Render must contain exactly one video stream.")
    stream = streams[0]
    try:
        fps_num_text, fps_den_text = str(stream["r_frame_rate"]).split("/", 1)
        return MeasuredRenderMetadata(
            width=int(stream["width"]),
            height=int(stream["height"]),
            fps_num=int(fps_num_text),
            fps_den=int(fps_den_text),
            duration_frames=int(stream["nb_frames"]),
            codec_name=str(stream["codec_name"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise _render_failed("Render metadata is incomplete or invalid.") from exc


def _validate_measured_timeline(
    measured: MeasuredRenderMetadata,
    timeline: ResolvedTimeline,
) -> None:
    profile = timeline.delivery_profile
    if (measured.width, measured.height) != (profile.width, profile.height):
        raise _render_failed("Render dimensions do not match ResolvedTimeline.")
    if measured.fps_num != profile.fps * measured.fps_den:
        raise _render_failed("Render FPS does not match ResolvedTimeline.")
    if measured.duration_frames != timeline.total_frames:
        raise _render_failed("Render frame count does not match ResolvedTimeline.")
```

`decoded_frame_sha256()` must run existing `ffmpeg_tools.run_command()` with `ffmpeg -v error -i <output> -map 0:v:0 -f framemd5 -`, remove comment/header lines, normalize line endings and SHA-256 the ordered per-frame checksum rows. This is decoded-frame evidence; it is distinct from `output_sha256` and must not include container metadata. `_measured_metadata()` must parse the first video stream's `width`, `height`, rational frame rate, `nb_frames` and `codec_name`; missing/ambiguous values are typed `RENDER_FAILED`, not guessed from filename or duration text.

The method must verify tool version after the selection has been durably begun, parse the pinned JSON schema, require zero errors, record warning counts, rehash source/assets between phases, validate output with `probe_clip()`, calculate output/decoded-frame hashes and build sealed source/render receipts. It must never include timestamps in timeline/source/decoded-frame fingerprints. Task 5 supplies the real committer implementation and crash/replay tests used by this orchestration boundary.

Import `Callable`, `Mapping`, `Protocol`, `Literal`, `cast`, `hashlib`, `json`, `re`, existing `probe_clip()`/`run_command()` and the named P3 models. `_source_invalid()` must return `RendererAttemptError(phase="source")`; `_render_failed()` must return `RendererAttemptError(phase="verify")`; `_renderer_unavailable()` returns a non-retryable `AiVideoError` with `code=RENDERER_UNAVAILABLE` before any executable work. No helper may start a fallback command.

Do not add preview to automated adapter flow. Preview belongs only to the explicit live spike gate because it starts a server/browser and is not necessary for deterministic batch execution.

- [ ] **Step 5: Run GREEN and commit**

```bash
python -m pytest tests/test_production_hyperframes.py -q
git add src/ai_video/production/hyperframes.py src/ai_video/production/__init__.py \
  tests/test_production_hyperframes.py
git commit -m "feat: add hyperframes renderer adapter"
```

Expected: fake/no-network tests pass; process call list proves one renderer and exact phase order.

### Task 5: Add the P2A-Owned Render-State Lifecycle

**Problem boundary:** activate one exact timeline/source/render/output set after one HyperFrames attempt. **Single owner:** existing `ProductionManifest` + `ProductionStateCommitter`. **Old path retired:** the former authorization-only Task 5, invented `RenderAttemptCommitter`, alias methods, second Manifest/writer, Legacy Manifest v1, `runs/<run_id>/` or ad-hoc discovery. **Unchanged contract:** existing `commit(StateCommitRequest)` and exact project/registry pair/replay stay unchanged; render operations prove that pair remains identical.

**Files:**
- Modify: `src/ai_video/production/paths.py`
- Modify: `src/ai_video/production/project.py`
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `src/ai_video/production/hyperframes.py`
- Modify: `src/ai_video/production/__init__.py`
- Modify: `tests/test_production_project.py`
- Modify: `tests/test_production_state_commit.py`
- Modify: `tests/test_production_state_recovery.py`
- Modify: `tests/test_production_hyperframes.py`
- Modify: `tests/helpers/p2a_crash_worker.py`

- [ ] **Step 1: Write RED path, migration and read-only loader cases**

Test canonical full-hash paths and containment for all five immutable namespaces plus safe attempt IDs. Reject empty, `.`/`..`, slash, backslash, absolute path, symlink escape, shortened hash filename, wrong namespace/extension and output hash/path mismatch.

Add P2 read-only tests:

```python
def test_reader_loads_20_without_render_state_and_does_not_rewrite(tmp_path): ...
def test_reader_loads_20_historical_custom_operation_without_rewrite(tmp_path): ...
def test_reader_loads_21_with_none_render_state(tmp_path): ...
def test_reader_verifies_21_selected_render_state_and_all_exact_artifacts(tmp_path): ...
def test_reader_rejects_tampered_or_mixed_render_state_without_fallback(tmp_path): ...
```

`load_production_project()` must preserve bytes and mtimes for both versions. A 2.0 Manifest remains valid until the first render lifecycle write; no eager migration.

- [ ] **Step 2: Add canonical path and attempt-path APIs**

In `paths.py`, add one constructor/validator per namespace:

```python
canonical_render_timeline_path(content_hash)
canonical_renderer_source_receipt_path(content_hash)
canonical_render_receipt_path(content_hash)
canonical_render_state_path(content_hash)
canonical_render_output_path(file_sha256, suffix=".mp4")
canonical_render_attempt_root(attempt_id)
```

In `state_commit.py` add:

```python
@dataclass(frozen=True)
class RenderAttemptPaths:
    attempt_root: Path
    source_root: Path
    staged_output_path: Path


def render_attempt_paths(self, attempt_id: str) -> RenderAttemptPaths:
    ...
```

This method is pure: it validates a conservative safe attempt ID, returns relative contained paths rooted at `state/render/attempts/<attempt-id>/`, and performs no mkdir/write/delete. The adapter creates only the exact attempt-owned directories it consumes.

Use the same immutable path validators in `project.py`: when a 2.1 Manifest has `active_render_state`, load that exact state snapshot, its three JSON artifacts and output; verify canonical path, file SHA-256, semantic revision/content hash, output size, and every cross identity. Return the verified render state as optional read-only data on `LoadedProductionProject`; do not scan, activate, recover or mutate.

- [ ] **Step 3: Define exact strict lifecycle requests**

Add frozen dataclasses/models in `state_commit.py`:

```python
@dataclass(frozen=True)
class BeginRenderAttemptRequest:
    attempt_id: str
    expected_manifest_revision: int
    current_project: ProjectSnapshotPointer
    current_registry: RegistrySnapshotPointer
    base_render_state: RenderStateSnapshotPointer | None
    renderer_selection: RendererSelectionReceipt


@dataclass(frozen=True)
class RecordRenderFailureRequest:
    attempt_id: str
    expected_manifest_revision: int
    current_project: ProjectSnapshotPointer
    current_registry: RegistrySnapshotPointer
    base_render_state: RenderStateSnapshotPointer | None
    renderer_selection: RendererSelectionReceipt
    phase: Literal["source", "lint", "check", "render", "verify"]
    error_code: str
    error_message: str


@dataclass(frozen=True)
class ActivateRenderStateRequest:
    attempt_id: str
    expected_manifest_revision: int
    current_project: ProjectSnapshotPointer
    current_registry: RegistrySnapshotPointer
    base_render_state: RenderStateSnapshotPointer | None
    renderer_selection: RendererSelectionReceipt
    artifacts: tuple[PreparedArtifact, ...]
    next_render_state: RenderStateSnapshotPointer
```

The request identity is the complete tuple of attempt ID, expected/base identities, selection, sorted `(relative_path, file_sha256)` artifact set and next pointer. `BeginRenderAttemptRequest.expected_manifest_revision=R`; its fresh write yields R+1. An outer `RecordRenderFailureRequest` is valid only against the authoritative begun revision R+1 and yields terminal R+2; if the attempt is already candidate-prepared at R+2, the request is stale and must be rejected because activation owns that stage. `ActivateRenderStateRequest.expected_manifest_revision=R+1` transfers ownership to `activate_render_state()`; its candidate-prepared and final/failed transitions use authoritative R+2 internally without constructing a stale external failure request. Begin/success exact replay returns the already-persisted corresponding Manifest state; reuse of an attempt ID with any differing identity is `PRODUCTION_STATE_INVALID`. Pre-candidate failure replay is idempotent only when phase/code/message and all base identities match. Requests reject stale `expected_manifest_revision` except an exact recognized replay for the same owner/stage.

For every render request, `current_project/current_registry` must equal the live Manifest pair. Persisted render attempts set `base_project == candidate_project == current_project` and `base_registry == candidate_registry == current_registry`; validators reject any project/registry change or any mixed project-registry/render operation.

- [ ] **Step 4: Implement begin and typed failure persistence**

Add real methods, not wrappers around `commit()`:

```python
def begin_render_attempt(self, request: BeginRenderAttemptRequest) -> ProductionManifest: ...
def record_render_failure(self, request: RecordRenderFailureRequest) -> ProductionManifest: ...
```

Both run under `state/commit.lock` and use the existing atomic Manifest writer. `begin_render_attempt()` validates selection contains exactly HyperFrames `0.7.103`, writes a running `StateCommitAttempt(render_phase="selection")`, and on the first render write migrates Manifest 2.0 -> 2.1 in that same replace. This durable write must finish before version/lint/check/render. It never switches `active_render_state`.

`record_render_failure()` requires the exact R+1 matching begun attempt with no candidate. It persists terminal R+2 `failed`, exact typed phase/code/redacted bounded message and finished time, and leaves `active_render_state` plus project/registry pointers unchanged. It rejects a candidate-prepared R+2 attempt; post-candidate failure persistence belongs only to `activate_render_state()`. Source materialization and installed-version/renderer-availability failures use phase `source`; lint, check, render and output verification use their named phases before activation begins. If failure persistence itself fails, surface the state error without claiming the render failure was recorded.

- [ ] **Step 5: Integrate one lifecycle-owned HyperFrames orchestration path**

Now add `hyperframes.py::render_with_hyperframes()` using the real Task 5 request types. It calls `begin_render_attempt()` before `runner.version()` or source materialization, obtains `render_attempt_paths()`, calls `HyperFramesAdapter.render()` once, builds the five exact prepared artifacts and calls `activate_render_state()` only after verify.

Use one explicit post-begin exception boundary:

```python
manifest = committer.begin_render_attempt(begin_request)
phase = "source"
try:
    paths = committer.render_attempt_paths(begin_request.attempt_id)
    version = runner.version()
    if version != expected_version:
        raise _renderer_unavailable("Installed HyperFrames version does not match the pin.")
    # materialize source, then advance phase before lint/check/render/verify
    result = adapter.render(...)
except Exception as exc:
    committer.record_render_failure(
        failure_request_from(exc, phase=phase, manifest=manifest)
    )
    raise
activation = activation_request(result, expected_manifest_revision=manifest.manifest_revision)
# Deliberately outside the outer failure handler: activate_render_state owns R+2 onward.
return committer.activate_render_state(activation)
```

Every ordinary exception after successful begin but before the call to `activate_render_state()`, including a plain `RENDERER_UNAVAILABLE` from `runner.version()`/wrong pin, `OSError` during source materialization, and typed lint/check/render/verify errors, is normalized into `RecordRenderFailureRequest` before re-raise. Version/availability/materialization use `phase="source"`. The outer function never catches `activate_render_state()` merely to call `record_render_failure()`; once activation durably writes R+2, R+1 is stale and only activation may write terminal failure. Process-level interruption/crash and `PRODUCTION_STATE_OUTCOME_UNKNOWN` remain explicit-recovery paths. If pre-candidate failure persistence itself fails, raise the state persistence error with the original exception attached as a note. No ordinary post-begin path may leave the attempt `running`.

Add focused order/persistence tests:

```python
def test_orchestrator_persists_selection_before_version_or_executable_call(tmp_path): ...

@pytest.mark.parametrize("failure", ["version_exception", "wrong_version", "source_exception"])
def test_orchestrator_records_post_begin_availability_as_source_failure(tmp_path, failure): ...

@pytest.mark.parametrize("phase", ["source", "lint", "check", "render", "verify"])
def test_orchestrator_records_every_ordinary_phase_and_never_leaves_running(tmp_path, phase): ...

def test_orchestrator_does_not_retry_record_failure_after_activation_takes_ownership(tmp_path): ...
```

Assert event order begins with `begin_render_attempt`. Pre-candidate failure ends in one `record_render_failure`; success ends in `activate_render_state`. If activation reports an internally persisted terminal failure or `PRODUCTION_STATE_OUTCOME_UNKNOWN`, `record_render_failure` is not called, so no stale R+1 retry occurs. Failed Manifest status is terminal, active/project/registry pointers are unchanged, and no alternate renderer runs.

- [ ] **Step 6: Prepare and validate the exact success artifact set**

The orchestration layer must pass exactly five `PreparedArtifact`s, sorted by canonical relative path:

1. sealed `ResolvedTimeline` JSON at `state/render/timelines/<timeline.content_hash>.json`;
2. sealed `RendererSourceReceipt` JSON at `state/render/source-receipts/<source.content_hash>.json`;
3. sealed `RenderReceipt` JSON at `state/render/render-receipts/<render.content_hash>.json`;
4. verified output bytes at `state/render/outputs/<output_sha256>.mp4`;
5. sealed `RenderStateSnapshot` JSON at `state/render/states/<state.content_hash>.json`.

`activate_render_state()` parses/reseals the four JSON artifacts, rehashes all bytes, reopens promoted files, verifies the output size/hash, validates the snapshot cross references and requires `next_render_state` to point exactly at the fifth artifact. Extra, missing, duplicate or noncanonical artifacts fail. The immutable writer uses file temp -> file fsync -> promote-without-overwrite -> parent-directory fsync -> reopen verify for every artifact/output.

- [ ] **Step 7: Durably prepare the candidate, then atomically activate one pointer**

Add:

```python
def activate_render_state(self, request: ActivateRenderStateRequest) -> ProductionManifest: ...
```

It requires the exact running attempt and unchanged project/registry pair. Activation has two separate durable Manifest transitions after all five immutable artifacts verify:

1. **candidate-prepared transition:** atomically replace a running Manifest attempt containing `candidate_render_state=next_render_state`, the exact sorted five-artifact `candidate_artifacts_hash` and `render_phase="activate"`; keep `active_render_state=base_render_state` and keep project/registry byte-for-byte unchanged. The candidate-prepared Manifest itself must complete temp write -> file fsync -> replace -> parent-directory fsync -> reopen/identity verification before final activation begins.
2. **final succeeded transition:** atomically replace one Manifest with `active_render_state=next_render_state` and the same project/registry pointers, then mark the exact attempt `succeeded`. Only this second replace is the active render commit point.

After candidate preparation is durably authoritative at R+2, `activate_render_state()` owns every remaining transition under the same `state/commit.lock`. It must internally catch every ordinary/non-`PRODUCTION_STATE_OUTCOME_UNKNOWN` exception before the final active-pointer `os.replace`, including final succeeded-Manifest serialization, temp open/write, file fsync and the last pre-replace checkpoint. It removes only its exact owned final-Manifest temp if present, then atomically writes a terminal R+3 `FAILED` Manifest derived from authoritative R+2: retain `candidate_render_state` and the five-artifact aggregate hash, keep `active_render_state=base_render_state`, keep project/registry unchanged, set `render_phase="activate"`, typed error code/redacted bounded message and finished time. Reopen and verify that terminal Manifest before re-raising the original typed activation error. The outer orchestrator must not call `record_render_failure()` for this error.

Once the final active-pointer `os.replace` has been attempted/completed, any replace, parent-directory-fsync, reopen or post-replace ambiguity becomes `PRODUCTION_STATE_OUTCOME_UNKNOWN`; `activate_render_state()` must not overwrite it with `FAILED`. Explicit recovery compares the exact old/new triples and resolves it.

If the base Manifest revision is `R`, a fresh success has exactly `R+1` after `begin_render_attempt()`, `R+2` after candidate preparation and `R+3` after the final pointer switch. A pre-candidate ordinary failure written by `record_render_failure()` is terminal R+2. A post-candidate pre-replace ordinary failure written internally by `activate_render_state()` is terminal R+3 with base active pointer and retained candidate/hash. If that internal terminal-failure write itself cannot become authoritative, raise `PRODUCTION_STATE_OUTCOME_UNKNOWN` and require recovery; never attempt an outer stale R+1 failure write.

Exact replay behavior:

- exact begin replay returns the current matching attempt at begun, candidate-prepared, failed or succeeded stage without revision increment;
- exact activation replay from begun state revalidates/promotes the same immutable set, writes candidate-prepared once, then final once;
- exact activation replay from candidate-prepared state revalidates the five artifacts and performs only the final switch;
- exact activation replay after succeeded state returns the active Manifest without artifact rewrite or revision increment;
- exact replay after an internally terminal failed R+3 returns that failed Manifest and does not retry activation; an outer R+1 `RecordRenderFailureRequest` is stale and rejected;
- a stale expected revision is accepted only for one of those exact identities; any attempt-ID/request/artifact/pointer mismatch is rejected.

Before the final `os.replace`, old/`None` render state stays active; after it, candidate is active. Candidate-prepared replace/directory-fsync ambiguity is resolved by reopening the Manifest and matching the exact attempt/candidate/hash while the active pointer remains base. Final replace ambiguity becomes `outcome_unknown` and is resolved only by explicit recovery.

Extend `CommitPhase` with render-specific checkpoints:

```python
AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_WRITE
AFTER_RENDER_CANDIDATE_MANIFEST_FILE_FSYNC
AFTER_RENDER_CANDIDATE_MANIFEST_REPLACE
AFTER_RENDER_CANDIDATE_MANIFEST_DIRECTORY_FSYNC
AFTER_RENDER_CANDIDATE_MANIFEST_VERIFICATION
AFTER_RENDER_FINAL_MANIFEST_TEMP_WRITE
AFTER_RENDER_FINAL_MANIFEST_FILE_FSYNC
BEFORE_RENDER_FINAL_MANIFEST_REPLACE
AFTER_RENDER_FINAL_MANIFEST_REPLACE
AFTER_RENDER_FINAL_MANIFEST_DIRECTORY_FSYNC
```

Keep existing P2A generic Manifest checkpoints unchanged for project/registry compatibility, but use these render-specific checkpoints for candidate/final transitions. Do not reuse one checkpoint name across candidate preparation, final activation or terminal-failure persistence.

- [ ] **Step 8: Extend explicit recovery and orphan reporting**

For running/outcome-unknown render attempts compare this exact triple:

```text
(active_project, active_registry, active_render_state)
```

Valid old state is `(base_project, base_registry, base_render_state)`; valid new state is `(candidate_project, candidate_registry, candidate_render_state)`, where project/registry members are unchanged. A begun attempt with no candidate and old active state is interrupted before preparation. A candidate-prepared attempt with old active state is interrupted before activation and its exact complete artifacts are preserved/reported. New active state means succeeded. Any changed project/registry member, render pointer outside old/new, tampered pointer/file/snapshot, candidate hash mismatch, incomplete candidate or mixed state fails recovery rather than guessing.

Cleanup is bounded to fixed Manifest temp, owned immutable temps and scratch/temp files below `state/render/attempts/<safe-id>/` for non-succeeded attempts. Never delete an active or user output. Preserve and report complete orphan immutable timelines, source receipts, render receipts, render states and outputs; do not activate or GC them. Succeeded attempt scratch is not auto-deleted by recovery unless a separately verified cleanup marker owns it.

- [ ] **Step 9: Add crash injection coverage**

Extend `tests/helpers/p2a_crash_worker.py` and recovery tests with process-level crashes at:

```text
begin attempt Manifest temp / fsync / replace / directory fsync
each artifact or output temp / file fsync / promote / directory fsync / reopen verify
candidate-prepared Manifest temp / file fsync / replace / directory fsync / reopen verify
final Manifest temp / file fsync / replace / directory fsync
```

Separately add one-shot ordinary exception injection tests inside `activate_render_state()`:

```python
@pytest.mark.parametrize(
    "phase",
    [
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_FILE_FSYNC,
        CommitPhase.BEFORE_RENDER_FINAL_MANIFEST_REPLACE,
    ],
)
def test_activation_ordinary_pre_replace_failure_is_internally_terminal_failed(phase): ...

@pytest.mark.parametrize(
    "phase",
    [
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_REPLACE,
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_DIRECTORY_FSYNC,
    ],
)
def test_activation_post_replace_ambiguity_remains_outcome_unknown(phase): ...
```

For each ordinary pre-replace case assert authoritative revision R+3, terminal `FAILED`, `render_phase="activate"`, typed/redacted error, base `active_render_state`, unchanged project/registry, retained candidate pointer/five-artifact hash, no running attempt, and rejection of a stale outer R+1 failure request. Assert the failure writer cleans only its owned final temp and is not reinjected by the one-shot injector. For after-replace/directory-fsync ambiguity assert `PRODUCTION_STATE_OUTCOME_UNKNOWN`, no FAILED overwrite, then explicit recovery resolves only by exact old/new triple.

For every process-level pre-final-replace crash assert old/`None` pointer remains active and project/registry unchanged. Candidate-prepared temp/fsync crashes recover as begun unless the exact replacement is readable; replace/directory-fsync ambiguity must reopen and accept only the exact candidate/hash identity. Recovery performs bounded temp cleanup and preserves/reports every complete orphan. For final replace/directory-fsync ambiguity assert explicit recovery resolves only by exact old/new render pointer plus unchanged pair. Assert revisions `R+1/R+2/R+3`, replay from each stage, replay after recovered success and conflicting attempt-ID rejection.

- [ ] **Step 10: Export the stable lifecycle surface explicitly**

Export from `production/__init__.py`:

```text
BeginRenderAttemptRequest
RecordRenderFailureRequest
ActivateRenderStateRequest
RenderAttemptPaths
RenderArtifactPointer
RenderOutputPointer
RenderStateSnapshot
RenderStateSnapshotPointer
ProductionStateCommitter
```

The public methods are `ProductionStateCommitter.begin_render_attempt()`、`record_render_failure()`、`activate_render_state()` and `render_attempt_paths()`. Keep `_candidate_artifacts_hash`, Manifest transition builders, `CommitPhase`, crash injectors, native file ops, canonical render path constructors/validators, recovery scanners and serialization/cross-validation helpers private to their modules. `hyperframes.py` may export `HyperFramesAdapter` and `render_with_hyperframes()` only after their API tests pass; injected runner protocols/results, materialization structs and redaction/command helpers remain module-private.

- [ ] **Step 11: Run focused GREEN and commit**

```bash
python -m pytest \
  tests/test_production_models.py \
  tests/test_production_project.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
git add src/ai_video/production/paths.py src/ai_video/production/project.py \
  src/ai_video/production/state_commit.py src/ai_video/production/hyperframes.py \
  src/ai_video/production/__init__.py \
  tests/test_production_project.py tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py tests/test_production_hyperframes.py \
  tests/helpers/p2a_crash_worker.py
git commit -m "feat: commit production render state"
```

Expected: selection is durable before any executable call; outer orchestration durably records every ordinary pre-candidate availability/source/lint/check/render/verify failure; `activate_render_state()` alone converts ordinary R+2-to-pre-replace failure into terminal R+3 while retaining candidate/hash and rejects stale outer failure; post-replace ambiguity remains outcome unknown; success `R+1/R+2/R+3` revisions and replay are deterministic; crash recovery preserves complete orphans; 2.0 historical/custom operation loading and existing P2A `commit(StateCommitRequest)` behavior remain unchanged and green.

### Task 6: Run Live Spike and Regression Proof

**Files:**
- Verify: all P3/P2A-owned files
- Verify unchanged: Legacy runtime, public CLI, Manifest v1 and flat layout

- [ ] **Step 1: Reconfirm the authorized live-spike containment**

The user explicitly authorized the live spike on 2026-08-09. Before running it, verify the exact browser revision/path from Task 0, establish an OS boundary that denies and observes external egress while allowing loopback, and use only the committed silent fixture. Dependency/browser installation may use network only before this boundary; the spike itself must fail on any external connection or install attempt. Preview may start local Chrome/server processes and must be stopped cleanly.

- [ ] **Step 2: Run the pinned no-network renderer spike**

Use the already installed exact browser path accepted by the Renderer Gate and run inside the OS boundary. Then set:

```bash
export CI=1
export HYPERFRAMES_NO_TELEMETRY=1
export DO_NOT_TRACK=1
export HYPERFRAMES_NO_UPDATE_CHECK=1
export HYPERFRAMES_NO_AUTO_INSTALL=1
test -n "$P3_HYPERFRAMES_BROWSER_PATH"
test -x "$P3_HYPERFRAMES_BROWSER_PATH"
export HYPERFRAMES_BROWSER_PATH="$P3_HYPERFRAMES_BROWSER_PATH"
```

These variables do not themselves prove offline execution: `HYPERFRAMES_NO_UPDATE_CHECK` does not stop the registry fetch and `HYPERFRAMES_NO_AUTO_INSTALL` does not stop browser download. The spike harness must independently deny/observe external egress and fail if the CLI attempts network or installation.

Run the entire lint/check/preview/curl/render block in one Linux namespace created with `unshare --user --map-root-user --net --pid --fork --mount-proc`; inside it run `ip link set lo up` so only loopback exists and `ps` sees only namespace-owned processes. Wrap HyperFrames/Chrome processes with `strace -ff -e trace=network` into the disposable spike directory and retain the trace as evidence of attempted sockets. If unprivileged user/network/PID namespaces, proc mounting, `ip`, `setsid`, `ps` or `strace` are unavailable, stop: do not fall back to env vars alone or run the live spike on the host network.

Run the exact pinned binary against the committed silent-image fixture copied into a disposable staging directory. The shown body must execute inside that one namespace (including preview and `curl`), with `strace` applied to every HyperFrames command. Start preview in its own namespace-scoped process group and install a trap before launch:

```bash
set -euo pipefail
P3_SPIKE_DIR=$(mktemp -d)
cp -R tests/fixtures/hyperframes/silent_image/. "$P3_SPIKE_DIR/"
strace -ff -e trace=network -o "$P3_SPIKE_DIR/version.net" \
  ./node_modules/.bin/hyperframes --version
strace -ff -e trace=network -o "$P3_SPIKE_DIR/doctor.net" \
  ./node_modules/.bin/hyperframes doctor
strace -ff -e trace=network -o "$P3_SPIKE_DIR/lint.net" \
  ./node_modules/.bin/hyperframes lint "$P3_SPIKE_DIR" --json
strace -ff -e trace=network -o "$P3_SPIKE_DIR/check.net" \
  ./node_modules/.bin/hyperframes check "$P3_SPIKE_DIR" --json

P3_PREVIEW_PID=""
P3_PREVIEW_PGID=""
cleanup_p3_preview() {
  if test -n "$P3_PREVIEW_PGID"; then
    case "$P3_PREVIEW_PGID" in
      *[!0-9]*|0|1) return 1 ;;
    esac
    if test "$P3_PREVIEW_PGID" != "$P3_PREVIEW_PID"; then
      return 1
    fi
    kill -TERM -- "-$P3_PREVIEW_PGID" 2>/dev/null || true
    for _ in {1..50}; do
      kill -0 -- "-$P3_PREVIEW_PGID" 2>/dev/null || break
      sleep 0.1
    done
    if kill -0 -- "-$P3_PREVIEW_PGID" 2>/dev/null; then
      kill -KILL -- "-$P3_PREVIEW_PGID"
    fi
    wait "$P3_PREVIEW_PID" 2>/dev/null || true
    ! kill -0 -- "-$P3_PREVIEW_PGID" 2>/dev/null
  fi
}
trap 'cleanup_p3_preview' EXIT
trap 'cleanup_p3_preview; exit 130' INT
trap 'cleanup_p3_preview; exit 143' TERM
setsid strace -ff -e trace=network -o "$P3_SPIKE_DIR/preview.net" \
  ./node_modules/.bin/hyperframes preview "$P3_SPIKE_DIR" --port 3017 \
  >"$P3_SPIKE_DIR/preview.log" 2>&1 &
P3_PREVIEW_PID=$!
P3_PREVIEW_PGID=$(ps -o pgid= -p "$P3_PREVIEW_PID" | tr -d ' ')
test "$P3_PREVIEW_PGID" = "$P3_PREVIEW_PID"
curl --fail --silent --show-error http://127.0.0.1:3017/ >/dev/null
cleanup_p3_preview
P3_PREVIEW_PID=""
P3_PREVIEW_PGID=""
! ps -eo comm= | rg -q '^(node|chrome|chromium|chrome-headless)'
strace -ff -e trace=network -o "$P3_SPIKE_DIR/render.net" \
  ./node_modules/.bin/hyperframes render "$P3_SPIKE_DIR" \
  -o "$P3_SPIKE_DIR/render.mp4"
strace -ff -e trace=network -o "$P3_SPIKE_DIR/render-repeat.net" \
  ./node_modules/.bin/hyperframes render "$P3_SPIKE_DIR" \
  -o "$P3_SPIKE_DIR/render-repeat.mp4"
```

Expected:

- exact version `0.7.103`;
- doctor reports usable Node/FFmpeg/Chromium;
- lint/check return machine-readable zero-error evidence;
- preview serves the fixture locally; trap cleanup terminates/waits the validated whole process group, escalates only that group if necessary, and proves no preview/Chrome descendant remains before render;
- render creates a non-empty local MP4 with measured width/height/FPS/frame duration matching `ResolvedTimeline`;
- source/asset hashes do not change;
- no registry/update/install/browser-download/cloud/telemetry egress is attempted or launched;
- repeated render is frame-equivalent by sampled frame hashes or decoded-frame comparison, while MP4 byte hashes may differ.

If `check` incompatibility, Chrome download need, remote fetch, telemetry/update attempt, timing mismatch, source mutation or non-equivalent decoded frames appears, stop P3 implementation and return to Renderer Gate. Do not weaken the contract or substitute Remotion.

After the isolated fixture spike passes, run one fake-runner-backed end-to-end lifecycle test through `render_with_hyperframes()` using `render_attempt_paths()` to prove the same begin -> source/lint/check/render/verify -> activate ordering without adding a second live render or bypassing `ProductionStateCommitter`.

- [ ] **Step 3: Run focused P3 tests**

```bash
python -m pytest \
  tests/test_production_models.py \
  tests/test_production_project.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
```

Expected: all P3/P2A tests pass with no P3 skip in the default fake suite.

- [ ] **Step 4: Run Legacy regression tests**

```bash
python -m pytest \
  tests/test_config.py tests/test_cli.py tests/test_manifest.py \
  tests/test_pipeline.py tests/test_resume_e2e.py \
  tests/test_workflow_loader.py tests/test_workflow_renderer.py \
  tests/test_ffmpeg_tools.py -q
```

Expected: Legacy public commands, config/workflow loading, Manifest v1, resume, FFmpeg helpers and flat layout remain unchanged.

- [ ] **Step 5: Run the full default no-network suite**

```bash
python -m pytest -q
```

Expected: exit `0`; existing optional skip may remain, but P3 fake tests do not skip or require installed HyperFrames.

- [ ] **Step 6: Verify scope and dependency pin**

```bash
git diff --check
git status --short
p3_base_commit=$(git merge-base HEAD main)
git diff --name-only "$p3_base_commit"..HEAD
npm ls hyperframes --depth=0
rg -n "npx|@latest|remotion|fetch\(|XMLHttpRequest|WebSocket|Math\.random|Date\.now|performance\.now" \
  src/ai_video/production tests/test_production_*.py tests/fixtures/hyperframes package.json
```

Expected: changed files match the exact map; runtime calls use the pinned local binary; forbidden source/runtime behaviors appear only in negative tests or explicit denial text.

- [ ] **Step 7: Record the proof bundle**

Record exact dependency/browser versions, namespace/trace evidence, lint/check JSON hashes, preview cleanup assertion, both output measurements/frame fingerprints, focused/Legacy/full pytest results and scope diff. Task 7 may use only this completed proof to write runtime truth.

### Task 7: Synchronize Verified Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/v0.2-runtime-baseline.md`
- Modify: `docs/v0.2-agentic-production-roadmap.md`
- Modify: `docs/agent-primary-contract-matrix.md`

- [ ] **Step 1: Document only verified P3 behavior**

Only after every Task 6 spike/focused/Legacy/full/scope check passes, document:

- importable `CompositionSpec`/`resolve_composition()`/HyperFrames adapter and stable lifecycle API;
- accepted strategies in this slice and explicit blocked strategies;
- `ResolvedTimeline` as only order/timing truth;
- exact pinned tool/browser versions and one-renderer-per-attempt rule;
- source hash/lint/check and render receipt fields;
- Manifest 2.0/2.1 compatibility, candidate-prepared transition, pre-candidate outer failure versus post-candidate activation-owned failure, one active render-state pointer, canonical immutable layout and P2A-owned recovery behavior;
- fake/no-network CI versus the explicitly authorized, egress-contained live spike;
- P4/P5/P6/P7/P8 remain unimplemented.

Do not claim byte-identical MP4, cloud readiness, Audio/Caption support, selective rebuild, new CLI or Legacy migration.

- [ ] **Step 2: Add the completed focused command to the contract matrix**

```bash
python -m pytest \
  tests/test_production_models.py \
  tests/test_production_project.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
```

- [ ] **Step 3: Scan claims and commit**

```bash
rg -n "P3|CompositionSpec|ResolvedTimeline|HyperFrames|Remotion|byte-identical|Audio|Caption|P5|Provider" \
  README.md docs/v0.2-runtime-baseline.md docs/v0.2-agentic-production-roadmap.md \
  docs/agent-primary-contract-matrix.md
git add README.md docs/v0.2-runtime-baseline.md \
  docs/v0.2-agentic-production-roadmap.md docs/agent-primary-contract-matrix.md
git commit -m "docs: document p3 composition runtime"
```

Expected: docs use the completed Task 6 evidence and describe only tested local behavior; every future capability remains planned/not implemented.

### Task 8: Obtain Final Independent Review and Record Branch Truth

- [ ] **Step 1: Obtain independent review after docs**

Review brief:

```text
Verdict must be accept, accept with concerns, or reject.
Verify P3 started from accepted P2A and did not add a second writer/Manifest.
Verify CompositionSpec is edit intent and ResolvedTimeline is the only order/timing owner.
Verify integer frame/sample boundaries, exact asset IDs/hashes, trim, transform,
opacity, z-order, transitions, delivery profile, renderer identity and fingerprint.
Verify selection persists before execution and all ordinary post-begin failures persist.
Verify candidate-prepared state is durable before the final single-pointer switch.
Verify outer orchestration never writes stale failure after activation takes R+2 ownership.
Verify activation internally terminals ordinary pre-replace failure but preserves outcome unknown after replace ambiguity.
Verify exact replay/recovery and P2A 2.0 custom-operation compatibility.
Verify HyperFrames source comes only from timeline/assets and is hash/lint/check audited.
Verify one attempt selects exactly one renderer and no Remotion/fallback/double render exists.
Verify fake/no-network defaults, preview process-group cleanup, atomic ordering and rollback.
Verify docs match Task 6 evidence and frame-equivalent proof is not byte-identical claim.
Verify Legacy CLI/Manifest/layout and P4/P5/P2A/Provider boundaries remain unchanged.
```

Required exit verdict: `accept` or `accept with concerns` with no blocking issue. The parent must inspect important claims, final diff and commands directly. Any review fix must rerun its affected Task 6 proof and rescan Task 7 docs before acceptance.

- [ ] **Step 2: Record final branch truth**

```bash
git status --short --branch
git log --oneline --decorate -15
git rev-list --left-right --count origin/main...HEAD
```

Expected: clean task branch/worktree and explicit local-vs-origin state. Do not claim push, merge or release without evidence.

## Failure and Rollback

Failure handling:

- schema/resolution failure before `begin_render_attempt()`: no external command and no state commit;
- selection is persisted by `begin_render_attempt()` before version/source/lint/check/render; wrong version, plain `RENDERER_UNAVAILABLE` and source exceptions are normalized to phase `source`, durably failed, then re-raised;
- lint failure: stop before `check`/render and persist the exact typed failed phase through `record_render_failure()`;
- check failure: stop before render and persist the exact typed failed phase through `record_render_failure()`;
- render/timeout/output verification failure: persist the typed phase and leave `active_render_state` old/`None`;
- before candidate preparation, outer `render_with_hyperframes()` owns exactly one `record_render_failure()` write from R+1; after R+2 candidate preparation it never catches activation merely to retry that stale request;
- candidate-prepared Manifest persists the exact candidate/hash while leaving active/project/registry pointers unchanged; `activate_render_state()` internally converts every ordinary final-temp/file-fsync/pre-replace failure into terminal R+3 failed with candidate identity retained;
- crash before final Manifest replace: explicit P2A recovery distinguishes begun from candidate-prepared, owns bounded temp cleanup, preserves/reports complete immutable orphans and keeps the old render pointer;
- final replace/directory-fsync/post-replace ambiguity is `PRODUCTION_STATE_OUTCOME_UNKNOWN`, never overwritten by failed; recovery validates the candidate render pointer plus unchanged project/registry pair and reads exact manifest-selected snapshot/artifact/output hashes, not console or Agent memory;
- renderer mismatch/unavailable: fail explicitly; no HyperFrames-to-Remotion or Remotion-to-HyperFrames retry.

Rollback is commit-based and must preserve user project artifacts:

```bash
git revert "$(git log -1 --format=%H --grep='^docs: document p3 composition runtime$')"
git revert "$(git log -1 --format=%H --grep='^feat: commit production render state$')"
git revert "$(git log -1 --format=%H --grep='^feat: add hyperframes renderer adapter$')"
git revert "$(git log -1 --format=%H --grep='^feat: materialize audited hyperframes sources$')"
git revert "$(git log -1 --format=%H --grep='^feat: resolve deterministic production timelines$')"
git revert "$(git log -1 --format=%H --grep='^feat: add composition and render contracts$')"
git revert "$(git log -1 --format=%H --grep='^build: pin hyperframes renderer tool$')"
```

Do not delete `projects/**`, accepted P2A snapshots, receipts or user renders during rollback. A separate explicit P2A GC policy decides when orphaned immutable artifacts may be reclaimed.

## Acceptance Criteria

P3 is accepted only when:

1. accepted P2A exists; `ProductionStateCommitter` remains the only durable write/pointer-switch/recovery owner, existing project/registry commit and non-empty operation compatibility are unchanged, and Manifest 2.0/2.1 read compatibility is proven without rewrite;
2. `CompositionSpec` captures explicit edit intent without filesystem discovery;
3. `ResolvedTimeline` is the only order/timing/layer truth and contains integer frame/sample boundaries;
4. asset ID/hash, trim, transform, opacity, z-order, transition, delivery profile, renderer kind/version and deterministic composition fingerprint are persisted in the contract;
5. identical resolved inputs produce identical timeline/source hashes and frame-equivalent output under the pinned tool/runtime;
6. no byte-identical MP4 claim is made without a separately proven encoder/container contract;
7. source is materialized only from timeline/registered assets, then hashed, linted and checked;
8. source contains no wall-clock randomness, implicit network fetch, remote URL or untracked asset;
9. each attempt has one renderer selection and one HyperFrames execution path;
10. Remotion is neither installed nor implemented and no double-render/fallback exists;
11. one immutable `RenderStateSnapshot` contains exact selection and timeline/source/render/output pointers, cross-validates all identities, and one Manifest pointer activates it;
12. selection is durable before any executable call; outer orchestration records every ordinary pre-candidate availability/source/lint/check/render/verify exception exactly once, then never submits a stale R+1 failure after activation takes ownership;
13. candidate-prepared state/hash is durably reopened at R+2; `activate_render_state()` internally writes terminal R+3 failed for ordinary final-temp/file-fsync/pre-replace failure while preserving base active pointer/candidate/hash, but final replace/directory-fsync ambiguity remains outcome unknown; successful `R+1/R+2/R+3` revisions, exact replay and recovery use unchanged project/registry pair;
14. complete orphan artifacts/output are preserved and reported; default tests are fake/no-network and the authorized real spike uses the pinned browser with OS-level external-egress denial/observation plus process-group/descendant cleanup proof;
15. no Audio/Caption, P5 graph, Provider/cloud/paid API, new CLI or Legacy schema/layout enters the diff;
16. focused P3/P2A, Legacy regression and full default suites pass;
17. docs are written only after live/focused/Legacy/full proof, then final independent review has no blocker.

## Plan-Time Known Blockers

- **Plan drafting / receipt contract:** none; the user selected the versioned `RenderStateSnapshot` approach and authorized this in-place revision on 2026-08-09.
- **P2A prerequisite:** satisfied on local `main`; it is not a P3 blocker.
- **P3 runtime execution:** authorized. Task 0 must still fail closed on an exact package integrity/source/browser mismatch, unavailable OS egress containment or conflicting workspace ownership; these are verification failures, not missing authorization.
- **Renderer offline gate:** env controls are necessary but insufficient; the live spike must prove external egress denial/observation, loopback-only preview and explicit preinstalled `HYPERFRAMES_BROWSER_PATH`.

## Execution Authorization Boundary

The user explicitly authorized P3 runtime execution on 2026-08-09 with: (a) one versioned `RenderStateSnapshot` selected by `ProductionManifest.active_render_state`; and (b) the full Renderer Gate, including exact `hyperframes@0.7.103`, necessary matching Chromium installation and an OS-egress-contained live lint/check/preview/render spike. Implementation must follow Tasks 0-8 and stop on verification failure or scope conflict. The authorization does not allow `npx` runtime resolution, another HyperFrames version/integrity, Remotion, Audio/Caption, P5+, Provider/cloud/paid API, new CLI, Legacy schema/layout changes, arbitrary network during the spike, push, merge or release.
