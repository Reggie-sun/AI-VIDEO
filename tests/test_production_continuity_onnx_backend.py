from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import math
import sys
from types import SimpleNamespace
from pathlib import Path

import numpy as np
import pytest

from ai_video.errors import AiVideoError
from ai_video.production.continuity_evaluator import (
    ContinuityModelAssets,
    SampledRgbFrame,
)
from ai_video.production.models import ToolIdentity


def _backend_module():
    return importlib.import_module("ai_video.production.continuity_onnx_backend")


def _model(module, *, role: str, payload: bytes):
    return module.CudaContinuityOnnxModel.create(
        role=role,
        content_sha256=hashlib.sha256(payload).hexdigest(),
        size_bytes=len(payload),
        input_name="images" if role == "detector" else "input",
        output_name="output" if role == "detector" else "fc_pred",
        input_width=8 if role == "detector" else 2,
        input_height=8 if role == "detector" else 4,
        opset=12,
        output_dimensions=85 if role == "detector" else 256,
        source_repository="fixture://continuity-models",
        source_revision="fixture-revision-1",
        license_id="fixture-only",
        preprocess_contract=(
            "yolox-rgb-to-bgr-letterbox114-bilinear-float32/1"
            if role == "detector"
            else "osnet-rgb-bilinear-float32-imagenet/1"
        ),
        output_contract=(
            "yolox-coco-raw/1" if role == "detector" else "l2-embedding/1"
        ),
    )


def _profile(
    module,
    *,
    detector_bytes: bytes,
    reid_bytes: bytes,
    detector_decode_strides: tuple[int, ...] = (8,),
):
    return module.CudaContinuityVisualProfile.create(
        profile_id="fixture-cuda-continuity",
        profile_version="1",
        sampler=ToolIdentity(name="fixture-rgb-sampler", version="1"),
        sample_width=8,
        sample_height=8,
        numeric_runtime=ToolIdentity(
            name="numpy", version=importlib.metadata.version("numpy")
        ),
        inference_runtime=ToolIdentity(
            name="onnxruntime-gpu",
            version="fixture-gpu-1",
        ),
        cuda_libraries=tuple(
            ToolIdentity(name=name, version="fixture-cuda-1")
            for name in module.CUDA_LIBRARY_PACKAGES
        ),
        detector=_model(module, role="detector", payload=detector_bytes),
        reid=_model(module, role="reid", payload=reid_bytes),
        tracker=ToolIdentity(name="deterministic-reid-tracker", version="2"),
        max_sample_count=9,
        subject_class_ids=(0,),
        detection_confidence_milli=300,
        detection_ambiguity_confidence_milli=100,
        detector_nms_iou_milli=450,
        detector_decode_strides=detector_decode_strides,
        cuda_provider_options=(("device_id", "0"), ("use_tf32", "0")),
        reid_similarity_milli=650,
        track_similarity_margin_milli=50,
        minimum_coverage_milli=700,
        minimum_direction_delta_milli=150,
        minimum_direction_consistency_milli=750,
        edge_band_milli=150,
    )


class _Session:
    def __init__(self, outputs, observed_inputs: list[np.ndarray]) -> None:
        self._outputs = outputs
        self._observed_inputs = observed_inputs
        self.requested_providers = ("CUDAExecutionProvider",)
        self.provider_options = {"device_id": "0", "use_tf32": "0"}
        self.cpu_fallback_disabled = True

    def run(self, _output_names, inputs):
        self._observed_inputs.append(next(iter(inputs.values())).copy())
        return [next(self._outputs)]


def _detector_row(*, score: float) -> np.ndarray:
    row = np.zeros((1, 1, 85), dtype=np.float32)
    row[0, 0, :4] = (0.5, 0.5, math.log(0.5), math.log(0.5))
    row[0, 0, 4] = score
    row[0, 0, 5] = score
    return row


