from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.production.image import (
    ImageGenerationAuthorization,
    ImageGenerationPreview,
    ImageGenerationRequest,
    ImageActivationCandidate,
    ImageLocalResourceEvidence,
    ImageProviderParameters,
    ImageProviderResult,
    ImageReferenceBinding,
    validate_image_activation_candidate,
    validate_image_result,
)
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    ArtifactReference,
    AssetRecord,
    AssetSourceKind,
    AssetType,
    DependencyLifecycle,
    DependencyNodeState,
    DependencyGraphSnapshotPointer,
    EgressMetadata,
    ProjectDependencyEvidence,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    ToolIdentity,
)
from ai_video.production.dependency import (
    build_production_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.registry import registry_semantic_sha256
from production_project_factory import make_p5_selective_rebuild_fixture


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


def _fresh_states(project, graph):
    desired = desired_fingerprints(graph)
    return tuple(
        DependencyNodeState(
            node_id=node.node_id,
            graph_revision_id=graph.revision_id,
            desired_fingerprint=desired[node.node_id],
            applied_fingerprint=desired[node.node_id],
            lifecycle=DependencyLifecycle.FRESH,
            applied_evidence=ProjectDependencyEvidence(
                owner="project_snapshot",
                pointer=project.manifest.active_project,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node.node_id],
            ),
        )
        for node in graph.nodes
    )


