from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.composition_contracts import DeliveryProfile
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    QaVerdict,
    SourceReference,
)

ZERO_HASH = "0" * 64


def _gate_api() -> tuple[object, ...]:
    from ai_video.production.quality_gate_coordinator import (
        UniversalHardCheck,
        UniversalQaApplicability,
        UniversalQaBlockReason,
        UniversalQaCheckOutcome,
        UniversalQaContext,
        UniversalQaProfile,
        UniversalQualityGateCoordinator,
    )

    return (
        UniversalHardCheck,
        UniversalQaApplicability,
        UniversalQaBlockReason,
        UniversalQaCheckOutcome,
        UniversalQaContext,
        UniversalQaProfile,
        UniversalQualityGateCoordinator,
    )


def _policy(*, required_layers: tuple[QaLayer, ...]) -> QaPolicy:
    return seal_artifact(
        QaPolicy(
            artifact_id="qa-policy-universal-gate",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="qa-policy-universal-gate",
            source_provenance=(
                SourceReference(kind="derived", reference="universal-gate-test"),
            ),
            policy_id="universal-gate-policy",
            policy_version="1",
            required_layers=required_layers,
            technical_thresholds=QaTechnicalThresholds(
                black_luma_max_milli=10,
                silence_peak_max_millidb=-60_000,
                clipping_peak_min_millidb=-100,
            ),
            layout_rules=QaLayoutRules(
                safe_area_inset_milli=50,
                caption_overflow_tolerance_milli=0,
            ),
            strategy_rules_version="1",
            semantic_requirement="optional",
        )
    )


def _fixture(
    *,
    layout_applicable: bool = False,
    continuity_applicable: bool = False,
    policy_layers: tuple[QaLayer, ...] = (QaLayer.TECHNICAL,),
) -> tuple[object, object, QaPolicy, tuple[object, ...]]:
    (
        UniversalHardCheck,
        UniversalQaApplicability,
        _,
        _,
        UniversalQaContext,
        UniversalQaProfile,
        _,
    ) = _gate_api()
    applicability = UniversalQaApplicability(
        has_audio=True,
        has_captions=False,
        has_graphics=layout_applicable,
        has_safe_area_requirements=layout_applicable,
        has_transitions=layout_applicable,
        requires_continuity=continuity_applicable,
    )
    hard_checks = (
        UniversalHardCheck.ASSET_PROVENANCE,
        UniversalHardCheck.MEDIA_DECODE,
        UniversalHardCheck.TIMELINE_BINDING,
        UniversalHardCheck.RENDER_OUTPUT,
        UniversalHardCheck.AUDIO_CAPTION_BINDING,
    ) + (
        (UniversalHardCheck.CONTINUITY_EVIDENCE,)
        if continuity_applicable
        else ()
    )
    required_layers = (QaLayer.TECHNICAL,) + (
        (QaLayer.LAYOUT,) if layout_applicable else ()
    )
    delivery_profile = DeliveryProfile(width=1080, height=1920, fps=24)
    profile = UniversalQaProfile.create(
        profile_id="vertical-universal",
        profile_version="1",
        delivery_profile=delivery_profile,
        applicability=applicability,
        required_hard_checks=hard_checks,
        required_review_layers=required_layers,
        continuity_requirement_ids=("continuity.identity",)
        if continuity_applicable
        else (),
    )
    policy = _policy(required_layers=policy_layers)
    context = UniversalQaContext(
        delivery_profile=delivery_profile,
        applicability=applicability,
        project_content_hash="1" * 64,
        registry_content_hash="2" * 64,
        dependency_graph_revision_id="3" * 64,
        render_state_content_hash="4" * 64,
        render_output_sha256="5" * 64,
        timeline_fingerprint="6" * 64,
        qa_policy_content_hash=policy.content_hash,
    )
    return profile, context, policy, hard_checks


def test_universal_profile_is_content_addressed_and_rejects_tampering() -> None:
    _, _, _, _, _, UniversalQaProfile, _ = _gate_api()
    profile, _, _, _ = _fixture()

    with pytest.raises(ValidationError, match="content hash"):
        UniversalQaProfile.model_validate(
            {**profile.model_dump(mode="json"), "profile_version": "tampered"}
        )


