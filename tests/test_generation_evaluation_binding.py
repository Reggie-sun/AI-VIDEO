"""Offline controlled evidence fixtures; no human viewing or media-quality claim."""

import pytest
import json


def time_window(**updates):
    from ai_video.production.requirement_semantics import EventTimeWindow

    return EventTimeWindow(**dict(kind="event_time_window", event_id="signal-end",
        event_definition="Last spoken word of the rescue signal ends", boundary="end",
        timebase="source_media_millis", source_role="fetched_raw", selection_rule="submitted_output",
        lower_millis=100, upper_millis=2700, lower_inclusive=True, upper_inclusive=True,
        allowed_methods=["word_alignment"], required_coverage=(0, 4000),
        uncertainty="bounded_interval") | updates)


@pytest.mark.parametrize("interval,verdict", [((2400, 2450), "PASS"), ((2680, 2720), "NOT_EVALUATED"),
                                            ((2800, 2850), "FAIL"), ((2700, 2700), "PASS")])
def test_time_predicate_uses_canonical_window_not_recipe_margin(interval, verdict):
    from ai_video.production.generation_evaluation_criteria import TemporalMeasurement, temporal_verdict

    result = TemporalMeasurement(artifact_sha256="a" * 64, size_bytes=32,
        evaluation_item_hash="b" * 64, event_id="signal-end", boundary="end",
        timebase="source_media_millis", interval_millis=interval, method="word_alignment",
        coverage_millis=(0, 4000), evidence_refs=("c" * 64,))
    assert temporal_verdict(time_window(), result) == verdict


def test_segment_end_cannot_prove_word_end_and_exclusive_boundary_is_strict():
    from ai_video.production.generation_evaluation_criteria import TemporalMeasurement, temporal_verdict

    result = TemporalMeasurement(artifact_sha256="a" * 64, size_bytes=32,
        evaluation_item_hash="b" * 64, event_id="signal-end", boundary="end",
        timebase="source_media_millis", interval_millis=(2440, 2440), method="asr_segment",
        coverage_millis=(0, 4000), evidence_refs=("c" * 64,))
    assert temporal_verdict(time_window(), result) == "NOT_EVALUATED"
    result = result.model_copy(update={"method": "word_alignment", "interval_millis": (2700, 2700)})
    assert temporal_verdict(time_window(upper_inclusive=False), result) == "FAIL"


def marked_context():
    from ai_video.production.models import QaPolicy, GenerationEvaluationAuthority
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.generation_recipe import RequirementExpression, GenerationRecipe
    from test_production_ecommerce_product_interaction_e2e import _commercial_policy
    from test_requirement_semantics import semantic_rule, marked_policy
    from test_production_generation_decision import setup_decision

    setup = setup_decision()
    rules = [semantic_rule("signal"), semantic_rule("early", "directional_preference", "recipe_hint")]
    policy = marked_policy(sorted(rules, key=lambda r: r["requirement_id"]))
    qa = _commercial_policy()
    qa = seal_artifact(QaPolicy.model_validate({**qa.model_dump(mode="json"), "generation_acceptance": policy,
        "generation_evaluation_authorities": [GenerationEvaluationAuthority(evaluator=qa.semantic_authorities[0], proof="analyzer")]}))
    candidate = setup["inputs"].candidates[0]
    recipe = GenerationRecipe.model_validate({**candidate.recipe.model_dump(mode="python"),
        "acceptance_policy": policy, "rubric_hash": policy.profile_content_hash,
        "expressions": [RequirementExpression.model_validate(r) for r in policy.profile_payload["generation_requirements"]]})
    return setup, candidate.model_copy(update={"recipe": recipe}), qa


