# F-005: Full-Video Evaluation Loop — Product Manager Analysis

**Feature**: full-video-evaluation-loop
**Priority**: High
**PM Concern**: The iteration engine that drives quality from Q0 to Q3. Without a tight loop, progress is slow and undirected.

---

## 1. The Loop Is the Product

### Core Insight

The quality improvement process IS the product at this stage. The "product" is not the CLI, not the pipeline, not the manifest -- it is the cycle of:

```
Configure → Run full pipeline → Evaluate output → Diagnose failures → Adjust → Repeat
```

Every other feature (F-001 through F-004) exists to make this loop faster, more informed, and more reproducible. F-005 is the loop itself.

---

## 2. Loop Design

### The Tight Loop (Per Iteration)

```
1. Start from last experiment record (F-004)
2. Identify the top failure mode from last evaluation (F-003)
3. Form a hypothesis: "Changing X should improve Y"
4. Make one targeted parameter change
5. Run full pipeline: ai-video run → 3 clips → stitch → final.mp4
6. Evaluate full video against checklist (F-003)
7. Record results in experiment log (F-004)
8. Compare to previous iteration: better / same / worse
9. If better → continue in same direction
10. If same → try a different parameter or approach
11. If worse → revert and try a different hypothesis
```

### Key Rules

1. **One change per iteration**: Changing 3 parameters simultaneously tells you nothing about causality
2. **Full video every time**: Never evaluate quality from a single clip alone
3. **Record before adjusting**: The evaluation MUST be recorded before deciding what to change next
4. **Time-box each iteration**: If an iteration takes more than 1 session, something is wrong (configuration complexity, ComfyUI issues, or scope creep)

---

## 3. The Diagnosis Framework

### Failure Mode Priority

When evaluating a full video, failures MUST be prioritized:

| Priority | Failure Type | Impact | Action |
|----------|-------------|--------|--------|
| P0 | Face morphing / identity change | Unwatchable; blocks all other evaluation | Fix before evaluating anything else |
| P1 | Body distortion / semantic error | Severely distracting; blocks consistency evaluation | Fix before evaluating consistency |
| P2 | Cross-clip inconsistency | Breaks "video" quality even if clips are individually OK | Fix with IPAdapter (F-002) |
| P3 | Flickering / temporal noise | Distracting but not identity-breaking | Fix with sampling parameters |
| P4 | Stitching artifacts | Noticeable at boundaries | Fix with normalize/stitch parameters |

### The Rule: Fix P0 Before P1 Before P2...

Do not try to fix flickering (P3) when there is face morphing (P0). The flickering fix may be irrelevant once the morphing is resolved. Fix the highest-priority failure first, then re-evaluate.

---

## 4. Loop Cadence

### Expected Iteration Budget

| Phase | Expected Iterations | Focus | Success Condition |
|-------|--------------------|-------|-------------------|
| Phase 0-1 | 3-5 | Single-clip fidelity (F-001) | One clip at Q1+ |
| Phase 2a | 2-3 | IPAdapter integration (F-002a) | Character identity stable in 3 clips |
| Phase 2b | 2-3 | IPAdapter + chaining (F-002b) | Full video at Q2 |
| Phase 3 | 3-5 | Polish to Q3 | Full video passes Q3 |

**Total**: 10-16 iterations to reach Q3. At 1 session per iteration, that is 10-16 sessions.

### When the Loop Stalls

If 3 consecutive iterations show no quality tier improvement:

1. **Re-examine the hypothesis**: Are we adjusting the right parameter?
2. **Try a fundamentally different approach**: Different sampling scheduler, different workflow variant, different IPAdapter model
3. **Consult community**: Search for others who solved the same failure mode
4. **Escalate if needed**: After 5 stalled iterations, reconsider the model choice

---

## 5. Automation Opportunities

### What Can Be Automated in the Loop

| Step | Manual Today | Automatable | Effort | Value |
|------|-------------|-------------|--------|-------|
| Run pipeline | Manual CLI command | Already automated (`ai-video run`) | Done | -- |
| Evaluate against checklist | Human review | Partially (face count, frame delta) | Medium | High (reduces fatigue) |
| Record in experiment log | Manual writing | Auto-populate from manifest + checklist | Low | Medium |
| Compare to previous | Manual comparison | Auto-diff of quality metrics | Medium | Medium |
| Suggest next parameter | Human judgment | Not automatable (requires domain expertise) | N/A | N/A |

### Priority for Automation

1. **Auto-record experiment data from manifest** -- Low effort, eliminates manual copying
2. **Auto-run checklist metrics** (frame delta, face count) -- Medium effort, reduces human fatigue
3. **Auto-compare to previous iteration** -- Medium effort, makes trajectory visible

Do not automate the judgment step. The human MUST decide what to change next.

---

## 6. The Full-Video Evaluation Loop and Feature Development

### Why Features Are Locked Behind Q3

The evaluation loop is the only activity that should consume development time until Q3 is reached. Any feature work (parallel shots, WebSocket progress, run cleanup) would:

1. **Interrupt the loop**: Context-switching from quality optimization to feature development breaks the iterative momentum
2. **Not benefit from quality**: Features built on Q0 output cannot be meaningfully tested
3. **Create merge risk**: Feature code changes may conflict with quality-driven parameter and workflow changes

### When Features Resume

After Q3 is achieved, the evaluation loop transitions to a maintenance mode:
- Run the loop occasionally to verify quality stability
- Accept feature development as the primary activity
- Use the quality framework (F-003) as a regression gate for new features

---

## 7. PM Recommendations

1. **F-005 is the operational core of the quality improvement process** -- all other features serve this loop
2. **Each loop iteration MUST produce a full stitched video** -- never evaluate quality from a single clip
3. **Each loop iteration MUST change exactly one parameter** -- causal attribution requires controlled experiments
4. **Failure modes MUST be prioritized** (P0 > P1 > P2 > P3 > P4) -- fix the most impactful problem first
5. **The loop SHOULD be time-boxed to 1 session per iteration** -- if it takes longer, diagnose what is blocking
6. **Stall detection MUST trigger a strategy change** -- 3 iterations without progress = change approach
7. **F-005 MUST NOT be automated end-to-end** -- human judgment for diagnosis and parameter selection is essential
8. **F-005 MAY add selective automation** (auto-record, auto-metrics) to reduce friction, but the judgment step stays human
