---
name: open-video
description: Use for AI-VIDEO Director coverage when raw creative input—missing, vague direction, concept, script, reference-led brief, or draft prompt—must be optimized into approved Shots and ordered coverage; guidance is advisory and must return to AI-VIDEO contracts.
---

# open-video — autonomous director skill

> **AI-VIDEO routing:** Raw creative input uses this Director preflight even for one short clip.
> [`h3-video`](../h3-video/SKILL.md) is eligible only after an approved Shot exists; the upstream
> v0.0.1 single-clip preference below must not bypass this boundary.

## 1. What open-video does

open-video is the **autonomous director** layer on top of open video models. It turns a concept
into a finished film by running the loop no open engine ships natively:

**plan → craft → validate → generate → judge → refine → stitch → deliver**

- **Model-agnostic core** (`core/`): planner (coherence bible), crafter, validator, judge-loop,
  stitcher, selector, ref-pack builder.
- **Pluggable backends** (`backends/<model>/`): baseline = **MiniMax H3** (#1 open model, Arena
  parity with closed, native stereo audio). Future: Wan2.2 (physics), LTX-2.3 (speed).
- **Engine adapter** (`engines/comfyui/`): drives ComfyUI via its HTTP API. open-video is the brain;
  ComfyUI is the hands.

It is NOT a video engine (ComfyUI is the engine) and NOT a model (H3/Wan/LTX are backends). It is
the agent brain ComfyUI lacks: judge→refine + multi-shot stitch + coherence planning **as they
land**.

**v0.0.1 honesty:** prefer [`skill/h3-video`](../h3-video/SKILL.md) for reliable high-quality
single clips. Multi-minute film is the flagship *design*. The judge is REAL when env-wired:
set `OPEN_VIDEO_VLM_URL` + `OPEN_VIDEO_VLM_MODEL` (+ `OPEN_VIDEO_VLM_KEY`) to any
OpenAI-compatible vision endpoint and every shot is scored + diagnosed automatically;
with the env unset it is an honest PASS stub — then manual frame review is mandatory.
Single open models still cap ~15s/shot; longer output needs multi-shot orchestration (partial).

## 2. Agentic procedure — run these steps in order

**Step 1 — Understand the request.** First distinguish raw creative input from an approved AI-VIDEO
Shot / ordered coverage. A user prompt is raw input, not approval. Classify raw input as
`missing`, `direction`, or `draft_prompt`; preserve its subject, action, style, product facts,
references, exclusions, and other explicit constraints. Fill bounded creative gaps when the
direction is adequate; ask a focused question only when an unresolved choice would materially
change product direction or exceed the accepted scope.

**Raw creative input Director boundary.** Every request without an approved Shot / ordered coverage
is a `DIRECTOR_PREFLIGHT_REQUEST`, whether the user supplied no prompt, a vague direction, a
concept/script, a reference-led brief, or a detailed draft prompt. Every such request requires
`director_skill=open-video`. The Agent must optimize raw input into Director coverage and select
exactly one `coverage_strategy`: `single_take` or `multi_shot`. It must not treat prompt presence,
prompt detail, duration, or Provider capability as approval.

Choose the strategy from the ordered narrative beats, whether action/space/time changes need a
viewpoint reset, whether one camera/blocking trajectory can carry every visible change, pacing and
information reveal, identity/continuity risk, and any explicit user single-take/cut preference.
These considerations are not a fixed score or duration formula. Duration is a pacing and
feasibility input, not a creative branch: a rich `30s` single take and a tightly cut `10s`
multi-shot plan are both valid when the Director rationale and coverage agree. Provider capability
is validated downstream and cannot silently choose or rewrite the creative strategy; an infeasible
selected strategy must return to Director planning.

Before crafting an approved Shot or Provider-specific prompt for a `DIRECTOR_PREFLIGHT_REQUEST`,
create Director Coverage Evidence with:

- request facts: `creative_input_kind=missing|direction|draft_prompt`, exact
  `creative_input_evidence` for `direction` / `draft_prompt` and `null` for `missing`,
  structured `creative_constraints` with stable `constraint_id`, `source_text` copied as a
  verbatim substring of `creative_input_evidence`, and `scope=global|beat_specific`,
  `target_duration_seconds`, `coverage_strategy`, `strategy_source`, a non-empty
  `director_decision_rationale`, `strategy_request_evidence` when the strategy was directly
  requested by the user, and
  `director_skill=open-video`;
