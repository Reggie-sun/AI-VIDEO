"""Exact evaluator-source projection, independent of live media analysis."""

from types import SimpleNamespace

import pytest

import ai_video.production.generation_evaluation as generation_evaluation
from ai_video.production.generation_evaluation import (
    GenerationEvaluationSource, GenerationObservation, UnresolvedQualityObservation,
    validate_generation_evaluation_sources,
)
from ai_video.production.models import ToolIdentity, GenerationEvaluationAuthority
from test_production_generation_decision import evidence, setup_decision


def fixture():
    setup = setup_decision(legacy_intent=True)
    entry = evidence(setup)
    tool = ToolIdentity(name="offline-evaluator", version="1")
    policy = SimpleNamespace(content_hash="a" * 64, semantic_authorities=(tool,),
        selected_generation_acceptance=lambda: setup["inputs"].candidates[0].recipe.acceptance_policy,
        generation_evaluation_authorities=(GenerationEvaluationAuthority(evaluator=tool, proof="technical"),))
    source = GenerationEvaluationSource(
        request_hash=entry.request_hash, artifact_sha256=entry.artifact_sha256,
        rubric_hash=entry.rubric_hash, qa_policy_content_hash=policy.content_hash,
        evaluator=tool, proof="technical", observations=(GenerationObservation(
            requirement_id="duration", verdict="PASS", observation="Injected four seconds"),))
    return entry.model_copy(update={"findings": source.project_findings()}), source, policy


def _v2_source(*, observations=(), unresolved=()):
    _, source, _ = fixture()
    from ai_video.production.hashing import seal_artifact

    qa_policy = seal_artifact(_whole_ad_policy())
    return GenerationEvaluationSource(
        schema_version="generation-evaluation/2",
        request_hash=source.request_hash,
        artifact_sha256=source.artifact_sha256,
        rubric_hash=source.rubric_hash,
        qa_policy_content_hash=qa_policy.content_hash,
        evaluator=source.evaluator,
        proof=source.proof,
        observations=observations,
        unresolved_quality_observations=unresolved,
        size_bytes=1,
        qa_policy_snapshot=qa_policy,
    )


def test_projection_keeps_exact_evaluator_document_identity():
    entry, source, policy = fixture()
    reopened = GenerationEvaluationSource.model_validate_json(source.model_dump_json())
    validate_generation_evaluation_sources(sources=(reopened,), evidence=entry, qa_policy=policy)
    assert entry.findings[0].source_sha256 == reopened.source_sha256


def test_project_findings_hashes_exact_source_once_per_call(monkeypatch):
    _, source, _ = fixture()
    observations = (
        source.observations[0],
        GenerationObservation(requirement_id="identity", verdict="PASS", observation="Same actor"),
        GenerationObservation(requirement_id="motion", verdict="PASS", observation="Required movement"),
    )
    source = source.model_copy(update={"observations": observations})
    expected_hash = generation_evaluation.canonical_sha256(source.model_dump(mode="json"))
    source_payload = source.model_dump(mode="json")
    original_hash = generation_evaluation.canonical_sha256
    hashed_source_payloads = []

    def counted_hash(payload):
        if isinstance(payload, dict) and payload.get("request_hash") == source.request_hash:
            hashed_source_payloads.append(payload)
        return original_hash(payload)

    monkeypatch.setattr(generation_evaluation, "canonical_sha256", counted_hash)
    findings = source.project_findings()

    assert hashed_source_payloads == [source_payload]
    assert tuple(f.source_sha256 for f in findings) == (expected_hash,) * len(observations)
    assert tuple(f.requirement_id for f in findings) == tuple(o.requirement_id for o in observations)
    assert tuple(f.observation for f in findings) == tuple(o.observation for o in observations)

    changed_observations = (
        observations[0].model_copy(update={"observation": "Changed source evidence"}),
        *observations[1:],
    )
    changed_source = source.model_copy(update={"observations": changed_observations})
    changed_payload = changed_source.model_dump(mode="json")
    changed_hash = original_hash(changed_payload)
    findings_after_change = changed_source.project_findings()

    assert hashed_source_payloads == [source_payload, changed_payload]
    assert findings_after_change[0].source_sha256 == changed_hash
    assert findings_after_change[0].source_sha256 != findings[0].source_sha256
    assert findings_after_change[0].observation == "Changed source evidence"


