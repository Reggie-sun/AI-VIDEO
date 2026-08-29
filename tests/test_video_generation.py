"""Tests for VideoGenerationService.validate_once / activate_once seam.

These tests focus on the *seam contract* required by the T1 provider console
execution control slice:

* ``validate_once`` performs exactly one canonical ``prepare_video_activation_candidate``
  action and never mutates the active pointer.
* ``activate_once`` performs exactly one canonical ``activate_video_candidate``
  action and never re-runs the preparer.
* The pre-existing ``fetch_and_activate`` keeps its combined legacy behavior.
"""

from __future__ import annotations

import inspect
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import StateCommitStatus, VideoAttemptPhase
from ai_video.production.video_generation import VideoGenerationService
from ai_video.production.video import VideoSubmission


@contextmanager
def _null_lease():
    yield None


class _FakeCommitter:
    def __init__(self, *, phase: VideoAttemptPhase) -> None:
        self.phase = phase
        self.prepare_calls = 0
        self.activate_calls = 0
        self.attempt = SimpleNamespace(
            attempt_id="attempt-1",
            status=StateCommitStatus.RUNNING,
            video_generation_state=SimpleNamespace(
                phase=phase,
                request=SimpleNamespace(output_asset_id="video-asset-1"),
            ),
        )

    def _read_manifest(self):
        return SimpleNamespace(active_project=None)

    def _video_attempt(self, _manifest, attempt_id: str):
        if attempt_id != self.attempt.attempt_id:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Video attempt missing.",
                retryable=False,
            )
        return self.attempt

    def prepare_video_activation_candidate(self, **_kwargs):
        self.prepare_calls += 1
        self.attempt = SimpleNamespace(
            attempt_id=self.attempt.attempt_id,
            status=StateCommitStatus.RUNNING,
            video_generation_state=SimpleNamespace(
                phase=VideoAttemptPhase.CANDIDATE,
                request=self.attempt.video_generation_state.request,
            ),
        )
        return {"prepared": True}

    def activate_video_candidate(self, **_kwargs):
        self.activate_calls += 1
        self.attempt = SimpleNamespace(
            attempt_id=self.attempt.attempt_id,
            status=StateCommitStatus.SUCCEEDED,
            video_generation_state=SimpleNamespace(
                phase=VideoAttemptPhase.ACTIVATE,
                request=self.attempt.video_generation_state.request,
            ),
        )
        return {"activated": True}


class _FakeProvider:
    pass


def _service(*, phase: VideoAttemptPhase):
    committer = _FakeCommitter(phase=phase)
    service = VideoGenerationService(committer=committer, provider=_FakeProvider())
    return service, committer


def test_video_generation_service_exposes_validate_once_and_activate_once() -> None:
    """T1 seam requires both validate_once() and activate_once() public methods."""

    assert hasattr(VideoGenerationService, "validate_once"), (
        "VideoGenerationService must expose validate_once() as a public seam"
    )
    assert hasattr(VideoGenerationService, "activate_once"), (
        "VideoGenerationService must expose activate_once() as a public seam"
    )
    for name in ("validate_once", "activate_once"):
        method = getattr(VideoGenerationService, name)
        assert callable(method), f"{name} must be callable"


def test_remote_reference_lease_reopens_only_activated_source_evidence(
    monkeypatch,
) -> None:
    request = object()
    submit_receipt = object()
    submission = SimpleNamespace(submission_fingerprint="a" * 64)
    observation = SimpleNamespace(observation_fingerprint="b" * 64)
    fetch_receipt = SimpleNamespace(
        fetch_fingerprint="c" * 64,
        remote_materialization=SimpleNamespace(content_hash="d" * 64),
    )
    lease = object()
    replay_calls = []
    state = SimpleNamespace(
        phase=VideoAttemptPhase.ACTIVATE,
        request="request-pointer",
        latest_observation="observation-pointer",
        fetch_receipt="fetch-pointer",
    )
    attempt = SimpleNamespace(
        attempt_id="attempt-1",
        status=StateCommitStatus.SUCCEEDED,
        video_generation_state=state,
        paid_provider_state=SimpleNamespace(submit_receipt="submit-pointer"),
    )

    class Committer:
        def replay_active_video_generation(self, *, attempt_id):
            replay_calls.append(attempt_id)
            return object()

        def _read_manifest(self):
            return object()

        def _video_attempt(self, _manifest, attempt_id):
            assert attempt_id == "attempt-1"
            return attempt

        def _reopen_video_request(self, pointer):
            assert pointer == "request-pointer"
            return request

        def _reopen_paid_submit(self, pointer):
            assert pointer == "submit-pointer"
            return submit_receipt

        def _reopen_video_status(self, pointer):
            assert pointer == "observation-pointer"
            return observation

        def _reopen_video_fetch(self, pointer):
            assert pointer == "fetch-pointer"
            return fetch_receipt

    class Provider:
        def refresh_provider_output_reference_lease(self, *values):
            assert values[:4] == (
                submission,
                submit_receipt,
                observation,
                fetch_receipt,
            )
            refresh_permit = values[4]
            assert refresh_permit._consume(
                submission_fingerprint=submission.submission_fingerprint,
                observation_fingerprint=observation.observation_fingerprint,
                fetch_fingerprint=fetch_receipt.fetch_fingerprint,
                materialization_receipt_id=(
                    fetch_receipt.remote_materialization.content_hash
                ),
            )
            return lease

    monkeypatch.setattr(
        VideoSubmission,
        "from_paid_submit_receipt",
        lambda **_kwargs: submission,
    )
    service = VideoGenerationService(committer=Committer(), provider=Provider())

    assert (
        service.refresh_remote_reference_lease_once(attempt_id="attempt-1")
        is lease
    )
    assert replay_calls == ["attempt-1", "attempt-1"]


