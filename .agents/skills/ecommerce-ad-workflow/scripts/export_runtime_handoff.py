#!/usr/bin/env python3
"""Pure exporter from package/2 plus reviewed visual contracts to Runtime handoff."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[3]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(REPOSITORY_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from contract_models import EcommerceAdProductionPackage
from validate_contract import validate_file

from ai_video.production import (
    EcommerceAcceptanceRequirement,
    EcommerceAllowedClaim,
    EcommerceArtifactProposals,
    EcommerceAssetRequirement,
    EcommerceBeatRoleBinding,
    EcommerceDeliveryProfile,
    EcommerceLayoutPlan,
    EcommerceProductionCompileProfile,
    EcommerceProductionHandoff,
    EcommerceProductFact,
    EcommerceProductTruth,
    EcommerceProhibitedClaim,
    EcommerceRuntimeRequirement,
    EcommerceUnsupportedGap,
    EcommerceVisualSystemProfile,
    EcommerceTruthSource,
)
from ai_video.production.ad_creative_types import (
    AdBeatPlan,
    AdCreativePlanProposal,
    AdSoundCue,
    CapabilityClassification,
    ProductPresentationRole,
    ProtagonistContinuityMode,
    ProtagonistContinuityPolicy,
)
from ai_video.production.commercial_graphics import AdSoundRole, GraphicRole
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

_GRAPHIC_ROLES = {item.name: item for item in GraphicRole}
_SOUND_ROLES = {
    "DIALOGUE": AdSoundRole.DIALOGUE,
    "VOICE_OVER": AdSoundRole.VOICE_OVER,
    "MUSIC": AdSoundRole.MUSIC,
    "SFX": AdSoundRole.SFX,
    "INTENTIONAL_SILENCE": AdSoundRole.INTENTIONAL_SILENCE,
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _validate_visual_contracts(
    package: EcommerceAdProductionPackage,
    delivery: EcommerceDeliveryProfile,
    visual: EcommerceVisualSystemProfile,
    layout: EcommerceLayoutPlan,
    compile_profile: EcommerceProductionCompileProfile,
) -> None:
    _require(package.package_id == layout.source_package_id, "layout package identity mismatch")
    _require(package.aspect_ratio == delivery.aspect_ratio, "delivery aspect ratio mismatch")
    _require(layout.delivery_profile_id == delivery.profile_id, "layout delivery identity mismatch")
    _require(
        layout.visual_system_profile_id == visual.profile_id,
        "layout visual system identity mismatch",
    )
    _require(
        compile_profile.delivery_profile_id == delivery.profile_id
        and compile_profile.visual_system_profile_id == visual.profile_id
        and compile_profile.layout_plan_id == layout.layout_plan_id,
        "compile profile does not bind exact visual contracts",
    )
    package_shots = tuple(item.shot_id for item in package.shot_intents)
    layout_shots = tuple(item.shot_id for item in layout.shots)
    _require(package_shots == layout_shots, "layout must preserve exact package Shot order")
    copies = {item.copy_id: item for item in package.copy_graphics_plan}
    treatments = {item.graphic_id: item for item in layout.graphic_treatments}
    _require(set(copies) == set(treatments), "layout must resolve every copy graphic exactly once")
    token_by_id = {item.token_id: item for item in visual.typography_tokens}
    token_id_by_role = {
        item.role: item.typography_token_id for item in visual.role_bindings
    }
    shot_frames = {
        item.shot_id: round((item.end_seconds - item.start_seconds) * delivery.fps)
        for item in package.shot_intents
    }
    for copy_id, copy in copies.items():
        treatment = treatments[copy_id]
        role = _GRAPHIC_ROLES[copy.role]
        _require(treatment.role is role, f"graphic role mismatch: {copy_id}")
        _require(
            treatment.text == copy.text and treatment.shot_id == copy.shot_id,
            f"graphic content binding mismatch: {copy_id}",
        )
        _require(
            treatment.start_frame_offset + treatment.duration_frames
            <= shot_frames[copy.shot_id],
            f"graphic exceeds Shot duration: {copy_id}",
        )
        token_id = token_id_by_role.get(role)
        _require(token_id is not None, f"graphic role lacks typography binding: {copy_id}")
        token = token_by_id[token_id]
        _require(
            treatment.font_size_px == token.font_size_px
            and treatment.font_weight == token.font_weight
            and treatment.letter_spacing_px == token.letter_spacing_px
            and treatment.text_color == token.text_color
            and treatment.background_color == token.background_color,
            f"graphic typography drifts from visual system: {copy_id}",
        )
        _require(treatment.safe_area == visual.safe_area, f"graphic safe area drift: {copy_id}")
        _require(
            copy.brand_token_reference in treatment.brand_token_ids,
            f"graphic lacks authoring brand token: {copy_id}",
        )
        _require(
            tuple(item.text for item in treatment.keyword_emphasis)
            == copy.keyword_emphasis,
            f"graphic keyword emphasis drift: {copy_id}",
        )
    package_presentations = {item.presentation_id for item in package.product_presentation}
    layout_presentations = {item.presentation_id for item in layout.product_presentations}
    _require(
        package_presentations == layout_presentations,
        "layout must resolve every product presentation exactly once",
    )
    _require(
        layout.protagonist_ids
        and set(layout.protagonist_ids)
        == {item.talent_id for item in package.talent_plan},
        "current AdCreativePlan requires exact declared talent protagonists",
    )


def export_runtime_handoff(
    package: EcommerceAdProductionPackage,
    *,
    delivery: EcommerceDeliveryProfile,
    visual: EcommerceVisualSystemProfile,
    layout: EcommerceLayoutPlan,
    compile_profile: EcommerceProductionCompileProfile,
) -> EcommerceProductionHandoff:
    """Project already-validated authoring truth into a sealed Runtime handoff."""

    package = EcommerceAdProductionPackage.model_validate(
        package.model_dump(mode="python")
    )
    delivery = EcommerceDeliveryProfile.model_validate(
        delivery.model_dump(mode="python")
    )
    visual = EcommerceVisualSystemProfile.model_validate(
        visual.model_dump(mode="python")
    )
    layout = EcommerceLayoutPlan.model_validate(layout.model_dump(mode="python"))
    compile_profile = EcommerceProductionCompileProfile.model_validate(
        compile_profile.model_dump(mode="python")
    )
    _validate_visual_contracts(package, delivery, visual, layout, compile_profile)
    provenance = (
        SourceReference(
            kind="derived",
            reference=f"ecommerce-package:{package.package_id}",
            content_hash=package.package_id,
        ),
    )
    brief = seal_artifact(
        ProductionBrief(
            artifact_id=f"brief-{package.product_truth.sku_id}",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id=f"ecommerce-authoring-{package.package_id}",
            source_provenance=provenance,
            title=f"{package.product_truth.product_name} ecommerce ad",
            objective=package.ad_strategy.objective,
            audience=package.ad_strategy.audience,
            format=f"{package.aspect_ratio} {package.ad_format}",
            language="und",
            constraints=delivery.constraints,
        )
    )
    story = seal_artifact(
        Story(
            artifact_id=f"story-{package.ad_strategy.strategy_id}",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id=f"ecommerce-authoring-{package.package_id}",
            source_provenance=provenance,
            language=brief.language,
            logline=package.ad_strategy.angle,
            synopsis=package.ad_strategy.promise,
            beats=tuple(
                StoryBeat(beat_id=item.beat_id, summary=item.message)
                for item in package.ad_beats
            ),
            source_references=tuple(
                item.source_id for item in package.product_truth.sources
            ),
        )
    )
    characters = tuple(
        seal_artifact(
            Character(
                artifact_id=f"character-{item.talent_id}",
                revision=1,
                content_hash=ZERO_HASH,
                creation_receipt_id=f"ecommerce-authoring-{package.package_id}",
                source_provenance=provenance,
                character_id=item.talent_id,
                name=item.role,
                identity=item.role,
                appearance_bible=item.appearance,
                wardrobe=(item.wardrobe,),
                allowed_variations=item.continuity_anchors,
            )
        )
        for item in package.talent_plan
    )
    scenes = tuple(
        seal_artifact(
            Scene(
                artifact_id=f"scene-{item.scene_id}",
                revision=1,
                content_hash=ZERO_HASH,
                creation_receipt_id=f"ecommerce-authoring-{package.package_id}",
                source_provenance=provenance,
                scene_id=item.scene_id,
                location=item.location,
                time=item.time,
                mood=item.mood,
                participant_ids=item.participant_ids,
                continuity_constraints=item.continuity_constraints,
            )
        )
        for item in layout.scenes
    )
    shot_to_group = {
        shot_id: group.group_id
        for group in package.storyboard
        for shot_id in group.shot_ids
    }
    layout_shots = {item.shot_id: item for item in layout.shots}
    intents = {item.shot_id: item for item in package.shot_intents}
    audio_events = tuple(package.audio_plan.events)
    shots: list[Shot] = []
    for shot_id in (item.shot_id for item in package.shot_intents):
        intent = intents[shot_id]
        planned = layout_shots[shot_id]
        dialogue = " ".join(
            item.verbatim_line or ""
            for item in audio_events
            if item.kind == "DIALOGUE" and shot_id in item.shot_ids
        ).strip()
        narration = " ".join(
            item.verbatim_line or ""
            for item in audio_events
            if item.kind == "VOICE_OVER" and shot_id in item.shot_ids
        ).strip()
        required_roles = (
            (
                AssetRoleRequirement(
                    role="final_visual",
                    asset_ids=(),
                    allowed_asset_types=(AssetType.VIDEO,),
                ),
            )
            if planned.visual_strategy is VisualStrategy.GENERATED_VIDEO
            else ()
        )
        _require(
            planned.visual_strategy is VisualStrategy.GENERATED_VIDEO,
            f"exporter currently requires generated_video for asset-free bootstrap: {shot_id}",
        )
        shots.append(
            seal_artifact(
                Shot(
                    artifact_id=f"shot-artifact-{shot_id}",
                    revision=1,
                    content_hash=ZERO_HASH,
                    creation_receipt_id=f"ecommerce-authoring-{package.package_id}",
                    source_provenance=provenance,
                    shot_id=shot_id,
                    scene_id=planned.scene_id,
                    storyboard_beat_id=shot_to_group[shot_id],
                    intent=intent.purpose,
                    dialogue=dialogue,
                    narration=narration,
                    duration_policy=DurationPolicy(
                        mode="fixed",
                        seconds=intent.end_seconds - intent.start_seconds,
                    ),
                    character_ids=planned.character_ids,
                    continuity_constraints=planned.continuity_constraints,
                    visual_strategy=planned.visual_strategy,
                    required_asset_roles=required_roles,
                    generated_video_rationale=intent.visual_strategy_need,
                    composition_directives=planned.composition_directives,
                )
            )
        )
    storyboard = seal_artifact(
        Storyboard(
            artifact_id=f"storyboard-{package.ad_strategy.strategy_id}",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id=f"ecommerce-authoring-{package.package_id}",
            source_provenance=provenance,
            beats=tuple(
                StoryboardBeat(
                    beat_id=item.group_id,
                    scene_id=layout_shots[item.shot_ids[0]].scene_id,
                    shot_ids=item.shot_ids,
                    narrative_intent=item.commercial_intent,
                )
                for item in package.storyboard
            ),
        )
    )
    beat_roles = {item.beat_id: item.role for item in layout.beat_roles}
    _require(
        set(beat_roles) == {item.beat_id for item in package.ad_beats},
        "layout must assign one Runtime ad role to every package beat",
    )
    declared_sync_ids = (
        {item.beat_id for item in package.ad_beats}
        | {item.presentation_id for item in layout.product_presentations}
        | {item.graphic_id for item in layout.graphic_treatments}
    )
    sound_cues = tuple(
        AdSoundCue(
            cue_id=item.event_id,
            role=_SOUND_ROLES[item.kind],
            audio_track_id=None if item.kind == "INTENTIONAL_SILENCE" else item.event_id,
            synchronized_event_id=(
                next(
                    (
                        sync_id
                        for sync_id in item.synchronized_event_ids
                        if sync_id in declared_sync_ids
                    ),
                    item.beat_ids[0],
                )
            ),
        )
        for item in package.audio_plan.events
    )
    hero_id = next(
        item.presentation_id
        for item in layout.product_presentations
        if item.role is ProductPresentationRole.HERO_SHOT
    )
    plan = AdCreativePlanProposal(
        creative_concept=f"{package.ad_strategy.angle} {package.ad_strategy.promise}",
        product_truth_source_ids=tuple(
            item.source_id for item in package.product_truth.sources
        ),
        claim_reference_ids=tuple(
            item.claim_id for item in package.product_truth.allowed_claims
        ),
        protagonist_continuity_policy=ProtagonistContinuityPolicy(
            mode=(
                ProtagonistContinuityMode.SINGLE_PROTAGONIST
                if len(layout.protagonist_ids) == 1
                else ProtagonistContinuityMode.DECLARED_MONTAGE
            ),
            protagonist_ids=layout.protagonist_ids,
        ),
        ad_arc=tuple(
            AdBeatPlan(
                beat_id=item.beat_id,
                role=beat_roles[item.beat_id],
                shot_ids=item.shot_ids,
            )
            for item in package.ad_beats
        ),
        product_presentations=layout.product_presentations,
        graphic_treatments=layout.graphic_treatments,
        sound_cues=sound_cues,
        visual_motif=package.ad_strategy.angle,
        hero_shot_presentation_id=hero_id,
        end_card_graphic_ids=(package.cta.end_card_copy_id,),
        cta_graphic_id=package.cta.cta_copy_id,
    )
    requirements = tuple(
        EcommerceRuntimeRequirement(
            requirement_id=item.requirement_id,
            capability=item.capability,
            classification=item.classification,
            rationale=item.rationale,
        )
        for item in package.runtime_handoff.requirements
    )
    presentation_requirements = tuple(
        EcommerceRuntimeRequirement(
            requirement_id=f"presentation:{item.presentation_id}",
            capability="product_integration",
            classification="REQUIRES_RUNTIME_CAPABILITY",
            rationale=(
                "The exact product presentation requires tracking, occlusion, lighting, "
                "or physical-integration evidence."
            ),
        )
        for item in layout.product_presentations
        if (
            item.capability_classification
            is CapabilityClassification.REQUIRES_RUNTIME_CAPABILITY
        )
    )
    requirements = (*requirements, *presentation_requirements)
    resolved_ids = {
        item.requirement_id for item in compile_profile.requirement_resolutions
    }
    unsupported: list[EcommerceUnsupportedGap] = []
    for gap in package.runtime_handoff.classified_gaps:
        remaining = tuple(item for item in gap.requirement_ids if item not in resolved_ids)
        if gap.classification != "SUPPORTED_CURRENTLY" and remaining:
            unsupported.append(
                EcommerceUnsupportedGap(
                    gap_id=gap.gap_id,
                    classification=gap.classification,
                    requirement_ids=remaining,
                    blocker_code=gap.blocker_code
                    or "ECOMMERCE_RUNTIME_CAPABILITY_UNRESOLVED",
                    rationale=gap.rationale,
                )
            )
    for item in layout.product_presentations:
        if (
            item.capability_classification
            is CapabilityClassification.REQUIRES_RUNTIME_CAPABILITY
        ):
            unsupported.append(
                EcommerceUnsupportedGap(
                    gap_id=f"gap-{item.presentation_id}-integration",
                    classification="REQUIRES_RUNTIME_CAPABILITY",
                    requirement_ids=(f"presentation:{item.presentation_id}",),
                    blocker_code="ECOMMERCE_PRODUCT_INTEGRATION_UNRESOLVED",
                    rationale="The exact presentation still requires runtime product integration evidence.",
                )
            )
    return EcommerceProductionHandoff.create(
        source_package_id=package.package_id,
        source_input_hash=package.source_input_hash,
        delivery_profile=delivery,
        visual_system_profile=visual,
        layout_plan=layout,
        compile_profile=compile_profile,
        product_truth=EcommerceProductTruth(
            product_id=package.product_truth.sku_id,
            product_name=package.product_truth.product_name,
            sources=tuple(
                EcommerceTruthSource(
                    source_id=item.source_id,
                    source_kind=item.source_kind,
                    reference=item.reference,
                    rights_status=item.rights_status,
                )
                for item in package.product_truth.sources
            ),
            facts=tuple(
                EcommerceProductFact(
                    fact_id=item.fact_id,
                    statement=item.statement,
                    source_ids=item.source_ids,
                )
                for item in package.product_truth.facts
            ),
            allowed_claims=tuple(
                EcommerceAllowedClaim(
                    claim_id=item.claim_id,
                    text=item.text,
                    claim_type=item.claim_type.value,
                    fact_ids=item.fact_ids,
                    source_ids=item.source_ids,
                )
                for item in package.product_truth.allowed_claims
            ),
            prohibited_claims=tuple(
                EcommerceProhibitedClaim(
                    claim_id=item.claim_id,
                    text=item.text,
                    claim_type=item.claim_type.value,
                    reason=item.reason,
                )
                for item in package.product_truth.prohibited_claims
            ),
            required_disclaimers=package.product_truth.required_disclaimers,
        ),
        artifact_proposals=EcommerceArtifactProposals(
            brief=brief,
            story=story,
            characters=characters,
            scenes=scenes,
            storyboard=storyboard,
            shots=tuple(shots),
        ),
        ad_creative_plan_proposal=plan,
        asset_requirements=tuple(
            EcommerceAssetRequirement(
                asset_id=item.asset_id,
                source_kind=item.source_kind,
                reference=item.reference,
                rights_status=item.rights_status,
                expected_sha256=None,
                expected_size_bytes=None,
            )
            for item in package.product_truth.source_assets
        ),
        runtime_requirements=requirements,
        acceptance_requirements=(
            *(
                EcommerceAcceptanceRequirement(
                    requirement_id=f"accept-shot-{item.shot_id}",
                    scope="SHOT",
                    subject_id=item.shot_id,
                    description=(
                        "Validate exact product, protagonist, continuity, motion, and "
                        "sealed commercial intent before the next Shot."
                    ),
                )
                for item in package.shot_intents
            ),
            EcommerceAcceptanceRequirement(
                requirement_id="accept-final-ecommerce-output",
                scope="FINAL_OUTPUT",
                subject_id="final-output",
                description=(
                    "Validate exact final watchability, pacing, product truth, graphics, "
                    "audio, captions, CTA, and brand closure."
                ),
            ),
        ),
        unsupported_gaps=tuple(unsupported),
    )


def schema_text() -> str:
    return (
        json.dumps(
            EcommerceProductionHandoff.model_json_schema(mode="validation"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _load_model(path: Path, model):
    return model.model_validate_json(path.read_text(encoding="utf-8"))


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--source-input", type=Path, required=True)
    parser.add_argument("--delivery-profile", type=Path, required=True)
    parser.add_argument("--visual-system-profile", type=Path, required=True)
    parser.add_argument("--layout-plan", type=Path, required=True)
    parser.add_argument("--compile-profile", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    package = validate_file(
        "package", args.package, source_input_path=args.source_input
    )
    assert isinstance(package, EcommerceAdProductionPackage)
    handoff = export_runtime_handoff(
        package,
        delivery=_load_model(args.delivery_profile, EcommerceDeliveryProfile),
        visual=_load_model(args.visual_system_profile, EcommerceVisualSystemProfile),
        layout=_load_model(args.layout_plan, EcommerceLayoutPlan),
        compile_profile=_load_model(
            args.compile_profile, EcommerceProductionCompileProfile
        ),
    )
    sys.stdout.write(
        json.dumps(
            handoff.model_dump(mode="json"),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
