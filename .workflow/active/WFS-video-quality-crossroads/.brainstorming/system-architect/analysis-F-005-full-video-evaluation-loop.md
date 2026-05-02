# F-005: Full Video Evaluation Loop — Architecture Analysis

## Problem Definition

The current workflow is open-loop: run the pipeline, look at the output, manually decide what to change, manually re-run. There is no mechanism to automatically evaluate the full video quality, suggest parameter adjustments, and re-run. The evaluation loop closes this gap by connecting quality evaluation (F-003) with parameter experimentation (F-004) in a cycle.

## Architecture: Closed-Loop System

```
           +------------------+
           | Initial Params   |
           +--------+---------+
                    |
                    v
           +------------------+
           | Pipeline Run     |  (existing pipeline.py)
           +--------+---------+
                    |
                    v
           +------------------+
           | Quality Eval     |  (F-003 quality.py)
           +--------+---------+
                    |
                    v
           +------------------+
           | Quality Gate     |  Score >= threshold?
           +--+------------+--+
              |            |
           Pass           Fail
              |            |
              v            v
        +----------+  +-------------------+
        | Publish  |  | Parameter Adjust  |
        +----------+  +---+---------------+
                          |
                          v
                      Back to Pipeline Run
```

## State Machine: Evaluation Loop

```
idle
  |
  v
running_pipeline  -------> pipeline_failed  (terminal)
  |
  v
evaluating_quality
  |
  +---> evaluation_error  (log and continue with human review)
  |
  v
quality_check
  |
  +---> quality_pass  -----> complete
  |
  +---> quality_fail
         |
         v
      adjusting_parameters
         |
         v
      checking_budget
         |
         +---> budget_exceeded  -----> complete_with_recommendations
         |
         +---> budget_remaining  -----> running_pipeline
```

### Budget Model

The evaluation loop MUST have a budget to prevent infinite iteration:

```python
class EvalLoopBudget(BaseModel):
    """Controls iteration limits for the evaluation loop."""
    max_iterations: int = 5          # maximum pipeline runs
    max_total_minutes: float = 120   # wall-clock time limit
    min_quality_threshold: float = 0.6  # composite score target
```

## New Module: `eval_loop.py`

```python
class EvalLoopRunner:
    """Orchestrates the quality evaluation loop."""

    def __init__(
        self,
        project: ProjectConfig,
        shots: list[ShotSpec],
        binding: WorkflowBinding,
        template: dict[str, Any],
        *,
        budget: EvalLoopBudget,
        quality_evaluator: QualityEvaluator | None = None,
        param_adjuster: ParamAdjuster | None = None,
    ):
        ...

    def run(self) -> EvalLoopResult:
        """Execute the full evaluation loop."""
        ...

    def _adjust_parameters(
        self,
        current_params: dict[str, Any],
        quality_report: QualityReport,
    ) -> dict[str, Any]:
        """Determine parameter adjustments based on quality results."""
        ...
```

### Parameter Adjustment Strategies

The loop needs a strategy for how to adjust parameters when quality is insufficient:

**Strategy 1: Rule-Based Adjustment (Recommended for initial implementation)**

```python
class RuleBasedAdjuster:
    """Adjusts parameters based on quality metric heuristics."""

    RULES = {
        "temporal_flicker_high": {"steps": +4, "cfg": +0.5},
        "sharpness_low": {"steps": +2},
        "face_inconsistency_high": {"ipadapter_weight": +0.1},
        "motion_incoherent": {"shift": -0.5, "noise_aug_strength": -0.01},
    }
```

**Strategy 2: Bayesian Optimization (Future)**

Use Gaussian processes or similar to model the parameter-quality relationship and suggest promising regions. This is a significant addition and SHOULD be deferred until Rule-Based proves insufficient.

**Strategy 3: Human-In-The-Loop (Essential for early phases)**

The evaluation loop SHOULD support a human checkpoint between iterations:

```bash
ai-video eval-loop run \
  --project wan22.project.yaml \
  --shots wan22.shots.yaml \
  --interactive   # Pause between iterations for human review
```

In interactive mode, after each iteration:
1. Display quality scores and sample frames
2. Ask human to rate and suggest adjustments
3. Apply human suggestions (override automated adjustment)
4. Continue to next iteration

