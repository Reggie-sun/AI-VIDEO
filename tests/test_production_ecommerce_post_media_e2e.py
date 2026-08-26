from __future__ import annotations

from dataclasses import replace

import pytest

from ai_video.errors import AiVideoError

from ai_video.production.ad_creative_types import (
    AdCompositionRequirements,
    AdShotProposal,
    CompiledAdCreativeHandoff,
)
from ai_video.production.commercial_execution import (
    CommercialExecutionDisposition,
    CommercialExecutionProjection,
    CommercialShotClass,
)
from ai_video.production.dependency import (
    build_production_dependency_graph,
    resolve_dependency_state,
)
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.ecommerce_ad_coordinator import run_ecommerce_ad_production
from ai_video.production.ecommerce_media_acceptance import (
    EcommerceAcceptanceEvidencePayload,
    EcommerceRequirementFinding,
    create_qingyan_ecommerce_acceptance_profile,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    QaVerdict,
    RendererKind,
    RendererSelectionReceipt,
    SourceReference,
    ToolIdentity,
)
from ai_video.production.project import load_production_project
from ai_video.production.quality_gate_coordinator import (
    UniversalHardCheck,
    UniversalQaApplicability,
    UniversalQaCheckOutcome,
    UniversalQaProfile,
)
from ai_video.production.state_commit import (
    BeginRenderAttemptRequest,
    ProductionStateCommitter,
)
import production_project_factory as project_factory
from test_production_hyperframes import (
    FakeRunner,
    _CountingRenderCommitter,
    _Manifest25RenderFixture,
    _write_executable,
)
from test_production_review import _Manifest25ReviewFixture


ZERO_HASH = "0" * 64
PLAN_HASH = "a" * 64
TOOL = ToolIdentity(name="whole-ad-evaluator", version="1")


def _projection(shot_id: str) -> CommercialExecutionProjection:
    values = {
        "schema_version": "commercial-execution-projection/1",
        "ad_creative_plan_id": "plan-e2e",
        "ad_creative_plan_revision": 1,
        "ad_creative_plan_hash": PLAN_HASH,
        "target_shot_id": shot_id,
        "primary_class": CommercialShotClass.END_CARD,
        "product_id": None,
        "product_reference_requirement_id": None,
        "source_requirement_id": None,
        "character_requirement_ids": (),
        "scene_requirement_fingerprint": "b" * 64,
        "wardrobe_requirement_fingerprint": "c" * 64,
        "accessory_requirement_fingerprint": "d" * 64,
        "recommended_disposition": CommercialExecutionDisposition.COMPOSITOR_ONLY,
        "requires_source_materialization": False,
        "requires_source_review": False,
        "invoke_video_provider": False,
        "graphic_ids": (),
        "sound_cue_ids": (),
    }
    values["projection_hash"] = canonical_sha256(values)
    return CommercialExecutionProjection.model_validate(values)


def _policy() -> QaPolicy:
    profile = create_qingyan_ecommerce_acceptance_profile()
    domain = DomainAcceptancePolicy(
        domain_id="ecommerce",
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_content_hash=profile.content_hash,
        profile_payload=profile.model_dump(mode="json"),
        measurement_contract_version=profile.measurement_contract_version,
        required_requirement_ids=profile.required_requirement_ids,
    )
    return seal_artifact(
        QaPolicy(
            artifact_id="ecommerce-e2e-policy",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="ecommerce-e2e-policy",
            source_provenance=(SourceReference(kind="derived", reference="e2e"),),
            policy_id="ecommerce-e2e-policy",
            policy_version="1",
            required_layers=(QaLayer.TECHNICAL, QaLayer.LAYOUT, QaLayer.SEMANTIC),
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
            semantic_authorities=(TOOL,),
            domain_acceptance=domain,
        )
    )


def _passing_payload() -> EcommerceAcceptanceEvidencePayload:
    profile = create_qingyan_ecommerce_acceptance_profile()
    return EcommerceAcceptanceEvidencePayload.create(
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_content_hash=profile.content_hash,
        findings=tuple(
            EcommerceRequirementFinding(
                requirement_id=requirement_id,
                verdict=QaVerdict.PASS,
                rationale="observed in exact canonical final candidate",
            )
            for requirement_id in profile.required_requirement_ids
        ),
    )


