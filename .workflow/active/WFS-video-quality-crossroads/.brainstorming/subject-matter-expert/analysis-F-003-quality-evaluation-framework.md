# F-003: Quality Evaluation Framework

**Priority**: High
**Owner**: Subject Matter Expert (with Product Manager and System Architect)
**Goal**: Establish a video quality evaluation system that is model-agnostic and reusable across future workflow/model switches

---

## 1. Why a Quality Framework Is Needed

Without a structured evaluation framework:
- Parameter tuning is subjective and inconsistent ("looks better" vs "looks worse")
- Progress cannot be measured across experiments
- There is no way to determine if a model change improved or degraded quality
- Different evaluators (developer now, team later) will apply different standards

The framework MUST be:
- **Model-agnostic**: Works for Wan2.2, HunyuanVideo, CogVideoX, or any future model
- **Multi-level**: Covers both single-clip quality and multi-clip consistency
- **Repeatable**: Same video always gets the same score
- **Practical**: Can be applied quickly during iteration (not a 30-minute evaluation per clip)

---

## 2. Quality Dimensions

### Dimension 1: Visual Fidelity (Single-Clip)
| Criterion | Description | Score Range |
|-----------|-------------|-------------|
| No morphing | Faces and bodies do not distort within the clip | 1-5 |
| Sharpness | Image is not blurry; details are visible | 1-5 |
| Color consistency | No abrupt color shifts within the clip | 1-5 |
| Motion coherence | Movement is natural, not jittery or frozen | 1-5 |
| Prompt adherence | Generated content matches the prompt | 1-5 |
| Artifact absence | No extra limbs, double heads, watermark-like patterns | 1-5 |

### Dimension 2: Character Consistency (Cross-Clip)
| Criterion | Description | Score Range |
|-----------|-------------|-------------|
| Face consistency | Same face across all clips | 1-5 |
| Outfit consistency | Same clothing appearance across clips | 1-5 |
| Body consistency | Same body shape/proportions across clips | 1-5 |
| Skin tone consistency | Same skin tone/color across clips | 1-5 |

### Dimension 3: Scene Consistency (Cross-Clip)
| Criterion | Description | Score Range |
|-----------|-------------|-------------|
| Background continuity | Background matches between adjacent clips | 1-5 |
| Lighting continuity | Lighting direction/intensity is consistent | 1-5 |
| Temporal flow | No jarring transitions or position jumps | 1-5 |

### Scoring Guide
- **1**: Severe problem (e.g., face completely different, obvious morphing)
- **2**: Noticeable problem (e.g., outfit color shifted, slight morphing)
- **3**: Acceptable with minor issues (e.g., subtle lighting change)
- **4**: Good consistency (e.g., only expert would notice issues)
- **5**: Perfect (e.g., indistinguishable from a real video)

---

## 3. Evaluation Protocol

### Level 1: Quick Check (Per Experiment)
- Watch the generated clip once at full speed
- Score only **Visual Fidelity** (6 criteria, 30 seconds)
- If average < 3.0: reject configuration, do not proceed
- If average >= 3.5: candidate for Level 2

### Level 2: Detailed Evaluation (Per Configuration)
- Watch clip frame-by-frame at key points (start, 25%, 50%, 75%, end)
- Score **Visual Fidelity** in detail
- Generate 3-clip chain and score **Character Consistency** and **Scene Consistency**
- Total evaluation time: ~5 minutes per configuration

### Level 3: Full Video Evaluation (Pre-Release)
- Generate complete video (all clips)
- Watch full stitched video twice
- Score all dimensions
- Check for temporal artifacts at stitch points
- Get second opinion if possible
- Total evaluation time: ~15 minutes

---

## 4. Automation Opportunities

### Currently Manual, Future Automated
| Criterion | Manual Now | Automation Path |
|-----------|-----------|-----------------|
| Face consistency | Watch and compare | Face similarity model (ArcFace) |
| Sharpness | Visual check | Laplacian variance on frames |
| Color consistency | Visual check | Histogram comparison between frames |
| Motion coherence | Visual check | Optical flow consistency analysis |
| Artifact detection | Visual check | Anomaly detection on frame differences |

