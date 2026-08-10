from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Callable, Iterator, Literal, Protocol

import yaml
from pydantic import BaseModel, ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    AssetRegistrySnapshot,
    LoadedProductionProject,
    ProductionManifest,
    ProductionProject,
    ProjectSnapshotPointer,
    RecoveryDisposition,
    RecoveryItem,
    RecoveryReport,
    RegistrySnapshotPointer,
    RendererSelectionReceipt,
    RendererSourceReceipt,
    RenderReceipt,
    RenderSourceBundlePointer,
    RenderStateSnapshot,
    RenderStateSnapshotPointer,
    ResolvedTimeline,
    StateCommitAttempt,
    StateCommitStatus,
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
)
from ai_video.production.project import (
    _render_source_binding_map,
    _render_source_payload_matches,
    _validate_source_timeline_bindings,
    load_production_project_candidate,
    load_verified_render_state,
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


@dataclass(frozen=True)
class RenderAttemptPaths:
    attempt_root: Path
    source_root: Path
    staged_output_path: Path
    verification_snapshot_path: Path


class CommitPhase(str, Enum):
    AFTER_ATTEMPT_STARTED = "after_attempt_started"
    AFTER_ARTIFACT_TEMP_WRITE = "after_artifact_temp_write"
    AFTER_ARTIFACT_FILE_FSYNC = "after_artifact_file_fsync"
    AFTER_ARTIFACT_PROMOTION = "after_artifact_promotion"
    AFTER_ARTIFACT_DIRECTORY_FSYNC = "after_artifact_directory_fsync"
    AFTER_ARTIFACT_VERIFICATION = "after_artifact_verification"
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


class CrashInjector(Protocol):
    def checkpoint(self, phase: CommitPhase) -> None: ...


class NoopCrashInjector:
    def checkpoint(self, phase: CommitPhase) -> None:
        return None


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


def _validated_transition(model: ProductionManifest | StateCommitAttempt, update: dict[str, object]) -> ProductionManifest | StateCommitAttempt:
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
    ) -> None:
        try:
            self._project_root = Path(project_root).resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise _state_invalid("Production state root is unsafe.", str(exc)) from exc
        if not self._project_root.is_dir():
            raise _state_invalid("Production state root must be a directory.")
        self._ops = file_ops or _NativeFileOps()
        self._crash_injector = crash_injector or NoopCrashInjector()

    @property
    def project_root(self) -> Path:
        return self._project_root

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
                    "schema_version": "2.1",
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
            if existing.status is StateCommitStatus.SUCCEEDED:
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
                final_manifest = _validated_transition(
                    manifest,
                    {
                        "manifest_revision": manifest.manifest_revision + 1,
                        "active_render_state": request.next_render_state,
                        "attempts": tuple(
                            succeeded if item.attempt_id == request.attempt_id else item
                            for item in manifest.attempts
                        ),
                    },
                )

                def mark_final_replaced() -> None:
                    nonlocal final_replaced
                    final_replaced = True

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
        return (
            attempt.candidate_project == request.current_project
            and attempt.candidate_registry == request.current_registry
            and attempt.candidate_render_state == request.next_render_state
            and attempt.candidate_artifacts_hash == candidate_hash
            and attempt.render_phase == "activate"
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
        paths = tuple(item.relative_path for item in request.artifacts)
        if paths != tuple(sorted(paths)):
            raise _state_invalid("Render activation artifacts must be canonically sorted.")
        artifacts: dict[Path, PreparedArtifact] = {}
        for item in request.artifacts:
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
        if manifest.active_render_state is not None:
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
            if attempt.operation == "render_state":
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
                    if (
                        self._render_state_artifacts_hash(
                            state, attempt.candidate_render_state
                        )
                        != attempt.candidate_artifacts_hash
                    ):
                        raise _state_invalid(
                            "Interrupted render candidate artifact hash is invalid."
                        )
                    if manifest.active_render_state == attempt.candidate_render_state:
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
                    else:
                        raise _state_invalid(
                            "Production Manifest selects a mixed interrupted render state."
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
            if active_pair == candidate_pair:
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
            repaired.append(replacement)
            changed = True
        return repaired, changed, items

    @staticmethod
    def _render_state_artifacts_hash(
        state: RenderStateSnapshot, pointer: RenderStateSnapshotPointer
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

    def _remove_owned_attempt_temps(
        self, attempts: list[StateCommitAttempt]
    ) -> tuple[RecoveryItem, ...]:
        items: list[RecoveryItem] = []
        paths: set[Path] = set()
        for attempt in attempts:
            if attempt.status is StateCommitStatus.SUCCEEDED:
                continue
            if attempt.candidate_project is not None:
                project_path = self._validate_recovery_project_pointer(attempt.candidate_project)
                paths.add(project_path.parent / _owned_temp_name(attempt.attempt_id, project_path))
            if attempt.candidate_registry is not None:
                registry_path = self._validate_recovery_registry_pointer(attempt.candidate_registry)
                paths.add(registry_path.parent / _owned_temp_name(attempt.attempt_id, registry_path))
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
        for item in self._render_orphan_items(manifest):
            items.setdefault(item.path, item)
        return tuple(items[path] for path in sorted(items))

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
                    return manifest
                raise _state_invalid("Production state commit attempt ID was already used.")
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
            if (
                request.next_project != manifest.active_project
                or request.next_registry != manifest.active_registry
            ):
                retained_render_state = None
            elif retained_render_state is not None:
                try:
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
                candidate_project=request.next_project,
                candidate_registry=request.next_registry,
                candidate_artifacts_hash=candidate_artifacts_hash,
                started_at=_timestamp(),
            )
            running_manifest = _validated_transition(manifest, {"manifest_revision": manifest.manifest_revision + 1, "attempts": manifest.attempts + (running_attempt,)})
            try:
                def mark_running_replaced() -> None:
                    nonlocal running_replaced
                    running_replaced = True

                self._write_manifest_atomic(running_manifest, on_replace=mark_running_replaced)
                self._crash_injector.checkpoint(CommitPhase.AFTER_ATTEMPT_STARTED)
                for artifact in sorted(request.artifacts, key=lambda item: item.relative_path.as_posix()):
                    self._write_immutable_artifact(artifact, attempt_id=request.attempt_id)
                self._verify_committed_candidates(request)
                succeeded_attempt = _validated_transition(running_attempt, {"status": StateCommitStatus.SUCCEEDED, "finished_at": _timestamp()})
                final_manifest = _validated_transition(
                    manifest,
                    {"manifest_revision": manifest.manifest_revision + 2, "active_project": request.next_project, "active_registry": request.next_registry, "active_render_state": retained_render_state, "attempts": manifest.attempts + (succeeded_attempt,)},
                )

                def mark_manifest_replaced() -> None:
                    final_manifest_replaced[0] = True

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
                    {"manifest_revision": manifest.manifest_revision + 2, "attempts": manifest.attempts + (failed_attempt,)},
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
                allow_entrypoint=False,
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
            or existing.candidate_project != request.next_project
            or existing.candidate_registry != request.next_registry
            or existing.candidate_artifacts_hash != candidate_artifacts_hash
        ):
            raise _state_invalid(
                "Production state commit attempt ID has different candidate snapshots."
            )

    def _verify_committed_candidates(self, request: StateCommitRequest) -> None:
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

    def _write_immutable_artifact(
        self, artifact: PreparedArtifact, *, attempt_id: str
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
                self._crash_injector.checkpoint(CommitPhase.AFTER_ARTIFACT_TEMP_WRITE)
                handle.flush()
                self._ops.fsync_file(handle, temp_path)
                self._crash_injector.checkpoint(CommitPhase.AFTER_ARTIFACT_FILE_FSYNC)
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
            self._crash_injector.checkpoint(CommitPhase.AFTER_ARTIFACT_PROMOTION)
            self._ops.fsync_directory(final_path.parent)
            self._crash_injector.checkpoint(CommitPhase.AFTER_ARTIFACT_DIRECTORY_FSYNC)
            if self._ops.sha256_file(final_path) != expected_sha256:
                raise _state_commit_failed("Immutable snapshot verification failed.")
            self._crash_injector.checkpoint(CommitPhase.AFTER_ARTIFACT_VERIFICATION)
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
