from __future__ import annotations

import pytest

import ai_video.production as production

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AudioKind,
    AudioTrackSpec,
    CompositionLayerSpec,
    SourceReference,
)
from production_project_factory import make_composition_spec


def _make_plan(**changes: object) -> production.AdCreativePlan:
    plan = production.AdCreativePlan(
        schema_version="ad-creative-plan/1",
        artifact_id="ad-plan-qingyan",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="approve-ad-plan-qingyan",
        source_provenance=(
            SourceReference(kind="derived", reference="ecommerce-package-qingyan"),
        ),
        creative_concept="腋下尴尬退场，清爽随身",
        product_truth_source_ids=("source-packaging-front",),
        claim_reference_ids=("claim-net-odor",),
        source_generation_evidence=(),
        protagonist_continuity_policy=production.ProtagonistContinuityPolicy(
            mode=production.ProtagonistContinuityMode.SINGLE_PROTAGONIST,
            protagonist_ids=("talent-adult-1",),
            allowed_variations=("wardrobe",),
        ),
        ad_arc=(
            production.AdBeatPlan(
                beat_id="beat-hook",
                role=production.AdBeatRole.PROBLEM,
                shot_ids=("shot-1",),
            ),
            production.AdBeatPlan(
                beat_id="beat-hero",
                role=production.AdBeatRole.HERO,
                shot_ids=("shot-2",),
            ),
            production.AdBeatPlan(
                beat_id="beat-close",
                role=production.AdBeatRole.BRAND_CLOSURE,
                shot_ids=("shot-2",),
            ),
        ),
        product_presentations=(
            production.ProductPresentation(
                presentation_id="product-hero",
                role=production.ProductPresentationRole.HERO_SHOT,
                mode=production.ProductPresentationMode.HERO_ASSET,
                beat_id="beat-hero",
                shot_id="shot-2",
                asset_id="product-packshot",
                composition_layer_id="layer-product-packshot",
                product_truth_reference_ids=("source-packaging-front",),
                transform_intent=production.ProductTransformIntent(),
                entrance=production.GraphicAnimation.SCALE_IN,
                exit=production.GraphicAnimation.FADE,
                graphic_treatment_ids=("brand-close",),
                sound_cue_ids=("music-bed",),
                capability_classification=production.CapabilityClassification.SUPPORTED_CURRENTLY,
            ),
        ),
        graphic_treatments=(
            production.GraphicTreatment(
                graphic_id="headline-hook",
                role=production.GraphicRole.HEADLINE,
                text="尴尬气味？",
                shot_id="shot-1",
                start_frame_offset=0,
                duration_frames=36,
                x_milli=80,
                y_milli=120,
                width_milli=840,
                font_size_px=64,
                text_color="#171717",
                background_color="#F7D000E6",
                claim_reference_ids=("claim-net-odor",),
                safe_area=production.GraphicSafeAreaInsets(
                    top_milli=40,
                    right_milli=40,
                    bottom_milli=40,
                    left_milli=40,
                ),
                avoidance_target_ids=("talent-adult-1",),
                keyword_emphasis=(
                    production.GraphicKeywordEmphasis(
                        text="气味",
                        brand_token_id="brand-accent-yellow",
                    ),
                ),
                brand_token_ids=("brand-accent-yellow",),
                synchronized_event_id="beat-hook",
                sound_cue_ids=("music-bed",),
                entrance=production.GraphicAnimation.SLIDE_UP,
                exit=production.GraphicAnimation.FADE,
                z_index=100,
            ),
            production.GraphicTreatment(
                graphic_id="cta-close",
                role=production.GraphicRole.CTA,
                text="看看青颜",
                shot_id="shot-2",
                start_frame_offset=24,
                duration_frames=48,
                x_milli=80,
                y_milli=720,
                width_milli=840,
                font_size_px=58,
                text_color="#FFFFFF",
                safe_area=production.GraphicSafeAreaInsets(
                    top_milli=40,
                    right_milli=40,
                    bottom_milli=40,
                    left_milli=40,
                ),
                brand_token_ids=("brand-text-light",),
                synchronized_event_id="product-hero",
                sound_cue_ids=("music-bed",),
                entrance=production.GraphicAnimation.FADE,
                exit=production.GraphicAnimation.FADE,
                z_index=110,
            ),
            production.GraphicTreatment(
                graphic_id="brand-close",
                role=production.GraphicRole.BRAND_END_CARD,
                text="青颜",
                shot_id="shot-2",
                start_frame_offset=24,
                duration_frames=48,
                x_milli=80,
                y_milli=120,
                width_milli=840,
                font_size_px=76,
                text_color="#171717",
                background_color="#F7D000FF",
                safe_area=production.GraphicSafeAreaInsets(
                    top_milli=40,
                    right_milli=40,
                    bottom_milli=40,
                    left_milli=40,
                ),
                brand_token_ids=("brand-accent-yellow",),
                synchronized_event_id="product-hero",
                sound_cue_ids=("music-bed",),
                entrance=production.GraphicAnimation.SCALE_IN,
                exit=production.GraphicAnimation.FADE,
                z_index=105,
            ),
        ),
        sound_cues=(
            production.AdSoundCue(
                cue_id="music-bed",
                role=production.AdSoundRole.MUSIC,
                audio_track_id="audio-music",
                synchronized_event_id="headline-hook",
            ),
        ),
        visual_motif="青颜黄、黑色粗体、短促 graphic reveal",
        hero_shot_presentation_id="product-hero",
        end_card_graphic_ids=("brand-close",),
        cta_graphic_id="cta-close",
    )
    if changes:
        plan = plan.model_copy(update=changes)
    return seal_artifact(plan.model_copy(update={"content_hash": "0" * 64}))