@pytest.fixture
def p7_candidate(tmp_path):
    inputs, _ = make_p5_selective_rebuild_fixture(tmp_path)
    base_graph = build_production_dependency_graph(inputs)
    base_graph_pointer = DependencyGraphSnapshotPointer(
        revision_id=base_graph.revision_id,
        content_hash=base_graph.content_hash,
        path=Path(f"state/dependency_graph.{base_graph.revision_id}.json"),
        file_sha256=hashlib.sha256(b"base-graph").hexdigest(),
    )
    base_project = inputs.project.model_copy(
        update={
            "manifest": inputs.project.manifest.model_copy(
                update={"active_dependency_graph": base_graph_pointer}
            ),
            "dependency_graph": base_graph,
        }
    )
    inputs = replace(inputs, project=base_project)
    assets = {asset.asset_id: asset for asset in base_project.registry.assets}
    character = base_project.characters[0]
    scene = base_project.scenes[0]
    character_asset_id = character.reference_asset_ids[0]
    scene_asset_id = scene.visual_reference_asset_ids[0]
    request = ImageGenerationRequest.create(
        attempt_id="image-attempt-candidate-1",
        provider_kind="fake-local",
        model_id="fixture-image-model-1",
        target_shot_id="shot-1",
        target_asset_role="still",
        prompt_text="Hero enters the archive room",
        negative_prompt_text="blur, watermark",
        parameters=ImageProviderParameters(
            seed=7,
            width=2,
            height=1,
            output_format="png",
            generation_revision=1,
        ),
        references=(
            ImageReferenceBinding(
                role="character",
                creative_artifact_id=character.artifact_id,
                creative_revision=character.revision,
                creative_content_hash=character.content_hash,
                asset_id=character_asset_id,
                asset_sha256=assets[character_asset_id].sha256,
            ),
            ImageReferenceBinding(
                role="scene",
                creative_artifact_id=scene.artifact_id,
                creative_revision=scene.revision,
                creative_content_hash=scene.content_hash,
                asset_id=scene_asset_id,
                asset_sha256=assets[scene_asset_id].sha256,
            ),
        ),
        base_project=base_project.manifest.active_project,
        base_registry=base_project.manifest.active_registry,
        base_dependency_graph=base_graph_pointer,
    )
    authorization = make_authorization(request)
    result = make_image_result(request, image_bytes=PNG_2X1_RGBA)
    measured, receipt = validate_image_result(request, authorization, result)
    image_record = AssetRecord(
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
    candidate_registry = base_project.registry.model_copy(
        update={
            "revision_id": ZERO_HASH,
            "content_hash": ZERO_HASH,
            "assets": (*base_project.registry.assets, image_record),
        }
    )
    registry_hash = registry_semantic_sha256(candidate_registry)
    candidate_registry = candidate_registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    registry_pointer = RegistrySnapshotPointer(
        path=Path(f"assets/registry.{registry_hash}.json"),
        revision_id=registry_hash,
        content_hash=registry_hash,
        file_sha256=hashlib.sha256(b"candidate-registry").hexdigest(),
    )

    base_shot = next(shot for shot in base_project.shots if shot.shot_id == "shot-1")
    role = next(item for item in base_shot.required_asset_roles if item.role == "still")
    candidate_shot = seal_artifact(
        base_shot.model_copy(
            update={
                "revision": base_shot.revision + 1,
                "content_hash": ZERO_HASH,
                "creation_receipt_id": receipt.content_hash,
                "required_asset_roles": (
                    role.model_copy(update={"asset_ids": (request.output_asset_id,)}),
                ),
            }
        )
    )
    shot_reference = next(
        item
        for item in base_project.project.artifacts.shots
        if item.artifact_id == candidate_shot.artifact_id
    )
    candidate_shot_reference = ArtifactReference(
        artifact_id=candidate_shot.artifact_id,
        revision=candidate_shot.revision,
        content_hash=candidate_shot.content_hash,
        path=shot_reference.path,
    )
    candidate_project_artifact = seal_artifact(
        base_project.project.model_copy(
            update={
                "revision": base_project.project.revision + 1,
                "content_hash": ZERO_HASH,
                "creation_receipt_id": receipt.content_hash,
                "artifacts": base_project.project.artifacts.model_copy(
                    update={
                        "shots": tuple(
                            candidate_shot_reference
                            if item.artifact_id == candidate_shot.artifact_id
                            else item
                            for item in base_project.project.artifacts.shots
                        )
                    }
                ),
            }
        )
    )
    project_pointer = ProjectSnapshotPointer(
        path=Path(
            f"state/projects/project.{candidate_project_artifact.revision}."
            f"{candidate_project_artifact.content_hash}.yaml"
        ),
        revision=candidate_project_artifact.revision,
        content_hash=candidate_project_artifact.content_hash,
        file_sha256=hashlib.sha256(b"candidate-project").hexdigest(),
    )
    candidate_project = base_project.model_copy(
        update={
            "project": candidate_project_artifact,
            "shots": tuple(
                candidate_shot if shot.shot_id == candidate_shot.shot_id else shot
                for shot in base_project.shots
            ),
            "registry": candidate_registry,
            "asset_paths": {
                **base_project.asset_paths,
                request.output_asset_id: tmp_path / image_record.artifact_path,
            },
            "manifest": base_project.manifest.model_copy(
                update={
                    "active_project": project_pointer,
                    "active_registry": registry_pointer,
                }
            ),
        }
    )
    candidate_inputs = replace(inputs, project=candidate_project)
    candidate_graph = build_production_dependency_graph(candidate_inputs)
    candidate_graph_pointer = DependencyGraphSnapshotPointer(
        revision_id=candidate_graph.revision_id,
        content_hash=candidate_graph.content_hash,
        path=Path(f"state/dependency_graph.{candidate_graph.revision_id}.json"),
        file_sha256=hashlib.sha256(b"candidate-graph").hexdigest(),
    )
    candidate_project = candidate_project.model_copy(
        update={
            "manifest": candidate_project.manifest.model_copy(
                update={"active_dependency_graph": candidate_graph_pointer}
            ),
            "dependency_graph": candidate_graph,
        }
    )
    candidate_inputs = replace(candidate_inputs, project=candidate_project)
    resolution = resolve_dependency_state(
        candidate_graph,
        _fresh_states(base_project, base_graph),
    )
    return {
        "base_project": base_project,
        "request": request,
        "authorization": authorization,
        "result": result,
        "measured": measured,
        "receipt": receipt,
        "candidate_project": candidate_project,
        "candidate_registry": candidate_registry,
        "candidate_graph": candidate_graph,
        "candidate_inputs": candidate_inputs,
        "resolution": resolution,
    }


def test_candidate_appends_one_image_and_changes_only_target_shot_role(p7_candidate):
    checked = validate_image_activation_candidate(**p7_candidate)

    assert isinstance(checked, ImageActivationCandidate)
    assert checked.image_asset_id == p7_candidate["request"].output_asset_id
    assert checked.changed_shot_ids == ("shot-1",)


@pytest.mark.parametrize("mutation", ["character", "unrelated_shot"])
def test_candidate_rejects_mutated_character_or_unrelated_shot(
    p7_candidate, mutation
):
    candidate = p7_candidate["candidate_project"]
    if mutation == "character":
        changed = candidate.characters[0].model_copy(update={"name": "Unauthorized"})
        changed_project = candidate.model_copy(update={"characters": (changed,)})
    else:
        unrelated = candidate.shots[1].model_copy(update={"intent": "unauthorized"})
        changed_project = candidate.model_copy(
            update={"shots": (candidate.shots[0], unrelated)}
        )
    tampered = {**p7_candidate, "candidate_project": changed_project}

    with pytest.raises(AiVideoError) as error:
        validate_image_activation_candidate(**tampered)

    assert error.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_image_activation_candidate_has_no_public_constructor():
    with pytest.raises(TypeError, match="validate_image_activation_candidate"):
        ImageActivationCandidate(object())


@pytest.mark.parametrize("mutation", ["overwrite", "extra"])
def test_candidate_rejects_registry_overwrite_or_extra_asset(p7_candidate, mutation):
    registry = p7_candidate["candidate_registry"]
    if mutation == "overwrite":
        assets = (
            registry.assets[0].model_copy(update={"usage_license": "tampered"}),
            *registry.assets[1:],
        )
    else:
        assets = (*registry.assets, registry.assets[-1].model_copy(update={"asset_id": "extra"}))
    tampered = {
        **p7_candidate,
        "candidate_registry": registry.model_copy(update={"assets": assets}),
    }

    with pytest.raises(AiVideoError) as error:
        validate_image_activation_candidate(**tampered)

    assert error.value.code is ErrorCode.PRODUCTION_STATE_INVALID
