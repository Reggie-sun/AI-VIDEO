from __future__ import annotations

from pathlib import Path

import pytest

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
from ai_video.production.composition import timeline_fingerprint
from ai_video.production.composition_contracts import (
    CompositionLayerSpec,
    CompositionSpec,
    DeliveryProfile,
    RendererIdentity,
    ResolvedTimeline,
    ResolvedVisualSpan,
)
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.ecommerce_media_acceptance import (
    EcommerceAcceptanceEvidencePayload,
    EcommerceRequirementFinding,
    create_qingyan_ecommerce_acceptance_profile,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaPolicyPointer,
    QaTechnicalThresholds,
    QaVerdict,
    RenderStateSnapshotPointer,
    ReviewRequest,
    SourceReference,
    TechnicalReviewContext,
    TechnicalReviewWindow,
    ToolIdentity,
    VisualStrategy,
)
from ai_video.production.quality_gate_coordinator import (
    UniversalHardCheck,
    UniversalQaApplicability,
    UniversalQaCheckOutcome,
    UniversalQaContext,
    UniversalQaProfile,
    UniversalQualityGateCoordinator,
)


ZERO_HASH = "0" * 64
TOOL = ToolIdentity(name="whole-ad-evaluator", version="1")


class _Permit:
    def __init__(self) -> None:
        self.consumed = False

    def _consume_review_analysis_permit(self, **_: object) -> bool:
        if self.consumed:
            return False
        self.consumed = True
        return True


def _projection() -> CommercialExecutionProjection:
    values = {
        "schema_version": "commercial-execution-projection/1",
        "ad_creative_plan_id": "plan-1",
        "ad_creative_plan_revision": 1,
        "ad_creative_plan_hash": "a" * 64,
        "target_shot_id": "shot-1",
        "primary_class": CommercialShotClass.CHARACTER_PERFORMANCE,
        "product_id": None,
        "product_reference_requirement_id": None,
        "source_requirement_id": None,
        "character_requirement_ids": ("hero",),
        "scene_requirement_fingerprint": "b" * 64,
        "wardrobe_requirement_fingerprint": "c" * 64,
        "accessory_requirement_fingerprint": "d" * 64,
        "recommended_disposition": (
            CommercialExecutionDisposition.EXISTING_CHARACTER_SCENE_PLANNING
        ),
        "requires_source_materialization": False,
        "requires_source_review": False,
        "invoke_video_provider": True,
        "graphic_ids": (),
        "sound_cue_ids": (),
    }
    values["projection_hash"] = canonical_sha256(values)
    return CommercialExecutionProjection.model_validate(values)


def _handoff() -> CompiledAdCreativeHandoff:
    composition = seal_artifact(
        CompositionSpec(
            schema_version="2.2",
            artifact_id="composition-1",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="composition-1",
            source_provenance=(SourceReference(kind="derived", reference="plan-1"),),
            composition_id="composition-1",
            shot_ids=("shot-1",),
            layers=(
                CompositionLayerSpec(
                    layer_id="layer-1",
                    shot_id="shot-1",
                    asset_role="generated_video",
                    asset_id="video-shot-1",
                ),
            ),
            delivery_profile=DeliveryProfile(width=1080, height=1920, fps=24),
            ad_creative_plan_id="plan-1",
            ad_creative_plan_hash="a" * 64,
        )
    )
    return CompiledAdCreativeHandoff(
        plan_id="plan-1",
        plan_content_hash="a" * 64,
        shot_proposals=(AdShotProposal(shot_id="shot-1", beat_ids=("beat-1",)),),
        composition_requirements=AdCompositionRequirements(),
        composition_spec=composition,
        commercial_execution_projections=(_projection(),),
    )


def _timeline(handoff: CompiledAdCreativeHandoff) -> ResolvedTimeline:
    provisional = ResolvedTimeline(
        schema_version="2.2",
        artifact_id="timeline-1",
        revision=1,
        content_hash=ZERO_HASH,
        creation_receipt_id="timeline-1",
        source_provenance=(
            SourceReference(
                kind="derived", reference=handoff.composition_spec.artifact_id
            ),
        ),
        timeline_id="timeline-1",
        composition_spec_id=handoff.composition_spec.composition_id,
        composition_spec_revision=handoff.composition_spec.revision,
        composition_spec_hash=handoff.composition_spec.content_hash,
        delivery_profile=handoff.composition_spec.delivery_profile,
        sample_rate=48_000,
        renderer=RendererIdentity(kind="hyperframes", version="0.7.103"),
        visual_spans=(
            ResolvedVisualSpan(
                layer_id="layer-1",
                shot_id="shot-1",
                asset_role="generated_video",
                asset_id="video-shot-1",
                asset_sha256="e" * 64,
                asset_mime_type="video/mp4",
                materialized_path=Path("assets/files/video-shot-1.mp4"),
                start_frame=0,
                duration_frames=48,
                start_sample=0,
                duration_samples=96_000,
                trim_start_frame=0,
                transform={},
                opacity_milli=1000,
                z_index=0,
            ),
        ),
        total_frames=48,
        total_samples=96_000,
        composition_fingerprint="6" * 64,
    )
    return seal_artifact(
        provisional.model_copy(
            update={"composition_fingerprint": timeline_fingerprint(provisional)}
        )
    )


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
            artifact_id="qa-policy-1",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="qa-policy-1",
            source_provenance=(SourceReference(kind="derived", reference="qa-policy"),),
            policy_id="qa-policy-1",
            policy_version="1",
            required_layers=(QaLayer.TECHNICAL, QaLayer.SEMANTIC),
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


