from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.video import (
    VideoGenerationMode,
    VideoGenerationPreview,
    VideoProviderCapabilities,
    VideoSubmission,
    VideoTaskState,
    build_video_paid_permit_binding,
)
from ai_video.production.video_fake import (
    FakeVideoScenario,
    ScriptedFakeVideoProvider,
)
from ai_video.production.video_compiler import (
    ProviderRequirementUnsupported,
    require_compiled_provider_request,
)
from ai_video.production.shot_router import (
    AdapterCompilerContract,
    MotionRequirement as RouterMotionRequirement,
    VideoGenerationResolver,
)
from test_production_video import (
    _paid_authorization,
    _paid_preview,
    _paid_submit_receipt,
    _request,
    _variant,
)
from video_provider_contract import (
    PaidProviderPermitDouble,
    VideoProviderContractCase,
    assert_video_provider_contract,
)
from test_production_shot_router import (
    _capabilities as _router_capabilities,
    _context as _router_context,
    _lifecycle as _router_lifecycle,
    _output as _router_output,
    _policy as _router_policy,
    _profile as _router_profile,
    _variant as _router_variant,
    _verified_requirement,
)


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
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    authorization = _paid_authorization(paid_preview)
    binding = build_video_paid_permit_binding(
        resolved,
        video_preview,
        paid_preview,
        authorization,
    )
    result = provider.submit(
        resolved,
        video_preview,
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


def test_fake_compiler_projects_bound_requirement_without_provider_side_effects():
    context = _router_context(
        motion=RouterMotionRequirement.FREE_COMPLEX,
        important=False,
    )
    capabilities = _router_capabilities(
        _router_variant(VideoGenerationMode.TEXT_TO_VIDEO)
    )
    provider = ScriptedFakeVideoProvider(
        capabilities=capabilities,
        artifact_bytes=_artifact_bytes(),
    )
    compiler_contract = AdapterCompilerContract.create(
        compiler_id="fake-video-compiler",
        compiler_version="1",
    )
    projection = _verified_requirement(context)
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_router_policy(),
        provider_profile=_router_profile(),
        capabilities=capabilities,
        selected_capability_id="capability-text_to_video",
        output_requirement=_router_output(),
        lifecycle=_router_lifecycle(context),
        compiler_contract=compiler_contract,
    )
    assert routing.provider_bound_request is not None

    first = provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )
    second = provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )

    assert first == second
    assert first.outcome == "compiled"
    assert first.request.requirement_hash == projection.requirement.requirement_hash
    assert first.request.provider_bound_request_hash == (
        routing.provider_bound_request.provider_bound_request_hash
    )
    resolved = provider.resolve(first.request)
    assert resolved.requirement_hash == projection.requirement.requirement_hash
    assert resolved.provider_bound_request_hash == (
        routing.provider_bound_request.provider_bound_request_hash
    )
    assert resolved.activation_scope is not None
    assert resolved.activation_scope.request == first.request
    for field in (
        "generation_mode=",
        "continuity_mode=",
        "motion_requirement=",
        "audio_need=",
        "open_state=",
        "identity_preservation=",
        "scene_id=",
        "space_screen_direction=",
        "axis_camera=",
        "action_progression=",
        "motion_direction=",
        "camera_framing=",
        "camera_position_lock=",
        "camera_orientation_lock=",
        "pacing_tempo=",
        "quality_objective=",
    ):
        assert field in first.provider_native_prompt
    assert provider.call_counts == type(provider.call_counts)(0, 1, 0, 0, 0, 0)


