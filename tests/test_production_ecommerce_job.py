from __future__ import annotations

from contextlib import contextmanager, nullcontext
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
import hashlib
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

from ai_video.errors import AiVideoError, ErrorCode
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
    project_generated_commercial_shot_binding,
)
from ai_video.production.composition_contracts import RendererIdentity, RendererKind
from ai_video.production.dependency import (
    ProductionDependencyInputs,
    build_production_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.ecommerce_ad_coordinator import (
    ActivatedCommercialShotCheckpoint,
    EcommerceShotNextAction,
)
from ai_video.production.ecommerce_job import (
    EcommerceProductionJobService,
    EcommerceShotExecutionInput,
    EcommerceShotExecutionPlan,
)
from ai_video.production.ecommerce_job_assembly import EcommerceAssemblyDecision
from ai_video.production.ecommerce_job_repair import (
    EcommerceAttemptIdentity,
    EcommerceShotRepairContext,
    bound_generation_attempt_ids,
    canonical_repair_frontier,
    input_attempt_identity,
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
from ai_video.production.ecommerce_job_review import EcommerceFinalReviewFrontier
from ai_video.production.ecommerce_media_acceptance import (
    create_qingyan_ecommerce_acceptance_profile,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.hyperframes import probe_clip_fd
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    CommercialShotEvaluationPhase,
    EgressMetadata,
    QaVerdict,
    StateCommitStatus,
    ToolIdentity,
)
from ai_video.production.models import VideoAttemptPhase
from ai_video.production.models import VisualStrategy
from ai_video.production.paths import canonical_image_asset_path
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    prepare_dependency_graph_transition,
)
from ai_video.production.video import (
    BillingKind,
    ProviderProfilePointer,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoOutputRequirement,
    VideoProviderCapabilities,
)
from ai_video.production.video_candidate_composition import (
    build_video_candidate_composition_spec,
)
from ai_video.production.video_generation import VideoGenerationService
from ecommerce_job_factory import make_ecommerce_handoff
from production_generation_execution_factory import (
    activate_fixture_generation_qa_policy,
    prepare_generation_execution,
)
from production_project_factory import (
    make_composition_spec,
    make_p8_video_candidate_preparer,
)
from test_production_commercial_visual_review import (
    REVIEW_TOOL,
    _policy as _commercial_policy,
)
from test_production_generated_video_e2e import (
    COMMERCIAL_EVALUATOR,
    FIXTURE,
    _CountingCommercialShotReviewer,
)
from test_production_ecommerce_job_repair import _diagnosis, _intervention
from test_production_local_video_state import LocalVideoProviderDouble


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
        is (
            EcommerceJobNextAction.GENERATE_SHOT
            if attempts > 0
            else EcommerceJobNextAction.BLOCKED
        )
    )
    return handoff, request


def _projection(
    *,
    plan_id: str = "product-one-plan",
    plan_hash: str = PLAN_HASH,
    shot_id: str = "shot-hero",
) -> CommercialExecutionProjection:
    values = {
        "schema_version": "commercial-execution-projection/1",
        "ad_creative_plan_id": plan_id,
        "ad_creative_plan_revision": 1,
        "ad_creative_plan_hash": plan_hash,
        "target_shot_id": shot_id,
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
    shot_ids: tuple[str, ...] = ("shot-hero",),
) -> CompiledAdCreativeHandoff:
    projections = tuple(
        _projection(plan_id=plan_id, plan_hash=plan_hash, shot_id=shot_id)
        for shot_id in shot_ids
    )
    return CompiledAdCreativeHandoff(
        plan_id=plan_id,
        plan_content_hash=plan_hash,
        shot_proposals=tuple(
            AdShotProposal(shot_id=shot_id, beat_ids=("beat-hero",))
            for shot_id in shot_ids
        ),
        composition_requirements=AdCompositionRequirements(),
        composition_spec=make_composition_spec(shot_ids=shot_ids),
        commercial_execution_projections=projections,
    )


@dataclass
class _FakeVideoService:
    verdict: QaVerdict
    project_root: Path
    shot_id: str = "shot-hero"
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
        self.guard_ids: list[str] = []

    def current_bound_commercial_request_identity(self, *, attempt_id: str):
        return self.bound_identity

    def commercial_execution_guard(self, *, attempt_id: str):
        self.guard_ids.append(attempt_id)
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
            shot_id=self.shot_id,
            resolved_generation_hash=self.bound_identity[0],
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
    assert service.guard_ids[:2] == [
        f"ecommerce-job-ceiling:{execution.handoff.plan_content_hash}",
        "attempt-shot-hero-1",
    ]
    assert set(service.guard_ids) <= {
        f"ecommerce-job-ceiling:{execution.handoff.plan_content_hash}",
        "attempt-shot-hero-1",
    }


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


def test_inspect_projects_blocked_before_initial_generation_at_zero_ceiling(
    tmp_path: Path,
) -> None:
    handoff, request = _bootstrapped_job(tmp_path, attempts=0)
    service = _FakeVideoService(QaVerdict.PASS, tmp_path.resolve())

    projected = EcommerceProductionJobService().inspect(
        request, handoff, shot_execution=_execution(service, handoff)
    )

    assert projected.next_action is EcommerceJobNextAction.BLOCKED
    assert projected.blocker is not None
    assert projected.blocker.blocker_code == "ECOMMERCE_JOB_GENERATION_CEILING_EXHAUSTED"
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


