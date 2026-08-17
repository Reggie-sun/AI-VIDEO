from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.dependency import dependency_graph_semantic_sha256
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.image import (
    ImageGenerationAuthorization,
    ImageGenerationRequest,
    ImageProvenanceReceipt,
    ImageProviderResult,
    _measure_png,
    validate_image_result,
)
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    Character,
    DependencyGraphSnapshot,
    LoadedProductionProject,
    ProductionProject,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    Scene,
    Shot,
    StateCommitAttempt,
    StateCommitStatus,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_dependency_graph_snapshot_path,
    canonical_image_asset_path,
    canonical_image_receipt_path,
    canonical_image_request_path,
    canonical_image_result_path,
    canonical_image_shot_revision_path,
)
from ai_video.production.registry import registry_semantic_sha256


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _read_canonical_json(
    root: Path,
    path: Path,
    *,
    label: str,
) -> tuple[dict[str, object], str]:
    snapshot = _read_regular_file_nofollow(root / path, contained_by=root)
    value = json.loads(snapshot.data)
    if not isinstance(value, dict) or snapshot.data != _canonical_json_bytes(value):
        raise ValueError(f"{label} is not canonical JSON")
    return value, snapshot.file_sha256


def _read_candidate_project(
    bundle: LoadedProductionProject,
    attempt: StateCommitAttempt,
) -> tuple[ProductionProject, str]:
    pointer = attempt.candidate_project
    if pointer is None:
        raise ValueError("image candidate project pointer is missing")
    snapshot = _read_regular_file_nofollow(
        bundle.root / pointer.path,
        contained_by=bundle.root / "state/projects",
    )
    if snapshot.file_sha256 != pointer.file_sha256:
        raise ValueError("image candidate project file hash mismatch")
    project = ProductionProject.model_validate(
        yaml.safe_load(snapshot.data.decode("utf-8"))
    )
    if (
        project.project_id != bundle.manifest.project_id
        or project.revision != pointer.revision
        or project.content_hash != pointer.content_hash
        or not verify_artifact_hash(project)
    ):
        raise ValueError("image candidate project identity mismatch")
    return project, snapshot.file_sha256


def _read_base_project(
    bundle: LoadedProductionProject,
    attempt: StateCommitAttempt,
) -> ProductionProject:
    pointer = attempt.base_project
    if pointer is None:
        raise ValueError("image base project pointer is missing")
    return _read_project_pointer(bundle, pointer, label="base")[0]


def _read_project_pointer(
    bundle: LoadedProductionProject,
    pointer: ProjectSnapshotPointer,
    *,
    label: str,
) -> tuple[ProductionProject, str]:
    snapshot = _read_regular_file_nofollow(
        bundle.root / pointer.path,
        contained_by=bundle.root,
    )
    if snapshot.file_sha256 != pointer.file_sha256:
        raise ValueError(f"image {label} project file hash mismatch")
    project = ProductionProject.model_validate(
        yaml.safe_load(snapshot.data.decode("utf-8"))
    )
    if (
        project.project_id != bundle.manifest.project_id
        or project.revision != pointer.revision
        or project.content_hash != pointer.content_hash
        or not verify_artifact_hash(project)
    ):
        raise ValueError(f"image {label} project identity mismatch")
    return project, snapshot.file_sha256


def _read_candidate_registry(
    bundle: LoadedProductionProject,
    attempt: StateCommitAttempt,
) -> tuple[AssetRegistrySnapshot, str]:
    pointer = attempt.candidate_registry
    if pointer is None:
        raise ValueError("image candidate Registry pointer is missing")
    return _read_registry_pointer(bundle, pointer, label="candidate")


def _read_base_registry(
    bundle: LoadedProductionProject,
    attempt: StateCommitAttempt,
) -> AssetRegistrySnapshot:
    pointer = attempt.base_registry
    if pointer is None:
        raise ValueError("image base Registry pointer is missing")
    return _read_registry_pointer(bundle, pointer, label="base")[0]


