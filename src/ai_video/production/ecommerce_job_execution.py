"""Exact per-Shot execution inputs for the Ecommerce Production Job."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ai_video.production.ad_creative_types import AdCreativePlan, CompiledAdCreativeHandoff
from ai_video.production.ecommerce_ad_coordinator import EcommerceVideoGenerationFacade
from ai_video.production.ecommerce_job_assembly import validate_ecommerce_plan_binding
from ai_video.production.ecommerce_job_contracts import EcommerceProductionHandoff
from ai_video.production.ecommerce_job_repair import EcommerceShotRepairContext


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
        validate_ecommerce_plan_binding(runtime_handoff, self.handoff, self.plan)
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


__all__ = [
    "EcommerceShotExecutionInput",
    "EcommerceShotExecutionPlan",
]
