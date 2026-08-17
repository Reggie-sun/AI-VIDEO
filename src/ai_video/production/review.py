"""Pure P6 review, freshness, repair-scope, and acceptance decisions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    EvidenceStrength,
    QaLayer,
    QaPolicy,
    QaVerdict,
    ReviewEvidence,
    VisualStrategy,
)


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


def adjudicate_review_evidence(
    policy: QaPolicy, layer: QaLayer, evidence: Sequence[ReviewEvidence]
) -> QaVerdict:
    """Derive verdict from selected policy and typed raw measurements."""
    if not evidence or any(
        item.layer is not layer
        or item.measured_payload.get("coverage_complete") is not True
        for item in evidence
    ):
        return QaVerdict.NOT_EVALUATED
    if layer is QaLayer.SEMANTIC:
        authorized = [
            item
            for item in evidence
            if item.strength
            in {EvidenceStrength.EXPLICIT_EVALUATOR, EvidenceStrength.HUMAN}
            and item.tool_identity in policy.semantic_authorities
            and isinstance(item.measured_payload.get("evaluator_identity"), str)
            and item.measured_payload.get("evaluator_identity")
            == f"{item.tool_identity.name}@{item.tool_identity.version}"
        ]
        if not authorized:
            return QaVerdict.NOT_EVALUATED
        return (
            QaVerdict.PASS
            if all(item.measured_payload.get("semantic_match") is True for item in authorized)
            else QaVerdict.FAIL
        )
    if layer is QaLayer.TECHNICAL:
        thresholds = policy.technical_thresholds
        for item in evidence:
            payload = item.measured_payload
            required = {
                "minimum_luma_milli",
                "audio_peak_millidb",
                "expects_audio",
                "windows",
            }
            if not required.issubset(payload):
                return QaVerdict.NOT_EVALUATED
            if (
                payload["expects_audio"] is True
                and not isinstance(payload["audio_peak_millidb"], int)
            ):
                return QaVerdict.NOT_EVALUATED
            if (
                isinstance(payload.get("minimum_luma_milli"), int)
                and payload["minimum_luma_milli"] <= thresholds.black_luma_max_milli
            ):
                return QaVerdict.FAIL
            if payload.get("expects_audio") is True and (
                isinstance(payload.get("audio_peak_millidb"), int)
                and payload["audio_peak_millidb"]
                <= thresholds.silence_peak_max_millidb
            ):
                return QaVerdict.FAIL
            if isinstance(payload.get("audio_peak_millidb"), int) and (
                payload["audio_peak_millidb"]
                >= thresholds.clipping_peak_min_millidb
            ):
                return QaVerdict.FAIL
            if payload.get("frozen_required_motion") is True:
                return QaVerdict.FAIL
            windows = payload["windows"]
            if not isinstance(windows, tuple | list):
                return QaVerdict.NOT_EVALUATED
            for window in windows:
                if not isinstance(window, Mapping):
                    return QaVerdict.NOT_EVALUATED
                if window.get("status") == "not_evaluated":
                    return QaVerdict.NOT_EVALUATED
                if window.get("visual_strategy") in {
                    VisualStrategy.GENERATED_VIDEO.value,
                    VisualStrategy.EXISTING_VIDEO.value,
                } and int(window.get("unique_frame_count", 0)) <= 1:
                    return QaVerdict.FAIL
        return QaVerdict.PASS
    if layer is QaLayer.LAYOUT:
        rules = policy.layout_rules
        for item in evidence:
            payload = item.measured_payload
            required = {
                "caption_overflow_milli",
                "safe_area_inset_milli",
                "layer_collision_count",
                "transition_boundary_violation_count",
            }
            if not required.issubset(payload):
                return QaVerdict.NOT_EVALUATED
            if (
                isinstance(payload.get("caption_overflow_milli"), int)
                and payload["caption_overflow_milli"]
                > rules.caption_overflow_tolerance_milli
            ) or (
                isinstance(payload.get("safe_area_inset_milli"), int)
                and payload["safe_area_inset_milli"] < rules.safe_area_inset_milli
            ) or int(payload.get("layer_collision_count", 0)) > 0 or int(
                payload.get("transition_boundary_violation_count", 0)
            ) > 0:
                return QaVerdict.FAIL
        return QaVerdict.PASS
    if layer is QaLayer.STRATEGY:
        if any(
            not {"evaluated_strategy_ids", "strategy_mismatch"}.issubset(
                item.measured_payload
            )
            for item in evidence
        ):
            return QaVerdict.NOT_EVALUATED
        return (
            QaVerdict.FAIL
            if any(item.measured_payload.get("strategy_mismatch") is True for item in evidence)
            else QaVerdict.PASS
        )
    return QaVerdict.NOT_EVALUATED


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
