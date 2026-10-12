"""Immutable Grok video hard controls sealed inside provider profiles."""

from __future__ import annotations

import re

from pydantic import ConfigDict, Field

from ai_video.production.models import StrictModel


_SAFE_ASSET_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"
_VOICE_ID = r"^[a-z0-9][a-z0-9_-]{0,63}$"


class GrokTimedKeyframe(StrictModel):
    """One profile-pinned frame referring to an exact request image asset.

    Timestamps are measured in thirds of a second. The adapter checks the
    timestamp against each request's output duration and verifies the asset
    identity against that request's Registry-bound image references.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    asset_id: str = Field(pattern=_SAFE_ASSET_ID)
    asset_sha256: str = Field(pattern=_SHA256)
    timestamp_ticks: int = Field(strict=True, gt=0, le=44)


def validate_grok_video_controls(
    keyframes: tuple[GrokTimedKeyframe, ...], reference_voices: tuple[str, ...]
) -> None:
    """Validate canonical profile-level keyframe and voice control ordering."""

    if len(keyframes) > 4:
        raise ValueError("Grok video profiles support at most four timed keyframes")
    if tuple(frame.timestamp_ticks for frame in keyframes) != tuple(
        sorted({frame.timestamp_ticks for frame in keyframes})
    ):
        raise ValueError("Grok keyframes must have unique, strictly increasing timestamps")
    identities: dict[str, str] = {}
    for frame in keyframes:
        if frame.asset_id in identities and identities[frame.asset_id] != frame.asset_sha256:
            raise ValueError("Grok repeated keyframe asset identity must match exact bytes")
        identities[frame.asset_id] = frame.asset_sha256
    if len(reference_voices) > 3:
        raise ValueError("Grok video profiles support at most three preset voice IDs")
    if len(set(reference_voices)) != len(reference_voices):
        raise ValueError("Grok preset voice IDs must be unique")
    if any(not voice_id.isascii() or not re.fullmatch(_VOICE_ID, voice_id)
           for voice_id in reference_voices):
        raise ValueError("Grok preset voice IDs must be canonical lowercase ASCII IDs")


__all__ = ["GrokTimedKeyframe", "validate_grok_video_controls"]
