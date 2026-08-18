from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from pathlib import Path
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


class _PaidLifecycleModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _canonical_paid_path(value: Path, expected: Path, label: str) -> Path:
    if value.is_absolute() or ".." in value.parts or value != expected:
        raise ValueError(f"{label} path must be canonical")
    return value


class PaidProviderBudgetSnapshotPointer(_PaidLifecycleModel):
    path: Path
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "PaidProviderBudgetSnapshotPointer":
        _canonical_paid_path(
            self.path,
            Path(f"state/paid-provider/budgets/{self.content_hash}.json"),
            "paid Provider budget",
        )
        return self


class PaidProviderGateReceiptPointer(_PaidLifecycleModel):
    path: Path
    gate_receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "PaidProviderGateReceiptPointer":
        _canonical_paid_path(
            self.path,
            Path(f"state/paid-provider/gates/{self.gate_receipt_fingerprint}.json"),
            "paid Provider Gate receipt",
        )
        return self


class PaidProviderSubmitReceiptPointer(_PaidLifecycleModel):
    path: Path
    submit_receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "PaidProviderSubmitReceiptPointer":
        _canonical_paid_path(
            self.path,
            Path(f"state/paid-provider/submits/{self.submit_receipt_fingerprint}.json"),
            "paid Provider submit receipt",
        )
        return self


class PaidProviderAttemptPhase(str, Enum):
    SUBMIT_INTENT = "submit_intent"
    ACCEPTED = "accepted"
    KNOWN_NO_EFFECT = "known_no_effect"
    OUTCOME_UNKNOWN = "outcome_unknown"
    SETTLED = "settled"


class PaidProviderAttemptState(_PaidLifecycleModel):
    gate_receipt: PaidProviderGateReceiptPointer
    reservation_id: str = Field(min_length=1)
    phase: PaidProviderAttemptPhase
    submit_receipt: PaidProviderSubmitReceiptPointer | None = None

    @model_validator(mode="after")
    def _validate_phase_evidence(self) -> "PaidProviderAttemptState":
        if self.phase is PaidProviderAttemptPhase.SUBMIT_INTENT:
            if self.submit_receipt is not None:
                raise ValueError("submit intent cannot select a submit receipt")
        elif self.submit_receipt is None:
            raise ValueError("paid Provider terminal phase requires a submit receipt")
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


def reject_explicit_paid_provider_fields(value: object) -> object:
    if not isinstance(value, Mapping):
        return value
    manifest_version = value.get("schema_version", "2.0")
    has_paid_attempt = any(
        isinstance(attempt, Mapping) and "paid_provider_state" in attempt
        for attempt in value.get("attempts", ())
    )
    if manifest_version != "2.6" and (
        "active_paid_provider_budget" in value or has_paid_attempt
    ):
        raise ValueError(
            f"Production Manifest {manifest_version} cannot contain explicit paid Provider fields"
        )
    return value


def reject_explicit_p7_fields(value: object) -> object:
    if not isinstance(value, Mapping):
        return value
    manifest_version = value.get("schema_version", "2.0")
    if manifest_version in {"2.5", "2.6"}:
        return value
    image_fields = {"image_request", "image_phase", "candidate_image_asset_ids"}
    for attempt in value.get("attempts", ()):
        if isinstance(attempt, Mapping) and (
            attempt.get("operation") == "image_generation"
            or image_fields.intersection(attempt)
        ):
            raise ValueError(
                f"Production Manifest {manifest_version} cannot contain explicit P7 image fields"
            )
    return value


def validate_paid_provider_manifest(manifest: Any) -> None:
    paid_attempts = [
        attempt
        for attempt in manifest.attempts
        if attempt.paid_provider_state is not None
    ]
    if paid_attempts and manifest.active_paid_provider_budget is None:
        raise ValueError("paid Provider attempts require an active paid Provider budget")
    gate_owners = [
        attempt.paid_provider_state.gate_receipt.gate_receipt_fingerprint
        for attempt in paid_attempts
    ]
    submit_owners = [
        attempt.paid_provider_state.submit_receipt.submit_receipt_fingerprint
        for attempt in paid_attempts
        if attempt.paid_provider_state.submit_receipt is not None
    ]
    if len(gate_owners) != len(set(gate_owners)) or len(submit_owners) != len(
        set(submit_owners)
    ):
        raise ValueError("paid Provider receipt ownership must be unique")
