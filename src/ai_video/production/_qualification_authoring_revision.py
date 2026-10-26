"""Bounded admission and locked closure checks for an authored media successor."""

from __future__ import annotations

from ai_video.production.generation_diagnosis import compare_compiled_requests
from ai_video.production.generation_authoring_revision import (
    validate_authored_generation_revision_binding,
    validate_prospective_authored_goal,
)
from ai_video.production.video import VideoGenerationMode
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.generation_authored_retarget import (
    _same_goal_with_new_version,
    validate_authored_generation_retarget_binding,
)


def allows_authored_generation_retarget(binding, selected) -> bool:
    """Admit one Seedance 2.0 R2V retarget after exact known fetched media."""
    try:
        if selected is None or binding.policy.execution_purpose != "qualification":
            return False
        inputs = binding.inputs
        limits = inputs.limits
        if (
            limits.paid_submits_used < 1
            or limits.paid_submit_ceiling != limits.paid_submits_used + 1
            or binding.decision.runtime_repair is not None
            or binding.decision.intervention is not None
            or inputs.policy.max_resamples != 0
            or limits.generation_forbidden
            or limits.allowed_remote_candidates != (selected.candidate_id,)
            or any(item.outcome == "unknown_outcome" for item in inputs.evidence)
        ):
            return False
        submitted = tuple(item for item in inputs.evidence
                          if item.task_id == limits.task_id and item.outcome != "not_submitted")
        submitted_keys = {}
        submitted_attempt_requests = {}
        for item in submitted:
            key = (item.attempt_id, item.request_hash)
            if (key in submitted_keys and submitted_keys[key] != item.shot_id
                    or item.attempt_id in submitted_attempt_requests
                    and submitted_attempt_requests[item.attempt_id] != item.request_hash):
                return False
            submitted_keys[key] = item.shot_id
            submitted_attempt_requests[item.attempt_id] = item.request_hash
        latest = next((item for item in inputs.evidence
                       if item.evidence_hash == inputs.latest_attempt_hash), None)
        prior_experiences = tuple(experience for experience in inputs.experiences
                                  if latest is not None and latest in experience.evidence)
        baseline = inputs.baseline_request
        scope = binding.compiled_request.activation_scope
        if (
            len(inputs.candidates) != 1
            or len(submitted_keys) != limits.paid_submits_used
            or latest is None
            or latest.outcome != "media"
            or latest.artifact_sha256 is None
            or not any(item.verdict == "FAIL" for item in latest.findings)
            or latest.task_id != limits.task_id
            or latest.shot_id != binding.context.target_shot_id
            or len(prior_experiences) != 1
            or baseline is None
            or baseline.request_input_hash != latest.request_hash
            or scope is None
        ):
            return False
        old_candidate = prior_experiences[0].candidate
        prior_variants = tuple(item for item in old_candidate.capabilities.variants
                               if item.capability_id == old_candidate.capability_id)
        variants = tuple(item for item in selected.capabilities.variants
                         if item.capability_id == selected.capability_id)
        if len(prior_variants) != 1 or len(variants) != 1:
            return False
        prior_variant, variant = prior_variants[0], variants[0]
        if (
            old_candidate.capabilities.provider_name != selected.capabilities.provider_name
            or prior_variant.provider_kind != variant.provider_kind
            or prior_variant.model_id == variant.model_id
            or variant.mode is not VideoGenerationMode.REFERENCE_TO_VIDEO
            or variant.output_capability is None
            or not variant.output_capability.supports(selected.output_requirement)
            or "reference" not in variant.allowed_image_roles
            or old_candidate.recipe.acceptance_policy != selected.recipe.acceptance_policy
            or not _same_goal_with_new_version(old_candidate.final_output_goal, selected.final_output_goal)
            or prior_experiences[0].projection.requirement.generation_intent
                == binding.projection.requirement.generation_intent
        ):
            return False
        before, after = baseline, scope.request
        if (
            after.provider_name != selected.capabilities.provider_name
            or after.provider_kind != variant.provider_kind
            or after.model_id != variant.model_id
            or after.mode is not VideoGenerationMode.REFERENCE_TO_VIDEO
            or after.base_project is None
            or after.base_project.revision != before.base_project.revision + 1
            or not after.image_bindings and not after.media_bindings
            or any(item.role != "reference" for item in after.image_bindings)
            or len(after.image_bindings) > variant.max_reference_count
            or any(item.role not in variant.allowed_image_roles for item in after.image_bindings)
            or variant.output_capability is None
            or not variant.output_capability.supports(after.output_requirement)
        ):
            return False
        from ai_video.production.video_contracts import media_bindings_satisfy_capabilities

        if not media_bindings_satisfy_capabilities(after.media_bindings, variant.media_capabilities):
            return False
        changed = set(compare_compiled_requests(before, after)["changed_variables"])
        return (
            {"model_id", "mode", "image_bindings"} <= changed
            and changed <= {
                "model_id", "mode", "image_bindings", "media_bindings", "prompt_text",
                "provider_profile", "output_requirement", "adapter_compiler_id",
                "adapter_compiler_version", "adapter_compiler_hash", "execution_stack_hash",
            }
        )
    except (AttributeError, TypeError, ValueError, StopIteration):
        return False


