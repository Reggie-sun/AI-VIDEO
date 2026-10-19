from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import Character
from ai_video.production.performance_direction import (
    CharacterPerformanceDirection,
    PerformanceBeat,
    performance_direction_issues,
    render_performance_direction,
)
from ai_video.production.video_requirement import (
    CapabilityNeed,
    ConditioningLane,
    ExpressionStrength,
    GenerationMode,
    PerformanceIntent,
    ProviderNeutralVideoRequirement,
)
from test_production_video_intent_validation import (
    _complete_intent,
    _compatible_fl2va,
)
from test_production_video_requirement import _requirement_kwargs


def _beat(phase: str = "response", **changes: str) -> PerformanceBeat:
    values = {
        "phase": phase,
        "trigger": "the announcement names the character",
        "emotion": "uncertain recognition",
        "intensity": "subtle",
        "facial_expression": "brows draw together, lips remain gently closed",
        "gaze_target": "the empty reflection beside the window",
        "breathing": "one shallow inhale, then a held breath",
        "body_behavior": "the shoulders tense slightly, hands remain still",
    }
    values.update(changes)
    return PerformanceBeat(**values)


def _direction(
    character_id: str = "hero",
    *,
    screen_identity: str = "the young passenger in a dark jacket",
    role: str = "principal",
    visibility: str = "visible",
    offscreen_reason: str | None = None,
    beats: tuple[PerformanceBeat, ...] | None = None,
) -> CharacterPerformanceDirection:
    if beats is None:
        beats = (_beat(),)
    return CharacterPerformanceDirection(
        character_id=character_id,
        screen_identity=screen_identity,
        role=role,
        visibility=visibility,
        offscreen_reason=offscreen_reason,
        beats=beats,
    )


def _character(character_id: str, name: str) -> Character:
    return Character(
        artifact_id=f"character-{character_id}",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id=f"receipt-{character_id}",
        source_provenance=({"kind": "user_input", "reference": "fixture"},),
        character_id=character_id,
        name=name,
        identity="authored identity",
        appearance_bible="ordinary clothing and silhouette",
    )


def _rich_requirement(
    directions: tuple[CharacterPerformanceDirection, ...],
) -> ProviderNeutralVideoRequirement:
    payload = _requirement_kwargs()
    payload.pop("contract_version")
    intent = _complete_intent()
    performance = intent.performance_intent
    assert performance is not None
    intent = intent.model_copy(
        update={
            "performance_intent": performance.model_copy(
                update={"character_directions": directions}
            ),
            "camera_intent": intent.camera_intent.model_copy(
                update={"expression_strength": ExpressionStrength.SEMANTIC_PROMPT_ALLOWED}
            ),
            "pacing": intent.pacing.model_copy(update={"shot_duration_seconds": 3.0}),
        }
    )
    payload["generation_intent"] = intent
    payload["generation_intent_hash"] = canonical_sha256(
        {
            "schema": "provider-neutral-generation-intent/2",
            "generation_intent": intent.model_dump(mode="json"),
        }
    )
    payload["conditioning_compatibility"] = _compatible_fl2va().model_copy(
        update={
            "lane": ConditioningLane.I2VA,
            "first_anchor_id": "frame-shot-1",
            "last_anchor_id": None,
            "available_duration_seconds": 3.0,
        }
    )
    payload["generation_mode"] = GenerationMode.IMAGE_TO_VIDEO
    payload["quality_need"] = payload["quality_need"].model_copy(
        update={
            "minimum_raster": None,
            "minimum_codec": None,
            "native_enforcement_required": False,
        }
    )
    return ProviderNeutralVideoRequirement.create(**payload)


def _legacy_t2va_requirement(
    directions: tuple[CharacterPerformanceDirection, ...],
) -> ProviderNeutralVideoRequirement:
    payload = _requirement_kwargs()
    payload.pop("contract_version")
    intent = _complete_intent()
    performance = intent.performance_intent
    assert performance is not None
    intent = intent.model_copy(
        update={
            "performance_intent": performance.model_copy(
                update={"character_directions": directions}
            ),
            "primary_camera_motion": None,
            "camera_subject_relation": None,
            "pacing": intent.pacing.model_copy(update={"shot_duration_seconds": 3.0}),
        }
    )
    payload.update(
        generation_intent=intent,
        generation_intent_hash=canonical_sha256(intent.model_dump(mode="json")),
        generation_mode=GenerationMode.TEXT_TO_VIDEO,
        continuity_mode="none",
        asset_evidence=(),
        semantic_reference_roles=(),
        capability_need=CapabilityNeed(),
    )
    return ProviderNeutralVideoRequirement.create(**payload)


