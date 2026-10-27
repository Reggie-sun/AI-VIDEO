from decimal import Decimal

import pytest
from pydantic import ValidationError

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
from ai_video.production.artifact_contracts import ToolIdentity


SHA = "a" * 64
OTHER_SHA = "b" * 64
IDENTITY = ToolIdentity(name="reviewer", version="1")


def window(start=0, end=24):
    return FrameWindow(start=start, end=end)


def playback(**changes):
    values = {
        "source_sha256": SHA,
        "size_bytes": 1024,
        "evaluator": IDENTITY,
        "proof": "human",
        "mode": "continuous_playback",
        "reviewed_windows": (window(0, 48),),
        "viewing_speed_milli": 1000,
        "audio_reviewed": True,
        "evidence_sha256": OTHER_SHA,
    }
    values.update(changes)
    return PlaybackEvidence(**values)


def take(**changes):
    values = {
        "scene_id": "scene-1",
        "shot_id": "shot-1",
        "take_id": "take-1",
        "asset_id": "asset-1",
        "asset_sha256": SHA,
        "size_bytes": 1024,
        "source_revision": "revision-4",
        "total_frames": 48,
        "duration_seconds": Decimal("2"),
        "playback": playback(),
        "usable_windows": (window(0, 24), window(30, 48)),
        "protected_windows": (window(30, 48),),
        "removable_windows": (window(24, 30),),
        "observations": tuple(TakeObservation(
            requirement_id=("event-approach" if dimension is QualityDimension.VISUAL_QUALITY
                            else f"req-{dimension.value}"), dimension=dimension,
            verdict="UNREVIEWED", observation="尚未完成观察",
        ) for dimension in QualityDimension),
        "defects": (TakeDefect(
            defect_id="defect-1", kind="surface", severity="minor", extent="local",
            window=window(24, 30), requirement_ids=("event-approach",),
            observation="第24至30帧出现局部闪烁",
        ),),
        "first_state": "人物在门外，右手持钥匙",
        "last_state": "人物进入房间，钥匙仍在右手",
        "alternative_asset_ids": ("asset-old-take",),
    }
    values.update(changes)
    return TakeAssessment(**values)


def estimate(lower="0", upper="0", basis="本地受控测量", unit="seconds"):
    return CostEstimate(lower=Decimal(lower) if lower is not None else None,
                        upper=Decimal(upper) if upper is not None else None,
                        basis=basis, unit=unit)


def candidate(**changes):
    values = {
        "plan_key": SHA,
        "operations": (SalvageOperation.TRIM,),
        "rationale": "切除故障区间，保留事件与有意停顿",
        "defect_ids": ("defect-1",),
        "viability": "feasible",
        "rejection_reasons": (),
        "evidence_sha256s": (OTHER_SHA,),
        "provider_cost": estimate(),
        "local_render_cost": estimate("1", "2", "同设备本地渲染基准", "minutes"),
        "elapsed_time": estimate("1", "2", "剪辑操作估计", "minutes"),
        "risks": CandidateRisk(
            narrative="low", identity="low", continuity="low", performance="low",
            approved_content="low", basis="保留同一批准素材中的非缺陷区间",
        ),
        "affected_shot_ids": ("shot-1",),
        "adjacent_shot_ids": ("shot-2",),
        "protected_requirement_ids": ("req-action_fidelity",),
        "alternative_expression": None,
    }
    values.update(changes)
    return CandidateRepairPlan(**values)


def review(**changes):
    values = {
        "task_id": "task-1",
        "parent_shot_id": "shot-1",
        "parent_shot_content_hash": SHA,
        "acceptance_profile_hash": OTHER_SHA,
        "genre": "suspense",
        "scene_intent": "观众持续等待门后的揭示，停顿不可自动缩短",
        "required_events": ("event-approach",),
        "transition_requirement_ids": ("cut-1",),
        "scene_requirement_ids": ("scene-cause",),
        "takes": (take(),),
        "candidate_plans": (candidate(),),
    }
    values.update(changes)
    return SalvageReview(**values)


def test_frame_windows_use_half_open_frame_boundaries():
    full = window(0, 10)
    assert full.contains(window(2, 10))
    assert not full.contains(window(10, 11))
    assert not window(0, 4).overlaps(window(4, 8))
    assert window(0, 5).overlaps(window(4, 8))


