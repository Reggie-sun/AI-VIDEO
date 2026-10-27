"""Persisted salvage decision tests through the canonical Planning/QA seam."""

from dataclasses import replace
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from ai_video.planning.production_strategy import (
    ProductionCapabilities,
    ProductionStrategyPolicy,
)
from ai_video.production.domain_acceptance import (
    ComponentRequirementAllocation,
    GenerationEvaluationAuthority,
)
from ai_video.production.final_output_contracts import (
    FinalOutputContract,
    FinalOutputRequirement,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.production_strategy_contracts import ProductionOperation, ProductionUnit
from ai_video.production.production_strategy_salvage import candidate_plan_key
from ai_video.production.production_strategy_salvage import salvage_report
from ai_video.production.production_strategy_salvage_contracts import (
    CandidateRepairPlan,
    CandidateRisk,
    CostEstimate,
    FrameWindow,
    PlaybackEvidence,
    QualityDimension,
    SalvageOperation,
    SalvageReview,
    TakeAssessment,
    TakeDefect,
    TakeObservation,
)
from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import prepare_project_registry_commit
from ai_video.production._state_commit_common import _canonical_yaml_bytes
from ai_video.production._state_commit_contracts import PreparedArtifact
from ai_video.production.source_use_evidence import SourceUseEvidence
from ai_video.production_planning import ProductionPlanningService
from production_strategy_factory import (
    TECHNICAL,
    _generation_acceptance,
    make_persisted_strategy_fixture,
)


def _span(start: int, end: int) -> FrameWindow:
    return FrameWindow(start=start, end=end)


def _estimate(lower, upper, *, basis, unit):
    return CostEstimate(lower=Decimal(lower) if lower is not None else None,
                        upper=Decimal(upper) if upper is not None else None,
                        basis=basis, unit=unit)


def _rebind_source_evidence(evidence, parent_hash, *, source_start=None, source_duration=None):
    response = json.loads(evidence.response_json)
    response["parent_shot_content_hash"] = parent_hash
    updates = {"parent_shot_content_hash": parent_hash}
    if source_start is not None:
        response["start"] = source_start
        updates["start"] = source_start
    if source_duration is not None:
        response["duration"] = source_duration
        updates["duration"] = source_duration
    return SourceUseEvidence.model_validate({
        **evidence.model_dump(mode="json"),
        **updates,
        "response_json": json.dumps(response),
    })


def _add_salvage_authoring_contract(fixture, *, insert_coverage=False):
    """Add one existing assembly requirement through Project/QA owners."""
    loaded = load_production_project(fixture.root / "project.yaml")
    parent = loaded.shots[0]
    intent = parent.production_intent
    visual = intent.coverage_options[0].units[0].model_copy(update={
        "intent": "Use the approved source window or generate the authored visual",
    })
    units = (visual,)
    operations = (*intent.allowed_operations, ProductionOperation.GENERATE_FULL_SHOT)
    if insert_coverage:
        source = visual.source_options[0].model_copy(update={"duration": 60})
        visual = visual.model_copy(update={"duration_frames": 60, "source_options": (source,)})
        insert = ProductionUnit(
            component_id="visual-insert",
            shot_id="shot-salvage-insert",
            intent="补充动作结果镜头，明确原素材中未完成的必需动作",
            duration_frames=12,
            requirement_ids=("visual",),
            required_operations=(ProductionOperation.INSERT_SHOT,),
        )
        units = (visual, insert)
        operations = (*operations, ProductionOperation.SPLIT_SHOT, ProductionOperation.INSERT_SHOT)
    coverage = intent.coverage_options[0].model_copy(update={"units": units})
    intent = intent.model_copy(update={
        "allowed_operations": operations,
        "assembly_requirement_ids": ("visual",),
        "coverage_options": (coverage,),
    })
    parent = seal_artifact(parent.model_copy(update={
        "revision": parent.revision + 1,
        "content_hash": "0" * 64,
        "production_intent": intent,
    }))
    from ai_video.production.artifact_contracts import ArtifactReference

    reference = ArtifactReference(
        artifact_id=parent.artifact_id,
        revision=parent.revision,
        content_hash=parent.content_hash,
        path=Path(f"creative/shots/{parent.content_hash}.yaml"),
    )
    project = seal_artifact(loaded.project.model_copy(update={
        "revision": loaded.project.revision + 1,
        "content_hash": "0" * 64,
        "artifacts": loaded.project.artifacts.model_copy(update={
            "shots": (reference, *loaded.project.artifacts.shots[1:]),
        }),
    }))
    request = prepare_project_registry_commit(
        manifest=loaded.manifest,
        project=project,
        registry=loaded.registry,
        attempt_id="salvage-authoring",
    )
    payload = _canonical_yaml_bytes(parent)
    artifact = PreparedArtifact(
        relative_path=reference.path,
        payload=payload,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    request = replace(request, artifacts=tuple(sorted(
        (*request.artifacts, artifact), key=lambda item: item.relative_path.as_posix(),
    )))
    candidate_loaded = loaded.model_copy(update={
        "project": project,
        "shots": (parent, *loaded.shots[1:]),
    })
    request = prepare_strategy_dependency_transition(
        base_loaded=loaded,
        candidate_loaded=candidate_loaded,
        request=request,
    )
    fixture.committer.commit(request)

    current = load_production_project(fixture.root / "project.yaml")
    policy = current.qa_policy
    allocation = policy.production_allocations[0].model_copy(update={
        "parent_shot_content_hash": parent.content_hash,
        "assembly_requirement_ids": ("visual",),
    })
    components = (
        allocation.components[0].model_copy(update={"generation_acceptance": _generation_acceptance()}),
        *allocation.components[1:],
    )
    if insert_coverage:
        components = (*components, ComponentRequirementAllocation(
            component_id="visual-insert",
            requirement_ids=("visual",),
            generation_acceptance=_generation_acceptance(),
        ))
    allocation = allocation.model_copy(update={"components": components})
    source_evidence = tuple(
        _rebind_source_evidence(
            evidence,
            parent.content_hash,
            source_start=visual.source_options[0].start,
            source_duration=visual.source_options[0].duration,
        ) if insert_coverage and evidence.component_id == visual.component_id
        else _rebind_source_evidence(evidence, parent.content_hash)
        for evidence in policy.production_source_evidence
    )
    final_output = FinalOutputContract(
        goal_id="salvage-scene-goal",
        goal_version="1",
        user_goal="保留必需事件与有意停顿，验证修复后场景连续性",
        requirements=(
            FinalOutputRequirement(requirement_id="visual", observable="视觉事件及转场完整", proof="evaluator"),
            FinalOutputRequirement(requirement_id="dialogue", observable="原定对白与声音连续", proof="evaluator"),
        ),
    )
    policy = seal_artifact(policy.model_copy(update={
        "revision": policy.revision + 1,
        "content_hash": "0" * 64,
        "final_output": final_output,
        "production_allocations": (allocation,),
        "production_source_evidence": source_evidence,
        "generation_evaluation_authorities": (
            *policy.generation_evaluation_authorities,
            GenerationEvaluationAuthority(evaluator=TECHNICAL, proof="analyzer"),
            GenerationEvaluationAuthority(evaluator=TECHNICAL, proof="human"),
        ),
    }))
    fixture.committer.activate_qa_policy(
        policy,
        expected_manifest_revision=current.manifest.manifest_revision,
        attempt_id="salvage-assembly-policy",
    )
    return load_production_project(fixture.root / "project.yaml")


def _take_for(loaded, *, defect_kind="surface", defect_extent="local",
              defect_window=(80, 90), playback_mode="continuous_playback",
              playback_windows=None, audio_reviewed=True, omit_dimension=None,
              protected_hold=(40, 56)):
    parent = loaded.shots[0]
    source = parent.production_intent.coverage_options[0].units[0].source_options[0]
    asset = next(item for item in loaded.registry.assets if item.asset_id == source.asset_id)
    meta = asset.video_metadata
    bad_window = _span(*defect_window)
    dimensions = tuple(QualityDimension)
    observations = []
    for dimension in dimensions:
        if dimension is omit_dimension:
            continue
        requirement_id = "dialogue" if dimension is QualityDimension.PERFORMANCE_QUALITY else "visual"
        failed = dimension is QualityDimension.VISUAL_QUALITY or dimension in {
            QualityDimension.VISUAL_QUALITY,
            QualityDimension.ACTION_FIDELITY,
            QualityDimension.NARRATIVE_COMPLETENESS,
        } and defect_kind in {"action_completion", "causality", "narrative"}
        if defect_extent == "structural" and requirement_id == "visual":
            failed = True
        observations.append(TakeObservation(
            requirement_id=requirement_id,
            dimension=dimension,
            verdict="FAIL" if failed else "PASS",
            observation=("必需动作未完成" if failed else "连续播放观察符合此维度要求"),
            window=bad_window if failed else None,
        ))
    defect = TakeDefect(
        defect_id="salvage-defect-1",
        kind=defect_kind,
        severity="blocker" if defect_extent == "structural" else "major",
        extent=defect_extent,
        window=bad_window,
        requirement_ids=("visual",),
        observation="在标注时间窗发现缺陷；保留范围及成片影响需评估",
    )
    if defect_kind == "surface" and defect_extent == "local":
        defect_ids = (defect,)
    else:
        defect_ids = (defect,)
    playback = PlaybackEvidence(
        source_sha256=asset.sha256,
        size_bytes=asset.size_bytes,
        evaluator=TECHNICAL,
        proof="human",
        mode=playback_mode,
        reviewed_windows=(playback_windows or (_span(0, meta.frame_count),)),
        viewing_speed_milli=1000,
        audio_reviewed=audio_reviewed,
        evidence_sha256="e" * 64,
    )
    take = TakeAssessment(
        scene_id=parent.scene_id,
        shot_id=parent.shot_id,
        take_id="take-salvage-1",
        asset_id=asset.asset_id,
        asset_sha256=asset.sha256,
        size_bytes=asset.size_bytes,
        source_revision=asset.creation_receipt_id,
        total_frames=meta.frame_count,
        duration_seconds=Decimal(meta.duration_milliseconds) / Decimal(1000),
        playback=playback,
        usable_windows=(_span(0, meta.frame_count),),
        protected_windows=(_span(*protected_hold),) if protected_hold else (),
        removable_windows=(bad_window,) if bad_window.start >= 80 else (),
        observations=tuple(observations),
        defects=defect_ids,
        first_state="人物在门外，钥匙在右手",
        last_state="人物进入房间，钥匙仍在右手",
    )
    return take


def _plans_for(loaded, decision, take, *, override_operation=None, viability="feasible"):
    plans = []
    source_hashes = {take.playback.evidence_sha256}
    source_hashes.update(item.evidence_hash for item in loaded.qa_policy.production_source_evidence)
    for candidate in decision.candidates:
        generating = candidate.new_generation_count > 0
        if override_operation is not None:
            operations = (override_operation,)
        elif generating and len(candidate.units) > 1:
            operations = (SalvageOperation.REGENERATE, SalvageOperation.GENERATE_INSERT)
        elif generating:
            operations = (SalvageOperation.REGENERATE,)
        else:
            operations = (SalvageOperation.TRIM,)
        plans.append(CandidateRepairPlan(
            plan_key=candidate_plan_key(candidate),
            operations=operations,
            rationale=("仅移除缺陷范围并保留保护区" if not generating
                       else "替换失败视觉组件，保留其余已批准内容"),
            defect_ids=tuple(d.defect_id for d in take.defects),
            viability=viability,
            rejection_reasons=("observed action is missing" if viability == "infeasible" else "",)
                if viability == "infeasible" else (),
            evidence_sha256s=tuple(sorted(source_hashes)),
            provider_cost=(_estimate(None, None, basis="测试未封存 Provider 价格", unit="credits")
                           if generating else _estimate("0", "0", basis="纯本地素材编辑", unit="credits")),
            local_render_cost=_estimate("0", "0", basis="确定性本地 timeline render", unit="seconds"),
            elapsed_time=_estimate("1", "3", basis="fixture 操作工时范围", unit="minutes"),
            risks=CandidateRisk(
                narrative="low", identity="low", continuity="low", performance="low",
                approved_content="low", basis="保留视觉外全部已批准组件；完整成片仍待P6",
            ),
            affected_shot_ids=(decision.parent_shot_id,),
            adjacent_shot_ids=(),
            protected_requirement_ids=loaded.shots[0].production_intent.protected_requirement_ids,
        ))
    return tuple(plans)


def make_persisted_salvage_fixture(
    root,
    *,
    defect_kind="surface",
    defect_extent="local",
    defect_window=(80, 90),
    playback_mode="continuous_playback",
    playback_windows=None,
    audio_reviewed=True,
    omit_dimension=None,
    protected_hold=(40, 56),
    override_operation=None,
    plan_viability="feasible",
    preference="qualified_reuse",
    insert_coverage=False,
):
    """Create approved Project + QA + a current exact salvage review for reuse."""
    fixture = make_persisted_strategy_fixture(root)
    loaded = _add_salvage_authoring_contract(fixture, insert_coverage=insert_coverage)
    take = _take_for(loaded, defect_kind=defect_kind, defect_extent=defect_extent,
        defect_window=defect_window, playback_mode=playback_mode,
        playback_windows=playback_windows, audio_reviewed=audio_reviewed,
        omit_dimension=omit_dimension, protected_hold=protected_hold)
    service = ProductionPlanningService(committer=fixture.committer,
        policy=ProductionStrategyPolicy(preference=preference, allow_generation_exploration=True))
    service._capabilities = lambda: ProductionCapabilities(generation_available=True)
    candidate_source = service.prepare(parent_shot_id=fixture.parent_shot_id)
    plans = _plans_for(loaded, candidate_source, take,
        override_operation=override_operation, viability=plan_viability)
    review = SalvageReview(
        task_id=loaded.shots[0].production_intent.task_id,
        parent_shot_id=loaded.shots[0].shot_id,
        parent_shot_content_hash=loaded.shots[0].content_hash,
        acceptance_profile_hash=loaded.qa_policy.domain_acceptance.profile_content_hash,
        genre="suspense",
        scene_intent="延迟揭示与门后停顿构成必需情绪节奏",
        required_events=loaded.shots[0].production_intent.protected_requirement_ids,
        transition_requirement_ids=("visual",),
        scene_requirement_ids=("visual",),
        takes=(take,),
        candidate_plans=plans,
    )
    policy = seal_artifact(loaded.qa_policy.model_copy(update={
        "revision": loaded.qa_policy.revision + 1,
        "content_hash": "0" * 64,
        "production_salvage_reviews": (review,),
    }))
    fixture.committer.activate_qa_policy(
        policy,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="activate-salvage-review",
    )
    latest = load_production_project(root / "project.yaml")
    return fixture, service, latest, review, take, candidate_source


def test_qualified_trim_beats_generation_preference_and_keeps_protected_hold(tmp_path):
    fixture, service, loaded, review, take, _ = make_persisted_salvage_fixture(
        tmp_path, defect_window=(80, 90), preference="generation",
    )
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    assert decision.disposition == "selected"
    assert decision.selected.new_generation_count == 0
    source = decision.selected.units[0].source
    assert (source.asset_id, source.start, source.duration) == (take.asset_id, 4, 72)
    assert source.start <= take.protected_windows[0].start
    assert source.start + source.duration >= take.protected_windows[0].end
    assert "Evidence-qualified existing footage" in decision.reasons[0]
    assert loaded.qa_policy.production_salvage_reviews[0].review_hash == review.review_hash


def test_full_take_failure_outside_retained_window_can_be_trimmed(tmp_path):
    fixture, service, _, _, take, _ = make_persisted_salvage_fixture(tmp_path,
        defect_window=(80, 90))
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    assert decision.selected is not None
    assert decision.selected.new_generation_count == 0
    assert not any("retained_failed_requirement" in item for item in decision.selected.blockers)
    assert take.defects[0].window.start >= 80


def test_structural_missing_action_vetoes_trim_even_when_plan_claims_feasible(tmp_path):
    fixture, service, _, _, _, _ = make_persisted_salvage_fixture(
        tmp_path, defect_kind="action_completion", defect_extent="structural",
        defect_window=(20, 30), protected_hold=None,
    )
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    trim = next(c for c in decision.candidates if c.new_generation_count == 0)
    assert any("retained_defect" in blocker or "retained_failed_requirement" in blocker
               for blocker in trim.blockers)
    assert decision.selected is not trim
    assert decision.selected is not None and decision.selected.new_generation_count == 1


def test_structural_missing_action_can_use_authored_generate_insert_candidate(tmp_path):
    fixture, service, _, review, _, _ = make_persisted_salvage_fixture(
        tmp_path,
        defect_kind="action_completion",
        defect_extent="structural",
        defect_window=(20, 30),
        protected_hold=None,
        insert_coverage=True,
    )
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)

    assert decision.selected is not None
    assert decision.selected.new_generation_count == 2
    assert len(decision.selected.units) == 2
    assert ProductionOperation.INSERT_SHOT in decision.selected.operations
    assert all("salvage_infeasible:retained_defect" in candidate.blockers
               for candidate in decision.candidates if candidate.new_generation_count == 0)
    selected_plan = next(
        plan for plan in review.candidate_plans
        if plan.plan_key == candidate_plan_key(decision.selected)
    )
    assert set(selected_plan.operations) == {
        SalvageOperation.REGENERATE,
        SalvageOperation.GENERATE_INSERT,
    }
    assert selected_plan.provider_cost.lower is None
    assert selected_plan.provider_cost.upper is None
    assert service.prepare(parent_shot_id=fixture.parent_shot_id).selected == decision.selected


@pytest.mark.parametrize("change", [
    "partial_playback", "sampled_frames", "audio_unreviewed", "dimension_gap", "plan_unreviewed",
])
def test_incomplete_review_blocks_both_edit_and_generation_fallback(tmp_path, change):
    options = {}
    if change == "partial_playback":
        options.update(playback_windows=(_span(0, 60),))
    elif change == "sampled_frames":
        options.update(playback_mode="sampled_frames")
    elif change == "audio_unreviewed":
        options.update(audio_reviewed=False)
    else:
        if change == "dimension_gap":
            options.update(omit_dimension=QualityDimension.EDITABILITY)
        else:
            options.update(plan_viability="unreviewed")
    fixture, service, _, _, _, _ = make_persisted_salvage_fixture(tmp_path, **options)
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    assert decision.selected is None
    assert decision.disposition == "evidence_required"
    if change == "plan_unreviewed":
        assert "evidence_required:salvage_candidate_unreviewed" in decision.reasons
    else:
        assert any("salvage_unreviewed" in item for item in decision.reasons)


def test_source_identity_drift_blocks_salvage_and_generation(tmp_path):
    fixture, service, loaded, review, take, _ = make_persisted_salvage_fixture(tmp_path)
    stale_sha = "f" * 64
    stale_take = take.model_copy(update={
        "asset_sha256": stale_sha,
        "playback": take.playback.model_copy(update={"source_sha256": stale_sha}),
    })
    stale_review = review.model_copy(update={"takes": (stale_take,)})
    policy = seal_artifact(loaded.qa_policy.model_copy(update={
        "revision": loaded.qa_policy.revision + 1,
        "content_hash": "0" * 64,
        "production_salvage_reviews": (stale_review,),
    }))
    fixture.committer.activate_qa_policy(policy,
        expected_manifest_revision=loaded.manifest.manifest_revision, attempt_id="stale-source-review")
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    assert decision.selected is None
    assert any("salvage_source_identity" in item for item in decision.reasons)


def test_candidate_plan_key_drift_cannot_reuse_old_salvage_evidence(tmp_path):
    fixture, service, loaded, review, _, _ = make_persisted_salvage_fixture(tmp_path)
    plans = tuple(plan.model_copy(update={"plan_key": "f" * 63 + format(index, "x")})
                  for index, plan in enumerate(review.candidate_plans))
    changed = review.model_copy(update={"candidate_plans": plans})
    policy = seal_artifact(loaded.qa_policy.model_copy(update={
        "revision": loaded.qa_policy.revision + 1,
        "content_hash": "0" * 64,
        "production_salvage_reviews": (changed,),
    }))
    fixture.committer.activate_qa_policy(policy,
        expected_manifest_revision=loaded.manifest.manifest_revision, attempt_id="stale-plan-review")
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    assert decision.selected is None
    assert decision.disposition == "evidence_required"
    assert "evidence_required:salvage_candidate_unreviewed" in decision.reasons


def test_unsupported_v2v_plan_is_not_smuggled_as_local_edit(tmp_path):
    fixture, service, _, _, _, _ = make_persisted_salvage_fixture(
        tmp_path, override_operation=SalvageOperation.GENERATIVE_REPAIR,
    )
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    assert decision.selected is None
    assert any("generative_repair_requires_selected_edit_executor" in item for item in decision.reasons)


def test_canonical_materialization_and_composition_preserve_exact_source_window(tmp_path):
    fixture, service, loaded, _, take, _ = make_persisted_salvage_fixture(tmp_path)
    before_assets = {a.asset_id: a.sha256 for a in loaded.registry.assets}
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    assert decision.selected is not None and decision.selected.new_generation_count == 0
    service.materialize(decision=decision, attempt_id="salvage-edit-materialize")
    reopened = load_production_project(tmp_path / "project.yaml")
    spec, timeline = service.composition(decision=decision, renderer_version="hyperframes-test/1")
    visual = [span for span in timeline.visual_spans if span.asset_id == take.asset_id]
    assert spec.shot_ids == (fixture.child_shot_id,)
    assert [(span.trim_start_frame, span.duration_frames) for span in visual] == [(4, 72)]
    assert len(timeline.audio_spans) == 1
    assert len(timeline.caption_cues) == 2
    assert {a.asset_id: a.sha256 for a in reopened.registry.assets} == before_assets
    assert not any(attempt.video_generation_state for attempt in reopened.manifest.attempts)


def test_candidate_selector_never_reports_verified_from_plan_evidence(tmp_path):
    fixture, service, loaded, _, _, _ = make_persisted_salvage_fixture(tmp_path)
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    parent = loaded.shots[0]
    report = salvage_report(loaded, parent, decision)
    assert decision.selected is not None and decision.selected.new_generation_count == 0
    assert report["status"] == "EDIT_CANDIDATE"
    assert report["verification"] == "NOT_EVALUATED"
