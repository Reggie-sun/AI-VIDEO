"""Derive named Vidu subjects only from sealed canonical artifacts and inputs."""

import hashlib

from ai_video.production.video_subjects import VideoSubjectBinding


def derive_vidu_subjects(requirement, bound) -> tuple[VideoSubjectBinding, ...]:
    if bound.mode.value != "reference_to_video" or requirement.requirement_hash != bound.requirement_hash:
        raise ValueError("named subjects require the same sealed R2V requirement")
    if (requirement.scene.scene_id != requirement.target_shot.scene_id
            or any(c.character_id not in requirement.target_shot.character_ids for c in requirement.characters)):
        raise ValueError("subject artifacts must belong to the canonical Shot")
    owners = {("character", c.character_id): c for c in requirement.characters}
    owners[("scene", requirement.scene.scene_id)] = requirement.scene
    grouped = {}
    evidence = {a.asset_id: a for a in requirement.asset_evidence}
    for role, asset in zip(bound.binding_roles, bound.input_assets, strict=True):
        key = (asset.canonical_owner_kind, asset.canonical_owner_id)
        owner = owners.get(key)
        allowed = (owner.reference_asset_ids if key[0] == "character"
                   else owner.visual_reference_asset_ids) if owner is not None else ()
        semantic = evidence.get(asset.asset_id)
        if (role != "reference" or owner is None or asset.asset_id not in allowed
                or asset.source_registry_revision_id != bound.lifecycle.base_registry.revision_id
                or asset.canonical_owner_content_hash != owner.content_hash
                or semantic is None or semantic.asset_sha256 != asset.asset_sha256
                or semantic.canonical_owner_id != asset.canonical_owner_id
                or semantic.canonical_owner_content_hash != owner.content_hash
                or semantic.role.value != ("identity" if key[0] == "character" else "scene")):
            raise ValueError("subject reference has no exact canonical owner and membership")
        grouped.setdefault(key, []).append(asset.asset_id)
    if not grouped:
        raise ValueError("named subjects require registered canonical references")
    speakers = {s.speaker_id: s for s in requirement.voice_routing.speakers} if requirement.voice_routing else {}
    subjects = []
    for (kind, owner_id), asset_ids in grouped.items():
        speaker = speakers.get(owner_id) if kind == "character" else None
        subjects.append(VideoSubjectBinding(
            name=("char_" if kind == "character" else "scene_") + hashlib.sha256(owner_id.encode()).hexdigest()[:16],
            canonical_owner_kind=kind, canonical_owner_id=owner_id,
            canonical_owner_content_hash=owners[(kind, owner_id)].content_hash,
            image_asset_ids=tuple(sorted(asset_ids)),
            voice_id=speaker.voice_id if speaker else None,
            voice_reference_asset_id=speaker.reference_asset_id if speaker else None,
            voice_reference_sha256=speaker.reference_sha256 if speaker else None,
        ))
    if any(s.speaker_id not in {item.canonical_owner_id for item in subjects if item.canonical_owner_kind == "character"}
           for s in speakers.values()):
        raise ValueError("dialogue speaker requires its own canonical image subject")
    return tuple(sorted(subjects, key=lambda s: s.name))


def validate_vidu_subjects(requirement, bound, subjects) -> None:
    if tuple(subjects) != derive_vidu_subjects(requirement, bound):
        raise ValueError("named subject projection differs from canonical inputs")


def validate_vidu_subject_prompt(requirement, bound, subjects, prompt_text) -> None:
    from ai_video.production._vidu_prompt import compile_vidu_subject_prompt

    validate_vidu_subjects(requirement, bound, subjects)
    prompt = compile_vidu_subject_prompt(requirement, bound, subjects)
    if prompt.outcome != "compiled" or prompt.prompt_text != prompt_text:
        raise ValueError("named subject prompt differs from the canonical projection")
