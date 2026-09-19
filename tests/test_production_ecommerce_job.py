from __future__ import annotations

from dataclasses import dataclass
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_video.production.ad_creative_types import (
    AdCompositionRequirements,
    AdShotProposal,
    CompiledAdCreativeHandoff,
)
from ai_video.production.ad_creative import create_ad_creative_plan
from ai_video.production.artifact_contracts import SourceReference
from ai_video.production.commercial_execution import (
    CommercialExecutionDisposition,
    CommercialExecutionProjection,
    CommercialShotClass,
)
from ai_video.production.ecommerce_ad_coordinator import (
    ActivatedCommercialShotCheckpoint,
    EcommerceShotNextAction,
)
from ai_video.production.ecommerce_job import (
    EcommerceProductionJobService,
    EcommerceShotExecutionInput,
    EcommerceShotExecutionPlan,
)
from ai_video.production.ecommerce_job_repair import (
    bound_generation_attempt_ids,
    canonical_repair_frontier,
    shots_match_handoff,
)
from ai_video.production.ecommerce_job_compiler import (
    bootstrap_ecommerce_production_project,
    compile_ecommerce_production_handoff,
)
from ai_video.production.ecommerce_job_contracts import (
    EcommerceJobNextAction,
    EcommerceProductionHandoff,
    EcommerceProductionJobRequest,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    AssetType,
    CommercialShotEvaluationPhase,
    QaVerdict,
    StateCommitStatus,
)
from ai_video.production.models import VideoAttemptPhase
from ai_video.production.models import VisualStrategy
from ecommerce_job_factory import make_ecommerce_handoff
from production_project_factory import make_composition_spec


PLAN_HASH = "a" * 64
RESOLVED_HASH = "b" * 64


def _runtime_handoff_without_external_assets() -> EcommerceProductionHandoff:
    handoff = make_ecommerce_handoff()
    values = {
        name: getattr(handoff, name)
        for name in EcommerceProductionHandoff.model_fields
        if name != "handoff_id"
    }
    return EcommerceProductionHandoff.create(
        **{**values, "asset_requirements": ()}
    )


def _request(root: Path, handoff: EcommerceProductionHandoff, *, attempts: int = 1):
    return EcommerceProductionJobRequest(
        schema_version="ecommerce-production-job-request/1",
        job_id="job-product-one",
        project_root=root.resolve(),
        handoff_id=handoff.handoff_id,
        expected_project_id="project-product-one",
        execution_policy_id=handoff.compile_profile.profile_id,
        delivery_profile_id=handoff.delivery_profile.profile_id,
        max_new_generation_attempts=attempts,
        max_repairs_per_shot=1,
    )


def _bootstrapped_job(tmp_path: Path, *, attempts: int = 1):
    handoff = _runtime_handoff_without_external_assets()
    request = _request(tmp_path, handoff, attempts=attempts)
    compiled = compile_ecommerce_production_handoff(
        handoff,
        expected_project_id=request.expected_project_id,
    )
    bootstrap_ecommerce_production_project(
        tmp_path,
        attempt_id="ecommerce-bootstrap-job-test",
        compiled=compiled,
    )
    assert (
        EcommerceProductionJobService().inspect(request, handoff).next_action
        is EcommerceJobNextAction.GENERATE_SHOT
    )
    return handoff, request


def _projection(
    *,
    plan_id: str = "product-one-plan",
    plan_hash: str = PLAN_HASH,
) -> CommercialExecutionProjection:
    values = {
        "schema_version": "commercial-execution-projection/1",
        "ad_creative_plan_id": plan_id,
        "ad_creative_plan_revision": 1,
        "ad_creative_plan_hash": plan_hash,
        "target_shot_id": "shot-hero",
        "primary_class": CommercialShotClass.CHARACTER_PERFORMANCE,
        "product_id": None,
        "product_reference_requirement_id": None,
        "source_requirement_id": None,
        "character_requirement_ids": ("talent-presenter",),
        "scene_requirement_fingerprint": "c" * 64,
        "wardrobe_requirement_fingerprint": "d" * 64,
        "accessory_requirement_fingerprint": "e" * 64,
        "recommended_disposition": (
            CommercialExecutionDisposition.EXISTING_CHARACTER_SCENE_PLANNING
        ),
        "requires_source_materialization": False,
        "requires_source_review": False,
        "invoke_video_provider": True,
        "graphic_ids": (),
        "sound_cue_ids": (),
    }
    values["projection_hash"] = canonical_sha256(values)
    return CommercialExecutionProjection.model_validate(values)


