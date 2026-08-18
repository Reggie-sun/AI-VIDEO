# AI-VIDEO

Local-first Python CLI for orchestrating long-video generation through default-local ComfyUI. Non-local ComfyUI requires explicit opt-in.

The MVP reads a project config and shot list, renders ComfyUI workflow JSON per shot, submits each shot locally, extracts the last frame, passes that frame into the next shot, and stitches normalized clips with ffmpeg.

## Roadmap Status

公共 CLI 仍是本 README 描述的 local-first `0.1.x` surface。P2 是可导入、只读的 Python API，用于 strict Production Project 与 content-addressed local assets；P2A 拥有 v2 state commit 和 explicit recovery。P3-P7 与 combined Base AI Comic E2E 已合入 local `main`。P7.1 offline/runtime-contract implementation 增加 sealed loopback-only ComfyUI image adapter 与 truthful human web-image import；首次授权 live smoke 已 fail closed，尚未通过 live 或 blind quality acceptance。

- Current runtime evidence: [`docs/v0.2-runtime-baseline.md`](docs/v0.2-runtime-baseline.md)
- New target contract: [`docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md`](docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md)
- Phase dependency map: [`docs/v0.2-agentic-production-roadmap.md`](docs/v0.2-agentic-production-roadmap.md)
- Product reframe plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p0-product-reframe.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p0-product-reframe.md)
- Accepted P2 core plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2-production-project-core.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2-production-project-core.md)
- Accepted P2A state commit plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2a-production-state-commit-protocol.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2a-production-state-commit-protocol.md)
- Verified P3 composition plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p3-deterministic-composition-hyperframes-adapter.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p3-deterministic-composition-hyperframes-adapter.md)
- Accepted P4 voice/caption plan: [`docs/superpowers/plans/2026-08-10-ai-video-agentic-production-harness-p4-voice-and-captions.md`](docs/superpowers/plans/2026-08-10-ai-video-agentic-production-harness-p4-voice-and-captions.md)
- P5 dependency/selective-rebuild plan: [`docs/superpowers/plans/2026-08-11-ai-video-agentic-production-harness-p5-dependency-graph-selective-rebuild.md`](docs/superpowers/plans/2026-08-11-ai-video-agentic-production-harness-p5-dependency-graph-selective-rebuild.md)
- Accepted P6 review/repair plan: [`docs/superpowers/plans/2026-08-17-ai-video-agentic-production-harness-p6-codex-review-repair-harness.md`](docs/superpowers/plans/2026-08-17-ai-video-agentic-production-harness-p6-codex-review-repair-harness.md)
- Accepted P7 image-asset plan: [`docs/superpowers/plans/2026-08-17-ai-video-agentic-production-harness-p7-image-asset-generation.md`](docs/superpowers/plans/2026-08-17-ai-video-agentic-production-harness-p7-image-asset-generation.md)
- Accepted Base AI Comic E2E plan: [`docs/superpowers/plans/2026-08-18-ai-video-base-ai-comic-e2e.md`](docs/superpowers/plans/2026-08-18-ai-video-base-ai-comic-e2e.md)
- Historical superseded spec: [`docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md`](docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md)
- Implemented local Legacy stabilization record: [`docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md`](docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md)

公共命令仍是 `validate`、`run` 和 `resume`；Legacy generation 继续只使用 default-local ComfyUI，Manifest v1 与 flat Legacy artifact layout 仍有效。P5 已 push 到 `origin/main`；P6-P7 与 Base E2E 已通过 `abc69c39b9d3d5f9ba317ecb65bbf26f1070d7d8` 合入 local `main`，但 local `main` 尚未 push、release 或 publish。P7.1 不修改 CLI、schema 或 Legacy layout；M7 只产生一次 loopback Qwen submit，未下载模型、未调用 remote service，也未运行 blind benchmark。

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Requirements:

- Python 3.11+
- Local ComfyUI already running
- `ffmpeg` and `ffprobe` on PATH

