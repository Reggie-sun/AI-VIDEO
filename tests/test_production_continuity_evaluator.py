from __future__ import annotations

import hashlib
import importlib.metadata
import os
import shutil
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production import continuity_evaluator
from ai_video.production.models import (
    EvidenceStrength,
    QaVerdict,
    ToolIdentity,
)
from ai_video.production.review import (
    GeneratedShotContinuityEvidence,
    adjudicate_generated_shot_continuity,
)
from ai_video.production.video_artifact import (
    MeasuredVideoMetadata,
    validate_generated_shot_continuity_evidence,
)
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


def _onnx_runtime_identity() -> ToolIdentity:
    for package_name in ("onnxruntime", "onnxruntime-gpu"):
        try:
            return ToolIdentity(
                name=package_name,
                version=importlib.metadata.version(package_name),
            )
        except importlib.metadata.PackageNotFoundError:
            continue
    raise AssertionError("an ONNX Runtime distribution is required")


def _onnx_model(*, role: str, payload: bytes):
    return continuity_evaluator.ContinuityOnnxModel.create(
        role=role,
        content_sha256=hashlib.sha256(payload).hexdigest(),
        size_bytes=len(payload),
        input_name=f"{role}_input",
        output_name=f"{role}_output",
        input_width=8,
        input_height=4,
        source_repository="fixture://continuity-models",
        source_revision="fixture-revision-1",
        license_id="fixture-only",
        output_contract=(
            "normalized-xyxy-score-class/1"
            if role == "detector"
            else "l2-embedding/1"
        ),
    )


def _visual_profile(
    *,
    detector_bytes: bytes,
    reid_bytes: bytes,
    max_sample_count: int = 9,
    inference_runtime_version: str | None = None,
):
    return continuity_evaluator.ContinuityVisualProfile.create(
        profile_id="fixture-subject-continuity",
        profile_version="1",
        sampler=ToolIdentity(name="fixture-rgb-sampler", version="1"),
        sample_width=8,
        sample_height=4,
        numeric_runtime=ToolIdentity(
            name="numpy", version=importlib.metadata.version("numpy")
        ),
        inference_runtime=_onnx_runtime_identity().model_copy(
            update={
                "version": (
                    inference_runtime_version
                    or _onnx_runtime_identity().version
                )
            }
        ),
        detector=_onnx_model(role="detector", payload=detector_bytes),
        reid=_onnx_model(role="reid", payload=reid_bytes),
        tracker=ToolIdentity(name="deterministic-reid-tracker", version="1"),
        max_sample_count=max_sample_count,
        subject_class_ids=(0,),
        detection_confidence_milli=700,
        reid_similarity_milli=850,
        track_similarity_margin_milli=100,
        minimum_coverage_milli=700,
        minimum_direction_delta_milli=150,
        minimum_direction_consistency_milli=750,
        edge_band_milli=150,
    )


def _human_confirmation_visual_profile():
    base_profile = _visual_profile(
        detector_bytes=b"detector-v1", reid_bytes=b"reid-v1"
    )
    return SimpleNamespace(
        **{
            name: getattr(base_profile, name)
            for name in type(base_profile).model_fields
            if name != "profile_content_hash"
        },
        automatic_match_policy="human-confirmation-required",
        profile_content_hash=continuity_evaluator.canonical_sha256(
            {
                "base": base_profile.profile_content_hash,
                "automatic_match_policy": "human-confirmation-required",
            }
        ),
    )


def test_visual_profile_hash_binds_model_and_tracker_configuration() -> None:
    first = _visual_profile(detector_bytes=b"detector-v1", reid_bytes=b"reid-v1")
    second = _visual_profile(detector_bytes=b"detector-v2", reid_bytes=b"reid-v1")
    third = _visual_profile(
        detector_bytes=b"detector-v1",
        reid_bytes=b"reid-v1",
        max_sample_count=11,
    )

    assert first.profile_content_hash != second.profile_content_hash
    assert first.profile_content_hash != third.profile_content_hash
    assert first.profile_content_hash == continuity_evaluator.canonical_sha256(
        first.model_dump(mode="json", exclude={"profile_content_hash"})
    )


