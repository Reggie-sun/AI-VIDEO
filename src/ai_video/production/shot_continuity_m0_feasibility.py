"""Exact-bound human endpoint-feasibility approval for M0 C4 qualification."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._state_commit_common import (
    _canonical_json_bytes,
    prepare_dependency_graph_transition,
    prepare_project_registry_commit,
)
from ai_video.production._state_commit_contracts import (
    PreparedArtifact,
    StateCommitRequest,
)
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256
from ai_video.production.dependency import desired_fingerprints
from ai_video.production.models import (
    ActorIdentity,
    LoadedProductionProject,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_m0_endpoint_feasibility_approval_path,
    canonical_m0_endpoint_feasibility_human_decision_path,
)
from ai_video.production.shot_continuity_motion_tail import (
    validate_full_source_motion_tail,
)


_SHA256 = r"^[0-9a-f]{64}$"
_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SCHEMA = "ai-video-m0-endpoint-feasibility-approval/1"


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_STATE_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class M0EndpointFeasibilityApproval(StrictModel):
    """One human PASS bound to every C4 anchor and the one-submit scope."""

    schema_version: Literal["ai-video-m0-endpoint-feasibility-approval/1"] = _SCHEMA
    approval_id: str = Field(pattern=_SAFE_ID)
    approved_by: ActorIdentity
    approved_at: str = Field(min_length=1)
    human_decision_content_hash: str = Field(pattern=_SHA256)
    human_decision_evidence_source_id: str = Field(pattern=_SAFE_ID)
    human_decision_evidence_sha256: str = Field(pattern=_SHA256)
    authorization_scope: Literal["local-m0-quality-v1-one-submit"]
    submit_limit: Literal[1]
    retry_allowed: Literal[False]
    fallback_allowed: Literal[False]
    attempt_id: str = Field(pattern=_SAFE_ID)
    generation_id: str = Field(pattern=_SAFE_ID)
    output_asset_id: str = Field(pattern=_SAFE_ID)
    validation_policy_id: Literal["quality-v1"]
    execution_stack_hash: str = Field(pattern=_SHA256)
    profile_document_hash: str = Field(pattern=_SHA256)
    project: ProjectSnapshotPointer
    registry: RegistrySnapshotPointer
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    output_duration_milliseconds: int = Field(strict=True, gt=0)
    terminal_anchor_content_hash: str = Field(pattern=_SHA256)
    identity_asset_id: str = Field(pattern=_SAFE_ID)
    identity_asset_sha256: str = Field(pattern=_SHA256)
    endpoint_asset_id: str = Field(pattern=_SAFE_ID)
    endpoint_asset_sha256: str = Field(pattern=_SHA256)
    motion_tail_asset_id: str = Field(pattern=_SAFE_ID)
    motion_tail_receipt_hash: str = Field(pattern=_SHA256)
    axis_check: Literal["PASS"]
    screen_direction_check: Literal["PASS"]
    subject_scale_check: Literal["PASS"]
    fov_check: Literal["PASS"]
    reachable_displacement_check: Literal["PASS"]
    no_teleport_check: Literal["PASS"]
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_approval(self) -> "M0EndpointFeasibilityApproval":
        if self.approved_by.actor_kind != "human":
            raise ValueError("M0 endpoint feasibility approval requires a human actor")
        try:
            approved_at = datetime.fromisoformat(self.approved_at)
        except ValueError as exc:
            raise ValueError("M0 endpoint approval time must be ISO-8601") from exc
        if approved_at.tzinfo is None:
            raise ValueError("M0 endpoint approval time must include a timezone")
        if self.content_hash != self.expected_content_hash():
            raise ValueError("M0 endpoint feasibility approval hash is invalid")
        return self

    def expected_content_hash(self) -> str:
        return canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        )

    @classmethod
    def create(cls, **values: object) -> "M0EndpointFeasibilityApproval":
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {
                **values,
                "content_hash": canonical_sha256(
                    provisional.model_dump(
                        mode="json", exclude={"content_hash"}, warnings=False
                    )
                ),
            }
        )


@dataclass(frozen=True)
class PreparedM0EndpointFeasibilityApproval:
    approval: M0EndpointFeasibilityApproval
    commit_request: StateCommitRequest | None
    replayed: bool = False


class M0EndpointFeasibilityHumanDecision(StrictModel):
    """Externally authored human checklist for one precomputed exact scope."""

    schema_version: Literal["ai-video-m0-endpoint-feasibility-human-decision/1"] = (
        "ai-video-m0-endpoint-feasibility-human-decision/1"
    )
    decision_id: str = Field(pattern=_SAFE_ID)
    reviewer: ActorIdentity
    decided_at: str = Field(min_length=1)
    evidence_source_id: str = Field(pattern=_SAFE_ID)
    evidence_source_sha256: str = Field(pattern=_SHA256)
    scope_fingerprint: str = Field(pattern=_SHA256)
    axis_check: Literal["PASS"]
    screen_direction_check: Literal["PASS"]
    subject_scale_check: Literal["PASS"]
    fov_check: Literal["PASS"]
    reachable_displacement_check: Literal["PASS"]
    no_teleport_check: Literal["PASS"]
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_decision(self) -> "M0EndpointFeasibilityHumanDecision":
        if self.reviewer.actor_kind != "human":
            raise ValueError("M0 endpoint decision requires a human reviewer")
        try:
            decided_at = datetime.fromisoformat(self.decided_at)
        except ValueError as exc:
            raise ValueError("M0 endpoint decision time must be ISO-8601") from exc
        if decided_at.tzinfo is None:
            raise ValueError("M0 endpoint decision time must include a timezone")
        if self.content_hash != canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        ):
            raise ValueError("M0 endpoint human decision hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "M0EndpointFeasibilityHumanDecision":
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {
                **values,
                "content_hash": canonical_sha256(
                    provisional.model_dump(
                        mode="json", exclude={"content_hash"}, warnings=False
                    )
                ),
            }
        )


def reopen_m0_endpoint_feasibility_human_decision(
    project_root: str | Path,
    content_hash: str,
) -> M0EndpointFeasibilityHumanDecision:
    """Strictly reopen the external human checklist bound by an approval."""

    root = Path(project_root).resolve(strict=True)
    try:
        path = canonical_m0_endpoint_feasibility_human_decision_path(content_hash)
        raw = _read_regular_file_nofollow(root / path, contained_by=root / "state")
        decision = M0EndpointFeasibilityHumanDecision.model_validate_json(raw.data)
    except (OSError, ValueError) as exc:
        raise _invalid("Could not reopen M0 endpoint human decision.", str(exc)) from exc
    if (
        decision.content_hash != content_hash
        or raw.data != _canonical_json_bytes(decision)
        or path
        != canonical_m0_endpoint_feasibility_human_decision_path(
            decision.content_hash
        )
    ):
        raise _invalid("M0 endpoint human decision identity is invalid.")
    return decision


def _asset(project: LoadedProductionProject, asset_id: str):
    try:
        return next(item for item in project.registry.assets if item.asset_id == asset_id)
    except StopIteration as exc:
        raise _invalid(f"M0 feasibility asset {asset_id} is not registered.") from exc


def _scope_fingerprint(
    *,
    project: LoadedProductionProject,
    target: Any,
    identity: Any,
    endpoint: Any,
    tail: Any,
    qualification_attempt_id: str,
    generation_id: str,
    output_asset_id: str,
    execution_stack_hash: str,
    profile_document_hash: str,
    output_duration_milliseconds: int,
    motion_tail_asset_id: str,
) -> str:
    return canonical_sha256(
        {
            "schema": "ai-video-m0-endpoint-feasibility-scope/1",
            "authorization_scope": "local-m0-quality-v1-one-submit",
            "attempt_id": qualification_attempt_id,
            "generation_id": generation_id,
            "output_asset_id": output_asset_id,
            "validation_policy_id": "quality-v1",
            "execution_stack_hash": execution_stack_hash,
            "profile_document_hash": profile_document_hash,
            "project_content_hash": project.project.content_hash,
            "registry_content_hash": project.registry.content_hash,
            "target_shot_id": target.shot_id,
            "target_shot_revision": target.revision,
            "target_shot_content_hash": target.content_hash,
            "output_duration_milliseconds": output_duration_milliseconds,
            "terminal_anchor_content_hash": tail.terminal_frame_evidence.content_hash,
            "identity_asset_id": identity.asset_id,
            "identity_asset_sha256": identity.sha256,
            "endpoint_asset_id": endpoint.asset_id,
            "endpoint_asset_sha256": endpoint.sha256,
            "motion_tail_asset_id": motion_tail_asset_id,
            "motion_tail_receipt_hash": tail.content_hash,
        }
    )


def m0_endpoint_feasibility_scope_fingerprint(
    *,
    project_root: str | Path,
    project: LoadedProductionProject,
    qualification_attempt_id: str,
    generation_id: str,
    output_asset_id: str,
    execution_stack_hash: str,
    profile_document_hash: str,
    target_shot_id: str,
    output_duration_milliseconds: int,
    identity_asset_id: str,
    endpoint_asset_id: str,
    motion_tail_asset_id: str,
) -> str:
    """Compute the exact scope a human must review before approval persistence."""

    tail = validate_full_source_motion_tail(
        project_root, project, motion_tail_asset_id
    )
    target = next(
        (item for item in project.shots if item.shot_id == target_shot_id), None
    )
    if target is None:
        raise _invalid("M0 endpoint feasibility target Shot is missing.")
    return _scope_fingerprint(
        project=project,
        target=target,
        identity=_asset(project, identity_asset_id),
        endpoint=_asset(project, endpoint_asset_id),
        tail=tail,
        qualification_attempt_id=qualification_attempt_id,
        generation_id=generation_id,
        output_asset_id=output_asset_id,
        execution_stack_hash=execution_stack_hash,
        profile_document_hash=profile_document_hash,
        output_duration_milliseconds=output_duration_milliseconds,
        motion_tail_asset_id=motion_tail_asset_id,
    )


def _validate_m0_endpoint_feasibility_approval(
    project_root: str | Path,
    project: LoadedProductionProject,
    approval: M0EndpointFeasibilityApproval,
    decision: M0EndpointFeasibilityHumanDecision,
) -> M0EndpointFeasibilityApproval:
    root = Path(project_root).resolve(strict=True)
    if root != project.root.resolve(strict=True):
        raise _invalid("M0 feasibility project root is not exact.")
    tail = validate_full_source_motion_tail(
        root, project, approval.motion_tail_asset_id
    )
    target = next(
        (item for item in project.shots if item.shot_id == approval.target_shot_id),
        None,
    )
    identity = _asset(project, approval.identity_asset_id)
    endpoint = _asset(project, approval.endpoint_asset_id)
    expected_scope = _scope_fingerprint(
        project=project,
        target=target,
        identity=identity,
        endpoint=endpoint,
        tail=tail,
        qualification_attempt_id=approval.attempt_id,
        generation_id=approval.generation_id,
        output_asset_id=approval.output_asset_id,
        execution_stack_hash=approval.execution_stack_hash,
        profile_document_hash=approval.profile_document_hash,
        output_duration_milliseconds=approval.output_duration_milliseconds,
        motion_tail_asset_id=approval.motion_tail_asset_id,
    ) if target is not None else None
    if (
        approval.project != project.manifest.active_project
        or approval.registry != project.manifest.active_registry
        or target is None
        or (target.revision, target.content_hash)
        != (approval.target_shot_revision, approval.target_shot_content_hash)
        or approval.identity_asset_id
        not in {
            asset_id
            for character in project.characters
            for asset_id in character.reference_asset_ids
        }
        or approval.endpoint_asset_id
        not in {
            asset_id
            for role in target.required_asset_roles
            if role.role == "approved_endpoint"
            for asset_id in role.asset_ids
        }
        or identity.sha256 != approval.identity_asset_sha256
        or endpoint.sha256 != approval.endpoint_asset_sha256
        or tail.target_shot_id != approval.target_shot_id
        or tail.target_shot_revision != approval.target_shot_revision
        or tail.target_shot_content_hash != approval.target_shot_content_hash
        or tail.terminal_frame_evidence.content_hash
        != approval.terminal_anchor_content_hash
        or tail.content_hash != approval.motion_tail_receipt_hash
        or decision.decision_id != approval.approval_id
        or decision.reviewer != approval.approved_by
        or decision.decided_at != approval.approved_at
        or decision.evidence_source_id
        != approval.human_decision_evidence_source_id
        or decision.evidence_source_sha256
        != approval.human_decision_evidence_sha256
        or decision.scope_fingerprint != expected_scope
        or decision.axis_check != approval.axis_check
        or decision.screen_direction_check != approval.screen_direction_check
        or decision.subject_scale_check != approval.subject_scale_check
        or decision.fov_check != approval.fov_check
        or decision.reachable_displacement_check
        != approval.reachable_displacement_check
        or decision.no_teleport_check != approval.no_teleport_check
    ):
        raise _invalid("M0 endpoint feasibility approval lineage changed.")
    return approval


def validate_m0_endpoint_feasibility_approval(
    project_root: str | Path,
    project: LoadedProductionProject,
    approval: M0EndpointFeasibilityApproval,
) -> M0EndpointFeasibilityApproval:
    """Validate one reopened approval against the current canonical anchors."""

    root = Path(project_root).resolve(strict=True)
    decision = reopen_m0_endpoint_feasibility_human_decision(
        root, approval.human_decision_content_hash
    )
    return _validate_m0_endpoint_feasibility_approval(
        root, project, approval, decision
    )


def reopen_m0_endpoint_feasibility_approval(
    project_root: str | Path,
    content_hash: str,
    *,
    project: LoadedProductionProject | None = None,
) -> M0EndpointFeasibilityApproval:
    """Strictly reopen a canonical approval, optionally validating active lineage."""

    root = Path(project_root).resolve(strict=True)
    try:
        path = canonical_m0_endpoint_feasibility_approval_path(content_hash)
        raw = _read_regular_file_nofollow(root / path, contained_by=root / "state")
        approval = M0EndpointFeasibilityApproval.model_validate_json(raw.data)
    except (OSError, ValueError) as exc:
        raise _invalid("Could not reopen M0 endpoint feasibility approval.", str(exc)) from exc
    if (
        approval.content_hash != content_hash
        or raw.data != _canonical_json_bytes(approval)
        or path
        != canonical_m0_endpoint_feasibility_approval_path(approval.content_hash)
    ):
        raise _invalid("M0 endpoint feasibility approval identity is invalid.")
    if project is not None:
        validate_m0_endpoint_feasibility_approval(root, project, approval)
    return approval


def prepare_m0_endpoint_feasibility_approval_commit(
    *,
    project_root: str | Path,
    committer: Any,
    project: LoadedProductionProject,
    attempt_id: str,
    human_decision: M0EndpointFeasibilityHumanDecision,
    qualification_attempt_id: str,
    generation_id: str,
    output_asset_id: str,
    execution_stack_hash: str,
    profile_document_hash: str,
    target_shot_id: str,
    output_duration_milliseconds: int,
    identity_asset_id: str,
    endpoint_asset_id: str,
    motion_tail_asset_id: str,
) -> PreparedM0EndpointFeasibilityApproval:
    """Prepare the immutable approval artifact without any Provider effect."""

    root = Path(project_root).resolve(strict=True)
    if (
        root != project.root.resolve(strict=True)
        or committer._read_manifest() != project.manifest
    ):
        raise _invalid("M0 endpoint feasibility approval base project is stale.")
    tail = validate_full_source_motion_tail(root, project, motion_tail_asset_id)
    target = next(
        (item for item in project.shots if item.shot_id == target_shot_id), None
    )
    if target is None:
        raise _invalid("M0 endpoint feasibility target Shot is missing.")
    identity = _asset(project, identity_asset_id)
    endpoint = _asset(project, endpoint_asset_id)
    try:
        decision = M0EndpointFeasibilityHumanDecision.model_validate(
            human_decision.model_dump(mode="json")
        )
    except (AttributeError, ValueError) as exc:
        raise _invalid("M0 endpoint human decision is invalid.", str(exc)) from exc
    scope_fingerprint = _scope_fingerprint(
        project=project,
        target=target,
        identity=identity,
        endpoint=endpoint,
        tail=tail,
        qualification_attempt_id=qualification_attempt_id,
        generation_id=generation_id,
        output_asset_id=output_asset_id,
        execution_stack_hash=execution_stack_hash,
        profile_document_hash=profile_document_hash,
        output_duration_milliseconds=output_duration_milliseconds,
        motion_tail_asset_id=motion_tail_asset_id,
    )
    if decision.scope_fingerprint != scope_fingerprint:
        raise _invalid("M0 endpoint human decision does not bind the exact scope.")
    approval = M0EndpointFeasibilityApproval.create(
        approval_id=decision.decision_id,
        approved_by=decision.reviewer,
        approved_at=decision.decided_at,
        human_decision_content_hash=decision.content_hash,
        human_decision_evidence_source_id=decision.evidence_source_id,
        human_decision_evidence_sha256=decision.evidence_source_sha256,
        authorization_scope="local-m0-quality-v1-one-submit",
        submit_limit=1,
        retry_allowed=False,
        fallback_allowed=False,
        attempt_id=qualification_attempt_id,
        generation_id=generation_id,
        output_asset_id=output_asset_id,
        validation_policy_id="quality-v1",
        execution_stack_hash=execution_stack_hash,
        profile_document_hash=profile_document_hash,
        project=project.manifest.active_project,
        registry=project.manifest.active_registry,
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        output_duration_milliseconds=output_duration_milliseconds,
        terminal_anchor_content_hash=tail.terminal_frame_evidence.content_hash,
        identity_asset_id=identity.asset_id,
        identity_asset_sha256=identity.sha256,
        endpoint_asset_id=endpoint.asset_id,
        endpoint_asset_sha256=endpoint.sha256,
        motion_tail_asset_id=motion_tail_asset_id,
        motion_tail_receipt_hash=tail.content_hash,
        axis_check=decision.axis_check,
        screen_direction_check=decision.screen_direction_check,
        subject_scale_check=decision.subject_scale_check,
        fov_check=decision.fov_check,
        reachable_displacement_check=decision.reachable_displacement_check,
        no_teleport_check=decision.no_teleport_check,
    )
    _validate_m0_endpoint_feasibility_approval(
        root, project, approval, decision
    )
    path = canonical_m0_endpoint_feasibility_approval_path(approval.content_hash)
    if (root / path).exists():
        reopened = reopen_m0_endpoint_feasibility_approval(
            root, approval.content_hash, project=project
        )
        if reopened != approval:
            raise _invalid("Existing M0 endpoint approval does not match replay.")
        return PreparedM0EndpointFeasibilityApproval(
            approval=approval, commit_request=None, replayed=True
        )
    base = prepare_project_registry_commit(
        manifest=project.manifest,
        project=project.project,
        registry=project.registry,
        attempt_id=attempt_id,
    )
    payload = _canonical_json_bytes(approval)
    decision_payload = _canonical_json_bytes(decision)
    artifact = PreparedArtifact(
        relative_path=path,
        payload=payload,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    decision_artifact = PreparedArtifact(
        relative_path=canonical_m0_endpoint_feasibility_human_decision_path(
            decision.content_hash
        ),
        payload=decision_payload,
        file_sha256=hashlib.sha256(decision_payload).hexdigest(),
    )
    if project.manifest.active_dependency_graph is None:
        raise _invalid("M0 endpoint feasibility requires an active dependency graph.")
    graph = committer._reopen_dependency_graph(
        project.manifest.active_dependency_graph
    )
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=project.manifest.manifest_revision,
        base_dependency_graph=project.manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=project.manifest.dependency_states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    return PreparedM0EndpointFeasibilityApproval(
        approval=approval,
        commit_request=replace(
            base,
            artifacts=tuple(
                sorted(
                    (*base.artifacts, decision_artifact, artifact),
                    key=lambda item: item.relative_path.as_posix(),
                )
            ),
            dependency_graph_transition=transition,
        ),
    )


__all__ = [
    "M0EndpointFeasibilityApproval",
    "M0EndpointFeasibilityHumanDecision",
    "PreparedM0EndpointFeasibilityApproval",
    "m0_endpoint_feasibility_scope_fingerprint",
    "prepare_m0_endpoint_feasibility_approval_commit",
    "reopen_m0_endpoint_feasibility_approval",
    "reopen_m0_endpoint_feasibility_human_decision",
    "validate_m0_endpoint_feasibility_approval",
]
