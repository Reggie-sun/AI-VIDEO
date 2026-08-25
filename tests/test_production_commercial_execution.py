from __future__ import annotations

import pytest

import ai_video.production as production

from ai_video.production.hashing import seal_artifact
from ai_video.production.models import AudioKind, AudioTrackSpec, CompositionLayerSpec, SourceReference
from production_project_factory import make_composition_spec


def _plan() -> production.AdCreativePlan:
    graphics = (
        production.GraphicTreatment(
            graphic_id="proof",
            role=production.GraphicRole.PROOF_LABEL,
            text="清爽净味",
            shot_id="shot-07",
            start_frame_offset=0,
            duration_frames=24,
            x_milli=100,
            y_milli=100,
            width_milli=800,
            font_size_px=48,
            text_color="#111111",
            brand_token_ids=("qingyan-yellow",),
            sound_cue_ids=("music",),
            z_index=100,
        ),
        production.GraphicTreatment(
            graphic_id="cta",
            role=production.GraphicRole.CTA,
            text="立即了解",
            shot_id="shot-08",
            start_frame_offset=0,
            duration_frames=24,
            x_milli=100,
            y_milli=700,
            width_milli=800,
            font_size_px=48,
            text_color="#FFFFFF",
            brand_token_ids=("qingyan-yellow",),
            sound_cue_ids=("music",),
            z_index=100,
        ),
        production.GraphicTreatment(
            graphic_id="brand",
            role=production.GraphicRole.BRAND_END_CARD,
            text="青颜",
            shot_id="shot-08",
            start_frame_offset=0,
            duration_frames=24,
            x_milli=100,
            y_milli=100,
            width_milli=800,
            font_size_px=64,
            text_color="#111111",
            brand_token_ids=("qingyan-yellow",),
            sound_cue_ids=("music",),
            z_index=100,
        ),
    )
    presentations = (
        production.ProductPresentation(
            presentation_id="interaction-03",
            role=production.ProductPresentationRole.DEMONSTRATION,
            mode=production.ProductPresentationMode.IN_SCENE_PROVIDER,
            beat_id="beat-03",
            shot_id="shot-03",
            product_id="qingyan-spray",
            product_reference_requirement_id="product-req-qingyan",
            source_requirement_id="source-req-03",
            product_truth_reference_ids=("truth-packaging",),
            graphic_treatment_ids=("proof",),
            sound_cue_ids=("music",),
            capability_classification=production.CapabilityClassification.REQUIRES_SOURCE_GENERATION_STRATEGY,
            requires_physical_interaction=True,
        ),
        production.ProductPresentation(
            presentation_id="interaction-04",
            role=production.ProductPresentationRole.DEMONSTRATION,
            mode=production.ProductPresentationMode.IN_SCENE_PROVIDER,
            beat_id="beat-04",
            shot_id="shot-04",
            product_id="qingyan-spray",
            product_reference_requirement_id="product-req-qingyan",
            source_requirement_id="source-req-04",
            product_truth_reference_ids=("truth-packaging",),
            graphic_treatment_ids=("proof",),
            sound_cue_ids=("music",),
            capability_classification=production.CapabilityClassification.REQUIRES_SOURCE_GENERATION_STRATEGY,
            requires_physical_interaction=True,
        ),
        production.ProductPresentation(
            presentation_id="hero-06",
            role=production.ProductPresentationRole.HERO_SHOT,
            mode=production.ProductPresentationMode.HERO_ASSET,
            beat_id="beat-06",
            shot_id="shot-06",
            asset_id="asset-packshot",
            composition_layer_id="layer-packshot",
            product_id="qingyan-spray",
            product_reference_requirement_id="product-req-qingyan",
            product_truth_reference_ids=("truth-packaging",),
            graphic_treatment_ids=("brand",),
            sound_cue_ids=("music",),
            capability_classification=production.CapabilityClassification.SUPPORTED_CURRENTLY,
        ),
    )
    plan = production.AdCreativePlan(
        schema_version="ad-creative-plan/2",
        artifact_id="ad-plan-qingyan",
        revision=2,
        content_hash="0" * 64,
        creation_receipt_id="approved-qingyan",
        source_provenance=(SourceReference(kind="derived", reference="package-qingyan"),),
        creative_concept="青颜商品互动广告",
        product_truth_source_ids=("truth-packaging",),
        claim_reference_ids=("claim-clean",),
        product_reference_requirements=(
            production.ProductReferenceRequirement(
                requirement_id="product-req-qingyan",
                product_id="qingyan-spray",
                truth_reference_ids=("truth-packaging",),
                expected_views=("front", "label"),
                fidelity_dimensions=("packaging_identity", "logo_label_identity"),
            ),
        ),
        source_generation_evidence=(),
        protagonist_continuity_policy=production.ProtagonistContinuityPolicy(
            mode=production.ProtagonistContinuityMode.SINGLE_PROTAGONIST,
            protagonist_ids=("character-qingyan",),
            allowed_variations=(),
        ),
        ad_arc=(
            production.AdBeatPlan(beat_id="beat-03", role=production.AdBeatRole.DEMONSTRATION, shot_ids=("shot-03",)),
            production.AdBeatPlan(beat_id="beat-04", role=production.AdBeatRole.DEMONSTRATION, shot_ids=("shot-04",)),
            production.AdBeatPlan(beat_id="beat-06", role=production.AdBeatRole.HERO, shot_ids=("shot-06",)),
            production.AdBeatPlan(beat_id="beat-07", role=production.AdBeatRole.PROOF, shot_ids=("shot-07",)),
            production.AdBeatPlan(beat_id="beat-08", role=production.AdBeatRole.BRAND_CLOSURE, shot_ids=("shot-08",)),
        ),
        product_presentations=presentations,
        graphic_treatments=graphics,
        sound_cues=(production.AdSoundCue(cue_id="music", role=production.AdSoundRole.MUSIC, audio_track_id="audio-music"),),
        visual_motif="yellow product truth",
        hero_shot_presentation_id="hero-06",
        end_card_graphic_ids=("brand",),
        cta_graphic_id="cta",
    )
    return production.AdCreativePlan.model_validate(seal_artifact(plan).model_dump(mode="python"))


