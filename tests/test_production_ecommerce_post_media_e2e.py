from __future__ import annotations

from dataclasses import replace

import production_project_factory as project_factory
import pytest
from production_e2e_support import (
    make_caption_quality_policy,
    make_caption_review_execution,
)
from test_production_hyperframes import (
    FakeRunner,
    _CountingRenderCommitter,
    _Manifest25RenderFixture,
    _write_executable,
)
from test_production_review import _Manifest25ReviewFixture

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._caption_quality_p6 import run_caption_review_transaction
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
from ai_video.production.ecommerce_ad_coordinator import (
    close_ecommerce_post_media_candidate,
    run_ecommerce_ad_production,
)
from ai_video.production.ecommerce_media_acceptance import (
    EcommerceAcceptanceEvidencePayload,
    EcommerceRequirementFinding,
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
from ai_video.production.project import (
    load_production_project,
    load_review_receipt,
    load_review_request,
)
from ai_video.production.quality_gate_coordinator import (
    UniversalHardCheck,
    UniversalQaApplicability,
    UniversalQaCheckOutcome,
    UniversalQaProfile,
)
from ai_video.production.state_commit import (
    BeginRenderAttemptRequest,
    ProductionStateCommitter,
    recover_production_state,
)
from ecommerce_job_factory import make_ecommerce_handoff

ZERO_HASH = "0" * 64
PLAN_HASH = "a" * 64
TOOL = ToolIdentity(name="whole-ad-evaluator", version="1")


def test_public_closure_refuses_handoff_without_exact_final_output_contract(
    tmp_path,
) -> None:
    compiled_handoff, timeline = _render_canonical_ad(tmp_path)
    policy = _policy(tmp_path, timeline)
    committer = ProductionStateCommitter(tmp_path)
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="ecommerce-missing-final-output-policy",
    )

    with pytest.raises(ValueError, match="final-output"):
        close_ecommerce_post_media_candidate(
            committer=committer,
            handoff=compiled_handoff,
            shot_facades={},
            universal_profile=object(),
            run_hard_check=lambda *_: None,
            run_review_layer=lambda *_: None,
            caption_review_execution=None,
            tool_identity=TOOL,
            evaluate=lambda *_: _passing_payload(),
            review_attempt_id="missing-final-output",
            review_request_id="missing-final-output-request",
            evidence_id="missing-final-output-evidence",
            review_id="missing-final-output-review",
            final_acceptance_id="missing-final-output-acceptance",
            runtime_handoff=make_ecommerce_handoff(),
        )


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


