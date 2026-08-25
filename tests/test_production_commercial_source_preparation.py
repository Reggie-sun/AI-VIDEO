from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

import ai_video.production as production

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.dependency import (
    build_applied_dependency_evidence,
    build_production_dependency_graph,
    asset_node_id,
    creative_node_id,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.models import (
    ActorIdentity,
    AssetType,
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    canonical_project_snapshot_path,
)
from ai_video.production.paths import canonical_dependency_graph_snapshot_path
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    _canonical_json_bytes,
    _canonical_yaml_bytes,
    prepare_dependency_graph_transition,
    prepare_project_registry_commit,
)
from ai_video.production._state_commit_common import _validated_transition
import production_project_factory as project_factory
from test_production_commercial_visual_review import REVIEW_TOOL, _policy


def _synthetic_reference_set() -> production.ProductReferenceSet:
    return production.ProductReferenceSet.create(
        artifact_id="product-reference-qingyan",
        revision=1,
        product_id="qingyan-spray",
        sku_id="qingyan-yellow-spray-50ml",
        formal_name="青颜净味喷雾",
        truth_reference_ids=("truth-packaging",),
        registry_revision_id="5" * 64,
        registry_content_hash="5" * 64,
        assets=(
            production.ProductReferenceAssetBinding(
                asset_id="product-front",
                asset_sha256="a" * 64,
                mime_type="image/png",
                width=2,
                height=1,
                view="front",
                purpose="product_truth",
            ),
            production.ProductReferenceAssetBinding(
                asset_id="product-label",
                asset_sha256="b" * 64,
                mime_type="image/png",
                width=2,
                height=1,
                view="label",
                purpose="label",
            ),
        ),
        packaging_form="yellow carton and spray bottle",
        bottle_silhouette="slender cylindrical bottle",
        dominant_color="qingyan yellow",
        cap_color="white",
        logo_label_identity="青颜 yellow label",
        protected_text_zones=("front-label",),
    )


def _creative_reference(artifact) -> production.CommercialCreativeReference:
    return production.CommercialCreativeReference(
        artifact_id=artifact.artifact_id,
        revision=artifact.revision,
        content_hash=artifact.content_hash,
    )


def _state_reference_set(loaded) -> production.ProductReferenceSet:
    image_assets = tuple(
        item
        for item in loaded.registry.assets
        if item.asset_type is AssetType.IMAGE
    )[:2]
    assert len(image_assets) == 2
    return production.ProductReferenceSet.create(
        artifact_id="product-reference-qingyan",
        revision=1,
        product_id="qingyan-spray",
        sku_id="qingyan-yellow-spray-50ml",
        formal_name="青颜净味喷雾",
        truth_reference_ids=("truth-packaging",),
        registry_revision_id=loaded.registry.revision_id,
        registry_content_hash=loaded.registry.content_hash,
        assets=tuple(
            production.ProductReferenceAssetBinding(
                asset_id=asset.asset_id,
                asset_sha256=asset.sha256,
                mime_type=asset.mime_type,
                width=asset.width,
                height=asset.height,
                view=view,
                purpose=purpose,
            )
            for asset, view, purpose in zip(
                image_assets,
                ("front", "label"),
                ("product_truth", "label"),
                strict=True,
            )
        ),
        packaging_form="yellow carton and spray bottle",
        bottle_silhouette="slender cylindrical bottle",
        dominant_color="qingyan yellow",
        cap_color="white",
        logo_label_identity="青颜 yellow label",
        protected_text_zones=("front-label",),
    )