def _read_registry_pointer(
    bundle: LoadedProductionProject,
    pointer: RegistrySnapshotPointer,
    *,
    label: str,
) -> tuple[AssetRegistrySnapshot, str]:
    snapshot = _read_regular_file_nofollow(
        bundle.root / pointer.path, contained_by=bundle.root / "assets"
    )
    if snapshot.file_sha256 != pointer.file_sha256:
        raise ValueError(f"image {label} Registry file hash mismatch")
    registry = AssetRegistrySnapshot.model_validate_json(snapshot.data)
    if (
        registry.revision_id != pointer.revision_id
        or registry.content_hash != pointer.content_hash
        or registry_semantic_sha256(registry) != pointer.content_hash
    ):
        raise ValueError(f"image {label} Registry identity mismatch")
    return registry, snapshot.file_sha256


def _read_candidate_graph(
    bundle: LoadedProductionProject,
    attempt: StateCommitAttempt,
) -> tuple[DependencyGraphSnapshot, str]:
    pointer = attempt.candidate_dependency_graph
    if pointer is None or pointer.path != canonical_dependency_graph_snapshot_path(
        pointer.revision_id
    ):
        raise ValueError("image candidate dependency graph pointer is invalid")
    snapshot = _read_regular_file_nofollow(
        bundle.root / pointer.path,
        contained_by=bundle.root / "state",
    )
    if snapshot.file_sha256 != pointer.file_sha256:
        raise ValueError("image candidate dependency graph file hash mismatch")
    graph = DependencyGraphSnapshot.model_validate_json(snapshot.data)
    if (
        graph.revision_id != pointer.revision_id
        or graph.content_hash != pointer.content_hash
        or dependency_graph_semantic_sha256(graph) != pointer.content_hash
    ):
        raise ValueError("image candidate dependency graph identity mismatch")
    return graph, snapshot.file_sha256


def _read_creative_reference(
    bundle: LoadedProductionProject,
    project: ProductionProject,
    *,
    artifact_id: str,
    role: str,
) -> Character | Scene:
    if role not in {"character", "scene"}:
        raise ValueError(f"unsupported image reference role: {role}")
    references = (
        project.artifacts.characters if role == "character" else project.artifacts.scenes
    )
    reference = next(
        (item for item in references if item.artifact_id == artifact_id), None
    )
    if reference is None:
        raise ValueError(f"image {role} reference is absent from the base project")
    snapshot = _read_regular_file_nofollow(
        bundle.root / reference.path,
        contained_by=bundle.root,
    )
    model_type = Character if role == "character" else Scene
    artifact = model_type.model_validate(yaml.safe_load(snapshot.data.decode("utf-8")))
    if (
        artifact.artifact_id != reference.artifact_id
        or artifact.revision != reference.revision
        or artifact.content_hash != reference.content_hash
        or not verify_artifact_hash(artifact)
    ):
        raise ValueError(f"image {role} reference identity mismatch")
    return artifact


def _verify_reference_bindings(
    bundle: LoadedProductionProject,
    request: ImageGenerationRequest,
    base_project: ProductionProject,
    base_registry: AssetRegistrySnapshot,
) -> None:
    assets = {item.asset_id: item for item in base_registry.assets}
    for binding in request.references:
        artifact = _read_creative_reference(
            bundle,
            base_project,
            artifact_id=binding.creative_artifact_id,
            role=binding.role,
        )
        memberships = (
            artifact.reference_asset_ids
            if isinstance(artifact, Character)
            else artifact.visual_reference_asset_ids
        )
        asset = assets.get(binding.asset_id)
        if (
            binding.creative_revision != artifact.revision
            or binding.creative_content_hash != artifact.content_hash
            or binding.asset_id not in memberships
            or asset is None
            or binding.asset_sha256 != asset.sha256
        ):
            raise ValueError(
                f"image {binding.role} reference is not bound to the base project"
            )


