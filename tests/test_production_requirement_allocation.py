from __future__ import annotations

import pytest

from ai_video.production.domain_acceptance import (
    ComponentRequirementAllocation,
    DomainAcceptancePolicy,
    ProductionRequirementAllocation,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    SourceReference,
    ToolIdentity,
)


HASH = "a" * 64
SHOT_HASH = "b" * 64


def _acceptance(*, profile_id: str, ids: tuple[str, ...], generation: bool) -> DomainAcceptancePolicy:
    payload = {
        "domain_id": "test",
        "profile_id": profile_id,
        "profile_version": "1",
        "measurement_contract_version": "test/1",
        "required_requirement_ids": ids,
    }
    if generation:
        payload["generation_requirements"] = tuple(
            {
                "requirement_id": requirement_id,
                "level": "acceptance",
                "stage": "raw_generation",
                "dimension": "fixture",
                "observable": requirement_id,
                "tolerance": "exact",
                "measurement": "fixture",
                "proof": "technical",
                "intent_paths": (),
                "production_owner": "fixture",
            }
            for requirement_id in ids
        )
    digest = canonical_sha256(payload)
    return DomainAcceptancePolicy(
        domain_id="test",
        profile_id=profile_id,
        profile_version="1",
        profile_content_hash=digest,
        profile_payload={**payload, "content_hash": digest},
        measurement_contract_version="test/1",
        required_requirement_ids=ids,
    )


def _qa_policy(*, domain: DomainAcceptancePolicy | None, generation: DomainAcceptancePolicy | None = None,
               allocations: tuple[ProductionRequirementAllocation, ...] = ()) -> QaPolicy:
    return seal_artifact(QaPolicy(
        artifact_id="fixture-policy",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="fixture-policy",
        source_provenance=(SourceReference(kind="derived", reference="fixture"),),
        policy_id="fixture-policy",
        policy_version="1",
        required_layers=(QaLayer.SEMANTIC,),
        technical_thresholds=QaTechnicalThresholds(
            black_luma_max_milli=10,
            silence_peak_max_millidb=-60_000,
            clipping_peak_min_millidb=-100,
        ),
        layout_rules=QaLayoutRules(
            safe_area_inset_milli=50,
            caption_overflow_tolerance_milli=0,
        ),
        strategy_rules_version="1",
        semantic_requirement="required",
        semantic_authorities=(ToolIdentity(name="fixture-reviewer", version="1"),),
        domain_acceptance=domain,
        generation_acceptance=generation,
        production_allocations=allocations,
    ))


def _allocation(*, parent: DomainAcceptancePolicy, components: tuple[ComponentRequirementAllocation, ...] = (),
                assembly: tuple[str, ...] = ("action", "timing", "audio")) -> ProductionRequirementAllocation:
    return ProductionRequirementAllocation(
        allocation_id="allocation-1",
        parent_shot_id="shot-1",
        parent_shot_content_hash=SHOT_HASH,
        task_id="task-1",
        parent_acceptance_hash=parent.profile_content_hash,
        parent_requirement_ids=("action", "timing", "audio"),
        components=components,
        assembly_requirement_ids=assembly,
    )


def test_complete_allocation_returns_only_explicit_component_generation_policy():
    final = _acceptance(profile_id="final", ids=("action", "timing", "audio"), generation=False)
    raw = _acceptance(profile_id="raw-action", ids=("action",), generation=True)
    allocation = _allocation(parent=final, components=(ComponentRequirementAllocation(
        component_id="action-plate", requirement_ids=("action",), generation_acceptance=raw,
    ), ComponentRequirementAllocation(
        component_id="audio", requirement_ids=("audio",), generation_acceptance=None,
    )))
    policy = _qa_policy(domain=final, allocations=(allocation,))

    assert policy.require_production_allocation(
        allocation_hash=allocation.allocation_hash,
        parent_shot_id="shot-1", parent_shot_content_hash=SHOT_HASH, task_id="task-1",
    ) == allocation
    assert policy.selected_component_generation_acceptance(
        allocation_hash=allocation.allocation_hash, component_id="action-plate",
        parent_shot_id="shot-1", parent_shot_content_hash=SHOT_HASH, task_id="task-1",
    ) == raw
    assert policy.selected_component_generation_acceptance(
        allocation_hash=allocation.allocation_hash, component_id="audio",
        parent_shot_id="shot-1", parent_shot_content_hash=SHOT_HASH, task_id="task-1",
    ) is None


