from __future__ import annotations

from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    PaidProviderAttemptPhase,
    ProductionManifest,
    StateCommitStatus,
    VideoAttemptPhase,
)
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video import VideoProviderCapabilities, VideoTaskState
from ai_video.production.video_fake import FakeVideoScenario, ScriptedFakeVideoProvider
from ai_video.production.video_generation import VideoGenerationService
from production_project_factory import (
    make_manifest_23_project,
    write_production_project,
)
from test_production_video import (
    _paid_authorization,
    _paid_preview,
    _request,
    _variant,
)


FIXTURE = Path(__file__).parent / "fixtures/generated_video/fake-video.mp4"
ATTEMPT_ID = "video-state-attempt-1"


def _provider(
    *, scenario: FakeVideoScenario | None = None
) -> ScriptedFakeVideoProvider:
    return ScriptedFakeVideoProvider(
        capabilities=VideoProviderCapabilities.create(
            provider_name="hailuo",
            variants=(_variant(),),
        ),
        artifact_bytes=FIXTURE.read_bytes(),
        scenario=scenario,
    )


def _p8_root(root: Path) -> None:
    write_production_project(root)
    make_manifest_23_project(root)
    path = root / "state/manifest.json"
    manifest = ProductionManifest.model_validate_json(path.read_bytes())
    path.write_text(
        manifest.model_copy(update={"schema_version": "2.7"}).model_dump_json(
            indent=2
        ),
        encoding="utf-8",
    )


