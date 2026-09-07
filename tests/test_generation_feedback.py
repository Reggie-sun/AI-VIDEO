"""Offline integration of real Router/compiler with the reusable input producer."""

import hashlib

import pytest

from ai_video.production.generation_decision import DecisionPolicy
from ai_video.production.generation_experience import GenerationExperience, empirical_assessment, extract_generation_features
from ai_video.production.generation_feedback import (
    GenerationFeedbackOrchestrator, GenerationHistory, RegisteredGenerationTarget,
    project_attempt_evidence,
)
from ai_video.production.video_compiler import ProviderNativePrompt, compile_provider_video_request
from ai_video.production.video_fake import ScriptedFakeVideoProvider
from ai_video.production.generation_diagnosis import Finding
from test_production_generation_decision import setup_decision, evidence, decide


class NativeFixtureProvider(ScriptedFakeVideoProvider):
    def compile_request(self, provider_bound, requirement):
        text = "Generate 4 seconds."
        return compile_provider_video_request(
            provider_bound=provider_bound, requirement=requirement,
            compiler_id="test-native", compiler_version="2", capabilities=self._capabilities,
            native_prompt=ProviderNativePrompt(grammar_contract="test-native/2", prompt_text=text,
                prompt_sha256=hashlib.sha256(text.encode()).hexdigest()))


def feedback_setup():
    setup = setup_decision()
    candidate = setup["inputs"].candidates[0]
    provider = NativeFixtureProvider(capabilities=candidate.capabilities, artifact_bytes=b"unused-offline")
    current = {key: value for key, value in setup.items() if key != "inputs"}
    current["acceptance"] = candidate.recipe.acceptance_policy
    history = [GenerationHistory()]
    orchestrator = GenerationFeedbackOrchestrator(
        targets=(RegisteredGenerationTarget(provider, candidate.provider_profile,
                  candidate.compiler_contract, candidate.output_requirement),),
        context_loader=lambda: current, history_loader=lambda: history[0],
        policy=DecisionPolicy(allow_bounded_exploration=True))
    return setup, provider, current, history, orchestrator


def test_common_caller_produces_failure_intervention_without_handwritten_proposal():
    setup, provider, current, history, orchestrator = feedback_setup()
    first = orchestrator.prepare(limits=setup["inputs"].limits)
    assert first.decision.disposition == "GENERATE_ONCE"
    assert first.resolved_request is not None
    finding = Finding(requirement_id="duration", rubric_hash=first.inputs.rubric_hash,
        stage="raw_generation", proof="technical", verdict="FAIL", source_sha256="c" * 64,
        observation="Only two usable seconds.")
    failed = project_attempt_evidence(prepared=first, task_id="task", shot_id=current["context"].target_shot_id,
        attempt_id="first", outcome="media", artifact_sha256="d" * 64, findings=(finding,))
    experience = GenerationExperience(projection=current["projection"], candidate=first.inputs.candidates[0],
                                     evidence=(failed,))
    history[0] = GenerationHistory((experience,), failed.evidence_hash, first.compilation.request)
    current["lifecycle"] = current["lifecycle"].model_copy(update={"generation_id": "repair"})
    repair = orchestrator.prepare(limits=setup["inputs"].limits)
    assert repair.decision.disposition == "GENERATE_ONCE"
    assert repair.decision.intervention.purpose == "resample"
    assert repair.compilation.request.seed == first.compilation.request.seed + 1
    assert repair.compilation.request.prompt_text == first.compilation.request.prompt_text
    second_failed = project_attempt_evidence(prepared=repair, task_id="task",
        shot_id=current["context"].target_shot_id, attempt_id="repair", outcome="media",
        artifact_sha256="e" * 64, findings=(finding,))
    history[0] = GenerationHistory((experience, GenerationExperience(projection=current["projection"],
        candidate=repair.inputs.candidates[0], evidence=(second_failed,))),
        second_failed.evidence_hash, repair.compilation.request)
    stopped = orchestrator.prepare(limits=setup["inputs"].limits)
    assert stopped.decision.disposition == "REASSESS_FEASIBILITY"
    assert stopped.compilation is None
    assert provider.call_counts.submit == provider.call_counts.fetch == 0


