from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Protocol

from ai_video.production.dependency import (
    DependencyResolution,
    ProductionDependencyInputs,
    asset_node_id,
    build_production_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
    shot_projection_node_id,
)
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    ArtifactReference,
    AssetRecord,
    AssetRegistrySnapshot,
    DependencyGraphSnapshot,
    DependencyGraphSnapshotPointer,
    DependencyLifecycle,
    DependencyNodeState,
    DependencySemanticRole,
    EgressMetadata,
    LoadedProductionProject,
    PaidProviderAttemptPhase,
    ProjectSnapshotPointer,
    ProjectDependencyEvidence,
    RegistryDependencyEvidence,
    RegistrySnapshotPointer,
    StateCommitStatus,
    TerminalFrameEvidencePointer,
    TerminalFrameExtractionReceiptPointer,
    VideoAttemptPhase,
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
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.video import ResolvedVideoGenerationRequest
from ai_video.production.video_artifact import (
    GeneratedShotContinuityReviewer,
    MeasuredVideoMetadata,
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


@dataclass(frozen=True)
class PreparedVideoCandidate:
    base_inputs: ProductionDependencyInputs
    candidate_project: LoadedProductionProject
    candidate_registry: AssetRegistrySnapshot
    candidate_inputs: ProductionDependencyInputs
    candidate_graph: DependencyGraphSnapshot
    resolution: DependencyResolution
    candidate_project_pointer: ProjectSnapshotPointer
    candidate_registry_pointer: RegistrySnapshotPointer
    candidate_graph_pointer: DependencyGraphSnapshotPointer
    candidate_shot_path: Path
    candidate_shot_bytes: bytes
    candidate_project_bytes: bytes
    candidate_registry_bytes: bytes
    candidate_graph_bytes: bytes


class VideoCandidatePreparer(Protocol):
    def __call__(
        self,
        base_project: LoadedProductionProject,
        request: ResolvedVideoGenerationRequest,
        measured: MeasuredVideoMetadata,
        probe_receipt: VideoProbeReceipt,
        provenance: VideoProvenanceReceipt,
        asset_record: AssetRecord,
        continuity_asset_record: AssetRecord | None = None,
    ) -> PreparedVideoCandidate: ...


def _prepared_artifact(path: Path, payload: bytes) -> PreparedArtifact:
    return PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest())


def _verify_prepared_candidate(candidate: PreparedVideoCandidate) -> None:
    if (
        not candidate.candidate_shot_bytes
        or not candidate.candidate_project_bytes
        or not candidate.candidate_registry_bytes
        or not candidate.candidate_graph_bytes
        or hashlib.sha256(candidate.candidate_project_bytes).hexdigest()
        != candidate.candidate_project_pointer.file_sha256
        or hashlib.sha256(candidate.candidate_registry_bytes).hexdigest()
        != candidate.candidate_registry_pointer.file_sha256
        or hashlib.sha256(candidate.candidate_graph_bytes).hexdigest()
        != candidate.candidate_graph_pointer.file_sha256
    ):
        raise _state_invalid("Video candidate prepared bytes are not exact.")


