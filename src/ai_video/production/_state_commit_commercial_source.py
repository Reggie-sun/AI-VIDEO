from __future__ import annotations

import hashlib
from typing import Callable, Literal

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.commercial_dependency import (
    extend_commercial_source_dependency_graph,
    resolve_commercial_source_approval_states,
    validate_commercial_source_dependency_graph,
)
from ai_video.production.commercial_source_preparation import (
    ApprovedCommercialSourceBinding,
    CommercialSourceCandidate,
    CommercialSourcePreparationRequest,
)
from ai_video.production.commercial_visual_review import (
    CommercialSourceReviewIntent,
    CommercialSourceReviewReceipt,
    CommercialVisualEvidence,
    adjudicate_commercial_visual_evidence,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.dependency import desired_fingerprints
from ai_video.production.commercial_reference import (
    validate_product_reference_set_against_registry,
)
from ai_video.production.image_import import (
    COMMERCIAL_IMAGE_IMPORT_TOOL,
    validate_commercial_image_import,
)
from ai_video.production.models import (
    CommercialSourceApprovalPointer,
    CommercialSourceAttemptState,
    CommercialSourceLifecycle,
    ProductionManifest,
    QaVerdict,
    ToolIdentity,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_commercial_source_approval_path,
    canonical_commercial_source_candidate_path,
    canonical_commercial_source_evidence_path,
    canonical_commercial_source_request_path,
    canonical_commercial_source_review_intent_path,
    canonical_commercial_source_review_path,
)

from ._state_commit_common import (
    _canonical_json_bytes,
    _outcome_unknown,
    _state_invalid,
    _validated_transition,
    prepare_dependency_graph_transition,
)
from ._state_commit_contracts import (
    PreparedArtifact,
    _COMMERCIAL_SOURCE_REVIEW_PERMIT_TOKEN,
    _DurableCommercialSourceReviewPermit,
)


class _StateCommitCommercialSourceMixin:
    def _commercial_source_base(
        self,
        manifest: ProductionManifest,
        request: CommercialSourcePreparationRequest,
    ):
        if manifest.schema_version not in {"2.12", "2.13", "2.14"}:
            raise _state_invalid("Commercial source preparation requires Manifest 2.12.")
        loaded = self._load_production_project(self._project_root / "project.yaml")
        graph = loaded.dependency_graph
        if graph is None:
            raise _state_invalid("Commercial source preparation requires active Dependency Graph.")
        if (
            loaded.manifest != manifest
            or loaded.project.content_hash != request.base_project_content_hash
            or loaded.registry.revision_id != request.base_registry_revision_id
            or loaded.registry.content_hash != request.base_registry_content_hash
            or graph.content_hash != request.base_dependency_graph_content_hash
        ):
            raise _state_invalid("Commercial source request base Project/Registry/Graph identity is stale.")
        try:
            validate_product_reference_set_against_registry(
                request.product_reference_set,
                loaded.registry,
                require_registry_identity=False,
            )
        except ValueError as exc:
            raise _state_invalid(
                "Commercial source ProductReferenceSet assets are not exact active Registry bytes.",
                str(exc),
            ) from exc
        shot = next((item for item in loaded.shots if item.shot_id == request.target_shot_id), None)
        if (
            shot is None
            or shot.revision != request.target_shot_revision
            or shot.content_hash != request.target_shot_content_hash
        ):
            raise _state_invalid("Commercial source target Shot identity is stale.")
        characters = {item.artifact_id: item for item in loaded.characters}
        scenes = {item.artifact_id: item for item in loaded.scenes}
        if any(
            (current := characters.get(reference.artifact_id)) is None
            or current.revision != reference.revision
            or current.content_hash != reference.content_hash
            for reference in request.character_references
        ) or any(
            (current := scenes.get(reference.artifact_id)) is None
            or current.revision != reference.revision
            or current.content_hash != reference.content_hash
            for reference in request.scene_references
        ):
            raise _state_invalid("Commercial source Character/Scene identity is stale.")
        return loaded

    def _write_commercial_source_artifact(self, *, attempt_id: str, path, model) -> str:
        artifact = self.prepare_artifact(attempt_id, path, _canonical_json_bytes(model))
        self._write_immutable_artifact(artifact, attempt_id=attempt_id)
        if self._ops.sha256_file(self._project_root / path) != artifact.file_sha256:
            raise _state_invalid("Commercial source artifact exact-byte reopen failed.")
        return artifact.file_sha256

    @staticmethod
    def _commercial_source_attempt(
        manifest: ProductionManifest, attempt_id: str
    ) -> CommercialSourceAttemptState | None:
        return next(
            (item for item in manifest.commercial_source_attempts if item.attempt_id == attempt_id),
            None,
        )

    @staticmethod
    def _replace_commercial_source_attempt(
        manifest: ProductionManifest, replacement: CommercialSourceAttemptState
    ) -> tuple[CommercialSourceAttemptState, ...]:
        return tuple(
            replacement if item.attempt_id == replacement.attempt_id else item
            for item in manifest.commercial_source_attempts
        )

    def _write_commercial_manifest(self, manifest: ProductionManifest) -> ProductionManifest:
        replaced = [False]
        try:
            self._write_manifest_atomic(
                manifest, on_replace=lambda: replaced.__setitem__(0, True)
            )
            reopened = self._load_production_project(self._project_root / "project.yaml")
            if reopened.manifest != manifest:
                raise _state_invalid("Commercial source Manifest did not reopen exactly.")
            return manifest
        except Exception as exc:
            if replaced[0]:
                raise _outcome_unknown(exc) from exc
            raise

    def _reopen_current_commercial_source_attempt(
        self,
        manifest: ProductionManifest,
        attempt: CommercialSourceAttemptState,
    ) -> None:
        loaded = self._load_production_project(self._project_root / "project.yaml")
        if loaded.manifest != manifest:
            raise _state_invalid(
                "Commercial source replay Manifest identity changed."
            )
        self._reopen_commercial_source_attempt(manifest, attempt)

    def begin_commercial_source_preparation(
        self, request: CommercialSourcePreparationRequest
    ) -> ProductionManifest:
        checked = CommercialSourcePreparationRequest.model_validate(
            request.model_dump(mode="python")
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            existing = self._commercial_source_attempt(manifest, checked.attempt_id)
            if existing is not None:
                if existing.request_fingerprint != checked.request_fingerprint:
                    raise _state_invalid("Commercial source attempt ID was reused with different request.")
                self._reopen_current_commercial_source_attempt(manifest, existing)
                return manifest
            self._commercial_source_base(manifest, checked)
            request_path = canonical_commercial_source_request_path(checked.request_fingerprint)
            self._write_commercial_source_artifact(
                attempt_id=checked.attempt_id, path=request_path, model=checked
            )
            attempt = CommercialSourceAttemptState(
                attempt_id=checked.attempt_id,
                request_id=checked.request_id,
                request_fingerprint=checked.request_fingerprint,
                request_path=request_path,
                target_shot_id=checked.target_shot_id,
                target_shot_content_hash=checked.target_shot_content_hash,
                product_reference_set_hash=checked.product_reference_set_hash,
                lifecycle=CommercialSourceLifecycle.REQUESTED,
            )
            updated = ProductionManifest.model_validate(
                manifest.model_copy(
                    update={
                        "manifest_revision": manifest.manifest_revision + 1,
                        "commercial_source_attempts": (*manifest.commercial_source_attempts, attempt),
                    }
                ).model_dump(mode="python")
            )
            return self._write_commercial_manifest(updated)

    def begin_commercial_source_review(
        self,
        request: CommercialSourcePreparationRequest,
        candidate: CommercialSourceCandidate,
        *,
        authority_kind: Literal["human", "calibrated_automatic", "automatic"],
        tool_identity: ToolIdentity,
    ) -> ProductionManifest:
        checked_request = CommercialSourcePreparationRequest.model_validate(
            request.model_dump(mode="python")
        )
        checked_candidate = CommercialSourceCandidate.model_validate(
            candidate.model_dump(mode="python")
        )
        checked_tool = ToolIdentity.model_validate(tool_identity.model_dump(mode="python"))
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._commercial_source_attempt(
                manifest, checked_request.attempt_id
            )
            candidate_hash = canonical_sha256(checked_candidate.model_dump(mode="json"))
            if attempt is not None and attempt.review_intent_hash is not None:
                if (
                    attempt.request_fingerprint
                    != checked_request.request_fingerprint
                ):
                    raise _state_invalid(
                        "Commercial source review replay request is not exact."
                    )
                intent, _ = self._read_commercial_model(
                    canonical_commercial_source_review_intent_path(
                        attempt.review_intent_hash
                    ),
                    CommercialSourceReviewIntent,
                )
                if (
                    attempt.candidate_record_hash != candidate_hash
                    or intent.authority_kind != authority_kind
                    or intent.tool_identity != checked_tool
                ):
                    raise _state_invalid(
                        "Commercial source review intent already binds different inputs."
                    )
                self._reopen_current_commercial_source_attempt(manifest, attempt)
                return manifest
            loaded = self._commercial_source_base(manifest, checked_request)
            if (
                loaded.qa_policy is None
                or checked_tool not in loaded.qa_policy.semantic_authorities
            ):
                raise _state_invalid(
                    "Commercial source review requires a policy-selected P6 authority."
                )
            if (
                attempt is None
                or attempt.lifecycle
                is not CommercialSourceLifecycle.MATERIALIZED_CANDIDATE
                or attempt.candidate_record_hash != candidate_hash
            ):
                raise _state_invalid(
                    "Commercial source review requires the exact durable candidate."
                )
            if self._commercial_source_review_authorizer is None:
                raise _state_invalid(
                    "Commercial source review authority is unavailable."
                )
            actor = self._commercial_source_review_authorizer(
                request_hash=checked_request.request_fingerprint,
                candidate_sha256=checked_candidate.asset_sha256,
                policy_hash=loaded.qa_policy.content_hash,
                authority_kind=authority_kind,
                tool_identity=checked_tool,
            )
            if actor is None:
                raise _state_invalid("Commercial source review was not authorized.")
            intent = CommercialSourceReviewIntent.create(
                intent_id=f"commercial-source-review-{checked_request.attempt_id}",
                source_request_hash=checked_request.request_fingerprint,
                target_shot_id=checked_request.target_shot_id,
                target_shot_content_hash=checked_request.target_shot_content_hash,
                candidate_asset_id=checked_candidate.asset_id,
                candidate_sha256=checked_candidate.asset_sha256,
                product_reference_set_hash=checked_request.product_reference_set_hash,
                policy_hash=loaded.qa_policy.content_hash,
                authority_kind=authority_kind,
                actor_identity=actor,
                tool_identity=checked_tool,
            )
            self._write_commercial_source_artifact(
                attempt_id=checked_request.attempt_id,
                path=canonical_commercial_source_review_intent_path(
                    intent.content_hash
                ),
                model=intent,
            )
            replacement = attempt.model_copy(
                update={
                    "review_intent_hash": intent.content_hash,
                    "review_phase": "requested",
                }
            )
            updated = ProductionManifest.model_validate(
                manifest.model_copy(
                    update={
                        "manifest_revision": manifest.manifest_revision + 1,
                        "commercial_source_attempts": self._replace_commercial_source_attempt(
                            manifest, replacement
                        ),
                    }
                ).model_dump(mode="python")
            )
            return self._write_commercial_manifest(updated)

    def _commercial_source_review_intent_is_consumed(
        self, *, attempt_id: str, intent_hash: str
    ) -> bool:
        manifest = self._read_manifest()
        attempt = self._commercial_source_attempt(manifest, attempt_id)
        return bool(
            attempt is not None
            and attempt.review_intent_hash == intent_hash
            and attempt.review_phase == "evidence"
        )

    def run_commercial_source_review_analysis(
        self,
        request: CommercialSourcePreparationRequest,
        candidate: CommercialSourceCandidate,
        *,
        expected_manifest_revision: int,
        analyzer: Callable[
            [CommercialSourceReviewIntent, _DurableCommercialSourceReviewPermit],
            CommercialVisualEvidence,
        ],
    ) -> tuple[ProductionManifest, CommercialSourceReviewReceipt]:
        checked_request = CommercialSourcePreparationRequest.model_validate(
            request.model_dump(mode="python")
        )
        checked_candidate = CommercialSourceCandidate.model_validate(
            candidate.model_dump(mode="python")
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._commercial_source_attempt(
                manifest, checked_request.attempt_id
            )
            if (
                attempt is not None
                and attempt.review_phase == "activate"
                and attempt.review_receipt_hash is not None
            ):
                candidate_hash = canonical_sha256(
                    checked_candidate.model_dump(mode="json")
                )
                if (
                    attempt.request_fingerprint
                    != checked_request.request_fingerprint
                    or attempt.candidate_record_hash != candidate_hash
                ):
                    raise _state_invalid(
                        "Commercial source review replay inputs are not exact."
                    )
                self._reopen_current_commercial_source_attempt(manifest, attempt)
                intent, _ = self._read_commercial_model(
                    canonical_commercial_source_review_intent_path(
                        attempt.review_intent_hash
                    ),
                    CommercialSourceReviewIntent,
                )
                receipt, _ = self._read_commercial_model(
                    canonical_commercial_source_review_path(
                        attempt.review_receipt_hash
                    ),
                    CommercialSourceReviewReceipt,
                )
                if (
                    intent.source_request_hash
                    != checked_request.request_fingerprint
                    or intent.candidate_asset_id != checked_candidate.asset_id
                    or intent.candidate_sha256 != checked_candidate.asset_sha256
                    or receipt.review_intent_hash != intent.content_hash
                    or receipt.source_request_hash
                    != checked_request.request_fingerprint
                    or receipt.candidate_asset_id != checked_candidate.asset_id
                    or receipt.candidate_sha256 != checked_candidate.asset_sha256
                ):
                    raise _state_invalid(
                        "Commercial source review replay lineage is not exact."
                    )
                return manifest, receipt
            if (
                manifest.manifest_revision != expected_manifest_revision
                or attempt is None
                or attempt.review_intent_hash is None
                or attempt.review_phase != "requested"
                or attempt.candidate_record_hash
                != canonical_sha256(checked_candidate.model_dump(mode="json"))
            ):
                raise AiVideoError(
                    ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
                    "Commercial source review analysis was already consumed or has unknown outcome; do not rerun blindly.",
                    retryable=False,
                )
            self._commercial_source_base(manifest, checked_request)
            intent, _ = self._read_commercial_model(
                canonical_commercial_source_review_intent_path(
                    attempt.review_intent_hash
                ),
                CommercialSourceReviewIntent,
            )
            consumed_attempt = attempt.model_copy(
                update={"review_phase": "evidence"}
            )
            consumed = ProductionManifest.model_validate(
                manifest.model_copy(
                    update={
                        "manifest_revision": manifest.manifest_revision + 1,
                        "commercial_source_attempts": self._replace_commercial_source_attempt(
                            manifest, consumed_attempt
                        ),
                    }
                ).model_dump(mode="python")
            )
            consumed = self._write_commercial_manifest(consumed)
            permit_binding = {
                "intent_hash": intent.content_hash,
                "request_hash": intent.source_request_hash,
                "candidate_sha256": intent.candidate_sha256,
                "policy_hash": intent.policy_hash,
            }
            permit = _DurableCommercialSourceReviewPermit(
                _COMMERCIAL_SOURCE_REVIEW_PERMIT_TOKEN,
                binding=permit_binding,
                durability_validator=lambda: self._commercial_source_review_intent_is_consumed(
                    attempt_id=checked_request.attempt_id,
                    intent_hash=intent.content_hash,
                ),
            )
        try:
            evidence = CommercialVisualEvidence.model_validate(
                analyzer(intent, permit).model_dump(mode="python")
            )
        except Exception as exc:
            raise AiVideoError(
                ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
                "Commercial source review analysis outcome is unknown; recover explicitly.",
                technical_detail=str(exc),
                retryable=False,
            ) from exc
        if not permit._was_commercial_source_review_permit_consumed():
            raise AiVideoError(
                ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
                "Commercial source review analyzer did not consume its one-use permit.",
                retryable=False,
            )
        return self._record_commercial_source_review(
            checked_request,
            checked_candidate,
            intent,
            evidence,
            expected_manifest_revision=consumed.manifest_revision,
        )

    def _record_commercial_source_review(
        self,
        checked_request: CommercialSourcePreparationRequest,
        checked_candidate: CommercialSourceCandidate,
        intent: CommercialSourceReviewIntent,
        checked_evidence: CommercialVisualEvidence,
        *,
        expected_manifest_revision: int,
    ) -> tuple[ProductionManifest, CommercialSourceReviewReceipt]:
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._commercial_source_attempt(
                manifest, checked_request.attempt_id
            )
            candidate_hash = canonical_sha256(
                checked_candidate.model_dump(mode="json")
            )
            loaded = self._commercial_source_base(manifest, checked_request)
            if loaded.qa_policy is None:
                raise _state_invalid(
                    "Commercial source review requires the active P6 QA policy."
                )
            checked_receipt = adjudicate_commercial_visual_evidence(
                checked_evidence,
                policy=loaded.qa_policy,
            )
            if (
                manifest.manifest_revision != expected_manifest_revision
                or attempt is None
                or attempt.review_intent_hash != intent.content_hash
                or attempt.review_phase != "evidence"
                or attempt.candidate_record_hash != candidate_hash
                or checked_evidence.review_intent_hash != intent.content_hash
                or checked_evidence.source_request_hash
                != checked_request.request_fingerprint
                or checked_evidence.target_shot_id != checked_request.target_shot_id
                or checked_evidence.target_shot_content_hash
                != checked_request.target_shot_content_hash
                or checked_evidence.candidate_asset_id != checked_candidate.asset_id
                or checked_evidence.candidate_sha256 != checked_candidate.asset_sha256
                or checked_evidence.product_reference_set_hash
                != checked_request.product_reference_set_hash
                or checked_evidence.policy_hash != intent.policy_hash
                or checked_evidence.authority_kind != intent.authority_kind
                or checked_evidence.observed_by != intent.actor_identity
                or checked_evidence.tool_identity != intent.tool_identity
                or checked_receipt.review_intent_hash != intent.content_hash
                or checked_receipt.source_request_hash
                != checked_request.request_fingerprint
                or checked_receipt.candidate_asset_id != checked_candidate.asset_id
                or checked_receipt.candidate_sha256
                != checked_candidate.asset_sha256
                or checked_receipt.product_reference_set_hash
                != checked_request.product_reference_set_hash
                or checked_receipt.observed_by != intent.actor_identity
                or checked_receipt.content_hash
                != canonical_sha256(
                    checked_receipt.model_dump(
                        mode="json", exclude={"receipt_id", "content_hash"}
                    )
                )
            ):
                raise _state_invalid("Commercial source review lineage is inconsistent.")
            self._write_commercial_source_artifact(
                attempt_id=checked_request.attempt_id,
                path=canonical_commercial_source_evidence_path(checked_evidence.content_hash),
                model=checked_evidence,
            )
            self._write_commercial_source_artifact(
                attempt_id=checked_request.attempt_id,
                path=canonical_commercial_source_review_path(checked_receipt.content_hash),
                model=checked_receipt,
            )
            lifecycle = (
                CommercialSourceLifecycle.EVIDENCED
                if checked_receipt.verdict is QaVerdict.PASS
                else CommercialSourceLifecycle.REJECTED
                if checked_receipt.verdict is QaVerdict.FAIL
                else CommercialSourceLifecycle.NOT_EVALUATED
            )
            replacement = attempt.model_copy(
                update={
                    "lifecycle": lifecycle,
                    "review_phase": "activate",
                    "review_evidence_hash": checked_evidence.content_hash,
                    "review_receipt_hash": checked_receipt.content_hash,
                }
            )
            updated = ProductionManifest.model_validate(
                manifest.model_copy(
                    update={
                        "manifest_revision": manifest.manifest_revision + 1,
                        "commercial_source_attempts": self._replace_commercial_source_attempt(
                            manifest, replacement
                        ),
                    }
                ).model_dump(mode="python")
            )
            return self._write_commercial_manifest(updated), checked_receipt

    def approve_commercial_source(
        self,
        request: CommercialSourcePreparationRequest,
        binding: ApprovedCommercialSourceBinding,
    ) -> ProductionManifest:
        checked_request = CommercialSourcePreparationRequest.model_validate(
            request.model_dump(mode="python")
        )
        checked_binding = ApprovedCommercialSourceBinding.model_validate(
            binding.model_dump(mode="python")
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._commercial_source_attempt(
                manifest, checked_request.attempt_id
            )
            existing = next(
                (
                    item
                    for item in manifest.active_commercial_source_approvals
                    if item.target_shot_id == checked_binding.target_shot_id
                ),
                None,
            )
            if (
                attempt is not None
                and attempt.lifecycle is CommercialSourceLifecycle.APPROVED
                and attempt.active_approval == existing
                and existing is not None
                and existing.content_hash == checked_binding.content_hash
            ):
                if (
                    attempt.request_fingerprint
                    != checked_request.request_fingerprint
                    or checked_binding.source_request_hash
                    != checked_request.request_fingerprint
                ):
                    raise _state_invalid(
                        "Commercial source approval replay request is not exact."
                    )
                self._reopen_current_commercial_source_attempt(manifest, attempt)
                if manifest.active_dependency_graph is None:
                    raise _state_invalid("Commercial source approval graph is missing.")
                graph = self._reopen_dependency_graph(
                    manifest.active_dependency_graph
                )
                try:
                    validate_commercial_source_dependency_graph(
                        graph,
                        product_reference_set=checked_binding.product_reference_set,
                        keyframe_asset_id=checked_binding.keyframe_asset_id,
                        keyframe_sha256=checked_binding.keyframe_sha256,
                    )
                except ValueError as exc:
                    raise _state_invalid(
                        "Commercial source approval dependency graph is stale.",
                        str(exc),
                    ) from exc
                return manifest
            loaded = self._commercial_source_base(manifest, checked_request)
            if (
                attempt is None
                or attempt.lifecycle is not CommercialSourceLifecycle.EVIDENCED
                or attempt.review_receipt_hash != checked_binding.review_receipt_hash
                or checked_binding.source_request_hash
                != checked_request.request_fingerprint
                or checked_binding.target_shot_id != checked_request.target_shot_id
                or checked_binding.target_shot_content_hash
                != checked_request.target_shot_content_hash
                or checked_binding.product_reference_set_hash
                != checked_request.product_reference_set_hash
                or checked_binding.product_reference_set
                != checked_request.product_reference_set
                or checked_binding.product_source_asset_hashes
                != checked_request.product_reference_asset_hashes
                or checked_binding.character_references
                != checked_request.character_references
                or checked_binding.scene_references
                != checked_request.scene_references
            ):
                raise _state_invalid("Commercial source approval is not current and exact.")
            if existing is not None:
                if existing.content_hash == checked_binding.content_hash:
                    self._reopen_current_commercial_source_attempt(manifest, attempt)
                    return manifest
                raise _state_invalid("Commercial source Shot already selects another approval.")
            path = canonical_commercial_source_approval_path(
                checked_binding.content_hash
            )
            file_hash = self._write_commercial_source_artifact(
                attempt_id=checked_request.attempt_id,
                path=path,
                model=checked_binding,
            )
            pointer = CommercialSourceApprovalPointer(
                path=path,
                approval_id=checked_binding.approval_id,
                target_shot_id=checked_binding.target_shot_id,
                content_hash=checked_binding.content_hash,
                file_sha256=file_hash,
            )
            replacement = attempt.model_copy(
                update={
                    "lifecycle": CommercialSourceLifecycle.APPROVED,
                    "active_approval": pointer,
                }
            )
            commercial_attempts = self._replace_commercial_source_attempt(
                manifest, replacement
            )
            approvals = tuple(
                sorted(
                    (*manifest.active_commercial_source_approvals, pointer),
                    key=lambda item: item.target_shot_id,
                )
            )
            try:
                candidate_graph = extend_commercial_source_dependency_graph(
                    loaded.dependency_graph,
                    product_reference_set=checked_binding.product_reference_set,
                    keyframe_asset_id=checked_binding.keyframe_asset_id,
                    keyframe_sha256=checked_binding.keyframe_sha256,
                )
                candidate_states = resolve_commercial_source_approval_states(
                    candidate_graph,
                    manifest.dependency_states,
                    approval=pointer,
                    product_reference_set=checked_binding.product_reference_set,
                    keyframe_asset_id=checked_binding.keyframe_asset_id,
                )
                transition = prepare_dependency_graph_transition(
                    expected_manifest_revision=manifest.manifest_revision,
                    base_dependency_graph=manifest.active_dependency_graph,
                    candidate_graph=candidate_graph,
                    candidate_dependency_states=candidate_states,
                    expected_desired_fingerprints=desired_fingerprints(
                        candidate_graph
                    ),
                )
                self._verify_dependency_candidate(
                    manifest,
                    candidate_graph,
                    transition.candidate_dependency_states,
                    commercial_source_attempts=commercial_attempts,
                    active_commercial_source_approvals=approvals,
                )
            except (AiVideoError, ValueError) as exc:
                detail = (
                    exc.technical_detail if isinstance(exc, AiVideoError) else str(exc)
                )
                raise _state_invalid(
                    "Commercial source approval dependency transition is invalid.",
                    detail,
                ) from exc
            graph_payload = _canonical_json_bytes(candidate_graph)
            graph_artifact = PreparedArtifact(
                transition.candidate_dependency_graph.path,
                graph_payload,
                hashlib.sha256(graph_payload).hexdigest(),
            )
            self._write_immutable_artifact(
                graph_artifact,
                attempt_id=checked_request.attempt_id,
                dependency_graph=True,
            )
            self._reopen_dependency_graph(transition.candidate_dependency_graph)
            updated = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "commercial_source_attempts": commercial_attempts,
                    "active_commercial_source_approvals": approvals,
                    "active_dependency_graph": transition.candidate_dependency_graph,
                    "dependency_states": transition.candidate_dependency_states,
                },
            )
            assert isinstance(updated, ProductionManifest)
            return self._write_commercial_manifest(updated)

    def record_commercial_source_candidate(
        self,
        request: CommercialSourcePreparationRequest,
        candidate: CommercialSourceCandidate,
    ) -> ProductionManifest:
        checked_request = CommercialSourcePreparationRequest.model_validate(
            request.model_dump(mode="python")
        )
        checked_candidate = CommercialSourceCandidate.model_validate(
            candidate.model_dump(mode="python")
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._commercial_source_attempt(manifest, checked_request.attempt_id)
            candidate_hash = canonical_sha256(checked_candidate.model_dump(mode="json"))
            if (
                attempt is not None
                and attempt.request_fingerprint
                == checked_request.request_fingerprint
                and attempt.candidate_asset_id == checked_candidate.asset_id
                and attempt.candidate_sha256 == checked_candidate.asset_sha256
                and attempt.candidate_record_hash == candidate_hash
            ):
                self._reopen_current_commercial_source_attempt(manifest, attempt)
                return manifest
            loaded = self._commercial_source_base(manifest, checked_request)
            if attempt is None or attempt.request_fingerprint != checked_request.request_fingerprint:
                raise _state_invalid("Commercial source request must be recorded first.")
            if (
                checked_candidate.request_hash != checked_request.request_fingerprint
                or checked_candidate.target_shot_id != checked_request.target_shot_id
                or checked_candidate.target_shot_content_hash != checked_request.target_shot_content_hash
            ):
                raise _state_invalid("Commercial source candidate lineage is inconsistent.")
            asset = next(
                (item for item in loaded.registry.assets if item.asset_id == checked_candidate.asset_id),
                None,
            )
            if asset is None or asset.sha256 != checked_candidate.asset_sha256:
                raise _state_invalid("Commercial source candidate is unregistered or has wrong bytes.")
            receipt = checked_candidate.import_receipt
            if (
                receipt.target_id != checked_request.request_id
                or receipt.product_reference_set_id
                != checked_request.product_reference_set_id
                or receipt.product_reference_set_hash
                != checked_request.product_reference_set_hash
                or receipt.product_reference_asset_hashes
                != checked_request.product_reference_asset_hashes
                or receipt.character_reference_ids
                != checked_request.character_reference_ids
                or receipt.scene_reference_ids != checked_request.scene_reference_ids
                or receipt.product_reference_set
                != checked_request.product_reference_set
                or asset.creation_receipt_id != receipt.content_hash
                or asset.tool != COMMERCIAL_IMAGE_IMPORT_TOOL
            ):
                raise _state_invalid(
                    "Commercial source import receipt lineage is inconsistent."
                )
            try:
                image_bytes = _read_regular_file_nofollow(
                    loaded.asset_paths[asset.asset_id],
                    contained_by=loaded.root / "assets",
                ).data
                validate_commercial_image_import(receipt, image_bytes)
            except (KeyError, OSError, ValueError, AiVideoError) as exc:
                raise _state_invalid(
                    "Commercial source import receipt does not match registered PNG bytes.",
                    str(exc),
                ) from exc
            if attempt.lifecycle is not CommercialSourceLifecycle.REQUESTED:
                if (
                    attempt.candidate_asset_id == checked_candidate.asset_id
                    and attempt.candidate_sha256 == checked_candidate.asset_sha256
                    and attempt.candidate_record_hash == candidate_hash
                ):
                    self._reopen_current_commercial_source_attempt(manifest, attempt)
                    return manifest
                raise _state_invalid("Commercial source attempt already selected a different candidate.")
            self._write_commercial_source_artifact(
                attempt_id=checked_request.attempt_id,
                path=canonical_commercial_source_candidate_path(candidate_hash),
                model=checked_candidate,
            )
            replacement = attempt.model_copy(
                update={
                    "lifecycle": CommercialSourceLifecycle.MATERIALIZED_CANDIDATE,
                    "candidate_asset_id": checked_candidate.asset_id,
                    "candidate_sha256": checked_candidate.asset_sha256,
                    "candidate_record_hash": candidate_hash,
                }
            )
            updated = ProductionManifest.model_validate(
                manifest.model_copy(
                    update={
                        "manifest_revision": manifest.manifest_revision + 1,
                        "commercial_source_attempts": self._replace_commercial_source_attempt(
                            manifest, replacement
                        ),
                    }
                ).model_dump(mode="python")
            )
            return self._write_commercial_manifest(updated)