- ordered `coverage_units`, each with `unit_id`, `duration_seconds`, finite `beat_function`,
  `objective`, `open_state`, `close_state`, finite `shot_scale`, finite `camera_treatment`,
  `camera_intent`, `visible_change`, finite `transition_out`, and `constraint_ids`;
- distinct objectives and visible changes; adjacent ordinary multi-Shot units must change finite
  beat, scale, and camera-treatment categories without requiring those categories to be globally
  unique across a long film; every global constraint ID must bind to every unit, while every
  beat-specific constraint ID must bind to at least one unit.

Validate the evidence before downstream authoring:

```bash
python .agents/skills/open-video/scripts/validate_director_coverage.py <coverage.json>
```

### Requirement-semantics handoff

Schema v3 remains the legacy coverage format and is read under its original rules. New Director
handoffs use schema v4: in addition to the same request and coverage fields, include an
`intent_items` inventory and all five `intent_groups`, even when a group is empty:

- `must_happen`: observable result needed for the approved goal.
- `must_not_happen`: result that would break narrative, quality, continuity, or an explicit user
  constraint.
- `preferred_performance`: a preferred performance or camera treatment for which a reasonable
  alternative can still satisfy the goal.
- `timing_targets`: a time target with `target_kind=delivery_constraint` or
  `target_kind=generation_margin`.
- `acceptable_variation`: a permitted variation linked to the result it must preserve.

Each `intent_items` entry has a stable `intent_item_id`, a single atomic `statement`, an `origin`
of `explicit_user`, `director_choice`, or `repair_margin`, non-empty `source_refs`, and explicit
`related_intent_ids` where it depends on another intent. A source reference carries the exact
`source_hash`, `locator`, source `intent_item_id`, verbatim `quote`, and `origin`; `fixed` is
optional. For `explicit_user`, quote the raw creative input verbatim and bind its SHA-256 to that
exact input. Do not describe a Director-written statement as user evidence. The same source intent
may support separately split performance and timing atoms, but an atom must not be copied into
conflicting groups.

`intent_groups` bind every inventory item by ID. Group entries are `{ "intent_item_id": "..." }`,
while a timing entry also includes its `target_kind`. `acceptable_variation` must name the result it
preserves through `related_intent_ids`. A `generation_margin` must be a `repair_margin` intent and
must point one-way to an original non-margin target; it cannot become an acceptance predicate by
being precise or by appearing in a prompt.

For example, a compound brief such as “the courier holds the sealed key at the delivery cut, no
phone appears, keep identity continuous, use natural hand motion, and reach the pose by 2.7s”
needs separate source-bound atoms for delivery state, phone absence, continuity, natural motion,
and timing. Do not turn the whole sentence, or a recipe margin, into one hard criterion.

Director coverage only records intent and suggested classification. Before any intent can enter the
QA acceptance inventory, the QA acceptance owner must independently approve its `hard_basis`,
predicate, stage, tolerance, measurement, and proof. A hard atom needs an explicit user fixed
requirement, approved narrative result, accepted quality/continuity or cut contract, or applicable
production contract, plus the result it protects and the proof boundary. If a fixed user constraint
conflicts with a proposed variation, return it to authoring/QA instead of weakening it. Prompt
wording, historical observations, Provider recipes, and generation margins never grant that
authority.

`VIDEO_EXTEND`, FLF2V, a terminal-frame handoff, `no cut`, and `uninterrupted` are continuity or
execution treatments, not the Director decision. They are valid only when the selected strategy is
`single_take`; if that strategy has multiple evolving internal coverage units, every non-final
transition must remain continuous. `multi_shot` requires at least two ordered units and cut-class
non-final transitions. `strategy_source=user_requested` requires direct user evidence;
`strategy_source=agent_directed` requires no invented user evidence. Director optimization may
expand gaps or restructure a draft, but must preserve explicit user constraints and disclose its
own decisions through the rationale. An already approved Shot does not re-enter this validator
unless the task changes its creative intent or coverage.