def resolve_video_activation_dependency_state(
    *,
    graph: DependencyGraphSnapshot,
    base_states: tuple[DependencyNodeState, ...],
    project_pointer: ProjectSnapshotPointer,
    registry_pointer: RegistrySnapshotPointer,
    target_shot_id: str,
    output_asset_id: str,
    continuity_asset_id: str | None = None,
) -> DependencyResolution:
    """Apply the exact generated asset and target visual in a restart-safe form."""

    desired = desired_fingerprints(graph)
    node_by_id = {item.node_id: item for item in graph.nodes}
    visual_node_id = shot_projection_node_id(
        target_shot_id, DependencySemanticRole.VISUAL.value
    )
    asset_ids = [asset_node_id(output_asset_id)]
    if continuity_asset_id is not None:
        asset_ids.append(asset_node_id(continuity_asset_id))
    if visual_node_id not in node_by_id or any(
        node_id not in node_by_id for node_id in asset_ids
    ):
        raise _state_invalid("Video activation target dependency nodes are missing.")
    seeds = [
        item
        for item in base_states
        if item.node_id not in {visual_node_id, *asset_ids}
    ]
    owned_nodes = [(visual_node_id, project_pointer, "project_snapshot")]
    owned_nodes.extend(
        (node_id, registry_pointer, "registry_snapshot")
        for node_id in asset_ids
    )
    for node_id, pointer, owner in owned_nodes:
        node = node_by_id[node_id]
        evidence = (
            ProjectDependencyEvidence(
                owner=owner,
                pointer=pointer,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node_id],
            )
            if owner == "project_snapshot"
            else RegistryDependencyEvidence(
                owner=owner,
                pointer=pointer,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node_id],
            )
        )
        seeds.append(
            DependencyNodeState(
                node_id=node_id,
                graph_revision_id=graph.revision_id,
                desired_fingerprint=desired[node_id],
                applied_fingerprint=desired[node_id],
                lifecycle=DependencyLifecycle.FRESH,
                applied_evidence=evidence,
            )
        )
    return resolve_dependency_state(
        graph,
        tuple(sorted(seeds, key=lambda item: item.node_id)),
    )


