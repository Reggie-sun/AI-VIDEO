# Continuity Review Coordinator And Human Evidence UI Implementation Recap

## Status

Implementation complete and committed locally on `main`. No push or release was performed.

## Governing Artifacts

- Task plan: `docs/when_to_do/2026-08-22-continuity-review-coordinator-and-human-evidence-ui.md`
- Related continuity spec: `docs/superpowers/specs/2026-08-19-ai-video-shot-continuity.md`
- This file is an implementation recap, not a new runtime specification or lifecycle contract.

## When To Start

- Phase 1（Product caller and bound decision）在现有 local CUDA reviewer、P6 adjudicator、`VideoGenerationService.fetch_and_activate(...)` 和 `ProductionStateCommitter` seam 已存在且计划状态为 `Ready for bounded implementation` 时开始；本轮已完成。
- Phase 2（read-only Human Evidence UI）必须在 Phase 1 通过 focused verification 并提交后开始；本轮已完成。
- Deferred Phase（`HUMAN_PENDING`、后台队列、多人 review 或 automatic measurement overlay）只有在计划列出的产品需求至少有一项被确认后才开始，不能由当前 UI 实现自动触发。
- 真实 live/paid Provider、媒体生成、real-shot calibration 和 Final Acceptance 不属于本计划的启动条件，必须另行批准和验证。

## Delivered

- Added `src/ai_video/production/continuity_review_coordinator.py` and focused tests.
- Added exact-bound `HumanReviewRequestV1` and `HumanReviewDecisionV1` handling.
- Added stale/tamper checks, reviewer identity validation, injectable local GPU lease, replay behavior, and fail-closed handling for incomplete human evidence.
- Preserved P6 as the sole verdict authority and `ProductionStateCommitter` as the sole durable writer.
- Added read-only Provider Console continuity projection, GET-only API, dependency-free contract helpers, React review UI, and regression tests.
- UI exports only `HumanReviewDecisionV1`; it does not write Manifest state, create canonical evidence, or activate a candidate.

## Commits

- `5e2674a feat: coordinate exact continuity review`
- `05b68f5 fix: reopen continuity fetch size`
- `78b00aa feat: add exact continuity review UI`

## Problems And Resolutions

- The first review identified TOCTOU, GPU lease lifetime, memory/error-boundary, and stale-state risks in the coordinator. These were corrected by reopening canonical state, holding an injectable lease through execution, and using typed fail-closed errors.
- The runtime fetch receipt used `size_bytes`, while the initial coordinator lookup used `artifact_size_bytes`. This was corrected and covered by regression tests.
- The UI review identified same-size media replacement, stale response races, and missing/wrong internal SHA validation. The API now streams the exact descriptor, verifies all hash links, and the UI uses request epochs plus target matching.
- The Phase 1 staged Harness receipt was not freshness-clean because another writer advanced `HEAD` during verification. The routed checks themselves passed; this must not be reported as a fresh clean checkout.

## Verification

- Continuity/P6 focused tests: `103 passed` with 17 unrelated concurrent C4 RED tests deselected.
- Provider Console Python/Harness focused checks: `89 passed`.
- Node continuity tests: `10 passed`.
- Sites API tests: `4 passed`.
- Vite production build: passed.
- Chrome CLI QA: real local workspace catalog/detail, MP4 controls, dialog close, GET-only error handling, and no console errors.
- Phase 2 exact commit-range receipt: `.agent/harness/runs/continuity-review-phase2-range-78b00aa/receipt.json`, status `passed`.

## Explicitly Not Done

The plan intentionally deferred `HUMAN_PENDING`, background scheduling, multi-reviewer queues, automatic measurement overlays, live/paid Provider calls, media generation, real-shot calibration, and Final Acceptance. No repository `VALIDATE` continuity attempt was available, so live human form submission, decision export, and activation were not executed.

## Publication State

`main` is ahead of `origin/main`; the task commits remain local. The shared working tree contains unrelated concurrent changes, which were preserved and not staged or committed by this task.
