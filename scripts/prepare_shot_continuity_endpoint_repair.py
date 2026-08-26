#!/usr/bin/env python3
"""Prepare a fresh rainy-station P0 bundle with one approved A3 repair."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ai_video.production.hashing import seal_artifact
from ai_video.production.image_import import (
    AUTOMATED_BROWSER_IMAGE_IMPORT_TOOL,
    CODEX_IMAGEGEN_IMPORT_TOOL,
    HUMAN_IMAGE_IMPORT_TOOL,
    AutomatedBrowserImageImportReceipt,
    HumanImageImportReceipt,
    ShotEndpointImageImportReferenceBinding,
    human_image_import_asset,
    prepare_human_image_import_commit,
)
from ai_video.production.models import (
    ActorIdentity,
    ArtifactReference,
    AssetRegistrySnapshot,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    canonical_project_snapshot_path,
    canonical_registry_snapshot_path,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_automated_browser_image_import_receipt_path,
    canonical_dependency_graph_snapshot_path,
    canonical_human_image_import_receipt_path,
    canonical_image_shot_revision_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.shot_continuity_source_runtime import (
    bootstrap_source_dependency_graph,
    build_source_closure,
    build_source_dependency_transition,
)
from ai_video.production.shot_continuity_m0_policy import M0ValidationPolicyId
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    _canonical_json_bytes,
    _canonical_yaml_bytes,
    prepare_project_registry_commit,
)
from scripts.prepare_shot_continuity_p0 import _record_p0


TARGET_SHOT_ARTIFACT_ID = "shot-rainy-station-3"
TARGET_ASSET_ROLE = "approved_endpoint"
SOURCE_WIDTH = 1659
SOURCE_HEIGHT = 948
EXPECTED_SHOT_ARTIFACT_IDS = tuple(
    f"shot-rainy-station-{index}" for index in range(1, 5)
)
SOURCE_REFERENCE_SHOT_ARTIFACT_IDS = (
    "shot-rainy-station-2",
    TARGET_SHOT_ARTIFACT_ID,
)


def _artifact(root: Path, relative_path: Path) -> PreparedArtifact:
    snapshot = _read_regular_file_nofollow(
        root / relative_path,
        contained_by=root,
    )
    return PreparedArtifact(
        relative_path=relative_path,
        payload=snapshot.data,
        file_sha256=hashlib.sha256(snapshot.data).hexdigest(),
    )


def _bootstrap_paths(bundle, root: Path) -> tuple[Path, ...]:
    paths = {
        bundle.project.artifacts.brief.path,
        bundle.project.artifacts.story.path,
        bundle.project.artifacts.storyboard.path,
        *(item.path for item in bundle.project.artifacts.characters),
        *(item.path for item in bundle.project.artifacts.scenes),
        *(item.path for item in bundle.project.artifacts.shots),
        *(item.artifact_path for item in bundle.registry.assets),
    }
    for asset in bundle.registry.assets:
        if asset.tool == AUTOMATED_BROWSER_IMAGE_IMPORT_TOOL:
            paths.add(
                canonical_automated_browser_image_import_receipt_path(
                    asset.creation_receipt_id
                )
            )
        elif asset.tool in {HUMAN_IMAGE_IMPORT_TOOL, CODEX_IMAGEGEN_IMPORT_TOOL}:
            paths.add(
                canonical_human_image_import_receipt_path(
                    asset.creation_receipt_id
                )
            )
        if asset.tool in {
            AUTOMATED_BROWSER_IMAGE_IMPORT_TOOL,
            HUMAN_IMAGE_IMPORT_TOOL,
            CODEX_IMAGEGEN_IMPORT_TOOL,
        }:
            receipt = _receipt_for_asset(root, asset)
            paths.update(
                reference.creative_artifact_path
                for reference in receipt.references
                if isinstance(
                    reference, ShotEndpointImageImportReferenceBinding
                )
            )
    return tuple(sorted(paths, key=Path.as_posix))


def _candidate_bytes(path: Path) -> tuple[bytes, int, int]:
    resolved = path.resolve(strict=True)
    payload = resolved.read_bytes()
    with Image.open(resolved) as image:
        image.load()
        width, height = image.size
        mode = image.mode
    if (width, height, mode) != (SOURCE_WIDTH, SOURCE_HEIGHT, "RGB"):
        raise ValueError(
            f"A3 repair must be RGB {SOURCE_WIDTH}x{SOURCE_HEIGHT}, got "
            f"{width}x{height} {mode}"
        )
    return payload, width, height


def _pointer_project(project) -> ProjectSnapshotPointer:
    payload = _canonical_yaml_bytes(project)
    return ProjectSnapshotPointer(
        path=canonical_project_snapshot_path(project.revision, project.content_hash),
        revision=project.revision,
        content_hash=project.content_hash,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )


def _pointer_registry(registry) -> RegistrySnapshotPointer:
    payload = _canonical_json_bytes(registry)
    return RegistrySnapshotPointer(
        path=canonical_registry_snapshot_path(registry.revision_id),
        revision_id=registry.revision_id,
        content_hash=registry.content_hash,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )


def _receipt_for_asset(root: Path, asset):
    if asset.tool == AUTOMATED_BROWSER_IMAGE_IMPORT_TOOL:
        path = canonical_automated_browser_image_import_receipt_path(
            asset.creation_receipt_id
        )
        model = AutomatedBrowserImageImportReceipt
    elif asset.tool in {HUMAN_IMAGE_IMPORT_TOOL, CODEX_IMAGEGEN_IMPORT_TOOL}:
        path = canonical_human_image_import_receipt_path(asset.creation_receipt_id)
        model = HumanImageImportReceipt
    else:
        raise ValueError(f"unsupported endpoint import tool: {asset.tool.name}")
    snapshot = _read_regular_file_nofollow(root / path, contained_by=root)
    value = json.loads(snapshot.data)
    receipt = model.model_validate(value)
    if snapshot.data != _canonical_json_bytes(receipt):
        raise ValueError("endpoint import receipt is not canonical JSON")
    return receipt


def _shot_endpoint_reference(bundle, shot) -> ShotEndpointImageImportReferenceBinding:
    artifact_reference = next(
        (
            item
            for item in bundle.project.artifacts.shots
            if item.artifact_id == shot.artifact_id
        ),
        None,
    )
    if artifact_reference is None:
        raise ValueError(f"source Shot {shot.artifact_id} artifact is absent")
    endpoint_role = next(
        (
            role
            for role in shot.required_asset_roles
            if role.role == TARGET_ASSET_ROLE
        ),
        None,
    )
    if endpoint_role is None or len(endpoint_role.asset_ids) != 1:
        raise ValueError(
            f"source Shot {shot.artifact_id} must select one {TARGET_ASSET_ROLE}"
        )
    asset = next(
        (
            item
            for item in bundle.registry.assets
            if item.asset_id == endpoint_role.asset_ids[0]
        ),
        None,
    )
    if asset is None:
        raise ValueError(f"source Shot {shot.artifact_id} endpoint asset is absent")
    return ShotEndpointImageImportReferenceBinding(
        role="shot_endpoint",
        creative_artifact_id=shot.artifact_id,
        creative_revision=shot.revision,
        creative_content_hash=shot.content_hash,
        creative_artifact_path=artifact_reference.path,
        asset_role=TARGET_ASSET_ROLE,
        asset_id=asset.asset_id,
        asset_sha256=asset.sha256,
    )


def prepare(args: argparse.Namespace) -> dict[str, object]:
    source_root = args.source_root.resolve(strict=True)
    root = args.root.resolve()
    if source_root == root or source_root in root.parents:
        raise ValueError("target root must be distinct from and outside the source root")
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"target root must be absent or empty: {root}")
    if len(args.prompt_fingerprint) != 64 or any(
        character not in "0123456789abcdef" for character in args.prompt_fingerprint
    ):
        raise ValueError("prompt fingerprint must be lowercase SHA-256")

    candidate_path = args.a3.resolve(strict=True)
    candidate_bytes, width, height = _candidate_bytes(candidate_path)
    source = load_production_project(source_root / "project.yaml")
    if source.project.project_id != "rainy-station-continuity-p0":
        raise ValueError("source root is not the rainy-station P0 project")
    source_shots_by_id = {item.artifact_id: item for item in source.shots}
    if tuple(source_shots_by_id) != EXPECTED_SHOT_ARTIFACT_IDS:
        raise ValueError(
            "source bundle does not contain the ordered rainy-station four-Shot closure"
        )

    receipt = HumanImageImportReceipt.create(
        source_surface="codex_imagegen_tool",
        declared_ui_product_label="OpenAI imagegen",
        original_filename=candidate_path.name,
        output_sha256=hashlib.sha256(candidate_bytes).hexdigest(),
        output_size_bytes=len(candidate_bytes),
        output_width=width,
        output_height=height,
        imported_at=args.imported_at,
        prompt_fingerprint=args.prompt_fingerprint,
        references=tuple(
            _shot_endpoint_reference(source, source_shots_by_id[artifact_id])
            for artifact_id in SOURCE_REFERENCE_SHOT_ARTIFACT_IDS
        ),
        target_kind="repair_replacement",
        target_artifact_id=TARGET_SHOT_ARTIFACT_ID,
        target_asset_role=TARGET_ASSET_ROLE,
        human_actor=ActorIdentity(
            actor_id="user-shot-continuity-owner",
            actor_kind="human",
        ),
        approved=True,
        approved_at=args.approved_at,
        license_source_note=(
            "User-approved OpenAI imagegen endpoint candidate; ownership and "
            "downstream usage rights are not inferred."
        ),
    )

    root.mkdir(parents=True, exist_ok=True)
    writer = ProductionStateCommitter(root)
    writer.bootstrap_initial_state(
        attempt_id="rainy-station-endpoint-repair-bootstrap-v1",
        project=source.project,
        registry=source.registry,
        artifacts=tuple(
            _artifact(source_root, path)
            for path in _bootstrap_paths(source, source_root)
        ),
    )
    base = load_production_project(root / "project.yaml")
    bootstrap_source_dependency_graph(
        writer,
        base,
        attempt_id="rainy-station-source-dependency-graph-base-clone-v1",
    )
    base = load_production_project(root / "project.yaml")

    base_target = next(
        item for item in base.shots if item.artifact_id == TARGET_SHOT_ARTIFACT_ID
    )
    roles = tuple(
        role.model_copy(update={"asset_ids": (human_image_import_asset(receipt).asset_id,)})
        if role.role == TARGET_ASSET_ROLE
        else role
        for role in base_target.required_asset_roles
    )
    if roles == base_target.required_asset_roles:
        raise ValueError("target Shot has no approved_endpoint role")
    asset = human_image_import_asset(receipt)
    candidate_target = seal_artifact(
        base_target.model_copy(
            update={
                "revision": base_target.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": receipt.content_hash,
                "required_asset_roles": roles,
            }
        )
    )
    target_path = canonical_image_shot_revision_path(
        candidate_target.revision, candidate_target.content_hash
    )
    candidate_registry = AssetRegistrySnapshot(
        revision_id="0" * 64,
        content_hash="0" * 64,
        assets=(*base.registry.assets, asset),
    )
    registry_hash = registry_semantic_sha256(candidate_registry)
    candidate_registry = candidate_registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    candidate_project = seal_artifact(
        base.project.model_copy(
            update={
                "revision": base.project.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": receipt.content_hash,
                "artifacts": base.project.artifacts.model_copy(
                    update={
                        "shots": tuple(
                            ArtifactReference(
                                artifact_id=candidate_target.artifact_id,
                                revision=candidate_target.revision,
                                content_hash=candidate_target.content_hash,
                                path=target_path,
                            )
                            if item.artifact_id == candidate_target.artifact_id
                            else item
                            for item in base.project.artifacts.shots
                        )
                    }
                ),
            }
        )
    )
    candidate_loaded = base.model_copy(
        update={
            "project": candidate_project,
            "shots": tuple(
                candidate_target if item.artifact_id == candidate_target.artifact_id else item
                for item in base.shots
            ),
            "registry": candidate_registry,
            "asset_paths": {**base.asset_paths, asset.asset_id: candidate_path},
            "manifest": base.manifest.model_copy(
                update={
                    "active_project": _pointer_project(candidate_project),
                    "active_registry": _pointer_registry(candidate_registry),
                }
            ),
        }
    )
    closure = build_source_closure(candidate_loaded)
    transition = build_source_dependency_transition(
        committer=writer,
        project=base,
        graph=closure.graph,
        desired=closure.desired_fingerprints,
    )
    graph_payload = _canonical_json_bytes(closure.graph)
    if transition.candidate_dependency_graph.path != canonical_dependency_graph_snapshot_path(
        closure.graph.revision_id
    ):
        raise ValueError("candidate dependency graph path is not canonical")
    base_commit = prepare_project_registry_commit(
        manifest=base.manifest,
        project=candidate_project,
        registry=candidate_registry,
        attempt_id="rainy-station-a3-motion-endpoint-import-v1",
    )
    base_commit = replace(
        base_commit,
        dependency_graph_transition=transition,
        artifacts=tuple(
            sorted(
                (
                    *base_commit.artifacts,
                    PreparedArtifact(
                        relative_path=target_path,
                        payload=_canonical_yaml_bytes(candidate_target),
                        file_sha256=hashlib.sha256(
                            _canonical_yaml_bytes(candidate_target)
                        ).hexdigest(),
                    ),
                    PreparedArtifact(
                        relative_path=transition.candidate_dependency_graph.path,
                        payload=graph_payload,
                        file_sha256=hashlib.sha256(graph_payload).hexdigest(),
                    ),
                ),
                key=lambda item: item.relative_path.as_posix(),
            )
        ),
    )
    writer.commit(
        prepare_human_image_import_commit(
            base=base,
            receipt=receipt,
            image_bytes=candidate_bytes,
            candidate_target=candidate_target,
            candidate_project=candidate_project,
            base_commit=base_commit,
        )
    )
    repaired = load_production_project(root / "project.yaml")
    assets_by_id = {item.asset_id: item for item in repaired.registry.assets}
    shot_assets = tuple(
        assets_by_id[shot.required_asset_roles[0].asset_ids[0]]
        for shot in repaired.shots
    )
    shot_receipts = tuple(
        _receipt_for_asset(root, endpoint_asset) for endpoint_asset in shot_assets
    )
    manifest, p0, validation_set, source_stack, m0, m1, inputs = _record_p0(
        root=root,
        shot_assets=shot_assets,
        shot_receipts=shot_receipts,
        approved_at=args.approved_at,
        m0_policy_id=args.m0_policy,
    )
    return {
        "root": root.as_posix(),
        "manifest_schema_version": manifest.schema_version,
        "manifest_revision": manifest.manifest_revision,
        "project_content_hash": repaired.project.content_hash,
        "registry_content_hash": repaired.registry.content_hash,
        "a3_asset_id": asset.asset_id,
        "a3_sha256": asset.sha256,
        "a3_import_receipt_hash": receipt.content_hash,
        "p0_receipt_hash": p0.content_hash,
        "validation_set_hash": validation_set.content_hash,
        "source_execution_stack_hash": source_stack.execution_stack_hash,
        "m0_execution_stack_hash": m0.execution_stack_hash,
        "m0_validation_policy_id": args.m0_policy.value,
        "m1_execution_stack_hash": m1.execution_stack_hash,
        "qualification_input_hashes": {
            item.input_kind: item.content_hash for item in inputs
        },
        "claims": {
            "video_generated": False,
            "winner_selected": False,
            "p6_pass": False,
            "final_acceptance": False,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--a3", type=Path, required=True)
    parser.add_argument("--prompt-fingerprint", required=True)
    parser.add_argument("--imported-at", required=True)
    parser.add_argument("--approved-at", required=True)
    parser.add_argument(
        "--m0-policy",
        type=M0ValidationPolicyId,
        choices=tuple(M0ValidationPolicyId),
        required=True,
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    for value in (args.imported_at, args.approved_at):
        timestamp = datetime.fromisoformat(value)
        if timestamp.tzinfo is None:
            raise ValueError("timestamps require explicit offsets")
    print(json.dumps(prepare(args), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