def simulated_source(candidate, qa, *, verdict="PASS", unresolved=False, advisory=False):
    """Explicit synthetic transcript for pure validation; never a live recording proof."""
    from ai_video.production.generation_evaluation import GenerationEvaluationSource, GenerationObservation
    from ai_video.production.generation_evaluation_criteria import evaluation_items, PresentationEvidence

    items = evaluation_items(acceptance=candidate.recipe.acceptance_policy, qa_policy_content_hash=qa.content_hash,
        request_hash="b" * 64, artifact_sha256="c" * 64, size_bytes=32)
    source = GenerationEvaluationSource(schema_version="generation-evaluation/2", request_hash="b" * 64,
        artifact_sha256="c" * 64, size_bytes=32, rubric_hash=candidate.recipe.rubric_hash,
        qa_policy_content_hash=qa.content_hash, qa_policy_snapshot=qa,
        evaluator=qa.semantic_authorities[0], proof="analyzer",
        observations=(GenerationObservation(requirement_id="signal", verdict=verdict, observation="Simulated signal result",
            evaluation_item_hash=items[0].evaluation_item_hash, question_text=items[0].question_text,
            presentation_ref="fixture/request", answer_ref="fixture/response"),),
        advisory_observations=([dict(requirement_id="early", observation="Later than preferred", evidence_refs=["fixture/frame"])] if advisory else []),
        unresolved_quality_observations=([dict(observation_id="visible-defect", original_answer="Unmodeled visible discontinuity",
            visible_problem="The background jumps", quality_basis="Continuity floor not covered by this rubric",
            evidence_refs=["fixture/frame"], answer_ref="fixture/response")] if unresolved else []))
    return source.model_copy(update={"presentation_evidence": PresentationEvidence(namespace="controlled-evaluator/1",
        interaction_ref="fixture", presentation_ref="fixture/request", answer_ref="fixture/response",
        event_order=("presentation", "answer"), actor_name=source.evaluator.name, actor_version=source.evaluator.version,
        items=items, answers_json=json.dumps(source.answer_payload()))})


def experience_for(source, setup, candidate):
    from ai_video.production.generation_evaluation import project_generation_evaluation_sources
    from ai_video.production.generation_experience import GenerationExperience
    from test_production_generation_decision import evidence

    findings, refs = project_generation_evaluation_sources(sources=(source,), acceptance=candidate.recipe.acceptance_policy)
    entry = evidence(setup, candidate=candidate, findings=findings, unresolved_quality_refs=refs,
                     artifact_sha256=source.artifact_sha256)
    return GenerationExperience(projection=setup["projection"], candidate=candidate,
                                evidence=(entry,), evaluation_sources=(source,))


@pytest.mark.parametrize("mutation", ["question", "item", "actor", "artifact", "hint", "final", "answer", "threshold"])
def test_correct_hash_does_not_admit_wrong_question_object_or_actor(mutation):
    from ai_video.production.generation_evaluation import project_generation_evaluation_sources
    setup, candidate, qa = marked_context()
    source = simulated_source(candidate, qa)
    obs = source.observations[0]
    if mutation == "question":
        source = source.model_copy(update={"observations": (obs.model_copy(update={"question_text": "Is the hand natural?"}),)})
    elif mutation == "item":
        source = source.model_copy(update={"observations": (obs.model_copy(update={"evaluation_item_hash": "d" * 64}),)})
    elif mutation == "actor":
        source = source.model_copy(update={"evaluator": source.evaluator.model_copy(update={"name": "other"})})
    elif mutation == "artifact":
        source = source.model_copy(update={"artifact_sha256": "d" * 64})
    elif mutation == "hint":
        source = source.model_copy(update={"observations": (obs.model_copy(update={"requirement_id": "early"}),)})
    elif mutation == "final":
        source = source.model_copy(update={"observations": (obs.model_copy(update={"requirement_id": "final-caption"}),)})
    elif mutation == "answer":
        source = source.model_copy(update={"observations": (obs.model_copy(update={"answer_ref": "other/response"}),)})
    else:
        source = source.model_copy(update={"observations": (obs.model_copy(update={"question_text": "Must finish before 2.2s"}),)})
    with pytest.raises(ValueError):
        project_generation_evaluation_sources(sources=(source,), acceptance=candidate.recipe.acceptance_policy)