def _make_commercial_state_project(root) -> tuple[
    production.ProductReferenceSet,
    production.CommercialImageImportReceipt,
]:
    inputs = project_factory.make_p5_dependency_inputs(root, decodable_pngs=True)
    project_payload = _canonical_yaml_bytes(inputs.project.project)
    project_path = canonical_project_snapshot_path(
        inputs.project.project.revision,
        inputs.project.project.content_hash,
    )
    (root / project_path).parent.mkdir(parents=True, exist_ok=True)
    (root / project_path).write_bytes(project_payload)
    project_pointer = ProjectSnapshotPointer(
        path=project_path,
        revision=inputs.project.project.revision,
        content_hash=inputs.project.project.content_hash,
        file_sha256=hashlib.sha256(project_payload).hexdigest(),
    )
    inputs = replace(
        inputs,
        project=inputs.project.model_copy(
            update={
                "manifest": inputs.project.manifest.model_copy(
                    update={"active_project": project_pointer}
                )
            }
        ),
    )
    initial_graph = build_production_dependency_graph(inputs)
    initial_states = resolve_dependency_state(
        initial_graph,
        build_applied_dependency_evidence(inputs, None),
    ).states
    initial_graph_payload = _canonical_json_bytes(initial_graph)
    initial_graph_path = canonical_dependency_graph_snapshot_path(
        initial_graph.revision_id
    )
    (root / initial_graph_path).parent.mkdir(parents=True, exist_ok=True)
    (root / initial_graph_path).write_bytes(initial_graph_payload)
    initial_pointer = DependencyGraphSnapshotPointer(
        revision_id=initial_graph.revision_id,
        content_hash=initial_graph.content_hash,
        path=initial_graph_path,
        file_sha256=hashlib.sha256(initial_graph_payload).hexdigest(),
    )
    initial_manifest = inputs.project.manifest.model_copy(
        update={
            "schema_version": "2.3",
            "manifest_revision": inputs.project.manifest.manifest_revision + 1,
            "active_dependency_graph": initial_pointer,
            "dependency_states": initial_states,
        }
    )
    (root / "state/manifest.json").write_text(
        initial_manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    base = load_production_project(root / "project.yaml")
    reference_set = _state_reference_set(base)
    image_bytes = project_factory._p7_png(rgba=b"\x31\x62\x93\xff")
    receipt = production.CommercialImageImportReceipt.create(
        source_kind="human_observed_import",
        original_filename="commercial-source.png",
        output_asset_id="commercial-interaction-keyframe",
        output_sha256=hashlib.sha256(image_bytes).hexdigest(),
        output_size_bytes=len(image_bytes),
        output_width=2,
        output_height=1,
        imported_at="2026-08-25T10:00:00+08:00",
        prompt_fingerprint=canonical_sha256({"fixture": "commercial-source"}),
        target_kind="commercial_interaction_keyframe",
        target_id="source-request-04",
        product_reference_set=reference_set,
        product_reference_set_id=reference_set.artifact_id,
        product_reference_set_hash=reference_set.content_hash,
        product_reference_asset_hashes=tuple(
            item.asset_sha256 for item in reference_set.assets
        ),
        target_shot_id=base.shots[0].shot_id,
        target_shot_content_hash=base.shots[0].content_hash,
        character_reference_ids=(base.characters[0].artifact_id,),
        scene_reference_ids=(base.scenes[0].artifact_id,),
        observed_by=ActorIdentity(
            actor_id="commercial-source-test-observer", actor_kind="human"
        ),
        provenance_note="Local registered PNG observed for test.",
        usage_license="test-only",
    )
    keyframe = production.commercial_image_import_asset(receipt)
    registry_draft = base.registry.model_copy(
        update={
            "revision_id": "0" * 64,
            "content_hash": "0" * 64,
            "assets": (*base.registry.assets, keyframe),
        }
    )
    registry_hash = registry_semantic_sha256(registry_draft)
    candidate_registry = registry_draft.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    registry_payload = _canonical_json_bytes(candidate_registry)
    registry_pointer = RegistrySnapshotPointer(
        path=base.manifest.active_registry.path.parent
        / f"registry.{registry_hash}.json",
        revision_id=registry_hash,
        content_hash=registry_hash,
        file_sha256=hashlib.sha256(registry_payload).hexdigest(),
    )
    candidate_loaded = base.model_copy(
        update={
            "registry": candidate_registry,
            "asset_paths": {
                **base.asset_paths,
                keyframe.asset_id: root / keyframe.artifact_path,
            },
            "manifest": base.manifest.model_copy(
                update={"active_registry": registry_pointer}
            ),
        }
    )
    candidate_inputs = replace(inputs, project=candidate_loaded)
    candidate_graph = build_production_dependency_graph(candidate_inputs)
    candidate_states = resolve_dependency_state(
        candidate_graph, base.manifest.dependency_states
    ).states
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=base.manifest.manifest_revision,
        base_dependency_graph=base.manifest.active_dependency_graph,
        candidate_graph=candidate_graph,
        candidate_dependency_states=candidate_states,
        expected_desired_fingerprints=desired_fingerprints(candidate_graph),
    )
    graph_payload = _canonical_json_bytes(candidate_graph)
    base_commit = prepare_project_registry_commit(
        manifest=base.manifest,
        project=base.project,
        registry=candidate_registry,
        attempt_id="commercial-keyframe-import",
    )
    base_commit = replace(
        base_commit,
        dependency_graph_transition=transition,
        artifacts=tuple(
            sorted(
                (
                    *base_commit.artifacts,
                    PreparedArtifact(
                        transition.candidate_dependency_graph.path,
                        graph_payload,
                        hashlib.sha256(graph_payload).hexdigest(),
                    ),
                ),
                key=lambda item: item.relative_path.as_posix(),
            )
        ),
    )
    request = production.prepare_commercial_image_import_commit(
        base=base,
        product_reference_set=reference_set,
        receipt=receipt,
        image_bytes=image_bytes,
        base_commit=base_commit,
    )
    ProductionStateCommitter(root).commit(request)
    return reference_set, receipt