@pytest.mark.parametrize("update, message", [
    ({"parent_requirement_ids": ("action", "timing", "unknown"),
      "assembly_requirement_ids": ("action", "timing", "unknown")}, "parent requirement"),
    ({"assembly_requirement_ids": ("timing",)}, "cover"),
    ({"components": (ComponentRequirementAllocation(component_id="action", requirement_ids=("action",)),),
      "assembly_requirement_ids": ("timing",)}, "cover"),
])
def test_allocation_rejects_unknown_or_uncovered_requirements(update, message):
    final = _acceptance(profile_id="final", ids=("action", "timing", "audio"), generation=False)
    with pytest.raises(ValueError, match=message):
        allocation = ProductionRequirementAllocation.model_validate({
            **_allocation(parent=final).model_dump(mode="json"), **update,
        })
        _qa_policy(domain=final, allocations=(allocation,))


def test_allocation_rejects_duplicate_component_and_allocation_ids():
    final = _acceptance(profile_id="final", ids=("action", "timing", "audio"), generation=False)
    with pytest.raises(ValueError, match="component IDs must be unique"):
        ProductionRequirementAllocation(
            **{
                **_allocation(parent=final).model_dump(mode="json"),
                "components": (
                ComponentRequirementAllocation(component_id="same", requirement_ids=("action",)),
                ComponentRequirementAllocation(component_id="same", requirement_ids=("audio",)),
                ),
                "assembly_requirement_ids": ("timing",),
            },
        )
    allocation = _allocation(parent=final)
    with pytest.raises(ValueError, match="allocation IDs must be unique"):
        _qa_policy(domain=final, allocations=(allocation, allocation))


@pytest.mark.parametrize("kwargs", [
    {"allocation_hash": HASH},
    {"parent_shot_id": "other-shot"},
    {"parent_shot_content_hash": HASH},
    {"task_id": "other-task"},
])
def test_lookup_rejects_stale_parent_identity(kwargs):
    final = _acceptance(profile_id="final", ids=("action", "timing", "audio"), generation=False)
    allocation = _allocation(parent=final)
    policy = _qa_policy(domain=final, allocations=(allocation,))
    identity = dict(
        allocation_hash=allocation.allocation_hash,
        parent_shot_id="shot-1", parent_shot_content_hash=SHOT_HASH, task_id="task-1",
    )
    identity.update(kwargs)
    with pytest.raises(ValueError, match="allocation"):
        policy.require_production_allocation(**identity)


def test_component_generation_acceptance_must_be_inventory_backed_and_a_subset():
    final = _acceptance(profile_id="final", ids=("action", "timing", "audio"), generation=False)
    invalid = _acceptance(profile_id="raw", ids=("timing",), generation=True)
    with pytest.raises(ValueError, match="subset"):
        ComponentRequirementAllocation(
            component_id="action", requirement_ids=("action",), generation_acceptance=invalid,
        )
    no_inventory = _acceptance(profile_id="no-inventory", ids=("timing",), generation=False)
    with pytest.raises(ValueError, match="generation inventory"):
        ComponentRequirementAllocation(
            component_id="timing", requirement_ids=("timing",), generation_acceptance=no_inventory,
        )


def test_legacy_empty_allocation_serialization_is_unchanged():
    final = _acceptance(profile_id="final", ids=("action", "timing", "audio"), generation=False)
    baseline = _qa_policy(domain=final)
    payload = baseline.model_dump(mode="json")
    assert "production_allocations" not in payload
    reopened = QaPolicy.model_validate(payload)
    assert reopened.model_dump(mode="json") == payload
    assert reopened.content_hash == baseline.content_hash


def test_explicit_revision_can_reallocate_and_old_lookup_fails():
    final = _acceptance(profile_id="final", ids=("action", "timing", "audio"), generation=False)
    original = _allocation(parent=final)
    old_policy = _qa_policy(domain=final, allocations=(original,))
    reallocated = original.model_copy(update={
        "allocation_id": "allocation-2",
        "assembly_requirement_ids": ("action", "timing", "audio"),
    })
    new_policy = seal_artifact(old_policy.model_copy(update={
        "revision": 2, "production_allocations": (reallocated,), "content_hash": "0" * 64,
    }))
    assert new_policy.content_hash != old_policy.content_hash
    with pytest.raises(ValueError, match="allocation"):
        new_policy.require_production_allocation(
            allocation_hash=original.allocation_hash,
            parent_shot_id="shot-1", parent_shot_content_hash=SHOT_HASH, task_id="task-1",
        )


def test_same_parent_can_keep_multiple_complete_production_alternatives():
    final = _acceptance(profile_id="final", ids=("action", "timing", "audio"), generation=False)
    first = _allocation(parent=final)
    second = first.model_copy(update={"allocation_id": "allocation-2"})

    policy = _qa_policy(domain=final, allocations=(first, second))
    assert {item.allocation_id for item in policy.production_allocations} == {
        "allocation-1", "allocation-2",
    }
