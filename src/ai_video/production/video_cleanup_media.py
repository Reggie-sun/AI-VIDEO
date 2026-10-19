"""Bounded local source preparation, without a timeline or generation provider."""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Literal

from PIL import Image
from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.video_artifact import MeasuredVideoMetadata
from ai_video.production.video_cleanup_contracts import VideoCleanupPlan
from ai_video.production.video_cleanup_pixels import apply_clean_plate_frame


_SHA = r"^[0-9a-f]{64}$"


@dataclass(frozen=True)
class VideoCleanupTools:
    """Explicit trusted tool injection; never discover tools or install models."""

    ffmpeg: Path
    ffprobe: Path
    timeout_seconds: int = 120
    max_elapsed_seconds: int = 600
    max_frames: int = 600
    max_source_bytes: int = 200 * 1024 * 1024
    max_decoded_bytes: int = 1024 * 1024 * 1024
    max_duration_milliseconds: int = 60_000
    max_audio_decoded_bytes: int = 64 * 1024 * 1024

    def __post_init__(self):
        for name in ("timeout_seconds", "max_elapsed_seconds", "max_frames", "max_source_bytes",
                     "max_decoded_bytes", "max_duration_milliseconds", "max_audio_decoded_bytes"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError("Cleanup resource bounds must be positive integers")


class CleanupFrameProof(StrictModel):
    input_rgb_sha256: str = Field(pattern=_SHA)
    output_rgb_sha256: str = Field(pattern=_SHA)
    effective_mask_sha256: str = Field(pattern=_SHA)
    protected_rgb_sha256: str = Field(pattern=_SHA)
    changed_pixel_count: int = Field(strict=True, ge=0)
    protected_pixel_changes: Literal[0] = 0

class VideoCleanupReceipt(StrictModel):
    contract_version: Literal["video-cleanup/1"] = "video-cleanup/1"
    qualification: Literal["NOT_EVALUATED"] = "NOT_EVALUATED"
    plan: VideoCleanupPlan
    source: MeasuredVideoMetadata
    output: MeasuredVideoMetadata
    ffmpeg_sha256: str = Field(pattern=_SHA)
    ffprobe_sha256: str = Field(pattern=_SHA)
    video_encoding: Literal["libx264rgb-crf0-rgb24/1"] = "libx264rgb-crf0-rgb24/1"
    source_frame_times: tuple[int, ...]
    output_frame_times: tuple[int, ...]
    input_audio_sha256: str | None = Field(default=None, pattern=_SHA)
    output_audio_sha256: str | None = Field(default=None, pattern=_SHA)
    input_audio_signature: dict[str, str | int] | None = None
    output_audio_signature: dict[str, str | int] | None = None
    frame_proofs: tuple[CleanupFrameProof, ...]
    content_hash: str = Field(pattern=_SHA)

    @model_validator(mode="after")
    def _identity_and_preservation(self):
        if self.content_hash != canonical_sha256(self):
            raise ValueError("Cleanup receipt seal changed")
        if self.plan.source_sha256 != self.source.artifact_sha256:
            raise ValueError("Cleanup plan differs from source identity")
        fields = ("width", "height", "fps_numerator", "fps_denominator", "frame_count",
                  "audio_stream_count", "duration_milliseconds")
        if any(getattr(self.source, name) != getattr(self.output, name) for name in fields):
            raise ValueError("Cleanup changed media geometry, timing or audio streams")
        count = self.source.frame_count
        if (len(self.frame_proofs) != count or len(self.source_frame_times) != count
                or self.source_frame_times != self.output_frame_times
                or self.source_frame_times[0] != 0
                or any(b <= a for a, b in zip(self.source_frame_times, self.source_frame_times[1:]))):
            raise ValueError("Cleanup must preserve every ordered frame and timestamp")
        selected = {frame.frame_index for frame in self.plan.frames}
        if any(index >= count for index in selected) or any(
                patch.plate_frame >= count for frame in self.plan.frames for patch in frame.patches):
            raise ValueError("Cleanup frame selection exceeds source frames")
        if any(proof.input_rgb_sha256 != proof.output_rgb_sha256
               for index, proof in enumerate(self.frame_proofs) if index not in selected):
            raise ValueError("Cleanup changed an unselected frame")
        if (self.input_audio_sha256 != self.output_audio_sha256
                or self.input_audio_signature != self.output_audio_signature
                or self.source.audio_stream_count not in (0, 1)):
            raise ValueError("Cleanup changed original audio samples or timing")
        if self.source.audio_stream_count == 1:
            if self.input_audio_sha256 is None or self.input_audio_signature is None:
                raise ValueError("Cleanup is missing native audio preservation proof")
        elif self.input_audio_sha256 is not None or self.input_audio_signature is not None:
            raise ValueError("Silent source cannot claim native audio samples")
        return self


@dataclass(frozen=True)
class PreparedVideoCleanup:
    media_bytes: bytes
    receipt: VideoCleanupReceipt

    def report(self) -> dict:
        return {"receipt": self.receipt.model_dump(mode="json"),
                "output_sha256": self.receipt.output.artifact_sha256,
                "output_size_bytes": len(self.media_bytes),
                "generation_calls": 0, "production_acceptance": "NOT_EVALUATED"}


class _LocalRunner:
    def __init__(self, tools: VideoCleanupTools):
        self.tools = tools
        self.deadline = time.monotonic() + tools.max_elapsed_seconds
        self.paths, self.hashes = {}, {}
        for key in ("ffmpeg", "ffprobe"):
            path = Path(getattr(tools, key))
            if not path.is_absolute():
                raise ValueError("Cleanup tools must be explicit absolute executables")
            path = path.resolve(strict=True)
            raw = _read_regular_file_nofollow(path, contained_by=path.parent)
            self.paths[key], self.hashes[key] = path, raw.file_sha256

    def check_tools(self):
        for key, path in self.paths.items():
            if _read_regular_file_nofollow(path, contained_by=path.parent).file_sha256 != self.hashes[key]:
                raise ValueError("Cleanup tool bytes changed during preparation")

    def run(self, key, args):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("Cleanup elapsed-time bound exhausted")
        self.check_tools()
        try:
            result = subprocess.run([str(self.paths[key]), *map(str, args)],
                stdin=subprocess.DEVNULL, capture_output=True, check=True,
                timeout=min(self.tools.timeout_seconds, remaining),
                env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "OMP_NUM_THREADS": "1"})
        except (subprocess.SubprocessError, OSError) as exc:
            raise ValueError(f"Local cleanup {key} operation failed ({type(exc).__name__})") from exc
        return result.stdout


