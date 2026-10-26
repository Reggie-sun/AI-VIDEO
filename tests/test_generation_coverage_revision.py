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


def _authored_revision_target(old_binding, experience, *, revised_ids=("duration", "performance"),
                              target_project=None, goal_requirement_revisions=()):
    from ai_video.production.generation_authoring_revision import AuthoredGenerationRevisionTarget
    from ai_video.production.models import ProjectSnapshotPointer, canonical_project_snapshot_path
    from ai_video.production._shot_router_contracts import AdapterCompilerContract
    from ai_video.production.video import VideoGenerationMode
    from ai_video.production.video_contracts import VideoFlexibleOutputRequirement

    old_candidate = experience.candidate
    baseline = old_binding.compiled_request.activation_scope.request
    variant = next(item for item in old_candidate.capabilities.variants
                   if item.capability_id == old_candidate.capability_id)
    old_intent = experience.projection.requirement.generation_intent
    performance = old_intent.performance_intent
    if performance is None:
        from ai_video.production.performance_direction import PerformanceIntent

        performance = PerformanceIntent(
            trigger="The clerk vanishes mid-transaction.",
            visible_response="The lead's gaze snaps to the empty place while the reach is still directed there.",
            gaze_target="The precise point where the clerk stood.",
            body_behavior="The lead's reaching hand stops in midair, then draws back by a few centimeters.",
            hand_behavior="Fingers remain half-curled around nothing for a brief beat.",
            terminal_performance_state="Alert and disbelieving, still facing the empty place.",
        )
    else:
        performance = performance.model_copy(update={
            "visible_response": "The lead reacts at once to the clerk's disappearance, still facing the empty place.",
            "gaze_target": "The exact place the clerk occupied.",
        })
    intent = old_intent.model_copy(update={"performance_intent": performance})

    old_acceptance = old_candidate.recipe.acceptance_policy
    data = old_acceptance.model_dump(mode="json")
    payload = data["profile_payload"]
    payload.pop("content_hash")
    payload["profile_version"] = f"{old_acceptance.profile_version}-authored"
    rows = [dict(row) for row in payload["generation_requirements"]]
    changed = False
    for row in rows:
        if row["requirement_id"] == "duration":
            row["observable"] = "The full disappearance and immediate reaction play within the approved 18-second window."
            changed = True
        if row["requirement_id"] == "performance":
            row["observable"] = "The lead reacts during the disappearance, while still facing the clerk's position."
            changed = True
    assert changed
    payload["generation_requirements"] = rows
    digest = canonical_sha256(payload)
    payload["content_hash"] = digest
    data.update(profile_version=payload["profile_version"], profile_content_hash=digest,
                profile_payload=payload)
    acceptance = DomainAcceptancePolicy.model_validate(data)

    old_request = old_binding.compiled_request.activation_scope.request
    project_revision = old_request.base_project.revision + 1
    project_hash = "d" * 64
    target_project = target_project or ProjectSnapshotPointer(
        path=canonical_project_snapshot_path(project_revision, project_hash),
        revision=project_revision,
        content_hash=project_hash,
        file_sha256="e" * 64,
    )
    output = VideoFlexibleOutputRequirement(
        timing_mode="exact_seconds", duration_seconds=18,
        dimension_mode="exact", width=1920, height=1080,
        resolution_label="1080p", ratio="16:9", fps=24,
        container="mp4", mime_type="video/mp4", native_audio=True,
    )
    return AuthoredGenerationRevisionTarget.create(
        task_id=old_binding.inputs.limits.task_id,
        shot_id=old_binding.context.target_shot_id,
        intent=intent,
        acceptance=acceptance,
        output_requirement=output,
        provider_name=old_candidate.capabilities.provider_name,
        provider_kind=variant.provider_kind,
        model_id=variant.model_id,
        provider_profile=old_candidate.provider_profile,
        capability_id="first-frame-v1",
        capabilities_fingerprint="c" * 64,
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="jimeng-seedance-2.5-first-frame-video-compiler",
            compiler_version="1",
        ),
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        target_project=target_project,
        first_frame_sha256="f" * 64,
        revised_requirement_ids=revised_ids,
        rationale="User explicitly revised the disappearance performance and approved a complete 18-second 1080p retake.",
        goal_requirement_revisions=goal_requirement_revisions,
    )


