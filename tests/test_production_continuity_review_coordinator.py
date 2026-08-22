from __future__ import annotations

import hashlib
from contextlib import contextmanager, nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.continuity_review_coordinator import (
    ContinuityReviewCoordinator,
    HumanReviewDecisionV1,
    HumanReviewRequestV1,
)
from ai_video.production.local_continuity_reviewer import (
    LocalCudaContinuityReviewerConfig,
)
from ai_video.production.models import (
    EvidenceStrength,
    StateCommitStatus,
    ToolIdentity,
    VideoAttemptPhase,
)
from ai_video.production.video_artifact import MeasuredVideoMetadata


AUTOMATIC = ToolIdentity(name="fixture-continuity-evaluator", version="2")
HUMAN = ToolIdentity(name="local-human-reviewer", version="1")


def _config() -> LocalCudaContinuityReviewerConfig:
    return LocalCudaContinuityReviewerConfig(
        model_root=Path("/opt/ai-video/continuity-models"),
        ffmpeg_executable=Path("/usr/bin/ffmpeg"),
        sampler=ToolIdentity(name="fixture-sampler", version="1"),
        evaluator=AUTOMATIC,
        sample_width=320,
        sample_height=180,
    )


def _decision(
    request: HumanReviewRequestV1,
    **changes: object,
) -> HumanReviewDecisionV1:
    values: dict[str, object] = {
        "review_request_content_hash": request.content_hash,
        "reviewer_identity": HUMAN,
        "identity": "PASS",
        "camera_axis": "PASS",
        "framing": "PASS",
        "motion_direction": "PASS",
        "entrance": "PASS",
        "exit": "PASS",
        "unexpected_reentry": "PASS",
        "rationale": "Reviewed every continuity dimension against the exact clip.",
    }
    values.update(changes)
    return HumanReviewDecisionV1.create(**values)


class _FakeCommitter:
    def __init__(self, root: Path, *, artifact_bytes: bytes = b"fetched-video") -> None:
        self.project_root = root
        self.artifact_bytes = artifact_bytes
        self.artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()
        artifact_path = Path(
            f"state/video-generation/fetch/files/{self.artifact_sha256}.mp4"
        )
        target = root / artifact_path
        target.parent.mkdir(parents=True)
        target.write_bytes(artifact_bytes)
        self.fetch_pointer = SimpleNamespace(
            artifact_path=artifact_path,
            artifact_sha256=self.artifact_sha256,
            artifact_size_bytes=len(artifact_bytes),
        )
        self.policy = SimpleNamespace(
            policy_id="qa-continuity-v1",
            policy_version="1",
            content_hash="a" * 64,
            semantic_authorities=(AUTOMATIC, HUMAN),
        )
        self.manifest = SimpleNamespace(
            active_qa_policy=SimpleNamespace(
                policy_id=self.policy.policy_id,
                policy_version=self.policy.policy_version,
                content_hash=self.policy.content_hash,
                file_sha256="b" * 64,
            )
        )
        terminal = SimpleNamespace(source_shot_id="shot-source")
        constraints = SimpleNamespace(content_hash="c" * 64)
        binding = SimpleNamespace(
            terminal_frame=terminal,
            target_shot_id="shot-target",
            target_shot_content_hash="d" * 64,
            constraints=constraints,
        )
        original = SimpleNamespace(
            target_shot_id="shot-target",
            target_shot_content_hash="d" * 64,
        )
        self.request = SimpleNamespace(
            continuity_binding=binding,
            activation_scope=SimpleNamespace(request=original),
            resolved_generation_hash="e" * 64,
            output_asset_id="video-shot-target",
        )
        self.state = SimpleNamespace(
            phase=VideoAttemptPhase.VALIDATE,
            request=object(),
            fetch_receipt=None,
            local_fetch_receipt=self.fetch_pointer,
            continuity_evaluation=None,
        )
        self.attempt = SimpleNamespace(
            attempt_id="attempt-1",
            status=StateCommitStatus.RUNNING,
            video_generation_state=self.state,
        )

    def _read_manifest(self):
        return self.manifest

    def _video_attempt(self, _manifest, attempt_id: str):
        if attempt_id != self.attempt.attempt_id:
            raise AiVideoError(
                ErrorCode.PRODUCTION_STATE_INVALID,
                "Video generation attempt does not exist.",
            )
        return self.attempt

    def _reopen_video_request(self, _pointer):
        return self.request

    def _reopen_local_video_fetch(self, _pointer):
        return SimpleNamespace(
            artifact_sha256=self.fetch_pointer.artifact_sha256,
            size_bytes=self.fetch_pointer.artifact_size_bytes,
        )


