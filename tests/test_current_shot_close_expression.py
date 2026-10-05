"""Authored close truth and offline bootstrap; no real media qualification."""

import pytest

from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import GenerationIntent, TypedStateReference


def close_facts():
    return dict(character_presence="one actor remains visible",
        prop_identity="one red book", prop_holder="actor holds the book",
        hand_contact="left hand supports the closed book", prop_functional_state="book closed and intact",
        action_phase="book lift completed", gaze_target="actor looks at the book",
        dialogue_turn="no dialogue", screen_motion_axis="stationary on the right",
        audio_bridge="silence")


def authored_close(**updates):
    facts = close_facts()
    return GenerationIntent(close_state=TypedStateReference(kind="typed_hash", state_hash=canonical_sha256(facts)),
        close_causal_facts=facts, **updates)


def test_complete_close_facts_are_authored_hash_bound_and_canonical():
    intent = authored_close()
    assert intent.close_state.state_text is None
    assert tuple(key.value for key in intent.close_causal_facts) == tuple(sorted(close_facts()))
    assert GenerationIntent.model_validate_json(intent.model_dump_json()) == intent


@pytest.mark.parametrize("defect", ["missing", "blank", "unresolved", "digest", "mismatch", "text"])
def test_invalid_close_declarations_block(defect):
    facts = close_facts()
    state = TypedStateReference(kind="typed_hash", state_hash=canonical_sha256(facts))
    if defect == "missing":
        facts.pop("prop_holder")
    elif defect == "blank":
        facts["hand_contact"] = " "
    elif defect == "unresolved":
        facts["hand_contact"] = "unspecified"
    elif defect == "digest":
        facts["hand_contact"] = "a" * 64
    elif defect == "mismatch":
        state = TypedStateReference(kind="typed_hash", state_hash="f" * 64)
    else:
        state = TypedStateReference(kind="typed_text", state_text="book lifted")
    with pytest.raises(ValueError):
        GenerationIntent(close_state=state, close_causal_facts=facts)


def test_absent_facts_preserve_legacy_serialization():
    assert "close_causal_facts" not in GenerationIntent().model_dump(mode="json")


@pytest.mark.parametrize("endpoint", ["open_state", "close_state"])
def test_local_h3_arbitrary_hash_never_becomes_prose(endpoint):
    from test_production_h3_prompt import _requirement
    from ai_video.production._h3_prompt import compile_h3_prompt

    requirement = _requirement()
    intent = requirement.generation_intent.model_copy(update={endpoint: TypedStateReference(kind="typed_hash", state_hash="a" * 64)})
    result = compile_h3_prompt(requirement.model_copy(update={"generation_intent": intent}))
    assert result.outcome == "unsupported"
    assert f"generation_intent.{endpoint}" in result.unsupported_field_paths


