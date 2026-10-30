"""Immutable voice-provider settings with legacy-compatible serialization."""
from __future__ import annotations

from pydantic import ConfigDict, Field, field_validator, model_serializer

from ai_video.production.models import StrictModel


class VoiceProviderParameters(StrictModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, hide_input_in_errors=True
    )
    stability_milli: int | None = Field(default=None, strict=True, ge=0, le=1000)
    similarity_boost_milli: int | None = Field(
        default=None, strict=True, ge=0, le=1000
    )
    style_milli: int | None = Field(default=None, strict=True, ge=0, le=1000)
    use_speaker_boost: bool | None = Field(default=None, strict=True)
    speed_milli: int | None = Field(default=None, strict=True, ge=700, le=1200)
    audio_tags: tuple[str, ...] = ()

    @field_validator("audio_tags")
    @classmethod
    def _validate_audio_tags(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        from ai_video.production.elevenlabs_performance import validate_audio_tags
        return validate_audio_tags(value)

    def validate_route(self, provider_kind: str, model_id: str) -> None:
        if self.audio_tags and (provider_kind != "elevenlabs" or model_id != "eleven_v4"):
            raise ValueError("Audio tags require the qualified ElevenLabs eleven_v4 route")

    @model_serializer(mode="wrap")
    def _preserve_legacy_parameters(self, handler):
        data = handler(self)
        if not self.audio_tags:
            data.pop("audio_tags", None)
        return data