def test_historical_universal_profile_reopens_without_version_or_hash_drift() -> None:
    (
        UniversalHardCheck,
        UniversalQaApplicability,
        _,
        _,
        _,
        UniversalQaProfile,
        _,
    ) = _gate_api()
    historical = {
        "profile_id": "historical-profile",
        "profile_version": "1",
        "delivery_profile": DeliveryProfile(
            width=1080, height=1920, fps=24
        ).model_dump(mode="json"),
        "applicability": UniversalQaApplicability().model_dump(mode="json"),
        "required_hard_checks": [
            UniversalHardCheck.ASSET_PROVENANCE.value,
            UniversalHardCheck.MEDIA_DECODE.value,
            UniversalHardCheck.TIMELINE_BINDING.value,
            UniversalHardCheck.RENDER_OUTPUT.value,
        ],
        "required_review_layers": [QaLayer.TECHNICAL.value],
        "continuity_requirement_ids": [],
    }
    historical["content_hash"] = canonical_sha256(
        {"schema": "universal-qa-profile/1", **historical}
    )

    reopened = UniversalQaProfile.model_validate(historical)

    assert reopened.profile_contract_version == 1
    assert reopened.model_dump(mode="json") == historical


def test_new_caption_profile_requires_caption_layer() -> None:
    (
        UniversalHardCheck,
        UniversalQaApplicability,
        _,
        _,
        _,
        UniversalQaProfile,
        _,
    ) = _gate_api()

    with pytest.raises(ValidationError, match="caption review layer"):
        UniversalQaProfile.create(
            profile_id="caption-v2",
            profile_version="2",
            delivery_profile=DeliveryProfile(width=1080, height=1920, fps=24),
            applicability=UniversalQaApplicability(has_captions=True),
            required_hard_checks=(
                UniversalHardCheck.ASSET_PROVENANCE,
                UniversalHardCheck.MEDIA_DECODE,
                UniversalHardCheck.TIMELINE_BINDING,
                UniversalHardCheck.RENDER_OUTPUT,
                UniversalHardCheck.AUDIO_CAPTION_BINDING,
            ),
            required_review_layers=(QaLayer.TECHNICAL, QaLayer.LAYOUT),
        )


@pytest.mark.parametrize(
    ("case", "message"),
    (
        ("missing_baseline", "always-required hard check"),
        ("missing_technical", "technical review layer"),
        ("final_acceptance", "not a Universal QA review layer"),
        ("missing_audio_caption", "audio/caption hard check"),
        ("missing_layout", "layout requirements"),
        ("missing_continuity", "continuity evidence"),
        ("blank_continuity_id", "requirement IDs must be nonblank"),
        ("duplicate_hard_check", "hard checks must be unique"),
    ),
)
def test_universal_profile_rejects_incomplete_or_duplicated_minimums(
    case: str,
    message: str,
) -> None:
    (
        UniversalHardCheck,
        UniversalQaApplicability,
        _,
        _,
        _,
        UniversalQaProfile,
        _,
    ) = _gate_api()
    hard_checks = (
        UniversalHardCheck.ASSET_PROVENANCE,
        UniversalHardCheck.MEDIA_DECODE,
        UniversalHardCheck.TIMELINE_BINDING,
        UniversalHardCheck.RENDER_OUTPUT,
    )
    applicability = UniversalQaApplicability()
    review_layers = (QaLayer.TECHNICAL,)
    continuity_requirement_ids: tuple[str, ...] = ()
    if case == "missing_baseline":
        hard_checks = hard_checks[:-1]
    elif case == "missing_technical":
        review_layers = (QaLayer.LAYOUT,)
    elif case == "final_acceptance":
        review_layers = (QaLayer.TECHNICAL, QaLayer.FINAL_ACCEPTANCE)
    elif case == "missing_audio_caption":
        applicability = UniversalQaApplicability(has_audio=True)
    elif case == "missing_layout":
        applicability = UniversalQaApplicability(has_captions=True)
        hard_checks += (UniversalHardCheck.AUDIO_CAPTION_BINDING,)
    elif case == "missing_continuity":
        applicability = UniversalQaApplicability(requires_continuity=True)
        continuity_requirement_ids = ("continuity.identity",)
    elif case == "blank_continuity_id":
        applicability = UniversalQaApplicability(requires_continuity=True)
        hard_checks += (UniversalHardCheck.CONTINUITY_EVIDENCE,)
        continuity_requirement_ids = ("",)
    elif case == "duplicate_hard_check":
        hard_checks += (UniversalHardCheck.ASSET_PROVENANCE,)

    with pytest.raises(ValidationError, match=message):
        UniversalQaProfile.create(
            profile_id="invalid-universal-profile",
            profile_version="1",
            delivery_profile=DeliveryProfile(width=1080, height=1920, fps=24),
            applicability=applicability,
            required_hard_checks=hard_checks,
            required_review_layers=review_layers,
            continuity_requirement_ids=continuity_requirement_ids,
        )