## Architecture Gate

Repository architecture regression 使用独立、local、no-network gate 验证，不改变 `ai-video` 的三个公共命令：

```bash
python -m scripts.architecture_gate check
```

默认比较 version-controlled baseline；在 branch/CI 上可用 `--base-ref <git-ref>` 直接比较 Git base。只有经 review 的显式操作才可更新 deterministic baseline：

```bash
python -m scripts.architecture_gate update-baseline
```

Historical oversized modules 与 existing import cycles 可 grandfather；超过 blocking threshold 的 oversized module growth、new blocking-sized module 和 new first-party dependency cycle 会阻止通过。`801–1500` LOC 的 growth/new module 为 warning，new high fan-out 仅作为 reviewer information。

## Development Verification Harness

仓库开发 Harness 是对现有 tests/checks 的轻量 mandatory runner，不是新的 Agent workflow，也不属于产品 runtime。Policy 位于 `.agent/harness/policy.yaml`，入口是 `scripts/agent_harness.py`，每次 verification 的本地 receipt 写入 `.agent/harness/runs/<run_id>/receipt.json`；run artifacts 默认不进入 Git。

```bash
# 查看当前 changes 必须执行的 checks
make harness-inspect

# 执行 checks 并生成 passing/failed receipt
make harness-verify

# 只验证 Harness 自身
make harness-test
```

工作区存在 unrelated changes 时，可通过 `HARNESS_ARGS` 限定本任务文件，或在只 stage 本任务文件后验证：

```bash
make harness-verify HARNESS_ARGS="--path src/ai_video/cli.py --path tests/test_cli.py"
make harness-verify HARNESS_ARGS="--staged"
```

Harness 按 changed-path category 合并 required checks；任何未映射路径都会 fail safe 到完整 no-network pytest suite 与 Architecture Gate。P6 Review/Repair 是产品 runtime QA surface，与这个开发 Harness 不同。

## Production Project Core Python API

P2 exposes a Python loading API for an explicitly materialized v2 project:

```python
from ai_video.production import load_production_project

project = load_production_project("projects/example/project.yaml")
```

上面的路径仅为示意；仓库不包含该 example project。Loader 保持 read-only 和 no-network。它以 `project.yaml` 为 stable validated entrypoint，然后验证 Production Manifest 选中的 project/registry snapshot path、semantic identity 和 exact file hash；也验证 sealed creative artifact reference、六种 Shot `visual_strategy` contract、concrete asset ID/type、local file size/SHA-256 与 project-root containment。对 Manifest 2.1/2.2，它还会验证选中的 P3/P4 timeline、audio/caption provenance、source/receipt/output 与 render-state graph；对 Manifest 2.3，它还验证 active immutable Dependency Graph snapshot 与 Manifest-owned dependency states；对 Manifest 2.4，它还会 reopen 并验证 active QA policy、review/repair/outcome/final-acceptance receipts 及其 exact evidence bindings；对 Manifest 2.5，它还会 reopen exact P7 request、submit intent、provider result、measured PNG 和 provenance evidence，但不会 scan、generate、recover、repair 或 rewrite。P2A state 存在后，root `project.yaml` 不是 active snapshot bytes truth。

P2 本身不创建目录、不更新 Manifest，也不激活 registry 或 graph revision。P2A `ProductionStateCommitter` 继续拥有全部 v2 state changes，并与 reader 保持分离；P6/P7/P7.1 只在该唯一 writer/control path 上增加 durable QA/repair、image lifecycle 与 human-import evidence。Manifest 2.5 可在不改变 schema 的情况下组合保留既有 voice/render/review/repair owners 和全部 P7 evidence。当前仍没有 v2 CLI、production coordinator、Remotion/Captions.ai final-render adapter、Video Provider、remote image Provider 或 cloud fallback。

## Production State Commit Protocol (P2A)