def test_cohort_survives_profile_renewal_without_exact_hash_pass():
    setup = setup_decision()
    candidate = setup["inputs"].candidates[0]
    historical = GenerationExperience(projection=setup["projection"], candidate=candidate,
                                     evidence=(evidence(setup),))
    from test_production_shot_router import _profile
    renewed_profile = _profile(profile_sha256="e" * 64)
    renewed = candidate.model_copy(update={"provider_profile": renewed_profile,
        "recipe": candidate.recipe.model_copy(update={"profile_sha256": "e" * 64})})
    assert renewed.scope_hash != candidate.scope_hash
    features = extract_generation_features(setup["projection"])
    result = decide(setup, candidates=(renewed,), evidence=historical.evidence,
                    experiences=(historical,), feature_scope=features)
    assessment = result.assessments[0]
    assert assessment.pass_count == 0  # exact attempt memory has no match
    assert assessment.empirical.observed_success_fraction == 1
    assert assessment.empirical.interval_95[0] < 0.3  # one sample is weak evidence
    assert assessment.fit == "supported"


def test_wrong_provider_and_changed_rubric_are_excluded_from_empirical_fit():
    setup = setup_decision()
    candidate = setup["inputs"].candidates[0]
    history = GenerationExperience(projection=setup["projection"], candidate=candidate,
                                  evidence=(evidence(setup),))
    from ai_video.production.video import VideoProviderCapabilities
    other = candidate.model_copy(update={"capabilities": VideoProviderCapabilities.create(
        provider_name="other", variants=candidate.capabilities.variants)})
    fit = empirical_assessment(other, history.features, (history,))
    assert fit.observed_success_fraction is None
    assert fit.exclusions[0][1] == "provider_or_model"
    other = candidate.model_copy(update={"recipe": candidate.recipe.model_copy(update={"rubric_hash": "e" * 64})})
    assert empirical_assessment(other, history.features, (history,)).exclusions[0][1] == "unmapped_acceptance_rubric"


def test_history_source_mismatch_and_stale_features_are_rejected():
    setup = setup_decision()
    with pytest.raises(ValueError, match="exact source"):
        GenerationExperience(projection=setup["projection"], candidate=setup["inputs"].candidates[0],
            evidence=(evidence(setup, facts_hash="f" * 64),))
    features = extract_generation_features(setup["projection"]).model_copy(update={"character_count": 99})
    with pytest.raises(ValueError, match="feature projection"):
        decide(setup, feature_scope=features)


def test_empirical_cohort_does_not_transfer_across_render_geometry_or_execution_strategy():
    setup = setup_decision()
    candidate = setup["inputs"].candidates[0]
    history = GenerationExperience(projection=setup["projection"], candidate=candidate,
                                  evidence=(evidence(setup),))
    higher_resolution = history.features.model_copy(update={"output_geometry": (3840, 2160, 60)})
    fit = empirical_assessment(candidate, higher_resolution, (history,))
    assert fit.observed_success_fraction is None
    assert fit.exclusions[0][1] == "feature_cohort"
    from ai_video.production.video import VideoProviderCapabilities
    variants = tuple(v.model_copy(update={"profile_version": "different-execution-strategy"})
                     for v in candidate.capabilities.variants)
    other = candidate.model_copy(update={"capabilities": VideoProviderCapabilities.create(
        provider_name=candidate.capabilities.provider_name, variants=variants)})
    fit = empirical_assessment(other, history.features, (history,))
    assert fit.observed_success_fraction is None
    assert fit.exclusions[0][1] == "generation_strategy"


