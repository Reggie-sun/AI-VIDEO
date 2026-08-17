from __future__ import annotations

import hashlib
import re
import struct
import unicodedata
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol

from pydantic import ConfigDict, Field, field_validator, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.dependency import (
    DependencyResolution,
    ProductionDependencyInputs,
    asset_node_id,
    build_production_dependency_graph,
    shot_projection_node_id,
)
from ai_video.production.hashing import (
    canonical_sha256,
    seal_artifact,
    verify_artifact_hash,
)
from ai_video.production.models import (
    ArtifactReference,
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    DependencyGraphSnapshot,
    DependencyGraphSnapshotPointer,
    EgressMetadata,
    LoadedProductionProject,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    StrictModel,
    ToolIdentity,
)
from ai_video.production.registry import registry_semantic_sha256


if TYPE_CHECKING:
    from ai_video.production.state_commit import DurableImageSubmitPermit


__all__ = [
    "ImageAssetProvider",
    "ImageActivationCandidate",
    "ImageGenerationAuthorization",
    "ImageGenerationPreview",
    "ImageGenerationRequest",
    "ImageLocalResourceEvidence",
    "ImageProvenanceReceipt",
    "ImageProviderParameters",
    "ImageProviderResult",
    "ImageReferenceBinding",
    "MeasuredPng",
    "image_receipt_semantic_sha256",
    "validate_image_activation_candidate",
    "validate_image_result",
]


_PROVIDER_IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_REFERENCE_ROLE_ORDER = {"character": 0, "scene": 1, "style": 2}
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PNG_BIT_DEPTHS = {
    0: {1, 2, 4, 8, 16},
    2: {8, 16},
    3: {1, 2, 4, 8},
    4: {8, 16},
    6: {8, 16},
}
_IMAGE_ACTIVATION_TOKEN = object()


def _image_bytes_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.ASSET_REGISTRY_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _image_scope_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_STATE_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class _ImageStrictModel(StrictModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )


class ImageProviderParameters(_ImageStrictModel):
    seed: int = Field(strict=True)
    width: int = Field(strict=True, gt=0)
    height: int = Field(strict=True, gt=0)
    output_format: Literal["png"]
    generation_revision: int = Field(strict=True, ge=1)


class ImageReferenceBinding(_ImageStrictModel):
    role: Literal["character", "scene", "style"]
    creative_artifact_id: str = Field(min_length=1)
    creative_revision: int = Field(strict=True, ge=1)
    creative_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_id: str = Field(min_length=1)
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ImageGenerationRequest(_ImageStrictModel):
    request_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    attempt_id: str = Field(min_length=1)
    provider_kind: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    target_shot_id: str = Field(min_length=1)
    target_asset_role: str = Field(min_length=1)
    output_asset_id: str = Field(pattern=r"^image-[0-9a-f]{64}$")
    prompt_text: str = Field(min_length=1)
    negative_prompt_text: str
    parameters: ImageProviderParameters
    references: tuple[ImageReferenceBinding, ...]
    base_project: ProjectSnapshotPointer
    base_registry: RegistrySnapshotPointer
    base_dependency_graph: DependencyGraphSnapshotPointer
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @staticmethod
    def _fingerprint_payload(data: dict[str, object]) -> dict[str, object]:
        prompt_text = data["prompt_text"]
        negative_prompt_text = data["negative_prompt_text"]
        if not isinstance(prompt_text, str) or not isinstance(negative_prompt_text, str):
            raise ValueError("image prompts must be text")
        return {
            "schema": "ai-video-image-request/1",
            "provider_kind": data["provider_kind"],
            "model_id": data["model_id"],
            "target_shot_id": data["target_shot_id"],
            "target_asset_role": data["target_asset_role"],
            "prompt_sha256": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
            "negative_prompt_sha256": hashlib.sha256(
                negative_prompt_text.encode("utf-8")
            ).hexdigest(),
            "parameters": data["parameters"],
            "references": data["references"],
            "base_project": data["base_project"],
            "base_registry": data["base_registry"],
            "base_dependency_graph": data["base_dependency_graph"],
        }

    @field_validator("prompt_text", "negative_prompt_text")
    @classmethod
    def _require_nfc_prompt(cls, value: str) -> str:
        if unicodedata.normalize("NFC", value) != value:
            raise ValueError("image prompt text must use Unicode NFC normalization")
        return value

    @model_validator(mode="after")
    def _validate_sealed_request(self) -> "ImageGenerationRequest":
        keys = tuple(
            (_REFERENCE_ROLE_ORDER[item.role], item.creative_artifact_id, item.asset_id)
            for item in self.references
        )
        if keys != tuple(sorted(keys)):
            raise ValueError("image references must use canonical order")
        unique = {(item.role, item.asset_id) for item in self.references}
        if len(unique) != len(self.references):
            raise ValueError("image references must be unique by role and asset_id")
        roles = {item.role for item in self.references}
        if not {"character", "scene"}.issubset(roles):
            raise ValueError("image request requires character and scene references")
        payload = self._fingerprint_payload(self.model_dump(mode="json"))
        expected = canonical_sha256(payload)
        if self.request_fingerprint != expected:
            raise ValueError("request_fingerprint does not match image request")
        if self.request_id != expected:
            raise ValueError("request_id must equal request_fingerprint")
        if self.output_asset_id != f"image-{expected}":
            raise ValueError("output_asset_id must derive from request_fingerprint")
        return self

    @classmethod
    def create(cls, **values: object) -> "ImageGenerationRequest":
        data = dict(values)
        serializable = {
            key: value.model_dump(mode="json")
            if isinstance(value, StrictModel)
            else tuple(
                item.model_dump(mode="json")
                if isinstance(item, StrictModel)
                else item
                for item in value
            )
            if key == "references" and isinstance(value, tuple)
            else value
            for key, value in data.items()
        }
        fingerprint = canonical_sha256(cls._fingerprint_payload(serializable))
        data["request_id"] = fingerprint
        data["request_fingerprint"] = fingerprint
        data["output_asset_id"] = f"image-{fingerprint}"
        return cls.model_validate(data)


