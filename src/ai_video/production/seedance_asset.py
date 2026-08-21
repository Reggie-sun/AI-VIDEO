"""Sealed imports for Ark materialized assets consumed by Seedance."""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Callable, Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.image import measure_png_bytes
from ai_video.production.models import (
    ActorIdentity,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    StrictModel,
    ToolIdentity,
)
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
)
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoMediaReferenceBinding,
)
from ai_video.production.registry import registry_semantic_sha256


SEEDANCE_MAX_SYNTHETIC_IMAGE_BYTES = 30_000_000
_SYNTHETIC_EGRESS_ID_PREFIX = "seedance-synthetic-egress:"
_SYNTHETIC_IMAGE_ID_PREFIX = "seedance-synthetic-image:"
_IMAGE_ROLE_ORDER = {"first_frame": 0, "last_frame": 1, "reference": 2}
_PROJECT_OWNED_FICTIONAL_IDENTITY_USE = (
    "project-owned-fictional-no-protected-identity:seedance-i2v"
)
_FICTIONAL_IDENTITY_SOURCE_KINDS = {
    AssetSourceKind.GENERATED,
    AssetSourceKind.DERIVED,
}
_FICTIONAL_IDENTITY_USAGE_LICENSES = {
    "project-owned-synthetic",
    "provider-output",
}

SeedanceSyntheticEvidenceSource = Callable[[str], bytes]
SeedancePaidProviderAuthorizer = Callable[
    [PaidProviderCallPreview], PaidProviderAuthorizationDecision | None
]


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(ErrorCode.VIDEO_REQUEST_INVALID, message, retryable=False)


def _egress_denied(message: str) -> AiVideoError:
    return AiVideoError(
        ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED,
        message,
        retryable=False,
    )


