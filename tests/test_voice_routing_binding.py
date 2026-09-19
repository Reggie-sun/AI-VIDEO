"""Durable task provenance for selected Voice Router effects."""

from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.models import VoiceRequestReceipt
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.voice_routing_contracts import VoiceMode
from test_production_minimax_speech import _DummySecret, _FakeTransport, _authorization, _policy, _pricing
from test_voice_routing_guards import _voice_request
from test_voice_routing_integration import _voice_requirement, _write_voice_project


def _prepared_separate_voice(root: Path):
    from test_voice_routing_guards import _context
    from test_voice_routing_integration import (
        _SCRIPT,
        _VOICE_ID,
        _orchestrator,
        _voice_setup,
        minimax_request,
    )

    source = _write_voice_project(
        root, _voice_requirement(mode=VoiceMode.SEPARATE_REQUIRED)
    )
    setup, _ = _voice_setup(source.shots[0], mode=VoiceMode.SEPARATE_REQUIRED)
    setup["context"] = setup["context"].model_copy(update={
        "selected_registry_revision_id": source.manifest.active_registry.revision_id,
    })
    setup["lifecycle"] = setup["lifecycle"].model_copy(update={
        "target_asset_role": source.shots[0].required_asset_roles[0].role,
        "base_project": source.manifest.active_project,
        "base_registry": source.manifest.active_registry,
        "base_dependency_graph": source.manifest.active_dependency_graph,
        "input_artifact_ids": (source.shots[0].artifact_id,),
    })
    request = minimax_request(
        provider_kind="minimax-speech",
        model_id="speech-2.8-hd",
        audio_kind="dialogue",
        script_text=_SCRIPT,
        speaker_id="hero",
        voice_id=_VOICE_ID,
        language="English",
        base_project=source.manifest.active_project,
        base_registry=source.manifest.active_registry,
        input_artifact_ids=(source.shots[0].artifact_id,),
    )
    from ai_video.production.minimax_speech import MiniMaxSpeechVoiceProvider

    provider = MiniMaxSpeechVoiceProvider(
        transport=_FakeTransport(),
        pricing=_pricing(),
        api_key=_DummySecret(),
        policy=_policy(),
    )
    base_context = _context(source, setup, request)
    context = base_context.model_copy(update={"audio_handoffs": tuple(
        item.model_copy(update={"voice_preview": provider.preview(request)})
        for item in base_context.audio_handoffs
    )})
    orchestrator, limits, _compiler, _projection = _orchestrator(
        setup=setup, source_project=source, voice_context=context
    )
    limits = limits.model_copy(update={"allowed_remote_candidates": tuple(
        item for item in limits.allowed_remote_candidates if item.endswith("/voice-separate")
    )})
    prepared = orchestrator.prepare(limits=limits)
    assert prepared.execution_binding is not None
    return source, request, provider, _authorization(provider, request), prepared


def _activate_changed_qa(root: Path) -> None:
    from ai_video.production.hashing import seal_artifact

    committer = ProductionStateCommitter(root)
    loaded = load_production_project(root / "project.yaml")
    assert loaded.qa_policy is not None
    policy = seal_artifact(loaded.qa_policy.model_copy(update={
        "artifact_id": "voice-routing-recheck-qa",
        "revision": loaded.qa_policy.revision + 1,
        "content_hash": "0" * 64,
        "creation_receipt_id": "voice-routing-recheck-qa",
    }))
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="voice-routing-qa-mutation",
    )


def _voice_envelope(prepared):
    from ai_video.production.voice_routing_execution import VoiceRoutingExecutionEnvelope
    from test_production_vidu import _setup as vidu_setup

    assert prepared.execution_binding is not None
    assert prepared.resolved_request is not None
    assert prepared.resolved_request.activation_scope is not None
    _provider, _transport, (_resolved, video_preview, video_paid_preview, _authorization, _permit) = vidu_setup(
        prepared.resolved_request.activation_scope.request
    )
    return VoiceRoutingExecutionEnvelope.create(
        binding=prepared.execution_binding,
        video_preview=video_preview,
        video_paid_preview=video_paid_preview,
    )


