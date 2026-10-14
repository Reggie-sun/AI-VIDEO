"""Read-only preparation for the existing masked image generation seam."""
from pathlib import Path

from ai_video.production.comfy_image import (
    load_local_image_execution_profile, validate_profile_request_match,
)
from ai_video.production.image import (
    ImageGenerationPreview, ImageGenerationRequest, ImageProviderParameters,
    ImageReferenceBinding,
)
from ai_video.production.image_edit_mask import validate_registered_edit_mask
from ai_video.production.models import AssetType


def prepare_canvas_masked_image(*, loaded, profile_path, artifact_root, attempt_id,
        shot_id, target_asset_role, character_id, character_asset_id, source_asset_id,
        mask_asset_id, prompt_text, seed, negative_prompt_text=""):
    """Bind explicit assets; never generate, invent a mask, or mutate Production."""
    profile = load_local_image_execution_profile(Path(profile_path), artifact_root=Path(artifact_root))
    if profile.lane_id != "qwen_image_edit_2511_masked_local":
        raise ValueError("masked preparation requires the explicit masked image profile")
    if loaded.manifest.active_dependency_graph is None:
        raise ValueError("image workflow requires the initialized canonical dependency graph")
    shot = next(s for s in loaded.shots if s.shot_id == shot_id)
    if not any(r.role == target_asset_role and AssetType.IMAGE in r.allowed_asset_types
               for r in shot.required_asset_roles):
        raise ValueError("target Shot has no selected image asset role")
    character = next(c for c in loaded.characters if c.character_id == character_id)
    scene = next(s for s in loaded.scenes if s.scene_id == shot.scene_id)
    if (character_asset_id not in character.reference_asset_ids
            or source_asset_id not in scene.visual_reference_asset_ids
            or mask_asset_id not in scene.visual_reference_asset_ids):
        raise ValueError("image workflow assets are not selected by current Character/Scene")
    assets = {a.asset_id: a for a in loaded.registry.assets}
    references = []
    for role, creative, aid in (("character", character, character_asset_id),
                                ("scene", scene, source_asset_id),
                                ("edit_mask", scene, mask_asset_id)):
        asset = assets[aid]
        if asset.asset_type != AssetType.IMAGE or asset.mime_type != "image/png":
            raise ValueError("image workflow references must be registered PNG images")
        references.append(ImageReferenceBinding(role=role,
            creative_artifact_id=creative.artifact_id, creative_revision=creative.revision,
            creative_content_hash=creative.content_hash, asset_id=aid, asset_sha256=asset.sha256))
    source = assets[source_asset_id]
    request = ImageGenerationRequest.create(attempt_id=attempt_id, provider_kind="comfyui_local",
        model_id=profile.profile_id, target_shot_id=shot_id, target_asset_role=target_asset_role,
        prompt_text=prompt_text, negative_prompt_text=negative_prompt_text,
        parameters=ImageProviderParameters(seed=seed, width=source.width, height=source.height,
            output_format="png", generation_revision=shot.revision), references=tuple(references),
        base_project=loaded.manifest.active_project, base_registry=loaded.manifest.active_registry,
        base_dependency_graph=loaded.manifest.active_dependency_graph)
    validate_profile_request_match(profile, request)
    validate_registered_edit_mask(request=request, root=loaded.root, registry=loaded.registry)
    preview = ImageGenerationPreview.create(request=request,
        reference_total_bytes=sum(assets[r.asset_id].size_bytes for r in request.references))
    return {"request": request, "preview": preview, "execution_profile": profile,
            "input_validation": "PASS", "runtime_readiness": "NOT_EVALUATED",
            "production_acceptance": "NOT_EVALUATED"}
