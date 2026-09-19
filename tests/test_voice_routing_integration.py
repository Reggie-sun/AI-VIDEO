"""Offline route wiring through the current planner, Router, and Vidu compiler."""

from __future__ import annotations

import json
import hashlib
from dataclasses import replace
from pathlib import Path

from ai_video.production.composition_contracts import AudioTrackSpec
from ai_video.production.generation_decision import DecisionPolicy
from ai_video.production.generation_feedback import (
    GenerationFeedbackOrchestrator,
    GenerationHistory,
    RegisteredGenerationTarget,
)
from ai_video.production.generation_recipe import RequirementExpression
from ai_video.production.hashing import seal_artifact
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    _canonical_json_bytes,
    _canonical_yaml_bytes,
    prepare_dependency_graph_transition,
    prepare_project_registry_commit,
)
from ai_video.production.shot_router import AdapterCompilerContract
from ai_video.production.video_requirement import (
    AmbienceIntent,
    AudioNeed,
    DialogueIntent,
    OutputNeed,
    Pacing,
)
from ai_video.production.voice_routing import (
    VoiceAudioHandoff,
    VoiceRouteBinding,
    VoiceRoutingContext,
    build_voice_readiness,
)
from ai_video.production.voice_routing_contracts import (
    VoiceMode,
    VoiceRoute,
    VoiceRoutingRequirement,
    VoiceSpeakerRequirement,
)
from ai_video.planning import ProductionPolicyInput, VideoPlanner, require_current_video_plan
from fixtures.planning_factory import make_character, make_request, make_scene
from ai_video.production.models import VisualStrategy
import production_project_factory as project_factory
from test_generation_provider_wiring import forbidden
from test_production_generation_decision import acceptance_policy, setup_decision
from test_production_minimax_speech import _policy as minimax_policy
from test_production_minimax_speech import _pricing as minimax_pricing, _request as minimax_request
from test_production_shot_router import _context, _lifecycle, _verified_requirement
from test_production_video_intent_validation import _complete_intent


_SCRIPT = "The gate is open."
_VOICE_ID = "English_expressive_narrator"
_EXECUTION_INPUTS_BY_ROOT = {}


def _voice_requirement(*, mode: VoiceMode = VoiceMode.AUTO, consistency: str = "single_shot"):
    return VoiceRoutingRequirement(
        mode=mode,
        speakers=(
            VoiceSpeakerRequirement(
                speaker_id="hero",
                language="en",
                script_text=_SCRIPT,
                voice_id=_VOICE_ID,
                consistency=consistency,
            ),
        ),
    )


def _minimax_preview(request):
    from ai_video.production.minimax_speech import MiniMaxSpeechVoiceProvider

    return MiniMaxSpeechVoiceProvider(
        transport=forbidden,
        pricing=minimax_pricing(),
        api_key=forbidden,
        policy=minimax_policy(),
    ).preview(request)


def _write_voice_project(
    root: Path,
    voice: VoiceRoutingRequirement,
    *,
    execution_source: bool = True,
):
    if execution_source:
        return _write_voice_execution_source(root, voice)
    project_factory.write_production_project(root)
    committer = ProductionStateCommitter(root)
    initial = load_production_project(root / "project.yaml")
    committer.upgrade_manifest_schema(
        "2.1", expected_manifest_revision=initial.manifest.manifest_revision
    )
    loaded = load_production_project(root / "project.yaml")
    original = loaded.shots[0]
    shot = seal_artifact(original.model_copy(update={
        "revision": original.revision + 1,
        "dialogue": _SCRIPT,
        "visual_strategy": VisualStrategy.GENERATED_VIDEO,
        "required_asset_roles": (
            project_factory.AssetRoleRequirement(
                role="final_visual",
                asset_ids=(),
                allowed_asset_types=(project_factory.AssetType.VIDEO,),
            ),
        ),
        "generated_video_rationale": "The sealed Shot requires a generated performance.",
        "voice_routing": voice,
    }))
    shot_path = loaded.project.artifacts.shots[0].path
    project_factory._write_yaml(root / shot_path, shot)
    refs = loaded.project.artifacts.model_copy(update={
        "shots": (project_factory._ref(shot, str(shot_path)),),
    })
    project = seal_artifact(loaded.project.model_copy(update={
        "revision": loaded.project.revision + 1,
        "artifacts": refs,
    }))
    registry = loaded.registry.model_copy(update={
        "schema_version": "2.1",
        "revision_id": "0" * 64,
        "content_hash": "0" * 64,
    })
    registry_hash = project_factory.registry_semantic_sha256(registry)
    registry = registry.model_copy(update={
        "revision_id": registry_hash,
        "content_hash": registry_hash,
    })
    commit = prepare_project_registry_commit(
        manifest=loaded.manifest,
        project=project,
        registry=registry,
        attempt_id="voice-routing-authoring",
    )
    committer.commit(commit)
    return load_production_project(root / "project.yaml")


