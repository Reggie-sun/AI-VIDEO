"""Provider-neutral safety contracts for remote metered submissions."""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Literal, Protocol
from urllib.parse import urlsplit

from pydantic import ConfigDict, Field, field_validator, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity, StrictModel


_SAFE_ID = re.compile(r"^[A-Za-z0-9._:/-]{1,512}$")
_SAFE_SHORT_ID = re.compile(r"^[A-Za-z0-9._:/-]{1,256}$")
_EXTERNAL_EFFECT_ID = re.compile(r"^[A-Za-z0-9._:/-]{1,512}$")


def _paid_error(code: ErrorCode, message: str) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, retryable=False)


def _canonical_https_origin(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("paid Provider destination must be a canonical HTTPS origin") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("paid Provider destination must be a canonical HTTPS origin")
    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    canonical = f"https://{host}"
    if port is not None and port != 443:
        canonical = f"{canonical}:{port}"
    if value != canonical:
        raise ValueError("paid Provider destination must be a canonical HTTPS origin")
    return value


class _PaidStrictModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class SecretReference(_PaidStrictModel):
    kind: Literal["environment", "secret_store"]
    reference_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)


class PaidProviderEgressItem(_PaidStrictModel):
    item_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(strict=True, ge=0)
    mime_type: str = Field(pattern=r"^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$")
    purpose: Literal["prompt", "reference", "script", "settings", "metadata"]


class PaidProviderCallPreview(_PaidStrictModel):
    attempt_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    operation: Literal["voice_generation", "video_generation"]
    provider_kind: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    model_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    billing_mode: Literal["remote_metered"]
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    estimated_cost_upper_bound_microunits: int = Field(strict=True, ge=0)
    destination: str
    method: Literal["POST"]
    egress_items: tuple[PaidProviderEgressItem, ...] = Field(min_length=1)
    retention_mode: Literal["provider_standard", "zero_retention"]
    provider_policy_snapshot_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    secret_reference: SecretReference
    preview_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("destination")
    @classmethod
    def _destination_is_canonical(cls, value: str) -> str:
        return _canonical_https_origin(value)

    @model_validator(mode="after")
    def _validate_seal(self) -> "PaidProviderCallPreview":
        if len({item.item_id for item in self.egress_items}) != len(self.egress_items):
            raise ValueError("paid Provider egress item IDs must be unique")
        data = self.model_dump(mode="json", exclude={"preview_fingerprint"})
        if canonical_sha256(data) != self.preview_fingerprint:
            raise ValueError("preview_fingerprint does not match paid Provider preview")
        return self

    @classmethod
    def create(cls, **values: object) -> "PaidProviderCallPreview":
        data = dict(values)
        candidate = cls.model_construct(**data, preview_fingerprint="0" * 64)
        data["preview_fingerprint"] = canonical_sha256(
            candidate.model_dump(
                mode="json", exclude={"preview_fingerprint"}, warnings=False
            )
        )
        return cls.model_validate(data)


class PaidProviderAuthorizationDecision(_PaidStrictModel):
    attempt_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    preview_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    explicit_opt_in: Literal[True]
    actor: ActorIdentity
    opt_in_policy_receipt_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    budget_policy_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    budget_currency: str = Field(pattern=r"^[A-Z]{3}$")
    project_budget_ceiling_microunits: int = Field(strict=True, gt=0)
    per_call_ceiling_microunits: int = Field(strict=True, ge=0)
    egress_authorized: Literal[True]
    egress_policy_receipt_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    live_test_authorized: Literal[True]
    live_authorization_receipt_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    issued_at: datetime
    expires_at: datetime
    max_submit_count: Literal[1]
    authorization_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_seal_and_time(self) -> "PaidProviderAuthorizationDecision":
        if self.issued_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("paid Provider authorization timestamps must be timezone-aware")
        if self.expires_at <= self.issued_at:
            raise ValueError("paid Provider authorization must expire after issue")
        data = self.model_dump(mode="json", exclude={"authorization_fingerprint"})
        if canonical_sha256(data) != self.authorization_fingerprint:
            raise ValueError("authorization_fingerprint does not match decision")
        return self

    @classmethod
    def create(cls, **values: object) -> "PaidProviderAuthorizationDecision":
        data = dict(values)
        candidate = cls.model_construct(**data, authorization_fingerprint="0" * 64)
        data["authorization_fingerprint"] = canonical_sha256(
            candidate.model_dump(
                mode="json", exclude={"authorization_fingerprint"}, warnings=False
            )
        )
        return cls.model_validate(data)