def test_authored_revision_can_change_performance_duration_and_an_explicitly_revised_pass_rule(tmp_path):
    from types import SimpleNamespace
    from ai_video.production.generation_authoring_revision import (
        validate_authored_generation_revision_target,
    )
    from ai_video.production.video import VideoImageReferenceBinding
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="PASS")
    old_binding = writer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    target = _authored_revision_target(old_binding, experience)
    assert any(item.requirement_id == "duration" and item.verdict == "PASS"
               for item in experience.evidence[-1].findings)

    # The original request may contain multimodal references without a first-frame endpoint.
    baseline = old_binding.compiled_request.activation_scope.request
    references = tuple(VideoImageReferenceBinding(
        role="reference", asset_id=f"old-reference-{index}", asset_sha256=f"{index + 1:x}" * 64,
        mime_type="image/png", width=1920, height=1080,
    ) for index in range(3))
    synthetic_request = SimpleNamespace(
        request_input_hash=baseline.request_input_hash,
        base_project=baseline.base_project,
        image_bindings=references,
    )
    synthetic_binding = SimpleNamespace(
        inputs=old_binding.inputs,
        context=old_binding.context,
        decision=old_binding.decision,
        projection=old_binding.projection,
        compiled_request=SimpleNamespace(
            activation_scope=SimpleNamespace(request=synthetic_request),
        ),
    )
    validate_authored_generation_revision_target(synthetic_binding, experience, target)


@pytest.mark.parametrize("change", ["unlisted_rule", "wrong_task", "same_project_revision", "wrong_model"])
def test_authored_revision_target_rejects_unlisted_or_misbound_changes(tmp_path, change):
    from ai_video.production.generation_authoring_revision import (
        validate_authored_generation_revision_target,
    )
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="PASS")
    old_binding = writer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    target = _authored_revision_target(old_binding, experience)
    if change == "unlisted_rule":
        target = _authored_revision_target(old_binding, experience, revised_ids=())
    elif change == "wrong_task":
        target = target.model_copy(update={"task_id": "different-task"})
        target = target.model_copy(update={
            "content_hash": canonical_sha256(target.model_dump(mode="json", exclude={"content_hash"})),
        })
    elif change == "same_project_revision":
        target = target.model_copy(update={"target_project": old_binding.compiled_request.activation_scope.request.base_project})
        target = target.model_copy(update={
            "content_hash": canonical_sha256(target.model_dump(mode="json", exclude={"content_hash"})),
        })
    else:
        target = target.model_copy(update={"model_id": "different-model"})
        target = target.model_copy(update={
            "content_hash": canonical_sha256(target.model_dump(mode="json", exclude={"content_hash"})),
        })
    with pytest.raises(ValueError):
        validate_authored_generation_revision_target(old_binding, experience, target)


def _authored_successor_binding(old_binding, experience, target, target_goal, *,
                                retained_evidence=None, paid_submits_used=1):
    from types import SimpleNamespace
    from ai_video.production.video import VideoGenerationMode, VideoGenerationRequest, VideoImageReferenceBinding

    old_candidate = experience.candidate
    baseline = old_binding.compiled_request.activation_scope.request
    candidate_id = f"{old_candidate.capabilities.provider_name}/{target.capability_id}"
    variant = SimpleNamespace(
        capability_id=target.capability_id,
        provider_kind=target.provider_kind,
        model_id=target.model_id,
        mode=target.mode,
    )
    capabilities = SimpleNamespace(
        provider_name=target.provider_name,
        capabilities_fingerprint=target.capabilities_fingerprint,
        variants=(variant,),
    )
    selected = SimpleNamespace(
        candidate_id=candidate_id,
        capabilities=capabilities,
        capability_id=target.capability_id,
        provider_profile=target.provider_profile,
        compiler_contract=target.compiler_contract,
        output_requirement=target.output_requirement,
        final_output_goal=target_goal,
        recipe=SimpleNamespace(acceptance_policy=target.acceptance),
    )
    target_request_values = baseline.model_dump(
        mode="python", exclude={"request_input_hash"}
    )
    target_request_values.update({
        "prompt_text": baseline.prompt_text + " Keep the immediate reaction in frame.",
        "mode": target.mode,
        "adapter_compiler_id": target.compiler_contract.compiler_id,
        "adapter_compiler_version": target.compiler_contract.compiler_version,
        "adapter_compiler_hash": target.compiler_contract.compiler_hash,
        "execution_stack_hash": target.execution_stack_hash,
        "image_bindings": (VideoImageReferenceBinding(
            role="first_frame", asset_id="authored-target-first-frame",
            asset_sha256=target.first_frame_sha256, mime_type="image/png",
            width=1920, height=1080, size_bytes=600_000,
        ),),
        "media_bindings": (),
        "output_requirement": target.output_requirement,
        "base_project": target.target_project,
        "input_artifact_ids": tuple(sorted(set((
            *baseline.input_artifact_ids,
            "authored-target-first-frame",
        )))),
    })
    current_request = VideoGenerationRequest.create(**target_request_values)
    resolved = SimpleNamespace(
        activation_scope=SimpleNamespace(request=current_request),
        effective_output=target.output_requirement,
        provider_name=target.provider_name,
        provider_kind=target.provider_kind,
        model_id=target.model_id,
        provider_profile=target.provider_profile,
        capability_id=target.capability_id,
        execution_stack_hash=target.execution_stack_hash,
        mode=target.mode,
        adapter_compiler_id=target.compiler_contract.compiler_id,
        adapter_compiler_version=target.compiler_contract.compiler_version,
        adapter_compiler_hash=target.compiler_contract.compiler_hash,
    )
    evidence = experience.evidence[-1]
    retained_evidence = tuple(retained_evidence or (evidence,))
    limits = old_binding.inputs.limits.model_copy(update={
        "paid_submits_used": paid_submits_used,
        "paid_submit_ceiling": paid_submits_used + 1,
        "allowed_remote_candidates": (candidate_id,),
    })
    inputs = old_binding.inputs.model_copy(update={
        "limits": limits,
        "policy": old_binding.inputs.policy.model_copy(update={"max_resamples": 0}),
        "candidates": (selected,),
        "evidence": retained_evidence,
        "latest_attempt_hash": retained_evidence[-1].evidence_hash,
        "experiences": (experience,),
        "baseline_request": baseline,
    })
    return SimpleNamespace(
        policy=SimpleNamespace(execution_purpose="qualification", remote_authorized=True, budget_authorized=True),
        inputs=inputs,
        projection=SimpleNamespace(requirement=SimpleNamespace(generation_intent=target.intent)),
        context=old_binding.context,
        decision=SimpleNamespace(selected_candidate_id=candidate_id, runtime_repair=None, intervention=None),
        compiled_request=resolved,
        binding_hash="target-test-binding-hash",
    )


