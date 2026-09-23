from __future__ import annotations

import json
import hashlib
import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import production_project_factory as project_factory
import pytest
from ecommerce_job_factory import make_ecommerce_handoff
from production_project_factory import make_composition_spec
from test_production_ecommerce_job_assembly import _plan_and_handoff
from test_production_ecommerce_post_media_e2e import _passing_payload
from test_production_ecommerce_post_media_e2e import TOOL as REVIEW_TOOL
from test_production_hyperframes import (
    FakeRunner,
    _CountingRenderCommitter,
    _Manifest25RenderFixture,
    _write_executable,
)
from test_production_review import _Manifest25ReviewFixture
from test_production_review import make_manifest_25_passing_review_fixture

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.ad_creative import (
    compile_ad_creative_handoff,
    create_ad_creative_plan,
)
from ai_video.production.artifact_contracts import SourceReference
from ai_video.production.composition import resolve_composition
from ai_video.production.dependency import (
    ProductionDependencyInputs,
    build_production_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.delivery_packager import (
    inspect_ecommerce_delivery,
    package_ecommerce_delivery,
)
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.ecommerce_ad_coordinator import (
    close_ecommerce_post_media_candidate,
)
from ai_video.production.ecommerce_job_compiler import (
    bootstrap_ecommerce_production_project,
    compile_ecommerce_production_handoff,
)
from ai_video.production.ecommerce_job_contracts import (
    EcommerceAssetRequirement,
    EcommerceLayoutPlan,
    EcommerceProductionCompileProfile,
    EcommerceProductionHandoff,
)
from ai_video.production.ecommerce_media_acceptance import (
    create_qingyan_ecommerce_acceptance_profile,
)
from ai_video.production.ecommerce_quality_gate import (
    EcommerceWholeAdEvaluationPayload,
)
from ai_video.production.final_output_contracts import (
    FinalOutputContract,
    FinalOutputRequirement,
)
from ai_video.production.final_output_review import (
    FinalOutputFinding,
    FinalOutputObservation,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetRoleRequirement,
    AssetSourceKind,
    AssetType,
    AudioKind,
    AudioTrackSpec,
    DeliveryProfile,
    EgressMetadata,
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    QaVerdict,
    RendererIdentity,
    RendererKind,
    RendererSelectionReceipt,
    ToolIdentity,
    VisualStrategy,
)
from ai_video.production.paths import canonical_image_asset_path
from ai_video.production.project import load_production_project
from ai_video.production.quality_gate_coordinator import (
    UniversalHardCheck,
    UniversalQaApplicability,
    UniversalQaCheckOutcome,
    UniversalQaProfile,
)
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import (
    BeginRenderAttemptRequest,
    PreparedArtifact,
    ProductionStateCommitter,
    prepare_dependency_graph_transition,
)


EXPORTED_AT = "2026-09-19T12:00:00+00:00"
PACKAGER = ToolIdentity(name="ecommerce-delivery-packager", version="1")


def _mismatched_identities():
    return _plan_and_handoff()


def _identities():
    product_bytes = project_factory._p7_png()
    product_hash = hashlib.sha256(product_bytes).hexdigest()
    final_bytes = project_factory._p7_png(rgba=b"\x20\x40\x60\xff")
    final_hash = hashlib.sha256(final_bytes).hexdigest()
    product_asset_id = "asset-product-test"
    final_asset_id = "asset-final-test"
    handoff = make_ecommerce_handoff()
    proposed_shot = handoff.artifact_proposals.shots[0]
    selected_shot = seal_artifact(
        proposed_shot.model_copy(
            update={
                "revision": proposed_shot.revision + 1,
                "content_hash": "0" * 64,
                "visual_strategy": VisualStrategy.STATIC_IMAGE,
                "required_asset_roles": (
                    AssetRoleRequirement(
                        role="final_visual",
                        asset_ids=(final_asset_id,),
                        allowed_asset_types=(AssetType.IMAGE,),
                    ),
                    AssetRoleRequirement(
                        role="product_overlay",
                        asset_ids=(product_asset_id,),
                        allowed_asset_types=(AssetType.IMAGE,),
                    ),
                ),
                "generated_video_rationale": None,
            }
        )
    )
    presentation = handoff.ad_creative_plan_proposal.product_presentations[
        0
    ].model_copy(
        update={
            "asset_id": product_asset_id,
            "composition_layer_id": "layer-product",
        }
    )
    plan_proposal = handoff.ad_creative_plan_proposal.model_copy(
        update={"product_presentations": (presentation,)}
    )
    layout = EcommerceLayoutPlan.create(
        source_package_id=handoff.source_package_id,
        delivery_profile_id=handoff.delivery_profile.profile_id,
        visual_system_profile_id=handoff.visual_system_profile.profile_id,
        scenes=handoff.layout_plan.scenes,
        shots=(
            handoff.layout_plan.shots[0].model_copy(
                update={"visual_strategy": VisualStrategy.STATIC_IMAGE}
            ),
        ),
        beat_roles=handoff.layout_plan.beat_roles,
        graphic_treatments=handoff.layout_plan.graphic_treatments,
        product_presentations=(presentation,),
        protagonist_ids=handoff.layout_plan.protagonist_ids,
    )
    compile_profile = EcommerceProductionCompileProfile.create(
        delivery_profile_id=handoff.delivery_profile.profile_id,
        visual_system_profile_id=handoff.visual_system_profile.profile_id,
        layout_plan_id=layout.layout_plan_id,
        requirement_resolutions=tuple(
            item.model_copy(
                update={
                    "evidence_ids": (
                        handoff.delivery_profile.profile_id,
                        handoff.visual_system_profile.profile_id,
                        layout.layout_plan_id,
                    )
                }
            )
            for item in handoff.compile_profile.requirement_resolutions
        ),
    )
    values = {
        name: getattr(handoff, name)
        for name in EcommerceProductionHandoff.model_fields
        if name != "handoff_id"
    }
    runtime_handoff = EcommerceProductionHandoff.create(
        **{
            **values,
            "layout_plan": layout,
            "compile_profile": compile_profile,
            "artifact_proposals": handoff.artifact_proposals.model_copy(
                update={"shots": (selected_shot,)}
            ),
            "ad_creative_plan_proposal": plan_proposal,
            "asset_requirements": (
                EcommerceAssetRequirement(
                    asset_id=product_asset_id,
                    source_kind="IMAGE",
                    reference="assets/product.png",
                    rights_status="CONFIRMED",
                    expected_sha256=product_hash,
                    expected_size_bytes=len(product_bytes),
                ),
            ),
        }
    )
    plan = create_ad_creative_plan(
        plan_proposal,
        artifact_id="product-one-plan",
        revision=1,
        creation_receipt_id="ecommerce-delivery-plan",
        source_provenance=(
            SourceReference(
                kind="derived",
                reference=f"ecommerce-handoff:{runtime_handoff.handoff_id}",
                content_hash=runtime_handoff.handoff_id,
            ),
            SourceReference(
                kind="derived",
                reference=(
                    "ecommerce-compile-profile:"
                    f"{runtime_handoff.compile_profile.profile_id}"
                ),
                content_hash=runtime_handoff.compile_profile.profile_id,
            ),
        ),
    )
    base = make_composition_spec(shot_ids=("shot-hero",))
    base = seal_artifact(
        base.model_copy(
            update={
                "schema_version": "2.1",
                "revision": base.revision + 1,
                "content_hash": "0" * 64,
                "delivery_profile": DeliveryProfile(
                    width=1080,
                    height=1920,
                    fps=24,
                ),
                "layers": (
                    base.layers[0].model_copy(
                        update={
                            "layer_id": "layer-primary",
                            "asset_role": "final_visual",
                            "asset_id": final_asset_id,
                        }
                    ),
                    base.layers[0].model_copy(
                        update={
                            "layer_id": "layer-product",
                            "asset_role": "product_overlay",
                            "asset_id": product_asset_id,
                            "z_index": 10,
                        }
                    ),
                ),
                "audio_tracks": (
                    AudioTrackSpec(
                        track_id="audio-music",
                        audio_kind=AudioKind.BGM,
                        asset_id="audio-music-asset",
                        start_sample=0,
                    ),
                ),
                "caption_tracks": (),
            }
        )
    )
    compiled = compile_ad_creative_handoff(plan, base)
    return (
        runtime_handoff,
        plan,
        compiled,
        (product_bytes, product_hash, final_bytes, final_hash),
    )


def _package_kwargs(
    tmp_path: Path,
    *,
    delivery_root: Path | None = None,
    mismatched: bool = False,
):
    if mismatched:
        handoff, plan, compiled = _mismatched_identities()
    else:
        handoff, plan, compiled, _ = _identities()
    return {
        "project_root": tmp_path,
        "delivery_root": delivery_root or (tmp_path / "deliveries"),
        "job_id": "job-delivery",
        "handoff": handoff,
        "plan": plan,
        "compiled_handoff": compiled,
        "exported_at": EXPORTED_AT,
        "tool_identity": PACKAGER,
    }


def _mismatched_final_accepted_project(
    tmp_path: Path, *, bind_handoff: bool = True
):
    handoff, plan, compiled = _mismatched_identities()
    fixture = make_manifest_25_passing_review_fixture(tmp_path)
    review = fixture.run_required_review()
    before = fixture.load_manifest()
    acceptance = fixture.acceptance(review)
    if bind_handoff:
        acceptance = seal_artifact(
            acceptance.model_copy(
                update={
                    "content_hash": "0" * 64,
                    "source_provenance": (
                        *acceptance.source_provenance,
                        SourceReference(
                            kind="derived",
                            reference=f"ecommerce-handoff:{handoff.handoff_id}",
                            content_hash=handoff.handoff_id,
                        ),
                        SourceReference(
                            kind="derived",
                            reference=f"ecommerce-source-package:{handoff.source_package_id}",
                            content_hash=handoff.source_package_id,
                        ),
                        SourceReference(
                            kind="derived",
                            reference=f"ad-creative-plan:{plan.artifact_id}",
                            content_hash=plan.content_hash,
                        ),
                        SourceReference(
                            kind="derived",
                            reference=(
                                f"composition:{compiled.composition_spec.artifact_id}"
                            ),
                            content_hash=compiled.composition_spec.content_hash,
                        ),
                    ),
                }
            )
        )
    accepted = fixture.committer.record_final_acceptance(
        acceptance,
        expected_manifest_revision=before.manifest_revision,
        attempt_id="delivery-final-acceptance",
    )
    return fixture, accepted


def _final_accepted_project(tmp_path: Path):
    handoff, plan, compiled, media = _identities()
    product_bytes, product_hash, final_bytes, final_hash = media
    bootstrap = compile_ecommerce_production_handoff(
        handoff,
        expected_project_id="project-product-one",
    )
    product_asset = AssetRecord(
        asset_id="asset-product-test",
        asset_type=AssetType.IMAGE,
        artifact_path=canonical_image_asset_path(product_hash),
        sha256=product_hash,
        size_bytes=len(product_bytes),
        mime_type="image/png",
        width=2,
        height=1,
        source_kind=AssetSourceKind.IMPORTED,
        tool=ToolIdentity(name="fixture", version="1"),
        input_fingerprint="9" * 64,
        creation_receipt_id="fixture-product",
        usage_license="fixture",
        egress=EgressMetadata(remote=False),
    )
    final_asset = product_asset.model_copy(
        update={
            "asset_id": "asset-final-test",
            "artifact_path": canonical_image_asset_path(final_hash),
            "sha256": final_hash,
            "size_bytes": len(final_bytes),
            "creation_receipt_id": "fixture-final",
        }
    )
    (tmp_path / "assets/files").mkdir(parents=True, exist_ok=True)
    audio_asset, audio_path = project_factory._make_audio_asset(
        tmp_path,
        asset_id="audio-music-asset",
        audio_kind=AudioKind.BGM,
        duration_samples=144_000,
    )
    audio_bytes = audio_path.read_bytes()
    registry = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id="0" * 64,
        content_hash="0" * 64,
        assets=(product_asset, final_asset, audio_asset),
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    bootstrap = replace(
        bootstrap,
        registry=registry,
        artifacts=(
            *bootstrap.artifacts,
            PreparedArtifact(product_asset.artifact_path, product_bytes, product_hash),
            PreparedArtifact(final_asset.artifact_path, final_bytes, final_hash),
            PreparedArtifact(
                audio_asset.artifact_path,
                audio_bytes,
                audio_asset.sha256,
            ),
        ),
    )
    bootstrap_ecommerce_production_project(
        tmp_path,
        attempt_id="ecommerce-delivery-bootstrap",
        compiled=bootstrap,
    )
    loaded = load_production_project(tmp_path / "project.yaml")
    inputs = ProductionDependencyInputs(
        project=loaded,
        composition_spec=compiled.composition_spec,
        renderer=RendererIdentity(
            kind=RendererKind.HYPERFRAMES,
            version="0.7.103",
        ),
        voice_requests=(),
        resolver_contract_fingerprint="1" * 64,
        source_materializer_contract_fingerprint="2" * 64,
        render_contract_fingerprint="3" * 64,
        caption_style_fingerprints=(),
    )
    graph = build_production_dependency_graph(inputs)
    resolution = resolve_dependency_state(graph, ())
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=loaded.manifest.manifest_revision,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=resolution.states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    writer = ProductionStateCommitter(tmp_path)
    writer.bootstrap_dependency_graph(
        attempt_id="ecommerce-delivery-graph",
        graph=graph,
        transition=transition,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    project_factory._refresh_p7_ready_project_registry_nodes(tmp_path, writer)
    loaded = load_production_project(tmp_path / "project.yaml")
    timeline = resolve_composition(
        loaded,
        compiled.composition_spec,
        renderer_version="0.7.103",
    )
    selection = RendererSelectionReceipt(
        receipt_id="ecommerce-delivery-render-selection",
        attempt_id="ecommerce-delivery-render",
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=loaded.manifest.active_project,
        current_registry=loaded.manifest.active_registry,
    )
    tools = tmp_path / "ecommerce-delivery-tools"
    tools.mkdir()
    render_fixture = _Manifest25RenderFixture(
        root=tmp_path,
        committer=_CountingRenderCommitter(tmp_path),
        begin_request=BeginRenderAttemptRequest(
            loaded.manifest.manifest_revision,
            loaded.manifest.active_render_state,
            selection,
        ),
        timeline=timeline,
        asset_sources={
            item.asset_id: loaded.asset_paths[item.asset_id]
            for item in (*timeline.visual_spans, *timeline.audio_spans)
        },
        browser=_write_executable(tools / "chrome"),
        ip_path=_write_executable(tools / "ip"),
        runner=FakeRunner(),
        dependency_graph=graph,
        candidate_dependency_states=loaded.manifest.dependency_states,
        changed_nodes=[],
    )
    render_fixture.render()
    committer = ProductionStateCommitter(tmp_path)
    ecommerce_profile = create_qingyan_ecommerce_acceptance_profile()
    domain = DomainAcceptancePolicy(
        domain_id="ecommerce",
        profile_id=ecommerce_profile.profile_id,
        profile_version=ecommerce_profile.profile_version,
        profile_content_hash=ecommerce_profile.content_hash,
        profile_payload=ecommerce_profile.model_dump(mode="json"),
        measurement_contract_version=ecommerce_profile.measurement_contract_version,
        required_requirement_ids=ecommerce_profile.required_requirement_ids,
    )
    final_requirements = tuple(
        item
        for item in handoff.acceptance_requirements
        if item.scope == "FINAL_OUTPUT"
    )
    final_output = FinalOutputContract(
        goal_id="ecommerce-delivery-final-output",
        goal_version="1",
        user_goal="Deliver the exact accepted ecommerce ad.",
        requirements=tuple(
            FinalOutputRequirement(
                requirement_id=item.requirement_id,
                observable=item.description,
                proof="evaluator",
            )
            for item in final_requirements
        ),
    )
    policy = seal_artifact(
        QaPolicy(
            artifact_id="ecommerce-delivery-policy",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id="ecommerce-delivery-policy",
            source_provenance=(
                SourceReference(kind="derived", reference="delivery-test"),
            ),
            policy_id="ecommerce-delivery-policy",
            policy_version="1",
            required_layers=(
                QaLayer.TECHNICAL,
                QaLayer.LAYOUT,
                QaLayer.SEMANTIC,
            ),
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
            semantic_authorities=(REVIEW_TOOL,),
            domain_acceptance=domain,
            final_output=final_output,
        )
    )
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="ecommerce-delivery-policy",
    )
    for layer in (QaLayer.TECHNICAL, QaLayer.LAYOUT):
        _Manifest25ReviewFixture(
            root=tmp_path,
            committer=committer,
            timeline=timeline,
            policy=policy,
            review_layer=layer,
            review_attempt_id=f"ecommerce-delivery-{layer.value}",
        ).run_required_review()
    universal_profile = UniversalQaProfile.create(
        profile_id="ecommerce-delivery",
        profile_version="1",
        delivery_profile=timeline.delivery_profile,
        applicability=UniversalQaApplicability(
            has_audio=True,
            has_graphics=True,
            has_safe_area_requirements=True,
        ),
        required_hard_checks=(
            UniversalHardCheck.ASSET_PROVENANCE,
            UniversalHardCheck.MEDIA_DECODE,
            UniversalHardCheck.TIMELINE_BINDING,
            UniversalHardCheck.RENDER_OUTPUT,
            UniversalHardCheck.AUDIO_CAPTION_BINDING,
        ),
        required_review_layers=(QaLayer.TECHNICAL, QaLayer.LAYOUT),
    )
    acceptance = close_ecommerce_post_media_candidate(
        committer=committer,
        handoff=compiled,
        shot_facades={},
        universal_profile=universal_profile,
        run_hard_check=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS,
            current=True,
        ),
        run_review_layer=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS,
            current=True,
        ),
        caption_review_execution=None,
        tool_identity=REVIEW_TOOL,
        evaluate=lambda target, _profile: EcommerceWholeAdEvaluationPayload(
            domain_acceptance=_passing_payload(),
            final_output=FinalOutputObservation(
                contract_hash=final_output.contract_hash,
                review_request_content_hash=target.review_request_content_hash,
                findings=tuple(
                    FinalOutputFinding(
                        requirement_id=item.requirement_id,
                        verdict="pass",
                        observation="Observed on the exact final Ecommerce render.",
                    )
                    for item in final_requirements
                ),
            ),
        ),
        review_attempt_id="ecommerce-delivery-semantic",
        review_request_id="ecommerce-delivery-semantic-request",
        evidence_id="ecommerce-delivery-semantic-evidence",
        review_id="ecommerce-delivery-semantic-review",
        final_acceptance_id="ecommerce-delivery-final-acceptance",
        runtime_handoff=handoff,
    )
    assert acceptance.final_acceptance_recorded is True
    accepted = load_production_project(tmp_path / "project.yaml").manifest
    return SimpleNamespace(committer=committer), accepted


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            nested
            for item in value.values()
            for nested in _all_keys(item)
        }
    if isinstance(value, list):
        return {nested for item in value for nested in _all_keys(item)}
    return set()