class _FakeService:
    def __init__(self, committer: _FakeCommitter) -> None:
        self.committer = committer
        self.calls: list[object] = []

    def fetch_and_activate(self, *, attempt_id: str, continuity_reviewer=None):
        self.calls.append(continuity_reviewer)
        if continuity_reviewer is not None:
            measured = MeasuredVideoMetadata(
                container_name="mp4",
                codec_name="h264",
                width=320,
                height=180,
                fps_numerator=24,
                fps_denominator=1,
                duration_milliseconds=1000,
                frame_count=24,
                audio_stream_count=0,
                size_bytes=len(self.committer.artifact_bytes),
                artifact_sha256=self.committer.artifact_sha256,
            )
            artifact_path = (
                self.committer.project_root / self.committer.fetch_pointer.artifact_path
            )
            with artifact_path.open("rb") as artifact:
                evidence = continuity_reviewer(
                    artifact.fileno(),
                    self.committer.request,
                    measured,
                    self.committer.policy.content_hash,
                )
            assert evidence.strength is EvidenceStrength.HUMAN
        return {"attempt_id": attempt_id, "activated": True}


def _coordinator(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    gpu_execution_lease=lambda: nullcontext(),
    reviewer_factory=None,
):
    import ai_video.production.continuity_review_coordinator as coordinator_module

    committer = _FakeCommitter(tmp_path)
    service = _FakeService(committer)
    monkeypatch.setattr(
        coordinator_module,
        "load_qa_policy",
        lambda _root, _pointer: committer.policy,
    )
    factory_calls: list[object] = []

    def default_factory(*, config, human_fallback, human_fallback_identity):
        factory_calls.append((config, human_fallback, human_fallback_identity))
        return human_fallback

    coordinator = ContinuityReviewCoordinator(
        committer=committer,
        video_service=service,
        reviewer_config=_config(),
        reviewer_identity=HUMAN,
        gpu_execution_lease=gpu_execution_lease,
        reviewer_factory=reviewer_factory or default_factory,
    )
    return coordinator, committer, service, factory_calls


def test_request_projects_exact_validate_bindings_without_writes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    coordinator, committer, service, factory_calls = _coordinator(
        monkeypatch, tmp_path
    )

    request = coordinator.prepare_request(attempt_id="attempt-1")

    assert request.attempt_id == "attempt-1"
    assert request.source_shot_id == "shot-source"
    assert request.target_shot_id == "shot-target"
    assert request.target_shot_content_hash == "d" * 64
    assert request.resolved_generation_hash == "e" * 64
    assert request.artifact_sha256 == committer.artifact_sha256
    assert request.continuity_constraints_hash == "c" * 64
    assert request.qa_policy_content_hash == "a" * 64
    assert request.automatic_evaluator == AUTOMATIC
    assert request.required_reviewer == HUMAN
    assert request.media_identity == f"sha256:{committer.artifact_sha256}"
    assert service.calls == []
    assert factory_calls == []


