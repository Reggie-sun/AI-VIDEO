from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.domain_acceptance import (
    ComponentRequirementAllocation,
    DomainAcceptancePolicy,
    ProductionRequirementAllocation,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.generation_feedback import RegisteredGenerationTarget
from ai_video.planning.production_strategy import ProductionStrategyPolicy
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
    GenerationEvaluationAuthority,
    QaPolicyPointer,
)
from ai_video.production_planning import ProductionPlanningService
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
from ai_video.production.seedance_source_expression import (
    PreservedSourceExpression, SourceReferenceMaterial, SourceReferencePart,
    SourceTextPart, source_parts_sha256,
)
from ai_video.production.production_strategy_materialization import (
    build_materialized_strategy_composition,
    build_strategy_composition,
    prepare_strategy_commit,
)
from ai_video.production.production_strategy_reader import validate_production_lineage
from ai_video.production.production_strategy_composition import validate_strategy_composition_uses
from ai_video.production.source_use_evidence import SourceUseEvidence
from ai_video.planning.production_strategy import ProductionStrategyResolver
from ai_video.production.video_retime import VideoTimeMap, VideoTimePoint
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from production_project_factory import write_production_project
from production_strategy_factory import make_persisted_strategy_fixture


HASH = "a" * 64


def _generation_target() -> RegisteredGenerationTarget:
    class _Projection:
        def __init__(self, payload):
            self.payload = payload

        def model_dump(self, *, mode):
            return self.payload

    capabilities = _Projection({"variants": ({"capability_id": "fixture-generation"},)})
    provider = SimpleNamespace(capabilities=lambda: capabilities)
    return RegisteredGenerationTarget(
        provider, _Projection({}), _Projection({}), _Projection({}),
    )


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


