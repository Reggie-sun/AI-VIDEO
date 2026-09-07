"""Generation decisions exercise the public Router and real compiler seams."""

import pytest
import hashlib

from ai_video.production.generation_recipe import GenerationRecipe, SeedPolicy
from ai_video.production.generation_decision import (
    DecisionInputs, DecisionPolicy, ExecutionLimits, GenerationCandidate,
)
from ai_video.production.shot_router import VideoGenerationResolver
from ai_video.production.shot_router import AdapterCompilerContract, ContinuityMode
from ai_video.planning.video_planner import VideoPlanner
from ai_video.production.generation_recipe import RequirementExpression
from ai_video.production.generation_decision import InputConflict
from ai_video.production.generation_diagnosis import (
    AttemptEvidence, Finding, Intervention, diagnose_attempt, compare_compiled_requests,
    intervention_prediction_outcome, verify_intervention_comparison,
)
from ai_video.production.video_compiler import (
    compile_provider_video_request, ProviderNativePrompt, ProviderRequirementUnsupported,
)
from ai_video.production.video import VideoGenerationMode, VideoExecutionKind
from test_production_shot_router import (
    _context, _verified_requirement, _variant, _capabilities, _profile, _output,
    _lifecycle, _policy,
)

HASH = "a" * 64


def acceptance_policy(expressions):
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.hashing import canonical_sha256
    ids = tuple(r.requirement_id for r in expressions if r.level == "acceptance")
    payload = dict(domain_id="test", profile_id="test-rubric", profile_version="1",
                   measurement_contract_version="1", required_requirement_ids=ids,
                   generation_requirements=tuple(r.model_dump(mode="json", exclude={"native_text"}) for r in expressions))
    digest = canonical_sha256(payload)
    return DomainAcceptancePolicy(domain_id="test", profile_id="test-rubric", profile_version="1",
                                   profile_content_hash=digest, measurement_contract_version="1",
                                   required_requirement_ids=ids, profile_payload={**payload, "content_hash": digest})


def recipe_with_rules(recipe, rules):
    policy = acceptance_policy(rules)
    return recipe.model_copy(update={"expressions": rules, "acceptance_policy": policy,
                                     "rubric_hash": policy.profile_content_hash})


def setup_decision(*, remote=False, seed_supported=True, reference_hash=None):
    from test_production_shot_router import _asset, _first_frame_projection
    keyframe = _asset("first_frame", "frame", reference_hash) if reference_hash else None
    context = _context(continuity=ContinuityMode.NONE, important=False, keyframe=keyframe)
    projection = _first_frame_projection(context) if reference_hash else _verified_requirement(context)
    compiler = AdapterCompilerContract.create(compiler_id="test-native", compiler_version="2")
    variant = _variant(VideoGenerationMode.IMAGE_TO_VIDEO if reference_hash else VideoGenerationMode.TEXT_TO_VIDEO,
                       execution_kind=VideoExecutionKind.REMOTE if remote else VideoExecutionKind.LOCAL)
    if remote or not seed_supported:
        from ai_video.production.video import VideoOutputRecoveryStrategy
        variant = variant.model_copy(update={"seed_supported": seed_supported,
                                              "output_recovery_strategy": VideoOutputRecoveryStrategy.REQUERY_BY_EFFECT_ID})
    expressions = (RequirementExpression(
            requirement_id="duration", level="acceptance", stage="raw_generation",
            dimension="action_and_time", observable="4 seconds usable", tolerance="exact",
            measurement="probe", proof="technical", intent_paths=("output_need.duration_seconds",),
            native_text=("4",), production_owner="shot_authoring"),)
    acceptance = acceptance_policy(expressions)
    recipe = GenerationRecipe(
        seed=SeedPolicy(kind="fixed", value=42) if seed_supported else SeedPolicy(kind="uncontrolled"),
        profile_sha256=_profile().profile_sha256, compiler_hash=compiler.compiler_hash,
        requirement_hash=projection.requirement.requirement_hash, rubric_hash=acceptance.profile_content_hash,
        acceptance_policy=acceptance, expressions=expressions,
    )
    candidate = GenerationCandidate(candidate_id="one", provider_profile=_profile(),
                                    capabilities=_capabilities(variant), capability_id=variant.capability_id,
                                    compiler_contract=compiler, output_requirement=_output(), recipe=recipe)
    inputs = DecisionInputs(projection_hash=projection.projection_hash,
                            facts_hash=VideoPlanner.generation_difficulty(projection)["facts_hash"],
                            rubric_hash=acceptance.profile_content_hash, policy=DecisionPolicy(allow_bounded_exploration=True),
                            limits=ExecutionLimits(task_id="task", generation_forbidden=False,
                                                   paid_submit_ceiling=2, paid_submits_used=0,
                                                   local_batch_limit=3, local_batch_used=0,
                                                   local_total_used=0, local_resource_available=True),
                            candidates=(candidate,))
    lifecycle = _lifecycle(context)
    if keyframe is not None:
        lifecycle = lifecycle.model_copy(update={"input_artifact_ids": (context.target_shot_id, keyframe.asset_id)})
    return dict(projection=projection, context=context, policy=_policy(remote_authorized=True, budget_authorized=True),
                lifecycle=lifecycle, inputs=inputs)


def decide(setup, **updates):
    return VideoGenerationResolver().resolve_requirement(
        **{**setup, "inputs": setup["inputs"].model_copy(update=updates)})


