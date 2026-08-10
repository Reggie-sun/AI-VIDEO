# AI-VIDEO

Local-first Python CLI for orchestrating long-video generation through default-local ComfyUI. Non-local ComfyUI requires explicit opt-in.

The MVP reads a project config and shot list, renders ComfyUI workflow JSON per shot, submits each shot locally, extracts the last frame, passes that frame into the next shot, and stitches normalized clips with ffmpeg.

## Roadmap Status

公共 CLI 仍是本 README 描述的 local-first `0.1.x` surface。P2 是可导入、只读的 Python API，用于 strict Production Project 与 content-addressed local assets；P2A 拥有 v2 state commit 和 explicit recovery。P3 deterministic composition 与 local HyperFrames rendering 已在 local `main` 验收；当前 feature branch 另包含已验收的 P4 Voice and Captions Python API。P4 不增加 CLI command、dependency graph、第二 renderer 或默认 remote Provider behavior。

- Current runtime evidence: [`docs/v0.2-runtime-baseline.md`](docs/v0.2-runtime-baseline.md)
- New target contract: [`docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md`](docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md)
- Phase dependency map: [`docs/v0.2-agentic-production-roadmap.md`](docs/v0.2-agentic-production-roadmap.md)
- Product reframe plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p0-product-reframe.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p0-product-reframe.md)
- Accepted P2 core plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2-production-project-core.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2-production-project-core.md)
- Accepted P2A state commit plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2a-production-state-commit-protocol.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2a-production-state-commit-protocol.md)
- Verified P3 composition plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p3-deterministic-composition-hyperframes-adapter.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p3-deterministic-composition-hyperframes-adapter.md)
- Accepted P4 voice/caption plan: [`docs/superpowers/plans/2026-08-10-ai-video-agentic-production-harness-p4-voice-and-captions.md`](docs/superpowers/plans/2026-08-10-ai-video-agentic-production-harness-p4-voice-and-captions.md)
- Historical superseded spec: [`docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md`](docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md)
- Implemented local Legacy stabilization record: [`docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md`](docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md)

公共命令仍是 `validate`、`run` 和 `resume`；Legacy generation 继续只使用 default-local ComfyUI，Manifest v1 与 flat Legacy artifact layout 仍有效。P2/P2A 和 P3 已在 local `main`（`3296b713` 是 P3 fast-forward merge 结果）；P4 只在当前 feature branch 验收。这些 local changes 均未 push、release 或 publish。

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

上面的路径仅为示意；仓库不包含该 example project。Loader 保持 read-only 和 no-network。它以 `project.yaml` 为 stable validated entrypoint，然后验证 Production Manifest 选中的 project/registry snapshot path、semantic identity 和 exact file hash；也验证 sealed creative artifact reference、六种 Shot `visual_strategy` contract、concrete asset ID/type、local file size/SHA-256 与 project-root containment。对 Manifest 2.1/2.2，它还会验证选中的 P3/P4 timeline、audio/caption provenance、source/receipt/output 与 render-state graph，但不会 scan、repair 或 rewrite。P2A state 存在后，root `project.yaml` 不是 active snapshot bytes truth。

P2 本身不创建目录、不更新 Manifest，也不激活 registry revision。P2A 拥有全部 v2 state changes，并与 reader 保持分离。当前没有 v2 CLI、dependency graph、QA/repair flow、Remotion/Captions.ai adapter、Video Provider 或 cloud fallback。

## Production State Commit Protocol (P2A)

P2A is an importable Python API, not a CLI surface. `ProductionManifest` is the sole lifecycle record; its `active_project` and `active_registry` pointers record exact relative paths, semantic revision/content hashes and file SHA-256 hashes. `ProductionStateCommitter` in `ai_video.production.state_commit` is the sole v2 writer and recovery owner.

On POSIX, a commit uses a same-filesystem `state/commit.lock`, writes and file-fsyncs immutable snapshot temps, promotes them without overwrite, parent-directory-fsyncs, then reopens and verifies them. Durable `ProductionManifest` writes also record running and failed attempt lifecycle; the one atomic replacement that switches active pointers is the single logical commit point. Recovery is explicit through `recover_production_state()`; normal P2 loading never silently repairs state. It accepts only an exact old pair or exact new pair, marks interrupted attempts without guessing activation, cleans only bounded non-succeeded owned temporary files, and preserves/reports complete orphan snapshots rather than activating or deleting them. These guarantees are deliberately narrower than byte-identical, all-platform, zero-data-loss or power-loss-safe claims.

