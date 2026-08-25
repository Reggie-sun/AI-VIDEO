from __future__ import annotations

import pytest

import ai_video.production as production
import ai_video.planning as planning
from ai_video.errors import AiVideoError
from ai_video.production import dependency as dependency
from ai_video.planning import (
    PlanOutcome,
    ProductionPolicyInput,
    ShotIntentEvidence,
    VideoPlanner,
    VideoPlanningRequest,
    require_current_video_plan,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    ActorIdentity,
    DependencyNode,
    DependencyNodeKind,
    DependencySemanticRole,
    FingerprintContribution,
    QaVerdict,
)
from ai_video.production.project import load_production_project
from ai_video.production.review import validate_repair_scope
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.shot_router import (
    AdapterCompilerContract,
    MotionRequirement,
    RoutingOutcome,
    VideoGenerationResolver,
)
from ai_video.production.video import VideoGenerationMode
from ai_video.production.video_compiler import (
    CompiledProviderVideoRequest,
    compile_provider_video_request,
)
from ai_video.production.video_requirement import (
    AudioNeed,
    GenerationIntent,
    MotionEnvelope,
    OutputNeed,
    ProviderNeutralGenerationIntentProjection,
    SubjectAction,
)
from production_project_factory import make_composition_spec
from test_production_commercial_execution import _plan as _commercial_plan
from test_production_commercial_source_preparation import (
    _candidate,
    _make_commercial_state_project,
    _review_authorizer,
    _review_candidate,
    _state_request,
)
from test_production_commercial_visual_review import (
    REVIEW_TOOL,
    _policy as _commercial_policy,
)
from test_production_ecommerce_ad_coordinator import _Facade
from test_production_shot_router import (
    HASH_F,
    _asset as _router_asset,
    _capabilities,
    _context,
    _lifecycle,
    _output,
    _policy as _routing_policy,
    _profile,
    _variant,
)


def test_commercial_failure_classification_keeps_product_pack_and_graphics_isolated() -> None:
    product_fidelity = production.classify_commercial_failure(
        failure_type=production.CommercialFailureType.PRODUCT_FIDELITY_MISMATCH,
        product_reference_node_id="product-reference-qingyan",
        source_node_id="source-keyframe-04",
        shot_node_id="shot-04-video",
    )
    typography = production.classify_commercial_failure(
        failure_type=production.CommercialFailureType.COMMERCIAL_TYPOGRAPHY,
        product_reference_node_id="product-reference-qingyan",
        source_node_id="source-keyframe-04",
        shot_node_id="shot-04-video",
        composition_node_id="composition-main",
    )

    assert product_fidelity.root_node_ids == ("source-keyframe-04",)
    assert product_fidelity.proposed_boundary_node_ids == (
        "source-keyframe-04",
        "shot-04-video",
    )
    assert "product-reference-qingyan" not in product_fidelity.proposed_boundary_node_ids
    assert typography.root_node_ids == ("composition-main",)
    assert typography.proposed_boundary_node_ids == ("composition-main",)
    assert validate_repair_scope(
        expected_node_ids=product_fidelity.proposed_boundary_node_ids,
        actual_node_ids=tuple(
            reversed(product_fidelity.proposed_boundary_node_ids)
        ),
    ) == tuple(sorted(product_fidelity.proposed_boundary_node_ids))
    with pytest.raises(AiVideoError):
        validate_repair_scope(
            expected_node_ids=product_fidelity.proposed_boundary_node_ids,
            actual_node_ids=(
                *product_fidelity.proposed_boundary_node_ids,
                "creative:graphic:proof-07",
            ),
        )