def _read_candidate_shot(
    bundle: LoadedProductionProject,
    project: ProductionProject,
    request: ImageGenerationRequest,
) -> tuple[Shot, Path, str]:
    active_shot = next(
        (item for item in bundle.shots if item.shot_id == request.target_shot_id),
        None,
    )
    reference = next(
        (
            item
            for item in project.artifacts.shots
            if active_shot is not None and item.artifact_id == active_shot.artifact_id
        ),
        None,
    )
    if reference is None:
        raise ValueError("image target Shot is absent from the candidate project")
    if reference.path != canonical_image_shot_revision_path(
        reference.revision, reference.content_hash
    ):
        raise ValueError("image candidate Shot path is not canonical")
    snapshot = _read_regular_file_nofollow(
        bundle.root / reference.path,
        contained_by=bundle.root,
    )
    shot = Shot.model_validate(yaml.safe_load(snapshot.data.decode("utf-8")))
    if (
        shot.artifact_id != reference.artifact_id
        or shot.revision != reference.revision
        or shot.content_hash != reference.content_hash
        or not verify_artifact_hash(shot)
    ):
        raise ValueError("image candidate Shot identity mismatch")
    return shot, reference.path, snapshot.file_sha256


def _attempt_summary_matches_request(
    attempt: StateCommitAttempt,
    request: ImageGenerationRequest,
) -> bool:
    summary = attempt.image_request
    return summary is not None and summary.model_dump(mode="json") == {
        "request_id": request.request_id,
        "attempt_id": request.attempt_id,
        "request_fingerprint": request.request_fingerprint,
        "provider_kind": request.provider_kind,
        "model_id": request.model_id,
        "target_shot_id": request.target_shot_id,
        "target_asset_role": request.target_asset_role,
        "output_asset_id": request.output_asset_id,
        "preview_fingerprint": summary.preview_fingerprint,
        "authorization_fingerprint": summary.authorization_fingerprint,
        "policy_receipt_id": summary.policy_receipt_id,
        "usage_license": summary.usage_license,
    }


def _result_fingerprint(
    receipt: ImageProvenanceReceipt,
    attempt: StateCommitAttempt,
) -> str:
    summary = attempt.image_request
    if summary is None:
        raise ValueError("image attempt request summary is missing")
    return canonical_sha256(
        ImageProviderResult._fingerprint_payload(
            {
                "request_id": receipt.request_id,
                "request_fingerprint": receipt.request_fingerprint,
                "image_sha256": receipt.output_sha256,
                "content_type": receipt.output_mime_type,
                "provider_request_id": receipt.provider_request_id,
                "adapter": receipt.adapter.model_dump(mode="json"),
                "resource_evidence": receipt.resource_evidence.model_dump(mode="json"),
                "preview_fingerprint": summary.preview_fingerprint,
                "authorization_fingerprint": summary.authorization_fingerprint,
                "terminal_status": "succeeded",
            }
        )
    )