def _compiled_handoff(
    *,
    plan_id: str = "product-one-plan",
    plan_hash: str = PLAN_HASH,
) -> CompiledAdCreativeHandoff:
    projection = _projection(plan_id=plan_id, plan_hash=plan_hash)
    return CompiledAdCreativeHandoff(
        plan_id=plan_id,
        plan_content_hash=plan_hash,
        shot_proposals=(AdShotProposal(shot_id="shot-hero", beat_ids=("beat-hero",)),),
        composition_requirements=AdCompositionRequirements(),
        composition_spec=make_composition_spec(shot_ids=("shot-hero",)),
        commercial_execution_projections=(projection,),
    )


@dataclass
class _FakeVideoService:
    verdict: QaVerdict
    project_root: Path
    raise_review_error: bool = False
    repair_verdict: QaVerdict | None = None

    def __post_init__(self) -> None:
        self.actions = [
            EcommerceShotNextAction.START,
            EcommerceShotNextAction.SUBMIT,
            EcommerceShotNextAction.POLL,
            EcommerceShotNextAction.FETCH,
            EcommerceShotNextAction.VALIDATE,
            EcommerceShotNextAction.ACTIVATE,
            EcommerceShotNextAction.DONE,
        ]
        self.effects: list[str] = []
        self.bound_identity = None
        self.checkpoint = None
        self.validated = False

    def current_bound_commercial_request_identity(self, *, attempt_id: str):
        return self.bound_identity

    def commercial_execution_guard(self, *, attempt_id: str):
        return nullcontext()

    def resume_next_action(self, *, attempt_id: str):
        if not self.actions:
            return EcommerceShotNextAction.DONE.value
        return self.actions[0].value

    def start(self, *, attempt_id: str, request, execution_binding=None):
        assert self.actions.pop(0) is EcommerceShotNextAction.START
        binding = request.commercial_binding
        self.bound_identity = (
            request.resolved_generation_hash,
            binding.ad_creative_plan_hash,
            binding.commercial_execution_projection_hash,
            binding.target_shot_id,
        )
        self.effects.append("start")

    def submit_local_once(self, *, attempt_id: str, pre_submit_guard=None):
        assert self.actions.pop(0) is EcommerceShotNextAction.SUBMIT
        self.effects.append("submit")

    def refresh_local_once(self, *, attempt_id: str):
        assert self.actions.pop(0) is EcommerceShotNextAction.POLL
        self.effects.append("poll")

    def fetch_local_once(self, *, attempt_id: str):
        assert self.actions.pop(0) is EcommerceShotNextAction.FETCH
        self.effects.append("fetch")

    def validate_once(self, *, attempt_id: str, **kwargs):
        assert self.actions.pop(0) is EcommerceShotNextAction.VALIDATE
        self.validated = True
        self.effects.append("validate")
        if kwargs.get("repair_commercial_evidence"):
            assert self.repair_verdict is not None
            self.verdict = self.repair_verdict
        if self.raise_review_error:
            from ai_video.errors import AiVideoError, ErrorCode

            raise AiVideoError(
                code=ErrorCode.REVIEW_EVIDENCE_INVALID,
                user_message="Commercial review did not pass.",
                retryable=False,
            )

    def current_commercial_validation_verdict(self, *, attempt_id: str):
        return self.verdict if self.validated else None

    def activate_once(self, *, attempt_id: str):
        assert self.verdict is QaVerdict.PASS
        assert self.actions.pop(0) is EcommerceShotNextAction.ACTIVATE
        assert self.bound_identity is not None
        self.checkpoint = ActivatedCommercialShotCheckpoint.create(
            ad_creative_plan_hash=self.bound_identity[1],
            commercial_execution_projection_hash=self.bound_identity[2],
            shot_id="shot-hero",
            resolved_generation_hash=RESOLVED_HASH,
            artifact_sha256="f" * 64,
            commercial_evidence_content_hash="1" * 64,
            verdict=QaVerdict.PASS,
            activated=True,
        )
        self.effects.append("activate")

    def current_activated_commercial_checkpoint(self, *, attempt_id: str):
        return self.checkpoint


