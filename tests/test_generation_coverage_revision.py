"""Pure admission tests for bounded authored coverage revisions."""

from types import SimpleNamespace

import pytest

from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.generation_coverage_revision import (
    CoverageRevisionTarget,
    allows_authored_coverage_revision,
    validate_coverage_target,
)
from ai_video.production.artifact_contracts import SourceReference
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.video import VideoGenerationRequest
from ai_video.production.video_requirement import ProviderNeutralVideoRequirement
from test_production_paid_submit_quota import _goal, _new_goal_pending


@pytest.fixture(scope="module")
def failed_media_case(tmp_path_factory):
    root = tmp_path_factory.mktemp("coverage-revision")
    writer, _, prior, experience, _ = _new_goal_pending(
        root, evaluation_verdict="FAIL", stop_after_goal=True
    )
    binding = writer._reopen_generation_execution_binding(
        prior.video_generation_state.execution_binding
    )
    assert any(item.verdict == "FAIL" for item in experience.evidence[-1].findings)
    return writer, prior, binding, experience


def _changed_intent(intent):
    return intent.model_copy(update={
        "subject_action": intent.subject_action.model_copy(update={
            "progression": "The subject pins the paper with one hand, then draws a single deliberate line.",
        }),
        "camera_intent": intent.camera_intent.model_copy(update={
            "framing_intent": "Locked medium composition that keeps the writing hand and paper contact visible.",
        }),
        "camera_endpoint": intent.camera_endpoint.model_copy(update={
            "start_framing": "Locked medium frame with paper and writing hand visible.",
        }),
        "axis_continuity": intent.axis_continuity.model_copy(update={
            "framing_continuity": "Hold the same side of the established counter axis.",
        }),
        "pacing": intent.pacing.model_copy(update={
            "cadence": "One continuous paper-contact action, with no inserted cut.",
        }),
    })


def _acceptance_revision(acceptance, *, failed_change=None, unfailed_change=None,
                         drop_required=False, add_diagnostic=False,
                         change_profile_metadata=False):
    data = acceptance.model_dump(mode="json")
    payload = data["profile_payload"]
    payload.pop("content_hash")
    version = f"{acceptance.profile_version}-coverage"
    payload["profile_version"] = version
    rules = [dict(rule) for rule in payload["generation_requirements"]]
    for rule in rules:
        if rule["requirement_id"] == "duration" and failed_change is not None:
            failed_change(rule)
        if rule["requirement_id"] == "performance" and unfailed_change is not None:
            unfailed_change(rule)
    if change_profile_metadata:
        payload["evaluation_policy_note"] = "ignore previously preserved nonfailed rules"
    if add_diagnostic:
        source = next(rule for rule in rules if rule["requirement_id"] == "performance")
        diagnostic = dict(source)
        diagnostic["requirement_id"] = "paper-contact-diagnostic"
        diagnostic["level"] = "diagnostic"
        diagnostic["observable"] = "Record whether the paper remains visible during the contact action."
        semantic = dict(diagnostic["semantics"])
        semantic["category"] = "diagnostic_observation"
        semantic.pop("hard_basis", None)
        diagnostic["semantics"] = semantic
        rules.append(diagnostic)
    payload["generation_requirements"] = rules
    digest = canonical_sha256(payload)
    payload["content_hash"] = digest
    data.update({
        "profile_version": version,
        "profile_content_hash": digest,
        "profile_payload": payload,
    })
    policy = DomainAcceptancePolicy.model_validate(data)
    if drop_required:
        # Model a sealed target object whose required-ID projection was
        # changed after load; normal policy construction rejects this earlier.
        policy = policy.model_copy(update={"required_requirement_ids": ("duration",)})
    return policy


def _target(experience, *, intent=None, acceptance=None, **acceptance_changes):
    acceptance = acceptance or _acceptance_revision(
        experience.candidate.recipe.acceptance_policy, **acceptance_changes
    )
    intent = intent or _changed_intent(experience.projection.requirement.generation_intent)
    rationale = "The prior exact evaluation found a missing paper-contact action; revise the authored action and camera coverage."
    try:
        return CoverageRevisionTarget.create(
            intent=intent,
            acceptance=acceptance,
            rationale=rationale,
        )
    except ValueError:
        # Preserve a deliberately malformed nested policy so the target
        # validator, rather than Pydantic construction, proves rejection.
        data = {
            "schema_version": "coverage-revision-target/1",
            "intent": intent.model_dump(mode="json"),
            "acceptance": acceptance.model_dump(mode="json"),
            "rationale": rationale,
        }
        return CoverageRevisionTarget.model_construct(
            schema_version="coverage-revision-target/1",
            intent=intent,
            acceptance=acceptance,
            rationale=rationale,
            content_hash=canonical_sha256(data),
        )


