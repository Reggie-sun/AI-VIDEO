from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    CONFIG_INVALID = "config_invalid"
    WORKFLOW_INVALID = "workflow_invalid"
    BINDING_INVALID = "binding_invalid"
    COMFY_UNAVAILABLE = "comfy_unavailable"
    COMFY_SUBMISSION_FAILED = "comfy_submission_failed"
    COMFY_QUEUE_TIMEOUT = "comfy_queue_timeout"
    COMFY_JOB_TIMEOUT = "comfy_job_timeout"
    COMFY_JOB_FAILED = "comfy_job_failed"
    COMFY_OUTPUT_MISSING = "comfy_output_missing"
    OUTPUT_INVALID = "output_invalid"
    FFMPEG_FAILED = "ffmpeg_failed"
    MANIFEST_INVALID = "manifest_invalid"
    PRODUCTION_PROJECT_INVALID = "production_project_invalid"
    ASSET_REGISTRY_INVALID = "asset_registry_invalid"
    PRODUCTION_STATE_INVALID = "production_state_invalid"
    PRODUCTION_STATE_BUSY = "production_state_busy"
    PRODUCTION_STATE_COMMIT_FAILED = "production_state_commit_failed"
    PRODUCTION_STATE_RECOVERY_FAILED = "production_state_recovery_failed"
    PRODUCTION_STATE_OUTCOME_UNKNOWN = "production_state_outcome_unknown"
    PRODUCTION_STATE_UNSUPPORTED = "production_state_unsupported"
    COMPOSITION_INVALID = "composition_invalid"
    RENDERER_UNAVAILABLE = "renderer_unavailable"
    RENDERER_SOURCE_INVALID = "renderer_source_invalid"
    RENDER_FAILED = "render_failed"
    AUDIO_ASSET_INVALID = "audio_asset_invalid"
    AUDIO_PROBE_FAILED = "audio_probe_failed"
    AUDIO_TIMELINE_INVALID = "audio_timeline_invalid"
    CAPTION_ALIGNMENT_INVALID = "caption_alignment_invalid"
    CAPTION_TRACK_INVALID = "caption_track_invalid"
    VOICE_REQUEST_INVALID = "voice_request_invalid"
    VOICE_BUDGET_REJECTED = "voice_budget_rejected"
    VOICE_EGRESS_NOT_AUTHORIZED = "voice_egress_not_authorized"
    VOICE_PROVIDER_FAILED = "voice_provider_failed"
    VOICE_PROVIDER_OUTCOME_UNKNOWN = "voice_provider_outcome_unknown"
    DISK_SPACE_LOW = "disk_space_low"
    DEPENDENCY_GRAPH_INVALID = "dependency_graph_invalid"
    DEPENDENCY_RESOLUTION_INVALID = "dependency_resolution_invalid"
    REVIEW_EVIDENCE_INVALID = "review_evidence_invalid"
    REVIEW_NOT_CURRENT = "review_not_current"
    REPAIR_AUTHORIZATION_REQUIRED = "repair_authorization_required"
    REPAIR_SCOPE_INVALID = "repair_scope_invalid"
    FINAL_ACCEPTANCE_INVALID = "final_acceptance_invalid"


@dataclass
class AiVideoError(Exception):
    code: ErrorCode
    user_message: str
    technical_detail: Optional[str] = None
    retryable: bool = False
    cause: Optional[BaseException] = None

    def __str__(self) -> str:
        return self.user_message


def config_error(code: ErrorCode, message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, technical_detail=detail, retryable=False)


def retryable_error(
    code: ErrorCode,
    message: str,
    detail: str | None = None,
    cause: BaseException | None = None,
) -> AiVideoError:
    return AiVideoError(
        code=code,
        user_message=message,
        technical_detail=detail,
        retryable=True,
        cause=cause,
    )
