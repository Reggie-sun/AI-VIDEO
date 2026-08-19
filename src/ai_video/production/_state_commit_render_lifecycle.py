from __future__ import annotations

import hashlib
from pathlib import Path

from ai_video.production.models import (
    DependencyGraphSnapshot,
    DependencyGraphTransition,
    ProductionManifest,
    ReviewLifecycle,
    StateCommitAttempt,
    StateCommitStatus,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_render_attempt_root,
)

from ._state_commit_common import (
    _as_state_error,
    _candidate_artifacts_evidence_hash,
    _candidate_artifacts_hash,
    _dependency_states_hash,
    _is_process_exception,
    _outcome_unknown,
    _redact_render_error_message,
    _state_commit_failed,
    _state_invalid,
    _timestamp,
    _validated_transition,
)
from ._state_commit_contracts import (
    ActivateRenderStateRequest,
    BeginRenderAttemptRequest,
    CommitPhase,
    PreparedArtifact,
    RecordRenderFailureRequest,
    RenderAttemptPaths,
)


class _StateCommitRenderLifecycleMixin:
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
        state = self._load_verified_render_state(
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
                if manifest.schema_version in {"2.3", "2.4", "2.5", "2.6", "2.7", "2.8"}:
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
                if (
                    manifest.schema_version in {"2.4", "2.5", "2.6", "2.7", "2.8"}
                    and manifest.active_qa_policy is not None
                ):
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
