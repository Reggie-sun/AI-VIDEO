"""Pure conversion of an already-selected production strategy into P2/P3 inputs."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from decimal import Decimal
from math import nextafter
from pathlib import Path

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._state_commit_common import (
    _canonical_yaml_bytes,
    prepare_project_registry_commit,
)
from ai_video.production._state_commit_contracts import PreparedArtifact, StateCommitRequest
from ai_video.production.artifact_contracts import ArtifactReference, SourceReference
from ai_video.production.composition_contracts import (
    CompositionLayerSpec,
    CompositionSpec,
    TransitionKind,
    TransitionSpec,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AssetRoleRequirement,
    AssetSourceKind,
    AssetType,
    HybridLayer,
    LoadedProductionProject,
    Shot,
    VisualStrategy,
)
from ai_video.production.production_strategy_contracts import (
    ProductionComponentLineage,
    ProductionCoverage,
    ProductionOperation,
    ProductionSelectedUnit,
    ProductionSourceOption,
    ProductionStrategyDecision,
)


def _project_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _composition_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.COMPOSITION_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _current_parent(loaded: LoadedProductionProject, decision: ProductionStrategyDecision) -> Shot:
    from ai_video.production.production_strategy_reader import production_parent_context

    parent, _, _, _ = production_parent_context(loaded, decision.parent_shot_id)
    if parent.content_hash != decision.parent_shot_content_hash:
        raise _project_invalid("Production strategy decision uses a stale parent Shot.")
    if parent.production_intent is None or parent.production_intent.task_id != decision.task_id:
        raise _project_invalid("Production strategy decision has no current parent intent.")
    return parent


def _selected_coverage(
    *,
    decision: ProductionStrategyDecision,
    coverage_options: tuple[ProductionCoverage, ...],
) -> tuple[ProductionCoverage, tuple[ProductionSelectedUnit, ...]]:
    selected = decision.selected
    if decision.disposition != "selected" or selected is None:
        raise _project_invalid("Production strategy decision is not selected.")
    if selected not in decision.candidates:
        raise _project_invalid("Production strategy selected candidate is not declared.")
    authored = [item for item in coverage_options if item.coverage_id == selected.coverage.coverage_id]
    if len(authored) != 1 or selected.coverage != authored[0]:
        raise _project_invalid("Production strategy selected coverage is not current authoring.")
    if tuple(item.component for item in selected.units) != authored[0].units:
        raise _project_invalid("Production strategy selected components differ from coverage authoring.")
    if not {item.operation for item in selected.units} <= set(selected.operations):
        raise _project_invalid("Production strategy selected operations are inconsistent.")
    return authored[0], selected.units


def _require_exact_parent_duration(
    *, parent: Shot, coverage: ProductionCoverage, fps: int
) -> None:
    if parent.duration_policy.mode != "fixed" or parent.duration_policy.seconds is None:
        raise _project_invalid("Production strategy parent Shot must have a fixed delivery duration.")
    expected = Decimal(str(parent.duration_policy.seconds)) * Decimal(fps)
    if expected != expected.to_integral_value() or expected <= 0:
        raise _project_invalid("Production strategy parent duration does not align to delivery frames.")
    if sum(item.duration_frames for item in coverage.units) != int(expected):
        raise _project_invalid("Production strategy coverage must preserve the parent delivery duration.")


def _require_current_allocation(
    *,
    loaded: LoadedProductionProject,
    decision: ProductionStrategyDecision,
    coverage: ProductionCoverage,
) -> object:
    policy = loaded.qa_policy
    if policy is None:
        raise _project_invalid("Production strategy materialization requires a QA policy.")
    try:
        allocation = policy.require_production_allocation(
            allocation_hash=decision.selected.allocation_hash,  # type: ignore[union-attr]
            parent_shot_id=decision.parent_shot_id,
            parent_shot_content_hash=decision.parent_shot_content_hash,
            task_id=decision.task_id,
        )
    except ValueError as exc:
        raise _project_invalid("Production strategy allocation is not current.", str(exc)) from exc
    if allocation.allocation_id != coverage.allocation_id:
        raise _project_invalid("Production strategy coverage does not use its selected allocation.")
    return allocation


def _parent_reference(loaded: LoadedProductionProject, parent: Shot) -> ArtifactReference:
    from ai_video.production.production_strategy_reader import production_parent_context

    return production_parent_context(loaded, parent.shot_id)[2]


def _seconds_for_frames(frames, fps):
    from ai_video.production.composition import _frames_for_fixed_seconds

    seconds = frames / fps
    if _frames_for_fixed_seconds(seconds, fps) != frames:
        seconds = nextafter(seconds, 0.0)
    return seconds


def _source_asset(loaded: LoadedProductionProject, source: ProductionSourceOption):
    asset = next((item for item in loaded.registry.assets if item.asset_id == source.asset_id), None)
    if asset is None or asset.sha256 != source.asset_sha256:
        raise _project_invalid("Production strategy source does not match the current registry.")
    if asset.asset_type is AssetType.IMAGE:
        if source.timebase != "still":
            raise _project_invalid("Image source use must use a still timebase.")
    elif asset.asset_type is AssetType.VIDEO:
        if source.timebase != "frames":
            raise _project_invalid("Video source use must use a frame timebase.")
    else:
        raise _project_invalid("Production strategy visual source has an unsupported asset type.")
    return asset


def _required_roles(
    loaded: LoadedProductionProject,
    primary: ProductionSourceOption | None,
    additional: tuple[ProductionSourceOption, ...],
    first_frame_asset_id: str | None,
) -> tuple[AssetRoleRequirement, ...]:
    if primary is None:
        if additional:
            raise _project_invalid("Pending generation cannot bind additional visual sources.")
        roles = [
            AssetRoleRequirement(
                role="primary_visual", asset_ids=(), allowed_asset_types=(AssetType.VIDEO,)
            )
        ]
        if first_frame_asset_id is not None:
            asset = next(
                (item for item in loaded.registry.assets if item.asset_id == first_frame_asset_id),
                None,
            )
            if asset is None or asset.asset_type is not AssetType.IMAGE:
                raise _project_invalid("Pending generation first frame must be a current image asset.")
            roles.append(
                AssetRoleRequirement(
                    role="first_frame", asset_ids=(asset.asset_id,), allowed_asset_types=(AssetType.IMAGE,)
                )
            )
        return tuple(roles)

    grouped: dict[str, tuple[AssetType, list[str]]] = {}
    for source in (primary, *additional):
        asset = _source_asset(loaded, source)
        existing = grouped.get(source.role)
        if existing is None:
            grouped[source.role] = (asset.asset_type, [asset.asset_id])
        elif existing[0] is not asset.asset_type:
            raise _project_invalid("Production strategy source role mixes asset types.")
        else:
            existing[1].append(asset.asset_id)
    return tuple(
        AssetRoleRequirement(role=role, asset_ids=tuple(asset_ids), allowed_asset_types=(asset_type,))
        for role, (asset_type, asset_ids) in grouped.items()
    )


def _visual_strategy(
    loaded: LoadedProductionProject,
    selected: ProductionSelectedUnit,
) -> tuple[VisualStrategy, tuple[HybridLayer, ...], str | None]:
    unit = selected.component
    primary = selected.source
    if primary is None:
        return VisualStrategy.GENERATED_VIDEO, (), f"Production strategy: {selected.operation.value}"
    asset = _source_asset(loaded, primary)
    if asset.asset_type is AssetType.IMAGE:
        return VisualStrategy.STATIC_IMAGE, (), None
    if asset.source_kind is AssetSourceKind.GENERATED:
        return VisualStrategy.GENERATED_VIDEO, (), f"Production strategy: {selected.operation.value}"
    if asset.source_kind is AssetSourceKind.IMPORTED:
        return VisualStrategy.EXISTING_VIDEO, (), None
    raise _project_invalid("Production strategy video source has an unsupported provenance kind.")


def _materialize_child(
    *,
    loaded: LoadedProductionProject,
    parent: Shot,
    parent_reference: ArtifactReference,
    coverage: ProductionCoverage,
    selected: ProductionSelectedUnit,
    decision: ProductionStrategyDecision,
) -> Shot:
    unit = selected.component
    if selected.operation not in parent.production_intent.allowed_operations:  # type: ignore[union-attr]
        raise _project_invalid("Production strategy operation is not authorized by the parent intent.")
    if selected.source is not None and selected.source not in unit.source_options:
        raise _project_invalid("Production strategy selected source is not an authored source option.")
    if selected.source is None and selected.operation is not ProductionOperation.GENERATE_FULL_SHOT:
        raise _project_invalid("Only full-shot generation may materialize a pending primary visual role.")

    visual_strategy, hybrid_layers, rationale = _visual_strategy(loaded, selected)
    roles = _required_roles(
        loaded, selected.source, unit.additional_sources, unit.first_frame_asset_id
    )
    previous = next((s for s in loaded.shots if s.shot_id == unit.shot_id), None)
    artifact_id, revision = (previous.artifact_id, previous.revision + 1) if previous else (unit.shot_id, 1)
    from ai_video.production.production_strategy_reader import production_parent_context
    lineage = ProductionComponentLineage(
        parent=parent_reference,
        origin_project_hash=production_parent_context(loaded, parent.shot_id)[3],
        parent_shot_id=parent.shot_id,
        task_id=decision.task_id,
        coverage_id=coverage.coverage_id,
        component_id=unit.component_id,
        allocation_hash=decision.selected.allocation_hash,  # type: ignore[union-attr]
        allocation_policy=loaded.manifest.active_qa_policy,
        decision_hash=decision.decision_hash,
        operation=selected.operation,
        source=selected.source,
    )
    return seal_artifact(Shot(
        artifact_id=artifact_id,
        revision=revision,
        content_hash="0" * 64,
        creation_receipt_id=decision.decision_hash,
        source_provenance=parent.source_provenance + (
            SourceReference(kind="derived", reference="production-strategy", content_hash=decision.decision_hash),
        ),
        shot_id=unit.shot_id,
        scene_id=parent.scene_id,
        storyboard_beat_id=parent.storyboard_beat_id,
        intent=unit.intent,
        dialogue=unit.dialogue,
        narration=unit.narration,
        duration_policy=parent.duration_policy.model_copy(update={
            "mode": "fixed", "seconds": _seconds_for_frames(unit.duration_frames, loaded.project.delivery_profile.fps),
            "minimum_seconds": None, "maximum_seconds": None,
        }),
        character_ids=parent.character_ids,
        continuity_constraints=parent.continuity_constraints,
        visual_strategy=visual_strategy,
        required_asset_roles=roles,
        generated_video_rationale=rationale,
        hybrid_layers=hybrid_layers,
        review_policy=parent.review_policy,
        production_lineage=lineage,
    ))


def _prepared_artifact(path: Path, model) -> PreparedArtifact:
    payload = _canonical_yaml_bytes(model)
    return PreparedArtifact(
        relative_path=path,
        payload=payload,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )


def prepare_strategy_commit(
    *, loaded: LoadedProductionProject, decision: ProductionStrategyDecision, attempt_id: str
) -> StateCommitRequest:
    """Build a P2 project/registry commit from one already-selected strategy."""
    parent = _current_parent(loaded, decision)
    coverage, selected_units = _selected_coverage(
        decision=decision, coverage_options=parent.production_intent.coverage_options  # type: ignore[union-attr]
    )
    _require_exact_parent_duration(
        parent=parent, coverage=coverage, fps=loaded.project.delivery_profile.fps
    )
    allocation = _require_current_allocation(loaded=loaded, decision=decision, coverage=coverage)
    allocation_component_ids = {item.component_id for item in allocation.components}
    if not {item.component.component_id for item in selected_units} <= allocation_component_ids:
        raise _project_invalid("Production strategy selected visual components are not allocated by QA.")
    parent_reference = _parent_reference(loaded, parent)
    from ai_video.production.production_strategy_reader import production_parent_context

    _, replaced_ids, _, _ = production_parent_context(loaded, parent.shot_id)
    children = tuple(
        _materialize_child(
            loaded=loaded,
            parent=parent,
            parent_reference=parent_reference,
            coverage=coverage,
            selected=selected,
            decision=decision,
        )
        for selected in selected_units
    )
    child_ids = tuple(item.shot_id for item in children)
    other_shot_ids = {item.shot_id for item in loaded.shots if item.shot_id not in replaced_ids}
    if len(set(child_ids)) != len(child_ids) or set(child_ids) & other_shot_ids:
        raise _project_invalid("Production strategy child Shot identities conflict with the current project.")

    beat_matches = [item for item in loaded.storyboard.beats if replaced_ids[0] in item.shot_ids]
    if len(beat_matches) != 1 or beat_matches[0].beat_id != parent.storyboard_beat_id:
        raise _project_invalid("Production strategy parent Shot is not in its current storyboard beat.")
    revised_beats = tuple(
        beat.model_copy(update={
            "shot_ids": tuple(child_id for shot_id in beat.shot_ids
                for child_id in (child_ids if shot_id == replaced_ids[0] else
                    () if shot_id in replaced_ids else (shot_id,))),
        })
        for beat in loaded.storyboard.beats
    )
    storyboard = seal_artifact(loaded.storyboard.model_copy(update={
        "revision": loaded.storyboard.revision + 1,
        "content_hash": "0" * 64,
        "creation_receipt_id": decision.decision_hash,
        "source_provenance": loaded.storyboard.source_provenance + (
            SourceReference(kind="derived", reference="production-strategy", content_hash=decision.decision_hash),
        ),
        "beats": revised_beats,
    }))
    child_refs = tuple(
        ArtifactReference(
            artifact_id=child.artifact_id,
            revision=child.revision,
            content_hash=child.content_hash,
            path=Path(f"creative/shots/{child.content_hash}.yaml"),
        )
        for child in children
    )
    previous_refs = loaded.project.artifacts.shots
    replaced_hashes = {s.content_hash for s in loaded.shots if s.shot_id in replaced_ids}
    revised_refs = tuple(
        reference
        for reference in previous_refs
        if reference.content_hash not in replaced_hashes
    )
    insertion_index = next(i for i, ref in enumerate(previous_refs) if ref.content_hash in replaced_hashes)
    refs = revised_refs[:insertion_index] + child_refs + revised_refs[insertion_index:]
    project = seal_artifact(loaded.project.model_copy(update={
        "revision": loaded.project.revision + 1,
        "content_hash": "0" * 64,
        "creation_receipt_id": decision.decision_hash,
        "source_provenance": loaded.project.source_provenance + (
            SourceReference(kind="derived", reference="production-strategy", content_hash=decision.decision_hash),
        ),
        "artifacts": loaded.project.artifacts.model_copy(update={
            "storyboard": ArtifactReference(
                artifact_id=storyboard.artifact_id,
                revision=storyboard.revision,
                content_hash=storyboard.content_hash,
                path=Path(f"creative/storyboards/{storyboard.content_hash}.yaml"),
            ),
            "shots": refs,
        }),
    }))
    base = prepare_project_registry_commit(
        manifest=loaded.manifest,
        project=project,
        registry=loaded.registry,
        attempt_id=attempt_id,
    )
    creative_artifacts = (
        _prepared_artifact(project.artifacts.storyboard.path, storyboard),
        *(_prepared_artifact(reference.path, child) for reference, child in zip(child_refs, children)),
    )
    request = replace(
        base,
        artifacts=tuple(sorted(
            (*base.artifacts, *creative_artifacts),
            key=lambda artifact: artifact.relative_path.as_posix(),
        )),
    )
    if loaded.dependency_graph is not None:
        from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition

        child_by_hash = {s.content_hash: s for s in children}
        untouched = {s.content_hash: s for s in loaded.shots if s.shot_id not in replaced_ids}
        candidate = loaded.model_copy(update={"project": project, "storyboard": storyboard,
            "shots": tuple(({**untouched, **child_by_hash})[r.content_hash] for r in refs),
            "production_parents": tuple({s.content_hash: s for s in (*loaded.production_parents, parent)}.values()),
        })
        request = prepare_strategy_dependency_transition(base_loaded=loaded,
            candidate_loaded=candidate, request=request)
    return request


def _materialized_coverage(
    *, loaded: LoadedProductionProject, decision: ProductionStrategyDecision
) -> tuple[ProductionCoverage, tuple[ProductionSelectedUnit, ...]]:
    coverage_options = tuple(
        item.production_lineage.coverage_id
        for item in loaded.shots
        if item.production_lineage is not None
        and item.production_lineage.parent_shot_id == decision.parent_shot_id
        and item.production_lineage.decision_hash == decision.decision_hash
    )
    coverage, selected_units = _selected_coverage(
        decision=decision,
        coverage_options=(decision.selected.coverage,),  # type: ignore[union-attr]
    )
    if not coverage_options or set(coverage_options) != {coverage.coverage_id}:
        raise _composition_invalid("Materialized production strategy children are not current.")
    _require_current_allocation(loaded=loaded, decision=decision, coverage=coverage)
    return coverage, selected_units


def build_strategy_composition(
    *,
    loaded: LoadedProductionProject,
    decision: ProductionStrategyDecision,
    composition_id: str = "production-strategy",
) -> CompositionSpec:
    """Build P3 inputs for already materialized, completed visual components."""
    coverage, selected_units = _materialized_coverage(loaded=loaded, decision=decision)
    shots_by_id = {item.shot_id: item for item in loaded.shots}
    layers: list[CompositionLayerSpec] = []
    for selected in selected_units:
        unit = selected.component
        child = shots_by_id.get(unit.shot_id)
        if child is None or child.production_lineage is None:
            raise _composition_invalid("Materialized production strategy child Shot is missing.")
        lineage = child.production_lineage
        if (
            lineage.parent_shot_id != decision.parent_shot_id
            or lineage.parent.content_hash != decision.parent_shot_content_hash
            or lineage.task_id != decision.task_id
            or lineage.coverage_id != coverage.coverage_id
            or lineage.component_id != unit.component_id
            or lineage.allocation_hash != decision.selected.allocation_hash  # type: ignore[union-attr]
            or lineage.decision_hash != decision.decision_hash
            or lineage.operation != selected.operation
            or lineage.source != selected.source
        ):
            raise _composition_invalid("Materialized production strategy lineage does not match the decision.")
        source = selected.source
        if source is None:
            role = next((r for r in child.required_asset_roles if r.role == "primary_visual"), None)
            if role is None or len(role.asset_ids) != 1:
                raise _composition_invalid("Pending generated visual components cannot be composed.")
            asset = next(a for a in loaded.registry.assets if a.asset_id == role.asset_ids[0])
            source = ProductionSourceOption(asset_id=asset.asset_id, asset_sha256=asset.sha256,
                role=role.role, timebase="frames", duration=unit.duration_frames,
                requirement_ids=unit.requirement_ids)
        asset = _source_asset(loaded, source)
        role = next((item for item in child.required_asset_roles if item.role == source.role), None)
        if role is None or source.asset_id not in role.asset_ids or asset.asset_type not in role.allowed_asset_types:
            raise _composition_invalid("Materialized production source is not bound to its child Shot role.")
        if child.visual_strategy in {VisualStrategy.GENERATED_VIDEO, VisualStrategy.EXISTING_VIDEO}:
            if asset.asset_type is not AssetType.VIDEO:
                raise _composition_invalid("Materialized production video component lacks a canonical video asset.")
        elif child.visual_strategy is VisualStrategy.STATIC_IMAGE:
            if asset.asset_type is not AssetType.IMAGE:
                raise _composition_invalid("Materialized production still component lacks a canonical image asset.")
        else:
            raise _composition_invalid("Materialized production visual strategy cannot be composed.")
        for index, use in enumerate((source, *unit.additional_sources)):
            use_asset = _source_asset(loaded, use)
            if use_asset.asset_type != asset.asset_type:
                raise _composition_invalid("Mixed raster/video composition requires a separate graphic contract.")
            layers.append(CompositionLayerSpec(
                layer_id=f"{unit.shot_id}:{use.role}:{index}", shot_id=unit.shot_id,
                asset_role=use.role, asset_id=use.asset_id, trim_start_frame=use.start,
                trim_duration_frames=use.duration if use.timebase == "frames" else None,
                transform=use.transform, opacity_milli=use.opacity_milli, z_index=use.z_index,
            ))
    shot_ids = tuple(item.component.shot_id for item in selected_units)
    transitions = tuple(
        TransitionSpec(from_shot_id=left, to_shot_id=right, kind=TransitionKind.CUT, duration_frames=0)
        for left, right in zip(shot_ids, shot_ids[1:])
    )
    return seal_artifact(CompositionSpec(
        artifact_id=f"composition-{composition_id}",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id=decision.decision_hash,
        source_provenance=(
            SourceReference(kind="derived", reference="production-strategy", content_hash=decision.decision_hash),
        ),
        schema_version="2.1",
        composition_id=composition_id,
        shot_ids=shot_ids,
        layers=tuple(layers),
        transitions=transitions,
        delivery_profile=loaded.project.delivery_profile,
        audio_tracks=coverage.audio and tuple(item.track for item in coverage.audio) or (),
        caption_tracks=coverage.captions,
    ))
