"""Sealed evidence for a returned remote image rejected during local materialization."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

from pydantic import Field, field_validator, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256

if TYPE_CHECKING:
    from ai_video.production.image import (
        ImageGenerationAuthorization,
        ImageGenerationPreview,
        ImageGenerationRequest,
        ImageProvenanceReceipt,
        ImageProviderResult,
        MeasuredPng,
    )
    from ai_video.production.models import LoadedProductionProject, StateCommitAttempt


_SHA256 = r"^[0-9a-f]{64}$"
_SCHEMA = "image-materialization-failure/1"
RetainedRemoteImageResult: TypeAlias = tuple[
    "ImageGenerationRequest",
    "ImageGenerationPreview",
    "ImageGenerationAuthorization",
    "ImageProviderResult",
    "MeasuredPng",
    "ImageProvenanceReceipt",
]
RetainedArtifactHashes: TypeAlias = tuple[tuple[Path, str], ...]


class ImageMaterializationFailurePointer(StrictModel):
    path: Path
    content_hash: str = Field(pattern=_SHA256)
    file_sha256: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _canonical_pointer(self) -> "ImageMaterializationFailurePointer":
        expected = Path(f"state/images/materialization-failures/{self.content_hash}.json")
        if self.path.is_absolute() or ".." in self.path.parts or self.path != expected:
            raise ValueError("image materialization failure path must be canonical")
        return self


class ImageMaterializationFailure(StrictModel):
    schema_version: Literal["image-materialization-failure/1"] = _SCHEMA
    project_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    expected_manifest_revision: int = Field(strict=True, ge=1)
    request_fingerprint: str = Field(pattern=_SHA256)
    result_fingerprint: str = Field(pattern=_SHA256)
    image_receipt_hash: str = Field(pattern=_SHA256)
    output_sha256: str = Field(pattern=_SHA256)
    paid_submit_fingerprint: str = Field(pattern=_SHA256)
    base_project_hash: str = Field(pattern=_SHA256)
    base_registry_hash: str = Field(pattern=_SHA256)
    base_graph_hash: str = Field(pattern=_SHA256)
    actor_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    recorded_at: datetime
    content_hash: str = Field(pattern=_SHA256)

    @field_validator("recorded_at")
    @classmethod
    def _require_aware_recorded_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("image materialization failure time must be timezone-aware")
        return value

    @field_validator("actor_id", "reason")
    @classmethod
    def _require_nonblank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("image materialization failure text must not be blank")
        return value

    @model_validator(mode="after")
    def _sealed_content_hash(self) -> "ImageMaterializationFailure":
        if self.content_hash != canonical_sha256(self):
            raise ValueError("image materialization failure content hash does not match")
        return self

    @classmethod
    def create(cls, **values: Any) -> "ImageMaterializationFailure":
        data = dict(values)
        data["schema_version"] = _SCHEMA
        draft = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(draft)
        return cls.model_validate(data)


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _read_canonical_json(root: Path, path: Path, *, label: str):
    from ai_video.production.paths import _read_regular_file_nofollow

    snapshot = _read_regular_file_nofollow(root / path, contained_by=root)
    value = json.loads(snapshot.data)
    if not isinstance(value, dict) or snapshot.data != _canonical_json_bytes(value):
        raise ValueError(f"{label} is not canonical JSON")
    return value, snapshot


def _load_retained_remote_image_result(
    root: Path,
    attempt: "StateCommitAttempt",
    result_fingerprint: str,
    image_receipt_hash: str,
) -> tuple[RetainedRemoteImageResult, RetainedArtifactHashes]:
    from ai_video.production._remote_image_reader import (
        reopen_remote_image_authority,
        reopen_remote_image_result,
    )
    from ai_video.production.image import (
        ImageGenerationAuthorization,
        ImageGenerationPreview,
        ImageGenerationRequest,
        ImageProvenanceReceipt,
        measure_png_bytes,
        validate_image_result,
    )
    from ai_video.production.paths import (
        _read_regular_file_nofollow,
        canonical_image_asset_path,
        canonical_image_authorization_path,
        canonical_image_preview_path,
        canonical_image_receipt_path,
        canonical_image_request_path,
        canonical_image_result_path,
    )

    root = Path(root)
    summary = attempt.image_request
    if (attempt.operation != "image_generation" or summary is None
            or attempt.image_phase != "materialize"
            or attempt.status.value not in {"outcome_unknown", "failed"}):
        raise ValueError("attempt is not a retained remote image materialization failure")

    request, preview, authorization = reopen_remote_image_authority(root, attempt)
    if authorization.remote_binding is None or not preview.remote:
        raise ValueError("retained image result is not remote")
    if (request.base_project != attempt.base_project
            or request.base_registry != attempt.base_registry
            or request.base_dependency_graph != attempt.base_dependency_graph):
        raise ValueError("retained image request base differs from its attempt")

    request_path = canonical_image_request_path(request.request_fingerprint)
    preview_path = canonical_image_preview_path(preview.preview_fingerprint)
    authorization_path = canonical_image_authorization_path(
        authorization.authorization_fingerprint
    )
    request_value, _ = _read_canonical_json(root, request_path, label="image request")
    preview_value, _ = _read_canonical_json(root, preview_path, label="image preview")
    authorization_value, _ = _read_canonical_json(
        root, authorization_path, label="image authorization"
    )
    if (ImageGenerationRequest.model_validate(request_value) != request
            or ImageGenerationPreview.model_validate(preview_value) != preview
            or ImageGenerationAuthorization.model_validate(authorization_value) != authorization):
        raise ValueError("retained image authority bytes differ from their reopened models")

    receipt_path = canonical_image_receipt_path(image_receipt_hash)
    receipt_value, receipt_file = _read_canonical_json(
        root, receipt_path, label="image provenance receipt"
    )
    receipt = ImageProvenanceReceipt.model_validate(receipt_value)
    if (receipt.content_hash != image_receipt_hash or not receipt.remote
            or receipt.remote_evidence is None):
        raise ValueError("retained image provenance receipt identity is invalid")

    png_path = canonical_image_asset_path(receipt.output_sha256)
    png_file = _read_regular_file_nofollow(
        root / png_path, contained_by=root / "assets/files"
    )
    measured_file = measure_png_bytes(png_file.data)
    if (png_file.file_sha256 != receipt.output_sha256
            or measured_file.sha256 != receipt.output_sha256
            or measured_file.size_bytes != receipt.output_size_bytes
            or measured_file.mime_type != receipt.output_mime_type
            or measured_file.width != receipt.output_width
            or measured_file.height != receipt.output_height):
        raise ValueError("retained PNG bytes do not match the image provenance receipt")

    result_path = canonical_image_result_path(result_fingerprint)
    result_value, result_file = _read_canonical_json(
        root, result_path, label="image provider result"
    )
    if ("image_bytes" in result_value or "wire_image_bytes" in result_value
            or result_value.get("result_fingerprint") != result_fingerprint):
        raise ValueError("retained image result identity or stored shape is invalid")
    reopened_authorization, result, wire_pairs = reopen_remote_image_result(
        root, attempt, receipt, png_file.data, result_value
    )
    measured, checked_receipt = validate_image_result(
        request, reopened_authorization, result
    )
    if (reopened_authorization != authorization or result.result_fingerprint != result_fingerprint
            or measured != measured_file or checked_receipt != receipt):
        raise ValueError("retained image result, PNG and provenance do not join exactly")

    values = (request, preview, authorization, result, measured, receipt)
    retained_pairs = (
        (result_path, result_file.file_sha256),
        (receipt_path, receipt_file.file_sha256),
        (png_path, png_file.file_sha256),
        *wire_pairs,
    )
    return values, retained_pairs


def load_retained_remote_image_result(
    root: Path,
    attempt: "StateCommitAttempt",
    result_fingerprint: str,
    image_receipt_hash: str,
) -> RetainedRemoteImageResult:
    """Reopen a returned remote image without consulting live Provider state."""

    values, _ = _load_retained_remote_image_result(
        root, attempt, result_fingerprint, image_receipt_hash
    )
    return values


def _verify_base_snapshot_joins(
    bundle: "LoadedProductionProject", attempt: "StateCommitAttempt"
) -> None:
    from ai_video.production._image_project_reader import (
        _read_project_pointer,
        _read_registry_pointer,
    )
    from ai_video.production.dependency import dependency_graph_semantic_sha256
    from ai_video.production.models import DependencyGraphSnapshot
    from ai_video.production.paths import (
        _read_regular_file_nofollow,
        canonical_dependency_graph_snapshot_path,
    )

    if attempt.base_dependency_graph is None:
        raise ValueError("image materialization failure has no base dependency graph")
    _read_project_pointer(bundle, attempt.base_project, label="materialization base")
    _read_registry_pointer(bundle, attempt.base_registry, label="materialization base")
    pointer = attempt.base_dependency_graph
    if pointer.path != canonical_dependency_graph_snapshot_path(pointer.revision_id):
        raise ValueError("image materialization base graph path is not canonical")
    snapshot = _read_regular_file_nofollow(
        bundle.root / pointer.path, contained_by=bundle.root / "state"
    )
    graph = DependencyGraphSnapshot.model_validate_json(snapshot.data)
    if (snapshot.file_sha256 != pointer.file_sha256
            or graph.revision_id != pointer.revision_id
            or graph.content_hash != pointer.content_hash
            or dependency_graph_semantic_sha256(graph) != pointer.content_hash):
        raise ValueError("image materialization base graph identity is invalid")


def verify_image_materialization_failure(
    bundle: "LoadedProductionProject", attempt: "StateCommitAttempt"
) -> RetainedArtifactHashes:
    """Verify a failed materialization closure and return its retained artifacts."""

    from ai_video.production.paths import _read_regular_file_nofollow

    pointer = getattr(attempt, "image_materialization_failure", None)
    if pointer is None:
        raise ValueError("image materialization failure pointer is missing")
    expected_path = Path(
        f"state/images/materialization-failures/{pointer.content_hash}.json"
    )
    if pointer.path != expected_path or pointer.path.is_absolute() or ".." in pointer.path.parts:
        raise ValueError("image materialization failure pointer path is not canonical")
    closure_file = _read_regular_file_nofollow(
        bundle.root / pointer.path, contained_by=bundle.root / "state"
    )
    if closure_file.file_sha256 != pointer.file_sha256:
        raise ValueError("image materialization failure file hash does not match its pointer")
    closure_value = json.loads(closure_file.data)
    if (not isinstance(closure_value, dict)
            or closure_file.data != _canonical_json_bytes(closure_value)):
        raise ValueError("image materialization failure is not canonical JSON")
    closure = ImageMaterializationFailure.model_validate(closure_value)
    if closure.content_hash != pointer.content_hash:
        raise ValueError("image materialization failure content hash does not match its pointer")

    candidate_bundle = (
        attempt.candidate_project,
        attempt.candidate_registry,
        attempt.candidate_dependency_graph,
        attempt.candidate_dependency_states_hash,
    )
    paid_state = attempt.paid_provider_state
    paid_phase = getattr(paid_state.phase, "value", paid_state.phase) if paid_state is not None else None
    if (attempt.operation != "image_generation" or attempt.status.value != "failed"
            or attempt.image_phase != "materialize"
            or attempt.error_code != "image_request_invalid"
            or attempt.finished_at != closure.recorded_at.isoformat()
            or any(item is not None for item in candidate_bundle)
            or attempt.candidate_image_asset_ids
            or paid_phase not in {"accepted", "settled"}):
        raise ValueError("image materialization failure attempt state is inconsistent")

    values, retained_pairs = _load_retained_remote_image_result(
        bundle.root, attempt, closure.result_fingerprint, closure.image_receipt_hash
    )
    request, _preview, _authorization, result, measured, receipt = values
    submit = result.remote_evidence.submit_receipt if result.remote_evidence is not None else None
    if (closure.project_id != bundle.manifest.project_id
            or closure.attempt_id != attempt.attempt_id
            or closure.expected_manifest_revision >= bundle.manifest.manifest_revision
            or closure.expected_manifest_revision < attempt.base_manifest_revision
            or closure.request_fingerprint != request.request_fingerprint
            or closure.result_fingerprint != result.result_fingerprint
            or closure.image_receipt_hash != receipt.content_hash
            or closure.output_sha256 != measured.sha256
            or submit is None
            or closure.paid_submit_fingerprint != submit.submit_receipt_fingerprint
            or paid_state.submit_receipt is None
            or paid_state.submit_receipt.submit_receipt_fingerprint != submit.submit_receipt_fingerprint
            or attempt.provider_request_id != result.provider_request_id
            or attempt.base_dependency_graph is None
            or closure.base_project_hash != attempt.base_project.content_hash
            or closure.base_registry_hash != attempt.base_registry.content_hash
            or closure.base_graph_hash != attempt.base_dependency_graph.content_hash
            or request.base_project != attempt.base_project
            or request.base_registry != attempt.base_registry
            or request.base_dependency_graph != attempt.base_dependency_graph):
        raise ValueError("image materialization failure closure does not join its retained evidence")
    _verify_base_snapshot_joins(bundle, attempt)
    return ((pointer.path, pointer.file_sha256), *retained_pairs)


__all__ = [
    "ImageMaterializationFailure",
    "ImageMaterializationFailurePointer",
    "load_retained_remote_image_result",
    "verify_image_materialization_failure",
]
