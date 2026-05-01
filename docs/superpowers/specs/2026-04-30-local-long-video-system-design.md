# Pure-Local AI Long-Video Generation System Design

Date: 2026-04-30

## Goal

Design a pure-local, CLI-only AI long-video generation system controlled by Python and powered by a local ComfyUI instance. The system generates a sequence of short video clips, extracts the last frame of each clip, feeds that frame into the next clip, and stitches all clips into a longer silent video with ffmpeg.

The first version should prove the full local chain with 3-5 short clips. It should not depend on external video generation APIs, frontend UI, automatic story splitting, model installation, ComfyUI process management, audio generation, or LoRA training.

## Approved Direction

Use a manifest-driven pipeline.

The Python controller reads project configuration and a shot list, renders a ComfyUI API workflow for each shot, submits it to an already-running local ComfyUI server, records every step in a run manifest, extracts the last frame after each successful clip, and uses that image as the next shot's init image. Final clips are normalized and stitched with ffmpeg.

This approach keeps the MVP workflow-agnostic without introducing a plugin system too early.

## MVP Scope

In scope:

- CLI-only project runner.
- Local editable install with a console script entry point.
- Local ComfyUI generation engine, assumed to already be running.
- Workflow-agnostic ComfyUI API-format JSON templates.
- Separate workflow binding files for prompts, seeds, images, output prefixes, and output collection.
- Shot-list-driven generation with 3-5 silent clips for the first prototype.
- Project-level character reference configuration.
- IPAdapter/reference-image injection through workflow bindings.
- Per-shot manifest state and resume support.
- Per-shot retries.
- Last-frame extraction with ffmpeg.
- Final ffmpeg stitching.
- Unit tests for config parsing, workflow rendering, manifest behavior, seed derivation, and ffmpeg command construction.
- Mocked tests for ComfyUI polling and output collection.

Out of scope for the first version:

- Frontend UI.
- External video generation APIs.
- Automatic prompt-to-story or story-to-shot planning.
- Starting or stopping ComfyUI from the CLI.
- Model download/install orchestration.
- LoRA training.
- Audio, subtitles, voice, music, or sound effects.
- Transitions between clips.
- Multi-GPU scheduling.
- Queue management across multiple independent projects.
- PyPI publishing, standalone binary builds, or cross-platform installer packaging.

## Module Boundaries

## MVP Data Flow

```text
project.yaml + shots.yaml + workflow binding
                  |
                  v
          Project Loader / Validator
                  |
                  v
        +-----------------------+
        | Pipeline Orchestrator |
        +-----------------------+
                  |
        per-shot context + prior last frame
                  |
                  v
        Workflow Renderer ---- rendered workflow snapshot
                  |
                  v
          Comfy Client ---- upload refs / chain image
                  |
                  v
          Local ComfyUI ---- generated clip metadata
                  |
                  v
          copied clip.mp4 ---- ffprobe validation
                  |
                  v
          ffmpeg last frame extraction
                  |
                  +---- last_frame.png feeds next shot
                  |
          after all shots succeed
                  v
          ffmpeg normalize + concat
                  |
                  v
          runs/<run_id>/final/final.mp4
```

## Shot State Machine

```text
pending
  |
  v
submitted
  |
  +--> failed_submission ------+
  |                            |
  v                            |
queued                         |
  |                            |
  +--> queue_timeout ----------+
  |                            |
  v                            |
running                        |
  |                            |
  +--> generation_failed ------+
  |                            |
  v                            |
collecting_output              |
  |                            |
  +--> missing_or_bad_output --+
  |                            |
  v                            |
extracting_last_frame          |
  |                            |
  +--> frame_extract_failed ---+
  |                            |
  v                            |
succeeded                      |
                               |
            retry if attempts remain
                               |
                               v
                            pending

terminal failed: no attempts remain or failure is unrecoverable
stale: upstream chain image or referenced input hash changed after success
```

### CLI

Owns user-facing commands and argument parsing.

Expected first commands:

- `validate`: validate project config, shot list, workflow template, and binding file.
- `run`: create a run directory and execute all shots.
- `resume`: resume an existing run from its manifest.

The CLI should not know ComfyUI node details. It delegates to the project loader, orchestrator, and manifest store.

