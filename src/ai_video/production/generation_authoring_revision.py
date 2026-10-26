"""One sealed, same-provider/model authored successor for known fetched media."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from pydantic import Field, model_serializer, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.final_output_contracts import FinalOutputContract, FinalOutputRequirement
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ProjectSnapshotPointer
from ai_video.production._shot_router_contracts import AdapterCompilerContract
from ai_video.production.video import ProviderProfilePointer, VideoGenerationMode
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.video_requirement import GenerationIntent


_SHA256 = r"^[0-9a-f]{64}$"
_REVISED_RULE_FIELDS = frozenset({"observable", "tolerance", "measurement", "intent_paths"})
_RULE_IDENTITY_FIELDS = frozenset({
    "requirement_id", "level", "stage", "proof", "dimension", "production_owner",
})


class AuthoredGoalRequirementRevision(StrictModel):
    """One exact, user-authorized observable replacement inside a final-output goal."""

    requirement_id: str = Field(min_length=1)
    old_requirement: FinalOutputRequirement
    new_requirement: FinalOutputRequirement
    authorization_reference: str = Field(min_length=1)
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_pair(self) -> "AuthoredGoalRequirementRevision":
        if not self.requirement_id.strip() or not self.authorization_reference.strip() or not self.reason.strip():
            raise ValueError("goal requirement revision needs an authorization reference and reason")
        if (
            self.old_requirement.requirement_id != self.requirement_id
            or self.new_requirement.requirement_id != self.requirement_id
            or self.old_requirement.observable == self.new_requirement.observable
            or self.old_requirement.model_dump(mode="json", exclude={"observable"})
            != self.new_requirement.model_dump(mode="json", exclude={"observable"})
        ):
            raise ValueError("goal requirement revision must preserve every field except its observable")
        return self


class AuthoredGenerationRevisionTarget(StrictModel):
    """Exact prospective authoring target authorized after a known fetched Shot."""

    schema_version: Literal["authored-generation-revision/1"] = "authored-generation-revision/1"
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
    mode: VideoGenerationMode
    target_project: ProjectSnapshotPointer
    first_frame_sha256: str = Field(pattern=_SHA256)
    revised_requirement_ids: tuple[str, ...] = ()
    goal_requirement_revisions: tuple[AuthoredGoalRequirementRevision, ...] = ()
    rationale: str = Field(min_length=1)
    content_hash: str = Field(pattern=_SHA256)

    @model_serializer(mode="wrap")
    def _legacy_empty_goal_revisions(self, handler):
        data = handler(self)
        if not self.goal_requirement_revisions:
            data.pop("goal_requirement_revisions", None)
        return data

    @model_validator(mode="after")
    def _verify_seal(self) -> "AuthoredGenerationRevisionTarget":
        if not self.rationale.strip():
            raise ValueError("authored generation revision rationale must be nonblank")
        if any(not value.strip() for value in self.revised_requirement_ids):
            raise ValueError("revised requirement IDs must be nonblank")
        if len(set(self.revised_requirement_ids)) != len(self.revised_requirement_ids):
            raise ValueError("revised requirement IDs must be unique")
        goal_revision_ids = tuple(item.requirement_id for item in self.goal_requirement_revisions)
        if len(goal_revision_ids) != len(set(goal_revision_ids)):
            raise ValueError("final-output goal requirement revision IDs must be unique")
        if self.content_hash != canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        ):
            raise ValueError("authored generation revision target content hash is invalid")
        return self

    @classmethod
    def create(cls, **values) -> "AuthoredGenerationRevisionTarget":
        data = dict(values)
        if isinstance(data.get("rationale"), str):
            data["rationale"] = data["rationale"].strip()
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"content_hash"})
        )
        return cls.model_validate(data).verify()

    def verify(self) -> "AuthoredGenerationRevisionTarget":
        # Re-enter nested schemas so a model_copy(update=...) cannot smuggle
        # invalid target data past the immutable closure writer.
        return type(self).model_validate_json(self.model_dump_json())


def _raw_rules(acceptance: DomainAcceptancePolicy) -> dict[str, dict]:
    inventory = acceptance.profile_payload.get("generation_requirements")
    if not isinstance(inventory, list | tuple) or not inventory:
        raise ValueError("authored revision requires the exact raw generation rule inventory")
    rules: dict[str, dict] = {}
    for item in inventory:
        if not isinstance(item, Mapping):
            raise ValueError("raw generation rules must be mappings")
        rule = dict(item)
        identifier = rule.get("requirement_id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in rules:
            raise ValueError("raw generation requirement IDs must be unique and nonblank")
        rules[identifier] = rule
    return rules


def _validate_acceptance(old: DomainAcceptancePolicy, target: AuthoredGenerationRevisionTarget) -> None:
    new = target.acceptance
    if (
        new.domain_id != old.domain_id
        or new.profile_id != old.profile_id
        or new.measurement_contract_version != old.measurement_contract_version
    ):
        raise ValueError("authored revision must retain the selected QA domain, profile, and measurement contract")
    if not set(old.required_requirement_ids) <= set(new.required_requirement_ids):
        raise ValueError("authored revision cannot remove an existing required QA ID")

    old_profile = old.model_dump(mode="json")["profile_payload"]
    new_profile = new.model_dump(mode="json")["profile_payload"]
    for profile in (old_profile, new_profile):
        profile.pop("content_hash", None)
        profile.pop("profile_version", None)
        profile.pop("generation_requirements", None)
        profile.pop("required_requirement_ids", None)
    if old_profile != new_profile:
        raise ValueError("authored revision cannot change QA profile rules outside the raw inventory")

    old_rules = _raw_rules(old)
    new_rules = _raw_rules(new)
    if not set(old_rules) <= set(new_rules):
        raise ValueError("authored revision cannot remove an existing raw QA rule")
    raw_required = {
        requirement_id for requirement_id in old.required_requirement_ids
        if requirement_id in old_rules
        and old_rules[requirement_id].get("level") == "acceptance"
        and old_rules[requirement_id].get("stage") == "raw_generation"
    }
    revised = set(target.revised_requirement_ids)
    if not revised <= raw_required:
        raise ValueError("only existing raw-generation required IDs may be explicitly revised")
    for requirement_id, old_rule in old_rules.items():
        new_rule = new_rules[requirement_id]
        if old_rule == new_rule:
            continue
        if requirement_id not in revised:
            raise ValueError("unlisted raw QA rule changed during authored revision")
        if any(old_rule.get(key) != new_rule.get(key) for key in _RULE_IDENTITY_FIELDS):
            raise ValueError("authored revision cannot lower raw QA rule identity or proof obligations")
        fields = set(old_rule) | set(new_rule)
        if any(
            old_rule.get(key) != new_rule.get(key)
            for key in fields - _REVISED_RULE_FIELDS
        ):
            raise ValueError("explicit raw QA revision changed protected rule fields")
    added_required = set(new.required_requirement_ids) - set(old.required_requirement_ids)
    if any(
        requirement_id not in new_rules
        or new_rules[requirement_id].get("level") != "acceptance"
        or new_rules[requirement_id].get("stage") != "raw_generation"
        for requirement_id in added_required
    ):
        raise ValueError("new required QA IDs must identify raw-generation acceptance rules")


def _old_candidate(old_binding, experience):
    if experience.projection != old_binding.projection:
        raise ValueError("authored revision does not bind the exact prior requirement projection")
    selected_id = old_binding.decision.selected_candidate_id
    candidates = tuple(
        candidate for candidate in old_binding.inputs.candidates
        if candidate.candidate_id == selected_id
    )
    if len(candidates) != 1 or experience.candidate != candidates[0]:
        raise ValueError("authored revision does not bind the exact prior selected candidate")
    return candidates[0]


def validate_authored_generation_revision_target(
    old_binding, experience, target: AuthoredGenerationRevisionTarget
) -> None:
    """Validate one target against exact prior media and the same Provider/model."""
    if not isinstance(target, AuthoredGenerationRevisionTarget):
        raise ValueError("authored revision target must be the sealed typed contract")
    target.verify()
    old_candidate = _old_candidate(old_binding, experience)
    request = old_binding.compiled_request.activation_scope.request
    if target.task_id != old_binding.inputs.limits.task_id:
        raise ValueError("authored revision target changed the generation task")
    if target.shot_id != old_binding.context.target_shot_id:
        raise ValueError("authored revision target changed the Shot")
    if request.base_project is None or target.target_project.revision <= request.base_project.revision:
        raise ValueError("authored revision target must name a prospective later Project snapshot")
    first_frames = tuple(item for item in request.image_bindings if item.role == "first_frame")
    if len(first_frames) > 1:
        raise ValueError("prior request has an ambiguous first-frame endpoint")
    variants = tuple(
        variant for variant in old_candidate.capabilities.variants
        if variant.capability_id == old_candidate.capability_id
    )
    if len(variants) != 1:
        raise ValueError("prior selected capability is not exact")
    prior_variant = variants[0]
    if (
        target.provider_name != old_candidate.capabilities.provider_name
        or target.provider_kind != prior_variant.provider_kind
        or target.model_id != prior_variant.model_id
    ):
        raise ValueError("authored revision cannot change Provider or model")
    if target.mode is not VideoGenerationMode.IMAGE_TO_VIDEO:
        raise ValueError("single first-frame authored revision requires image-to-video mode")
    _validate_acceptance(old_candidate.recipe.acceptance_policy, target)
    if not experience.evidence:
        raise ValueError("authored revision requires retained prior media evidence")
    evidence = experience.evidence[-1]
    if (
        evidence.outcome != "media"
        or evidence.artifact_sha256 is None
        or evidence.request_hash != request.request_input_hash
        or evidence.task_id != target.task_id
        or evidence.shot_id != target.shot_id
        or evidence.recipe_scope_hash != old_candidate.scope_hash
        or evidence.rubric_hash != old_candidate.recipe.rubric_hash
    ):
        raise ValueError("authored revision must retain the exact known fetched Shot evaluation")


def validate_authored_generation_revision_binding(binding, selected, target, *, target_goal) -> None:
    """Match the prospective binding byte-for-byte to a sealed authored target."""
    target = target.verify()
    latest = next((
        item for item in binding.inputs.evidence
        if item.evidence_hash == binding.inputs.latest_attempt_hash
    ), None)
    old_experiences = tuple(
        item for item in binding.inputs.experiences
        if latest is not None and latest in item.evidence
    )
    if latest is None or len(old_experiences) != 1:
        raise ValueError("authored successor must retain one exact prior goal experience")
    validate_authored_revision_goal(
        old_experiences[0].candidate.final_output_goal,
        target_goal,
        goal_requirement_revisions=target.goal_requirement_revisions,
    )
    resolved = binding.compiled_request
    request = resolved.activation_scope.request
    requirement = binding.projection.requirement
    frames = tuple(item for item in request.image_bindings if item.role == "first_frame")
    variants = tuple(
        item for item in selected.capabilities.variants
        if item.capability_id == selected.capability_id
    )
    if len(frames) != 1 or len(request.image_bindings) != 1 or request.media_bindings:
        raise ValueError("authored successor must bind only its exact first-frame image")
    if len(variants) != 1:
        raise ValueError("authored successor selected capability is not exact")
    variant = variants[0]
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
        or frames[0].asset_sha256 != target.first_frame_sha256
        or selected.final_output_goal != target_goal
    ):
        raise ValueError("compiled authored successor differs from its sealed exact target")


def allows_authored_generation_revision(binding, selected) -> bool:
    """Pure qualification check; the committer still requires exact /4 closure."""
    from ai_video.production._qualification_authoring_revision import (
        allows_authored_generation_revision as allows,
    )

    return allows(binding, selected)


def validate_authored_revision_goal(
    old_goal: FinalOutputContract,
    target_goal: FinalOutputContract,
    *,
    goal_requirement_revisions: tuple[AuthoredGoalRequirementRevision, ...] = (),
    authorization_receipt_id: str | None = None,
) -> None:
    """Preserve the old goal verbatim except for exact authorized observable pairs."""
    from ai_video.production.generation_visual_revision import validate_visual_revision_goal

    if not goal_requirement_revisions:
        validate_visual_revision_goal(old_goal, target_goal)
        return
    goal_requirement_revisions = tuple(
        AuthoredGoalRequirementRevision.model_validate_json(item.model_dump_json())
        for item in goal_requirement_revisions
    )
    old_goal = FinalOutputContract.model_validate_json(old_goal.model_dump_json())
    target_goal = FinalOutputContract.model_validate_json(target_goal.model_dump_json())
    if (
        old_goal.goal_id != target_goal.goal_id
        or old_goal.goal_version == target_goal.goal_version
    ):
        raise ValueError("authored goal revision must advance the same final-output goal")
    old = {item.requirement_id: item for item in old_goal.requirements}
    new = {item.requirement_id: item for item in target_goal.requirements}
    revisions = {item.requirement_id: item for item in goal_requirement_revisions}
    if len(revisions) != len(goal_requirement_revisions):
        raise ValueError("authored goal requirement revision IDs must be unique")
    if not set(old) <= set(new) or not set(revisions) <= set(old):
        raise ValueError("authored goal revision cannot remove old IDs or revise a new ID")
    for requirement_id, original in old.items():
        target = new[requirement_id]
        revision = revisions.get(requirement_id)
        if revision is None:
            if target != original:
                raise ValueError("unlisted final-output requirement changed during authored revision")
            continue
        if (
            revision.old_requirement != original
            or revision.new_requirement != target
            or revision.authorization_reference.strip() == ""
            or revision.reason.strip() == ""
        ):
            raise ValueError("authored goal revision differs from its exact old/new requirement pair")
        if (
            authorization_receipt_id is not None
            and revision.authorization_reference != authorization_receipt_id
        ):
            raise ValueError("authored goal revision does not name the exact closure authorization")


def validate_prospective_authored_goal(
    old_goal: FinalOutputContract, target_goal: FinalOutputContract
) -> None:
    """Allow only same-goal, same-ID/proof observable deltas before the /4 lock."""
    old_goal = FinalOutputContract.model_validate_json(old_goal.model_dump_json())
    target_goal = FinalOutputContract.model_validate_json(target_goal.model_dump_json())
    if (
        old_goal.goal_id != target_goal.goal_id
        or old_goal.goal_version == target_goal.goal_version
    ):
        raise ValueError("authored goal must keep its ID and advance its version")
    old = {item.requirement_id: item for item in old_goal.requirements}
    new = {item.requirement_id: item for item in target_goal.requirements}
    if not set(old) <= set(new):
        raise ValueError("authored goal cannot remove an existing requirement ID")
    for requirement_id, original in old.items():
        target = new[requirement_id]
        if (
            original.proof != target.proof
            or original.model_dump(mode="json", exclude={"observable"})
            != target.model_dump(mode="json", exclude={"observable"})
        ):
            raise ValueError("prospective authored goal changed a protected requirement field")