def allows_authored_generation_revision(binding, selected) -> bool:
    """Admit one known same-provider/model authored successor without a permit."""
    try:
        variants = tuple(item for item in selected.capabilities.variants
                         if item.capability_id == selected.capability_id) if selected is not None else ()
        if len(variants) == 1 and variants[0].mode is VideoGenerationMode.REFERENCE_TO_VIDEO:
            return allows_authored_generation_retarget(binding, selected)
    except (AttributeError, TypeError, ValueError):
        return False
    try:
        if selected is None or binding.policy.execution_purpose != "qualification":
            return False
        inputs = binding.inputs
        limits = inputs.limits
        if (
            limits.paid_submits_used < 1
            or limits.paid_submit_ceiling != limits.paid_submits_used + 1
            or binding.decision.runtime_repair is not None
            or binding.decision.intervention is not None
            or inputs.policy.max_resamples != 0
            or any(item.outcome == "unknown_outcome" for item in inputs.evidence)
            or limits.generation_forbidden
            or limits.allowed_remote_candidates != (selected.candidate_id,)
        ):
            return False
        submitted = tuple(
            item
            for item in inputs.evidence
            if item.task_id == limits.task_id and item.outcome != "not_submitted"
        )
        submitted_keys = {}
        submitted_attempt_requests = {}
        for item in submitted:
            key = (item.attempt_id, item.request_hash)
            if (key in submitted_keys and submitted_keys[key] != item.shot_id
                    or item.attempt_id in submitted_attempt_requests
                    and submitted_attempt_requests[item.attempt_id] != item.request_hash):
                return False
            submitted_keys[key] = item.shot_id
            submitted_attempt_requests[item.attempt_id] = item.request_hash
        latest = next(
            (item for item in inputs.evidence if item.evidence_hash == inputs.latest_attempt_hash),
            None,
        )
        prior_matches = tuple(
            experience for experience in inputs.experiences
            if latest is not None and latest in experience.evidence
        )
        baseline = inputs.baseline_request
        scope = binding.compiled_request.activation_scope
        if (
            len(inputs.candidates) != 1
            or len(submitted_keys) != limits.paid_submits_used
            or latest is None
            or latest.outcome != "media"
            or latest.artifact_sha256 is None
            or latest.task_id != limits.task_id
            or latest.shot_id != binding.context.target_shot_id
            or len(prior_matches) != 1
            or baseline is None
            or scope is None
            or baseline.request_input_hash != latest.request_hash
        ):
            return False
        prior_candidate = prior_matches[0].candidate
        selected_variant = tuple(
            variant for variant in selected.capabilities.variants
            if variant.capability_id == selected.capability_id
        )
        prior_variants = tuple(
            variant for variant in prior_candidate.capabilities.variants
            if variant.capability_id == prior_candidate.capability_id
        )
        if len(selected_variant) != 1 or len(prior_variants) != 1:
            return False
        if (
            prior_candidate.capabilities.provider_name != selected.capabilities.provider_name
            or prior_variants[0].provider_kind != selected_variant[0].provider_kind
            or prior_variants[0].model_id != selected_variant[0].model_id
        ):
            return False
        validate_prospective_authored_goal(
            prior_candidate.final_output_goal, selected.final_output_goal
        )
        before, after = baseline, scope.request
        frames = tuple(item for item in after.image_bindings if item.role == "first_frame")
        changed = set(compare_compiled_requests(before, after)["changed_variables"])
        return (
            after.mode is VideoGenerationMode.IMAGE_TO_VIDEO
            and isinstance(after.output_requirement, VideoFlexibleOutputRequirement)
            and len(after.image_bindings) == 1
            and len(frames) == 1
            and not after.media_bindings
            and after.base_project.revision > before.base_project.revision
            and bool(changed & {"image_bindings", "prompt_text", "output_requirement", "mode"})
            and changed <= {
                "image_bindings", "prompt_text", "provider_profile", "output_requirement", "mode",
                "media_bindings",
                "adapter_compiler_id", "adapter_compiler_version", "adapter_compiler_hash",
                "execution_stack_hash",
            }
        )
    except (AttributeError, TypeError, ValueError, StopIteration):
        return False