@pytest.mark.parametrize("failure", ["artifact", "policy", "attempt"])
def test_request_rejects_stale_or_wrong_canonical_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure: str,
) -> None:
    coordinator, committer, _, _ = _coordinator(monkeypatch, tmp_path)
    if failure == "artifact":
        (committer.project_root / committer.fetch_pointer.artifact_path).write_bytes(
            b"replacement"
        )
        attempt_id = "attempt-1"
    elif failure == "policy":
        committer.policy.content_hash = "f" * 64
        attempt_id = "attempt-1"
    else:
        attempt_id = "wrong-attempt"

    with pytest.raises(AiVideoError) as caught:
        coordinator.prepare_request(attempt_id=attempt_id)

    assert caught.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_decision_requires_sealed_hash_and_nonblank_locked_identity() -> None:
    request = HumanReviewRequestV1.create(
        attempt_id="attempt-1",
        source_shot_id="source",
        target_shot_id="target",
        target_shot_content_hash="a" * 64,
        resolved_generation_hash="b" * 64,
        artifact_sha256="c" * 64,
        continuity_constraints_hash="d" * 64,
        qa_policy_content_hash="e" * 64,
        automatic_evaluator=AUTOMATIC,
        required_reviewer=HUMAN,
        media_identity=f"sha256:{'c' * 64}",
    )
    tampered = _decision(request).model_dump(mode="json")
    tampered["rationale"] = "changed after sealing"
    with pytest.raises(ValidationError, match="content hash"):
        HumanReviewDecisionV1.model_validate(tampered)
    with pytest.raises(ValidationError):
        HumanReviewDecisionV1.create(
            **{
                **_decision(request).model_dump(
                    mode="python", exclude={"content_hash"}
                ),
                "reviewer_identity": ToolIdentity(name=" ", version="1"),
            }
        )


