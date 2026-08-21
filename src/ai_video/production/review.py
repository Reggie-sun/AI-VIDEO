"""Pure P6 review, freshness, repair-scope, and acceptance decisions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import Field, SerializerFunctionWrapHandler, model_serializer, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    EvidenceStrength,
    LoadedProductionProject,
    MotionExpectation,
    QaLayer,
    QaPolicy,
    QaVerdict,
    ReviewEvidence,
    ResolvedTimeline,
    StrictModel,
    TechnicalReviewContext,
    TechnicalReviewWindow,
    ToolIdentity,
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


class ContinuityCheckMeasurement(StrictModel):
    status: Literal["match", "mismatch", "not_evaluated"]
    expected: str = Field(min_length=1)
    observed: str | None = None
    confidence_milli: int | None = Field(default=None, ge=0, le=1000)
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_observation(self) -> "ContinuityCheckMeasurement":
        evaluated = self.status != "not_evaluated"
        if evaluated != (self.observed is not None and self.confidence_milli is not None):
            raise ValueError("evaluated continuity checks require observed value and confidence")
        return self


class ContinuitySampledFrameMeasurement(StrictModel):
    frame_index: int = Field(strict=True, ge=0)
    frame_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ContinuityTransitionMeasurement(StrictModel):
    start_frame_index: int = Field(strict=True, ge=0)
    end_frame_index: int = Field(strict=True, ge=0)
    changed_pixel_count: int = Field(strict=True, ge=0)
    centroid_x_milli: int | None = Field(default=None, ge=0, le=1000)
    left_edge_touched: bool
    right_edge_touched: bool


class GeneratedShotContinuityMeasurements(StrictModel):
    measurement_contract_version: Literal["hybrid-continuity-evaluator-v1"]
    sampler: ToolIdentity
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    sample_width: int = Field(strict=True, gt=0)
    sample_height: int = Field(strict=True, gt=0)
    sampled_frames: tuple[ContinuitySampledFrameMeasurement, ...] = Field(min_length=2)
    transitions: tuple[ContinuityTransitionMeasurement, ...]
    identity: ContinuityCheckMeasurement
    camera_axis: ContinuityCheckMeasurement
    framing: ContinuityCheckMeasurement
    motion_direction: ContinuityCheckMeasurement
    entrance_state: ContinuityCheckMeasurement
    exit_state: ContinuityCheckMeasurement
    unexpected_reentry: ContinuityCheckMeasurement

    @model_validator(mode="after")
    def _validate_samples(self) -> "GeneratedShotContinuityMeasurements":
        indices = tuple(item.frame_index for item in self.sampled_frames)
        if indices != tuple(sorted(set(indices))):
            raise ValueError("continuity sampled frame indices must be unique and ordered")
        expected_transitions = tuple(zip(indices, indices[1:]))
        observed_transitions = tuple(
            (item.start_frame_index, item.end_frame_index) for item in self.transitions
        )
        if observed_transitions != expected_transitions:
            raise ValueError("continuity transitions must bind adjacent sampled frames")
        return self


class GeneratedShotContinuityEvidence(StrictModel):
    """Raw evaluator evidence for one exact continuity-bound generated Shot."""

    source_shot_id: str = Field(min_length=1)
    target_shot_id: str = Field(min_length=1)
    target_shot_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    resolved_generation_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    continuity_constraints_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    qa_policy_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluator: ToolIdentity
    strength: EvidenceStrength
    coverage_complete: bool
    identity_match: bool
    camera_axis_match: bool
    framing_match: bool
    motion_direction_match: bool
    entrance_state_match: bool
    exit_state_match: bool
    unexpected_reentry: bool
    raw_measurements: GeneratedShotContinuityMeasurements | None = None
    rationale: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_evidence(self) -> "GeneratedShotContinuityEvidence":
        if self.strength not in {
            EvidenceStrength.EXPLICIT_EVALUATOR,
            EvidenceStrength.HUMAN,
        }:
            raise ValueError(
                "generated Shot continuity requires explicit evaluator or human evidence"
            )
        if self.raw_measurements is not None:
            measurements = self.raw_measurements
            statuses = {
                "identity_match": measurements.identity.status,
                "camera_axis_match": measurements.camera_axis.status,
                "framing_match": measurements.framing.status,
                "motion_direction_match": measurements.motion_direction.status,
                "entrance_state_match": measurements.entrance_state.status,
                "exit_state_match": measurements.exit_state.status,
            }
            if measurements.artifact_sha256 != self.artifact_sha256 or any(
                getattr(self, field) != (status == "match")
                for field, status in statuses.items()
            ):
                raise ValueError("continuity measurements do not match evidence fields")
            reentry_status = measurements.unexpected_reentry.status
            if self.unexpected_reentry != (reentry_status == "mismatch"):
                raise ValueError("continuity re-entry measurement does not match evidence")
            complete = all(
                status != "not_evaluated"
                for status in (*statuses.values(), reentry_status)
            )
            if self.coverage_complete != complete:
                raise ValueError("continuity measurement coverage does not match evidence")
        expected = canonical_sha256(
            {
                "schema": "generated-shot-continuity-evidence/1",
                **self.model_dump(
                    mode="json", exclude={"content_hash"}, exclude_none=True
                ),
            }
        )
        if self.content_hash != expected:
            raise ValueError("generated Shot continuity evidence hash is invalid")
        return self

    @model_serializer(mode="wrap")
    def _serialize_compatible_variant(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.raw_measurements is None:
            data.pop("raw_measurements", None)
        return data

    @classmethod
    def create(cls, **values: object) -> "GeneratedShotContinuityEvidence":
        data = dict(values)
        if data.get("raw_measurements") is not None:
            data["raw_measurements"] = GeneratedShotContinuityMeasurements.model_validate(
                data["raw_measurements"]
            )
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            {
                "schema": "generated-shot-continuity-evidence/1",
                **candidate.model_dump(
                    mode="json",
                    exclude={"content_hash"},
                    exclude_none=True,
                    warnings=False,
                ),
            }
        )
        return cls.model_validate(data)


def adjudicate_generated_shot_continuity(
    evidence: GeneratedShotContinuityEvidence,
) -> QaVerdict:
    """Derive a verdict from raw continuity evidence; evaluators never self-verdict."""

    if evidence.raw_measurements is not None and any(
        item.status == "mismatch"
        for item in (
            evidence.raw_measurements.identity,
            evidence.raw_measurements.camera_axis,
            evidence.raw_measurements.framing,
            evidence.raw_measurements.motion_direction,
            evidence.raw_measurements.entrance_state,
            evidence.raw_measurements.exit_state,
            evidence.raw_measurements.unexpected_reentry,
        )
    ):
        return QaVerdict.FAIL
    if not evidence.coverage_complete:
        return QaVerdict.NOT_EVALUATED
    if (
        evidence.identity_match
        and evidence.camera_axis_match
        and evidence.framing_match
        and evidence.motion_direction_match
        and evidence.entrance_state_match
        and evidence.exit_state_match
        and not evidence.unexpected_reentry
    ):
        return QaVerdict.PASS
    return QaVerdict.FAIL


def build_technical_review_context(
    bundle: LoadedProductionProject,
    timeline: ResolvedTimeline,
    *,
    render_output_sha256: str,
    measurement_contract_version: str,
) -> TechnicalReviewContext:
    """Derive complete Shot windows only from verified project/timeline truth."""
    shots = {item.shot_id: item for item in bundle.shots}
    grouped: dict[str, list[object]] = {}
    order: list[str] = []
    for span in sorted(timeline.visual_spans, key=lambda item: (item.start_frame, item.z_index)):
        if span.shot_id not in grouped:
            grouped[span.shot_id] = []
            order.append(span.shot_id)
        grouped[span.shot_id].append(span)
    windows: list[TechnicalReviewWindow] = []
    for shot_id in order:
        shot = shots.get(shot_id)
        spans = grouped[shot_id]
        if shot is None or not spans:
            raise ValueError("ResolvedTimeline contains an unknown or empty Shot window")
        start_frame = min(item.start_frame for item in spans)
        end_frame = max(item.start_frame + item.duration_frames for item in spans)
        start_sample = min(item.start_sample for item in spans)
        end_sample = max(item.start_sample + item.duration_samples for item in spans)
        expects_audio = any(
            item.start_sample < end_sample
            and item.start_sample + item.duration_samples > start_sample
            for item in timeline.audio_spans
        )
        expectation = None
        if shot.visual_strategy in {
            VisualStrategy.IMAGE_MOTION,
            VisualStrategy.MOTION_GRAPHICS,
        } and shot.motion_directives:
            directive = shot.motion_directives[0]
            expectation = MotionExpectation(
                directive_kind=directive.kind,
                directive_parameters_fingerprint=canonical_sha256(
                    directive.parameters
                ),
                measurement_kind=(
                    "layer_state_delta"
                    if shot.visual_strategy is VisualStrategy.MOTION_GRAPHICS
                    else "transform_delta"
                ),
                minimum_measured_delta_milli=1,
                tolerance_milli=0,
            )
        windows.append(
            TechnicalReviewWindow(
                shot_id=shot_id,
                visual_strategy=shot.visual_strategy,
                start_frame=start_frame,
                end_frame_exclusive=end_frame,
                expects_audio=expects_audio,
                visual_span_ids=tuple(sorted(item.layer_id for item in spans)),
                motion_expectation=expectation,
            )
        )
    if (
        not windows
        or windows[0].start_frame != 0
        or windows[-1].end_frame_exclusive != timeline.total_frames
        or any(
            left.end_frame_exclusive != right.start_frame
            for left, right in zip(windows, windows[1:])
        )
    ):
        raise ValueError("Technical review windows must cover the exact timeline once")
    return TechnicalReviewContext(
        render_output_sha256=render_output_sha256,
        timeline_fingerprint=timeline.composition_fingerprint,
        windows=tuple(windows),
        measurement_contract_version=measurement_contract_version,
    )


def validate_technical_review_context(
    context: TechnicalReviewContext,
    bundle: LoadedProductionProject,
    timeline: ResolvedTimeline,
    *,
    render_output_sha256: str,
) -> TechnicalReviewContext:
    expected = build_technical_review_context(
        bundle,
        timeline,
        render_output_sha256=render_output_sha256,
        measurement_contract_version=context.measurement_contract_version,
    )
    if context != expected:
        raise AiVideoError(
            ErrorCode.PRODUCTION_STATE_INVALID,
            "Technical review context does not match verified Shot/timeline truth.",
        )
    return context


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