def _runtime(
    root: Path,
    *,
    scenario: FakeVideoScenario | None = None,
):
    _p8_root(root)
    provider = _provider(scenario=scenario)
    resolved = provider.resolve(_request())
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(
        resolved,
        attempt_id=ATTEMPT_ID,
        video_preview=video_preview,
    )
    authorization = _paid_authorization(paid_preview)
    committer = ProductionStateCommitter(
        root,
        paid_provider_authorizer=(
            lambda exact: authorization if exact == paid_preview else None
        ),
        paid_provider_clock=lambda: authorization.issued_at,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    return committer, service, provider, resolved, paid_preview


def test_video_service_persists_request_submit_poll_and_fetch_without_second_task_id(
    tmp_path: Path,
):
    committer, service, provider, resolved, paid_preview = _runtime(tmp_path)

    started = service.start(attempt_id=ATTEMPT_ID, request=resolved)
    started_state = started.attempts[-1].video_generation_state
    assert started_state is not None
    assert started_state.phase is VideoAttemptPhase.REQUEST
    assert (tmp_path / started_state.request.path).is_file()

    service.submit_once(
        attempt_id=ATTEMPT_ID,
        paid_preview=paid_preview,
        reservation_id="video-reservation-1",
    )
    submitted = committer._read_manifest().attempts[-1]
    submitted_state = submitted.video_generation_state
    assert submitted_state is not None
    assert submitted_state.phase is VideoAttemptPhase.SUBMITTED
    assert submitted_state.paid_submit_receipt is not None
    submit_receipt = committer._reopen_paid_submit(
        submitted_state.paid_submit_receipt
    )
    assert submit_receipt.external_effect_id == "fake-task-1"
    assert "external_effect_id" not in submitted_state.model_dump(mode="json")

    observations = [service.refresh_once(attempt_id=ATTEMPT_ID) for _ in range(3)]
    assert [item.state for item in observations] == [
        VideoTaskState.QUEUED,
        VideoTaskState.RUNNING,
        VideoTaskState.SUCCEEDED,
    ]
    assert service.resume_next_action(attempt_id=ATTEMPT_ID) == "fetch"
    fetched = service.fetch_once(attempt_id=ATTEMPT_ID)
    fetched_path = tmp_path / fetched.relative_path
    assert fetched.relative_path.suffix == ".mp4"
    assert not fetched.relative_path.name.endswith(".mp4.part")
    assert fetched_path.read_bytes() == FIXTURE.read_bytes()
    assert list(fetched_path.parent.glob("*.part")) == []
    assert provider.call_counts.submit == 1
    assert provider.call_counts.fetch == 1


def test_recovery_before_gate_marks_request_interrupted_without_provider_call(
    tmp_path: Path,
):
    committer, service, provider, resolved, _ = _runtime(tmp_path)
    service.start(attempt_id=ATTEMPT_ID, request=resolved)

    report = ProductionStateCommitter(tmp_path).recover()
    attempt = ProductionStateCommitter(tmp_path)._read_manifest().attempts[-1]

    assert report.manifest_revision_after > report.manifest_revision_before
    assert attempt.status is StateCommitStatus.INTERRUPTED
    assert provider.call_counts.submit == 0


def test_recovery_of_unresolved_submit_intent_is_outcome_unknown_and_never_remints(
    tmp_path: Path,
):
    committer, service, provider, resolved, paid_preview = _runtime(tmp_path)
    service.start(attempt_id=ATTEMPT_ID, request=resolved)
    committer.record_paid_provider_submit_intent(
        paid_preview,
        reservation_id="video-reservation-1",
    )

    ProductionStateCommitter(tmp_path).recover()
    recovered = ProductionStateCommitter(tmp_path)._read_manifest().attempts[-1]
    assert recovered.status is StateCommitStatus.OUTCOME_UNKNOWN
    assert recovered.paid_provider_state is not None
    assert (
        recovered.paid_provider_state.phase
        is PaidProviderAttemptPhase.OUTCOME_UNKNOWN
    )
    assert provider.call_counts.submit == 0
    assert (
        ProductionStateCommitter(tmp_path).video_resume_next_action(
            attempt_id=ATTEMPT_ID
        )
        == "stop"
    )


def test_rejected_submit_persists_known_no_effect_and_never_remints(tmp_path: Path):
    committer, service, provider, resolved, paid_preview = _runtime(
        tmp_path,
        scenario=FakeVideoScenario(submit_outcome="rejected"),
    )
    service.start(attempt_id=ATTEMPT_ID, request=resolved)

    with pytest.raises(AiVideoError) as exc_info:
        service.submit_once(
            attempt_id=ATTEMPT_ID,
            paid_preview=paid_preview,
            reservation_id="video-reservation-1",
        )

    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    attempt = committer._read_manifest().attempts[-1]
    assert attempt.status is StateCommitStatus.FAILED
    assert attempt.paid_provider_state is not None
    assert attempt.paid_provider_state.phase is PaidProviderAttemptPhase.KNOWN_NO_EFFECT
    assert service.resume_next_action(attempt_id=ATTEMPT_ID) == "stop"
    assert provider.call_counts.submit == 1


def test_ambiguous_submit_persists_outcome_unknown_and_never_remints(tmp_path: Path):
    committer, service, provider, resolved, paid_preview = _runtime(
        tmp_path,
        scenario=FakeVideoScenario(submit_outcome="outcome_unknown"),
    )
    service.start(attempt_id=ATTEMPT_ID, request=resolved)

    with pytest.raises(AiVideoError) as exc_info:
        service.submit_once(
            attempt_id=ATTEMPT_ID,
            paid_preview=paid_preview,
            reservation_id="video-reservation-1",
        )

    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    attempt = committer._read_manifest().attempts[-1]
    assert attempt.status is StateCommitStatus.OUTCOME_UNKNOWN
    assert attempt.paid_provider_state is not None
    assert attempt.paid_provider_state.phase is PaidProviderAttemptPhase.OUTCOME_UNKNOWN
    assert service.resume_next_action(attempt_id=ATTEMPT_ID) == "stop"
    assert provider.call_counts.submit == 1


def test_restart_polls_durable_task_and_fetch_failure_never_resubmits(
    tmp_path: Path,
):
    committer, service, provider, resolved, paid_preview = _runtime(
        tmp_path,
        scenario=FakeVideoScenario(
            status_events=(VideoTaskState.SUCCEEDED,),
            fetch_outcome="failure",
        ),
    )
    service.start(attempt_id=ATTEMPT_ID, request=resolved)
    service.submit_once(
        attempt_id=ATTEMPT_ID,
        paid_preview=paid_preview,
        reservation_id="video-reservation-1",
    )

    restarted = VideoGenerationService(
        committer=ProductionStateCommitter(tmp_path),
        provider=provider,
    )
    ProductionStateCommitter(tmp_path).recover()
    assert restarted.resume_next_action(attempt_id=ATTEMPT_ID) == "poll"
    restarted.refresh_once(attempt_id=ATTEMPT_ID)
    with pytest.raises(AiVideoError):
        restarted.fetch_once(attempt_id=ATTEMPT_ID)

    fetch_root = tmp_path / "state/video-generation/fetch"
    assert list(fetch_root.glob("*.part")) == []
    assert list(fetch_root.glob("*.mp4")) == []
    assert restarted.resume_next_action(attempt_id=ATTEMPT_ID) == "fetch"
    assert provider.call_counts.submit == 1
    assert provider.call_counts.status == 1
    assert provider.call_counts.fetch == 1