def validate_paid_provider_authorization(
    preview: PaidProviderCallPreview,
    authorization: PaidProviderAuthorizationDecision,
    *,
    now: datetime,
) -> PaidProviderAuthorizationDecision:
    if (
        authorization.attempt_id != preview.attempt_id
        or authorization.preview_fingerprint != preview.preview_fingerprint
    ):
        raise _paid_error(
            ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
            "Paid Provider authorization does not match the exact preview.",
        )
    if authorization.budget_currency != preview.currency:
        raise _paid_error(
            ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            "Paid Provider budget currency does not match the preview.",
        )
    if authorization.per_call_ceiling_microunits < (
        preview.estimated_cost_upper_bound_microunits
    ):
        raise _paid_error(
            ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            "Paid Provider upper bound exceeds the authorized per-call ceiling.",
        )
    if now.tzinfo is None or now < authorization.issued_at or now >= authorization.expires_at:
        raise _paid_error(
            ErrorCode.PAID_PROVIDER_LIVE_AUTHORIZATION_REQUIRED,
            "Paid Provider live authorization is not current.",
        )
    return authorization


class BudgetReservationStatus(str, Enum):
    RESERVED = "reserved"
    SETTLED = "settled"
    RELEASED = "released"
    UNSETTLED = "unsettled"


class PaidProviderBudgetReservation(_PaidStrictModel):
    reservation_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    attempt_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    preview_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    upper_bound_microunits: int = Field(strict=True, ge=0)
    status: BudgetReservationStatus
    actual_cost_microunits: int | None = Field(default=None, strict=True, ge=0)
    submit_receipt_fingerprint: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )

    @model_validator(mode="after")
    def _validate_state(self) -> "PaidProviderBudgetReservation":
        if self.status is BudgetReservationStatus.SETTLED:
            if self.actual_cost_microunits is None:
                raise ValueError("settled reservation requires actual cost")
        elif self.status is BudgetReservationStatus.RELEASED:
            if self.actual_cost_microunits != 0:
                raise ValueError("released reservation requires exact zero actual cost")
        elif self.actual_cost_microunits is not None:
            raise ValueError("reserved or unsettled reservation cannot claim actual cost")
        return self


class PaidProviderBudgetSnapshot(_PaidStrictModel):
    schema_version: Literal["1"] = "1"
    revision: int = Field(strict=True, ge=1)
    policy_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    project_ceiling_microunits: int = Field(strict=True, gt=0)
    reservations: tuple[PaidProviderBudgetReservation, ...] = ()
    blocked: bool = Field(strict=True)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_seal_and_uniqueness(self) -> "PaidProviderBudgetSnapshot":
        reservation_ids = [item.reservation_id for item in self.reservations]
        attempt_ids = [item.attempt_id for item in self.reservations]
        if len(reservation_ids) != len(set(reservation_ids)):
            raise ValueError("paid Provider reservation IDs must be unique")
        if len(attempt_ids) != len(set(attempt_ids)):
            raise ValueError("paid Provider attempts can reserve only once")
        data = self.model_dump(mode="json", exclude={"content_hash"})
        if canonical_sha256(data) != self.content_hash:
            raise ValueError("paid Provider budget content hash does not match")
        return self

    @property
    def committed_microunits(self) -> int:
        total = 0
        for reservation in self.reservations:
            if reservation.status is BudgetReservationStatus.SETTLED:
                assert reservation.actual_cost_microunits is not None
                total += reservation.actual_cost_microunits
            elif reservation.status in {
                BudgetReservationStatus.RESERVED,
                BudgetReservationStatus.UNSETTLED,
            }:
                total += reservation.upper_bound_microunits
        return total

    @property
    def available_microunits(self) -> int:
        return max(0, self.project_ceiling_microunits - self.committed_microunits)

    @classmethod
    def create(cls, **values: object) -> "PaidProviderBudgetSnapshot":
        data = dict(values)
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            candidate.model_dump(mode="json", exclude={"content_hash"})
        )
        return cls.model_validate(data)


