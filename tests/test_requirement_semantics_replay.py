"""Development-only shadow interpretation; no new evaluation or Production writes.

CI uses explicit synthetic evidence. A local caller may pass a real project and
exact historical Gate paths to shadow_project; no run directory is implicit.
"""

import hashlib
import json
from pathlib import Path

import pytest

from ai_video.production.generation_diagnosis import diagnose_exact_result
from ai_video.production.hashing import canonical_sha256
from ai_video.production.requirement_semantics import validate_semantic_inventory


def shadow_assessment(*, original_experiences, gate, artifact_bytes, proposed_policy, lineage, assessments):
    digest = hashlib.sha256(artifact_bytes).hexdigest()
    if digest != gate["artifact_sha256"] or len(artifact_bytes) != gate["size_bytes"]:
        raise ValueError("shadow input is not the exact historical media")
    matches = [exp for exp in original_experiences if any(e.artifact_sha256 == digest for e in exp.evidence)]
    if not matches:
        raise ValueError("shadow replay requires retained original experience")
    last = matches[-1]
    entry = next(e for e in reversed(last.evidence) if e.artifact_sha256 == digest)
    rules = validate_semantic_inventory(proposed_policy.profile_payload, proposed_policy.required_requirement_ids)
    old_ids = {r.requirement_id for r in last.candidate.recipe.expressions}
    if set(lineage) != {r.requirement_id for r in rules} or any(
        not refs or not set(refs) <= old_ids for refs in lineage.values()
    ):
        raise ValueError("shadow mapping must cover every proposed atom with original lineage")
    if set(gate["observations"]) != old_ids:
        raise ValueError("historical Gate inventory does not match original QA")
    if set(assessments) != set(lineage) or any(
        item.get("assessment") not in {"PASS", "FAIL", "NOT_EVALUATED", "advisory"}
        or not item.get("applicability") or not item.get("reason") for item in assessments.values()
    ):
        raise ValueError("each shadow atom requires an explicit applicability and assessment rationale")
    if any((assessments[r.requirement_id]["assessment"] == "advisory") != (r.level != "acceptance") for r in rules):
        raise ValueError("shadow hard and advisory assessments must stay separate")
    diagnosis = diagnose_exact_result(entry, tuple(e for exp in matches for e in exp.evidence), last.candidate.recipe)
    return dict(authority="development_shadow_only", artifact_sha256=digest, size_bytes=len(artifact_bytes),
        request_hash=entry.request_hash, original_rubric_hash=entry.rubric_hash,
        original_experience_hashes=[canonical_sha256(exp.model_dump(mode="json")) for exp in matches],
        original_source_hashes=[s.source_sha256 for exp in matches for s in exp.evaluation_sources],
        original_gate=gate, original_diagnosis=diagnosis.model_dump(mode="json"),
        proposed_rubric_hash=proposed_policy.profile_content_hash,
        proposed_version=proposed_policy.profile_payload["requirement_semantics_version"],
        atoms=[dict(requirement_id=r.requirement_id, category=r.semantics.category, stage=r.stage,
            original_requirement_ids=lineage[r.requirement_id],
            historical_references={key: gate["observations"][key] for key in lineage[r.requirement_id]},
            proposed_assessment=assessments[r.requirement_id]["assessment"],
            evidence_applicability=assessments[r.requirement_id]["applicability"],
            reason=assessments[r.requirement_id]["reason"],
            proof_origin="historical_reference_not_new_presentation") for r in rules],
        production_permission=False, empirical_benefit="not_established")


