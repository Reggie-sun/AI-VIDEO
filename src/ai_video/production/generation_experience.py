"""Versioned, source-bound empirical cohorts, independent of exact recipe hashes.

These estimates describe observed whole-result outcomes, not calibrated model
probabilities. No development record, RAG index, or learning document is read.
"""

from __future__ import annotations

from math import sqrt
from typing import Literal, TYPE_CHECKING

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.generation_diagnosis import AttemptEvidence, diagnose_exact_result
from ai_video.production.generation_evaluation import GenerationEvaluationSource
from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import VerifiedGenerationRequirementProjection

if TYPE_CHECKING:
    from ai_video.production.generation_decision import GenerationCandidate


class GenerationFeatures(StrictModel):
    version: Literal["generation-features/1"] = "generation-features/1"
    character_count: int = Field(ge=0)
    motion_requirement: str
    camera_movement: str | None
    camera_amplitude: str | None
    dialogue_length_band: str
    dialogue_window_band: str
    reference_structure: tuple[str, ...]
    continuity: str
    identity_preservation: str
    audio_need: str
    duration_band: str
    output_geometry: tuple[int | None, int | None, float | None]
    # Free-text action complexity/hand contact cannot be inferred reliably by
    # this deterministic extractor. Unknown is not evidence of a simple Shot.
    unknown_features: tuple[str, ...] = ("action_complexity", "hand_prop_interaction")


def _band(value, boundaries):
    if value is None:
        return "unknown"
    return str(sum(value > boundary for boundary in boundaries))


def extract_generation_features(projection) -> GenerationFeatures:
    projection = VerifiedGenerationRequirementProjection.model_validate(
        projection.model_dump(mode="python"))
    requirement = projection.requirement
    intent = requirement.generation_intent
    camera = intent.primary_camera_motion
    dialogue = intent.dialogue_intent
    text = dialogue.verbatim_text if dialogue is not None else None
    window = (dialogue.end_seconds - dialogue.start_seconds
              if dialogue is not None and dialogue.end_seconds is not None
              and dialogue.start_seconds is not None else None)
    return GenerationFeatures(
        character_count=len(requirement.characters),
        motion_requirement=requirement.motion_requirement.value,
        camera_movement=camera.movement_kind.value if camera else None,
        camera_amplitude=camera.amplitude_class.value if camera else None,
        dialogue_length_band=("none" if dialogue is not None and dialogue.mode == "none"
                              else _band(len(text) if text else None, (12, 30, 60))),
        dialogue_window_band=_band(window, (2, 4, 8)),
        reference_structure=tuple(sorted(role.value for role in requirement.semantic_reference_roles)),
        continuity=requirement.continuity_mode.value,
        identity_preservation=intent.identity_continuity.preservation.value,
        audio_need=requirement.audio_need.value,
        duration_band=_band(
            requirement.output_need.duration_seconds
            if requirement.output_need.duration_seconds is not None else
            requirement.output_need.frame_count / requirement.output_need.fps
            if requirement.output_need.frame_count is not None and requirement.output_need.fps else None,
            (3, 5, 10)),
        output_geometry=(requirement.output_need.width, requirement.output_need.height,
                         requirement.output_need.fps),
    )


class GenerationExperience(StrictModel):
    """An evaluator projection joined to its verified historical authoring input."""

    projection: VerifiedGenerationRequirementProjection
    candidate: "GenerationCandidate"
    evidence: tuple[AttemptEvidence, ...] = Field(min_length=1)
    evaluation_sources: tuple[GenerationEvaluationSource, ...] = ()

    @model_validator(mode="after")
    def _source_identity(self):
        requirement = self.projection.requirement
        facts_hash = canonical_sha256(requirement.model_dump(
            mode="json", exclude={"requirement_id", "requirement_hash"}))
        if self.candidate.recipe.requirement_hash != requirement.requirement_hash:
            raise ValueError("experience candidate is not bound to its historical requirement")
        if any(e.recipe_scope_hash != self.candidate.scope_hash
               or e.facts_hash != facts_hash
               or e.rubric_hash != self.candidate.recipe.rubric_hash
               or e.shot_id != requirement.target_shot.shot_id for e in self.evidence):
            raise ValueError("experience evidence does not match its exact source")
        return self

    @property
    def features(self):
        return extract_generation_features(self.projection)


