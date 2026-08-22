from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.production.local_continuity_reviewer import (
    LocalCudaContinuityReviewerConfig,
    create_local_cuda_continuity_reviewer,
)
from ai_video.production.models import ToolIdentity


def _config(**changes: object) -> LocalCudaContinuityReviewerConfig:
    values: dict[str, object] = {
        "model_root": Path("/opt/ai-video/continuity-models"),
        "ffmpeg_executable": Path("/usr/bin/ffmpeg"),
        "sampler": ToolIdentity(name="ffmpeg", version="7.1"),
        "evaluator": ToolIdentity(name="local-cuda-continuity", version="1"),
        "sample_width": 640,
        "sample_height": 360,
    }
    values.update(changes)
    return LocalCudaContinuityReviewerConfig.model_validate(values)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("model_root", Path("relative-models")),
        ("ffmpeg_executable", Path("ffmpeg")),
        ("sample_width", 0),
        ("sample_height", True),
        ("max_sample_count", 2),
        ("timeout_seconds", float("inf")),
        ("sampler", ToolIdentity(name="", version="1")),
        ("evaluator", ToolIdentity(name="local-cuda-continuity", version=" ")),
    ),
)
def test_local_cuda_config_rejects_unsealed_or_invalid_values(
    field: str, value: object
) -> None:
    with pytest.raises(ValidationError):
        _config(**{field: value})


def test_local_cuda_config_defaults_are_strict_and_do_not_require_assets() -> None:
    config = _config()

    assert config.model_root == Path("/opt/ai-video/continuity-models")
    assert config.max_sample_count == 9
    assert config.timeout_seconds == 30.0


def test_factory_composes_exact_sealed_local_components(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ai_video.production.local_continuity_reviewer as module

    config = _config(max_sample_count=7, timeout_seconds=12.5)
    profile = object()
    assets = object()
    reviewer = object()
    observed: dict[str, object] = {}

    def fallback(*_args: object) -> object:
        raise AssertionError("fallback must only be bound during construction")

    fallback_identity = ToolIdentity(name="human-continuity", version="2026-08")

    def create_profile(**kwargs: object) -> object:
        observed["profile"] = kwargs
        return profile

    def create_assets(root: Path) -> object:
        observed["assets"] = root
        return assets

    class Tracker:
        instance: "Tracker"

        def __init__(self, **kwargs: object) -> None:
            observed["tracker"] = kwargs
            Tracker.instance = self

    class Sampler:
        instance: "Sampler"

        def __init__(self, **kwargs: object) -> None:
            observed["sampler"] = kwargs
            Sampler.instance = self

    def create_evaluator(**kwargs: object) -> object:
        observed["evaluator"] = kwargs
        return reviewer

    monkeypatch.setattr(module, "create_yolox_osnet_profile", create_profile)
    monkeypatch.setattr(module, "yolox_osnet_assets", create_assets)
    monkeypatch.setattr(module, "CudaOnnxSubjectTrackerBackend", Tracker)
    monkeypatch.setattr(module, "FfmpegRgbFrameSampler", Sampler)
    monkeypatch.setattr(module, "HybridContinuityEvaluatorV1", create_evaluator)

    result = create_local_cuda_continuity_reviewer(
        config=config,
        human_fallback=fallback,
        human_fallback_identity=fallback_identity,
    )

    assert result is reviewer
    assert observed["profile"] == {
        "sampler": config.sampler,
        "sample_width": 640,
        "sample_height": 360,
        "max_sample_count": 7,
    }
    assert observed["assets"] == config.model_root
    assert observed["tracker"] == {"profile": profile, "assets": assets}
    assert observed["sampler"] == {
        "executable": config.ffmpeg_executable,
        "identity": config.sampler,
        "sample_width": 640,
        "sample_height": 360,
        "timeout_seconds": 12.5,
    }
    assert observed["evaluator"] == {
        "sampler": Sampler.instance,
        "evaluator": config.evaluator,
        "tracker": Tracker.instance,
        "human_fallback": fallback,
        "human_fallback_identity": fallback_identity,
    }

    with pytest.raises(TypeError):
        create_local_cuda_continuity_reviewer(
            config=config,
            human_fallback=fallback,
        )


def test_factory_rejects_explicitly_missing_human_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ai_video.production.local_continuity_reviewer as module

    constructor_calls: list[str] = []
    monkeypatch.setattr(
        module,
        "create_yolox_osnet_profile",
        lambda **_kwargs: constructor_calls.append("profile") or object(),
    )
    monkeypatch.setattr(
        module,
        "yolox_osnet_assets",
        lambda _root: constructor_calls.append("assets") or object(),
    )
    monkeypatch.setattr(
        module,
        "CudaOnnxSubjectTrackerBackend",
        lambda **_kwargs: constructor_calls.append("tracker") or object(),
    )
    monkeypatch.setattr(
        module,
        "FfmpegRgbFrameSampler",
        lambda **_kwargs: constructor_calls.append("sampler") or object(),
    )

    with pytest.raises(ValueError, match="human fallback"):
        create_local_cuda_continuity_reviewer(
            config=_config(),
            human_fallback=None,  # type: ignore[arg-type]
            human_fallback_identity=None,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="human fallback"):
        create_local_cuda_continuity_reviewer(
            config=_config(),
            human_fallback=lambda *_args: object(),
            human_fallback_identity=ToolIdentity(name="", version="1"),
        )

    assert constructor_calls == []
