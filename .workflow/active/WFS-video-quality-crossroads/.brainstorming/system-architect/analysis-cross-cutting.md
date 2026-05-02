# Cross-Cutting Architecture Decisions

## 1. Workflow Template Versioning Strategy

**Problem**: As we iterate on quality, we will produce many variants of workflow templates. We need a strategy that prevents template drift and enables rollback.

**Decision**: Use filename-based versioning with a naming convention.

```
workflows/templates/
  wan22_i2v_api.json              # current "production" template
  wan22_i2v_api.v2.json           # iteration 2
  wan22_i2v_ipadapter_api.json    # IPAdapter variant
```

The `project.yaml` `workflow.template` path selects which template to use. No code changes required to switch.

**Binding co-versioning**: Each template MUST have a corresponding binding file with the same base name:

```
workflows/bindings/
  wan22_i2v_binding.yaml              # matches wan22_i2v_api.json
  wan22_i2v_ipadapter_binding.yaml    # matches wan22_i2v_ipadapter_api.json
```

Validation already checks that binding paths exist in the template (`_validate_binding_paths`). This catches template-binding mismatches at validate time.

**Rationale**: The existing manifest already records `workflow_template_hash` and `workflow_binding_hash`. Combined with filename versioning, this gives full reproducibility without introducing a database or version control system inside the tool.

## 2. Binding Schema Evolution

**Current state**: `WorkflowBinding` supports:
- `positive_prompt`, `negative_prompt`, `seed`, `init_image`, `output_prefix`
- `character_refs: list[CharacterRefBinding]` (currently empty for wan22)
- `clip_output`

**What needs to change for IPAdapter**: The binding schema already supports IPAdapter via `character_refs`. Each `CharacterRefBinding` has `image_path` and `weight_path` pointing to workflow JSON paths. No schema change required.

**What needs to change for parameter experiments**: We need to bind additional tunable parameters. Two approaches:

**Option A (Recommended): Extended binding with `param_overrides`**

```yaml
param_overrides:
  - name: steps
    path: ["562", "inputs", "steps"]
  - name: cfg
    path: ["562", "inputs", "cfg"]
  - name: shift
    path: ["562", "inputs", "shift"]
  - name: scheduler
    path: ["562", "inputs", "scheduler"]
```

This allows the experiment tracker to modify sampler parameters through the same binding mechanism, without adding model-specific code to the pipeline.

**Option B: Shot-level metadata overrides**: Use `shot.metadata` to carry parameter overrides, but this mixes configuration with data. Rejected.

**Decision**: Add `param_overrides: list[ParamOverrideBinding]` to `WorkflowBinding`. Each entry maps a human-readable parameter name to a JSON path. The experiment tracker reads and writes through these paths.

## 3. Manifest Extensibility

**Problem**: Adding quality scores and experiment metadata to the manifest risks schema churn and breaking resume logic.

**Decision**: Use a sidecar model, not manifest extension.

**Run directory structure evolution**:

```
runs/<run_id>/
  manifest.json                # existing, unchanged
  quality_report.json          # new sidecar: quality metrics per clip
  experiment_meta.json         # new sidecar: experiment parameters
  shots/
    shot_001/
      clip.mp4
      last_frame.png
      attempt_1/
        workflow.json
      quality_metrics.json     # new sidecar: per-clip quality data
```

**Rationale**:
- Manifest is the "source of truth" for pipeline state. Quality and experiment data are observations, not pipeline state.
- Sidecars can be regenerated without risking manifest integrity.
- Resume logic stays simple: it reads manifest, not quality data.
- Quality framework can evolve independently.

## 4. Model-Agnostic Design Principles

The following MUST be true for any model/workflow switch:

1. **Pipeline code is model-agnostic**: `pipeline.py`, `cli.py`, `manifest.py` never reference model-specific node IDs or parameter names.
2. **Binding is the translation layer**: All model-specific knowledge lives in template + binding files.
3. **Widget name mapping is the only code-level concession**: `workflow_loader.py` has `ARRAY_WIDGET_NAME_MAP` which is model-specific. This is acceptable because it is a conversion concern, not a pipeline concern.
4. **Quality metrics operate on video output, not model internals**: CLIP-based metrics, temporal consistency, and perceptual quality scores all work on the generated `.mp4` files, not on latent representations.
5. **Experiment records include model/workflow identifiers**: Every experiment MUST record the template filename, binding filename, and their hashes.

## 5. Parameter Binding Architecture

**Current gap**: The workflow template has hardcoded sampler parameters (steps=8, cfg=1.0, shift=3.0) that cannot be overridden without editing the JSON file directly.

**Architecture for parameterized runs**:

```python
# In workflow_renderer.py
def render_workflow(
    *,
    template: dict[str, Any],
    binding: WorkflowBinding,
    shot: ShotSpec,
    defaults: DefaultsConfig,
    characters: Mapping[str, CharacterProfile],
    shot_index: int,
    chain_image_name: str | None,
    character_image_names: Mapping[str, str],
    output_prefix: str,
    param_overrides: Mapping[str, Any] | None = None,  # NEW
) -> RenderedWorkflow:
    # ... existing logic ...
    # Apply param_overrides through binding.param_overrides paths
    if param_overrides and binding.param_overrides:
        for override in binding.param_overrides:
            if override.name in param_overrides:
                _set_path(workflow, override.path, param_overrides[override.name], override.name)
```

This keeps `render_workflow` pure and testable. The experiment tracker provides `param_overrides` at call time.

## 6. Risk: IPAdapter and Last-Frame Chaining Conflict

**Concern**: IPAdapter injects character appearance from reference images. Last-frame chaining injects visual continuity from the previous clip. Both modify the generation conditioning. They could compete or cancel each other.

**Mitigation architecture**:
- IPAdapter MUST operate on a separate node from the init_image encoder. In ComfyUI terms, IPAdapter is typically applied as a separate attention injection, while init_image goes through the VAE encoder. They should not conflict at the node level.
- Weight tuning is critical: IPAdapter weight (0.6-0.8 typical) must be balanced against `start_latent_strength` and `end_latent_strength` in `WanVideoImageToVideoEncode`.
- The architecture SHOULD support per-shot IPAdapter weight overrides so we can tune the balance per scene.

**Validation approach**: Phase 2 testing MUST compare:
1. Chaining only (current)
2. IPAdapter only
3. Both combined
4. Both combined with reduced IPAdapter weight

The experiment tracker makes this systematic.

## 7. Quality Gate Placement

Quality gates are decision points in the pipeline where automated quality checks determine whether to proceed, retry, or fail.

**Recommended gate placements**:

| Gate | Location | Check | Action |
|------|----------|-------|--------|
| G1 | Post-clip (per shot) | Single-clip quality score | Flag but continue (quality data is informational at this stage) |
| G2 | Post-stitch | Cross-clip consistency score | Flag but continue |
| G3 | Post-run (evaluation loop) | Composite quality score | Decide whether to adjust parameters and re-run |

**Important**: Gates SHOULD NOT block the pipeline in Phase 3-4. They SHOULD produce data that informs human or automated decisions. Blocking gates can be added later once confidence in quality thresholds is established.

## 8. Data Flow for Experiment Loop

```
project.yaml + shots.yaml + workflow template + binding
                    |
                    v
            Experiment Config (which params to sweep)
                    |
                    v
            Pipeline Runner (param_overrides injected)
                    |
                    v
            Run produces: clips + manifest + quality sidecars
                    |
                    v
            Quality Evaluation (automated metrics)
                    |
                    v
            Experiment Record (params -> quality scores)
                    |
                    v
            Decision: adjust params and re-run?
```

This loop MUST be supported by the CLI. A new `evaluate` command or `--evaluate` flag on `run` would trigger the quality evaluation step after generation completes.