def _candidate(
    request: production.CommercialSourcePreparationRequest,
    *,
    asset_id: str,
    asset_sha256: str,
    size_bytes: int = 1,
    width: int = 1,
    height: int = 1,
    import_receipt: production.CommercialImageImportReceipt | None = None,
) -> production.CommercialSourceCandidate:
    receipt = import_receipt or production.CommercialImageImportReceipt.create(
        source_kind="human_observed_import",
        original_filename="commercial-source.png",
        output_asset_id=asset_id,
        output_sha256=asset_sha256,
        output_size_bytes=size_bytes,
        output_width=width,
        output_height=height,
        imported_at="2026-08-25T10:00:00+08:00",
        prompt_fingerprint=canonical_sha256(
            {"request": request.request_fingerprint, "asset": asset_id}
        ),
        target_kind="commercial_interaction_keyframe",
        target_id=request.request_id,
        product_reference_set=request.product_reference_set,
        product_reference_set_id=request.product_reference_set_id,
        product_reference_set_hash=request.product_reference_set_hash,
        product_reference_asset_hashes=request.product_reference_asset_hashes,
        target_shot_id=request.target_shot_id,
        target_shot_content_hash=request.target_shot_content_hash,
        character_reference_ids=request.character_reference_ids,
        scene_reference_ids=request.scene_reference_ids,
        observed_by=ActorIdentity(
            actor_id="commercial-source-test-observer", actor_kind="human"
        ),
        provenance_note="Local registered PNG observed for test.",
        usage_license="test-only",
    )
    return production.CommercialSourceCandidate(
        request_hash=request.request_fingerprint,
        target_shot_id=request.target_shot_id,
        target_shot_content_hash=request.target_shot_content_hash,
        asset_id=asset_id,
        asset_sha256=asset_sha256,
        import_receipt_hash=receipt.content_hash,
        import_receipt=receipt,
    )


