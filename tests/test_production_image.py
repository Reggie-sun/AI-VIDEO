from __future__ import annotations

import hashlib
import struct
import zlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.production.image import (
    ImageGenerationAuthorization,
    ImageGenerationPreview,
    ImageGenerationRequest,
    ImageLocalResourceEvidence,
    ImageProviderParameters,
    ImageProviderResult,
    ImageReferenceBinding,
    validate_image_result,
)
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    ToolIdentity,
)


ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64
TWO_HASH = "2" * 64
THREE_HASH = "3" * 64


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def _rgba_png(width: int, height: int) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    row = b"\x00" + (b"\x00\x00\x00\xff" * width)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(row * height))
        + _png_chunk(b"IEND", b"")
    )


PNG_2X1_RGBA = _rgba_png(2, 1)
PNG_WITH_TRUNCATED_IHDR = b"\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR\x00\x00"


def make_image_request(**overrides: object) -> ImageGenerationRequest:
    width = int(overrides.pop("width", 512))
    height = int(overrides.pop("height", 512))
    generation_revision = int(overrides.pop("generation_revision", 1))
    values: dict[str, object] = {
        "attempt_id": "image-attempt-1",
        "provider_kind": "fake-local",
        "model_id": "fixture-image-model-1",
        "target_shot_id": "shot-1",
        "target_asset_role": "hero",
        "prompt_text": "Hero enters the archive room",
        "negative_prompt_text": "blur, watermark",
        "parameters": ImageProviderParameters(
            seed=7,
            width=width,
            height=height,
            output_format="png",
            generation_revision=generation_revision,
        ),
        "references": (
            ImageReferenceBinding(
                role="character",
                creative_artifact_id="character-hero",
                creative_revision=1,
                creative_content_hash=ZERO_HASH,
                asset_id="image-character-hero",
                asset_sha256=ONE_HASH,
            ),
            ImageReferenceBinding(
                role="scene",
                creative_artifact_id="scene-archive",
                creative_revision=1,
                creative_content_hash=TWO_HASH,
                asset_id="image-scene-archive",
                asset_sha256=THREE_HASH,
            ),
        ),
        "base_project": ProjectSnapshotPointer(
            path=Path(f"state/projects/project.1.{ZERO_HASH}.yaml"),
            revision=1,
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        ),
        "base_registry": RegistrySnapshotPointer(
            path=Path(f"assets/registry.{ONE_HASH}.json"),
            revision_id=ONE_HASH,
            content_hash=ONE_HASH,
            file_sha256=TWO_HASH,
        ),
        "base_dependency_graph": DependencyGraphSnapshotPointer(
            revision_id=TWO_HASH,
            content_hash=TWO_HASH,
            path=Path(f"state/dependency_graph.{TWO_HASH}.json"),
            file_sha256=THREE_HASH,
        ),
    }
    values.update(overrides)
    return ImageGenerationRequest.create(**values)


def make_preview_payload(**overrides: object) -> dict[str, object]:
    request = make_image_request()
    preview = ImageGenerationPreview.create(
        request=request,
        reference_total_bytes=321,
    )
    payload = preview.model_dump(mode="json")
    payload.update(overrides)
    return payload


def make_authorization(
    request: ImageGenerationRequest,
) -> ImageGenerationAuthorization:
    preview = ImageGenerationPreview.create(
        request=request,
        reference_total_bytes=321,
    )
    return ImageGenerationAuthorization.create(
        request=request,
        preview=preview,
        usage_license="project-owned-fixture",
        policy_receipt_id="policy-local-image-1",
    )


def make_image_result(
    request: ImageGenerationRequest,
    *,
    image_bytes: bytes = b"fixture-image-bytes",
) -> ImageProviderResult:
    authorization = make_authorization(request)
    return ImageProviderResult.create(
        request=request,
        authorization=authorization,
        image_bytes=image_bytes,
        content_type="image/png",
        provider_request_id="local-job-1",
        adapter=ToolIdentity(name="fake-local-image", version="1"),
        resource_evidence=ImageLocalResourceEvidence(
            elapsed_milliseconds=5,
            device_kind="cpu",
            measured_peak_memory_bytes=1024,
        ),
    )