def test_cuda_backend_decodes_yolox_and_normalizes_osnet_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _backend_module()
    real_version = module.importlib.metadata.version
    monkeypatch.setattr(
        module.importlib.metadata,
        "version",
        lambda name: (
            "fixture-gpu-1"
            if name == "onnxruntime-gpu"
            else "fixture-cuda-1"
            if name.startswith("nvidia-")
            else real_version(name)
        ),
    )
    detector_bytes = b"detector-v2"
    reid_bytes = b"reid-v2"
    detector_path = tmp_path / "detector.onnx"
    reid_path = tmp_path / "reid.onnx"
    detector_path.write_bytes(detector_bytes)
    reid_path.write_bytes(reid_bytes)
    detector_inputs: list[np.ndarray] = []
    reid_inputs: list[np.ndarray] = []
    detector_outputs = iter((_detector_row(score=0.9),) * 2)
    reid_outputs = iter((np.ones((1, 256), dtype=np.float32),) * 2)

    def factory(
        model_bytes: bytes,
        providers: tuple[str, ...],
        provider_options: dict[str, str],
    ):
        assert providers == ("CUDAExecutionProvider",)
        assert provider_options == {"device_id": "0", "use_tf32": "0"}
        if model_bytes == detector_bytes:
            return _Session(detector_outputs, detector_inputs)
        return _Session(reid_outputs, reid_inputs)

    backend = module.CudaOnnxSubjectTrackerBackend(
        profile=_profile(
            module,
            detector_bytes=detector_bytes,
            reid_bytes=reid_bytes,
        ),
        assets=ContinuityModelAssets(detector_path=detector_path, reid_path=reid_path),
        session_factory=factory,
    )
    frame = SampledRgbFrame(
        frame_index=0,
        width=8,
        height=8,
        pixels=bytes((10, 20, 30)) * 64,
    )

    observations = backend.track(
        (frame, SampledRgbFrame(**{**frame.__dict__, "frame_index": 1}))
    )

    assert tuple(item.state for item in observations) == ("present", "present")
    assert observations[0].x_min_milli == 250
    assert observations[0].x_max_milli == 750
    assert observations[0].detection_confidence_milli == 810
    assert observations[0].track_identity == observations[1].track_identity
    assert detector_inputs[0].shape == (1, 3, 8, 8)
    assert detector_inputs[0][0, :, 0, 0].tolist() == [30.0, 20.0, 10.0]
    assert reid_inputs[0].shape == (1, 3, 4, 2)
    expected = (
        np.asarray([10.0, 20.0, 30.0], dtype=np.float32) / 255.0
        - np.asarray([0.485, 0.456, 0.406], dtype=np.float32)
    ) / np.asarray([0.229, 0.224, 0.225], dtype=np.float32)
    np.testing.assert_allclose(reid_inputs[0][0, :, 0, 0], expected, rtol=1e-6)


def test_cuda_backend_distinguishes_ambiguous_from_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _backend_module()
    real_version = module.importlib.metadata.version
    monkeypatch.setattr(
        module.importlib.metadata,
        "version",
        lambda name: (
            "fixture-gpu-1"
            if name == "onnxruntime-gpu"
            else "fixture-cuda-1"
            if name.startswith("nvidia-")
            else real_version(name)
        ),
    )
    detector_bytes = b"detector-v2"
    reid_bytes = b"reid-v2"
    detector_path = tmp_path / "detector.onnx"
    reid_path = tmp_path / "reid.onnx"
    detector_path.write_bytes(detector_bytes)
    reid_path.write_bytes(reid_bytes)
    detector_outputs = iter((_detector_row(score=0.4), _detector_row(score=0.2)))

    def factory(
        model_bytes: bytes,
        _providers: tuple[str, ...],
        _provider_options: dict[str, str],
    ):
        outputs = detector_outputs if model_bytes == detector_bytes else iter(())
        return _Session(outputs, [])

    backend = module.CudaOnnxSubjectTrackerBackend(
        profile=_profile(
            module,
            detector_bytes=detector_bytes,
            reid_bytes=reid_bytes,
        ),
        assets=ContinuityModelAssets(detector_path=detector_path, reid_path=reid_path),
        session_factory=factory,
    )
    frames = tuple(
        SampledRgbFrame(
            frame_index=index,
            width=8,
            height=8,
            pixels=bytes(8 * 8 * 3),
        )
        for index in range(2)
    )

    observations = backend.track(frames)

    assert tuple(item.state for item in observations) == (
        "ambiguous",
        "absent",
    )


