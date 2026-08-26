"""P6 transaction adapter for exact-target Ecommerce Gate 2 evidence."""

from __future__ import annotations

import hashlib
import json

from ai_video.production.ad_creative_types import CompiledAdCreativeHandoff
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.ecommerce_quality_gate import (
    EcommerceAcceptedShotIdentity,
    EcommerceGateBlockReason,
    EcommerceGateOutcome,
    EcommerceGateResult,
    EcommerceQualityGateCoordinator,
    EcommerceWholeAdEvaluator,
    _result,
    universal_qa_gate_result_hash,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    QaLayer,
    QaPolicy,
    QaVerdict,
    ReviewEvidencePointer,
    ReviewReceipt,
    ReviewReceiptPointer,
    ReviewRequest,
    SourceReference,
    ToolIdentity,
)
from ai_video.production.paths import canonical_review_evidence_path
from ai_video.production.project import load_production_project
from ai_video.production.quality_gate_coordinator import (
    UniversalQaContext,
    UniversalQaGateResult,
    UniversalQaProfile,
)
from ai_video.production.review import build_technical_review_context
from ai_video.production.state_commit import ProductionStateCommitter


class EcommerceGateReviewTransaction(StrictModel):
    gate: EcommerceGateOutcome
    review_receipt: ReviewReceiptPointer | None = None
    p6_receipt_recorded: bool = False


def _canonical_json_bytes(value: object) -> bytes:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")  # type: ignore[union-attr]
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (payload + "\n").encode("utf-8")


def _dependency_states_hash(manifest) -> str:
    return canonical_sha256(
        {
            "dependency_states": [
                item.model_dump(mode="json") for item in manifest.dependency_states
            ]
        }
    )