def _gate_one(
    policy: QaPolicy,
    *,
    timeline_fingerprint_value: str,
    current: bool = True,
    verdict: QaVerdict = QaVerdict.PASS,
):
    applicability = UniversalQaApplicability(has_audio=False)
    profile = UniversalQaProfile.create(
        profile_id="universal-final-media",
        profile_version="1",
        delivery_profile=DeliveryProfile(width=1080, height=1920, fps=24),
        applicability=applicability,
        required_hard_checks=(
            UniversalHardCheck.ASSET_PROVENANCE,
            UniversalHardCheck.MEDIA_DECODE,
            UniversalHardCheck.TIMELINE_BINDING,
            UniversalHardCheck.RENDER_OUTPUT,
        ),
        required_review_layers=(QaLayer.TECHNICAL,),
    )
    context = UniversalQaContext(
        delivery_profile=profile.delivery_profile,
        applicability=applicability,
        project_content_hash="1" * 64,
        registry_content_hash="2" * 64,
        dependency_graph_revision_id="3" * 64,
        render_state_content_hash="4" * 64,
        render_output_sha256="5" * 64,
        timeline_fingerprint=timeline_fingerprint_value,
        qa_policy_content_hash=policy.content_hash,
    )
    result = UniversalQualityGateCoordinator().run_once(
        profile=profile,
        context=context,
        policy=policy,
        run_hard_check=lambda *_: UniversalQaCheckOutcome(
            verdict=verdict, current=current
        ),
        run_review_layer=lambda *_: UniversalQaCheckOutcome(
            verdict=verdict, current=current
        ),
    )
    return profile, context, result


def _request(policy: QaPolicy, *, timeline_fingerprint_value: str) -> ReviewRequest:
    return seal_artifact(
        ReviewRequest(
            artifact_id="review-request-1",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="review-request-1",
            source_provenance=(
                SourceReference(kind="derived", reference="final-media"),
            ),
            request_id="review-request-1",
            base_manifest_revision=1,
            dependency_graph=DependencyGraphSnapshotPointer(
                path=Path(f"state/dependency_graph.{'3' * 64}.json"),
                revision_id="3" * 64,
                content_hash="3" * 64,
                file_sha256="8" * 64,
            ),
            dependency_states_hash="9" * 64,
            render_state=RenderStateSnapshotPointer(
                path=Path(f"state/render/states/{'4' * 64}.json"),
                revision=1,
                content_hash="4" * 64,
                file_sha256="a" * 64,
            ),
            render_output_sha256="5" * 64,
            timeline_fingerprint=timeline_fingerprint_value,
            qa_policy=QaPolicyPointer(
                path=Path(f"state/reviews/policy.{policy.content_hash}.json"),
                policy_id=policy.policy_id,
                policy_version=policy.policy_version,
                content_hash=policy.content_hash,
                file_sha256="b" * 64,
            ),
            requested_layers=(QaLayer.SEMANTIC,),
            evidence_tool_identities=(TOOL,),
            technical_context=TechnicalReviewContext(
                render_output_sha256="5" * 64,
                timeline_fingerprint=timeline_fingerprint_value,
                windows=(
                    TechnicalReviewWindow(
                        shot_id="shot-1",
                        visual_strategy=VisualStrategy.GENERATED_VIDEO,
                        start_frame=0,
                        end_frame_exclusive=48,
                        expects_audio=False,
                        visual_span_ids=("layer-1",),
                    ),
                ),
                measurement_contract_version="ecommerce-media-acceptance/1",
            ),
        )
    )


def _accepted_shot():
    from ai_video.production.ecommerce_quality_gate import EcommerceAcceptedShotIdentity

    projection = _projection()
    return EcommerceAcceptedShotIdentity.create(
        ad_creative_plan_hash="a" * 64,
        commercial_execution_projection_hash=projection.projection_hash,
        shot_id="shot-1",
        resolved_generation_hash="c" * 64,
        artifact_sha256="e" * 64,
        commercial_evidence_content_hash="d" * 64,
        checkpoint_content_hash="f" * 64,
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
                rationale="observed in exact final media",
            )
            for requirement_id in profile.required_requirement_ids
        ),
    )