The P2A implementation file map is `src/ai_video/production/models.py`, `src/ai_video/production/project.py`, `src/ai_video/production/state_commit.py`, `src/ai_video/production/__init__.py`, `tests/production_project_factory.py`, `tests/test_production_models.py`, `tests/test_production_project.py`, `tests/test_production_validation.py`, `tests/test_production_state_commit.py`, `tests/test_production_state_recovery.py`, and `tests/helpers/p2a_crash_worker.py`.

## Deterministic Composition and HyperFrames (P3)

P3 exposes importable `CompositionSpec`, `ResolvedTimeline`, `resolve_composition()`, lifecycle request/path models and durable `render_with_hyperframes()`. `ResolvedTimeline` is the only ordering and timing truth. The accepted surface is deliberately narrow: local PNG/JPEG/WebP `STATIC_IMAGE` spans, deterministic transforms/z-order/opacity, and zero-duration `CUT` transitions. Crossfade, motion directives, other visual strategies and Remotion selection fail closed.

The renderer is exactly project-pinned `hyperframes@0.7.103` with the verified Chrome Headless Shell `152.0.7928.2`. Every non-version command uses root `--json` inside a fresh user/network/PID namespace with a controlled environment and no host fallback. Generated HTML uses root boolean `data-no-timeline`, exact frame/sample metadata and capture-safe CSS opacity keyframes; URL, raster and source-bundle audits run before activation.

`ProductionStateCommitter` remains the sole writer. It durably records selection before any executable call, owns source/output receipts and the canonical immutable `state/render/**` layout, and switches the single `active_render_state` pointer only after held-FD output verification. Manifest 2.0 remains readable; the first render lifecycle write migrates to 2.1. Changing the active project/registry pair clears the render pointer without deleting immutable evidence. Recovery compares the exact project/registry/render triple and preserves complete orphans.

默认 P3 tests 使用 fake runner 且不联网。Explicit committed-fixture proof 将同一个 two-image `10`-frame `24fps` CUT timeline 渲染两次，验证 frame 4 为红色、frame 5 为蓝色、无 audio、decoded-frame fingerprint 相同、command lineage 精确且 network trace fail closed。这是 frame-equivalence evidence，不保证 MP4 byte-identical。P3 本身不增加 selective rebuild、新 CLI 或 cloud behavior；P4 扩展同一个 renderer contract，而不是增加另一个 renderer。

## Voice and Captions (P4)

P4 将 `dialogue`、`narration`、`ambience`、`sfx` 和 `bgm` 建模为 first-class audio kinds。Local import 与 immutable `VoiceGenerationRequest` flow 绑定 source、speaker/voice、language、script hash、duration、sample rate、channels、loudness、timing、gain/fade/ducking 和 provenance。Provider-neutral `VoiceAssetProvider` contract 要求先完成 deterministic budget/egress preview 与 authorization，P2A 才写 R+1 request 和 R+2 submit intent；只有 committer-issued one-use permit 能跨越 transport boundary。Materialized audio 经 probe、hash，并随 alignment、cost、policy/retention 与 provenance evidence 注册后，才进入 R+3 candidate preparation 与 R+4 activation。

`CaptionTrack` 是 script/transcript identity、segments、optional words、half-open timing、speaker、segmentation policy、confidence/provider、style reference 与 timing fingerprint 的 canonical structured source，不会变成 burned-in pixel state。P4 用 audio spans 和 caption cues 扩展 `CompositionSpec` 与既有 `ResolvedTimeline`；该 timeline 继续是唯一 order/frame/sample/timing owner。Selected HyperFrames renderer 拥有 caption layout/drawing 和 deterministic audio mixing/muxing。

`ProductionStateCommitter` 仍是唯一 v2 writer 和 recovery owner。成功的 P4 lifecycle write 使用 Manifest 2.2 与 Registry 2.1，Composition/ResolvedTimeline 则保持 forward-compatible 2.1 extensions。R+1/R+2/R+3/R+4 crash windows、`outcome_unknown`、explicit recovery 与 idempotent replay 都 fail closed：replay 不再次调用 provider 或 renderer，也不存在 schema downgrade 或 automatic recovery。Rollback 是 operational strategy：关闭或移除新的 P4 entrypoints 与 opt-in adapter，同时保留 Manifest 2.2 及对应 reader/recovery compatibility；当前没有独立的 runtime rollback API。

默认 acceptance 使用 deterministic local fixtures、fake providers/transports 且不联网。`ai_video.production.elevenlabs` 是 thin explicit-opt-in candidate，并且有意不从 package root 导出。P4 acceptance 未进行 ElevenLabs live call、secret 读取、SDK installation，也未使用免费或付费 quota。Live call 即使使用免费额度，也需要单独授权，并重新通过 budget、egress、secret-redaction 与 crash-safe persistence gates。P4 只为未来 P5 暴露 fingerprints 和 dependency inputs；不实现 dependency graph 或 selective rebuild。

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
