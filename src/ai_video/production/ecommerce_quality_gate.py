"""Exact-target Ecommerce whole-ad Gate 2 over the existing P6 evidence envelope."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Protocol

from pydantic import Field, ValidationError, model_validator

from ai_video.production.ad_creative_types import CompiledAdCreativeHandoff
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.composition_contracts import ResolvedTimeline
from ai_video.production.composition import timeline_fingerprint
from ai_video.production.ecommerce_media_acceptance import (
    EcommerceAcceptanceEvidencePayload,
    EcommerceAcceptanceProfile,
    adjudicate_ecommerce_acceptance,
)
from ai_video.production.hashing import (
    canonical_sha256,
    seal_artifact,
    verify_artifact_hash,
)
from ai_video.production.models import (
    EvidenceStrength,
    QaLayer,
    QaPolicy,
    QaVerdict,
    ReviewEvidence,
    ReviewRequest,
    SourceReference,
    ToolIdentity,
)
from ai_video.production.quality_gate_coordinator import (
    UniversalQaContext,
    UniversalQaGateResult,
    UniversalQaProfile,
)


_SHA256 = r"^[0-9a-f]{64}$"


class EcommerceGateBlockReason(str, Enum):
    INPUT_INVALID = "input_invalid"
    UNIVERSAL_GATE_NOT_PASS = "universal_gate_not_pass"
    UNIVERSAL_GATE_NOT_CURRENT = "universal_gate_not_current"
    DOMAIN_POLICY_NOT_SELECTED = "domain_policy_not_selected"
    REVIEW_REQUEST_NOT_CURRENT = "review_request_not_current"
    COMPOSITION_NOT_CURRENT = "composition_not_current"
    SHOT_LINEAGE_NOT_CURRENT = "shot_lineage_not_current"
    DOMAIN_EVIDENCE_INVALID = "domain_evidence_invalid"
    DOMAIN_EVIDENCE_BLOCKED = "domain_evidence_blocked"


class EcommerceAcceptedShotIdentity(StrictModel):
    """Immutable projection of one exact activated Shot checkpoint."""

    schema_version: Literal["ecommerce-accepted-shot/1"] = "ecommerce-accepted-shot/1"
    ad_creative_plan_hash: str = Field(pattern=_SHA256)
    commercial_execution_projection_hash: str = Field(pattern=_SHA256)
    shot_id: str = Field(min_length=1)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    artifact_sha256: str = Field(pattern=_SHA256)
    commercial_evidence_content_hash: str = Field(pattern=_SHA256)
    checkpoint_content_hash: str = Field(pattern=_SHA256)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "EcommerceAcceptedShotIdentity":
        if self.content_hash != canonical_sha256(self):
            raise ValueError("Accepted Ecommerce Shot identity hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "EcommerceAcceptedShotIdentity":
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {**values, "content_hash": canonical_sha256(provisional)}
        )


class EcommerceWholeAdAcceptanceTarget(StrictModel):
    """The exact final-media and upstream lineage accepted by Gate 2."""

    schema_version: Literal["ecommerce-whole-ad-acceptance-target/1"] = (
        "ecommerce-whole-ad-acceptance-target/1"
    )
    ad_creative_plan_hash: str = Field(pattern=_SHA256)
    accepted_shots: tuple[EcommerceAcceptedShotIdentity, ...] = ()
    composition_spec_content_hash: str = Field(pattern=_SHA256)
    resolved_timeline_content_hash: str = Field(pattern=_SHA256)
    timeline_fingerprint: str = Field(pattern=_SHA256)
    project_content_hash: str = Field(pattern=_SHA256)
    registry_content_hash: str = Field(pattern=_SHA256)
    dependency_graph_revision_id: str = Field(pattern=_SHA256)
    render_state_content_hash: str = Field(pattern=_SHA256)
    render_output_sha256: str = Field(pattern=_SHA256)
    qa_policy_content_hash: str = Field(pattern=_SHA256)
    ecommerce_profile_content_hash: str = Field(pattern=_SHA256)
    universal_profile_content_hash: str = Field(pattern=_SHA256)
    universal_context_content_hash: str = Field(pattern=_SHA256)
    universal_gate_result_hash: str = Field(pattern=_SHA256)
    review_request_content_hash: str = Field(pattern=_SHA256)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "EcommerceWholeAdAcceptanceTarget":
        if self.content_hash != canonical_sha256(self):
            raise ValueError("Ecommerce whole-ad acceptance target hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "EcommerceWholeAdAcceptanceTarget":
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {**values, "content_hash": canonical_sha256(provisional)}
        )


class EcommerceGateResult(StrictModel):
    schema_version: Literal["ecommerce-whole-ad-gate-result/1"] = (
        "ecommerce-whole-ad-gate-result/1"
    )
    verdict: QaVerdict
    target_content_hash: str | None = Field(default=None, pattern=_SHA256)
    universal_gate_result_hash: str | None = Field(default=None, pattern=_SHA256)
    evidence_content_hash: str | None = Field(default=None, pattern=_SHA256)
    block_reason: EcommerceGateBlockReason | None = None
    blocked_identifiers: tuple[str, ...] = ()
    eligible_for_p6_review: bool = False
    eligible_for_final_acceptance: bool = False
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_result(self) -> "EcommerceGateResult":
        if self.content_hash != canonical_sha256(self):
            raise ValueError("Ecommerce Gate result hash is invalid")
        if self.eligible_for_p6_review and (
            self.verdict is not QaVerdict.PASS
            or self.target_content_hash is None
            or self.universal_gate_result_hash is None
            or self.evidence_content_hash is None
            or self.block_reason is not None
        ):
            raise ValueError("P6 eligibility requires exact PASS evidence")
        if self.eligible_for_final_acceptance:
            raise ValueError("Gate 2 cannot issue Final Acceptance")
        return self

    @classmethod
    def create(cls, **values: object) -> "EcommerceGateResult":
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {**values, "content_hash": canonical_sha256(provisional)}
        )


class EcommerceGateOutcome(StrictModel):
    result: EcommerceGateResult
    target: EcommerceWholeAdAcceptanceTarget | None = None
    evidence: ReviewEvidence | None = None


class ReviewAnalysisPermit(Protocol):
    def _consume_review_analysis_permit(
        self,
        *,
        request_content_hash: str,
        render_output_sha256: str,
        technical_context_hash: str,
    ) -> bool: ...


EcommerceWholeAdEvaluator = Callable[
    [EcommerceWholeAdAcceptanceTarget, EcommerceAcceptanceProfile],
    EcommerceAcceptanceEvidencePayload,
]


def universal_qa_context_content_hash(context: UniversalQaContext) -> str:
    return canonical_sha256(
        {
            "schema": "universal-qa-context/1",
            **context.model_dump(mode="json"),
        }
    )


def universal_qa_gate_result_hash(result: UniversalQaGateResult) -> str:
    return canonical_sha256(
        {
            "schema": "universal-qa-gate-result/1",
            **result.model_dump(mode="json"),
        }
    )


def validate_ecommerce_review_evidence_binding(
    *,
    policy: QaPolicy,
    evidence: ReviewEvidence,
    review_request_content_hash: str | None,
) -> bool:
    """Validate the Gate 1 and exact-target envelope carried by P6 evidence."""

    if review_request_content_hash is None or policy.domain_acceptance is None:
        return False
    payload = evidence.measured_payload
    try:
        target_payload = payload.get("acceptance_target")
        gate_payload = payload.get("universal_gate_result")
        context_payload = payload.get("universal_qa_context")
        profile_payload = payload.get("universal_qa_profile")
        if not all(
            isinstance(item, dict) or hasattr(item, "items")
            for item in (target_payload, gate_payload, context_payload, profile_payload)
        ):
            return False
        target = EcommerceWholeAdAcceptanceTarget.model_validate(dict(target_payload))  # type: ignore[arg-type]
        gate_result = UniversalQaGateResult.model_validate(dict(gate_payload))  # type: ignore[arg-type]
        context = UniversalQaContext.model_validate(dict(context_payload))  # type: ignore[arg-type]
        profile = UniversalQaProfile.model_validate(dict(profile_payload))  # type: ignore[arg-type]
    except (TypeError, ValidationError, ValueError):
        return False

    gate_hash = universal_qa_gate_result_hash(gate_result)
    context_hash = universal_qa_context_content_hash(context)
    domain = policy.domain_acceptance
    return (
        gate_result.verdict is QaVerdict.PASS
        and gate_result.eligible_for_domain_gate
        and gate_result.profile_content_hash == profile.content_hash
        and gate_result.context_content_hash == context_hash
        and gate_result.qa_policy_content_hash == policy.content_hash
        and gate_result.expected_qa_policy_content_hash == policy.content_hash
        and target.universal_gate_result_hash == gate_hash
        and target.universal_context_content_hash == context_hash
        and target.universal_profile_content_hash == profile.content_hash
        and target.review_request_content_hash == review_request_content_hash
        and target.render_output_sha256 == evidence.render_output_sha256
        and target.timeline_fingerprint == evidence.timeline_fingerprint
        and target.dependency_graph_revision_id == evidence.dependency_graph_revision_id
        and target.render_output_sha256 == context.render_output_sha256
        and target.timeline_fingerprint == context.timeline_fingerprint
        and target.dependency_graph_revision_id == context.dependency_graph_revision_id
        and target.render_state_content_hash == context.render_state_content_hash
        and target.project_content_hash == context.project_content_hash
        and target.registry_content_hash == context.registry_content_hash
        and target.qa_policy_content_hash == policy.content_hash
        and target.ecommerce_profile_content_hash == domain.profile_content_hash
    )


def _result(
    *,
    verdict: QaVerdict,
    target: EcommerceWholeAdAcceptanceTarget | None = None,
    universal_result_hash: str | None = None,
    evidence: ReviewEvidence | None = None,
    block_reason: EcommerceGateBlockReason | None = None,
    blocked_identifiers: tuple[str, ...] = (),
    eligible_for_p6_review: bool = False,
) -> EcommerceGateResult:
    return EcommerceGateResult.create(
        verdict=verdict,
        target_content_hash=None if target is None else target.content_hash,
        universal_gate_result_hash=universal_result_hash,
        evidence_content_hash=None if evidence is None else evidence.content_hash,
        block_reason=block_reason,
        blocked_identifiers=blocked_identifiers,
        eligible_for_p6_review=eligible_for_p6_review,
        eligible_for_final_acceptance=False,
    )


@dataclass(frozen=True)
class _PreparedGate:
    target: EcommerceWholeAdAcceptanceTarget
    profile: EcommerceAcceptanceProfile
    universal_result_hash: str


class EcommerceQualityGateCoordinator:
    """Run Gate 2 once for one exact Gate-1-qualified final candidate."""

    def _prepare(
        self,
        *,
        universal_profile: UniversalQaProfile,
        universal_context: UniversalQaContext,
        universal_result: UniversalQaGateResult,
        policy: QaPolicy,
        review_request: ReviewRequest,
        handoff: CompiledAdCreativeHandoff,
        timeline: ResolvedTimeline,
        active_timeline_content_hash: str,
        accepted_shots: tuple[EcommerceAcceptedShotIdentity, ...],
        tool_identity: ToolIdentity,
    ) -> _PreparedGate | EcommerceGateResult:
        try:
            selected_profile = UniversalQaProfile.model_validate(
                universal_profile.model_dump(mode="json")
            )
            selected_context = UniversalQaContext.model_validate(
                universal_context.model_dump(mode="json")
            )
            selected_result = UniversalQaGateResult.model_validate(
                universal_result.model_dump(mode="json")
            )
            selected_policy = QaPolicy.model_validate(policy.model_dump(mode="json"))
            selected_request = ReviewRequest.model_validate(
                review_request.model_dump(mode="json")
            )
            selected_handoff = CompiledAdCreativeHandoff.model_validate(
                handoff.model_dump(mode="python")
            )
            selected_timeline = ResolvedTimeline.model_validate(
                timeline.model_dump(mode="json")
            )
            selected_shots = tuple(
                EcommerceAcceptedShotIdentity.model_validate(
                    item.model_dump(mode="json")
                )
                for item in accepted_shots
            )
        except (AttributeError, TypeError, ValidationError, ValueError):
            return _result(
                verdict=QaVerdict.NOT_EVALUATED,
                block_reason=EcommerceGateBlockReason.INPUT_INVALID,
            )

        result_hash = universal_qa_gate_result_hash(selected_result)
        context_hash = universal_qa_context_content_hash(selected_context)
        if (
            selected_result.verdict is not QaVerdict.PASS
            or not selected_result.eligible_for_domain_gate
        ):
            return _result(
                verdict=QaVerdict.NOT_EVALUATED,
                universal_result_hash=result_hash,
                block_reason=EcommerceGateBlockReason.UNIVERSAL_GATE_NOT_PASS,
            )
        if (
            selected_result.profile_content_hash != selected_profile.content_hash
            or selected_result.context_content_hash != context_hash
            or selected_result.qa_policy_content_hash != selected_policy.content_hash
            or selected_result.expected_qa_policy_content_hash
            != selected_policy.content_hash
        ):
            return _result(
                verdict=QaVerdict.NOT_EVALUATED,
                universal_result_hash=result_hash,
                block_reason=EcommerceGateBlockReason.UNIVERSAL_GATE_NOT_CURRENT,
            )

        domain = selected_policy.domain_acceptance
        if domain is None or domain.domain_id != "ecommerce":
            return _result(
                verdict=QaVerdict.NOT_EVALUATED,
                universal_result_hash=result_hash,
                block_reason=EcommerceGateBlockReason.DOMAIN_POLICY_NOT_SELECTED,
            )
        try:
            ecommerce_profile = EcommerceAcceptanceProfile.model_validate(
                domain.profile_payload
            )
        except ValidationError:
            return _result(
                verdict=QaVerdict.NOT_EVALUATED,
                universal_result_hash=result_hash,
                block_reason=EcommerceGateBlockReason.DOMAIN_POLICY_NOT_SELECTED,
            )

        if (
            not verify_artifact_hash(selected_policy)
            or not verify_artifact_hash(selected_request)
            or selected_request.requested_layers != (QaLayer.SEMANTIC,)
            or selected_request.evidence_tool_identities != (tool_identity,)
            or tool_identity not in selected_policy.semantic_authorities
            or selected_request.qa_policy.content_hash != selected_policy.content_hash
            or selected_request.dependency_graph.revision_id
            != selected_context.dependency_graph_revision_id
            or selected_request.render_state.content_hash
            != selected_context.render_state_content_hash
            or selected_request.render_output_sha256
            != selected_context.render_output_sha256
            or selected_request.timeline_fingerprint
            != selected_context.timeline_fingerprint
            or selected_request.technical_context.render_output_sha256
            != selected_request.render_output_sha256
            or selected_request.technical_context.timeline_fingerprint
            != selected_request.timeline_fingerprint
            or selected_request.technical_context.measurement_contract_version
            != domain.measurement_contract_version
        ):
            return _result(
                verdict=QaVerdict.NOT_EVALUATED,
                universal_result_hash=result_hash,
                block_reason=EcommerceGateBlockReason.REVIEW_REQUEST_NOT_CURRENT,
            )

        composition = selected_handoff.composition_spec
        composition_checks = {
            "composition_hash": verify_artifact_hash(composition),
            "timeline_hash": verify_artifact_hash(selected_timeline),
            "active_timeline_hash": (
                selected_timeline.content_hash == active_timeline_content_hash
            ),
            "computed_timeline_fingerprint": (
                timeline_fingerprint(selected_timeline)
                == selected_timeline.composition_fingerprint
            ),
            "plan_id": composition.ad_creative_plan_id == selected_handoff.plan_id,
            "plan_hash": (
                composition.ad_creative_plan_hash == selected_handoff.plan_content_hash
            ),
            "composition_id": (
                selected_timeline.composition_spec_id == composition.artifact_id
            ),
            "composition_revision": (
                selected_timeline.composition_spec_revision == composition.revision
            ),
            "composition_content_hash": (
                selected_timeline.composition_spec_hash == composition.content_hash
            ),
            "timeline_fingerprint": (
                selected_timeline.composition_fingerprint
                == selected_request.timeline_fingerprint
            ),
            "delivery_profile": (
                selected_timeline.delivery_profile == selected_context.delivery_profile
            ),
        }
        failed_composition_checks = tuple(
            name for name, passed in composition_checks.items() if not passed
        )
        if failed_composition_checks:
            return _result(
                verdict=QaVerdict.NOT_EVALUATED,
                universal_result_hash=result_hash,
                block_reason=EcommerceGateBlockReason.COMPOSITION_NOT_CURRENT,
                blocked_identifiers=failed_composition_checks,
            )

        projection_by_shot = {
            item.target_shot_id: item
            for item in selected_handoff.commercial_execution_projections
        }
        expected_provider_shots = tuple(
            item.shot_id
            for item in selected_handoff.shot_proposals
            if projection_by_shot[item.shot_id].invoke_video_provider
        )
        if tuple(item.shot_id for item in selected_shots) != expected_provider_shots:
            return _result(
                verdict=QaVerdict.NOT_EVALUATED,
                universal_result_hash=result_hash,
                block_reason=EcommerceGateBlockReason.SHOT_LINEAGE_NOT_CURRENT,
                blocked_identifiers=expected_provider_shots,
            )
        spans_by_shot: dict[str, set[str]] = {}
        for span in selected_timeline.visual_spans:
            spans_by_shot.setdefault(span.shot_id, set()).add(span.asset_sha256)
        for shot in selected_shots:
            projection = projection_by_shot.get(shot.shot_id)
            if (
                projection is None
                or shot.ad_creative_plan_hash != selected_handoff.plan_content_hash
                or shot.commercial_execution_projection_hash
                != projection.projection_hash
                or shot.artifact_sha256 not in spans_by_shot.get(shot.shot_id, set())
            ):
                return _result(
                    verdict=QaVerdict.NOT_EVALUATED,
                    universal_result_hash=result_hash,
                    block_reason=EcommerceGateBlockReason.SHOT_LINEAGE_NOT_CURRENT,
                    blocked_identifiers=(shot.shot_id,),
                )

        target = EcommerceWholeAdAcceptanceTarget.create(
            ad_creative_plan_hash=selected_handoff.plan_content_hash,
            accepted_shots=selected_shots,
            composition_spec_content_hash=composition.content_hash,
            resolved_timeline_content_hash=selected_timeline.content_hash,
            timeline_fingerprint=selected_timeline.composition_fingerprint,
            project_content_hash=selected_context.project_content_hash,
            registry_content_hash=selected_context.registry_content_hash,
            dependency_graph_revision_id=selected_context.dependency_graph_revision_id,
            render_state_content_hash=selected_context.render_state_content_hash,
            render_output_sha256=selected_context.render_output_sha256,
            qa_policy_content_hash=selected_policy.content_hash,
            ecommerce_profile_content_hash=ecommerce_profile.content_hash,
            universal_profile_content_hash=selected_profile.content_hash,
            universal_context_content_hash=context_hash,
            universal_gate_result_hash=result_hash,
            review_request_content_hash=selected_request.content_hash,
        )
        return _PreparedGate(
            target=target,
            profile=ecommerce_profile,
            universal_result_hash=result_hash,
        )

    def run_once(
        self,
        *,
        universal_profile: UniversalQaProfile,
        universal_context: UniversalQaContext,
        universal_result: UniversalQaGateResult,
        policy: QaPolicy,
        review_request: ReviewRequest,
        handoff: CompiledAdCreativeHandoff,
        timeline: ResolvedTimeline,
        active_timeline_content_hash: str,
        accepted_shots: tuple[EcommerceAcceptedShotIdentity, ...],
        tool_identity: ToolIdentity,
        permit: ReviewAnalysisPermit,
        evidence_id: str,
        evaluate: EcommerceWholeAdEvaluator,
    ) -> EcommerceGateOutcome:
        prepared = self._prepare(
            universal_profile=universal_profile,
            universal_context=universal_context,
            universal_result=universal_result,
            policy=policy,
            review_request=review_request,
            handoff=handoff,
            timeline=timeline,
            active_timeline_content_hash=active_timeline_content_hash,
            accepted_shots=accepted_shots,
            tool_identity=tool_identity,
        )
        if isinstance(prepared, EcommerceGateResult):
            return EcommerceGateOutcome(result=prepared)

        consumed = permit._consume_review_analysis_permit(
            request_content_hash=review_request.content_hash,
            render_output_sha256=review_request.render_output_sha256,
            technical_context_hash=canonical_sha256(
                review_request.technical_context.model_dump(mode="json")
            ),
        )
        if consumed is not True:
            raise ValueError("Review analysis permit is invalid or already consumed")

        payload: EcommerceAcceptanceEvidencePayload | None
        try:
            payload = EcommerceAcceptanceEvidencePayload.model_validate(
                evaluate(prepared.target, prepared.profile).model_dump(mode="json")
            )
        except (AttributeError, TypeError, ValidationError, ValueError):
            payload = None

        measured_payload: dict[str, object] = {
            "coverage_complete": payload is not None,
            "evaluator_identity": f"{tool_identity.name}@{tool_identity.version}",
            "acceptance_target": prepared.target.model_dump(mode="json"),
            "universal_gate_result": universal_result.model_dump(mode="json"),
            "universal_qa_context": universal_context.model_dump(mode="json"),
            "universal_qa_profile": universal_profile.model_dump(mode="json"),
        }
        if payload is None:
            measured_payload["domain_evidence_invalid"] = True
            verdict = QaVerdict.NOT_EVALUATED
        else:
            measured_payload["domain_acceptance"] = payload.model_dump(mode="json")
            verdict = adjudicate_ecommerce_acceptance(policy.domain_acceptance, payload)  # type: ignore[arg-type]
        evidence = seal_artifact(
            ReviewEvidence(
                artifact_id=evidence_id,
                revision=1,
                content_hash="0" * 64,
                creation_receipt_id=evidence_id,
                source_provenance=(
                    SourceReference(
                        kind="derived", reference=prepared.target.content_hash
                    ),
                ),
                evidence_id=evidence_id,
                layer=QaLayer.SEMANTIC,
                strength=EvidenceStrength.EXPLICIT_EVALUATOR,
                render_output_sha256=review_request.render_output_sha256,
                timeline_fingerprint=review_request.timeline_fingerprint,
                dependency_graph_revision_id=(
                    review_request.dependency_graph.revision_id
                ),
                tool_identity=tool_identity,
                measurement_contract_version=(
                    review_request.technical_context.measurement_contract_version
                ),
                subject_ids=handoff.composition_spec.shot_ids,
                measured_payload=measured_payload,
            )
        )
        result = _result(
            verdict=verdict,
            target=prepared.target,
            universal_result_hash=prepared.universal_result_hash,
            evidence=evidence,
            block_reason=(
                None
                if verdict is QaVerdict.PASS
                else (
                    EcommerceGateBlockReason.DOMAIN_EVIDENCE_INVALID
                    if payload is None
                    else EcommerceGateBlockReason.DOMAIN_EVIDENCE_BLOCKED
                )
            ),
            eligible_for_p6_review=verdict is QaVerdict.PASS,
        )
        return EcommerceGateOutcome(
            result=result,
            target=prepared.target,
            evidence=evidence,
        )


__all__ = [
    "EcommerceAcceptedShotIdentity",
    "EcommerceGateBlockReason",
    "EcommerceGateOutcome",
    "EcommerceGateResult",
    "EcommerceQualityGateCoordinator",
    "EcommerceWholeAdAcceptanceTarget",
    "EcommerceWholeAdEvaluator",
    "universal_qa_context_content_hash",
    "universal_qa_gate_result_hash",
    "validate_ecommerce_review_evidence_binding",
]
