# Product Manager Analysis — AI-VIDEO Quality Crossroads

**Role**: Product Manager
**Session**: WFS-video-quality-crossroads
**Date**: 2026-05-02

---

## Executive Summary

AI-VIDEO is a local long-video generation pipeline that currently produces technically complete but visually unacceptable output. The pipeline runs, stitches, and resumes -- but the video quality is far below any publishable standard. The core product decision is unambiguous: quality MUST be the sole focus until a single complete video meets "commercial-grade" criteria. This analysis defines what "commercial-grade" means concretely, breaks the quality journey into evaluable iterations, and establishes a priority framework that keeps the project on track. The north star metric is simple: **can you post this video on a social platform without embarrassment?**

---

## Product Vision & User Profile

### The Product

AI-VIDEO is a **local-first Python CLI** that orchestrates multi-clip long-video generation through ComfyUI. It takes a project config + shot list, generates each clip via I2V, chains clips via last-frame continuity, and stitches the result into a single publishable video.

### The User (Today)

The primary user is the developer themselves -- a solo creator with an RTX 5090 who wants to produce narrative video content locally without relying on cloud services. The user is both the builder and the first customer.

### Value Proposition

**"Produce narrative-length AI video on your own hardware, with visual quality you can publish."**

The value collapses to zero if the output is unwatchable. A pipeline that runs perfectly but produces bad video is a well-engineered toy, not a product.

### Future Users (Post-Quality)

Once quality is proven, the user profile expands to:
- Content creators who want local, private video generation
- Artists prototyping visual narratives
- Developers extending the pipeline for other models/workflows

These future users will not arrive if the quality bar is not cleared first.

---

## Quality Definition: What "Commercial-Grade" Means

### The Three Pillars

| Pillar | Definition | Failure Mode | Measurable Signal |
|--------|-----------|-------------|-------------------|
| **Single-Clip Fidelity** | Each 5-second clip is visually coherent with no artifacts | Face morphing, body distortion, flickering, semantic errors | Zero face morph events per clip; no visible frame-to-frame distortion |
| **Cross-Clip Consistency** | Characters and scenes remain visually consistent across clips | Character appearance changes, outfit swaps, background jumps | Same character recognizable across all clips; outfit/style stable |
| **Stitching Seamlessness** | Clip boundaries do not produce visible or jarring transitions | Hard cuts, color shifts, resolution changes at boundaries | Smooth visual flow at all clip boundaries |

### Concrete Quality Criteria (MUST all pass)

1. **No Face Morphing**: Face shape, features, and skin tone remain stable within each clip and across clips
2. **No Body Distortion**: Limbs and body proportions remain human-plausible throughout
3. **Semantic Correctness**: The visual content matches the prompt (person walks = person walks, not person dissolves)
4. **Character Identity Stable**: Same person across all clips -- recognizable face, same outfit, same hair
5. **Scene Continuity**: Background and lighting do not jump unexpectedly between clips
6. **No Flickering**: Frame-to-frame coherence without visible temporal noise or strobing
7. **Publishable Resolution**: At minimum 832x480 @ 16fps without visible upscaling artifacts

### Quality Tiers

| Tier | Name | Description | Status |
|------|------|-------------|--------|
| Q0 | Broken | Obvious morphing, distortion, semantic errors | **Current** |
| Q1 | Watchable | No jarring artifacts, but not impressive; noticeable imperfections on close inspection | Target for Iteration 1 |
| Q2 | Passable | No obvious flaws at first glance; minor issues on repeat viewing | Target for Iteration 2 |
| Q3 | Commercial-Grade | Comfortable to post publicly; holds up to typical social media scrolling attention | Target for Iteration 3 |
| Q4 | Premium | Noticeably high quality; viewers pause to watch | Aspirational |

---

## Feature Point Index

| Feature ID | Name | PM Priority | Key PM Concern | Analysis Document |
|------------|------|-------------|----------------|-------------------|
| F-001 | wan22-quality-baseline | **Critical** | First gate: can Wan2.2 even reach Q2? | @analysis-F-001-wan22-quality-baseline.md |
| F-002 | ipadapter-consistency | **Critical** | Cross-clip consistency is the harder problem | @analysis-F-002-ipadapter-consistency.md |
| F-003 | quality-evaluation-framework | **Critical** | Without measurement, optimization is blind | @analysis-F-003-quality-evaluation-framework.md |
| F-004 | param-experiment-tracker | High | Reproducibility and transferability enabler | @analysis-F-004-param-experiment-tracker.md |
| F-005 | full-video-evaluation-loop | High | The iteration engine that drives quality up | @analysis-F-005-full-video-evaluation-loop.md |

### Cross-Cutting Analysis

See @analysis-cross-cutting.md for decisions that span multiple features: quality-vs-features priority framework, iteration cadence, model-switching future-proofing, and success metrics.

---

## Iteration Roadmap

### Phase 0: Quality Baseline Probe (1-2 sessions)
- Research Wan2.2 community best configurations
- Run a single clip with community-recommended parameters
- Evaluate: does the quality ceiling reach Q2?
- **Deliverable**: One clip at community-baseline quality
- **Gate**: If Q1 not reachable, escalate to model replacement decision