The validator proves declared-inventory structure, verbatim source anchoring, and binding
completeness; it does not prove exhaustive constraint extraction or natural-language entailment.
Before Shot approval, the Agent must first compare raw evidence against the declared inventory for
unextracted explicit constraints, then compare the declared inventory against planned coverage for
omissions, reversals, or unauthorized reinterpretation.

**Step 2 — Pick the mode.** Mode is auto-derived from inputs (see `backends/h3/backend.py` and
`scripts/validate_prompt.py` `detect_mode`):
- **T2V / T2VA** — text only, no image. Native audio + video.
- **I2V / I2VA** — one image (first frame). Instruction line: `"For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced."`
- **FL2VA** — two images (first + last frame). Continuous interpolation. **This is the multi-shot
  chain mode**: previous shot's last frame → next shot's first frame for continuous handoff.
- **L2VA** — one image referenced at the **final** timestamp.
- **R2V / Ref2VA** — reference video/audio for identity / style / motion / voice. Tag refs
  `<Picture 1>`, `<Video 1>`, `<Audio 1>` and explicitly assign each a role.

**Step 3 — Craft the 3-field prompt** (per `backends/h3/PROMPT_GRAMMAR.md`). Exact structure:
```
[<instruction line>     # ONLY for I2V/FL2VA/L2VA — first line, then a blank line]

integrated_multimodal_description: [Shot 1] <style first>, <composition/subjects/scene>. <camera type + amplitude + speed>. [Shot 2] At 00:0X.XXX, the camera cuts to <next beat>.
overall_soundscape: <1–4 sentences: ambient / physical / non-verbal human sound>
non_diegetic_music: <1–3 sentences: instrumentation / tempo / rhythm / dynamics — NO mood words>
```
Hard rules: state **style first** in Shot 1 (Cinematic / live-action / 2D-animated / 3D CG / claymation / watercolor / vintage film); **don't timestamp Shot 1**; later shots use **strictly increasing** cut times within the duration; keep identity/wardrobe/color/objects/spatial relations consistent across shots; camera motion = natural prose combining **type + amplitude + speed** (Push In / Pull Out / Pan / Truck / Tilt / Arc / Tracking / Static / POV / Roll — omit amplitude/speed when medium/normal); dialogue as `<d>[lang] verbatim words</d>` with stable `(S1)/(S2)` speaker IDs (first appearance gives age/gender/on-screen/pitch/timbre/rate/accent); on-screen text in English double quotes, verbatim; **every detail must be visible or audible — no abstract mood/emotion words**; prefer camera motion over a cut for mere distance/angle changes.

**Step 4 — Validate before generate** (`core/validator.py`, hard gate — never skip). Checks: all 3
required fields present; duration within 4–15s; mode matches the instruction line; image/ref counts
match the mode; cut times strictly increasing and within duration; `<d>[lang]…</d>` well-formed.
**Fix every issue before spending GPU.** A shot that fails validation will fail the judge.

**Step 5 — Generate** via ComfyUI (`backends/h3/backend.py` + `engines/comfyui/adapter.py`).
Confirm the server is up first (§3). H3 defaults: 1344×768, 20 steps, `res_multistep` / `simple`
scheduler, `shift_video=12.0` / `shift_audio=3.0`, INT8 ConvRot quants, engine flags
`--lowvram --use-sage-attention`. `length` snaps to the 17k+5 grid.

**Step 6 — Run the mandatory per-Shot post-media Gate.** After each exact MP4 lands, fix its
SHA-256 and immediately call the project-local `video-analysis` MCP. Map raw MCP evidence to the
sealed Shot intent as requirement-level `PASS` / `FAIL` / `NOT_EVALUATED`; from Shot 2 onward,
include previous accepted end-state evidence when continuity applies. Only all-required `PASS`
allows generation of the next Shot. `FAIL`, `NOT_EVALUATED`, missing/stale evidence, identity
drift, or unavailable MCP stops before the next submit. The asynchronous analysis hook does not
satisfy this Gate. Follow `.agent/context/control-plane-playbook.md` `Per-Shot Post-Media Gate`.

