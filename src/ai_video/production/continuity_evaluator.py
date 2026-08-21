"""Local frame sampling and conservative Shot continuity measurements."""

from __future__ import annotations

import hashlib
import importlib.metadata
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from pydantic import Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import EvidenceStrength, StrictModel, ToolIdentity
from ai_video.production.review import (
    ContinuityCheckMeasurement,
    ContinuityEvaluationIntent,
    ContinuityHumanFallbackEvidence,
    ContinuitySampledFrameMeasurement,
    ContinuityTrackedSubjectFrameMeasurement,
    GeneratedShotContinuityEvidence,
    TrackedGeneratedShotContinuityMeasurements,
)
from ai_video.production.video import ResolvedVideoGenerationRequest
from ai_video.production.video_artifact import MeasuredVideoMetadata


class ContinuityOnnxModel(StrictModel):
    role: Literal["detector", "reid"]
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(strict=True, gt=0)
    input_name: str = Field(min_length=1)
    output_name: str = Field(min_length=1)
    input_width: int = Field(strict=True, gt=0)
    input_height: int = Field(strict=True, gt=0)
    source_repository: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    license_id: str = Field(min_length=1)
    output_contract: Literal[
        "normalized-xyxy-score-class/1",
        "l2-embedding/1",
    ]

    @model_validator(mode="after")
    def _validate_role_contract(self) -> "ContinuityOnnxModel":
        expected = (
            "normalized-xyxy-score-class/1"
            if self.role == "detector"
            else "l2-embedding/1"
        )
        if self.output_contract != expected:
            raise ValueError("continuity ONNX role does not match output contract")
        return self

    @classmethod
    def create(cls, **values: object) -> "ContinuityOnnxModel":
        return cls.model_validate(values)


class ContinuityVisualProfile(StrictModel):
    schema_version: Literal["continuity-visual-profile/1"] = (
        "continuity-visual-profile/1"
    )
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    sampler: ToolIdentity
    sample_width: int = Field(strict=True, gt=0)
    sample_height: int = Field(strict=True, gt=0)
    preprocess_contract: Literal["rgb24-nearest-chw-float32-0-1/1"] = (
        "rgb24-nearest-chw-float32-0-1/1"
    )
    numeric_runtime: ToolIdentity
    inference_runtime: ToolIdentity
    detector: ContinuityOnnxModel
    reid: ContinuityOnnxModel
    tracker: ToolIdentity
    max_sample_count: int = Field(strict=True, ge=3)
    subject_class_ids: tuple[int, ...] = Field(min_length=1)
    detection_confidence_milli: int = Field(strict=True, ge=1, le=1000)
    reid_similarity_milli: int = Field(strict=True, ge=1, le=1000)
    track_similarity_margin_milli: int = Field(strict=True, ge=0, le=1000)
    minimum_coverage_milli: int = Field(strict=True, ge=1, le=1000)
    minimum_direction_delta_milli: int = Field(strict=True, ge=1, le=1000)
    minimum_direction_consistency_milli: int = Field(
        strict=True, ge=1, le=1000
    )
    edge_band_milli: int = Field(strict=True, ge=1, lt=500)
    execution_providers: tuple[Literal["CPUExecutionProvider"], ...] = (
        "CPUExecutionProvider",
    )
    profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_profile(self) -> "ContinuityVisualProfile":
        if self.detector.role != "detector" or self.reid.role != "reid":
            raise ValueError("continuity visual profile model roles are invalid")
        if self.subject_class_ids != tuple(sorted(set(self.subject_class_ids))):
            raise ValueError("continuity subject class IDs must be unique and ordered")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"profile_content_hash"})
        )
        if self.profile_content_hash != expected:
            raise ValueError("continuity visual profile hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "ContinuityVisualProfile":
        data = dict(values)
        provisional = cls.model_construct(**data, profile_content_hash="0" * 64)
        data["profile_content_hash"] = canonical_sha256(
            provisional.model_dump(
                mode="json",
                exclude={"profile_content_hash"},
                warnings=False,
            )
        )
        return cls.model_validate(data)


@dataclass(frozen=True)
class ContinuityModelAssets:
    detector_path: Path
    reid_path: Path


class OnnxSession(Protocol):
    def run(self, output_names: list[str], inputs: dict[str, object]) -> list[object]: ...


class OnnxSessionFactory(Protocol):
    def __call__(
        self, model_bytes: bytes, providers: tuple[str, ...]
    ) -> OnnxSession: ...


def _default_session_factory(
    model_bytes: bytes, providers: tuple[str, ...]
) -> OnnxSession:
    try:
        import onnxruntime as ort  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - dependency gate
        raise _review_error("Continuity ONNX runtime dependency is unavailable.") from exc
    return ort.InferenceSession(model_bytes, providers=list(providers))


def _read_model_bytes(path: Path, expected: ContinuityOnnxModel) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise _review_error("Continuity model bytes could not be opened.", type(exc).__name__) from exc
    try:
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or opened.st_size != expected.size_bytes
        ):
            raise _review_error("Continuity model bytes do not match the sealed profile.")
        payload = bytearray()
        while chunk := os.read(fd, 1024 * 1024):
            payload.extend(chunk)
    finally:
        os.close(fd)
    data = bytes(payload)
    if hashlib.sha256(data).hexdigest() != expected.content_sha256:
        raise _review_error("Continuity model bytes do not match the sealed profile.")
    return data


