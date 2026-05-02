# F-003: Quality Evaluation Framework — Product Manager Analysis

**Feature**: quality-evaluation-framework
**Priority**: Critical
**PM Concern**: Without measurement, optimization is blind. "I think it looks better" is not a quality signal.

---

## 1. Why a Framework Matters

### The Problem With Unstructured Evaluation

Current evaluation is ad hoc: run the pipeline, watch the video, feel disappointed, change something, repeat. This approach has two fatal flaws:

1. **No comparability**: Cannot reliably say whether Iteration 5 is better than Iteration 3
2. **No transferability**: When switching models later, cannot apply the same quality judgment consistently

### What the Framework Needs to Provide

- **Consistent criteria**: Same checklist applied to every output
- **Documented evidence**: Each evaluation recorded with specific observations
- **Progress tracking**: Visible trajectory from Q0 to Q3
- **Model-agnostic structure**: Criteria that work for any I2V model, not just Wan2.2

---

## 2. Framework Design: Human-Centered, Not Automated

### Current Reality Check

This is a solo developer project with no QA team, no automated video quality metrics pipeline, and no budget for ML-based quality scoring. The evaluation framework MUST work within these constraints.

### Phase-Appropriate Approach

| Phase | Evaluation Method | Rationale |
|-------|-------------------|-----------|
| Phase 0-1 | Human review + checklist | Only a few outputs; human judgment is fast and accurate |
| Phase 2-3 | Human review + checklist + simple automated metrics | Volume increases; automated metrics reduce human fatigue |
| Post-Q3 | Full automated + human spot-check | Scale requires automation; human validates edge cases |

### The Checklist (Must-Have from Day 1)

For each full-video output, evaluate:

```
Single-Clip Fidelity:
[ ] No face morphing (0 events across all clips)
[ ] No body distortion (0 events across all clips)
[ ] Semantic correctness (each clip matches its prompt)
[ ] No flickering (stable temporal output in all clips)

Cross-Clip Consistency:
[ ] Character face stable across all clips
[ ] Character outfit stable across all clips
[ ] Character hair/style stable across all clips
[ ] Scene continuity maintained across transitions

Stitching Quality:
[ ] No hard visual jump at clip boundaries
[ ] No color shift at boundaries
[ ] No resolution change at boundaries

Overall:
[ ] Quality Tier: Q0 / Q1 / Q2 / Q3 / Q4
[ ] Would you post this? Yes / No
[ ] Key failure (if any): _______________
[ ] Improvement over last iteration? Yes / No / Same
```

This checklist takes 2-3 minutes to fill out. It is the minimum viable evaluation framework.

---

## 3. Automated Metrics: What to Add and When

### High-Value, Low-Effort Metrics (Phase 2+)

| Metric | What It Measures | Tool | Effort |
|--------|-----------------|------|--------|
| Frame delta | Flickering / temporal stability | Frame-by-frame PSNR or SSIM between adjacent frames | Low (ffmpeg + Python) |
| Face count per frame | Face morphing / disappearance | Face detection per frame, count stability | Low (existing Python libraries) |
| Color histogram stability | Color shifts at boundaries | Histogram comparison between last frame of clip N and first frame of clip N+1 | Low |

### Medium-Effort Metrics (Post-Q3)

| Metric | What It Measures | Tool | Effort |
|--------|-----------------|------|--------|
| CLIP score | Prompt adherence | CLIP model comparison between prompt and frames | Medium |
| Face embedding distance | Character identity consistency | Face embedding extraction, cosine similarity | Medium |

### What NOT to Build

- Full no-reference video quality assessment (VQA) models -- overkill for current scale
- A/B testing infrastructure -- not needed for solo developer
- Real-time quality monitoring -- no streaming use case

---

## 4. Evaluation Log Structure

### Per-Iteration Record

```markdown
## Iteration N — [Date]

**Configuration**: [Link to parameter snapshot]
**Output**: runs/[run_id]/final/final.mp4

### Checklist Results
- Face morphing: [0 / 1 / 2+ events]
- Body distortion: [0 / 1 / 2+ events]
- Semantic correctness: [Pass / Fail — details]
- Flickering: [None / Minor / Severe]
- Character face stable: [Yes / No — details]
- Character outfit stable: [Yes / No — details]
- Scene continuity: [Yes / No — details]
- Boundary quality: [Smooth / Visible / Jarring]

### Quality Tier: Q[0-4]
### Would post: [Yes / No]
### Key failure: [Description]
### Key improvement over last: [Description]
### Next action: [What to try next]
```

### Why This Structure Matters

1. **Forces specificity**: "Looks bad" becomes "Face morphing: 2 events in shot_002"
2. **Enables comparison**: Iteration 3 vs Iteration 5, same criteria
3. **Builds institutional memory**: When switching models later, this log shows what quality problems to watch for
4. **Drives decisions**: "3 iterations without improvement" is detectable from the log

---

## 5. Model-Agnostic Design

### The Separation Principle

The evaluation framework separates **criteria** (what we measure) from **parameters** (what we tune):

- **Criteria** are model-agnostic: "No face morphing" means the same thing regardless of model
- **Parameters** are model-specific: sampling steps, CFG, IPAdapter weight -- these vary by model
- **The mapping** (which parameters affect which criteria) is discovered through experimentation

This separation means when switching models:
- The checklist stays the same
- The evaluation log format stays the same
- Only the parameter snapshot and the mapping change

---

## 6. PM Recommendations

1. **F-003 MUST start with the human checklist from Day 1** -- it costs nothing and provides immediate value
2. **F-003 SHOULD add automated metrics only when the volume of outputs makes human review tedious** (Phase 2+)
3. **F-003 MUST maintain an evaluation log** for every quality iteration -- this is the project's quality memory
4. **F-003 MUST keep criteria model-agnostic** -- Wan2.2-specific observations go in the log, not in the criteria definition
5. **F-003 MAY defer full automation to post-Q3** -- the human checklist is sufficient for quality optimization itself
6. **F-003 SHOULD NOT become a development project of its own** -- the framework serves quality improvement, not the other way around