def evidence(setup, *, candidate=None, verdict="PASS", proof="technical", outcome="media", attempt="1", **updates):
    inputs = setup["inputs"]
    candidate = candidate or inputs.candidates[0]
    return AttemptEvidence(
        **{**dict(task_id="historical-task", shot_id=setup["context"].target_shot_id, attempt_id=attempt,
                  recipe_scope_hash=candidate.scope_hash, facts_hash=inputs.facts_hash, rubric_hash=candidate.recipe.rubric_hash,
                  request_hash="b" * 64, artifact_sha256=hashlib.sha256(attempt.encode()).hexdigest() if outcome == "media" else None,
                  outcome=outcome, runtime_reason="OOM" if outcome == "runtime_failure" else None,
                  findings=(Finding(requirement_id="duration", rubric_hash=candidate.recipe.rubric_hash, stage="raw_generation",
                                    proof=proof, verdict=verdict, source_sha256="c" * 64,
                                    observation="exact measured evidence"),) if outcome == "media" else ()),
           **updates})


def compile_decision(result, setup):
    c = next(c for c in setup["inputs"].candidates if c.candidate_id == result.selected_candidate_id)
    text = "Generate 4 seconds."
    return compile_provider_video_request(
        provider_bound=result.routing.provider_bound_request, requirement=setup["projection"].requirement,
        compiler_id=c.compiler_contract.compiler_id, compiler_version=c.compiler_contract.compiler_version,
        capabilities=c.capabilities,
        native_prompt=ProviderNativePrompt(grammar_contract="test-native/2", prompt_text=text,
                                          prompt_sha256=hashlib.sha256(text.encode()).hexdigest()))


def test_new_task_cannot_use_external_preselection():
    with pytest.raises(TypeError):
        VideoGenerationResolver().resolve_requirement(selected_capability_id="old")


def test_seed_policy_requires_explicit_value_and_uncontrolled_is_honest():
    with pytest.raises(ValueError):
        SeedPolicy(kind="fixed")
    assert SeedPolicy(kind="uncontrolled").value is None
    assert SeedPolicy(kind="fixed", value=42).value == 42


def test_a1_a3_readiness_is_not_quality_and_unknown_is_bounded():
    setup = setup_decision()
    result = decide(setup)
    assert result.disposition == "GENERATE_ONCE"
    assert result.assessments[0].fit == "unknown"
    assert "no quality guarantee" in result.rationale[0]
    assert decide(setup, policy=DecisionPolicy()).disposition == "INSUFFICIENT_EVIDENCE"


def test_a2_unauthorized_supported_provider_is_only_a_recommendation():
    setup = setup_decision(remote=True)
    e = evidence(setup, shot_id="historical-shot")
    result = decide(setup, evidence=(e,))
    assert result.disposition == "CHANGE_PROVIDER_MODEL"
    assert result.routing is None
    assert result.assessments[0].fit == "supported"
    assert "REMOTE_SCOPE_NOT_AUTHORIZED" in result.assessments[0].reasons


@pytest.mark.parametrize("outcome,expected", [("runtime_failure", "RUNTIME_FAILURE"),
                                               ("unknown_outcome", "UNKNOWN_OUTCOME")])
def test_a8_a12_no_media_is_not_model_quality_failure(outcome, expected):
    setup = setup_decision()
    e = evidence(setup, outcome=outcome, task_id="task")
    result = decide(setup, evidence=(e,), latest_attempt_hash=e.evidence_hash)
    assert result.disposition == expected
    assert result.assessments[0].fail_count == 0
    assert result.routing is None


def test_known_exact_recovery_keeps_unknown_history_without_permanent_block():
    setup = setup_decision()
    unknown = evidence(setup, outcome="unknown_outcome", task_id="task")
    recovered = evidence(setup, task_id="task")
    result = decide(setup, evidence=(unknown, recovered), latest_attempt_hash=recovered.evidence_hash)
    assert result.disposition == "REVIEW_CURRENT_RESULT"
    unrelated = recovered.model_copy(update={"request_hash": "e" * 64})
    result = decide(setup, evidence=(unknown, unrelated), latest_attempt_hash=unrelated.evidence_hash)
    assert result.disposition == "UNKNOWN_OUTCOME"


def test_prepared_only_latest_cannot_erase_submitted_failure():
    setup = setup_decision()
    failed = evidence(setup, verdict="FAIL", task_id="task")
    prepared = evidence(setup, outcome="not_submitted", task_id="task", attempt="prepared-only")
    result = decide(setup, evidence=(failed, prepared), latest_attempt_hash=prepared.evidence_hash,
                    policy=DecisionPolicy(max_resamples=0))
    assert result.disposition == "EVIDENCE_GAP"
    assert result.routing is None


def test_a8_evidence_repair_first_on_the_same_bytes():
    setup = setup_decision()
    e = evidence(setup, verdict="NOT_EVALUATED", task_id="task")
    result = decide(setup, evidence=(e,), latest_attempt_hash=e.evidence_hash)
    assert result.disposition == "EVIDENCE_GAP"
    assert result.assessments[0].not_evaluated_count == 1
    assert result.routing is None


def test_a5_a9_conflicts_return_to_owner_without_rewriting_verdict():
    setup = setup_decision()
    for kind, disposition in (("reference", "CHANGE_REFERENCE_STRATEGY"),
                               ("rubric", "RUBRIC_OR_STAGE_ERROR")):
        conflict = InputConflict(kind=kind, source_sha256=HASH, observation="endpoint/stage conflict",
                                 affected_requirements=("duration",), next_owner="authoring")
        result = decide(setup, conflicts=(conflict,))
        assert result.disposition == disposition
        assert result.routing is None