def _policy(
    tmp_path,
    timeline,
    *,
    final_output: FinalOutputContract | None = None,
) -> QaPolicy:
    profile = create_qingyan_ecommerce_acceptance_profile()
    loaded = load_production_project(tmp_path / "project.yaml")
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
            schema_version="2.1",
            artifact_id="ecommerce-e2e-policy",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="ecommerce-e2e-policy",
            source_provenance=(SourceReference(kind="derived", reference="e2e"),),
            policy_id="ecommerce-e2e-policy",
            policy_version="1",
            required_layers=(
                QaLayer.TECHNICAL,
                QaLayer.LAYOUT,
                QaLayer.CAPTION,
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
            semantic_authorities=(TOOL,),
            domain_acceptance=domain,
            caption_policy=make_caption_quality_policy(loaded, timeline),
            final_output=final_output,
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


def _final_output_contract() -> FinalOutputContract:
    return FinalOutputContract(
        goal_id="ecommerce-final-output",
        goal_version="1",
        user_goal="The final ad must show the authored CTA and readable captions.",
        requirements=(
            FinalOutputRequirement(
                requirement_id="cta",
                observable="Authored CTA is present in the final output.",
                proof="evaluator",
            ),
            FinalOutputRequirement(
                requirement_id="captions",
                observable="Applicable captions remain readable in the final output.",
                proof="evaluator",
            ),
        ),
    )


def _whole_ad_payload(
    target,
    *,
    verdicts: dict[str, str],
    request_hash: str | None = None,
) -> EcommerceWholeAdEvaluationPayload:
    contract = _final_output_contract()
    return EcommerceWholeAdEvaluationPayload(
        domain_acceptance=_passing_payload(),
        final_output=FinalOutputObservation(
            contract_hash=contract.contract_hash,
            review_request_content_hash=(
                target.review_request_content_hash
                if request_hash is None
                else request_hash
            ),
            findings=tuple(
                FinalOutputFinding(
                    requirement_id=requirement_id,
                    verdict=verdict,
                    observation="Observed on the exact canonical final render.",
                )
                for requirement_id, verdict in verdicts.items()
            ),
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
    policy = _policy(tmp_path, timeline)
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
        required_review_layers=(
            QaLayer.TECHNICAL,
            QaLayer.LAYOUT,
            QaLayer.CAPTION,
        ),
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
        caption_review_execution=make_caption_review_execution("ecommerce-e2e"),
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
        QaLayer.TECHNICAL.value,
        QaLayer.LAYOUT.value,
    ]
    assert result.render_output_sha256 == bundle.render_state.output.file_sha256
    assert final.final_acceptance_state is not None
    before_replay = (tmp_path / "state/manifest.json").read_bytes()
    replay = run_caption_review_transaction(
        committer=committer,
        execution=make_caption_review_execution("ecommerce-e2e-replay"),
    )
    assert replay.verdict is QaVerdict.PASS
    assert replay.current is True
    assert (tmp_path / "state/manifest.json").read_bytes() == before_replay


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        ("missing", QaVerdict.NOT_EVALUATED),
        ("visual_fail", QaVerdict.FAIL),
        ("partial", QaVerdict.NOT_EVALUATED),
        ("stale", QaVerdict.NOT_EVALUATED),
        ("pass", QaVerdict.PASS),
    ),
)
def test_ecommerce_pass_cannot_replace_exact_complete_final_output_observation(
    tmp_path,
    case: str,
    expected: QaVerdict,
) -> None:
    handoff, timeline = _render_canonical_ad(tmp_path)
    final_output = _final_output_contract()
    policy = _policy(tmp_path, timeline, final_output=final_output)
    committer = ProductionStateCommitter(tmp_path)
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id=f"ecommerce-final-output-{case}-policy",
    )
    for layer in (QaLayer.TECHNICAL, QaLayer.LAYOUT):
        _Manifest25ReviewFixture(
            root=tmp_path,
            committer=committer,
            timeline=timeline,
            policy=policy,
            review_layer=layer,
            review_attempt_id=f"ecommerce-final-output-{case}-{layer.value}",
        ).run_required_review()
    profile = UniversalQaProfile.create(
        profile_id=f"ecommerce-final-output-{case}",
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
        required_review_layers=(
            QaLayer.TECHNICAL,
            QaLayer.LAYOUT,
            QaLayer.CAPTION,
        ),
    )

    def evaluate(target, _profile):
        if case == "missing":
            return _passing_payload()
        verdicts = {
            "cta": "fail" if case == "visual_fail" else "pass",
            **({} if case == "partial" else {"captions": "pass"}),
        }
        return _whole_ad_payload(
            target,
            verdicts=verdicts,
            request_hash="f" * 64 if case == "stale" else None,
        )

    result = run_ecommerce_ad_production(
        handoff,
        facades={},
        activate_final_render=lambda *_: None,
        committer=committer,
        universal_profile=profile,
        run_hard_check=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS,
            current=True,
        ),
        run_review_layer=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS,
            current=True,
        ),
        caption_review_execution=make_caption_review_execution(
            f"ecommerce-final-output-{case}"
        ),
        tool_identity=TOOL,
        evaluate=evaluate,
        review_attempt_id=f"ecommerce-final-output-{case}-semantic",
        review_request_id=f"ecommerce-final-output-{case}-request",
        evidence_id=f"ecommerce-final-output-{case}-evidence",
        review_id=f"ecommerce-final-output-{case}-review",
        final_acceptance_id=f"ecommerce-final-output-{case}-acceptance",
    ).post_media_acceptance

    assert result is not None
    assert result.gate_two.verdict is expected
    assert result.final_acceptance_recorded is (expected is QaVerdict.PASS)
    assert (
        load_production_project(tmp_path / "project.yaml").manifest.final_acceptance_state
        is not None
    ) is (expected is QaVerdict.PASS)


