"""Explicit local CUDA continuity reviewer assembly."""

from __future__ import annotations

import math
from pathlib import Path

from pydantic import Field, model_validator

from ai_video.production.continuity_evaluator import (
    FfmpegRgbFrameSampler,
    HumanContinuityFallback,
    HybridContinuityEvaluatorV1,
)
from ai_video.production.continuity_onnx_backend import (
    CudaOnnxSubjectTrackerBackend,
    create_yolox_osnet_profile,
    yolox_osnet_assets,
)
from ai_video.production.models import StrictModel, ToolIdentity


def _identity_is_bound(identity: ToolIdentity) -> bool:
    return bool(identity.name.strip() and identity.version.strip())


class LocalCudaContinuityReviewerConfig(StrictModel):
    """Explicit, read-free inputs for local CUDA continuity review assembly."""

    model_root: Path
    ffmpeg_executable: Path
    sampler: ToolIdentity
    evaluator: ToolIdentity
    sample_width: int = Field(strict=True, gt=0)
    sample_height: int = Field(strict=True, gt=0)
    max_sample_count: int = Field(default=9, strict=True, ge=3)
    timeout_seconds: float = Field(default=30.0, strict=True, gt=0)

    @model_validator(mode="after")
    def _validate_local_paths_and_timeout(
        self,
    ) -> "LocalCudaContinuityReviewerConfig":
        if not self.model_root.is_absolute() or not self.ffmpeg_executable.is_absolute():
            raise ValueError("local continuity reviewer paths must be absolute")
        if not math.isfinite(self.timeout_seconds):
            raise ValueError("local continuity reviewer timeout must be finite")
        if not _identity_is_bound(self.sampler) or not _identity_is_bound(
            self.evaluator
        ):
            raise ValueError("local continuity reviewer identities must be non-empty")
        return self


def create_local_cuda_continuity_reviewer(
    *,
    config: LocalCudaContinuityReviewerConfig,
    human_fallback: HumanContinuityFallback,
    human_fallback_identity: ToolIdentity,
) -> HybridContinuityEvaluatorV1:
    """Build the sealed local CUDA reviewer with an explicit human fallback."""

    if (
        not callable(human_fallback)
        or not isinstance(human_fallback_identity, ToolIdentity)
        or not _identity_is_bound(human_fallback_identity)
    ):
        raise ValueError("local CUDA continuity reviewer requires a bound human fallback")

    profile = create_yolox_osnet_profile(
        sampler=config.sampler,
        sample_width=config.sample_width,
        sample_height=config.sample_height,
        max_sample_count=config.max_sample_count,
    )
    tracker = CudaOnnxSubjectTrackerBackend(
        profile=profile,
        assets=yolox_osnet_assets(config.model_root),
    )
    sampler = FfmpegRgbFrameSampler(
        executable=config.ffmpeg_executable,
        identity=config.sampler,
        sample_width=config.sample_width,
        sample_height=config.sample_height,
        timeout_seconds=config.timeout_seconds,
    )
    return HybridContinuityEvaluatorV1(
        sampler=sampler,
        evaluator=config.evaluator,
        tracker=tracker,
        human_fallback=human_fallback,
        human_fallback_identity=human_fallback_identity,
    )
