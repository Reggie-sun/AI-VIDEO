from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_video.production.domain_acceptance import (
    ComponentRequirementAllocation,
    DomainAcceptancePolicy,
    ProductionRequirementAllocation,
)
from ai_video.production.final_output_contracts import (
    FinalOutputContract,
    FinalOutputRequirement,
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


SHOT_HASH = "b" * 64


def _acceptance(
    profile_id: str,
    required_ids: tuple[str, ...],
    *,
    rows: tuple[dict, ...] = (),
) -> DomainAcceptancePolicy:
    payload = {
        "domain_id": "allocation-test",
        "profile_id": profile_id,
        "profile_version": "1",
        "measurement_contract_version": "test/1",
        "required_requirement_ids": required_ids,
        **({"generation_requirements": rows} if rows else {}),
    }
    digest = canonical_sha256(payload)
    return DomainAcceptancePolicy(
        domain_id="allocation-test",
        profile_id=profile_id,
        profile_version="1",
        profile_content_hash=digest,
        profile_payload={**payload, "content_hash": digest},
        measurement_contract_version="test/1",
        required_requirement_ids=required_ids,
    )


def _row(requirement_id: str, *, level="acceptance", stage="raw_generation") -> dict:
    return {
        "requirement_id": requirement_id,
        "level": level,
        "stage": stage,
        "dimension": "fixture",
        "observable": requirement_id,
        "tolerance": "exact",
        "measurement": "fixture",
        "proof": "technical",
        "intent_paths": (),
        "production_owner": "fixture",
    }


def _allocation(
    parent: DomainAcceptancePolicy,
    components: tuple[ComponentRequirementAllocation, ...],
    *,
    assembly: tuple[str, ...] = (),
) -> ProductionRequirementAllocation:
    return ProductionRequirementAllocation(
        allocation_id="allocation-1",
        parent_shot_id="shot-1",
        parent_shot_content_hash=SHOT_HASH,
        task_id="task-1",
        parent_acceptance_hash=parent.profile_content_hash,
        parent_requirement_ids=parent.required_requirement_ids,
        components=components,
        assembly_requirement_ids=assembly,
    )


def _final_output(*requirement_ids: str) -> FinalOutputContract:
    return FinalOutputContract(
        goal_id="final-goal",
        goal_version="1",
        user_goal="Deliver the authored result.",
        requirements=tuple(
            FinalOutputRequirement(
                requirement_id=requirement_id,
                observable=requirement_id,
                proof="human",
            )
            for requirement_id in requirement_ids
        ),
    )


def _qa_policy(
    parent: DomainAcceptancePolicy,
    allocation: ProductionRequirementAllocation,
    *,
    final_output: FinalOutputContract | None = None,
) -> QaPolicy:
    return seal_artifact(
        QaPolicy(
            artifact_id="allocation-policy",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id="allocation-policy",
            source_provenance=(SourceReference(kind="derived", reference="fixture"),),
            policy_id="allocation-policy",
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
            domain_acceptance=parent,
            final_output=final_output,
            production_allocations=(allocation,),
        )
    )


def test_complete_raw_and_assembly_responsibilities_are_accepted():
    from ai_video.production.domain_acceptance import production_allocation_issues

    parent = _acceptance(
        "parent",
        ("action", "editorial"),
        rows=(_row("action"), _row("editorial", stage="shot_editorial")),
    )
    raw = _acceptance("raw", ("action",), rows=(_row("action"),))
    allocation = _allocation(
        parent,
        (ComponentRequirementAllocation(
            component_id="plate-A",
            requirement_ids=("action",),
            generation_acceptance=raw,
        ),),
        assembly=("editorial",),
    )
    policy = _qa_policy(parent, allocation, final_output=_final_output("editorial"))

    assert production_allocation_issues(policy, allocation) == ()


def test_component_raw_rubric_must_cover_every_nonassembly_id():
    from ai_video.production.domain_acceptance import production_allocation_issues

    parent = _acceptance("parent", ("action", "timing"))
    raw = _acceptance("raw", ("action",), rows=(_row("action"),))
    allocation = _allocation(
        parent,
        (ComponentRequirementAllocation(
            component_id="plate-A",
            requirement_ids=("action", "timing"),
            generation_acceptance=raw,
        ),),
    )

    assert production_allocation_issues(_qa_policy(parent, allocation), allocation) == (
        "component_raw_required_missing:plate-A:timing",
    )


@pytest.mark.parametrize(
    "row, issue",
    [
        (_row("action", level="recipe_hint"), "component_rubric_not_raw:plate-A:action"),
        (_row("action", stage="final_composition"), "component_rubric_not_raw:plate-A:action"),
    ],
)
def test_component_required_id_cannot_be_hint_or_final_stage(row, issue):
    from ai_video.production.domain_acceptance import production_allocation_issues

    parent = _acceptance("parent", ("action",))
    rubric = _acceptance("raw", ("action",), rows=(row,))
    allocation = _allocation(
        parent,
        (ComponentRequirementAllocation(
            component_id="plate-A",
            requirement_ids=("action",),
            generation_acceptance=rubric,
        ),),
    )

    assert issue in production_allocation_issues(_qa_policy(parent, allocation), allocation)


def test_overlapping_raw_and_assembly_ownership_and_repeated_component_ids_are_valid():
    from ai_video.production.domain_acceptance import production_allocation_issues

    parent = _acceptance("parent", ("action",))
    raw = _acceptance("raw", ("action",), rows=(_row("action"),))
    allocation = _allocation(
        parent,
        (
            ComponentRequirementAllocation(
                component_id="plate-A",
                requirement_ids=("action",),
                generation_acceptance=raw,
            ),
            ComponentRequirementAllocation(
                component_id="plate-B",
                requirement_ids=("action",),
                generation_acceptance=raw,
            ),
        ),
        assembly=("action",),
    )

    assert production_allocation_issues(
        _qa_policy(parent, allocation, final_output=_final_output("action")), allocation
    ) == ()


def test_source_only_component_does_not_need_generation_acceptance():
    from ai_video.production.domain_acceptance import production_allocation_issues

    parent = _acceptance("parent", ("source-use",))
    allocation = _allocation(
        parent,
        (ComponentRequirementAllocation(
            component_id="imported-source",
            requirement_ids=("source-use",),
        ),),
    )

    assert production_allocation_issues(_qa_policy(parent, allocation), allocation) == ()


def test_source_only_allocation_tolerates_explicit_null_legacy_parent_inventory():
    from ai_video.production.domain_acceptance import production_allocation_issues

    parent = _acceptance("parent", ("source-use",))
    allocation = _allocation(
        parent,
        (ComponentRequirementAllocation(
            component_id="imported-source",
            requirement_ids=("source-use",),
        ),),
    )
    legacy_policy = SimpleNamespace(
        domain_acceptance=SimpleNamespace(
            profile_payload={"generation_requirements": None},
            required_requirement_ids=("source-use",),
        ),
        final_output=None,
    )

    assert production_allocation_issues(legacy_policy, allocation) == ()


def test_declared_hard_post_goal_must_be_assigned_to_assembly():
    from ai_video.production.domain_acceptance import production_allocation_issues

    parent = _acceptance(
        "parent",
        ("action", "editorial"),
        rows=(_row("action"), _row("editorial", stage="shot_editorial")),
    )
    allocation = _allocation(
        parent,
        (ComponentRequirementAllocation(
            component_id="source-only",
            requirement_ids=("action", "editorial"),
        ),),
    )

    assert "post_goal_not_in_assembly:editorial" in production_allocation_issues(
        _qa_policy(parent, allocation), allocation
    )


def test_legacy_incomplete_allocation_remains_readable_but_reports_new_use_blocker():
    from ai_video.production.domain_acceptance import production_allocation_issues
    from ai_video.production.models import QaPolicy as QaPolicyModel

    parent = _acceptance("parent", ("action", "timing"))
    raw = _acceptance("raw", ("action",), rows=(_row("action"),))
    allocation = _allocation(
        parent,
        (ComponentRequirementAllocation(
            component_id="plate-A",
            requirement_ids=("action", "timing"),
            generation_acceptance=raw,
        ),),
    )
    historical = _qa_policy(parent, allocation)
    reopened = QaPolicyModel.model_validate(historical.model_dump(mode="json"))

    assert reopened.model_dump(mode="json") == historical.model_dump(mode="json")
    assert reopened.content_hash == historical.content_hash
    assert "component_raw_required_missing:plate-A:timing" in production_allocation_issues(
        reopened, reopened.production_allocations[0]
    )


def _with_component_stage(policy: QaPolicy, stage: str) -> QaPolicy:
    allocation = policy.production_allocations[0]
    component = allocation.components[0]
    rubric = component.generation_acceptance
    assert rubric is not None
    payload = dict(rubric.profile_payload)
    rows = tuple({**dict(row), "stage": stage} for row in payload["generation_requirements"])
    payload.pop("content_hash", None)
    payload["generation_requirements"] = rows
    digest = canonical_sha256(payload)
    changed_rubric = DomainAcceptancePolicy.model_validate({
        **rubric.model_dump(mode="json"),
        "profile_content_hash": digest,
        "profile_payload": {**payload, "content_hash": digest},
    })
    changed_component = component.model_copy(update={"generation_acceptance": changed_rubric})
    changed_allocation = allocation.model_copy(update={"components": (changed_component, *allocation.components[1:])})
    return seal_artifact(policy.model_copy(update={
        "revision": policy.revision + 1,
        "content_hash": "0" * 64,
        "production_allocations": (changed_allocation, *policy.production_allocations[1:]),
    }))


def test_new_qa_publication_rejects_incomplete_raw_rubric_before_artifact_write(tmp_path):
    from ai_video.errors import AiVideoError
    from ai_video.production.paths import canonical_qa_policy_path
    from ai_video.production.project import load_production_project
    from production_strategy_factory import make_persisted_strategy_fixture

    fixture = make_persisted_strategy_fixture(tmp_path, generation_only=True)
    before = load_production_project(tmp_path / "project.yaml")
    invalid = _with_component_stage(before.qa_policy, "final_composition")
    path = canonical_qa_policy_path(invalid.content_hash)

    with pytest.raises(AiVideoError, match="responsibility admission"):
        fixture.committer.activate_qa_policy(
            invalid,
            expected_manifest_revision=before.manifest.manifest_revision,
            attempt_id="reject-incomplete-allocation",
        )

    after = load_production_project(tmp_path / "project.yaml")
    assert after.manifest == before.manifest
    assert after.manifest.attempts == before.manifest.attempts
    assert not (tmp_path / path).exists()


def test_current_strategy_planning_reports_allocation_responsibility_blocker_without_attempt(tmp_path):
    from ai_video.planning.production_strategy import (
        ProductionCapabilities,
        ProductionStrategyPolicy,
        ProductionStrategyResolver,
    )
    from ai_video.production.project import load_production_project
    from production_strategy_factory import make_persisted_strategy_fixture

    fixture = make_persisted_strategy_fixture(tmp_path, generation_only=True)
    loaded = load_production_project(tmp_path / "project.yaml")
    invalid = _with_component_stage(loaded.qa_policy, "final_composition")
    candidate = ProductionStrategyResolver().resolve(
        loaded=loaded.model_copy(update={"qa_policy": invalid}),
        parent_shot_id=fixture.parent_shot_id,
        policy=ProductionStrategyPolicy(allow_generation_exploration=True),
        capabilities=ProductionCapabilities(generation_available=True),
    )

    assert candidate.selected is None
    assert any(
        "allocation_responsibility:component_rubric_not_raw:visual-1:visual" in reason
        for reason in candidate.reasons
    )
    assert load_production_project(tmp_path / "project.yaml").manifest.attempts == loaded.manifest.attempts


def test_materialization_rechecks_the_selected_current_allocation(tmp_path):
    from ai_video.errors import AiVideoError, ErrorCode
    from ai_video.planning.production_strategy import (
        ProductionCapabilities,
        ProductionStrategyPolicy,
        ProductionStrategyResolver,
    )
    from ai_video.production.production_strategy_materialization import prepare_strategy_commit
    from production_strategy_factory import make_persisted_strategy_fixture

    fixture = make_persisted_strategy_fixture(tmp_path, generation_only=True)
    from ai_video.production.project import load_production_project

    loaded = load_production_project(fixture.root / "project.yaml")
    decision = ProductionStrategyResolver().resolve(
        loaded=loaded,
        parent_shot_id=fixture.parent_shot_id,
        policy=ProductionStrategyPolicy(allow_generation_exploration=True),
        capabilities=ProductionCapabilities(generation_available=True),
    )
    assert decision.selected is not None
    invalid = _with_component_stage(loaded.qa_policy, "final_composition")
    bad_candidate = decision.selected.model_copy(update={
        "allocation_hash": invalid.production_allocations[0].allocation_hash,
    })
    bad_decision = decision.model_copy(update={
        "selected": bad_candidate,
        "candidates": tuple(
            bad_candidate if item == decision.selected else item for item in decision.candidates
        ),
    })

    with pytest.raises(AiVideoError) as exc:
        prepare_strategy_commit(
            loaded=loaded.model_copy(update={"qa_policy": invalid}),
            decision=bad_decision,
            attempt_id="materialize-incomplete-allocation",
        )

    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def _incomplete_materialized_project(tmp_path):
    from ai_video.planning.production_strategy import (
        ProductionCapabilities,
        ProductionStrategyPolicy,
        ProductionStrategyResolver,
    )
    from ai_video.production.artifact_contracts import QaPolicyPointer
    from ai_video.production.production_strategy_materialization import prepare_strategy_commit
    from test_production_strategy_materialization import (
        _loaded_with_intent,
        _materialized_loaded,
        _with_selected_policy,
    )

    loaded, _ = _loaded_with_intent(tmp_path, pending=True)
    allocation = loaded.qa_policy.production_allocations[0]
    component = allocation.components[0].model_copy(update={
        "generation_acceptance": _acceptance("raw", ("visual",), rows=(_row("visual"),)),
    })
    allocation = allocation.model_copy(update={"components": (component,)})
    policy = seal_artifact(loaded.qa_policy.model_copy(update={
        "content_hash": "0" * 64,
        "production_allocations": (allocation,),
    }))
    loaded = _with_selected_policy(loaded.model_copy(update={"qa_policy": policy}))
    decision = ProductionStrategyResolver().resolve(
        loaded=loaded,
        parent_shot_id=loaded.shots[0].shot_id,
        policy=ProductionStrategyPolicy(allow_generation_exploration=True),
        capabilities=ProductionCapabilities(generation_available=True),
    )
    assert decision.selected is not None
    request = prepare_strategy_commit(loaded=loaded, decision=decision, attempt_id="materialize-fixture")
    materialized = _materialized_loaded(loaded, request).model_copy(update={
        "production_parents": loaded.shots,
        "production_allocation_policies": (policy,),
    })
    child = materialized.shots[0]
    invalid = _with_component_stage(policy, "final_composition")
    lineage = child.production_lineage.model_copy(update={
        "allocation_hash": invalid.production_allocations[0].allocation_hash,
        "allocation_policy": None,
    })
    child = seal_artifact(child.model_copy(update={
        "content_hash": "0" * 64,
        "production_lineage": lineage,
    }))
    refs = tuple(
        reference.model_copy(update={"content_hash": child.content_hash})
        if reference.artifact_id == child.artifact_id
        else reference
        for reference in materialized.project.artifacts.shots
    )
    project = seal_artifact(materialized.project.model_copy(update={
        "revision": materialized.project.revision + 1,
        "content_hash": "0" * 64,
        "artifacts": materialized.project.artifacts.model_copy(update={"shots": refs}),
    }))
    pointer = QaPolicyPointer(
        path=Path(f"state/reviews/policy.{invalid.content_hash}.json"),
        policy_id=invalid.policy_id,
        policy_version=invalid.policy_version,
        content_hash=invalid.content_hash,
        file_sha256="c" * 64,
    )
    return materialized.model_copy(update={
        "project": project,
        "shots": (child,),
        "production_parents": loaded.shots,
        "production_allocation_policies": (),
        "manifest": materialized.manifest.model_copy(update={"active_qa_policy": pointer}),
        "qa_policy": invalid,
    })


def test_current_generation_and_source_use_reject_historically_readable_incomplete_allocation(tmp_path):
    from ai_video.errors import AiVideoError, ErrorCode
    from ai_video.production.production_strategy_reader import (
        require_production_source_eligibility,
        selected_shot_generation_acceptance,
        validate_production_lineage,
    )

    loaded = _incomplete_materialized_project(tmp_path)
    shot_id = loaded.shots[0].shot_id
    attempts_before = loaded.manifest.attempts

    assert validate_production_lineage(loaded) is None
    with pytest.raises(AiVideoError) as generation_error:
        selected_shot_generation_acceptance(loaded, shot_id)
    assert generation_error.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert "component_rubric_not_raw:component-1:visual" in generation_error.value.technical_detail

    with pytest.raises(AiVideoError) as source_error:
        require_production_source_eligibility(loaded)
    assert source_error.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert "component_rubric_not_raw:component-1:visual" in source_error.value.technical_detail
    assert loaded.manifest.attempts == attempts_before