def _interaction_projection(
    *,
    source_plan_shot_id: str,
    target_shot_id: str,
) -> production.CommercialExecutionProjection:
    source = next(
        item
        for item in production.project_commercial_executions(_commercial_plan())
        if item.target_shot_id == source_plan_shot_id
    )
    payload = source.model_dump(mode="python", exclude={"projection_hash"})
    payload.update(
        target_shot_id=target_shot_id,
        scene_requirement_fingerprint=canonical_sha256(
            {"shot_id": target_shot_id, "dimension": "scene"}
        ),
        wardrobe_requirement_fingerprint=canonical_sha256(
            {"shot_id": target_shot_id, "dimension": "wardrobe"}
        ),
        accessory_requirement_fingerprint=canonical_sha256(
            {"shot_id": target_shot_id, "dimension": "accessory"}
        ),
    )
    payload["projection_hash"] = canonical_sha256(payload)
    return production.CommercialExecutionProjection.model_validate(payload)


def _approved_commercial_project(root, *, source_plan_shot_id: str):
    reference_set, import_receipt = _make_commercial_state_project(root)
    committer = ProductionStateCommitter(
        root,
        commercial_source_review_authorizer=_review_authorizer,
    )
    initial = load_production_project(root / "project.yaml").manifest
    with_policy = committer.activate_qa_policy(
        _commercial_policy(),
        expected_manifest_revision=initial.manifest_revision,
        attempt_id="activate-commercial-e2e-policy",
    )
    committer.upgrade_manifest_schema(
        "2.12",
        expected_manifest_revision=with_policy.manifest_revision,
    )
    loaded = load_production_project(root / "project.yaml")
    projection = _interaction_projection(
        source_plan_shot_id=source_plan_shot_id,
        target_shot_id=loaded.shots[0].shot_id,
    )
    request = _state_request(root, reference_set, projection=projection)
    committer.begin_commercial_source_preparation(request)
    loaded = load_production_project(root / "project.yaml")
    asset = next(
        item
        for item in loaded.registry.assets
        if item.asset_id == import_receipt.output_asset_id
    )
    image_bytes = loaded.asset_paths[asset.asset_id].read_bytes()
    candidate = _candidate(
        request,
        asset_id=asset.asset_id,
        asset_sha256=asset.sha256,
        size_bytes=len(image_bytes),
        width=asset.width,
        height=asset.height,
        import_receipt=import_receipt,
    )
    committer.record_commercial_source_candidate(request, candidate)
    _, receipt = _review_candidate(
        committer,
        request,
        candidate,
        evidence_id=f"commercial-source-review-{source_plan_shot_id}",
    )
    binding = production.ApprovedCommercialSourceBinding.create(
        approval_id=f"approved-commercial-source-{source_plan_shot_id}",
        ad_creative_plan_hash=projection.ad_creative_plan_hash,
        execution_projection_hash=projection.projection_hash,
        product_reference_set=reference_set,
        character_references=request.character_references,
        scene_references=request.scene_references,
        wardrobe_requirement_hash=projection.wardrobe_requirement_fingerprint,
        accessory_requirement_hash=projection.accessory_requirement_fingerprint,
        candidate=candidate,
        review_receipt=receipt,
    )
    committer.approve_commercial_source(request, binding)
    return load_production_project(root / "project.yaml"), projection, binding


def _base_commercial_planning_request(loaded) -> VideoPlanningRequest:
    target_shot = loaded.shots[0]
    scene = next(item for item in loaded.scenes if item.scene_id == target_shot.scene_id)
    intent = ProviderNeutralGenerationIntentProjection.create(
        generation_intent=GenerationIntent(
            subject_action=SubjectAction(
                start_state="holds the approved Qingyan source pose",
                progression="raises the spray bottle toward the underarm",
            ),
            motion_envelope=MotionEnvelope(
                onset="gentle",
                peak="controlled product interaction",
                settle="product label remains visible",
            ),
        ),
        output_need=OutputNeed(
            duration_seconds=4,
            width=1024,
            height=576,
            fps=24,
            container_mime="video/mp4",
        ),
        audio_need=AudioNeed.FORBIDDEN,
        quality_need=production.QualityNeed(objective_tier="production"),
    )
    return VideoPlanningRequest.create(
        request_id=f"commercial-planning-{target_shot.shot_id}",
        target_shot=target_shot,
        character_context=(loaded.characters[0],),
        scene_context=scene,
        available_assets=(),
        previous_shot_state=None,
        shot_intent_evidence=ShotIntentEvidence(
            target_shot_id=target_shot.shot_id,
            target_shot_content_hash=target_shot.content_hash,
            character_action_required=True,
            subject_motion_directive_present=True,
        ),
        review_decision=None,
        production_policy=ProductionPolicyInput(
            local_resources_available=True,
            remote_authorized=False,
            budget_authorized=False,
        ),
        generation_intent=intent,
        planning_contract_version="video-planner/3",
    )


