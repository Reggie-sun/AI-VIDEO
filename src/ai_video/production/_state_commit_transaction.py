from __future__ import annotations

import hashlib
from pathlib import Path

import yaml
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    ApprovedRepairReceipt,
    AssetRegistrySnapshot,
    ProductionManifest,
    ProductionProject,
    StateCommitAttempt,
    StateCommitStatus,
    require_canonical_project_snapshot_path,
    require_canonical_registry_snapshot_path,
)
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.project import (
    _load_exact_render_state,
    load_production_project_candidate,
)
from ai_video.production.registry import registry_semantic_sha256

from ._state_commit_common import (
    _as_state_error,
    _candidate_artifacts_hash,
    _is_process_exception,
    _outcome_unknown,
    _state_commit_failed,
    _state_invalid,
    _timestamp,
    _validated_transition,
)
from ._state_commit_contracts import (
    CommitPhase,
    PreparedArtifact,
    StateCommitRequest,
)


class _StateCommitTransactionMixin:
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
            if request.operation == "repair":
                self._validate_repair_request_against_manifest(manifest, request)
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
            if manifest.schema_version not in {"2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"} and (
                request.next_project != manifest.active_project
                or request.next_registry != manifest.active_registry
            ):
                retained_render_state = None
            elif retained_render_state is not None:
                try:
                    if manifest.schema_version in {"2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"}:
                        active_bundle = load_production_project_candidate(
                            self._project_root,
                            manifest,
                            manifest.active_project.path,
                            manifest.active_registry.path,
                        )
                        _load_exact_render_state(active_bundle, retained_render_state)
                    else:
                        state = self._load_verified_render_state(
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
                approved_repair_receipt=request.approved_repair_receipt,
                started_at=_timestamp(),
            )
            running_manifest = _validated_transition(
                manifest,
                {
                    "schema_version": (
                        "2.2"
                        if request.operation == "audio_import"
                        and manifest.schema_version not in {"2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"}
                        else manifest.schema_version
                    ),
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": manifest.attempts + (running_attempt,),
                    **(
                        {"active_approved_repair": None}
                        if request.operation == "repair"
                        else {}
                    ),
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
                succeeded_attempt = _validated_transition(
                    running_attempt,
                    {
                        "status": StateCommitStatus.SUCCEEDED,
                        "finished_at": _timestamp(),
                    },
                )
                if graph_transition is not None and candidate_graph is not None:
                    verification_attempts = manifest.attempts + (succeeded_attempt,)
                    self._verify_dependency_candidate(
                        manifest,
                        candidate_graph,
                        graph_transition.candidate_dependency_states,
                        project_pointer=request.next_project,
                        registry_pointer=request.next_registry,
                        attempts=verification_attempts,
                    )
                final_update: dict[str, object] = {
                    "schema_version": (
                        "2.2"
                        if request.operation == "audio_import"
                        and manifest.schema_version not in {"2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"}
                        else manifest.schema_version
                    ),
                    "manifest_revision": manifest.manifest_revision + 2,
                    "active_project": request.next_project,
                    "active_registry": request.next_registry,
                    "active_render_state": retained_render_state,
                    "attempts": manifest.attempts + (succeeded_attempt,),
                }
                if request.operation == "repair":
                    final_update["active_approved_repair"] = None
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
                            and manifest.schema_version not in {"2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"}
                            else manifest.schema_version
                        ),
                        "manifest_revision": manifest.manifest_revision + 2,
                        "attempts": manifest.attempts + (failed_attempt,),
                        **(
                            {"active_approved_repair": None}
                            if request.operation == "repair"
                            else {}
                        ),
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
        if request.operation == "repair":
            if request.approved_repair_receipt is None:
                raise AiVideoError(
                    ErrorCode.REPAIR_AUTHORIZATION_REQUIRED,
                    "Production repair requires a durable Approved Repair Receipt.",
                )
            if request.dependency_graph_transition is None:
                raise AiVideoError(
                    ErrorCode.REPAIR_SCOPE_INVALID,
                    "Production repair requires an exact P5 graph transition.",
                )
        elif request.approved_repair_receipt is not None:
            raise _state_invalid("Only repair commits may carry repair authorization.")
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
            or existing.approved_repair_receipt != request.approved_repair_receipt
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

    def _validate_repair_request_against_manifest(
        self, manifest: ProductionManifest, request: StateCommitRequest
    ) -> None:
        pointer = request.approved_repair_receipt
        if pointer is None or manifest.active_approved_repair != pointer:
            raise AiVideoError(
                ErrorCode.REPAIR_AUTHORIZATION_REQUIRED,
                "Production repair authorization is not current.",
            )
        snapshot = _read_regular_file_nofollow(
            self._project_root / pointer.path,
            contained_by=self._project_root / "state",
        )
        try:
            approved = ApprovedRepairReceipt.model_validate_json(snapshot.data)
        except (ValidationError, ValueError) as exc:
            raise _state_invalid(
                "Approved Repair Receipt could not be reopened.", str(exc)
            ) from exc
        if (
            snapshot.file_sha256 != pointer.file_sha256
            or approved.content_hash != pointer.content_hash
            or approved.repair_id != pointer.repair_id
            or not verify_artifact_hash(approved)
        ):
            raise _state_invalid("Approved Repair Receipt identity is invalid.")
        current_render = self._current_render_state(manifest)
        if (
            manifest.active_dependency_graph != approved.dependency_graph
            or self._dependency_states_hash(manifest)
            != approved.dependency_states_hash
            or manifest.active_render_state != approved.render_state
            or current_render.output.file_sha256 != approved.render_output_sha256
            or current_render.timeline_fingerprint != approved.timeline_fingerprint
            or manifest.active_qa_policy != approved.qa_policy
            or tuple(item.review_id for item in manifest.active_review_receipts)
            != approved.review_receipt_ids
        ):
            raise AiVideoError(
                ErrorCode.REPAIR_AUTHORIZATION_REQUIRED,
                "Approved Repair Receipt base identities are stale.",
            )
        transition = request.dependency_graph_transition
        if transition is None:
            raise AiVideoError(
                ErrorCode.REPAIR_SCOPE_INVALID,
                "Production repair requires an exact P5 graph transition.",
            )
        before = {
            item.node_id: item.desired_fingerprint
            for item in manifest.dependency_states
        }
        after = {
            item.node_id: item.desired_fingerprint
            for item in transition.candidate_dependency_states
        }
        actual = tuple(
            sorted(
                node_id
                for node_id in set(before) | set(after)
                if before.get(node_id) != after.get(node_id)
            )
        )
        if actual != tuple(sorted(set(approved.expected_invalidation_node_ids))):
            raise AiVideoError(
                ErrorCode.REPAIR_SCOPE_INVALID,
                "Repair graph transition does not match the approved exact invalidation set.",
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
