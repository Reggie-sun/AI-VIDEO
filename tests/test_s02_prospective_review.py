"""S02 correctness and explicit read-only shadow; no production acceptance writes."""

import hashlib
import json
from pathlib import Path

import pytest

from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import QaPolicy
from ai_video.production.requirement_semantics import require_qa_semantic_admission


def s02_policy():
    path = Path(__file__).parents[1] / "docs/superpowers/artifacts/drama/jieshi-episode-01/s02-prospective-qa-v2.json"
    policy = QaPolicy.model_validate_json(path.read_bytes())
    assert verify_artifact_hash(policy)
    require_qa_semantic_admission(policy)
    return policy


def prospective_candidate(base, projection, qa):
    from ai_video.production.generation_feedback import _expressions
    from ai_video.production.generation_recipe import GenerationRecipe

    acceptance = qa.generation_acceptance
    recipe = GenerationRecipe.model_validate({**base.recipe.model_dump(mode="python"),
        "rubric_hash": acceptance.profile_content_hash, "acceptance_policy": acceptance,
        "expressions": _expressions(acceptance, projection.requirement)})
    return base.model_copy(update={"recipe": recipe, "final_output_goal": qa.final_output})


def test_s02_split_and_final_output_preserve_real_hard_requirements():
    qa = s02_policy()
    rules = {r["requirement_id"]: r for r in qa.generation_acceptance.profile_payload["generation_requirements"]}
    hard = set(qa.generation_acceptance.required_requirement_ids)
    assert "s02-chenli-boundary" not in rules
    assert {"s02-narrative-focus", "s02-question-progression", "s02-chenli-continuity",
            "s02-visible-artifacts", "s02-natural-action", "s02-open-continuity",
            "s02-turn-endpoint", "s02-identity-scene", "s02-no-generated-text",
            "s02-p4-dialogue", "s02-p4-ambience"} == hard
    assert {r.requirement_id for r in qa.final_output.requirements} == hard
    assert qa.final_output.goal_version == "2"
    for final in qa.final_output.requirements:
        assert final.observable == rules[final.requirement_id]["observable"]
    preference = rules["s02-chenli-framing-preference"]
    assert preference["level"] == "recipe_hint"
    assert preference["semantics"]["category"] == "directional_preference"
    assert "hard_basis" not in preference["semantics"]
    assert preference["semantics"]["derived_from"][0]["locator"] == "s02-chenli-boundary"


@pytest.mark.parametrize("hard_failure", [None, "s02-chenli-continuity", "s02-visible-artifacts"])
def test_face_only_is_advisory_but_real_hard_defects_still_fail(hard_failure):
    from ai_video.production.generation_diagnosis import diagnose_attempt
    from ai_video.production.generation_evaluation import GenerationEvaluationSource, project_generation_evaluation_sources
    from ai_video.production.generation_evaluation_criteria import evaluation_items, PresentationEvidence
    from test_production_generation_decision import setup_decision, evidence

    qa = s02_policy()
    setup = setup_decision()
    candidate = prospective_candidate(setup["inputs"].candidates[0], setup["projection"], qa)
    items = evaluation_items(acceptance=qa.generation_acceptance, qa_policy_content_hash=qa.content_hash,
        request_hash="b"*64, artifact_sha256="c"*64, size_bytes=32)
    assert "s02-chenli-framing-preference" not in {i.requirement_id for i in items}
    sources = []
    for authority in qa.generation_evaluation_authorities:
        if authority.proof != "analyzer":
            continue  # Never manufacture human presentation with a controlled evaluator.
        presented = tuple(i for i in items if i.proof == authority.proof)
        if not presented:
            continue
        source = GenerationEvaluationSource(schema_version="generation-evaluation/2", request_hash="b"*64,
            artifact_sha256="c"*64, size_bytes=32, rubric_hash=candidate.recipe.rubric_hash,
            qa_policy_content_hash=qa.content_hash, qa_policy_snapshot=qa,
            evaluator=authority.evaluator, proof=authority.proof,
            observations=[dict(requirement_id=i.requirement_id,
                verdict="FAIL" if i.requirement_id == hard_failure else "NOT_EVALUATED",
                observation="Synthetic real hard defect" if i.requirement_id == hard_failure else "Synthetic evidence gap",
                evaluation_item_hash=i.evaluation_item_hash, question_text=i.question_text,
                presentation_ref="fixture/request", answer_ref="fixture/response") for i in presented],
            advisory_observations=[dict(requirement_id="s02-chenli-framing-preference",
                observation="Head, ear and partial face enter the frame", evidence_refs=["fixture/frame"])])
        source = source.model_copy(update={"presentation_evidence": PresentationEvidence(namespace="controlled-evaluator/1",
            interaction_ref="fixture", presentation_ref="fixture/request", answer_ref="fixture/response",
            event_order=("presentation", "answer"), actor_name=authority.evaluator.name,
            actor_version=authority.evaluator.version, items=presented, answers_json=json.dumps(source.answer_payload()))})
        sources.append(source)
    findings, refs = project_generation_evaluation_sources(sources=sources, acceptance=qa.generation_acceptance)
    entry = evidence(setup, candidate=candidate, artifact_sha256="c"*64, findings=findings, unresolved_quality_refs=refs)
    diagnosis = diagnose_attempt(entry, candidate.recipe, evaluation_sources=sources)
    assert ("QUALITY_FAILURE" in diagnosis.failure_classes) == (hard_failure is not None)
    assert set(diagnosis.failed_requirements) == ({hard_failure} if hard_failure else set())
    assert "EVIDENCE_GAP" in diagnosis.failure_classes
    assert not diagnosis.all_required_observed_pass