def test_remote_reference_lease_rejects_superseded_active_source_before_provider():
    class Committer:
        def replay_active_video_generation(self, *, attempt_id):
            assert attempt_id == "historical-attempt"
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="Video generation success is not exact active evidence.",
                retryable=False,
            )

    class Provider:
        def refresh_provider_output_reference_lease(self, *_values):
            raise AssertionError("stale source must stop before Provider access")

    service = VideoGenerationService(committer=Committer(), provider=Provider())

    with pytest.raises(AiVideoError) as exc_info:
        service.refresh_remote_reference_lease_once(attempt_id="historical-attempt")

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_validate_once_signature_accepts_continuity_reviewer() -> None:
    """validate_once must accept a continuity_reviewer argument (continuity seam)."""

    sig = inspect.signature(VideoGenerationService.validate_once)
    assert "attempt_id" in sig.parameters
    assert "continuity_reviewer" in sig.parameters, (
        "validate_once must forward continuity_reviewer to the canonical preparer"
    )


def test_activate_once_signature_accepts_only_attempt_id() -> None:
    """activate_once must be a one-action seam that only takes attempt_id."""

    sig = inspect.signature(VideoGenerationService.activate_once)
    assert list(sig.parameters) == ["self", "attempt_id"], (
        "activate_once must accept exactly (self, *, attempt_id) — no other inputs"
    )
    attempt_id_param = sig.parameters["attempt_id"]
    assert attempt_id_param.kind is inspect.Parameter.KEYWORD_ONLY, (
        "attempt_id must be keyword-only so the activate seam is unambiguous"
    )


def test_validate_once_runs_only_prepare_when_phase_is_validate() -> None:
    service, committer = _service(phase=VideoAttemptPhase.VALIDATE)

    result = service.validate_once(attempt_id="attempt-1", continuity_reviewer=None)

    assert committer.prepare_calls == 1
    assert committer.activate_calls == 0
    assert result == {"prepared": True}


def test_validate_once_rejects_non_validate_phase() -> None:
    service, committer = _service(phase=VideoAttemptPhase.SUBMITTED)

    with pytest.raises(AiVideoError) as caught:
        service.validate_once(attempt_id="attempt-1", continuity_reviewer=None)

    assert caught.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert committer.prepare_calls == 0
    assert committer.activate_calls == 0


@pytest.mark.parametrize(
    "phase",
    [
        VideoAttemptPhase.REQUEST,
        VideoAttemptPhase.SUBMITTED,
        VideoAttemptPhase.POLLING,
        VideoAttemptPhase.FETCH,
        VideoAttemptPhase.CANDIDATE,
        VideoAttemptPhase.ACTIVATE,
    ],
)
def test_validate_once_strictly_requires_validate_phase(phase: VideoAttemptPhase) -> None:
    service, committer = _service(phase=phase)

    with pytest.raises(AiVideoError) as caught:
        service.validate_once(attempt_id="attempt-1", continuity_reviewer=None)

    assert caught.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert committer.prepare_calls == 0
    assert committer.activate_calls == 0


def test_activate_once_runs_only_activate_when_phase_is_candidate() -> None:
    service, committer = _service(phase=VideoAttemptPhase.CANDIDATE)

    result = service.activate_once(attempt_id="attempt-1")

    assert committer.activate_calls == 1
    assert committer.prepare_calls == 0
    assert result == {"activated": True}


def test_activate_once_preserves_recovered_interrupted_candidate_contract() -> None:
    service, committer = _service(phase=VideoAttemptPhase.CANDIDATE)
    committer.attempt.status = StateCommitStatus.INTERRUPTED

    result = service.activate_once(attempt_id="attempt-1")

    assert result == {"activated": True}
    assert committer.activate_calls == 1


