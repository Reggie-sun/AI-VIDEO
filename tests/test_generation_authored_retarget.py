"""Narrow /5 authored model and multimodal retarget contracts."""

from types import SimpleNamespace

import pytest


def _retarget_target(old_binding, experience, *, image_bindings=None, media_bindings=(), **changes):
    from ai_video.production.generation_authored_retarget import AuthoredGenerationRetargetTarget
    from ai_video.production.hashing import canonical_sha256
    from ai_video.production.models import ProjectSnapshotPointer, canonical_project_snapshot_path
    from ai_video.production._shot_router_contracts import AdapterCompilerContract
    from ai_video.production.video import VideoGenerationMode
    from ai_video.production.video_contracts import (
        VideoFlexibleOutputRequirement,
        VideoMediaReferenceBinding,
    )

    prior = old_binding.compiled_request.activation_scope.request
    candidate = experience.candidate
    variant = next(item for item in candidate.capabilities.variants
                   if item.capability_id == candidate.capability_id)
    source_intent = experience.projection.requirement.generation_intent
    target_intent = source_intent.model_copy(update={
        "pacing": source_intent.pacing.model_copy(update={
            "cadence": "A natural, brisk scan; bottle settles before the disappearance; immediate reaction.",
        }),
    })
    refs = image_bindings
    if refs is None:
        from ai_video.production.video import VideoImageReferenceBinding

        refs = (
            VideoImageReferenceBinding(
                role="reference", asset_id="s03-reference-01", asset_sha256="1" * 64,
                mime_type="image/png", width=1920, height=1080, size_bytes=100_000,
            ),
            VideoImageReferenceBinding(
                role="reference", asset_id="s03-reference-02", asset_sha256="2" * 64,
                mime_type="image/png", width=1920, height=1080, size_bytes=120_000,
            ),
        )
    if not media_bindings:
        media_bindings = (
            VideoMediaReferenceBinding(
                kind="audio", role="reference_audio", asset_id="s03-reference-audio",
                asset_sha256="3" * 64, mime_type="audio/mpeg", duration_millis=1000,
                size_bytes=32_000,
            ),
        )
    revision = prior.base_project.revision + 1
    values = {
        "task_id": old_binding.inputs.limits.task_id,
        "shot_id": old_binding.context.target_shot_id,
        "intent": target_intent,
        "acceptance": candidate.recipe.acceptance_policy,
        "output_requirement": VideoFlexibleOutputRequirement(
            timing_mode="exact_seconds", duration_seconds=15,
            dimension_mode="exact", width=1920, height=1080,
            resolution_label="1080p", ratio="16:9", fps=24,
            container="mp4", mime_type="video/mp4", native_audio=True,
        ),
        "provider_name": candidate.capabilities.provider_name,
        "provider_kind": variant.provider_kind,
        "model_id": "seedance_2.0_vip",
        "provider_profile": candidate.provider_profile,
        "capability_id": "seedance-2-0-vip-reference-to-video",
        "capabilities_fingerprint": "c" * 64,
        "compiler_contract": AdapterCompilerContract.create(
            compiler_id="jimeng-seedance-2-0-multimodal-video-compiler", compiler_version="1",
        ),
        "execution_stack_hash": prior.execution_stack_hash,
        "mode": VideoGenerationMode.REFERENCE_TO_VIDEO,
        "target_project": ProjectSnapshotPointer(
            path=canonical_project_snapshot_path(revision, "d" * 64), revision=revision,
            content_hash="d" * 64, file_sha256="e" * 64,
        ),
        "image_bindings": refs,
        "media_bindings": media_bindings,
        "authorization_reference": "user-authorized-seedance-2-0-s03-retarget",
        "rationale": "User explicitly authorized the exact Seedance 2.0 multimodal S03 retarget.",
    }
    values.update(changes)
    return AuthoredGenerationRetargetTarget.create(**values)


