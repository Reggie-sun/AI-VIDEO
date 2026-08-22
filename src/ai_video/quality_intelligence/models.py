"""Strict immutable models for QualityExperienceRecord v1 passive capture."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from enum import Enum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
    model_validator,
)


_HEX64 = r"^[0-9a-f]{64}$"
_SAFE_ID = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$"
_COMMIT = r"^[0-9a-f]{40,64}$"
_UTC_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)
_DENIED_FREE_TEXT = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"https?://",
        r"\bauthorization\s*:",
        r"\bcookie\s*:",
        r"\b(?:api[_-]?key|secret|token|password)\s*=",
        r"\bAKIA[0-9A-Z]{16}\b",
        r"\[(?:prompt|response)\s+begin\]",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        r"(?:^|\s)/(?:home|Users|private|var|tmp|etc)/",
        r"\b[A-Z]:\\(?:Users|Documents|AppData)\\",
    )
)


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )


class RecordKind(str, Enum):
    PROSPECTIVE_Q0_ATTEMPT = "prospective_q0_attempt"


class AttemptKind(str, Enum):
    INITIAL = "initial"
    RETRY = "retry"
    REPAIR = "repair"
    COMPARISON = "comparison"


class CanonicalRuntimeBoundary(str, Enum):
    PRODUCTION_MANIFEST = "production_manifest"
    LAB_ONLY = "lab_only"


class EvidenceState(str, Enum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    INCOMPLETE = "incomplete"
    NOT_APPLICABLE = "not_applicable"


class HumanReviewStatus(str, Enum):
    GO = "GO"
    NO_GO = "NO_GO"
    NOT_REVIEWED = "NOT_REVIEWED"


def _require_nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _require_safe_text(value: str) -> str:
    normalized = _require_nfc(value)
    if not normalized or len(normalized) > 2048:
        raise ValueError("free text violates the length boundary")
    if any(unicodedata.category(char).startswith("C") for char in normalized):
        raise ValueError("free text contains disallowed control characters")
    if any(pattern.search(normalized) for pattern in _DENIED_FREE_TEXT):
        raise ValueError("free text contains disallowed sensitive content")
    return normalized


def _require_clean_relative_path(value: str) -> str:
    normalized = _require_nfc(value)
    path = PurePosixPath(normalized)
    if (
        not normalized
        or path.is_absolute()
        or "\\" in normalized
        or any(part in {"", ".", ".."} for part in path.parts)
        or str(path) != normalized
    ):
        raise ValueError("path must be a clean relative POSIX path")
    return normalized


def _require_utc_timestamp(value: str) -> str:
    if not _UTC_TIMESTAMP.fullmatch(value):
        raise ValueError("timestamp must be canonical UTC")
    return value


def _require_sorted_safe_ids(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    if values != tuple(sorted(values)) or len(values) != len(set(values)):
        raise ValueError(f"{label} must be sorted and unique")
    if any(re.fullmatch(_SAFE_ID, value) is None for value in values):
        raise ValueError(f"{label} contain an invalid identifier")
    return values


def _require_plain_pattern(value: object, pattern: str, label: str) -> object:
    if isinstance(value, str) and re.fullmatch(pattern, value) is None:
        raise ValueError(f"{label} is invalid")
    return value


def _validate_evidence_metadata(model: object) -> None:
    for name in ("reason", "known_fragment", "source_span"):
        value = getattr(model, name, None)
        if value is not None:
            _require_safe_text(value)
    source_document = getattr(model, "source_document", None)
    if source_document is not None:
        _require_clean_relative_path(source_document)
    _require_sorted_safe_ids(getattr(model, "missing_fields", ()), "missing fields")


class BoundedFreeText(StrictModel):
    value: str

    _normalize_and_reject = field_validator("value")(_require_safe_text)


class EvidenceHex64(StrictModel):
    state: EvidenceState
    value: str | None = Field(default=None, pattern=_HEX64)
    reason: str | None = None
    known_fragment: str | None = None
    missing_fields: tuple[str, ...] = ()
    source_document: str | None = None
    source_span: str | None = None

    @model_validator(mode="after")
    def _validate_variant(self) -> "EvidenceHex64":
        _validate_evidence_metadata(self)
        if self.state is EvidenceState.KNOWN:
            if (
                self.value is None
                or not self.source_document
                or not self.source_span
                or self.reason is not None
                or self.known_fragment is not None
                or self.missing_fields
            ):
                raise ValueError("known evidence requires value and source")
        elif self.state is EvidenceState.UNKNOWN:
            if (
                not self.reason
                or self.value is not None
                or self.known_fragment is not None
                or self.missing_fields
                or self.source_document is not None
                or self.source_span is not None
            ):
                raise ValueError("unknown evidence requires a reason")
        elif self.state is EvidenceState.INCOMPLETE:
            if (
                not self.missing_fields
                or not self.source_span
                or self.value is not None
                or self.reason is not None
            ):
                raise ValueError("incomplete evidence requires missing fields and source span")
        elif (
            not self.reason
            or self.value is not None
            or self.known_fragment is not None
            or self.missing_fields
            or self.source_document is not None
            or self.source_span is not None
        ):
            raise ValueError("not-applicable evidence requires only a reason")
        return self


class EvidenceString(StrictModel):
    state: EvidenceState
    value: str | None = Field(default=None, pattern=_SAFE_ID)
    reason: str | None = None
    known_fragment: str | None = None
    missing_fields: tuple[str, ...] = ()
    source_document: str | None = None
    source_span: str | None = None

    @model_validator(mode="after")
    def _validate_variant(self) -> "EvidenceString":
        _validate_evidence_metadata(self)
        if self.state is EvidenceState.KNOWN:
            if (
                self.value is None
                or not self.source_document
                or not self.source_span
                or self.reason is not None
                or self.known_fragment is not None
                or self.missing_fields
            ):
                raise ValueError("known evidence requires value and source")
        elif self.state is EvidenceState.UNKNOWN:
            if (
                not self.reason
                or self.value is not None
                or self.known_fragment is not None
                or self.missing_fields
                or self.source_document is not None
                or self.source_span is not None
            ):
                raise ValueError("unknown evidence requires a reason")
        elif self.state is EvidenceState.INCOMPLETE:
            if (
                not self.missing_fields
                or not self.source_span
                or self.value is not None
                or self.reason is not None
            ):
                raise ValueError("incomplete evidence requires missing fields and source span")
        elif (
            not self.reason
            or self.value is not None
            or self.known_fragment is not None
            or self.missing_fields
            or self.source_document is not None
            or self.source_span is not None
        ):
            raise ValueError("not-applicable evidence requires only a reason")
        return self


class EvidenceScalar(StrictModel):
    state: EvidenceState
    value: bool | int | float | str | None = None
    reason: str | None = None
    missing_fields: tuple[str, ...] = ()
    source_document: str | None = None
    source_span: str | None = None

    @model_validator(mode="after")
    def _validate_variant(self) -> "EvidenceScalar":
        _validate_evidence_metadata(self)
        if isinstance(self.value, float) and not math.isfinite(self.value):
            raise ValueError("numeric evidence must be finite")
        if isinstance(self.value, str):
            _require_safe_text(self.value)
        if self.state is EvidenceState.KNOWN:
            if (
                self.value is None
                or not self.source_document
                or not self.source_span
                or self.reason is not None
                or self.missing_fields
            ):
                raise ValueError("known evidence requires value and source")
        elif self.state is EvidenceState.UNKNOWN:
            if (
                not self.reason
                or self.value is not None
                or self.missing_fields
                or self.source_document is not None
                or self.source_span is not None
            ):
                raise ValueError("unknown evidence requires a reason")
        elif self.state is EvidenceState.INCOMPLETE:
            if (
                not self.missing_fields
                or not self.source_span
                or self.value is not None
                or self.reason is not None
            ):
                raise ValueError("incomplete evidence requires missing fields and source span")
        elif (
            not self.reason
            or self.value is not None
            or self.missing_fields
            or self.source_document is not None
            or self.source_span is not None
        ):
            raise ValueError("not-applicable evidence requires only a reason")
        return self


class EvidenceTimestamp(StrictModel):
    state: Literal["known", "not_applicable"]
    value: str | None = None
    reason: str | None = None
    source_document: str | None = None
    source_span: str | None = None

    @model_validator(mode="after")
    def _validate_variant(self) -> "EvidenceTimestamp":
        _validate_evidence_metadata(self)
        if self.state == "known":
            if (
                self.value is None
                or not self.source_document
                or not self.source_span
                or self.reason is not None
            ):
                raise ValueError("known timestamp evidence requires value and source")
            _require_utc_timestamp(self.value)
        elif (
            not self.reason
            or self.value is not None
            or self.source_document is not None
            or self.source_span is not None
        ):
            raise ValueError("not-applicable timestamp evidence requires only a reason")
        return self


class NamedParameter(StrictModel):
    key: str = Field(pattern=_SAFE_ID)
    value: EvidenceScalar


class NamedParameters(StrictModel):
    parameters: tuple[NamedParameter, ...] = ()

    @model_validator(mode="after")
    def _require_sorted_unique(self) -> "NamedParameters":
        keys = tuple(item.key for item in self.parameters)
        if keys != tuple(sorted(keys)) or len(keys) != len(set(keys)):
            raise ValueError("parameter keys must be sorted and unique")
        return self


class ParameterSource(StrictModel):
    key: str = Field(pattern=_SAFE_ID)
    source: Literal["requested", "default", "provider_selected", "effective"]


class ParameterSources(StrictModel):
    items: tuple[ParameterSource, ...]

    @model_validator(mode="after")
    def _require_sorted_unique(self) -> "ParameterSources":
        keys = tuple(item.key for item in self.items)
        if keys != tuple(sorted(keys)) or len(keys) != len(set(keys)):
            raise ValueError("parameter source keys must be sorted and unique")
        return self


class RubricItem(StrictModel):
    item_id: str = Field(pattern=_SAFE_ID)
    verdict: Literal["pass", "fail", "not_reviewed"]
    concerns: tuple[BoundedFreeText, ...] = ()


class RubricItems(StrictModel):
    items: tuple[RubricItem, ...] = ()

    @model_validator(mode="after")
    def _require_sorted_unique(self) -> "RubricItems":
        keys = tuple(item.item_id for item in self.items)
        if keys != tuple(sorted(keys)) or len(keys) != len(set(keys)):
            raise ValueError("rubric item IDs must be sorted and unique")
        return self


class AttemptIdentityKey(StrictModel):
    canonical_runtime_boundary: CanonicalRuntimeBoundary
    project_id: str = Field(pattern=_SAFE_ID)
    attempt_id: str = Field(pattern=_SAFE_ID)
    generation_id: str = Field(pattern=_SAFE_ID)
    identity_hash: str = Field(pattern=_HEX64)

    @staticmethod
    def _hash_components(
        *,
        canonical_runtime_boundary: CanonicalRuntimeBoundary,
        project_id: str,
        attempt_id: str,
        generation_id: str,
    ) -> str:
        payload = {
            "domain": "ai-video.quality-experience.attempt-identity/v1",
            "canonical_runtime_boundary": canonical_runtime_boundary.value,
            "project_id": project_id,
            "attempt_id": attempt_id,
            "generation_id": generation_id,
        }
        encoded = (
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            + "\n"
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @classmethod
    def from_components(
        cls,
        *,
        canonical_runtime_boundary: CanonicalRuntimeBoundary | str,
        project_id: str,
        attempt_id: str,
        generation_id: str,
    ) -> "AttemptIdentityKey":
        boundary = CanonicalRuntimeBoundary(canonical_runtime_boundary)
        return cls(
            canonical_runtime_boundary=boundary,
            project_id=project_id,
            attempt_id=attempt_id,
            generation_id=generation_id,
            identity_hash=cls._hash_components(
                canonical_runtime_boundary=boundary,
                project_id=project_id,
                attempt_id=attempt_id,
                generation_id=generation_id,
            ),
        )

    @model_validator(mode="after")
    def _require_component_hash(self) -> "AttemptIdentityKey":
        expected = self._hash_components(
            canonical_runtime_boundary=self.canonical_runtime_boundary,
            project_id=self.project_id,
            attempt_id=self.attempt_id,
            generation_id=self.generation_id,
        )
        if self.identity_hash != expected:
            raise ValueError("attempt identity hash does not match components")
        return self


class QualityRecordPointer(StrictModel):
    record_kind: Literal["prospective_q0_attempt"]
    schema_version: Literal["1.0", "1.1"]
    relative_path: str
    content_hash: str = Field(pattern=_HEX64)
    file_sha256: str = Field(pattern=_HEX64)
    recorded_sequence: int = Field(ge=1)
    recorded_attempt_id: str = Field(pattern=_SAFE_ID)

    _clean_relative_path = field_validator("relative_path")(
        _require_clean_relative_path
    )


class RecordIdentity(StrictModel):
    project_artifact_id: str = Field(pattern=_SAFE_ID)
    project_artifact_revision: int = Field(ge=1)
    project_artifact_content_hash: str = Field(pattern=_HEX64)
    manifest_observation_revision: int = Field(ge=1)
    manifest_observation_file_hash: str = Field(pattern=_HEX64)
    registry_observation_revision: int = Field(ge=1)
    registry_observation_file_hash: str = Field(pattern=_HEX64)
    scene_id: str = Field(pattern=_SAFE_ID)
    scene_revision: int = Field(ge=1)
    scene_content_hash: str = Field(pattern=_HEX64)
    shot_id: str = Field(pattern=_SAFE_ID)
    shot_revision: int = Field(ge=1)
    shot_content_hash: str = Field(pattern=_HEX64)
    generation_id: str = Field(pattern=_SAFE_ID)
    attempt_id: str = Field(pattern=_SAFE_ID)


class AttemptLineage(StrictModel):
    attempt_sequence: int = Field(ge=1)
    attempt_kind: AttemptKind
    predecessor: QualityRecordPointer | None = None

    @model_validator(mode="after")
    def _require_backward_predecessor(self) -> "AttemptLineage":
        if (
            self.predecessor is not None
            and self.predecessor.recorded_sequence >= self.attempt_sequence
        ):
            raise ValueError("predecessor must point backward")
        return self


class EvidencePath(StrictModel):
    state: Literal["known", "not_applicable"]
    value: str | None = None
    reason: str | None = None
    source_document: str | None = None
    source_span: str | None = None

    @model_validator(mode="after")
    def _validate_variant(self) -> "EvidencePath":
        _validate_evidence_metadata(self)
        if self.state == "known":
            if (
                self.value is None
                or not self.source_document
                or not self.source_span
                or self.reason is not None
            ):
                raise ValueError("known path evidence requires value and source")
            _require_clean_relative_path(self.value)
        elif (
            not self.reason
            or self.value is not None
            or self.source_document is not None
            or self.source_span is not None
        ):
            raise ValueError("not-applicable path evidence requires only a reason")
        return self


class ProviderBinding(StrictModel):
    name: str = Field(pattern=_SAFE_ID)
    kind: str = Field(pattern=_SAFE_ID)
    execution_kind: Literal["local", "remote"]
    billing_kind: Literal["unmetered", "metered"]
    profile_id: str = Field(pattern=_SAFE_ID)
    profile_version: str = Field(pattern=_SAFE_ID)
    profile_path: str
    profile_sha256: str = Field(pattern=_HEX64)
    capability_id: str = Field(pattern=_SAFE_ID)
    workflow_id: EvidenceString
    workflow_version: EvidenceString
    workflow_path: EvidencePath
    workflow_fingerprint: EvidenceHex64
    model_id: EvidenceString
    adapter_compiler_id: str | EvidenceString
    adapter_compiler_version: str | EvidenceString
    adapter_compiler_hash: str | EvidenceHex64

    @field_validator("adapter_compiler_id", "adapter_compiler_version")
    @classmethod
    def _plain_compiler_id_is_safe(cls, value: object) -> object:
        return _require_plain_pattern(value, _SAFE_ID, "compiler identity")

    @field_validator("adapter_compiler_hash")
    @classmethod
    def _plain_compiler_hash_is_hex(cls, value: object) -> object:
        return _require_plain_pattern(value, _HEX64, "compiler hash")

    _clean_profile_path = field_validator("profile_path")(
        _require_clean_relative_path
    )

    @model_validator(mode="after")
    def _require_consistent_workflow_binding(self) -> "ProviderBinding":
        states = (
            self.workflow_id.state.value,
            self.workflow_version.state.value,
            self.workflow_path.state,
            self.workflow_fingerprint.state.value,
        )
        if len(set(states)) != 1 or states[0] not in {"known", "not_applicable"}:
            raise ValueError("workflow identity must be wholly known or not applicable")
        return self


class PlanningBinding(StrictModel):
    planning_request_hash: str | EvidenceHex64
    plan_hash: str | EvidenceHex64
    requirement_hash: str | EvidenceHex64
    readiness_request_hash: str | EvidenceHex64
    readiness_result_hash: str | EvidenceHex64
    readiness_state: Literal["READY", "BLOCKED"] | EvidenceString
    check_reason_codes: tuple[str, ...]

    @field_validator(
        "planning_request_hash",
        "plan_hash",
        "requirement_hash",
        "readiness_request_hash",
        "readiness_result_hash",
    )
    @classmethod
    def _plain_hash_is_hex(cls, value: object) -> object:
        return _require_plain_pattern(value, _HEX64, "planning hash")

    @model_validator(mode="after")
    def _canonical_reasons(self) -> "PlanningBinding":
        _require_sorted_safe_ids(self.check_reason_codes, "readiness reason codes")
        return self


class RoutingBinding(StrictModel):
    semantic_decision_hash: str | EvidenceHex64
    audit_decision_hash: str | EvidenceHex64
    policy_id: str | EvidenceString
    policy_version: str | EvidenceString
    policy_hash: str | EvidenceHex64
    provider_capabilities_fingerprint: str | EvidenceHex64
    selected_capability_id: str = Field(pattern=_SAFE_ID)
    selected_capability_fingerprint: str | EvidenceHex64
    provider_bound_request_hash: str | EvidenceHex64

    @field_validator("policy_id", "policy_version")
    @classmethod
    def _plain_policy_identity_is_safe(cls, value: object) -> object:
        return _require_plain_pattern(value, _SAFE_ID, "routing policy identity")

    @field_validator(
        "semantic_decision_hash",
        "audit_decision_hash",
        "policy_hash",
        "provider_capabilities_fingerprint",
        "selected_capability_fingerprint",
        "provider_bound_request_hash",
    )
    @classmethod
    def _plain_hash_is_hex(cls, value: object) -> object:
        return _require_plain_pattern(value, _HEX64, "routing hash")


class PromptBinding(StrictModel):
    prompt_sha256: str = Field(pattern=_HEX64)
    negative_prompt_sha256: str = Field(pattern=_HEX64)
    structured_intent_hash: str | EvidenceHex64
    compiler_id: str | EvidenceString
    compiler_version: str | EvidenceString
    compiler_hash: str | EvidenceHex64

    @field_validator("compiler_id", "compiler_version")
    @classmethod
    def _plain_compiler_identity_is_safe(cls, value: object) -> object:
        return _require_plain_pattern(value, _SAFE_ID, "prompt compiler identity")

    @field_validator("structured_intent_hash", "compiler_hash")
    @classmethod
    def _plain_hash_is_hex(cls, value: object) -> object:
        return _require_plain_pattern(value, _HEX64, "prompt hash")


class ParameterBinding(StrictModel):
    requested_seed: EvidenceScalar
    effective_seed: EvidenceScalar
    effective_output_hash: str = Field(pattern=_HEX64)
    duration_milliseconds: int = Field(gt=0)
    frame_count: int = Field(gt=0)
    fps_numerator: int = Field(gt=0)
    fps_denominator: int = Field(gt=0)
    steps: EvidenceScalar
    sampler: EvidenceString
    scheduler: EvidenceString
    audio_mode: EvidenceString
    provider_parameters: NamedParameters
    sources: ParameterSources

    @model_validator(mode="after")
    def _require_source_for_every_parameter(self) -> "ParameterBinding":
        expected = {
            "audio_mode",
            "duration_milliseconds",
            "effective_seed",
            "fps",
            "frame_count",
            "requested_seed",
            "sampler",
            "scheduler",
            "steps",
            *(f"provider.{item.key}" for item in self.provider_parameters.parameters),
        }
        if {item.key for item in self.sources.items} != expected:
            raise ValueError("every parameter requires an exact resolution source")
        return self


class InputBinding(StrictModel):
    role: str = Field(pattern=_SAFE_ID)
    artifact_id: str = Field(pattern=_SAFE_ID)
    revision: EvidenceScalar
    content_hash: str = Field(pattern=_HEX64)
    file_sha256: str = Field(pattern=_HEX64)
    mime_type: str = Field(pattern=r"^[a-z0-9.+-]+/[a-z0-9.+-]+$")
    size_bytes: int = Field(gt=0)
    registry_revision: str = Field(pattern=_SAFE_ID)
    registry_file_sha256: str = Field(pattern=_HEX64)
    creation_receipt_id: str = Field(pattern=_SAFE_ID)
    creation_receipt_hash: str | EvidenceHex64
    provenance_receipt_id: str | EvidenceString
    provenance_receipt_hash: str | EvidenceHex64

    @field_validator("provenance_receipt_id")
    @classmethod
    def _plain_provenance_id_is_safe(cls, value: object) -> object:
        return _require_plain_pattern(value, _SAFE_ID, "provenance identity")

    @field_validator("creation_receipt_hash", "provenance_receipt_hash")
    @classmethod
    def _plain_receipt_hash_is_hex(cls, value: object) -> object:
        return _require_plain_pattern(value, _HEX64, "receipt hash")

    @property
    def sort_key(self) -> tuple[str, str]:
        return (self.role, self.artifact_id)


class InputBindings(StrictModel):
    items: tuple[InputBinding, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _canonical_inputs(self) -> "InputBindings":
        keys = tuple(item.sort_key for item in self.items)
        if keys != tuple(sorted(keys)) or len(keys) != len(set(keys)):
            raise ValueError("input bindings must be sorted and unique")
        return self


class ContinuityBinding(StrictModel):
    mode: Literal["exact_terminal", "reference", "semantic", "none"]
    source_shot_id: EvidenceString
    target_shot_id: str = Field(pattern=_SAFE_ID)
    terminal_frame_hash: EvidenceHex64
    keyframe_hash: EvidenceHex64
    continuity_state_hash: EvidenceHex64
    first_frame_binding_hash: EvidenceHex64
    last_frame_binding_hash: EvidenceHex64

    @model_validator(mode="after")
    def _require_consistent_mode(self) -> "ContinuityBinding":
        evidence = (
            self.source_shot_id,
            self.terminal_frame_hash,
            self.keyframe_hash,
            self.continuity_state_hash,
            self.first_frame_binding_hash,
            self.last_frame_binding_hash,
        )
        if self.mode == "none" and any(
            item.state is not EvidenceState.NOT_APPLICABLE for item in evidence
        ):
            raise ValueError("none continuity requires explicit not-applicable evidence")
        if self.mode != "none" and self.source_shot_id.state is not EvidenceState.KNOWN:
            raise ValueError("continuity mode requires an exact source Shot")
        required_by_mode = {
            "exact_terminal": (
                self.terminal_frame_hash,
                self.continuity_state_hash,
                self.first_frame_binding_hash,
            ),
            "reference": (
                self.keyframe_hash,
                self.continuity_state_hash,
                self.first_frame_binding_hash,
            ),
            "semantic": (self.continuity_state_hash,),
        }
        if self.mode != "none" and any(
            item.state is not EvidenceState.KNOWN
            for item in required_by_mode[self.mode]
        ):
            raise ValueError("continuity mode is missing required exact evidence")
        return self


class ArtifactEvidenceKnown(StrictModel):
    state: Literal["known"]
    boundary: Literal["canonical", "lab"]
    relative_path: str
    asset_id: str = Field(pattern=_SAFE_ID)
    file_sha256: str = Field(pattern=_HEX64)
    size_bytes: int = Field(gt=0)
    container: str = Field(pattern=_SAFE_ID)
    codec: str = Field(pattern=_SAFE_ID)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps_numerator: int = Field(gt=0)
    fps_denominator: int = Field(gt=0)
    duration_milliseconds: int = Field(gt=0)
    frame_count: int = Field(gt=0)
    audio_stream_count: int = Field(ge=0)
    ffprobe_hash: str = Field(pattern=_HEX64)
    video_probe_receipt_id: str = Field(pattern=_SAFE_ID)
    probe_receipt_hash: str = Field(pattern=_HEX64)
    provenance_receipt_id: str = Field(pattern=_SAFE_ID)
    provenance_receipt_hash: str = Field(pattern=_HEX64)

    _clean_relative_path = field_validator("relative_path")(
        _require_clean_relative_path
    )


class ArtifactEvidenceNotPresent(StrictModel):
    state: Literal["not_present"]
    reason_code: str = Field(pattern=_SAFE_ID)


ArtifactEvidence = Annotated[
    ArtifactEvidenceKnown | ArtifactEvidenceNotPresent,
    Field(discriminator="state"),
]


class ReplayCounters(StrictModel):
    provider_calls: int = Field(ge=0)
    renderer_calls: int = Field(ge=0)
    analyzer_calls: int = Field(ge=0)
    manifest_writes: int = Field(ge=0)


class DurabilityBinding(StrictModel):
    activation_state: Literal["not_candidate", "candidate", "activated", "unknown"]
    manifest_revision: int = Field(ge=1)
    strict_reopen_result: Literal["verified", "failed", "not_observed"]
    recovery_observation: Literal["not_required", "recovered", "preserved_orphan", "unknown"]
    exact_replay_counters: ReplayCounters
    exact_replay_result: Literal["zero_effect", "not_run", "failed"]


class KnownBooleanMeasurement(StrictModel):
    state: Literal["known"]
    value: bool = Field(strict=True)
    source_document: str
    source_span: str

    @model_validator(mode="after")
    def _require_source(self) -> "KnownBooleanMeasurement":
        _validate_evidence_metadata(self)
        return self


class KnownRatioMeasurement(StrictModel):
    state: Literal["known"]
    value: float = Field(strict=True, ge=0.0, le=1.0)
    source_document: str
    source_span: str

    @model_validator(mode="after")
    def _require_source(self) -> "KnownRatioMeasurement":
        _validate_evidence_metadata(self)
        return self


class KnownCountMeasurement(StrictModel):
    state: Literal["known"]
    value: int = Field(strict=True, ge=0)
    source_document: str
    source_span: str

    @model_validator(mode="after")
    def _require_source(self) -> "KnownCountMeasurement":
        _validate_evidence_metadata(self)
        return self


class BooleanAnalyzerMeasurement(StrictModel):
    key: Literal["audio_integrity"]
    value: KnownBooleanMeasurement


class RatioAnalyzerMeasurement(StrictModel):
    key: Literal["black_ratio", "continuity_score", "detail_score", "freeze_ratio"]
    value: KnownRatioMeasurement


class CountAnalyzerMeasurement(StrictModel):
    key: Literal["scene_change_count"]
    value: KnownCountMeasurement


AnalyzerMeasurement = Annotated[
    BooleanAnalyzerMeasurement | RatioAnalyzerMeasurement | CountAnalyzerMeasurement,
    Field(discriminator="key"),
]


class AnalyzerMeasurements(StrictModel):
    parameters: tuple[AnalyzerMeasurement, ...]

    @model_validator(mode="after")
    def _require_q0_measurement_set(self) -> "AnalyzerMeasurements":
        keys = tuple(item.key for item in self.parameters)
        required = (
            "audio_integrity",
            "black_ratio",
            "continuity_score",
            "detail_score",
            "freeze_ratio",
            "scene_change_count",
        )
        if keys != required:
            raise ValueError("analyzer evidence requires the canonical Q0 measurement set")
        return self


class AnalyzerEvidenceItem(StrictModel):
    evidence_id: str = Field(pattern=_SAFE_ID)
    evidence_hash: str = Field(pattern=_HEX64)
    tool_name: str = Field(pattern=_SAFE_ID)
    tool_version: str = Field(pattern=_SAFE_ID)
    measurement_contract_version: str = Field(pattern=_SAFE_ID)
    subject_id: str = Field(pattern=_SAFE_ID)
    span_hash: str = Field(pattern=_HEX64)
    measurements_hash: str = Field(pattern=_HEX64)
    measurements: AnalyzerMeasurements


class AnalyzerBinding(StrictModel):
    state: Literal["known", "not_applicable"]
    reason_code: str | None = Field(default=None, pattern=_SAFE_ID)
    evidence: tuple[AnalyzerEvidenceItem, ...] = ()

    @model_validator(mode="after")
    def _validate_state(self) -> "AnalyzerBinding":
        ids = tuple(item.evidence_id for item in self.evidence)
        if ids != tuple(sorted(ids)) or len(ids) != len(set(ids)):
            raise ValueError("analyzer evidence must be sorted and unique")
        if self.state == "known" and (not self.evidence or self.reason_code is not None):
            raise ValueError("known analyzer evidence requires exact items")
        if self.state == "not_applicable" and (self.evidence or not self.reason_code):
            raise ValueError("not-applicable analyzer evidence requires only a reason")
        return self


class HumanReviewBinding(StrictModel):
    status: HumanReviewStatus
    reviewer_id: EvidenceString
    reviewer_kind: EvidenceString
    rubric_id: str = Field(pattern=_SAFE_ID)
    rubric_version: str = Field(pattern=_SAFE_ID)
    rubric_hash: str = Field(pattern=_HEX64)
    watched_at: EvidenceTimestamp
    items: RubricItems

    @model_validator(mode="after")
    def _validate_review_state(self) -> "HumanReviewBinding":
        tagged = (self.reviewer_id, self.reviewer_kind, self.watched_at)
        states = tuple(
            item.state.value if isinstance(item.state, EvidenceState) else item.state
            for item in tagged
        )
        if self.status is HumanReviewStatus.NOT_REVIEWED:
            if any(state != "not_applicable" for state in states):
                raise ValueError("not-reviewed evidence must be explicitly not applicable")
            if self.items.items:
                raise ValueError("not-reviewed evidence cannot contain rubric verdicts")
        elif any(state != "known" for state in states):
            raise ValueError("reviewed evidence requires exact pseudonymous identity")
        elif not self.items.items:
            raise ValueError("reviewed evidence requires rubric item verdicts")
        elif self.status is HumanReviewStatus.GO and any(
            item.verdict != "pass" for item in self.items.items
        ):
            raise ValueError("GO review cannot contain a non-pass rubric verdict")
        elif self.status is HumanReviewStatus.NO_GO and not any(
            item.verdict == "fail" for item in self.items.items
        ):
            raise ValueError("NO_GO review requires a failed rubric item")
        return self


class InterventionBinding(StrictModel):
    kind: Literal["none", "changed"]
    failure_taxonomy: EvidenceString
    changed_variables: NamedParameters
    unchanged_controls: NamedParameters
    confounders: tuple[BoundedFreeText, ...]
    rationale: BoundedFreeText

    @model_validator(mode="after")
    def _validate_kind(self) -> "InterventionBinding":
        if self.kind == "none" and (
            self.failure_taxonomy.state is not EvidenceState.NOT_APPLICABLE
            or self.changed_variables.parameters
        ):
            raise ValueError("no intervention cannot declare changes")
        if self.kind == "changed" and (
            self.failure_taxonomy.state is not EvidenceState.KNOWN
            or not self.changed_variables.parameters
        ):
            raise ValueError("changed intervention requires taxonomy and variables")
        return self


class ExactEvidencePointer(StrictModel):
    kind: str = Field(pattern=_SAFE_ID)
    relative_path: str
    content_hash: str = Field(pattern=_HEX64)
    file_sha256: str = Field(pattern=_HEX64)
    freshness: Literal["fresh", "stale", "not_observed"]

    _clean_relative_path = field_validator("relative_path")(
        _require_clean_relative_path
    )


class ContinuityEvidenceBinding(StrictModel):
    intent: ExactEvidencePointer
    evidence: ExactEvidencePointer
    evaluation_fingerprint: str = Field(pattern=_HEX64)
    artifact_sha256: str = Field(pattern=_HEX64)
    resolved_generation_hash: str = Field(pattern=_HEX64)
    target_shot_content_hash: str = Field(pattern=_HEX64)
    constraints_hash: str = Field(pattern=_HEX64)
    qa_policy_hash: str = Field(pattern=_HEX64)
    evaluator_profile_hash: str = Field(pattern=_HEX64)
    evaluator_identity: str = Field(pattern=_SAFE_ID)
    authority_binding_hash: str = Field(pattern=_HEX64)
    human_fallback_hash: EvidenceHex64

    @model_validator(mode="after")
    def _require_exact_pointer_kinds(self) -> "ContinuityEvidenceBinding":
        if self.intent.kind != "continuity_intent":
            raise ValueError("continuity intent pointer kind is invalid")
        if self.evidence.kind != "continuity_evidence":
            raise ValueError("continuity evidence pointer kind is invalid")
        return self


class OutcomeBoundaryBinding(StrictModel):
    artifact_claim: BoundedFreeText
    p6_state: Literal["not_present", "present", "stale"]
    p6_observations: tuple[ExactEvidencePointer, ...]
    allowed_conclusions: tuple[BoundedFreeText, ...] = Field(min_length=1)
    forbidden_extrapolations: tuple[BoundedFreeText, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_boundary(self) -> "OutcomeBoundaryBinding":
        keys = tuple((item.kind, item.relative_path) for item in self.p6_observations)
        if keys != tuple(sorted(keys)) or len(keys) != len(set(keys)):
            raise ValueError("P6 observations must be sorted and unique")
        if self.p6_state == "not_present" and self.p6_observations:
            raise ValueError("absent P6 state cannot contain pointers")
        if self.p6_state != "not_present" and not self.p6_observations:
            raise ValueError("observed P6 state requires exact pointers")
        has_fresh = any(
            item.freshness == "fresh" for item in self.p6_observations
        )
        if self.p6_state == "present" and not has_fresh:
            raise ValueError("present P6 state requires a fresh pointer")
        if self.p6_state == "stale" and has_fresh:
            raise ValueError("stale P6 state cannot contain a fresh pointer")
        return self


class OutcomeSucceeded(StrictModel):
    variant: Literal["succeeded"]
    terminal_boundary: Literal["fetched", "candidate", "activated"]
    observed_at: str

    _canonical_observed_at = field_validator("observed_at")(_require_utc_timestamp)


class OutcomeKnownFailure(StrictModel):
    variant: Literal["known_failure"]
    error_code: str = Field(pattern=_SAFE_ID)
    last_durable_phase: str = Field(pattern=_SAFE_ID)
    retryable: bool
    observed_at: str
    error_boundary: BoundedFreeText

    _canonical_observed_at = field_validator("observed_at")(_require_utc_timestamp)


class OutcomeUnknown(StrictModel):
    variant: Literal["outcome_unknown"]
    reason: BoundedFreeText
    retryability: Literal["unknown"]
    observed_at: str

    @field_validator("observed_at")
    @classmethod
    def _canonical_observed_at(cls, value: str) -> str:
        return _require_utc_timestamp(value)


AttemptOutcome = Annotated[
    OutcomeSucceeded | OutcomeKnownFailure | OutcomeUnknown,
    Field(discriminator="variant"),
]


class QualityExperienceRecordV1(StrictModel):
    record_kind: Literal["prospective_q0_attempt"]
    schema_version: Literal["1.0", "1.1"]
    content_hash: str | None = Field(default=None, pattern=_HEX64)
    experiment_id: str = Field(pattern=_SAFE_ID)
    pilot_id: str = Field(pattern=_SAFE_ID)
    captured_at: str
    repository_commit: str = Field(pattern=_COMMIT)
    purpose: BoundedFreeText
    hypothesis: BoundedFreeText
    capture_actor: str = Field(pattern=_SAFE_ID)
    authorization_boundary: str = Field(pattern=_SAFE_ID)
    canonical_runtime_boundary: CanonicalRuntimeBoundary
    identity: RecordIdentity
    lineage: AttemptLineage
    planning: PlanningBinding
    routing: RoutingBinding
    provider: ProviderBinding
    prompt: PromptBinding
    parameters: ParameterBinding
    inputs: InputBindings
    continuity: ContinuityBinding
    continuity_evidence: ContinuityEvidenceBinding | None = None
    outcome: AttemptOutcome
    artifact_evidence: ArtifactEvidence
    durability: DurabilityBinding
    analyzer: AnalyzerBinding
    human_review: HumanReviewBinding
    intervention: InterventionBinding
    outcome_boundary: OutcomeBoundaryBinding

    @field_validator("captured_at")
    @classmethod
    def _canonical_captured_at(cls, value: str) -> str:
        return _require_utc_timestamp(value)

    @model_serializer(mode="wrap")
    def _serialize_compatible_schema(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.schema_version == "1.0":
            data.pop("continuity_evidence", None)
        return data

    @property
    def attempt_identity_key(self) -> AttemptIdentityKey:
        return AttemptIdentityKey.from_components(
            canonical_runtime_boundary=self.canonical_runtime_boundary,
            project_id=self.identity.project_artifact_id,
            attempt_id=self.identity.attempt_id,
            generation_id=self.identity.generation_id,
        )

    @model_validator(mode="after")
    def _require_complete_exact_bindings(self) -> "QualityExperienceRecordV1":
        if self.schema_version == "1.0" and self.continuity_evidence is not None:
            raise ValueError("schema 1.0 cannot contain continuity evidence")
        if self.schema_version == "1.1" and self.continuity_evidence is None:
            raise ValueError("schema 1.1 requires continuity evidence")
        if self.schema_version == "1.1":
            continuity_evidence = self.continuity_evidence
            continuity_state = self.continuity.continuity_state_hash
            if (
                not isinstance(self.artifact_evidence, ArtifactEvidenceKnown)
                or self.continuity.mode == "none"
                or continuity_state.state is not EvidenceState.KNOWN
                or continuity_state.value is None
                or continuity_evidence.artifact_sha256
                != self.artifact_evidence.file_sha256
                or continuity_evidence.target_shot_content_hash
                != self.identity.shot_content_hash
                or continuity_evidence.constraints_hash != continuity_state.value
            ):
                raise ValueError(
                    "schema 1.1 continuity evidence must bind the exact artifact and Shot"
                )
        if self.schema_version == "1.0":
            legacy_values = (
                self.planning.planning_request_hash,
                self.planning.plan_hash,
                self.planning.requirement_hash,
                self.planning.readiness_request_hash,
                self.planning.readiness_result_hash,
                self.planning.readiness_state,
                self.routing.semantic_decision_hash,
                self.routing.audit_decision_hash,
                self.routing.policy_id,
                self.routing.policy_version,
                self.routing.policy_hash,
                self.routing.provider_capabilities_fingerprint,
                self.routing.selected_capability_fingerprint,
                self.routing.provider_bound_request_hash,
                self.provider.adapter_compiler_id,
                self.provider.adapter_compiler_version,
                self.provider.adapter_compiler_hash,
                self.prompt.structured_intent_hash,
                self.prompt.compiler_id,
                self.prompt.compiler_version,
                self.prompt.compiler_hash,
                *(
                    value
                    for item in self.inputs.items
                    for value in (
                        item.creation_receipt_hash,
                        item.provenance_receipt_id,
                        item.provenance_receipt_hash,
                    )
                ),
            )
            if any(not isinstance(value, str) for value in legacy_values):
                raise ValueError("schema 1.0 requires legacy exact string bindings")
        if self.routing.selected_capability_id != self.provider.capability_id:
            raise ValueError("routing and Provider capability identities must match")
        if self.continuity.target_shot_id != self.identity.shot_id:
            raise ValueError("continuity target must match record Shot")
        succeeded = isinstance(self.outcome, OutcomeSucceeded)
        if succeeded != isinstance(self.artifact_evidence, ArtifactEvidenceKnown):
            raise ValueError("outcome and artifact evidence boundary must match")
        if succeeded and self.analyzer.state != "known":
            raise ValueError("succeeded capture requires analyzer evidence")
        if isinstance(self.artifact_evidence, ArtifactEvidenceKnown):
            if (
                self.parameters.duration_milliseconds
                != self.artifact_evidence.duration_milliseconds
                or self.parameters.frame_count != self.artifact_evidence.frame_count
                or self.parameters.fps_numerator
                != self.artifact_evidence.fps_numerator
                or self.parameters.fps_denominator
                != self.artifact_evidence.fps_denominator
                or any(
                    item.subject_id != self.artifact_evidence.asset_id
                    for item in self.analyzer.evidence
                )
            ):
                raise ValueError("artifact measurement bindings are contradictory")
        if isinstance(self.outcome, OutcomeSucceeded):
            expected_activation = {
                "fetched": "not_candidate",
                "candidate": "candidate",
                "activated": "activated",
            }[self.outcome.terminal_boundary]
            if self.durability.activation_state != expected_activation:
                raise ValueError("outcome and durability boundaries are contradictory")
        elif isinstance(self.outcome, OutcomeKnownFailure):
            if self.durability.activation_state != "not_candidate":
                raise ValueError("known failure cannot claim candidate activation")
        elif self.durability.activation_state != "unknown":
            raise ValueError("unknown outcome requires unknown durability state")
        if not succeeded and self.human_review.status is not HumanReviewStatus.NOT_REVIEWED:
            raise ValueError("attempts without an artifact cannot claim human review")
        if self.canonical_runtime_boundary is CanonicalRuntimeBoundary.PRODUCTION_MANIFEST:
            if isinstance(self.artifact_evidence, ArtifactEvidenceKnown) and (
                self.artifact_evidence.boundary != "canonical"
            ):
                raise ValueError("Production attempt requires canonical artifact boundary")
        elif isinstance(self.artifact_evidence, ArtifactEvidenceKnown) and (
            self.artifact_evidence.boundary != "lab"
        ):
            raise ValueError("lab attempt requires lab artifact boundary")

        def reject_incomplete(value: object) -> None:
            if isinstance(value, dict):
                if value.get("state") in {"unknown", "incomplete"}:
                    raise ValueError("prospective exact evidence cannot be incomplete")
                for item in value.values():
                    reject_incomplete(item)
            elif isinstance(value, list):
                for item in value:
                    reject_incomplete(item)

        reject_incomplete(self.model_dump(mode="json"))
        return self


class HistoricalEvidence(StrictModel):
    state: EvidenceState
    value: bool | int | float | str | None = None
    reason: str | None = None
    known_fragment: str | None = None
    missing_fields: tuple[str, ...] = ()
    source_document: str | None = None
    source_span: str | None = None

    @model_validator(mode="after")
    def _validate_variant(self) -> "HistoricalEvidence":
        _validate_evidence_metadata(self)
        if isinstance(self.value, float) and not math.isfinite(self.value):
            raise ValueError("historical numeric evidence must be finite")
        if self.state is EvidenceState.KNOWN:
            if (
                self.value is None
                or not self.source_document
                or not self.source_span
                or self.reason is not None
                or self.known_fragment is not None
                or self.missing_fields
            ):
                raise ValueError("known historical evidence requires exact source")
        elif self.state is EvidenceState.UNKNOWN:
            if (
                not self.reason
                or self.value is not None
                or self.known_fragment is not None
                or self.missing_fields
                or self.source_document is not None
                or self.source_span is not None
            ):
                raise ValueError("unknown historical evidence requires a reason")
        elif self.state is EvidenceState.INCOMPLETE:
            if (
                not self.known_fragment
                or not self.missing_fields
                or not self.source_document
                or not self.source_span
                or self.value is not None
                or self.reason is not None
            ):
                raise ValueError("incomplete historical evidence requires fragment and source")
        elif (
            not self.reason
            or self.value is not None
            or self.known_fragment is not None
            or self.missing_fields
            or self.source_document is not None
            or self.source_span is not None
        ):
            raise ValueError("not-applicable historical evidence requires a reason")
        for candidate in (
            self.value if isinstance(self.value, str) else None,
            self.reason,
            self.known_fragment,
            self.source_span,
        ):
            if candidate is not None:
                _require_safe_text(candidate)
        if self.source_document is not None:
            _require_clean_relative_path(self.source_document)
        return self


class HistoricalFieldEvidence(StrictModel):
    field_name: str = Field(pattern=_SAFE_ID)
    evidence: HistoricalEvidence


class HistoricalImportPointer(StrictModel):
    schema_version: Literal["1.0"]
    relative_path: str
    content_hash: str = Field(pattern=_HEX64)
    file_sha256: str = Field(pattern=_HEX64)

    _clean_relative_path = field_validator("relative_path")(
        _require_clean_relative_path
    )


class HistoricalQualityExperienceImportV1(StrictModel):
    record_kind: Literal["historical_quality_experience_import"]
    schema_version: Literal["1.0"]
    content_hash: str | None = Field(default=None, pattern=_HEX64)
    import_id: str = Field(pattern=_SAFE_ID)
    imported_at: str
    source_document: str
    source_document_sha256: str = Field(pattern=_HEX64)
    fields: tuple[HistoricalFieldEvidence, ...]

    _clean_source_document = field_validator("source_document")(
        _require_clean_relative_path
    )

    @field_validator("imported_at")
    @classmethod
    def _canonical_imported_at(cls, value: str) -> str:
        return _require_utc_timestamp(value)

    @model_validator(mode="after")
    def _require_sorted_unique_fields(self) -> "HistoricalQualityExperienceImportV1":
        names = tuple(item.field_name for item in self.fields)
        if names != tuple(sorted(names)) or len(names) != len(set(names)):
            raise ValueError("historical field names must be sorted and unique")
        return self


class LogicalShotKey(StrictModel):
    project_id: str = Field(pattern=_SAFE_ID)
    scene_id: str = Field(pattern=_SAFE_ID)
    shot_id: str = Field(pattern=_SAFE_ID)

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return (self.project_id, self.scene_id, self.shot_id)


class ManifestObservationV1(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    relative_path: Literal["state/manifest.json"] = "state/manifest.json"
    project_id: str = Field(pattern=_SAFE_ID)
    manifest_revision: int = Field(ge=1)
    file_sha256: str = Field(pattern=_HEX64)
    attempt_count: int = Field(ge=0)
    ordered_attempt_ids_hash: str = Field(pattern=_HEX64)


class PilotCaptureCohortPointer(StrictModel):
    schema_version: Literal["1.0"]
    pilot_id: str = Field(pattern=_SAFE_ID)
    relative_path: str
    content_hash: str = Field(pattern=_HEX64)
    file_sha256: str = Field(pattern=_HEX64)

    _clean_relative_path = field_validator("relative_path")(
        _require_clean_relative_path
    )


class PilotCaptureCohortV1(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    content_hash: str | None = Field(default=None, pattern=_HEX64)
    pilot_id: str = Field(pattern=_SAFE_ID)
    purpose: BoundedFreeText
    hypothesis: BoundedFreeText
    authorization_boundary: str = Field(pattern=_SAFE_ID)
    capture_contract_version: str = Field(pattern=_SAFE_ID)
    rubric_id: str = Field(pattern=_SAFE_ID)
    rubric_version: str = Field(pattern=_SAFE_ID)
    rubric_hash: str = Field(pattern=_HEX64)
    repository_commit: str = Field(pattern=_COMMIT)
    allowed_attempt_source: Literal["production_manifest"] = "production_manifest"
    base_manifest: ManifestObservationV1
    shot_keys: tuple[LogicalShotKey, ...] = Field(min_length=4, max_length=8)

    @model_validator(mode="after")
    def _require_canonical_shots(self) -> "PilotCaptureCohortV1":
        keys = tuple(item.sort_key for item in self.shot_keys)
        if keys != tuple(sorted(keys)) or len(keys) != len(set(keys)):
            raise ValueError("cohort Shot keys must be sorted and unique")
        if any(item.project_id != self.base_manifest.project_id for item in self.shot_keys):
            raise ValueError("cohort Shots must belong to the observed project")
        return self


class PilotAttemptRosterEntry(StrictModel):
    attempt_identity_key: AttemptIdentityKey
    shot: LogicalShotKey
    shot_revision: int = Field(ge=1)
    shot_content_hash: str = Field(pattern=_HEX64)
    attempt_sequence: int = Field(ge=1)


class PilotAttemptRosterPointer(StrictModel):
    schema_version: Literal["1.0"]
    pilot_id: str = Field(pattern=_SAFE_ID)
    relative_path: str
    content_hash: str = Field(pattern=_HEX64)
    file_sha256: str = Field(pattern=_HEX64)

    _clean_relative_path = field_validator("relative_path")(
        _require_clean_relative_path
    )


class PilotAttemptRosterV1(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    content_hash: str | None = Field(default=None, pattern=_HEX64)
    pilot_id: str = Field(pattern=_SAFE_ID)
    cohort: PilotCaptureCohortPointer
    terminal_manifest: ManifestObservationV1
    entries: tuple[PilotAttemptRosterEntry, ...]

    @model_validator(mode="after")
    def _require_canonical_entries(self) -> "PilotAttemptRosterV1":
        sequences = tuple(item.attempt_sequence for item in self.entries)
        identities = tuple(item.attempt_identity_key.identity_hash for item in self.entries)
        if sequences != tuple(sorted(sequences)) or len(sequences) != len(set(sequences)):
            raise ValueError("roster entries must follow unique Manifest sequence")
        if len(identities) != len(set(identities)):
            raise ValueError("roster attempt identities must be unique")
        if self.cohort.pilot_id != self.pilot_id:
            raise ValueError("roster and cohort pilot identities must match")
        if any(
            item.attempt_identity_key.canonical_runtime_boundary
            is not CanonicalRuntimeBoundary.PRODUCTION_MANIFEST
            or item.attempt_identity_key.project_id != item.shot.project_id
            or item.shot.project_id != self.terminal_manifest.project_id
            or item.attempt_sequence > self.terminal_manifest.attempt_count
            for item in self.entries
        ):
            raise ValueError("roster entries must bind the terminal Production Manifest")
        return self


class PilotDatasetIndexEntry(StrictModel):
    record: QualityRecordPointer
    experiment_id: str = Field(pattern=_SAFE_ID)
    pilot_id: str = Field(pattern=_SAFE_ID)
    project_id: str = Field(pattern=_SAFE_ID)
    scene_id: str = Field(pattern=_SAFE_ID)
    shot_id: str = Field(pattern=_SAFE_ID)
    attempt_id: str = Field(pattern=_SAFE_ID)
    generation_id: str = Field(pattern=_SAFE_ID)
    attempt_sequence: int = Field(ge=1)
    provider_name: str = Field(pattern=_SAFE_ID)
    provider_kind: str = Field(pattern=_SAFE_ID)
    profile_id: str = Field(pattern=_SAFE_ID)
    capability_id: str = Field(pattern=_SAFE_ID)
    model_id: str = Field(pattern=_SAFE_ID)
    outcome: Literal["succeeded", "known_failure", "outcome_unknown"]
    human_verdict: HumanReviewStatus
    coverage_tags: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _require_sorted_coverage(self) -> "PilotDatasetIndexEntry":
        _require_sorted_safe_ids(self.coverage_tags, "entry coverage tags")
        return self

    @property
    def sort_key(self) -> tuple[object, ...]:
        return (
            self.project_id,
            self.scene_id,
            self.shot_id,
            self.attempt_sequence,
            self.attempt_id,
            self.record.file_sha256,
        )


class PilotDatasetPointer(StrictModel):
    schema_version: Literal["1.0"]
    pilot_id: str = Field(pattern=_SAFE_ID)
    relative_path: str
    content_hash: str = Field(pattern=_HEX64)
    file_sha256: str = Field(pattern=_HEX64)

    _clean_relative_path = field_validator("relative_path")(
        _require_clean_relative_path
    )


class PilotDatasetIndexV1(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    content_hash: str | None = Field(default=None, pattern=_HEX64)
    pilot_id: str = Field(pattern=_SAFE_ID)
    dataset_purpose: BoundedFreeText
    rubric_id: str = Field(pattern=_SAFE_ID)
    rubric_version: str = Field(pattern=_SAFE_ID)
    rubric_hash: str = Field(pattern=_HEX64)
    capture_contract_version: str = Field(pattern=_SAFE_ID)
    created_at: str
    repository_commit: str = Field(pattern=_COMMIT)
    cohort: PilotCaptureCohortPointer
    roster: PilotAttemptRosterPointer
    shot_keys: tuple[LogicalShotKey, ...] = Field(min_length=4, max_length=8)
    entries: tuple[PilotDatasetIndexEntry, ...]
    coverage_tags: tuple[str, ...] = ()
    known_confounders: tuple[BoundedFreeText, ...] = ()

    @field_validator("created_at")
    @classmethod
    def _canonical_created_at(cls, value: str) -> str:
        return _require_utc_timestamp(value)

    @model_validator(mode="after")
    def _require_canonical_aggregate(self) -> "PilotDatasetIndexV1":
        shots = tuple(item.sort_key for item in self.shot_keys)
        if shots != tuple(sorted(shots)) or len(shots) != len(set(shots)):
            raise ValueError("dataset Shot keys must be sorted and unique")
        entry_keys = tuple(item.sort_key for item in self.entries)
        if entry_keys != tuple(sorted(entry_keys)):
            raise ValueError("dataset entries must use canonical order")
        hashes = tuple(item.record.file_sha256 for item in self.entries)
        if len(hashes) != len(set(hashes)):
            raise ValueError("dataset record pointers must be unique")
        _require_sorted_safe_ids(self.coverage_tags, "dataset coverage tags")
        if self.cohort.pilot_id != self.pilot_id or self.roster.pilot_id != self.pilot_id:
            raise ValueError("dataset pointer pilot identities must match")
        return self
