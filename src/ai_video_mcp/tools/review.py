from __future__ import annotations

import subprocess
import hashlib
import re
from pathlib import Path

from ai_video.production.models import (
    ReviewAttemptPhase,
    ReviewRequestPointer,
    StateCommitStatus,
    TechnicalReviewContext,
    VisualStrategy,
)
from ai_video.production.project import load_production_project, load_review_request
from ai_video_mcp.cache import AnalysisCache
from ai_video_mcp.config import ServerConfig
from ai_video_mcp.errors import McpError, McpErrorCode
from ai_video_mcp.tools.analyze import video_analyze
from ai_video_mcp.tools.probe import _validate_video


def _sample_frame_hashes(video_path: Path, *, sample_fps: float = 1.0) -> list[str]:
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(video_path),
        "-vf",
        f"fps={sample_fps},scale=32:32,format=gray",
        "-f",
        "framemd5",
        "-",
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise McpError(
            McpErrorCode.FFMPEG_FAILED,
            "Frame hash sampling failed",
            detail=(exc.stderr or exc.stdout or str(exc)).strip(),
        ) from exc

    hashes: list[str] = []
    for line in result.stdout.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",")]
        if parts:
            hashes.append(parts[-1])
    return hashes


def _sample_window_hashes(video_path: Path, start_frame: int, end_frame: int) -> list[str]:
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(video_path),
        "-vf", f"select='between(n,{start_frame},{end_frame - 1})',scale=32:32,format=gray",
        "-vsync", "0", "-f", "framemd5", "-",
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise McpError(McpErrorCode.FFMPEG_FAILED, "Frame window sampling failed") from exc
    return [
        line.split(",")[-1].strip()
        for line in result.stdout.splitlines()
        if line and not line.startswith("#")
    ]