P2A is an importable Python API, not a CLI surface. `ProductionManifest` is the sole lifecycle record; its `active_project` and `active_registry` pointers record exact relative paths, semantic revision/content hashes and file SHA-256 hashes. `ProductionStateCommitter` in `ai_video.production.state_commit` is the sole v2 writer and recovery owner.

On POSIX, a commit uses a same-filesystem `state/commit.lock`, writes and file-fsyncs immutable snapshot temps, promotes them without overwrite, parent-directory-fsyncs, then reopens and verifies them. Durable `ProductionManifest` writes also record running and failed attempt lifecycle; the one atomic replacement that switches active pointers is the single logical commit point. Recovery is explicit through `recover_production_state()`; normal P2 loading never silently repairs state. It accepts only an exact old pair or exact new pair, marks interrupted attempts without guessing activation, cleans only bounded non-succeeded owned temporary files, and preserves/reports complete orphan snapshots rather than activating or deleting them. These guarantees are deliberately narrower than byte-identical, all-platform, zero-data-loss or power-loss-safe claims.

The P2A implementation file map is `src/ai_video/production/models.py`, `src/ai_video/production/project.py`, `src/ai_video/production/state_commit.py`, `src/ai_video/production/__init__.py`, `tests/production_project_factory.py`, `tests/test_production_models.py`, `tests/test_production_project.py`, `tests/test_production_validation.py`, `tests/test_production_state_commit.py`, `tests/test_production_state_recovery.py`, and `tests/helpers/p2a_crash_worker.py`.

## Deterministic Composition and HyperFrames (P3)

P3 exposes importable `CompositionSpec`, `ResolvedTimeline`, `resolve_composition()`, lifecycle request/path models and durable `render_with_hyperframes()`. `ResolvedTimeline` is the only ordering and timing truth. The accepted surface is deliberately narrow: local PNG/JPEG/WebP `STATIC_IMAGE` spans, deterministic transforms/z-order/opacity, and zero-duration `CUT` transitions. Crossfade, motion directives, other visual strategies and Remotion selection fail closed.

The renderer is exactly project-pinned `hyperframes@0.7.103` with the verified Chrome Headless Shell `152.0.7928.2`. Every non-version command uses root `--json` inside a fresh user/network/PID namespace with a controlled environment and no host fallback. Generated HTML uses root boolean `data-no-timeline`, exact frame/sample metadata and capture-safe CSS opacity keyframes; URL, raster and source-bundle audits run before activation.

`ProductionStateCommitter` remains the sole writer. It durably records selection before any executable call, owns source/output receipts and the canonical immutable `state/render/**` layout, and switches the single `active_render_state` pointer only after held-FD output verification. Manifest 2.0 remains readable; the first render lifecycle write migrates to 2.1. Manifest 2.0-2.2 keeps the historical pair-change render-pointer behavior；Manifest 2.3 instead preserves immutable historical render evidence and uses P5 dependency states for precise freshness. Recovery compares exact selected identities and preserves complete orphans.

默认 P3 tests 使用 fake runner 且不联网。Explicit committed-fixture proof 将同一个 two-image `10`-frame `24fps` CUT timeline 渲染两次，验证 frame 4 为红色、frame 5 为蓝色、无 audio、decoded-frame fingerprint 相同、command lineage 精确且 network trace fail closed。这是 frame-equivalence evidence，不保证 MP4 byte-identical。P3 本身不增加 selective rebuild、新 CLI 或 cloud behavior；P4 扩展同一个 renderer contract，而不是增加另一个 renderer。

## Voice and Captions (P4)

P4 将 `dialogue`、`narration`、`ambience`、`sfx` 和 `bgm` 建模为 first-class audio kinds。Local import 与 immutable `VoiceGenerationRequest` flow 绑定 source、speaker/voice、language、script hash、duration、sample rate、channels、loudness、timing、gain/fade/ducking 和 provenance。Provider-neutral `VoiceAssetProvider` contract 要求先完成 deterministic budget/egress preview 与 authorization，P2A 才写 R+1 request 和 R+2 submit intent；只有 committer-issued one-use permit 能跨越 transport boundary。Materialized audio 经 probe、hash，并随 alignment、cost、policy/retention 与 provenance evidence 注册后，才进入 R+3 candidate preparation 与 R+4 activation。

