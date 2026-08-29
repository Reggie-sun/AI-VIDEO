from __future__ import annotations

import hashlib

import pytest

from ai_video.production._h3_prompt import (
    H3PromptCompilation,
    H3PromptUnsupported,
    compile_h3_prompt,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import (
    CapabilityNeed,
    CameraAmplitudeClass,
    CameraMotionContract,
    CameraMovementKind,
    CameraMotionEndState,
    CameraMotionStartState,
    CameraSpeedClass,
    CameraSubjectRelation,
    ConditioningLane,
    ContinuityMode,
    DialogueIntent,
    GenerationMode,
    IdentityContinuity,
    IdentityPreservation,
    MusicIntent,
    Pacing,
    ProviderNeutralVideoRequirement,
    SceneContinuity,
)
from tests.test_production_video_intent_validation import (
    _compatible_fl2va,
    _complete_intent,
)
from tests.test_production_video_requirement import _requirement_kwargs


def _requirement(*, movement: CameraMovementKind = CameraMovementKind.DOLLY_IN):
    payload = _requirement_kwargs()
    payload.pop("contract_version")
    intent = _complete_intent().model_copy(
        update={
            "pacing": Pacing(shot_duration_seconds=3.0),
            "primary_camera_motion": CameraMotionContract(
                movement_kind=movement,
                direction="forward" if movement is not CameraMovementKind.LOCKED else "none",
                amplitude_class=CameraAmplitudeClass.SUBTLE,
                speed_class=(
                    CameraSpeedClass.VERY_SLOW
                    if movement is CameraMovementKind.LOCKED
                    else CameraSpeedClass.SLOW
                ),
                start_motion_state=CameraMotionStartState.STATIONARY,
                end_motion_state=CameraMotionEndState.SETTLED,
            )
        }
    )
    payload["generation_intent"] = intent
    payload["conditioning_compatibility"] = _compatible_fl2va().model_copy(
        update={
            "lane": ConditioningLane.I2VA,
            "first_anchor_id": "frame-shot-1",
            "last_anchor_id": None,
            "available_duration_seconds": 3.0,
        }
    )
    payload["generation_mode"] = GenerationMode.IMAGE_TO_VIDEO
    payload["generation_intent_hash"] = canonical_sha256(
        {
            "schema": "provider-neutral-generation-intent/2",
            "generation_intent": intent.model_dump(mode="json"),
        }
    )
    payload["quality_need"] = payload["quality_need"].model_copy(
        update={
            "minimum_raster": None,
            "minimum_codec": None,
            "native_enforcement_required": False,
        }
    )
    return ProviderNeutralVideoRequirement.create(**payload)


def test_h3_prompt_is_exact_single_take_three_field_grammar() -> None:
    result = compile_h3_prompt(_requirement())

    assert isinstance(result, H3PromptCompilation)
    prompt = result.prompt_text
    assert prompt.count("[Shot 1]") == 1
    assert "[Shot 2]" not in prompt
    assert [
        line.split(":", 1)[0]
        for line in prompt.splitlines()
        if line.startswith(
            (
                "integrated_multimodal_description:",
                "overall_soundscape:",
                "non_diegetic_music:",
            )
        )
    ] == [
        "integrated_multimodal_description",
        "overall_soundscape",
        "non_diegetic_music",
    ]
    assert "dolly in with subtle amplitude at slow speed" in prompt
    assert "terminal motion state settled" in prompt
    assert prompt.endswith("non_diegetic_music: none")
    assert result.prompt_sha256 == hashlib.sha256(prompt.encode("utf-8")).hexdigest()


@pytest.mark.parametrize("camera_movement", ("locked", "locked-off"))
def test_h3_prompt_compiles_complete_legacy_t2v_without_neutral_field_leakage(
    camera_movement: str,
) -> None:
    current = _requirement()
    intent = current.generation_intent.model_copy(
        update={
            "identity_continuity": IdentityContinuity(
                character_ids=tuple(
                    character.character_id for character in current.characters
                ),
                preservation=IdentityPreservation.EXACT,
            ),
            "scene_continuity": SceneContinuity(
                scene_id=current.scene.scene_id,
                time_of_day="night",
                mood=(
                    '{"conflict_and_stakes":"guarded trust",'
                    '"objective":"the hero proves they will stay"}'
                ),
                state_constraints=(
                    '{"axis_crossing_authorized":false,"screen_axis":"stable"}',
                    "future shot reveals the key and asks whether he will stay",
                ),
            ),
            "camera_intent": current.generation_intent.camera_intent.model_copy(
                update={"movement": camera_movement}
            ),
            "primary_camera_motion": None,
            "camera_subject_relation": None,
        }
    )
    payload = current.model_dump(
        mode="python",
        exclude={"requirement_id", "requirement_hash"},
    )
    payload.update(
        contract_version="provider-neutral-video-requirement/1",
        generation_mode=GenerationMode.TEXT_TO_VIDEO,
        continuity_mode=ContinuityMode.NONE,
        generation_intent=intent,
        generation_intent_hash=canonical_sha256(intent.model_dump(mode="json")),
        conditioning_compatibility=None,
        asset_evidence=(),
        semantic_reference_roles=(),
        capability_need=CapabilityNeed(),
    )

    result = compile_h3_prompt(ProviderNeutralVideoRequirement.create(**payload))

    assert isinstance(result, H3PromptCompilation)
    assert result.prompt_text.count("[Shot 1]") == 1
    assert len(result.prompt_text.splitlines()) == 3
    assert result.prompt_text.count("locked-off camera") == 1
    assert "no visible text, captions, or subtitles" in result.prompt_text
    assert "no speech, no dialogue, no narration, and no voices" in result.prompt_text
    assert "guarded trust" not in result.prompt_text
    assert "the hero proves they will stay" not in result.prompt_text
    assert "future shot reveals the key" not in result.prompt_text
    assert "identity preservation" not in result.prompt_text
    assert "identity characters" not in result.prompt_text
    assert "scene continuity" not in result.prompt_text
    assert f"scene {current.scene.scene_id};" not in result.prompt_text
    assert "{" not in result.prompt_text
    assert "}" not in result.prompt_text
    assert "generation_mode=" not in result.prompt_text
    assert "identity_characters=" not in result.prompt_text
    assert "scene_mood=" not in result.prompt_text
    assert "scene_constraints=" not in result.prompt_text
    assert f"shot intent {current.target_shot.intent}" in result.prompt_text
    assert "performance trigger receives the product offer" in result.prompt_text
    assert "pacing unspecified; tempo unspecified" in result.prompt_text

    changed_intent = intent.model_copy(
        update={
            "subject_action": intent.subject_action.model_copy(
                update={"progression": "The subject completes a different action."}
            )
        }
    )
    changed_payload = dict(payload)
    changed_payload.update(
        generation_intent=changed_intent,
        generation_intent_hash=canonical_sha256(
            changed_intent.model_dump(mode="json")
        ),
    )
    changed = compile_h3_prompt(
        ProviderNeutralVideoRequirement.create(**changed_payload)
    )
    assert isinstance(changed, H3PromptCompilation)
    assert changed.prompt_text != result.prompt_text
    assert "The subject completes a different action." in changed.prompt_text


def test_h3_legacy_prompt_uses_dialogue_intent_as_only_speech_owner() -> None:
    current = _requirement()
    exact_dialogue = "钥匙还在。回去，一起开门。"
    intent = current.generation_intent.model_copy(
        update={
            "open_state": current.generation_intent.open_state.model_copy(
                update={
                    "state_text": (
                        "Full legacy visual instruction says exactly "
                        f"{exact_dialogue} with rain and no music."
                    )
                }
            ),
            "dialogue_intent": DialogueIntent(
                mode="dialogue",
                language="zh-CN",
                speaker_id="hero",
                verbatim_text=exact_dialogue,
                start_seconds=0.5,
                end_seconds=2.0,
                on_screen=True,
                response_obligation="listener visibly attends",
                lip_sync_required=True,
            ),
            "primary_camera_motion": None,
            "camera_subject_relation": None,
        }
    )
    payload = current.model_dump(
        mode="python",
        exclude={"requirement_id", "requirement_hash"},
    )
    payload.update(
        contract_version="provider-neutral-video-requirement/1",
        generation_mode=GenerationMode.TEXT_TO_VIDEO,
        continuity_mode=ContinuityMode.NONE,
        generation_intent=intent,
        generation_intent_hash=canonical_sha256(intent.model_dump(mode="json")),
        conditioning_compatibility=None,
        asset_evidence=(),
        semantic_reference_roles=(),
        capability_need=CapabilityNeed(),
    )

    result = compile_h3_prompt(ProviderNeutralVideoRequirement.create(**payload))

    assert isinstance(result, H3PromptCompilation)
    assert result.prompt_text.count(exact_dialogue) == 1
    assert "Full legacy visual instruction" not in result.prompt_text
    assert f"speaker hero says once <d>[Chinese]{exact_dialogue}</d>" in result.prompt_text


@pytest.mark.parametrize("language", (None, "ja-JP", "es-ES", "ar"))
def test_h3_legacy_prompt_requires_supported_sealed_dialogue_language(
    language: str | None,
) -> None:
    current = _requirement()
    intent = current.generation_intent.model_copy(
        update={
            "dialogue_intent": DialogueIntent(
                mode="dialogue",
                language=language,
                speaker_id="hero",
                verbatim_text="Exact speech.",
                start_seconds=0.5,
                end_seconds=2.0,
                on_screen=True,
                response_obligation="listener attends",
            ),
            "primary_camera_motion": None,
            "camera_subject_relation": None,
        }
    )
    payload = current.model_dump(
        mode="python",
        exclude={"requirement_id", "requirement_hash"},
    )
    payload.update(
        contract_version="provider-neutral-video-requirement/1",
        generation_mode=GenerationMode.TEXT_TO_VIDEO,
        continuity_mode=ContinuityMode.NONE,
        generation_intent=intent,
        generation_intent_hash=canonical_sha256(intent.model_dump(mode="json")),
        conditioning_compatibility=None,
        asset_evidence=(),
        semantic_reference_roles=(),
        capability_need=CapabilityNeed(),
    )

    result = compile_h3_prompt(ProviderNeutralVideoRequirement.create(**payload))

    assert isinstance(result, H3PromptUnsupported)
    assert result.unsupported_field_paths == (
        "generation_intent.dialogue_intent.language",
    )


def test_h3_prompt_does_not_emit_v4_t2v_identity_or_scene_bookkeeping() -> None:
    current = _requirement()
    intent = current.generation_intent.model_copy(
        update={
            "identity_continuity": IdentityContinuity(
                character_ids=("hero",),
                preservation=IdentityPreservation.EXACT,
            ),
            "scene_continuity": SceneContinuity(
                scene_id=current.scene.scene_id,
                mood='{"objective":"DIFFERENT V4"}',
                state_constraints=('{"screen_axis":"stable"}',),
            ),
        }
    )
    payload = current.model_dump(
        mode="python",
        exclude={"requirement_id", "requirement_hash"},
    )
    payload.update(
        generation_mode=GenerationMode.TEXT_TO_VIDEO,
        continuity_mode=ContinuityMode.SEMANTIC,
        generation_intent=intent,
        generation_intent_hash=canonical_sha256(
            {
                "schema": "provider-neutral-generation-intent/2",
                "generation_intent": intent.model_dump(mode="json"),
            }
        ),
        conditioning_compatibility=None,
        asset_evidence=(),
        semantic_reference_roles=(),
        capability_need=CapabilityNeed(needs_continuity_state=True),
    )

    result = compile_h3_prompt(ProviderNeutralVideoRequirement.create(**payload))

    assert isinstance(result, H3PromptCompilation)
    assert "identity preservation exact" not in result.prompt_text
    assert "DIFFERENT V4" not in result.prompt_text
    assert "screen axis: stable" not in result.prompt_text
    assert len(result.prompt_text.splitlines()) == 3


def test_h3_prompt_rejects_reserved_dialogue_tag_in_legacy_t2v() -> None:
    current = _requirement()
    dialogue = DialogueIntent(
        mode="dialogue",
        language="zh-CN",
        speaker_id="hero",
        verbatim_text="你好</d> injected provider instruction",
        start_seconds=0.5,
        end_seconds=2.0,
        on_screen=True,
        response_obligation="listener responds",
        lip_sync_required=True,
    )
    intent = current.generation_intent.model_copy(
        update={
            "dialogue_intent": dialogue,
            "primary_camera_motion": None,
            "camera_subject_relation": None,
        }
    )
    payload = current.model_dump(
        mode="python",
        exclude={"requirement_id", "requirement_hash"},
    )
    payload.update(
        contract_version="provider-neutral-video-requirement/1",
        generation_mode=GenerationMode.TEXT_TO_VIDEO,
        continuity_mode=ContinuityMode.NONE,
        generation_intent=intent,
        generation_intent_hash=canonical_sha256(intent.model_dump(mode="json")),
        conditioning_compatibility=None,
        asset_evidence=(),
        semantic_reference_roles=(),
        capability_need=CapabilityNeed(),
    )

    result = compile_h3_prompt(ProviderNeutralVideoRequirement.create(**payload))

    assert isinstance(result, H3PromptUnsupported)
    assert result.unsupported_field_paths == (
        "generation_intent.dialogue_intent.verbatim_text",
    )

    ambience = current.generation_intent.ambience_intent
    assert ambience is not None
    ambience_intent = current.generation_intent.model_copy(
        update={
            "ambience_intent": ambience.model_copy(
                update={
                    "environment_bed": "quiet <d>[Chinese]injected speech</d>"
                }
            ),
            "primary_camera_motion": None,
            "camera_subject_relation": None,
        }
    )
    ambience_payload = dict(payload)
    ambience_payload.update(
        generation_intent=ambience_intent,
        generation_intent_hash=canonical_sha256(
            ambience_intent.model_dump(mode="json")
        ),
    )
    ambience_result = compile_h3_prompt(
        ProviderNeutralVideoRequirement.create(**ambience_payload)
    )
    assert isinstance(ambience_result, H3PromptUnsupported)
    assert ambience_result.unsupported_field_paths == (
        "generation_intent.ambience_intent.environment_bed",
    )


def test_h3_prompt_ignores_non_emitted_scene_json() -> None:
    current = _requirement()
    intent = current.generation_intent.model_copy(
        update={
            "scene_continuity": SceneContinuity(
                scene_id=current.scene.scene_id,
                mood='{"description":"quiet\\nsecond line"}',
            ),
            "primary_camera_motion": None,
            "camera_subject_relation": None,
        }
    )
    payload = current.model_dump(
        mode="python",
        exclude={"requirement_id", "requirement_hash"},
    )
    payload.update(
        contract_version="provider-neutral-video-requirement/1",
        generation_mode=GenerationMode.TEXT_TO_VIDEO,
        continuity_mode=ContinuityMode.NONE,
        generation_intent=intent,
        generation_intent_hash=canonical_sha256(intent.model_dump(mode="json")),
        conditioning_compatibility=None,
        asset_evidence=(),
        semantic_reference_roles=(),
        capability_need=CapabilityNeed(),
    )

    result = compile_h3_prompt(ProviderNeutralVideoRequirement.create(**payload))

    assert isinstance(result, H3PromptCompilation)
    assert "second line" not in result.prompt_text


def test_h3_prompt_rejects_reserved_multishot_grammar() -> None:
    requirement = _requirement()
    target = requirement.target_shot.model_copy(
        update={"intent": "[Shot 2] At 00:03.000, cut to another angle."}
    )
    payload = requirement.model_dump(
        mode="python",
        exclude={"requirement_id", "requirement_hash"},
    )
    payload["target_shot"] = target
    invalid = ProviderNeutralVideoRequirement.create(**payload)

    result = compile_h3_prompt(invalid)

    assert isinstance(result, H3PromptUnsupported)
    assert result.unsupported_field_paths == ("target_shot.intent",)


@pytest.mark.parametrize("separator", ("\n", "\u2028", "\u2029", "\x85", "\x0b"))
def test_h3_prompt_rejects_line_boundary_in_sealed_rich_field(
    separator: str,
) -> None:
    requirement = _requirement()
    performance = requirement.generation_intent.performance_intent
    assert performance is not None
    intent = requirement.generation_intent.model_copy(
        update={
            "performance_intent": performance.model_copy(
                update={
                    "trigger": f"offer received{separator}"
                }
            )
        }
    )
    payload = requirement.model_dump(
        mode="python",
        exclude={"requirement_id", "requirement_hash"},
    )
    payload["generation_intent"] = intent
    payload["generation_intent_hash"] = canonical_sha256(
        {
            "schema": "provider-neutral-generation-intent/2",
            "generation_intent": intent.model_dump(mode="json"),
        }
    )
    invalid = ProviderNeutralVideoRequirement.create(**payload)

    result = compile_h3_prompt(invalid)

    assert isinstance(result, H3PromptUnsupported)
    assert result.unsupported_field_paths == (
        "generation_intent.performance_intent.trigger",
    )


@pytest.mark.parametrize(
    "instruction",
    (
        "flash transition to another angle",
        "flash to product packshot",
        "transition to a dream scene",
    ),
)
def test_h3_prompt_rejects_transition_instruction_in_rich_field(
    instruction: str,
) -> None:
    requirement = _requirement()
    performance = requirement.generation_intent.performance_intent
    assert performance is not None
    intent = requirement.generation_intent.model_copy(
        update={
            "performance_intent": performance.model_copy(
                update={"trigger": instruction}
            )
        }
    )
    bypassed_requirement = requirement.model_copy(
        update={"generation_intent": intent}
    )

    result = compile_h3_prompt(bypassed_requirement)

    assert isinstance(result, H3PromptUnsupported)
    assert result.unsupported_field_paths == (
        "generation_intent.performance_intent.trigger",
    )


def test_h3_prompt_rejects_conflicting_legacy_camera_owner() -> None:
    requirement = _requirement()
    intent = requirement.generation_intent.model_copy(
        update={
            "camera_intent": requirement.generation_intent.camera_intent.model_copy(
                update={"movement": "orbit_left"}
            )
        }
    )
    payload = requirement.model_dump(
        mode="python",
        exclude={"requirement_id", "requirement_hash"},
    )
    payload["generation_intent"] = intent
    payload["generation_intent_hash"] = canonical_sha256(
        {
            "schema": "provider-neutral-generation-intent/2",
            "generation_intent": intent.model_dump(mode="json"),
        }
    )
    invalid = ProviderNeutralVideoRequirement.create(**payload)

    result = compile_h3_prompt(invalid)

    assert isinstance(result, H3PromptUnsupported)
    assert result.unsupported_field_paths == (
        "generation_intent.camera_intent.movement",
    )


def test_h3_prompt_serializes_locked_camera_without_motion_strength() -> None:
    result = compile_h3_prompt(_requirement(movement=CameraMovementKind.LOCKED))

    assert isinstance(result, H3PromptCompilation)
    assert "locked-off camera" in result.prompt_text
    assert "locked with" not in result.prompt_text


def test_h3_prompt_preserves_exact_dialogue_bytes_and_sealed_music() -> None:
    requirement = _requirement()
    exact_dialogue = (
        'He said "I\'m ready" — 好。 Literal <d>tag</d>; '
        "cut costs; dissolve one tablet."
    )
    intent = requirement.generation_intent.model_copy(
        update={
            "dialogue_intent": DialogueIntent(
                mode="dialogue",
                language="en-US",
                speaker_id="hero",
                verbatim_text=exact_dialogue,
                start_seconds=0.5,
                end_seconds=2.0,
                on_screen=True,
                response_obligation="elder acknowledges",
                lip_sync_required=True,
            ),
            "music_intent": MusicIntent(
                mode="music",
                instrumentation="muted guzheng",
                tempo_rhythm="72 bpm sparse pulse",
                dynamics="low under dialogue",
            ),
        }
    )
    payload = requirement.model_dump(
        mode="python",
        exclude={"requirement_id", "requirement_hash"},
    )
    payload["generation_intent"] = intent
    payload["generation_intent_hash"] = canonical_sha256(
        {
            "schema": "provider-neutral-generation-intent/2",
            "generation_intent": intent.model_dump(mode="json"),
        }
    )

    result = compile_h3_prompt(ProviderNeutralVideoRequirement.create(**payload))

    assert isinstance(result, H3PromptCompilation)
    assert exact_dialogue in result.prompt_text
    assert f"utf8_bytes={len(exact_dialogue.encode('utf-8'))}" in result.prompt_text
    assert "non_diegetic_music: muted guzheng; 72 bpm sparse pulse; low under dialogue" in result.prompt_text


def test_h3_prompt_rejects_secondary_motion_in_bypassed_relation_model() -> None:
    requirement = _requirement()
    relation = requirement.generation_intent.camera_subject_relation
    assert relation is not None
    relation_payload = relation.model_dump(mode="python")
    relation_payload["end_relation"] = "orbit left around subject"
    bypassed = CameraSubjectRelation.model_construct(**relation_payload)
    intent = requirement.generation_intent.model_copy(
        update={"camera_subject_relation": bypassed}
    )
    bypassed_requirement = requirement.model_copy(
        update={"generation_intent": intent}
    )

    result = compile_h3_prompt(bypassed_requirement)

    assert isinstance(result, H3PromptUnsupported)
    assert result.unsupported_field_paths == (
        "generation_intent.camera_subject_relation.end_relation",
    )
