# AI-VIDEO Agentic Production Harness P3 Deterministic Composition and HyperFrames Adapter Implementation Plan

> **For agentic workers:** 实施本 plan 时，REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans。按 Task 顺序执行，并使用 checkbox (`- [ ]`) 跟踪进度。

**Goal:** 在 accepted P2A state commit protocol 之上，实现 renderer-neutral `CompositionSpec`、唯一 order/timing owner `ResolvedTimeline`、exclusive HyperFrames adapter、durable renderer source bundle/receipt 和 render receipt，并以 local raster + cut-only silent fixture 证明 deterministic composition。

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

本 slice 只验收已有 registered local PNG/JPEG/WebP raster image assets 的 `STATIC_IMAGE`、`CUT`-only silent composition。`image_motion`、`motion_graphics`、`generated_video`、`existing_video`（source video）和 `hybrid` 均显式以 `COMPOSITION_INVALID` 拒绝；它不生成素材，不接受 motion directives，不引入 voice/caption/audio tracks，不实现 P5 selective dependency invalidation，也不通过新 CLI 暴露 v2 runtime。

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
| renderer source | `hyperframes.py::materialize_hyperframes_source()` output + durable source bundle + `RendererSourceReceipt` | source 必须完全由 timeline/assets materialize；scratch 不进入 semantic identity，canonical HTML/raster bytes 必须随 render state 持久化，不能 scan filesystem 决策 |
| render execution | public `render_with_hyperframes()` + private `_NetworkIsolatedHyperFramesRunner` | `HyperFramesAdapter` 仅为 module-internal/test phase seam；每个 tool process 必须 fresh namespace，package caller 不能注入 runner、host fallback、alternate renderer 或 double render |
| durable project/registry transaction | `state_commit.py::ProductionStateCommitter.commit(StateCommitRequest)` | 现有 P2A request/replay owner 保持；2.1 pair 改变时同一 commit blanket-clear `active_render_state`，same-pair 仅在完整 provenance 验证后保留；P3 render operation 不借用或改写该 pair |
| render attempt lifecycle | `ProductionStateCommitter.begin_render_attempt()` / `record_render_failure()` / `activate_render_state()` | `record_render_failure()` 只拥有外层尚未调用 activation 的 R+1 ordinary failure；`activate_render_state()` 从方法调用入口起独占 candidate transition、final activation 与它们的 failure/ambiguity ownership。它们不是 `commit()` alias wrapper；不得增加第二 writer 或 Manifest |
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

- `CompositionSpec`: ordered `shot_ids`、exact `(asset_role, asset_id)` bindings、visual layer/edit intent、fixed-point transform、fixed-point opacity、z-order、cut transition、delivery profile 和 requested renderer。既有 trim fields 在本 slice 只允许 `trim_start_frame=0`/`trim_duration_frames=None`，非默认值 typed-fail。
- `ResolvedTimeline`: width/height/FPS/codec profile、sample rate、integer `start_frame`/`duration_frames`、integer `start_sample`/`duration_samples`、asset ID/hash/materialized path、default-only trim fields、transform、opacity、z-order、transition、total frames/samples、renderer kind/version 和 `composition_fingerprint`。
- duration resolution: P3 silent fixture 只接受 `DurationPolicy.mode == "fixed"`；使用 `Decimal(str(seconds))`，`ROUND_CEILING` 到整数 frame，绝不使用 binary float 累加。
- sample boundaries: `start_sample = floor(start_frame * sample_rate / fps)`，`end_sample = floor(end_frame * sample_rate / fps)`，duration 是两者之差。P3 只建立 timebase，不创建 audio track。
- transition resolution: 本 slice 只接受 `cut` 且 `duration_frames == 0`；`crossfade` 和任何 overlap 均以 `COMPOSITION_INVALID` 拒绝。
- composition fingerprint: 对 fully resolved timeline projection 做 stable JSON + SHA-256，排除 self hash、receipt timestamp、absolute staging path 和 wall-clock data。
- source receipt: renderer kind/version、timeline fingerprint、canonical source-bundle root/index path/hash、exact raster bindings/paths/hashes、lint/check command identity、exit status 和 output evidence hashes；attempt scratch path 不入 receipt。
- render receipt: attempt ID、renderer/tool version、timeline fingerprint、source-bundle hash、asset hashes、final canonical durable `state/render/outputs/<full-output-sha256>.mp4` path/hash/size、measured width/height/FPS/frame count/codec 和 result status。

### Manifest and Render-State Migration

- `ProductionManifest.schema_version` 接受 `"2.0"` 和 `"2.1"`。`2.0` 只允许 `active_render_state=None` 且 `attempts` 中不得有 render operation；首次 `begin_render_attempt()` 用一次 durable Manifest replace 迁移为 `2.1`。迁移不 backfill、rewrite 或 reseal 任何 immutable P2/P2A project/registry snapshot。
- `2.1` 增加 `active_render_state: RenderStateSnapshotPointer | None = None`。P2 `load_production_project()` 保持 read-only/no-network，同时接受 2.0/2.1；当 pointer 不为 `None` 时必须校验其 contained canonical path、file hash、snapshot semantic identity 与 cross references，不激活、不修复。
- `RenderStateSnapshotPointer` 含 `path`、`revision`、`content_hash`、`file_sha256`；canonical path 是 `state/render/states/<full-content-hash>.json`，禁止 alias、`current` symlink 和 truncated hash filename。
- `RenderArtifactPointer` 含 `path`、`revision`、`content_hash`、`file_sha256`，用于 exact `ResolvedTimeline`、`RendererSourceReceipt` 和 `RenderReceipt`。`RenderOutputPointer` 含 exact `path`、`file_sha256`、`size_bytes`。
- immutable sealed `RenderStateSnapshot(VersionedArtifact)` 含 `attempt_id`、render 所依据的 exact active project/registry pointers、exact `RendererSelectionReceipt`、duplicated renderer/timeline/source-bundle/asset identities、`timeline`、`source_bundle`、`source_receipt`、`render_receipt`、`output`。model validator 校验 embedded selection，reader/committer 加载 exact pointers 后 cross-validate 同一 attempt ID、project/registry、renderer kind/version、timeline fingerprint、source-bundle/index hash、ordered asset hashes 和 output path/hash/size；任一 mixed/tampered identity 失败。
- `RendererSelectionReceipt` 是 attempt ID、`timeline_fingerprint`、当前 active project pointer 和当前 active registry pointer 的唯一 authoritative identity source；`BeginRenderAttemptRequest` 只增加 expected revision、base render pointer 并引用该 selection，不重复这些字段。Exact replay 必须逐项相同，不能只靠 renderer name。
- 对 2.1 Manifest，既有 `commit(StateCommitRequest)` 若切换 project 或 registry pointer，必须在同一次 atomic Manifest replace 中将 `active_render_state` 清为 `None`；这是 P3 的 blanket render invalidation，不是 P5 graph。旧 immutable render/source/output artifacts 保留为 orphan evidence。若 pair 完全相同，只有在重新验证当前 render snapshot 与其 project/registry provenance 仍一致后才可保留 pointer，否则 typed-fail，不得猜测或静默清理。

### Canonical Durable Layout

```text
state/render/timelines/<full-content-hash>.json
state/render/sources/<full-source-bundle-sha256>/index.html
state/render/sources/<full-source-bundle-sha256>/assets/<full-asset-sha256>.<png|jpg|webp>
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
- `tests/fixtures/hyperframes/silent_image/source/assets/431ced6916a2a21a156e38701afe55bbd7f88969fbbfc56d7fe099d47f265460.png`
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
| 0 | accepted P2A fact check + exact dependency/browser install + disposable compatibility spike before runtime edits | prerequisites/Renderer Gate | `build: pin hyperframes renderer tool` |
| 1 | strict composition/timeline/receipt/render-state schema + 2.0/2.1 model compatibility | `models.py` | `feat: add composition and render contracts` |
| 2 | exact frame/sample resolution, fingerprint and shared no-follow file reads | `composition.py` + `paths.py` | `feat: resolve deterministic production timelines` |
| 3 | pure caller-supplied contained source materialization + raster/URL audit | `hyperframes.py` source layer | `feat: materialize audited hyperframes sources` |
| 4 | fake lint/check/render, exact namespace argv and typed receipts | private runner + module-internal `HyperFramesAdapter` boundary | `feat: add hyperframes renderer adapter` |
| 5 | canonical attempt paths + durable source bundle/output + provenance/invalidation + orchestration/activation/replay/recovery | `project.py` + `hyperframes.py` + `ProductionStateCommitter` + P2A tests | `feat: commit production render state` |
| 6 | committed-fixture integration proof + focused/P2A/Legacy/full regression proof (not the prerequisite gate) | verification | no commit unless correction is required |
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
./node_modules/.bin/hyperframes --help | rg '(^|[[:space:]])doctor([[:space:]]|$)'
npm ls hyperframes --depth=0
node -e 'const l=require("./package-lock.json"); const p=l.packages["node_modules/hyperframes"]; if (p.version!=="0.7.103" || p.integrity!=="sha512-+E+CXuBiHgd6Rae/BltrErJGr0PtC/AL5uHXm6ZN77ziERtIFJvqaJveWDmJ4PH6UEJ/lf3Cqxuv8GpATt4Ljw==") process.exit(1)'
```

Expected: version is exactly `0.7.103`, the exact installed CLI advertises `doctor`, and `package-lock.json` contains one exact top-level pin matching the recorded registry integrity. If `doctor` is absent, stop before invoking it or editing Task 1. Do not use `npx hyperframes`, `@latest`, caret or range resolution in runtime commands.

- [ ] **Step 5: Preinstall the exact required browser and pin its executable path**

Inspect the installed `0.7.103` source before any browser download. If it confirms Chrome Headless Shell `152.0.7928.2`, run the locked installer exactly:

```bash
./node_modules/.bin/browsers install chrome-headless-shell@152.0.7928.2 \
  --path .hyperframes/browser-cache
./node_modules/.bin/browsers list --path .hyperframes/browser-cache
```

Record the listed executable as `P3_HYPERFRAMES_BROWSER_PATH`, require `test -x`, and verify the binary reports `152.0.7928.2`. If the source-required revision differs, the locked installer binary is absent, or the resolved binary reports another version, stop and revise this plan before download/render. Network is allowed for this dependency/browser installation step only; no render source or user asset may be present.

Do not rely on HyperFrames auto-download. Every live `check`/`preview`/`render` command must set `HYPERFRAMES_BROWSER_PATH` to the verified executable and set `HYPERFRAMES_NO_AUTO_INSTALL=1`.

- [ ] **Step 6: Run the prerequisite disposable Renderer compatibility spike**

This is the Renderer Gate and must pass **before Task 1 edits**. It uses a disposable hand-authored local PNG composition, not the future Task 3 committed fixture. First verify `unshare --user --map-root-user --net --pid --fork --mount-proc`, `ip`, `strace`, `setsid`, `curl`, `ffprobe`, `ffmpeg`, `sha256sum` and process-group cleanup are available; otherwise stop. The exact published `0.7.103` source/CLI help must confirm `doctor` exists before invoking it.

Create a fresh `P3_GATE_DIR=$(mktemp -d)` outside the repository, write a known valid minimal PNG by decoding a reviewed fixed base64 literal, verify PNG magic bytes and `image/png`, and hand-author `index.html` with only that relative PNG, `320x180`, `24` FPS and `48` frames. Record input hashes before the namespace:

```bash
P3_GATE_DIR=$(mktemp -d)
P3_GATE_SOURCE="$P3_GATE_DIR/source"
P3_GATE_EVIDENCE="$P3_GATE_DIR/evidence"
mkdir -p "$P3_GATE_SOURCE/assets" "$P3_GATE_EVIDENCE"
printf '%s' 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=' \
  | base64 -d >"$P3_GATE_SOURCE/assets/gate.png"
printf '%s\n' \
  '<!doctype html>' \
  '<html><head><meta charset="utf-8"><style>html,body{margin:0;width:100%;height:100%;overflow:hidden}.clip{position:absolute;inset:0;z-index:0;opacity:1}.clip img{width:100%;height:100%;object-fit:cover;transform:translate(0px,0px) scale(1,1) rotate(0deg);transform-origin:0 0}</style></head>' \
  '<body><div id="stage" data-composition-id="p3-gate" data-timeline-fingerprint="0000000000000000000000000000000000000000000000000000000000000000" data-width="320" data-height="180" data-fps="24" data-start="0" data-duration="2">' \
  '<div class="clip" data-shot-id="gate-shot" data-start-frame="0" data-duration-frames="48" data-transition-kind="cut" data-transition-frames="0"><img src="assets/gate.png" alt=""></div>' \
  '</div></body></html>' >"$P3_GATE_SOURCE/index.html"
test "$(od -An -tx1 -N8 "$P3_GATE_SOURCE/assets/gate.png" | tr -d ' \n')" = "89504e470d0a1a0a"
test "$(file --brief --mime-type "$P3_GATE_SOURCE/assets/gate.png")" = "image/png"
sha256sum "$P3_GATE_SOURCE/index.html" "$P3_GATE_SOURCE/assets/gate.png" >"$P3_GATE_EVIDENCE/input.before.sha256"
```