def _pure_binding(failed_media_case, *, quota_used=1, quota_ceiling=2,
                  new_intent=None, changed_request="prompt", unknown=False,
                  candidate_id=None):
    _writer, _attempt, old_binding, experience = failed_media_case
    evidence = experience.evidence[-1]
    baseline = old_binding.compiled_request.activation_scope.request
    payload = baseline.model_dump(mode="python", exclude={"request_input_hash"})
    if changed_request != "noop":
        payload["prompt_text"] = payload["prompt_text"] + "\n\nSealed paper-contact coverage revision."
    if changed_request == "model":
        payload["model_id"] = "different-model"
    elif changed_request == "reference":
        references = list(payload["image_bindings"])
        references[0] = {**references[0], "asset_sha256": "a" * 64}
        payload["image_bindings"] = tuple(references)
    current_request = VideoGenerationRequest.create(**payload)

    acceptance = _acceptance_revision(experience.candidate.recipe.acceptance_policy)
    target_goal = _goal("2")
    selected = SimpleNamespace(
        candidate_id=candidate_id or experience.candidate.candidate_id,
        capabilities=experience.candidate.capabilities,
        capability_id=experience.candidate.capability_id,
        output_requirement=experience.candidate.output_requirement,
        final_output_goal=target_goal,
        recipe=SimpleNamespace(acceptance_policy=acceptance),
    )
    current_intent = new_intent or _changed_intent(experience.projection.requirement.generation_intent)
    current_requirement = experience.projection.requirement.model_copy(
        update={"generation_intent": current_intent}
    )
    current_projection = SimpleNamespace(requirement=current_requirement)
    inputs_evidence = (evidence,)
    if unknown:
        inputs_evidence = (*inputs_evidence, evidence.model_copy(update={
            "attempt_id": "coverage-unknown-predecessor",
            "outcome": "unknown_outcome",
            "artifact_sha256": None,
            "findings": (),
        }))
    limits = SimpleNamespace(
        paid_submits_used=quota_used,
        paid_submit_ceiling=quota_ceiling,
        generation_forbidden=False,
        allowed_remote_candidates=(selected.candidate_id,),
        task_id=evidence.task_id,
    )
    inputs = SimpleNamespace(
        limits=limits,
        policy=SimpleNamespace(max_resamples=0),
        runtime_repairs=(),
        candidates=(selected,),
        experiences=(experience,),
        evidence=inputs_evidence,
        latest_attempt_hash=evidence.evidence_hash,
        baseline_request=baseline,
    )
    return SimpleNamespace(
        policy=SimpleNamespace(
            execution_purpose="qualification",
            remote_authorized=True,
            budget_authorized=True,
        ),
        inputs=inputs,
        decision=SimpleNamespace(runtime_repair=None, intervention=None),
        context=SimpleNamespace(target_shot_id=evidence.shot_id),
        projection=current_projection,
        compiled_request=SimpleNamespace(
            activation_scope=SimpleNamespace(request=current_request)
        ),
    ), selected


def test_target_is_sealed_and_repairs_only_failed_rule(failed_media_case):
    _writer, _attempt, old_binding, experience = failed_media_case
    target = _target(
        experience,
        failed_change=lambda rule: rule.update(
            observable="Keep the paper flat under the thumb through one visible pen stroke.",
            measurement="frame-by-frame visible paper and fingertip contact",
            intent_paths=["generation_intent.subject_action.progression"],
        ),
        add_diagnostic=True,
    )

    assert target.verify() == target
    validate_coverage_target(old_binding, experience, target)
    assert target.acceptance.profile_content_hash != experience.candidate.recipe.rubric_hash
    assert "paper-contact-diagnostic" in {
        item["requirement_id"]
        for item in target.acceptance.profile_payload["generation_requirements"]
    }


