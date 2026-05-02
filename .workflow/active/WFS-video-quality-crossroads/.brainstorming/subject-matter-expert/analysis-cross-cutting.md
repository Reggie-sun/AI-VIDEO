# Cross-Cutting Analysis: Wan2.2 I2V Quality Optimization

**Role**: Subject Matter Expert
**Scope**: Decisions, patterns, and constraints spanning F-001 through F-005

---

## 1. The 4-Step Distilled LoRA Problem

### Finding
The current workflow loads `wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors` with strength=1 and runs only 8 sampling steps. This is a **distilled acceleration LoRA** designed for rapid preview/iteration, not for production quality.

### Official Reference
The Wan2.1 official I2V inference uses:
- **40 steps** (I2V-14B), no distilled LoRA
- **guidance_scale = 5.0**
- **flow_shift = 3.0** (480P) or **5.0** (720P)
- **UniPCMultistepScheduler** with flow_prediction

### Quality Gap Estimate
Based on community reports and diffusion model behavior:
- 4-step distilled: ~30-40% of full quality ceiling
- 8-step with distilled LoRA: ~40-50% of full quality ceiling
- 20-step base model: ~80-85% of full quality ceiling
- 40-step base model: ~95-100% of full quality ceiling (reference)

### Action
The project MUST remove the 4-step LoRA and increase steps to at least 20 (minimum viable quality) or 40 (reference quality) as the very first experiment. This single change is expected to resolve the majority of morphing and semantic distortion issues.

### Speed Consideration
On RTX 5090 with 32GB VRAM, 40 steps at 832x480 with 14B fp8 model:
- Estimated: 3-8 minutes per clip (vs. current ~1-2 minutes with 8 steps)
- This is acceptable for "quality first" strategy

---

## 2. Parameter Impact Ranking

Parameters ranked by their impact on single-clip quality:

| Rank | Parameter | Current | Recommended | Impact Level | Notes |
|------|-----------|---------|-------------|-------------|-------|
| 1 | Steps + LoRA choice | 8 + 4-step LoRA | 30-40, no distill LoRA | **Critical** | Accounts for 50%+ of quality gap |
| 2 | CFG / guidance_scale | 1.0 | 5.0 | **Critical** | No guidance = no prompt adherence |
| 3 | Negative prompt | empty | (see F-001 section 4) | **High** | Prevents common artifacts |
| 4 | Scheduler | euler | UniPC or euler | Medium | UniPC slightly better at low steps |
| 5 | Prompt engineering | minimal | detailed + structured | High | See F-001 section 5 |
| 6 | IPAdapter weight | N/A | 0.6-0.8 | High (cross-clip) | See F-002 |
| 7 | noise_aug_strength | 0.03 | 0.03-0.06 | Low | Fine-tuning only |
| 8 | Seed | 100 | random per clip | Low | For variety; fix for A/B testing |
| 9 | shift | 3.0 | 3.0 (480P) | Already correct | Change to 5.0 if 720P |

---

## 3. Model-Workflow Compatibility Matrix

| Configuration | Steps | CFG | Shift | Scheduler | Quality | Speed | VRAM |
|---------------|-------|-----|-------|-----------|---------|-------|------|
| Current (distilled) | 8 | 1.0 | 3.0 | euler | Very Low | Fast | ~20GB |
| Recommended baseline | 30 | 5.0 | 3.0 | uniPC | Good | Moderate | ~24GB |
| Full reference | 40 | 5.0 | 3.0 | uniPC | Best | Slow | ~24GB |
| 720P target | 40 | 5.0 | 5.0 | uniPC | Best | Slower | ~28GB |

RTX 5090 with 32GB VRAM SHOULD be able to run 720P at 40 steps with block swap enabled (current setting: 15 blocks swapped). If OOM occurs, enable tiled VAE.

---

## 4. Reproducibility Requirements for Parameter Experiments

Every parameter experiment MUST record:

```yaml
experiment:
  id: EXP-001
  timestamp: 2026-05-02T10:00:00Z
  model: wan2.2_i2v_high_noise_14B_fp8_scaled
  lora: none
  steps: 30
  cfg: 5.0
  shift: 3.0
  scheduler: uniPC
  resolution: 832x480
  num_frames: 93
  seed: 42
  negative_prompt: "..."
  prompt: "..."
  ipadapter_enabled: false
  workflow_hash: <sha256 of workflow JSON>
  output_path: runs/<run_id>/shot_001/output.mp4
  quality_notes: "No face morphing, stable background, motion coherent"
  quality_score: 7/10  # subjective baseline
```

This structure MUST be model-agnostic -- the same schema works for HunyuanVideo, CogVideoX, or any future model. Only the `model`, `lora`, and `workflow_hash` fields change.

---

## 5. Future Model Switching: Transferability Assessment

When the project switches models, these learnings transfer:

| Learning | Transferable? | Notes |
|----------|-------------|-------|
| Steps impact on quality | Yes | All diffusion models need 30+ steps for good quality |
| CFG/guidance_scale concept | Yes | All models benefit from CFG > 1.0 |
| Negative prompt patterns | Partially | Model-specific; needs re-tuning |
| IPAdapter for consistency | Partially | Depends on model architecture support |
| Prompt engineering patterns | Partially | General structure transfers; specifics differ |
| Shift parameter | No | Wan-specific (flow matching shift) |
| Quality evaluation criteria | Yes | Frame consistency, artifact absence, motion coherence |

---

## 6. Experiment Framework Design Principles

The parameter experiment tracker (F-004) and evaluation loop (F-005) SHOULD follow these principles:

1. **One variable at a time** -- change only steps, then only CFG, then only scheduler, etc.
2. **Fixed seed per comparison** -- use seed=42 for all A/B tests
3. **Same init image** -- use a single reference image for all single-clip experiments
4. **Record everything** -- even failed experiments teach something
5. **Compare to baseline** -- always include the "recommended baseline" (30 steps, CFG 5.0, shift 3.0) as reference
6. **Document quality subjectively** -- use 1-10 scale with written notes until automated metrics are available
7. **Full-video evaluation** -- after single-clip parameters are locked, run a 3-clip chain with the same parameters and evaluate cross-clip consistency
