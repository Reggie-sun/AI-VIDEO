"""Sealed, explicit one-way extensions of a paid Provider ledger ceiling."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity, PaidProviderBudgetSnapshotPointer, StrictModel


_HASH = r"^[0-9a-f]{64}$"


class PaidProviderBudgetCeilingExtension(StrictModel):
    schema_version: Literal["paid-provider-budget-extension/1"] = "paid-provider-budget-extension/1"
    extension_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    project_id: str = Field(min_length=1)
    actor: ActorIdentity
    explicit_opt_in: Literal[True]
    authorization_receipt_id: str = Field(min_length=1)
    expected_manifest_revision: int = Field(strict=True, ge=0)
    base_budget: PaidProviderBudgetSnapshotPointer
    policy_id: str = Field(min_length=1)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    old_ceiling_microunits: int = Field(strict=True, gt=0)
    new_ceiling_microunits: int = Field(strict=True, gt=0)
    issued_at: datetime
    expires_at: datetime
    content_hash: str = Field(pattern=_HASH)

    @model_validator(mode="after")
    def _sealed(self):
        if self.new_ceiling_microunits <= self.old_ceiling_microunits:
            raise ValueError("budget extension ceiling must strictly increase")
        if self.issued_at.tzinfo is None or self.expires_at.tzinfo is None or self.expires_at <= self.issued_at:
            raise ValueError("budget extension window is invalid")
        if self.content_hash != canonical_sha256(self.model_dump(mode="json")):
            raise ValueError("budget extension content hash is invalid")
        return self

    @classmethod
    def create(cls, **values):
        data = dict(values)
        trial = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(trial.model_dump(mode="json"))
        return cls.model_validate(data)

    def valid_at(self, now: datetime) -> bool:
        return now.tzinfo is not None and self.issued_at <= now < self.expires_at