def test_empty_directions_keep_the_legacy_six_field_hash() -> None:
    legacy = _complete_intent().performance_intent
    assert legacy is not None
    explicit_empty = legacy.model_copy(update={"character_directions": ()})

    assert tuple(explicit_empty.model_dump(mode="json")) == (
        "trigger",
        "visible_response",
        "gaze_target",
        "body_behavior",
        "hand_behavior",
        "terminal_performance_state",
    )
    assert canonical_sha256(explicit_empty.model_dump(mode="json")) == (
        "b33f58485e4c0f9a2fef257335cac9cc1bc5e39dff589b989ef35aea49310206"
    )
    assert canonical_sha256(_complete_intent().model_dump(mode="json")) == (
        "6c61c0afdc861ff99c956003e4e9d84adb53467560bc25ec5eb578d2d4fc9ed0"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("trigger", "   "),
        ("emotion", "unspecified"),
        ("facial_expression", "none"),
        ("gaze_target", "TBD"),
        ("breathing", "-"),
        ("body_behavior", "unknown"),
    ],
)
def test_beat_text_fields_reject_blank_and_placeholder_values(field: str, value: str):
    with pytest.raises(ValidationError):
        _beat(**{field: value})


@pytest.mark.parametrize(
    "values",
    (
        {"screen_identity": "unspecified"},
        {"character_id": "unknown"},
        {
            "visibility": "offscreen",
            "offscreen_reason": "TBD",
            "beats": (),
        },
    ),
)
def test_character_identity_and_offscreen_fields_reject_placeholders(values):
    with pytest.raises(ValidationError):
        _direction(**values)


@pytest.mark.parametrize("phase", ("opening", "response", "settle"))
def test_visible_actor_requires_authored_beats(phase: str):
    assert _direction(beats=(_beat(phase),)).beats[0].phase == phase
    with pytest.raises(ValidationError):
        _direction(beats=())


def test_beats_require_ordered_unique_phases_and_standalone_throughout():
    _direction(beats=(_beat("opening"), _beat("response"), _beat("settle")))
    with pytest.raises(ValidationError):
        _direction(beats=(_beat("response"), _beat("opening")))
    with pytest.raises(ValidationError):
        _direction(beats=(_beat("response"), _beat("response")))
    with pytest.raises(ValidationError):
        _direction(beats=(_beat("throughout"), _beat("settle")))


def test_visibility_rules_reject_missing_or_conflicting_offscreen_state():
    _direction(
        character_id="dispatcher",
        screen_identity="the off-screen station dispatcher",
        role="supporting",
        visibility="offscreen",
        offscreen_reason="voice comes from the train speaker outside frame",
        beats=(),
    )
    with pytest.raises(ValidationError):
        _direction(visibility="offscreen", offscreen_reason=None, beats=())
    with pytest.raises(ValidationError):
        _direction(visibility="visible", offscreen_reason="behind the camera")
    with pytest.raises(ValidationError):
        _direction(
            visibility="offscreen",
            offscreen_reason="outside frame",
            beats=(_beat(),),
        )


def test_performance_intent_rejects_duplicate_actor_ids():
    legacy = _complete_intent().performance_intent
    assert legacy is not None
    first = _direction("hero")
    duplicate = _direction("hero", screen_identity="a second visible hero")
    with pytest.raises(ValidationError):
        PerformanceIntent.model_validate(
            {
                **legacy.model_dump(mode="python"),
                "character_directions": (first, duplicate),
            }
        )


def test_performance_intent_bounds_cast_direction_count():
    legacy = _complete_intent().performance_intent
    assert legacy is not None
    directions = tuple(
        _direction(f"actor-{index}", screen_identity=f"visible actor {index}")
        for index in range(17)
    )
    with pytest.raises(ValidationError):
        PerformanceIntent.model_validate(
            {
                **legacy.model_dump(mode="python"),
                "character_directions": directions,
            }
        )