def fresh_fixture(tmp_path, monkeypatch):
    import test_planning_sequence_continuity as s
    from test_typed_causal_native_expression import metaso_canonical_fixture
    from test_production_shot_router import _policy
    from test_requirement_semantics import semantic_rule, marked_policy
    from ai_video.planning import VideoPlanningRequest, VideoPlanner, require_current_video_plan
    from ai_video.planning.generation_feedback_context import require_feedback_context
    from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator, RegisteredGenerationTarget
    from ai_video.production.video_requirement import ProviderNeutralGenerationIntentProjection, SubjectAction, ActionEndpoint
    from ai_video.production.project import load_production_project
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.models import GenerationEvaluationAuthority

    provider, fixture = metaso_canonical_fixture(tmp_path, monkeypatch)
    request, bound = fixture["request"], fixture["provider_bound"]
    author = request.generation_intent
    facts = close_facts()
    intent = GenerationIntent.model_validate({**author.generation_intent.model_dump(mode="python"),
        "open_state": TypedStateReference(kind="typed_text", state_text="actor starts raising the closed red book"),
        "close_state": TypedStateReference(kind="typed_hash", state_hash=canonical_sha256(facts)),
        "close_causal_facts": facts,
        "subject_action": SubjectAction(start_state="actor supports the closed red book",
            progression="actor raises the book with the left hand",
            endpoint=ActionEndpoint(state_text="actor holds the raised book still"))})
    author = ProviderNeutralGenerationIntentProjection.create(**{
        **{name: getattr(author, name) for name in type(author).model_fields if name != "projection_hash"},
        "generation_intent": intent})
    request = VideoPlanningRequest.create(**{
        **request.model_dump(mode="python", exclude={"request_content_hash"}),
        "generation_intent": author, "previous_shot_state": None, "continuity_transition_policy": None})
    rule = semantic_rule("causal-close")
    rule.update(dimension="causal_state", observable=intent.close_state.state_hash,
        tolerance="exact", measurement="Inspect every dimension at the raw Shot close",
        intent_paths=["generation_intent.close_state.state_hash"])
    rule["semantics"]["source_refs"][0].update(source_hash=author.projection_hash,
        locator="generation_intent.close_causal_facts", quote="Explicit terminal declaration")
    rule["semantics"]["hard_basis"].update(source_hash=author.projection_hash,
        locator="generation_intent.close_causal_facts", necessity="The next Shot needs an exact accepted source endpoint")
    committer = ProductionStateCommitter(tmp_path)
    loaded = load_production_project(tmp_path / "project.yaml")
    qa = seal_artifact(loaded.qa_policy.model_copy(update={"revision": loaded.qa_policy.revision + 1,
        "content_hash": "0" * 64, "generation_acceptance": marked_policy([rule]),
        "generation_evaluation_authorities": (GenerationEvaluationAuthority(
            evaluator=loaded.qa_policy.semantic_authorities[0], proof="analyzer"),)}))
    committer.activate_qa_policy(qa, expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="fresh-authored-close-qa")
    loaded = load_production_project(tmp_path / "project.yaml")
    lifecycle = bound.lifecycle.model_copy(update={"hard_cut_keyframe_binding": None,
        "seal_terminal_frame": True,
        "base_project": loaded.manifest.active_project, "base_registry": loaded.manifest.active_registry,
        "base_dependency_graph": loaded.manifest.active_dependency_graph})
    plan = VideoPlanner().plan(request)
    projection = require_current_video_plan(current_request=request, plan=plan)
    def current(selected):
        return require_feedback_context(loaded=selected, planning_request=request, video_plan=plan,
            context=s._context(selected, request, plan, None),
            routing_policy=_policy(remote_authorized=True, budget_authorized=True), lifecycle=lifecycle)
    prepared = GenerationFeedbackOrchestrator.for_project(committer=committer,
        targets=(RegisteredGenerationTarget(provider=provider, profile=bound.provider_profile,
            compiler_contract=bound.compiler_contract, output_requirement=bound.output_requirement),),
        context_loader=current, policy=fixture["source"]["binding"].inputs.policy).prepare(
            limits=fixture["source"]["binding"].inputs.limits.model_copy(update={"task_id": "fresh-native-close",
                "allowed_remote_candidates": (f"{bound.provider_name}/{bound.capability_id}",)}))
    assert prepared.execution_binding is not None, (prepared.decision, prepared.compilation)
    return dict(provider=provider, prepared=prepared, requirement=projection.requirement,
        provider_bound=prepared.decision.routing.provider_bound_request, committer=committer,
        loaded=loaded, fixture=fixture)


def test_fresh_source_native_close_and_exact_pre_submit_zero_effects(tmp_path, monkeypatch):
    from ai_video.production.video_generation import VideoGenerationService
    from ai_video.production.project import load_production_project

    f = fresh_fixture(tmp_path, monkeypatch)
    prepared = f["prepared"]
    bound = f["provider_bound"]
    assert f["requirement"].continuity_mode.value == "none"
    prompt = prepared.compilation.request.prompt_text
    for fact in close_facts().values():
        assert fact in prompt
    assert f["requirement"].generation_intent.close_state.state_hash not in prompt
    assert prepared.execution_binding.continuity_routing is None
    service = VideoGenerationService(committer=f["committer"], provider=f["provider"])
    service.start(attempt_id="fresh-native-close", request=prepared.resolved_request,
        execution_binding=prepared.execution_binding)
    loaded = load_production_project(tmp_path / "project.yaml")
    state = next(a.video_generation_state for a in loaded.manifest.attempts if a.attempt_id == "fresh-native-close")
    service._validate_generation_execution_binding(state, prepared.resolved_request)
    assert state.phase.value == "request"


