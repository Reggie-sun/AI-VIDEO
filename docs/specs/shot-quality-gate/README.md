# Shot Readiness Gate — Slice v3

Status: proposed v3 specification; docs only; no runtime implementation accepted

Owner: Main Agent planning-side pre-submit readiness

本 slice 将 v2 的两个“quality gate”收敛为一个 provider-neutral `ShotReadinessGate`。它消费 current sealed `VideoPlanningRequest` 与已生成的 `VideoGenerationPlan`，在任何 Router、Provider、placeholder/materializer、composition 或 render 调用前给出 deterministic `READY | BLOCKED` 结果。

它不重新推导 `VideoPlanner` 的 strategy、continuity、motion 或 capability truth，也不判断 identity drift、动作自然度、跨 Shot continuity、主观画质或 Final Acceptance。上述 perceptual/semantic quality 仍归 P6 Review 与 human Pilot Reality Gate。

## Documents

1. [requirements.md](requirements.md) — scope、requirements、acceptance 与 traceability。
2. [design.md](design.md) — decision ledger、schemas、algorithm、owner migration 与 Harness routing contract。
3. [tasks.md](tasks.md) — T1–T8 的 RED-first implementation plan 和 deferred slices。
4. [test-spec.md](test-spec.md) — TC-01–TC-20 executable test contract。
5. [integration.md](integration.md) — Main Agent STOP integration 与 current Production route。

## v3 Decision Summary

| Disposition | Check / seam | Canonical owner / rationale |
| --- | --- | --- |
| Keep, rename, and make typed | current plan readiness | `ShotReadinessGate`; replaces the decision body currently inside `require_current_video_plan()` |
| Keep | current request/plan/Shot binding | Gate consumes existing seals and identities; it does not invent canonical truth |
| Keep | required asset readiness | Gate checks only roles already declared by the accepted plan against the current request projection |
| Remove | v2 `STRATEGY` re-derivation | `VideoPlanner` already owns strategy coherence |
| Remove | v2 `COMPLEXITY` | `intent.split()` is not deterministic multilingual semantics and has no canonical typed owner |
| Remove | `RECEIPT_INTEGRITY` | typed fetch receipt validation and durable reopen already own the seal |
| Remove | `CONTENT_TYPE_BINDING` | `VideoFetchReceipt.create()` already checks the durable expected content type; the receipt has no submission projection to re-resolve it |
| Remove from v3 | post-fetch `VideoQualityGate` | no non-duplicative fully projected structural check currently exists |
| Remove from v3 | committer parameters and Manifest hash fields | a pure pre-submit slice has no writer or schema seam |
| Defer | receipt persistence | only as a separately approved Manifest migration with version/reopen/compatibility/recovery contracts |
| Defer | future post-fetch structural projection | only after a real gap exists outside fetch constructor/committer/Review owners |

## Planned Runtime Surface

The future implementation slice may add:

- `src/ai_video/quality_gates/__init__.py`
- `src/ai_video/quality_gates/_readiness_models.py`
- `src/ai_video/quality_gates/shot_readiness_gate.py`
- `src/ai_video/planning/_asset_readiness.py` (single extracted owner for existing role-readiness semantics)
- `tests/fixtures/shot_readiness_factory.py`
- `tests/test_shot_readiness_gate.py`

It must also convert `planning.require_current_video_plan()` into a compatibility wrapper that delegates to the gate and preserves `ErrorCode.PLANNING_PREFLIGHT_BLOCKED`. It must not leave two readiness algorithms.

## Boundary at a Glance

| Concern | Sole owner |
| --- | --- |
| Character / Scene / Shot truth | `ProductionProject` creative artifacts |
| Asset identity, provenance, and active binding | Asset Registry + canonical Shot roles |
| Strategy, continuity, motion, required roles, and capability proposal | `VideoPlanner` |
| Pre-submit current-plan readiness and STOP decision | `ShotReadinessGate` |
| Provider selection/execution and fetched candidate lifecycle | existing AI-VIDEO Router / Provider / `ProductionStateCommitter` |
| Manifest writes, activation, and recovery | `ProductionStateCommitter` |
| Timing and render | `ResolvedTimeline` + HyperFrames |
| Semantic/perceptual QA, repair, and Final Acceptance | P6 Review / Repair + human Pilot Reality Gate |

`READY` only means that the current sealed plan is eligible to enter existing Production gates. It does not mean generated, selected, activated, reviewed, quality-accepted, or finally accepted.

## Status and Count

- Specification: proposed v3, internally paired across all six documents.
- Runtime implementation: not started by this docs-only task.
- Implementation tasks: T1–T8 exactly.
- Executable cases planned: TC-01–TC-20 exactly.
- Deferred sections: D1–D2 only; neither is part of v3 acceptance.
- Provider calls, media generation, Manifest migration, policy edits, and runtime code changes: absent from this revision.