def require_authored_generation_revision_predecessor(
    committer, manifest, binding, *, loaded=None
) -> None:
    """Reopen the exact /4 or /5 source and match it under submit lock."""
    if binding.policy.execution_purpose != "qualification":
        return
    selected = next(
        (candidate for candidate in binding.inputs.candidates
         if candidate.candidate_id == binding.decision.selected_candidate_id),
        None,
    )
    allowed = allows_authored_generation_revision(binding, selected)

    from ai_video.production._state_commit_common import _state_invalid
    from ai_video.production._generation_feedback_reader import load_generation_visual_supersession
    from ai_video.production.generation_authoring_revision import validate_authored_revision_goal
    from ai_video.production.project import load_production_project
    from ai_video.production.models import StateCommitStatus

    latest = next((
        item for item in binding.inputs.evidence
        if item.evidence_hash == binding.inputs.latest_attempt_hash
    ), None)
    if latest is None:
        if allowed:
            raise _state_invalid("Authored generation revision has no exact latest source evidence.")
        return
    previous = next((item for item in manifest.attempts if item.attempt_id == latest.attempt_id), None)
    state = previous.video_generation_state if previous is not None else None
    if (
        previous is None
        or previous.status is not StateCommitStatus.FAILED
        or previous.error_code != "generation_visual_superseded"
        or state is None
        or state.visual_supersession is None
        or not state.generation_experiences
    ):
        if not allowed:
            return
        raise _state_invalid("Authored generation revision requires its exact canonical supersession.")
    receipt = load_generation_visual_supersession(committer.project_root, state.visual_supersession)
    is_retarget = receipt.schema_version == "generation-visual-supersession/5"
    target = receipt.authored_retarget if is_retarget else receipt.authored_revision
    if (
        receipt.schema_version not in {"generation-visual-supersession/4", "generation-visual-supersession/5"}
        or target is None
    ):
        if not allowed:
            return
        raise _state_invalid("Authored generation revision requires a sealed /4 target.")
    if not allowed:
        raise _state_invalid("A sealed authored revision cannot be redirected to another history or candidate.")
    if loaded is None:
        loaded = load_production_project(committer.project_root / "project.yaml")
    if (
        loaded.manifest != manifest
        or manifest.active_project != target.target_project
        or loaded.manifest.active_project != target.target_project
    ):
        raise _state_invalid("Authored target Project has not been committed and activated.")

    request = binding.compiled_request.activation_scope.request
    if (
        receipt.attempt_id != latest.attempt_id
        or receipt.request_fingerprint != latest.request_hash
        or receipt.request_fingerprint != state.request.request_input_hash
        or receipt.artifact_sha256 != latest.artifact_sha256
        or receipt.experience_content_hash != state.generation_experiences[-1].content_hash
        or receipt.task_id != binding.inputs.limits.task_id
        or receipt.shot_id != binding.context.target_shot_id
        or (not is_retarget and receipt.target_first_frame_sha256 != target.first_frame_sha256)
        or (is_retarget and receipt.target_first_frame_sha256 is not None)
        or request.base_project != target.target_project
    ):
        raise _state_invalid("Authored target differs from its retained paid source or exact new request.")
    try:
        if is_retarget:
            validate_authored_generation_retarget_binding(
                binding, selected, target, target_goal=receipt.target_goal,
                authorization_receipt_id=receipt.authorization_receipt_id,
            )
        else:
            validate_authored_revision_goal(
                receipt.old_goal,
                receipt.target_goal,
                goal_requirement_revisions=target.goal_requirement_revisions,
                authorization_receipt_id=receipt.authorization_receipt_id,
            )
            validate_authored_generation_revision_binding(
                binding, selected, target, target_goal=receipt.target_goal
            )
    except (AttributeError, KeyError, StopIteration, TypeError, ValueError) as exc:
        raise _state_invalid("Authored successor differs from its sealed target.", str(exc)) from exc

    # Match every retained submitted source to its durable same-task paid history.
    retained_paid = {}
    retained_attempt_ids = set()
    for item in binding.inputs.evidence:
        if item.task_id != target.task_id or item.outcome == "not_submitted":
            continue
        key = (item.attempt_id, item.request_hash)
        if key in retained_paid:
            if retained_paid[key] != item.shot_id:
                raise _state_invalid("Retained same-task paid evaluations disagree on Shot identity.")
            continue
        if item.attempt_id in retained_attempt_ids:
            raise _state_invalid("Retained same-task paid evidence changes an attempt request identity.")
        retained_paid[key] = item.shot_id
        retained_attempt_ids.add(item.attempt_id)
    if len(retained_paid) != binding.inputs.limits.paid_submits_used:
        raise _state_invalid("Retained same-task paid evidence count differs from the sealed submit count.")

    durable_paid = {}
    for attempt in manifest.attempts:
        prior = attempt.video_generation_state
        if prior is None:
            if (
                attempt.operation == "video_generation"
                and attempt.status in {StateCommitStatus.OUTCOME_UNKNOWN, StateCommitStatus.INTERRUPTED}
            ):
                raise _state_invalid("Unknown video history without an exact binding cannot be excluded from this task.")
            continue
        if (
            prior.execution_binding is not None
            and prior.execution_binding.binding_hash == binding.binding_hash
        ):
            # The current successor is admitted now and has not paid yet.
            continue
        if attempt.status in {StateCommitStatus.OUTCOME_UNKNOWN, StateCommitStatus.INTERRUPTED}:
            if prior.execution_binding is None:
                raise _state_invalid("Unknown video history without an exact binding cannot be excluded from this task.")
            prior_binding = committer._reopen_generation_execution_binding(prior.execution_binding)
            if prior_binding.inputs.limits.task_id == target.task_id:
                raise _state_invalid("Unknown or interrupted same-task history cannot authorize an authored revision.")
        if prior.execution_binding is None:
            if prior.paid_submit_receipt is not None or attempt.paid_provider_state is not None:
                raise _state_invalid(
                    "Paid history without an exact execution binding cannot be excluded from this task."
                )
            continue
        prior_binding = committer._reopen_generation_execution_binding(prior.execution_binding)
        if prior_binding.inputs.limits.task_id != target.task_id:
            continue
        prior_request = committer._reopen_video_request(prior.request)
        prior_binding.validate_request(prior_request)
        if attempt.paid_provider_state is not None:
            if attempt.paid_provider_state.submit_receipt != prior.paid_submit_receipt:
                raise _state_invalid("Durable same-task paid history has inconsistent submit receipt pointers.")
        submit_pointer = prior.paid_submit_receipt or (
            attempt.paid_provider_state.submit_receipt
            if attempt.paid_provider_state is not None else None
        )
        if submit_pointer is None:
            continue
        submit_receipt = committer._reopen_paid_submit(submit_pointer)
        if submit_receipt.attempt_id != attempt.attempt_id:
            raise _state_invalid("Durable same-task paid history differs from its exact attempt.")
        key = (attempt.attempt_id, prior_request.request_input_hash)
        if key in durable_paid:
            raise _state_invalid("Durable same-task paid history contains a duplicate attempt.")
        durable_paid[key] = prior_binding.context.target_shot_id
    if durable_paid != retained_paid:
        raise _state_invalid("Durable same-task paid history differs from all retained submitted evidence.")