@pytest.mark.parametrize("grammar", ["remote", "local"])
def test_close_uses_authored_facts_and_no_digest(tmp_path, monkeypatch, grammar):
    from ai_video.production._remote_video_native_prompt import compile_remote_video_prompt
    from ai_video.production._h3_prompt import compile_h3_prompt

    f = fresh_fixture(tmp_path, monkeypatch)
    compile_prompt = compile_remote_video_prompt if grammar == "remote" else compile_h3_prompt
    result = compile_prompt(f["requirement"], provider_bound=f["provider_bound"])
    assert result.outcome == "compiled", result
    assert all(fact in result.prompt_text for fact in close_facts().values())
    assert f["requirement"].generation_intent.close_state.state_hash not in result.prompt_text
    assert "generation_intent.close_state.state_hash" in result.expressed_control_paths


@pytest.mark.parametrize("defect", ["target", "intent", "hash", "missing", "bound"])
def test_close_expression_reopens_exact_sealed_input(tmp_path, monkeypatch, defect):
    from ai_video.production._remote_video_native_prompt import compile_remote_video_prompt

    f = fresh_fixture(tmp_path, monkeypatch)
    requirement, bound = f["requirement"], f["provider_bound"]
    if defect == "target":
        requirement = requirement.model_copy(update={"target_shot": requirement.target_shot.model_copy(update={"shot_id": "wrong-shot"})})
    elif defect == "bound":
        bound = bound.model_copy(update={"requirement_hash": "f" * 64})
    else:
        intent = requirement.generation_intent
        if defect == "intent":
            intent = intent.model_copy(update={"subject_action": intent.subject_action.model_copy(update={"progression": "a stale action"})})
        elif defect == "hash":
            intent = intent.model_copy(update={"close_state": TypedStateReference(kind="typed_hash", state_hash="f" * 64)})
        else:
            facts = dict(intent.close_causal_facts)
            facts.pop(next(iter(facts)))
            intent = intent.model_copy(update={"close_causal_facts": facts})
        requirement = requirement.model_copy(update={"generation_intent": intent})
    result = compile_remote_video_prompt(requirement, provider_bound=bound)
    assert result.outcome == "unsupported"
    assert "generation_intent.close_state" in result.unsupported_field_paths


@pytest.mark.parametrize("equal", [False, True])
@pytest.mark.parametrize("grammar", ["remote", "local"])
def test_opening_proof_never_authorizes_current_close(tmp_path, equal, grammar):
    from test_typed_causal_native_expression import canonical_expression_fixture, expression_context
    from ai_video.production._remote_video_native_prompt import compile_remote_video_prompt
    from ai_video.production._h3_prompt import compile_h3_prompt

    f = canonical_expression_fixture(tmp_path, close_hash=True, equal_close=equal, arbitrary_close=not equal)
    expression = expression_context(f)
    intent = f["requirement"].generation_intent
    assert (intent.open_state.state_hash == intent.close_state.state_hash) is equal
    compiler = compile_remote_video_prompt if grammar == "remote" else compile_h3_prompt
    result = compiler(f["requirement"], provider_bound=f["provider_bound"], continuity_expression=expression)
    assert result.outcome == "unsupported"
    assert result.unsupported_field_paths == ("generation_intent.close_state",)


def test_local_uses_the_existing_verified_opening_owner(tmp_path):
    from test_typed_causal_native_expression import canonical_expression_fixture, expression_context
    from ai_video.production._h3_prompt import compile_h3_prompt

    f = canonical_expression_fixture(tmp_path)
    result = compile_h3_prompt(f["requirement"], provider_bound=f["provider_bound"],
        continuity_expression=expression_context(f))
    assert result.outcome == "compiled", result
    assert f["requirement"].generation_intent.open_state.state_hash not in result.prompt_text
    assert all(change.target_open in result.prompt_text for change in f["routing"].transition_policy.causal_state_changes)