def test_a6_fixed_seed_survives_independent_attempt_identity():
    setup = setup_decision()
    first = compile_decision(decide(setup), setup).request
    setup2 = {**setup, "lifecycle": setup["lifecycle"].model_copy(update={"generation_id": "generation-new"})}
    second = compile_decision(decide(setup2), setup2).request
    assert first.request_input_hash != second.request_input_hash
    assert first.seed == second.seed == 42
    from ai_video.production.comfy_t8_native_turbo_video import _effective_seed
    assert _effective_seed(first) == _effective_seed(second) == 42
    assert compare_compiled_requests(first, second)["changed_variables"] == ()


def test_a6_uncontrolled_seed_stays_uncontrolled():
    setup = setup_decision(remote=True, seed_supported=False)
    setup["inputs"] = setup["inputs"].model_copy(update={
        "limits": setup["inputs"].limits.model_copy(update={"allowed_remote_candidates": ("one",)})})
    request = compile_decision(decide(setup), setup).request
    assert request.seed is None
    assert compare_compiled_requests(request, request)["uncontrolled_stochasticity"]


def test_a9_final_captions_are_not_raw_findings_and_hints_cannot_block():
    setup = setup_decision()
    recipe = setup["inputs"].candidates[0].recipe
    rule = recipe.expressions[0]
    recipe = recipe_with_rules(recipe, (rule,
        rule.model_copy(update={"requirement_id": "subtitles", "stage": "final_composition"})))
    c = setup["inputs"].candidates[0].model_copy(update={"recipe": recipe})
    assert diagnose_attempt(evidence(setup, candidate=c), recipe).all_required_observed_pass
    hint = rule.model_copy(update={"requirement_id": "deadline", "level": "recipe_hint"})
    hinted = recipe_with_rules(recipe, (hint, rule))
    c = c.model_copy(update={"recipe": hinted})
    e = evidence(setup, candidate=c, verdict="FAIL")
    e = e.model_copy(update={"findings": (e.findings[0].model_copy(update={"requirement_id": "deadline"}),)})
    diagnosis = diagnose_attempt(e, hinted)
    assert "RUBRIC_OR_STAGE_ERROR" in diagnosis.failure_classes
    assert not diagnosis.all_required_observed_pass


def test_a10_human_rejection_survives_technical_pass():
    setup = setup_decision()
    passed = evidence(setup)
    human = passed.findings[0].model_copy(update={"proof": "human", "verdict": "FAIL"})
    e = passed.model_copy(update={"findings": (*passed.findings, human)})
    diagnosis = diagnose_attempt(e, setup["inputs"].candidates[0].recipe)
    assert diagnosis.failed_requirements == ("duration",)
    assert not diagnosis.all_required_observed_pass


def test_a11_limit_and_no_new_hypothesis_stop_without_resetting_task_count():
    setup = setup_decision()
    limits = setup["inputs"].limits.model_copy(update={"local_batch_used": 3, "local_total_used": 30})
    result = decide(setup, limits=limits)
    assert result.disposition == "BLOCKED_EXECUTION"
    assert "LOCAL_BATCH_REVIEW_REQUIRED" in result.assessments[0].reasons
    e = evidence(setup, verdict="FAIL", task_id="task")
    assert decide(setup, evidence=(e,), latest_attempt_hash=e.evidence_hash).disposition == "REASSESS_FEASIBILITY"


def test_a12_stale_current_projection_and_recipe_fail_closed():
    setup = setup_decision()
    with pytest.raises(ValueError, match="stale"):
        decide(setup, projection_hash="0" * 64)
    c = setup["inputs"].candidates[0]
    c = c.model_copy(update={"recipe": c.recipe.model_copy(update={"requirement_hash": "0" * 64})})
    with pytest.raises(ValueError, match="stale"):
        decide(setup, candidates=(c,))


def test_a13_feedback_changes_decision_and_unrelated_model_does_not():
    setup = setup_decision()
    failures = tuple(evidence(setup, verdict="FAIL", attempt=str(i), shot_id="historical-shot") for i in range(3))
    assert decide(setup).disposition == "GENERATE_ONCE"
    assert decide(setup, evidence=failures).disposition == "CAPABILITY_BOUNDARY"
    stale = tuple(e.model_copy(update={"recipe_scope_hash": "0" * 64}) for e in failures)
    result = decide(setup, evidence=stale)
    assert result.disposition == "GENERATE_ONCE"
    assert len(result.assessments[0].ignored_evidence_hashes) == 3


def test_a14_old_exact_binding_bytes_remain_hash_compatible():
    setup = setup_decision()
    c = setup["inputs"].candidates[0]
    result = VideoGenerationResolver()._bind_requirement(
        **{k: v for k, v in setup.items() if k != "inputs"}, provider_profile=c.provider_profile,
        capabilities=c.capabilities, selected_capability_id=c.capability_id,
        output_requirement=c.output_requirement, compiler_contract=c.compiler_contract)
    payload = result.provider_bound_request.model_dump(mode="json")
    assert "generation_recipe" not in payload
    from ai_video.production.hashing import canonical_sha256
    expected = canonical_sha256({"schema": "provider-bound-video-request/1",
                                 **{k: v for k, v in payload.items() if k != "provider_bound_request_hash"}})
    assert payload["provider_bound_request_hash"] == expected


def test_a15_compiler_rejects_unexpressed_requirement():
    setup = setup_decision()
    c = setup["inputs"].candidates[0]
    rule = c.recipe.expressions[0].model_copy(update={"native_text": ("impossible omitted clause",)})
    c = c.model_copy(update={"recipe": c.recipe.model_copy(update={"expressions": (rule,)})})
    setup["inputs"] = setup["inputs"].model_copy(update={"candidates": (c,)})
    compiled = compile_decision(decide(setup), setup)
    assert isinstance(compiled, ProviderRequirementUnsupported)
    assert compiled.unsupported_field_paths == ("duration",)