def test_s02_new_policy_can_publish_without_rewriting_history(tmp_path):
    from ai_video.production.project import load_production_project
    from test_production_repair import make_manifest_25_failed_layout_review_fixture

    fixture = make_manifest_25_failed_layout_review_fixture(tmp_path)
    before = load_production_project(tmp_path / "project.yaml")
    old = (tmp_path / before.manifest.active_qa_policy.path).read_bytes()
    fixture.committer.activate_qa_policy(s02_policy(),
        expected_manifest_revision=before.manifest.manifest_revision, attempt_id="prospective-s02")
    after = load_production_project(tmp_path / "project.yaml")
    assert after.qa_policy == s02_policy()
    assert before.manifest.attempts == after.manifest.attempts
    assert (tmp_path / before.manifest.active_qa_policy.path).read_bytes() == old


def test_recorded_exact_shadow_is_incomplete_not_quality_failure_or_permission():
    path = Path(__file__).parents[1] / "docs/superpowers/artifacts/drama/jieshi-episode-01/s02-prospective-shadow-v2.json"
    report = json.loads(path.read_bytes())
    assert report["prospective_qa"] == s02_policy().content_hash
    assert report["manifest_revision"] == 35
    assert [r["artifact_sha256"] for r in report["results"]] == [
        "382e74c78b5699ea2c1d3b4c942cca9abfc4fd2de3b1a872a06092535b7312bc",
        "2c82bfe8197d96241dd535154faaab30dfa4d2aa54dba66e76c7b1a32020c92a"]
    for result in report["results"]:
        assert result["historical_gate"]["status"] == "FAIL"
        assert result["diagnosis"]["failure_classes"] == ["EVIDENCE_GAP"]
        assert not result["diagnosis"]["all_required_observed_pass"]
        assert result["diagnosis"]["failed_requirements"] == result["proposed_interventions"] == []
        assert result["holistic_status"] == "NOT_EVALUATED"
        assert result["production_permission"] is False
        hard = {r["requirement_id"] for r in result["atoms"] if r["status"] == "NOT_EVALUATED"}
        assert hard == set(s02_policy().generation_acceptance.required_requirement_ids)