def _voice_envelope_with_video_authorization(prepared):
    from ai_video.production.voice_routing_execution import VoiceRoutingExecutionEnvelope
    from test_production_vidu import _setup as vidu_setup

    assert prepared.execution_binding is not None
    assert prepared.resolved_request is not None
    assert prepared.resolved_request.activation_scope is not None
    _provider, _transport, (_resolved, video_preview, video_paid_preview, authorization, _permit) = vidu_setup(
        prepared.resolved_request.activation_scope.request
    )
    return (
        VoiceRoutingExecutionEnvelope.create(
            binding=prepared.execution_binding,
            video_preview=video_preview,
            video_paid_preview=video_paid_preview,
        ),
        video_paid_preview,
        authorization,
    )


def test_voice_request_receipt_preserves_routed_task_binding() -> None:
    receipt = VoiceRequestReceipt(
        request_id="voice-request",
        attempt_id="voice-attempt",
        request_fingerprint="a" * 64,
        script_hash="b" * 64,
        provider_kind="minimax-speech",
        model_id="speech-2.8-hd",
        voice_id="English_expressive_narrator",
        language="English",
        pricing_snapshot_id="pricing",
        budget_reservation_receipt_id="budget",
        egress_authorization_receipt_id="egress",
        destination="https://api.example.test",
        routing_task_id="voice-router-task",
        routing_binding_hash="c" * 64,
    )

    assert receipt.routing_task_id == "voice-router-task"
    assert receipt.routing_binding_hash == "c" * 64


def test_legacy_voice_receipt_omits_route_fields_when_reopened() -> None:
    receipt = VoiceRequestReceipt(
        request_id="legacy-request",
        attempt_id="legacy-attempt",
        request_fingerprint="a" * 64,
        script_hash="b" * 64,
        provider_kind="minimax-speech",
        model_id="speech-2.8-hd",
        voice_id="English_expressive_narrator",
        language="English",
        pricing_snapshot_id="pricing",
        budget_reservation_receipt_id="budget",
        egress_authorization_receipt_id="egress",
        destination="https://api.example.test",
    )

    payload = receipt.model_dump(mode="json")
    assert "routing_task_id" not in payload
    assert "routing_binding_hash" not in payload
    assert VoiceRequestReceipt.model_validate(payload) == receipt