def _technical_signal_measurements(video_path: Path) -> dict:
    black = subprocess.run(
        [
            "ffmpeg", "-v", "info", "-i", str(video_path), "-vf",
            "blackdetect=d=0.1:pix_th=0.10", "-an", "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    black_ranges = [
        {"start_seconds": float(start), "end_seconds": float(end)}
        for start, end in re.findall(
            r"black_start:([0-9.]+).*?black_end:([0-9.]+)", black.stderr
        )
    ]
    audio = subprocess.run(
        [
            "ffmpeg", "-v", "info", "-i", str(video_path), "-af",
            "silencedetect=noise=-60dB:d=0.1,volumedetect", "-vn", "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    silence_ranges = [
        {"start_seconds": float(start), "end_seconds": float(end)}
        for start, end in re.findall(
            r"silence_start: ([0-9.]+).*?silence_end: ([0-9.]+)",
            audio.stderr,
            flags=re.DOTALL,
        )
    ]
    peak = re.search(r"max_volume: (-?[0-9.]+) dB", audio.stderr)
    return {
        "black_ranges": black_ranges,
        "silence_ranges": silence_ranges,
        "audio_peak_millidb": (
            round(float(peak.group(1)) * 1000) if peak is not None else None
        ),
    }


def _make_issue(
    *,
    issue_id: str,
    severity: str,
    summary: str,
    evidence: dict,
    actions: list[dict],
) -> dict:
    return {
        "id": issue_id,
        "severity": severity,
        "summary": summary,
        "evidence": evidence,
        "suggested_actions": actions,
    }


def _review_issues(analysis: dict, quality_metrics: dict) -> list[dict]:
    probe = analysis["probe"]
    summary = analysis["analysis_summary"]
    width = probe["video_stream"]["width"]
    height = probe["video_stream"]["height"]
    fps = probe["video_stream"]["fps"]
    duration = probe["file"]["duration_seconds"]
    scene_count = summary["scene_count"]
    unique_frame_ratio = quality_metrics["unique_frame_ratio"]
    unique_frame_count = quality_metrics["unique_frame_count"]

    issues: list[dict] = []

    if width < 1024 or height < 576:
        issues.append(
            _make_issue(
                issue_id="low_resolution",
                severity="high" if width < 854 or height < 480 else "medium",
                summary="Rendered output resolution is below a strong review baseline for iteration videos.",
                evidence={
                    "width": width,
                    "height": height,
                    "recommended_minimum": "1024x576",
                },
                actions=[
                    {
                        "area": "workflow_and_project_defaults",
                        "summary": "Raise generation and normalization resolution.",
                        "file_hints": [
                            "configs/*.project.yaml",
                            "workflows/templates/*.json",
                            "src/ai_video/ffmpeg_tools.py",
                        ],
                    }
                ],
            )
        )

    if fps < 20:
        issues.append(
            _make_issue(
                issue_id="low_fps",
                severity="medium",
                summary="Frame rate is low enough to make motion look choppy during review.",
                evidence={
                    "fps": fps,
                    "recommended_minimum": 20,
                },
                actions=[
                    {
                        "area": "timing_and_export",
                        "summary": "Increase generated clip fps and ensure ffmpeg normalization keeps it.",
                        "file_hints": [
                            "configs/*.project.yaml",
                            "src/ai_video/ffmpeg_tools.py",
                            "src/ai_video/pipeline.py",
                        ],
                    }
                ],
            )
        )

    if unique_frame_ratio <= 0.5 or (duration >= 8 and scene_count <= 1 and unique_frame_count <= 2):
        issues.append(
            _make_issue(
                issue_id="static_visuals",
                severity="high",
                summary="Sampled frames are overly repetitive, suggesting weak motion or a nearly static shot plan.",
                evidence={
                    "scene_count": scene_count,
                    "sampled_frame_count": quality_metrics["sampled_frame_count"],
                    "unique_frame_count": unique_frame_count,
                    "unique_frame_ratio": unique_frame_ratio,
                },
                actions=[
                    {
                        "area": "shot_prompt_and_motion_nodes",
                        "summary": "Strengthen motion cues in shot prompts and inspect workflow nodes that control motion strength or conditioning carry-over.",
                        "file_hints": [
                            "configs/*.shots.yaml",
                            "workflows/templates/*.json",
                            "workflows/bindings/*.yaml",
                        ],
                    }
                ],
            )
        )

    return issues


def video_review(
    video_path: str,
    config: ServerConfig,
    cache: AnalysisCache,
    *,
    frame_interval: float | None = None,
    max_frames: int | None = None,
    scene_threshold: float | None = None,
    transcribe_audio: bool = False,
    production_context: dict | None = None,
    production_project_path: str | None = None,
    production_review_request: dict | None = None,
) -> dict:
    p = _validate_video(video_path, config)

    production_inputs = (
        production_context,
        production_project_path,
        production_review_request,
    )
    if any(item is not None for item in production_inputs):
        if any(item is None for item in production_inputs):
            raise McpError(
                McpErrorCode.INVALID_PARAMETER,
                "Production review requires verified project and durable request",
            )
        bundle = load_production_project(production_project_path)
        request_pointer = ReviewRequestPointer.model_validate(
            production_review_request
        )
        if not any(
            item.operation == "review"
            and item.status is StateCommitStatus.RUNNING
            and item.review_phase is ReviewAttemptPhase.EVIDENCE
            and item.review_request == request_pointer
            for item in bundle.manifest.attempts
        ):
            raise McpError(
                McpErrorCode.INVALID_PARAMETER,
                "Production ReviewRequest is not active",
            )
        durable_request = load_review_request(bundle.root, request_pointer)
        try:
            context = TechnicalReviewContext.model_validate(production_context)
        except ValueError as exc:
            raise McpError(
                McpErrorCode.INVALID_PARAMETER,
                "Production technical review context is invalid",
                detail=str(exc),
            ) from exc
        if context != durable_request.technical_context:
            raise McpError(
                McpErrorCode.INVALID_PARAMETER,
                "Production technical context does not match ReviewRequest",
            )
        actual_hash = hashlib.sha256(p.read_bytes()).hexdigest()
        expected_hash = context.render_output_sha256
        if actual_hash != expected_hash:
            raise McpError(
                McpErrorCode.INVALID_PARAMETER,
                "Production render output hash does not match review context",
            )
        window_measurements: list[dict] = []
        frame_hashes: list[str] = []
        for window in context.windows:
            hashes = _sample_window_hashes(
                p, window.start_frame, window.end_frame_exclusive
            )
            frame_hashes.extend(hashes)
            unique = len(set(hashes))
            count = len(hashes)
            status = "measured"
            if window.visual_strategy in {
                VisualStrategy.IMAGE_MOTION,
                VisualStrategy.MOTION_GRAPHICS,
            }:
                status = "not_evaluated"
            window_measurements.append(
                {
                    "shot_id": window.shot_id,
                    "visual_strategy": window.visual_strategy.value,
                    "start_frame": window.start_frame,
                    "end_frame_exclusive": window.end_frame_exclusive,
                    "sampled_frame_count": count,
                    "unique_frame_count": unique,
                    "unique_frame_ratio": round(unique / count, 3) if count else 0.0,
                    "status": status,
                }
            )
        unique_count = len(set(frame_hashes))
        sample_count = len(frame_hashes)
        ratio = round(unique_count / sample_count, 3) if sample_count else 0.0
        return {
            "mode": "production_evidence",
            "video_path": str(p),
            "render_output_sha256": actual_hash,
            "timeline_fingerprint": context.timeline_fingerprint,
            "measurement_contract_version": context.measurement_contract_version,
            "windows": window_measurements,
            "measurements": {
                "coverage_complete": True,
                "sampled_frame_count": sample_count,
                "unique_frame_count": unique_count,
                "unique_frame_ratio": ratio,
                "expects_audio": any(item.expects_audio for item in context.windows),
                "windows": window_measurements,
                **_technical_signal_measurements(p),
            },
            # Production thresholds and verdicts belong to production.review.
            "issues": [],
        }

    analysis = video_analyze(
        video_path,
        config,
        cache,
        extract_frames=True,
        frame_interval=frame_interval,
        max_frames=max_frames,
        transcribe_audio=transcribe_audio,
        detect_scenes=True,
        scene_threshold=scene_threshold,
    )

    frame_hashes = _sample_frame_hashes(p)
    unique_frame_count = len(set(frame_hashes))
    sampled_frame_count = len(frame_hashes)
    unique_frame_ratio = round(unique_frame_count / sampled_frame_count, 3) if sampled_frame_count else 0.0

    quality_metrics = {
        "duration_seconds": analysis["probe"]["file"]["duration_seconds"],
        "fps": analysis["probe"]["video_stream"]["fps"],
        "resolution": analysis["analysis_summary"]["resolution"],
        "scene_count": analysis["analysis_summary"]["scene_count"],
        "sampled_frame_count": sampled_frame_count,
        "unique_frame_count": unique_frame_count,
        "unique_frame_ratio": unique_frame_ratio,
        "has_audio": analysis["analysis_summary"]["has_audio"],
        "estimated_speaking_duration_seconds": analysis["analysis_summary"]["estimated_speaking_duration_seconds"],
    }
    issues = _review_issues(analysis, quality_metrics)

    return {
        "video_path": str(p),
        "analysis_summary": analysis["analysis_summary"],
        "quality_metrics": quality_metrics,
        "issues": issues,
    }
