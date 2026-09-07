"""Immutable evidence for explicitly closing a known generated-media failure."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

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

    schema_version: Literal["generation-quality-rejection/1"] = (
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
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _exact_quality_failure(self) -> "GenerationQualityRejectionReceipt":
        if self.diagnosis.failure_classes != ("QUALITY_FAILURE",):
            raise ValueError("quality rejection requires exactly QUALITY_FAILURE")
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
