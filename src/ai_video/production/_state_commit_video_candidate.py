from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable

from ai_video.production.models import (
    EgressMetadata,
    PaidProviderAttemptPhase,
    StateCommitStatus,
    TerminalFrameEvidencePointer,
    TerminalFrameExtractionReceiptPointer,
    VideoAttemptPhase,
    VideoProbeReceiptPointer,
    VideoProvenanceReceiptPointer,
)
from ai_video.production.paid_provider import BudgetReservationStatus
from ai_video.production.paths import (
    _open_regular_file_nofollow,
    _read_regular_file_nofollow,
    canonical_video_asset_path,
    canonical_image_asset_path,
    canonical_video_probe_receipt_path,
    canonical_video_provenance_receipt_path,
    canonical_terminal_frame_evidence_path,
    canonical_terminal_frame_extraction_receipt_path,
)
from ai_video.production.project import load_qa_policy
from ai_video.production.video_artifact import (
    GeneratedCommercialShotReviewer,
    GeneratedShotContinuityReviewer,
    TerminalFrameExtractor,
    VideoProbeReceipt,
    VideoProvenanceReceipt,
    _measure_generated_video_candidate_for_committer,
    bind_terminal_frame_evidence,
    build_generated_video_asset_record,
    build_terminal_frame_asset_record,
    extract_terminal_frame_candidate,
    probe_generated_video_candidate,
)

from ._state_commit_common import (
    _candidate_artifacts_hash,
    _canonical_json_bytes,
    _dependency_states_hash,
    _state_invalid,
    _validated_transition,
)
from ._state_commit_contracts import PreparedArtifact
from ._state_commit_video_continuity import checkpoint_generated_shot_continuity
from ._state_commit_video_commercial import (
    checkpoint_generated_commercial_shot,
    commercial_evaluation_authority,
)
from ._state_commit_video_candidate_validation import (
    PreparedVideoCandidate,
    VideoCandidatePreparer,
    resolve_video_activation_dependency_state,
    validate_video_activation_candidate,
)


def _prepared_artifact(path: Path, payload: bytes) -> PreparedArtifact:
    return PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest())