class ImageGenerationPreview(_ImageStrictModel):
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    local_only: Literal[True]
    remote: Literal[False]
    output_count: Literal[1]
    output_mime_type: Literal["image/png"]
    reference_asset_ids: tuple[str, ...] = Field(min_length=2)
    reference_total_bytes: int = Field(strict=True, ge=0)
    preview_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_sealed_preview(self) -> "ImageGenerationPreview":
        data = self.model_dump(mode="json", exclude={"preview_fingerprint"})
        if canonical_sha256(data) != self.preview_fingerprint:
            raise ValueError("preview_fingerprint does not match image preview")
        return self

    @classmethod
    def create(
        cls,
        *,
        request: ImageGenerationRequest,
        reference_total_bytes: int,
    ) -> "ImageGenerationPreview":
        data: dict[str, object] = {
            "request_fingerprint": request.request_fingerprint,
            "local_only": True,
            "remote": False,
            "output_count": 1,
            "output_mime_type": "image/png",
            "reference_asset_ids": tuple(item.asset_id for item in request.references),
            "reference_total_bytes": reference_total_bytes,
        }
        data["preview_fingerprint"] = canonical_sha256(data)
        return cls.model_validate(data)


class ImageGenerationAuthorization(_ImageStrictModel):
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    preview_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_enabled: Literal[True]
    local_only: Literal[True]
    usage_license: str = Field(min_length=1)
    policy_receipt_id: str = Field(min_length=1)
    authorization_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_sealed_authorization(self) -> "ImageGenerationAuthorization":
        data = self.model_dump(mode="json", exclude={"authorization_fingerprint"})
        if canonical_sha256(data) != self.authorization_fingerprint:
            raise ValueError(
                "authorization_fingerprint does not match image authorization"
            )
        return self

    @classmethod
    def create(
        cls,
        *,
        request: ImageGenerationRequest,
        preview: ImageGenerationPreview,
        usage_license: str,
        policy_receipt_id: str,
    ) -> "ImageGenerationAuthorization":
        if preview.request_fingerprint != request.request_fingerprint:
            raise ValueError("image preview does not match request")
        data: dict[str, object] = {
            "request_fingerprint": request.request_fingerprint,
            "preview_fingerprint": preview.preview_fingerprint,
            "provider_enabled": True,
            "local_only": True,
            "usage_license": usage_license,
            "policy_receipt_id": policy_receipt_id,
        }
        data["authorization_fingerprint"] = canonical_sha256(data)
        return cls.model_validate(data)