def test_unknown_semantic_review_attempt_blocks_new_ids_and_second_analysis(
    tmp_path,
) -> None:
    handoff, timeline = _render_canonical_ad(tmp_path)
    policy = _policy(tmp_path, timeline)
    committer = ProductionStateCommitter(tmp_path)
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="ecommerce-semantic-unknown-policy",
    )
    for layer in (QaLayer.TECHNICAL, QaLayer.LAYOUT):
        _Manifest25ReviewFixture(
            root=tmp_path,
            committer=committer,
            timeline=timeline,
            policy=policy,
            review_layer=layer,
            review_attempt_id=f"ecommerce-semantic-unknown-{layer.value}",
        ).run_required_review()
    profile = UniversalQaProfile.create(
        profile_id="ecommerce-semantic-unknown",
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
        required_review_layers=(
            QaLayer.TECHNICAL,
            QaLayer.LAYOUT,
            QaLayer.CAPTION,
        ),
    )
    analyzer_calls: list[str] = []

    def interrupted(*_):
        analyzer_calls.append("called")
        raise OSError("semantic evaluator interrupted")

    common = dict(
        facades={},
        activate_final_render=lambda *_: None,
        committer=committer,
        universal_profile=profile,
        run_hard_check=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS,
            current=True,
        ),
        run_review_layer=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS,
            current=True,
        ),
        caption_review_execution=make_caption_review_execution(
            "ecommerce-semantic-unknown"
        ),
        tool_identity=TOOL,
    )
    with pytest.raises(OSError, match="interrupted"):
        run_ecommerce_ad_production(
            handoff,
            evaluate=interrupted,
            review_attempt_id="ecommerce-semantic-unknown-first",
            review_request_id="ecommerce-semantic-unknown-first-request",
            evidence_id="ecommerce-semantic-unknown-first-evidence",
            review_id="ecommerce-semantic-unknown-first-review",
            final_acceptance_id="ecommerce-semantic-unknown-first-acceptance",
            **common,
        )

    with pytest.raises(AiVideoError) as exc_info:
        run_ecommerce_ad_production(
            handoff,
            evaluate=lambda *_: analyzer_calls.append("second") or _passing_payload(),
            review_attempt_id="ecommerce-semantic-unknown-second",
            review_request_id="ecommerce-semantic-unknown-second-request",
            evidence_id="ecommerce-semantic-unknown-second-evidence",
            review_id="ecommerce-semantic-unknown-second-review",
            final_acceptance_id="ecommerce-semantic-unknown-second-acceptance",
            **common,
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    assert analyzer_calls == ["called"]
    assert (
        load_production_project(tmp_path / "project.yaml").manifest.final_acceptance_state
        is None
    )


def test_passed_semantic_receipt_replay_records_acceptance_without_second_analysis(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handoff, timeline = _render_canonical_ad(tmp_path)
    policy = _policy(tmp_path, timeline)
    committer = ProductionStateCommitter(tmp_path)
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="ecommerce-semantic-replay-policy",
    )
    for layer in (QaLayer.TECHNICAL, QaLayer.LAYOUT):
        _Manifest25ReviewFixture(
            root=tmp_path,
            committer=committer,
            timeline=timeline,
            policy=policy,
            review_layer=layer,
            review_attempt_id=f"ecommerce-semantic-replay-{layer.value}",
        ).run_required_review()
    profile = UniversalQaProfile.create(
        profile_id="ecommerce-semantic-replay",
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
        required_review_layers=(
            QaLayer.TECHNICAL,
            QaLayer.LAYOUT,
            QaLayer.CAPTION,
        ),
    )
    analysis_calls: list[str] = []
    original_record = committer.record_final_acceptance

    def fail_acceptance_once(*args, **kwargs):
        raise OSError("acceptance write interrupted")

    common = dict(
        facades={},
        activate_final_render=lambda *_: None,
        committer=committer,
        universal_profile=profile,
        run_hard_check=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS,
            current=True,
        ),
        run_review_layer=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS,
            current=True,
        ),
        caption_review_execution=make_caption_review_execution(
            "ecommerce-semantic-replay"
        ),
        tool_identity=TOOL,
    )
    monkeypatch.setattr(committer, "record_final_acceptance", fail_acceptance_once)
    with pytest.raises(OSError, match="acceptance write interrupted"):
        run_ecommerce_ad_production(
            handoff,
            evaluate=lambda *_: analysis_calls.append("first") or _passing_payload(),
            review_attempt_id="ecommerce-semantic-replay-first",
            review_request_id="ecommerce-semantic-replay-first-request",
            evidence_id="ecommerce-semantic-replay-first-evidence",
            review_id="ecommerce-semantic-replay-first-review",
            final_acceptance_id="ecommerce-semantic-replay-first-acceptance",
            **common,
        )
    monkeypatch.setattr(committer, "record_final_acceptance", original_record)

    drifted_profile = UniversalQaProfile.create(
        profile_id="ecommerce-semantic-replay",
        profile_version="2",
        delivery_profile=timeline.delivery_profile,
        applicability=UniversalQaApplicability(
            has_audio=True,
            has_captions=True,
            has_transitions=True,
            requires_continuity=True,
        ),
        required_hard_checks=(
            *profile.required_hard_checks,
            UniversalHardCheck.CONTINUITY_EVIDENCE,
        ),
        required_review_layers=profile.required_review_layers,
        continuity_requirement_ids=("continuity-product-identity",),
    )
    with pytest.raises(ValueError, match="not current"):
        run_ecommerce_ad_production(
            handoff,
            evaluate=lambda *_: (_ for _ in ()).throw(
                AssertionError("profile drift reran the semantic analyzer")
            ),
            review_attempt_id="ecommerce-semantic-replay-profile-drift",
            review_request_id="ecommerce-semantic-replay-profile-drift-request",
            evidence_id="ecommerce-semantic-replay-profile-drift-evidence",
            review_id="ecommerce-semantic-replay-profile-drift-review",
            final_acceptance_id="ecommerce-semantic-replay-profile-drift-acceptance",
            **{**common, "universal_profile": drifted_profile},
        )

    result = run_ecommerce_ad_production(
        handoff,
        evaluate=lambda *_: analysis_calls.append("second") or _passing_payload(),
        review_attempt_id="ecommerce-semantic-replay-second",
        review_request_id="ecommerce-semantic-replay-second-request",
        evidence_id="ecommerce-semantic-replay-second-evidence",
        review_id="ecommerce-semantic-replay-second-review",
        final_acceptance_id="ecommerce-semantic-replay-second-acceptance",
        **common,
    ).post_media_acceptance

    assert result is not None
    assert result.final_acceptance_recorded is True
    assert analysis_calls == ["first"]
    before_completed_replay = (tmp_path / "state/manifest.json").read_bytes()
    monkeypatch.setattr(committer, "record_final_acceptance", fail_acceptance_once)

    completed_replay = run_ecommerce_ad_production(
        handoff,
        evaluate=lambda *_: analysis_calls.append("third") or _passing_payload(),
        review_attempt_id="ecommerce-semantic-replay-third",
        review_request_id="ecommerce-semantic-replay-third-request",
        evidence_id="ecommerce-semantic-replay-third-evidence",
        review_id="ecommerce-semantic-replay-third-review",
        final_acceptance_id="ecommerce-semantic-replay-third-acceptance",
        **common,
    ).post_media_acceptance

    assert completed_replay is not None
    assert completed_replay.final_acceptance_recorded is True
    assert analysis_calls == ["first"]
    assert (tmp_path / "state/manifest.json").read_bytes() == before_completed_replay


