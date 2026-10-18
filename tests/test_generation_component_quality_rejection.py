"""Component-scoped generation rubrics remain exact quality authorities."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.domain_acceptance import (
    ComponentRequirementAllocation,
    DomainAcceptancePolicy,
    GenerationEvaluationAuthority,
    ProductionRequirementAllocation,
)
from ai_video.production.generation_diagnosis import AttemptEvidence
from ai_video.production.generation_evaluation import (
    GenerationEvaluationSource,
    GenerationObservation,
)
from ai_video.production.generation_feedback import record_attempt_evaluation
from ai_video.production.generation_experience import GenerationExperience
from ai_video.production.generation_rejection import validate_quality_rejection_experience
from ai_video.production.generation_recipe import RequirementExpression
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.dependency import (
    build_production_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.models import (
    ArtifactReference,
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    SourceReference,
    ToolIdentity,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    _canonical_json_bytes,
    _canonical_yaml_bytes,
    prepare_dependency_graph_transition,
    prepare_project_registry_commit,
)
from ai_video.production.production_strategy_contracts import (
    ProductionComponentLineage,
    ProductionCoverage,
    ProductionIntent,
    ProductionOperation,
    ProductionUnit,
)
from ai_video.production.video import (
    BillingKind,
    ProviderProfilePointer,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoOutputRecoveryStrategy,
    VideoOutputRequirement,
    VideoProviderCapabilities,
    VideoTaskState,
)
from ai_video.production.video_fake import FakeVideoScenario
from ai_video.production.video_generation import VideoGenerationService
from ai_video.production_planning import ProductionPlanningService
from ai_video.planning.production_strategy import ProductionStrategyPolicy
from ai_video.production.video_requirement import (
    ProviderNeutralVideoRequirement,
    VerifiedGenerationRequirementProjection,
)

from production_generation_execution_factory import (
    NativeFixtureVideoProvider,
    prepare_generation_execution,
)
from production_project_factory import make_p8_video_generation_base
from test_generation_quality_rejection import ACTOR
from test_generation_quality_rejection import _fetched_experience
from test_production_planning_generation import _generation_target
from test_production_video import _paid_authorization, _paid_preview


def _component_acceptance(global_acceptance, *, profile_id="component-specific-generation"):
    payload = dict(global_acceptance.profile_payload)
    payload.pop("content_hash", None)
    payload["profile_id"] = profile_id
    digest = canonical_sha256(payload)
    return type(global_acceptance).model_validate({
        **global_acceptance.model_dump(mode="python"),
        "profile_id": profile_id,
        "profile_content_hash": digest,
        "profile_payload": {**payload, "content_hash": digest},
    })


def _component_experience(
    tmp_path,
    *,
    lineage_component_id="component-visual",
    lineage_allocation_hash=None,
    qa_profile_id=None,
):
    committer, original, _, attempt = _fetched_experience(tmp_path, verdict="FAIL")
    loaded = __import__(
        "ai_video.production.project", fromlist=["load_production_project"]
    ).load_production_project(tmp_path / "project.yaml")
    binding = committer._reopen_generation_execution_binding(
        attempt.video_generation_state.execution_binding
    )
    global_acceptance = loaded.qa_policy.selected_generation_acceptance()
    component_acceptance = _component_acceptance(global_acceptance)
    selected_component_acceptance = (
        _component_acceptance(global_acceptance, profile_id=qa_profile_id)
        if qa_profile_id else component_acceptance
    )
    requirement_id = global_acceptance.required_requirement_ids[0]
    task_id = binding.inputs.limits.task_id
    parent = loaded.shots[1]
    parent_ref = loaded.project.artifacts.shots[1]
    allocation = ProductionRequirementAllocation(
        allocation_id="component-quality-allocation",
        parent_shot_id=parent.shot_id,
        parent_shot_content_hash=parent.content_hash,
        task_id=task_id,
        parent_acceptance_hash=global_acceptance.profile_content_hash,
        parent_requirement_ids=(requirement_id,),
        components=(ComponentRequirementAllocation(
            component_id="component-visual",
            requirement_ids=(requirement_id,),
            generation_acceptance=selected_component_acceptance,
        ),),
    )
    qa_policy = seal_artifact(loaded.qa_policy.model_copy(update={
        "revision": loaded.qa_policy.revision + 1,
        "production_allocations": (allocation,),
        "content_hash": "0" * 64,
    }))
    original_shot = binding.projection.requirement.target_shot
    lineage = ProductionComponentLineage(
        parent=parent_ref,
        origin_project_hash=loaded.project.content_hash,
        parent_shot_id=parent.shot_id,
        task_id=task_id,
        coverage_id="component-quality-coverage",
        component_id=lineage_component_id,
        allocation_hash=lineage_allocation_hash or allocation.allocation_hash,
        decision_hash="a" * 64,
        operation=ProductionOperation.GENERATE_FULL_SHOT,
    )
    target_shot = seal_artifact(original_shot.model_copy(update={
        "revision": original_shot.revision + 1,
        "content_hash": "0" * 64,
        "production_lineage": lineage,
    }))
    requirement = ProviderNeutralVideoRequirement.create(**{
        **binding.projection.requirement.model_dump(mode="python"),
        "target_shot": target_shot,
    })
    projection = VerifiedGenerationRequirementProjection.create(
        requirement=requirement,
        plan_hash=binding.projection.plan_hash,
        verified_source_request_content_hash=requirement.source_request_content_hash,
        target_shot_id=target_shot.shot_id,
        target_shot_revision=target_shot.revision,
        target_shot_content_hash=target_shot.content_hash,
    )
    from ai_video.planning.video_planner import VideoPlanner

    recipe = original.candidate.recipe.model_copy(update={
        "acceptance_policy": component_acceptance,
        "rubric_hash": component_acceptance.profile_content_hash,
        "requirement_hash": requirement.requirement_hash,
    })
    candidate = original.candidate.model_copy(update={"recipe": recipe})
    inputs = binding.inputs.model_copy(update={
        "candidates": tuple(candidate if item.candidate_id == candidate.candidate_id else item
                             for item in binding.inputs.candidates),
        "facts_hash": VideoPlanner.generation_difficulty(projection)["facts_hash"],
        "rubric_hash": component_acceptance.profile_content_hash,
    })
    binding = binding.model_copy(update={"projection": projection, "inputs": inputs})
    source = original.evaluation_sources[0].model_copy(update={
        "rubric_hash": component_acceptance.profile_content_hash,
        "qa_policy_content_hash": qa_policy.content_hash,
    })
    evidence = original.evidence[0].model_copy(update={
        "recipe_scope_hash": candidate.scope_hash,
        "facts_hash": canonical_sha256(requirement.model_dump(
            mode="json", exclude={"requirement_id", "requirement_hash"}
        )),
        "rubric_hash": component_acceptance.profile_content_hash,
        "findings": source.project_findings(),
    })
    experience = GenerationExperience(
        projection=projection,
        candidate=candidate,
        evidence=(evidence,),
        evaluation_sources=(source,),
    )
    return binding, experience, evidence, source, qa_policy


def test_component_rubric_is_used_for_quality_rejection_validation(tmp_path):
    binding, experience, evidence, source, qa_policy = _component_experience(tmp_path)

    diagnosis = validate_quality_rejection_experience(
        binding=binding,
        experience=experience,
        evidence=evidence,
        request=binding.compiled_request.activation_scope.request,
        attempt_id=evidence.attempt_id,
        artifact_sha256=evidence.artifact_sha256,
        qa_policy=qa_policy,
        history=(evidence,),
        evaluation_sources=(source,),
    )

    assert diagnosis.failure_classes == ("QUALITY_FAILURE",)


@pytest.mark.parametrize(
    "mismatch",
    ["component", "allocation", "rubric", "selected-authority"],
)
def test_component_quality_rejection_mismatches_fail_without_writes(tmp_path, mismatch):
    kwargs = {}
    if mismatch == "component":
        kwargs["lineage_component_id"] = "unallocated-component"
    elif mismatch == "allocation":
        kwargs["lineage_allocation_hash"] = "0" * 64
    elif mismatch == "selected-authority":
        kwargs["qa_profile_id"] = "different-selected-component-rubric"
    binding, experience, evidence, source, qa_policy = _component_experience(
        tmp_path, **kwargs,
    )
    if mismatch == "rubric":
        source = source.model_copy(update={"rubric_hash": "0" * 64})
        evidence = evidence.model_copy(update={"findings": source.project_findings()})
        experience = experience.model_copy(update={
            "evidence": (evidence,),
            "evaluation_sources": (source,),
        })
    before = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in (tmp_path / "state").rglob("*") if path.is_file()
    }

    with pytest.raises(ValueError):
        validate_quality_rejection_experience(
            binding=binding,
            experience=experience,
            evidence=evidence,
            request=binding.compiled_request.activation_scope.request,
            attempt_id=evidence.attempt_id,
            artifact_sha256=evidence.artifact_sha256,
            qa_policy=qa_policy,
            history=(evidence,),
            evaluation_sources=(source,),
        )

    after = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in (tmp_path / "state").rglob("*") if path.is_file()
    }
    assert after == before


def _component_generation_acceptance(
    *, profile_id="strategy-component-generation-quality-close",
):
    rule = RequirementExpression(
        requirement_id="visual",
        level="acceptance",
        stage="raw_generation",
        dimension="visual",
        observable="authored component visual",
        tolerance="exact",
        measurement="fixture evaluator",
        proof="technical",
        production_owner="generation",
        intent_paths=("target_shot.shot_id",),
    )
    payload = {
        "domain_id": "strategy-test",
        "profile_id": profile_id,
        "profile_version": "1",
        "measurement_contract_version": "strategy-test/1",
        "required_requirement_ids": ("visual",),
        "generation_requirements": (
            rule.model_dump(mode="json", exclude={"native_text"}),
        ),
    }
    digest = canonical_sha256(payload)
    return DomainAcceptancePolicy(
        domain_id="strategy-test",
        profile_id=profile_id,
        profile_version="1",
        profile_content_hash=digest,
        profile_payload={**payload, "content_hash": digest},
        measurement_contract_version="strategy-test/1",
        required_requirement_ids=("visual",),
    )


def _parent_visual_acceptance():
    payload = {
        "domain_id": "component-quality-close",
        "profile_id": "component-quality-close-final",
        "profile_version": "1",
        "measurement_contract_version": "component-quality-close/1",
        "required_requirement_ids": ("visual",),
        "source_use_requirements": ({
            "requirement_id": "visual",
            "proof": "technical",
            "stage": "source_use",
        },),
    }
    digest = canonical_sha256(payload)
    return DomainAcceptancePolicy(
        domain_id=payload["domain_id"],
        profile_id=payload["profile_id"],
        profile_version="1",
        profile_content_hash=digest,
        profile_payload={**payload, "content_hash": digest},
        measurement_contract_version=payload["measurement_contract_version"],
        required_requirement_ids=("visual",),
    )


def _persist_video_component_authoring(tmp_path):
    inputs = make_p8_video_generation_base(tmp_path, schema_version="2.7")
    loaded = inputs.project
    parent = loaded.shots[0]
    task_id = "component-quality-close-task"
    child_shot_id = "component-quality-close-child"
    duration_frames = round(
        parent.duration_policy.seconds * loaded.project.delivery_profile.fps
    )
    unit = ProductionUnit(
        component_id="component-quality-close-visual",
        shot_id=child_shot_id,
        intent="Generate the authored component visual.",
        duration_frames=duration_frames,
        requirement_ids=("visual",),
        source_options=(),
    )
    coverage = ProductionCoverage(
        coverage_id="component-quality-close-coverage",
        allocation_id="component-quality-close-allocation",
        units=(unit,),
    )
    intent = ProductionIntent(
        task_id=task_id,
        allowed_operations=(ProductionOperation.GENERATE_FULL_SHOT,),
        protected_requirement_ids=("visual",),
        coverage_options=(coverage,),
    )
    parent = seal_artifact(parent.model_copy(update={
        "revision": parent.revision + 1,
        "content_hash": "0" * 64,
        "production_intent": intent,
    }))
    parent_reference = ArtifactReference(
        artifact_id=parent.artifact_id,
        revision=parent.revision,
        content_hash=parent.content_hash,
        path=Path(f"creative/shots/{parent.content_hash}.yaml"),
    )
    project = seal_artifact(loaded.project.model_copy(update={
        "revision": loaded.project.revision + 1,
        "content_hash": "0" * 64,
        "artifacts": loaded.project.artifacts.model_copy(update={
            "shots": (parent_reference, *loaded.project.artifacts.shots[1:]),
        }),
    }))
    committer = ProductionStateCommitter(tmp_path)
    base = prepare_project_registry_commit(
        manifest=loaded.manifest,
        project=project,
        registry=loaded.registry,
        attempt_id="component-quality-close-authoring",
    )
    candidate_loaded = loaded.model_copy(update={
        "project": project,
        "shots": (parent, *loaded.shots[1:]),
        "manifest": loaded.manifest.model_copy(update={
            "active_project": base.next_project,
            "active_registry": base.next_registry,
        }),
    })
    graph = build_production_dependency_graph(replace(inputs, project=candidate_loaded))
    states = resolve_dependency_state(graph, loaded.manifest.dependency_states).states
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=loaded.manifest.manifest_revision,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    graph_payload = _canonical_json_bytes(graph)
    shot_payload = _canonical_yaml_bytes(parent)
    project_commit = replace(
        base,
        dependency_graph_transition=transition,
        artifacts=tuple(sorted(
            (*base.artifacts,
             PreparedArtifact(
                 transition.candidate_dependency_graph.path,
                 graph_payload,
                 hashlib.sha256(graph_payload).hexdigest(),
             ),
             PreparedArtifact(
                 parent_reference.path,
                 shot_payload,
                 hashlib.sha256(shot_payload).hexdigest(),
             )),
            key=lambda item: item.relative_path.as_posix(),
        )),
    )
    committer.commit(project_commit)
    loaded = load_production_project(tmp_path / "project.yaml")

    parent_acceptance = _parent_visual_acceptance()
    component_acceptance = _component_generation_acceptance()
    allocation = ProductionRequirementAllocation(
        allocation_id=coverage.allocation_id,
        parent_shot_id=parent.shot_id,
        parent_shot_content_hash=parent.content_hash,
        task_id=task_id,
        parent_acceptance_hash=parent_acceptance.profile_content_hash,
        parent_requirement_ids=("visual",),
        components=(ComponentRequirementAllocation(
            component_id=unit.component_id,
            requirement_ids=("visual",),
            generation_acceptance=component_acceptance,
        ),),
    )
    evaluator = ToolIdentity(name="component-quality-close-evaluator", version="1")
    policy = seal_artifact(QaPolicy(
        artifact_id="component-quality-close-qa",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="component-quality-close-qa",
        source_provenance=(SourceReference(
            kind="derived", reference="component-quality-close-fixture",
        ),),
        policy_id="component-quality-close-qa",
        policy_version="1",
        required_layers=(QaLayer.SEMANTIC,),
        technical_thresholds=QaTechnicalThresholds(
            black_luma_max_milli=10,
            silence_peak_max_millidb=-60_000,
            clipping_peak_min_millidb=-100,
        ),
        layout_rules=QaLayoutRules(
            safe_area_inset_milli=50,
            caption_overflow_tolerance_milli=0,
        ),
        strategy_rules_version="1",
        semantic_requirement="required",
        semantic_authorities=(evaluator,),
        generation_evaluation_authorities=(
            GenerationEvaluationAuthority(evaluator=evaluator, proof="technical"),
            GenerationEvaluationAuthority(evaluator=evaluator, proof="human"),
        ),
        domain_acceptance=parent_acceptance,
        production_allocations=(allocation,),
    ))
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="component-quality-close-qa-selection",
    )
    return committer, task_id, parent.shot_id, child_shot_id, component_acceptance


def _component_close_runtime(tmp_path, *, abandon):
    committer, task_id, parent_shot_id, child_shot_id, acceptance = (
        _persist_video_component_authoring(tmp_path)
    )

    planning = ProductionPlanningService(
        committer=committer,
        targets=(_generation_target(),),
        policy=ProductionStrategyPolicy(
            preference="generation", allow_generation_exploration=True,
        ),
    )
    decision = planning.prepare(parent_shot_id=parent_shot_id)
    assert decision.disposition == "selected"
    planning.materialize(decision=decision, attempt_id="component-quality-close-materialize")

    loaded = load_production_project(tmp_path / "project.yaml")
    child = next(shot for shot in loaded.shots if shot.shot_id == child_shot_id)
    assert child.production_lineage is not None
    assert child.production_lineage.source is None
    source = next(asset for asset in loaded.registry.assets if asset.asset_id == "image-shot-1")
    output = VideoOutputRequirement(
        duration_seconds=3,
        width=64,
        height=64,
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=False,
    )
    profile = ProviderProfilePointer(
        profile_id="component-quality-video-profile",
        profile_version="v1",
        profile_path=Path(f"provider-profiles/{'d' * 64}.json"),
        profile_sha256="d" * 64,
    )
    capability = VideoCapabilityVariant(
        capability_id="component-quality-i2v",
        provider_kind="fake_video",
        model_id="fake-h264",
        profile_version="v1",
        execution_kind=VideoExecutionKind.REMOTE,
        billing_kind=BillingKind.METERED,
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        output=output,
        allowed_image_roles=("first_frame",),
        required_first_frame=True,
        max_reference_count=0,
        allowed_image_mime_types=(source.mime_type,),
        max_image_bytes=max(source.size_bytes, 1),
        min_image_width=1,
        min_image_height=1,
        negative_prompt_supported=True,
        seed_supported=True,
        fps_supported=True,
        idempotent_submit=False,
        lookup_supported=True,
        output_recovery_strategy=VideoOutputRecoveryStrategy.REQUERY_BY_EFFECT_ID,
    )
    provider = NativeFixtureVideoProvider(
        native_prompt_text=f"{child.shot_id} authored component visual",
        compiler_id="component-quality-close-fixture",
        capabilities=VideoProviderCapabilities.create(
            provider_name="fake-video", variants=(capability,),
        ),
        artifact_bytes=(
            Path(__file__).parent / "fixtures/generated_video/fake-video.mp4"
        ).read_bytes(),
        scenario=FakeVideoScenario(status_events=(VideoTaskState.SUCCEEDED,)),
    )
    request = VideoGenerationRequest.create(
        generation_id="component-quality-close-generation",
        provider_name="fake-video",
        provider_kind="fake_video",
        model_id="fake-h264",
        provider_profile=profile,
        target_shot_id=child.shot_id,
        target_shot_revision=child.revision,
        target_shot_content_hash=child.content_hash,
        target_asset_role="primary_visual",
        target_visual_strategy="generated_video",
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        prompt_text=f"Generate {child.shot_id} authored component visual",
        negative_prompt_text="flicker",
        image_bindings=(VideoImageReferenceBinding(
            role="first_frame",
            asset_id=source.asset_id,
            asset_sha256=source.sha256,
            mime_type=source.mime_type,
            width=source.width or 64,
            height=source.height or 64,
            size_bytes=source.size_bytes,
        ),),
        output_requirement=output,
        seed=17,
        base_project=loaded.manifest.active_project,
        base_registry=loaded.manifest.active_registry,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        input_artifact_ids=(child.artifact_id, source.asset_id),
        output_asset_id="component-quality-close-video",
    )
    prepared = prepare_generation_execution(
        project=loaded,
        provider=provider,
        request=provider.resolve(request),
        task_id=task_id,
        compiler_id="component-quality-close-fixture",
        compiler_version="1",
        use_current_generation_acceptance=True,
    )
    candidate = next(
        item for item in prepared.binding.inputs.candidates
        if item.candidate_id == prepared.binding.decision.selected_candidate_id
    )
    assert candidate.recipe.acceptance_policy == acceptance

    attempt_id = "component-quality-close-abandon" if abandon else "component-quality-close-reject"
    preview = _paid_preview(
        prepared.resolved,
        attempt_id=attempt_id,
        video_preview=provider.preview(prepared.resolved),
    )
    authorization = _paid_authorization(preview)
    committer = ProductionStateCommitter(
        tmp_path,
        paid_provider_authorizer=lambda exact: authorization if exact == preview else None,
        paid_provider_clock=lambda: authorization.issued_at,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=attempt_id,
        request=prepared.resolved,
        execution_binding=prepared.binding,
    )
    service.submit_once(
        attempt_id=attempt_id,
        paid_preview=preview,
        reservation_id=f"{attempt_id}-reservation",
    )
    service.refresh_once(attempt_id=attempt_id)
    service.fetch_once(attempt_id=attempt_id)

    manifest = committer._read_manifest()
    attempt = next(item for item in manifest.attempts if item.attempt_id == attempt_id)
    state = attempt.video_generation_state
    fetch = committer._reopen_video_fetch(state.fetch_receipt)
    policy = load_production_project(tmp_path / "project.yaml").qa_policy
    assert policy is not None
    technical_verdict = "NOT_EVALUATED" if abandon else "FAIL"
    sources = [
        GenerationEvaluationSource(
            request_hash=prepared.resolved.activation_scope.request.request_input_hash,
            artifact_sha256=fetch.artifact_sha256,
            rubric_hash=candidate.recipe.rubric_hash,
            qa_policy_content_hash=policy.content_hash,
            evaluator=next(
                item.evaluator for item in policy.generation_evaluation_authorities
                if item.proof == "technical"
            ),
            proof="technical",
            observations=(GenerationObservation(
                requirement_id="visual",
                verdict=technical_verdict,
                observation="Exact offline evaluator retains the component result.",
            ),),
        ),
    ]
    if abandon:
        sources.append(GenerationEvaluationSource(
            request_hash=prepared.resolved.activation_scope.request.request_input_hash,
            artifact_sha256=fetch.artifact_sha256,
            rubric_hash=candidate.recipe.rubric_hash,
            qa_policy_content_hash=policy.content_hash,
            evaluator=next(
                item.evaluator for item in policy.generation_evaluation_authorities
                if item.proof == "human"
            ),
            proof="human",
            observations=(GenerationObservation(
                requirement_id="visual",
                verdict="FAIL",
                observation="Human review rejects the fetched component result.",
            ),),
        ))
    evidence = AttemptEvidence(
        task_id=task_id,
        shot_id=child.shot_id,
        attempt_id=attempt_id,
        recipe_scope_hash=candidate.scope_hash,
        facts_hash=prepared.binding.inputs.facts_hash,
        rubric_hash=candidate.recipe.rubric_hash,
        request_hash=prepared.resolved.activation_scope.request.request_input_hash,
        artifact_sha256=fetch.artifact_sha256,
        outcome="media",
        findings=tuple(finding for source_item in sources
                       for finding in source_item.project_findings()),
    )
    experience = GenerationExperience(
        projection=prepared.binding.projection,
        candidate=candidate,
        evidence=(evidence,),
        evaluation_sources=tuple(sources),
    )
    committer.record_generation_experience(attempt_id=attempt_id, experience=experience)
    manifest = committer._read_manifest()
    attempt = next(item for item in manifest.attempts if item.attempt_id == attempt_id)
    return committer, attempt_id, attempt, manifest, experience


@pytest.mark.parametrize("abandon", [False, True], ids=["reject", "abandon-mixed"])
def test_materialized_component_quality_close_reopens_and_replays(tmp_path, abandon):
    committer, attempt_id, attempt, manifest, experience = _component_close_runtime(
        tmp_path, abandon=abandon,
    )
    state = attempt.video_generation_state
    arguments = {
        "attempt_id": attempt_id,
        "expected_manifest_revision": manifest.manifest_revision,
        "experience_content_hash": state.generation_experiences[-1].content_hash,
        "actor": ACTOR,
    }
    if abandon:
        closed = committer.abandon_video_generation(
            **arguments,
            reason="The offline mixed evaluation retains a known failure and unresolved proof.",
        )
    else:
        closed = committer.reject_video_generation(**arguments)

    closed_attempt = next(item for item in closed.attempts if item.attempt_id == attempt_id)
    receipt = committer._reopen_generation_quality_rejection(
        closed_attempt.video_generation_state.quality_rejection
    )
    assert closed_attempt.status.value == "failed"
    assert receipt.evidence_hash == experience.evidence[-1].evidence_hash
    assert receipt.qa_policy.content_hash == experience.evaluation_sources[0].qa_policy_content_hash
    assert receipt.diagnosis.failure_classes == (
        ("EVIDENCE_GAP", "QUALITY_FAILURE") if abandon else ("QUALITY_FAILURE",)
    )
    reopened = load_production_project(tmp_path / "project.yaml")
    assert reopened.manifest == closed
    if abandon:
        replay = committer.abandon_video_generation(
            **arguments,
            reason="The offline mixed evaluation retains a known failure and unresolved proof.",
        )
    else:
        replay = committer.reject_video_generation(**arguments)
    assert replay == closed
    assert record_attempt_evaluation(
        committer=committer, attempt_id=attempt_id,
    ) == experience


def test_component_quality_close_refuses_stale_selected_rubric_without_writes(tmp_path):
    committer, attempt_id, attempt, _, _ = _component_close_runtime(
        tmp_path, abandon=False,
    )
    loaded = load_production_project(tmp_path / "project.yaml")
    allocation = loaded.qa_policy.production_allocations[0]
    changed_acceptance = _component_generation_acceptance(
        profile_id="stale-component-quality-close-rubric",
    )
    changed_allocation = allocation.model_copy(update={
        "components": tuple(
            component.model_copy(update={"generation_acceptance": changed_acceptance})
            if component.component_id == "component-quality-close-visual"
            else component
            for component in allocation.components
        ),
    })
    changed_policy = seal_artifact(loaded.qa_policy.model_copy(update={
        "revision": loaded.qa_policy.revision + 1,
        "production_allocations": (changed_allocation,),
        "content_hash": "0" * 64,
    }))
    active = committer.activate_qa_policy(
        changed_policy,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="component-quality-close-stale-rubric",
    )
    state = attempt.video_generation_state
    arguments = {
        "attempt_id": attempt_id,
        "expected_manifest_revision": active.manifest_revision,
        "experience_content_hash": state.generation_experiences[-1].content_hash,
        "actor": ACTOR,
    }
    before = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file() and path != tmp_path / "state/commit.lock"
    }

    with pytest.raises(AiVideoError, match="component generation acceptance is not current"):
        committer.reject_video_generation(**arguments)

    after = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file() and path != tmp_path / "state/commit.lock"
    }
    assert after == before