class ImageLocalResourceEvidence(_ImageStrictModel):
    elapsed_milliseconds: int = Field(strict=True, ge=0)
    device_kind: Literal["cpu", "gpu", "unknown"]
    measured_peak_memory_bytes: int | None = Field(default=None, strict=True, ge=0)


class ImageProviderResult(_ImageStrictModel):
    request_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    image_bytes: bytes = Field(min_length=1)
    image_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_type: Literal["image/png"]
    provider_request_id: str | None = None
    adapter: ToolIdentity
    resource_evidence: ImageLocalResourceEvidence
    preview_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    authorization_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    terminal_status: Literal["succeeded"]
    result_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("provider_request_id")
    @classmethod
    def _sanitize_provider_identifier(cls, value: str | None) -> str | None:
        if value is not None and _PROVIDER_IDENTIFIER.fullmatch(value) is None:
            raise ValueError("provider_request_id must be sanitized")
        return value

    @staticmethod
    def _fingerprint_payload(data: dict[str, object]) -> dict[str, object]:
        return {
            "schema": "ai-video-image-result/1",
            "request_id": data["request_id"],
            "request_fingerprint": data["request_fingerprint"],
            "image_sha256": data["image_sha256"],
            "content_type": data["content_type"],
            "provider_request_id": data["provider_request_id"],
            "adapter": data["adapter"],
            "resource_evidence": data["resource_evidence"],
            "preview_fingerprint": data["preview_fingerprint"],
            "authorization_fingerprint": data["authorization_fingerprint"],
            "terminal_status": data["terminal_status"],
        }

    @model_validator(mode="after")
    def _validate_sealed_result(self) -> "ImageProviderResult":
        expected_image = hashlib.sha256(self.image_bytes).hexdigest()
        if self.image_sha256 != expected_image:
            raise ValueError("image_sha256 does not match exact image_bytes")
        if self.request_id != self.request_fingerprint:
            raise ValueError("image result request identity is inconsistent")
        data = self.model_dump(mode="json", exclude={"image_bytes"})
        if canonical_sha256(self._fingerprint_payload(data)) != self.result_fingerprint:
            raise ValueError("result_fingerprint does not match image result")
        return self

    @classmethod
    def create(
        cls,
        *,
        request: ImageGenerationRequest,
        authorization: ImageGenerationAuthorization,
        image_bytes: bytes,
        content_type: Literal["image/png"],
        provider_request_id: str | None,
        adapter: ToolIdentity,
        resource_evidence: ImageLocalResourceEvidence,
    ) -> "ImageProviderResult":
        if authorization.request_fingerprint != request.request_fingerprint:
            raise ValueError("image authorization does not match request")
        data: dict[str, object] = {
            "request_id": request.request_id,
            "request_fingerprint": request.request_fingerprint,
            "image_bytes": image_bytes,
            "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
            "content_type": content_type,
            "provider_request_id": provider_request_id,
            "adapter": adapter,
            "resource_evidence": resource_evidence,
            "preview_fingerprint": authorization.preview_fingerprint,
            "authorization_fingerprint": authorization.authorization_fingerprint,
            "terminal_status": "succeeded",
        }
        serializable = {
            key: value.model_dump(mode="json")
            if isinstance(value, StrictModel)
            else value
            for key, value in data.items()
            if key != "image_bytes"
        }
        data["result_fingerprint"] = canonical_sha256(
            cls._fingerprint_payload(serializable)
        )
        return cls.model_validate(data)


class MeasuredPng(_ImageStrictModel):
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(strict=True, gt=0)
    mime_type: Literal["image/png"]
    width: int = Field(strict=True, gt=0)
    height: int = Field(strict=True, gt=0)
    bit_depth: Literal[1, 2, 4, 8, 16]
    color_type: Literal[0, 2, 3, 4, 6]


