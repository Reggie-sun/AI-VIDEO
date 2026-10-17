"""Exact native-video audio mapping and source-materialization proof values."""
import hashlib
import json
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel

_SHA = r"^[0-9a-f]{64}$"


class AudioTimeSegment(StrictModel):
    source_start_sample: int = Field(strict=True, ge=0)
    source_duration_samples: int = Field(strict=True, gt=0)
    output_offset_sample: int = Field(strict=True, ge=0)
    output_duration_samples: int = Field(strict=True, gt=0)


class NativeAudioRetime(StrictModel):
    visual_layer_id: str = Field(min_length=1)
    stream_index: Literal[0] = 0
    time_map_sha256: str = Field(pattern=_SHA)
    segments: tuple[AudioTimeSegment, ...] = Field(min_length=1, max_length=63)

    @model_validator(mode="after")
    def _continuous(self):
        if self.segments[0].output_offset_sample != 0:
            raise ValueError("Native audio mapping must begin at output offset zero")
        for left, right in zip(self.segments, self.segments[1:]):
            if (left.source_start_sample + left.source_duration_samples != right.source_start_sample
                    or left.output_offset_sample + left.output_duration_samples != right.output_offset_sample):
                raise ValueError("Native audio mapping must cover continuous source/output windows")
        return self


class AudioSegmentProcessingProof(StrictModel):
    segment: AudioTimeSegment
    processed_samples: int = Field(strict=True, gt=0)
    padded_samples: int = Field(strict=True, ge=0)
    trimmed_samples: int = Field(strict=True, ge=0)

    @model_validator(mode="after")
    def _counts(self):
        if self.padded_samples and self.trimmed_samples:
            raise ValueError("A segment cannot be both padded and trimmed")
        if self.processed_samples + self.padded_samples - self.trimmed_samples != self.segment.output_duration_samples:
            raise ValueError("Native audio correction does not cover exact output samples")
        return self


class NativeAudioDerivationProof(StrictModel):
    processor: Literal["ffmpeg-atempo/1"] = "ffmpeg-atempo/1"
    track_id: str = Field(min_length=1)
    source_video_asset_id: str = Field(min_length=1)
    source_video_sha256: str = Field(pattern=_SHA)
    stream_index: Literal[0] = 0
    sample_rate_hz: int = Field(strict=True, gt=0)
    channels: Literal[2] = 2
    audio_start_sample: int = Field(strict=True, ge=0)
    input_pcm_sha256: str = Field(pattern=_SHA)
    input_samples: int = Field(strict=True, gt=0)
    mapped_pcm_sha256: str = Field(pattern=_SHA)
    mapped_samples: int = Field(strict=True, gt=0)
    mapping_sha256: str = Field(pattern=_SHA)
    ffmpeg_sha256: str = Field(pattern=_SHA)
    ffprobe_sha256: str = Field(pattern=_SHA)
    segment_results: tuple[AudioSegmentProcessingProof, ...] = Field(min_length=1, max_length=63)

    @model_validator(mode="after")
    def _coverage(self):
        if self.audio_start_sample >= self.input_samples:
            raise ValueError("Native audio proof source does not overlap the decoded window")
        if sum(item.segment.output_duration_samples for item in self.segment_results) != self.mapped_samples:
            raise ValueError("Native audio proof output coverage differs from mapped samples")
        if max(item.segment.source_start_sample + item.segment.source_duration_samples
               for item in self.segment_results) > self.input_samples:
            raise ValueError("Native audio proof reads outside decoded input")
        return self


def native_audio_mapping_sha256(mapping: NativeAudioRetime) -> str:
    payload = json.dumps(
        mapping.model_dump(mode="json"),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()
