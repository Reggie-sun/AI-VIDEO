from __future__ import annotations

from ai_video.production import (
    EcommerceAcceptanceRequirement,
    EcommerceAllowedClaim,
    EcommerceArtifactProposals,
    EcommerceAssetRequirement,
    EcommerceBeatRoleBinding,
    EcommerceDeliveryProfile,
    EcommerceGraphicRoleBinding,
    EcommerceLayoutPlan,
    EcommerceLayoutScene,
    EcommerceLayoutShot,
    EcommerceProductionCompileProfile,
    EcommerceProductionHandoff,
    EcommerceProductFact,
    EcommerceProductTruth,
    EcommerceRequirementResolution,
    EcommerceRuntimeRequirement,
    EcommerceTypographyToken,
    EcommerceTruthSource,
    EcommerceVisualSystemProfile,
)
from ai_video.production.ad_creative_types import (
    AdBeatPlan,
    AdBeatRole,
    AdCreativePlanProposal,
    AdSoundCue,
    CapabilityClassification,
    ProductPresentation,
    ProductPresentationMode,
    ProductPresentationRole,
    ProtagonistContinuityMode,
    ProtagonistContinuityPolicy,
)
from ai_video.production.commercial_graphics import (
    AdSoundRole,
    GraphicRole,
    GraphicSafeAreaInsets,
    GraphicTreatment,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AssetRoleRequirement,
    AssetType,
    Character,
    DurationPolicy,
    ProductionBrief,
    Scene,
    Shot,
    SourceReference,
    Story,
    StoryBeat,
    Storyboard,
    StoryboardBeat,
    VisualStrategy,
)


ZERO_HASH = "0" * 64
PACKAGE_ID = "1" * 64
INPUT_HASH = "2" * 64


