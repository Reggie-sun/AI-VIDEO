# AI-VIDEO Agentic Production Harness P3 Deterministic Composition and HyperFrames Adapter Implementation Plan

> **For agentic workers:** 实施本 plan 时，REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans。按 Task 顺序执行，并使用 checkbox (`- [ ]`) 跟踪进度。

**Goal:** 在 accepted P2A state commit protocol 之上，实现 renderer-neutral `CompositionSpec`、唯一 order/timing owner `ResolvedTimeline`、exclusive HyperFrames adapter、renderer source receipt 和 render receipt，并以 image-only silent fixture 证明 deterministic composition。

**Architecture:** `src/ai_video/production/models.py` 继续拥有 v2 schema，新的 `composition.py` 只负责从显式 Shot/asset bindings 解析整数 frame/sample boundaries 和 composition fingerprint，新的 `hyperframes.py` 只把已解析 timeline materialize 成受审计的 local source 并通过单一 HyperFrames CLI 执行。所有 durable write、active pointer switch、failed/succeeded attempt commit 都必须委托 accepted P2A canonical state committer；P3 不新建第二套 Manifest、timeline、renderer control plane，也不触碰 Legacy runtime。

**Tech Stack:** Python 3.11+、Pydantic v2、`Decimal`、`hashlib`、现有 `AiVideoError`/`ErrorCode`、现有 `probe_clip()`、pytest fake runner；在单独 dependency-install authorization 后才允许加入 pinned `hyperframes@0.7.102`、Node.js `>=22`、FFmpeg 和本地 Chromium。默认 CI 不调用 Node、Chrome、network 或真实 render。

---

Status: Docs-only implementation planning. This document is not P3 runtime implementation authorization.

## Problem Boundary

P3 的唯一 production path 是：

```text
accepted P2 LoadedProductionProject
+ explicit CompositionSpec
+ exact Asset Registry IDs, hashes and resolved contained paths
+ accepted P2A staging/commit owner
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
lint -> inspect -> render through one pinned tool
        |
        v
measured output + render receipt
        |
        v
P2A atomic attempt commit
```

本 slice 只验收已有 registered local image/composition assets 的 silent composition。它不生成素材，不引入 voice/caption/audio tracks，不实现 dependency invalidation，也不通过新 CLI 暴露 v2 runtime。

## Hard Prerequisites

P3 runtime implementation 有三个硬前置；任一未满足都必须停止，不得开始 Task 1：

1. **Accepted P2A:** 必须已有独立 P2A plan、实施、crash-injection tests 和 acceptance，能够提供 staging、atomic content commit、Production Manifest pointer switch、failed attempt persistence 和 orphan/partial recovery。2026-08-09 当前仓库没有 P2A plan 或 implementation；这不阻塞本 plan 的编写，但阻塞本 plan 的执行。
2. **Renderer Gate:** 必须重新核对并记录 HyperFrames package、CLI commands、license、Node/FFmpeg/Chromium requirements、pinned installation mode 和 offline controls，并获得 Node dependency/tool installation 的独立授权。
3. **State and Layout Gate:** 如果 accepted P2A 没有通用的 timeline/source/render receipt commit surface，任何 Production Manifest schema 或 v2 artifact layout 扩展都必须获得独立授权并先更新本 plan；P3 不得临时把 receipts 写进 Legacy Manifest v1 或 `runs/<run_id>/` flat layout。

执行前还需确认没有其他 writer 拥有这些目标文件。若 current tree 有 unrelated uncommitted changes，使用独立 branch/worktree；不要在 dirty tree 上写入。

## Current Renderer Gate Evidence

2026-08-09 的只读核对结论：