@pytest.mark.parametrize("hard_verdict", ["PASS", "FAIL"])
def test_unresolved_refs_survive_reopen_merge_and_failure_first_statistics(hard_verdict):
    from ai_video.production.generation_experience import GenerationExperience, empirical_assessment
    from ai_video.production.generation_diagnosis import diagnose_exact_result

    setup, candidate, qa = marked_context()
    source = simulated_source(candidate, qa, verdict=hard_verdict, unresolved=True, advisory=True)
    experience = experience_for(source, setup, candidate)
    reopened = GenerationExperience.model_validate_json(experience.model_dump_json())
    assert reopened == experience
    assert len(reopened.evidence[0].unresolved_quality_refs) == 1
    later = experience_for(simulated_source(candidate, qa), setup, candidate)
    diagnosis = diagnose_exact_result(later.evidence[0], reopened.evidence, candidate.recipe,
        evaluation_sources=(*later.evaluation_sources, *reopened.evaluation_sources))
    assert "RUBRIC_OR_STAGE_ERROR" in diagnosis.failure_classes
    assert diagnosis.next_owner == "acceptance_owner"
    assert not diagnosis.all_required_observed_pass
    estimate = empirical_assessment(candidate, reopened.features, (reopened, later))
    assert not estimate.supported_artifacts
    if hard_verdict == "FAIL":
        assert "QUALITY_FAILURE" in diagnosis.failure_classes
        assert diagnosis.failed_requirements == ("signal",)
        assert estimate.failed_artifacts == (source.artifact_sha256,)
        assert not estimate.incomplete_artifacts
        assert estimate.observed_success_fraction == 0
    else:
        assert "QUALITY_FAILURE" not in diagnosis.failure_classes
        assert not diagnosis.failed_requirements
        assert estimate.incomplete_artifacts == (source.artifact_sha256,)
        assert estimate.observed_success_fraction is None
    malformed = experience.model_dump(mode="json")
    malformed["evidence"][0].pop("unresolved_quality_refs")
    with pytest.raises(ValueError, match="differ from original"):
        GenerationExperience.model_validate(malformed)


def test_advisory_cannot_fail_and_pure_diagnosis_defends_hint_injection():
    from ai_video.production.generation_diagnosis import diagnose_attempt
    from ai_video.production.generation_experience import empirical_assessment

    setup, candidate, qa = marked_context()
    exp = experience_for(simulated_source(candidate, qa, advisory=True), setup, candidate)
    assert len(exp.evidence[0].findings) == 1
    assert empirical_assessment(candidate, exp.features, (exp,)).observed_success_fraction == 1
    injected = exp.evidence[0].findings[0].model_copy(update={"requirement_id": "early", "proof": "human", "verdict": "FAIL"})
    result = diagnose_attempt(exp.evidence[0].model_copy(update={"findings": (*exp.evidence[0].findings, injected)}),
        candidate.recipe, evaluation_sources=exp.evaluation_sources)
    assert result.failure_classes == ("RUBRIC_OR_STAGE_ERROR",)
    assert result.failed_requirements == ()


def test_marked_qa_rejects_legacy_source_and_unsealed_snapshot():
    from ai_video.production.generation_evaluation import GenerationEvaluationSource, project_generation_evaluation_sources

    _, candidate, qa = marked_context()
    source = simulated_source(candidate, qa)
    old = GenerationEvaluationSource(request_hash=source.request_hash, artifact_sha256=source.artifact_sha256,
        rubric_hash=source.rubric_hash, qa_policy_content_hash=qa.content_hash, evaluator=source.evaluator,
        proof=source.proof, observations=[dict(requirement_id="signal", verdict="PASS", observation="Historical answer")])
    with pytest.raises(ValueError, match="matching evaluation version"):
        project_generation_evaluation_sources(sources=(old,), acceptance=candidate.recipe.acceptance_policy)
    payload = source.model_dump(mode="json")
    payload["qa_policy_snapshot"]["policy_version"] = "forged-same-hash"
    with pytest.raises(ValueError, match="sealed QA snapshot"):
        GenerationEvaluationSource.model_validate(payload)


def test_advisory_only_source_is_incomplete_without_creating_a_failure_sample():
    from ai_video.production.generation_experience import empirical_assessment
    from ai_video.production.generation_diagnosis import diagnose_attempt

    setup, candidate, qa = marked_context()
    source = simulated_source(candidate, qa, advisory=True).model_copy(update={"observations": ()})
    source = source.model_copy(update={"presentation_evidence": source.presentation_evidence.model_copy(
        update={"answers_json": json.dumps(source.answer_payload())})})
    experience = experience_for(source, setup, candidate)
    diagnosis = diagnose_attempt(experience.evidence[0], candidate.recipe)
    assert diagnosis.failure_classes == ("EVIDENCE_GAP",)
    assert not diagnosis.failed_requirements and not diagnosis.all_required_observed_pass
    estimate = empirical_assessment(candidate, experience.features, (experience,))
    assert estimate.observed_success_fraction is None
    assert not estimate.failed_artifacts and not estimate.supported_artifacts
    assert estimate.incomplete_artifacts == (source.artifact_sha256,)


