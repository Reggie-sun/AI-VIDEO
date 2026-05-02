# System Architect Analysis — AI-VIDEO Quality Crossroads

**Role**: system-architect
**Session**: WFS-video-quality-crossroads
**Date**: 2026-05-02

---

## Executive Summary

The AI-VIDEO pipeline is functionally complete (run/resume/stitch/manifest, 31 tests), but video quality is the blocking problem: single-clip output is poor and cross-clip consistency is absent. The root cause is unoptimized workflow parameters, not model capability limits. The architecture MUST evolve in three concurrent directions: (1) a parameter experiment framework that makes tuning systematic and reproducible, (2) IPAdapter integration through the existing binding schema to solve cross-clip character consistency, and (3) a model-agnostic quality evaluation layer that can survive future model/workflow switching. The binding schema already has `character_refs` and `IPAdapterConfig` -- the plumbing exists, it is just not connected to the current Wan2.2 workflow template.

## Feature Point Index

| Feature ID | Name | Architecture Impact | Key Doc |
|------------|------|---------------------|---------|
| F-001 | wan22-quality-baseline | Parameter tuning in existing workflow; no new modules | @analysis-F-001-wan22-quality-baseline.md |
| F-002 | ipadapter-consistency | New workflow nodes + binding entries; `_prepare_character_images` activation | @analysis-F-002-ipadapter-consistency.md |
| F-003 | quality-evaluation-framework | New `quality.py` module; manifest extension | @analysis-F-003-quality-evaluation-framework.md |
| F-004 | param-experiment-tracker | New `experiments.py` module; run directory extension | @analysis-F-004-param-experiment-tracker.md |
| F-005 | full-video-evaluation-loop | Pipeline orchestration extension; quality gate integration | @analysis-F-005-full-video-evaluation-loop.md |

## Cross-Cutting Concerns

See @analysis-cross-cutting.md for: workflow template versioning strategy, binding schema evolution, manifest extensibility for quality/experiment data, and model-agnostic design principles.

## Technical Roadmap (Phased)

### Phase 1: Quality Baseline (F-001)
- Research and apply Wan2.2 community best-practice parameters
- Modify `wan22_i2v_api.json` sampler parameters (steps, cfg, shift, scheduler)
- Improve prompt engineering in `wan22.project.yaml` defaults
- **Exit**: At least 1 single clip rated "acceptable" by manual review

### Phase 2: IPAdapter Integration (F-002)
- Create `wan22_i2v_ipadapter_api.json` with IPAdapter nodes
- Populate `character_refs` in binding YAML
- Configure character profiles with reference images and weights
- Validate IPAdapter + last-frame chaining do not conflict
- **Exit**: Multi-clip run with stable character appearance

### Phase 3: Quality + Experiment Framework (F-003, F-004)
- Build `quality.py` for automated metric collection
- Build `experiments.py` for parameter experiment tracking
- Extend manifest schema with quality scores and experiment metadata
- **Exit**: Each run produces quantified quality data; experiments are reproducible

### Phase 4: Closed-Loop Evaluation (F-005)
- Integrate quality gates into pipeline post-clip and post-stitch
- Enable "run -> evaluate -> adjust -> re-run" workflow
- **Exit**: Automated quality-driven iteration cycle

### Dependencies
- F-001 is a hard prerequisite for F-002 (must have quality baseline before testing IPAdapter)
- F-002 is a soft prerequisite for F-003 (need realistic multi-clip output to evaluate)
- F-003 and F-004 can proceed in parallel after F-001
- F-005 requires F-003 (needs quality metrics to close the loop)

## Key Architecture Decisions

1. **Workflow templates are interchangeable units**: Each quality experiment or model change produces a new template + binding pair. The pipeline never hardcodes node IDs.
2. **Binding schema is the contract**: IPAdapter integration requires new `character_refs` entries, not Python code changes. The `CharacterRefBinding` model already supports this.
3. **Quality evaluation is model-agnostic**: Metrics operate on video pixels and semantic embeddings, not on model internals. This survives model switching.
4. **Experiment tracking is sidecar, not inline**: Experiment metadata lives alongside the run manifest, not inside it. This keeps the manifest schema stable.
5. **Fallback to model switching is architecturally cheap**: Switching from Wan2.2 to another model requires a new template + binding pair + new widget name maps in `workflow_loader.py`. No pipeline code changes.