def test_exact_final_accepted_render_packages_without_production_mutation(
    tmp_path: Path,
) -> None:
    fixture, accepted = _final_accepted_project(tmp_path)
    project = load_production_project(tmp_path / "project.yaml")
    assert project.render_state is not None
    source = tmp_path / project.render_state.output.path
    manifest_before = (tmp_path / "state/manifest.json").read_bytes()

    result = package_ecommerce_delivery(
        **_package_kwargs(tmp_path),
    )

    assert result.render_output_sha256 == project.render_state.output.file_sha256
    assert result.final_acceptance_content_hash == (
        accepted.final_acceptance_state.active_receipt.content_hash
    )
    assert result.bundle_path.is_dir()
    assert (result.bundle_path / "final.mp4").read_bytes() == source.read_bytes()
    inventory = json.loads((result.bundle_path / "bundle.json").read_text())
    lineage = json.loads((result.bundle_path / "lineage.json").read_text())
    assert inventory["bundle_id"] == result.bundle_id
    assert lineage["render_output_sha256"] == result.render_output_sha256
    assert lineage["render_media_facts"]["width"] > 0
    assert lineage["render_media_facts"]["height"] > 0
    assert lineage["render_media_facts"]["duration_frames"] > 0
    assert lineage["source_package_id"] == _identities()[0].source_package_id
    assert lineage["ad_creative_plan"]["content_hash"] == _identities()[1].content_hash
    assert lineage["composition"]["content_hash"] == (
        _identities()[2].composition_spec.content_hash
    )
    assert lineage["exported_at"] == EXPORTED_AT
    assert lineage["tool_identity"] == PACKAGER.model_dump(mode="json")
    assert lineage["storyboard"]["content_hash"] == (
        _identities()[0].artifact_proposals.storyboard.content_hash
    )
    assert [item["content_hash"] for item in lineage["shots"]] == [
        item.content_hash for item in _identities()[0].artifact_proposals.shots
    ]
    assert lineage["final_acceptance"] == accepted.final_acceptance_state.active_receipt.model_dump(
        mode="json"
    )
    assert not {
        key
        for key in _all_keys(lineage)
        if "secret" in key.lower() or "permit" in key.lower()
    }
    assert (tmp_path / "state/manifest.json").read_bytes() == manifest_before


