"""Seedance authored text must prove controls against the exact final prompt."""

import hashlib

import pytest

from ai_video.production.generation_recipe import GenerationRecipe, RequirementExpression, SeedPolicy
from ai_video.production.performance_direction import (
    CharacterPerformanceDirection,
    PerformanceBeat,
    PerformanceIntent,
)
from ai_video.production.seedance import SeedanceVideoProvider
from ai_video.production.seedance_native_prompt import SeedanceNativePromptBinding
from ai_video.production.shot_router import (
    AdapterCompilerContract,
    ProviderBoundVideoRequest,
    VideoGenerationResolver,
)
from ai_video.production.video_requirement import (
    AudioNeed,
    GenerationIntent,
    OutputNeed,
    Pacing,
    SubjectAction,
)
from test_production_provider_neutral_adapters import _replace_requirement
from test_production_seedance import _profile, _profile_pointer, _request
from test_production_shot_router import (
    _context,
    _lifecycle,
    _policy,
    _verified_requirement,
)


def _performance_fixture(final_text=None, *, cast_shape="single", compiler_version="4", bind=True,
                        omit_paths=(), generic_parent=False, performance_intent_override=None,
                        qa_performance_override=None):
    """Build a normal routed Seedance request with QA-sealed leaf evidence."""
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.hashing import canonical_sha256

    profile = _profile()
    output = _request(profile).output_requirement
    if cast_shape == "single":
        identities = ("lead",)
        shot_text = "A passenger sits quietly in a carriage."
        directions = (CharacterPerformanceDirection(
            character_id="lead",
            screen_identity="the seated lead",
            role="principal",
            visibility="visible",
            beats=(PerformanceBeat(
                phase="response",
                trigger="the overhead announcement",
                emotion="uneasy attention",
                intensity="subtle",
                facial_expression="her brow briefly tightens",
                gaze_target="toward the carriage doors",
                breathing="a short held breath",
                body_behavior="her shoulders settle without leaving the seat",
            ),),
        ),)
    elif cast_shape == "mixed":
        identities = ("lead", "commuter", "offscreen-witness")
        shot_text = "A courier waits at a station counter."
        directions = (
            CharacterPerformanceDirection(
                character_id="lead",
                screen_identity="the waiting courier",
                role="principal",
                visibility="visible",
                beats=(
                    PerformanceBeat(
                        phase="response",
                        trigger="the service bell rings",
                        emotion="brief uncertainty",
                        intensity="subtle",
                        facial_expression="the courier's eyes narrow briefly",
                        gaze_target="toward the service bell",
                        breathing="one quiet inhale",
                        body_behavior="the courier shifts weight inside the stance",
                    ),
                    PerformanceBeat(
                        phase="settle",
                        trigger="the bell stops",
                        emotion="composed patience",
                        intensity="subtle",
                        facial_expression="the brow relaxes",
                        gaze_target="back to the counter",
                        breathing="breathing returns to an even rhythm",
                        body_behavior="the shoulders settle while the hands remain visible",
                    ),
                ),
            ),
            CharacterPerformanceDirection(
                character_id="commuter",
                screen_identity="a background commuter",
                role="background",
                visibility="visible",
                beats=(PerformanceBeat(
                    phase="throughout",
                    trigger="the station remains routine",
                    emotion="ordinary attention",
                    intensity="none",
                    facial_expression="a relaxed neutral expression",
                    gaze_target="the posted schedule",
                    breathing="quiet regular breathing",
                    body_behavior="one hand steadies a bag while seated",
                ),),
            ),
            CharacterPerformanceDirection(
                character_id="offscreen-witness",
                screen_identity="an offscreen witness",
                role="supporting",
                visibility="offscreen",
                offscreen_reason="the shot remains framed on the counter and waiting cast",
            ),
        )
    elif cast_shape == "pair":
        identities = ("scientist", "colleague")
        shot_text = "Two researchers study a display in a narrow lab."
        directions = (
            CharacterPerformanceDirection(
                character_id="scientist",
                screen_identity="the researcher nearest the display",
                role="principal",
                visibility="visible",
                beats=(PerformanceBeat(
                    phase="throughout",
                    trigger="the display remains stable",
                    emotion="focused concentration",
                    intensity="subtle",
                    facial_expression="the eyes track one changing line",
                    gaze_target="the lower edge of the display",
                    breathing="a steady unforced breath",
                    body_behavior="the head stays nearly still as the eyes follow the line",
                ),),
            ),
            CharacterPerformanceDirection(
                character_id="colleague",
                screen_identity="the colleague beside the display",
                role="supporting",
                visibility="visible",
                beats=(PerformanceBeat(
                    phase="throughout",
                    trigger="the display remains stable",
                    emotion="quiet concentration",
                    intensity="subtle",
                    facial_expression="the jaw loosens slightly",
                    gaze_target="the same lower display line",
                    breathing="soft regular breathing",
                    body_behavior="the colleague remains balanced beside the desk",
                ),),
            ),
        )
    else:
        raise AssertionError(f"unknown cast shape: {cast_shape}")

    context = _context(
        important=False,
        shot_intent=shot_text,
        scene_id={"single": "scene-carriage", "mixed": "scene-station-counter",
                  "pair": "scene-lab"}[cast_shape],
    )
    from ai_video.production.hashing import seal_artifact

    authored_shot = seal_artifact(context.activated_shot.model_copy(update={"character_ids": identities}))
    context = type(context).model_validate({
        **context.model_dump(mode="python"),
        "activated_shot": authored_shot,
        "target_shot_content_hash": authored_shot.content_hash,
    })
    base = _verified_requirement(context)
    source = base.requirement.target_shot.intent
    performance = PerformanceIntent(
        trigger="an ordinary cue arrives in the scene",
        visible_response="the visible cast responds within its own role",
        gaze_target="each visible character's authored target",
        body_behavior="each visible character keeps a plausible balance",
        hand_behavior="hands remain consistent with the current scene",
        terminal_performance_state="each visible character reaches the authored settle state",
        character_directions=directions,
    )
    current_performance = performance_intent_override or performance
    qa_performance = qa_performance_override or performance
    intent = GenerationIntent(
        subject_action=SubjectAction(progression=source),
        pacing=Pacing(shot_duration_seconds=output.duration_seconds),
        performance_intent=current_performance,
    )
    qa_intent = GenerationIntent(
        subject_action=SubjectAction(progression=source),
        pacing=Pacing(shot_duration_seconds=output.duration_seconds),
        performance_intent=qa_performance,
    )
    projection = _replace_requirement(
        base,
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
    canonical_ids = tuple(sorted(character.character_id for character in projection.requirement.characters))
    assert canonical_ids == tuple(sorted(identities))
    assert tuple(sorted(projection.requirement.target_shot.character_ids)) == canonical_ids
    assert tuple(sorted(direction.character_id for direction in directions)) == canonical_ids

    pairs = [
        (f"generation_intent.performance_intent.{name}", getattr(qa_performance, name))
        for name in ("trigger", "visible_response", "gaze_target", "body_behavior",
                     "hand_behavior", "terminal_performance_state")
    ]
    for actor_index, direction in enumerate(qa_performance.character_directions):
        base_path = f"generation_intent.performance_intent.character_directions.{actor_index}"
        pairs.extend((f"{base_path}.{name}", getattr(direction, name))
                     for name in ("screen_identity", "role", "visibility"))
        if direction.offscreen_reason is not None:
            pairs.append((f"{base_path}.offscreen_reason", direction.offscreen_reason))
        for beat_index, beat in enumerate(direction.beats):
            beat_path = f"{base_path}.beats.{beat_index}"
            pairs.extend((f"{beat_path}.{name}", getattr(beat, name))
                         for name in ("phase", "trigger", "emotion", "intensity",
                                      "facial_expression", "gaze_target", "breathing",
                                      "body_behavior"))
    paths = tuple(path for path, _ in pairs)
    fragments = tuple(value for _, value in pairs)
    map_bindings = tuple({"intent_path": path, "fragment_indices": [index]}
                         for index, (path, _) in enumerate(pairs))
    if generic_parent:
        generic = "The character performs naturally throughout the shot."
        paths = ("generation_intent.performance_intent",)
        fragments = (generic,)
        map_bindings = ({"intent_path": paths[0], "fragment_indices": [0]},)
    selected_fragments = tuple(fragment for path, fragment in zip(paths, fragments, strict=True)
                                if path not in set(omit_paths))
    compact_text = f"{source} " + "; ".join(selected_fragments)
    final_text = compact_text if final_text is None else final_text
    rule = RequirementExpression(
        requirement_id="lead-expression",
        level="acceptance",
        stage="raw_generation",
        dimension="character_performance",
        observable="Each visible character shows the selected performance; offscreen characters retain their authored visibility.",
        tolerance="as authored",
        measurement="inspect the exact final native prompt and generated media",
        proof="human",
        intent_paths=paths,
        native_text=fragments,
        native_text_mapping={
            "contract_version": "native-text-mapping/1",
            "intent_sha256": canonical_sha256(qa_intent.model_dump(mode="json")),
            "bindings": list(map_bindings),
        },
        production_owner="qa_acceptance",
    )
    acceptance_identity = {
        "domain_id": "seedance-fidelity-test",
        "profile_id": "seedance-fidelity-rubric",
        "profile_version": "1",
        "measurement_contract_version": "1",
        "required_requirement_ids": (rule.requirement_id,),
        "generation_requirements": (rule.model_dump(mode="json"),),
    }
    payload = dict(acceptance_identity)
    digest = canonical_sha256(payload)
    selected_acceptance = DomainAcceptancePolicy(
        domain_id=acceptance_identity["domain_id"],
        profile_id=acceptance_identity["profile_id"],
        profile_version=acceptance_identity["profile_version"],
        profile_content_hash=digest,
        measurement_contract_version=acceptance_identity["measurement_contract_version"],
        required_requirement_ids=acceptance_identity["required_requirement_ids"],
        profile_payload={**payload, "content_hash": digest},
    )

    provider = SeedanceVideoProvider(
        profile=profile,
        transport=object(),
        credential=lambda: pytest.fail("offline prompt compilation must not read credentials"),
        input_reference=object(),
        native_prompt_binding=None,
    )
    selected = next(
        item for item in provider.capabilities().variants
        if item.model_id == _request(profile).model_id
        and item.mode.value == projection.requirement.generation_mode.value
        and item.output_capability is not None
        and item.output_capability.supports(output)
    )
    compiler = AdapterCompilerContract.create(
        compiler_id="seedance-video-compiler",
        compiler_version=compiler_version,
    )
    routed = VideoGenerationResolver()._bind_requirement(
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
    assert routed.provider_bound_request is not None, routed.decision
    recipe = GenerationRecipe(
        seed=SeedPolicy(kind="uncontrolled"),
        profile_sha256=profile.profile_sha256,
        compiler_hash=compiler.compiler_hash,
        requirement_hash=projection.requirement.requirement_hash,
        rubric_hash=selected_acceptance.profile_content_hash,
        acceptance_policy=selected_acceptance,
        expressions=(rule,),
    )
    bound = ProviderBoundVideoRequest.create(**{
        **{
            name: getattr(routed.provider_bound_request, name)
            for name in ProviderBoundVideoRequest.model_fields
            if name != "provider_bound_request_hash"
        },
        "generation_recipe": recipe,
    })
    binding = None if not bind else SeedanceNativePromptBinding(
            provider_bound_request_hash=bound.provider_bound_request_hash,
            prompt_text=final_text,
            prompt_sha256=hashlib.sha256(final_text.encode()).hexdigest(),
            source_evidence_sha256=hashlib.sha256(final_text.encode()).hexdigest(),
            source_preservation=False,
        )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=object(),
        credential=lambda: pytest.fail("offline prompt compilation must not read credentials"),
        input_reference=object(),
        native_prompt_binding=binding,
    )
    return (provider, bound, projection.requirement, fragments, paths, final_text,
            current_performance, context, projection, selected_acceptance, output, compiler, profile)


def _with_lead_facial_expression(performance, value):
    directions = list(performance.character_directions)
    lead = directions[0]
    beats = list(lead.beats)
    beats[0] = beats[0].model_copy(update={"facial_expression": value})
    directions[0] = lead.model_copy(update={"beats": tuple(beats)})
    return performance.model_copy(update={"character_directions": tuple(directions)})


def test_fresh_authored_binding_rejects_missing_qa_mapped_leaf_from_final_text():
    from ai_video.production._sequence_source import compile_with_sequence_expression
    from ai_video.production.video_compiler import (
        ProviderRequirementUnsupported,
        ProviderRequirementUnsupportedReason,
    )

    provider, bound, requirement, fragments, paths, final_text, _, *_ = _performance_fixture(
        cast_shape="single",
        omit_paths=("generation_intent.performance_intent.character_directions.0.beats.0.facial_expression",),
    )

    compiled = compile_with_sequence_expression(provider, bound, requirement)

    assert isinstance(compiled, ProviderRequirementUnsupported)
    assert compiled.reason is ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED
    assert "lead-expression" in compiled.unsupported_field_paths
    assert "generation_intent.performance_intent.character_directions.0.beats.0.facial_expression" \
        in compiled.unsupported_field_paths


def test_replacing_required_expression_with_opposite_text_is_rejected():
    from ai_video.production._sequence_source import compile_with_sequence_expression
    from ai_video.production.video_compiler import ProviderRequirementUnsupported

    original_text = _performance_fixture()[5]
    opposite_text = original_text.replace(
        "her brow briefly tightens", "her brow remains relaxed", 1,
    )
    provider, bound, requirement, _, _, _, _, *_ = _performance_fixture(final_text=opposite_text)

    compiled = compile_with_sequence_expression(provider, bound, requirement)

    assert isinstance(compiled, ProviderRequirementUnsupported)
    assert "lead-expression" in compiled.unsupported_field_paths
    assert "generation_intent.performance_intent.character_directions.0.beats.0.facial_expression" \
        in compiled.unsupported_field_paths


@pytest.mark.parametrize("cast_shape", ["single", "mixed", "pair"])
def test_fresh_authored_binding_compiles_exact_compact_text_for_different_casts(cast_shape):
    from ai_video.production._sequence_source import compile_with_sequence_expression
    from ai_video.production.video_compiler import CompiledProviderVideoRequest
    from ai_video.production.performance_direction import render_performance_direction

    provider, bound, requirement, fragments, paths, final_text, performance, *_ = _performance_fixture(
        cast_shape=cast_shape,
    )

    compiled = compile_with_sequence_expression(provider, bound, requirement)

    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert compiled.adapter_compiler_version == "4"
    assert compiled.provider_native_prompt == final_text
    assert compiled.request.prompt_text == final_text
    assert "Character performance directions." not in final_text
    assert render_performance_direction(performance) not in final_text
    assert all(fragment in final_text for fragment in fragments)


def test_feedback_prepare_accepts_mapped_prompt_and_keeps_quality_unrated():
    from ai_video.production.video_compiler import CompiledProviderVideoRequest
    from ai_video.production.video_reference_controls import prepared_generation_report

    orchestrator, limits, effects, requirement, final_text = _feedback_orchestrator_fixture()
    prepared = orchestrator.prepare(limits=limits)

    assert isinstance(prepared.compilation, CompiledProviderVideoRequest)
    assert prepared.compilation.adapter_compiler_version == "4"
    assert prepared.resolved_request.prompt_text == final_text
    assert prepared.execution_binding is not None
    report = _performance_report(
        requirement,
        final_text,
        prepared.decision.routing.provider_bound_request.generation_recipe.expressions,
    )
    assert report["final_native_prompt"]["prompt_text"] == final_text
    assert report["input_expression"] == "MAPPED_FRAGMENTS_PRESENT"
    assert report["missing_final_text_paths"] == []
    assert report["actual_quality"] == "NOT_EVALUATED"
    prepared_report = prepared_generation_report(prepared)
    reported_performance = prepared_report["reference_control"]["performance_control"]
    assert reported_performance["final_native_prompt"]["prompt_text"] == final_text
    assert reported_performance["input_expression"] == "MAPPED_FRAGMENTS_PRESENT"
    assert reported_performance["actual_quality"] == "NOT_EVALUATED"
    assert effects == {"credentials": [], "transport": []}


def test_feedback_prepare_rejects_old_qa_mapping_after_performance_intent_changes():
    from ai_video.production.hashing import canonical_sha256
    from ai_video.production.video_compiler import (
        ProviderRequirementUnsupported,
        ProviderRequirementUnsupportedReason,
    )

    _, _, _, _, _, _, original_performance, *_ = _performance_fixture()
    changed_performance = _with_lead_facial_expression(
        original_performance, "her brow remains relaxed",
    )
    orchestrator, limits, effects, requirement, final_text = _feedback_orchestrator_fixture(
        performance_intent_override=changed_performance,
    )

    prepared = orchestrator.prepare(limits=limits)

    path = "generation_intent.performance_intent.character_directions.0.beats.0.facial_expression"
    assert isinstance(prepared.compilation, ProviderRequirementUnsupported)
    assert prepared.compilation.reason is ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED
    assert "lead-expression" in prepared.compilation.unsupported_field_paths
    assert path in prepared.compilation.unsupported_field_paths
    assert "her brow briefly tightens" in final_text
    assert "her brow remains relaxed" not in final_text
    assert prepared.execution_binding is None
    assert prepared.resolved_request is None
    assert effects == {"credentials": [], "transport": []}
    current_intent_hash = canonical_sha256(requirement.generation_intent.model_dump(mode="json"))
    selected_mapping = prepared.decision.routing.provider_bound_request.generation_recipe.expressions[
        0
    ].native_text_mapping
    assert current_intent_hash != selected_mapping.intent_sha256


def test_feedback_prepare_accepts_resealed_qa_mapping_for_changed_performance_intent():
    from ai_video.production.hashing import canonical_sha256
    from ai_video.production.video_compiler import CompiledProviderVideoRequest

    baseline = _performance_fixture()
    original_performance = baseline[6]
    original_acceptance = baseline[9]
    changed_performance = _with_lead_facial_expression(
        original_performance, "her brow remains relaxed",
    )
    orchestrator, limits, effects, requirement, final_text = _feedback_orchestrator_fixture(
        performance_intent_override=changed_performance,
        qa_performance_override=changed_performance,
    )

    prepared = orchestrator.prepare(limits=limits)

    assert isinstance(prepared.compilation, CompiledProviderVideoRequest)
    assert prepared.execution_binding is not None
    assert prepared.resolved_request.prompt_text == final_text
    assert "her brow remains relaxed" in final_text
    assert "her brow briefly tightens" not in final_text
    recipe = prepared.decision.routing.provider_bound_request.generation_recipe
    selected_qa_rule = recipe.acceptance_policy.profile_payload["generation_requirements"][0]
    current_intent_hash = canonical_sha256(requirement.generation_intent.model_dump(mode="json"))
    assert recipe.acceptance_policy.profile_content_hash != original_acceptance.profile_content_hash
    assert selected_qa_rule["native_text_mapping"]["intent_sha256"] == current_intent_hash
    assert recipe.expressions[0].native_text_mapping.intent_sha256 == current_intent_hash
    assert "her brow remains relaxed" in selected_qa_rule["native_text"]
    assert effects == {"credentials": [], "transport": []}


def test_feedback_start_stops_missing_mapped_span_before_durable_or_provider_effects():
    from ai_video.production.video_reference_controls import prepared_generation_report
    from ai_video.production.video_compiler import (
        ProviderRequirementUnsupported,
        ProviderRequirementUnsupportedReason,
    )

    orchestrator, limits, effects, requirement, final_text = _feedback_orchestrator_fixture(
        omit_paths=("generation_intent.performance_intent.character_directions.0.beats.0.facial_expression",),
    )

    class NoCommitter:
        calls = []

        def __getattr__(self, name):
            self.calls.append(name)
            raise AssertionError("unsupported preparation must not enter the durable committer")

    committer = NoCommitter()
    prepared = orchestrator.start(
        committer=committer,
        attempt_id="missing-performance-span",
        limits=limits,
    )

    missing = "generation_intent.performance_intent.character_directions.0.beats.0.facial_expression"
    assert isinstance(prepared.compilation, ProviderRequirementUnsupported)
    assert prepared.compilation.reason is ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED
    assert "lead-expression" in prepared.compilation.unsupported_field_paths
    assert missing in prepared.compilation.unsupported_field_paths
    assert prepared.execution_binding is None
    assert prepared.resolved_request is None
    assert committer.calls == []
    assert effects == {"credentials": [], "transport": []}

    report = _performance_report(
        requirement,
        final_text,
        prepared.decision.routing.provider_bound_request.generation_recipe.expressions,
    )
    assert report["final_native_prompt"]["prompt_text"] == final_text
    assert report["input_expression"] != "MAPPED_FRAGMENTS_PRESENT"
    assert missing in report["missing_final_text_paths"]
    assert report["actual_quality"] == "NOT_EVALUATED"
    prepared_report = prepared_generation_report(prepared)
    reported_control = prepared_report["reference_control"]
    diagnostic = reported_control["compilation"]["input_expression_report"]
    assert diagnostic["prompt_text"] == final_text
    assert missing in diagnostic["missing_requirement_paths"]
    assert diagnostic["coverage_source"] == "selected_qa_final_text"
    assert diagnostic["rejected_coverage_source"] == "inherited_automatic_prose"
    assert diagnostic["actual_quality"] == "NOT_EVALUATED"
    reported_performance = reported_control["performance_control"]
    assert reported_performance["final_native_prompt"]["prompt_text"] == final_text
    assert missing in reported_performance["missing_final_text_paths"]
    assert reported_performance["actual_quality"] == "NOT_EVALUATED"


def test_execution_binding_cannot_mint_from_tampered_final_seedance_text():
    from ai_video.errors import AiVideoError, ErrorCode
    from ai_video.production.generation_execution import GenerationDecisionExecutionBinding

    orchestrator, limits, _, _, _ = _feedback_orchestrator_fixture()
    prepared = orchestrator.prepare(limits=limits)
    binding = prepared.execution_binding
    assert binding is not None
    tampered_text = prepared.resolved_request.prompt_text.replace(
        "her brow briefly tightens", "her brow remains relaxed", 1,
    )
    assert tampered_text != prepared.resolved_request.prompt_text
    tampered_request = prepared.resolved_request.model_copy(update={"prompt_text": tampered_text})

    with pytest.raises(AiVideoError) as rejected:
        GenerationDecisionExecutionBinding.create(
            projection=binding.projection,
            context=binding.context,
            policy=binding.policy,
            lifecycle=binding.lifecycle,
            inputs=binding.inputs,
            decision=binding.decision,
            compiled_request=tampered_request,
            continuity_routing=binding.continuity_routing,
            unsubmitted_predecessor_evidence_hash=binding.unsubmitted_predecessor_evidence_hash,
        )
    assert rejected.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def _legacy_auto_prose_fixture():
    from ai_video.production.generation_recipe import GenerationRecipe, RequirementExpression, SeedPolicy
    from ai_video.production.shot_router import AdapterCompilerContract, ProviderBoundVideoRequest
    from ai_video.production.video_requirement import AudioNeed, OutputNeed
    from test_production_generation_decision import acceptance_policy
    from tests.test_production_video_intent_validation import _complete_intent

    profile = _profile()
    output = _request(profile).output_requirement
    context = _context(important=False)
    projection = _replace_requirement(
        _verified_requirement(context),
        contract_version="provider-neutral-video-requirement/4",
        generation_intent=_complete_intent(),
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
        credential=lambda: pytest.fail("offline prompt compilation must not read credentials"),
        input_reference=object(),
    )
    selected = next(
        item for item in provider.capabilities().variants
        if item.model_id == _request(profile).model_id
        and item.mode.value == projection.requirement.generation_mode.value
        and item.output_capability is not None
        and item.output_capability.supports(output)
    )
    compiler = AdapterCompilerContract.create(
        compiler_id="seedance-video-compiler", compiler_version="2",
    )
    expression = RequirementExpression(
        requirement_id="hand-behavior",
        level="acceptance",
        stage="raw_generation",
        dimension="interaction",
        observable="the hand secures the product",
        tolerance="exact",
        measurement="human review",
        proof="human",
        intent_paths=("generation_intent.performance_intent.hand_behavior",),
        native_text=("reaches once and secures the product",),
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
    routed = VideoGenerationResolver()._bind_requirement(
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
    assert routed.provider_bound_request is not None
    bound = ProviderBoundVideoRequest.create(**{
        **{
            name: getattr(routed.provider_bound_request, name)
            for name in ProviderBoundVideoRequest.model_fields
            if name != "provider_bound_request_hash"
        },
        "generation_recipe": recipe,
    })
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=object(),
        credential=lambda: pytest.fail("offline prompt compilation must not read credentials"),
        input_reference=object(),
    )

    return provider, bound, projection.requirement


def _feedback_orchestrator_fixture(*, omit_paths=(), performance_intent_override=None,
                                   qa_performance_override=None):
    """Route through the common prepare owner, then bind authored text to its exact request."""
    from ai_video.production.generation_decision import DecisionPolicy, ExecutionLimits
    from ai_video.production.generation_feedback import (
        GenerationFeedbackOrchestrator,
        GenerationHistory,
        RegisteredGenerationTarget,
    )
    from ai_video.production.video import VideoProviderCapabilities

    (_, _, requirement, _, _, final_text, _, context, projection, acceptance,
     output, compiler, profile) = _performance_fixture(
        omit_paths=omit_paths,
        performance_intent_override=performance_intent_override,
        qa_performance_override=qa_performance_override,
    )
    current = {
        "projection": projection,
        "context": context,
        "policy": _policy(remote_authorized=True, budget_authorized=True),
        "lifecycle": _lifecycle(context),
        "acceptance": acceptance,
    }
    effects = {"credentials": [], "transport": []}

    class NoEffectTransport:
        def request(self, *args, **kwargs):
            effects["transport"].append((args, kwargs))
            pytest.fail("prepare must not submit or query Seedance")

    def provider(binding=None):
        def credential():
            effects["credentials"].append(True)
            pytest.fail("prepare must not read provider credentials")

        class SingleCapabilitySeedanceProvider(SeedanceVideoProvider):
            def __init__(self):
                super().__init__(
                    profile=profile,
                    transport=NoEffectTransport(),
                    credential=credential,
                    input_reference=object(),
                    native_prompt_binding=binding,
                )
                model_id = _request(profile).model_id
                selected = next(
                    variant for variant in self._capabilities.variants
                    if variant.model_id == model_id
                    and variant.output_capability is not None
                    and variant.output_capability.supports(output)
                )
                self._capabilities = VideoProviderCapabilities.create(
                    provider_name="seedance", variants=(selected,),
                )

        return SingleCapabilitySeedanceProvider()

    def orchestrator(adapter):
        return GenerationFeedbackOrchestrator(
            targets=(RegisteredGenerationTarget(adapter, _profile_pointer(profile), compiler, output),),
            context_loader=lambda: current,
            history_loader=GenerationHistory,
            policy=DecisionPolicy(allow_bounded_exploration=True),
        )

    unbound_provider = provider()
    limits = ExecutionLimits(
        task_id="seedance-prompt-fidelity",
        generation_forbidden=False,
        allowed_remote_candidates=tuple(
            f"seedance/{variant.capability_id}"
            for variant in unbound_provider.capabilities().variants
            if variant.execution_kind.value == "remote"
        ),
        paid_submit_ceiling=2,
        paid_submits_used=0,
        local_batch_limit=2,
        local_batch_used=0,
        local_total_limit=2,
        local_total_used=0,
        local_resource_available=True,
    )
    probe = orchestrator(unbound_provider).prepare(limits=limits)
    probe_bound = probe.decision.routing.provider_bound_request
    assert probe_bound is not None
    from ai_video.production.video_compiler import ProviderRequirementUnsupported
    assert isinstance(probe.compilation, ProviderRequirementUnsupported)
    assert probe.execution_binding is None
    digest = hashlib.sha256(final_text.encode()).hexdigest()
    binding = SeedanceNativePromptBinding(
        provider_bound_request_hash=probe_bound.provider_bound_request_hash,
        prompt_text=final_text,
        prompt_sha256=digest,
        source_evidence_sha256=digest,
        source_preservation=False,
    )
    adapter = provider(binding)
    final_orchestrator = orchestrator(adapter)
    return final_orchestrator, limits, effects, requirement, final_text


def _performance_report(requirement, final_text, expressions):
    from ai_video.production.performance_authoring import performance_authoring_report

    return performance_authoring_report(
        intent=requirement.generation_intent,
        characters=requirement.characters,
        rules=expressions,
        required_ids=tuple(rule.requirement_id for rule in expressions
                           if rule.level == "acceptance"),
        prompt_text=final_text,
    )


def test_no_binding_keeps_existing_recipe_compiler_and_old_serialization_shape():
    from ai_video.production._sequence_source import compile_with_sequence_expression
    from ai_video.production.video_compiler import CompiledProviderVideoRequest

    provider, bound, requirement = _legacy_auto_prose_fixture()
    compiled = compile_with_sequence_expression(provider, bound, requirement)

    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert compiled.adapter_compiler_version == "2"
    assert "reaches once and secures the product" in compiled.provider_native_prompt
    legacy = RequirementExpression(
        requirement_id="legacy-duration",
        level="acceptance",
        stage="raw_generation",
        dimension="timing",
        observable="The generated output uses the requested duration.",
        tolerance="exact",
        measurement="inspect the request",
        proof="technical",
        intent_paths=("output_need.duration_seconds",),
        production_owner="qa_acceptance",
    )
    assert "native_text_mapping" not in legacy.model_dump(mode="json")


def test_parent_performance_path_cannot_cover_all_visible_actor_beats():
    from ai_video.production._sequence_source import compile_with_sequence_expression
    from ai_video.production.video_compiler import ProviderRequirementUnsupported

    provider, bound, requirement, _, paths, _, _, *_ = _performance_fixture(generic_parent=True)

    compiled = compile_with_sequence_expression(provider, bound, requirement)

    assert isinstance(compiled, ProviderRequirementUnsupported)
    assert "lead-expression" in compiled.unsupported_field_paths
    assert any("character_directions.0.beats.0." in path
               for path in compiled.unsupported_field_paths)


def test_recipe_cannot_replace_selected_qa_fragment_after_sealing():
    from pydantic import ValidationError

    _, bound, _, _, _, _, _, *_ = _performance_fixture()
    payload = bound.generation_recipe.model_dump(mode="json")
    payload["expressions"][0]["native_text"][0] = "a different unselected phrase"

    with pytest.raises((ValidationError, ValueError), match="fragment|selected QA|native_text"):
        GenerationRecipe.model_validate(payload)


def test_authored_binding_from_another_request_cannot_be_resealed_as_current():
    from ai_video.production._sequence_source import compile_with_sequence_expression
    from ai_video.production.video_compiler import ProviderRequirementUnsupported

    provider, _, _, _, _, _, _, *_ = _performance_fixture(cast_shape="single")
    _, other_bound, other_requirement, _, _, _, _, *_ = _performance_fixture(cast_shape="pair")

    compiled = compile_with_sequence_expression(provider, other_bound, other_requirement)

    assert isinstance(compiled, ProviderRequirementUnsupported)


def test_fresh_authored_binding_cannot_fall_back_to_legacy_v2():
    from ai_video.production._sequence_source import compile_with_sequence_expression
    from ai_video.production.video_compiler import ProviderRequirementUnsupported

    provider, bound, requirement, _, _, _, _, *_ = _performance_fixture(compiler_version="2")

    try:
        compiled = compile_with_sequence_expression(provider, bound, requirement)
    except ValueError:
        return

    assert isinstance(compiled, ProviderRequirementUnsupported)


def test_historical_preserved_source_flag_still_uses_its_v2_contract():
    from ai_video.production.video_compiler import CompiledProviderVideoRequest
    from test_seedance_source_prompt import _case, _compile

    profile, bound, requirement, source = _case()

    compiled = _compile(profile, bound, requirement, source, preserved=True)

    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert compiled.adapter_compiler_version == "2"
    assert compiled.request.prompt_text == source


def test_old_seedance_recipe_request_replays_only_against_its_sealed_request():
    from ai_video.production._sequence_source import compile_with_sequence_expression
    from ai_video.production.video_compiler import CompiledProviderVideoRequest

    provider, bound, requirement = _legacy_auto_prose_fixture()
    sealed = provider.compile_request(bound, requirement)
    assert isinstance(sealed, CompiledProviderVideoRequest)

    replayed = compile_with_sequence_expression(
        provider, bound, requirement, expected_request=sealed.request,
    )

    assert isinstance(replayed, CompiledProviderVideoRequest)
    assert replayed.compiled_request_hash == sealed.compiled_request_hash
    assert replayed.request.request_input_hash == sealed.request.request_input_hash
