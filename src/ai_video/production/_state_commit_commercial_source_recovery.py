from __future__ import annotations

from pydantic import ValidationError

from ai_video.production.commercial_source_preparation import (
    ApprovedCommercialSourceBinding,
    CommercialSourceCandidate,
    CommercialSourcePreparationRequest,
)
from ai_video.production.commercial_visual_review import (
    CommercialSourceReviewIntent,
    CommercialSourceReviewReceipt,
    CommercialVisualEvidence,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    CommercialSourceAttemptState,
    CommercialSourceLifecycle,
    ProductionManifest,
    RecoveryDisposition,
    RecoveryItem,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_commercial_source_approval_path,
    canonical_commercial_source_candidate_path,
    canonical_commercial_source_evidence_path,
    canonical_commercial_source_review_intent_path,
    canonical_commercial_source_review_path,
)

from ._state_commit_common import _state_invalid


class _StateCommitCommercialSourceRecoveryMixin:
    def _read_commercial_model(self, path, model_type):
        try:
            snapshot = _read_regular_file_nofollow(
                self._project_root / path,
                contained_by=self._project_root / "state/commercial-source",
            )
            model = model_type.model_validate_json(snapshot.data)
        except (OSError, ValueError, ValidationError) as exc:
            raise _state_invalid(
                "Commercial source durable evidence could not be reopened.", str(exc)
            ) from exc
        return model, snapshot.file_sha256

    def _reopen_commercial_source_attempt(
        self,
        manifest: ProductionManifest,
        attempt: CommercialSourceAttemptState,
    ) -> tuple[CommercialSourceAttemptState, tuple[RecoveryItem, ...]]:
        request, request_file_hash = self._read_commercial_model(
            attempt.request_path, CommercialSourcePreparationRequest
        )
        if (
            request.attempt_id != attempt.attempt_id
            or request.request_id != attempt.request_id
            or request.request_fingerprint != attempt.request_fingerprint
            or request.target_shot_id != attempt.target_shot_id
            or request.target_shot_content_hash != attempt.target_shot_content_hash
            or request.product_reference_set_hash != attempt.product_reference_set_hash
        ):
            raise _state_invalid("Commercial source request evidence is inconsistent.")
        items = [
            RecoveryItem(
                path=attempt.request_path,
                disposition=RecoveryDisposition.ACTIVE,
                sha256=request_file_hash,
            )
        ]
        if attempt.candidate_record_hash is not None:
            candidate_path = canonical_commercial_source_candidate_path(
                attempt.candidate_record_hash
            )
            candidate, candidate_file_hash = self._read_commercial_model(
                candidate_path, CommercialSourceCandidate
            )
            if (
                canonical_sha256(candidate.model_dump(mode="json"))
                != attempt.candidate_record_hash
                or candidate.request_hash != attempt.request_fingerprint
                or candidate.target_shot_id != attempt.target_shot_id
                or candidate.target_shot_content_hash != attempt.target_shot_content_hash
                or candidate.asset_id != attempt.candidate_asset_id
                or candidate.asset_sha256 != attempt.candidate_sha256
            ):
                raise _state_invalid("Commercial source candidate evidence is inconsistent.")
            items.append(
                RecoveryItem(
                    path=candidate_path,
                    disposition=RecoveryDisposition.ACTIVE,
                    sha256=candidate_file_hash,
                )
            )
        intent: CommercialSourceReviewIntent | None = None
        if attempt.review_intent_hash is not None:
            intent_path = canonical_commercial_source_review_intent_path(
                attempt.review_intent_hash
            )
            intent, intent_file_hash = self._read_commercial_model(
                intent_path, CommercialSourceReviewIntent
            )
            if (
                intent.content_hash != attempt.review_intent_hash
                or intent.source_request_hash != attempt.request_fingerprint
                or intent.target_shot_id != attempt.target_shot_id
                or intent.target_shot_content_hash
                != attempt.target_shot_content_hash
                or intent.candidate_asset_id != attempt.candidate_asset_id
                or intent.candidate_sha256 != attempt.candidate_sha256
            ):
                raise _state_invalid(
                    "Commercial source review intent is inconsistent."
                )
            items.append(
                RecoveryItem(
                    path=intent_path,
                    disposition=RecoveryDisposition.ACTIVE,
                    sha256=intent_file_hash,
                )
            )
        if attempt.review_evidence_hash is not None:
            evidence_path = canonical_commercial_source_evidence_path(
                attempt.review_evidence_hash
            )
            evidence, evidence_file_hash = self._read_commercial_model(
                evidence_path, CommercialVisualEvidence
            )
            if (
                evidence.content_hash != attempt.review_evidence_hash
                or intent is None
                or evidence.review_intent_hash != intent.content_hash
                or evidence.observed_by != intent.actor_identity
                or evidence.tool_identity != intent.tool_identity
            ):
                raise _state_invalid("Commercial source review evidence hash is inconsistent.")
            items.append(
                RecoveryItem(
                    path=evidence_path,
                    disposition=RecoveryDisposition.ACTIVE,
                    sha256=evidence_file_hash,
                )
            )
        if attempt.review_receipt_hash is not None:
            review_path = canonical_commercial_source_review_path(
                attempt.review_receipt_hash
            )
            receipt, review_file_hash = self._read_commercial_model(
                review_path, CommercialSourceReviewReceipt
            )
            if receipt.content_hash != attempt.review_receipt_hash:
                raise _state_invalid("Commercial source review receipt hash is inconsistent.")
            items.append(
                RecoveryItem(
                    path=review_path,
                    disposition=RecoveryDisposition.ACTIVE,
                    sha256=review_file_hash,
                )
            )
        if attempt.active_approval is not None:
            pointer = attempt.active_approval
            if pointer.path != canonical_commercial_source_approval_path(pointer.content_hash):
                raise _state_invalid("Commercial source approval path is not canonical.")
            approval, approval_file_hash = self._read_commercial_model(
                pointer.path, ApprovedCommercialSourceBinding
            )
            if (
                approval.content_hash != pointer.content_hash
                or approval.approval_id != pointer.approval_id
                or approval.target_shot_id != pointer.target_shot_id
                or approval_file_hash != pointer.file_sha256
            ):
                raise _state_invalid("Commercial source approval pointer is inconsistent.")
            items.append(
                RecoveryItem(
                    path=pointer.path,
                    disposition=RecoveryDisposition.ACTIVE,
                    sha256=approval_file_hash,
                )
            )
        if (
            attempt.lifecycle is CommercialSourceLifecycle.APPROVED
            and attempt.active_approval not in manifest.active_commercial_source_approvals
        ):
            raise _state_invalid("Commercial source approved attempt is not actively selected.")
        return attempt, tuple(items)

    def recover_commercial_source_attempt(
        self, attempt_id: str
    ) -> CommercialSourceAttemptState:
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if manifest.schema_version != "2.12":
                raise _state_invalid("Commercial source recovery requires Manifest 2.12.")
            attempt = next(
                (
                    item
                    for item in manifest.commercial_source_attempts
                    if item.attempt_id == attempt_id
                ),
                None,
            )
            if attempt is None:
                raise _state_invalid("Commercial source recovery attempt is absent.")
            try:
                loaded = self._load_production_project(
                    self._project_root / "project.yaml"
                )
            except Exception as exc:
                detail = getattr(exc, "technical_detail", None) or str(exc)
                raise _state_invalid(
                    "Commercial source recovery could not reopen current Production state.",
                    detail,
                ) from exc
            if loaded.manifest != manifest:
                raise _state_invalid(
                    "Commercial source recovery Manifest identity changed."
                )
            reopened, _ = self._reopen_commercial_source_attempt(manifest, attempt)
            return reopened

    def _active_commercial_source_recovery_items(
        self, manifest: ProductionManifest
    ) -> tuple[RecoveryItem, ...]:
        if manifest.schema_version != "2.12":
            return ()
        items: list[RecoveryItem] = []
        for attempt in manifest.commercial_source_attempts:
            _, attempt_items = self._reopen_commercial_source_attempt(manifest, attempt)
            items.extend(attempt_items)
        return tuple(items)