def test_noncanonical_file_cannot_be_supplied_as_post_media_candidate() -> None:
    assert "file" not in run_ecommerce_ad_production.__annotations__
    assert "mp4" not in run_ecommerce_ad_production.__annotations__
    assert "project_root" not in run_ecommerce_ad_production.__annotations__
    assert "timeline" not in run_ecommerce_ad_production.__annotations__
    assert "universal_result" not in run_ecommerce_ad_production.__annotations__


def test_changed_active_render_bytes_cannot_enter_gate_closure(tmp_path) -> None:
    handoff, timeline = _render_canonical_ad(tmp_path)
    policy = _policy(tmp_path, timeline)
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
    policy = _policy(tmp_path, timeline)
    committer = ProductionStateCommitter(tmp_path)
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="ecommerce-invalid-policy",
    )
    for layer in (QaLayer.TECHNICAL, QaLayer.LAYOUT):
        _Manifest25ReviewFixture(
            root=tmp_path,
            committer=committer,
            timeline=timeline,
            policy=policy,
            review_layer=layer,
            review_attempt_id=f"ecommerce-invalid-{layer.value}",
        ).run_required_review()
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
        required_review_layers=(
            QaLayer.TECHNICAL,
            QaLayer.LAYOUT,
            QaLayer.CAPTION,
        ),
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
        caption_review_execution=make_caption_review_execution(
            "ecommerce-invalid"
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
    repaired_evidence_calls: list[str] = []
    repaired = run_ecommerce_ad_production(
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
        caption_review_execution=make_caption_review_execution(
            "ecommerce-invalid-repair"
        ),
        tool_identity=TOOL,
        evaluate=lambda *_: (
            repaired_evidence_calls.append("called") or _passing_payload()
        ),
        review_attempt_id="ecommerce-invalid-repair-semantic",
        review_request_id="ecommerce-invalid-repair-request",
        evidence_id="ecommerce-invalid-repair-evidence",
        review_id="ecommerce-invalid-repair-review",
        final_acceptance_id="ecommerce-invalid-repair-final",
    ).post_media_acceptance

    assert repaired is not None
    assert repaired.gate_two.verdict is QaVerdict.PASS
    assert repaired.final_acceptance_recorded is True
    assert repaired_evidence_calls == ["called"]


def test_captioned_closure_without_caption_execution_stops_before_gate_two(
    tmp_path,
) -> None:
    handoff, timeline = _render_canonical_ad(tmp_path)
    committer = ProductionStateCommitter(tmp_path)
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    policy = _policy(tmp_path, timeline)
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="ecommerce-missing-caption-policy",
    )
    profile = UniversalQaProfile.create(
        profile_id="ecommerce-missing-caption",
        profile_version="2",
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
        required_review_layers=(
            QaLayer.TECHNICAL,
            QaLayer.LAYOUT,
            QaLayer.CAPTION,
        ),
    )
    gate_two_calls: list[str] = []

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
        evaluate=lambda *_: gate_two_calls.append("called"),
        review_attempt_id="ecommerce-missing-caption-semantic",
        review_request_id="ecommerce-missing-caption-request",
        evidence_id="ecommerce-missing-caption-evidence",
        review_id="ecommerce-missing-caption-review",
        final_acceptance_id="ecommerce-missing-caption-final",
    )

    result = production.post_media_acceptance
    assert result is not None
    assert result.gate_two.verdict is QaVerdict.NOT_EVALUATED
    assert result.p6_semantic_receipt_recorded is False
    assert result.final_acceptance_recorded is False
    assert gate_two_calls == []
    assert all(
        item.layer is not QaLayer.CAPTION
        for item in load_production_project(
            tmp_path / "project.yaml"
        ).manifest.active_review_receipts
    )