class EmpiricalEstimate(StrictModel):
    version: Literal["generation-cohort/1"] = "generation-cohort/1"
    supported_artifacts: tuple[str, ...] = ()
    failed_artifacts: tuple[str, ...] = ()
    incomplete_artifacts: tuple[str, ...] = ()
    evidence_hashes: tuple[str, ...] = ()
    exclusions: tuple[tuple[str, str], ...] = ()
    failed_requirements: tuple[str, ...] = ()
    observed_success_fraction: float | None = None
    interval_95: tuple[float, float] | None = None
    limitations: tuple[str, ...] = (
        "observational cohort; selection and intervention confounding remain",
        "unknown action complexity and hand/prop interaction are not matched",
        "interval is binomial sampling uncertainty, not causal or calibrated prediction",
    )


def empirical_assessment(candidate, features, experiences) -> EmpiricalEstimate:
    """Compare only same Provider/model/mode and acceptance-owner rubric."""
    accepted, rejected, incomplete, hashes, failed_ids = set(), set(), set(), set(), set()
    exclusions = []
    variant = next(v for v in candidate.capabilities.variants
                   if v.capability_id == candidate.capability_id)
    all_evidence = tuple(entry for experience in experiences for entry in experience.evidence)
    for experience in experiences:
        old = experience.candidate
        old_variant = next(v for v in old.capabilities.variants if v.capability_id == old.capability_id)
        reason = None
        if (old.capabilities.provider_name != candidate.capabilities.provider_name
                or old_variant.model_id != variant.model_id):
            reason = "provider_or_model"
        elif (old_variant.mode != variant.mode
              or old_variant.provider_kind != variant.provider_kind
              or old_variant.profile_version != variant.profile_version):
            reason = "generation_strategy"
        elif old.recipe.rubric_hash != candidate.recipe.rubric_hash:
            reason = "unmapped_acceptance_rubric"
        elif features is None or experience.features != features:
            reason = "feature_cohort"
        for entry in experience.evidence:
            if reason or entry.outcome != "media" or entry.stage != "raw_generation":
                exclusions.append((entry.evidence_hash, reason or "not_raw_media"))
                continue
            hashes.add(entry.evidence_hash)
            diagnosis = diagnose_exact_result(entry, all_evidence, old.recipe)
            if "QUALITY_FAILURE" in diagnosis.failure_classes:
                rejected.add(entry.artifact_sha256)
                failed_ids.update(diagnosis.failed_requirements)
            elif diagnosis.all_required_observed_pass:
                accepted.add(entry.artifact_sha256)
            else:
                incomplete.add(entry.artifact_sha256)
    accepted -= rejected | incomplete
    incomplete -= rejected
    count = len(accepted | rejected)
    fraction, interval = None, None
    if count:
        fraction = len(accepted) / count
        z2 = 1.96 ** 2
        center = (fraction + z2 / (2 * count)) / (1 + z2 / count)
        margin = 1.96 * sqrt(fraction * (1 - fraction) / count + z2 / (4 * count ** 2)) / (1 + z2 / count)
        interval = (max(0., center - margin), min(1., center + margin))
    return EmpiricalEstimate(
        supported_artifacts=tuple(sorted(accepted)), failed_artifacts=tuple(sorted(rejected)),
        incomplete_artifacts=tuple(sorted(incomplete)), evidence_hashes=tuple(sorted(hashes)),
        exclusions=tuple(sorted(set(exclusions))), failed_requirements=tuple(sorted(failed_ids)),
        observed_success_fraction=fraction, interval_95=interval,
    )


# Late model binding avoids importing the Router policy while it imports these
# independent contracts. The common caller completes this once both are loaded.
def bind_experience_models(candidate_type):
    GenerationExperience.model_rebuild(_types_namespace={"GenerationCandidate": candidate_type})
