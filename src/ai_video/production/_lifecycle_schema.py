from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ImageRequestReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    attempt_id: str = Field(min_length=1)
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_kind: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    target_shot_id: str = Field(min_length=1)
    target_asset_role: str = Field(min_length=1)
    output_asset_id: str = Field(pattern=r"^image-[0-9a-f]{64}$")
    preview_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    authorization_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    policy_receipt_id: str = Field(min_length=1)
    usage_license: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_request_identity(self) -> "ImageRequestReceipt":
        if self.request_id != self.request_fingerprint:
            raise ValueError("image request ID must equal request fingerprint")
        if self.output_asset_id != f"image-{self.request_fingerprint}":
            raise ValueError("image output asset ID must match request fingerprint")
        return self


P5_AWARE_OPERATIONS: frozenset[str] = frozenset(
    {
        "bootstrap_dependency_graph",
        "commit_project_registry",
        "audio_import",
        "voice_generation",
        "image_generation",
        "render_state",
        "repair",
    }
)

_VOICE_FIELDS = (
    "voice_request",
    "voice_phase",
    "candidate_audio_asset_ids",
    "candidate_caption_asset_ids",
)
_IMAGE_FIELDS = ("image_request", "image_phase", "candidate_image_asset_ids")


def validate_provider_attempt(attempt: Any) -> None:
    operation = attempt.operation
    voice_fields_present = any(
        getattr(attempt, field) not in (None, ()) for field in _VOICE_FIELDS
    )
    image_fields_present = any(
        getattr(attempt, field) not in (None, ()) for field in _IMAGE_FIELDS
    )
    if operation != "voice_generation" and voice_fields_present:
        raise ValueError("non-voice operations cannot contain voice fields")
    if operation != "image_generation" and image_fields_present:
        raise ValueError("non-image operations cannot contain image fields")
    if operation not in {"voice_generation", "image_generation"} and (
        attempt.provider_request_id is not None
    ):
        raise ValueError(
            "non-provider operations cannot contain provider request identity"
        )
    if operation == "voice_generation":
        _validate_voice_attempt(attempt)
    if operation == "image_generation":
        _validate_image_attempt(attempt)


def _validate_voice_attempt(attempt: Any) -> None:
    if attempt.voice_request is None or attempt.voice_phase is None:
        raise ValueError("voice_generation attempts require voice request and phase")
    if attempt.voice_request.attempt_id != attempt.attempt_id:
        raise ValueError("voice attempt identity does not match request")
    all_phases = {
        "request",
        "submit_intent",
        "provider_call",
        "materialize",
        "probe",
        "align",
        "candidate",
        "activate",
    }
    allowed_phases = {
        "running": all_phases,
        "succeeded": {"activate"},
        "failed": all_phases,
        "interrupted": {"request", "materialize", "probe", "align", "candidate"},
        "outcome_unknown": all_phases - {"request"},
    }
    if attempt.voice_phase not in allowed_phases[attempt.status.value]:
        raise ValueError("voice attempt status and phase are inconsistent")
    if attempt.candidate_project not in (None, attempt.base_project):
        raise ValueError("voice candidate project identity does not match")
    if attempt.voice_phase in {"candidate", "activate"}:
        if attempt.candidate_registry is None or not attempt.candidate_audio_asset_ids:
            raise ValueError("voice candidate phase requires candidate audio bundle")
    elif (
        attempt.candidate_registry is not None
        or attempt.candidate_audio_asset_ids
        or attempt.candidate_caption_asset_ids
    ):
        raise ValueError("voice candidate bundle requires candidate phase")


def _validate_image_attempt(attempt: Any) -> None:
    if attempt.image_request is None or attempt.image_phase is None:
        raise ValueError("image_generation attempts require image request and phase")
    if attempt.image_request.attempt_id != attempt.attempt_id:
        raise ValueError("image attempt identity does not match request")
    if attempt.base_dependency_graph is None:
        raise ValueError("image_generation attempts require base dependency graph")
    all_phases = {
        "request",
        "submit_intent",
        "provider_call",
        "materialize",
        "validate",
        "candidate",
        "activate",
    }
    allowed_phases = {
        "running": all_phases,
        "succeeded": {"activate"},
        "failed": all_phases,
        "interrupted": {"request", "materialize", "validate", "candidate"},
        "outcome_unknown": all_phases - {"request"},
    }
    if attempt.image_phase not in allowed_phases[attempt.status.value]:
        raise ValueError("image attempt status and phase are inconsistent")
    candidate_bundle = (
        attempt.candidate_project,
        attempt.candidate_registry,
        attempt.candidate_dependency_graph,
        attempt.candidate_dependency_states_hash,
    )
    if attempt.image_phase in {"candidate", "activate"}:
        if not all(item is not None for item in candidate_bundle):
            raise ValueError("image candidate phase requires exact candidate bundle")
        if attempt.candidate_image_asset_ids != (
            attempt.image_request.output_asset_id,
        ):
            raise ValueError("image candidate asset ID must match request output")
    elif any(item is not None for item in candidate_bundle) or (
        attempt.candidate_image_asset_ids
    ):
        raise ValueError("image candidate bundle requires candidate or activate phase")


def prune_attempt_fields(data: dict[str, object], operation: str) -> None:
    if operation != "voice_generation":
        for field in _VOICE_FIELDS:
            data.pop(field, None)
    if operation != "image_generation":
        for field in _IMAGE_FIELDS:
            data.pop(field, None)
    if operation not in {"voice_generation", "image_generation"}:
        data.pop("provider_request_id", None)


def has_p6_state(manifest: Any) -> bool:
    top_level_state = manifest.active_qa_policy is not None or any(
        (
            manifest.active_review_receipts,
            manifest.review_states,
            manifest.active_approved_repair,
            manifest.repair_outcome_receipts,
            manifest.final_acceptance_state,
        )
    )
    attempt_state = any(
        attempt.operation in {"review", "repair"}
        or attempt.review_request is not None
        or attempt.review_phase is not None
        or attempt.approved_repair_receipt is not None
        for attempt in manifest.attempts
    )
    return top_level_state or attempt_state