def test_nonaccepted_project_is_refused_without_bundle(tmp_path: Path) -> None:
    fixture = make_manifest_25_passing_review_fixture(tmp_path)
    fixture.run_required_review()
    delivery_root = tmp_path / "deliveries"

    with pytest.raises(AiVideoError) as exc_info:
        package_ecommerce_delivery(
            **_package_kwargs(tmp_path, delivery_root=delivery_root),
        )

    assert exc_info.value.code is ErrorCode.FINAL_ACCEPTANCE_INVALID
    assert not delivery_root.exists() or not tuple(delivery_root.iterdir())


def test_hash_mismatched_final_render_is_refused_without_bundle(tmp_path: Path) -> None:
    _final_accepted_project(tmp_path)
    project = load_production_project(tmp_path / "project.yaml")
    assert project.render_state is not None
    (tmp_path / project.render_state.output.path).write_bytes(b"tampered-render")
    delivery_root = tmp_path / "deliveries"

    with pytest.raises(AiVideoError):
        package_ecommerce_delivery(
            **_package_kwargs(tmp_path, delivery_root=delivery_root),
        )

    assert not delivery_root.exists() or not tuple(delivery_root.iterdir())


def test_final_acceptance_with_mismatched_composition_is_refused_without_bundle(
    tmp_path: Path,
) -> None:
    _final_accepted_project(tmp_path)
    handoff, plan, compiled, _ = _identities()
    drifted_composition = seal_artifact(
        compiled.composition_spec.model_copy(
            update={
                "revision": compiled.composition_spec.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": "drifted-after-final-acceptance",
            }
        )
    )
    delivery_root = tmp_path / "deliveries"

    with pytest.raises(AiVideoError, match="lineage"):
        package_ecommerce_delivery(
            project_root=tmp_path,
            delivery_root=delivery_root,
            job_id="job-delivery",
            handoff=handoff,
            plan=plan,
            compiled_handoff=compiled.model_copy(
                update={"composition_spec": drifted_composition}
            ),
            exported_at=EXPORTED_AT,
            tool_identity=PACKAGER,
        )

    assert not delivery_root.exists()


