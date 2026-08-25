"""Explicit Gate 1-only orchestration for exact-bound Universal Production QA."""

from __future__ import annotations

import re
from collections.abc import Callable
from enum import Enum
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.composition_contracts import DeliveryProfile
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.models import QaLayer, QaPolicy, QaVerdict


_SHA256 = r"^[0-9a-f]{64}$"


class UniversalHardCheck(str, Enum):
    ASSET_PROVENANCE = "asset_provenance"
    MEDIA_DECODE = "media_decode"
    TIMELINE_BINDING = "timeline_binding"
    RENDER_OUTPUT = "render_output"
    AUDIO_CAPTION_BINDING = "audio_caption_binding"
    CONTINUITY_EVIDENCE = "continuity_evidence"


_ALWAYS_REQUIRED_HARD_CHECKS = frozenset(
    {
        UniversalHardCheck.ASSET_PROVENANCE,
        UniversalHardCheck.MEDIA_DECODE,
        UniversalHardCheck.TIMELINE_BINDING,
        UniversalHardCheck.RENDER_OUTPUT,
    }
)


class UniversalQaBlockReason(str, Enum):
    PROFILE_INVALID = "profile_invalid"
    CONTEXT_INVALID = "context_invalid"
    PROFILE_CONTEXT_MISMATCH = "profile_context_mismatch"
    QA_POLICY_INVALID = "qa_policy_invalid"
    QA_POLICY_NOT_CURRENT = "qa_policy_not_current"
    QA_POLICY_COVERAGE_INCOMPLETE = "qa_policy_coverage_incomplete"
    HARD_CHECK_BLOCKED = "hard_check_blocked"
    HARD_CHECK_NOT_CURRENT = "hard_check_not_current"
    HARD_CHECK_OUTCOME_UNKNOWN = "hard_check_outcome_unknown"
    REVIEW_LAYER_BLOCKED = "review_layer_blocked"
    REVIEW_LAYER_NOT_CURRENT = "review_layer_not_current"
    REVIEW_LAYER_OUTCOME_UNKNOWN = "review_layer_outcome_unknown"


class UniversalQaApplicability(StrictModel):
    has_audio: bool = False
    has_captions: bool = False
    has_graphics: bool = False
    has_safe_area_requirements: bool = False
    has_transitions: bool = False
    requires_continuity: bool = False

    @property
    def layout_required(self) -> bool:
        return any(
            (
                self.has_captions,
                self.has_graphics,
                self.has_safe_area_requirements,
                self.has_transitions,
            )
        )