def test_authored_revision_requires_source_closure_active_project_and_exact_binding_under_real_lock(tmp_path):
    from dataclasses import replace
    from ai_video.errors import AiVideoError
    from ai_video.production._qualification_authoring_revision import (
        allows_authored_generation_revision,
        require_authored_generation_revision_predecessor,
    )
    from ai_video.production.project import load_production_project
    from ai_video.production.state_commit import (
        prepare_dependency_graph_transition,
        prepare_project_registry_commit,
    )
    from ai_video.production.dependency import desired_fingerprints
    from ai_video.production.models import ActorIdentity
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="PASS")
    old_binding = writer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    initial = writer._read_manifest()
    loaded = load_production_project(tmp_path / "project.yaml")
    next_project = seal_artifact(loaded.project.model_copy(update={
        "revision": loaded.project.revision + 1,
        "content_hash": "0" * 64,
        "creation_receipt_id": "authored-revision-test-project",
    }))
    def prepare_target_project_commit(manifest):
        base = prepare_project_registry_commit(
            manifest=manifest,
            project=next_project,
            registry=loaded.registry,
            attempt_id="authored-revision-test-project-commit",
        )
        graph = writer._reopen_dependency_graph(manifest.active_dependency_graph)
        transition = prepare_dependency_graph_transition(
            expected_manifest_revision=manifest.manifest_revision,
            base_dependency_graph=manifest.active_dependency_graph,
            candidate_graph=graph,
            candidate_dependency_states=manifest.dependency_states,
            expected_desired_fingerprints=desired_fingerprints(graph),
        )
        return replace(base, dependency_graph_transition=transition)

    prospective_commit = prepare_target_project_commit(initial)
    target = _authored_revision_target(
        old_binding, experience, target_project=prospective_commit.next_project
    )
    goal = _goal("2-authored")
    prospective = _authored_successor_binding(old_binding, experience, target, goal)
    selected = prospective.inputs.candidates[0]
    assert allows_authored_generation_revision(prospective, selected)

    with writer._exclusive_lock(), pytest.raises(AiVideoError):
        require_authored_generation_revision_predecessor(writer, initial, prospective, loaded=loaded)
    closed = writer.supersede_video_generation(
        attempt_id=prior.attempt_id,
        expected_manifest_revision=initial.manifest_revision,
        experience_content_hash=prior.video_generation_state.generation_experiences[-1].content_hash,
        actor=ActorIdentity(actor_id="authored-revision-test", actor_kind="codex"),
        authorization_receipt_id="user-authored-revision-test",
        reason="Explicitly authorized exact performance and output revision.",
        target_goal=goal,
        target_first_frame_sha256=target.first_frame_sha256,
        authored_revision=target,
    )
    uncommitted_project = load_production_project(tmp_path / "project.yaml")
    with writer._exclusive_lock(), pytest.raises(AiVideoError, match="not been committed"):
        require_authored_generation_revision_predecessor(
            writer, closed, prospective, loaded=uncommitted_project
        )

    commit = prepare_target_project_commit(closed)
    committed = writer.commit(commit)
    current = load_production_project(tmp_path / "project.yaml")
    with writer._exclusive_lock():
        require_authored_generation_revision_predecessor(
            writer, committed, prospective, loaded=current
        )
        repeated_inputs = prospective.inputs.model_copy(update={
            "evidence": (*prospective.inputs.evidence, prospective.inputs.evidence[0]),
        })
        repeated = SimpleNamespace(**{**vars(prospective), "inputs": repeated_inputs})
        require_authored_generation_revision_predecessor(
            writer, committed, repeated, loaded=current
        )

    source_evidence = experience.evidence[-1]
    extra_evidence = source_evidence.model_copy(update={
        "attempt_id": "retained-but-not-durable-prior",
        "request_hash": "a" * 64,
    })
    retained_history = (extra_evidence, source_evidence)
    retained_experience = experience.model_copy(update={"evidence": retained_history})
    two_submit_binding = _authored_successor_binding(
        old_binding,
        retained_experience,
        target,
        goal,
        retained_evidence=retained_history,
        paid_submits_used=2,
    )
    assert allows_authored_generation_revision(
        two_submit_binding, two_submit_binding.inputs.candidates[0]
    )
    with writer._exclusive_lock(), pytest.raises(
        AiVideoError, match="differs from all retained submitted evidence"
    ):
        require_authored_generation_revision_predecessor(
            writer, committed, two_submit_binding, loaded=current
        )

    source_attempts = tuple(
        attempt.model_copy(update={
            "video_generation_state": attempt.video_generation_state.model_copy(
                update={"execution_binding": None}
            )
        })
        if attempt.attempt_id == prior.attempt_id and attempt.video_generation_state is not None
        else attempt
        for attempt in committed.attempts
    )
    unbound_source = committed.model_copy(update={"attempts": source_attempts})
    with writer._exclusive_lock(), pytest.raises(
        AiVideoError, match="without an exact execution binding"
    ):
        require_authored_generation_revision_predecessor(
            writer,
            unbound_source,
            prospective,
            loaded=current.model_copy(update={"manifest": unbound_source}),
        )

    unknown = experience.evidence[-1].model_copy(update={
        "outcome": "unknown_outcome", "artifact_sha256": None, "findings": (),
    })
    bad_history = prospective.inputs.model_copy(update={
        "evidence": (unknown,), "latest_attempt_hash": unknown.evidence_hash,
    })
    with writer._exclusive_lock(), pytest.raises(AiVideoError, match="redirected"):
        require_authored_generation_revision_predecessor(
            writer, committed, SimpleNamespace(**{**vars(prospective), "inputs": bad_history}),
            loaded=current,
        )
    reused = experience.evidence[-1].model_copy(update={
        "attempt_id": "reused-old-paid-attempt", "request_hash": "a" * 64,
    })
    bad_history = prospective.inputs.model_copy(update={
        "evidence": (*prospective.inputs.evidence, reused),
    })
    with writer._exclusive_lock(), pytest.raises(AiVideoError, match="redirected"):
        require_authored_generation_revision_predecessor(
            writer, committed, SimpleNamespace(**{**vars(prospective), "inputs": bad_history}),
            loaded=current,
        )

    candidate = prospective.inputs.candidates[0]
    mismatched_variant = SimpleNamespace(**{
        **vars(candidate.capabilities.variants[0]), "model_id": "different-model",
    })
    mismatched_capabilities = SimpleNamespace(**{
        **vars(candidate.capabilities), "variants": (mismatched_variant,),
    })
    wrong_model_candidate = SimpleNamespace(**{
        **vars(candidate), "capabilities": mismatched_capabilities,
    })
    wrong_model_inputs = prospective.inputs.model_copy(update={
        "candidates": (wrong_model_candidate,),
    })
    wrong_model_decision = SimpleNamespace(**{
        **vars(prospective.decision), "selected_candidate_id": wrong_model_candidate.candidate_id,
    })
    wrong_model_binding = SimpleNamespace(**{
        **vars(prospective), "inputs": wrong_model_inputs, "decision": wrong_model_decision,
    })
    with writer._exclusive_lock(), pytest.raises(AiVideoError, match="redirected"):
        require_authored_generation_revision_predecessor(
            writer, committed, wrong_model_binding, loaded=current
        )

    wrong = _authored_successor_binding(old_binding, experience, target, goal)
    wrong_request = wrong.compiled_request.activation_scope.request
    wrong_frame = wrong_request.image_bindings[0].model_copy(update={"asset_sha256": "a" * 64})
    from ai_video.production.video import VideoGenerationRequest
    values = wrong_request.model_dump(mode="python", exclude={"request_input_hash"})
    values["image_bindings"] = (wrong_frame,)
    wrong_request = VideoGenerationRequest.create(**values)
    wrong.compiled_request.activation_scope.request = wrong_request
    with writer._exclusive_lock(), pytest.raises(AiVideoError, match="differs from its sealed target"):
        require_authored_generation_revision_predecessor(
            writer, committed, wrong, loaded=current
        )