def test_generation_lane_blocks_before_effect_without_product_aware_capability() -> None:
    reference_set = _synthetic_reference_set()
    request = production.CommercialSourcePreparationRequest.create(
        request_id="source-request-04",
        attempt_id="source-attempt-04",
        acquisition_kind=production.CommercialSourceAcquisitionKind.P7_GENERATION,
        ad_creative_plan_id="ad-plan-qingyan",
        ad_creative_plan_hash="1" * 64,
        execution_projection_hash="2" * 64,
        target_shot_id="shot-04",
        target_shot_revision=1,
        target_shot_content_hash="3" * 64,
        base_project_content_hash="4" * 64,
        base_registry_revision_id="5" * 64,
        base_registry_content_hash="5" * 64,
        base_dependency_graph_content_hash="6" * 64,
        product_reference_set=reference_set,
        character_references=(
            production.CommercialCreativeReference(
                artifact_id="character-qingyan", revision=1, content_hash="c" * 64
            ),
        ),
        scene_references=(
            production.CommercialCreativeReference(
                artifact_id="scene-bedroom", revision=1, content_hash="d" * 64
            ),
        ),
        wardrobe_requirement_hash="8" * 64,
        accessory_requirement_hash="9" * 64,
    )
    effects = 0

    def forbidden_effect(_: production.CommercialSourcePreparationRequest) -> None:
        nonlocal effects
        effects += 1

    coordinator = production.CommercialSourcePreparationCoordinator(
        generated_materializer=forbidden_effect,
        product_aware_generation_capability=False,
    )

    with pytest.raises(AiVideoError) as caught:
        coordinator.prepare(request)

    assert caught.value.code is ErrorCode.PLANNING_PREFLIGHT_BLOCKED
    assert effects == 0


def test_approved_binding_requires_exact_pass_receipt() -> None:
    reference_set = _synthetic_reference_set()
    request = production.CommercialSourcePreparationRequest.create(
        request_id="source-request-04",
        attempt_id="source-attempt-04",
        acquisition_kind=production.CommercialSourceAcquisitionKind.REGISTERED_IMPORT,
        ad_creative_plan_id="ad-plan-qingyan",
        ad_creative_plan_hash="1" * 64,
        execution_projection_hash="2" * 64,
        target_shot_id="shot-04",
        target_shot_revision=1,
        target_shot_content_hash="2" * 64,
        base_project_content_hash="4" * 64,
        base_registry_revision_id="5" * 64,
        base_registry_content_hash="5" * 64,
        base_dependency_graph_content_hash="6" * 64,
        product_reference_set=reference_set,
        character_references=(
            production.CommercialCreativeReference(
                artifact_id="character-qingyan", revision=1, content_hash="c" * 64
            ),
        ),
        scene_references=(
            production.CommercialCreativeReference(
                artifact_id="scene-bedroom", revision=1, content_hash="d" * 64
            ),
        ),
        wardrobe_requirement_hash="8" * 64,
        accessory_requirement_hash="9" * 64,
    )
    candidate = _candidate(
        request,
        asset_id="interaction-keyframe-04",
        asset_sha256="3" * 64,
    )
    receipt = production.CommercialSourceReviewReceipt.create(
        source_request_hash="1" * 64,
        target_shot_id="shot-04",
        target_shot_content_hash="2" * 64,
        candidate_asset_id="interaction-keyframe-04",
        candidate_sha256="3" * 64,
        product_reference_set_hash="6" * 64,
        policy_hash="7" * 64,
        evidence_id="commercial-evidence-not-evaluated",
        evidence_hash="8" * 64,
        authority=REVIEW_TOOL,
        verdict=production.QaVerdict.NOT_EVALUATED,
        target_kind="source_image",
    )

    with pytest.raises(ValueError, match="PASS"):
        production.ApprovedCommercialSourceBinding.create(
            approval_id="approved-source-04",
            ad_creative_plan_hash="8" * 64,
            execution_projection_hash="9" * 64,
            product_reference_set=reference_set,
            character_references=request.character_references,
            scene_references=request.scene_references,
            wardrobe_requirement_hash="a" * 64,
            accessory_requirement_hash="b" * 64,
            candidate=candidate,
            review_receipt=receipt,
        )


