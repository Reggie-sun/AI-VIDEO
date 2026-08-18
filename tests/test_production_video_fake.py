from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.video import (
    VideoProviderCapabilities,
    VideoSubmission,
    VideoTaskState,
    build_video_paid_permit_binding,
)
from ai_video.production.video_fake import (
    FakeVideoScenario,
    ScriptedFakeVideoProvider,
)
from test_production_video import (
    _paid_authorization,
    _paid_preview,
    _paid_submit_receipt,
    _request,
    _variant,
)
from video_provider_contract import PaidProviderPermitDouble, assert_video_provider_contract


FIXTURE_PATH = Path(__file__).parent / "fixtures/generated_video/fake-video.mp4"


def _artifact_bytes() -> bytes:
    return FIXTURE_PATH.read_bytes()


def _provider(*, scenario: FakeVideoScenario | None = None) -> ScriptedFakeVideoProvider:
    return ScriptedFakeVideoProvider(
        capabilities=VideoProviderCapabilities.create(
            provider_name="hailuo",
            variants=(_variant(),),
        ),
        artifact_bytes=_artifact_bytes(),
        scenario=scenario,
    )


def _accepted_submission(provider: ScriptedFakeVideoProvider):
    resolved = provider.resolve(_request())
    paid_preview = _paid_preview(resolved)
    authorization = _paid_authorization(paid_preview)
    binding = build_video_paid_permit_binding(resolved, paid_preview, authorization)
    result = provider.submit(
        resolved,
        paid_preview,
        authorization,
        PaidProviderPermitDouble(binding),
    )
    paid_receipt = _paid_submit_receipt(
        resolved,
        paid_preview,
        external_effect_id=result.external_effect_id,
    )
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved,
        receipt=paid_receipt,
    )
    return resolved, paid_receipt, submission


def test_fake_provider_contract_and_success_sequence_are_deterministic():
    provider = _provider()
    assert_video_provider_contract(provider=provider)
    _, paid_receipt, submission = _accepted_submission(provider)
    observations = [provider.get_status(submission, paid_receipt) for _ in range(3)]
    sink = BytesIO()
    receipt = provider.fetch(submission, paid_receipt, observations[-1], sink)

    assert [item.state for item in observations] == [
        VideoTaskState.QUEUED,
        VideoTaskState.RUNNING,
        VideoTaskState.SUCCEEDED,
    ]
    assert sink.getvalue() == _artifact_bytes()
    assert receipt.artifact_sha256 == hashlib.sha256(_artifact_bytes()).hexdigest()
    assert provider.call_counts.submit == 1
    assert provider.call_counts.status == 3
    assert provider.call_counts.fetch == 1


@pytest.mark.parametrize("permit_kind", ["missing", "mismatched", "reused"])
def test_fake_metered_submit_rejects_bad_permit_with_zero_submit_calls(permit_kind: str):
    provider = _provider()
    resolved = provider.resolve(_request())
    paid_preview = _paid_preview(resolved)
    authorization = _paid_authorization(paid_preview)
    binding = build_video_paid_permit_binding(resolved, paid_preview, authorization)
    permit = PaidProviderPermitDouble(
        {**binding, "request_fingerprint": "f" * 64}
        if permit_kind == "mismatched"
        else binding
    )
    if permit_kind == "reused":
        assert permit._consume_paid_provider_operation_permit(**binding)

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            paid_preview,
            authorization,
            None if permit_kind == "missing" else permit,
        )
    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED
    assert provider.call_counts.submit == 0


@pytest.mark.parametrize(
    ("outcome", "error_code"),
    [
        ("rejected", ErrorCode.VIDEO_PROVIDER_FAILED),
        ("outcome_unknown", ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN),
    ],
)
def test_fake_submit_terminal_outcomes_are_typed(outcome: str, error_code: ErrorCode):
    provider = _provider(scenario=FakeVideoScenario(submit_outcome=outcome))
    resolved = provider.resolve(_request())
    paid_preview = _paid_preview(resolved)
    authorization = _paid_authorization(paid_preview)
    permit = PaidProviderPermitDouble(
        build_video_paid_permit_binding(resolved, paid_preview, authorization)
    )
    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(resolved, paid_preview, authorization, permit)
    assert exc_info.value.code is error_code
    assert provider.call_counts.submit == 1


def test_fake_transient_status_failure_does_not_resubmit():
    provider = _provider(
        scenario=FakeVideoScenario(
            status_events=("transient_error", VideoTaskState.SUCCEEDED)
        )
    )
    _, paid_receipt, submission = _accepted_submission(provider)
    with pytest.raises(AiVideoError) as exc_info:
        provider.get_status(submission, paid_receipt)
    assert exc_info.value.retryable is True
    succeeded = provider.get_status(submission, paid_receipt)
    assert succeeded.state is VideoTaskState.SUCCEEDED
    assert provider.call_counts.submit == 1
    assert provider.call_counts.status == 2


def test_fake_terminal_failure_and_timeout_sequences_are_explicit():
    failed = _provider(
        scenario=FakeVideoScenario(status_events=(VideoTaskState.FAILED,))
    )
    _, failed_receipt, failed_submission = _accepted_submission(failed)
    assert failed.get_status(failed_submission, failed_receipt).state is VideoTaskState.FAILED

    queued = _provider(
        scenario=FakeVideoScenario(status_events=(VideoTaskState.QUEUED,))
    )
    _, queued_receipt, queued_submission = _accepted_submission(queued)
    assert [
        queued.get_status(queued_submission, queued_receipt).state for _ in range(3)
    ] == [VideoTaskState.QUEUED] * 3


@pytest.mark.parametrize("fetch_outcome", ["failure", "tampered"])
def test_fake_fetch_failure_and_tampered_bytes_are_observable(fetch_outcome: str):
    provider = _provider(scenario=FakeVideoScenario(fetch_outcome=fetch_outcome))
    _, paid_receipt, submission = _accepted_submission(provider)
    observation = provider.get_status(submission, paid_receipt)
    while observation.state is not VideoTaskState.SUCCEEDED:
        observation = provider.get_status(submission, paid_receipt)
    sink = BytesIO()
    if fetch_outcome == "failure":
        with pytest.raises(AiVideoError):
            provider.fetch(submission, paid_receipt, observation, sink)
        return
    receipt = provider.fetch(submission, paid_receipt, observation, sink)
    assert hashlib.sha256(sink.getvalue()).hexdigest() != receipt.artifact_sha256


def test_two_fake_instances_return_identical_fixture_hash():
    hashes = []
    for _ in range(2):
        provider = _provider()
        _, paid_receipt, submission = _accepted_submission(provider)
        observation = provider.get_status(submission, paid_receipt)
        while observation.state is not VideoTaskState.SUCCEEDED:
            observation = provider.get_status(submission, paid_receipt)
        sink = BytesIO()
        provider.fetch(submission, paid_receipt, observation, sink)
        hashes.append(hashlib.sha256(sink.getvalue()).hexdigest())
    assert len(set(hashes)) == 1