def _execution(
    service: _FakeVideoService,
    handoff: EcommerceProductionHandoff,
    *,
    plan_artifact_id: str = "product-one-plan",
    different_proposal: bool = False,
) -> EcommerceShotExecutionPlan:
    proposal = handoff.ad_creative_plan_proposal
    if different_proposal:
        proposal = proposal.model_copy(
            update={"creative_concept": f"{proposal.creative_concept} alternate"}
        )
    plan = create_ad_creative_plan(
        proposal,
        artifact_id=plan_artifact_id,
        revision=1,
        creation_receipt_id="ecommerce-plan-test",
        source_provenance=(
            SourceReference(
                kind="derived",
                reference=f"ecommerce-handoff:{handoff.handoff_id}",
                content_hash=handoff.handoff_id,
            ),
            SourceReference(
                kind="derived",
                reference=(
                    "ecommerce-compile-profile:"
                    f"{handoff.compile_profile.profile_id}"
                ),
                content_hash=handoff.compile_profile.profile_id,
            ),
        ),
    )
    projection = _projection(plan_id=plan.artifact_id, plan_hash=plan.content_hash)
    binding = SimpleNamespace(
        ad_creative_plan_hash=plan.content_hash,
        commercial_execution_projection_hash=projection.projection_hash,
        target_shot_id="shot-hero",
    )
    request = SimpleNamespace(
        resolved_generation_hash=RESOLVED_HASH,
        commercial_binding=binding,
        provider_kind="local-test",
        model_id="local-model",
    )
    return EcommerceShotExecutionPlan(
        handoff=_compiled_handoff(plan_id=plan.artifact_id, plan_hash=plan.content_hash),
        plan=plan,
        shots=(
            EcommerceShotExecutionInput(
                shot_id="shot-hero",
                attempt_id="attempt-shot-hero-1",
                service=service,
                request=request,
                lane="local",
                commercial_reviewer=object(),
            ),
        ),
    )


def test_advance_generate_shot_delegates_to_existing_coordinator_and_replays_no_effect(
    tmp_path: Path,
) -> None:
    handoff, request = _bootstrapped_job(tmp_path)
    service = _FakeVideoService(QaVerdict.PASS, tmp_path.resolve())
    execution = _execution(service, handoff)
    job = EcommerceProductionJobService()

    first = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=execution,
    )
    first_effects = tuple(service.effects)
    replay = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=execution,
    )

    assert first.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION
    assert replay.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION
    assert first_effects == ("start", "submit", "poll", "fetch", "validate", "activate")
    assert tuple(service.effects) == first_effects


@pytest.mark.parametrize(
    ("verdict", "expected"),
    (
        (QaVerdict.FAIL, EcommerceJobNextAction.REPAIR_SHOT_MEDIA),
        (QaVerdict.NOT_EVALUATED, EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE),
    ),
)
def test_advance_nonpass_never_activates_and_maps_exact_gate_outcome(
    tmp_path: Path,
    verdict: QaVerdict,
    expected: EcommerceJobNextAction,
) -> None:
    handoff, request = _bootstrapped_job(tmp_path)
    service = _FakeVideoService(verdict, tmp_path.resolve())

    result = EcommerceProductionJobService().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=_execution(service, handoff),
    )

    assert result.next_action is expected
    assert "activate" not in service.effects


def test_advance_refuses_generation_before_the_projected_action(tmp_path: Path) -> None:
    handoff = _runtime_handoff_without_external_assets()
    request = _request(tmp_path, handoff)
    service = _FakeVideoService(QaVerdict.PASS, tmp_path.resolve())

    result = EcommerceProductionJobService().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=_execution(service, handoff),
    )

    assert result.next_action is EcommerceJobNextAction.BOOTSTRAP_PROJECT
    assert service.effects == []


def test_advance_enforces_job_generation_ceiling_before_any_effect(tmp_path: Path) -> None:
    handoff, request = _bootstrapped_job(tmp_path, attempts=0)
    service = _FakeVideoService(QaVerdict.PASS, tmp_path.resolve())

    result = EcommerceProductionJobService().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=_execution(service, handoff),
    )

    assert result.next_action is EcommerceJobNextAction.BLOCKED
    assert result.blocker is not None
    assert result.blocker.blocker_code == "ECOMMERCE_JOB_GENERATION_CEILING_EXHAUSTED"
    assert service.effects == []


