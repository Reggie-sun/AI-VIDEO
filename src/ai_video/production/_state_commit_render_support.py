from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, ValidationError

from ai_video.errors import AiVideoError
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    DependencyGraphSnapshot,
    DependencyLifecycle,
    DependencyNodeKind,
    DependencyNodeState,
    ProductionManifest,
    RenderDependencyEvidence,
    RendererSelectionReceipt,
    RendererSourceReceipt,
    RenderReceipt,
    RenderStateSnapshot,
    RenderStateSnapshotPointer,
    ResolvedTimeline,
    StateCommitAttempt,
)
from ai_video.production.paths import (
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
)

from ._state_commit_common import (
    _bundle_hash_from_pointers,
    _canonical_json_bytes,
    _owned_temp_name,
    _state_commit_failed,
    _state_invalid,
)
from ._state_commit_contracts import (
    ActivateRenderStateRequest,
    BeginRenderAttemptRequest,
    CommitPhase,
    PreparedArtifact,
)


class _StateCommitRenderSupportMixin:
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
        loaded = self._load_verified_render_state(
            self._project_root,
            request.next_render_state,
            project=request.current_project,
            registry=request.current_registry,
        )
        if loaded != state:
            raise _state_commit_failed(
                "Durable render graph reopen verification failed."
            )
