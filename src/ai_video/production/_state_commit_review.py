from __future__ import annotations

import hashlib
from typing import Callable

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.models import (
    DependencyLifecycle,
    DependencyNodeKind,
    FinalAcceptanceReceipt,
    FinalAcceptanceReceiptPointer,
    FinalAcceptanceState,
    ProductionManifest,
    QaLayer,
    QaPolicy,
    QaPolicyPointer,
    QaVerdict,
    ReviewAttemptPhase,
    ReviewEvidence,
    ReviewEvidencePointer,
    ReviewLayerState,
    ReviewLifecycle,
    ReviewReceipt,
    ReviewReceiptPointer,
    ReviewRequest,
    ReviewRequestPointer,
    StateCommitAttempt,
    StateCommitStatus,
)
from ai_video.production.paths import (
    canonical_final_acceptance_receipt_path,
    canonical_qa_policy_path,
    canonical_review_evidence_path,
    canonical_review_receipt_path,
    canonical_review_request_path,
)
from ai_video.production.project import (
    load_qa_policy,
    load_review_receipt,
    load_review_request,
)
from ai_video.production.review import (
    adjudicate_review_evidence,
    validate_technical_review_context,
)

from ._state_commit_common import (
    _candidate_artifacts_hash,
    _canonical_json_bytes,
    _state_invalid,
    _timestamp,
)
from ._state_commit_contracts import (
    PreparedArtifact,
    _REVIEW_PERMIT_TOKEN,
    _DurableReviewAnalysisPermit,
)


