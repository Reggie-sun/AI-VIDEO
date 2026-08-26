"""Fixed ffmpeg signalstats evidence for full-source M0 motion tails."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.models import AssetRecord, AssetType, ToolIdentity
from ai_video.production.paths import (
    _open_regular_file_nofollow,
    canonical_video_asset_path,
)


_SHA256 = r"^[0-9a-f]{64}$"
_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class _AnalysisStrictModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class FullSourceMotionSpanMeasurement(_AnalysisStrictModel):
    """One quantitative ffmpeg signalstats span over exact source frames."""

    span_id: str = Field(pattern=_SAFE_ID)
    start_frame_index: int = Field(strict=True, ge=0)
    end_frame_index: int = Field(strict=True, ge=0)
    sample_count: int = Field(strict=True, ge=2)
    nonzero_ydif_count: int = Field(strict=True, ge=1)
    longest_nonzero_ydif_run: int = Field(strict=True, ge=2)
    mean_ydif_millionths: int = Field(strict=True, gt=0)
    measurement_output_sha256: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_span(self) -> "FullSourceMotionSpanMeasurement":
        if (
            self.end_frame_index <= self.start_frame_index
            or self.sample_count
            != self.end_frame_index - self.start_frame_index + 1
            or self.nonzero_ydif_count > self.sample_count
            or self.longest_nonzero_ydif_run > self.nonzero_ydif_count
        ):
            raise ValueError("motion span measurements are inconsistent")
        return self


class FullSourceMotionAnalysisReceipt(_AnalysisStrictModel):
    """Hash-sealed quantitative evidence produced for one exact source MP4."""

    source_video_asset_id: str = Field(pattern=_SAFE_ID)
    source_video_sha256: str = Field(pattern=_SHA256)
    source_frame_count: int = Field(strict=True, ge=3)
    analyzer: ToolIdentity
    analyzer_executable_sha256: str = Field(pattern=_SHA256)
    analyzer_version_output_sha256: str = Field(pattern=_SHA256)
    analyzer_contract_version: Literal["ffmpeg-signalstats-ydif-v2"]
    canonical_arguments: tuple[str, ...] = Field(min_length=1)
    spans: tuple[FullSourceMotionSpanMeasurement, ...] = Field(min_length=2)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_analysis(self) -> "FullSourceMotionAnalysisReceipt":
        if self.analyzer.name != "ffmpeg" or not self.analyzer.version.strip():
            raise ValueError("motion analysis requires an exact ffmpeg identity")
        if len({item.span_id for item in self.spans}) != len(self.spans):
            raise ValueError("motion analysis span IDs must be distinct")
        previous_end = -1
        for span in self.spans:
            if (
                span.start_frame_index <= previous_end
                or span.end_frame_index >= self.source_frame_count
            ):
                raise ValueError("motion analysis spans must be ordered and in range")
            previous_end = span.end_frame_index
        if self.canonical_arguments != _canonical_analysis_arguments(
            self.source_frame_count
        ):
            raise ValueError("motion analysis arguments are not the fixed contract")
        payload = self.model_dump(mode="json", exclude={"content_hash"})
        if self.content_hash != _seal_analysis(payload):
            raise ValueError("full-source motion analysis hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "FullSourceMotionAnalysisReceipt":
        data = dict(values)
        data.pop("content_hash", None)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = _seal_analysis(
            provisional.model_dump(
                mode="json", exclude={"content_hash"}, warnings=False
            )
        )
        return cls.model_validate(data)


def _seal_analysis(payload: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(
            {"schema": "ai-video-full-source-motion-analysis/1", **payload},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _analysis_spans(frame_count: int) -> tuple[tuple[int, int], ...]:
    midpoint = frame_count // 2
    if midpoint < 2 or frame_count - midpoint < 2:
        raise _invalid("Full-source motion analysis requires two multi-frame spans.")
    return ((0, midpoint - 1), (midpoint, frame_count - 1))


def _span_filter(start_frame: int, end_frame: int) -> str:
    return (
        f"trim=start_frame={start_frame}:end_frame={end_frame + 1},"
        "signalstats,metadata=print:key=lavfi.signalstats.YDIF"
    )


def _canonical_analysis_arguments(frame_count: int) -> tuple[str, ...]:
    common = ("-nostdin", "-hide_banner", "-loglevel", "info", "-i", "{SOURCE}")
    suffix = ("-an", "-f", "null", "-")
    values: list[str] = []
    for index, (start_frame, end_frame) in enumerate(_analysis_spans(frame_count)):
        if index:
            values.append("{NEXT_SPAN}")
        values.extend((*common, "-vf", _span_filter(start_frame, end_frame), *suffix))
    return tuple(values)


def _fd_sha256(descriptor: int) -> str:
    digest = hashlib.sha256()
    offset = 0
    while chunk := os.pread(descriptor, 1024 * 1024, offset):
        digest.update(chunk)
        offset += len(chunk)
    return digest.hexdigest()


def _longest_true_run(values: tuple[bool, ...]) -> int:
    longest = current = 0
    for value in values:
        current = current + 1 if value else 0
        longest = max(longest, current)
    return longest


def _measure_span(
    *,
    ffmpeg_descriptor: int,
    source_descriptor: int,
    start_frame: int,
    end_frame: int,
) -> FullSourceMotionSpanMeasurement:
    arguments = (
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "info",
        "-i",
        f"/proc/self/fd/{source_descriptor}",
        "-vf",
        _span_filter(start_frame, end_frame),
        "-an",
        "-f",
        "null",
        "-",
    )
    try:
        completed = subprocess.run(
            (f"/proc/self/fd/{ffmpeg_descriptor}", *arguments),
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
            pass_fds=(ffmpeg_descriptor, source_descriptor),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise _invalid("Full-source motion analyzer failed.", str(exc)) from exc
    values = re.findall(
        r"lavfi\.signalstats\.YDIF=([0-9]+(?:\.[0-9]+)?)",
        f"{completed.stdout}\n{completed.stderr}",
    )
    expected = end_frame - start_frame + 1
    if len(values) != expected:
        raise _invalid(
            "Full-source motion analyzer returned an unexpected sample count.",
            f"expected={expected} actual={len(values)}",
        )
    decimals = tuple(Decimal(value) for value in values)
    nonzero = tuple(value > 0 for value in decimals)
    mean = sum(decimals, Decimal(0)) / Decimal(len(decimals))
    canonical_output = "\n".join(values).encode("ascii") + b"\n"
    return FullSourceMotionSpanMeasurement(
        span_id=f"frames-{start_frame}-{end_frame}",
        start_frame_index=start_frame,
        end_frame_index=end_frame,
        sample_count=len(values),
        nonzero_ydif_count=sum(nonzero),
        longest_nonzero_ydif_run=_longest_true_run(nonzero),
        mean_ydif_millionths=int(
            (mean * Decimal(1_000_000)).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        ),
        measurement_output_sha256=hashlib.sha256(canonical_output).hexdigest(),
    )


def analyze_full_source_motion(
    project_root: str | Path,
    source_asset: AssetRecord,
    *,
    ffmpeg_executable: str | Path | None = None,
) -> FullSourceMotionAnalysisReceipt:
    """Run the fixed signalstats contract over exact registered source bytes."""

    root = Path(project_root).resolve(strict=True)
    metadata = source_asset.video_metadata
    if (
        source_asset.asset_type is not AssetType.VIDEO
        or metadata is None
        or source_asset.artifact_path != canonical_video_asset_path(source_asset.sha256)
    ):
        raise _invalid("Full-source motion analyzer requires a canonical video asset.")
    source_path = root / source_asset.artifact_path
    candidate = (
        Path(ffmpeg_executable)
        if ffmpeg_executable is not None
        else Path(shutil.which("ffmpeg") or "")
    )
    try:
        selected = candidate.resolve(strict=True)
    except OSError as exc:
        raise _invalid("Full-source motion analyzer executable is unavailable.") from exc
    if not selected.is_absolute() or not selected.is_file():
        raise _invalid("Full-source motion analyzer executable is unavailable.")
    try:
        with _open_regular_file_nofollow(
            source_path, contained_by=root / "assets"
        ) as (source_descriptor, source_opened), _open_regular_file_nofollow(
            selected, contained_by=selected.parent
        ) as (ffmpeg_descriptor, ffmpeg_opened):
            source_sha256 = _fd_sha256(source_descriptor)
            ffmpeg_sha256 = _fd_sha256(ffmpeg_descriptor)
            if (
                source_sha256 != source_asset.sha256
                or source_opened.st_size != source_asset.size_bytes
            ):
                raise _invalid("Full-source motion analyzer input bytes are not exact.")
            version = subprocess.run(
                (f"/proc/self/fd/{ffmpeg_descriptor}", "-version"),
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
                pass_fds=(ffmpeg_descriptor,),
            )
            spans = tuple(
                _measure_span(
                    ffmpeg_descriptor=ffmpeg_descriptor,
                    source_descriptor=source_descriptor,
                    start_frame=start,
                    end_frame=end,
                )
                for start, end in _analysis_spans(metadata.frame_count)
            )
            if (
                _fd_sha256(source_descriptor) != source_sha256
                or _fd_sha256(ffmpeg_descriptor) != ffmpeg_sha256
                or os.fstat(source_descriptor).st_size != source_opened.st_size
                or os.fstat(ffmpeg_descriptor).st_size != ffmpeg_opened.st_size
            ):
                raise _invalid("Full-source motion analyzer bytes changed during analysis.")
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise _invalid("Full-source motion analyzer identity failed.", str(exc)) from exc
    version_line = version.stdout.splitlines()[0] if version.stdout else ""
    if not version_line.startswith("ffmpeg version "):
        raise _invalid("Full-source motion analyzer identity is not ffmpeg.")
    return FullSourceMotionAnalysisReceipt.create(
        source_video_asset_id=source_asset.asset_id,
        source_video_sha256=source_asset.sha256,
        source_frame_count=metadata.frame_count,
        analyzer=ToolIdentity(name="ffmpeg", version=version_line),
        analyzer_executable_sha256=ffmpeg_sha256,
        analyzer_version_output_sha256=hashlib.sha256(
            version.stdout.encode("utf-8")
        ).hexdigest(),
        analyzer_contract_version="ffmpeg-signalstats-ydif-v2",
        canonical_arguments=_canonical_analysis_arguments(metadata.frame_count),
        spans=spans,
    )


__all__ = [
    "FullSourceMotionAnalysisReceipt",
    "FullSourceMotionSpanMeasurement",
    "analyze_full_source_motion",
]