def test_generation_ceiling_counts_prior_bound_attempts_across_service_instances(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.bound_generation_attempt_ids",
        lambda _root, _execution: ("attempt-shot-hero-prior",),
    )

    handoff, request = _bootstrapped_job(tmp_path, attempts=1)
    service = _FakeVideoService(QaVerdict.PASS, tmp_path.resolve())

    result = EcommerceProductionJobService().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=_execution(service, handoff),
    )

    assert result.next_action is EcommerceJobNextAction.BLOCKED
    assert result.blocker is not None
    assert result.blocker.blocker_code == "ECOMMERCE_JOB_GENERATION_CEILING_EXHAUSTED"
    assert service.effects == []


def test_advance_unknown_outcome_stops_without_retry(tmp_path: Path) -> None:
    class _UnknownOutcomeJob(EcommerceProductionJobService):
        @staticmethod
        def _attempt_status(request, execution, *, shot_id):
            return StateCommitStatus.OUTCOME_UNKNOWN

    handoff, request = _bootstrapped_job(tmp_path)
    service = _FakeVideoService(QaVerdict.PASS, tmp_path.resolve())
    service.actions = [EcommerceShotNextAction.START, EcommerceShotNextAction.STOP]

    result = _UnknownOutcomeJob().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=_execution(service, handoff),
    )

    assert result.next_action is EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME
    assert service.effects == ["start"]


def test_execution_rejects_service_bound_to_another_project_before_effect(
    tmp_path: Path,
) -> None:
    handoff, request = _bootstrapped_job(tmp_path)
    service = _FakeVideoService(QaVerdict.PASS, (tmp_path / "other").resolve())

    result = EcommerceProductionJobService().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=_execution(service, handoff),
    )

    assert result.next_action is EcommerceJobNextAction.BLOCKED
    assert result.blocker is not None
    assert result.blocker.blocker_code == "ECOMMERCE_SHOT_EXECUTION_INVALID"
    assert service.effects == []


def test_execution_rejects_same_shot_ids_from_a_different_plan_before_effect(
    tmp_path: Path,
) -> None:
    handoff, request = _bootstrapped_job(tmp_path)
    service = _FakeVideoService(QaVerdict.PASS, tmp_path.resolve())
    execution = _execution(service, handoff, different_proposal=True)

    result = EcommerceProductionJobService().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=execution,
    )

    assert result.next_action is EcommerceJobNextAction.BLOCKED
    assert result.blocker is not None
    assert result.blocker.blocker_code == "ECOMMERCE_SHOT_EXECUTION_INVALID"
    assert service.effects == []


@pytest.mark.parametrize(
    ("verdict", "expected"),
    (
        (QaVerdict.FAIL, EcommerceJobNextAction.REPAIR_SHOT_MEDIA),
        (QaVerdict.NOT_EVALUATED, EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE),
    ),
)
def test_real_review_exception_shape_still_maps_durable_gate_outcome(
    tmp_path: Path,
    verdict: QaVerdict,
    expected: EcommerceJobNextAction,
) -> None:
    handoff, request = _bootstrapped_job(tmp_path)
    service = _FakeVideoService(
        verdict,
        tmp_path.resolve(),
        raise_review_error=True,
    )

    result = EcommerceProductionJobService().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=_execution(service, handoff),
    )

    assert result.next_action is expected
    assert "activate" not in service.effects


