"""Immutable policy selection and result projection for M0 qualification."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256


_SHA256 = r"^[0-9a-f]{64}$"
_POLICY_SCHEMA = "m0-validation-policy/1"


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class M0ValidationPolicyId(str, Enum):
    FAST_V1 = "fast-v1"
    QUALITY_V1 = "quality-v1"


class M0ValidationPolicy(StrictModel):
    """One sealed, non-interchangeable M0 validation policy."""

    policy_id: M0ValidationPolicyId
    policy_hash: str = Field(pattern=_SHA256)
    profile_document_hash: str = Field(pattern=_SHA256)
    execution_stack_hash: str = Field(pattern=_SHA256)
    rubric_hash: str = Field(pattern=_SHA256)
    conclusion_scope: Literal["m0_qualification"]
    conclusion_capability_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_policy_hash(self) -> "M0ValidationPolicy":
        if self.policy_hash != self.expected_policy_hash():
            raise ValueError("M0 validation policy hash is invalid")
        return self

    def expected_policy_hash(self) -> str:
        return canonical_sha256(
            {
                "schema": _POLICY_SCHEMA,
                **self.model_dump(mode="json", exclude={"policy_hash"}),
            }
        )

    @classmethod
    def create(cls, **values: object) -> "M0ValidationPolicy":
        provisional = cls.model_construct(**values, policy_hash="0" * 64)
        return cls.model_validate(
            {
                **values,
                "policy_hash": canonical_sha256(
                    {
                        "schema": _POLICY_SCHEMA,
                        **provisional.model_dump(
                            mode="json",
                            exclude={"policy_hash"},
                            warnings=False,
                        ),
                    }
                ),
            }
        )


class M0ValidationSelection(StrictModel):
    """Explicit user selection bound to every identity that affects its verdict."""

    policy_id: M0ValidationPolicyId
    policy_hash: str = Field(pattern=_SHA256)
    profile_document_hash: str = Field(pattern=_SHA256)
    execution_stack_hash: str = Field(pattern=_SHA256)
    rubric_hash: str = Field(pattern=_SHA256)
    conclusion_scope: Literal["m0_qualification"]

    @classmethod
    def from_policy(cls, policy: M0ValidationPolicy) -> "M0ValidationSelection":
        validated = M0ValidationPolicy.model_validate(policy.model_dump(mode="json"))
        return cls(
            policy_id=validated.policy_id,
            policy_hash=validated.policy_hash,
            profile_document_hash=validated.profile_document_hash,
            execution_stack_hash=validated.execution_stack_hash,
            rubric_hash=validated.rubric_hash,
            conclusion_scope=validated.conclusion_scope,
        )


class M0ValidationPolicyCatalog(StrictModel):
    """Resolve only the two explicitly registered M0 policies, without fallback."""

    policies: tuple[M0ValidationPolicy, ...] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def _validate_catalog(self) -> "M0ValidationPolicyCatalog":
        validated = tuple(
            M0ValidationPolicy.model_validate(item.model_dump(mode="json"))
            for item in self.policies
        )
        expected_ids = set(M0ValidationPolicyId)
        if {item.policy_id for item in validated} != expected_ids:
            raise ValueError("M0 validation catalog requires fast-v1 and quality-v1")
        for label, values in (
            ("policy hashes", {item.policy_hash for item in validated}),
            (
                "profile document hashes",
                {item.profile_document_hash for item in validated},
            ),
            (
                "execution stack hashes",
                {item.execution_stack_hash for item in validated},
            ),
            (
                "conclusion capability IDs",
                {item.conclusion_capability_id for item in validated},
            ),
        ):
            if len(values) != len(validated):
                raise ValueError(f"M0 validation {label} must be non-interchangeable")
        if len({item.rubric_hash for item in validated}) != 1:
            raise ValueError(
                "M0 validation policies must use the same frozen rubric"
            )
        return self

    def resolve(
        self, policy_id: M0ValidationPolicyId | str | None
    ) -> M0ValidationPolicy:
        if policy_id is None:
            raise _invalid("M0 validation policy selection is required.")
        try:
            selected_id = M0ValidationPolicyId(policy_id)
        except ValueError as exc:
            raise _invalid(
                "M0 validation policy selection is unknown.",
                detail=str(policy_id),
            ) from exc
        for policy in self.policies:
            if policy.policy_id is selected_id:
                try:
                    return M0ValidationPolicy.model_validate(
                        policy.model_dump(mode="json")
                    )
                except ValidationError as exc:
                    raise _invalid(
                        "M0 validation policy identity is invalid.",
                        detail=selected_id.value,
                    ) from exc
        raise _invalid(
            "M0 validation policy selection is not registered.",
            detail=selected_id.value,
        )

    def resolve_selection(
        self, selection: M0ValidationSelection | None
    ) -> M0ValidationPolicy:
        if selection is None:
            raise _invalid("M0 validation policy selection is required.")
        try:
            selected = M0ValidationSelection.model_validate(
                selection.model_dump(mode="json")
            )
        except ValidationError as exc:
            raise _invalid("M0 validation policy selection is invalid.") from exc
        policy = self.resolve(selected.policy_id)
        expected = M0ValidationSelection.from_policy(policy)
        if selected != expected:
            raise _invalid(
                "M0 validation policy selection does not match the registered policy.",
                detail=selected.policy_id.value,
            )
        return policy
