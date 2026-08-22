from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.comfy_image import LocalImageExecutionProfile
from ai_video.production.dependency import dependency_graph_semantic_sha256
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.image import (
    ContinuityTerminalImageReferenceBinding,
    ImageGenerationAuthorization,
    ImageGenerationPreview,
    ImageGenerationRequest,
    ImageProvenanceReceipt,
    ImageProviderResult,
    _measure_png,
    _reference_graph_input_ids,
    _validate_continuity_terminal_reference,
    validate_image_result,
)
from ai_video.production.image_import import (
    HUMAN_IMAGE_IMPORT_TOOL,
    HumanImageImportReceipt,
    human_image_import_asset,
    validate_human_image_import,
)
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    Character,
    DependencyGraphSnapshot,
    LoadedProductionProject,
    ProductionManifest,
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
    canonical_image_authorization_path,
    canonical_image_execution_profile_path,
    canonical_human_image_import_receipt_path,
    canonical_image_preview_path,
    canonical_image_receipt_path,
    canonical_image_request_path,
    canonical_image_result_path,
    canonical_image_shot_revision_path,
    canonical_image_submit_intent_path,
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
        if isinstance(binding, ContinuityTerminalImageReferenceBinding):
            from ai_video.production._video_project_reader import (
                load_terminal_frame_evidence,
                load_video_request_receipt,
            )

            _validate_continuity_terminal_reference(
                binding, bundle, validate_target=False
            )
            active_target = next(
                (shot for shot in bundle.shots if shot.shot_id == binding.target_shot_id),
                None,
            )
            base_target = next(
                (
                    item
                    for item in base_project.artifacts.shots
                    if active_target is not None
                    and item.artifact_id == active_target.artifact_id
                ),
                None,
            )
            if (
                base_target is None
                or base_target.revision != binding.target_shot_revision
                or base_target.content_hash != binding.target_shot_content_hash
            ):
                raise ValueError(
                    "continuity terminal target does not match the base project"
                )
            matching = tuple(
                attempt
                for attempt in bundle.manifest.attempts
                if attempt.video_generation_state is not None
                and attempt.video_generation_state.terminal_frame_evidence is not None
                and attempt.video_generation_state.terminal_frame_evidence.content_hash
                == binding.terminal_frame.content_hash
            )
            if len(matching) != 1:
                raise ValueError(
                    "continuity terminal has no unique source activation"
                )
            state = matching[0].video_generation_state
            assert state is not None and state.terminal_frame_evidence is not None
            source_request = load_video_request_receipt(bundle.root, state.request)
            source_scope = source_request.activation_scope
            if (
                load_terminal_frame_evidence(
                    bundle.root, state.terminal_frame_evidence
                )
                != binding.terminal_frame
                or source_scope is None
                or source_scope.request.target_shot_id
                != binding.terminal_frame.source_shot_id
                or source_scope.request.target_shot_revision
                != binding.terminal_frame.source_shot_revision
                or source_scope.request.target_shot_content_hash
                != binding.terminal_frame.source_shot_content_hash
            ):
                raise ValueError(
                    "continuity terminal does not match durable evidence bytes"
                )
            continue
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


