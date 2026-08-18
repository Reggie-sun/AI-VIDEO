from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.image_import import (
    HUMAN_IMAGE_IMPORT_TOOL,
    HumanImageImportReceipt,
    human_image_import_asset,
    prepare_human_image_import_commit,
    validate_human_image_import,
)
from ai_video.production.dependency import (
    build_production_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    ActorIdentity,
    ArtifactReference,
    AssetSourceKind,
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)
from ai_video.production.paths import (
    canonical_dependency_graph_snapshot_path,
    canonical_human_image_import_receipt_path,
    canonical_image_shot_revision_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    _canonical_json_bytes,
    _canonical_yaml_bytes,
    prepare_dependency_graph_transition,
    prepare_project_registry_commit,
)
import production_project_factory as project_factory


def _receipt(image_bytes: bytes, **overrides: object) -> HumanImageImportReceipt:
    values: dict[str, object] = {
        "declared_ui_product_label": "ChatGPT Images 2.0",
        "original_filename": "downloaded-image.png",
        "output_sha256": hashlib.sha256(image_bytes).hexdigest(),
        "output_size_bytes": len(image_bytes),
        "output_width": 2,
        "output_height": 1,
        "imported_at": "2026-08-18T10:00:00+08:00",
        "prompt_fingerprint": "1" * 64,
        "references": (),
        "target_kind": "key_shot",
        "target_artifact_id": "shot-artifact-1",
        "target_asset_role": "still",
        "human_actor": ActorIdentity(actor_id="human-operator", actor_kind="human"),
        "approved": True,
        "approved_at": "2026-08-18T10:01:00+08:00",
        "license_source_note": "Human supplied; ownership not inferred.",
    }
    values.update(overrides)
    return HumanImageImportReceipt.create(**values)


def test_human_import_receipt_is_truthful_sealed_and_builds_imported_asset() -> None:
    png = project_factory._p7_png()
    receipt = _receipt(png)

    validate_human_image_import(receipt, png)
    asset = human_image_import_asset(receipt)

    assert receipt.source_surface == "chatgpt_images_2_web"
    assert receipt.backend_model_id is None
    assert receipt.provider_request_id is None
    assert not receipt.durable_submit_intent_present
    assert not receipt.automated_browser
    assert asset.source_kind is AssetSourceKind.IMPORTED
    assert asset.tool == HUMAN_IMAGE_IMPORT_TOOL
    assert asset.creation_receipt_id == receipt.content_hash


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("backend_model_id", "invented-model"),
        ("provider_request_id", "invented-request"),
        ("durable_submit_intent_present", True),
        ("automated_browser", True),
        ("approved", False),
        ("license_source_note", ""),
        ("human_actor", ActorIdentity(actor_id="bot", actor_kind="automation")),
    ],
)
def test_human_import_receipt_rejects_invented_or_nonhuman_evidence(
    field: str,
    value: object,
) -> None:
    with pytest.raises((ValidationError, ValueError)):
        _receipt(project_factory._p7_png(), **{field: value})


def test_human_import_rejects_tampered_or_non_png_bytes() -> None:
    png = project_factory._p7_png()
    receipt = _receipt(png)

    with pytest.raises(AiVideoError) as tampered:
        validate_human_image_import(receipt, png + b"tampered")
    with pytest.raises(AiVideoError) as non_png:
        validate_human_image_import(receipt, b"not-png")

    assert tampered.value.code is ErrorCode.IMAGE_ASSET_INVALID
    assert non_png.value.code is ErrorCode.IMAGE_ASSET_INVALID


def test_human_import_original_filename_is_a_png_basename() -> None:
    png = project_factory._p7_png()
    with pytest.raises(ValidationError):
        _receipt(png, original_filename="../downloaded-image.png")
    with pytest.raises(ValidationError):
        _receipt(png, original_filename="downloaded-image.webp")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("imported_at", "2026-08-18T10:00:00"),
        ("approved_at", "not-a-timestamp"),
        ("approved_at", "2026-08-18T09:59:59+08:00"),
    ],
)
def test_human_import_requires_ordered_offset_timestamps(
    field: str, value: str
) -> None:
    with pytest.raises(ValidationError):
        _receipt(project_factory._p7_png(), **{field: value})