@pytest.mark.parametrize("protected_change", [
    "identity", "dialogue", "audio", "music", "scene", "space", "duration",
    "action_start", "action_endpoint", "visual", "lighting",
])
def test_coverage_target_rejects_changes_outside_action_and_camera(protected_change, failed_media_case):
    from ai_video.production.video_requirement import (
        ActionEndpoint,
        AmbienceIntent,
        ConversationTurn,
        DialogueIntent,
        LightingIntent,
        MusicIntent,
        SceneContinuity,
        VisualTreatment,
    )

    _writer, _attempt, old_binding, experience = failed_media_case
    intent = _changed_intent(experience.projection.requirement.generation_intent)
    if protected_change == "identity":
        intent = intent.model_copy(update={
            "identity_continuity": intent.identity_continuity.model_copy(update={
                "allowed_variation": ("change the face",),
            })
        })
    elif protected_change == "dialogue":
        intent = intent.model_copy(update={
            "dialogue_intent": DialogueIntent(
                mode="conversation",
                language="zh-CN",
                turns=(ConversationTurn(
                    speaker_id="linxu",
                    verbatim_text="慢点。",
                    on_screen=True,
                    response_obligation="Wait for the clerk to finish speaking.",
                    lip_sync_required=True,
                ),),
            )
        })
    elif protected_change == "music":
        intent = intent.model_copy(update={"music_intent": MusicIntent(mode="none")})
    elif protected_change == "audio":
        intent = intent.model_copy(update={
            "ambience_intent": AmbienceIntent(
                environment_bed="steady rain under the fluorescent hum",
                foley_cues=("paper slides across the counter",),
            )
        })
    elif protected_change == "scene":
        intent = intent.model_copy(update={
            "scene_continuity": SceneContinuity(scene_id=experience.projection.requirement.scene.scene_id)
        })
    elif protected_change == "space":
        intent = intent.model_copy(update={
            "space_continuity": intent.space_continuity.model_copy(update={
                "subject_position": "opposite side of the counter",
            })
        })
    elif protected_change == "duration":
        intent = intent.model_copy(update={
            "pacing": intent.pacing.model_copy(update={"shot_duration_seconds": 15.0})
        })
    elif protected_change == "action_start":
        intent = intent.model_copy(update={
            "subject_action": intent.subject_action.model_copy(update={
                "start_state": "the clerk has already lifted the rice ball",
            })
        })
    elif protected_change == "action_endpoint":
        intent = intent.model_copy(update={
            "subject_action": intent.subject_action.model_copy(update={
                "endpoint": ActionEndpoint(state_text="the rice ball is left on the empty paper"),
            })
        })
    elif protected_change == "visual":
        intent = intent.model_copy(update={
            "visual_treatment": VisualTreatment(
                medium_look="flat cel shading",
                palette="bright saturated primary colors",
                material_treatment="plastic skin",
                prohibited_visual_drift=("photoreal CG",),
            )
        })
    else:
        intent = intent.model_copy(update={
            "lighting_intent": LightingIntent(
                motivated_source="unmotivated overhead spotlight",
                direction="directly overhead",
                exposure_priority="blown out highlights",
                continuity_state="hard jump from prior frame",
            )
        })

    with pytest.raises(ValueError):
        validate_coverage_target(old_binding, experience, _target(experience, intent=intent))


@pytest.mark.parametrize("bad_acceptance", [
    "change_unfailed", "failed_identity", "drop_required", "profile_metadata",
])
def test_coverage_target_rejects_weakening_or_changing_protected_qa(bad_acceptance, failed_media_case):
    _writer, _attempt, old_binding, experience = failed_media_case
    if bad_acceptance == "change_unfailed":
        acceptance = _acceptance_revision(
            experience.candidate.recipe.acceptance_policy,
            unfailed_change=lambda rule: rule.update(observable="Changed an unevaluated rule."),
        )
        target = _target(experience, acceptance=acceptance)
    elif bad_acceptance == "failed_identity":
        acceptance = _acceptance_revision(
            experience.candidate.recipe.acceptance_policy,
            failed_change=lambda rule: rule.update(proof="human"),
        )
        target = _target(experience, acceptance=acceptance)
    elif bad_acceptance == "drop_required":
        acceptance = _acceptance_revision(
            experience.candidate.recipe.acceptance_policy,
            drop_required=True,
        )
        target = _target(experience, acceptance=acceptance)
    else:
        acceptance = _acceptance_revision(
            experience.candidate.recipe.acceptance_policy,
            change_profile_metadata=True,
        )
        target = _target(experience, acceptance=acceptance)

    with pytest.raises((ValueError, TypeError)):
        validate_coverage_target(old_binding, experience, target)


def test_coverage_target_rejects_noop_intent_and_tampered_seal(failed_media_case):
    _writer, _attempt, old_binding, experience = failed_media_case
    old_intent = experience.projection.requirement.generation_intent
    target = _target(experience, intent=old_intent)
    with pytest.raises(ValueError, match="only authored action/camera"):
        validate_coverage_target(old_binding, experience, target)
    with pytest.raises(ValueError, match="content hash"):
        target.model_copy(update={"rationale": "unsealed reason"}).verify()