@pytest.mark.parametrize("history_change", ["unknown", "reused_paid_history", "submit_ceiling"])
def test_authored_revision_admission_rejects_unknown_or_reused_history(tmp_path, history_change):
    from types import SimpleNamespace
    from ai_video.production._qualification_authoring_revision import allows_authored_generation_revision
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="PASS")
    old_binding = writer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    target = _authored_revision_target(old_binding, experience)
    prospective = _authored_successor_binding(old_binding, experience, target, _goal("2-authored"))
    selected = prospective.inputs.candidates[0]
    assert allows_authored_generation_revision(prospective, selected)
    inputs = prospective.inputs
    if history_change == "unknown":
        unknown = experience.evidence[-1].model_copy(update={
            "outcome": "unknown_outcome", "artifact_sha256": None, "findings": (),
        })
        bad_inputs = inputs.model_copy(update={
            "evidence": (unknown,), "latest_attempt_hash": unknown.evidence_hash,
        })
    elif history_change == "reused_paid_history":
        reused = experience.evidence[-1].model_copy(update={
            "attempt_id": "reused-old-paid-attempt", "request_hash": "a" * 64,
        })
        bad_inputs = inputs.model_copy(update={"evidence": (*inputs.evidence, reused)})
    else:
        bad_inputs = inputs.model_copy(update={
            "limits": inputs.limits.model_copy(update={
                "paid_submits_used": 2, "paid_submit_ceiling": 3,
            }),
        })
    changed = SimpleNamespace(**{**vars(prospective), "inputs": bad_inputs})
    assert not allows_authored_generation_revision(changed, selected)