def test_a16_registration_order_tie_and_audit_only_changes():
    setup = setup_decision()
    c = setup["inputs"].candidates[0]
    second = c.model_copy(update={"candidate_id": "two"})
    a = decide(setup, candidates=(c, second))
    b = decide(setup, candidates=(second, c))
    assert a == b
    assert a.disposition == "UNRESOLVED_TIE"
    e = evidence(setup, shot_id="historical-shot")
    first = decide(setup)
    informed = decide(setup, evidence=(e,))
    assert first.decision_hash != informed.decision_hash
    assert first.routing.provider_bound_request.provider_bound_request_hash == informed.routing.provider_bound_request.provider_bound_request_hash


def test_a17_local_exemption_and_explicit_forbidden_scope():
    setup = setup_decision()
    setup["policy"] = _policy(remote_authorized=False, budget_authorized=False)
    assert decide(setup).disposition == "GENERATE_ONCE"
    limits = setup["inputs"].limits.model_copy(update={"generation_forbidden": True})
    assert decide(setup, limits=limits).routing is None


def test_multiple_records_of_same_bytes_are_one_sample():
    setup = setup_decision()
    e = evidence(setup)
    duplicate = e.model_copy(update={"attempt_id": "another-record"})
    result = decide(setup, evidence=(e, duplicate))
    assert result.assessments[0].sample_count == 1


def intervention(e, **updates):
    return Intervention(**{**dict(
        intervention_id="replace-endpoint", candidate_id="one", purpose="diagnostic",
        disposition="GENERATE_ONCE", closes=("duration",), support=(e.evidence_hash,),
        changed_variables=("image_bindings",), held_constants=("seed", "prompt_text"),
        uncontrolled_variables=(), regression_risks=("hand motion",),
        hypothesis="endpoint conditioning conflicts with the intended motion",
        confidence_basis="exact failure span; causal effect remains uncertain",
        improvement_prediction="motion no longer freezes at the endpoint",
        falsification_prediction="same frozen span despite new endpoint",
        insufficient_evidence_condition="missing dense frames or human viewing"), **updates})


def test_a4_actual_reference_intervention_fixed_seed_and_compiler_delta_guard():
    from ai_video.production.generation_diagnosis import seal_intervention_comparison
    before = setup_decision(reference_hash="a" * 64)
    baseline = compile_decision(decide(before), before).request
    e = evidence(before, verdict="FAIL", task_id="task", request_hash=baseline.request_input_hash)
    proposal = intervention(e)
    after = setup_decision(reference_hash="b" * 64)
    candidate = after["inputs"].candidates[0]
    recipe = candidate.recipe.model_copy(update={"comparison": seal_intervention_comparison(proposal, baseline)})
    after["inputs"] = after["inputs"].model_copy(update={
        "candidates": (candidate.model_copy(update={"recipe": recipe}),),
        "historical_recipes": before["inputs"].candidates,
        "baseline_request": baseline,
        "evidence": (e,), "latest_attempt_hash": e.evidence_hash, "interventions": (proposal,)})
    result = decide(after)
    assert result.disposition == "GENERATE_ONCE"
    compiled = compile_decision(result, after)
    assert compiled.outcome == "compiled"
    assert compiled.request.seed == baseline.seed == 42
    delta = verify_intervention_comparison(proposal, baseline, compiled.request)
    assert delta["changed_variables"] == ("image_bindings",)
    assert not delta["uncontrolled_stochasticity"]
    changed_seed = recipe.model_copy(update={"seed": SeedPolicy(kind="fixed", value=99)})
    bad_candidate = candidate.model_copy(update={"recipe": changed_seed})
    after["inputs"] = after["inputs"].model_copy(update={"candidates": (bad_candidate,)})
    rejected = compile_decision(decide(after), after)
    assert rejected.outcome == "unsupported"
    assert rejected.unsupported_field_paths == ("generation_recipe.comparison.actual_delta",)
    # A caller cannot repair that rejection by pretending the old seed was 99.
    from ai_video.production.hashing import canonical_sha256
    forged = recipe.comparison.model_copy(update={"variable_hashes": tuple(
        (name, canonical_sha256({"value": 99}) if name == "seed" else value)
        for name, value in recipe.comparison.variable_hashes)})
    after["inputs"] = after["inputs"].model_copy(update={"candidates": (
        bad_candidate.model_copy(update={"recipe": changed_seed.model_copy(update={"comparison": forged})}),)})
    with pytest.raises(ValueError, match="exact compiled baseline"):
        decide(after)


def test_historical_uncontrolled_seed_allows_fixed_seed_repair_with_explicit_delta():
    from ai_video.production.generation_diagnosis import verify_intervention_comparison
    from ai_video.production.video import VideoGenerationRequest

    setup = setup_decision(reference_hash="a" * 64)
    current = setup["inputs"].candidates[0]
    historical = GenerationCandidate.model_validate({
        **current.model_dump(mode="python"),
        "recipe": current.recipe.model_copy(update={"seed": SeedPolicy(kind="uncontrolled")}),
    })
    with pytest.raises(ValueError, match="current candidates"):
        DecisionInputs.model_validate({
            **setup["inputs"].model_dump(mode="python"), "candidates": (historical,),
        })
    unsupported = setup_decision(remote=True, seed_supported=False)["inputs"].candidates[0]
    with pytest.raises(ValueError, match="seed-supported capability"):
        GenerationCandidate.model_validate({
            **unsupported.model_dump(mode="python"),
            "recipe": unsupported.recipe.model_copy(update={"seed": SeedPolicy(kind="fixed", value=42)}),
        })

    controlled_baseline = compile_decision(decide(setup), setup).request
    baseline = VideoGenerationRequest.create(**{
        **controlled_baseline.model_dump(mode="python", exclude={"request_input_hash"}), "seed": None,
    })
    prior = evidence(setup, candidate=historical, verdict="FAIL", task_id="task",
                     request_hash=baseline.request_input_hash)
    proposal = intervention(prior, purpose="resample", resample_limit=1, changed_variables=("seed",),
                            held_constants=("prompt_text",), uncontrolled_variables=("seed",))
    setup["inputs"] = DecisionInputs.model_validate({
        **setup["inputs"].model_dump(mode="python"), "historical_recipes": (historical,),
        "evidence": (prior,), "latest_attempt_hash": prior.evidence_hash,
        "interventions": (proposal,), "baseline_request": baseline,
    })

    result = decide(setup)
    compiled = compile_decision(result, setup).request
    assert result.disposition == "GENERATE_ONCE"
    assert compiled.seed == 42
    assert result.routing.provider_bound_request.generation_recipe.comparison.changed_variables == ("seed",)
    assert verify_intervention_comparison(proposal, baseline, compiled)["uncontrolled_stochasticity"]