def _record_ecommerce_gate_review(
    *,
    committer: ProductionStateCommitter,
    universal_profile: UniversalQaProfile,
    universal_context: UniversalQaContext,
    universal_result: UniversalQaGateResult,
    policy: QaPolicy,
    handoff: CompiledAdCreativeHandoff,
    accepted_shots: tuple[EcommerceAcceptedShotIdentity, ...],
    tool_identity: ToolIdentity,
    evaluate: EcommerceWholeAdEvaluator,
    attempt_id: str,
    request_id: str,
    evidence_id: str,
    review_id: str,
) -> EcommerceGateReviewTransaction:
    """Persist Gate 2 through the sole P6 review transaction owner."""

    bundle, timeline = committer.current_final_media_target()
    manifest = bundle.manifest
    render_state = bundle.render_state
    if (
        manifest.active_dependency_graph is None
        or manifest.active_render_state is None
        or manifest.active_qa_policy is None
        or render_state is None
        or manifest.active_qa_policy.content_hash != policy.content_hash
        or manifest.active_project.content_hash
        != universal_context.project_content_hash
        or manifest.active_registry.content_hash
        != universal_context.registry_content_hash
        or manifest.active_dependency_graph.revision_id
        != universal_context.dependency_graph_revision_id
        or manifest.active_render_state.content_hash
        != universal_context.render_state_content_hash
        or render_state.output.file_sha256 != universal_context.render_output_sha256
        or render_state.timeline_fingerprint != universal_context.timeline_fingerprint
    ):
        gate = EcommerceGateOutcome(
            result=_result(
                verdict=QaVerdict.NOT_EVALUATED,
                universal_result_hash=universal_qa_gate_result_hash(universal_result),
                block_reason=EcommerceGateBlockReason.REVIEW_REQUEST_NOT_CURRENT,
            )
        )
        return EcommerceGateReviewTransaction(gate=gate)

    domain = policy.domain_acceptance
    if domain is None:
        gate = EcommerceGateOutcome(
            result=_result(
                verdict=QaVerdict.NOT_EVALUATED,
                universal_result_hash=universal_qa_gate_result_hash(universal_result),
                block_reason=EcommerceGateBlockReason.DOMAIN_POLICY_NOT_SELECTED,
            )
        )
        return EcommerceGateReviewTransaction(gate=gate)
    context = build_technical_review_context(
        bundle,
        timeline,
        render_output_sha256=render_state.output.file_sha256,
        measurement_contract_version=domain.measurement_contract_version,
    )
    request = seal_artifact(
        ReviewRequest(
            artifact_id=request_id,
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id=request_id,
            source_provenance=(
                SourceReference(kind="derived", reference=handoff.plan_content_hash),
            ),
            request_id=request_id,
            base_manifest_revision=manifest.manifest_revision,
            dependency_graph=manifest.active_dependency_graph,
            dependency_states_hash=_dependency_states_hash(manifest),
            render_state=manifest.active_render_state,
            render_output_sha256=render_state.output.file_sha256,
            timeline_fingerprint=render_state.timeline_fingerprint,
            qa_policy=manifest.active_qa_policy,
            requested_layers=(QaLayer.SEMANTIC,),
            evidence_tool_identities=(tool_identity,),
            technical_context=context,
        )
    )
    coordinator = EcommerceQualityGateCoordinator()
    prepared = coordinator._prepare(
        universal_profile=universal_profile,
        universal_context=universal_context,
        universal_result=universal_result,
        policy=policy,
        review_request=request,
        handoff=handoff,
        timeline=timeline,
        active_timeline_content_hash=render_state.timeline.content_hash,
        accepted_shots=accepted_shots,
        tool_identity=tool_identity,
    )
    if isinstance(prepared, EcommerceGateResult):
        return EcommerceGateReviewTransaction(
            gate=EcommerceGateOutcome(result=prepared)
        )

    begun = committer.begin_review(request, attempt_id=attempt_id)
    request_pointer = next(
        item.review_request
        for item in begun.attempts
        if item.attempt_id == attempt_id and item.review_request is not None
    )

    def analyzer(
        durable_request: ReviewRequest, permit: object
    ) -> EcommerceGateOutcome:
        return coordinator.run_once(
            universal_profile=universal_profile,
            universal_context=universal_context,
            universal_result=universal_result,
            policy=policy,
            review_request=durable_request,
            handoff=handoff,
            timeline=timeline,
            active_timeline_content_hash=render_state.timeline.content_hash,
            accepted_shots=accepted_shots,
            tool_identity=tool_identity,
            permit=permit,  # type: ignore[arg-type]
            evidence_id=evidence_id,
            evaluate=evaluate,
        )

    gate = committer.run_review_analysis(
        review_request=request_pointer,
        expected_manifest_revision=begun.manifest_revision,
        analyzer=analyzer,
    )
    if not isinstance(gate, EcommerceGateOutcome) or gate.evidence is None:
        raise ValueError("Ecommerce Gate 2 did not produce durable review evidence")
    evidence_payload = _canonical_json_bytes(gate.evidence)
    evidence_pointer = ReviewEvidencePointer(
        path=canonical_review_evidence_path(gate.evidence.content_hash),
        evidence_id=gate.evidence.evidence_id,
        layer=gate.evidence.layer,
        strength=gate.evidence.strength,
        content_hash=gate.evidence.content_hash,
        file_sha256=hashlib.sha256(evidence_payload).hexdigest(),
    )
    receipt = seal_artifact(
        ReviewReceipt(
            artifact_id=review_id,
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id=review_id,
            source_provenance=(
                SourceReference(kind="derived", reference=gate.evidence.evidence_id),
            ),
            review_id=review_id,
            layer=QaLayer.SEMANTIC,
            review_request=request_pointer,
            render_state=request.render_state,
            render_output_sha256=request.render_output_sha256,
            timeline_fingerprint=request.timeline_fingerprint,
            dependency_graph_revision_id=request.dependency_graph.revision_id,
            qa_policy=request.qa_policy,
            evidence=(evidence_pointer,),
            evidence_ids=(gate.evidence.evidence_id,),
            tool_identities=(tool_identity,),
            verdict=gate.result.verdict,
        )
    )
    current = load_production_project(committer.project_root / "project.yaml").manifest
    recorded = committer.record_review_receipt(
        receipt,
        (gate.evidence,),
        expected_manifest_revision=current.manifest_revision,
        attempt_id=attempt_id,
    )
    active_pointer = next(
        item
        for item in recorded.active_review_receipts
        if item.layer is QaLayer.SEMANTIC
    )
    return EcommerceGateReviewTransaction(
        gate=gate,
        review_receipt=active_pointer,
        p6_receipt_recorded=True,
    )


__all__ = [
    "EcommerceGateReviewTransaction",
]
