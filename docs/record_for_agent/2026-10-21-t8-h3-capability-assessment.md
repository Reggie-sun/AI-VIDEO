---
record_kind: research_note
topic_id: t8-capability-assessment-2026-10-21
learning_eligibility: ineligible
evidence_index_version: "1"
---

# T8 / MiniMax H3 Capability Assessment Record

Date: 2026-10-21

## Purpose

Capture the desk-research pass and one targeted evidence re-check performed on
`github.com/T8mars/comfyui-minimax-h3-audio-T8` HEAD `e576eba`
(2026-10-20, v1.101.0) against this project's current sealed runtime,
so future evaluators can inherit:

- a stable [L1]/[L2]/[L3]/[L4] evidence grading convention,
- the precise data on Wuli Native 8 weight and 5090 resident memory,
- the corrected MiniMax-H3 vs H3-Max API parameter deltas,
- and a deferred A/B task list that respects the local ComfyUI exemption
  but explicitly avoids blind adoption of T8 features that are
  unverified on RTX 5090 SM120.

This is research, not experiment: no Provider call, no GPU generation,
no model download, no paid action. The deliverables are documented,
reviewed, and pushed; the next actions are A/B tasks owned by future
windows.

## Current Runtime Truth

- Project sealed runtime T8 pin: `custom_nodes/minimax-h3-audio-T8@977df788fcf8`
  (2026-08-21), version 1.36.2. HEAD is 135 commits ahead
  (`git rev-list --count 977df788fcf8..e576eba`).
- Project HAS NOT adopted any 1.85.0 → 1.101.0 feature.
- Closest local-GPU evidence [L3]:
  `docs/v0.2-runtime-baseline.md:1173` — Turbo v2 4-step
  `dual_clock_euler` measured wall 119–155 s, peak GPU
  19,932–26,797 MiB, peak ComfyUI RSS ~58 GiB; faster than Quality v1
  by 65.6% but with motion/detail regression and audio
  Integrated-LUFS ≈ −52.5 (largely inaudible).
- Project historical bottleneck [L3]:
  `docs/v0.2-runtime-baseline.md:1012-1053` — 17 s Ref2VA failed
  6/6 physical submits with OOM root-caused to
  `comfy_kitchen.int8_linear → torch.cat(scaled_parts)` materialising
  full INT32 outputs in eager path because ComfyUI 0.33.2 on CUDA 12.8
  ships with both CUDA and Triton backends disabled by default.
- Project cloud surface [L1]: `src/ai_video/production/minimax_h3.py:200-202`
  caps the official MiniMax-H3 adapter at `768P/4s/16:9` T2V with
  `max_reference_count=0`; `src/ai_video/production/minimax_h3_max.py:37-40`
  covers H3-Max 480P/768P; `src/ai_video/production/metaso_h3.py:148`
  ships the 9-reference-image family.

## Session Work And Decisions

Two durable artifacts were authored and pushed. Both follow the same
English-title / Chinese-narrative convention as the rest of
`docs/research/`.

### Artifact A — Initial capability assessment

- Path: `docs/research/2026-10-21-t8-h3-capability-assessment.md`
- Commit: `838e319`
- Push: `838e319462f3cabe1b5c41bf8d6b53245ab1149e` (confirmed remote main)
- Scope: 14-feature review matrix, 5-dimension priority (P0/P1/P2/不推荐),
  3 most-worthy verification directions + minimal A/B designs,
  phased implementation plan.
- Highlight conclusions later corrected by Artifact B:
  - Wuli weight reported as "19.9 GiB / 25 GB" (inconsistent across
    subagent B and earlier conversation summary; both wrong).
  - H3 prompt enhancement described as `extra.prompt_expansion_mode`
    in the video creation body (wrong — H3 does not carry that
    field; H3 uses the independent `POST /v2/h3_context_ir` endpoint).
  - Regenerate described as a single path with `content + base_video`
    (incomplete — second path `source_task_id` whitelist
    + ≤7-day window is omitted).
  - Spark / KJ Sage / Sol-Attn summarised as "完全失效 on 5090",
    conflating [L1] hard gate code with [L4] actual dispatch result.
  - Audio evaluation gated on a single LUFS threshold (−30 LUFS),
    collapsing Loudness / Quality / Lip-sync / Audio-Action sync
    into one dimension.

### Artifact B — Targeted evidence re-check

- Path: `docs/research/2026-10-21-t8-h3-capability-assessment-revision.md`
- Commit: `661c025`
- Push: `661c0254a5a5e4846f93f52f21f37e49ae648d51` (confirmed remote main)
- Scope: corrects the 5 specific points above; adds strict
  `[L1]/[L2]/[L3]/[L4]` grading envelope; relocates A/B task design
  into A/B/C/D/E tiers by execution cost; rewrites the audio evaluation
  gate as 4 dimensions.

### Decision ledger (this session)

- DID NOT introduce any T8 1.85.0 → 1.101.0 feature into the sealed
  runtime.
- DID NOT download any large model (Wuli weight of 23.29 GiB was named
  in the report only).
- DID NOT call any paid API or run any GPU generation.
- PRESERVED the 12 working-tree modifications owned by other agents
  (visible in `git status --short`); no `git restore --staged` was
  applied to those paths after the initial self-correction commit; the
  only commits made are `838e319` (1 file) and `661c025` (1 file).