def test_a7_improving_target_does_not_inherit_other_requirement_acceptance():
    setup = setup_decision()
    recipe = setup["inputs"].candidates[0].recipe
    rule = recipe.expressions[0]
    other = rule.model_copy(update={"requirement_id": "performance", "dimension": "performance",
                                   "proof": "human"})
    recipe = recipe_with_rules(recipe, (rule, other))
    e = evidence(setup, candidate=setup["inputs"].candidates[0].model_copy(update={"recipe": recipe}))
    e = e.model_copy(update={"findings": (*e.findings, e.findings[0].model_copy(update={
        "requirement_id": "performance", "proof": "human", "verdict": "FAIL"}))})
    diagnosis = diagnose_attempt(e, recipe)
    assert diagnosis.preserved_requirements == ("duration",)
    assert diagnosis.failed_requirements == ("performance",)
    assert not diagnosis.all_required_observed_pass


def test_a18_new_selector_preserves_continuity_route_lock():
    from test_production_shot_router import (
        _sequence_fixture, _bound_route_identity, _transition_policy, _continuity_routing,
        _exact_terminal_projection,
    )
    from ai_video.production.video_transition import BoundaryKind, ContinuityObligation
    source, previous, context, lifecycle, _ = _sequence_fixture()
    route = _bound_route_identity(previous)
    transition = _transition_policy(source_context=source, target_context=context, lifecycle=lifecycle,
                                    boundary=BoundaryKind.WITHIN_CONTINUOUS_TAKE,
                                    obligation=ContinuityObligation.FULL_CONTINUITY,
                                    source_route=route, destination_route=route)
    binding = _continuity_routing(transition=transition, previous_bound=previous,
                                  previous_shot=source.activated_shot, destination_route=route)
    setup = setup_decision(reference_hash="b" * 64)
    projection = _exact_terminal_projection(context)
    c = setup["inputs"].candidates[0]
    c = c.model_copy(update={"recipe": c.recipe.model_copy(update={
        "requirement_hash": projection.requirement.requirement_hash})})
    setup.update(projection=projection, context=context, lifecycle=lifecycle, continuity_routing=binding)
    setup["inputs"] = setup["inputs"].model_copy(update={
        "projection_hash": projection.projection_hash,
        "facts_hash": VideoPlanner.generation_difficulty(projection)["facts_hash"], "candidates": (c,)})
    result = decide(setup)
    assert result.routing is None
    assert "CONTINUITY_PROVIDER_LOCKED" in result.assessments[0].reasons


def test_current_history_cannot_omit_latest_attempt_and_bypass_diagnosis():
    setup = setup_decision()
    e = evidence(setup, verdict="NOT_EVALUATED", task_id="task")
    assert decide(setup, evidence=(e,)).disposition == "EVIDENCE_GAP"


def test_raw_rubric_reinterpretation_retains_original_finding():
    setup = setup_decision()
    e = evidence(setup, verdict="FAIL")
    original_hash = e.evidence_hash
    original = setup["inputs"].candidates[0].recipe
    recipe = recipe_with_rules(original, (original.expressions[0].model_copy(update={"tolerance": "different"}),))
    result = diagnose_attempt(e, recipe)
    assert "RUBRIC_OR_STAGE_ERROR" in result.failure_classes
    assert e.evidence_hash == original_hash
    assert e.findings[0].verdict == "FAIL"


def test_partial_dimension_evidence_cannot_claim_supported_fit():
    setup = setup_decision()
    candidate = setup["inputs"].candidates[0]
    recipe = candidate.recipe
    human = recipe.expressions[0].model_copy(update={"requirement_id": "viewing", "proof": "human"})
    candidate = candidate.model_copy(update={"recipe": recipe_with_rules(recipe, (*recipe.expressions, human))})
    e = evidence(setup, candidate=candidate)
    result = decide(setup, candidates=(candidate,), evidence=(e,), rubric_hash=candidate.recipe.rubric_hash)
    assert result.assessments[0].fit == "unknown"
    assert result.assessments[0].pass_count == 0
    assert result.assessments[0].not_evaluated_count == 1


