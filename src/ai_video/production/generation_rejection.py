"""Immutable evidence for explicitly closing a known generated-media failure."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_serializer, model_validator

from ai_video.production.artifact_contracts import QaPolicyPointer, StrictModel
from ai_video.production.generation_diagnosis import Diagnosis, diagnose_exact_result
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity


_SHA256 = r"^[0-9a-f]{64}$"


class GenerationQualityRejectionReceipt(StrictModel):
    """A terminal quality decision over exact already-fetched bytes.

    It is not Provider failure, settlement, candidate activation, or a retry
    permit.  The committer is the only writer of this receipt.
    """

    schema_version: Literal["generation-quality-rejection/1", "generation-quality-rejection/2"] = (
        "generation-quality-rejection/1"
    )
    attempt_id: str = Field(min_length=1)
    actor: ActorIdentity
    request_fingerprint: str = Field(pattern=_SHA256)
    artifact_sha256: str = Field(pattern=_SHA256)
    artifact_size_bytes: int = Field(strict=True, gt=0)
    experience_content_hash: str = Field(pattern=_SHA256)
    evidence_hash: str = Field(pattern=_SHA256)
    qa_policy: QaPolicyPointer
    expected_manifest_revision: int = Field(strict=True, ge=0)
    diagnosis: Diagnosis
    abandonment_reason: str | None = None
    unresolved_requirements: tuple[str, ...] = ()
    content_hash: str = Field(pattern=_SHA256)

    @model_serializer(mode="wrap")
    def _serialize(self, handler):
        data = handler(self)
        if self.abandonment_reason is None:
            data.pop("abandonment_reason", None)
        if not self.unresolved_requirements:
            data.pop("unresolved_requirements", None)
        return data

    @model_validator(mode="after")
    def _exact_quality_failure(self) -> "GenerationQualityRejectionReceipt":
        if self.schema_version == "generation-quality-rejection/1":
            if self.diagnosis.failure_classes != ("QUALITY_FAILURE",):
                raise ValueError("quality rejection requires exactly QUALITY_FAILURE")
            if self.abandonment_reason is not None or self.unresolved_requirements:
                raise ValueError("historical quality rejection cannot declare abandonment")
        elif (self.diagnosis.failure_classes != ("EVIDENCE_GAP", "QUALITY_FAILURE")
              or not self.diagnosis.failed_requirements
              or self.diagnosis.all_required_observed_pass
              or not self.abandonment_reason or not self.abandonment_reason.strip()
              or not self.unresolved_requirements
              or tuple(sorted(set(self.unresolved_requirements))) != self.unresolved_requirements):
            raise ValueError("abandonment requires a known quality failure with unresolved evidence")
        if self.evidence_hash not in self.diagnosis.evidence_hashes:
            raise ValueError("quality rejection diagnosis omits its exact evidence")
        if self.content_hash != canonical_sha256(self.model_dump(mode="json")):
            raise ValueError("quality rejection receipt content hash is invalid")
        return self

    @property
    def qa_policy_content_hash(self) -> str:
        """Compatibility view of the sealed evaluation-time policy identity."""
        return self.qa_policy.content_hash

    @classmethod
    def create(cls, **values: object) -> "GenerationQualityRejectionReceipt":
        data = dict(values)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(provisional.model_dump(mode="json"))
        return cls.model_validate(data)


def validate_quality_rejection_experience(
    *, binding, experience, evidence, request, attempt_id: str, artifact_sha256: str,
    qa_policy, history: tuple,
):
    """Validate the original decision joins shared by close and strict replay."""
    selected = next(
        (
            item for item in binding.inputs.candidates
            if item.candidate_id == binding.decision.selected_candidate_id
        ),
        None,
    )
    if (
        selected is None
        or experience.projection != binding.projection
        or experience.candidate != selected
        or evidence.attempt_id != attempt_id
        or evidence.request_hash != request.request_input_hash
        or evidence.outcome != "media"
        or evidence.artifact_sha256 != artifact_sha256
        or evidence.task_id != binding.inputs.limits.task_id
        or evidence.shot_id != binding.context.target_shot_id
        or evidence.recipe_scope_hash != selected.scope_hash
        or evidence.facts_hash != binding.inputs.facts_hash
        or evidence.rubric_hash != selected.recipe.rubric_hash
    ):
        raise ValueError("quality rejection evidence does not match its execution binding")
    intervention = binding.decision.intervention
    if intervention is None:
        if (
            evidence.intervention_id is not None
            or evidence.intervention_semantic_hash is not None
            or evidence.actual_delta
        ):
            raise ValueError("quality rejection evidence invents an intervention")
    elif (
        evidence.intervention_id != intervention.intervention_id
        or evidence.intervention_semantic_hash != intervention.semantic_hash
        or set(evidence.actual_delta) != set(intervention.changed_variables)
    ):
        raise ValueError("quality rejection evidence does not match its intervention")
    from ai_video.production.generation_evaluation import (
        validate_generation_evaluation_sources,
    )

    validate_generation_evaluation_sources(
        sources=experience.evaluation_sources,
        evidence=evidence,
        qa_policy=qa_policy,
    )
    return diagnose_exact_result(evidence, history, experience.candidate.recipe)


def unresolved_generation_requirements(evidence, history, recipe) -> tuple[str, ...]:
    """Retain explicitly unobservable requirements; missing proof is not exhaustion."""
    diagnosis = diagnose_exact_result(evidence, history, recipe)
    exact_hashes = set(diagnosis.evidence_hashes)
    findings = tuple(f for e in (*history, evidence) if e.evidence_hash in exact_hashes
                     for f in e.findings)
    unresolved = []
    for rule in recipe.expressions:
        if rule.level != "acceptance" or rule.stage != evidence.stage:
            continue
        observed = tuple(f for f in findings if f.requirement_id == rule.requirement_id
                         and f.proof == rule.proof and f.stage == rule.stage
                         and f.rubric_hash == recipe.rubric_hash)
        if not observed:
            raise ValueError("abandonment requires explicit observations for every applicable requirement")
        if all(f.verdict == "NOT_EVALUATED" for f in observed):
            unresolved.append(rule.requirement_id)
    return tuple(sorted(unresolved))


def validate_abandoned_result(receipt, *, experience, evidence, history) -> None:
    """Pure exact-result join; persisted terminal authority is checked at execution."""
    receipt = GenerationQualityRejectionReceipt.model_validate(receipt.model_dump(mode="python"))
    if (receipt.schema_version != "generation-quality-rejection/2"
            or receipt.attempt_id != evidence.attempt_id
            or receipt.request_fingerprint != evidence.request_hash
            or receipt.artifact_sha256 != evidence.artifact_sha256
            or receipt.evidence_hash != evidence.evidence_hash
            or receipt.experience_content_hash != canonical_sha256(experience.model_dump(mode="json"))
            or evidence not in experience.evidence
            or receipt.diagnosis != diagnose_exact_result(evidence, history, experience.candidate.recipe)
            or receipt.unresolved_requirements != unresolved_generation_requirements(
                evidence, history, experience.candidate.recipe)):
        raise ValueError("abandoned result differs from exact latest evidence")
