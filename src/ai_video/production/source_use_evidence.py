"""Immutable source-window qualification records for production strategies."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Literal, Protocol

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel, ToolIdentity
from ai_video.production.hashing import canonical_sha256
from ai_video.production.composition_contracts import FixedTransform


class _QaPolicyLike(Protocol):
    domain_acceptance: object | None
    production_source_evidence: tuple["SourceUseEvidence", ...]
    semantic_authorities: tuple[ToolIdentity, ...]
    generation_evaluation_authorities: tuple[object, ...]

    def selected_generation_acceptance(self) -> object | None: ...


class SourceUseEvidence(StrictModel):
    """One evaluator's unmodified evidence for one exact source use."""

    evidence_id: str = Field(min_length=1)
    parent_shot_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    task_id: str = Field(min_length=1)
    acceptance_profile_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    component_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0)
    role: str = Field(min_length=1)
    timebase: Literal["frames", "samples", "still"]
    start: int = Field(ge=0)
    duration: int = Field(gt=0)
    evaluator: ToolIdentity
    proof: Literal["technical", "analyzer", "human"]
    response_json: str = Field(min_length=1)
    transform: FixedTransform = Field(default_factory=FixedTransform)
    opacity_milli: int = Field(default=1000, ge=0, le=1000)
    z_index: int = 0

    @model_validator(mode="after")
    def _validate_original_response(self) -> "SourceUseEvidence":
        try:
            response = json.loads(self.response_json)
        except json.JSONDecodeError as exc:
            raise ValueError("Source-use response JSON is invalid") from exc
        if not isinstance(response, Mapping):
            raise ValueError("Source-use response JSON must be an object")
        expected = {
            "parent_shot_content_hash": self.parent_shot_content_hash,
            "task_id": self.task_id,
            "acceptance_profile_hash": self.acceptance_profile_hash,
            "component_id": self.component_id,
            "asset_id": self.asset_id,
            "asset_sha256": self.asset_sha256,
            "size_bytes": self.size_bytes,
            "role": self.role,
            "timebase": self.timebase,
            "start": self.start,
            "duration": self.duration,
            "evaluator": self.evaluator.model_dump(mode="json"),
            "proof": self.proof,
        }
        for key, value, default in (
            ("transform", self.transform.model_dump(mode="json"), FixedTransform().model_dump(mode="json")),
            ("opacity_milli", self.opacity_milli, 1000), ("z_index", self.z_index, 0),
        ):
            if value != default or key in response:
                expected[key] = value
        if any(response.get(key) != value for key, value in expected.items()):
            raise ValueError("Source-use response identity does not match evidence")
        observations = response.get("observations")
        if not isinstance(observations, list) or not observations:
            raise ValueError("Source-use response needs nonempty observations")
        requirement_ids: list[str] = []
        for observation in observations:
            if not isinstance(observation, Mapping):
                raise ValueError("Source-use response observations must be objects")
            requirement_id = observation.get("requirement_id")
            if not isinstance(requirement_id, str) or not requirement_id.strip():
                raise ValueError("Source-use response requirement IDs must be nonblank")
            if observation.get("verdict") not in {"PASS", "FAIL", "NOT_EVALUATED"}:
                raise ValueError("Source-use response verdict is invalid")
            if not isinstance(observation.get("observation"), str) or not observation["observation"].strip():
                raise ValueError("Source-use response observations must be nonblank")
            requirement_ids.append(requirement_id)
        if len(set(requirement_ids)) != len(requirement_ids):
            raise ValueError("Source-use response requirement IDs must be unique")
        if self.proof == "human":
            for key in ("human_actor_id", "evidence_ref"):
                if not isinstance(response.get(key), str) or not response[key].strip():
                    raise ValueError(f"Human source-use response requires {key}")
        return self

    @property
    def evidence_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))

    @property
    def observations(self) -> tuple[tuple[str, Literal["PASS", "FAIL", "NOT_EVALUATED"]], ...]:
        response = json.loads(self.response_json)
        return tuple(
            (item["requirement_id"], item["verdict"])
            for item in response["observations"]
        )


def require_source_use_evidence_authority(
    qa_policy: _QaPolicyLike, evidence: SourceUseEvidence
) -> None:
    """Require an explicitly selected evaluator and proof kind for source use."""
    if evidence.evaluator not in qa_policy.semantic_authorities:
        raise ValueError("Source-use evidence evaluator is not policy-selected")
    if not any(
        getattr(authority, "evaluator", None) == evidence.evaluator
        and getattr(authority, "proof", None) == evidence.proof
        for authority in qa_policy.generation_evaluation_authorities
    ):
        raise ValueError("Source-use evidence proof mapping is not explicitly policy-selected")


def _current_acceptance(qa_policy: _QaPolicyLike):
    return (
        qa_policy.domain_acceptance
        if qa_policy.domain_acceptance is not None
        else qa_policy.selected_generation_acceptance()
    )


