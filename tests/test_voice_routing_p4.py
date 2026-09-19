"""P4 resolves routed separate speech from one exact activated video decision."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.composition import resolve_composition
from ai_video.production.composition_contracts import (
    AudioTrackSpec,
    VoiceCompositionSource,
)
from ai_video.production.models import ActorIdentity
from ai_video.production.paid_provider import PaidProviderAuthorizationDecision
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video_generation import VideoGenerationService
from ai_video.production.voice_candidate import make_voice_candidate_preparer
from ai_video.production.voice_routing_contracts import VoiceMode
import production_project_factory as project_factory
from test_production_minimax_speech import (
    _DummySecret, _FakeTransport, _authorization, _policy, _pricing, _response,
)
from test_production_vidu import NOW as VIDU_NOW, _setup as vidu_setup
from test_production_voice_candidate import _toolchain
from test_voice_routing_execution import _paid_preview
from test_voice_routing_guards import _context, _voice_request
from test_voice_routing_integration import (
    _EXECUTION_INPUTS_BY_ROOT,
    _SCRIPT,
    _orchestrator,
    _voice_dependency_transition,
    _voice_requirement,
    _voice_setup,
    _write_voice_project,
)


def _fixture_video(path: Path) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg is required for the local Vidu response fixture")
    subprocess.run(
        [
            ffmpeg, "-nostdin", "-v", "error", "-f", "lavfi", "-i",
            "color=size=1280x720:rate=24:color=black", "-t", "5", "-c:v",
            "libx264", "-pix_fmt", "yuv420p", "-an", str(path),
        ],
        check=True,
    )
    return path.read_bytes()


def _current_setup(source):
    setup, _ = _voice_setup(source.shots[0], mode=VoiceMode.SEPARATE_REQUIRED)
    return setup | {
        "context": setup["context"].model_copy(update={
            "selected_registry_revision_id": source.manifest.active_registry.revision_id,
        }),
        "lifecycle": setup["lifecycle"].model_copy(update={
            "target_asset_role": source.shots[0].required_asset_roles[0].role,
            "base_project": source.manifest.active_project,
            "base_registry": source.manifest.active_registry,
            "base_dependency_graph": source.manifest.active_dependency_graph,
            "input_artifact_ids": (source.shots[0].artifact_id,),
        }),
    }


def _activate_separate_voice(
    root: Path, *, shared_budget: bool = True, holder: dict | None = None
):
    source = _write_voice_project(
        root, _voice_requirement(mode=VoiceMode.SEPARATE_REQUIRED)
    )
    setup = _current_setup(source)
    request = _voice_request(source)
    voice_transport = _FakeTransport(_response(mutate=lambda payload: payload["extra_info"].update(
        usage_characters=len(_SCRIPT)
    )))
    if holder is not None:
        holder["voice_transport"] = voice_transport
    from ai_video.production.minimax_speech import MiniMaxSpeechVoiceProvider

    voice_provider = MiniMaxSpeechVoiceProvider(
        transport=voice_transport,
        pricing=_pricing().model_copy(update={"currency": "CNY"}),
        api_key=_DummySecret(),
        policy=_policy(),
    )
    context = _context(source, setup, request).model_copy(update={
        "audio_handoffs": tuple(item.model_copy(update={
            "voice_preview": voice_provider.preview(request),
        }) for item in _context(source, setup, request).audio_handoffs),
    })
    orchestrator, limits, compiler_provider, _projection = _orchestrator(
        setup=setup, source_project=source, voice_context=context
    )
    limits = limits.model_copy(update={"allowed_remote_candidates": tuple(
        item for item in limits.allowed_remote_candidates if item.endswith("/voice-separate")
    )})
    prepared = orchestrator.prepare(limits=limits)
    compiler_provider._now = lambda: VIDU_NOW
    assert prepared.resolved_request is not None
    assert prepared.resolved_request.activation_scope is not None
    _video_provider, _video_transport, (
        prospective_resolved, _video_preview, video_paid_preview, video_authorization, _permit,
    ) = vidu_setup(prepared.resolved_request.activation_scope.request)
    assert prospective_resolved == prepared.resolved_request
    voice_preview = _paid_preview(voice_provider, request)
    voice_authorization = _authorization(voice_provider, request)
    now = VIDU_NOW
    paid_authorization = PaidProviderAuthorizationDecision.create(
        attempt_id=request.attempt_id,
        preview_fingerprint=voice_preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="test-owner", actor_kind="human"),
        opt_in_policy_receipt_id="test-speech-opt-in",
        budget_policy_id="budget" if shared_budget else "mismatched-budget",
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
            paid_authorization if exact == voice_preview
            else video_authorization if exact == video_paid_preview
            else None
        ),
        paid_provider_clock=lambda: now,
    )
    orchestrator.generate_selected_voice(
        committer=committer,
        prepared=prepared,
        speaker_id="hero",
        provider=voice_provider,
        authorization=voice_authorization,
        paid_preview=voice_preview,
        video_paid_preview=video_paid_preview,
        dependency_transition_preparer=lambda candidate: _voice_dependency_transition(root, candidate),
    )
    return load_production_project(root / "project.yaml"), request, voice_transport


def test_separate_voice_rejects_mismatched_joint_monetary_budget_before_tts(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    holder = {}

    with pytest.raises(AiVideoError):
        _activate_separate_voice(root, shared_budget=False, holder=holder)

    assert holder["voice_transport"].invocations == 0


def _activated_separate_video(root: Path, fixture: Path):
    source, voice_request, voice_transport = _activate_separate_voice(root)
    setup = _current_setup(source)
    context = _context(source, setup, voice_request)
    orchestrator, limits, _compiler_provider, _projection = _orchestrator(
        setup=setup, source_project=source, voice_context=context
    )
    limits = limits.model_copy(update={"allowed_remote_candidates": tuple(
        item for item in limits.allowed_remote_candidates if item.endswith("/voice-separate")
    )})
    prepared = orchestrator.prepare(limits=limits)
    assert prepared.resolved_request is not None
    assert prepared.execution_binding is not None
    assert prepared.resolved_request.activation_scope is not None
    provider, transport, (resolved, preview, paid_preview, authorization, _permit) = vidu_setup(
        prepared.resolved_request.activation_scope.request
    )
    assert resolved == prepared.resolved_request
    transport.body = _fixture_video(fixture)
    inputs = replace(
        _EXECUTION_INPUTS_BY_ROOT[source.root],
        project=source,
        voice_requests=(voice_request,),
    )
    committer = ProductionStateCommitter(
        root,
        video_candidate_preparer=project_factory.make_p8_video_candidate_preparer(inputs),
        paid_provider_authorizer=lambda exact: authorization if exact == paid_preview else None,
        paid_provider_clock=lambda: authorization.issued_at,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=paid_preview.attempt_id,
        request=resolved,
        execution_binding=prepared.execution_binding,
    )
    service.submit_once(
        attempt_id=paid_preview.attempt_id,
        paid_preview=paid_preview,
        reservation_id="voice-routing-video-reservation",
    )
    service.refresh_once(attempt_id=paid_preview.attempt_id)
    committer.settle_paid_provider_reservation(
        attempt_id=paid_preview.attempt_id,
        actual_cost_microunits=1_000_000,
    )
    service.fetch_and_activate(attempt_id=paid_preview.attempt_id)
    return load_production_project(root / "project.yaml"), voice_request, voice_transport, resolved


def _p4_spec(source, voice_request, video_request, root: Path):
    base = _EXECUTION_INPUTS_BY_ROOT[source.root].composition_spec
    voice_asset_id = f"voice-{voice_request.attempt_id}"
    spec = base.model_copy(update={
        "revision": base.revision + 1,
        "content_hash": "0" * 64,
        "shot_ids": ("shot-1",),
        "layers": tuple(
            layer.model_copy(update={"asset_id": video_request.output_asset_id})
            for layer in base.layers if layer.shot_id == "shot-1"
        ),
        "audio_tracks": tuple(
            AudioTrackSpec(
                track_id="planned-dialogue", audio_kind="dialogue",
                asset_id=voice_asset_id, shot_id="shot-1",
            ) for track in base.audio_tracks
            if track.shot_id == "shot-1" and track.audio_kind.value == "dialogue"
        ),
        "caption_tracks": (),
        "transitions": (),
        "sample_rate": 44_100,
        "voice_sources": (VoiceCompositionSource(
            shot_id="shot-1", source_project_file=(root / "project.yaml").resolve(),
            execution_binding=source.manifest.attempts[-1].video_generation_state.execution_binding,
        ),),
    })

    return spec


def test_separate_voice_then_vidu_activation_resolves_exact_p4_handoff(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    source, voice_request, voice_transport, video_request = _activated_separate_video(
        root, tmp_path / "vidu-response.mp4"
    )
    timeline = resolve_composition(
        source, _p4_spec(source, voice_request, video_request, root),
        renderer_version="test-hyperframes",
    )

    assert voice_transport.invocations == 1
    video_asset = next(item for item in source.registry.assets if item.asset_id == video_request.output_asset_id)
    assert any(span.asset_sha256 == video_asset.sha256
               for span in timeline.visual_spans)
    assert next(span for span in timeline.audio_spans if span.track_id == "planned-dialogue").asset_id == f"voice-{voice_request.attempt_id}"


@pytest.mark.parametrize("mutation", ("trim", "wrong_asset", "wrong_track", "no_source"))
def test_p4_rejects_tampered_separate_voice_handoff(tmp_path: Path, mutation: str) -> None:
    root = tmp_path / "project"
    root.mkdir()
    source, voice_request, _voice_transport, video_request = _activated_separate_video(
        root, tmp_path / "vidu-response.mp4"
    )
    spec = _p4_spec(source, voice_request, video_request, root)
    track = spec.audio_tracks[0]
    if mutation == "trim":
        spec = spec.model_copy(update={"audio_tracks": (
            track.model_copy(update={"trim_start_sample": 1}),
        )})
    elif mutation == "wrong_asset":
        spec = spec.model_copy(update={"audio_tracks": (
            track.model_copy(update={"asset_id": "voice-dialogue"}),
        )})
    elif mutation == "wrong_track":
        spec = spec.model_copy(update={"audio_tracks": (
            track.model_copy(update={"track_id": "unselected-dialogue"}),
        )})
    else:
        spec = spec.model_copy(update={"voice_sources": ()})

    with pytest.raises(AiVideoError):
        resolve_composition(source, spec, renderer_version="test-hyperframes")
