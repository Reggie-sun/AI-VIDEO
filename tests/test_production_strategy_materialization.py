from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.domain_acceptance import (
    ComponentRequirementAllocation,
    DomainAcceptancePolicy,
    ProductionRequirementAllocation,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    ArtifactReference,
    AssetSourceKind,
    AssetType,
    ProductionProject,
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    SourceReference,
    Storyboard,
    ToolIdentity,
    VideoAssetMetadata,
)
from ai_video.production.production_strategy_contracts import (
    ProductionCandidate,
    ProductionCoverage,
    ProductionIntent,
    ProductionOperation,
    ProductionSelectedUnit,
    ProductionSourceOption,
    ProductionStrategyDecision,
    ProductionUnit,
)
from ai_video.production.production_strategy_materialization import (
    build_strategy_composition,
    prepare_strategy_commit,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from production_project_factory import write_production_project


HASH = "a" * 64


def _acceptance() -> DomainAcceptancePolicy:
    required = ("visual",)
    payload = {
        "domain_id": "test",
        "profile_id": "strategy-final",
        "profile_version": "1",
        "measurement_contract_version": "test/1",
        "required_requirement_ids": required,
        "source_use_requirements": tuple({"requirement_id": i, "proof": "technical", "stage": "source_use"} for i in required),
    }
    digest = canonical_sha256(payload)
    return DomainAcceptancePolicy(
        domain_id="test", profile_id="strategy-final", profile_version="1",
        profile_content_hash=digest, profile_payload={**payload, "content_hash": digest},
        measurement_contract_version="test/1", required_requirement_ids=required,
    )


def _qa_policy(acceptance: DomainAcceptancePolicy, allocation: ProductionRequirementAllocation) -> QaPolicy:
    tool = ToolIdentity(name="fixture-reviewer", version="1")
    return seal_artifact(QaPolicy(
        artifact_id="strategy-policy", revision=1, content_hash="0" * 64,
        creation_receipt_id="strategy-policy",
        source_provenance=(SourceReference(kind="derived", reference="fixture"),),
        policy_id="strategy-policy", policy_version="1",
        required_layers=(QaLayer.SEMANTIC,),
        technical_thresholds=QaTechnicalThresholds(
            black_luma_max_milli=10, silence_peak_max_millidb=-60_000,
            clipping_peak_min_millidb=-100,
        ),
        layout_rules=QaLayoutRules(safe_area_inset_milli=50, caption_overflow_tolerance_milli=0),
        strategy_rules_version="1", semantic_requirement="required",
        semantic_authorities=(tool,), domain_acceptance=acceptance,
        production_allocations=(allocation,),
    ))


def _loaded_with_intent(
    tmp_path: Path,
    *,
    pending: bool = False,
    video_source_kind: AssetSourceKind | None = None,
    split: bool = False,
    split_frames: tuple[int, ...] = (24, 48),
):
    loaded = load_production_project(write_production_project(tmp_path))
    parent = loaded.shots[0]
    asset = loaded.registry.assets[0]
    if video_source_kind is not None:
        asset = asset.model_copy(update={
            "asset_type": AssetType.VIDEO,
            "sha256": "d" * 64,
            "size_bytes": 4096,
            "mime_type": "video/mp4",
            "duration_seconds": 3.0,
            "width": 1280,
            "height": 720,
            "source_kind": video_source_kind,
            "video_metadata": VideoAssetMetadata(
                container_name="mp4", codec_name="h264", width=1280, height=720,
                fps_numerator=24, fps_denominator=1, duration_milliseconds=3000,
                frame_count=72, probe_receipt_id="probe", request_receipt_fingerprint="e" * 64,
                resolved_generation_hash="f" * 64, provenance_receipt_id="provenance",
            ),
        })
        registry = loaded.registry.model_copy(update={"assets": (asset,)})
        registry_hash = registry_semantic_sha256(registry)
        loaded = loaded.model_copy(update={
            "registry": registry.model_copy(update={"revision_id": registry_hash, "content_hash": registry_hash}),
        })
    source = None if pending else ProductionSourceOption(
        asset_id=asset.asset_id, asset_sha256=asset.sha256, role="primary_visual",
        timebase="frames" if asset.asset_type is AssetType.VIDEO else "still",
        duration=72, requirement_ids=("visual",),
    )
    durations = split_frames if split else (72,)
    units = tuple(
        ProductionUnit(
            component_id=f"component-{index}", shot_id=f"shot-1-reuse-{index}",
            intent="Hold on the hero.", duration_frames=duration,
            requirement_ids=("visual",),
            source_options=() if source is None else (source.model_copy(update={"duration": duration}),),
        )
        for index, duration in enumerate(durations, start=1)
    )
    coverage = ProductionCoverage(coverage_id="coverage-1", allocation_id="allocation-1", units=units)
    intent = ProductionIntent(
        task_id="task-1", allowed_operations=(
            ProductionOperation.EXISTING_ASSET_REUSE, ProductionOperation.GENERATE_FULL_SHOT,
        ), protected_requirement_ids=("visual",), coverage_options=(coverage,),
    )
    parent = seal_artifact(parent.model_copy(update={
        "revision": 2, "content_hash": "0" * 64, "production_intent": intent,
    }))
    parent_ref = ArtifactReference(
        artifact_id=parent.artifact_id, revision=parent.revision, content_hash=parent.content_hash,
        path=Path("creative/shots/shot-1.yaml"),
    )
    project = seal_artifact(loaded.project.model_copy(update={
        "revision": 2, "content_hash": "0" * 64,
        "artifacts": loaded.project.artifacts.model_copy(update={"shots": (parent_ref,)}),
    }))
    acceptance = _acceptance()
    allocation = ProductionRequirementAllocation(
        allocation_id="allocation-1", parent_shot_id=parent.shot_id,
        parent_shot_content_hash=parent.content_hash, task_id="task-1",
        parent_acceptance_hash=acceptance.profile_content_hash,
        parent_requirement_ids=("visual",),
        components=tuple(
            ComponentRequirementAllocation(component_id=unit.component_id, requirement_ids=("visual",))
            for unit in units
        ),
    )
    policy = _qa_policy(acceptance, allocation)
    loaded = loaded.model_copy(update={"project": project, "shots": (parent,), "qa_policy": policy})
    operation = ProductionOperation.GENERATE_FULL_SHOT if pending else ProductionOperation.EXISTING_ASSET_REUSE
    selected_units = tuple(
        ProductionSelectedUnit(
            component=unit,
            operation=operation,
            source=None if source is None else unit.source_options[0],
        )
        for unit in units
    )
    candidate = ProductionCandidate(
        coverage=coverage, allocation_hash=allocation.allocation_hash,
        units=selected_units, operations=tuple(operation for _ in selected_units), new_generation_count=int(pending),
    )
    decision = ProductionStrategyDecision(
        input_hash=HASH, parent_shot_id=parent.shot_id, parent_shot_content_hash=parent.content_hash,
        task_id="task-1", candidates=(candidate,), selected=candidate, disposition="selected",
    )
    return loaded, decision


def _materialized_loaded(loaded, request):
    payloads = {artifact.relative_path: artifact.payload for artifact in request.artifacts}
    project_payload = next(payload for path, payload in payloads.items() if path.as_posix().startswith("state/projects/"))
    project = ProductionProject.model_validate(yaml.safe_load(project_payload))
    storyboard_ref = project.artifacts.storyboard
    storyboard = Storyboard.model_validate(yaml.safe_load(payloads[storyboard_ref.path]))
    shots = tuple(
        __import__("ai_video.production.models", fromlist=["Shot"]).Shot.model_validate(
            yaml.safe_load(payloads[reference.path])
        )
        for reference in project.artifacts.shots
    )
    return loaded.model_copy(update={"project": project, "storyboard": storyboard, "shots": shots})


def test_materializes_exact_selected_coverage_with_content_addressed_children(tmp_path):
    loaded, decision = _loaded_with_intent(tmp_path)
    request = prepare_strategy_commit(loaded=loaded, decision=decision, attempt_id="strategy-1")
    materialized = _materialized_loaded(loaded, request)

    assert request.expected_manifest_revision == loaded.manifest.manifest_revision
    assert tuple(shot.shot_id for shot in materialized.shots) == ("shot-1-reuse-1",)
    child = materialized.shots[0]
    assert child.production_intent is None
    assert child.production_lineage.parent.content_hash == decision.parent_shot_content_hash
    assert child.required_asset_roles[0].allowed_asset_types[0].value == "image"
    assert child.required_asset_roles[0].asset_ids == (loaded.registry.assets[0].asset_id,)
    assert materialized.project.artifacts.shots[0].path == Path(f"creative/shots/{child.content_hash}.yaml")
    assert materialized.storyboard.beats[0].shot_ids == ("shot-1-reuse-1",)

    spec = build_strategy_composition(loaded=materialized, decision=decision)
    assert spec.schema_version == "2.1"
    assert spec.shot_ids == ("shot-1-reuse-1",)
    assert spec.layers[0].asset_id == loaded.registry.assets[0].asset_id
    assert spec.transitions == ()


def test_non_integral_second_split_roundtrips_exact_canonical_frames(tmp_path):
    from ai_video.production.composition import _frames_for_fixed_seconds
    from ai_video.production.production_strategy_reader import validate_production_lineage

    loaded, decision = _loaded_with_intent(tmp_path, split=True, split_frames=(25, 47))
    request = prepare_strategy_commit(loaded=loaded, decision=decision, attempt_id="fractional-cut")
    materialized = _materialized_loaded(loaded, request).model_copy(update={
        "production_parents": loaded.shots,
    })
    validate_production_lineage(materialized)
    assert tuple(_frames_for_fixed_seconds(s.duration_policy.seconds, 24)
                 for s in materialized.shots) == (25, 47)


def test_rejects_old_or_tampered_selected_coverage(tmp_path):
    loaded, decision = _loaded_with_intent(tmp_path)
    old = decision.model_copy(update={"parent_shot_content_hash": HASH})
    with pytest.raises(AiVideoError) as old_error:
        prepare_strategy_commit(loaded=loaded, decision=old, attempt_id="strategy-1")
    assert old_error.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID

    replacement = decision.selected.model_copy(update={"coverage": decision.selected.coverage.model_copy(update={"coverage_id": "other"})})
    tampered = decision.model_copy(update={"selected": replacement})
    with pytest.raises(AiVideoError) as tampered_error:
        prepare_strategy_commit(loaded=loaded, decision=tampered, attempt_id="strategy-1")
    assert tampered_error.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_pending_generation_cannot_be_composed_as_an_illegal_bound_role(tmp_path):
    loaded, decision = _loaded_with_intent(tmp_path, pending=True)
    request = prepare_strategy_commit(loaded=loaded, decision=decision, attempt_id="strategy-1")
    materialized = _materialized_loaded(loaded, request)

    with pytest.raises(AiVideoError) as error:
        build_strategy_composition(loaded=materialized, decision=decision)
    assert error.value.code is ErrorCode.COMPOSITION_INVALID


def test_allowed_split_preserves_ordered_duration_and_exact_parent_references(tmp_path):
    loaded, decision = _loaded_with_intent(tmp_path, split=True)
    request = prepare_strategy_commit(loaded=loaded, decision=decision, attempt_id="strategy-1")
    materialized = _materialized_loaded(loaded, request)

    assert tuple(shot.shot_id for shot in materialized.shots) == ("shot-1-reuse-1", "shot-1-reuse-2")
    assert tuple(shot.duration_policy.seconds for shot in materialized.shots) == (1.0, 2.0)
    assert materialized.storyboard.beats[0].shot_ids == ("shot-1-reuse-1", "shot-1-reuse-2")
    assert {shot.production_lineage.parent.content_hash for shot in materialized.shots} == {
        decision.parent_shot_content_hash,
    }


@pytest.mark.parametrize(
    ("source_kind", "strategy"),
    ((AssetSourceKind.GENERATED, "generated_video"), (AssetSourceKind.IMPORTED, "existing_video")),
)
def test_materialization_preserves_video_source_provenance(tmp_path, source_kind, strategy):
    loaded, decision = _loaded_with_intent(tmp_path, video_source_kind=source_kind)
    request = prepare_strategy_commit(loaded=loaded, decision=decision, attempt_id="strategy-1")
    materialized = _materialized_loaded(loaded, request)

    assert materialized.shots[0].visual_strategy.value == strategy
    assert materialized.shots[0].required_asset_roles[0].allowed_asset_types == (AssetType.VIDEO,)