def test_onnx_backend_rejects_model_bytes_before_session_creation(
    tmp_path: Path,
) -> None:
    detector_path = tmp_path / "detector.onnx"
    reid_path = tmp_path / "reid.onnx"
    detector_path.write_bytes(b"tampered-detector")
    reid_path.write_bytes(b"reid-v1")
    profile = _visual_profile(
        detector_bytes=b"detector-v1", reid_bytes=b"reid-v1"
    )
    factory_calls: list[tuple[bytes, tuple[str, ...]]] = []

    def session_factory(model_bytes: bytes, providers: tuple[str, ...]):
        factory_calls.append((model_bytes, providers))
        return object()

    with pytest.raises(AiVideoError, match="model bytes"):
        continuity_evaluator.OnnxSubjectTrackerBackend(
            profile=profile,
            assets=continuity_evaluator.ContinuityModelAssets(
                detector_path=detector_path,
                reid_path=reid_path,
            ),
            session_factory=session_factory,
        )

    assert factory_calls == []


def test_onnx_backend_rejects_unsealed_runtime_before_session_creation(
    tmp_path: Path,
) -> None:
    detector_path = tmp_path / "detector.onnx"
    reid_path = tmp_path / "reid.onnx"
    detector_path.write_bytes(b"detector-v1")
    reid_path.write_bytes(b"reid-v1")
    profile = _visual_profile(
        detector_bytes=b"detector-v1",
        reid_bytes=b"reid-v1",
        inference_runtime_version="unexpected-version",
    )
    factory_calls = 0

    def session_factory(*_args):
        nonlocal factory_calls
        factory_calls += 1
        return object()

    with pytest.raises(AiVideoError, match="sealed profile"):
        continuity_evaluator.OnnxSubjectTrackerBackend(
            profile=profile,
            assets=continuity_evaluator.ContinuityModelAssets(
                detector_path=detector_path,
                reid_path=reid_path,
            ),
            session_factory=session_factory,
        )

    assert factory_calls == 0


def test_onnx_backend_decodes_post_nms_boxes_and_reidentifies_returning_track(
    tmp_path: Path,
) -> None:
    detector_bytes = b"detector-v1"
    reid_bytes = b"reid-v1"
    detector_path = tmp_path / "detector.onnx"
    reid_path = tmp_path / "reid.onnx"
    detector_path.write_bytes(detector_bytes)
    reid_path.write_bytes(reid_bytes)
    profile = _visual_profile(
        detector_bytes=detector_bytes, reid_bytes=reid_bytes
    )
    detector_outputs = iter(
        (
            np.empty((0, 6), dtype=np.float32),
            np.asarray([[0.00, 0.20, 0.20, 0.80, 0.95, 0]], dtype=np.float32),
            np.asarray([[0.40, 0.20, 0.60, 0.80, 0.96, 0]], dtype=np.float32),
            np.asarray([[0.80, 0.20, 1.00, 0.80, 0.97, 0]], dtype=np.float32),
            np.empty((0, 6), dtype=np.float32),
            np.asarray([[0.80, 0.20, 1.00, 0.80, 0.94, 0]], dtype=np.float32),
        )
    )
    reid_outputs = iter(
        np.asarray([[1.0, 0.0, 0.0]], dtype=np.float32) for _ in range(4)
    )
    observed_providers: list[tuple[str, ...]] = []

    class _Session:
        def __init__(self, outputs) -> None:
            self.outputs = outputs

        def run(self, output_names, inputs):
            assert len(output_names) == 1
            tensor = next(iter(inputs.values()))
            assert tensor.shape == (1, 3, 4, 8)
            return [next(self.outputs)]

    def factory(model_bytes: bytes, providers: tuple[str, ...]):
        observed_providers.append(providers)
        return _Session(
            detector_outputs if model_bytes == detector_bytes else reid_outputs
        )

    backend = continuity_evaluator.OnnxSubjectTrackerBackend(
        profile=profile,
        assets=continuity_evaluator.ContinuityModelAssets(
            detector_path=detector_path,
            reid_path=reid_path,
        ),
        session_factory=factory,
    )
    frames = tuple(
        continuity_evaluator.SampledRgbFrame(
            frame_index=index,
            width=8,
            height=4,
            pixels=bytes([index + 1] * (8 * 4 * 3)),
        )
        for index in range(6)
    )

    observations = backend.track(frames)

    assert tuple(item.state for item in observations) == (
        "absent",
        "present",
        "present",
        "present",
        "absent",
        "present",
    )
    identities = {
        item.track_identity for item in observations if item.state == "present"
    }
    assert len(identities) == 1
    assert observations[1].x_min_milli == 0
    assert observations[3].x_max_milli == 1000
    assert observed_providers == [
        ("CPUExecutionProvider",),
        ("CPUExecutionProvider",),
    ]


