"""CUDA-only YOLOX and OSNet subject tracking for continuity measurements."""

from __future__ import annotations

import importlib.metadata
import ctypes
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from pydantic import Field, model_validator

from ai_video.production.continuity_evaluator import (
    ContinuityModelAssets,
    OnnxSubjectTrackerBackend,
    SampledRgbFrame,
    _read_model_bytes,
    _review_error,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel, ToolIdentity


YOLOX_S_FILENAME = "yolox_s.onnx"
OSNET_X1_FILENAME = "osnet_x1_0_msmt17.onnx"
CUDA_LIBRARY_PACKAGES = (
    "nvidia-cuda-runtime-cu12",
    "nvidia-nvjitlink-cu12",
    "nvidia-cublas-cu12",
    "nvidia-cufft-cu12",
    "nvidia-curand-cu12",
    "nvidia-cuda-nvrtc-cu12",
    "nvidia-cudnn-cu12",
)
CUDA_LIBRARY_DIRECTORIES = (
    "nvidia/cuda_runtime/lib",
    "nvidia/nvjitlink/lib",
    "nvidia/cublas/lib",
    "nvidia/cufft/lib",
    "nvidia/curand/lib",
    "nvidia/cuda_nvrtc/lib",
    "nvidia/cudnn/lib",
)


class CudaContinuityOnnxModel(StrictModel):
    role: Literal["detector", "reid"]
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    upstream_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(strict=True, gt=0)
    input_name: str = Field(min_length=1)
    output_name: str = Field(min_length=1)
    input_width: int = Field(strict=True, gt=0)
    input_height: int = Field(strict=True, gt=0)
    input_batch: Literal[1] = 1
    input_channels: Literal[3] = 3
    input_dtype: Literal["float32"] = "float32"
    opset: int = Field(strict=True, ge=1)
    output_batch: Literal[1] = 1
    output_dimensions: int = Field(strict=True, gt=1)
    source_repository: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    license_id: str = Field(min_length=1)
    conversion_contract: str = Field(min_length=1)
    preprocess_contract: Literal[
        "yolox-rgb-to-bgr-letterbox114-bilinear-float32/1",
        "osnet-rgb-bilinear-float32-imagenet/1",
    ]
    output_contract: Literal["yolox-coco-raw/1", "l2-embedding/1"]

    @model_validator(mode="after")
    def _validate_role_contract(self) -> "CudaContinuityOnnxModel":
        expected = {
            "detector": (
                "yolox-rgb-to-bgr-letterbox114-bilinear-float32/1",
                "yolox-coco-raw/1",
            ),
            "reid": (
                "osnet-rgb-bilinear-float32-imagenet/1",
                "l2-embedding/1",
            ),
        }[self.role]
        if (self.preprocess_contract, self.output_contract) != expected:
            raise ValueError("continuity CUDA model role contract is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "CudaContinuityOnnxModel":
        data = dict(values)
        data.setdefault("upstream_content_sha256", data.get("content_sha256"))
        data.setdefault("conversion_contract", "fixture/no-conversion")
        return cls.model_validate(data)


class CudaContinuityVisualProfile(StrictModel):
    schema_version: Literal["continuity-visual-profile/2"] = (
        "continuity-visual-profile/2"
    )
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    sampler: ToolIdentity
    sample_width: int = Field(strict=True, gt=0)
    sample_height: int = Field(strict=True, gt=0)
    numeric_runtime: ToolIdentity
    inference_runtime: ToolIdentity
    cuda_libraries: tuple[ToolIdentity, ...]
    detector: CudaContinuityOnnxModel
    reid: CudaContinuityOnnxModel
    tracker: ToolIdentity
    automatic_match_policy: Literal["human-confirmation-required"] = (
        "human-confirmation-required"
    )
    max_sample_count: int = Field(strict=True, ge=3)
    subject_class_ids: tuple[int, ...] = Field(min_length=1)
    detection_confidence_milli: int = Field(strict=True, ge=1, le=1000)
    detection_ambiguity_confidence_milli: int = Field(strict=True, ge=1, le=1000)
    detector_nms_iou_milli: int = Field(strict=True, ge=1, lt=1000)
    detector_decode_strides: tuple[int, ...] = Field(min_length=1)
    reid_similarity_milli: int = Field(strict=True, ge=1, le=1000)
    track_similarity_margin_milli: int = Field(strict=True, ge=0, le=1000)
    minimum_coverage_milli: int = Field(strict=True, ge=1, le=1000)
    minimum_direction_delta_milli: int = Field(strict=True, ge=1, le=1000)
    minimum_direction_consistency_milli: int = Field(strict=True, ge=1, le=1000)
    edge_band_milli: int = Field(strict=True, ge=1, lt=500)
    execution_providers: tuple[Literal["CUDAExecutionProvider"], ...] = (
        "CUDAExecutionProvider",
    )
    cuda_provider_options: tuple[tuple[str, str], ...]
    profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_profile(self) -> "CudaContinuityVisualProfile":
        if self.detector.role != "detector" or self.reid.role != "reid":
            raise ValueError("continuity CUDA model roles are invalid")
        if self.inference_runtime.name != "onnxruntime-gpu":
            raise ValueError("continuity CUDA runtime must be onnxruntime-gpu")
        if tuple(identity.name for identity in self.cuda_libraries) != (
            CUDA_LIBRARY_PACKAGES
        ):
            raise ValueError("continuity CUDA library identities are invalid")
        if self.execution_providers != ("CUDAExecutionProvider",):
            raise ValueError(
                "continuity CUDA profile requires CUDAExecutionProvider only"
            )
        if self.cuda_provider_options != (
            ("device_id", "0"),
            ("use_tf32", "0"),
        ):
            raise ValueError("continuity CUDA provider options are not sealed")
        if self.subject_class_ids != tuple(sorted(set(self.subject_class_ids))):
            raise ValueError("continuity subject class IDs must be unique and ordered")
        if any(
            class_id < 0 or class_id >= self.detector.output_dimensions - 5
            for class_id in self.subject_class_ids
        ):
            raise ValueError("continuity subject class IDs are outside detector output")
        if self.detection_ambiguity_confidence_milli >= self.detection_confidence_milli:
            raise ValueError("continuity detection ambiguity threshold is invalid")
        if self.detector_decode_strides != tuple(
            sorted(set(self.detector_decode_strides))
        ) or any(
            self.detector.input_width % stride or self.detector.input_height % stride
            for stride in self.detector_decode_strides
        ):
            raise ValueError("continuity YOLOX decode strides are invalid")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"profile_content_hash"})
        )
        if self.profile_content_hash != expected:
            raise ValueError("continuity CUDA profile hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "CudaContinuityVisualProfile":
        data = dict(values)
        data.setdefault("execution_providers", ("CUDAExecutionProvider",))
        provisional = cls.model_construct(**data, profile_content_hash="0" * 64)
        data["profile_content_hash"] = canonical_sha256(
            provisional.model_dump(
                mode="json",
                exclude={"profile_content_hash"},
                warnings=False,
            )
        )
        return cls.model_validate(data)


class CudaOnnxSession(Protocol):
    requested_providers: tuple[str, ...]
    provider_options: dict[str, str]
    cpu_fallback_disabled: bool

    def run(
        self, output_names: list[str], inputs: dict[str, object]
    ) -> list[object]: ...


class CudaOnnxSessionFactory(Protocol):
    def __call__(
        self,
        model_bytes: bytes,
        providers: tuple[str, ...],
        provider_options: dict[str, str],
    ) -> CudaOnnxSession: ...


@dataclass
class _VerifiedCudaSession:
    session: object
    requested_providers: tuple[str, ...]
    provider_options: dict[str, str]
    cpu_fallback_disabled: bool = True

    def run(self, output_names: list[str], inputs: dict[str, object]) -> list[object]:
        return self.session.run(output_names, inputs)  # type: ignore[attr-defined,no-any-return]


def _default_cuda_session_factory(
    model_bytes: bytes,
    providers: tuple[str, ...],
    provider_options: dict[str, str],
) -> CudaOnnxSession:
    try:
        import onnxruntime as ort  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - dependency gate
        raise _review_error(
            "Continuity CUDA runtime dependency is unavailable."
        ) from exc
    if "CUDAExecutionProvider" not in ort.get_available_providers():
        raise _review_error("Continuity CUDA execution provider is unavailable.")
    _preload_cuda_libraries()
    options = ort.SessionOptions()
    options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
    try:
        session = ort.InferenceSession(
            model_bytes,
            sess_options=options,
            providers=[(providers[0], provider_options)],
        )
    except Exception as exc:
        raise _review_error(
            "Continuity CUDA model session could not be created.",
            type(exc).__name__,
        ) from exc
    return _VerifiedCudaSession(
        session=session,
        requested_providers=providers,
        provider_options=dict(provider_options),
    )


def _preload_cuda_libraries() -> None:
    for package_name, relative_directory in zip(
        CUDA_LIBRARY_PACKAGES,
        CUDA_LIBRARY_DIRECTORIES,
        strict=True,
    ):
        try:
            distribution = importlib.metadata.distribution(package_name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise _review_error(
                "Continuity CUDA library dependency is unavailable.",
                package_name,
            ) from exc
        library_directory = Path(distribution.locate_file(relative_directory))
        library_paths = tuple(sorted(library_directory.glob("*.so*")))
        if not library_paths:
            raise _review_error(
                "Continuity CUDA library dependency is unavailable.",
                package_name,
            )
        try:
            for library_path in library_paths:
                ctypes.CDLL(str(library_path), mode=ctypes.RTLD_GLOBAL)
        except OSError as exc:
            raise _review_error(
                "Continuity CUDA library dependency could not be loaded.",
                package_name,
            ) from exc


def _bilinear_resize(image, *, width: int, height: int):
    import numpy as np

    source_height, source_width, _ = image.shape
    if source_width == width and source_height == height:
        return np.ascontiguousarray(image, dtype=np.float32)
    x = (np.arange(width, dtype=np.float32) + 0.5) * source_width / width - 0.5
    y = (np.arange(height, dtype=np.float32) + 0.5) * source_height / height - 0.5
    x = np.clip(x, 0, source_width - 1)
    y = np.clip(y, 0, source_height - 1)
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    x1 = np.minimum(x0 + 1, source_width - 1)
    y1 = np.minimum(y0 + 1, source_height - 1)
    x_weight = (x - x0).reshape(1, width, 1)
    y_weight = (y - y0).reshape(height, 1, 1)
    top = image[y0][:, x0] * (1.0 - x_weight) + image[y0][:, x1] * x_weight
    bottom = image[y1][:, x0] * (1.0 - x_weight) + image[y1][:, x1] * x_weight
    return np.ascontiguousarray(
        top * (1.0 - y_weight) + bottom * y_weight,
        dtype=np.float32,
    )


def _iou(box, boxes):
    import numpy as np

    left = np.maximum(box[0], boxes[:, 0])
    top = np.maximum(box[1], boxes[:, 1])
    right = np.minimum(box[2], boxes[:, 2])
    bottom = np.minimum(box[3], boxes[:, 3])
    intersection = np.maximum(0.0, right - left) * np.maximum(0.0, bottom - top)
    box_area = (box[2] - box[0]) * (box[3] - box[1])
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    return intersection / np.maximum(box_area + areas - intersection, 1e-12)


class CudaOnnxSubjectTrackerBackend(OnnxSubjectTrackerBackend):
    """Sealed CUDA-only YOLOX detector and OSNet appearance tracker."""

    def __init__(
        self,
        *,
        profile: CudaContinuityVisualProfile,
        assets: ContinuityModelAssets,
        session_factory: CudaOnnxSessionFactory = _default_cuda_session_factory,
    ) -> None:
        for identity, package_name in (
            (profile.numeric_runtime, "numpy"),
            (profile.inference_runtime, "onnxruntime-gpu"),
            *((identity, identity.name) for identity in profile.cuda_libraries),
        ):
            try:
                installed_version = importlib.metadata.version(package_name)
            except importlib.metadata.PackageNotFoundError as exc:
                raise _review_error(
                    "Continuity CUDA runtime dependency is unavailable.", package_name
                ) from exc
            if identity != ToolIdentity(name=package_name, version=installed_version):
                raise _review_error(
                    "Continuity CUDA runtime does not match the sealed profile.",
                    package_name,
                )
        detector_bytes = _read_model_bytes(assets.detector_path, profile.detector)
        reid_bytes = _read_model_bytes(assets.reid_path, profile.reid)
        provider_options = dict(profile.cuda_provider_options)
        self.profile = profile
        self._detector = session_factory(
            detector_bytes, profile.execution_providers, provider_options
        )
        self._reid = session_factory(
            reid_bytes, profile.execution_providers, provider_options
        )
        for session in (self._detector, self._reid):
            if (
                not session.cpu_fallback_disabled
                or session.requested_providers != profile.execution_providers
                or session.provider_options != provider_options
            ):
                raise _review_error("Continuity CUDA session permits CPU fallback.")

    def _detector_tensor(self, frame: SampledRgbFrame):
        import numpy as np

        image = np.frombuffer(frame.pixels, dtype=np.uint8).reshape(
            frame.height, frame.width, 3
        )
        ratio = min(
            self.profile.detector.input_height / frame.height,
            self.profile.detector.input_width / frame.width,
        )
        resized_width = max(1, int(frame.width * ratio))
        resized_height = max(1, int(frame.height * ratio))
        resized = _bilinear_resize(image, width=resized_width, height=resized_height)
        padded = np.full(
            (
                self.profile.detector.input_height,
                self.profile.detector.input_width,
                3,
            ),
            114.0,
            dtype=np.float32,
        )
        padded[:resized_height, :resized_width] = resized[:, :, ::-1]
        tensor = np.ascontiguousarray(padded.transpose(2, 0, 1)[None])
        return tensor, ratio

    def _embedding(self, frame: SampledRgbFrame, box: tuple[float, ...]):
        import numpy as np

        x1, y1, x2, y2 = box
        left = min(frame.width - 1, max(0, int(x1 * frame.width)))
        top = min(frame.height - 1, max(0, int(y1 * frame.height)))
        right = min(frame.width, max(left + 1, int(np.ceil(x2 * frame.width))))
        bottom = min(frame.height, max(top + 1, int(np.ceil(y2 * frame.height))))
        image = np.frombuffer(frame.pixels, dtype=np.uint8).reshape(
            frame.height, frame.width, 3
        )
        crop = image[top:bottom, left:right]
        resized = (
            _bilinear_resize(
                crop,
                width=self.profile.reid.input_width,
                height=self.profile.reid.input_height,
            )
            / 255.0
        )
        mean = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)
        tensor = np.ascontiguousarray(
            ((resized - mean) / std).transpose(2, 0, 1)[None],
            dtype=np.float32,
        )
        output = self._reid.run(
            [self.profile.reid.output_name],
            {self.profile.reid.input_name: tensor},
        )
        if len(output) != 1:
            raise _review_error("Continuity OSNet model returned invalid output.")
        vector = np.asarray(output[0], dtype=np.float32)
        if vector.shape != (1, self.profile.reid.output_dimensions):
            raise _review_error("Continuity OSNet model returned invalid output.")
        vector = vector[0]
        norm = float(np.linalg.norm(vector))
        if not np.isfinite(vector).all() or norm <= 0:
            raise _review_error("Continuity OSNet model returned invalid output.")
        return np.ascontiguousarray(vector / norm, dtype=np.float32)

    def _decoded_yolox_rows(self, raw, *, ratio: float, frame: SampledRgbFrame):
        import numpy as np

        rows = np.asarray(raw, dtype=np.float32)
        expected_count = sum(
            (self.profile.detector.input_height // stride)
            * (self.profile.detector.input_width // stride)
            for stride in self.profile.detector_decode_strides
        )
        if (
            rows.shape != (1, expected_count, self.profile.detector.output_dimensions)
            or not np.isfinite(rows).all()
        ):
            raise _review_error("Continuity YOLOX model returned invalid output.")
        grids = []
        expanded_strides = []
        for stride in self.profile.detector_decode_strides:
            height = self.profile.detector.input_height // stride
            width = self.profile.detector.input_width // stride
            x_grid, y_grid = np.meshgrid(np.arange(width), np.arange(height))
            grids.append(np.stack((x_grid, y_grid), axis=2).reshape(-1, 2))
            expanded_strides.append(
                np.full((height * width, 1), stride, dtype=np.float32)
            )
        grid = np.concatenate(grids, axis=0).astype(np.float32)
        strides = np.concatenate(expanded_strides, axis=0)
        decoded = rows[0].copy()
        decoded[:, :2] = (decoded[:, :2] + grid) * strides
        with np.errstate(over="ignore", invalid="ignore"):
            decoded[:, 2:4] = np.exp(decoded[:, 2:4]) * strides
        if not np.isfinite(decoded[:, :4]).all():
            raise _review_error("Continuity YOLOX model returned invalid boxes.")
        class_scores = decoded[:, 5:]
        subject_class_ids = np.asarray(self.profile.subject_class_ids, dtype=np.int64)
        subject_scores = decoded[:, 4, None] * class_scores[:, subject_class_ids]
        minimum = self.profile.detection_ambiguity_confidence_milli / 1000.0
        row_indices, subject_positions = np.nonzero(subject_scores >= minimum)
        decoded = decoded[row_indices]
        scores = subject_scores[row_indices, subject_positions]
        class_ids = subject_class_ids[subject_positions]
        if not len(decoded):
            return ()
        boxes = np.empty((len(decoded), 4), dtype=np.float32)
        boxes[:, 0] = (decoded[:, 0] - decoded[:, 2] / 2.0) / ratio
        boxes[:, 1] = (decoded[:, 1] - decoded[:, 3] / 2.0) / ratio
        boxes[:, 2] = (decoded[:, 0] + decoded[:, 2] / 2.0) / ratio
        boxes[:, 3] = (decoded[:, 1] + decoded[:, 3] / 2.0) / ratio
        boxes[:, (0, 2)] = np.clip(boxes[:, (0, 2)] / frame.width, 0.0, 1.0)
        boxes[:, (1, 3)] = np.clip(boxes[:, (1, 3)] / frame.height, 0.0, 1.0)
        valid = np.logical_and(boxes[:, 0] < boxes[:, 2], boxes[:, 1] < boxes[:, 3])
        boxes, scores, class_ids = boxes[valid], scores[valid], class_ids[valid]
        selected: list[int] = []
        for class_id in self.profile.subject_class_ids:
            indices = np.flatnonzero(class_ids == class_id)
            indices = indices[np.argsort(scores[indices])[::-1]]
            while len(indices):
                current = int(indices[0])
                selected.append(current)
                if len(indices) == 1:
                    break
                overlap = _iou(boxes[current], boxes[indices[1:]])
                indices = indices[1:][
                    overlap <= self.profile.detector_nms_iou_milli / 1000.0
                ]
        return tuple(
            (tuple(float(value) for value in boxes[index]), float(scores[index]))
            for index in sorted(selected, key=lambda item: scores[item], reverse=True)
        )

    def _detections(self, frame: SampledRgbFrame):
        tensor, ratio = self._detector_tensor(frame)
        output = self._detector.run(
            [self.profile.detector.output_name],
            {self.profile.detector.input_name: tensor},
        )
        if len(output) != 1:
            raise _review_error("Continuity YOLOX model returned invalid output.")
        rows = self._decoded_yolox_rows(output[0], ratio=ratio, frame=frame)
        selected = []
        uncertain_subject = False
        for box, score in rows:
            confidence = round(score * 1000)
            if confidence < self.profile.detection_confidence_milli:
                uncertain_subject = True
                continue
            selected.append((box, confidence, self._embedding(frame, box)))
        return tuple(selected), uncertain_subject


def yolox_osnet_assets(model_root: Path) -> ContinuityModelAssets:
    if not model_root.is_absolute():
        raise ValueError("continuity model root must be absolute")
    return ContinuityModelAssets(
        detector_path=model_root / YOLOX_S_FILENAME,
        reid_path=model_root / OSNET_X1_FILENAME,
    )


def create_yolox_osnet_profile(
    *,
    sampler: ToolIdentity,
    sample_width: int,
    sample_height: int,
    max_sample_count: int = 9,
) -> CudaContinuityVisualProfile:
    return CudaContinuityVisualProfile.create(
        profile_id="yolox-s-osnet-x1-msmt17-cuda",
        profile_version="1",
        sampler=sampler,
        sample_width=sample_width,
        sample_height=sample_height,
        numeric_runtime=ToolIdentity(
            name="numpy", version=importlib.metadata.version("numpy")
        ),
        inference_runtime=ToolIdentity(
            name="onnxruntime-gpu",
            version=importlib.metadata.version("onnxruntime-gpu"),
        ),
        cuda_libraries=tuple(
            ToolIdentity(
                name=package_name,
                version=importlib.metadata.version(package_name),
            )
            for package_name in CUDA_LIBRARY_PACKAGES
        ),
        detector=CudaContinuityOnnxModel.create(
            role="detector",
            content_sha256=(
                "c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063"
            ),
            size_bytes=35_858_002,
            input_name="images",
            output_name="output",
            input_width=640,
            input_height=640,
            opset=11,
            output_dimensions=85,
            source_repository="https://github.com/Megvii-BaseDetection/YOLOX",
            source_revision="0.1.1rc0/e1052df71842031413f6030723c3607b839c80ce",
            license_id="Apache-2.0",
            conversion_contract="upstream-release-onnx/no-conversion",
            preprocess_contract=("yolox-rgb-to-bgr-letterbox114-bilinear-float32/1"),
            output_contract="yolox-coco-raw/1",
        ),
        reid=CudaContinuityOnnxModel.create(
            role="reid",
            content_sha256=(
                "afea03904fab11c61e6a32b4e36a1cd5942875b4b3e4514c15de1e98d795173e"
            ),
            upstream_content_sha256=(
                "48df972f72887b95cf3b43b3a07c3a7d2398381aea0f9cae64a7ef11d512b727"
            ),
            size_bytes=8_728_948,
            input_name="images",
            output_name="output",
            input_width=128,
            input_height=256,
            opset=12,
            output_dimensions=512,
            source_repository="https://github.com/KaiyangZhou/deep-person-reid",
            source_revision=(
                "checkpoint-a5c5cc037c24235cda3b21085b93ad77c9616224/"
                "converter-f8cd150fdf77e8d9e1ed143b7f308c2c609ded50"
            ),
            license_id="MIT",
            conversion_contract=(
                "torch-2.9.0+cu128/onnx-1.19.1/opset-12/"
                "strict-state-dict/eval-fixed-batch-1"
            ),
            preprocess_contract="osnet-rgb-bilinear-float32-imagenet/1",
            output_contract="l2-embedding/1",
        ),
        tracker=ToolIdentity(name="deterministic-reid-tracker", version="2"),
        max_sample_count=max_sample_count,
        subject_class_ids=(0,),
        detection_confidence_milli=300,
        detection_ambiguity_confidence_milli=100,
        detector_nms_iou_milli=450,
        detector_decode_strides=(8, 16, 32),
        cuda_provider_options=(("device_id", "0"), ("use_tf32", "0")),
        reid_similarity_milli=650,
        track_similarity_margin_milli=50,
        minimum_coverage_milli=700,
        minimum_direction_delta_milli=150,
        minimum_direction_consistency_milli=750,
        edge_band_milli=150,
    )