def _probe(runner, path, raw):
    base = ["-v", "error", "-protocol_whitelist", "file", "-f", "mov"]
    info = json.loads(runner.run("ffprobe", [*base, "-show_streams", "-show_format", "-of", "json", path]))
    videos = [s for s in info["streams"] if s["codec_type"] == "video"]
    audios = [s for s in info["streams"] if s["codec_type"] == "audio"]
    if len(videos) != 1 or len(audios) > 1 or len(info["streams"]) != len(videos) + len(audios):
        raise ValueError("Cleanup requires one video and zero or one original audio stream")
    video = videos[0]
    if video.get("pix_fmt") not in {"yuv420p", "yuvj420p", "yuv422p", "yuv444p", "gbrp", "rgb24"}:
        raise ValueError("Cleanup currently supports only explicit 8-bit video formats")
    declared_count = int(video.get("nb_frames", 0))
    width, height = int(video["width"]), int(video["height"])
    duration_ms = int((Decimal(info["format"]["duration"]) * 1000).to_integral_value(rounding=ROUND_HALF_UP))
    if declared_count <= 0 or declared_count > runner.tools.max_frames:
        raise ValueError("Cleanup source exceeds frame bound or lacks declared MP4 frames")
    if width * height * 3 * declared_count > runner.tools.max_decoded_bytes:
        raise ValueError("Cleanup decoded-frame resource bound exceeded")
    if duration_ms > runner.tools.max_duration_milliseconds:
        raise ValueError("Cleanup duration resource bound exceeded")
    frames = json.loads(runner.run("ffprobe", [*base, "-select_streams", "v:0", "-show_frames",
        "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", path]))["frames"]
    rate = Fraction(video["avg_frame_rate"])
    if rate <= 0 or len(frames) != declared_count:
        raise ValueError("Cleanup source exceeds frame bound or has no exact frame rate")
    times = tuple(int((Decimal(frame["best_effort_timestamp_time"]) * 1_000_000)
                     .to_integral_value(rounding=ROUND_HALF_UP)) for frame in frames)
    if not times or times[0] != 0 or any(abs(t - round(Fraction(i * 1_000_000, 1) / rate)) > 1
                                       for i, t in enumerate(times)):
        raise ValueError("Cleanup requires zero-origin constant-frame-rate video")
    signature = None
    if audios:
        audio = audios[0]
        signature = {key: audio[key] for key in ("codec_name", "sample_rate", "channels", "time_base",
            "start_pts", "duration_ts") if key in audio}
        if set(signature) != {"codec_name", "sample_rate", "channels", "time_base", "start_pts", "duration_ts"}:
            raise ValueError("Cleanup audio stream lacks exact timing")
        pcm_size = (int(audio["duration_ts"]) * Fraction(audio["time_base"])
                    * int(audio["sample_rate"]) * int(audio["channels"]) * 2)
        if pcm_size > runner.tools.max_audio_decoded_bytes:
            raise ValueError("Cleanup decoded-audio resource bound exceeded")
    measured = MeasuredVideoMetadata(container_name="mp4", codec_name=video["codec_name"],
        width=width, height=height, fps_numerator=rate.numerator, fps_denominator=rate.denominator,
        duration_milliseconds=duration_ms, frame_count=len(times),
        audio_stream_count=len(audios), size_bytes=len(raw), artifact_sha256=sha256(raw).hexdigest())
    return measured, times, signature