def test_coverage_target_requires_a_known_failed_raw_rule(failed_media_case):
    _writer, _attempt, old_binding, experience = failed_media_case
    latest = experience.evidence[-1]
    no_failure = latest.model_copy(update={
        "findings": tuple(
            item.model_copy(update={"verdict": "NOT_EVALUATED"})
            if item.verdict == "FAIL" else item
            for item in latest.findings
        )
    })
    no_failure_experience = experience.model_copy(update={
        "evidence": (*experience.evidence[:-1], no_failure),
    })
    with pytest.raises(ValueError, match="known raw-generation failure"):
        validate_coverage_target(old_binding, no_failure_experience, _target(experience))


def _serialized_shot_lineage_revision(requirement, *, bad_asset_hash=False,
                                      drop_constraint=False, change_dialogue=False):
    old_shot = seal_artifact(requirement.target_shot.model_copy(update={
        "continuity_constraints": ("Keep the original counter axis.",),
    }))
    old_asset = requirement.asset_evidence[0].model_copy(update={
        "canonical_owner_id": old_shot.shot_id,
        "canonical_owner_content_hash": old_shot.content_hash,
    })
    old_data = requirement.model_dump(mode="python", exclude={"requirement_id", "requirement_hash"})
    old_data.update(target_shot=old_shot, asset_evidence=(old_asset,))
    old_requirement = ProviderNeutralVideoRequirement.create(**old_data)
    old_shot = old_requirement.target_shot
    shot_changes = {
        "revision": old_shot.revision + 1,
        "creation_receipt_id": "coverage-revision-shot",
        "source_provenance": (
            *old_shot.source_provenance,
            SourceReference(kind="user_input", reference="coverage revision authoring"),
        ),
        "intent": old_shot.intent + " Keep the established D design and add explicit coverage.",
        "continuity_constraints": (
            () if drop_constraint else (*old_shot.continuity_constraints, "Keep the new paper-contact camera coverage.")
        ),
    }
    if change_dialogue:
        shot_changes["dialogue"] = old_shot.dialogue + " Changed dialogue."
    new_shot = seal_artifact(old_shot.model_copy(update=shot_changes))
    new_asset = old_asset.model_copy(update={
        "canonical_owner_content_hash": (
            "a" * 64 if bad_asset_hash else new_shot.content_hash
        )
    })
    new_data = old_requirement.model_dump(mode="python", exclude={"requirement_id", "requirement_hash"})
    new_data.update({
        "target_shot": new_shot,
        "asset_evidence": (new_asset,),
        "source_request_content_hash": "b" * 64,
        "generation_intent": _changed_intent(old_requirement.generation_intent),
        "intent_evidence_hash": "c" * 64,
        "generation_intent_hash": "d" * 64,
    })
    return old_requirement, ProviderNeutralVideoRequirement.create(**new_data)


def test_requirement_lineage_allows_exact_resealed_shot_and_owned_asset_revision(failed_media_case):
    from ai_video.production.generation_coverage_revision import _non_intent_requirement_facts_match

    _writer, _attempt, _binding, experience = failed_media_case
    old, new = _serialized_shot_lineage_revision(experience.projection.requirement)
    assert old.target_shot.continuity_constraints == new.target_shot.continuity_constraints[:
        len(old.target_shot.continuity_constraints)
    ]
    assert new.target_shot.content_hash != old.target_shot.content_hash
    assert new.asset_evidence[0].canonical_owner_content_hash == new.target_shot.content_hash
    assert _non_intent_requirement_facts_match(old, new)


@pytest.mark.parametrize("change", ["wrong_owner_hash", "asset_bytes", "dropped_constraint", "dialogue"])
def test_requirement_lineage_rejects_unrelated_asset_or_shot_changes(failed_media_case, change):
    from ai_video.production.generation_coverage_revision import _non_intent_requirement_facts_match

    _writer, _attempt, _binding, experience = failed_media_case
    if change == "wrong_owner_hash":
        old, new = _serialized_shot_lineage_revision(
            experience.projection.requirement, bad_asset_hash=True
        )
    elif change == "dropped_constraint":
        old, new = _serialized_shot_lineage_revision(
            experience.projection.requirement, drop_constraint=True
        )
    elif change == "dialogue":
        old, new = _serialized_shot_lineage_revision(
            experience.projection.requirement, change_dialogue=True
        )
    else:
        old, new = _serialized_shot_lineage_revision(experience.projection.requirement)
        altered = new.asset_evidence[0].model_copy(update={"asset_sha256": "e" * 64})
        new = new.model_copy(update={"asset_evidence": (altered,)})
    assert not _non_intent_requirement_facts_match(old, new)


