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
    ApprovedRepairReceipt,
    ApprovedRepairReceiptPointer,
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
    FinalAcceptanceReceipt,
    FinalAcceptanceReceiptPointer,
    FinalAcceptanceState,
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
    RepairOutcomeReceipt,
    RepairOutcomeReceiptPointer,
    RepairRequest,
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
    ReviewEvidence,
    ReviewEvidencePointer,
    ReviewReceipt,
    ReviewReceiptPointer,
    ReviewRequest,
    ReviewRequestPointer,
    ReviewAttemptPhase,
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
    canonical_approved_repair_receipt_path,
    canonical_final_acceptance_receipt_path,
    canonical_qa_policy_path,
    canonical_repair_outcome_receipt_path,
    canonical_repair_request_path,
    canonical_review_evidence_path,
    canonical_review_receipt_path,
    canonical_review_request_path,
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
    load_production_project,
    load_qa_policy,
    load_review_receipt,
    load_review_request,
    load_verified_render_state,
)
from ai_video.production.dependency import (
    dependency_graph_semantic_sha256,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.review import (
    adjudicate_review_evidence,
    validate_technical_review_context,
)

from ._state_commit_common import (
    _GRAPH_ARTIFACT_PHASES,
    _RESERVED_TARGETS,
    _as_state_error,
    _bundle_hash_from_pointers,
    _candidate_artifacts_evidence_hash,
    _candidate_artifacts_hash,
    _canonical_json_bytes,
    _canonical_yaml_bytes,
    _dependency_states_hash,
    _handle_cleanup_errors,
    _is_process_exception,
    _outcome_unknown,
    _owned_temp_name,
    _owned_temp_prefix,
    _redact_render_error_message,
    _stable_voice_terminal_message,
    _state_commit_failed,
    _state_error,
    _state_invalid,
    _state_recovery_failed,
    _state_unsupported,
    _timestamp,
    _validated_transition,
    prepare_audio_registry_commit,
    prepare_dependency_graph_transition,
    prepare_project_registry_commit,
)
from ._state_commit_contracts import (
    ActivateRenderStateRequest,
    BeginRenderAttemptRequest,
    CommitPhase,
    CrashInjector,
    NoopCrashInjector,
    PreparedArtifact,
    PreparedVoiceCandidate,
    RecordRenderFailureRequest,
    RenderAttemptPaths,
    StateCommitRequest,
    VoiceAttemptPaths,
    VoiceCandidatePreparer,
    VoiceDependencyTransitionPreparer,
    _REVIEW_PERMIT_TOKEN,
    _VOICE_PERMIT_TOKEN,
    _DurableReviewAnalysisPermit,
    _DurableVoiceSubmitPermit,
)
from ._state_commit_io import _FileOps, _NativeFileOps, _StateCommitIoMixin
from ._state_commit_dependency import _StateCommitDependencyMixin
from ._state_commit_repair import _StateCommitRepairMixin
from ._state_commit_render_lifecycle import _StateCommitRenderLifecycleMixin
from ._state_commit_render_support import _StateCommitRenderSupportMixin
from ._state_commit_review import _StateCommitReviewMixin
from ._state_commit_transaction import _StateCommitTransactionMixin
from ._state_commit_voice_activation import _StateCommitVoiceActivationMixin
from ._state_commit_voice_candidate import _StateCommitVoiceCandidateMixin
from ._state_commit_voice_intent import _StateCommitVoiceIntentMixin

if TYPE_CHECKING:
    from ._state_commit_contracts import DurableVoiceSubmitPermit

try:
    import fcntl
except ImportError:  # pragma: no cover - exercised through platform injection
    fcntl = None  # type: ignore[assignment]






class ProductionStateCommitter(
    _StateCommitVoiceIntentMixin,
    _StateCommitVoiceCandidateMixin,
    _StateCommitVoiceActivationMixin,
    _StateCommitReviewMixin,
    _StateCommitRepairMixin,
    _StateCommitDependencyMixin,
    _StateCommitRenderLifecycleMixin,
    _StateCommitRenderSupportMixin,
    _StateCommitTransactionMixin,
    _StateCommitIoMixin,
):
    """Single owner for durable POSIX P2A state commits."""

    def __init__(
        self,
        project_root: str | Path,
        *,
        file_ops: _FileOps | None = None,
        crash_injector: CrashInjector | None = None,
        voice_candidate_preparer: VoiceCandidatePreparer | None = None,
        repair_authorizer: Callable[[RepairRequest], ActorIdentity | None] | None = None,
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
        self._repair_authorizer = repair_authorizer








    @property
    def project_root(self) -> Path:
        return self._project_root


    def _current_render_state(
        self, manifest: ProductionManifest
    ) -> RenderStateSnapshot:
        pointer = manifest.active_render_state
        if pointer is None:
            raise _state_invalid("Current render state is required.")
        snapshot = _read_regular_file_nofollow(
            self._project_root / pointer.path,
            contained_by=self._project_root / "state",
        )
        try:
            state = RenderStateSnapshot.model_validate_json(snapshot.data)
        except (ValidationError, ValueError) as exc:
            raise _state_invalid("Current render state could not be reopened.", str(exc)) from exc
        if (
            snapshot.file_sha256 != pointer.file_sha256
            or state.content_hash != pointer.content_hash
            or state.revision != pointer.revision
            or not verify_artifact_hash(state)
        ):
            raise _state_invalid("Current render state identity is invalid.")
        return state

    def _current_resolved_timeline(
        self, render_state: RenderStateSnapshot
    ) -> ResolvedTimeline:
        pointer = render_state.timeline
        snapshot = _read_regular_file_nofollow(
            self._project_root / pointer.path,
            contained_by=self._project_root / "state",
        )
        try:
            timeline = ResolvedTimeline.model_validate_json(snapshot.data)
        except (ValidationError, ValueError) as exc:
            raise _state_invalid(
                "Current ResolvedTimeline could not be reopened.", str(exc)
            ) from exc
        if (
            snapshot.file_sha256 != pointer.file_sha256
            or timeline.content_hash != pointer.content_hash
            or timeline.revision != pointer.revision
            or timeline.composition_fingerprint
            != render_state.timeline_fingerprint
            or not verify_artifact_hash(timeline)
        ):
            raise _state_invalid("Current ResolvedTimeline identity is invalid.")
        return timeline

    def _load_production_project(
        self,
        project_path: str | Path,
    ) -> LoadedProductionProject:
        return load_production_project(project_path)

    def _load_verified_render_state(
        self,
        root: Path,
        pointer: RenderStateSnapshotPointer,
        *,
        project: ProjectSnapshotPointer,
        registry: RegistrySnapshotPointer,
    ) -> RenderStateSnapshot:
        return load_verified_render_state(
            root,
            pointer,
            project=project,
            registry=registry,
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
            if manifest.schema_version in {"2.3", "2.4"}:
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
        items.extend(self._p6_active_recovery_items(manifest))
        return tuple(items)

    def _p6_active_recovery_items(
        self, manifest: ProductionManifest
    ) -> tuple[RecoveryItem, ...]:
        if manifest.schema_version != "2.4" or manifest.active_qa_policy is None:
            return ()
        pointers: dict[Path, str] = {
            manifest.active_qa_policy.path: manifest.active_qa_policy.file_sha256,
        }
        for receipt_pointer in manifest.active_review_receipts:
            receipt = load_review_receipt(self._project_root, receipt_pointer)
            pointers[receipt_pointer.path] = receipt_pointer.file_sha256
            for evidence_pointer in receipt.evidence:
                pointers[evidence_pointer.path] = evidence_pointer.file_sha256
        if manifest.active_approved_repair is not None:
            pointer = manifest.active_approved_repair
            pointers[pointer.path] = pointer.file_sha256
            snapshot = _read_regular_file_nofollow(
                self._project_root / pointer.path,
                contained_by=self._project_root / "state",
            )
            approved = ApprovedRepairReceipt.model_validate_json(snapshot.data)
            request_path = canonical_repair_request_path(
                approved.request_content_hash
            )
            request_snapshot = _read_regular_file_nofollow(
                self._project_root / request_path,
                contained_by=self._project_root / "state",
            )
            pointers[request_path] = request_snapshot.file_sha256
        for pointer in manifest.repair_outcome_receipts:
            pointers[pointer.path] = pointer.file_sha256
        if (
            manifest.final_acceptance_state is not None
            and manifest.final_acceptance_state.active_receipt is not None
        ):
            pointer = manifest.final_acceptance_state.active_receipt
            pointers[pointer.path] = pointer.file_sha256
        for attempt in manifest.attempts:
            if attempt.review_request is not None:
                pointers[attempt.review_request.path] = attempt.review_request.file_sha256
        items: list[RecoveryItem] = []
        for path, expected_hash in sorted(pointers.items()):
            actual_hash = self._require_recovery_file_hash(
                self._project_root / path, expected_hash
            )
            items.append(
                RecoveryItem(
                    path=path,
                    disposition=RecoveryDisposition.ACTIVE,
                    sha256=actual_hash,
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
            manifest.schema_version not in {"2.3", "2.4"}
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
            if attempt.operation == "review":
                if attempt.review_request is None:
                    raise _state_invalid("Interrupted review attempt has no request.")
                if attempt.status is StateCommitStatus.RUNNING:
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.OUTCOME_UNKNOWN,
                            "review_phase": ReviewAttemptPhase.EVIDENCE,
                            "finished_at": _timestamp(),
                            "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                            "error_message": "Review evidence outcome is unknown; do not rerun analysis blindly.",
                        },
                    )
                    repaired.append(replacement)
                    items.append(
                        RecoveryItem(
                            path=attempt.review_request.path,
                            disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                            sha256=attempt.review_request.file_sha256,
                        )
                    )
                    changed = True
                else:
                    repaired.append(attempt)
                continue
            if attempt.operation == "bootstrap_dependency_graph":
                if (
                    attempt.base_dependency_graph is None
                    and manifest.schema_version in {"2.3", "2.4"}
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
