"""Offline execution-stack seal for the Shot Continuity upstream source lane."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production import comfy_video
from ai_video.production.comfy_video import (
    LocalVideoQualityExecutionProfile,
    load_local_video_execution_profile,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.video_execution_stack import (
    ExecutionStackMaterialization,
    GenerationExecutionStackIdentity,
    RuntimeSeal,
    StackComponentIdentity,
)


SOURCE_PROFILE_PATH = Path("workflows/profiles/minimax_h3_fl2va_quality.json")
_COMPONENT_IDS = ("pruned-fl2va", "qwen-clip", "video-vae", "audio-vae")


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


@dataclass(frozen=True)
class ShotContinuitySourceExecutionSources:
    profile: LocalVideoQualityExecutionProfile
    initial_stack: GenerationExecutionStackIdentity
    materialized_stack: GenerationExecutionStackIdentity
    materialization: ExecutionStackMaterialization


def _profile_source_bundle(profile_bytes: bytes, binding_bytes: bytes) -> bytes:
    return json.dumps(
        {
            "binding_bytes_base64": base64.b64encode(binding_bytes).decode("ascii"),
            "profile_bytes_base64": base64.b64encode(profile_bytes).decode("ascii"),
            "schema_version": "1",
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _read_exact(root: Path, relative: Path, expected_hash: str, label: str) -> bytes:
    try:
        snapshot = _read_regular_file_nofollow(root / relative, contained_by=root)
    except (OSError, ValueError) as exc:
        raise _invalid(f"Shot Continuity source {label} could not be reopened.", str(exc)) from exc
    if snapshot.file_sha256 != expected_hash:
        raise _invalid(f"Shot Continuity source {label} hash does not match.")
    return snapshot.data


def load_shot_continuity_source_execution_sources(
    *,
    artifact_root: str | Path,
    profile_path: str | Path = SOURCE_PROFILE_PATH,
) -> ShotContinuitySourceExecutionSources:
    """Seal the existing local FL2VA quality lane without any runtime effect."""

    root = Path(artifact_root).resolve(strict=True)
    requested_profile = Path(profile_path)
    if not requested_profile.is_absolute():
        requested_profile = root / requested_profile
    try:
        profile_snapshot = _read_regular_file_nofollow(
            requested_profile.resolve(strict=True),
            contained_by=root,
        )
        profile = load_local_video_execution_profile(
            requested_profile,
            artifact_root=root,
        )
        if not isinstance(profile, LocalVideoQualityExecutionProfile):
            raise ValueError("source profile must be the quality FL2VA lane")
        workflow_bytes = _read_exact(
            root,
            profile.workflow_path,
            profile.workflow_sha256,
            "workflow",
        )
        binding_bytes = _read_exact(
            root,
            profile.binding_path,
            profile.binding_sha256,
            "binding",
        )
        compiler_snapshot = _read_regular_file_nofollow(
            Path(comfy_video.__file__).resolve(strict=True),
            contained_by=root,
        )
    except (OSError, ValueError) as exc:
        if isinstance(exc, AiVideoError):
            raise
        raise _invalid("Shot Continuity source execution profile is invalid.", str(exc)) from exc

    if (
        profile.lane_id != "minimax_h3_fl2va_quality_local"
        or profile.loopback_endpoints != ("http://127.0.0.1:8188",)
        or not profile.optional_last_frame_supported
        or profile.optional_lora_enabled
        or profile.remote_refiner_enabled
        or profile.cloud_fallback_enabled
        or profile.max_width < 1344
        or profile.max_height < 768
        or profile.min_frame_count > 124
        or profile.max_frame_count < 124
        or 124 % profile.frame_grid_step != profile.frame_grid_remainder
        or profile.fps != 24
        or profile.sampler != "res_multistep"
        or profile.scheduler != "simple"
        or profile.steps != 20
        or profile.output_container != "mp4"
        or profile.output_crf != 17
        or not profile.native_audio_required
    ):
        raise _invalid("Shot Continuity source profile does not match the frozen local lane.")

    materialization = ExecutionStackMaterialization.from_bytes(
        candidate_label="source",
        profile_bytes=_profile_source_bundle(profile_snapshot.data, binding_bytes),
        compiler_bytes=compiler_snapshot.data,
        workflow_bytes=workflow_bytes,
    )
    initial_stack = GenerationExecutionStackIdentity.create(
        materialization_status="unmaterialized",
        candidate_id="minimax-h3-fl2va-rainy-station-source-v1",
        contract_version="1",
        provider_kind="minimax_h3_fl2va",
        deployment_identity="loopback-127.0.0.1-8188",
        model_id="minimax-h3-fl2va",
        capability_id="minimax-h3-fl2va-local-v1",
        profile_hash="none",
        compiler_hash="none",
        workflow_hash="none",
        components=tuple(
            StackComponentIdentity(
                ordinal=ordinal,
                kind="checkpoint" if ordinal == 0 else "artifact",
                component_id=component_id,
                content_hash=component.sha256,
            )
            for ordinal, (component_id, component) in enumerate(
                zip(_COMPONENT_IDS, profile.components, strict=True)
            )
        ),
        sampler_identity=profile.sampler,
        scheduler_identity=profile.scheduler,
        runtime_seals=(
            RuntimeSeal(
                name="comfyui",
                version=profile.comfyui_commit,
                content_hash=canonical_sha256({"commit": profile.comfyui_commit}),
            ),
        ),
        output_contract_hash=canonical_sha256(
            {
                "width": 1344,
                "height": 768,
                "frames": 124,
                "fps": 24,
                "container": "mp4",
                "crf": 17,
                "native_audio": True,
            }
        ),
    )
    return ShotContinuitySourceExecutionSources(
        profile=profile,
        initial_stack=initial_stack,
        materialized_stack=initial_stack.materialize(materialization),
        materialization=materialization,
    )


def validate_shot_continuity_source_stack(
    sources: ShotContinuitySourceExecutionSources,
    stack: GenerationExecutionStackIdentity,
) -> None:
    if stack not in (sources.initial_stack, sources.materialized_stack):
        raise _invalid("Shot Continuity source stack does not match its exact execution sources.")


__all__ = [
    "SOURCE_PROFILE_PATH",
    "ShotContinuitySourceExecutionSources",
    "load_shot_continuity_source_execution_sources",
    "validate_shot_continuity_source_stack",
]