@pytest.mark.parametrize(
    ("job_ceiling", "shot_ceiling", "expected_blocker"),
    (
        (1, 1, "ECOMMERCE_JOB_GENERATION_CEILING_EXHAUSTED"),
        (2, 0, "ECOMMERCE_SHOT_REPAIR_CEILING_EXHAUSTED"),
    ),
)
def test_inspect_projects_blocked_when_failed_shot_has_no_repair_capacity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    job_ceiling: int,
    shot_ceiling: int,
    expected_blocker: str,
) -> None:
    handoff, request = _bootstrapped_job(tmp_path, attempts=job_ceiling)
    request = request.model_copy(update={"max_repairs_per_shot": shot_ceiling})
    service = _FakeVideoService(QaVerdict.FAIL, tmp_path.resolve())
    execution = _execution(service, handoff)
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_projection.canonical_repair_frontier",
        lambda *_: (EcommerceJobNextAction.REPAIR_SHOT_MEDIA, "shot-hero"),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_projection.bound_generation_attempt_ids",
        lambda *_: ("failed-attempt",),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_projection.bound_generation_attempt_ids_for_shot",
        lambda *_, **__: ("failed-attempt",),
    )

    projected = EcommerceProductionJobService().inspect(
        request, handoff, shot_execution=execution
    )

    assert projected.next_action is EcommerceJobNextAction.BLOCKED
    assert projected.blocker is not None
    assert projected.blocker.blocker_code == expected_blocker
    assert service.effects == []


@pytest.mark.parametrize(
    ("prior_attempt_id", "diagnosis_hash", "expected_blocker"),
    (
        ("attempt-old", "d" * 64, "ECOMMERCE_SHOT_REPAIR_IDENTITY_MISMATCH"),
        ("attempt-latest", "a" * 64, "ECOMMERCE_SHOT_REPAIR_EVIDENCE_MISMATCH"),
        ("attempt-latest", "d" * 64, None),
    ),
)
def test_media_repair_rejects_stale_attempt_or_gate_evidence_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    prior_attempt_id: str,
    diagnosis_hash: str,
    expected_blocker: str | None,
) -> None:
    class _RepairJob(EcommerceProductionJobService):
        def inspect(self, request, handoff, *, shot_execution=None):
            return self._projection(
                request,
                next_action=EcommerceJobNextAction.REPAIR_SHOT_MEDIA,
                manifest_revision=2,
                next_shot_id="shot-hero",
            )

    handoff, request = _bootstrapped_job(tmp_path, attempts=3)
    request = request.model_copy(update={"max_repairs_per_shot": 2})
    service = _FakeVideoService(QaVerdict.PASS, tmp_path.resolve())
    base = _execution(service, handoff)
    proposed = replace(base.shots[0], attempt_id="attempt-proposed")
    prior = EcommerceAttemptIdentity(
        attempt_id=prior_attempt_id,
        routing_binding_hash="c" * 64,
        permit_id="permit-prior",
        resolved_generation_hash="a" * 64,
    )
    context = EcommerceShotRepairContext(
        shot_id="shot-hero",
        verdict=QaVerdict.FAIL,
        outcome_known=True,
        diagnosis=_diagnosis("QUALITY_FAILURE").model_copy(
            update={"evidence_hashes": (diagnosis_hash,)}
        ),
        intervention=_intervention(),
        prior_attempt=prior,
        proposed_attempt=input_attempt_identity(proposed),
        existing_job_attempts=2,
        existing_shot_repairs=1,
        request_delta_verified=True,
    )
    execution = replace(
        base, shots=(replace(proposed, repair_context=context),)
    )
    latest = SimpleNamespace(
        attempt_id="attempt-latest",
        video_generation_state=SimpleNamespace(
            commercial_evaluation=SimpleNamespace(
                evidence=SimpleNamespace(content_hash="d" * 64)
            )
        ),
    )
    loaded = SimpleNamespace(
        manifest=SimpleNamespace(manifest_revision=2, attempts=(latest,))
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.load_production_project",
        lambda *_: loaded,
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.bound_generation_attempt_ids",
        lambda *_: ("attempt-old", "attempt-latest"),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.bound_generation_attempt_ids_for_shot",
        lambda *_, **__: ("attempt-old", "attempt-latest"),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.canonical_attempt_identity",
        lambda _root, _attempt_id: prior,
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.repair_request_delta_is_verified",
        lambda *_, **__: True,
    )
    generation_calls: list[str] = []

    def run_generation(*_args, **_kwargs):
        if expected_blocker is not None:
            pytest.fail("stale repair reached generation")
        generation_calls.append("run")
        return SimpleNamespace(complete=True)

    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.run_ecommerce_ad_generation",
        run_generation,
    )

    result = _RepairJob().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.REPAIR_SHOT_MEDIA,
        shot_execution=execution,
    )

    if expected_blocker is None:
        assert result.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION
        assert generation_calls == ["run"]
    else:
        assert result.next_action is EcommerceJobNextAction.BLOCKED
        assert result.blocker is not None
        assert result.blocker.blocker_code == expected_blocker
        assert generation_calls == []
    assert service.effects == []


class _ConcurrentAdmissionVideoService(_FakeVideoService):
    admission_lock = threading.Lock()
    first_started = threading.Event()
    release_first = threading.Event()

    def commercial_execution_guard(self, *, attempt_id: str):
        self.guard_ids.append(attempt_id)
        if not attempt_id.startswith("ecommerce-job-ceiling:"):
            return nullcontext()

        @contextmanager
        def guard():
            if not self.admission_lock.acquire(blocking=False):
                raise AiVideoError(
                    code=ErrorCode.PRODUCTION_STATE_BUSY,
                    user_message="Ecommerce Job execution is busy.",
                    retryable=False,
                )
            try:
                yield
            finally:
                self.admission_lock.release()

        return guard()

    def start(self, *, attempt_id: str, request, execution_binding=None):
        self.first_started.set()
        assert self.release_first.wait(timeout=5)
        super().start(
            attempt_id=attempt_id,
            request=request,
            execution_binding=execution_binding,
        )


