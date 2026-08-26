from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from ai_video.production.ad_creative_types import (
    AdCompositionRequirements,
    AdShotProposal,
    CompiledAdCreativeHandoff,
)
from ai_video.production.commercial_execution import (
    CommercialExecutionDisposition,
    CommercialExecutionProjection,
    CommercialShotClass,
)
from ai_video.production.ecommerce_ad_coordinator import (
    ActivatedCommercialShotCheckpoint,
    EcommerceShotNextAction,
    EcommerceStopReason,
    run_ecommerce_ad_generation,
    run_ecommerce_ad_production,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import QaVerdict
from ai_video.production.state_commit import ProductionStateCommitter
from production_project_factory import make_composition_spec


def _projection(shot_id: str, *, invoke: bool) -> CommercialExecutionProjection:
    primary_class = (
        CommercialShotClass.CHARACTER_PERFORMANCE
        if invoke
        else CommercialShotClass.END_CARD
    )
    disposition = (
        CommercialExecutionDisposition.EXISTING_CHARACTER_SCENE_PLANNING
        if invoke
        else CommercialExecutionDisposition.COMPOSITOR_ONLY
    )
    values = {
        "schema_version": "commercial-execution-projection/1",
        "ad_creative_plan_id": "qingyan-plan",
        "ad_creative_plan_revision": 1,
        "ad_creative_plan_hash": "a" * 64,
        "target_shot_id": shot_id,
        "primary_class": primary_class,
        "product_id": None,
        "product_reference_requirement_id": None,
        "source_requirement_id": None,
        "character_requirement_ids": ("qingyan-miao-girl",),
        "scene_requirement_fingerprint": "b" * 64,
        "wardrobe_requirement_fingerprint": "c" * 64,
        "accessory_requirement_fingerprint": "d" * 64,
        "recommended_disposition": disposition,
        "requires_source_materialization": False,
        "requires_source_review": False,
        "invoke_video_provider": invoke,
        "graphic_ids": (),
        "sound_cue_ids": (),
    }
    values["projection_hash"] = canonical_sha256(values)
    return CommercialExecutionProjection.model_validate(values)


def _handoff() -> CompiledAdCreativeHandoff:
    shot_ids = ("shot-b", "shot-a", "shot-later", "shot-end")
    projections = (
        _projection("shot-a", invoke=True),
        _projection("shot-end", invoke=False),
        _projection("shot-b", invoke=True),
        _projection("shot-later", invoke=True),
    )
    return CompiledAdCreativeHandoff(
        plan_id="qingyan-plan",
        plan_content_hash="a" * 64,
        shot_proposals=tuple(
            AdShotProposal(shot_id=shot_id, beat_ids=(f"beat-{shot_id}",))
            for shot_id in shot_ids
        ),
        composition_requirements=AdCompositionRequirements(),
        composition_spec=make_composition_spec(shot_ids=shot_ids),
        commercial_execution_projections=projections,
    )


def _checkpoint(shot_id: str, projection_hash: str):
    return ActivatedCommercialShotCheckpoint.create(
        ad_creative_plan_hash="a" * 64,
        commercial_execution_projection_hash=projection_hash,
        shot_id=shot_id,
        resolved_generation_hash=(
            {"shot-b": "1", "shot-a": "2", "shot-later": "7"}[shot_id] * 64
        ),
        artifact_sha256=(
            {"shot-b": "3", "shot-a": "4", "shot-later": "8"}[shot_id] * 64
        ),
        commercial_evidence_content_hash=(
            {"shot-b": "5", "shot-a": "6", "shot-later": "9"}[shot_id] * 64
        ),
        verdict=QaVerdict.PASS,
        activated=True,
    )


@dataclass
class _Facade:
    shot_id: str
    projection_hash: str
    verdict: QaVerdict = QaVerdict.PASS
    plan_hash: str = "a" * 64
    actions: list[EcommerceShotNextAction] = field(
        default_factory=lambda: [
            EcommerceShotNextAction.START,
            EcommerceShotNextAction.SUBMIT,
            EcommerceShotNextAction.POLL,
            EcommerceShotNextAction.FETCH,
            EcommerceShotNextAction.VALIDATE,
            EcommerceShotNextAction.ACTIVATE,
            EcommerceShotNextAction.DONE,
        ]
    )
    effects: list[str] = field(default_factory=list)
    checkpoint: ActivatedCommercialShotCheckpoint | None = None
    validated_verdict: QaVerdict | None = None

    def bound_commercial_identity(self):
        return (self.plan_hash, self.projection_hash, self.shot_id)

    def next_action(self):
        return self.actions[0]

    def _effect(self, expected: EcommerceShotNextAction):
        assert self.actions.pop(0) is expected
        self.effects.append(expected.value)

    def start(self):
        self._effect(EcommerceShotNextAction.START)

    def submit(self):
        self._effect(EcommerceShotNextAction.SUBMIT)

    def poll(self):
        self._effect(EcommerceShotNextAction.POLL)

    def fetch(self):
        self._effect(EcommerceShotNextAction.FETCH)

    def validate(self):
        self._effect(EcommerceShotNextAction.VALIDATE)
        self.validated_verdict = self.verdict
        return self.verdict

    def activate(self):
        self._effect(EcommerceShotNextAction.ACTIVATE)
        self.checkpoint = _checkpoint(self.shot_id, self.projection_hash)
        return self.checkpoint

    def current_activation_checkpoint(self):
        return self.checkpoint

    def current_validation_verdict(self):
        return self.validated_verdict


def _facades(
    *,
    verdicts: dict[str, QaVerdict] | None = None,
):
    handoff = _handoff()
    by_shot = {
        item.target_shot_id: item for item in handoff.commercial_execution_projections
    }
    facades = {
        "shot-b": _Facade("shot-b", by_shot["shot-b"].projection_hash),
        "shot-a": _Facade(
            "shot-a",
            by_shot["shot-a"].projection_hash,
        ),
        "shot-later": _Facade(
            "shot-later",
            by_shot["shot-later"].projection_hash,
        ),
    }
    for shot_id, verdict in (verdicts or {}).items():
        facades[shot_id].verdict = verdict
    return handoff, facades


def test_coordinator_uses_proposal_order_and_skips_deterministic_shots() -> None:
    handoff, facades = _facades()

    result = run_ecommerce_ad_generation(handoff, facades=facades)

    assert result.complete is True
    assert tuple(item.shot_id for item in result.activated_shots) == (
        "shot-b",
        "shot-a",
        "shot-later",
    )
    assert facades["shot-b"].effects[-1] == "activate"
    assert facades["shot-a"].effects[-1] == "activate"


@pytest.mark.parametrize("failed_shot", ("shot-b", "shot-a", "shot-later"))
@pytest.mark.parametrize("verdict", (QaVerdict.FAIL, QaVerdict.NOT_EVALUATED))
def test_any_shot_nonpass_stops_before_activation_and_later_submit(
    failed_shot: str,
    verdict: QaVerdict,
) -> None:
    handoff, facades = _facades(verdicts={failed_shot: verdict})

    result = run_ecommerce_ad_generation(handoff, facades=facades)

    assert result.complete is False
    assert result.stopped_shot_id == failed_shot
    assert result.stop_reason is EcommerceStopReason.SHOT_NOT_PASS
    assert "activate" not in facades[failed_shot].effects
    ordered = ("shot-b", "shot-a", "shot-later")
    failed_index = ordered.index(failed_shot)
    assert all(facades[item].effects == [] for item in ordered[failed_index + 1 :])


def test_user_stop_between_shots_keeps_later_submit_count_zero() -> None:
    handoff, facades = _facades()
    stop_checks = 0

    def stop_requested() -> bool:
        nonlocal stop_checks
        stop_checks += 1
        return bool(facades["shot-b"].checkpoint)

    result = run_ecommerce_ad_generation(
        handoff,
        facades=facades,
        stop_requested=stop_requested,
    )

    assert result.stop_reason is EcommerceStopReason.USER_STOP
    assert facades["shot-a"].effects == []


def test_done_resume_reuses_checkpoint_without_duplicate_effects() -> None:
    handoff, facades = _facades()
    for shot_id, facade in facades.items():
        facade.actions = [EcommerceShotNextAction.DONE]
        facade.checkpoint = _checkpoint(shot_id, facade.projection_hash)
        facade.validated_verdict = QaVerdict.PASS

    result = run_ecommerce_ad_generation(handoff, facades=facades)

    assert result.complete is True
    assert all(facade.effects == [] for facade in facades.values())


def test_facade_identity_mismatch_stops_before_any_service_effect() -> None:
    handoff, facades = _facades()
    facades["shot-b"], facades["shot-a"] = facades["shot-a"], facades["shot-b"]

    result = run_ecommerce_ad_generation(handoff, facades=facades)

    assert result.complete is False
    assert result.stopped_shot_id == "shot-b"
    assert result.stop_reason is EcommerceStopReason.CHECKPOINT_INVALID
    assert all(facade.effects == [] for facade in facades.values())


def test_production_path_rejects_protocol_facades_before_any_effect(tmp_path) -> None:
    handoff, facades = _facades()
    render_effects: list[str] = []

    with pytest.raises(ValueError, match="not owned"):
        run_ecommerce_ad_production(
            handoff,
            facades=facades,  # type: ignore[arg-type]
            activate_final_render=lambda *_: render_effects.append("render"),
            committer=ProductionStateCommitter(tmp_path),
            universal_profile=None,  # type: ignore[arg-type]
            run_hard_check=lambda *_: None,  # type: ignore[arg-type]
            run_review_layer=lambda *_: None,  # type: ignore[arg-type]
            tool_identity=None,  # type: ignore[arg-type]
            evaluate=lambda *_: None,  # type: ignore[arg-type]
            review_attempt_id="unused-attempt",
            review_request_id="unused-request",
            evidence_id="unused-evidence",
            review_id="unused-review",
            final_acceptance_id="unused-final",
        )

    assert render_effects == []
    assert all(facade.effects == [] for facade in facades.values())
