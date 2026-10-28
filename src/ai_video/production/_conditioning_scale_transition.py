"""Exact prospective FL2VA scale-change review; never a media acceptance receipt."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Literal

from pydantic import Field, field_validator, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel

if TYPE_CHECKING:
    from ai_video.production.video_requirement import GenerationIntent

_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"
_FINDING_SOURCES = {
    "anchor_correspondence": "anchor_geometry_review",
    "scale_fov_continuity": "trajectory",
    "duration_reachable": "trajectory",
    "continuous_camera_path": "trajectory",
}


class ScaleTransitionSource(StrictModel):
    source_id: str = Field(pattern=_SAFE_ID)
    kind: Literal["anchor_geometry_review", "trajectory", "proxy"]
    evidence_ref: str = Field(pattern=_SAFE_ID)
    sha256: str = Field(pattern=_SHA256)


class ScaleTransitionFinding(StrictModel):
    finding_id: Literal[
        "anchor_correspondence", "scale_fov_continuity",
        "duration_reachable", "continuous_camera_path",
    ]
    verdict: Literal["PASS", "FAIL", "NOT_EVALUATED"]
    rationale: str = Field(min_length=1)
    source_ids: tuple[str, ...] = Field(min_length=1)

    @field_validator("rationale")
    @classmethod
    def _nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("scale-transition rationale must not be blank")
        return value

    @field_validator("source_ids")
    @classmethod
    def _ordered_sources(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("finding source IDs must be unique")
        return tuple(sorted(values))


def scale_transition_camera_intent_hash(intent: GenerationIntent) -> str:
    """Bind existing camera/space/timing facts without deriving another timeline."""
    fields = (
        "camera_intent", "camera_endpoint", "primary_camera_motion",
        "camera_subject_relation", "motion_envelope", "space_continuity",
        "axis_continuity", "pacing",
    )
    return canonical_sha256({
        "schema": "conditioning-scale-transition-camera/1",
        **{name: None if (value := getattr(intent, name)) is None
           else value.model_dump(mode="json") for name in fields},
    })


class ScaleTransitionEvidence(StrictModel):
    schema_version: Literal["conditioning-scale-transition/1"] = "conditioning-scale-transition/1"
    first_anchor_id: str = Field(pattern=_SAFE_ID)
    first_anchor_sha256: str = Field(pattern=_SHA256)
    last_anchor_id: str = Field(pattern=_SAFE_ID)
    last_anchor_sha256: str = Field(pattern=_SHA256)
    camera_intent_hash: str = Field(pattern=_SHA256)
    available_duration_seconds: float = Field(gt=0, allow_inf_nan=False)
    sources: tuple[ScaleTransitionSource, ...] = Field(min_length=2)
    findings: tuple[ScaleTransitionFinding, ...]
    content_hash: str = Field(pattern=_SHA256)

    @field_validator("sources")
    @classmethod
    def _ordered_sources(cls, values):
        if len({item.source_id for item in values}) != len(values):
            raise ValueError("scale-transition source IDs must be unique")
        return tuple(sorted(values, key=lambda item: item.source_id))

    @field_validator("findings")
    @classmethod
    def _ordered_findings(cls, values):
        if len(values) != 4 or {item.finding_id for item in values} != set(_FINDING_SOURCES):
            raise ValueError("scale-transition requires all four unique findings")
        return tuple(sorted(values, key=lambda item: item.finding_id))

    @model_validator(mode="after")
    def _validate_review(self):
        sources = {item.source_id: item for item in self.sources}
        kinds = {item.kind for item in self.sources}
        if not {"anchor_geometry_review", "trajectory"}.issubset(kinds):
            raise ValueError("scale-transition needs exact anchor review and trajectory sources")
        for finding in self.findings:
            if not set(finding.source_ids).issubset(sources):
                raise ValueError("finding references an unknown source ID")
            if _FINDING_SOURCES[finding.finding_id] not in {
                sources[key].kind for key in finding.source_ids
            }:
                raise ValueError("finding lacks its required review source kind")
        if self.content_hash != canonical_sha256(self):
            raise ValueError("scale-transition content_hash does not match exact evidence")
        return self

    @classmethod
    def create(cls, **values: object) -> ScaleTransitionEvidence:
        data = dict(values)
        data["sources"] = tuple(sorted(
            (ScaleTransitionSource.model_validate(item) for item in data.get("sources", ())),
            key=lambda item: item.source_id,
        ))
        data["findings"] = tuple(sorted(
            (ScaleTransitionFinding.model_validate(item) for item in data.get("findings", ())),
            key=lambda item: item.finding_id,
        ))
        data["content_hash"] = "0" * 64
        candidate = cls.model_construct(**data)
        data["content_hash"] = canonical_sha256(candidate)
        return cls.model_validate(data)


def validate_scale_transition_binding(
    evidence: ScaleTransitionEvidence,
    *,
    first_anchor_id: str,
    last_anchor_id: str | None,
    available_duration_seconds: float,
    generation_intent: GenerationIntent | None,
    output_duration_seconds: float | None,
) -> tuple[str, ...]:
    """Reopen copied/nested evidence and bind it to the current prospective input."""
    from pydantic import ValidationError

    prefix = "conditioning_compatibility.scale_transition"
    try:
        current = ScaleTransitionEvidence.model_validate(evidence.model_dump(mode="json"))
    except (ValidationError, AttributeError, TypeError):
        return (f"{prefix}.content_hash",)
    diagnostics = []
    if (current.first_anchor_id, current.last_anchor_id) != (first_anchor_id, last_anchor_id):
        diagnostics.append(f"{prefix}.anchor_ids")
    if generation_intent is None or current.camera_intent_hash != scale_transition_camera_intent_hash(generation_intent):
        diagnostics.append(f"{prefix}.camera_intent_hash")
    motion = None if generation_intent is None else generation_intent.primary_camera_motion
    if motion is None or motion.movement_kind == "locked":
        diagnostics.append(f"{prefix}.primary_camera_motion")
    intent_duration = None if generation_intent is None else generation_intent.pacing.shot_duration_seconds
    if any(duration is None or not math.isfinite(duration)
           or abs(duration-current.available_duration_seconds) > 1e-6
           for duration in (available_duration_seconds, intent_duration, output_duration_seconds)):
        diagnostics.append(f"{prefix}.available_duration_seconds")
    if any(finding.verdict != "PASS" for finding in current.findings):
        diagnostics.append(f"{prefix}.findings")
    return tuple(diagnostics)
