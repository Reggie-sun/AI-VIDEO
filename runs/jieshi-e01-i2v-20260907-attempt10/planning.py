"""Exact approved S01 repair planning through the existing planner."""
import json
from pathlib import Path
from ai_video.planning import AssetRole, AvailableAsset, VideoPlanner, VideoPlanningRequest, require_current_video_plan
from ai_video.production.video_requirement import ProviderNeutralGenerationIntentProjection, SemanticReferenceRole
RUN = Path(__file__).resolve().parent
SOURCE_RUN = RUN.parent / "jieshi-e01-i2v-20260906-attempt01"
SOURCE_SHA = "4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb"

def planning(loaded, source):
    prior = VideoPlanningRequest.model_validate_json((SOURCE_RUN / "planning-request-v2.json").read_bytes())
    shot = loaded.shots[0]
    intent_data = {key: getattr(prior.generation_intent, key) for key in type(prior.generation_intent).model_fields if key != "projection_hash"}
    # Raster is sealed by output_requirement.resolution_label and measured after fetch.
    # The compiler does not implement the separate quality.minimum_raster hint.
    intent_data["quality_need"] = prior.generation_intent.quality_need.model_copy(update={"minimum_raster": None})
    intent_data["audio_need"] = type(prior.generation_intent.audio_need)("required")
    intent_data["semantic_reference_roles"] = (SemanticReferenceRole.FIRST_FRAME, SemanticReferenceRole.LAST_FRAME)
    endpoint_role = next(r for r in shot.required_asset_roles if r.role == "last_frame")
    endpoint, = (a for a in loaded.registry.assets if a.asset_id in endpoint_role.asset_ids)
    if endpoint.sha256 != "d9a21860e91cadc7cf4cfe0ce74a44b57c2aa6d600b8c8cc06dc17e4fb4cd1da":
        raise RuntimeError("Approved repaired endpoint must be canonically imported before planning")
    gi = prior.generation_intent.generation_intent
    draft = json.loads((RUN / "request-draft.json").read_text())
    scene = gi.scene_continuity.model_copy(update={"state_constraints": (draft["prompt_draft"],), "time_of_day": "深夜"})
    intent_data["generation_intent"] = gi.model_copy(update={
        "scene_continuity": scene,
        "subject_action": gi.subject_action.model_copy(update={"progression": draft["action_progression"]}),
        "camera_intent": gi.camera_intent.model_copy(update={
            "stability": draft["camera_stability"], "framing_intent": draft["camera_framing"],
        }),
    })
    intent = ProviderNeutralGenerationIntentProjection.create(**intent_data)
    data = prior.model_dump()
    data.update(
        request_id="jieshi-e01-s01-i2v-plan-attempt10",
        generation_intent=intent,
        production_policy=prior.production_policy.model_copy(update={"remote_authorized": True, "budget_authorized": True}),
        target_shot=shot,
        available_assets=(AvailableAsset(
            role=AssetRole.APPROVED_KEYFRAME, asset_id=source.asset_id,
            asset_sha256=source.sha256, canonical_owner_id=shot.shot_id,
            canonical_owner_content_hash=shot.content_hash, mime_type=source.mime_type,
            width=941, height=1672, size_bytes=source.size_bytes,
        ), AvailableAsset(
            role=AssetRole.LAST_FRAME, asset_id=endpoint.asset_id,
            asset_sha256=endpoint.sha256, canonical_owner_id=shot.shot_id,
            canonical_owner_content_hash=shot.content_hash, mime_type=endpoint.mime_type,
            width=endpoint.width, height=endpoint.height, size_bytes=endpoint.size_bytes,
        )),
        shot_intent_evidence=prior.shot_intent_evidence.model_copy(update={
            "target_shot_content_hash": shot.content_hash,
        }),
    )
    data.pop("request_content_hash")
    request = VideoPlanningRequest.create(**data)
    plan = VideoPlanner().plan(request)
    verified = require_current_video_plan(current_request=request, plan=plan)
    return request, plan, verified