The OpenVideo judge (`core/judge.py`) is supplemental. Activate the real judge with env:
`OPEN_VIDEO_VLM_URL` + `OPEN_VIDEO_VLM_MODEL` (+ `OPEN_VIDEO_VLM_KEY`) — the pipeline then
extracts frames and assesses vs prompt intent + quality bar automatically
(`QualityJudge.from_env()` is the entry point; explicit `QualityJudge(vision_fn=…)` also works).
Verdict: **PASS / REFINE / FAIL**, with score + issues in the receipt (`run --json` exposes them).
With the env unset the judge auto-PASSes; that stub is never evidence for the mandatory Gate.

**Step 7 — Stop and diagnose on REFINE / FAIL / NOT_EVALUATED.** Do not submit another Shot or
silently regenerate. If the accepted task scope and Provider gates authorize a new attempt, apply
one targeted fix (prompt tweak / +steps / different mode / ref-pack for identity lock / different
seed), then run that attempt through the same mandatory MCP Gate. Best-of-N is an optional,
separately authorized escape hatch, not the default.

**Step 8 — Stitch accepted multi-shot media.** Each subsequent shot's `first_frame` = the previous
accepted shot's last frame (ffmpeg-extracted at `-sseof -0.1`); a `t2v` shot is auto-upgraded to
`i2v` when a handoff frame exists. Current `LongFilmPipeline.make_film()` must not be used as an
unattended multi-Shot generator when it cannot synchronously wait for the required external MCP
Gate. Invoke one Shot at a time, Gate it, then stitch only accepted shots with ffmpeg concat
(`-f concat -c copy`) and cross-shot audio continuity. Optional 2K upscale remains a final step.

**Step 9 — Deliver.** One coherent film + per-shot receipts (prompt, seed, settings, judge verdict,
extracted frames). Persist receipts under `artifacts/verify/`.

## 3. Key commands

**Server — start ComfyUI first (the engine), on `http://127.0.0.1:8188`:**
```bash
cd /path/to/ComfyUI && python main.py --lowvram --use-sage-attention   # H3 default flags
```
Health check: `curl -s http://127.0.0.1:8188/system_stats` (returns JSON when up). In Python:
`ComfyUIAdapter(server="http://127.0.0.1:8188").health()`.

**Generate one shot — open-video Python API (the contract; lives in `backends/` + `engines/`):**
```python
from open_video.backends.h3.backend import H3Backend
from open_video.core.backend import ShotRequest
from open_video.engines.comfyui.adapter import ComfyUIAdapter

engine = ComfyUIAdapter(server="http://127.0.0.1:8188")
backend = H3Backend()
req = ShotRequest(prompt=<3-field prompt string>, mode="t2v",
                  width=1344, height=768, duration_s=10.0, seed=0)
result = backend.generate(req, engine=engine)   # → ShotResult(ok, video_path, receipt)
```
- User-facing CLI (shipped): `open-video "<concept>" --duration 10 --model h3 --json`
  (durations above ~15s trigger the multi-shot v0 template path — single-shot ≤15s uses your
  prompt verbatim and is the reliable v0.0.1 route).
- Proven baseline scripts (same workflows, ported from the early lab):
  - Single shot: `scripts/h3_agent.py --request "<simple NL>" --duration 5 --width 1344 --height 768`
    (use `--prompt "<full 3-field prompt>"` for best quality; `--first-frame`/`--last-frame` for I2V/FL2VA).
  - Validate: `scripts/validate_prompt.py` (exit 0 = clean, 1 = issues).

**Multishot / long film — one-Shot-at-a-time AI-VIDEO orchestration:**
`plan` is a `list[Shot(scene_id, prompt, mode, duration_s, seed, …)]`. For AI-VIDEO work, invoke one
Shot, wait for the external MCP Gate, and only then extract the accepted last frame and continue.
`core/pipeline.py` `LongFilmPipeline.make_film(plan, out_path)` does not currently own that external
MCP stop point, so it is not an authorized unattended generation path; it may only stitch inputs
that have already passed the per-Shot Gate.
- Proven baseline only, not an AI-VIDEO Gate-compliant unattended path:
  `scripts/h3_multishot.py --plan library/plans/multishot_demo.json --out output/long_demo.mp4`
  (a ready example plan ships at `library/plans/multishot_demo.json`; plan JSON =
  `{"shots": [{"prompt_file": "...", "duration": 10, "first_frame": null}, …]}`).