def test_cast_binding_requires_one_authored_direction_per_bound_character():
    hero = _character("hero", "Lin Yan")
    passenger = _character("passenger", "Seated passenger")
    principal = _direction("hero")
    background = _direction(
        "passenger",
        screen_identity="the passenger in a tan coat",
        role="background",
        beats=(
            _beat(
                "throughout",
                emotion="quietly occupied",
                facial_expression="neutral, attentive eyes",
                gaze_target="the phone in their hands",
                breathing="subtle steady breathing",
                body_behavior="sits naturally and makes one small thumb movement",
            ),
        ),
    )
    performance = _complete_intent().performance_intent
    assert performance is not None
    assert performance_direction_issues(
        performance.model_copy(update={"character_directions": ()}),
        (hero, passenger),
    ) == (
        "generation_intent.performance_intent.character_directions[hero]",
        "generation_intent.performance_intent.character_directions[passenger]",
    )
    assert performance_direction_issues(
        performance.model_copy(
            update={"character_directions": (principal, background)}
        ),
        (hero, passenger),
    ) == ()
    assert performance_direction_issues(
        performance.model_copy(update={"character_directions": (principal,)}),
        (hero, passenger),
    ) == (
        "generation_intent.performance_intent.character_directions[passenger]",
    )
    assert performance_direction_issues(
        performance.model_copy(update={"character_directions": (principal,)}),
        (),
    ) == (
        "generation_intent.performance_intent.character_directions[hero].character_id",
    )
    assert performance_direction_issues(
        performance.model_copy(update={"character_directions": ()}), (),
    ) == ()
    assert performance_direction_issues(
        performance.model_copy(
            update={"character_directions": (principal, background)}
        ),
        ("hero", "passenger"),
    ) == ()


def test_rendering_keeps_only_authored_directions_and_human_identity():
    directions = (
        _direction("internal-hero-12", screen_identity="林砚，车厢里的年轻乘客"),
        _direction(
            "internal-robot-7",
            screen_identity="a small non-human service robot",
            role="background",
            beats=(
                _beat(
                    "throughout",
                    emotion="calm focus",
                    facial_expression="single status light remains steady",
                    gaze_target="the station map",
                    breathing="no biological breathing; a cooling fan pulses softly",
                    body_behavior="keeps both wheels planted",
                ),
            ),
        ),
        _direction(
            "internal-dispatcher",
            screen_identity="the station dispatcher",
            role="supporting",
            visibility="offscreen",
            offscreen_reason="the announcement comes from the train speaker outside frame",
            beats=(),
        ),
    )
    text = render_performance_direction(
        PerformanceIntent(
            trigger="announcement",
            visible_response="looks toward the empty seat",
            gaze_target="empty seat",
            body_behavior="holds still",
            hand_behavior="raises the left hand",
            terminal_performance_state="hand hovering near the glass",
            character_directions=directions,
        )
    )

    assert "林砚，车厢里的年轻乘客" in text
    assert "a small non-human service robot" in text
    assert "internal-hero-12" not in text
    assert "internal-robot-7" not in text
    assert "internal-dispatcher" not in text
    assert "single status light remains steady" in text
    assert (
        "remains offscreen because the announcement comes from the train speaker outside frame"
        in text
    )
    assert "In the response" in text
    assert "with subtle intensity" in text
    assert "screen_identity" not in text
    assert "character_id" not in text
    assert "{\"" not in text
    assert "}" not in text
    assert "blink" not in text


def test_remote_and_h3_compilers_emit_and_attest_authored_directions():
    from ai_video.production._h3_prompt import H3PromptCompilation, compile_h3_prompt
    from ai_video.production._remote_video_native_prompt import (
        RemoteVideoPromptCompilation,
        compile_remote_video_prompt,
    )

    direction = _direction("internal-hero-token")
    requirement = _rich_requirement((direction,))
    expected = render_performance_direction(requirement.generation_intent.performance_intent)
    path = "generation_intent.performance_intent.character_directions"
    performance_path = "generation_intent.performance_intent"

    remote = compile_remote_video_prompt(requirement)
    h3 = compile_h3_prompt(requirement)

    assert isinstance(remote, RemoteVideoPromptCompilation)
    assert isinstance(h3, H3PromptCompilation)
    for result in (remote, h3):
        assert expected in result.prompt_text
        assert performance_path in result.expressed_control_paths
        assert path in result.expressed_control_paths
        assert "internal-hero-token" not in result.prompt_text
    assert len(h3.prompt_text.splitlines()) == 3
    assert h3.prompt_sha256 == hashlib.sha256(h3.prompt_text.encode("utf-8")).hexdigest()


