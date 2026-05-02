# F-002: IPAdapter Consistency

**Priority**: High
**Owner**: Subject Matter Expert
**Goal**: Integrate IPAdapter into Wan2.2 I2V workflow for cross-clip character consistency

---

## 1. Why IPAdapter Is Needed

### The Problem
Last-frame chaining alone cannot maintain character appearance across clips because:
- The I2V model only sees the last frame as an init image, not as a "this is what the character looks like" reference
- Small appearance drift accumulates across clips (skin tone shifts, outfit variations, facial feature changes)
- Lighting and angle changes between clips cause the model to interpret the character differently

### What IPAdapter Adds
IPAdapter provides **explicit reference image conditioning** -- the model receives a separate signal saying "this is what the character looks like" independent of the init image. This creates a dual conditioning path:
- **Init image** (last frame): provides scene context and motion continuity
- **IPAdapter reference**: provides character identity and appearance anchor

### Combined Strategy
The guidance specification confirmed: IPAdapter + last-frame chaining combined. These two mechanisms address different aspects of consistency and SHOULD NOT conflict when configured properly:
- IPAdapter handles **appearance** (face, body, outfit)
- Last-frame chaining handles **scene** (background, lighting, pose continuity)

---

## 2. IPAdapter Integration Options for Wan2.2

### Option A: IPAdapter-Plus (Recommended)
The ComfyUI IPAdapter-Plus by cubiq is the most mature implementation.

**Required nodes:**
1. `IPAdapter Unified Loader` -- loads the IPAdapter model
2. `IPAdapter Advanced` -- applies the reference image with weight control
3. `CLIP Vision Loader` -- loads CLIP vision model for encoding the reference image

**Workflow changes needed:**
1. Add `Load CLIP Vision Model` node (loads `clip-vision/vit-h.safetensors` or similar)
2. Add `IPAdapter Model Loader` node (loads IPAdapter model compatible with Wan2.2)
3. Add `IPAdapter Advanced` node (receives model + reference image + weight)
4. Connect IPAdapter output to the Wan2.2 model pipeline (cross-attention injection)

**Critical concern**: IPAdapter-Plus was originally designed for Stable Diffusion architectures. Wan2.2 uses a different architecture (DiT-based). The IPAdapter model MUST be compatible with the Wan2.2 architecture. As of 2026-05, community IPAdapter models for Wan2.2 are still emerging.

### Option B: Wan2-Native Reference Attention
Some Wan2.2 implementations support a native "reference attention" mechanism where:
- The reference image is encoded by the VAE
- The reference latents are injected into the diffusion model's self-attention layers
- No separate IPAdapter model is needed

**Advantage**: Architecture-native, no compatibility issues
**Disadvantage**: Less control over weight/strength, fewer community configurations

### Option C: FaceID + IPAdapter
For face-specific consistency (strongest face preservation):
1. Use `IPAdapter Unified Loader FaceID` node
2. Requires `insightface` library installation
3. Provides the strongest face identity preservation but may be over-constraining for full-body shots

### Recommendation
Start with **Option A** (IPAdapter-Plus) because it offers the most control and community support. If Wan2.2-specific IPAdapter models are not yet available, fall back to **Option B** (native reference attention). The project MUST verify IPAdapter compatibility with Wan2.2 before investing in workflow integration.

---

## 3. IPAdapter-Plus Technical Setup

### Required Models
| Model | Path | Source |
|-------|------|--------|
| CLIP Vision | `models/clip_vision/clip-vit-h-14-laion2b-s32b-b79k.safetensors` | HuggingFace |
| IPAdapter | `models/ipadapter/ip-adapter-plus_sd15.safetensors` (or Wan2-compatible version) | CivitAI / HuggingFace |

**NOTE**: The exact IPAdapter model for Wan2.2 DiT architecture MUST be verified. Standard SD1.5/SDXL IPAdapter models WILL NOT work with Wan2.2's architecture. Check:
- Kijai's ComfyUI-Wan2Wrapper for built-in reference/IPAdapter support
- ComfyUI community forums for Wan2.2-specific IPAdapter nodes
- If no Wan2.2-specific IPAdapter exists, use the Wan2-native reference image approach (Option B)

### Node Configuration in Workflow

**New nodes to add (if IPAdapter-Plus compatible):**

```json
{
  "ref_clip_vision": {
    "class_type": "CLIPVisionLoader",
    "inputs": {
      "clip_name": "clip-vit-h-14-laion2b-s32b-b79k.safetensors"
    }
  },
  "ref_image_load": {
    "class_type": "LoadImage",
    "inputs": {
      "image": "character_reference.png"
    }
  },
  "ipadapter_loader": {
    "class_type": "IPAdapterUnifiedLoader",
    "inputs": {
      "model": ["559", 0],
      "ipadapter_file": "ip-adapter-plus-wan2.safetensors",
      "clip_vision": ["ref_clip_vision", 0]
    }
  },
  "ipadapter_apply": {
    "class_type": "IPAdapterAdvanced",
    "inputs": {
      "model": ["ipadapter_loader", 0],
      "image": ["ref_image_load", 0],
      "weight": 0.7,
      "weight_type": "standard",
      "start_at": 0.0,
      "end_at": 1.0
    }
  }
}
```

