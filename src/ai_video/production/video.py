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
from ai_video.production.video_contracts import (
    VideoFlexibleOutputRequirement,
    VideoMediaCapability,
    VideoMediaReferenceBinding,
    VideoOutputCapability,
    VideoProviderTaskBinding,
    media_bindings_satisfy_capabilities,
)


_SAFE_ID = re.compile(r"^[A-Za-z0-9._:/-]{1,256}$")
_SHA256 = r"^[0-9a-f]{64}$"
_MIME_TYPE = r"^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$"
_ROLE_ORDER = {"first_frame": 0, "last_frame": 1, "reference": 2}
_MEDIA_ROLE_ORDER = {"reference_video": 0, "reference_audio": 1}


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
    REFERENCE_TO_VIDEO = "reference_to_video"
    VIDEO_EDIT = "video_edit"
    VIDEO_EXTEND = "video_extend"


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
    role: Literal["first_frame", "last_frame", "reference"]
    asset_id: str = Field(pattern=_SAFE_ID.pattern)
    asset_sha256: str = Field(pattern=_SHA256)
    mime_type: str = Field(pattern=_MIME_TYPE)
    width: int = Field(strict=True, gt=0)
    height: int = Field(strict=True, gt=0)
    size_bytes: int | None = Field(default=None, strict=True, ge=0)


class ContinuityArtifactIdentity(_VideoStrictModel):
    artifact_id: str = Field(pattern=_SAFE_ID.pattern)
    revision: int = Field(strict=True, ge=1)
    content_hash: str = Field(pattern=_SHA256)