def test_ad_creative_plan_seals_typed_product_graphic_and_sound_contracts() -> None:
    assert hasattr(production, "AdCreativePlan")
    plan = _make_plan()

    assert plan.schema_version == "ad-creative-plan/1"
    assert plan.product_presentations[0].mode.value == "hero_asset"
    assert plan.product_presentations[0].beat_id == "beat-hero"
    assert plan.product_presentations[0].graphic_treatment_ids == ("brand-close",)
    assert plan.graphic_treatments[0].role.value == "headline"
    assert plan.graphic_treatments[0].claim_reference_ids == ("claim-net-odor",)
    assert plan.graphic_treatments[0].safe_area.left_milli == 40
    assert plan.graphic_treatments[0].keyword_emphasis[0].text == "气味"
    assert plan.graphic_treatments[0].brand_token_ids == ("brand-accent-yellow",)
    assert plan.sound_cues[0].role.value == "music"
    assert plan.content_hash != "0" * 64


def _make_base_composition() -> production.CompositionSpec:
    base = make_composition_spec()
    product_layer = CompositionLayerSpec(
        layer_id="layer-product-packshot",
        shot_id="shot-2",
        asset_role="product_graphic",
        asset_id="product-packshot",
        z_index=10,
    )
    music = AudioTrackSpec(
        track_id="audio-music",
        audio_kind=AudioKind.BGM,
        asset_id="music-bed",
        start_sample=0,
    )
    return seal_artifact(
        base.model_copy(
            update={
                "schema_version": "2.1",
                "content_hash": "0" * 64,
                "layers": (*base.layers, product_layer),
                "audio_tracks": (music,),
            }
        )
    )