`CaptionTrack` 是 script/transcript identity、segments、optional words、half-open timing、speaker、segmentation policy、confidence/provider、style reference 与 timing fingerprint 的 canonical structured source，不会变成 burned-in pixel state。P4 用 audio spans 和 caption cues 扩展 `CompositionSpec` 与既有 `ResolvedTimeline`；该 timeline 继续是唯一 order/frame/sample/timing owner。Selected HyperFrames renderer 拥有 caption layout/drawing 和 deterministic audio mixing/muxing。

`ProductionStateCommitter` 仍是唯一 v2 writer 和 recovery owner。成功的 P4 lifecycle write 使用 Manifest 2.2 与 Registry 2.1，Composition/ResolvedTimeline 则保持 forward-compatible 2.1 extensions。R+1/R+2/R+3/R+4 crash windows、`outcome_unknown`、explicit recovery 与 idempotent replay 都 fail closed：replay 不再次调用 provider 或 renderer，也不存在 schema downgrade 或 automatic recovery。Rollback 是 operational strategy：关闭或移除新的 P4 entrypoints 与 opt-in adapter，同时保留 Manifest 2.2 及对应 reader/recovery compatibility；当前没有独立的 runtime rollback API。

默认 acceptance 使用 deterministic local fixtures、fake providers/transports 且不联网。`ai_video.production.elevenlabs` 是 thin explicit-opt-in candidate，并且有意不从 package root 导出。P4 acceptance 未进行 ElevenLabs live call、secret 读取、SDK installation，也未使用免费或付费 quota。Live call 即使使用免费额度，也需要单独授权，并重新通过 budget、egress、secret-redaction 与 crash-safe persistence gates。P4 暴露的 composition、timeline、audio、alignment、caption 与 renderer fingerprints 现在由 P5 typed graph 输入消费；P4 modules 本身仍不拥有 dependency lifecycle。

## Dependency Graph and Selective Rebuild (P5)

P5 在 `ai_video.production.dependency` 中把 P2/P3/P4 的 immutable inputs 映射成 content-addressed `DependencyGraphSnapshot` 2.0。Graph 只保存 typed nodes、typed edges、`DependencyReason` 和 fingerprint contributions；它不保存 desired/applied、fresh/stale/failed/blocked/superseded 或任何 mutable status，也不推导 frame/sample/order/timing。`ResolvedTimeline` 仍是唯一 canonical timeline owner。

Manifest 2.3 是 `active_dependency_graph`、per-node desired/applied fingerprints 和 lifecycle 的唯一 owner。Resolver 用 canonical upstream desired fingerprints 做 precise transitive invalidation，保留无关 fresh nodes；same desired failure 不会 auto-retry，changed desired 才重新进入 stale frontier。Composition、ResolvedTimeline、renderer source 与 render 组成一个 `render_with_hyperframes` durable execution unit，只有 final `RenderStateSnapshot` activation 才能在同一个 Manifest replace 中一起 fresh。`ProductionStateCommitter` 继续是 graph snapshot write、project/registry/render/graph co-activation、single final Manifest replace 与 explicit recovery 的唯一 control path；不存在第二 Manifest、registry writer、graph writer 或 automatic recovery。

Graph snapshot 使用 canonical `state/dependency_graph.<revision>.json`。Reader/recovery 保持 Manifest 2.0-2.2 compatibility；2.3 的 graph temp、promotion、verification、final Manifest replace、unknown outcome、orphan preservation 与 idempotent recovery 均 fail closed，rollback 只能停用新的 mutation/rebuild entrypoints并保留 2.3 reader/recovery，不能 schema downgrade。默认 P5 acceptance 使用 two-Shot deterministic P4 fixtures、fake/no-network render/voice evidence；required mutation matrix 已证明 script、voice settings、alignment policy/receipt、caption timing/style、audio mix、visual asset、CompositionSpec、renderer source/render contract 只影响精确节点。最终验证为 canonical `1256 passed, 3 skipped`、Legacy `58 passed`、full `1386 passed, 4 skipped`。