class ContinuityConstraintSet(_VideoStrictModel):
    scene_identity: ContinuityArtifactIdentity
    character_identities: tuple[ContinuityArtifactIdentity, ...] = Field(
        min_length=1
    )
    camera_axis: str = Field(min_length=1)
    framing: str = Field(min_length=1)
    lighting: str = Field(min_length=1)
    color: str = Field(min_length=1)
    motion_direction: str = Field(min_length=1)
    exit_state: str = Field(min_length=1)
    entrance_state: str = Field(min_length=1)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "ContinuityConstraintSet":
        identities = tuple(
            (item.artifact_id, item.revision, item.content_hash)
            for item in self.character_identities
        )
        if identities != tuple(sorted(identities)) or len(identities) != len(
            set(identities)
        ):
            raise ValueError("continuity character identities must be unique and ordered")
        text_values = (
            self.camera_axis,
            self.framing,
            self.lighting,
            self.color,
            self.motion_direction,
            self.exit_state,
            self.entrance_state,
        )
        if any(unicodedata.normalize("NFC", value) != value for value in text_values):
            raise ValueError("continuity constraint text must use Unicode NFC normalization")
        expected = canonical_sha256(
            {
                "schema": "ai-video-continuity-constraints/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        )
        if self.content_hash != expected:
            raise ValueError("continuity constraint hash does not match content")
        return self

    @classmethod
    def create(cls, **values: object) -> "ContinuityConstraintSet":
        data = dict(values)
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            {
                "schema": "ai-video-continuity-constraints/1",
                **candidate.model_dump(
                    mode="json", exclude={"content_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


class TerminalFrameEvidence(_VideoStrictModel):
    source_shot_id: str = Field(pattern=_SAFE_ID.pattern)
    source_shot_revision: int = Field(strict=True, ge=1)
    source_shot_content_hash: str = Field(pattern=_SHA256)
    source_video_asset_id: str = Field(pattern=_SAFE_ID.pattern)
    source_video_sha256: str = Field(pattern=_SHA256)
    source_generation_id: str = Field(pattern=_SAFE_ID.pattern)
    source_request_input_hash: str = Field(pattern=_SHA256)
    source_resolved_generation_hash: str = Field(pattern=_SHA256)
    source_provenance_receipt_id: str = Field(pattern=_SAFE_ID.pattern)
    extraction_receipt_id: str = Field(pattern=_SHA256)
    source_registry: RegistrySnapshotPointer
    source_container_name: Literal["mp4"]
    source_codec_name: str = Field(min_length=1)
    source_width: int = Field(strict=True, gt=0)
    source_height: int = Field(strict=True, gt=0)
    source_fps_numerator: int = Field(strict=True, gt=0)
    source_fps_denominator: int = Field(strict=True, gt=0)
    source_duration_milliseconds: int = Field(strict=True, gt=0)
    source_frame_count: int = Field(strict=True, gt=0)
    frame_index: int = Field(strict=True, ge=0)
    timestamp_numerator: int = Field(strict=True, ge=0)
    timestamp_denominator: int = Field(strict=True, gt=0)
    selection_rule: Literal["generated_candidate_terminal", "resolved_trim_out"]
    extraction_contract_version: str = Field(pattern=_SAFE_ID.pattern)
    extractor_name: str = Field(pattern=_SAFE_ID.pattern)
    extractor_version: str = Field(pattern=_SAFE_ID.pattern)
    extracted_asset_id: str = Field(pattern=_SAFE_ID.pattern)
    extracted_sha256: str = Field(pattern=_SHA256)
    extracted_mime_type: Literal["image/png"]
    extracted_size_bytes: int = Field(strict=True, gt=0)
    extracted_width: int = Field(strict=True, gt=0)
    extracted_height: int = Field(strict=True, gt=0)
    extracted_color_space: str = Field(pattern=_SAFE_ID.pattern)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "TerminalFrameEvidence":
        if self.frame_index >= self.source_frame_count:
            raise ValueError("terminal frame index is outside source video")
        if (
            self.selection_rule == "generated_candidate_terminal"
            and self.frame_index != self.source_frame_count - 1
        ):
            raise ValueError("generated candidate terminal frame must be the last frame")
        if (
            self.timestamp_numerator * 1000
            >= self.source_duration_milliseconds * self.timestamp_denominator
        ):
            raise ValueError("terminal frame timestamp is outside source duration")
        expected = canonical_sha256(
            {
                "schema": "ai-video-terminal-frame-evidence/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        )
        if self.content_hash != expected:
            raise ValueError("terminal frame evidence hash does not match content")
        return self

    @classmethod
    def create(cls, **values: object) -> "TerminalFrameEvidence":
        data = dict(values)
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            {
                "schema": "ai-video-terminal-frame-evidence/1",
                **candidate.model_dump(
                    mode="json", exclude={"content_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


class ContinuityReferenceBinding(_VideoStrictModel):
    role: Literal["first_frame"]
    terminal_frame: TerminalFrameEvidence
    target_shot_id: str = Field(pattern=_SAFE_ID.pattern)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    constraints: ContinuityConstraintSet
    binding_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "ContinuityReferenceBinding":
        expected = canonical_sha256(
            {
                "schema": "ai-video-continuity-reference-binding/1",
                **self.model_dump(mode="json", exclude={"binding_hash"}),
            }
        )
        if self.binding_hash != expected:
            raise ValueError("continuity binding hash does not match content")
        return self

    @classmethod
    def create(cls, **values: object) -> "ContinuityReferenceBinding":
        data = dict(values)
        candidate = cls.model_construct(**data, binding_hash="0" * 64)
        data["binding_hash"] = canonical_sha256(
            {
                "schema": "ai-video-continuity-reference-binding/1",
                **candidate.model_dump(
                    mode="json", exclude={"binding_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


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
    continuity_binding: ContinuityReferenceBinding | None = None
    seal_terminal_frame: bool = Field(default=False, strict=True)
    media_bindings: tuple[VideoMediaReferenceBinding, ...] = ()
    output_requirement: VideoOutputRequirement | VideoFlexibleOutputRequirement
    seed: int | None = Field(default=None, strict=True, ge=-1)
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
        media_bindings = data.get("media_bindings")
        mode = data.get("mode")
        output = data.get("output_requirement")
        image_bindings = data.get("image_bindings")
        continuity = data.get("continuity_binding")
        seal_terminal_frame = data.get("seal_terminal_frame", False)
        advanced = bool(
            media_bindings
            or mode
            in {
                VideoGenerationMode.REFERENCE_TO_VIDEO.value,
                VideoGenerationMode.VIDEO_EDIT.value,
                VideoGenerationMode.VIDEO_EXTEND.value,
            }
            or isinstance(output, dict)
            and "timing_mode" in output
            or isinstance(image_bindings, list)
            and any(binding.get("role") == "last_frame" for binding in image_bindings)
        )
        selected = {
            key: value
            for key, value in data.items()
            if key not in {"generation_id", "request_input_hash"}
        }
        if not advanced:
            selected.pop("media_bindings", None)
        if continuity is None:
            selected.pop("continuity_binding", None)
        if not seal_terminal_frame:
            selected.pop("seal_terminal_frame", None)
        return {
            "schema": (
                "ai-video-generation-request/3"
                if continuity is not None or seal_terminal_frame
                else "ai-video-generation-request/2"
                if advanced
                else "ai-video-generation-request/1"
            ),
            **selected,
        }

    @model_validator(mode="after")
    def _validate_request(self) -> "VideoGenerationRequest":
        if self.mode is VideoGenerationMode.TEXT_TO_VIDEO and self.image_bindings:
            raise ValueError("text-to-video requests cannot contain image bindings")
        if self.mode is VideoGenerationMode.TEXT_TO_VIDEO and self.media_bindings:
            raise ValueError("text-to-video requests cannot contain media bindings")
        if self.mode is VideoGenerationMode.IMAGE_TO_VIDEO and (
            not self.image_bindings or self.media_bindings
        ):
            raise ValueError("image-to-video requests require image bindings")
        if self.mode is VideoGenerationMode.REFERENCE_TO_VIDEO and not (
            self.image_bindings or self.media_bindings
        ):
            raise ValueError("reference-to-video requests require reference bindings")
        if self.mode in {
            VideoGenerationMode.VIDEO_EDIT,
            VideoGenerationMode.VIDEO_EXTEND,
        } and not any(binding.kind == "video" for binding in self.media_bindings):
            raise ValueError("video edit and extend requests require a video reference")
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
        media_keys = tuple(
            (_MEDIA_ROLE_ORDER[binding.role], binding.asset_id)
            for binding in self.media_bindings
        )
        if media_keys != tuple(sorted(media_keys)):
            raise ValueError("video media bindings must use canonical role and asset order")
        if len({(binding.role, binding.asset_id) for binding in self.media_bindings}) != len(
            self.media_bindings
        ):
            raise ValueError("video media bindings must be unique")
        if len(set(self.input_artifact_ids)) != len(self.input_artifact_ids):
            raise ValueError("video input artifact IDs must be unique")
        continuity = self.continuity_binding
        if continuity is not None:
            terminal = continuity.terminal_frame
            if self.mode is not VideoGenerationMode.IMAGE_TO_VIDEO:
                raise ValueError("continuity requests must use image-to-video mode")
            if (
                continuity.target_shot_id != self.target_shot_id
                or continuity.target_shot_revision != self.target_shot_revision
                or continuity.target_shot_content_hash
                != self.target_shot_content_hash
            ):
                raise ValueError("continuity binding does not match target Shot")
            expected_frame = VideoImageReferenceBinding(
                role="first_frame",
                asset_id=terminal.extracted_asset_id,
                asset_sha256=terminal.extracted_sha256,
                mime_type=terminal.extracted_mime_type,
                width=terminal.extracted_width,
                height=terminal.extracted_height,
                size_bytes=terminal.extracted_size_bytes,
            )
            optional_last = self.image_bindings[1:]
            if (
                not self.image_bindings
                or self.image_bindings[0] != expected_frame
                or len(optional_last) > 1
                or any(item.role != "last_frame" for item in optional_last)
            ):
                raise ValueError("continuity request does not bind the exact terminal frame")
            required_inputs = {
                terminal.source_shot_id,
                terminal.source_video_asset_id,
                terminal.extracted_asset_id,
            }
            if not required_inputs.issubset(self.input_artifact_ids):
                raise ValueError("continuity input artifact identity is incomplete")
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
    output: VideoOutputRequirement | None = None
    output_capability: VideoOutputCapability | None = None
    allowed_image_roles: tuple[Literal["first_frame", "last_frame", "reference"], ...]
    required_first_frame: bool
    max_reference_count: int = Field(strict=True, ge=0, le=32)
    allowed_image_mime_types: tuple[str, ...]
    max_image_bytes: int = Field(strict=True, gt=0)
    min_image_width: int = Field(strict=True, gt=0)
    min_image_height: int = Field(strict=True, gt=0)
    media_capabilities: tuple[VideoMediaCapability, ...] = ()
    negative_prompt_supported: bool
    seed_supported: bool
    fps_supported: bool
    idempotent_submit: bool
    lookup_supported: bool

    @model_validator(mode="after")
    def _validate_variant(self) -> "VideoCapabilityVariant":
        if (self.output is None) == (self.output_capability is None):
            raise ValueError("video capability requires exactly one output contract")
        if len(set(self.allowed_image_roles)) != len(self.allowed_image_roles):
            raise ValueError("video capability image roles must be unique")
        if len(set(self.allowed_image_mime_types)) != len(self.allowed_image_mime_types):
            raise ValueError("video capability image MIME types must be unique")
        if self.mode is VideoGenerationMode.TEXT_TO_VIDEO and (
            self.allowed_image_roles
            or self.required_first_frame
            or self.max_reference_count
            or self.media_capabilities
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


class VideoActivationScope(_VideoStrictModel):
    """Separately sealed authoring scope kept outside the legacy resolved hash."""

    request: VideoGenerationRequest
    usage_license: str = Field(min_length=1)
    scope_fingerprint: str = Field(pattern=_SHA256)

    @staticmethod
    def _fingerprint_payload(
        request: VideoGenerationRequest, usage_license: str
    ) -> dict[str, object]:
        request_payload = request.model_dump(mode="json")
        uses_continuity = (
            request.continuity_binding is not None or request.seal_terminal_frame
        )
        if not uses_continuity:
            request_payload.pop("continuity_binding", None)
            request_payload.pop("seal_terminal_frame", None)
        return {
            "schema": (
                "ai-video-activation-scope/2"
                if uses_continuity
                else "ai-video-activation-scope/1"
            ),
            "request": request_payload,
            "usage_license": usage_license,
        }

    @model_validator(mode="after")
    def _validate_scope(self) -> "VideoActivationScope":
        if self.scope_fingerprint != canonical_sha256(
            self._fingerprint_payload(self.request, self.usage_license)
        ):
            raise ValueError("activation scope fingerprint does not match request")
        return self

    @classmethod
    def create(
        cls,
        request: VideoGenerationRequest,
        *,
        usage_license: str = "provider-output",
    ) -> "VideoActivationScope":
        data = {"request": request, "usage_license": usage_license}
        candidate = cls.model_construct(**data, scope_fingerprint="0" * 64)
        return cls.model_validate(
            {
                **data,
                "scope_fingerprint": canonical_sha256(
                    cls._fingerprint_payload(
                        candidate.request, candidate.usage_license
                    )
                ),
            }
        )


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
    prompt_text: str = Field(min_length=1)
    image_bindings: tuple[VideoImageReferenceBinding, ...]
    continuity_binding: ContinuityReferenceBinding | None = None
    seal_terminal_frame: bool = Field(default=False, strict=True)
    media_bindings: tuple[VideoMediaReferenceBinding, ...] = ()
    effective_output: VideoOutputRequirement | VideoFlexibleOutputRequirement
    provider_task_binding: VideoProviderTaskBinding | None = None
    effective_seed: int | None = Field(default=None, strict=True, ge=-1)
    effective_negative_prompt_text: str
    output_asset_id: str = Field(pattern=_SAFE_ID.pattern)
    activation_scope: VideoActivationScope | None = None
    resolved_generation_hash: str = Field(pattern=_SHA256)
    desired_generation_fingerprint: str = Field(pattern=_SHA256)

    @field_validator("prompt_text")
    @classmethod
    def _require_nfc(cls, value: str) -> str:
        if unicodedata.normalize("NFC", value) != value:
            raise ValueError("resolved video prompt text must use Unicode NFC normalization")
        return value

    @model_validator(mode="after")
    def _validate_seal(self) -> "ResolvedVideoGenerationRequest":
        data = self.model_dump(
            mode="json",
            exclude={
                "activation_scope",
                "resolved_generation_hash",
                "desired_generation_fingerprint",
            },
        )
        schema = (
            "ai-video-resolved-request/4"
            if self.continuity_binding is not None or self.seal_terminal_frame
            else "ai-video-resolved-request/3"
            if self._uses_extended_contract()
            else "ai-video-resolved-request/2"
        )
        if schema.endswith("/2"):
            data.pop("media_bindings", None)
        if self.continuity_binding is None:
            data.pop("continuity_binding", None)
        if not self.seal_terminal_frame:
            data.pop("seal_terminal_frame", None)
        if self.provider_task_binding is None:
            data.pop("provider_task_binding", None)
        expected = canonical_sha256({"schema": schema, **data})
        if self.resolved_generation_hash != expected:
            raise ValueError("resolved_generation_hash does not match resolved request")
        if self.desired_generation_fingerprint != expected:
            raise ValueError("desired generation fingerprint must equal resolved hash")
        scope = self.activation_scope
        if scope is not None:
            request = scope.request
            if (
                request.generation_id != self.generation_id
                or request.request_input_hash != self.request_input_hash
                or request.provider_name != self.provider_name
                or request.provider_kind != self.provider_kind
                or request.model_id != self.model_id
                or request.provider_profile != self.provider_profile
                or request.mode is not self.mode
                or request.prompt_text != self.prompt_text
                or request.image_bindings != self.image_bindings
                or request.continuity_binding != self.continuity_binding
                or request.seal_terminal_frame != self.seal_terminal_frame
                or request.media_bindings != self.media_bindings
                or request.output_requirement != self.effective_output
                or request.output_asset_id != self.output_asset_id
            ):
                raise ValueError("activation scope does not match resolved request")
        return self

    def _uses_extended_contract(self) -> bool:
        return bool(
            self.media_bindings
            or self.mode
            in {
                VideoGenerationMode.REFERENCE_TO_VIDEO,
                VideoGenerationMode.VIDEO_EDIT,
                VideoGenerationMode.VIDEO_EXTEND,
            }
            or isinstance(self.effective_output, VideoFlexibleOutputRequirement)
            or self.provider_task_binding is not None
            or any(binding.role == "last_frame" for binding in self.image_bindings)
        )

    @classmethod
    def create(
        cls,
        *,
        request: VideoGenerationRequest,
        capability: VideoCapabilityVariant,
        effective_output: VideoOutputRequirement | VideoFlexibleOutputRequirement,
        effective_seed: int | None,
        effective_negative_prompt_text: str,
        provider_task_binding: VideoProviderTaskBinding | None = None,
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
        output_supported = (
            capability.output is not None
            and effective_output == capability.output
            or capability.output_capability is not None
            and isinstance(effective_output, VideoFlexibleOutputRequirement)
            and capability.output_capability.supports(effective_output)
        )
        if effective_output != request.output_requirement or not output_supported:
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
        last_frames = sum(binding.role == "last_frame" for binding in request.image_bindings)
        references = sum(binding.role == "reference" for binding in request.image_bindings)
        if (
            (capability.required_first_frame and first_frames != 1)
            or first_frames > 1
            or last_frames > 1
            or references > capability.max_reference_count
            or any(
                binding.role not in capability.allowed_image_roles
                for binding in request.image_bindings
            )
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
        if not media_bindings_satisfy_capabilities(
            request.media_bindings, capability.media_capabilities
        ):
            raise _video_error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Video media bindings do not satisfy the selected capability variant.",
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
            "prompt_text": request.prompt_text,
            "image_bindings": request.image_bindings,
            "continuity_binding": request.continuity_binding,
            "seal_terminal_frame": request.seal_terminal_frame,
            "media_bindings": request.media_bindings,
            "effective_output": effective_output,
            "provider_task_binding": provider_task_binding,
            "effective_seed": effective_seed,
            "effective_negative_prompt_text": effective_negative_prompt_text,
            "output_asset_id": request.output_asset_id,
            "activation_scope": VideoActivationScope.create(request),
        }
        candidate = cls.model_construct(
            **data,
            resolved_generation_hash="0" * 64,
            desired_generation_fingerprint="0" * 64,
        )
        fingerprint_data = candidate.model_dump(
            mode="json",
            exclude={
                "activation_scope",
                "resolved_generation_hash",
                "desired_generation_fingerprint",
            },
            warnings=False,
        )
        schema = (
            "ai-video-resolved-request/4"
            if candidate.continuity_binding is not None or candidate.seal_terminal_frame
            else "ai-video-resolved-request/3"
            if candidate._uses_extended_contract()
            else "ai-video-resolved-request/2"
        )
        if schema.endswith("/2"):
            fingerprint_data.pop("media_bindings", None)
        if candidate.continuity_binding is None:
            fingerprint_data.pop("continuity_binding", None)
        if not candidate.seal_terminal_frame:
            fingerprint_data.pop("seal_terminal_frame", None)
        if provider_task_binding is None:
            fingerprint_data.pop("provider_task_binding", None)
        fingerprint = canonical_sha256({"schema": schema, **fingerprint_data})
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
    provider_task_binding: VideoProviderTaskBinding | None = None
    expected_container: Literal["mp4", "mov"] | None = None
    expected_content_type: Literal["video/mp4", "video/quicktime"] | None = None
    submission_fingerprint: str = Field(pattern=_SHA256)

    @field_validator("submitted_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return _require_aware(value, "video submission timestamp")

    @model_validator(mode="after")
    def _validate_seal(self) -> "VideoSubmission":
        expected_type = {
            "mp4": "video/mp4",
            "mov": "video/quicktime",
            None: None,
        }[self.expected_container]
        if self.expected_content_type != expected_type:
            raise ValueError("video submission container and content type must match")
        fingerprint_data = self.model_dump(
            mode="json", exclude={"submission_fingerprint"}
        )
        if self.expected_container is None:
            fingerprint_data.pop("expected_container", None)
            fingerprint_data.pop("expected_content_type", None)
        if self.provider_task_binding is None:
            fingerprint_data.pop("provider_task_binding", None)
        if self.submission_fingerprint != canonical_sha256(
            fingerprint_data
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
            "provider_task_binding": resolved.provider_task_binding,
            "expected_container": (
                resolved.effective_output.container
                if isinstance(
                    resolved.effective_output, VideoFlexibleOutputRequirement
                )
                else None
            ),
            "expected_content_type": (
                resolved.effective_output.mime_type
                if isinstance(
                    resolved.effective_output, VideoFlexibleOutputRequirement
                )
                else None
            ),
        }
        candidate = cls.model_construct(**data, submission_fingerprint="0" * 64)
        fingerprint_data = candidate.model_dump(
            mode="json", exclude={"submission_fingerprint"}, warnings=False
        )
        if data["expected_container"] is None:
            fingerprint_data.pop("expected_container", None)
            fingerprint_data.pop("expected_content_type", None)
        if data["provider_task_binding"] is None:
            fingerprint_data.pop("provider_task_binding", None)
        data["submission_fingerprint"] = canonical_sha256(
            fingerprint_data
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
    content_type: Literal["video/mp4", "video/quicktime"]
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
        content_type: Literal["video/mp4", "video/quicktime"],
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
        if (
            submission.expected_content_type is not None
            and content_type != submission.expected_content_type
        ):
            raise _video_error(
                ErrorCode.VIDEO_ARTIFACT_INVALID,
                "Video fetch content type does not match the durable submit intent.",
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
    "ContinuityArtifactIdentity",
    "ContinuityConstraintSet",
    "ContinuityReferenceBinding",
    "ProviderProfilePointer",
    "ResolvedVideoGenerationRequest",
    "TerminalFrameEvidence",
    "VideoActivationScope",
    "VideoCapabilityVariant",
    "VideoExecutionKind",
    "VideoFetchReceipt",
    "VideoGenerationMode",
    "VideoGenerationPreview",
    "VideoGenerationRequest",
    "VideoFlexibleOutputRequirement",
    "VideoImageReferenceBinding",
    "VideoMediaCapability",
    "VideoMediaReferenceBinding",
    "VideoOutputCapability",
    "VideoOutputRequirement",
    "VideoProviderTaskBinding",
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
