# F-002: IPAdapter Consistency — Architecture Analysis

## Problem Definition

Cross-clip character consistency is currently absent. The only mechanism is last-frame chaining, which provides visual continuity but not identity consistency. IPAdapter can inject character appearance from reference images, providing a stronger identity anchor. The architecture challenge is integrating IPAdapter into the workflow without breaking the existing pipeline.

## Current Architecture State

### What Already Works
- `CharacterProfile` model has `ipadapter: IPAdapterConfig` with `weight`, `start_at`, `end_at`
- `CharacterRefBinding` model maps `character -> image_path + weight_path` in workflow JSON
- `workflow_renderer.py` `_set_path` logic already applies character ref images and weights
- `_prepare_character_images` in `pipeline.py` uploads reference images via ComfyClient
- `example_i2v_binding.yaml` demonstrates the full character_ref pattern with `hero` character

### What Is Missing
- The `wan22_i2v_api.json` template has NO IPAdapter nodes
- The `wan22_i2v_binding.yaml` has `character_refs: []`
- The `wan22.project.yaml` has `characters: []`
- No IPAdapter model loading node exists in the current workflow

## Required Workflow Template Changes

The IPAdapter workflow MUST include these additional nodes compared to the current template:

### New Nodes Required

| Node Type | Purpose | Key Inputs |
|-----------|---------|------------|
| IPAdapterModelLoader | Load IPAdapter model | model_name, provider |
| LoadImage (for reference) | Load character reference image | image |
| IPAdapterAdvanced | Apply IPAdapter attention | model, image, weight, start_at, end_at |

### Workflow Data Flow Change

```
Current:
  WanVideoModelLoader -> WanVideoSampler -> WanVideoDecode

With IPAdapter:
  WanVideoModelLoader -> IPAdapterModelLoader -> IPAdapterAdvanced -> WanVideoSampler -> WanVideoDecode
                            |                        ^
                      LoadImage (ref)          weight, start_at, end_at
```

The IPAdapter is applied BETWEEN model loading and sampling. It modifies the model's attention layers to incorporate reference image features.

### Concrete Node Addition Plan

```json
{
  "600": {
    "class_type": "IPAdapterModelLoader",
    "inputs": {
      "model_name": "ip-adapter-plus_sdxl_vit-h.bin",
      "provider": "CUDA"
    },
    "_meta": {"title": "IPAdapter Model"}
  },
  "601": {
    "class_type": "LoadImage",
    "inputs": {
      "image": "hero_ref.png"
    },
    "_meta": {"title": "Character Reference Image"}
  },
  "602": {
    "class_type": "IPAdapterAdvanced",
    "inputs": {
      "model": ["559", 0],
      "ipadapter": ["600", 0],
      "image": ["601", 0],
      "weight": 0.8,
      "start_at": 0.0,
      "end_at": 1.0,
      "weight_type": "standard"
    },
    "_meta": {"title": "IPAdapter Apply"}
  }
}
```

**Important**: The Wan2.2 model architecture is DiT-based, not UNet-based. IPAdapter compatibility with Wan2.2 MUST be verified before implementation. If standard IPAdapter does not support DiT architectures, an alternative approach such as `InstantID`, `PhotoMaker`, or Wan2.2-specific reference image conditioning may be required.

### Binding Changes

```yaml
# wan22_i2v_ipadapter_binding.yaml
positive_prompt:
  path: ["549", "inputs", "text"]
negative_prompt:
  path: ["548", "inputs", "negative_prompt"]
seed:
  path: ["561", "inputs", "value"]
init_image:
  path: ["521", "inputs", "image"]
output_prefix:
  path: ["30", "inputs", "filename_prefix"]
character_refs:
  - character: hero
    image_path: ["601", "inputs", "image"]
    weight_path: ["602", "inputs", "weight"]
clip_output:
  node: "30"
  kind: gifs
  extensions: [".mp4"]
  select: first
param_overrides:
  # ... sampler params as in F-001
```

