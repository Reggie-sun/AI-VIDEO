# F-004: Parameter Experiment Tracker — Product Manager Analysis

**Feature**: param-experiment-tracker
**Priority**: High (not Critical -- quality comes first, systematization follows)
**PM Concern**: Reproducibility and transferability enabler. Without it, every model switch starts from scratch.

---

## 1. The Problem: Memory Loss

### Current Situation

When the user runs the pipeline with different parameters and observes quality changes, that knowledge exists only in their head (and maybe scattered notes). When they later switch models or workflows, all that experiential knowledge is lost.

### The Cost of No Tracking

- **Repeated mistakes**: Parameters that produced bad output are re-tried because the failure was not recorded
- **No reproducibility**: A good output cannot be reproduced because the exact parameters were not captured
- **No transferability**: Lessons from Wan2.2 tuning do not inform the next model's tuning strategy
- **No progress visibility**: Cannot see whether the quality trajectory is improving over time

---

## 2. Minimum Viable Experiment Tracker

### What It Must Capture

| Field | Purpose | Example |
|-------|---------|---------|
| Experiment ID | Unique identifier | EXP-001 |
| Date | When it was run | 2026-05-02 |
| Model/Workflow | Which model and workflow template | Wan2.2 I2V v1.2 |
| Parameters | Complete parameter snapshot | sampling_steps=30, cfg=7.5, seed=100, ... |
| Output reference | Link to run artifacts | runs/run-xxx/ |
| Quality tier | Evaluation result | Q1 |
| Key observations | What happened | "Face morphing in shot_002; outfit stable" |
| Next action | What to try differently | "Increase sampling steps to 40" |

### Format: Start Simple

**Day 1 format**: A markdown file in the project directory.

```markdown
# Experiment Log

## EXP-001 — 2026-05-02
- Model: Wan2.2 I2V
- Workflow: wan22_i2v_api.json
- Params: steps=20, cfg=7.0, seed=100, neg_prompt="", style="cinematic"
- Output: runs/run-20260502-xxx/
- Quality: Q1
- Notes: Face stable but background flickers in shot_003
- Next: Try steps=30, add negative prompt for flickering
```

This costs zero development effort. It is a text file. It can be searched, versioned, and read by anyone.

### Phase 2+ Format: Structured Data

When the number of experiments grows (10+), a markdown file becomes unwieldy. At that point, consider:
- JSON or YAML experiment records
- A simple Python script to query/filter experiments
- Integration with the manifest (each run's manifest links to its experiment record)

**But do not build this until the simple format proves insufficient.**

---

## 3. The Reproducibility Contract

### What "Reproducible" Means

Given an experiment record, someone SHOULD be able to:
1. Set up the same model + workflow version
2. Apply the same parameters
3. Get output within the same quality tier

### Why This Matters for Model Switching

When switching from Wan2.2 to a new model:
1. The old experiment log shows what parameters mattered for Wan2.2
2. The new model's parameters are different, but the **quality criteria** are the same
3. The experiment log from Wan2.2 tells you what to watch for (e.g., "CFG above 9 caused face morphing")
4. This informs the initial parameter search for the new model

The experiment tracker is not about reproducing the exact same output -- it is about reproducing the **quality level** with a different model by transferring the **knowledge of what matters**.

---

## 4. Integration With Other Features

### F-001 (Quality Baseline)

F-001 produces the first experiment records. Each community config test is an experiment. The tracker records which config got closest to Q1.

### F-003 (Evaluation Framework)

Each evaluation result flows into the experiment tracker. The tracker is the persistence layer for the evaluation framework.

### F-005 (Full-Video Evaluation Loop)

Each loop iteration creates one experiment record. The loop is: run → evaluate → record → adjust → repeat. The tracker is the "record" step.

### The Data Flow

```
F-005 (Loop) → F-003 (Evaluate) → F-004 (Record) → Next iteration
                                        ↓
                              F-001 (Baseline) uses records
```

---

## 5. PM Recommendations

1. **F-004 MUST start as a simple markdown log** -- no code, no database, no tooling
2. **F-004 MUST capture model/workflow version** alongside parameters -- this is critical for future model switching
3. **F-004 MUST link to run artifacts** -- the experiment record is not the output; it points to the output
4. **F-004 SHOULD evolve to structured format only when markdown becomes unwieldy** (10+ experiments)
5. **F-004 MUST NOT become a development project** -- if building the tracker takes more than 1 session, the scope is too large
6. **F-004 MAY be automated** (auto-populate from manifest data) in Phase 4, but this is a convenience, not a requirement