def make_ecommerce_handoff() -> EcommerceProductionHandoff:
    delivery = EcommerceDeliveryProfile.create(
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        fps=24,
        codec_profile="h264",
        audio_sample_rate_hz=48_000,
        platform="short-video",
        placement="vertical-feed",
        constraints=("Keep all copy within the sealed safe area.",),
    )
    safe_area = GraphicSafeAreaInsets(
        top_milli=50,
        right_milli=50,
        bottom_milli=80,
        left_milli=50,
    )
    visual = EcommerceVisualSystemProfile.create(
        brand_token_ids=("brand-primary", "brand-end-card"),
        safe_area=safe_area,
        typography_tokens=(
            EcommerceTypographyToken(
                token_id="type-primary",
                font_family="sans-serif",
                font_size_px=64,
                font_weight=700,
                letter_spacing_px=0,
                text_color="#FFFFFFFF",
                background_color="#00000099",
            ),
        ),
        role_bindings=(
            EcommerceGraphicRoleBinding(
                role=GraphicRole.CTA,
                typography_token_id="type-primary",
            ),
            EcommerceGraphicRoleBinding(
                role=GraphicRole.BRAND_END_CARD,
                typography_token_id="type-primary",
            ),
        ),
    )
    cta = GraphicTreatment(
        graphic_id="graphic-cta",
        role=GraphicRole.CTA,
        text="Shop now",
        shot_id="shot-hero",
        start_frame_offset=0,
        duration_frames=48,
        x_milli=100,
        y_milli=650,
        width_milli=800,
        font_size_px=64,
        text_color="#FFFFFFFF",
        background_color="#00000099",
        safe_area=safe_area,
        brand_token_ids=("brand-primary",),
        sound_cue_ids=("sound-hero",),
        z_index=10,
    )
    end_card = GraphicTreatment(
        graphic_id="graphic-end-card",
        role=GraphicRole.BRAND_END_CARD,
        text="Product One",
        shot_id="shot-hero",
        start_frame_offset=48,
        duration_frames=24,
        x_milli=100,
        y_milli=300,
        width_milli=800,
        font_size_px=64,
        text_color="#FFFFFFFF",
        background_color="#00000099",
        safe_area=safe_area,
        brand_token_ids=("brand-end-card",),
        sound_cue_ids=("sound-hero",),
        z_index=10,
    )
    presentation = ProductPresentation(
        presentation_id="presentation-hero",
        role=ProductPresentationRole.HERO_SHOT,
        mode=ProductPresentationMode.HERO_ASSET,
        beat_id="beat-hero",
        shot_id="shot-hero",
        asset_id="asset-product",
        composition_layer_id="layer-product",
        product_truth_reference_ids=("source-product",),
        graphic_treatment_ids=("graphic-cta", "graphic-end-card"),
        sound_cue_ids=("sound-hero",),
        capability_classification=CapabilityClassification.SUPPORTED_CURRENTLY,
    )
    layout = EcommerceLayoutPlan.create(
        source_package_id=PACKAGE_ID,
        delivery_profile_id=delivery.profile_id,
        visual_system_profile_id=visual.profile_id,
        scenes=(
            EcommerceLayoutScene(
                scene_id="scene-product",
                source_set_id="set-product",
                location="Product stage",
                time="day",
                mood="clean commercial",
                participant_ids=("talent-presenter",),
                continuity_constraints=("Product remains frame center.",),
            ),
        ),
        shots=(
            EcommerceLayoutShot(
                shot_id="shot-hero",
                scene_id="scene-product",
                character_ids=("talent-presenter",),
                visual_strategy=VisualStrategy.GENERATED_VIDEO,
                continuity_constraints=("Preserve product identity.",),
            ),
        ),
        beat_roles=(
            EcommerceBeatRoleBinding(beat_id="beat-hero", role=AdBeatRole.HERO),
            EcommerceBeatRoleBinding(beat_id="beat-cta", role=AdBeatRole.CTA),
            EcommerceBeatRoleBinding(
                beat_id="beat-brand", role=AdBeatRole.BRAND_CLOSURE
            ),
        ),
        graphic_treatments=(cta, end_card),
        product_presentations=(presentation,),
        protagonist_ids=("talent-presenter",),
    )
    compile_profile = EcommerceProductionCompileProfile.create(
        delivery_profile_id=delivery.profile_id,
        visual_system_profile_id=visual.profile_id,
        layout_plan_id=layout.layout_plan_id,
        requirement_resolutions=(
            EcommerceRequirementResolution(
                requirement_id="req-ad-graphics",
                capability="advertising_copy_graphics",
                resolution_kind="EXACT_GRAPHIC_LAYOUT",
                evidence_ids=(
                    delivery.profile_id,
                    visual.profile_id,
                    layout.layout_plan_id,
                ),
            ),
        ),
    )
    provenance = (
        SourceReference(
            kind="derived",
            reference=f"ecommerce-package:{PACKAGE_ID}",
            content_hash=PACKAGE_ID,
        ),
    )
    brief = seal_artifact(
        ProductionBrief(
            artifact_id="brief-product-one",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="ecommerce-authoring-brief",
            source_provenance=provenance,
            title="Product One vertical ad",
            objective="Conversion",
            audience="People seeking a compact product",
            format="9:16 ecommerce ad",
            language="en",
            constraints=delivery.constraints,
        )
    )
    story = seal_artifact(
        Story(
            artifact_id="story-product-one",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="ecommerce-authoring-story",
            source_provenance=provenance,
            language="en",
            logline="A presenter reveals Product One and closes with a clear CTA.",
            synopsis="One concise hero product demonstration.",
            beats=(StoryBeat(beat_id="story-hero", summary="Reveal the product."),),
            source_references=("source-product",),
        )
    )
    character = seal_artifact(
        Character(
            artifact_id="character-talent-presenter",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="ecommerce-authoring-character",
            source_provenance=provenance,
            character_id="talent-presenter",
            name="Presenter",
            identity="Product presenter",
            appearance_bible="Friendly adult presenter with stable facial identity.",
            wardrobe=("solid neutral shirt",),
            allowed_variations=("natural gesture variation",),
        )
    )
    scene = seal_artifact(
        Scene(
            artifact_id="scene-product-stage",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="ecommerce-authoring-scene",
            source_provenance=provenance,
            scene_id="scene-product",
            location="Product stage",
            time="day",
            mood="clean commercial",
            participant_ids=("talent-presenter",),
            continuity_constraints=("Product remains frame center.",),
        )
    )
    shot = seal_artifact(
        Shot(
            artifact_id="shot-artifact-hero",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="ecommerce-authoring-shot",
            source_provenance=provenance,
            shot_id="shot-hero",
            scene_id="scene-product",
            storyboard_beat_id="storyboard-hero",
            intent="Reveal Product One with a stable presenter and product identity.",
            duration_policy=DurationPolicy(mode="fixed", seconds=3.0),
            character_ids=("talent-presenter",),
            continuity_constraints=("Preserve product identity.",),
            visual_strategy=VisualStrategy.GENERATED_VIDEO,
            required_asset_roles=(
                AssetRoleRequirement(
                    role="final_visual",
                    asset_ids=(),
                    allowed_asset_types=(AssetType.VIDEO,),
                ),
            ),
            generated_video_rationale="The approved Shot requires presenter motion.",
        )
    )
    storyboard = seal_artifact(
        Storyboard(
            artifact_id="storyboard-product-one",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="ecommerce-authoring-storyboard",
            source_provenance=provenance,
            beats=(
                StoryboardBeat(
                    beat_id="storyboard-hero",
                    scene_id="scene-product",
                    shot_ids=("shot-hero",),
                    narrative_intent="Reveal the product, then close.",
                ),
            ),
        )
    )
    ad_plan = AdCreativePlanProposal(
        creative_concept="Clean product reveal with readable end-card closure.",
        product_truth_source_ids=("source-product",),
        claim_reference_ids=("claim-product",),
        protagonist_continuity_policy=ProtagonistContinuityPolicy(
            mode=ProtagonistContinuityMode.SINGLE_PROTAGONIST,
            protagonist_ids=("talent-presenter",),
        ),
        ad_arc=(
            AdBeatPlan(
                beat_id="beat-hero", role=AdBeatRole.HERO, shot_ids=("shot-hero",)
            ),
            AdBeatPlan(
                beat_id="beat-cta", role=AdBeatRole.CTA, shot_ids=("shot-hero",)
            ),
            AdBeatPlan(
                beat_id="beat-brand",
                role=AdBeatRole.BRAND_CLOSURE,
                shot_ids=("shot-hero",),
            ),
        ),
        product_presentations=(presentation,),
        graphic_treatments=(cta, end_card),
        sound_cues=(
            AdSoundCue(
                cue_id="sound-hero",
                role=AdSoundRole.MUSIC,
                audio_track_id="audio-music",
                synchronized_event_id="presentation-hero",
            ),
        ),
        visual_motif="Clean centered packshot with high-contrast lower CTA.",
        hero_shot_presentation_id="presentation-hero",
        end_card_graphic_ids=("graphic-end-card",),
        cta_graphic_id="graphic-cta",
    )
    return EcommerceProductionHandoff.create(
        source_package_id=PACKAGE_ID,
        source_input_hash=INPUT_HASH,
        delivery_profile=delivery,
        visual_system_profile=visual,
        layout_plan=layout,
        compile_profile=compile_profile,
        product_truth=EcommerceProductTruth(
            product_id="product-one",
            product_name="Product One",
            sources=(
                EcommerceTruthSource(
                    source_id="source-product",
                    source_kind="BRAND_DOCUMENT",
                    reference="brand/product-one.pdf",
                    rights_status="CONFIRMED",
                ),
            ),
            facts=(
                EcommerceProductFact(
                    fact_id="fact-product",
                    statement="Product One is the named product.",
                    source_ids=("source-product",),
                ),
            ),
            allowed_claims=(
                EcommerceAllowedClaim(
                    claim_id="claim-product",
                    text="Product One",
                    claim_type="FACT",
                    fact_ids=("fact-product",),
                    source_ids=("source-product",),
                ),
            ),
            prohibited_claims=(),
            required_disclaimers=(),
        ),
        artifact_proposals=EcommerceArtifactProposals(
            brief=brief,
            story=story,
            characters=(character,),
            scenes=(scene,),
            storyboard=storyboard,
            shots=(shot,),
        ),
        ad_creative_plan_proposal=ad_plan,
        asset_requirements=(
            EcommerceAssetRequirement(
                asset_id="asset-product",
                source_kind="IMAGE",
                reference="assets/product-one.png",
                rights_status="CONFIRMED",
            ),
        ),
        runtime_requirements=(
            EcommerceRuntimeRequirement(
                requirement_id="req-ad-graphics",
                capability="advertising_copy_graphics",
                classification="REQUIRES_RUNTIME_CAPABILITY",
                rationale="The exact visual contracts resolve this authoring gap.",
            ),
        ),
        acceptance_requirements=(
            EcommerceAcceptanceRequirement(
                requirement_id="accept-shot-product",
                scope="SHOT",
                subject_id="shot-hero",
                description="Product and presenter identity remain stable.",
            ),
            EcommerceAcceptanceRequirement(
                requirement_id="accept-final-layout",
                scope="FINAL_OUTPUT",
                subject_id="final-output",
                description="CTA and end card are readable and do not cover the product.",
            ),
        ),
        unsupported_gaps=(),
    )
