from __future__ import annotations

from enum import Enum
import re
from typing import Annotated, Literal

from pydantic import Field, model_validator

from ai_video.planning._planner_models import (
    AssetRole,
    PlanOutcome,
    PlanWarning,
    VideoGenerationPlan,
    VideoPlanningRequest,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel
from ai_video.production.video_requirement import (
    VerifiedGenerationRequirementProjection,
)


_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"
_UNSEALED_HASH = "0" * 64
_CHECK_ORDER = (
    "request_plan_binding",
    "plan_eligibility",
    "required_asset_readiness",
)


def _canonical_hash_without(model: StrictModel, *excluded_fields: str) -> str:
    payload = model.model_dump(mode="json")
    for field in excluded_fields:
        payload.pop(field)
    return canonical_sha256(payload)


class ReadinessStatus(str, Enum):
    READY = "ready"
    BLOCKED = "blocked"


class ReadinessCheckStatus(str, Enum):
    PASS = "pass"
    BLOCKED = "blocked"


class ReadinessReason(str, Enum):
    READINESS_REQUEST_SEAL_INVALID = "readiness_request_seal_invalid"
    LEGACY_PLANNER_REOPEN_ONLY = "legacy_planner_reopen_only"
    CURRENT_PLAN_PROJECTION_INVALID = "current_plan_projection_invalid"
    VERIFIED_PROJECTION_BINDING_INVALID = (
        "verified_projection_binding_invalid"
    )
    PLAN_BLOCKED = "plan_blocked"
    HUMAN_REVIEW_UNRESOLVED = "human_review_unresolved"
    REQUIRED_ASSET_MISSING = "required_asset_missing"


class ShotReadinessRequest(StrictModel):
    request_id: str = Field(pattern=_SAFE_ID)
    current_request: VideoPlanningRequest
    plan: VideoGenerationPlan
    contract_version: Literal["shot-readiness-gate/1"] = (
        "shot-readiness-gate/1"
    )
    request_content_hash: str = Field(pattern=_SHA256)

    def _hash_payload(self) -> dict[str, object]:
        requirement = self.plan.generation_requirement
        return {
            "contract_version": self.contract_version,
            "current_request_content_hash": (
                self.current_request.request_content_hash
            ),
            "plan_hash": self.plan.plan_hash,
            "embedded_requirement_hash": (
                requirement.requirement_hash if requirement is not None else None
            ),
        }

    @classmethod
    def create(cls, **values: object) -> "ShotReadinessRequest":
        payload = dict(values)
        payload.setdefault("contract_version", "shot-readiness-gate/1")
        unexpected = set(payload) - {
            "request_id",
            "current_request",
            "plan",
            "contract_version",
        }
        if unexpected:
            raise ValueError(
                f"unexpected readiness request fields: {sorted(unexpected)}"
            )
        request_id = payload.get("request_id")
        current_request = payload.get("current_request")
        plan = payload.get("plan")
        contract_version = payload.get("contract_version")
        if not isinstance(request_id, str) or re.fullmatch(_SAFE_ID, request_id) is None:
            raise ValueError("request_id must be a safe identifier")
        if not isinstance(current_request, VideoPlanningRequest):
            raise TypeError("current_request must be a VideoPlanningRequest")
        if not isinstance(plan, VideoGenerationPlan):
            raise TypeError("plan must be a VideoGenerationPlan")
        if contract_version != "shot-readiness-gate/1":
            raise ValueError("unsupported readiness request contract")

        draft = cls.model_construct(
            request_id=request_id,
            current_request=current_request,
            plan=plan,
            contract_version=contract_version,
            request_content_hash=_UNSEALED_HASH,
        )
        return cls.model_construct(
            request_id=request_id,
            current_request=current_request,
            plan=plan,
            contract_version=contract_version,
            request_content_hash=canonical_sha256(
                draft._hash_payload()
            ),
        )


class RequestPlanBindingPayload(StrictModel):
    outer_request_seal_valid: bool
    current_v3_contract: bool
    request_seal_valid: bool
    plan_seal_valid: bool
    unique_current_derivation_valid: bool
    plan_id_valid: bool
    source_request_valid: bool
    target_shot_valid: bool
    embedded_requirement_valid: bool
    verified_projection_valid: bool
    request_content_hash: str = Field(pattern=_SHA256)
    plan_hash: str = Field(pattern=_SHA256)
    requirement_hash: str | None = Field(default=None, pattern=_SHA256)
    projection_hash: str | None = Field(default=None, pattern=_SHA256)
    failure_field_paths: tuple[str, ...] = ()


class PlanEligibilityPayload(StrictModel):
    plan_outcome: PlanOutcome
    warnings: tuple[PlanWarning, ...]
    unresolved_human_review: bool


class RequiredAssetReadinessPayload(StrictModel):
    required_roles: tuple[AssetRole, ...]
    ready_roles: tuple[AssetRole, ...]
    missing_roles: tuple[AssetRole, ...]


class _ReadinessCheck(StrictModel):
    status: ReadinessCheckStatus
    reason_codes: tuple[ReadinessReason, ...] = ()

    @model_validator(mode="after")
    def _validate_status_reasons(self) -> "_ReadinessCheck":
        if self.status is ReadinessCheckStatus.PASS and self.reason_codes:
            raise ValueError("passing readiness check cannot carry reasons")
        if self.status is ReadinessCheckStatus.BLOCKED and not self.reason_codes:
            raise ValueError("blocked readiness check requires a reason")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("readiness reason_codes must be unique")
        return self


class RequestPlanBindingOutcome(_ReadinessCheck):
    check_id: Literal["request_plan_binding"] = "request_plan_binding"
    payload: RequestPlanBindingPayload


class PlanEligibilityOutcome(_ReadinessCheck):
    check_id: Literal["plan_eligibility"] = "plan_eligibility"
    payload: PlanEligibilityPayload


class RequiredAssetReadinessOutcome(_ReadinessCheck):
    check_id: Literal["required_asset_readiness"] = (
        "required_asset_readiness"
    )
    payload: RequiredAssetReadinessPayload


ReadinessCheck = Annotated[
    RequestPlanBindingOutcome
    | PlanEligibilityOutcome
    | RequiredAssetReadinessOutcome,
    Field(discriminator="check_id"),
]


class ShotReadinessResult(StrictModel):
    status: ReadinessStatus
    checks: tuple[ReadinessCheck, ...] = Field(min_length=3, max_length=3)
    verified_generation_requirement: (
        VerifiedGenerationRequirementProjection | None
    ) = None
    result_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_result(self) -> "ShotReadinessResult":
        check_ids = tuple(check.check_id for check in self.checks)
        if check_ids != _CHECK_ORDER:
            raise ValueError("readiness checks must use the canonical order")
        any_blocked = any(
            check.status is ReadinessCheckStatus.BLOCKED
            for check in self.checks
        )
        expected_status = (
            ReadinessStatus.BLOCKED if any_blocked else ReadinessStatus.READY
        )
        if self.status is not expected_status:
            raise ValueError("readiness status contradicts check outcomes")
        if (
            self.status is ReadinessStatus.READY
        ) != (self.verified_generation_requirement is not None):
            raise ValueError("only READY result may expose verified projection")
        if self.verified_generation_requirement is not None:
            binding = self.checks[0]
            if not isinstance(binding, RequestPlanBindingOutcome):
                raise ValueError("first readiness check must be binding")
            if (
                binding.payload.projection_hash
                != self.verified_generation_requirement.projection_hash
            ):
                raise ValueError("result projection does not match binding payload")
        if self.result_hash != _canonical_hash_without(self, "result_hash"):
            raise ValueError("result_hash does not match readiness result")
        return self

    @classmethod
    def create(cls, **values: object) -> "ShotReadinessResult":
        payload = dict(values)
        candidate = cls.model_construct(
            **payload,
            result_hash=_UNSEALED_HASH,
        )
        payload["result_hash"] = _canonical_hash_without(
            candidate,
            "result_hash",
        )
        return cls.model_validate(payload)
