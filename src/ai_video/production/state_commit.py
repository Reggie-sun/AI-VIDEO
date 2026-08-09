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
from typing import BinaryIO, Callable, Iterator, Protocol

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
    StateCommitAttempt,
    StateCommitStatus,
)
from ai_video.production.project import load_production_project_candidate
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
def _as_state_error(exc: BaseException) -> AiVideoError:
    if isinstance(exc, AiVideoError):
        return exc
    return _state_commit_failed("Production state commit failed.", str(exc))
def _candidate_artifacts_hash(artifacts: tuple[PreparedArtifact, ...]) -> str:
    pairs = [(item.relative_path.as_posix(), item.file_sha256) for item in artifacts]
    if len({path for path, _ in pairs}) != len(pairs):
        raise _state_invalid("Production state request contains duplicate artifact paths.")
    payload = json.dumps(sorted(pairs), separators=(",", ":")).encode("utf-8")
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
    project_path = Path(
        f"state/projects/project.{project.revision}.{project.content_hash}.yaml"
    )
    registry_path = Path(f"assets/registry.{registry.revision_id}.json")
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
            attempts, changed, interrupted_items = self._recover_attempts(manifest)

            items.extend(self._remove_fixed_manifest_temp())
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
            items.extend(self._remove_owned_attempt_temps(attempts))
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
        return (
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

    def _remove_fixed_manifest_temp(self) -> tuple[RecoveryItem, ...]:
        return self._remove_recovery_temp(self._state_directory() / ".p2a-manifest.tmp")

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
        for path in sorted(paths):
            items.extend(self._remove_recovery_temp(path))
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
        path = pointer.path
        if path != Path("project.yaml") and not (
            len(path.parts) == 3 and path.parts[:2] == ("state", "projects")
        ):
            raise _state_invalid("Production recovery project snapshot path is unsafe.")
        self._validate_relative_components(path)
        return self._project_root / path

    def _validate_recovery_registry_pointer(self, pointer: RegistrySnapshotPointer) -> Path:
        path = pointer.path
        if len(path.parts) != 2 or path.parts[0] != "assets":
            raise _state_invalid("Production recovery registry snapshot path is unsafe.")
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
            if manifest.manifest_revision != request.expected_manifest_revision:
                raise _state_invalid("Production Manifest revision is stale.")

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
                    {"manifest_revision": manifest.manifest_revision + 2, "active_project": request.next_project, "active_registry": request.next_registry, "attempts": manifest.attempts + (succeeded_attempt,)},
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