def test_separate_legal_advisory_source_does_not_block_complete_bound_proof():
    from ai_video.production.generation_experience import empirical_assessment
    from ai_video.production.generation_diagnosis import diagnose_exact_result

    setup, candidate, qa = marked_context()
    passed = experience_for(simulated_source(candidate,qa),setup,candidate)
    source = simulated_source(candidate,qa,advisory=True).model_copy(update={"observations":()})
    source = source.model_copy(update={"presentation_evidence":source.presentation_evidence.model_copy(
        update={"answers_json":json.dumps(source.answer_payload())})})
    advisory = experience_for(source,setup,candidate)
    result = diagnose_exact_result(advisory.evidence[0],passed.evidence,candidate.recipe,
        evaluation_sources=(*passed.evaluation_sources,*advisory.evaluation_sources))
    assert result.all_required_observed_pass and not result.failure_classes
    estimate = empirical_assessment(candidate,passed.features,(passed,advisory))
    assert estimate.supported_artifacts == (source.artifact_sha256,)
    assert not estimate.failed_artifacts and not estimate.incomplete_artifacts


@pytest.mark.parametrize("mutation", ["proof", "question", "criterion", "artifact", "source", "missing"])
def test_pure_exact_diagnosis_and_router_reject_unbound_marked_proof(mutation):
    from ai_video.production.generation_decision import DecisionInputs
    from ai_video.production.generation_diagnosis import diagnose_exact_result
    from ai_video.production.shot_router import VideoGenerationResolver

    setup, candidate, qa = marked_context()
    source = simulated_source(candidate, qa)
    exp = experience_for(source, setup, candidate)
    entry = exp.evidence[0]
    sources = (source,)
    if mutation == "proof":
        wrong = entry.findings[0].model_copy(update={"proof": "human", "verdict": "FAIL"})
        entry = entry.model_copy(update={"findings": (*entry.findings, wrong)})
    elif mutation in {"question", "criterion"}:
        update = {"question_text": "Is the hand natural?"} if mutation == "question" else {
            "evaluation_item_hash": "d" * 64}
        source = source.model_copy(update={"observations": (
            source.observations[0].model_copy(update=update),)})
        sources = (source,)
    elif mutation == "artifact":
        entry = entry.model_copy(update={"artifact_sha256": "d" * 64})
    elif mutation == "source":
        entry = entry.model_copy(update={"findings": (
            entry.findings[0].model_copy(update={"source_sha256": "d" * 64}),)})
    else:
        sources = ()
    result = diagnose_exact_result(entry, (), candidate.recipe, evaluation_sources=sources)
    assert not result.all_required_observed_pass
    assert set(result.failure_classes) & {"EVIDENCE_GAP", "RUBRIC_OR_STAGE_ERROR"}
    # Caller-supplied bare Findings cannot bypass original source admission.
    inputs = DecisionInputs.model_validate(setup["inputs"].model_copy(update={
        "candidates": (candidate,), "rubric_hash": candidate.recipe.rubric_hash,
        "evidence": (entry,), "latest_attempt_hash": entry.evidence_hash,
    }).model_dump(mode="python"))
    decision = VideoGenerationResolver().resolve_requirement(**{**setup, "inputs": inputs})
    assert decision.disposition != "REVIEW_CURRENT_RESULT"
    assert not decision.diagnosis.all_required_observed_pass


def test_pure_exact_diagnosis_preserves_bound_fail_beside_pass():
    from ai_video.production.generation_diagnosis import diagnose_exact_result

    setup, candidate, qa = marked_context()
    passed = experience_for(simulated_source(candidate, qa), setup, candidate)
    failed = experience_for(simulated_source(candidate, qa, verdict="FAIL"), setup, candidate)
    result = diagnose_exact_result(passed.evidence[0], failed.evidence, candidate.recipe,
        evaluation_sources=(*passed.evaluation_sources, *failed.evaluation_sources))
    assert result.failed_requirements == ("signal",)
    assert "QUALITY_FAILURE" in result.failure_classes
    assert not result.all_required_observed_pass


def test_invalid_same_record_proof_does_not_erase_independently_bound_fail():
    from ai_video.production.generation_diagnosis import diagnose_attempt, diagnose_exact_result

    setup, candidate, qa = marked_context()
    exp = experience_for(simulated_source(candidate, qa, verdict="FAIL"), setup, candidate)
    entry = exp.evidence[0]
    invalid = entry.findings[0].model_copy(update={"proof": "human", "verdict": "PASS"})
    entry = entry.model_copy(update={"findings": (*entry.findings, invalid)})
    for result in (diagnose_attempt(entry, candidate.recipe, evaluation_sources=exp.evaluation_sources),
                   diagnose_exact_result(entry, (), candidate.recipe, evaluation_sources=exp.evaluation_sources)):
        assert result.failed_requirements == ("signal",)
        assert set(result.failure_classes) == {"QUALITY_FAILURE", "RUBRIC_OR_STAGE_ERROR"}
        assert not result.all_required_observed_pass


