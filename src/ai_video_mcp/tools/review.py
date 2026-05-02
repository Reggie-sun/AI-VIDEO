from __future__ import annotations

import subprocess
from pathlib import Path

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
) -> dict:
    p = _validate_video(video_path, config)

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