def test_direct_voice_admission_cannot_bypass_new_routed_binding(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    source = _write_voice_project(
        root, _voice_requirement(mode=VoiceMode.SEPARATE_REQUIRED)
    )
    request = _voice_request(source).model_copy(update={
        "input_artifact_ids": (source.shots[0].artifact_id,),
    })
    from ai_video.production.minimax_speech import MiniMaxSpeechVoiceProvider

    provider = MiniMaxSpeechVoiceProvider(
        transport=_FakeTransport(),
        pricing=_pricing(),
        api_key=_DummySecret(),
        policy=_policy(),
    )
    authorization = _authorization(provider, request)
    before = (root / "state/manifest.json").read_bytes()

    with pytest.raises(AiVideoError, match="durable route binding"):
        ProductionStateCommitter(root).begin_voice_generation(
            request,
            provider.preview(request),
            authorization,
            dependency_transition_preparer_available=True,
        )

    assert (root / "state/manifest.json").read_bytes() == before


def test_voice_begin_and_submit_intent_recheck_qa_inside_existing_locks(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    source, request, provider, authorization, prepared = _prepared_separate_voice(root)
    _activate_changed_qa(root)
    committer = ProductionStateCommitter(root)
    after_qa = (root / "state/manifest.json").read_bytes()

    with pytest.raises(AiVideoError, match="route binding is not current"):
        committer.begin_voice_generation(
            request,
            provider.preview(request),
            authorization,
            dependency_transition_preparer_available=True,
            routing_execution_envelope=_voice_envelope(prepared),
        )
    assert (root / "state/manifest.json").read_bytes() == after_qa

    # Recreate a fresh binding, commit R+1, then mutate QA before R+2.  The
    # submit-intent lock must reject it without reaching a Provider transport.
    root2 = tmp_path / "intent-project"
    root2.mkdir()
    source2, request2, provider2, authorization2, prepared2 = _prepared_separate_voice(root2)
    committer2 = ProductionStateCommitter(root2)
    committer2.begin_voice_generation(
        request2,
        provider2.preview(request2),
        authorization2,
        dependency_transition_preparer_available=True,
        routing_execution_envelope=_voice_envelope(prepared2),
    )
    _activate_changed_qa(root2)
    after_qa_r1 = (root2 / "state/manifest.json").read_bytes()
    with pytest.raises(AiVideoError, match="route binding is not current"):
        committer2.record_voice_submit_intent(
            request2, provider2.preview(request2), authorization2
        )
    assert (root2 / "state/manifest.json").read_bytes() == after_qa_r1


def test_direct_routed_voice_rechecks_joint_budget_inside_paid_lock(tmp_path: Path) -> None:
    from datetime import timedelta

    from ai_video.production.models import ActorIdentity
    from ai_video.production.paid_provider import PaidProviderAuthorizationDecision
    from test_production_vidu import NOW as VIDU_NOW
    from test_voice_routing_execution import _paid_preview

    root = tmp_path / "project"
    root.mkdir()
    _source, request, provider, authorization, prepared = _prepared_separate_voice(root)
    envelope, video_paid_preview, video_authorization = _voice_envelope_with_video_authorization(prepared)
    voice_paid_preview = _paid_preview(provider, request)
    voice_authorization = PaidProviderAuthorizationDecision.create(
        attempt_id=request.attempt_id,
        preview_fingerprint=voice_paid_preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="test-owner", actor_kind="human"),
        opt_in_policy_receipt_id="voice-opt-in",
        budget_policy_id="voice-budget",
        budget_currency="USD",
        project_budget_ceiling_microunits=100_000_000,
        per_call_ceiling_microunits=10_000_000,
        egress_authorized=True,
        egress_policy_receipt_id="voice-egress",
        live_test_authorized=True,
        live_authorization_receipt_id="voice-live",
        issued_at=VIDU_NOW,
        expires_at=VIDU_NOW + timedelta(minutes=10),
        max_submit_count=1,
        voice_batch_submit_limit=None,
    )
    committer = ProductionStateCommitter(
        root,
        paid_provider_authorizer=lambda exact: (
            voice_authorization if exact == voice_paid_preview
            else video_authorization if exact == video_paid_preview
            else None
        ),
        paid_provider_clock=lambda: VIDU_NOW,
    )

    with pytest.raises(AiVideoError, match="shared budget"):
        committer.generate_voice_asset(
            request,
            provider,
            authorization,
            paid_preview=voice_paid_preview,
            dependency_transition_preparer=lambda state: state,
            routing_execution_envelope=envelope,
        )

    assert provider._transport.invocations == 0


def test_direct_routed_voice_requires_paid_preview_before_manifest_or_transport(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    _source, request, provider, authorization, prepared = _prepared_separate_voice(root)
    before = (root / "state/manifest.json").read_bytes()

    with pytest.raises(AiVideoError, match="Paid Provider preview"):
        ProductionStateCommitter(root).generate_voice_asset(
            request,
            provider,
            authorization,
            dependency_transition_preparer=lambda state: state,
            routing_execution_envelope=_voice_envelope(prepared),
        )

    assert (root / "state/manifest.json").read_bytes() == before
    assert provider._transport.invocations == 0


def test_direct_routed_voice_rejects_changed_paid_credential_before_transport(tmp_path: Path) -> None:
    from datetime import timedelta

    from ai_video.production.models import ActorIdentity
    from ai_video.production.paid_provider import (
        PaidProviderAuthorizationDecision,
        PaidProviderCallPreview,
        SecretReference,
    )
    from test_production_vidu import NOW as VIDU_NOW
    from test_voice_routing_execution import _paid_preview

    root = tmp_path / "project"
    root.mkdir()
    _source, request, provider, authorization, prepared = _prepared_separate_voice(root)
    envelope, video_paid_preview, video_authorization = _voice_envelope_with_video_authorization(prepared)
    voice_paid_preview = _paid_preview(provider, request)
    changed_voice_preview = PaidProviderCallPreview.create(**{
        **voice_paid_preview.model_dump(mode="python", exclude={"preview_fingerprint"}),
        "secret_reference": SecretReference(
            kind=voice_paid_preview.secret_reference.kind,
            reference_id="unsealed-credential-reference",
        ),
    })
    changed_voice_authorization = PaidProviderAuthorizationDecision.create(
        attempt_id=request.attempt_id,
        preview_fingerprint=changed_voice_preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="test-owner", actor_kind="human"),
        opt_in_policy_receipt_id="voice-opt-in",
        budget_policy_id="voice-budget",
        budget_currency="USD",
        project_budget_ceiling_microunits=100_000_000,
        per_call_ceiling_microunits=10_000_000,
        egress_authorized=True,
        egress_policy_receipt_id="voice-egress",
        live_test_authorized=True,
        live_authorization_receipt_id="voice-live",
        issued_at=VIDU_NOW,
        expires_at=VIDU_NOW + timedelta(minutes=10),
        max_submit_count=1,
        voice_batch_submit_limit=None,
    )
    committer = ProductionStateCommitter(
        root,
        paid_provider_authorizer=lambda exact: (
            changed_voice_authorization if exact == changed_voice_preview
            else video_authorization if exact == video_paid_preview
            else None
        ),
        paid_provider_clock=lambda: VIDU_NOW,
    )

    with pytest.raises(AiVideoError, match="sealed handoff"):
        committer.generate_voice_asset(
            request,
            provider,
            authorization,
            paid_preview=changed_voice_preview,
            dependency_transition_preparer=lambda state: state,
            routing_execution_envelope=envelope,
        )

    assert provider._transport.invocations == 0


def test_routed_paid_intent_cannot_fall_back_when_binding_artifact_is_missing(tmp_path: Path) -> None:
    from datetime import timedelta

    from ai_video.production.models import ActorIdentity
    from ai_video.production.paid_provider import PaidProviderAuthorizationDecision
    from test_production_vidu import NOW as VIDU_NOW
    from test_voice_routing_execution import _paid_preview

    root = tmp_path / "project"
    root.mkdir()
    _source, request, provider, authorization, prepared = _prepared_separate_voice(root)
    voice_paid_preview = _paid_preview(provider, request)
    paid_authorization = PaidProviderAuthorizationDecision.create(
        attempt_id=request.attempt_id,
        preview_fingerprint=voice_paid_preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="test-owner", actor_kind="human"),
        opt_in_policy_receipt_id="voice-opt-in",
        budget_policy_id="voice-budget",
        budget_currency="USD",
        project_budget_ceiling_microunits=100_000_000,
        per_call_ceiling_microunits=10_000_000,
        egress_authorized=True,
        egress_policy_receipt_id="voice-egress",
        live_test_authorized=True,
        live_authorization_receipt_id="voice-live",
        issued_at=VIDU_NOW,
        expires_at=VIDU_NOW + timedelta(minutes=10),
        max_submit_count=1,
        voice_batch_submit_limit=None,
    )
    committer = ProductionStateCommitter(
        root,
        paid_provider_authorizer=lambda exact: (
            paid_authorization if exact == voice_paid_preview else None
        ),
        paid_provider_clock=lambda: VIDU_NOW,
    )
    committer.begin_voice_generation(
        request,
        provider.preview(request),
        authorization,
        dependency_transition_preparer_available=True,
        routing_execution_envelope=_voice_envelope(prepared),
    )
    committer.record_voice_submit_intent(
        request, provider.preview(request), authorization
    )
    binding_path = (
        root / "state/voice/attempts" / request.attempt_id / "routing-binding.json"
    )
    binding_path.unlink()
    before = (root / "state/manifest.json").read_bytes()

    with pytest.raises(AiVideoError, match="Routed voice evidence"):
        committer.record_paid_provider_submit_intent(
            voice_paid_preview, reservation_id="routed-binding-missing"
        )

    assert (root / "state/manifest.json").read_bytes() == before
    assert provider._transport.invocations == 0


