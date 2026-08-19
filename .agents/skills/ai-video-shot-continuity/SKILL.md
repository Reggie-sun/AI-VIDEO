---
name: ai-video-shot-continuity
description: Project-level workflow and guardrails for AI-VIDEO Shot Continuity, Local MiniMax H3 fl2va, terminal-frame to first_frame binding, official ComfyUI workflow provenance, continuity evidence/replay/recovery, playback-safe review artifacts, and VS Code video playback. Use proactively whenever an AI-VIDEO task mentions H3, shot continuity, first frame, last frame, terminal frame, local ComfyUI video, continuity proof, evidence MP4, black or silent playback, VS Code media preview, or choosing between local draft and paid Provider continuity lanes; also use before changing continuity specs, plans, runtime code, workflow templates, bindings, profiles, proof artifacts, or review paths.
---

# AI-VIDEO Shot Continuity

## Start From Repository Truth

1. Resolve the AI-VIDEO repository root and read `../../../AGENTS.md`.
2. Read `../../../docs/record_for_agent/2026-08-20-h3-shot-continuity-and-vscode-playback.md` as the dated session baseline.
3. For contract, implementation, or acceptance work, also read:
   - `../../../docs/superpowers/specs/2026-08-19-ai-video-shot-continuity.md`
   - `../../../docs/superpowers/plans/2026-08-19-ai-video-shot-continuity.md`
   - `../../../docs/superpowers/specs/2026-08-19-ai-video-minimal-shot-continuity-proof.md` when the task concerns the bounded proof or review artifacts.
4. Treat code, tests, current Git state, and verified runtime evidence as newer truth than the dated record. Never promote a record-only claim into current runtime behavior.
5. Before editing, inspect live writer ownership, `git status --short --branch`, the exact target files, and the index. Preserve unrelated staged or dirty work.

## Classify The Requested Lane

Choose exactly one primary lane before acting:

- **Inspect/report**: perform read-only checks and report current runtime, artifact, or playback truth.
- **Docs/plan**: update contracts only; do not run ComfyUI, generate media, or call a Provider.
- **Runtime implementation**: change the existing provider-neutral continuity path with focused tests and repository Harness checks required by `.agent/harness/policy.yaml`.
- **Local live proof**: require an explicit current request to generate or rerun local media; use only the sealed loopback H3 profile and never add remote fallback.
- **Paid Provider continuity**: require current task-scoped authorization plus exact preview, Budget Guard, Cloud Egress, durable submit intent, and one-use permit.
- **Playback diagnosis**: inspect exact bytes, codecs, audio levels, and the selected review path; do not reinterpret player compatibility as generation failure.

Do not let docs-only work, historical evidence, an installed model, or an existing credential authorize a live call.

## Preserve Continuity Contracts

- Bind the exact activated Shot N terminal PNG bytes to Shot N+1 `first_frame`; matching filenames or paths are insufficient.
- Bind `last_frame` only when both the request and sealed profile explicitly require it. Never silently add, drop, or downgrade it.
- Keep `fl2va` and `ref2va` as separate workflow/profile/checkpoint identities.
- Keep `ProductionStateCommitter` as the only writer, P5 as the only dependency resolver, and `ResolvedTimeline` as the only composition timing owner.
- Keep local H3 loopback-only with no proxy, refiner, cloud fallback, or automatic Provider escalation.
- Treat the pinned official Comfy-Org workflow as reviewed node/model compatibility provenance, not as owner of Manifest, Registry, activation, recovery, invalidation, or replay.
- Require upstream workflow upgrades to be reviewed, diffed, hash-resealed, and re-accepted before changing an active production profile.
- Preserve cost order: local H3 draft and screening first; only explicitly selected Shots enter paid Provider lanes.

## Separate Artifact Truth

Always distinguish these artifact layers:

1. **Raw generated asset**: immutable generation/provenance bytes under the project asset store.
2. **Playback-safe evidence**: derived review media such as `runs/h3-minimal-shot-continuity-proof-20260819-v1/evidence/continuity-review-playback-safe.mp4`.
3. **Final production render**: output of the existing composition/audio/caption path.

Do not replace raw provenance with a playback-safe copy. Do not claim that a system player or external player proves VS Code WebView codec support. Do not claim that a technical two-Shot proof establishes subjective continuity quality.

For silent or black playback reports:

1. Resolve the exact path the user opened.
2. Measure streams with `ffprobe` and audio level with `ffmpeg` before diagnosing.
3. Prefer the proof run's `evidence/*-playback-safe.mp4` for human review.
4. Treat `runs/continuity-review-vscode.webm` as valid review media when system playback succeeds; if VS Code reports unsupported format, use `Open in external player` as a byte-preserving fallback.
5. Keep embedded generated-video audio separate from P4 audio ownership; never bypass `CompositionSpec -> ResolvedTimeline -> HyperFrames` because a source MP4 contains audio.

## Verify Claims Proportionally

For implementation or proof work, collect the evidence relevant to the lane:

- exact workflow, binding, profile, component, and artifact hashes;
- loopback endpoint and zero-remote-call evidence for Local H3;
- terminal PNG SHA-256 equality with the consumed `first_frame` bytes;
- candidate/terminal activation, reopen, recovery, P5 closure, and zero-effect replay;
- `ffprobe`, audio-level, black/freeze, contact-sheet, and project-local `video-analysis` evidence when media quality is in scope;
- focused tests and the exact staged or commit-range Harness receipt required by current policy.

State technical acceptance, playback usability, and subjective quality separately. If subjective review was not performed, say so explicitly.

## Stop Conditions

Stop and report the exact blocker when:

- another writer owns the target file or tightly coupled area;
- the task would overwrite or commit unrelated staged work;
- a local task would require remote fallback;
- a paid/live request lacks a valid gate, budget ceiling, materialized external asset identity, or replay-safe permit;
- the proposed change creates a second writer, resolver, timeline, or hidden continuity profile;
- the exact source artifact, hash, evidence identity, or player path cannot be resolved.

Never reset, clean, stash, or overwrite other work to continue.

## Report Completion

Lead with the result and include:

- changed files and commit, if any;
- tests/Harness or the reason they were unnecessary;
- exact playable evidence path when media was produced or diagnosed;
- whether calls were local, remote, paid, or zero-call;
- remaining implementation, live-proof, playback, and subjective-quality risks.