class _StateCommitReviewMixin:
    def activate_qa_policy(
        self,
        policy: QaPolicy,
        *,
        expected_manifest_revision: int,
        attempt_id: str,
    ) -> ProductionManifest:
        """Select one immutable QA policy; policy drift only stales review state."""
        if not verify_artifact_hash(policy):
            raise _state_invalid("QA policy semantic content hash is invalid.")
        payload = _canonical_json_bytes(policy)
        file_sha256 = hashlib.sha256(payload).hexdigest()
        pointer = QaPolicyPointer(
            path=canonical_qa_policy_path(policy.content_hash),
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            content_hash=policy.content_hash,
            file_sha256=file_sha256,
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if manifest.manifest_revision != expected_manifest_revision:
                if (
                    manifest.schema_version in {"2.4", "2.5", "2.6"}
                    and manifest.active_qa_policy == pointer
                ):
                    return manifest
                raise _state_invalid("QA policy base Manifest revision changed.")
            if manifest.schema_version not in {"2.3", "2.4", "2.5", "2.6"}:
                raise _state_invalid("P6 requires a P5 Manifest 2.3, 2.4, or 2.5 base.")
            if manifest.active_dependency_graph is None:
                raise _state_invalid("P6 requires an active dependency graph.")
            if (
                manifest.schema_version in {"2.4", "2.5", "2.6"}
                and manifest.active_qa_policy == pointer
            ):
                return manifest
            artifact = PreparedArtifact(pointer.path, payload, file_sha256)
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            stale_states = tuple(
                item.model_copy(
                    update={
                        "lifecycle": ReviewLifecycle.STALE,
                        "active_receipt": None,
                    }
                )
                for item in manifest.review_states
            )
            final_state = manifest.final_acceptance_state
            if final_state is not None:
                final_state = final_state.model_copy(
                    update={
                        "lifecycle": ReviewLifecycle.STALE,
                        "active_receipt": None,
                    }
                )
            updated = manifest.model_copy(
                update={
                    "schema_version": (
                        "2.4" if manifest.schema_version == "2.3" else manifest.schema_version
                    ),
                    "manifest_revision": manifest.manifest_revision + 1,
                    "active_qa_policy": pointer,
                    "active_review_receipts": (),
                    "review_states": stale_states,
                    "final_acceptance_state": final_state,
                }
            )
            updated = ProductionManifest.model_validate(updated.model_dump(mode="python"))
            self._write_p6_manifest_atomic(updated)
            return self._read_manifest()


    def record_review_receipt(
        self,
        receipt: ReviewReceipt,
        evidence: tuple[ReviewEvidence, ...],
        *,
        expected_manifest_revision: int,
        attempt_id: str,
    ) -> ProductionManifest:
        """Persist and activate one exact current-layer Review Receipt."""
        if not verify_artifact_hash(receipt):
            raise _state_invalid("Review Receipt semantic content hash is invalid.")
        evidence_artifacts: list[PreparedArtifact] = []
        evidence_pointers: list[ReviewEvidencePointer] = []
        for item in evidence:
            if not verify_artifact_hash(item):
                raise _state_invalid("Review evidence semantic content hash is invalid.")
            item_payload = _canonical_json_bytes(item)
            item_hash = hashlib.sha256(item_payload).hexdigest()
            item_pointer = ReviewEvidencePointer(
                path=canonical_review_evidence_path(item.content_hash),
                evidence_id=item.evidence_id,
                layer=item.layer,
                strength=item.strength,
                content_hash=item.content_hash,
                file_sha256=item_hash,
            )
            evidence_pointers.append(item_pointer)
            evidence_artifacts.append(
                PreparedArtifact(item_pointer.path, item_payload, item_hash)
            )
        if tuple(evidence_pointers) != receipt.evidence:
            raise _state_invalid("Review Receipt does not bind the supplied evidence.")
        payload = _canonical_json_bytes(receipt)
        file_sha256 = hashlib.sha256(payload).hexdigest()
        pointer = ReviewReceiptPointer(
            path=canonical_review_receipt_path(receipt.content_hash),
            review_id=receipt.review_id,
            layer=receipt.layer,
            content_hash=receipt.content_hash,
            file_sha256=file_sha256,
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if manifest.manifest_revision != expected_manifest_revision:
                if pointer in manifest.active_review_receipts:
                    return manifest
                raise _state_invalid("Review base Manifest revision changed.")
            attempt = next(
                (
                    item
                    for item in manifest.attempts
                    if item.attempt_id == attempt_id
                ),
                None,
            )
            if (
                attempt is None
                or attempt.operation != "review"
                or attempt.status is not StateCommitStatus.RUNNING
                or attempt.review_phase is not ReviewAttemptPhase.EVIDENCE
                or attempt.review_request != receipt.review_request
            ):
                raise _state_invalid("Review Receipt requires its durable running request.")
            durable_request = load_review_request(
                self._project_root, receipt.review_request
            )
            if (
                receipt.layer not in durable_request.requested_layers
                or any(
                    identity not in durable_request.evidence_tool_identities
                    for identity in receipt.tool_identities
                )
                or durable_request.dependency_graph.revision_id
                != receipt.dependency_graph_revision_id
                or durable_request.render_state != receipt.render_state
                or durable_request.render_output_sha256
                != receipt.render_output_sha256
                or durable_request.timeline_fingerprint
                != receipt.timeline_fingerprint
                or durable_request.qa_policy != receipt.qa_policy
            ):
                raise _state_invalid("Review Receipt does not match its durable request.")
            current_render = self._current_render_state(manifest)
            bundle = self._load_production_project(self._project_root / "project.yaml")
            timeline = self._current_resolved_timeline(current_render)
            validate_technical_review_context(
                durable_request.technical_context,
                bundle,
                timeline,
                render_output_sha256=current_render.output.file_sha256,
            )
            if (
                manifest.schema_version not in {"2.4", "2.5", "2.6"}
                or bundle.manifest != manifest
                or manifest.active_qa_policy != receipt.qa_policy
                or manifest.active_dependency_graph is None
                or manifest.active_dependency_graph.revision_id
                != receipt.dependency_graph_revision_id
                or manifest.active_render_state != receipt.render_state
            ):
                raise _state_invalid("Review Receipt does not bind current Production state.")
            render_state = self._current_render_state(manifest)
            if (
                render_state.output.file_sha256 != receipt.render_output_sha256
                or render_state.timeline_fingerprint != receipt.timeline_fingerprint
            ):
                raise _state_invalid("Review Receipt output or timeline is stale.")
            for item in evidence:
                if (
                    item.layer is not receipt.layer
                    or item.render_output_sha256 != receipt.render_output_sha256
                    or item.timeline_fingerprint != receipt.timeline_fingerprint
                    or item.dependency_graph_revision_id
                    != receipt.dependency_graph_revision_id
                    or item.tool_identity not in receipt.tool_identities
                    or item.measurement_contract_version
                    != durable_request.technical_context.measurement_contract_version
                ):
                    raise _state_invalid("Review evidence identity does not match receipt.")
            policy = load_qa_policy(self._project_root, receipt.qa_policy)
            expected_verdict = adjudicate_review_evidence(
                policy, receipt.layer, evidence
            )
            if receipt.verdict is not expected_verdict:
                raise _state_invalid("Review Receipt verdict does not match durable evidence.")
            for artifact in evidence_artifacts:
                self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            artifact = PreparedArtifact(pointer.path, payload, file_sha256)
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            desired = canonical_sha256(
                {
                    "layer": receipt.layer.value,
                    "graph": receipt.dependency_graph_revision_id,
                    "render": receipt.render_state.content_hash,
                    "output": receipt.render_output_sha256,
                    "timeline": receipt.timeline_fingerprint,
                    "policy": receipt.qa_policy.content_hash,
                }
            )
            lifecycle = {
                QaVerdict.PASS: ReviewLifecycle.FRESH,
                QaVerdict.FAIL: ReviewLifecycle.FAILED,
                QaVerdict.NOT_EVALUATED: ReviewLifecycle.NOT_EVALUATED,
            }[receipt.verdict]
            state = ReviewLayerState(
                layer=receipt.layer,
                desired_fingerprint=desired,
                applied_fingerprint=desired,
                lifecycle=lifecycle,
                active_receipt=pointer,
            )
            receipts = tuple(
                item for item in manifest.active_review_receipts if item.layer != receipt.layer
            ) + (pointer,)
            states = tuple(
                item for item in manifest.review_states if item.layer != receipt.layer
            ) + (state,)
            updated = manifest.model_copy(
                update={
                    "manifest_revision": manifest.manifest_revision + 1,
                    "active_review_receipts": tuple(
                        sorted(receipts, key=lambda item: item.layer.value)
                    ),
                    "review_states": tuple(sorted(states, key=lambda item: item.layer.value)),
                    "final_acceptance_state": None,
                    "attempts": tuple(
                        item.model_copy(
                            update={
                                "status": StateCommitStatus.SUCCEEDED,
                                "review_phase": ReviewAttemptPhase.ACTIVATE,
                                "finished_at": _timestamp(),
                            }
                        )
                        if item.attempt_id == attempt_id
                        else item
                        for item in manifest.attempts
                    ),
                }
            )
            updated = ProductionManifest.model_validate(updated.model_dump(mode="python"))
            self._write_p6_manifest_atomic(updated)
            return self._read_manifest()


    def begin_review(
        self,
        request: ReviewRequest,
        *,
        attempt_id: str,
    ) -> ProductionManifest:
        """Persist the exact ReviewRequest before any analyzer invocation."""
        if not verify_artifact_hash(request):
            raise _state_invalid("ReviewRequest content hash is invalid.")
        payload = _canonical_json_bytes(request)
        file_sha256 = hashlib.sha256(payload).hexdigest()
        pointer = ReviewRequestPointer(
            path=canonical_review_request_path(request.content_hash),
            request_id=request.request_id,
            content_hash=request.content_hash,
            file_sha256=file_sha256,
        )
        artifact = PreparedArtifact(pointer.path, payload, file_sha256)
        with self._exclusive_lock():
            manifest = self._read_manifest()
            existing = next(
                (item for item in manifest.attempts if item.attempt_id == attempt_id),
                None,
            )
            if existing is not None:
                if existing.operation == "review" and existing.review_request == pointer:
                    return manifest
                raise _state_invalid("Review attempt ID was already used.")
            current_render = self._current_render_state(manifest)
            bundle = self._load_production_project(self._project_root / "project.yaml")
            timeline = self._current_resolved_timeline(current_render)
            validate_technical_review_context(
                request.technical_context,
                bundle,
                timeline,
                render_output_sha256=current_render.output.file_sha256,
            )
            if (
                manifest.schema_version not in {"2.4", "2.5", "2.6"}
                or bundle.manifest != manifest
                or manifest.manifest_revision != request.base_manifest_revision
                or manifest.active_dependency_graph != request.dependency_graph
                or self._dependency_states_hash(manifest)
                != request.dependency_states_hash
                or manifest.active_render_state != request.render_state
                or current_render.output.file_sha256 != request.render_output_sha256
                or current_render.timeline_fingerprint != request.timeline_fingerprint
                or manifest.active_qa_policy != request.qa_policy
            ):
                raise _state_invalid("ReviewRequest does not bind current Production state.")
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            running = StateCommitAttempt(
                attempt_id=attempt_id,
                operation="review",
                status=StateCommitStatus.RUNNING,
                base_manifest_revision=manifest.manifest_revision,
                base_project=manifest.active_project,
                base_registry=manifest.active_registry,
                candidate_artifacts_hash=_candidate_artifacts_hash((artifact,)),
                review_request=pointer,
                review_phase=ReviewAttemptPhase.REQUESTED,
                started_at=_timestamp(),
            )
            updated = manifest.model_copy(
                update={
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": manifest.attempts + (running,),
                }
            )
            updated = ProductionManifest.model_validate(updated.model_dump(mode="python"))
            self._write_p6_manifest_atomic(updated)
            return self._read_manifest()


    def run_review_analysis(
        self,
        *,
        review_request: ReviewRequestPointer,
        expected_manifest_revision: int,
        analyzer: Callable[[ReviewRequest, object], object],
    ) -> object:
        """Consume durable intent, mint one-use proof, then invoke evidence collection."""
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = next(
                (
                    item
                    for item in manifest.attempts
                    if item.review_request == review_request
                ),
                None,
            )
            if (
                manifest.manifest_revision != expected_manifest_revision
                or attempt is None
                or attempt.operation != "review"
                or attempt.status is not StateCommitStatus.RUNNING
                or attempt.review_phase is not ReviewAttemptPhase.REQUESTED
            ):
                raise AiVideoError(
                    ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
                    "Review analysis was already consumed or has unknown outcome; do not rerun blindly.",
                )
            request = load_review_request(self._project_root, review_request)
            consumed = attempt.model_copy(
                update={"review_phase": ReviewAttemptPhase.EVIDENCE}
            )
            updated = manifest.model_copy(
                update={
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        consumed if item.attempt_id == attempt.attempt_id else item
                        for item in manifest.attempts
                    ),
                }
            )
            updated = ProductionManifest.model_validate(updated.model_dump(mode="python"))
            self._write_p6_manifest_atomic(updated)
            permit = _DurableReviewAnalysisPermit(
                _REVIEW_PERMIT_TOKEN,
                binding={
                    "request_content_hash": request.content_hash,
                    "render_output_sha256": request.render_output_sha256,
                    "technical_context_hash": canonical_sha256(
                        request.technical_context.model_dump(mode="json")
                    ),
                },
                durability_validator=lambda: self._review_request_is_consumed(
                    review_request
                ),
            )
        return analyzer(request, permit)






    def record_final_acceptance(
        self,
        receipt: FinalAcceptanceReceipt,
        *,
        expected_manifest_revision: int,
        attempt_id: str,
    ) -> ProductionManifest:
        """Accept only the current graph, render, policy, and fresh pass receipts."""
        if not verify_artifact_hash(receipt):
            raise _state_invalid("Final Acceptance Receipt content hash is invalid.")
        payload = _canonical_json_bytes(receipt)
        file_sha256 = hashlib.sha256(payload).hexdigest()
        pointer = FinalAcceptanceReceiptPointer(
            path=canonical_final_acceptance_receipt_path(receipt.content_hash),
            acceptance_id=receipt.acceptance_id,
            content_hash=receipt.content_hash,
            file_sha256=file_sha256,
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if manifest.manifest_revision != expected_manifest_revision:
                if (
                    manifest.final_acceptance_state is not None
                    and manifest.final_acceptance_state.active_receipt == pointer
                ):
                    return manifest
                raise _state_invalid("Final acceptance base revision changed.")
            active_states = {item.layer: item for item in manifest.review_states}
            receipt_layers = {item.layer for item in receipt.required_review_receipts}
            if manifest.active_qa_policy is None or manifest.active_dependency_graph is None:
                raise AiVideoError(
                    ErrorCode.FINAL_ACCEPTANCE_INVALID,
                    "Final acceptance requires selected QA policy and dependency graph.",
                )
            policy = load_qa_policy(self._project_root, manifest.active_qa_policy)
            required_layers = {
                layer
                for layer in policy.required_layers
                if layer is not QaLayer.FINAL_ACCEPTANCE
            }
            current_render = self._current_render_state(manifest)
            graph = self._reopen_dependency_graph(manifest.active_dependency_graph)
            node_kinds = {item.node_id: item.kind for item in graph.nodes}
            render_states = tuple(
                state
                for state in manifest.dependency_states
                if node_kinds.get(state.node_id) is DependencyNodeKind.RENDER
            )
            render_nodes_fresh = all(
                state.lifecycle is DependencyLifecycle.FRESH
                for state in render_states
            )
            reopened_reviews = tuple(
                load_review_receipt(self._project_root, item)
                for item in receipt.required_review_receipts
            )
            if (
                manifest.active_dependency_graph != receipt.dependency_graph
                or manifest.active_render_state != receipt.render_state
                or manifest.active_qa_policy != receipt.qa_policy
                or receipt.dependency_states_hash
                != self._dependency_states_hash(manifest)
                or current_render.output.file_sha256 != receipt.render_output_sha256
                or current_render.timeline_fingerprint != receipt.timeline_fingerprint
                or receipt_layers != required_layers
                or set(receipt.required_review_receipts)
                != {
                    item
                    for item in manifest.active_review_receipts
                    if item.layer in required_layers
                }
                or not render_nodes_fresh
                or not render_states
                or any(item.verdict is not QaVerdict.PASS for item in reopened_reviews)
                or any(
                    item.dependency_graph_revision_id
                    != manifest.active_dependency_graph.revision_id
                    or item.render_state != manifest.active_render_state
                    or item.qa_policy != manifest.active_qa_policy
                    or item.render_output_sha256 != current_render.output.file_sha256
                    or item.timeline_fingerprint
                    != current_render.timeline_fingerprint
                    for item in reopened_reviews
                )
                or any(
                    active_states.get(layer) is None
                    or active_states[layer].lifecycle is not ReviewLifecycle.FRESH
                    for layer in receipt_layers
                )
            ):
                raise AiVideoError(
                    ErrorCode.FINAL_ACCEPTANCE_INVALID,
                    "Final acceptance requires current identities and fresh pass reviews.",
                )
            artifact = PreparedArtifact(pointer.path, payload, file_sha256)
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            desired = canonical_sha256(
                {
                    "graph": receipt.dependency_graph.content_hash,
                    "render": receipt.render_state.content_hash,
                    "output": receipt.render_output_sha256,
                    "timeline": receipt.timeline_fingerprint,
                    "policy": receipt.qa_policy.content_hash,
                    "reviews": [item.content_hash for item in receipt.required_review_receipts],
                }
            )
            updated = manifest.model_copy(
                update={
                    "manifest_revision": manifest.manifest_revision + 1,
                    "final_acceptance_state": FinalAcceptanceState(
                        desired_fingerprint=desired,
                        applied_fingerprint=desired,
                        lifecycle=ReviewLifecycle.FRESH,
                        active_receipt=pointer,
                    ),
                }
            )
            updated = ProductionManifest.model_validate(updated.model_dump(mode="python"))
            self._write_p6_manifest_atomic(updated)
            return self._read_manifest()


    def _review_request_is_consumed(self, pointer: ReviewRequestPointer) -> bool:
        try:
            manifest = self._read_manifest()
        except AiVideoError:
            return False
        return any(
            item.operation == "review"
            and item.status is StateCommitStatus.RUNNING
            and item.review_phase is ReviewAttemptPhase.EVIDENCE
            and item.review_request == pointer
            for item in manifest.attempts
        )