def test_voice_submit_count_uses_durable_current_task_provenance(tmp_path: Path) -> None:
    from ai_video.production._voice_project_reader import read_canonical_voice_model
    from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
    from ai_video.production.shot_router import VideoGenerationResolver
    from ai_video.production.voice_routing import validate_voice_execution
    from ai_video.production.voice_routing_execution import VoiceRoutingExecutionEnvelope
    from test_voice_routing_p4 import _activate_separate_voice, _current_setup
    from test_voice_routing_guards import _context
    from test_voice_routing_integration import _orchestrator

    root = tmp_path / "project"
    root.mkdir()
    source, request, _transport = _activate_separate_voice(root)
    task_id = next(
        item.voice_request.routing_task_id
        for item in source.manifest.attempts
        if item.voice_request is not None and item.voice_request.routing_task_id is not None
    )
    setup = _current_setup(source)
    context = _context(source, setup, request)
    orchestrator, limits, _provider, _projection = _orchestrator(
        setup=setup, source_project=source, voice_context=context
    )
    limits = limits.model_copy(update={"allowed_remote_candidates": tuple(
        item for item in limits.allowed_remote_candidates if item.endswith("/voice-separate")
    )})

    different_task = orchestrator.prepare(limits=limits.model_copy(update={
        "task_id": "a-different-production-task",
        "paid_submit_ceiling": 1,
    }))
    same_task = orchestrator.prepare(limits=limits.model_copy(update={
        "task_id": task_id,
        "paid_submit_ceiling": 1,
    }))
    different_route = next(
        item.voice_route for item in different_task.inputs.candidates
        if item.voice_route is not None and item.voice_route.route.value == "separate"
    )
    same_route = next(
        item.voice_route for item in same_task.inputs.candidates
        if item.voice_route is not None and item.voice_route.route.value == "separate"
    )

    assert different_route.readiness.voice_submits_used == 0
    assert same_route.readiness.voice_submits_used == 1
    assert different_task.decision.disposition == "GENERATE_ONCE"
    assert same_task.decision.disposition == "BLOCKED_EXECUTION"

    prior_envelope, _ = read_canonical_voice_model(
        source.root,
        request.attempt_id,
        "routing-binding.json",
        VoiceRoutingExecutionEnvelope,
    )
    prior = prior_envelope.binding
    allowed = orchestrator.prepare(limits=limits.model_copy(update={
        "task_id": task_id,
        "paid_submit_ceiling": prior.inputs.limits.paid_submit_ceiling,
    }))
    assert allowed.execution_binding is not None
    forged_inputs = allowed.execution_binding.inputs.model_copy(update={
        "limits": allowed.execution_binding.inputs.limits.model_copy(update={
            "paid_submits_used": 0,
        }),
    })
    forged_decision = VideoGenerationResolver().resolve_requirement(
        projection=allowed.execution_binding.projection,
        context=allowed.execution_binding.context,
        policy=allowed.execution_binding.policy,
        lifecycle=allowed.execution_binding.lifecycle,
        inputs=forged_inputs,
        continuity_routing=allowed.execution_binding.continuity_routing,
    )
    forged = GenerationDecisionExecutionBinding.create(
        projection=allowed.execution_binding.projection,
        context=allowed.execution_binding.context,
        policy=allowed.execution_binding.policy,
        lifecycle=allowed.execution_binding.lifecycle,
        inputs=forged_inputs,
        decision=forged_decision,
        compiled_request=allowed.execution_binding.compiled_request,
        continuity_routing=allowed.execution_binding.continuity_routing,
    )

    with pytest.raises(ValueError, match="submit usage"):
        validate_voice_execution(forged, source)