def test_job_ceiling_admission_serializes_distinct_attempt_ids(tmp_path: Path) -> None:
    _ConcurrentAdmissionVideoService.first_started.clear()
    _ConcurrentAdmissionVideoService.release_first.clear()
    handoff, request = _bootstrapped_job(tmp_path, attempts=1)
    first_service = _ConcurrentAdmissionVideoService(QaVerdict.PASS, tmp_path.resolve())
    second_service = _ConcurrentAdmissionVideoService(QaVerdict.PASS, tmp_path.resolve())
    first = _execution(first_service, handoff)
    second_base = _execution(second_service, handoff)
    second = replace(
        second_base,
        shots=(replace(second_base.shots[0], attempt_id="attempt-shot-hero-2"),),
    )
    job = EcommerceProductionJobService()

    with ThreadPoolExecutor(max_workers=1) as pool:
        running = pool.submit(
            job.advance_once,
            request,
            handoff,
            expected_action=EcommerceJobNextAction.GENERATE_SHOT,
            shot_execution=first,
        )
        assert first_service.first_started.wait(timeout=5)
        blocked = job.advance_once(
            request,
            handoff,
            expected_action=EcommerceJobNextAction.GENERATE_SHOT,
            shot_execution=second,
        )
        first_service.release_first.set()
        completed = running.result(timeout=5)

    assert completed.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION
    assert blocked.next_action is EcommerceJobNextAction.BLOCKED
    assert blocked.blocker is not None
    assert blocked.blocker.blocker_code == "ECOMMERCE_JOB_EXECUTION_BUSY"
    assert first_service.effects.count("submit") == 1
    assert second_service.effects == []


def test_advance_unknown_outcome_stops_without_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handoff, request = _bootstrapped_job(tmp_path)
    service = _FakeVideoService(QaVerdict.PASS, tmp_path.resolve())
    service.actions = [EcommerceShotNextAction.START, EcommerceShotNextAction.STOP]
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.ecommerce_attempt_status",
        lambda _root, _execution, *, shot_id: StateCommitStatus.OUTCOME_UNKNOWN,
    )

    result = EcommerceProductionJobService().advance_once(
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


def test_evidence_repair_uses_declared_input_instead_of_deferred_replacement(
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
    declared = execution.shots[0]
    binding = declared.request.commercial_binding
    service.bound_identity = (
        declared.request.resolved_generation_hash,
        binding.ad_creative_plan_hash,
        binding.commercial_execution_projection_hash,
        binding.target_shot_id,
    )
    replacement_service = _FakeVideoService(QaVerdict.PASS, tmp_path.resolve())
    replacement = replace(
        declared,
        service=replacement_service,
        request=SimpleNamespace(
            commercial_binding=declared.request.commercial_binding,
            resolved_generation_hash="9" * 64,
            provider_kind="replacement-provider",
            model_id="replacement-model",
        ),
    )
    factory_calls: list[str] = []

    def replace_validated_input(shot_id: str):
        factory_calls.append(shot_id)
        return replacement

    execution = replace(execution, input_factory=replace_validated_input)
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.bound_generation_attempt_ids",
        lambda _root, _execution: (declared.attempt_id,),
    )

    result = _EvidenceRepairJob().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE,
        shot_execution=execution,
    )

    assert result.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION
    assert factory_calls == []
    assert service.effects == ["validate", "activate"]
    assert replacement_service.effects == []


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


@pytest.mark.parametrize(
    ("repair_verdict", "reopened_action"),
    (
        (QaVerdict.FAIL, EcommerceJobNextAction.REPAIR_SHOT_MEDIA),
        (QaVerdict.NOT_EVALUATED, EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE),
    ),
)
def test_evidence_repair_error_returns_durable_typed_repair_frontier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    repair_verdict: QaVerdict,
    reopened_action: EcommerceJobNextAction,
) -> None:
    class _EvidenceRepairJob(EcommerceProductionJobService):
        inspections = 0

        def inspect(self, request, handoff, *, shot_execution=None):
            self.inspections += 1
            action = (
                EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE
                if self.inspections <= 2
                else reopened_action
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
        repair_verdict=repair_verdict,
    )
    service.actions = [EcommerceShotNextAction.VALIDATE]
    execution = _execution(service, handoff)
    declared = execution.shots[0]
    binding = declared.request.commercial_binding
    service.bound_identity = (
        declared.request.resolved_generation_hash,
        binding.ad_creative_plan_hash,
        binding.commercial_execution_projection_hash,
        binding.target_shot_id,
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.bound_generation_attempt_ids",
        lambda _root, _execution: (declared.attempt_id,),
    )

    result = _EvidenceRepairJob().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.REPAIR_SHOT_EVIDENCE,
        shot_execution=execution,
    )

    assert result.next_action is reopened_action
    assert result.next_shot_id == "shot-hero"
    assert result.blocker is None
    assert service.effects == ["validate"]


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


@dataclass
class _FakeCompositionExecution:
    state: str = "render"
    fail_unknown: bool = False

    def __post_init__(self) -> None:
        self.prepared: list[Path] = []
        self.rendered: list[object] = []

    def prepare(self, _handoff, *, project_root: Path):
        prepared = SimpleNamespace(project_root=project_root)
        self.prepared.append(project_root)
        return prepared

    def render(self, prepared):
        self.rendered.append(prepared)
        if self.fail_unknown:
            self.state = "recover"
            raise OSError("renderer outcome is unknown")
        self.state = "active"
        return object()


class _CompositionJob(EcommerceProductionJobService):
    def inspect(
        self,
        request,
        handoff,
        *,
        shot_execution=None,
        composition_execution=None,
    ):
        if composition_execution is None:
            action = EcommerceJobNextAction.PREPARE_COMPOSITION
        elif composition_execution.state == "render":
            action = EcommerceJobNextAction.RENDER_FINAL
        elif composition_execution.state == "recover":
            action = EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME
        else:
            action = EcommerceJobNextAction.REVIEW_FINAL
        return self._projection(request, next_action=action, manifest_revision=7)


def _fake_advance_composition(execution, handoff, *, project_root, render):
    prepared = execution.prepare(handoff, project_root=project_root)
    if not render:
        return EcommerceAssemblyDecision(EcommerceJobNextAction.RENDER_FINAL)
    try:
        execution.render(prepared)
    except OSError:
        return EcommerceAssemblyDecision(
            EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME
        )
    return EcommerceAssemblyDecision(EcommerceJobNextAction.REVIEW_FINAL)


