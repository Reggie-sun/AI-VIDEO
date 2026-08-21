"""Pure helpers and immutable-snapshot preparation for the production state committer.

Every helper in this module is either:
  * a deterministic, I/O-free encoder (canonical bytes, hashes, transitions), or
  * a typed error-construction utility, or
  * a commit-point phase/cleanup helper that operates on in-memory values only.

Nothing in this module opens files, opens sockets, or mutates Production state;
all of those responsibilities remain with ``ai_video.production.state_commit``.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping

import yaml
from pydantic import BaseModel, ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.dependency import (
    dependency_graph_semantic_sha256,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production._lifecycle_schema import has_p6_state
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    AssetRegistrySnapshot,
    AssetType,
    DependencyGraphSnapshot,
    DependencyGraphSnapshotPointer,
    DependencyGraphTransition,
    DependencyNodeState,
    ProductionManifest,
    ProductionProject,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    ReviewLifecycle,
    RenderSourceBundlePointer,
    StateCommitAttempt,
    StateCommitStatus,
    canonical_project_snapshot_path,
    canonical_registry_snapshot_path,
)
from ai_video.production.paths import canonical_dependency_graph_snapshot_path
from ai_video.production.registry import registry_semantic_sha256

from ._state_commit_contracts import (
    CommitPhase,
    PreparedArtifact,
    StateCommitRequest,
)


_GRAPH_ARTIFACT_PHASES = {
    CommitPhase.AFTER_ARTIFACT_TEMP_WRITE: CommitPhase.AFTER_GRAPH_CANDIDATE_TEMP_WRITE,
    CommitPhase.AFTER_ARTIFACT_FILE_FSYNC: CommitPhase.AFTER_GRAPH_CANDIDATE_FILE_FSYNC,
    CommitPhase.AFTER_ARTIFACT_PROMOTION: CommitPhase.AFTER_GRAPH_CANDIDATE_PROMOTION,
    CommitPhase.AFTER_ARTIFACT_DIRECTORY_FSYNC: CommitPhase.AFTER_GRAPH_CANDIDATE_DIRECTORY_FSYNC,
    CommitPhase.AFTER_ARTIFACT_VERIFICATION: CommitPhase.AFTER_GRAPH_CANDIDATE_VERIFICATION,
}


_RESERVED_TARGETS = {
    Path("state/manifest.json"),
    Path("state/commit.lock"),
}
_TEMP_ATTEMPT_LABEL_LIMIT = 24
_TEMP_FINAL_LABEL_LIMIT = 180
_TEMP_DIGEST_LENGTH = 12


def _owned_temp_name(attempt_id: str, final_path: Path) -> str:
    attempt_label = re.sub(r"[^A-Za-z0-9_-]", "_", attempt_id) or "attempt"
    attempt_label = attempt_label[:_TEMP_ATTEMPT_LABEL_LIMIT]
    attempt_digest = hashlib.sha256(attempt_id.encode("utf-8")).hexdigest()[:_TEMP_DIGEST_LENGTH]
    original_final_name = final_path.name
    final_label = re.sub(r"[^A-Za-z0-9._-]", "_", original_final_name) or "artifact"
    if len(final_label) > _TEMP_FINAL_LABEL_LIMIT:
        final_digest = hashlib.sha256(original_final_name.encode("utf-8")).hexdigest()[:_TEMP_DIGEST_LENGTH]
        final_label = "{}-{}".format(
            final_label[: _TEMP_FINAL_LABEL_LIMIT - _TEMP_DIGEST_LENGTH - 1], final_digest
        )
    return f".p2a-{attempt_label}-{attempt_digest}-{final_label}.tmp"


def _owned_temp_prefix(attempt_id: str) -> str:
    attempt_label = re.sub(r"[^A-Za-z0-9_-]", "_", attempt_id) or "attempt"
    attempt_label = attempt_label[:_TEMP_ATTEMPT_LABEL_LIMIT]
    attempt_digest = hashlib.sha256(attempt_id.encode("utf-8")).hexdigest()[
    :_TEMP_DIGEST_LENGTH
    ]
    return f".p2a-{attempt_label}-{attempt_digest}-"


def _canonical_json_bytes(model: BaseModel) -> bytes:
    payload = json.dumps(
        model.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (payload + "\n").encode("utf-8")


def _canonical_yaml_bytes(model: BaseModel) -> bytes:
    payload = yaml.safe_dump(
        model.model_dump(mode="json"),
        sort_keys=True,
        allow_unicode=True,
    )
    return payload.encode("utf-8")


def _state_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return _state_error(ErrorCode.PRODUCTION_STATE_INVALID, message, detail)


def _state_commit_failed(message: str, detail: str | None = None) -> AiVideoError:
    return _state_error(ErrorCode.PRODUCTION_STATE_COMMIT_FAILED, message, detail)


def _state_recovery_failed(message: str, detail: str | None = None) -> AiVideoError:
    return _state_error(ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED, message, detail)


def _state_unsupported(message: str, detail: str | None = None) -> AiVideoError:
    return _state_error(ErrorCode.PRODUCTION_STATE_UNSUPPORTED, message, detail)


def _state_error(code: ErrorCode, message: str, detail: str | None) -> AiVideoError:
    return AiVideoError(
        code=code,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )
def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redact_render_error_message(value: str) -> str:
    bounded = value[-2_048:]
    return re.sub(
        r"(?i)(token|secret|authorization|password)(\s*[:=]\s*)[^\s,;]+",
        r"\1\2[REDACTED]",
        bounded,
    )


def _stable_voice_terminal_message(
    status: StateCommitStatus,
    phase: str,
) -> str:
    if status is StateCommitStatus.FAILED:
        if phase == "provider_call":
            return "Voice provider rejected the submitted request."
        return "Voice generation failed before its provider outcome became ambiguous."
    if phase == "materialize":
        return "Voice result could not be durably activated; explicit recovery is required."
    return "Voice provider outcome is unknown; blind retry is forbidden."


def _as_state_error(exc: BaseException) -> AiVideoError:
    if isinstance(exc, AiVideoError):
        return exc
    return _state_commit_failed("Production state commit failed.", str(exc))
def _candidate_artifacts_hash(artifacts: tuple[PreparedArtifact, ...]) -> str:
    pairs = [(item.relative_path.as_posix(), item.file_sha256) for item in artifacts]
    if len({path for path, _ in pairs}) != len(pairs):
        raise _state_invalid("Production state request contains duplicate artifact paths.")
    return _candidate_artifacts_evidence_hash(artifacts)


def _candidate_artifacts_evidence_hash(
    artifacts: tuple[PreparedArtifact, ...],
) -> str:
    pairs = [(item.relative_path.as_posix(), item.file_sha256) for item in artifacts]
    payload = json.dumps(sorted(pairs), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _bundle_hash_from_pointers(bundle: RenderSourceBundlePointer) -> str:
    entries = [
        (
            bundle.index.path.relative_to(bundle.root_path).as_posix(),
            bundle.index.file_sha256,
        ),
        *(
            (item.path.relative_to(bundle.root_path).as_posix(), item.file_sha256)
            for item in bundle.assets
        ),
    ]
    payload = json.dumps(sorted(entries), ensure_ascii=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _outcome_unknown(exc: BaseException) -> AiVideoError:
    if isinstance(exc, AiVideoError) and exc.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN:
        return exc
    primary = _as_state_error(exc)
    unknown = AiVideoError(ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN, "Production state commit outcome is unknown after Manifest replacement.", primary.technical_detail or str(primary))
    unknown.add_note(f"Original commit failure: {primary}")
    return unknown


def _is_process_exception(exc: BaseException) -> bool:
    return not isinstance(exc, Exception)


def _handle_cleanup_errors(
    primary: BaseException | None,
    cleanup_errors: list[BaseException],
    *,
    label: str,
    no_primary_message: str,
) -> None:
    process_error = next((item for item in cleanup_errors if _is_process_exception(item)), None)
    if process_error is not None:
        if primary is not None:
            process_error.add_note(f"{label} interrupted after prior failure: {primary}")
        for cleanup_error in cleanup_errors:
            if cleanup_error is not process_error:
                process_error.add_note(f"{label} also failed: {cleanup_error}")
        raise process_error
    if primary is not None:
        for cleanup_error in cleanup_errors:
            primary.add_note(f"{label} failed: {cleanup_error}")
    elif cleanup_errors:
        raise _state_commit_failed(
            no_primary_message, "; ".join(str(item) for item in cleanup_errors)
        ) from cleanup_errors[0]


def _validated_transition(
    model: ProductionManifest | StateCommitAttempt, update: dict[str, object]
) -> ProductionManifest | StateCommitAttempt:
    if isinstance(model, ProductionManifest) and (
        model.schema_version == "2.4"
        or (model.schema_version in {"2.5", "2.6", "2.7", "2.8", "2.9"} and has_p6_state(model))
    ):
        identity_fields = (
            "active_project",
            "active_registry",
            "active_render_state",
            "active_dependency_graph",
            "active_qa_policy",
        )
        if any(
            field in update and update[field] != getattr(model, field)
            for field in identity_fields
        ):
            update = {
                **update,
                "active_review_receipts": (),
                "review_states": tuple(
                    item.model_copy(
                        update={
                            "lifecycle": ReviewLifecycle.STALE,
                            "active_receipt": None,
                        }
                    )
                    for item in model.review_states
                ),
                "final_acceptance_state": None,
            }
    return type(model).model_validate({**model.model_dump(mode="python"), **update})


def prepare_project_registry_commit(
    *,
    manifest: ProductionManifest,
    project: ProductionProject,
    registry: AssetRegistrySnapshot,
    attempt_id: str,
) -> StateCommitRequest:
    """Build the immutable snapshots selected by one P2A manifest transition."""
    if project.project_id != manifest.project_id:
        raise _state_invalid("Project ID does not match Production Manifest.")
    if not verify_artifact_hash(project):
        raise _state_invalid("Project semantic content hash is invalid.")
    registry_hash = registry_semantic_sha256(registry)
    if (
        registry.revision_id != registry.content_hash
        or registry.content_hash != registry_hash
    ):
        raise _state_invalid("Registry revision and semantic content hash are invalid.")
    if project.revision < manifest.active_project.revision:
        raise _state_invalid("Project revision cannot move backwards.")
    if (
        project.revision == manifest.active_project.revision
        and project.content_hash != manifest.active_project.content_hash
    ):
        raise _state_invalid("A project revision cannot be reused with different content.")

    project_payload = _canonical_yaml_bytes(project)
    registry_payload = _canonical_json_bytes(registry)
    project_path = canonical_project_snapshot_path(
        project.revision, project.content_hash
    )
    registry_path = canonical_registry_snapshot_path(registry.revision_id)
    project_file_hash = hashlib.sha256(project_payload).hexdigest()
    registry_file_hash = hashlib.sha256(registry_payload).hexdigest()
    return StateCommitRequest(
        attempt_id=attempt_id,
        operation="commit_project_registry",
        expected_manifest_revision=manifest.manifest_revision,
        artifacts=tuple(
            sorted(
                (
                    PreparedArtifact(project_path, project_payload, project_file_hash),
                    PreparedArtifact(registry_path, registry_payload, registry_file_hash),
                ),
                key=lambda artifact: artifact.relative_path.as_posix(),
            )
        ),
        next_project=ProjectSnapshotPointer(
            path=project_path,
            revision=project.revision,
            content_hash=project.content_hash,
            file_sha256=project_file_hash,
        ),
        next_registry=RegistrySnapshotPointer(
            path=registry_path,
            revision_id=registry.revision_id,
            content_hash=registry.content_hash,
            file_sha256=registry_file_hash,
        ),
    )


def prepare_audio_registry_commit(
    *,
    manifest: ProductionManifest,
    project: ProductionProject,
    base_registry: AssetRegistrySnapshot,
    registry: AssetRegistrySnapshot,
    attempt_id: str,
    artifacts: tuple[PreparedArtifact, ...],
    active_project_artifact: PreparedArtifact | None = None,
) -> StateCommitRequest:
    """Purely build one exact audio/caption registry commit for the P2A writer."""

    if (
        project.project_id != manifest.project_id
        or project.revision != manifest.active_project.revision
        or project.content_hash != manifest.active_project.content_hash
        or not verify_artifact_hash(project)
    ):
        raise _state_invalid("Audio registry project does not match the active Manifest snapshot.")
    if active_project_artifact is None:
        raise _state_invalid("Audio registry commit requires exact active project bytes.")
    project_payload = active_project_artifact.payload
    project_file_hash = hashlib.sha256(project_payload).hexdigest()
    try:
        parsed_project = ProductionProject.model_validate(yaml.safe_load(project_payload))
    except (ValidationError, ValueError, yaml.YAMLError) as exc:
        raise _state_invalid("Audio registry active project bytes are invalid.", str(exc)) from exc
    if parsed_project != project or project_file_hash != manifest.active_project.file_sha256:
        raise _state_invalid("Audio registry project bytes do not match the active Manifest snapshot.")
    if (
        base_registry.revision_id != manifest.active_registry.revision_id
        or base_registry.content_hash != manifest.active_registry.content_hash
        or registry_semantic_sha256(base_registry) != base_registry.content_hash
        or hashlib.sha256(_canonical_json_bytes(base_registry)).hexdigest()
        != manifest.active_registry.file_sha256
    ):
        raise _state_invalid("Audio registry base does not match the active Manifest snapshot.")
    if registry.schema_version != "2.1":
        raise _state_invalid("Audio registry commits require Asset Registry 2.1.")
    if registry.assets[: len(base_registry.assets)] != base_registry.assets:
        raise _state_invalid("Audio registry candidate must preserve every base record exactly.")
    new_records = registry.assets[len(base_registry.assets) :]
    if tuple(item.asset_id for item in new_records) != tuple(
        sorted(item.asset_id for item in new_records)
    ):
        raise _state_invalid("Audio registry new records must use canonical asset-id order.")
    if any(
        item.asset_type
        not in {AssetType.VOICE, AssetType.MUSIC, AssetType.SFX, AssetType.CAPTION}
        for item in new_records
    ):
        raise _state_invalid("Audio registry commits may only add P4 audio or caption assets.")
    candidate_ids = [item.asset_id for item in registry.assets]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise _state_invalid("Audio registry candidate contains duplicate asset IDs.")
    prepared_by_path = {item.relative_path: item for item in artifacts}
    expected_paths = {item.artifact_path for item in new_records}
    expected_paths.update(
        Path(f"assets/styles/{item.caption_metadata.style_content_hash}.json")
        for item in new_records
        if item.caption_metadata is not None
        and item.caption_metadata.style_content_hash is not None
    )
    if set(prepared_by_path) != expected_paths or len(prepared_by_path) != len(artifacts):
        raise _state_invalid(
            "Audio registry candidate does not contain the exact declared new artifact set."
        )
    for record in new_records:
        artifact = prepared_by_path.get(record.artifact_path)
        if (
            artifact is None
            or artifact.file_sha256 != record.sha256
            or len(artifact.payload) != record.size_bytes
        ):
            raise _state_invalid(
                "Audio registry candidate does not contain the exact new asset artifact set."
            )

    project_artifact = active_project_artifact
    if (
        project_artifact.relative_path != manifest.active_project.path
        or project_artifact.payload != project_payload
        or project_artifact.file_sha256 != project_file_hash
    ):
        raise _state_invalid("Audio registry active project artifact is not exact.")
    registry_hash = registry_semantic_sha256(registry)
    if registry.revision_id != registry_hash or registry.content_hash != registry_hash:
        raise _state_invalid("Audio registry semantic hash is invalid.")
    registry_payload = _canonical_json_bytes(registry)
    registry_path = canonical_registry_snapshot_path(registry.revision_id)
    registry_artifact = PreparedArtifact(
        registry_path,
        registry_payload,
        hashlib.sha256(registry_payload).hexdigest(),
    )
    next_project = manifest.active_project
    next_registry = RegistrySnapshotPointer(
        path=registry_path,
        revision_id=registry.revision_id,
        content_hash=registry.content_hash,
        file_sha256=registry_artifact.file_sha256,
    )
    base_artifacts = (project_artifact, registry_artifact)
    combined = base_artifacts + artifacts
    paths = [item.relative_path for item in combined]
    if len(paths) != len(set(paths)):
        raise _state_invalid("Audio registry commit contains duplicate artifact paths.")
    return StateCommitRequest(
        attempt_id=attempt_id,
        operation="audio_import",
        expected_manifest_revision=manifest.manifest_revision,
        artifacts=tuple(sorted(combined, key=lambda item: item.relative_path.as_posix())),
        next_project=next_project,
        next_registry=next_registry,
    )


def _dependency_states_hash(states: tuple[DependencyNodeState, ...]) -> str:
    payload = json.dumps(
        [state.model_dump(mode="json") for state in states],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def prepare_dependency_graph_transition(
    *,
    expected_manifest_revision: int,
    base_dependency_graph: DependencyGraphSnapshotPointer | None,
    candidate_graph: DependencyGraphSnapshot,
    candidate_dependency_states: tuple[DependencyNodeState, ...],
    expected_desired_fingerprints: Mapping[str, str],
) -> DependencyGraphTransition:
    """Purely bind one immutable graph and its exact Manifest lifecycle.

    The function deliberately accepts no project root and performs no I/O.
    Callers supply the expected desired map, but it is recomputed from the
    graph before a transition value is returned.
    """

    semantic_hash = dependency_graph_semantic_sha256(candidate_graph)
    if (
        candidate_graph.revision_id != semantic_hash
        or candidate_graph.content_hash != semantic_hash
    ):
        raise _state_invalid("Dependency graph semantic identity is invalid.")
    desired = desired_fingerprints(candidate_graph)
    if dict(expected_desired_fingerprints) != desired:
        raise _state_invalid("Dependency graph desired fingerprints are stale.")
    canonical_states = tuple(
        sorted(candidate_dependency_states, key=lambda state: state.node_id)
    )
    if canonical_states != candidate_dependency_states:
        raise _state_invalid("Dependency graph states are not canonically ordered.")
    if any(
        state.applied_fingerprint is not None and state.applied_evidence is None
        for state in canonical_states
    ):
        raise _state_invalid(
            "Dependency graph applied fingerprints require reopenable evidence."
        )
    resolved = resolve_dependency_state(candidate_graph, canonical_states)
    if resolved.states != canonical_states:
        raise _state_invalid("Dependency graph states are not a resolved lifecycle.")
    payload = _canonical_json_bytes(candidate_graph)
    pointer = DependencyGraphSnapshotPointer(
        revision_id=candidate_graph.revision_id,
        content_hash=candidate_graph.content_hash,
        path=canonical_dependency_graph_snapshot_path(candidate_graph.revision_id),
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    return DependencyGraphTransition(
        expected_manifest_revision=expected_manifest_revision,
        base_dependency_graph=base_dependency_graph,
        candidate_dependency_graph=pointer,
        candidate_dependency_states=canonical_states,
        candidate_dependency_states_hash=_dependency_states_hash(canonical_states),
    )
