from __future__ import annotations

import hashlib
from typing import Mapping

from pydantic import ValidationError

from ai_video.errors import AiVideoError
from ai_video.production.dependency import (
    dependency_graph_semantic_sha256,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    DependencyAppliedEvidence,
    DependencyGraphSnapshot,
    DependencyGraphSnapshotPointer,
    DependencyGraphTransition,
    DependencyLifecycle,
    DependencyNodeKind,
    DependencyNodeState,
    ProductionManifest,
    ProjectDependencyEvidence,
    ProjectSnapshotPointer,
    RegistryDependencyEvidence,
    RegistrySnapshotPointer,
    RenderDependencyEvidence,
    RenderStateSnapshotPointer,
    StateCommitAttempt,
    StateCommitStatus,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_dependency_graph_snapshot_path,
)
from ai_video.production.project import (
    _verify_dependency_project_evidence,
    _verify_dependency_registry_evidence,
    _verify_manifest_dependency_states,
    load_production_project_candidate,
)

from ._state_commit_common import (
    _as_state_error,
    _candidate_artifacts_hash,
    _canonical_json_bytes,
    _dependency_states_hash,
    _outcome_unknown,
    _redact_render_error_message,
    _state_commit_failed,
    _state_invalid,
    _timestamp,
    _validated_transition,
    prepare_dependency_graph_transition,
)
from ._state_commit_contracts import (
    CommitPhase,
    PreparedArtifact,
    StateCommitRequest,
)


class _StateCommitDependencyMixin:
    @staticmethod
    def _dependency_states_hash(manifest: ProductionManifest) -> str:
        return canonical_sha256(
            {"dependency_states": [item.model_dump(mode="json") for item in manifest.dependency_states]}
        )


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
                    "schema_version": (
                        manifest.schema_version
                        if manifest.schema_version in {"2.4", "2.5"}
                        else "2.3"
                    ),
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
        if manifest.schema_version not in {"2.3", "2.4"}:
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
        if manifest.schema_version not in {"2.3", "2.4"}:
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
