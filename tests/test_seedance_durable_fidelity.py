"""Fresh admission and immutable replay through a real Production project."""
import hashlib

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.generation_decision import DecisionPolicy, ExecutionLimits
from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
from ai_video.production.generation_feedback import (
    GenerationFeedbackOrchestrator, GenerationHistory, RegisteredGenerationTarget,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.performance_direction import render_performance_direction
from ai_video.production.project import load_production_project
from ai_video.production.seedance import SeedanceVideoProvider
from ai_video.production.seedance_native_prompt import SeedanceNativePromptBinding
from ai_video.production.shot_router import AdapterCompilerContract
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video import VideoProviderCapabilities
from ai_video.production.video_compiler import CompiledProviderVideoRequest
from ai_video.production.video_generation import VideoGenerationService
from ai_video.production.video_requirement import AudioNeed, OutputNeed, Pacing
from production_project_factory import make_p8_video_generation_base
from production_generation_execution_factory import (
    activate_generated_video_shot, activate_fixture_generation_qa_policy, fixture_performance_intent,
)
from test_production_provider_neutral_adapters import _replace_requirement
from test_production_seedance import _profile, _profile_pointer, _request
from test_production_shot_router import _context, _lifecycle, _policy, _verified_requirement
from tests.test_production_video_intent_validation import _complete_intent


def _project_execution(root, *, ordinary_compiler_version="2"):
    inputs = make_p8_video_generation_base(root, schema_version="2.8")
    inputs = activate_generated_video_shot(root=root, inputs=inputs, require_first_frame=False)
    profile = _profile()
    output = _request(profile).output_requirement
    inputs = activate_fixture_generation_qa_policy(root=root, inputs=inputs, output=output)
    project = inputs.project
    shot = project.shots[0]
    scene = next(s for s in project.scenes if s.scene_id == shot.scene_id)
    characters = tuple(c for c in project.characters if c.character_id in shot.character_ids)
    context = _context(important=False).model_copy(update={
        "activated_shot": shot, "target_shot_id": shot.shot_id,
        "target_shot_revision": shot.revision, "target_shot_content_hash": shot.content_hash,
        "selected_registry_revision_id": project.manifest.active_registry.revision_id,
        "character_bible_content_hashes": (),
        "scene_content_hash": scene.content_hash, "canonical_character_references": (),
        "canonical_scene_reference": None, "shot_keyframe": None,
    })
    performance = fixture_performance_intent(characters, trigger="the shot opens",
        emotion="focused curiosity", facial_expression="brows lift slightly",
        gaze_target="the room ahead", breathing="quiet even breathing",
        body_behavior="stands balanced and attentive")
    intent = _complete_intent().model_copy(update={"performance_intent": performance,
        "pacing": Pacing(shot_duration_seconds=output.duration_seconds)})
    projection = _replace_requirement(_verified_requirement(context),
        contract_version="provider-neutral-video-requirement/4", target_shot=shot,
        scene=scene, characters=characters, generation_intent=intent,
        output_need=OutputNeed(duration_seconds=output.duration_seconds, width=output.width,
            height=output.height, aspect_ratio=output.ratio, fps=output.fps, container_mime=output.mime_type),
        audio_need=AudioNeed.REQUIRED)
    lifecycle = _lifecycle(context).model_copy(update={
        "base_project": project.manifest.active_project,
        "base_registry": project.manifest.active_registry,
        "base_dependency_graph": project.manifest.active_dependency_graph,
        "target_asset_role": next(r.role for r in shot.required_asset_roles if not r.asset_ids),
        "input_artifact_ids": (shot.artifact_id, scene.artifact_id, *(c.artifact_id for c in characters)),
    })
    provider = SeedanceVideoProvider(profile=profile, transport=object(),
        credential=lambda: pytest.fail("offline admission must not read credentials"), input_reference=object())
    selected = next(v for v in provider.capabilities().variants
        if v.model_id == _request(profile).model_id and v.mode.value == "text_to_video"
        and v.output_capability.supports(output))
    provider._capabilities = VideoProviderCapabilities.create(provider_name="seedance", variants=(selected,))
    if ordinary_compiler_version != "2":
        # The public common compiler can create a self-consistent request with
        # a caller-selected version. That alone must never grant admission.
        def public_compile(bound, requirement, **kwargs):
            from ai_video.production._remote_video_native_prompt import compile_remote_video_prompt
            from ai_video.production.video_compiler import ProviderNativePrompt, compile_provider_video_request

            automatic = compile_remote_video_prompt(requirement, provider_bound=bound,
                max_prompt_characters=None)
            text = automatic.prompt_text.replace(render_performance_direction(performance), "")
            native = ProviderNativePrompt(grammar_contract="remote-video-prose-v1",
                prompt_text=text, prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
                expressed_control_paths=automatic.expressed_control_paths)
            return compile_provider_video_request(provider_bound=bound, requirement=requirement,
                compiler_id="seedance-video-compiler", compiler_version=ordinary_compiler_version,
                capabilities=provider.capabilities(), native_prompt=native)
        provider.compile_new_request = public_compile
    current = {"projection": projection, "context": context,
        "policy": _policy(remote_authorized=True, budget_authorized=True), "lifecycle": lifecycle,
        "acceptance": project.qa_policy.selected_generation_acceptance(),
        "final_output_goal": project.qa_policy.final_output, "source_project": project}
    caller = GenerationFeedbackOrchestrator(targets=(RegisteredGenerationTarget(provider,
        _profile_pointer(profile), AdapterCompilerContract.create(
            compiler_id="seedance-video-compiler", compiler_version=ordinary_compiler_version), output),),
        context_loader=lambda: current, history_loader=GenerationHistory,
        policy=DecisionPolicy(allow_bounded_exploration=True))
    limits = ExecutionLimits(task_id="durable-fidelity", generation_forbidden=False,
        paid_submit_ceiling=1, paid_submits_used=0,
        local_batch_limit=1, local_batch_used=0, local_total_used=0, local_resource_available=False,
        allowed_remote_candidates=(f"seedance/{selected.capability_id}",))
    prepared = caller.prepare(limits=limits)
    assert prepared.execution_binding is not None, prepared.compilation or prepared.decision
    prepared.execution_binding.validate_current_project(project)
    return provider, prepared, ProductionStateCommitter(root), performance


def _resealed_legacy_binding(provider, prepared, performance):
    bound = prepared.decision.routing.provider_bound_request
    text = prepared.resolved_request.prompt_text
    block = render_performance_direction(performance)
    assert block in text
    text = text.replace(block, "")
    provider._native_prompt_binding = SeedanceNativePromptBinding(
        provider_bound_request_hash=bound.provider_bound_request_hash,
        prompt_text=text, prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
        source_evidence_sha256="a" * 64)
    compiled = provider.compile_request(bound, prepared.execution_binding.projection.requirement)
    assert isinstance(compiled, CompiledProviderVideoRequest)
    request = provider.resolve(compiled.request)
    data = prepared.execution_binding.model_dump(mode="json", exclude={"binding_hash"})
    data["compiled_request"] = request.model_dump(mode="json")
    data["binding_hash"] = canonical_sha256({"schema": "generation-decision-execution-binding/1", **data})
    return request, GenerationDecisionExecutionBinding.model_validate(data)


def test_canonical_begin_rejects_resealed_legacy_replacement_before_writes(tmp_path):
    provider, prepared, committer, performance = _project_execution(tmp_path)
    request, forged = _resealed_legacy_binding(provider, prepared, performance)
    before = committer._read_manifest()
    files = {p.relative_to(tmp_path) for p in (tmp_path / "state").rglob("*") if p.is_file()}
    with pytest.raises(AiVideoError, match="compiler/4|lineage"):
        VideoGenerationService(committer=committer, provider=provider).start(
            attempt_id="resealed-v2", request=request, execution_binding=forged)
    assert committer._read_manifest() == before
    assert {p.relative_to(tmp_path) for p in (tmp_path / "state").rglob("*") if p.is_file()} == files


@pytest.mark.parametrize("version", ["3", "99"])
def test_canonical_begin_rejects_ordinary_v3_or_unknown_contract_before_writes(tmp_path, monkeypatch, version):
    # Prepare the exact self-sealed candidate admitted by the previous guard,
    # then restore all admission checks before canonical start.
    with monkeypatch.context() as previous:
        previous.setattr(GenerationDecisionExecutionBinding, "_require_fresh_seedance_expression",
            staticmethod(lambda **_: None))
        provider, prepared, committer, _ = _project_execution(tmp_path, ordinary_compiler_version=version)
    assert prepared.resolved_request.adapter_compiler_version == version
    before = committer._read_manifest()
    files = {p.relative_to(tmp_path) for p in (tmp_path / "state").rglob("*") if p.is_file()}
    with pytest.raises(AiVideoError, match="supported compiler contract|preserved-source"):
        prepared.execution_binding.validate_current_project(load_production_project(tmp_path / "project.yaml"))
    with pytest.raises(AiVideoError, match="lineage"):
        VideoGenerationService(committer=committer, provider=provider).start(
            attempt_id="ordinary-contract", request=prepared.resolved_request,
            execution_binding=prepared.execution_binding)
    assert committer._read_manifest() == before
    assert {p.relative_to(tmp_path) for p in (tmp_path / "state").rglob("*") if p.is_file()} == files


def test_fresh_preserved_source_v3_is_recompiled_exactly():
    from ai_video.production.seedance_native_prompt import require_fresh_seedance_request
    from ai_video.production.seedance_source_expression import SourceTextPart
    from ai_video.production.shot_router import ProviderBoundVideoRequest
    from test_seedance_source_expression import _expression, _rebind_source_expression
    from test_seedance_source_prompt import _case

    profile, bound, requirement, text = _case()
    bound, requirement = _rebind_source_expression(bound, requirement,
        _expression((SourceTextPart(text=text),)), text)
    compiler = AdapterCompilerContract.create(compiler_id="seedance-video-compiler", compiler_version="3")
    bound = ProviderBoundVideoRequest.create(**{
        **{key: getattr(bound, key) for key in type(bound).model_fields
            if key != "provider_bound_request_hash"},
        "compiler_contract": compiler,
        "generation_recipe": bound.generation_recipe.model_copy(update={"compiler_hash": compiler.compiler_hash}),
    })
    provider = SeedanceVideoProvider(profile=profile, transport=object(),
        credential=lambda: pytest.fail("offline admission must not read credentials"), input_reference=object())
    compiled = provider.compile_new_request(bound, requirement)
    assert isinstance(compiled, CompiledProviderVideoRequest)
    request = provider.resolve(compiled.request)
    require_fresh_seedance_request(bound, requirement, request, provider.capabilities())
    assert request.prompt_text == text
    with pytest.raises(AiVideoError, match="current final-text QA evidence"):
        require_fresh_seedance_request(bound, requirement,
            request.model_copy(update={"activation_scope": request.activation_scope.model_copy(update={
                "request": compiled.request.model_copy(update={"prompt_text": text + " Invented action."})})}),
            provider.capabilities())


def test_manifest_owned_legacy_request_reopens_with_same_hashes(tmp_path):
    provider, prepared, committer, _ = _project_execution(tmp_path)
    request, binding = prepared.resolved_request, prepared.execution_binding
    VideoGenerationService(committer=committer, provider=provider).start(
        attempt_id="old-v2", request=request, execution_binding=binding)
    from ai_video.production._video_project_reader import load_generation_execution_binding, load_video_request_receipt
    project = load_production_project(tmp_path / "project.yaml")
    state = next(a.video_generation_state for a in project.manifest.attempts if a.attempt_id == "old-v2")
    reopened = load_generation_execution_binding(tmp_path, state.execution_binding)
    reopened.validate_current_project(project)
    assert reopened == binding
    assert load_video_request_receipt(tmp_path, state.request) == request
    assert reopened.binding_hash == binding.binding_hash
    assert request.adapter_compiler_version == "2"


def test_exact_preexisting_v2_replacement_is_not_migrated_on_resume(tmp_path, monkeypatch):
    provider, prepared, committer, performance = _project_execution(tmp_path)
    request, old_binding = _resealed_legacy_binding(provider, prepared, performance)
    service = VideoGenerationService(committer=committer, provider=provider)
    # Materialize the historical precondition through the real committer using
    # the prior admission behavior; this is not proof of fresh eligibility.
    with monkeypatch.context() as legacy:
        legacy.setattr(GenerationDecisionExecutionBinding, "_validate_seedance_admission", lambda *_: None)
        service.start(attempt_id="preexisting-v2", request=request, execution_binding=old_binding)
    project = load_production_project(tmp_path / "project.yaml")
    old_binding.validate_current_project(project)
    from ai_video.production._sequence_source import compile_with_sequence_expression
    result = compile_with_sequence_expression(provider, prepared.decision.routing.provider_bound_request,
        prepared.execution_binding.projection.requirement, expected_request=request.activation_scope.request)
    assert isinstance(result, CompiledProviderVideoRequest)
    assert result.request == request.activation_scope.request
    state = next(a.video_generation_state for a in project.manifest.attempts if a.attempt_id == "preexisting-v2")
    service._validate_generation_execution_binding(state, request)
    revision = project.manifest.manifest_revision
    with pytest.raises(AiVideoError, match="identity is already owned"):
        service.start(attempt_id="preexisting-v2", request=request, execution_binding=old_binding)
    assert committer._read_manifest().manifest_revision == revision
    assert old_binding.compiled_request == request


def test_replay_cannot_claim_another_persisted_binding_pointer(tmp_path):
    provider, prepared, committer, _ = _project_execution(tmp_path)
    binding = prepared.execution_binding
    VideoGenerationService(committer=committer, provider=provider).start(
        attempt_id="pointer-owner", request=prepared.resolved_request, execution_binding=binding)
    project = load_production_project(tmp_path / "project.yaml")
    attempts = tuple(attempt.model_copy(update={"video_generation_state":
        attempt.video_generation_state.model_copy(update={"execution_binding":
            attempt.video_generation_state.execution_binding.model_copy(update={"binding_hash": "b" * 64})})})
        if attempt.attempt_id == "pointer-owner" else attempt for attempt in project.manifest.attempts)
    mismatched = project.model_copy(update={"manifest": project.manifest.model_copy(update={"attempts": attempts})})
    with pytest.raises(ValueError, match="Manifest-owned request and binding"):
        binding.validate_current_project(mismatched)
