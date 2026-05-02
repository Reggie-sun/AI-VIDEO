# F-001: Wan2.2 Quality Baseline — Architecture Analysis

## Problem Definition

Current Wan2.2 I2V output quality is poor. The workflow template `wan22_i2v_api.json` uses default/minimal parameters that are not optimized for visual quality. The pipeline architecture itself works; the problem is in the parameter space.

## Current Parameter Inventory

From the actual rendered workflow (`first-real-run/shot_001/attempt_1/workflow.json`):

| Parameter | Current Value | Node ID | Concern |
|-----------|--------------|---------|---------|
| steps | 8 | 562 (WanVideoSampler) | Too few for quality; community uses 20-50 |
| cfg | 1.0 | 562 | Very low; typical I2V range 1.0-7.0 |
| shift | 3.0 | 562 | Needs tuning per step count |
| scheduler | euler | 562 | May not be optimal; uni_pc, dpm++ alternatives |
| riflex_freq_index | 0 | 562 | Unknown impact |
| noise_aug_strength | 0.03 | 514 (I2VEncode) | Low; affects how much init image is preserved |
| start_latent_strength | 1 | 514 | Maximum; locks to init image strongly |
| end_latent_strength | 1 | 514 | Maximum; may reduce motion |
| LoRA | lightx2v_4steps_lora_v1_high_noise | 565 | Paired with 4-step distilled model; may conflict with higher step counts |
| model | 14B fp8_scaled | 559 | Quantized; quality vs VRAM tradeoff |
| num_frames | 93 | 514 | 93 frames at 16fps = ~5.8s; reasonable |
| max_side_length | 576 | 546 (QuantizeAndCrop) | Affects init image resolution |
| negative_prompt | (empty) | 548 | No negative guidance |
| style_prompt | "cinematic, consistent character, stable outfit" | defaults | Reasonable but could be more specific |

## Architecture Changes Required

### 1. Parameter Override Path (param_overrides in binding)

The binding MUST gain `param_overrides` entries so the experiment tracker can modify sampler parameters without editing the template JSON:

```yaml
# Addition to wan22_i2v_binding.yaml
param_overrides:
  - name: steps
    path: ["562", "inputs", "steps"]
  - name: cfg
    path: ["562", "inputs", "cfg"]
  - name: shift
    path: ["562", "inputs", "shift"]
  - name: scheduler
    path: ["562", "inputs", "scheduler"]
  - name: noise_aug_strength
    path: ["514", "inputs", "noise_aug_strength"]
  - name: start_latent_strength
    path: ["514", "inputs", "start_latent_strength"]
  - name: end_latent_strength
    path: ["514", "inputs", "end_latent_strength"]
```

### 2. LoRA Compatibility Check

**Critical**: The current LoRA `wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise` is a distilled LoRA designed for 4-step inference. Using it with 20+ steps may produce degraded output.

**Architecture decision**: The param_overrides mechanism SHOULD also support LoRA parameter changes:

```yaml
  - name: lora_0
    path: ["565", "inputs", "lora_0"]
  - name: strength_0
    path: ["565", "inputs", "strength_0"]
```

When increasing steps beyond 4-8, the LoRA SHOULD be switched to the standard (non-distilled) version or disabled entirely.

### 3. Negative Prompt Population

Current negative prompt is empty. The binding already supports `negative_prompt` path. The `wan22.project.yaml` defaults SHOULD include meaningful negative prompts:

```yaml
defaults:
  negative_prompt: "blur, distorted face, extra limbs, low quality, blurry, watermark, text"
```

### 4. Prompt Engineering Improvements

The `compose_prompt` function in `workflow_renderer.py` already supports: `style_prompt + character_descriptions + shot_prompt + continuity_note`. This is architecturally sound.

**Recommendation**: The quality baseline SHOULD focus on:
- More specific style prompts (lighting, camera angle, film stock)
- Better continuity notes (not just "same outfit" but specific visual anchors)
- Shot-level negative prompts for specific failure modes

## Model Changes Required

| Model | Change | Reason |
|-------|--------|--------|
| `WorkflowBinding` | Add `param_overrides: list[ParamOverrideBinding]` | Enable parameter injection through binding |
| `ParamOverrideBinding` | New model: `name: str, path: JsonPath` | Map human names to JSON paths |
| `DefaultsConfig` | No change needed | Negative prompt already exists |
| `ShotSpec` | No change needed | `metadata` field can carry overrides |

## Pipeline Changes Required

| Module | Change | Scope |
|--------|--------|-------|
| `workflow_renderer.py` | Accept and apply `param_overrides` | Small, additive |
| `pipeline.py` | Pass `param_overrides` from config/experiment to renderer | Small, additive |
| `models.py` | Add `ParamOverrideBinding` | Small, additive |
| `cli.py` | Optional `--params` flag for ad-hoc overrides | Small, additive |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Distilled LoRA incompatible with high steps | High | Quality regression | Switch LoRA or disable when steps > 8 |
| fp8 quantization limits quality ceiling | Medium | Cannot reach commercial quality | Test bf16 model on 5090 (32GB may be sufficient) |
| Community parameters not transferable to this exact setup | Medium | Wasted effort | Test one parameter at a time, not wholesale copy |
| VRAM overflow with higher steps or bf16 model | Low-Medium | OOM crash | Block swap already at 15; can increase or reduce resolution |

## Success Criteria for F-001

1. At least one parameter set produces a single 5-second clip that a human reviewer rates as "visually acceptable" (no face distortion, coherent motion, no artifacts)
2. The parameter set is recorded in a reproducible format (binding + config)
3. The quality improvement is measurable (even if the metric is manual review at this stage)