def test_model_copy_tampering_is_revalidated_before_any_gate_effect() -> None:
    (
        UniversalHardCheck,
        _,
        UniversalQaBlockReason,
        UniversalQaCheckOutcome,
        _,
        _,
        UniversalQualityGateCoordinator,
    ) = _gate_api()
    profile, context, policy, _ = _fixture()
    tampered_profile = profile.model_copy(
        update={
            "required_hard_checks": (UniversalHardCheck.ASSET_PROVENANCE,),
            "required_review_layers": (),
        }
    )
    calls: list[str] = []

    result = UniversalQualityGateCoordinator().run_once(
        profile=tampered_profile,
        context=context,
        policy=policy,
        run_hard_check=lambda check, *_: (
            calls.append(check.value)
            or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
        ),
        run_review_layer=lambda layer, *_: (
            calls.append(layer.value)
            or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
        ),
    )

    assert result.verdict is QaVerdict.NOT_EVALUATED
    assert result.block_reason is UniversalQaBlockReason.PROFILE_INVALID
    assert calls == []


def test_invalid_declared_profile_hash_returns_not_evaluated() -> None:
    (
        _,
        _,
        UniversalQaBlockReason,
        UniversalQaCheckOutcome,
        _,
        _,
        UniversalQualityGateCoordinator,
    ) = _gate_api()
    profile, context, policy, _ = _fixture()
    tampered_profile = profile.model_copy(update={"content_hash": "not-a-sha256"})
    calls: list[str] = []

    result = UniversalQualityGateCoordinator().run_once(
        profile=tampered_profile,
        context=context,
        policy=policy,
        run_hard_check=lambda check, *_: (
            calls.append(check.value)
            or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
        ),
        run_review_layer=lambda layer, *_: (
            calls.append(layer.value)
            or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
        ),
    )

    assert result.verdict is QaVerdict.NOT_EVALUATED
    assert result.block_reason is UniversalQaBlockReason.PROFILE_INVALID
    assert result.profile_content_hash is None
    assert calls == []


def test_context_model_copy_tampering_is_revalidated_before_any_gate_effect() -> None:
    (
        _,
        _,
        UniversalQaBlockReason,
        UniversalQaCheckOutcome,
        _,
        _,
        UniversalQualityGateCoordinator,
    ) = _gate_api()
    profile, context, policy, _ = _fixture()
    tampered_context = context.model_copy(
        update={"render_output_sha256": "not-a-sha256"}
    )
    calls: list[str] = []

    result = UniversalQualityGateCoordinator().run_once(
        profile=profile,
        context=tampered_context,
        policy=policy,
        run_hard_check=lambda check, *_: (
            calls.append(check.value)
            or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
        ),
        run_review_layer=lambda layer, *_: (
            calls.append(layer.value)
            or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
        ),
    )

    assert result.verdict is QaVerdict.NOT_EVALUATED
    assert result.block_reason is UniversalQaBlockReason.CONTEXT_INVALID
    assert calls == []


def test_policy_coverage_blocks_before_any_gate_effect() -> None:
    (
        _,
        _,
        UniversalQaBlockReason,
        _,
        _,
        _,
        UniversalQualityGateCoordinator,
    ) = _gate_api()
    profile, context, policy, _ = _fixture(
        layout_applicable=True,
        policy_layers=(QaLayer.TECHNICAL,),
    )
    calls: list[str] = []

    result = UniversalQualityGateCoordinator().run_once(
        profile=profile,
        context=context,
        policy=policy,
        run_hard_check=lambda check, *_: calls.append(check.value),
        run_review_layer=lambda layer, *_: calls.append(layer.value),
    )

    assert result.verdict is QaVerdict.NOT_EVALUATED
    assert result.block_reason is UniversalQaBlockReason.QA_POLICY_COVERAGE_INCOMPLETE
    assert result.blocked_identifiers == (QaLayer.LAYOUT.value,)
    assert calls == []
    assert result.eligible_for_domain_gate is False
    assert result.eligible_for_final_acceptance is False