def test_legacy_h3_t2va_compiler_emits_authored_character_directions():
    from ai_video.production._h3_prompt import H3PromptCompilation, compile_h3_prompt

    direction = _direction("internal-legacy-actor")
    requirement = _legacy_t2va_requirement((direction,))
    result = compile_h3_prompt(requirement)

    assert isinstance(result, H3PromptCompilation)
    assert render_performance_direction(requirement.generation_intent.performance_intent) in (
        result.prompt_text
    )
    assert "generation_intent.performance_intent.character_directions" in (
        result.expressed_control_paths
    )
    assert "generation_intent.performance_intent" in result.expressed_control_paths
    assert "internal-legacy-actor" not in result.prompt_text
    assert len(result.prompt_text.splitlines()) == 3


def test_rich_seedance_compile_covers_root_qa_performance_expression():
    from ai_video.production.generation_recipe import (
        GenerationRecipe,
        RequirementExpression,
        SeedPolicy,
    )
    from ai_video.production.shot_router import (
        AdapterCompilerContract,
        ProviderBoundVideoRequest,
        VideoGenerationResolver,
    )
    from ai_video.production.video_compiler import CompiledProviderVideoRequest
    from ai_video.production.video_requirement import AudioNeed, OutputNeed
    from ai_video.production._remote_video_native_prompt import (
        RemoteVideoPromptCompilation,
        compile_remote_video_prompt,
    )
    from test_production_generation_decision import acceptance_policy
    from test_production_provider_neutral_adapters import _replace_requirement
    from test_production_seedance import (
        SeedanceVideoProvider,
        _profile,
        _profile_pointer,
        _request,
    )
    from test_production_shot_router import _context, _lifecycle, _policy, _verified_requirement

    profile = _profile()
    request_fixture = _request(profile)
    output = request_fixture.output_requirement
    context = _context(important=False)
    intent = _complete_intent()
    performance = intent.performance_intent
    assert performance is not None
    direction = _direction("hero")
    intent = intent.model_copy(
        update={
            "performance_intent": PerformanceIntent(
                **{
                    **performance.model_dump(mode="python"),
                    "character_directions": (direction,),
                }
            )
        }
    )
    projection = _replace_requirement(
        _verified_requirement(context),
        contract_version="provider-neutral-video-requirement/4",
        generation_intent=intent,
        output_need=OutputNeed(
            duration_seconds=output.duration_seconds,
            width=output.width,
            height=output.height,
            aspect_ratio=output.ratio,
            fps=output.fps,
            container_mime=output.mime_type,
        ),
        audio_need=AudioNeed.REQUIRED,
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=object(),
        credential=lambda: "unused",
        input_reference=object(),
    )
    selected = next(
        variant
        for variant in provider.capabilities().variants
        if variant.model_id == request_fixture.model_id
        and variant.mode is request_fixture.mode
        and variant.output_capability is not None
        and variant.output_capability.supports(output)
    )
    compiler = AdapterCompilerContract.create(
        compiler_id="seedance-video-compiler", compiler_version="2"
    )
    expression = RequirementExpression(
        requirement_id="character-performance",
        level="acceptance",
        stage="raw_generation",
        dimension="interaction",
        observable="the authored per-character performance is expressed",
        tolerance="exact",
        measurement="human review",
        proof="human",
        intent_paths=("generation_intent.performance_intent",),
        native_text=(),
        production_owner="shot_authoring",
    )
    acceptance = acceptance_policy((expression,))
    recipe = GenerationRecipe(
        seed=SeedPolicy(kind="uncontrolled"),
        profile_sha256=profile.profile_sha256,
        compiler_hash=compiler.compiler_hash,
        requirement_hash=projection.requirement.requirement_hash,
        rubric_hash=acceptance.profile_content_hash,
        acceptance_policy=acceptance,
        expressions=(expression,),
    )
    routing = VideoGenerationResolver()._bind_requirement(
        projection=projection,
        context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=_profile_pointer(profile),
        capabilities=provider.capabilities(),
        selected_capability_id=selected.capability_id,
        output_requirement=output,
        lifecycle=_lifecycle(context),
        compiler_contract=compiler,
    )
    assert routing.provider_bound_request is not None
    bound = ProviderBoundVideoRequest.create(
        **{
            **{
                name: getattr(routing.provider_bound_request, name)
                for name in ProviderBoundVideoRequest.model_fields
                if name != "provider_bound_request_hash"
            },
            "generation_recipe": recipe,
        }
    )

    native = compile_remote_video_prompt(
        projection.requirement,
        provider_bound=bound,
    )
    compiled = provider.compile_request(bound, projection.requirement)

    assert isinstance(native, RemoteVideoPromptCompilation)
    assert "generation_intent.performance_intent" in native.expressed_control_paths
    assert "generation_intent.performance_intent.character_directions" in (
        native.expressed_control_paths
    )
    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert render_performance_direction(intent) in compiled.provider_native_prompt
    assert all(
        getattr(performance, field) in compiled.provider_native_prompt
        for field in (
            "trigger",
            "visible_response",
            "gaze_target",
            "body_behavior",
            "hand_behavior",
            "terminal_performance_state",
        )
    )