def _verify_submit_audit_chain(
    bundle: LoadedProductionProject,
    attempt: StateCommitAttempt,
    request: ImageGenerationRequest,
    request_path: Path,
    request_sha256: str,
    base_registry: AssetRegistrySnapshot,
) -> tuple[tuple[Path, str], ...]:
    summary = attempt.image_request
    if summary is None:
        raise ValueError("image attempt request summary is missing")

    preview_path = canonical_image_preview_path(summary.preview_fingerprint)
    preview_value, preview_sha256 = _read_canonical_json(
        bundle.root, preview_path, label="image preview"
    )
    preview = ImageGenerationPreview.model_validate(preview_value)

    authorization_path = canonical_image_authorization_path(
        summary.authorization_fingerprint
    )
    authorization_value, authorization_sha256 = _read_canonical_json(
        bundle.root, authorization_path, label="image authorization"
    )
    authorization = ImageGenerationAuthorization.model_validate(
        authorization_value
    )

    assets = {item.asset_id: item for item in base_registry.assets}
    reference_asset_ids = tuple(item.asset_id for item in request.references)
    if (
        preview.request_fingerprint != request.request_fingerprint
        or preview.preview_fingerprint != summary.preview_fingerprint
        or preview.reference_asset_ids != reference_asset_ids
        or preview.reference_total_bytes
        != sum(assets[asset_id].size_bytes for asset_id in reference_asset_ids)
        or authorization.request_fingerprint != request.request_fingerprint
        or authorization.preview_fingerprint != preview.preview_fingerprint
        or authorization.authorization_fingerprint
        != summary.authorization_fingerprint
        or authorization.policy_receipt_id != summary.policy_receipt_id
        or authorization.usage_license != summary.usage_license
    ):
        raise ValueError(
            "image preview or authorization does not match its selected attempt"
        )

    profile_pairs: tuple[tuple[Path, str], ...] = ()
    if request.provider_kind == "comfyui_local":
        prefix = "local-image-profile:sha256:"
        if not request.model_id.startswith(prefix):
            raise ValueError("local image model_id is not an execution profile identity")
        profile_hash = request.model_id.removeprefix(prefix)
        profile_path = canonical_image_execution_profile_path(profile_hash)
        profile_value, profile_sha256 = _read_canonical_json(
            bundle.root, profile_path, label="image execution profile"
        )
        profile = LocalImageExecutionProfile.model_validate(profile_value)
        if profile.profile_id != request.model_id:
            raise ValueError("image execution profile identity mismatch")
        profile_pairs = ((profile_path, profile_sha256),)

    r1_pairs = sorted(
        (
            (request_path.as_posix(), request_sha256),
            (preview_path.as_posix(), preview_sha256),
            (authorization_path.as_posix(), authorization_sha256),
            *((path.as_posix(), digest) for path, digest in profile_pairs),
        )
    )
    evidence_hash = hashlib.sha256(
        json.dumps(r1_pairs, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    submit_intent_path = canonical_image_submit_intent_path(
        request.request_fingerprint
    )
    submit_intent, _ = _read_canonical_json(
        bundle.root, submit_intent_path, label="image submit intent"
    )
    expected_submit_intent = {
        "schema": "ai-video-image-submit-intent/1",
        "attempt_id": request.attempt_id,
        "request_fingerprint": request.request_fingerprint,
        "preview_fingerprint": preview.preview_fingerprint,
        "authorization_fingerprint": authorization.authorization_fingerprint,
        "policy_receipt_id": authorization.policy_receipt_id,
        "usage_license": authorization.usage_license,
        "base_project": request.base_project.model_dump(mode="json"),
        "base_registry": request.base_registry.model_dump(mode="json"),
        "base_dependency_graph": request.base_dependency_graph.model_dump(
            mode="json"
        ),
        "evidence_hash": evidence_hash,
    }
    if submit_intent != expected_submit_intent:
        raise ValueError(
            "image submit intent does not match its exact R+1 evidence"
        )
    return profile_pairs


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
    profile_pairs = _verify_submit_audit_chain(
        bundle,
        attempt,
        request,
        request_path,
        request_sha256,
        base_registry,
    )

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

    roles = tuple(
        item
        for item in candidate_shot.required_asset_roles
        if item.role == request.target_asset_role
    )
    expected_inputs = (
        candidate_shot.artifact_id,
        *(
            identity
            for item in request.references
            for identity in _reference_graph_input_ids(item)
        ),
    )
    if (
        len(roles) != 1
        or roles[0].asset_ids != (asset.asset_id,)
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
        *profile_pairs,
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
    expected_count = 9 if attempt.image_request.provider_kind == "comfyui_local" else 8
    if (
        len(normalized) != expected_count
        or len({path for path, _ in normalized}) != expected_count
    ):
        raise ValueError("image candidate artifact set is not exact")
    actual = hashlib.sha256(
        json.dumps(normalized, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if actual != attempt.candidate_artifacts_hash:
        raise ValueError("image candidate artifact hash mismatch")


def _verify_image_activation_chronology(
    manifest: ProductionManifest,
    attempt: StateCommitAttempt,
) -> None:
    """Bind activation-time state evidence without freezing later P5 results."""

    activation_revision = attempt.base_manifest_revision + 4
    if manifest.manifest_revision < activation_revision:
        raise ValueError("active image Manifest revision predates activation")
    if manifest.manifest_revision == activation_revision:
        if attempt.candidate_project != manifest.active_project:
            raise ValueError("selected image candidate was not activated")
        states_payload = json.dumps(
            [
                item.model_dump(mode="json")
                for item in manifest.dependency_states
            ],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if attempt.candidate_dependency_states_hash != hashlib.sha256(
            states_payload
        ).hexdigest():
            raise ValueError("active image dependency state hash mismatch")


def verify_image_attempt_evidence(
    bundle: LoadedProductionProject,
    attempt: StateCommitAttempt,
) -> tuple[tuple[Path, str], ...]:
    """Reopen the authoritative P7 or local-profile P7.1 candidate proof."""

    if (
        attempt.operation != "image_generation"
        or attempt.image_request is None
        or attempt.candidate_project is None
        or attempt.candidate_registry is None
        or attempt.candidate_dependency_graph is None
        or attempt.candidate_dependency_states_hash is None
        or len(attempt.candidate_image_asset_ids) != 1
    ):
        raise _invalid("P7 image candidate evidence identity is incomplete.")
    asset_id = attempt.candidate_image_asset_ids[0]
    assets_by_id = {item.asset_id: item for item in bundle.registry.assets}
    asset = assets_by_id.get(asset_id)
    if asset is None:
        raise _invalid("P7 image candidate asset is absent from its Registry.")
    try:
        candidate_project, project_sha256 = _read_candidate_project(bundle, attempt)
        candidate_registry, registry_sha256 = _read_candidate_registry(
            bundle, attempt
        )
        _, graph_sha256 = _read_candidate_graph(bundle, attempt)
        base_project = _read_base_project(bundle, attempt)
        base_registry = _read_base_registry(bundle, attempt)
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
        pairs = (
            *evidence_pairs,
            (attempt.candidate_project.path, project_sha256),
            (attempt.candidate_registry.path, registry_sha256),
            (attempt.candidate_dependency_graph.path, graph_sha256),
        )
        _verify_candidate_artifacts_hash(attempt, pairs)
        return pairs
    except (AiVideoError, OSError, UnicodeError, ValidationError, ValueError) as exc:
        detail = exc.technical_detail if isinstance(exc, AiVideoError) else str(exc)
        raise _invalid(
            "P7 image candidate history or reference provenance is invalid.",
            detail,
        ) from exc


def reopen_image_attempt_request(
    bundle: LoadedProductionProject,
    attempt: StateCommitAttempt,
) -> ImageGenerationRequest:
    verify_image_attempt_evidence(bundle, attempt)
    if attempt.image_request is None:
        raise _invalid("P7 image attempt has no request summary.")
    request_value, _ = _read_canonical_json(
        bundle.root,
        canonical_image_request_path(attempt.image_request.request_fingerprint),
        label="image request",
    )
    try:
        request = ImageGenerationRequest.model_validate(request_value)
    except ValidationError as exc:
        raise _invalid("P7 image request evidence is invalid.", str(exc)) from exc
    if not _attempt_summary_matches_request(attempt, request):
        raise _invalid("P7 image request does not match its selected attempt.")
    return request


def verify_hard_cut_keyframe_evidence(
    bundle: LoadedProductionProject,
    resolved_request,
    *,
    require_active_base: bool,
) -> None:
    from ai_video.production._video_project_reader import load_terminal_frame_evidence
    from ai_video.production.video import (
        validate_hard_cut_keyframe_binding_against_project,
    )

    scope = resolved_request.activation_scope
    if scope is None or scope.request.hard_cut_keyframe_binding is None:
        return
    request = scope.request
    binding = request.hard_cut_keyframe_binding
    validate_hard_cut_keyframe_binding_against_project(
        request,
        bundle,
        require_active_base=require_active_base,
    )
    image_attempts = tuple(
        attempt
        for attempt in bundle.manifest.attempts
        if attempt.image_request is not None
        and attempt.image_request.request_fingerprint
        == binding.keyframe_request_fingerprint
    )
    if len(image_attempts) != 1:
        raise _invalid("Hard-cut keyframe has no unique P7 activation.")
    image_request = reopen_image_attempt_request(bundle, image_attempts[0])
    terminal_references = tuple(
        reference
        for reference in image_request.references
        if reference.role == "continuity_terminal"
    )
    matching_terminal_pointers = tuple(
        attempt.video_generation_state.terminal_frame_evidence
        for attempt in bundle.manifest.attempts
        if attempt.video_generation_state is not None
        and attempt.video_generation_state.terminal_frame_evidence is not None
        and attempt.video_generation_state.terminal_frame_evidence.content_hash
        == binding.terminal_frame.content_hash
    )
    if (
        image_request.output_asset_id != binding.keyframe_asset_id
        or len(terminal_references) != 1
        or terminal_references[0].terminal_frame != binding.terminal_frame
        or terminal_references[0].constraints != binding.constraints
        or len(matching_terminal_pointers) != 1
        or load_terminal_frame_evidence(
            bundle.root, matching_terminal_pointers[0]
        )
        != binding.terminal_frame
    ):
        raise _invalid(
            "Hard-cut binding does not match exact durable P7 and terminal evidence."
        )


def verify_active_image_evidence(bundle: LoadedProductionProject) -> None:
    if bundle.manifest.schema_version not in {"2.5", "2.6", "2.7", "2.8", "2.9", "2.10"}:
        return
    attempts = tuple(
        item
        for item in bundle.manifest.attempts
        if item.operation == "image_generation"
        and item.status is StateCommitStatus.SUCCEEDED
        and item.image_phase == "activate"
    )
    assets_by_id = {item.asset_id: item for item in bundle.registry.assets}
    active_placements: dict[str, list[tuple[str, str, tuple[str, ...], str | None]]] = {}
    for shot in bundle.shots:
        for role in shot.required_asset_roles:
            for asset_id in role.asset_ids:
                asset = assets_by_id.get(asset_id)
                if (
                    asset is not None
                    and asset.asset_type is AssetType.IMAGE
                    and asset.source_kind is AssetSourceKind.GENERATED
                ):
                    active_placements.setdefault(asset_id, []).append(
                        (
                            shot.shot_id,
                            role.role,
                            role.asset_ids,
                            shot.creation_receipt_id,
                        )
                    )
    active_asset_ids = set(active_placements)
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
            summary = attempt.image_request
            asset = assets_by_id[asset_id]
            placements = active_placements[asset_id]
            if (
                summary is None
                or placements
                != [
                    (
                        summary.target_shot_id,
                        summary.target_asset_role,
                        (asset_id,),
                        asset.creation_receipt_id,
                    )
                ]
            ):
                raise ValueError(
                    "active generated image placement provenance is inconsistent"
                )
            verify_image_attempt_evidence(bundle, attempt)

        if selected:
            latest = max(selected.values(), key=lambda item: item.base_manifest_revision)
            _verify_image_activation_chronology(bundle.manifest, latest)
    except (AiVideoError, OSError, UnicodeError, ValidationError, ValueError) as exc:
        detail = exc.technical_detail if isinstance(exc, AiVideoError) else str(exc)
        raise _invalid(
            "Active P7 image candidate history or reference provenance is invalid.",
            detail,
        ) from exc

    try:
        imported = tuple(
            item
            for item in bundle.registry.assets
            if item.source_kind is AssetSourceKind.IMPORTED
            and item.asset_type is AssetType.IMAGE
            and item.tool == HUMAN_IMAGE_IMPORT_TOOL
        )
        for asset in imported:
            receipt_path = canonical_human_image_import_receipt_path(
                asset.creation_receipt_id
            )
            receipt_value, _ = _read_canonical_json(
                bundle.root, receipt_path, label="human image import receipt"
            )
            receipt = HumanImageImportReceipt.model_validate(receipt_value)
            image = _read_regular_file_nofollow(
                bundle.root / asset.artifact_path,
                contained_by=bundle.root / "assets/files",
            )
            validate_human_image_import(receipt, image.data)
            if human_image_import_asset(receipt) != asset:
                raise ValueError("selected human image import AssetRecord is inconsistent")
            if receipt.target_kind == "character_master":
                targets = tuple(
                    item
                    for item in bundle.characters
                    if item.artifact_id == receipt.target_artifact_id
                    and item.reference_asset_ids == (asset.asset_id,)
                    and item.creation_receipt_id == receipt.content_hash
                )
            elif receipt.target_kind == "scene_reference":
                targets = tuple(
                    item
                    for item in bundle.scenes
                    if item.artifact_id == receipt.target_artifact_id
                    and item.visual_reference_asset_ids == (asset.asset_id,)
                    and item.creation_receipt_id == receipt.content_hash
                )
            else:
                targets = tuple(
                    item
                    for item in bundle.shots
                    if item.artifact_id == receipt.target_artifact_id
                    and item.creation_receipt_id == receipt.content_hash
                    and any(
                        role.role == receipt.target_asset_role
                        and role.asset_ids == (asset.asset_id,)
                        for role in item.required_asset_roles
                    )
                )
            if len(targets) != 1:
                raise ValueError("selected human image import target binding is inconsistent")
    except (AiVideoError, OSError, UnicodeError, ValidationError, ValueError) as exc:
        detail = exc.technical_detail if isinstance(exc, AiVideoError) else str(exc)
        raise _invalid(
            "Active human image import provenance is invalid.",
            detail,
        ) from exc