def test_authored_revision_admits_three_reference_to_first_frame_mode_and_compiler_change(tmp_path):
    from types import SimpleNamespace
    from ai_video.production._qualification_authoring_revision import allows_authored_generation_revision
    from ai_video.production.generation_diagnosis import compare_compiled_requests
    from ai_video.production.video import VideoGenerationMode, VideoGenerationRequest, VideoImageReferenceBinding
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="PASS")
    old_binding = writer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    original = old_binding.compiled_request.activation_scope.request
    old_values = original.model_dump(mode="python", exclude={"request_input_hash"})
    old_values["mode"] = VideoGenerationMode.REFERENCE_TO_VIDEO
    old_values["image_bindings"] = tuple(VideoImageReferenceBinding(
        role="reference", asset_id=f"multimodal-reference-{index}",
        asset_sha256=f"{index + 1:x}" * 64, mime_type="image/png",
        width=1920, height=1080,
    ) for index in range(3))
    old_values["input_artifact_ids"] = tuple(sorted({
        *original.input_artifact_ids,
        "multimodal-reference-0", "multimodal-reference-1", "multimodal-reference-2",
    }))
    three_reference_request = VideoGenerationRequest.create(**old_values)
    prior_evidence = experience.evidence[-1].model_copy(update={
        "request_hash": three_reference_request.request_input_hash,
    })
    prior_experience = SimpleNamespace(
        candidate=experience.candidate,
        evidence=(prior_evidence,),
        projection=experience.projection,
    )
    inputs = old_binding.inputs.model_copy(update={
        "limits": old_binding.inputs.limits.model_copy(update={
            "paid_submits_used": 1, "paid_submit_ceiling": 2,
        }),
        "evidence": (prior_evidence,),
        "latest_attempt_hash": prior_evidence.evidence_hash,
        "experiences": (prior_experience,),
        "baseline_request": three_reference_request,
    })
    source = SimpleNamespace(
        inputs=inputs,
        decision=old_binding.decision,
        context=old_binding.context,
        projection=old_binding.projection,
        compiled_request=SimpleNamespace(
            activation_scope=SimpleNamespace(request=three_reference_request),
        ),
    )
    target = _authored_revision_target(source, prior_experience)
    prospective = _authored_successor_binding(source, prior_experience, target, _goal("2-authored"))
    selected = prospective.inputs.candidates[0]
    delta = set(compare_compiled_requests(
        three_reference_request, prospective.compiled_request.activation_scope.request,
    )["changed_variables"])
    assert {"image_bindings", "mode", "output_requirement", "adapter_compiler_id"} <= delta
    assert allows_authored_generation_revision(prospective, selected)