- DID NOT alter any node schema seal, profile content hash, workflow
  binding, registry, manifest, or ProductionStateCommitter state.

## Verification And Evidence

All evidence referenced inside the two artifacts is graded. The grading
rubric is now the project's de-facto convention for future T8
evaluations:

| Grade | Meaning |
|---|---|
| `[L1]` | Source code line or official doc quote — verifiable verbatim |
| `[L2]` | T8 author or upstream author GPU benchmark on their hardware |
| `[L3]` | This project's local RTX 5090 / ComfyUI measurement |
| `[L4]` | Unverified inference; must NOT be cited as proof |

The most consequential single-grade move:

| Concern | Pre-revision claim | Post-revision graded form |
|---|---|---|
| Spark on 5090 | "完全失效" | `[L1]` 硬门 SM89; `[L4]` 是否走 dense 完整不报错未实测 |
| Wuli priority | "P0 填空候选" | "P0 高风险 A/B", 强制 P0-a/b/c 三步探针 |
| Audio gate | ≥ −30 LUFS 单阈值 | Loudness / Quality / Lip-sync (≤80 ms) / Audio-Action 4 维 |

A full evidence table is intentionally OMITTED from this record because
it is not eligible for autonomous distillation (research note; no
controlled experiments; no arms). For the per-claim sources, the two
artifacts above are the authoritative references.

## Assessment

Net session verdict: **adopt nothing yet; do the A/B; harden Receipt
schema in parallel**. The project does not have a feature gap relative
to T8 that is worth aggressive adoption — the dominant blocker is
either (a) a stability problem (`torch.cat(scaled_parts)` OOM) that T8
features only obliquely address, or (b) the cloud capability surface
that needs no T8 at all (H3 / H3-Max v2 API).

Direction 1 — **Wuli Native 8** is the only T8 feature with a
defensible case for filling the Quality-v1-vs-Turbo-v2 quality/speed
gap. But the 23.29 GiB weight on a 31.84 GiB GPU leaves only 8.55 GiB
for activation, and the project historical peak activation is ~23.88
GiB. The bottleneck may remain or shift, not necessarily disappear.
The 3-step probe is mandatory.

Direction 2 — **Official API capability completion** is the cleanest
leverage point: 2K, multi-reference, H3-Context-IR, Regenerate (both
paths) are entirely a project-side capability surface that requires no
T8 adoption. Architecture Gate does not block it; paid execution does.
Treat it as a paid provider rollout task, not as a research task.

Direction 3 — **Receipt schema hardening** is the highest-leverage
operational takeaway from the T8 NFE-resume silent-drift finding.
Add `weight_bytes_sha256`, `prompt_content_hash`, `actual_seed`,
`actual_scheduler`, `actual_cfg`, `actual_shift_video`,
`actual_shift_audio` to Receipt; force non-empty writes; add a
regression test that proves "change weight OR change prompt ⇒ Receipt
hash diverges ⇒ Manifest refuses to accept". This work has no GPU
cost and zero blast radius.

Everything else remains not-recommended until A/B evidence on
5090 SM120 is collected, and even then only if it survives the
Per-Shot Post-Media Gate on a real Shot.

## Remaining Risks Or Next Work

- H1–H10 in `2026-10-21-t8-h3-capability-assessment-revision.md` §4
  are `[L4]` claims awaiting A/B; none are currently scheduled
  because this window did NOT open the A/B environment.
- The 12 working-tree dirty modifications owned by other agents
  remain unstaged (no ownership has been transferred). Future windows
  must check `git status --short` before staging to avoid the same
  mixed-commit hazard that was caught and corrected in
  this session.
- H3 / H3-Max cloud 2K rollout will require a Budget Guard entry,
  one-use permit issuance, Task ID persistence, and ratio validation
  in `minimax_h3_v2_api` capability profile. None of those artefacts
  exist yet.
- The T8 `features.json` ↔ `tests/test_preflight_and_registration.py:19`
  node-count drift (738 vs 371) is a T8-internal problem; it does NOT
  block this project's sealed runtime but should be flagged if the
  project ever consumes T8's test output for CI.

## Agent Guardrails

- **Do not equate T8 author's GPU data with this project's RTX 5090.**
  Read `[L2]` as "their hardware", not "ours".
- **Do not collapse audio evaluation into a single LUFS gate.**
  4 dimensions are now the project's de-facto check.
- **Do not assume T8 nodes turn red on failure.** They don't — the
  AGENTS.md / PATCH_STACK_POLICY.md deliberately permits silent
  fallback. Verification = reading `report_json` for
  `scope_effective` / `actual_*_calls` / `delegate_reasons`.
- **Do not commit another window's dirty work.** Always check
  `git status --short --branch` before `git commit`; use
  path-limited `git add <specific-files>` only.
- **Do not quote Wuli weight from memory.** It is 23.290 GiB
  (= 25,007,719,260 bytes). Any other number is wrong.
- **Do not write `extra.prompt_expansion_mode` into a MiniMax-H3 (not
  H3-Max) capability profile.** H3 uses `POST /v2/h3_context_ir`.
- **Do not pass both `source_task_id` and `content + base_video` to
  Regenerate.** They are mutually exclusive; the API will reject.
- **Do not promote `P0 high-risk A/B` past the P0-a/b/c probe
  sequence** without `[L3]` evidence from the 5090.
