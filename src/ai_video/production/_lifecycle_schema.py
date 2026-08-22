from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)


class ImageRequestReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    attempt_id: str = Field(min_length=1)
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_kind: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    target_shot_id: str = Field(min_length=1)
    target_asset_role: str = Field(min_length=1)
    output_asset_id: str = Field(pattern=r"^image-[0-9a-f]{64}$")
    preview_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    authorization_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    policy_receipt_id: str = Field(min_length=1)
    usage_license: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_request_identity(self) -> "ImageRequestReceipt":
        if self.request_id != self.request_fingerprint:
            raise ValueError("image request ID must equal request fingerprint")
        if self.output_asset_id != f"image-{self.request_fingerprint}":
            raise ValueError("image output asset ID must match request fingerprint")
        return self


class _PaidLifecycleModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _canonical_paid_path(value: Path, expected: Path, label: str) -> Path:
    if value.is_absolute() or ".." in value.parts or value != expected:
        raise ValueError(f"{label} path must be canonical")
    return value


class PaidProviderBudgetSnapshotPointer(_PaidLifecycleModel):
    path: Path
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "PaidProviderBudgetSnapshotPointer":
        _canonical_paid_path(
            self.path,
            Path(f"state/paid-provider/budgets/{self.content_hash}.json"),
            "paid Provider budget",
        )
        return self


class PaidProviderGateReceiptPointer(_PaidLifecycleModel):
    path: Path
    gate_receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "PaidProviderGateReceiptPointer":
        _canonical_paid_path(
            self.path,
            Path(f"state/paid-provider/gates/{self.gate_receipt_fingerprint}.json"),
            "paid Provider Gate receipt",
        )
        return self


class PaidProviderSubmitReceiptPointer(_PaidLifecycleModel):
    path: Path
    submit_receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "PaidProviderSubmitReceiptPointer":
        _canonical_paid_path(
            self.path,
            Path(f"state/paid-provider/submits/{self.submit_receipt_fingerprint}.json"),
            "paid Provider submit receipt",
        )
        return self


class PaidProviderAttemptPhase(str, Enum):
    SUBMIT_INTENT = "submit_intent"
    ACCEPTED = "accepted"
    KNOWN_NO_EFFECT = "known_no_effect"
    OUTCOME_UNKNOWN = "outcome_unknown"
    SETTLED = "settled"


class PaidProviderAttemptState(_PaidLifecycleModel):
    gate_receipt: PaidProviderGateReceiptPointer
    reservation_id: str = Field(min_length=1)
    phase: PaidProviderAttemptPhase
    submit_receipt: PaidProviderSubmitReceiptPointer | None = None

    @model_validator(mode="after")
    def _validate_phase_evidence(self) -> "PaidProviderAttemptState":
        if self.phase is PaidProviderAttemptPhase.SUBMIT_INTENT:
            if self.submit_receipt is not None:
                raise ValueError("submit intent cannot select a submit receipt")
        elif self.submit_receipt is None:
            raise ValueError("paid Provider terminal phase requires a submit receipt")
        return self


class VideoRequestReceiptPointer(_PaidLifecycleModel):
    path: Path
    request_receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    generation_id: str = Field(min_length=1)
    request_input_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    resolved_generation_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_asset_id: str = Field(min_length=1)
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "VideoRequestReceiptPointer":
        _canonical_paid_path(
            self.path,
            Path(
                "state/video-generation/requests/"
                f"{self.request_receipt_fingerprint}.json"
            ),
            "video generation request receipt",
        )
        return self


class VideoStatusReceiptPointer(_PaidLifecycleModel):
    path: Path
    observation_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    paid_submit_receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "VideoStatusReceiptPointer":
        _canonical_paid_path(
            self.path,
            Path(
                "state/video-generation/status/"
                f"{self.observation_fingerprint}.json"
            ),
            "video generation status receipt",
        )
        return self