def _run(
    *,
    gate_current: bool = True,
    gate_verdict: QaVerdict = QaVerdict.PASS,
    mutate_timeline: bool = False,
    evaluator=None,
    active_timeline_hash: str | None = None,
):
    from ai_video.production.ecommerce_quality_gate import (
        EcommerceQualityGateCoordinator,
    )

    policy = _policy()
    handoff = _handoff()
    timeline = _timeline(handoff)
    gate_profile, gate_context, gate_result = _gate_one(
        policy,
        timeline_fingerprint_value=timeline.composition_fingerprint,
        current=gate_current,
        verdict=gate_verdict,
    )
    if mutate_timeline:
        timeline = timeline.model_copy(update={"composition_fingerprint": "0" * 64})
    calls: list[str] = []
    permit = _Permit()
    outcome = EcommerceQualityGateCoordinator().run_once(
        universal_profile=gate_profile,
        universal_context=gate_context,
        universal_result=gate_result,
        policy=policy,
        review_request=_request(
            policy, timeline_fingerprint_value=timeline.composition_fingerprint
        ),
        handoff=handoff,
        timeline=timeline,
        active_timeline_content_hash=active_timeline_hash or timeline.content_hash,
        accepted_shots=(_accepted_shot(),),
        tool_identity=TOOL,
        permit=permit,
        evidence_id="whole-ad-evidence-1",
        evaluate=evaluator
        or (lambda *_: calls.append("evaluate") or _passing_payload()),
    )
    return outcome, calls, permit


def test_gate_two_pass_binds_exact_final_candidate_and_gate_one() -> None:
    outcome, calls, permit = _run()

    assert outcome.result.verdict is QaVerdict.PASS
    assert outcome.result.eligible_for_p6_review is True
    assert outcome.evidence is not None
    assert outcome.evidence.render_output_sha256 == "5" * 64
    assert (
        outcome.evidence.measured_payload["acceptance_target"]["render_output_sha256"]
        == "5" * 64
    )
    assert calls == ["evaluate"]
    assert permit.consumed is True
    from ai_video.production.review import adjudicate_review_evidence

    assert (
        adjudicate_review_evidence(
            _policy(),
            QaLayer.SEMANTIC,
            (outcome.evidence,),
            review_request_content_hash=outcome.target.review_request_content_hash,
        )
        is QaVerdict.PASS
    )
    assert (
        adjudicate_review_evidence(
            _policy(),
            QaLayer.SEMANTIC,
            (outcome.evidence,),
            review_request_content_hash="0" * 64,
        )
        is QaVerdict.NOT_EVALUATED
    )
    changed_bytes = outcome.evidence.model_copy(
        update={"render_output_sha256": "f" * 64}
    )
    assert (
        adjudicate_review_evidence(
            _policy(),
            QaLayer.SEMANTIC,
            (changed_bytes,),
            review_request_content_hash=outcome.target.review_request_content_hash,
        )
        is QaVerdict.NOT_EVALUATED
    )


@pytest.mark.parametrize("case", ("gate_not_current", "gate_fail", "timeline_stale"))
def test_stale_gate_or_timeline_blocks_before_evaluator(case: str) -> None:
    outcome, calls, permit = _run(
        gate_current=case != "gate_not_current",
        gate_verdict=(QaVerdict.FAIL if case == "gate_fail" else QaVerdict.PASS),
        mutate_timeline=case == "timeline_stale",
    )

    assert outcome.result.verdict is QaVerdict.NOT_EVALUATED
    assert outcome.result.eligible_for_p6_review is False
    assert outcome.evidence is None
    assert calls == []
    assert permit.consumed is False


def test_reusing_review_analysis_permit_fails_closed() -> None:
    from ai_video.production.ecommerce_quality_gate import (
        EcommerceQualityGateCoordinator,
    )

    policy = _policy()
    handoff = _handoff()
    timeline = _timeline(handoff)
    gate_profile, gate_context, gate_result = _gate_one(
        policy, timeline_fingerprint_value=timeline.composition_fingerprint
    )
    permit = _Permit()
    permit.consumed = True

    with pytest.raises(ValueError, match="permit"):
        EcommerceQualityGateCoordinator().run_once(
            universal_profile=gate_profile,
            universal_context=gate_context,
            universal_result=gate_result,
            policy=policy,
            review_request=_request(
                policy, timeline_fingerprint_value=timeline.composition_fingerprint
            ),
            handoff=handoff,
            timeline=timeline,
            active_timeline_content_hash=timeline.content_hash,
            accepted_shots=(_accepted_shot(),),
            tool_identity=TOOL,
            permit=permit,
            evidence_id="whole-ad-evidence-reused",
            evaluate=lambda *_: _passing_payload(),
        )


def test_invalid_domain_evaluator_produces_not_evaluated_receipt_evidence() -> None:
    outcome, _, permit = _run(evaluator=lambda *_: object())

    assert permit.consumed is True
    assert outcome.result.verdict is QaVerdict.NOT_EVALUATED
    assert outcome.result.block_reason.value == "domain_evidence_invalid"
    assert outcome.evidence is not None
    assert outcome.evidence.measured_payload["domain_evidence_invalid"] is True


def test_gate_two_rejects_timeline_not_owned_by_active_render() -> None:
    outcome, calls, permit = _run(active_timeline_hash="0" * 64)

    assert outcome.result.verdict is QaVerdict.NOT_EVALUATED
    assert outcome.result.block_reason.value == "composition_not_current"
    assert outcome.result.blocked_identifiers == ("active_timeline_hash",)
    assert calls == []
    assert permit.consumed is False