The MVP distribution target is local editable install only. `pyproject.toml` should define a console script, for example `ai-video`, and the README should use that command after `pip install -e .`. Publishing to PyPI or building standalone binaries is not part of the first version.

### Project Loader

Loads and validates:

- Project config.
- Shot list.
- Character profiles.
- Workflow template path.
- Workflow binding path.
- Output directory paths.

It resolves relative paths against the project file location so examples and real projects remain portable.

Because the product promise is pure-local generation, config validation should treat `comfy.base_url` as local by default. `localhost`, `127.0.0.1`, and `::1` are allowed. LAN or remote hosts should require an explicit opt-in such as `comfy.allow_non_local: true`, and the CLI should print a warning that images and workflows will be sent to that host.

Before `run`, the project loader or orchestrator should check that the output root has at least a configurable minimum amount of free disk space. Exact future output size is model-dependent, so the MVP should use a simple guard such as `output.min_free_gb`.

### Workflow Renderer

Loads a ComfyUI API-format workflow JSON template and applies a binding file.

Responsibilities:

- Replace positive prompt fields.
- Replace negative prompt fields.
- Replace seed fields.
- Replace init image / chain image fields.
- Replace character reference image fields.
- Replace IPAdapter weight fields when configured.
- Replace output filename prefixes.
- Produce a rendered workflow snapshot for manifest/debugging.

It should be pure and testable: given a template, binding, and shot context, it returns a rendered workflow object without submitting anything to ComfyUI.

Workflow rendering should use one internal binding path helper for all nested JSON reads and writes. That helper should report the business field name, the failed path, and whether the failure was a missing key, missing index, or wrong container type. Prompt, seed, image, output prefix, and output collection logic should not each hand-roll nested dictionary traversal.

### Comfy Client

Owns communication with the local ComfyUI server.

Responsibilities:

- Check server availability.
- Resolve, upload, or register input images for the MVP.
- Submit rendered workflows.
- Poll for job completion.
- Read queue/history state.
- Request ComfyUI memory cleanup after OOM-like failures when configured.
- Collect output metadata.
- Download or copy output artifacts into the run directory.

The client should not know shot sequencing. It only knows how to submit one workflow and return one completed job result or a typed error.

### Pipeline Orchestrator

Owns the run state machine and shot chaining.

Responsibilities:

- Create or resume a run.
- Execute shots in order.
- Decide whether a shot can be skipped on resume.
- Submit each shot through the Comfy client.
- Trigger last-frame extraction after a successful clip.
- Pass the previous shot's last frame into the next shot context.
- Retry failed shots according to policy.
- Stop the run on unrecoverable failures.
- Trigger final stitching after all shots succeed.

### Manifest Store

Owns persistent run state.

Responsibilities:

- Write manifest updates atomically.
- Record config and workflow hashes.
- Record per-shot status, attempts, seeds, prompt IDs, artifacts, artifact hashes, and errors.
- Validate artifact existence on resume.
- Mark downstream shots stale if an upstream chain image or referenced input hash changes.

### ffmpeg Tools

Own frame extraction, clip validation, normalization, and final stitching.

Responsibilities:

- Probe generated clips with ffprobe.
- Extract a last frame from each clip.
- Normalize clips to a shared fps, resolution, pixel format, and codec profile.
- Generate concat list files.
- Stitch normalized clips into the final output.

### Error Model

All module boundaries should use typed application errors rather than free-form strings. The shared error shape should include:

- `code`: stable machine-readable error code.
- `user_message`: concise CLI-facing explanation.
- `technical_detail`: optional debugging detail.
- `retryable`: whether another attempt may succeed without user changes.
- `cause`: optional original exception.

The pipeline should make retry decisions from `retryable` and failure class, not from exception text.

## Data Models

Use Pydantic v2 models for project config, shot specs, character profiles, workflow binding, and run manifest records. YAML loading should produce plain dictionaries first, then Pydantic should own type coercion, defaults, cross-field validation, and user-facing validation errors.

Keep behavior out of the model classes unless it is simple validation. Pipeline decisions, ComfyUI calls, and ffmpeg operations should stay in service modules.

### ProjectConfig

Conceptual fields:

- `project_name`
- `comfy.base_url`
- `workflow.template`
- `workflow.binding`
- `output.root`
- `defaults.width`
- `defaults.height`
- `defaults.fps`
- `defaults.clip_seconds`
- `defaults.seed`
- `defaults.seed_policy`
- `defaults.negative_prompt`
- `defaults.style_prompt`
- `defaults.max_attempts`
- `defaults.poll_interval_seconds`
- `defaults.job_timeout_seconds`
- `characters`
- `ffmpeg.encoder`
- `ffmpeg.pixel_format`

### CharacterProfile

Conceptual fields:

- `id`
- `name`
- `description`
- `reference_images`
- `ipadapter.weight`
- `ipadapter.start_at`
- `ipadapter.end_at`
- `future_lora.path`
- `future_lora.weight`

The MVP should accept future LoRA fields in config but does not apply them unless the workflow binding explicitly maps them.

### ShotSpec

Conceptual fields:

- `id`
- `prompt`
- `negative_prompt`
- `characters`
- `seed`
- `clip_seconds`
- `fps`
- `width`
- `height`
- `init_image`
- `continuity_note`
- `metadata`

Shot-level values override project defaults. The first prototype should use a manually authored shot list rather than automatic scene planning.

### WorkflowBinding

The binding maps stable business variables to ComfyUI workflow JSON paths.

Example shape:

```yaml
positive_prompt:
  path: ["6", "inputs", "text"]
negative_prompt:
  path: ["7", "inputs", "text"]
seed:
  path: ["3", "inputs", "seed"]
init_image:
  path: ["12", "inputs", "image"]
output_prefix:
  path: ["42", "inputs", "filename_prefix"]
character_refs:
  - character: "protagonist"
    image_path: ["20", "inputs", "image"]
    weight_path: ["25", "inputs", "weight"]
clip_output:
  node: "42"
  kind: "gifs"
  extensions: [".mp4", ".webm", ".mov"]
  select: "first"
```

The MVP can use explicit node IDs because it is simple and reliable when paired with a checked-in workflow template. Future versions can add lookup by node title or adapter classes if multiple workflows become common.

`clip_output` should define enough artifact selection detail to be testable:

- `node`: the output node ID to inspect in ComfyUI history.
- `kind`: the key inside that node's output payload, such as `gifs` for common video helper nodes.
- `extensions`: allowed generated video extensions.
- `select`: which matching artifact to use when multiple files are present, initially `first` or `last`.

Collected artifacts should be normalized into an internal structure with `filename`, `subfolder`, `type`, `extension`, and `source_node` before they are copied or downloaded.

### RunManifest

Conceptual fields:

- `run_id`
- `created_at`
- `updated_at`
- `project_config_path`
- `shot_list_path`
- `project_config_hash`
- `workflow_template_hash`
- `workflow_binding_hash`
- `status`
- `shots`
- `final_output`

Each shot record stores:

- `shot_id`
- `status`
- `attempts`
- `active_attempt`
- `seed`
- `rendered_workflow_path`
- `rendered_workflow_hash`
- `comfy_prompt_id`
- `clip_path`
- `clip_hash`
- `normalized_clip_path`
- `normalized_clip_hash`
- `last_frame_path`
- `last_frame_hash`
- `chain_input_hash`
- `character_ref_hashes`
- `started_at`
- `completed_at`
- `error`

## Project Directory Structure

Recommended first structure:

```text
AI-VIDEO/
  pyproject.toml
  README.md
  configs/
    example.project.yaml
    example.shots.yaml
  workflows/
    templates/
      example_i2v_api.json
    bindings/
      example_i2v_binding.yaml
  src/
    ai_video/
      cli.py
      config.py
      models.py
      pipeline.py
      comfy_client.py
      workflow_renderer.py
      manifest.py
      ffmpeg_tools.py
      errors.py
  tests/
    test_cli.py
    test_config.py
    test_workflow_renderer.py
    test_pipeline.py
    test_manifest.py
    test_ffmpeg_tools.py
    test_comfy_client.py
  docs/
    superpowers/
      specs/
  runs/
    .gitkeep
```

`runs/` should be ignored by git except for a placeholder because it will contain generated videos, frames, rendered workflow snapshots, and manifests.

The MVP retention policy is conservative: keep rendered workflow snapshots, manifests, successful clips, normalized clips, last frames, and failed attempts for debugging. Provide a README note that users can delete old `runs/<run_id>` directories manually. Automated cleanup is out of scope for the first version.

## ComfyUI Workflow JSON Strategy