def test_prepare_composition_is_pure_and_projects_exact_render(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handoff = _runtime_handoff_without_external_assets()
    request = _request(tmp_path, handoff)
    execution = _FakeCompositionExecution()
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.advance_ecommerce_job_assembly",
        _fake_advance_composition,
    )

    result = _CompositionJob().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PREPARE_COMPOSITION,
        composition_execution=execution,
    )

    assert result.next_action is EcommerceJobNextAction.RENDER_FINAL
    assert execution.prepared == [tmp_path.resolve()]
    assert execution.rendered == []


def test_render_final_invokes_once_and_exact_replay_has_no_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handoff = _runtime_handoff_without_external_assets()
    request = _request(tmp_path, handoff)
    execution = _FakeCompositionExecution()
    job = _CompositionJob()
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.advance_ecommerce_job_assembly",
        _fake_advance_composition,
    )

    first = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.RENDER_FINAL,
        composition_execution=execution,
    )
    replay = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.RENDER_FINAL,
        composition_execution=execution,
    )

    assert first.next_action is EcommerceJobNextAction.REVIEW_FINAL
    assert replay.next_action is EcommerceJobNextAction.REVIEW_FINAL
    assert len(execution.rendered) == 1


def test_render_unknown_outcome_stops_for_explicit_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handoff = _runtime_handoff_without_external_assets()
    request = _request(tmp_path, handoff)
    execution = _FakeCompositionExecution(fail_unknown=True)
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.advance_ecommerce_job_assembly",
        _fake_advance_composition,
    )

    result = _CompositionJob().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.RENDER_FINAL,
        composition_execution=execution,
    )

    assert result.next_action is EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME
    assert len(execution.rendered) == 1


@dataclass
class _FakeReviewExecution:
    verdict: QaVerdict
    accepted: bool
    owner: object
    frontier: EcommerceFinalReviewFrontier = (
        EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED
    )

    def __post_init__(self) -> None:
        self.calls = 0

    def run(self, _handoff, *, project_root: Path):
        self.calls += 1
        self.owner.state = (
            "package" if self.accepted else self.frontier.value
        )
        return SimpleNamespace(
            final_acceptance_recorded=self.accepted,
            gate_two=SimpleNamespace(verdict=self.verdict),
        )


@dataclass
class _FakeDeliveryExecution:
    published: bool = False
    package_calls: int = 0

    def package(self, _handoff, *, project_root: Path, job_id: str):
        self.package_calls += 1
        self.published = True
        return object()


class _FinalJob(EcommerceProductionJobService):
    def __init__(self) -> None:
        self.state = "review"

    def inspect(
        self,
        request,
        handoff,
        *,
        shot_execution=None,
        composition_execution=None,
        review_execution=None,
        delivery_execution=None,
    ):
        if delivery_execution is not None and delivery_execution.published:
            action = EcommerceJobNextAction.COMPLETE
        elif self.state == "package":
            action = EcommerceJobNextAction.PACKAGE_DELIVERY
        elif self.state == EcommerceFinalReviewFrontier.PREPARE_COMPOSITION.value:
            action = EcommerceJobNextAction.PREPARE_COMPOSITION
        elif self.state == EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED.value:
            return self._blocked(
                request,
                blocker_code="ECOMMERCE_FINAL_REPAIR_DIAGNOSIS_REQUIRED",
                stage="final_review",
                subject_id=request.job_id,
                failure_classification="WHOLE_VIDEO_FAILURE",
                required_action="Diagnose the exact failed final requirement.",
                manifest_revision=11,
            )
        else:
            action = EcommerceJobNextAction.REVIEW_FINAL
        return self._projection(request, next_action=action, manifest_revision=11)


@pytest.mark.parametrize(
    ("verdict", "accepted", "frontier", "expected"),
    (
        (
            QaVerdict.PASS,
            True,
            EcommerceFinalReviewFrontier.PACKAGE_DELIVERY,
            EcommerceJobNextAction.PACKAGE_DELIVERY,
        ),
        (
            QaVerdict.FAIL,
            False,
            EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED,
            EcommerceJobNextAction.BLOCKED,
        ),
        (
            QaVerdict.NOT_EVALUATED,
            False,
            EcommerceFinalReviewFrontier.REVIEW_FINAL,
            EcommerceJobNextAction.REVIEW_FINAL,
        ),
        (
            QaVerdict.FAIL,
            False,
            EcommerceFinalReviewFrontier.PREPARE_COMPOSITION,
            EcommerceJobNextAction.PREPARE_COMPOSITION,
        ),
    ),
)
def test_review_final_routes_exact_outcome_to_smallest_frontier(
    tmp_path: Path,
    verdict: QaVerdict,
    accepted: bool,
    frontier: EcommerceFinalReviewFrontier,
    expected: EcommerceJobNextAction,
) -> None:
    handoff = _runtime_handoff_without_external_assets()
    request = _request(tmp_path, handoff)
    job = _FinalJob()
    execution = _FakeReviewExecution(verdict, accepted, job, frontier)

    result = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.REVIEW_FINAL,
        review_execution=execution,
    )

    assert result.next_action is expected
    assert execution.calls == 1


def test_delivery_publish_completes_and_exact_replay_has_no_effect(
    tmp_path: Path,
) -> None:
    handoff = _runtime_handoff_without_external_assets()
    request = _request(tmp_path, handoff)
    job = _FinalJob()
    job.state = "package"
    delivery = _FakeDeliveryExecution()

    first = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PACKAGE_DELIVERY,
        delivery_execution=delivery,
    )
    replay = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PACKAGE_DELIVERY,
        delivery_execution=delivery,
    )

    assert first.next_action is EcommerceJobNextAction.COMPLETE
    assert replay.next_action is EcommerceJobNextAction.COMPLETE
    assert delivery.package_calls == 1