class VideoFetchReceiptPointer(_PaidLifecycleModel):
    path: Path
    fetch_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_path: Path
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_size_bytes: int = Field(strict=True, gt=0)
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_paths(self) -> "VideoFetchReceiptPointer":
        _canonical_paid_path(
            self.path,
            Path(
                "state/video-generation/fetch/receipts/"
                f"{self.fetch_fingerprint}.json"
            ),
            "video fetch receipt",
        )
        _canonical_paid_path(
            self.artifact_path,
            Path(
                "state/video-generation/fetch/files/"
                f"{self.artifact_sha256}.mp4"
            ),
            "video fetched artifact",
        )
        return self


class LocalVideoSubmitIntentPointer(_PaidLifecycleModel):
    path: Path
    intent_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "LocalVideoSubmitIntentPointer":
        _canonical_paid_path(
            self.path,
            Path(
                "state/video-generation/local/intents/"
                f"{self.intent_fingerprint}.json"
            ),
            "local video submit intent",
        )
        return self


class LocalVideoSubmitReceiptPointer(_PaidLifecycleModel):
    path: Path
    result_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_request_id: str = Field(min_length=1)
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "LocalVideoSubmitReceiptPointer":
        _canonical_paid_path(
            self.path,
            Path(
                "state/video-generation/local/submits/"
                f"{self.result_fingerprint}.json"
            ),
            "local video submit receipt",
        )
        return self


class LocalVideoStatusReceiptPointer(_PaidLifecycleModel):
    path: Path
    observation_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    submit_result_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "LocalVideoStatusReceiptPointer":
        _canonical_paid_path(
            self.path,
            Path(
                "state/video-generation/local/status/"
                f"{self.observation_fingerprint}.json"
            ),
            "local video status receipt",
        )
        return self


class LocalVideoFetchReceiptPointer(_PaidLifecycleModel):
    path: Path
    fetch_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_path: Path
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_size_bytes: int = Field(strict=True, gt=0)
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_paths(self) -> "LocalVideoFetchReceiptPointer":
        _canonical_paid_path(
            self.path,
            Path(
                "state/video-generation/local/fetch/receipts/"
                f"{self.fetch_fingerprint}.json"
            ),
            "local video fetch receipt",
        )
        _canonical_paid_path(
            self.artifact_path,
            Path(
                "state/video-generation/fetch/files/"
                f"{self.artifact_sha256}.mp4"
            ),
            "local video fetched artifact",
        )
        return self


class TerminalFrameEvidencePointer(_PaidLifecycleModel):
    path: Path
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    extracted_asset_id: str = Field(min_length=1)
    extracted_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "TerminalFrameEvidencePointer":
        _canonical_paid_path(
            self.path,
            Path(
                "state/video-generation/terminal-evidence/"
                f"{self.content_hash}.json"
            ),
            "terminal frame evidence",
        )
        return self


class TerminalFrameExtractionReceiptPointer(_PaidLifecycleModel):
    path: Path
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    extracted_asset_id: str = Field(min_length=1)
    extracted_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "TerminalFrameExtractionReceiptPointer":
        _canonical_paid_path(
            self.path,
            Path(
                "state/video-generation/terminal-extractions/"
                f"{self.content_hash}.json"
            ),
            "terminal frame extraction receipt",
        )
        return self


class ContinuityEvaluationIntentPointer(_PaidLifecycleModel):
    path: Path
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluation_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluator_profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "ContinuityEvaluationIntentPointer":
        _canonical_paid_path(
            self.path,
            Path(
                "state/video-generation/continuity-evaluation/intents/"
                f"{self.content_hash}.json"
            ),
            "continuity evaluation intent",
        )
        return self


class GeneratedShotContinuityEvidencePointer(_PaidLifecycleModel):
    path: Path
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluation_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "GeneratedShotContinuityEvidencePointer":
        _canonical_paid_path(
            self.path,
            Path(
                "state/video-generation/continuity-evaluation/evidence/"
                f"{self.content_hash}.json"
            ),
            "generated Shot continuity evidence",
        )
        return self


class VideoProbeReceiptPointer(_PaidLifecycleModel):
    path: Path
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    resolved_generation_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    fetch_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "VideoProbeReceiptPointer":
        _canonical_paid_path(
            self.path,
            Path(
                "state/video-generation/probes/"
                f"{self.content_hash}.json"
            ),
            "video probe receipt",
        )
        return self


