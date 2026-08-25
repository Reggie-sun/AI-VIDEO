from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.models import QaVerdict
from ai_video.production.models import EvidenceStrength, ToolIdentity
from ai_video.production.video import GeneratedCommercialShotBinding


def _api() -> tuple[object, ...]:
    from ai_video.production.ecommerce_media_acceptance import (
        EcommerceAcceptanceEvidencePayload,
        EcommerceRequirementFinding,
        adjudicate_ecommerce_acceptance,
        create_qingyan_ecommerce_acceptance_profile,
    )

    return (
        EcommerceAcceptanceEvidencePayload,
        EcommerceRequirementFinding,
        adjudicate_ecommerce_acceptance,
        create_qingyan_ecommerce_acceptance_profile,
    )


def _profile_and_policy() -> tuple[object, DomainAcceptancePolicy]:
    *_, create_profile = _api()
    profile = create_profile()
    policy = DomainAcceptancePolicy(
        domain_id="ecommerce",
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_content_hash=profile.content_hash,
        profile_payload=profile.model_dump(mode="json"),
        measurement_contract_version="ecommerce-media-acceptance/1",
        required_requirement_ids=profile.required_requirement_ids,
    )
    return profile, policy


def _payload(
    *,
    verdicts: tuple[QaVerdict, ...] | None = None,
    requirement_ids: tuple[str, ...] | None = None,
) -> object:
    EvidencePayload, Finding, *_ = _api()
    profile, _ = _profile_and_policy()
    selected_ids = requirement_ids or profile.required_requirement_ids
    selected_verdicts = verdicts or tuple(QaVerdict.PASS for _ in selected_ids)
    return EvidencePayload.create(
        domain_id="ecommerce",
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_content_hash=profile.content_hash,
        measurement_contract_version="ecommerce-media-acceptance/1",
        findings=tuple(
            Finding(
                requirement_id=requirement_id,
                verdict=verdict,
                rationale=f"observed {requirement_id}",
            )
            for requirement_id, verdict in zip(
                selected_ids, selected_verdicts, strict=True
            )
        ),
    )


def test_qingyan_profile_seals_exact_shot_and_whole_ad_requirements() -> None:
    *_, create_profile = _api()
    profile = create_profile()

    assert profile.shot_requirement_ids == (
        "shot.identity.main_character",
        "shot.identity.elder",
        "shot.cast.allowed_count",
        "shot.product.presence_window",
        "shot.product.packaging_identity",
        "shot.product.label_fidelity",
        "shot.product.interaction",
        "shot.dialogue.verbatim",
        "shot.dialogue.speaker_binding",
        "shot.motion.required",
        "shot.camera.intent",
        "shot.continuity.in_out",
    )
    assert profile.required_requirement_ids == (
        "ad.hook.first_second",
        "ad.arc.problem_recommendation_use_payoff",
        "ad.cast.elder_interaction",
        "ad.product.first_appearance",
        "ad.product.exposure_balance",
        "ad.product.packaging_consistency",
        "ad.audio.coverage",
        "ad.audio.product_recommendation",
        "ad.audio.voice_continuity",
        "ad.cta.brand_closure",
        "ad.continuity.character",
        "ad.motion.required_windows",
        "ad.edit.pacing",
        "ad.copy.claim_compliance",
        "ad.delivery.duration_aspect",
    )
    with pytest.raises(ValidationError, match="content hash"):
        type(profile).model_validate(
            {
                **profile.model_dump(mode="json"),
                "product_first_appearance_end_milliseconds": 7_000,
            }
        )


def test_domain_policy_rejects_profile_requirement_drift() -> None:
    profile, _ = _profile_and_policy()
    with pytest.raises(ValidationError, match="coverage"):
        DomainAcceptancePolicy(
            domain_id="ecommerce",
            profile_id=profile.profile_id,
            profile_version=profile.profile_version,
            profile_content_hash=profile.content_hash,
            profile_payload=profile.model_dump(mode="json"),
            measurement_contract_version="ecommerce-media-acceptance/1",
            required_requirement_ids=profile.required_requirement_ids[:-1],
        )


@pytest.mark.parametrize("coverage_mutation", ["missing", "extra", "reordered", "duplicate"])
def test_ecommerce_evidence_requires_exact_ordered_coverage(
    coverage_mutation: str,
) -> None:
    profile, policy = _profile_and_policy()
    requirement_ids = profile.required_requirement_ids
    if coverage_mutation == "missing":
        requirement_ids = requirement_ids[:-1]
    elif coverage_mutation == "extra":
        requirement_ids = (*requirement_ids, "ad.unselected")
    elif coverage_mutation == "reordered":
        requirement_ids = (requirement_ids[1], requirement_ids[0], *requirement_ids[2:])
    else:
        requirement_ids = (*requirement_ids, requirement_ids[-1])
    _, _, adjudicate, _ = _api()

    assert adjudicate(policy, _payload(requirement_ids=requirement_ids)) is QaVerdict.NOT_EVALUATED


