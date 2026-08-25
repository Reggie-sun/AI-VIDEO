"""Sequential Ecommerce Shot orchestration over preselected public service facades."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from enum import Enum
from typing import Literal, Protocol

from pydantic import Field, model_validator

from ai_video.errors import AiVideoError
from ai_video.production.ad_creative_types import CompiledAdCreativeHandoff
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import QaVerdict


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
    "EcommerceShotNextAction",
    "EcommerceStopReason",
    "run_ecommerce_ad_generation",
]