### Binding Changes Required
The binding schema MUST be extended with new fields:

```yaml
# New binding fields for IPAdapter
character_reference_image:
  path: ["ref_image_load", "inputs", "image"]
ipadapter_weight:
  path: ["ipadapter_apply", "inputs", "weight"]
ipadapter_start_at:
  path: ["ipadapter_apply", "inputs", "start_at"]
ipadapter_end_at:
  path: ["ipadapter_apply", "inputs", "end_at"]
```

### Pipeline Integration
The characters section in the project config (`wan22.project.yaml`) currently is `characters: []`. This MUST be extended to:

```yaml
characters:
  - id: char_001
    name: "protagonist"
    reference_image: "assets/character_reference.png"
    ipadapter_weight: 0.7
```

---

## 4. IPAdapter Weight Tuning

### Weight Ranges and Effects

| Weight | Effect | Use Case |
|--------|--------|----------|
| 0.3-0.4 | Subtle style/color influence | Style transfer, not character identity |
| 0.5-0.6 | Moderate character influence | Loosely maintain character look |
| **0.6-0.8** | **Strong character consistency** | **Recommended starting range** |
| 0.8-1.0 | Very strong, may over-constrain | Exact face/body replication |
| > 1.0 | Likely artifacts | Avoid |

### Recommendation
Start at **weight=0.7** and adjust based on results:
- If character still drifts: increase to 0.8
- If generation feels "stuck" or motion is constrained: decrease to 0.6
- If face is good but body drifts: consider using start_at=0.0, end_at=0.5 (apply IPAdapter only in early denoising)

### Interaction with CFG
- Higher IPAdapter weight + higher CFG can amplify character consistency
- If CFG=5.0 and weight=0.7 feels over-constrained, try CFG=4.0 or weight=0.6
- The project SHOULD test 3-4 weight/CFG combinations to find the sweet spot

---

## 5. Preventing IPAdapter/Chaining Conflicts

### Potential Conflicts
1. **Double conditioning on appearance**: Last frame from chaining + IPAdapter reference both influence appearance. If they contradict (e.g., different lighting), the model may produce artifacts.
2. **Over-constrained motion**: IPAdapter at full strength (end_at=1.0) can lock the character pose, preventing natural motion.

### Mitigation Strategy
- **Use IPAdapter for face/identity only** (if possible): Some IPAdapter implementations allow face-only mode via FaceID models
- **Reduce IPAdapter influence in late denoising**: Set `end_at=0.6` or `end_at=0.7` so the model has freedom in final refinement
- **Ensure reference image and last frame are visually compatible**: The reference image SHOULD match the general scene (same lighting conditions, similar angle)
- **Phase the testing**:
  1. Test IPAdapter alone (no chaining) -- verify character consistency
  2. Test chaining alone (no IPAdapter) -- verify scene continuity
  3. Test both combined -- verify they don't conflict
  4. Adjust weights until both work harmoniously

---

## 6. Implementation Phases

### Phase 1: Verify Compatibility (1-2 hours)
- Check if Kijai's ComfyUI-Wan2Wrapper supports IPAdapter or reference attention
- Check if Wan2.2-specific IPAdapter models exist on CivitAI/HuggingFace
- If neither exists, search for Wan2-native reference image conditioning methods

### Phase 2: Single-Clip IPAdapter Test (2-4 hours)
- Add IPAdapter/reference nodes to workflow template
- Generate single clip with and without IPAdapter
- Compare character consistency with same seed

### Phase 3: Multi-Clip Consistency Test (4-8 hours)
- Generate 3-clip chain with IPAdapter + last-frame chaining
- Evaluate cross-clip character consistency
- Tune weight, start_at, end_at parameters

### Phase 4: Binding and Config Integration (2-4 hours)
- Update binding schema with IPAdapter fields
- Update project config with character definitions
- Update pipeline code to pass character reference images
- Add tests for new binding fields

---

## 7. Fallback: If IPAdapter Is Not Available for Wan2.2

If no compatible IPAdapter implementation exists for Wan2.2:

1. **Wan2-native reference attention**: Some community workflows inject reference image latents into the diffusion model's attention layers. Search for "Wan2 reference image" workflows on ComfyUI community sites.

2. **Character LoRA**: Train or find a lightweight LoRA that captures the specific character appearance. This is less flexible than IPAdapter (requires retraining per character) but provides strong consistency.

3. **Enhanced prompt consistency**: Use extremely detailed, identical character descriptions in every clip's prompt. This is the weakest approach but requires no workflow changes.

4. **Post-processing face swap**: Use a face-swap tool (e.g., InsightFace swap) in post-processing to unify faces across clips. This is a band-aid, not a solution, but MAY be used as a temporary measure.
