"""Local frame sampling and conservative Shot continuity measurements."""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import EvidenceStrength, ToolIdentity
from ai_video.production.review import (
    ContinuityCheckMeasurement,
    ContinuitySampledFrameMeasurement,
    ContinuityTransitionMeasurement,
    GeneratedShotContinuityEvidence,
    GeneratedShotContinuityMeasurements,
)
from ai_video.production.video import ResolvedVideoGenerationRequest
from ai_video.production.video_artifact import MeasuredVideoMetadata


_MINIMUM_CONFIDENCE_MILLI = 500


@dataclass(frozen=True)
class SampledGrayFrame:
    frame_index: int
    width: int
    height: int
    pixels: bytes

    def __post_init__(self) -> None:
        if (
            self.frame_index < 0
            or self.width <= 0
            or self.height <= 0
            or len(self.pixels) != self.width * self.height
        ):
            raise ValueError("sampled grayscale frame is invalid")


class ContinuityFrameSampler(Protocol):
    identity: ToolIdentity

    def sample(
        self,
        held_fd: int,
        measured: MeasuredVideoMetadata,
        frame_indices: tuple[int, ...],
    ) -> tuple[SampledGrayFrame, ...]: ...


@dataclass(frozen=True)
class FfmpegGrayFrameSampler:
    executable: Path
    identity: ToolIdentity
    sample_width: int = 64
    sample_height: int = 36
    timeout_seconds: int = 30

    def __post_init__(self) -> None:
        if (
            not self.executable.is_absolute()
            or self.sample_width <= 0
            or self.sample_height <= 0
            or self.timeout_seconds <= 0
        ):
            raise ValueError("ffmpeg continuity sampler configuration is invalid")

    def sample(
        self,
        held_fd: int,
        measured: MeasuredVideoMetadata,
        frame_indices: tuple[int, ...],
    ) -> tuple[SampledGrayFrame, ...]:
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
                "flags=area,format=gray"
            ),
            "-vsync",
            "0",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "gray",
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
                "Continuity frame sampling failed.", type(exc).__name__
            ) from exc
        frame_size = self.sample_width * self.sample_height
        if result.returncode != 0 or len(result.stdout) != frame_size * len(frame_indices):
            detail = result.stderr.decode("utf-8", errors="replace")[:500]
            raise _review_error("Continuity frame sampling returned invalid output.", detail)
        return tuple(
            SampledGrayFrame(
                frame_index=frame_index,
                width=self.sample_width,
                height=self.sample_height,
                pixels=result.stdout[offset * frame_size : (offset + 1) * frame_size],
            )
            for offset, frame_index in enumerate(frame_indices)
        )


@dataclass(frozen=True)
class ContinuityEvaluatorConfig:
    max_sample_count: int = 9
    pixel_delta_threshold: int = 64
    minimum_changed_pixels: int = 2
    maximum_changed_fraction_milli: int = 600
    minimum_direction_delta_milli: int = 150
    edge_band_milli: int = 200

    def __post_init__(self) -> None:
        if (
            self.max_sample_count < 3
            or not 1 <= self.pixel_delta_threshold <= 255
            or self.minimum_changed_pixels < 1
            or not 1 <= self.maximum_changed_fraction_milli <= 1000
            or not 1 <= self.minimum_direction_delta_milli <= 1000
            or not 1 <= self.edge_band_milli < 500
        ):
            raise ValueError("continuity evaluator configuration is invalid")


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


def _transition(
    left: SampledGrayFrame,
    right: SampledGrayFrame,
    config: ContinuityEvaluatorConfig,
) -> ContinuityTransitionMeasurement:
    changed = tuple(
        index
        for index, (before, after) in enumerate(zip(left.pixels, right.pixels))
        if abs(before - after) >= config.pixel_delta_threshold
    )
    if changed:
        xs = tuple(index % left.width for index in changed)
        centroid = round(sum(xs) * 1000 / (len(xs) * max(1, left.width - 1)))
        edge_width = max(1, round(left.width * config.edge_band_milli / 1000))
        left_touched = min(xs) < edge_width
        right_touched = max(xs) >= left.width - edge_width
    else:
        centroid = None
        left_touched = False
        right_touched = False
    return ContinuityTransitionMeasurement(
        start_frame_index=left.frame_index,
        end_frame_index=right.frame_index,
        changed_pixel_count=len(changed),
        centroid_x_milli=centroid,
        left_edge_touched=left_touched,
        right_edge_touched=right_touched,
    )


