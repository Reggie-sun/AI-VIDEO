# AI-VIDEO

Local-first Python CLI for orchestrating long-video generation through default-local ComfyUI. Non-local ComfyUI requires explicit opt-in.

The MVP reads a project config and shot list, renders ComfyUI workflow JSON per shot, submits each shot locally, extracts the last frame, passes that frame into the next shot, and stitches normalized clips with ffmpeg.

## Roadmap Status

公共 CLI 仍是本 README 描述的 local-first `0.1.x` surface。P2 是可导入、只读的 Python API，用于 strict Production Project 与 content-addressed local assets；P2A 拥有 v2 state commit 和 explicit recovery。P3 deterministic composition、local HyperFrames rendering 与 P4 Voice and Captions 已在 local `main` 验收；当前 feature branch 另包含 P5 immutable Dependency Graph、Manifest-owned lifecycle 与 selective rebuild Python API。P5 不增加 CLI command、第二 renderer 或默认 remote Provider behavior。

- Current runtime evidence: [`docs/v0.2-runtime-baseline.md`](docs/v0.2-runtime-baseline.md)
- New target contract: [`docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md`](docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md)
- Phase dependency map: [`docs/v0.2-agentic-production-roadmap.md`](docs/v0.2-agentic-production-roadmap.md)
- Product reframe plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p0-product-reframe.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p0-product-reframe.md)
- Accepted P2 core plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2-production-project-core.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2-production-project-core.md)
- Accepted P2A state commit plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2a-production-state-commit-protocol.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2a-production-state-commit-protocol.md)
- Verified P3 composition plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p3-deterministic-composition-hyperframes-adapter.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p3-deterministic-composition-hyperframes-adapter.md)
- Accepted P4 voice/caption plan: [`docs/superpowers/plans/2026-08-10-ai-video-agentic-production-harness-p4-voice-and-captions.md`](docs/superpowers/plans/2026-08-10-ai-video-agentic-production-harness-p4-voice-and-captions.md)
- P5 dependency/selective-rebuild plan: [`docs/superpowers/plans/2026-08-11-ai-video-agentic-production-harness-p5-dependency-graph-selective-rebuild.md`](docs/superpowers/plans/2026-08-11-ai-video-agentic-production-harness-p5-dependency-graph-selective-rebuild.md)
- Historical superseded spec: [`docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md`](docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md)
- Implemented local Legacy stabilization record: [`docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md`](docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md)

公共命令仍是 `validate`、`run` 和 `resume`；Legacy generation 继续只使用 default-local ComfyUI，Manifest v1 与 flat Legacy artifact layout 仍有效。P4 已随 `f9eedaeb5f6432d8ba0bf937c78111dbcfa3ce80` fast-forward 合入 local `main`，merged-main full verification 为 `1094 passed, 4 skipped`。P5 当前只在独立 feature branch 实现并完成 deterministic focused acceptance；这些 local changes 均未 push、release 或 publish。

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

## Production Project Core Python API

P2 exposes a Python loading API for an explicitly materialized v2 project:

```python
from ai_video.production import load_production_project

project = load_production_project("projects/example/project.yaml")
```

上面的路径仅为示意；仓库不包含该 example project。Loader 保持 read-only 和 no-network。它以 `project.yaml` 为 stable validated entrypoint，然后验证 Production Manifest 选中的 project/registry snapshot path、semantic identity 和 exact file hash；也验证 sealed creative artifact reference、六种 Shot `visual_strategy` contract、concrete asset ID/type、local file size/SHA-256 与 project-root containment。对 Manifest 2.1/2.2，它还会验证选中的 P3/P4 timeline、audio/caption provenance、source/receipt/output 与 render-state graph；对 Manifest 2.3，它还验证 active immutable Dependency Graph snapshot 与 Manifest-owned dependency states，但不会 scan、repair 或 rewrite。P2A state 存在后，root `project.yaml` 不是 active snapshot bytes truth。

P2 本身不创建目录、不更新 Manifest，也不激活 registry 或 graph revision。P2A 拥有全部 v2 state changes，并与 reader 保持分离。当前没有 v2 CLI、QA/repair flow、Remotion/Captions.ai adapter、Video Provider 或 cloud fallback。

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

Manifest 2.3 是 `active_dependency_graph`、per-node desired/applied fingerprints 和 lifecycle 的唯一 owner。Resolver 用 canonical upstream desired fingerprints 做 precise transitive invalidation，保留无关 fresh nodes；same desired failure 不会 auto-retry，changed desired 才重新进入 stale frontier，renderer source/render 仍作为一个 HyperFrames execution unit。`ProductionStateCommitter` 继续是 graph snapshot write、project/registry/render/graph co-activation、single final Manifest replace 与 explicit recovery 的唯一 control path；不存在第二 Manifest、registry writer、graph writer 或 automatic recovery。

Graph snapshot 使用 canonical `state/dependency_graph.<revision>.json`。Reader/recovery 保持 Manifest 2.0-2.2 compatibility；2.3 的 graph temp、promotion、verification、final Manifest replace、unknown outcome、orphan preservation 与 idempotent recovery 均 fail closed，rollback 只能停用新的 mutation/rebuild entrypoints并保留 2.3 reader/recovery，不能 schema downgrade。默认 P5 acceptance 使用 two-Shot deterministic P4 fixtures、fake/no-network render/voice evidence；required mutation matrix 已证明 script、voice settings、caption timing/style、audio mix、visual asset、CompositionSpec、renderer source/render contract 只影响精确节点，focused result 为 `802 passed`。

P5 没有实现 P6 QA/repair、P7 image generation、P8 Provider/cloud 或 P9 hardening；future generated-image input 只通过 strict synthetic `AssetRecord` seam 验证。Legacy CLI、Manifest v1、flat `runs/` layout、ComfyUI path 和现有公共 CLI 保持不变。

## Development MCP

Project-local MCP configuration exposes `video-analysis` as the default video inspection server for this repository.

If you also have a global `videoscan` MCP installed, treat it as optional helper tooling for metadata lookup or raw frame extraction only. For repo work here, use `video-analysis` for probing, scene detection, frame extraction, transcription, review, optimization planning, safe auto-application of config edits, and comprehensive analysis.

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