### Recommended Automation Roadmap
1. **Immediate**: Manual scoring only (quick to implement, sufficient for current iteration)
2. **Short-term**: Add frame extraction and basic metrics (sharpness, color histogram) to pipeline output
3. **Medium-term**: Integrate face similarity scoring (ArcFace) for character consistency
4. **Long-term**: Full automated quality scoring pipeline

### Important Constraint
The project MUST NOT delay quality tuning waiting for automated metrics. Manual evaluation is sufficient for the current phase. Automation is a nice-to-have for future scaling.

---

## 5. Quality Gate Definition

### Minimum Viable Quality (MVQ)
A configuration meets MVQ when:
- Visual Fidelity average >= 3.5 (no dimension below 3)
- Character Consistency average >= 3.0 (no dimension below 2)
- Scene Consistency average >= 3.0 (no dimension below 2)

### Publishable Quality (PQ)
A configuration meets PQ when:
- Visual Fidelity average >= 4.0 (no dimension below 3)
- Character Consistency average >= 4.0 (no dimension below 3)
- Scene Consistency average >= 3.5 (no dimension below 3)

### Quality Gate Implementation
The pipeline SHOULD log quality scores alongside each run. When a configuration meets MVQ, it can be used as the baseline for further optimization. When it meets PQ, it is ready for production use.

---

## 6. Model Alternatives: If Wan2.2 Cannot Reach PQ

### Alternative Models Assessment

| Model | Architecture | I2V Support | Quality Ceiling | Character Consistency | VRAM Required | ComfyUI Support |
|-------|-------------|-------------|----------------|----------------------|---------------|-----------------|
| **HunyuanVideo** | DiT | Yes (I2V variant) | Very High | Good (native face ref) | 24-40GB | Yes (community nodes) |
| **CogVideoX** | DiT (3D RoPE) | Yes (I2V variant) | High | Moderate | 20-36GB | Yes (official nodes) |
| **Stable Video Diffusion** | UNet | Yes (native) | Medium | Low | 12-16GB | Yes (native) |
| **AnimateDiff** | UNet + Motion | Yes (with ControlNet) | Medium-High | Moderate | 16-24GB | Yes (mature) |

### Switching Decision Criteria
The project SHOULD consider switching models if:
1. Wan2.2 with optimal parameters (40 steps, CFG 5.0) fails to reach MVQ after 3+ tuning iterations
2. Character consistency remains below 3.0 even with IPAdapter
3. A specific quality dimension cannot be improved above 2.5 regardless of parameter changes

### Recommended Switch Order
1. **HunyuanVideo** -- highest quality ceiling, strong character consistency features, active community
2. **CogVideoX** -- good quality, official ComfyUI support, strong prompt adherence
3. **AnimateDiff + SDXL** -- if IPAdapter + character consistency is the primary concern (most mature ecosystem)

### Migration Path
When switching models:
- Quality evaluation framework transfers directly (same dimensions, same scoring)
- Parameter experiment schema transfers (same fields, different model-specific values)
- Workflow template is replaced entirely (different node structure)
- Binding schema adapts to new template (different paths, same logical fields)
- Pipeline code (run/resume/manifest) remains unchanged -- it is model-agnostic by design

---

## 7. Quality Benchmark Record

### Baseline Measurement (Before Any Changes)
When the first parameter experiment runs, record:

```yaml
quality_benchmark:
  timestamp: 2026-05-02
  model: wan2.2_i2v_high_noise_14B_fp8_scaled
  configuration: current (8 steps, CFG 1.0, 4-step LoRA)
  visual_fidelity:
    no_morphing: 1  # severe morphing expected
    sharpness: 2
    color_consistency: 2
    motion_coherence: 2
    prompt_adherence: 1  # no guidance = no adherence
    artifact_absence: 1
    average: 1.5
  character_consistency:
    face: N/A  # no IPAdapter
    outfit: N/A
    body: N/A
    skin_tone: N/A
    average: N/A
  scene_consistency:
    background: 2
    lighting: 2
    temporal_flow: 1
    average: 1.7
  notes: "Expected to be very low quality due to distilled LoRA + no guidance"
```

This baseline MUST be established BEFORE making any parameter changes, so progress can be measured quantitatively.