class OnnxSubjectTrackerBackend:
    """CPU-only sealed ONNX sessions; tracking is implemented below."""

    def __init__(
        self,
        *,
        profile: ContinuityVisualProfile,
        assets: ContinuityModelAssets,
        session_factory: OnnxSessionFactory = _default_session_factory,
    ) -> None:
        expected_runtimes = (
            (profile.numeric_runtime, "numpy"),
            (profile.inference_runtime, "onnxruntime"),
        )
        for identity, package_name in expected_runtimes:
            try:
                installed_version = importlib.metadata.version(package_name)
            except importlib.metadata.PackageNotFoundError as exc:
                raise _review_error(
                    "Continuity visual runtime dependency is unavailable.",
                    package_name,
                ) from exc
            if identity != ToolIdentity(
                name=package_name, version=installed_version
            ):
                raise _review_error(
                    "Continuity visual runtime does not match the sealed profile.",
                    package_name,
                )
        detector_bytes = _read_model_bytes(assets.detector_path, profile.detector)
        reid_bytes = _read_model_bytes(assets.reid_path, profile.reid)
        self.profile = profile
        self._detector = session_factory(detector_bytes, profile.execution_providers)
        self._reid = session_factory(reid_bytes, profile.execution_providers)

    @staticmethod
    def _rgb_tensor(frame: "SampledRgbFrame", width: int, height: int):
        import numpy as np

        image = np.frombuffer(frame.pixels, dtype=np.uint8).reshape(
            frame.height, frame.width, 3
        )
        y_indices = np.linspace(0, frame.height - 1, height).round().astype(int)
        x_indices = np.linspace(0, frame.width - 1, width).round().astype(int)
        resized = image[y_indices][:, x_indices]
        return np.ascontiguousarray(
            resized.transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        )

    def _embedding(self, frame: "SampledRgbFrame", box: tuple[float, ...]):
        import numpy as np

        x1, y1, x2, y2 = box
        left = min(frame.width - 1, max(0, int(x1 * frame.width)))
        top = min(frame.height - 1, max(0, int(y1 * frame.height)))
        right = min(frame.width, max(left + 1, int(np.ceil(x2 * frame.width))))
        bottom = min(frame.height, max(top + 1, int(np.ceil(y2 * frame.height))))
        image = np.frombuffer(frame.pixels, dtype=np.uint8).reshape(
            frame.height, frame.width, 3
        )
        crop = np.ascontiguousarray(image[top:bottom, left:right])
        crop_frame = SampledRgbFrame(
            frame_index=frame.frame_index,
            width=right - left,
            height=bottom - top,
            pixels=crop.tobytes(),
        )
        tensor = self._rgb_tensor(
            crop_frame, self.profile.reid.input_width, self.profile.reid.input_height
        )
        output = self._reid.run(
            [self.profile.reid.output_name],
            {self.profile.reid.input_name: tensor},
        )
        if len(output) != 1:
            raise _review_error("Continuity ReID model returned invalid output.")
        vector = np.asarray(output[0], dtype=np.float32)
        if vector.ndim != 2 or vector.shape[0] != 1 or vector.shape[1] < 2:
            raise _review_error("Continuity ReID model returned invalid output.")
        vector = vector[0]
        norm = float(np.linalg.norm(vector))
        if not np.isfinite(vector).all() or norm <= 0:
            raise _review_error("Continuity ReID model returned invalid output.")
        return np.ascontiguousarray(vector / norm, dtype=np.float32)

    def _detections(self, frame: "SampledRgbFrame"):
        import numpy as np

        tensor = self._rgb_tensor(
            frame,
            self.profile.detector.input_width,
            self.profile.detector.input_height,
        )
        output = self._detector.run(
            [self.profile.detector.output_name],
            {self.profile.detector.input_name: tensor},
        )
        if len(output) != 1:
            raise _review_error("Continuity detector returned invalid output.")
        rows = np.asarray(output[0], dtype=np.float32)
        if rows.ndim != 2 or rows.shape[1] != 6 or not np.isfinite(rows).all():
            raise _review_error("Continuity detector returned invalid output.")
        selected = []
        uncertain_subject = False
        for x1, y1, x2, y2, score, class_id in rows:
            rounded_class = int(round(float(class_id)))
            if (
                abs(float(class_id) - rounded_class) > 1e-6
                or not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1)
                or not 0 <= score <= 1
            ):
                raise _review_error("Continuity detector returned invalid normalized boxes.")
            if rounded_class not in self.profile.subject_class_ids:
                continue
            if (
                round(float(score) * 1000)
                < self.profile.detection_confidence_milli
            ):
                uncertain_subject = True
                continue
            box = (float(x1), float(y1), float(x2), float(y2))
            selected.append(
                (box, round(float(score) * 1000), self._embedding(frame, box))
            )
        return tuple(selected), uncertain_subject

    def track(
        self, frames: tuple["SampledRgbFrame", ...]
    ) -> tuple["TrackedSubjectObservation", ...]:
        import numpy as np

        reference = None
        identity = None
        observations: list[TrackedSubjectObservation] = []
        for frame in frames:
            candidates, uncertain_subject = self._detections(frame)
            if uncertain_subject:
                observations.append(
                    TrackedSubjectObservation(
                        frame_index=frame.frame_index, state="ambiguous"
                    )
                )
                continue
            if not candidates:
                observations.append(
                    TrackedSubjectObservation(frame_index=frame.frame_index, state="absent")
                )
                continue
            if reference is None:
                if len(candidates) != 1:
                    observations.append(
                        TrackedSubjectObservation(
                            frame_index=frame.frame_index, state="ambiguous"
                        )
                    )
                    continue
                selected = candidates[0]
                reference = selected[2]
                identity = hashlib.sha256(reference.tobytes()).hexdigest()
            else:
                ranked = sorted(
                    (
                        round(float(np.dot(reference, candidate[2])) * 1000),
                        candidate,
                    )
                    for candidate in candidates
                )
                best_similarity, selected = ranked[-1]
                second_similarity = ranked[-2][0] if len(ranked) > 1 else -1000
                if (
                    best_similarity < self.profile.reid_similarity_milli
                    or best_similarity - second_similarity
                    < self.profile.track_similarity_margin_milli
                ):
                    observations.append(
                        TrackedSubjectObservation(
                            frame_index=frame.frame_index, state="ambiguous"
                        )
                    )
                    continue
            box, confidence, _ = selected
            observations.append(
                TrackedSubjectObservation(
                    frame_index=frame.frame_index,
                    state="present",
                    x_min_milli=round(box[0] * 1000),
                    x_max_milli=round(box[2] * 1000),
                    detection_confidence_milli=confidence,
                    track_identity=identity,
                )
            )
        return tuple(observations)


