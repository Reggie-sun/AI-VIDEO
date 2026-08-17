from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import BinaryIO, Callable, Protocol

from ai_video.errors import AiVideoError
from ai_video.production.models import ProductionManifest

from ._state_commit_common import (
    _GRAPH_ARTIFACT_PHASES,
    _RESERVED_TARGETS,
    _canonical_json_bytes,
    _handle_cleanup_errors,
    _outcome_unknown,
    _owned_temp_name,
    _state_commit_failed,
    _state_invalid,
    _state_unsupported,
)
from ._state_commit_contracts import CommitPhase, PreparedArtifact


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


class _StateCommitIoMixin:
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

    def _write_p6_manifest_atomic(self, manifest: ProductionManifest) -> Path:
        replaced = False

        def mark_replaced() -> None:
            nonlocal replaced
            replaced = True

        try:
            return self._write_manifest_atomic(manifest, on_replace=mark_replaced)
        except BaseException as exc:
            if replaced:
                raise _outcome_unknown(exc) from exc
            raise

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