def test_close_qa_item_contains_exact_preimage_and_rejects_missing_input(tmp_path, monkeypatch):
    from ai_video.production.generation_evaluation_criteria import evaluation_items

    f = fresh_fixture(tmp_path, monkeypatch)
    candidate = f["prepared"].execution_binding.inputs.candidates[0]
    values = dict(acceptance=candidate.recipe.acceptance_policy,
        qa_policy_content_hash=f["loaded"].qa_policy.content_hash,
        request_hash=f["prepared"].resolved_request.request_input_hash,
        artifact_sha256="c" * 64, size_bytes=32)
    rule = candidate.recipe.expressions[0]
    assert rule.intent_paths == ("generation_intent.close_state.state_hash",)
    assert rule.observable == f["requirement"].generation_intent.close_state.state_hash
    item, = evaluation_items(**values, requirement=f["requirement"])
    assert item.observable == rule.observable
    assert all(fact in item.question_text for fact in close_facts().values())
    with pytest.raises(ValueError, match="preimage"):
        evaluation_items(**values)


def test_evaluator_reopen_rejects_hash_only_stale_or_other_shot_truth(tmp_path, monkeypatch):
    import json
    from ai_video.production.generation_evaluation import GenerationEvaluationSource, GenerationObservation, project_generation_evaluation_sources
    from ai_video.production.generation_evaluation_criteria import evaluation_items, PresentationEvidence
    from ai_video.production.video_requirement import ProviderNeutralVideoRequirement

    f = fresh_fixture(tmp_path, monkeypatch)
    candidate = f["prepared"].execution_binding.inputs.candidates[0]
    acceptance, qa = candidate.recipe.acceptance_policy, f["loaded"].qa_policy
    values = dict(acceptance=acceptance, qa_policy_content_hash=qa.content_hash,
        request_hash=f["prepared"].resolved_request.request_input_hash, artifact_sha256="c" * 64, size_bytes=32)
    item, = evaluation_items(**values, requirement=f["requirement"])
    def source_for(question):
        source = GenerationEvaluationSource(schema_version="generation-evaluation/2",
            request_hash=values["request_hash"], artifact_sha256="c" * 64, size_bytes=32,
            rubric_hash=acceptance.profile_content_hash, qa_policy_content_hash=qa.content_hash, qa_policy_snapshot=qa,
            evaluator=qa.semantic_authorities[0], proof="analyzer", observations=(GenerationObservation(
                requirement_id=question.requirement_id, verdict="PASS", observation="scripted offline answer",
                evaluation_item_hash=question.evaluation_item_hash, question_text=question.question_text,
                presentation_ref="fixture/question", answer_ref="fixture/answer"),))
        return source.model_copy(update={"presentation_evidence": PresentationEvidence(namespace="controlled-evaluator/1",
            interaction_ref="fixture", presentation_ref="fixture/question", answer_ref="fixture/answer",
            event_order=("presentation", "answer"), actor_name=source.evaluator.name, actor_version=source.evaluator.version,
            items=(question,), answers_json=json.dumps(source.answer_payload()))})
    source = source_for(item)
    assert project_generation_evaluation_sources(sources=(source,), acceptance=acceptance,
        requirement=f["requirement"])[0][0].verdict == "PASS"
    for measurement in (candidate.recipe.expressions[0].measurement, item.measurement + " stale fact"):
        with pytest.raises(ValueError, match="canonical evaluation items"):
            project_generation_evaluation_sources(sources=(source_for(item.model_copy(update={"measurement": measurement})),),
                acceptance=acceptance, requirement=f["requirement"])
    with pytest.raises(ValueError, match="preimage"):
        project_generation_evaluation_sources(sources=(source,), acceptance=acceptance)
    requirement = f["requirement"]
    other = ProviderNeutralVideoRequirement.create(**{
        **requirement.model_dump(mode="python", exclude={"requirement_id", "requirement_hash"}),
        "target_shot": requirement.target_shot.model_copy(update={"shot_id": "other-shot"})})
    with pytest.raises(ValueError, match="canonical evaluation items"):
        project_generation_evaluation_sources(sources=(source,), acceptance=acceptance, requirement=other)