P5 slice 本身没有实现 QA/repair、Provider/cloud 或 hardening；P6 在不修改 graph ownership 的前提下增加下述 review/repair lifecycle。Legacy CLI、Manifest v1、flat `runs/` layout、ComfyUI path 和现有公共 CLI 保持不变。

## Codex Review and Repair Runtime (P6)

P6 通过 `ai_video.production.review`、Manifest 2.4 和既有 `ProductionStateCommitter` 提供 strategy-aware QA。`video-analysis` MCP 只收集 technical raw measurements；它不拥有 Production Manifest、review/repair lifecycle 或 final acceptance。Technical review context 只能从已验证的 `LoadedProductionProject`、`ResolvedTimeline`、exact render/output hash 和 Shot `visual_strategy` 构建。合法 `static_image`、`image_motion` 与 `motion_graphics` 按各自策略预期判定，不再被统一的 video-like diversity heuristic 误判。

Manifest 2.4 是 selected QA policy、review lifecycle、approved repair/outcome 与 final acceptance 的唯一 mutable owner。Review/Repair/Outcome/Final Acceptance receipts 均为 immutable、content-addressed、versioned evidence，绑定当前 dependency graph revision、timeline fingerprint、render/output identity、QA policy/version、evidence/tool/actor identity 与 before/after fingerprints。`technical`、`layout`、`strategy`、`semantic`、`final_acceptance` 五层全部 fail closed；semantic 只接受 policy-selected explicit evaluator 或 human durable evidence。Final acceptance 必须 reopen 当前 desired graph、`ResolvedTimeline`、render hash 和 fresh required review receipts。

Repair 默认未授权，只有 injected trusted authorizer 返回 QA policy 允许的 `ActorIdentity` 后才能记录 approved receipt 并进入执行。它必须绑定 issue/evidence IDs、root-cause hypothesis、exact target artifacts 与 P5 resolver 得出的 exact invalidation closure；禁止 blanket stale。QA policy-only change 只使 affected review/final acceptance stale，不重建 assets/render；只有 approved Repair Receipt 才能触发 selective rebuild。Exact replay 不重复analysis、repair 或 render，crash/unknown outcome 后不 blind reapply，恢复仍由 `ProductionStateCommitter` 单一拥有。

P6 默认 acceptance 仅使用 deterministic fixtures 与 fake/no-network evidence。Focused result 为 `739 passed`，independent review verdict 为 `accept with concerns` 且无 blocking issue；保留的非阻塞风险是未来补一条不使用 monkeypatch 的 activated render/timeline snapshot reopen E2E。P6 未运行 ComfyUI、HyperFrames executable、Provider、付费 API、secret 或 quota，也不授权 P8-P9 scope；P7 是后续单独获批并验收的独立 slice。

## Image Asset Generation (P7)

P7 在 `ai_video.production.image` 定义 provider-neutral、local-only 的 immutable image request/preview/authorization/result/provenance contract 和 `ImageAssetProvider` protocol。`ImageGenerationRequest` 显式绑定 target Shot/role、prompt/seed/dimensions、exact Character/Scene/reference identities 以及 base project/registry/graph；repository 没有打包 concrete/live Provider。默认 acceptance 只注入 deterministic fake provider 并验证 PNG bytes、MIME、dimensions、SHA-256、license 和 local/no-egress provenance。

Manifest 2.5 组合 P6 review/repair 与 P7 image lifecycle，但不让两者互为 runtime prerequisite。`ProductionStateCommitter` 仍是 request、submit intent、one-use permit、provider result、PNG/provenance、candidate project/Registry/graph、single final Manifest replace 与 explicit recovery 的唯一 public writer owner。成功 activation 只生成一个新 target Shot revision、向 Registry append 一个 GENERATED/PNG record，并原子切换 exact project/registry/graph tuple；reader 只按 selected evidence reopen，不扫描 newest file 或隐式恢复。