def test_incomplete_results_never_produce_a_success_fraction():
    setup = setup_decision()
    history = GenerationExperience(projection=setup["projection"], candidate=setup["inputs"].candidates[0],
                                  evidence=(evidence(setup, verdict="NOT_EVALUATED"),))
    fit = empirical_assessment(history.candidate, history.features, (history,))
    assert fit.observed_success_fraction is None
    assert len(fit.incomplete_artifacts) == 1


def test_similar_new_shot_keeps_empirical_evidence_without_exact_identity():
    setup = setup_decision()
    candidate = setup["inputs"].candidates[0]
    history = GenerationExperience(projection=setup["projection"], candidate=candidate,
                                  evidence=(evidence(setup),))
    from test_production_shot_router import _context, _verified_requirement, _lifecycle
    context = _context(important=False, shot_id="new-shot", shot_intent="Another authored action.")
    projection = _verified_requirement(context)
    new_candidate = candidate.model_copy(update={"recipe": candidate.recipe.model_copy(
        update={"requirement_hash": projection.requirement.requirement_hash})})
    from ai_video.production.hashing import canonical_sha256
    new_setup = {**setup, "context": context, "projection": projection, "lifecycle": _lifecycle(context)}
    result = decide(new_setup, candidates=(new_candidate,), projection_hash=projection.projection_hash,
        facts_hash=canonical_sha256(projection.requirement.model_dump(mode="json", exclude={"requirement_id", "requirement_hash"})),
        experiences=(history,), evidence=history.evidence, feature_scope=extract_generation_features(projection))
    assert result.disposition == "GENERATE_ONCE"
    assert result.assessments[0].pass_count == 0
    assert result.assessments[0].empirical.supported_artifacts
    assert "hand_prop_interaction" in extract_generation_features(projection).unknown_features


def test_router_prefers_observed_fit_across_technically_compatible_providers():
    setup = setup_decision()
    original = setup["inputs"].candidates[0]
    from ai_video.production.video import VideoProviderCapabilities
    alternative = original.model_copy(update={"candidate_id": "alternative", "capabilities":
        VideoProviderCapabilities.create(provider_name="alternative", variants=original.capabilities.variants)})
    poor = GenerationExperience(projection=setup["projection"], candidate=original,
        evidence=tuple(evidence(setup, verdict="FAIL", attempt=f"bad-{i}") for i in range(4)))
    better = GenerationExperience(projection=setup["projection"], candidate=alternative,
        evidence=tuple(evidence(setup, candidate=alternative, attempt=f"good-{i}") for i in range(4)))
    setup, (original, alternative) = _next_shot(setup, (original, alternative))
    result = decide(setup, candidates=(original, alternative), experiences=(poor, better),
        evidence=(*poor.evidence, *better.evidence), feature_scope=poor.features)
    assert result.selected_candidate_id == "alternative"
    assert all(item.compatible for item in result.assessments)
    assert {item.candidate_id: item.fit for item in result.assessments} == {
        "alternative": "supported", "one": "unsupported"}


def test_mixed_cohort_remains_eligible_and_outweighs_one_lucky_result():
    setup = setup_decision()
    original = setup["inputs"].candidates[0]
    from ai_video.production.video import VideoProviderCapabilities
    alternative = original.model_copy(update={"candidate_id": "alternative", "capabilities":
        VideoProviderCapabilities.create(provider_name="alternative", variants=original.capabilities.variants)})
    established = GenerationExperience(projection=setup["projection"], candidate=original,
        evidence=tuple(evidence(setup, verdict="PASS" if i < 9 else "FAIL", attempt=f"mixed-{i}")
                       for i in range(10)))
    lucky = GenerationExperience(projection=setup["projection"], candidate=alternative,
        evidence=(evidence(setup, candidate=alternative, attempt="lucky"),))
    setup, (original, alternative) = _next_shot(setup, (original, alternative))
    result = decide(setup, candidates=(original, alternative), experiences=(established, lucky),
        evidence=(*established.evidence, *lucky.evidence), feature_scope=established.features)
    assert result.selected_candidate_id == original.candidate_id
    assert all(item.fit == "supported" for item in result.assessments)