def test_native_compiler_rejects_forged_close_control_paths(tmp_path, monkeypatch):
    import hashlib
    from ai_video.production.video_compiler import compile_provider_video_request, ProviderNativePrompt

    f = fresh_fixture(tmp_path, monkeypatch)
    bound = f["provider_bound"]
    text = "Closing state: " + f["requirement"].generation_intent.close_state.state_hash
    forged = ProviderNativePrompt(grammar_contract="remote-video-prose-v1", prompt_text=text,
        prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
        expressed_control_paths=("generation_intent.close_state.state_hash", "generation_intent.close_causal_facts"))
    result = compile_provider_video_request(provider_bound=bound, requirement=f["requirement"],
        compiler_id=bound.compiler_contract.compiler_id, compiler_version=bound.compiler_contract.compiler_version,
        capabilities=f["provider"].capabilities(), native_prompt=forged)
    assert result.outcome == "unsupported"
    assert result.reason.value == "PROMPT_EXPRESSION_UNSUPPORTED"


@pytest.mark.parametrize("endpoint", ["open_state", "close_state", "action_endpoint"])
def test_legacy_native_grammar_cannot_bypass_causal_endpoint_authority(tmp_path, monkeypatch, endpoint):
    import hashlib
    from ai_video.production.video_requirement import ProviderNeutralVideoRequirement
    from ai_video.production.shot_router import ProviderBoundVideoRequest
    from ai_video.production.video_compiler import compile_provider_video_request, ProviderNativePrompt

    f = fresh_fixture(tmp_path, monkeypatch)
    requirement = f["requirement"]
    state = requirement.generation_intent.close_state
    if endpoint == "action_endpoint":
        from ai_video.production.video_requirement import SubjectAction, ActionEndpoint

        intent = GenerationIntent(subject_action=SubjectAction(endpoint=ActionEndpoint(state_hash=state.state_hash)))
    else:
        intent = GenerationIntent(**{endpoint: state})
    requirement = ProviderNeutralVideoRequirement.create(**{
        **requirement.model_dump(mode="python", exclude={"requirement_id", "requirement_hash"}),
        "contract_version": "provider-neutral-video-requirement/1", "generation_intent": intent,
        "conditioning_compatibility": None})
    bound = ProviderBoundVideoRequest.create(**{
        **{name: getattr(f["provider_bound"], name) for name in ProviderBoundVideoRequest.model_fields
            if name != "provider_bound_request_hash"},
        "requirement_hash": requirement.requirement_hash, "generation_recipe": None})
    for text in ("Generate a Shot.", "Causal state: " + state.state_hash):
        result = compile_provider_video_request(provider_bound=bound, requirement=requirement,
            compiler_id=bound.compiler_contract.compiler_id, compiler_version=bound.compiler_contract.compiler_version,
            capabilities=f["provider"].capabilities(), native_prompt=ProviderNativePrompt(
                grammar_contract="legacy-fixture/1", prompt_text=text,
                prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
                expressed_control_paths=(f"generation_intent.{endpoint}.state_hash",)))
        assert result.outcome == "unsupported"
        assert result.reason.value == "PROMPT_EXPRESSION_UNSUPPORTED"


