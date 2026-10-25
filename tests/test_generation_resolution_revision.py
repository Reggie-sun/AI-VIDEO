"""Pure contracts for narrowly increasing an adaptive video output tier."""

from types import SimpleNamespace

import pytest

from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.generation_resolution_revision import (
    ResolutionRevisionTarget,
    allows_authored_resolution_revision,
    _same_requirement_facts,
    validate_resolution_target,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.video import VideoGenerationRequest


def _output(resolution_label: str) -> VideoFlexibleOutputRequirement:
    return VideoFlexibleOutputRequirement(
        timing_mode="nominal_seconds",
        duration_seconds=16,
        dimension_mode="adaptive",
        fps=None,
        resolution_label=resolution_label,
        ratio="16:9",
        container="mp4",
        mime_type="video/mp4",
        native_audio=True,
    )


def _target(old="480p", new="1080p", **changes):
    return ResolutionRevisionTarget.create(
        old_output=_output(old),
        target_output=_output(new).model_copy(update=changes),
        rationale="The approved low-resolution sample should be regenerated at the selected delivery tier.",
    )


def _validation_case(*, findings=("PASS", "NOT_EVALUATED"), request_hash="a" * 64):
    old_output = _output("480p")
    target = ResolutionRevisionTarget.create(
        old_output=old_output,
        target_output=_output("1080p"),
        rationale="Raise the approved adaptive output tier while retaining every other request fact.",
    )
    request = SimpleNamespace(
        request_input_hash=request_hash,
        output_requirement=old_output,
    )
    candidate = SimpleNamespace(
        candidate_id="seedance-25-image-to-video",
        output_requirement=old_output,
        scope_hash="c" * 64,
        recipe=SimpleNamespace(rubric_hash="d" * 64),
    )
    requirement = SimpleNamespace(
        generation_intent="sealed-intent",
        model_dump=lambda **_kwargs: {"generation_intent": "sealed-intent"},
    )
    projection = SimpleNamespace(requirement=requirement)
    evidence = SimpleNamespace(
        outcome="media",
        artifact_sha256="b" * 64,
        request_hash=request_hash,
        task_id="shizhen-s01",
        shot_id="S01",
        recipe_scope_hash=candidate.scope_hash,
        facts_hash=canonical_sha256({"generation_intent": "sealed-intent"}),
        rubric_hash=candidate.recipe.rubric_hash,
        stage="raw_generation",
        findings=tuple(SimpleNamespace(verdict=item) for item in findings),
    )
    binding = SimpleNamespace(
        projection=projection,
        decision=SimpleNamespace(selected_candidate_id=candidate.candidate_id),
        inputs=SimpleNamespace(
            candidates=(candidate,),
            limits=SimpleNamespace(task_id="shizhen-s01"),
        ),
        compiled_request=SimpleNamespace(
            activation_scope=SimpleNamespace(request=request),
        ),
        context=SimpleNamespace(target_shot_id="S01"),
    )
    experience = SimpleNamespace(
        projection=projection,
        candidate=candidate,
        evidence=(evidence,),
    )
    return binding, experience, target


def test_resolution_target_seals_only_a_strict_adaptive_tier_increase():
    target = _target()

    assert target.verify() == target
    assert target.old_output.resolution_label == "480p"
    assert target.target_output.resolution_label == "1080p"

    with pytest.raises(ValueError):
        _target("1080p", "720p")
    with pytest.raises(ValueError):
        _target("480p", "1080p", native_audio=False)
    with pytest.raises(ValueError):
        _target("480p", "1080p", width=1920)


def test_resolution_target_revalidates_nested_models_and_content_hash():
    target = _target()
    malformed_output = target.target_output.model_copy(update={"width": 1920})
    malformed = target.model_copy(update={"target_output": malformed_output})

    with pytest.raises(ValueError):
        malformed.verify()


def test_resolution_target_accepts_exact_latest_media_with_ne_findings():
    binding, experience, target = _validation_case()

    validate_resolution_target(binding, experience, target)


@pytest.mark.parametrize(
    "mutation",
    ["projection", "candidate", "output", "request", "task", "shot", "artifact", "fail"],
)
def test_resolution_target_rejects_mismatched_or_failed_prior_media(mutation):
    binding, experience, target = _validation_case()
    if mutation == "projection":
        experience.projection = SimpleNamespace(requirement=SimpleNamespace(generation_intent="other"))
    elif mutation == "candidate":
        experience.candidate = SimpleNamespace(candidate_id="different", output_requirement=target.old_output)
    elif mutation == "output":
        binding.inputs.candidates[0].output_requirement = _output("720p")
    elif mutation == "request":
        binding.compiled_request.activation_scope.request.request_input_hash = "c" * 64
    elif mutation == "task":
        experience.evidence[0].task_id = "different-task"
    elif mutation == "shot":
        experience.evidence[0].shot_id = "S02"
    elif mutation == "artifact":
        experience.evidence[0].artifact_sha256 = None
    else:
        experience.evidence[0].findings = (SimpleNamespace(verdict="FAIL"),)

    with pytest.raises(ValueError):
        validate_resolution_target(binding, experience, target)


@pytest.fixture(scope="module")
def adaptive_history(tmp_path_factory):
    from test_production_paid_submit_quota import _new_goal_pending

    root = tmp_path_factory.mktemp("resolution-admission")
    writer, _project, attempt, experience, _source = _new_goal_pending(
        root,
        stop_after_goal=True,
        evaluation_verdict="NOT_EVALUATED",
    )
    old_binding = writer._reopen_generation_execution_binding(
        attempt.video_generation_state.execution_binding
    )
    old_candidate = old_binding.inputs.candidates[0]
    request = old_binding.compiled_request.activation_scope.request
    fixed = old_candidate.output_requirement
    old_output = _output("480p").model_copy(
        update={
            "duration_seconds": fixed.duration_seconds,
            "ratio": "1:1" if fixed.width == fixed.height else "16:9",
            "fps": fixed.fps,
            "native_audio": fixed.native_audio,
        }
    )
    old_candidate = old_candidate.model_copy(update={"output_requirement": old_output})
    request_data = request.model_dump(mode="python", exclude={"request_input_hash"})
    request_data["output_requirement"] = old_output
    baseline = VideoGenerationRequest.create(**request_data)
    return old_binding, old_candidate, baseline, experience


def _admission_case(adaptive_history):
    from types import SimpleNamespace

    from test_production_paid_submit_quota import _goal

    from ai_video.production.video_requirement import GenerationIntent

    old_binding, old_candidate, baseline, original_experience = adaptive_history
    target_output = old_candidate.output_requirement.model_copy(
        update={"resolution_label": "1080p"}
    )
    selected = old_candidate.model_copy(
        update={
            "output_requirement": target_output,
            "final_output_goal": _goal("2"),
        }
    )
    current_data = baseline.model_dump(mode="python", exclude={"request_input_hash"})
    current_data["output_requirement"] = target_output
    current_request = VideoGenerationRequest.create(**current_data)
    evidence = original_experience.evidence[-1].model_copy(
        update={
            "request_hash": baseline.request_input_hash,
            "recipe_scope_hash": old_candidate.scope_hash,
        }
    )
    experience = SimpleNamespace(
        projection=old_binding.projection,
        candidate=old_candidate,
        evidence=(evidence,),
    )
    inputs = SimpleNamespace(
        limits=SimpleNamespace(
            task_id=evidence.task_id,
            generation_forbidden=False,
            allowed_remote_candidates=(selected.candidate_id,),
            paid_submits_used=1,
            paid_submit_ceiling=2,
        ),
        policy=SimpleNamespace(max_resamples=0),
        runtime_repairs=(),
        candidates=(selected,),
        experiences=(experience,),
        evidence=(evidence,),
        latest_attempt_hash=evidence.evidence_hash,
        baseline_request=baseline,
    )
    binding = SimpleNamespace(
        policy=SimpleNamespace(
            execution_purpose="qualification",
            remote_authorized=True,
            budget_authorized=True,
        ),
        inputs=inputs,
        decision=SimpleNamespace(
            selected_candidate_id=selected.candidate_id,
            runtime_repair=None,
            intervention=None,
        ),
        context=SimpleNamespace(target_shot_id=evidence.shot_id),
        projection=old_binding.projection,
        compiled_request=SimpleNamespace(
            activation_scope=SimpleNamespace(request=current_request),
        ),
    )
    return binding, selected, experience, GenerationIntent


def test_admission_allows_one_output_only_tier_increase_after_exact_known_media(adaptive_history):
    binding, selected, _experience, _generation_intent = _admission_case(adaptive_history)

    assert allows_authored_resolution_revision(binding, selected)


@pytest.mark.parametrize(
    "mutation",
    ["prompt", "frame", "qa", "intent", "task", "reset", "unknown", "history", "resample", "fail"],
)
def test_admission_rejects_changes_to_history_or_protected_generation_facts(
    adaptive_history, mutation
):
    from types import SimpleNamespace

    from ai_video.production.video import VideoGenerationRequest

    binding, selected, experience, GenerationIntent = _admission_case(adaptive_history)
    if mutation in {"prompt", "frame"}:
        current = binding.compiled_request.activation_scope.request
        values = current.model_dump(mode="python", exclude={"request_input_hash"})
        if mutation == "prompt":
            values["prompt_text"] += " Altered prompt."
        else:
            images = list(values["image_bindings"])
            image = dict(images[0])
            image["asset_sha256"] = "f" * 64
            images[0] = image
            values["image_bindings"] = tuple(images)
        binding.compiled_request.activation_scope.request = VideoGenerationRequest.create(**values)
    elif mutation == "qa":
        altered_policy = SimpleNamespace(profile_version="changed")
        altered_recipe = SimpleNamespace(
            acceptance_policy=altered_policy,
            expressions=selected.recipe.expressions,
        )
        selected = selected.model_copy(update={"recipe": altered_recipe})
        binding.inputs.candidates = (selected,)
    elif mutation == "intent":
        requirement = binding.projection.requirement.model_copy(
            update={"generation_intent": GenerationIntent()}
        )
        binding.projection = binding.projection.model_copy(update={"requirement": requirement})
    elif mutation == "task":
        binding.inputs.limits.task_id = "different-task"
    elif mutation == "reset":
        binding.inputs.limits.paid_submits_used = 0
        binding.inputs.limits.paid_submit_ceiling = 1
    elif mutation == "unknown":
        unknown = experience.evidence[-1].model_copy(
            update={"outcome": "unknown_outcome", "artifact_sha256": None, "findings": ()}
        )
        binding.inputs.evidence = (*binding.inputs.evidence, unknown)
    elif mutation == "history":
        duplicate_submit = experience.evidence[-1].model_copy(
            update={"attempt_id": "unrecorded-extra-submit"}
        )
        binding.inputs.evidence = (*binding.inputs.evidence, duplicate_submit)
    elif mutation == "fail":
        failed_finding = experience.evidence[-1].findings[0].model_copy(
            update={"verdict": "FAIL"}
        )
        failed_evidence = experience.evidence[-1].model_copy(
            update={"findings": (failed_finding,)}
        )
        experience.evidence = (failed_evidence,)
        binding.inputs.experiences = (experience,)
        binding.inputs.evidence = (failed_evidence,)
        binding.inputs.latest_attempt_hash = failed_evidence.evidence_hash
    else:
        binding.inputs.policy.max_resamples = 1

    assert not allows_authored_resolution_revision(binding, selected)


def test_requirement_facts_allow_only_same_semantic_shot_revision_lineage(adaptive_history):
    requirement = adaptive_history[0].projection.requirement
    old_shot = requirement.target_shot
    new_shot = old_shot.model_copy(
        update={
            "revision": old_shot.revision + 1,
            "content_hash": "f" * 64,
            "creation_receipt_id": "shot-revision-receipt-4",
            "source_provenance": tuple(
                item.model_copy(update={"reference": f"{item.reference}-revision-4"})
                for item in old_shot.source_provenance
            ),
        }
    )
    old_asset = requirement.asset_evidence[0].model_copy(
        update={
            "canonical_owner_id": old_shot.shot_id,
            "canonical_owner_content_hash": old_shot.content_hash,
        }
    )
    new_asset = old_asset.model_copy(
        update={"canonical_owner_content_hash": new_shot.content_hash}
    )
    old_requirement = requirement.model_copy(update={"asset_evidence": (old_asset,)})
    new_requirement = old_requirement.model_copy(
        update={
            "target_shot": new_shot,
            "asset_evidence": (new_asset,),
            "requirement_id": "video-requirement-revision-4",
            "requirement_hash": "a" * 64,
            "source_request_content_hash": "b" * 64,
            "intent_evidence_hash": "c" * 64,
            "generation_intent_hash": "d" * 64,
        }
    )

    assert _same_requirement_facts(old_requirement, new_requirement)

    changed_intent = new_shot.model_copy(update={"intent": new_shot.intent + " changed"})
    changed_creative = new_requirement.model_copy(update={"target_shot": changed_intent})
    changed_asset = new_asset.model_copy(update={"asset_sha256": "e" * 64})
    changed_pixels = new_requirement.model_copy(update={"asset_evidence": (changed_asset,)})
    non_shot_old = old_asset.model_copy(
        update={"canonical_owner_id": "scene-owner", "canonical_owner_content_hash": "1" * 64}
    )
    non_shot_new = non_shot_old.model_copy(update={"canonical_owner_content_hash": "2" * 64})
    changed_non_shot_owner = new_requirement.model_copy(
        update={"asset_evidence": (non_shot_new,)}
    )
    non_shot_baseline = old_requirement.model_copy(update={"asset_evidence": (non_shot_old,)})

    assert not _same_requirement_facts(old_requirement, changed_creative)
    assert not _same_requirement_facts(old_requirement, changed_pixels)
    assert not _same_requirement_facts(non_shot_baseline, changed_non_shot_owner)
