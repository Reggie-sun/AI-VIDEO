"""Exact per-Shot execution inputs for the Ecommerce Production Job."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from ai_video.production.ad_creative_types import AdCreativePlan, CompiledAdCreativeHandoff
from ai_video.production.ecommerce_ad_coordinator import (
    ActivatedCommercialShotCheckpoint,
    EcommerceVideoGenerationFacade,
)
from ai_video.production.ecommerce_job_assembly import validate_ecommerce_plan_binding
from ai_video.production.ecommerce_job_contracts import EcommerceProductionHandoff
from ai_video.production.ecommerce_job_repair import (
    EcommerceShotRepairContext,
    bound_generation_attempt_ids_for_shot,
)
from ai_video.production.models import StateCommitStatus, VideoAttemptPhase
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
    input_factory: Callable[[str], EcommerceShotExecutionInput] | None = None

    def job_execution_guard(self):
        """Serialize the Job-owned ceiling check through its Shot side effect."""

        if not self.shots:
            raise ValueError("Ecommerce Shot execution plan has no Provider Shots")
        return self.shots[0].service.commercial_execution_guard(
            attempt_id=f"ecommerce-job-ceiling:{self.handoff.plan_content_hash}"
        )

    def validate(
        self,
        runtime_handoff: EcommerceProductionHandoff,
        *,
        project_root: Path,
    ) -> None:
        validate_ecommerce_plan_binding(runtime_handoff, self.handoff, self.plan)
        proposed_shots = tuple(
            item.shot_id for item in runtime_handoff.artifact_proposals.shots
        )
        compiled_shots = tuple(item.shot_id for item in self.handoff.shot_proposals)
        if compiled_shots != proposed_shots:
            raise ValueError("Compiled Ecommerce Shot order does not match the Job handoff")
        provider_shot_ids = tuple(
            item.target_shot_id
            for item in self.handoff.commercial_execution_projections
            if item.invoke_video_provider
        )
        inputs = {item.shot_id: item for item in self.shots}
        if len(inputs) != len(self.shots) or set(inputs) != set(provider_shot_ids):
            raise ValueError("Ecommerce Shot execution inputs do not cover exact Provider Shots")
        if len(provider_shot_ids) > 1 and self.input_factory is None:
            raise ValueError("Multiple Provider Shots require deferred execution inputs")
        for item in self.shots:
            service_root = getattr(item.service, "project_root", None)
            if service_root is None or Path(service_root).resolve() != project_root.resolve():
                raise ValueError("Ecommerce Shot service is bound to another Project root")

    def build_facade_for_shot(
        self,
        shot_id: str,
        runtime_handoff: EcommerceProductionHandoff,
        *,
        project_root: Path,
        realize_deferred: bool = True,
    ) -> EcommerceVideoGenerationFacade:
        self.validate(runtime_handoff, project_root=project_root)
        declared = next((item for item in self.shots if item.shot_id == shot_id), None)
        if declared is None:
            raise ValueError("Ecommerce Shot is not declared by the execution plan")
        selected = (
            self.input_factory(shot_id)
            if realize_deferred and self.input_factory
            else declared
        )
        if selected.shot_id != shot_id or selected.attempt_id != declared.attempt_id:
            raise ValueError("Deferred Ecommerce Shot input changed declared identity")
        projection = next(
            item
            for item in self.handoff.commercial_execution_projections
            if item.invoke_video_provider and item.target_shot_id == shot_id
        )
        return selected.build_facade(
            project_root=project_root,
            plan_hash=self.handoff.plan_content_hash,
            projection_hash=projection.projection_hash,
        )

    def current_completed_checkpoints(
        self,
    ) -> dict[str, ActivatedCommercialShotCheckpoint]:
        """Read canonical activations without realizing deferred execution inputs."""

        from ai_video.production._video_project_reader import (
            load_video_request_receipt,
        )

        loaded = load_production_project(
            Path(self.shots[0].service.project_root) / "project.yaml"
        )
        checkpoints = {}
        for item in self.shots:
            active_shot = next(
                (shot for shot in loaded.shots if shot.shot_id == item.shot_id),
                None,
            )
            attempt_ids = bound_generation_attempt_ids_for_shot(
                loaded.root, self, shot_id=item.shot_id
            )
            for attempt_id in reversed(attempt_ids):
                attempt = next(
                    stored for stored in loaded.manifest.attempts
                    if stored.attempt_id == attempt_id
                )
                state = attempt.video_generation_state
                if (
                    attempt.status is not StateCommitStatus.SUCCEEDED
                    or state is None
                    or state.phase is not VideoAttemptPhase.ACTIVATE
                ):
                    continue
                request = load_video_request_receipt(loaded.root, state.request)
                scope = request.activation_scope
                if active_shot is None or scope is None or not any(
                    role.role == scope.request.target_asset_role
                    and role.asset_ids == (request.output_asset_id,)
                    for role in active_shot.required_asset_roles
                ):
                    continue
                checkpoint = item.service.current_activated_commercial_checkpoint(
                    attempt_id=attempt_id
                )
                if checkpoint is None:
                    raise ValueError("Canonical active Shot has no activation checkpoint")
                checkpoints[item.shot_id] = checkpoint
                break
            if not attempt_ids and item.service.current_bound_commercial_request_identity(
                attempt_id=item.attempt_id
            ) is not None:
                checkpoint = item.service.current_activated_commercial_checkpoint(
                    attempt_id=item.attempt_id
                )
                if checkpoint is not None:
                    checkpoints[item.shot_id] = checkpoint
        return checkpoints

    def build_facades(
        self,
        runtime_handoff: EcommerceProductionHandoff,
        *,
        project_root: Path,
    ) -> dict[str, EcommerceVideoGenerationFacade]:
        self.validate(runtime_handoff, project_root=project_root)
        return {
            item.shot_id: self.build_facade_for_shot(
                item.shot_id,
                runtime_handoff,
                project_root=project_root,
            )
            for item in self.shots
        }


__all__ = [
    "EcommerceShotExecutionInput",
    "EcommerceShotExecutionPlan",
]