def test_offline_fresh_source_raw_pass_activation_terminal_and_reopen(tmp_path, monkeypatch):
    import asyncio
    import hashlib
    from dataclasses import replace
    from ai_video.production.project import load_production_project
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_generation import VideoGenerationService
    from ai_video.production.video_fake import ScriptedFakeVideoProvider, FakeVideoScenario
    from ai_video.production.video import VideoTaskState
    from ai_video.production.generation_evaluation import GenerationEvaluationSource, GenerationObservation
    from ai_video.production.generation_evaluation_criteria import evaluation_items
    from ai_video.production.generation_feedback import record_attempt_evaluation
    from ai_video.production._sequence_source import accepted_sequence_source
    from ai_video_mcp.generation_feedback import ControlledPresentationVerifier, GenerationReviewInput
    from production_project_factory import make_p8_video_candidate_preparer
    from test_production_video import _paid_preview, _paid_authorization
    import test_production_generated_video_e2e as e

    f = fresh_fixture(tmp_path, monkeypatch)
    prepared = f["prepared"]
    resolved = prepared.resolved_request
    scripted = ScriptedFakeVideoProvider(capabilities=f["provider"].capabilities(),
        artifact_bytes=e.FIXTURE.read_bytes(), scenario=FakeVideoScenario(status_events=(VideoTaskState.SUCCEEDED,),
            external_effect_id="offline-fresh-task", provider_file_id="offline-fresh-file"))
    scripted.compile_request = f["provider"].compile_request
    scripted.resolve = f["provider"].resolve
    preview = _paid_preview(resolved, attempt_id="fresh-native-close", video_preview=scripted.preview(resolved))
    authorization = _paid_authorization(preview)
    inputs = replace(f["fixture"]["source"]["inputs"], project=f["loaded"])
    committer = ProductionStateCommitter(tmp_path, video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        paid_provider_authorizer=lambda exact: authorization if exact == preview else None,
        paid_provider_clock=lambda: authorization.issued_at)
    service = VideoGenerationService(committer=committer, provider=scripted)
    service.start(attempt_id="fresh-native-close", request=resolved, execution_binding=prepared.execution_binding)
    # All runtime effects below are confined to ScriptedFakeVideoProvider and tmp_path.
    service.submit_once(attempt_id="fresh-native-close", paid_preview=preview, reservation_id="offline-fresh-reservation")
    service.refresh_once(attempt_id="fresh-native-close")
    committer.settle_paid_provider_reservation(attempt_id="fresh-native-close", actual_cost_microunits=1_000_000)
    service.fetch_once(attempt_id="fresh-native-close")
    candidate = prepared.execution_binding.inputs.candidates[0]
    qa = f["loaded"].qa_policy
    digest = hashlib.sha256(e.FIXTURE.read_bytes()).hexdigest()
    items = evaluation_items(acceptance=candidate.recipe.acceptance_policy, qa_policy_content_hash=qa.content_hash,
        request_hash=resolved.request_input_hash, artifact_sha256=digest, size_bytes=len(e.FIXTURE.read_bytes()),
        requirement=f["requirement"])
    def scripted_evaluation(presented):
        assert presented.request is None and presented.projection is None and presented.recipe is None
        item, = presented.evaluation_items
        assert all(fact in item.question_text for fact in close_facts().values())
        return (GenerationEvaluationSource(schema_version="generation-evaluation/2",
            request_hash=resolved.request_input_hash, artifact_sha256=digest, size_bytes=len(e.FIXTURE.read_bytes()),
            rubric_hash=candidate.recipe.rubric_hash, qa_policy_content_hash=qa.content_hash, qa_policy_snapshot=qa,
            evaluator=qa.semantic_authorities[0], proof="analyzer", observations=(GenerationObservation(
                requirement_id="causal-close", verdict="PASS", observation="Scripted complete close-state PASS; no live quality claim",
                question_text=item.question_text, evaluation_item_hash=item.evaluation_item_hash,
                presentation_ref=presented.presentation_ref, answer_ref=presented.answer_ref),)),)
    verified = asyncio.run(ControlledPresentationVerifier(evaluator=qa.semantic_authorities[0], proof="analyzer",
        adjudicate=scripted_evaluation).present_and_verify(review_input=GenerationReviewInput(
            resolved, prepared.execution_binding.projection, candidate.recipe, qa, None, items),
            attempt_id="fresh-native-close"))
    record_attempt_evaluation(committer=committer, attempt_id="fresh-native-close",
        evaluation_sources=verified.sources, presentation_proof=verified.recording_proof)
    service.validate_once(attempt_id="fresh-native-close")
    service.activate_once(attempt_id="fresh-native-close")
    loaded = load_production_project(tmp_path / "project.yaml")
    shot = next(s for s in loaded.shots if s.shot_id == f["requirement"].target_shot.shot_id)
    binding, request, terminal, hashes, _ = accepted_sequence_source(loaded, shot, require_causal_close=True)
    assert binding.projection.requirement == f["requirement"]
    assert request.request_input_hash == resolved.request_input_hash
    assert hashes and terminal is not None