def reserve_paid_provider_budget(
    snapshot: PaidProviderBudgetSnapshot | None,
    *,
    preview: PaidProviderCallPreview,
    authorization: PaidProviderAuthorizationDecision,
    reservation_id: str,
) -> tuple[PaidProviderBudgetSnapshot, PaidProviderBudgetReservation]:
    validate_paid_provider_authorization(preview, authorization, now=authorization.issued_at)
    if snapshot is None:
        snapshot = PaidProviderBudgetSnapshot.create(
            revision=1,
            policy_id=authorization.budget_policy_id,
            currency=authorization.budget_currency,
            project_ceiling_microunits=(
                authorization.project_budget_ceiling_microunits
            ),
            reservations=(),
            blocked=False,
        )
    if snapshot.blocked:
        raise _paid_error(
            ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            "Paid Provider budget is blocked by unresolved or exceeded cost.",
        )
    if (
        snapshot.policy_id != authorization.budget_policy_id
        or snapshot.currency != authorization.budget_currency
        or snapshot.project_ceiling_microunits
        != authorization.project_budget_ceiling_microunits
    ):
        raise _paid_error(
            ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            "Paid Provider budget policy does not match the active ledger.",
        )
    if any(
        item.attempt_id == preview.attempt_id or item.reservation_id == reservation_id
        for item in snapshot.reservations
    ):
        raise _paid_error(
            ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            "Paid Provider attempt or reservation was already recorded.",
        )
    upper_bound = preview.estimated_cost_upper_bound_microunits
    if upper_bound > snapshot.available_microunits:
        raise _paid_error(
            ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            "Paid Provider budget is insufficient for the declared upper bound.",
        )
    reservation = PaidProviderBudgetReservation(
        reservation_id=reservation_id,
        attempt_id=preview.attempt_id,
        request_fingerprint=preview.request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        upper_bound_microunits=upper_bound,
        status=BudgetReservationStatus.RESERVED,
    )
    updated = PaidProviderBudgetSnapshot.create(
        revision=snapshot.revision + 1,
        policy_id=snapshot.policy_id,
        currency=snapshot.currency,
        project_ceiling_microunits=snapshot.project_ceiling_microunits,
        reservations=snapshot.reservations + (reservation,),
        blocked=False,
    )
    return updated, reservation


class PaidProviderGateReceipt(_PaidStrictModel):
    preview: PaidProviderCallPreview
    authorization: PaidProviderAuthorizationDecision
    reservation_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    budget_snapshot_revision: int = Field(strict=True, ge=1)
    budget_snapshot_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    budget_snapshot_file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    gate_receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_seal_and_binding(self) -> "PaidProviderGateReceipt":
        if (
            self.authorization.attempt_id != self.preview.attempt_id
            or self.authorization.preview_fingerprint != self.preview.preview_fingerprint
        ):
            raise ValueError("paid Provider Gate receipt identities do not match")
        data = self.model_dump(mode="json", exclude={"gate_receipt_fingerprint"})
        if canonical_sha256(data) != self.gate_receipt_fingerprint:
            raise ValueError("paid Provider Gate receipt fingerprint does not match")
        return self

    @classmethod
    def create(cls, **values: object) -> "PaidProviderGateReceipt":
        data = dict(values)
        candidate = cls.model_construct(**data, gate_receipt_fingerprint="0" * 64)
        data["gate_receipt_fingerprint"] = canonical_sha256(
            candidate.model_dump(mode="json", exclude={"gate_receipt_fingerprint"})
        )
        return cls.model_validate(data)


class PaidProviderSubmitOutcome(str, Enum):
    ACCEPTED = "accepted"
    KNOWN_NO_EFFECT = "known_no_effect"
    OUTCOME_UNKNOWN = "outcome_unknown"


class PaidProviderSubmitReceipt(_PaidStrictModel):
    attempt_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    preview_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    gate_receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    reservation_id: str = Field(pattern=_SAFE_SHORT_ID.pattern)
    outcome: PaidProviderSubmitOutcome
    external_effect_id: str | None = None
    recorded_at: datetime
    submit_receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("external_effect_id")
    @classmethod
    def _validate_effect_id(cls, value: str | None) -> str | None:
        if value is not None and _EXTERNAL_EFFECT_ID.fullmatch(value) is None:
            raise ValueError("external effect ID is invalid")
        return value

    @model_validator(mode="after")
    def _validate_seal_and_outcome(self) -> "PaidProviderSubmitReceipt":
        if self.recorded_at.tzinfo is None:
            raise ValueError("paid Provider submit receipt time must be timezone-aware")
        if self.outcome is PaidProviderSubmitOutcome.ACCEPTED:
            if self.external_effect_id is None:
                raise ValueError("accepted paid submit requires exact external effect ID")
        elif self.external_effect_id is not None:
            raise ValueError("non-accepted paid submit cannot claim an external effect ID")
        data = self.model_dump(mode="json", exclude={"submit_receipt_fingerprint"})
        if canonical_sha256(data) != self.submit_receipt_fingerprint:
            raise ValueError("paid Provider submit receipt fingerprint does not match")
        return self

    @classmethod
    def create(cls, **values: object) -> "PaidProviderSubmitReceipt":
        data = dict(values)
        candidate = cls.model_construct(**data, submit_receipt_fingerprint="0" * 64)
        data["submit_receipt_fingerprint"] = canonical_sha256(
            candidate.model_dump(mode="json", exclude={"submit_receipt_fingerprint"})
        )
        return cls.model_validate(data)