def shadow_project(*, project_root, gate_paths, proposed_policy, lineage, assessments_by_artifact):
    """Explicit local read-only wrapper through standard selected-state loading."""
    from ai_video.production.project import load_production_project
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.paths import _read_regular_file_nofollow

    root = Path(project_root).resolve(strict=True)
    loaded = load_production_project(root / "project.yaml")
    experiences = ProductionStateCommitter(root).read_generation_experiences()
    results = []
    for gate_path in gate_paths:
        gate = json.loads(Path(gate_path).read_bytes())
        state = next((attempt.video_generation_state for attempt in loaded.manifest.attempts
            if attempt.video_generation_state is not None and any(
                pointer is not None and pointer.artifact_sha256 == gate["artifact_sha256"] for pointer in (
                    attempt.video_generation_state.fetch_receipt, attempt.video_generation_state.local_fetch_receipt))), None)
        if state is None:
            raise ValueError("historical Gate has no canonical fetched artifact")
        pointer = state.fetch_receipt or state.local_fetch_receipt
        raw = _read_regular_file_nofollow(root / pointer.artifact_path, contained_by=root)
        results.append(shadow_assessment(original_experiences=experiences, gate=gate, artifact_bytes=raw.data,
            proposed_policy=proposed_policy, lineage=lineage,
            assessments=assessments_by_artifact[gate["artifact_sha256"]]))
    return results


def test_simulated_non_s01_shadow_retains_original_failure_and_has_no_permission():
    from ai_video.production.generation_experience import GenerationExperience
    from test_production_generation_decision import setup_decision, evidence
    from test_requirement_semantics import semantic_rule, marked_policy

    raw = b"explicit synthetic media identity fixture; not playable media"
    digest = hashlib.sha256(raw).hexdigest()
    setup = setup_decision()
    candidate = setup["inputs"].candidates[0]
    entry = evidence(setup, verdict="FAIL", artifact_sha256=digest)
    exp = GenerationExperience(projection=setup["projection"], candidate=candidate, evidence=(entry,))
    before = exp.model_dump_json()
    proposed = marked_policy([semantic_rule("readable"), semantic_rule("early", "directional_preference", "recipe_hint")])
    gate = dict(artifact_sha256=digest, size_bytes=len(raw), status="FAIL",
                observations={"duration": ["FAIL", "Historical duration miss"]})
    assessments = {"readable": dict(assessment="NOT_EVALUATED", applicability="criterion_changed",
        reason="Old duration observation does not prove rescue readability"),
        "early": dict(assessment="advisory", applicability="preference_only",
        reason="Historical duration miss remains available as a timing preference observation")}
    result = shadow_assessment(original_experiences=(exp,), gate=gate, artifact_bytes=raw,
        proposed_policy=proposed, lineage={"readable": ("duration",), "early": ("duration",)}, assessments=assessments)
    assert result["original_gate"]["status"] == "FAIL"
    assert result["original_diagnosis"]["failure_classes"] == ["QUALITY_FAILURE"]
    assert [a["proposed_assessment"] for a in result["atoms"]] == ["NOT_EVALUATED", "advisory"]
    assert result["production_permission"] is False
    assert exp.model_dump_json() == before
    with pytest.raises(ValueError, match="exact historical media"):
        shadow_assessment(original_experiences=(exp,), gate=gate, artifact_bytes=b"other",
            proposed_policy=proposed, lineage={"readable": ("duration",), "early": ("duration",)}, assessments=assessments)


def test_marked_raw_pass_cannot_replace_final_output_naturalness_or_proof():
    from ai_video.production.models import QaVerdict, QaLayer
    from ai_video.production.review import adjudicate_review_evidence
    from test_generation_evaluation_binding import marked_context, simulated_source, experience_for
    from test_production_final_output import viewing_policy, viewing_evidence

    setup, candidate, qa = marked_context()
    exp = experience_for(simulated_source(candidate, qa), setup, candidate)
    assert diagnose_exact_result(exp.evidence[0], (), candidate.recipe,
        evaluation_sources=exp.evaluation_sources).all_required_observed_pass
    policy = viewing_policy()
    for natural, expected in (("fail", QaVerdict.FAIL), ("not_evaluated", QaVerdict.NOT_EVALUATED)):
        result = adjudicate_review_evidence(policy, QaLayer.SEMANTIC,
            (viewing_evidence(policy, {"timing": "pass", "natural": natural, "audio": "pass"}),),
            review_request_content_hash="a" * 64)
        assert result is expected


def prospective_s01_policy():
    from ai_video.production.models import QaPolicy
    from ai_video.production.hashing import verify_artifact_hash

    path = Path(__file__).parents[1] / "docs/superpowers/artifacts/drama/jieshi-episode-01/s01-prospective-qa-v3.json"
    policy = QaPolicy.model_validate_json(path.read_bytes())
    assert verify_artifact_hash(policy)
    return policy