Use ComfyUI API-format JSON for templates. The template should be exported from a known-good ComfyUI workflow that can generate one short image-to-video clip locally.

The Python controller should not generate ComfyUI graphs from scratch. It should only:

1. Load the template JSON.
2. Load the binding YAML.
3. Verify the template is ComfyUI API-format JSON, not UI workflow JSON.
4. Verify every required binding path exists in the template.
5. Resolve a shot context.
6. Apply replacements through the binding paths.
7. Save the rendered workflow snapshot into the run directory.
8. Submit the rendered workflow to ComfyUI.

This makes model choice and workflow construction a ComfyUI concern, while Python remains the orchestration layer.

The binding file is the contract between Python and the workflow. If a user changes the ComfyUI graph, they update the binding file rather than Python code.

Validation should fail fast with a clear message if the template looks like UI workflow JSON, for example a top-level `nodes` array with UI metadata, instead of API-format JSON with node IDs as top-level keys and each node containing fields such as `class_type` and `inputs`.

## Replacing Prompts, Images, Seeds, And Output Paths

### Prompt Composition

Positive prompt composition should be deterministic:

```text
global style prompt
+ character description blocks for referenced characters
+ shot prompt
+ continuity note
```

Negative prompt composition should be:

```text
global negative prompt
+ shot negative prompt override or extension
```

The system should record the final composed prompts in the rendered workflow snapshot or manifest so a run can be audited later.

### Image Replacement

Image inputs come from three sources:

- Project or shot initial image.
- Previous shot last frame.
- Character reference images.

For the MVP, the Comfy client prepares these images for ComfyUI and returns ComfyUI-compatible image names. The workflow renderer writes those names into LoadImage or equivalent image input nodes through binding paths.

A separate asset manager is a future extraction point if image caching, dedupe, cross-run reuse, or richer validation becomes complex enough to justify its own module.

The first shot should use `shot.init_image` or `project.initial_image` when the selected workflow requires an init image. Text-to-video first-shot support can be added later if a binding marks `init_image` as optional.

### Seed Replacement

Seed policy should be deterministic by default.

Recommended behavior:

- If a shot has an explicit seed, use it.
- Else derive shot seed from the run seed plus shot index.
- Record actual seed in the manifest.
- On retry, reuse the same seed first.
- Optional future setting: use a new derived seed after the first failed retry.

### Output Path Replacement

For each shot attempt, generate a unique output prefix such as:

```text
<project_name>/<run_id>/<shot_id>/attempt_<n>
```

Write that value into workflow output prefix nodes when the binding provides a path. The canonical artifact copied into the run directory should still be controlled by Python, for example:

```text
runs/<run_id>/shots/<shot_id>/clip.mp4
runs/<run_id>/shots/<shot_id>/last_frame.png
```

The system should not rely only on ComfyUI's output directory layout. It should use history metadata and copy/download outputs into the run directory.

## Polling ComfyUI Jobs And Collecting Outputs

Initial MVP flow:

1. Check ComfyUI availability.
2. Upload/register images needed by the shot.
3. POST the rendered workflow to ComfyUI.
4. If ComfyUI returns validation `error` or `node_errors`, fail the attempt immediately.
5. Store `prompt_id` and queue position when submission succeeds.
6. Poll `/queue` and `/history/{prompt_id}` as separate signals.
7. Classify the job as `queued`, `running`, `completed`, `failed`, `missing`, or `timeout`.
8. Stop polling on queue timeout, job timeout, explicit failure, or completed history.
9. Parse the output node declared in the binding after completion.
10. Copy or download the generated clip into the run directory.
11. Validate the clip with ffprobe.

WebSocket progress can be added after the polling path works. It is useful for live progress display but should not be required for the first working prototype.

The Comfy client should expose a lifecycle-aware result instead of a raw history payload. This keeps retry/resume decisions in the pipeline deterministic and gives the CLI clear error messages for validation failures, queued-too-long jobs, execution failures, missing history, and invalid outputs.

Output collection should be binding-driven. For workflows using VideoHelperSuite-style video outputs, the binding can identify a node and output kind such as `gifs`, allowed video extensions, and how to choose from multiple generated files. For image-sequence workflows, future bindings can point to an `images` output kind, but the MVP assumes video file output.

## Last-Frame Extraction And Shot Chaining

