from __future__ import annotations

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.models import QaLayer, QaVerdict, VisualStrategy
from ai_video.production.review import (
    ReviewIdentity,
    adjudicate_layer,
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
