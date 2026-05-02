# F-003: Quality Evaluation Framework — Architecture Analysis

## Problem Definition

Quality is currently assessed by manual human review only. There is no automated way to compare two parameter sets, track quality trends, or determine whether a change improved or degraded output. A quality evaluation framework MUST provide model-agnostic metrics that work on video output files.

## Design Principles

1. **Model-agnostic**: Metrics operate on `.mp4` files and extracted frames. They do not depend on model internals, latent representations, or specific node types.
2. **Sidecar architecture**: Quality data lives in sidecar files, not in the manifest. The manifest tracks pipeline state; quality data is an observation.
3. **Layered evaluation**: Per-frame metrics, per-clip metrics, and cross-clip metrics. Each layer serves a different diagnostic purpose.
4. **Hybrid scoring**: Automated metrics + human review scores. Automated metrics catch objective problems; human review catches subjective quality.
5. **Composable**: New metrics can be added without changing the framework structure.

## Quality Metric Categories

### Layer 1: Per-Frame Quality (within a single clip)

| Metric | What It Measures | Implementation | Model-Agnostic |
|--------|-----------------|----------------|----------------|
| BRISQUE | Natural image quality (no-reference) | OpenCV / pyiqa | Yes |
| Sharpness | Edge clarity (Laplacian variance) | OpenCV | Yes |
| Face consistency | Same face across frames within clip | InsightFace or similar | Yes |
| Color coherence | No sudden color shifts within clip | Histogram comparison between adjacent frames | Yes |

### Layer 2: Per-Clip Quality (aggregate of frames)

| Metric | What It Measures | Implementation | Model-Agnostic |
|--------|-----------------|----------------|----------------|
| Motion coherence | No sudden jumps or frozen frames | Optical flow consistency (RAFT) | Yes |
| Temporal flicker | Frame-to-frame pixel stability | Frame difference scores | Yes |
| CLIP semantic score | Does the clip match the prompt? | CLIP model on sampled frames | Yes |
| Composite quality | Weighted average of L1 metrics | Weighted formula | Yes |

### Layer 3: Cross-Clip Consistency (between clips)

| Metric | What It Measures | Implementation | Model-Agnostic |
|--------|-----------------|----------------|----------------|
| Character identity | Same character across clips | Face embedding distance (InsightFace) | Yes |
| Scene continuity | Visual coherence at clip boundaries | Last-frame vs next-clip-first-frame SSIM | Yes |
| Color consistency | Same color palette across clips | Histogram comparison between clips | Yes |
| Stitch seam quality | Transition smoothness | Frame difference at stitch points | Yes |

## Architecture

### New Module: `quality.py`

```python
# Conceptual interface
class QualityEvaluator:
    """Evaluates video quality on generated output files."""

    def evaluate_clip(self, clip_path: Path, prompt: str) -> ClipQualityReport:
        """Run all Layer 1 + Layer 2 metrics on a single clip."""
        ...

    def evaluate_cross_clip(
        self, clip_reports: list[ClipQualityReport]
    ) -> CrossClipQualityReport:
        """Run all Layer 3 metrics across multiple clips."""
        ...

    def evaluate_stitch(self, final_path: Path) -> StitchQualityReport:
        """Evaluate the final stitched video."""
        ...
```

### Data Models

```python
class FrameQualityMetrics(BaseModel):
    frame_index: int
    brisque_score: float | None = None
    sharpness: float | None = None
    face_consistency: float | None = None

class ClipQualityReport(BaseModel):
    shot_id: str
    clip_path: str
    prompt: str
    frame_metrics: list[FrameQualityMetrics]
    motion_coherence: float | None = None
    temporal_flicker: float | None = None
    clip_semantic_score: float | None = None
    composite_score: float | None = None
    evaluated_at: str

class CrossClipQualityReport(BaseModel):
    run_id: str
    character_identity_scores: dict[str, float]  # character_id -> score
    scene_continuity_scores: list[float]  # per boundary
    color_consistency: float | None = None
    stitch_seam_scores: list[float] | None = None
    overall_consistency: float | None = None
    evaluated_at: str
```

### File Output

```
runs/<run_id>/
  quality_report.json          # Contains ClipQualityReport + CrossClipQualityReport
  shots/
    shot_001/
      quality_metrics.json     # Per-clip detailed metrics
```

## Implementation Phases

### Phase 3a: Minimal Viable Metrics (no ML dependencies)

- Frame extraction via ffmpeg (already available)
- Sharpness (Laplacian variance) — OpenCV only
- Temporal flicker (frame difference) — OpenCV only
- Stitch seam quality (SSIM at boundaries) — OpenCV only

**Rationale**: Start with metrics that require only OpenCV and ffmpeg, which are already available or easy to install. No GPU inference needed.

### Phase 3b: ML-Based Metrics (add optional dependencies)

- BRISQUE — requires `pyiqa` or `opencv-contrib`
- CLIP semantic score — requires `transformers` + `torch`
- Face consistency — requires `insightface` or `facexlib`
- Motion coherence — requires `raft` optical flow

**Rationale**: These metrics provide higher signal but add heavy dependencies. They SHOULD be optional and gracefully skipped when dependencies are missing.

### Dependency Strategy

```toml
# pyproject.toml
[project.optional-dependencies]
quality-lite = ["opencv-python>=4.8"]
quality-full = [
    "opencv-python>=4.8",
    "pyiqa>=0.1",
    "transformers>=4.30",
    "torch>=2.0",
    "insightface>=0.7",
]
```

The `quality-lite` set provides basic metrics with minimal dependencies. The `quality-full` set provides comprehensive metrics with ML dependencies.

## CLI Integration

```bash
# Evaluate an existing run
ai-video evaluate --run runs/<run_id>

# Run with automatic evaluation
ai-video run --project wan22.project.yaml --shots wan22.shots.yaml --evaluate
```

The `evaluate` command reads the manifest, locates clip files, runs quality metrics, and writes sidecar reports.

## Quality Gate Architecture

Quality gates are decision points that use quality metrics:

```python
class QualityGate:
    """Determines if quality meets a threshold."""

    def check_clip(self, report: ClipQualityReport) -> QualityGateResult:
        """Check if a clip meets quality thresholds."""
        ...

    def check_stitch(self, report: CrossClipQualityReport) -> QualityGateResult:
        """Check if cross-clip consistency meets thresholds."""
        ...
```

**Important**: Quality gates SHOULD NOT block the pipeline in early phases. They SHOULD produce data that informs decisions. Blocking behavior can be added once thresholds are calibrated.

## Risk: Metric Validity

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| BRISQUE/CLIP scores do not correlate with human quality perception | Medium | Misleading optimization targets | Always calibrate automated metrics against human review; use automated scores as proxies, not ground truth |
| Face detection fails on stylized/animated output | Low-Medium | Missing face consistency data | Fall back gracefully; report "face detection unavailable" rather than error |
| Heavy ML dependencies conflict with existing environment | Low | Installation failure | Use optional dependency groups; isolate quality evaluation from pipeline |

## Success Criteria for F-003

1. `ai-video evaluate` produces a quality report with at least 4 metrics (sharpness, flicker, seam quality, one ML metric)
2. Quality reports are sidecar files that do not affect manifest or resume logic
3. Metrics are model-agnostic (tested on at least 2 different video sources)
4. Human review scores correlate with automated composite score (r > 0.5)
