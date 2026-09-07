"""Exact evaluator-source projection, independent of live media analysis."""

from types import SimpleNamespace

import pytest

from ai_video.production.generation_evaluation import (
    GenerationEvaluationSource, GenerationObservation, validate_generation_evaluation_sources,
)
from ai_video.production.models import ToolIdentity, GenerationEvaluationAuthority
from test_production_generation_decision import evidence, setup_decision


def fixture():
    entry = evidence(setup_decision())
    tool = ToolIdentity(name="offline-evaluator", version="1")
    policy = SimpleNamespace(content_hash="a" * 64, semantic_authorities=(tool,),
        selected_generation_acceptance=lambda: SimpleNamespace(profile_content_hash=entry.rubric_hash),
        generation_evaluation_authorities=(GenerationEvaluationAuthority(evaluator=tool, proof="technical"),))
    source = GenerationEvaluationSource(
        request_hash=entry.request_hash, artifact_sha256=entry.artifact_sha256,
        rubric_hash=entry.rubric_hash, qa_policy_content_hash=policy.content_hash,
        evaluator=tool, proof="technical", observations=(GenerationObservation(
            requirement_id="duration", verdict="PASS", observation="Injected four seconds"),))
    return entry.model_copy(update={"findings": source.project_findings()}), source, policy


def test_projection_keeps_exact_evaluator_document_identity():
    entry, source, policy = fixture()
    reopened = GenerationEvaluationSource.model_validate_json(source.model_dump_json())
    validate_generation_evaluation_sources(sources=(reopened,), evidence=entry, qa_policy=policy)
    assert entry.findings[0].source_sha256 == reopened.source_sha256


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
    assert canonical_sha256(reopened) == policy.content_hash
    assert reopened.model_dump(mode="json") == payload


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
