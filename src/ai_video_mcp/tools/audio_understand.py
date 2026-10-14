"""Exact project media -> preview or an injected, authorized audio analyzer."""
from __future__ import annotations

import importlib
import json
import math
import re
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ai_video.production.paths import _read_regular_file_nofollow
from ai_video_mcp.audio_understanding import (
    AudioUnderstandingError, GeminiAudioAnalyzer, prepare_audio_request,
)
from ai_video_mcp.config import ServerConfig


@dataclass(frozen=True)
class AudioUnderstandingRuntime:
    """Trusted operator owns live qualification, durable authorization and quota.

    A JSON flag is not a permit. The supplier must return a real one-use
    capability with validate/consume methods for this exact preview.
    """
    analyzer: GeminiAudioAnalyzer
    permit_supplier: Callable[[dict], object]


def _error(code, message, outcome="EVIDENCE_GAP"):
    return AudioUnderstandingError(code, outcome, message)


def _media_root(config):
    if config.audio_media_root is not None:
        root = Path(config.audio_media_root)
        if not root.is_absolute():
            raise _error("invalid_media_root", "Audio media root must be an absolute operator setting.")
    else:
        root = Path(__file__).resolve().parents[3]
        if not (root / "pyproject.toml").is_file():
            raise _error("media_root_required", "Configure the project audio media root first.")
    return root.resolve(strict=True)


def _read_source(path, root, expected_sha256):
    if (not isinstance(expected_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None):
        raise _error("invalid_source_identity", "Expected SHA-256 must identify the exact selected media.")
    path = Path(path)
    if not path.is_absolute() or path.suffix.lower() not in {".mp4", ".wav"}:
        raise _error("invalid_media", "Select an absolute project MP4 or PCM WAV path.")
    try:
        path.relative_to(root)
        info = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or info.st_size > 128 * 1024 * 1024:
            raise ValueError
        source = _read_regular_file_nofollow(path, contained_by=root)
    except (OSError, ValueError):
        raise _error("invalid_media", "Audio source is not a bounded regular file inside the project media root.") from None
    if source.file_sha256 != expected_sha256:
        raise _error("source_changed", "The selected media differs from its expected SHA-256.")
    return source


def _audio_bytes(source, suffix):
    if suffix == ".wav":
        return source.data, 0.0
    with tempfile.TemporaryDirectory(prefix="ai_video_audio_analysis_") as temporary:
        original = Path(temporary) / "source.mp4"
        audio = Path(temporary) / "analysis.wav"
        original.write_bytes(source.data)
        try:
            # Restrict both subprocesses before opening input: a .mp4 suffix
            # must not enable HLS/concat or MOV external track references.
            input_options = ["-protocol_whitelist", "file", "-f", "mov",
                "-enable_drefs", "0", "-use_absolute_path", "0"]
            probe = subprocess.run(["ffprobe", "-v", "error", *input_options,
                "-show_streams", "-show_format", "-of", "json", str(original)],
                check=True, capture_output=True, timeout=45)
            metadata = json.loads(probe.stdout)
            streams = metadata.get("streams", [])
            audio_stream = next(s for s in streams if s.get("codec_type") == "audio")
            video_stream = next(s for s in streams if s.get("codec_type") == "video")
            duration = float(metadata["format"]["duration"])
            if not math.isfinite(duration) or not 0 < duration <= 120:
                raise ValueError
            offset = float(audio_stream.get("start_time", 0)) - float(video_stream.get("start_time", 0))
            if not math.isfinite(offset) or offset < 0:
                raise ValueError
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", *input_options, "-i", str(original),
                "-map", "0:a:0", "-vn", "-c:a", "pcm_s16le", str(audio)],
                check=True, capture_output=True, timeout=45)
            data = audio.read_bytes()
        except Exception:
            raise _error("audio_extraction_failed", "A complete bounded source audio track could not be decoded.") from None
        return data, offset


def _runtime(config):
    reference = config.audio_runtime_factory
    if (not isinstance(reference, str)
            or re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*", reference) is None):
        raise _error("runtime_required", "EVIDENCE_REPAIR_FIRST: configure a qualified audio operator runtime; no POST was made.",
                     "KNOWN_NO_EFFECT")
    module, name = reference.split(":")
    try:
        runtime = getattr(importlib.import_module(module), name)()
    except Exception:
        raise _error("runtime_unavailable", "The configured audio operator runtime is unavailable.", "KNOWN_NO_EFFECT") from None
    if (not isinstance(runtime, AudioUnderstandingRuntime)
            or not isinstance(runtime.analyzer, GeminiAudioAnalyzer)
            or not callable(runtime.permit_supplier)):
        raise _error("runtime_invalid", "The audio operator must inject an analyzer and real one-use permit supplier.")
    return runtime


def audio_understand(media_path: str, config: ServerConfig, *, expected_sha256: str,
                     execute: bool = False) -> dict:
    """Default preview has no runtime import, credential lookup, upload or POST."""
    if type(execute) is not bool:
        raise _error("invalid_execution_mode", "Audio execution must be an explicit boolean.")
    try:
        root = _media_root(config)
        source = _read_source(media_path, root, expected_sha256)
        audio, offset = _audio_bytes(source, Path(media_path).suffix.lower())
        prepared = prepare_audio_request(audio_bytes=audio, source_sha256=source.file_sha256,
            source_size_bytes=len(source.data), model_id=config.audio_model_id, audio_start_seconds=offset)
        if not execute:
            result = {"schema_version": "audio-understanding-preview/1", "preview": prepared.preview(),
                "network_calls": 0, "production_acceptance": "NOT_EVALUATED"}
        else:
            runtime = _runtime(config)
            try:
                permit = runtime.permit_supplier(prepared.preview())
            except Exception:
                raise _error("permit_unavailable", "The authorized audio permit is unavailable.", "KNOWN_NO_EFFECT") from None
            result = runtime.analyzer.analyze(prepared, permit=permit)
        after = _read_source(media_path, root, expected_sha256)
        if after.data != source.data:
            raise _error("source_changed", "Media changed during audio analysis; do not use this evidence.")
        return {**result, "media_path": str(Path(media_path).absolute()),
                "analysis_audio_derivation": "exact_pcm_wav" if Path(media_path).suffix.lower() == ".wav"
                else "full_source_track_pcm_derivative", "human_acceptance": "NOT_EVALUATED"}
    except AudioUnderstandingError:
        raise
    except Exception:
        raise _error("audio_analysis_failed", "Audio analysis could not produce usable exact-media evidence.") from None
