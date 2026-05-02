# Cross-Cutting Analysis — Product Manager Perspective

**Session**: WFS-video-quality-crossroads
**Date**: 2026-05-02

---

## 1. Quality-First Strategy: Why It Is Non-Negotiable

### The Value Chain Argument

The product value chain is linear and unforgiving:

```
Quality = 0 → Pipeline value = 0 (regardless of features)
Quality > 0 → Pipeline value = Quality x Feature_Richness
```

A pipeline that runs perfectly, resumes flawlessly, and stitches seamlessly -- but produces unwatchable video -- has zero product value. Feature development on top of Q0 output is pure waste.

### The Sunk Cost Trap

The pipeline is already built (run/resume/stitch/manifest). The temptation is to "add more features" because that feels like progress. But each feature added on top of bad output increases the cost of later quality rework (more code paths to validate against new parameters, more configurations to test). Features MUST wait.

### The Quality Compounding Effect

Quality improvements compound: a single-clip quality fix propagates to every clip in the video. A consistency fix propagates to every transition. But a pipeline feature (parallel shots, for example) only helps if the underlying clips are worth generating. Quality is the highest-leverage investment.

---

## 2. Iteration Cadence: Full Video Per Cycle

### The Full-Video Rule

Every quality iteration MUST produce a complete stitched video (3 clips, ~15 seconds). Rationale:

1. **Single-clip quality does not predict full-video quality**: A good-looking individual clip can still break at transitions
2. **Consistency is only measurable in sequence**: You cannot evaluate cross-clip consistency from a single clip
3. **Stitching artifacts only appear in the final product**: Normalize + stitch can introduce its own issues
4. **Psychological completeness**: Reviewing a full video gives holistic feedback that reviewing clips in isolation cannot

### Iteration Rhythm

```
Research → Configure → Run (full pipeline) → Review full video → Diagnose → Repeat
```

Each cycle SHOULD take 1-2 sessions. If a cycle takes more than 3 sessions without measurable improvement, the approach MUST change (different parameter space, different workflow variant, or escalate to model replacement).

### Anti-Pattern: Per-Clip Micro-Optimization

Do NOT spend many sessions perfecting one clip before running the full pipeline. The risk is over-fitting parameters to one scene that do not generalize. Run full videos early and often.

---

## 3. Model-Switching Future-Proofing

### The Transition Requirement

The user has confirmed plans to switch models/workflows in the future. This means the quality framework MUST NOT bake in Wan2.2-specific assumptions.

### What MUST Be Model-Agnostic

| Component | Requirement |
|-----------|------------|
| Quality criteria (the 7 concrete criteria) | MUST be model-agnostic (face morphing, consistency, etc. are universal) |
| Quality tier definitions (Q0-Q4) | MUST be model-agnostic |
| Evaluation process (run full video → review against criteria) | MUST be model-agnostic |
| Success metric ("would you post this?") | MUST be model-agnostic |

### What WILL Be Model-Specific

| Component | Nature |
|-----------|--------|
| Parameter names and ranges | Wan2.2-specific data |
| Workflow template structure | Model-specific (different node graphs) |
| Optimal sampling steps, CFG values | Model-specific |
| IPAdapter integration details | May vary by model |

### Architecture Implication

The experiment tracker (F-004) MUST record model/workflow version alongside parameters. The quality evaluation framework (F-003) MUST separate "what we measure" (model-agnostic) from "what we tuned" (model-specific). This separation enables future model switches without rebuilding the evaluation system.

---

## 4. Success Metrics Architecture

### Three Layers of Measurement

```
Layer 1: Binary Gate (pass/fail)
  "Would you post this video?" → Yes/No
  This is the ultimate metric. All other metrics are diagnostic.

Layer 2: Quality Tier (ordinal)
  Q0 → Q1 → Q2 → Q3 → Q4
  Tracks progress between binary gate transitions.

Layer 3: Diagnostic Metrics (continuous)
  Face morph count, prompt adherence score, boundary smoothness, etc.
  Explains WHY a video is at a certain tier, enables targeted improvement.
```

### Measurement Protocol

1. After each full-video run, evaluate against Layer 1 (binary gate)
2. If "No," assign a Quality Tier (Layer 2) to track trajectory
3. Use diagnostic metrics (Layer 3) to identify the specific failure mode
4. Target the highest-impact diagnostic metric for next iteration
5. Repeat

### Progress Tracking

| Iteration | Date | Quality Tier | Key Diagnostic | Action Taken |
|-----------|------|-------------|----------------|-------------|
| 0 (current) | 2026-05-01 | Q0 | Face morphing, inconsistency | -- |
| 1 | -- | -- | -- | Community config baseline |
| ... | -- | -- | -- | -- |

This table MUST be maintained throughout the quality optimization process. It serves as both a progress log and a decision record.

---

## 5. The "Quality Plateau" Protocol

### Problem

At some point, parameter tuning may stop yielding improvements. The video reaches Q2 but cannot reach Q3 despite multiple iterations. This is the "quality plateau."

### Decision Tree

```
Quality plateau reached?
├─ Yes, at Q0-Q1 → Model may be fundamentally limited
│  └─ Action: Escalate to model replacement decision (do not waste time)
├─ Yes, at Q1-Q2 → Parameter space may be exhausted
│  └─ Action: Try fundamentally different workflow structure (add IPAdapter, change sampling strategy)
├─ Yes, at Q2-Q3 → Close to target, try fine-grained tuning
│  └─ Action: Focus on specific failure modes (transitions? consistency? fidelity?)
└─ No plateau → Continue iterating
```

### Escalation Criteria

- **3 consecutive iterations** with no tier improvement → Pause and reassess approach
- **5 consecutive iterations** at the same tier → Escalate to model replacement decision
- **Phase 0 gate failure** (community configs do not reach Q1) → Immediate model replacement discussion

---

## 6. Minimal Viable Quality Framework

### What Is Needed Now (Not Later)

The quality optimization process needs a lightweight framework from day one. This is NOT a full testing system -- it is the minimum structure to make quality progress reproducible and transferable.

### Must-Have (Day 1)

1. **Quality criteria checklist**: The 7 concrete criteria defined in analysis.md
2. **Run comparison log**: A simple table tracking iteration → quality tier → key diagnostic
3. **Parameter snapshot**: Record what parameters produced what output (even if just in a text file)

### Should-Have (Phase 3-4)

4. **Automated quality metrics**: Flicker detection, PSNR between adjacent frames, face detection stability
5. **Experiment tracker**: Structured parameter recording with search/filter

### May-Have (Post-Q3)

6. **A/B comparison tool**: Side-by-side playback of different parameter outputs
7. **Regression detection**: Alert when a parameter change degrades a previously-passing criterion

### The Point

Do not build the framework before doing the quality work. Build the minimum needed to make the quality work reproducible, and extend as needed. The framework serves the quality goal, not the other way around.
