"""Narrow contracts for an authored adaptive-resolution increase."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.generation_diagnosis import compare_compiled_requests
from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement


_OUTPUT_TIERS = {"480p": 1, "720p": 2, "1080p": 3, "4k": 4}
_DERIVED_REQUIREMENT_FIELDS = frozenset(
    {
        "requirement_id",
        "requirement_hash",
        "source_request_content_hash",
        "intent_evidence_hash",
        "generation_intent_hash",
    }
)


def _validate_output_increase(old, new) -> None:
    if not isinstance(old, VideoFlexibleOutputRequirement) or not isinstance(
        new, VideoFlexibleOutputRequirement
    ):
        raise ValueError("resolution revision requires adaptive flexible output requirements")
    if old.dimension_mode != "adaptive" or new.dimension_mode != "adaptive":
        raise ValueError("resolution revision can change only adaptive output tiers")
    old_tier = _OUTPUT_TIERS.get(old.resolution_label)
    new_tier = _OUTPUT_TIERS.get(new.resolution_label)
    if old_tier is None or new_tier is None or new_tier <= old_tier:
        raise ValueError("resolution revision must strictly increase a supported adaptive tier")
    before = old.model_dump(mode="json")
    after = new.model_dump(mode="json")
    before.pop("resolution_label")
    after.pop("resolution_label")
    if before != after:
        raise ValueError("resolution revision must preserve every other output requirement")


class ResolutionRevisionTarget(StrictModel):
    """One sealed request to raise only the adaptive output-resolution tier."""

    schema_version: Literal["resolution-revision-target/1"] = "resolution-revision-target/1"
    old_output: VideoFlexibleOutputRequirement
    target_output: VideoFlexibleOutputRequirement
    rationale: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_seal(self):
        if not self.rationale.strip():
            raise ValueError("resolution revision rationale must be nonblank")
        _validate_output_increase(self.old_output, self.target_output)
        if self.content_hash != canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        ):
            raise ValueError("resolution revision target content hash is invalid")
        return self

    @classmethod
    def create(
        cls,
        *,
        old_output: VideoFlexibleOutputRequirement,
        target_output: VideoFlexibleOutputRequirement,
        rationale: str,
    ) -> "ResolutionRevisionTarget":
        data = {
            "schema_version": "resolution-revision-target/1",
            "old_output": old_output,
            "target_output": target_output,
            "rationale": rationale.strip() if isinstance(rationale, str) else rationale,
        }
        payload = {
            key: value.model_dump(mode="json") if hasattr(value, "model_dump") else value
            for key, value in data.items()
        }
        data["content_hash"] = canonical_sha256(payload)
        return cls.model_validate(data).verify()

    def verify(self) -> "ResolutionRevisionTarget":
        # Strict JSON re-entry catches invalid nested objects smuggled through
        # model_copy(update=...), before any immutable writer can use this seal.
        return type(self).model_validate_json(self.model_dump_json())


def validate_resolution_target(old_binding, experience, target: ResolutionRevisionTarget) -> None:
    """Bind the target to the exact prior candidate and its latest known media."""
    if not isinstance(target, ResolutionRevisionTarget):
        raise ValueError("resolution revision target must be the sealed typed contract")
    target.verify()
    if experience.projection != old_binding.projection:
        raise ValueError("resolution revision does not bind the exact prior requirement projection")

    selected_id = old_binding.decision.selected_candidate_id
    candidates = tuple(
        candidate
        for candidate in old_binding.inputs.candidates
        if candidate.candidate_id == selected_id
    )
    if len(candidates) != 1 or experience.candidate != candidates[0]:
        raise ValueError("resolution revision does not bind the prior selected candidate")
    candidate = candidates[0]
    request = old_binding.compiled_request.activation_scope.request
    if (
        not isinstance(candidate.output_requirement, VideoFlexibleOutputRequirement)
        or request.output_requirement != candidate.output_requirement
        or target.old_output != request.output_requirement
    ):
        raise ValueError("resolution revision old output differs from the exact prior candidate request")

    if not experience.evidence:
        raise ValueError("resolution revision requires retained prior media evidence")
    evidence = experience.evidence[-1]
    if (
        evidence.outcome != "media"
        or evidence.artifact_sha256 is None
        or evidence.request_hash != request.request_input_hash
        or evidence.task_id != old_binding.inputs.limits.task_id
        or evidence.shot_id != old_binding.context.target_shot_id
        or evidence.recipe_scope_hash != candidate.scope_hash
        or evidence.facts_hash
        != canonical_sha256(
            experience.projection.requirement.model_dump(
                mode="json", exclude={"requirement_id", "requirement_hash"}
            )
        )
        or evidence.rubric_hash != candidate.recipe.rubric_hash
        or evidence.stage != "raw_generation"
    ):
        raise ValueError("resolution revision must use the exact latest fetched Shot evidence")
    if any(item.verdict == "FAIL" for item in evidence.findings):
        raise ValueError("resolution revision cannot supersede known failed raw-generation findings")


def _same_requirement_facts(old_requirement, new_requirement) -> bool:
    old = old_requirement.model_dump(mode="json")
    new = new_requirement.model_dump(mode="json")
    for field in _DERIVED_REQUIREMENT_FIELDS:
        old.pop(field, None)
        new.pop(field, None)

    old_shot = dict(old["target_shot"])
    new_shot = dict(new["target_shot"])
    old_shot_id = old_shot["shot_id"]
    new_shot_id = new_shot["shot_id"]
    old_shot_hash = old_shot["content_hash"]
    new_shot_hash = new_shot["content_hash"]
    old_revision = old_shot["revision"]
    new_revision = new_shot["revision"]
    if old_shot_id != new_shot_id:
        return False
    if old_shot != new_shot:
        if new_revision <= old_revision or old_shot_hash == new_shot_hash:
            return False
        for shot in (old_shot, new_shot):
            for field in ("revision", "content_hash", "creation_receipt_id", "source_provenance"):
                shot.pop(field, None)
        if old_shot != new_shot:
            return False
    old["target_shot"] = old_shot
    new["target_shot"] = new_shot

    old_assets = old.pop("asset_evidence")
    new_assets = new.pop("asset_evidence")
    if len(old_assets) != len(new_assets):
        return False
    for old_asset, new_asset in zip(old_assets, new_assets, strict=True):
        old_asset = dict(old_asset)
        new_asset = dict(new_asset)
        old_owner = old_asset.get("canonical_owner_id")
        new_owner = new_asset.get("canonical_owner_id")
        if old_owner == old_shot_id or new_owner == new_shot_id:
            if (
                old_owner != old_shot_id
                or new_owner != new_shot_id
                or old_asset.get("canonical_owner_content_hash") != old_shot_hash
                or new_asset.get("canonical_owner_content_hash") != new_shot_hash
            ):
                return False
            old_asset.pop("canonical_owner_content_hash", None)
            new_asset.pop("canonical_owner_content_hash", None)
        if old_asset != new_asset:
            return False
    old.pop("asset_evidence", None)
    new.pop("asset_evidence", None)
    return old == new


def _known_latest_experience(binding, selected):
    inputs = binding.inputs
    latest_hash = inputs.latest_attempt_hash
    if not latest_hash:
        return None, None
    matches = [
        (experience, evidence)
        for experience in inputs.experiences
        for evidence in experience.evidence
        if evidence.evidence_hash == latest_hash
    ]
    if len(matches) != 1:
        return None, None
    experience, latest = matches[0]
    if not experience.evidence or experience.evidence[-1] != latest:
        return None, None
    if experience.candidate.candidate_id != selected.candidate_id:
        return None, None
    return experience, latest


def allows_authored_resolution_revision(binding, selected) -> bool:
    """Allow one same-candidate submit after only an authored tier increase."""
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
        if any(item.outcome == "unknown_outcome" for item in inputs.evidence):
            return False

        prior, latest = _known_latest_experience(binding, selected)
        if prior is None or latest is None:
            return False
        if (
            latest.outcome != "media"
            or latest.artifact_sha256 is None
            or latest.task_id != limits.task_id
            or latest.shot_id != binding.context.target_shot_id
        ):
            return False
        submitted_attempts = {
            item.attempt_id
            for item in inputs.evidence
            if item.task_id == limits.task_id and item.outcome != "not_submitted"
        }
        if len(submitted_attempts) != limits.paid_submits_used:
            return False

        baseline = inputs.baseline_request
        current_scope = binding.compiled_request.activation_scope
        if (
            baseline is None
            or current_scope is None
            or baseline.request_input_hash != latest.request_hash
        ):
            return False
        current_request = current_scope.request
        delta = compare_compiled_requests(baseline, current_request)
        changed = set(delta["changed_variables"])
        if changed not in ({"output_requirement"}, {"output_requirement", "provider_profile"}):
            return False

        old_candidate = prior.candidate
        old_output = old_candidate.output_requirement
        target_output = selected.output_requirement
        _validate_output_increase(old_output, target_output)
        if (
            old_candidate.candidate_id != selected.candidate_id
            or old_candidate.capabilities.provider_name != selected.capabilities.provider_name
            or old_candidate.capabilities != selected.capabilities
            or old_candidate.capability_id != selected.capability_id
            or not isinstance(old_output, VideoFlexibleOutputRequirement)
            or not isinstance(target_output, VideoFlexibleOutputRequirement)
            or current_request.output_requirement != target_output
            or current_request.provider_profile != selected.provider_profile
            or baseline.provider_profile != old_candidate.provider_profile
            or old_candidate.final_output_goal is None
            or selected.final_output_goal is None
            or old_candidate.recipe.acceptance_policy != selected.recipe.acceptance_policy
            or old_candidate.recipe.expressions != selected.recipe.expressions
        ):
            return False

        old_recipe = old_candidate.recipe.model_dump(mode="json")
        new_recipe = selected.recipe.model_dump(mode="json")
        for field in ("profile_sha256", "requirement_hash"):
            old_recipe.pop(field, None)
            new_recipe.pop(field, None)
        if old_recipe != new_recipe:
            return False

        old_requirement = prior.projection.requirement
        new_requirement = binding.projection.requirement
        if (
            old_requirement.generation_intent != new_requirement.generation_intent
            or not _same_requirement_facts(old_requirement, new_requirement)
        ):
            return False

        from ai_video.production.generation_visual_revision import validate_visual_revision_goal

        validate_visual_revision_goal(old_candidate.final_output_goal, selected.final_output_goal)

        # Reuse the exact-media validator on the sealed historical authoring
        # snapshot; this also rejects FAIL while allowing mixed PASS/NE evidence.
        from types import SimpleNamespace

        prior_binding = SimpleNamespace(
            projection=prior.projection,
            decision=SimpleNamespace(selected_candidate_id=old_candidate.candidate_id),
            inputs=SimpleNamespace(
                candidates=(old_candidate,),
                limits=SimpleNamespace(task_id=limits.task_id),
            ),
            compiled_request=SimpleNamespace(
                activation_scope=SimpleNamespace(request=baseline),
            ),
            context=SimpleNamespace(target_shot_id=binding.context.target_shot_id),
        )
        target = ResolutionRevisionTarget.create(
            old_output=old_output,
            target_output=target_output,
            rationale="Internal qualification proof of the authored adaptive-resolution increase.",
        )
        validate_resolution_target(prior_binding, prior, target)
        return True
    except (AttributeError, KeyError, StopIteration, TypeError, ValueError):
        return False


def require_authored_resolution_revision_predecessor(committer, manifest, binding) -> None:
    """Reopen the exact /3 authorization and retained evidence at the submit lock."""
    if binding.policy.execution_purpose != "qualification":
        return
    selected = next(
        (
            candidate
            for candidate in binding.inputs.candidates
            if candidate.candidate_id == binding.decision.selected_candidate_id
        ),
        None,
    )
    if not allows_authored_resolution_revision(binding, selected):
        return

    from ai_video.errors import AiVideoError
    from ai_video.production._generation_feedback_reader import (
        load_generation_experience,
        load_generation_visual_supersession,
    )
    from ai_video.production._state_commit_common import _state_invalid
    from ai_video.production._video_project_reader import load_video_fetch_receipt
    from ai_video.production.project import load_production_project

    latest = next(
        (
            evidence
            for evidence in binding.inputs.evidence
            if evidence.evidence_hash == binding.inputs.latest_attempt_hash
        ),
        None,
    )
    if latest is None:
        raise _state_invalid("Authored resolution revision has no exact latest attempt evidence.")
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
        or state.request is None
        or state.fetch_receipt is None
        or state.paid_submit_receipt is None
        or not state.generation_experiences
        or previous.paid_provider_state is None
        or previous.paid_provider_state.submit_receipt != state.paid_submit_receipt
    ):
        raise _state_invalid("Authored resolution revision requires its exact canonical supersession.")

    try:
        receipt = load_generation_visual_supersession(
            committer.project_root, state.visual_supersession
        )
        if receipt.schema_version != "generation-visual-supersession/3" or receipt.resolution_revision is None:
            raise ValueError("the prior receipt is not a sealed resolution supersession")
        old_request = committer._reopen_video_request(state.request)
        old_binding = committer._reopen_generation_execution_binding(state.execution_binding)
        old_binding.validate_request(old_request)
        fetch = load_video_fetch_receipt(committer.project_root, state.fetch_receipt)
        experience_pointer = state.generation_experiences[-1]
        experience = load_generation_experience(committer.project_root, experience_pointer)
        current_request = binding.compiled_request.activation_scope.request
        old_frames = tuple(
            item for item in old_request.activation_scope.request.image_bindings
            if item.role == "first_frame"
        )
        current_frames = tuple(
            item for item in current_request.image_bindings if item.role == "first_frame"
        )
        old_candidates = tuple(
            candidate
            for candidate in old_binding.inputs.candidates
            if candidate.candidate_id == old_binding.decision.selected_candidate_id
        )
        if len(old_candidates) != 1:
            raise ValueError("prior binding does not select exactly one candidate")
        old_candidate = old_candidates[0]
        current_project = load_production_project(committer._project_root / "project.yaml")

        if (
            current_project.manifest != manifest
            or current_project.qa_policy is None
            or latest.outcome != "media"
            or latest.artifact_sha256 is None
            or latest.task_id != binding.inputs.limits.task_id
            or latest.shot_id != binding.context.target_shot_id
            or latest.attempt_id != previous.attempt_id
            or latest not in experience.evidence
            or experience.evidence[-1] != latest
            or experience.projection != old_binding.projection
            or experience.candidate != old_candidate
            or receipt.attempt_id != previous.attempt_id
            or receipt.execution_binding != state.execution_binding
            or receipt.fetch_receipt != state.fetch_receipt
            or receipt.paid_submit_receipt != state.paid_submit_receipt
            or receipt.experience_content_hash != experience_pointer.content_hash
            or receipt.evidence_hash != latest.evidence_hash
            or receipt.request_fingerprint != latest.request_hash
            or old_request.activation_scope.request.request_input_hash != latest.request_hash
            or receipt.artifact_sha256 != latest.artifact_sha256
            or state.fetch_receipt.artifact_sha256 != latest.artifact_sha256
            or fetch.artifact_sha256 != latest.artifact_sha256
            or receipt.task_id != latest.task_id
            or receipt.shot_id != latest.shot_id
            or receipt.base_project != previous.base_project
            or old_request.activation_scope.request.base_project != previous.base_project
            or len(old_frames) != 1
            or len(current_frames) != 1
            or receipt.old_first_frame_sha256 != old_frames[0].asset_sha256
            or receipt.target_first_frame_sha256 != current_frames[0].asset_sha256
            or current_frames[0].asset_sha256 != old_frames[0].asset_sha256
            or current_request.base_project.revision <= receipt.base_project.revision
            or receipt.old_goal != old_candidate.final_output_goal
            or receipt.target_goal != selected.final_output_goal
            or current_project.qa_policy.final_output != selected.final_output_goal
            or current_project.manifest.active_project != current_request.base_project
            or receipt.resolution_revision.target_output != selected.output_requirement
            or state.phase.value != "validate"
            or state.quality_rejection is not None
            or state.candidate_video_asset_ids
            or previous.paid_provider_state.phase.value not in {"accepted", "settled"}
        ):
            raise ValueError("resolution revision differs from its exact retained authorization or media")
        validate_resolution_target(old_binding, experience, receipt.resolution_revision)
    except AiVideoError:
        raise
    except (OSError, AttributeError, KeyError, IndexError, StopIteration, TypeError, ValueError) as exc:
        raise _state_invalid("Authored resolution predecessor no longer matches its sealed target.", str(exc)) from exc