def test_fake_compiler_returns_typed_unsupported_for_wrong_compiler_contract():
    context = _router_context(
        motion=RouterMotionRequirement.FREE_COMPLEX,
        important=False,
    )
    capabilities = _router_capabilities(
        _router_variant(VideoGenerationMode.TEXT_TO_VIDEO)
    )
    projection = _verified_requirement(context)
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_router_policy(),
        provider_profile=_router_profile(),
        capabilities=capabilities,
        selected_capability_id="capability-text_to_video",
        output_requirement=_router_output(),
        lifecycle=_router_lifecycle(context),
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="another-compiler",
            compiler_version="1",
        ),
    )
    assert routing.provider_bound_request is not None
    provider = ScriptedFakeVideoProvider(
        capabilities=capabilities,
        artifact_bytes=_artifact_bytes(),
    )

    result = provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )

    assert isinstance(result, ProviderRequirementUnsupported)
    assert result.retryable is False
    assert result.prompt_text is None
    assert result.payload is None
    assert provider.call_counts == type(provider.call_counts)(0, 0, 0, 0, 0, 0)
    with pytest.raises(AiVideoError) as exc:
        require_compiled_provider_request(result)
    assert exc.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED
    assert exc.value.retryable is False


def test_fake_provider_contract_and_success_sequence_are_deterministic():
    provider = _provider()
    assert_video_provider_contract(
        _provider,
        (
            VideoProviderContractCase(
                request=_request(),
                unsupported_request=_request(
                    mode=VideoGenerationMode.TEXT_TO_VIDEO,
                    image_bindings=(),
                ),
                paid_preview_factory=lambda resolved, video_preview: _paid_preview(
                    resolved,
                    video_preview=video_preview,
                ),
                authorization_factory=_paid_authorization,
                submit_receipt_factory=lambda resolved, preview, result: (
                    _paid_submit_receipt(
                        resolved,
                        preview,
                        external_effect_id=result.external_effect_id,
                    )
                ),
                expected_artifact_sha256=hashlib.sha256(
                    _artifact_bytes()
                ).hexdigest(),
            ),
        ),
    )
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
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    authorization = _paid_authorization(paid_preview)
    binding = build_video_paid_permit_binding(
        resolved,
        video_preview,
        paid_preview,
        authorization,
    )
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
            video_preview,
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
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    authorization = _paid_authorization(paid_preview)
    permit = PaidProviderPermitDouble(
        build_video_paid_permit_binding(
            resolved,
            video_preview,
            paid_preview,
            authorization,
        )
    )
    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            video_preview,
            paid_preview,
            authorization,
            permit,
        )
    assert exc_info.value.code is error_code
    assert provider.call_counts.submit == 1


@pytest.mark.parametrize(
    "paid_preview_changes",
    [
        {"destination": "https://other.invalid"},
        {"estimated_cost_upper_bound_microunits": 1_000_001},
        {"egress_item_ids": ("reference",)},
    ],
)
def test_fake_submit_rejects_paid_preview_that_differs_from_video_preview(
    paid_preview_changes: dict[str, object],
):
    provider = _provider()
    resolved = provider.resolve(_request())
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(
        resolved,
        video_preview=video_preview,
        **paid_preview_changes,
    )
    authorization = _paid_authorization(paid_preview)

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            video_preview,
            paid_preview,
            authorization,
            PaidProviderPermitDouble({}),
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert provider.call_counts.submit == 0


def test_fake_submit_rejects_jointly_substituted_video_and_paid_previews():
    provider = _provider()
    resolved = provider.resolve(_request())
    substituted_video_preview = VideoGenerationPreview.create(
        resolved=resolved,
        estimated_cost_upper_bound_microunits=1_000_000,
        currency="USD",
        destination="https://other.invalid",
        egress_item_ids=("prompt",),
    )
    substituted_paid_preview = _paid_preview(
        resolved,
        video_preview=substituted_video_preview,
    )
    authorization = _paid_authorization(substituted_paid_preview)
    permit = PaidProviderPermitDouble(
        build_video_paid_permit_binding(
            resolved,
            substituted_video_preview,
            substituted_paid_preview,
            authorization,
        )
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            substituted_video_preview,
            substituted_paid_preview,
            authorization,
            permit,
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert provider.call_counts.submit == 0


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