def test_cuda_backend_applies_class_aware_nms_before_tracking(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _backend_module()
    real_version = module.importlib.metadata.version
    monkeypatch.setattr(
        module.importlib.metadata,
        "version",
        lambda name: (
            "fixture-gpu-1"
            if name == "onnxruntime-gpu"
            else "fixture-cuda-1"
            if name.startswith("nvidia-")
            else real_version(name)
        ),
    )
    detector_bytes = b"detector-v2"
    reid_bytes = b"reid-v2"
    detector_path = tmp_path / "detector.onnx"
    reid_path = tmp_path / "reid.onnx"
    detector_path.write_bytes(detector_bytes)
    reid_path.write_bytes(reid_bytes)
    raw = np.zeros((1, 4, 85), dtype=np.float32)
    raw[0, 0, :4] = (1.0, 1.0, 0.0, 0.0)
    raw[0, 1, :4] = (0.0, 1.0, 0.0, 0.0)
    raw[0, :2, 4] = (0.95, 0.90)
    raw[0, :2, 5] = (0.95, 0.90)
    reid_calls = 0

    def factory(
        model_bytes: bytes,
        _providers: tuple[str, ...],
        _provider_options: dict[str, str],
    ):
        nonlocal reid_calls
        if model_bytes == detector_bytes:
            return _Session(iter((raw,)), [])

        class _ReidSession(_Session):
            def run(self, output_names, inputs):
                nonlocal reid_calls
                reid_calls += 1
                return super().run(output_names, inputs)

        return _ReidSession(iter((np.ones((1, 256), dtype=np.float32),)), [])

    backend = module.CudaOnnxSubjectTrackerBackend(
        profile=_profile(
            module,
            detector_bytes=detector_bytes,
            reid_bytes=reid_bytes,
            detector_decode_strides=(4,),
        ),
        assets=ContinuityModelAssets(detector_path=detector_path, reid_path=reid_path),
        session_factory=factory,
    )
    observation = backend.track(
        (
            SampledRgbFrame(
                frame_index=0,
                width=8,
                height=8,
                pixels=bytes(8 * 8 * 3),
            ),
        )
    )[0]

    assert observation.state == "present"
    assert reid_calls == 1


def test_cuda_backend_scores_subject_class_without_global_argmax(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _backend_module()
    real_version = module.importlib.metadata.version
    monkeypatch.setattr(
        module.importlib.metadata,
        "version",
        lambda name: (
            "fixture-gpu-1"
            if name == "onnxruntime-gpu"
            else "fixture-cuda-1"
            if name.startswith("nvidia-")
            else real_version(name)
        ),
    )
    detector_bytes = b"detector-v2"
    reid_bytes = b"reid-v2"
    detector_path = tmp_path / "detector.onnx"
    reid_path = tmp_path / "reid.onnx"
    detector_path.write_bytes(detector_bytes)
    reid_path.write_bytes(reid_bytes)
    raw = _detector_row(score=0.9)
    raw[0, 0, 6] = 0.95

    def factory(
        model_bytes: bytes,
        _providers: tuple[str, ...],
        _provider_options: dict[str, str],
    ):
        output = (
            raw
            if model_bytes == detector_bytes
            else np.ones((1, 256), dtype=np.float32)
        )
        return _Session(iter((output,)), [])

    backend = module.CudaOnnxSubjectTrackerBackend(
        profile=_profile(
            module,
            detector_bytes=detector_bytes,
            reid_bytes=reid_bytes,
        ),
        assets=ContinuityModelAssets(detector_path=detector_path, reid_path=reid_path),
        session_factory=factory,
    )

    observation = backend.track(
        (
            SampledRgbFrame(
                frame_index=0,
                width=8,
                height=8,
                pixels=bytes(8 * 8 * 3),
            ),
        )
    )[0]

    assert observation.state == "present"
    assert observation.detection_confidence_milli == 810


def test_default_cuda_factory_wraps_ort_base_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _backend_module()

    class _OrtFailure(Exception):
        pass

    class _SessionOptions:
        def add_session_config_entry(self, _key: str, _value: str) -> None:
            pass

    fake_ort = SimpleNamespace(
        SessionOptions=_SessionOptions,
        get_available_providers=lambda: ["CUDAExecutionProvider"],
        InferenceSession=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            _OrtFailure("fixture ORT failure")
        ),
    )
    monkeypatch.setitem(sys.modules, "onnxruntime", fake_ort)
    monkeypatch.setattr(module, "_preload_cuda_libraries", lambda: None)

    with pytest.raises(AiVideoError, match="session could not be created"):
        module._default_cuda_session_factory(
            b"invalid-model",
            ("CUDAExecutionProvider",),
            {"device_id": "0", "use_tf32": "0"},
        )


def test_cuda_profile_rejects_cpu_provider_and_unsealed_hash() -> None:
    module = _backend_module()
    profile = _profile(module, detector_bytes=b"detector-v2", reid_bytes=b"reid-v2")

    with pytest.raises(ValueError, match="CUDAExecutionProvider"):
        module.CudaContinuityVisualProfile.model_validate(
            {
                **profile.model_dump(mode="python"),
                "execution_providers": ("CPUExecutionProvider",),
            }
        )
    with pytest.raises(ValueError, match="profile hash"):
        module.CudaContinuityVisualProfile.model_validate(
            {
                **profile.model_dump(mode="python"),
                "detector_nms_iou_milli": 500,
            }
        )


def test_cuda_backend_rejects_session_that_exposes_cpu_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _backend_module()
    real_version = module.importlib.metadata.version
    monkeypatch.setattr(
        module.importlib.metadata,
        "version",
        lambda name: (
            "fixture-gpu-1"
            if name == "onnxruntime-gpu"
            else "fixture-cuda-1"
            if name.startswith("nvidia-")
            else real_version(name)
        ),
    )
    detector_bytes = b"detector-v2"
    reid_bytes = b"reid-v2"
    detector_path = tmp_path / "detector.onnx"
    reid_path = tmp_path / "reid.onnx"
    detector_path.write_bytes(detector_bytes)
    reid_path.write_bytes(reid_bytes)

    class _FallbackSession(_Session):
        cpu_fallback_disabled = False

    def factory(
        _model_bytes: bytes,
        _providers: tuple[str, ...],
        _provider_options: dict[str, str],
    ):
        session = _FallbackSession(iter(()), [])
        session.cpu_fallback_disabled = False
        return session

    with pytest.raises(AiVideoError, match="CPU fallback"):
        module.CudaOnnxSubjectTrackerBackend(
            profile=_profile(
                module,
                detector_bytes=detector_bytes,
                reid_bytes=reid_bytes,
            ),
            assets=ContinuityModelAssets(
                detector_path=detector_path, reid_path=reid_path
            ),
            session_factory=factory,
        )
