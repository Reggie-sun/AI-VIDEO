# Subject Matter Expert Analysis: Wan2.2 I2V Quality Optimization

**Role**: Subject Matter Expert (AI Video Generation)
**Session**: WFS-video-quality-crossroads
**Date**: 2026-05-02

---

## Executive Summary

The current pipeline produces unacceptable video quality because its workflow parameters are set to distilled/accelerated defaults rather than quality-optimized values. The most critical finding is that the workflow runs **8 steps with a 4-step distilled LoRA** (lightx2v) while the official Wan2.1 I2V reference uses **40 steps with the base model** -- this alone accounts for the majority of quality degradation. Additionally, CFG is set to 1.0 (effectively no guidance), negative prompt is empty, and no character consistency mechanism (IPAdapter) is configured. The fix path is clear: switch to full-step sampling with proper CFG/shift/negative-prompt values, then add IPAdapter for cross-clip consistency. If Wan2.2 at full quality still falls short, HunyuanVideo and CogVideoX are viable alternatives.

## Feature Point Index

| Feature | File | Priority |
|---------|------|----------|
| F-001: wan22-quality-baseline | @analysis-F-001-wan22-quality-baseline.md | High |
| F-002: ipadapter-consistency | @analysis-F-002-ipadapter-consistency.md | High |
| F-003: quality-evaluation-framework | @analysis-F-003-quality-evaluation-framework.md | High |
| F-004: param-experiment-tracker | @analysis-cross-cutting.md (shared) | Medium |
| F-005: full-video-evaluation-loop | @analysis-cross-cutting.md (shared) | Medium |

## Cross-Cutting Summary

Key findings that span all features are documented in @analysis-cross-cutting.md:

- **The 4-step LoRA is the primary quality killer** -- it trades 80%+ quality loss for 5x speed. Remove it first.
- **CFG=1.0 means zero classifier-free guidance** -- the model generates without any prompt steering. Official I2V uses guidance_scale=5.0.
- **shift=3.0 is correct for 480P**, but the workflow should use 5.0 if targeting 720P.
- **IPAdapter for video models is not yet standardized** -- the most reliable path is using IPAdapter-Plus with CLIP vision encoding, then injecting into the Wan2 model's cross-attention layers. This requires custom node support.
- **All parameter experiments MUST record model version, workflow hash, and seed** for reproducibility across future model/workflow switches.

## Current Workflow Diagnosis (Quick Reference)

| Parameter | Current Value | Official/Community Value | Impact |
|-----------|--------------|--------------------------|--------|
| steps | 8 | 30-40 | **Critical** |
| LoRA | lightx2v 4-step | None (base model) | **Critical** |
| CFG | 1.0 | 5.0 | **Critical** |
| shift | 3.0 | 3.0 (480P) / 5.0 (720P) | OK for 480P |
| scheduler | euler | UniPC / euler | Medium |
| negative_prompt | "" | (see prompt section) | **High** |
| noise_aug_strength | 0.03 | 0.03 | OK |
| IPAdapter | None | Required for consistency | **High** (for cross-clip) |
