"""Immutable authoring contracts for pre-generation voice source routing."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from enum import Enum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256


_SAFE_ID = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$"
_SHA256 = r"^[0-9a-f]{64}$"
_BCP47_CORE = (
    r"^[a-z]{2,3}"
    r"(?:-[A-Z][a-z]{3})?"
    r"(?:-(?:[A-Z]{2}|[0-9]{3}))?"
    r"(?:-(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*$"
)


class VoiceRoute(str, Enum):
    NATIVE = "native"
    SEPARATE = "separate"
    NO_VOICE = "no_voice"


class VoiceMode(str, Enum):
    AUTO = "auto"
    NATIVE_REQUIRED = "native_required"
    SEPARATE_REQUIRED = "separate_required"
    NO_VOICE = "no_voice"


class VoiceSpeakerRequirement(StrictModel):
    speaker_id: str = Field(pattern=_SAFE_ID)
    language: str = Field(pattern=_BCP47_CORE)
    script_text: str = Field(min_length=1)
    consistency: Literal["single_shot", "cross_shot_fixed"] = "single_shot"
    voice_id: str | None = Field(default=None, min_length=1)
    reference_asset_id: str | None = Field(default=None, pattern=_SAFE_ID)
    reference_sha256: str | None = Field(default=None, pattern=_SHA256)

    @field_validator("language")
    @classmethod
    def _validate_canonical_language_variants(cls, value: str) -> str:
        subtags = value.split("-")[1:]
        index = 0
        if subtags and re.fullmatch(r"[A-Z][a-z]{3}", subtags[0]):
            index += 1
        if index < len(subtags) and re.fullmatch(
            r"(?:[A-Z]{2}|[0-9]{3})", subtags[index]
        ):
            index += 1
        variants = subtags[index:]
        if any(variant != variant.lower() for variant in variants):
            raise ValueError("language variants must use canonical lowercase")
        if len(variants) != len(set(variants)):
            raise ValueError("language variants must be unique")
        return value

    @model_validator(mode="after")
    def _validate_identity_evidence(self) -> "VoiceSpeakerRequirement":
        if not self.script_text.strip():
            raise ValueError("script_text must contain spoken text")
        if not unicodedata.is_normalized("NFC", self.script_text):
            raise ValueError("script_text must be NFC normalized")
        if (self.reference_asset_id is None) != (self.reference_sha256 is None):
            raise ValueError("reference_asset_id and reference_sha256 must be paired")
        if self.consistency == "cross_shot_fixed" and (
            self.voice_id is None and self.reference_asset_id is None
        ):
            raise ValueError("cross_shot_fixed requires a voice_id or an exact reference")
        return self

    @property
    def script_hash(self) -> str:
        return hashlib.sha256(self.script_text.encode("utf-8")).hexdigest()


class VoiceRoutingRequirement(StrictModel):
    contract_version: Literal["voice-routing/1"] = "voice-routing/1"
    mode: VoiceMode = VoiceMode.AUTO
    speakers: tuple[VoiceSpeakerRequirement, ...] = ()
    native_sound_required: bool = Field(default=False, strict=True)

    @model_validator(mode="after")
    def _validate_mode_and_speakers(self) -> "VoiceRoutingRequirement":
        speaker_ids = tuple(speaker.speaker_id for speaker in self.speakers)
        if len(set(speaker_ids)) != len(speaker_ids):
            raise ValueError("speaker IDs must be unique")
        if self.mode == VoiceMode.NO_VOICE:
            if self.speakers:
                raise ValueError("no_voice mode must not include speakers")
        elif not self.speakers:
            raise ValueError("voice routing modes require at least one speaker")
        if self.mode == VoiceMode.SEPARATE_REQUIRED and self.native_sound_required:
            raise ValueError("separate_required cannot require native sound")
        return self

    @property
    def content_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))

    @property
    def audio_need(self) -> str:
        if self.mode == VoiceMode.NATIVE_REQUIRED:
            return "required"
        if self.mode == VoiceMode.SEPARATE_REQUIRED:
            return "forbidden"
        if self.mode == VoiceMode.NO_VOICE and self.native_sound_required:
            return "required"
        return "optional"