@pytest.mark.parametrize("values", [
    {"start": 1, "end": 1},
    {"start": -1, "end": 2},
    {"start": True, "end": 2},
    {"start": 1.0, "end": 2},
])
def test_frame_window_rejects_empty_negative_and_coerced_frames(values):
    with pytest.raises(ValidationError):
        FrameWindow(**values)


def test_take_requires_exact_media_playback_identity_and_representable_dimensions():
    with pytest.raises(ValidationError, match="playback identity"):
        take(playback=playback(source_sha256=OTHER_SHA))
    assert len(take(observations=take().observations[:-1]).observations) == 6
    with pytest.raises(ValidationError, match="within the source"):
        take(usable_windows=(window(0, 49),))
    with pytest.raises(ValidationError, match="finite"):
        take(duration_seconds=Decimal("Infinity"))
    with pytest.raises(ValidationError):
        take(total_frames=True)
    assert take(duration_seconds=2).duration_seconds == Decimal("2")


def test_take_rejects_overlapping_windows_and_protected_removal_but_preserves_truth():
    with pytest.raises(ValidationError, match="ordered and disjoint"):
        take(usable_windows=(window(10, 30), window(20, 40)))
    with pytest.raises(ValidationError, match="protected and removable"):
        take(removable_windows=(window(30, 40),))
    assert take(usable_windows=()).usable_windows == ()
    assert take(protected_windows=(window(24, 28),), removable_windows=()).protected_windows == (window(24, 28),)
    assert take(removable_windows=(window(20, 24),), protected_windows=()).removable_windows == (window(20, 24),)


def test_unreviewed_evidence_and_observations_remain_representable():
    value = take(playback=playback(
        mode="continuous_playback", reviewed_windows=(window(0, 24),), audio_reviewed=False,
        viewing_speed_milli=1000,
    ))
    assert value.observations[0].verdict == "UNREVIEWED"
    assert value.playback.reviewed_windows == (window(0, 24),)
    assert review(takes=(value,), candidate_plans=()).review_hash


def test_cost_estimates_allow_explicit_unknown_but_reject_half_ranges_and_infinity():
    assert estimate(None, None, "缺少供应商最新计价", "credits").lower is None
    with pytest.raises(ValidationError, match="both bounds"):
        estimate("1", None)
    with pytest.raises(ValidationError, match="finite"):
        CostEstimate(lower=Decimal("Infinity"), upper=Decimal("Infinity"),
                     basis="invalid", unit="credits")
    with pytest.raises(ValidationError, match="lower cost"):
        estimate("2", "1")


def test_generation_candidate_requires_explicit_cost_and_feasible_evidence():
    with pytest.raises(ValidationError, match="provider_cost"):
        CandidateRepairPlan(**{k: v for k, v in candidate().model_dump().items()
                               if k != "provider_cost"})
    with pytest.raises(ValidationError, match="evidence"):
        candidate(evidence_sha256s=())
    with pytest.raises(ValidationError, match="SHA-256"):
        candidate(evidence_sha256s=("bad-hash",))
    with pytest.raises(ValidationError, match="rejection reason"):
        candidate(viability="infeasible", rejection_reasons=(), evidence_sha256s=())
    generated = candidate(operations=(SalvageOperation.GENERATIVE_REPAIR,),
                          provider_cost=estimate(None, None, "未封存费率", "credits"))
    assert generated.provider_cost.lower is None


def test_review_rejects_duplicate_take_plan_defect_and_unknown_references():
    with pytest.raises(ValidationError, match="take IDs"):
        review(takes=(take(), take(take_id="take-1", asset_id="asset-other")), candidate_plans=())
    with pytest.raises(ValidationError, match="plan keys"):
        review(candidate_plans=(candidate(), candidate(plan_key=SHA)))
    with pytest.raises(ValidationError, match="unknown defect"):
        review(candidate_plans=(candidate(defect_ids=("missing",)),))
    with pytest.raises(ValidationError, match="required event"):
        review(required_events=("missing-event",))


def test_scene_review_never_uses_candidate_viability_as_acceptance():
    value = review()
    assert value.candidate_plans[0].viability == "feasible"
    assert all(item.verdict == "UNREVIEWED" for item in value.takes[0].observations)
    assert value.review_hash == review().review_hash