def _render_canonical_ad(tmp_path):
    from ai_video.production.composition import resolve_composition

    runtime = project_factory.make_p7_reuse_runtime(tmp_path)
    runtime.generate_all()
    loaded = load_production_project(tmp_path / "project.yaml")
    base = runtime.base_inputs.composition_spec
    composition = seal_artifact(
        base.model_copy(
            update={
                "schema_version": "2.2",
                "revision": base.revision + 1,
                "content_hash": ZERO_HASH,
                "layers": tuple(
                    layer.model_copy(
                        update={
                            "asset_id": next(
                                role.asset_ids[0]
                                for shot in loaded.shots
                                if shot.shot_id == layer.shot_id
                                for role in shot.required_asset_roles
                                if role.role == layer.asset_role
                            )
                        }
                    )
                    for layer in base.layers
                ),
                "ad_creative_plan_id": "plan-e2e",
                "ad_creative_plan_hash": PLAN_HASH,
            }
        )
    )
    timeline = resolve_composition(loaded, composition, renderer_version="0.7.103")
    asset_sources = {
        span.asset_id: loaded.asset_paths[span.asset_id]
        for span in (*timeline.visual_spans, *timeline.audio_spans)
    }
    asset_sources.update(
        {
            cue.caption_asset_id: loaded.asset_paths[cue.caption_asset_id]
            for cue in timeline.caption_cues
        }
    )
    for binding in composition.caption_tracks:
        if binding.style_reference is not None:
            asset_sources[binding.style_reference.artifact_id] = (
                tmp_path / binding.style_reference.path
            )
    graph = build_production_dependency_graph(
        replace(
            runtime.base_inputs,
            project=loaded,
            composition_spec=composition,
            voice_requests=(),
        )
    )
    states = resolve_dependency_state(graph, loaded.manifest.dependency_states).states
    selection = RendererSelectionReceipt(
        receipt_id="ecommerce-e2e-render-selection",
        attempt_id="ecommerce-e2e-render",
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=loaded.manifest.active_project,
        current_registry=loaded.manifest.active_registry,
    )
    tools = tmp_path / "ecommerce-render-tools"
    tools.mkdir()
    fixture = _Manifest25RenderFixture(
        root=tmp_path,
        committer=_CountingRenderCommitter(tmp_path),
        begin_request=BeginRenderAttemptRequest(
            loaded.manifest.manifest_revision,
            loaded.manifest.active_render_state,
            selection,
        ),
        timeline=timeline,
        asset_sources=asset_sources,
        browser=_write_executable(tools / "chrome"),
        ip_path=_write_executable(tools / "ip"),
        runner=FakeRunner(),
        dependency_graph=graph,
        candidate_dependency_states=states,
        changed_nodes=[],
    )
    fixture.render()
    handoff = CompiledAdCreativeHandoff(
        plan_id="plan-e2e",
        plan_content_hash=PLAN_HASH,
        shot_proposals=tuple(
            AdShotProposal(shot_id=shot_id, beat_ids=(f"beat-{shot_id}",))
            for shot_id in composition.shot_ids
        ),
        composition_requirements=AdCompositionRequirements(),
        composition_spec=composition,
        commercial_execution_projections=tuple(
            _projection(shot_id) for shot_id in composition.shot_ids
        ),
    )
    return handoff, timeline


def test_canonical_final_candidate_closes_gate_two_p6_and_final_acceptance(
    tmp_path,
) -> None:
    handoff, timeline = _render_canonical_ad(tmp_path)
    policy = _policy()
    committer = ProductionStateCommitter(tmp_path)
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="ecommerce-e2e-policy",
    )
    for layer in (QaLayer.TECHNICAL, QaLayer.LAYOUT):
        fixture = _Manifest25ReviewFixture(
            root=tmp_path,
            committer=committer,
            timeline=timeline,
            policy=policy,
            review_layer=layer,
            review_attempt_id=f"ecommerce-e2e-{layer.value}",
        )
        fixture.run_required_review()

    bundle = load_production_project(tmp_path / "project.yaml")
    assert bundle.render_state is not None
    assert bundle.manifest.active_dependency_graph is not None
    assert bundle.manifest.active_render_state is not None
    applicability = UniversalQaApplicability(
        has_audio=True,
        has_captions=True,
        has_transitions=True,
    )
    profile = UniversalQaProfile.create(
        profile_id="ecommerce-final-media",
        profile_version="1",
        delivery_profile=timeline.delivery_profile,
        applicability=applicability,
        required_hard_checks=(
            UniversalHardCheck.ASSET_PROVENANCE,
            UniversalHardCheck.MEDIA_DECODE,
            UniversalHardCheck.TIMELINE_BINDING,
            UniversalHardCheck.RENDER_OUTPUT,
            UniversalHardCheck.AUDIO_CAPTION_BINDING,
        ),
        required_review_layers=(QaLayer.TECHNICAL, QaLayer.LAYOUT),
    )
    gate_one_calls: list[str] = []
    render_activation_calls: list[str] = []
    production = run_ecommerce_ad_production(
        handoff,
        facades={},
        activate_final_render=lambda *_: render_activation_calls.append("render"),
        committer=committer,
        universal_profile=profile,
        run_hard_check=lambda hard_check, *_: (
            gate_one_calls.append(hard_check.value)
            or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
        ),
        run_review_layer=lambda layer, *_: (
            gate_one_calls.append(layer.value)
            or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
        ),
        tool_identity=TOOL,
        evaluate=lambda *_: _passing_payload(),
        review_attempt_id="ecommerce-e2e-semantic",
        review_request_id="ecommerce-e2e-semantic-request",
        evidence_id="ecommerce-e2e-semantic-evidence",
        review_id="ecommerce-e2e-semantic-review",
        final_acceptance_id="ecommerce-e2e-final-acceptance",
    )
    result = production.post_media_acceptance
    assert result is not None

    final = load_production_project(tmp_path / "project.yaml").manifest
    assert production.complete is True
    assert render_activation_calls == ["render"]
    assert result.final_acceptance_recorded is True
    assert gate_one_calls == [
        *(item.value for item in profile.required_hard_checks),
        *(item.value for item in profile.required_review_layers),
    ]
    assert result.render_output_sha256 == bundle.render_state.output.file_sha256
    assert final.final_acceptance_state is not None