def validate_video_activation_candidate(
    *,
    base_project: LoadedProductionProject,
    request: ResolvedVideoGenerationRequest,
    asset_record: AssetRecord,
    continuity_asset_record: AssetRecord | None,
    prepared: PreparedVideoCandidate,
) -> PreparedVideoCandidate:
    scope = request.activation_scope
    if scope is None:
        raise _state_invalid("Video activation request has no durable authoring scope.")
    original = scope.request
    if (
        original.base_project != base_project.manifest.active_project
        or original.base_registry != base_project.manifest.active_registry
        or original.base_dependency_graph
        != base_project.manifest.active_dependency_graph
        or prepared.base_inputs.project != base_project
    ):
        raise _state_invalid("Video activation base identity is not exact.")
    base_shots = {item.shot_id: item for item in base_project.shots}
    next_shots = {item.shot_id: item for item in prepared.candidate_project.shots}
    base_shot = base_shots.get(original.target_shot_id)
    if (
        base_shot is None
        or base_shot.revision != original.target_shot_revision
        or base_shot.content_hash != original.target_shot_content_hash
        or set(base_shots) != set(next_shots)
    ):
        raise _state_invalid("Video activation target Shot identity is invalid.")
    roles = tuple(
        item for item in base_shot.required_asset_roles
        if item.role == original.target_asset_role
    )
    if len(roles) != 1:
        raise _state_invalid("Video activation target role is ambiguous.")
    candidate_shot = next_shots[original.target_shot_id]
    if (
        candidate_shot.revision != base_shot.revision + 1
        or candidate_shot.visual_strategy.value != original.target_visual_strategy
        or not candidate_shot.generated_video_rationale
        or tuple(
            item.asset_ids
            for item in candidate_shot.required_asset_roles
            if item.role == original.target_asset_role
        ) != ((request.output_asset_id,),)
        or any(
            next_shots[shot_id] != shot
            for shot_id, shot in base_shots.items()
            if shot_id != original.target_shot_id
        )
        or not verify_artifact_hash(candidate_shot)
    ):
        raise _state_invalid("Video candidate changed content outside its sealed scope.")

    base_assets = base_project.registry.assets
    registry = prepared.candidate_registry
    appended_assets = (
        (asset_record, continuity_asset_record)
        if continuity_asset_record is not None
        else (asset_record,)
    )
    if (
        registry.schema_version != "2.2"
        or registry.assets[: len(base_assets)] != base_assets
        or registry.assets[len(base_assets):] != appended_assets
        or registry_semantic_sha256(registry) != registry.content_hash
        or registry.revision_id != registry.content_hash
    ):
        raise _state_invalid("Video candidate Registry must append one exact asset.")
    candidate = prepared.candidate_project
    if (
        candidate.registry != registry
        or candidate.root != base_project.root
        or candidate.brief != base_project.brief
        or candidate.story != base_project.story
        or candidate.characters != base_project.characters
        or candidate.scenes != base_project.scenes
        or candidate.storyboard != base_project.storyboard
        or candidate.render_state != base_project.render_state
        or not verify_artifact_hash(candidate.project)
        or dict(candidate.asset_paths)
        != {
            **base_project.asset_paths,
            request.output_asset_id: base_project.root / asset_record.artifact_path,
            **(
                {
                    continuity_asset_record.asset_id: (
                        base_project.root / continuity_asset_record.artifact_path
                    )
                }
                if continuity_asset_record is not None
                else {}
            ),
        }
    ):
        raise _state_invalid("Video candidate changed unrelated project content.")
    refs = {
        item.artifact_id: item for item in candidate.project.artifacts.shots
    }
    candidate_ref = refs.get(candidate_shot.artifact_id)
    if (
        candidate_ref is None
        or candidate_ref
        != ArtifactReference(
            artifact_id=candidate_shot.artifact_id,
            revision=candidate_shot.revision,
            content_hash=candidate_shot.content_hash,
            path=prepared.candidate_shot_path,
        )
    ):
        raise _state_invalid("Video candidate project does not select the target Shot.")

    if (
        prepared.candidate_inputs.project != candidate
        or replace(prepared.candidate_inputs, project=base_project)
        != prepared.base_inputs
    ):
        raise _state_invalid("Video candidate changed non-project dependency inputs.")
    expected_graph = build_production_dependency_graph(prepared.candidate_inputs)
    expected_resolution = resolve_video_activation_dependency_state(
        graph=expected_graph,
        base_states=base_project.manifest.dependency_states,
        project_pointer=prepared.candidate_project_pointer,
        registry_pointer=prepared.candidate_registry_pointer,
        target_shot_id=original.target_shot_id,
        output_asset_id=request.output_asset_id,
        continuity_asset_id=(
            continuity_asset_record.asset_id
            if continuity_asset_record is not None
            else None
        ),
    )
    if (
        prepared.candidate_graph != expected_graph
        or prepared.resolution != expected_resolution
        or candidate.dependency_graph != expected_graph
        or prepared.candidate_graph_pointer.revision_id != expected_graph.revision_id
        or prepared.candidate_graph_pointer.content_hash != expected_graph.content_hash
        or candidate.manifest.active_project != prepared.candidate_project_pointer
        or candidate.manifest.active_registry != prepared.candidate_registry_pointer
        or candidate.manifest.active_dependency_graph
        != prepared.candidate_graph_pointer
    ):
        raise _state_invalid("Video candidate graph is not exact P5 output.")
    _verify_prepared_candidate(prepared)
    return prepared


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
            if request.continuity_binding is not None:
                if manifest.active_qa_policy is None:
                    raise _state_invalid(
                        "Continuity-bound video validation requires an active QA policy."
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
                        "Continuity-bound video validation requires semantic authorities."
                    )
                continuity_policy_content_hash = policy.content_hash
                continuity_authorities = policy.semantic_authorities
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
                if request.continuity_binding is not None:
                    manifest, attempt, state, probe_receipt = (
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
                            continuity_reviewer=continuity_reviewer,
                            continuity_policy_content_hash=(
                                continuity_policy_content_hash
                            ),
                            continuity_authorities=continuity_authorities,
                        )
                    )
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
                _prepared_artifact(
                    canonical_video_probe_receipt_path(probe_receipt.content_hash),
                    _canonical_json_bytes(probe_receipt),
                ),
                _prepared_artifact(
                    canonical_video_provenance_receipt_path(provenance.content_hash),
                    _canonical_json_bytes(provenance),
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
            candidate_state = state.model_copy(
                update={
                    "phase": VideoAttemptPhase.CANDIDATE,
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