def _write_voice_execution_source(root: Path, voice: VoiceRoutingRequirement):
    from ai_video.production.dependency import (
        build_production_dependency_graph,
        desired_fingerprints,
        resolve_dependency_state,
    )
    from production_generation_execution_factory import (
        activate_fixture_generation_qa_policy,
        activate_generated_video_shot,
    )

    from test_production_vidu import _profile, _request

    inputs = project_factory.make_p8_video_generation_base(root, schema_version="2.7")
    inputs = activate_generated_video_shot(root=root, inputs=inputs)
    inputs = activate_fixture_generation_qa_policy(
        root=root,
        inputs=inputs,
        output=_request(profile=_profile()).output_requirement,
    )
    loaded = inputs.project
    original = loaded.shots[0]
    shot = seal_artifact(original.model_copy(update={
        "revision": original.revision + 1,
        "content_hash": "0" * 64,
        "dialogue": _SCRIPT,
        "voice_routing": voice,
    }))
    shot_ref = loaded.project.artifacts.shots[0].model_copy(update={
        "revision": shot.revision,
        "content_hash": shot.content_hash,
        "path": Path(
            f"creative/shots/{shot.shot_id}-voice-routing-{shot.content_hash[:12]}.yaml"
        ),
    })
    project = seal_artifact(loaded.project.model_copy(update={
        "revision": loaded.project.revision + 1,
        "content_hash": "0" * 64,
        "artifacts": loaded.project.artifacts.model_copy(update={
            "shots": (shot_ref, *loaded.project.artifacts.shots[1:]),
        }),
    }))
    base_commit = prepare_project_registry_commit(
        manifest=loaded.manifest,
        project=project,
        registry=loaded.registry,
        attempt_id="voice-routing-authoring",
    )
    candidate = loaded.model_copy(update={
        "project": project,
        "shots": (shot, *loaded.shots[1:]),
        "manifest": loaded.manifest.model_copy(update={
            "active_project": base_commit.next_project,
        }),
    })
    graph = build_production_dependency_graph(replace(inputs, project=candidate))
    states = resolve_dependency_state(graph, loaded.manifest.dependency_states).states
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=loaded.manifest.manifest_revision,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    graph_bytes = _canonical_json_bytes(graph)
    shot_bytes = _canonical_yaml_bytes(shot)
    commit = replace(
        base_commit,
        dependency_graph_transition=transition,
        artifacts=tuple(sorted((
            *base_commit.artifacts,
            PreparedArtifact(
                transition.candidate_dependency_graph.path,
                graph_bytes,
                hashlib.sha256(graph_bytes).hexdigest(),
            ),
            PreparedArtifact(
                shot_ref.path,
                shot_bytes,
                hashlib.sha256(shot_bytes).hexdigest(),
            ),
        ), key=lambda artifact: artifact.relative_path.as_posix())),
    )
    ProductionStateCommitter(root).commit(commit)
    reopened = load_production_project(root / "project.yaml")
    _EXECUTION_INPUTS_BY_ROOT[reopened.root] = replace(inputs, project=reopened)
    return reopened


