from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from pydantic import ValidationError

from ai_video.errors import AiVideoError
from ai_video.production.dependency import dependency_graph_semantic_sha256
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.models import (
    DependencyGraphSnapshot,
    DependencyGraphSnapshotPointer,
    LoadedProductionProject,
    ProductionManifest,
    ProjectSnapshotPointer,
    RecoveryDisposition,
    RecoveryItem,
    RegistrySnapshotPointer,
    RenderStateSnapshot,
    RenderStateSnapshotPointer,
    StateCommitAttempt,
    StateCommitStatus,
    require_canonical_project_snapshot_path,
    require_canonical_registry_snapshot_path,
)
from ai_video.production.paths import (
    _list_regular_files_nofollow,
    _open_directory_nofollow,
    _read_regular_file_nofollow,
    canonical_dependency_graph_snapshot_path,
    canonical_render_attempt_root,
)
from ai_video.production.project import load_production_project_candidate

from ._state_commit_common import (
    _handle_cleanup_errors,
    _owned_temp_name,
    _owned_temp_prefix,
    _state_commit_failed,
    _state_invalid,
)


class _StateCommitRecoveryFsMixin:
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
                    state = self._load_verified_render_state(
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
        for item in self._p6_orphan_items(manifest):
            items.setdefault(item.path, item)
        return tuple(items[path] for path in sorted(items))

    def _p6_orphan_items(
        self, manifest: ProductionManifest
    ) -> tuple[RecoveryItem, ...]:
        active = {item.path for item in self._p6_active_recovery_items(manifest)}
        namespaces = (
            (
                self._project_root / "state/reviews",
                re.compile(r"^(?:policy|evidence|request|review)\.(?P<hash>[0-9a-f]{64})\.json$"),
            ),
            (
                self._project_root / "state/repairs",
                re.compile(r"^(?:request|approved|outcome)\.(?P<hash>[0-9a-f]{64})\.json$"),
            ),
            (
                self._project_root / "state/acceptance",
                re.compile(r"^final\.(?P<hash>[0-9a-f]{64})\.json$"),
            ),
        )
        items: list[RecoveryItem] = []
        for directory, pattern in namespaces:
            for path, match in self._recovery_namespace_entries(directory, pattern):
                relative = path.relative_to(self._project_root)
                if relative in active:
                    continue
                try:
                    snapshot = _read_regular_file_nofollow(
                        path, contained_by=self._project_root / "state"
                    )
                    payload = json.loads(snapshot.data)
                    if (
                        not isinstance(payload, dict)
                        or payload.get("content_hash") != match.group("hash")
                        or canonical_sha256(payload) != match.group("hash")
                    ):
                        continue
                except (OSError, ValueError, json.JSONDecodeError):
                    continue
                items.append(
                    RecoveryItem(
                        path=relative,
                        disposition=RecoveryDisposition.ORPHAN_PRESERVED,
                        sha256=snapshot.file_sha256,
                    )
                )
        return tuple(items)

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
                active = self._load_verified_render_state(
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
                verified = self._load_verified_render_state(
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
