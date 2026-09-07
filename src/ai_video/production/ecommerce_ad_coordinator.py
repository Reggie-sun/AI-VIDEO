"""Sequential Ecommerce Shot orchestration over preselected public service facades."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import nullcontext
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Protocol

from pydantic import Field, model_validator

from ai_video.errors import AiVideoError
from ai_video.production._caption_quality_p6 import (
    CaptionReviewExecution,
    caption_aware_review_layer_runner,
)
from ai_video.production._ecommerce_quality_gate_p6 import (
    _record_ecommerce_gate_review,
)
from ai_video.production.ad_creative_types import CompiledAdCreativeHandoff
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.ecommerce_quality_gate import (
    EcommerceAcceptedShotIdentity,
    EcommerceGateResult,
    EcommerceWholeAdEvaluator,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    FinalAcceptanceReceipt,
    QaLayer,
    QaVerdict,
    SourceReference,
    ToolIdentity,
)
from ai_video.production.paid_provider import PaidProviderCallPreview
from ai_video.production.project import load_production_project
from ai_video.production.quality_gate_coordinator import (
    HardCheckRunner,
    ReviewLayerRunner,
    UniversalQaApplicability,
    UniversalQaContext,
    UniversalQaProfile,
    UniversalQualityGateCoordinator,
)
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video import ResolvedVideoGenerationRequest
from ai_video.production.video_generation import VideoGenerationService


class EcommerceShotNextAction(str, Enum):
    START = "start"
    SUBMIT = "submit"
    POLL = "poll"
    FETCH = "fetch"
    VALIDATE = "validate"
    ACTIVATE = "activate"
    DONE = "done"
    STOP = "stop"


class EcommerceStopReason(str, Enum):
    USER_STOP = "user_stop"
    SHOT_NOT_PASS = "shot_not_pass"
    SERVICE_STOP = "service_stop"
    CHECKPOINT_INVALID = "checkpoint_invalid"


class ActivatedCommercialShotCheckpoint(StrictModel):
    schema_version: Literal["activated-commercial-shot/1"] = (
        "activated-commercial-shot/1"
    )
    ad_creative_plan_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    commercial_execution_projection_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    shot_id: str = Field(min_length=1)
    resolved_generation_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    commercial_evidence_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    verdict: QaVerdict
    activated: bool
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_checkpoint(self) -> "ActivatedCommercialShotCheckpoint":
        if self.verdict is not QaVerdict.PASS or self.activated is not True:
            raise ValueError("activated commercial Shot checkpoint requires exact PASS")
        if self.content_hash != canonical_sha256(self):
            raise ValueError("activated commercial Shot checkpoint hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "ActivatedCommercialShotCheckpoint":
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {**values, "content_hash": canonical_sha256(provisional)}
        )


class EcommerceShotExecutionFacade(Protocol):
    def bound_commercial_identity(self) -> tuple[str, str, str]: ...

    def next_action(self) -> EcommerceShotNextAction: ...

    def start(self) -> None: ...

    def submit(self) -> None: ...

    def poll(self) -> None: ...

    def fetch(self) -> None: ...

    def validate(self) -> QaVerdict: ...

    def activate(self) -> ActivatedCommercialShotCheckpoint: ...

    def current_validation_verdict(self) -> QaVerdict | None: ...

    def current_activation_checkpoint(
        self,
    ) -> ActivatedCommercialShotCheckpoint | None: ...


@dataclass
class EcommerceVideoGenerationFacade:
    """Production adapter over one preselected local or paid video service."""

    service: VideoGenerationService
    attempt_id: str
    request: ResolvedVideoGenerationRequest
    lane: Literal["local", "paid"]
    commercial_reviewer: Any
    paid_preview: PaidProviderCallPreview | None = None
    reservation_id: str | None = None
    probe: Callable[[int], dict] | None = None
    terminal_frame_extractor: Any = None
    continuity_reviewer: Any = None
    pre_submit_guard: Callable[[ResolvedVideoGenerationRequest], None] | None = None
    before_validate: Callable[[], None] | None = None
    execution_binding: Any = None
    _started: bool = False

    def __post_init__(self) -> None:
        if self.request.commercial_binding is None:
            raise ValueError("Ecommerce facade requires a commercial-bound request")
        if self.lane == "paid" and (
            self.paid_preview is None or self.reservation_id is None
        ):
            raise ValueError("Paid Ecommerce facade requires preview and reservation")

    def _declared_commercial_request_identity(
        self,
    ) -> tuple[str, str, str, str]:
        binding = self.request.commercial_binding
        assert binding is not None
        return (
            self.request.resolved_generation_hash,
            binding.ad_creative_plan_hash,
            binding.commercial_execution_projection_hash,
            binding.target_shot_id,
        )

    def bound_commercial_identity(self) -> tuple[str, str, str]:
        declared = self._declared_commercial_request_identity()
        durable = self.service.current_bound_commercial_request_identity(
            attempt_id=self.attempt_id
        )
        if durable is not None and durable != declared:
            raise ValueError(
                "Ecommerce facade request does not match the durable attempt"
            )
        return declared[1:]

    def _require_durable_request_identity(self) -> None:
        durable = self.service.current_bound_commercial_request_identity(
            attempt_id=self.attempt_id
        )
        if durable != self._declared_commercial_request_identity():
            raise ValueError(
                "Ecommerce facade request does not match the durable attempt"
            )

    def next_action(self) -> EcommerceShotNextAction:
        try:
            return EcommerceShotNextAction(
                self.service.resume_next_action(attempt_id=self.attempt_id)
            )
        except AiVideoError:
            return (
                EcommerceShotNextAction.STOP
                if self._started
                else EcommerceShotNextAction.START
            )

    def execution_guard(self):
        return self.service.commercial_execution_guard(attempt_id=self.attempt_id)

    def start(self) -> None:
        self.service.start(attempt_id=self.attempt_id, request=self.request,
                           execution_binding=self.execution_binding)
        self._started = True

    def submit(self) -> None:
        self._require_durable_request_identity()
        if self.lane == "local":
            self.service.submit_local_once(
                attempt_id=self.attempt_id,
                pre_submit_guard=self.pre_submit_guard,
            )
            return
        assert self.paid_preview is not None and self.reservation_id is not None
        self.service.submit_once(
            attempt_id=self.attempt_id,
            paid_preview=self.paid_preview,
            reservation_id=self.reservation_id,
        )

    def poll(self) -> None:
        self._require_durable_request_identity()
        if self.lane == "local":
            self.service.refresh_local_once(attempt_id=self.attempt_id)
        else:
            self.service.refresh_once(attempt_id=self.attempt_id)

    def fetch(self) -> None:
        self._require_durable_request_identity()
        if self.lane == "local":
            self.service.fetch_local_once(attempt_id=self.attempt_id)
        else:
            self.service.fetch_once(attempt_id=self.attempt_id)

    def validate(self) -> QaVerdict:
        self._require_durable_request_identity()
        if self.before_validate is not None:
            self.before_validate()
        self.service.validate_once(
            attempt_id=self.attempt_id,
            probe=self.probe,
            terminal_frame_extractor=self.terminal_frame_extractor,
            continuity_reviewer=self.continuity_reviewer,
            commercial_reviewer=self.commercial_reviewer,
        )
        verdict = self.current_validation_verdict()
        return QaVerdict.NOT_EVALUATED if verdict is None else verdict

    def activate(self) -> ActivatedCommercialShotCheckpoint:
        self._require_durable_request_identity()
        self.service.activate_once(attempt_id=self.attempt_id)
        checkpoint = self.current_activation_checkpoint()
        if checkpoint is None:
            raise ValueError("Commercial activation checkpoint is missing")
        return checkpoint

    def current_validation_verdict(self) -> QaVerdict | None:
        return self.service.current_commercial_validation_verdict(
            attempt_id=self.attempt_id
        )

    def current_activation_checkpoint(
        self,
    ) -> ActivatedCommercialShotCheckpoint | None:
        return self.service.current_activated_commercial_checkpoint(
            attempt_id=self.attempt_id
        )


class EcommerceAdGenerationResult(StrictModel):
    """Provider Shot-stage result only; never composition or delivery acceptance."""

    complete: bool
    activated_shots: tuple[ActivatedCommercialShotCheckpoint, ...]
    stopped_shot_id: str | None = None
    stop_reason: EcommerceStopReason | None = None

    @model_validator(mode="after")
    def _validate_result(self) -> "EcommerceAdGenerationResult":
        if self.complete == (self.stop_reason is not None):
            raise ValueError("Ecommerce generation result completion is inconsistent")
        if (self.stopped_shot_id is None) != (self.stop_reason is None):
            raise ValueError("Ecommerce generation stop identity is incomplete")
        return self


class EcommercePostMediaAcceptanceResult(StrictModel):
    """Closure status for one exact active canonical Ecommerce render."""

    shot_stage_complete: bool
    gate_two: EcommerceGateResult
    p6_semantic_receipt_recorded: bool = False
    final_acceptance_recorded: bool = False
    render_output_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    final_acceptance_content_hash: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )

    @model_validator(mode="after")
    def _validate_closure(self) -> "EcommercePostMediaAcceptanceResult":
        if self.final_acceptance_recorded and (
            not self.shot_stage_complete
            or not self.p6_semantic_receipt_recorded
            or self.gate_two.verdict is not QaVerdict.PASS
            or self.render_output_sha256 is None
            or self.final_acceptance_content_hash is None
        ):
            raise ValueError(
                "Final Acceptance requires the complete exact Gate closure"
            )
        return self


class EcommerceAdProductionResult(StrictModel):
    """End-to-end result whose completion means exact Final Acceptance."""

    shot_generation: EcommerceAdGenerationResult
    post_media_acceptance: EcommercePostMediaAcceptanceResult | None = None

    @model_validator(mode="after")
    def _validate_production_result(self) -> "EcommerceAdProductionResult":
        if self.shot_generation.complete != (self.post_media_acceptance is not None):
            raise ValueError(
                "Complete Ecommerce Shot execution must enter post-media acceptance"
            )
        return self

    @property
    def complete(self) -> bool:
        return bool(
            self.post_media_acceptance is not None
            and self.post_media_acceptance.final_acceptance_recorded
        )


def _stopped(
    activated: list[ActivatedCommercialShotCheckpoint],
    *,
    shot_id: str,
    reason: EcommerceStopReason,
) -> EcommerceAdGenerationResult:
    return EcommerceAdGenerationResult(
        complete=False,
        activated_shots=tuple(activated),
        stopped_shot_id=shot_id,
        stop_reason=reason,
    )


def _checkpoint_is_exact(
    checkpoint: ActivatedCommercialShotCheckpoint | None,
    *,
    plan_hash: str,
    projection_hash: str,
    shot_id: str,
) -> bool:
    if not isinstance(checkpoint, ActivatedCommercialShotCheckpoint):
        return False
    try:
        reopened = ActivatedCommercialShotCheckpoint.model_validate(
            checkpoint.model_dump(mode="json")
        )
    except ValueError:
        return False
    return (
        reopened.ad_creative_plan_hash == plan_hash
        and reopened.commercial_execution_projection_hash == projection_hash
        and reopened.shot_id == shot_id
        and reopened.verdict is QaVerdict.PASS
        and reopened.activated is True
    )


def _run_claimed_shot(
    *,
    plan_hash: str,
    projection_hash: str,
    shot_id: str,
    facade: EcommerceShotExecutionFacade,
    should_stop: Callable[[], bool],
    activated: list[ActivatedCommercialShotCheckpoint],
) -> EcommerceAdGenerationResult | ActivatedCommercialShotCheckpoint:
    dispatch = {
        EcommerceShotNextAction.START: "start",
        EcommerceShotNextAction.SUBMIT: "submit",
        EcommerceShotNextAction.POLL: "poll",
        EcommerceShotNextAction.FETCH: "fetch",
    }
    while True:
        if should_stop():
            return _stopped(
                activated,
                shot_id=shot_id,
                reason=EcommerceStopReason.USER_STOP,
            )
        try:
            action = EcommerceShotNextAction(facade.next_action())
            if action is EcommerceShotNextAction.STOP:
                return _stopped(
                    activated,
                    shot_id=shot_id,
                    reason=EcommerceStopReason.SERVICE_STOP,
                )
            if action is EcommerceShotNextAction.DONE:
                checkpoint = facade.current_activation_checkpoint()
                if not _checkpoint_is_exact(
                    checkpoint,
                    plan_hash=plan_hash,
                    projection_hash=projection_hash,
                    shot_id=shot_id,
                ):
                    return _stopped(
                        activated,
                        shot_id=shot_id,
                        reason=EcommerceStopReason.CHECKPOINT_INVALID,
                    )
                return checkpoint
            method_name = dispatch.get(action)
            if method_name is not None:
                getattr(facade, method_name)()
                continue
            if action is EcommerceShotNextAction.VALIDATE:
                verdict = facade.validate()
                if verdict is not QaVerdict.PASS:
                    return _stopped(
                        activated,
                        shot_id=shot_id,
                        reason=EcommerceStopReason.SHOT_NOT_PASS,
                    )
                continue
            if action is EcommerceShotNextAction.ACTIVATE:
                if facade.current_validation_verdict() is not QaVerdict.PASS:
                    return _stopped(
                        activated,
                        shot_id=shot_id,
                        reason=EcommerceStopReason.SHOT_NOT_PASS,
                    )
                checkpoint = facade.activate()
                if not _checkpoint_is_exact(
                    checkpoint,
                    plan_hash=plan_hash,
                    projection_hash=projection_hash,
                    shot_id=shot_id,
                ):
                    return _stopped(
                        activated,
                        shot_id=shot_id,
                        reason=EcommerceStopReason.CHECKPOINT_INVALID,
                    )
                continue
        except (AiVideoError, ValueError):
            return _stopped(
                activated,
                shot_id=shot_id,
                reason=EcommerceStopReason.SERVICE_STOP,
            )


def run_ecommerce_ad_generation(
    handoff: CompiledAdCreativeHandoff,
    *,
    facades: Mapping[str, EcommerceVideoGenerationFacade],
    stop_requested: Callable[[], bool] | None = None,
) -> EcommerceAdGenerationResult:
    """Run Provider Shots strictly in proposal order with a synchronous PASS barrier."""

    selected = CompiledAdCreativeHandoff.model_validate(
        handoff.model_dump(mode="python")
    )
    proposal_ids = tuple(item.shot_id for item in selected.shot_proposals)
    projection_by_shot = {
        item.target_shot_id: item for item in selected.commercial_execution_projections
    }
    if set(projection_by_shot) != set(proposal_ids):
        raise ValueError("Commercial projections must cover exact proposed Shot IDs")
    provider_shot_ids = tuple(
        shot_id
        for shot_id in proposal_ids
        if projection_by_shot[shot_id].invoke_video_provider
    )
    if set(facades) != set(provider_shot_ids):
        raise ValueError("Preselected Shot service facades do not match Provider Shots")

    for shot_id in provider_shot_ids:
        projection = projection_by_shot[shot_id]
        try:
            identity = facades[shot_id].bound_commercial_identity()
        except (AttributeError, TypeError, ValueError):
            identity = None
        if identity != (
            selected.plan_content_hash,
            projection.projection_hash,
            shot_id,
        ):
            return _stopped(
                [],
                shot_id=shot_id,
                reason=EcommerceStopReason.CHECKPOINT_INVALID,
            )

    should_stop = stop_requested or (lambda: False)
    activated: list[ActivatedCommercialShotCheckpoint] = []
    for shot_id in provider_shot_ids:
        projection = projection_by_shot[shot_id]
        facade = facades[shot_id]
        if should_stop():
            return _stopped(
                activated,
                shot_id=shot_id,
                reason=EcommerceStopReason.USER_STOP,
            )
        guard_factory = getattr(facade, "execution_guard", None)
        guard = nullcontext() if guard_factory is None else guard_factory()
        try:
            with guard:
                try:
                    guarded_identity = facade.bound_commercial_identity()
                except (AttributeError, TypeError, ValueError):
                    guarded_identity = None
                if guarded_identity != (
                    selected.plan_content_hash,
                    projection.projection_hash,
                    shot_id,
                ):
                    return _stopped(
                        activated,
                        shot_id=shot_id,
                        reason=EcommerceStopReason.CHECKPOINT_INVALID,
                    )
                outcome = _run_claimed_shot(
                    plan_hash=selected.plan_content_hash,
                    projection_hash=projection.projection_hash,
                    shot_id=shot_id,
                    facade=facade,
                    should_stop=should_stop,
                    activated=activated,
                )
        except AiVideoError:
            return _stopped(
                activated,
                shot_id=shot_id,
                reason=EcommerceStopReason.SERVICE_STOP,
            )
        if isinstance(outcome, EcommerceAdGenerationResult):
            return outcome
        activated.append(outcome)

    return EcommerceAdGenerationResult(
        complete=True,
        activated_shots=tuple(activated),
    )


def _close_ecommerce_post_media_candidate(
    *,
    committer: ProductionStateCommitter,
    handoff: CompiledAdCreativeHandoff,
    shot_facades: Mapping[str, EcommerceVideoGenerationFacade],
    universal_profile: UniversalQaProfile,
    run_hard_check: HardCheckRunner,
    run_review_layer: ReviewLayerRunner,
    caption_review_execution: CaptionReviewExecution | None,
    tool_identity: ToolIdentity,
    evaluate: EcommerceWholeAdEvaluator,
    review_attempt_id: str,
    review_request_id: str,
    evidence_id: str,
    review_id: str,
    final_acceptance_id: str,
) -> EcommercePostMediaAcceptanceResult:
    """Close an already-active canonical render through Gate 2, P6, and Final Acceptance.

    This function never accepts a file path or arbitrary MP4. The exact bytes must
    already be the current Production render bound by ``timeline`` and Gate 1.
    """

    bundle, timeline = committer.current_final_media_target()
    policy = bundle.qa_policy
    render_state = bundle.render_state
    if (
        policy is None
        or render_state is None
        or bundle.manifest.active_dependency_graph is None
        or bundle.manifest.active_render_state is None
    ):
        raise ValueError(
            "Ecommerce closure requires current canonical Production state"
        )

    actual_applicability = UniversalQaApplicability(
        has_audio=bool(timeline.audio_spans),
        has_captions=bool(timeline.caption_cues),
        has_graphics=bool(timeline.commercial_graphics)
        or any(item.graphic_animation is not None for item in timeline.visual_spans),
        has_safe_area_requirements=(
            universal_profile.applicability.has_safe_area_requirements
        ),
        has_transitions=any(
            item.incoming_transition is not None for item in timeline.visual_spans
        ),
        requires_continuity=universal_profile.applicability.requires_continuity,
    )
    universal_context = UniversalQaContext(
        delivery_profile=timeline.delivery_profile,
        applicability=actual_applicability,
        project_content_hash=bundle.manifest.active_project.content_hash,
        registry_content_hash=bundle.manifest.active_registry.content_hash,
        dependency_graph_revision_id=(
            bundle.manifest.active_dependency_graph.revision_id
        ),
        render_state_content_hash=bundle.manifest.active_render_state.content_hash,
        render_output_sha256=render_state.output.file_sha256,
        timeline_fingerprint=render_state.timeline_fingerprint,
        qa_policy_content_hash=policy.content_hash,
    )
    run_canonical_review_layer = caption_aware_review_layer_runner(
        committer=committer,
        profile=universal_profile,
        context=universal_context,
        policy=policy,
        execution=caption_review_execution,
        fallback=run_review_layer,
    )

    universal_result = UniversalQualityGateCoordinator().run_once(
        profile=universal_profile,
        context=universal_context,
        policy=policy,
        run_hard_check=run_hard_check,
        run_review_layer=run_canonical_review_layer,
    )

    projection_by_shot = {
        item.target_shot_id: item for item in handoff.commercial_execution_projections
    }
    provider_shot_ids = tuple(
        item.shot_id
        for item in handoff.shot_proposals
        if projection_by_shot[item.shot_id].invoke_video_provider
    )
    if set(shot_facades) != set(provider_shot_ids):
        raise ValueError(
            "Current Provider Shot sources do not match the Ecommerce plan"
        )

    checkpoints: list[ActivatedCommercialShotCheckpoint] = []
    for shot_id in provider_shot_ids:
        facade = shot_facades[shot_id]
        projection = projection_by_shot[shot_id]
        if (
            not isinstance(facade, EcommerceVideoGenerationFacade)
            or facade.service.project_root.resolve() != committer.project_root.resolve()
            or facade.bound_commercial_identity()
            != (handoff.plan_content_hash, projection.projection_hash, shot_id)
        ):
            raise ValueError(
                "Ecommerce Shot source is not bound to current Production state"
            )
        checkpoint = facade.current_activation_checkpoint()
        if not _checkpoint_is_exact(
            checkpoint,
            plan_hash=handoff.plan_content_hash,
            projection_hash=projection.projection_hash,
            shot_id=shot_id,
        ):
            raise ValueError("Ecommerce Shot checkpoint is not current and activated")
        assert checkpoint is not None
        checkpoints.append(checkpoint)

    accepted_shots = tuple(
        EcommerceAcceptedShotIdentity.create(
            ad_creative_plan_hash=item.ad_creative_plan_hash,
            commercial_execution_projection_hash=(
                item.commercial_execution_projection_hash
            ),
            shot_id=item.shot_id,
            resolved_generation_hash=item.resolved_generation_hash,
            artifact_sha256=item.artifact_sha256,
            commercial_evidence_content_hash=item.commercial_evidence_content_hash,
            checkpoint_content_hash=item.content_hash,
        )
        for item in checkpoints
    )
    review = _record_ecommerce_gate_review(
        committer=committer,
        universal_profile=universal_profile,
        universal_context=universal_context,
        universal_result=universal_result,
        policy=policy,
        handoff=handoff,
        accepted_shots=accepted_shots,
        tool_identity=tool_identity,
        evaluate=evaluate,
        attempt_id=review_attempt_id,
        request_id=review_request_id,
        evidence_id=evidence_id,
        review_id=review_id,
    )
    if (
        review.gate.result.verdict is not QaVerdict.PASS
        or not review.p6_receipt_recorded
    ):
        return EcommercePostMediaAcceptanceResult(
            shot_stage_complete=True,
            gate_two=review.gate.result,
            p6_semantic_receipt_recorded=review.p6_receipt_recorded,
        )

    bundle = load_production_project(committer.project_root / "project.yaml")
    manifest = bundle.manifest
    render_state = bundle.render_state
    if (
        manifest.active_dependency_graph is None
        or manifest.active_render_state is None
        or manifest.active_qa_policy is None
        or render_state is None
    ):
        raise ValueError("Final Acceptance requires current canonical Production state")
    required_layers = {
        layer
        for layer in policy.required_layers
        if layer is not QaLayer.FINAL_ACCEPTANCE
    }
    current_receipts = tuple(
        item
        for item in manifest.active_review_receipts
        if item.layer in required_layers
    )
    if {item.layer for item in current_receipts} != required_layers:
        raise ValueError(
            "Final Acceptance requires all current Gate 1 and Gate 2 receipts"
        )
    acceptance = seal_artifact(
        FinalAcceptanceReceipt(
            schema_version=(
                "2.1" if QaLayer.CAPTION in required_layers else "2.0"
            ),
            artifact_id=final_acceptance_id,
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id=final_acceptance_id,
            source_provenance=(
                SourceReference(
                    kind="derived", reference=review.gate.result.content_hash
                ),
            ),
            acceptance_id=final_acceptance_id,
            dependency_graph=manifest.active_dependency_graph,
            dependency_states_hash=canonical_sha256(
                {
                    "dependency_states": [
                        item.model_dump(mode="json")
                        for item in manifest.dependency_states
                    ]
                }
            ),
            render_state=manifest.active_render_state,
            render_output_sha256=render_state.output.file_sha256,
            timeline_fingerprint=render_state.timeline_fingerprint,
            qa_policy=manifest.active_qa_policy,
            required_review_receipts=current_receipts,
            verdict=QaVerdict.PASS,
        )
    )
    accepted = committer.record_final_acceptance(
        acceptance,
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id=final_acceptance_id,
    )
    if accepted.final_acceptance_state is None:
        raise ValueError("Final Acceptance was not recorded")
    return EcommercePostMediaAcceptanceResult(
        shot_stage_complete=True,
        gate_two=review.gate.result,
        p6_semantic_receipt_recorded=True,
        final_acceptance_recorded=True,
        render_output_sha256=render_state.output.file_sha256,
        final_acceptance_content_hash=acceptance.content_hash,
    )


def run_ecommerce_ad_production(
    handoff: CompiledAdCreativeHandoff,
    *,
    facades: Mapping[str, EcommerceVideoGenerationFacade],
    activate_final_render: Callable[
        [CompiledAdCreativeHandoff, EcommerceAdGenerationResult], None
    ],
    committer: ProductionStateCommitter,
    universal_profile: UniversalQaProfile,
    run_hard_check: HardCheckRunner,
    run_review_layer: ReviewLayerRunner,
    caption_review_execution: CaptionReviewExecution | None = None,
    tool_identity: ToolIdentity,
    evaluate: EcommerceWholeAdEvaluator,
    review_attempt_id: str,
    review_request_id: str,
    evidence_id: str,
    review_id: str,
    final_acceptance_id: str,
    stop_requested: Callable[[], bool] | None = None,
) -> EcommerceAdProductionResult:
    """Run the canonical Ecommerce Shot-to-Final-Acceptance application path."""

    selected = CompiledAdCreativeHandoff.model_validate(
        handoff.model_dump(mode="python")
    )
    projection_by_shot = {
        item.target_shot_id: item for item in selected.commercial_execution_projections
    }
    provider_shot_ids = tuple(
        item.shot_id
        for item in selected.shot_proposals
        if projection_by_shot[item.shot_id].invoke_video_provider
    )
    if set(facades) != set(provider_shot_ids):
        raise ValueError("Production facades do not match the Ecommerce Provider Shots")
    for shot_id in provider_shot_ids:
        facade = facades[shot_id]
        projection = projection_by_shot[shot_id]
        if (
            not isinstance(facade, EcommerceVideoGenerationFacade)
            or facade.service.project_root.resolve() != committer.project_root.resolve()
            or facade.bound_commercial_identity()
            != (selected.plan_content_hash, projection.projection_hash, shot_id)
        ):
            raise ValueError(
                "Production Shot facade is not owned by the current Ecommerce project"
            )
    generation = run_ecommerce_ad_generation(
        selected,
        facades=facades,
        stop_requested=stop_requested,
    )
    if not generation.complete:
        return EcommerceAdProductionResult(shot_generation=generation)

    activate_final_render(selected, generation)
    post_media = _close_ecommerce_post_media_candidate(
        committer=committer,
        handoff=selected,
        shot_facades=facades,
        universal_profile=universal_profile,
        run_hard_check=run_hard_check,
        run_review_layer=run_review_layer,
        caption_review_execution=caption_review_execution,
        tool_identity=tool_identity,
        evaluate=evaluate,
        review_attempt_id=review_attempt_id,
        review_request_id=review_request_id,
        evidence_id=evidence_id,
        review_id=review_id,
        final_acceptance_id=final_acceptance_id,
    )
    return EcommerceAdProductionResult(
        shot_generation=generation,
        post_media_acceptance=post_media,
    )


__all__ = [
    "ActivatedCommercialShotCheckpoint",
    "EcommerceAdGenerationResult",
    "EcommerceAdProductionResult",
    "EcommercePostMediaAcceptanceResult",
    "EcommerceShotExecutionFacade",
    "EcommerceVideoGenerationFacade",
    "EcommerceShotNextAction",
    "EcommerceStopReason",
    "run_ecommerce_ad_generation",
    "run_ecommerce_ad_production",
]
