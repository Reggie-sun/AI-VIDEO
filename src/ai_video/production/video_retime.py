"""Authored source/output frame coordinates for the composition owner."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel


class VideoTimePoint(StrictModel):
    source_frame: int = Field(strict=True, ge=0)
    output_frame: int = Field(strict=True, ge=0)


class VideoTimeMap(StrictModel):
    contract_version: Literal["video-time-map/1"] = "video-time-map/1"
    points: tuple[VideoTimePoint, ...] = Field(min_length=2, max_length=64)
    audio_policy: Literal["mute"]

    @model_validator(mode="after")
    def _ordered_coordinates(self):
        if self.points[0] != VideoTimePoint(source_frame=0, output_frame=0):
            raise ValueError("Video time map must begin at the selected source/output origin")
        for left, right in zip(self.points, self.points[1:]):
            source = right.source_frame - left.source_frame
            output = right.output_frame - left.output_frame
            if source <= 0 or output <= 0:
                raise ValueError("Video time map coordinates must increase without freezes or reversal")
            if not Fraction(1, 10) <= Fraction(source, output) <= 5:
                raise ValueError("Video time map exceeds the pinned renderer playback-rate range")
        return self

    @property
    def source_duration_frames(self) -> int:
        return self.points[-1].source_frame

    @property
    def output_duration_frames(self) -> int:
        return self.points[-1].output_frame


@dataclass(frozen=True)
class VideoTimeSegment:
    source_start_frame: int
    source_duration_frames: int
    output_start_frame: int
    output_duration_frames: int


def resolve_video_time_segments(
    time_map: VideoTimeMap,
) -> tuple[VideoTimeSegment, ...]:
    return tuple(
        VideoTimeSegment(
            source_start_frame=left.source_frame,
            source_duration_frames=right.source_frame - left.source_frame,
            output_start_frame=left.output_frame,
            output_duration_frames=right.output_frame - left.output_frame,
        )
        for left, right in zip(time_map.points, time_map.points[1:])
    )


def resolve_video_time_source_frames(
    segment: VideoTimeSegment,
) -> tuple[int, ...]:
    """Map each output frame to its exact source-frame offset.

    Integer floor sampling repeats source frames for slow motion and skips
    source frames for fast motion while keeping the source and output windows
    half-open and bounded by the authored segment endpoints.
    """
    return tuple(
        segment.source_start_frame
        + (output_offset * segment.source_duration_frames)
        // segment.output_duration_frames
        for output_offset in range(segment.output_duration_frames)
    )