@pytest.mark.parametrize("dimension", ["action_and_time", "identity"])
def test_partial_dimension_proofs_on_different_artifacts_cannot_be_pooled(dimension):
    setup = setup_decision()
    candidate = setup["inputs"].candidates[0]
    recipe = candidate.recipe
    viewing = recipe.expressions[0].model_copy(update={
        "requirement_id": "viewing", "proof": "human", "dimension": dimension,
    })
    candidate = candidate.model_copy(update={"recipe": recipe_with_rules(recipe, (*recipe.expressions, viewing))})
    duration = evidence(setup, candidate=candidate, attempt="duration")
    viewing_only = evidence(setup, candidate=candidate, attempt="viewing")
    viewing_only = viewing_only.model_copy(update={"findings": (
        viewing_only.findings[0].model_copy(update={"requirement_id": "viewing", "proof": "human"}),
    )})
    result = decide(setup, candidates=(candidate,), evidence=(duration, viewing_only),
                    rubric_hash=candidate.recipe.rubric_hash)
    assessment = result.assessments[0]
    assert assessment.fit == "unknown"
    assert assessment.supported_dimensions == (() if dimension == "action_and_time" else ("action_and_time", "identity"))
    assert assessment.pass_count == 0


def test_recipe_cannot_omit_a_sealed_acceptance_item():
    setup = setup_decision()
    recipe = setup["inputs"].candidates[0].recipe
    second = recipe.expressions[0].model_copy(update={"requirement_id": "viewing", "proof": "human"})
    complete = recipe_with_rules(recipe, (*recipe.expressions, second))
    with pytest.raises(ValueError, match="omits"):
        GenerationRecipe.model_validate(complete.model_copy(update={"expressions": recipe.expressions}).model_dump(mode="python"))


def test_compiler_rejects_dropped_canonical_action_even_if_recipe_claims_duration_only():
    from test_production_provider_neutral_adapters import _replace_requirement
    from ai_video.production.video_requirement import SubjectAction
    setup = setup_decision()
    original = setup["projection"]
    projection = _replace_requirement(original, generation_intent=original.requirement.generation_intent.model_copy(update={
        "subject_action": SubjectAction(progression="Raise the LEFT hand and keep the RIGHT hand still")}))
    setup["projection"] = projection
    c = setup["inputs"].candidates[0]
    c = c.model_copy(update={"recipe": c.recipe.model_copy(update={"requirement_hash": projection.requirement.requirement_hash})})
    setup["inputs"] = setup["inputs"].model_copy(update={"candidates": (c,),
        "projection_hash": projection.projection_hash, "facts_hash": VideoPlanner.generation_difficulty(projection)["facts_hash"]})
    result = compile_decision(decide(setup), setup)
    assert result.outcome == "unsupported"
    assert "generation_intent.subject_action.progression" in result.unsupported_field_paths


def test_real_vidu_native_compiler_accepts_recipe_and_output_controls_without_placeholder():
    from test_production_vidu import _setup, _profile as vidu_profile, _native_prompt_intent
    from test_production_provider_neutral_adapters import _replace_requirement
    from ai_video.production.video_requirement import OutputNeed, AudioNeed
    setup = setup_decision(remote=True)
    provider, transport, args = _setup()
    output = args[0].effective_output
    projection = _replace_requirement(setup["projection"],
        generation_intent=_native_prompt_intent(setup["context"].activated_shot.scene_id),
        output_need=OutputNeed(duration_seconds=5, width=1280, height=720, aspect_ratio="16:9", fps=24, container_mime="video/mp4"),
        audio_need=AudioNeed.REQUIRED)
    compiler = AdapterCompilerContract.create(compiler_id="vidu-video-compiler", compiler_version="2")
    c = setup["inputs"].candidates[0]
    rules = (c.recipe.expressions[0].model_copy(update={"native_text": (), "observable": "5 seconds usable"}),)
    recipe = recipe_with_rules(c.recipe, rules).model_copy(update={
        "requirement_hash": projection.requirement.requirement_hash,
        "profile_sha256": vidu_profile().pointer().profile_sha256,
        "compiler_hash": compiler.compiler_hash})
    c = GenerationCandidate(candidate_id="one", provider_profile=vidu_profile().pointer(),
                            capabilities=provider.capabilities(), capability_id=args[0].capability_id,
                            compiler_contract=compiler, output_requirement=output, recipe=recipe)
    setup["projection"] = projection
    setup["inputs"] = setup["inputs"].model_copy(update={"candidates": (c,), "rubric_hash": recipe.rubric_hash,
        "projection_hash": projection.projection_hash, "facts_hash": VideoPlanner.generation_difficulty(projection)["facts_hash"],
        "limits": setup["inputs"].limits.model_copy(update={"allowed_remote_candidates": ("one",)})})
    decision = decide(setup)
    result = provider.compile_request(decision.routing.provider_bound_request, projection.requirement)
    assert result.outcome == "compiled", result
    resolved = provider.resolve(result.request)
    assert resolved.effective_seed == 42
    assert "The subject performs the authored action." in result.provider_native_prompt
    assert transport.calls == []


def test_intervention_rename_cannot_reset_semantic_resample_limit():
    setup = setup_decision()
    e = evidence(setup, verdict="FAIL", task_id="task")
    first = intervention(e, purpose="resample", resample_limit=1, changed_variables=("seed",), held_constants=())
    e = e.model_copy(update={"intervention_id": first.intervention_id, "intervention_semantic_hash": first.semantic_hash})
    renamed = first.model_copy(update={"intervention_id": "new-run-new-name", "support": (e.evidence_hash,)})
    assert renamed.semantic_hash == first.semantic_hash
    assert decide(setup, evidence=(e,), latest_attempt_hash=e.evidence_hash,
                  interventions=(renamed,)).disposition == "REASSESS_FEASIBILITY"


def test_intervention_semantics_ignore_explanatory_prose_but_bind_controlled_values():
    setup = setup_decision()
    proposed = intervention(evidence(setup), semantic_variable_hashes=(("image_bindings", "d" * 64),))
    reworded = proposed.model_copy(update={
        "hypothesis": "a differently worded explanation",
        "confidence_basis": "different prose",
        "improvement_prediction": "different predicted wording",
        "falsification_prediction": "different falsification wording",
        "insufficient_evidence_condition": "different evidence wording",
    })
    changed_target = proposed.model_copy(update={"semantic_variable_hashes": (("image_bindings", "e" * 64),)})
    assert reworded.semantic_hash == proposed.semantic_hash
    assert changed_target.semantic_hash != proposed.semantic_hash


