from __future__ import annotations

from collections.abc import Callable

from ai_video.planning._asset_readiness import current_review
from ai_video.planning._planner_models import (
    CurrentPlanProjectionFailure,
    CurrentPlanProjectionFailureReason,
    VideoGenerationPlan,
    VideoPlanningRequest,
    _canonical_hash_without,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import (
    VerifiedGenerationRequirementProjection,
)


def _failure(
    reasons: list[CurrentPlanProjectionFailureReason],
    field_paths: list[str],
) -> CurrentPlanProjectionFailure:
    return CurrentPlanProjectionFailure(
        reason_codes=tuple(reasons),
        field_paths=tuple(field_paths),
    )


def verify_current_generation_requirement_projection(
    *,
    current_request: VideoPlanningRequest,
    plan: VideoGenerationPlan,
    derive_plan: Callable[[VideoPlanningRequest], VideoGenerationPlan],
) -> VerifiedGenerationRequirementProjection | CurrentPlanProjectionFailure:
    reasons: list[CurrentPlanProjectionFailureReason] = []
    field_paths: list[str] = []

    def add(
        reason: CurrentPlanProjectionFailureReason,
        *paths: str,
    ) -> None:
        if reason not in reasons:
            reasons.append(reason)
        for path in paths:
            if path not in field_paths:
                field_paths.append(path)

    if (
        current_request.planning_contract_version != "video-planner/3"
        or plan.planning_contract_version != "video-planner/3"
    ):
        add(
            CurrentPlanProjectionFailureReason.LEGACY_CONTRACT,
            "current_request.planning_contract_version",
            "plan.planning_contract_version",
        )
        return _failure(reasons, field_paths)

    expected_request_hash = _canonical_hash_without(
        current_request,
        "request_id",
        "request_content_hash",
    )
    if current_request.request_content_hash != expected_request_hash:
        add(
            CurrentPlanProjectionFailureReason.REQUEST_SEAL_INVALID,
            "current_request.request_content_hash",
        )
    if plan.plan_hash != _canonical_hash_without(plan, "plan_hash"):
        add(
            CurrentPlanProjectionFailureReason.PLAN_SEAL_INVALID,
            "plan.plan_hash",
        )

    expected_plan = derive_plan(current_request)
    if plan.plan_hash != expected_plan.plan_hash:
        add(
            CurrentPlanProjectionFailureReason.PLAN_NOT_UNIQUE_CURRENT_DERIVATION,
            "plan.plan_hash",
        )
    expected_plan_id = f"plan-{plan.source_request_content_hash[:24]}"
    if plan.plan_id != expected_plan_id:
        add(
            CurrentPlanProjectionFailureReason.PLAN_ID_INVALID,
            "plan.plan_id",
        )
    if plan.source_request_content_hash != current_request.request_content_hash:
        add(
            CurrentPlanProjectionFailureReason.SOURCE_REQUEST_STALE,
            "plan.source_request_content_hash",
            "current_request.request_content_hash",
        )
    if (
        plan.target_shot_id != current_request.target_shot.shot_id
        or plan.target_shot_revision != current_request.target_shot.revision
        or plan.target_shot_content_hash
        != current_request.target_shot.content_hash
    ):
        add(
            CurrentPlanProjectionFailureReason.TARGET_SHOT_STALE,
            "plan.target_shot_id",
            "plan.target_shot_revision",
            "plan.target_shot_content_hash",
        )

    requirement = plan.generation_requirement
    if requirement is None:
        add(
            CurrentPlanProjectionFailureReason.EMBEDDED_REQUIREMENT_MISSING,
            "plan.generation_requirement",
        )
    else:
        embedded_requirement_stale = bool(
            requirement.source_request_content_hash
            != current_request.request_content_hash
            or requirement.intent_evidence_hash
            != canonical_sha256(
                current_request.shot_intent_evidence.model_dump(mode="json")
            )
            or current_request.generation_intent is None
            or requirement.generation_intent_hash
            != current_request.generation_intent.projection_hash
            or requirement.generation_intent
            != current_request.generation_intent.generation_intent
            or requirement.scene != current_request.scene_context
            or requirement.characters
            != tuple(
                character
                for character in current_request.character_context
                if character.character_id
                in current_request.target_shot.character_ids
            )
        )
        current_assets = {
            (asset.asset_id, asset.asset_sha256): asset
            for asset in current_request.available_assets
        }
        for evidence in requirement.asset_evidence:
            asset = current_assets.get((evidence.asset_id, evidence.asset_sha256))
            if asset is None or (
                evidence.canonical_owner_id != asset.canonical_owner_id
                or evidence.canonical_owner_content_hash
                != asset.canonical_owner_content_hash
                or evidence.mime_type != asset.mime_type
                or evidence.width != asset.width
                or evidence.height != asset.height
                or evidence.size_bytes != asset.size_bytes
                or evidence.duration_millis != asset.duration_millis
                or evidence.fps != asset.fps
            ):
                embedded_requirement_stale = True
                break
        review = current_review(current_request)
        expected_review_hash = (
            canonical_sha256(review.model_dump(mode="json"))
            if review is not None
            else None
        )
        if (
            (requirement.review_evidence is None) != (review is None)
            or requirement.review_evidence is not None
            and requirement.review_evidence.review_decision_hash
            != expected_review_hash
        ):
            embedded_requirement_stale = True
        try:
            type(requirement).model_validate(requirement.model_dump(mode="python"))
        except ValueError:
            embedded_requirement_stale = True
        if embedded_requirement_stale:
            add(
                CurrentPlanProjectionFailureReason.EMBEDDED_REQUIREMENT_STALE,
                "plan.generation_requirement",
            )

    if reasons:
        return _failure(reasons, field_paths)

    assert requirement is not None
    try:
        projection = VerifiedGenerationRequirementProjection.create(
            requirement=requirement,
            plan_hash=plan.plan_hash,
            verified_source_request_content_hash=(
                current_request.request_content_hash
            ),
            target_shot_id=current_request.target_shot.shot_id,
            target_shot_revision=current_request.target_shot.revision,
            target_shot_content_hash=current_request.target_shot.content_hash,
        )
        return VerifiedGenerationRequirementProjection.model_validate(
            projection.model_dump(mode="python")
        )
    except ValueError:
        add(
            CurrentPlanProjectionFailureReason.VERIFIED_PROJECTION_INVALID,
            "verified_generation_requirement",
        )
        return _failure(reasons, field_paths)