@dataclass(frozen=True)
class SampledRgbFrame:
    frame_index: int
    width: int
    height: int
    pixels: bytes

    def __post_init__(self) -> None:
        if (
            self.frame_index < 0
            or self.width <= 0
            or self.height <= 0
            or len(self.pixels) != self.width * self.height * 3
        ):
            raise ValueError("sampled RGB frame is invalid")


@dataclass(frozen=True)
class TrackedSubjectObservation:
    frame_index: int
    state: Literal["present", "absent", "ambiguous"]
    x_min_milli: int | None = None
    x_max_milli: int | None = None
    detection_confidence_milli: int | None = None
    track_identity: str | None = None

    def __post_init__(self) -> None:
        values = (
            self.x_min_milli,
            self.x_max_milli,
            self.detection_confidence_milli,
            self.track_identity,
        )
        if self.frame_index < 0:
            raise ValueError("tracked subject frame index is invalid")
        if self.state == "present":
            if any(value is None for value in values):
                raise ValueError("present tracked subjects require identity, box, and confidence")
            if (
                not 0 <= self.x_min_milli < self.x_max_milli <= 1000  # type: ignore[operator]
                or not 0 <= self.detection_confidence_milli <= 1000  # type: ignore[operator]
            ):
                raise ValueError("tracked subject measurement is invalid")
        elif any(value is not None for value in values):
            raise ValueError("non-present tracked subjects cannot claim an identity")