def test_compiler_projects_plan_into_composition_22_without_caption_overload() -> None:
    assert hasattr(production, "compile_ad_creative_plan")
    compiled = production.compile_ad_creative_plan(
        _make_plan(),
        _make_base_composition(),
    )

    assert compiled.schema_version == "2.2"
    assert compiled.revision == 2
    assert compiled.graphic_layer_ids == ("layer-product-packshot",)
    assert compiled.graphic_layer_animations[0].layer_id == "layer-product-packshot"
    assert compiled.graphic_layer_animations[0].entrance.value == "scale_in"
    assert tuple(item.graphic_id for item in compiled.commercial_graphics) == (
        "headline-hook",
        "cta-close",
        "brand-close",
    )
    assert compiled.caption_tracks == ()
    assert compiled.audio_tracks[0].track_id == "audio-music"
    assert compiled.commercial_graphics[0].claim_reference_ids == ("claim-net-odor",)
    assert compiled.commercial_graphics[0].synchronized_event_id == "beat-hook"
    assert compiled.advertising_sound_cues[0].cue_id == "music-bed"
    assert compiled.ad_creative_plan_hash == _make_plan().content_hash
    assert any(
        item.reference == _make_plan().artifact_id
        and item.content_hash == _make_plan().content_hash
        for item in compiled.source_provenance
    )
    assert compiled.content_hash != "0" * 64


def test_compiler_fails_closed_for_unresolved_physical_product_interaction() -> None:
    presentation = _make_plan().product_presentations[0].model_copy(
        update={
            "capability_classification": production.CapabilityClassification.REQUIRES_RUNTIME_CAPABILITY,
            "requires_physical_interaction": True,
        }
    )
    plan = _make_plan(product_presentations=(presentation,))

    with pytest.raises(AiVideoError) as caught:
        production.compile_ad_creative_plan(plan, _make_base_composition())

    assert caught.value.code is ErrorCode.COMPOSITION_INVALID
    assert "physical interaction" in caught.value.user_message.lower()


def test_compiler_revalidates_sealed_plan_invariants_at_public_boundary() -> None:
    graphic = _make_plan().graphic_treatments[0].model_copy(
        update={"claim_reference_ids": ("claim-not-declared",)}
    )
    plan = _make_plan(
        graphic_treatments=(graphic, *_make_plan().graphic_treatments[1:])
    )

    with pytest.raises(AiVideoError) as caught:
        production.compile_ad_creative_plan(plan, _make_base_composition())

    assert caught.value.code is ErrorCode.COMPOSITION_INVALID
    assert "adcreativeplan" in caught.value.user_message.lower()


def test_compiler_rejects_unregistered_in_scene_source_evidence() -> None:
    presentation = _make_plan().product_presentations[0].model_copy(
        update={
            "mode": production.ProductPresentationMode.IN_SCENE_PROVIDER,
            "composition_layer_id": None,
            "source_evidence_id": "arbitrary-unverified-string",
            "capability_classification": production.CapabilityClassification.REQUIRES_SOURCE_GENERATION_STRATEGY,
        }
    )
    plan = _make_plan(product_presentations=(presentation,))

    with pytest.raises(AiVideoError) as caught:
        production.compile_ad_creative_plan(plan, _make_base_composition())

    assert caught.value.code is ErrorCode.COMPOSITION_INVALID
    assert "source evidence" in caught.value.user_message.lower()


def test_compiler_accepts_exact_in_scene_source_evidence_pointer() -> None:
    evidence = production.SourceGenerationEvidencePointer(
        evidence_id="source-evidence-product-hero",
        artifact_id="generated-shot-product-hero",
        revision=1,
        content_hash="b" * 64,
        shot_id="shot-2",
        asset_id="image-shot-2",
    )
    presentation = _make_plan().product_presentations[0].model_copy(
        update={
            "mode": production.ProductPresentationMode.IN_SCENE_PROVIDER,
            "asset_id": evidence.asset_id,
            "composition_layer_id": None,
            "source_evidence_id": evidence.evidence_id,
            "capability_classification": production.CapabilityClassification.REQUIRES_SOURCE_GENERATION_STRATEGY,
        }
    )
    plan = _make_plan(
        source_generation_evidence=(evidence,),
        product_presentations=(presentation,),
        source_provenance=(
            *_make_plan().source_provenance,
            SourceReference(
                kind="derived",
                reference=evidence.artifact_id,
                content_hash=evidence.content_hash,
            ),
        ),
    )

    compiled = production.compile_ad_creative_plan(plan, _make_base_composition())

    assert compiled.graphic_layer_ids == ()
    assert compiled.ad_creative_plan_hash == plan.content_hash