两个 `static_image` Shot 可以复用同一个 Character 和 Scene reference state，同时各自拥有不同的 generated PNG 与 exact provenance。P7 不修改 `dependency.py`，也不声称 reference bytes 变化会自动触发 regeneration；新 request/output 激活后由既有 P5 resolver 只传播 target Shot visual projection 的精确 downstream invalidation，无关 Shot、audio、voice 和 caption nodes 保持 fresh。Exact replay 的 provider/materializer/Manifest write 均为零；explicit recovery 不 remint permit、不 blind resubmit，只接受 exact old/new tuple 并保留完整 orphan evidence。

P7 原始 fake/no-network acceptance 已随 Base E2E 合入 local `main`。它没有增加 CLI、renderer、Composition/timeline、video generation 或 remote Provider；local `main` 尚未 push、release 或 publish。

### Hybrid Local Image Production (P7.1, offline-verified; live blocked)

`ai_video.production.comfy_image` 提供 sealed Qwen-Image-Edit-2511 与 FLUX.2-klein-4B local execution profile、loopback-only transport、exact workflow binding，以及在任何 P7 R+1 durable evidence 之前执行的 component SHA/size、ComfyUI commit 和 registered `/object_info` node preflight。Exact replay 仍在 preflight 之前返回，因此不会访问 ComfyUI；submit 后 history/output 不确定性继续进入 `outcome_unknown`，recovery 不 remint permit。

`ai_video.production.image_import` 将人工下载的 ChatGPT Images web PNG 记录为 `chatgpt_images_2_web` human import，不虚构 backend model、provider request、durable submit 或 browser automation。Character master、Scene reference、key Shot 与 repair replacement 都复用同一个 `ProductionStateCommitter` project/Registry/P5 graph atomic activation path。

本地 static compatibility gate 已验证 pinned official-template lineage、Qwen profile `local-image-profile:sha256:3871ae162aabe70ff3217ea6a9dbc4e83194b70a1d00e2ca249da202d4d8c6df`、FLUX profile `local-image-profile:sha256:3963b58e0aad18e8359044b9ad043c92961c940dde19002f94723cd196718eb8`、两个 lane 的 exact component digests、ComfyUI checkout `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`、Torch `2.11.0+cu130` / CUDA `13.0` 与 lane budgets。2026-08-18 的首次授权 M7 session 在唯一一次 Qwen submit 后因 reference fixture 不是可解码 PNG 而失败，Manifest 记录 `outcome_unknown` 并 recovery 到 revision 6；没有 blind retry，也没有 FLUX submit。smoke fixture validation 已增加 PNG chunk/CRC/IDAT 解压回归并改用有效 PNG，但重新 live submit 需要新授权。M8 仍缺至少 18 组人工 ChatGPT web outputs、两名 reviewer 与 tie-break，因此 P7.1 仍不得称为 live-accepted 或 quality-accepted。

## Base AI Comic E2E

已合入 local `main` 的 Base AI Comic E2E 证明 no-Video-Provider production path 可以从 reusable Character/Scene state 生成两个独立 PNG，继续完成 fake voice、canonical `CaptionTrack`、`ResolvedTimeline`、injected HyperFrames render、strategy-aware QA、exact composition repair、rerender 与 Final Acceptance。Fresh runtime 会 reopen exact Project/Registry/Graph/Render/Review/Repair evidence；exact replay 的 image、voice、analysis、renderer 与 Manifest write counters 全部为零。

这个 acceptance 只组合既有 P3-P7 contracts。Manifest 2.5 的 image evidence 在 voice、render、review、repair、recovery 与 replay 后保持不变；没有增加 schema、public CLI、production coordinator、asset layout、runtime dependency、concrete/live Provider 或 P8 implementation。Task 8 full suite 为 `1714 passed, 4 skipped`，Architecture Gate PASS，independent review verdict 为 `accept`、无 blocker。P8 仍需单独获批并验收 Paid Provider Gate；local `main` 尚未 push、release 或 publish。

