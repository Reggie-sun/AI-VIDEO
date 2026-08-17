from __future__ import annotations

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.models import (
    EvidenceStrength,
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    QaVerdict,
    ReviewEvidence,
    VisualStrategy,
)
from ai_video.production.review import (
    ReviewIdentity,
    adjudicate_layer,
    adjudicate_review_evidence,
    adjudicate_visual_motion,
    evaluate_final_acceptance,
    is_review_current,
)


def identity(**changes: str) -> ReviewIdentity:
    values = {
        "dependency_graph_revision_id": "0" * 64,
        "dependency_states_hash": "1" * 64,
        "render_state_content_hash": "2" * 64,
        "render_output_sha256": "3" * 64,
        "timeline_fingerprint": "4" * 64,
        "qa_policy_content_hash": "5" * 64,
    }
    values.update(changes)
    return ReviewIdentity(**values)


@pytest.mark.parametrize(
    "field",
    [
        "dependency_graph_revision_id",
        "render_state_content_hash",
        "render_output_sha256",
        "timeline_fingerprint",
        "qa_policy_content_hash",
    ],
)
def test_identity_drift_makes_review_stale(field):
    assert not is_review_current(
        receipt_identity=identity(),
        current_identity=identity(**{field: "f" * 64}),
        layer=QaLayer.TECHNICAL,
    )


def test_semantic_requires_explicit_evaluator_or_human_evidence():
    assert adjudicate_layer(
        QaLayer.SEMANTIC, [{"strength": "measured", "result": "pass"}]
    ) is QaVerdict.NOT_EVALUATED
    assert adjudicate_layer(
        QaLayer.SEMANTIC,
        [{"strength": "explicit_evaluator", "result": "pass"}],
    ) is QaVerdict.PASS


def policy():
    return QaPolicy.model_construct(
        technical_thresholds=QaTechnicalThresholds(
            black_luma_max_milli=10,
            silence_peak_max_millidb=-60_000,
            clipping_peak_min_millidb=-100,
        ),
        layout_rules=QaLayoutRules(
            safe_area_inset_milli=50,
            caption_overflow_tolerance_milli=0,
        ),
    )


def evidence(layer, strength, **payload):
    return ReviewEvidence.model_construct(
        layer=layer,
        strength=strength,
        measured_payload={"coverage_complete": True, **payload},
    )


def test_selected_policy_recomputes_technical_and_layout_verdicts():
    assert adjudicate_review_evidence(
        policy(),
        QaLayer.TECHNICAL,
        (evidence(
            QaLayer.TECHNICAL,
            EvidenceStrength.MEASURED,
            minimum_luma_milli=9,
            black_ranges=[],
            silence_ranges=[],
            audio_peak_millidb=-1000,
            expects_audio=False,
            windows=[],
        ),),
    ) is QaVerdict.FAIL
    assert adjudicate_review_evidence(
        policy(),
        QaLayer.LAYOUT,
        (evidence(
            QaLayer.LAYOUT,
            EvidenceStrength.RENDERER_BOUND,
            caption_overflow_milli=1,
            safe_area_inset_milli=50,
            layer_collision_count=0,
            transition_boundary_violation_count=0,
        ),),
    ) is QaVerdict.FAIL


def test_selected_policy_fails_closed_when_required_measurement_is_absent():
    assert adjudicate_review_evidence(
        policy(),
        QaLayer.TECHNICAL,
        (evidence(
            QaLayer.TECHNICAL,
            EvidenceStrength.MEASURED,
            black_ranges=[],
            silence_ranges=[],
            expects_audio=True,
            windows=[],
        ),),
    ) is QaVerdict.NOT_EVALUATED


def test_semantic_typed_evidence_requires_evaluator_identity():
    assert adjudicate_review_evidence(
        policy(),
        QaLayer.SEMANTIC,
        (evidence(QaLayer.SEMANTIC, EvidenceStrength.EXPLICIT_EVALUATOR, semantic_match=True),),
    ) is QaVerdict.NOT_EVALUATED
    assert adjudicate_review_evidence(
        policy(),
        QaLayer.SEMANTIC,
        (evidence(
            QaLayer.SEMANTIC,
            EvidenceStrength.EXPLICIT_EVALUATOR,
            evaluator_identity="fixture-evaluator-v1",
            semantic_match=True,
        ),),
    ) is QaVerdict.PASS


@pytest.mark.parametrize(
    ("layer", "issue_id"),
    [
        (QaLayer.TECHNICAL, "frozen_frames"),
        (QaLayer.TECHNICAL, "black_frames"),
        (QaLayer.TECHNICAL, "silent_audio"),
        (QaLayer.TECHNICAL, "clipped_audio"),
        (QaLayer.LAYOUT, "caption_overflow"),
        (QaLayer.LAYOUT, "safe_area_violation"),
        (QaLayer.LAYOUT, "layer_collision"),
        (QaLayer.LAYOUT, "transition_boundary"),
        (QaLayer.STRATEGY, "strategy_mismatch"),
    ],
)
def test_measured_failures_fail_their_owned_layer(layer, issue_id):
    evidence = [{"strength": "measured", "result": "fail", "issue_id": issue_id}]
    assert adjudicate_layer(layer, evidence) is QaVerdict.FAIL


def test_static_and_explicit_low_motion_strategy_are_not_misclassified():
    assert adjudicate_visual_motion(
        visual_strategy=VisualStrategy.STATIC_IMAGE,
        unique_frame_ratio=0.01,
        motion_expectation=None,
    ) is QaVerdict.PASS
    expectation = {"minimum_measured_delta_milli": 10, "tolerance_milli": 2}
    assert adjudicate_visual_motion(
        visual_strategy=VisualStrategy.IMAGE_MOTION,
        unique_frame_ratio=0.01,
        motion_expectation=expectation,
        measured_delta_milli=8,
    ) is QaVerdict.PASS
    assert adjudicate_visual_motion(
        visual_strategy=VisualStrategy.MOTION_GRAPHICS,
        unique_frame_ratio=0.01,
        motion_expectation=expectation,
        measured_delta_milli=7,
    ) is QaVerdict.FAIL


def test_final_acceptance_fails_closed_for_stale_or_missing_pass():
    with pytest.raises(AiVideoError):
        evaluate_final_acceptance(
            required_layers=(QaLayer.TECHNICAL,),
            verdicts={QaLayer.TECHNICAL: QaVerdict.PASS},
            receipts_current=False,
        )
    with pytest.raises(AiVideoError):
        evaluate_final_acceptance(
            required_layers=(QaLayer.TECHNICAL, QaLayer.SEMANTIC),
            verdicts={QaLayer.TECHNICAL: QaVerdict.PASS},
            receipts_current=True,
        )