def test_validate_consumes_exact_decision_and_only_calls_existing_service(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    coordinator, _, service, factory_calls = _coordinator(monkeypatch, tmp_path)
    request = coordinator.prepare_request(attempt_id="attempt-1")
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(
        _decision(request).model_dump_json(indent=2), encoding="utf-8"
    )

    result = coordinator.validate_and_activate(
        attempt_id="attempt-1", decision_path=decision_path
    )

    assert result == {"attempt_id": "attempt-1", "activated": True}
    assert len(factory_calls) == 1
    assert len(service.calls) == 1


@pytest.mark.parametrize(
    ("decision_change", "expected_code"),
    [
        ({"review_request_content_hash": "f" * 64}, ErrorCode.REVIEW_EVIDENCE_INVALID),
        ({"reviewer_identity": AUTOMATIC}, ErrorCode.REVIEW_EVIDENCE_INVALID),
        ({"identity": "NOT_SURE"}, ErrorCode.REVIEW_EVIDENCE_INVALID),
    ],
)
def test_stale_wrong_identity_or_not_sure_decision_fails_before_gpu_lease(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    decision_change: dict[str, object],
    expected_code: ErrorCode,
) -> None:
    lease_calls = 0

    @contextmanager
    def gpu_execution_lease():
        nonlocal lease_calls
        lease_calls += 1
        yield

    coordinator, _, service, factory_calls = _coordinator(
        monkeypatch, tmp_path, gpu_execution_lease=gpu_execution_lease
    )
    request = coordinator.prepare_request(attempt_id="attempt-1")
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(
        _decision(request, **decision_change).model_dump_json(), encoding="utf-8"
    )

    with pytest.raises(AiVideoError) as caught:
        coordinator.validate_and_activate(
            attempt_id="attempt-1", decision_path=decision_path
        )

    assert caught.value.code is expected_code
    assert lease_calls == 0
    assert factory_calls == []
    assert service.calls == []


def test_missing_decision_gpu_busy_and_invalid_runtime_fail_without_advancement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    coordinator, _, service, factory_calls = _coordinator(monkeypatch, tmp_path)
    with pytest.raises(AiVideoError) as missing:
        coordinator.validate_and_activate(
            attempt_id="attempt-1", decision_path=tmp_path / "missing.json"
        )
    assert missing.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID
    assert service.calls == factory_calls == []

    @contextmanager
    def busy_lease():
        raise AiVideoError(
            ErrorCode.PRODUCTION_STATE_BUSY,
            "Local continuity evaluator is busy.",
            retryable=True,
        )
        yield

    busy, _, busy_service, busy_factory_calls = _coordinator(
        monkeypatch, tmp_path / "busy", gpu_execution_lease=busy_lease
    )
    busy_request = busy.prepare_request(attempt_id="attempt-1")
    busy_decision = tmp_path / "busy-decision.json"
    busy_decision.write_text(_decision(busy_request).model_dump_json(), encoding="utf-8")
    with pytest.raises(AiVideoError) as unavailable:
        busy.validate_and_activate(
            attempt_id="attempt-1", decision_path=busy_decision
        )
    assert unavailable.value.code is ErrorCode.PRODUCTION_STATE_BUSY
    assert busy_service.calls == busy_factory_calls == []

    def invalid_factory(**_kwargs):
        raise ValueError("invalid sealed runtime")

    invalid, _, invalid_service, _ = _coordinator(
        monkeypatch,
        tmp_path / "invalid",
        reviewer_factory=invalid_factory,
    )
    invalid_request = invalid.prepare_request(attempt_id="attempt-1")
    invalid_decision = tmp_path / "invalid-decision.json"
    invalid_decision.write_text(
        _decision(invalid_request).model_dump_json(), encoding="utf-8"
    )
    with pytest.raises(AiVideoError) as sealed:
        invalid.validate_and_activate(
            attempt_id="attempt-1", decision_path=invalid_decision
        )
    assert sealed.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID
    assert invalid_service.calls == []


def test_existing_evidence_replays_without_decision_gpu_or_reviewer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def forbidden_gpu_lease():
        raise AssertionError("replay must not acquire GPU")

    coordinator, committer, service, factory_calls = _coordinator(
        monkeypatch, tmp_path, gpu_execution_lease=forbidden_gpu_lease
    )
    committer.state.continuity_evaluation = SimpleNamespace(evidence=object())

    result = coordinator.validate_and_activate(
        attempt_id="attempt-1", decision_path=tmp_path / "missing.json"
    )

    assert result["activated"] is True
    assert factory_calls == []
    assert service.calls == [None]


def test_gpu_lease_covers_reviewer_construction_and_service_execution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    events: list[str] = []

    @contextmanager
    def lease():
        events.append("acquire")
        try:
            yield
        finally:
            events.append("release")

    def factory(*, config, human_fallback, human_fallback_identity):
        assert events == ["acquire"]

        def reviewer(held_fd, request, measured, policy_hash):
            assert events == ["acquire"]
            return human_fallback(held_fd, request, measured, policy_hash)

        return reviewer

    coordinator, _, _, _ = _coordinator(
        monkeypatch,
        tmp_path,
        gpu_execution_lease=lease,
        reviewer_factory=factory,
    )
    request = coordinator.prepare_request(attempt_id="attempt-1")
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(_decision(request).model_dump_json(), encoding="utf-8")

    coordinator.validate_and_activate(
        attempt_id="attempt-1", decision_path=decision_path
    )

    assert events == ["acquire", "release"]


def test_lease_acquisition_is_typed_and_service_error_propagates_after_release(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    @contextmanager
    def broken_lease():
        raise RuntimeError("lock backend unavailable")
        yield

    broken, _, _, _ = _coordinator(
        monkeypatch,
        tmp_path / "broken",
        gpu_execution_lease=broken_lease,
    )
    broken_request = broken.prepare_request(attempt_id="attempt-1")
    broken_decision = tmp_path / "broken-decision.json"
    broken_decision.write_text(
        _decision(broken_request).model_dump_json(), encoding="utf-8"
    )
    with pytest.raises(AiVideoError) as unavailable:
        broken.validate_and_activate(
            attempt_id="attempt-1", decision_path=broken_decision
        )
    assert unavailable.value.code is ErrorCode.PRODUCTION_STATE_BUSY

    events: list[str] = []

    @contextmanager
    def lease():
        events.append("acquire")
        try:
            yield
        finally:
            events.append("release")

    coordinator, _, service, _ = _coordinator(
        monkeypatch,
        tmp_path / "service-error",
        gpu_execution_lease=lease,
    )
    request = coordinator.prepare_request(attempt_id="attempt-1")
    decision = tmp_path / "service-error-decision.json"
    decision.write_text(_decision(request).model_dump_json(), encoding="utf-8")
    expected = AiVideoError(
        ErrorCode.VIDEO_PROVIDER_FAILED,
        "Injected downstream failure.",
    )

    def fail_service(**_kwargs):
        raise expected

    service.fetch_and_activate = fail_service
    with pytest.raises(AiVideoError) as caught:
        coordinator.validate_and_activate(
            attempt_id="attempt-1", decision_path=decision
        )
    assert caught.value is expected
    assert events == ["acquire", "release"]


def test_runtime_guard_rejects_policy_rotation_before_intent_or_evaluator(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    inner_calls: list[str] = []

    class InnerReviewer:
        def create_intent(self, request, measured, policy_hash):
            inner_calls.append("intent")
            raise AssertionError("stale decision must fail before durable intent")

        def __call__(self, held_fd, request, measured, policy_hash):
            inner_calls.append("evaluate")
            raise AssertionError("stale decision must fail before evaluator")

    coordinator, committer, service, _ = _coordinator(
        monkeypatch,
        tmp_path,
        reviewer_factory=lambda **_kwargs: InnerReviewer(),
    )
    request = coordinator.prepare_request(attempt_id="attempt-1")
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(_decision(request).model_dump_json(), encoding="utf-8")

    def raced_fetch_and_activate(*, attempt_id, continuity_reviewer):
        committer.policy.content_hash = "f" * 64
        measured = MeasuredVideoMetadata(
            container_name="mp4",
            codec_name="h264",
            width=320,
            height=180,
            fps_numerator=24,
            fps_denominator=1,
            duration_milliseconds=1000,
            frame_count=24,
            audio_stream_count=0,
            size_bytes=len(committer.artifact_bytes),
            artifact_sha256=committer.artifact_sha256,
        )
        continuity_reviewer.create_intent(
            committer.request, measured, committer.policy.content_hash
        )
        raise AssertionError("guard should reject before service can continue")

    service.fetch_and_activate = raced_fetch_and_activate

    with pytest.raises(AiVideoError) as caught:
        coordinator.validate_and_activate(
            attempt_id="attempt-1", decision_path=decision_path
        )

    assert caught.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID
    assert inner_calls == []


def test_unexpected_reentry_pass_uses_non_inverted_evidence_meaning(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured = []

    def factory(*, config, human_fallback, human_fallback_identity):
        def reviewer(held_fd, request, measured, policy_hash):
            evidence = human_fallback(held_fd, request, measured, policy_hash)
            captured.append(evidence)
            return evidence

        return reviewer

    coordinator, _, _, _ = _coordinator(
        monkeypatch, tmp_path, reviewer_factory=factory
    )
    request = coordinator.prepare_request(attempt_id="attempt-1")
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(_decision(request).model_dump_json(), encoding="utf-8")

    coordinator.validate_and_activate(
        attempt_id="attempt-1", decision_path=decision_path
    )

    assert captured[0].unexpected_reentry is False
    assert captured[0].coverage_complete is True


# ---------------------------------------------------------------------------
# T1: validate_once seam (Console validate action)
# ---------------------------------------------------------------------------


class _ValidateOnlyService:
    """Records which VideoGenerationService seam the coordinator invokes."""

    def __init__(self, committer: _FakeCommitter) -> None:
        self.committer = committer
        self.validate_calls: list[object] = []
        self.activate_calls: list[object] = []
        self.fetch_and_activate_calls: list[object] = []

    def validate_once(self, *, attempt_id: str, continuity_reviewer=None):
        self.validate_calls.append((attempt_id, continuity_reviewer))
        return {"attempt_id": attempt_id, "validated": True}

    def activate_once(self, *, attempt_id: str):
        self.activate_calls.append(attempt_id)
        return {"attempt_id": attempt_id, "activated": True}

    def fetch_and_activate(self, *, attempt_id: str, continuity_reviewer=None):
        self.fetch_and_activate_calls.append((attempt_id, continuity_reviewer))
        return {"attempt_id": attempt_id, "activated": True}


def _coordinator_with_validate_only_service(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    gpu_execution_lease=lambda: nullcontext(),
    reviewer_factory=None,
):
    import ai_video.production.continuity_review_coordinator as coordinator_module

    committer = _FakeCommitter(tmp_path)
    service = _ValidateOnlyService(committer)
    monkeypatch.setattr(
        coordinator_module,
        "load_qa_policy",
        lambda _root, _pointer: committer.policy,
    )
    factory_calls: list[object] = []

    def default_factory(*, config, human_fallback, human_fallback_identity):
        factory_calls.append((config, human_fallback, human_fallback_identity))
        return human_fallback

    coordinator = ContinuityReviewCoordinator(
        committer=committer,
        video_service=service,  # type: ignore[arg-type]
        reviewer_config=_config(),
        reviewer_identity=HUMAN,
        gpu_execution_lease=gpu_execution_lease,
        reviewer_factory=reviewer_factory or default_factory,
    )
    return coordinator, committer, service, factory_calls


def test_validate_once_seam_is_exposed_on_coordinator() -> None:
    """T1 requires ContinuityReviewCoordinator.validate_once to exist."""

    assert hasattr(ContinuityReviewCoordinator, "validate_once"), (
        "ContinuityReviewCoordinator must expose validate_once as a public seam"
    )


def test_validate_once_invokes_only_service_validate_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """validate_once must delegate to video_service.validate_once only."""

    coordinator, _, service, factory_calls = _coordinator_with_validate_only_service(
        monkeypatch, tmp_path
    )
    request = coordinator.prepare_request(attempt_id="attempt-1")
    decision = _decision(request)

    result = coordinator.validate_once(attempt_id="attempt-1", decision=decision)

    assert result == {"attempt_id": "attempt-1", "validated": True}
    assert len(service.validate_calls) == 1
    assert len(service.activate_calls) == 0
    assert len(service.fetch_and_activate_calls) == 0
    assert factory_calls, "validate_once must construct the reviewer exactly once"


def test_validate_once_rejects_stale_request_hash_before_gpu_lease(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Stale review_request_content_hash must fail before acquiring the GPU."""

    lease_calls = 0

    @contextmanager
    def gpu_execution_lease():
        nonlocal lease_calls
        lease_calls += 1
        yield

    coordinator, _, service, factory_calls = _coordinator_with_validate_only_service(
        monkeypatch, tmp_path, gpu_execution_lease=gpu_execution_lease
    )
    request = coordinator.prepare_request(attempt_id="attempt-1")
    stale_decision = _decision(request, review_request_content_hash="f" * 64)

    with pytest.raises(AiVideoError) as caught:
        coordinator.validate_once(attempt_id="attempt-1", decision=stale_decision)

    assert caught.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID
    assert lease_calls == 0
    assert factory_calls == []
    assert service.validate_calls == []


def test_validate_once_requires_exact_decision_model_before_gpu_lease(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    @contextmanager
    def gpu_execution_lease():
        raise AssertionError("GPU must not be acquired for an unvalidated model")
        yield

    coordinator, _, service, factory_calls = _coordinator_with_validate_only_service(
        monkeypatch, tmp_path, gpu_execution_lease=gpu_execution_lease
    )

    with pytest.raises(AiVideoError) as caught:
        coordinator.validate_once(  # type: ignore[arg-type]
            attempt_id="attempt-1",
            decision={"reviewer_identity": HUMAN},
        )

    assert caught.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID
    assert factory_calls == []
    assert service.validate_calls == []


def test_validate_once_rejects_wrong_reviewer_identity_before_gpu_lease(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Wrong reviewer identity must fail before any side effects."""

    @contextmanager
    def gpu_execution_lease():
        raise AssertionError("GPU must not be acquired for a stale decision")
        yield

    coordinator, _, service, factory_calls = _coordinator_with_validate_only_service(
        monkeypatch, tmp_path, gpu_execution_lease=gpu_execution_lease
    )
    request = coordinator.prepare_request(attempt_id="attempt-1")
    wrong_reviewer = _decision(request, reviewer_identity=AUTOMATIC)

    with pytest.raises(AiVideoError) as caught:
        coordinator.validate_once(
            attempt_id="attempt-1", decision=wrong_reviewer
        )

    assert caught.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID
    assert factory_calls == []
    assert service.validate_calls == []


def test_validate_once_rejects_incomplete_axes_before_gpu_lease(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """NOT_SURE on any axis must be rejected before acquiring the GPU."""

    lease_calls = 0

    @contextmanager
    def gpu_execution_lease():
        nonlocal lease_calls
        lease_calls += 1
        yield

    coordinator, _, service, factory_calls = _coordinator_with_validate_only_service(
        monkeypatch, tmp_path, gpu_execution_lease=gpu_execution_lease
    )
    request = coordinator.prepare_request(attempt_id="attempt-1")
    incomplete = _decision(request, identity="NOT_SURE")

    with pytest.raises(AiVideoError) as caught:
        coordinator.validate_once(attempt_id="attempt-1", decision=incomplete)

    assert caught.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID
    assert lease_calls == 0
    assert factory_calls == []
    assert service.validate_calls == []


def test_validate_once_rejects_gpu_busy_without_calling_service(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A typed GPU busy error must surface and skip the validate service call."""

    @contextmanager
    def busy_lease():
        raise AiVideoError(
            ErrorCode.PRODUCTION_STATE_BUSY,
            "Local continuity evaluator is busy.",
            retryable=True,
        )
        yield

    coordinator, _, service, factory_calls = _coordinator_with_validate_only_service(
        monkeypatch, tmp_path, gpu_execution_lease=busy_lease
    )
    request = coordinator.prepare_request(attempt_id="attempt-1")
    decision = _decision(request)

    with pytest.raises(AiVideoError) as caught:
        coordinator.validate_once(attempt_id="attempt-1", decision=decision)

    assert caught.value.code is ErrorCode.PRODUCTION_STATE_BUSY
    assert factory_calls == []
    assert service.validate_calls == []


def test_validate_once_rejects_invalid_reviewer_runtime_without_calling_service(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A reviewer factory failure must surface as a typed error."""

    def invalid_factory(**_kwargs):
        raise ValueError("invalid sealed runtime")

    coordinator, _, service, factory_calls = _coordinator_with_validate_only_service(
        monkeypatch,
        tmp_path,
        reviewer_factory=invalid_factory,
    )
    request = coordinator.prepare_request(attempt_id="attempt-1")
    decision = _decision(request)

    with pytest.raises(AiVideoError) as caught:
        coordinator.validate_once(attempt_id="attempt-1", decision=decision)

    assert caught.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID
    assert factory_calls == []
    assert service.validate_calls == []


def test_validate_once_legacy_validate_and_activate_remains_compatible(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The legacy validate_and_activate(decision_path) API must keep working."""

    coordinator, _, service, factory_calls = _coordinator(
        monkeypatch, tmp_path
    )
    request = coordinator.prepare_request(attempt_id="attempt-1")
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(
        _decision(request).model_dump_json(), encoding="utf-8"
    )

    result = coordinator.validate_and_activate(
        attempt_id="attempt-1", decision_path=decision_path
    )

    assert result == {"attempt_id": "attempt-1", "activated": True}
    assert service.calls, "Legacy validate_and_activate must still invoke the service"
    assert len(factory_calls) == 1
    # Legacy path uses fetch_and_activate, never the new validate_once seam.
    assert not hasattr(service, "validate_once") or not getattr(
        service, "validate_once_calls", []
    )


def test_validate_once_does_not_call_fetch_and_activate_or_activate_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The new seam must never invoke the legacy or activate actions."""

    coordinator, _, service, _ = _coordinator_with_validate_only_service(
        monkeypatch, tmp_path
    )
    request = coordinator.prepare_request(attempt_id="attempt-1")
    decision = _decision(request)

    coordinator.validate_once(attempt_id="attempt-1", decision=decision)

    assert service.fetch_and_activate_calls == []
    assert service.activate_calls == []
    assert len(service.validate_calls) == 1