def _retarget_binding(old_binding, experience, target, *, request_changes=None,
                     paid_submits_used=1, paid_submit_ceiling=2, unknown=False):
    from ai_video.production.video import VideoGenerationRequest

    candidate = experience.candidate
    target_goal = candidate.final_output_goal.model_copy(update={
        "goal_version": f"{candidate.final_output_goal.goal_version}-seedance-2-retarget",
    })
    media_capability = SimpleNamespace(
        kind="audio", supports=lambda bindings: all(item.kind == "audio" for item in bindings),
    )
    prior = old_binding.compiled_request.activation_scope.request
    capability_id = target.capability_id
    variant = SimpleNamespace(
        capability_id=capability_id, provider_kind=target.provider_kind,
        model_id=target.model_id, mode=target.mode,
        execution_kind=next(item for item in candidate.capabilities.variants
                            if item.capability_id == candidate.capability_id).execution_kind,
        billing_kind=next(item for item in candidate.capabilities.variants
                          if item.capability_id == candidate.capability_id).billing_kind,
        production_qualification=next(item for item in candidate.capabilities.variants
                                      if item.capability_id == candidate.capability_id).production_qualification,
        output_capability=SimpleNamespace(supports=lambda output: (
            output.duration_seconds is None or output.duration_seconds <= 15
        )),
        allowed_image_roles=("reference",), max_reference_count=12,
        media_capabilities=(media_capability,),
    )
    capabilities = SimpleNamespace(
        provider_name=target.provider_name, capabilities_fingerprint=target.capabilities_fingerprint,
        variants=(variant,),
    )
    selected = SimpleNamespace(
        candidate_id=f"{target.provider_name}/{capability_id}", capabilities=capabilities,
        capability_id=capability_id, provider_profile=target.provider_profile,
        compiler_contract=target.compiler_contract, output_requirement=target.output_requirement,
        final_output_goal=target_goal,
        recipe=SimpleNamespace(acceptance_policy=target.acceptance),
    )
    values = prior.model_dump(mode="python", exclude={"request_input_hash"})
    values.update({
        "model_id": target.model_id, "mode": target.mode,
        "adapter_compiler_id": target.compiler_contract.compiler_id,
        "adapter_compiler_version": target.compiler_contract.compiler_version,
        "adapter_compiler_hash": target.compiler_contract.compiler_hash,
        "execution_stack_hash": target.execution_stack_hash,
        "image_bindings": target.image_bindings, "media_bindings": target.media_bindings,
        "output_requirement": target.output_requirement, "base_project": target.target_project,
        "input_artifact_ids": tuple(sorted(set((
            *prior.input_artifact_ids,
            *(item.asset_id for item in target.image_bindings),
            *(item.asset_id for item in target.media_bindings),
        )))),
    })
    values.update(request_changes or {})
    request = VideoGenerationRequest.create(**values)
    resolved = SimpleNamespace(
        activation_scope=SimpleNamespace(request=request), effective_output=target.output_requirement,
        provider_name=target.provider_name, provider_kind=target.provider_kind,
        model_id=target.model_id, provider_profile=target.provider_profile,
        capability_id=target.capability_id, execution_stack_hash=target.execution_stack_hash,
        mode=target.mode, adapter_compiler_id=target.compiler_contract.compiler_id,
        adapter_compiler_version=target.compiler_contract.compiler_version,
        adapter_compiler_hash=target.compiler_contract.compiler_hash,
    )
    evidence = experience.evidence[-1]
    if unknown:
        evidence = evidence.model_copy(update={
            "attempt_id": "unknown-before-retarget", "outcome": "unknown_outcome",
            "artifact_sha256": None, "findings": (),
        })
    limits = old_binding.inputs.limits.model_copy(update={
        "paid_submits_used": paid_submits_used,
        "paid_submit_ceiling": paid_submit_ceiling,
        "allowed_remote_candidates": (selected.candidate_id,),
    })
    inputs = old_binding.inputs.model_copy(update={
        "limits": limits, "policy": old_binding.inputs.policy.model_copy(update={"max_resamples": 0}),
        "candidates": (selected,), "evidence": (evidence,),
        "latest_attempt_hash": evidence.evidence_hash, "experiences": (experience,),
        "baseline_request": prior,
    })
    return SimpleNamespace(
        policy=SimpleNamespace(execution_purpose="qualification", remote_authorized=True,
                               budget_authorized=True),
        inputs=inputs,
        projection=SimpleNamespace(requirement=SimpleNamespace(generation_intent=target.intent)),
        context=old_binding.context,
        decision=SimpleNamespace(selected_candidate_id=selected.candidate_id,
                                 runtime_repair=None, intervention=None),
        compiled_request=resolved, binding_hash="retarget-test-binding",
    ), selected


