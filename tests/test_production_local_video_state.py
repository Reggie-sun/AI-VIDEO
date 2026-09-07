from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.local_h3_provider_family import LocalH3VideoProviderFamily
from ai_video.production.local_video import (
    LocalVideoFetchReceipt,
    LocalVideoSubmission,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
    LocalVideoTaskObservation,
)
from ai_video.production.models import (
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    SourceReference,
    StateCommitStatus,
    VideoAttemptPhase,
)
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.ecommerce_media_acceptance import (
    create_qingyan_ecommerce_acceptance_profile,
)
from ai_video.production.ecommerce_ad_coordinator import (
    EcommerceStopReason,
    EcommerceVideoGenerationFacade,
    run_ecommerce_ad_generation,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video import (
    BillingKind,
    GeneratedCommercialShotBinding,
    ProviderProfilePointer,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoOutputRequirement,
    VideoProviderCapabilities,
    VideoProviderRegistry,
    VideoTaskState,
)
from ai_video.production.video_fake import ScriptedFakeVideoProvider
from ai_video.production.video_generation import VideoGenerationService
from ai_video.production.video_compiler import (
    ProviderNativePrompt,
    compile_provider_video_request,
)
from ai_video.production.project import load_production_project
from production_project_factory import (
    make_p8_video_candidate_preparer,
    make_p8_video_generation_base,
)
from production_generation_execution_factory import (
    activate_generated_video_shot,
    activate_fixture_generation_qa_policy,
    prepare_generation_execution,
)


FIXTURE = Path(__file__).parent / "fixtures/generated_video/fake-video.mp4"
ATTEMPT_ID = "local-h3-video-attempt"


class LocalVideoProviderDouble:
    def __init__(
        self,
        *,
        capabilities,
        artifact_bytes: bytes,
        native_prompt_text: str = "Generate the sealed local video request.",
        submit_error: ErrorCode | None = None,
        status_state: VideoTaskState = VideoTaskState.SUCCEEDED,
        status_error: ErrorCode | None = None,
    ) -> None:
        self._delegate = ScriptedFakeVideoProvider(
            capabilities=capabilities,
            artifact_bytes=artifact_bytes,
        )
        self._artifact_bytes = artifact_bytes
        self._native_prompt_text = native_prompt_text
        self.submit_error = submit_error
        self.status_state = status_state
        self.status_error = status_error
        self.submit_calls = 0
        self.status_calls = 0
        self.fetch_calls = 0

    def capabilities(self):
        return self._delegate.capabilities()

    def resolve(self, request):
        return self._delegate.resolve(request)

    def compile_request(self, provider_bound, requirement):
        prompt_text = self._native_prompt_text
        return compile_provider_video_request(
            provider_bound=provider_bound,
            requirement=requirement,
            compiler_id="local-video-state-fixture",
            compiler_version="1",
            capabilities=self.capabilities(),
            native_prompt=ProviderNativePrompt(
                grammar_contract="local-video-state-fixture-v1",
                prompt_text=prompt_text,
                prompt_sha256=hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
            ),
        )

    def preview(self, request):
        return self._delegate.preview(request)

    def preflight(self, request) -> None:
        return None

    def submit_local(self, request, preview, intent, permit):
        if preview != self.preview(request):
            raise AssertionError("preview mismatch")
        if self.submit_error is ErrorCode.VIDEO_PROVIDER_FAILED:
            raise AiVideoError(
                code=self.submit_error,
                user_message="local pre-submit validation failed",
                retryable=False,
            )
        if not permit._consume_local_video_submit_permit(
            intent_fingerprint=intent.intent_fingerprint,
            request_fingerprint=request.resolved_generation_hash,
        ):
            raise AiVideoError(
                code=ErrorCode.VIDEO_PROVIDER_FAILED,
                user_message="local permit rejected",
                retryable=False,
            )
        self.submit_calls += 1
        if self.submit_error is not None:
            raise AiVideoError(
                code=self.submit_error,
                user_message="local submit did not produce a durable task identity",
                retryable=False,
            )
        return LocalVideoSubmitResult.create(
            resolved=request,
            provider_request_id="comfy-prompt-1",
            submitted_at=datetime(2026, 8, 19, tzinfo=UTC),
        )

    def get_local_status(self, request, submission: LocalVideoSubmission):
        self.status_calls += 1
        if self.status_error is not None:
            raise AiVideoError(
                code=self.status_error,
                user_message="local poll outcome is unknown",
                retryable=False,
            )
        return LocalVideoTaskObservation.create(
            submission=submission,
            state=self.status_state,
            provider_file_id=(
                "comfy-output-1"
                if self.status_state is VideoTaskState.SUCCEEDED
                else None
            ),
            progress_milli=(
                1000 if self.status_state is VideoTaskState.SUCCEEDED else None
            ),
            observed_at=datetime(2026, 8, 19, 0, 0, 1, tzinfo=UTC),
        )

    def fetch_local(self, request, submission, observation, sink):
        self.fetch_calls += 1
        sink.write(self._artifact_bytes)
        return LocalVideoFetchReceipt.create(
            submission=submission,
            observation=observation,
            content_type="video/mp4",
            size_bytes=len(self._artifact_bytes),
            artifact_sha256=hashlib.sha256(self._artifact_bytes).hexdigest(),
            fetched_at=datetime(2026, 8, 19, 0, 0, 2, tzinfo=UTC),
        )


def _runtime(
    root: Path,
    *,
    t8_t2va: bool = False,
    execution_stack_hash: str | None = None,
    submit_error: ErrorCode | None = None,
    status_state: VideoTaskState = VideoTaskState.SUCCEEDED,
    status_error: ErrorCode | None = None,
    commercial: bool = False,
    commercial_plan_hash: str = "a" * 64,
    prompt_text: str = "Continue the camera move from the exact terminal frame.",
):
    inputs = make_p8_video_generation_base(
        root, schema_version="2.13" if commercial else "2.8"
    )
    inputs = activate_generated_video_shot(root=root, inputs=inputs)
    shot = inputs.project.shots[0]
    source = inputs.project.registry.assets[0]
    output = VideoOutputRequirement(
        duration_seconds=1,
        width=64,
        height=64,
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=t8_t2va,
    )
    profile_sha = "a" * 64
    provider_name = "comfy-local-h3-t8" if t8_t2va else "comfy-local-h3"
    provider_kind = "minimax_h3_t8_t2va" if t8_t2va else "minimax_h3_fl2va"
    model_id = "minimax-h3-t8-t2va-quality" if t8_t2va else "minimax-h3-fl2va"
    generation_mode = (
        VideoGenerationMode.TEXT_TO_VIDEO
        if t8_t2va
        else VideoGenerationMode.IMAGE_TO_VIDEO
    )
    commercial_profile = (
        create_qingyan_ecommerce_acceptance_profile() if commercial else None
    )
    inputs = activate_fixture_generation_qa_policy(root=root, inputs=inputs, output=output)
    shot = inputs.project.shots[0]
    source = inputs.project.registry.assets[0]
    if commercial:
        from test_production_generated_video_e2e import (
            COMMERCIAL_EVALUATOR,
            _commercial_projection,
        )

        commercial_binding = GeneratedCommercialShotBinding.create(
            ad_creative_plan_id="qingyan-ad-plan",
            ad_creative_plan_hash=commercial_plan_hash,
            commercial_execution_projection_hash=(
                _commercial_projection(
                    shot.shot_id,
                    plan_hash=commercial_plan_hash,
                ).projection_hash
            ),
            target_shot_id=shot.shot_id,
            profile_content_hash=commercial_profile.content_hash,
            applicable_requirement_ids=(
                commercial_profile.shot_requirement_ids[0],
                commercial_profile.shot_requirement_ids[1],
            ),
            expected_actor_ids=("qingyan-miao-girl", "qingyan-elder"),
            output_asset_id="local-h3-video-1",
        )
    else:
        commercial_binding = None
    request = VideoGenerationRequest.create(
        generation_id="local-h3-generation-1",
        provider_name=provider_name,
        provider_kind=provider_kind,
        model_id=model_id,
        provider_profile=ProviderProfilePointer(
            profile_id=(
                "minimax-h3-t8-t2va-quality" if t8_t2va else "minimax-h3-fl2va"
            ),
            profile_version="v1",
            profile_path=Path(f"provider-profiles/{profile_sha}.json"),
            profile_sha256=profile_sha,
        ),
        execution_stack_hash=execution_stack_hash,
        target_shot_id=shot.shot_id,
        target_shot_revision=shot.revision,
        target_shot_content_hash=shot.content_hash,
        target_asset_role=shot.required_asset_roles[0].role,
        target_visual_strategy="generated_video",
        mode=generation_mode,
        prompt_text=prompt_text,
        negative_prompt_text="",
        image_bindings=(
            ()
            if t8_t2va
            else (
                VideoImageReferenceBinding(
                    role="first_frame",
                    asset_id=source.asset_id,
                    asset_sha256=source.sha256,
                    mime_type=source.mime_type,
                    width=source.width or 64,
                    height=source.height or 64,
                    size_bytes=source.size_bytes,
                ),
            )
        ),
        commercial_binding=commercial_binding,
        seal_terminal_frame=not t8_t2va,
        output_requirement=output,
        seed=19,
        base_project=inputs.project.manifest.active_project,
        base_registry=inputs.project.manifest.active_registry,
        base_dependency_graph=inputs.project.manifest.active_dependency_graph,
        input_artifact_ids=(
            (shot.artifact_id,) if t8_t2va else (shot.artifact_id, source.asset_id)
        ),
        output_asset_id="local-h3-video-1",
    )
    variant = VideoCapabilityVariant(
        capability_id=(
            "minimax-h3-t8-t2va-quality-v1" if t8_t2va else "minimax-h3-fl2va-local"
        ),
        provider_kind=provider_kind,
        model_id=model_id,
        profile_version="v1",
        execution_kind=VideoExecutionKind.LOCAL,
        billing_kind=BillingKind.LOCAL_UNMETERED,
        mode=generation_mode,
        output=output,
        allowed_image_roles=(() if t8_t2va else ("first_frame", "last_frame")),
        required_first_frame=not t8_t2va,
        max_reference_count=0,
        allowed_image_mime_types=(() if t8_t2va else (source.mime_type,)),
        max_image_bytes=(1 if t8_t2va else max(source.size_bytes, 1)),
        min_image_width=1,
        min_image_height=1,
        negative_prompt_supported=False,
        seed_supported=True,
        fps_supported=True,
        idempotent_submit=False,
        lookup_supported=False,
    )
    provider = LocalVideoProviderDouble(
        capabilities=VideoProviderCapabilities.create(
            provider_name=provider_name, variants=(variant,)
        ),
        artifact_bytes=FIXTURE.read_bytes(),
        native_prompt_text=prompt_text,
        submit_error=submit_error,
        status_state=status_state,
        status_error=status_error,
    )
    resolved = provider.resolve(request)
    prepared = prepare_generation_execution(
        project=inputs.project,
        provider=provider,
        request=resolved,
        task_id="local-video-state-fixture",
        compiler_id="local-video-state-fixture",
        compiler_version="1",
    )
    committer = ProductionStateCommitter(
        root,
        video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        paid_provider_clock=lambda: datetime(2026, 8, 19, tzinfo=UTC),
    )
    if commercial_profile is not None:
        policy = seal_artifact(
            QaPolicy(
                artifact_id="qa-policy-local-commercial",
                revision=1,
                content_hash="0" * 64,
                creation_receipt_id="qa-policy-local-commercial",
                source_provenance=(
                    SourceReference(kind="derived", reference="local-fixture"),
                ),
                policy_id="qa-policy-local-commercial",
                policy_version="1",
                required_layers=(QaLayer.SEMANTIC,),
                technical_thresholds=QaTechnicalThresholds(
                    black_luma_max_milli=10,
                    silence_peak_max_millidb=-60_000,
                    clipping_peak_min_millidb=-100,
                ),
                layout_rules=QaLayoutRules(
                    safe_area_inset_milli=50,
                    caption_overflow_tolerance_milli=0,
                ),
                strategy_rules_version="1",
                semantic_requirement="required",
                semantic_authorities=(COMMERCIAL_EVALUATOR, *inputs.project.qa_policy.semantic_authorities),
                generation_acceptance=inputs.project.qa_policy.selected_generation_acceptance(),
                generation_evaluation_authorities=inputs.project.qa_policy.generation_evaluation_authorities,
                domain_acceptance=DomainAcceptancePolicy(
                    domain_id="ecommerce",
                    profile_id=commercial_profile.profile_id,
                    profile_version=commercial_profile.profile_version,
                    profile_content_hash=commercial_profile.content_hash,
                    profile_payload=commercial_profile.model_dump(mode="json"),
                    measurement_contract_version=(
                        commercial_profile.measurement_contract_version
                    ),
                    required_requirement_ids=(
                        commercial_profile.required_requirement_ids
                    ),
                ),
            )
        )
        current = committer._read_manifest()
        committer.activate_qa_policy(
            policy,
            expected_manifest_revision=current.manifest_revision,
            attempt_id="activate-local-commercial-policy",
        )
    return inputs, provider, prepared.resolved, prepared.binding, committer


def test_local_video_lifecycle_never_claims_paid_authority_and_replays_exactly(
    tmp_path: Path,
) -> None:
    _, provider, resolved, execution_binding, committer = _runtime(tmp_path)
    service = VideoGenerationService(committer=committer, provider=provider)

    service.start(
        attempt_id=ATTEMPT_ID,
        request=resolved,
        execution_binding=execution_binding,
    )
    submission = service.submit_local_once(attempt_id=ATTEMPT_ID)
    observation = service.refresh_local_once(attempt_id=ATTEMPT_ID)

    assert submission.provider_request_id == "comfy-prompt-1"
    assert observation.state is VideoTaskState.SUCCEEDED
    assert service.resume_next_action(attempt_id=ATTEMPT_ID) == "fetch"
    state = committer._read_manifest().attempts[-1]
    assert state.paid_provider_state is None
    assert state.video_generation_state is not None
    assert state.video_generation_state.local_submit_intent is not None
    assert state.video_generation_state.local_submit_receipt is not None
    assert state.video_generation_state.local_latest_observation is not None

    activated = service.fetch_and_activate(attempt_id=ATTEMPT_ID)
    active_state = activated.attempts[-1]
    assert active_state.status is StateCommitStatus.SUCCEEDED
    assert active_state.video_generation_state is not None
    assert active_state.video_generation_state.phase is VideoAttemptPhase.ACTIVATE
    assert active_state.video_generation_state.local_fetch_receipt is not None
    assert active_state.video_generation_state.fetch_receipt is None
    selected = load_production_project(tmp_path / "project.yaml")
    generated = next(
        item for item in selected.registry.assets if item.asset_id == resolved.output_asset_id
    )
    assert generated.cost_receipt_id is None
    assert generated.egress.remote is False
    assert generated.video_metadata is not None
    provenance_payload = json.loads(
        (
            tmp_path
            / "state/video-generation/provenance"
            / f"{generated.video_metadata.provenance_receipt_id}.json"
        ).read_text(encoding="utf-8")
    )
    assert "local_submit_result_fingerprint" in provenance_payload
    assert "paid_submit_receipt_fingerprint" not in provenance_payload
    assert active_state.video_generation_state.terminal_frame_evidence is not None

    replayed = service.fetch_and_activate(attempt_id=ATTEMPT_ID)
    assert replayed == activated
    assert provider.submit_calls == 1
    assert provider.status_calls == 1
    assert provider.fetch_calls == 1

    with pytest.raises(AiVideoError) as exc_info:
        service.submit_local_once(attempt_id=ATTEMPT_ID)
    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert provider.submit_calls == 1


def test_local_ecommerce_facade_uses_real_service_and_replays_zero_effect(
    tmp_path: Path,
) -> None:
    from test_production_generated_video_e2e import (
        _CountingCommercialShotReviewer,
        _commercial_handoff,
    )

    _, provider, resolved, execution_binding, committer = _runtime(tmp_path, commercial=True)
    facade = EcommerceVideoGenerationFacade(
        service=VideoGenerationService(committer=committer, provider=provider),
        attempt_id=ATTEMPT_ID,
        request=resolved,
        lane="local",
        commercial_reviewer=_CountingCommercialShotReviewer(),
        execution_binding=execution_binding,
    )
    binding = resolved.commercial_binding
    assert binding is not None
    handoff = _commercial_handoff(binding.target_shot_id)

    result = run_ecommerce_ad_generation(
        handoff, facades={binding.target_shot_id: facade}
    )
    first_counts = (provider.submit_calls, provider.status_calls, provider.fetch_calls)
    replay = run_ecommerce_ad_generation(
        handoff, facades={binding.target_shot_id: facade}
    )

    assert result.complete is True
    assert replay.complete is True
    assert first_counts == (1, 1, 1)
    assert (provider.submit_calls, provider.status_calls, provider.fetch_calls) == first_counts


@pytest.mark.parametrize("preexisting_attempt", (True, False))
def test_local_ecommerce_resume_rejects_durable_request_mismatch_before_effect(
    tmp_path: Path,
    preexisting_attempt: bool,
) -> None:
    from test_production_generated_video_e2e import (
        _CountingCommercialShotReviewer,
        _commercial_handoff,
    )

    expected_root = tmp_path / "expected"
    durable_root = tmp_path / "durable"
    _, _, expected_request, expected_execution_binding, _ = _runtime(expected_root, commercial=True)
    _, provider, durable_request, durable_execution_binding, committer = _runtime(
        durable_root,
        commercial=True,
        commercial_plan_hash="b" * 64,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    if preexisting_attempt:
        service.start(
            attempt_id=ATTEMPT_ID,
            request=durable_request,
            execution_binding=durable_execution_binding,
        )
    binding = expected_request.commercial_binding
    assert binding is not None
    facade = EcommerceVideoGenerationFacade(
        service=service,
        attempt_id=ATTEMPT_ID,
        request=expected_request,
        lane="local",
        commercial_reviewer=_CountingCommercialShotReviewer(),
        execution_binding=expected_execution_binding,
    )
    competing_start_done = preexisting_attempt

    def start_competing_request_after_preflight() -> bool:
        nonlocal competing_start_done
        if not competing_start_done:
            service.start(
                attempt_id=ATTEMPT_ID,
                request=durable_request,
                execution_binding=durable_execution_binding,
            )
            competing_start_done = True
        return False

    result = run_ecommerce_ad_generation(
        _commercial_handoff(binding.target_shot_id),
        facades={binding.target_shot_id: facade},
        stop_requested=start_competing_request_after_preflight,
    )

    assert result.stop_reason is EcommerceStopReason.CHECKPOINT_INVALID
    assert (provider.submit_calls, provider.status_calls, provider.fetch_calls) == (
        0,
        0,
        0,
    )


def test_local_ecommerce_duplicate_coordinator_claims_fetch_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from test_production_generated_video_e2e import (
        _CountingCommercialShotReviewer,
        _commercial_handoff,
    )

    _, provider, resolved, execution_binding, committer = _runtime(tmp_path, commercial=True)
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=ATTEMPT_ID,
        request=resolved,
        execution_binding=execution_binding,
    )
    service.submit_local_once(attempt_id=ATTEMPT_ID)
    service.refresh_local_once(attempt_id=ATTEMPT_ID)
    facade = EcommerceVideoGenerationFacade(
        service=service,
        attempt_id=ATTEMPT_ID,
        request=resolved,
        lane="local",
        commercial_reviewer=_CountingCommercialShotReviewer(),
        execution_binding=execution_binding,
    )
    binding = resolved.commercial_binding
    assert binding is not None
    handoff = _commercial_handoff(binding.target_shot_id)
    first_fetch_entered = threading.Event()
    release_first_fetch = threading.Event()
    fetch_invocations = 0
    original_fetch_local = provider.fetch_local

    def blocking_fetch_local(*args, **kwargs):
        nonlocal fetch_invocations
        fetch_invocations += 1
        if fetch_invocations == 1:
            first_fetch_entered.set()
            assert release_first_fetch.wait(timeout=10)
        return original_fetch_local(*args, **kwargs)

    monkeypatch.setattr(provider, "fetch_local", blocking_fetch_local)
    results = []
    first = threading.Thread(
        target=lambda: results.append(
            run_ecommerce_ad_generation(
                handoff,
                facades={binding.target_shot_id: facade},
            )
        )
    )
    first.start()
    assert first_fetch_entered.wait(timeout=10)
    duplicate = run_ecommerce_ad_generation(
        handoff,
        facades={binding.target_shot_id: facade},
    )
    release_first_fetch.set()
    first.join(timeout=10)

    assert first.is_alive() is False
    assert fetch_invocations == 1
    assert provider.fetch_calls == 1
    assert duplicate.stop_reason is EcommerceStopReason.SERVICE_STOP
    assert results[0].complete is True
    assert tuple(
        (tmp_path / "state/video-generation/fetch").glob(
            f"{ATTEMPT_ID}.*.mp4"
        )
    ) == ()


def test_local_ecommerce_guard_rechecks_completed_durable_request_identity(
    tmp_path: Path,
) -> None:
    from test_production_generated_video_e2e import (
        _CountingCommercialShotReviewer,
        _commercial_handoff,
    )

    _, _, expected_request, expected_execution_binding, _ = _runtime(
        tmp_path / "expected",
        commercial=True,
        prompt_text="Expected exact Qingyan commercial prompt.",
    )
    _, provider, competing_request, competing_execution_binding, committer = _runtime(
        tmp_path / "durable",
        commercial=True,
        prompt_text="Competing prompt with the same commercial binding.",
    )
    expected_binding = expected_request.commercial_binding
    competing_binding = competing_request.commercial_binding
    assert expected_binding == competing_binding
    assert (
        expected_request.resolved_generation_hash
        != competing_request.resolved_generation_hash
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    expected_facade = EcommerceVideoGenerationFacade(
        service=service,
        attempt_id=ATTEMPT_ID,
        request=expected_request,
        lane="local",
        commercial_reviewer=_CountingCommercialShotReviewer(),
        execution_binding=expected_execution_binding,
    )
    competing_facade = EcommerceVideoGenerationFacade(
        service=service,
        attempt_id=ATTEMPT_ID,
        request=competing_request,
        lane="local",
        commercial_reviewer=_CountingCommercialShotReviewer(),
        execution_binding=competing_execution_binding,
    )
    assert expected_binding is not None
    handoff = _commercial_handoff(expected_binding.target_shot_id)
    competing_complete = False

    def complete_competing_request_after_preflight() -> bool:
        nonlocal competing_complete
        if not competing_complete:
            competing = run_ecommerce_ad_generation(
                handoff,
                facades={expected_binding.target_shot_id: competing_facade},
            )
            assert competing.complete is True
            competing_complete = True
        return False

    result = run_ecommerce_ad_generation(
        handoff,
        facades={expected_binding.target_shot_id: expected_facade},
        stop_requested=complete_competing_request_after_preflight,
    )

    assert result.complete is False
    assert result.stop_reason is EcommerceStopReason.CHECKPOINT_INVALID
    assert provider.submit_calls == 1
    assert provider.status_calls == 1
    assert provider.fetch_calls == 1


def test_t8_t2va_reuses_local_intent_permit_and_state_lifecycle(tmp_path: Path) -> None:
    _, provider, resolved, execution_binding, committer = _runtime(tmp_path, t8_t2va=True)
    service = VideoGenerationService(committer=committer, provider=provider)

    service.start(
        attempt_id=ATTEMPT_ID,
        request=resolved,
        execution_binding=execution_binding,
    )
    submission = service.submit_local_once(attempt_id=ATTEMPT_ID)
    observation = service.refresh_local_once(attempt_id=ATTEMPT_ID)

    assert resolved.provider_name == "comfy-local-h3-t8"
    assert resolved.mode is VideoGenerationMode.TEXT_TO_VIDEO
    assert resolved.image_bindings == ()
    assert resolved.effective_output.native_audio is True
    assert submission.provider_request_id == "comfy-prompt-1"
    assert observation.state is VideoTaskState.SUCCEEDED
    state = committer._read_manifest().attempts[-1]
    assert state.paid_provider_state is None
    assert state.video_generation_state is not None
    assert state.video_generation_state.local_submit_intent is not None
    assert state.video_generation_state.local_submit_receipt is not None
    assert state.video_generation_state.local_latest_observation is not None
    assert service.resume_next_action(attempt_id=ATTEMPT_ID) == "fetch"
    assert provider.submit_calls == 1
    assert provider.status_calls == 1


def test_stack_bound_local_intent_requires_guard_inside_committer(
    tmp_path: Path,
) -> None:
    stack_hash = "e" * 64
    _, provider, resolved, execution_binding, committer = _runtime(
        tmp_path,
        execution_stack_hash=stack_hash,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=ATTEMPT_ID,
        request=resolved,
        execution_binding=execution_binding,
    )
    before = committer._read_manifest()
    preview = provider.preview(resolved)

    with pytest.raises(AiVideoError, match="requires a pre-submit guard"):
        committer.record_local_video_submit_intent(
            attempt_id=ATTEMPT_ID,
            preview=preview,
        )

    assert committer._read_manifest() == before
    calls: list[str] = []

    def guard(request) -> None:
        calls.append(request.execution_stack_hash)

    intent, _ = committer.record_local_video_submit_intent(
        attempt_id=ATTEMPT_ID,
        preview=preview,
        pre_submit_guard=guard,
    )

    assert calls == [stack_hash]
    assert intent.request_fingerprint == resolved.resolved_generation_hash
    assert provider.submit_calls == 0


def test_stack_drift_after_preview_denies_intent_permit_and_submit(
    tmp_path: Path,
) -> None:
    stack_hash = "e" * 64
    _, provider, resolved, execution_binding, committer = _runtime(
        tmp_path,
        execution_stack_hash=stack_hash,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=ATTEMPT_ID,
        request=resolved,
        execution_binding=execution_binding,
    )
    before = committer._read_manifest()
    guard_calls = 0

    def drifting_guard(request) -> None:
        nonlocal guard_calls
        guard_calls += 1
        assert request.execution_stack_hash == stack_hash
        if guard_calls == 2:
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_INVALID,
                user_message="M0 execution stack drifted after preview.",
                retryable=False,
            )

    with pytest.raises(AiVideoError, match="drifted after preview"):
        service.submit_local_once(
            attempt_id=ATTEMPT_ID,
            pre_submit_guard=drifting_guard,
        )

    assert guard_calls == 2
    assert provider._delegate.call_counts.preview == 1
    assert provider.submit_calls == 0
    assert committer._read_manifest() == before


def test_t8_family_registry_assembly_restarts_without_last_selected_state(
    tmp_path: Path,
) -> None:
    _, quality, resolved, execution_binding, committer = _runtime(tmp_path, t8_t2va=True)
    quality_variant = quality.capabilities().variants[0]
    turbo_variant = VideoCapabilityVariant.model_validate(
        {
            **quality_variant.model_dump(mode="python"),
            "capability_id": "minimax-h3-t8-t2va-turbo-v1",
            "provider_kind": "minimax_h3_t8_t2va_turbo",
            "model_id": "minimax-h3-t8-t2va-turbo",
        }
    )
    turbo = LocalVideoProviderDouble(
        capabilities=VideoProviderCapabilities.create(
            provider_name="comfy-local-h3-t8",
            variants=(turbo_variant,),
        ),
        artifact_bytes=FIXTURE.read_bytes(),
    )
    family = LocalH3VideoProviderFamily((quality, turbo))
    seedance = object()
    hailuo = object()
    registry = VideoProviderRegistry(
        (
            ("comfy-local-h3-t8", family),
            ("seedance", seedance),
            ("minimax_hailuo", hailuo),
        )
    )

    selected = registry.resolve(resolved.provider_name)
    assert selected is family
    assert registry.resolve("seedance") is seedance
    assert registry.resolve("minimax_hailuo") is hailuo

    service = VideoGenerationService(committer=committer, provider=selected)
    service.start(
        attempt_id=ATTEMPT_ID,
        request=resolved,
        execution_binding=execution_binding,
    )
    service.submit_local_once(attempt_id=ATTEMPT_ID)

    restarted_family = LocalH3VideoProviderFamily((quality, turbo))
    restarted_registry = VideoProviderRegistry(
        (("comfy-local-h3-t8", restarted_family),)
    )
    restarted_service = VideoGenerationService(
        committer=committer,
        provider=restarted_registry.resolve(resolved.provider_name),
    )
    observation = restarted_service.refresh_local_once(attempt_id=ATTEMPT_ID)
    candidate = restarted_service.fetch_local_once(attempt_id=ATTEMPT_ID)

    assert observation.state is VideoTaskState.SUCCEEDED
    assert isinstance(candidate.receipt, LocalVideoFetchReceipt)
    assert quality.submit_calls == 1
    assert quality.status_calls == 1
    assert quality.fetch_calls == 1
    assert turbo.submit_calls == 0
    assert turbo.status_calls == 0
    assert turbo.fetch_calls == 0


def test_local_submit_intent_recovery_stops_without_resubmit(tmp_path: Path) -> None:
    _, provider, resolved, execution_binding, committer = _runtime(tmp_path)
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=ATTEMPT_ID,
        request=resolved,
        execution_binding=execution_binding,
    )
    preview = provider.preview(resolved)
    intent, _ = committer.record_local_video_submit_intent(
        attempt_id=ATTEMPT_ID, preview=preview
    )
    assert isinstance(intent, LocalVideoSubmitIntent)

    ProductionStateCommitter(tmp_path).recover()
    recovered = ProductionStateCommitter(tmp_path)._read_manifest().attempts[-1]
    assert recovered.status in {
        StateCommitStatus.OUTCOME_UNKNOWN,
        StateCommitStatus.INTERRUPTED,
    }
    assert provider.submit_calls == 0
    assert (
        ProductionStateCommitter(tmp_path).video_resume_next_action(
            attempt_id=ATTEMPT_ID
        )
        == "stop"
    )