@pytest.mark.parametrize(
    "phase",
    [
        VideoAttemptPhase.REQUEST,
        VideoAttemptPhase.SUBMITTED,
        VideoAttemptPhase.POLLING,
        VideoAttemptPhase.FETCH,
        VideoAttemptPhase.VALIDATE,
        VideoAttemptPhase.ACTIVATE,
    ],
)
def test_activate_once_strictly_requires_candidate_phase(phase: VideoAttemptPhase) -> None:
    service, committer = _service(phase=phase)

    with pytest.raises(AiVideoError) as caught:
        service.activate_once(attempt_id="attempt-1")

    assert caught.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert committer.activate_calls == 0
    assert committer.prepare_calls == 0


def test_validate_then_activate_is_two_separate_actions() -> None:
    """The two seams together must compose exactly one prepare + one activate."""

    service, committer = _service(phase=VideoAttemptPhase.VALIDATE)

    service.validate_once(attempt_id="attempt-1", continuity_reviewer=None)
    # After validate_once the canonical state should advance to CANDIDATE.
    service.activate_once(attempt_id="attempt-1")

    assert committer.prepare_calls == 1
    assert committer.activate_calls == 1


def test_fetch_and_activate_legacy_path_remains_present() -> None:
    """The existing fetch_and_activate API must keep its combined semantics."""

    assert hasattr(VideoGenerationService, "fetch_and_activate")
    legacy = VideoGenerationService.fetch_and_activate
    assert callable(legacy)
    sig = inspect.signature(legacy)
    # Legacy accepts continuity_reviewer and probe parameters.
    assert "attempt_id" in sig.parameters
    assert "continuity_reviewer" in sig.parameters
    assert "probe" in sig.parameters


def test_local_submit_pre_submit_guard_denies_before_preview_or_intent() -> None:
    committer = _FakeCommitter(phase=VideoAttemptPhase.REQUEST)
    committer.attempt.paid_provider_state = None
    request = SimpleNamespace(execution_stack_hash="a" * 64)
    committer._reopen_video_request = MagicMock(return_value=request)
    committer.record_local_video_submit_intent = MagicMock()
    provider = MagicMock()
    guard_error = AiVideoError(
        code=ErrorCode.PRODUCTION_STATE_INVALID,
        user_message="M0 execution stack drifted.",
        retryable=False,
    )
    guard = MagicMock(side_effect=guard_error)
    service = VideoGenerationService(committer=committer, provider=provider)

    with pytest.raises(AiVideoError, match="execution stack"):
        service.submit_local_once(
            attempt_id="attempt-1",
            pre_submit_guard=guard,
        )

    guard.assert_called_once_with(request)
    provider.preview.assert_not_called()
    committer.record_local_video_submit_intent.assert_not_called()


def test_stack_bound_local_submit_cannot_omit_pre_submit_guard() -> None:
    committer = _FakeCommitter(phase=VideoAttemptPhase.REQUEST)
    committer.attempt.paid_provider_state = None
    request = SimpleNamespace(execution_stack_hash="a" * 64)
    committer._reopen_video_request = MagicMock(return_value=request)
    committer.record_local_video_submit_intent = MagicMock()
    provider = MagicMock()
    service = VideoGenerationService(committer=committer, provider=provider)

    with pytest.raises(AiVideoError, match="requires a pre-submit guard"):
        service.submit_local_once(attempt_id="attempt-1")

    provider.preview.assert_not_called()
    committer.record_local_video_submit_intent.assert_not_called()


def test_validate_once_does_not_invoke_legacy_fetch_and_activate() -> None:
    """validate_once must call the canonical preparer, never fetch_and_activate."""

    service, committer = _service(phase=VideoAttemptPhase.VALIDATE)
    # Replace the committer with a mock that records all interactions.
    sentinel = MagicMock()
    sentinel._read_manifest = committer._read_manifest
    sentinel._video_attempt = committer._video_attempt
    sentinel.prepare_video_activation_candidate = MagicMock(
        side_effect=committer.prepare_video_activation_candidate
    )
    service._committer = sentinel  # type: ignore[assignment]

    service.validate_once(attempt_id="attempt-1", continuity_reviewer=None)

    sentinel.prepare_video_activation_candidate.assert_called_once()
    assert not hasattr(sentinel, "fetch_and_activate") or not any(
        call.args and call.args[0] == "fetch_and_activate"
        for call in sentinel.method_calls
    ), "validate_once must not delegate to the legacy fetch_and_activate"


def test_activate_once_does_not_re_invoke_prepare() -> None:
    """activate_once must only delegate to activate_video_candidate."""

    service, committer = _service(phase=VideoAttemptPhase.CANDIDATE)
    sentinel = MagicMock()
    sentinel._read_manifest = committer._read_manifest
    sentinel._video_attempt = committer._video_attempt
    sentinel.activate_video_candidate = MagicMock(
        side_effect=committer.activate_video_candidate
    )
    service._committer = sentinel  # type: ignore[assignment]

    service.activate_once(attempt_id="attempt-1")

    sentinel.activate_video_candidate.assert_called_once()
    sentinel.prepare_video_activation_candidate.assert_not_called()
