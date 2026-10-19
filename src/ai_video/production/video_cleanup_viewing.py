"""Prepare a browser-compatible viewing proxy from a lossless RGB cleanup master."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_artifact import MeasuredVideoMetadata
from ai_video.production.video_cleanup_media import (
    VideoCleanupTools,
    _LocalRunner,
    _pcm_hash,
    _probe,
)


_SHA = r"^[0-9a-f]{64}$"
_FRAME_FIELDS = (
    "width",
    "height",
    "fps_numerator",
    "fps_denominator",
    "frame_count",
    "audio_stream_count",
    "duration_milliseconds",
)


class CleanupViewingProxyReceipt(StrictModel):
    """Sealed technical evidence for a separate, lossy viewing derivative."""

    contract_version: Literal["video-cleanup-viewing-proxy/1"] = (
        "video-cleanup-viewing-proxy/1"
    )
    qualification: Literal["NOT_EVALUATED"] = "NOT_EVALUATED"
    source: MeasuredVideoMetadata
    output: MeasuredVideoMetadata
    source_pixel_format: Literal["gbrp", "rgb24"]
    output_pixel_format: Literal["yuv420p"] = "yuv420p"
    output_color_range: Literal["tv"] = "tv"
    output_color_space: Literal["bt709"] = "bt709"
    output_color_primaries: Literal["bt709"] = "bt709"
    output_color_transfer: Literal["bt709"] = "bt709"
    ffmpeg_sha256: str = Field(pattern=_SHA)
    ffprobe_sha256: str = Field(pattern=_SHA)
    video_encoding: Literal["libx264-crf17-veryfast-bt709-limited-yuv420p/1"] = (
        "libx264-crf17-veryfast-bt709-limited-yuv420p/1"
    )
    source_frame_times: tuple[int, ...]
    output_frame_times: tuple[int, ...]
    input_audio_sha256: str | None = Field(default=None, pattern=_SHA)
    output_audio_sha256: str | None = Field(default=None, pattern=_SHA)
    input_audio_signature: dict[str, str | int] | None = None
    output_audio_signature: dict[str, str | int] | None = None
    content_hash: str = Field(pattern=_SHA)

    @model_validator(mode="after")
    def _validate_seal_and_preservation(self):
        if self.content_hash != canonical_sha256(self):
            raise ValueError("Cleanup viewing proxy receipt seal changed")
        if self.source.artifact_sha256 == self.output.artifact_sha256:
            raise ValueError("Cleanup viewing proxy must be a separate media artifact")
        if any(
            getattr(self.source, name) != getattr(self.output, name)
            for name in _FRAME_FIELDS
        ):
            raise ValueError(
                "Cleanup viewing proxy changed geometry, timing or audio streams"
            )
        count = self.source.frame_count
        if (
            len(self.source_frame_times) != count
            or len(self.output_frame_times) != count
            or self.source_frame_times != self.output_frame_times
            or not self.source_frame_times
            or self.source_frame_times[0] != 0
            or any(
                type(value) is not int
                for value in (*self.source_frame_times, *self.output_frame_times)
            )
            or any(
                after <= before
                for before, after in zip(
                    self.source_frame_times, self.source_frame_times[1:]
                )
            )
        ):
            raise ValueError(
                "Cleanup viewing proxy must preserve every ordered frame timestamp"
            )
        if self.source.audio_stream_count not in (0, 1):
            raise ValueError(
                "Cleanup viewing proxy supports at most one original audio stream"
            )
        if (
            self.input_audio_sha256 != self.output_audio_sha256
            or self.input_audio_signature != self.output_audio_signature
        ):
            raise ValueError(
                "Cleanup viewing proxy changed native audio samples or timing"
            )
        if self.source.audio_stream_count == 1:
            if self.input_audio_sha256 is None or self.input_audio_signature is None:
                raise ValueError(
                    "Cleanup viewing proxy is missing native audio preservation evidence"
                )
        elif (
            self.input_audio_sha256 is not None
            or self.input_audio_signature is not None
            or self.output_audio_sha256 is not None
            or self.output_audio_signature is not None
        ):
            raise ValueError("Silent cleanup master cannot claim native audio samples")
        if self.output.codec_name != "h264":
            raise ValueError(
                "Cleanup viewing proxy must use browser-compatible H.264 video"
            )
        return self


@dataclass(frozen=True)
class PreparedCleanupViewingProxy:
    media_bytes: bytes
    receipt: CleanupViewingProxyReceipt


def _video_stream_details(runner: _LocalRunner, path: Path) -> dict[str, str]:
    info = json.loads(
        runner.run(
            "ffprobe",
            [
                "-v",
                "error",
                "-protocol_whitelist",
                "file",
                "-f",
                "mov",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name,pix_fmt,color_range,color_space,color_primaries,color_transfer",
                "-of",
                "json",
                path,
            ],
        )
    )
    streams = info.get("streams", [])
    if len(streams) != 1:
        raise ValueError("Cleanup viewing proxy requires one video stream")
    return streams[0]


def prepare_cleanup_viewing_proxy(
    *,
    source_bytes: bytes,
    tools: VideoCleanupTools,
) -> PreparedCleanupViewingProxy:
    """Create a lossy, human-viewable proxy without modifying the RGB master."""
    if (
        not isinstance(source_bytes, bytes)
        or not source_bytes
        or len(source_bytes) > tools.max_source_bytes
    ):
        raise ValueError("Cleanup viewing source byte bound exceeded")

    runner = _LocalRunner(tools)
    with tempfile.TemporaryDirectory(prefix="ai-video-cleanup-view-") as tmp:
        root = Path(tmp)
        source_path, output_path = (
            root / "cleanup-master.mp4",
            root / "viewing-proxy.mp4",
        )
        source_path.write_bytes(source_bytes)
        source, source_times, source_audio_signature = _probe(
            runner, source_path, source_bytes
        )
        source_details = _video_stream_details(runner, source_path)
        source_pixel_format = source_details.get("pix_fmt")
        if source_details.get("codec_name") != "h264" or source_pixel_format not in {
            "gbrp",
            "rgb24",
        }:
            raise ValueError(
                "Viewing proxy requires an H.264 RGB cleanup master (gbrp or rgb24)"
            )
        if source.width % 2 or source.height % 2:
            raise ValueError(
                "yuv420p viewing proxy requires even cleanup master geometry"
            )

        input_audio_sha256 = _pcm_hash(
            runner, source_path, source.audio_stream_count == 1
        )
        runner.run(
            "ffmpeg",
            [
                "-nostdin",
                "-v",
                "error",
                "-protocol_whitelist",
                "file",
                "-f",
                "mov",
                "-i",
                source_path,
                "-map",
                "0:v:0",
                "-map",
                "0:a:0?",
                "-vf",
                "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p",
                "-fps_mode",
                "passthrough",
                "-c:v",
                "libx264",
                "-crf",
                "17",
                "-preset",
                "veryfast",
                "-x264-params",
                "colorprim=bt709:transfer=bt709:colormatrix=bt709:range=limited",
                "-pix_fmt",
                "yuv420p",
                "-color_range",
                "tv",
                "-colorspace",
                "bt709",
                "-color_primaries",
                "bt709",
                "-color_trc",
                "bt709",
                "-threads",
                "1",
                "-c:a",
                "copy",
                "-map_metadata",
                "-1",
                "-movflags",
                "+faststart",
                "-fs",
                str(tools.max_source_bytes),
                output_path,
            ],
        )
        if not output_path.is_file():
            raise ValueError("Cleanup viewing proxy encoder produced no file")
        output_bytes = output_path.read_bytes()
        if not output_bytes or len(output_bytes) > tools.max_source_bytes:
            raise ValueError("Cleanup viewing proxy output byte bound exceeded")
        output, output_times, output_audio_signature = _probe(
            runner, output_path, output_bytes
        )
        output_details = _video_stream_details(runner, output_path)
        expected_tags = {
            "codec_name": "h264",
            "pix_fmt": "yuv420p",
            "color_range": "tv",
            "color_space": "bt709",
            "color_primaries": "bt709",
            "color_transfer": "bt709",
        }
        if any(
            output_details.get(name) != expected
            for name, expected in expected_tags.items()
        ):
            raise ValueError(
                "Cleanup viewing proxy output pixel format or BT.709 color tags are invalid"
            )
        output_audio_sha256 = _pcm_hash(
            runner, output_path, output.audio_stream_count == 1
        )
        runner.check_tools()

        data = {
            "contract_version": "video-cleanup-viewing-proxy/1",
            "qualification": "NOT_EVALUATED",
            "source": source.model_dump(mode="python"),
            "output": output.model_dump(mode="python"),
            "source_pixel_format": source_pixel_format,
            "output_pixel_format": "yuv420p",
            "output_color_range": "tv",
            "output_color_space": "bt709",
            "output_color_primaries": "bt709",
            "output_color_transfer": "bt709",
            "ffmpeg_sha256": runner.hashes["ffmpeg"],
            "ffprobe_sha256": runner.hashes["ffprobe"],
            "video_encoding": "libx264-crf17-veryfast-bt709-limited-yuv420p/1",
            "source_frame_times": source_times,
            "output_frame_times": output_times,
            "input_audio_sha256": input_audio_sha256,
            "output_audio_sha256": output_audio_sha256,
            "input_audio_signature": source_audio_signature,
            "output_audio_signature": output_audio_signature,
        }
        data["content_hash"] = canonical_sha256(data)
        receipt = CleanupViewingProxyReceipt.model_validate(data)
        return PreparedCleanupViewingProxy(media_bytes=output_bytes, receipt=receipt)