def test_pure_admission_accepts_single_same_provider_prompt_revision(failed_media_case):
    binding, selected = _pure_binding(failed_media_case)
    assert allows_authored_coverage_revision(binding, selected)


@pytest.mark.parametrize("case", [
    "reset", "expanded", "unknown", "model", "reference", "candidate", "noop",
    "resample", "intervention", "runtime_repair",
])
def test_pure_admission_rejects_counter_unknown_or_execution_scope_drift(case, failed_media_case):
    options = {}
    if case == "reset":
        options.update(quota_used=0, quota_ceiling=1)
    elif case == "expanded":
        options.update(quota_used=1, quota_ceiling=3)
    elif case == "unknown":
        options["unknown"] = True
    elif case in {"model", "reference"}:
        options["changed_request"] = case
    elif case == "noop":
        options["changed_request"] = "noop"
        _writer, _attempt, old_binding, experience = failed_media_case
        options["new_intent"] = experience.projection.requirement.generation_intent
    elif case == "candidate":
        options["candidate_id"] = "different-candidate"
    binding, selected = _pure_binding(failed_media_case, **options)
    if case == "resample":
        binding.inputs.policy.max_resamples = 1
    elif case == "intervention":
        binding.decision.intervention = object()
    elif case == "runtime_repair":
        binding.inputs.runtime_repairs = (object(),)
    assert not allows_authored_coverage_revision(binding, selected)


def test_submit_lock_requires_the_exact_coverage_supersession(tmp_path):
    from ai_video.errors import AiVideoError
    from ai_video.production.generation_coverage_revision import (
        require_authored_coverage_revision_predecessor,
    )
    from ai_video.production.models import canonical_project_snapshot_path
    from test_generation_coverage_supersession import _inputs
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="FAIL")
    args = _inputs(writer, prior, experience)
    old_state = prior.video_generation_state
    old_binding = writer._reopen_generation_execution_binding(old_state.execution_binding)
    baseline = writer._reopen_video_request(old_state.request).activation_scope.request
    evidence = experience.evidence[-1]
    selected = experience.candidate.model_copy(update={"final_output_goal": args["target_goal"]})
    raw = baseline.model_dump(mode="python", exclude={"request_input_hash"})
    raw["prompt_text"] += "\n\nKeep the original first frame while correcting action coverage."
    next_revision = baseline.base_project.revision + 1
    raw["base_project"] = baseline.base_project.model_copy(update={
        "revision": next_revision,
        "path": canonical_project_snapshot_path(next_revision, baseline.base_project.content_hash),
    })
    current_request = VideoGenerationRequest.create(**raw)
    inputs = old_binding.inputs.model_copy(update={
        "candidates": (selected,),
        "experiences": (experience,),
        "evidence": experience.evidence,
        "latest_attempt_hash": evidence.evidence_hash,
        "baseline_request": baseline,
        "limits": old_binding.inputs.limits.model_copy(update={
            "paid_submits_used": 1,
            "paid_submit_ceiling": 2,
            "allowed_remote_candidates": (selected.candidate_id,),
        }),
        "policy": old_binding.inputs.policy.model_copy(update={"max_resamples": 0}),
        "runtime_repairs": (),
    })
    current_projection = experience.projection.model_copy(update={
        "requirement": experience.projection.requirement.model_copy(update={
            "generation_intent": args["coverage_revision"].intent,
        })
    })
    prospective = SimpleNamespace(
        policy=SimpleNamespace(
            execution_purpose="qualification",
            remote_authorized=True,
            budget_authorized=True,
        ),
        inputs=inputs,
        projection=current_projection,
        context=old_binding.context,
        decision=SimpleNamespace(
            selected_candidate_id=selected.candidate_id,
            runtime_repair=None,
            intervention=None,
        ),
        compiled_request=SimpleNamespace(activation_scope=SimpleNamespace(request=current_request)),
    )
    assert allows_authored_coverage_revision(prospective, selected)

    before = writer._read_manifest()
    with writer._exclusive_lock(), pytest.raises(AiVideoError, match="canonical supersession"):
        require_authored_coverage_revision_predecessor(writer, before, prospective)

    closed = writer.supersede_video_generation(**args)
    with writer._exclusive_lock():
        require_authored_coverage_revision_predecessor(writer, closed, prospective)