def test_qingyan_commercial_execution_projection_uses_distinct_primary_lanes() -> None:
    projections = production.project_commercial_executions(_plan())
    by_shot = {item.target_shot_id: item for item in projections}

    assert by_shot["shot-03"].primary_class is production.CommercialShotClass.PRODUCT_INTERACTION
    assert by_shot["shot-04"].requires_source_materialization is True
    assert by_shot["shot-06"].primary_class is production.CommercialShotClass.PRODUCT_HERO
    assert by_shot["shot-07"].primary_class is production.CommercialShotClass.PROOF_GRAPHIC
    assert by_shot["shot-08"].primary_class is production.CommercialShotClass.END_CARD
    assert by_shot["shot-07"].invoke_video_provider is False
    assert by_shot["shot-08"].invoke_video_provider is False
    assert production.project_commercial_executions(_plan()) == projections


def test_current_ad_plan_rejects_legacy_source_evidence_as_readiness() -> None:
    legacy = production.SourceGenerationEvidencePointer(
        evidence_id="legacy-evidence",
        artifact_id="legacy-image",
        revision=1,
        content_hash="f" * 64,
        shot_id="shot-03",
        asset_id="legacy-asset",
    )
    payload = _plan().model_dump(mode="python")
    payload["source_generation_evidence"] = (legacy,)

    with pytest.raises(ValueError, match="legacy"):
        production.AdCreativePlan.model_validate(payload)


def test_current_ad_factory_emits_exact_v2_bytes_when_explicitly_selected() -> None:
    expected = _plan()
    proposal = production.AdCreativePlanProposal.model_validate(
        {
            key: value
            for key, value in expected.model_dump(mode="python").items()
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
        schema_version="ad-creative-plan/2",
        artifact_id=expected.artifact_id,
        revision=expected.revision,
        creation_receipt_id=expected.creation_receipt_id,
        source_provenance=expected.source_provenance,
    )

    assert rebuilt == expected
    assert rebuilt.model_dump_json() == expected.model_dump_json()
    assert rebuilt.content_hash == expected.content_hash


def test_current_composition_compile_does_not_require_interaction_overlay_evidence() -> None:
    plan = _plan()
    base = make_composition_spec(
        shot_ids=tuple(
            dict.fromkeys(
                shot_id for beat in plan.ad_arc for shot_id in beat.shot_ids
            )
        )
    )
    base = seal_artifact(
        base.model_copy(
            update={
                "schema_version": "2.1",
                "content_hash": "0" * 64,
                "layers": (
                    *base.layers,
                    CompositionLayerSpec(
                        layer_id="layer-packshot",
                        shot_id="shot-06",
                        asset_role="product_graphic",
                        asset_id="asset-packshot",
                    ),
                ),
                "audio_tracks": (
                    AudioTrackSpec(
                        track_id="audio-music",
                        audio_kind=AudioKind.BGM,
                        asset_id="music",
                        start_sample=0,
                    ),
                ),
            }
        )
    )

    compiled = production.compile_ad_creative_plan(plan, base)
    report = production.review_ad_creative_plan(plan, compiled)

    assert compiled.ad_creative_plan_hash == plan.content_hash
    assert report.is_ready is True
    assert report.requires_source_preparation is True
    assert report.source_preparation_ready is False
    assert all(
        layer.asset_id not in {None, "interaction-keyframe-03", "interaction-keyframe-04"}
        for layer in compiled.layers
    )