def test_legitimate_activated_shot_revision_is_not_treated_as_artifact_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = _runtime_handoff_without_external_assets().artifact_proposals.shots[0]
    target_role = expected.required_asset_roles[0].role
    active = seal_artifact(
        expected.model_copy(
            update={
                "revision": expected.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": "video-provenance-receipt",
                "visual_strategy": VisualStrategy.GENERATED_VIDEO,
                "generated_video_rationale": "Sealed generation generation-shot-hero.",
                "required_asset_roles": tuple(
                    role.model_copy(
                        update={
                            "asset_ids": ("generated-shot-asset",),
                            "allowed_asset_types": (AssetType.VIDEO,),
                        }
                    )
                    if role.role == target_role
                    else role
                    for role in expected.required_asset_roles
                ),
            }
        )
    )
    state = SimpleNamespace(
        phase=VideoAttemptPhase.ACTIVATE,
        request=object(),
        generation_id="generation-shot-hero",
        candidate_video_asset_ids=("generated-shot-asset",),
    )
    manifest = SimpleNamespace(
        attempts=(
            SimpleNamespace(
                attempt_id="attempt-activated-shot",
                status=StateCommitStatus.SUCCEEDED,
                video_generation_state=state,
            ),
        )
    )
    binding = SimpleNamespace(target_shot_id=expected.shot_id)
    activation_request = SimpleNamespace(
        target_shot_id=expected.shot_id,
        target_asset_role=target_role,
    )
    resolved_request = SimpleNamespace(
        commercial_binding=binding,
        activation_scope=SimpleNamespace(request=activation_request),
        output_asset_id="generated-shot-asset",
    )
    monkeypatch.setattr(
        "ai_video.production._video_project_reader.load_video_request_receipt",
        lambda _root, _pointer: resolved_request,
    )

    assert shots_match_handoff(
        tmp_path,
        expected_shots=(expected,),
        active_shots=(active,),
        manifest=manifest,
    )
    assert not shots_match_handoff(
        tmp_path,
        expected_shots=(expected,),
        active_shots=(active.model_copy(update={"scene_id": "scene-drift"}),),
        manifest=manifest,
    )


def test_evidence_repair_resumes_exact_attempt_without_media_submit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _EvidenceRepairJob(EcommerceProductionJobService):
        def inspect(self, request, handoff, *, shot_execution=None):
            return self._projection(
                request,
                next_action=EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE,
                manifest_revision=1,
                next_shot_id="shot-hero",
            )

    handoff, request = _bootstrapped_job(tmp_path)
    service = _FakeVideoService(
        QaVerdict.NOT_EVALUATED,
        tmp_path.resolve(),
        repair_verdict=QaVerdict.PASS,
    )
    service.actions = [
        EcommerceShotNextAction.VALIDATE,
        EcommerceShotNextAction.ACTIVATE,
        EcommerceShotNextAction.DONE,
    ]
    execution = _execution(service, handoff)
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.bound_generation_attempt_ids",
        lambda _root, _execution: (execution.shots[0].attempt_id,),
    )
    resolved = execution.shots[0].request
    binding = resolved.commercial_binding
    service.bound_identity = (
        resolved.resolved_generation_hash,
        binding.ad_creative_plan_hash,
        binding.commercial_execution_projection_hash,
        binding.target_shot_id,
    )

    result = _EvidenceRepairJob().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE,
        shot_execution=execution,
    )

    assert result.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION
    assert service.effects == ["validate", "activate"]


def test_evidence_repair_rejects_a_new_attempt_before_any_effect(
    tmp_path: Path,
) -> None:
    class _EvidenceRepairJob(EcommerceProductionJobService):
        def inspect(self, request, handoff, *, shot_execution=None):
            return self._projection(
                request,
                next_action=EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE,
                manifest_revision=1,
                next_shot_id="shot-hero",
            )

    handoff, request = _bootstrapped_job(tmp_path)
    service = _FakeVideoService(QaVerdict.NOT_EVALUATED, tmp_path.resolve())

    result = _EvidenceRepairJob().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE,
        shot_execution=_execution(service, handoff),
    )

    assert result.next_action is EcommerceJobNextAction.BLOCKED
    assert result.blocker is not None
    assert result.blocker.blocker_code == "ECOMMERCE_EVIDENCE_REPAIR_ATTEMPT_MISMATCH"
    assert service.effects == []


def test_evidence_repair_rejects_request_identity_drift_before_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _EvidenceRepairJob(EcommerceProductionJobService):
        def inspect(self, request, handoff, *, shot_execution=None):
            return self._projection(
                request,
                next_action=EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE,
                manifest_revision=1,
                next_shot_id="shot-hero",
            )

    handoff, request = _bootstrapped_job(tmp_path)
    service = _FakeVideoService(
        QaVerdict.NOT_EVALUATED,
        tmp_path.resolve(),
        repair_verdict=QaVerdict.PASS,
    )
    execution = _execution(service, handoff)
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.bound_generation_attempt_ids",
        lambda _root, _execution: (execution.shots[0].attempt_id,),
    )
    service.bound_identity = (
        "6" * 64,
        execution.handoff.plan_content_hash,
        execution.handoff.commercial_execution_projections[0].projection_hash,
        "shot-hero",
    )

    result = _EvidenceRepairJob().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE,
        shot_execution=execution,
    )

    assert result.next_action is EcommerceJobNextAction.BLOCKED
    assert service.effects == []


