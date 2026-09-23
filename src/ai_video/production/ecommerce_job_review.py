"""Exact review and delivery facades for the Ecommerce Production Job."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ai_video.errors import AiVideoError
from ai_video.production._caption_quality_p6 import CaptionReviewExecution
from ai_video.production.caption_quality import reopen_caption_review_chain
from ai_video.production.caption_quality_contracts import (
    CAPTION_REQUIREMENT_GROUPS,
    CaptionCoverageStatus,
    CaptionEvidencePayload,
    CaptionFindingReasonCode,
    CaptionRequirementGroup,
)
from ai_video.production.ad_creative_types import AdCreativePlan, CompiledAdCreativeHandoff
from ai_video.production.delivery_packager import (
    EcommerceDeliveryBundleResult,
    inspect_ecommerce_delivery,
    package_ecommerce_delivery,
)
from ai_video.production.ecommerce_ad_coordinator import (
    EcommercePostMediaAcceptanceResult,
    EcommerceVideoGenerationFacade,
    close_ecommerce_post_media_candidate,
)
from ai_video.production.ecommerce_job_assembly import validate_ecommerce_plan_binding
from ai_video.production.ecommerce_job_contracts import EcommerceProductionHandoff
from ai_video.production.ecommerce_media_acceptance import (
    EcommerceAcceptanceEvidencePayload,
)
from ai_video.production.ecommerce_quality_gate import (
    EcommerceWholeAdEvaluator,
    validate_ecommerce_final_output_contract,
)
from ai_video.production.final_output_review import FinalOutputObservation
from ai_video.production.models import QaLayer, QaVerdict, ReviewLifecycle, ToolIdentity
from ai_video.production.project import (
    load_production_project,
    load_review_evidence,
    load_review_receipt,
)
from ai_video.production.quality_gate_coordinator import (
    HardCheckRunner,
    ReviewLayerRunner,
    UniversalQaProfile,
)
from ai_video.production.state_commit import ProductionStateCommitter


class EcommerceFinalReviewFrontier(str, Enum):
    PACKAGE_DELIVERY = "package_delivery"
    PREPARE_COMPOSITION = "prepare_composition"
    REVIEW_FINAL = "review_final"
    EVIDENCE_REPAIR_REQUIRED = "evidence_repair_required"
    DIAGNOSIS_REQUIRED = "diagnosis_required"


def _caption_repair_frontier(project, pointer) -> EcommerceFinalReviewFrontier:
    """Only cue timing/readability failures justify a composition-only repair."""

    try:
        reopened = reopen_caption_review_chain(
            project=project, receipt_pointer=pointer
        )
        if reopened.verdict is not QaVerdict.FAIL:
            return EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED
        findings = tuple(
            finding
            for evidence in reopened.evidence
            for finding in CaptionEvidencePayload.model_validate(
                dict(evidence.measured_payload)
            ).findings
        )
    except (AiVideoError, OSError, TypeError, ValueError):
        return EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED
    if (
        {finding.requirement_group for finding in findings}
        != set(CAPTION_REQUIREMENT_GROUPS)
        or any(
            finding.verdict == "not_evaluated"
            or finding.coverage_status is not CaptionCoverageStatus.COMPLETE
            for finding in findings
        )
    ):
        return EcommerceFinalReviewFrontier.EVIDENCE_REPAIR_REQUIRED
    failed = tuple(finding for finding in findings if finding.verdict == "fail")
    if any(
        finding.reason_code
        in {
            CaptionFindingReasonCode.COVERAGE_PARTIAL,
            CaptionFindingReasonCode.UNSUPPORTED_LANGUAGE_OR_TOOL,
            CaptionFindingReasonCode.LOW_CONFIDENCE,
            CaptionFindingReasonCode.IDENTITY_MISMATCH,
            CaptionFindingReasonCode.CONFLICTING_EVIDENCE,
        }
        for finding in failed
    ) or any(
        finding.requirement_group == passed.requirement_group
        for finding in failed
        for passed in findings
        if passed.verdict == "pass"
    ):
        return EcommerceFinalReviewFrontier.EVIDENCE_REPAIR_REQUIRED
    local_reasons = {
        CaptionRequirementGroup.TIMING_CONTRACT:
            CaptionFindingReasonCode.TIMING_OUT_OF_BOUNDS,
        CaptionRequirementGroup.LAYOUT_READABILITY:
            CaptionFindingReasonCode.LAYOUT_UNREADABLE,
    }
    if failed and all(
        local_reasons.get(finding.requirement_group) is finding.reason_code
        for finding in failed
    ):
        return EcommerceFinalReviewFrontier.PREPARE_COMPOSITION
    return EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED


def _semantic_repair_frontier(
    evidence: object,
) -> EcommerceFinalReviewFrontier:
    payload = getattr(evidence, "measured_payload", {})
    try:
        domain = EcommerceAcceptanceEvidencePayload.model_validate(
            payload.get("domain_acceptance")
        )
        FinalOutputObservation.model_validate(
            payload.get("final_output")
        )
    except (TypeError, ValueError):
        return EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED
    if any(item.verdict is not QaVerdict.PASS for item in domain.findings):
        return EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED
    # A semantic finding does not prove that its fix is independent of the
    # sealed AdCreativePlan. CTA and other plan-bound graphics need a new
    # authoring handoff, not a CompositionSpec-only repair.
    return EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED


def inspect_ecommerce_review_frontier(
    project_root: Path,
) -> EcommerceFinalReviewFrontier:
    """Fail closed when no exact execution plan can diagnose semantic evidence."""

    project = load_production_project(project_root / "project.yaml")
    manifest = project.manifest
    receipts = tuple(
        (pointer, load_review_receipt(project_root, pointer))
        for pointer in manifest.active_review_receipts
    )
    if any(receipt.verdict is QaVerdict.NOT_EVALUATED for _, receipt in receipts):
        return EcommerceFinalReviewFrontier.EVIDENCE_REPAIR_REQUIRED
    failed = [
        (pointer, receipt)
        for pointer, receipt in receipts
        if receipt.verdict is QaVerdict.FAIL
    ]
    if len(failed) == 1 and failed[0][1].layer is QaLayer.CAPTION:
        return _caption_repair_frontier(project, failed[0][0])
    if failed:
        return EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED
    return EcommerceFinalReviewFrontier.REVIEW_FINAL


@dataclass(frozen=True)
class EcommercePostMediaExecutionPlan:
    handoff: CompiledAdCreativeHandoff
    plan: AdCreativePlan
    shot_facades: Mapping[str, EcommerceVideoGenerationFacade]
    committer: ProductionStateCommitter
    universal_profile: UniversalQaProfile
    run_hard_check: HardCheckRunner
    run_review_layer: ReviewLayerRunner
    tool_identity: ToolIdentity
    evaluate: EcommerceWholeAdEvaluator
    review_attempt_id: str
    review_request_id: str
    evidence_id: str
    review_id: str
    final_acceptance_id: str
    caption_review_execution: CaptionReviewExecution | None = None

    def _validate_runtime_binding(
        self,
        runtime_handoff: EcommerceProductionHandoff,
        *,
        project_root: Path,
    ):
        validate_ecommerce_plan_binding(runtime_handoff, self.handoff, self.plan)
        if self.committer.project_root.resolve() != project_root.resolve():
            raise ValueError("Ecommerce review committer is bound to another Project")
        bundle, timeline = self.committer.current_final_media_target()
        policy = bundle.qa_policy
        if policy is None:
            raise ValueError("Selected QA policy is required for Ecommerce review")
        validate_ecommerce_final_output_contract(runtime_handoff, policy)
        if timeline.caption_cues and (
            policy.caption_policy is None
            or QaLayer.CAPTION not in policy.required_layers
            or not self.universal_profile.applicability.has_captions
            or QaLayer.CAPTION
            not in self.universal_profile.required_review_layers
        ):
            raise ValueError("Caption-applicable output requires caption policy and review")
        return bundle, timeline

    def inspect_frontier(
        self,
        runtime_handoff: EcommerceProductionHandoff,
        *,
        project_root: Path,
    ) -> EcommerceFinalReviewFrontier:
        self._validate_runtime_binding(runtime_handoff, project_root=project_root)
        manifest = load_production_project(project_root / "project.yaml").manifest
        acceptance = manifest.final_acceptance_state
        if (
            acceptance is not None
            and acceptance.lifecycle is ReviewLifecycle.FRESH
            and acceptance.active_receipt is not None
        ):
            return EcommerceFinalReviewFrontier.PACKAGE_DELIVERY
        failed = []
        not_evaluated = False
        for pointer in manifest.active_review_receipts:
            receipt = load_review_receipt(project_root, pointer)
            if receipt.verdict is QaVerdict.FAIL:
                failed.append((pointer, receipt))
            elif receipt.verdict is QaVerdict.NOT_EVALUATED:
                not_evaluated = True
        if not_evaluated:
            return EcommerceFinalReviewFrontier.EVIDENCE_REPAIR_REQUIRED
        if not failed:
            return EcommerceFinalReviewFrontier.REVIEW_FINAL
        failed_layers = {receipt.layer for _, receipt in failed}
        if len(failed) == 1 and failed[0][1].layer is QaLayer.CAPTION:
            return _caption_repair_frontier(
                load_production_project(project_root / "project.yaml"),
                failed[0][0],
            )
        if failed_layers - {QaLayer.LAYOUT, QaLayer.CAPTION, QaLayer.SEMANTIC}:
            return EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED
        semantic = [item for item in failed if item[1].layer is QaLayer.SEMANTIC]
        if len(semantic) != 1:
            return EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED
        evidence = tuple(
            load_review_evidence(project_root, pointer)
            for pointer in semantic[0][1].evidence
        )
        if len(evidence) != 1:
            return EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED
        return _semantic_repair_frontier(evidence[0])

    def run(
        self,
        runtime_handoff: EcommerceProductionHandoff,
        *,
        project_root: Path,
    ) -> EcommercePostMediaAcceptanceResult:
        self._validate_runtime_binding(runtime_handoff, project_root=project_root)
        return close_ecommerce_post_media_candidate(
            committer=self.committer,
            handoff=self.handoff,
            shot_facades=self.shot_facades,
            universal_profile=self.universal_profile,
            run_hard_check=self.run_hard_check,
            run_review_layer=self.run_review_layer,
            caption_review_execution=self.caption_review_execution,
            tool_identity=self.tool_identity,
            evaluate=self.evaluate,
            review_attempt_id=self.review_attempt_id,
            review_request_id=self.review_request_id,
            evidence_id=self.evidence_id,
            review_id=self.review_id,
            final_acceptance_id=self.final_acceptance_id,
            runtime_handoff=runtime_handoff,
        )


@dataclass(frozen=True)
class EcommerceDeliveryExecutionPlan:
    delivery_root: Path
    plan: AdCreativePlan
    compiled_handoff: CompiledAdCreativeHandoff
    exported_at: str
    tool_identity: ToolIdentity

    def inspect(
        self,
        runtime_handoff: EcommerceProductionHandoff,
        *,
        project_root: Path,
        job_id: str,
    ) -> EcommerceDeliveryBundleResult | None:
        return inspect_ecommerce_delivery(
            project_root=project_root,
            delivery_root=self.delivery_root,
            job_id=job_id,
            handoff=runtime_handoff,
            plan=self.plan,
            compiled_handoff=self.compiled_handoff,
            exported_at=self.exported_at,
            tool_identity=self.tool_identity,
        )

    def package(
        self,
        runtime_handoff: EcommerceProductionHandoff,
        *,
        project_root: Path,
        job_id: str,
    ) -> EcommerceDeliveryBundleResult:
        return package_ecommerce_delivery(
            project_root=project_root,
            delivery_root=self.delivery_root,
            job_id=job_id,
            handoff=runtime_handoff,
            plan=self.plan,
            compiled_handoff=self.compiled_handoff,
            exported_at=self.exported_at,
            tool_identity=self.tool_identity,
        )


__all__ = [
    "EcommerceDeliveryExecutionPlan",
    "EcommercePostMediaExecutionPlan",
]