def _voice_dependency_transition(root: Path, request):
    """Rebuild the P8 graph against the exact generated-voice registry candidate."""
    from ai_video.production.audio import VoiceGenerationRequest
    from ai_video.production.dependency import (
        build_applied_dependency_evidence,
        build_production_dependency_graph,
        desired_fingerprints,
        resolve_dependency_state,
    )
    from ai_video.production.models import AssetRegistrySnapshot, ProductionProject

    active = load_production_project(root / "project.yaml")
    base = _EXECUTION_INPUTS_BY_ROOT[active.root]
    project_artifact = next(
        item for item in request.artifacts if item.relative_path == request.next_project.path
    )
    registry_artifact = next(
        item for item in request.artifacts if item.relative_path == request.next_registry.path
    )
    import yaml

    project = ProductionProject.model_validate(yaml.safe_load(project_artifact.payload))
    registry = AssetRegistrySnapshot.model_validate_json(registry_artifact.payload)
    voice_request_path = ProductionStateCommitter(root).voice_attempt_paths(
        request.attempt_id
    ).request_path.relative_to(root)
    voice_request = VoiceGenerationRequest.model_validate_json(next(
        item.payload for item in request.artifacts if item.relative_path == voice_request_path
    ))
    candidate = active.model_copy(update={
        "project": project,
        "registry": registry,
        "manifest": active.manifest.model_copy(update={
            "active_project": request.next_project,
            "active_registry": request.next_registry,
        }),
        "dependency_graph": None,
    })
    candidate_inputs = replace(
        base,
        project=candidate,
        voice_requests=tuple(
            item for item in base.voice_requests
            if item.input_artifact_ids != voice_request.input_artifact_ids
        ) + (voice_request,),
    )
    graph = build_production_dependency_graph(candidate_inputs)
    states = resolve_dependency_state(
        graph, build_applied_dependency_evidence(candidate_inputs, None)
    ).states
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=request.expected_manifest_revision,
        base_dependency_graph=active.manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    graph_bytes = _canonical_json_bytes(graph)
    return replace(
        request,
        artifacts=tuple(sorted((
            *request.artifacts,
            PreparedArtifact(
                transition.candidate_dependency_graph.path,
                graph_bytes,
                hashlib.sha256(graph_bytes).hexdigest(),
            ),
        ), key=lambda artifact: artifact.relative_path.as_posix())),
        dependency_graph_transition=transition,
    )


def _voice_setup(shot=None, *, mode: VoiceMode = VoiceMode.AUTO):
    voice = _voice_requirement(mode=mode)
    base_context = _context(important=False)
    base_projection = _verified_requirement(base_context)
    shot = shot or seal_artifact(base_context.activated_shot.model_copy(update={
        "dialogue": _SCRIPT, "character_ids": ("hero",), "voice_routing": voice,
    }))
    context = base_context.model_copy(update={
        "activated_shot": shot,
        "target_shot_id": shot.shot_id,
        "target_shot_revision": shot.revision,
        "target_shot_content_hash": shot.content_hash,
    })
    setup = setup_decision()
    setup.update(
        context=context,
        projection=base_projection,
        lifecycle=_lifecycle(context),
    )
    return setup, voice


def _voice_projection(setup, output):
    voice = setup["context"].activated_shot.voice_routing
    assert voice is not None
    intent = _complete_intent().model_copy(update={
        "pacing": Pacing(shot_duration_seconds=output.duration_seconds or 4),
        "ambience_intent": AmbienceIntent(environment_bed="none", explicitly_silent=True),
        "dialogue_intent": DialogueIntent(
            mode="dialogue",
            language="en",
            speaker_id="hero",
            verbatim_text=_SCRIPT,
            start_seconds=0,
            end_seconds=2,
            on_screen=False,
            response_obligation="The hero opens the gate.",
        ),
    })
    from ai_video.production.video_requirement import (
        GenerationOperation,
        ProviderNeutralGenerationIntentProjection,
        QualityNeed,
    )
    generation_intent = ProviderNeutralGenerationIntentProjection.create(
        generation_operation=GenerationOperation.TEXT_TO_VIDEO,
        generation_intent=intent,
        voice_routing=voice,
        output_need=OutputNeed(
            timing_mode="fixed",
            duration_seconds=output.duration_seconds,
            width=output.width,
            height=output.height,
            geometry_policy=output.dimension_mode,
            aspect_ratio=output.ratio,
            fps=output.fps,
            container_mime=output.mime_type,
        ),
        audio_need=AudioNeed(voice.audio_need),
        quality_need=QualityNeed(objective_tier="production"),
    )
    request = make_request(
        target_shot=setup["context"].activated_shot,
        character_context=(make_character(character_id="hero"),),
        scene_context=make_scene(scene_id=setup["context"].activated_shot.scene_id),
        available_assets=(),
        review_decision=None,
        production_policy=ProductionPolicyInput(
            local_resources_available=True,
            remote_authorized=True,
            budget_authorized=True,
            quality_preference="production",
            accept_static_image_fallback=False,
        ),
        planning_contract_version="video-planner/3",
        generation_intent=generation_intent,
    )
    plan = VideoPlanner().plan(request)
    return require_current_video_plan(current_request=request, plan=plan)