class ContinuitySubjectTracker(Protocol):
    profile: ContinuityVisualProfile

    def track(
        self, frames: tuple[SampledRgbFrame, ...]
    ) -> tuple[TrackedSubjectObservation, ...]: ...


class HumanContinuityFallback(Protocol):
    def __call__(
        self,
        held_fd: int,
        request: ResolvedVideoGenerationRequest,
        measured: MeasuredVideoMetadata,
        qa_policy_content_hash: str,
    ) -> GeneratedShotContinuityEvidence: ...


class ContinuityRgbFrameSampler(Protocol):
    identity: ToolIdentity
    sample_width: int
    sample_height: int

    def sample(
        self,
        held_fd: int,
        measured: MeasuredVideoMetadata,
        frame_indices: tuple[int, ...],
    ) -> tuple[SampledRgbFrame, ...]: ...


@dataclass(frozen=True)
class FfmpegRgbFrameSampler:
    executable: Path
    identity: ToolIdentity
    sample_width: int
    sample_height: int
    timeout_seconds: int = 30

    def __post_init__(self) -> None:
        if (
            not self.executable.is_absolute()
            or self.sample_width <= 0
            or self.sample_height <= 0
            or self.timeout_seconds <= 0
        ):
            raise ValueError("ffmpeg RGB continuity sampler configuration is invalid")

    def sample(
        self,
        held_fd: int,
        measured: MeasuredVideoMetadata,
        frame_indices: tuple[int, ...],
    ) -> tuple[SampledRgbFrame, ...]:
        del measured
        if not frame_indices or frame_indices != tuple(sorted(set(frame_indices))):
            raise _review_error("Continuity frame sample indices are invalid.")
        selection = "+".join(f"eq(n\\,{index})" for index in frame_indices)
        argv = [
            str(self.executable),
            "-v",
            "error",
            "-nostdin",
            "-i",
            f"/proc/self/fd/{held_fd}",
            "-vf",
            (
                f"select={selection},scale={self.sample_width}:{self.sample_height}:"
                "flags=area,format=rgb24"
            ),
            "-vsync",
            "0",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ]
        try:
            result = subprocess.run(
                argv,
                capture_output=True,
                check=False,
                env={"LANG": "C", "LC_ALL": "C"},
                pass_fds=(held_fd,),
                timeout=self.timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise _review_error(
                "Continuity RGB frame sampling failed.", type(exc).__name__
            ) from exc
        frame_size = self.sample_width * self.sample_height * 3
        if result.returncode != 0 or len(result.stdout) != frame_size * len(frame_indices):
            detail = result.stderr.decode("utf-8", errors="replace")[:500]
            raise _review_error(
                "Continuity RGB frame sampling returned invalid output.", detail
            )
        return tuple(
            SampledRgbFrame(
                frame_index=frame_index,
                width=self.sample_width,
                height=self.sample_height,
                pixels=result.stdout[offset * frame_size : (offset + 1) * frame_size],
            )
            for offset, frame_index in enumerate(frame_indices)
        )


def _review_error(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.REVIEW_EVIDENCE_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _sample_indices(frame_count: int, maximum: int) -> tuple[int, ...]:
    if frame_count < 2:
        raise _review_error("Continuity evaluation requires at least two frames.")
    if frame_count <= maximum:
        return tuple(range(frame_count))
    last = frame_count - 1
    return tuple(round(position * last / (maximum - 1)) for position in range(maximum))


def _screen_edge(value: str, *, action: str | None = None) -> str | None:
    normalized = value.casefold().replace("_", "-").replace(" ", "-")
    if action == "entrance" and not any(
        token in normalized for token in ("enter", "entrance")
    ):
        return None
    if action == "exit" and not any(
        token in normalized for token in ("exit", "leave", "leaving")
    ):
        return None
    if any(token in normalized for token in ("screen-right", "rightward", "left-to-right")):
        return "right"
    if any(token in normalized for token in ("screen-left", "leftward", "right-to-left")):
        return "left"
    return None


def _not_evaluated(expected: str, rationale: str) -> ContinuityCheckMeasurement:
    return ContinuityCheckMeasurement(
        status="not_evaluated",
        expected=expected,
        observed=None,
        confidence_milli=None,
        rationale=rationale,
    )


def _evaluated(
    *, expected: str, observed: str, matches: bool, confidence_milli: int, rationale: str
) -> ContinuityCheckMeasurement:
    return ContinuityCheckMeasurement(
        status="match" if matches else "mismatch",
        expected=expected,
        observed=observed,
        confidence_milli=confidence_milli,
        rationale=rationale,
    )


class HybridContinuityEvaluatorV1:
    """Measure bounded tracked continuity and defer unsupported semantics to humans."""

    def __init__(
        self,
        *,
        sampler: ContinuityRgbFrameSampler,
        evaluator: ToolIdentity,
        tracker: ContinuitySubjectTracker,
        human_fallback: HumanContinuityFallback | None = None,
        human_fallback_identity: ToolIdentity | None = None,
    ) -> None:
        if (human_fallback is None) != (human_fallback_identity is None):
            raise ValueError("continuity human fallback identity is incomplete")
        self._sampler = sampler
        self._evaluator = evaluator
        self._tracker = tracker
        self._human_fallback = human_fallback
        self._human_fallback_identity = human_fallback_identity

    def _evaluation_profile_content_hash(self) -> str:
        if self._human_fallback_identity is None:
            return self._tracker.profile.profile_content_hash
        return canonical_sha256(
            {
                "schema": "hybrid-continuity-evaluator-profile/1",
                "visual_profile_content_hash": (
                    self._tracker.profile.profile_content_hash
                ),
                "human_fallback": self._human_fallback_identity.model_dump(
                    mode="json"
                ),
            }
        )

    def create_intent(
        self,
        request: ResolvedVideoGenerationRequest,
        measured: MeasuredVideoMetadata,
        qa_policy_content_hash: str,
    ) -> ContinuityEvaluationIntent:
        binding = request.continuity_binding
        original = request.activation_scope.request if request.activation_scope else None
        if binding is None or original is None:
            raise _review_error(
                "Durable continuity evaluation requires a sealed tracked backend."
            )
        return ContinuityEvaluationIntent.create(
            source_shot_id=binding.terminal_frame.source_shot_id,
            target_shot_id=original.target_shot_id,
            target_shot_content_hash=original.target_shot_content_hash,
            resolved_generation_hash=request.resolved_generation_hash,
            artifact_sha256=measured.artifact_sha256,
            continuity_constraints_hash=binding.constraints.content_hash,
            qa_policy_content_hash=qa_policy_content_hash,
            evaluator=self._evaluator,
            evaluator_profile_content_hash=self._evaluation_profile_content_hash(),
        )

    def _invoke_human_fallback(
        self,
        held_fd: int,
        request: ResolvedVideoGenerationRequest,
        measured: MeasuredVideoMetadata,
        qa_policy_content_hash: str,
    ) -> GeneratedShotContinuityEvidence | None:
        fallback = self._human_fallback
        expected_identity = self._human_fallback_identity
        if fallback is None or expected_identity is None:
            return None
        position = os.lseek(held_fd, 0, os.SEEK_CUR)
        fallback_fd = os.dup(held_fd)
        try:
            os.lseek(fallback_fd, 0, os.SEEK_SET)
            evidence = fallback(
                fallback_fd, request, measured, qa_policy_content_hash
            )
        finally:
            try:
                os.close(fallback_fd)
            except OSError:
                pass
            os.lseek(held_fd, position, os.SEEK_SET)
        binding = request.continuity_binding
        original = request.activation_scope.request if request.activation_scope else None
        if (
            binding is None
            or original is None
            or not isinstance(evidence, GeneratedShotContinuityEvidence)
            or evidence.strength is not EvidenceStrength.HUMAN
            or evidence.evaluator != expected_identity
            or not evidence.coverage_complete
            or evidence.source_shot_id != binding.terminal_frame.source_shot_id
            or evidence.target_shot_id != original.target_shot_id
            or evidence.target_shot_content_hash != original.target_shot_content_hash
            or evidence.resolved_generation_hash != request.resolved_generation_hash
            or evidence.artifact_sha256 != measured.artifact_sha256
            or evidence.continuity_constraints_hash != binding.constraints.content_hash
            or evidence.qa_policy_content_hash != qa_policy_content_hash
        ):
            raise _review_error(
                "Human continuity fallback does not bind complete exact evidence."
            )
        return evidence

    def __call__(
        self,
        held_fd: int,
        request: ResolvedVideoGenerationRequest,
        measured: MeasuredVideoMetadata,
        qa_policy_content_hash: str,
    ) -> GeneratedShotContinuityEvidence:
        return self._evaluate_tracked(
            held_fd, request, measured, qa_policy_content_hash
        )

    def _evaluate_tracked(
        self,
        held_fd: int,
        request: ResolvedVideoGenerationRequest,
        measured: MeasuredVideoMetadata,
        qa_policy_content_hash: str,
    ) -> GeneratedShotContinuityEvidence:
        binding = request.continuity_binding
        original = request.activation_scope.request if request.activation_scope else None
        tracker = self._tracker
        if binding is None or original is None:
            raise _review_error("Continuity evaluator requires an exact activation binding.")
        if self._sampler.identity != tracker.profile.sampler:
            raise _review_error("Continuity sampler does not match the sealed visual profile.")
        if (
            self._sampler.sample_width != tracker.profile.sample_width
            or self._sampler.sample_height != tracker.profile.sample_height
        ):
            raise _review_error(
                "Continuity sample geometry does not match the sealed visual profile."
            )

        position = os.lseek(held_fd, 0, os.SEEK_CUR)
        digest = hashlib.sha256()
        size_bytes = 0
        try:
            os.lseek(held_fd, 0, os.SEEK_SET)
            while chunk := os.read(held_fd, 1024 * 1024):
                size_bytes += len(chunk)
                digest.update(chunk)
            if (
                size_bytes != measured.size_bytes
                or digest.hexdigest() != measured.artifact_sha256
            ):
                raise _review_error(
                    "Continuity evaluator artifact does not match measured MP4 evidence."
                )
            frame_indices = _sample_indices(
                measured.frame_count, tracker.profile.max_sample_count
            )
            os.lseek(held_fd, 0, os.SEEK_SET)
            frames = self._sampler.sample(held_fd, measured, frame_indices)
            observations = tracker.track(frames)
        finally:
            os.lseek(held_fd, position, os.SEEK_SET)

        if (
            len(frames) != len(frame_indices)
            or tuple(item.frame_index for item in frames) != frame_indices
            or len({(item.width, item.height) for item in frames}) != 1
            or any(
                item.width != tracker.profile.sample_width
                or item.height != tracker.profile.sample_height
                for item in frames
            )
            or tuple(item.frame_index for item in observations) != frame_indices
        ):
            raise _review_error("Continuity subject tracker returned incomplete coverage.")
        profile = tracker.profile
        usable = tuple(item for item in observations if item.state != "ambiguous")
        coverage_milli = round(len(usable) * 1000 / len(observations))
        present = tuple(item for item in observations if item.state == "present")
        identities = {item.track_identity for item in present}
        confident = (
            coverage_milli >= profile.minimum_coverage_milli
            and bool(present)
            and len(identities) == 1
            and min(item.detection_confidence_milli for item in present)
            >= profile.detection_confidence_milli
        )
        constraints = binding.constraints

        def unavailable(expected: str, detail: str) -> ContinuityCheckMeasurement:
            return _not_evaluated(expected, detail)

        if not confident:
            reason = "Subject track coverage, confidence, or identity stability is insufficient."
            motion = unavailable(constraints.motion_direction, reason)
            entrance = unavailable(constraints.entrance_state, reason)
            exit_state = unavailable(constraints.exit_state, reason)
            reentry = unavailable("absent", reason)
        else:
            track_identity = next(iter(identities))
            entrance_pair = next(
                (
                    (left, right)
                    for left, right in zip(observations, observations[1:])
                    if left.state == "absent"
                    and right.state == "present"
                    and right.track_identity == track_identity
                ),
                None,
            )
            exit_pair = next(
                (
                    (index, left, right)
                    for index, (left, right) in enumerate(
                        zip(observations, observations[1:])
                    )
                    if left.state == "present"
                    and left.track_identity == track_identity
                    and right.state == "absent"
                ),
                None,
            )
            motion_limit = exit_pair[0] + 1 if exit_pair is not None else len(observations)
            motion_present = tuple(
                item
                for item in observations[:motion_limit]
                if item.state == "present" and item.track_identity == track_identity
            )
            deltas = tuple(
                ((right.x_min_milli + right.x_max_milli) // 2)
                - ((left.x_min_milli + left.x_max_milli) // 2)
                for left, right in zip(motion_present, motion_present[1:])
            )
            expected_motion = _screen_edge(constraints.motion_direction)
            if expected_motion is None or not deltas:
                motion = unavailable(
                    constraints.motion_direction,
                    "Motion grammar is unsupported or the trusted track is too short.",
                )
            else:
                total_delta = sum(deltas)
                observed_motion = (
                    "right" if total_delta > 0 else "left" if total_delta < 0 else "stationary"
                )
                same_direction = sum(
                    delta > 0 if observed_motion == "right" else delta < 0
                    for delta in deltas
                )
                consistency_milli = round(same_direction * 1000 / len(deltas))
                if (
                    abs(total_delta) < profile.minimum_direction_delta_milli
                    or consistency_milli < profile.minimum_direction_consistency_milli
                ):
                    motion = unavailable(
                        constraints.motion_direction,
                        "Trusted track direction is below displacement or consistency gates.",
                    )
                else:
                    motion = _evaluated(
                        expected=expected_motion,
                        observed=observed_motion,
                        matches=observed_motion == expected_motion,
                        confidence_milli=min(coverage_milli, consistency_milli),
                        rationale="Measured signed centers of one stable subject track.",
                    )

            def observed_edge(item: TrackedSubjectObservation) -> str:
                touches_left = item.x_min_milli <= profile.edge_band_milli
                touches_right = item.x_max_milli >= 1000 - profile.edge_band_milli
                if touches_left == touches_right:
                    return "interior"
                if touches_left:
                    return "left"
                return "right"

            expected_entrance = _screen_edge(
                constraints.entrance_state, action="entrance"
            )
            if expected_entrance is None or entrance_pair is None:
                entrance = unavailable(
                    constraints.entrance_state,
                    "Entrance grammar or a signed absent-to-present crossing is unavailable.",
                )
            else:
                edge = observed_edge(entrance_pair[1])
                entrance = (
                    unavailable(
                        constraints.entrance_state,
                        "Sparse sampling did not observe the entrance at a screen edge.",
                    )
                    if edge == "interior"
                    else _evaluated(
                        expected=expected_entrance,
                        observed=edge,
                        matches=edge == expected_entrance,
                        confidence_milli=coverage_milli,
                        rationale=(
                            "Measured an absent-to-present crossing for the trusted track."
                        ),
                    )
                )

            expected_exit = _screen_edge(constraints.exit_state, action="exit")
            if expected_exit is None or exit_pair is None:
                exit_state = unavailable(
                    constraints.exit_state,
                    "Exit grammar or a signed present-to-absent crossing is unavailable.",
                )
                reentry = unavailable(
                    "absent", "Unexpected re-entry requires a trusted prior exit crossing."
                )
            else:
                edge = observed_edge(exit_pair[1])
                if edge == "interior":
                    exit_state = unavailable(
                        constraints.exit_state,
                        "Sparse sampling did not observe the exit at a screen edge.",
                    )
                    reentry = unavailable(
                        "absent",
                        "Unexpected re-entry requires a trusted prior screen-edge exit.",
                    )
                else:
                    exit_state = _evaluated(
                        expected=expected_exit,
                        observed=edge,
                        matches=edge == expected_exit,
                        confidence_milli=coverage_milli,
                        rationale=(
                            "Measured a present-to-absent crossing for the trusted track."
                        ),
                    )
                    returned = any(
                        item.state == "present"
                        and item.track_identity == track_identity
                        for item in observations[exit_pair[0] + 2 :]
                    )
                    reentry = _evaluated(
                        expected="absent",
                        observed="present" if returned else "absent",
                        matches=not returned,
                        confidence_milli=coverage_milli,
                        rationale=(
                            "Checked the same ReID track after its trusted exit crossing."
                        ),
                    )

        identity = _not_evaluated(
            str(tuple(item.artifact_id for item in constraints.character_identities)),
            "Track ReID is not canonical Character identity; human fallback is required.",
        )
        camera_axis = _not_evaluated(
            constraints.camera_axis,
            "No trusted camera-axis backend is configured; human fallback is required.",
        )
        framing = _not_evaluated(
            constraints.framing,
            "No trusted framing backend is configured; human fallback is required.",
        )
        automatic_checks = (
            identity,
            camera_axis,
            framing,
            motion,
            entrance,
            exit_state,
            reentry,
        )
        fallback_evidence = None
        if (
            not any(item.status == "mismatch" for item in automatic_checks)
            and any(item.status == "not_evaluated" for item in automatic_checks)
        ):
            fallback_evidence = self._invoke_human_fallback(
                held_fd, request, measured, qa_policy_content_hash
            )

        def merge_human(
            automatic: ContinuityCheckMeasurement, matches: bool
        ) -> ContinuityCheckMeasurement:
            if not matches:
                return _evaluated(
                    expected=automatic.expected,
                    observed="human-rejected",
                    matches=False,
                    confidence_milli=1000,
                    rationale="Rejected by exact human fallback evidence.",
                )
            if automatic.status != "not_evaluated":
                return automatic
            return _evaluated(
                expected=automatic.expected,
                observed="human-confirmed",
                matches=True,
                confidence_milli=1000,
                rationale="Resolved by exact human fallback evidence.",
            )

        if fallback_evidence is not None:
            identity = merge_human(identity, fallback_evidence.identity_match)
            camera_axis = merge_human(
                camera_axis, fallback_evidence.camera_axis_match
            )
            framing = merge_human(framing, fallback_evidence.framing_match)
            motion = merge_human(
                motion, fallback_evidence.motion_direction_match
            )
            entrance = merge_human(
                entrance, fallback_evidence.entrance_state_match
            )
            exit_state = merge_human(
                exit_state, fallback_evidence.exit_state_match
            )
            reentry = merge_human(
                reentry, not fallback_evidence.unexpected_reentry
            )
        measurements = TrackedGeneratedShotContinuityMeasurements(
            measurement_contract_version="tracked-continuity-evaluator/1",
            sampler=self._sampler.identity,
            evaluator_profile_content_hash=self._evaluation_profile_content_hash(),
            artifact_sha256=measured.artifact_sha256,
            sample_width=frames[0].width,
            sample_height=frames[0].height,
            sampled_frames=tuple(
                ContinuitySampledFrameMeasurement(
                    frame_index=item.frame_index,
                    frame_sha256=hashlib.sha256(item.pixels).hexdigest(),
                )
                for item in frames
            ),
            subject_track=tuple(
                ContinuityTrackedSubjectFrameMeasurement(
                    frame_index=item.frame_index,
                    state=item.state,
                    x_min_milli=item.x_min_milli,
                    x_max_milli=item.x_max_milli,
                    detection_confidence_milli=item.detection_confidence_milli,
                    track_identity=item.track_identity,
                )
                for item in observations
            ),
            fallback_evidence=(
                ContinuityHumanFallbackEvidence.from_generated(
                    fallback_evidence
                )
                if fallback_evidence is not None
                else None
            ),
            identity=identity,
            camera_axis=camera_axis,
            framing=framing,
            motion_direction=motion,
            entrance_state=entrance,
            exit_state=exit_state,
            unexpected_reentry=reentry,
        )
        checks = (identity, camera_axis, framing, motion, entrance, exit_state, reentry)
        return GeneratedShotContinuityEvidence.create(
            source_shot_id=binding.terminal_frame.source_shot_id,
            target_shot_id=original.target_shot_id,
            target_shot_content_hash=original.target_shot_content_hash,
            resolved_generation_hash=request.resolved_generation_hash,
            artifact_sha256=measured.artifact_sha256,
            continuity_constraints_hash=constraints.content_hash,
            qa_policy_content_hash=qa_policy_content_hash,
            evaluator=self._evaluator,
            strength=(
                EvidenceStrength.HUMAN
                if fallback_evidence is not None
                else EvidenceStrength.EXPLICIT_EVALUATOR
            ),
            coverage_complete=all(item.status != "not_evaluated" for item in checks),
            identity_match=identity.status == "match",
            camera_axis_match=camera_axis.status == "match",
            framing_match=framing.status == "match",
            motion_direction_match=motion.status == "match",
            entrance_state_match=entrance.status == "match",
            exit_state_match=exit_state.status == "match",
            unexpected_reentry=reentry.status == "mismatch",
            raw_measurements=measurements,
            rationale=(
                "Automatic exact subject-track measurements recorded"
                + (
                    " and incomplete dimensions resolved by bound human fallback."
                    if fallback_evidence is not None
                    else "; unsupported semantic dimensions require human fallback."
                )
            ),
        )