@pytest.mark.parametrize(
    "target_kind",
    ["character_master", "scene_reference", "key_shot", "repair_replacement"],
)
def test_human_import_reuses_atomic_project_registry_graph_commit_and_replays(
    tmp_path: Path,
    target_kind: str,
) -> None:
    project_factory.write_production_project(tmp_path)
    base_inputs = project_factory.make_p7_image_generation_base(tmp_path)
    base = load_production_project(tmp_path / "project.yaml")
    field = {
        "character_master": "characters",
        "scene_reference": "scenes",
        "key_shot": "shots",
        "repair_replacement": "shots",
    }[target_kind]
    base_target = getattr(base, field)[0]
    target_role = (
        base_target.required_asset_roles[0].role if field == "shots" else "reference"
    )
    png = project_factory._p7_png()
    receipt = _receipt(
        png,
        target_kind=target_kind,
        target_artifact_id=base_target.artifact_id,
        target_asset_role=target_role,
    )
    asset = human_image_import_asset(receipt)

    candidate_registry = base.registry.model_copy(
        update={
            "revision_id": "0" * 64,
            "content_hash": "0" * 64,
            "assets": (*base.registry.assets, asset),
        }
    )
    registry_hash = registry_semantic_sha256(candidate_registry)
    candidate_registry = candidate_registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    registry_payload = _canonical_json_bytes(candidate_registry)
    registry_pointer = RegistrySnapshotPointer(
        path=Path(f"assets/registry.{registry_hash}.json"),
        revision_id=registry_hash,
        content_hash=registry_hash,
        file_sha256=hashlib.sha256(registry_payload).hexdigest(),
    )

    target_update = {
        "revision": base_target.revision + 1,
        "content_hash": "0" * 64,
        "creation_receipt_id": receipt.content_hash,
    }
    if field == "characters":
        target_update["reference_asset_ids"] = (asset.asset_id,)
    elif field == "scenes":
        target_update["visual_reference_asset_ids"] = (asset.asset_id,)
    else:
        target_update["required_asset_roles"] = tuple(
            role.model_copy(update={"asset_ids": (asset.asset_id,)})
            if role.role == receipt.target_asset_role
            else role
            for role in base_target.required_asset_roles
        )
    candidate_target = seal_artifact(
        base_target.model_copy(
            update={
                **target_update,
            }
        )
    )
    target_path = (
        canonical_image_shot_revision_path(
            candidate_target.revision, candidate_target.content_hash
        )
        if field == "shots"
        else Path(
            f"creative/{field}/{candidate_target.artifact_id}."
            f"{candidate_target.revision}.{candidate_target.content_hash}.yaml"
        )
    )
    target_payload = _canonical_yaml_bytes(candidate_target)
    candidate_project = seal_artifact(
        base.project.model_copy(
            update={
                "revision": base.project.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": receipt.content_hash,
                "artifacts": base.project.artifacts.model_copy(
                    update={
                        field: tuple(
                            ArtifactReference(
                                artifact_id=candidate_target.artifact_id,
                                revision=candidate_target.revision,
                                content_hash=candidate_target.content_hash,
                                path=target_path,
                            )
                            if item.artifact_id == candidate_target.artifact_id
                            else item
                            for item in getattr(base.project.artifacts, field)
                        )
                    }
                ),
            }
        )
    )
    project_payload = _canonical_yaml_bytes(candidate_project)
    project_path = Path(
        f"state/projects/project.{candidate_project.revision}."
        f"{candidate_project.content_hash}.yaml"
    )
    project_pointer = ProjectSnapshotPointer(
        path=project_path,
        revision=candidate_project.revision,
        content_hash=candidate_project.content_hash,
        file_sha256=hashlib.sha256(project_payload).hexdigest(),
    )
    candidate_loaded = base.model_copy(
        update={
            "project": candidate_project,
            field: tuple(
                candidate_target
                if item.artifact_id == candidate_target.artifact_id
                else item
                for item in getattr(base, field)
            ),
            "registry": candidate_registry,
            "asset_paths": {
                **base.asset_paths,
                asset.asset_id: tmp_path / asset.artifact_path,
            },
            "manifest": base.manifest.model_copy(
                update={
                    "active_project": project_pointer,
                    "active_registry": registry_pointer,
                }
            ),
        }
    )
    candidate_inputs = replace(base_inputs, project=candidate_loaded)
    graph = build_production_dependency_graph(candidate_inputs)
    resolution = resolve_dependency_state(graph, base.manifest.dependency_states)
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=base.manifest.manifest_revision,
        base_dependency_graph=base.manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=resolution.states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    graph_payload = _canonical_json_bytes(graph)
    assert transition.candidate_dependency_graph == DependencyGraphSnapshotPointer(
        revision_id=graph.revision_id,
        content_hash=graph.content_hash,
        path=canonical_dependency_graph_snapshot_path(graph.revision_id),
        file_sha256=hashlib.sha256(graph_payload).hexdigest(),
    )
    base_commit = prepare_project_registry_commit(
        manifest=base.manifest,
        project=candidate_project,
        registry=candidate_registry,
        attempt_id="human-image-import-1",
    )
    base_commit = replace(
        base_commit,
        dependency_graph_transition=transition,
        artifacts=tuple(
            sorted(
                (
                    *base_commit.artifacts,
                    PreparedArtifact(
                        target_path,
                        target_payload,
                        hashlib.sha256(target_payload).hexdigest(),
                    ),
                    PreparedArtifact(
                        transition.candidate_dependency_graph.path,
                        graph_payload,
                        hashlib.sha256(graph_payload).hexdigest(),
                    ),
                ),
                key=lambda item: item.relative_path.as_posix(),
            )
        ),
    )
    request = prepare_human_image_import_commit(
        base=base,
        receipt=receipt,
        image_bytes=png,
        candidate_target=candidate_target,
        candidate_project=candidate_project,
        base_commit=base_commit,
    )

    final = ProductionStateCommitter(tmp_path).commit(request)
    loaded = load_production_project(tmp_path / "project.yaml")
    assert loaded.manifest == final
    assert loaded.registry.assets[-1] == asset
    assert getattr(loaded, field)[0] == candidate_target
    assert not any(item.operation == "image_generation" for item in final.attempts)
    assert final.attempts[-1].operation == "commit_project_registry"
    assert final.dependency_states == resolution.states

    decoy = receipt.model_copy(update={"content_hash": "f" * 64})
    decoy_path = tmp_path / canonical_human_image_import_receipt_path("f" * 64)
    decoy_path.parent.mkdir(parents=True, exist_ok=True)
    decoy_path.write_text(
        json.dumps(decoy.model_dump(mode="json"), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    assert load_production_project(tmp_path / "project.yaml").manifest == final

    class _NoWriteCommitter(ProductionStateCommitter):
        def _write_manifest_atomic(self, manifest, *, on_replace=None):
            raise AssertionError("exact import replay must not write")

    assert _NoWriteCommitter(tmp_path).commit(request) == final
