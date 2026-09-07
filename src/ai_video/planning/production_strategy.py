"""Pure production-means selection over canonical authoring and use evidence.

No Provider, filesystem, writer, renderer or generation recipe is invoked here.
Generation candidates remain proposals for the existing generation owners.
"""

from itertools import product
from decimal import Decimal
from math import prod
from typing import Literal

from pydantic import Field

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import AssetType, CompositionLayerSpec, FixedTransform
from ai_video.production.production_strategy_contracts import (
    ProductionCandidate, ProductionOperation as Op, ProductionSelectedUnit,
    ProductionStrategyDecision,
)
from ai_video.production.source_use_evidence import assess_source_use
from ai_video.production.visual_media import resolved_video_trim_duration


class ProductionStrategyPolicy(StrictModel):
    version: Literal["production-strategy/1"] = "production-strategy/1"
    preference: Literal["qualified_reuse", "generation", "unresolved"] = "qualified_reuse"
    allow_generation_exploration: bool = False
    max_candidates: int = Field(default=128, strict=True, gt=0, le=1024)


class ProductionCapabilities(StrictModel):
    """Observed generation availability; deterministic operations are code-owned."""

    generation_available: bool = False
    generation_targets_hash: str = Field(default="0" * 64, pattern=r"^[0-9a-f]{64}$")


# These are operations actually expressible by current Shot/P3/P4 contracts.
# Masking, tracking, arbitrary motion, dubbing and extension have no executor.
_SUPPORTED = frozenset({Op.GENERATE_FULL_SHOT, Op.EXISTING_ASSET_REUSE,
    Op.SPLIT_SHOT, Op.CUTAWAY, Op.REACTION_SHOT, Op.INSERT_SHOT,
    Op.REFRAME, Op.TRIM_EXISTING, Op.REPLACE_AUDIO,
    Op.COMPOSITE_MULTIPLE_ASSETS, Op.SIMPLIFY_ACTION})


def _source_blockers(loaded, parent, component_id, source, requirement_ids):
    asset = next((a for a in loaded.registry.assets if a.asset_id == source.asset_id), None)
    if asset is None or asset.sha256 != source.asset_sha256:
        return ("evidence_required:source_identity",)
    blockers = []
    if source.timebase == "frames":
        if asset.asset_type != AssetType.VIDEO:
            blockers.append("capability_gap:video_type")
        else:
            try:
                resolved_video_trim_duration(asset, CompositionLayerSpec(
                    layer_id="source-use",
                    shot_id="qualification", asset_id=asset.asset_id, asset_role=source.role,
                    trim_start_frame=source.start, trim_duration_frames=source.duration,
                ), duration_frames=source.duration, delivery_profile=loaded.project.delivery_profile)
            except ValueError:
                blockers.append("capability_gap:video_window")
    elif source.timebase == "still":
        if asset.asset_type != AssetType.IMAGE or source.start != 0:
            blockers.append("capability_gap:still_source")
    else:
        meta = asset.audio_metadata
        if (meta is None or meta.sample_rate_hz != 48000
                or source.start + source.duration > meta.duration_samples):
            blockers.append("capability_gap:audio_window")
    try:
        verdict = assess_source_use(qa_policy=loaded.qa_policy,
            parent_shot_content_hash=parent.content_hash, task_id=parent.production_intent.task_id,
            component_id=component_id, asset_id=asset.asset_id, asset_sha256=asset.sha256,
            size_bytes=asset.size_bytes, role=source.role, timebase=source.timebase,
            start=source.start, duration=source.duration, requirement_ids=requirement_ids,
            evidence_ids=source.evidence_ids, transform=source.transform,
            opacity_milli=source.opacity_milli, z_index=source.z_index)
    except ValueError:
        verdict = "NOT_EVALUATED"
    if verdict != "PASS":
        blockers.append("evidence_required:source_" + verdict.lower())
    return tuple(blockers)


def _unit_options(unit):
    options = []
    for source in unit.source_options:
        operation = Op.TRIM_EXISTING if source.start else Op.EXISTING_ASSET_REUSE
        options.append(ProductionSelectedUnit(component=unit, operation=operation, source=source))
    options.append(ProductionSelectedUnit(component=unit, operation=Op.GENERATE_FULL_SHOT))
    return tuple(options)


