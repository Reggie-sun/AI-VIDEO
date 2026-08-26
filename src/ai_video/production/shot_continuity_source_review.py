"""Pure, content-addressed P6 evidence for qualification source boundaries."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from io import BytesIO
import math
from typing import TYPE_CHECKING, Literal, Protocol

import numpy as np
from PIL import Image
from pydantic import Field, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import QaVerdict, StrictModel, ToolIdentity

if TYPE_CHECKING:
    from ai_video.production.local_video import LocalVideoFetchReceipt
    from ai_video.production.video import (
        ResolvedVideoGenerationRequest,
        VideoFetchReceipt,
    )
    from ai_video.production.video_artifact import MeasuredVideoMetadata
    from ai_video.production.video_transition import P0QualificationPreparedReceipt


_SHA256 = r"^[0-9a-f]{64}$"


class SourceBoundaryMeasurementContractV1(StrictModel):
    """Frozen interpretation of the pre-existing P0 boundary thresholds."""

    schema_version: Literal["1"]
    p0_qualification_receipt_hash: str = Field(pattern=_SHA256)
    p0_rubric_hash: str = Field(pattern=_SHA256)
    first_frame_asset_id: str = Field(min_length=1)
    first_frame_sha256: str = Field(pattern=_SHA256)
    last_frame_asset_id: str = Field(min_length=1)
    last_frame_sha256: str = Field(pattern=_SHA256)
    sample_width: int = Field(strict=True, gt=0)
    sample_height: int = Field(strict=True, gt=0)
    decoder: ToolIdentity
    frame_selection: Literal["decoded-frame-0-and-terminal"]
    video_pixel_format: Literal["rgb24"]
    anchor_resize: Literal["pillow-lanczos-no-crop"]
    psnr_channel: Literal["rgb"]
    psnr_threshold_millidb: Literal[30000]
    ssim_channel: Literal["bt709-luma"]
    ssim_window: Literal["uniform-7x7-sample-covariance"]
    ssim_data_range: Literal[255]
    ssim_threshold_millionths: Literal[900000]
    comparison_rounding: Literal["half-even-to-integer"]
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_hash(self) -> "SourceBoundaryMeasurementContractV1":
        expected = canonical_sha256(
            {
                "schema": "source-boundary-measurement-contract/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        )
        if self.content_hash != expected:
            raise ValueError("source boundary measurement contract hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "SourceBoundaryMeasurementContractV1":
        data = {
            "schema_version": "1",
            **values,
            "frame_selection": "decoded-frame-0-and-terminal",
            "video_pixel_format": "rgb24",
            "anchor_resize": "pillow-lanczos-no-crop",
            "psnr_channel": "rgb",
            "psnr_threshold_millidb": 30_000,
            "ssim_channel": "bt709-luma",
            "ssim_window": "uniform-7x7-sample-covariance",
            "ssim_data_range": 255,
            "ssim_threshold_millionths": 900_000,
            "comparison_rounding": "half-even-to-integer",
        }
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            {
                "schema": "source-boundary-measurement-contract/1",
                **provisional.model_dump(
                    mode="json", exclude={"content_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


class SourceBoundaryHumanDecisionV1(StrictModel):
    schema_version: Literal["1"]
    resolved_generation_hash: str = Field(pattern=_SHA256)
    artifact_sha256: str = Field(pattern=_SHA256)
    reviewer: ToolIdentity
    raw_full_speed_reviewed: bool
    identity_match: bool | None
    camera_axis_match: bool | None
    framing_match: bool | None
    motion_direction_match: bool | None
    action_phase_match: bool | None
    entrance_exit_match: bool | None
    no_unexpected_stop_or_reentry: bool | None
    pacing_waiver: bool
    rationale: str = Field(min_length=1)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_hash(self) -> "SourceBoundaryHumanDecisionV1":
        expected = canonical_sha256(
            {
                "schema": "source-boundary-human-decision/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        )
        if self.content_hash != expected:
            raise ValueError("source boundary human decision hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "SourceBoundaryHumanDecisionV1":
        data = {"schema_version": "1", **values}
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            {
                "schema": "source-boundary-human-decision/1",
                **provisional.model_dump(
                    mode="json", exclude={"content_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


class SourceBoundaryReviewIntent(StrictModel):
    resolved_generation_hash: str = Field(pattern=_SHA256)
    request_input_hash: str = Field(pattern=_SHA256)
    artifact_sha256: str = Field(pattern=_SHA256)
    artifact_size_bytes: int = Field(strict=True, gt=0)
    fetch_fingerprint: str = Field(pattern=_SHA256)
    target_shot_id: str = Field(min_length=1)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    source_profile_content_hash: str = Field(pattern=_SHA256)
    source_execution_stack_hash: str = Field(pattern=_SHA256)
    measurement_contract_hash: str = Field(pattern=_SHA256)
    human_decision_hash: str = Field(pattern=_SHA256)
    evaluator: ToolIdentity
    evaluation_fingerprint: str = Field(pattern=_SHA256)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_hashes(self) -> "SourceBoundaryReviewIntent":
        body = self.model_dump(
            mode="json", exclude={"evaluation_fingerprint", "content_hash"}
        )
        if self.evaluation_fingerprint != canonical_sha256(
            {"schema": "source-boundary-evaluation-fingerprint/1", **body}
        ):
            raise ValueError("source boundary evaluation fingerprint is invalid")
        if self.content_hash != canonical_sha256(
            {
                "schema": "source-boundary-review-intent/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        ):
            raise ValueError("source boundary review intent hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "SourceBoundaryReviewIntent":
        data = dict(values)
        provisional = cls.model_construct(
            **data,
            evaluation_fingerprint="0" * 64,
            content_hash="0" * 64,
        )
        body = provisional.model_dump(
            mode="json",
            exclude={"evaluation_fingerprint", "content_hash"},
            warnings=False,
        )
        data["evaluation_fingerprint"] = canonical_sha256(
            {"schema": "source-boundary-evaluation-fingerprint/1", **body}
        )
        with_fingerprint = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            {
                "schema": "source-boundary-review-intent/1",
                **with_fingerprint.model_dump(
                    mode="json", exclude={"content_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


class SourceBoundaryEndpointMeasurement(StrictModel):
    role: Literal["first_frame", "last_frame"]
    frame_index: int = Field(strict=True, ge=0)
    anchor_asset_id: str = Field(min_length=1)
    anchor_sha256: str = Field(pattern=_SHA256)
    psnr_millidb: int = Field(strict=True, ge=0)
    ssim_millionths: int = Field(strict=True, ge=-1_000_000, le=1_000_000)


class SourceBoundaryReviewEvidence(StrictModel):
    intent: SourceBoundaryReviewIntent
    measurement_contract: SourceBoundaryMeasurementContractV1
    human_decision: SourceBoundaryHumanDecisionV1
    measured_metadata_hash: str = Field(pattern=_SHA256)
    first_frame: SourceBoundaryEndpointMeasurement
    last_frame: SourceBoundaryEndpointMeasurement
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_binding(self) -> "SourceBoundaryReviewEvidence":
        contract = self.measurement_contract
        if (
            contract.content_hash != self.intent.measurement_contract_hash
            or self.human_decision.content_hash != self.intent.human_decision_hash
            or self.human_decision.resolved_generation_hash
            != self.intent.resolved_generation_hash
            or self.human_decision.artifact_sha256 != self.intent.artifact_sha256
            or self.first_frame.role != "first_frame"
            or self.first_frame.frame_index != 0
            or self.first_frame.anchor_asset_id != contract.first_frame_asset_id
            or self.first_frame.anchor_sha256 != contract.first_frame_sha256
            or self.last_frame.role != "last_frame"
            or self.last_frame.frame_index <= 0
            or self.last_frame.anchor_asset_id != contract.last_frame_asset_id
            or self.last_frame.anchor_sha256 != contract.last_frame_sha256
        ):
            raise ValueError("source boundary review evidence binding is not exact")
        if self.content_hash != canonical_sha256(
            {
                "schema": "source-boundary-review-evidence/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        ):
            raise ValueError("source boundary review evidence hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "SourceBoundaryReviewEvidence":
        data = dict(values)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            {
                "schema": "source-boundary-review-evidence/1",
                **provisional.model_dump(
                    mode="json", exclude={"content_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


class SourceBoundaryReviewReceipt(StrictModel):
    intent_content_hash: str = Field(pattern=_SHA256)
    evidence_content_hash: str = Field(pattern=_SHA256)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    artifact_sha256: str = Field(pattern=_SHA256)
    verdict: QaVerdict
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_hash(self) -> "SourceBoundaryReviewReceipt":
        if self.content_hash != canonical_sha256(
            {
                "schema": "source-boundary-review-receipt/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        ):
            raise ValueError("source boundary review receipt hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "SourceBoundaryReviewReceipt":
        data = dict(values)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            {
                "schema": "source-boundary-review-receipt/1",
                **provisional.model_dump(
                    mode="json", exclude={"content_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


def adjudicate_source_boundary_review(
    evidence: SourceBoundaryReviewEvidence,
) -> SourceBoundaryReviewReceipt:
    """Produce the only source-boundary P6 verdict from exact raw evidence."""

    checked = SourceBoundaryReviewEvidence.model_validate(
        evidence.model_dump(mode="python")
    )
    contract = checked.measurement_contract
    measurements = (checked.first_frame, checked.last_frame)
    human = checked.human_decision
    human_values = (
        human.identity_match,
        human.camera_axis_match,
        human.framing_match,
        human.motion_direction_match,
        human.action_phase_match,
        human.entrance_exit_match,
        human.no_unexpected_stop_or_reentry,
    )
    if any(
        item.psnr_millidb < contract.psnr_threshold_millidb
        or item.ssim_millionths < contract.ssim_threshold_millionths
        for item in measurements
    ) or any(item is False for item in human_values):
        verdict = QaVerdict.FAIL
    elif not human.raw_full_speed_reviewed or any(
        item is None for item in human_values
    ):
        verdict = QaVerdict.NOT_EVALUATED
    else:
        verdict = QaVerdict.PASS
    return SourceBoundaryReviewReceipt.create(
        intent_content_hash=checked.intent.content_hash,
        evidence_content_hash=checked.content_hash,
        resolved_generation_hash=checked.intent.resolved_generation_hash,
        artifact_sha256=checked.intent.artifact_sha256,
        verdict=verdict,
    )


def source_boundary_supported_rubric_payload() -> dict[str, object]:
    """Return the one frozen P0 rubric interpreted by the v1 evaluator."""

    return {
        "boundary": {
            "decoded_first_and_last_required": True,
            "perceptual_backend_missing": ("NOT_EVALUATED_requires_exact_human_review"),
            "psnr_db_minimum": 30.0,
            "ssim_minimum": 0.9,
        },
        "identity": {
            "automatic_missing": "NOT_EVALUATED_requires_exact_human_review",
            "dimensions": ["face", "hair", "wardrobe", "satchel", "body_scale"],
        },
        "motion": {
            "dimensions": [
                "subject_direction_velocity",
                "camera_direction_velocity",
                "action_phase",
                "entrance_exit",
                "unexpected_stop_or_reentry",
            ],
            "single_frame_metric_sufficient": False,
        },
        "sequence": {
            "raw_full_speed_review_required": True,
            "crossfade_optical_flow_interpolation_retime_forbidden": True,
        },
        "verdict_owner": "P6",
        "human_evidence_required": True,
    }


def validate_source_boundary_review_intent(
    *,
    request: object,
    fetch_receipt: object,
    intent: SourceBoundaryReviewIntent,
) -> SourceBoundaryReviewIntent:
    """Validate fields independently owned by the exact request and fetch."""

    validate_source_boundary_qualification_request(request)
    scope = request.activation_scope
    if scope is None:
        raise ValueError("source boundary request has no authoring scope")
    original = scope.request
    if (
        intent.resolved_generation_hash != request.resolved_generation_hash
        or intent.request_input_hash != request.request_input_hash
        or intent.artifact_sha256 != fetch_receipt.artifact_sha256
        or intent.artifact_size_bytes != fetch_receipt.size_bytes
        or intent.fetch_fingerprint != fetch_receipt.fetch_fingerprint
        or intent.target_shot_id != original.target_shot_id
        or intent.target_shot_revision != original.target_shot_revision
        or intent.target_shot_content_hash != original.target_shot_content_hash
        or intent.source_execution_stack_hash != request.execution_stack_hash
        or intent.evaluator
        != ToolIdentity(name="ai-video-source-boundary-review", version="1")
    ):
        raise ValueError("source boundary review intent is not exact")
    return intent


def validate_source_boundary_review_closure(
    *,
    request: object,
    fetch_receipt: object,
    intent: SourceBoundaryReviewIntent,
    evidence: SourceBoundaryReviewEvidence,
    receipt: SourceBoundaryReviewReceipt,
    probe: object,
    provenance: object,
    p0_receipt: object,
    p0_rubric: object,
    source_execution_stack_hashes: tuple[str, ...],
    require_pass: bool = True,
) -> SourceBoundaryReviewEvidence:
    """Validate one self-contained immutable source-boundary PASS closure."""

    validate_source_boundary_review_intent(
        request=request,
        fetch_receipt=fetch_receipt,
        intent=intent,
    )
    scope = request.activation_scope
    if scope is None:
        raise ValueError("source boundary request has no authoring scope")
    original = scope.request
    measured = probe.measured
    contract = evidence.measurement_contract
    human = evidence.human_decision
    expected_evaluator = ToolIdentity(
        name="ai-video-source-boundary-review",
        version="1",
    )
    if (
        p0_receipt.content_hash != contract.p0_qualification_receipt_hash
        or p0_receipt.rubric_hash != contract.p0_rubric_hash
        or p0_receipt.project != original.base_project
        or p0_receipt.registry != original.base_registry
        or p0_rubric.input_kind != "rubric"
        or p0_rubric.content_hash != p0_receipt.rubric_hash
        or p0_rubric.payload != source_boundary_supported_rubric_payload()
        or intent.source_execution_stack_hash not in source_execution_stack_hashes
        or intent.artifact_sha256 != measured.artifact_sha256
        or intent.artifact_size_bytes != measured.size_bytes
        or intent.measurement_contract_hash != contract.content_hash
        or intent.human_decision_hash != human.content_hash
        or intent.evaluator != expected_evaluator
        or human.resolved_generation_hash != request.resolved_generation_hash
        or human.artifact_sha256 != measured.artifact_sha256
        or contract.first_frame_asset_id != request.image_bindings[0].asset_id
        or contract.first_frame_sha256 != request.image_bindings[0].asset_sha256
        or contract.last_frame_asset_id != request.image_bindings[1].asset_id
        or contract.last_frame_sha256 != request.image_bindings[1].asset_sha256
        or contract.sample_width != request.effective_output.width
        or contract.sample_height != request.effective_output.height
        or contract.sample_width != measured.width
        or contract.sample_height != measured.height
        or evidence.intent != intent
        or evidence.measured_metadata_hash != canonical_sha256(measured)
        or evidence.first_frame.frame_index != 0
        or evidence.last_frame.frame_index != measured.frame_count - 1
        or receipt != adjudicate_source_boundary_review(evidence)
        or probe.request_receipt_fingerprint != request.desired_generation_fingerprint
        or probe.resolved_generation_hash != request.resolved_generation_hash
        or probe.fetch_fingerprint != fetch_receipt.fetch_fingerprint
        or measured.artifact_sha256 != fetch_receipt.artifact_sha256
        or measured.size_bytes != fetch_receipt.size_bytes
        or provenance.generation_id != request.generation_id
        or provenance.request_receipt_fingerprint
        != request.desired_generation_fingerprint
        or provenance.resolved_generation_hash != request.resolved_generation_hash
        or provenance.provider_kind != request.provider_kind
        or provenance.model_id != request.model_id
        or provenance.profile_sha256 != request.provider_profile.profile_sha256
        or provenance.fetch_fingerprint != fetch_receipt.fetch_fingerprint
        or provenance.artifact_sha256 != fetch_receipt.artifact_sha256
        or provenance.probe_receipt_id != probe.content_hash
        or provenance.usage_license != scope.usage_license
    ):
        raise ValueError("source boundary immutable closure is not exact")
    if require_pass and receipt.verdict is not QaVerdict.PASS:
        raise ValueError("source boundary immutable closure is not PASS")
    return evidence


class SourceBoundaryReviewer(Protocol):
    """Effect boundary used only by the Production committer checkpoint."""

    source_profile_content_hash: str
    source_execution_stack_hash: str
    measurement_contract: SourceBoundaryMeasurementContractV1
    human_decision: SourceBoundaryHumanDecisionV1
    evaluator: ToolIdentity

    def create_intent(
        self,
        request: "ResolvedVideoGenerationRequest",
        measured: "MeasuredVideoMetadata",
        fetch_receipt: "VideoFetchReceipt | LocalVideoFetchReceipt",
        p0_receipt: "P0QualificationPreparedReceipt",
    ) -> SourceBoundaryReviewIntent: ...

    def __call__(
        self,
        held_fd: int,
        request: "ResolvedVideoGenerationRequest",
        measured: "MeasuredVideoMetadata",
        intent: SourceBoundaryReviewIntent,
    ) -> SourceBoundaryReviewEvidence: ...


def is_source_boundary_qualification_request(request: object) -> bool:
    """Identify the reserved sealed approved-endpoint owner before validation."""

    scope = getattr(request, "activation_scope", None)
    if scope is None:
        return False
    original = scope.request
    return (
        original.target_asset_role == "approved_endpoint"
        and getattr(request, "seal_terminal_frame", False)
        and original.seal_terminal_frame
    )


def validate_source_boundary_qualification_request(request: object) -> object:
    """Fail closed when the reserved source owner has any alternate P6 shape."""

    if not is_source_boundary_qualification_request(request):
        raise ValueError("request is not an approved-endpoint source qualification")
    original = request.activation_scope.request
    binding_names = (
        "c4_multi_anchor_binding",
        "continuity_binding",
        "commercial_binding",
        "hard_cut_keyframe_binding",
    )
    if (
        any(getattr(request, name, None) is not None for name in binding_names)
        or any(getattr(original, name, None) is not None for name in binding_names)
        or not request.seal_terminal_frame
        or not original.seal_terminal_frame
        or tuple(item.role for item in request.image_bindings)
        != ("first_frame", "last_frame")
        or tuple(item.role for item in original.image_bindings)
        != ("first_frame", "last_frame")
    ):
        raise ValueError(
            "approved-endpoint source qualification must not include continuity, "
            "commercial, hard-cut, or C4 bindings and must use exact sealed "
            "first/last frames"
        )
    return request


def _valid_uniform_mean(values: np.ndarray, window: int) -> np.ndarray:
    integral = np.pad(values, ((1, 0), (1, 0)), mode="constant").cumsum(0).cumsum(1)
    return (
        integral[window:, window:]
        - integral[:-window, window:]
        - integral[window:, :-window]
        + integral[:-window, :-window]
    ) / (window * window)


def _rgb_psnr_millidb(anchor: np.ndarray, frame: np.ndarray) -> int:
    error = anchor.astype(np.float64) - frame.astype(np.float64)
    mse = float(np.mean(error * error))
    if mse == 0:
        return 999_000
    return round(10_000 * math.log10((255.0 * 255.0) / mse))


def _bt709_luma_ssim_millionths(anchor: np.ndarray, frame: np.ndarray) -> int:
    coefficients = np.array((0.2126, 0.7152, 0.0722), dtype=np.float64)
    left = anchor.astype(np.float64) @ coefficients
    right = frame.astype(np.float64) @ coefficients
    window = 7
    left_mean = _valid_uniform_mean(left, window)
    right_mean = _valid_uniform_mean(right, window)
    left_square_mean = _valid_uniform_mean(left * left, window)
    right_square_mean = _valid_uniform_mean(right * right, window)
    product_mean = _valid_uniform_mean(left * right, window)
    covariance_normalization = (window * window) / (window * window - 1)
    left_variance = covariance_normalization * (
        left_square_mean - left_mean * left_mean
    )
    right_variance = covariance_normalization * (
        right_square_mean - right_mean * right_mean
    )
    covariance = covariance_normalization * (product_mean - left_mean * right_mean)
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    score = np.mean(
        ((2 * left_mean * right_mean + c1) * (2 * covariance + c2))
        / (
            (left_mean * left_mean + right_mean * right_mean + c1)
            * (left_variance + right_variance + c2)
        )
    )
    return round(float(score) * 1_000_000)


def _decode_anchor(payload: bytes, *, width: int, height: int) -> np.ndarray:
    try:
        with Image.open(BytesIO(payload)) as image:
            rgb = image.convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
            return np.asarray(rgb, dtype=np.uint8)
    except (OSError, ValueError) as exc:
        raise ValueError("source boundary anchor image is invalid") from exc


@dataclass(frozen=True)
class SourceBoundaryReviewerV1:
    """Decode the exact endpoints and preserve a separately bound human decision."""

    source_profile_content_hash: str
    source_execution_stack_hash: str
    measurement_contract: SourceBoundaryMeasurementContractV1
    human_decision: SourceBoundaryHumanDecisionV1
    evaluator: ToolIdentity
    sampler: object
    first_anchor_bytes: bytes
    last_anchor_bytes: bytes

    def __post_init__(self) -> None:
        contract = self.measurement_contract
        sha256_values = (
            self.source_profile_content_hash,
            self.source_execution_stack_hash,
        )
        if (
            hashlib.sha256(self.first_anchor_bytes).hexdigest()
            != contract.first_frame_sha256
            or hashlib.sha256(self.last_anchor_bytes).hexdigest()
            != contract.last_frame_sha256
            or getattr(self.sampler, "identity", None) != contract.decoder
            or any(
                len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
                for value in sha256_values
            )
        ):
            raise ValueError("source boundary reviewer inputs are not exact")

    def create_intent(
        self,
        request,
        measured,
        fetch_receipt,
        p0_receipt,
    ) -> SourceBoundaryReviewIntent:
        del p0_receipt
        scope = request.activation_scope
        if scope is None:
            raise ValueError("source boundary request has no authoring scope")
        original = scope.request
        return SourceBoundaryReviewIntent.create(
            resolved_generation_hash=request.resolved_generation_hash,
            request_input_hash=request.request_input_hash,
            artifact_sha256=measured.artifact_sha256,
            artifact_size_bytes=measured.size_bytes,
            fetch_fingerprint=fetch_receipt.fetch_fingerprint,
            target_shot_id=original.target_shot_id,
            target_shot_revision=original.target_shot_revision,
            target_shot_content_hash=original.target_shot_content_hash,
            source_profile_content_hash=self.source_profile_content_hash,
            source_execution_stack_hash=self.source_execution_stack_hash,
            measurement_contract_hash=self.measurement_contract.content_hash,
            human_decision_hash=self.human_decision.content_hash,
            evaluator=self.evaluator,
        )

    def __call__(
        self,
        held_fd: int,
        request,
        measured,
        intent: SourceBoundaryReviewIntent,
    ) -> SourceBoundaryReviewEvidence:
        if (
            intent.resolved_generation_hash != request.resolved_generation_hash
            or intent.artifact_sha256 != measured.artifact_sha256
        ):
            raise ValueError("source boundary evaluator intent is not exact")
        sampled = self.sampler.sample(
            held_fd,
            measured,
            (0, measured.frame_count - 1),
        )
        if (
            len(sampled) != 2
            or sampled[0].frame_index != 0
            or sampled[1].frame_index != measured.frame_count - 1
            or any(
                item.width != self.measurement_contract.sample_width
                or item.height != self.measurement_contract.sample_height
                for item in sampled
            )
        ):
            raise ValueError("source boundary sampled frames are not exact")
        anchors = (
            _decode_anchor(
                self.first_anchor_bytes,
                width=self.measurement_contract.sample_width,
                height=self.measurement_contract.sample_height,
            ),
            _decode_anchor(
                self.last_anchor_bytes,
                width=self.measurement_contract.sample_width,
                height=self.measurement_contract.sample_height,
            ),
        )
        frames = tuple(
            np.frombuffer(item.pixels, dtype=np.uint8).reshape(
                item.height, item.width, 3
            )
            for item in sampled
        )
        contract = self.measurement_contract
        measurements = tuple(
            SourceBoundaryEndpointMeasurement(
                role=role,
                frame_index=sample.frame_index,
                anchor_asset_id=asset_id,
                anchor_sha256=anchor_sha256,
                psnr_millidb=_rgb_psnr_millidb(anchor, frame),
                ssim_millionths=_bt709_luma_ssim_millionths(anchor, frame),
            )
            for role, sample, asset_id, anchor_sha256, anchor, frame in zip(
                ("first_frame", "last_frame"),
                sampled,
                (contract.first_frame_asset_id, contract.last_frame_asset_id),
                (contract.first_frame_sha256, contract.last_frame_sha256),
                anchors,
                frames,
                strict=True,
            )
        )
        return SourceBoundaryReviewEvidence.create(
            intent=intent,
            measurement_contract=contract,
            human_decision=self.human_decision,
            measured_metadata_hash=canonical_sha256(measured),
            first_frame=measurements[0],
            last_frame=measurements[1],
        )


__all__ = [
    "SourceBoundaryEndpointMeasurement",
    "SourceBoundaryHumanDecisionV1",
    "SourceBoundaryMeasurementContractV1",
    "SourceBoundaryReviewEvidence",
    "SourceBoundaryReviewIntent",
    "SourceBoundaryReviewReceipt",
    "SourceBoundaryReviewer",
    "SourceBoundaryReviewerV1",
    "adjudicate_source_boundary_review",
    "is_source_boundary_qualification_request",
    "validate_source_boundary_qualification_request",
    "source_boundary_supported_rubric_payload",
    "validate_source_boundary_review_intent",
    "validate_source_boundary_review_closure",
]