def _two_shot_runtime_handoff() -> EcommerceProductionHandoff:
    base = _runtime_handoff_without_external_assets()
    first_shot = base.artifact_proposals.shots[0]
    second_shot = seal_artifact(
        first_shot.model_copy(
            update={
                "artifact_id": "shot-artifact-proof",
                "content_hash": "0" * 64,
                "creation_receipt_id": "ecommerce-authoring-shot-proof",
                "shot_id": "shot-proof",
                "intent": "Show a second deterministic product proof angle.",
            }
        )
    )
    storyboard = base.artifact_proposals.storyboard
    second_storyboard = seal_artifact(
        storyboard.model_copy(
            update={
                "content_hash": "0" * 64,
                "creation_receipt_id": "ecommerce-authoring-storyboard-two-shot",
                "beats": (
                    storyboard.beats[0].model_copy(
                        update={"shot_ids": (first_shot.shot_id, second_shot.shot_id)}
                    ),
                ),
            }
        )
    )
    base_layout = base.layout_plan
    layout_values = {
        name: getattr(base_layout, name)
        for name in type(base_layout).model_fields
        if name != "layout_plan_id"
    }
    second_layout_shot = base_layout.shots[0].model_copy(
        update={"shot_id": second_shot.shot_id}
    )
    layout = type(base_layout).create(
        **{**layout_values, "shots": (*base_layout.shots, second_layout_shot)}
    )
    evidence_ids = (
        base.delivery_profile.profile_id,
        base.visual_system_profile.profile_id,
        layout.layout_plan_id,
    )
    base_profile = base.compile_profile
    profile_values = {
        name: getattr(base_profile, name)
        for name in type(base_profile).model_fields
        if name != "profile_id"
    }
    compile_profile = type(base_profile).create(
        **{
            **profile_values,
            "layout_plan_id": layout.layout_plan_id,
            "requirement_resolutions": tuple(
                item.model_copy(update={"evidence_ids": evidence_ids})
                for item in base_profile.requirement_resolutions
            ),
        }
    )
    acceptance = base.acceptance_requirements[0].model_copy(
        update={
            "requirement_id": "accept-shot-proof",
            "subject_id": second_shot.shot_id,
            "description": "Second product proof Shot preserves product identity.",
        }
    )
    values = {
        name: getattr(base, name)
        for name in EcommerceProductionHandoff.model_fields
        if name != "handoff_id"
    }
    return EcommerceProductionHandoff.create(
        **{
            **values,
            "layout_plan": layout,
            "compile_profile": compile_profile,
            "artifact_proposals": base.artifact_proposals.model_copy(
                update={
                    "storyboard": second_storyboard,
                    "shots": (first_shot, second_shot),
                }
            ),
            "acceptance_requirements": (
                base.acceptance_requirements[0],
                acceptance,
                *base.acceptance_requirements[1:],
            ),
        }
    )


def _two_shot_execution(
    handoff: EcommerceProductionHandoff,
    *,
    project_root: Path,
) -> EcommerceShotExecutionPlan:
    plan = create_ad_creative_plan(
        handoff.ad_creative_plan_proposal,
        artifact_id="product-one-two-shot-plan",
        revision=1,
        creation_receipt_id="ecommerce-two-shot-plan-test",
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
    shot_ids = tuple(item.shot_id for item in handoff.artifact_proposals.shots)
    compiled = _compiled_handoff(
        plan_id=plan.artifact_id,
        plan_hash=plan.content_hash,
        shot_ids=shot_ids,
    )
    projections = {
        item.target_shot_id: item
        for item in compiled.commercial_execution_projections
    }
    inputs = tuple(
            EcommerceShotExecutionInput(
                shot_id=shot_id,
                attempt_id=f"attempt-{shot_id}-1",
                service=_FakeVideoService(
                    QaVerdict.PASS,
                    project_root,
                    shot_id=shot_id,
                ),
                request=SimpleNamespace(
                    resolved_generation_hash=(
                        "1" if shot_id == "shot-hero" else "2"
                    )
                    * 64,
                    commercial_binding=SimpleNamespace(
                        ad_creative_plan_hash=plan.content_hash,
                        commercial_execution_projection_hash=(
                            projections[shot_id].projection_hash
                        ),
                        target_shot_id=shot_id,
                    ),
                    provider_kind="local-test",
                    model_id="local-model",
                ),
                lane="local",
                commercial_reviewer=object(),
            )
            for shot_id in shot_ids
        )
    by_shot = {item.shot_id: item for item in inputs}
    return EcommerceShotExecutionPlan(
        handoff=compiled,
        plan=plan,
        shots=inputs,
        input_factory=by_shot.__getitem__,
    )


class _OfflineScenarioJob(EcommerceProductionJobService):
    def __init__(self) -> None:
        self.state = "shots"

    def inspect(
        self,
        request,
        handoff,
        *,
        shot_execution=None,
        composition_execution=None,
        review_execution=None,
        delivery_execution=None,
    ):
        if delivery_execution is not None and delivery_execution.published:
            action = EcommerceJobNextAction.COMPLETE
        elif self.state == "package":
            action = EcommerceJobNextAction.PACKAGE_DELIVERY
        elif self.state == EcommerceFinalReviewFrontier.PREPARE_COMPOSITION.value:
            action = EcommerceJobNextAction.PREPARE_COMPOSITION
        elif self.state == "review":
            action = EcommerceJobNextAction.REVIEW_FINAL
        elif composition_execution is not None:
            action = (
                EcommerceJobNextAction.RENDER_FINAL
                if composition_execution.state == "render"
                else EcommerceJobNextAction.REVIEW_FINAL
            )
        elif shot_execution is not None:
            pending = next(
                (
                    item.shot_id
                    for item in shot_execution.shots
                    if item.service.checkpoint is None
                ),
                None,
            )
            action = (
                EcommerceJobNextAction.GENERATE_SHOT
                if pending is not None
                else EcommerceJobNextAction.PREPARE_COMPOSITION
            )
            return self._projection(
                request,
                next_action=action,
                manifest_revision=1,
                next_shot_id=pending,
            )
        else:
            action = EcommerceJobNextAction.PREPARE_COMPOSITION
        return self._projection(request, next_action=action, manifest_revision=1)


def _bootstrapped_two_shot_job(tmp_path: Path):
    handoff = _two_shot_runtime_handoff()
    request = _request(tmp_path, handoff, attempts=2)
    assert (
        EcommerceProductionJobService().inspect(request, handoff).next_action
        is EcommerceJobNextAction.BOOTSTRAP_PROJECT
    )
    compiled = compile_ecommerce_production_handoff(
        handoff,
        expected_project_id=request.expected_project_id,
    )
    bootstrap_ecommerce_production_project(
        tmp_path,
        attempt_id="ecommerce-two-shot-bootstrap",
        compiled=compiled,
    )
    return handoff, request, _two_shot_execution(
        handoff,
        project_root=tmp_path.resolve(),
    )


def test_offline_two_shot_job_runs_bootstrap_through_delivery_and_exact_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handoff, request, shot_execution = _bootstrapped_two_shot_job(tmp_path)
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.bound_generation_attempt_ids",
        lambda _root, _execution: (),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.advance_ecommerce_job_assembly",
        _fake_advance_composition,
    )
    job = _OfflineScenarioJob()

    generated = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=shot_execution,
    )
    composition = _FakeCompositionExecution()
    prepared = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PREPARE_COMPOSITION,
        shot_execution=shot_execution,
        composition_execution=composition,
    )
    rendered = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.RENDER_FINAL,
        shot_execution=shot_execution,
        composition_execution=composition,
    )
    review = _FakeReviewExecution(QaVerdict.PASS, True, job)
    reviewed = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.REVIEW_FINAL,
        shot_execution=shot_execution,
        composition_execution=composition,
        review_execution=review,
    )
    delivery = _FakeDeliveryExecution()
    delivered = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PACKAGE_DELIVERY,
        shot_execution=shot_execution,
        composition_execution=composition,
        review_execution=review,
        delivery_execution=delivery,
    )
    manifest_bytes = (tmp_path / "state/manifest.json").read_bytes()
    effect_snapshot = {
        item.shot_id: tuple(item.service.effects)
        for item in shot_execution.shots
    }
    replay = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PACKAGE_DELIVERY,
        shot_execution=shot_execution,
        composition_execution=composition,
        review_execution=review,
        delivery_execution=delivery,
    )

    assert generated.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION
    assert prepared.next_action is EcommerceJobNextAction.RENDER_FINAL
    assert rendered.next_action is EcommerceJobNextAction.REVIEW_FINAL
    assert reviewed.next_action is EcommerceJobNextAction.PACKAGE_DELIVERY
    assert delivered.next_action is EcommerceJobNextAction.COMPLETE
    assert replay.next_action is EcommerceJobNextAction.COMPLETE
    assert tuple(item.shot_id for item in shot_execution.shots) == (
        "shot-hero",
        "shot-proof",
    )
    assert all(effects[-1] == "activate" for effects in effect_snapshot.values())
    assert {
        item.shot_id: tuple(item.service.effects)
        for item in shot_execution.shots
    } == effect_snapshot
    assert len(composition.rendered) == 1
    assert review.calls == 1
    assert delivery.package_calls == 1
    assert (tmp_path / "state/manifest.json").read_bytes() == manifest_bytes