## 4. Constraints (H3 baseline — hard, evidence-based)

- **Duration: 4–15s per shot** (`backends/h3/backend.py` `constraints()` → `duration_range_s: (4, 15)`).
  No single shot >15s. For longer content, use multishot — that is the entire point of the stitcher.
- **Frame grid: num_frames snaps to 17k+5 @ 24fps** (video-VAE temporal constraint; `_snap_17k5`).
  Valid lengths: 5, 22, 39, 56, … Do **not** pass arbitrary frame counts.
- **Resolution: local ceiling = 768 short edge** (native canvas 768×1344), multiples of 32
  (`resolution_multiple: 32`). **2K = API upscale only** — never attempt 2K locally.
- **Refs: ≤9 images, ≤3 videos, ≤3 audios, ≤12 total** (`max_refs`).
- **Quant — use INT8 ConvRot** (`minimax_h3_fl2va_pruned_int8_convrot.safetensors`, ~21 GB, proven on
  RTX 5090). **Avoid NVFP4 on RTX 5090 — ComfyUI issue #14157 bug** (recorded in
  `backends/h3/backend.py` `default_settings()["known_issues"]` and `docs/h3_ecosystem.md`).
  Other quants: NF4 (~8 GB, lowest VRAM), W4 ConvRot (~10 GB, stock-compatible), BF16 (~62 GB, multi-GPU only).
- **Audio: 32 kHz stereo native; CFG-distilled** (no negative prompt, no guidance scale).
- **Known issues to guard against** (`docs/h3_ecosystem.md` "Known issues"): wide-shot face
  corruption (Comfy-Org #30), 2K upscale fails in ref2va (#19), ref2va persistent noise (HF #50),
  AMD/Apple Silicon partial support (#17/#24/#33), prompt metadata embedded in output files (#13).

## 5. Docs — read these for depth (do not guess from memory)

- `README.md` — what/why, three interfaces (App / CLI / Skill), the thesis.
- `ARCHITECTURE.md` — core / backends / engines / library layers; the quality loop; the long-film pipeline diagram.
- `PLAN.md` — phased roadmap, open decisions, the make-or-break success metric.
- `backends/h3/PROMPT_GRAMMAR.md` — the official H3 3-field prompt guide (condensed). **Read before crafting any H3 prompt.**
- `docs/h3_ecosystem.md` — quants, multishot tools, speed nodes, known issues, build-on targets.
- `templates/model_backend.py` — the plugin template (§6).
- `CONTRIBUTING.md` — plugin points + good-first-issues.

## 6. Adding a model backend (Wan2.2, LTX, …)

The core never changes — add a plugin. Copy `templates/model_backend.py` →
`backends/<model>/backend.py` and implement the `ModelBackend` ABC (`core/backend.py`):

1. **`capabilities`** (`Capabilities(...)`) — which modes (`t2v`/`i2v`/`flf2v`/`r2v`),
   `native_audio`, `max_duration_s`, `max_short_edge_px`, `strengths` (the `selector` keys on these).
2. **`prompt_guide()` + `craft_prompt(intent, mode)`** — your model's prompt grammar.
3. **`constraints()`** — duration range, frame grid (or `None`), `max_refs`, resolution multiple.
4. **`generate(req, engine)` + `_build_workflow(req)`** — build the engine workflow (e.g. ComfyUI
   JSON loaded from `workflows/`), run via the engine adapter, return `ShotResult(ok, video_path, receipt)`.
5. **`default_settings()`** — steps / sampler / scheduler / quant (evidence-based via `bench/`).
6. **`duration_to_length()` / `resolution_for()`** — model-specific frame/fps and resolution-grid math.

Then add `backends/<model>/workflows/` (engine JSON), `PROMPT_GRAMMAR.md`, and `__init__.py`.
**See `backends/h3/backend.py` for a complete working example** — the H3 backend is the reference
implementation. PR it; `CONTRIBUTING.md` lists plugin points as good-first-issues.