def test_caption_profile_requires_caption_policy_before_any_gate_effect() -> None:
    (
        UniversalHardCheck,
        UniversalQaApplicability,
        UniversalQaBlockReason,
        _,
        UniversalQaContext,
        UniversalQaProfile,
        UniversalQualityGateCoordinator,
    ) = _gate_api()
    applicability = UniversalQaApplicability(has_audio=True, has_captions=True)
    profile = UniversalQaProfile.create(
        profile_id="caption-v2",
        profile_version="2",
        delivery_profile=DeliveryProfile(width=1080, height=1920, fps=24),
        applicability=applicability,
        required_hard_checks=(
            UniversalHardCheck.ASSET_PROVENANCE,
            UniversalHardCheck.MEDIA_DECODE,
            UniversalHardCheck.TIMELINE_BINDING,
            UniversalHardCheck.RENDER_OUTPUT,
            UniversalHardCheck.AUDIO_CAPTION_BINDING,
        ),
        required_review_layers=(
            QaLayer.TECHNICAL,
            QaLayer.LAYOUT,
            QaLayer.CAPTION,
        ),
    )
    policy = _policy(required_layers=(QaLayer.TECHNICAL, QaLayer.LAYOUT))
    context = UniversalQaContext(
        delivery_profile=profile.delivery_profile,
        applicability=applicability,
        project_content_hash="1" * 64,
        registry_content_hash="2" * 64,
        dependency_graph_revision_id="3" * 64,
        render_state_content_hash="4" * 64,
        render_output_sha256="5" * 64,
        timeline_fingerprint="6" * 64,
        qa_policy_content_hash=policy.content_hash,
    )
    calls: list[str] = []

    result = UniversalQualityGateCoordinator().run_once(
        profile=profile,
        context=context,
        policy=policy,
        run_hard_check=lambda check, *_: calls.append(check.value),
        run_review_layer=lambda layer, *_: calls.append(layer.value),
    )

    assert result.verdict is QaVerdict.NOT_EVALUATED
    assert result.block_reason is UniversalQaBlockReason.QA_POLICY_COVERAGE_INCOMPLETE
    assert result.blocked_identifiers == ("caption_policy", QaLayer.CAPTION.value)
    assert calls == []


def test_unsealed_policy_is_rejected_even_when_context_repeats_its_hash() -> None:
    (
        _,
        _,
        UniversalQaBlockReason,
        UniversalQaCheckOutcome,
        _,
        _,
        UniversalQualityGateCoordinator,
    ) = _gate_api()
    profile, context, policy, _ = _fixture()
    unsealed_policy = policy.model_copy(update={"content_hash": ZERO_HASH})
    matching_unsealed_context = context.model_copy(
        update={"qa_policy_content_hash": ZERO_HASH}
    )
    calls: list[str] = []

    result = UniversalQualityGateCoordinator().run_once(
        profile=profile,
        context=matching_unsealed_context,
        policy=unsealed_policy,
        run_hard_check=lambda check, *_: (
            calls.append(check.value)
            or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
        ),
        run_review_layer=lambda layer, *_: (
            calls.append(layer.value)
            or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
        ),
    )

    assert result.verdict is QaVerdict.NOT_EVALUATED
    assert result.block_reason is UniversalQaBlockReason.QA_POLICY_INVALID
    assert calls == []


def test_policy_mismatch_result_binds_selected_policy_identity() -> None:
    (
        _,
        _,
        UniversalQaBlockReason,
        UniversalQaCheckOutcome,
        _,
        _,
        UniversalQualityGateCoordinator,
    ) = _gate_api()
    profile, context, _, _ = _fixture()
    selected_policy = _policy(required_layers=(QaLayer.TECHNICAL,)).model_copy(
        update={"policy_version": "2", "content_hash": ZERO_HASH}
    )
    selected_policy = seal_artifact(selected_policy)
    calls: list[str] = []

    result = UniversalQualityGateCoordinator().run_once(
        profile=profile,
        context=context,
        policy=selected_policy,
        run_hard_check=lambda check, *_: (
            calls.append(check.value)
            or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
        ),
        run_review_layer=lambda layer, *_: (
            calls.append(layer.value)
            or UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)
        ),
    )

    assert result.verdict is QaVerdict.NOT_EVALUATED
    assert result.block_reason is UniversalQaBlockReason.QA_POLICY_NOT_CURRENT
    assert result.qa_policy_content_hash == selected_policy.content_hash
    assert result.expected_qa_policy_content_hash == context.qa_policy_content_hash
    assert result.qa_policy_content_hash != context.qa_policy_content_hash
    assert calls == []