def _changed_acceptance(policy, *, changes=None):
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.hashing import canonical_sha256

    data = policy.model_dump(mode="json")
    payload = data["profile_payload"]
    payload.pop("content_hash")
    payload["profile_version"] = f"{policy.profile_version}-tampered"
    rules = [dict(item) for item in payload["generation_requirements"]]
    updates = changes or {rules[0]["requirement_id"]: {
        "observable": "Changed QA observable that was never authorized.",
    }}
    for rule in rules:
        for field, value in updates.get(rule["requirement_id"], {}).items():
            rule[field] = value
    payload["generation_requirements"] = rules
    digest = canonical_sha256(payload)
    payload["content_hash"] = digest
    data.update(profile_version=payload["profile_version"], profile_content_hash=digest,
                profile_payload=payload)
    return DomainAcceptancePolicy.model_validate(data)


def test_retarget_target_seals_exact_model_mode_and_full_image_media_references(tmp_path):
    from ai_video.production.generation_authored_retarget import (
        validate_authored_generation_retarget_target,
    )
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="FAIL")
    old_binding = writer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    target = _retarget_target(old_binding, experience)
    validate_authored_generation_retarget_target(old_binding, experience, target)
    assert target.schema_version == "authored-generation-retarget/1"
    assert target.model_id == "seedance_2.0_vip"
    assert target.mode.value == "reference_to_video"
    assert len(target.image_bindings) == 2
    assert len(target.media_bindings) == 1
    assert target.verify().content_hash == target.content_hash
    serialized = target.model_dump(mode="json")
    assert "revised_requirement_ids" not in serialized
    assert "additional_image_reference_ids" not in serialized
    prospective, selected = _retarget_binding(old_binding, experience, target)
    from ai_video.production.generation_authored_retarget import (
        validate_authored_generation_retarget_binding,
    )
    validate_authored_generation_retarget_binding(
        prospective, selected, target, target_goal=selected.final_output_goal,
        authorization_receipt_id=target.authorization_reference,
    )
    from ai_video.production.models import ActorIdentity
    from ai_video.production._generation_feedback_reader import load_generation_visual_supersession

    closed = writer.supersede_video_generation(
        attempt_id=prior.attempt_id,
        expected_manifest_revision=writer._read_manifest().manifest_revision,
        experience_content_hash=prior.video_generation_state.generation_experiences[-1].content_hash,
        actor=ActorIdentity(actor_id="authored-retarget-test", actor_kind="codex"),
        authorization_receipt_id=target.authorization_reference,
        reason="User explicitly selected the exact Seedance 2.0 multimodal retarget.",
        target_goal=selected.final_output_goal,
        target_first_frame_sha256=None,
        authored_retarget=target,
    )
    source = next(item for item in closed.attempts if item.attempt_id == prior.attempt_id)
    receipt = load_generation_visual_supersession(
        writer.project_root, source.video_generation_state.visual_supersession,
    )
    assert receipt.schema_version == "generation-visual-supersession/5"
    assert receipt.target_first_frame_sha256 is None
    assert receipt.authored_retarget == target
    assert receipt.target_goal == selected.final_output_goal