def test_onnx_backend_marks_subthreshold_subject_as_ambiguous_not_absent(
    tmp_path: Path,
) -> None:
    detector_bytes = b"detector-v1"
    reid_bytes = b"reid-v1"
    detector_path = tmp_path / "detector.onnx"
    reid_path = tmp_path / "reid.onnx"
    detector_path.write_bytes(detector_bytes)
    reid_path.write_bytes(reid_bytes)
    detector_outputs = iter(
        (
            np.asarray(
                [[0.10, 0.20, 0.30, 0.80, 0.69, 0]], dtype=np.float32
            ),
            np.empty((0, 6), dtype=np.float32),
        )
    )

    class _Session:
        def __init__(self, outputs) -> None:
            self.outputs = outputs

        def run(self, _output_names, _inputs):
            return [next(self.outputs)]

    def factory(model_bytes: bytes, _providers: tuple[str, ...]):
        return _Session(
            detector_outputs if model_bytes == detector_bytes else iter(())
        )

    backend = continuity_evaluator.OnnxSubjectTrackerBackend(
        profile=_visual_profile(
            detector_bytes=detector_bytes, reid_bytes=reid_bytes
        ),
        assets=continuity_evaluator.ContinuityModelAssets(
            detector_path=detector_path,
            reid_path=reid_path,
        ),
        session_factory=factory,
    )
    frames = tuple(
        continuity_evaluator.SampledRgbFrame(
            frame_index=index,
            width=8,
            height=4,
            pixels=bytes([index + 1] * (8 * 4 * 3)),
        )
        for index in range(2)
    )

    observations = backend.track(frames)

    assert tuple(item.state for item in observations) == ("ambiguous", "absent")


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
    assert evidence.evaluation_fingerprint is None
    assert (
        evidence.content_hash
        == "91bfb46c7a66e5dfd95db888c13d9437d8c56add03e0e9ff524067b5b8680983"
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


def test_ffmpeg_sampler_decodes_exact_requested_frames_from_held_fd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = tmp_path / "candidate.mp4"
    artifact.write_bytes(b"held-video")
    observed: dict[str, object] = {}
    raw_frames = bytes(range(96)) + bytes(range(96, 192))

    class _Result:
        returncode = 0
        stdout = raw_frames
        stderr = b""

    def run(argv, **kwargs):
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return _Result()

    monkeypatch.setattr(continuity_evaluator.subprocess, "run", run)
    sampler = continuity_evaluator.FfmpegRgbFrameSampler(
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
    assert frames[0].pixels == raw_frames[:96]
    assert frames[1].pixels == raw_frames[96:]
    assert observed["argv"] == [
        "/usr/bin/ffmpeg",
        "-v",
        "error",
        "-nostdin",
        "-i",
        f"/proc/self/fd/{held_fd}",
        "-vf",
        "select=eq(n\\,0)+eq(n\\,6),scale=8:4:flags=area,format=rgb24",
        "-vsync",
        "0",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "pipe:1",
    ]
    assert observed["kwargs"] == {
        "capture_output": True,
        "check": False,
        "env": {"LANG": "C", "LC_ALL": "C"},
        "pass_fds": (held_fd,),
        "timeout": 30,
    }


def test_ffmpeg_sampler_reads_existing_mp4_through_held_fd() -> None:
    executable = shutil.which("ffmpeg")
    if executable is None:
        pytest.skip("local ffmpeg is unavailable")
    artifact = Path("tests/fixtures/generated_video/fake-video.mp4").resolve()
    artifact_bytes = artifact.read_bytes()
    sampler = continuity_evaluator.FfmpegRgbFrameSampler(
        executable=Path(executable).resolve(),
        identity=ToolIdentity(name="ffmpeg", version="local-test"),
        sample_width=8,
        sample_height=4,
    )

    with artifact.open("rb") as held:
        frames = sampler.sample(
            held.fileno(),
            _measured(artifact_bytes, frame_count=24),
            (0, 23),
        )

    assert tuple(item.frame_index for item in frames) == (0, 23)
    assert all(len(item.pixels) == 8 * 4 * 3 for item in frames)
class _FixtureRgbSampler:
    identity = ToolIdentity(name="fixture-rgb-sampler", version="1")
    sample_width = 8
    sample_height = 4

    def __init__(self, frame_count: int) -> None:
        self.calls = 0
        self.frames = tuple(
            continuity_evaluator.SampledRgbFrame(
                frame_index=index,
                width=8,
                height=4,
                pixels=bytes([index] * (8 * 4 * 3)),
            )
            for index in range(frame_count)
        )

    def sample(self, held_fd, measured, frame_indices):
        del held_fd, measured
        self.calls += 1
        assert frame_indices == tuple(range(len(self.frames)))
        return self.frames


class _FixtureTrackedBackend:
    def __init__(self, profile, observations) -> None:
        self.profile = profile
        self.observations = observations
        self.calls = 0

    def track(self, frames):
        self.calls += 1
        assert tuple(item.frame_index for item in frames) == tuple(
            item.frame_index for item in self.observations
        )
        return self.observations


def _tracked_observation(
    frame_index: int,
    state: str,
    *,
    center_x_milli: int | None = None,
    track_identity: str | None = None,
):
    if state != "present":
        return continuity_evaluator.TrackedSubjectObservation(
            frame_index=frame_index,
            state=state,
        )
    assert center_x_milli is not None and track_identity is not None
    return continuity_evaluator.TrackedSubjectObservation(
        frame_index=frame_index,
        state="present",
        x_min_milli=max(0, center_x_milli - 100),
        x_max_milli=min(1000, center_x_milli + 100),
        detection_confidence_milli=950,
        track_identity=track_identity,
    )


def _tracked_evaluate(
    tmp_path: Path,
    observations,
    *,
    resolved=None,
    human_fallback=None,
    human_fallback_identity=None,
    visual_profile=None,
):
    artifact_bytes = b"tracked-continuity-artifact"
    artifact = tmp_path / "tracked.mp4"
    artifact.write_bytes(artifact_bytes)
    detector = b"detector-v1"
    reid = b"reid-v1"
    profile = visual_profile or _visual_profile(
        detector_bytes=detector, reid_bytes=reid
    )
    sampler = _FixtureRgbSampler(len(observations))
    tracker = _FixtureTrackedBackend(profile, observations)
    evaluator = continuity_evaluator.HybridContinuityEvaluatorV1(
        sampler=sampler,
        tracker=tracker,
        evaluator=ToolIdentity(name="hybrid-continuity-evaluator", version="2"),
        human_fallback=human_fallback,
        human_fallback_identity=human_fallback_identity,
    )
    with artifact.open("rb") as held:
        evidence = evaluator(
            held.fileno(),
            resolved or _resolved_with_screen_constraints(),
            _measured(artifact_bytes, frame_count=len(observations)),
            HASH_E,
        )
    return evidence, sampler, tracker, profile


def test_tracked_measurements_bind_profile_and_signed_subject_state(
    tmp_path: Path,
) -> None:
    track = "subject-track-a"
    observations = (
        _tracked_observation(0, "absent"),
        _tracked_observation(1, "present", center_x_milli=80, track_identity=track),
        _tracked_observation(2, "present", center_x_milli=400, track_identity=track),
        _tracked_observation(3, "present", center_x_milli=920, track_identity=track),
        _tracked_observation(4, "absent"),
    )

    evidence, sampler, tracker, profile = _tracked_evaluate(tmp_path, observations)

    measurements = evidence.raw_measurements
    assert measurements is not None
    assert measurements.measurement_contract_version == "tracked-continuity-evaluator/1"
    assert measurements.evaluator_profile_content_hash == profile.profile_content_hash
    assert measurements.motion_direction.status == "match"
    assert measurements.entrance_state.status == "match"
    assert measurements.exit_state.status == "match"
    assert measurements.unexpected_reentry.status == "match"
    assert measurements.identity.status == "not_evaluated"
    assert measurements.camera_axis.status == "not_evaluated"
    assert measurements.framing.status == "not_evaluated"
    assert evidence.evaluation_fingerprint is not None
    assert evidence.coverage_complete is False
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.NOT_EVALUATED
    assert sampler.calls == tracker.calls == 1


def test_profile_can_require_human_confirmation_for_automatic_matches(
    tmp_path: Path,
) -> None:
    guarded_profile = _human_confirmation_visual_profile()
    track = "subject-track-a"
    observations = (
        _tracked_observation(0, "absent"),
        _tracked_observation(
            1, "present", center_x_milli=80, track_identity=track
        ),
        _tracked_observation(
            2, "present", center_x_milli=500, track_identity=track
        ),
        _tracked_observation(
            3, "present", center_x_milli=920, track_identity=track
        ),
        _tracked_observation(4, "absent"),
    )

    evidence, *_ = _tracked_evaluate(
        tmp_path,
        observations,
        visual_profile=guarded_profile,
    )

    measurements = evidence.raw_measurements
    assert measurements is not None
    assert measurements.motion_direction.status == "not_evaluated"
    assert measurements.entrance_state.status == "not_evaluated"
    assert measurements.exit_state.status == "not_evaluated"
    assert measurements.unexpected_reentry.status == "not_evaluated"
    assert evidence.coverage_complete is False
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.NOT_EVALUATED

    human_identity = ToolIdentity(
        name="fixture-human-continuity", version="guarded-1"
    )

    def fallback(_held_fd, request, measured, qa_policy_content_hash):
        binding = request.continuity_binding
        original = request.activation_scope.request
        assert binding is not None
        return GeneratedShotContinuityEvidence.create(
            source_shot_id=binding.terminal_frame.source_shot_id,
            target_shot_id=original.target_shot_id,
            target_shot_content_hash=original.target_shot_content_hash,
            resolved_generation_hash=request.resolved_generation_hash,
            artifact_sha256=measured.artifact_sha256,
            continuity_constraints_hash=binding.constraints.content_hash,
            qa_policy_content_hash=qa_policy_content_hash,
            evaluator=human_identity,
            strength=EvidenceStrength.HUMAN,
            coverage_complete=True,
            identity_match=True,
            camera_axis_match=True,
            framing_match=True,
            motion_direction_match=True,
            entrance_state_match=True,
            exit_state_match=True,
            unexpected_reentry=False,
            rationale="Human confirmed the guarded automatic observations.",
        )

    confirmed, *_ = _tracked_evaluate(
        tmp_path,
        observations,
        visual_profile=guarded_profile,
        human_fallback=fallback,
        human_fallback_identity=human_identity,
    )

    assert confirmed.strength is EvidenceStrength.HUMAN
    assert confirmed.coverage_complete is True
    assert adjudicate_generated_shot_continuity(confirmed) is QaVerdict.PASS


def test_human_confirmation_policy_preserves_automatic_mismatch(
    tmp_path: Path,
) -> None:
    track = "subject-track-a"
    observations = (
        _tracked_observation(0, "absent"),
        _tracked_observation(
            1, "present", center_x_milli=920, track_identity=track
        ),
        _tracked_observation(
            2, "present", center_x_milli=500, track_identity=track
        ),
        _tracked_observation(
            3, "present", center_x_milli=80, track_identity=track
        ),
        _tracked_observation(4, "absent"),
    )
    fallback_calls = 0

    def forbidden_fallback(*_args):
        nonlocal fallback_calls
        fallback_calls += 1
        raise AssertionError("known automatic mismatch must not request fallback")

    evidence, *_ = _tracked_evaluate(
        tmp_path,
        observations,
        visual_profile=_human_confirmation_visual_profile(),
        human_fallback=forbidden_fallback,
        human_fallback_identity=ToolIdentity(
            name="fixture-human-continuity", version="guarded-1"
        ),
    )

    measurements = evidence.raw_measurements
    assert measurements is not None
    assert measurements.motion_direction.status == "mismatch"
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.FAIL
    assert fallback_calls == 0


def test_evaluator_intent_binds_profile_before_visual_execution(
    tmp_path: Path,
) -> None:
    observations = tuple(
        _tracked_observation(
            index,
            "present",
            center_x_milli=100 + index * 150,
            track_identity="subject-track-a",
        )
        for index in range(5)
    )
    artifact_bytes = b"tracked-continuity-artifact"
    detector = b"detector-v1"
    reid = b"reid-v1"
    profile = _visual_profile(detector_bytes=detector, reid_bytes=reid)
    sampler = _FixtureRgbSampler(len(observations))
    tracker = _FixtureTrackedBackend(profile, observations)
    evaluator = continuity_evaluator.HybridContinuityEvaluatorV1(
        sampler=sampler,
        tracker=tracker,
        evaluator=ToolIdentity(name="hybrid-continuity-evaluator", version="2"),
    )
    resolved = _resolved_with_screen_constraints()
    measured = _measured(artifact_bytes, frame_count=len(observations))

    intent = evaluator.create_intent(resolved, measured, HASH_E)

    assert intent.evaluator_profile_content_hash == profile.profile_content_hash
    assert intent.artifact_sha256 == measured.artifact_sha256
    assert intent.resolved_generation_hash == resolved.resolved_generation_hash
    assert sampler.calls == tracker.calls == 0


def test_tracked_evaluator_rejects_exact_artifact_hash_mismatch(
    tmp_path: Path,
) -> None:
    observations = tuple(
        _tracked_observation(
            index,
            "present",
            center_x_milli=100 + index * 150,
            track_identity="subject-track-a",
        )
        for index in range(5)
    )
    profile = _visual_profile(
        detector_bytes=b"detector-v1", reid_bytes=b"reid-v1"
    )
    evaluator = continuity_evaluator.HybridContinuityEvaluatorV1(
        sampler=_FixtureRgbSampler(len(observations)),
        tracker=_FixtureTrackedBackend(profile, observations),
        evaluator=ToolIdentity(name="hybrid-continuity-evaluator", version="2"),
    )
    artifact = tmp_path / "tracked.mp4"
    artifact.write_bytes(b"unexpected-bytes")

    with artifact.open("rb") as held, pytest.raises(AiVideoError) as rejected:
        evaluator(
            held.fileno(),
            _resolved_with_screen_constraints(),
            _measured(b"different-bytes", frame_count=len(observations)),
            HASH_E,
        )

    assert rejected.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID


def test_tracked_evaluator_rejects_sampler_output_geometry_outside_profile(
    tmp_path: Path,
) -> None:
    artifact_bytes = b"tracked-continuity-artifact"
    artifact = tmp_path / "tracked.mp4"
    artifact.write_bytes(artifact_bytes)
    observations = tuple(
        _tracked_observation(
            index,
            "present",
            center_x_milli=100 + index * 150,
            track_identity="subject-track-a",
        )
        for index in range(5)
    )
    profile = _visual_profile(
        detector_bytes=b"detector-v1", reid_bytes=b"reid-v1"
    )
    sampler = _FixtureRgbSampler(len(observations))
    sampler.frames = tuple(
        continuity_evaluator.SampledRgbFrame(
            frame_index=index,
            width=4,
            height=2,
            pixels=bytes([index] * (4 * 2 * 3)),
        )
        for index in range(len(observations))
    )
    evaluator = continuity_evaluator.HybridContinuityEvaluatorV1(
        sampler=sampler,
        tracker=_FixtureTrackedBackend(profile, observations),
        evaluator=ToolIdentity(name="hybrid-continuity-evaluator", version="2"),
    )

    with artifact.open("rb") as held, pytest.raises(AiVideoError, match="coverage"):
        evaluator(
            held.fileno(),
            _resolved_with_screen_constraints(),
            _measured(artifact_bytes, frame_count=len(observations)),
            HASH_E,
        )


def test_tracked_direction_reversal_is_a_known_mismatch(tmp_path: Path) -> None:
    track = "subject-track-a"
    observations = tuple(
        _tracked_observation(
            index,
            "present",
            center_x_milli=center,
            track_identity=track,
        )
        for index, center in enumerate((900, 700, 500, 300, 100))
    )

    evidence, *_ = _tracked_evaluate(tmp_path, observations)

    assert evidence.raw_measurements.motion_direction.status == "mismatch"
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.FAIL


def test_tracked_exit_edge_mismatch_and_same_track_reentry_are_failures(
    tmp_path: Path,
) -> None:
    track = "subject-track-a"
    observations = (
        _tracked_observation(0, "absent"),
        _tracked_observation(1, "present", center_x_milli=80, track_identity=track),
        _tracked_observation(2, "present", center_x_milli=500, track_identity=track),
        _tracked_observation(3, "present", center_x_milli=920, track_identity=track),
        _tracked_observation(4, "absent"),
        _tracked_observation(5, "present", center_x_milli=920, track_identity=track),
    )
    resolved = _resolved_with_screen_constraints(exit_state="subject-exits-screen-left")

    evidence, *_ = _tracked_evaluate(tmp_path, observations, resolved=resolved)

    assert evidence.raw_measurements.exit_state.status == "mismatch"
    assert evidence.raw_measurements.unexpected_reentry.status == "mismatch"
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.FAIL


def test_ambiguous_or_low_coverage_track_requires_human_fallback(
    tmp_path: Path,
) -> None:
    observations = (
        _tracked_observation(0, "ambiguous"),
        _tracked_observation(1, "ambiguous"),
        _tracked_observation(
            2, "present", center_x_milli=500, track_identity="subject-track-a"
        ),
        _tracked_observation(3, "ambiguous"),
        _tracked_observation(4, "ambiguous"),
    )

    evidence, *_ = _tracked_evaluate(tmp_path, observations)

    assert evidence.raw_measurements.motion_direction.status == "not_evaluated"
    assert evidence.raw_measurements.entrance_state.status == "not_evaluated"
    assert evidence.raw_measurements.exit_state.status == "not_evaluated"
    assert evidence.raw_measurements.unexpected_reentry.status == "not_evaluated"
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.NOT_EVALUATED


def test_sparse_interior_crossings_are_incomplete_not_known_mismatches(
    tmp_path: Path,
) -> None:
    track = "subject-track-a"
    observations = (
        _tracked_observation(0, "absent"),
        _tracked_observation(1, "present", center_x_milli=500, track_identity=track),
        _tracked_observation(2, "present", center_x_milli=700, track_identity=track),
        _tracked_observation(3, "absent"),
    )

    evidence, *_ = _tracked_evaluate(tmp_path, observations)

    assert evidence.raw_measurements.entrance_state.status == "not_evaluated"
    assert evidence.raw_measurements.exit_state.status == "not_evaluated"
    assert evidence.raw_measurements.unexpected_reentry.status == "not_evaluated"
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.NOT_EVALUATED


def test_subject_touching_both_edge_bands_has_no_signed_crossing(
    tmp_path: Path,
) -> None:
    track = "subject-track-a"
    observations = (
        _tracked_observation(0, "absent"),
        continuity_evaluator.TrackedSubjectObservation(
            frame_index=1,
            state="present",
            x_min_milli=50,
            x_max_milli=950,
            detection_confidence_milli=950,
            track_identity=track,
        ),
        _tracked_observation(2, "absent"),
    )

    evidence, *_ = _tracked_evaluate(tmp_path, observations)

    assert evidence.raw_measurements.entrance_state.status == "not_evaluated"
    assert evidence.raw_measurements.exit_state.status == "not_evaluated"
    assert evidence.raw_measurements.unexpected_reentry.status == "not_evaluated"


def test_bound_human_fallback_completes_only_not_evaluated_dimensions(
    tmp_path: Path,
) -> None:
    track = "subject-track-a"
    observations = (
        _tracked_observation(0, "absent"),
        _tracked_observation(1, "present", center_x_milli=80, track_identity=track),
        _tracked_observation(2, "present", center_x_milli=500, track_identity=track),
        _tracked_observation(3, "present", center_x_milli=920, track_identity=track),
        _tracked_observation(4, "absent"),
    )
    human_identity = ToolIdentity(name="fixture-human-continuity", version="1")
    fallback_calls = 0

    def fallback(held_fd, request, measured, qa_policy_content_hash):
        nonlocal fallback_calls
        fallback_calls += 1
        assert os.lseek(held_fd, 0, os.SEEK_CUR) == 0
        binding = request.continuity_binding
        original = request.activation_scope.request
        assert binding is not None
        return GeneratedShotContinuityEvidence.create(
            source_shot_id=binding.terminal_frame.source_shot_id,
            target_shot_id=original.target_shot_id,
            target_shot_content_hash=original.target_shot_content_hash,
            resolved_generation_hash=request.resolved_generation_hash,
            artifact_sha256=measured.artifact_sha256,
            continuity_constraints_hash=binding.constraints.content_hash,
            qa_policy_content_hash=qa_policy_content_hash,
            evaluator=human_identity,
            strength=EvidenceStrength.HUMAN,
            coverage_complete=True,
            identity_match=True,
            camera_axis_match=True,
            framing_match=True,
            motion_direction_match=True,
            entrance_state_match=True,
            exit_state_match=True,
            unexpected_reentry=False,
            rationale="Human reviewed every exact continuity dimension.",
        )

    evidence, _, _, visual_profile = _tracked_evaluate(
        tmp_path,
        observations,
        human_fallback=fallback,
        human_fallback_identity=human_identity,
    )

    measurements = evidence.raw_measurements
    assert measurements is not None
    assert measurements.motion_direction.status == "match"
    assert measurements.identity.status == "match"
    assert measurements.fallback_evidence is not None
    assert measurements.fallback_evidence.evaluator == human_identity
    assert measurements.fallback_evidence.artifact_sha256 == evidence.artifact_sha256
    assert (
        measurements.evaluator_profile_content_hash
        != visual_profile.profile_content_hash
    )
    assert evidence.strength is EvidenceStrength.HUMAN
    assert evidence.coverage_complete is True
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.PASS
    assert fallback_calls == 1

    resolved = _resolved_with_screen_constraints()
    measured = _measured(b"tracked-continuity-artifact", frame_count=len(observations))
    automatic_identity = ToolIdentity(
        name="hybrid-continuity-evaluator", version="2"
    )
    with pytest.raises(AiVideoError, match="does not bind"):
        validate_generated_shot_continuity_evidence(
            evidence,
            request=resolved,
            measured=measured,
            policy_content_hash=HASH_E,
            authorities=(automatic_identity,),
            require_pass=True,
        )
    assert (
        validate_generated_shot_continuity_evidence(
            evidence,
            request=resolved,
            measured=measured,
            policy_content_hash=HASH_E,
            authorities=(automatic_identity, human_identity),
            require_pass=True,
        )
        is evidence
    )


def test_bound_human_rejection_overrides_automatic_match(tmp_path: Path) -> None:
    track = "subject-track-a"
    observations = (
        _tracked_observation(0, "absent"),
        _tracked_observation(1, "present", center_x_milli=80, track_identity=track),
        _tracked_observation(2, "present", center_x_milli=500, track_identity=track),
        _tracked_observation(3, "present", center_x_milli=920, track_identity=track),
        _tracked_observation(4, "absent"),
    )
    human_identity = ToolIdentity(name="fixture-human-continuity", version="1")

    def fallback(_held_fd, request, measured, qa_policy_content_hash):
        binding = request.continuity_binding
        original = request.activation_scope.request
        assert binding is not None
        return GeneratedShotContinuityEvidence.create(
            source_shot_id=binding.terminal_frame.source_shot_id,
            target_shot_id=original.target_shot_id,
            target_shot_content_hash=original.target_shot_content_hash,
            resolved_generation_hash=request.resolved_generation_hash,
            artifact_sha256=measured.artifact_sha256,
            continuity_constraints_hash=binding.constraints.content_hash,
            qa_policy_content_hash=qa_policy_content_hash,
            evaluator=human_identity,
            strength=EvidenceStrength.HUMAN,
            coverage_complete=True,
            identity_match=True,
            camera_axis_match=True,
            framing_match=True,
            motion_direction_match=False,
            entrance_state_match=True,
            exit_state_match=True,
            unexpected_reentry=False,
            rationale="Human rejected motion on the exact artifact.",
        )

    evidence, *_ = _tracked_evaluate(
        tmp_path,
        observations,
        human_fallback=fallback,
        human_fallback_identity=human_identity,
    )

    assert evidence.raw_measurements.motion_direction.status == "mismatch"
    assert evidence.raw_measurements.fallback_evidence is not None
    assert not evidence.raw_measurements.fallback_evidence.motion_direction_match
    assert adjudicate_generated_shot_continuity(evidence) is QaVerdict.FAIL
