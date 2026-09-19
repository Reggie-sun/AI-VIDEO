"""Read-only next-action projection for one Ecommerce Production Job."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.ecommerce_ad_coordinator import (
    EcommerceStopReason,
    run_ecommerce_ad_generation,
)
from ai_video.production.ecommerce_job_contracts import (
    EcommerceJobNextAction,
    EcommerceProductionHandoff,
    EcommerceProductionJobProjection,
    EcommerceProductionJobRequest,
)
from ai_video.production.ecommerce_job_assembly import (
    EcommerceCompositionExecutionPlan,
    advance_ecommerce_job_assembly,
    inspect_ecommerce_job_assembly,
)
from ai_video.production.ecommerce_job_execution import (
    EcommerceShotExecutionInput,
    EcommerceShotExecutionPlan,
)
from ai_video.production.ecommerce_job_repair import (
    bound_generation_attempt_ids,
    bound_generation_attempt_ids_for_shot,
    attempt_requires_explicit_recovery,
    canonical_attempt_identity,
    canonical_repair_frontier,
    ecommerce_attempt_status,
    ecommerce_manifest_revision,
    input_attempt_identity,
    plan_ecommerce_shot_repair,
    repair_request_delta_is_verified,
    shot_gate_verdict,
    shots_match_handoff,
)
from ai_video.production.ecommerce_job_projection import (
    block_ecommerce_job,
    project_ecommerce_job,
    project_ecommerce_review_frontier,
)
from ai_video.production.ecommerce_job_review import (
    EcommerceDeliveryExecutionPlan,
    EcommercePostMediaExecutionPlan,
    inspect_ecommerce_review_frontier,
)
from ai_video.production.models import (
    QaVerdict,
    ReviewLifecycle,
    StateCommitStatus,
)
from ai_video.production.project import load_production_project


class EcommerceProductionJobService:
    """Derive one safe next action without persisting Job-owned lifecycle."""

    _projection = staticmethod(project_ecommerce_job)
    _blocked = staticmethod(block_ecommerce_job)

    def inspect(
        self,
        request: EcommerceProductionJobRequest,
        handoff: EcommerceProductionHandoff,
        *,
        shot_execution: EcommerceShotExecutionPlan | None = None,
        composition_execution: EcommerceCompositionExecutionPlan | None = None,
        review_execution: EcommercePostMediaExecutionPlan | None = None,
        delivery_execution: EcommerceDeliveryExecutionPlan | None = None,
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
            if attempt_requires_explicit_recovery(item)
            or (
                item.operation == "review"
                and item.status is StateCommitStatus.RUNNING
            )
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
                shot_execution.validate(
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

        assembly = inspect_ecommerce_job_assembly(
            composition_execution,
            handoff,
            project_root=request.project_root,
        )
        if assembly.error is not None:
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_COMPOSITION_EXECUTION_INVALID",
                stage="composition",
                subject_id=request.job_id,
                failure_classification="EXECUTION_INPUT_INVALID",
                required_action="Repair the exact composition inputs through their owner.",
                error_code=(
                    assembly.error.code
                    if isinstance(assembly.error, AiVideoError)
                    else ErrorCode.PRODUCTION_STATE_INVALID
                ),
                manifest_revision=revision,
            )
        if assembly.next_action is not EcommerceJobNextAction.REVIEW_FINAL:
            return self._projection(
                request,
                next_action=assembly.next_action,
                manifest_revision=revision,
            )
        acceptance = loaded.manifest.final_acceptance_state
        if (
            acceptance is None
            or acceptance.lifecycle is not ReviewLifecycle.FRESH
            or acceptance.active_receipt is None
        ):
            if review_execution is not None:
                try:
                    frontier = review_execution.inspect_frontier(
                        handoff,
                        project_root=request.project_root,
                    )
                except (AiVideoError, OSError, TypeError, ValueError) as exc:
                    return self._blocked(
                        request,
                        blocker_code="ECOMMERCE_FINAL_REVIEW_BINDING_INVALID",
                        stage="final_review",
                        subject_id=request.job_id,
                        failure_classification="EXECUTION_INPUT_INVALID",
                        required_action=(
                            "Repair the exact review policy, evidence, or handoff binding."
                        ),
                        error_code=(
                            exc.code
                            if isinstance(exc, AiVideoError)
                            else ErrorCode.REVIEW_EVIDENCE_INVALID
                        ),
                        manifest_revision=revision,
                    )
                return project_ecommerce_review_frontier(
                    request,
                    frontier=frontier,
                    manifest_revision=revision,
                )
            return project_ecommerce_review_frontier(
                request,
                frontier=inspect_ecommerce_review_frontier(request.project_root),
                manifest_revision=revision,
            )
        if delivery_execution is not None:
            try:
                packaged = delivery_execution.inspect(
                    handoff,
                    project_root=request.project_root,
                    job_id=request.job_id,
                )
            except (AiVideoError, OSError, TypeError, ValueError) as exc:
                return self._blocked(
                    request,
                    blocker_code="ECOMMERCE_DELIVERY_BUNDLE_INVALID",
                    stage="delivery",
                    subject_id=request.job_id,
                    failure_classification="DELIVERY_INTEGRITY",
                    required_action="Repair or remove the invalid delivery bundle.",
                    error_code=(
                        exc.code
                        if isinstance(exc, AiVideoError)
                        else ErrorCode.PRODUCTION_STATE_INVALID
                    ),
                    manifest_revision=revision,
                )
            if packaged is not None:
                return self._projection(
                    request,
                    next_action=EcommerceJobNextAction.COMPLETE,
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
        composition_execution: EcommerceCompositionExecutionPlan | None = None,
        review_execution: EcommercePostMediaExecutionPlan | None = None,
        delivery_execution: EcommerceDeliveryExecutionPlan | None = None,
    ) -> EcommerceProductionJobProjection:
        inspect_kwargs: dict[str, object] = {"shot_execution": shot_execution}
        if review_execution is not None:
            inspect_kwargs["review_execution"] = review_execution
        if delivery_execution is not None:
            inspect_kwargs["delivery_execution"] = delivery_execution
        if (
            composition_execution is not None
            and expected_action is not EcommerceJobNextAction.PREPARE_COMPOSITION
        ):
            inspect_kwargs["composition_execution"] = composition_execution
        current = self.inspect(request, handoff, **inspect_kwargs)
        if current.next_action is not expected_action:
            return current
        if expected_action in {
            EcommerceJobNextAction.PREPARE_COMPOSITION,
            EcommerceJobNextAction.RENDER_FINAL,
        }:
            if composition_execution is None:
                return self._blocked(
                    request,
                    blocker_code="ECOMMERCE_COMPOSITION_EXECUTION_INPUT_MISSING",
                    stage="composition",
                    subject_id=request.job_id,
                    failure_classification="EXECUTION_INPUT_MISSING",
                    required_action="Provide exact sealed composition and HyperFrames inputs.",
                    manifest_revision=current.manifest_revision,
                )
            assembly = advance_ecommerce_job_assembly(
                composition_execution,
                handoff,
                project_root=request.project_root,
                render=expected_action is EcommerceJobNextAction.RENDER_FINAL,
            )
            if assembly.error is not None:
                return self._blocked(
                    request,
                    blocker_code="ECOMMERCE_RENDER_EXECUTION_FAILED",
                    stage="render",
                    subject_id=request.job_id,
                    failure_classification="RENDER_FAILED",
                    required_action="Provide a new exact render attempt after diagnosis.",
                    error_code=(
                        assembly.error.code
                        if isinstance(assembly.error, AiVideoError)
                        else ErrorCode.RENDER_FAILED
                    ),
                    manifest_revision=current.manifest_revision,
                )
            return self._projection(
                request,
                next_action=assembly.next_action,
                manifest_revision=ecommerce_manifest_revision(
                    request.project_root, current.manifest_revision
                ),
            )
        if expected_action is EcommerceJobNextAction.REVIEW_FINAL:
            if review_execution is None:
                return self._blocked(
                    request,
                    blocker_code="ECOMMERCE_FINAL_REVIEW_INPUT_MISSING",
                    stage="final_review",
                    subject_id=request.job_id,
                    failure_classification="EXECUTION_INPUT_MISSING",
                    required_action="Provide exact bound whole-video review inputs.",
                    manifest_revision=current.manifest_revision,
                )
            try:
                review_execution.run(
                    handoff,
                    project_root=request.project_root,
                )
            except (AiVideoError, OSError, TypeError, ValueError) as exc:
                reopened = self.inspect(
                    request,
                    handoff,
                    shot_execution=shot_execution,
                    composition_execution=composition_execution,
                    review_execution=review_execution,
                    delivery_execution=delivery_execution,
                )
                if (
                    reopened.next_action
                    is EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME
                ):
                    return reopened
                return self._blocked(
                    request,
                    blocker_code="ECOMMERCE_FINAL_REVIEW_FAILED",
                    stage="final_review",
                    subject_id=request.job_id,
                    failure_classification="REVIEW_EXECUTION_FAILED",
                    required_action="Repair exact evidence or diagnose the failed final layer.",
                    error_code=(
                        exc.code
                        if isinstance(exc, AiVideoError)
                        else ErrorCode.REVIEW_EVIDENCE_INVALID
                    ),
                    manifest_revision=current.manifest_revision,
                )
            return self.inspect(
                request,
                handoff,
                shot_execution=shot_execution,
                composition_execution=composition_execution,
                review_execution=review_execution,
                delivery_execution=delivery_execution,
            )
        if expected_action is EcommerceJobNextAction.PACKAGE_DELIVERY:
            if delivery_execution is None:
                return self._blocked(
                    request,
                    blocker_code="ECOMMERCE_DELIVERY_INPUT_MISSING",
                    stage="delivery",
                    subject_id=request.job_id,
                    failure_classification="EXECUTION_INPUT_MISSING",
                    required_action="Provide the exact delivery destination.",
                    manifest_revision=current.manifest_revision,
                )
            try:
                delivery_execution.package(
                    handoff,
                    project_root=request.project_root,
                    job_id=request.job_id,
                )
            except (AiVideoError, OSError, TypeError, ValueError) as exc:
                return self._blocked(
                    request,
                    blocker_code="ECOMMERCE_DELIVERY_PUBLISH_FAILED",
                    stage="delivery",
                    subject_id=request.job_id,
                    failure_classification="DELIVERY_FAILED",
                    required_action="Repair the delivery destination and replay packaging.",
                    error_code=(
                        exc.code
                        if isinstance(exc, AiVideoError)
                        else ErrorCode.PRODUCTION_STATE_INVALID
                    ),
                    manifest_revision=current.manifest_revision,
                )
            return self._projection(
                request,
                next_action=EcommerceJobNextAction.COMPLETE,
                manifest_revision=current.manifest_revision,
            )
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
            with shot_execution.job_execution_guard():
                locked = self.inspect(request, handoff, **inspect_kwargs)
                if locked.next_action is not expected_action:
                    return locked
                current = locked
                try:
                    loaded = load_production_project(request.project_root / "project.yaml")
                    bound_attempt_ids = set(
                        bound_generation_attempt_ids(request.project_root, shot_execution)
                    )
                    requested_attempt_ids = {item.attempt_id for item in shot_execution.shots}
                    if len(bound_attempt_ids | requested_attempt_ids) > request.max_new_generation_attempts:
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
                                request_delta_verified=repair_request_delta_is_verified(
                                    request.project_root,
                                    prior_attempt_id=context.prior_attempt.attempt_id,
                                    proposed_request=item.request,
                                    intervention=context.intervention,
                                ),
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
                    facades = {}
                    shot_execution.validate(
                        handoff,
                        project_root=request.project_root,
                    )
                    completed_checkpoints = (
                        shot_execution.current_completed_checkpoints()
                    )

                    def facade_factory(shot_id: str):
                        facade = shot_execution.build_facade_for_shot(
                            shot_id,
                            handoff,
                            project_root=request.project_root,
                            realize_deferred=(
                                expected_action
                                is EcommerceJobNextAction.GENERATE_SHOT
                            ),
                        )
                        facades[shot_id] = facade
                        return facade

                    result = run_ecommerce_ad_generation(
                        shot_execution.handoff,
                        facade_factory=facade_factory,
                        completed_checkpoints=completed_checkpoints,
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
                            or (
                                isinstance(exc, AiVideoError)
                                and exc.code is ErrorCode.REVIEW_EVIDENCE_INVALID
                                and reopened.next_action
                                in {
                                    EcommerceJobNextAction.REPAIR_SHOT_MEDIA,
                                    EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE,
                                }
                            )
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

                revision = ecommerce_manifest_revision(
                    request.project_root, current.manifest_revision
                )
                if result.complete:
                    return self._projection(
                        request,
                        next_action=EcommerceJobNextAction.PREPARE_COMPOSITION,
                        manifest_revision=revision,
                    )

                shot_id = result.stopped_shot_id
                assert shot_id is not None
                status = ecommerce_attempt_status(
                    request.project_root, shot_execution, shot_id=shot_id
                )
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
        except AiVideoError as exc:
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_JOB_EXECUTION_BUSY",
                stage="shot_execution",
                subject_id=current.next_shot_id or request.job_id,
                failure_classification="EXECUTION_BUSY",
                required_action="Replay after the active Ecommerce Job execution finishes.",
                error_code=exc.code,
                manifest_revision=current.manifest_revision,
            )


__all__ = [
    "EcommerceProductionJobService",
    "EcommerceShotExecutionInput",
    "EcommerceShotExecutionPlan",
]