def test_offline_two_shot_reopen_skips_first_activation_and_runs_second_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handoff, request, shot_execution = _bootstrapped_two_shot_job(tmp_path)
    by_shot = {item.shot_id: item for item in shot_execution.shots}
    first_input = by_shot["shot-hero"]
    first = first_input.service
    first.actions = [EcommerceShotNextAction.DONE]
    first.validated_verdict = QaVerdict.PASS
    first_binding = first_input.request.commercial_binding
    first.checkpoint = ActivatedCommercialShotCheckpoint.create(
        ad_creative_plan_hash=first_binding.ad_creative_plan_hash,
        commercial_execution_projection_hash=(
            first_binding.commercial_execution_projection_hash
        ),
        shot_id=first_input.shot_id,
        resolved_generation_hash="1" * 64,
        artifact_sha256="3" * 64,
        commercial_evidence_content_hash="5" * 64,
        verdict=QaVerdict.PASS,
        activated=True,
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job.bound_generation_attempt_ids",
        lambda _root, _execution: ("attempt-shot-hero-1",),
    )
    reopened = _OfflineScenarioJob()

    before = reopened.inspect(request, handoff, shot_execution=shot_execution)
    result = reopened.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=shot_execution,
    )

    assert before.next_shot_id == "shot-proof"
    assert result.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION
    assert first.effects == []
    assert by_shot["shot-proof"].service.effects == [
        "start",
        "submit",
        "poll",
        "fetch",
        "validate",
        "activate",
    ]


OUTPUT = VideoOutputRequirement(
    duration_seconds=1,
    width=64,
    height=64,
    fps=24,
    container="mp4",
    mime_type="video/mp4",
    native_audio=False,
)


def _bootstrapped_canonical_job(root: Path):
    handoff = _two_shot_runtime_handoff()
    request = _request(root, handoff, attempts=2)
    compiled = compile_ecommerce_production_handoff(
        handoff,
        expected_project_id=request.expected_project_id,
    )
    assets = []
    prepared = []
    for shot_id in ("shot-hero", "shot-proof"):
        payload = f"offline-placeholder:{shot_id}".encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        asset = AssetRecord(
            asset_id=f"image-{shot_id}",
            asset_type=AssetType.IMAGE,
            artifact_path=canonical_image_asset_path(digest),
            sha256=digest,
            size_bytes=len(payload),
            mime_type="image/png",
            width=64,
            height=64,
            source_kind=AssetSourceKind.IMPORTED,
            tool=ToolIdentity(name="fixture", version="1"),
            input_fingerprint=digest,
            creation_receipt_id=f"fixture-{shot_id}",
            usage_license="fixture",
            egress=EgressMetadata(remote=False),
        )
        assets.append(asset)
        prepared.append(PreparedArtifact(asset.artifact_path, payload, digest))
    registry = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id="0" * 64,
        content_hash="0" * 64,
        assets=tuple(assets),
    )
    registry_hash = registry_semantic_sha256(registry)
    compiled = replace(
        compiled,
        registry=registry.model_copy(
            update={"revision_id": registry_hash, "content_hash": registry_hash}
        ),
        artifacts=(*compiled.artifacts, *prepared),
    )
    bootstrap_ecommerce_production_project(
        root,
        attempt_id="ecommerce-canonical-two-shot-bootstrap",
        compiled=compiled,
    )
    skeleton = _two_shot_execution(handoff, project_root=root.resolve())
    base_spec = skeleton.handoff.composition_spec
    canonical_spec = seal_artifact(
        base_spec.model_copy(
            update={
                "revision": base_spec.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": "ecommerce-canonical-two-shot-composition",
                "layers": tuple(
                    layer.model_copy(update={"asset_role": "final_visual"})
                    for layer in base_spec.layers
                ),
            }
        )
    )
    skeleton = replace(
        skeleton,
        handoff=skeleton.handoff.model_copy(
            update={"composition_spec": canonical_spec}
        ),
    )
    return handoff, request, skeleton


