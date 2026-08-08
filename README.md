# AI-VIDEO

Pure-local Python CLI for orchestrating long-video generation through a local ComfyUI server.

The MVP reads a project config and shot list, renders ComfyUI workflow JSON per shot, submits each shot locally, extracts the last frame, passes that frame into the next shot, and stitches normalized clips with ffmpeg.

## Roadmap Status

The currently implemented runtime is the pure-local `0.1.x` CLI described in this README. The proposed v0.2 direction is a local-first, provider-agnostic production runtime, but it is delivered through separately approved P0-P9 slices; the specification does not make those features available today.

- Current evidence: [`docs/v0.2-runtime-baseline.md`](docs/v0.2-runtime-baseline.md)
- Target contract: [`docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md`](docs/superpowers/specs/2026-08-08-ai-video-production-runtime-v0.2.md)
- First gate plan: [`docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p0-contract-baseline.md`](docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p0-contract-baseline.md)

Until a later slice is implemented and documented, the public commands remain `validate`, `run`, and `resume`; generation remains local ComfyUI; Manifest v1 and the current artifact layout remain active.

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

The MVP keeps rendered workflow snapshots and the Attempt history attached to a Shot that eventually succeeds. A terminally failed Shot does not yet persist its complete Attempt history; that gap is assigned to the v0.2 P1 plan. Delete old `runs/<run_id>` directories manually when you no longer need them.

## Resume

```bash
ai-video resume --manifest runs/<run_id>/manifest.json
```

Resume currently reloads the existing Manifest and validates the persisted clip and last-frame hashes before deciding whether to skip a successful Shot. `chain_input_hash` and character-reference hashes are recorded but are not yet part of validity, and downstream stale propagation is not wired into the real resume path. Until the P1 fix lands, an upstream rerun can therefore leave a downstream Shot incorrectly skippable when that Shot's own checked hashes still match.

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