class HybridContinuityEvaluatorV1:
    """Measure bounded screen-space continuity and defer semantic vision to humans."""

    def __init__(
        self,
        *,
        sampler: ContinuityFrameSampler,
        evaluator: ToolIdentity,
        config: ContinuityEvaluatorConfig | None = None,
    ) -> None:
        self._sampler = sampler
        self._evaluator = evaluator
        self._config = config or ContinuityEvaluatorConfig()

    def __call__(
        self,
        held_fd: int,
        request: ResolvedVideoGenerationRequest,
        measured: MeasuredVideoMetadata,
        qa_policy_content_hash: str,
    ) -> GeneratedShotContinuityEvidence:
        binding = request.continuity_binding
        original = request.activation_scope.request if request.activation_scope else None
        if binding is None or original is None:
            raise _review_error("Continuity evaluator requires an exact activation binding.")

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
                measured.frame_count, self._config.max_sample_count
            )
            os.lseek(held_fd, 0, os.SEEK_SET)
            frames = self._sampler.sample(held_fd, measured, frame_indices)
        finally:
            os.lseek(held_fd, position, os.SEEK_SET)

        if (
            len(frames) != len(frame_indices)
            or tuple(item.frame_index for item in frames) != frame_indices
            or len({(item.width, item.height) for item in frames}) != 1
        ):
            raise _review_error("Continuity frame sampler returned incomplete coverage.")
        width, height = frames[0].width, frames[0].height
        transitions = tuple(
            _transition(left, right, self._config)
            for left, right in zip(frames, frames[1:])
        )
        maximum_changed = width * height * self._config.maximum_changed_fraction_milli // 1000
        useful = tuple(
            item
            for item in transitions
            if item.centroid_x_milli is not None
            and self._config.minimum_changed_pixels
            <= item.changed_pixel_count
            <= maximum_changed
        )
        coverage_milli = round(len(useful) * 1000 / max(1, len(transitions)))
        constraints = binding.constraints

        motion_expected = _screen_edge(constraints.motion_direction)
        if motion_expected is None or len(useful) < 2:
            motion = _not_evaluated(
                constraints.motion_direction,
                "Unsupported motion grammar or insufficient dominant-motion coverage.",
            )
        else:
            delta = useful[-1].centroid_x_milli - useful[0].centroid_x_milli
            observed = "right" if delta > 0 else "left" if delta < 0 else "stationary"
            confidence = min(1000, abs(delta) * coverage_milli // 500)
            if (
                abs(delta) < self._config.minimum_direction_delta_milli
                or confidence < _MINIMUM_CONFIDENCE_MILLI
            ):
                motion = _not_evaluated(
                    constraints.motion_direction,
                    "Dominant screen-space motion confidence is below threshold.",
                )
            else:
                motion = _evaluated(
                    expected=motion_expected,
                    observed=observed,
                    matches=observed == motion_expected,
                    confidence_milli=confidence,
                    rationale="Compared first and last confident motion centroids.",
                )

        entrance_expected = _screen_edge(constraints.entrance_state, action="entrance")
        exit_expected = _screen_edge(constraints.exit_state, action="exit")
        edge_coverage_confident = coverage_milli >= _MINIMUM_CONFIDENCE_MILLI
        if not edge_coverage_confident or entrance_expected is None:
            entrance = _not_evaluated(
                constraints.entrance_state,
                "Entrance requires supported screen-edge grammar and confident motion.",
            )
        else:
            first = useful[0]
            observed = (
                "left"
                if first.left_edge_touched
                else "right"
                if first.right_edge_touched
                else "interior"
            )
            entrance = _evaluated(
                expected=entrance_expected,
                observed=observed,
                matches=observed == entrance_expected,
                confidence_milli=coverage_milli,
                rationale="Measured the first confident motion transition at a screen edge.",
            )
        if not edge_coverage_confident or exit_expected is None:
            exit_state = _not_evaluated(
                constraints.exit_state,
                "Exit requires supported screen-edge grammar and confident motion.",
            )
            reentry = _not_evaluated(
                "absent",
                "Re-entry requires a supported and confidently observed exit edge.",
            )
        else:
            last = useful[-1]
            observed = (
                "left"
                if last.left_edge_touched
                else "right"
                if last.right_edge_touched
                else "interior"
            )
            exit_state = _evaluated(
                expected=exit_expected,
                observed=observed,
                matches=observed == exit_expected,
                confidence_milli=coverage_milli,
                rationale="Measured the last confident motion transition at a screen edge.",
            )
            touches_expected = lambda item: (
                item.right_edge_touched
                if exit_expected == "right"
                else item.left_edge_touched
            )
            exit_positions = tuple(
                index for index, item in enumerate(useful) if touches_expected(item)
            )
            reentered = bool(
                exit_positions
                and any(
                    not touches_expected(item)
                    for item in useful[exit_positions[0] + 1 :]
                )
            )
            reentry = _evaluated(
                expected="absent",
                observed="present" if reentered else "absent",
                matches=not reentered,
                confidence_milli=coverage_milli,
                rationale="Checked for confident motion away from an already reached exit edge.",
            )

        identity = _not_evaluated(
            str(tuple(item.artifact_id for item in constraints.character_identities)),
            "No trusted identity backend is configured; human fallback is required.",
        )
        camera_axis = _not_evaluated(
            constraints.camera_axis,
            "No trusted camera-axis backend is configured; human fallback is required.",
        )
        framing = _not_evaluated(
            constraints.framing,
            "No trusted framing backend is configured; human fallback is required.",
        )
        measurements = GeneratedShotContinuityMeasurements(
            measurement_contract_version="hybrid-continuity-evaluator-v1",
            sampler=self._sampler.identity,
            artifact_sha256=measured.artifact_sha256,
            sample_width=width,
            sample_height=height,
            sampled_frames=tuple(
                ContinuitySampledFrameMeasurement(
                    frame_index=item.frame_index,
                    frame_sha256=hashlib.sha256(item.pixels).hexdigest(),
                )
                for item in frames
            ),
            transitions=transitions,
            identity=identity,
            camera_axis=camera_axis,
            framing=framing,
            motion_direction=motion,
            entrance_state=entrance,
            exit_state=exit_state,
            unexpected_reentry=reentry,
        )
        checks = (
            identity,
            camera_axis,
            framing,
            motion,
            entrance,
            exit_state,
            reentry,
        )
        coverage_complete = all(item.status != "not_evaluated" for item in checks)
        return GeneratedShotContinuityEvidence.create(
            source_shot_id=binding.terminal_frame.source_shot_id,
            target_shot_id=original.target_shot_id,
            target_shot_content_hash=original.target_shot_content_hash,
            resolved_generation_hash=request.resolved_generation_hash,
            artifact_sha256=measured.artifact_sha256,
            continuity_constraints_hash=constraints.content_hash,
            qa_policy_content_hash=qa_policy_content_hash,
            evaluator=self._evaluator,
            strength=EvidenceStrength.EXPLICIT_EVALUATOR,
            coverage_complete=coverage_complete,
            identity_match=identity.status == "match",
            camera_axis_match=camera_axis.status == "match",
            framing_match=framing.status == "match",
            motion_direction_match=motion.status == "match",
            entrance_state_match=entrance.status == "match",
            exit_state_match=exit_state.status == "match",
            unexpected_reentry=reentry.status == "mismatch",
            raw_measurements=measurements,
            rationale=(
                "Automatic screen-space measurements recorded; identity, camera axis, "
                "and framing require human fallback."
            ),
        )