After a shot clip passes validation:

1. Use ffmpeg to extract a PNG from the end of the clip.
2. Store it as `runs/<run_id>/shots/<shot_id>/last_frame.png`.
3. Validate the PNG exists and is readable.
4. Record it in the manifest.
5. Use it as `chain_image` for the next shot.

The next shot context should prefer:

1. Explicit `shot.init_image`, if present and the user intentionally overrides chaining.
2. Previous shot `last_frame_path`.
3. Project initial image, only for the first shot.

If the previous shot is regenerated, downstream shots should be considered stale because their chain image changed.

## Avoiding Character And Style Drift

The MVP should reduce drift through consistency rather than complex correction:

- Inject the same project-level character reference images into every shot that uses the character.
- Keep IPAdapter weights stable unless a shot explicitly overrides them.
- Reuse the same global style prompt and negative prompt across all shots.
- Keep model, checkpoint, VAE, sampler, resolution, fps, and clip duration stable across a run.
- Use stable character descriptions from `CharacterProfile` instead of rewriting the same character differently in every shot.
- Feed the previous shot's last frame into the next shot to preserve pose, outfit, lighting, and composition continuity.
- Keep clips short enough that individual generations do not drift too far.

Known risk: last-frame chaining can accumulate artifacts. The design should reserve future config for `anchor_every_n_shots`, stronger periodic reference-image injection, curated keyframes, or LoRA-based identity stabilization. These are not required in the first prototype.

## Failure And Retry Strategy

### Failure Classes

The system should distinguish:

- ComfyUI unavailable.
- Image upload failure.
- Prompt submission failure.
- Queue timeout.
- Generation failure reported by ComfyUI.
- Job timeout.
- Missing output.
- Invalid output file.
- ffmpeg last-frame extraction failure.
- ffmpeg normalization or stitching failure.
- Manifest read/write failure.

Each failure class should map to a typed error code and default retryability. Configuration, validation, missing binding paths, and wrong workflow format are not retryable. ComfyUI transient availability, queue timeout, and output copy failures may be retryable. Invalid generated output and ffmpeg failures should be retryable only when another generation attempt could plausibly produce a valid artifact.

For OOM-like ComfyUI failures, the retry path should optionally call ComfyUI's memory cleanup route before the next attempt. If cleanup fails or the next attempt fails with the same memory class, the CLI should stop with a clear message suggesting a smaller workflow, lower resolution, shorter clip length, or manual ComfyUI restart.

### Retry Policy

Retry at the shot level.

Recommended defaults:

- `max_attempts`: 2 or 3.
- Retry with the same seed first.
- Keep each attempt in its own attempt directory.
- Promote only a validated successful attempt to canonical shot artifacts.
- Do not delete failed attempt artifacts automatically; they are useful for debugging.

### Resume Policy

On resume:

- Load manifest.
- Verify completed shot artifacts still exist and match recorded hashes.
- If a clip exists but its last frame is missing, re-extract the last frame.
- Skip successful shots whose artifacts, upstream chain inputs, and referenced character images are still valid.
- Re-run failed or incomplete shots.
- If a user forces an upstream shot to rerun, mark downstream shots stale.

Manifest writes should be atomic: write a temporary file, then rename it into place.

## ffmpeg Stitching Strategy

The MVP should avoid transitions and audio. It should produce a clean silent video from normalized clips.

Recommended process:

1. Probe each clip with ffprobe.
2. Normalize each clip to the project's fps, width, height, pixel format, and codec settings.
3. Write normalized clips to `runs/<run_id>/normalized/`.
4. Generate a concat list file.
5. Use ffmpeg concat demuxer to produce `runs/<run_id>/final/final.mp4`.

For compatibility, default to H.264 with `yuv420p`. Add an encoder setting so users can choose CPU encoding or NVENC. If all normalized clips share identical parameters, final concat can use stream copy. If not, do a final re-encode pass.

## First Working Prototype Development Plan

### Phase 1: Dry-Run Foundation

- Create project skeleton.
- Define config, shot, character, binding, and manifest schemas.
- Use Pydantic v2 for config, binding, and manifest models.
- Implement validation.
- Validate that ComfyUI base URL is local unless explicitly allowed.
- Validate minimum free disk space under the configured output root.
- Reject non-API-format ComfyUI workflow JSON with a clear error.
- Validate that every required binding path exists before rendering.
- Implement workflow rendering without submitting to ComfyUI.
- Save rendered workflow snapshots.
- Add unit tests for config loading, binding replacement, and seed derivation.