def test_unresolved_refs_hashes_exact_source_once_per_call(monkeypatch):
    unresolved = (
        UnresolvedQualityObservation(
            observation_id="quality-1", original_answer="Soft image", visible_problem="Blur",
            quality_basis="Edges lose detail", evidence_refs=("frame-1",), answer_ref="answer-1",
        ),
        UnresolvedQualityObservation(
            observation_id="quality-2", original_answer="Soft face", visible_problem="Identity detail",
            quality_basis="Facial features are unclear", evidence_refs=("frame-2",), answer_ref="answer-1",
        ),
    )
    source = _v2_source(unresolved=unresolved)
    expected_source_hash = generation_evaluation.canonical_sha256(source.model_dump(mode="json"))
    source_payload = source.model_dump(mode="json")
    original_hash = generation_evaluation.canonical_sha256
    hashed_source_payloads = []

    def counted_hash(payload):
        if isinstance(payload, dict) and payload.get("request_hash") == source.request_hash:
            hashed_source_payloads.append(payload)
        return original_hash(payload)

    monkeypatch.setattr(generation_evaluation, "canonical_sha256", counted_hash)
    refs = source.unresolved_refs()
    expected_refs = tuple(original_hash({
        "source_hash": expected_source_hash,
        "entry": item.model_dump(mode="json"),
    }) for item in unresolved)

    assert hashed_source_payloads == [source_payload]
    assert refs == expected_refs

    changed_unresolved = (
        unresolved[0].model_copy(update={"visible_problem": "Changed visible problem"}),
        *unresolved[1:],
    )
    changed_source = source.model_copy(update={"unresolved_quality_observations": changed_unresolved})
    changed_payload = changed_source.model_dump(mode="json")
    changed_source_hash = original_hash(changed_payload)
    changed_refs = changed_source.unresolved_refs()

    assert hashed_source_payloads == [source_payload, changed_payload]
    assert changed_refs == tuple(original_hash({
        "source_hash": changed_source_hash,
        "entry": item.model_dump(mode="json"),
    }) for item in changed_unresolved)
    assert changed_refs != refs


def test_empty_projection_does_not_hash_source(monkeypatch):
    source = _v2_source()
    hash_calls = []
    original_hash = generation_evaluation.canonical_sha256

    def counted_hash(payload):
        hash_calls.append(payload)
        return original_hash(payload)

    monkeypatch.setattr(generation_evaluation, "canonical_sha256", counted_hash)

    assert source.project_findings() == ()
    assert source.unresolved_refs() == ()
    assert hash_calls == []


@pytest.mark.parametrize("field", ["request_hash", "artifact_sha256", "rubric_hash", "qa_policy_content_hash"])
def test_source_from_different_exact_context_is_rejected(field):
    entry, source, policy = fixture()
    source = source.model_copy(update={field: "f" * 64})
    with pytest.raises(ValueError, match="exact media"):
        validate_generation_evaluation_sources(sources=(source,), evidence=entry, qa_policy=policy)


def test_caller_cannot_replace_findings_or_omit_sources():
    entry, source, policy = fixture()
    with pytest.raises(ValueError, match="original evaluator"):
        validate_generation_evaluation_sources(sources=(), evidence=entry, qa_policy=policy)
    altered = entry.model_copy(update={"findings": (entry.findings[0].model_copy(update={"verdict": "FAIL"}),)})
    with pytest.raises(ValueError, match="differ from original"):
        validate_generation_evaluation_sources(sources=(source,), evidence=altered, qa_policy=policy)


def test_unselected_evaluator_is_rejected():
    entry, source, policy = fixture()
    policy.semantic_authorities = (ToolIdentity(name="another", version="1"),)
    with pytest.raises(ValueError, match="policy-selected"):
        validate_generation_evaluation_sources(sources=(source,), evidence=entry, qa_policy=policy)


def test_selected_tool_cannot_relabel_its_result_as_human_proof():
    entry, source, policy = fixture()
    source = source.model_copy(update={"proof": "human"})
    entry = entry.model_copy(update={"findings": source.project_findings()})
    with pytest.raises(ValueError, match="proof kind"):
        validate_generation_evaluation_sources(sources=(source,), evidence=entry, qa_policy=policy)