def shadow_s02(*, project_root, gate_paths):
    """Explicit local call only. Reuses pure diagnosis; never invents new findings.

    Historical raw observations remain references. All new proof is missing:
    no continuous human presentation or evaluator answer is fabricated here.
    """
    from ai_video.production.project import load_production_project
    from ai_video.production.paths import _read_regular_file_nofollow
    from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
    from ai_video.production.generation_diagnosis import AttemptEvidence, diagnose_attempt
    from ai_video.production.generation_feedback import derive_generation_interventions, GenerationHistory
    from ai_video.production.state_commit import ProductionStateCommitter

    root = Path(project_root).resolve(strict=True)
    loaded = load_production_project(root / "project.yaml")
    qa = s02_policy()
    history = ProductionStateCommitter(root).read_generation_experiences()
    results = []
    for path in map(Path, gate_paths):
        gate_bytes = path.read_bytes()
        gate = json.loads(gate_bytes)
        binding_bytes = (path.parent / "s02-execution-binding.json").read_bytes()
        binding = GenerationDecisionExecutionBinding.model_validate_json(binding_bytes)
        attempt = next(a for a in loaded.manifest.attempts if a.video_generation_state is not None
            and a.video_generation_state.fetch_receipt is not None
            and a.video_generation_state.fetch_receipt.artifact_sha256 == gate["artifact_sha256"])
        pointer = attempt.video_generation_state.fetch_receipt
        if (attempt.attempt_id != gate["attempt_id"]
                or binding.context.target_shot_id != gate["shot_id"]
                or binding.inputs.rubric_hash != gate["acceptance_content_hash"]
                or attempt.video_generation_state.execution_binding.binding_hash != binding.binding_hash
                or attempt.video_generation_state.request.request_input_hash != binding.compiled_request.request_input_hash):
            raise ValueError("shadow Gate/binding/fetch identity mismatch")
        raw = _read_regular_file_nofollow(root / pointer.artifact_path, contained_by=root).data
        if hashlib.sha256(raw).hexdigest() != gate["artifact_sha256"] or len(raw) != gate["artifact_size_bytes"]:
            raise ValueError("shadow media differs from exact historical Gate")
        base = next(c for c in binding.inputs.candidates if c.candidate_id == binding.decision.selected_candidate_id)
        candidate = prospective_candidate(base, binding.projection, qa)
        entry = AttemptEvidence(task_id=binding.inputs.limits.task_id, shot_id=binding.context.target_shot_id,
            attempt_id=attempt.attempt_id, recipe_scope_hash=candidate.scope_hash,
            facts_hash=binding.inputs.facts_hash, rubric_hash=candidate.recipe.rubric_hash,
            request_hash=binding.compiled_request.request_input_hash,
            artifact_sha256=gate["artifact_sha256"], outcome="media")
        diagnosis = diagnose_attempt(entry, candidate.recipe)
        matches = [exp for exp in history if any(e.artifact_sha256 == gate["artifact_sha256"] for e in exp.evidence)]
        latest = matches[-1].evidence[-1].evidence_hash if matches else None
        proposals, conflicts = derive_generation_interventions(projection=binding.projection,
            candidates=(candidate,), history=GenerationHistory(tuple(matches), latest, binding.inputs.baseline_request),
            policy=binding.inputs.policy)
        results.append(dict(authority="development_shadow_only", production_permission=False,
            artifact_sha256=gate["artifact_sha256"], size_bytes=len(raw), request_hash=entry.request_hash,
            historical_gate_sha256=hashlib.sha256(gate_bytes).hexdigest(), historical_gate=gate,
            historical_binding_sha256=hashlib.sha256(binding_bytes).hexdigest(),
            retained_experience_count=len(matches), proposed_qa_hash=qa.content_hash,
            proposed_rubric_hash=qa.generation_acceptance.profile_content_hash,
            diagnosis=diagnosis.model_dump(mode="json"), proposed_interventions=[p.model_dump(mode="json") for p in proposals],
            conflicts=[c.model_dump(mode="json") for c in conflicts],
            holistic_status="NOT_EVALUATED", next_action="human 1.0x review of exact attempt02 first",
            atoms=[dict(requirement_id=r.requirement_id, category=r.semantics.category,
                stage=r.stage, status="NOT_EVALUATED" if r.level == "acceptance" else "advisory",
                historical_lineage=[ref.model_dump(mode="json") for ref in r.semantics.derived_from],
                reason="No fresh proof for the new criterion; historical sampled observations are references, not PASS/FAIL transfer."
                    if r.level == "acceptance" else "Framing/performance deviation alone is not a quality failure.")
                for r in candidate.recipe.expressions]))
    return dict(authority="development_shadow_only", manifest_revision=loaded.manifest.manifest_revision,
        selected_qa_unchanged=loaded.qa_policy.content_hash, prospective_qa=qa.content_hash, results=results)
