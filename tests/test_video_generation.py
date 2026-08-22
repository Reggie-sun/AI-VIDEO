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