def _orchestrator(*, setup, source_project=None, voice_context=None):
    from ai_video.production.vidu import ViduVideoProvider
    from test_production_vidu import _profile, _request

    profile = _profile()
    output = _request(profile=profile).output_requirement
    provider = ViduVideoProvider(
        profile=profile,
        transport=forbidden,
        credential=forbidden,
        image_resolver=forbidden,
    )
    projection = _voice_projection(setup, output)
    acceptance = acceptance_policy((RequirementExpression(
        requirement_id="hand",
        level="acceptance",
        stage="raw_generation",
        dimension="action",
        observable="hand secures product",
        tolerance="exact",
        measurement="viewing",
        proof="human",
        intent_paths=("generation_intent.performance_intent.hand_behavior",),
        production_owner="shot_authoring",
    ),))
    if source_project is not None and source_project.qa_policy is not None:
        from ai_video.production.production_strategy_reader import (
            selected_shot_generation_acceptance,
        )

        current_acceptance = selected_shot_generation_acceptance(
            source_project, setup["context"].target_shot_id
        )
        if current_acceptance is not None:
            acceptance = current_acceptance
    current = {
        **{key: value for key, value in setup.items() if key != "inputs"},
        "projection": projection,
        "acceptance": acceptance,
    }
    if source_project is not None:
        current["source_project"] = source_project
        if source_project.qa_policy is not None:
            current["final_output_goal"] = source_project.qa_policy.final_output
    if voice_context is not None:
        current["voice_context"] = voice_context
    target = RegisteredGenerationTarget(
        provider,
        profile.pointer(),
        AdapterCompilerContract.create(
            compiler_id="vidu-video-compiler", compiler_version="3"
        ),
        output,
    )
    selected = next(
        variant
        for variant in provider.capabilities().variants
        if variant.model_id == "viduq3-pro" and variant.mode.value == "text_to_video"
    )
    limits = setup["inputs"].limits.model_copy(update={
        "allowed_remote_candidates": (
            f"vidu/{selected.capability_id}/voice-native",
            f"vidu/{selected.capability_id}/voice-separate",
        ),
    })
    return (
        GenerationFeedbackOrchestrator(
            targets=(target,),
            context_loader=lambda: current,
            history_loader=GenerationHistory,
            policy=DecisionPolicy(allow_bounded_exploration=True),
        ),
        limits,
        provider,
        projection,
    )


def test_auto_voice_keeps_canonical_authoring_and_blocks_without_readiness() -> None:
    setup, voice = _voice_setup()
    orchestrator, limits, _provider, projection = _orchestrator(setup=setup)

    prepared = orchestrator.prepare(limits=limits)

    assert setup["context"].activated_shot.voice_routing == voice
    assert projection.requirement.voice_routing == voice
    assert projection.requirement.audio_need is AudioNeed.OPTIONAL
    assert {candidate.voice_route.route for candidate in prepared.inputs.candidates} == {
        VoiceRoute.NATIVE,
        VoiceRoute.SEPARATE,
    }
    assert prepared.decision.disposition == "BLOCKED_CAPABILITY"
    assert prepared.compilation is None
    assert any("VOICE_READINESS_REQUIRED" in reason for reason in prepared.decision.rationale)