## Integration Architecture

### How F-005 Connects F-001 Through F-004

| Component | Role in Eval Loop | Source |
|-----------|-------------------|--------|
| Pipeline runner | Execute generation | F-001 (existing) |
| Quality evaluator | Score output | F-003 |
| Experiment tracker | Record iterations | F-004 |
| Param overrides | Inject adjusted params | F-001 (param_overrides) |
| Quality gate | Decision point | F-003 (threshold) |

### EvalLoopResult Model

```python
class EvalLoopResult(BaseModel):
    """Result of a complete evaluation loop."""
    loop_id: str
    budget: EvalLoopBudget
    iterations: list[EvalLoopIteration]
    final_quality_score: float | None = None
    best_parameters: dict[str, Any] | None = None
    status: str  # "completed", "budget_exceeded", "quality_achieved"
    recommendations: list[str] = []

class EvalLoopIteration(BaseModel):
    """Single iteration of the evaluation loop."""
    iteration: int
    parameters: dict[str, Any]
    run_id: str
    quality_score: float | None = None
    quality_report_path: str | None = None
    human_rating: int | None = None
    parameter_changes: dict[str, tuple[Any, Any]]  # param -> (old, new)
```

## Pipeline Integration

The eval loop calls the pipeline runner for each iteration. The key integration point is parameter injection:

```python
# Current pipeline.run() signature
def run(self, run_id: str | None = None, ...) -> RunManifest:

# Extended with param_overrides
def run(self, run_id: str | None = None, *,
        param_overrides: dict[str, Any] | None = None, ...) -> RunManifest:
```

The pipeline passes `param_overrides` through to `render_workflow`, which applies them via `binding.param_overrides`. This is the ONLY change needed in pipeline.py.

## CLI Integration

```bash
# Run evaluation loop
ai-video eval-loop \
  --project wan22.project.yaml \
  --shots wan22.shots.yaml \
  --max-iterations 5 \
  --quality-threshold 0.7

# Run with interactive human review between iterations
ai-video eval-loop \
  --project wan22.project.yaml \
  --shots wan22.shots.yaml \
  --interactive

# Resume an interrupted eval loop
ai-video eval-loop-resume \
  --loop-dir experiments/<loop_id>
```

## File Output

```
experiments/
  eval-loop-<id>/
    eval_loop_result.json    # EvalLoopResult
    iterations/
      1/
        iteration.json       # EvalLoopIteration
        run/                 # link to actual run
        quality/             # quality reports
      2/
        ...
```

## Risk: Automated Adjustment Quality

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Rule-based adjustment makes wrong choices | Medium | Wastes iterations | Human-in-the-loop as default; automated as opt-in |
| Loop oscillates between parameter sets | Medium | No convergence | Track parameter history; detect oscillation; suggest manual intervention |
| Quality metrics mislead optimization | Medium | Optimizes wrong thing | Always include human review checkpoint; metrics are suggestions, not commands |
| Single iteration takes too long | Low | Budget exhausted quickly | Quick mode: single-shot evaluation for screening |

## Fallback: Model Switching

If the evaluation loop consistently fails to reach the quality threshold after exhausting the parameter space, the architecture supports model switching:

1. The loop SHOULD detect when it is "stuck" (no improvement across 3+ iterations)
2. It SHOULD report: "Parameter optimization appears saturated. Consider switching models."
3. Switching models requires:
   - New workflow template JSON (e.g., `svd_i2v_api.json`)
   - New binding YAML (e.g., `svd_i2v_binding.yaml`)
   - New `ARRAY_WIDGET_NAME_MAP` entries in `workflow_loader.py` if node types differ
   - No pipeline code changes

The cost of model switching is: 1 new template + 1 new binding + minor `workflow_loader.py` entries. The pipeline, manifest, experiment tracker, and quality evaluator are all model-agnostic.

## Success Criteria for F-005

1. The evaluation loop can run at least 3 iterations automatically
2. Each iteration produces quality scores and parameter change records
3. The loop terminates on budget exhaustion or quality threshold
4. Interactive mode allows human-guided parameter adjustment
5. "Stuck" detection triggers model-switching recommendation