def test_profile_context_mismatch_blocks_before_any_gate_effect() -> None:
    (
        _,
        UniversalQaApplicability,
        UniversalQaBlockReason,
        _,
        _,
        _,
        UniversalQualityGateCoordinator,
    ) = _gate_api()
    profile, context, policy, _ = _fixture()
    changed_context = context.model_copy(
        update={
            "applicability": UniversalQaApplicability(
                has_audio=True,
                has_captions=True,
                has_graphics=False,
                has_safe_area_requirements=True,
                has_transitions=False,
                requires_continuity=False,
            )
        }
    )
    calls: list[str] = []

    result = UniversalQualityGateCoordinator().run_once(
        profile=profile,
        context=changed_context,
        policy=policy,
        run_hard_check=lambda check, *_: calls.append(check.value),
        run_review_layer=lambda layer, *_: calls.append(layer.value),
    )

    assert result.verdict is QaVerdict.NOT_EVALUATED
    assert result.block_reason is UniversalQaBlockReason.PROFILE_CONTEXT_MISMATCH
    assert calls == []


def test_gate_one_runs_required_checks_in_order_and_never_final_accepts() -> None:
    (
        _,
        _,
        _,
        UniversalQaCheckOutcome,
        _,
        _,
        UniversalQualityGateCoordinator,
    ) = _gate_api()
    profile, context, policy, hard_checks = _fixture(
        layout_applicable=True,
        continuity_applicable=True,
        policy_layers=(QaLayer.TECHNICAL, QaLayer.LAYOUT, QaLayer.SEMANTIC),
    )
    calls: list[str] = []

    def pass_hard(check: object, *_: object) -> object:
        calls.append(f"hard:{check.value}")
        return UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)

    def pass_review(layer: QaLayer, *_: object) -> object:
        calls.append(f"review:{layer.value}")
        return UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)

    result = UniversalQualityGateCoordinator().run_once(
        profile=profile,
        context=context,
        policy=policy,
        run_hard_check=pass_hard,
        run_review_layer=pass_review,
    )

    assert calls == [
        *(f"hard:{check.value}" for check in hard_checks),
        "review:technical",
        "review:layout",
    ]
    assert result.verdict is QaVerdict.PASS
    assert result.eligible_for_domain_gate is True
    assert result.eligible_for_final_acceptance is False
    assert result.profile_content_hash == profile.content_hash
    assert result.context_content_hash == canonical_sha256(
        {
            "schema": "universal-qa-context/1",
            **context.model_dump(mode="json"),
        }
    )
    assert result.qa_policy_content_hash == policy.content_hash
    assert result.completed_hard_checks == hard_checks
    assert result.completed_review_layers == (QaLayer.TECHNICAL, QaLayer.LAYOUT)


def test_domain_eligibility_requires_complete_consistent_identity() -> None:
    from ai_video.production.quality_gate_coordinator import UniversalQaGateResult

    with pytest.raises(ValidationError, match="complete consistent identity"):
        UniversalQaGateResult(
            verdict=QaVerdict.PASS,
            context_content_hash="1" * 64,
            eligible_for_domain_gate=True,
        )


def test_provider_native_claims_are_absent_from_gate_and_acceptance_models() -> None:
    from ai_video.production.ecommerce_quality_gate import (
        EcommerceGateResult,
        EcommerceWholeAdAcceptanceTarget,
    )
    from ai_video.production.models import FinalAcceptanceReceipt
    from ai_video.production.quality_gate_coordinator import (
        UniversalQaContext,
        UniversalQaGateResult,
        UniversalQaProfile,
    )

    forbidden = {
        "provider_name",
        "provider_kind",
        "provider_status",
        "provider_file_id",
        "model_id",
        "seed",
        "scheduler",
        "workflow_hash",
        "output_url",
    }

    for model in (
        UniversalQaProfile,
        UniversalQaContext,
        UniversalQaGateResult,
        EcommerceWholeAdAcceptanceTarget,
        EcommerceGateResult,
        FinalAcceptanceReceipt,
    ):
        assert forbidden.isdisjoint(model.model_fields)


