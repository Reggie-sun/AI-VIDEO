# F-001: Wan2.2 Quality Baseline

**Priority**: High
**Owner**: Subject Matter Expert
**Goal**: Establish single-clip quality baseline using community-validated parameter configurations

---

## 1. Official Wan2.1/Wan2.2 I2V Reference Parameters

The Wan2.1 official repository provides these I2V inference settings:

| Parameter | Official I2V-14B Value | Notes |
|-----------|----------------------|-------|
| steps | 40 | I2V uses 40; T2V uses 50 |
| guidance_scale (CFG) | 5.0 | Critical for prompt adherence |
| flow_shift | 3.0 (480P) / 5.0 (720P) | Resolution-dependent |
| scheduler | UniPCMultistepScheduler | With flow_prediction, use_flow_sigmas=True |
| resolution | 480x832 (480P) / 720x1280 (720P) | Max area; aspect follows input image |
| num_frames | 81 | ~5 seconds at 16fps |
| negative_prompt | (see section 4) | Official list provided |

### Key Insight: Wan2.2 vs Wan2.1
Wan2.2 is the successor model. The high_noise variant in the current workflow (`wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`) is the full 14B model with fp8 quantization. The "high_noise" designation refers to the noise schedule variant (different from low_noise), not a quality degradation. The model itself is capable of high-quality output when given proper parameters.

---

## 2. The 4-Step LoRA: Root Cause Analysis

### What It Is
`wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors` is a **knowledge-distillation LoRA** that compresses 40 steps of denoising into 4 effective steps. It is designed for rapid iteration/preview, not production quality.