## Development MCP

Project-local MCP configuration exposes `video-analysis` as the default video inspection server for this repository.

If you also have a global `videoscan` MCP installed, treat it as optional helper tooling for metadata lookup or raw frame extraction only. For repo work here, use `video-analysis` for probing, scene detection, frame extraction, transcription, and technical evidence collection. Its legacy optimization helpers remain outside the Production control plane; Production review requires committer-issued durable intent and a one-use analysis permit, and Production repair/final acceptance remain owned by `ProductionStateCommitter`.

## Validate Example Files

```bash
ai-video validate --project configs/example.project.yaml --shots configs/example.shots.yaml
```

The example workflow is API-format JSON for validation and rendering tests.

There is also a real Wan 2.2 example wired from a ComfyUI UI-graph export:

```bash
ai-video validate --project configs/wan22.project.yaml --shots configs/wan22.shots.yaml
```

For faster iteration while tuning prompts, bindings, or workflow parameters, use the quick preset:

```bash
ai-video validate --project configs/wan22_fast.project.yaml --shots configs/wan22_quick.shots.yaml
```

The Wan 2.2 image-to-video presets expect the first shot to provide an `init_image`. Match that image's aspect ratio to your target output to avoid portrait clips being normalized into a landscape delivery.

## Workflow JSON

`ai-video` accepts either:

- ComfyUI API-format JSON
- ComfyUI UI workflow graph JSON

If you point to a UI workflow graph JSON, the CLI converts it to an API prompt before validation and submission. API-format JSON still remains the lowest-risk option when you want exact parity with a known exported prompt.

When the ComfyUI graph changes, update the matching binding file under `workflows/bindings/`.

## Run

```bash
ai-video run --project configs/example.project.yaml --shots configs/example.shots.yaml
```

For quick Wan 2.2 verification runs that finish much faster than the full 3-shot preset:

```bash
ai-video run --project configs/wan22_fast.project.yaml --shots configs/wan22_quick.shots.yaml --run-id quick-verify
```

Generated artifacts are written under `runs/<run_id>/`:

- `manifest.json`
- `shots/<shot_id>/clip.mp4`
- `shots/<shot_id>/last_frame.png`
- `normalized/<shot_id>.mp4`
- `final/final.mp4`

The runtime persists rendered workflow snapshots and every Shot Attempt history, including a terminal failure, before the original failure escapes. A later resume appends to that history. Delete old `runs/<run_id>` directories manually when you no longer need them.

## FPS Semantics

`defaults.fps` is both the generation fallback and the fixed delivery-normalization FPS. A Shot-level `fps` overrides only source workflow generation; it does not change normalization. This compatibility behavior adds no config or Manifest schema fields.

## Resume

```bash
ai-video resume --manifest runs/<run_id>/manifest.json
```

Resume reloads the existing Manifest and validates each successful Shot's persisted clip and last-frame hashes before deciding whether to skip it. For a Shot actually bound to the previous frame, resume also compares the persisted direct-upstream frame hash: a changed hash stales only its direct consumer, then propagates edge-by-edge when a new output changes the next upstream hash. An identical regenerated frame does not stale its consumer, and an explicit Shot `init_image` stops this previous-frame dependency. Character-reference hashes are recorded but are not validity inputs in P1.

## Real ComfyUI Smoke Test

1. Start local ComfyUI.
2. Verify a known-good image-to-video workflow manually.
3. Either export API-format JSON or save the UI workflow JSON.
4. Update the project config to point to that template.
5. Update the matching binding file so each path matches the workflow node IDs.
6. Run `ai-video validate`.
7. Run a 3-shot example.
8. Confirm every shot has `clip.mp4` and `last_frame.png`.
9. Confirm `final/final.mp4` plays.