def test_authored_goal_requirement_revisions_are_exact_and_explicit():
    from ai_video.production.final_output_contracts import FinalOutputContract, FinalOutputRequirement
    from ai_video.production.generation_authoring_revision import (
        AuthoredGoalRequirementRevision,
        validate_authored_revision_goal,
    )

    old_requirements = tuple(FinalOutputRequirement(
        requirement_id=f"goal-rule-{index}",
        observable=f"Original observable {index}.",
        proof="human" if index % 2 else "evaluator",
    ) for index in range(5))
    old = FinalOutputContract(
        goal_id="same-goal",
        goal_version="1",
        user_goal="Preserve the complete approved scene.",
        requirements=old_requirements,
    )
    changed = tuple(item.model_copy(update={
        "observable": f"Explicitly revised observable {index}."
    }) for index, item in enumerate(old_requirements))
    appended = FinalOutputRequirement(
        requirement_id="new-additional-rule",
        observable="The scene remains legible throughout.",
        proof="human",
    )
    target = FinalOutputContract(
        goal_id=old.goal_id,
        goal_version="2",
        user_goal=old.user_goal,
        requirements=(*changed, appended),
    )
    authorization = "user-style-change-01"
    revisions = tuple(AuthoredGoalRequirementRevision(
        requirement_id=old_item.requirement_id,
        old_requirement=old_item,
        new_requirement=new_item,
        authorization_reference=authorization,
        reason="The user changed the desired image-making style.",
    ) for old_item, new_item in zip(old_requirements, changed))

    with pytest.raises(ValueError):
        validate_authored_revision_goal(old, target)
    validate_authored_revision_goal(
        old,
        target,
        goal_requirement_revisions=revisions,
        authorization_receipt_id=authorization,
    )

    mismatch = revisions[0].model_copy(update={
        "old_requirement": old_requirements[1],
    })
    with pytest.raises(ValueError):
        validate_authored_revision_goal(
            old,
            target,
            goal_requirement_revisions=(mismatch, *revisions[1:]),
            authorization_receipt_id=authorization,
        )
    proof_changed = changed[0].model_copy(update={"proof": "human"})
    proof_target = target.model_copy(update={"requirements": (proof_changed, *changed[1:], appended)})
    proof_revision = revisions[0].model_copy(update={"new_requirement": proof_changed})
    with pytest.raises(ValueError):
        validate_authored_revision_goal(
            old,
            proof_target,
            goal_requirement_revisions=(proof_revision, *revisions[1:]),
            authorization_receipt_id=authorization,
        )
    with pytest.raises(ValueError):
        validate_authored_revision_goal(
            old,
            target,
            goal_requirement_revisions=revisions,
            authorization_receipt_id="different-authorization",
        )


def test_authored_goal_user_text_can_follow_an_explicit_revision_without_weakening_requirements():
    from ai_video.production.final_output_contracts import FinalOutputContract, FinalOutputRequirement
    from ai_video.production.generation_authoring_revision import validate_authored_revision_goal, validate_prospective_authored_goal

    old = FinalOutputContract(goal_id="same-scene", goal_version="1", user_goal="Original complete scene", requirements=(FinalOutputRequirement(requirement_id="story", observable="Preserve the complete story", proof="human"),))
    new = old.model_copy(update={"goal_version": "2", "user_goal": "Original complete scene plus the latest explicit user revision"})
    validate_authored_revision_goal(old, new)
    validate_prospective_authored_goal(old, new)
    changed = new.model_copy(update={"requirements": (old.requirements[0].model_copy(update={"observable": "Silently discard the story"}),)})
    with pytest.raises(ValueError):
        validate_authored_revision_goal(old, changed)


