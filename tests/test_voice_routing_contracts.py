from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from ai_video.production.hashing import canonical_sha256
from ai_video.production.voice_routing_contracts import (
    VoiceMode,
    VoiceRoute,
    VoiceRoutingRequirement,
    VoiceSpeakerRequirement,
)


_SHA256 = "a" * 64


def _speaker(**changes: object) -> VoiceSpeakerRequirement:
    values: dict[str, object] = {
        "speaker_id": "chen-li",
        "language": "zh-Hans-CN",
        "script_text": "你回来了。",
    }
    values.update(changes)
    return VoiceSpeakerRequirement(**values)


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"mode": VoiceMode.AUTO}, "at least one speaker"),
        ({"mode": VoiceMode.NO_VOICE, "speakers": (_speaker(),)}, "must not include speakers"),
        (
            {
                "mode": VoiceMode.SEPARATE_REQUIRED,
                "speakers": (_speaker(),),
                "native_sound_required": True,
            },
            "cannot require native sound",
        ),
        (
            {"mode": VoiceMode.AUTO, "speakers": (_speaker(), _speaker())},
            "speaker IDs must be unique",
        ),
    ],
)
def test_voice_routing_requirement_rejects_invalid_boundary_matrix(
    values: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        VoiceRoutingRequirement(**values)


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"speaker_id": "bad id"}, "speaker_id"),
        ({"language": "Chinese"}, "language"),
        ({"language": "zh-hans-CN"}, "language"),
        ({"language": "en-US-foo"}, "language"),
        ({"language": "en-US-ABCDE"}, "canonical lowercase"),
        ({"language": "en-US-abcde-abcde"}, "must be unique"),
        ({"script_text": "e\u0301"}, "NFC"),
        ({"script_text": " \t\n"}, "spoken text"),
        ({"reference_asset_id": "voice-ref"}, "paired"),
        ({"reference_sha256": _SHA256}, "paired"),
        ({"consistency": "cross_shot_fixed"}, "voice_id or an exact reference"),
    ],
)
def test_speaker_requirement_rejects_unsealed_identity_or_invalid_text(
    values: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        _speaker(**values)


def test_unicode_script_hash_content_hash_and_audio_need_are_deterministic() -> None:
    speaker = _speaker(
        consistency="cross_shot_fixed",
        reference_asset_id="voice-ref",
        reference_sha256=_SHA256,
    )
    requirement = VoiceRoutingRequirement(speakers=(speaker,))

    assert speaker.script_hash == hashlib.sha256("你回来了。".encode("utf-8")).hexdigest()
    assert requirement.content_hash == canonical_sha256(requirement.model_dump(mode="json"))
    assert requirement.audio_need == "optional"
    assert VoiceRoutingRequirement(
        mode=VoiceMode.NATIVE_REQUIRED, speakers=(speaker,)
    ).audio_need == "required"
    assert VoiceRoutingRequirement(
        mode=VoiceMode.SEPARATE_REQUIRED, speakers=(speaker,)
    ).audio_need == "forbidden"
    assert VoiceRoutingRequirement(mode=VoiceMode.NO_VOICE).audio_need == "optional"
    assert VoiceRoutingRequirement(
        mode=VoiceMode.NO_VOICE, native_sound_required=True
    ).audio_need == "required"
    assert {route.value for route in VoiceRoute} == {"native", "separate", "no_voice"}


def test_contract_models_are_frozen_and_native_sound_requires_a_real_boolean() -> None:
    speaker = _speaker()
    requirement = VoiceRoutingRequirement(speakers=(speaker,))

    with pytest.raises(ValidationError, match="frozen"):
        speaker.language = "en-US"  # type: ignore[misc]
    with pytest.raises(ValidationError, match="frozen"):
        requirement.mode = VoiceMode.NO_VOICE  # type: ignore[misc]
    with pytest.raises(ValidationError):
        VoiceRoutingRequirement(speakers=(speaker,), native_sound_required=1)