Exit criteria: `validate` and dry-run rendering work against example files.

### Phase 2: Single-Shot ComfyUI Execution

- Implement ComfyUI availability check.
- Implement image upload/register path.
- Submit one rendered workflow.
- Poll history until completion.
- Collect one generated video file.
- Validate the video with ffprobe.
- Add mocked Comfy client tests.

Exit criteria: one shot produces one local clip artifact.

### Phase 3: Shot Chaining

- Execute shots in order.
- Extract last frame after each shot.
- Inject previous last frame into the next shot.
- Record all artifacts in manifest.

Exit criteria: 3-5 clips generate sequentially and each shot after the first receives the previous last frame.

### Phase 4: Resume And Retry

- Add per-shot attempts.
- Add retry policy.
- Add resume command.
- Add artifact validation on resume.
- Add stale downstream handling for regenerated upstream shots.

Exit criteria: interrupted runs can continue without regenerating successful shots.

### Phase 5: Final Stitching

- Normalize all successful clips.
- Generate concat list.
- Produce final silent MP4.
- Record final output in manifest.

Exit criteria: one command produces `final.mp4` from the shot list.

### Phase 6: Prototype Hardening

- Improve error messages.
- Add example configs and README usage.
- Add smoke-test checklist for a real local ComfyUI workflow.
- Document how to export API-format workflow JSON and maintain binding files.

Exit criteria: a new user with an existing ComfyUI I2V workflow can adapt the example binding and run the prototype locally.

## Validation Strategy

Use `pytest` as the MVP test runner. `pyproject.toml` should define test/dev dependencies and the README should document a single local command:

```bash
pytest
```

Automated tests:

- CLI command behavior for `validate`, dry-run `run`, and `resume`, including exit codes and clear error messages.
- Config validation.
- Path resolution.
- Workflow binding replacement.
- Binding path get/set helper behavior, including missing keys and wrong container types.
- Prompt composition.
- Seed derivation.
- Manifest atomic updates and resume decisions.
- Pipeline orchestration with a mocked Comfy client and mocked ffmpeg tools:
  - 3-shot chain passes each last frame into the next shot.
  - retry reuses the same seed before terminal failure.
  - resume skips valid completed shots.
  - upstream hash changes mark downstream shots stale.
- Typed error mapping and retryability decisions.
- ffmpeg command construction.
- ffmpeg integration tests using tiny generated video fixtures when `ffmpeg` and `ffprobe` are available:
  - last-frame extraction writes a readable PNG.
  - normalization produces expected fps/resolution/pixel format.
  - concat list handles paths with spaces and produces a playable MP4.
  - tests skip with a clear reason if ffmpeg binaries are unavailable.
- ComfyUI client behavior with mocked HTTP responses.
- ComfyUI client failure matrix with mocked HTTP responses:
  - server unavailable.
  - `/prompt` validation `error` and `node_errors`.
  - queued-too-long timeout.
  - job timeout.
  - missing history.
  - execution failure payload.
  - missing output node or output kind.
  - multiple output candidates and extension filtering.
- Output collector behavior for expected history payload shapes.

Manual smoke test:

1. Start local ComfyUI.
2. Verify one known-good I2V workflow works manually.
3. Export API-format workflow JSON.
4. Create binding YAML.
5. Run `validate`.
6. Run a 3-shot example.
7. Confirm each shot has `clip.mp4` and `last_frame.png`.
8. Confirm final `final.mp4` plays.
9. Interrupt and resume a run to verify manifest behavior.

## Key Design Risks

- ComfyUI workflow output metadata differs between nodes. Mitigation: make output collection binding-driven.
- Node IDs in workflow templates can change when users edit graphs. Mitigation: keep template and binding versioned together; add validation that all bound paths exist.
- Last-frame chaining may accumulate visual artifacts. Mitigation: keep clips short and inject character references every shot; reserve future anchor/keyframe support.
- Different generated clips may have incompatible encoding parameters. Mitigation: always normalize clips before concat.
- Retry with new seeds can hide deterministic workflow errors. Mitigation: retry same seed first and record all attempts.

## Engineering Review Notes