def test_empty_authored_goal_revisions_preserve_legacy_target_hash_bytes(tmp_path):
    writer, prior, experience = __import__(
        "test_generation_visual_revision", fromlist=["_ready_fixture"]
    )._ready_fixture(tmp_path, evaluation_verdict="PASS")
    old_binding = writer._reopen_generation_execution_binding(
        prior.video_generation_state.execution_binding
    )
    target = _authored_revision_target(old_binding, experience)
    legacy_payload = target.model_dump(mode="json")
    assert "goal_requirement_revisions" not in legacy_payload
    from ai_video.production.generation_authoring_revision import AuthoredGenerationRevisionTarget

    reopened = AuthoredGenerationRevisionTarget.model_validate(legacy_payload)
    assert reopened.content_hash == target.content_hash
    assert reopened.model_dump_json() == target.model_dump_json()


def test_authored_revision_admits_exact_prior_paid_count_and_next_ceiling(tmp_path):
    from ai_video.production._qualification_authoring_revision import allows_authored_generation_revision
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="PASS")
    old_binding = writer._reopen_generation_execution_binding(
        prior.video_generation_state.execution_binding
    )
    source = experience.evidence[-1]
    used = 5
    retained = tuple(
        source.model_copy(update={
            "attempt_id": f"retained-prior-{index}",
            "request_hash": f"{index + 1:064x}",
        })
        for index in range(used - 1)
    ) + (source,)
    retained_experience = experience.model_copy(update={"evidence": retained})
    target = _authored_revision_target(old_binding, retained_experience)
    prospective = _authored_successor_binding(
        old_binding,
        retained_experience,
        target,
        _goal("2-authored"),
        retained_evidence=retained,
        paid_submits_used=used,
    )
    selected = prospective.inputs.candidates[0]
    assert allows_authored_generation_revision(prospective, selected)
    repeated = _authored_successor_binding(
        old_binding, retained_experience, target, _goal("2-authored"),
        retained_evidence=(*retained, retained[0], source), paid_submits_used=used,
    )
    assert allows_authored_generation_revision(repeated, repeated.inputs.candidates[0])
    for conflicting in (
        retained[0].model_copy(update={"shot_id": "different-shot"}),
        retained[0].model_copy(update={"request_hash": "f" * 64}),
    ):
        wrong = _authored_successor_binding(
            old_binding, retained_experience, target, _goal("2-authored"),
            retained_evidence=(*retained, conflicting), paid_submits_used=used,
        )
        assert not allows_authored_generation_revision(wrong, wrong.inputs.candidates[0])

    for invalid_evidence, ceiling in ((retained[:-1], used + 1), (retained, used + 2)):
        invalid = _authored_successor_binding(
            old_binding,
            retained_experience,
            target,
            _goal("2-authored"),
            retained_evidence=invalid_evidence,
            paid_submits_used=used,
        )
        invalid_inputs = invalid.inputs.model_copy(update={
            "limits": invalid.inputs.limits.model_copy(update={
            "paid_submit_ceiling": ceiling,
            }),
        })
        assert not allows_authored_generation_revision(
            SimpleNamespace(**{**vars(invalid), "inputs": invalid_inputs}), selected
        )


def test_authored_revision_retains_first_frame_for_terminal_anatomy_repair(tmp_path):
    """An explicit framing repair must not require changing a good identity anchor."""
    from ai_video.production._qualification_authoring_revision import allows_authored_generation_revision
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="PASS")
    old_binding = writer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    target = _authored_revision_target(old_binding, experience)
    prospective = _authored_successor_binding(old_binding, experience, target, _goal("2-anatomy"))
    request = prospective.compiled_request.activation_scope.request
    baseline = prospective.inputs.baseline_request
    from ai_video.production.video import VideoGenerationRequest

    def rebase(updates):
        values = baseline.model_dump(mode="python", exclude={"request_input_hash"})
        values.update(updates)
        revised = VideoGenerationRequest.create(**values)
        source = experience.evidence[-1].model_copy(update={"request_hash": revised.request_input_hash})
        retained = experience.model_copy(update={"evidence": (source,)})
        prospective.inputs = prospective.inputs.model_copy(update={
            "baseline_request": revised, "evidence": (source,),
            "latest_attempt_hash": source.evidence_hash, "experiences": (retained,),
        })

    # Same image binding in both requests, changed authored performance text.
    rebase({"image_bindings": request.image_bindings})
    assert allows_authored_generation_revision(prospective, prospective.inputs.candidates[0])
    # A profile/project bookkeeping change alone cannot buy an unexplained retry.
    rebase({
        "image_bindings": request.image_bindings, "prompt_text": request.prompt_text,
        "mode": request.mode, "output_requirement": request.output_requirement,
        "adapter_compiler_id": request.adapter_compiler_id,
        "adapter_compiler_version": request.adapter_compiler_version,
        "adapter_compiler_hash": request.adapter_compiler_hash,
    })
    assert not allows_authored_generation_revision(prospective, prospective.inputs.candidates[0])