@pytest.mark.parametrize("first_verdict", ["PASS", "FAIL"])
def test_partial_proofs_from_different_qa_authorities_cannot_form_one_pass(first_verdict):
    from ai_video.production.models import QaPolicy, GenerationEvaluationAuthority
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.generation_recipe import GenerationRecipe, RequirementExpression
    from ai_video.production.generation_evaluation import GenerationObservation
    from ai_video.production.generation_evaluation_criteria import evaluation_items
    from ai_video.production.generation_diagnosis import diagnose_exact_result
    from ai_video.production.generation_experience import empirical_assessment
    from test_requirement_semantics import semantic_rule, marked_policy

    setup, candidate, qa = marked_context()
    rules = [semantic_rule("req-a"), semantic_rule("req-b")]
    policy = marked_policy(rules)
    recipe = GenerationRecipe.model_validate({**candidate.recipe.model_dump(mode="python"),
        "acceptance_policy":policy,"rubric_hash":policy.profile_content_hash,
        "expressions":tuple(RequirementExpression.model_validate(r) for r in rules)})
    candidate = candidate.model_copy(update={"recipe":recipe})
    qa = seal_artifact(QaPolicy.model_validate({**qa.model_dump(mode="python"),"generation_acceptance":policy}))
    actor = qa.semantic_authorities[0].model_copy(update={"version":"replacement"})
    replacement = seal_artifact(QaPolicy.model_validate({**qa.model_dump(mode="python"),
        "semantic_authorities":(actor,),"generation_evaluation_authorities":(
            GenerationEvaluationAuthority(evaluator=actor,proof="analyzer"),)}))
    experiences=[]
    for selected, verdicts in ((qa,(first_verdict,"NOT_EVALUATED")),(replacement,("NOT_EVALUATED","PASS"))):
        source=simulated_source(candidate,selected)
        items=evaluation_items(acceptance=policy,qa_policy_content_hash=selected.content_hash,
            request_hash=source.request_hash,artifact_sha256=source.artifact_sha256,size_bytes=source.size_bytes)
        source=source.model_copy(update={"observations":tuple(GenerationObservation(
            requirement_id=item.requirement_id,verdict=verdict,observation="Synthetic partial observation",
            evaluation_item_hash=item.evaluation_item_hash,question_text=item.question_text,
            presentation_ref="fixture/request",answer_ref="fixture/response") for item,verdict in zip(items,verdicts))})
        source=source.model_copy(update={"presentation_evidence":source.presentation_evidence.model_copy(
            update={"answers_json":json.dumps(source.answer_payload())})})
        experiences.append(experience_for(source,setup,candidate))
    all_evidence=tuple(e for x in experiences for e in x.evidence)
    diagnosis=diagnose_exact_result(all_evidence[-1],all_evidence,recipe,
        evaluation_sources=tuple(s for x in experiences for s in x.evaluation_sources))
    assert "RUBRIC_OR_STAGE_ERROR" in diagnosis.failure_classes
    assert not diagnosis.all_required_observed_pass
    assert diagnosis.failed_requirements == (("req-a",) if first_verdict=="FAIL" else ())
    estimate=empirical_assessment(candidate,experiences[0].features,tuple(experiences))
    assert not estimate.supported_artifacts
    assert estimate.observed_success_fraction != 1


@pytest.mark.parametrize("observation", [
    "The rescue signal is visible before 2s.",
    "The prompt margin of 2.2s is irrelevant; the rescue signal is visible.",
    "The rescue signal is visible [frame 12].",
])
def test_observation_timestamps_and_evidence_citations_are_not_thresholds(observation):
    from ai_video.production.generation_evaluation import project_generation_evaluation_sources

    _, candidate, qa = marked_context()
    source = simulated_source(candidate, qa)
    source = source.model_copy(update={"observations": (
        source.observations[0].model_copy(update={"observation": observation}),)})
    source = source.model_copy(update={"presentation_evidence": source.presentation_evidence.model_copy(
        update={"answers_json": json.dumps(source.answer_payload())})})
    findings, refs = project_generation_evaluation_sources(sources=(source,), acceptance=candidate.recipe.acceptance_policy)
    assert findings[0].verdict == "PASS" and not refs


