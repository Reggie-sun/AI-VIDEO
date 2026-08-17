"""Pure P6 review, freshness, repair-scope, and acceptance decisions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import EvidenceStrength, QaLayer, QaVerdict, VisualStrategy


@dataclass(frozen=True)
class ReviewIdentity:
    dependency_graph_revision_id: str
    dependency_states_hash: str
    render_state_content_hash: str
    render_output_sha256: str
    timeline_fingerprint: str
    qa_policy_content_hash: str


def review_desired_fingerprint(identity: ReviewIdentity, layer: QaLayer) -> str:
    return canonical_sha256({**identity.__dict__, "layer": layer.value})


def is_review_current(
    *, receipt_identity: ReviewIdentity, current_identity: ReviewIdentity, layer: QaLayer
) -> bool:
    return review_desired_fingerprint(receipt_identity, layer) == review_desired_fingerprint(
        current_identity, layer
    )


def adjudicate_layer(
    layer: QaLayer,
    evidence: Sequence[Mapping[str, object]],
) -> QaVerdict:
    """Apply deterministic policy decisions to already-collected evidence."""
    if not evidence:
        return QaVerdict.NOT_EVALUATED
    if layer is QaLayer.SEMANTIC:
        strengths = {item.get("strength") for item in evidence}
        if not strengths.intersection(
            {EvidenceStrength.EXPLICIT_EVALUATOR.value, EvidenceStrength.HUMAN.value}
        ):
            return QaVerdict.NOT_EVALUATED
    for item in evidence:
        if item.get("result") == "fail":
            return QaVerdict.FAIL
        if item.get("result") not in {"pass", "fail"}:
            return QaVerdict.NOT_EVALUATED
    return QaVerdict.PASS


def adjudicate_visual_motion(
    *,
    visual_strategy: VisualStrategy,
    unique_frame_ratio: float,
    motion_expectation: Mapping[str, object] | None,
    measured_delta_milli: int | None = None,
) -> QaVerdict:
    """Judge only explicit strategy expectations; diversity alone is not a failure."""
    if visual_strategy is VisualStrategy.STATIC_IMAGE:
        return QaVerdict.PASS
    if visual_strategy in {VisualStrategy.IMAGE_MOTION, VisualStrategy.MOTION_GRAPHICS}:
        if motion_expectation is None or measured_delta_milli is None:
            return QaVerdict.NOT_EVALUATED
        minimum = int(motion_expectation["minimum_measured_delta_milli"])
        tolerance = int(motion_expectation.get("tolerance_milli", 0))
        return (
            QaVerdict.PASS
            if measured_delta_milli + tolerance >= minimum
            else QaVerdict.FAIL
        )
    return QaVerdict.FAIL if unique_frame_ratio == 0 else QaVerdict.PASS


def validate_repair_scope(
    *, expected_node_ids: Sequence[str], actual_node_ids: Sequence[str]
) -> tuple[str, ...]:
    expected = tuple(sorted(set(expected_node_ids)))
    actual = tuple(sorted(set(actual_node_ids)))
    if actual != expected:
        raise AiVideoError(
            ErrorCode.REPAIR_SCOPE_INVALID,
            "Repair invalidation does not match the exact approved graph scope.",
        )
    return actual


def evaluate_final_acceptance(
    *,
    required_layers: Sequence[QaLayer],
    verdicts: Mapping[QaLayer, QaVerdict],
    receipts_current: bool,
) -> QaVerdict:
    if not receipts_current:
        raise AiVideoError(
            ErrorCode.REVIEW_NOT_CURRENT,
            "Final acceptance requires fresh review receipts for current render state.",
        )
    if any(verdicts.get(layer) is not QaVerdict.PASS for layer in required_layers):
        raise AiVideoError(
            ErrorCode.FINAL_ACCEPTANCE_INVALID,
            "Every required QA layer must have a fresh pass receipt.",
        )
    return QaVerdict.PASS