def test_authored_timing_correction_preserves_source_and_rejects_creative_changes(tmp_path):
    from ai_video.production.generation_authoring_revision import AuthoredGenerationRevisionTarget
    from ai_video.production.generation_visual_revision import (
        GenerationVisualSupersessionReceipt, load_generation_visual_supersession,
        validate_authored_timing_correction,
    )
    from ai_video.production.models import ActorIdentity
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="PASS")
    binding = writer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    target = _authored_revision_target(binding, experience)
    values = {name:getattr(target, name) for name in type(target).model_fields if name != "content_hash"}
    values["intent"] = target.intent.model_copy(update={"pacing":target.intent.pacing.model_copy(update={"shot_duration_seconds":8})})
    target = AuthoredGenerationRevisionTarget.create(**values)
    before = writer._read_manifest()
    closed = writer.supersede_video_generation(
        attempt_id=prior.attempt_id, expected_manifest_revision=before.manifest_revision,
        experience_content_hash=prior.video_generation_state.generation_experiences[-1].content_hash,
        actor=ActorIdentity(actor_id="test", actor_kind="codex"), authorization_receipt_id="test-user",
        reason="Explicit authored target", target_goal=_goal("2-timing"),
        target_first_frame_sha256=target.first_frame_sha256, authored_revision=target,
    )
    source = next(a for a in closed.attempts if a.attempt_id == prior.attempt_id)
    pointer = source.video_generation_state.visual_supersession
    previous = load_generation_visual_supersession(tmp_path, pointer)
    assert "previous_supersession" not in previous.model_dump(mode="json")
    seconds = target.intent.pacing.shot_duration_seconds
    assert seconds is not None and seconds != target.output_requirement.duration_seconds
    values = {name:getattr(target, name) for name in type(target).model_fields if name != "content_hash"}
    values["output_requirement"] = target.output_requirement.model_copy(update={"duration_seconds":int(seconds)})
    corrected_target = AuthoredGenerationRevisionTarget.create(**values)
    values = {name:getattr(previous, name) for name in type(previous).model_fields if name != "content_hash"}
    values.update(authored_revision=corrected_target, previous_supersession=pointer,
                  reason="Correct output to unchanged intent", expected_manifest_revision=closed.manifest_revision)
    corrected = GenerationVisualSupersessionReceipt.create(**values)
    validate_authored_timing_correction(previous, corrected)
    for changed in (
        corrected.model_copy(update={"authorization_receipt_id":"another-user"}),
        corrected.model_copy(update={"authored_revision":corrected_target.model_copy(update={"first_frame_sha256":"a"*64})}),
        corrected.model_copy(update={"authored_revision":target}),
        corrected.model_copy(update={"previous_supersession":None}),
    ):
        with pytest.raises(ValueError):
            validate_authored_timing_correction(previous, changed)


def test_authored_first_frame_successor_can_drop_old_multimodal_audio(tmp_path):
    from ai_video.production._qualification_authoring_revision import allows_authored_generation_revision
    from ai_video.production.video import VideoGenerationRequest, VideoMediaReferenceBinding, VideoGenerationMode
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="PASS")
    binding = writer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    target = _authored_revision_target(binding, experience)
    prospective = _authored_successor_binding(binding, experience, target, _goal("2-drop-audio"))
    baseline = prospective.inputs.baseline_request
    audio = VideoMediaReferenceBinding(kind="audio", role="reference_audio", asset_id="old-voice",
        asset_sha256="a" * 64, mime_type="audio/wav", duration_millis=1000, size_bytes=96044)
    values = baseline.model_dump(mode="python", exclude={"request_input_hash"})
    values["media_bindings"] = (audio,)
    values["mode"] = VideoGenerationMode.REFERENCE_TO_VIDEO
    old = VideoGenerationRequest.create(**values)
    source = experience.evidence[-1].model_copy(update={"request_hash":old.request_input_hash})
    retained = experience.model_copy(update={"evidence":(source,)})
    prospective.inputs = prospective.inputs.model_copy(update={"baseline_request":old,
        "evidence":(source,), "latest_attempt_hash":source.evidence_hash, "experiences":(retained,)})
    assert allows_authored_generation_revision(prospective, prospective.inputs.candidates[0])
    request = prospective.compiled_request.activation_scope.request
    prospective.compiled_request.activation_scope.request = request.model_copy(update={"media_bindings":(audio,)})
    assert not allows_authored_generation_revision(prospective, prospective.inputs.candidates[0])