These notes were added by `/plan-eng-review` on 2026-04-30.

### What Already Exists

- Existing project code: none. The repository currently contains this design document and `TODOS.md`.
- Existing tests: none. The implementation should introduce pytest from the first code change.
- Existing local services to reuse: a user-managed local ComfyUI server and local ffmpeg/ffprobe binaries.
- Existing ComfyUI capability to reuse: API-format workflow submission, image upload, queue/history polling, optional WebSocket events, and memory cleanup route.
- Existing media capability to reuse: ffmpeg probing, last-frame extraction, normalization, and concat demuxer.
- Existing design decisions to preserve: workflow-agnostic templates, binding-driven replacements, per-shot manifest, deterministic seeds, local-only default, and no frontend.

### NOT In Scope

- Frontend UI: CLI-only is enough to prove the local generation chain.
- External generation APIs: violates the pure-local product constraint.
- Automatic story-to-shot planning: useful later, but manual shot lists keep MVP deterministic.
- ComfyUI process management: users start ComfyUI themselves for v1.
- Model download/install orchestration: too environment-specific for the first prototype.
- Public package publishing or standalone installers: local editable install is the MVP distribution target.
- WebSocket progress UI: tracked in `TODOS.md`, but polling is enough for v1 correctness.
- Separate Asset Manager module: tracked in `TODOS.md`, but image prep stays in Comfy client for MVP.
- Automatic old-run cleanup: tracked in `TODOS.md`; manual deletion avoids early destructive behavior.
- Audio, subtitles, transitions, LoRA training, multi-GPU scheduling, and queue management across multiple projects: all defer until the video chain works.

### Planned Coverage Diagram

```text
CODE PATHS                                                USER FLOWS
[+] cli.py                                                [+] Validate project
  ├── [PLAN] validate success/failure branches              ├── [PLAN] good config exits 0
  ├── [PLAN] run creates new manifest                       └── [PLAN] bad workflow export gives clear error
  └── [PLAN] resume loads existing manifest               [+] Run 3-shot chain [->E2E]
[+] config.py/models.py                                     ├── [PLAN] config + path validation
  ├── [PLAN] Pydantic valid/invalid configs                 ├── [PLAN] shot 2 receives shot 1 last frame
  ├── [PLAN] non-local ComfyUI opt-in warning               └── [PLAN] output final.mp4 after success
  └── [PLAN] character id/reference validation            [+] Resume interrupted run
[+] workflow_renderer.py                                    ├── [PLAN] skip valid completed shots
  ├── [PLAN] prompt/seed/image binding replacement          ├── [PLAN] re-extract missing last frame
  ├── [PLAN] missing/wrong binding path errors              └── [PLAN] mark downstream stale on hash change
  └── [PLAN] reject UI workflow JSON                      [+] Failure states
[+] comfy_client.py                                         ├── [PLAN] Comfy validation error is actionable
  ├── [PLAN] mocked submit/poll/output collection           ├── [PLAN] queued-too-long is retryable
  ├── [PLAN] prompt validation error / node_errors          └── [PLAN] invalid output stops before stitch
  ├── [PLAN] queue timeout / missing history
  └── [PLAN] artifact selection with multiple outputs
[+] pipeline.py
  ├── [PLAN] retry same seed then fail terminally
  ├── [PLAN] successful chain across 3 shots
  └── [PLAN] stale downstream detection
[+] manifest.py
  ├── [PLAN] atomic write + resume decisions
  └── [PLAN] content hash mismatch decisions
[+] ffmpeg_tools.py
  ├── [PLAN] command construction
  ├── [PLAN] actual last-frame extraction on tiny fixture
  └── [PLAN] concat list escaping/safe paths

PLANNED COVERAGE: 30/30 identified paths
QUALITY TARGET: public functions and commands covered; pipeline happy path gets one mocked E2E-style integration test.
```

### Failure Modes To Cover

