from __future__ import annotations

import hashlib
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production import continuity_evaluator
from ai_video.production.models import (
    EvidenceStrength,
    QaVerdict,
    StateCommitStatus,
    ToolIdentity,
    VideoAttemptPhase,
)
from ai_video.production.review import (
    GeneratedShotContinuityEvidence,
    GeneratedShotContinuityMeasurements,
    adjudicate_generated_shot_continuity,
)
from ai_video.production.video_artifact import MeasuredVideoMetadata
from ai_video.production.video_generation import VideoGenerationService
from test_production_video import (
    _continuity_binding,
    _continuity_constraints,
    _first_frame,
    _request,
    _resolved,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64


def _check(status: str, *, expected: str, observed: str | None) -> dict[str, object]:
    return {
        "status": status,
        "expected": expected,
        "observed": observed,
        "confidence_milli": 900 if observed is not None else None,
        "rationale": "fixture observation",
    }


def _raw_measurements(*, motion_status: str) -> dict[str, object]:
    return {
        "measurement_contract_version": "hybrid-continuity-evaluator-v1",
        "sampler": {"name": "fixture-frame-sampler", "version": "1"},
        "artifact_sha256": HASH_C,
        "sample_width": 8,
        "sample_height": 4,
        "sampled_frames": (
            {"frame_index": 0, "frame_sha256": HASH_A},
            {"frame_index": 5, "frame_sha256": HASH_B},
        ),
        "transitions": (
            {
                "start_frame_index": 0,
                "end_frame_index": 5,
                "changed_pixel_count": 4,
                "centroid_x_milli": 500,
                "left_edge_touched": False,
                "right_edge_touched": False,
            },
        ),
        "identity": _check(
            "not_evaluated", expected="character identity", observed=None
        ),
        "camera_axis": _check(
            "not_evaluated", expected="axis east", observed=None
        ),
        "framing": _check(
            "not_evaluated", expected="medium wide", observed=None
        ),
        "motion_direction": _check(
            motion_status, expected="right", observed="left"
        ),
        "entrance_state": _check("match", expected="left", observed="left"),
        "exit_state": _check("match", expected="right", observed="right"),
        "unexpected_reentry": _check(
            "match", expected="absent", observed="absent"
        ),
    }


def test_known_dynamic_mismatch_fails_before_incomplete_human_dimensions() -> None:
    evidence = GeneratedShotContinuityEvidence.create(
        source_shot_id="shot-001",
        target_shot_id="shot-002",
        target_shot_content_hash=HASH_A,
        resolved_generation_hash=HASH_B,
        artifact_sha256=HASH_C,
        continuity_constraints_hash=HASH_D,
        qa_policy_content_hash=HASH_E,
        evaluator=ToolIdentity(name="continuity-evaluator", version="1"),
        strength=EvidenceStrength.EXPLICIT_EVALUATOR,
        coverage_complete=False,
        identity_match=False,
        camera_axis_match=False,
        framing_match=False,
        motion_direction_match=False,
        entrance_state_match=True,
        exit_state_match=True,
        unexpected_reentry=False,
        raw_measurements=_raw_measurements(motion_status="mismatch"),
        rationale="Automatic motion mismatch; human fallback still required.",
    )

    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.FAIL


class _FixtureSampler:
    identity = ToolIdentity(name="fixture-gray-frame-sampler", version="1")

    def __init__(self, frames: tuple[object, ...]) -> None:
        self.frames = frames
        self.calls = 0

    def sample(self, held_fd, measured, frame_indices):
        self.calls += 1
        assert os.lseek(held_fd, 0, os.SEEK_CUR) == 0
        assert tuple(frame.frame_index for frame in self.frames) == frame_indices
        return self.frames


def _frame(frame_index: int, position: int | None, *, width: int = 8, height: int = 4):
    pixels = bytearray(width * height)
    if position is not None:
        for y in (1, 2):
            for x in (position, min(position + 1, width - 1)):
                pixels[y * width + x] = 255
    return continuity_evaluator.SampledGrayFrame(
        frame_index=frame_index,
        width=width,
        height=height,
        pixels=bytes(pixels),
    )


def _resolved_with_screen_constraints(
    *,
    motion_direction: str = "subject-moves-screen-right",
    entrance_state: str = "subject-enters-screen-left",
    exit_state: str = "subject-exits-screen-right",
):
    constraints = _continuity_constraints(
        motion_direction=motion_direction,
        entrance_state=entrance_state,
        exit_state=exit_state,
    )
    binding = _continuity_binding(constraints=constraints)
    terminal = binding.terminal_frame
    first_frame = _first_frame().model_copy(
        update={
            "asset_id": terminal.extracted_asset_id,
            "asset_sha256": terminal.extracted_sha256,
            "mime_type": terminal.extracted_mime_type,
            "width": terminal.extracted_width,
            "height": terminal.extracted_height,
            "size_bytes": terminal.extracted_size_bytes,
        }
    )
    request = _request(
        image_bindings=(first_frame,),
        continuity_binding=binding,
        input_artifact_ids=(
            binding.target_shot_id,
            terminal.source_shot_id,
            terminal.source_video_asset_id,
            terminal.extracted_asset_id,
        ),
    )
    return _resolved(request)


def _measured(artifact_bytes: bytes, *, frame_count: int) -> MeasuredVideoMetadata:
    return MeasuredVideoMetadata(
        container_name="mp4",
        codec_name="h264",
        width=1280,
        height=720,
        fps_numerator=24,
        fps_denominator=1,
        duration_milliseconds=6000,
        frame_count=frame_count,
        audio_stream_count=0,
        size_bytes=len(artifact_bytes),
        artifact_sha256=hashlib.sha256(artifact_bytes).hexdigest(),
    )


def _evaluate(
    tmp_path: Path,
    frames: tuple[object, ...],
    *,
    resolved=None,
):
    artifact_bytes = b"exact-continuity-artifact"
    artifact = tmp_path / "candidate.mp4"
    artifact.write_bytes(artifact_bytes)
    sampler = _FixtureSampler(frames)
    evaluator = continuity_evaluator.HybridContinuityEvaluatorV1(
        sampler=sampler,
        evaluator=ToolIdentity(name="hybrid-continuity-evaluator", version="1"),
    )
    with artifact.open("rb") as held:
        evidence = evaluator(
            held.fileno(),
            resolved or _resolved_with_screen_constraints(),
            _measured(artifact_bytes, frame_count=len(frames)),
            HASH_E,
        )
    return evidence, sampler


def test_samples_exact_artifact_and_measures_supported_dynamic_checks(
    tmp_path: Path,
) -> None:
    frames = tuple(_frame(index, index) for index in range(7))

    evidence, sampler = _evaluate(tmp_path, frames)

    measurements = evidence.raw_measurements
    assert measurements is not None
    assert measurements.artifact_sha256 == hashlib.sha256(
        b"exact-continuity-artifact"
    ).hexdigest()
    assert tuple(item.frame_index for item in measurements.sampled_frames) == tuple(
        range(7)
    )
    assert measurements.motion_direction.status == "match"
    assert measurements.entrance_state.status == "match"
    assert measurements.exit_state.status == "match"
    assert measurements.unexpected_reentry.status == "match"
    assert measurements.identity.status == "not_evaluated"
    assert measurements.camera_axis.status == "not_evaluated"
    assert measurements.framing.status == "not_evaluated"
    assert evidence.coverage_complete is False
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.NOT_EVALUATED
    assert "human fallback" in evidence.rationale.lower()
    assert sampler.calls == 1


def test_direction_reversal_is_a_known_failure(tmp_path: Path) -> None:
    frames = tuple(_frame(index, 6 - index) for index in range(7))

    evidence, _ = _evaluate(tmp_path, frames)

    assert evidence.raw_measurements is not None
    assert evidence.raw_measurements.motion_direction.status == "mismatch"
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.FAIL


def test_exit_edge_mismatch_is_a_known_failure(tmp_path: Path) -> None:
    frames = tuple(_frame(index, index) for index in range(7))
    resolved = _resolved_with_screen_constraints(exit_state="subject-exits-screen-left")

    evidence, _ = _evaluate(tmp_path, frames, resolved=resolved)

    assert evidence.raw_measurements is not None
    assert evidence.raw_measurements.exit_state.status == "mismatch"
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.FAIL


def test_leave_then_return_is_reported_as_unexpected_reentry(tmp_path: Path) -> None:
    positions = (0, 2, 4, 6, None, 0, 2)
    frames = tuple(_frame(index, position) for index, position in enumerate(positions))

    evidence, _ = _evaluate(tmp_path, frames)

    assert evidence.raw_measurements is not None
    assert evidence.raw_measurements.unexpected_reentry.status == "mismatch"
    assert evidence.unexpected_reentry is True
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.FAIL


def test_low_motion_returns_incomplete_and_requires_human_fallback(
    tmp_path: Path,
) -> None:
    frames = tuple(_frame(index, 3) for index in range(7))

    evidence, _ = _evaluate(tmp_path, frames)

    assert evidence.raw_measurements is not None
    assert evidence.raw_measurements.motion_direction.status == "not_evaluated"
    assert evidence.raw_measurements.entrance_state.status == "not_evaluated"
    assert evidence.raw_measurements.exit_state.status == "not_evaluated"
    assert evidence.raw_measurements.unexpected_reentry.status == "not_evaluated"
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.NOT_EVALUATED
    assert "human fallback" in evidence.rationale.lower()


def test_sparse_edge_observation_does_not_become_a_known_failure(
    tmp_path: Path,
) -> None:
    positions = (None, None, None, None, None, None, 0)
    frames = tuple(_frame(index, position) for index, position in enumerate(positions))

    evidence, _ = _evaluate(tmp_path, frames)

    assert evidence.raw_measurements is not None
    assert evidence.raw_measurements.entrance_state.status == "not_evaluated"
    assert evidence.raw_measurements.exit_state.status == "not_evaluated"
    assert evidence.raw_measurements.unexpected_reentry.status == "not_evaluated"
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.NOT_EVALUATED


def test_human_fallback_can_supply_complete_evidence_after_auto_incomplete(
    tmp_path: Path,
) -> None:
    frames = tuple(_frame(index, index) for index in range(7))
    automatic, _ = _evaluate(tmp_path, frames)

    human = GeneratedShotContinuityEvidence.create(
        source_shot_id=automatic.source_shot_id,
        target_shot_id=automatic.target_shot_id,
        target_shot_content_hash=automatic.target_shot_content_hash,
        resolved_generation_hash=automatic.resolved_generation_hash,
        artifact_sha256=automatic.artifact_sha256,
        continuity_constraints_hash=automatic.continuity_constraints_hash,
        qa_policy_content_hash=automatic.qa_policy_content_hash,
        evaluator=ToolIdentity(name="human-continuity-reviewer", version="1"),
        strength=EvidenceStrength.HUMAN,
        coverage_complete=True,
        identity_match=True,
        camera_axis_match=True,
        framing_match=True,
        motion_direction_match=True,
        entrance_state_match=True,
        exit_state_match=True,
        unexpected_reentry=False,
        rationale="Human reviewed the exact artifact and all continuity dimensions.",
    )

    assert adjudicate_generated_shot_continuity(automatic) is QaVerdict.NOT_EVALUATED
    assert adjudicate_generated_shot_continuity(human) is QaVerdict.PASS


def test_raw_transitions_must_bind_adjacent_sampled_frame_indices(
    tmp_path: Path,
) -> None:
    frames = tuple(_frame(index, index) for index in range(7))
    evidence, _ = _evaluate(tmp_path, frames)
    assert evidence.raw_measurements is not None
    payload = evidence.raw_measurements.model_dump(mode="json")
    payload["transitions"][0]["end_frame_index"] = 6

    with pytest.raises(ValidationError, match="adjacent sampled frames"):
        GeneratedShotContinuityMeasurements.model_validate(payload)


def test_evaluator_rejects_artifact_hash_mismatch(tmp_path: Path) -> None:
    artifact = tmp_path / "candidate.mp4"
    artifact.write_bytes(b"unexpected-bytes")
    frames = tuple(_frame(index, index) for index in range(7))
    evaluator = continuity_evaluator.HybridContinuityEvaluatorV1(
        sampler=_FixtureSampler(frames),
        evaluator=ToolIdentity(name="hybrid-continuity-evaluator", version="1"),
    )

    with artifact.open("rb") as held, pytest.raises(AiVideoError) as rejected:
        evaluator(
            held.fileno(),
            _resolved_with_screen_constraints(),
            _measured(b"different-bytes", frame_count=len(frames)),
            HASH_E,
        )

    assert rejected.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID


def test_ffmpeg_sampler_decodes_exact_requested_frames_from_held_fd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = tmp_path / "candidate.mp4"
    artifact.write_bytes(b"held-video")
    observed: dict[str, object] = {}
    raw_frames = bytes(range(32)) + bytes(range(32, 64))

    class _Result:
        returncode = 0
        stdout = raw_frames
        stderr = b""

    def run(argv, **kwargs):
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return _Result()

    monkeypatch.setattr(continuity_evaluator.subprocess, "run", run)
    sampler = continuity_evaluator.FfmpegGrayFrameSampler(
        executable=Path("/usr/bin/ffmpeg"),
        identity=ToolIdentity(name="ffmpeg", version="7.1"),
        sample_width=8,
        sample_height=4,
    )
    measured = _measured(b"held-video", frame_count=7)

    with artifact.open("rb") as held:
        frames = sampler.sample(held.fileno(), measured, (0, 6))
        held_fd = held.fileno()

    assert tuple(item.frame_index for item in frames) == (0, 6)
    assert frames[0].pixels == raw_frames[:32]
    assert frames[1].pixels == raw_frames[32:]
    assert observed["argv"] == [
        "/usr/bin/ffmpeg",
        "-v",
        "error",
        "-nostdin",
        "-i",
        f"/proc/self/fd/{held_fd}",
        "-vf",
        "select=eq(n\\,0)+eq(n\\,6),scale=8:4:flags=area,format=gray",
        "-vsync",
        "0",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "pipe:1",
    ]
    assert observed["kwargs"] == {
        "capture_output": True,
        "check": False,
        "env": {"LANG": "C", "LC_ALL": "C"},
        "pass_fds": (held_fd,),
        "timeout": 30,
    }


def test_successful_activation_replay_does_not_repeat_evaluator_side_effect(
    tmp_path: Path,
) -> None:
    artifact_bytes = b"exact-continuity-artifact"
    artifact = tmp_path / "candidate.mp4"
    artifact.write_bytes(artifact_bytes)
    frames = tuple(_frame(index, index) for index in range(7))
    sampler = _FixtureSampler(frames)
    evaluator = continuity_evaluator.HybridContinuityEvaluatorV1(
        sampler=sampler,
        evaluator=ToolIdentity(name="hybrid-continuity-evaluator", version="1"),
    )
    resolved = _resolved_with_screen_constraints()
    measured = _measured(artifact_bytes, frame_count=len(frames))

    class _Committer:
        def __init__(self) -> None:
            self.attempt = SimpleNamespace(status=StateCommitStatus.RUNNING)
            self.state = SimpleNamespace(phase=VideoAttemptPhase.VALIDATE)

        def _read_manifest(self):
            return object()

        def _video_attempt(self, manifest, attempt_id):
            del manifest, attempt_id
            return SimpleNamespace(
                status=self.attempt.status,
                video_generation_state=self.state,
            )

        def prepare_video_activation_candidate(self, **kwargs):
            with artifact.open("rb") as held:
                kwargs["continuity_reviewer"](
                    held.fileno(), resolved, measured, HASH_E
                )
            self.state = SimpleNamespace(phase=VideoAttemptPhase.CANDIDATE)

        def activate_video_candidate(self, **kwargs):
            del kwargs
            self.attempt = SimpleNamespace(status=StateCommitStatus.SUCCEEDED)
            self.state = SimpleNamespace(phase=VideoAttemptPhase.ACTIVATE)
            return "activated"

        def replay_active_video_generation(self, **kwargs):
            del kwargs
            return "replayed"

    committer = _Committer()
    service = VideoGenerationService(committer=committer, provider=object())

    assert (
        service.fetch_and_activate(
            attempt_id="attempt-1", continuity_reviewer=evaluator
        )
        == "activated"
    )
    assert (
        service.fetch_and_activate(
            attempt_id="attempt-1", continuity_reviewer=evaluator
        )
        == "replayed"
    )
    assert sampler.calls == 1