def test_image_request_binds_prompt_target_references_and_base_pointers():
    request = make_image_request(target_shot_id="shot-1", generation_revision=1)

    assert request.request_id == request.request_fingerprint
    assert request.output_asset_id == f"image-{request.request_fingerprint}"
    assert tuple(item.role for item in request.references) == (
        "character",
        "scene",
    )
    assert request.base_dependency_graph.revision_id == TWO_HASH


def test_image_request_rejects_changed_prompt_under_old_fingerprint():
    request = make_image_request(target_shot_id="shot-1", generation_revision=1)
    payload = request.model_dump(mode="json")
    payload["prompt_text"] = "Different prompt"

    with pytest.raises(ValidationError, match="request_fingerprint"):
        ImageGenerationRequest.model_validate(payload)


def test_image_contract_rejects_remote_preview_and_non_png_output():
    with pytest.raises(ValidationError):
        ImageGenerationPreview.model_validate(make_preview_payload(remote=True))
    with pytest.raises(ValidationError):
        ImageProviderParameters(
            seed=7,
            width=512,
            height=512,
            output_format="jpeg",
            generation_revision=1,
        )


def test_image_request_rejects_noncanonical_or_incomplete_references():
    request = make_image_request()

    with pytest.raises(ValidationError, match="canonical order"):
        make_image_request(references=tuple(reversed(request.references)))
    with pytest.raises(ValidationError, match="character.*scene"):
        make_image_request(references=(request.references[0],))


def test_image_request_rejects_non_nfc_prompt_text():
    with pytest.raises(ValidationError, match="NFC"):
        make_image_request(prompt_text="Cafe\u0301")


def test_image_result_rejects_changed_bytes_under_old_hash():
    request = make_image_request()
    result = make_image_result(request)
    payload = result.model_dump(mode="python")
    payload["image_bytes"] = b"changed"

    with pytest.raises(ValidationError, match="image_sha256"):
        ImageProviderResult.model_validate(payload)


def test_validate_image_result_uses_measured_png_dimensions_and_hash():
    request = make_image_request(width=2, height=1)
    authorization = make_authorization(request)
    result = make_image_result(request, image_bytes=PNG_2X1_RGBA)

    measured, receipt = validate_image_result(request, authorization, result)

    assert (measured.width, measured.height) == (2, 1)
    assert measured.sha256 == hashlib.sha256(PNG_2X1_RGBA).hexdigest()
    assert measured.size_bytes == len(PNG_2X1_RGBA)
    assert receipt.request_fingerprint == request.request_fingerprint
    assert receipt.content_hash
    assert receipt.resource_evidence == result.resource_evidence


@pytest.mark.parametrize(
    "payload",
    [b"not-png", PNG_WITH_TRUNCATED_IHDR, _rgba_png(1, 2)],
)
def test_validate_image_result_rejects_invalid_or_wrong_size_png(payload: bytes):
    request = make_image_request(width=2, height=1)
    authorization = make_authorization(request)
    result = make_image_result(request, image_bytes=payload)

    with pytest.raises(AiVideoError) as error:
        validate_image_result(request, authorization, result)

    assert error.value.code is ErrorCode.ASSET_REGISTRY_INVALID


def test_image_provider_result_rejects_empty_bytes():
    request = make_image_request()

    with pytest.raises(ValidationError, match="image_bytes"):
        make_image_result(request, image_bytes=b"")


def test_validate_image_result_rejects_wrong_authorization_binding():
    request = make_image_request()
    other_request = make_image_request(prompt_text="A different shot prompt")
    result = make_image_result(request, image_bytes=_rgba_png(512, 512))

    with pytest.raises(AiVideoError) as error:
        validate_image_result(request, make_authorization(other_request), result)

    assert error.value.code is ErrorCode.PRODUCTION_STATE_INVALID
