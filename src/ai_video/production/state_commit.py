from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import stat
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, Callable, Iterator, Literal, Mapping, Protocol

import yaml
from pydantic import BaseModel, ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import (
    PreparedAudioImport,
    VoiceAssetProvider,
    VoiceCallAuthorization,
    VoiceGenerationPreview,
    VoiceGenerationRequest,
    VoiceProviderResult,
    VoiceCostReceipt,
    VoiceProvenanceReceipt,
    _result_fingerprint,
)
from ai_video.production.captions import (
    CaptionImportRequest,
    PreparedCaptionImport,
    _canonical_track_bytes,
    caption_timing_fingerprint,
)
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.models import (
    AssetType,
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AudioAssetMetadata,
    AudioSource,
    CaptionAssetMetadata,
    CaptionTrack,
    DependencyAppliedEvidence,
    DependencyGraphSnapshot,
    DependencyGraphSnapshotPointer,
    DependencyGraphTransition,
    DependencyLifecycle,
    DependencyNodeKind,
    DependencyNodeState,
    EgressMetadata,
    LoadedProductionProject,
    ProductionManifest,
    ProductionProject,
    QaLayer,
    QaPolicy,
    QaPolicyPointer,
    QaVerdict,
    ProjectSnapshotPointer,
    RecoveryDisposition,
    RecoveryItem,
    RecoveryReport,
    RegistrySnapshotPointer,
    ProjectDependencyEvidence,
    RegistryDependencyEvidence,
    RenderDependencyEvidence,
    RendererSelectionReceipt,
    RendererSourceReceipt,
    RenderReceipt,
    RenderSourceBundlePointer,
    RenderStateSnapshot,
    RenderStateSnapshotPointer,
    ReviewLayerState,
    ReviewLifecycle,
    ReviewReceipt,
    ReviewReceiptPointer,
    ResolvedTimeline,
    SourceReference,
    StateCommitAttempt,
    StateCommitStatus,
    VoiceRequestReceipt,
    canonical_project_snapshot_path,
    canonical_registry_snapshot_path,
    require_canonical_project_snapshot_path,
    require_canonical_registry_snapshot_path,
)
from ai_video.production.paths import (
    _list_regular_files_nofollow,
    _open_directory_nofollow,
    _read_regular_file_nofollow,
    canonical_render_attempt_root,
    canonical_render_output_path,
    canonical_render_receipt_path,
    canonical_render_source_asset_path,
    canonical_render_source_index_path,
    canonical_render_source_root,
    canonical_render_state_path,
    canonical_render_timeline_path,
    canonical_renderer_source_receipt_path,
    canonical_voice_attempt_artifact_path,
    canonical_voice_attempt_root,
    canonical_voice_audio_candidate_path,
    canonical_audio_asset_path,
    canonical_dependency_graph_snapshot_path,
    canonical_qa_policy_path,
    canonical_review_receipt_path,
)
from ai_video.production.project import (
    _load_exact_render_state,
    _render_source_binding_map,
    _render_source_payload_matches,
    _validate_source_timeline_bindings,
    _verify_dependency_project_evidence,
    _verify_dependency_registry_evidence,
    _verify_dependency_render_evidence,
    _verify_manifest_dependency_states,
    load_production_project_candidate,
    load_verified_render_state,
)
from ai_video.production.dependency import (
    dependency_graph_semantic_sha256,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.registry import registry_semantic_sha256

try:
    import fcntl
except ImportError:  # pragma: no cover - exercised through platform injection
    fcntl = None  # type: ignore[assignment]


@dataclass(frozen=True)
class PreparedArtifact:
    relative_path: Path
    payload: bytes
    file_sha256: str


@dataclass(frozen=True)
class StateCommitRequest:
    attempt_id: str
    operation: str
    expected_manifest_revision: int
    artifacts: tuple[PreparedArtifact, ...]
    next_project: ProjectSnapshotPointer
    next_registry: RegistrySnapshotPointer
    dependency_graph_transition: DependencyGraphTransition | None = None


@dataclass(frozen=True)
class BeginRenderAttemptRequest:
    expected_manifest_revision: int
    base_render_state: RenderStateSnapshotPointer | None
    renderer_selection: RendererSelectionReceipt


@dataclass(frozen=True)
class RecordRenderFailureRequest:
    attempt_id: str
    expected_manifest_revision: int
    current_project: ProjectSnapshotPointer
    current_registry: RegistrySnapshotPointer
    base_render_state: RenderStateSnapshotPointer | None
    renderer_selection: RendererSelectionReceipt
    phase: Literal["source", "lint", "check", "render", "verify"]
    error_code: str
    error_message: str


@dataclass(frozen=True)
class ActivateRenderStateRequest:
    attempt_id: str
    expected_manifest_revision: int
    current_project: ProjectSnapshotPointer
    current_registry: RegistrySnapshotPointer
    base_render_state: RenderStateSnapshotPointer | None
    renderer_selection: RendererSelectionReceipt
    artifacts: tuple[PreparedArtifact, ...]
    next_render_state: RenderStateSnapshotPointer
    dependency_graph_transition: DependencyGraphTransition | None = None


@dataclass(frozen=True)
class RenderAttemptPaths:
    attempt_root: Path
    source_root: Path
    staged_output_path: Path
    verification_snapshot_path: Path


@dataclass(frozen=True)
class VoiceAttemptPaths:
    attempt_root: Path
    request_path: Path
    preview_path: Path
    authorization_path: Path
    submit_intent_path: Path
    audio_candidate_path: Path
    alignment_path: Path
    cost_path: Path
    provenance_path: Path
    outcome_path: Path


VoiceCandidatePreparer = Callable[
    [
        VoiceGenerationRequest,
        VoiceGenerationPreview,
        VoiceCallAuthorization,
        VoiceProviderResult,
        VoiceAttemptPaths,
    ],
    "PreparedVoiceCandidate",
]
VoiceDependencyTransitionPreparer = Callable[
    [StateCommitRequest], StateCommitRequest
]


@dataclass(frozen=True)
class PreparedVoiceCandidate:
    """Narrow local-only output; it carries no registry/write/activation authority."""

    audio: PreparedAudioImport
    caption: PreparedCaptionImport | None = None
    caption_asset_record: AssetRecord | None = None

    def __post_init__(self) -> None:
        if (self.caption is None) != (self.caption_asset_record is None):
            raise ValueError("Prepared voice caption bytes and AssetRecord must be all-or-none.")


class CommitPhase(str, Enum):
    AFTER_ATTEMPT_STARTED = "after_attempt_started"
    AFTER_ARTIFACT_TEMP_WRITE = "after_artifact_temp_write"
    AFTER_ARTIFACT_FILE_FSYNC = "after_artifact_file_fsync"
    AFTER_ARTIFACT_PROMOTION = "after_artifact_promotion"
    AFTER_ARTIFACT_DIRECTORY_FSYNC = "after_artifact_directory_fsync"
    AFTER_ARTIFACT_VERIFICATION = "after_artifact_verification"
    AFTER_GRAPH_CANDIDATE_TEMP_WRITE = "after_graph_candidate_temp_write"
    AFTER_GRAPH_CANDIDATE_FILE_FSYNC = "after_graph_candidate_file_fsync"
    AFTER_GRAPH_CANDIDATE_PROMOTION = "after_graph_candidate_promotion"
    AFTER_GRAPH_CANDIDATE_DIRECTORY_FSYNC = "after_graph_candidate_directory_fsync"
    AFTER_GRAPH_CANDIDATE_VERIFICATION = "after_graph_candidate_verification"
    AFTER_GRAPH_FINAL_MANIFEST_REPLACE = "after_graph_final_manifest_replace"
    AFTER_MANIFEST_TEMP_WRITE = "after_manifest_temp_write"
    AFTER_MANIFEST_FILE_FSYNC = "after_manifest_file_fsync"
    AFTER_MANIFEST_REPLACE = "after_manifest_replace"
    AFTER_MANIFEST_DIRECTORY_FSYNC = "after_manifest_directory_fsync"
    BEFORE_RENDER_CANDIDATE_MANIFEST_SERIALIZATION = "before_render_candidate_manifest_serialization"
    AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_OPEN = "after_render_candidate_manifest_temp_open"
    AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_WRITE = "after_render_candidate_manifest_temp_write"
    AFTER_RENDER_CANDIDATE_MANIFEST_FILE_FSYNC = "after_render_candidate_manifest_file_fsync"
    BEFORE_RENDER_CANDIDATE_MANIFEST_REPLACE = "before_render_candidate_manifest_replace"
    AFTER_RENDER_CANDIDATE_MANIFEST_REPLACE = "after_render_candidate_manifest_replace"
    AFTER_RENDER_CANDIDATE_MANIFEST_DIRECTORY_FSYNC = "after_render_candidate_manifest_directory_fsync"
    AFTER_RENDER_CANDIDATE_MANIFEST_VERIFICATION = "after_render_candidate_manifest_verification"
    AFTER_RENDER_FINAL_MANIFEST_TEMP_WRITE = "after_render_final_manifest_temp_write"
    AFTER_RENDER_FINAL_MANIFEST_FILE_FSYNC = "after_render_final_manifest_file_fsync"
    BEFORE_RENDER_FINAL_MANIFEST_REPLACE = "before_render_final_manifest_replace"
    AFTER_RENDER_FINAL_MANIFEST_REPLACE = "after_render_final_manifest_replace"
    AFTER_RENDER_FINAL_MANIFEST_DIRECTORY_FSYNC = "after_render_final_manifest_directory_fsync"
    BEFORE_VOICE_SUBMIT_INTENT = "before_voice_submit_intent"
    AFTER_VOICE_SUBMIT_INTENT = "after_voice_submit_intent"
    AFTER_VOICE_PROVIDER_RESULT = "after_voice_provider_result"
    AFTER_VOICE_CANDIDATE_MANIFEST = "after_voice_candidate_manifest"
    AFTER_VOICE_FINAL_MANIFEST_REPLACE = "after_voice_final_manifest_replace"


class CrashInjector(Protocol):
    def checkpoint(self, phase: CommitPhase) -> None: ...


class NoopCrashInjector:
    def checkpoint(self, phase: CommitPhase) -> None:
        return None


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
_VOICE_PERMIT_TOKEN = object()


class _DurableVoiceSubmitPermit:
    """Process-local one-use proof that the exact R+2 intent is durable."""

    __slots__ = (
        "_binding",
        "_manifest_revision",
        "_manifest_file_sha256",
        "_durability_validator",
        "_consumed",
        "_lock",
    )

    def __init__(
        self,
        token: object,
        *,
        binding: dict[str, str],
        manifest_revision: int,
        manifest_file_sha256: str,
        durability_validator: Callable[[], bool],
    ) -> None:
        if token is not _VOICE_PERMIT_TOKEN:
            raise TypeError("Voice submit permits are minted only by ProductionStateCommitter.")
        self._binding = dict(binding)
        self._manifest_revision = manifest_revision
        self._manifest_file_sha256 = manifest_file_sha256
        self._durability_validator = durability_validator
        self._consumed = False
        self._lock = threading.Lock()

    def _validate_voice_submit_permit(self, **binding: str) -> bool:
        return (
            not self._consumed
            and binding == self._binding
            and self._durability_validator()
        )

    def _consume_voice_submit_permit(self, **binding: str) -> bool:
        with self._lock:
            if not self._validate_voice_submit_permit(**binding):
                return False
            self._consumed = True
            return True

    def __reduce__(self) -> object:
        raise TypeError("Voice submit permits cannot be serialized.")


if TYPE_CHECKING:
    DurableVoiceSubmitPermit = _DurableVoiceSubmitPermit


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
    if isinstance(model, ProductionManifest) and model.schema_version == "2.4":
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


class _FileOps(Protocol):
    def mkdir(self, path: Path) -> bool: ...
    def open_exclusive(self, path: Path) -> BinaryIO: ...
    def fsync_file(self, handle: BinaryIO, path: Path) -> None: ...
    def replace(self, source: Path, destination: Path) -> None: ...
    def fsync_directory(self, path: Path) -> None: ...
    def stat(self, path: Path) -> os.stat_result: ...
    def link(self, source: Path, destination: Path) -> None: ...
    def sha256_file(self, path: Path) -> str: ...
    def unlink(self, path: Path, *, missing_ok: bool = False) -> None: ...


class _NativeFileOps:
    def mkdir(self, path: Path) -> bool:
        try:
            path.mkdir()
        except FileExistsError:
            return False
        return True
    def open_exclusive(self, path: Path) -> BinaryIO:
        return path.open("xb")
    def fsync_file(self, handle: BinaryIO, path: Path) -> None:
        os.fsync(handle.fileno())
    def replace(self, source: Path, destination: Path) -> None:
        os.replace(source, destination)
    def fsync_directory(self, path: Path) -> None:
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        descriptor = os.open(path, flags)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    def stat(self, path: Path) -> os.stat_result:
        return path.stat()
    def link(self, source: Path, destination: Path) -> None:
        os.link(source, destination)
    def sha256_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    def unlink(self, path: Path, *, missing_ok: bool = False) -> None:
        path.unlink(missing_ok=missing_ok)


class ProductionStateCommitter:
    """Single owner for durable POSIX P2A state commits."""

    def __init__(
        self,
        project_root: str | Path,
        *,
        file_ops: _FileOps | None = None,
        crash_injector: CrashInjector | None = None,
        voice_candidate_preparer: VoiceCandidatePreparer | None = None,
    ) -> None:
        try:
            self._project_root = Path(project_root).resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise _state_invalid("Production state root is unsafe.", str(exc)) from exc
        if not self._project_root.is_dir():
            raise _state_invalid("Production state root must be a directory.")
        self._ops = file_ops or _NativeFileOps()
        self._crash_injector = crash_injector or NoopCrashInjector()
        self._voice_candidate_preparer = voice_candidate_preparer

    def activate_qa_policy(
        self,
        policy: QaPolicy,
        *,
        expected_manifest_revision: int,
        attempt_id: str,
    ) -> ProductionManifest:
        """Select one immutable QA policy; policy drift only stales review state."""
        if not verify_artifact_hash(policy):
            raise _state_invalid("QA policy semantic content hash is invalid.")
        payload = _canonical_json_bytes(policy)
        file_sha256 = hashlib.sha256(payload).hexdigest()
        pointer = QaPolicyPointer(
            path=canonical_qa_policy_path(policy.content_hash),
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            content_hash=policy.content_hash,
            file_sha256=file_sha256,
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if manifest.manifest_revision != expected_manifest_revision:
                if manifest.schema_version == "2.4" and manifest.active_qa_policy == pointer:
                    return manifest
                raise _state_invalid("QA policy base Manifest revision changed.")
            if manifest.schema_version not in {"2.3", "2.4"}:
                raise _state_invalid("P6 requires a P5 Manifest 2.3 or 2.4 base.")
            if manifest.active_dependency_graph is None:
                raise _state_invalid("P6 requires an active dependency graph.")
            if manifest.schema_version == "2.4" and manifest.active_qa_policy == pointer:
                return manifest
            artifact = PreparedArtifact(pointer.path, payload, file_sha256)
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            stale_states = tuple(
                item.model_copy(
                    update={
                        "lifecycle": ReviewLifecycle.STALE,
                        "active_receipt": None,
                    }
                )
                for item in manifest.review_states
            )
            final_state = manifest.final_acceptance_state
            if final_state is not None:
                final_state = final_state.model_copy(
                    update={
                        "lifecycle": ReviewLifecycle.STALE,
                        "active_receipt": None,
                    }
                )
            updated = manifest.model_copy(
                update={
                    "schema_version": "2.4",
                    "manifest_revision": manifest.manifest_revision + 1,
                    "active_qa_policy": pointer,
                    "active_review_receipts": (),
                    "review_states": stale_states,
                    "final_acceptance_state": final_state,
                }
            )
            updated = ProductionManifest.model_validate(updated.model_dump(mode="python"))
            self._write_manifest_atomic(updated)
            return self._read_manifest()

    def record_review_receipt(
        self,
        receipt: ReviewReceipt,
        *,
        expected_manifest_revision: int,
        attempt_id: str,
    ) -> ProductionManifest:
        """Persist and activate one exact current-layer Review Receipt."""
        if not verify_artifact_hash(receipt):
            raise _state_invalid("Review Receipt semantic content hash is invalid.")
        payload = _canonical_json_bytes(receipt)
        file_sha256 = hashlib.sha256(payload).hexdigest()
        pointer = ReviewReceiptPointer(
            path=canonical_review_receipt_path(receipt.content_hash),
            review_id=receipt.review_id,
            layer=receipt.layer,
            content_hash=receipt.content_hash,
            file_sha256=file_sha256,
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if manifest.manifest_revision != expected_manifest_revision:
                if pointer in manifest.active_review_receipts:
                    return manifest
                raise _state_invalid("Review base Manifest revision changed.")
            if (
                manifest.schema_version != "2.4"
                or manifest.active_qa_policy != receipt.qa_policy
                or manifest.active_dependency_graph is None
                or manifest.active_dependency_graph.revision_id
                != receipt.dependency_graph_revision_id
                or manifest.active_render_state != receipt.render_state
            ):
                raise _state_invalid("Review Receipt does not bind current Production state.")
            artifact = PreparedArtifact(pointer.path, payload, file_sha256)
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            desired = canonical_sha256(
                {
                    "layer": receipt.layer.value,
                    "graph": receipt.dependency_graph_revision_id,
                    "render": receipt.render_state.content_hash,
                    "output": receipt.render_output_sha256,
                    "timeline": receipt.timeline_fingerprint,
                    "policy": receipt.qa_policy.content_hash,
                }
            )
            lifecycle = {
                QaVerdict.PASS: ReviewLifecycle.FRESH,
                QaVerdict.FAIL: ReviewLifecycle.FAILED,
                QaVerdict.NOT_EVALUATED: ReviewLifecycle.NOT_EVALUATED,
            }[receipt.verdict]
            state = ReviewLayerState(
                layer=receipt.layer,
                desired_fingerprint=desired,
                applied_fingerprint=desired,
                lifecycle=lifecycle,
                active_receipt=pointer,
            )
            receipts = tuple(
                item for item in manifest.active_review_receipts if item.layer != receipt.layer
            ) + (pointer,)
            states = tuple(
                item for item in manifest.review_states if item.layer != receipt.layer
            ) + (state,)
            updated = manifest.model_copy(
                update={
                    "manifest_revision": manifest.manifest_revision + 1,
                    "active_review_receipts": tuple(
                        sorted(receipts, key=lambda item: item.layer.value)
                    ),
                    "review_states": tuple(sorted(states, key=lambda item: item.layer.value)),
                    "final_acceptance_state": None,
                }
            )
            updated = ProductionManifest.model_validate(updated.model_dump(mode="python"))
            self._write_manifest_atomic(updated)
            return self._read_manifest()

    @property
    def project_root(self) -> Path:
        return self._project_root

    def voice_attempt_paths(self, attempt_id: str) -> VoiceAttemptPaths:
        try:
            root = canonical_voice_attempt_root(self._project_root, attempt_id)
            return VoiceAttemptPaths(
                attempt_root=root,
                request_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "request.json"
                ),
                preview_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "preview.json"
                ),
                authorization_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "authorization.json"
                ),
                submit_intent_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "submit-intent.json"
                ),
                audio_candidate_path=canonical_voice_audio_candidate_path(
                    self._project_root, attempt_id
                ),
                alignment_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "alignment.json"
                ),
                cost_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "cost.json"
                ),
                provenance_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "provenance.json"
                ),
                outcome_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "outcome.json"
                ),
            )
        except ValueError as exc:
            raise _state_invalid("Voice attempt ID is unsafe.", str(exc)) from exc

    @staticmethod
    def _voice_receipt(
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
    ) -> VoiceRequestReceipt:
        if (
            preview.request_fingerprint != request.voice_request_fingerprint
            or authorization.request_fingerprint != request.voice_request_fingerprint
            or authorization.preview_fingerprint != preview.preview_fingerprint
            or authorization.destination != preview.destination
            or authorization.budget_reservation_receipt_id
            != request.budget_reservation_receipt_id
            or authorization.egress_authorization_receipt_id
            != request.egress_authorization_receipt_id
            or preview.pricing_snapshot_id != request.pricing_snapshot_id
            or authorization.pricing_snapshot_id != request.pricing_snapshot_id
            or authorization.payload_categories != preview.payload_categories
            or authorization.cost_ceiling_microunits
            < preview.estimated_cost_upper_bound_microunits
            or not preview.timing_supported
            or not preview.output_supported
            or not authorization.provider_enabled
        ):
            raise _state_invalid(
                "Voice preview or authorization does not match the immutable request."
            )
        return VoiceRequestReceipt(
            request_id=request.request_id,
            attempt_id=request.attempt_id,
            request_fingerprint=request.voice_request_fingerprint,
            script_hash=request.script_hash,
            provider_kind=request.provider_kind,
            model_id=request.model_id,
            voice_id=request.voice_id,
            language=request.language,
            pricing_snapshot_id=request.pricing_snapshot_id,
            budget_reservation_receipt_id=request.budget_reservation_receipt_id,
            egress_authorization_receipt_id=request.egress_authorization_receipt_id,
            destination=authorization.destination,
        )

    def _voice_prepared_artifact(
        self, attempt_id: str, absolute_path: Path, payload: bytes
    ) -> PreparedArtifact:
        return self.prepare_artifact(
            attempt_id, absolute_path.relative_to(self._project_root), payload
        )

    def begin_voice_generation(
        self,
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
        *,
        dependency_transition_preparer_available: bool = False,
    ) -> ProductionManifest:
        """Persist R+1 request, preview, and authorization evidence without transport."""

        receipt = self._voice_receipt(request, preview, authorization)
        paths = self.voice_attempt_paths(request.attempt_id)
        evidence = (
            self._voice_prepared_artifact(
                request.attempt_id, paths.request_path, _canonical_json_bytes(request)
            ),
            self._voice_prepared_artifact(
                request.attempt_id, paths.preview_path, _canonical_json_bytes(preview)
            ),
            self._voice_prepared_artifact(
                request.attempt_id,
                paths.authorization_path,
                _canonical_json_bytes(authorization),
            ),
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if (
                manifest.schema_version == "2.3"
                and not dependency_transition_preparer_available
            ):
                raise _state_invalid(
                    "Manifest 2.3 voice generation requires a dependency transition preparer."
                )
            existing = next(
                (item for item in manifest.attempts if item.attempt_id == request.attempt_id),
                None,
            )
            if existing is not None:
                if (
                    existing.operation == "voice_generation"
                    and existing.voice_request == receipt
                    and existing.base_project == request.base_project
                    and existing.base_registry == request.base_registry
                    and existing.voice_phase == "request"
                    and existing.status is StateCommitStatus.RUNNING
                ):
                    reopened = self._reopen_voice_evidence(
                        request.attempt_id, include_intent=False
                    )
                    if reopened != evidence or (
                        _candidate_artifacts_hash(reopened)
                        != existing.candidate_artifacts_hash
                    ):
                        raise _state_invalid("Voice R+1 replay evidence is not exact.")
                    return manifest
                raise _state_invalid("Voice attempt ID was already used by another request.")
            if (
                request.base_project != manifest.active_project
                or request.base_registry != manifest.active_registry
            ):
                raise _state_invalid("Voice request base project or registry is stale.")
            if any(
                item.status in {StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN}
                for item in manifest.attempts
            ):
                raise _state_invalid(
                    "Production state has an unresolved attempt; explicit recovery is required."
                )
            for artifact in evidence:
                self._write_immutable_artifact(artifact, attempt_id=request.attempt_id)
            attempt = StateCommitAttempt(
                attempt_id=request.attempt_id,
                operation="voice_generation",
                status=StateCommitStatus.RUNNING,
                base_manifest_revision=manifest.manifest_revision,
                base_project=manifest.active_project,
                base_registry=manifest.active_registry,
                candidate_artifacts_hash=_candidate_artifacts_hash(evidence),
                voice_request=receipt,
                voice_phase="request",
                started_at=_timestamp(),
            )
            r1 = _validated_transition(
                manifest,
                {
                    "schema_version": (
                        "2.3" if manifest.schema_version == "2.3" else "2.2"
                    ),
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": manifest.attempts + (attempt,),
                },
            )
            self._write_manifest_atomic(r1)
            return self._read_manifest()

    def record_voice_submit_intent(
        self,
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
    ) -> _DurableVoiceSubmitPermit:
        """Persist R+2, reopen it, and mint exactly one process-local permit."""

        receipt = self._voice_receipt(request, preview, authorization)
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = next(
                (item for item in manifest.attempts if item.attempt_id == request.attempt_id),
                None,
            )
            if (
                attempt is None
                or attempt.operation != "voice_generation"
                or attempt.voice_request != receipt
                or attempt.status is not StateCommitStatus.RUNNING
                or attempt.voice_phase != "request"
                or manifest.active_project != request.base_project
                or manifest.active_registry != request.base_registry
            ):
                raise _state_invalid(
                    "Voice submit intent requires the exact current R+1 attempt."
                )
            self._crash_injector.checkpoint(CommitPhase.BEFORE_VOICE_SUBMIT_INTENT)
            paths = self.voice_attempt_paths(request.attempt_id)
            intent_payload = (
                json.dumps(
                    {
                        "attempt_id": request.attempt_id,
                        "request_fingerprint": request.voice_request_fingerprint,
                        "authorization_fingerprint": authorization.authorization_fingerprint,
                        "destination": authorization.destination,
                        "budget_reservation_receipt_id": authorization.budget_reservation_receipt_id,
                        "egress_authorization_receipt_id": authorization.egress_authorization_receipt_id,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            ).encode()
            artifact = self._voice_prepared_artifact(
                request.attempt_id, paths.submit_intent_path, intent_payload
            )
            r1_artifacts = self._reopen_voice_evidence(request.attempt_id, include_intent=False)
            expected_r1 = (
                self._voice_prepared_artifact(
                    request.attempt_id, paths.request_path, _canonical_json_bytes(request)
                ),
                self._voice_prepared_artifact(
                    request.attempt_id, paths.preview_path, _canonical_json_bytes(preview)
                ),
                self._voice_prepared_artifact(
                    request.attempt_id,
                    paths.authorization_path,
                    _canonical_json_bytes(authorization),
                ),
            )
            if (
                r1_artifacts != expected_r1
                or _candidate_artifacts_hash(r1_artifacts)
                != attempt.candidate_artifacts_hash
            ):
                raise _state_invalid("Voice R+1 evidence changed before submit intent.")
            self._write_immutable_artifact(artifact, attempt_id=request.attempt_id)
            aggregate = _candidate_artifacts_hash((*r1_artifacts, artifact))
            r2_attempt = _validated_transition(
                attempt,
                {
                    "voice_phase": "submit_intent",
                    "candidate_artifacts_hash": aggregate,
                },
            )
            r2 = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        r2_attempt if item.attempt_id == request.attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(r2)
            reopened = self._read_manifest()
            reopened_attempt = next(
                item for item in reopened.attempts if item.attempt_id == request.attempt_id
            )
            if (
                reopened_attempt.voice_phase != "submit_intent"
                or reopened_attempt.candidate_artifacts_hash != aggregate
            ):
                raise _state_commit_failed("Voice submit intent reopen verification failed.")
            intent_snapshot = _read_regular_file_nofollow(
                paths.submit_intent_path,
                contained_by=self._project_root,
            )
            if (
                intent_snapshot.data != intent_payload
                or intent_snapshot.file_sha256 != artifact.file_sha256
            ):
                raise _state_commit_failed("Voice submit intent exact-byte verification failed.")
            manifest_snapshot = _read_regular_file_nofollow(
                self._project_root / "state/manifest.json",
                contained_by=self._project_root,
            )
            self._crash_injector.checkpoint(CommitPhase.AFTER_VOICE_SUBMIT_INTENT)
            binding = {
                "attempt_id": request.attempt_id,
                "request_fingerprint": request.voice_request_fingerprint,
                "authorization_fingerprint": authorization.authorization_fingerprint,
                "destination": authorization.destination,
                "budget_reservation_receipt_id": authorization.budget_reservation_receipt_id,
                "egress_authorization_receipt_id": authorization.egress_authorization_receipt_id,
            }
            return _DurableVoiceSubmitPermit(
                _VOICE_PERMIT_TOKEN,
                binding=binding,
                manifest_revision=reopened.manifest_revision,
                manifest_file_sha256=manifest_snapshot.file_sha256,
                durability_validator=lambda: self._voice_submit_intent_is_current(
                    reopened.manifest_revision,
                    manifest_snapshot.file_sha256,
                    request.attempt_id,
                    aggregate,
                    artifact.file_sha256,
                    intent_payload,
                ),
            )

    def _reopen_voice_evidence(
        self, attempt_id: str, *, include_intent: bool
    ) -> tuple[PreparedArtifact, ...]:
        paths = self.voice_attempt_paths(attempt_id)
        selected = [paths.request_path, paths.preview_path, paths.authorization_path]
        if include_intent:
            selected.append(paths.submit_intent_path)
        artifacts = []
        for path in selected:
            snapshot = _read_regular_file_nofollow(path, contained_by=self._project_root)
            artifacts.append(
                PreparedArtifact(
                    relative_path=path.relative_to(self._project_root),
                    payload=snapshot.data,
                    file_sha256=snapshot.file_sha256,
                )
            )
        return tuple(artifacts)

    def _voice_submit_intent_is_current(
        self,
        manifest_revision: int,
        manifest_file_sha256: str,
        attempt_id: str,
        aggregate_hash: str,
        intent_sha256: str,
        intent_payload: bytes,
    ) -> bool:
        try:
            snapshot = _read_regular_file_nofollow(
                self._project_root / "state/manifest.json",
                contained_by=self._project_root,
            )
            if snapshot.file_sha256 != manifest_file_sha256:
                return False
            manifest = ProductionManifest.model_validate_json(snapshot.data)
            evidence = self._reopen_voice_evidence(attempt_id, include_intent=True)
        except (AiVideoError, OSError, ValidationError, ValueError):
            return False
        attempt = next(
            (item for item in manifest.attempts if item.attempt_id == attempt_id), None
        )
        return (
            manifest.manifest_revision == manifest_revision
            and attempt is not None
            and attempt.operation == "voice_generation"
            and attempt.status is StateCommitStatus.RUNNING
            and attempt.voice_phase == "submit_intent"
            and attempt.candidate_artifacts_hash == aggregate_hash
            and _candidate_artifacts_hash(evidence) == aggregate_hash
            and evidence[-1].file_sha256 == intent_sha256
            and evidence[-1].payload == intent_payload
        )

    def _record_voice_terminal(
        self,
        attempt_id: str,
        *,
        status: StateCommitStatus,
        phase: Literal[
            "request",
            "submit_intent",
            "provider_call",
            "materialize",
            "probe",
            "align",
            "candidate",
            "activate",
        ],
        error_code: str,
        error_message: str,
    ) -> ProductionManifest:
        if status not in {StateCommitStatus.FAILED, StateCommitStatus.OUTCOME_UNKNOWN}:
            raise _state_invalid("Voice terminal transition status is invalid.")
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = next(
                (item for item in manifest.attempts if item.attempt_id == attempt_id), None
            )
            stable_message = _stable_voice_terminal_message(status, phase)
            if attempt is None or attempt.operation != "voice_generation":
                raise _state_invalid("Voice terminal transition has no matching attempt.")
            if attempt.status is status:
                if (
                    attempt.voice_phase == phase
                    and attempt.error_code == error_code
                    and attempt.error_message == stable_message
                ):
                    return manifest
                raise _state_invalid("Voice terminal replay does not match durable state.")
            if attempt.status is not StateCommitStatus.RUNNING:
                raise _state_invalid("Voice terminal transition is stale.")
            terminal_attempt = _validated_transition(
                attempt,
                {
                    "status": status,
                    "voice_phase": phase,
                    "finished_at": _timestamp(),
                    "error_code": error_code,
                    "error_message": stable_message,
                },
            )
            terminal = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        terminal_attempt if item.attempt_id == attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(terminal)
            return self._read_manifest()

    def record_voice_failure(
        self,
        attempt_id: str,
        *,
        phase: Literal[
            "request", "submit_intent", "provider_call", "materialize", "probe", "align", "candidate", "activate"
        ],
        error_code: str,
        error_message: str,
    ) -> ProductionManifest:
        return self._record_voice_terminal(
            attempt_id,
            status=StateCommitStatus.FAILED,
            phase=phase,
            error_code=error_code,
            error_message=error_message,
        )

    def record_voice_outcome_unknown(
        self,
        attempt_id: str,
        *,
        phase: Literal[
            "submit_intent", "provider_call", "materialize", "probe", "align", "candidate", "activate"
        ],
        error_code: str = ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN.value,
        error_message: str = "Voice provider outcome is unknown; blind retry is forbidden.",
    ) -> ProductionManifest:
        return self._record_voice_terminal(
            attempt_id,
            status=StateCommitStatus.OUTCOME_UNKNOWN,
            phase=phase,
            error_code=error_code,
            error_message=error_message,
        )

    @staticmethod
    def _validate_voice_provider_result(
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
        result: VoiceProviderResult,
    ) -> None:
        if not isinstance(result, VoiceProviderResult):
            raise _state_invalid("Voice provider returned an untyped result.")
        if (
            result.request_id != request.request_id
            or result.request_fingerprint != request.voice_request_fingerprint
            or result.preview_fingerprint != preview.preview_fingerprint
            or result.authorization_fingerprint
            != authorization.authorization_fingerprint
            or result.content_type not in {"audio/wav", "audio/x-wav"}
            or result.cost_receipt.pricing_snapshot_id
            != request.pricing_snapshot_id
            or result.cost_receipt.estimated_cost_upper_bound_microunits
            != preview.estimated_cost_upper_bound_microunits
            or (
                result.cost_receipt.provider_reported_cost_microunits is not None
                and result.cost_receipt.provider_reported_cost_microunits
                > authorization.cost_ceiling_microunits
            )
            or result.provenance_receipt.provider_kind != request.provider_kind
            or result.provenance_receipt.model_id != request.model_id
            or result.provenance_receipt.voice_id != request.voice_id
            or result.provenance_receipt.language != request.language
            or result.provenance_receipt.script_hash != request.script_hash
            or result.provenance_receipt.egress_authorization_receipt_id
            != request.egress_authorization_receipt_id
        ):
            raise _state_invalid(
                "Voice provider result contradicts request, preview, authorization, or receipts."
            )

    def _prepare_voice_activation_request(
        self,
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
        result: VoiceProviderResult,
        prepared: PreparedVoiceCandidate,
    ) -> tuple[StateCommitRequest, tuple[str, ...], tuple[str, ...]]:
        self._validate_voice_provider_result(request, preview, authorization, result)
        if not isinstance(prepared, PreparedVoiceCandidate) or not isinstance(
            prepared.audio, PreparedAudioImport
        ):
            raise _state_invalid("Voice candidate preparer returned an unsafe capability.")
        audio = prepared.audio
        probe = audio.probe
        if (
            audio.payload != result.audio_bytes
            or probe.file_sha256 != result.audio_sha256
            or probe.size_bytes != len(result.audio_bytes)
            or probe.mime_type != result.content_type
            or probe.codec_name != request.output_codec
            or probe.sample_rate_hz != request.output_sample_rate_hz
            or probe.channels != request.output_channels
        ):
            raise _state_invalid("Prepared voice audio does not match the exact provider result.")

        paths = self.voice_attempt_paths(request.attempt_id)
        provenance_bytes = _canonical_json_bytes(result.provenance_receipt)
        cost_bytes = _canonical_json_bytes(result.cost_receipt)
        provenance_hash = hashlib.sha256(provenance_bytes).hexdigest()
        cost_hash = hashlib.sha256(cost_bytes).hexdigest()
        alignment_hash = result.alignment_receipt_sha256
        audio_id = f"voice-{request.attempt_id}"
        audio_record = AssetRecord(
            asset_id=audio_id,
            asset_type=AssetType.VOICE,
            artifact_path=canonical_audio_asset_path(result.audio_sha256),
            sha256=result.audio_sha256,
            size_bytes=len(result.audio_bytes),
            mime_type=result.content_type,
            source_kind=AssetSourceKind.GENERATED,
            tool=result.provenance_receipt.adapter,
            input_artifact_ids=request.input_artifact_ids,
            input_fingerprint=request.input_fingerprint,
            creation_receipt_id=f"voice-result-{result.result_fingerprint}",
            usage_license=result.provenance_receipt.license_policy_decision,
            egress=EgressMetadata(
                remote=True,
                destination=authorization.destination,
                authorization_receipt_id=request.egress_authorization_receipt_id,
                request_fingerprint=request.voice_request_fingerprint,
                payload_fingerprint=request.script_hash,
                retention_mode=result.provenance_receipt.retention_mode,
                provider_policy_snapshot_id=result.provenance_receipt.policy_receipt_id,
            ),
            cost_receipt_id=f"cost-{cost_hash}",
            audio_metadata=AudioAssetMetadata(
                audio_kind=request.audio_kind,
                source=AudioSource(
                    kind=AssetSourceKind.GENERATED,
                    provider_or_tool=result.provenance_receipt.adapter,
                    input_artifact_ids=request.input_artifact_ids,
                    input_fingerprint=request.input_fingerprint,
                ),
                speaker_id=request.speaker_id,
                voice_id=request.voice_id,
                language=request.language,
                script_hash=request.script_hash,
                duration_samples=probe.duration_samples,
                sample_rate_hz=probe.sample_rate_hz,
                channels=probe.channels,
                channel_layout=probe.channel_layout,
                codec_name=probe.codec_name,
                loudness=probe.loudness,
                provenance_receipt_id=f"provenance-{provenance_hash}",
                alignment_receipt_id=f"alignment-{alignment_hash}",
            ),
        )
        asset_artifacts = [
            PreparedArtifact(audio_record.artifact_path, audio.payload, result.audio_sha256)
        ]
        new_records = [audio_record]
        caption_ids: tuple[str, ...] = ()
        if prepared.caption is not None:
            assert prepared.caption_asset_record is not None
            caption = prepared.caption
            supplied = prepared.caption_asset_record
            caption_id = f"caption-{request.attempt_id}"
            try:
                CaptionImportRequest(
                    caption_track=caption.caption_track,
                    track_bytes=caption.track_bytes,
                    track_sha256=caption.track_sha256,
                    style_reference=caption.style_reference,
                    style_bytes=caption.style_bytes,
                    style_sha256=caption.style_sha256,
                )
            except ValidationError as exc:
                raise _state_invalid("Prepared caption bytes are not canonical.", str(exc)) from exc
            track = caption.caption_track
            expected_caption_record = AssetRecord(
                asset_id=caption_id,
                asset_type=AssetType.CAPTION,
                artifact_path=Path(f"assets/captions/{caption.track_sha256}.json"),
                sha256=caption.track_sha256,
                size_bytes=len(caption.track_bytes),
                mime_type="application/json",
                source_kind=AssetSourceKind.DERIVED,
                tool=result.provenance_receipt.adapter,
                input_artifact_ids=(audio_id,),
                input_fingerprint=result.audio_sha256,
                creation_receipt_id=track.creation_receipt_id,
                usage_license=result.provenance_receipt.license_policy_decision,
                caption_metadata=CaptionAssetMetadata(
                    caption_track_id=track.caption_track_id,
                    language=track.language,
                    source_audio_asset_id=audio_id,
                    source_audio_sha256=result.audio_sha256,
                    script_hash=track.script_hash,
                    transcript_hash=track.transcript_hash,
                    segment_count=len(track.segments),
                    word_count=sum(len(item.words or ()) for item in track.segments),
                    segmentation_policy_id=track.segmentation_policy.policy_id,
                    segmentation_policy_version=track.segmentation_policy.policy_version,
                    alignment_receipt_id=track.alignment_receipt_id,
                    timing_fingerprint=track.timing_fingerprint,
                    style_reference_id=(
                        caption.style_reference.artifact_id
                        if caption.style_reference is not None
                        else None
                    ),
                    style_content_hash=(
                        caption.style_reference.content_hash
                        if caption.style_reference is not None
                        else None
                    ),
                    style_reference_revision=(
                        caption.style_reference.revision
                        if caption.style_reference is not None
                        else None
                    ),
                ),
            )
            if (
                supplied != expected_caption_record
                or track.source_audio_asset_id != audio_id
                or track.source_audio_sha256 != result.audio_sha256
                or track.script_hash != request.script_hash
                or track.transcript_hash != request.script_hash
                or track.source_sample_rate_hz != request.output_sample_rate_hz
                or track.language != request.language
                or track.alignment_receipt_id
                != f"alignment-{result.alignment_receipt_sha256}"
                or track.creation_receipt_id
                != f"caption-result-{result.result_fingerprint}"
                or track.source_provenance
                != (
                    SourceReference(
                        kind="derived",
                        reference=f"alignment-{result.alignment_receipt_sha256}",
                    ),
                )
                or track.timing_fingerprint != caption_timing_fingerprint(track)
            ):
                raise _state_invalid("Prepared caption identity does not match generated voice.")
            new_records.append(supplied)
            asset_artifacts.append(
                PreparedArtifact(supplied.artifact_path, caption.track_bytes, caption.track_sha256)
            )
            if caption.style_reference is not None:
                assert caption.style_bytes is not None and caption.style_sha256 is not None
                asset_artifacts.append(
                    PreparedArtifact(
                        caption.style_reference.path,
                        caption.style_bytes,
                        caption.style_sha256,
                    )
                )
            caption_ids = (caption_id,)

        manifest = self._read_manifest()
        project_snapshot = _read_regular_file_nofollow(
            self._project_root / request.base_project.path,
            contained_by=self._project_root,
        )
        registry_snapshot = _read_regular_file_nofollow(
            self._project_root / request.base_registry.path,
            contained_by=self._project_root,
        )
        try:
            project = ProductionProject.model_validate(yaml.safe_load(project_snapshot.data))
            base_registry = AssetRegistrySnapshot.model_validate_json(registry_snapshot.data)
        except (ValidationError, ValueError, yaml.YAMLError) as exc:
            raise _state_invalid("Voice base project or registry could not be reopened.", str(exc)) from exc
        ordered_new = tuple(sorted(new_records, key=lambda item: item.asset_id))
        registry = AssetRegistrySnapshot(
            schema_version="2.1",
            revision_id="0" * 64,
            content_hash="0" * 64,
            assets=base_registry.assets + ordered_new,
        )
        registry_hash = registry_semantic_sha256(registry)
        registry = registry.model_copy(
            update={"revision_id": registry_hash, "content_hash": registry_hash}
        )
        base_commit = prepare_audio_registry_commit(
            manifest=manifest,
            project=project,
            base_registry=base_registry,
            registry=registry,
            attempt_id=request.attempt_id,
            artifacts=tuple(asset_artifacts),
            active_project_artifact=PreparedArtifact(
                request.base_project.path, project_snapshot.data, project_snapshot.file_sha256
            ),
        )
        outcome_payload = (
            json.dumps(
                {
                    "request_id": result.request_id,
                    "request_fingerprint": result.request_fingerprint,
                    "preview_fingerprint": result.preview_fingerprint,
                    "authorization_fingerprint": result.authorization_fingerprint,
                    "result_fingerprint": result.result_fingerprint,
                    "provider_request_id": result.provider_request_id,
                    "provider_trace_id": result.provider_trace_id,
                    "audio_sha256": result.audio_sha256,
                    "alignment_receipt_sha256": result.alignment_receipt_sha256,
                    "content_type": result.content_type,
                    "policy_receipt_id": result.provenance_receipt.policy_receipt_id,
                    "retention_mode": result.provenance_receipt.retention_mode,
                    "terminal_status": result.terminal_status,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode()
        evidence = (
            *self._reopen_voice_evidence(request.attempt_id, include_intent=True),
            PreparedArtifact(
                paths.alignment_path.relative_to(self._project_root),
                result.alignment_receipt_bytes,
                alignment_hash,
            ),
            PreparedArtifact(
                paths.cost_path.relative_to(self._project_root), cost_bytes, cost_hash
            ),
            PreparedArtifact(
                paths.provenance_path.relative_to(self._project_root),
                provenance_bytes,
                provenance_hash,
            ),
            PreparedArtifact(
                paths.outcome_path.relative_to(self._project_root),
                outcome_payload,
                hashlib.sha256(outcome_payload).hexdigest(),
            ),
        )
        by_path = {
            item.relative_path: item for item in (*base_commit.artifacts, *evidence)
        }
        commit = StateCommitRequest(
            attempt_id=request.attempt_id,
            operation="voice_generation",
            expected_manifest_revision=manifest.manifest_revision,
            artifacts=tuple(sorted(by_path.values(), key=lambda item: item.relative_path.as_posix())),
            next_project=base_commit.next_project,
            next_registry=base_commit.next_registry,
        )
        return commit, (audio_id,), caption_ids

    def activate_voice_assets(
        self,
        request: StateCommitRequest,
        *,
        audio_asset_ids: tuple[str, ...],
        caption_asset_ids: tuple[str, ...] = (),
    ) -> ProductionManifest:
        """Persist R+3 exact candidates, then atomically select R+4 without transport."""

        if request.operation != "voice_generation" or not audio_asset_ids:
            raise _state_invalid("Voice activation request is incomplete.")
        self._validate_request(request)
        registry_artifact = next(
            (
                item
                for item in request.artifacts
                if item.relative_path == request.next_registry.path
            ),
            None,
        )
        if registry_artifact is None:
            raise _state_invalid("Voice activation registry artifact is missing.")
        try:
            candidate_registry = AssetRegistrySnapshot.model_validate_json(
                registry_artifact.payload
            )
        except (ValidationError, ValueError) as exc:
            raise _state_invalid("Voice activation registry artifact is invalid.", str(exc)) from exc
        by_id = {item.asset_id: item for item in candidate_registry.assets}
        if set(audio_asset_ids).intersection(caption_asset_ids) or any(
            asset_id not in by_id
            or by_id[asset_id].asset_type
            not in {AssetType.VOICE, AssetType.MUSIC, AssetType.SFX}
            for asset_id in audio_asset_ids
        ) or any(
            asset_id not in by_id or by_id[asset_id].asset_type is not AssetType.CAPTION
            for asset_id in caption_asset_ids
        ):
            raise _state_invalid("Voice activation asset IDs do not match the candidate registry.")
        candidate_hash = _candidate_artifacts_hash(request.artifacts)
        final_replaced = False
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = next(
                (item for item in manifest.attempts if item.attempt_id == request.attempt_id),
                None,
            )
            if attempt is None or attempt.operation != "voice_generation":
                raise _state_invalid("Voice activation has no matching attempt.")
            graph_transition: DependencyGraphTransition | None = None
            candidate_graph: DependencyGraphSnapshot | None = None
            if attempt.status is StateCommitStatus.SUCCEEDED:
                transition = request.dependency_graph_transition
                if manifest.schema_version == "2.3":
                    if transition is None or (
                        attempt.base_dependency_graph != transition.base_dependency_graph
                        or attempt.candidate_dependency_graph
                        != transition.candidate_dependency_graph
                        or attempt.candidate_dependency_states_hash
                        != transition.candidate_dependency_states_hash
                        or manifest.active_dependency_graph
                        != transition.candidate_dependency_graph
                        or manifest.dependency_states
                        != transition.candidate_dependency_states
                    ):
                        raise _state_invalid(
                            "Succeeded voice replay dependency transition does not match active state."
                        )
                    graph_transition = transition
                    active_graph = self._reopen_dependency_graph(
                        transition.candidate_dependency_graph
                    )
                    self._verify_dependency_candidate(
                        manifest, active_graph, manifest.dependency_states
                    )
                elif transition is not None:
                    raise _state_invalid(
                        "Dependency graph transition requires Manifest 2.3."
                    )
            else:
                graph_transition, candidate_graph = self._validate_dependency_transition(
                    manifest,
                    expected_manifest_revision=request.expected_manifest_revision,
                    artifacts=request.artifacts,
                    transition=request.dependency_graph_transition,
                )
            if (
                manifest.schema_version != "2.3"
                and (
                    attempt.status is StateCommitStatus.SUCCEEDED
                    or attempt.voice_phase == "candidate"
                )
            ):
                durable_request = self._reconstruct_voice_activation_request(attempt)
                if durable_request != request:
                    raise _state_invalid(
                        "Voice activation replay does not match the current durable candidate graph."
                    )
            provider_request_id = self._validate_voice_activation_graph(
                request,
                attempt,
                candidate_registry,
                audio_asset_ids,
                caption_asset_ids,
            )
            if attempt.status is StateCommitStatus.SUCCEEDED:
                if (
                    manifest.active_registry == request.next_registry
                    and attempt.candidate_artifacts_hash == candidate_hash
                    and attempt.candidate_audio_asset_ids == audio_asset_ids
                    and attempt.candidate_caption_asset_ids == caption_asset_ids
                ):
                    return manifest
                raise _state_invalid("Succeeded voice replay does not match active state.")
            candidate_exists = attempt.voice_phase == "candidate"
            if candidate_exists:
                if (
                    attempt.status not in {StateCommitStatus.RUNNING, StateCommitStatus.INTERRUPTED}
                    or attempt.candidate_project not in (None, request.next_project)
                    or attempt.candidate_registry != request.next_registry
                    or attempt.candidate_artifacts_hash != candidate_hash
                    or attempt.candidate_audio_asset_ids != audio_asset_ids
                    or attempt.candidate_caption_asset_ids != caption_asset_ids
                    or (
                        graph_transition is not None
                        and (
                            attempt.base_dependency_graph
                            != graph_transition.base_dependency_graph
                            or attempt.candidate_dependency_graph
                            != graph_transition.candidate_dependency_graph
                            or attempt.candidate_dependency_states_hash
                            != graph_transition.candidate_dependency_states_hash
                        )
                    )
                ):
                    raise _state_invalid("Voice candidate replay identity does not match.")
            else:
                if (
                    attempt.status is not StateCommitStatus.RUNNING
                    or attempt.voice_phase not in {
                        "submit_intent", "provider_call", "materialize", "probe", "align"
                    }
                    or manifest.manifest_revision != request.expected_manifest_revision
                    or manifest.active_project != attempt.base_project
                    or manifest.active_registry != attempt.base_registry
                    or request.next_project != attempt.base_project
                ):
                    raise _state_invalid("Voice activation base state or revision is stale.")
                for artifact in sorted(
                    request.artifacts, key=lambda item: item.relative_path.as_posix()
                ):
                    self._write_immutable_artifact(
                        artifact,
                        attempt_id=request.attempt_id,
                        dependency_graph=(
                            graph_transition is not None
                            and artifact.relative_path
                            == graph_transition.candidate_dependency_graph.path
                        ),
                    )
                self._verify_voice_committed_candidates(request)
                candidate_attempt = _validated_transition(
                    attempt,
                    {
                        "candidate_project": None,
                        "candidate_registry": request.next_registry,
                        "candidate_artifacts_hash": candidate_hash,
                        "candidate_audio_asset_ids": audio_asset_ids,
                        "candidate_caption_asset_ids": caption_asset_ids,
                        "provider_request_id": provider_request_id,
                        "voice_phase": "candidate",
                        "base_dependency_graph": (
                            None
                            if graph_transition is None
                            else graph_transition.base_dependency_graph
                        ),
                        "candidate_dependency_graph": (
                            None
                            if graph_transition is None
                            else graph_transition.candidate_dependency_graph
                        ),
                        "candidate_dependency_states_hash": (
                            None
                            if graph_transition is None
                            else graph_transition.candidate_dependency_states_hash
                        ),
                    },
                )
                if graph_transition is not None and candidate_graph is not None:
                    verification_attempt = _validated_transition(
                        candidate_attempt,
                        {
                            "status": StateCommitStatus.SUCCEEDED,
                            "voice_phase": "activate",
                            "finished_at": _timestamp(),
                            "error_code": None,
                            "error_message": None,
                        },
                    )
                    verification_attempts = tuple(
                        verification_attempt
                        if item.attempt_id == request.attempt_id
                        else item
                        for item in manifest.attempts
                    )
                    self._verify_dependency_candidate(
                        manifest,
                        candidate_graph,
                        graph_transition.candidate_dependency_states,
                        project_pointer=request.next_project,
                        registry_pointer=request.next_registry,
                        attempts=verification_attempts,
                    )
                candidate_manifest = _validated_transition(
                    manifest,
                    {
                        "manifest_revision": manifest.manifest_revision + 1,
                        "attempts": tuple(
                            candidate_attempt
                            if item.attempt_id == request.attempt_id
                            else item
                            for item in manifest.attempts
                        ),
                    },
                )
                self._write_manifest_atomic(candidate_manifest)
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_VOICE_CANDIDATE_MANIFEST
                )
                manifest = self._read_manifest()
                attempt = next(
                    item for item in manifest.attempts if item.attempt_id == request.attempt_id
                )
            succeeded = _validated_transition(
                attempt,
                {
                    "status": StateCommitStatus.SUCCEEDED,
                    "voice_phase": "activate",
                    "finished_at": _timestamp(),
                    "error_code": None,
                    "error_message": None,
                },
            )
            final_update: dict[str, object] = {
                "manifest_revision": manifest.manifest_revision + 1,
                "active_project": request.next_project,
                "active_registry": request.next_registry,
                "active_render_state": (
                    manifest.active_render_state
                    if manifest.schema_version == "2.3"
                    else None
                ),
                "attempts": tuple(
                    succeeded if item.attempt_id == request.attempt_id else item
                    for item in manifest.attempts
                ),
            }
            if graph_transition is not None:
                final_update.update(
                    {
                        "active_dependency_graph": graph_transition.candidate_dependency_graph,
                        "dependency_states": graph_transition.candidate_dependency_states,
                    }
                )
            final = _validated_transition(
                manifest,
                final_update,
            )

            def mark_replaced() -> None:
                nonlocal final_replaced
                final_replaced = True
                if graph_transition is not None:
                    self._crash_injector.checkpoint(
                        CommitPhase.AFTER_GRAPH_FINAL_MANIFEST_REPLACE
                    )

            try:
                self._write_manifest_atomic(final, on_replace=mark_replaced)
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_VOICE_FINAL_MANIFEST_REPLACE
                )
                return self._read_manifest()
            except Exception as exc:
                if final_replaced:
                    raise _outcome_unknown(exc) from exc
                raise

    def _validate_voice_activation_graph(
        self,
        commit: StateCommitRequest,
        attempt: StateCommitAttempt,
        candidate_registry: AssetRegistrySnapshot,
        audio_asset_ids: tuple[str, ...],
        caption_asset_ids: tuple[str, ...],
    ) -> str | None:
        if len(set(caption_asset_ids)) != len(caption_asset_ids):
            raise _state_invalid("Voice candidate graph contains duplicate caption asset IDs.")
        paths = self.voice_attempt_paths(commit.attempt_id)
        artifacts = {item.relative_path: item for item in commit.artifacts}
        evidence_paths = {
            path.relative_to(self._project_root)
            for path in (
                paths.request_path,
                paths.preview_path,
                paths.authorization_path,
                paths.submit_intent_path,
                paths.alignment_path,
                paths.cost_path,
                paths.provenance_path,
                paths.outcome_path,
            )
        }
        if not evidence_paths.issubset(artifacts):
            raise _state_invalid("Voice candidate graph is missing durable lifecycle evidence.")
        try:
            voice_request = VoiceGenerationRequest.model_validate_json(
                artifacts[paths.request_path.relative_to(self._project_root)].payload
            )
            preview = VoiceGenerationPreview.model_validate_json(
                artifacts[paths.preview_path.relative_to(self._project_root)].payload
            )
            authorization = VoiceCallAuthorization.model_validate_json(
                artifacts[paths.authorization_path.relative_to(self._project_root)].payload
            )
            cost = VoiceCostReceipt.model_validate_json(
                artifacts[paths.cost_path.relative_to(self._project_root)].payload
            )
            provenance = VoiceProvenanceReceipt.model_validate_json(
                artifacts[paths.provenance_path.relative_to(self._project_root)].payload
            )
            outcome = json.loads(
                artifacts[paths.outcome_path.relative_to(self._project_root)].payload
            )
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            raise _state_invalid("Voice candidate evidence is malformed.", str(exc)) from exc
        receipt = self._voice_receipt(voice_request, preview, authorization)
        if (
            receipt != attempt.voice_request
            or voice_request.base_project != attempt.base_project
            or voice_request.base_registry != attempt.base_registry
            or outcome.get("request_id") != voice_request.request_id
            or outcome.get("request_fingerprint") != voice_request.voice_request_fingerprint
            or outcome.get("preview_fingerprint") != preview.preview_fingerprint
            or outcome.get("authorization_fingerprint")
            != authorization.authorization_fingerprint
            or outcome.get("provider_request_id") != cost.provider_request_id
            or outcome.get("provider_request_id") != provenance.provider_request_id
            or outcome.get("provider_trace_id") != provenance.provider_trace_id
            or outcome.get("terminal_status") != "succeeded"
            or outcome.get("alignment_receipt_sha256")
            != artifacts[paths.alignment_path.relative_to(self._project_root)].file_sha256
        ):
            raise _state_invalid("Voice candidate evidence identity is inconsistent.")
        base_snapshot = _read_regular_file_nofollow(
            self._project_root / attempt.base_registry.path,
            contained_by=self._project_root,
        )
        try:
            base_registry = AssetRegistrySnapshot.model_validate_json(base_snapshot.data)
        except (ValidationError, ValueError) as exc:
            raise _state_invalid("Voice candidate base registry is invalid.", str(exc)) from exc
        if candidate_registry.assets[: len(base_registry.assets)] != base_registry.assets:
            raise _state_invalid("Voice candidate registry mutated or deleted base assets.")
        new_records = candidate_registry.assets[len(base_registry.assets) :]
        expected_ids = set(audio_asset_ids) | set(caption_asset_ids)
        if {item.asset_id for item in new_records} != expected_ids:
            raise _state_invalid("Voice candidate registry contains extra or missing assets.")
        audio_records = tuple(
            item for item in new_records if item.asset_id in audio_asset_ids
        )
        if len(audio_records) != 1:
            raise _state_invalid("Voice candidate graph requires exactly one generated audio asset.")
        audio_record = audio_records[0]
        expected_result_fingerprint = _result_fingerprint(
            {
                "request_id": voice_request.request_id,
                "request_fingerprint": voice_request.voice_request_fingerprint,
                "audio_sha256": audio_record.sha256,
                "content_type": outcome.get("content_type"),
                "provider_request_id": outcome.get("provider_request_id"),
                "provider_trace_id": outcome.get("provider_trace_id"),
                "alignment_receipt_sha256": outcome.get(
                    "alignment_receipt_sha256"
                ),
                "cost_receipt": cost.model_dump(mode="json"),
                "provenance_receipt": provenance.model_dump(mode="json"),
                "terminal_status": outcome.get("terminal_status"),
                "preview_fingerprint": preview.preview_fingerprint,
                "authorization_fingerprint": authorization.authorization_fingerprint,
            }
        )
        metadata = audio_record.audio_metadata
        if (
            outcome.get("result_fingerprint") != expected_result_fingerprint
            or outcome.get("audio_sha256") != audio_record.sha256
            or outcome.get("content_type") != audio_record.mime_type
            or outcome.get("policy_receipt_id") != provenance.policy_receipt_id
            or outcome.get("retention_mode") != provenance.retention_mode
            or audio_record.creation_receipt_id
            != f"voice-result-{expected_result_fingerprint}"
            or audio_record.cost_receipt_id
            != f"cost-{hashlib.sha256(_canonical_json_bytes(cost)).hexdigest()}"
            or audio_record.egress.retention_mode != provenance.retention_mode
            or audio_record.egress.provider_policy_snapshot_id
            != provenance.policy_receipt_id
            or metadata is None
            or metadata.provenance_receipt_id
            != f"provenance-{hashlib.sha256(_canonical_json_bytes(provenance)).hexdigest()}"
            or metadata.alignment_receipt_id
            != f"alignment-{outcome.get('alignment_receipt_sha256')}"
        ):
            raise _state_invalid("Voice candidate result, policy, or registry identity is inconsistent.")
        caption_records = tuple(
            item for item in new_records if item.asset_id in caption_asset_ids
        )
        if len(caption_records) != len(caption_asset_ids):
            raise _state_invalid("Voice candidate caption registry identity is inconsistent.")
        expected_alignment_id = f"alignment-{outcome.get('alignment_receipt_sha256')}"
        expected_caption_receipt = f"caption-result-{expected_result_fingerprint}"
        for caption_record in caption_records:
            caption_artifact = artifacts.get(caption_record.artifact_path)
            caption_metadata = caption_record.caption_metadata
            if caption_artifact is None or caption_metadata is None:
                raise _state_invalid("Voice candidate caption artifact is missing.")
            try:
                track = CaptionTrack.model_validate_json(caption_artifact.payload)
            except (ValidationError, ValueError) as exc:
                raise _state_invalid("Voice candidate caption track is malformed.", str(exc)) from exc
            word_count = sum(len(segment.words or ()) for segment in track.segments)
            metadata_identity = (
                caption_metadata.caption_track_id,
                caption_metadata.language,
                caption_metadata.source_audio_asset_id,
                caption_metadata.source_audio_sha256,
                caption_metadata.script_hash,
                caption_metadata.transcript_hash,
                caption_metadata.segment_count,
                caption_metadata.word_count,
                caption_metadata.segmentation_policy_id,
                caption_metadata.segmentation_policy_version,
                caption_metadata.alignment_receipt_id,
                caption_metadata.timing_fingerprint,
                caption_metadata.style_reference_id,
            )
            track_identity = (
                track.caption_track_id,
                track.language,
                track.source_audio_asset_id,
                track.source_audio_sha256,
                track.script_hash,
                track.transcript_hash,
                len(track.segments),
                word_count,
                track.segmentation_policy.policy_id,
                track.segmentation_policy.policy_version,
                track.alignment_receipt_id,
                track.timing_fingerprint,
                track.style_reference_id,
            )
            if (
                caption_artifact.payload != _canonical_track_bytes(track)
                or not verify_artifact_hash(track)
                or track.timing_fingerprint != caption_timing_fingerprint(track)
                or metadata_identity != track_identity
                or track.source_audio_asset_id != audio_record.asset_id
                or track.source_audio_sha256 != audio_record.sha256
                or track.source_sample_rate_hz != metadata.sample_rate_hz
                or track.script_hash != voice_request.script_hash
                or track.transcript_hash != voice_request.script_hash
                or track.alignment_receipt_id != expected_alignment_id
                or track.alignment_receipt_id != metadata.alignment_receipt_id
                or track.creation_receipt_id != expected_caption_receipt
                or caption_record.creation_receipt_id != track.creation_receipt_id
                or caption_record.input_artifact_ids != (audio_record.asset_id,)
                or caption_record.input_fingerprint != audio_record.sha256
            ):
                raise _state_invalid("Voice candidate caption identity is inconsistent.")
            if caption_metadata.style_reference_id is None:
                if caption_metadata.style_content_hash is not None:
                    raise _state_invalid("Voice candidate caption style identity is inconsistent.")
            else:
                style_hash = caption_metadata.style_content_hash
                style_path = Path(f"assets/styles/{style_hash}.json")
                style_artifact = artifacts.get(style_path)
                if (
                    style_hash is None
                    or style_artifact is None
                    or style_artifact.file_sha256 != style_hash
                    or hashlib.sha256(style_artifact.payload).hexdigest() != style_hash
                ):
                    raise _state_invalid("Voice candidate caption style identity is inconsistent.")
        declared_paths = {item.artifact_path for item in new_records}
        declared_paths.update(
            Path(f"assets/styles/{item.caption_metadata.style_content_hash}.json")
            for item in new_records
            if item.caption_metadata is not None
            and item.caption_metadata.style_content_hash is not None
        )
        exact_paths = evidence_paths | declared_paths | {
            commit.next_project.path,
            commit.next_registry.path,
        }
        if commit.dependency_graph_transition is not None:
            graph_path = commit.dependency_graph_transition.candidate_dependency_graph.path
            if graph_path in artifacts:
                exact_paths.add(graph_path)
        if set(artifacts) != exact_paths:
            raise _state_invalid("Voice candidate graph contains extra or missing artifacts.")
        for record in new_records:
            artifact = artifacts.get(record.artifact_path)
            if (
                artifact is None
                or artifact.file_sha256 != record.sha256
                or len(artifact.payload) != record.size_bytes
            ):
                raise _state_invalid("Voice candidate registry bytes are inconsistent.")
        return outcome.get("provider_request_id")

    def generate_voice_asset(
        self,
        request: VoiceGenerationRequest,
        provider: VoiceAssetProvider,
        authorization: VoiceCallAuthorization,
        *,
        dependency_transition_preparer: VoiceDependencyTransitionPreparer | None = None,
    ) -> ProductionManifest:
        """Only public path allowed to invoke one voice provider transport call."""

        preflight_manifest = self._read_manifest()
        if (
            preflight_manifest.schema_version == "2.3"
            and dependency_transition_preparer is None
        ):
            raise _state_invalid(
                "Manifest 2.3 voice generation requires a dependency transition preparer."
            )

        preview = provider.preview(request)
        self.begin_voice_generation(
            request,
            preview,
            authorization,
            dependency_transition_preparer_available=(
                dependency_transition_preparer is not None
            ),
        )
        permit = self.record_voice_submit_intent(request, preview, authorization)
        try:
            result = provider.generate(request, authorization, permit)
        except AiVideoError as exc:
            if exc.code is ErrorCode.VOICE_PROVIDER_FAILED:
                self.record_voice_failure(
                    request.attempt_id,
                    phase="provider_call",
                    error_code=exc.code.value,
                    error_message=exc.user_message,
                )
            else:
                self.record_voice_outcome_unknown(
                    request.attempt_id,
                    phase="provider_call",
                    error_code=exc.code.value,
                    error_message=exc.user_message,
                )
            raise

        except Exception as exc:
            self.record_voice_outcome_unknown(
                request.attempt_id,
                phase="provider_call",
                error_message=f"Voice transport failed after submit intent: {exc}",
            )
            raise
        self._crash_injector.checkpoint(CommitPhase.AFTER_VOICE_PROVIDER_RESULT)
        try:
            self._validate_voice_provider_result(request, preview, authorization, result)
        except Exception as exc:
            self.record_voice_outcome_unknown(
                request.attempt_id,
                phase="provider_call",
                error_message=f"Voice provider returned contradictory durable evidence: {exc}",
            )
            raise
        if self._voice_candidate_preparer is None:
            self.record_voice_outcome_unknown(
                request.attempt_id,
                phase="materialize",
                error_message="Voice result is durable only in process; candidate preparation is unavailable.",
            )
            raise _state_unsupported(
                "Voice candidate preparation requires an injected local deterministic materializer."
            )
        try:
            prepared = self._voice_candidate_preparer(
                request,
                preview,
                authorization,
                result,
                self.voice_attempt_paths(request.attempt_id),
            )
            commit_request, audio_ids, caption_ids = self._prepare_voice_activation_request(
                request, preview, authorization, result, prepared
            )
            if preflight_manifest.schema_version == "2.3":
                assert dependency_transition_preparer is not None
                prepared_request = dependency_transition_preparer(commit_request)
                if (
                    not isinstance(prepared_request, StateCommitRequest)
                    or prepared_request.attempt_id != commit_request.attempt_id
                    or prepared_request.operation != commit_request.operation
                    or prepared_request.expected_manifest_revision
                    != commit_request.expected_manifest_revision
                    or prepared_request.next_project != commit_request.next_project
                    or prepared_request.next_registry != commit_request.next_registry
                    or prepared_request.dependency_graph_transition is None
                    or not set(commit_request.artifacts).issubset(
                        prepared_request.artifacts
                    )
                ):
                    raise _state_invalid(
                        "Voice dependency transition preparer changed the owned candidate."
                    )
                commit_request = prepared_request
            return self.activate_voice_assets(
                commit_request,
                audio_asset_ids=audio_ids,
                caption_asset_ids=caption_ids,
            )
        except Exception as exc:
            current = self._read_manifest()
            active_attempt = next(
                item for item in current.attempts if item.attempt_id == request.attempt_id
            )
            if active_attempt.status is StateCommitStatus.RUNNING:
                self.record_voice_outcome_unknown(
                    request.attempt_id,
                    phase="materialize",
                    error_message=f"Voice result could not be durably activated: {exc}",
                )
            raise

    def _verify_voice_committed_candidates(self, request: StateCommitRequest) -> None:
        for artifact in request.artifacts:
            snapshot = _read_regular_file_nofollow(
                self._project_root / artifact.relative_path,
                contained_by=self._project_root,
            )
            if snapshot.file_sha256 != artifact.file_sha256:
                raise _state_commit_failed("Voice candidate artifact reopen verification failed.")
        registry_snapshot = _read_regular_file_nofollow(
            self._project_root / request.next_registry.path,
            contained_by=self._project_root,
        )
        try:
            registry = AssetRegistrySnapshot.model_validate_json(registry_snapshot.data)
        except (ValidationError, ValueError) as exc:
            raise _state_commit_failed("Voice candidate registry reopen failed.", str(exc)) from exc
        if (
            registry.revision_id != request.next_registry.revision_id
            or registry.content_hash != request.next_registry.content_hash
            or registry_semantic_sha256(registry) != registry.content_hash
            or registry_snapshot.file_sha256 != request.next_registry.file_sha256
        ):
            raise _state_commit_failed("Voice candidate registry identity is invalid.")

    def render_attempt_paths(self, attempt_id: str) -> RenderAttemptPaths:
        try:
            relative = canonical_render_attempt_root(attempt_id)
        except ValueError as exc:
            raise _state_invalid("Render attempt ID is unsafe.", str(exc)) from exc
        attempt_root = self._project_root / relative
        try:
            attempt_root.relative_to(self._project_root)
        except ValueError as exc:  # pragma: no cover - constructor is already lexical
            raise _state_invalid("Render attempt path escapes the project root.") from exc
        return RenderAttemptPaths(
            attempt_root=attempt_root,
            source_root=attempt_root / "source",
            staged_output_path=attempt_root / "output/render.mp4",
            verification_snapshot_path=attempt_root / "verified.mp4",
        )

    def _ensure_render_attempt_namespace(self) -> Path:
        namespace = self._project_root / "state/render/attempts"
        self._ensure_directory_chain(namespace)
        return namespace

    def begin_render_attempt(
        self, request: BeginRenderAttemptRequest
    ) -> ProductionManifest:
        manifest, _ = self._begin_render_attempt_with_status(request)
        return manifest

    def _begin_render_attempt_with_status(
        self, request: BeginRenderAttemptRequest
    ) -> tuple[ProductionManifest, bool]:
        with self._exclusive_lock():
            manifest = self._read_manifest()
            selection = request.renderer_selection
            self._validate_render_selection(selection, manifest)
            if request.expected_manifest_revision < 1:
                raise _state_invalid("Render attempt expected Manifest revision is invalid.")
            existing = next(
                (item for item in manifest.attempts if item.attempt_id == selection.attempt_id),
                None,
            )
            if existing is not None:
                if not self._same_render_begin(existing, request):
                    raise _state_invalid("Render attempt ID was already used by another request.")
                return manifest, False
            if manifest.manifest_revision != request.expected_manifest_revision:
                raise _state_invalid("Production Manifest revision is stale.")

            if request.base_render_state != manifest.active_render_state:
                raise _state_invalid("Render attempt base state is stale.")
            if any(
                item.status
                in {StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN}
                for item in manifest.attempts
            ):
                raise _state_invalid(
                    "Production state has an unresolved attempt; explicit recovery is required."
                )
            attempt = StateCommitAttempt(
                attempt_id=selection.attempt_id,
                operation="render_state",
                status=StateCommitStatus.RUNNING,
                base_manifest_revision=manifest.manifest_revision,
                base_project=manifest.active_project,
                base_registry=manifest.active_registry,
                candidate_artifacts_hash=hashlib.sha256(b"[]").hexdigest(),
                base_render_state=manifest.active_render_state,
                renderer_selection=selection,
                render_phase="selection",
                started_at=_timestamp(),
            )
            begun = _validated_transition(
                manifest,
                {
                    "schema_version": (
                        "2.1"
                        if manifest.schema_version == "2.0"
                        else manifest.schema_version
                    ),
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": manifest.attempts + (attempt,),
                },
            )
            self._write_manifest_atomic(begun)
            return self._read_manifest(), True

    def _replay_render_attempt(
        self,
        request: BeginRenderAttemptRequest,
        manifest: ProductionManifest,
    ) -> ProductionManifest:
        attempt = next(
            (
                item
                for item in manifest.attempts
                if item.attempt_id == request.renderer_selection.attempt_id
            ),
            None,
        )
        if attempt is None or not self._same_render_begin(attempt, request):
            raise _state_invalid("Render replay does not match its persisted attempt.")
        if attempt.status is StateCommitStatus.FAILED:
            if manifest.active_render_state != attempt.base_render_state:
                raise _state_invalid("Failed render replay base state changed.")
            return manifest
        if attempt.status is StateCommitStatus.SUCCEEDED or (
            attempt.status is StateCommitStatus.RUNNING
            and attempt.candidate_render_state is not None
            and attempt.render_phase == "activate"
        ):
            activation = self._reconstruct_render_activation_request(
                manifest, attempt
            )
            return self.activate_render_state(activation)
        raise _state_invalid(
            "Render replay requires explicit recovery before execution can continue."
        )

    def _reconstruct_render_activation_request(
        self,
        manifest: ProductionManifest,
        attempt: StateCommitAttempt,
    ) -> ActivateRenderStateRequest:
        pointer = attempt.candidate_render_state
        if (
            pointer is None
            or attempt.candidate_project != attempt.base_project
            or attempt.candidate_registry != attempt.base_registry
        ):
            raise _state_invalid("Render replay candidate identity is incomplete.")
        if attempt.status is StateCommitStatus.SUCCEEDED:
            if manifest.active_render_state != pointer:
                raise _state_invalid("Succeeded render replay is not the active state.")
        elif manifest.active_render_state != attempt.base_render_state:
            raise _state_invalid("Candidate render replay no longer has its base state.")
        state = load_verified_render_state(
            self._project_root,
            pointer,
            project=attempt.base_project,
            registry=attempt.base_registry,
        )
        paths = {
            state.timeline.path,
            state.source_bundle.index.path,
            *(item.path for item in state.source_bundle.assets),
            state.source_receipt.path,
            state.render_receipt.path,
            state.output.path,
            pointer.path,
        }
        artifacts = tuple(
            PreparedArtifact(
                relative_path=path,
                payload=snapshot.data,
                file_sha256=snapshot.file_sha256,
            )
            for path in sorted(paths)
            for snapshot in (
                _read_regular_file_nofollow(
                    self._project_root / path,
                    contained_by=self._project_root,
                ),
            )
        )
        transition = None
        if attempt.candidate_dependency_graph is not None:
            if (
                attempt.base_dependency_graph is None
                or attempt.candidate_dependency_states_hash is None
                or manifest.active_dependency_graph
                != attempt.candidate_dependency_graph
                or _dependency_states_hash(manifest.dependency_states)
                != attempt.candidate_dependency_states_hash
            ):
                raise _state_invalid(
                    "Render replay dependency transition identity is incomplete."
                )
            transition = DependencyGraphTransition(
                expected_manifest_revision=attempt.base_manifest_revision + 1,
                base_dependency_graph=attempt.base_dependency_graph,
                candidate_dependency_graph=attempt.candidate_dependency_graph,
                candidate_dependency_states=manifest.dependency_states,
                candidate_dependency_states_hash=attempt.candidate_dependency_states_hash,
            )
            if _candidate_artifacts_hash(artifacts) != attempt.candidate_artifacts_hash:
                graph_snapshot = _read_regular_file_nofollow(
                    self._project_root / attempt.candidate_dependency_graph.path,
                    contained_by=self._project_root / "state",
                )
                artifacts = tuple(
                    sorted(
                        (
                            *artifacts,
                            PreparedArtifact(
                                attempt.candidate_dependency_graph.path,
                                graph_snapshot.data,
                                graph_snapshot.file_sha256,
                            ),
                        ),
                        key=lambda item: item.relative_path.as_posix(),
                    )
                )
        if _candidate_artifacts_hash(artifacts) != attempt.candidate_artifacts_hash:
            raise _state_invalid("Render replay artifact identity is invalid.")
        selection = attempt.renderer_selection
        if selection is None:  # pragma: no cover - enforced by StateCommitAttempt
            raise _state_invalid("Render replay selection identity is missing.")
        return ActivateRenderStateRequest(
            attempt_id=attempt.attempt_id,
            expected_manifest_revision=attempt.base_manifest_revision + 1,
            current_project=attempt.base_project,
            current_registry=attempt.base_registry,
            base_render_state=attempt.base_render_state,
            renderer_selection=selection,
            artifacts=artifacts,
            next_render_state=pointer,
            dependency_graph_transition=transition,
        )

    def record_render_failure(
        self, request: RecordRenderFailureRequest
    ) -> ProductionManifest:
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if (
                not request.error_code
                or not request.error_message
                or request.phase not in {"source", "lint", "check", "render", "verify"}
            ):
                raise _state_invalid("Render failure request requires typed error detail.")
            self._validate_render_selection(request.renderer_selection, manifest)
            if (
                request.attempt_id != request.renderer_selection.attempt_id
                or request.current_project != manifest.active_project
                or request.current_registry != manifest.active_registry
                or request.base_render_state != manifest.active_render_state
            ):
                raise _state_invalid("Render failure request does not match active state.")
            existing = next(
                (item for item in manifest.attempts if item.attempt_id == request.attempt_id),
                None,
            )
            if existing is None or not self._same_render_begin(
                existing,
                BeginRenderAttemptRequest(
                    expected_manifest_revision=existing.base_manifest_revision if existing else 0,
                    base_render_state=request.base_render_state,
                    renderer_selection=request.renderer_selection,
                ),
            ):
                raise _state_invalid("Render failure does not match a begun attempt.")
            redacted = _redact_render_error_message(request.error_message)
            if existing.status is StateCommitStatus.FAILED:
                if (
                    existing.candidate_render_state is None
                    and existing.render_phase == request.phase
                    and existing.error_code == request.error_code
                    and existing.error_message == redacted
                ):
                    return manifest
                raise _state_invalid("Render failure replay does not match terminal state.")
            if (
                manifest.manifest_revision != request.expected_manifest_revision
                or existing.status is not StateCommitStatus.RUNNING
                or existing.candidate_render_state is not None
                or existing.render_phase != "selection"
            ):
                raise _state_invalid("Render failure request is stale or activation already began.")
            failed = _validated_transition(
                existing,
                {
                    "status": StateCommitStatus.FAILED,
                    "render_phase": request.phase,
                    "finished_at": _timestamp(),
                    "error_code": request.error_code,
                    "error_message": redacted,
                },
            )
            terminal = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        failed if item.attempt_id == request.attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(terminal)
            return self._read_manifest()

    def activate_render_state(
        self, request: ActivateRenderStateRequest
    ) -> ProductionManifest:
        """Promote one exact render graph and atomically select its state pointer."""
        candidate_replaced = False
        final_replaced = False
        with self._exclusive_lock():
            manifest = self._read_manifest()
            candidate_hash = _candidate_artifacts_evidence_hash(request.artifacts)
            existing = next(
                (item for item in manifest.attempts if item.attempt_id == request.attempt_id),
                None,
            )
            if existing is None or not self._render_activation_identity(
                existing, request, candidate_hash
            ):
                raise _state_invalid("Render activation does not match its begun attempt.")
            graph_transition: DependencyGraphTransition | None = None
            candidate_graph: DependencyGraphSnapshot | None = None
            if existing.status is StateCommitStatus.SUCCEEDED:
                transition = request.dependency_graph_transition
                if manifest.schema_version == "2.3":
                    if transition is None or (
                        existing.base_dependency_graph
                        != transition.base_dependency_graph
                        or existing.candidate_dependency_graph
                        != transition.candidate_dependency_graph
                        or existing.candidate_dependency_states_hash
                        != transition.candidate_dependency_states_hash
                        or manifest.active_dependency_graph
                        != transition.candidate_dependency_graph
                        or manifest.dependency_states
                        != transition.candidate_dependency_states
                    ):
                        raise _state_invalid(
                            "Succeeded render replay dependency transition does not match active state."
                        )
                    active_graph = self._reopen_dependency_graph(
                        transition.candidate_dependency_graph
                    )
                    self._verify_dependency_candidate(
                        manifest, active_graph, manifest.dependency_states
                    )
                elif transition is not None:
                    raise _state_invalid(
                        "Dependency graph transition requires Manifest 2.3."
                    )
                self._verify_durable_render_graph(request)
                if (
                    manifest.active_project != request.current_project
                    or manifest.active_registry != request.current_registry
                    or manifest.active_render_state != request.next_render_state
                ):
                    raise _state_invalid(
                        "Succeeded render replay does not match active state."
                    )
                return manifest
            graph_transition, candidate_graph = self._validate_dependency_transition(
                manifest,
                expected_manifest_revision=request.expected_manifest_revision,
                artifacts=request.artifacts,
                transition=request.dependency_graph_transition,
            )
            if existing.status is StateCommitStatus.FAILED:
                self._validate_render_artifacts(request)
                if (
                    manifest.active_project != request.current_project
                    or manifest.active_registry != request.current_registry
                    or manifest.active_render_state != request.base_render_state
                ):
                    raise _state_invalid(
                        "Failed render replay does not match its base state."
                    )
                return manifest
            if existing.status is not StateCommitStatus.RUNNING:
                raise _state_invalid("Render activation requires explicit recovery.")
            if (
                request.current_project != manifest.active_project
                or request.current_registry != manifest.active_registry
                or request.base_render_state != manifest.active_render_state
            ):
                raise _state_invalid("Render activation active provenance changed.")
            if (
                existing.candidate_render_state is None
                and manifest.manifest_revision != request.expected_manifest_revision
            ):
                raise _state_invalid("Render activation Manifest revision is stale.")

            begun_manifest = manifest
            candidate_attempt = (
                existing
                if existing.candidate_render_state is not None
                else _validated_transition(
                    existing,
                    {
                        "candidate_project": request.current_project,
                        "candidate_registry": request.current_registry,
                        "candidate_render_state": request.next_render_state,
                        "candidate_artifacts_hash": candidate_hash,
                        "render_phase": "activate",
                        "base_dependency_graph": (
                            None
                            if graph_transition is None
                            else graph_transition.base_dependency_graph
                        ),
                        "candidate_dependency_graph": (
                            None
                            if graph_transition is None
                            else graph_transition.candidate_dependency_graph
                        ),
                        "candidate_dependency_states_hash": (
                            None
                            if graph_transition is None
                            else graph_transition.candidate_dependency_states_hash
                        ),
                    },
                )
            )
            candidate_manifest: ProductionManifest | None = None
            try:
                _candidate_artifacts_hash(request.artifacts)
                state = self._validate_render_artifacts(request)
                if (
                    state.project != manifest.active_project
                    or state.registry != manifest.active_registry
                ):
                    raise _state_invalid(
                        "Render activation artifact provenance changed."
                    )
                if existing.candidate_render_state is None:
                    for artifact in request.artifacts:
                        if (
                            graph_transition is not None
                            and artifact.relative_path
                            == graph_transition.candidate_dependency_graph.path
                        ):
                            self._write_immutable_artifact(
                                artifact,
                                attempt_id=request.attempt_id,
                                dependency_graph=True,
                            )
                        else:
                            self._write_render_immutable_artifact(
                                artifact, attempt_id=request.attempt_id
                            )
                        snapshot = _read_regular_file_nofollow(
                            self._project_root / artifact.relative_path,
                            contained_by=self._project_root,
                        )
                        if snapshot.file_sha256 != artifact.file_sha256:
                            raise _state_commit_failed(
                                "Immutable render artifact verification failed."
                            )
                self._verify_durable_render_graph(request)
                if graph_transition is not None and candidate_graph is not None:
                    self._verify_render_dependency_application(
                        candidate_graph,
                        graph_transition.candidate_dependency_states,
                        request.next_render_state,
                    )

                if existing.candidate_render_state is None:
                    candidate_manifest = _validated_transition(
                        manifest,
                        {
                            "manifest_revision": manifest.manifest_revision + 1,
                            "attempts": tuple(
                                candidate_attempt
                                if item.attempt_id == request.attempt_id
                                else item
                                for item in manifest.attempts
                            ),
                        },
                    )

                    def mark_candidate_replaced() -> None:
                        nonlocal candidate_replaced
                        candidate_replaced = True

                    self._write_render_manifest_atomic(
                        candidate_manifest,
                        candidate=True,
                        on_replace=mark_candidate_replaced,
                    )
                    manifest = self._read_manifest()
                    existing = next(
                        item
                        for item in manifest.attempts
                        if item.attempt_id == request.attempt_id
                    )
                else:
                    candidate_attempt = existing
                    candidate_manifest = manifest
                    if (
                        existing.candidate_render_state != request.next_render_state
                        or existing.candidate_artifacts_hash != candidate_hash
                        or existing.render_phase != "activate"
                    ):
                        raise _state_invalid("Render candidate replay identity is invalid.")

                succeeded = _validated_transition(
                    candidate_attempt,
                    {
                        "status": StateCommitStatus.SUCCEEDED,
                        "finished_at": _timestamp(),
                        "error_code": None,
                        "error_message": None,
                    },
                )
                if graph_transition is not None and candidate_graph is not None:
                    verification_attempts = tuple(
                        succeeded if item.attempt_id == request.attempt_id else item
                        for item in manifest.attempts
                    )
                    self._verify_dependency_candidate(
                        manifest,
                        candidate_graph,
                        graph_transition.candidate_dependency_states,
                        render_pointer=request.next_render_state,
                        attempts=verification_attempts,
                    )
                final_update: dict[str, object] = {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "active_render_state": request.next_render_state,
                    "attempts": tuple(
                        succeeded if item.attempt_id == request.attempt_id else item
                        for item in manifest.attempts
                    ),
                }
                if manifest.schema_version == "2.4":
                    final_update.update(
                        {
                            "active_review_receipts": (),
                            "review_states": tuple(
                                item.model_copy(
                                    update={
                                        "lifecycle": ReviewLifecycle.STALE,
                                        "active_receipt": None,
                                    }
                                )
                                for item in manifest.review_states
                            ),
                            "final_acceptance_state": None,
                        }
                    )
                if graph_transition is not None:
                    final_update.update(
                        {
                            "active_dependency_graph": graph_transition.candidate_dependency_graph,
                            "dependency_states": graph_transition.candidate_dependency_states,
                        }
                    )
                final_manifest = _validated_transition(
                    manifest,
                    final_update,
                )

                def mark_final_replaced() -> None:
                    nonlocal final_replaced
                    final_replaced = True
                    if graph_transition is not None:
                        self._crash_injector.checkpoint(
                            CommitPhase.AFTER_GRAPH_FINAL_MANIFEST_REPLACE
                        )

                self._write_render_manifest_atomic(
                    final_manifest,
                    candidate=False,
                    on_replace=mark_final_replaced,
                )
                authoritative = self._read_manifest()
                if authoritative != final_manifest:
                    raise _state_commit_failed(
                        "Final render Manifest verification failed."
                    )
                return authoritative
            except Exception as exc:
                if final_replaced:
                    raise _outcome_unknown(exc) from exc
                primary = _as_state_error(exc)
                try:
                    authoritative = self._read_manifest()
                except Exception as reopen_error:
                    raise _outcome_unknown(reopen_error) from reopen_error
                current_attempt = next(
                    (
                        item
                        for item in authoritative.attempts
                        if item.attempt_id == request.attempt_id
                    ),
                    None,
                )
                if current_attempt is None:
                    raise _outcome_unknown(exc) from exc
                if current_attempt.status is StateCommitStatus.FAILED:
                    raise primary from exc
                expected_candidate = candidate_attempt
                candidate_is_authoritative = (
                    expected_candidate is not None
                    and current_attempt == expected_candidate
                    and authoritative.active_render_state
                    == request.base_render_state
                    and authoritative.manifest_revision
                    == begun_manifest.manifest_revision + 1
                )
                if candidate_replaced or candidate_is_authoritative:
                    if (
                        expected_candidate is None
                        or current_attempt != expected_candidate
                        or authoritative.active_render_state != request.base_render_state
                    ):
                        raise _outcome_unknown(exc) from exc
                elif (
                    current_attempt != existing
                    or authoritative.manifest_revision
                    != begun_manifest.manifest_revision
                    or authoritative.active_render_state != request.base_render_state
                ):
                    raise _outcome_unknown(exc) from exc
                failed = _validated_transition(
                    current_attempt,
                    {
                        "candidate_project": request.current_project,
                        "candidate_registry": request.current_registry,
                        "candidate_render_state": request.next_render_state,
                        "candidate_artifacts_hash": candidate_hash,
                        "render_phase": "activate",
                        "status": StateCommitStatus.FAILED,
                        "finished_at": _timestamp(),
                        "error_code": primary.code.value,
                        "error_message": _redact_render_error_message(
                            primary.user_message
                        ),
                    },
                )
                terminal = _validated_transition(
                    authoritative,
                    {
                        "manifest_revision": authoritative.manifest_revision + 1,
                        "attempts": tuple(
                            failed if item.attempt_id == request.attempt_id else item
                            for item in authoritative.attempts
                        ),
                    },
                )
                try:
                    self._write_manifest_atomic(terminal)
                    if self._read_manifest() != terminal:
                        raise _state_commit_failed(
                            "Render activation failure Manifest did not persist."
                        )
                except BaseException as persist_error:
                    if _is_process_exception(persist_error):
                        raise
                    raise _outcome_unknown(persist_error) from persist_error
                raise primary from exc

    def _write_render_manifest_atomic(
        self,
        manifest: ProductionManifest,
        *,
        candidate: bool,
        on_replace: Callable[[], None],
    ) -> None:
        final_path = self._state_directory() / "manifest.json"
        temp_name = (
            ".p2a-render-candidate-manifest.tmp"
            if candidate
            else ".p2a-render-final-manifest.tmp"
        )
        temp_path = final_path.parent / temp_name
        primary: BaseException | None = None
        try:
            if candidate:
                self._crash_injector.checkpoint(
                    CommitPhase.BEFORE_RENDER_CANDIDATE_MANIFEST_SERIALIZATION
                )
            payload = _canonical_json_bytes(manifest)
            with self._ops.open_exclusive(temp_path) as handle:
                if candidate:
                    self._crash_injector.checkpoint(
                        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_OPEN
                    )
                handle.write(payload)
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_WRITE
                    if candidate
                    else CommitPhase.AFTER_RENDER_FINAL_MANIFEST_TEMP_WRITE
                )
                handle.flush()
                self._ops.fsync_file(handle, temp_path)
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_FILE_FSYNC
                    if candidate
                    else CommitPhase.AFTER_RENDER_FINAL_MANIFEST_FILE_FSYNC
                )
            self._crash_injector.checkpoint(
                CommitPhase.BEFORE_RENDER_CANDIDATE_MANIFEST_REPLACE
                if candidate
                else CommitPhase.BEFORE_RENDER_FINAL_MANIFEST_REPLACE
            )
            self._validate_final_path(final_path)
            self._ops.replace(temp_path, final_path)
            on_replace()
            self._crash_injector.checkpoint(
                CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_REPLACE
                if candidate
                else CommitPhase.AFTER_RENDER_FINAL_MANIFEST_REPLACE
            )
            self._ops.fsync_directory(final_path.parent)
            self._crash_injector.checkpoint(
                CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_DIRECTORY_FSYNC
                if candidate
                else CommitPhase.AFTER_RENDER_FINAL_MANIFEST_DIRECTORY_FSYNC
            )
            if self._read_manifest() != manifest:
                raise _state_commit_failed("Render Manifest reopen verification failed.")
            if candidate:
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_VERIFICATION
                )
        except BaseException as exc:
            primary = exc
            raise
        finally:
            if primary is not None:
                try:
                    self._validate_cleanup_temp_path(temp_path)
                    self._ops.unlink(temp_path, missing_ok=True)
                except BaseException as cleanup_error:
                    primary.add_note(
                        f"Render Manifest temporary cleanup failed: {cleanup_error}"
                    )

    def _write_render_immutable_artifact(
        self, artifact: PreparedArtifact, *, attempt_id: str
    ) -> Path:
        expected = hashlib.sha256(artifact.payload).hexdigest()
        if expected != artifact.file_sha256:
            raise _state_invalid("Prepared render artifact hash is invalid.")
        relative = self._validate_artifact_path(artifact.relative_path)
        final_path = self._project_root / relative
        self._ensure_parent_directory(final_path.parent)
        temp_name = _owned_temp_name(attempt_id, final_path)
        primary: BaseException | None = None
        with _open_directory_nofollow(
            final_path.parent, contained_by=self._project_root
        ) as parent_fd:
            temp_fd: int | None = None
            try:
                temp_fd = os.open(
                    temp_name,
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent_fd,
                )
                view = memoryview(artifact.payload)
                while view:
                    written = os.write(temp_fd, view)
                    view = view[written:]
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_ARTIFACT_TEMP_WRITE
                )
                os.fsync(temp_fd)
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_ARTIFACT_FILE_FSYNC
                )
                try:
                    os.link(
                        temp_name,
                        final_path.name,
                        src_dir_fd=parent_fd,
                        dst_dir_fd=parent_fd,
                        follow_symlinks=False,
                    )
                except FileExistsError:
                    existing_fd = os.open(
                        final_path.name,
                        os.O_RDONLY
                        | getattr(os, "O_NOFOLLOW", 0)
                        | getattr(os, "O_NONBLOCK", 0),
                        dir_fd=parent_fd,
                    )
                    try:
                        if not stat.S_ISREG(os.fstat(existing_fd).st_mode):
                            raise _state_commit_failed(
                                "Immutable render path is not a regular file."
                            )
                        digest = hashlib.sha256()
                        while chunk := os.read(existing_fd, 1024 * 1024):
                            digest.update(chunk)
                        if digest.hexdigest() != expected:
                            raise _state_commit_failed(
                                "Immutable render path already has different bytes."
                            )
                    finally:
                        os.close(existing_fd)
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_ARTIFACT_PROMOTION
                )
                os.fsync(parent_fd)
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_ARTIFACT_DIRECTORY_FSYNC
                )
                verified_fd = os.open(
                    final_path.name,
                    os.O_RDONLY
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_NONBLOCK", 0),
                    dir_fd=parent_fd,
                )
                try:
                    if not stat.S_ISREG(os.fstat(verified_fd).st_mode):
                        raise _state_commit_failed(
                            "Immutable render artifact is not a regular file."
                        )
                    digest = hashlib.sha256()
                    while chunk := os.read(verified_fd, 1024 * 1024):
                        digest.update(chunk)
                    if digest.hexdigest() != expected:
                        raise _state_commit_failed(
                            "Immutable render artifact verification failed."
                        )
                finally:
                    os.close(verified_fd)
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_ARTIFACT_VERIFICATION
                )
                return final_path
            except AiVideoError as exc:
                primary = exc
                raise
            except BaseException as exc:
                if not isinstance(exc, Exception):
                    primary = exc
                    raise
                primary = _state_commit_failed(
                    "Could not promote immutable render artifact.", str(exc)
                )
                raise primary from exc
            finally:
                if temp_fd is not None:
                    try:
                        os.close(temp_fd)
                    except BaseException as cleanup_error:
                        if primary is not None:
                            primary.add_note(
                                f"Render artifact temp close failed: {cleanup_error}"
                            )
                try:
                    os.unlink(temp_name, dir_fd=parent_fd)
                except FileNotFoundError:
                    pass
                except BaseException as cleanup_error:
                    if primary is not None:
                        primary.add_note(
                            f"Render artifact temp cleanup failed: {cleanup_error}"
                        )
                    else:
                        raise

    @staticmethod
    def _render_activation_identity(
        attempt: StateCommitAttempt,
        request: ActivateRenderStateRequest,
        candidate_hash: str,
    ) -> bool:
        if (
            attempt.operation != "render_state"
            or attempt.base_manifest_revision != request.expected_manifest_revision - 1
            or attempt.base_project != request.current_project
            or attempt.base_registry != request.current_registry
            or attempt.base_render_state != request.base_render_state
            or attempt.renderer_selection != request.renderer_selection
        ):
            return False
        if attempt.candidate_render_state is None:
            return attempt.render_phase == "selection"
        transition = request.dependency_graph_transition
        return (
            attempt.candidate_project == request.current_project
            and attempt.candidate_registry == request.current_registry
            and attempt.candidate_render_state == request.next_render_state
            and attempt.candidate_artifacts_hash == candidate_hash
            and attempt.render_phase == "activate"
            and (
                (
                    transition is None
                    and attempt.base_dependency_graph is None
                    and attempt.candidate_dependency_graph is None
                    and attempt.candidate_dependency_states_hash is None
                )
                or (
                    transition is not None
                    and attempt.base_dependency_graph
                    == transition.base_dependency_graph
                    and attempt.candidate_dependency_graph
                    == transition.candidate_dependency_graph
                    and attempt.candidate_dependency_states_hash
                    == transition.candidate_dependency_states_hash
                )
            )
        )

    @staticmethod
    def _verify_render_dependency_application(
        graph: DependencyGraphSnapshot,
        states: tuple[DependencyNodeState, ...],
        pointer: RenderStateSnapshotPointer,
    ) -> None:
        state_by_id = {state.node_id: state for state in states}
        unit_nodes = tuple(
            node
            for node in graph.nodes
            if node.kind
            in {
                DependencyNodeKind.COMPOSITION_SPEC,
                DependencyNodeKind.RESOLVED_TIMELINE,
                DependencyNodeKind.RENDERER_SOURCE,
                DependencyNodeKind.RENDER,
            }
        )
        required_kinds = {
            DependencyNodeKind.COMPOSITION_SPEC,
            DependencyNodeKind.RESOLVED_TIMELINE,
            DependencyNodeKind.RENDERER_SOURCE,
            DependencyNodeKind.RENDER,
        }
        if len(unit_nodes) != 4 or {node.kind for node in unit_nodes} != required_kinds:
            raise _state_invalid(
                "Render dependency graph has an incomplete atomic render unit."
            )
        for node in unit_nodes:
            state = state_by_id.get(node.node_id)
            evidence = None if state is None else state.applied_evidence
            if (
                state is None
                or state.lifecycle is not DependencyLifecycle.FRESH
                or state.applied_fingerprint != state.desired_fingerprint
                or not isinstance(evidence, RenderDependencyEvidence)
                or evidence.pointer != pointer
                or evidence.artifact_id != node.artifact_id
            ):
                raise _state_invalid(
                    "Composition, timeline, renderer source and render nodes must "
                    "be atomically applied."
                )

    @staticmethod
    def _same_render_begin(
        attempt: StateCommitAttempt, request: BeginRenderAttemptRequest
    ) -> bool:
        return (
            attempt.operation == "render_state"
            and attempt.base_manifest_revision == request.expected_manifest_revision
            and attempt.base_render_state == request.base_render_state
            and attempt.renderer_selection == request.renderer_selection
        )

    @staticmethod
    def _validate_render_selection(
        selection: RendererSelectionReceipt, manifest: ProductionManifest
    ) -> None:
        try:
            canonical_render_attempt_root(selection.attempt_id)
        except ValueError as exc:
            raise _state_invalid("Renderer selection attempt ID is unsafe.", str(exc)) from exc
        if (
            selection.requested_kind.value != "hyperframes"
            or selection.selected_kinds != (selection.requested_kind,)
            or selection.renderer_version != "0.7.103"
            or selection.current_project != manifest.active_project
            or selection.current_registry != manifest.active_registry
        ):
            raise _state_invalid("Renderer selection does not match active production state.")

    def _validate_render_artifacts(
        self, request: ActivateRenderStateRequest
    ) -> RenderStateSnapshot:
        if request.attempt_id != request.renderer_selection.attempt_id:
            raise _state_invalid("Render activation attempt identity is invalid.")
        if request.expected_manifest_revision < 2:
            raise _state_invalid("Render activation expected revision is invalid.")
        graph_path = (
            request.dependency_graph_transition.candidate_dependency_graph.path
            if request.dependency_graph_transition is not None
            else None
        )
        render_artifacts = tuple(
            item for item in request.artifacts if item.relative_path != graph_path
        )
        paths = tuple(item.relative_path for item in render_artifacts)
        if paths != tuple(sorted(paths)):
            raise _state_invalid("Render activation artifacts must be canonically sorted.")
        artifacts: dict[Path, PreparedArtifact] = {}
        for item in render_artifacts:
            path = self._validate_artifact_path(item.relative_path)
            if path in artifacts:
                raise _state_invalid("Render activation has duplicate artifact paths.")
            if hashlib.sha256(item.payload).hexdigest() != item.file_sha256:
                raise _state_invalid("Render activation artifact hash is invalid.")
            artifacts[path] = item

        state_artifact = artifacts.get(request.next_render_state.path)
        if (
            state_artifact is None
            or state_artifact.file_sha256 != request.next_render_state.file_sha256
        ):
            raise _state_invalid("Render state pointer does not match its artifact.")
        state = self._parse_render_model(
            state_artifact.payload, RenderStateSnapshot, "render state"
        )
        if (
            not verify_artifact_hash(state)
            or state.revision != request.next_render_state.revision
            or state.content_hash != request.next_render_state.content_hash
            or canonical_render_state_path(state.content_hash)
            != request.next_render_state.path
            or state.project != request.current_project
            or state.registry != request.current_registry
            or state.renderer_selection != request.renderer_selection
            or state.attempt_id != request.attempt_id
        ):
            raise _state_invalid("Render state artifact identity is invalid.")

        timeline_artifact = self._require_render_artifact(
            artifacts, state.timeline.path, state.timeline.file_sha256
        )
        timeline = self._parse_render_model(
            timeline_artifact.payload, ResolvedTimeline, "resolved timeline"
        )
        source_artifact = self._require_render_artifact(
            artifacts, state.source_receipt.path, state.source_receipt.file_sha256
        )
        source = self._parse_render_model(
            source_artifact.payload, RendererSourceReceipt, "renderer source receipt"
        )
        render_artifact = self._require_render_artifact(
            artifacts, state.render_receipt.path, state.render_receipt.file_sha256
        )
        render = self._parse_render_model(
            render_artifact.payload, RenderReceipt, "render receipt"
        )
        if not all(verify_artifact_hash(item) for item in (timeline, source, render)):
            raise _state_invalid("Render artifact semantic hash is invalid.")
        if (
            timeline.revision != state.timeline.revision
            or timeline.content_hash != state.timeline.content_hash
            or state.timeline.path != canonical_render_timeline_path(timeline.content_hash)
            or source.revision != state.source_receipt.revision
            or source.content_hash != state.source_receipt.content_hash
            or state.source_receipt.path
            != canonical_renderer_source_receipt_path(source.content_hash)
            or render.revision != state.render_receipt.revision
            or render.content_hash != state.render_receipt.content_hash
            or state.render_receipt.path
            != canonical_render_receipt_path(render.content_hash)
        ):
            raise _state_invalid("Render artifact pointer identity is invalid.")

        bundle = state.source_bundle
        expected_root = canonical_render_source_root(bundle.bundle_sha256)
        if (
            source.source_bundle != bundle
            or bundle.root_path != expected_root
            or bundle.index.path
            != canonical_render_source_index_path(bundle.bundle_sha256)
            or _bundle_hash_from_pointers(bundle) != bundle.bundle_sha256
        ):
            raise _state_invalid("Render source bundle identity is invalid.")
        index = self._require_render_artifact(
            artifacts, bundle.index.path, bundle.index.file_sha256
        )
        if len(index.payload) != bundle.index.size_bytes:
            raise _state_invalid("Render source index size is invalid.")
        try:
            binding_map = _render_source_binding_map(source)
            _validate_source_timeline_bindings(source, timeline)
        except ValueError as exc:
            raise _state_invalid("Render source bindings are invalid.", str(exc)) from exc
        pointer_by_path = {item.path: item for item in bundle.assets}
        if len(pointer_by_path) != len(bundle.assets):
            raise _state_invalid("Render source bundle contains duplicate asset paths.")
        for path, (_, digest, _) in binding_map.items():
            pointer = pointer_by_path.get(path)
            if pointer is None or digest != pointer.file_sha256:
                raise _state_invalid(
                    "Render source binding hash does not match its bundle pointer."
                )
        if set(binding_map) != {item.path for item in bundle.assets}:
            raise _state_invalid("Render source bindings do not match bundle assets.")
        for pointer in bundle.assets:
            suffix = pointer.path.suffix
            if pointer.path != canonical_render_source_asset_path(
                bundle.bundle_sha256, pointer.file_sha256, suffix
            ):
                raise _state_invalid("Render source asset path is noncanonical.")
            artifact = self._require_render_artifact(
                artifacts, pointer.path, pointer.file_sha256
            )
            role, _, binding = binding_map[pointer.path]
            if len(artifact.payload) != pointer.size_bytes or not _render_source_payload_matches(
                artifact.payload,
                suffix=suffix,
                role=role,
                binding=binding,
                timeline=timeline,
            ):
                raise _state_invalid("Render source asset type or bytes are invalid.")

        output = self._require_render_artifact(
            artifacts, state.output.path, state.output.file_sha256
        )
        if (
            state.output.path != canonical_render_output_path(state.output.file_sha256)
            or len(output.payload) != state.output.size_bytes
            or render.output_path != state.output.path
            or render.output_sha256 != state.output.file_sha256
            or render.output_size_bytes != state.output.size_bytes
        ):
            raise _state_invalid("Render output identity is invalid.")
        if (
            source.attempt_id != state.attempt_id
            or render.attempt_id != state.attempt_id
            or timeline.composition_fingerprint != state.timeline_fingerprint
            or source.timeline_fingerprint != state.timeline_fingerprint
            or render.timeline_fingerprint != state.timeline_fingerprint
            or timeline.renderer != state.renderer
            or source.renderer != state.renderer
            or render.renderer != state.renderer
            or source.source_sha256 != state.source_sha256
            or render.source_sha256 != state.source_sha256
            or source.source_bundle.bundle_sha256 != state.source_bundle_sha256
            or render.source_bundle_sha256 != state.source_bundle_sha256
            or render.asset_hashes != state.asset_hashes
        ):
            raise _state_invalid("Render artifact graph contains mixed provenance.")
        expected_paths = {
            state.timeline.path,
            bundle.index.path,
            *(item.path for item in bundle.assets),
            state.source_receipt.path,
            state.render_receipt.path,
            state.output.path,
            request.next_render_state.path,
        }
        if set(artifacts) != expected_paths or len(artifacts) != len(bundle.assets) + 6:
            raise _state_invalid("Render activation artifact set is not exact.")
        return state

    @staticmethod
    def _parse_render_model(
        payload: bytes, model_type: type[BaseModel], label: str
    ) -> BaseModel:
        try:
            return model_type.model_validate_json(payload)
        except (ValidationError, ValueError) as exc:
            raise _state_invalid(f"Could not validate {label} artifact.", str(exc)) from exc

    @staticmethod
    def _require_render_artifact(
        artifacts: dict[Path, PreparedArtifact], path: Path, expected_hash: str
    ) -> PreparedArtifact:
        item = artifacts.get(path)
        if item is None or item.file_sha256 != expected_hash:
            raise _state_invalid("Render artifact pointer does not match prepared bytes.")
        return item

    def _verify_durable_render_graph(self, request: ActivateRenderStateRequest) -> None:
        for artifact in request.artifacts:
            snapshot = _read_regular_file_nofollow(
                self._project_root / artifact.relative_path,
                contained_by=self._project_root,
            )
            if snapshot.file_sha256 != artifact.file_sha256:
                raise _state_commit_failed("Durable render artifact changed after promotion.")
        state = self._validate_render_artifacts(request)
        loaded = load_verified_render_state(
            self._project_root,
            request.next_render_state,
            project=request.current_project,
            registry=request.current_registry,
        )
        if loaded != state:
            raise _state_commit_failed(
                "Durable render graph reopen verification failed."
            )

    def prepare_artifact(
        self,
        attempt_id: str,
        relative_path: str | Path,
        payload: bytes,
    ) -> PreparedArtifact:
        if not attempt_id:
            raise _state_invalid("State commit attempt ID must not be empty.")
        if not isinstance(payload, bytes):
            raise _state_invalid("Production artifact payload must be bytes.")
        clean_path = self._validate_artifact_path(Path(relative_path))
        return PreparedArtifact(
            relative_path=clean_path,
            payload=payload,
            file_sha256=hashlib.sha256(payload).hexdigest(),
        )

    @contextmanager
    def _exclusive_lock(self) -> Iterator[BinaryIO]:
        if fcntl is None:
            raise _state_unsupported("Production state commits require POSIX fcntl locking.")
        state_dir = self._state_directory()
        lock_path = state_dir / "commit.lock"
        self._reject_symlink(lock_path)
        try:
            handle = lock_path.open("a+b")
        except OSError as exc:
            raise _state_commit_failed("Could not open production state commit lock.", str(exc)) from exc
        acquired = False
        primary: BaseException | None = None
        try:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                primary = AiVideoError(
                    code=ErrorCode.PRODUCTION_STATE_BUSY,
                    user_message="Production state commit is already in progress.",
                    technical_detail=str(exc),
                    retryable=False,
                )
                raise primary from exc
            except OSError as exc:
                if exc.errno in {errno.EACCES, errno.EAGAIN}:
                    primary = AiVideoError(
                        code=ErrorCode.PRODUCTION_STATE_BUSY,
                        user_message="Production state commit is already in progress.",
                        technical_detail=str(exc),
                        retryable=False,
                    )
                    raise primary from exc
                primary = _state_unsupported("POSIX state locking is unavailable.", str(exc))
                raise primary from exc
            acquired = True
            try:
                yield handle
            except BaseException as exc:
                primary = exc
                raise
        finally:
            cleanup_errors: list[BaseException] = []
            if acquired:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                except BaseException as exc:
                    cleanup_errors.append(exc)
            try:
                handle.close()
            except BaseException as exc:
                cleanup_errors.append(exc)
            _handle_cleanup_errors(
                primary,
                cleanup_errors,
                label="Production state lock cleanup",
                no_primary_message="Production state lock cleanup failed.",
            )

    def commit(self, request: StateCommitRequest) -> ProductionManifest:
        """Durably select a project and registry in one Manifest transition."""
        final_manifest_replaced = [False]
        try:
            return self._commit_locked(request, final_manifest_replaced)
        except Exception as exc:
            if final_manifest_replaced[0]:
                raise _outcome_unknown(exc) from exc
            raise
        except BaseException as exc:
            if final_manifest_replaced[0]:
                exc.add_note("Production state outcome may be committed or unknown.")
            raise

    def bootstrap_dependency_graph(
        self,
        *,
        attempt_id: str,
        graph: DependencyGraphSnapshot,
        transition: DependencyGraphTransition,
        expected_desired_fingerprints: Mapping[str, str],
    ) -> ProductionManifest:
        """Durably migrate the current exact bundle to Manifest 2.3."""

        prepared = prepare_dependency_graph_transition(
            expected_manifest_revision=transition.expected_manifest_revision,
            base_dependency_graph=transition.base_dependency_graph,
            candidate_graph=graph,
            candidate_dependency_states=transition.candidate_dependency_states,
            expected_desired_fingerprints=expected_desired_fingerprints,
        )
        if prepared != transition:
            raise _state_invalid("Dependency graph transition claim is invalid.")
        final_replaced = [False]
        try:
            return self._bootstrap_dependency_graph_locked(
                attempt_id, graph, transition, final_replaced
            )
        except Exception as exc:
            if final_replaced[0]:
                raise _outcome_unknown(exc) from exc
            raise
        except BaseException as exc:
            if final_replaced[0]:
                exc.add_note("Dependency graph activation outcome may be committed or unknown.")
            raise

    def _bootstrap_dependency_graph_locked(
        self,
        attempt_id: str,
        graph: DependencyGraphSnapshot,
        transition: DependencyGraphTransition,
        final_replaced: list[bool],
    ) -> ProductionManifest:
        if not attempt_id:
            raise _state_invalid("Dependency graph bootstrap attempt ID is required.")
        graph_payload = _canonical_json_bytes(graph)
        graph_artifact = PreparedArtifact(
            transition.candidate_dependency_graph.path,
            graph_payload,
            hashlib.sha256(graph_payload).hexdigest(),
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            existing = next(
                (item for item in manifest.attempts if item.attempt_id == attempt_id),
                None,
            )
            if existing is not None:
                if (
                    existing.operation == "bootstrap_dependency_graph"
                    and existing.status is StateCommitStatus.SUCCEEDED
                    and existing.base_manifest_revision
                    == transition.expected_manifest_revision
                    and existing.base_dependency_graph
                    == transition.base_dependency_graph
                    and existing.candidate_dependency_graph
                    == transition.candidate_dependency_graph
                    and existing.candidate_dependency_states_hash
                    == transition.candidate_dependency_states_hash
                    and manifest.active_dependency_graph
                    == transition.candidate_dependency_graph
                    and manifest.dependency_states
                    == transition.candidate_dependency_states
                ):
                    self._reopen_dependency_graph(
                        transition.candidate_dependency_graph
                    )
                    return manifest
                raise _state_invalid(
                    "Dependency graph bootstrap attempt ID was already used."
                )
            if manifest.schema_version == "2.3" and (
                manifest.active_dependency_graph == transition.candidate_dependency_graph
                and manifest.dependency_states == transition.candidate_dependency_states
            ):
                if (
                    manifest.manifest_revision != transition.expected_manifest_revision
                    or manifest.active_dependency_graph != transition.base_dependency_graph
                ):
                    raise _state_invalid("Dependency graph exact replay identity is stale.")
                self._reopen_dependency_graph(transition.candidate_dependency_graph)
                return manifest
            if manifest.manifest_revision != transition.expected_manifest_revision:
                raise _state_invalid("Production Manifest revision is stale.")
            if manifest.active_dependency_graph != transition.base_dependency_graph:
                raise _state_invalid("Dependency graph base identity is stale.")
            unresolved = next(
                (
                    item
                    for item in manifest.attempts
                    if item.status
                    in {StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN}
                ),
                None,
            )
            if unresolved is not None:
                raise _state_invalid(
                    "Production state has an unresolved attempt; explicit recovery is required."
                )
            self._verify_dependency_candidate(
                manifest, graph, transition.candidate_dependency_states
            )
            running = StateCommitAttempt(
                attempt_id=attempt_id,
                operation="bootstrap_dependency_graph",
                status=StateCommitStatus.RUNNING,
                base_manifest_revision=manifest.manifest_revision,
                base_project=manifest.active_project,
                base_registry=manifest.active_registry,
                candidate_artifacts_hash=_candidate_artifacts_hash((graph_artifact,)),
                base_dependency_graph=transition.base_dependency_graph,
                candidate_dependency_graph=transition.candidate_dependency_graph,
                candidate_dependency_states_hash=transition.candidate_dependency_states_hash,
                started_at=_timestamp(),
            )
            running_manifest = _validated_transition(
                manifest,
                {
                    "schema_version": "2.3",
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": manifest.attempts + (running,),
                },
            )
            running_replaced = False
            try:
                def mark_running() -> None:
                    nonlocal running_replaced
                    running_replaced = True

                self._write_manifest_atomic(running_manifest, on_replace=mark_running)
                self._crash_injector.checkpoint(CommitPhase.AFTER_ATTEMPT_STARTED)
                self._write_immutable_artifact(
                    graph_artifact,
                    attempt_id=attempt_id,
                    dependency_graph=True,
                )
                self._reopen_dependency_graph(transition.candidate_dependency_graph)
                succeeded = _validated_transition(
                    running,
                    {"status": StateCommitStatus.SUCCEEDED, "finished_at": _timestamp()},
                )
                final = _validated_transition(
                    manifest,
                    {
                        "schema_version": "2.3",
                        "manifest_revision": manifest.manifest_revision + 2,
                        "active_dependency_graph": transition.candidate_dependency_graph,
                        "dependency_states": transition.candidate_dependency_states,
                        "attempts": manifest.attempts + (succeeded,),
                    },
                )

                def mark_final() -> None:
                    final_replaced[0] = True
                    self._crash_injector.checkpoint(
                        CommitPhase.AFTER_GRAPH_FINAL_MANIFEST_REPLACE
                    )

                self._write_manifest_atomic(final, on_replace=mark_final)
                reopened = self._read_manifest()
                if reopened != final:
                    raise _state_commit_failed(
                        "Dependency graph Manifest reopen verification failed."
                    )
                return reopened
            except Exception as exc:
                primary = _as_state_error(exc)
                if final_replaced[0] or not running_replaced:
                    raise primary from exc
                failed_attempt = _validated_transition(
                    running,
                    {
                        "status": StateCommitStatus.FAILED,
                        "finished_at": _timestamp(),
                        "error_code": primary.code.value,
                        "error_message": primary.user_message,
                    },
                )
                failed_manifest = _validated_transition(
                    manifest,
                    {
                        "schema_version": "2.3",
                        "manifest_revision": manifest.manifest_revision + 2,
                        "attempts": manifest.attempts + (failed_attempt,),
                    },
                )
                try:
                    self._write_manifest_atomic(failed_manifest)
                except BaseException as persist_error:
                    primary.add_note(
                        f"Could not persist failed dependency graph bootstrap: {persist_error}"
                    )
                raise primary from exc

    def _verify_dependency_candidate(
        self,
        manifest: ProductionManifest,
        graph: DependencyGraphSnapshot,
        states: tuple[DependencyNodeState, ...],
        *,
        project_pointer: ProjectSnapshotPointer | None = None,
        registry_pointer: RegistrySnapshotPointer | None = None,
        render_pointer: RenderStateSnapshotPointer | None = None,
        attempts: tuple[StateCommitAttempt, ...] | None = None,
    ) -> None:
        project_pointer = project_pointer or manifest.active_project
        registry_pointer = registry_pointer or manifest.active_registry
        try:
            bundle = load_production_project_candidate(
                self._project_root,
                manifest,
                project_pointer.path,
                registry_pointer.path,
            )
            candidate_manifest = ProductionManifest.model_validate(
                {
                    **manifest.model_dump(mode="python"),
                    "schema_version": "2.3",
                    "active_project": project_pointer,
                    "active_registry": registry_pointer,
                    "active_render_state": (
                        manifest.active_render_state
                        if render_pointer is None
                        else render_pointer
                    ),
                    "active_dependency_graph": DependencyGraphSnapshotPointer(
                        revision_id=graph.revision_id,
                        content_hash=graph.content_hash,
                        path=canonical_dependency_graph_snapshot_path(graph.revision_id),
                        file_sha256=hashlib.sha256(_canonical_json_bytes(graph)).hexdigest(),
                    ),
                    "dependency_states": states,
                    "attempts": manifest.attempts if attempts is None else attempts,
                }
            )
            candidate_bundle = bundle.model_copy(
                update={
                    "manifest": candidate_manifest,
                    "dependency_graph": graph,
                }
            )
            _verify_manifest_dependency_states(candidate_bundle, graph)
        except (AiVideoError, ValidationError, ValueError) as exc:
            detail = exc.technical_detail if isinstance(exc, AiVideoError) else str(exc)
            raise _state_invalid(
                "Dependency graph candidate evidence is invalid.", detail
            ) from exc

    def _validate_request_dependency_transition(
        self,
        manifest: ProductionManifest,
        request: StateCommitRequest,
    ) -> tuple[DependencyGraphTransition | None, DependencyGraphSnapshot | None]:
        return self._validate_dependency_transition(
            manifest,
            expected_manifest_revision=request.expected_manifest_revision,
            artifacts=request.artifacts,
            transition=request.dependency_graph_transition,
        )

    def _validate_dependency_transition(
        self,
        manifest: ProductionManifest,
        *,
        expected_manifest_revision: int,
        artifacts: tuple[PreparedArtifact, ...],
        transition: DependencyGraphTransition | None,
    ) -> tuple[DependencyGraphTransition | None, DependencyGraphSnapshot | None]:
        if manifest.schema_version != "2.3":
            if transition is not None:
                raise _state_invalid(
                    "Dependency graph transition requires Manifest 2.3."
                )
            return None, None
        if transition is None:
            raise _state_invalid(
                "Manifest 2.3 mutation requires a dependency graph transition."
            )
        if (
            transition.expected_manifest_revision != expected_manifest_revision
            or transition.base_dependency_graph != manifest.active_dependency_graph
        ):
            raise _state_invalid("Dependency graph transition base identity is stale.")
        artifact = next(
            (
                item
                for item in artifacts
                if item.relative_path == transition.candidate_dependency_graph.path
            ),
            None,
        )
        if artifact is None:
            if transition.candidate_dependency_graph != manifest.active_dependency_graph:
                raise _state_invalid("Candidate dependency graph artifact is missing.")
            graph = self._reopen_dependency_graph(transition.candidate_dependency_graph)
        else:
            if artifact.file_sha256 != transition.candidate_dependency_graph.file_sha256:
                raise _state_invalid("Candidate dependency graph file hash is stale.")
            try:
                graph = DependencyGraphSnapshot.model_validate_json(artifact.payload)
            except (ValidationError, ValueError) as exc:
                raise _state_invalid(
                    "Candidate dependency graph artifact is invalid.", str(exc)
                ) from exc
        expected = prepare_dependency_graph_transition(
            expected_manifest_revision=expected_manifest_revision,
            base_dependency_graph=manifest.active_dependency_graph,
            candidate_graph=graph,
            candidate_dependency_states=transition.candidate_dependency_states,
            expected_desired_fingerprints=desired_fingerprints(graph),
        )
        if expected != transition:
            raise _state_invalid("Dependency graph transition claim is invalid.")
        return transition, graph

    def _reopen_dependency_graph(
        self, pointer: DependencyGraphSnapshotPointer
    ) -> DependencyGraphSnapshot:
        try:
            snapshot = _read_regular_file_nofollow(
                self._project_root / pointer.path,
                contained_by=self._project_root / "state",
            )
        except (OSError, ValueError) as exc:
            raise _state_commit_failed(
                "Dependency graph snapshot could not be reopened.", str(exc)
            ) from exc
        try:
            graph = DependencyGraphSnapshot.model_validate_json(snapshot.data)
        except (ValidationError, ValueError) as exc:
            raise _state_commit_failed(
                "Dependency graph snapshot could not be reopened.", str(exc)
            ) from exc
        if (
            snapshot.file_sha256 != pointer.file_sha256
            or graph.revision_id != pointer.revision_id
            or graph.content_hash != pointer.content_hash
            or dependency_graph_semantic_sha256(graph) != pointer.content_hash
        ):
            raise _state_commit_failed("Dependency graph snapshot identity is invalid.")
        return graph

    def record_dependency_node_applied(
        self,
        *,
        expected_manifest_revision: int,
        active_dependency_graph: DependencyGraphSnapshotPointer,
        candidate_dependency_graph: DependencyGraphSnapshotPointer,
        node_id: str,
        desired_fingerprint: str,
        evidence: DependencyAppliedEvidence,
    ) -> ProductionManifest:
        """Record fixed-owner evidence after reopening it under commit.lock."""

        with self._exclusive_lock():
            manifest, graph, node, current = self._dependency_result_context(
                expected_manifest_revision=expected_manifest_revision,
                active_dependency_graph=active_dependency_graph,
                candidate_dependency_graph=candidate_dependency_graph,
                node_id=node_id,
                desired_fingerprint=desired_fingerprint,
            )
            bundle = load_production_project_candidate(
                self._project_root,
                manifest,
                manifest.active_project.path,
                manifest.active_registry.path,
            )
            if evidence.artifact_id != node.artifact_id:
                raise _state_invalid("Dependency evidence artifact identity is invalid.")
            if isinstance(evidence, ProjectDependencyEvidence):
                if node.kind is not DependencyNodeKind.CREATIVE_ARTIFACT or evidence.pointer != manifest.active_project:
                    raise _state_invalid("Dependency project evidence owner is invalid.")
                _verify_dependency_project_evidence(bundle, evidence, node)
            elif isinstance(evidence, RegistryDependencyEvidence):
                if node.kind is not DependencyNodeKind.ASSET or evidence.pointer != manifest.active_registry:
                    raise _state_invalid("Dependency registry evidence owner is invalid.")
                _verify_dependency_registry_evidence(bundle, evidence, node)
            elif isinstance(evidence, RenderDependencyEvidence):
                if (
                    node.kind in {DependencyNodeKind.CREATIVE_ARTIFACT, DependencyNodeKind.ASSET}
                    or evidence.pointer != manifest.active_render_state
                ):
                    raise _state_invalid("Dependency render evidence owner is invalid.")
                raise _state_invalid(
                    "Render-domain dependency nodes require atomic render activation."
                )
            else:  # pragma: no cover - Pydantic union is exhaustive
                raise _state_invalid("Dependency applied evidence type is invalid.")
            if evidence.artifact_fingerprint != desired_fingerprint:
                raise _state_invalid("Dependency applied fingerprint is stale.")
            if current.lifecycle is DependencyLifecycle.FRESH:
                if current.applied_evidence == evidence:
                    return manifest
                raise _state_invalid("Fresh dependency evidence cannot be replaced.")
            if current.lifecycle is not DependencyLifecycle.STALE:
                raise _state_invalid("Only a ready dependency node may be applied.")
            applied = current.model_copy(
                update={
                    "applied_fingerprint": desired_fingerprint,
                    "lifecycle": DependencyLifecycle.FRESH,
                    "applied_evidence": evidence,
                    "blocked_by": (),
                    "error_code": None,
                    "error_message": None,
                }
            )
            return self._write_dependency_result(manifest, graph, node_id, applied)

    def record_dependency_node_failed(
        self,
        *,
        expected_manifest_revision: int,
        active_dependency_graph: DependencyGraphSnapshotPointer,
        candidate_dependency_graph: DependencyGraphSnapshotPointer,
        node_id: str,
        desired_fingerprint: str,
        error_code: str,
        error_message: str,
    ) -> ProductionManifest:
        """Persist one same-desired typed failure without blanket staleness."""

        if not error_code or not error_message:
            raise _state_invalid("Dependency failure requires typed error fields.")
        with self._exclusive_lock():
            manifest, graph, node, current = self._dependency_result_context(
                expected_manifest_revision=expected_manifest_revision,
                active_dependency_graph=active_dependency_graph,
                candidate_dependency_graph=candidate_dependency_graph,
                node_id=node_id,
                desired_fingerprint=desired_fingerprint,
            )
            if node.kind in {
                DependencyNodeKind.RENDERER_SOURCE,
                DependencyNodeKind.RENDER,
            }:
                raise _state_invalid(
                    "Renderer source and render failures must be recorded atomically."
                )
            sanitized_message = _redact_render_error_message(error_message)
            if (
                current.lifecycle is DependencyLifecycle.FAILED
                and current.error_code == error_code
                and current.error_message == sanitized_message
            ):
                return manifest
            if current.lifecycle is not DependencyLifecycle.STALE:
                raise _state_invalid("Only a ready dependency node may fail.")
            failed = current.model_copy(
                update={
                    "lifecycle": DependencyLifecycle.FAILED,
                    "blocked_by": (),
                    "error_code": error_code,
                    "error_message": sanitized_message,
                }
            )
            return self._write_dependency_result(manifest, graph, node_id, failed)

    def _dependency_result_context(
        self,
        *,
        expected_manifest_revision: int,
        active_dependency_graph: DependencyGraphSnapshotPointer,
        candidate_dependency_graph: DependencyGraphSnapshotPointer,
        node_id: str,
        desired_fingerprint: str,
    ) -> tuple[ProductionManifest, DependencyGraphSnapshot, object, DependencyNodeState]:
        manifest = self._read_manifest()
        if manifest.schema_version != "2.3":
            raise _state_invalid("Dependency results require Manifest 2.3.")
        if manifest.manifest_revision != expected_manifest_revision:
            raise _state_invalid("Production Manifest revision is stale.")
        if (
            manifest.active_dependency_graph != active_dependency_graph
            or candidate_dependency_graph != active_dependency_graph
        ):
            raise _state_invalid("Dependency result graph identity is stale.")
        graph = self._reopen_dependency_graph(active_dependency_graph)
        desired = desired_fingerprints(graph)
        if desired.get(node_id) != desired_fingerprint:
            raise _state_invalid("Dependency result desired fingerprint is stale.")
        node = next((item for item in graph.nodes if item.node_id == node_id), None)
        current = next(
            (item for item in manifest.dependency_states if item.node_id == node_id),
            None,
        )
        if node is None or current is None:
            raise _state_invalid("Dependency result node is not active.")
        return manifest, graph, node, current

    def _write_dependency_result(
        self,
        manifest: ProductionManifest,
        graph: DependencyGraphSnapshot,
        node_id: str,
        replacement: DependencyNodeState,
    ) -> ProductionManifest:
        previous = tuple(
            replacement if state.node_id == node_id else state
            for state in manifest.dependency_states
        )
        states = resolve_dependency_state(graph, previous).states
        updated = _validated_transition(
            manifest,
            {
                "manifest_revision": manifest.manifest_revision + 1,
                "dependency_states": states,
            },
        )
        final_replaced = [False]
        try:
            self._write_manifest_atomic(
                updated,
                on_replace=lambda: final_replaced.__setitem__(0, True),
            )
            reopened = self._read_manifest()
            if reopened != updated:
                raise _state_commit_failed(
                    "Dependency result Manifest verification failed."
                )
            return reopened
        except Exception as exc:
            if final_replaced[0]:
                raise _outcome_unknown(exc) from exc
            raise
        except BaseException as exc:
            if final_replaced[0]:
                exc.add_note(
                    "Dependency result outcome may be committed or unknown."
                )
            raise

    def recover(self) -> RecoveryReport:
        """Repair interrupted P2A attempts without selecting unreferenced snapshots."""
        try:
            return self._recover_locked()
        except AiVideoError as exc:
            if exc.code in {
                ErrorCode.PRODUCTION_STATE_BUSY,
                ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED,
            }:
                raise
            raise _state_recovery_failed(
                "Could not recover production state.", exc.technical_detail or str(exc)
            ) from exc
        except Exception as exc:
            raise _state_recovery_failed("Could not recover production state.", str(exc)) from exc

    def _recover_locked(self) -> RecoveryReport:
        with self._exclusive_lock():
            manifest = self._read_manifest()
            revision_before = manifest.manifest_revision
            items = list(self._active_recovery_items(manifest))
            attempts_before_recovery = list(manifest.attempts)
            attempts, changed, interrupted_items = self._recover_attempts(manifest)

            items.extend(self._remove_fixed_manifest_temp())
            items.extend(self._remove_owned_attempt_temps(attempts_before_recovery))
            items.extend(self._remove_render_attempt_scratch(attempts_before_recovery))
            if changed:
                manifest = _validated_transition(
                    manifest,
                    {
                        "manifest_revision": manifest.manifest_revision + 1,
                        "attempts": tuple(attempts),
                    },
                )
                self._write_manifest_atomic(manifest)
            items.extend(interrupted_items)
            items.extend(self._preserved_orphan_items(manifest, attempts))
            return RecoveryReport(
                manifest_revision_before=revision_before,
                manifest_revision_after=manifest.manifest_revision,
                items=tuple(items),
            )

    def _active_recovery_items(self, manifest: ProductionManifest) -> tuple[RecoveryItem, ...]:
        project_path = self._validate_recovery_project_pointer(manifest.active_project)
        registry_path = self._validate_recovery_registry_pointer(manifest.active_registry)
        project_hash = self._require_recovery_file_hash(
            project_path, manifest.active_project.file_sha256
        )
        registry_hash = self._require_recovery_file_hash(
            registry_path, manifest.active_registry.file_sha256
        )
        registry_snapshot = _read_regular_file_nofollow(
            registry_path, contained_by=self._project_root
        )
        try:
            active_registry = AssetRegistrySnapshot.model_validate_json(
                registry_snapshot.data
            )
        except (ValidationError, ValueError) as exc:
            raise _state_invalid("Active registry recovery parse failed.", str(exc)) from exc
        p4_asset_items: tuple[RecoveryItem, ...] = ()
        if active_registry.schema_version == "2.1":
            if (
                active_registry.revision_id != manifest.active_registry.revision_id
                or active_registry.content_hash != manifest.active_registry.content_hash
                or registry_semantic_sha256(active_registry) != active_registry.content_hash
            ):
                raise _state_invalid("Active P4 registry recovery identity is invalid.")
            project_snapshot = _read_regular_file_nofollow(
                project_path, contained_by=self._project_root
            )
            try:
                active_project = ProductionProject.model_validate(
                    yaml.safe_load(project_snapshot.data.decode("utf-8"))
                )
            except (UnicodeDecodeError, ValidationError, ValueError, yaml.YAMLError) as exc:
                raise _state_invalid("Active project recovery parse failed.", str(exc)) from exc
            if (
                active_project.project_id != manifest.project_id
                or active_project.revision != manifest.active_project.revision
                or active_project.content_hash != manifest.active_project.content_hash
                or not verify_artifact_hash(active_project)
            ):
                raise _state_invalid("Active project recovery identity is invalid.")
            asset_items: list[RecoveryItem] = []
            for record in active_registry.assets:
                snapshot = _read_regular_file_nofollow(
                    self._project_root / record.artifact_path,
                    contained_by=self._project_root,
                )
                if snapshot.file_sha256 != record.sha256 or len(snapshot.data) != record.size_bytes:
                    raise _state_invalid("Active P4 asset recovery identity is invalid.")
                asset_items.append(
                    RecoveryItem(
                        path=record.artifact_path,
                        disposition=RecoveryDisposition.ACTIVE,
                        sha256=snapshot.file_sha256,
                    )
                )
            p4_asset_items = tuple(asset_items)
        else:
            bundle = load_production_project_candidate(
                self._project_root,
                manifest,
                manifest.active_project.path,
                manifest.active_registry.path,
            )
            self._require_loaded_pointer_identity(
                bundle, manifest.active_project, manifest.active_registry
            )
        self._require_recovery_file_hash(project_path, manifest.active_project.file_sha256)
        self._require_recovery_file_hash(registry_path, manifest.active_registry.file_sha256)
        items = [
            RecoveryItem(
                path=manifest.active_project.path,
                disposition=RecoveryDisposition.ACTIVE,
                sha256=project_hash,
            ),
            RecoveryItem(
                path=manifest.active_registry.path,
                disposition=RecoveryDisposition.ACTIVE,
                sha256=registry_hash,
            ),
        ]
        items.extend(p4_asset_items)
        if manifest.active_dependency_graph is not None:
            graph = self._reopen_dependency_graph(manifest.active_dependency_graph)
            self._verify_dependency_candidate(
                manifest, graph, manifest.dependency_states
            )
            items.append(
                RecoveryItem(
                    path=manifest.active_dependency_graph.path,
                    disposition=RecoveryDisposition.ACTIVE,
                    sha256=manifest.active_dependency_graph.file_sha256,
                )
            )
        if manifest.active_render_state is not None:
            if manifest.schema_version == "2.3":
                bundle = load_production_project_candidate(
                    self._project_root,
                    manifest,
                    manifest.active_project.path,
                    manifest.active_registry.path,
                )
                state = _load_exact_render_state(
                    bundle, manifest.active_render_state
                )
            else:
                state = load_verified_render_state(
                    self._project_root,
                    manifest.active_render_state,
                    project=manifest.active_project,
                    registry=manifest.active_registry,
                )
            items.extend(
                self._render_graph_recovery_items(
                    state,
                    manifest.active_render_state,
                    RecoveryDisposition.ACTIVE,
                )
            )
        return tuple(items)

    def _recovery_dependency_outcome(
        self,
        manifest: ProductionManifest,
        attempt: StateCommitAttempt,
    ) -> Literal["legacy", "base", "candidate"]:
        graph_fields = (
            attempt.base_dependency_graph,
            attempt.candidate_dependency_graph,
            attempt.candidate_dependency_states_hash,
        )
        if all(item is None for item in graph_fields):
            return "legacy"
        if (
            manifest.schema_version != "2.3"
            or attempt.candidate_dependency_graph is None
            or attempt.candidate_dependency_states_hash is None
        ):
            raise _state_invalid(
                "Interrupted P5 attempt dependency identity is incomplete."
            )
        active_graph = manifest.active_dependency_graph
        active_states_hash = _dependency_states_hash(manifest.dependency_states)
        if (
            active_graph == attempt.candidate_dependency_graph
            and active_states_hash == attempt.candidate_dependency_states_hash
        ):
            graph = self._reopen_dependency_graph(
                attempt.candidate_dependency_graph
            )
            self._verify_dependency_candidate(
                manifest, graph, manifest.dependency_states
            )
            return "candidate"
        if active_graph == attempt.base_dependency_graph:
            try:
                self._reopen_dependency_graph(attempt.candidate_dependency_graph)
            except AiVideoError:
                candidate_absent = self._dependency_graph_candidate_is_absent(
                    attempt
                )
                recoverable_absence = (
                    attempt.operation in {"commit_project_registry", "audio_import"}
                    and candidate_absent
                )
                if (
                    not (
                        candidate_absent
                        and self._has_owned_dependency_graph_temp(attempt)
                    )
                    and not recoverable_absence
                ):
                    raise
            return "base"
        raise _state_invalid(
            "Production Manifest selects a mixed interrupted dependency graph."
        )

    def _interrupted_dependency_graph_item(
        self,
        manifest: ProductionManifest,
        attempt: StateCommitAttempt,
    ) -> RecoveryItem | None:
        candidate = attempt.candidate_dependency_graph
        if candidate is None or candidate == manifest.active_dependency_graph:
            return None
        if self._dependency_graph_candidate_is_absent(attempt):
            return None
        self._reopen_dependency_graph(candidate)
        return RecoveryItem(
            path=candidate.path,
            disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
            sha256=candidate.file_sha256,
        )

    def _has_owned_dependency_graph_temp(
        self, attempt: StateCommitAttempt
    ) -> bool:
        candidate = attempt.candidate_dependency_graph
        if candidate is None or attempt.status is not StateCommitStatus.RUNNING:
            return False
        expected_path = canonical_dependency_graph_snapshot_path(
            candidate.revision_id
        )
        if candidate.path != expected_path:
            raise _state_invalid(
                "Interrupted dependency graph path is noncanonical."
            )
        final_path = self._project_root / expected_path
        temp_path = final_path.parent / _owned_temp_name(
            attempt.attempt_id, final_path
        )
        try:
            self._recovery_file_digest(temp_path)
        except FileNotFoundError:
            return False
        return True

    def _dependency_graph_candidate_is_absent(
        self, attempt: StateCommitAttempt
    ) -> bool:
        candidate = attempt.candidate_dependency_graph
        if candidate is None or attempt.status is not StateCommitStatus.RUNNING:
            return False
        expected_path = canonical_dependency_graph_snapshot_path(
            candidate.revision_id
        )
        if candidate.path != expected_path:
            raise _state_invalid(
                "Interrupted dependency graph path is noncanonical."
            )
        try:
            self._recovery_file_digest(self._project_root / expected_path)
        except FileNotFoundError:
            return True
        return False

    @staticmethod
    def _candidate_hash_with_optional_graph(
        artifacts: tuple[PreparedArtifact, ...],
        attempt: StateCommitAttempt,
    ) -> tuple[str, ...]:
        hashes = [_candidate_artifacts_hash(artifacts)]
        graph = attempt.candidate_dependency_graph
        if graph is not None and all(
            item.relative_path != graph.path for item in artifacts
        ):
            hashes.append(
                _candidate_artifacts_hash(
                    (
                        *artifacts,
                        PreparedArtifact(graph.path, b"", graph.file_sha256),
                    )
                )
            )
        return tuple(hashes)

    @staticmethod
    def _render_graph_recovery_items(
        state: RenderStateSnapshot,
        pointer: RenderStateSnapshotPointer,
        disposition: RecoveryDisposition,
    ) -> tuple[RecoveryItem, ...]:
        pairs = [
            (state.timeline.path, state.timeline.file_sha256),
            (state.source_bundle.index.path, state.source_bundle.index.file_sha256),
            *((item.path, item.file_sha256) for item in state.source_bundle.assets),
            (state.source_receipt.path, state.source_receipt.file_sha256),
            (state.render_receipt.path, state.render_receipt.file_sha256),
            (state.output.path, state.output.file_sha256),
            (pointer.path, pointer.file_sha256),
        ]
        return tuple(
            RecoveryItem(path=path, disposition=disposition, sha256=digest)
            for path, digest in sorted(pairs, key=lambda item: item[0].as_posix())
        )

    def _recover_attempts(
        self, manifest: ProductionManifest
    ) -> tuple[list[StateCommitAttempt], bool, list[RecoveryItem]]:
        repaired: list[StateCommitAttempt] = []
        items: list[RecoveryItem] = []
        changed = False
        for attempt in manifest.attempts:
            if attempt.status not in {
                StateCommitStatus.RUNNING,
                StateCommitStatus.OUTCOME_UNKNOWN,
            }:
                repaired.append(attempt)
                continue
            if attempt.operation == "bootstrap_dependency_graph":
                if (
                    attempt.base_dependency_graph is None
                    and manifest.schema_version == "2.3"
                    and manifest.active_dependency_graph is not None
                    and manifest.active_dependency_graph
                    != attempt.candidate_dependency_graph
                ):
                    raise _state_invalid(
                        "Interrupted dependency bootstrap has a mixed active graph."
                    )
                if (
                    attempt.candidate_dependency_graph is None
                    or attempt.candidate_dependency_states_hash is None
                    or attempt.base_project != manifest.active_project
                    or attempt.base_registry != manifest.active_registry
                ):
                    raise _state_invalid(
                        "Interrupted dependency bootstrap identity is incomplete."
                    )
                active_graph = manifest.active_dependency_graph
                candidate = attempt.candidate_dependency_graph
                expected_artifacts_hash = _candidate_artifacts_hash(
                    (
                        PreparedArtifact(
                            candidate.path,
                            b"",
                            candidate.file_sha256,
                        ),
                    )
                )
                if expected_artifacts_hash != attempt.candidate_artifacts_hash:
                    raise _state_invalid(
                        "Interrupted dependency graph artifact hash is invalid."
                    )
                if active_graph == candidate:
                    graph = self._reopen_dependency_graph(candidate)
                    if (
                        _dependency_states_hash(manifest.dependency_states)
                        != attempt.candidate_dependency_states_hash
                    ):
                        raise _state_invalid(
                            "Activated dependency bootstrap state hash is invalid."
                        )
                    self._verify_dependency_candidate(
                        manifest, graph, manifest.dependency_states
                    )
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.SUCCEEDED,
                            "finished_at": _timestamp(),
                            "error_code": None,
                            "error_message": None,
                        },
                    )
                elif active_graph == attempt.base_dependency_graph:
                    try:
                        graph = self._reopen_dependency_graph(candidate)
                    except AiVideoError:
                        if (
                            self._dependency_graph_candidate_is_absent(attempt)
                            and (
                                self._has_owned_dependency_graph_temp(attempt)
                                or attempt.operation
                                == "bootstrap_dependency_graph"
                            )
                        ):
                            graph = None
                        else:
                            raise
                    if graph is not None:
                        items.append(
                            RecoveryItem(
                                path=candidate.path,
                                disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                                sha256=candidate.file_sha256,
                            )
                        )
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.INTERRUPTED,
                            "finished_at": _timestamp(),
                            "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                            "error_message": (
                                "Dependency graph bootstrap was interrupted before activation."
                            ),
                        },
                    )
                else:
                    raise _state_invalid(
                        "Production Manifest selects a mixed interrupted dependency graph."
                    )
                repaired.append(replacement)
                changed = True
                continue
            if attempt.operation == "voice_generation":
                dependency_outcome = self._recovery_dependency_outcome(
                    manifest, attempt
                )
                active_pair = (manifest.active_project, manifest.active_registry)
                base_pair = (attempt.base_project, attempt.base_registry)
                if attempt.voice_phase == "candidate":
                    if attempt.candidate_registry is None:
                        raise _state_invalid("Voice candidate recovery identity is incomplete.")
                    candidate_project = attempt.candidate_project or attempt.base_project
                    self._validate_recovery_project_pointer(candidate_project)
                    self._validate_recovery_registry_pointer(attempt.candidate_registry)
                    replay = self._reconstruct_voice_activation_request(attempt)
                    replay_registry_artifact = next(
                        item
                        for item in replay.artifacts
                        if item.relative_path == replay.next_registry.path
                    )
                    replay_registry = AssetRegistrySnapshot.model_validate_json(
                        replay_registry_artifact.payload
                    )
                    self._validate_voice_activation_graph(
                        replay,
                        attempt,
                        replay_registry,
                        attempt.candidate_audio_asset_ids,
                        attempt.candidate_caption_asset_ids,
                    )
                    if attempt.candidate_artifacts_hash not in (
                        self._candidate_hash_with_optional_graph(
                            replay.artifacts, attempt
                        )
                    ):
                        raise _state_invalid("Voice recovery candidate graph hash is invalid.")
                    candidate_pair = (
                        candidate_project,
                        attempt.candidate_registry,
                    )
                    if active_pair == candidate_pair:
                        if dependency_outcome not in {"legacy", "candidate"}:
                            raise _state_invalid(
                                "Voice recovery selects a mixed candidate graph."
                            )
                        replacement = _validated_transition(
                            attempt,
                            {
                                "status": StateCommitStatus.SUCCEEDED,
                                "voice_phase": "activate",
                                "finished_at": _timestamp(),
                                "error_code": None,
                                "error_message": None,
                            },
                        )
                    elif active_pair == base_pair:
                        if dependency_outcome not in {"legacy", "base"}:
                            raise _state_invalid(
                                "Voice recovery selects a mixed base graph."
                            )
                        replacement = _validated_transition(
                            attempt,
                            {
                                "status": StateCommitStatus.INTERRUPTED,
                                "finished_at": _timestamp(),
                                "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                                "error_message": "Voice candidate is durable but explicit activation is required.",
                            },
                        )
                        items.append(
                            RecoveryItem(
                                path=attempt.candidate_registry.path,
                                disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                            )
                        )
                        dependency_item = self._interrupted_dependency_graph_item(
                            manifest, attempt
                        )
                        if dependency_item is not None:
                            items.append(dependency_item)
                    else:
                        raise _state_invalid(
                            "Production Manifest selects a mixed interrupted voice pair."
                        )
                elif attempt.status is StateCommitStatus.OUTCOME_UNKNOWN:
                    repaired.append(attempt)
                    continue
                elif attempt.voice_phase == "request":
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.INTERRUPTED,
                            "finished_at": _timestamp(),
                            "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                            "error_message": "Voice attempt was interrupted before durable submit intent.",
                        },
                    )
                else:
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.OUTCOME_UNKNOWN,
                            "finished_at": _timestamp(),
                            "error_code": ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN.value,
                            "error_message": "Voice submit outcome is unknown; blind retry is forbidden.",
                        },
                    )
                repaired.append(replacement)
                changed = True
                continue
            if attempt.operation == "render_state":
                dependency_outcome = self._recovery_dependency_outcome(
                    manifest, attempt
                )
                active_pair = (manifest.active_project, manifest.active_registry)
                base_pair = (attempt.base_project, attempt.base_registry)
                if active_pair != base_pair:
                    raise _state_invalid(
                        "Production Manifest selects a mixed interrupted render pair."
                    )
                if attempt.candidate_render_state is None:
                    if (
                        attempt.candidate_project is not None
                        or attempt.candidate_registry is not None
                        or manifest.active_render_state != attempt.base_render_state
                    ):
                        raise _state_invalid(
                            "Interrupted render attempt has a mixed begun identity."
                        )
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.INTERRUPTED,
                            "finished_at": _timestamp(),
                            "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                            "error_message": "Render state attempt was interrupted before authoritative candidate preparation.",
                        },
                    )
                else:
                    if (
                        attempt.candidate_project != attempt.base_project
                        or attempt.candidate_registry != attempt.base_registry
                    ):
                        raise _state_invalid(
                            "Interrupted render candidate changed project or registry."
                        )
                    state = load_verified_render_state(
                        self._project_root,
                        attempt.candidate_render_state,
                        project=attempt.base_project,
                        registry=attempt.base_registry,
                    )
                    render_hashes = {
                        self._render_state_artifacts_hash(
                            state, attempt.candidate_render_state
                        )
                    }
                    if attempt.candidate_dependency_graph is not None:
                        render_hashes.add(
                            self._render_state_artifacts_hash(
                                state,
                                attempt.candidate_render_state,
                                graph=attempt.candidate_dependency_graph,
                            )
                        )
                    if attempt.candidate_artifacts_hash not in render_hashes:
                        raise _state_invalid(
                            "Interrupted render candidate artifact hash is invalid."
                        )
                    if manifest.active_render_state == attempt.candidate_render_state:
                        if dependency_outcome not in {"legacy", "candidate"}:
                            raise _state_invalid(
                                "Render recovery selects a mixed candidate graph."
                            )
                        replacement = _validated_transition(
                            attempt,
                            {
                                "status": StateCommitStatus.SUCCEEDED,
                                "finished_at": _timestamp(),
                                "error_code": None,
                                "error_message": None,
                            },
                        )
                    elif manifest.active_render_state == attempt.base_render_state:
                        if dependency_outcome not in {"legacy", "base"}:
                            raise _state_invalid(
                                "Render recovery selects a mixed base graph."
                            )
                        replacement = _validated_transition(
                            attempt,
                            {
                                "status": StateCommitStatus.INTERRUPTED,
                                "finished_at": _timestamp(),
                                "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                                "error_message": "Render state attempt was interrupted before selecting its candidate state.",
                            },
                        )
                        items.append(
                            RecoveryItem(
                                path=attempt.candidate_render_state.path,
                                disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                            )
                        )
                        dependency_item = self._interrupted_dependency_graph_item(
                            manifest, attempt
                        )
                        if dependency_item is not None:
                            items.append(dependency_item)
                    else:
                        raise _state_invalid(
                            "Production Manifest selects a mixed interrupted render state."
                        )
                repaired.append(replacement)
                changed = True
                continue
            if attempt.operation == "audio_import":
                dependency_outcome = self._recovery_dependency_outcome(
                    manifest, attempt
                )
                if (
                    attempt.candidate_project is not None
                    or attempt.candidate_registry is None
                ):
                    raise _state_invalid("Interrupted audio import identity is incomplete.")
                self._validate_recovery_project_pointer(attempt.base_project)
                self._validate_recovery_registry_pointer(attempt.base_registry)
                self._validate_recovery_registry_pointer(attempt.candidate_registry)
                active_pair = (manifest.active_project, manifest.active_registry)
                base_pair = (attempt.base_project, attempt.base_registry)
                candidate_pair = (attempt.base_project, attempt.candidate_registry)
                if active_pair == candidate_pair:
                    if dependency_outcome not in {"legacy", "candidate"}:
                        raise _state_invalid(
                            "Audio recovery selects a mixed candidate graph."
                        )
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.SUCCEEDED,
                            "finished_at": _timestamp(),
                            "error_code": None,
                            "error_message": None,
                        },
                    )
                elif active_pair == base_pair:
                    if dependency_outcome not in {"legacy", "base"}:
                        raise _state_invalid(
                            "Audio recovery selects a mixed base graph."
                        )
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.INTERRUPTED,
                            "finished_at": _timestamp(),
                            "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                            "error_message": "Audio import was interrupted before registry activation.",
                        },
                    )
                    items.append(
                        RecoveryItem(
                            path=attempt.candidate_registry.path,
                            disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                        )
                    )
                    dependency_item = self._interrupted_dependency_graph_item(
                        manifest, attempt
                    )
                    if dependency_item is not None:
                        items.append(dependency_item)
                else:
                    raise _state_invalid(
                        "Production Manifest selects a mixed interrupted audio import pair."
                    )
                repaired.append(replacement)
                changed = True
                continue
            if attempt.candidate_project is None or attempt.candidate_registry is None:
                raise _state_invalid("Incomplete production state attempt has no candidate snapshots.")
            self._validate_recovery_project_pointer(attempt.candidate_project)
            self._validate_recovery_registry_pointer(attempt.candidate_registry)
            self._validate_recovery_project_pointer(attempt.base_project)
            self._validate_recovery_registry_pointer(attempt.base_registry)
            active_pair = (manifest.active_project, manifest.active_registry)
            candidate_pair = (attempt.candidate_project, attempt.candidate_registry)
            base_pair = (attempt.base_project, attempt.base_registry)
            dependency_outcome = self._recovery_dependency_outcome(
                manifest, attempt
            )
            if active_pair == candidate_pair:
                if dependency_outcome not in {"legacy", "candidate"}:
                    raise _state_invalid(
                        "State recovery selects a mixed candidate graph."
                    )
                replacement = _validated_transition(
                    attempt,
                    {
                        "status": StateCommitStatus.SUCCEEDED,
                        "finished_at": _timestamp(),
                        "error_code": None,
                        "error_message": None,
                    },
                )
            elif active_pair != base_pair:
                raise _state_invalid(
                    "Production Manifest selects a mixed interrupted state commit pair."
                )
            else:
                if dependency_outcome not in {"legacy", "base"}:
                    raise _state_invalid(
                        "State recovery selects a mixed base graph."
                    )
                replacement = _validated_transition(
                    attempt,
                    {
                        "status": StateCommitStatus.INTERRUPTED,
                        "finished_at": _timestamp(),
                        "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                        "error_message": "Production state attempt was interrupted before selecting its candidate snapshots.",
                    },
                )
                items.append(
                    RecoveryItem(
                        path=attempt.candidate_project.path,
                        disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                    )
                )
                dependency_item = self._interrupted_dependency_graph_item(
                    manifest, attempt
                )
                if dependency_item is not None:
                    items.append(dependency_item)
            repaired.append(replacement)
            changed = True
        return repaired, changed, items

    @staticmethod
    def _render_state_artifacts_hash(
        state: RenderStateSnapshot,
        pointer: RenderStateSnapshotPointer,
        *,
        graph: DependencyGraphSnapshotPointer | None = None,
    ) -> str:
        pairs = [
            (state.timeline.path, state.timeline.file_sha256),
            (state.source_bundle.index.path, state.source_bundle.index.file_sha256),
            *((item.path, item.file_sha256) for item in state.source_bundle.assets),
            (state.source_receipt.path, state.source_receipt.file_sha256),
            (state.render_receipt.path, state.render_receipt.file_sha256),
            (state.output.path, state.output.file_sha256),
            (pointer.path, pointer.file_sha256),
        ]
        if graph is not None:
            pairs.append((graph.path, graph.file_sha256))
        artifacts = tuple(
            PreparedArtifact(path, b"", digest)
            for path, digest in sorted(pairs, key=lambda item: item[0].as_posix())
        )
        return _candidate_artifacts_hash(artifacts)

    def _remove_fixed_manifest_temp(self) -> tuple[RecoveryItem, ...]:
        items: list[RecoveryItem] = []
        for name in (
            ".p2a-manifest.tmp",
            ".p2a-render-candidate-manifest.tmp",
            ".p2a-render-final-manifest.tmp",
        ):
            items.extend(self._remove_recovery_temp(self._state_directory() / name))
        return tuple(items)

    def _reconstruct_voice_activation_request(
        self, attempt: StateCommitAttempt
    ) -> StateCommitRequest:
        if attempt.candidate_registry is None:
            raise _state_invalid("Voice candidate registry identity is missing.")
        registry_snapshot = _read_regular_file_nofollow(
            self._project_root / attempt.candidate_registry.path,
            contained_by=self._project_root,
        )
        try:
            registry = AssetRegistrySnapshot.model_validate_json(registry_snapshot.data)
        except (ValidationError, ValueError) as exc:
            raise _state_invalid("Voice candidate registry could not be reopened.", str(exc)) from exc
        candidate_ids = set(attempt.candidate_audio_asset_ids) | set(
            attempt.candidate_caption_asset_ids
        )
        by_id = {item.asset_id: item for item in registry.assets}
        if not candidate_ids or not candidate_ids.issubset(by_id):
            raise _state_invalid("Voice candidate asset identities are incomplete.")
        paths = self.voice_attempt_paths(attempt.attempt_id)
        relative_paths = {
            attempt.base_project.path,
            attempt.candidate_registry.path,
            *(by_id[item].artifact_path for item in candidate_ids),
            *(
                path.relative_to(self._project_root)
                for path in (
                    paths.request_path,
                    paths.preview_path,
                    paths.authorization_path,
                    paths.submit_intent_path,
                    paths.alignment_path,
                    paths.cost_path,
                    paths.provenance_path,
                    paths.outcome_path,
                )
            ),
        }
        relative_paths.update(
            Path(f"assets/styles/{by_id[item].caption_metadata.style_content_hash}.json")
            for item in candidate_ids
            if by_id[item].caption_metadata is not None
            and by_id[item].caption_metadata.style_content_hash is not None
        )
        artifacts = tuple(
            PreparedArtifact(path, snapshot.data, snapshot.file_sha256)
            for path in sorted(relative_paths, key=Path.as_posix)
            for snapshot in (
                _read_regular_file_nofollow(
                    self._project_root / path,
                    contained_by=self._project_root,
                ),
            )
        )
        return StateCommitRequest(
            attempt_id=attempt.attempt_id,
            operation="voice_generation",
            expected_manifest_revision=attempt.base_manifest_revision + 2,
            artifacts=artifacts,
            next_project=attempt.base_project,
            next_registry=attempt.candidate_registry,
        )

    def _remove_owned_attempt_temps(
        self, attempts: list[StateCommitAttempt]
    ) -> tuple[RecoveryItem, ...]:
        items: list[RecoveryItem] = []
        paths: set[Path] = set()
        for attempt in attempts:
            if attempt.status is StateCommitStatus.SUCCEEDED:
                continue
            try:
                for relative in _list_regular_files_nofollow(
                    self._state_directory()
                ):
                    if (
                        relative.name.startswith(
                            _owned_temp_prefix(attempt.attempt_id)
                        )
                        and relative.name.endswith(".tmp")
                    ):
                        paths.add(self._state_directory() / relative)
            except (OSError, ValueError) as exc:
                raise _state_invalid(
                    "Dependency graph temporary files could not be inspected.",
                    str(exc),
                ) from exc
            if attempt.candidate_project is not None:
                project_path = self._validate_recovery_project_pointer(attempt.candidate_project)
                paths.add(project_path.parent / _owned_temp_name(attempt.attempt_id, project_path))
            if attempt.candidate_registry is not None:
                registry_path = self._validate_recovery_registry_pointer(attempt.candidate_registry)
                paths.add(registry_path.parent / _owned_temp_name(attempt.attempt_id, registry_path))
            if attempt.candidate_dependency_graph is not None:
                graph_pointer = attempt.candidate_dependency_graph
                expected_graph_path = canonical_dependency_graph_snapshot_path(
                    graph_pointer.revision_id
                )
                if graph_pointer.path != expected_graph_path:
                    raise _state_invalid(
                        "Production recovery dependency graph path is unsafe."
                    )
                graph_path = self._project_root / expected_graph_path
                paths.add(
                    graph_path.parent
                    / _owned_temp_name(attempt.attempt_id, graph_path)
                )
            if (
                attempt.operation == "render_state"
                and attempt.candidate_render_state is not None
            ):
                try:
                    state = load_verified_render_state(
                        self._project_root,
                        attempt.candidate_render_state,
                        project=attempt.base_project,
                        registry=attempt.base_registry,
                    )
                    for item in self._render_graph_recovery_items(
                        state,
                        attempt.candidate_render_state,
                        RecoveryDisposition.ORPHAN_PRESERVED,
                    ):
                        final_path = self._project_root / item.path
                        paths.add(
                            final_path.parent
                            / _owned_temp_name(attempt.attempt_id, final_path)
                        )
                except AiVideoError:
                    pass
            if attempt.operation == "render_state":
                render_root = self._project_root / "state/render"
                try:
                    for relative in _list_regular_files_nofollow(render_root):
                        if (
                            relative.name.startswith(_owned_temp_prefix(attempt.attempt_id))
                            and relative.name.endswith(".tmp")
                        ):
                            paths.add(render_root / relative)
                except FileNotFoundError:
                    pass
                except (OSError, ValueError) as exc:
                    raise _state_invalid(
                        "Render immutable temporary files could not be inspected.",
                        str(exc),
                    ) from exc
            if attempt.operation == "audio_import":
                try:
                    for relative in _list_regular_files_nofollow(self._project_root):
                        if (
                            relative.name.startswith(
                                _owned_temp_prefix(attempt.attempt_id)
                            )
                            and relative.name.endswith(".tmp")
                        ):
                            paths.add(self._project_root / relative)
                except (OSError, ValueError) as exc:
                    raise _state_invalid(
                        "Audio import immutable temporary files could not be inspected.",
                        str(exc),
                    ) from exc
        for path in sorted(paths):
            items.extend(self._remove_recovery_temp(path))
        return tuple(items)

    def _remove_render_attempt_scratch(
        self, attempts: list[StateCommitAttempt]
    ) -> tuple[RecoveryItem, ...]:
        items: list[RecoveryItem] = []
        for attempt in attempts:
            if (
                attempt.operation != "render_state"
                or attempt.status is StateCommitStatus.SUCCEEDED
            ):
                continue
            try:
                root = self._project_root / canonical_render_attempt_root(
                    attempt.attempt_id
                )
                relative_files = _list_regular_files_nofollow(root)
            except FileNotFoundError:
                continue
            except (OSError, ValueError) as exc:
                raise _state_invalid(
                    "Render attempt scratch could not be inspected safely.", str(exc)
                ) from exc
            for relative in sorted(relative_files):
                items.extend(self._remove_recovery_temp(root / relative))
        return tuple(items)

    def _remove_recovery_temp(self, path: Path) -> tuple[RecoveryItem, ...]:
        self._validate_cleanup_temp_path(path)
        try:
            digest, file_stat = self._recovery_file_digest(path)
            self._unlink_recovery_file(path, file_stat)
        except FileNotFoundError:
            return ()
        except OSError as exc:
            raise _state_commit_failed("Could not remove production recovery temporary file.", str(exc)) from exc
        return (
            RecoveryItem(
                path=path.relative_to(self._project_root),
                disposition=RecoveryDisposition.PARTIAL_REMOVED,
                sha256=digest,
            ),
        )

    def _preserved_orphan_items(
        self, manifest: ProductionManifest, attempts: list[StateCommitAttempt]
    ) -> tuple[RecoveryItem, ...]:
        items: dict[Path, RecoveryItem] = {}
        for item in self._attempt_orphan_pair_items(manifest, attempts):
            items[item.path] = item
        for item in self._project_orphan_items(manifest):
            items.setdefault(item.path, item)
        for item in self._registry_orphan_items(manifest):
            items.setdefault(item.path, item)
        interrupted_graph_paths = {
            attempt.candidate_dependency_graph.path
            for attempt in attempts
            if attempt.status is not StateCommitStatus.SUCCEEDED
            and attempt.candidate_dependency_graph is not None
        }
        for item in self._dependency_graph_orphan_items(manifest):
            if item.path in interrupted_graph_paths:
                continue
            items.setdefault(item.path, item)
        for item in self._render_orphan_items(manifest):
            items.setdefault(item.path, item)
        return tuple(items[path] for path in sorted(items))

    def _dependency_graph_orphan_items(
        self, manifest: ProductionManifest
    ) -> tuple[RecoveryItem, ...]:
        directory = self._project_root / "state"
        pattern = re.compile(
            r"^dependency_graph\.(?P<revision>[0-9a-f]{64})\.json$"
        )
        items: list[RecoveryItem] = []
        for path, match in self._recovery_namespace_entries(directory, pattern):
            relative = path.relative_to(self._project_root)
            if (
                manifest.active_dependency_graph is not None
                and relative == manifest.active_dependency_graph.path
            ):
                continue
            try:
                snapshot = _read_regular_file_nofollow(
                    path, contained_by=self._project_root / "state"
                )
                graph = DependencyGraphSnapshot.model_validate_json(snapshot.data)
                if (
                    graph.revision_id != match.group("revision")
                    or graph.content_hash != dependency_graph_semantic_sha256(graph)
                ):
                    continue
                pointer = DependencyGraphSnapshotPointer(
                    revision_id=graph.revision_id,
                    content_hash=graph.content_hash,
                    path=relative,
                    file_sha256=snapshot.file_sha256,
                )
                self._reopen_dependency_graph(pointer)
            except (AiVideoError, OSError, ValidationError, ValueError):
                continue
            items.append(
                RecoveryItem(
                    path=relative,
                    disposition=RecoveryDisposition.ORPHAN_PRESERVED,
                    sha256=snapshot.file_sha256,
                )
            )
        return tuple(items)

    def _render_orphan_items(
        self, manifest: ProductionManifest
    ) -> tuple[RecoveryItem, ...]:
        directory = self._project_root / "state/render/states"
        pattern = re.compile(r"^(?P<hash>[0-9a-f]{64})\.json$")
        active_paths: set[Path] = set()
        if manifest.active_render_state is not None:
            try:
                active = load_verified_render_state(
                    self._project_root,
                    manifest.active_render_state,
                    project=manifest.active_project,
                    registry=manifest.active_registry,
                )
                active_paths = {
                    item.path
                    for item in self._render_graph_recovery_items(
                        active,
                        manifest.active_render_state,
                        RecoveryDisposition.ACTIVE,
                    )
                }
            except AiVideoError:
                return ()
        items: dict[Path, RecoveryItem] = {}
        for path, match in self._recovery_namespace_entries(directory, pattern):
            relative = path.relative_to(self._project_root)
            if relative in active_paths:
                continue
            try:
                snapshot = _read_regular_file_nofollow(
                    path, contained_by=self._project_root
                )
                state = RenderStateSnapshot.model_validate_json(snapshot.data)
                if (
                    state.content_hash != match.group("hash")
                    or not verify_artifact_hash(state)
                ):
                    continue
                pointer = RenderStateSnapshotPointer(
                    path=relative,
                    revision=state.revision,
                    content_hash=state.content_hash,
                    file_sha256=snapshot.file_sha256,
                )
                verified = load_verified_render_state(
                    self._project_root,
                    pointer,
                    project=state.project,
                    registry=state.registry,
                )
            except (AiVideoError, OSError, ValidationError, ValueError):
                continue
            for item in self._render_graph_recovery_items(
                verified, pointer, RecoveryDisposition.ORPHAN_PRESERVED
            ):
                if item.path not in active_paths:
                    items[item.path] = item
        return tuple(items[path] for path in sorted(items))

    def _attempt_orphan_pair_items(
        self, manifest: ProductionManifest, attempts: list[StateCommitAttempt]
    ) -> tuple[RecoveryItem, ...]:
        items: list[RecoveryItem] = []
        seen_pairs: set[tuple[ProjectSnapshotPointer, RegistrySnapshotPointer]] = set()
        for attempt in attempts:
            if attempt.status is StateCommitStatus.SUCCEEDED:
                continue
            if attempt.candidate_project is None or attempt.candidate_registry is None:
                continue
            pair = (attempt.candidate_project, attempt.candidate_registry)
            if pair in seen_pairs or pair == (manifest.active_project, manifest.active_registry):
                continue
            seen_pairs.add(pair)
            try:
                project_path = self._validate_recovery_project_pointer(pair[0])
                registry_path = self._validate_recovery_registry_pointer(pair[1])
                project_hash = self._require_recovery_file_hash(
                    project_path, pair[0].file_sha256
                )
                registry_hash = self._require_recovery_file_hash(
                    registry_path, pair[1].file_sha256
                )
                bundle = load_production_project_candidate(
                    self._project_root, manifest, pair[0].path, pair[1].path
                )
                self._require_loaded_pointer_identity(bundle, pair[0], pair[1])
                self._require_recovery_file_hash(project_path, pair[0].file_sha256)
                self._require_recovery_file_hash(registry_path, pair[1].file_sha256)
            except (AiVideoError, OSError):
                continue
            for path, digest in ((pair[0].path, project_hash), (pair[1].path, registry_hash)):
                if path in {manifest.active_project.path, manifest.active_registry.path}:
                    continue
                items.append(
                    RecoveryItem(
                        path=path,
                        disposition=RecoveryDisposition.ORPHAN_PRESERVED,
                        sha256=digest,
                    )
                )
        return tuple(items)

    def _project_orphan_items(self, manifest: ProductionManifest) -> tuple[RecoveryItem, ...]:
        directory = self._project_root / "state/projects"
        pattern = re.compile(r"^project\.(?P<revision>[1-9][0-9]*)\.(?P<hash>[0-9a-f]{64})\.yaml$")
        items: list[RecoveryItem] = []
        for path, match in self._recovery_namespace_entries(directory, pattern):
            relative = path.relative_to(self._project_root)
            if relative == manifest.active_project.path:
                continue
            try:
                pointer = ProjectSnapshotPointer(
                    path=relative,
                    revision=int(match.group("revision")),
                    content_hash=match.group("hash"),
                    file_sha256=self._recovery_file_digest(path)[0],
                )
                bundle = load_production_project_candidate(
                    self._project_root,
                    manifest,
                    pointer.path,
                    manifest.active_registry.path,
                )
                self._require_loaded_pointer_identity(
                    bundle, pointer, manifest.active_registry
                )
                self._require_recovery_file_hash(path, pointer.file_sha256)
            except (AiVideoError, OSError):
                continue
            items.append(
                RecoveryItem(
                    path=relative,
                    disposition=RecoveryDisposition.ORPHAN_PRESERVED,
                    sha256=pointer.file_sha256,
                )
            )
        return tuple(items)

    def _registry_orphan_items(self, manifest: ProductionManifest) -> tuple[RecoveryItem, ...]:
        directory = self._project_root / "assets"
        pattern = re.compile(r"^registry\.(?P<hash>[0-9a-f]{64})\.json$")
        items: list[RecoveryItem] = []
        for path, match in self._recovery_namespace_entries(directory, pattern):
            relative = path.relative_to(self._project_root)
            if relative == manifest.active_registry.path:
                continue
            try:
                pointer = RegistrySnapshotPointer(
                    path=relative,
                    revision_id=match.group("hash"),
                    content_hash=match.group("hash"),
                    file_sha256=self._recovery_file_digest(path)[0],
                )
                bundle = load_production_project_candidate(
                    self._project_root,
                    manifest,
                    manifest.active_project.path,
                    pointer.path,
                )
                self._require_loaded_pointer_identity(
                    bundle, manifest.active_project, pointer
                )
                self._require_recovery_file_hash(path, pointer.file_sha256)
            except (AiVideoError, OSError):
                continue
            items.append(
                RecoveryItem(
                    path=relative,
                    disposition=RecoveryDisposition.ORPHAN_PRESERVED,
                    sha256=pointer.file_sha256,
                )
            )
        return tuple(items)

    def _recovery_namespace_entries(
        self, directory: Path, pattern: re.Pattern[str]
    ) -> tuple[tuple[Path, re.Match[str]], ...]:
        entries: list[tuple[Path, re.Match[str]]] = []
        try:
            with self._recovery_directory_descriptor(directory) as descriptor:
                for name in os.listdir(descriptor):
                    match = pattern.fullmatch(name)
                    if match is not None:
                        entries.append((directory / name, match))
        except FileNotFoundError:
            return ()
        except OSError as exc:
            raise _state_invalid("Production recovery namespace could not be inspected.", str(exc)) from exc
        return tuple(sorted(entries, key=lambda item: item[0].name))

    @contextmanager
    def _recovery_directory_descriptor(self, directory: Path) -> Iterator[int]:
        relative = directory.relative_to(self._project_root)
        self._validate_relative_components(relative)
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptors: list[int] = []
        primary: BaseException | None = None
        try:
            descriptors.append(os.open(self._project_root, flags))
            for component in relative.parts:
                descriptors.append(os.open(component, flags, dir_fd=descriptors[-1]))
            if not stat.S_ISDIR(os.fstat(descriptors[-1]).st_mode):
                raise _state_invalid("Production recovery namespace must be a directory.", str(directory))
            yield descriptors[-1]
        except BaseException as exc:
            primary = exc
            raise
        finally:
            self._close_recovery_descriptors(primary, descriptors)

    @contextmanager
    def _recovery_file_descriptor(
        self, parent_descriptor: int, name: str
    ) -> Iterator[int]:
        descriptor: int | None = None
        primary: BaseException | None = None
        try:
            descriptor = os.open(
                name,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=parent_descriptor,
            )
            yield descriptor
        except BaseException as exc:
            primary = exc
            raise
        finally:
            self._close_recovery_descriptors(primary, (descriptor,))

    @staticmethod
    def _close_recovery_descriptors(
        primary: BaseException | None, descriptors: tuple[int | None, ...] | list[int]
    ) -> None:
        cleanup_errors: list[BaseException] = []
        for descriptor in reversed(descriptors):
            if descriptor is None:
                continue
            try:
                os.close(descriptor)
            except BaseException as cleanup_error:
                cleanup_errors.append(cleanup_error)
        _handle_cleanup_errors(
            primary,
            cleanup_errors,
            label="Production recovery descriptor cleanup",
            no_primary_message="Could not close production recovery file descriptors.",
        )

    def _recovery_file_digest(self, path: Path) -> tuple[str, os.stat_result]:
        self._validate_cleanup_temp_path(path)
        with self._recovery_directory_descriptor(path.parent) as parent_descriptor:
            with self._recovery_file_descriptor(parent_descriptor, path.name) as file_descriptor:
                file_stat = os.fstat(file_descriptor)
                if not stat.S_ISREG(file_stat.st_mode):
                    raise _state_invalid("Production recovery path must be a regular file.", str(path))
                digest = hashlib.sha256()
                while chunk := os.read(file_descriptor, 1024 * 1024):
                    digest.update(chunk)
                current = os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
                if (current.st_dev, current.st_ino) != (file_stat.st_dev, file_stat.st_ino):
                    raise _state_invalid("Production recovery path changed during inspection.", str(path))
                return digest.hexdigest(), file_stat

    def _unlink_recovery_file(self, path: Path, expected: os.stat_result) -> None:
        with self._recovery_directory_descriptor(path.parent) as parent_descriptor:
            current = os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
            if (current.st_dev, current.st_ino) != (expected.st_dev, expected.st_ino):
                raise _state_invalid("Production recovery path changed before cleanup.", str(path))
            os.unlink(path.name, dir_fd=parent_descriptor)

    def _require_recovery_file_hash(self, path: Path, expected_hash: str) -> str:
        actual_hash, _ = self._recovery_file_digest(path)
        if actual_hash != expected_hash:
            raise _state_invalid("Production recovery snapshot hash is invalid.", str(path))
        return actual_hash

    @staticmethod
    def _require_loaded_pointer_identity(
        bundle: LoadedProductionProject,
        project_pointer: ProjectSnapshotPointer,
        registry_pointer: RegistrySnapshotPointer,
    ) -> None:
        project = bundle.project
        registry = bundle.registry
        if (
            project.revision != project_pointer.revision
            or project.content_hash != project_pointer.content_hash
        ):
            raise _state_invalid("Production recovery project snapshot pointer is invalid.")
        if (
            registry.revision_id != registry_pointer.revision_id
            or registry.content_hash != registry_pointer.content_hash
        ):
            raise _state_invalid("Production recovery registry snapshot pointer is invalid.")

    def _validate_recovery_project_pointer(self, pointer: ProjectSnapshotPointer) -> Path:
        try:
            path = require_canonical_project_snapshot_path(
                pointer.path,
                pointer.revision,
                pointer.content_hash,
                allow_entrypoint=True,
            )
        except ValueError as exc:
            raise _state_invalid(
                "Production recovery project snapshot path is unsafe.", str(exc)
            ) from exc
        self._validate_relative_components(path)
        return self._project_root / path

    def _validate_recovery_registry_pointer(self, pointer: RegistrySnapshotPointer) -> Path:
        try:
            path = require_canonical_registry_snapshot_path(
                pointer.path, pointer.revision_id
            )
        except ValueError as exc:
            raise _state_invalid(
                "Production recovery registry snapshot path is unsafe.", str(exc)
            ) from exc
        self._validate_relative_components(path)
        return self._project_root / path

    def _commit_locked(
        self, request: StateCommitRequest, final_manifest_replaced: list[bool]
    ) -> ProductionManifest:
        running_replaced = False
        running_attempt: StateCommitAttempt | None = None
        with self._exclusive_lock():
            self._validate_request(request)
            candidate_artifacts_hash = _candidate_artifacts_hash(request.artifacts)
            manifest = self._read_manifest()
            existing = next((item for item in manifest.attempts if item.attempt_id == request.attempt_id), None)
            if existing is not None:
                self._validate_replay(existing, request, candidate_artifacts_hash)
                if existing.status is StateCommitStatus.SUCCEEDED:
                    transition = request.dependency_graph_transition
                    if transition is not None:
                        if (
                            manifest.active_project != request.next_project
                            or manifest.active_registry != request.next_registry
                            or manifest.active_dependency_graph
                            != transition.candidate_dependency_graph
                            or manifest.dependency_states
                            != transition.candidate_dependency_states
                        ):
                            raise _state_invalid(
                                "Succeeded P5 commit replay no longer matches active state."
                            )
                        graph = self._reopen_dependency_graph(
                            transition.candidate_dependency_graph
                        )
                        self._verify_dependency_candidate(
                            manifest, graph, manifest.dependency_states
                        )
                    return manifest
                raise _state_invalid("Production state commit attempt ID was already used.")
            graph_transition, candidate_graph = self._validate_request_dependency_transition(
                manifest, request
            )
            unresolved = next(
                (
                    item
                    for item in manifest.attempts
                    if item.status
                    in {
                        StateCommitStatus.RUNNING,
                        StateCommitStatus.OUTCOME_UNKNOWN,
                    }
                ),
                None,
            )
            if unresolved is not None:
                raise _state_invalid(
                    "Production state has an unresolved attempt; explicit recovery is required."
                )
            if manifest.manifest_revision != request.expected_manifest_revision:
                raise _state_invalid("Production Manifest revision is stale.")

            retained_render_state = manifest.active_render_state
            if manifest.schema_version != "2.3" and (
                request.next_project != manifest.active_project
                or request.next_registry != manifest.active_registry
            ):
                retained_render_state = None
            elif retained_render_state is not None:
                try:
                    if manifest.schema_version == "2.3":
                        active_bundle = load_production_project_candidate(
                            self._project_root,
                            manifest,
                            manifest.active_project.path,
                            manifest.active_registry.path,
                        )
                        _load_exact_render_state(active_bundle, retained_render_state)
                    else:
                        load_verified_render_state(
                            self._project_root,
                            retained_render_state,
                            project=manifest.active_project,
                            registry=manifest.active_registry,
                        )
                except AiVideoError as exc:
                    raise _state_invalid(
                        "Active render state could not be retained safely.",
                        exc.technical_detail or str(exc),
                    ) from exc

            running_attempt = StateCommitAttempt(
                attempt_id=request.attempt_id,
                operation=request.operation,
                status=StateCommitStatus.RUNNING,
                base_manifest_revision=manifest.manifest_revision,
                base_project=manifest.active_project,
                base_registry=manifest.active_registry,
                candidate_project=(
                    None if request.operation == "audio_import" else request.next_project
                ),
                candidate_registry=request.next_registry,
                candidate_artifacts_hash=candidate_artifacts_hash,
                base_dependency_graph=(
                    None if graph_transition is None else graph_transition.base_dependency_graph
                ),
                candidate_dependency_graph=(
                    None
                    if graph_transition is None
                    else graph_transition.candidate_dependency_graph
                ),
                candidate_dependency_states_hash=(
                    None
                    if graph_transition is None
                    else graph_transition.candidate_dependency_states_hash
                ),
                started_at=_timestamp(),
            )
            running_manifest = _validated_transition(
                manifest,
                {
                    "schema_version": (
                        "2.2"
                        if request.operation == "audio_import"
                        and manifest.schema_version != "2.3"
                        else manifest.schema_version
                    ),
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": manifest.attempts + (running_attempt,),
                },
            )
            try:
                def mark_running_replaced() -> None:
                    nonlocal running_replaced
                    running_replaced = True

                self._write_manifest_atomic(running_manifest, on_replace=mark_running_replaced)
                self._crash_injector.checkpoint(CommitPhase.AFTER_ATTEMPT_STARTED)
                for artifact in sorted(request.artifacts, key=lambda item: item.relative_path.as_posix()):
                    self._write_immutable_artifact(
                        artifact,
                        attempt_id=request.attempt_id,
                        dependency_graph=(
                            graph_transition is not None
                            and artifact.relative_path
                            == graph_transition.candidate_dependency_graph.path
                        ),
                    )
                self._verify_committed_candidates(request)
                if graph_transition is not None and candidate_graph is not None:
                    self._verify_dependency_candidate(
                        manifest,
                        candidate_graph,
                        graph_transition.candidate_dependency_states,
                        project_pointer=request.next_project,
                        registry_pointer=request.next_registry,
                    )
                succeeded_attempt = _validated_transition(running_attempt, {"status": StateCommitStatus.SUCCEEDED, "finished_at": _timestamp()})
                final_update: dict[str, object] = {
                    "schema_version": (
                        "2.2"
                        if request.operation == "audio_import"
                        and manifest.schema_version != "2.3"
                        else manifest.schema_version
                    ),
                    "manifest_revision": manifest.manifest_revision + 2,
                    "active_project": request.next_project,
                    "active_registry": request.next_registry,
                    "active_render_state": retained_render_state,
                    "attempts": manifest.attempts + (succeeded_attempt,),
                }
                if graph_transition is not None:
                    final_update.update(
                        {
                            "active_dependency_graph": graph_transition.candidate_dependency_graph,
                            "dependency_states": graph_transition.candidate_dependency_states,
                        }
                    )
                final_manifest = _validated_transition(
                    manifest,
                    final_update,
                )

                def mark_manifest_replaced() -> None:
                    final_manifest_replaced[0] = True
                    if graph_transition is not None:
                        self._crash_injector.checkpoint(
                            CommitPhase.AFTER_GRAPH_FINAL_MANIFEST_REPLACE
                        )

                self._write_manifest_atomic(final_manifest, on_replace=mark_manifest_replaced)
                return self._read_manifest()
            except Exception as exc:
                primary = _as_state_error(exc)
                if final_manifest_replaced[0]:
                    raise
                if not running_replaced or running_attempt is None:
                    raise primary from exc
                failed_attempt = _validated_transition(
                    running_attempt,
                    {"status": StateCommitStatus.FAILED, "finished_at": _timestamp(), "error_code": primary.code.value, "error_message": primary.user_message},
                )
                failed_manifest = _validated_transition(
                    manifest,
                    {
                        "schema_version": (
                            "2.2"
                            if request.operation == "audio_import"
                            and manifest.schema_version != "2.3"
                            else manifest.schema_version
                        ),
                        "manifest_revision": manifest.manifest_revision + 2,
                        "attempts": manifest.attempts + (failed_attempt,),
                    },
                )
                try:
                    self._write_manifest_atomic(failed_manifest)
                except BaseException as persist_error:
                    if _is_process_exception(persist_error):
                        persist_error.add_note(
                            "Failed production state attempt persistence interrupted after: "
                            f"{primary} ({exc})"
                        )
                        raise
                    primary.add_note(
                        f"Could not persist failed production state attempt: {persist_error}"
                    )
                raise primary from exc

    def _read_manifest(self) -> ProductionManifest:
        manifest_path = self._state_directory() / "manifest.json"
        self._reject_symlink(manifest_path)
        try:
            return ProductionManifest.model_validate_json(
                manifest_path.read_text(encoding="utf-8")
            )
        except (OSError, ValidationError, ValueError) as exc:
            raise _state_invalid("Could not read Production Manifest.", str(exc)) from exc

    def _validate_request(self, request: StateCommitRequest) -> None:
        if not request.attempt_id or not request.operation:
            raise _state_invalid("Production state commit request is incomplete.")
        if request.expected_manifest_revision < 1:
            raise _state_invalid("Production state expected Manifest revision is invalid.")
        try:
            require_canonical_project_snapshot_path(
                request.next_project.path,
                request.next_project.revision,
                request.next_project.content_hash,
                allow_entrypoint=request.operation in {"audio_import", "voice_generation"},
            )
            require_canonical_registry_snapshot_path(
                request.next_registry.path, request.next_registry.revision_id
            )
        except ValueError as exc:
            raise _state_invalid(
                "Production state commit request uses a noncanonical snapshot path.",
                str(exc),
            ) from exc
        artifacts: dict[Path, PreparedArtifact] = {}
        for artifact in request.artifacts:
            clean_path = self._validate_artifact_path(artifact.relative_path)
            if clean_path in artifacts:
                raise _state_invalid("Production state request contains duplicate artifact paths.")
            if hashlib.sha256(artifact.payload).hexdigest() != artifact.file_sha256:
                raise _state_invalid("Prepared artifact hash does not match its payload.")
            artifacts[clean_path] = artifact
        self._require_pointer_artifact(
            request.next_project.path, request.next_project.file_sha256, artifacts
        )
        self._require_pointer_artifact(
            request.next_registry.path, request.next_registry.file_sha256, artifacts
        )

    @staticmethod
    def _require_pointer_artifact(
        path: Path, file_sha256: str, artifacts: dict[Path, PreparedArtifact]
    ) -> None:
        artifact = artifacts.get(path)
        if artifact is None or artifact.file_sha256 != file_sha256:
            raise _state_invalid("Production snapshot pointer does not match a prepared artifact.")

    @staticmethod
    def _validate_replay(
        existing: StateCommitAttempt,
        request: StateCommitRequest,
        candidate_artifacts_hash: str,
    ) -> None:
        if (
            existing.operation != request.operation
            or not (
                existing.candidate_project == request.next_project
                or (
                    request.operation == "audio_import"
                    and existing.candidate_project is None
                    and request.next_project == existing.base_project
                )
            )
            or existing.candidate_registry != request.next_registry
            or existing.candidate_artifacts_hash != candidate_artifacts_hash
            or (
                request.dependency_graph_transition is None
                and (
                    existing.base_dependency_graph is not None
                    or existing.candidate_dependency_graph is not None
                    or existing.candidate_dependency_states_hash is not None
                )
            )
            or (
                request.dependency_graph_transition is not None
                and (
                    existing.base_dependency_graph
                    != request.dependency_graph_transition.base_dependency_graph
                    or existing.candidate_dependency_graph
                    != request.dependency_graph_transition.candidate_dependency_graph
                    or existing.candidate_dependency_states_hash
                    != request.dependency_graph_transition.candidate_dependency_states_hash
                )
            )
        ):
            raise _state_invalid(
                "Production state commit attempt ID has different candidate snapshots."
            )

    def _verify_committed_candidates(self, request: StateCommitRequest) -> None:
        if request.operation == "audio_import":
            for artifact in request.artifacts:
                snapshot = _read_regular_file_nofollow(
                    self._project_root / artifact.relative_path,
                    contained_by=self._project_root,
                )
                if snapshot.file_sha256 != artifact.file_sha256:
                    raise _state_commit_failed(
                        "Audio import candidate artifact reopen verification failed."
                    )
            project_snapshot = _read_regular_file_nofollow(
                self._project_root / request.next_project.path,
                contained_by=self._project_root,
            )
            registry_snapshot = _read_regular_file_nofollow(
                self._project_root / request.next_registry.path,
                contained_by=self._project_root,
            )
            try:
                project = ProductionProject.model_validate(
                    yaml.safe_load(project_snapshot.data)
                )
                registry = AssetRegistrySnapshot.model_validate_json(
                    registry_snapshot.data
                )
            except (ValidationError, ValueError, yaml.YAMLError) as exc:
                raise _state_commit_failed(
                    "Audio import candidate snapshots could not be reopened.", str(exc)
                ) from exc
            if (
                project.project_id != self._read_manifest().project_id
                or project.revision != request.next_project.revision
                or project.content_hash != request.next_project.content_hash
                or project_snapshot.file_sha256 != request.next_project.file_sha256
                or registry.revision_id != request.next_registry.revision_id
                or registry.content_hash != request.next_registry.content_hash
                or registry_semantic_sha256(registry) != registry.content_hash
                or registry_snapshot.file_sha256 != request.next_registry.file_sha256
            ):
                raise _state_commit_failed(
                    "Audio import candidate snapshot identity is invalid."
                )
            return
        bundle = load_production_project_candidate(
            self._project_root,
            self._read_manifest(),
            request.next_project.path,
            request.next_registry.path,
        )
        project = bundle.project
        registry = bundle.registry
        if (
            project.project_id != self._read_manifest().project_id
            or project.revision != request.next_project.revision
            or project.content_hash != request.next_project.content_hash
        ):
            raise _state_commit_failed("Committed project snapshot verification failed.")
        if (
            registry.revision_id != request.next_registry.revision_id
            or registry.content_hash != request.next_registry.content_hash
        ):
            raise _state_commit_failed("Committed registry snapshot verification failed.")

    def _write_manifest_atomic(
        self, manifest: ProductionManifest, *, on_replace: Callable[[], None] | None = None
    ) -> Path:
        final_path = self._state_directory() / "manifest.json"
        self._write_mutable_atomic(
            final_path,
            _canonical_json_bytes(manifest),
            temp_name=".p2a-manifest.tmp",
            phases=(
                CommitPhase.AFTER_MANIFEST_TEMP_WRITE,
                CommitPhase.AFTER_MANIFEST_FILE_FSYNC,
                CommitPhase.AFTER_MANIFEST_REPLACE,
                CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC,
            ),
            on_replace=on_replace,
        )
        return final_path

    def _write_mutable_atomic(
        self,
        final_path: Path,
        payload: bytes,
        *,
        temp_name: str,
        phases: tuple[CommitPhase, CommitPhase, CommitPhase, CommitPhase] | None = None,
        on_replace: Callable[[], None] | None = None,
    ) -> None:
        final_path = self._validate_final_path(final_path)
        if Path(temp_name).name != temp_name or not temp_name:
            raise _state_invalid("Production state temporary filename is unsafe.")
        temp_path = final_path.parent / temp_name
        if temp_path.parent != final_path.parent:
            raise _state_invalid("Production state temporary path must share final parent.")
        primary: BaseException | None = None
        try:
            with self._ops.open_exclusive(temp_path) as handle:
                handle.write(payload)
                if phases:
                    self._crash_injector.checkpoint(phases[0])
                handle.flush()
                self._ops.fsync_file(handle, temp_path)
                if phases:
                    self._crash_injector.checkpoint(phases[1])
            self._validate_final_path(final_path)
            self._ops.replace(temp_path, final_path)
            if on_replace is not None:
                on_replace()
            if phases:
                self._crash_injector.checkpoint(phases[2])
            self._ops.fsync_directory(final_path.parent)
            if phases:
                self._crash_injector.checkpoint(phases[3])
        except AiVideoError as exc:
            primary = exc
            raise
        except BaseException as exc:
            if not isinstance(exc, Exception):
                primary = exc
                raise
            primary = _state_commit_failed(
                "Could not write production state atomically.", str(exc)
            )
            raise primary from exc
        finally:
            if primary is not None:
                cleanup_errors: list[BaseException] = []
                try:
                    self._validate_cleanup_temp_path(temp_path)
                    self._ops.unlink(temp_path, missing_ok=True)
                except BaseException as cleanup_error:
                    cleanup_errors.append(cleanup_error)
                _handle_cleanup_errors(
                    primary,
                    cleanup_errors,
                    label="Production state temporary cleanup",
                    no_primary_message="Could not clean production state temporary file.",
                )

    def _artifact_checkpoint(
        self, phase: CommitPhase, dependency_graph: bool
    ) -> None:
        self._crash_injector.checkpoint(phase)
        if dependency_graph:
            self._crash_injector.checkpoint(_GRAPH_ARTIFACT_PHASES[phase])

    def _write_immutable_artifact(
        self,
        artifact: PreparedArtifact,
        *,
        attempt_id: str,
        dependency_graph: bool = False,
    ) -> Path:
        expected_sha256 = hashlib.sha256(artifact.payload).hexdigest()
        if artifact.file_sha256 != expected_sha256:
            raise _state_invalid("Prepared artifact hash does not match its payload.")
        final_path = self._validate_artifact_path(artifact.relative_path)
        final_path = self._project_root / final_path
        self._ensure_parent_directory(final_path.parent)
        temp_path = final_path.parent / _owned_temp_name(attempt_id, final_path)
        primary: BaseException | None = None
        try:
            with self._ops.open_exclusive(temp_path) as handle:
                handle.write(artifact.payload)
                self._artifact_checkpoint(
                    CommitPhase.AFTER_ARTIFACT_TEMP_WRITE, dependency_graph
                )
                handle.flush()
                self._ops.fsync_file(handle, temp_path)
                self._artifact_checkpoint(
                    CommitPhase.AFTER_ARTIFACT_FILE_FSYNC, dependency_graph
                )
            self._validate_final_path(final_path)
            self._require_same_filesystem(temp_path, final_path.parent)
            self._validate_final_path(final_path)
            try:
                self._ops.link(temp_path, final_path)
            except FileExistsError:
                if self._ops.sha256_file(final_path) != expected_sha256:
                    raise _state_commit_failed(
                        "Immutable snapshot path already has different bytes."
                    )
            self._artifact_checkpoint(
                CommitPhase.AFTER_ARTIFACT_PROMOTION, dependency_graph
            )
            self._ops.fsync_directory(final_path.parent)
            self._artifact_checkpoint(
                CommitPhase.AFTER_ARTIFACT_DIRECTORY_FSYNC, dependency_graph
            )
            if self._ops.sha256_file(final_path) != expected_sha256:
                raise _state_commit_failed("Immutable snapshot verification failed.")
            self._artifact_checkpoint(
                CommitPhase.AFTER_ARTIFACT_VERIFICATION, dependency_graph
            )
            return final_path
        except AiVideoError as exc:
            primary = exc
            raise
        except BaseException as exc:
            if not isinstance(exc, Exception):
                primary = exc
                raise
            primary = _state_commit_failed(
                "Could not promote immutable production artifact.", str(exc)
            )
            raise primary from exc
        finally:
            cleanup_errors: list[BaseException] = []
            try:
                self._validate_cleanup_temp_path(temp_path)
                self._ops.unlink(temp_path, missing_ok=True)
            except BaseException as cleanup_error:
                cleanup_errors.append(cleanup_error)
            _handle_cleanup_errors(
                primary,
                cleanup_errors,
                label="Immutable temporary cleanup",
                no_primary_message="Could not clean immutable production temporary file.",
            )

    def _state_directory(self) -> Path:
        state_dir = self._project_root / "state"
        self._ensure_directory_chain(state_dir)
        return state_dir

    def _validate_artifact_path(self, relative_path: Path) -> Path:
        if (
            relative_path == Path(".")
            or relative_path.is_absolute()
            or ".." in relative_path.parts
            or relative_path in _RESERVED_TARGETS
            or relative_path.parts[0] in {"runs", ".workflow"}
        ):
            raise _state_invalid("Production artifact target path is unsafe.")
        self._validate_relative_components(relative_path)
        return relative_path

    def _validate_final_path(self, final_path: Path) -> Path:
        try:
            relative_path = final_path.relative_to(self._project_root)
        except ValueError as exc:
            raise _state_invalid("Production state final path escapes project root.") from exc
        self._validate_relative_components(relative_path)
        self._ensure_parent_directory(final_path.parent)
        return final_path

    def _validate_cleanup_temp_path(self, temp_path: Path) -> None:
        try:
            relative_path = temp_path.relative_to(self._project_root)
        except ValueError as exc:
            raise _state_invalid("Production state temporary path escapes project root.") from exc
        self._validate_relative_components(relative_path)

    def _validate_relative_components(self, relative_path: Path) -> None:
        current = self._project_root
        for component in relative_path.parts:
            current = current / component
            self._reject_symlink(current)
        try:
            (self._project_root / relative_path).resolve(strict=False).relative_to(
                self._project_root
            )
        except (OSError, RuntimeError, ValueError) as exc:
            raise _state_invalid("Production artifact target escapes project root.", str(exc)) from exc

    def _ensure_parent_directory(self, parent: Path) -> None:
        self._ensure_directory_chain(parent)

    def _ensure_directory_chain(self, directory: Path) -> None:
        self._validate_final_parent(directory)
        relative_directory = directory.relative_to(self._project_root)
        current = self._project_root
        for component in relative_directory.parts:
            current = current / component
            self._reject_symlink(current)
            if not current.exists():
                try:
                    self._ops.mkdir(current)
                except OSError as exc:
                    raise _state_commit_failed(
                        "Could not create production artifact directory.", str(exc)
                    ) from exc
                self._reject_symlink(current)
            if not current.is_dir():
                raise _state_invalid("Production state path must be a directory.", str(current))
            try:
                self._ops.fsync_directory(current.parent)
            except OSError as exc:
                raise _state_commit_failed(
                    "Could not persist production artifact directory.", str(exc)
                ) from exc

    def _validate_final_parent(self, parent: Path) -> None:
        try:
            relative_parent = parent.relative_to(self._project_root)
        except ValueError as exc:
            raise _state_invalid("Production artifact parent escapes project root.") from exc
        if relative_parent == Path("."):
            return
        self._validate_relative_components(relative_parent)

    @staticmethod
    def _reject_symlink(path: Path) -> None:
        try:
            if path.is_symlink():
                raise _state_invalid("Production state path cannot contain a symlink.", str(path))
        except OSError as exc:
            raise _state_invalid("Production state path could not be inspected.", str(exc)) from exc

    def _require_same_filesystem(self, temp_path: Path, final_parent: Path) -> None:
        try:
            if self._ops.stat(temp_path).st_dev != self._ops.stat(final_parent).st_dev:
                raise _state_unsupported(
                    "Production immutable promotion requires one POSIX filesystem."
                )
        except AiVideoError:
            raise
        except OSError as exc:
            raise _state_commit_failed("Could not verify production artifact filesystem.", str(exc)) from exc


def recover_production_state(project_root: str | Path) -> RecoveryReport:
    """Explicitly recover P2A state after an interrupted process."""
    try:
        return ProductionStateCommitter(project_root).recover()
    except AiVideoError as exc:
        if exc.code in {
            ErrorCode.PRODUCTION_STATE_BUSY,
            ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED,
        }:
            raise
        raise _state_recovery_failed(
            "Could not recover production state.", exc.technical_detail or str(exc)
        ) from exc