def test_interrupted_publish_leaves_no_active_or_staging_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _final_accepted_project(tmp_path)
    delivery_root = tmp_path / "deliveries"

    def interrupt(*_: object) -> None:
        raise OSError("injected publish interruption")

    monkeypatch.setattr(
        "ai_video.production.delivery_packager.os.replace",
        interrupt,
    )
    with pytest.raises(OSError, match="publish interruption"):
        package_ecommerce_delivery(
            **_package_kwargs(tmp_path, delivery_root=delivery_root),
        )

    assert delivery_root.is_dir()
    assert tuple(delivery_root.iterdir()) == ()


def test_exact_package_replay_reuses_same_bundle_without_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _final_accepted_project(tmp_path)
    delivery_root = tmp_path / "deliveries"
    first = package_ecommerce_delivery(
        **_package_kwargs(tmp_path, delivery_root=delivery_root),
    )

    monkeypatch.setattr(
        "ai_video.production.delivery_packager.shutil.copyfile",
        lambda *_: (_ for _ in ()).throw(AssertionError("replay copied media")),
    )
    replay = package_ecommerce_delivery(
        **_package_kwargs(tmp_path, delivery_root=delivery_root),
    )

    assert replay == first


@pytest.mark.parametrize("link_kind", ("symlink", "hardlink"))
def test_existing_bundle_linked_media_is_refused_on_inspect_and_replay(
    tmp_path: Path,
    link_kind: str,
) -> None:
    _final_accepted_project(tmp_path)
    kwargs = _package_kwargs(tmp_path)
    first = package_ecommerce_delivery(**kwargs)
    loaded = load_production_project(tmp_path / "project.yaml")
    assert loaded.render_state is not None
    source = tmp_path / loaded.render_state.output.path
    published = first.bundle_path / "final.mp4"
    published.unlink()
    if link_kind == "symlink":
        published.symlink_to(source)
    else:
        os.link(source, published)

    with pytest.raises(AiVideoError, match="regular file"):
        inspect_ecommerce_delivery(**kwargs)
    with pytest.raises(AiVideoError, match="regular file"):
        package_ecommerce_delivery(**kwargs)


def test_unbound_handoff_is_refused_before_delivery_directory_creation(
    tmp_path: Path,
) -> None:
    _mismatched_final_accepted_project(tmp_path, bind_handoff=False)
    delivery_root = tmp_path / "deliveries"

    with pytest.raises(AiVideoError, match="handoff"):
        package_ecommerce_delivery(
            **_package_kwargs(
                tmp_path,
                delivery_root=delivery_root,
                mismatched=True,
            ),
        )

    assert not delivery_root.exists()


def test_existing_bundle_inventory_tamper_is_refused_on_replay(
    tmp_path: Path,
) -> None:
    _final_accepted_project(tmp_path)
    delivery_root = tmp_path / "deliveries"
    first = package_ecommerce_delivery(
        **_package_kwargs(tmp_path, delivery_root=delivery_root),
    )
    (first.bundle_path / "lineage.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(AiVideoError, match="lineage"):
        package_ecommerce_delivery(
            **_package_kwargs(tmp_path, delivery_root=delivery_root),
        )