Run version/doctor/lint/check/render through the exact per-command namespace argv contract later implemented by `_NetworkIsolatedHyperFramesRunner`: every invocation creates a fresh namespace and uses the fixed `exec "$@"` wrapper, with no host fallback. Substitute only already verified absolute paths. Preview uses the same outer wrapper to exec a companion in-namespace supervisor because readiness curl and cleanup must share its loopback; preview remains Renderer-Gate-only and is never part of the production runner surface.

```bash
P3_UNSHARE=$(command -v unshare)
P3_IP_PATH=$(command -v ip)
P3_BASH=$(command -v bash)
P3_BINARY="$PWD/node_modules/.bin/hyperframes"
test -x "$P3_UNSHARE" && test -x "$P3_IP_PATH" && test -x "$P3_BASH"
test -x "$P3_BINARY" && test -x "$P3_HYPERFRAMES_BROWSER_PATH"
test ! -L "$P3_HYPERFRAMES_BROWSER_PATH"
export P3_GATE_DIR P3_GATE_SOURCE P3_GATE_EVIDENCE P3_HYPERFRAMES_BROWSER_PATH P3_IP_PATH
export CI=1 HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1
export HYPERFRAMES_NO_UPDATE_CHECK=1 HYPERFRAMES_NO_AUTO_INSTALL=1
export HYPERFRAMES_BROWSER_PATH="$P3_HYPERFRAMES_BROWSER_PATH"

p3_isolated_exec() {
  trace_prefix=$1
  shift
  strace -ff -e trace=network -o "$trace_prefix" \
    "$P3_UNSHARE" --user --map-root-user --net --pid --fork --mount-proc \
    "$P3_BASH" -ceu '"$P3_IP_PATH" link set lo up; exec "$@"' \
    p3-hyperframes "$@"
}

p3_isolated_exec "$P3_GATE_EVIDENCE/version.net" \
  "$P3_BINARY" --version 2>&1 | tee "$P3_GATE_EVIDENCE/version.txt"
test "$(tail -n1 "$P3_GATE_EVIDENCE/version.txt")" = "0.7.103"
p3_isolated_exec "$P3_GATE_EVIDENCE/doctor.net" \
  "$P3_BINARY" doctor 2>&1 | tee "$P3_GATE_EVIDENCE/doctor.txt"
rg -qi 'chrom(e|ium)|browser' "$P3_GATE_EVIDENCE/doctor.txt"
p3_isolated_exec "$P3_GATE_EVIDENCE/lint.net" \
  "$P3_BINARY" lint "$P3_GATE_SOURCE" --json >"$P3_GATE_EVIDENCE/lint.json"
p3_isolated_exec "$P3_GATE_EVIDENCE/check.net" \
  "$P3_BINARY" check "$P3_GATE_SOURCE" --json >"$P3_GATE_EVIDENCE/check.json"

strace -ff -e trace=network -o "$P3_GATE_EVIDENCE/preview.net" \
  "$P3_UNSHARE" --user --map-root-user --net --pid --fork --mount-proc \
  "$P3_BASH" -ceu '"$P3_IP_PATH" link set lo up; exec "$@"' \
  p3-hyperframes-preview-supervisor \
  "$P3_BASH" -ceu '
    preview_pid=
    cleanup() {
      test -z "${preview_pid:-}" && return 0
      kill -TERM -- "-$preview_pid" 2>/dev/null || true
      for _ in 1 2 3 4 5; do kill -0 "$preview_pid" 2>/dev/null || break; sleep 1; done
      kill -KILL -- "-$preview_pid" 2>/dev/null || true
      wait "$preview_pid" 2>/dev/null || true
    }
    trap cleanup EXIT INT TERM
    setsid "$1" preview "$2" --port 3017 >"$3" 2>&1 & preview_pid=$!
    ready=0
    for _ in 1 2 3 4 5 6 7 8 9 10; do curl -fsS http://127.0.0.1:3017/ >/dev/null && ready=1 && break; sleep 1; done
    test "$ready" -eq 1
    cleanup
    preview_pid=
    ! ps -eo args= | grep -E "[h]yperframes preview|[c]hrome-headless-shell"
  ' p3-preview "$P3_BINARY" "$P3_GATE_SOURCE" "$P3_GATE_EVIDENCE/preview.log"

p3_isolated_exec "$P3_GATE_EVIDENCE/render-1.net" \
  "$P3_BINARY" render "$P3_GATE_SOURCE" -o "$P3_GATE_EVIDENCE/render-1.mp4"
p3_isolated_exec "$P3_GATE_EVIDENCE/render-2.net" \
  "$P3_BINARY" render "$P3_GATE_SOURCE" -o "$P3_GATE_EVIDENCE/render-2.mp4"
test -s "$P3_GATE_EVIDENCE/render-1.mp4"
test -s "$P3_GATE_EVIDENCE/render-2.mp4"
```

Afterward, hash the original `index.html` and PNG again and compare to their recorded pre-run hashes. Parse every `*.net*` trace and fail if a `connect`/`sendto`/`sendmsg` destination uses `AF_INET`/`AF_INET6` without exact loopback `127.0.0.1` or `::1`; `AF_UNIX` is allowed and ignored. Do not treat a failed network syscall as safe merely because it failed:

```bash
sha256sum "$P3_GATE_SOURCE/index.html" "$P3_GATE_SOURCE/assets/gate.png" >"$P3_GATE_EVIDENCE/input.after.sha256"
diff -u "$P3_GATE_EVIDENCE/input.before.sha256" "$P3_GATE_EVIDENCE/input.after.sha256"
if rg -n 'connect\(|sendto\(|sendmsg\(' "$P3_GATE_EVIDENCE"/*.net* \
  | rg 'AF_INET6?' | rg -v '127\.0\.0\.1|\[::1\]|inet_pton\(AF_INET6, "::1"'; then
  echo 'non-loopback network destination observed' >&2
  exit 1
fi
python - "$P3_GATE_EVIDENCE/lint.json" "$P3_GATE_EVIDENCE/check.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    lint = json.load(handle)
assert int(lint["errorCount"]) == 0
with open(sys.argv[2], encoding="utf-8") as handle:
    check = json.load(handle)
assert check["ok"] is True
for section in ("lint", "runtime", "layout", "motion", "contrast"):
    assert int(check[section]["errorCount"]) == 0
PY
ffprobe -v error -show_streams -show_format -of json "$P3_GATE_EVIDENCE/render-1.mp4" >"$P3_GATE_EVIDENCE/probe-1.json"
ffprobe -v error -show_streams -show_format -of json "$P3_GATE_EVIDENCE/render-2.mp4" >"$P3_GATE_EVIDENCE/probe-2.json"
python - "$P3_GATE_EVIDENCE/probe-1.json" "$P3_GATE_EVIDENCE/probe-2.json" <<'PY'
import json, sys
for name in sys.argv[1:]:
    with open(name, encoding="utf-8") as handle:
        data = json.load(handle)
    video = [s for s in data["streams"] if s.get("codec_type") == "video"]
    audio = [s for s in data["streams"] if s.get("codec_type") == "audio"]
    assert len(video) == 1 and not audio
    stream = video[0]
    assert (int(stream["width"]), int(stream["height"])) == (320, 180)
    assert stream["r_frame_rate"] == "24/1"
    assert int(stream["nb_frames"]) == 48
PY
ffmpeg -v error -i "$P3_GATE_EVIDENCE/render-1.mp4" -map 0:v:0 -f framemd5 "$P3_GATE_EVIDENCE/render-1.framemd5"
ffmpeg -v error -i "$P3_GATE_EVIDENCE/render-2.mp4" -map 0:v:0 -f framemd5 "$P3_GATE_EVIDENCE/render-2.framemd5"
diff -u "$P3_GATE_EVIDENCE/render-1.framemd5" "$P3_GATE_EVIDENCE/render-2.framemd5"
```

Record browser/Node/FFmpeg versions and keep the disposable directory as gate evidence. Any source mutation, non-loopback destination, doctor/check incompatibility, preview leak, metadata mismatch or frame mismatch stops before Task 1; do not weaken the gate or substitute another renderer.

- [ ] **Step 7: Ignore only local install/scratch output**

Append to `.gitignore`:

```gitignore
node_modules/
.hyperframes/
```

- [ ] **Step 8: Commit the dependency lock only after the compatibility spike passes**

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
            timeline_fingerprint="a" * 64,
            current_project=make_project_pointer(),
            current_registry=make_registry_pointer(),
        )


def test_manifest_20_rejects_render_state_and_render_attempts(): ...


def test_manifest_20_preserves_historical_custom_nonempty_operation_without_rewrite(): ...


def test_manifest_21_accepts_none_or_one_render_state_pointer(): ...


def test_render_state_snapshot_rejects_mixed_attempt_renderer_timeline_source_asset_or_output_identity(): ...


def test_composition_layer_requires_exact_declared_asset_role_and_id(): ...


def test_render_receipt_requires_canonical_durable_output_path(): ...


def test_render_state_snapshot_fixes_project_registry_and_source_bundle_provenance(): ...


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
    asset_role: str = Field(min_length=1)
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
    asset_role: str
    asset_id: str
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_mime_type: Literal["image/png", "image/jpeg", "image/webp"]
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
    timeline_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    current_project: ProjectSnapshotPointer
    current_registry: RegistrySnapshotPointer


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
    asset_mime_type: Literal["image/png", "image/jpeg", "image/webp"]
    materialized_path: Path


class RenderSourceFilePointer(StrictModel):
    path: Path
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0)


class RenderSourceBundlePointer(StrictModel):
    root_path: Path
    bundle_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    index: RenderSourceFilePointer
    assets: tuple[RenderSourceFilePointer, ...] = Field(min_length=1)


class RendererSourceReceipt(VersionedArtifact):
    attempt_id: str
    renderer: RendererIdentity
    timeline_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_bundle: RenderSourceBundlePointer
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")  # exact index hash
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
    source_bundle_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_hashes: tuple[str, ...] = Field(min_length=1)
    output_path: Path  # canonical state/render/outputs/<full sha256>.mp4
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
    project: ProjectSnapshotPointer
    registry: RegistrySnapshotPointer
    renderer_selection: RendererSelectionReceipt
    renderer: RendererIdentity
    timeline_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_bundle_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_hashes: tuple[str, ...] = Field(min_length=1)
    timeline: RenderArtifactPointer
    source_bundle: RenderSourceBundlePointer
    source_receipt: RenderArtifactPointer
    render_receipt: RenderArtifactPointer
    output: RenderOutputPointer


class RenderStateSnapshotPointer(StrictModel):
    path: Path
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
```

`RenderStateSnapshot` model validator loads no files; it cross-validates selection attempt ID, project/registry pointers, timeline fingerprint and renderer kind/version against the duplicated snapshot identities. `project.py`/`state_commit.py` load the exact pointed timeline/source bundle/source receipt/render receipt/output and cross-validate them against the snapshot's one `attempt_id`, active project/registry provenance, renderer, timeline fingerprint, source/index/bundle hashes, ordered asset hashes and canonical output path/hash/size. No field is inferred from directory contents.

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

Preserve P2A compatibility: persisted `StateCommitAttempt.operation` remains the historical non-empty `str`, not a new `Literal`. Existing `commit(StateCommitRequest)` keeps accepting/persisting its already accepted non-empty operation values and must load a valid 2.0 Manifest containing a historical/custom operation unchanged. On a 2.1 Manifest it also owns blanket render invalidation: a changed project or registry pointer clears `active_render_state` in that same commit; a same-pair commit may retain it only after exact render-state/provenance verification. Only the new P3 lifecycle methods write and require exact `operation="render_state"`; attempts with that operation must satisfy `base_project == candidate_project == manifest.active_project` and `base_registry == candidate_registry == manifest.active_registry`. `base_render_state` is the pointer observed at begin. A plain begun attempt and outer pre-activation terminal failure have no candidate and use the canonical empty prepared-artifact hash. Once `activate_render_state()` is called, either a running candidate-prepared attempt or an activation-owned terminal failure must retain the request's exact `candidate_render_state` and aggregate identity hash of the variable exact artifact set, even if candidate Manifest replace was never attempted. Reject render fields on any non-render operation and reject mixed candidate state. A 2.0 Manifest rejects render fields/`render_state` attempts but continues accepting historical non-render operation strings; a 2.1 Manifest allows no active render yet. Reading does not rewrite either version or immutable P2/P2A snapshots.

Receipt timestamps are intentionally absent from semantic fingerprints. If P2A adds lifecycle timestamps, they remain Manifest/receipt-envelope metadata and are excluded from `composition_fingerprint`.

- [ ] **Step 5: Export only stable P3 schema contracts**

Export these stable schema types from `production/__init__.py`: `CompositionSpec`, `ResolvedTimeline`, `RendererSelectionReceipt`, `RendererSourceReceipt`, `RenderReceipt`, `RenderArtifactPointer`, `RenderSourceFilePointer`, `RenderSourceBundlePointer`, `RenderOutputPointer`, `RenderStateSnapshot` and `RenderStateSnapshotPointer`. Task 5 later adds the stable lifecycle request/path exports. Keep validators, canonical serialization helpers, path constructors and cross-validation helpers module-private; do not export a second writer or CLI command.

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
- Modify: `src/ai_video/production/paths.py`
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


def test_cut_keeps_integer_frame_and_sample_boundaries(tmp_path):
    timeline = resolve_composition(
        write_and_load_two_shot_project(tmp_path, seconds=(2.0, 2.0), fps=24),
        make_composition_spec(sample_rate=48_000),
        "0.7.103",
    )
    assert timeline.visual_spans[1].start_frame == 48
    assert timeline.visual_spans[1].start_sample == 96_000
    assert timeline.total_frames == 96
    assert timeline.total_samples == 192_000


def test_same_resolved_inputs_have_same_fingerprint_after_mtime_change(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    first = resolve_composition(loaded, spec, "0.7.103")
    os.utime(loaded.asset_paths[spec.layers[0].asset_id], (1_900_000_000, 1_900_000_000))
    second = resolve_composition(loaded, spec, "0.7.103")
    assert second.composition_fingerprint == first.composition_fingerprint
```

