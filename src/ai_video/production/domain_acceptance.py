"""Generic sealed policy binding for one selected domain acceptance profile."""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator, model_validator

from ai_video.production._immutable_models import ImmutableDict
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256


def _deep_immutable_json(value: object) -> object:
    if isinstance(value, dict):
        return ImmutableDict(
            {key: _deep_immutable_json(item) for key, item in value.items()}
        )
    if isinstance(value, list | tuple):
        return tuple(_deep_immutable_json(item) for item in value)
    return value


class DomainAcceptancePolicy(StrictModel):
    """Bind a content-addressed domain profile into the selected QA policy."""

    domain_id: str = Field(min_length=1)
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    profile_payload: dict[str, Any]
    measurement_contract_version: str = Field(min_length=1)
    required_requirement_ids: tuple[str, ...] = Field(min_length=1)

    @field_validator("profile_payload")
    @classmethod
    def _freeze_profile_payload(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _deep_immutable_json(value)  # type: ignore[return-value]

    @model_validator(mode="after")
    def _validate_profile_binding(self) -> "DomainAcceptancePolicy":
        requirement_ids = self.required_requirement_ids
        if any(not item.strip() for item in requirement_ids):
            raise ValueError("Domain acceptance requirement IDs must be nonblank")
        if len(set(requirement_ids)) != len(requirement_ids):
            raise ValueError("Domain acceptance requirement IDs must be unique")

        payload = dict(self.profile_payload)
        declared_hash = payload.pop("content_hash", None)
        if declared_hash != self.profile_content_hash:
            raise ValueError("Domain acceptance profile hash does not match payload")
        if canonical_sha256(payload) != self.profile_content_hash:
            raise ValueError("Domain acceptance profile payload is not sealed")
        expected_identity = {
            "domain_id": self.domain_id,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "measurement_contract_version": self.measurement_contract_version,
        }
        if any(self.profile_payload.get(key) != value for key, value in expected_identity.items()):
            raise ValueError("Domain acceptance profile identity does not match policy")
        if tuple(self.profile_payload.get("required_requirement_ids", ())) != requirement_ids:
            raise ValueError("Domain acceptance requirement coverage does not match profile")
        return self