def test_compiler_rejects_ad_beat_bound_to_unknown_shot() -> None:
    broken_beat = _make_plan().ad_arc[0].model_copy(
        update={"shot_ids": ("shot-missing",)}
    )
    plan = _make_plan(ad_arc=(broken_beat, *_make_plan().ad_arc[1:]))

    with pytest.raises(AiVideoError) as caught:
        production.compile_ad_creative_plan(plan, _make_base_composition())

    assert caught.value.code is ErrorCode.COMPOSITION_INVALID
    assert "beat" in caught.value.user_message.lower()
    assert "shot" in caught.value.user_message.lower()


def test_compiler_rejects_ad_arc_shot_order_that_review_would_reject() -> None:
    plan = _make_plan()
    reordered = _make_plan(
        ad_arc=(plan.ad_arc[1], plan.ad_arc[0], plan.ad_arc[2])
    )

    with pytest.raises(AiVideoError) as caught:
        production.compile_ad_creative_plan(reordered, _make_base_composition())

    assert caught.value.code is ErrorCode.COMPOSITION_INVALID
    assert "order" in caught.value.user_message.lower()


def test_compiler_normalizes_duplicate_product_layer_validation_error() -> None:
    duplicate = _make_plan().product_presentations[0].model_copy(
        update={"presentation_id": "product-duplicate", "role": production.ProductPresentationRole.CTA_SUPPORT}
    )
    plan = _make_plan(
        product_presentations=(*_make_plan().product_presentations, duplicate)
    )

    with pytest.raises(AiVideoError) as caught:
        production.compile_ad_creative_plan(plan, _make_base_composition())

    assert caught.value.code is ErrorCode.COMPOSITION_INVALID
    assert "composition" in caught.value.user_message.lower()


def test_typed_authoring_proposal_compiles_shot_and_composition_handoff() -> None:
    plan = _make_plan()
    proposal = production.AdCreativePlanProposal.model_validate(
        {
            key: value
            for key, value in plan.model_dump(mode="python").items()
            if key
            not in {
                "schema_version",
                "artifact_id",
                "revision",
                "content_hash",
                "creation_receipt_id",
                "source_provenance",
            }
        }
    )
    rebuilt = production.create_ad_creative_plan(
        proposal,
        artifact_id="ad-plan-from-authoring",
        revision=1,
        creation_receipt_id="accept-authoring-proposal",
        source_provenance=plan.source_provenance,
    )
    handoff = production.compile_ad_creative_handoff(
        rebuilt,
        _make_base_composition(),
    )

    assert rebuilt.schema_version == "ad-creative-plan/2"
    expected_payload = plan.model_copy(
        update={
            "schema_version": "ad-creative-plan/2",
            "artifact_id": "ad-plan-from-authoring",
            "creation_receipt_id": "accept-authoring-proposal",
            "content_hash": rebuilt.content_hash,
        }
    )
    assert rebuilt.model_dump(mode="json") == expected_payload.model_dump(mode="json")
    assert handoff.plan_id == rebuilt.artifact_id
    assert handoff.plan_content_hash == rebuilt.content_hash
    assert tuple(item.shot_id for item in handoff.shot_proposals) == (
        "shot-1",
        "shot-2",
    )
    assert handoff.shot_proposals[0].sound_cue_ids == ("music-bed",)
    assert handoff.shot_proposals[1].sound_cue_ids == ("music-bed",)
    assert handoff.composition_requirements.graphic_layer_ids == (
        "layer-product-packshot",
    )
    assert handoff.composition_spec.ad_creative_plan_hash == rebuilt.content_hash