def test_empty_directions_preserve_compiler_prompt_bytes_and_omit_attestation():
    from ai_video.production._h3_prompt import compile_h3_prompt
    from ai_video.production._remote_video_native_prompt import compile_remote_video_prompt

    legacy = _rich_requirement(())
    remote = compile_remote_video_prompt(legacy)
    h3 = compile_h3_prompt(legacy)
    assert remote.prompt_sha256 == (
        "4a100569a4dea53c5bb4ddc465efcee6a7f41220aca0a20b1614f5da65b32ca3"
    )
    assert h3.prompt_sha256 == (
        "8a41728d3712657746311696b46b1d5aa15886b4a52330d1e111fe2eeb954099"
    )
    assert remote.expressed_control_paths == (
        "generation_intent.ambience_intent.explicitly_silent",
        "generation_intent.camera_subject_relation.relation_kind",
        "generation_intent.dialogue_intent.lip_sync_required",
        "generation_intent.pacing.shot_duration_seconds",
        "generation_intent.primary_camera_motion.amplitude_class",
        "generation_intent.primary_camera_motion.end_motion_state",
        "generation_intent.primary_camera_motion.movement_kind",
        "generation_intent.primary_camera_motion.speed_class",
        "generation_intent.primary_camera_motion.start_motion_state",
    )
    assert h3.expressed_control_paths == (
        "generation_intent.primary_camera_motion.movement_kind",
        "generation_intent.primary_camera_motion.amplitude_class",
        "generation_intent.primary_camera_motion.speed_class",
        "generation_intent.primary_camera_motion.start_motion_state",
        "generation_intent.primary_camera_motion.end_motion_state",
        "generation_intent.pacing.shot_duration_seconds",
        "generation_intent.ambience_intent.explicitly_silent",
        "generation_intent.camera_subject_relation.relation_kind",
        "generation_intent.dialogue_intent.start_seconds",
        "generation_intent.dialogue_intent.end_seconds",
        "generation_intent.dialogue_intent.on_screen",
        "generation_intent.dialogue_intent.lip_sync_required",
    )
    assert "generation_intent.performance_intent.character_directions" not in (
        remote.expressed_control_paths
    )
    assert "generation_intent.performance_intent.character_directions" not in (
        h3.expressed_control_paths
    )
    assert "generation_intent.performance_intent" not in remote.expressed_control_paths
    assert "generation_intent.performance_intent" not in h3.expressed_control_paths