def test_continuity_runner_receives_exact_profile_requirement_ids() -> None:
    (
        UniversalHardCheck,
        _,
        _,
        UniversalQaCheckOutcome,
        _,
        _,
        UniversalQualityGateCoordinator,
    ) = _gate_api()
    profile, context, policy, _ = _fixture(
        continuity_applicable=True,
        policy_layers=(QaLayer.TECHNICAL,),
    )
    observed_requirement_ids: list[tuple[str, ...]] = []

    def run_hard(check: object, _: object, selected_profile: object) -> object:
        if check is UniversalHardCheck.CONTINUITY_EVIDENCE:
            observed_requirement_ids.append(
                selected_profile.continuity_requirement_ids
            )
        return UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)

    result = UniversalQualityGateCoordinator().run_once(
        profile=profile,
        context=context,
        policy=policy,
        run_hard_check=run_hard,
        run_review_layer=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS,
            current=True,
        ),
    )

    assert result.verdict is QaVerdict.PASS
    assert observed_requirement_ids == [("continuity.identity",)]


def test_hard_failure_stops_before_review_layers() -> None:
    (
        UniversalHardCheck,
        _,
        UniversalQaBlockReason,
        UniversalQaCheckOutcome,
        _,
        _,
        UniversalQualityGateCoordinator,
    ) = _gate_api()
    profile, context, policy, _ = _fixture()
    calls: list[str] = []

    def run_hard(check: object, *_: object) -> object:
        calls.append(check.value)
        return UniversalQaCheckOutcome(
            verdict=(
                QaVerdict.FAIL
                if check is UniversalHardCheck.MEDIA_DECODE
                else QaVerdict.PASS
            ),
            current=True,
        )

    result = UniversalQualityGateCoordinator().run_once(
        profile=profile,
        context=context,
        policy=policy,
        run_hard_check=run_hard,
        run_review_layer=lambda layer, *_: pytest.fail(
            f"review layer ran after hard failure: {layer}"
        ),
    )

    assert calls == ["asset_provenance", "media_decode"]
    assert result.verdict is QaVerdict.FAIL
    assert result.block_reason is UniversalQaBlockReason.HARD_CHECK_BLOCKED
    assert result.blocked_identifiers == (UniversalHardCheck.MEDIA_DECODE.value,)
    assert result.eligible_for_domain_gate is False


def test_stale_review_result_fails_closed_and_stops_remaining_layers() -> None:
    (
        _,
        _,
        UniversalQaBlockReason,
        UniversalQaCheckOutcome,
        _,
        _,
        UniversalQualityGateCoordinator,
    ) = _gate_api()
    profile, context, policy, _ = _fixture(
        layout_applicable=True,
        policy_layers=(QaLayer.TECHNICAL, QaLayer.LAYOUT),
    )
    review_calls: list[QaLayer] = []

    def run_review(layer: QaLayer, *_: object) -> object:
        review_calls.append(layer)
        return UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=False)

    result = UniversalQualityGateCoordinator().run_once(
        profile=profile,
        context=context,
        policy=policy,
        run_hard_check=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS,
            current=True,
        ),
        run_review_layer=run_review,
    )

    assert review_calls == [QaLayer.TECHNICAL]
    assert result.verdict is QaVerdict.NOT_EVALUATED
    assert result.block_reason is UniversalQaBlockReason.REVIEW_LAYER_NOT_CURRENT
    assert result.blocked_identifiers == (QaLayer.TECHNICAL.value,)
    assert result.eligible_for_domain_gate is False


@pytest.mark.parametrize("unknown_stage", ("hard", "review"))
def test_unknown_check_outcome_fails_closed_without_retry(unknown_stage: str) -> None:
    (
        _,
        _,
        UniversalQaBlockReason,
        UniversalQaCheckOutcome,
        _,
        _,
        UniversalQualityGateCoordinator,
    ) = _gate_api()
    profile, context, policy, _ = _fixture()
    attempts = {"hard": 0, "review": 0}

    def run_hard(*_: object) -> object:
        attempts["hard"] += 1
        if unknown_stage == "hard":
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
                user_message="hard check outcome is unknown",
            )
        return UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)

    def run_review(*_: object) -> object:
        attempts["review"] += 1
        if unknown_stage == "review":
            raise AiVideoError(
                code=ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
                user_message="review layer outcome is unknown",
            )
        return UniversalQaCheckOutcome(verdict=QaVerdict.PASS, current=True)

    result = UniversalQualityGateCoordinator().run_once(
        profile=profile,
        context=context,
        policy=policy,
        run_hard_check=run_hard,
        run_review_layer=run_review,
    )

    assert result.verdict is QaVerdict.NOT_EVALUATED
    assert result.block_reason is (
        UniversalQaBlockReason.HARD_CHECK_OUTCOME_UNKNOWN
        if unknown_stage == "hard"
        else UniversalQaBlockReason.REVIEW_LAYER_OUTCOME_UNKNOWN
    )
    assert attempts[unknown_stage] == 1