def test_non_resample_generate_once_repair_cannot_be_a_noop():
    setup = setup_decision()
    with pytest.raises(ValueError, match="must change"):
        intervention(evidence(setup), purpose="production_repair", changed_variables=(),
                     held_constants=("seed", "prompt_text", "image_bindings"))


@pytest.mark.parametrize("purpose", ["production_repair", "diagnostic"])
def test_seed_only_operation_cannot_be_relabeled_to_bypass_sampling_policy(purpose):
    with pytest.raises(ValueError, match="bounded resample"):
        intervention(evidence(setup_decision()), purpose=purpose,
                     changed_variables=("seed",), held_constants=("prompt_text",))


def test_compiler_checks_declared_target_values_against_actual_reference_bytes():
    before = setup_decision(reference_hash="a" * 64)
    baseline = compile_decision(decide(before), before).request
    failed = evidence(before, verdict="FAIL", task_id="task", request_hash=baseline.request_input_hash)
    after = setup_decision(reference_hash="b" * 64)
    proposed = intervention(failed, semantic_variable_hashes=(("image_bindings", "d" * 64),))
    decision = decide(after, historical_recipes=before["inputs"].candidates,
        baseline_request=baseline, evidence=(failed,), latest_attempt_hash=failed.evidence_hash,
        interventions=(proposed,))
    result = compile_decision(decision, after)
    assert result.outcome == "unsupported"
    assert result.unsupported_field_paths == ("generation_recipe.comparison.target_values",)


def test_policy_resample_cap_counts_submitted_cross_task_semantic_experiment_only():
    setup = setup_decision()
    baseline = compile_decision(decide(setup), setup).request
    latest = evidence(setup, verdict="FAIL", task_id="task", attempt="current",
                      request_hash=baseline.request_input_hash)
    proposal = intervention(latest, purpose="resample", resample_limit=99,
                            changed_variables=("seed",), held_constants=("prompt_text", "image_bindings"))
    original = setup["inputs"].candidates[0]
    changed = original.model_copy(update={"recipe": original.recipe.model_copy(
        update={"seed": SeedPolicy(kind="fixed", value=43)})})
    setup = {**setup, "inputs": setup["inputs"].model_copy(
        update={"candidates": (changed,), "historical_recipes": (original,)})}
    prior = evidence(setup, verdict="FAIL", task_id="previous-task", attempt="submitted")
    prior = prior.model_copy(update={"intervention_id": "historical-name",
                                     "intervention_semantic_hash": proposal.semantic_hash})
    blocked = decide(setup, evidence=(prior, latest), latest_attempt_hash=latest.evidence_hash,
                     interventions=(proposal,), baseline_request=baseline,
                     policy=DecisionPolicy(max_resamples=1))
    assert blocked.disposition == "REASSESS_FEASIBILITY"
    not_submitted = prior.model_copy(update={"outcome": "not_submitted", "artifact_sha256": None,
                                             "findings": (), "attempt_id": "prepared-only"})
    allowed = decide(setup, evidence=(not_submitted, latest), latest_attempt_hash=latest.evidence_hash,
                     interventions=(proposal,), baseline_request=baseline,
                     policy=DecisionPolicy(max_resamples=1))
    assert allowed.disposition == "GENERATE_ONCE"
    unknown = prior.model_copy(update={"outcome": "unknown_outcome", "artifact_sha256": None,
                                       "findings": (), "attempt_id": "unknown"})
    fail_closed = decide(setup, evidence=(unknown, latest), latest_attempt_hash=latest.evidence_hash,
                         interventions=(proposal,), baseline_request=baseline,
                         policy=DecisionPolicy(max_resamples=1))
    assert fail_closed.disposition == "UNKNOWN_OUTCOME"


def test_prediction_outcome_is_observational_and_protects_declared_requirements():
    from ai_video.production.generation_diagnosis import Diagnosis

    setup = setup_decision()
    proposed = intervention(evidence(setup), protected_requirements=("continuity",))
    supported = Diagnosis(failure_classes=(), failed_requirements=(),
                          preserved_requirements=("duration", "continuity"),
                          evidence_hashes=("a" * 64,), next_owner="review_owner")
    refuted = supported.model_copy(update={"failed_requirements": ("continuity",),
                                           "preserved_requirements": ("duration",)})
    incomplete = supported.model_copy(update={"preserved_requirements": ("duration",)})
    assert intervention_prediction_outcome(proposed, supported) == "supported"
    assert intervention_prediction_outcome(proposed, refuted) == "refuted"
    assert intervention_prediction_outcome(proposed, incomplete) == "undetermined"


def test_undetermined_prior_repair_prediction_requires_evidence_before_reeligibility():
    setup = setup_decision()
    baseline = compile_decision(decide(setup), setup).request
    latest = evidence(setup, verdict="FAIL", task_id="task", attempt="current",
                      request_hash=baseline.request_input_hash)
    proposal = intervention(latest)
    prior = evidence(setup, verdict="NOT_EVALUATED", task_id="previous-task", attempt="prior")
    prior = prior.model_copy(update={"intervention_id": "old-name",
                                     "intervention_semantic_hash": proposal.semantic_hash})
    result = decide(setup, evidence=(prior, latest), latest_attempt_hash=latest.evidence_hash,
                    interventions=(proposal,), baseline_request=baseline)
    assert result.disposition == "EVIDENCE_GAP"