def _state_request(
    root,
    reference_set: production.ProductReferenceSet,
    *,
    projection: production.CommercialExecutionProjection | None = None,
) -> production.CommercialSourcePreparationRequest:
    loaded = load_production_project(root / "project.yaml")
    assert loaded.manifest.active_dependency_graph is not None
    target_shot = loaded.shots[0]
    if projection is not None and projection.target_shot_id != target_shot.shot_id:
        raise ValueError("Test projection must target the active fixture Shot")
    return production.CommercialSourcePreparationRequest.create(
        request_id="source-request-04",
        attempt_id="source-attempt-04",
        acquisition_kind=production.CommercialSourceAcquisitionKind.REGISTERED_IMPORT,
        ad_creative_plan_id=(
            projection.ad_creative_plan_id
            if projection is not None
            else "ad-plan-qingyan"
        ),
        ad_creative_plan_hash=(
            projection.ad_creative_plan_hash
            if projection is not None
            else "1" * 64
        ),
        execution_projection_hash=(
            projection.projection_hash if projection is not None else "2" * 64
        ),
        target_shot_id=target_shot.shot_id,
        target_shot_revision=target_shot.revision,
        target_shot_content_hash=target_shot.content_hash,
        base_project_content_hash=loaded.project.content_hash,
        base_registry_revision_id=loaded.registry.revision_id,
        base_registry_content_hash=loaded.registry.content_hash,
        base_dependency_graph_content_hash=loaded.dependency_graph.content_hash,
        product_reference_set=reference_set,
        character_references=(_creative_reference(loaded.characters[0]),),
        scene_references=(_creative_reference(loaded.scenes[0]),),
        wardrobe_requirement_hash=(
            projection.wardrobe_requirement_fingerprint
            if projection is not None
            else "8" * 64
        ),
        accessory_requirement_hash=(
            projection.accessory_requirement_fingerprint
            if projection is not None
            else "9" * 64
        ),
    )


def test_committer_records_registered_candidate_and_exact_replay_without_revision_change(
    tmp_path,
) -> None:
    reference_set, import_receipt = _make_commercial_state_project(tmp_path)
    committer = ProductionStateCommitter(tmp_path)
    initial = load_production_project(tmp_path / "project.yaml").manifest
    upgraded = committer.upgrade_manifest_schema(
        "2.12", expected_manifest_revision=initial.manifest_revision
    )
    request = _state_request(tmp_path, reference_set)
    loaded = load_production_project(tmp_path / "project.yaml")
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
    assert hashlib.sha256(image_bytes).hexdigest() == asset.sha256

    requested = committer.begin_commercial_source_preparation(request)
    materialized = committer.record_commercial_source_candidate(request, candidate)
    replay = committer.record_commercial_source_candidate(request, candidate)

    assert requested.manifest_revision == upgraded.manifest_revision + 1
    assert materialized.manifest_revision == requested.manifest_revision + 1
    assert replay.manifest_revision == materialized.manifest_revision
    state = replay.commercial_source_attempts[0]
    assert state.lifecycle is production.CommercialSourceLifecycle.MATERIALIZED_CANDIDATE
    assert state.candidate_asset_id == asset.asset_id


def test_committer_rejects_unregistered_or_wrong_candidate_bytes_before_state_change(
    tmp_path,
) -> None:
    reference_set, _ = _make_commercial_state_project(tmp_path)
    committer = ProductionStateCommitter(tmp_path)
    initial = load_production_project(tmp_path / "project.yaml").manifest
    with_policy = committer.activate_qa_policy(
        _policy(),
        expected_manifest_revision=initial.manifest_revision,
        attempt_id="activate-commercial-source-policy",
    )
    committer.upgrade_manifest_schema(
        "2.12", expected_manifest_revision=with_policy.manifest_revision
    )
    request = _state_request(tmp_path, reference_set)
    committer.begin_commercial_source_preparation(request)
    before = load_production_project(tmp_path / "project.yaml").manifest
    candidate = _candidate(
        request,
        asset_id="unregistered-candidate",
        asset_sha256="f" * 64,
    )

    with pytest.raises(AiVideoError) as caught:
        committer.record_commercial_source_candidate(request, candidate)

    assert caught.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert load_production_project(tmp_path / "project.yaml").manifest == before


