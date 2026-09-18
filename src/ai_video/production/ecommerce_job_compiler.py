"""Pure Ecommerce handoff compiler and canonical bootstrap adapter."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.ecommerce_job_contracts import EcommerceProductionHandoff
from ai_video.production.hashing import seal_artifact, verify_artifact_hash
from ai_video.production.models import (
    ArtifactReference,
    AssetRegistrySnapshot,
    Character,
    DeliveryProfile,
    ProductionBrief,
    ProductionProject,
    ProjectArtifactRefs,
    RendererPolicy,
    Scene,
    Shot,
    SourceReference,
    Story,
    Storyboard,
)
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter


_ZERO_HASH = "0" * 64


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _canonical_yaml_bytes(model: object) -> bytes:
    return yaml.safe_dump(
        model.model_dump(mode="json"),
        sort_keys=False,
        allow_unicode=True,
    ).encode("utf-8")


def _prepared(path: Path, model: object) -> PreparedArtifact:
    payload = _canonical_yaml_bytes(model)
    return PreparedArtifact(
        relative_path=path,
        payload=payload,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )


def _reference(model: object, path: Path) -> ArtifactReference:
    return ArtifactReference(
        artifact_id=model.artifact_id,
        revision=model.revision,
        content_hash=model.content_hash,
        path=path,
    )


@dataclass(frozen=True)
class CompiledEcommerceProductionProject:
    handoff_id: str
    project: ProductionProject
    registry: AssetRegistrySnapshot
    artifacts: tuple[PreparedArtifact, ...]
    brief: ProductionBrief
    story: Story
    characters: tuple[Character, ...]
    scenes: tuple[Scene, ...]
    storyboard: Storyboard
    shots: tuple[Shot, ...]


def _validate_handoff_bindings(handoff: EcommerceProductionHandoff) -> None:
    proposals = handoff.artifact_proposals
    artifacts = (
        proposals.brief,
        proposals.story,
        *proposals.characters,
        *proposals.scenes,
        proposals.storyboard,
        *proposals.shots,
    )
    if any(not verify_artifact_hash(item) for item in artifacts):
        raise _invalid("Ecommerce artifact proposal hash is invalid.")

    layout = handoff.layout_plan
    if tuple(item.scene_id for item in proposals.scenes) != tuple(
        item.scene_id for item in layout.scenes
    ):
        raise _invalid("Ecommerce layout scenes do not match artifact proposals.")
    if tuple(item.shot_id for item in proposals.shots) != tuple(
        item.shot_id for item in layout.shots
    ):
        raise _invalid("Ecommerce layout Shots do not match artifact proposals.")
    scenes_by_id = {item.scene_id: item for item in proposals.scenes}
    for layout_scene in layout.scenes:
        scene = scenes_by_id[layout_scene.scene_id]
        if (
            scene.location != layout_scene.location
            or scene.time != layout_scene.time
            or scene.mood != layout_scene.mood
            or scene.participant_ids != layout_scene.participant_ids
            or scene.continuity_constraints != layout_scene.continuity_constraints
        ):
            raise _invalid(
                "Ecommerce layout scene semantics do not match artifact proposals.",
                layout_scene.scene_id,
            )
    shots_by_id = {item.shot_id: item for item in proposals.shots}
    for layout_shot in layout.shots:
        shot = shots_by_id[layout_shot.shot_id]
        if (
            shot.scene_id != layout_shot.scene_id
            or shot.character_ids != layout_shot.character_ids
            or shot.visual_strategy is not layout_shot.visual_strategy
            or shot.continuity_constraints != layout_shot.continuity_constraints
            or shot.composition_directives != layout_shot.composition_directives
        ):
            raise _invalid(
                "Ecommerce layout Shot semantics do not match artifact proposals.",
                layout_shot.shot_id,
            )

    plan = handoff.ad_creative_plan_proposal
    truth_source_ids = tuple(item.source_id for item in handoff.product_truth.sources)
    claim_ids = tuple(item.claim_id for item in handoff.product_truth.allowed_claims)
    if plan.product_truth_source_ids != truth_source_ids:
        raise _invalid("Ecommerce AdCreativePlan truth sources do not match Product Truth.")
    if plan.claim_reference_ids != claim_ids:
        raise _invalid("Ecommerce AdCreativePlan claims do not match Product Truth.")
    visual = handoff.visual_system_profile
    typography = {item.token_id: item for item in visual.typography_tokens}
    role_bindings = {
        item.role: typography[item.typography_token_id]
        for item in visual.role_bindings
    }
    layout_shot_ids = {item.shot_id for item in layout.shots}
    for treatment in layout.graphic_treatments:
        token = role_bindings.get(treatment.role)
        if token is None:
            raise _invalid(
                "Ecommerce graphic role has no visual-system typography binding.",
                treatment.graphic_id,
            )
        if (
            treatment.shot_id not in layout_shot_ids
            or treatment.safe_area != visual.safe_area
            or treatment.font_size_px != token.font_size_px
            or treatment.font_weight != token.font_weight
            or treatment.letter_spacing_px != token.letter_spacing_px
            or treatment.text_color != token.text_color
            or treatment.background_color != token.background_color
            or not set(treatment.brand_token_ids).issubset(visual.brand_token_ids)
        ):
            raise _invalid(
                "Ecommerce graphic treatment drifts from the visual system.",
                treatment.graphic_id,
            )
    if plan.graphic_treatments != layout.graphic_treatments:
        raise _invalid("Ecommerce graphic treatments do not match the layout plan.")
    if plan.product_presentations != layout.product_presentations:
        raise _invalid("Ecommerce product presentations do not match the layout plan.")
    if (
        plan.protagonist_continuity_policy.protagonist_ids
        != layout.protagonist_ids
    ):
        raise _invalid("Ecommerce protagonist identity does not match the layout plan.")
    character_ids = {item.character_id for item in proposals.characters}
    if not set(layout.protagonist_ids).issubset(character_ids):
        raise _invalid("Ecommerce protagonist is missing from Character proposals.")
    if tuple((item.beat_id, item.role) for item in plan.ad_arc) != tuple(
        (item.beat_id, item.role) for item in layout.beat_roles
    ):
        raise _invalid("Ecommerce ad beats do not match the layout plan.")
    if any(
        not set(item.shot_ids).issubset(layout_shot_ids) for item in plan.ad_arc
    ):
        raise _invalid("Ecommerce ad beat references a Shot outside the layout plan.")
    shot_acceptance = {
        item.subject_id
        for item in handoff.acceptance_requirements
        if item.scope == "SHOT"
    }
    final_acceptance = tuple(
        item
        for item in handoff.acceptance_requirements
        if item.scope == "FINAL_OUTPUT"
    )
    if shot_acceptance != layout_shot_ids or not final_acceptance:
        raise _invalid(
            "Ecommerce acceptance requirements must cover every Shot and final output."
        )
    if any(item.rights_status != "CONFIRMED" for item in handoff.asset_requirements):
        raise _invalid("Ecommerce asset rights are not confirmed.")

    requirements = {
        item.requirement_id: item for item in handoff.runtime_requirements
    }
    expected_evidence = (
        handoff.delivery_profile.profile_id,
        handoff.visual_system_profile.profile_id,
        handoff.layout_plan.layout_plan_id,
    )
    resolved_ids: set[str] = set()
    for resolution in handoff.compile_profile.requirement_resolutions:
        requirement = requirements.get(resolution.requirement_id)
        if (
            requirement is None
            or requirement.capability != resolution.capability
            or resolution.evidence_ids != expected_evidence
        ):
            raise _invalid(
                "Ecommerce compile requirement resolution is not exact.",
                resolution.requirement_id,
            )
        resolved_ids.add(resolution.requirement_id)
    unresolved = [
        item.requirement_id
        for item in handoff.runtime_requirements
        if item.classification != "SUPPORTED_CURRENTLY"
        and item.requirement_id not in resolved_ids
    ]
    if handoff.unsupported_gaps or unresolved:
        gap_ids = [item.gap_id for item in handoff.unsupported_gaps]
        raise _invalid(
            "Ecommerce handoff contains unresolved runtime capability gaps.",
            f"requirements={sorted(unresolved)}; gaps={sorted(gap_ids)}",
        )


def compile_ecommerce_production_handoff(
    handoff: EcommerceProductionHandoff,
    *,
    expected_project_id: str,
) -> CompiledEcommerceProductionProject:
    """Compile one sealed handoff without reading or mutating Production state."""

    if not expected_project_id.strip():
        raise _invalid("Expected Ecommerce project identity is required.")
    _validate_handoff_bindings(handoff)
    proposals = handoff.artifact_proposals

    brief_path = Path("creative/brief.yaml")
    story_path = Path("creative/story.yaml")
    storyboard_path = Path("creative/storyboard.yaml")
    character_paths = tuple(
        Path(f"creative/characters/{item.content_hash}.yaml")
        for item in proposals.characters
    )
    scene_paths = tuple(
        Path(f"creative/scenes/{item.content_hash}.yaml") for item in proposals.scenes
    )
    shot_paths = tuple(
        Path(f"creative/shots/{item.content_hash}.yaml") for item in proposals.shots
    )
    refs = ProjectArtifactRefs(
        brief=_reference(proposals.brief, brief_path),
        story=_reference(proposals.story, story_path),
        characters=tuple(
            _reference(item, path)
            for item, path in zip(proposals.characters, character_paths, strict=True)
        ),
        scenes=tuple(
            _reference(item, path)
            for item, path in zip(proposals.scenes, scene_paths, strict=True)
        ),
        storyboard=_reference(proposals.storyboard, storyboard_path),
        shots=tuple(
            _reference(item, path)
            for item, path in zip(proposals.shots, shot_paths, strict=True)
        ),
    )
    project_provenance = (
        SourceReference(
            kind="derived",
            reference=f"ecommerce-handoff:{handoff.handoff_id}",
            content_hash=handoff.handoff_id,
        ),
        SourceReference(
            kind="derived",
            reference=f"ecommerce-compile-profile:{handoff.compile_profile.profile_id}",
            content_hash=handoff.compile_profile.profile_id,
        ),
    )
    project = seal_artifact(
        ProductionProject(
            artifact_id=f"project-{expected_project_id}",
            revision=1,
            content_hash=_ZERO_HASH,
            creation_receipt_id=f"ecommerce-compile-{handoff.handoff_id}",
            source_provenance=project_provenance,
            project_id=expected_project_id,
            title=proposals.brief.title,
            default_language=proposals.brief.language,
            delivery_profile=DeliveryProfile(
                width=handoff.delivery_profile.width,
                height=handoff.delivery_profile.height,
                fps=handoff.delivery_profile.fps,
                codec_profile=handoff.delivery_profile.codec_profile,
            ),
            renderer_policy=RendererPolicy(),
            artifacts=refs,
        )
    )
    registry = AssetRegistrySnapshot(
        schema_version="2.0",
        revision_id=_ZERO_HASH,
        content_hash=_ZERO_HASH,
        assets=(),
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    artifacts = (
        _prepared(brief_path, proposals.brief),
        _prepared(story_path, proposals.story),
        *(
            _prepared(path, item)
            for item, path in zip(proposals.characters, character_paths, strict=True)
        ),
        *(
            _prepared(path, item)
            for item, path in zip(proposals.scenes, scene_paths, strict=True)
        ),
        _prepared(storyboard_path, proposals.storyboard),
        *(
            _prepared(path, item)
            for item, path in zip(proposals.shots, shot_paths, strict=True)
        ),
    )
    return CompiledEcommerceProductionProject(
        handoff_id=handoff.handoff_id,
        project=project,
        registry=registry,
        artifacts=tuple(sorted(artifacts, key=lambda item: item.relative_path.as_posix())),
        brief=proposals.brief,
        story=proposals.story,
        characters=proposals.characters,
        scenes=proposals.scenes,
        storyboard=proposals.storyboard,
        shots=proposals.shots,
    )


def bootstrap_ecommerce_production_project(
    project_root: Path,
    *,
    attempt_id: str,
    compiled: CompiledEcommerceProductionProject,
):
    """Delegate initial mutation and exact replay to the canonical committer."""

    return ProductionStateCommitter(project_root).bootstrap_initial_state(
        attempt_id=attempt_id,
        project=compiled.project,
        registry=compiled.registry,
        artifacts=compiled.artifacts,
    )


__all__ = [
    "CompiledEcommerceProductionProject",
    "bootstrap_ecommerce_production_project",
    "compile_ecommerce_production_handoff",
]