def _preserved_expression(source_text: str) -> PreservedSourceExpression:
    materials = (
        SourceReferenceMaterial(
            asset_id="image-shot-1",
            asset_sha256="96a15fd15c5e013722daa2ad32490aa3cb89ea7b6d31c738577f56da55305a45",
            role="identity",
        ),
        SourceReferenceMaterial(
            asset_id="image-shot-2",
            asset_sha256="2814f96281d4a1f6c1837ae77161c30e514e53bb6b34ecb72b902f24709c3efa",
            role="scene",
        ),
    )
    parts = (
        SourceTextPart(text=source_text),
        SourceReferencePart(slot_id="ordered-reference", materials=materials),
        SourceTextPart(text="按原文结束并保留镜头限制。"),
    )
    return PreservedSourceExpression(
        source_sha256=source_parts_sha256(parts), parts=parts,
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
    parent_preserved_source_expression: PreservedSourceExpression | None = None,
    unit_preserved_source_expression: PreservedSourceExpression | None = None,
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
            preserved_source_expression=unit_preserved_source_expression,
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
        "preserved_source_expression": parent_preserved_source_expression,
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


def _with_selected_policy(loaded):
    policy = loaded.qa_policy
    payload = policy.model_dump_json().encode()
    relative_path = Path(f"state/reviews/policy.{policy.content_hash}.json")
    path = loaded.root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    pointer = QaPolicyPointer(
        path=relative_path,
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        content_hash=policy.content_hash,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    return loaded.model_copy(update={
        "manifest": loaded.manifest.model_copy(update={"active_qa_policy": pointer})
    })


def _loaded_with_mapped_video(tmp_path: Path, *, evidence_map: VideoTimeMap | None = None):
    loaded, _ = _loaded_with_intent(tmp_path, video_source_kind=AssetSourceKind.IMPORTED)
    parent = loaded.shots[0]
    old_unit = parent.production_intent.coverage_options[0].units[0]
    asset = loaded.registry.assets[0]
    time_map = VideoTimeMap(points=(
        VideoTimePoint(source_frame=0, output_frame=0),
        VideoTimePoint(source_frame=48, output_frame=72),
    ), audio_policy="mute")
    source = old_unit.source_options[0].model_copy(update={
        "duration": 48,
        "source_time_map": time_map,
    })
    unit = old_unit.model_copy(update={"source_options": (source,)})
    coverage = parent.production_intent.coverage_options[0].model_copy(update={"units": (unit,)})
    intent = parent.production_intent.model_copy(update={
        "allowed_operations": parent.production_intent.allowed_operations + (ProductionOperation.EDIT_EXISTING_VIDEO,),
        "coverage_options": (coverage,),
    })
    parent = seal_artifact(parent.model_copy(update={
        "content_hash": "0" * 64,
        "production_intent": intent,
    }))
    parent_reference = loaded.project.artifacts.shots[0].model_copy(update={
        "revision": parent.revision,
        "content_hash": parent.content_hash,
    })
    project = seal_artifact(loaded.project.model_copy(update={
        "revision": loaded.project.revision + 1,
        "content_hash": "0" * 64,
        "artifacts": loaded.project.artifacts.model_copy(update={"shots": (parent_reference,)}),
    }))
    acceptance = loaded.qa_policy.domain_acceptance
    allocation = loaded.qa_policy.production_allocations[0].model_copy(update={
        "parent_shot_content_hash": parent.content_hash,
    })
    qa = loaded.qa_policy
    evaluator = qa.semantic_authorities[0]
    evidence_map = time_map if evidence_map is None else evidence_map
    identity = {
        "parent_shot_content_hash": parent.content_hash,
        "task_id": intent.task_id,
        "acceptance_profile_hash": acceptance.profile_content_hash,
        "component_id": unit.component_id,
        "asset_id": asset.asset_id,
        "asset_sha256": asset.sha256,
        "size_bytes": asset.size_bytes,
        "role": source.role,
        "timebase": source.timebase,
        "start": source.start,
        "duration": source.duration,
        "evaluator": evaluator.model_dump(mode="json"),
        "proof": "technical",
    }
    evidence = SourceUseEvidence(
        **identity,
        evidence_id="mapped-source-pass",
        source_time_map=evidence_map,
        response_json=json.dumps({
            **identity,
            "source_time_map": evidence_map.model_dump(mode="json"),
            "observations": [{
                "requirement_id": "visual", "verdict": "PASS",
                "observation": "the retimed mapped source meets the allocated visual requirement",
            }],
        }),
    )
    qa = seal_artifact(qa.model_copy(update={
        "content_hash": "0" * 64,
        "production_allocations": (allocation,),
        "generation_evaluation_authorities": (
            GenerationEvaluationAuthority(evaluator=evaluator, proof="technical"),
        ),
        "production_source_evidence": (evidence,),
    }))
    return loaded.model_copy(update={
        "project": project,
        "shots": (parent,),
        "qa_policy": qa,
    }), time_map


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


def test_materialization_hands_explicit_preserved_source_to_generated_child(tmp_path):
    expression = _preserved_expression("At a glass partition, a courier pauses and lowers one hand.")
    loaded, decision = _loaded_with_intent(
        tmp_path, pending=True, unit_preserved_source_expression=expression,
    )

    request = prepare_strategy_commit(loaded=loaded, decision=decision, attempt_id="source-handoff")
    child = _materialized_loaded(loaded, request).shots[0]

    assert child.preserved_source_expression == expression
    assert child.preserved_source_expression.model_dump(mode="json") == expression.model_dump(mode="json")
    assert child.preserved_source_expression.parts[1].materials == expression.parts[1].materials


def test_materialization_does_not_inherit_parent_source_expression_without_unit_declaration(tmp_path):
    parent_expression = _preserved_expression("A rover crosses a workshop, stops, and turns toward a doorway.")
    loaded, decision = _loaded_with_intent(
        tmp_path, pending=True, parent_preserved_source_expression=parent_expression,
    )

    request = prepare_strategy_commit(loaded=loaded, decision=decision, attempt_id="no-source-inference")
    child = _materialized_loaded(loaded, request).shots[0]

    assert loaded.shots[0].preserved_source_expression == parent_expression
    assert decision.selected.units[0].component.preserved_source_expression is None
    assert child.preserved_source_expression is None


def test_source_backed_component_rejects_generation_only_preserved_source_expression(tmp_path):
    expression = _preserved_expression("At a glass partition, a courier pauses and lowers one hand.")
    loaded, decision = _loaded_with_intent(
        tmp_path, unit_preserved_source_expression=expression,
    )

    with pytest.raises(AiVideoError, match="only bind to generated production components"):
        prepare_strategy_commit(loaded=loaded, decision=decision, attempt_id="source-backed-expression")


@pytest.mark.parametrize(
    "source_text",
    (
        "At a glass partition, a courier pauses and lowers one hand.",
        "A rover crosses a workshop, stops, and turns toward a doorway.",
    ),
)
def test_explicit_preserved_source_survives_planning_committer_and_standard_reload(
    tmp_path, source_text,
):
    expression = _preserved_expression(source_text)
    fixture = make_persisted_strategy_fixture(
        tmp_path, generation_only=True,
        unit_preserved_source_expression=expression,
    )
    service = ProductionPlanningService(
        committer=fixture.committer,
        targets=(_generation_target(),),
        policy=ProductionStrategyPolicy(
            preference="generation", allow_generation_exploration=True,
        ),
    )

    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    assert decision.disposition == "selected"
    assert decision.selected.units[0].component.preserved_source_expression == expression

    service.materialize(decision=decision, attempt_id="preserved-source-roundtrip")
    reopened = load_production_project(tmp_path / "project.yaml")
    child = next(shot for shot in reopened.shots if shot.shot_id == fixture.child_shot_id)

    assert child.preserved_source_expression == expression
    assert child.preserved_source_expression.parts[0].text == source_text
    assert child.preserved_source_expression.parts[1].materials == expression.parts[1].materials


def test_mapped_edit_materializes_exact_map_and_reopens_through_composition(tmp_path):
    loaded, time_map = _loaded_with_mapped_video(tmp_path)
    loaded = _with_selected_policy(loaded)
    decision = ProductionStrategyResolver().resolve(loaded=loaded, parent_shot_id="shot-1")
    assert decision.disposition == "selected"
    assert decision.selected.units[0].operation is ProductionOperation.EDIT_EXISTING_VIDEO

    request = prepare_strategy_commit(loaded=loaded, decision=decision, attempt_id="mapped-edit")
    materialized = _materialized_loaded(loaded, request).model_copy(
        update={"production_parents": (loaded.shots[0],),
                "production_allocation_policies": (loaded.qa_policy,)}
    )
    validate_production_lineage(materialized)
    spec = build_strategy_composition(loaded=materialized, decision=decision)
    reopened_spec = build_materialized_strategy_composition(
        loaded=materialized, family_shot_id="shot-1-reuse-1"
    )

    assert spec.schema_version == "2.3"
    assert spec.layers[0].trim_duration_frames == 48
    assert spec.layers[0].source_time_map == time_map
    assert reopened_spec.shot_ids == spec.shot_ids
    assert reopened_spec.layers == spec.layers

    altered_layer = spec.layers[0].model_copy(update={"source_time_map": VideoTimeMap(
        points=(VideoTimePoint(source_frame=0, output_frame=0),
            VideoTimePoint(source_frame=48, output_frame=71)),
        audio_policy="mute",
    )})
    altered_spec = spec.model_copy(update={"layers": (altered_layer,)})
    with pytest.raises(AiVideoError, match="differs from approved production lineage"):
        validate_strategy_composition_uses(materialized, altered_spec)

    child = materialized.shots[0]
    changed_lineage = child.production_lineage.model_copy(update={
        "operation": ProductionOperation.EXISTING_ASSET_REUSE,
    })
    with pytest.raises(AiVideoError, match="exact authored time map"):
        validate_production_lineage(materialized.model_copy(update={
            "shots": (child.model_copy(update={"production_lineage": changed_lineage}),),
        }))


def test_mapped_edit_requires_evidence_for_the_exact_map(tmp_path):
    loaded, time_map = _loaded_with_mapped_video(tmp_path)
    stale_map = VideoTimeMap(points=(
        VideoTimePoint(source_frame=0, output_frame=0),
        VideoTimePoint(source_frame=48, output_frame=71),
    ), audio_policy="mute")
    qa = loaded.qa_policy
    old = qa.production_source_evidence[0]
    stale = SourceUseEvidence.model_validate({
        **old.model_dump(mode="json"),
        "source_time_map": stale_map.model_dump(mode="json"),
        "response_json": old.response_json.replace(
            json.dumps(time_map.model_dump(mode="json")),
            json.dumps(stale_map.model_dump(mode="json")),
        ),
    })
    qa = seal_artifact(qa.model_copy(update={
        "content_hash": "0" * 64,
        "production_source_evidence": (stale,),
    }))
    decision = ProductionStrategyResolver().resolve(
        loaded=loaded.model_copy(update={"qa_policy": qa}), parent_shot_id="shot-1"
    )

    assert decision.disposition == "evidence_required"
    assert decision.selected is None


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
    materialized = _materialized_loaded(loaded, request).model_copy(
        update={"production_parents": (loaded.shots[0],)}
    )

    with pytest.raises(AiVideoError) as error:
        build_strategy_composition(loaded=materialized, decision=decision)
    assert error.value.code is ErrorCode.COMPOSITION_INVALID

    with pytest.raises(AiVideoError, match="existing-source components") as reopened_error:
        build_materialized_strategy_composition(
            loaded=materialized, family_shot_id="shot-1-reuse-1"
        )
    assert reopened_error.value.code is ErrorCode.COMPOSITION_INVALID


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
