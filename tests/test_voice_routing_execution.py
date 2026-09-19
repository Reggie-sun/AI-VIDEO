"""Exact offline voice handoff activation and Router reprepare coverage."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderEgressItem,
    SecretReference,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.voice_candidate import make_voice_candidate_preparer
from ai_video.production.voice_routing_handoff import generate_selected_voice
from test_production_minimax_speech import (
    _DummySecret,
    _FakeTransport,
    _authorization,
    _policy,
    _pricing,
    _response,
)
from test_production_vidu import NOW as VIDU_NOW, _setup as vidu_setup
from test_production_voice_candidate import _toolchain
from test_voice_routing_guards import _context, _voice_request
from test_voice_routing_integration import (
    _SCRIPT,
    _orchestrator,
    _voice_requirement,
    _voice_dependency_transition,
    _voice_setup,
    _write_voice_project,
)
from ai_video.production.models import ActorIdentity
from ai_video.production.voice_routing_contracts import VoiceMode


def _paid_preview(provider, request) -> PaidProviderCallPreview:
    preview = provider.preview(request)
    return PaidProviderCallPreview.create(
        attempt_id=request.attempt_id,
        operation="voice_generation",
        provider_kind=request.provider_kind,
        model_id=request.model_id,
        request_fingerprint=request.voice_request_fingerprint,
        billing_mode="remote_metered",
        currency=preview.currency,
        estimated_cost_upper_bound_microunits=preview.estimated_cost_upper_bound_microunits,
        destination=preview.destination,
        method="POST",
        egress_items=(PaidProviderEgressItem(
            item_id="script",
            sha256=request.script_hash,
            size_bytes=len(request.script_text.encode("utf-8")),
            mime_type="text/plain",
            purpose="script",
        ),),
        retention_mode=provider._policy.retention_mode,
        provider_policy_snapshot_id=provider._policy.policy_receipt_id,
        secret_reference=SecretReference(
            kind=provider._policy.credential_reference_kind,
            reference_id=provider._policy.credential_reference_id,
        ),
    )


def test_separate_voice_activation_reprepares_from_registered_exact_asset(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
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
    request = _voice_request(source)
    transport = _FakeTransport(_response(
        mutate=lambda payload: payload["extra_info"].update(
            usage_characters=len(_SCRIPT)
        )
    ))
    from ai_video.production.minimax_speech import MiniMaxSpeechVoiceProvider

    provider = MiniMaxSpeechVoiceProvider(
        transport=transport,
        pricing=_pricing().model_copy(update={"currency": "CNY"}),
        api_key=_DummySecret(),
        policy=_policy(),
    )
    initial_context = _context(source, setup, request)
    context = initial_context.model_copy(update={"audio_handoffs": tuple(
        item.model_copy(update={"voice_preview": provider.preview(request)})
        for item in initial_context.audio_handoffs
    )})
    orchestrator, limits, video_provider, _projection = _orchestrator(
        setup=setup,
        source_project=source,
        voice_context=context,
    )
    limits = limits.model_copy(update={
        "allowed_remote_candidates": tuple(
            item for item in limits.allowed_remote_candidates
            if item.endswith("/voice-separate")
        ),
    })
    prepared = orchestrator.prepare(limits=limits)
    authorization = _authorization(provider, request)
    paid_preview = _paid_preview(provider, request)
    video_provider._now = lambda: VIDU_NOW
    assert prepared.resolved_request is not None
    assert prepared.resolved_request.activation_scope is not None
    _prospective_provider, _prospective_transport, (
        prospective_resolved, _preview, video_paid_preview, video_authorization, _permit,
    ) = vidu_setup(prepared.resolved_request.activation_scope.request)
    assert prospective_resolved == prepared.resolved_request
    now = VIDU_NOW
    paid_authorization = PaidProviderAuthorizationDecision.create(
        attempt_id=request.attempt_id,
        preview_fingerprint=paid_preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="test-owner", actor_kind="human"),
        opt_in_policy_receipt_id="test-speech-opt-in",
        budget_policy_id="budget",
        budget_currency="CNY",
        project_budget_ceiling_microunits=100_000_000,
        per_call_ceiling_microunits=10_000_000,
        egress_authorized=True,
        egress_policy_receipt_id="test-speech-egress",
        live_test_authorized=True,
        live_authorization_receipt_id="test-speech-live",
        issued_at=now,
        expires_at=now + timedelta(minutes=10),
        max_submit_count=1,
        voice_batch_submit_limit=None,
    )
    committer = ProductionStateCommitter(
        root,
        voice_candidate_preparer=make_voice_candidate_preparer(root, _toolchain()),
        paid_provider_authorizer=lambda exact: (
            paid_authorization if exact == paid_preview
            else video_authorization if exact == video_paid_preview
            else None
        ),
        paid_provider_clock=lambda: now,
    )

    manifest = generate_selected_voice(
        orchestrator,
        committer=committer,
        prepared=prepared,
        speaker_id="hero",
        provider=provider,
        authorization=authorization,
        paid_preview=paid_preview,
        video_paid_preview=video_paid_preview,
        dependency_transition_preparer=lambda candidate: _voice_dependency_transition(
            root, candidate
        ),
    )

    assert transport.invocations == 1
    assert manifest.attempts[-1].status.value == "succeeded"
    activated = load_production_project(root / "project.yaml")
    assert any(asset.asset_id == f"voice-{request.attempt_id}" for asset in activated.registry.assets)

    replay_context = _context(activated, setup, request)
    reprepare, replay_limits, _replay_video_provider, _replay_projection = _orchestrator(
        setup=setup,
        source_project=activated,
        voice_context=replay_context,
    )
    replay_limits = replay_limits.model_copy(update={
        "allowed_remote_candidates": tuple(
            item for item in replay_limits.allowed_remote_candidates
            if item.endswith("/voice-separate")
        ),
    })
    replayed = reprepare.prepare(limits=replay_limits)
    selected = next(
        item for item in replayed.inputs.candidates
        if item.candidate_id == replayed.decision.selected_candidate_id
    )
    assert replayed.decision.disposition == "GENERATE_ONCE"
    assert selected.voice_route.readiness.pending_voice_requests == ()
    with pytest.raises(ValueError):
        generate_selected_voice(
            reprepare,
            committer=committer,
            prepared=replayed,
            speaker_id="hero",
            provider=provider,
            authorization=authorization,
            paid_preview=paid_preview,
            video_paid_preview=video_paid_preview,
            dependency_transition_preparer=lambda candidate: _voice_dependency_transition(
                root, candidate
            ),
        )
    assert transport.invocations == 1
