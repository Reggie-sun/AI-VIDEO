"""Read-only next-action projection for one Ecommerce Production Job."""

from __future__ import annotations

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.ecommerce_job_contracts import (
    EcommerceJobBlocker,
    EcommerceJobNextAction,
    EcommerceProductionHandoff,
    EcommerceProductionJobProjection,
    EcommerceProductionJobRequest,
)
from ai_video.production.models import ReviewLifecycle, StateCommitStatus
from ai_video.production.project import load_production_project


class EcommerceProductionJobService:
    """Derive one safe next action without persisting Job-owned lifecycle."""

    @staticmethod
    def _projection(
        request: EcommerceProductionJobRequest,
        *,
        next_action: EcommerceJobNextAction,
        manifest_revision: int | None = None,
        next_shot_id: str | None = None,
        blocker: EcommerceJobBlocker | None = None,
    ) -> EcommerceProductionJobProjection:
        return EcommerceProductionJobProjection(
            schema_version="ecommerce-production-job-projection/1",
            job_id=request.job_id,
            handoff_id=request.handoff_id,
            expected_project_id=request.expected_project_id,
            next_action=next_action,
            manifest_revision=manifest_revision,
            next_shot_id=next_shot_id,
            blocker=blocker,
        )

    @classmethod
    def _blocked(
        cls,
        request: EcommerceProductionJobRequest,
        *,
        blocker_code: str,
        stage: str,
        subject_id: str,
        failure_classification: str,
        required_action: str,
        error_code: ErrorCode = ErrorCode.PRODUCTION_STATE_INVALID,
        manifest_revision: int | None = None,
        evidence_pointers: tuple[str, ...] = (),
        outcome_known: bool = True,
    ) -> EcommerceProductionJobProjection:
        return cls._projection(
            request,
            next_action=EcommerceJobNextAction.BLOCKED,
            manifest_revision=manifest_revision,
            blocker=EcommerceJobBlocker(
                blocker_code=blocker_code,
                error_code=error_code,
                stage=stage,
                subject_id=subject_id,
                failure_classification=failure_classification,
                diagnosis_id=None,
                evidence_pointers=evidence_pointers,
                retryable=False,
                required_owner="EcommerceProductionJobService",
                required_action=required_action,
                outcome_known=outcome_known,
            ),
        )

    def inspect(
        self,
        request: EcommerceProductionJobRequest,
        handoff: EcommerceProductionHandoff,
    ) -> EcommerceProductionJobProjection:
        """Strictly reopen canonical state and derive exactly one next action."""

        if request.handoff_id != handoff.handoff_id:
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_HANDOFF_IDENTITY_MISMATCH",
                stage="request",
                subject_id=request.job_id,
                failure_classification="IDENTITY_MISMATCH",
                required_action="Use the exact sealed handoff named by the Job request.",
            )
        if request.execution_policy_id != handoff.compile_profile.profile_id:
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_EXECUTION_POLICY_MISMATCH",
                stage="request",
                subject_id=request.job_id,
                failure_classification="IDENTITY_MISMATCH",
                required_action="Use the exact sealed compile profile.",
            )
        if request.delivery_profile_id != handoff.delivery_profile.profile_id:
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_DELIVERY_PROFILE_MISMATCH",
                stage="request",
                subject_id=request.job_id,
                failure_classification="IDENTITY_MISMATCH",
                required_action="Use the exact sealed delivery profile.",
            )

        root = request.project_root
        project_path = root / "project.yaml"
        manifest_path = root / "state/manifest.json"
        if not project_path.exists() and not manifest_path.exists():
            return self._projection(
                request,
                next_action=EcommerceJobNextAction.BOOTSTRAP_PROJECT,
            )
        if not project_path.is_file() or not manifest_path.is_file():
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_CANONICAL_STATE_INCOMPLETE",
                stage="reopen",
                subject_id=request.expected_project_id,
                failure_classification="PARTIAL_STATE",
                required_action="Recover or remove the partial canonical bootstrap state.",
                evidence_pointers=(
                    project_path.as_posix(),
                    manifest_path.as_posix(),
                ),
            )

        try:
            loaded = load_production_project(project_path)
        except (AiVideoError, OSError, ValueError) as exc:
            code = exc.code if isinstance(exc, AiVideoError) else ErrorCode.PRODUCTION_STATE_INVALID
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_CANONICAL_STATE_INVALID",
                stage="reopen",
                subject_id=request.expected_project_id,
                failure_classification="INVALID_CANONICAL_STATE",
                required_action="Repair canonical Production state through its existing owner.",
                error_code=code,
                evidence_pointers=(project_path.as_posix(), manifest_path.as_posix()),
            )

        revision = loaded.manifest.manifest_revision
        if (
            loaded.project.project_id != request.expected_project_id
            or loaded.manifest.project_id != request.expected_project_id
        ):
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_PROJECT_IDENTITY_MISMATCH",
                stage="reconcile",
                subject_id=request.expected_project_id,
                failure_classification="IDENTITY_MISMATCH",
                required_action="Select the intended Project root or compile a new revision.",
                manifest_revision=revision,
            )
        provenance = {
            (item.reference, item.content_hash)
            for item in loaded.project.source_provenance
        }
        required_provenance = {
            (f"ecommerce-handoff:{handoff.handoff_id}", handoff.handoff_id),
            (
                f"ecommerce-compile-profile:{handoff.compile_profile.profile_id}",
                handoff.compile_profile.profile_id,
            ),
        }
        if not required_provenance.issubset(provenance):
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_PROJECT_BINDING_MISMATCH",
                stage="reconcile",
                subject_id=loaded.project.content_hash,
                failure_classification="IDENTITY_MISMATCH",
                required_action="Reconcile through a new immutable Project revision.",
                manifest_revision=revision,
            )
        expected_artifacts = handoff.artifact_proposals
        expected_identities = tuple(
            (item.artifact_id, item.revision, item.content_hash)
            for item in (
                expected_artifacts.brief,
                expected_artifacts.story,
                *expected_artifacts.characters,
                *expected_artifacts.scenes,
                expected_artifacts.storyboard,
                *expected_artifacts.shots,
            )
        )
        active_identities = tuple(
            (item.artifact_id, item.revision, item.content_hash)
            for item in (
                loaded.brief,
                loaded.story,
                *loaded.characters,
                *loaded.scenes,
                loaded.storyboard,
                *loaded.shots,
            )
        )
        if active_identities != expected_identities:
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_PROJECT_ARTIFACT_MISMATCH",
                stage="reconcile",
                subject_id=loaded.project.content_hash,
                failure_classification="ARTIFACT_DRIFT",
                required_action="Reconcile through a new immutable Project revision.",
                manifest_revision=revision,
            )
        delivery = loaded.project.delivery_profile
        if (
            delivery.width != handoff.delivery_profile.width
            or delivery.height != handoff.delivery_profile.height
            or delivery.fps != handoff.delivery_profile.fps
            or delivery.codec_profile != handoff.delivery_profile.codec_profile
        ):
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_PROJECT_DELIVERY_MISMATCH",
                stage="reconcile",
                subject_id=loaded.project.content_hash,
                failure_classification="DELIVERY_DRIFT",
                required_action="Compile a Project revision bound to the delivery profile.",
                manifest_revision=revision,
            )

        unknown_attempts = tuple(
            item.attempt_id
            for item in loaded.manifest.attempts
            if item.status is StateCommitStatus.OUTCOME_UNKNOWN
        )
        if unknown_attempts:
            return self._projection(
                request,
                next_action=EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME,
                manifest_revision=revision,
            )

        registered = {item.asset_id: item for item in loaded.registry.assets}
        missing_assets = tuple(
            item.asset_id
            for item in handoff.asset_requirements
            if item.expected_sha256 is None
            or item.expected_size_bytes is None
            or item.asset_id not in registered
            or registered[item.asset_id].sha256 != item.expected_sha256
            or registered[item.asset_id].size_bytes != item.expected_size_bytes
        )
        if missing_assets:
            return self._projection(
                request,
                next_action=EcommerceJobNextAction.PREPARE_REFERENCES,
                manifest_revision=revision,
            )

        for shot in loaded.shots:
            if any(not role.asset_ids for role in shot.required_asset_roles):
                return self._projection(
                    request,
                    next_action=EcommerceJobNextAction.GENERATE_SHOT,
                    manifest_revision=revision,
                    next_shot_id=shot.shot_id,
                )

        if loaded.manifest.active_render_state is None:
            return self._projection(
                request,
                next_action=EcommerceJobNextAction.PREPARE_COMPOSITION,
                manifest_revision=revision,
            )
        acceptance = loaded.manifest.final_acceptance_state
        if (
            acceptance is None
            or acceptance.lifecycle is not ReviewLifecycle.FRESH
            or acceptance.active_receipt is None
        ):
            return self._projection(
                request,
                next_action=EcommerceJobNextAction.REVIEW_FINAL,
                manifest_revision=revision,
            )
        return self._projection(
            request,
            next_action=EcommerceJobNextAction.PACKAGE_DELIVERY,
            manifest_revision=revision,
        )


__all__ = ["EcommerceProductionJobService"]
