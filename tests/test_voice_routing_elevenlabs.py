"""ElevenLabs participates in the canonical separate-voice Router handoff."""

import pytest

from ai_video.production.hashing import canonical_sha256
from ai_video.production.composition_contracts import AudioTrackSpec
from ai_video.production.elevenlabs import ElevenLabsVoiceProvider
from ai_video.production.voice_routing import (
    VoiceAudioHandoff, VoiceRoutingContext, voice_provider_language,
)
from ai_video.production.voice_routing_contracts import VoiceMode
from test_generation_provider_wiring import forbidden
from test_production_elevenlabs import _policy, _pricing, _request
from test_voice_routing_integration import (
    _SCRIPT, _VOICE_ID, _orchestrator, _voice_requirement, _voice_setup,
    _write_voice_project,
)


@pytest.mark.parametrize("language,provider,expected", [
    ("en", "minimax-speech", "English"), ("zh", "minimax-speech", "Chinese"),
    ("en", "elevenlabs", "en"), ("zh", "elevenlabs", "zh"),
    ("Chinese", "elevenlabs", None), ("en", "unknown", None),
])
def test_language_projection_is_provider_bound(language, provider, expected):
    assert voice_provider_language(language, provider) == expected
    assert voice_provider_language("zh") == "Chinese"


@pytest.mark.parametrize("mutation,language", [(None, "en"), (None, "zh"),
    ("origin", "en"), ("model", "en"), ("language", "en"), ("provider", "en"), ("rate", "en")])
def test_elevenlabs_exact_separate_handoff_is_selected_or_rejected(tmp_path, monkeypatch, mutation, language):
    import test_voice_routing_integration as fixture

    # The existing fixture authors English dialogue; seal the requested language
    # through the same real planner entry for the Chinese arm.
    original_dialogue = fixture.DialogueIntent
    monkeypatch.setattr(fixture, "DialogueIntent",
        lambda **values: original_dialogue(**{**values, "language": language}))
    root = tmp_path / "project"
    root.mkdir()
    voice = _voice_requirement(mode=VoiceMode.SEPARATE_REQUIRED)
    voice = voice.model_copy(update={"speakers": tuple(
        speaker.model_copy(update={"language": language}) for speaker in voice.speakers)})
    source = _write_voice_project(root, voice)
    setup, _ = _voice_setup(source.shots[0], mode=VoiceMode.SEPARATE_REQUIRED)
    changes = {"model": {"model_id": "unqualified-model"},
               "language": {"language": "English"},
               "provider": {"provider_kind": "unknown"},
               "rate": {"output_sample_rate_hz": 44100}}.get(mutation, {})
    values = dict(script_text=_SCRIPT, speaker_id="hero", voice_id=_VOICE_ID,
        language=language, base_project=source.manifest.active_project,
        base_registry=source.manifest.active_registry)
    values.update(changes)
    request = _request(**values)
    provider = ElevenLabsVoiceProvider(transport=forbidden, pricing=_pricing(),
                                     api_key=forbidden, policy=_policy())
    preview = provider.preview(request)
    if mutation == "origin":
        values = preview.model_dump(mode="json", exclude={"preview_fingerprint"})
        values["destination"] = "https://api.minimaxi.com"
        preview = type(preview).model_validate({**values, "preview_fingerprint": canonical_sha256(values)})
    context = VoiceRoutingContext(final_project_file=(root / "project.yaml").resolve(),
        audio_handoffs=(VoiceAudioHandoff(speaker_id="hero", voice_request=request,
            voice_preview=preview, credential_reference_id="ELEVENLABS_API_KEY",
            track=AudioTrackSpec(track_id="planned-dialogue", audio_kind="dialogue",
                asset_id=f"voice-{request.attempt_id}", shot_id=setup["context"].target_shot_id)),))
    orchestrator, limits, _, _ = _orchestrator(setup=setup, source_project=source, voice_context=context)
    limits = limits.model_copy(update={"allowed_remote_candidates": tuple(
        item for item in limits.allowed_remote_candidates if item.endswith("/voice-separate"))})
    prepared = orchestrator.prepare(limits=limits)
    if mutation is None:
        assert prepared.decision.disposition == "GENERATE_ONCE", prepared.decision.rationale
        assert prepared.resolved_request.effective_output.native_audio is False
        assert prepared.voice_handoffs[0].voice_request == request
    else:
        assert prepared.decision.disposition == "BLOCKED_CAPABILITY"
        assert any("VOICE_REQUEST_OR_CAPABILITY_CONFLICT" in reason
                   for reason in prepared.decision.rationale)