@pytest.mark.parametrize("source_plan_shot_id", ("shot-03", "shot-04"))
def test_offline_qingyan_approved_source_routes_exact_i2v_and_compiles_product_fidelity(
    tmp_path,
    source_plan_shot_id: str,
) -> None:
    loaded, projection, _ = _approved_commercial_project(
        tmp_path,
        source_plan_shot_id=source_plan_shot_id,
    )
    selected_shot = loaded.shots[0]
    selected_scene = next(
        item for item in loaded.scenes if item.scene_id == selected_shot.scene_id
    )
    selected_approval = next(
        item
        for item in loaded.manifest.active_commercial_source_approvals
        if item.target_shot_id == selected_shot.shot_id
    )
    selected_asset = next(
        item
        for item in loaded.registry.assets
        if item.asset_id
        == loaded.manifest.commercial_source_attempts[0].candidate_asset_id
    )
    keyframe = _router_asset(
        "first_frame",
        selected_asset.asset_id,
        selected_asset.sha256,
    ).model_copy(update={"asset_id": selected_asset.asset_id})
    character_references = tuple(
        _router_asset(
            "character_reference",
            character.character_id,
            character.content_hash,
            canonical_owner_id=character.character_id,
            canonical_owner_content_hash=character.content_hash,
        )
        for character in loaded.characters
        if character.character_id in selected_shot.character_ids
    )
    scene_reference = _router_asset(
        "scene_reference",
        selected_scene.scene_id,
        selected_scene.content_hash,
        canonical_owner_id=selected_scene.scene_id,
        canonical_owner_content_hash=selected_scene.content_hash,
    )
    context = _context(
        shot_id=selected_shot.shot_id,
        scene_id=selected_shot.scene_id,
        important=True,
        keyframe=keyframe,
        important_character_ids=selected_shot.character_ids,
        character_bible_hashes=tuple(
            character.content_hash
            for character in loaded.characters
            if character.character_id in selected_shot.character_ids
        ),
        character_references=character_references,
        scene_reference=scene_reference,
        scene_content_hash=selected_scene.content_hash,
        motion=MotionRequirement.CHARACTER_ACTION,
    )
    context = type(context).model_validate(
        context.model_copy(
            update={
                "activated_shot": selected_shot,
                "target_shot_id": selected_shot.shot_id,
                "target_shot_revision": selected_shot.revision,
                "target_shot_content_hash": selected_shot.content_hash,
                "selected_registry_revision_id": loaded.registry.revision_id,
                "character_bible_content_hashes": (
                    loaded.characters[0].content_hash,
                ),
                "scene_content_hash": selected_scene.content_hash,
                "canonical_character_references": tuple(
                    item.model_copy(
                        update={
                            "source_registry_revision_id": loaded.registry.revision_id
                        }
                    )
                    for item in character_references
                ),
                "canonical_scene_reference": scene_reference.model_copy(
                    update={
                        "source_registry_revision_id": loaded.registry.revision_id
                    }
                ),
                "shot_keyframe": keyframe.model_copy(
                    update={
                        "source_registry_revision_id": loaded.registry.revision_id
                    }
                ),
            }
        ).model_dump(mode="python")
    )
    request = planning.build_commercial_video_planning_request(
        base_request=_base_commercial_planning_request(loaded),
        execution_projection=projection,
        loaded_project=loaded,
    )
    approval = request.approved_commercial_source
    assert approval is not None
    assert request.active_commercial_source_approval == selected_approval

    plan = VideoPlanner().plan(request)
    verified = require_current_video_plan(current_request=request, plan=plan)
    requirement = verified.requirement

    assert plan.outcome is PlanOutcome.PROPOSED
    assert requirement.contract_version == "provider-neutral-video-requirement/3"
    assert requirement.commercial_execution_class == "product_interaction"
    assert requirement.capability_need.needs_product_fidelity is True
    assert requirement.product_fidelity_requirement.product_id == "qingyan-spray"
    assert requirement.asset_evidence[0].asset_id == approval.keyframe_asset_id
    assert tuple(item.asset_id for item in requirement.asset_evidence) == (
        approval.keyframe_asset_id,
    )

    compiler = AdapterCompilerContract.create(
        compiler_id="offline-commercial-video-compiler",
        compiler_version="1",
    )
    assert loaded.manifest.active_dependency_graph is not None
    lifecycle = type(_lifecycle(context)).model_validate(
        _lifecycle(context).model_copy(
            update={
                "base_project": loaded.manifest.active_project,
                "base_registry": loaded.manifest.active_registry,
                "base_dependency_graph": loaded.manifest.active_dependency_graph,
                "input_artifact_ids": (
                    context.target_shot_id,
                    approval.keyframe_asset_id,
                ),
            }
        ).model_dump(mode="python")
    )
    selected = VideoGenerationResolver().resolve_requirement(
        projection=verified,
        context=context,
        policy=_routing_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.IMAGE_TO_VIDEO)),
        selected_capability_id="capability-image_to_video",
        output_requirement=_output(),
        lifecycle=lifecycle,
        compiler_contract=compiler,
    )
    denied_t2v = VideoGenerationResolver().resolve_requirement(
        projection=verified,
        context=context,
        policy=_routing_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.TEXT_TO_VIDEO)),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
        lifecycle=lifecycle,
        compiler_contract=compiler,
    )

    assert selected.decision.outcome is RoutingOutcome.SELECTED
    assert selected.provider_bound_request is not None
    assert selected.provider_bound_request.binding_roles == ("first_frame",)
    assert denied_t2v.decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY

    compiled = compile_provider_video_request(
        provider_bound=selected.provider_bound_request,
        requirement=requirement,
        compiler_id=compiler.compiler_id,
        compiler_version=compiler.compiler_version,
        capabilities=_capabilities(_variant(VideoGenerationMode.IMAGE_TO_VIDEO)),
    )

    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert "product_id=qingyan-spray" in compiled.provider_native_prompt
    assert "product_source_asset_hashes=" in compiled.provider_native_prompt
    assert tuple(item.asset_id for item in compiled.request.image_bindings) == (
        approval.keyframe_asset_id,
    )