class _StateCommitVideoCandidateMixin:
    def _reopen_exact_video_artifact(
        self, artifact: PreparedArtifact
    ) -> PreparedArtifact:
        try:
            snapshot = _read_regular_file_nofollow(
                self._project_root / artifact.relative_path,
                contained_by=self._project_root,
            )
        except (OSError, ValueError) as exc:
            raise _state_invalid("Video candidate artifact could not be reopened.", str(exc)) from exc
        reopened = PreparedArtifact(
            artifact.relative_path, snapshot.data, snapshot.file_sha256
        )
        if reopened != artifact:
            raise _state_invalid("Video candidate artifact bytes changed during reopen.")
        return reopened

    def prepare_video_activation_candidate(
        self,
        *,
        attempt_id: str,
        probe: Callable[[int], dict] | None = None,
        terminal_frame_extractor: TerminalFrameExtractor | None = None,
        continuity_reviewer: GeneratedShotContinuityReviewer | None = None,
        commercial_reviewer: GeneratedCommercialShotReviewer | None = None,
    ):
        """Measure fetched bytes and persist an inactive exact bundle candidate."""

        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._video_attempt(manifest, attempt_id)
            state = attempt.video_generation_state
            paid_state = attempt.paid_provider_state
            local_lane = state is not None and state.local_fetch_receipt is not None
            if (
                attempt.status is not StateCommitStatus.RUNNING
                or state is None
                or state.phase is not VideoAttemptPhase.VALIDATE
            ):
                raise _state_invalid(
                    "Video validation requires exact durable fetched evidence."
                )
            request = self._reopen_video_request(state.request)
            continuity_policy_content_hash = None
            continuity_authorities = ()
            commercial_policy_content_hash = None
            commercial_authorities = ()
            if request.continuity_binding is not None:
                if manifest.active_qa_policy is None:
                    raise _state_invalid(
                        "Evaluated video validation requires an active QA policy."
                    )
                policy = load_qa_policy(
                    self._project_root,
                    manifest.active_qa_policy,
                )
                if (
                    policy.content_hash != manifest.active_qa_policy.content_hash
                    or not policy.semantic_authorities
                ):
                    raise _state_invalid(
                        "Evaluated video validation requires semantic authorities."
                    )
                continuity_policy_content_hash = policy.content_hash
                continuity_authorities = policy.semantic_authorities
            if request.commercial_binding is not None:
                (
                    commercial_policy_content_hash,
                    commercial_authorities,
                ) = commercial_evaluation_authority(
                    self,
                    manifest=manifest,
                    request=request,
                )
            if local_lane:
                if (
                    state.local_latest_observation is None
                    or state.local_submit_receipt is None
                    or paid_state is not None
                ):
                    raise _state_invalid("Local video evidence chain is incomplete.")
                fetch_pointer = state.local_fetch_receipt
                observation = self._reopen_local_video_status(
                    state.local_latest_observation
                )
                fetch_receipt = self._reopen_local_video_fetch(fetch_pointer)
                egress = EgressMetadata()
                cost_receipt_id = None
            else:
                if (
                    state.fetch_receipt is None
                    or state.latest_observation is None
                    or state.paid_submit_receipt is None
                    or paid_state is None
                    or paid_state.phase is not PaidProviderAttemptPhase.SETTLED
                    or manifest.active_paid_provider_budget is None
                ):
                    raise _state_invalid(
                        "Remote video validation requires exact settled evidence."
                    )
                budget = self._reopen_paid_budget(
                    manifest.active_paid_provider_budget
                )
                reservation = next(
                    (
                        item
                        for item in budget.reservations
                        if item.reservation_id == paid_state.reservation_id
                    ),
                    None,
                )
                if (
                    reservation is None
                    or reservation.status is not BudgetReservationStatus.SETTLED
                    or reservation.attempt_id != attempt_id
                    or reservation.request_fingerprint
                    != state.request.resolved_generation_hash
                    or reservation.submit_receipt_fingerprint
                    != state.paid_submit_receipt.submit_receipt_fingerprint
                    or reservation.actual_cost_microunits is None
                ):
                    raise _state_invalid(
                        "Video validation requires the exact settled budget receipt."
                    )
                fetch_pointer = state.fetch_receipt
                observation = self._reopen_video_status(state.latest_observation)
                fetch_receipt = self._reopen_video_fetch(fetch_pointer)
                gate = self._reopen_paid_gate(paid_state.gate_receipt)
                egress = EgressMetadata(
                    remote=True,
                    destination=gate.preview.destination,
                    authorization_receipt_id=(
                        gate.authorization.egress_policy_receipt_id
                    ),
                    request_fingerprint=request.resolved_generation_hash,
                    payload_fingerprint=gate.preview.preview_fingerprint,
                    retention_mode=gate.preview.retention_mode,
                    provider_policy_snapshot_id=(
                        gate.preview.provider_policy_snapshot_id
                    ),
                )
                cost_receipt_id = manifest.active_paid_provider_budget.content_hash
            terminal_frame_bytes = None
            terminal_extraction = None
            provenance = None
            commercial_evidence = None
            with _open_regular_file_nofollow(
                self._project_root / fetch_pointer.artifact_path,
                contained_by=(
                    self._project_root / "state" / "video-generation" / "fetch"
                ),
            ) as (held_fd, _):
                fetched_bytes, measured, probe_receipt = (
                    _measure_generated_video_candidate_for_committer(
                        held_fd,
                        request,
                        fetch_receipt,
                        probe=probe,
                    )
                    if request.continuity_binding is not None
                    or request.commercial_binding is not None
                    else probe_generated_video_candidate(
                        held_fd,
                        request,
                        fetch_receipt,
                        probe=probe,
                        continuity_reviewer=continuity_reviewer,
                        continuity_policy_content_hash=continuity_policy_content_hash,
                        continuity_authorities=continuity_authorities,
                    )
                )
                if request.commercial_binding is not None:
                    manifest, attempt, state, commercial_evidence = (
                        checkpoint_generated_commercial_shot(
                            self,
                            attempt_id=attempt_id,
                            manifest=manifest,
                            attempt=attempt,
                            state=state,
                            held_fd=held_fd,
                            request=request,
                            measured=measured,
                            commercial_reviewer=commercial_reviewer,
                            commercial_policy_content_hash=(
                                commercial_policy_content_hash
                            ),
                            commercial_authorities=commercial_authorities,
                        )
                    )
                if request.continuity_binding is not None:
                    manifest, attempt, state, probe_receipt, provenance = (
                        checkpoint_generated_shot_continuity(
                            self,
                            attempt_id=attempt_id,
                            manifest=manifest,
                            attempt=attempt,
                            state=state,
                            held_fd=held_fd,
                            request=request,
                            measured=measured,
                            fetch_receipt=fetch_receipt,
                            observation=observation,
                            local_lane=local_lane,
                            continuity_reviewer=continuity_reviewer,
                            continuity_policy_content_hash=(
                                continuity_policy_content_hash
                            ),
                            continuity_authorities=continuity_authorities,
                            commercial_evidence=commercial_evidence,
                        )
                    )
                elif commercial_evidence is not None:
                    probe_receipt = VideoProbeReceipt.create(
                        request=request,
                        fetch_receipt=fetch_receipt,
                        measured=measured,
                        commercial_evidence=commercial_evidence,
                    )
            if provenance is None:
                provenance = (
                    VideoProvenanceReceipt.create_local(
                        request=request,
                        observation=observation,
                        fetch_receipt=fetch_receipt,
                        probe_receipt=probe_receipt,
                    )
                    if local_lane
                    else VideoProvenanceReceipt.create(
                        request=request,
                        observation=observation,
                        fetch_receipt=fetch_receipt,
                        probe_receipt=probe_receipt,
                    )
                )
            if (
                request.activation_scope.request.seal_terminal_frame
                and state.terminal_frame_extraction is None
            ):
                with _open_regular_file_nofollow(
                    self._project_root / fetch_pointer.artifact_path,
                    contained_by=(
                        self._project_root / "state" / "video-generation" / "fetch"
                    ),
                ) as (held_fd, _):
                    terminal_frame_bytes, _, terminal_extraction = (
                        extract_terminal_frame_candidate(
                            held_fd,
                            request=request,
                            measured_video=measured,
                            source_provenance_receipt_id=provenance.content_hash,
                            extracted_asset_id=(
                                f"{request.output_asset_id}:terminal-frame"
                            ),
                            extractor=terminal_frame_extractor,
                        )
                    )
            if state.terminal_frame_extraction is not None:
                terminal_frame_bytes, terminal_extraction = (
                    self._reopen_terminal_frame_extraction(
                        state.terminal_frame_extraction
                    )
                )
            elif terminal_extraction is not None and terminal_frame_bytes is not None:
                terminal_asset_artifact = _prepared_artifact(
                    canonical_image_asset_path(terminal_extraction.extracted_sha256),
                    terminal_frame_bytes,
                )
                terminal_extraction_artifact = _prepared_artifact(
                    canonical_terminal_frame_extraction_receipt_path(
                        terminal_extraction.content_hash
                    ),
                    _canonical_json_bytes(terminal_extraction),
                )
                for artifact in (
                    terminal_asset_artifact,
                    terminal_extraction_artifact,
                ):
                    self._write_immutable_artifact(
                        artifact, attempt_id=attempt_id
                    )
                    self._reopen_exact_video_artifact(artifact)
                extraction_pointer = TerminalFrameExtractionReceiptPointer(
                    path=terminal_extraction_artifact.relative_path,
                    content_hash=terminal_extraction.content_hash,
                    extracted_asset_id=terminal_extraction.extracted_asset_id,
                    extracted_sha256=terminal_extraction.extracted_sha256,
                    file_sha256=terminal_extraction_artifact.file_sha256,
                )
                checkpoint_state = state.model_copy(
                    update={"terminal_frame_extraction": extraction_pointer}
                )
                checkpoint_attempt = _validated_transition(
                    attempt,
                    {"video_generation_state": checkpoint_state},
                )
                checkpoint_manifest = _validated_transition(
                    manifest,
                    {
                        "manifest_revision": manifest.manifest_revision + 1,
                        "attempts": tuple(
                            checkpoint_attempt
                            if item.attempt_id == attempt_id
                            else item
                            for item in manifest.attempts
                        ),
                    },
                )
                self._write_manifest_atomic(checkpoint_manifest)
                manifest = self._read_manifest()
                attempt = self._video_attempt(manifest, attempt_id)
                state = attempt.video_generation_state
                if state is None:
                    raise _state_invalid(
                        "Terminal extraction checkpoint lost video state."
                    )
            if terminal_extraction is not None and (
                terminal_extraction.source_resolved_generation_hash
                != request.resolved_generation_hash
                or terminal_extraction.source_provenance_receipt_id
                != provenance.content_hash
                or terminal_extraction.source_video_sha256
                != measured.artifact_sha256
            ):
                raise _state_invalid(
                    "Terminal extraction checkpoint does not match exact source evidence."
                )
            probe_artifact = _prepared_artifact(
                canonical_video_probe_receipt_path(probe_receipt.content_hash),
                _canonical_json_bytes(probe_receipt),
            )
            provenance_artifact = _prepared_artifact(
                canonical_video_provenance_receipt_path(provenance.content_hash),
                _canonical_json_bytes(provenance),
            )
            asset_record = build_generated_video_asset_record(
                request=request,
                measured=measured,
                probe_receipt=probe_receipt,
                provenance=provenance,
                egress=egress,
                cost_receipt_id=cost_receipt_id,
            )
            continuity_asset_record = (
                build_terminal_frame_asset_record(
                    request=request,
                    extraction=terminal_extraction,
                )
                if terminal_extraction is not None
                else None
            )
            if self._video_candidate_preparer is None:
                raise _state_invalid(
                    "Video candidate preparation requires an injected deterministic preparer."
                )
            base_project = self._load_production_project(
                self._project_root / "project.yaml"
            )
            if base_project.manifest != manifest:
                raise _state_invalid("Video activation base bundle changed.")
            prepared = self._video_candidate_preparer(
                base_project,
                request,
                measured,
                probe_receipt,
                provenance,
                asset_record,
                continuity_asset_record,
            )
            if not isinstance(prepared, PreparedVideoCandidate):
                raise _state_invalid("Video candidate preparer returned an unsafe value.")
            accepted = validate_video_activation_candidate(
                base_project=base_project,
                request=request,
                asset_record=asset_record,
                continuity_asset_record=continuity_asset_record,
                prepared=prepared,
            )
            fetched = _read_regular_file_nofollow(
                self._project_root / fetch_pointer.artifact_path,
                contained_by=(
                    self._project_root / "state" / "video-generation" / "fetch"
                ),
            )
            if (
                fetched.data != fetched_bytes
                or fetched.file_sha256 != measured.artifact_sha256
            ):
                raise _state_invalid(
                    "Fetched video path changed after held-file validation."
                )
            terminal_evidence = (
                bind_terminal_frame_evidence(
                    terminal_extraction,
                    source_registry=accepted.candidate_registry_pointer,
                )
                if terminal_extraction is not None
                else None
            )
            terminal_evidence_artifact = (
                _prepared_artifact(
                    canonical_terminal_frame_evidence_path(
                        terminal_evidence.content_hash
                    ),
                    _canonical_json_bytes(terminal_evidence),
                )
                if terminal_evidence is not None
                else None
            )
            terminal_pointer = (
                TerminalFrameEvidencePointer(
                    path=terminal_evidence_artifact.relative_path,
                    content_hash=terminal_evidence.content_hash,
                    extracted_asset_id=terminal_evidence.extracted_asset_id,
                    extracted_sha256=terminal_evidence.extracted_sha256,
                    file_sha256=terminal_evidence_artifact.file_sha256,
                )
                if terminal_evidence is not None
                and terminal_evidence_artifact is not None
                else None
            )
            artifacts = (
                _prepared_artifact(
                    canonical_video_asset_path(measured.artifact_sha256),
                    fetched_bytes,
                ),
                *(
                    ()
                    if (
                        request.continuity_binding is not None
                        and state.continuity_evaluation is not None
                        and state.continuity_evaluation.probe is not None
                    )
                    else (
                        probe_artifact,
                        provenance_artifact,
                    )
                ),
                *(
                    (
                        terminal_evidence_artifact,
                    )
                    if terminal_extraction is not None
                    and terminal_frame_bytes is not None
                    and terminal_evidence_artifact is not None
                    else ()
                ),
                _prepared_artifact(
                    accepted.candidate_shot_path, accepted.candidate_shot_bytes
                ),
                _prepared_artifact(
                    accepted.candidate_project_pointer.path,
                    accepted.candidate_project_bytes,
                ),
                _prepared_artifact(
                    accepted.candidate_registry_pointer.path,
                    accepted.candidate_registry_bytes,
                ),
                _prepared_artifact(
                    accepted.candidate_graph_pointer.path,
                    accepted.candidate_graph_bytes,
                ),
            )
            reopened = []
            for artifact in artifacts:
                self._write_immutable_artifact(
                    artifact,
                    attempt_id=attempt_id,
                    dependency_graph=(
                        artifact.relative_path
                        == accepted.candidate_graph_pointer.path
                    ),
                )
                reopened.append(self._reopen_exact_video_artifact(artifact))
            commercial_evaluation = state.commercial_evaluation
            if commercial_evaluation is not None:
                continuity_capture = state.continuity_evaluation
                probe_pointer = (
                    continuity_capture.probe
                    if continuity_capture is not None
                    and continuity_capture.probe is not None
                    else VideoProbeReceiptPointer(
                        path=probe_artifact.relative_path,
                        content_hash=probe_receipt.content_hash,
                        request_receipt_fingerprint=(
                            probe_receipt.request_receipt_fingerprint
                        ),
                        resolved_generation_hash=(
                            probe_receipt.resolved_generation_hash
                        ),
                        fetch_fingerprint=probe_receipt.fetch_fingerprint,
                        artifact_sha256=probe_receipt.measured.artifact_sha256,
                        file_sha256=probe_artifact.file_sha256,
                    )
                )
                provenance_pointer = (
                    continuity_capture.provenance
                    if continuity_capture is not None
                    and continuity_capture.provenance is not None
                    else VideoProvenanceReceiptPointer(
                        path=provenance_artifact.relative_path,
                        content_hash=provenance.content_hash,
                        request_receipt_fingerprint=(
                            provenance.request_receipt_fingerprint
                        ),
                        resolved_generation_hash=(
                            provenance.resolved_generation_hash
                        ),
                        fetch_fingerprint=provenance.fetch_fingerprint,
                        artifact_sha256=provenance.artifact_sha256,
                        probe_receipt_id=provenance.probe_receipt_id,
                        file_sha256=provenance_artifact.file_sha256,
                    )
                )
                commercial_evaluation = commercial_evaluation.model_copy(
                    update={
                        "probe": probe_pointer,
                        "provenance": provenance_pointer,
                    }
                )
            candidate_state = state.model_copy(
                update={
                    "phase": VideoAttemptPhase.CANDIDATE,
                    "commercial_evaluation": commercial_evaluation,
                    "terminal_frame_extraction": state.terminal_frame_extraction,
                    "terminal_frame_evidence": terminal_pointer,
                    "candidate_video_asset_ids": (request.output_asset_id,),
                    "candidate_continuity_asset_ids": (
                        (continuity_asset_record.asset_id,)
                        if continuity_asset_record is not None
                        else ()
                    ),
                }
            )
            candidate_attempt = _validated_transition(
                attempt,
                {
                    "candidate_project": accepted.candidate_project_pointer,
                    "candidate_registry": accepted.candidate_registry_pointer,
                    "candidate_dependency_graph": accepted.candidate_graph_pointer,
                    "candidate_dependency_states_hash": _dependency_states_hash(
                        accepted.resolution.states
                    ),
                    "candidate_artifacts_hash": _candidate_artifacts_hash(
                        tuple(reopened)
                    ),
                    "video_generation_state": candidate_state,
                },
            )
            candidate_manifest = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        candidate_attempt if item.attempt_id == attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(candidate_manifest)
            return self._read_manifest()