class ImageProvenanceReceipt(_ImageStrictModel):
    request_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_shot_id: str = Field(min_length=1)
    target_asset_role: str = Field(min_length=1)
    output_asset_id: str = Field(pattern=r"^image-[0-9a-f]{64}$")
    adapter: ToolIdentity
    provider_request_id: str | None = None
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_size_bytes: int = Field(strict=True, gt=0)
    output_mime_type: Literal["image/png"]
    output_width: int = Field(strict=True, gt=0)
    output_height: int = Field(strict=True, gt=0)
    usage_license: str = Field(min_length=1)
    policy_receipt_id: str = Field(min_length=1)
    references: tuple[ImageReferenceBinding, ...]
    resource_evidence: ImageLocalResourceEvidence
    remote: Literal[False]
    cost_receipt_id: None = None
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("provider_request_id")
    @classmethod
    def _sanitize_provider_identifier(cls, value: str | None) -> str | None:
        if value is not None and _PROVIDER_IDENTIFIER.fullmatch(value) is None:
            raise ValueError("provider_request_id must be sanitized")
        return value

    @model_validator(mode="after")
    def _validate_content_hash(self) -> "ImageProvenanceReceipt":
        if image_receipt_semantic_sha256(self) != self.content_hash:
            raise ValueError("content_hash does not match image provenance receipt")
        return self

    @classmethod
    def create(cls, **values: object) -> "ImageProvenanceReceipt":
        data = dict(values)
        data["content_hash"] = image_receipt_semantic_sha256(data)
        return cls.model_validate(data)


def image_receipt_semantic_sha256(
    receipt: ImageProvenanceReceipt | dict[str, object],
) -> str:
    if isinstance(receipt, ImageProvenanceReceipt):
        payload = receipt.model_dump(mode="json", exclude={"content_hash"})
    else:
        payload = dict(receipt)
        payload.pop("content_hash", None)
        payload = {
            key: value.model_dump(mode="json")
            if isinstance(value, StrictModel)
            else tuple(
                item.model_dump(mode="json")
                if isinstance(item, StrictModel)
                else item
                for item in value
            )
            if isinstance(value, tuple)
            else value
            for key, value in payload.items()
        }
    return canonical_sha256(payload)


def _measure_png(payload: bytes) -> MeasuredPng:
    if not payload.startswith(_PNG_SIGNATURE):
        raise _image_bytes_invalid("Image provider output is not a PNG file.")

    cursor = len(_PNG_SIGNATURE)
    chunk_index = 0
    saw_idat = False
    saw_iend = False
    width = height = bit_depth = color_type = None
    while cursor < len(payload):
        if len(payload) - cursor < 12:
            raise _image_bytes_invalid("PNG output contains a truncated chunk.")
        length = struct.unpack(">I", payload[cursor : cursor + 4])[0]
        kind = payload[cursor + 4 : cursor + 8]
        chunk_end = cursor + 12 + length
        if chunk_end > len(payload):
            raise _image_bytes_invalid("PNG output contains a truncated chunk.")
        chunk_data = payload[cursor + 8 : cursor + 8 + length]
        expected_crc = struct.unpack(">I", payload[cursor + 8 + length : chunk_end])[0]
        measured_crc = zlib.crc32(kind + chunk_data) & 0xFFFFFFFF
        if expected_crc != measured_crc:
            raise _image_bytes_invalid("PNG output contains an invalid chunk checksum.")

        if chunk_index == 0:
            if kind != b"IHDR" or length != 13:
                raise _image_bytes_invalid("PNG output must start with a complete IHDR chunk.")
            (
                width,
                height,
                bit_depth,
                color_type,
                compression,
                filter_method,
                interlace,
            ) = struct.unpack(">IIBBBBB", chunk_data)
            if width <= 0 or height <= 0:
                raise _image_bytes_invalid("PNG output has invalid dimensions.")
            if bit_depth not in _PNG_BIT_DEPTHS.get(color_type, set()):
                raise _image_bytes_invalid("PNG output has an invalid color type or bit depth.")
            if compression != 0 or filter_method != 0 or interlace not in {0, 1}:
                raise _image_bytes_invalid("PNG output has unsupported IHDR methods.")
        elif kind == b"IHDR":
            raise _image_bytes_invalid("PNG output contains more than one IHDR chunk.")

        if kind == b"IDAT":
            saw_idat = True
        if kind == b"IEND":
            if length != 0 or not saw_idat or chunk_end != len(payload):
                raise _image_bytes_invalid("PNG output has an invalid IEND boundary.")
            saw_iend = True
        cursor = chunk_end
        chunk_index += 1

    if not saw_iend or width is None or height is None:
        raise _image_bytes_invalid("PNG output is incomplete.")
    return MeasuredPng(
        sha256=hashlib.sha256(payload).hexdigest(),
        size_bytes=len(payload),
        mime_type="image/png",
        width=width,
        height=height,
        bit_depth=bit_depth,
        color_type=color_type,
    )


