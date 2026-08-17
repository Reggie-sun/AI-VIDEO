from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import TYPE_CHECKING, Literal, Protocol

from pydantic import ConfigDict, Field, field_validator, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    StrictModel,
    ToolIdentity,
)


if TYPE_CHECKING:
    from ai_video.production.state_commit import DurableImageSubmitPermit


__all__ = [
    "ImageAssetProvider",
    "ImageGenerationAuthorization",
    "ImageGenerationPreview",
    "ImageGenerationRequest",
    "ImageLocalResourceEvidence",
    "ImageProviderParameters",
    "ImageProviderResult",
    "ImageReferenceBinding",
]


_PROVIDER_IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_REFERENCE_ROLE_ORDER = {"character": 0, "scene": 1, "style": 2}


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


class ImageAssetProvider(Protocol):
    def generate(
        self,
        request: ImageGenerationRequest,
        authorization: ImageGenerationAuthorization,
        permit: "DurableImageSubmitPermit",
    ) -> ImageProviderResult: ...