def _canonical_model_bytes(model: StrictModel) -> bytes:
    return json.dumps(
        model.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _canonical_registry_bytes(registry: AssetRegistrySnapshot) -> bytes:
    return _canonical_model_bytes(registry) + b"\n"


def _read_evidence(
    source: SeedanceSyntheticEvidenceSource,
    evidence_id: str,
) -> bytes:
    try:
        payload = source(evidence_id)
    except Exception:
        raise _invalid("Seedance synthetic evidence is unavailable.") from None
    if type(payload) is not bytes:
        raise _invalid("Seedance synthetic evidence bytes are invalid.")
    return payload


class SeedanceAssetMaterializationReceipt(StrictModel):
    """Human-observed binding from one exact local asset to an active Ark asset."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal["1"] = "1"
    provider_name: Literal["seedance"] = "seedance"
    provider_kind: Literal["volcengine_ark_seedance"] = "volcengine_ark_seedance"
    source_surface: Literal["ark_console"] = "ark_console"
    source_asset_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
    source_asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_mime_type: str = Field(pattern=r"^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$")
    source_size_bytes: int = Field(strict=True, gt=0)
    provider_asset_id: str = Field(pattern=r"^asset-[A-Za-z0-9._:-]{1,250}$")
    provider_asset_group_id: str = Field(pattern=r"^group-[A-Za-z0-9._:-]{1,250}$")
    materialization_scope: Literal["aigc", "trusted_real_person"]
    observed_status: Literal["Active"]
    observed_at: datetime
    observed_by: ActorIdentity
    provider_confirmation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    rights_source_note: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_truthful_observation(self) -> "SeedanceAssetMaterializationReceipt":
        if self.observed_at.tzinfo is None:
            raise ValueError("Ark asset observation requires a timezone-aware timestamp")
        if self.observed_by.actor_kind != "human":
            raise ValueError("Ark console asset observation requires a human actor")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        )
        if self.content_hash != expected:
            raise ValueError("Ark asset materialization receipt seal does not match")
        return self

    @classmethod
    def create(cls, **values: object) -> "SeedanceAssetMaterializationReceipt":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.setdefault("provider_name", "seedance")
        data.setdefault("provider_kind", "volcengine_ark_seedance")
        data.setdefault("source_surface", "ark_console")
        data.pop("content_hash", None)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            provisional.model_dump(
                mode="json", exclude={"content_hash"}, warnings=False
            )
        )
        return cls.model_validate(data)


class SeedanceAssetReferenceResolver:
    """Resolve only exact local bindings backed by sealed active Ark receipts."""

    def __init__(
        self,
        receipts: tuple[SeedanceAssetMaterializationReceipt, ...],
        *,
        provider_confirmation_evidence: Mapping[str, bytes],
    ) -> None:
        by_source: dict[str, SeedanceAssetMaterializationReceipt] = {}
        provider_ids: set[str] = set()
        for receipt in receipts:
            if (
                receipt.source_asset_id in by_source
                or receipt.provider_asset_id in provider_ids
            ):
                raise _invalid("Seedance Ark asset materialization identities are ambiguous.")
            confirmation = provider_confirmation_evidence.get(receipt.provider_asset_id)
            if (
                not isinstance(confirmation, bytes)
                or hashlib.sha256(confirmation).hexdigest()
                != receipt.provider_confirmation_sha256
            ):
                raise _invalid("Seedance Ark asset confirmation evidence is not exact.")
            by_source[receipt.source_asset_id] = receipt
            provider_ids.add(receipt.provider_asset_id)
        self._by_source = by_source

    def __call__(
        self, binding: VideoImageReferenceBinding | VideoMediaReferenceBinding
    ) -> str:
        receipt = self._by_source.get(binding.asset_id)
        if receipt is None:
            raise _invalid("Seedance input has no active Ark asset materialization receipt.")
        if (
            receipt.source_asset_sha256 != binding.asset_sha256
            or receipt.source_mime_type != binding.mime_type
            or receipt.source_size_bytes != binding.size_bytes
        ):
            raise _invalid("Seedance Ark asset receipt does not match the exact local input.")
        return f"asset://{receipt.provider_asset_id}"


class SeedanceSyntheticImageReferenceReceipt(StrictModel):
    """Human-attested eligibility and exact local identity for one synthetic PNG."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal["1"] = "1"
    provider_kind: Literal["volcengine_ark_seedance"]
    model_id: str = Field(pattern=r"^[A-Za-z0-9._:-]{1,256}$")
    mode: Literal["image_to_video"]
    transport: Literal["inline_base64"]
    source_asset_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
    source_registry_revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_mime_type: Literal["image/png"]
    source_size_bytes: int = Field(
        strict=True, gt=0, lt=SEEDANCE_MAX_SYNTHETIC_IMAGE_BYTES
    )
    source_width: int = Field(strict=True, gt=0)
    source_height: int = Field(strict=True, gt=0)
    creator: ActorIdentity
    source_record_id: str = Field(min_length=1)
    source_tool: ToolIdentity
    source_evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    rights_source_note: str = Field(min_length=1)
    classification: Literal[
        "real_person_or_protected_identity",
        "synthetic_photorealistic_person",
        "clearly_illustrated_anime_non_real_character",
        "ordinary_non_character_image",
    ]
    attested_by: ActorIdentity
    task_scope_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
    attested_at: datetime
    permitted_use: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_eligibility(self) -> "SeedanceSyntheticImageReferenceReceipt":
        if self.classification == "real_person_or_protected_identity":
            raise ValueError("Seedance inline input rejects real or protected identity")
        if (
            self.classification == "synthetic_photorealistic_person"
            and self.permitted_use != _PROJECT_OWNED_FICTIONAL_IDENTITY_USE
        ):
            raise ValueError(
                "Seedance photorealistic fictional identity requires explicit project-owned attestation"
            )
        if self.classification not in {
            "synthetic_photorealistic_person",
            "clearly_illustrated_anime_non_real_character",
            "ordinary_non_character_image",
        }:
            raise ValueError("Seedance inline input requires a non-identity-bearing class")
        if self.attested_by.actor_kind != "human":
            raise ValueError("Seedance synthetic input requires human attestation")
        if self.attested_at.tzinfo is None:
            raise ValueError("Seedance synthetic attestation requires a timezone")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        )
        if self.content_hash != expected:
            raise ValueError("Seedance synthetic image receipt seal does not match")
        return self

    @classmethod
    def create(cls, **values: object) -> "SeedanceSyntheticImageReferenceReceipt":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.pop("content_hash", None)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            provisional.model_dump(
                mode="json", exclude={"content_hash"}, warnings=False
            )
        )
        return cls.model_validate(data)

    @property
    def evidence_id(self) -> str:
        return f"{_SYNTHETIC_IMAGE_ID_PREFIX}{self.content_hash}"