def test_current_qa_identity_cannot_authorize_an_unselected_generation_rubric():
    entry, source, policy = fixture()
    policy.selected_generation_acceptance = lambda: SimpleNamespace(profile_content_hash="f" * 64)
    with pytest.raises(ValueError, match="rubric is not selected"):
        validate_generation_evaluation_sources(sources=(source,), evidence=entry, qa_policy=policy)


def test_old_qa_policy_keeps_exact_bytes_when_new_authority_field_is_absent():
    from test_production_ecommerce_product_interaction_e2e import _commercial_policy
    from ai_video.production.models import QaPolicy
    from ai_video.production.hashing import canonical_sha256

    policy = _commercial_policy()
    payload = policy.model_dump(mode="json")
    assert "generation_evaluation_authorities" not in payload
    assert "generation_acceptance" not in payload
    reopened = QaPolicy.model_validate(payload)
    assert policy.content_hash == "7c2365bca6069e6b5434cf9c953959145e750c3c643a4aae1ec988f7a4f66cce"
    assert canonical_sha256(reopened) == policy.content_hash
    assert reopened.model_dump(mode="json") == payload


def test_legacy_evaluator_source_and_nested_evidence_hashes_are_frozen():
    """A /1 source remains byte-identical while /2 semantics are introduced elsewhere."""
    entry, source, _ = fixture()
    payload = source.model_dump(mode="json")

    assert payload == {
        "schema_version": "generation-evaluation/1",
        "request_hash": entry.request_hash,
        "artifact_sha256": entry.artifact_sha256,
        "rubric_hash": entry.rubric_hash,
        "qa_policy_content_hash": "a" * 64,
        "evaluator": {"name": "offline-evaluator", "version": "1"},
        "proof": "technical",
        "observations": [{
            "requirement_id": "duration",
            "verdict": "PASS",
            "observation": "Injected four seconds",
            "span_millis": None,
        }],
    }
    assert "analysis_evidence" not in payload
    assert source.source_sha256 == "7462c4ac94d4d2f9bb987cb8c564c72d2bfc19c70d7badd3e63c4292b6d50d79"
    assert entry.evidence_hash == "4c977fa225df858e3d6b344599a269dacba8fc3a7f07b9a6f74d3a229f054721"
    assert GenerationEvaluationSource.model_validate(payload).model_dump(mode="json") == payload
    assert entry.findings[0].model_dump(mode="json") == {
        "requirement_id": "duration",
        "rubric_hash": entry.rubric_hash,
        "stage": "raw_generation",
        "proof": "technical",
        "verdict": "PASS",
        "source_sha256": source.source_sha256,
        "observation": "Injected four seconds",
        "span_millis": None,
    }


def test_generation_acceptance_does_not_replace_whole_ad_policy():
    from ai_video.production.models import QaPolicy

    policy = _whole_ad_policy()
    generation = setup_decision()["inputs"].candidates[0].recipe.acceptance_policy
    payload = policy.model_dump(mode="json")
    payload["generation_acceptance"] = generation.model_dump(mode="json")
    reopened = QaPolicy.model_validate(payload)
    assert reopened.domain_acceptance == policy.domain_acceptance
    assert reopened.selected_generation_acceptance() == generation


def test_whole_ad_policy_without_projection_is_not_generation_acceptance():
    assert _whole_ad_policy().selected_generation_acceptance() is None


def _whole_ad_policy():
    from test_production_ecommerce_product_interaction_e2e import _commercial_policy
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.ecommerce_media_acceptance import create_qingyan_ecommerce_acceptance_profile
    from ai_video.production.models import QaPolicy

    profile = create_qingyan_ecommerce_acceptance_profile()
    domain = DomainAcceptancePolicy(domain_id="ecommerce", profile_id=profile.profile_id,
        profile_version=profile.profile_version, profile_content_hash=profile.content_hash,
        profile_payload=profile.model_dump(mode="json"),
        measurement_contract_version=profile.measurement_contract_version,
        required_requirement_ids=profile.required_requirement_ids)
    return QaPolicy.model_validate({**_commercial_policy().model_dump(mode="json"),
        "domain_acceptance": domain.model_dump(mode="json")})