def test_retarget_source_accepts_historical_baseline_only_when_latest_fetched_request_matches(tmp_path):
    from ai_video.production.generation_authored_retarget import (
        validate_authored_generation_retarget_target,
    )
    from ai_video.production.video import VideoGenerationRequest
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="FAIL")
    old_binding = writer._reopen_generation_execution_binding(
        prior.video_generation_state.execution_binding,
    )
    current = old_binding.compiled_request.activation_scope.request
    values = current.model_dump(mode="python", exclude={"request_input_hash"})
    values["prompt_text"] += " Earlier attempt baseline."
    historical = VideoGenerationRequest.create(**values)
    assert historical.request_input_hash != current.request_input_hash
    old_binding = old_binding.model_copy(update={
        "inputs": old_binding.inputs.model_copy(update={"baseline_request": historical}),
    })
    target = _retarget_target(old_binding, experience)

    # The current request is tied to the exact fetched FAIL evidence even when
    # this execution binding retains an older attempt as its planning baseline.
    validate_authored_generation_retarget_target(old_binding, experience, target)

    wrong_evidence = experience.evidence[-1].model_copy(update={
        "request_hash": historical.request_input_hash,
    })
    wrong_experience = experience.model_copy(update={
        "evidence": (*experience.evidence[:-1], wrong_evidence),
    })
    with pytest.raises(ValueError, match="exact known fetched Shot evaluation"):
        validate_authored_generation_retarget_target(old_binding, wrong_experience, target)


@pytest.mark.parametrize("change", ["unknown", "target_tamper", "wrong_model", "wrong_mode",
                                     "wrong_reference", "wrong_media", "excessive_duration",
                                     "changed_qa", "wrong_project"])
def test_retarget_owner_boundary_rejects_unsealed_or_mismatched_target(tmp_path, change):
    from ai_video.production.generation_authored_retarget import (
        validate_authored_generation_retarget_binding,
        validate_authored_generation_retarget_target,
    )
    from ai_video.production.video import VideoGenerationMode
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="FAIL")
    old_binding = writer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    target = _retarget_target(old_binding, experience)
    prospective, selected = _retarget_binding(old_binding, experience, target)
    if change == "unknown":
        prospective, selected = _retarget_binding(old_binding, experience, target, unknown=True)
    elif change == "target_tamper":
        target = target.model_copy(update={"model_id": "seedance_2.0_fast_vip"})
    elif change == "wrong_model":
        selected.capabilities.variants = (selected.capabilities.variants[0].__class__(
            **{**vars(selected.capabilities.variants[0]), "model_id": "seedance_2.0_fast_vip"}),)
    elif change == "wrong_mode":
        prospective.compiled_request.activation_scope.request = prospective.compiled_request.activation_scope.request.model_copy(
            update={"mode": VideoGenerationMode.IMAGE_TO_VIDEO})
    elif change == "wrong_reference":
        req = prospective.compiled_request.activation_scope.request
        changed = req.image_bindings[0].model_copy(update={"asset_sha256": "a" * 64})
        prospective.compiled_request.activation_scope.request = req.model_copy(
            update={"image_bindings": (changed, *req.image_bindings[1:])})
    elif change == "wrong_media":
        req = prospective.compiled_request.activation_scope.request
        changed = req.media_bindings[0].model_copy(update={"size_bytes": req.media_bindings[0].size_bytes + 1})
        prospective.compiled_request.activation_scope.request = req.model_copy(
            update={"media_bindings": (changed,)})
    elif change == "excessive_duration":
        target = _retarget_target(old_binding, experience, output_requirement=target.output_requirement.model_copy(
            update={"duration_seconds": 16}))
    elif change == "changed_qa":
        target = _retarget_target(old_binding, experience,
                                  acceptance=_changed_acceptance(experience.candidate.recipe.acceptance_policy))
    elif change == "wrong_project":
        target = _retarget_target(old_binding, experience, target_project=old_binding.compiled_request.activation_scope.request.base_project)
    if change not in {"unknown", "wrong_model", "wrong_mode", "wrong_reference", "wrong_media",
                      "excessive_duration"}:
        with pytest.raises(ValueError):
            validate_authored_generation_retarget_target(old_binding, experience, target)
    with pytest.raises(ValueError):
        validate_authored_generation_retarget_binding(
            prospective, selected, target, target_goal=selected.final_output_goal,
            authorization_receipt_id=target.authorization_reference,
        )