def test_product_reference_change_invalidates_only_source_and_generated_shot_chain(
    tmp_path,
) -> None:
    _, _, approval = _approved_commercial_project(
        tmp_path,
        source_plan_shot_id="shot-04",
    )
    reference_set = approval.product_reference_set
    unrelated = DependencyNode(
        node_id="creative:graphic:proof-07",
        kind=DependencyNodeKind.CREATIVE_ARTIFACT,
        semantic_role=DependencySemanticRole.NONE,
        artifact_id="proof-07",
        artifact_revision=1,
        contributions=(
            FingerprintContribution(key="graphic", fingerprint="8" * 64),
        ),
    )
    registered_assets = tuple(
        DependencyNode(
            node_id=dependency.asset_node_id(asset_id),
            kind=DependencyNodeKind.ASSET,
            semantic_role=DependencySemanticRole.VISUAL,
            artifact_id=asset_id,
            contributions=(
                FingerprintContribution(
                    key="registered_asset",
                    fingerprint=digest,
                ),
            ),
        )
        for asset_id, digest in (
            *(
                (item.asset_id, item.asset_sha256)
                for item in reference_set.assets
            ),
            (approval.keyframe_asset_id, approval.keyframe_sha256),
            ("generated-shot-04", "9" * 64),
        )
    )
    base = dependency.build_dependency_graph(
        (unrelated, *registered_assets), ()
    )
    first = production.extend_commercial_source_dependency_graph(
        base,
        product_reference_set=reference_set,
        keyframe_asset_id=approval.keyframe_asset_id,
        keyframe_sha256=approval.keyframe_sha256,
        generated_shot_asset_id="generated-shot-04",
        generated_shot_fingerprint="9" * 64,
    )
    changed_values = reference_set.model_dump(
        mode="python", exclude={"content_hash"}
    )
    changed_values["dominant_color"] = "tampered black"
    changed_reference_set = production.ProductReferenceSet.create(**changed_values)
    second = production.extend_commercial_source_dependency_graph(
        base,
        product_reference_set=changed_reference_set,
        keyframe_asset_id=approval.keyframe_asset_id,
        keyframe_sha256=approval.keyframe_sha256,
        generated_shot_asset_id="generated-shot-04",
        generated_shot_fingerprint="9" * 64,
    )

    first_desired = dependency.desired_fingerprints(first)
    second_desired = dependency.desired_fingerprints(second)

    assert first_desired["creative:graphic:proof-07"] == second_desired[
        "creative:graphic:proof-07"
    ]
    keyframe_node_id = dependency.asset_node_id(approval.keyframe_asset_id)
    assert first_desired[keyframe_node_id] != second_desired[
        keyframe_node_id
    ]
    assert first_desired["asset:generated-shot-04"] != second_desired[
        "asset:generated-shot-04"
    ]


