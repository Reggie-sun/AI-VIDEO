from __future__ import annotations

import pytest

import ai_video.production as production
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    QaLayoutRules,
    QaLayer,
    QaPolicy,
    QaTechnicalThresholds,
    SourceReference,
    ToolIdentity,
)


REVIEW_TOOL = ToolIdentity(name="commercial-human-reviewer", version="1")


def _policy(*, authority: ToolIdentity = REVIEW_TOOL) -> QaPolicy:
    return seal_artifact(
        QaPolicy(
            artifact_id="commercial-source-policy",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id="commercial-source-policy",
            source_provenance=(
                SourceReference(kind="derived", reference="offline-commercial-policy"),
            ),
            policy_id="commercial-source-policy",
            policy_version="1",
            required_layers=(QaLayer.SEMANTIC,),
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
            semantic_requirement="required",
            semantic_authorities=(authority,),
        )
    )


REQUIRED_DIMENSION_NAMES = (
    "CHARACTER_IDENTITY",
    "HAIRSTYLE",
    "WARDROBE",
    "ACCESSORY",
    "PRODUCT_PRESENCE",
    "PACKAGING_IDENTITY",
    "BOTTLE_SILHOUETTE",
    "DOMINANT_COLOR",
    "CAP_COLOR",
    "LOGO_LABEL_IDENTITY",
    "LABEL_TEXT_ZONE_INTEGRITY",
    "PRODUCT_SCALE",
    "PERSPECTIVE_MATCH",
    "LIGHTING_MATCH",
    "HAND_OBJECT_CONTACT",
    "OCCLUSION_PLAUSIBILITY",
    "INTERACTION_PLAUSIBILITY",
    "FLAT_OVERLAY_ABSENT",
)


def _evidence(
    *,
    changed_dimension: production.CommercialVisualDimension | None = None,
    changed_status: str = "match",
) -> production.CommercialVisualEvidence:
    dimensions = tuple(
        getattr(production.CommercialVisualDimension, name)
        for name in REQUIRED_DIMENSION_NAMES
    )
    measurements = tuple(
        production.CommercialVisualMeasurement(
            dimension=dimension,
            status=(changed_status if dimension is changed_dimension else "match"),
            expected=f"expected-{dimension.value}",
            observed=f"observed-{dimension.value}",
            confidence_milli=950,
            rationale="human exact-bound observation",
        )
        for dimension in dimensions
    )
    return production.CommercialVisualEvidence.create(
        evidence_id="commercial-evidence-1",
        source_request_hash="1" * 64,
        target_shot_id="shot-04",
        target_shot_content_hash="2" * 64,
        candidate_asset_id="interaction-keyframe-04",
        candidate_sha256="3" * 64,
        product_reference_set_hash="4" * 64,
        policy_hash=_policy().content_hash,
        authority_kind="human",
        tool_identity=REVIEW_TOOL,
        measurements=measurements,
    )


def test_exact_human_commercial_visual_evidence_can_pass_source_review() -> None:
    receipt = production.adjudicate_commercial_visual_evidence(
        _evidence(),
        policy=_policy(),
    )

    assert receipt.verdict is production.QaVerdict.PASS
    assert receipt.target_kind == "source_image"


@pytest.mark.parametrize("dimension_name", REQUIRED_DIMENSION_NAMES)
def test_each_required_commercial_mismatch_fails_source_review(
    dimension_name: str,
) -> None:
    dimension = getattr(production.CommercialVisualDimension, dimension_name)
    receipt = production.adjudicate_commercial_visual_evidence(
        _evidence(
            changed_dimension=dimension,
            changed_status=production.CommercialMatchStatus.MISMATCH,
        ),
        policy=_policy(),
    )

    assert receipt.verdict is production.QaVerdict.FAIL
    assert receipt.failure_classification is not None


def test_not_evaluated_and_unselected_authority_never_become_pass() -> None:
    not_evaluated = production.adjudicate_commercial_visual_evidence(
        _evidence(
            changed_dimension=production.CommercialVisualDimension.LOGO_LABEL_IDENTITY,
            changed_status=production.CommercialMatchStatus.NOT_EVALUATED,
        ),
        policy=_policy(),
    )
    wrong_authority = production.adjudicate_commercial_visual_evidence(
        _evidence(),
        policy=_policy(
            authority=ToolIdentity(name="different-reviewer", version="1")
        ),
    )

    assert not_evaluated.verdict is production.QaVerdict.NOT_EVALUATED
    assert wrong_authority.verdict is production.QaVerdict.NOT_EVALUATED