def _next_shot(setup, candidates):
    from test_production_shot_router import _context, _verified_requirement, _lifecycle
    from ai_video.planning.video_planner import VideoPlanner

    context = _context(important=False, shot_id="new-ranking-shot", shot_intent="Another authored action.")
    projection = _verified_requirement(context)
    candidates = tuple(c.model_copy(update={"recipe": c.recipe.model_copy(update={
        "requirement_hash": projection.requirement.requirement_hash})}) for c in candidates)
    inputs = setup["inputs"].model_copy(update={"projection_hash": projection.projection_hash,
        "facts_hash": VideoPlanner.generation_difficulty(projection)["facts_hash"]})
    return {**setup, "context": context, "projection": projection,
            "lifecycle": _lifecycle(context), "inputs": inputs}, candidates


def test_separate_proof_repair_receipt_reuses_the_same_artifact():
    setup = setup_decision()
    candidate = setup["inputs"].candidates[0]
    missing = evidence(setup, verdict="NOT_EVALUATED")
    complete = evidence(setup)
    experiences = tuple(GenerationExperience(projection=setup["projection"], candidate=candidate,
        evidence=(entry,)) for entry in (missing, complete))
    result = empirical_assessment(candidate, experiences[0].features, experiences)
    assert result.observed_success_fraction == 1
    assert result.supported_artifacts == (complete.artifact_sha256,)
    assert not result.incomplete_artifacts


def test_new_task_continues_prior_shot_failure_without_resetting_history():
    setup, _, current, history, orchestrator = feedback_setup()
    first = orchestrator.prepare(limits=setup["inputs"].limits)
    failed = project_attempt_evidence(prepared=first, task_id="task",
        shot_id=current["context"].target_shot_id, attempt_id="first", outcome="media",
        artifact_sha256="d" * 64, findings=(Finding(requirement_id="duration",
            rubric_hash=first.inputs.rubric_hash, stage="raw_generation", proof="technical",
            verdict="FAIL", source_sha256="c" * 64, observation="Too short"),))
    history[0] = GenerationHistory((GenerationExperience(projection=current["projection"],
        candidate=first.inputs.candidates[0], evidence=(failed,)),), failed.evidence_hash,
        first.compilation.request)
    continued = orchestrator.prepare(limits=setup["inputs"].limits.model_copy(update={"task_id": "new-task"}))
    assert continued.decision.disposition == "GENERATE_ONCE"
    assert continued.decision.intervention.purpose == "resample"
    assert continued.inputs.evidence == (failed,)


def test_pass_breaks_failure_streak_instead_of_accumulating_lifetime_failures():
    setup, _, current, history, orchestrator = feedback_setup()
    first = orchestrator.prepare(limits=setup["inputs"].limits)
    records = []
    for number, verdict in enumerate(("FAIL", "FAIL", "FAIL", "PASS", "FAIL")):
        entry = project_attempt_evidence(prepared=first, task_id="task",
            shot_id=current["context"].target_shot_id, attempt_id=str(number), outcome="media",
            artifact_sha256=hashlib.sha256(str(number).encode()).hexdigest(),
            findings=(Finding(requirement_id="duration", rubric_hash=first.inputs.rubric_hash,
                stage="raw_generation", proof="technical", verdict=verdict,
                source_sha256="c" * 64, observation="Injected measured duration"),))
        records.append(GenerationExperience(projection=current["projection"],
            candidate=first.inputs.candidates[0], evidence=(entry,)))
    history[0] = GenerationHistory(tuple(records), entry.evidence_hash, first.compilation.request)
    from ai_video.production.generation_feedback import derive_generation_interventions
    proposals, _ = derive_generation_interventions(projection=current["projection"],
        candidates=first.inputs.candidates, history=history[0], policy=orchestrator.policy)
    assert len(proposals) == 1
    assert proposals[0].purpose == "resample"