| Codepath | Realistic failure | Test coverage | Error handling | User-visible behavior |
|----------|-------------------|---------------|----------------|-----------------------|
| CLI validate | user exports UI workflow JSON instead of API format | planned | typed validation error | clear message with Save API Format guidance |
| CLI run | output root has too little disk space | planned | preflight failure | clear message before generation starts |
| Config loader | shot references missing character ID | planned | Pydantic/cross-field validation | clear config error naming the shot and character |
| Workflow renderer | binding path points through wrong JSON container | planned | binding path helper error | clear field/path error before ComfyUI submission |
| Comfy client submit | `/prompt` returns validation `node_errors` | planned | non-retryable typed error | clear node validation failure |
| Comfy client poll | job remains queued beyond timeout | planned | retryable timeout error | clear queued-too-long message and retry if attempts remain |
| Comfy client collect | output node exists but no allowed video extension | planned | invalid output error | shot fails before ffmpeg and reports expected extensions |
| Pipeline orchestrator | second shot fails after first shot succeeds | planned | per-shot attempt handling | manifest records first success and second failure for resume |
| Manifest resume | last-frame path exists but hash changed | planned | stale downstream detection | downstream shots rerun instead of silently skipping |
| ffmpeg extract | generated clip cannot be decoded | planned | retryable/terminal ffmpeg error based on attempts | clear clip validation/extraction error |
| ffmpeg concat | clip path contains spaces or unsafe characters | planned | concat list escaping and validation | final stitch succeeds or reports exact path failure |
| Memory recovery | ComfyUI fails with OOM-like error | planned | optional memory cleanup before retry | clear cleanup/retry result and next-step advice |

No critical failure mode remains both silent and untested in the plan.

### Inline Diagrams To Maintain During Implementation

- `pipeline.py`: keep a short shot state-machine comment near the orchestrator loop.
- `manifest.py`: keep a resume/stale-decision diagram near manifest validation logic.
- `workflow_renderer.py`: keep a binding path replacement diagram or table near the internal path helper.
- `ffmpeg_tools.py`: keep a pipeline comment for probe -> extract/normalize -> concat when command construction becomes non-obvious.

### Worktree Parallelization Strategy

| Step | Modules touched | Depends on |
|------|-----------------|------------|
| Foundation schemas and CLI shell | `src/ai_video/`, `configs/`, `workflows/`, `tests/` | none |
| Workflow rendering | `src/ai_video/`, `workflows/`, `tests/` | foundation schemas |
| Comfy client | `src/ai_video/`, `tests/` | foundation schemas |
| ffmpeg tools | `src/ai_video/`, `tests/` | foundation schemas |
| Manifest and pipeline orchestration | `src/ai_video/`, `tests/` | workflow rendering, Comfy client interface, ffmpeg tools interface |
| Docs and smoke checklist | `README.md`, `docs/`, `configs/`, `workflows/` | foundation schemas |

Parallel lanes:

- Lane A: foundation schemas and CLI shell -> workflow rendering.
- Lane B: Comfy client after foundation schemas.
- Lane C: ffmpeg tools after foundation schemas.
- Lane D: docs/examples after foundation schemas.
- Lane E: manifest and pipeline orchestration after A, B, and C interfaces settle.

Execution order:

1. Build foundation first.
2. Launch workflow rendering, Comfy client, ffmpeg tools, and docs/examples in parallel worktrees if desired.
3. Merge interfaces.
4. Build manifest and pipeline orchestration sequentially.

Conflict flags:

- Lanes A, B, C, and E all touch `src/ai_video/`, so parallel work should coordinate model/interface changes carefully.
- If only one engineer/agent is implementing, sequential execution is safer until the foundation contracts are stable.

### References Used In Engineering Review

- ComfyUI local server routes: https://docs.comfy.org/development/comfyui-server/comms_routes
- ComfyUI execution messages: https://docs.comfy.org/development/comfyui-server/comms_messages
- ComfyUI API-format workflow submission example: https://docs.comfy.org/development/cloud/overview
- ComfyUI UI workflow JSON schema reference: https://docs.comfy.org/specs/workflow_json
- FFmpeg concat demuxer and image2 options: https://ffmpeg.org/ffmpeg-formats.html

## Open Future Extensions

- Optional ComfyUI process manager.
- WebSocket progress UI in the CLI.
- Workflow adapter plugins.
- First-shot text-to-video mode.
- Image-sequence output mode.
- Audio/music/voice pipeline.
- Subtitle generation.
- LoRA application and later LoRA training workflow.
- Scene planner that converts a story prompt into a shot list.
- Visual review tool for selecting replacement keyframes.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | clean | 17 issues, 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **UNRESOLVED:** 0
- **VERDICT:** ENG CLEARED — ready to implement.