Also add negative tests for duplicate/missing Shot IDs, missing/unregistered asset, wrong asset hash, asset path outside loaded registry mapping, non-fixed duration, any non-default `trim_start_frame` or non-`None` `trim_duration_frames`, duplicate layer ID, layer/Shot mismatch, undeclared `asset_role`, asset ID not bound to that exact Shot role, role rejecting `AssetType.IMAGE`, non-raster MIME/magic/extension mismatch, any `motion_directives`, any non-`STATIC_IMAGE` strategy (`IMAGE_MOTION`, `MOTION_GRAPHICS`, `GENERATED_VIDEO`, `EXISTING_VIDEO`/source video, `HYBRID`), crossfade/nonzero transition duration, duplicate z-order within a Shot, unsupported `remotion`, and empty timeline. Every slice-boundary rejection uses `COMPOSITION_INVALID`.

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


def _validated_raster_suffix(
    snapshot: NoFollowFile,
    *,
    suffix: str,
    mime_type: str,
) -> str:
    head = snapshot.data[:16]
    suffix = suffix.lower()
    if mime_type == "image/png" and suffix == ".png" and head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if mime_type == "image/jpeg" and suffix in {".jpg", ".jpeg"} and head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if mime_type == "image/webp" and suffix == ".webp" and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    raise _invalid("P3 asset MIME, magic bytes and raster suffix do not agree.")
```

Add the one shared internal read primitive in `production/paths.py` and use it everywhere P3 reads source, scratch or durable bytes:

```python
@dataclass(frozen=True)
class NoFollowFile:
    data: bytes
    file_sha256: str
    size_bytes: int
    mode: int
    device: int
    inode: int


def _read_regular_file_nofollow(path: Path, *, contained_by: Path) -> NoFollowFile: ...
```

It performs lexical absolute containment first, `lstat()` on the root and every existing component, rejects every artifact-path symlink even when it remains contained, opens/traverses beneath the root using directory FDs and `os.open(..., O_RDONLY | O_NOFOLLOW, dir_fd=...)`, requires `stat.S_ISREG(os.fstat(fd).st_mode)`, and reads/hash/magic-checks from that same FD. It compares final `lstat`/`fstat` device+inode and fails if a swap is observed. It never `resolve()`s and then reopens a pathname. `_create_directory_nofollow()` uses a validated parent dir FD plus `mkdirat`/no-follow reopen. `_create_regular_file_nofollow()` is the paired scratch/durable file primitive: validated parent directory FD, `O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW`, write bytes already returned by the read helper, file fsync, same-FD hash/size verification, then directory fsync. No P3 code uses `Path.mkdir()`, `shutil.copyfile()` or `sha256_file()` for these artifact surfaces.

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
        if transition.kind is not TransitionKind.CUT or transition.duration_frames != 0:
            raise _invalid("P3 accepts only zero-duration cut transitions.")
        transition_by_target[transition.to_shot_id] = transition

    spans: list[ResolvedVisualSpan] = []
    cursor = 0
    for shot_id in spec.shot_ids:
        shot = shots_by_id.get(shot_id)
        if shot is None:
            raise _invalid(f"CompositionSpec references unknown Shot {shot_id}.")
        if shot.visual_strategy is not VisualStrategy.STATIC_IMAGE:
            raise _invalid(f"Shot {shot_id} must use static_image in P3.")
        if shot.motion_directives:
            raise _invalid(f"Shot {shot_id} must not use motion_directives in P3.")
        if shot.duration_policy.mode != "fixed" or shot.duration_policy.seconds is None:
            raise _invalid(f"Shot {shot_id} requires a fixed duration in P3.")
        duration_frames = _frames_for_fixed_seconds(
            shot.duration_policy.seconds, spec.delivery_profile.fps
        )
        incoming = transition_by_target.get(shot_id)
        start_frame = cursor
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
            if layer.trim_start_frame != 0 or layer.trim_duration_frames is not None:
                raise _invalid("P3 static raster layers do not implement trim.")
            asset = assets_by_id.get(layer.asset_id)
            source_path = project.asset_paths.get(layer.asset_id)
            if asset is None or source_path is None:
                raise _invalid(f"Layer {layer.layer_id} references an unregistered asset.")
            roles = {item.role: item for item in shot.required_asset_roles}
            role = roles.get(layer.asset_role)
            if role is None or layer.asset_id not in role.asset_ids:
                raise _invalid(
                    f"Layer {layer.layer_id} is not bound to its declared Shot asset role."
                )
            if AssetType.IMAGE not in role.allowed_asset_types or asset.asset_type is not AssetType.IMAGE:
                raise _invalid(f"Layer {layer.layer_id} must bind a registry image asset.")
            source_snapshot = _read_regular_file_nofollow(
                source_path,
                contained_by=project.root,
            )
            if source_snapshot.file_sha256 != asset.sha256:
                raise _invalid(f"Asset hash changed before timeline resolution: {asset.asset_id}.")
            suffix = _validated_raster_suffix(
                source_snapshot,
                suffix=source_path.suffix,
                mime_type=asset.mime_type,
            )
            logical_path = Path("assets") / f"{asset.sha256}{suffix}"
            spans.append(
                ResolvedVisualSpan(
                    layer_id=layer.layer_id,
                    shot_id=shot_id,
                    asset_role=layer.asset_role,
                    asset_id=asset.asset_id,
                    asset_sha256=asset.sha256,
                    asset_mime_type=asset.mime_type,
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
4. accept only fixed-duration `STATIC_IMAGE` Shots with no motion directives, default-only trim (`0`/`None`) and local registry PNG/JPEG/WebP bytes; reject non-default trim, `image_motion`, `motion_graphics`, `generated_video`, `existing_video`/source video and `hybrid` with `COMPOSITION_INVALID` rather than silently degrading;
5. require each layer's `(asset_role, asset_id)` to match one exact `Shot.required_asset_roles` binding and its registry image record; construct `assets/<full-asset-sha256>.<canonical-lowercase-suffix>` without using raw `asset_id` in any path;
6. compute integer frame/sample boundaries and only zero-duration cuts;
7. sort only same-Shot layers by explicit `(z_index, layer_id)` after rejecting conflicting duplicate z-order; never sort Shots by ID or path;
8. construct a provisional `ResolvedTimeline`, calculate one `composition_fingerprint`, then `seal_artifact()` the final immutable timeline.

`_validated_raster_suffix()` reads bytes without following a symlink and requires one exact triple: PNG magic + `image/png` + `.png`; JPEG magic + `image/jpeg` + `.jpg`/`.jpeg` (canonical target `.jpg`); or RIFF/WEBP magic + `image/webp` + `.webp`. It rejects SVG, HTML, CSS, extension-only claims, ambiguous MIME and every other payload. The same validation is repeated after materialized copy in Task 3.

Keep this as the single resolver; do not add a second resolver or renderer-specific timing function.

- [ ] **Step 5: Run GREEN and commit**

```bash
python -m pytest tests/test_production_models.py tests/test_production_composition.py -q
git add src/ai_video/production/composition.py src/ai_video/production/paths.py \
  tests/test_production_composition.py \
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
- Create: `tests/fixtures/hyperframes/silent_image/source/assets/431ced6916a2a21a156e38701afe55bbd7f88969fbbfc56d7fe099d47f265460.png`

- [ ] **Step 1: Write source RED tests**

```python
def test_source_is_materialized_only_from_timeline_and_bound_assets(tmp_path):
    timeline = make_resolved_timeline(order=("shot-2", "shot-1"))
    result = materialize_hyperframes_source(
        timeline,
        asset_sources=make_asset_sources(tmp_path, timeline),
        allowed_asset_root=tmp_path,
        staging_root=tmp_path / "staging",
        allowed_staging_parent=tmp_path,
    )
    assert result.source_sha256 == _read_regular_file_nofollow(
        result.index_path,
        contained_by=result.root,
    ).file_sha256
    html = result.index_path.read_text(encoding="utf-8")
    assert html.index('data-shot-id="shot-2"') < html.index('data-shot-id="shot-1"')
    assert 'data-asset-id="image-hero-1"' in html
    assert 'src="assets/431ced6916a2a21a156e38701afe55bbd7f88969fbbfc56d7fe099d47f265460.png"' in html


def test_materializer_validates_target_containment_before_any_mkdir_or_copy(tmp_path): ...


@pytest.mark.parametrize("location", ["contained", "external"])
def test_materializer_rejects_asset_symlink_without_following_it(tmp_path, location): ...


def test_nofollow_reader_detects_inode_swap_between_lstat_and_open(tmp_path): ...


def test_source_snapshot_applies_transform_origin_opacity_and_z_index_exactly(tmp_path): ...


def test_audit_parses_every_media_url_and_requires_exact_declared_set(tmp_path): ...


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

Also assert source audit rejects absolute paths, `..`, URI schemes, protocol-relative URLs, `data:`/`blob:`, `srcset` extras, CSS `url()`/`@import`, external or inline script, external stylesheet/font, undeclared/missing files, symlink assets, asset hash mismatch, MIME/magic/extension mismatch, SVG/HTML/CSS payloads, missing composition/timeline identity, and a source asset binding not present in the timeline. Assertions inspect the parsed DOM/CSS URL set, not substring presence alone.

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
    bundle_sha256: str
    asset_bindings: tuple[RendererAssetBinding, ...]
```

Implement:

```python
def materialize_hyperframes_source(
    timeline: ResolvedTimeline,
    *,
    asset_sources: Mapping[str, Path],
    allowed_asset_root: Path,
    staging_root: Path,
    allowed_staging_parent: Path,
) -> MaterializedHyperFramesSource:
    expected_ids = {item.asset_id for item in timeline.visual_spans}
    if set(asset_sources) != expected_ids:
        raise _source_invalid("Asset sources must exactly match timeline asset IDs.")
    root = _validate_new_contained_root(
        staging_root,
        allowed_parent=allowed_staging_parent,
    )

    bindings_by_id: dict[str, RendererAssetBinding] = {}
    planned_asset_ids: set[str] = set()
    planned: list[tuple[ResolvedVisualSpan, NoFollowFile, Path]] = []
    for span in timeline.visual_spans:
        if span.asset_id in planned_asset_ids:
            continue
        planned_asset_ids.add(span.asset_id)
        source = asset_sources[span.asset_id]
        source_snapshot = _read_regular_file_nofollow(
            source,
            contained_by=allowed_asset_root,
        )
        suffix = _validated_raster_suffix(
            source_snapshot,
            suffix=source.suffix,
            mime_type=span.asset_mime_type,
        )
        if source_snapshot.file_sha256 != span.asset_sha256:
            raise _source_invalid(f"Asset bytes do not match timeline: {span.asset_id}.")
        relative = Path("assets") / f"{span.asset_sha256}{suffix}"
        if relative != span.materialized_path:
            raise _source_invalid("Timeline materialized path is not canonical for asset hash.")
        target = _validate_contained_target(root, relative, before_creation=True)
        planned.append((span, source_snapshot, target))

    # No mkdir/copy occurs until every root and target has passed containment validation.
    _create_directory_nofollow(root, contained_by=allowed_staging_parent)
    assets_root = root / "assets"
    _create_directory_nofollow(assets_root, contained_by=root)
    for span, source_snapshot, target in planned:
        target_snapshot = _create_regular_file_nofollow(
            target,
            data=source_snapshot.data,
            contained_by=root,
        )
        suffix = _validated_raster_suffix(
            target_snapshot,
            suffix=target.suffix,
            mime_type=span.asset_mime_type,
        )
        if suffix != target.suffix or target_snapshot.file_sha256 != span.asset_sha256:
            raise _source_invalid(f"Copied asset hash mismatch: {span.asset_id}.")
        bindings_by_id[span.asset_id] = RendererAssetBinding(
            asset_id=span.asset_id,
            asset_sha256=span.asset_sha256,
            asset_mime_type=span.asset_mime_type,
            materialized_path=target.relative_to(root),
        )

    fps = timeline.delivery_profile.fps
    clips: list[str] = []
    for span in timeline.visual_spans:
        transform = _css_transform(span.transform)
        opacity = _decimal_milli(span.opacity_milli)
        clips.append(
            "\n".join(
                [
                    (
                        f'<div class="clip" data-layer-id="{escape(span.layer_id)}"'
                        f' data-shot-id="{escape(span.shot_id)}"'
                        f' data-asset-id="{escape(span.asset_id)}"'
                        f' data-asset-role="{escape(span.asset_role)}"'
                        f' data-asset-sha256="{span.asset_sha256}"'
                        f' data-start="{_seconds(span.start_frame, fps)}"'
                        f' data-duration="{_seconds(span.duration_frames, fps)}"'
                        f' data-start-frame="{span.start_frame}"'
                        f' data-duration-frames="{span.duration_frames}"'
                        f' data-start-sample="{span.start_sample}"'
                        f' data-duration-samples="{span.duration_samples}"'
                        f' data-transition-kind="cut" data-transition-frames="0"'
                        f' style="z-index:{span.z_index};opacity:{opacity}">'
                    ),
                    (
                        f'  <img src="{span.materialized_path.as_posix()}"'
                        f' style="transform:{escape(transform)};transform-origin:0 0" alt="" />'
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
    index_path = _validate_contained_target(root, Path("index.html"), before_creation=True)
    index_snapshot = _create_regular_file_nofollow(
        index_path,
        data=source.encode("utf-8"),
        contained_by=root,
    )
    bindings = tuple(bindings_by_id[key] for key in sorted(bindings_by_id))
    audit_hyperframes_source(index_path, expected_assets=bindings)
    bundle_sha256 = _source_bundle_sha256(index_path, bindings)
    return MaterializedHyperFramesSource(
        root=root,
        index_path=index_path,
        source_sha256=index_snapshot.file_sha256,
        bundle_sha256=bundle_sha256,
        asset_bindings=bindings,
    )


def audit_hyperframes_source(
    index_path: Path,
    *,
    expected_assets: tuple[RendererAssetBinding, ...],
) -> None:
    source_root = index_path.parent
    index_snapshot = _read_regular_file_nofollow(index_path, contained_by=source_root)
    source = index_snapshot.data.decode("utf-8", errors="strict")
    parsed = _parse_source_document(source)  # stdlib HTMLParser + explicit CSS url()/@import scanner
    if not parsed.composition_id or not parsed.timeline_fingerprint:
        raise _source_invalid("HyperFrames source is missing composition identity.")
    if parsed.has_script or parsed.external_styles_or_fonts or parsed.css_imports:
        raise _source_invalid("HyperFrames source contains script/style/font imports.")
    expected_urls = {item.materialized_path.as_posix() for item in expected_assets}
    if parsed.media_urls != expected_urls:
        raise _source_invalid("Parsed media URLs do not exactly match declared raster bindings.")
    for url in parsed.all_urls:
        _validate_local_relative_url(url)  # rejects absolute, '..', scheme, //, data:, blob:
    for binding in expected_assets:
        relative = binding.materialized_path
        if relative.is_absolute() or ".." in relative.parts:
            raise _source_invalid(f"Unsafe materialized asset path: {relative}")
        target = _validate_contained_target(source_root, relative, before_creation=False)
        target_snapshot = _read_regular_file_nofollow(target, contained_by=source_root)
        if target_snapshot.file_sha256 != binding.asset_sha256:
            raise _source_invalid(f"Untracked or changed source asset: {binding.asset_id}")
        _validated_raster_suffix(
            target_snapshot,
            suffix=target.suffix,
            mime_type=binding.asset_mime_type,
        )
    expected_files = {Path("index.html"), *(item.materialized_path for item in expected_assets)}
    actual_files = _list_regular_files_nofollow(source_root)
    if actual_files != expected_files:
        raise _source_invalid("HyperFrames staging contains an untracked file.")


def _seconds(frame_count: int, fps: int) -> str:
    value = Decimal(frame_count) / Decimal(fps)
    rendered = format(value.quantize(Decimal("0.000000001")), "f")
    return rendered.rstrip("0").rstrip(".") or "0"


def _decimal_milli(value: int) -> str:
    rendered = format(Decimal(value) / Decimal(1000), "f")
    return rendered.rstrip("0").rstrip(".") or "0"


def _decimal_millidegrees(value: int) -> str:
    return _decimal_milli(value)


def _css_transform(transform: FixedTransform) -> str:
    return (
        f"translate({transform.translate_x_px}px,{transform.translate_y_px}px) "
        f"scale({_decimal_milli(transform.scale_x_milli)},{_decimal_milli(transform.scale_y_milli)}) "
        f"rotate({_decimal_millidegrees(transform.rotation_millidegrees)}deg)"
    )
```

Import `Mapping`, `dataclass`, `Decimal`, `escape` from `html`, `HTMLParser`, `urlsplit`, `re`, the shared no-follow read/create/list primitives, and the named production models. `_parse_source_document()` must enumerate every URL-bearing `src`, `href`, `poster`, `srcset`, inline-style `url()` and style-block `url()`/`@import`; it does not accept a substring-only audit. `_validated_raster_suffix()` validates magic bytes, exact MIME and suffix for PNG/JPEG/WebP from the no-follow snapshot before and after copy. `_source_bundle_sha256()` hashes stable JSON of the exact ordered `(relative_path, file_sha256)` set including `index.html`, using only same-FD snapshots. `_list_regular_files_nofollow()` rejects symlink entries/directories instead of traversing them. After Task 4 introduces `RendererAttemptError`, `_source_invalid()` returns a non-retryable instance with `code=ErrorCode.RENDERER_SOURCE_INVALID` and `phase="source"`.

Materialization rules:

- Task 3 is pure and has no dependency on the not-yet-created Task 5 `RenderAttemptPaths`. Its caller supplies both a new `staging_root` and an existing `allowed_staging_parent`; `_validate_new_contained_root()` rejects symlink/escape/existing targets and validates every planned child target **before** any mkdir/copy. Task 5 later adds the canonical integration call with `render_attempt_paths()`.
- Copy each timeline asset to `assets/<full-asset-sha256>.<png|jpg|webp>` after verifying registry SHA-256 plus magic/MIME/extension; raw `asset_id` never contributes to a filesystem path. Do not accept SVG, HTML, CSS or any other payload.
- Generate `index.html` in exact `timeline.visual_spans` order. Convert frame boundaries to decimal seconds only at source materialization with `Decimal(frame) / Decimal(fps)` and a stable string formatter.
- Embed timeline fingerprint, renderer version and asset ID/role/hash as data attributes. Trim is not serialized because only `0`/`None` is accepted. Apply fixed transform, `transform-origin: 0 0`, opacity and z-order as deterministic inline CSS used by the rendered DOM; source snapshot tests assert the exact CSS and the decoded-frame integration proof exercises a non-default transform/opacity/z-order case. Do not claim or serialize motion directives.
- Use only local HTML/CSS/HyperFrames runtime features proven by the live spike. Do not reference CDN GSAP, Google Fonts, remote media, `.env`, current time or randomness.
- Write source once into the caller-supplied staging root, hash it, run `audit_hyperframes_source()`, and return the result. No source rewrite is allowed after hashing.

Keep these as straight-line materialization/audit functions; no template discovery, glob or alternate renderer branch is permitted.

- [ ] **Step 4: Seal the deterministic fixture**

Commit a human-readable `timeline.json`, its exact expected `index.html` and the reviewed minimal local PNG `assets/431ced6916a2a21a156e38701afe55bbd7f88969fbbfc56d7fe099d47f265460.png`. The unit test must regenerate source under its caller-supplied contained `tmp_path`, assert exact text/hash equality and validate PNG magic/MIME/hash. Fixture files contain only local relative raster assets and no generated binary output.

- [ ] **Step 5: Run GREEN and commit**

```bash
python -m pytest tests/test_production_hyperframes.py -q -k 'source or audit'
git add src/ai_video/production/hyperframes.py tests/test_production_hyperframes.py \
  tests/fixtures/hyperframes/silent_image/timeline.json \
  tests/fixtures/hyperframes/silent_image/source/index.html \
  tests/fixtures/hyperframes/silent_image/source/assets/431ced6916a2a21a156e38701afe55bbd7f88969fbbfc56d7fe099d47f265460.png
git commit -m "feat: materialize audited hyperframes sources"
```

Expected: fixture/source hash tests pass without Node, Chrome or network.

### Task 4: Add the Exclusive HyperFrames Adapter

**Files:**
- Modify: `src/ai_video/production/hyperframes.py`
- Test: `tests/test_production_hyperframes.py`

- [ ] **Step 1: Write fake-runner RED tests**

Exercise runner injection only through the module-internal adapter seam; default tests must never execute the real binary:

```python
def test_adapter_runs_one_pinned_renderer_in_order(tmp_path):
    validated_browser_path = write_fake_browser_executable(tmp_path)
    runner = FakeRunner(
        version="0.7.103",
        results={"lint": clean_lint_json(), "check": clean_check_json(), "render": ""},
    )
    result = HyperFramesAdapter(
        runner=runner,
        expected_version="0.7.103",
        browser_path=validated_browser_path,
    ).render(
        attempt=make_render_attempt(tmp_path),
    )
    assert [call.command for call in runner.calls] == ["version", "doctor", "lint", "check", "render"]
    assert {call.env["HYPERFRAMES_NO_UPDATE_CHECK"] for call in runner.calls} == {"1"}
    assert {call.env["HYPERFRAMES_BROWSER_PATH"] for call in runner.calls} == {
        str(validated_browser_path)
    }
    assert result.output.output_sha256 == _read_regular_file_nofollow(
        result.output.scratch_path,
        contained_by=result.output.scratch_path.parent.parent,
    ).file_sha256


def test_adapter_rejects_remotion_without_fallback(tmp_path):
    runner = FakeRunner()
    with pytest.raises(AiVideoError) as exc:
        HyperFramesAdapter(
            runner, "0.7.103", browser_path=write_fake_browser_executable(tmp_path)
        ).render(
            attempt=make_render_attempt(tmp_path, renderer_kind="remotion")
        )
    assert exc.value.code is ErrorCode.RENDERER_UNAVAILABLE
    assert runner.calls == []


@pytest.mark.parametrize("failed_phase", ["lint", "check", "render"])
def test_adapter_reports_typed_phase_failure_without_next_command(tmp_path, failed_phase):
    runner = FakeRunner(fail_at=failed_phase)
    with pytest.raises(RendererAttemptError) as exc:
        HyperFramesAdapter(
            runner, "0.7.103", browser_path=write_fake_browser_executable(tmp_path)
        ).render(make_render_attempt(tmp_path))
    assert exc.value.phase == failed_phase
    assert all(call.command != "render" for call in runner.calls) if failed_phase != "render" else True


def test_production_runner_builds_exact_unshare_argv_and_fixed_exec_wrapper(tmp_path): ...


def test_production_runner_has_no_host_network_fallback_when_namespace_is_unavailable(tmp_path): ...


def test_production_runner_injects_exact_browser_env_timeout_and_redacts_output(tmp_path): ...


```

Also cover wrong tool version/failed doctor, malformed JSON, lint errors, check errors, warnings policy, missing/empty output, output hash mismatch, measured width/height/FPS/frame-count mismatch, unexpected audio stream, timeout, stderr truncation/redaction, no source mutation after lint, and only one selected renderer.

Add output-path tests proving a sibling/absolute/`..`/symlink-escape output is rejected before mkdir/render. The adapter validates the exact scratch output and parent beneath `allowed_staging_parent`, then explicitly creates that validated parent; it never attempts to express the output relative to the source root.

Add verify-boundary tests where injected `probe_clip()`, `decoded_frame_sha256()`, ffprobe parsing or framemd5 parsing raises plain exceptions, `AiVideoError(code=FFMPEG_FAILED)` or another `AiVideoError`. Every case must emerge as non-retryable `RendererAttemptError(code=RENDER_FAILED, phase="verify")`; no `FFMPEG_FAILED` crosses the P3 public boundary, and lifecycle orchestration records phase `verify`.

- [ ] **Step 2: Run adapter RED**

```bash
python -m pytest tests/test_production_hyperframes.py -q -k 'adapter or receipt or failure'
```

Expected: tests fail because runner/adapter/verified-output construction is not implemented.

- [ ] **Step 3: Implement the private production runner and internal adapter seam**

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
    def version(self, *, env: dict[str, str]) -> str:
        pass

    def doctor(self, *, env: dict[str, str]) -> RendererCommandResult:
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