class SeedanceSyntheticImageReceiptBinding(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    role: Literal["first_frame", "last_frame", "reference"]
    asset_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
    receipt_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class SeedanceSyntheticImageEgressPolicyReceipt(StrictModel):
    """Canonical request-level egress evidence over every synthetic image receipt."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal["1"] = "1"
    task_scope_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
    attempt_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    preview_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    prompt_size_bytes: int = Field(strict=True, ge=0)
    provider_kind: Literal["volcengine_ark_seedance"]
    model_id: str = Field(pattern=r"^[A-Za-z0-9._:-]{1,256}$")
    mode: Literal["image_to_video"]
    transport: Literal["inline_base64"]
    destination: Literal["https://ark.cn-beijing.volces.com"]
    retention_mode: Literal["provider_standard", "zero_retention"]
    children: tuple[SeedanceSyntheticImageReceiptBinding, ...] = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_aggregate(self) -> "SeedanceSyntheticImageEgressPolicyReceipt":
        keys = tuple(
            (_IMAGE_ROLE_ORDER[child.role], child.asset_id) for child in self.children
        )
        if keys != tuple(sorted(keys)):
            raise ValueError("Seedance synthetic receipt children are not canonical")
        if len({child.asset_id for child in self.children}) != len(self.children):
            raise ValueError("Seedance synthetic receipt children are ambiguous")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        )
        if self.content_hash != expected:
            raise ValueError("Seedance synthetic egress receipt seal does not match")
        return self

    @classmethod
    def create(cls, **values: object) -> "SeedanceSyntheticImageEgressPolicyReceipt":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.pop("content_hash", None)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            provisional.model_dump(
                mode="json", exclude={"content_hash"}, warnings=False
            )
        )
        return cls.model_validate(data)

    @property
    def evidence_id(self) -> str:
        return f"{_SYNTHETIC_EGRESS_ID_PREFIX}{self.content_hash}"


def _reopen_synthetic_evidence(
    source: SeedanceSyntheticEvidenceSource,
    policy_receipt_id: str,
) -> tuple[
    SeedanceSyntheticImageEgressPolicyReceipt,
    tuple[SeedanceSyntheticImageReferenceReceipt, ...],
]:
    policy_bytes = _read_evidence(source, policy_receipt_id)
    try:
        policy = SeedanceSyntheticImageEgressPolicyReceipt.model_validate_json(
            policy_bytes
        )
    except Exception:
        raise _invalid("Seedance synthetic egress evidence is invalid.") from None
    if policy.evidence_id != policy_receipt_id or _canonical_model_bytes(policy) != policy_bytes:
        raise _invalid("Seedance synthetic egress evidence is not canonical.")
    receipts: list[SeedanceSyntheticImageReferenceReceipt] = []
    for child in policy.children:
        child_id = f"{_SYNTHETIC_IMAGE_ID_PREFIX}{child.receipt_content_hash}"
        child_bytes = _read_evidence(source, child_id)
        try:
            receipt = SeedanceSyntheticImageReferenceReceipt.model_validate_json(
                child_bytes
            )
        except Exception:
            raise _invalid("Seedance synthetic image evidence is invalid.") from None
        if (
            receipt.evidence_id != child_id
            or receipt.content_hash != child.receipt_content_hash
            or receipt.source_asset_id != child.asset_id
            or _canonical_model_bytes(receipt) != child_bytes
        ):
            raise _invalid("Seedance synthetic image evidence is not canonical.")
        receipts.append(receipt)
    return policy, tuple(receipts)


def _validate_photorealistic_source_evidence(
    source: SeedanceSyntheticEvidenceSource,
    receipts: tuple[SeedanceSyntheticImageReferenceReceipt, ...],
) -> None:
    for receipt in receipts:
        if receipt.classification != "synthetic_photorealistic_person":
            continue
        source_bytes = _read_evidence(source, receipt.source_record_id)
        if hashlib.sha256(source_bytes).hexdigest() != receipt.source_evidence_sha256:
            raise _invalid(
                "Seedance photorealistic fictional identity source evidence does not match."
            )


def _reopen_registry_snapshot(payload: bytes) -> AssetRegistrySnapshot:
    if type(payload) is not bytes:
        raise _invalid("Seedance Registry evidence bytes are invalid.")
    try:
        registry = AssetRegistrySnapshot.model_validate_json(payload)
    except Exception:
        raise _invalid("Seedance Registry evidence is invalid.") from None
    if (
        _canonical_registry_bytes(registry) != payload
        or registry.revision_id != registry.content_hash
        or registry.content_hash != registry_semantic_sha256(registry)
    ):
        raise _invalid("Seedance Registry evidence is not canonical.")
    return registry


def _validate_policy_against_preview(
    policy: SeedanceSyntheticImageEgressPolicyReceipt,
    receipts: tuple[SeedanceSyntheticImageReferenceReceipt, ...],
    preview: PaidProviderCallPreview,
) -> None:
    egress = {item.item_id: item for item in preview.egress_items}
    prompt = egress.get("prompt")
    if (
        policy.attempt_id != preview.attempt_id
        or policy.request_fingerprint != preview.request_fingerprint
        or policy.preview_fingerprint != preview.preview_fingerprint
        or policy.provider_kind != preview.provider_kind
        or policy.model_id != preview.model_id
        or policy.destination != preview.destination
        or policy.retention_mode != preview.retention_mode
        or prompt is None
        or prompt.purpose != "prompt"
        or prompt.sha256 != policy.prompt_sha256
        or prompt.size_bytes != policy.prompt_size_bytes
        or prompt.mime_type != "text/plain"
        or set(egress) != {"prompt", *(receipt.source_asset_id for receipt in receipts)}
        or any(
            (item := egress.get(receipt.source_asset_id)) is None
            or item.purpose != "reference"
            or item.sha256 != receipt.source_asset_sha256
            or item.size_bytes != receipt.source_size_bytes
            or item.mime_type != receipt.source_mime_type
            or receipt.task_scope_id != policy.task_scope_id
            or receipt.provider_kind != policy.provider_kind
            or receipt.model_id != policy.model_id
            or receipt.mode != policy.mode
            for receipt in receipts
        )
    ):
        raise _egress_denied(
            "Seedance synthetic authorization evidence does not match the preview."
        )


class SeedanceSyntheticImageAuthorizer:
    """Wrap an existing authorizer with independent canonical evidence reopening."""

    def __init__(
        self,
        *,
        delegate: SeedancePaidProviderAuthorizer,
        evidence_source: SeedanceSyntheticEvidenceSource,
    ) -> None:
        self._delegate = delegate
        self._evidence_source = evidence_source

    def __call__(
        self, preview: PaidProviderCallPreview
    ) -> PaidProviderAuthorizationDecision | None:
        authorization = self._delegate(preview)
        if authorization is None:
            return None
        try:
            policy, receipts = _reopen_synthetic_evidence(
                self._evidence_source,
                authorization.egress_policy_receipt_id,
            )
            _validate_photorealistic_source_evidence(
                self._evidence_source,
                receipts,
            )
        except AiVideoError:
            raise _egress_denied(
                "Seedance synthetic authorization evidence is unavailable."
            ) from None
        _validate_policy_against_preview(policy, receipts, preview)
        return authorization


class SeedanceSyntheticImageReferenceResolver:
    """Resolve exact human-attested synthetic PNG bytes to an in-memory data URI."""

    def __init__(
        self,
        receipts: tuple[SeedanceSyntheticImageReferenceReceipt, ...],
        *,
        policy_receipt: SeedanceSyntheticImageEgressPolicyReceipt,
        image_bytes: Mapping[str, bytes],
        evidence_source: SeedanceSyntheticEvidenceSource,
        registry_snapshot_bytes: bytes,
    ) -> None:
        reopened_policy, reopened_receipts = _reopen_synthetic_evidence(
            evidence_source, policy_receipt.evidence_id
        )
        if reopened_policy != policy_receipt or reopened_receipts != receipts:
            raise _invalid("Seedance synthetic evidence does not match caller identity.")
        _validate_photorealistic_source_evidence(evidence_source, receipts)
        registry = _reopen_registry_snapshot(registry_snapshot_bytes)
        by_source: dict[str, SeedanceSyntheticImageReferenceReceipt] = {}
        measured_bytes: dict[str, bytes] = {}
        for receipt in receipts:
            if type(receipt) is not SeedanceSyntheticImageReferenceReceipt:
                raise _invalid("Seedance synthetic input receipt type is invalid.")
            if receipt.source_asset_id in by_source:
                raise _invalid("Seedance synthetic input receipt identities are ambiguous.")
            payload = image_bytes.get(receipt.source_asset_id)
            if not isinstance(payload, bytes):
                raise _invalid("Seedance synthetic input bytes are unavailable.")
            try:
                measured = measure_png_bytes(payload)
            except (AiVideoError, ValueError, TypeError):
                raise _invalid("Seedance synthetic input PNG is invalid.") from None
            if (
                receipt.source_registry_revision_id != registry.revision_id
                or measured.sha256 != receipt.source_asset_sha256
                or measured.size_bytes != receipt.source_size_bytes
                or measured.mime_type != receipt.source_mime_type
                or measured.width != receipt.source_width
                or measured.height != receipt.source_height
            ):
                raise _invalid("Seedance synthetic input bytes do not match the receipt.")
            registry_records = tuple(
                record
                for record in registry.assets
                if record.asset_id == receipt.source_asset_id
            )
            if len(registry_records) != 1:
                raise _invalid("Seedance synthetic Registry asset is unavailable.")
            record = registry_records[0]
            if (
                record.asset_type is not AssetType.IMAGE
                or record.sha256 != receipt.source_asset_sha256
                or record.size_bytes != receipt.source_size_bytes
                or record.mime_type != receipt.source_mime_type
                or record.width != receipt.source_width
                or record.height != receipt.source_height
            ):
                raise _invalid("Seedance synthetic Registry asset does not match receipt.")
            if receipt.classification == "synthetic_photorealistic_person" and (
                record.source_kind not in _FICTIONAL_IDENTITY_SOURCE_KINDS
                or record.tool != receipt.source_tool
                or record.creation_receipt_id != receipt.source_record_id
                or record.usage_license not in _FICTIONAL_IDENTITY_USAGE_LICENSES
            ):
                raise _invalid(
                    "Seedance photorealistic fictional identity provenance is not sealed."
                )
            by_source[receipt.source_asset_id] = receipt
            measured_bytes[receipt.source_asset_id] = payload
        if set(image_bytes) != set(by_source):
            raise _invalid("Seedance synthetic input bytes do not match receipt ownership.")
        if type(policy_receipt) is not SeedanceSyntheticImageEgressPolicyReceipt:
            raise _invalid("Seedance synthetic egress policy receipt type is invalid.")
        expected_children = tuple(
            (
                child.asset_id,
                child.receipt_content_hash,
            )
            for child in policy_receipt.children
        )
        actual_children = tuple(
            (receipt.source_asset_id, receipt.content_hash) for receipt in receipts
        )
        if expected_children != actual_children:
            raise _invalid("Seedance synthetic egress children do not match receipts.")
        self._by_source = MappingProxyType(by_source)
        self._image_bytes = MappingProxyType(measured_bytes)
        self._policy_receipt = policy_receipt
        self._registry = registry
        self._registry_snapshot_sha256 = hashlib.sha256(registry_snapshot_bytes).hexdigest()

    @property
    def egress_policy_receipt_id(self) -> str:
        return self._policy_receipt.evidence_id

    def validate_submit(
        self,
        request: ResolvedVideoGenerationRequest,
        preview: PaidProviderCallPreview,
        authorization: PaidProviderAuthorizationDecision,
    ) -> None:
        policy = self._policy_receipt
        prompt_bytes = request.prompt_text.encode()
        scope = request.activation_scope
        expected_children = tuple(
            SeedanceSyntheticImageReceiptBinding(
                role=binding.role,
                asset_id=binding.asset_id,
                receipt_content_hash=self._by_source[binding.asset_id].content_hash,
            )
            for binding in request.image_bindings
            if binding.asset_id in self._by_source
        )
        if (
            scope is None
            or scope.request.base_registry.revision_id != self._registry.revision_id
            or scope.request.base_registry.content_hash != self._registry.content_hash
            or scope.request.base_registry.file_sha256 != self._registry_snapshot_sha256
            or request.media_bindings
            or len(expected_children) != len(request.image_bindings)
            or expected_children != policy.children
            or any(
                receipt.task_scope_id != policy.task_scope_id
                or receipt.provider_kind != request.provider_kind
                or receipt.model_id != request.model_id
                or receipt.mode != request.mode.value
                for receipt in self._by_source.values()
            )
            or policy.attempt_id != preview.attempt_id
            or policy.request_fingerprint != request.resolved_generation_hash
            or policy.preview_fingerprint != preview.preview_fingerprint
            or policy.prompt_sha256 != hashlib.sha256(prompt_bytes).hexdigest()
            or policy.prompt_size_bytes != len(prompt_bytes)
            or policy.provider_kind != request.provider_kind
            or policy.model_id != request.model_id
            or policy.mode != request.mode.value
            or policy.destination != preview.destination
            or policy.retention_mode != preview.retention_mode
        ):
            raise _invalid("Seedance synthetic egress evidence does not match the request.")
        if authorization.egress_policy_receipt_id != self.egress_policy_receipt_id:
            raise _egress_denied(
                "Seedance synthetic egress authorization does not match the exact receipt."
            )

    def __call__(self, binding: VideoImageReferenceBinding) -> str:
        if type(binding) is not VideoImageReferenceBinding:
            raise _invalid("Seedance synthetic input requires an image binding.")
        receipt = self._by_source.get(binding.asset_id)
        payload = self._image_bytes.get(binding.asset_id)
        if receipt is None or payload is None:
            raise _invalid("Seedance synthetic input has no exact receipt.")
        if (
            binding.asset_sha256 != receipt.source_asset_sha256
            or binding.mime_type != receipt.source_mime_type
            or binding.size_bytes != receipt.source_size_bytes
            or binding.width != receipt.source_width
            or binding.height != receipt.source_height
        ):
            raise _invalid("Seedance synthetic receipt does not match the image binding.")
        encoded = base64.b64encode(payload).decode("ascii")
        return f"data:{receipt.source_mime_type};base64,{encoded}"