def _dependency_inputs(root: Path, execution) -> ProductionDependencyInputs:
    return ProductionDependencyInputs(
        project=load_production_project(root / "project.yaml"),
        composition_spec=execution.handoff.composition_spec,
        renderer=RendererIdentity(kind=RendererKind.HYPERFRAMES, version="0.7.103"),
        voice_requests=(),
        resolver_contract_fingerprint="1" * 64,
        source_materializer_contract_fingerprint="2" * 64,
        render_contract_fingerprint="3" * 64,
        caption_style_fingerprints=(),
    )


def _activate_offline_ecommerce_policy(
    root: Path,
    inputs: ProductionDependencyInputs,
) -> ProductionDependencyInputs:
    committer = ProductionStateCommitter(root)
    manifest = committer._read_manifest()
    graph = build_production_dependency_graph(inputs)
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=manifest.manifest_revision,
        base_dependency_graph=manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=resolve_dependency_state(graph, ()).states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    committer.bootstrap_dependency_graph(
        attempt_id="bootstrap-ecommerce-job-canonical-e2e-graph",
        graph=graph,
        transition=transition,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    current = committer._read_manifest()
    committer.upgrade_manifest_schema(
        "2.13",
        expected_manifest_revision=current.manifest_revision,
    )
    inputs = replace(
        inputs,
        project=load_production_project(root / "project.yaml"),
    )
    profile = create_qingyan_ecommerce_acceptance_profile()
    policy = _commercial_policy()
    policy = seal_artifact(
        policy.model_copy(
            update={
                "artifact_id": "qa-policy-ecommerce-job-canonical-e2e",
                "revision": policy.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": "qa-policy-ecommerce-job-canonical-e2e",
                "semantic_authorities": (REVIEW_TOOL, COMMERCIAL_EVALUATOR),
                "domain_acceptance": DomainAcceptancePolicy(
                    domain_id="ecommerce",
                    profile_id=profile.profile_id,
                    profile_version=profile.profile_version,
                    profile_content_hash=profile.content_hash,
                    profile_payload=profile.model_dump(mode="json"),
                    measurement_contract_version=profile.measurement_contract_version,
                    required_requirement_ids=profile.required_requirement_ids,
                ),
            }
        )
    )
    current = committer._read_manifest()
    committer.activate_qa_policy(
        policy,
        expected_manifest_revision=current.manifest_revision,
        attempt_id="activate-ecommerce-job-canonical-e2e-policy",
    )
    refreshed = replace(
        inputs,
        project=load_production_project(root / "project.yaml"),
    )
    return activate_fixture_generation_qa_policy(
        root=root,
        inputs=refreshed,
        output=OUTPUT,
    )


def _real_input(
    *,
    root: Path,
    execution,
    shot_id: str,
    composition_spec,
) -> tuple[EcommerceShotExecutionInput, LocalVideoProviderDouble]:
    loaded = load_production_project(root / "project.yaml")
    inputs = ProductionDependencyInputs(
        project=loaded,
        composition_spec=composition_spec,
        renderer=RendererIdentity(kind=RendererKind.HYPERFRAMES, version="0.7.103"),
        voice_requests=(),
        resolver_contract_fingerprint="1" * 64,
        source_materializer_contract_fingerprint="2" * 64,
        render_contract_fingerprint="3" * 64,
        caption_style_fingerprints=(),
    )
    shot = next(item for item in loaded.shots if item.shot_id == shot_id)
    projection = next(
        item
        for item in execution.handoff.commercial_execution_projections
        if item.target_shot_id == shot_id
    )
    profile = create_qingyan_ecommerce_acceptance_profile()
    output_asset_id = f"canonical-ecommerce-{shot_id}-video"
    commercial_binding = project_generated_commercial_shot_binding(
        projection,
        profile=profile,
        applicable_requirement_ids=(
            "shot.identity.main_character",
            "shot.motion.required",
            "shot.camera.intent",
        ),
        approved_source=None,
        expected_actor_ids=projection.character_requirement_ids,
        output_asset_id=output_asset_id,
    )
    provider_kind = "offline-local-ecommerce"
    model_id = "offline-local-fixture"
    request = VideoGenerationRequest.create(
        generation_id=f"canonical-ecommerce-{shot_id}-generation",
        provider_name=provider_kind,
        provider_kind=provider_kind,
        model_id=model_id,
        provider_profile=ProviderProfilePointer(
            profile_id="offline-local-ecommerce-profile",
            profile_version="v1",
            profile_path=Path(f"provider-profiles/{'a' * 64}.json"),
            profile_sha256="a" * 64,
        ),
        target_shot_id=shot.shot_id,
        target_shot_revision=shot.revision,
        target_shot_content_hash=shot.content_hash,
        target_asset_role=shot.required_asset_roles[0].role,
        target_visual_strategy="generated_video",
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
        prompt_text=f"Render deterministic offline Ecommerce Shot {shot_id}.",
        negative_prompt_text="",
        image_bindings=(),
        commercial_binding=commercial_binding,
        output_requirement=OUTPUT,
        seed=19,
        base_project=loaded.manifest.active_project,
        base_registry=loaded.manifest.active_registry,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        input_artifact_ids=(shot.artifact_id,),
        output_asset_id=output_asset_id,
    )
    variant = VideoCapabilityVariant(
        capability_id="offline-local-ecommerce-t2v",
        provider_kind=provider_kind,
        model_id=model_id,
        profile_version="v1",
        execution_kind=VideoExecutionKind.LOCAL,
        billing_kind=BillingKind.LOCAL_UNMETERED,
        mode=VideoGenerationMode.TEXT_TO_VIDEO,
        output=OUTPUT,
        allowed_image_roles=(),
        required_first_frame=False,
        max_reference_count=0,
        allowed_image_mime_types=(),
        max_image_bytes=1,
        min_image_width=1,
        min_image_height=1,
        negative_prompt_supported=False,
        seed_supported=True,
        fps_supported=True,
        idempotent_submit=False,
        lookup_supported=False,
    )
    provider = LocalVideoProviderDouble(
        capabilities=VideoProviderCapabilities.create(
            provider_name=provider_kind,
            variants=(variant,),
        ),
        artifact_bytes=FIXTURE.read_bytes(),
        native_prompt_text=request.prompt_text,
    )
    prepared = prepare_generation_execution(
        project=loaded,
        provider=provider,
        request=provider.resolve(request),
        task_id=f"canonical-ecommerce-{shot_id}",
        compiler_id="local-video-state-fixture",
        compiler_version="1",
    )
    service = VideoGenerationService(
        committer=ProductionStateCommitter(
            root,
            video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        ),
        provider=provider,
    )
    return (
        EcommerceShotExecutionInput(
            shot_id=shot_id,
            attempt_id=f"canonical-ecommerce-{shot_id}-attempt",
            service=service,
            request=prepared.resolved,
            lane="local",
            commercial_reviewer=_CountingCommercialShotReviewer(),
            probe=probe_clip_fd,
            execution_binding=prepared.binding,
        ),
        provider,
    )


def test_canonical_two_shot_reopen_resumes_second_and_replay_has_zero_effects(
    tmp_path: Path,
) -> None:
    handoff, request, skeleton = _bootstrapped_canonical_job(tmp_path)
    inputs = _activate_offline_ecommerce_policy(
        tmp_path,
        _dependency_inputs(tmp_path, skeleton),
    )
    base_spec = inputs.composition_spec
    first_input, first_provider = _real_input(
        root=tmp_path,
        execution=skeleton,
        shot_id="shot-hero",
        composition_spec=base_spec,
    )
    second_declared, _ = _real_input(
        root=tmp_path,
        execution=skeleton,
        shot_id="shot-proof",
        composition_spec=base_spec,
    )
    first_factory_calls: list[str] = []

    def interrupt_after_first(shot_id: str):
        first_factory_calls.append(shot_id)
        if shot_id == "shot-proof":
            loaded = load_production_project(tmp_path / "project.yaml")
            assert any(
                item.asset_id == "canonical-ecommerce-shot-hero-video"
                for item in loaded.registry.assets
            )
            raise ValueError("simulated process interruption before Shot 2 binding")
        return first_input

    first_plan = replace(
        skeleton,
        shots=(first_input, second_declared),
        input_factory=interrupt_after_first,
    )
    interrupted = EcommerceProductionJobService().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=first_plan,
    )

    assert interrupted.next_action is EcommerceJobNextAction.BLOCKED
    assert first_factory_calls == ["shot-hero", "shot-proof"]
    assert first_provider.submit_calls == 1
    assert first_provider.fetch_calls == 1

    after_first_spec = build_video_candidate_composition_spec(
        base_spec,
        target_shot_id="shot-hero",
        target_asset_role=first_input.request.activation_scope.request.target_asset_role,
        output_asset_id="canonical-ecommerce-shot-hero-video",
    )
    reopened_first, _ = _real_input(
        root=tmp_path,
        execution=skeleton,
        shot_id="shot-hero",
        composition_spec=after_first_spec,
    )
    reopened_second, second_provider = _real_input(
        root=tmp_path,
        execution=skeleton,
        shot_id="shot-proof",
        composition_spec=after_first_spec,
    )
    resumed_factory_calls: list[str] = []

    def resume_second_only(shot_id: str):
        assert shot_id != "shot-hero"
        resumed_factory_calls.append(shot_id)
        return reopened_second

    resumed_plan = replace(
        skeleton,
        shots=(reopened_first, reopened_second),
        input_factory=resume_second_only,
    )
    reopened_job = EcommerceProductionJobService()
    before_resume = reopened_job.inspect(
        request,
        handoff,
        shot_execution=resumed_plan,
    )
    resumed = reopened_job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=resumed_plan,
    )

    assert before_resume.next_action is EcommerceJobNextAction.GENERATE_SHOT
    assert before_resume.next_shot_id == "shot-proof"
    assert resumed.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION
    assert resumed_factory_calls == ["shot-proof"]
    assert second_provider.submit_calls == 1
    assert second_provider.fetch_calls == 1

    manifest_before_replay = (tmp_path / "state/manifest.json").read_bytes()
    replay_factory_calls: list[str] = []
    replay_plan = replace(
        resumed_plan,
        input_factory=lambda shot_id: replay_factory_calls.append(shot_id),
    )
    replay = EcommerceProductionJobService().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=replay_plan,
    )

    assert replay.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION
    assert replay_factory_calls == []
    assert first_provider.submit_calls == 1
    assert first_provider.fetch_calls == 1
    assert second_provider.submit_calls == 1
    assert second_provider.fetch_calls == 1
    assert (tmp_path / "state/manifest.json").read_bytes() == manifest_before_replay
    final = load_production_project(tmp_path / "project.yaml")
    assert {
        item.asset_id
        for item in final.registry.assets
        if item.asset_id.startswith("canonical-ecommerce-")
    } == {
        "canonical-ecommerce-shot-hero-video",
        "canonical-ecommerce-shot-proof-video",
    }