def validate_image_result(
    request: ImageGenerationRequest,
    authorization: ImageGenerationAuthorization,
    result: ImageProviderResult,
) -> tuple[MeasuredPng, ImageProvenanceReceipt]:
    if authorization.request_fingerprint != request.request_fingerprint:
        raise _image_scope_invalid("Image authorization does not match the request.")
    if (
        result.request_id != request.request_id
        or result.request_fingerprint != request.request_fingerprint
        or result.preview_fingerprint != authorization.preview_fingerprint
        or result.authorization_fingerprint != authorization.authorization_fingerprint
    ):
        raise _image_scope_invalid("Image provider result does not match its request authorization.")

    measured = _measure_png(result.image_bytes)
    if (
        measured.width != request.parameters.width
        or measured.height != request.parameters.height
    ):
        raise _image_bytes_invalid(
            "Image provider output dimensions do not match the request.",
            f"expected={request.parameters.width}x{request.parameters.height}, "
            f"measured={measured.width}x{measured.height}",
        )
    receipt = ImageProvenanceReceipt.create(
        request_id=request.request_id,
        request_fingerprint=request.request_fingerprint,
        target_shot_id=request.target_shot_id,
        target_asset_role=request.target_asset_role,
        output_asset_id=request.output_asset_id,
        adapter=result.adapter,
        provider_request_id=result.provider_request_id,
        output_sha256=measured.sha256,
        output_size_bytes=measured.size_bytes,
        output_mime_type=measured.mime_type,
        output_width=measured.width,
        output_height=measured.height,
        usage_license=authorization.usage_license,
        policy_receipt_id=authorization.policy_receipt_id,
        references=request.references,
        resource_evidence=result.resource_evidence,
        remote=False,
        cost_receipt_id=None,
    )
    return measured, receipt


@dataclass(frozen=True, init=False)
class ImageActivationCandidate:
    image_asset_id: str
    changed_shot_ids: tuple[str, ...]
    base_project: LoadedProductionProject
    candidate_project: LoadedProductionProject
    candidate_registry: AssetRegistrySnapshot
    candidate_inputs: ProductionDependencyInputs
    candidate_graph: DependencyGraphSnapshot
    resolution: DependencyResolution
    receipt: ImageProvenanceReceipt

    def __new__(cls, token: object) -> "ImageActivationCandidate":
        if token is not _IMAGE_ACTIVATION_TOKEN:
            raise TypeError(
                "ImageActivationCandidate is returned by "
                "validate_image_activation_candidate()"
            )
        return super().__new__(cls)

    def __init__(self, token: object) -> None:
        del token

    @classmethod
    def _validated(
        cls,
        *,
        image_asset_id: str,
        changed_shot_ids: tuple[str, ...],
        base_project: LoadedProductionProject,
        candidate_project: LoadedProductionProject,
        candidate_registry: AssetRegistrySnapshot,
        candidate_inputs: ProductionDependencyInputs,
        candidate_graph: DependencyGraphSnapshot,
        resolution: DependencyResolution,
        receipt: ImageProvenanceReceipt,
    ) -> "ImageActivationCandidate":
        candidate = cls(_IMAGE_ACTIVATION_TOKEN)
        for field_name, value in locals().copy().items():
            if field_name not in {"cls", "candidate"}:
                object.__setattr__(candidate, field_name, value)
        return candidate


def _same_except(
    left: StrictModel,
    right: StrictModel,
    excluded: set[str],
) -> bool:
    return left.model_dump(mode="json", exclude=excluded) == right.model_dump(
        mode="json", exclude=excluded
    )