@pytest.mark.parametrize("observation", [
    "按[early]判断：未满足提前到位偏好，所以FAIL。",
])
def test_correct_question_cannot_admit_explicit_foreign_criterion_in_answer(observation):
    from ai_video.production.generation_evaluation import project_generation_evaluation_sources

    _, candidate, qa = marked_context()
    source = simulated_source(candidate, qa, verdict="FAIL")
    source = source.model_copy(update={"observations": (
        source.observations[0].model_copy(update={"observation": observation}),)})
    source = source.model_copy(update={"presentation_evidence": source.presentation_evidence.model_copy(
        update={"answers_json": json.dumps(source.answer_payload())})})
    with pytest.raises(ValueError, match="canonical criterion"):
        project_generation_evaluation_sources(sources=(source,), acceptance=candidate.recipe.acceptance_policy)


@pytest.mark.parametrize("end,text,valid", [
    (2440,"FAIL because it exceeds the prompt margin of 2.2s.",False),
    (2440,"FAIL: 2.44s > 2.2s.",False),
    (3100,"FAIL because the measured completion is > 3.0s, beyond the canonical 2.7s upper bound.",True),
])
def test_timing_failure_requires_canonical_measurement_not_prose(end,text,valid):
    from ai_video.production.generation_evaluation import project_generation_evaluation_sources
    from ai_video.production.generation_evaluation_criteria import TemporalMeasurement, evaluation_items
    from ai_video.production.generation_recipe import GenerationRecipe, RequirementExpression
    from ai_video.production.models import QaPolicy
    from ai_video.production.hashing import seal_artifact
    from test_requirement_semantics import semantic_rule, marked_policy

    _, candidate, qa = marked_context()
    spec = time_window()
    rule=semantic_rule("signal")
    rule.update(tolerance=spec.tolerance_text, measurement=spec.measurement_text, measurement_spec=spec.model_dump(mode="json"))
    policy=marked_policy([rule])
    qa=seal_artifact(QaPolicy.model_validate({**qa.model_dump(mode="python"),"generation_acceptance":policy}))
    recipe=GenerationRecipe.model_validate({**candidate.recipe.model_dump(mode="python"),
        "acceptance_policy":policy,"rubric_hash":policy.profile_content_hash,"expressions":(RequirementExpression.model_validate(rule),)})
    candidate=candidate.model_copy(update={"recipe":recipe})
    source=simulated_source(candidate,qa,verdict="FAIL")
    item=evaluation_items(acceptance=policy,qa_policy_content_hash=qa.content_hash,request_hash=source.request_hash,
        artifact_sha256=source.artifact_sha256,size_bytes=source.size_bytes)[0]
    measured=TemporalMeasurement(artifact_sha256=item.artifact_sha256,size_bytes=item.size_bytes,
        evaluation_item_hash=item.evaluation_item_hash,event_id=spec.event_id,boundary="end",timebase="source_media_millis",
        interval_millis=(end,end),method="word_alignment",coverage_millis=(0,4000),evidence_refs=("fixture/audio",))
    source=source.model_copy(update={"observations":(source.observations[0].model_copy(
        update={"observation":text,"measurement_result":measured}),)})
    source=source.model_copy(update={"presentation_evidence":source.presentation_evidence.model_copy(
        update={"answers_json":json.dumps(source.answer_payload())})})
    if valid:
        findings,_=project_generation_evaluation_sources(sources=(source,),acceptance=policy)
        assert findings[0].verdict=="FAIL"
    else:
        with pytest.raises(ValueError,match="time verdict contradicts"):
            project_generation_evaluation_sources(sources=(source,),acceptance=policy)


def test_non_temporal_failure_can_describe_measured_freeze_duration():
    from ai_video.production.generation_evaluation import project_generation_evaluation_sources

    _, candidate, qa = marked_context()
    source = simulated_source(candidate, qa, verdict="FAIL")
    source = source.model_copy(update={"observations": (
        source.observations[0].model_copy(update={"observation": "FAIL because the entire frame is frozen for > 1s, destroying visibility of the moving signal."}),)})
    source = source.model_copy(update={"presentation_evidence": source.presentation_evidence.model_copy(
        update={"answers_json": json.dumps(source.answer_payload())})})
    findings, _ = project_generation_evaluation_sources(sources=(source,), acceptance=candidate.recipe.acceptance_policy)
    assert findings[0].verdict == "FAIL"