class _NetworkIsolatedHyperFramesRunner:
    """Sole production runner; low-level tests inject RendererRunner fakes."""

    _WRAPPER = '"$P3_IP_PATH" link set lo up; exec "$@"'

    def _namespace_argv(self, *renderer_argv: str) -> list[str]:
        return [
            str(self._unshare),
            "--user", "--map-root-user", "--net", "--pid", "--fork", "--mount-proc",
            str(self._bash), "-ceu", self._WRAPPER, "p3-hyperframes",
            str(self._binary), *renderer_argv,
        ]

    def _invoke(self, *renderer_argv: str, timeout_seconds: int) -> RendererCommandResult:
        completed = subprocess.run(
            self._namespace_argv(*renderer_argv),
            cwd=self._project_root,
            env=dict(self._env),
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return _bounded_redacted_result(completed)


@dataclass(frozen=True)
class HyperFramesRenderAttempt:
    attempt_id: str
    selection: RendererSelectionReceipt
    timeline: ResolvedTimeline
    asset_sources: Mapping[str, Path]
    allowed_asset_root: Path
    staging_root: Path
    allowed_staging_parent: Path
    output_path: Path


@dataclass(frozen=True)
class VerifiedRenderOutput:
    scratch_path: Path
    output_sha256: str
    output_size_bytes: int
    measured: MeasuredRenderMetadata
    decoded_frame_fingerprint: str


@dataclass(frozen=True)
class HyperFramesRenderResult:
    materialized: MaterializedHyperFramesSource
    checks: tuple[RendererCheckReceipt, RendererCheckReceipt]
    output: VerifiedRenderOutput


OFFLINE_ENV = {
    "CI": "1",
    "HYPERFRAMES_NO_TELEMETRY": "1",
    "DO_NOT_TRACK": "1",
    "HYPERFRAMES_NO_UPDATE_CHECK": "1",
    "HYPERFRAMES_NO_AUTO_INSTALL": "1",
}


def _controlled_env(browser_path: Path) -> dict[str, str]:
    if not browser_path.is_absolute():
        raise _renderer_unavailable("Pinned HyperFrames browser path must be absolute.")
    snapshot = _read_regular_file_nofollow(
        browser_path,
        contained_by=browser_path.parent,
    )
    if snapshot.mode & 0o111 == 0:
        raise _renderer_unavailable("Pinned HyperFrames browser is not executable.")
    env = {
        key: os.environ[key]
        for key in ("PATH", "LANG", "LC_ALL", "TMPDIR")
        if key in os.environ
    }
    env.update(OFFLINE_ENV)
    env["HYPERFRAMES_BROWSER_PATH"] = str(browser_path)
    return env
```

The private `_NetworkIsolatedHyperFramesRunner` constructor validates the lock-resolved project-local `node_modules/.bin/hyperframes` target/integrity, exact no-follow browser and absolute executable `unshare`, `ip`, `bash` paths with `lstat`; npm's expected `.bin` link is accepted only when its target is the exact lock-owned package executable under this `node_modules`, while source/scratch/durable artifact symlinks remain categorically forbidden. Its controlled env fixes `P3_IP_PATH` for the literal wrapper and `HYPERFRAMES_BROWSER_PATH` for HyperFrames. It runs a harmless namespace capability probe through the same argv form; missing user/net/PID namespace, loopback setup, executable or permission maps to non-retryable `RENDERER_UNAVAILABLE`. Every production `version`, `doctor`, `lint`, `check` and `render` call creates a new Linux user+network+PID namespace, brings up loopback, then uses the fixed `exec "$@"` wrapper. Renderer arguments are positional argv after sentinel `$0`; none is interpolated into shell text. There is no direct-host subprocess path, retry or fallback. Timeout, bounded capture and redaction apply at this concrete boundary.

Task 4 implements the private production runner plus the module-internal adapter seam, lint/check evidence and scratch-output verification. Runner injection exists only at that internal test seam. Task 5 knows canonical durable paths and therefore is the only stage that seals `RendererSourceReceipt`/`RenderReceipt`; Task 4 must not put scratch paths into semantic receipts. Task 5 also adds the named `render_with_hyperframes()` orchestration after the real lifecycle request/API types exist; do not create a temporary alias or duplicate request model here.

`OFFLINE_ENV` 是必要但不充分的 process policy：它不阻止 npm update fetch 或 browser download。默认 unit tests 只使用 fake runner；real runner/live spike 还必须在 OS-level egress denial/observability 下运行，并用经 Renderer Gate 验收的 `HYPERFRAMES_BROWSER_PATH` 显式指向预先安装的 browser。

`_NetworkIsolatedHyperFramesRunner` is the only production runner constructed by public `render_with_hyperframes()`. It calls only the approved local binary, never `npx`, `upgrade`, `browser`, `cloud`, `lambda`, `tts` or `transcribe`. `HyperFramesAdapter` and `RendererRunner` remain low-level internal/test seams; production callers cannot inject a host runner through the stable API. Exact version `0.7.103` and `doctor` must succeed through the isolated runner before lint/check/render.

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
        browser_path: Path,
    ) -> None:
        self._runner = runner
        self._expected_version = expected_version
        self._probe = probe
        self._decoded_frames = decoded_frames
        self._env = _controlled_env(browser_path)

    def _check(
        self,
        command: Literal["lint", "check"],
        root: Path,
    ) -> RendererCheckReceipt:
        result = self._runner.run(
            command,
            (str(root), "--json"),
            cwd=root,
            env=dict(self._env),
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
        if self._runner.version(env=dict(self._env)) != self._expected_version:
            raise _renderer_unavailable("Installed HyperFrames version does not match the pin.")
        doctor = self._runner.doctor(env=dict(self._env))
        if doctor.returncode != 0:
            raise _renderer_unavailable("HyperFrames doctor did not accept the pinned runtime.")
        materialized = materialize_hyperframes_source(
            attempt.timeline,
            asset_sources=attempt.asset_sources,
            allowed_asset_root=attempt.allowed_asset_root,
            staging_root=attempt.staging_root,
            allowed_staging_parent=attempt.allowed_staging_parent,
        )
        lint_receipt = self._check("lint", materialized.root)
        _verify_materialized_unchanged(materialized)
        check_receipt = self._check("check", materialized.root)
        _verify_materialized_unchanged(materialized)
        staged_output = _validate_new_contained_output(
            attempt.output_path,
            allowed_parent=attempt.allowed_staging_parent,
            suffix=".mp4",
        )
        _create_directory_nofollow(
            staged_output.parent,
            contained_by=attempt.allowed_staging_parent,
        )
        command_result = self._runner.run(
            "render",
            (str(materialized.root), "-o", str(staged_output)),
            cwd=materialized.root,
            env=dict(self._env),
            timeout_seconds=1800,
        )
        if command_result.returncode != 0:
            raise _render_error("render", command_result)
        _verify_materialized_unchanged(materialized)
        try:
            output_snapshot = _read_regular_file_nofollow(
                staged_output,
                contained_by=attempt.allowed_staging_parent,
            )
            if output_snapshot.size_bytes == 0:
                raise _render_failed("HyperFrames output is missing or empty.")
            output_size = output_snapshot.size_bytes
            output_sha256 = output_snapshot.file_sha256
            measured = _measured_metadata(self._probe(staged_output))
            _validate_measured_timeline(measured, attempt.timeline)
            decoded = self._decoded_frames(staged_output)
            return HyperFramesRenderResult(
                materialized=materialized,
                checks=(lint_receipt, check_receipt),
                output=VerifiedRenderOutput(
                    scratch_path=staged_output,
                    output_sha256=output_sha256,
                    output_size_bytes=output_size,
                    measured=measured,
                    decoded_frame_fingerprint=decoded,
                ),
            )
        except Exception as exc:
            raise _verify_failed(exc) from exc


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


def _verify_failed(exc: Exception) -> RendererAttemptError:
    # Includes AiVideoError/FFMPEG_FAILED plus probe, framemd5 and parse failures.
    return RendererAttemptError(
        code=ErrorCode.RENDER_FAILED,
        user_message="Rendered output could not be verified.",
        technical_detail=_redact(str(exc)),
        retryable=False,
        phase="verify",
    )


def _verify_materialized_unchanged(value: MaterializedHyperFramesSource) -> None:
    snapshot = _read_regular_file_nofollow(value.index_path, contained_by=value.root)
    if snapshot.file_sha256 != value.source_sha256:
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
    all_streams = probe.get("streams", [])
    streams = [item for item in all_streams if item.get("codec_type") == "video"]
    audio = [item for item in all_streams if item.get("codec_type") == "audio"]
    if len(streams) != 1 or audio:
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

The method must verify exact tool version and successful `doctor` after selection has been durably begun, parse the pinned JSON schema, require zero errors, record warning counts, rehash source/assets between phases, validate output with `probe_clip()`, and calculate output/decoded-frame hashes. The verify boundary catches every `AiVideoError` including `FFMPEG_FAILED` plus plain probe/framemd5/parse exceptions and exposes only non-retryable `RendererAttemptError(RENDER_FAILED, phase="verify")`. It never includes timestamps or scratch paths in timeline/source/decoded-frame identity. Task 5 builds canonical durable receipts and supplies the real committer/crash/replay tests.

Import `Callable`, `Mapping`, `Protocol`, `Literal`, `cast`, `hashlib`, `json`, `os`, `re`, `subprocess`, the shared no-follow primitives, existing `probe_clip()`/`run_command()` and the named P3 models. `_source_invalid()` must return `RendererAttemptError(phase="source")`; `_render_failed()` must return `RendererAttemptError(phase="verify")`; `_renderer_unavailable()` returns non-retryable `AiVideoError(RENDERER_UNAVAILABLE)`. Public orchestration persists begin before constructing/probing the isolated runner; no helper may start a host fallback command.

Do not add preview to automated adapter flow. Preview belongs only to the explicit live spike gate because it starts a server/browser and is not necessary for deterministic batch execution.

- [ ] **Step 5: Run GREEN and commit**

```bash
python -m pytest tests/test_production_hyperframes.py -q
git add src/ai_video/production/hyperframes.py tests/test_production_hyperframes.py
git commit -m "feat: add hyperframes renderer adapter"
```

Expected: fake/no-network tests pass; process call list proves one renderer and exact phase order.

### Task 5: Add the P2A-Owned Render-State Lifecycle

**Problem boundary:** activate one exact project/registry-derived timeline/durable-source/render/output set after one HyperFrames attempt. **Single owner:** existing `ProductionManifest` + `ProductionStateCommitter`. **Old path retired:** the former authorization-only Task 5, invented `RenderAttemptCommitter`, alias methods, second Manifest/writer, Legacy Manifest v1, `runs/<run_id>/` or ad-hoc discovery. **Compatibility contract:** existing `commit(StateCommitRequest)` request/replay remains P2A-owned; on Manifest 2.1 it additionally performs the required blanket `active_render_state` invalidation when the project/registry pair changes, without implementing P5 selective invalidation.

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

Test canonical full-hash paths and containment for timelines, source-bundle root/index/raster files, source receipts, render receipts, states and outputs plus safe attempt IDs. Reject empty, `.`/`..`, slash, backslash, absolute path, symlink escape, shortened hash filename, wrong namespace/extension, source MIME/magic mismatch and output hash/path mismatch.

Add P2 read-only tests:

```python
def test_reader_loads_20_without_render_state_and_does_not_rewrite(tmp_path): ...
def test_reader_loads_20_historical_custom_operation_without_rewrite(tmp_path): ...
def test_reader_loads_21_with_none_render_state(tmp_path): ...
def test_reader_verifies_21_selected_render_state_and_all_exact_artifacts(tmp_path): ...
def test_reader_rejects_tampered_or_mixed_render_state_without_fallback(tmp_path): ...
def test_commit_changed_project_or_registry_clears_active_render_state_atomically(tmp_path): ...
def test_commit_same_pair_retains_only_fully_verified_render_state(tmp_path): ...
def test_commit_invalidation_preserves_previous_render_and_source_bytes_as_orphans(tmp_path): ...
def test_reader_rejects_contained_and_external_symlinks_for_every_render_artifact(tmp_path): ...
def test_reader_nofollow_reopen_detects_inode_swap_without_accepting_replacement(tmp_path): ...
```

`load_production_project()` must preserve bytes and mtimes for both versions. A 2.0 Manifest remains valid until the first render lifecycle write; no eager migration.

- [ ] **Step 2: Add canonical path and attempt-path APIs**

In `paths.py`, add one constructor/validator per namespace:

```python
canonical_render_timeline_path(content_hash)
canonical_render_source_root(bundle_sha256)
canonical_render_source_index_path(bundle_sha256)
canonical_render_source_asset_path(bundle_sha256, asset_sha256, suffix)
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

This method is pure: it validates a conservative safe attempt ID, resolves clean absolute project-root-contained paths corresponding to `state/render/attempts/<attempt-id>/`, and performs no mkdir/write/delete. The persisted identities remain canonical project-relative paths; the adapter creates only the exact validated attempt-owned directories it consumes.

Use the same immutable path validators and the single `_read_regular_file_nofollow()` primitive in `project.py` and `state_commit.py`: when a 2.1 Manifest has `active_render_state`, open the exact state snapshot, timeline/source receipt/render receipt JSON, canonical source index and every bound raster, plus output without following any symlink; verify canonical path, same-FD file SHA-256, source bundle hash, raster MIME/magic/suffix, semantic revision/content hash, output size, exact project/registry provenance and every cross identity. Candidate promotion/reopen and recovery use the same primitive. Return the verified render state as optional read-only data on `LoadedProductionProject`; do not scan, activate, recover or mutate.

Add the Task 3/Task 5 integration test: `render_attempt_paths()` returns validated attempt/source/output paths; orchestration rechecks containment, creates exactly `paths.attempt_root`, then `materialize_hyperframes_source(..., staging_root=paths.source_root, allowed_staging_parent=paths.attempt_root)` succeeds without any alternate path API. The adapter separately validates and creates the exact output parent. This is the first task that may claim canonical attempt paths exist.

Extend the existing `ProductionStateCommitter.commit(StateCommitRequest)` in place, without a second commit path. While holding the existing lock, compare the authoritative old and requested new project/registry pointers. If either pointer changes, the one candidate Manifest atomically sets `active_render_state=None`; it never deletes or rewrites the previous state/source/output bytes. If the pair is identical and an active render pointer exists, reopen and fully verify its snapshot, source bundle and project/registry provenance before retaining it; verification failure is typed `PRODUCTION_STATE_INVALID` and does not commit. Exact replay includes the resulting cleared-or-retained render pointer. Add crash/reopen tests proving pair switch and pointer clearing are one commit point and orphan evidence survives.

- [ ] **Step 3: Define exact strict lifecycle requests**

Add frozen dataclasses/models in `state_commit.py`:

```python
@dataclass(frozen=True)
class BeginRenderAttemptRequest:
    expected_manifest_revision: int
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

The request identity is the complete tuple of authoritative `renderer_selection` (including attempt ID, exact timeline fingerprint and active project/registry pointers), expected revision, base render pointer, sorted `(relative_path, file_sha256)` variable artifact set and next pointer. `BeginRenderAttemptRequest` does not duplicate selection identity; the committer compares selection pointers/fingerprint directly with the live Manifest and resolved timeline, and `RenderStateSnapshot` later fixes the same provenance. `BeginRenderAttemptRequest.expected_manifest_revision=R`; its fresh write yields R+1. An outer `RecordRenderFailureRequest` is valid only before activation is called, against authoritative begun R+1, and yields terminal R+2 with no candidate. `ActivateRenderStateRequest.expected_manifest_revision=R+1` transfers sole ownership at method entry: candidate-transition ordinary failure may terminalize directly from R+1 to R+2 with exact candidate/hash; successful candidate preparation yields authoritative R+2; final success or activation-owned failure then yields R+3 internally. The outer layer never constructs a failure request after that call. Begin/success exact replay returns the already-persisted corresponding Manifest state only when selection, base pointer and every stage identity match; any mismatch is `PRODUCTION_STATE_INVALID`. Pre-activation failure replay is idempotent only when phase/code/message and all provenance/base identities match. Requests reject stale `expected_manifest_revision` except an exact recognized replay for the same owner/stage.

For every render request, `current_project/current_registry` must equal the live Manifest pair. Persisted render attempts set `base_project == candidate_project == current_project` and `base_registry == candidate_registry == current_registry`; validators reject any project/registry change or any mixed project-registry/render operation.

- [ ] **Step 4: Implement begin and typed failure persistence**

Add real methods, not wrappers around `commit()`:

```python
def begin_render_attempt(self, request: BeginRenderAttemptRequest) -> ProductionManifest: ...
def record_render_failure(self, request: RecordRenderFailureRequest) -> ProductionManifest: ...
```

Both run under `state/commit.lock` and use the existing atomic Manifest writer. `begin_render_attempt()` validates selection contains exactly HyperFrames `0.7.103`, the resolved timeline fingerprint and exact live active project/registry pointers, writes a running `StateCommitAttempt(render_phase="selection")`, and on the first render write migrates Manifest 2.0 -> 2.1 in that same replace. This durable write must finish before version/doctor/lint/check/render. It never switches `active_render_state`.

`record_render_failure()` requires the exact R+1 matching begun attempt with no candidate and is called only before activation method entry. It persists terminal R+2 `failed`, exact typed phase/code/redacted bounded message and finished time, and leaves `active_render_state` plus project/registry pointers unchanged. It rejects any candidate-bearing or later-stage attempt; every failure after activation is called belongs only to `activate_render_state()`. Source materialization and installed-version/renderer-availability failures use phase `source`; lint, check, render and output verification use their named phases before activation begins. If failure persistence itself fails, surface the state error without claiming the render failure was recorded.

- [ ] **Step 5: Integrate one lifecycle-owned HyperFrames orchestration path**

Now add `hyperframes.py::render_with_hyperframes()` using the real Task 5 request/path types. It exposes no runner/adapter injection parameter. It calls `begin_render_attempt()` first, then inside the post-begin failure boundary constructs the sole private `_NetworkIsolatedHyperFramesRunner`, obtains `render_attempt_paths()`, calls the internal `HyperFramesAdapter.render()` once, derives canonical durable source-bundle/output paths from full hashes, seals receipts/snapshot with exact project/registry provenance, builds the variable exact prepared-artifact set and calls `activate_render_state()` only after verify. Tests may exercise a private helper with a fake `RendererRunner`; package callers cannot bypass isolation.

Use one explicit post-begin exception boundary:

```python
manifest = committer.begin_render_attempt(begin_request)
phase = "source"
try:
    paths = committer.render_attempt_paths(begin_request.renderer_selection.attempt_id)
    validate_render_attempt_paths(paths)
    _create_directory_nofollow(
        paths.attempt_root,
        contained_by=committer.project_root,
    )
    runner = _NetworkIsolatedHyperFramesRunner(
        project_root=committer.project_root,
        binary_path=validated_binary_path,
        browser_path=validated_browser_path,
        unshare_path=validated_unshare_path,
        ip_path=validated_ip_path,
        bash_path=validated_bash_path,
    )
    adapter = HyperFramesAdapter(
        runner=runner,
        expected_version=expected_version,
        browser_path=validated_browser_path,
    )
    # Adapter verifies version/doctor under controlled env, then source/lint/check/render/verify.
    result = adapter.render(...)
    durable = prepare_durable_render_artifacts(
        result,
        timeline=timeline,
        current_project=manifest.active_project,
        current_registry=manifest.active_registry,
    )
except Exception as exc:
    committer.record_render_failure(
        failure_request_from(exc, phase=phase, manifest=manifest)
    )
    raise
activation = activation_request(durable, expected_manifest_revision=manifest.manifest_revision)
# Deliberately outside the outer handler: activation owns every candidate/final window from entry.
return committer.activate_render_state(activation)
```

Every ordinary exception after successful begin but before the call to `activate_render_state()`, including missing namespace/tool capability, isolated-runner or controlled-env/browser-path construction, plain `RENDERER_UNAVAILABLE` from version/wrong pin/doctor, `OSError` during scratch/source materialization, and typed lint/check/render/verify errors, is normalized into `RecordRenderFailureRequest` before re-raise. Version/doctor/availability/materialization use `phase="source"`. There is no host-network fallback. The outer function never catches `activate_render_state()` merely to call `record_render_failure()`; activation owns candidate serialization through final ambiguity from method entry, even while R+1 is still authoritative. Process-level interruption/crash and `PRODUCTION_STATE_OUTCOME_UNKNOWN` remain explicit-recovery paths. If pre-activation failure persistence itself fails, raise the state persistence error with the original exception attached as a note. No conclusively ordinary post-begin path may leave the attempt `running`.

`prepare_durable_render_artifacts()` is pure construction plus sealing: it does not write. It computes `state/render/sources/<bundle-sha>/...` paths and `state/render/outputs/<output-sha>.mp4`, then creates `RendererSourceReceipt`, `RenderReceipt` and `RenderStateSnapshot` whose paths are those final canonical destinations. It must never call `relative_to()` between scratch source/output siblings or persist an attempt scratch path. Add focused order/persistence tests:

```python
def test_orchestrator_persists_selection_before_version_or_executable_call(tmp_path): ...

@pytest.mark.parametrize("failure", ["version_exception", "wrong_version", "source_exception"])
def test_orchestrator_records_post_begin_availability_as_source_failure(tmp_path, failure): ...

@pytest.mark.parametrize("phase", ["source", "lint", "check", "render", "verify"])
def test_orchestrator_records_every_ordinary_phase_and_never_leaves_running(tmp_path, phase): ...

def test_orchestrator_does_not_retry_record_failure_after_activation_takes_ownership(tmp_path): ...

def test_activation_request_exactly_matches_sealed_durable_n_plus_6_set_and_state_pointer(tmp_path): ...

def test_package_root_exports_render_with_hyperframes_but_omits_adapter_runner_and_scratch_types(): ...

def test_public_render_with_hyperframes_has_no_runner_or_adapter_injection_parameter(): ...

def test_live_committed_fixture_render_state_lifecycle(tmp_path): ...  # opt-in Task 6 only
```

Assert event order begins with `begin_render_attempt`. Pre-candidate failure ends in one `record_render_failure`; success ends in `activate_render_state`. Assert `activation_request(durable, ...)` carries exactly the sealed durable result's sorted `N + 6` `PreparedArtifact`s and exact `RenderStateSnapshotPointer`; it must not accept the scratch `HyperFramesRenderResult`. If activation reports an internally persisted terminal failure or `PRODUCTION_STATE_OUTCOME_UNKNOWN`, `record_render_failure` is not called, so no stale R+1 retry occurs. Failed Manifest status is terminal, active/project/registry pointers are unchanged, and no alternate renderer runs. The live test is marked/guarded so only the explicit Task 6 command selects it; default fake tests do not claim live proof.

- [ ] **Step 6: Prepare and validate the variable exact success artifact set**

For `N` unique bound raster assets, the orchestration layer passes exactly `N + 6` `PreparedArtifact`s, sorted by canonical relative path:

1. one sealed `ResolvedTimeline` JSON at `state/render/timelines/<timeline.content_hash>.json`;
2. one actual source `index.html` at `state/render/sources/<bundle_sha256>/index.html`;
3. exactly `N` actual bound raster files at `state/render/sources/<bundle_sha256>/assets/<full-asset-sha256>.<png|jpg|webp>`;
4. one sealed `RendererSourceReceipt` JSON at `state/render/source-receipts/<source.content_hash>.json` pointing to that exact bundle/root/index/raster set;
5. one sealed `RenderReceipt` JSON at `state/render/render-receipts/<render.content_hash>.json` whose `output_path` is the final canonical durable path;
6. one verified output file at `state/render/outputs/<output_sha256>.mp4`;
7. one sealed `RenderStateSnapshot` JSON at `state/render/states/<state.content_hash>.json` fixing active project/registry, timeline, source bundle/receipt, render receipt and output pointers.

The count is `1 + 1 + N + 1 + 1 + 1 + 1 = N + 6`; no fixed-count shortcut remains. Duplicate assets in multiple spans produce one raster artifact but remain explicitly referenced by each binding. `activate_render_state()` parses/reseals the four JSON artifacts, audits/re-hashes the HTML and every raster, recomputes the exact bundle hash, rehashes/reopens every promoted file, verifies output size/hash, validates the snapshot project/registry and cross references, and requires `next_render_state` to point exactly at the state artifact. Extra, missing, duplicate or noncanonical artifacts fail. The immutable writer uses file temp -> file fsync -> promote-without-overwrite -> parent-directory fsync -> reopen verify for every artifact/output; it explicitly creates each already-validated canonical parent before opening a temp file.

- [ ] **Step 7: Durably prepare the candidate, then atomically activate one pointer**

Add:

```python
def activate_render_state(self, request: ActivateRenderStateRequest) -> ProductionManifest: ...
```

It requires the exact R+1 running attempt and unchanged project/registry pair. From method entry, activation owns four windows under the same `state/commit.lock`:

1. **R+1 before candidate replace is attempted:** build the exact candidate/hash from `ActivateRenderStateRequest`. Candidate Manifest serialization, temp open/write, file fsync and the explicit pre-replace checkpoint are activation-owned. Any ordinary/non-outcome-unknown failure is caught internally; remove only the exact owned candidate temp, then atomically write/reopen terminal R+2 `FAILED` from authoritative R+1. That failed attempt contains exact `candidate_render_state` and aggregate hash of the `N + 6` artifact identities for orphan evidence, keeps `active_render_state=base_render_state`, keeps project/registry unchanged, and records `render_phase="activate"`, typed code/redacted bounded message and finished time. The outer orchestrator never retries failure persistence.
2. **candidate replace/directory-fsync/reopen ambiguity:** reopen the Manifest under the still-held lock. Accept only the exact R+1 begun identity or exact R+2 candidate-prepared identity for the same request. If exact R+1 is authoritative and the checkpoint/file-op evidence conclusively proves pre-replace, write the terminal R+2 activation-owned failure above. If exact R+2 is authoritative and no final replace was attempted, an exact replay continues normally; an ordinary candidate-transition error terminalizes to R+3 `FAILED` with candidate/hash retained. If neither identity or the replace outcome is provable, raise `PRODUCTION_STATE_OUTCOME_UNKNOWN` and require recovery. Never overwrite an uncertain candidate state.
3. **authoritative R+2 until final replace is attempted:** every ordinary/non-outcome-unknown final succeeded-Manifest serialization, temp open/write, file fsync or pre-replace failure is caught internally and terminalized as R+3 `FAILED` from authoritative R+2, retaining candidate/hash and base active/project/registry state.
4. **final replace/post-replace ambiguity:** once final active-pointer replace is attempted, replace/directory-fsync/reopen/post-replace uncertainty is `PRODUCTION_STATE_OUTCOME_UNKNOWN` only. Never overwrite it with `FAILED`; explicit recovery compares exact old/new triples.

The successful path has two separate durable Manifest transitions after the entire variable exact immutable set verifies:

1. **candidate-prepared transition:** atomically replace a running Manifest attempt containing `candidate_render_state=next_render_state`, the exact sorted variable-set `candidate_artifacts_hash` and `render_phase="activate"`; keep `active_render_state=base_render_state` and keep project/registry byte-for-byte unchanged. The candidate-prepared Manifest itself must complete temp write -> file fsync -> replace -> parent-directory fsync -> reopen/identity verification before final activation begins.
2. **final succeeded transition:** atomically replace one Manifest with `active_render_state=next_render_state` and the same project/registry pointers, then mark the exact attempt `succeeded`. Only this second replace is the active render commit point.

For either activation-owned ordinary-failure window, reopen and verify the terminal Manifest before re-raising the original typed activation error. If the internal terminal-failure write cannot become authoritative, raise `PRODUCTION_STATE_OUTCOME_UNKNOWN` and require recovery; never attempt an outer failure write.

If the base Manifest revision is `R`, a fresh success has exactly `R+1` after `begin_render_attempt()`, `R+2` after candidate preparation and `R+3` after the final pointer switch. An outer pre-activation failure is terminal R+2 without candidate. An activation-owned pre-candidate-replace failure is terminal R+2 with candidate/hash. An activation-owned post-candidate pre-final-replace failure is terminal R+3 with candidate/hash. These two R+2 terminal shapes are distinguished by candidate presence and request identity.

Exact replay behavior:

- exact begin replay returns the current matching attempt at begun, candidate-prepared, failed or succeeded stage without revision increment;
- exact activation replay from begun state revalidates/promotes the same immutable set, writes candidate-prepared once, then final once;
- exact activation replay from candidate-prepared state revalidates the entire `N + 6` artifact set and performs only the final switch;
- exact activation replay after succeeded state returns the active Manifest without artifact rewrite or revision increment;
- exact replay after an internally terminal failed R+2 or R+3 returns that failed Manifest and does not retry activation; the outer layer never submits `RecordRenderFailureRequest` after activation was called;
- a stale expected revision is accepted only for one of those exact identities; any attempt-ID/request/artifact/pointer mismatch is rejected.

Before the final `os.replace`, old/`None` render state stays active; after it, candidate is active. Candidate ambiguity follows window 2 exact reopen rules; final ambiguity follows window 4 outcome-unknown rules.

Extend `CommitPhase` with render-specific checkpoints:

```python
BEFORE_RENDER_CANDIDATE_MANIFEST_SERIALIZATION
AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_OPEN
AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_WRITE
AFTER_RENDER_CANDIDATE_MANIFEST_FILE_FSYNC
BEFORE_RENDER_CANDIDATE_MANIFEST_REPLACE
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

Valid old state is `(base_project, base_registry, base_render_state)`; valid new state is `(candidate_project, candidate_registry, candidate_render_state)`, where project/registry members are unchanged and the candidate snapshot itself fixes those exact pointers. A begun R+1 attempt with no candidate and old active state is interrupted before authoritative preparation; recovery scans and preserves complete canonical timeline/source HTML/raster/receipt/output/state orphans without inventing candidate identity. A candidate-prepared R+2 attempt with old active state is interrupted before final activation and its exact variable artifact set is preserved/reported. New active state means succeeded. Any changed project/registry member, render pointer outside old/new, tampered pointer/file/snapshot, source bundle hash mismatch, candidate hash mismatch, incomplete candidate or mixed state fails recovery rather than guessing.

Cleanup is bounded to fixed Manifest temp, owned immutable temps and scratch/temp files below `state/render/attempts/<safe-id>/` for non-succeeded attempts. Never delete an active or user output. Preserve and report complete orphan immutable timelines, canonical source HTML/raster bundles, source receipts, render receipts, render states and outputs; do not activate or GC them. Succeeded attempt scratch is not auto-deleted by recovery unless a separately verified cleanup marker owns it.

- [ ] **Step 9: Add crash injection coverage**

Extend `tests/helpers/p2a_crash_worker.py` and recovery tests with process-level crashes at:

```text
begin attempt Manifest temp / fsync / replace / directory fsync
each timeline, source HTML, bound raster, receipt, state or output temp / file fsync / promote / directory fsync / reopen verify
candidate Manifest serialization / temp open-write / file fsync / pre-replace / replace / directory fsync / reopen verify
final Manifest temp / file fsync / replace / directory fsync
```

Separately add one-shot ordinary exception injection tests inside `activate_render_state()`:

```python
@pytest.mark.parametrize(
    "phase",
    [
        CommitPhase.BEFORE_RENDER_CANDIDATE_MANIFEST_SERIALIZATION,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_OPEN,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_FILE_FSYNC,
        CommitPhase.BEFORE_RENDER_CANDIDATE_MANIFEST_REPLACE,
    ],
)
def test_activation_candidate_pre_replace_ordinary_failure_is_terminal_r2(phase): ...

@pytest.mark.parametrize(
    "phase",
    [
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_REPLACE,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_DIRECTORY_FSYNC,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_VERIFICATION,
    ],
)
def test_activation_candidate_ambiguity_reopens_exact_r1_or_r2_or_returns_unknown(phase): ...

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

For each candidate serialization/temp-open-write/file-fsync/pre-replace ordinary case assert authoritative terminal R+2 `FAILED`, `render_phase="activate"`, typed/redacted error, base `active_render_state`, unchanged project/registry, retained exact candidate pointer/variable-set aggregate hash, no running residue and no outer failure-writer call. Assert the one-shot failure writer cleans only its owned candidate temp and is not reinjected.

For candidate replace/directory-fsync/reopen cases inject reopened exact R+1, exact R+2 and mixed/tampered identities. Conclusively pre-replace exact R+1 terminalizes at R+2 with candidate/hash; exact R+2 either continues on replay or terminalizes at R+3 for the injected ordinary error; unprovable/mixed state raises `PRODUCTION_STATE_OUTCOME_UNKNOWN` and stays for recovery. Never overwrite uncertainty.

For each final ordinary pre-replace case assert authoritative revision R+3, terminal `FAILED`, `render_phase="activate"`, typed/redacted error, base `active_render_state`, unchanged project/registry, retained candidate pointer/variable-set aggregate hash, no running attempt and no outer failure-writer call. Assert the failure writer cleans only its owned final temp and is not reinjected. For after-final-replace/directory-fsync ambiguity assert `PRODUCTION_STATE_OUTCOME_UNKNOWN`, no FAILED overwrite, then explicit recovery resolves only by exact old/new triple.

For every process-level pre-final-replace crash assert old/`None` pointer remains active and project/registry unchanged. Candidate-prepared temp/fsync crashes recover as begun unless the exact replacement is readable; replace/directory-fsync ambiguity must reopen and accept only the exact candidate/hash identity. Recovery performs bounded temp cleanup and preserves/reports every complete orphan. For final replace/directory-fsync ambiguity assert explicit recovery resolves only by exact old/new render pointer plus unchanged pair. Assert revisions `R+1/R+2/R+3`, replay from each stage, replay after recovered success and conflicting attempt-ID rejection.

- [ ] **Step 10: Export the stable lifecycle surface explicitly**

Export from `production/__init__.py`:

```text
BeginRenderAttemptRequest
RecordRenderFailureRequest
ActivateRenderStateRequest
RenderAttemptPaths
RenderArtifactPointer
RenderSourceFilePointer
RenderSourceBundlePointer
RenderOutputPointer
RenderStateSnapshot
RenderStateSnapshotPointer
ProductionStateCommitter
render_with_hyperframes
```

The state lifecycle methods remain `ProductionStateCommitter.begin_render_attempt()`、`record_render_failure()`、`activate_render_state()` and `render_attempt_paths()`, with their request/path models as stable data contracts. The only stable P3 renderer-execution API exported from the package root is durable `render_with_hyperframes()`. Do **not** export `HyperFramesAdapter`, `RendererRunner`, `_NetworkIsolatedHyperFramesRunner`, `HyperFramesRenderAttempt` or `HyperFramesRenderResult`; they are module-internal/test boundaries and cannot be used to bypass network isolation. Keep `_candidate_artifacts_hash`, Manifest transition builders, `CommitPhase`, crash injectors, native file ops, canonical render path constructors/validators, recovery scanners and serialization/cross-validation helpers private to their modules.

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

Expected: selection durably fixes timeline/project/registry provenance before any executable call; exact `0.7.103` version/doctor precede lint; canonical source HTML/raster bytes and final output path are in the variable prepared set; outer orchestration records only ordinary failures before activation is called; `activate_render_state()` owns all four candidate/final windows, producing terminal R+2 or R+3 with candidate/hash for conclusive ordinary failures, exact R+1/R+2 reopen handling for candidate ambiguity, and outcome unknown for unprovable candidate or final-replace ambiguity; no outer retry occurs; success `R+1/R+2/R+3` revisions and replay are deterministic; crash recovery preserves complete source/render orphans; 2.0 historical/custom operation loading stays compatible; 2.1 project/registry changes atomically clear `active_render_state`, while same-pair commits retain it only after full verification.

### Task 6: Run Committed-Fixture Integration and Regression Proof

**Files:**
- Verify: all P3/P2A-owned files
- Verify unchanged: Legacy runtime, public CLI, Manifest v1 and flat layout

- [ ] **Step 1: Confirm Task 0 gate evidence still matches the lock**

Verify the recorded Task 0 compatibility proof names exact `hyperframes@0.7.103`, the accepted browser executable/revision, successful version/doctor/lint/check/preview/two renders, source hashes, trace audit, ffprobe metadata and equal framemd5. Recheck `package-lock.json` integrity and browser `--version`. This is a drift check; the Renderer Gate was already required before Task 1 and must not be deferred here.

- [ ] **Step 2: Run the committed-fixture production integration proof**

Run the opt-in `test_live_committed_fixture_render_state_lifecycle` added in Task 5. Do not wrap pytest in an outer namespace: the public API must prove that its private production runner creates a fresh namespace for every HyperFrames command. Wrap pytest with `strace -ff` only to observe the runner and all descendants:

```bash
export P3_LIVE_RENDERER=1
export HYPERFRAMES_BROWSER_PATH="$P3_HYPERFRAMES_BROWSER_PATH"
P3_INTEGRATION_EVIDENCE=$(mktemp -d)
export P3_INTEGRATION_EVIDENCE
strace -ff -e trace=network -o "$P3_INTEGRATION_EVIDENCE/integration.net" \
  python -m pytest tests/test_production_hyperframes.py -q \
  -k test_live_committed_fixture_render_state_lifecycle
if rg -n 'connect\(|sendto\(|sendmsg\(' "$P3_INTEGRATION_EVIDENCE"/integration.net* \
  | rg 'AF_INET6?' | rg -v '127\.0\.0\.1|\[::1\]|inet_pton\(AF_INET6, "::1"'; then
  exit 1
fi
```

The test copies the committed PNG fixture into a disposable project, builds a real `STATIC_IMAGE`/cut-only timeline with a non-default deterministic transform/opacity/z-order, calls public `render_with_hyperframes()` (which constructs the private isolated runner) once, and completes `begin_render_attempt -> version -> doctor -> source -> lint -> check -> render -> verify -> activate_render_state`. It asserts final `active_render_state`, exact project/registry/timeline provenance, canonical durable source HTML/raster bundle and hashes, source/render receipts, canonical output path/hash, decoded-frame evidence, no audio, scratch paths absent from receipts, and unchanged Legacy state. Unit tests already assert exact subprocess argv; this harness hashes committed source inputs before/after and parses all trace files with the same “any non-loopback AF_INET/AF_INET6 destination fails” rule from Task 0. It is an integration/regression proof, not a late compatibility gate or a substitute for the pre-Task-1 hand-authored spike.

The live test is selected only by the command above and fail-closes unless `P3_LIVE_RENDERER=1`, exact binary/browser and namespace tracing are present. Default tests exercise the same lifecycle with a fake runner and no Node/Chrome/network; the opt-in test may be deselected by default, not silently reported as a passing live proof.

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

Expected: all P3/P2A fake tests pass; the single explicitly named live integration case is deselected or skipped unless `P3_LIVE_RENDERER=1`, and that skip is never presented as live proof.

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

Only after the pre-edit Task 0 compatibility gate and every Task 6 committed-fixture/focused/Legacy/full/scope check pass, document:

- importable `CompositionSpec`/`resolve_composition()`/durable `render_with_hyperframes()` and stable lifecycle data API; low-level adapter/runner remain unexported;
- only accepted `STATIC_IMAGE` + zero-duration `CUT` + local PNG/JPEG/WebP semantics, with all other visual strategies, crossfade and motion directives explicitly blocked;
- `ResolvedTimeline` as only order/timing truth;
- exact pinned tool/browser versions and one-renderer-per-attempt rule;
- parsed-URL/raster audit, deterministic inline CSS, durable source bundle/hash/lint/check and canonical-output render receipt fields;
- exact timeline/project/registry replay provenance, Manifest 2.0/2.1 compatibility, pair-change blanket render invalidation, candidate-prepared transition, outer pre-activation failure versus activation-owned four-window failure/ambiguity, one active render-state pointer, canonical immutable layout and P2A-owned recovery behavior;
- verify errors map to P3 `RENDER_FAILED` without leaking `FFMPEG_FAILED`;
- fake/no-network CI versus the pre-edit egress-contained compatibility gate and later committed-fixture integration proof;
- forward-compatible rollback keeps 2.1 read/recovery and disables new entrypoints; no downgrade exists;
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

Expected: docs use completed Task 0 compatibility plus Task 6 integration/regression evidence and describe only tested local behavior; every future capability remains planned/not implemented.

### Task 8: Obtain Final Independent Review and Record Branch Truth

- [ ] **Step 1: Obtain independent review after docs**

Review brief:

```text
Verdict must be accept, accept with concerns, or reject.
Verify P3 started from accepted P2A and did not add a second writer/Manifest.
Verify CompositionSpec is edit intent and ResolvedTimeline is the only order/timing owner.
Verify only STATIC_IMAGE, zero-duration CUT and local PNG/JPEG/WebP are accepted;
all motion/video/hybrid strategies, crossfade and motion directives typed-fail.
Verify integer frame/sample boundaries, exact Shot asset role/ID/MIME/hash, rejection of non-default trim,
actually-applied inline CSS transform/origin/opacity/z-order, delivery profile and fingerprint.
Verify no raw asset ID enters a path, every target is contained before mkdir/copy,
magic/MIME/suffix and parsed HTML/CSS URLs enforce the exact declared raster set.
Verify one lstat/openat O_NOFOLLOW helper owns all artifact reads/reopens, scratch writes
use O_EXCL/O_NOFOLLOW, contained/external symlinks and inode-swap attempts fail closed.
Verify selection fixes timeline fingerprint and active project/registry before execution.
Verify RenderStateSnapshot repeats that provenance and exact replay rejects any mismatch.
Verify changed project/registry commit atomically clears active render state, same-pair
retention fully verifies it, and immutable former source/render artifacts remain orphans.
Verify candidate-prepared state is durable before the final single-pointer switch.
Verify outer orchestration never writes failure after activation method entry transfers ownership.
Verify activation owns candidate pre-replace, candidate ambiguity, R+2-to-final and final ambiguity windows.
Verify conclusive ordinary cases terminalize with exact R+2/R+3 candidate evidence while uncertainty remains outcome unknown.
Verify exact replay/recovery and P2A 2.0 custom-operation compatibility.
Verify canonical durable source HTML/raster bytes and final output path are in the variable
N+6 artifact set; no scratch path enters source/render receipts or snapshot identity.
Verify activation_request consumes the sealed durable result, not scratch render result,
and its sorted artifacts/next pointer exactly match that durable N+6 identity.
Verify HyperFrames source comes only from timeline/assets and is parsed/hash/lint/check audited.
Verify exact 0.7.103 version and doctor run with controlled validated browser env.
Verify public render_with_hyperframes alone constructs the private namespace runner;
every tool argv has exact unshare flags/fixed exec "$@", shell=False and no host fallback,
and package-root exports omit adapter, runner and scratch result types.
Verify probe/ffprobe/framemd5/plain errors map to non-retryable RENDER_FAILED verify;
FFMPEG_FAILED never crosses the P3 public boundary.
Verify one attempt selects exactly one renderer and no Remotion/fallback/double render exists.
Verify Task 0 gate precedes Task 1, traces reject every non-loopback AF_INET/AF_INET6
destination, preview readiness retries and process-group cleanup leaves no descendant.
Verify Task 6 separately proves committed-fixture lifecycle integration.
Verify rollback keeps 2.1 reader/recovery, disables new entrypoints and never downgrades/deletes.
Verify docs match Task 0/Task 6 evidence and frame-equivalent proof is not byte-identical claim.
Verify Legacy CLI/Manifest/layout and P4/P5/P2A/Provider boundaries remain unchanged.
```

Required exit verdict: `accept` or `accept with concerns` with no blocking issue. The parent must inspect important claims, final diff and commands directly. Any review fix must rerun its affected Task 0 gate and/or Task 6 proof and rescan Task 7 docs before acceptance.

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
- selection with exact timeline/project/registry provenance is persisted by `begin_render_attempt()` before version/doctor/source/lint/check/render; wrong version, failed doctor, plain `RENDERER_UNAVAILABLE` and source exceptions are normalized to phase `source`, durably failed, then re-raised;
- missing `unshare`/user-net-PID namespace/loopback/bash/ip capability is non-retryable `RENDERER_UNAVAILABLE`, persisted as source failure after begin; no tool runs on the host network as fallback;
- lint failure: stop before `check`/render and persist the exact typed failed phase through `record_render_failure()`;
- check failure: stop before render and persist the exact typed failed phase through `record_render_failure()`;
- render/timeout/output verification failure: persist the typed phase and leave `active_render_state` old/`None`; probe/ffprobe/framemd5/parse errors, including underlying `FFMPEG_FAILED`, cross the P3 boundary only as non-retryable `RENDER_FAILED` phase `verify`;
- a normal P2A project/registry commit that changes either pointer clears `active_render_state` atomically and preserves the former timeline/source bundle/receipts/output/state as orphan evidence; same-pair commit retains it only after exact provenance verification;
- before `activate_render_state()` is called, outer `render_with_hyperframes()` owns exactly one `record_render_failure()` write from R+1; after method entry it never catches activation to retry failure persistence;
- activation-owned candidate serialization/temp-open-write/file-fsync/pre-replace ordinary failure becomes terminal R+2 failed with exact candidate/hash and base active/project/registry state;
- candidate replace/directory-fsync/reopen ambiguity accepts only exact reopened R+1/R+2; conclusive ordinary state terminalizes at the matching next revision, while unprovable state remains outcome unknown;
- authoritative candidate-prepared R+2 persists exact candidate/hash while leaving active/project/registry pointers unchanged; final-temp/file-fsync/pre-replace ordinary failure becomes terminal R+3 failed;
- crash before final Manifest replace: explicit P2A recovery distinguishes begun from candidate-prepared, owns bounded temp cleanup, preserves/reports complete immutable timeline/source HTML/raster/receipt/output/state orphans and keeps the old render pointer;
- final replace/directory-fsync/post-replace ambiguity is `PRODUCTION_STATE_OUTCOME_UNKNOWN`, never overwritten by failed; recovery validates the candidate render pointer plus unchanged project/registry pair and reads exact manifest-selected snapshot/artifact/output hashes, not console or Agent memory;
- renderer mismatch/unavailable: fail explicitly; no HyperFrames-to-Remotion or Remotion-to-HyperFrames retry.

Rollback after a 2.1 Manifest may exist is **forward-compatible**, not a schema downgrade. Keep the 2.1 models, reader, `ProductionStateCommitter` render recovery and project/registry blanket invalidation. First make a focused rollback commit that disables new P3 entry by removing its public `render_with_hyperframes` export and making only a fresh `begin_render_attempt()` fail closed with typed non-retryable `RENDERER_UNAVAILABLE`; exact read/replay needed to recognize existing terminal state and explicit recovery remain available. Run 2.0/2.1 reader/recovery and Legacy tests before removing any tool surface.

Only adapter/docs/dependency commits may then be reverted when `git grep` proves no retained 2.1 reader/recovery import depends on them:

```bash
git revert "$(git log -1 --format=%H --grep='^docs: document p3 composition runtime$')"
git revert "$(git log -1 --format=%H --grep='^feat: add hyperframes renderer adapter$')"
git revert "$(git log -1 --format=%H --grep='^build: pin hyperframes renderer tool$')"
```

If the adapter commit cannot be cleanly removed without breaking retained source-bundle models/verification, leave its code installed but unreachable; dependency removal is then also deferred. Never revert the schema/writer commit, composition contracts or source materializer merely to make old code reject 2.1. No downgrade is implemented. A 2.1 -> 2.0 downgrade would require separate explicit authorization and a crash-safe migration plan/tests. Do not delete `projects/**`, accepted P2A snapshots, source bundles, receipts or user renders. A separate explicit P2A GC policy decides when orphaned immutable artifacts may be reclaimed.

## Acceptance Criteria

P3 is accepted only when:

1. accepted P2A exists; `ProductionStateCommitter` remains the only durable write/pointer-switch/recovery owner, historical non-empty operation compatibility remains, Manifest 2.0/2.1 read compatibility is proven without rewrite, and project/registry pair changes atomically clear `active_render_state` while preserving orphan bytes;
2. `CompositionSpec` captures explicit edit intent without filesystem discovery;
3. `ResolvedTimeline` is the only order/timing/layer truth and contains integer frame/sample boundaries;
4. only `STATIC_IMAGE`, zero-duration `CUT`, local PNG/JPEG/WebP, default-only trim and no motion directives are accepted; exact `(asset_role, asset_id)`, MIME/hash, actually-applied inline CSS transform/origin/opacity/z-order, delivery profile, renderer kind/version and deterministic composition fingerprint are persisted;
5. identical resolved inputs produce identical timeline/source hashes and frame-equivalent output under the pinned tool/runtime;
6. no byte-identical MP4 claim is made without a separately proven encoder/container contract;
7. every materialized target is contained before creation, filename derives only from full asset hash plus allowlisted lowercase raster suffix, and one lstat/openat `O_NOFOLLOW` helper owns source/scratch/durable/reader bytes; `O_EXCL|O_NOFOLLOW` writes, contained/external symlink tests and inode-swap tests fail closed;
8. parsed HTML/CSS media URLs exactly equal declared relative raster sources; source contains no SVG/HTML/CSS asset payload, wall-clock randomness, implicit network fetch, remote/absolute/parent/scheme/data/blob URL or untracked file;
9. each attempt has one authoritative selection identity and one HyperFrames execution path; `BeginRenderAttemptRequest` does not duplicate timeline/project/registry fields;
10. Remotion is neither installed nor implemented and no double-render/fallback exists;
11. one immutable `RenderStateSnapshot` fixes exact active project/registry, selection/timeline fingerprint, canonical durable source HTML/raster bundle, source/render receipts and final canonical output pointers; one Manifest pointer activates it and no scratch path is semantic;
12. Task 0 exact 0.7.103 version/doctor/lint/check/preview/two-render compatibility gate passes before Task 1 using the same namespace wrapper contract; runtime selection is durable before any executable call, only private `_NetworkIsolatedHyperFramesRunner` runs tools with fresh user/net/PID namespace + fixed `exec "$@"`/`shell=False`, controlled env injects the validated browser path, missing capability has no host fallback, outer orchestration records every ordinary availability/source/lint/check/render/verify exception only before activation method entry, and `FFMPEG_FAILED` never leaks across P3;
13. `activation_request()` consumes the sealed durable `N+6` result, never scratch result; `activate_render_state()` owns all four windows: candidate pre-replace ordinary failure is terminal R+2 with exact candidate/hash; candidate ambiguity reopens only exact R+1/R+2 or returns outcome unknown; authoritative R+2 pre-final ordinary failure is terminal R+3; final replace/post-replace ambiguity remains outcome unknown. All terminal paths preserve base active/project/registry state, successful revisions remain `R+1/R+2/R+3`, and exact replay/recovery leaves no conclusively ordinary running residue;
14. complete timeline/source-bundle/receipt/state/output orphans are preserved and reported; default tests are fake/no-network, the pre-edit Task 0 gate uses the pinned browser with OS-level external-egress denial/observation plus retrying preview cleanup proof, and Task 6 separately proves the committed fixture/lifecycle integration;
15. no Audio/Caption, P5 graph, Provider/cloud/paid API, new CLI or Legacy schema/layout enters the diff;
16. focused P3/P2A, Legacy regression and full default suites pass;
17. forward rollback keeps 2.1 read/recovery and disables new entrypoints without downgrade or artifact deletion; docs are written only after live/focused/Legacy/full proof, then final independent review has no blocker.

## Plan-Time Known Blockers

- **Plan drafting / receipt contract:** none; the user selected the versioned `RenderStateSnapshot` approach and authorized this in-place revision on 2026-08-09.
- **P2A prerequisite:** satisfied on local `main`; it is not a P3 blocker.
- **P3 runtime execution:** authorized. Task 0 must still fail closed on an exact package integrity/source/browser mismatch, unavailable OS egress containment or conflicting workspace ownership; these are verification failures, not missing authorization.
- **Renderer offline gate:** env controls are necessary but insufficient; the live spike must prove external egress denial/observation, loopback-only preview and explicit preinstalled `HYPERFRAMES_BROWSER_PATH`.

## Execution Authorization Boundary

The user explicitly authorized P3 runtime execution on 2026-08-09 with: (a) one versioned `RenderStateSnapshot` selected by `ProductionManifest.active_render_state`; and (b) the full Renderer Gate, including exact `hyperframes@0.7.103`, necessary matching Chromium installation and an OS-egress-contained live lint/check/preview/render spike. Implementation must follow Tasks 0-8 and stop on verification failure or scope conflict. The authorization does not allow `npx` runtime resolution, another HyperFrames version/integrity, Remotion, Audio/Caption, P5+, Provider/cloud/paid API, new CLI, Legacy schema/layout changes, arbitrary network during the spike, push, merge or release.
