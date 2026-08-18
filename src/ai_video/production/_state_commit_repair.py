from __future__ import annotations

import hashlib

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.models import (
    ApprovedRepairReceipt,
    ApprovedRepairReceiptPointer,
    DependencyLifecycle,
    DependencyNodeKind,
    ProductionManifest,
    RepairOutcomeReceipt,
    RepairOutcomeReceiptPointer,
    RepairRequest,
    ReviewLifecycle,
    StateCommitStatus,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_approved_repair_receipt_path,
    canonical_repair_outcome_receipt_path,
    canonical_repair_request_path,
)
from ai_video.production.project import load_qa_policy

from ._state_commit_common import _canonical_json_bytes, _state_invalid
from ._state_commit_contracts import PreparedArtifact


class _StateCommitRepairMixin:
    def record_approved_repair_receipt(
        self,
        request: RepairRequest,
        receipt: ApprovedRepairReceipt,
        *,
        expected_manifest_revision: int,
        attempt_id: str,
    ) -> ProductionManifest:
        """Persist authorization before any Production creative mutation."""
        if not verify_artifact_hash(request) or not verify_artifact_hash(receipt):
            raise _state_invalid("Approved Repair Receipt content hash is invalid.")
        compared_fields = (
            "repair_id",
            "base_manifest_revision",
            "dependency_graph",
            "dependency_states_hash",
            "render_state",
            "render_output_sha256",
            "timeline_fingerprint",
            "qa_policy",
            "review_receipt_ids",
            "issue_ids",
            "evidence_ids",
            "root_cause_hypothesis",
            "selected_repair_action",
            "exact_target_artifact_ids",
            "exact_target_node_ids",
            "expected_invalidation_node_ids",
            "actor",
            "authorization",
            "before_fingerprints",
        )
        if receipt.request_content_hash != request.content_hash or any(
            getattr(receipt, field) != getattr(request, field)
            for field in compared_fields
        ):
            raise _state_invalid("Approved Repair Receipt does not exactly copy its request.")
        expected_scope_fingerprint = canonical_sha256(
            {
                "repair_id": request.repair_id,
                "actor": request.actor.model_dump(mode="json"),
                "action": request.selected_repair_action.model_dump(mode="json"),
                "target_artifact_ids": list(request.exact_target_artifact_ids),
                "target_node_ids": list(request.exact_target_node_ids),
                "expected_invalidation_node_ids": list(
                    request.expected_invalidation_node_ids
                ),
            }
        )
        if request.authorization.scope_fingerprint != expected_scope_fingerprint:
            raise AiVideoError(
                ErrorCode.REPAIR_AUTHORIZATION_REQUIRED,
                "Repair authorization scope fingerprint is invalid.",
            )
        request_payload = _canonical_json_bytes(request)
        request_artifact = PreparedArtifact(
            canonical_repair_request_path(request.content_hash),
            request_payload,
            hashlib.sha256(request_payload).hexdigest(),
        )
        payload = _canonical_json_bytes(receipt)
        file_sha256 = hashlib.sha256(payload).hexdigest()
        pointer = ApprovedRepairReceiptPointer(
            path=canonical_approved_repair_receipt_path(receipt.content_hash),
            repair_id=receipt.repair_id,
            content_hash=receipt.content_hash,
            file_sha256=file_sha256,
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if manifest.manifest_revision != expected_manifest_revision:
                if manifest.active_approved_repair == pointer:
                    return manifest
                raise _state_invalid("Repair authorization base revision changed.")
            if (
                manifest.schema_version not in {"2.4", "2.5", "2.6", "2.7"}
                or manifest.active_qa_policy is None
            ):
                raise AiVideoError(
                    ErrorCode.REPAIR_AUTHORIZATION_REQUIRED,
                    "Repair approval requires the current selected QA policy.",
                )
            policy = load_qa_policy(self._project_root, manifest.active_qa_policy)
            authorized_by = (
                self._repair_authorizer(request)
                if self._repair_authorizer is not None
                else None
            )
            if (
                authorized_by is None
                or authorized_by not in policy.repair_authorities
                or receipt.authorization.authorized_by != authorized_by
            ):
                raise AiVideoError(
                    ErrorCode.REPAIR_AUTHORIZATION_REQUIRED,
                    "Repair approval requires a policy-selected trusted authorizer.",
                )
            if (
                manifest.active_dependency_graph != receipt.dependency_graph
                or manifest.active_render_state != receipt.render_state
                or manifest.active_qa_policy != receipt.qa_policy
                or receipt.base_manifest_revision != manifest.manifest_revision
                or receipt.dependency_states_hash
                != self._dependency_states_hash(manifest)
                or tuple(item.review_id for item in manifest.active_review_receipts)
                != receipt.review_receipt_ids
            ):
                raise AiVideoError(
                    ErrorCode.REPAIR_AUTHORIZATION_REQUIRED,
                    "Approved Repair Receipt does not bind current Production state.",
                )
            current_render = self._current_render_state(manifest)
            if (
                current_render.output.file_sha256 != receipt.render_output_sha256
                or current_render.timeline_fingerprint != receipt.timeline_fingerprint
            ):
                raise AiVideoError(
                    ErrorCode.REPAIR_AUTHORIZATION_REQUIRED,
                    "Approved Repair Receipt output or timeline is stale.",
                )
            graph = self._reopen_dependency_graph(receipt.dependency_graph)
            node_ids = {item.node_id for item in graph.nodes}
            targets = set(receipt.exact_target_node_ids)
            if not targets or not targets.issubset(node_ids):
                raise AiVideoError(
                    ErrorCode.REPAIR_SCOPE_INVALID,
                    "Repair target nodes are not in the current dependency graph.",
                )
            outgoing: dict[str, set[str]] = {}
            for edge in graph.edges:
                outgoing.setdefault(edge.source_node_id, set()).add(edge.target_node_id)
            allowed = set(targets)
            frontier = list(targets)
            while frontier:
                for target in outgoing.get(frontier.pop(), ()):
                    if target not in allowed:
                        allowed.add(target)
                        frontier.append(target)
            expected = set(receipt.expected_invalidation_node_ids)
            if expected != allowed:
                raise AiVideoError(
                    ErrorCode.REPAIR_SCOPE_INVALID,
                    "Repair expected invalidation must equal the exact graph closure.",
                )
            self._write_immutable_artifact(request_artifact, attempt_id=attempt_id)
            artifact = PreparedArtifact(pointer.path, payload, file_sha256)
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            updated = manifest.model_copy(
                update={
                    "manifest_revision": manifest.manifest_revision + 1,
                    "active_approved_repair": pointer,
                    "final_acceptance_state": None,
                }
            )
            updated = ProductionManifest.model_validate(updated.model_dump(mode="python"))
            self._write_p6_manifest_atomic(updated)
            return self._read_manifest()

    def record_repair_outcome(
        self,
        receipt: RepairOutcomeReceipt,
        *,
        expected_manifest_revision: int,
        attempt_id: str,
    ) -> ProductionManifest:
        """Close one approved repair only after its rerender and fresh reviews."""
        if not verify_artifact_hash(receipt):
            raise _state_invalid("Repair Outcome Receipt content hash is invalid.")
        payload = _canonical_json_bytes(receipt)
        file_sha256 = hashlib.sha256(payload).hexdigest()
        pointer = RepairOutcomeReceiptPointer(
            path=canonical_repair_outcome_receipt_path(receipt.content_hash),
            repair_id=receipt.repair_id,
            content_hash=receipt.content_hash,
            file_sha256=file_sha256,
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if manifest.manifest_revision != expected_manifest_revision:
                if pointer in manifest.repair_outcome_receipts:
                    return manifest
                raise _state_invalid("Repair outcome base revision changed.")
            current_render = self._current_render_state(manifest)
            state_by_layer = {item.layer: item for item in manifest.review_states}
            approved_snapshot = _read_regular_file_nofollow(
                self._project_root / receipt.approved_receipt.path,
                contained_by=self._project_root / "state",
            )
            try:
                approved = ApprovedRepairReceipt.model_validate_json(
                    approved_snapshot.data
                )
            except (ValidationError, ValueError) as exc:
                raise _state_invalid(
                    "Repair outcome approval could not be reopened.", str(exc)
                ) from exc
            if (
                approved_snapshot.file_sha256
                != receipt.approved_receipt.file_sha256
                or approved.content_hash != receipt.approved_receipt.content_hash
                or not verify_artifact_hash(approved)
            ):
                raise _state_invalid("Repair outcome approval identity is invalid.")
            approval_fields_match = all(
                getattr(receipt, field) == getattr(approved, field)
                for field in (
                    "repair_id",
                    "review_receipt_ids",
                    "issue_ids",
                    "evidence_ids",
                    "root_cause_hypothesis",
                    "selected_repair_action",
                    "exact_target_artifact_ids",
                    "exact_target_node_ids",
                    "expected_invalidation_node_ids",
                    "actor",
                    "authorization",
                    "before_fingerprints",
                )
            )
            repair_index = next(
                (index
                for index, item in enumerate(manifest.attempts)
                if item.operation == "repair"
                and item.status is StateCommitStatus.SUCCEEDED
                and item.approved_repair_receipt == receipt.approved_receipt),
                None,
            )
            if repair_index is None:
                raise AiVideoError(
                    ErrorCode.REPAIR_SCOPE_INVALID,
                    "Repair outcome has no succeeded repair attempt.",
                )
            rerender_recorded = any(
                item.operation == "render_state"
                and item.status is StateCommitStatus.SUCCEEDED
                and item.candidate_render_state == receipt.rerender_state
                for item in manifest.attempts[repair_index + 1 :]
            )
            if manifest.active_dependency_graph is None:
                raise _state_invalid("Repair outcome requires active graph.")
            graph = self._reopen_dependency_graph(manifest.active_dependency_graph)
            node_kinds = {item.node_id: item.kind for item in graph.nodes}
            render_states = tuple(
                item
                for item in manifest.dependency_states
                if node_kinds.get(item.node_id) is DependencyNodeKind.RENDER
            )
            if (
                not any(
                    item.operation == "repair"
                    and item.status is StateCommitStatus.SUCCEEDED
                    and item.approved_repair_receipt == receipt.approved_receipt
                    for item in manifest.attempts
                )
                or receipt.rerender_state == approved.render_state
                or not rerender_recorded
                or not render_states
                or any(
                    item.lifecycle is not DependencyLifecycle.FRESH
                    for item in render_states
                )
                or manifest.active_render_state != receipt.rerender_state
                or current_render.output.file_sha256 != receipt.rerender_output_sha256
                or current_render.timeline_fingerprint
                != receipt.rerender_timeline_fingerprint
                or not approval_fields_match
                or receipt.actual_invalidation_node_ids
                != approved.expected_invalidation_node_ids
                or not set(receipt.fresh_review_receipts).issubset(
                    set(manifest.active_review_receipts)
                )
                or any(
                    state_by_layer.get(item.layer) is None
                    or state_by_layer[item.layer].lifecycle
                    is not ReviewLifecycle.FRESH
                    for item in receipt.fresh_review_receipts
                )
            ):
                raise AiVideoError(
                    ErrorCode.REPAIR_SCOPE_INVALID,
                    "Repair outcome does not match authorization, rerender, and fresh review state.",
                )
            artifact = PreparedArtifact(pointer.path, payload, file_sha256)
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            updated = manifest.model_copy(
                update={
                    "manifest_revision": manifest.manifest_revision + 1,
                    "active_approved_repair": None,
                    "repair_outcome_receipts": manifest.repair_outcome_receipts
                    + (pointer,),
                }
            )
            updated = ProductionManifest.model_validate(updated.model_dump(mode="python"))
            self._write_p6_manifest_atomic(updated)
            return self._read_manifest()