def test_retarget_qualification_admits_only_one_known_exact_next_submit(tmp_path):
    from ai_video.production._qualification_authoring_revision import (
        allows_authored_generation_retarget,
    )
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="FAIL")
    old_binding = writer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    target = _retarget_target(old_binding, experience)
    prospective, selected = _retarget_binding(old_binding, experience, target)
    assert allows_authored_generation_retarget(prospective, selected)
    from ai_video.production._generation_authored_prospect import (
        is_authored_generation_retarget_prospect,
    )
    decision_projection = SimpleNamespace(requirement=SimpleNamespace(
        target_shot=SimpleNamespace(shot_id=prospective.context.target_shot_id),
        generation_intent=target.intent,
    ))
    assert is_authored_generation_retarget_prospect(
        inputs=prospective.inputs, projection=decision_projection,
        policy=prospective.policy, latest=prospective.inputs.evidence[-1],
        prior=experience.candidate,
    )
    for changes in (
        {"paid_submit_ceiling": 3},
        {"paid_submits_used": 2, "paid_submit_ceiling": 3},
    ):
        changed = prospective.inputs.model_copy(update={
            "limits": prospective.inputs.limits.model_copy(update=changes),
        })
        assert not allows_authored_generation_retarget(
            SimpleNamespace(**{**vars(prospective), "inputs": changed}), selected
        )
    unknown, unknown_selected = _retarget_binding(old_binding, experience, target, unknown=True)
    assert not allows_authored_generation_retarget(unknown, unknown_selected)


def _same_model_reference_repair(tmp_path):
    """A pure guard fixture whose baseline already has the complete R2V inputs."""
    from test_generation_visual_revision import _ready_fixture

    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="FAIL")
    original = writer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    initial = _retarget_target(original, experience)
    source, source_selected = _retarget_binding(original, experience, initial)
    source_request = source.compiled_request.activation_scope.request
    candidate = SimpleNamespace(**{
        **vars(source_selected), "scope_hash": experience.candidate.scope_hash,
        "recipe": experience.candidate.recipe,
        "final_output_goal": experience.candidate.final_output_goal,
    })
    evidence = experience.evidence[-1].model_copy(update={
        "request_hash": source_request.request_input_hash,
    })
    retained = SimpleNamespace(projection=experience.projection, candidate=candidate,
                               evidence=(evidence,))
    baseline = SimpleNamespace(compiled_request=source.compiled_request,
        inputs=source.inputs, context=source.context, projection=experience.projection)
    target = _retarget_target(baseline, retained)
    repaired, selected = _retarget_binding(baseline, retained, target,
        request_changes={"prompt_text": source_request.prompt_text + " Urgent restrained speech."})
    # The real capability document is unchanged by a fresh node/profile pointer.
    selected.capabilities = candidate.capabilities
    return baseline, retained, target, repaired, selected


def test_same_model_r2v_repair_preserves_inputs_and_admits_exact_one_next_submit(tmp_path):
    from ai_video.production.generation_authored_retarget import (
        validate_authored_generation_retarget_target,
        validate_authored_generation_retarget_binding,
    )
    from ai_video.production._qualification_authoring_revision import allows_authored_generation_retarget
    from ai_video.production._generation_authored_prospect import is_authored_generation_retarget_prospect

    baseline, retained, target, repaired, selected = _same_model_reference_repair(tmp_path)
    validate_authored_generation_retarget_target(baseline, retained, target)
    validate_authored_generation_retarget_binding(repaired, selected, target,
        target_goal=selected.final_output_goal, authorization_receipt_id=target.authorization_reference)
    assert allows_authored_generation_retarget(repaired, selected)
    projection = SimpleNamespace(requirement=SimpleNamespace(
        target_shot=SimpleNamespace(shot_id=target.shot_id), generation_intent=target.intent))
    assert is_authored_generation_retarget_prospect(inputs=repaired.inputs, projection=projection,
        policy=repaired.policy, latest=repaired.inputs.evidence[-1], prior=retained.candidate)