def test_prospective_s01_qa_uses_existing_activation_and_exact_history(tmp_path):
    from ai_video.production.project import load_production_project, load_qa_policy
    from ai_video.production.production_strategy_reader import selected_shot_generation_acceptance
    from test_production_repair import make_manifest_25_failed_layout_review_fixture

    fixture = make_manifest_25_failed_layout_review_fixture(tmp_path)
    before = load_production_project(tmp_path / "project.yaml")
    old_pointer = before.manifest.active_qa_policy
    old_bytes = (tmp_path / old_pointer.path).read_bytes()
    policy = prospective_s01_policy()
    fixture.committer.activate_qa_policy(policy,
        expected_manifest_revision=before.manifest.manifest_revision, attempt_id="prospective-s01-policy")
    after = load_production_project(tmp_path / "project.yaml")
    assert after.qa_policy == policy
    assert selected_shot_generation_acceptance(after, after.shots[0].shot_id) == policy.generation_acceptance
    assert after.manifest.attempts == before.manifest.attempts
    assert (tmp_path / old_pointer.path).read_bytes() == old_bytes
    assert load_qa_policy(tmp_path, old_pointer) == before.qa_policy


def test_prospective_s01_timing_preferences_cannot_create_a_quality_failure():
    from ai_video.production.generation_recipe import GenerationRecipe
    from ai_video.production.generation_feedback import _expressions
    from ai_video.production.generation_evaluation import GenerationEvaluationSource, project_generation_evaluation_sources
    from ai_video.production.generation_evaluation_criteria import evaluation_items, PresentationEvidence
    from ai_video.production.generation_diagnosis import diagnose_attempt
    from test_production_generation_decision import setup_decision, evidence

    qa = prospective_s01_policy()
    acceptance = qa.generation_acceptance
    setup = setup_decision()
    base = setup["inputs"].candidates[0]
    recipe = GenerationRecipe.model_validate({**base.recipe.model_dump(mode="python"),
        "rubric_hash": acceptance.profile_content_hash, "acceptance_policy": acceptance,
        "expressions": _expressions(acceptance, setup["projection"].requirement)})
    candidate = base.model_copy(update={"recipe": recipe, "final_output_goal": qa.final_output})
    items = evaluation_items(acceptance=acceptance, qa_policy_content_hash=qa.content_hash,
        request_hash="b"*64, artifact_sha256="c"*64, size_bytes=32)
    hints = {r.requirement_id for r in recipe.expressions if r.level == "recipe_hint"}
    assert hints == {"arrival-margin", "immediate-onset", "hand-trajectory", "fixed-palm", "zero-camera-motion", "broadcast-margin"}
    assert not hints & {item.requirement_id for item in items}
    assert not hints & {item.requirement_id for item in qa.final_output.requirements}
    assert all(r.intent_paths for r in recipe.expressions if r.stage == "raw_generation")
    actor = next(a.evaluator for a in qa.generation_evaluation_authorities if a.proof == "analyzer")
    presented = tuple(item for item in items if item.proof == "analyzer")
    source = GenerationEvaluationSource(schema_version="generation-evaluation/2", request_hash="b"*64,
        artifact_sha256="c"*64, size_bytes=32, rubric_hash=recipe.rubric_hash,
        qa_policy_content_hash=qa.content_hash, qa_policy_snapshot=qa, evaluator=actor, proof="analyzer",
        observations=[dict(requirement_id=i.requirement_id, verdict="NOT_EVALUATED", observation="Synthetic incomplete evidence",
            evaluation_item_hash=i.evaluation_item_hash, question_text=i.question_text,
            presentation_ref="fixture/request", answer_ref="fixture/response") for i in presented],
        advisory_observations=[dict(requirement_id="arrival-margin", observation="Later than 1.5s preferred endpoint",
            evidence_refs=["fixture/frame"])])
    source = source.model_copy(update={"presentation_evidence": PresentationEvidence(namespace="controlled-evaluator/1",
        interaction_ref="fixture", presentation_ref="fixture/request", answer_ref="fixture/response",
        event_order=("presentation", "answer"), actor_name=actor.name, actor_version=actor.version,
        items=presented, answers_json=json.dumps(source.answer_payload()))})
    findings, refs = project_generation_evaluation_sources(sources=(source,), acceptance=acceptance)
    entry = evidence(setup, candidate=candidate, findings=findings, unresolved_quality_refs=refs, artifact_sha256="c"*64)
    diagnosis = diagnose_attempt(entry, recipe, evaluation_sources=(source,))
    assert diagnosis.failure_classes == ("EVIDENCE_GAP",)
    assert not diagnosis.failed_requirements and not diagnosis.all_required_observed_pass
    assert {i.requirement_id for i in findings}.isdisjoint(hints)


