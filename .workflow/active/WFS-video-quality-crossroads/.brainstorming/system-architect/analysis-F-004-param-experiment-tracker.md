# F-004: Parameter Experiment Tracker — Architecture Analysis

## Problem Definition

Parameter tuning is currently ad-hoc: edit the workflow JSON or config YAML, run, look at the output, repeat. There is no systematic tracking of which parameters produced which results. This makes it impossible to reproduce results, compare parameter sets, or build institutional knowledge about what works.

## Design Principles

1. **Reproducibility**: Every experiment MUST be fully reproducible from its recorded parameters + templates + seeds.
2. **Non-intrusive**: The experiment tracker MUST NOT change the pipeline's core behavior. It records observations; it does not control generation.
3. **Binding-driven**: Parameters are identified by their binding names, not by workflow-internal node IDs. This makes experiment records model-agnostic.
4. **Sweep-friendly**: The tracker MUST support parameter sweeps (grid search, random search) without manual iteration.

## Experiment Data Model

```python
class ExperimentRun(BaseModel):
    """Record of a single parameter experiment."""
    experiment_id: str = Field(default_factory=lambda: uuid4().hex[:8])
    experiment_name: str
    created_at: str = Field(default_factory=_now)

    # What was tested
    parameter_set: dict[str, Any]       # param_name -> value
    template_path: str                   # workflow template filename
    binding_path: str                    # binding filename
    template_hash: str
    binding_hash: str

    # Context
    project_config_snapshot: dict        # relevant project config at experiment time
    shot_list_snapshot: dict             # shot list at experiment time

    # Results
    run_id: str | None = None            # link to actual run
    quality_report_path: str | None = None
    composite_quality_score: float | None = None

    # Human annotation
    human_rating: int | None = None      # 1-5 scale
    human_notes: str | None = None
    selected: bool = False               # was this parameter set chosen?
```

### Experiment Batch (Sweep)

```python
class ExperimentBatch(BaseModel):
    """A group of related experiments (e.g., a parameter sweep)."""
    batch_id: str = Field(default_factory=lambda: uuid4().hex[:8])
    batch_name: str
    created_at: str = Field(default_factory=_now)

    # Sweep definition
    base_parameters: dict[str, Any]      # common params for all experiments
    sweep_parameters: dict[str, list[Any]]  # param_name -> [values to try]

    # Results
    experiments: list[ExperimentRun] = []
    best_experiment_id: str | None = None

    # Metadata
    model_name: str                      # e.g., "wan2.2_i2v_14B"
    workflow_type: str                   # e.g., "i2v", "i2v_ipadapter"
```

## File Output

```
experiments/
  <batch_id>/
    batch.json                         # ExperimentBatch record
    <experiment_id>/
      experiment.json                  # ExperimentRun record
      run/                             # symlink or copy of the actual run
```

The `experiments/` directory is separate from `runs/` to avoid polluting the run namespace. Each experiment links to its run for traceability.

## Experiment Runner Architecture

### New Module: `experiments.py`

```python
class ExperimentRunner:
    """Runs parameter experiments systematically."""

    def __init__(self, project: ProjectConfig, shots: list[ShotSpec],
                 binding: WorkflowBinding, template: dict[str, Any]):
        ...

    def run_single(self, params: dict[str, Any],
                   name: str | None = None) -> ExperimentRun:
        """Run a single experiment with specified parameter overrides."""
        ...

    def run_sweep(self, sweep_params: dict[str, list[Any]],
                  base_params: dict[str, Any] | None = None,
                  batch_name: str | None = None) -> ExperimentBatch:
        """Run a parameter sweep (grid search)."""
        ...

    def compare(self, experiment_ids: list[str]) -> ComparisonReport:
        """Compare quality results across experiments."""
        ...
```

### Sweep Execution Flow

```
1. Define base parameters (from binding defaults)
2. Define sweep parameters (which params to vary, which values)
3. For each combination:
   a. Create ExperimentRun with merged parameters
   b. Run pipeline with param_overrides
   c. Evaluate quality (if quality framework available)
   d. Record results in experiment record
4. After all combinations:
   a. Rank experiments by composite quality score
   b. Record best experiment in batch
   c. Output comparison report
```

### Grid Search Optimization

Full grid search can be expensive (e.g., 5 values x 4 values x 3 values = 60 runs at ~2 min each = 2 hours). Strategies to manage this:

1. **One-at-a-time first**: Vary one parameter at a time, find its optimal range, then do local grid search around the optima.
2. **Early stopping**: If a parameter combination produces obviously bad output (e.g., composite_score < threshold), skip remaining shots in that run.
3. **Quick mode**: Use a single shot for screening, then validate promising candidates with the full shot list.

## Integration with `param_overrides`

The experiment runner injects parameters through the same `param_overrides` mechanism described in F-001:

```python
# In experiment runner
run_result = pipeline_runner.run(
    run_id=f"exp-{experiment.experiment_id}",
    param_overrides=experiment.parameter_set,
)
```

The pipeline passes `param_overrides` to `render_workflow`, which applies them through `binding.param_overrides` paths. This keeps the experiment runner completely decoupled from workflow internals.

## CLI Integration

```bash
# Run a single experiment with parameter overrides
ai-video experiment run \
  --project wan22.project.yaml \
  --shots wan22.shots.yaml \
  --params steps=20,cfg=5.0,shift=5.0

# Run a parameter sweep
ai-video experiment sweep \
  --project wan22.project.yaml \
  --shots wan22.shots.yaml \
  --sweep steps=[8,16,20,30,50] \
  --sweep cfg=[1.0,3.0,5.0,7.0] \
  --base shift=5.0

# Compare experiments
ai-video experiment compare \
  --batch experiments/<batch_id>

# Mark best experiment
ai-video experiment select \
  --experiment experiments/<batch_id>/<exp_id>
```

## Comparison Report

```python
class ComparisonReport(BaseModel):
    """Comparison of experiments within a batch."""
    batch_id: str
    rankings: list[ExperimentRanking]  # sorted by composite_score
    parameter_impact: dict[str, float]  # param_name -> correlation with quality

class ExperimentRanking(BaseModel):
    experiment_id: str
    rank: int
    composite_score: float
    parameter_set: dict[str, Any]
    human_rating: int | None = None
```

The `parameter_impact` field is particularly valuable: it tells you which parameters have the strongest correlation with quality, guiding future tuning focus.

## Risk: Experiment Run Time

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Grid search takes too long (hours) | High | Slow iteration cycle | One-at-a-time screening + local grid search; single-shot quick mode |
| VRAM fragmentation across many runs | Medium | Degraded quality in later runs | ComfyUI memory cleanup between runs (`free_memory` already exists) |
| Experiment records grow large | Low | Disk usage | Clean up old experiments; keep only selected + top-N |
| Parameter combinations produce OOM | Low-Medium | Failed experiments | Catch OOM errors; mark experiment as "failed_oom"; reduce batch size |

## Success Criteria for F-004

1. A single experiment can be run with `--params` overrides and produces a reproducible record
2. A parameter sweep of at least 10 combinations runs to completion
3. Comparison report ranks experiments by quality score
4. A "selected" parameter set can be promoted to the production binding without manual editing
5. Experiment records include enough information to fully reproduce any run
