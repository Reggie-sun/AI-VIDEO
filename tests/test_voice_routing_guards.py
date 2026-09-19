"""Voice Router rejects stale authoring and unsafe exact handoffs before effects."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_video.production.composition_contracts import AudioTrackSpec
from ai_video.production.hashing import seal_artifact
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.voice_routing import (
    VoiceAudioHandoff,
    VoiceRoutingContext,
    route_blockers,
)
from ai_video.production.voice_routing_handoff import generate_selected_voice
from ai_video.production.voice_routing_contracts import VoiceMode, VoiceRoute
from test_generation_provider_wiring import forbidden
from test_voice_routing_integration import (
    _SCRIPT,
    _VOICE_ID,
    _minimax_preview,
    _orchestrator,
    _voice_requirement,
    _voice_setup,
    _write_voice_project,
    minimax_request,
)


def _voice_request(source):
    return minimax_request(
        provider_kind="minimax-speech",
        model_id="speech-2.8-hd",
        audio_kind="dialogue",
        script_text=_SCRIPT,
        speaker_id="hero",
        voice_id=_VOICE_ID,
        language="English",
        base_project=source.manifest.active_project,
        base_registry=source.manifest.active_registry,
    )


def _context(source, setup, request=None, *, asset_id=None):
    track = AudioTrackSpec(
        track_id="planned-dialogue",
        audio_kind="dialogue",
        asset_id=asset_id or (f"voice-{request.attempt_id}" if request else "native-dialogue"),
        shot_id=setup["context"].target_shot_id,
    )
    handoff = VoiceAudioHandoff(track=track, speaker_id="hero")
    if request is not None:
        handoff = handoff.model_copy(update={
            "voice_request": request,
            "voice_preview": _minimax_preview(request),
            "credential_reference_id": "MINIMAX_SPEECH_API_KEY",
        })
    return VoiceRoutingContext(
        final_project_file=(source.root / "project.yaml").resolve(),
        audio_handoffs=(handoff,),
    )


def test_current_source_and_final_shot_authoring_are_required(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    source = _write_voice_project(root, _voice_requirement())
    stale = seal_artifact(source.shots[0].model_copy(update={
        "revision": source.shots[0].revision + 1,
        "intent": "A different current Shot.",
    }))
    stale_setup, _ = _voice_setup(stale)
    context = _context(source, stale_setup)
    orchestrator, limits, _provider, _projection = _orchestrator(
        setup=stale_setup,
        source_project=source,
        voice_context=context,
    )

    prepared = orchestrator.prepare(limits=limits)

    native = next(c for c in prepared.inputs.candidates if c.voice_route.route is VoiceRoute.NATIVE)
    assert "SOURCE_SHOT_NOT_CURRENT" in native.voice_route.readiness.native_blockers

    final_root = tmp_path / "final"
    final_root.mkdir()
    final = _write_voice_project(
        final_root,
        _voice_requirement(mode=VoiceMode.NATIVE_REQUIRED),
        execution_source=False,
    )
    setup, _ = _voice_setup(source.shots[0])
    final_context = VoiceRoutingContext(
        final_project_file=(final.root / "project.yaml").resolve(),
        audio_handoffs=_context(source, setup).audio_handoffs,
    )
    orchestrator, limits, _provider, _projection = _orchestrator(
        setup=setup,
        source_project=source,
        voice_context=final_context,
    )
    prepared = orchestrator.prepare(limits=limits)
    native = next(c for c in prepared.inputs.candidates if c.voice_route.route is VoiceRoute.NATIVE)
    assert "FINAL_SHOT_NOT_CURRENT" in native.voice_route.readiness.native_blockers


def test_fixed_voice_without_review_is_evidence_required(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    source = _write_voice_project(
        root, _voice_requirement(consistency="cross_shot_fixed")
    )
    setup, _ = _voice_setup(source.shots[0])
    orchestrator, limits, _provider, _projection = _orchestrator(
        setup=setup,
        source_project=source,
        voice_context=_context(source, setup),
    )

    prepared = orchestrator.prepare(limits=limits)

    native = next(c for c in prepared.inputs.candidates if c.voice_route.route is VoiceRoute.NATIVE)
    assert "EVIDENCE_REQUIRED" in native.voice_route.readiness.native_blockers


def test_tampered_native_output_and_wrong_voice_asset_are_blocked(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    source = _write_voice_project(root, _voice_requirement())
    setup, _ = _voice_setup(source.shots[0])
    native_context = _context(source, setup)
    orchestrator, limits, _provider, projection = _orchestrator(
        setup=setup,
        source_project=source,
        voice_context=native_context,
    )
    prepared = orchestrator.prepare(limits=limits)
    native = next(c for c in prepared.inputs.candidates if c.voice_route.route is VoiceRoute.NATIVE)
    tampered = native.model_copy(update={
        "output_requirement": native.output_requirement.model_copy(update={"native_audio": False}),
    })
    assert route_blockers(projection.requirement, tampered) == ("VOICE_ROUTE_OUTPUT_CONFLICT",)

    separate_voice = _voice_requirement(mode=VoiceMode.SEPARATE_REQUIRED)
    separate_root = tmp_path / "separate"
    separate_root.mkdir()
    separate = _write_voice_project(separate_root, separate_voice)
    separate_setup, _ = _voice_setup(
        separate.shots[0], mode=VoiceMode.SEPARATE_REQUIRED
    )
    request = _voice_request(separate)
    wrong_context = _context(
        separate,
        separate_setup,
        request,
        asset_id="wrong-generated-voice-id",
    )
    orchestrator, limits, _provider, _projection = _orchestrator(
        setup=separate_setup,
        source_project=separate,
        voice_context=wrong_context,
    )
    limits = limits.model_copy(update={
        "allowed_remote_candidates": tuple(
            item for item in limits.allowed_remote_candidates
            if item.endswith("/voice-separate")
        ),
    })

    prepared = orchestrator.prepare(limits=limits)

    candidate = prepared.inputs.candidates[0]
    assert "VOICE_REQUEST_OR_CAPABILITY_CONFLICT" in candidate.voice_route.readiness.separate_blockers
    assert prepared.decision.disposition == "BLOCKED_CAPABILITY"


def test_readiness_is_exact_binding_state_but_not_media_fit_scope(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    source = _write_voice_project(root, _voice_requirement())
    setup, _ = _voice_setup(source.shots[0])
    orchestrator, limits, _provider, _projection = _orchestrator(
        setup=setup,
        source_project=source,
        voice_context=_context(source, setup),
    )
    prepared = orchestrator.prepare(limits=limits)
    native = next(c for c in prepared.inputs.candidates if c.voice_route.route is VoiceRoute.NATIVE)
    changed_route = native.voice_route.model_copy(update={
        "readiness": native.voice_route.readiness.model_copy(update={
            "voice_submits_used": native.voice_route.readiness.voice_submits_used + 1,
        }),
    })
    changed = native.model_copy(update={"voice_route": changed_route})

    assert changed_route.content_hash != native.voice_route.content_hash
    assert changed.scope_hash == native.scope_hash


def test_missing_voice_materializer_stops_before_repreparing_or_calling_provider(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    source = _write_voice_project(
        root, _voice_requirement(mode=VoiceMode.SEPARATE_REQUIRED)
    )
    setup, _ = _voice_setup(source.shots[0], mode=VoiceMode.SEPARATE_REQUIRED)
    request = _voice_request(source)
    context = _context(source, setup, request)
    orchestrator, limits, _provider, _projection = _orchestrator(
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
    manifest_before = (root / "state" / "manifest.json").read_bytes()

    with pytest.raises(ValueError, match="candidate materializer"):
        generate_selected_voice(
            orchestrator,
            committer=ProductionStateCommitter(root),
            prepared=prepared,
            speaker_id="hero",
            provider=forbidden,
            authorization=forbidden,
            paid_preview=forbidden,
        )

    assert (root / "state" / "manifest.json").read_bytes() == manifest_before
