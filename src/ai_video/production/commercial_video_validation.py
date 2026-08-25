"""Pure current-state validation for commercial generated-video checkpoints."""

from __future__ import annotations

from ai_video.production.commercial_source_preparation import (
    ApprovedCommercialSourceBinding,
)
from ai_video.production.commercial_video_contracts import (
    GeneratedCommercialShotBinding,
)
from ai_video.production.ecommerce_media_acceptance import (
    CommercialShotEvaluationIntent,
    GeneratedCommercialShotEvidence,
)
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import CommercialSourceLifecycle, QaPolicy, QaVerdict
from ai_video.production.models import LoadedProductionProject
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_commercial_source_approval_path,
)
from ai_video.production.video import ResolvedVideoGenerationRequest
from ai_video.production.video_artifact import (
    VideoProbeReceipt,
    validate_generated_commercial_shot_evidence,
)


def commercial_source_hashes(
    approval: ApprovedCommercialSourceBinding,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Derive request lineage only from one reopened approved source owner."""

    checked = ApprovedCommercialSourceBinding.model_validate(
        approval.model_dump(mode="python")
    )
    truth = tuple(
        sorted(
            item.asset_sha256
            for item in checked.product_reference_set.assets
            if item.purpose == "product_truth"
        )
    )
    references = tuple(
        sorted(item.asset_sha256 for item in checked.product_reference_set.assets)
    )
    return truth, references, (checked.content_hash,)


def current_commercial_source_approval(
    bundle: LoadedProductionProject,
    binding: GeneratedCommercialShotBinding,
) -> ApprovedCommercialSourceBinding | None:
    """Reopen the Manifest-selected source needed by this exact binding."""

    if not binding.source_approval_hashes:
        return None
    from ai_video.production._commercial_project_reader import (
        reopen_active_commercial_source_approval,
    )

    approval = reopen_active_commercial_source_approval(
        bundle,
        target_shot_id=binding.target_shot_id,
    )
    if binding.source_approval_hashes != (approval.content_hash,):
        raise ValueError("Commercial request source approval is no longer active")
    return approval


def bound_commercial_source_approval(
    bundle: LoadedProductionProject,
    binding: GeneratedCommercialShotBinding,
    *,
    require_current: bool,
) -> ApprovedCommercialSourceBinding | None:
    """Reopen current approval before activation, or its consumed immutable seal after."""

    if not binding.source_approval_hashes:
        validate_commercial_source_binding(binding, None)
        return None
    if require_current:
        return current_commercial_source_approval(bundle, binding)

    from ai_video.production._commercial_project_reader import (
        verify_active_commercial_source_approvals,
    )

    verify_active_commercial_source_approvals(bundle)
    content_hash = binding.source_approval_hashes[0]
    path = canonical_commercial_source_approval_path(content_hash)
    snapshot = _read_regular_file_nofollow(
        bundle.root / path,
        contained_by=bundle.root / "state" / "commercial-source",
    )
    approval = ApprovedCommercialSourceBinding.model_validate_json(snapshot.data)
    if (
        approval.content_hash != content_hash
        or not verify_artifact_hash(approval)
        or not any(
            item.lifecycle is CommercialSourceLifecycle.STALE
            and item.request_fingerprint == approval.source_request_hash
            and item.target_shot_id == approval.target_shot_id
            and item.candidate_asset_id == approval.keyframe_asset_id
            and item.candidate_sha256 == approval.keyframe_sha256
            and item.review_receipt_hash == approval.review_receipt_hash
            for item in bundle.manifest.commercial_source_attempts
        )
    ):
        raise ValueError("Consumed commercial source approval lineage is not exact")
    validate_commercial_source_binding(binding, approval)
    return approval


def validate_commercial_source_binding(
    binding: GeneratedCommercialShotBinding,
    approval: ApprovedCommercialSourceBinding | None,
) -> None:
    """Require product lineage to equal one exact current source approval."""

    has_product_lineage = bool(
        binding.product_truth_hashes
        or binding.product_reference_hashes
        or binding.source_approval_hashes
    )
    if not has_product_lineage:
        if approval is not None:
            raise ValueError("Commercial binding has an unexpected source approval")
        return
    if approval is None:
        raise ValueError("Commercial product binding has no current source approval")
    checked = ApprovedCommercialSourceBinding.model_validate(
        approval.model_dump(mode="python")
    )
    if (
        checked.ad_creative_plan_hash != binding.ad_creative_plan_hash
        or checked.execution_projection_hash
        != binding.commercial_execution_projection_hash
        or checked.target_shot_id != binding.target_shot_id
        or commercial_source_hashes(checked)
        != (
            binding.product_truth_hashes,
            binding.product_reference_hashes,
            binding.source_approval_hashes,
        )
    ):
        raise ValueError("Commercial source approval does not match request binding")


def validate_current_commercial_checkpoint(
    *,
    request: ResolvedVideoGenerationRequest,
    intent: CommercialShotEvaluationIntent,
    evidence: GeneratedCommercialShotEvidence,
    probe: VideoProbeReceipt,
    policy: QaPolicy,
    approval: ApprovedCommercialSourceBinding | None,
) -> QaVerdict:
    """Validate one checkpoint against current policy, source and measured bytes."""

    binding = request.commercial_binding
    domain = policy.domain_acceptance
    if (
        binding is None
        or domain is None
        or domain.domain_id != "ecommerce"
        or domain.profile_content_hash != binding.profile_content_hash
        or tuple(domain.profile_payload.get("shot_requirement_ids", ()))
        and any(
            item
            not in tuple(domain.profile_payload.get("shot_requirement_ids", ()))
            for item in binding.applicable_requirement_ids
        )
        or probe.request_receipt_fingerprint
        != request.desired_generation_fingerprint
        or probe.resolved_generation_hash != request.resolved_generation_hash
        or probe.commercial_evidence != evidence
    ):
        raise ValueError("Commercial checkpoint is not current and exact")
    validate_commercial_source_binding(binding, approval)
    validate_generated_commercial_shot_evidence(
        evidence,
        request=request,
        measured=probe.measured,
        policy_content_hash=policy.content_hash,
        authorities=policy.semantic_authorities,
        require_pass=True,
        intent=intent,
    )
    return QaVerdict.PASS