def _pcm_hash(runner, path, present):
    if not present:
        return None
    # Decoder performs no resampling or channel remapping. Packet copy is checked
    # by exact decoded samples as well as the stream's start/duration/time base.
    raw = runner.run("ffmpeg", ["-nostdin", "-v", "error", "-protocol_whitelist", "file", "-f", "mov",
        "-i", path, "-map", "0:a:0", "-vn", "-c:a", "pcm_s16le", "-f", "s16le", "pipe:1"])
    return sha256(raw).hexdigest()


def prepare_video_cleanup(*, source_bytes: bytes, plan, tools: VideoCleanupTools) -> PreparedVideoCleanup:
    """Prepare a same-duration derivative; all durable writes belong to caller."""
    plan = VideoCleanupPlan.model_validate(plan)
    if not source_bytes or len(source_bytes) > tools.max_source_bytes:
        raise ValueError("Cleanup source byte bound exceeded")
    if sha256(source_bytes).hexdigest() != plan.source_sha256:
        raise ValueError("Cleanup source identity differs from the explicit plan")
    runner = _LocalRunner(tools)
    with tempfile.TemporaryDirectory(prefix="ai-video-clean-plate-") as tmp:
        root = Path(tmp)
        source_path, output_path = root / "source.mp4", root / "cleaned.mp4"
        source_path.write_bytes(source_bytes)
        measured, source_times, audio_signature = _probe(runner, source_path, source_bytes)
        indices = [frame.frame_index for frame in plan.frames]
        plates = {patch.plate_frame for frame in plan.frames for patch in frame.patches}
        if max((*indices, *plates)) >= measured.frame_count:
            raise ValueError("Cleanup plan exceeds source frame range")
        source_frames, output_frames, decoded_frames = (root / name for name in ("source", "output", "decoded"))
        for directory in (source_frames, output_frames, decoded_frames):
            directory.mkdir()
        decode = ["-nostdin", "-v", "error", "-protocol_whitelist", "file", "-f", "mov",
                  "-i", source_path, "-map", "0:v:0", "-fps_mode", "passthrough", "-pix_fmt", "rgb24",
                  "-threads", "1", source_frames / "%06d.png"]
        runner.run("ffmpeg", decode)
        files = sorted(source_frames.glob("*.png"))
        if len(files) != measured.frame_count:
            raise ValueError("Cleanup decoder did not preserve the source frame count")
        plate_images = {}
        for index in plates:
            with Image.open(files[index]) as image:
                plate_images[index] = image.convert("RGB")
        by_index = {frame.frame_index: frame for frame in plan.frames}
        proofs = []
        for index, path in enumerate(files):
            if time.monotonic() >= runner.deadline:
                raise ValueError("Cleanup elapsed-time bound exhausted during pixel preparation")
            with Image.open(path) as image:
                source = image.convert("RGB")
            if index in by_index:
                output, proof = apply_clean_plate_frame(source, plate_images, by_index[index])
                values = asdict(proof) if is_dataclass(proof) else proof.model_dump(mode="python")
                proofs.append(CleanupFrameProof.model_validate(values))
            else:
                output = source
                digest = sha256(source.tobytes()).hexdigest()
                proofs.append(CleanupFrameProof(input_rgb_sha256=digest, output_rgb_sha256=digest,
                    effective_mask_sha256=sha256(bytes(measured.width * measured.height)).hexdigest(),
                    protected_rgb_sha256=sha256(source.tobytes() * 2).hexdigest(), changed_pixel_count=0))
            output.save(output_frames / path.name, format="PNG")
        # This encodes a prepared source, not a composition or a second timeline.
        rate = f"{measured.fps_numerator}/{measured.fps_denominator}"
        runner.run("ffmpeg", ["-nostdin", "-v", "error", "-framerate", rate, "-i", output_frames / "%06d.png",
            "-protocol_whitelist", "file", "-f", "mov", "-i", source_path,
            "-map", "0:v:0", "-map", "1:a:0?", "-c:v", "libx264rgb", "-crf", "0", "-preset", "veryfast",
            "-pix_fmt", "rgb24", "-threads", "1", "-c:a", "copy", "-map_metadata", "-1", output_path])
        output_bytes = output_path.read_bytes()
        out_measured, out_times, out_signature = _probe(runner, output_path, output_bytes)
        decode[decode.index(source_path)] = output_path
        decode[-1] = decoded_frames / "%06d.png"
        runner.run("ffmpeg", decode)
        decoded = sorted(decoded_frames.glob("*.png"))
        if len(decoded) != len(proofs):
            raise ValueError("Cleanup encoded output lost source frames")
        for path, proof in zip(decoded, proofs):
            with Image.open(path) as image:
                digest = sha256(image.convert("RGB").tobytes()).hexdigest()
            if digest != proof.output_rgb_sha256:
                raise ValueError("Cleanup lossless output differs from the protected pixel operation")
        values = dict(plan=plan, source=measured, output=out_measured,
            ffmpeg_sha256=runner.hashes["ffmpeg"], ffprobe_sha256=runner.hashes["ffprobe"],
            source_frame_times=source_times, output_frame_times=out_times,
            input_audio_sha256=_pcm_hash(runner, source_path, measured.audio_stream_count),
            output_audio_sha256=_pcm_hash(runner, output_path, measured.audio_stream_count),
            input_audio_signature=audio_signature, output_audio_signature=out_signature,
            frame_proofs=tuple(proofs))
        provisional = VideoCleanupReceipt.model_construct(**values, content_hash="0" * 64)
        receipt = VideoCleanupReceipt.model_validate({**provisional.model_dump(mode="python"),
            "content_hash": canonical_sha256(provisional)})
        runner.check_tools()
        return PreparedVideoCleanup(media_bytes=output_bytes, receipt=receipt)