@pytest.mark.parametrize(
    ("verdicts", "expected"),
    [
        ((QaVerdict.PASS,), QaVerdict.PASS),
        ((QaVerdict.FAIL,), QaVerdict.FAIL),
        ((QaVerdict.NOT_EVALUATED,), QaVerdict.NOT_EVALUATED),
    ],
)
def test_ecommerce_required_findings_aggregate_fail_closed(
    verdicts: tuple[QaVerdict, ...], expected: QaVerdict
) -> None:
    profile, policy = _profile_and_policy()
    expanded = tuple(QaVerdict.PASS for _ in profile.required_requirement_ids)
    expanded = (verdicts[0], *expanded[1:])
    _, _, adjudicate, _ = _api()

    assert adjudicate(policy, _payload(verdicts=expanded)) is expected


def test_ecommerce_evidence_with_wrong_profile_hash_is_not_evaluated() -> None:
    _, policy = _profile_and_policy()
    payload = _payload().model_copy(update={"profile_content_hash": "f" * 64})
    _, _, adjudicate, _ = _api()

    assert adjudicate(policy, payload) is QaVerdict.NOT_EVALUATED


def _shot_binding() -> GeneratedCommercialShotBinding:
    return GeneratedCommercialShotBinding.create(
        ad_creative_plan_id="qingyan-ad-plan",
        ad_creative_plan_hash="1" * 64,
        commercial_execution_projection_hash="2" * 64,
        target_shot_id="shot-03",
        profile_content_hash="3" * 64,
        applicable_requirement_ids=(
            "shot.identity.main_character",
            "shot.product.interaction",
            "shot.motion.required",
        ),
        product_truth_hashes=("4" * 64,),
        product_reference_hashes=("5" * 64,),
        source_approval_hashes=("6" * 64,),
        expected_actor_ids=("qingyan-miao-girl", "qingyan-elder"),
        output_asset_id="generated-shot-03",
    )


def _shot_evidence(*, verdict: QaVerdict = QaVerdict.PASS):
    from ai_video.production.ecommerce_media_acceptance import (
        CommercialShotEvaluationIntent,
        EcommerceRequirementFinding,
        GeneratedCommercialShotEvidence,
    )

    binding = _shot_binding()
    evaluator = ToolIdentity(name="commercial-shot-evaluator", version="1")
    intent = CommercialShotEvaluationIntent.create(
        binding=binding,
        resolved_generation_hash="7" * 64,
        artifact_sha256="8" * 64,
        measured_metadata_hash="9" * 64,
        qa_policy_content_hash="a" * 64,
        evaluator=evaluator,
        evaluator_profile_content_hash="b" * 64,
    )
    evidence = GeneratedCommercialShotEvidence.create(
        intent=intent,
        strength=EvidenceStrength.EXPLICIT_EVALUATOR,
        findings=tuple(
            EcommerceRequirementFinding(
                requirement_id=requirement_id,
                verdict=verdict if index == 0 else QaVerdict.PASS,
                rationale=f"observed {requirement_id}",
            )
            for index, requirement_id in enumerate(
                binding.applicable_requirement_ids
            )
        ),
    )
    return binding, intent, evidence


@pytest.mark.parametrize(
    ("finding_verdict", "expected"),
    [
        (QaVerdict.PASS, QaVerdict.PASS),
        (QaVerdict.FAIL, QaVerdict.FAIL),
        (QaVerdict.NOT_EVALUATED, QaVerdict.NOT_EVALUATED),
    ],
)
def test_generated_commercial_shot_evidence_aggregates_exact_requirements(
    finding_verdict: QaVerdict,
    expected: QaVerdict,
) -> None:
    from ai_video.production.ecommerce_media_acceptance import (
        adjudicate_generated_commercial_shot_evidence,
    )

    binding, _, evidence = _shot_evidence(verdict=finding_verdict)
    assert adjudicate_generated_commercial_shot_evidence(
        evidence,
        binding=binding,
    ) is expected


def test_generated_commercial_shot_evidence_rejects_drift_and_partial_coverage() -> None:
    from ai_video.production.ecommerce_media_acceptance import (
        GeneratedCommercialShotEvidence,
        adjudicate_generated_commercial_shot_evidence,
    )

    binding, intent, evidence = _shot_evidence()
    partial = GeneratedCommercialShotEvidence.create(
        intent=intent,
        strength=EvidenceStrength.EXPLICIT_EVALUATOR,
        findings=evidence.findings[:-1],
    )
    assert adjudicate_generated_commercial_shot_evidence(
        partial,
        binding=binding,
    ) is QaVerdict.NOT_EVALUATED

    changed_binding = GeneratedCommercialShotBinding.create(
        **{
            **binding.model_dump(mode="python", exclude={"content_hash"}),
            "profile_content_hash": "f" * 64,
        }
    )
    assert adjudicate_generated_commercial_shot_evidence(
        evidence,
        binding=changed_binding,
    ) is QaVerdict.NOT_EVALUATED
