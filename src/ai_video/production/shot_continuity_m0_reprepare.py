"""Reseal the inactive M0 qualification closure after source activation.

This module does not materialize an execution stack or invoke a Provider.  It
only replaces stale Project/Registry pointers and the final edge's planned
source derivations with exact registered terminal-frame and motion-tail
evidence, then delegates the durable write to ``ProductionStateCommitter``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import AssetType
from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_motion_tail import (
    validate_full_source_motion_tail,
)
from ai_video.production.video_transition import (
    ContinuityAnchorBinding,
    ContinuityAnchorRole,
    ContinuityTransitionPolicy,
    CreativeArtifactIdentity,
    P0QualificationPreparedReceipt,
    RealShotValidationSet,
    ValidationEdgeBinding,
)


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_STATE_INVALID,
        user_message=message,
        retryable=False,
    )


@dataclass(frozen=True)
class RegisteredContinuityAnchor:
    asset_id: str
    asset_sha256: str
    evidence_fingerprint: str
    materialization_receipt_id: str


@dataclass(frozen=True)
class M0ReprepareResult:
    manifest: Any
    receipt: P0QualificationPreparedReceipt
    policies: tuple[ContinuityTransitionPolicy, ...]
    validation_set: RealShotValidationSet


def _registered_anchor(
    *,
    role: ContinuityAnchorRole,
    anchor: RegisteredContinuityAnchor,
    registry_by_id: dict[str, Any],
    expected_asset_types: tuple[AssetType, ...],
    expected_mime_types: tuple[str, ...],
) -> ContinuityAnchorBinding:
    asset = registry_by_id.get(anchor.asset_id)
    if (
        asset is None
        or asset.sha256 != anchor.asset_sha256
        or asset.creation_receipt_id != anchor.evidence_fingerprint
        or asset.creation_receipt_id != anchor.materialization_receipt_id
        or asset.asset_type not in expected_asset_types
        or asset.mime_type not in expected_mime_types
    ):
        raise _invalid(f"M0 {role.value} anchor is not exact in the active Registry.")
    return ContinuityAnchorBinding(
        role=role,
        source_kind="registered_asset",
        source_identity=anchor.asset_id,
        content_hash=anchor.asset_sha256,
        evidence_fingerprint=anchor.evidence_fingerprint,
        materialization_receipt_id=anchor.materialization_receipt_id,
    )


def reprepare_m0_qualification(
    *,
    committer: Any,
    historical_receipt_hash: str,
    terminal_anchor: RegisteredContinuityAnchor,
    motion_tail_anchor: RegisteredContinuityAnchor,
    expected_manifest_revision: int,
    attempt_id: str,
) -> M0ReprepareResult:
    """Create one current unmaterialized P0 closure without Provider effects."""

    historical = committer.reopen_p0_qualification_history(historical_receipt_hash)
    old_receipt, candidates, old_policies, old_validation, inputs, sources = historical
    if any(
        stack.materialization_status != "unmaterialized"
        for stack in (*sources, *candidates)
    ):
        raise _invalid("M0 reprepare requires an unmaterialized historical closure.")

    loaded = load_production_project(committer.project_root / "project.yaml")
    manifest = loaded.manifest
    if manifest.manifest_revision != expected_manifest_revision:
        raise _invalid("M0 reprepare base Manifest revision changed.")
    existing_pointer = manifest.active_p0_qualification_prepared
    registry_by_id = {asset.asset_id: asset for asset in loaded.registry.assets}
    try:
        tail_receipt = validate_full_source_motion_tail(
            committer.project_root, loaded, motion_tail_anchor.asset_id
        )
    except AiVideoError as exc:
        raise _invalid("M0 reference_video anchor is not exact.") from exc
    terminal = tail_receipt.terminal_frame_evidence
    if (
        tail_receipt.content_hash != motion_tail_anchor.evidence_fingerprint
        or tail_receipt.content_hash != motion_tail_anchor.materialization_receipt_id
        or tail_receipt.source_video_sha256 != motion_tail_anchor.asset_sha256
        or terminal.extracted_asset_id != terminal_anchor.asset_id
        or terminal.extracted_sha256 != terminal_anchor.asset_sha256
        or terminal.extraction_receipt_id != terminal_anchor.evidence_fingerprint
        or terminal.extraction_receipt_id
        != terminal_anchor.materialization_receipt_id
    ):
        raise _invalid("M0 reprepare terminal and motion-tail lineage is not exact.")
    current_shots = {
        shot.artifact_id: CreativeArtifactIdentity(
            artifact_id=shot.artifact_id,
            revision=shot.revision,
            content_hash=shot.content_hash,
        )
        for shot in loaded.shots
    }
    current_shot_models = {shot.artifact_id: shot for shot in loaded.shots}

    policies: list[ContinuityTransitionPolicy] = []
    for old in old_policies:
        source_shot = current_shots.get(old.source_shot.artifact_id)
        target_shot = current_shots.get(old.target_shot.artifact_id)
        if source_shot is None or target_shot is None:
            raise _invalid("M0 reprepare Shot identity changed.")
        target_model = current_shot_models[old.target_shot.artifact_id]
        endpoint_roles = tuple(
            item
            for item in target_model.required_asset_roles
            if item.role == "approved_endpoint"
        )
        if len(endpoint_roles) != 1 or len(endpoint_roles[0].asset_ids) != 1:
            raise _invalid("M0 reprepare target approved endpoint is not exact.")
        endpoint_asset = registry_by_id.get(endpoint_roles[0].asset_ids[0])
        if endpoint_asset is None:
            raise _invalid("M0 reprepare target approved endpoint is unregistered.")
        endpoint_mime_types = (
            ("image/png",)
            if AssetType.IMAGE in endpoint_roles[0].allowed_asset_types
            else ()
        ) + (
            ("video/mp4", "video/quicktime")
            if AssetType.VIDEO in endpoint_roles[0].allowed_asset_types
            else ()
        )
        anchors_by_role = {item.role: item for item in old.anchors}
        anchors_by_role[ContinuityAnchorRole.LAST_FRAME] = _registered_anchor(
            role=ContinuityAnchorRole.LAST_FRAME,
            anchor=RegisteredContinuityAnchor(
                asset_id=endpoint_asset.asset_id,
                asset_sha256=endpoint_asset.sha256,
                evidence_fingerprint=endpoint_asset.creation_receipt_id,
                materialization_receipt_id=endpoint_asset.creation_receipt_id,
            ),
            registry_by_id=registry_by_id,
            expected_asset_types=endpoint_roles[0].allowed_asset_types,
            expected_mime_types=endpoint_mime_types,
        )
        if old.policy_id == "rainy-station-edge-3-4":
            anchors_by_role[ContinuityAnchorRole.FIRST_FRAME] = _registered_anchor(
                role=ContinuityAnchorRole.FIRST_FRAME,
                anchor=terminal_anchor,
                registry_by_id=registry_by_id,
                expected_asset_types=(AssetType.IMAGE,),
                expected_mime_types=("image/png",),
            )
            anchors_by_role[ContinuityAnchorRole.REFERENCE_VIDEO] = _registered_anchor(
                role=ContinuityAnchorRole.REFERENCE_VIDEO,
                anchor=motion_tail_anchor,
                registry_by_id=registry_by_id,
                expected_asset_types=(AssetType.VIDEO,),
                expected_mime_types=("video/mp4",),
            )
        anchors = tuple(
            sorted(anchors_by_role.values(), key=lambda item: item.role.value)
        )
        for anchor in anchors:
            if anchor.source_kind == "registered_asset":
                asset = registry_by_id.get(anchor.source_identity)
                if asset is None or asset.sha256 != anchor.content_hash:
                    raise _invalid(f"M0 {old.policy_id} registered anchor changed.")
        values = old.model_dump(
            mode="python",
            exclude={
                "policy_hash",
                "project",
                "registry",
                "source_shot",
                "target_shot",
                "anchors",
            },
        )
        policies.append(
            ContinuityTransitionPolicy.create(
                **values,
                project=manifest.active_project,
                registry=manifest.active_registry,
                source_shot=source_shot,
                target_shot=target_shot,
                anchors=anchors,
            )
        )
    policies_tuple = tuple(policies)
    policy_by_edge = {
        (item.source_shot.artifact_id, item.target_shot.artifact_id): item
        for item in policies_tuple
    }
    validation_values = old_validation.model_dump(
        mode="python",
        exclude={
            "content_hash",
            "project",
            "registry",
            "character",
            "scene",
            "shots",
            "edges",
        },
    )
    validation_set = RealShotValidationSet.create(
        **validation_values,
        project=manifest.active_project,
        registry=manifest.active_registry,
        character=old_validation.character,
        scene=old_validation.scene,
        shots=tuple(current_shots[item.artifact_id] for item in old_validation.shots),
        edges=tuple(
            ValidationEdgeBinding(
                source_shot_id=edge.source_shot_id,
                target_shot_id=edge.target_shot_id,
                policy_hash=policy_by_edge[
                    (edge.source_shot_id, edge.target_shot_id)
                ].policy_hash,
                motion_coverage=edge.motion_coverage,
            )
            for edge in old_validation.edges
        ),
    )
    receipt_values = old_receipt.model_dump(
        mode="python",
        exclude={
            "content_hash",
            "project",
            "registry",
            "validation_set_hash",
            "policy_hashes",
            "candidate_stacks",
            "limitations",
        },
    )
    receipt = P0QualificationPreparedReceipt.create(
        **receipt_values,
        project=manifest.active_project,
        registry=manifest.active_registry,
        validation_set_hash=validation_set.content_hash,
        policy_hashes=tuple(sorted(item.policy_hash for item in policies_tuple)),
        candidate_stacks=old_receipt.candidate_stacks,
        limitations=(
            "The accepted upstream source video is active and P6-accepted only "
            "for motion-tail derivation.",
            "No M0 qualification video has been generated or accepted.",
            "No candidate winner or active M0 capability has been selected.",
            "M1 Hybrid artifact is absent and its stack remains unmaterialized.",
            "No M0 P6 verdict, Final Acceptance, push, or release is claimed.",
        ),
    )
    if existing_pointer is not None:
        reopened = committer.reopen_p0_qualification_prepared()
        reopened_sources = committer.reopen_p0_qualification_source_stacks()
        if (
            existing_pointer.content_hash != receipt.content_hash
            or reopened
            != (receipt, candidates, policies_tuple, validation_set, inputs)
            or reopened_sources != sources
        ):
            raise _invalid("Active P0 qualification closure does not match replay.")
        return M0ReprepareResult(
            manifest=manifest,
            receipt=receipt,
            policies=policies_tuple,
            validation_set=validation_set,
        )
    committed = committer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=candidates,
        source_stacks=sources,
        policies=policies_tuple,
        validation_set=validation_set,
        qualification_inputs=inputs,
        expected_manifest_revision=expected_manifest_revision,
        attempt_id=attempt_id,
    )
    reopened = committer.reopen_p0_qualification_prepared()
    if reopened != (
        receipt,
        candidates,
        policies_tuple,
        validation_set,
        inputs,
    ):
        raise _invalid("M0 reprepare closure did not reopen exactly.")
    if committer.reopen_p0_qualification_source_stacks() != sources:
        raise _invalid("M0 reprepare source stack did not reopen exactly.")
    return M0ReprepareResult(
        manifest=committed,
        receipt=receipt,
        policies=policies_tuple,
        validation_set=validation_set,
    )


__all__ = [
    "M0ReprepareResult",
    "RegisteredContinuityAnchor",
    "reprepare_m0_qualification",
]
