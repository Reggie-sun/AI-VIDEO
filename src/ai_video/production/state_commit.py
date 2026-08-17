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

if TYPE_CHECKING:
    from ._state_commit_contracts import DurableVoiceSubmitPermit

try:
    import fcntl
except ImportError:  # pragma: no cover - exercised through platform injection
    fcntl = None  # type: ignore[assignment]






class ProductionStateCommitter(
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


    def voice_attempt_paths(self, attempt_id: str) -> VoiceAttemptPaths:
        try:
            root = canonical_voice_attempt_root(self._project_root, attempt_id)
            return VoiceAttemptPaths(
                attempt_root=root,
                request_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "request.json"
                ),
                preview_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "preview.json"
                ),
                authorization_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "authorization.json"
                ),
                submit_intent_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "submit-intent.json"
                ),
                audio_candidate_path=canonical_voice_audio_candidate_path(
                    self._project_root, attempt_id
                ),
                alignment_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "alignment.json"
                ),
                cost_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "cost.json"
                ),
                provenance_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "provenance.json"
                ),
                outcome_path=canonical_voice_attempt_artifact_path(
                    self._project_root, attempt_id, "outcome.json"
                ),
            )
        except ValueError as exc:
            raise _state_invalid("Voice attempt ID is unsafe.", str(exc)) from exc

    @staticmethod
    def _voice_receipt(
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
    ) -> VoiceRequestReceipt:
        if (
            preview.request_fingerprint != request.voice_request_fingerprint
            or authorization.request_fingerprint != request.voice_request_fingerprint
            or authorization.preview_fingerprint != preview.preview_fingerprint
            or authorization.destination != preview.destination
            or authorization.budget_reservation_receipt_id
            != request.budget_reservation_receipt_id
            or authorization.egress_authorization_receipt_id
            != request.egress_authorization_receipt_id
            or preview.pricing_snapshot_id != request.pricing_snapshot_id
            or authorization.pricing_snapshot_id != request.pricing_snapshot_id
            or authorization.payload_categories != preview.payload_categories
            or authorization.cost_ceiling_microunits
            < preview.estimated_cost_upper_bound_microunits
            or not preview.timing_supported
            or not preview.output_supported
            or not authorization.provider_enabled
        ):
            raise _state_invalid(
                "Voice preview or authorization does not match the immutable request."
            )
        return VoiceRequestReceipt(
            request_id=request.request_id,
            attempt_id=request.attempt_id,
            request_fingerprint=request.voice_request_fingerprint,
            script_hash=request.script_hash,
            provider_kind=request.provider_kind,
            model_id=request.model_id,
            voice_id=request.voice_id,
            language=request.language,
            pricing_snapshot_id=request.pricing_snapshot_id,
            budget_reservation_receipt_id=request.budget_reservation_receipt_id,
            egress_authorization_receipt_id=request.egress_authorization_receipt_id,
            destination=authorization.destination,
        )

    def _voice_prepared_artifact(
        self, attempt_id: str, absolute_path: Path, payload: bytes
    ) -> PreparedArtifact:
        return self.prepare_artifact(
            attempt_id, absolute_path.relative_to(self._project_root), payload
        )

    def begin_voice_generation(
        self,
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
        *,
        dependency_transition_preparer_available: bool = False,
    ) -> ProductionManifest:
        """Persist R+1 request, preview, and authorization evidence without transport."""

        receipt = self._voice_receipt(request, preview, authorization)
        paths = self.voice_attempt_paths(request.attempt_id)
        evidence = (
            self._voice_prepared_artifact(
                request.attempt_id, paths.request_path, _canonical_json_bytes(request)
            ),
            self._voice_prepared_artifact(
                request.attempt_id, paths.preview_path, _canonical_json_bytes(preview)
            ),
            self._voice_prepared_artifact(
                request.attempt_id,
                paths.authorization_path,
                _canonical_json_bytes(authorization),
            ),
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if (
                manifest.schema_version in {"2.3", "2.4"}
                and not dependency_transition_preparer_available
            ):
                raise _state_invalid(
                    "Manifest 2.3 voice generation requires a dependency transition preparer."
                )
            existing = next(
                (item for item in manifest.attempts if item.attempt_id == request.attempt_id),
                None,
            )
            if existing is not None:
                if (
                    existing.operation == "voice_generation"
                    and existing.voice_request == receipt
                    and existing.base_project == request.base_project
                    and existing.base_registry == request.base_registry
                    and existing.voice_phase == "request"
                    and existing.status is StateCommitStatus.RUNNING
                ):
                    reopened = self._reopen_voice_evidence(
                        request.attempt_id, include_intent=False
                    )
                    if reopened != evidence or (
                        _candidate_artifacts_hash(reopened)
                        != existing.candidate_artifacts_hash
                    ):
                        raise _state_invalid("Voice R+1 replay evidence is not exact.")
                    return manifest
                raise _state_invalid("Voice attempt ID was already used by another request.")
            if (
                request.base_project != manifest.active_project
                or request.base_registry != manifest.active_registry
            ):
                raise _state_invalid("Voice request base project or registry is stale.")
            if any(
                item.status in {StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN}
                for item in manifest.attempts
            ):
                raise _state_invalid(
                    "Production state has an unresolved attempt; explicit recovery is required."
                )
            for artifact in evidence:
                self._write_immutable_artifact(artifact, attempt_id=request.attempt_id)
            attempt = StateCommitAttempt(
                attempt_id=request.attempt_id,
                operation="voice_generation",
                status=StateCommitStatus.RUNNING,
                base_manifest_revision=manifest.manifest_revision,
                base_project=manifest.active_project,
                base_registry=manifest.active_registry,
                candidate_artifacts_hash=_candidate_artifacts_hash(evidence),
                voice_request=receipt,
                voice_phase="request",
                started_at=_timestamp(),
            )
            r1 = _validated_transition(
                manifest,
                {
                    "schema_version": (
                        manifest.schema_version
                        if manifest.schema_version in {"2.3", "2.4"}
                        else "2.2"
                    ),
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": manifest.attempts + (attempt,),
                },
            )
            self._write_manifest_atomic(r1)
            return self._read_manifest()

    def record_voice_submit_intent(
        self,
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
    ) -> _DurableVoiceSubmitPermit:
        """Persist R+2, reopen it, and mint exactly one process-local permit."""

        receipt = self._voice_receipt(request, preview, authorization)
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = next(
                (item for item in manifest.attempts if item.attempt_id == request.attempt_id),
                None,
            )
            if (
                attempt is None
                or attempt.operation != "voice_generation"
                or attempt.voice_request != receipt
                or attempt.status is not StateCommitStatus.RUNNING
                or attempt.voice_phase != "request"
                or manifest.active_project != request.base_project
                or manifest.active_registry != request.base_registry
            ):
                raise _state_invalid(
                    "Voice submit intent requires the exact current R+1 attempt."
                )
            self._crash_injector.checkpoint(CommitPhase.BEFORE_VOICE_SUBMIT_INTENT)
            paths = self.voice_attempt_paths(request.attempt_id)
            intent_payload = (
                json.dumps(
                    {
                        "attempt_id": request.attempt_id,
                        "request_fingerprint": request.voice_request_fingerprint,
                        "authorization_fingerprint": authorization.authorization_fingerprint,
                        "destination": authorization.destination,
                        "budget_reservation_receipt_id": authorization.budget_reservation_receipt_id,
                        "egress_authorization_receipt_id": authorization.egress_authorization_receipt_id,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            ).encode()
            artifact = self._voice_prepared_artifact(
                request.attempt_id, paths.submit_intent_path, intent_payload
            )
            r1_artifacts = self._reopen_voice_evidence(request.attempt_id, include_intent=False)
            expected_r1 = (
                self._voice_prepared_artifact(
                    request.attempt_id, paths.request_path, _canonical_json_bytes(request)
                ),
                self._voice_prepared_artifact(
                    request.attempt_id, paths.preview_path, _canonical_json_bytes(preview)
                ),
                self._voice_prepared_artifact(
                    request.attempt_id,
                    paths.authorization_path,
                    _canonical_json_bytes(authorization),
                ),
            )
            if (
                r1_artifacts != expected_r1
                or _candidate_artifacts_hash(r1_artifacts)
                != attempt.candidate_artifacts_hash
            ):
                raise _state_invalid("Voice R+1 evidence changed before submit intent.")
            self._write_immutable_artifact(artifact, attempt_id=request.attempt_id)
            aggregate = _candidate_artifacts_hash((*r1_artifacts, artifact))
            r2_attempt = _validated_transition(
                attempt,
                {
                    "voice_phase": "submit_intent",
                    "candidate_artifacts_hash": aggregate,
                },
            )
            r2 = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        r2_attempt if item.attempt_id == request.attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(r2)
            reopened = self._read_manifest()
            reopened_attempt = next(
                item for item in reopened.attempts if item.attempt_id == request.attempt_id
            )
            if (
                reopened_attempt.voice_phase != "submit_intent"
                or reopened_attempt.candidate_artifacts_hash != aggregate
            ):
                raise _state_commit_failed("Voice submit intent reopen verification failed.")
            intent_snapshot = _read_regular_file_nofollow(
                paths.submit_intent_path,
                contained_by=self._project_root,
            )
            if (
                intent_snapshot.data != intent_payload
                or intent_snapshot.file_sha256 != artifact.file_sha256
            ):
                raise _state_commit_failed("Voice submit intent exact-byte verification failed.")
            manifest_snapshot = _read_regular_file_nofollow(
                self._project_root / "state/manifest.json",
                contained_by=self._project_root,
            )
            self._crash_injector.checkpoint(CommitPhase.AFTER_VOICE_SUBMIT_INTENT)
            binding = {
                "attempt_id": request.attempt_id,
                "request_fingerprint": request.voice_request_fingerprint,
                "authorization_fingerprint": authorization.authorization_fingerprint,
                "destination": authorization.destination,
                "budget_reservation_receipt_id": authorization.budget_reservation_receipt_id,
                "egress_authorization_receipt_id": authorization.egress_authorization_receipt_id,
            }
            return _DurableVoiceSubmitPermit(
                _VOICE_PERMIT_TOKEN,
                binding=binding,
                manifest_revision=reopened.manifest_revision,
                manifest_file_sha256=manifest_snapshot.file_sha256,
                durability_validator=lambda: self._voice_submit_intent_is_current(
                    reopened.manifest_revision,
                    manifest_snapshot.file_sha256,
                    request.attempt_id,
                    aggregate,
                    artifact.file_sha256,
                    intent_payload,
                ),
            )

    def _reopen_voice_evidence(
        self, attempt_id: str, *, include_intent: bool
    ) -> tuple[PreparedArtifact, ...]:
        paths = self.voice_attempt_paths(attempt_id)
        selected = [paths.request_path, paths.preview_path, paths.authorization_path]
        if include_intent:
            selected.append(paths.submit_intent_path)
        artifacts = []
        for path in selected:
            snapshot = _read_regular_file_nofollow(path, contained_by=self._project_root)
            artifacts.append(
                PreparedArtifact(
                    relative_path=path.relative_to(self._project_root),
                    payload=snapshot.data,
                    file_sha256=snapshot.file_sha256,
                )
            )
        return tuple(artifacts)

    def _voice_submit_intent_is_current(
        self,
        manifest_revision: int,
        manifest_file_sha256: str,
        attempt_id: str,
        aggregate_hash: str,
        intent_sha256: str,
        intent_payload: bytes,
    ) -> bool:
        try:
            snapshot = _read_regular_file_nofollow(
                self._project_root / "state/manifest.json",
                contained_by=self._project_root,
            )
            if snapshot.file_sha256 != manifest_file_sha256:
                return False
            manifest = ProductionManifest.model_validate_json(snapshot.data)
            evidence = self._reopen_voice_evidence(attempt_id, include_intent=True)
        except (AiVideoError, OSError, ValidationError, ValueError):
            return False
        attempt = next(
            (item for item in manifest.attempts if item.attempt_id == attempt_id), None
        )
        return (
            manifest.manifest_revision == manifest_revision
            and attempt is not None
            and attempt.operation == "voice_generation"
            and attempt.status is StateCommitStatus.RUNNING
            and attempt.voice_phase == "submit_intent"
            and attempt.candidate_artifacts_hash == aggregate_hash
            and _candidate_artifacts_hash(evidence) == aggregate_hash
            and evidence[-1].file_sha256 == intent_sha256
            and evidence[-1].payload == intent_payload
        )

    def _record_voice_terminal(
        self,
        attempt_id: str,
        *,
        status: StateCommitStatus,
        phase: Literal[
            "request",
            "submit_intent",
            "provider_call",
            "materialize",
            "probe",
            "align",
            "candidate",
            "activate",
        ],
        error_code: str,
        error_message: str,
    ) -> ProductionManifest:
        if status not in {StateCommitStatus.FAILED, StateCommitStatus.OUTCOME_UNKNOWN}:
            raise _state_invalid("Voice terminal transition status is invalid.")
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = next(
                (item for item in manifest.attempts if item.attempt_id == attempt_id), None
            )
            stable_message = _stable_voice_terminal_message(status, phase)
            if attempt is None or attempt.operation != "voice_generation":
                raise _state_invalid("Voice terminal transition has no matching attempt.")
            if attempt.status is status:
                if (
                    attempt.voice_phase == phase
                    and attempt.error_code == error_code
                    and attempt.error_message == stable_message
                ):
                    return manifest
                raise _state_invalid("Voice terminal replay does not match durable state.")
            if attempt.status is not StateCommitStatus.RUNNING:
                raise _state_invalid("Voice terminal transition is stale.")
            terminal_attempt = _validated_transition(
                attempt,
                {
                    "status": status,
                    "voice_phase": phase,
                    "finished_at": _timestamp(),
                    "error_code": error_code,
                    "error_message": stable_message,
                },
            )
            terminal = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        terminal_attempt if item.attempt_id == attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(terminal)
            return self._read_manifest()

    def record_voice_failure(
        self,
        attempt_id: str,
        *,
        phase: Literal[
            "request", "submit_intent", "provider_call", "materialize", "probe", "align", "candidate", "activate"
        ],
        error_code: str,
        error_message: str,
    ) -> ProductionManifest:
        return self._record_voice_terminal(
            attempt_id,
            status=StateCommitStatus.FAILED,
            phase=phase,
            error_code=error_code,
            error_message=error_message,
        )

    def record_voice_outcome_unknown(
        self,
        attempt_id: str,
        *,
        phase: Literal[
            "submit_intent", "provider_call", "materialize", "probe", "align", "candidate", "activate"
        ],
        error_code: str = ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN.value,
        error_message: str = "Voice provider outcome is unknown; blind retry is forbidden.",
    ) -> ProductionManifest:
        return self._record_voice_terminal(
            attempt_id,
            status=StateCommitStatus.OUTCOME_UNKNOWN,
            phase=phase,
            error_code=error_code,
            error_message=error_message,
        )

    @staticmethod
    def _validate_voice_provider_result(
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
        result: VoiceProviderResult,
    ) -> None:
        if not isinstance(result, VoiceProviderResult):
            raise _state_invalid("Voice provider returned an untyped result.")
        if (
            result.request_id != request.request_id
            or result.request_fingerprint != request.voice_request_fingerprint
            or result.preview_fingerprint != preview.preview_fingerprint
            or result.authorization_fingerprint
            != authorization.authorization_fingerprint
            or result.content_type not in {"audio/wav", "audio/x-wav"}
            or result.cost_receipt.pricing_snapshot_id
            != request.pricing_snapshot_id
            or result.cost_receipt.estimated_cost_upper_bound_microunits
            != preview.estimated_cost_upper_bound_microunits
            or (
                result.cost_receipt.provider_reported_cost_microunits is not None
                and result.cost_receipt.provider_reported_cost_microunits
                > authorization.cost_ceiling_microunits
            )
            or result.provenance_receipt.provider_kind != request.provider_kind
            or result.provenance_receipt.model_id != request.model_id
            or result.provenance_receipt.voice_id != request.voice_id
            or result.provenance_receipt.language != request.language
            or result.provenance_receipt.script_hash != request.script_hash
            or result.provenance_receipt.egress_authorization_receipt_id
            != request.egress_authorization_receipt_id
        ):
            raise _state_invalid(
                "Voice provider result contradicts request, preview, authorization, or receipts."
            )

    def _prepare_voice_activation_request(
        self,
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
        result: VoiceProviderResult,
        prepared: PreparedVoiceCandidate,
    ) -> tuple[StateCommitRequest, tuple[str, ...], tuple[str, ...]]:
        self._validate_voice_provider_result(request, preview, authorization, result)
        if not isinstance(prepared, PreparedVoiceCandidate) or not isinstance(
            prepared.audio, PreparedAudioImport
        ):
            raise _state_invalid("Voice candidate preparer returned an unsafe capability.")
        audio = prepared.audio
        probe = audio.probe
        if (
            audio.payload != result.audio_bytes
            or probe.file_sha256 != result.audio_sha256
            or probe.size_bytes != len(result.audio_bytes)
            or probe.mime_type != result.content_type
            or probe.codec_name != request.output_codec
            or probe.sample_rate_hz != request.output_sample_rate_hz
            or probe.channels != request.output_channels
        ):
            raise _state_invalid("Prepared voice audio does not match the exact provider result.")

        paths = self.voice_attempt_paths(request.attempt_id)
        provenance_bytes = _canonical_json_bytes(result.provenance_receipt)
        cost_bytes = _canonical_json_bytes(result.cost_receipt)
        provenance_hash = hashlib.sha256(provenance_bytes).hexdigest()
        cost_hash = hashlib.sha256(cost_bytes).hexdigest()
        alignment_hash = result.alignment_receipt_sha256
        audio_id = f"voice-{request.attempt_id}"
        audio_record = AssetRecord(
            asset_id=audio_id,
            asset_type=AssetType.VOICE,
            artifact_path=canonical_audio_asset_path(result.audio_sha256),
            sha256=result.audio_sha256,
            size_bytes=len(result.audio_bytes),
            mime_type=result.content_type,
            source_kind=AssetSourceKind.GENERATED,
            tool=result.provenance_receipt.adapter,
            input_artifact_ids=request.input_artifact_ids,
            input_fingerprint=request.input_fingerprint,
            creation_receipt_id=f"voice-result-{result.result_fingerprint}",
            usage_license=result.provenance_receipt.license_policy_decision,
            egress=EgressMetadata(
                remote=True,
                destination=authorization.destination,
                authorization_receipt_id=request.egress_authorization_receipt_id,
                request_fingerprint=request.voice_request_fingerprint,
                payload_fingerprint=request.script_hash,
                retention_mode=result.provenance_receipt.retention_mode,
                provider_policy_snapshot_id=result.provenance_receipt.policy_receipt_id,
            ),
            cost_receipt_id=f"cost-{cost_hash}",
            audio_metadata=AudioAssetMetadata(
                audio_kind=request.audio_kind,
                source=AudioSource(
                    kind=AssetSourceKind.GENERATED,
                    provider_or_tool=result.provenance_receipt.adapter,
                    input_artifact_ids=request.input_artifact_ids,
                    input_fingerprint=request.input_fingerprint,
                ),
                speaker_id=request.speaker_id,
                voice_id=request.voice_id,
                language=request.language,
                script_hash=request.script_hash,
                duration_samples=probe.duration_samples,
                sample_rate_hz=probe.sample_rate_hz,
                channels=probe.channels,
                channel_layout=probe.channel_layout,
                codec_name=probe.codec_name,
                loudness=probe.loudness,
                provenance_receipt_id=f"provenance-{provenance_hash}",
                alignment_receipt_id=f"alignment-{alignment_hash}",
            ),
        )
        asset_artifacts = [
            PreparedArtifact(audio_record.artifact_path, audio.payload, result.audio_sha256)
        ]
        new_records = [audio_record]
        caption_ids: tuple[str, ...] = ()
        if prepared.caption is not None:
            assert prepared.caption_asset_record is not None
            caption = prepared.caption
            supplied = prepared.caption_asset_record
            caption_id = f"caption-{request.attempt_id}"
            try:
                CaptionImportRequest(
                    caption_track=caption.caption_track,
                    track_bytes=caption.track_bytes,
                    track_sha256=caption.track_sha256,
                    style_reference=caption.style_reference,
                    style_bytes=caption.style_bytes,
                    style_sha256=caption.style_sha256,
                )
            except ValidationError as exc:
                raise _state_invalid("Prepared caption bytes are not canonical.", str(exc)) from exc
            track = caption.caption_track
            expected_caption_record = AssetRecord(
                asset_id=caption_id,
                asset_type=AssetType.CAPTION,
                artifact_path=Path(f"assets/captions/{caption.track_sha256}.json"),
                sha256=caption.track_sha256,
                size_bytes=len(caption.track_bytes),
                mime_type="application/json",
                source_kind=AssetSourceKind.DERIVED,
                tool=result.provenance_receipt.adapter,
                input_artifact_ids=(audio_id,),
                input_fingerprint=result.audio_sha256,
                creation_receipt_id=track.creation_receipt_id,
                usage_license=result.provenance_receipt.license_policy_decision,
                caption_metadata=CaptionAssetMetadata(
                    caption_track_id=track.caption_track_id,
                    language=track.language,
                    source_audio_asset_id=audio_id,
                    source_audio_sha256=result.audio_sha256,
                    script_hash=track.script_hash,
                    transcript_hash=track.transcript_hash,
                    segment_count=len(track.segments),
                    word_count=sum(len(item.words or ()) for item in track.segments),
                    segmentation_policy_id=track.segmentation_policy.policy_id,
                    segmentation_policy_version=track.segmentation_policy.policy_version,
                    alignment_receipt_id=track.alignment_receipt_id,
                    timing_fingerprint=track.timing_fingerprint,
                    style_reference_id=(
                        caption.style_reference.artifact_id
                        if caption.style_reference is not None
                        else None
                    ),
                    style_content_hash=(
                        caption.style_reference.content_hash
                        if caption.style_reference is not None
                        else None
                    ),
                    style_reference_revision=(
                        caption.style_reference.revision
                        if caption.style_reference is not None
                        else None
                    ),
                ),
            )
            if (
                supplied != expected_caption_record
                or track.source_audio_asset_id != audio_id
                or track.source_audio_sha256 != result.audio_sha256
                or track.script_hash != request.script_hash
                or track.transcript_hash != request.script_hash
                or track.source_sample_rate_hz != request.output_sample_rate_hz
                or track.language != request.language
                or track.alignment_receipt_id
                != f"alignment-{result.alignment_receipt_sha256}"
                or track.creation_receipt_id
                != f"caption-result-{result.result_fingerprint}"
                or track.source_provenance
                != (
                    SourceReference(
                        kind="derived",
                        reference=f"alignment-{result.alignment_receipt_sha256}",
                    ),
                )
                or track.timing_fingerprint != caption_timing_fingerprint(track)
            ):
                raise _state_invalid("Prepared caption identity does not match generated voice.")
            new_records.append(supplied)
            asset_artifacts.append(
                PreparedArtifact(supplied.artifact_path, caption.track_bytes, caption.track_sha256)
            )
            if caption.style_reference is not None:
                assert caption.style_bytes is not None and caption.style_sha256 is not None
                asset_artifacts.append(
                    PreparedArtifact(
                        caption.style_reference.path,
                        caption.style_bytes,
                        caption.style_sha256,
                    )
                )
            caption_ids = (caption_id,)

        manifest = self._read_manifest()
        project_snapshot = _read_regular_file_nofollow(
            self._project_root / request.base_project.path,
            contained_by=self._project_root,
        )
        registry_snapshot = _read_regular_file_nofollow(
            self._project_root / request.base_registry.path,
            contained_by=self._project_root,
        )
        try:
            project = ProductionProject.model_validate(yaml.safe_load(project_snapshot.data))
            base_registry = AssetRegistrySnapshot.model_validate_json(registry_snapshot.data)
        except (ValidationError, ValueError, yaml.YAMLError) as exc:
            raise _state_invalid("Voice base project or registry could not be reopened.", str(exc)) from exc
        ordered_new = tuple(sorted(new_records, key=lambda item: item.asset_id))
        registry = AssetRegistrySnapshot(
            schema_version="2.1",
            revision_id="0" * 64,
            content_hash="0" * 64,
            assets=base_registry.assets + ordered_new,
        )
        registry_hash = registry_semantic_sha256(registry)
        registry = registry.model_copy(
            update={"revision_id": registry_hash, "content_hash": registry_hash}
        )
        base_commit = prepare_audio_registry_commit(
            manifest=manifest,
            project=project,
            base_registry=base_registry,
            registry=registry,
            attempt_id=request.attempt_id,
            artifacts=tuple(asset_artifacts),
            active_project_artifact=PreparedArtifact(
                request.base_project.path, project_snapshot.data, project_snapshot.file_sha256
            ),
        )
        outcome_payload = (
            json.dumps(
                {
                    "request_id": result.request_id,
                    "request_fingerprint": result.request_fingerprint,
                    "preview_fingerprint": result.preview_fingerprint,
                    "authorization_fingerprint": result.authorization_fingerprint,
                    "result_fingerprint": result.result_fingerprint,
                    "provider_request_id": result.provider_request_id,
                    "provider_trace_id": result.provider_trace_id,
                    "audio_sha256": result.audio_sha256,
                    "alignment_receipt_sha256": result.alignment_receipt_sha256,
                    "content_type": result.content_type,
                    "policy_receipt_id": result.provenance_receipt.policy_receipt_id,
                    "retention_mode": result.provenance_receipt.retention_mode,
                    "terminal_status": result.terminal_status,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode()
        evidence = (
            *self._reopen_voice_evidence(request.attempt_id, include_intent=True),
            PreparedArtifact(
                paths.alignment_path.relative_to(self._project_root),
                result.alignment_receipt_bytes,
                alignment_hash,
            ),
            PreparedArtifact(
                paths.cost_path.relative_to(self._project_root), cost_bytes, cost_hash
            ),
            PreparedArtifact(
                paths.provenance_path.relative_to(self._project_root),
                provenance_bytes,
                provenance_hash,
            ),
            PreparedArtifact(
                paths.outcome_path.relative_to(self._project_root),
                outcome_payload,
                hashlib.sha256(outcome_payload).hexdigest(),
            ),
        )
        by_path = {
            item.relative_path: item for item in (*base_commit.artifacts, *evidence)
        }
        commit = StateCommitRequest(
            attempt_id=request.attempt_id,
            operation="voice_generation",
            expected_manifest_revision=manifest.manifest_revision,
            artifacts=tuple(sorted(by_path.values(), key=lambda item: item.relative_path.as_posix())),
            next_project=base_commit.next_project,
            next_registry=base_commit.next_registry,
        )
        return commit, (audio_id,), caption_ids

    def activate_voice_assets(
        self,
        request: StateCommitRequest,
        *,
        audio_asset_ids: tuple[str, ...],
        caption_asset_ids: tuple[str, ...] = (),
    ) -> ProductionManifest:
        """Persist R+3 exact candidates, then atomically select R+4 without transport."""

        if request.operation != "voice_generation" or not audio_asset_ids:
            raise _state_invalid("Voice activation request is incomplete.")
        self._validate_request(request)
        registry_artifact = next(
            (
                item
                for item in request.artifacts
                if item.relative_path == request.next_registry.path
            ),
            None,
        )
        if registry_artifact is None:
            raise _state_invalid("Voice activation registry artifact is missing.")
        try:
            candidate_registry = AssetRegistrySnapshot.model_validate_json(
                registry_artifact.payload
            )
        except (ValidationError, ValueError) as exc:
            raise _state_invalid("Voice activation registry artifact is invalid.", str(exc)) from exc
        by_id = {item.asset_id: item for item in candidate_registry.assets}
        if set(audio_asset_ids).intersection(caption_asset_ids) or any(
            asset_id not in by_id
            or by_id[asset_id].asset_type
            not in {AssetType.VOICE, AssetType.MUSIC, AssetType.SFX}
            for asset_id in audio_asset_ids
        ) or any(
            asset_id not in by_id or by_id[asset_id].asset_type is not AssetType.CAPTION
            for asset_id in caption_asset_ids
        ):
            raise _state_invalid("Voice activation asset IDs do not match the candidate registry.")
        candidate_hash = _candidate_artifacts_hash(request.artifacts)
        final_replaced = False
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = next(
                (item for item in manifest.attempts if item.attempt_id == request.attempt_id),
                None,
            )
            if attempt is None or attempt.operation != "voice_generation":
                raise _state_invalid("Voice activation has no matching attempt.")
            graph_transition: DependencyGraphTransition | None = None
            candidate_graph: DependencyGraphSnapshot | None = None
            if attempt.status is StateCommitStatus.SUCCEEDED:
                transition = request.dependency_graph_transition
                if manifest.schema_version in {"2.3", "2.4"}:
                    if transition is None or (
                        attempt.base_dependency_graph != transition.base_dependency_graph
                        or attempt.candidate_dependency_graph
                        != transition.candidate_dependency_graph
                        or attempt.candidate_dependency_states_hash
                        != transition.candidate_dependency_states_hash
                        or manifest.active_dependency_graph
                        != transition.candidate_dependency_graph
                        or manifest.dependency_states
                        != transition.candidate_dependency_states
                    ):
                        raise _state_invalid(
                            "Succeeded voice replay dependency transition does not match active state."
                        )
                    graph_transition = transition
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
            else:
                graph_transition, candidate_graph = self._validate_dependency_transition(
                    manifest,
                    expected_manifest_revision=request.expected_manifest_revision,
                    artifacts=request.artifacts,
                    transition=request.dependency_graph_transition,
                )
            if (
                manifest.schema_version not in {"2.3", "2.4"}
                and (
                    attempt.status is StateCommitStatus.SUCCEEDED
                    or attempt.voice_phase == "candidate"
                )
            ):
                durable_request = self._reconstruct_voice_activation_request(attempt)
                if durable_request != request:
                    raise _state_invalid(
                        "Voice activation replay does not match the current durable candidate graph."
                    )
            provider_request_id = self._validate_voice_activation_graph(
                request,
                attempt,
                candidate_registry,
                audio_asset_ids,
                caption_asset_ids,
            )
            if attempt.status is StateCommitStatus.SUCCEEDED:
                if (
                    manifest.active_registry == request.next_registry
                    and attempt.candidate_artifacts_hash == candidate_hash
                    and attempt.candidate_audio_asset_ids == audio_asset_ids
                    and attempt.candidate_caption_asset_ids == caption_asset_ids
                ):
                    return manifest
                raise _state_invalid("Succeeded voice replay does not match active state.")
            candidate_exists = attempt.voice_phase == "candidate"
            if candidate_exists:
                if (
                    attempt.status not in {StateCommitStatus.RUNNING, StateCommitStatus.INTERRUPTED}
                    or attempt.candidate_project not in (None, request.next_project)
                    or attempt.candidate_registry != request.next_registry
                    or attempt.candidate_artifacts_hash != candidate_hash
                    or attempt.candidate_audio_asset_ids != audio_asset_ids
                    or attempt.candidate_caption_asset_ids != caption_asset_ids
                    or (
                        graph_transition is not None
                        and (
                            attempt.base_dependency_graph
                            != graph_transition.base_dependency_graph
                            or attempt.candidate_dependency_graph
                            != graph_transition.candidate_dependency_graph
                            or attempt.candidate_dependency_states_hash
                            != graph_transition.candidate_dependency_states_hash
                        )
                    )
                ):
                    raise _state_invalid("Voice candidate replay identity does not match.")
            else:
                if (
                    attempt.status is not StateCommitStatus.RUNNING
                    or attempt.voice_phase not in {
                        "submit_intent", "provider_call", "materialize", "probe", "align"
                    }
                    or manifest.manifest_revision != request.expected_manifest_revision
                    or manifest.active_project != attempt.base_project
                    or manifest.active_registry != attempt.base_registry
                    or request.next_project != attempt.base_project
                ):
                    raise _state_invalid("Voice activation base state or revision is stale.")
                for artifact in sorted(
                    request.artifacts, key=lambda item: item.relative_path.as_posix()
                ):
                    self._write_immutable_artifact(
                        artifact,
                        attempt_id=request.attempt_id,
                        dependency_graph=(
                            graph_transition is not None
                            and artifact.relative_path
                            == graph_transition.candidate_dependency_graph.path
                        ),
                    )
                self._verify_voice_committed_candidates(request)
                candidate_attempt = _validated_transition(
                    attempt,
                    {
                        "candidate_project": None,
                        "candidate_registry": request.next_registry,
                        "candidate_artifacts_hash": candidate_hash,
                        "candidate_audio_asset_ids": audio_asset_ids,
                        "candidate_caption_asset_ids": caption_asset_ids,
                        "provider_request_id": provider_request_id,
                        "voice_phase": "candidate",
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
                if graph_transition is not None and candidate_graph is not None:
                    verification_attempt = _validated_transition(
                        candidate_attempt,
                        {
                            "status": StateCommitStatus.SUCCEEDED,
                            "voice_phase": "activate",
                            "finished_at": _timestamp(),
                            "error_code": None,
                            "error_message": None,
                        },
                    )
                    verification_attempts = tuple(
                        verification_attempt
                        if item.attempt_id == request.attempt_id
                        else item
                        for item in manifest.attempts
                    )
                    self._verify_dependency_candidate(
                        manifest,
                        candidate_graph,
                        graph_transition.candidate_dependency_states,
                        project_pointer=request.next_project,
                        registry_pointer=request.next_registry,
                        attempts=verification_attempts,
                    )
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
                self._write_manifest_atomic(candidate_manifest)
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_VOICE_CANDIDATE_MANIFEST
                )
                manifest = self._read_manifest()
                attempt = next(
                    item for item in manifest.attempts if item.attempt_id == request.attempt_id
                )
            succeeded = _validated_transition(
                attempt,
                {
                    "status": StateCommitStatus.SUCCEEDED,
                    "voice_phase": "activate",
                    "finished_at": _timestamp(),
                    "error_code": None,
                    "error_message": None,
                },
            )
            final_update: dict[str, object] = {
                "manifest_revision": manifest.manifest_revision + 1,
                "active_project": request.next_project,
                "active_registry": request.next_registry,
                "active_render_state": (
                    manifest.active_render_state
                    if manifest.schema_version in {"2.3", "2.4"}
                    else None
                ),
                "attempts": tuple(
                    succeeded if item.attempt_id == request.attempt_id else item
                    for item in manifest.attempts
                ),
            }
            if graph_transition is not None:
                final_update.update(
                    {
                        "active_dependency_graph": graph_transition.candidate_dependency_graph,
                        "dependency_states": graph_transition.candidate_dependency_states,
                    }
                )
            final = _validated_transition(
                manifest,
                final_update,
            )

            def mark_replaced() -> None:
                nonlocal final_replaced
                final_replaced = True
                if graph_transition is not None:
                    self._crash_injector.checkpoint(
                        CommitPhase.AFTER_GRAPH_FINAL_MANIFEST_REPLACE
                    )

            try:
                self._write_manifest_atomic(final, on_replace=mark_replaced)
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_VOICE_FINAL_MANIFEST_REPLACE
                )
                return self._read_manifest()
            except Exception as exc:
                if final_replaced:
                    raise _outcome_unknown(exc) from exc
                raise

    def _validate_voice_activation_graph(
        self,
        commit: StateCommitRequest,
        attempt: StateCommitAttempt,
        candidate_registry: AssetRegistrySnapshot,
        audio_asset_ids: tuple[str, ...],
        caption_asset_ids: tuple[str, ...],
    ) -> str | None:
        if len(set(caption_asset_ids)) != len(caption_asset_ids):
            raise _state_invalid("Voice candidate graph contains duplicate caption asset IDs.")
        paths = self.voice_attempt_paths(commit.attempt_id)
        artifacts = {item.relative_path: item for item in commit.artifacts}
        evidence_paths = {
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
        }
        if not evidence_paths.issubset(artifacts):
            raise _state_invalid("Voice candidate graph is missing durable lifecycle evidence.")
        try:
            voice_request = VoiceGenerationRequest.model_validate_json(
                artifacts[paths.request_path.relative_to(self._project_root)].payload
            )
            preview = VoiceGenerationPreview.model_validate_json(
                artifacts[paths.preview_path.relative_to(self._project_root)].payload
            )
            authorization = VoiceCallAuthorization.model_validate_json(
                artifacts[paths.authorization_path.relative_to(self._project_root)].payload
            )
            cost = VoiceCostReceipt.model_validate_json(
                artifacts[paths.cost_path.relative_to(self._project_root)].payload
            )
            provenance = VoiceProvenanceReceipt.model_validate_json(
                artifacts[paths.provenance_path.relative_to(self._project_root)].payload
            )
            outcome = json.loads(
                artifacts[paths.outcome_path.relative_to(self._project_root)].payload
            )
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            raise _state_invalid("Voice candidate evidence is malformed.", str(exc)) from exc
        receipt = self._voice_receipt(voice_request, preview, authorization)
        if (
            receipt != attempt.voice_request
            or voice_request.base_project != attempt.base_project
            or voice_request.base_registry != attempt.base_registry
            or outcome.get("request_id") != voice_request.request_id
            or outcome.get("request_fingerprint") != voice_request.voice_request_fingerprint
            or outcome.get("preview_fingerprint") != preview.preview_fingerprint
            or outcome.get("authorization_fingerprint")
            != authorization.authorization_fingerprint
            or outcome.get("provider_request_id") != cost.provider_request_id
            or outcome.get("provider_request_id") != provenance.provider_request_id
            or outcome.get("provider_trace_id") != provenance.provider_trace_id
            or outcome.get("terminal_status") != "succeeded"
            or outcome.get("alignment_receipt_sha256")
            != artifacts[paths.alignment_path.relative_to(self._project_root)].file_sha256
        ):
            raise _state_invalid("Voice candidate evidence identity is inconsistent.")
        base_snapshot = _read_regular_file_nofollow(
            self._project_root / attempt.base_registry.path,
            contained_by=self._project_root,
        )
        try:
            base_registry = AssetRegistrySnapshot.model_validate_json(base_snapshot.data)
        except (ValidationError, ValueError) as exc:
            raise _state_invalid("Voice candidate base registry is invalid.", str(exc)) from exc
        if candidate_registry.assets[: len(base_registry.assets)] != base_registry.assets:
            raise _state_invalid("Voice candidate registry mutated or deleted base assets.")
        new_records = candidate_registry.assets[len(base_registry.assets) :]
        expected_ids = set(audio_asset_ids) | set(caption_asset_ids)
        if {item.asset_id for item in new_records} != expected_ids:
            raise _state_invalid("Voice candidate registry contains extra or missing assets.")
        audio_records = tuple(
            item for item in new_records if item.asset_id in audio_asset_ids
        )
        if len(audio_records) != 1:
            raise _state_invalid("Voice candidate graph requires exactly one generated audio asset.")
        audio_record = audio_records[0]
        expected_result_fingerprint = _result_fingerprint(
            {
                "request_id": voice_request.request_id,
                "request_fingerprint": voice_request.voice_request_fingerprint,
                "audio_sha256": audio_record.sha256,
                "content_type": outcome.get("content_type"),
                "provider_request_id": outcome.get("provider_request_id"),
                "provider_trace_id": outcome.get("provider_trace_id"),
                "alignment_receipt_sha256": outcome.get(
                    "alignment_receipt_sha256"
                ),
                "cost_receipt": cost.model_dump(mode="json"),
                "provenance_receipt": provenance.model_dump(mode="json"),
                "terminal_status": outcome.get("terminal_status"),
                "preview_fingerprint": preview.preview_fingerprint,
                "authorization_fingerprint": authorization.authorization_fingerprint,
            }
        )
        metadata = audio_record.audio_metadata
        if (
            outcome.get("result_fingerprint") != expected_result_fingerprint
            or outcome.get("audio_sha256") != audio_record.sha256
            or outcome.get("content_type") != audio_record.mime_type
            or outcome.get("policy_receipt_id") != provenance.policy_receipt_id
            or outcome.get("retention_mode") != provenance.retention_mode
            or audio_record.creation_receipt_id
            != f"voice-result-{expected_result_fingerprint}"
            or audio_record.cost_receipt_id
            != f"cost-{hashlib.sha256(_canonical_json_bytes(cost)).hexdigest()}"
            or audio_record.egress.retention_mode != provenance.retention_mode
            or audio_record.egress.provider_policy_snapshot_id
            != provenance.policy_receipt_id
            or metadata is None
            or metadata.provenance_receipt_id
            != f"provenance-{hashlib.sha256(_canonical_json_bytes(provenance)).hexdigest()}"
            or metadata.alignment_receipt_id
            != f"alignment-{outcome.get('alignment_receipt_sha256')}"
        ):
            raise _state_invalid("Voice candidate result, policy, or registry identity is inconsistent.")
        caption_records = tuple(
            item for item in new_records if item.asset_id in caption_asset_ids
        )
        if len(caption_records) != len(caption_asset_ids):
            raise _state_invalid("Voice candidate caption registry identity is inconsistent.")
        expected_alignment_id = f"alignment-{outcome.get('alignment_receipt_sha256')}"
        expected_caption_receipt = f"caption-result-{expected_result_fingerprint}"
        for caption_record in caption_records:
            caption_artifact = artifacts.get(caption_record.artifact_path)
            caption_metadata = caption_record.caption_metadata
            if caption_artifact is None or caption_metadata is None:
                raise _state_invalid("Voice candidate caption artifact is missing.")
            try:
                track = CaptionTrack.model_validate_json(caption_artifact.payload)
            except (ValidationError, ValueError) as exc:
                raise _state_invalid("Voice candidate caption track is malformed.", str(exc)) from exc
            word_count = sum(len(segment.words or ()) for segment in track.segments)
            metadata_identity = (
                caption_metadata.caption_track_id,
                caption_metadata.language,
                caption_metadata.source_audio_asset_id,
                caption_metadata.source_audio_sha256,
                caption_metadata.script_hash,
                caption_metadata.transcript_hash,
                caption_metadata.segment_count,
                caption_metadata.word_count,
                caption_metadata.segmentation_policy_id,
                caption_metadata.segmentation_policy_version,
                caption_metadata.alignment_receipt_id,
                caption_metadata.timing_fingerprint,
                caption_metadata.style_reference_id,
            )
            track_identity = (
                track.caption_track_id,
                track.language,
                track.source_audio_asset_id,
                track.source_audio_sha256,
                track.script_hash,
                track.transcript_hash,
                len(track.segments),
                word_count,
                track.segmentation_policy.policy_id,
                track.segmentation_policy.policy_version,
                track.alignment_receipt_id,
                track.timing_fingerprint,
                track.style_reference_id,
            )
            if (
                caption_artifact.payload != _canonical_track_bytes(track)
                or not verify_artifact_hash(track)
                or track.timing_fingerprint != caption_timing_fingerprint(track)
                or metadata_identity != track_identity
                or track.source_audio_asset_id != audio_record.asset_id
                or track.source_audio_sha256 != audio_record.sha256
                or track.source_sample_rate_hz != metadata.sample_rate_hz
                or track.script_hash != voice_request.script_hash
                or track.transcript_hash != voice_request.script_hash
                or track.alignment_receipt_id != expected_alignment_id
                or track.alignment_receipt_id != metadata.alignment_receipt_id
                or track.creation_receipt_id != expected_caption_receipt
                or caption_record.creation_receipt_id != track.creation_receipt_id
                or caption_record.input_artifact_ids != (audio_record.asset_id,)
                or caption_record.input_fingerprint != audio_record.sha256
            ):
                raise _state_invalid("Voice candidate caption identity is inconsistent.")
            if caption_metadata.style_reference_id is None:
                if caption_metadata.style_content_hash is not None:
                    raise _state_invalid("Voice candidate caption style identity is inconsistent.")
            else:
                style_hash = caption_metadata.style_content_hash
                style_path = Path(f"assets/styles/{style_hash}.json")
                style_artifact = artifacts.get(style_path)
                if (
                    style_hash is None
                    or style_artifact is None
                    or style_artifact.file_sha256 != style_hash
                    or hashlib.sha256(style_artifact.payload).hexdigest() != style_hash
                ):
                    raise _state_invalid("Voice candidate caption style identity is inconsistent.")
        declared_paths = {item.artifact_path for item in new_records}
        declared_paths.update(
            Path(f"assets/styles/{item.caption_metadata.style_content_hash}.json")
            for item in new_records
            if item.caption_metadata is not None
            and item.caption_metadata.style_content_hash is not None
        )
        exact_paths = evidence_paths | declared_paths | {
            commit.next_project.path,
            commit.next_registry.path,
        }
        if commit.dependency_graph_transition is not None:
            graph_path = commit.dependency_graph_transition.candidate_dependency_graph.path
            if graph_path in artifacts:
                exact_paths.add(graph_path)
        if set(artifacts) != exact_paths:
            raise _state_invalid("Voice candidate graph contains extra or missing artifacts.")
        for record in new_records:
            artifact = artifacts.get(record.artifact_path)
            if (
                artifact is None
                or artifact.file_sha256 != record.sha256
                or len(artifact.payload) != record.size_bytes
            ):
                raise _state_invalid("Voice candidate registry bytes are inconsistent.")
        return outcome.get("provider_request_id")

    def generate_voice_asset(
        self,
        request: VoiceGenerationRequest,
        provider: VoiceAssetProvider,
        authorization: VoiceCallAuthorization,
        *,
        dependency_transition_preparer: VoiceDependencyTransitionPreparer | None = None,
    ) -> ProductionManifest:
        """Only public path allowed to invoke one voice provider transport call."""

        preflight_manifest = self._read_manifest()
        if (
            preflight_manifest.schema_version in {"2.3", "2.4"}
            and dependency_transition_preparer is None
        ):
            raise _state_invalid(
                "Manifest 2.3 voice generation requires a dependency transition preparer."
            )

        preview = provider.preview(request)
        self.begin_voice_generation(
            request,
            preview,
            authorization,
            dependency_transition_preparer_available=(
                dependency_transition_preparer is not None
            ),
        )
        permit = self.record_voice_submit_intent(request, preview, authorization)
        try:
            result = provider.generate(request, authorization, permit)
        except AiVideoError as exc:
            if exc.code is ErrorCode.VOICE_PROVIDER_FAILED:
                self.record_voice_failure(
                    request.attempt_id,
                    phase="provider_call",
                    error_code=exc.code.value,
                    error_message=exc.user_message,
                )
            else:
                self.record_voice_outcome_unknown(
                    request.attempt_id,
                    phase="provider_call",
                    error_code=exc.code.value,
                    error_message=exc.user_message,
                )
            raise

        except Exception as exc:
            self.record_voice_outcome_unknown(
                request.attempt_id,
                phase="provider_call",
                error_message=f"Voice transport failed after submit intent: {exc}",
            )
            raise
        self._crash_injector.checkpoint(CommitPhase.AFTER_VOICE_PROVIDER_RESULT)
        try:
            self._validate_voice_provider_result(request, preview, authorization, result)
        except Exception as exc:
            self.record_voice_outcome_unknown(
                request.attempt_id,
                phase="provider_call",
                error_message=f"Voice provider returned contradictory durable evidence: {exc}",
            )
            raise
        if self._voice_candidate_preparer is None:
            self.record_voice_outcome_unknown(
                request.attempt_id,
                phase="materialize",
                error_message="Voice result is durable only in process; candidate preparation is unavailable.",
            )
            raise _state_unsupported(
                "Voice candidate preparation requires an injected local deterministic materializer."
            )
        try:
            prepared = self._voice_candidate_preparer(
                request,
                preview,
                authorization,
                result,
                self.voice_attempt_paths(request.attempt_id),
            )
            commit_request, audio_ids, caption_ids = self._prepare_voice_activation_request(
                request, preview, authorization, result, prepared
            )
            if preflight_manifest.schema_version in {"2.3", "2.4"}:
                assert dependency_transition_preparer is not None
                prepared_request = dependency_transition_preparer(commit_request)
                if (
                    not isinstance(prepared_request, StateCommitRequest)
                    or prepared_request.attempt_id != commit_request.attempt_id
                    or prepared_request.operation != commit_request.operation
                    or prepared_request.expected_manifest_revision
                    != commit_request.expected_manifest_revision
                    or prepared_request.next_project != commit_request.next_project
                    or prepared_request.next_registry != commit_request.next_registry
                    or prepared_request.dependency_graph_transition is None
                    or not set(commit_request.artifacts).issubset(
                        prepared_request.artifacts
                    )
                ):
                    raise _state_invalid(
                        "Voice dependency transition preparer changed the owned candidate."
                    )
                commit_request = prepared_request
            return self.activate_voice_assets(
                commit_request,
                audio_asset_ids=audio_ids,
                caption_asset_ids=caption_ids,
            )
        except Exception as exc:
            current = self._read_manifest()
            active_attempt = next(
                item for item in current.attempts if item.attempt_id == request.attempt_id
            )
            if active_attempt.status is StateCommitStatus.RUNNING:
                self.record_voice_outcome_unknown(
                    request.attempt_id,
                    phase="materialize",
                    error_message=f"Voice result could not be durably activated: {exc}",
                )
            raise

    def _verify_voice_committed_candidates(self, request: StateCommitRequest) -> None:
        for artifact in request.artifacts:
            snapshot = _read_regular_file_nofollow(
                self._project_root / artifact.relative_path,
                contained_by=self._project_root,
            )
            if snapshot.file_sha256 != artifact.file_sha256:
                raise _state_commit_failed("Voice candidate artifact reopen verification failed.")
        registry_snapshot = _read_regular_file_nofollow(
            self._project_root / request.next_registry.path,
            contained_by=self._project_root,
        )
        try:
            registry = AssetRegistrySnapshot.model_validate_json(registry_snapshot.data)
        except (ValidationError, ValueError) as exc:
            raise _state_commit_failed("Voice candidate registry reopen failed.", str(exc)) from exc
        if (
            registry.revision_id != request.next_registry.revision_id
            or registry.content_hash != request.next_registry.content_hash
            or registry_semantic_sha256(registry) != registry.content_hash
            or registry_snapshot.file_sha256 != request.next_registry.file_sha256
        ):
            raise _state_commit_failed("Voice candidate registry identity is invalid.")


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