| Surface | Verified Current Fact | Planning Consequence |
| --- | --- | --- |
| Codex plugin | `codex plugin list` 显示 `hyperframes@openai-curated` 为 `not installed` | plugin 不是 runtime readiness 证据；安装仍需独立授权 |
| Cached skill bundle | 本机 cache 只有 plugin bundle `0.1.2` | cache 可用于了解能力，但不能作为 CLI installed/version proof |
| PATH/global npm | `command -v hyperframes` 无结果；`npm list -g --depth=0 hyperframes` 为空 | adapter 不得假设 PATH binary |
| Published CLI | official npm metadata 的 `hyperframes` latest 为 `0.7.102`，Apache-2.0，Node `>=22` | Renderer Gate 通过时只允许 exact pin `0.7.102`；禁止 `latest`/caret/range |
| Local Node | `v22.21.0` | 满足 current Node lower bound，但 implementation day 仍需重跑 |
| Local FFmpeg | PATH 存在 `/home/reggie/miniconda3/bin/ffmpeg` | 只证明 binary 存在；codec、Chrome 和 render parity 未验证 |
| CLI surface | upstream CLI 注册 `lint`、`inspect`、`preview`、`render`、`check` | P3 source receipt 必须单独保存 lint/inspect evidence；preview/render 只在 live spike gate 执行 |
| CLI drift | upstream `inspect` 已进入向 aggregate `check` 迁移的 deprecated path | exact pinned version 必须锁住 command/JSON contract；升级需要 parity review |
| Network behavior | upstream CLI 可做 telemetry、npm update check 和 background auto-install | invocation env 必须固定 `CI=1`、`HYPERFRAMES_NO_TELEMETRY=1`、`DO_NOT_TRACK=1`、`HYPERFRAMES_NO_UPDATE_CHECK=1`、`HYPERFRAMES_NO_AUTO_INSTALL=1`；source audit 还必须拒绝 remote URLs/fetch |

Primary sources：