def _matches_use(
    evidence: SourceUseEvidence,
    *,
    parent_shot_content_hash: str,
    task_id: str,
    acceptance_profile_hash: str,
    component_id: str,
    asset_id: str,
    asset_sha256: str,
    size_bytes: int,
    role: str,
    timebase: Literal["frames", "samples", "still"],
    start: int,
    duration: int,
    transform: FixedTransform,
    opacity_milli: int,
    z_index: int,
) -> bool:
    return (
        evidence.parent_shot_content_hash == parent_shot_content_hash
        and evidence.task_id == task_id
        and evidence.acceptance_profile_hash == acceptance_profile_hash
        and evidence.component_id == component_id
        and evidence.asset_id == asset_id
        and evidence.asset_sha256 == asset_sha256
        and evidence.size_bytes == size_bytes
        and evidence.role == role
        and evidence.timebase == timebase
        and evidence.start == start
        and evidence.duration == duration
        and evidence.transform == transform
        and evidence.opacity_milli == opacity_milli
        and evidence.z_index == z_index
    )


def assess_source_use(
    *,
    qa_policy: _QaPolicyLike,
    parent_shot_content_hash: str,
    task_id: str,
    component_id: str,
    asset_id: str,
    asset_sha256: str,
    size_bytes: int,
    role: str,
    timebase: Literal["frames", "samples", "still"],
    start: int,
    duration: int,
    requirement_ids: Sequence[str],
    evidence_ids: Sequence[str],
    transform: FixedTransform | None = None,
    opacity_milli: int = 1000,
    z_index: int = 0,
) -> Literal["PASS", "FAIL", "NOT_EVALUATED"]:
    """Assess an exact use from all current evidence, never a caller-picked subset."""
    acceptance = _current_acceptance(qa_policy)
    if acceptance is None:
        raise ValueError("Source-use assessment requires a current acceptance policy")
    accepted_ids = set(getattr(acceptance, "required_requirement_ids"))
    requested_ids = tuple(requirement_ids)
    if not requested_ids or any(not item.strip() for item in requested_ids):
        raise ValueError("Source-use assessment requirement IDs must be nonblank")
    if len(set(requested_ids)) != len(requested_ids):
        raise ValueError("Source-use assessment requirement IDs must be unique")
    if not set(requested_ids) <= accepted_ids:
        raise ValueError("Source-use assessment requirements are not accepted by the current policy")

    all_evidence = tuple(qa_policy.production_source_evidence)
    evidence_by_id = {item.evidence_id: item for item in all_evidence}
    if len(evidence_by_id) != len(all_evidence):
        raise ValueError("Source-use evidence IDs must be unique")
    selected_ids = tuple(evidence_ids)
    if len(set(selected_ids)) != len(selected_ids):
        raise ValueError("Source-use selected evidence IDs must be unique")
    unknown_ids = set(selected_ids) - set(evidence_by_id)
    if unknown_ids:
        raise ValueError("Source-use assessment names unknown evidence IDs")

    expected = dict(
        parent_shot_content_hash=parent_shot_content_hash,
        task_id=task_id,
        acceptance_profile_hash=getattr(acceptance, "profile_content_hash"),
        component_id=component_id,
        asset_id=asset_id,
        asset_sha256=asset_sha256,
        size_bytes=size_bytes,
        role=role,
        timebase=timebase,
        start=start,
        duration=duration,
        transform=transform or FixedTransform(), opacity_milli=opacity_milli, z_index=z_index,
    )
    if any(not _matches_use(item, **expected) for item in (evidence_by_id[item_id] for item_id in selected_ids)):
        return "NOT_EVALUATED"
    matching = tuple(item for item in all_evidence if _matches_use(item, **expected))
    if not matching:
        return "NOT_EVALUATED"
    for evidence in matching:
        require_source_use_evidence_authority(qa_policy, evidence)

    observations: dict[str, list[Literal["PASS", "FAIL", "NOT_EVALUATED"]]] = {
        requirement_id: [] for requirement_id in requested_ids
    }
    payload = getattr(acceptance, "profile_payload")
    inventory = payload.get("source_use_requirements", payload.get("generation_requirements", ()))
    rules = {item["requirement_id"]: item for item in inventory}
    for evidence in matching:
        for requirement_id, verdict in evidence.observations:
            if requirement_id in observations:
                rule = rules.get(requirement_id)
                # Negative observations remain a veto; positive evidence cannot
                # substitute a weaker proof or an assembly-stage measurement.
                compatible = (rule is not None and rule.get("proof") == evidence.proof
                    and rule.get("stage") in {"source_use", "raw_generation"})
                if verdict == "FAIL" or compatible:
                    observations[requirement_id].append(verdict)
    if any("FAIL" in values for values in observations.values()):
        return "FAIL"
    if any("PASS" not in values for values in observations.values()):
        return "NOT_EVALUATED"
    return "PASS"