class VideoProvenanceReceiptPointer(_PaidLifecycleModel):
    path: Path
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    resolved_generation_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    fetch_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    probe_receipt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "VideoProvenanceReceiptPointer":
        _canonical_paid_path(
            self.path,
            Path(
                "state/video-generation/provenance/"
                f"{self.content_hash}.json"
            ),
            "video provenance receipt",
        )
        return self


class ContinuityEvaluationPhase(str, Enum):
    INTENT = "intent"
    EVIDENCED = "evidenced"


class ContinuityEvaluationState(_PaidLifecycleModel):
    phase: ContinuityEvaluationPhase
    intent: ContinuityEvaluationIntentPointer
    evidence: GeneratedShotContinuityEvidencePointer | None = None
    probe: VideoProbeReceiptPointer | None = None
    provenance: VideoProvenanceReceiptPointer | None = None

    @model_serializer(mode="wrap")
    def _serialize_compatible_variant(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.probe is None:
            data.pop("probe", None)
        if self.provenance is None:
            data.pop("provenance", None)
        return data

    @model_validator(mode="after")
    def _validate_phase(self) -> "ContinuityEvaluationState":
        if self.phase is ContinuityEvaluationPhase.INTENT:
            if any(
                item is not None
                for item in (self.evidence, self.probe, self.provenance)
            ):
                raise ValueError("continuity evaluation intent cannot contain evidence")
        elif (
            self.evidence is None
            or self.evidence.evaluation_fingerprint
            != self.intent.evaluation_fingerprint
            or self.evidence.artifact_sha256 != self.intent.artifact_sha256
        ):
            raise ValueError("continuity evaluation evidence does not match its intent")
        if (self.probe is None) != (self.provenance is None):
            raise ValueError(
                "continuity capture checkpoint requires probe and provenance together"
            )
        if self.probe is not None and self.provenance is not None and (
            self.probe.resolved_generation_hash
            != self.provenance.resolved_generation_hash
            or self.probe.artifact_sha256 != self.intent.artifact_sha256
            or self.probe.request_receipt_fingerprint
            != self.provenance.request_receipt_fingerprint
            or self.probe.fetch_fingerprint != self.provenance.fetch_fingerprint
            or self.probe.artifact_sha256 != self.provenance.artifact_sha256
            or self.provenance.probe_receipt_id != self.probe.content_hash
        ):
            raise ValueError(
                "continuity capture checkpoint does not bind exact video evidence"
            )
        return self


class VideoAttemptPhase(str, Enum):
    REQUEST = "request"
    SUBMIT_INTENT = "submit_intent"
    SUBMITTED = "submitted"
    POLLING = "polling"
    FETCH = "fetch"
    VALIDATE = "validate"
    CANDIDATE = "candidate"
    ACTIVATE = "activate"


_VIDEO_PRE_SUBMIT_PHASES = frozenset(
    {VideoAttemptPhase.REQUEST, VideoAttemptPhase.SUBMIT_INTENT}
)
_VIDEO_OBSERVED_PHASES = frozenset(
    {
        VideoAttemptPhase.POLLING,
        VideoAttemptPhase.FETCH,
        VideoAttemptPhase.VALIDATE,
        VideoAttemptPhase.CANDIDATE,
        VideoAttemptPhase.ACTIVATE,
    }
)
_VIDEO_CANDIDATE_PHASES = frozenset(
    {VideoAttemptPhase.CANDIDATE, VideoAttemptPhase.ACTIVATE}
)


class VideoGenerationAttemptState(_PaidLifecycleModel):
    request: VideoRequestReceiptPointer
    generation_id: str = Field(min_length=1)
    resolved_generation_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    phase: VideoAttemptPhase
    paid_submit_receipt: PaidProviderSubmitReceiptPointer | None = None
    latest_observation: VideoStatusReceiptPointer | None = None
    fetch_receipt: VideoFetchReceiptPointer | None = None
    local_submit_intent: LocalVideoSubmitIntentPointer | None = None
    local_submit_receipt: LocalVideoSubmitReceiptPointer | None = None
    local_latest_observation: LocalVideoStatusReceiptPointer | None = None
    local_fetch_receipt: LocalVideoFetchReceiptPointer | None = None
    provider_file_id: str | None = Field(default=None, min_length=1)
    terminal_frame_evidence: TerminalFrameEvidencePointer | None = None
    terminal_frame_extraction: TerminalFrameExtractionReceiptPointer | None = None
    continuity_evaluation: ContinuityEvaluationState | None = None
    candidate_video_asset_ids: tuple[str, ...] = ()
    candidate_continuity_asset_ids: tuple[str, ...] = ()

    @model_serializer(mode="wrap")
    def _serialize_optional_continuity_state(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.terminal_frame_evidence is None:
            data.pop("terminal_frame_evidence", None)
        if self.terminal_frame_extraction is None:
            data.pop("terminal_frame_extraction", None)
        if self.continuity_evaluation is None:
            data.pop("continuity_evaluation", None)
        if not self.candidate_continuity_asset_ids:
            data.pop("candidate_continuity_asset_ids", None)
        for field in (
            "local_submit_intent",
            "local_submit_receipt",
            "local_latest_observation",
            "local_fetch_receipt",
        ):
            if getattr(self, field) is None:
                data.pop(field, None)
        return data

    @model_validator(mode="after")
    def _validate_video_attempt_state(self) -> "VideoGenerationAttemptState":
        if (
            self.request.generation_id != self.generation_id
            or self.request.resolved_generation_hash != self.resolved_generation_hash
        ):
            raise ValueError("video attempt identity does not match its request pointer")
        local_fields = (
            self.local_submit_intent,
            self.local_submit_receipt,
            self.local_latest_observation,
            self.local_fetch_receipt,
        )
        remote_fields = (
            self.paid_submit_receipt,
            self.latest_observation,
            self.fetch_receipt,
        )
        local_lane = any(item is not None for item in local_fields)
        remote_lane = any(item is not None for item in remote_fields)
        if local_lane and remote_lane:
            raise ValueError("video attempt cannot mix local and paid evidence")
        if self.phase is VideoAttemptPhase.REQUEST:
            if (
                local_lane
                or remote_lane
            ):
                raise ValueError(
                    "pre-submit video phases cannot select submit or observation evidence"
                )
        elif self.phase is VideoAttemptPhase.SUBMIT_INTENT:
            if local_lane and (
                self.local_submit_intent is None
                or any(item is not None for item in local_fields[1:])
            ):
                raise ValueError("local video submit intent contains terminal evidence")
            if remote_lane:
                raise ValueError(
                    "paid video submit intent phase cannot contain submit evidence"
                )
        elif local_lane:
            if self.local_submit_intent is None or self.local_submit_receipt is None:
                raise ValueError("submitted local video phases require exact submit evidence")
        elif self.paid_submit_receipt is None:
            raise ValueError("submitted video phases require a paid Provider submit receipt")
        observation = (
            self.local_latest_observation if local_lane else self.latest_observation
        )
        fetch = self.local_fetch_receipt if local_lane else self.fetch_receipt
        if self.phase in _VIDEO_OBSERVED_PHASES and observation is None:
            raise ValueError("observed video phases require a latest observation pointer")
        if observation is not None:
            if (
                observation.request_receipt_fingerprint
                != self.request.request_receipt_fingerprint
            ):
                raise ValueError("video observation does not belong to the attempt request")
            if not local_lane and (
                self.paid_submit_receipt is not None
                and self.latest_observation is not None
                and self.latest_observation.paid_submit_receipt_fingerprint
                != self.paid_submit_receipt.submit_receipt_fingerprint
            ):
                raise ValueError("video observation does not match the submit receipt")
            if local_lane and (
                self.local_submit_receipt is None
                or self.local_latest_observation is None
                or self.local_latest_observation.submit_result_fingerprint
                != self.local_submit_receipt.result_fingerprint
            ):
                raise ValueError("local video observation does not match submit receipt")
        elif self.provider_file_id is not None:
            raise ValueError("video provider file locator requires an observation pointer")
        if self.phase in {
            VideoAttemptPhase.VALIDATE,
            VideoAttemptPhase.CANDIDATE,
            VideoAttemptPhase.ACTIVATE,
        }:
            if fetch is None:
                raise ValueError("post-fetch video phases require a fetch receipt")
        elif fetch is not None:
            raise ValueError("video fetch receipt requires a post-fetch phase")
        if self.continuity_evaluation is not None:
            if self.phase not in {
                VideoAttemptPhase.VALIDATE,
                VideoAttemptPhase.CANDIDATE,
                VideoAttemptPhase.ACTIVATE,
            }:
                raise ValueError("continuity evaluation requires a post-fetch phase")
            if (
                self.continuity_evaluation.phase is ContinuityEvaluationPhase.INTENT
                and self.phase is not VideoAttemptPhase.VALIDATE
            ):
                raise ValueError("incomplete continuity evaluation must remain in validate")
        if self.phase in _VIDEO_CANDIDATE_PHASES:
            if self.candidate_video_asset_ids != (self.request.output_asset_id,):
                raise ValueError("video candidate asset ID must match request output")
            if self.terminal_frame_evidence is None:
                if self.candidate_continuity_asset_ids or self.terminal_frame_extraction:
                    raise ValueError(
                        "continuity candidate asset requires terminal frame evidence"
                    )
            elif (
                self.terminal_frame_extraction is None
                or self.candidate_continuity_asset_ids
                != (self.terminal_frame_evidence.extracted_asset_id,)
                or self.terminal_frame_extraction.extracted_asset_id
                != self.terminal_frame_evidence.extracted_asset_id
                or self.terminal_frame_extraction.extracted_sha256
                != self.terminal_frame_evidence.extracted_sha256
            ):
                raise ValueError(
                    "continuity candidate asset must match terminal frame evidence"
                )
        elif (
            self.candidate_video_asset_ids
            or self.candidate_continuity_asset_ids
            or self.terminal_frame_evidence is not None
            or self.terminal_frame_extraction is not None
            and self.phase is not VideoAttemptPhase.VALIDATE
        ):
            raise ValueError("video candidate asset IDs require candidate or activate phase")
        return self


P5_AWARE_OPERATIONS: frozenset[str] = frozenset(
    {
        "bootstrap_dependency_graph",
        "commit_project_registry",
        "audio_import",
        "voice_generation",
        "image_generation",
        "video_generation",
        "render_state",
        "repair",
    }
)

_VOICE_FIELDS = (
    "voice_request",
    "voice_phase",
    "candidate_audio_asset_ids",
    "candidate_caption_asset_ids",
)
_IMAGE_FIELDS = ("image_request", "image_phase", "candidate_image_asset_ids")
_VIDEO_FIELDS = ("video_generation_state",)


def validate_provider_attempt(attempt: Any) -> None:
    operation = attempt.operation
    voice_fields_present = any(
        getattr(attempt, field) not in (None, ()) for field in _VOICE_FIELDS
    )
    image_fields_present = any(
        getattr(attempt, field) not in (None, ()) for field in _IMAGE_FIELDS
    )
    video_fields_present = any(
        getattr(attempt, field) not in (None, ()) for field in _VIDEO_FIELDS
    )
    if operation != "voice_generation" and voice_fields_present:
        raise ValueError("non-voice operations cannot contain voice fields")
    if operation != "image_generation" and image_fields_present:
        raise ValueError("non-image operations cannot contain image fields")
    if operation != "video_generation" and video_fields_present:
        raise ValueError("non-video operations cannot contain video fields")
    if operation not in {"voice_generation", "image_generation"} and (
        attempt.provider_request_id is not None
    ):
        raise ValueError(
            "non-provider operations cannot contain provider request identity"
        )
    if operation == "voice_generation":
        _validate_voice_attempt(attempt)
    if operation == "image_generation":
        _validate_image_attempt(attempt)
    if operation == "video_generation":
        _validate_video_attempt(attempt)


def _validate_video_attempt(attempt: Any) -> None:
    state = attempt.video_generation_state
    if state is None:
        raise ValueError("video_generation attempts require video generation state")
    if attempt.base_dependency_graph is None:
        raise ValueError("video_generation attempts require base dependency graph")
    paid_state = attempt.paid_provider_state
    local_lane = state.local_submit_intent is not None
    if state.phase is VideoAttemptPhase.REQUEST:
        if paid_state is not None:
            raise ValueError("video request phase cannot contain paid Provider Gate state")
    elif local_lane:
        if paid_state is not None:
            raise ValueError("local video attempt cannot contain paid Provider Gate state")
        if state.phase is VideoAttemptPhase.SUBMIT_INTENT:
            if attempt.status.value not in {"running", "failed", "outcome_unknown"}:
                raise ValueError("local video submit intent status is inconsistent")
    else:
        if paid_state is None:
            raise ValueError("post-request video phases require paid Provider Gate state")
        if state.phase is VideoAttemptPhase.SUBMIT_INTENT:
            allowed_submit_outcomes = {
                (PaidProviderAttemptPhase.SUBMIT_INTENT, "running"),
                (PaidProviderAttemptPhase.KNOWN_NO_EFFECT, "failed"),
                (PaidProviderAttemptPhase.OUTCOME_UNKNOWN, "outcome_unknown"),
            }
            if (paid_state.phase, attempt.status.value) not in allowed_submit_outcomes:
                raise ValueError(
                    "video submit intent, paid Provider phase, and outer status "
                    "are inconsistent"
                )
        else:
            allowed_paid_phases = {
                VideoAttemptPhase.SUBMITTED: {
                    PaidProviderAttemptPhase.ACCEPTED,
                    PaidProviderAttemptPhase.SETTLED,
                },
                VideoAttemptPhase.POLLING: {
                    PaidProviderAttemptPhase.ACCEPTED,
                    PaidProviderAttemptPhase.SETTLED,
                },
                VideoAttemptPhase.FETCH: {
                    PaidProviderAttemptPhase.ACCEPTED,
                    PaidProviderAttemptPhase.SETTLED,
                },
                VideoAttemptPhase.VALIDATE: {
                    PaidProviderAttemptPhase.ACCEPTED,
                    PaidProviderAttemptPhase.SETTLED,
                },
                VideoAttemptPhase.CANDIDATE: {
                    PaidProviderAttemptPhase.SETTLED,
                },
                VideoAttemptPhase.ACTIVATE: {
                    PaidProviderAttemptPhase.SETTLED,
                },
            }[state.phase]
            if paid_state.phase not in allowed_paid_phases:
                raise ValueError(
                    "video phase is incompatible with paid Provider Gate phase"
                )
    allowed_phases = {
        "running": set(VideoAttemptPhase),
        "succeeded": {VideoAttemptPhase.ACTIVATE},
        "failed": set(VideoAttemptPhase),
        "interrupted": {
            VideoAttemptPhase.REQUEST,
            VideoAttemptPhase.FETCH,
            VideoAttemptPhase.VALIDATE,
            VideoAttemptPhase.CANDIDATE,
        },
        "outcome_unknown": set(VideoAttemptPhase) - {VideoAttemptPhase.REQUEST},
    }
    if state.phase not in allowed_phases[attempt.status.value]:
        raise ValueError("video attempt status and phase are inconsistent")
    if (
        state.paid_submit_receipt is not None
        and paid_state is not None
        and paid_state.submit_receipt != state.paid_submit_receipt
    ):
        raise ValueError("video submit receipt must match the paid Provider Gate receipt")
    candidate_bundle = (
        attempt.candidate_project,
        attempt.candidate_registry,
        attempt.candidate_dependency_graph,
        attempt.candidate_dependency_states_hash,
    )
    if state.phase in _VIDEO_CANDIDATE_PHASES:
        if not all(item is not None for item in candidate_bundle):
            raise ValueError("video candidate phase requires exact candidate bundle")
    elif any(item is not None for item in candidate_bundle):
        raise ValueError("video candidate bundle requires candidate or activate phase")


def _validate_voice_attempt(attempt: Any) -> None:
    if attempt.voice_request is None or attempt.voice_phase is None:
        raise ValueError("voice_generation attempts require voice request and phase")
    if attempt.voice_request.attempt_id != attempt.attempt_id:
        raise ValueError("voice attempt identity does not match request")
    all_phases = {
        "request",
        "submit_intent",
        "provider_call",
        "materialize",
        "probe",
        "align",
        "candidate",
        "activate",
    }
    allowed_phases = {
        "running": all_phases,
        "succeeded": {"activate"},
        "failed": all_phases,
        "interrupted": {"request", "materialize", "probe", "align", "candidate"},
        "outcome_unknown": all_phases - {"request"},
    }
    if attempt.voice_phase not in allowed_phases[attempt.status.value]:
        raise ValueError("voice attempt status and phase are inconsistent")
    if attempt.candidate_project not in (None, attempt.base_project):
        raise ValueError("voice candidate project identity does not match")
    if attempt.voice_phase in {"candidate", "activate"}:
        if attempt.candidate_registry is None or not attempt.candidate_audio_asset_ids:
            raise ValueError("voice candidate phase requires candidate audio bundle")
    elif (
        attempt.candidate_registry is not None
        or attempt.candidate_audio_asset_ids
        or attempt.candidate_caption_asset_ids
    ):
        raise ValueError("voice candidate bundle requires candidate phase")


def _validate_image_attempt(attempt: Any) -> None:
    if attempt.image_request is None or attempt.image_phase is None:
        raise ValueError("image_generation attempts require image request and phase")
    if attempt.image_request.attempt_id != attempt.attempt_id:
        raise ValueError("image attempt identity does not match request")
    if attempt.base_dependency_graph is None:
        raise ValueError("image_generation attempts require base dependency graph")
    all_phases = {
        "request",
        "submit_intent",
        "provider_call",
        "materialize",
        "validate",
        "candidate",
        "activate",
    }
    allowed_phases = {
        "running": all_phases,
        "succeeded": {"activate"},
        "failed": all_phases,
        "interrupted": {"request", "materialize", "validate", "candidate"},
        "outcome_unknown": all_phases - {"request"},
    }
    if attempt.image_phase not in allowed_phases[attempt.status.value]:
        raise ValueError("image attempt status and phase are inconsistent")
    candidate_bundle = (
        attempt.candidate_project,
        attempt.candidate_registry,
        attempt.candidate_dependency_graph,
        attempt.candidate_dependency_states_hash,
    )
    if attempt.image_phase in {"candidate", "activate"}:
        if not all(item is not None for item in candidate_bundle):
            raise ValueError("image candidate phase requires exact candidate bundle")
        if attempt.candidate_image_asset_ids != (
            attempt.image_request.output_asset_id,
        ):
            raise ValueError("image candidate asset ID must match request output")
    elif any(item is not None for item in candidate_bundle) or (
        attempt.candidate_image_asset_ids
    ):
        raise ValueError("image candidate bundle requires candidate or activate phase")


def prune_attempt_fields(data: dict[str, object], operation: str) -> None:
    if operation != "voice_generation":
        for field in _VOICE_FIELDS:
            data.pop(field, None)
    if operation != "image_generation":
        for field in _IMAGE_FIELDS:
            data.pop(field, None)
    if operation != "video_generation":
        for field in _VIDEO_FIELDS:
            data.pop(field, None)
    if operation not in {"voice_generation", "image_generation"}:
        data.pop("provider_request_id", None)


def has_p6_state(manifest: Any) -> bool:
    top_level_state = manifest.active_qa_policy is not None or any(
        (
            manifest.active_review_receipts,
            manifest.review_states,
            manifest.active_approved_repair,
            manifest.repair_outcome_receipts,
            manifest.final_acceptance_state,
        )
    )
    attempt_state = any(
        attempt.operation in {"review", "repair"}
        or attempt.review_request is not None
        or attempt.review_phase is not None
        or attempt.approved_repair_receipt is not None
        for attempt in manifest.attempts
    )
    return top_level_state or attempt_state


def reject_explicit_paid_provider_fields(value: object) -> object:
    if not isinstance(value, Mapping):
        return value
    manifest_version = value.get("schema_version", "2.0")
    has_paid_attempt = any(
        isinstance(attempt, Mapping) and "paid_provider_state" in attempt
        for attempt in value.get("attempts", ())
    )
    if manifest_version not in {"2.6", "2.7", "2.8", "2.9", "2.10"} and (
        "active_paid_provider_budget" in value or has_paid_attempt
    ):
        raise ValueError(
            f"Production Manifest {manifest_version} cannot contain explicit paid Provider fields"
        )
    return value


def reject_explicit_p8_video_fields(value: object) -> object:
    if not isinstance(value, Mapping):
        return value
    manifest_version = value.get("schema_version", "2.0")
    if manifest_version == "2.7":
        continuity_fields = {
            "terminal_frame_evidence",
            "terminal_frame_extraction",
            "candidate_continuity_asset_ids",
        }
        for attempt in value.get("attempts", ()):
            if not isinstance(attempt, Mapping):
                continue
            state = attempt.get("video_generation_state")
            if isinstance(state, Mapping) and continuity_fields.intersection(state):
                raise ValueError(
                    "Production Manifest 2.7 cannot contain explicit "
                    "Shot continuity fields; Manifest 2.8 is required"
                )
        return value
    if manifest_version == "2.8":
        for attempt in value.get("attempts", ()):
            if not isinstance(attempt, Mapping):
                continue
            state = attempt.get("video_generation_state")
            if isinstance(state, Mapping) and "continuity_evaluation" in state:
                raise ValueError(
                    "Production Manifest 2.8 cannot contain durable continuity "
                    "evaluation fields; Manifest 2.9 is required"
                )
        return value
    if manifest_version == "2.9":
        for attempt in value.get("attempts", ()):
            if not isinstance(attempt, Mapping):
                continue
            state = attempt.get("video_generation_state")
            evaluation = (
                state.get("continuity_evaluation")
                if isinstance(state, Mapping)
                else None
            )
            if isinstance(evaluation, Mapping) and (
                "probe" in evaluation or "provenance" in evaluation
            ):
                raise ValueError(
                    "Production Manifest 2.9 cannot contain continuity capture "
                    "checkpoint fields; Manifest 2.10 is required"
                )
        return value
    if manifest_version == "2.10":
        for attempt in value.get("attempts", ()):
            if not isinstance(attempt, Mapping):
                continue
            state = attempt.get("video_generation_state")
            evaluation = (
                state.get("continuity_evaluation")
                if isinstance(state, Mapping)
                else None
            )
            if (
                isinstance(evaluation, Mapping)
                and evaluation.get("phase") == ContinuityEvaluationPhase.EVIDENCED.value
                and (
                    evaluation.get("probe") is None
                    or evaluation.get("provenance") is None
                )
            ):
                raise ValueError(
                    "Production Manifest 2.10 evidenced continuity requires "
                    "exact probe and provenance checkpoints"
                )
        return value
    for attempt in value.get("attempts", ()):
        if isinstance(attempt, Mapping) and (
            attempt.get("operation") == "video_generation"
            or "video_generation_state" in attempt
        ):
            raise ValueError(
                f"Production Manifest {manifest_version} "
                "cannot contain explicit P8 video fields"
            )
    return value


def reject_explicit_p7_fields(value: object) -> object:
    if not isinstance(value, Mapping):
        return value
    manifest_version = value.get("schema_version", "2.0")
    if manifest_version in {"2.5", "2.6", "2.7", "2.8", "2.9", "2.10"}:
        return value
    image_fields = {"image_request", "image_phase", "candidate_image_asset_ids"}
    for attempt in value.get("attempts", ()):
        if isinstance(attempt, Mapping) and (
            attempt.get("operation") == "image_generation"
            or image_fields.intersection(attempt)
        ):
            raise ValueError(
                f"Production Manifest {manifest_version} cannot contain explicit P7 image fields"
            )
    return value


def validate_paid_provider_manifest(manifest: Any) -> None:
    paid_attempts = [
        attempt
        for attempt in manifest.attempts
        if attempt.paid_provider_state is not None
    ]
    if paid_attempts and manifest.active_paid_provider_budget is None:
        raise ValueError("paid Provider attempts require an active paid Provider budget")
    gate_owners = [
        attempt.paid_provider_state.gate_receipt.gate_receipt_fingerprint
        for attempt in paid_attempts
    ]
    submit_owners = [
        attempt.paid_provider_state.submit_receipt.submit_receipt_fingerprint
        for attempt in paid_attempts
        if attempt.paid_provider_state.submit_receipt is not None
    ]
    if len(gate_owners) != len(set(gate_owners)) or len(submit_owners) != len(
        set(submit_owners)
    ):
        raise ValueError("paid Provider receipt ownership must be unique")