def test_commercial_source_explicit_reopen_verifies_all_durable_bytes(tmp_path) -> None:
    reference_set, import_receipt = _make_commercial_state_project(tmp_path)
    committer = ProductionStateCommitter(tmp_path)
    initial = load_production_project(tmp_path / "project.yaml").manifest
    with_policy = committer.activate_qa_policy(
        _policy(),
        expected_manifest_revision=initial.manifest_revision,
        attempt_id="activate-commercial-source-policy",
    )
    committer.upgrade_manifest_schema(
        "2.12", expected_manifest_revision=with_policy.manifest_revision
    )
    request = _state_request(tmp_path, reference_set)
    committer.begin_commercial_source_preparation(request)
    loaded = load_production_project(tmp_path / "project.yaml")
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
    committed = committer.record_commercial_source_candidate(request, candidate)

    reopened = committer.recover_commercial_source_attempt(request.attempt_id)

    assert reopened == committed.commercial_source_attempts[0]
    assert load_production_project(tmp_path / "project.yaml").manifest == committed

    (tmp_path / reopened.request_path).write_text("{}", encoding="utf-8")
    with pytest.raises(AiVideoError) as load_caught:
        load_production_project(tmp_path / "project.yaml")
    assert load_caught.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    with pytest.raises(AiVideoError) as caught:
        committer.recover_commercial_source_attempt(request.attempt_id)
    assert caught.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_only_exact_semantic_pass_is_selected_and_approval_replay_is_zero_write(
    tmp_path,
) -> None:
    reference_set, import_receipt = _make_commercial_state_project(tmp_path)
    committer = ProductionStateCommitter(tmp_path)
    initial = load_production_project(tmp_path / "project.yaml").manifest
    with_policy = committer.activate_qa_policy(
        _policy(),
        expected_manifest_revision=initial.manifest_revision,
        attempt_id="activate-commercial-source-policy",
    )
    committer.upgrade_manifest_schema(
        "2.12", expected_manifest_revision=with_policy.manifest_revision
    )
    request = _state_request(tmp_path, reference_set)
    committer.begin_commercial_source_preparation(request)
    loaded = load_production_project(tmp_path / "project.yaml")
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
    evidence = production.CommercialVisualEvidence.create(
        evidence_id="commercial-evidence-04",
        source_request_hash=request.request_fingerprint,
        target_shot_id=request.target_shot_id,
        target_shot_content_hash=request.target_shot_content_hash,
        candidate_asset_id=candidate.asset_id,
        candidate_sha256=candidate.asset_sha256,
        product_reference_set_hash=request.product_reference_set_hash,
        policy_hash=_policy().content_hash,
        authority_kind="human",
        tool_identity=REVIEW_TOOL,
        measurements=tuple(
            production.CommercialVisualMeasurement(
                dimension=dimension,
                status=production.CommercialMatchStatus.MATCH,
                expected=f"expected-{dimension.value}",
                observed=f"observed-{dimension.value}",
                confidence_milli=950,
                rationale="exact human source-image observation",
            )
            for dimension in production.CommercialVisualDimension
        ),
    )
    receipt = production.adjudicate_commercial_visual_evidence(
        evidence,
        policy=_policy(),
    )
    evidenced = committer.record_commercial_source_review(
        request, candidate, evidence, receipt
    )
    binding = production.ApprovedCommercialSourceBinding.create(
        approval_id="approved-source-04",
        ad_creative_plan_hash=request.ad_creative_plan_hash,
        execution_projection_hash=request.execution_projection_hash,
        product_reference_set=request.product_reference_set,
        character_references=request.character_references,
        scene_references=request.scene_references,
        wardrobe_requirement_hash=request.wardrobe_requirement_hash,
        accessory_requirement_hash=request.accessory_requirement_hash,
        candidate=candidate,
        review_receipt=receipt,
    )

    approved = committer.approve_commercial_source(request, binding)
    replay = committer.approve_commercial_source(request, binding)
    request_replay = committer.begin_commercial_source_preparation(request)
    candidate_replay = committer.record_commercial_source_candidate(
        request, candidate
    )
    review_replay = committer.record_commercial_source_review(
        request, candidate, evidence, receipt
    )

    assert evidenced.commercial_source_attempts[0].lifecycle is production.CommercialSourceLifecycle.EVIDENCED
    assert approved.commercial_source_attempts[0].lifecycle is production.CommercialSourceLifecycle.APPROVED
    assert approved.active_commercial_source_approvals[0].content_hash == binding.content_hash
    assert approved.active_dependency_graph != evidenced.active_dependency_graph
    production.validate_commercial_source_dependency_graph(
        load_production_project(tmp_path / "project.yaml").dependency_graph,
        product_reference_set=reference_set,
        keyframe_asset_id=candidate.asset_id,
        keyframe_sha256=candidate.asset_sha256,
    )
    states = {item.node_id: item for item in approved.dependency_states}
    product_state = states[
        creative_node_id("product-reference-set", reference_set.artifact_id)
    ]
    keyframe_state = states[asset_node_id(candidate.asset_id)]
    assert product_state.lifecycle is production.DependencyLifecycle.FRESH
    assert keyframe_state.lifecycle is production.DependencyLifecycle.FRESH
    assert product_state.applied_evidence.owner == "commercial_source_approval"
    assert keyframe_state.applied_evidence.owner == "commercial_source_approval"
    assert replay.manifest_revision == approved.manifest_revision
    assert request_replay.manifest_revision == approved.manifest_revision
    assert candidate_replay.manifest_revision == approved.manifest_revision
    assert review_replay.manifest_revision == approved.manifest_revision

    changed_registry = RegistrySnapshotPointer(
        path=approved.active_registry.path.parent / f"registry.{'f' * 64}.json",
        revision_id="f" * 64,
        content_hash="f" * 64,
        file_sha256="e" * 64,
    )
    invalidated = _validated_transition(
        approved,
        {
            "manifest_revision": approved.manifest_revision + 1,
            "active_registry": changed_registry,
        },
    )
    assert invalidated.active_commercial_source_approvals == ()
    assert invalidated.commercial_source_attempts[0].lifecycle is (
        production.CommercialSourceLifecycle.STALE
    )
    assert invalidated.commercial_source_attempts[0].active_approval is None

    approval_path = tmp_path / approved.active_commercial_source_approvals[0].path
    approval_payload = approval_path.read_bytes()
    approval_path.write_text("{}", encoding="utf-8")
    with pytest.raises(AiVideoError) as caught:
        load_production_project(tmp_path / "project.yaml")
    assert caught.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    approval_path.write_bytes(approval_payload)

    current_policy = _policy()
    rotated_policy = seal_artifact(
        current_policy.model_copy(
            update={
                "revision": current_policy.revision + 1,
                "content_hash": "0" * 64,
                "policy_version": "2",
            }
        )
    )
    policy_invalidated = committer.activate_qa_policy(
        rotated_policy,
        expected_manifest_revision=approved.manifest_revision,
        attempt_id="rotate-commercial-source-policy",
    )
    assert policy_invalidated.active_commercial_source_approvals == ()
    assert policy_invalidated.commercial_source_attempts[0].lifecycle is (
        production.CommercialSourceLifecycle.STALE
    )
    assert policy_invalidated.commercial_source_attempts[0].active_approval is None