def test_prospective_s01_compiler_carries_list_intent_and_uses_native_enum_controls():
    from ai_video.production.generation_feedback import _expressions
    from ai_video.production.generation_recipe import GenerationRecipe, expression_errors
    from ai_video.production._vidu_prompt import compile_vidu_prompt
    from test_production_vidu_prompt import _requirement
    from test_production_generation_decision import setup_decision

    requirement = _requirement()
    qa = prospective_s01_policy()
    policy = qa.generation_acceptance
    base = setup_decision()["inputs"].candidates[0].recipe
    recipe = GenerationRecipe.model_validate({**base.model_dump(mode="python"),
        "rubric_hash":policy.profile_content_hash,"acceptance_policy":policy,
        "expressions":_expressions(policy,requirement)})
    native = compile_vidu_prompt(requirement)
    assert expression_errors(recipe,requirement,native.prompt_text,native.expressed_control_paths) == ()
    rules = {r.requirement_id:r for r in recipe.expressions}
    assert rules["broadcast-core"].native_text == requirement.generation_intent.scene_continuity.state_constraints
    assert rules["identity-continuity"].native_text == ()
    assert "generation_intent.identity_continuity.preservation" in native.expressed_control_paths


@pytest.mark.parametrize("end,method,expected", [(2320,"word_aligned_audio","PASS"),
    (2440,"word_aligned_audio","PASS"),(2440,"asr_segment","NOT_EVALUATED"),(2800,"word_aligned_audio","FAIL")])
def test_prospective_s01_broadcast_uses_only_canonical_window(end, method, expected):
    from ai_video.production.generation_evaluation_criteria import TemporalMeasurement, temporal_verdict
    policy = prospective_s01_policy()
    rules = validate_semantic_inventory(policy.generation_acceptance.profile_payload,
        policy.generation_acceptance.required_requirement_ids)
    spec = next(r.measurement_spec for r in rules if r.requirement_id == "broadcast-window")
    assert (spec.lower_millis, spec.upper_millis) == (100,2700)
    measured = TemporalMeasurement(artifact_sha256="a"*64,size_bytes=32,evaluation_item_hash="b"*64,
        event_id=spec.event_id,boundary="end",timebase="source_media_millis",interval_millis=(end,end),
        method=method,coverage_millis=(0,4000),evidence_refs=("fixture/audio",))
    assert temporal_verdict(spec, measured) == expected


def test_prospective_s01_freeze_remains_a_final_output_failure():
    from ai_video.production.models import QaVerdict, QaLayer
    from ai_video.production.review import adjudicate_review_evidence
    from test_production_final_output import viewing_evidence

    policy = prospective_s01_policy()
    verdicts = {r.requirement_id: "pass" for r in policy.final_output.requirements if r.proof == "human"}
    verdicts["natural-dynamics"] = "fail"
    actor = next(a.evaluator for a in policy.generation_evaluation_authorities if a.proof == "human")
    item = viewing_evidence(policy, verdicts)
    item = item.model_copy(update={"tool_identity": actor,
        "measured_payload": {**item.measured_payload,"evaluator_identity": f"{actor.name}@{actor.version}"}})
    assert adjudicate_review_evidence(policy, QaLayer.SEMANTIC, (item,),
        review_request_content_hash="a"*64) is QaVerdict.FAIL