def test_typed_authoring_proposal_can_explicitly_reopen_legacy_plan_exactly() -> None:
    plan = _make_plan()
    proposal = production.AdCreativePlanProposal.model_validate(
        {
            key: value
            for key, value in plan.model_dump(mode="python").items()
            if key
            not in {
                "schema_version",
                "artifact_id",
                "revision",
                "content_hash",
                "creation_receipt_id",
                "source_provenance",
            }
        }
    )

    rebuilt = production.create_ad_creative_plan(
        proposal,
        artifact_id="ad-plan-from-authoring",
        revision=1,
        creation_receipt_id="accept-authoring-proposal",
        source_provenance=plan.source_provenance,
        schema_version="ad-creative-plan/1",
    )

    assert rebuilt.schema_version == "ad-creative-plan/1"
    expected_payload = plan.model_copy(
        update={
            "artifact_id": "ad-plan-from-authoring",
            "creation_receipt_id": "accept-authoring-proposal",
            "content_hash": rebuilt.content_hash,
        }
    )
    assert rebuilt.model_dump(mode="json") == expected_payload.model_dump(mode="json")


def test_shot_handoff_preserves_ordered_union_of_explicit_and_synchronized_sounds() -> None:
    base = _make_plan()
    sync_only = production.AdSoundCue(
        cue_id="sync-only",
        role=production.AdSoundRole.SFX,
        audio_track_id="audio-music",
        synchronized_event_id="headline-hook",
    )
    explicit_only = production.AdSoundCue(
        cue_id="explicit-only",
        role=production.AdSoundRole.REVEAL_HIT,
        audio_track_id="audio-music",
    )
    product = base.product_presentations[0].model_copy(
        update={"sound_cue_ids": ("explicit-only", "music-bed")}
    )
    graphics = tuple(
        item.model_copy(
            update={
                "sound_cue_ids": (
                    ("sync-only", "music-bed")
                    if item.shot_id == "shot-1"
                    else ("explicit-only", "music-bed")
                )
            }
        )
        for item in base.graphic_treatments
    )
    plan = _make_plan(
        product_presentations=(product,),
        graphic_treatments=graphics,
        sound_cues=(sync_only, explicit_only, *base.sound_cues),
    )

    handoff = production.compile_ad_creative_handoff(
        plan,
        _make_base_composition(),
    )

    assert handoff.shot_proposals[0].sound_cue_ids == ("sync-only", "music-bed")
    assert handoff.shot_proposals[1].sound_cue_ids == (
        "explicit-only",
        "music-bed",
    )


def test_ad_creative_review_is_pure_and_never_claims_production_acceptance() -> None:
    assert hasattr(production, "review_ad_creative_plan")
    plan = _make_plan()
    compiled = production.compile_ad_creative_plan(plan, _make_base_composition())

    report = production.review_ad_creative_plan(plan, compiled)

    assert report.is_ready is True
    assert report.production_verdict is None
    assert report.findings == ()
    assert {item.value for item in report.checked_dimensions} == {
        "product_integration",
        "commercial_typography",
        "ad_arc",
        "sound_synchronization",
        "brand_closure",
    }


def test_ad_creative_review_reports_missing_product_layer_without_mutation() -> None:
    plan = _make_plan()
    compiled = production.compile_ad_creative_plan(plan, _make_base_composition())
    broken = compiled.model_copy(update={"graphic_layer_ids": ()})

    report = production.review_ad_creative_plan(plan, broken)

    assert report.is_ready is False
    assert report.production_verdict is None
    assert tuple(item.code for item in report.findings) == (
        "composition_schema_invalid",
    )
    assert compiled.graphic_layer_ids == ("layer-product-packshot",)