def test_noncanonical_file_cannot_be_supplied_as_post_media_candidate() -> None:
    assert "file" not in run_ecommerce_ad_production.__annotations__
    assert "mp4" not in run_ecommerce_ad_production.__annotations__
    assert "project_root" not in run_ecommerce_ad_production.__annotations__
    assert "timeline" not in run_ecommerce_ad_production.__annotations__
    assert "universal_result" not in run_ecommerce_ad_production.__annotations__


def test_changed_active_render_bytes_cannot_enter_gate_closure(tmp_path) -> None:
    handoff, timeline = _render_canonical_ad(tmp_path)
    policy = _policy()
    committer = ProductionStateCommitter(tmp_path)
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="ecommerce-mutated-policy",
    )
    bundle = load_production_project(tmp_path / "project.yaml")
    assert bundle.render_state is not None
    output = tmp_path / bundle.render_state.output.path
    output.write_bytes(output.read_bytes() + b"post-gate-mutation")
    calls: list[str] = []
    profile = UniversalQaProfile.create(
        profile_id="ecommerce-mutated-final-media",
        profile_version="1",
        delivery_profile=timeline.delivery_profile,
        applicability=UniversalQaApplicability(),
        required_hard_checks=(
            UniversalHardCheck.ASSET_PROVENANCE,
            UniversalHardCheck.MEDIA_DECODE,
            UniversalHardCheck.TIMELINE_BINDING,
            UniversalHardCheck.RENDER_OUTPUT,
        ),
        required_review_layers=(QaLayer.TECHNICAL,),
    )

    with pytest.raises(AiVideoError):
        run_ecommerce_ad_production(
            handoff,
            facades={},
            activate_final_render=lambda *_: None,
            committer=committer,
            universal_profile=profile,
            run_hard_check=lambda *_: (
                calls.append("hard")
                or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
            ),
            run_review_layer=lambda *_: (
                calls.append("review")
                or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
            ),
            tool_identity=TOOL,
            evaluate=lambda *_: _passing_payload(),
            review_attempt_id="ecommerce-mutated-semantic",
            review_request_id="ecommerce-mutated-request",
            evidence_id="ecommerce-mutated-evidence",
            review_id="ecommerce-mutated-review",
            final_acceptance_id="ecommerce-mutated-final",
        )

    assert calls == []


def test_invalid_gate_two_evidence_is_durably_not_evaluated(tmp_path) -> None:
    handoff, timeline = _render_canonical_ad(tmp_path)
    policy = _policy()
    committer = ProductionStateCommitter(tmp_path)
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="ecommerce-invalid-policy",
    )
    profile = UniversalQaProfile.create(
        profile_id="ecommerce-invalid-final-media",
        profile_version="1",
        delivery_profile=timeline.delivery_profile,
        applicability=UniversalQaApplicability(
            has_audio=True,
            has_captions=True,
            has_transitions=True,
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

    production = run_ecommerce_ad_production(
        handoff,
        facades={},
        activate_final_render=lambda *_: None,
        committer=committer,
        universal_profile=profile,
        run_hard_check=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS, current=True
        ),
        run_review_layer=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS, current=True
        ),
        tool_identity=TOOL,
        evaluate=lambda *_: object(),
        review_attempt_id="ecommerce-invalid-semantic",
        review_request_id="ecommerce-invalid-request",
        evidence_id="ecommerce-invalid-evidence",
        review_id="ecommerce-invalid-review",
        final_acceptance_id="ecommerce-invalid-final",
    )
    result = production.post_media_acceptance
    assert result is not None

    current = load_production_project(tmp_path / "project.yaml").manifest
    assert result.gate_two.verdict is QaVerdict.NOT_EVALUATED
    assert result.p6_semantic_receipt_recorded is True
    assert result.final_acceptance_recorded is False
    assert current.final_acceptance_state is None
    assert any(
        item.layer is QaLayer.SEMANTIC for item in current.active_review_receipts
    )