class UniversalQaProfile(StrictModel):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    delivery_profile: DeliveryProfile
    applicability: UniversalQaApplicability
    required_hard_checks: tuple[UniversalHardCheck, ...] = Field(min_length=1)
    required_review_layers: tuple[QaLayer, ...] = Field(min_length=1)
    continuity_requirement_ids: tuple[str, ...] = ()
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_contract(self) -> "UniversalQaProfile":
        hard_checks = set(self.required_hard_checks)
        review_layers = set(self.required_review_layers)
        if len(hard_checks) != len(self.required_hard_checks):
            raise ValueError("Universal QA hard checks must be unique")
        if len(review_layers) != len(self.required_review_layers):
            raise ValueError("Universal QA review layers must be unique")
        if not _ALWAYS_REQUIRED_HARD_CHECKS.issubset(hard_checks):
            raise ValueError("Universal QA profile omits an always-required hard check")
        if QaLayer.TECHNICAL not in review_layers:
            raise ValueError("Universal QA profile requires the technical review layer")
        if QaLayer.FINAL_ACCEPTANCE in review_layers:
            raise ValueError("Final Acceptance is not a Universal QA review layer")
        if (
            self.applicability.has_audio or self.applicability.has_captions
        ) and UniversalHardCheck.AUDIO_CAPTION_BINDING not in hard_checks:
            raise ValueError("audio or captions require the audio/caption hard check")
        if self.applicability.layout_required and QaLayer.LAYOUT not in review_layers:
            raise ValueError("applicable layout requirements require the layout layer")
        if self.applicability.requires_continuity:
            if UniversalHardCheck.CONTINUITY_EVIDENCE not in hard_checks:
                raise ValueError("applicable continuity requires continuity evidence")
            if not self.continuity_requirement_ids:
                raise ValueError("applicable continuity requires stable requirement IDs")
        elif self.continuity_requirement_ids:
            raise ValueError("continuity requirement IDs require applicable continuity")
        if any(not item.strip() for item in self.continuity_requirement_ids):
            raise ValueError("continuity requirement IDs must be nonblank")
        if len(set(self.continuity_requirement_ids)) != len(
            self.continuity_requirement_ids
        ):
            raise ValueError("continuity requirement IDs must be unique")
        expected_hash = canonical_sha256(
            {
                "schema": "universal-qa-profile/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        )
        if self.content_hash != expected_hash:
            raise ValueError("Universal QA profile content hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "UniversalQaProfile":
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {
                **values,
                "content_hash": canonical_sha256(
                    {
                        "schema": "universal-qa-profile/1",
                        **provisional.model_dump(
                            mode="json",
                            exclude={"content_hash"},
                            warnings=False,
                        ),
                    }
                ),
            }
        )


class UniversalQaContext(StrictModel):
    delivery_profile: DeliveryProfile
    applicability: UniversalQaApplicability
    project_content_hash: str = Field(pattern=_SHA256)
    registry_content_hash: str = Field(pattern=_SHA256)
    dependency_graph_revision_id: str = Field(pattern=_SHA256)
    render_state_content_hash: str = Field(pattern=_SHA256)
    render_output_sha256: str = Field(pattern=_SHA256)
    timeline_fingerprint: str = Field(pattern=_SHA256)
    qa_policy_content_hash: str = Field(pattern=_SHA256)


class UniversalQaCheckOutcome(StrictModel):
    verdict: QaVerdict
    current: bool


class UniversalQaCoverageResult(StrictModel):
    verdict: QaVerdict
    block_reason: UniversalQaBlockReason | None = None
    blocked_identifiers: tuple[str, ...] = ()


class UniversalQaGateResult(StrictModel):
    verdict: QaVerdict
    profile_content_hash: str | None = Field(default=None, pattern=_SHA256)
    context_content_hash: str = Field(pattern=_SHA256)
    qa_policy_content_hash: str | None = Field(default=None, pattern=_SHA256)
    expected_qa_policy_content_hash: str | None = Field(
        default=None,
        pattern=_SHA256,
    )
    completed_hard_checks: tuple[UniversalHardCheck, ...] = ()
    completed_review_layers: tuple[QaLayer, ...] = ()
    block_reason: UniversalQaBlockReason | None = None
    blocked_identifiers: tuple[str, ...] = ()
    eligible_for_domain_gate: bool = False
    eligible_for_final_acceptance: Literal[False] = False

    @model_validator(mode="after")
    def _validate_domain_eligibility(self) -> "UniversalQaGateResult":
        if self.eligible_for_domain_gate and (
            self.verdict is not QaVerdict.PASS
            or self.block_reason is not None
            or self.profile_content_hash is None
            or self.qa_policy_content_hash is None
            or self.expected_qa_policy_content_hash is None
            or self.qa_policy_content_hash != self.expected_qa_policy_content_hash
            or not self.completed_hard_checks
            or not self.completed_review_layers
        ):
            raise ValueError(
                "Domain gate eligibility requires complete consistent identity "
                "and completed Gate 1 evidence"
            )
        return self


HardCheckRunner = Callable[
    [UniversalHardCheck, UniversalQaContext, UniversalQaProfile],
    UniversalQaCheckOutcome,
]
ReviewLayerRunner = Callable[
    [QaLayer, UniversalQaContext, UniversalQaProfile], UniversalQaCheckOutcome
]


def _context_content_hash(context: UniversalQaContext) -> str:
    return canonical_sha256(
        {
            "schema": "universal-qa-context/1",
            **context.model_dump(mode="json"),
        }
    )


def _valid_declared_hash(value: object) -> str | None:
    if isinstance(value, str) and re.fullmatch(_SHA256, value):
        return value
    return None


def _gate_result(
    *,
    profile: UniversalQaProfile,
    context: UniversalQaContext,
    policy: QaPolicy,
    verdict: QaVerdict,
    completed_hard_checks: tuple[UniversalHardCheck, ...] = (),
    completed_review_layers: tuple[QaLayer, ...] = (),
    block_reason: UniversalQaBlockReason | None = None,
    blocked_identifiers: tuple[str, ...] = (),
    eligible_for_domain_gate: bool = False,
) -> UniversalQaGateResult:
    return UniversalQaGateResult(
        verdict=verdict,
        profile_content_hash=_valid_declared_hash(profile.content_hash),
        context_content_hash=_context_content_hash(context),
        qa_policy_content_hash=_valid_declared_hash(policy.content_hash),
        expected_qa_policy_content_hash=_valid_declared_hash(
            context.qa_policy_content_hash
        ),
        completed_hard_checks=completed_hard_checks,
        completed_review_layers=completed_review_layers,
        block_reason=block_reason,
        blocked_identifiers=blocked_identifiers,
        eligible_for_domain_gate=eligible_for_domain_gate,
    )


def validate_universal_qa_coverage(
    *,
    profile: UniversalQaProfile,
    context: UniversalQaContext,
    policy: QaPolicy,
) -> UniversalQaCoverageResult:
    try:
        validated_profile = UniversalQaProfile.model_validate(
            profile.model_dump(mode="json")
        )
    except ValidationError:
        return UniversalQaCoverageResult(
            verdict=QaVerdict.NOT_EVALUATED,
            block_reason=UniversalQaBlockReason.PROFILE_INVALID,
        )
    try:
        validated_context = UniversalQaContext.model_validate(
            context.model_dump(mode="json")
        )
    except ValidationError:
        return UniversalQaCoverageResult(
            verdict=QaVerdict.NOT_EVALUATED,
            block_reason=UniversalQaBlockReason.CONTEXT_INVALID,
        )
    try:
        validated_policy = QaPolicy.model_validate(policy.model_dump(mode="json"))
    except ValidationError:
        return UniversalQaCoverageResult(
            verdict=QaVerdict.NOT_EVALUATED,
            block_reason=UniversalQaBlockReason.QA_POLICY_INVALID,
        )
    if (
        validated_profile.delivery_profile != validated_context.delivery_profile
        or validated_profile.applicability != validated_context.applicability
    ):
        return UniversalQaCoverageResult(
            verdict=QaVerdict.NOT_EVALUATED,
            block_reason=UniversalQaBlockReason.PROFILE_CONTEXT_MISMATCH,
        )
    if not verify_artifact_hash(validated_policy):
        return UniversalQaCoverageResult(
            verdict=QaVerdict.NOT_EVALUATED,
            block_reason=UniversalQaBlockReason.QA_POLICY_INVALID,
        )
    if validated_policy.content_hash != validated_context.qa_policy_content_hash:
        return UniversalQaCoverageResult(
            verdict=QaVerdict.NOT_EVALUATED,
            block_reason=UniversalQaBlockReason.QA_POLICY_NOT_CURRENT,
        )
    selected_layers = set(validated_policy.required_layers)
    missing_layers = tuple(
        layer.value
        for layer in validated_profile.required_review_layers
        if layer not in selected_layers
    )
    if missing_layers:
        return UniversalQaCoverageResult(
            verdict=QaVerdict.NOT_EVALUATED,
            block_reason=UniversalQaBlockReason.QA_POLICY_COVERAGE_INCOMPLETE,
            blocked_identifiers=missing_layers,
        )
    return UniversalQaCoverageResult(verdict=QaVerdict.PASS)


class UniversalQualityGateCoordinator:
    """Run preselected Gate 1 checks once; never run Domain or Final Acceptance."""

    def run_once(
        self,
        *,
        profile: UniversalQaProfile,
        context: UniversalQaContext,
        policy: QaPolicy,
        run_hard_check: HardCheckRunner,
        run_review_layer: ReviewLayerRunner,
    ) -> UniversalQaGateResult:
        coverage = validate_universal_qa_coverage(
            profile=profile,
            context=context,
            policy=policy,
        )
        if coverage.verdict is not QaVerdict.PASS:
            return _gate_result(
                profile=profile,
                context=context,
                policy=policy,
                verdict=coverage.verdict,
                block_reason=coverage.block_reason,
                blocked_identifiers=coverage.blocked_identifiers,
            )

        validated_profile = UniversalQaProfile.model_validate(
            profile.model_dump(mode="json")
        )
        validated_context = UniversalQaContext.model_validate(
            context.model_dump(mode="json")
        )

        completed_hard_checks: list[UniversalHardCheck] = []
        for hard_check in validated_profile.required_hard_checks:
            try:
                outcome = UniversalQaCheckOutcome.model_validate(
                    run_hard_check(hard_check, validated_context, validated_profile)
                )
            except AiVideoError as exc:
                if exc.code is not ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN:
                    raise
                return _gate_result(
                    profile=profile,
                    context=context,
                    policy=policy,
                    verdict=QaVerdict.NOT_EVALUATED,
                    completed_hard_checks=tuple(completed_hard_checks),
                    block_reason=UniversalQaBlockReason.HARD_CHECK_OUTCOME_UNKNOWN,
                    blocked_identifiers=(hard_check.value,),
                )
            if not outcome.current:
                return _gate_result(
                    profile=profile,
                    context=context,
                    policy=policy,
                    verdict=QaVerdict.NOT_EVALUATED,
                    completed_hard_checks=tuple(completed_hard_checks),
                    block_reason=UniversalQaBlockReason.HARD_CHECK_NOT_CURRENT,
                    blocked_identifiers=(hard_check.value,),
                )
            if outcome.verdict is not QaVerdict.PASS:
                return _gate_result(
                    profile=profile,
                    context=context,
                    policy=policy,
                    verdict=outcome.verdict,
                    completed_hard_checks=tuple(completed_hard_checks),
                    block_reason=UniversalQaBlockReason.HARD_CHECK_BLOCKED,
                    blocked_identifiers=(hard_check.value,),
                )
            completed_hard_checks.append(hard_check)

        completed_review_layers: list[QaLayer] = []
        for layer in validated_profile.required_review_layers:
            try:
                outcome = UniversalQaCheckOutcome.model_validate(
                    run_review_layer(layer, validated_context, validated_profile)
                )
            except AiVideoError as exc:
                if exc.code is not ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN:
                    raise
                return _gate_result(
                    profile=profile,
                    context=context,
                    policy=policy,
                    verdict=QaVerdict.NOT_EVALUATED,
                    completed_hard_checks=tuple(completed_hard_checks),
                    completed_review_layers=tuple(completed_review_layers),
                    block_reason=UniversalQaBlockReason.REVIEW_LAYER_OUTCOME_UNKNOWN,
                    blocked_identifiers=(layer.value,),
                )
            if not outcome.current:
                return _gate_result(
                    profile=profile,
                    context=context,
                    policy=policy,
                    verdict=QaVerdict.NOT_EVALUATED,
                    completed_hard_checks=tuple(completed_hard_checks),
                    completed_review_layers=tuple(completed_review_layers),
                    block_reason=UniversalQaBlockReason.REVIEW_LAYER_NOT_CURRENT,
                    blocked_identifiers=(layer.value,),
                )
            if outcome.verdict is not QaVerdict.PASS:
                return _gate_result(
                    profile=profile,
                    context=context,
                    policy=policy,
                    verdict=outcome.verdict,
                    completed_hard_checks=tuple(completed_hard_checks),
                    completed_review_layers=tuple(completed_review_layers),
                    block_reason=UniversalQaBlockReason.REVIEW_LAYER_BLOCKED,
                    blocked_identifiers=(layer.value,),
                )
            completed_review_layers.append(layer)

        return _gate_result(
            profile=profile,
            context=context,
            policy=policy,
            verdict=QaVerdict.PASS,
            completed_hard_checks=tuple(completed_hard_checks),
            completed_review_layers=tuple(completed_review_layers),
            eligible_for_domain_gate=True,
        )
