"""Verify a supplied planning/context snapshot against current selected artifacts."""
from ai_video.planning import require_current_video_plan


def require_feedback_context(*, loaded, planning_request, video_plan, context, routing_policy, lifecycle):
    projection = require_current_video_plan(current_request=planning_request, plan=video_plan)
    shot = next((x for x in loaded.shots if x.shot_id == context.target_shot_id), None)
    if shot is None or shot != planning_request.target_shot or shot.scene_id != planning_request.scene_context.scene_id:
        raise ValueError("configured planning target is stale")
    characters = tuple(sorted((x for x in loaded.characters if x.character_id in shot.character_ids),
                              key=lambda x: x.character_id))
    if tuple(sorted(planning_request.character_context, key=lambda x: x.character_id)) != characters:
        raise ValueError("configured planning characters are stale")
    scene = next((x for x in loaded.scenes if x.scene_id == shot.scene_id), None)
    if scene != planning_request.scene_context:
        raise ValueError("configured planning scene is stale")
    if (context.target_shot_revision != shot.revision or context.target_shot_content_hash != shot.content_hash
            or context.activated_shot != shot
            or context.storyboard_content_hash != loaded.storyboard.content_hash
            or context.storyboard_revision != loaded.storyboard.revision
            or context.selected_registry_revision_id != loaded.registry.revision_id
            or context.scene_content_hash != scene.content_hash
            or lifecycle.base_project != loaded.manifest.active_project
            or lifecycle.base_registry != loaded.manifest.active_registry
            or lifecycle.base_dependency_graph != loaded.manifest.active_dependency_graph):
        raise ValueError("configured routing or lifecycle lineage is stale")
    return {"projection": projection, "context": context,
            "policy": routing_policy, "lifecycle": lifecycle}