def _rebind_preserved_source_with_performance(
    *, include_direction: bool, omit_legacy_value: str | None = None
):
    import sys
    from pathlib import Path
    from types import ModuleType

    local_tests = str(Path(__file__).resolve().parent)
    package = sys.modules.get("tests")
    package_paths = tuple(str(path) for path in getattr(package, "__path__", ()))
    if not any(Path(path).resolve() == Path(local_tests) for path in package_paths):
        package = ModuleType("tests")
        package.__path__ = [local_tests]
        sys.modules["tests"] = package

    from ai_video.production.hashing import seal_artifact
    from ai_video.production.seedance_source_expression import (
        PreservedSourceExpression,
        SourceTextPart,
        compile_preserved_source,
        source_parts_sha256,
    )
    from ai_video.production.shot_router import ProviderBoundVideoRequest
    from test_production_metaso_h3 import _seedance_preserved_source_case

    _, bound, requirement, source = _seedance_preserved_source_case()
    performance_values = {
        "trigger": "the station announcement names the passenger",
        "visible_response": "looks toward the empty reflection",
        "gaze_target": "the empty seat in the window",
        "body_behavior": "holds the shoulders quietly",
        "hand_behavior": "raises the left hand toward the glass",
        "terminal_performance_state": "the left hand stops near the glass",
    }
    direction = _direction("internal-hero-token")
    performance = PerformanceIntent(
        **performance_values,
        character_directions=(direction,),
    )
    source_values = {
        key: value
        for key, value in performance_values.items()
        if key != omit_legacy_value
    }
    source_prompt = source + "\n" + " ".join(source_values.values())
    if include_direction:
        source_prompt += "\n" + render_performance_direction(performance)
    expression_data = requirement.target_shot.preserved_source_expression.model_dump(
        mode="python"
    )
    parts = (SourceTextPart(text=source_prompt),)
    expression_data.update(
        source_sha256=source_parts_sha256(
            parts,
            requirement.target_shot.preserved_source_expression.implicit_references,
        ),
        parts=parts,
    )
    expression = PreservedSourceExpression.model_validate(expression_data)
    generation_intent = requirement.generation_intent.model_copy(
        update={
            "performance_intent": performance,
            "subject_action": requirement.generation_intent.subject_action.model_copy(
                update={"progression": source_prompt}
            ),
        }
    )
    target_shot = seal_artifact(
        requirement.target_shot.model_copy(
            update={
                "intent": source_prompt,
                "preserved_source_expression": expression,
            }
        )
    )
    requirement_data = requirement.model_dump(
        mode="python", exclude={"requirement_id", "requirement_hash"}
    )
    requirement_data.update(
        target_shot=target_shot,
        generation_intent=generation_intent,
        generation_intent_hash=canonical_sha256(
            generation_intent.model_dump(mode="json")
        ),
    )
    rebound_requirement = ProviderNeutralVideoRequirement.create(**requirement_data)
    bound_data = {
        name: getattr(bound, name)
        for name in ProviderBoundVideoRequest.model_fields
        if name != "provider_bound_request_hash"
    }
    bound_data.update(
        requirement_hash=rebound_requirement.requirement_hash,
        target_shot_content_hash=target_shot.content_hash,
        generation_recipe=bound.generation_recipe.model_copy(
            update={"requirement_hash": rebound_requirement.requirement_hash}
        ),
    )
    rebound_bound = ProviderBoundVideoRequest.create(**bound_data)
    native = compile_preserved_source(
        rebound_bound,
        rebound_requirement,
        provider_name="seedance",
        compiler_id="seedance-video-compiler",
        compiler_version="3",
    )
    return native, source_prompt


def test_preserved_source_requires_authored_direction_and_legacy_values_verbatim():
    with pytest.raises(ValueError, match="direction block verbatim"):
        _rebind_preserved_source_with_performance(include_direction=False)

    native, source_prompt = _rebind_preserved_source_with_performance(
        include_direction=True
    )
    assert native.prompt_text == source_prompt
    assert (
        "generation_intent.performance_intent",
        "generation_intent.performance_intent.character_directions",
    ) == tuple(
        path
        for path in native.expressed_control_paths
        if path.startswith("generation_intent.performance_intent")
    )

    with pytest.raises(ValueError, match="every authored legacy performance value"):
        _rebind_preserved_source_with_performance(
            include_direction=True,
            omit_legacy_value="terminal_performance_state",
        )


def test_full_seedance_compile_covers_performance_recipe_ancestor(tmp_path):
    from test_canvas_source_expression import subject_service

    service, limits = subject_service(tmp_path, provider_family="seedance")
    prepared = service.prepare(limits=limits)

    assert prepared.execution_binding is not None, prepared.compilation
    intent = prepared.execution_binding.projection.requirement.generation_intent
    assert intent.performance_intent.character_directions
    assert render_performance_direction(intent) in prepared.resolved_request.prompt_text