def test_comparison_discloses_uncontrolled_historical_baseline():
    from ai_video.production.generation_diagnosis import seal_intervention_comparison, compiled_comparison_errors
    from ai_video.production.video import VideoGenerationRequest
    setup = setup_decision()
    controlled = compile_decision(decide(setup), setup).request
    values = controlled.model_dump(mode="python", exclude={"request_input_hash"})
    for seed in (None, -1):
        baseline = VideoGenerationRequest.create(**{**values, "seed": seed})
        e = evidence(setup, verdict="FAIL")
        proposed = intervention(e, purpose="resample", resample_limit=1,
                               changed_variables=("seed",), held_constants=("prompt_text",))
        comparison = seal_intervention_comparison(proposed, baseline)
        assert compiled_comparison_errors(comparison, controlled) == ("generation_recipe.comparison.uncontrolled_seed",)


@pytest.mark.parametrize("changes,path", [
    ({"camera_endpoint": {"position_lock": True, "orientation_lock": True}}, "generation_intent.camera_endpoint.position_lock"),
    ({"pacing": {"shot_duration_seconds": 3}}, "generation_intent.pacing.shot_duration_seconds"),
    ({"identity_continuity": {"preservation": "bounded_variation"}}, "generation_intent.identity_continuity.preservation"),
])
def test_canonical_nontext_controls_cannot_be_silently_dropped(changes, path):
    from test_production_provider_neutral_adapters import _replace_requirement
    from ai_video.production.video_requirement import GenerationIntent
    setup = setup_decision()
    intent = GenerationIntent.model_validate({**setup["projection"].requirement.generation_intent.model_dump(mode="python"), **changes})
    projection = _replace_requirement(setup["projection"], generation_intent=intent)
    c = setup["inputs"].candidates[0]
    c = c.model_copy(update={"recipe": c.recipe.model_copy(update={"requirement_hash": projection.requirement.requirement_hash})})
    setup["projection"] = projection
    setup["inputs"] = setup["inputs"].model_copy(update={"candidates": (c,),
        "projection_hash": projection.projection_hash, "facts_hash": VideoPlanner.generation_difficulty(projection)["facts_hash"]})
    compiled = compile_decision(decide(setup), setup)
    assert compiled.outcome == "unsupported"
    assert path in compiled.unsupported_field_paths


def test_missing_historical_intervention_semantics_requires_evidence_repair():
    setup = setup_decision()
    e = evidence(setup, verdict="FAIL", task_id="task", intervention_id="previous-resample")
    proposed = intervention(e, intervention_id="new-resample", purpose="resample", resample_limit=1)
    result = decide(setup, evidence=(e,), latest_attempt_hash=e.evidence_hash, interventions=(proposed,))
    assert result.disposition == "EVIDENCE_GAP"


def test_current_complete_result_returns_to_acceptance_owner_without_regeneration():
    setup = setup_decision()
    e = evidence(setup, task_id="task")
    result = decide(setup, evidence=(e,), latest_attempt_hash=e.evidence_hash)
    assert result.disposition == "REVIEW_CURRENT_RESULT"
    assert result.routing is None


def test_current_result_preserves_separate_human_rejection_of_same_bytes():
    setup = setup_decision()
    rejected = evidence(setup, task_id="task", verdict="FAIL", proof="human")
    measured = evidence(setup, task_id="task")
    result = decide(setup, evidence=(rejected, measured), latest_attempt_hash=measured.evidence_hash)
    assert result.disposition != "REVIEW_CURRENT_RESULT"
    assert "QUALITY_FAILURE" in result.diagnosis.failure_classes
    assert not result.diagnosis.all_required_observed_pass
    assert set(result.diagnosis.evidence_hashes) == {rejected.evidence_hash, measured.evidence_hash}


def test_current_result_is_not_rejected_by_human_failure_on_other_bytes():
    setup = setup_decision()
    rejected = evidence(setup, task_id="task", verdict="FAIL", proof="human", attempt="old")
    measured = evidence(setup, task_id="task")
    result = decide(setup, evidence=(rejected, measured), latest_attempt_hash=measured.evidence_hash)
    assert result.disposition == "REVIEW_CURRENT_RESULT"
    assert result.diagnosis.evidence_hashes == (measured.evidence_hash,)


def test_current_result_can_complete_previously_missing_evidence_on_same_bytes():
    setup = setup_decision()
    missing = evidence(setup, task_id="task", verdict="NOT_EVALUATED")
    measured = evidence(setup, task_id="task")
    result = decide(setup, evidence=(missing, measured), latest_attempt_hash=measured.evidence_hash)
    assert result.disposition == "REVIEW_CURRENT_RESULT"
    assert result.diagnosis.all_required_observed_pass
    assert set(result.diagnosis.evidence_hashes) == {missing.evidence_hash, measured.evidence_hash}
    assert result.assessments[0].pass_count == 1


@pytest.mark.parametrize("update", [{"generation_forbidden": True}, {"local_batch_used": 3}, {"local_resource_available": False}])
def test_supported_fit_does_not_turn_resource_stop_into_provider_switch(update):
    setup = setup_decision()
    e = evidence(setup, shot_id="historical-shot")
    result = decide(setup, evidence=(e,), limits=setup["inputs"].limits.model_copy(update=update))
    assert result.disposition == "BLOCKED_EXECUTION"
    assert result.routing is None


def test_new_task_cannot_omit_latest_same_shot_submitted_history():
    setup = setup_decision()
    prior = evidence(setup, verdict="FAIL", task_id="previous-task")
    result = decide(setup, evidence=(prior,), policy=DecisionPolicy(max_resamples=0))
    assert result.disposition == "EVIDENCE_GAP"
    assert result.routing is None