def test_local_submit_unknown_is_durable_and_never_resubmitted(tmp_path: Path) -> None:
    _, provider, resolved, execution_binding, committer = _runtime(
        tmp_path, submit_error=ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=ATTEMPT_ID,
        request=resolved,
        execution_binding=execution_binding,
    )

    with pytest.raises(AiVideoError) as exc_info:
        service.submit_local_once(attempt_id=ATTEMPT_ID)
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    manifest = committer._read_manifest()
    attempt = manifest.attempts[-1]
    assert attempt.status is StateCommitStatus.OUTCOME_UNKNOWN
    assert attempt.video_generation_state is not None
    assert attempt.video_generation_state.phase is VideoAttemptPhase.SUBMIT_INTENT
    assert service.resume_next_action(attempt_id=ATTEMPT_ID) == "stop"
    assert provider.submit_calls == 1

    with pytest.raises(AiVideoError):
        service.submit_local_once(attempt_id=ATTEMPT_ID)
    assert provider.submit_calls == 1


def test_local_known_pre_submit_failure_is_durable_without_prompt(
    tmp_path: Path,
) -> None:
    _, provider, resolved, execution_binding, committer = _runtime(
        tmp_path, submit_error=ErrorCode.VIDEO_PROVIDER_FAILED
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=ATTEMPT_ID,
        request=resolved,
        execution_binding=execution_binding,
    )

    with pytest.raises(AiVideoError) as exc_info:
        service.submit_local_once(attempt_id=ATTEMPT_ID)
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    attempt = committer._read_manifest().attempts[-1]
    assert attempt.status is StateCommitStatus.FAILED
    assert attempt.video_generation_state is not None
    assert attempt.video_generation_state.phase is VideoAttemptPhase.SUBMIT_INTENT
    assert service.resume_next_action(attempt_id=ATTEMPT_ID) == "stop"
    assert provider.submit_calls == 0

    with pytest.raises(AiVideoError):
        service.submit_local_once(attempt_id=ATTEMPT_ID)
    assert provider.submit_calls == 0