def test_commercial_handoff_rejects_duplicate_approval_cardinality(tmp_path) -> None:
    _, projection, durable_approval = _approved_commercial_project(
        tmp_path,
        source_plan_shot_id="shot-04",
    )

    with pytest.raises(ValueError, match="unique"):
        production.CompiledAdCreativeHandoff(
            plan_id=projection.ad_creative_plan_id,
            plan_content_hash=projection.ad_creative_plan_hash,
            shot_proposals=(
                production.AdShotProposal(
                    shot_id=projection.target_shot_id,
                    beat_ids=("beat-04",),
                ),
            ),
            composition_requirements=production.AdCompositionRequirements(),
            composition_spec=make_composition_spec(
                shot_ids=(projection.target_shot_id,)
            ),
            commercial_execution_projections=(projection,),
            approved_commercial_sources=(durable_approval, durable_approval),
        )


def test_product_interaction_nonpass_stops_at_sequential_coordinator(
    tmp_path,
) -> None:
    _, projection, durable_approval = _approved_commercial_project(
        tmp_path,
        source_plan_shot_id="shot-04",
    )
    handoff = production.CompiledAdCreativeHandoff(
        plan_id=projection.ad_creative_plan_id,
        plan_content_hash=projection.ad_creative_plan_hash,
        shot_proposals=(
            production.AdShotProposal(
                shot_id=projection.target_shot_id,
                beat_ids=("beat-04",),
            ),
        ),
        composition_requirements=production.AdCompositionRequirements(),
        composition_spec=make_composition_spec(
            shot_ids=(projection.target_shot_id,)
        ),
        commercial_execution_projections=(projection,),
        approved_commercial_sources=(durable_approval,),
    )
    facade = _Facade(
        projection.target_shot_id,
        projection.projection_hash,
        verdict=QaVerdict.FAIL,
    )

    result = production.run_ecommerce_ad_generation(
        handoff,
        facades={projection.target_shot_id: facade},
    )

    assert result.stop_reason is production.EcommerceStopReason.SHOT_NOT_PASS
    assert "activate" not in facade.effects

    plan = _commercial_plan()
    interaction_projections = tuple(
        item
        for item in production.project_commercial_executions(plan)
        if item.primary_class is production.CommercialShotClass.PRODUCT_INTERACTION
    )

    def approval_for(
        interaction: production.CommercialExecutionProjection,
    ) -> production.ApprovedCommercialSourceBinding:
        request_hash = canonical_sha256(
            {"plan": plan.content_hash, "projection": interaction.projection_hash}
        )
        observed_by = ActorIdentity(
            actor_id="commercial-cardinality-test-observer",
            actor_kind="human",
        )
        import_receipt = production.CommercialImageImportReceipt.create(
            source_kind="human_observed_import",
            original_filename=f"{interaction.target_shot_id}.png",
            output_asset_id=f"keyframe-{interaction.target_shot_id}",
            output_sha256=canonical_sha256(
                {"keyframe": interaction.target_shot_id}
            ),
            output_size_bytes=1,
            output_width=1,
            output_height=1,
            imported_at="2026-08-25T10:00:00+08:00",
            prompt_fingerprint=canonical_sha256(
                {"prompt": interaction.target_shot_id}
            ),
            target_kind="commercial_interaction_keyframe",
            target_id=f"request-{interaction.target_shot_id}",
            product_reference_set=durable_approval.product_reference_set,
            product_reference_set_id=durable_approval.product_reference_set_id,
            product_reference_set_hash=durable_approval.product_reference_set_hash,
            product_reference_asset_hashes=(
                durable_approval.product_source_asset_hashes
            ),
            target_shot_id=interaction.target_shot_id,
            target_shot_content_hash=canonical_sha256(
                {"shot": interaction.target_shot_id}
            ),
            character_reference_ids=durable_approval.character_reference_ids,
            scene_reference_ids=durable_approval.scene_reference_ids,
            observed_by=observed_by,
            provenance_note="Synthetic exact approval cardinality fixture.",
            usage_license="test-only",
        )
        candidate = production.CommercialSourceCandidate(
            request_hash=request_hash,
            target_shot_id=interaction.target_shot_id,
            target_shot_content_hash=import_receipt.target_shot_content_hash,
            asset_id=import_receipt.output_asset_id,
            asset_sha256=import_receipt.output_sha256,
            import_receipt_hash=import_receipt.content_hash,
            import_receipt=import_receipt,
        )
        receipt = production.CommercialSourceReviewReceipt.create(
            review_intent_hash=canonical_sha256(
                {"review": interaction.projection_hash}
            ),
            source_request_hash=request_hash,
            target_shot_id=interaction.target_shot_id,
            target_shot_content_hash=candidate.target_shot_content_hash,
            candidate_asset_id=candidate.asset_id,
            candidate_sha256=candidate.asset_sha256,
            product_reference_set_hash=durable_approval.product_reference_set_hash,
            policy_hash="7" * 64,
            evidence_id=f"evidence-{interaction.target_shot_id}",
            evidence_hash=canonical_sha256(
                {"evidence": interaction.target_shot_id}
            ),
            observed_by=observed_by,
            authority=REVIEW_TOOL,
            verdict=production.QaVerdict.PASS,
            target_kind="source_image",
        )
        return production.ApprovedCommercialSourceBinding.create(
            approval_id=f"approval-{interaction.target_shot_id}",
            ad_creative_plan_hash=plan.content_hash,
            execution_projection_hash=interaction.projection_hash,
            product_reference_set=durable_approval.product_reference_set,
            character_references=durable_approval.character_references,
            scene_references=durable_approval.scene_references,
            wardrobe_requirement_hash=interaction.wardrobe_requirement_fingerprint,
            accessory_requirement_hash=interaction.accessory_requirement_fingerprint,
            candidate=candidate,
            review_receipt=receipt,
        )

    exact_approvals = tuple(approval_for(item) for item in interaction_projections)
    composition = make_composition_spec(
        shot_ids=("shot-03", "shot-04", "shot-06", "shot-07", "shot-08")
    )
    baseline = production.review_ad_creative_plan(
        plan,
        composition,
        approved_commercial_sources=exact_approvals,
    )
    duplicate = production.review_ad_creative_plan(
        plan,
        composition,
        approved_commercial_sources=(exact_approvals[0], exact_approvals[0]),
    )

    assert baseline.source_preparation_ready is True
    assert duplicate.source_preparation_ready is False