def _replace_reservation(
    snapshot: PaidProviderBudgetSnapshot,
    updated: PaidProviderBudgetReservation,
) -> PaidProviderBudgetSnapshot:
    reservations = tuple(
        updated if item.reservation_id == updated.reservation_id else item
        for item in snapshot.reservations
    )
    return PaidProviderBudgetSnapshot.create(
        revision=snapshot.revision + 1,
        policy_id=snapshot.policy_id,
        currency=snapshot.currency,
        project_ceiling_microunits=snapshot.project_ceiling_microunits,
        reservations=reservations,
        blocked=(
            snapshot.blocked
            or sum(
                item.actual_cost_microunits or 0
                for item in reservations
                if item.status is BudgetReservationStatus.SETTLED
            )
            > snapshot.project_ceiling_microunits
        ),
    )


def apply_paid_provider_submit_receipt(
    snapshot: PaidProviderBudgetSnapshot,
    receipt: PaidProviderSubmitReceipt,
) -> PaidProviderBudgetSnapshot:
    reservation = next(
        (
            item
            for item in snapshot.reservations
            if item.reservation_id == receipt.reservation_id
        ),
        None,
    )
    if (
        reservation is None
        or reservation.attempt_id != receipt.attempt_id
        or reservation.request_fingerprint != receipt.request_fingerprint
        or reservation.preview_fingerprint != receipt.preview_fingerprint
        or reservation.status is not BudgetReservationStatus.RESERVED
        or reservation.submit_receipt_fingerprint is not None
    ):
        raise _paid_error(
            ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            "Paid Provider submit receipt does not match an open reservation.",
        )
    if receipt.outcome is PaidProviderSubmitOutcome.ACCEPTED:
        status = BudgetReservationStatus.RESERVED
        actual = None
    elif receipt.outcome is PaidProviderSubmitOutcome.KNOWN_NO_EFFECT:
        status = BudgetReservationStatus.RELEASED
        actual = 0
    else:
        status = BudgetReservationStatus.UNSETTLED
        actual = None
    updated = PaidProviderBudgetReservation.model_validate(
        {
            **reservation.model_dump(mode="python"),
            "status": status,
            "actual_cost_microunits": actual,
            "submit_receipt_fingerprint": receipt.submit_receipt_fingerprint,
        }
    )
    return _replace_reservation(snapshot, updated)


def settle_paid_provider_budget(
    snapshot: PaidProviderBudgetSnapshot,
    *,
    reservation_id: str,
    actual_cost_microunits: int,
) -> PaidProviderBudgetSnapshot:
    if type(actual_cost_microunits) is not int or actual_cost_microunits < 0:
        raise _paid_error(
            ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            "Paid Provider actual cost must be a non-negative integer.",
        )
    reservation = next(
        (item for item in snapshot.reservations if item.reservation_id == reservation_id),
        None,
    )
    if reservation is None:
        raise _paid_error(
            ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            "Paid Provider reservation does not exist.",
        )
    if reservation.status is BudgetReservationStatus.UNSETTLED:
        raise _paid_error(
            ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN,
            "Paid Provider outcome is unknown and cannot be settled automatically.",
        )
    if (
        reservation.status is not BudgetReservationStatus.RESERVED
        or reservation.submit_receipt_fingerprint is None
    ):
        raise _paid_error(
            ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            "Paid Provider reservation has no accepted submit receipt to settle.",
        )
    updated = PaidProviderBudgetReservation.model_validate(
        {
            **reservation.model_dump(mode="python"),
            "status": BudgetReservationStatus.SETTLED,
            "actual_cost_microunits": actual_cost_microunits,
        }
    )
    next_snapshot = _replace_reservation(snapshot, updated)
    if actual_cost_microunits > reservation.upper_bound_microunits:
        next_snapshot = PaidProviderBudgetSnapshot.create(
            revision=next_snapshot.revision + 1,
            policy_id=next_snapshot.policy_id,
            currency=next_snapshot.currency,
            project_ceiling_microunits=next_snapshot.project_ceiling_microunits,
            reservations=next_snapshot.reservations,
            blocked=True,
        )
    return next_snapshot


class DurablePaidProviderSubmitPermit(Protocol):
    def _validate_paid_provider_operation_permit(
        self, **binding: str
    ) -> bool: ...

    def _consume_paid_provider_operation_permit(
        self, **binding: str
    ) -> bool: ...