def _verify_evidence(
    bundle: LoadedProductionProject,
    attempt: StateCommitAttempt,
    asset: AssetRecord,
    candidate_project: ProductionProject,
    base_project: ProductionProject,
    base_registry: AssetRegistrySnapshot,
) -> tuple[tuple[Path, str], ...]:
    summary = attempt.image_request
    if summary is None:
        raise ValueError("image attempt request summary is missing")
    request_path = canonical_image_request_path(summary.request_fingerprint)
    request_value, request_sha256 = _read_canonical_json(
        bundle.root, request_path, label="image request"
    )
    request = ImageGenerationRequest.model_validate(request_value)
    if not _attempt_summary_matches_request(attempt, request):
        raise ValueError("image request does not match its selected attempt")
    if (
        request.base_project != attempt.base_project
        or request.base_registry != attempt.base_registry
        or request.base_dependency_graph != attempt.base_dependency_graph
    ):
        raise ValueError("image request base pointers do not match its attempt")
    _verify_reference_bindings(bundle, request, base_project, base_registry)

    receipt_path = canonical_image_receipt_path(asset.creation_receipt_id)
    receipt_value, receipt_sha256 = _read_canonical_json(
        bundle.root, receipt_path, label="image receipt"
    )
    receipt = ImageProvenanceReceipt.model_validate(receipt_value)
    if receipt.content_hash != asset.creation_receipt_id:
        raise ValueError("image receipt identity does not match the Registry")

    if asset.artifact_path != canonical_image_asset_path(asset.sha256):
        raise ValueError("generated image asset path is noncanonical")
    image_snapshot = _read_regular_file_nofollow(
        bundle.root / asset.artifact_path,
        contained_by=bundle.root / "assets/files",
    )
    measured = _measure_png(image_snapshot.data)
    if (
        image_snapshot.file_sha256 != asset.sha256
        or image_snapshot.size_bytes != asset.size_bytes
        or measured.sha256 != asset.sha256
        or measured.size_bytes != asset.size_bytes
        or measured.mime_type != asset.mime_type
        or measured.width != asset.width
        or measured.height != asset.height
    ):
        raise ValueError("generated PNG bytes do not match the Registry")

    result_path = canonical_image_result_path(_result_fingerprint(receipt, attempt))
    result_value, result_sha256 = _read_canonical_json(
        bundle.root, result_path, label="image provider result"
    )
    if "image_bytes" in result_value:
        raise ValueError("durable image result must store metadata only")
    result = ImageProviderResult.model_validate(
        {**result_value, "image_bytes": image_snapshot.data}
    )
    authorization = ImageGenerationAuthorization(
        request_fingerprint=summary.request_fingerprint,
        preview_fingerprint=summary.preview_fingerprint,
        provider_enabled=True,
        local_only=True,
        usage_license=summary.usage_license,
        policy_receipt_id=summary.policy_receipt_id,
        authorization_fingerprint=summary.authorization_fingerprint,
    )
    checked_measured, checked_receipt = validate_image_result(
        request, authorization, result
    )
    if checked_measured != measured or checked_receipt != receipt:
        raise ValueError("image request, result and receipt are not exact")

    candidate_shot, shot_path, shot_sha256 = _read_candidate_shot(
        bundle, candidate_project, request
    )

    shot = next(
        (item for item in bundle.shots if item.shot_id == request.target_shot_id),
        None,
    )
    roles = (
        tuple(
            item
            for item in shot.required_asset_roles
            if item.role == request.target_asset_role
        )
        if shot is not None
        else ()
    )
    selected_roles = tuple(
        (item.shot_id, role.role)
        for item in bundle.shots
        for role in item.required_asset_roles
        if asset.asset_id in role.asset_ids
    )
    expected_inputs = (
        shot.artifact_id if shot is not None else "",
        *(
            identity
            for item in request.references
            for identity in (item.creative_artifact_id, item.asset_id)
        ),
    )
    if (
        shot is None
        or len(roles) != 1
        or roles[0].asset_ids != (asset.asset_id,)
        or selected_roles != ((request.target_shot_id, request.target_asset_role),)
        or shot.creation_receipt_id != receipt.content_hash
        or candidate_shot.creation_receipt_id != receipt.content_hash
        or receipt.request_id != request.request_id
        or receipt.request_fingerprint != request.request_fingerprint
        or receipt.target_shot_id != request.target_shot_id
        or receipt.target_asset_role != request.target_asset_role
        or receipt.output_asset_id != asset.asset_id
        or receipt.references != request.references
        or receipt.provider_request_id != attempt.provider_request_id
        or asset.asset_type is not AssetType.IMAGE
        or asset.source_kind is not AssetSourceKind.GENERATED
        or asset.tool != receipt.adapter
        or asset.input_artifact_ids != expected_inputs
        or asset.input_fingerprint != request.request_fingerprint
        or asset.usage_license != receipt.usage_license
        or asset.egress.remote
        or asset.cost_receipt_id is not None
    ):
        raise ValueError("active generated image provenance is inconsistent")
    return (
        (request_path, request_sha256),
        (result_path, result_sha256),
        (receipt_path, receipt_sha256),
        (asset.artifact_path, image_snapshot.file_sha256),
        (shot_path, shot_sha256),
    )


