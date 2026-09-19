"""Immutable routed-voice execution evidence consumed by the existing committer."""

from pydantic import Field, model_validator
from typing import Literal

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
from ai_video.production.hashing import canonical_sha256
from ai_video.production.paid_provider import PaidProviderCallPreview
from ai_video.production.video import VideoGenerationPreview


class VoiceRoutingExecutionEnvelope(StrictModel):
    """One selected voice handoff and its prospective video budget counterpart."""

    schema_version: Literal["voice-routing-execution/1"] = "voice-routing-execution/1"
    binding: GenerationDecisionExecutionBinding
    video_preview: VideoGenerationPreview
    video_paid_preview: PaidProviderCallPreview
    envelope_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @staticmethod
    def _payload(values: dict[str, object]) -> dict[str, object]:
        return {
            "schema": "voice-routing-execution/1",
            **{key: value for key, value in values.items() if key != "envelope_hash"},
        }

    @model_validator(mode="after")
    def _validate_hash(self) -> "VoiceRoutingExecutionEnvelope":
        expected = canonical_sha256(
            self._payload(self.model_dump(mode="json", exclude={"envelope_hash"}))
        )
        if self.envelope_hash != expected:
            raise ValueError("voice routing execution envelope hash is invalid")
        if self.video_paid_preview.operation != "video_generation":
            raise ValueError("voice routing envelope requires a prospective video preview")
        return self

    @classmethod
    def create(
        cls,
        *,
        binding: GenerationDecisionExecutionBinding,
        video_preview: VideoGenerationPreview,
        video_paid_preview: PaidProviderCallPreview,
    ) -> "VoiceRoutingExecutionEnvelope":
        values: dict[str, object] = {
            "schema_version": "voice-routing-execution/1",
            "binding": binding,
            "video_preview": video_preview,
            "video_paid_preview": video_paid_preview,
        }
        provisional = cls.model_construct(**values, envelope_hash="0" * 64)
        values["envelope_hash"] = canonical_sha256(
            cls._payload(provisional.model_dump(mode="json", exclude={"envelope_hash"}))
        )
        return cls.model_validate(values)
