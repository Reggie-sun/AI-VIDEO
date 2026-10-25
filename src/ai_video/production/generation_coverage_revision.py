"""Sealed authored revisions that repair observable raw-generation coverage."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.generation_diagnosis import compare_compiled_requests
from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import GenerationIntent


_MUTABLE_FAILED_RULE_FIELDS = frozenset(
    {"observable", "tolerance", "measurement", "intent_paths"}
)
_FAILED_RULE_IDENTITY_FIELDS = frozenset(
    {"requirement_id", "level", "stage", "proof", "dimension", "production_owner"}
)
_ALLOWED_INTENT_FIELDS = frozenset(
    {
        "subject_action",
        "camera_intent",
        "camera_endpoint",
        "primary_camera_motion",
        "camera_subject_relation",
        "axis_continuity",
        "pacing",
    }
)


class CoverageRevisionTarget(StrictModel):
    """The exact revised GenerationIntent and raw QA acceptance selected for a Shot."""

    schema_version: Literal["coverage-revision-target/1"] = "coverage-revision-target/1"
    intent: GenerationIntent
    acceptance: DomainAcceptancePolicy
    rationale: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _verify_hash(self):
        if not self.rationale.strip():
            raise ValueError("coverage revision rationale must be nonblank")
        if self.content_hash != canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        ):
            raise ValueError("coverage revision target content hash is invalid")
        return self

    @classmethod
    def create(
        cls,
        *,
        intent: GenerationIntent,
        acceptance: DomainAcceptancePolicy,
        rationale: str,
    ) -> "CoverageRevisionTarget":
        data = {
            "intent": intent,
            "acceptance": acceptance,
            "rationale": rationale.strip() if isinstance(rationale, str) else rationale,
        }
        data["content_hash"] = canonical_sha256(
            {
                "schema_version": "coverage-revision-target/1",
                **{
                    key: value.model_dump(mode="json") if hasattr(value, "model_dump") else value
                    for key, value in data.items()
                },
            }
        )
        return cls.model_validate(data).verify()

    def verify(self) -> "CoverageRevisionTarget":
        # model_copy can retain unvalidated nested model instances. Re-enter
        # every nested schema before a target can reach an immutable writer.
        return type(self).model_validate_json(self.model_dump_json())


def _raw_rules(acceptance: DomainAcceptancePolicy) -> dict[str, dict]:
    payload = acceptance.model_dump(mode="json")["profile_payload"]
    inventory = payload.get("generation_requirements")
    if not isinstance(inventory, list | tuple) or not inventory:
        raise ValueError("coverage revision requires the exact raw generation rule inventory")
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


def _intent_changes_only_coverage_fields(old: GenerationIntent, new: GenerationIntent) -> bool:
    before = old.model_dump(mode="json")
    after = new.model_dump(mode="json")
    if set(before) != set(after):
        return False

    changed = False
    for field in before:
        if field not in _ALLOWED_INTENT_FIELDS:
            if before[field] != after[field]:
                return False
            continue
        if field == "subject_action":
            left, right = before[field], after[field]
            if set(left) != set(right):
                return False
            if any(left[key] != right[key] for key in left if key != "progression"):
                return False
            changed |= left["progression"] != right["progression"]
        elif field == "axis_continuity":
            left, right = before[field], after[field]
            if set(left) != set(right):
                return False
            if any(left[key] != right[key] for key in left if key != "framing_continuity"):
                return False
            changed |= left["framing_continuity"] != right["framing_continuity"]
        elif field == "pacing":
            left, right = before[field], after[field]
            if set(left) != set(right):
                return False
            if any(left[key] != right[key] for key in left if key != "cadence"):
                return False
            changed |= left["cadence"] != right["cadence"]
        else:
            changed |= before[field] != after[field]
    return changed


def _non_intent_requirement_facts_match(old_requirement, new_requirement) -> bool:
    """Allow exact authored lineage derivations, no unrelated requirement edits."""
    old = old_requirement.model_dump(mode="json")
    new = new_requirement.model_dump(mode="json")
    for field in (
        "requirement_id",
        "requirement_hash",
        "source_request_content_hash",
        "intent_evidence_hash",
        "generation_intent_hash",
    ):
        old.pop(field, None)
        new.pop(field, None)
    old_shot = dict(old["target_shot"])
    new_shot = dict(new["target_shot"])
    old_shot_hash = old_shot["content_hash"]
    new_shot_hash = new_shot["content_hash"]
    old_shot_id = old_shot["shot_id"]
    new_shot_id = new_shot["shot_id"]
    for field in ("revision", "content_hash", "creation_receipt_id", "source_provenance", "intent"):
        old_shot.pop(field, None)
        new_shot.pop(field, None)
    old_constraints = old_shot.pop("continuity_constraints")
    new_constraints = new_shot.pop("continuity_constraints")
    if tuple(new_constraints[:len(old_constraints)]) != tuple(old_constraints):
        return False
    old["target_shot"] = old_shot
    new["target_shot"] = new_shot
    if old_shot_id != new_shot_id:
        return False

    old_assets = old.pop("asset_evidence")
    new_assets = new.pop("asset_evidence")
    if len(old_assets) != len(new_assets):
        return False
    for old_asset, new_asset in zip(old_assets, new_assets, strict=True):
        old_owner_hash = old_asset.pop("canonical_owner_content_hash")
        new_owner_hash = new_asset.pop("canonical_owner_content_hash")
        if old_asset != new_asset:
            return False
        owner_id = old_asset.get("canonical_owner_id")
        if owner_id == old_shot_id or new_asset.get("canonical_owner_id") == new_shot_id:
            if not (
                owner_id == new_shot_id == old_shot_id
                and old_owner_hash == old_shot_hash
                and new_owner_hash == new_shot_hash
            ):
                return False
        elif old_owner_hash != new_owner_hash:
            return False

    old.pop("generation_intent", None)
    new.pop("generation_intent", None)
    return old == new


def _latest_media_experience(old_binding, experience):
    if experience.projection != old_binding.projection:
        raise ValueError("coverage revision does not bind the exact prior requirement projection")
    selected_id = old_binding.decision.selected_candidate_id
    candidates = tuple(item for item in old_binding.inputs.candidates if item.candidate_id == selected_id)
    if len(candidates) != 1 or experience.candidate != candidates[0]:
        raise ValueError("coverage revision does not bind the prior selected candidate")
    request = old_binding.compiled_request.activation_scope.request
    if not experience.evidence:
        raise ValueError("coverage revision requires the retained prior media evaluation")
    evidence = experience.evidence[-1]
    if (
        evidence.outcome != "media"
        or evidence.artifact_sha256 is None
        or evidence.request_hash != request.request_input_hash
        or evidence.task_id != old_binding.inputs.limits.task_id
        or evidence.shot_id != old_binding.context.target_shot_id
    ):
        raise ValueError("coverage revision must use the exact prior fetched Shot evidence")
    failed = {item.requirement_id for item in evidence.findings if item.verdict == "FAIL"}
    if not failed:
        raise ValueError("coverage revision requires a known raw-generation failure to address")
    return candidates[0], evidence, failed


def validate_coverage_target(old_binding, experience, target: CoverageRevisionTarget) -> None:
    """Validate allowed intent scope and preserve all nonfailed QA rules verbatim."""
    if not isinstance(target, CoverageRevisionTarget):
        raise ValueError("coverage revision target must be the sealed typed contract")
    target.verify()
    _validate_coverage_target_values(
        old_binding,
        experience,
        intent=target.intent,
        acceptance=target.acceptance,
    )


def _validate_coverage_target_values(old_binding, experience, *, intent, acceptance) -> None:
    prior, _, failed_ids = _latest_media_experience(old_binding, experience)
    old_intent = experience.projection.requirement.generation_intent
    if not _intent_changes_only_coverage_fields(old_intent, intent):
        raise ValueError("coverage revision must change only authored action/camera coverage fields")

    old_acceptance = prior.recipe.acceptance_policy
    old_rules = _raw_rules(old_acceptance)
    new_rules = _raw_rules(acceptance)
    if (
        acceptance.domain_id != old_acceptance.domain_id
        or acceptance.profile_id != old_acceptance.profile_id
        or acceptance.measurement_contract_version
        != old_acceptance.measurement_contract_version
    ):
        raise ValueError("coverage revision must retain the exact QA profile identity")
    old_profile = old_acceptance.model_dump(mode="json")["profile_payload"]
    new_profile = acceptance.model_dump(mode="json")["profile_payload"]
    for profile in (old_profile, new_profile):
        profile.pop("content_hash", None)
        profile.pop("profile_version", None)
        profile.pop("generation_requirements", None)
        profile.pop("required_requirement_ids", None)
    if old_profile != new_profile:
        raise ValueError("coverage revision cannot change QA profile rules outside the raw inventory")
    if not set(old_acceptance.required_requirement_ids) <= set(acceptance.required_requirement_ids):
        raise ValueError("coverage revision cannot drop an existing required requirement ID")
    added_required_ids = set(acceptance.required_requirement_ids) - set(old_acceptance.required_requirement_ids)
    if any(
        requirement_id not in new_rules
        or new_rules[requirement_id].get("level") != "acceptance"
        or new_rules[requirement_id].get("stage") != "raw_generation"
        for requirement_id in added_required_ids
    ):
        raise ValueError("new required IDs must name added raw-generation acceptance rules")
    if not failed_ids <= set(old_rules):
        raise ValueError("latest failed observation references no exact old raw QA rule")
    if not failed_ids <= set(new_rules):
        raise ValueError("coverage revision cannot remove a failed raw QA rule")

    for requirement_id, old_rule in old_rules.items():
        new_rule = new_rules.get(requirement_id)
        if new_rule is None:
            raise ValueError("coverage revision cannot remove a prior raw QA rule")
        if requirement_id not in failed_ids:
            if new_rule != old_rule:
                raise ValueError("coverage revision must preserve every nonfailed raw QA rule exactly")
            continue
        if set(new_rule) != set(old_rule):
            raise ValueError("failed raw rules must retain their complete sealed field set")
        if any(new_rule.get(field) != old_rule.get(field) for field in _FAILED_RULE_IDENTITY_FIELDS):
            raise ValueError("revised failed rules must preserve their identity, stage, proof, dimension and owner")
        immutable_fields = (set(old_rule) | set(new_rule)) - _MUTABLE_FAILED_RULE_FIELDS
        if any(new_rule.get(field) != old_rule.get(field) for field in immutable_fields):
            raise ValueError("failed raw rules may change only observable, tolerance, measurement and intent paths")


def allows_authored_coverage_revision(binding, selected) -> bool:
    """Admit one qualified, same-provider submit after an authored coverage change."""
    try:
        if selected is None or binding.policy.execution_purpose != "qualification":
            return False
        inputs = binding.inputs
        limits = inputs.limits
        if (
            limits.paid_submits_used < 1
            or limits.paid_submit_ceiling != limits.paid_submits_used + 1
            or limits.generation_forbidden
            or limits.allowed_remote_candidates != (selected.candidate_id,)
            or inputs.policy.max_resamples != 0
            or inputs.runtime_repairs
            or binding.decision.runtime_repair is not None
            or binding.decision.intervention is not None
            or len(inputs.candidates) != 1
            or inputs.candidates[0] != selected
            or not inputs.experiences
            or not binding.policy.remote_authorized
            or not binding.policy.budget_authorized
        ):
            return False

        prior = next(
            (item for item in inputs.experiences
             if any(e.evidence_hash == inputs.latest_attempt_hash for e in item.evidence)),
            None,
        )
        if prior is None or not prior.evidence:
            return False
        latest = next((item for item in prior.evidence
                       if item.evidence_hash == inputs.latest_attempt_hash), None)
        if (
            latest is None
            or latest.outcome != "media"
            or latest.artifact_sha256 is None
            or latest.task_id != limits.task_id
            or latest.shot_id != binding.context.target_shot_id
            or not any(item.verdict == "FAIL" for item in latest.findings)
            or any(item.outcome == "unknown_outcome" for item in inputs.evidence)
        ):
            return False
        submitted_attempts = {
            item.attempt_id for item in inputs.evidence
            if item.task_id == limits.task_id and item.outcome != "not_submitted"
        }
        if len(submitted_attempts) != limits.paid_submits_used:
            return False

        baseline = inputs.baseline_request
        current_scope = binding.compiled_request.activation_scope
        if baseline is None or current_scope is None or baseline.request_input_hash != latest.request_hash:
            return False
        current_request = current_scope.request
        delta = compare_compiled_requests(baseline, current_request)
        changed = set(delta["changed_variables"])
        if "prompt_text" not in changed or not changed <= {"prompt_text", "provider_profile"}:
            return False

        old_candidate = prior.candidate
        if (
            old_candidate.candidate_id != selected.candidate_id
            or old_candidate.capabilities.provider_name != selected.capabilities.provider_name
            or old_candidate.capabilities != selected.capabilities
            or old_candidate.capability_id != selected.capability_id
            or old_candidate.output_requirement != selected.output_requirement
            or old_candidate.final_output_goal is None
            or selected.final_output_goal is None
        ):
            return False
        if not _non_intent_requirement_facts_match(
            prior.projection.requirement,
            binding.projection.requirement,
        ):
            return False
        if not _intent_changes_only_coverage_fields(
            prior.projection.requirement.generation_intent,
            binding.projection.requirement.generation_intent,
        ):
            return False
        from ai_video.production.generation_visual_revision import validate_visual_revision_goal

        validate_visual_revision_goal(old_candidate.final_output_goal, selected.final_output_goal)
        # The old durable experience is the authoritative baseline. It carries
        # the original projection and candidate even when the current binding
        # has already moved to a new authoring revision.
        old_binding = _PriorCoverageBinding(prior, latest, baseline, binding.context.target_shot_id)
        _validate_coverage_target_values(
            old_binding,
            prior,
            intent=binding.projection.requirement.generation_intent,
            acceptance=selected.recipe.acceptance_policy,
        )
        return True
    except (AttributeError, KeyError, StopIteration, TypeError, ValueError):
        return False


def require_authored_coverage_revision_predecessor(committer, manifest, binding) -> None:
    """Reopen the exact /2 coverage authorization at the existing submit lock."""
    if binding.policy.execution_purpose != "qualification":
        return
    selected = next(
        (candidate for candidate in binding.inputs.candidates
         if candidate.candidate_id == binding.decision.selected_candidate_id),
        None,
    )
    if not allows_authored_coverage_revision(binding, selected):
        return

    from ai_video.production._state_commit_common import _state_invalid
    from ai_video.production._generation_feedback_reader import (
        load_generation_experience,
        load_generation_visual_supersession,
    )

    latest = next((
        evidence for evidence in binding.inputs.evidence
        if evidence.evidence_hash == binding.inputs.latest_attempt_hash
    ), None)
    if latest is None:
        raise _state_invalid("Authored coverage revision has no exact latest attempt evidence.")
    previous = next(
        (attempt for attempt in manifest.attempts if attempt.attempt_id == latest.attempt_id),
        None,
    )
    state = previous.video_generation_state if previous is not None else None
    if (
        previous is None
        or previous.status.value != "failed"
        or previous.error_code != "generation_visual_superseded"
        or state is None
        or state.visual_supersession is None
        or state.execution_binding is None
        or state.fetch_receipt is None
        or not state.generation_experiences
    ):
        raise _state_invalid("Authored coverage revision requires its exact canonical supersession.")

    receipt = load_generation_visual_supersession(committer.project_root, state.visual_supersession)
    if receipt.schema_version != "generation-visual-supersession/2" or receipt.coverage_revision is None:
        raise _state_invalid("Authored coverage revision requires a sealed coverage supersession target.")

    current_request = binding.compiled_request.activation_scope.request
    current_frames = tuple(item for item in current_request.image_bindings if item.role == "first_frame")
    old_request = committer._reopen_video_request(state.request).activation_scope.request
    old_frames = tuple(item for item in old_request.image_bindings if item.role == "first_frame")
    experience_pointer = state.generation_experiences[-1]
    experience = load_generation_experience(committer.project_root, experience_pointer)
    old_binding = committer._reopen_generation_execution_binding(state.execution_binding)

    if (
        not any(item.evidence_hash == latest.evidence_hash for item in experience.evidence)
        or latest.outcome != "media"
        or latest.artifact_sha256 is None
        or latest.task_id != binding.inputs.limits.task_id
        or latest.shot_id != binding.context.target_shot_id
        or receipt.attempt_id != previous.attempt_id
        or receipt.execution_binding != state.execution_binding
        or receipt.fetch_receipt != state.fetch_receipt
        or receipt.experience_content_hash != experience_pointer.content_hash
        or receipt.evidence_hash != latest.evidence_hash
        or receipt.request_fingerprint != latest.request_hash
        or old_request.request_input_hash != latest.request_hash
        or receipt.artifact_sha256 != latest.artifact_sha256
        or state.fetch_receipt.artifact_sha256 != latest.artifact_sha256
        or receipt.task_id != latest.task_id
        or receipt.shot_id != latest.shot_id
        or receipt.base_project != previous.base_project
        or len(old_frames) != 1
        or len(current_frames) != 1
        or receipt.old_first_frame_sha256 != old_frames[0].asset_sha256
        or receipt.target_first_frame_sha256 != current_frames[0].asset_sha256
        or current_frames[0].asset_sha256 != old_frames[0].asset_sha256
        or current_request.base_project.revision <= receipt.base_project.revision
        or receipt.target_goal != selected.final_output_goal
        or receipt.coverage_revision.intent != binding.projection.requirement.generation_intent
        or receipt.coverage_revision.acceptance != selected.recipe.acceptance_policy
    ):
        raise _state_invalid("Authored coverage revision differs from its sealed target or retained history.")

    try:
        validate_coverage_target(old_binding, experience, receipt.coverage_revision)
    except (AttributeError, KeyError, StopIteration, TypeError, ValueError) as exc:
        raise _state_invalid("Authored coverage predecessor no longer matches its sealed target.", str(exc)) from exc


class _PriorCoverageBinding:
    """Small read-only view of a durable experience's sealed original inputs."""

    def __init__(self, experience, evidence, request, shot_id):
        from types import SimpleNamespace

        self.projection = experience.projection
        self.decision = SimpleNamespace(selected_candidate_id=experience.candidate.candidate_id)
        self.inputs = SimpleNamespace(
            candidates=(experience.candidate,),
            limits=SimpleNamespace(task_id=evidence.task_id),
        )
        self.compiled_request = SimpleNamespace(activation_scope=SimpleNamespace(request=request))
        self.context = SimpleNamespace(target_shot_id=shot_id)