def test_ad_creative_review_rejects_resealed_semantic_tampering() -> None:
    plan = _make_plan()
    compiled = production.compile_ad_creative_plan(plan, _make_base_composition())
    graphic = compiled.commercial_graphics[0].model_copy(
        update={"claim_reference_ids": ()}
    )
    tampered = seal_artifact(
        compiled.model_copy(
            update={
                "content_hash": "0" * 64,
                "commercial_graphics": (graphic, *compiled.commercial_graphics[1:]),
            }
        )
    )

    report = production.review_ad_creative_plan(plan, tampered)

    assert report.is_ready is False
    assert "commercial_graphic_projection_mismatch" in {
        item.code for item in report.findings
    }


def test_ad_creative_review_revalidates_plan_schema_at_public_boundary() -> None:
    original = _make_plan()
    graphic = original.graphic_treatments[0].model_copy(
        update={"claim_reference_ids": ("claim-not-declared",)}
    )
    invalid = seal_artifact(
        original.model_copy(
            update={
                "content_hash": "0" * 64,
                "graphic_treatments": (graphic, *original.graphic_treatments[1:]),
            }
        )
    )

    report = production.review_ad_creative_plan(
        invalid,
        production.compile_ad_creative_plan(original, _make_base_composition()),
    )

    assert report.is_ready is False
    assert "ad_plan_schema_invalid" in {item.code for item in report.findings}


def test_ad_creative_review_returns_report_for_structurally_invalid_model_copy() -> None:
    plan = _make_plan().model_copy(update={"ad_arc": ("not-a-beat",)})

    report = production.review_ad_creative_plan(
        plan,
        production.compile_ad_creative_plan(_make_plan(), _make_base_composition()),
    )

    assert report.is_ready is False
    assert report.production_verdict is None
    assert tuple(item.code for item in report.findings) == (
        "ad_plan_schema_invalid",
    )


@pytest.mark.parametrize("invalid_target", ["plan", "composition"])
def test_ad_creative_review_returns_report_when_top_level_identity_is_invalid(
    invalid_target: str,
) -> None:
    plan = _make_plan()
    composition = production.compile_ad_creative_plan(
        plan,
        _make_base_composition(),
    )
    if invalid_target == "plan":
        plan = plan.model_copy(update={"artifact_id": ""})
        expected_code = "ad_plan_schema_invalid"
    else:
        composition = composition.model_copy(update={"artifact_id": ""})
        expected_code = "composition_schema_invalid"

    report = production.review_ad_creative_plan(plan, composition)

    assert report.is_ready is False
    assert report.production_verdict is None
    assert expected_code in {item.code for item in report.findings}
    assert report.plan_id
    assert report.composition_id


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_shot",
        "reordered_shots",
        "extra_shot",
        "missing_graphic_layer",
        "extra_graphic_layer",
    ],
)
def test_ad_creative_review_requires_exact_shot_and_graphic_layer_projection(
    mutation: str,
) -> None:
    plan = _make_plan()
    compiled = production.compile_ad_creative_plan(plan, _make_base_composition())
    if mutation == "missing_shot":
        update = {"shot_ids": ("shot-2",)}
        expected_code = "ad_arc_shot_projection_mismatch"
    elif mutation == "reordered_shots":
        update = {"shot_ids": tuple(reversed(compiled.shot_ids))}
        expected_code = "ad_arc_shot_projection_mismatch"
    elif mutation == "extra_shot":
        update = {"shot_ids": (*compiled.shot_ids, "shot-extra")}
        expected_code = "ad_arc_shot_projection_mismatch"
    elif mutation == "missing_graphic_layer":
        update = {
            "graphic_layer_ids": (),
            "graphic_layer_animations": (),
        }
        expected_code = "product_graphic_layer_projection_mismatch"
    else:
        update = {
            "graphic_layer_ids": (
                *compiled.graphic_layer_ids,
                compiled.layers[0].layer_id,
            )
        }
        expected_code = "product_graphic_layer_projection_mismatch"
    tampered = seal_artifact(
        compiled.model_copy(update={"content_hash": "0" * 64, **update})
    )

    report = production.review_ad_creative_plan(plan, tampered)

    assert report.is_ready is False
    assert expected_code in {item.code for item in report.findings}