- [HyperFrames repository and runtime overview](https://github.com/heygen-com/hyperframes)
- [HyperFrames CLI package metadata](https://github.com/heygen-com/hyperframes/blob/main/packages/cli/package.json)
- [HyperFrames CLI commands](https://github.com/heygen-com/hyperframes/blob/main/packages/cli/README.md)
- [HyperFrames Apache-2.0 license](https://github.com/heygen-com/hyperframes/blob/main/LICENSE)
- [HyperFrames command registration and executable-boundary error handling](https://github.com/heygen-com/hyperframes/blob/main/packages/cli/src/cli.ts)
- [HyperFrames telemetry opt-out](https://github.com/heygen-com/hyperframes/blob/main/packages/cli/src/commands/telemetry.ts)
- [HyperFrames update-check controls](https://github.com/heygen-com/hyperframes/blob/main/packages/cli/src/utils/updateCheck.ts)

不得把 cached skill 中的 `--docker` 描述升级为本项目的 byte-identical guarantee。P3 只要求在相同 `ResolvedTimeline`、renderer source、asset hashes 和 pinned tool/runtime 下得到 frame-equivalent output；container metadata/encoder behavior 没有独立契约时，不承诺 byte-identical MP4。

## Open-Source Fusion Decision

本 plan 依照 `github-oss-fusion` 只融合最小结构、测试和错误处理思想，不复制 external implementation：

| Repository | Inspected | Fused | Rejected or Deferred |
| --- | --- | --- | --- |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | README、CLI metadata、license、CLI source、CLI tests | exact version pin、machine-readable lint/inspect、single executable failure boundary、offline env controls、source-first renderer adapter | 不复制 TypeScript renderer internals；不采用 auto-update、telemetry、cloud/Lambda、TTS/transcribe |
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
| durable staging/commit/pointer | accepted P2A committer | P3 不写第二份 Manifest，不自行 atomic-switch active state |
| measured render evidence | `RenderReceipt` built from output hash + `probe_clip()` | console text 不是 final status |

## Old Path Decisions

- 不修改或复用 `src/ai_video/workflow_renderer.py` 作为 composition renderer；它继续只拥有 Legacy Comfy workflow template/binding pure render。
- 不修改 `src/ai_video/pipeline.py` 作为 v2 timeline owner；Legacy ordered Shot chaining 保持原状。
- 不把 `src/ai_video/ffmpeg_tools.py::stitch_clips()` 当作 canonical renderer；P3 只复用 `probe_clip()` 验证 HyperFrames output。
- 不修改 `src/ai_video/manifest.py` 或 Legacy `RunManifest`。
- 不让 `ProductionProject.renderer_policy.default_preference` 静默选择未实现 adapter；requested/default 为 `remotion` 时必须 typed-fail。
- 不在 HyperFrames failure 后调用 Remotion、ffmpeg stitch 或任何 alternate final-render path。
- 不扫描 project directories、glob、mtime 或 lexicographic filename 来决定 Shot/layer order。
- 不把 arbitrary Codex-authored HTML 直接视为 accepted source；source 必须通过 timeline materialization、static audit、hash、lint 和 inspect。

## Unchanged Contracts

- Legacy public CLI 仍只有 `ai-video validate`、`ai-video run`、`ai-video resume`。
- Legacy default-local ComfyUI、Manifest v1、resume、flat `runs/<run_id>/` layout 和 current workflow loader/renderer 均不变。
- P2 `ProductionProject`、creative artifact、Asset Registry、path containment、read-only loading 和 content hashes 不被重定义。
- `validate` 保持无副作用，不安装 tool、不创建 v2 state、不联网或 render。
- P3 不实现 Audio/Caption domain、P5 dependency graph/desired-applied lifecycle、P2A commit protocol、QA/repair、Provider、cloud、paid API、new CLI 或 Legacy schema/layout migration。
- 安装 Node dependency/tool、下载/安装 Chromium、修改 public CLI、Production Manifest schema 或 artifact layout 都保持独立 authorization gate。

## Contract Details

P3 contract 必须显式包含：

- `CompositionSpec`: ordered `shot_ids`、exact asset bindings、visual layer/edit intent、trim、fixed-point transform、fixed-point opacity、z-order、transition、delivery profile 和 requested renderer。
- `ResolvedTimeline`: width/height/FPS/codec profile、sample rate、integer `start_frame`/`duration_frames`、integer `start_sample`/`duration_samples`、asset ID/hash/materialized path、trim、transform、opacity、z-order、transition、total frames/samples、renderer kind/version 和 `composition_fingerprint`。
- duration resolution: P3 silent fixture 只接受 `DurationPolicy.mode == "fixed"`；使用 `Decimal(str(seconds))`，`ROUND_CEILING` 到整数 frame，绝不使用 binary float 累加。
- sample boundaries: `start_sample = floor(start_frame * sample_rate / fps)`，`end_sample = floor(end_frame * sample_rate / fps)`，duration 是两者之差。P3 只建立 timebase，不创建 audio track。
- transition resolution: `cut` 为 0 frame；`crossfade` 使用 explicit integer `duration_frames`，后一个 Shot 的 `start_frame = previous_end_frame - duration_frames`，并验证 overlap 小于两个相邻 Shot duration。
- composition fingerprint: 对 fully resolved timeline projection 做 stable JSON + SHA-256，排除 self hash、receipt timestamp、absolute staging path 和 wall-clock data。
- source receipt: renderer kind/version、timeline fingerprint、source SHA-256、exact asset bindings/hashes、lint/inspect command identity、exit status 和 output evidence hashes。
- render receipt: attempt ID、renderer/tool version、timeline fingerprint、source hash、asset hashes、output hash/size、measured width/height/FPS/duration/codec 和 result status。

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
- `src/ai_video/production/__init__.py`
- `src/ai_video/errors.py`
- `tests/test_production_models.py`
- `tests/production_project_factory.py`
- `.gitignore` only to add `node_modules/` and local HyperFrames scratch output
- `README.md`
- `docs/v0.2-runtime-baseline.md`
- `docs/v0.2-agentic-production-roadmap.md`
- `docs/agent-primary-contract-matrix.md`

Accepted P2A-owned files may be modified only if its approved contract explicitly requires adapter registration. Before changing them, record their exact paths/symbols and obtain state/schema/layout authorization if the P2A API does not already support generic staged artifacts and receipts. No P3 task may invent a fallback writer.

Do not modify:

- `src/ai_video/{cli,config,models,manifest,pipeline,workflow_loader,workflow_renderer,comfy_client}.py`
- `src/ai_video/ffmpeg_tools.py`
- `tests/test_{cli,config,manifest,pipeline,resume_e2e,workflow_loader,workflow_renderer}.py`
- `configs/**`、`workflows/**`、`runs/**`、`.workflow/**`

## Test and Commit Map

| Task | RED Focus | Owner | Commit |
| --- | --- | --- | --- |
| 0 | accepted P2A + pinned Renderer Gate | prerequisites/dependency lock | `build: pin hyperframes renderer tool` |
| 1 | strict composition/timeline/receipt schema | `models.py` | `feat: add composition and render contracts` |
| 2 | exact frame/sample resolution and fingerprint | `composition.py` | `feat: resolve deterministic production timelines` |
| 3 | timeline-only source materialization and audit | `hyperframes.py` source layer | `feat: materialize audited hyperframes sources` |
| 4 | fake lint/inspect/render and typed receipts | `HyperFramesAdapter` | `feat: add hyperframes renderer adapter` |
| 5 | accepted P2A commit integration and single-renderer gate | P2A adapter boundary | `feat: commit exclusive render attempts` |
| 6 | docs and verified runtime truth | docs | `docs: document p3 composition runtime` |
| 7 | live spike, regression and independent review | verification | no commit unless correction is required |

### Task 0: Pass P2A and Renderer Gates

**Files:**
- Verify: accepted P2A plan/source/tests/docs
- Create after dependency authorization: `package.json`
- Create after dependency authorization: `package-lock.json`
- Modify after dependency authorization: `.gitignore`

- [ ] **Step 1: Verify accepted P2A exists**

Run:

```bash
rg -n "P2A|State Commit|atomic|fsync|orphan|partial|pointer" \
  docs/superpowers/plans src/ai_video/production tests
test -f src/ai_video/production/state_commit.py
test -f tests/test_production_state_commit.py
test -f tests/test_production_state_recovery.py
python -m pytest \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
```

Expected: an approved P2A plan, implemented canonical committer and passing crash-injection suite exist at these expected canonical paths. Because they do not exist on 2026-08-09, this step currently ends execution with a blocker and no workspace change. If accepted P2A chooses different names or a different public API, revise and re-review this P3 plan before implementation; do not create aliases merely to satisfy these checks.

- [ ] **Step 2: Recheck official renderer facts**

Run read-only commands:

```bash
codex plugin list | rg '^hyperframes@'
command -v hyperframes || true
npm view hyperframes version engines license dist-tags repository --json
node --version
npm --version
ffmpeg -version | sed -n '1,3p'
```

Expected: evidence is recorded with date. If latest package, license, required Node version or CLI surface differs from `0.7.102`/Apache-2.0/Node `>=22`, stop and revise the pin and compatibility tests before installing anything.

- [ ] **Step 3: Obtain dependency-install authorization**

Stop and ask for explicit authorization covering all of:

- `package.json`/`package-lock.json` creation;
- exact `hyperframes@0.7.102` installation;
- local Chromium availability/install decision;
- live lint/inspect/preview/render spike;
- any P2A-owned Manifest schema or artifact layout change identified in Step 1.

Expected: without explicit authorization, no install command, `npx`, Chrome download, preview or render runs.

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
    "hyperframes": "0.7.102"
  }
}
```

Then run exactly:

```bash
npm install --save-exact hyperframes@0.7.102
./node_modules/.bin/hyperframes --version
npm ls hyperframes --depth=0
```

Expected: version is exactly `0.7.102`; `package-lock.json` contains one exact top-level pin. Do not use `npx hyperframes`, `@latest`, caret or range resolution in runtime commands.

- [ ] **Step 5: Ignore only local install/scratch output**

Append to `.gitignore`:

```gitignore
node_modules/
.hyperframes/
```

- [ ] **Step 6: Commit the dependency lock**

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
            renderer_version="0.7.102",
        )
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
    command: Literal["lint", "inspect"]
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

Receipt timestamps are intentionally absent from semantic fingerprints. If P2A adds lifecycle timestamps, they remain Manifest/receipt-envelope metadata and are excluded from `composition_fingerprint`.

- [ ] **Step 5: Export only stable P3 contracts**

Export `CompositionSpec`, `ResolvedTimeline`, `RendererSelectionReceipt`, `RendererSourceReceipt` and `RenderReceipt` from `production/__init__.py`. Do not export a runtime command or writer.

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
    timeline = resolve_composition(loaded, spec, renderer_version="0.7.102")
    assert [span.shot_id for span in timeline.visual_spans] == ["shot-2", "shot-1"]


def test_fixed_seconds_round_up_once_at_shot_boundary(tmp_path):
    loaded = write_and_load_two_shot_project(tmp_path, seconds=(1.001, 2.0), fps=24)
    timeline = resolve_composition(loaded, make_composition_spec(), "0.7.102")
    assert [(span.start_frame, span.duration_frames) for span in timeline.visual_spans] == [
        (0, 25),
        (25, 48),
    ]


def test_crossfade_uses_integer_overlap_and_sample_boundaries(tmp_path):
    timeline = resolve_composition(
        write_and_load_two_shot_project(tmp_path, seconds=(2.0, 2.0), fps=24),
        make_composition_spec(crossfade_frames=12, sample_rate=48_000),
        "0.7.102",
    )
    assert timeline.visual_spans[1].start_frame == 36
    assert timeline.visual_spans[1].start_sample == 72_000
    assert timeline.total_frames == 84
    assert timeline.total_samples == 168_000


def test_same_resolved_inputs_have_same_fingerprint_after_mtime_change(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    first = resolve_composition(loaded, spec, "0.7.102")
    os.utime(loaded.asset_paths[spec.layers[0].asset_id], (1_900_000_000, 1_900_000_000))
    second = resolve_composition(loaded, spec, "0.7.102")
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

- `staging_root` is supplied by P2A; this function never chooses active layout or switches a pointer.
- Copy each timeline asset to `assets/<asset_id>-<first12sha><suffix>` after verifying the source bytes still match registry SHA-256; no symlink and no directory scan.
- Generate `index.html` in exact `timeline.visual_spans` order. Convert frame boundaries to decimal seconds only at source materialization with `Decimal(frame) / Decimal(fps)` and a stable string formatter.
- Embed timeline fingerprint, renderer version, asset ID/hash, trim, fixed transform, opacity, z-order and transition as explicit local data attributes/JSON.
- Use only local HTML/CSS/HyperFrames runtime features proven by the live spike. Do not reference CDN GSAP, Google Fonts, remote media, `.env`, current time or randomness.
- Write source once into P2A staging, hash it, run `audit_hyperframes_source()`, and return the result. No source rewrite is allowed after hashing.

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
        version="0.7.102",
        results={"lint": clean_lint_json(), "inspect": clean_inspect_json(), "render": ""},
    )
    result = HyperFramesAdapter(runner=runner, expected_version="0.7.102").render(
        attempt=make_render_attempt(tmp_path),
    )
    assert [call.command for call in runner.calls] == ["lint", "inspect", "render"]
    assert {call.env["HYPERFRAMES_NO_UPDATE_CHECK"] for call in runner.calls} == {"1"}
    assert result.render.renderer.kind is RendererKind.HYPERFRAMES


def test_adapter_rejects_remotion_without_fallback(tmp_path):
    runner = FakeRunner()
    with pytest.raises(AiVideoError) as exc:
        HyperFramesAdapter(runner, "0.7.102").render(
            attempt=make_render_attempt(tmp_path, renderer_kind="remotion")
        )
    assert exc.value.code is ErrorCode.RENDERER_UNAVAILABLE
    assert runner.calls == []


@pytest.mark.parametrize("failed_phase", ["lint", "inspect", "render"])
def test_adapter_persists_typed_phase_failure_without_next_command(tmp_path, failed_phase):
    runner = FakeRunner(fail_at=failed_phase)
    committer = FakeP2ACommitter()
    with pytest.raises(AiVideoError):
        execute_hyperframes_attempt(make_render_attempt(tmp_path), runner, committer)
    assert committer.failed_phase == failed_phase
    assert all(call.command != "render" for call in runner.calls) if failed_phase != "render" else True
    assert committer.active_pointer_switches == 0
```

Also cover wrong tool version, malformed JSON, lint errors, inspect errors, warnings policy, missing/empty output, output hash mismatch, measured width/height/FPS/duration mismatch, timeout, stderr truncation/redaction, no source mutation after lint, and only one selected renderer.

- [ ] **Step 2: Run adapter RED**

```bash
python -m pytest tests/test_production_hyperframes.py -q -k 'adapter or receipt or failure'
```

Expected: tests fail because runner/adapter/receipt construction is not implemented.

- [ ] **Step 3: Implement the injected executable boundary**

```python
@dataclass
class RendererAttemptError(AiVideoError):
    phase: Literal["source", "lint", "inspect", "render", "verify"] = "render"


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

The production runner must call only the approved local binary path `node_modules/.bin/hyperframes`, pass argv as a list without `shell=True`, enforce timeout, capture bounded stdout/stderr, redact secrets and never invoke `npx`, `upgrade`, `browser`, `cloud`, `lambda`, `tts` or `transcribe`.

- [ ] **Step 4: Implement strict phase parsing and receipts**

`HyperFramesAdapter.render()` must run exactly:

```text
node_modules/.bin/hyperframes lint "$STAGING_ROOT" --json
node_modules/.bin/hyperframes inspect "$STAGING_ROOT" --json
node_modules/.bin/hyperframes render "$STAGING_ROOT" -o "$P2A_STAGED_OUTPUT_PATH"
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
        command: Literal["lint", "inspect"],
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
            error_count = int(payload["errorCount"])
            warning_count = int(payload["warningCount"])
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
        inspect_receipt = self._check("inspect", materialized.root)
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
                checks=(lint_receipt, inspect_receipt),
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
            if phase in {"lint", "inspect"}
            else ErrorCode.RENDER_FAILED
        ),
        user_message=f"HyperFrames {phase} failed.",
        technical_detail=_redact(result.stderr or result.stdout),
        retryable=False,
        phase=cast(Literal["lint", "inspect", "render"], phase),
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

The method must verify tool version before phase 1, parse the pinned JSON schema, require zero errors, record warning counts, rehash source/assets between phases, validate output with `probe_clip()`, calculate output/decoded-frame hashes and build sealed source/render receipts. It must never include timestamps in timeline/source/decoded-frame fingerprints.

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

### Task 5: Integrate with the Accepted P2A Committer

**Files:**
- Modify: accepted P2A adapter-registration file only if its approved public API requires it
- Modify: `src/ai_video/production/hyperframes.py`
- Test: accepted P2A integration test file
- Test: `tests/test_production_hyperframes.py`

- [ ] **Step 1: Record the actual P2A symbols**

Run:

```bash
rg -n "class .*Commit|def .*commit|stage|pointer|failed_attempt|render" \
  src/ai_video/production tests
```

Expected: identify one accepted canonical committer and its focused tests. If there are multiple state writers or no generic artifact/receipt transaction, stop; do not add a P3 writer.

- [ ] **Step 2: Add a consumer protocol without owning persistence**

The HyperFrames module may depend on this structural protocol:

```python
class RenderAttemptCommitter(Protocol):
    def staging_root(self, attempt_id: str) -> Path:
        pass

    def staged_output_path(self, attempt_id: str) -> Path:
        pass

    def commit_renderer_selection(self, selection: RendererSelectionReceipt) -> None:
        pass

    def commit_failed_attempt(
        self, selection: RendererSelectionReceipt, phase: str, error: AiVideoError
    ) -> None:
        pass

    def commit_succeeded_attempt(
        self,
        selection: RendererSelectionReceipt,
        timeline: ResolvedTimeline,
        source: RendererSourceReceipt,
        render: RenderReceipt,
    ) -> None:
        pass
```

This protocol contains no file-writing implementation. The accepted P2A committer must satisfy it directly or through a thin adapter in its own canonical module.

Use this single coordinator; it delegates every state mutation to P2A:

```python
def execute_hyperframes_attempt(
    attempt: HyperFramesRenderAttempt,
    runner: RendererRunner,
    committer: RenderAttemptCommitter,
    *,
    expected_version: str = "0.7.102",
) -> HyperFramesRenderResult:
    if attempt.selection.selected_kinds != (RendererKind.HYPERFRAMES,):
        raise _renderer_unavailable("Render attempt must select exactly hyperframes.")
    if attempt.staging_root != committer.staging_root(attempt.attempt_id):
        raise _render_failed("Attempt staging root is not owned by P2A.")
    if attempt.output_path != committer.staged_output_path(attempt.attempt_id):
        raise _render_failed("Attempt output path is not owned by P2A.")
    committer.commit_renderer_selection(attempt.selection)
    try:
        result = HyperFramesAdapter(runner, expected_version).render(attempt)
    except RendererAttemptError as exc:
        committer.commit_failed_attempt(attempt.selection, exc.phase, exc)
        raise
    committer.commit_succeeded_attempt(
        attempt.selection,
        attempt.timeline,
        result.source,
        result.render,
    )
    return result
```

Every adapter/source/check/render verification failure must be normalized to `RendererAttemptError` with one explicit phase before crossing this coordinator. Generic `AiVideoError` must not escape without a phase, and the coordinator must not infer phase by parsing a message string.

- [ ] **Step 3: Prove commit ordering with failure injection**

Integration tests must assert:

1. renderer selection is one-element and persisted before executable work;
2. lint/inspect/render operate only in the P2A staging root;
3. lint/inspect/render failure commits a failed attempt and never switches active render pointer;
4. output/source/assets are rehashed before success commit;
5. success performs one P2A atomic commit after all receipts are complete;
6. simulated crash before commit leaves active state unchanged and restart follows P2A orphan/partial rules;
7. `remotion` selection yields typed failure with zero HyperFrames and zero alternate renderer invocations.

- [ ] **Step 4: Run P2A and P3 GREEN**

```bash
python -m pytest \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_models.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py -q
```

Expected: all pass; no test writes Legacy Manifest v1 or `runs/**`. If accepted P2A does not use these expected canonical test paths, revise and re-review this plan before execution.

- [ ] **Step 5: Commit only the integration surface**

```bash
git add src/ai_video/production/hyperframes.py \
  src/ai_video/production/state_commit.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py
git commit -m "feat: commit exclusive render attempts"
```

Expected: the explicit paths recorded in Step 1 are staged; no broad `git add` is used. If satisfying the protocol requires Manifest schema/layout changes not already authorized, stop before editing.

### Task 6: Synchronize Verified Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/v0.2-runtime-baseline.md`
- Modify: `docs/v0.2-agentic-production-roadmap.md`
- Modify: `docs/agent-primary-contract-matrix.md`

- [ ] **Step 1: Document only verified P3 behavior**

After focused, live spike and regression gates pass, document:

- importable `CompositionSpec`/`resolve_composition()`/HyperFrames adapter API;
- accepted strategies in this slice and explicit blocked strategies;
- `ResolvedTimeline` as only order/timing truth;
- exact pinned tool version and one-renderer-per-attempt rule;
- source hash/lint/inspect and render receipt fields;
- fake/no-network CI versus separately authorized live spike;
- P4/P5/P6/P7/P8 remain unimplemented.

Do not claim byte-identical MP4, cloud readiness, Audio/Caption support, selective rebuild, new CLI or Legacy migration.

- [ ] **Step 2: Add focused contract validation**

Add to the contract matrix:

```bash
python -m pytest \
  tests/test_production_models.py \
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

Expected: P3 text describes only tested local behavior; every future capability remains planned/not implemented.

### Task 7: Run Live Spike, Regressions and Independent Review

**Files:**
- Verify: all P3/P2A-owned files
- Verify unchanged: Legacy runtime, public CLI, Manifest v1 and flat layout

- [ ] **Step 1: Stop for explicit live-spike authorization**

Even after dependency installation is approved, do not run real HyperFrames commands until the user explicitly authorizes the live spike. The spike may start local Chrome/server processes and create temporary render output; it must use a disposable P2A staging attempt and no user asset.

- [ ] **Step 2: Run the pinned no-network renderer spike**

With authorization, set:

```bash
export CI=1
export HYPERFRAMES_NO_TELEMETRY=1
export DO_NOT_TRACK=1
export HYPERFRAMES_NO_UPDATE_CHECK=1
export HYPERFRAMES_NO_AUTO_INSTALL=1
```

Run the exact pinned binary against the committed silent-image fixture copied into a disposable staging directory:

```bash
P3_SPIKE_DIR=$(mktemp -d)
cp -R tests/fixtures/hyperframes/silent_image/. "$P3_SPIKE_DIR/"
./node_modules/.bin/hyperframes --version
./node_modules/.bin/hyperframes doctor
./node_modules/.bin/hyperframes lint "$P3_SPIKE_DIR" --json
./node_modules/.bin/hyperframes inspect "$P3_SPIKE_DIR" --json
./node_modules/.bin/hyperframes preview "$P3_SPIKE_DIR" --port 3017 \
  >"$P3_SPIKE_DIR/preview.log" 2>&1 &
P3_PREVIEW_PID=$!
curl --fail --silent --show-error http://127.0.0.1:3017/ >/dev/null
kill "$P3_PREVIEW_PID"
wait "$P3_PREVIEW_PID" || true
./node_modules/.bin/hyperframes render "$P3_SPIKE_DIR" \
  -o "$P3_SPIKE_DIR/render.mp4"
```

Expected:

- exact version `0.7.102`;
- doctor reports usable Node/FFmpeg/Chromium;
- lint/inspect return machine-readable zero-error evidence;
- preview serves the fixture locally and is stopped cleanly after one manual/browser smoke;
- render creates a non-empty local MP4 with measured width/height/FPS/frame duration matching `ResolvedTimeline`;
- source/asset hashes do not change;
- no update/install/cloud/telemetry process is launched;
- repeated render is frame-equivalent by sampled frame hashes or decoded-frame comparison, while MP4 byte hashes may differ.

If `inspect` incompatibility, Chrome download need, remote fetch, telemetry/update attempt, timing mismatch, source mutation or non-equivalent decoded frames appears, stop P3 implementation and return to Renderer Gate. Do not weaken the contract or substitute Remotion.

- [ ] **Step 3: Run focused P3 tests**

```bash
python -m pytest \
  tests/test_production_models.py \
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

- [ ] **Step 7: Obtain independent review**

Review brief:

```text
Verdict must be accept, accept with concerns, or reject.
Verify P3 started from accepted P2A and did not add a second writer/Manifest.
Verify CompositionSpec is edit intent and ResolvedTimeline is the only order/timing owner.
Verify integer frame/sample boundaries, exact asset IDs/hashes, trim, transform,
opacity, z-order, transitions, delivery profile, renderer identity and fingerprint.
Verify HyperFrames source comes only from timeline/assets and is hash/lint/inspect audited.
Verify one attempt selects exactly one renderer and no Remotion/fallback/double render exists.
Verify fake/no-network defaults, typed phase failures, atomic commit ordering and rollback.
Verify frame-equivalent evidence is not misreported as byte-identical output.
Verify Legacy CLI/Manifest/layout and P4/P5/P2A/Provider boundaries remain unchanged.
```

Required exit verdict: `accept` or `accept with concerns` with no blocking issue. The parent must inspect important claims, final diff and commands directly.

- [ ] **Step 8: Record final branch truth**

```bash
git status --short --branch
git log --oneline --decorate -15
git rev-list --left-right --count origin/main...HEAD
```

Expected: clean task branch/worktree and explicit local-vs-origin state. Do not claim push, merge or release without evidence.

## Failure and Rollback

Failure handling:

- schema/resolution/source audit failure: no external command and no state commit;
- lint failure: persist typed failed attempt through P2A, do not inspect/render;
- inspect failure: persist typed failed attempt, do not render;
- render/timeout/output validation failure: persist typed failed attempt, leave active pointer unchanged;
- crash before success commit: P2A recovery owns partial/orphan cleanup and active pointer remains old;
- crash after P2A commit: resume reads the committed timeline/source/render receipts and hashes, not console or Agent memory;
- renderer mismatch/unavailable: fail explicitly; no HyperFrames-to-Remotion or Remotion-to-HyperFrames retry.

Rollback is commit-based and must preserve user project artifacts:

```bash
git revert "$(git log -1 --format=%H --grep='^docs: document p3 composition runtime$')"
git revert "$(git log -1 --format=%H --grep='^feat: commit exclusive render attempts$')"
git revert "$(git log -1 --format=%H --grep='^feat: add hyperframes renderer adapter$')"
git revert "$(git log -1 --format=%H --grep='^feat: materialize audited hyperframes sources$')"
git revert "$(git log -1 --format=%H --grep='^feat: resolve deterministic production timelines$')"
git revert "$(git log -1 --format=%H --grep='^feat: add composition and render contracts$')"
git revert "$(git log -1 --format=%H --grep='^build: pin hyperframes renderer tool$')"
```

Do not delete `projects/**`, accepted P2A snapshots, receipts or user renders during rollback. A separate explicit P2A GC policy decides when orphaned immutable artifacts may be reclaimed.

## Acceptance Criteria

P3 is accepted only when:

1. accepted P2A exists and owns every durable write/pointer switch;
2. `CompositionSpec` captures explicit edit intent without filesystem discovery;
3. `ResolvedTimeline` is the only order/timing/layer truth and contains integer frame/sample boundaries;
4. asset ID/hash, trim, transform, opacity, z-order, transition, delivery profile, renderer kind/version and deterministic composition fingerprint are persisted in the contract;
5. identical resolved inputs produce identical timeline/source hashes and frame-equivalent output under the pinned tool/runtime;
6. no byte-identical MP4 claim is made without a separately proven encoder/container contract;
7. source is materialized only from timeline/registered assets, then hashed, linted and inspected;
8. source contains no wall-clock randomness, implicit network fetch, remote URL or untracked asset;
9. each attempt has one renderer selection and one HyperFrames execution path;
10. Remotion is neither installed nor implemented and no double-render/fallback exists;
11. source/render receipts include exact tool/timeline/source/asset/output evidence;
12. default tests are fake/no-network and the real spike ran only after explicit authorization;
13. lint/inspect/render failures are typed, crash-safe through P2A and leave active state unchanged;
14. no Audio/Caption, P5 graph, P2A implementation, Provider/cloud/paid API, new CLI or Legacy migration enters the diff;
15. focused P3/P2A, Legacy regression and full default suites pass;
16. docs describe only verified behavior and independent review has no blocker.

## Plan-Time Known Blockers

- **Plan drafting:** none.
- **P3 runtime execution:** blocked by accepted P2A, Renderer Gate and dependency-install authorization.
- **Potential additional gate:** accepted P2A may require separately authorized Production Manifest schema or v2 artifact layout extension for timeline/source/render receipts.
- **Known document drift:** roadmap/contract matrix still contain P2 integration-pending wording even though local `main` at `a5be154` contains accepted P2. This plan records Git/test truth but does not modify those unrelated stale lines during docs-only planning.

## Execution Authorization Boundary

This plan may be reviewed and accepted now, but it must not be executed in whole or in part until the user explicitly authorizes P3 runtime work after P2A acceptance and separately authorizes the Renderer Gate dependency/tool installation and live spike. Creating this document and its planning commit grants no authority to install HyperFrames, download Chromium, modify `src/**` or tests, change Manifest/schema/layout, start preview, or render media.
