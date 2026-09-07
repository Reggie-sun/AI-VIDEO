"""Strict, read-only reopening of materialized production-strategy children."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.artifact_contracts import ArtifactReference
from ai_video.production.models import (
    AssetSourceKind,
    AssetType,
    LoadedProductionProject,
    ProductionManifest,
    ProductionProject,
    ProjectSnapshotPointer,
    Shot,
    VisualStrategy,
)
from ai_video.production.production_strategy_contracts import (
    ProductionComponentLineage,
    ProductionOperation,
    ProductionSourceOption,
)

if TYPE_CHECKING:
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _reference_identity(reference: ArtifactReference) -> tuple[str, int, str]:
    return (reference.artifact_id, reference.revision, reference.content_hash)


def _shot_identity(shot: Shot) -> tuple[str, int, str]:
    return (shot.artifact_id, shot.revision, shot.content_hash)


def _project_pointers(manifest: ProductionManifest) -> tuple[ProjectSnapshotPointer, ...]:
    """All immutable project snapshots retained by the canonical Manifest."""
    values: list[ProjectSnapshotPointer] = [manifest.active_project]
    for attempt in manifest.attempts:
        values.append(attempt.base_project)
        if attempt.candidate_project is not None:
            values.append(attempt.candidate_project)
    result: list[ProjectSnapshotPointer] = []
    seen: set[tuple[Path, int, str, str]] = set()
    for pointer in values:
        identity = (
            pointer.path,
            pointer.revision,
            pointer.content_hash,
            pointer.file_sha256,
        )
        if identity not in seen:
            result.append(pointer)
            seen.add(identity)
    return tuple(result)


def _load_origin_project(
    root: Path,
    pointer: ProjectSnapshotPointer,
) -> ProductionProject:
    """Load one Manifest-retained snapshot with its pointer identity verified."""
    # Kept as a local import so project.py can call this module while loading.
    from ai_video.production.project import (
        _load_yaml_artifact,
        _resolve_candidate_project_path,
        _verify_snapshot_file_hash,
    )

    path = _resolve_candidate_project_path(root, pointer.path)
    _verify_snapshot_file_hash(path, pointer.file_sha256, "production parent project")
    project = _load_yaml_artifact(path, ProductionProject)
    if (
        project.revision != pointer.revision
        or project.content_hash != pointer.content_hash
    ):
        raise _invalid("Production parent project snapshot identity is invalid.")
    return project


def _load_parent_from_origin(
    *,
    root: Path,
    origin: ProductionProject,
    lineage: ProductionComponentLineage,
) -> Shot | None:
    from ai_video.production.project import _load_referenced_artifact

    matches = [
        reference
        for reference in origin.artifacts.shots
        if reference == lineage.parent
    ]
    if not matches:
        return None
    if len(matches) != 1:
        raise _invalid("Production parent project repeats the lineage parent reference.")
    parent = _load_referenced_artifact(root, matches[0], Shot)
    if parent.production_lineage is not None:
        raise _invalid("Production strategy parents cannot themselves be strategy children.")
    if parent.shot_id != lineage.parent_shot_id:
        raise _invalid("Production lineage parent Shot identity is invalid.")
    if parent.production_intent is None:
        raise _invalid("Production lineage parent has no immutable production intent.")
    if parent.production_intent.task_id != lineage.task_id:
        raise _invalid("Production lineage task does not match its parent intent.")
    return parent


def load_production_parents(
    *,
    root: Path,
    manifest: ProductionManifest,
    project: ProductionProject,
    shots: tuple[Shot, ...],
) -> tuple[Shot, ...]:
    """Reopen every original parent through a Manifest-retained project snapshot.

    The current active project intentionally no longer references a replaced parent
    Shot.  This function does not trust a child-provided path alone: the exact
    parent reference must occur in a project snapshot whose verified content hash
    equals ``origin_project_hash``.
    """
    lineages = tuple(
        shot.production_lineage for shot in shots if shot.production_lineage is not None
    )
    if not lineages:
        return ()

    snapshots: dict[str, list[ProductionProject]] = defaultdict(list)
    for pointer in _project_pointers(manifest):
        if pointer.content_hash not in {item.origin_project_hash for item in lineages}:
            continue
        origin = _load_origin_project(root, pointer)
        snapshots[pointer.content_hash].append(origin)

    parents: dict[tuple[str, int, str], Shot] = {}
    for lineage in lineages:
        origins = snapshots.get(lineage.origin_project_hash, [])
        if not origins:
            raise _invalid("Production lineage origin project is not retained by the Manifest.")
        matches: dict[tuple[str, int, str], Shot] = {}
        for origin in origins:
            parent = _load_parent_from_origin(root=root, origin=origin, lineage=lineage)
            if parent is not None:
                matches[_shot_identity(parent)] = parent
        if len(matches) != 1:
            raise _invalid("Production lineage parent is absent or ambiguous in its origin project.")
        parents.update(matches)
    return tuple(parents[key] for key in sorted(parents))


def load_production_allocation_policies(root, shots):
    from ai_video.production.project import load_qa_policy

    pointers = {}
    for shot in shots:
        lineage = shot.production_lineage
        if lineage is None or lineage.allocation_policy is None:
            continue
        pointer = lineage.allocation_policy
        previous = pointers.setdefault(pointer.content_hash, pointer)
        if previous != pointer:
            raise _invalid("Production allocation pointers disagree on exact policy file identity.")
    return tuple(load_qa_policy(root, pointer) for pointer in pointers.values())


def _parent_for_lineage(
    bundle: LoadedProductionProject, lineage: ProductionComponentLineage
) -> Shot:
    matches = [
        parent for parent in bundle.production_parents
        if _shot_identity(parent) == _reference_identity(lineage.parent)
    ]
    if len(matches) != 1:
        raise _invalid("Production lineage parent was not strictly reopened.")
    parent = matches[0]
    if (
        parent.shot_id != lineage.parent_shot_id
        or parent.production_lineage is not None
        or parent.production_intent is None
        or parent.production_intent.task_id != lineage.task_id
    ):
        raise _invalid("Production lineage parent does not match its child.")
    return parent


def _coverage_unit(parent: Shot, lineage: ProductionComponentLineage):
    assert parent.production_intent is not None
    coverages = [
        coverage for coverage in parent.production_intent.coverage_options
        if coverage.coverage_id == lineage.coverage_id
    ]
    if len(coverages) != 1:
        raise _invalid("Production lineage coverage is not authorized by its parent intent.")
    coverage = coverages[0]
    units = [unit for unit in coverage.units if unit.component_id == lineage.component_id]
    if len(units) != 1:
        raise _invalid("Production lineage component is not authorized by its coverage.")
    return coverage, units[0]


def _required_role(child: Shot, source: ProductionSourceOption):
    matches = [role for role in child.required_asset_roles if role.role == source.role]
    if len(matches) != 1:
        raise _invalid("Production lineage source role is not bound by its child Shot.")
    return matches[0]


def _validate_source(
    *,
    bundle: LoadedProductionProject,
    child: Shot,
    parent: Shot,
    lineage: ProductionComponentLineage,
    unit,
) -> None:
    source = lineage.source
    if source is None:
        if (
            lineage.operation is not ProductionOperation.GENERATE_FULL_SHOT
            or unit.additional_sources
            or child.visual_strategy is not VisualStrategy.GENERATED_VIDEO
        ):
            raise _invalid("Production lineage has an invalid unbound generated component.")
        primary = [role for role in child.required_asset_roles if role.role == "primary_visual"]
        if len(primary) != 1 or primary[0].allowed_asset_types != (AssetType.VIDEO,):
            raise _invalid("Generated production component has no canonical primary-video role.")
        if primary[0].asset_ids:
            assets = {asset.asset_id: asset for asset in bundle.registry.assets}
            for asset_id in primary[0].asset_ids:
                asset = assets.get(asset_id)
                if (
                    asset is None
                    or asset.asset_type is not AssetType.VIDEO
                    or asset.source_kind is not AssetSourceKind.GENERATED
                ):
                    raise _invalid("Generated production component bound an invalid video asset.")
        if unit.first_frame_asset_id is not None:
            frame = [role for role in child.required_asset_roles if role.role == "first_frame"]
            assets = {asset.asset_id: asset for asset in bundle.registry.assets}
            if (
                len(frame) != 1
                or frame[0].asset_ids != (unit.first_frame_asset_id,)
                or frame[0].allowed_asset_types != (AssetType.IMAGE,)
                or assets.get(unit.first_frame_asset_id) is None
                or assets[unit.first_frame_asset_id].asset_type is not AssetType.IMAGE
            ):
                raise _invalid("Generated production component first-frame binding drifted.")
        return

    if source not in unit.source_options:
        raise _invalid("Production lineage source is not an authored component option.")
    assets = {asset.asset_id: asset for asset in bundle.registry.assets}
    asset = assets.get(source.asset_id)
    if asset is None or asset.sha256 != source.asset_sha256:
        raise _invalid("Production lineage source bytes no longer match the registry.")
    if (source.timebase == "still") != (asset.asset_type is AssetType.IMAGE):
        raise _invalid("Production lineage image source has an invalid timebase.")
    if (source.timebase == "frames") != (asset.asset_type is AssetType.VIDEO):
        raise _invalid("Production lineage video source has an invalid timebase.")
    role = _required_role(child, source)
    if source.asset_id not in role.asset_ids or asset.asset_type not in role.allowed_asset_types:
        raise _invalid("Production lineage source is not bound to the child role.")

    for additional in unit.additional_sources:
        extra_asset = assets.get(additional.asset_id)
        extra_role = _required_role(child, additional)
        if (
            extra_asset is None
            or extra_asset.sha256 != additional.asset_sha256
            or (additional.timebase == "still") != (extra_asset.asset_type is AssetType.IMAGE)
            or (additional.timebase == "frames") != (extra_asset.asset_type is AssetType.VIDEO)
            or additional.asset_id not in extra_role.asset_ids
            or extra_asset.asset_type not in extra_role.allowed_asset_types
        ):
            raise _invalid("Production lineage additional source is not bound exactly.")

    # P3 can compose several deterministic layers while the Shot's primary
    # strategy remains the source's concrete kind; HYBRID itself is not a P3
    # strategy.  Additional sources are bound above, not used as a second
    # strategy selector.
    if asset.asset_type is AssetType.IMAGE:
        if child.visual_strategy is not VisualStrategy.STATIC_IMAGE:
            raise _invalid("Still production component changed its visual strategy.")
    elif asset.source_kind is AssetSourceKind.IMPORTED:
        if child.visual_strategy is not VisualStrategy.EXISTING_VIDEO:
            raise _invalid("Imported-video production component changed its visual strategy.")
    elif asset.source_kind is AssetSourceKind.GENERATED:
        if child.visual_strategy is not VisualStrategy.GENERATED_VIDEO:
            raise _invalid("Generated-video production component changed its visual strategy.")
    else:
        raise _invalid("Production lineage source has unsupported provenance.")


def _validate_child(
    bundle: LoadedProductionProject,
    child: Shot,
    parent: Shot,
) -> tuple[object, object]:
    lineage = child.production_lineage
    assert lineage is not None
    coverage, unit = _coverage_unit(parent, lineage)
    intent = parent.production_intent
    assert intent is not None
    if (
        child.production_intent is not None
        or lineage.operation not in intent.allowed_operations
        or child.shot_id != unit.shot_id
        or child.intent != unit.intent
        or child.dialogue != unit.dialogue
        or child.narration != unit.narration
        or child.scene_id != parent.scene_id
        or child.storyboard_beat_id != parent.storyboard_beat_id
        or child.character_ids != parent.character_ids
        or child.continuity_constraints != parent.continuity_constraints
        or child.duration_policy.mode != "fixed"
        or child.duration_policy.seconds is None
        or _component_frames(child, bundle.project.delivery_profile.fps) != unit.duration_frames
    ):
        raise _invalid("Production strategy child drifted from its authorized component.")
    _validate_source(
        bundle=bundle, child=child, parent=parent, lineage=lineage, unit=unit
    )
    return coverage, unit


def _component_frames(child, fps):
    from ai_video.production.composition import _frames_for_fixed_seconds

    return _frames_for_fixed_seconds(child.duration_policy.seconds, fps)


def _validate_allocation(
    bundle: LoadedProductionProject,
    parent: Shot,
    lineage: ProductionComponentLineage,
    coverage,
    unit,
) -> None:
    policy = bundle.qa_policy
    if lineage.allocation_policy is not None:
        policy = next((p for p in bundle.production_allocation_policies
                       if p.content_hash == lineage.allocation_policy.content_hash), None)
        if policy is None:
            raise _invalid("Production historical allocation policy was not reopened.")
    if policy is None:
        return
    try:
        allocation = policy.require_production_allocation(
            allocation_hash=lineage.allocation_hash,
            parent_shot_id=parent.shot_id,
            parent_shot_content_hash=parent.content_hash,
            task_id=lineage.task_id,
        )
    except ValueError as exc:
        raise _invalid("Production strategy allocation is not current.", str(exc)) from exc
    intent = parent.production_intent
    assert intent is not None
    if (
        allocation.allocation_id != coverage.allocation_id
        or allocation.parent_requirement_ids != intent.protected_requirement_ids
        or allocation.assembly_requirement_ids != intent.assembly_requirement_ids
    ):
        raise _invalid("Production strategy allocation does not preserve parent obligations.")
    components = [item for item in allocation.components if item.component_id == unit.component_id]
    if len(components) != 1 or components[0].requirement_ids != unit.requirement_ids:
        raise _invalid("Production strategy component allocation is not exact.")


def _validate_coverage_groups(
    bundle: LoadedProductionProject,
    contexts: list[tuple[Shot, Shot, object, object]],
) -> None:
    groups: dict[tuple[str, int, str, str, str, str, str], list[tuple[Shot, Shot, object, object]]] = defaultdict(list)
    for child, parent, coverage, unit in contexts:
        lineage = child.production_lineage
        assert lineage is not None
        groups[(
            lineage.parent.artifact_id, lineage.parent.revision, lineage.parent.content_hash,
            lineage.task_id, lineage.coverage_id, lineage.allocation_hash, lineage.decision_hash,
        )].append((child, parent, coverage, unit))

    beat_order = {
        beat.beat_id: beat.shot_ids for beat in bundle.storyboard.beats
    }
    for children in groups.values():
        first_child, parent, coverage, _ = children[0]
        expected_units = coverage.units
        by_component = {
            child.production_lineage.component_id: child  # type: ignore[union-attr]
            for child, *_ in children
        }
        if len(by_component) != len(children) or tuple(by_component) != tuple(
            unit.component_id for unit in expected_units
        ):
            raise _invalid("Production strategy coverage dropped or duplicated a component.")
        expected_shots = tuple(unit.shot_id for unit in expected_units)
        actual_shots = tuple(by_component[unit.component_id].shot_id for unit in expected_units)
        if actual_shots != expected_shots:
            raise _invalid("Production strategy coverage child order is invalid.")
        beat_shots = beat_order.get(parent.storyboard_beat_id, ())
        positions = [beat_shots.index(shot_id) for shot_id in expected_shots if shot_id in beat_shots]
        if len(positions) != len(expected_shots) or positions != list(range(min(positions), min(positions) + len(positions))):
            raise _invalid("Production strategy coverage is not contiguous in its storyboard beat.")


def validate_production_lineage(bundle: LoadedProductionProject) -> None:
    """Validate immutable parent, allocation, component and source relationships."""
    contexts: list[tuple[Shot, Shot, object, object]] = []
    for child in bundle.shots:
        if child.production_lineage is None:
            continue
        parent = _parent_for_lineage(bundle, child.production_lineage)
        coverage, unit = _validate_child(bundle, child, parent)
        _validate_allocation(bundle, parent, child.production_lineage, coverage, unit)
        contexts.append((child, parent, coverage, unit))
    _validate_coverage_groups(bundle, contexts)


def selected_shot_generation_acceptance(
    loaded: LoadedProductionProject, shot_id: str
) -> "DomainAcceptancePolicy | None":
    """Return the current component rubric only after lineage is fully verified."""
    shots = [shot for shot in loaded.shots if shot.shot_id == shot_id]
    if len(shots) != 1:
        raise _invalid("Generation acceptance target Shot is not current.")
    shot = shots[0]
    policy = loaded.qa_policy
    if shot.production_lineage is None:
        return policy.selected_generation_acceptance() if policy is not None else None
    validate_production_lineage(loaded)
    if policy is None:
        raise _invalid("Production component generation acceptance requires a QA policy.")
    lineage = shot.production_lineage
    try:
        return policy.selected_component_generation_acceptance(
            allocation_hash=lineage.allocation_hash,
            component_id=lineage.component_id,
            parent_shot_id=lineage.parent_shot_id,
            parent_shot_content_hash=lineage.parent.content_hash,
            task_id=lineage.task_id,
        )
    except ValueError as exc:
        raise _invalid("Production component generation acceptance is not current.", str(exc)) from exc


def production_family_shot_ids(
    loaded: LoadedProductionProject, shot_id: str
) -> tuple[str, ...]:
    """Return the immutable root Shot and all units in the selected coverage."""
    shots = [shot for shot in loaded.shots if shot.shot_id == shot_id]
    if len(shots) != 1:
        raise _invalid("Production family target Shot is not current.")
    shot = shots[0]
    if shot.production_lineage is None:
        return (shot_id,)
    validate_production_lineage(loaded)
    lineage = shot.production_lineage
    parent = _parent_for_lineage(loaded, lineage)
    return tuple(dict.fromkeys((parent.shot_id, *(unit.shot_id
        for coverage in parent.production_intent.coverage_options for unit in coverage.units))))


def production_parent_context(bundle, shot_id):
    """Read the same approved root intent before or after materialization."""
    active = next((s for s in bundle.shots if s.shot_id == shot_id), None)
    if active is not None and active.production_intent is not None:
        reference = next(r for r in bundle.project.artifacts.shots if r.content_hash == active.content_hash)
        return active, (active.shot_id,), reference, bundle.project.content_hash
    root_id = active.production_lineage.parent_shot_id if active is not None and active.production_lineage else shot_id
    family = tuple(s for s in bundle.shots if s.production_lineage is not None
                   and s.production_lineage.parent_shot_id == root_id)
    if not family:
        raise _invalid("Production intent is not selected or retained by current components.")
    validate_production_lineage(bundle)
    lineage = family[0].production_lineage
    parent = _parent_for_lineage(bundle, lineage)
    return parent, tuple(s.shot_id for s in family), lineage.parent, lineage.origin_project_hash


def require_production_source_eligibility(
    bundle: LoadedProductionProject, spec=None, *, family_shot_id: str | None = None,
) -> None:
    """Current execution eligibility; historical reading never manufactures PASS."""
    from ai_video.production.source_use_evidence import assess_source_use

    family = production_family_shot_ids(bundle, family_shot_id) if family_shot_id is not None else None
    children = tuple(s for s in bundle.shots if s.production_lineage is not None
                     and (spec is None or s.shot_id in spec.shot_ids)
                     and (family is None or s.shot_id in family))
    if not children:
        return
    if (bundle.qa_policy is None or bundle.manifest.active_qa_policy is None
            or bundle.manifest.active_qa_policy.content_hash != bundle.qa_policy.content_hash):
        raise _invalid("Production execution requires a selected durable QA policy.")
    validate_production_lineage(bundle)
    if spec is not None:
        from ai_video.production.production_strategy_composition import validate_strategy_composition_uses

        validate_strategy_composition_uses(bundle, spec)
    assets = {a.asset_id: a for a in bundle.registry.assets}
    checked_audio = set()
    for child in children:
        lineage = child.production_lineage
        parent = _parent_for_lineage(bundle, lineage)
        coverage, unit = _coverage_unit(parent, lineage)
        try:
            bundle.qa_policy.require_production_allocation(allocation_hash=lineage.allocation_hash,
                parent_shot_id=parent.shot_id, parent_shot_content_hash=parent.content_hash,
                task_id=lineage.task_id)
        except ValueError as exc:
            raise _invalid("Current allocation requires production reassessment.", str(exc)) from exc
        uses = [(unit.component_id, s, s.requirement_ids or unit.requirement_ids)
                for s in ((lineage.source,) if lineage.source is not None else ()) + unit.additional_sources]
        if (parent.content_hash, coverage.coverage_id) not in checked_audio:
            uses.extend((a.component_id, a.source, a.requirement_ids) for a in coverage.audio)
            checked_audio.add((parent.content_hash, coverage.coverage_id))
        for component_id, source, requirements in uses:
            asset = assets.get(source.asset_id)
            if asset is None or asset.sha256 != source.asset_sha256:
                raise _invalid("Production source identity is no longer current.")
            try:
                verdict = assess_source_use(qa_policy=bundle.qa_policy,
                    parent_shot_content_hash=parent.content_hash, task_id=lineage.task_id,
                    component_id=component_id, asset_id=asset.asset_id, asset_sha256=asset.sha256,
                    size_bytes=asset.size_bytes, role=source.role, timebase=source.timebase,
                    start=source.start, duration=source.duration, requirement_ids=requirements,
                    evidence_ids=source.evidence_ids, transform=source.transform,
                    opacity_milli=source.opacity_milli, z_index=source.z_index)
            except ValueError as exc:
                raise _invalid("Production source-use evidence is invalid.", str(exc)) from exc
            if verdict != "PASS":
                raise _invalid("Production source use is not currently qualified: " + verdict)
