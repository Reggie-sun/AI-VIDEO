"""P4 admission regressions for mandatory routed speech and legacy bytes."""
import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.composition import resolve_composition
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import CompositionSpec
from ai_video.production.voice_routing_contracts import VoiceRoutingRequirement, VoiceSpeakerRequirement
from production_project_factory import make_loaded_project_and_spec


def test_legacy_composition_reopen_omits_voice_sources_and_keeps_hash(tmp_path):
    _project, spec = make_loaded_project_and_spec(tmp_path)
    original = spec.model_dump_json()
    assert "voice_sources" not in original
    reopened = CompositionSpec.model_validate_json(original)
    assert reopened.content_hash == spec.content_hash
    assert reopened.model_dump_json() == original


def test_p4_cannot_treat_auto_optional_as_optional_speech(tmp_path):
    project, spec = make_loaded_project_and_spec(tmp_path)
    shot = project.shots[0]
    voice = VoiceRoutingRequirement(speakers=(VoiceSpeakerRequirement(
        speaker_id=shot.character_ids[0], language="en", script_text="Hello."),))
    authored = seal_artifact(shot.model_copy(update={"voice_routing": voice, "dialogue": "Hello."}))
    # Negative consumer test: an otherwise valid canonical timeline has no
    # speech. AudioNeed.OPTIONAL must not let its required dialogue disappear.
    project = project.model_copy(update={"shots": (authored, *project.shots[1:])})
    with pytest.raises(AiVideoError) as caught:
        resolve_composition(project, spec, renderer_version="0.7.103")
    assert caught.value.code is ErrorCode.COMPOSITION_INVALID
    assert "selected execution binding" in caught.value.technical_detail


def test_imported_audio_cannot_qualify_fixed_voice_even_with_matching_metadata(tmp_path):
    from types import SimpleNamespace
    from ai_video.production.voice_routing import _separate_identity_samples
    from production_project_factory import make_p4_composition_fixture

    project, _spec = make_p4_composition_fixture(tmp_path)
    audio = next(a for a in project.registry.assets if a.audio_metadata is not None)
    evidence = SimpleNamespace(subject_ids=(audio.asset_id, project.shots[0].shot_id))
    # This is an adversarial reader-level check, not a synthetic PASS receipt.
    # Imported samples have no exact succeeded voice-request lineage.
    assert not _separate_identity_samples(project, evidence, (audio.sha256,), None, None)


def test_native_fixed_voice_has_no_bindable_control_even_if_evidence_is_claimed():
    from ai_video.production.voice_routing import _voice_identity_evidence
    from ai_video.production.voice_routing_contracts import VoiceRoute

    assert _voice_identity_evidence(None, None, None, None, VoiceRoute.NATIVE, None) is None
