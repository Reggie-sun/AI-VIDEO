# AI-VIDEO

Local-first Python CLI for orchestrating long-video generation through default-local ComfyUI. Non-local ComfyUI requires explicit opt-in.

The MVP reads a project config and shot list, renders ComfyUI workflow JSON per shot, submits each shot locally, extracts the last frame, passes that frame into the next shot, and stitches normalized clips with ffmpeg.

## Roadmap Status

The public runtime remains the local-first `0.1.x` CLI described in this README. P2 is available as an importable, read-only Python API: it loads strict `ProductionProject` and creative artifacts, validates concrete Shot-to-Asset bindings and verifies a content-addressed local Asset Registry snapshot. P2A separately implements the v2 project/registry commit and explicit recovery protocol on its feature branch; it adds no public command and does not make HyperFrames, Remotion, ElevenLabs, Captions, Audio, dependency graphs or Providers available.

- Current runtime evidence: [`docs/v0.2-runtime-baseline.md`](docs/v0.2-runtime-baseline.md)
- New target contract: [`docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md`](docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md)
- Phase dependency map: [`docs/v0.2-agentic-production-roadmap.md`](docs/v0.2-agentic-production-roadmap.md)
- Product reframe plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p0-product-reframe.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p0-product-reframe.md)
- Accepted P2 core plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2-production-project-core.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2-production-project-core.md)
- P2A state commit plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2a-production-state-commit.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p2a-production-state-commit.md)
- Planning-only P3 composition plan: [`docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p3-deterministic-composition-hyperframes-adapter.md`](docs/superpowers/plans/2026-08-09-ai-video-agentic-production-harness-p3-deterministic-composition-hyperframes-adapter.md)
- Historical superseded spec: [`docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md`](docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md)
- Implemented local Legacy stabilization record: [`docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md`](docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md)

The public commands remain `validate`, `run`, and `resume`; generation remains ComfyUI-only and default-local; Manifest v1 and the current artifact layout remain active. P2 is accepted and present on local `main`. P2A is implemented and independently slice-reviewed on `feat/p2a-production-state-commit`, but is not merged, pushed, released, or published; final whole-branch review follows this documentation checkpoint.

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

The path above is illustrative; this repository does not bundle that example project. The loader is read-only and no-network. It uses `project.yaml` as the stable validated entrypoint, then verifies the Production Manifest-selected project and registry snapshot paths, semantic identities and exact file hashes. It also validates sealed creative artifact references, six Shot `visual_strategy` contracts, concrete asset IDs/types, local file size/SHA-256 and project-root containment. The root `project.yaml` is not the active snapshot bytes truth once P2A state exists.

P2 itself does not create directories, update a Manifest or activate a registry revision. P2A owns those v2 state changes; it remains separate from the P2 reader. There is no v2 CLI, renderer, Audio/Caption domain, dependency graph, QA/repair flow or Provider integration yet.

## Production State Commit Protocol (P2A)

P2A is an importable Python API, not a CLI surface. `ProductionManifest` is the sole lifecycle record; its `active_project` and `active_registry` pointers record exact relative paths, semantic revision/content hashes and file SHA-256 hashes. `ProductionStateCommitter` in `ai_video.production.state_commit` is the sole v2 writer and recovery owner.

On POSIX, a commit uses a same-filesystem `state/commit.lock`, writes and file-fsyncs immutable snapshot temps, promotes them without overwrite, parent-directory-fsyncs, then reopens and verifies them. Durable `ProductionManifest` writes also record running and failed attempt lifecycle; the one atomic replacement that switches active pointers is the single logical commit point. Recovery is explicit through `recover_production_state()`; normal P2 loading never silently repairs state. It accepts only an exact old pair or exact new pair, marks interrupted attempts without guessing activation, cleans only bounded non-succeeded owned temporary files, and preserves/reports complete orphan snapshots rather than activating or deleting them. These guarantees are deliberately narrower than byte-identical, all-platform, zero-data-loss or power-loss-safe claims.

The P2A implementation file map is `src/ai_video/production/models.py`, `src/ai_video/production/project.py`, `src/ai_video/production/state_commit.py`, `src/ai_video/production/__init__.py`, `tests/production_project_factory.py`, `tests/test_production_models.py`, `tests/test_production_project.py`, `tests/test_production_validation.py`, `tests/test_production_state_commit.py`, `tests/test_production_state_recovery.py`, and `tests/helpers/p2a_crash_worker.py`.

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