def test_same_model_repair_seals_explicit_performance_qa_and_additive_closeup_references(tmp_path):
    from ai_video.production.generation_authored_retarget import (
        validate_authored_generation_retarget_target,
        validate_authored_generation_retarget_binding,
    )
    from ai_video.production.video import VideoImageReferenceBinding
    from ai_video.production._qualification_authoring_revision import allows_authored_generation_retarget
    from ai_video.production._generation_authored_prospect import is_authored_generation_retarget_prospect

    baseline, retained, original, _, _ = _same_model_reference_repair(tmp_path)
    # The previously fixed output contract remains unchanged while the raw QA
    # coverage and performance observables gain explicit revisions.
    coverage_and_performance = _changed_acceptance(
        retained.candidate.recipe.acceptance_policy,
        changes={
            "duration": {"observable": "The continuous authored event uses multiple camera shots and one settled bottle state."},
            "performance": {"observable": "Visible anxious face and hurried, restrained speech while checking the impossible absence."},
        },
    )
    closeups = (
        VideoImageReferenceBinding(
            role="reference", asset_id="s03-closeup-face-a", asset_sha256="a" * 64,
            mime_type="image/png", width=1920, height=1080, size_bytes=101_000,
        ),
        VideoImageReferenceBinding(
            role="reference", asset_id="s03-closeup-face-b", asset_sha256="b" * 64,
            mime_type="image/png", width=1920, height=1080, size_bytes=102_000,
        ),
    )
    target = _retarget_target(
        baseline, retained,
        image_bindings=tuple(sorted((*original.image_bindings, *closeups), key=lambda item: item.asset_id)),
        acceptance=coverage_and_performance,
        revised_requirement_ids=("duration", "performance"),
        additional_image_reference_ids=("s03-closeup-face-a", "s03-closeup-face-b"),
    )
    validate_authored_generation_retarget_target(baseline, retained, target)
    assert target.output_requirement == baseline.compiled_request.activation_scope.request.output_requirement
    bound_by_id = {item.asset_id: item for item in target.image_bindings}
    for item in original.image_bindings:
        assert bound_by_id[item.asset_id] == item
    for item in closeups:
        assert bound_by_id[item.asset_id] == item
    assert target.verify().content_hash == target.content_hash

    prompt = baseline.compiled_request.activation_scope.request.prompt_text
    repaired, selected = _retarget_binding(
        baseline, retained, target,
        request_changes={
            "prompt_text": prompt + " Multi-shot coverage, visible anxious closeup, immediate reaction.",
        },
    )
    # The candidate's QA recipe is the new exact acceptance contract.
    selected.capabilities = retained.candidate.capabilities
    selected.recipe = SimpleNamespace(acceptance_policy=coverage_and_performance)
    validate_authored_generation_retarget_binding(
        repaired, selected, target, target_goal=selected.final_output_goal,
        authorization_receipt_id=target.authorization_reference,
    )
    assert allows_authored_generation_retarget(repaired, selected)
    projection = SimpleNamespace(requirement=SimpleNamespace(
        target_shot=SimpleNamespace(shot_id=target.shot_id), generation_intent=target.intent))
    assert is_authored_generation_retarget_prospect(
        inputs=repaired.inputs, projection=projection, policy=repaired.policy,
        latest=repaired.inputs.evidence[-1], prior=retained.candidate,
    )


