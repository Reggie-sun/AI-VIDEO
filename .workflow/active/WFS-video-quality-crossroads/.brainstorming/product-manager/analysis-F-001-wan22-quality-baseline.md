# F-001: Wan2.2 Quality Baseline — Product Manager Analysis

**Feature**: wan22-quality-baseline
**Priority**: Critical
**PM Concern**: First gate -- can Wan2.2 even reach Q2? If not, all downstream work is wasted.

---

## 1. The Gate Question

**"Given properly optimized parameters, can Wan2.2 I2V produce single-clip output that reaches at least Q1 (watchable, no jarring artifacts)?"**

This is an existential question for the current project trajectory. If the answer is no, the project MUST pivot to a different model before investing in consistency work, IPAdapter integration, or any other downstream feature.

---

## 2. Why This Is the First Thing

### Dependency Chain

```
F-001 (Wan2.2 baseline) → F-002 (IPAdapter consistency) → F-005 (full-video loop)
                    → F-003 (evaluation framework)
                    → F-004 (experiment tracker)
```

Every other feature depends on F-001 producing a positive answer. Without a quality baseline, IPAdapter consistency work is meaningless (you cannot make bad clips consistent in a useful way), and the evaluation framework has nothing to evaluate.

### Risk of Skipping

If we skip to IPAdapter integration or pipeline features without establishing that Wan2.2 can produce acceptable single clips, we risk:
- Wasting sessions integrating IPAdapter for a model that cannot reach Q2
- Building workflow complexity on top of a fundamentally inadequate model
- Delaying the model replacement decision by weeks

---

## 3. Success Criteria for F-001

### Minimum Viable Result

| Criterion | Threshold | Current |
|-----------|-----------|---------|
| No face morphing | 0 events per 5-second clip | Multiple |
| No body distortion | 0 events per clip | Frequent |
| Semantic correctness | Visual matches prompt | Often fails |
| No flickering | Stable temporal output | Visible strobing |
| Overall quality tier | Q1 (watchable) | Q0 (broken) |

### The Gate Decision

- **Q1 achieved with community configs** → Proceed to F-002 (IPAdapter). Wan2.2 is viable.
- **Q1 achieved only with significant custom tuning** → Proceed cautiously. Document the tuning gap; the model may have limited headroom.
- **Q1 NOT achievable after community + reasonable custom tuning (5+ iterations)** → ESCALATE. Discuss model replacement before continuing.

---

## 4. Approach: Community-First

### Step 1: Research (1 session)

- Search Wan2.2 I2V community workflows, blog posts, Reddit threads
- Identify 2-3 recommended parameter configurations from trusted sources
- Record source, parameters, and claimed quality level

### Step 2: Test Community Configs (1 session)

- Apply each community config to a single test clip
- Evaluate against quality criteria
- Select the best-performing config as the baseline

### Step 3: Gate Evaluation

- Compare best community config output against Q1 criteria
- Make the gate decision (proceed / cautious proceed / escalate)

### Step 4: If Proceeding -- Baseline Documentation

- Record the winning configuration as "Wan2.2 Baseline v1"
- This becomes the reference point for all subsequent quality work

---

## 5. What F-001 Is NOT

- F-001 is NOT exhaustive parameter optimization -- that comes later
- F-001 is NOT about cross-clip consistency -- that is F-002
- F-001 is NOT about building tools or frameworks -- that is F-003/F-004
- F-001 IS a risk gate: confirm the model is viable before investing further

---

## 6. PM Recommendations

1. **F-001 MUST complete before any other feature work begins** -- this is a hard gate
2. **F-001 SHOULD use community configs as-is first** -- do not reinvent; validate what works
3. **F-001 MAY involve limited custom tuning** if community configs are close but not quite Q1
4. **F-001 MUST produce a documented gate decision** -- "proceed," "cautious proceed," or "escalate to model replacement"
5. **Time-box F-001 to 2-3 sessions maximum** -- if no progress after 3 sessions, escalate rather than continue tweaking

---

## 7. Escalation Path

If F-001 gate fails:

1. **Document the evidence**: What was tested, what quality level was reached, what specific failures remain
2. **Evaluate alternatives**: What other I2V models are available locally? (SVD, CogVideoX, etc.)
3. **Assess migration cost**: How much pipeline code depends on Wan2.2-specific workflow structure?
4. **Make decision**: Replace model vs. accept lower quality tier vs. wait for model updates

The silver lining: if model replacement is needed, the pipeline infrastructure (run/resume/stitch/manifest) is model-agnostic. Only the workflow template and binding need to change.