### Project Config Changes

```yaml
# wan22.project.yaml (modified)
characters:
  - id: hero
    name: Hero
    description: same face, same outfit, same hairstyle
    reference_images:
      - refs/hero.png
    ipadapter:
      weight: 0.8
      start_at: 0.0
      end_at: 1.0
```

## Pipeline Code Changes

### `pipeline.py` — No Changes Required

The existing `_prepare_character_images` method already:
1. Iterates over `project.characters`
2. Uploads each character's first reference image
3. Returns `character_image_names` mapping

The `render_workflow` call already passes `character_image_names`. The existing code path works end-to-end when `characters` is not empty and `character_refs` in the binding is not empty.

**This is the strongest evidence that the architecture was designed for IPAdapter from the start.**

### `workflow_renderer.py` — Minor Enhancement

The `render_workflow` function already handles `character_refs` through this code path:

```python
for ref in binding.character_refs:
    image_name = character_image_names.get(ref.character)
    if image_name is not None:
        _set_path(workflow, ref.image_path, image_name, ...)
    if ref.weight_path is not None and ref.character in characters:
        _set_path(workflow, ref.weight_path,
                  characters[ref.character].ipadapter.weight, ...)
```

**Missing**: `start_at` and `end_at` from `IPAdapterConfig` are not applied. The binding would need additional path entries for these:

```yaml
character_refs:
  - character: hero
    image_path: ["601", "inputs", "image"]
    weight_path: ["602", "inputs", "weight"]
    start_at_path: ["602", "inputs", "start_at"]   # NEW
    end_at_path: ["602", "inputs", "end_at"]       # NEW
```

This requires extending `CharacterRefBinding` with optional `start_at_path` and `end_at_path` fields.

### `models.py` — Schema Extension

```python
class CharacterRefBinding(BaseModel):
    character: str
    image_path: JsonPath
    weight_path: JsonPath | None = None
    start_at_path: JsonPath | None = None   # NEW
    end_at_path: JsonPath | None = None     # NEW
```

## IPAdapter + Last-Frame Chaining Interaction

### How They Combine

| Mechanism | What It Controls | Failure Mode |
|-----------|-----------------|--------------|
| Last-frame chaining | Visual continuity (pose, scene, lighting) | Artifact accumulation |
| IPAdapter | Identity consistency (face, outfit, body) | Over-constraining (frozen appearance) |

### Potential Conflicts

1. **IPAdapter weight too high**: Character becomes rigid, no motion variation. The clip looks like a still image with motion blur.
2. **IPAdapter weight too low**: No identity benefit, same as chaining alone.
3. **Reference image vs last-frame mismatch**: If the reference image shows a different pose/scene than the last frame, IPAdapter and chaining pull in opposite directions.

### Recommended Tuning Strategy

- Start with IPAdapter weight 0.6-0.7 for character scenes
- Reduce `start_latent_strength` to 0.7-0.9 to give IPAdapter more room to influence
- Keep `end_latent_strength` at 1.0 to ensure final frames are clean
- Test with and without `start_at`/`end_at` scheduling (applying IPAdapter more strongly at the start of the clip)

## VRAM Impact

IPAdapter adds a small model (typically ~700MB) to GPU memory. On RTX 5090 (32GB), this SHOULD be fine alongside the existing fp8 14B model. However:

- If switching to bf16 model (~28GB for 14B), IPAdapter may cause OOM
- The existing block swap (15 blocks) provides headroom
- The `WanVideoBlockSwap` settings MAY need adjustment

## Success Criteria for F-002

1. A character defined in `project.yaml` with reference image produces consistent appearance across 3+ clips
2. IPAdapter weight is tunable through the binding without code changes
3. IPAdapter + last-frame chaining do not cause visual regressions compared to chaining alone
4. The `wan22_i2v_ipadapter_api.json` template passes `validate` with the new binding
