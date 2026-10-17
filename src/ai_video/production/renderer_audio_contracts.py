"""P4 renderer audio source bindings and exact derivation proof."""
from pathlib import Path
from typing import Literal

from pydantic import Field, SerializerFunctionWrapHandler, model_serializer, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.audio_retime_contracts import NativeAudioDerivationProof


class RendererAudioBinding(StrictModel):
    asset_id: str = Field(min_length=1)
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_mime_type: Literal[
        "audio/wav",
        "audio/mpeg",
        "audio/mp4",
        "audio/aac",
        "audio/flac",
    ]
    materialized_path: Path
    sample_rate_hz: int = Field(strict=True, gt=0)
    channels: int = Field(strict=True, ge=1, le=2)
    duration_samples: int = Field(strict=True, gt=0)
    resolved_track_ids: tuple[str, ...] = Field(min_length=1)
    native_audio_derivations: tuple[NativeAudioDerivationProof, ...] = ()

    @model_validator(mode="after")
    def _validate_materialized_identity(self) -> "RendererAudioBinding":
        suffix_by_mime = {
            "audio/wav": ".wav",
            "audio/mpeg": ".mp3",
            "audio/mp4": ".m4a",
            "audio/aac": ".aac",
            "audio/flac": ".flac",
        }
        if (
            self.materialized_path.stem != self.asset_sha256
            or self.materialized_path.suffix != suffix_by_mime[self.asset_mime_type]
        ):
            raise ValueError("renderer audio MIME requires exact hash suffix mapping")
        if len(self.resolved_track_ids) != len(set(self.resolved_track_ids)):
            raise ValueError("renderer audio resolved track IDs must be unique")
        derivation_track_ids = tuple(item.track_id for item in self.native_audio_derivations)
        if len(derivation_track_ids) != len(set(derivation_track_ids)):
            raise ValueError("native audio derivation track IDs must be unique")
        return self

    @model_serializer(mode="wrap")
    def _serialize_compatible_native_audio_derivations(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if not self.native_audio_derivations:
            data.pop("native_audio_derivations", None)
        return data