def test_tampered_caption_request_chain_blocks_standard_project_reopen(
    tmp_path,
) -> None:
    _, timeline = _render_canonical_ad(tmp_path)
    committer = ProductionStateCommitter(tmp_path)
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    committer.activate_qa_policy(
        _policy(tmp_path, timeline),
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="ecommerce-caption-tamper-policy",
    )
    outcome = run_caption_review_transaction(
        committer=committer,
        execution=make_caption_review_execution("ecommerce-caption-tamper"),
    )
    assert outcome.verdict is QaVerdict.PASS
    current = load_production_project(tmp_path / "project.yaml")
    pointer = next(
        item
        for item in current.manifest.active_review_receipts
        if item.layer is QaLayer.CAPTION
    )
    receipt = load_review_receipt(tmp_path, pointer)
    request_path = tmp_path / receipt.review_request.path
    request_path.write_bytes(request_path.read_bytes() + b" ")

    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")


def test_recovered_unknown_caption_attempt_blocks_new_execution(tmp_path) -> None:
    _, timeline = _render_canonical_ad(tmp_path)
    committer = ProductionStateCommitter(tmp_path)
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    committer.activate_qa_policy(
        _policy(tmp_path, timeline),
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="ecommerce-caption-unknown-policy",
    )
    failing = replace(
        make_caption_review_execution("ecommerce-caption-unknown"),
        evaluator=lambda *_: (_ for _ in ()).throw(RuntimeError("interrupted")),
    )
    with pytest.raises(RuntimeError, match="interrupted"):
        run_caption_review_transaction(committer=committer, execution=failing)
    recover_production_state(tmp_path)
    before = (tmp_path / "state/manifest.json").read_bytes()

    with pytest.raises(AiVideoError) as exc_info:
        run_caption_review_transaction(
            committer=committer,
            execution=make_caption_review_execution(
                "ecommerce-caption-after-unknown"
            ),
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_newer_unknown_caption_attempt_blocks_active_receipt_replay(tmp_path) -> None:
    _, timeline = _render_canonical_ad(tmp_path)
    committer = ProductionStateCommitter(tmp_path)
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    committer.activate_qa_policy(
        _policy(tmp_path, timeline),
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="ecommerce-caption-active-unknown-policy",
    )
    outcome = run_caption_review_transaction(
        committer=committer,
        execution=make_caption_review_execution("ecommerce-caption-active"),
    )
    assert outcome.verdict is QaVerdict.PASS
    current = load_production_project(tmp_path / "project.yaml")
    pointer = next(
        item
        for item in current.manifest.active_review_receipts
        if item.layer is QaLayer.CAPTION
    )
    receipt = load_review_receipt(tmp_path, pointer)
    original = load_review_request(tmp_path, receipt.review_request)
    unknown_request = seal_artifact(
        original.model_copy(
            update={
                "artifact_id": "ecommerce-caption-newer-unknown-request",
                "request_id": "ecommerce-caption-newer-unknown-request",
                "creation_receipt_id": "ecommerce-caption-newer-unknown-request",
                "revision": original.revision + 1,
                "content_hash": ZERO_HASH,
                "base_manifest_revision": current.manifest.manifest_revision,
            }
        )
    )
    committer.begin_review(
        unknown_request,
        attempt_id="ecommerce-caption-newer-unknown",
    )
    recover_production_state(tmp_path)
    before = (tmp_path / "state/manifest.json").read_bytes()

    with pytest.raises(AiVideoError) as exc_info:
        run_caption_review_transaction(
            committer=committer,
            execution=make_caption_review_execution(
                "ecommerce-caption-replay-masked"
            ),
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    assert (tmp_path / "state/manifest.json").read_bytes() == before