@pytest.mark.parametrize("change", [
    "undeclared_qa", "wrong_qa_declaration", "changed_proof", "undeclared_image",
    "removed_original", "changed_original_hash", "wrong_image_declaration",
])
def test_same_model_repair_rejects_undeclared_or_non_additive_qa_and_images(tmp_path, change):
    from ai_video.production.generation_authored_retarget import (
        validate_authored_generation_retarget_target,
    )
    from ai_video.production.video import VideoImageReferenceBinding

    baseline, retained, original, _, _ = _same_model_reference_repair(tmp_path)
    old_acceptance = retained.candidate.recipe.acceptance_policy
    revised_acceptance = _changed_acceptance(
        old_acceptance,
        changes={"performance": {"observable": "The subject visibly shows anxiety in a readable closeup."}},
    )
    additional = VideoImageReferenceBinding(
        role="reference", asset_id="s03-new-closeup", asset_sha256="a" * 64,
        mime_type="image/png", width=1920, height=1080, size_bytes=90_000,
    )
    images = (*original.image_bindings, additional)
    values = {
        "image_bindings": tuple(sorted(images, key=lambda item: item.asset_id)),
        "acceptance": revised_acceptance,
        "revised_requirement_ids": ("performance",),
        "additional_image_reference_ids": (additional.asset_id,),
    }
    if change == "undeclared_qa":
        values["revised_requirement_ids"] = ()
    elif change == "wrong_qa_declaration":
        values["revised_requirement_ids"] = ("duration",)
    elif change == "changed_proof":
        old_proof = next(
            item["proof"] for item in old_acceptance.profile_payload["generation_requirements"]
            if item["requirement_id"] == "performance"
        )
        values["acceptance"] = _changed_acceptance(
            old_acceptance, changes={"performance": {
                "proof": "human" if old_proof != "human" else "technical",
            }},
        )
    elif change == "undeclared_image":
        values["image_bindings"] = tuple(sorted(images, key=lambda item: item.asset_id))
        values["additional_image_reference_ids"] = ()
    elif change == "removed_original":
        values["image_bindings"] = original.image_bindings[1:]
        values["additional_image_reference_ids"] = ()
    elif change == "changed_original_hash":
        changed = original.image_bindings[0].model_copy(update={"asset_sha256": "f" * 64})
        values["image_bindings"] = tuple(sorted(
            (changed, *original.image_bindings[1:]), key=lambda item: item.asset_id,
        ))
        values["additional_image_reference_ids"] = ()
    elif change == "wrong_image_declaration":
        values["additional_image_reference_ids"] = ("s03-not-bound",)

    target = _retarget_target(baseline, retained, **values)
    with pytest.raises(ValueError):
        validate_authored_generation_retarget_target(baseline, retained, target)


def test_same_model_repair_rejects_duplicate_or_nonraw_declarations(tmp_path):
    from ai_video.production.generation_authored_retarget import (
        _acceptance_revision_ids,
    )
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.hashing import canonical_sha256
    from ai_video.production.video import VideoImageReferenceBinding

    baseline, retained, original, _, _ = _same_model_reference_repair(tmp_path)
    old_acceptance = retained.candidate.recipe.acceptance_policy
    old_proof = next(
        item["proof"] for item in old_acceptance.profile_payload["generation_requirements"]
        if item["requirement_id"] == "performance"
    )
    changed_proof = _changed_acceptance(old_acceptance, changes={
        "performance": {"proof": "human" if old_proof != "human" else "technical"},
    })
    assert _acceptance_revision_ids(old_acceptance, changed_proof) is None
    assert _acceptance_revision_ids(
        old_acceptance,
        old_acceptance.model_copy(update={"measurement_contract_version": "unapproved-v2"}),
    ) is None
    renamed_data = old_acceptance.model_dump(mode="json")
    renamed_payload = renamed_data["profile_payload"]
    renamed_payload.pop("content_hash")
    renamed_ids = tuple(
        "performance-renamed" if item == "performance" else item
        for item in renamed_data["required_requirement_ids"]
    )
    renamed_payload["required_requirement_ids"] = list(renamed_ids)
    renamed_payload["generation_requirements"] = [
        {
            **rule,
            "requirement_id": "performance-renamed"
            if rule["requirement_id"] == "performance" else rule["requirement_id"],
        }
        for rule in renamed_payload["generation_requirements"]
    ]
    renamed_hash = canonical_sha256(renamed_payload)
    renamed_payload["content_hash"] = renamed_hash
    renamed_data.update(
        required_requirement_ids=renamed_ids,
        profile_content_hash=renamed_hash,
        profile_payload=renamed_payload,
    )
    renamed_acceptance = DomainAcceptancePolicy.model_validate(renamed_data)
    assert _acceptance_revision_ids(old_acceptance, renamed_acceptance) is None

    extra = VideoImageReferenceBinding(
        role="reference", asset_id="s03-extra", asset_sha256="c" * 64,
        mime_type="image/png", width=1920, height=1080, size_bytes=80_000,
    )
    with pytest.raises(ValueError, match="unique and in canonical order"):
        _retarget_target(
            baseline, retained,
            image_bindings=tuple(sorted((*original.image_bindings, extra), key=lambda item: item.asset_id)),
            additional_image_reference_ids=("s03-extra", "s03-extra"),
        )
    with pytest.raises(ValueError, match="unique and in canonical order"):
        _retarget_target(
            baseline, retained,
            revised_requirement_ids=("performance", "performance"),
        )
    with pytest.raises(ValueError, match="unique canonical asset order"):
        _retarget_target(
            baseline, retained,
            image_bindings=tuple(sorted(
                (*original.image_bindings, original.image_bindings[0]),
                key=lambda item: item.asset_id,
            )),
        )

    # Removing a previously required raw-generation rule is not a revision of
    # that rule; the existing /4 validator and shared delta predicate reject it.
    reduced = old_acceptance.model_copy(update={
        "required_requirement_ids": tuple(
            item for item in old_acceptance.required_requirement_ids if item != "performance"
        ),
    })
    assert _acceptance_revision_ids(old_acceptance, reduced) is None