def _candidate(loaded, parent, coverage, selected_units, policy, capabilities):
    intent = parent.production_intent
    allocation = next((a for a in loaded.qa_policy.production_allocations
        if a.allocation_id == coverage.allocation_id), None) if loaded.qa_policy else None
    blockers = []
    operations = set()
    generation_count = sum(u.source is None for u in selected_units)
    if allocation is None:
        blockers.append("needs_authoring_revision:allocation_missing")
    elif (allocation.parent_shot_id != parent.shot_id
            or allocation.parent_shot_content_hash != parent.content_hash
            or allocation.task_id != intent.task_id
            or set(allocation.parent_requirement_ids) != set(intent.protected_requirement_ids)
            or set(allocation.assembly_requirement_ids) != set(intent.assembly_requirement_ids)):
        blockers.append("needs_authoring_revision:allocation_identity")
    else:
        actual = {c.component_id: set(c.requirement_ids) for c in allocation.components}
        expected = {c.component_id: set(c.requirement_ids) for c in (*coverage.units, *coverage.audio)}
        if actual != expected:
            blockers.append("needs_authoring_revision:requirement_coverage")
    if (parent.duration_policy.mode != "fixed" or parent.duration_policy.seconds is None
            or sum(u.duration_frames for u in coverage.units) !=
            Decimal(str(parent.duration_policy.seconds)) * loaded.project.delivery_profile.fps):
        blockers.append("needs_authoring_revision:duration")
    if len(coverage.units) > 1:
        operations.add(Op.SPLIT_SHOT)
        if intent.single_take or intent.co_visible_required:
            blockers.append("blocked_scope:indivisible_intent")
    active_ids = {s.shot_id for s in loaded.shots if s.production_lineage is None
                  or s.production_lineage.parent_shot_id != parent.shot_id}
    if any(u.shot_id in active_ids for u in coverage.units):
        blockers.append("needs_authoring_revision:child_identity_collision")
    for selected in selected_units:
        unit, source = selected.component, selected.source
        operations.add(selected.operation)
        operations.update(unit.required_operations)
        if source is None:
            if not policy.allow_generation_exploration:
                blockers.append("blocked_scope:generation_exploration_disabled")
            if not capabilities.generation_available:
                blockers.append("capability_gap:generation_unavailable")
            component = next((c for c in allocation.components if c.component_id == unit.component_id), None) if allocation else None
            if component is None or component.generation_acceptance is None:
                blockers.append("needs_authoring_revision:component_generation_acceptance")
            if unit.additional_sources:
                blockers.append("capability_gap:pending_generation_layers")
        else:
            if unit.motion_required and source.timebase == "still":
                blockers.append("capability_gap:still_cannot_supply_motion")
            primary_ids = source.requirement_ids or unit.requirement_ids
            blockers.extend(_source_blockers(loaded, parent, unit.component_id, source, primary_ids))
            supplied = set(primary_ids)
            for extra in unit.additional_sources:
                supplied.update(extra.requirement_ids)
            if supplied != set(unit.requirement_ids):
                blockers.append("needs_authoring_revision:source_requirement_coverage")
        sources = ((*unit.additional_sources, source) if source else unit.additional_sources)
        if unit.additional_sources:
            operations.add(Op.COMPOSITE_MULTIPLE_ASSETS)
            types = {a.asset_type for a in loaded.registry.assets
                     if a.asset_id in {s.asset_id for s in sources}}
            if len(types) > 1:
                blockers.append("capability_gap:mixed_raster_video_layers")
            if len({s.z_index for s in sources}) != len(sources):
                blockers.append("needs_authoring_revision:duplicate_layer_depth")
        for extra in unit.additional_sources:
            blockers.extend(_source_blockers(loaded, parent, unit.component_id, extra, extra.requirement_ids))
        for item in sources:
            if item.transform != FixedTransform():
                operations.add(Op.REFRAME)
            if item.start:
                operations.add(Op.TRIM_EXISTING)
    if coverage.audio:
        operations.add(Op.REPLACE_AUDIO)
    for audio in coverage.audio:
        blockers.extend(_source_blockers(loaded, parent, audio.component_id, audio.source, audio.requirement_ids))
    for operation in sorted(operations, key=lambda op: op.value):
        if operation not in intent.allowed_operations:
            blockers.append("blocked_scope:" + operation.value)
        if operation not in _SUPPORTED:
            blockers.append("capability_gap:" + operation.value)
    return ProductionCandidate(coverage=coverage,
        allocation_hash=allocation.allocation_hash if allocation else "0" * 64,
        units=selected_units, operations=tuple(sorted(operations, key=lambda op: op.value)),
        blockers=tuple(dict.fromkeys(blockers)), new_generation_count=generation_count)


