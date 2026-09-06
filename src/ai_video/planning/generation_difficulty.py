"""Canonical, relational Shot facts; no model-success probability."""

from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import VerifiedGenerationRequirementProjection


def generation_difficulty(projection: VerifiedGenerationRequirementProjection) -> dict:
    projection = VerifiedGenerationRequirementProjection.model_validate(
        projection.model_dump(mode="python")
    )
    requirement = projection.requirement
    intent = requirement.generation_intent
    facts = {
        "action_and_time": (intent.subject_action.model_dump(mode="json"),
                            intent.motion_envelope.model_dump(mode="json"),
                            intent.pacing.model_dump(mode="json")),
        "performance": intent.performance_intent,
        "camera_and_space": (intent.camera_intent, intent.camera_endpoint,
                             intent.camera_subject_relation, intent.space_continuity),
        "continuity_and_identity": (requirement.continuity_mode,
                                    intent.identity_continuity, intent.scene_continuity),
        "dialogue_and_sound": (intent.dialogue_intent, intent.ambience_intent,
                               intent.music_intent, requirement.audio_need),
        "output_and_viewing": (requirement.output_need, requirement.quality_need),
        "accepted_constraints": requirement.target_shot.continuity_constraints,
    }
    # JSON projection uses the existing canonical requirement serialization;
    # coupled facts remain grouped rather than converted into a scalar score.
    from pydantic import TypeAdapter

    payload = TypeAdapter(dict).dump_python(facts, mode="json")
    return {"facts": payload, "facts_hash": canonical_sha256(
                requirement.model_dump(mode="json", exclude={"requirement_id", "requirement_hash"})),
            "unknowns": ("semantic difficulty observations require sourced evidence",
                         "readiness and planner confidence are not quality estimates")}
