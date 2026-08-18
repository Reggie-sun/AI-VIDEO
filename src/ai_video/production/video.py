"""Provider-neutral generated-video contracts with no I/O or provider routing policy."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Iterable, Literal, Protocol
from urllib.parse import urlsplit

from pydantic import ConfigDict, Field, field_validator, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    StrictModel,
)
from ai_video.production.paid_provider import (
    DurablePaidProviderSubmitPermit,
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
    validate_paid_provider_authorization,
)


_SAFE_ID = re.compile(r"^[A-Za-z0-9._:/-]{1,256}$")
_SHA256 = r"^[0-9a-f]{64}$"
_MIME_TYPE = r"^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$"
_ROLE_ORDER = {"first_frame": 0, "reference": 1}


def _video_error(code: ErrorCode, message: str) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, retryable=False)


def _require_aware(value: datetime, label: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value


def _canonical_https_origin(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("video destination must be a canonical HTTPS origin") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("video destination must be a canonical HTTPS origin")
    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    canonical = f"https://{host}"
    if port is not None and port != 443:
        canonical = f"{canonical}:{port}"
    if value != canonical:
        raise ValueError("video destination must be a canonical HTTPS origin")
    return value


class _VideoStrictModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class VideoGenerationMode(str, Enum):
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"


class VideoExecutionKind(str, Enum):
    LOCAL = "local"
    REMOTE = "remote"


class BillingKind(str, Enum):
    LOCAL_UNMETERED = "local_unmetered"
    METERED = "metered"


class VideoTaskState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class VideoOutputRequirement(_VideoStrictModel):
    duration_seconds: int = Field(strict=True, gt=0, le=600)
    width: int = Field(strict=True, gt=0, le=16384)
    height: int = Field(strict=True, gt=0, le=16384)
    fps: int | None = Field(default=None, strict=True, gt=0, le=240)
    container: Literal["mp4"]
    mime_type: Literal["video/mp4"]
    native_audio: bool


class VideoImageReferenceBinding(_VideoStrictModel):
    role: Literal["first_frame", "reference"]
    asset_id: str = Field(pattern=_SAFE_ID.pattern)
    asset_sha256: str = Field(pattern=_SHA256)
    mime_type: str = Field(pattern=_MIME_TYPE)
    width: int = Field(strict=True, gt=0)
    height: int = Field(strict=True, gt=0)
    size_bytes: int | None = Field(default=None, strict=True, ge=0)


class ProviderProfilePointer(_VideoStrictModel):
    profile_id: str = Field(pattern=_SAFE_ID.pattern)
    profile_version: str = Field(pattern=_SAFE_ID.pattern)
    profile_path: Path
    profile_sha256: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _canonical_path(self) -> "ProviderProfilePointer":
        if (
            self.profile_path.is_absolute()
            or ".." in self.profile_path.parts
            or self.profile_path
            != Path(f"provider-profiles/{self.profile_sha256}.json")
        ):
            raise ValueError("provider profile path must be canonical and content-addressed")
        return self


class VideoGenerationRequest(_VideoStrictModel):
    generation_id: str = Field(pattern=_SAFE_ID.pattern)
    provider_name: str = Field(pattern=_SAFE_ID.pattern)
    provider_kind: str = Field(pattern=_SAFE_ID.pattern)
    model_id: str = Field(pattern=_SAFE_ID.pattern)
    provider_profile: ProviderProfilePointer
    target_shot_id: str = Field(pattern=_SAFE_ID.pattern)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    target_asset_role: str = Field(pattern=_SAFE_ID.pattern)
    target_visual_strategy: Literal["generated_video"]
    mode: VideoGenerationMode
    prompt_text: str = Field(min_length=1)
    negative_prompt_text: str
    image_bindings: tuple[VideoImageReferenceBinding, ...]
    output_requirement: VideoOutputRequirement
    seed: int | None = Field(default=None, strict=True, ge=0)
    base_project: ProjectSnapshotPointer
    base_registry: RegistrySnapshotPointer
    base_dependency_graph: DependencyGraphSnapshotPointer
    input_artifact_ids: tuple[str, ...] = Field(min_length=1)
    output_asset_id: str = Field(pattern=_SAFE_ID.pattern)
    request_input_hash: str = Field(pattern=_SHA256)

    @field_validator("prompt_text", "negative_prompt_text")
    @classmethod
    def _require_nfc(cls, value: str) -> str:
        if unicodedata.normalize("NFC", value) != value:
            raise ValueError("video prompt text must use Unicode NFC normalization")
        return value

    @staticmethod
    def _fingerprint_payload(data: dict[str, object]) -> dict[str, object]:
        return {
            "schema": "ai-video-generation-request/1",
            **{
                key: value
                for key, value in data.items()
                if key not in {"generation_id", "request_input_hash"}
            },
        }

    @model_validator(mode="after")
    def _validate_request(self) -> "VideoGenerationRequest":
        if self.mode is VideoGenerationMode.TEXT_TO_VIDEO and self.image_bindings:
            raise ValueError("text-to-video requests cannot contain image bindings")
        if self.mode is VideoGenerationMode.IMAGE_TO_VIDEO and not self.image_bindings:
            raise ValueError("image-to-video requests require image bindings")
        keys = tuple(
            (_ROLE_ORDER[binding.role], binding.asset_id)
            for binding in self.image_bindings
        )
        if keys != tuple(sorted(keys)):
            raise ValueError("video image bindings must use canonical role and asset order")
        if len({(binding.role, binding.asset_id) for binding in self.image_bindings}) != len(
            self.image_bindings
        ):
            raise ValueError("video image bindings must be unique")
        if len(set(self.input_artifact_ids)) != len(self.input_artifact_ids):
            raise ValueError("video input artifact IDs must be unique")
        if self.request_input_hash != canonical_sha256(
            self._fingerprint_payload(self.model_dump(mode="json"))
        ):
            raise ValueError("request_input_hash does not match video request")
        return self

    @classmethod
    def create(cls, **values: object) -> "VideoGenerationRequest":
        data = dict(values)
        candidate = cls.model_construct(**data, request_input_hash="0" * 64)
        data["request_input_hash"] = canonical_sha256(
            cls._fingerprint_payload(
                candidate.model_dump(mode="json", warnings=False)
            )
        )
        return cls.model_validate(data)


class VideoCapabilityVariant(_VideoStrictModel):
    capability_id: str = Field(pattern=_SAFE_ID.pattern)
    provider_kind: str = Field(pattern=_SAFE_ID.pattern)
    model_id: str = Field(pattern=_SAFE_ID.pattern)
    profile_version: str = Field(pattern=_SAFE_ID.pattern)
    execution_kind: VideoExecutionKind
    billing_kind: BillingKind
    mode: VideoGenerationMode
    output: VideoOutputRequirement
    allowed_image_roles: tuple[Literal["first_frame", "reference"], ...]
    required_first_frame: bool
    max_reference_count: int = Field(strict=True, ge=0, le=32)
    allowed_image_mime_types: tuple[str, ...]
    max_image_bytes: int = Field(strict=True, gt=0)
    min_image_width: int = Field(strict=True, gt=0)
    min_image_height: int = Field(strict=True, gt=0)
    negative_prompt_supported: bool
    seed_supported: bool
    fps_supported: bool
    idempotent_submit: bool
    lookup_supported: bool

    @model_validator(mode="after")
    def _validate_variant(self) -> "VideoCapabilityVariant":
        if len(set(self.allowed_image_roles)) != len(self.allowed_image_roles):
            raise ValueError("video capability image roles must be unique")
        if len(set(self.allowed_image_mime_types)) != len(self.allowed_image_mime_types):
            raise ValueError("video capability image MIME types must be unique")
        if self.mode is VideoGenerationMode.TEXT_TO_VIDEO and (
            self.allowed_image_roles or self.required_first_frame or self.max_reference_count
        ):
            raise ValueError("text-to-video capability cannot declare image bindings")
        if self.required_first_frame and "first_frame" not in self.allowed_image_roles:
            raise ValueError("required first frame must be an allowed image role")
        if (
            self.execution_kind is VideoExecutionKind.LOCAL
            and self.billing_kind is not BillingKind.LOCAL_UNMETERED
        ) or (
            self.execution_kind is VideoExecutionKind.REMOTE
            and self.billing_kind is not BillingKind.METERED
        ):
            raise ValueError(
                "video capability execution and billing kinds must use a supported pair"
            )
        return self


class VideoProviderCapabilities(_VideoStrictModel):
    provider_name: str = Field(pattern=_SAFE_ID.pattern)
    variants: tuple[VideoCapabilityVariant, ...] = Field(min_length=1)
    capabilities_fingerprint: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "VideoProviderCapabilities":
        if len({variant.capability_id for variant in self.variants}) != len(self.variants):
            raise ValueError("video capability IDs must be unique")
        if self.capabilities_fingerprint != canonical_sha256(
            self.model_dump(mode="json", exclude={"capabilities_fingerprint"})
        ):
            raise ValueError("capabilities_fingerprint does not match variants")
        return self

    @classmethod
    def create(
        cls,
        *,
        provider_name: str,
        variants: tuple[VideoCapabilityVariant, ...],
    ) -> "VideoProviderCapabilities":
        data: dict[str, object] = {
            "provider_name": provider_name,
            "variants": variants,
        }
        candidate = cls.model_construct(**data, capabilities_fingerprint="0" * 64)
        data["capabilities_fingerprint"] = canonical_sha256(
            candidate.model_dump(
                mode="json", exclude={"capabilities_fingerprint"}, warnings=False
            )
        )
        return cls.model_validate(data)


class ResolvedVideoGenerationRequest(_VideoStrictModel):
    generation_id: str = Field(pattern=_SAFE_ID.pattern)
    request_input_hash: str = Field(pattern=_SHA256)
    provider_name: str = Field(pattern=_SAFE_ID.pattern)
    provider_kind: str = Field(pattern=_SAFE_ID.pattern)
    model_id: str = Field(pattern=_SAFE_ID.pattern)
    provider_profile: ProviderProfilePointer
    capability_id: str = Field(pattern=_SAFE_ID.pattern)
    execution_kind: VideoExecutionKind
    billing_kind: BillingKind
    mode: VideoGenerationMode
    image_bindings: tuple[VideoImageReferenceBinding, ...]
    effective_output: VideoOutputRequirement
    effective_seed: int | None = Field(default=None, strict=True, ge=0)
    effective_negative_prompt_text: str
    output_asset_id: str = Field(pattern=_SAFE_ID.pattern)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    desired_generation_fingerprint: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "ResolvedVideoGenerationRequest":
        data = self.model_dump(
            mode="json",
            exclude={"resolved_generation_hash", "desired_generation_fingerprint"},
        )
        expected = canonical_sha256({"schema": "ai-video-resolved-request/1", **data})
        if self.resolved_generation_hash != expected:
            raise ValueError("resolved_generation_hash does not match resolved request")
        if self.desired_generation_fingerprint != expected:
            raise ValueError("desired generation fingerprint must equal resolved hash")
        return self

    @classmethod
    def create(
        cls,
        *,
        request: VideoGenerationRequest,
        capability: VideoCapabilityVariant,
        effective_output: VideoOutputRequirement,
        effective_seed: int | None,
        effective_negative_prompt_text: str,
    ) -> "ResolvedVideoGenerationRequest":
        if (
            capability.provider_kind != request.provider_kind
            or capability.model_id != request.model_id
            or capability.profile_version != request.provider_profile.profile_version
            or capability.mode is not request.mode
        ):
            raise _video_error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Video request does not match the selected capability variant.",
            )
        if effective_output != request.output_requirement or effective_output != capability.output:
            raise _video_error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Video output requirement is not an exact supported capability combination.",
            )
        if (
            request.negative_prompt_text
            and not effective_negative_prompt_text
        ) or (request.seed is not None and effective_seed is None):
            raise _video_error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "Video resolution cannot silently drop requested creative settings.",
            )
        if request.negative_prompt_text and not capability.negative_prompt_supported:
            raise _video_error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Selected video capability does not support a negative prompt.",
            )
        if request.seed is not None and not capability.seed_supported:
            raise _video_error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Selected video capability does not support a seed.",
            )
        if request.output_requirement.fps is not None and not capability.fps_supported:
            raise _video_error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Selected video capability does not support a requested FPS.",
            )
        first_frames = sum(binding.role == "first_frame" for binding in request.image_bindings)
        references = sum(binding.role == "reference" for binding in request.image_bindings)
        if (
            (capability.required_first_frame and first_frames != 1)
            or first_frames > 1
            or references > capability.max_reference_count
            or any(binding.role not in capability.allowed_image_roles for binding in request.image_bindings)
            or any(
                binding.mime_type not in capability.allowed_image_mime_types
                or binding.width < capability.min_image_width
                or binding.height < capability.min_image_height
                or (
                    binding.size_bytes is not None
                    and binding.size_bytes > capability.max_image_bytes
                )
                for binding in request.image_bindings
            )
        ):
            raise _video_error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Video image bindings do not satisfy the selected capability variant.",
            )
        data: dict[str, object] = {
            "generation_id": request.generation_id,
            "request_input_hash": request.request_input_hash,
            "provider_name": request.provider_name,
            "provider_kind": request.provider_kind,
            "model_id": request.model_id,
            "provider_profile": request.provider_profile,
            "capability_id": capability.capability_id,
            "execution_kind": capability.execution_kind,
            "billing_kind": capability.billing_kind,
            "mode": request.mode,
            "image_bindings": request.image_bindings,
            "effective_output": effective_output,
            "effective_seed": effective_seed,
            "effective_negative_prompt_text": effective_negative_prompt_text,
            "output_asset_id": request.output_asset_id,
        }
        candidate = cls.model_construct(
            **data,
            resolved_generation_hash="0" * 64,
            desired_generation_fingerprint="0" * 64,
        )
        fingerprint = canonical_sha256(
            {
                "schema": "ai-video-resolved-request/1",
                **candidate.model_dump(
                    mode="json",
                    exclude={"resolved_generation_hash", "desired_generation_fingerprint"},
                    warnings=False,
                ),
            }
        )
        data["resolved_generation_hash"] = fingerprint
        data["desired_generation_fingerprint"] = fingerprint
        return cls.model_validate(data)


class VideoGenerationPreview(_VideoStrictModel):
    resolved_generation_hash: str = Field(pattern=_SHA256)
    execution_kind: VideoExecutionKind
    billing_kind: BillingKind
    estimated_cost_upper_bound_microunits: int | None = Field(
        default=None, strict=True, ge=0
    )
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    destination: str | None = None
    egress_item_ids: tuple[str, ...]
    preview_fingerprint: str = Field(pattern=_SHA256)

    @field_validator("destination")
    @classmethod
    def _validate_destination(cls, value: str | None) -> str | None:
        return None if value is None else _canonical_https_origin(value)

    @model_validator(mode="after")
    def _validate_preview(self) -> "VideoGenerationPreview":
        if self.execution_kind is VideoExecutionKind.REMOTE:
            if self.destination is None or not self.egress_item_ids:
                raise ValueError("remote video preview requires destination and egress items")
        elif self.destination is not None or self.egress_item_ids:
            raise ValueError("local video preview cannot contain remote egress fields")
        if self.billing_kind is BillingKind.METERED:
            if self.estimated_cost_upper_bound_microunits is None or self.currency is None:
                raise ValueError("metered video preview requires a bounded cost and currency")
        elif self.estimated_cost_upper_bound_microunits is not None or self.currency is not None:
            raise ValueError("unmetered video preview cannot contain metered cost fields")
        if len(set(self.egress_item_ids)) != len(self.egress_item_ids):
            raise ValueError("video preview egress item IDs must be unique")
        if self.preview_fingerprint != canonical_sha256(
            self.model_dump(mode="json", exclude={"preview_fingerprint"})
        ):
            raise ValueError("preview_fingerprint does not match video preview")
        return self

    @classmethod
    def create(
        cls,
        *,
        resolved: ResolvedVideoGenerationRequest,
        estimated_cost_upper_bound_microunits: int | None,
        currency: str | None,
        destination: str | None,
        egress_item_ids: tuple[str, ...],
    ) -> "VideoGenerationPreview":
        data: dict[str, object] = {
            "resolved_generation_hash": resolved.resolved_generation_hash,
            "execution_kind": resolved.execution_kind,
            "billing_kind": resolved.billing_kind,
            "estimated_cost_upper_bound_microunits": estimated_cost_upper_bound_microunits,
            "currency": currency,
            "destination": destination,
            "egress_item_ids": egress_item_ids,
        }
        candidate = cls.model_construct(**data, preview_fingerprint="0" * 64)
        data["preview_fingerprint"] = canonical_sha256(
            candidate.model_dump(
                mode="json", exclude={"preview_fingerprint"}, warnings=False
            )
        )
        return cls.model_validate(data)


class VideoSubmitResult(_VideoStrictModel):
    generation_id: str = Field(pattern=_SAFE_ID.pattern)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    external_effect_id: str = Field(pattern=_SAFE_ID.pattern)
    submitted_at: datetime
    result_fingerprint: str = Field(pattern=_SHA256)

    @field_validator("submitted_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return _require_aware(value, "video submit result timestamp")

    @model_validator(mode="after")
    def _validate_seal(self) -> "VideoSubmitResult":
        if self.result_fingerprint != canonical_sha256(
            self.model_dump(mode="json", exclude={"result_fingerprint"})
        ):
            raise ValueError("result_fingerprint does not match video submit result")
        return self

    @classmethod
    def create(
        cls,
        *,
        resolved: ResolvedVideoGenerationRequest,
        external_effect_id: str,
        submitted_at: datetime,
    ) -> "VideoSubmitResult":
        data: dict[str, object] = {
            "generation_id": resolved.generation_id,
            "resolved_generation_hash": resolved.resolved_generation_hash,
            "external_effect_id": external_effect_id,
            "submitted_at": submitted_at,
        }
        candidate = cls.model_construct(**data, result_fingerprint="0" * 64)
        data["result_fingerprint"] = canonical_sha256(
            candidate.model_dump(
                mode="json", exclude={"result_fingerprint"}, warnings=False
            )
        )
        return cls.model_validate(data)


class VideoSubmission(_VideoStrictModel):
    generation_id: str = Field(pattern=_SAFE_ID.pattern)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    paid_submit_receipt_fingerprint: str = Field(pattern=_SHA256)
    submitted_at: datetime
    submission_fingerprint: str = Field(pattern=_SHA256)

    @field_validator("submitted_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return _require_aware(value, "video submission timestamp")

    @model_validator(mode="after")
    def _validate_seal(self) -> "VideoSubmission":
        if self.submission_fingerprint != canonical_sha256(
            self.model_dump(mode="json", exclude={"submission_fingerprint"})
        ):
            raise ValueError("submission_fingerprint does not match video submission")
        return self

    @classmethod
    def from_paid_submit_receipt(
        cls,
        *,
        resolved: ResolvedVideoGenerationRequest,
        receipt: PaidProviderSubmitReceipt,
    ) -> "VideoSubmission":
        if (
            receipt.outcome is not PaidProviderSubmitOutcome.ACCEPTED
            or receipt.request_fingerprint != resolved.resolved_generation_hash
            or receipt.external_effect_id is None
        ):
            raise _video_error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "Video submission requires an exact accepted Paid Provider receipt.",
            )
        data: dict[str, object] = {
            "generation_id": resolved.generation_id,
            "resolved_generation_hash": resolved.resolved_generation_hash,
            "paid_submit_receipt_fingerprint": receipt.submit_receipt_fingerprint,
            "submitted_at": receipt.recorded_at,
        }
        candidate = cls.model_construct(**data, submission_fingerprint="0" * 64)
        data["submission_fingerprint"] = canonical_sha256(
            candidate.model_dump(
                mode="json", exclude={"submission_fingerprint"}, warnings=False
            )
        )
        return cls.model_validate(data)


class VideoTaskObservation(_VideoStrictModel):
    submission_fingerprint: str = Field(pattern=_SHA256)
    paid_submit_receipt_fingerprint: str = Field(pattern=_SHA256)
    state: VideoTaskState
    observed_at: datetime
    progress_milli: int | None = Field(default=None, strict=True, ge=0, le=1000)
    provider_file_id: str | None = Field(default=None, pattern=_SAFE_ID.pattern)
    observation_fingerprint: str = Field(pattern=_SHA256)

    @field_validator("observed_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return _require_aware(value, "video observation timestamp")

    @model_validator(mode="after")
    def _validate_observation(self) -> "VideoTaskObservation":
        if self.state is VideoTaskState.SUCCEEDED and self.provider_file_id is None:
            raise ValueError("succeeded video observation requires a provider file ID")
        if self.state is VideoTaskState.FAILED and self.provider_file_id is not None:
            raise ValueError("failed video observation cannot contain a provider file ID")
        if self.observation_fingerprint != canonical_sha256(
            self.model_dump(mode="json", exclude={"observation_fingerprint"})
        ):
            raise ValueError("observation_fingerprint does not match video observation")
        return self

    @classmethod
    def create(
        cls,
        *,
        submission: VideoSubmission,
        state: VideoTaskState,
        observed_at: datetime,
        progress_milli: int | None = None,
        provider_file_id: str | None = None,
    ) -> "VideoTaskObservation":
        data: dict[str, object] = {
            "submission_fingerprint": submission.submission_fingerprint,
            "paid_submit_receipt_fingerprint": submission.paid_submit_receipt_fingerprint,
            "state": state,
            "observed_at": observed_at,
            "progress_milli": progress_milli,
            "provider_file_id": provider_file_id,
        }
        candidate = cls.model_construct(**data, observation_fingerprint="0" * 64)
        data["observation_fingerprint"] = canonical_sha256(
            candidate.model_dump(
                mode="json", exclude={"observation_fingerprint"}, warnings=False
            )
        )
        return cls.model_validate(data)


class VideoFetchReceipt(_VideoStrictModel):
    submission_fingerprint: str = Field(pattern=_SHA256)
    observation_fingerprint: str = Field(pattern=_SHA256)
    paid_submit_receipt_fingerprint: str = Field(pattern=_SHA256)
    provider_file_id: str = Field(pattern=_SAFE_ID.pattern)
    content_type: Literal["video/mp4"]
    size_bytes: int = Field(strict=True, gt=0)
    artifact_sha256: str = Field(pattern=_SHA256)
    fetched_at: datetime
    fetch_fingerprint: str = Field(pattern=_SHA256)

    @field_validator("fetched_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return _require_aware(value, "video fetch timestamp")

    @model_validator(mode="after")
    def _validate_seal(self) -> "VideoFetchReceipt":
        if self.fetch_fingerprint != canonical_sha256(
            self.model_dump(mode="json", exclude={"fetch_fingerprint"})
        ):
            raise ValueError("fetch_fingerprint does not match video fetch receipt")
        return self

    @classmethod
    def create(
        cls,
        *,
        submission: VideoSubmission,
        observation: VideoTaskObservation,
        content_type: Literal["video/mp4"],
        size_bytes: int,
        artifact_sha256: str,
        fetched_at: datetime,
    ) -> "VideoFetchReceipt":
        if (
            observation.submission_fingerprint != submission.submission_fingerprint
            or observation.paid_submit_receipt_fingerprint
            != submission.paid_submit_receipt_fingerprint
            or observation.state is not VideoTaskState.SUCCEEDED
            or observation.provider_file_id is None
        ):
            raise _video_error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "Video fetch requires an exact succeeded task observation.",
            )
        data: dict[str, object] = {
            "submission_fingerprint": submission.submission_fingerprint,
            "observation_fingerprint": observation.observation_fingerprint,
            "paid_submit_receipt_fingerprint": submission.paid_submit_receipt_fingerprint,
            "provider_file_id": observation.provider_file_id,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "artifact_sha256": artifact_sha256,
            "fetched_at": fetched_at,
        }
        candidate = cls.model_construct(**data, fetch_fingerprint="0" * 64)
        data["fetch_fingerprint"] = canonical_sha256(
            candidate.model_dump(
                mode="json", exclude={"fetch_fingerprint"}, warnings=False
            )
        )
        return cls.model_validate(data)


class VideoProviderFailure(_VideoStrictModel):
    operation: Literal["resolve", "preview", "submit", "status", "fetch"]
    failure_kind: Literal[
        "configuration",
        "authentication",
        "unsupported_capability",
        "invalid_request",
        "quota_rate_limit",
        "provider_unavailable",
        "generation_rejected",
        "generation_failed",
        "poll_timeout",
        "download_failure",
        "artifact_invalid",
    ]
    outcome_certainty: Literal["known_no_effect", "outcome_unknown", "known_effect"]
    retry_safety: Literal[
        "safe_same_effect",
        "unsafe_same_effect",
        "new_generation_only",
        "not_retryable",
    ]
    generic_retryable: bool
    public_error_code: ErrorCode


def build_video_paid_permit_binding(
    request: ResolvedVideoGenerationRequest,
    video_preview: VideoGenerationPreview,
    paid_preview: PaidProviderCallPreview,
    authorization: PaidProviderAuthorizationDecision,
) -> dict[str, str]:
    """Validate and project the exact shared Paid Provider permit binding."""

    if (
        request.execution_kind is not VideoExecutionKind.REMOTE
        or request.billing_kind is not BillingKind.METERED
        or video_preview.resolved_generation_hash != request.resolved_generation_hash
        or video_preview.execution_kind is not VideoExecutionKind.REMOTE
        or video_preview.billing_kind is not BillingKind.METERED
        or paid_preview.operation != "video_generation"
        or paid_preview.request_fingerprint != request.resolved_generation_hash
        or paid_preview.provider_kind != request.provider_kind
        or paid_preview.model_id != request.model_id
        or paid_preview.destination != video_preview.destination
        or paid_preview.currency != video_preview.currency
        or paid_preview.estimated_cost_upper_bound_microunits
        != video_preview.estimated_cost_upper_bound_microunits
        or tuple(item.item_id for item in paid_preview.egress_items)
        != video_preview.egress_item_ids
    ):
        raise _video_error(
            ErrorCode.VIDEO_REQUEST_INVALID,
            "Paid Provider preview does not match the resolved video request.",
        )
    validate_paid_provider_authorization(
        paid_preview,
        authorization,
        now=authorization.issued_at,
    )
    return {
        "attempt_id": paid_preview.attempt_id,
        "operation": paid_preview.operation,
        "request_fingerprint": paid_preview.request_fingerprint,
        "destination": paid_preview.destination,
        "provider_kind": paid_preview.provider_kind,
        "model_id": paid_preview.model_id,
        "currency": paid_preview.currency,
        "estimated_cost_upper_bound_microunits": str(
            paid_preview.estimated_cost_upper_bound_microunits
        ),
        "provider_policy_snapshot_id": paid_preview.provider_policy_snapshot_id,
        "retention_mode": paid_preview.retention_mode,
        "secret_reference_kind": paid_preview.secret_reference.kind,
        "secret_reference_id": paid_preview.secret_reference.reference_id,
    }


class VideoProvider(Protocol):
    def capabilities(self) -> VideoProviderCapabilities: ...

    def resolve(self, request: VideoGenerationRequest) -> ResolvedVideoGenerationRequest: ...

    def preview(self, request: ResolvedVideoGenerationRequest) -> VideoGenerationPreview: ...

    def submit(
        self,
        request: ResolvedVideoGenerationRequest,
        video_preview: VideoGenerationPreview,
        paid_preview: PaidProviderCallPreview | None,
        authorization: PaidProviderAuthorizationDecision | None,
        permit: DurablePaidProviderSubmitPermit | None,
    ) -> VideoSubmitResult: ...

    def get_status(
        self,
        submission: VideoSubmission,
        submit_receipt: PaidProviderSubmitReceipt,
    ) -> VideoTaskObservation: ...

    def fetch(
        self,
        submission: VideoSubmission,
        submit_receipt: PaidProviderSubmitReceipt,
        observation: VideoTaskObservation,
        sink: BinaryIO,
    ) -> VideoFetchReceipt: ...


class VideoProviderRegistry:
    """Exact injected provider lookup with no selection or fallback behavior."""

    def __init__(self, providers: Iterable[tuple[str, object]]) -> None:
        entries: dict[str, object] = {}
        for name, provider in providers:
            if _SAFE_ID.fullmatch(name) is None:
                raise ValueError("video provider registry name is invalid")
            if name in entries:
                raise ValueError(f"duplicate video provider name: {name}")
            entries[name] = provider
        self._providers = entries

    def resolve(self, name: str) -> object:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise _video_error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                f"Video provider is not registered: {name}",
            ) from exc


__all__ = [
    "BillingKind",
    "ProviderProfilePointer",
    "ResolvedVideoGenerationRequest",
    "VideoCapabilityVariant",
    "VideoExecutionKind",
    "VideoFetchReceipt",
    "VideoGenerationMode",
    "VideoGenerationPreview",
    "VideoGenerationRequest",
    "VideoImageReferenceBinding",
    "VideoOutputRequirement",
    "VideoProvider",
    "VideoProviderCapabilities",
    "VideoProviderFailure",
    "VideoProviderRegistry",
    "VideoSubmission",
    "VideoSubmitResult",
    "VideoTaskObservation",
    "VideoTaskState",
    "build_video_paid_permit_binding",
]