class ProductionStrategyResolver:
    """Enumerate production alternatives before any generation routing."""

    def resolve(self, *, loaded, parent_shot_id, policy=None, capabilities=None):
        policy = policy or ProductionStrategyPolicy()
        capabilities = capabilities or ProductionCapabilities()
        from ai_video.production.production_strategy_reader import production_parent_context

        parent, _, _, _ = production_parent_context(loaded, parent_shot_id)
        intent = parent.production_intent
        input_hash = canonical_sha256({
            "project": loaded.project.content_hash, "registry": loaded.registry.content_hash,
            "manifest": loaded.manifest.model_dump(mode="json"), "parent": parent.content_hash,
            "qa": loaded.qa_policy.content_hash if loaded.qa_policy else None,
            "policy": policy.model_dump(mode="json"), "capabilities": capabilities.model_dump(mode="json"),
        })
        common = dict(input_hash=input_hash, parent_shot_id=parent.shot_id,
            parent_shot_content_hash=parent.content_hash, task_id=intent.task_id)
        # Global unresolved lifecycle blocks planning changes as well as submit.
        if any(a.status.value in {"outcome_unknown", "interrupted"} for a in loaded.manifest.attempts):
            return ProductionStrategyDecision(**common, candidates=(), disposition="recovery_required",
                reasons=("canonical attempt requires explicit recovery",))
        combinations = sum(prod(len(_unit_options(u)) for u in c.units) for c in intent.coverage_options)
        if combinations > policy.max_candidates:
            return ProductionStrategyDecision(**common, candidates=(), disposition="unresolved_choice",
                reasons=("candidate bound exceeded; narrow authored alternatives",))
        candidates = tuple(_candidate(loaded, parent, coverage, units, policy, capabilities)
            for coverage in intent.coverage_options
            for units in product(*(_unit_options(u) for u in coverage.units)))
        feasible = tuple(c for c in candidates if not c.blockers)
        if feasible:
            if policy.preference == "qualified_reuse":
                score = min(c.new_generation_count for c in feasible)
                preferred = tuple(c for c in feasible if c.new_generation_count == score)
            elif policy.preference == "generation":
                score = max(c.new_generation_count for c in feasible)
                preferred = tuple(c for c in feasible if c.new_generation_count == score)
            else:
                preferred = feasible
            if len(preferred) == 1:
                return ProductionStrategyDecision(**common, candidates=candidates,
                    selected=preferred[0], disposition="selected")
            return ProductionStrategyDecision(**common, candidates=candidates,
                disposition="unresolved_choice", reasons=("equally preferred production alternatives",))
        reasons = tuple(dict.fromkeys(b for c in candidates for b in c.blockers))
        # Report the feasible alternative's evidence gap before unavailable fallbacks.
        evidence_only = any(c.blockers and all(b.startswith("evidence_required:") for b in c.blockers)
                            for c in candidates)
        disposition = "evidence_required" if evidence_only else (
            "needs_authoring_revision" if any(b.startswith("needs_authoring_revision:") for b in reasons)
            else "capability_gap" if any(b.startswith("capability_gap:") for b in reasons) else "blocked_scope")
        return ProductionStrategyDecision(**common, candidates=candidates,
            disposition=disposition, reasons=reasons)
