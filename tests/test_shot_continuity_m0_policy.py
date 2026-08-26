from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.shot_continuity_m0_policy import (
    M0ValidationPolicy,
    M0ValidationPolicyCatalog,
    M0ValidationPolicyId,
    M0ValidationSelection,
)


def _policy(policy_id: M0ValidationPolicyId) -> M0ValidationPolicy:
    if policy_id is M0ValidationPolicyId.FAST_V1:
        digit = "1"
        capability_id = "m0-fast-qualification"
    else:
        digit = "2"
        capability_id = "m0-quality-qualification"
    return M0ValidationPolicy.create(
        policy_id=policy_id,
        profile_document_hash=digit * 64,
        execution_stack_hash=("3" if digit == "1" else "4") * 64,
        rubric_hash="5" * 64,
        conclusion_scope="m0_qualification",
        conclusion_capability_id=capability_id,
    )


def _catalog() -> M0ValidationPolicyCatalog:
    return M0ValidationPolicyCatalog(
        policies=(
            _policy(M0ValidationPolicyId.FAST_V1),
            _policy(M0ValidationPolicyId.QUALITY_V1),
        )
    )


def test_policy_is_immutable_content_addressed_and_rejects_tampering() -> None:
    policy = _policy(M0ValidationPolicyId.FAST_V1)

    assert policy.policy_hash == policy.expected_policy_hash()
    with pytest.raises(ValidationError, match="policy hash"):
        M0ValidationPolicy.model_validate(
            {
                **policy.model_dump(mode="json"),
                "profile_document_hash": "9" * 64,
            }
        )
    with pytest.raises(ValidationError, match="frozen"):
        policy.rubric_hash = "8" * 64  # type: ignore[misc]


def test_selection_is_explicit_and_exactly_bound_to_registered_policy() -> None:
    catalog = _catalog()
    policy = catalog.resolve(M0ValidationPolicyId.FAST_V1)
    selection = M0ValidationSelection.from_policy(policy)

    assert catalog.resolve_selection(selection) == policy
    with pytest.raises(ValidationError, match="Field required"):
        M0ValidationSelection.model_validate(
            {
                "policy_hash": policy.policy_hash,
                "profile_document_hash": policy.profile_document_hash,
                "execution_stack_hash": policy.execution_stack_hash,
                "rubric_hash": policy.rubric_hash,
                "conclusion_scope": "m0_qualification",
            }
        )


@pytest.mark.parametrize("policy_id", (None, "draft-v1", "FAST"))
def test_missing_or_unknown_policy_never_resolves(
    policy_id: str | None,
) -> None:
    with pytest.raises(AiVideoError) as caught:
        _catalog().resolve(policy_id)

    assert caught.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert caught.value.retryable is False


def test_fast_and_quality_policies_are_not_interchangeable_or_fallbacks() -> None:
    catalog = _catalog()
    fast = catalog.resolve(M0ValidationPolicyId.FAST_V1)
    quality = catalog.resolve(M0ValidationPolicyId.QUALITY_V1)
    fast_selection = M0ValidationSelection.from_policy(fast)
    mixed_selection = fast_selection.model_copy(
        update={
            "policy_id": quality.policy_id,
            "policy_hash": quality.policy_hash,
        }
    )

    assert fast.policy_hash != quality.policy_hash
    assert fast.profile_document_hash != quality.profile_document_hash
    assert fast.execution_stack_hash != quality.execution_stack_hash
    with pytest.raises(AiVideoError, match="does not match"):
        catalog.resolve_selection(mixed_selection)
    with pytest.raises(AiVideoError, match="required"):
        catalog.resolve_selection(None)


def test_catalog_rejects_interchangeable_policy_identities() -> None:
    fast = _policy(M0ValidationPolicyId.FAST_V1)
    quality = _policy(M0ValidationPolicyId.QUALITY_V1)
    interchangeable_quality = M0ValidationPolicy.create(
        policy_id=quality.policy_id,
        profile_document_hash=fast.profile_document_hash,
        execution_stack_hash=quality.execution_stack_hash,
        rubric_hash=quality.rubric_hash,
        conclusion_scope=quality.conclusion_scope,
        conclusion_capability_id=quality.conclusion_capability_id,
    )

    with pytest.raises(ValidationError, match="non-interchangeable"):
        M0ValidationPolicyCatalog(policies=(fast, interchangeable_quality))


def test_catalog_requires_one_frozen_rubric_for_both_policies() -> None:
    fast = _policy(M0ValidationPolicyId.FAST_V1)
    quality = M0ValidationPolicy.create(
        policy_id=M0ValidationPolicyId.QUALITY_V1,
        profile_document_hash="2" * 64,
        execution_stack_hash="4" * 64,
        rubric_hash="8" * 64,
        conclusion_scope="m0_qualification",
        conclusion_capability_id="m0-quality-qualification",
    )

    with pytest.raises(ValidationError, match="same frozen rubric"):
        M0ValidationPolicyCatalog(policies=(fast, quality))


def test_policy_layer_does_not_create_a_parallel_verdict_owner() -> None:
    fields = set(M0ValidationPolicy.model_fields) | set(
        M0ValidationSelection.model_fields
    )

    assert "verdict" not in fields
    assert "findings" not in fields