### Phase 1: Single-Clip Quality (2-4 sessions)
- Parameter tuning on single clip until Q2 achieved
- Focus: sampling steps, CFG, negative prompt, LoRA selection
- **Deliverable**: One acceptable 5-second clip
- **Gate**: Single clip passes Q2 criteria

### Phase 2: Cross-Clip Consistency (3-5 sessions)
- Integrate IPAdapter into workflow
- Validate IPAdapter + last-frame chaining together
- Run 3-clip sequence; evaluate consistency
- **Deliverable**: 3-clip stitched video with consistent character
- **Gate**: Full video passes Q2 criteria (all three pillars)

### Phase 3: Polish to Commercial-Grade (2-3 sessions)
- Fine-tune transitions at clip boundaries
- Optimize IPAdapter weight and reference selection
- Iterate on full-video quality until Q3
- **Deliverable**: Complete publishable video
- **Gate**: Video passes Q3 criteria; comfortable to post publicly

### Phase 4: Systematize (1-2 sessions)
- Document proven parameter configurations
- Formalize the evaluation framework
- Ensure experiment tracker captures all learnings
- **Deliverable**: Reusable quality framework for future model/workflow changes

---

## Priority Framework

### Decision Rule: Quality Always Wins (Until Baseline Met)

| Condition | Quality Work | Feature Work | Decision |
|-----------|-------------|-------------|----------|
| Current quality at Q0 | Any | Any | Quality ALWAYS wins |
| Quality at Q1 | Consistency improvement | Pipeline features | Quality wins |
| Quality at Q2 (single clip) | Cross-clip consistency | Pipeline features | Quality wins |
| Quality at Q2 (full video) | Polish to Q3 | Non-urgent features | Quality wins |
| Quality at Q3+ | Minor refinement | Feature development | Features MAY proceed |

**The rule is simple**: No feature work until a complete video hits Q3. A pipeline feature that generates bad video faster is negative value.

### Priority Within Quality Work

1. **Single-clip fidelity** -- If individual clips are broken, nothing else matters
2. **Cross-clip consistency** -- Only meaningful after single clips are acceptable
3. **Stitching polish** -- Only meaningful after clips are individually good AND consistent
4. **Framework systematization** -- Important for transferability, but secondary to actually achieving quality

---

## Success Metrics

### Leading Indicators (Per Iteration)

| Metric | How to Measure | Target |
|--------|---------------|--------|
| Face morph events per clip | Human review (count) | 0 |
| Cross-clip character mismatch | Human review (yes/no per transition) | None |
| Prompt adherence score | Human review (1-5 scale) | >= 4 |
| Clip boundary smoothness | Human review (1-5 scale) | >= 4 |
| Total quality tier | Against quality tier definition | Q3 |

### Lagging Indicators (Overall Progress)

| Metric | How to Measure | Target |
|--------|---------------|--------|
| Iterations to reach Q3 | Count | < 15 sessions |
| Parameter configurations tested | Experiment tracker count | >= 10 |
| Failed attempts before Q3 | Experiment tracker count | Accept any (learning) |
| Time from Q0 to Q3 | Calendar | No deadline (quality first) |

### The One Metric That Matters

**"Would you post this video on your social media?"** -- Yes/No. Everything else is diagnostic detail.

---

## User Journey & Pain Points

### Ideal Workflow (Target State)

```
1. Prepare reference images (character, style)
2. Write shot list with prompts
3. Configure project YAML (workflow, defaults, character refs)
4. Run `ai-video run`
5. Wait for generation (~5-10 min local)
6. Review final.mp4
7. If quality acceptable -> publish
8. If not -> adjust parameters, re-run
```

### Current Pain Points (Q0 Reality)

| Step | Pain Point | Severity |
|------|-----------|----------|
| 1 | No reference image support (IPAdapter missing) | Critical |
| 2 | Prompts produce unpredictable results (parameters unoptimized) | Critical |
| 3 | Character refs config exists but is empty (`characters: []`) | Critical |
| 4 | Run works but produces unwatchable output | Critical |
| 5 | N/A | -- |
| 6 | Review reveals morphing, inconsistency, semantic errors | Critical |
| 7 | Cannot publish -- every attempt fails quality bar | Critical |
| 8 | Re-running with same parameters produces same bad results | Critical |

### Key Insight

The user journey is completely blocked at step 6-7. The pipeline is mechanically correct, but the output fails the only test that matters: is it watchable? No amount of pipeline feature development will unblock this. Only quality optimization will.

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Wan2.2 quality ceiling below Q3 | Medium | Critical | Phase 0 gate: if community configs do not reach Q1, escalate to model replacement early |
| IPAdapter + chaining conflict | Medium | High | Phase 2: test IPAdapter alone first, then add chaining incrementally |
| Endless parameter tuning without progress | Medium | Medium | Each iteration MUST produce a full video for comparison; if 3 iterations show no improvement, change approach |
| Over-optimization for one scene type | Low | Medium | Test with at least 2 different scene types during tuning |
| Quality framework too Wan2.2-specific | Low | High | Framework MUST use model-agnostic quality criteria; Wan2.2-specific parameters are data, not structure |