def validate_image_activation_candidate(
    *,
    base_project: LoadedProductionProject,
    request: ImageGenerationRequest,
    authorization: ImageGenerationAuthorization,
    result: ImageProviderResult,
    measured: MeasuredPng,
    receipt: ImageProvenanceReceipt,
    candidate_project: LoadedProductionProject,
    candidate_registry: AssetRegistrySnapshot,
    candidate_graph: DependencyGraphSnapshot,
    candidate_inputs: ProductionDependencyInputs,
    resolution: DependencyResolution,
) -> ImageActivationCandidate:
    checked_measured, checked_receipt = validate_image_result(
        request, authorization, result
    )
    if checked_measured != measured or checked_receipt != receipt:
        raise _image_scope_invalid(
            "Image activation candidate does not carry the exact validated result."
        )
    if (
        request.base_project != base_project.manifest.active_project
        or request.base_registry != base_project.manifest.active_registry
        or request.base_dependency_graph
        != base_project.manifest.active_dependency_graph
        or base_project.dependency_graph is None
        or request.base_dependency_graph.revision_id
        != base_project.dependency_graph.revision_id
    ):
        raise _image_scope_invalid(
            "Image request base pointers do not match the loaded project."
        )

    base_assets = base_project.registry.assets
    if (
        candidate_registry.assets[: len(base_assets)] != base_assets
        or len(candidate_registry.assets) != len(base_assets) + 1
        or registry_semantic_sha256(candidate_registry)
        != candidate_registry.content_hash
        or candidate_registry.revision_id != candidate_registry.content_hash
    ):
        raise _image_scope_invalid(
            "Image candidate Registry must append exactly one sealed asset."
        )
    expected_record = AssetRecord(
        asset_id=request.output_asset_id,
        asset_type=AssetType.IMAGE,
        artifact_path=Path(f"assets/files/{measured.sha256}.png"),
        sha256=measured.sha256,
        size_bytes=measured.size_bytes,
        mime_type=measured.mime_type,
        width=measured.width,
        height=measured.height,
        source_kind=AssetSourceKind.GENERATED,
        tool=result.adapter,
        input_artifact_ids=tuple(item.asset_id for item in request.references),
        input_fingerprint=request.request_fingerprint,
        creation_receipt_id=receipt.content_hash,
        usage_license=authorization.usage_license,
        egress=EgressMetadata(remote=False),
        cost_receipt_id=None,
    )
    if candidate_registry.assets[-1] != expected_record:
        raise _image_scope_invalid(
            "Image candidate Registry record does not match the validated output."
        )

    base_shots = {shot.shot_id: shot for shot in base_project.shots}
    next_shots = {shot.shot_id: shot for shot in candidate_project.shots}
    if set(base_shots) != set(next_shots) or request.target_shot_id not in base_shots:
        raise _image_scope_invalid("Image candidate changed the Shot identity set.")
    base_shot = base_shots[request.target_shot_id]
    target_roles = tuple(
        role
        for role in base_shot.required_asset_roles
        if role.role == request.target_asset_role
    )
    if len(target_roles) != 1:
        raise _image_scope_invalid(
            "Image request target role does not identify exactly one Shot role."
        )
    expected_roles = tuple(
        role.model_copy(update={"asset_ids": (request.output_asset_id,)})
        if role.role == request.target_asset_role
        else role
        for role in base_shot.required_asset_roles
    )
    expected_shot = seal_artifact(
        base_shot.model_copy(
            update={
                "revision": base_shot.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": receipt.content_hash,
                "required_asset_roles": expected_roles,
            }
        )
    )
    if next_shots[request.target_shot_id] != expected_shot:
        raise _image_scope_invalid(
            "Image candidate must change only the target Shot asset role."
        )
    if any(
        next_shots[shot_id] != shot
        for shot_id, shot in base_shots.items()
        if shot_id != request.target_shot_id
    ):
        raise _image_scope_invalid("Image candidate changed an unrelated Shot.")

    base_ref = tuple(
        item
        for item in base_project.project.artifacts.shots
        if item.artifact_id == expected_shot.artifact_id
    )
    if len(base_ref) != 1:
        raise _image_scope_invalid("Target Shot project reference is ambiguous.")
    expected_ref = ArtifactReference(
        artifact_id=expected_shot.artifact_id,
        revision=expected_shot.revision,
        content_hash=expected_shot.content_hash,
        path=base_ref[0].path,
    )
    expected_project_artifact = seal_artifact(
        base_project.project.model_copy(
            update={
                "revision": base_project.project.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": receipt.content_hash,
                "artifacts": base_project.project.artifacts.model_copy(
                    update={
                        "shots": tuple(
                            expected_ref
                            if item.artifact_id == expected_shot.artifact_id
                            else item
                            for item in base_project.project.artifacts.shots
                        )
                    }
                ),
            }
        )
    )
    if (
        candidate_project.project != expected_project_artifact
        or not verify_artifact_hash(candidate_project.project)
        or candidate_project.registry != candidate_registry
        or candidate_project.root != base_project.root
        or candidate_project.brief != base_project.brief
        or candidate_project.story != base_project.story
        or candidate_project.characters != base_project.characters
        or candidate_project.scenes != base_project.scenes
        or candidate_project.storyboard != base_project.storyboard
        or candidate_project.render_state != base_project.render_state
    ):
        raise _image_scope_invalid(
            "Image candidate changed project content outside the target Shot."
        )
    expected_asset_paths = {
        **base_project.asset_paths,
        request.output_asset_id: base_project.root / expected_record.artifact_path,
    }
    if dict(candidate_project.asset_paths) != expected_asset_paths:
        raise _image_scope_invalid("Image candidate asset path map is not exact.")

    active_project = candidate_project.manifest.active_project
    active_registry = candidate_project.manifest.active_registry
    active_graph = candidate_project.manifest.active_dependency_graph
    if (
        active_project.revision != candidate_project.project.revision
        or active_project.content_hash != candidate_project.project.content_hash
        or active_registry.revision_id != candidate_registry.revision_id
        or active_registry.content_hash != candidate_registry.content_hash
        or active_graph is None
    ):
        raise _image_scope_invalid("Image candidate active pointers are inconsistent.")
    if not _same_except(
        base_project.manifest,
        candidate_project.manifest,
        {"active_project", "active_registry", "active_dependency_graph"},
    ):
        raise _image_scope_invalid("Image candidate changed unrelated Manifest state.")

    if candidate_inputs.project != candidate_project:
        raise _image_scope_invalid("Image candidate dependency inputs use another project.")
    expected_graph = build_production_dependency_graph(candidate_inputs)
    if (
        candidate_graph != expected_graph
        or candidate_project.dependency_graph != expected_graph
        or resolution.graph != expected_graph
        or active_graph.revision_id != expected_graph.revision_id
        or active_graph.content_hash != expected_graph.content_hash
    ):
        raise _image_scope_invalid(
            "Image candidate graph does not equal the existing P5 builder output."
        )
    target_visual_id = shot_projection_node_id(request.target_shot_id, "visual")
    output_node_id = asset_node_id(request.output_asset_id)
    target_asset_node_ids = {
        asset_node_id(asset_id)
        for asset_id in target_roles[0].asset_ids
    } | {output_node_id}
    affected = set(resolution.affected_node_ids)
    if not {target_visual_id, output_node_id}.issubset(affected):
        raise _image_scope_invalid(
            "Image candidate resolution omits the target visual generation frontier."
        )
    for node_id in affected:
        if node_id.startswith("creative:shot:") and node_id != target_visual_id:
            raise _image_scope_invalid(
                "Image candidate resolution affects an unrelated Shot projection."
            )
        if node_id.startswith("asset:") and node_id not in target_asset_node_ids:
            raise _image_scope_invalid(
                "Image candidate resolution affects an unrelated asset."
            )
        if ":voice" in node_id or ":caption" in node_id:
            raise _image_scope_invalid(
                "Image candidate resolution affects voice or caption state."
            )

    return ImageActivationCandidate._validated(
        image_asset_id=request.output_asset_id,
        changed_shot_ids=(request.target_shot_id,),
        base_project=base_project,
        candidate_project=candidate_project,
        candidate_registry=candidate_registry,
        candidate_inputs=candidate_inputs,
        candidate_graph=candidate_graph,
        resolution=resolution,
        receipt=receipt,
    )


class ImageAssetProvider(Protocol):
    def generate(
        self,
        request: ImageGenerationRequest,
        authorization: ImageGenerationAuthorization,
        permit: "DurableImageSubmitPermit",
    ) -> ImageProviderResult: ...
