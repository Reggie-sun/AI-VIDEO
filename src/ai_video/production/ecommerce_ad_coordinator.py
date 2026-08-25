"""Sequential Ecommerce Shot orchestration over preselected public service facades."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Protocol

from pydantic import Field, model_validator

from ai_video.errors import AiVideoError
from ai_video.production.ad_creative_types import CompiledAdCreativeHandoff
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import QaVerdict
from ai_video.production.paid_provider import PaidProviderCallPreview
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
    _started: bool = False

    def __post_init__(self) -> None:
        if self.request.commercial_binding is None:
            raise ValueError("Ecommerce facade requires a commercial-bound request")
        if self.lane == "paid" and (
            self.paid_preview is None or self.reservation_id is None
        ):
            raise ValueError("Paid Ecommerce facade requires preview and reservation")

    def bound_commercial_identity(self) -> tuple[str, str, str]:
        binding = self.request.commercial_binding
        assert binding is not None
        return (
            binding.ad_creative_plan_hash,
            binding.commercial_execution_projection_hash,
            binding.target_shot_id,
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

    def start(self) -> None:
        self.service.start(attempt_id=self.attempt_id, request=self.request)
        self._started = True

    def submit(self) -> None:
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
        if self.lane == "local":
            self.service.refresh_local_once(attempt_id=self.attempt_id)
        else:
            self.service.refresh_once(attempt_id=self.attempt_id)

    def fetch(self) -> None:
        if self.lane == "local":
            self.service.fetch_local_once(attempt_id=self.attempt_id)
        else:
            self.service.fetch_once(attempt_id=self.attempt_id)

    def validate(self) -> QaVerdict:
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


def run_ecommerce_ad_generation(
    handoff: CompiledAdCreativeHandoff,
    *,
    facades: Mapping[str, EcommerceShotExecutionFacade],
    stop_requested: Callable[[], bool] | None = None,
) -> EcommerceAdGenerationResult:
    """Run Provider Shots strictly in proposal order with a synchronous PASS barrier."""

    selected = CompiledAdCreativeHandoff.model_validate(
        handoff.model_dump(mode="python")
    )
    proposal_ids = tuple(item.shot_id for item in selected.shot_proposals)
    projection_by_shot = {
        item.target_shot_id: item
        for item in selected.commercial_execution_projections
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
    dispatch = {
        EcommerceShotNextAction.START: "start",
        EcommerceShotNextAction.SUBMIT: "submit",
        EcommerceShotNextAction.POLL: "poll",
        EcommerceShotNextAction.FETCH: "fetch",
    }
    for shot_id in provider_shot_ids:
        projection = projection_by_shot[shot_id]
        facade = facades[shot_id]
        if should_stop():
            return _stopped(
                activated,
                shot_id=shot_id,
                reason=EcommerceStopReason.USER_STOP,
            )
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
                        plan_hash=selected.plan_content_hash,
                        projection_hash=projection.projection_hash,
                        shot_id=shot_id,
                    ):
                        return _stopped(
                            activated,
                            shot_id=shot_id,
                            reason=EcommerceStopReason.CHECKPOINT_INVALID,
                        )
                    activated.append(checkpoint)
                    break
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
                        plan_hash=selected.plan_content_hash,
                        projection_hash=projection.projection_hash,
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

    return EcommerceAdGenerationResult(
        complete=True,
        activated_shots=tuple(activated),
    )


__all__ = [
    "ActivatedCommercialShotCheckpoint",
    "EcommerceAdGenerationResult",
    "EcommerceShotExecutionFacade",
    "EcommerceVideoGenerationFacade",
    "EcommerceShotNextAction",
    "EcommerceStopReason",
    "run_ecommerce_ad_generation",
]
