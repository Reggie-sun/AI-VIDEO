# F-002: IPAdapter Consistency — Product Manager Analysis

**Feature**: ipadapter-consistency
**Priority**: Critical
**PM Concern**: Cross-clip consistency is the harder problem -- and the one that makes or breaks "publishable."

---

## 1. Why Consistency Matters More Than Fidelity

### The Product Reality

A single clip with minor imperfections (slight flickering, occasional softness) is still watchable. A video where the character's face, hair, and outfit change between every 5-second clip is unwatchable -- regardless of how good each individual clip looks.

**Consistency is the difference between "nice clip" and "watchable video."**

### Current State

- Last-frame chaining exists but produces visual inconsistency (character appearance drifts)
- `character_refs` field exists in binding schema but is empty (`characters: []`)
- No IPAdapter nodes in the current Wan2.2 workflow template
- The manifest tracks `character_ref_hashes: {}` -- infrastructure exists, but unused

---

## 2. What "Consistency" Means Concretely

### Must-Be-Consistent Elements

| Element | Consistency Requirement | Current Failure Mode |
|---------|----------------------|---------------------|
| Face | Same person, recognizable, stable features | Face morphs, changes identity |
| Hair | Same style, color, length | Changes between clips |
| Outfit | Same clothing, same colors | Swaps or shifts |
| Body type | Same proportions | Distorts or changes |
| Skin tone | Same color, same lighting response | Shifts between clips |

### Nice-to-Be-Consistent Elements

| Element | Consistency Requirement | Acceptable Drift |
|---------|----------------------|-----------------|
| Background | Generally same environment | Slight parallax or angle change OK |
| Lighting | Generally same mood | Gradual shifts OK, hard jumps not |
| Camera angle | Follows narrative | Smooth transitions OK |

---

## 3. IPAdapter as the Consistency Mechanism

### Product Requirements for IPAdapter Integration

1. **Reference image support**: User MUST be able to specify character reference images in the project config
2. **Per-character configuration**: If multiple characters, each has their own reference and weight
3. **Configurable weight**: IPAdapter influence MUST be adjustable (too high = frozen; too low = no effect)
4. **Workflow compatibility**: IPAdapter nodes MUST integrate into the existing Wan2.2 I2V workflow template
5. **Binding schema update**: The binding file MUST expose IPAdapter-related fields (reference image, weight) for per-shot configuration

### IPAdapter + Last-Frame Chaining: Dual Strategy

| Mechanism | What It Controls | Limitation |
|-----------|-----------------|------------|
| IPAdapter | Character appearance (face, outfit, style) | Does not control motion or scene continuity |
| Last-frame chaining | Visual continuity between clips (motion, scene, lighting) | Does not control character identity |

**Both are needed.** IPAdapter without chaining produces consistent-looking but jarringly disconnected clips. Chaining without IPAdapter produces smooth but identity-drifting sequences.

### Product Rule

- IPAdapter MUST be configured for character consistency (primary mechanism)
- Last-frame chaining MUST be retained for visual continuity (secondary mechanism)
- The two mechanisms MUST NOT conflict (IPAdapter for appearance, chaining for motion)

---

## 4. Phased Integration Plan

### Phase 2a: IPAdapter Alone (1-2 sessions)

- Add IPAdapter nodes to Wan2.2 workflow template
- Update binding schema with `character_refs` and `ipadapter_weight` fields
- Run 3-clip test with IPAdapter only (no chaining)
- Evaluate: does character identity stabilize?

**Gate**: If IPAdapter alone does not improve consistency, investigate whether the IPAdapter model/version is compatible with Wan2.2

### Phase 2b: IPAdapter + Chaining (1-2 sessions)

- Combine IPAdapter reference images with last-frame chaining
- Tune IPAdapter weight to balance consistency vs. natural motion
- Run 3-clip test with both mechanisms
- Evaluate: does the full video show both consistency AND continuity?

**Gate**: Full video passes Q2 criteria for cross-clip consistency

### Phase 2c: Transition Polish (1 session)

- Evaluate clip boundaries specifically
- Adjust normalize/stitch parameters if boundaries are visible
- Fine-tune IPAdapter weight per-transition if needed

**Gate**: Full video passes Q2 criteria on all three pillars

---

## 5. Configuration Design (Product Perspective)

### What the User Needs to Configure

```yaml
# In project config
characters:
  - id: main_character
    reference_image: ./refs/main_character.png
    ipadapter_weight: 0.8   # Tunable; start high, reduce if too frozen
```

```yaml
# In binding file
character_refs:
  type: ipadapter
  nodes: [...]              # IPAdapter node IDs in workflow
  reference_image_path: [...]  # Path to reference image input
  weight_path: [...]        # IPAdapter weight input
```

### Configuration Principles

1. **Sensible defaults**: IPAdapter weight SHOULD default to 0.8 (strong influence) and be tuned down
2. **Per-character granularity**: Each character has independent reference and weight
3. **Shot-level override**: Individual shots MAY override character weight (e.g., distant shot = lower weight)
4. **Minimal required config**: User MUST provide only reference image; weight has a default

---

## 6. Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| IPAdapter model incompatible with Wan2.2 | Critical (consistency blocked) | Research compatible IPAdapter versions before integration |
| IPAdapter weight too high (frozen character) | Medium (looks unnatural) | Start high, tune down; weight is configurable |
| IPAdapter weight too low (no consistency gain) | Medium (no improvement) | Increase weight; if max weight insufficient, investigate IPAdapter model quality |
| IPAdapter adds significant generation time | Low | Acceptable for quality; not a blocker |
| Multiple IPAdapter nodes for multi-character | Low | Defer multi-character to post-Q3; focus on single character first |

---

## 7. PM Recommendations

1. **F-002 MUST NOT begin until F-001 establishes Q1 single-clip baseline** -- consistency work on broken clips is waste
2. **F-002 SHOULD integrate IPAdapter incrementally** -- IPAdapter alone first, then combine with chaining
3. **F-002 MUST update the binding schema** to expose IPAdapter configuration to the user
4. **F-002 SHOULD produce a full 3-clip stitched video at each sub-phase** for evaluation
5. **Single-character focus**: F-002 MUST solve single-character consistency first; multi-character is post-Q3
