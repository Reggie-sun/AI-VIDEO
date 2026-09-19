"""Read-only next-action projection for one Ecommerce Production Job."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.ad_creative_types import (
    AdCreativePlan,
    AdCreativePlanProposal,
    CompiledAdCreativeHandoff,
)
from ai_video.production.ecommerce_ad_coordinator import (
    EcommerceStopReason,
    EcommerceVideoGenerationFacade,
    run_ecommerce_ad_generation,
)
from ai_video.production.ecommerce_job_contracts import (
    EcommerceJobBlocker,
    EcommerceJobNextAction,
    EcommerceProductionHandoff,
    EcommerceProductionJobProjection,
    EcommerceProductionJobRequest,
)
from ai_video.production.ecommerce_job_repair import (
    EcommerceShotRepairContext,
    bound_generation_attempt_ids,
    bound_generation_attempt_ids_for_shot,
    canonical_attempt_identity,
    canonical_repair_frontier,
    input_attempt_identity,
    plan_ecommerce_shot_repair,
    shot_gate_verdict,
    shots_match_handoff,
)
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    QaVerdict,
    ReviewLifecycle,
    StateCommitStatus,
)
from ai_video.production.project import load_production_project


@dataclass(frozen=True)
class EcommerceShotExecutionInput:
    shot_id: str
    attempt_id: str
    service: Any
    request: Any
    lane: Literal["local", "paid"]
    commercial_reviewer: Any
    paid_preview: Any = None
    reservation_id: str | None = None
    probe: Any = None
    terminal_frame_extractor: Any = None
    continuity_reviewer: Any = None
    pre_submit_guard: Any = None
    before_validate: Any = None
    execution_binding: Any = None
    repair_context: EcommerceShotRepairContext | None = None

    def build_facade(
        self,
        *,
        project_root: Path,
        plan_hash: str,
        projection_hash: str,
    ) -> EcommerceVideoGenerationFacade:
        service_root = getattr(self.service, "project_root", None)
        if service_root is None or Path(service_root).resolve() != project_root.resolve():
            raise ValueError("Ecommerce Shot service is bound to another Project root")
        binding = getattr(self.request, "commercial_binding", None)
        if binding is None or (
            binding.ad_creative_plan_hash != plan_hash
            or binding.commercial_execution_projection_hash != projection_hash
            or binding.target_shot_id != self.shot_id
        ):
            raise ValueError("Ecommerce Shot execution input is not exactly bound")
        if self.lane == "paid" and (
            self.paid_preview is None
            or self.reservation_id is None
            or self.paid_preview.attempt_id != self.attempt_id
            or self.paid_preview.provider_kind != self.request.provider_kind
            or self.paid_preview.model_id != self.request.model_id
        ):
            raise ValueError("Paid Ecommerce Shot execution input is not re-sealed")
        return EcommerceVideoGenerationFacade(
            service=self.service,
            attempt_id=self.attempt_id,
            request=self.request,
            lane=self.lane,
            commercial_reviewer=self.commercial_reviewer,
            paid_preview=self.paid_preview,
            reservation_id=self.reservation_id,
            probe=self.probe,
            terminal_frame_extractor=self.terminal_frame_extractor,
            continuity_reviewer=self.continuity_reviewer,
            pre_submit_guard=self.pre_submit_guard,
            before_validate=self.before_validate,
            execution_binding=self.execution_binding,
        )

    def repair_evidence_once(self) -> None:
        binding = self.request.commercial_binding
        expected = (
            self.request.resolved_generation_hash,
            binding.ad_creative_plan_hash,
            binding.commercial_execution_projection_hash,
            binding.target_shot_id,
        )
        with self.service.commercial_execution_guard(attempt_id=self.attempt_id):
            current = self.service.current_bound_commercial_request_identity(
                attempt_id=self.attempt_id
            )
            if current != expected:
                raise ValueError(
                    "Commercial evidence repair request identity is not durable"
                )
            self.service.validate_once(
                attempt_id=self.attempt_id,
                probe=self.probe,
                terminal_frame_extractor=self.terminal_frame_extractor,
                continuity_reviewer=self.continuity_reviewer,
                commercial_reviewer=self.commercial_reviewer,
                repair_commercial_evidence=True,
            )


@dataclass(frozen=True)
class EcommerceShotExecutionPlan:
    handoff: CompiledAdCreativeHandoff
    plan: AdCreativePlan
    shots: tuple[EcommerceShotExecutionInput, ...]

    def build_facades(
        self,
        runtime_handoff: EcommerceProductionHandoff,
        *,
        project_root: Path,
    ) -> dict[str, EcommerceVideoGenerationFacade]:
        proposal = AdCreativePlanProposal.model_validate(
            self.plan.model_dump(
                mode="python",
                exclude={
                    "schema_version",
                    "artifact_id",
                    "revision",
                    "content_hash",
                    "creation_receipt_id",
                    "source_provenance",
                },
            )
        )
        provenance = {
            (item.reference, item.content_hash)
            for item in self.plan.source_provenance
        }
        required_provenance = {
            (
                f"ecommerce-handoff:{runtime_handoff.handoff_id}",
                runtime_handoff.handoff_id,
            ),
            (
                "ecommerce-compile-profile:"
                f"{runtime_handoff.compile_profile.profile_id}",
                runtime_handoff.compile_profile.profile_id,
            ),
        }
        if (
            not verify_artifact_hash(self.plan)
            or proposal != runtime_handoff.ad_creative_plan_proposal
            or not required_provenance.issubset(provenance)
            or self.handoff.plan_id != self.plan.artifact_id
            or self.handoff.plan_content_hash != self.plan.content_hash
        ):
            raise ValueError("Compiled Ecommerce execution is not bound to the selected plan")
        proposed_shots = tuple(
            item.shot_id for item in runtime_handoff.artifact_proposals.shots
        )
        compiled_shots = tuple(item.shot_id for item in self.handoff.shot_proposals)
        if compiled_shots != proposed_shots:
            raise ValueError("Compiled Ecommerce Shot order does not match the Job handoff")
        projections = {
            item.target_shot_id: item
            for item in self.handoff.commercial_execution_projections
            if item.invoke_video_provider
        }
        inputs = {item.shot_id: item for item in self.shots}
        if len(inputs) != len(self.shots) or set(inputs) != set(projections):
            raise ValueError("Ecommerce Shot execution inputs do not cover exact Provider Shots")
        return {
            shot_id: inputs[shot_id].build_facade(
                project_root=project_root,
                plan_hash=self.handoff.plan_content_hash,
                projection_hash=projection.projection_hash,
            )
            for shot_id, projection in projections.items()
        }


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
        *,
        shot_execution: EcommerceShotExecutionPlan | None = None,
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
            )
        )
        if (
            active_identities != expected_identities
            or not shots_match_handoff(
                root,
                expected_shots=expected_artifacts.shots,
                active_shots=loaded.shots,
                manifest=loaded.manifest,
            )
        ):
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

        if shot_execution is not None:
            try:
                shot_execution.build_facades(
                    handoff,
                    project_root=request.project_root,
                )
                repair = canonical_repair_frontier(
                    request.project_root,
                    shot_execution,
                    loaded.manifest,
                )
            except (AiVideoError, OSError, TypeError, ValueError):
                return self._blocked(
                    request,
                    blocker_code="ECOMMERCE_SHOT_EXECUTION_INVALID",
                    stage="shot_execution",
                    subject_id=request.job_id,
                    failure_classification="EXECUTION_INPUT_INVALID",
                    required_action="Repair the exact Shot execution inputs through their owner.",
                    manifest_revision=revision,
                )
            if repair is not None:
                action, shot_id = repair
                return self._projection(
                    request,
                    next_action=action,
                    manifest_revision=revision,
                    next_shot_id=shot_id,
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

    def advance_once(
        self,
        request: EcommerceProductionJobRequest,
        handoff: EcommerceProductionHandoff,
        *,
        expected_action: EcommerceJobNextAction,
        shot_execution: EcommerceShotExecutionPlan | None = None,
    ) -> EcommerceProductionJobProjection:
        current = self.inspect(
            request,
            handoff,
            shot_execution=shot_execution,
        )
        if current.next_action is not expected_action:
            return current
        if expected_action not in {
            EcommerceJobNextAction.GENERATE_SHOT,
            EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE,
            EcommerceJobNextAction.REPAIR_SHOT_MEDIA,
        }:
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_JOB_ACTION_NOT_IMPLEMENTED",
                stage="advance",
                subject_id=request.job_id,
                failure_classification="UNSUPPORTED_ACTION",
                required_action="Invoke an implemented bounded Job action.",
                manifest_revision=current.manifest_revision,
            )
        if shot_execution is None:
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_SHOT_EXECUTION_INPUT_MISSING",
                stage="shot_execution",
                subject_id=current.next_shot_id or request.job_id,
                failure_classification="EXECUTION_INPUT_MISSING",
                required_action="Provide exact sealed inputs for the projected Shot frontier.",
                manifest_revision=current.manifest_revision,
            )

        try:
            loaded = load_production_project(request.project_root / "project.yaml")
            bound_attempt_ids = set(
                bound_generation_attempt_ids(request.project_root, shot_execution)
            )
            requested_attempt_ids = {
                item.attempt_id for item in shot_execution.shots
            }
            if (
                len(bound_attempt_ids | requested_attempt_ids)
                > request.max_new_generation_attempts
            ):
                return self._blocked(
                    request,
                    blocker_code="ECOMMERCE_JOB_GENERATION_CEILING_EXHAUSTED",
                    stage="shot_execution",
                    subject_id=current.next_shot_id or request.job_id,
                    failure_classification="ATTEMPT_CEILING",
                    required_action="Stop or authorize a new finite Job request.",
                    manifest_revision=loaded.manifest.manifest_revision,
                )
            if expected_action is EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE:
                item = next(
                    (
                        candidate
                        for candidate in shot_execution.shots
                        if candidate.shot_id == current.next_shot_id
                    ),
                    None,
                )
                if item is None or item.attempt_id not in bound_attempt_ids:
                    return self._blocked(
                        request,
                        blocker_code="ECOMMERCE_EVIDENCE_REPAIR_ATTEMPT_MISMATCH",
                        stage="shot_repair",
                        subject_id=current.next_shot_id or request.job_id,
                        failure_classification="IDENTITY_MISMATCH",
                        required_action="Resume the exact failed evidence attempt without a new submit.",
                        manifest_revision=loaded.manifest.manifest_revision,
                    )
                item.repair_evidence_once()
            if expected_action is EcommerceJobNextAction.REPAIR_SHOT_MEDIA:
                shot_id = current.next_shot_id
                item = next(
                    (
                        candidate
                        for candidate in shot_execution.shots
                        if candidate.shot_id == shot_id
                    ),
                    None,
                )
                if item is None or item.repair_context is None:
                    return self._blocked(
                        request,
                        blocker_code="ECOMMERCE_SHOT_REPAIR_DIAGNOSIS_INCOMPLETE",
                        stage="shot_repair",
                        subject_id=shot_id or request.job_id,
                        failure_classification="REPAIR_INPUT_INVALID",
                        required_action="Provide the exact diagnosed bounded repair context.",
                        manifest_revision=loaded.manifest.manifest_revision,
                    )
                context = item.repair_context
                prior = canonical_attempt_identity(
                    request.project_root,
                    context.prior_attempt.attempt_id,
                )
                proposed = input_attempt_identity(item)
                if (
                    context.shot_id != shot_id
                    or context.prior_attempt != prior
                    or context.proposed_attempt != proposed
                ):
                    return self._blocked(
                        request,
                        blocker_code="ECOMMERCE_SHOT_REPAIR_IDENTITY_MISMATCH",
                        stage="shot_repair",
                        subject_id=shot_id or request.job_id,
                        failure_classification="IDENTITY_MISMATCH",
                        required_action="Re-seal repair against canonical prior and proposed identities.",
                        manifest_revision=loaded.manifest.manifest_revision,
                    )
                shot_attempts = bound_generation_attempt_ids_for_shot(
                    request.project_root,
                    shot_execution,
                    shot_id=shot_id,
                )
                decision = plan_ecommerce_shot_repair(
                    replace(
                        context,
                        existing_job_attempts=len(bound_attempt_ids),
                        existing_shot_repairs=max(0, len(shot_attempts) - 1),
                    ),
                    max_new_generation_attempts=request.max_new_generation_attempts,
                    max_repairs_per_shot=request.max_repairs_per_shot,
                )
                if not decision.media_submit_allowed:
                    return self._blocked(
                        request,
                        blocker_code=(
                            decision.blocker_code
                            or "ECOMMERCE_SHOT_REPAIR_NOT_AUTHORIZED"
                        ),
                        stage="shot_repair",
                        subject_id=shot_id or request.job_id,
                        failure_classification="REPAIR_BLOCKED",
                        required_action="Stop or provide a valid bounded repair decision.",
                        manifest_revision=loaded.manifest.manifest_revision,
                    )
            facades = shot_execution.build_facades(
                handoff,
                project_root=request.project_root,
            )
            result = run_ecommerce_ad_generation(
                shot_execution.handoff,
                facades=facades,
            )
        except (AiVideoError, OSError, TypeError, ValueError) as exc:
            if expected_action is EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE:
                reopened = self.inspect(
                    request,
                    handoff,
                    shot_execution=shot_execution,
                )
                if (
                    reopened.next_action
                    is EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME
                ):
                    return reopened
            code = exc.code if isinstance(exc, AiVideoError) else ErrorCode.PRODUCTION_STATE_INVALID
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_SHOT_EXECUTION_INVALID",
                stage="shot_execution",
                subject_id=current.next_shot_id or request.job_id,
                failure_classification="EXECUTION_INPUT_INVALID",
                required_action="Repair the exact Shot execution inputs through their owner.",
                error_code=code,
                manifest_revision=current.manifest_revision,
            )

        revision = self._manifest_revision(request, current.manifest_revision)
        if result.complete:
            return self._projection(
                request,
                next_action=EcommerceJobNextAction.PREPARE_COMPOSITION,
                manifest_revision=revision,
            )

        shot_id = result.stopped_shot_id
        assert shot_id is not None
        status = self._attempt_status(request, shot_execution, shot_id=shot_id)
        if status is StateCommitStatus.OUTCOME_UNKNOWN:
            return self._projection(
                request,
                next_action=EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME,
                manifest_revision=revision,
                next_shot_id=shot_id,
            )
        reopened = self.inspect(
            request,
            handoff,
            shot_execution=shot_execution,
        )
        if reopened.next_action is EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME:
            return reopened
        verdict = shot_gate_verdict(
            request.project_root,
            shot_execution,
            facades,
            shot_id=shot_id,
        )
        if verdict in {QaVerdict.FAIL, QaVerdict.NOT_EVALUATED}:
            action = (
                EcommerceJobNextAction.REPAIR_SHOT_MEDIA
                if verdict is QaVerdict.FAIL
                else EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE
            )
            return self._projection(
                request,
                next_action=action,
                manifest_revision=revision,
                next_shot_id=shot_id,
            )
        if result.stop_reason is EcommerceStopReason.SHOT_NOT_PASS:
            return self._projection(
                request,
                next_action=EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE,
                manifest_revision=revision,
                next_shot_id=shot_id,
            )
        return self._blocked(
            request,
            blocker_code="ECOMMERCE_SHOT_EXECUTION_STOPPED",
            stage="shot_execution",
            subject_id=shot_id,
            failure_classification=(
                result.stop_reason.value if result.stop_reason is not None else "STOPPED"
            ),
            required_action="Inspect the canonical attempt and select its typed recovery path.",
            manifest_revision=revision,
        )

    @staticmethod
    def _manifest_revision(
        request: EcommerceProductionJobRequest,
        fallback: int | None,
    ) -> int | None:
        try:
            return load_production_project(
                request.project_root / "project.yaml"
            ).manifest.manifest_revision
        except (AiVideoError, OSError, ValueError):
            return fallback

    @staticmethod
    def _attempt_status(
        request: EcommerceProductionJobRequest,
        execution: EcommerceShotExecutionPlan,
        *,
        shot_id: str,
    ) -> StateCommitStatus | None:
        attempt_id = next(
            item.attempt_id for item in execution.shots if item.shot_id == shot_id
        )
        try:
            manifest = load_production_project(
                request.project_root / "project.yaml"
            ).manifest
        except (AiVideoError, OSError, ValueError):
            return None
        attempt = next(
            (item for item in manifest.attempts if item.attempt_id == attempt_id),
            None,
        )
        return None if attempt is None else attempt.status



__all__ = [
    "EcommerceProductionJobService",
    "EcommerceShotExecutionInput",
    "EcommerceShotExecutionPlan",
]
