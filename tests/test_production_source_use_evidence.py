from __future__ import annotations

import json

import pytest

from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    GenerationEvaluationAuthority,
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    SourceReference,
    ToolIdentity,
)
from ai_video.production.source_use_evidence import SourceUseEvidence, assess_source_use


HASH = "a" * 64
SHOT_HASH = "b" * 64
ASSET_HASH = "c" * 64
TECHNICAL = ToolIdentity(name="fixture-analyzer", version="1")
HUMAN = ToolIdentity(name="fixture-human", version="1")


def _acceptance(*, ids: tuple[str, ...] = ("action", "timing"), proof="technical", stage="source_use") -> DomainAcceptancePolicy:
    payload = {
        "domain_id": "test",
        "profile_id": "final",
        "profile_version": "1",
        "measurement_contract_version": "test/1",
        "required_requirement_ids": ids,
        "source_use_requirements": tuple({"requirement_id": i, "proof": proof, "stage": stage} for i in ids),
    }
    digest = canonical_sha256(payload)
    return DomainAcceptancePolicy(
        domain_id="test", profile_id="final", profile_version="1",
        profile_content_hash=digest, profile_payload={**payload, "content_hash": digest},
        measurement_contract_version="test/1", required_requirement_ids=ids,
    )


def _evidence(*, acceptance: DomainAcceptancePolicy, evidence_id: str = "evidence-1",
              evaluator: ToolIdentity = TECHNICAL, proof: str = "technical",
              observations: tuple[tuple[str, str], ...] = (("action", "PASS"), ("timing", "PASS")),
              start: int = 0, role: str = "reuse", human_actor_id: str | None = None,
              evidence_ref: str | None = None) -> SourceUseEvidence:
    response = {
        "parent_shot_content_hash": SHOT_HASH,
        "task_id": "task-1",
        "acceptance_profile_hash": acceptance.profile_content_hash,
        "component_id": "component-1",
        "asset_id": "asset-1",
        "asset_sha256": ASSET_HASH,
        "size_bytes": 123,
        "role": role,
        "timebase": "frames",
        "start": start,
        "duration": 24,
        "evaluator": evaluator.model_dump(mode="json"),
        "proof": proof,
        "observations": [
            {"requirement_id": requirement_id, "verdict": verdict, "observation": requirement_id}
            for requirement_id, verdict in observations
        ],
    }
    if human_actor_id is not None:
        response["human_actor_id"] = human_actor_id
    if evidence_ref is not None:
        response["evidence_ref"] = evidence_ref
    return SourceUseEvidence(
        evidence_id=evidence_id,
        parent_shot_content_hash=SHOT_HASH,
        task_id="task-1",
        acceptance_profile_hash=acceptance.profile_content_hash,
        component_id="component-1",
        asset_id="asset-1",
        asset_sha256=ASSET_HASH,
        size_bytes=123,
        role=role,
        timebase="frames",
        start=start,
        duration=24,
        evaluator=evaluator,
        proof=proof,
        response_json=json.dumps(response),
    )


def _policy(*, acceptance: DomainAcceptancePolicy, evidence: tuple[SourceUseEvidence, ...] = (),
            authorities: tuple[GenerationEvaluationAuthority, ...] | None = None) -> QaPolicy:
    if authorities is None:
        authorities = (GenerationEvaluationAuthority(evaluator=TECHNICAL, proof="technical"),)
    return seal_artifact(QaPolicy(
        artifact_id="fixture-policy", revision=1, content_hash="0" * 64,
        creation_receipt_id="fixture-policy",
        source_provenance=(SourceReference(kind="derived", reference="fixture"),),
        policy_id="fixture-policy", policy_version="1",
        required_layers=(QaLayer.SEMANTIC,),
        technical_thresholds=QaTechnicalThresholds(
            black_luma_max_milli=10, silence_peak_max_millidb=-60_000,
            clipping_peak_min_millidb=-100,
        ),
        layout_rules=QaLayoutRules(safe_area_inset_milli=50, caption_overflow_tolerance_milli=0),
        strategy_rules_version="1", semantic_requirement="required",
        semantic_authorities=tuple(item.evaluator for item in authorities),
        generation_evaluation_authorities=authorities,
        domain_acceptance=acceptance,
        production_source_evidence=evidence,
    ))


def _assess(policy: QaPolicy, *, start: int = 0, role: str = "reuse", ids: tuple[str, ...] = ("evidence-1",)):
    return assess_source_use(
        qa_policy=policy,
        parent_shot_content_hash=SHOT_HASH,
        task_id="task-1",
        component_id="component-1",
        asset_id="asset-1",
        asset_sha256=ASSET_HASH,
        size_bytes=123,
        role=role,
        timebase="frames",
        start=start,
        duration=24,
        requirement_ids=("action", "timing"),
        evidence_ids=ids,
    )


def test_exact_current_source_use_passes_with_complete_authorized_coverage():
    acceptance = _acceptance()
    evidence = _evidence(acceptance=acceptance)
    policy = _policy(acceptance=acceptance, evidence=(evidence,))

    assert _assess(policy) == "PASS"
    assert evidence.evidence_hash == canonical_sha256(evidence.model_dump(mode="json"))