### Why It Degrades Quality
- Distilled models lose fine-grained detail recovery in early denoising stages
- With only 8 steps (current setting, even more than the LoRA's 4-step design), the model has insufficient iterations to refine details
- Morphing and semantic drift occur because the model skips intermediate refinement stages that would normally correct distortions
- The LoRA was trained for 4-step inference; running 8 steps with it creates a mismatch between the LoRA's expected noise schedule and the actual schedule

### Recommended Action
The project MUST:
1. Set `lora_0` to "none" in node 565 (WanVideoLoraSelectMulti)
2. Increase steps from 8 to 30 (minimum viable) or 40 (reference quality)
3. Increase CFG from 1.0 to 5.0
4. Update scheduler from "euler" to "uniPC" (or keep euler if uniPC is not available in the Kijai wrapper)

---

## 3. Parameter Optimization Priority Order

Execute these changes in order, testing each before moving to the next:

### Phase 1: Critical Fixes (Expected: 60%+ quality improvement)
1. **Remove 4-step LoRA** -- set all lora slots to "none"
2. **Increase steps to 30** -- start with 30 (75% of reference), increase to 40 if quality still insufficient
3. **Set CFG to 5.0** -- this enables prompt-conditioned generation
4. **Add negative prompt** -- use official list (section 4)

### Phase 2: Fine-Tuning (Expected: 15-25% additional improvement)
5. **Test schedulers**: euler vs uniPC vs dpmpp_2m -- compare at same step count
6. **Tune shift**: 3.0 is correct for 480P; test 3.5 and 4.0 for slightly different motion dynamics
7. **Tune noise_aug_strength**: 0.03 is standard; test 0.05 and 0.06 for more/less init image adherence
8. **Tune start_latent_strength / end_latent_strength**: both at 1.0 currently; reducing end_latent_strength to 0.8-0.9 may reduce flickering at clip boundaries

### Phase 3: Advanced Optimization (Expected: 5-15% additional improvement)
9. **Resolution upgrade**: test 720P (shift=5.0) if VRAM allows
10. **Prompt engineering**: structured prompts with detailed motion descriptions
11. **Character LoRA**: if a specific character style is needed, a dedicated character LoRA MAY be added

---

## 4. Negative Prompt

The official Wan2.1 repository provides this negative prompt for I2V:

```
Bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, three legs, many people in the background, walking backwards
```

### Usage Notes
- This negative prompt MUST be set in node 548 (WanVideoTextEncode) `negative_prompt` field
- Currently the field is empty (`""`), which means the model has no negative guidance
- For character-focused content, ADD: `face morphing, outfit changing, body shape changing, inconsistent appearance`
- For motion-focused content, ADD: `frozen, jittering, reversing motion, unnatural movement`

---

## 5. Prompt Engineering for I2V

### Structure Pattern
Effective I2V prompts follow this structure:

```
[Subject description], [Action/Motion], [Camera movement], [Environment/Scene], [Style qualifiers]
```

### Examples

**Current** (minimal):
```
a person walks into frame and looks toward the camera
```

**Improved** (detailed):
```
A young woman in a dark blue jacket walks slowly into the frame from the left, her hair gently swaying, she turns her head and looks directly at the camera with a calm expression, urban street at dusk, warm streetlights, cinematic lighting, shallow depth of field
```

### Motion Description Guidelines
- Be specific about direction: "walks from left to right" not "walks"
- Describe speed: "slowly", "quickly", "gradually"
- Include body parts: "her hair swaying", "hands at her sides"
- Camera movement: "static camera", "slow pan right", "subtle zoom in"
- Avoid conflicting descriptions: do not describe both "walking forward" and "turning around" in the same clip

### Style Prompt
The current `style_prompt: "cinematic, consistent character, stable outfit"` is a good start but SHOULD be expanded:
```
cinematic, consistent character appearance, stable outfit throughout, natural motion, coherent lighting, professional color grading, 35mm film look, no morphing
```

### Negative Prompt Integration
The style_prompt SHOULD be appended to the positive prompt, not used as a separate input (unless the workflow has a dedicated style field). The current binding structure has `positive_prompt` mapped to node 549 and `negative_prompt` mapped to node 548.

---

## 6. Recommended Starting Parameters

### Configuration A: "Safe Baseline" (test first)
```yaml
steps: 30
cfg: 5.0
shift: 3.0
scheduler: euler
lora: none
negative_prompt: "Bright tones, overexposed, static, blurred details, subtitles, worst quality, low quality, JPEG compression residue, ugly, deformed, disfigured, misshapen limbs, fused fingers, still picture, face morphing, outfit changing"
noise_aug_strength: 0.03
start_latent_strength: 1.0
end_latent_strength: 1.0
resolution: 832x480
num_frames: 81
seed: 42  # fixed for A/B testing
```

### Configuration B: "Full Reference" (if A is good)
```yaml
steps: 40
cfg: 5.0
shift: 3.0
scheduler: uniPC
lora: none
negative_prompt: (same as A)
noise_aug_strength: 0.03
start_latent_strength: 1.0
end_latent_strength: 1.0
resolution: 832x480
num_frames: 81
seed: 42
```

### Configuration C: "720P Upgrade" (if VRAM allows)
```yaml
steps: 40
cfg: 5.0
shift: 5.0
scheduler: uniPC
lora: none
negative_prompt: (same as A)
noise_aug_strength: 0.03
start_latent_strength: 1.0
end_latent_strength: 1.0
resolution: 1280x720
num_frames: 81
seed: 42
```

### Expected Timeline
- Configuration A test: ~5 minutes per clip on RTX 5090
- Compare A vs current: immediate visual improvement expected
- If A is good, proceed to B for final quality ceiling test
- If A is still insufficient, proceed to C (720P) or consider model alternatives

---

## 7. Quality Diagnosis: Symptom-Cause-Fix Map

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Face morphing within a clip | Low steps + no CFG + no negative prompt | Steps 30+, CFG 5.0, negative prompt |
| Flickering/jittering | Low steps, insufficient denoising refinement | Steps 30+, try different scheduler |
| Outfit/shape changing | No guidance (CFG=1.0), no negative prompt | CFG 5.0, add "outfit changing" to negative |
| Blurry/low detail | 4-step distilled LoRA | Remove LoRA, increase steps |
| Static/no motion | Prompt too vague, no motion description | Detailed motion prompts |
| Color shifts | No negative prompt, weak guidance | Add negative prompt, CFG 5.0 |
| Cross-clip inconsistency | No IPAdapter, no character reference | See F-002: IPAdapter integration |
