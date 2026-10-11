"""Explicit bounded endpoint admission; never changes a submitted request."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity, StrictModel
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement


_SHA256 = r"^[0-9a-f]{64}$"


class VideoNominalEndpointRecovery(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal["video-nominal-endpoint-recovery/1"]
    request_receipt_fingerprint: str = Field(pattern=_SHA256)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    fetch_fingerprint: str = Field(pattern=_SHA256)
    measured_content_hash: str = Field(pattern=_SHA256)
    original_output: VideoFlexibleOutputRequirement
    duration_milliseconds: int = Field(strict=True, gt=0)
    frame_count: int = Field(strict=True, gt=0)
    actor: ActorIdentity
    reason: str = Field(min_length=1, max_length=2048)
    original_failure: Literal["exact_seconds_timing_mismatch"]
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_recovery(self):
        if (
            not self.reason.strip()
            or self.original_output.timing_mode != "exact_seconds"
            or self.original_output.matches_timing_measurement(
                duration_milliseconds=self.duration_milliseconds,
                frame_count=self.frame_count,
            )
            or not self.original_output.model_copy(
                update={"timing_mode": "nominal_seconds"}
            ).matches_timing_measurement(
                duration_milliseconds=self.duration_milliseconds,
                frame_count=self.frame_count,
            )
            or self.content_hash != canonical_sha256(
                self.model_dump(mode="json", exclude={"content_hash"})
            )
        ):
            raise ValueError("nominal endpoint recovery is not an exact bounded exception")
        return self

    @classmethod
    def create(cls, *, request, fetch_receipt, measured, actor, reason):
        output = request.effective_output
        if not isinstance(output, VideoFlexibleOutputRequirement) or (
            request.continuity_binding is not None
            or request.commercial_binding is not None
            or request.hard_cut_keyframe_binding is not None
            or request.c4_multi_anchor_binding is not None
            or any(item.role == "last_frame" for item in request.image_bindings)
            or measured.fps_numerator != output.fps * measured.fps_denominator
        ):
            raise ValueError("nominal endpoint recovery requires an unconditioned exact request")
        data = {
            "schema_version": "video-nominal-endpoint-recovery/1",
            "request_receipt_fingerprint": request.desired_generation_fingerprint,
            "resolved_generation_hash": request.resolved_generation_hash,
            "fetch_fingerprint": fetch_receipt.fetch_fingerprint,
            "measured_content_hash": canonical_sha256(measured.model_dump(mode="json")),
            "original_output": output,
            "duration_milliseconds": measured.duration_milliseconds,
            "frame_count": measured.frame_count,
            "actor": actor,
            "reason": reason,
            "original_failure": "exact_seconds_timing_mismatch",
        }
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        return cls.model_validate({
            **data,
            "content_hash": canonical_sha256(
                candidate.model_dump(mode="json", exclude={"content_hash"})
            ),
        })

    def validate_probe_binding(self, *, probe_receipt):
        if (
            self.request_receipt_fingerprint != probe_receipt.request_receipt_fingerprint
            or self.resolved_generation_hash != probe_receipt.resolved_generation_hash
            or self.fetch_fingerprint != probe_receipt.fetch_fingerprint
            or self.measured_content_hash
            != canonical_sha256(probe_receipt.measured.model_dump(mode="json"))
            or self.duration_milliseconds != probe_receipt.measured.duration_milliseconds
            or self.frame_count != probe_receipt.measured.frame_count
        ):
            raise ValueError("nominal endpoint recovery does not bind the exact probe")

    def validate_binding(self, *, request, fetch_receipt, measured):
        exact = self.create(
            request=request, fetch_receipt=fetch_receipt, measured=measured,
            actor=self.actor, reason=self.reason,
        )
        if exact != self:
            raise ValueError("nominal endpoint recovery does not bind current evidence")