@pytest.mark.parametrize("proof,stage", [("human", "source_use"), ("technical", "shot_editorial")])
def test_source_pass_cannot_replace_required_proof_or_assembly_stage(proof, stage):
    acceptance = _acceptance(proof=proof, stage=stage)
    policy = _policy(acceptance=acceptance, evidence=(_evidence(acceptance=acceptance),))
    assert _assess(policy) == "NOT_EVALUATED"


def test_wrong_window_or_role_is_not_evaluated():
    acceptance = _acceptance()
    policy = _policy(acceptance=acceptance, evidence=(_evidence(acceptance=acceptance),))

    assert _assess(policy, start=1) == "NOT_EVALUATED"
    assert _assess(policy, role="insert") == "NOT_EVALUATED"


def test_full_frame_evidence_cannot_qualify_a_different_reframe():
    from ai_video.production.composition_contracts import FixedTransform

    acceptance = _acceptance()
    policy = _policy(acceptance=acceptance, evidence=(_evidence(acceptance=acceptance),))
    assert assess_source_use(qa_policy=policy, parent_shot_content_hash=SHOT_HASH,
        task_id="task-1", component_id="component-1", asset_id="asset-1", asset_sha256=ASSET_HASH,
        size_bytes=123, role="reuse", timebase="frames", start=0, duration=24,
        requirement_ids=("action", "timing"), evidence_ids=("evidence-1",),
        transform=FixedTransform(translate_x_px=20)) == "NOT_EVALUATED"


def test_profile_and_evaluator_tampering_are_rejected():
    acceptance = _acceptance()
    stale = _evidence(acceptance=acceptance)
    stale_response = json.loads(stale.response_json)
    stale_response["acceptance_profile_hash"] = HASH
    stale = SourceUseEvidence.model_validate({
        **stale.model_dump(mode="json"), "acceptance_profile_hash": HASH,
        "response_json": json.dumps(stale_response),
    })
    with pytest.raises(ValueError, match="acceptance hash is stale"):
        _policy(acceptance=acceptance, evidence=(stale,))

    unselected = _evidence(
        acceptance=acceptance, evaluator=ToolIdentity(name="other", version="1"),
    )
    with pytest.raises(ValueError, match="policy-selected"):
        _policy(acceptance=acceptance, evidence=(unselected,))


def test_human_identity_and_explicit_proof_mapping_are_required():
    acceptance = _acceptance()
    with pytest.raises(ValueError, match="human_actor_id"):
        _evidence(acceptance=acceptance, evaluator=HUMAN, proof="human")
    human = _evidence(
        acceptance=acceptance, evaluator=HUMAN, proof="human",
        human_actor_id="reviewer-1", evidence_ref="review.md#1",
    )
    with pytest.raises(ValueError, match="proof mapping"):
        _policy(
            acceptance=acceptance,
            evidence=(human,),
            authorities=(GenerationEvaluationAuthority(evaluator=HUMAN, proof="technical"),),
        )


def test_missing_coverage_is_not_evaluated_and_unknown_caller_ids_fail_closed():
    acceptance = _acceptance()
    evidence = _evidence(acceptance=acceptance, observations=(("action", "PASS"),))
    policy = _policy(acceptance=acceptance, evidence=(evidence,))

    assert _assess(policy) == "NOT_EVALUATED"
    with pytest.raises(ValueError, match="unknown"):
        _assess(policy, ids=("missing",))


def test_later_human_fail_cannot_be_hidden_by_old_selected_pass():
    acceptance = _acceptance()
    old_pass = _evidence(acceptance=acceptance, evidence_id="old-pass")
    human_fail = _evidence(
        acceptance=acceptance, evidence_id="human-fail", evaluator=HUMAN, proof="human",
        observations=(("action", "FAIL"), ("timing", "PASS")),
        human_actor_id="reviewer-1", evidence_ref="review.md#2",
    )
    policy = _policy(
        acceptance=acceptance,
        evidence=(old_pass, human_fail),
        authorities=(
            GenerationEvaluationAuthority(evaluator=TECHNICAL, proof="technical"),
            GenerationEvaluationAuthority(evaluator=HUMAN, proof="human"),
        ),
    )

    assert _assess(policy, ids=("old-pass",)) == "FAIL"


def test_response_identity_is_not_synthesized_and_legacy_policy_bytes_are_unchanged():
    acceptance = _acceptance()
    evidence = _evidence(acceptance=acceptance)
    response = json.loads(evidence.response_json)
    response["role"] = "insert"
    with pytest.raises(ValueError, match="response"):
        SourceUseEvidence.model_validate({
            **evidence.model_dump(mode="json"), "response_json": json.dumps(response),
        })

    policy = _policy(acceptance=acceptance)
    payload = policy.model_dump(mode="json")
    assert "production_source_evidence" not in payload
    assert QaPolicy.model_validate(payload).model_dump(mode="json") == payload
