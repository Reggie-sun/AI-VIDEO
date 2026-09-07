"""Pure selector tests; standard persisted application coverage is separate."""

import json

from ai_video.planning.production_strategy import (
    ProductionCapabilities, ProductionStrategyPolicy, ProductionStrategyResolver,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import GenerationEvaluationAuthority
from ai_video.production.source_use_evidence import SourceUseEvidence
from test_production_strategy_materialization import _loaded_with_intent


def qualified_context(tmp_path):
    loaded, _ = _loaded_with_intent(tmp_path)
    parent = loaded.shots[0]
    qa = loaded.qa_policy
    source = parent.production_intent.coverage_options[0].units[0].source_options[0]
    asset = loaded.registry.assets[0]
    identity = dict(parent_shot_content_hash=parent.content_hash, task_id="task-1",
        acceptance_profile_hash=qa.domain_acceptance.profile_content_hash,
        component_id="component-1", asset_id=asset.asset_id, asset_sha256=asset.sha256,
        size_bytes=asset.size_bytes, role=source.role, timebase=source.timebase,
        start=source.start, duration=source.duration,
        evaluator=qa.semantic_authorities[0].model_dump(mode="json"), proof="technical")
    evidence = SourceUseEvidence(**identity, evidence_id="source-observation",
        response_json=json.dumps({**identity, "observations": [{
            "requirement_id": "visual", "verdict": "PASS", "observation": "fixture source matches visual"}]}))
    qa = seal_artifact(qa.model_copy(update={
        "generation_evaluation_authorities": (GenerationEvaluationAuthority(
            evaluator=qa.semantic_authorities[0], proof="technical"),),
        "production_source_evidence": (evidence,),
    }))
    return loaded.model_copy(update={"qa_policy": qa})


def resolve(loaded, **kwargs):
    return ProductionStrategyResolver().resolve(loaded=loaded, parent_shot_id="shot-1", **kwargs)


def test_real_candidate_producer_selects_qualified_source_without_generation_capability(tmp_path):
    loaded = qualified_context(tmp_path)
    decision = resolve(loaded)
    assert decision.disposition == "selected"
    assert decision.selected.new_generation_count == 0
    assert len(decision.candidates) == 2
    assert decision == resolve(loaded)


def test_registered_bytes_without_use_evidence_cannot_be_selected(tmp_path):
    loaded, _ = _loaded_with_intent(tmp_path)
    decision = resolve(loaded)
    assert decision.disposition == "evidence_required"
    assert decision.selected is None


def test_failed_source_is_not_overridden_by_technical_registration(tmp_path):
    loaded = qualified_context(tmp_path)
    record = loaded.qa_policy.production_source_evidence[0]
    raw = json.loads(record.response_json)
    raw["observations"][0]["verdict"] = "FAIL"
    failed = SourceUseEvidence.model_validate({**record.model_dump(), "response_json": json.dumps(raw)})
    qa = seal_artifact(loaded.qa_policy.model_copy(update={"production_source_evidence": (failed,)}))
    decision = resolve(loaded.model_copy(update={"qa_policy": qa}))
    assert decision.selected is None
    assert "evidence_required:source_fail" in decision.reasons


def test_policy_and_qa_change_decision_identity(tmp_path):
    loaded = qualified_context(tmp_path)
    before = resolve(loaded)
    after = resolve(loaded, policy=ProductionStrategyPolicy(preference="unresolved"))
    assert before.input_hash != after.input_hash
    qa = seal_artifact(loaded.qa_policy.model_copy(update={"revision": loaded.qa_policy.revision + 1}))
    assert resolve(loaded.model_copy(update={"qa_policy": qa})).input_hash != before.input_hash


def test_generation_is_selected_only_with_component_acceptance_and_explicit_policy(tmp_path):
    from test_production_generation_decision import acceptance_policy
    from ai_video.production.generation_recipe import RequirementExpression

    loaded = qualified_context(tmp_path)
    rule = RequirementExpression(requirement_id="visual", level="acceptance",
        stage="raw_generation", dimension="visual", observable="intended visual",
        tolerance="exact", measurement="fixture", proof="technical", production_owner="generation")
    acceptance = acceptance_policy((rule,))
    allocation = loaded.qa_policy.production_allocations[0]
    component = allocation.components[0].model_copy(update={"generation_acceptance": acceptance})
    allocation = allocation.model_copy(update={"components": (component,)})
    qa = seal_artifact(loaded.qa_policy.model_copy(update={"production_allocations": (allocation,)}))
    loaded = loaded.model_copy(update={"qa_policy": qa})
    decision = resolve(loaded, capabilities=ProductionCapabilities(generation_available=True),
        policy=ProductionStrategyPolicy(preference="generation", allow_generation_exploration=True))
    assert decision.disposition == "selected"
    assert decision.selected.new_generation_count == 1
    assert resolve(loaded).selected.new_generation_count == 0


def test_enumeration_overflow_does_not_pick_first_candidate(tmp_path):
    loaded = qualified_context(tmp_path)
    decision = resolve(loaded, policy=ProductionStrategyPolicy(max_candidates=1))
    assert decision.disposition == "unresolved_choice"
    assert decision.selected is None