def _verify_candidate_artifacts_hash(
    attempt: StateCommitAttempt,
    pairs: tuple[tuple[Path, str], ...],
) -> None:
    normalized = sorted((path.as_posix(), digest) for path, digest in pairs)
    if len(normalized) != 8 or len({path for path, _ in normalized}) != 8:
        raise ValueError("image candidate artifact set is not exact")
    actual = hashlib.sha256(
        json.dumps(normalized, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if actual != attempt.candidate_artifacts_hash:
        raise ValueError("image candidate artifact hash mismatch")


def verify_active_image_evidence(bundle: LoadedProductionProject) -> None:
    if bundle.manifest.schema_version != "2.5":
        return
    attempts = tuple(
        item
        for item in bundle.manifest.attempts
        if item.operation == "image_generation"
        and item.status is StateCommitStatus.SUCCEEDED
        and item.image_phase == "activate"
    )
    assets_by_id = {item.asset_id: item for item in bundle.registry.assets}
    active_asset_ids = {
        asset_id
        for shot in bundle.shots
        for role in shot.required_asset_roles
        for asset_id in role.asset_ids
        if (
            (asset := assets_by_id.get(asset_id)) is not None
            and asset.asset_type is AssetType.IMAGE
            and asset.source_kind is AssetSourceKind.GENERATED
        )
    }
    selected: dict[str, StateCommitAttempt] = {}
    for attempt in attempts:
        for asset_id in attempt.candidate_image_asset_ids:
            if asset_id in active_asset_ids:
                if asset_id in selected:
                    raise _invalid(
                        "Active generated image is claimed by multiple P7 attempts."
                    )
                selected[asset_id] = attempt
    if set(selected) != active_asset_ids:
        raise _invalid(
            "Active generated images do not match succeeded P7 attempts."
        )
    try:
        for asset_id, attempt in selected.items():
            candidate_project, project_sha256 = _read_candidate_project(bundle, attempt)
            candidate_registry, registry_sha256 = _read_candidate_registry(
                bundle, attempt
            )
            _, graph_sha256 = _read_candidate_graph(bundle, attempt)
            base_project = _read_base_project(bundle, attempt)
            base_registry = _read_base_registry(bundle, attempt)
            asset = assets_by_id[asset_id]
            if (
                attempt.candidate_image_asset_ids != (asset_id,)
                or len(candidate_registry.assets) != len(base_registry.assets) + 1
                or candidate_registry.assets[:-1] != base_registry.assets
                or candidate_registry.assets[-1] != asset
                or bundle.registry.assets[: len(candidate_registry.assets)]
                != candidate_registry.assets
                or candidate_project.creation_receipt_id != asset.creation_receipt_id
            ):
                raise ValueError("selected image candidate history is not retained")
            evidence_pairs = _verify_evidence(
                bundle,
                attempt,
                asset,
                candidate_project,
                base_project,
                base_registry,
            )
            _verify_candidate_artifacts_hash(
                attempt,
                (
                    *evidence_pairs,
                    (attempt.candidate_project.path, project_sha256),
                    (attempt.candidate_registry.path, registry_sha256),
                    (attempt.candidate_dependency_graph.path, graph_sha256),
                ),
            )

        if selected:
            latest = max(selected.values(), key=lambda item: item.base_manifest_revision)
            if (
                latest.candidate_project != bundle.manifest.active_project
                or latest.candidate_registry != bundle.manifest.active_registry
            ):
                raise ValueError("latest selected image candidate is not active")
            states_payload = json.dumps(
                [
                    item.model_dump(mode="json")
                    for item in bundle.manifest.dependency_states
                ],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            if (
                latest.candidate_dependency_graph
                == bundle.manifest.active_dependency_graph
                and latest.candidate_dependency_states_hash
                != hashlib.sha256(states_payload).hexdigest()
            ):
                raise ValueError("active image dependency state hash mismatch")
    except (AiVideoError, OSError, UnicodeError, ValidationError, ValueError) as exc:
        detail = exc.technical_detail if isinstance(exc, AiVideoError) else str(exc)
        raise _invalid(
            "Active P7 image candidate history or reference provenance is invalid.",
            detail,
        ) from exc