def test_local_terminal_job_failure_is_durable_and_never_repolled(
    tmp_path: Path,
) -> None:
    _, provider, resolved, execution_binding, committer = _runtime(
        tmp_path, status_state=VideoTaskState.FAILED
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=ATTEMPT_ID,
        request=resolved,
        execution_binding=execution_binding,
    )
    service.submit_local_once(attempt_id=ATTEMPT_ID)
    observation = service.refresh_local_once(attempt_id=ATTEMPT_ID)

    assert observation.state is VideoTaskState.FAILED
    manifest = committer._read_manifest()
    attempt = manifest.attempts[-1]
    assert attempt.status is StateCommitStatus.FAILED
    assert attempt.video_generation_state is not None
    assert attempt.video_generation_state.phase is VideoAttemptPhase.POLLING
    assert service.resume_next_action(attempt_id=ATTEMPT_ID) == "stop"
    assert provider.status_calls == 1

    with pytest.raises(AiVideoError):
        service.refresh_local_once(attempt_id=ATTEMPT_ID)
    assert provider.status_calls == 1


def test_local_poll_timeout_is_durable_outcome_unknown_and_never_repolled(
    tmp_path: Path,
) -> None:
    _, provider, resolved, execution_binding, committer = _runtime(
        tmp_path, status_error=ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=ATTEMPT_ID,
        request=resolved,
        execution_binding=execution_binding,
    )
    service.submit_local_once(attempt_id=ATTEMPT_ID)

    with pytest.raises(AiVideoError) as exc_info:
        service.refresh_local_once(attempt_id=ATTEMPT_ID)
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    attempt = committer._read_manifest().attempts[-1]
    assert attempt.status is StateCommitStatus.OUTCOME_UNKNOWN
    assert service.resume_next_action(attempt_id=ATTEMPT_ID) == "stop"
    assert provider.status_calls == 1

    with pytest.raises(AiVideoError):
        service.refresh_local_once(attempt_id=ATTEMPT_ID)
    assert provider.status_calls == 1