def test_commercial_intent_only_frontier_routes_to_explicit_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handoff = _runtime_handoff_without_external_assets()
    execution = _execution(
        _FakeVideoService(QaVerdict.PASS, tmp_path.resolve()),
        handoff,
    )
    evaluation = SimpleNamespace(
        phase=CommercialShotEvaluationPhase.INTENT,
        evidence=None,
    )
    attempt = SimpleNamespace(
        attempt_id="attempt-evaluator-unknown",
        status=StateCommitStatus.RUNNING,
        video_generation_state=SimpleNamespace(
            request=object(),
            commercial_evaluation=evaluation,
        ),
    )
    projection = execution.handoff.commercial_execution_projections[0]
    binding = SimpleNamespace(
        ad_creative_plan_hash=execution.handoff.plan_content_hash,
        commercial_execution_projection_hash=projection.projection_hash,
        target_shot_id=projection.target_shot_id,
    )
    monkeypatch.setattr(
        "ai_video.production._video_project_reader.load_video_request_receipt",
        lambda _root, _pointer: SimpleNamespace(commercial_binding=binding),
    )

    assert canonical_repair_frontier(
        tmp_path,
        execution,
        SimpleNamespace(attempts=(attempt,)),
    ) == (EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME, "shot-hero")


def test_evidence_repair_interruption_returns_reopened_recovery_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _InterruptedRepairJob(EcommerceProductionJobService):
        inspections = 0

        def inspect(self, request, handoff, *, shot_execution=None):
            self.inspections += 1
            action = (
                EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE
                if self.inspections == 1
                else EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME
            )
            return self._projection(
                request,
                next_action=action,
                manifest_revision=self.inspections,
                next_shot_id="shot-hero",
            )

    handoff, request = _bootstrapped_job(tmp_path)
    service = _FakeVideoService(
        QaVerdict.NOT_EVALUATED,
        tmp_path.resolve(),
        raise_review_error=True,
        repair_verdict=QaVerdict.NOT_EVALUATED,
    )
    service.actions = [EcommerceShotNextAction.VALIDATE]
    execution = _execution(service, handoff)
    resolved = execution.shots[0].request
    binding = resolved.commercial_binding
    service.bound_identity = (
        resolved.resolved_generation_hash,
        binding.ad_creative_plan_hash,
        binding.commercial_execution_projection_hash,
        binding.target_shot_id,
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.bound_generation_attempt_ids",
        lambda _root, _execution: (execution.shots[0].attempt_id,),
    )

    result = _InterruptedRepairJob().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE,
        shot_execution=execution,
    )

    assert result.next_action is EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME
    assert result.blocker is None


def test_existing_shot_attempt_from_another_plan_cannot_reset_job_ceiling(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handoff = _runtime_handoff_without_external_assets()
    execution = _execution(
        _FakeVideoService(QaVerdict.PASS, tmp_path.resolve()),
        handoff,
    )
    state = SimpleNamespace(request=object())
    loaded = SimpleNamespace(
        manifest=SimpleNamespace(
            attempts=(
                SimpleNamespace(
                    attempt_id="attempt-old-plan",
                    video_generation_state=state,
                ),
            )
        )
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_repair.load_production_project",
        lambda _path: loaded,
    )
    old_binding = SimpleNamespace(
        ad_creative_plan_hash="7" * 64,
        commercial_execution_projection_hash="8" * 64,
        target_shot_id="shot-hero",
    )
    monkeypatch.setattr(
        "ai_video.production._video_project_reader.load_video_request_receipt",
        lambda _root, _pointer: SimpleNamespace(commercial_binding=old_binding),
    )

    with pytest.raises(ValueError, match="selected plan"):
        bound_generation_attempt_ids(tmp_path, execution)


def test_shot_execution_contracts_are_public_python_api() -> None:
    from ai_video import production

    assert production.EcommerceShotExecutionInput is EcommerceShotExecutionInput
    assert production.EcommerceShotExecutionPlan is EcommerceShotExecutionPlan
