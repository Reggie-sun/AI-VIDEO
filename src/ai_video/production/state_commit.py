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
    ActorIdentity,
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
    PreparedImageCandidate,
    PreparedVoiceCandidate,
    RecordRenderFailureRequest,
    RenderAttemptPaths,
    StateCommitRequest,
    VoiceAttemptPaths,
    VoiceCandidatePreparer,
    VoiceDependencyTransitionPreparer,
    ImageCandidatePreparer,
    _REVIEW_PERMIT_TOKEN,
    _VOICE_PERMIT_TOKEN,
    _DurableReviewAnalysisPermit,
    _DurableImageSubmitPermit,
    _DurablePaidProviderSubmitPermit,
    _DurableVoiceSubmitPermit,
)
from ._state_commit_io import _FileOps, _NativeFileOps, _StateCommitIoMixin
from ._state_commit_recovery import _StateCommitRecoveryMixin
from ._state_commit_recovery_attempts import _StateCommitRecoveryAttemptsMixin
from ._state_commit_recovery_fs import _StateCommitRecoveryFsMixin
from ._state_commit_dependency import _StateCommitDependencyMixin
from ._state_commit_image_activation import _StateCommitImageActivationMixin
from ._state_commit_image_candidate import _StateCommitImageCandidateMixin
from ._state_commit_image_intent import _StateCommitImageIntentMixin
from ._state_commit_image_recovery import _StateCommitImageRecoveryMixin
from ._state_commit_paid_provider import (
    PaidProviderAuthorizer,
    _StateCommitPaidProviderMixin,
)
from ._state_commit_repair import _StateCommitRepairMixin
from ._state_commit_render_lifecycle import _StateCommitRenderLifecycleMixin
from ._state_commit_render_support import _StateCommitRenderSupportMixin
from ._state_commit_review import _StateCommitReviewMixin
from ._state_commit_transaction import _StateCommitTransactionMixin
from ._state_commit_video import _StateCommitVideoMixin
from ._state_commit_voice_activation import _StateCommitVoiceActivationMixin
from ._state_commit_voice_candidate import _StateCommitVoiceCandidateMixin
from ._state_commit_voice_intent import _StateCommitVoiceIntentMixin

if TYPE_CHECKING:
    from ._state_commit_contracts import (
        DurableImageSubmitPermit,
        DurableVoiceSubmitPermit,
    )

try:
    import fcntl
except ImportError:  # pragma: no cover - exercised through platform injection
    fcntl = None  # type: ignore[assignment]






class ProductionStateCommitter(
    _StateCommitVideoMixin,
    _StateCommitPaidProviderMixin,
    _StateCommitReviewMixin,
    _StateCommitRepairMixin,
    _StateCommitImageIntentMixin,
    _StateCommitImageCandidateMixin,
    _StateCommitImageActivationMixin,
    _StateCommitVoiceIntentMixin,
    _StateCommitVoiceCandidateMixin,
    _StateCommitVoiceActivationMixin,
    _StateCommitRenderLifecycleMixin,
    _StateCommitRenderSupportMixin,
    _StateCommitDependencyMixin,
    _StateCommitRecoveryMixin,
    _StateCommitImageRecoveryMixin,
    _StateCommitRecoveryAttemptsMixin,
    _StateCommitRecoveryFsMixin,
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
        image_candidate_preparer: ImageCandidatePreparer | None = None,
        repair_authorizer: Callable[[RepairRequest], ActorIdentity | None] | None = None,
        paid_provider_authorizer: PaidProviderAuthorizer | None = None,
        paid_provider_clock: Callable[[], datetime] | None = None,
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
        self._image_candidate_preparer = image_candidate_preparer
        self._repair_authorizer = repair_authorizer
        self._paid_provider_authorizer = paid_provider_authorizer
        self._paid_provider_clock = paid_provider_clock or (
            lambda: datetime.now(timezone.utc)
        )








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