def test_auto_native_uses_real_target_layout_and_vidu_payload(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    voice = _voice_requirement()
    source = _write_voice_project(source_root, voice)
    final = _write_voice_project(target_root, voice, execution_source=False)
    setup, _voice = _voice_setup(source.shots[0])
    context = VoiceRoutingContext(
        final_project_file=(final.root / "project.yaml").resolve(),
        audio_handoffs=(VoiceAudioHandoff(track=AudioTrackSpec(
            track_id="planned-dialogue",
            audio_kind="dialogue",
            asset_id="future-voice-dialogue",
            shot_id=setup["context"].target_shot_id,
        ), speaker_id="hero"),),
    )
    orchestrator, limits, provider, _projection = _orchestrator(
        setup=setup,
        source_project=source,
        voice_context=context,
    )

    prepared = orchestrator.prepare(limits=limits)

    assert prepared.decision.disposition == "GENERATE_ONCE", prepared.decision.rationale
    assert prepared.resolved_request is not None
    assert prepared.resolved_request.effective_output.native_audio is True
    endpoint, payload = provider._payload(prepared.resolved_request)
    assert endpoint == "text2video"
    assert json.loads(payload)["audio"] is True
    assert _SCRIPT in prepared.resolved_request.prompt_text


def test_separate_route_binds_exact_script_but_current_vidu_layout_stays_blocked(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    voice = _voice_requirement()
    source = _write_voice_project(source_root, voice)
    final = _write_voice_project(target_root, voice, execution_source=False)
    setup, _voice = _voice_setup(source.shots[0])
    request = minimax_request(
        provider_kind="minimax-speech",
        model_id="speech-2.8-hd",
        audio_kind="dialogue",
        script_text=_SCRIPT,
        speaker_id="hero",
        voice_id=_VOICE_ID,
        language="English",
        base_project=source.manifest.active_project,
        base_registry=source.manifest.active_registry,
    )
    context = VoiceRoutingContext(
        final_project_file=(final.root / "project.yaml").resolve(),
        audio_handoffs=(VoiceAudioHandoff(track=AudioTrackSpec(
            track_id="planned-dialogue",
            audio_kind="dialogue",
            asset_id=f"voice-{request.attempt_id}",
            shot_id=setup["context"].target_shot_id,
        ), speaker_id="hero", voice_request=request,
              voice_preview=_minimax_preview(request), credential_reference_id="MINIMAX_SPEECH_API_KEY"),),
    )
    orchestrator, limits, _provider, projection = _orchestrator(
        setup=setup,
        source_project=source,
        voice_context=context,
    )
    candidates = orchestrator.prepare(limits=limits).inputs.candidates
    separate = next(item for item in candidates if item.voice_route.route is VoiceRoute.SEPARATE)
    readiness = build_voice_readiness(
        source=source,
        requirement=projection.requirement,
        candidate=separate,
        context=context,
        generation_id=setup["lifecycle"].generation_id,
    )

    assert request.script_text == voice.speakers[0].script_text
    assert request.script_hash == voice.speakers[0].script_hash
    assert "GENERATED_VOICE_CROSS_PROJECT_HANDOFF_UNSUPPORTED" in readiness.separate_blockers
    from ai_video.production._remote_video_native_prompt import compile_remote_video_prompt

    prompt = compile_remote_video_prompt(
        projection.requirement,
        voice_route=VoiceRouteBinding(
            route=VoiceRoute.SEPARATE,
            requirement_hash=voice.content_hash,
        ),
    )
    assert prompt.outcome == "compiled"
    assert _SCRIPT not in prompt.prompt_text
    assert "Dialogue is supplied separately" in prompt.prompt_text


def test_same_project_separate_compiles_with_exact_minimax_preview(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    voice = _voice_requirement(mode=VoiceMode.SEPARATE_REQUIRED)
    source = _write_voice_project(root, voice)
    setup, _voice = _voice_setup(source.shots[0], mode=VoiceMode.SEPARATE_REQUIRED)
    request = minimax_request(
        provider_kind="minimax-speech",
        model_id="speech-2.8-hd",
        audio_kind="dialogue",
        script_text=_SCRIPT,
        speaker_id="hero",
        voice_id=_VOICE_ID,
        language="English",
        base_project=source.manifest.active_project,
        base_registry=source.manifest.active_registry,
    )
    context = VoiceRoutingContext(
        final_project_file=(source.root / "project.yaml").resolve(),
        audio_handoffs=(VoiceAudioHandoff(
            track=AudioTrackSpec(
                track_id="planned-dialogue",
                audio_kind="dialogue",
                asset_id=f"voice-{request.attempt_id}",
                shot_id=setup["context"].target_shot_id,
            ),
            speaker_id="hero",
            voice_request=request,
            voice_preview=_minimax_preview(request),
            credential_reference_id="MINIMAX_SPEECH_API_KEY",
        ),),
    )
    orchestrator, limits, provider, _projection = _orchestrator(
        setup=setup,
        source_project=source,
        voice_context=context,
    )
    limits = limits.model_copy(update={
        "allowed_remote_candidates": tuple(
            candidate for candidate in limits.allowed_remote_candidates
            if candidate.endswith("/voice-separate")
        ),
    })

    prepared = orchestrator.prepare(limits=limits)

    assert prepared.decision.disposition == "GENERATE_ONCE", prepared.decision.rationale
    assert prepared.resolved_request is not None
    assert prepared.resolved_request.effective_output.native_audio is False
    _endpoint, payload = provider._payload(prepared.resolved_request)
    assert json.loads(payload)["audio"] is False
    assert _SCRIPT not in prepared.resolved_request.prompt_text
    assert prepared.voice_handoffs[0].voice_preview == _minimax_preview(request)