@pytest.mark.parametrize("change", ["images", "media", "output", "compiler", "capability"])
def test_same_model_repair_cannot_retarget_conditioning_or_execution_contract(tmp_path, change):
    from ai_video.production.generation_authored_retarget import (
        AuthoredGenerationRetargetTarget, validate_authored_generation_retarget_target,
    )
    from ai_video.production._shot_router_contracts import AdapterCompilerContract

    baseline, retained, target, _, _ = _same_model_reference_repair(tmp_path)
    values = {key: getattr(target, key) for key in type(target).model_fields if key != "content_hash"}
    if change == "images":
        values["image_bindings"] = (target.image_bindings[0].model_copy(update={"asset_sha256": "f" * 64}),
                                    *target.image_bindings[1:])
    elif change == "media":
        values["media_bindings"] = ()
    elif change == "output":
        values["output_requirement"] = target.output_requirement.model_copy(update={"duration_seconds": 14})
    elif change == "compiler":
        values["compiler_contract"] = AdapterCompilerContract.create(compiler_id="other", compiler_version="1")
    else:
        values["capability_id"] = "other"
    changed = AuthoredGenerationRetargetTarget.create(**values)
    with pytest.raises(ValueError, match="same-model authored repair"):
        validate_authored_generation_retarget_target(baseline, retained, changed)


@pytest.mark.parametrize("change", ["unknown", "quota", "resample", "remote", "budget", "same_prompt", "images", "output"])
def test_same_model_compiled_repair_remains_fail_closed(tmp_path, change):
    from ai_video.production._qualification_authoring_revision import allows_authored_generation_retarget

    baseline, _, _, repaired, selected = _same_model_reference_repair(tmp_path)
    if change == "unknown":
        item = repaired.inputs.evidence[-1].model_copy(update={"outcome": "unknown_outcome"})
        repaired.inputs = repaired.inputs.model_copy(update={"evidence": (item,), "latest_attempt_hash": item.evidence_hash})
    elif change == "quota":
        repaired.inputs = repaired.inputs.model_copy(update={"limits": repaired.inputs.limits.model_copy(
            update={"paid_submit_ceiling": 3})})
    elif change == "resample":
        repaired.inputs = repaired.inputs.model_copy(update={"policy": repaired.inputs.policy.model_copy(
            update={"max_resamples": 1})})
    elif change in {"remote", "budget"}:
        setattr(repaired.policy, change + "_authorized", False)
    else:
        request = repaired.compiled_request.activation_scope.request
        key, value = ({
            "same_prompt": ("prompt_text", baseline.compiled_request.activation_scope.request.prompt_text),
            "images": ("image_bindings", request.image_bindings[1:]),
            "output": ("output_requirement", request.output_requirement.model_copy(update={"duration_seconds": 14})),
        })[change]
        repaired.compiled_request.activation_scope.request = request.model_copy(update={key: value})
    assert not allows_authored_generation_retarget(repaired, selected)
