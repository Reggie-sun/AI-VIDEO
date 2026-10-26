"""Exact model/mode retarget authority for one known fetched video result."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.final_output_contracts import FinalOutputContract
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ProjectSnapshotPointer
from ai_video.production._shot_router_contracts import AdapterCompilerContract
from ai_video.production.video import (
    ProviderProfilePointer,
    VideoGenerationMode,
    VideoImageReferenceBinding,
)
from ai_video.production.video_contracts import (
    VideoFlexibleOutputRequirement,
    VideoMediaReferenceBinding,
)
from ai_video.production.video_requirement import GenerationIntent


_SHA256 = r"^[0-9a-f]{64}$"


class AuthoredGenerationRetargetTarget(StrictModel):
    """Sealed /5 target whose complete multimodal inputs are immutable."""

    schema_version: Literal["authored-generation-retarget/1"] = "authored-generation-retarget/1"
    task_id: str = Field(min_length=1)
    shot_id: str = Field(min_length=1)
    intent: GenerationIntent
    acceptance: DomainAcceptancePolicy
    output_requirement: VideoFlexibleOutputRequirement
    provider_name: str = Field(min_length=1)
    provider_kind: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    provider_profile: ProviderProfilePointer
    capability_id: str = Field(min_length=1)
    capabilities_fingerprint: str = Field(pattern=_SHA256)
    compiler_contract: AdapterCompilerContract
    execution_stack_hash: str | None = Field(default=None, pattern=_SHA256)
    mode: Literal[VideoGenerationMode.REFERENCE_TO_VIDEO] = VideoGenerationMode.REFERENCE_TO_VIDEO
    target_project: ProjectSnapshotPointer
    image_bindings: tuple[VideoImageReferenceBinding, ...] = Field(min_length=1)
    media_bindings: tuple[VideoMediaReferenceBinding, ...] = ()
    authorization_reference: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _verify_seal(self) -> "AuthoredGenerationRetargetTarget":
        if not self.authorization_reference.strip() or not self.rationale.strip():
            raise ValueError("authored retarget needs an explicit authority reference and rationale")
        if any(item.role != "reference" for item in self.image_bindings):
            raise ValueError("authored reference-to-video targets may bind only reference images")
        image_keys = tuple(item.asset_id for item in self.image_bindings)
        if image_keys != tuple(sorted(set(image_keys))):
            raise ValueError("authored image references must use unique canonical asset order")
        media_keys = tuple((item.role, item.asset_id) for item in self.media_bindings)
        if media_keys != tuple(sorted(set(media_keys))):
            raise ValueError("authored media references must use unique canonical asset order")
        if not self.image_bindings and not self.media_bindings:
            raise ValueError("authored reference-to-video target needs exact reference inputs")
        if self.content_hash != canonical_sha256(self.model_dump(mode="json", exclude={"content_hash"})):
            raise ValueError("authored retarget target content hash is invalid")
        return self

    @classmethod
    def create(cls, **values) -> "AuthoredGenerationRetargetTarget":
        data = dict(values)
        for key in ("authorization_reference", "rationale"):
            if isinstance(data.get(key), str):
                data[key] = data[key].strip()
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"content_hash"})
        )
        return cls.model_validate(data).verify()

    def verify(self) -> "AuthoredGenerationRetargetTarget":
        return type(self).model_validate_json(self.model_dump_json())


def _source_candidate(experience):
    candidate = experience.candidate
    variants = tuple(item for item in candidate.capabilities.variants
                     if item.capability_id == candidate.capability_id)
    if len(variants) != 1:
        raise ValueError("retarget source must retain one exact selected capability")
    return candidate, variants[0]


def _validate_target_against_source(*, source_request, task_id, shot_id, experience,
                                   target: AuthoredGenerationRetargetTarget) -> None:
    target = target.verify()
    candidate, variant = _source_candidate(experience)
    if (
        target.task_id != task_id
        or target.shot_id != shot_id
        or target.provider_name != candidate.capabilities.provider_name
        or target.provider_kind != variant.provider_kind
        or target.model_id == variant.model_id
    ):
        raise ValueError("authored retarget must preserve task, Shot, Provider and kind while selecting a new model")
    if source_request.base_project is None or target.target_project.revision != source_request.base_project.revision + 1:
        raise ValueError("authored retarget Project must advance the exact source snapshot by one revision")
    if not experience.evidence:
        raise ValueError("authored retarget needs the exact retained fetched evaluation")
    evidence = experience.evidence[-1]
    if (
        evidence.outcome != "media"
        or evidence.artifact_sha256 is None
        or not any(item.verdict == "FAIL" for item in evidence.findings)
        or evidence.request_hash != source_request.request_input_hash
        or evidence.task_id != task_id
        or evidence.shot_id != shot_id
        or evidence.recipe_scope_hash != candidate.scope_hash
        or evidence.rubric_hash != candidate.recipe.rubric_hash
    ):
        raise ValueError("authored retarget must retain the exact known fetched Shot evaluation")
    if target.acceptance != candidate.recipe.acceptance_policy:
        raise ValueError("authored retarget cannot change the selected QA acceptance contract")
    if target.intent == experience.projection.requirement.generation_intent:
        raise ValueError("authored retarget must change the exact failed Shot intent")


def validate_authored_generation_retarget_target(
    old_binding, experience, target: AuthoredGenerationRetargetTarget,
) -> None:
    """Bind a typed target to one exact source attempt and current task/Shot."""
    if not isinstance(target, AuthoredGenerationRetargetTarget):
        raise ValueError("authored retarget target must be the sealed typed contract")
    target.verify()
    if experience.projection != old_binding.projection:
        raise ValueError("authored retarget does not bind the exact prior requirement projection")
    if experience.candidate.final_output_goal is None:
        raise ValueError("authored retarget source needs its complete final-output goal")
    request = old_binding.compiled_request.activation_scope.request
    if request.base_project is None:
        raise ValueError("authored retarget source request has no exact base Project")
    if request.target_shot_id != old_binding.context.target_shot_id:
        raise ValueError("authored retarget source request changed the target Shot")
    _validate_target_against_source(
        source_request=request,
        task_id=old_binding.inputs.limits.task_id,
        shot_id=old_binding.context.target_shot_id,
        experience=experience,
        target=target,
    )


def _same_goal_with_new_version(old: FinalOutputContract, new: FinalOutputContract) -> bool:
    return (
        old.goal_id == new.goal_id
        and old.goal_version != new.goal_version
        and old.model_dump(mode="json", exclude={"goal_version"})
        == new.model_dump(mode="json", exclude={"goal_version"})
    )


def validate_authored_generation_retarget_binding(
    binding, selected, target: AuthoredGenerationRetargetTarget, *, target_goal,
    authorization_receipt_id: str,
) -> None:
    """Match the compiled /5 request, all inputs and the advanced unchanged goal."""
    target = target.verify()
    if target.authorization_reference != authorization_receipt_id:
        raise ValueError("retarget target must cite the exact authorization receipt")
    experiences = tuple(binding.inputs.experiences)
    latest = next((item for item in binding.inputs.evidence
                   if item.evidence_hash == binding.inputs.latest_attempt_hash), None)
    source_experiences = tuple(item for item in experiences
                               if latest is not None and latest in item.evidence)
    if latest is None or len(source_experiences) != 1:
        raise ValueError("retarget successor must retain one exact prior goal experience")
    experience = source_experiences[0]
    baseline = binding.inputs.baseline_request
    if baseline is None:
        raise ValueError("retarget successor must retain the exact source request")
    _validate_target_against_source(
        source_request=baseline,
        task_id=binding.inputs.limits.task_id,
        shot_id=binding.context.target_shot_id,
        experience=experience,
        target=target,
    )
    if (
        any(item.outcome == "unknown_outcome" for item in binding.inputs.evidence)
        or binding.inputs.limits.paid_submits_used < 1
        or binding.inputs.limits.paid_submit_ceiling != binding.inputs.limits.paid_submits_used + 1
        or binding.inputs.policy.max_resamples != 0
        or binding.decision.runtime_repair is not None
        or binding.decision.intervention is not None
    ):
        raise ValueError("retarget successor exceeds one known, finite authored submit")
    if not _same_goal_with_new_version(experience.candidate.final_output_goal, target_goal):
        raise ValueError("retarget goal must preserve all existing requirements and advance only its version")
    request = binding.compiled_request.activation_scope.request
    requirement = binding.projection.requirement
    variants = tuple(item for item in selected.capabilities.variants
                     if item.capability_id == selected.capability_id)
    if len(variants) != 1:
        raise ValueError("retarget successor capability must be exact")
    variant = variants[0]
    if (
        variant.output_capability is None
        or not variant.output_capability.supports(target.output_requirement)
        or "reference" not in variant.allowed_image_roles
        or len(target.image_bindings) > variant.max_reference_count
        or any(item.role not in variant.allowed_image_roles for item in target.image_bindings)
    ):
        raise ValueError("authored retarget inputs or output exceed the exact selected capability")
    from ai_video.production.video_contracts import media_bindings_satisfy_capabilities

    if not media_bindings_satisfy_capabilities(target.media_bindings, variant.media_capabilities):
        raise ValueError("authored retarget media references exceed the exact selected capability")
    resolved = binding.compiled_request
    if (
        binding.inputs.limits.task_id != target.task_id
        or binding.context.target_shot_id != target.shot_id
        or requirement.generation_intent != target.intent
        or selected.recipe.acceptance_policy != target.acceptance
        or selected.output_requirement != target.output_requirement
        or request.output_requirement != target.output_requirement
        or resolved.effective_output != target.output_requirement
        or selected.capabilities.provider_name != target.provider_name
        or variant.provider_kind != target.provider_kind
        or variant.model_id != target.model_id
        or selected.provider_profile != target.provider_profile
        or selected.capabilities.capabilities_fingerprint != target.capabilities_fingerprint
        or selected.capability_id != target.capability_id
        or selected.compiler_contract != target.compiler_contract
        or resolved.execution_stack_hash != target.execution_stack_hash
        or variant.mode is not target.mode
        or resolved.provider_name != target.provider_name
        or resolved.provider_kind != target.provider_kind
        or resolved.model_id != target.model_id
        or resolved.provider_profile != target.provider_profile
        or resolved.capability_id != target.capability_id
        or resolved.mode is not target.mode
        or resolved.adapter_compiler_id != target.compiler_contract.compiler_id
        or resolved.adapter_compiler_version != target.compiler_contract.compiler_version
        or resolved.adapter_compiler_hash != target.compiler_contract.compiler_hash
        or request.execution_stack_hash != target.execution_stack_hash
        or request.provider_name != target.provider_name
        or request.provider_kind != target.provider_kind
        or request.model_id != target.model_id
        or request.provider_profile != target.provider_profile
        or request.mode is not target.mode
        or request.adapter_compiler_id != target.compiler_contract.compiler_id
        or request.adapter_compiler_version != target.compiler_contract.compiler_version
        or request.adapter_compiler_hash != target.compiler_contract.compiler_hash
        or request.base_project != target.target_project
        or request.image_bindings != target.image_bindings
        or request.media_bindings != target.media_bindings
        or selected.final_output_goal != target_goal
    ):
        raise ValueError("compiled multimodal retarget differs from its sealed exact target")


