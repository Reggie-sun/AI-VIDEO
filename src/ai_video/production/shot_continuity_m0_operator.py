"""Explicit quality-v1 M0 qualification operator.

The operator opens only the already materialized inactive M0 stack.  It never
selects fast-v1, retries, falls back, activates a capability, or advances M1.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._video_continuity import (
    C4ApprovedEndpointEvidence,
    C4FeasibilityReceipt,
    C4IdentityAnchorEvidence,
    C4MultiAnchorBinding,
    C4SemanticBoundaryState,
    ContinuityArtifactIdentity,
    ContinuityConstraintSet,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import LoadedProductionProject
from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_m0_caller import (
    M0AcceptedUpstreamSnapshot,
    M0QualificationCaller,
    M0QualificationProvider,
)
from ai_video.production.shot_continuity_m0_feasibility import (
    M0EndpointFeasibilityApproval,
    reopen_m0_endpoint_feasibility_approval,
    validate_m0_endpoint_feasibility_approval,
)
from ai_video.production.shot_continuity_m0_policy import (
    M0ValidationPolicy,
    M0ValidationPolicyId,
)
from ai_video.production.shot_continuity_m0_qualification import (
    M0_REFERENCE_VIDEO_MAX_DURATION_MILLISECONDS,
    M0_REFERENCE_VIDEO_MIN_DURATION_MILLISECONDS,
    M0QualificationExecutionSources,
    load_m0_qualification_execution_sources,
)
from ai_video.production.shot_continuity_m0_motion_tail import (
    validate_m0_motion_tail,
)
from ai_video.production.shot_continuity_source_runtime import (
    make_source_production_committer,
)
from ai_video.production.shot_continuity_source_transport import (
    ComfySourceQualificationTransport,
)
from ai_video.production.video import (
    BillingKind,
    ProviderProfilePointer,
    ResolvedVideoGenerationRequest,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoImageReferenceBinding,
)
from ai_video.production.video_compiler import (
    VideoGenerationRequestCompilation,
    compile_video_generation_request,
)
from ai_video.production.video_contracts import (
    VideoBindingCardinalityConstraint,
    VideoFlexibleOutputRequirement,
    VideoMediaCapability,
    VideoMediaReferenceBinding,
    VideoOutputCapability,
)
from ai_video.production.video_generation import (
    FetchedVideoCandidate,
    VideoGenerationService,
)


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_STATE_INVALID,
        user_message=message,
        retryable=False,
    )


def _asset(project: LoadedProductionProject, asset_id: str):
    try:
        return next(
            item for item in project.registry.assets if item.asset_id == asset_id
        )
    except StopIteration as exc:
        raise _invalid(f"M0 anchor {asset_id} is not registered.") from exc


def _m0_constraints(project: LoadedProductionProject) -> ContinuityConstraintSet:
    scene = project.scenes[0]
    character = project.characters[0]
    return ContinuityConstraintSet.create(
        scene_identity=ContinuityArtifactIdentity(
            artifact_id=scene.artifact_id,
            revision=scene.revision,
            content_hash=scene.content_hash,
        ),
        character_identities=(
            ContinuityArtifactIdentity(
                artifact_id=character.artifact_id,
                revision=character.revision,
                content_hash=character.content_hash,
            ),
        ),
        camera_axis="screen-right side profile",
        framing="chest-height medium 50mm-equivalent parallel tracking",
        lighting="rain-soaked railway platform at blue hour",
        color="cool blue-hour platform with mustard-yellow raincoat",
        motion_direction="subject and camera continue screen-right",
        exit_state="accepted source gait phase at exact terminal frame",
        entrance_state="preserve gait phase then decelerate toward A4 endpoint",
    )


def build_m0_quality_request(
    *,
    project: LoadedProductionProject,
    sources: M0QualificationExecutionSources,
    prompt: str,
    attempt_id: str,
    generation_id: str,
    output_asset_id: str,
    identity_asset_id: str,
    endpoint_asset_id: str,
    motion_tail_asset_id: str,
    feasibility_approval: M0EndpointFeasibilityApproval,
    execution_stack_hash: str,
) -> ResolvedVideoGenerationRequest:
    """Build one hash-bound C4 request from current active canonical evidence."""

    profile = sources.profile
    validate_m0_endpoint_feasibility_approval(
        project.root, project, feasibility_approval
    )
    if (
        project.project.content_hash != profile.project_content_hash
        or project.registry.content_hash != profile.registry_content_hash
    ):
        raise _invalid("M0 profile does not bind the active Project and Registry.")
    import hashlib

    if hashlib.sha256(prompt.encode("utf-8")).hexdigest() != profile.prompt_sha256:
        raise _invalid("M0 prompt does not match the sealed quality profile.")
    receipt = validate_m0_motion_tail(
        project.root,
        project,
        motion_tail_asset_id,
    )
    tail_asset = _asset(project, motion_tail_asset_id)
    tail = receipt.to_c4_motion_tail_evidence(
        registry_revision_id=project.registry.revision_id,
        tail_asset=tail_asset,
    )
    terminal = receipt.terminal_frame_evidence
    terminal_asset = _asset(project, terminal.extracted_asset_id)
    identity_asset = _asset(project, identity_asset_id)
    endpoint_asset = _asset(project, endpoint_asset_id)
    target = next(
        (item for item in project.shots if item.shot_id == receipt.target_shot_id),
        None,
    )
    character = project.characters[0]
    if (
        target is None
        or identity_asset_id not in character.reference_asset_ids
        or endpoint_asset_id
        not in {
            asset_id
            for role in target.required_asset_roles
            if role.role == "approved_endpoint"
            for asset_id in role.asset_ids
        }
        or terminal_asset.creation_receipt_id != terminal.extraction_receipt_id
    ):
        raise _invalid("M0 exact identity, endpoint, or terminal selection changed.")
    constraints = _m0_constraints(project)
    if receipt.continuity_constraint_snapshot_hash != constraints.content_hash:
        raise _invalid("M0 motion-tail continuity constraint closure changed.")
    identity = C4IdentityAnchorEvidence.create(
        character_artifact_id=character.artifact_id,
        character_revision=character.revision,
        character_content_hash=character.content_hash,
        registry_revision_id=project.registry.revision_id,
        asset_id=identity_asset.asset_id,
        asset_sha256=identity_asset.sha256,
        asset_mime_type=identity_asset.mime_type,
        asset_size_bytes=identity_asset.size_bytes,
        asset_width=identity_asset.width,
        asset_height=identity_asset.height,
        source_provenance_receipt_id=identity_asset.creation_receipt_id,
        source_provenance_receipt_sha256=identity_asset.creation_receipt_id,
        materialization_receipt_id=identity_asset.creation_receipt_id,
        materialization_receipt_sha256=identity_asset.creation_receipt_id,
    )
    duration_milliseconds = round(profile.frame_count * 1000 / profile.fps)
    if (
        feasibility_approval.output_duration_milliseconds
        != duration_milliseconds
        or feasibility_approval.identity_asset_id != identity_asset_id
        or feasibility_approval.endpoint_asset_id != endpoint_asset_id
        or feasibility_approval.motion_tail_asset_id != motion_tail_asset_id
        or feasibility_approval.terminal_anchor_content_hash != terminal.content_hash
        or feasibility_approval.motion_tail_receipt_hash != receipt.content_hash
        or feasibility_approval.attempt_id != attempt_id
        or feasibility_approval.generation_id != generation_id
        or feasibility_approval.output_asset_id != output_asset_id
        or feasibility_approval.validation_policy_id != "quality-v1"
        or feasibility_approval.execution_stack_hash != execution_stack_hash
        or feasibility_approval.profile_document_hash != sources.profile_document_hash
    ):
        raise _invalid("M0 endpoint feasibility approval does not match the request.")
    feasibility = C4FeasibilityReceipt.create(
        receipt_id=feasibility_approval.content_hash,
        human_approval_receipt_id=feasibility_approval.content_hash,
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        output_duration_milliseconds=duration_milliseconds,
        terminal_anchor_content_hash=terminal.content_hash,
        identity_anchor_content_hash=identity.content_hash,
        motion_tail_content_hash=tail.content_hash,
        feasibility_decision="PASS",
        axis_check=feasibility_approval.axis_check,
        screen_direction_check=feasibility_approval.screen_direction_check,
        subject_scale_check=feasibility_approval.subject_scale_check,
        fov_check=feasibility_approval.fov_check,
        reachable_displacement_check=feasibility_approval.reachable_displacement_check,
        no_teleport_check=feasibility_approval.no_teleport_check,
    )
    endpoint = C4ApprovedEndpointEvidence.create(
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        registry_revision_id=project.registry.revision_id,
        asset_id=endpoint_asset.asset_id,
        asset_sha256=endpoint_asset.sha256,
        asset_mime_type=endpoint_asset.mime_type,
        asset_size_bytes=endpoint_asset.size_bytes,
        asset_width=endpoint_asset.width,
        asset_height=endpoint_asset.height,
        source_provenance_receipt_id=endpoint_asset.creation_receipt_id,
        source_provenance_receipt_sha256=endpoint_asset.creation_receipt_id,
        materialization_receipt_id=endpoint_asset.creation_receipt_id,
        materialization_receipt_sha256=endpoint_asset.creation_receipt_id,
        duration_milliseconds=duration_milliseconds,
        feasibility_receipt=feasibility,
    )
    semantic = C4SemanticBoundaryState.create(
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        open_state=("exact source terminal pixels", "accepted gait and camera phase"),
        must_hold=(
            "canonical traveler identity",
            "wardrobe and red satchel",
            "screen-right axis",
        ),
        changes_here=("natural deceleration toward the approved A4 pose",),
        close_state=(
            "exact approved A4 endpoint pose, scale, FOV, and camera endpoint",
        ),
    )
    c4 = C4MultiAnchorBinding.create(
        tier="motion_boundary",
        selected_registry_revision_id=project.registry.revision_id,
        terminal_materialization_receipt_id=terminal_asset.creation_receipt_id,
        terminal_materialization_receipt_sha256=terminal_asset.creation_receipt_id,
        terminal_source_provenance_receipt_sha256=terminal.source_provenance_receipt_id,
        terminal=terminal,
        identity_anchor=identity,
        approved_endpoint=endpoint,
        motion_tail=tail,
        semantic_boundary=semantic,
        constraints=constraints,
    )
    output = VideoFlexibleOutputRequirement(
        timing_mode="frame_count",
        frame_count=profile.frame_count,
        dimension_mode="exact",
        width=profile.width,
        height=profile.height,
        resolution_label="h3_native",
        ratio="adaptive",
        fps=profile.fps,
        container="mp4",
        mime_type="video/mp4",
        native_audio=profile.native_audio,
    )
    image_bindings = (
        VideoImageReferenceBinding(
            role="first_frame",
            asset_id=terminal.extracted_asset_id,
            asset_sha256=terminal.extracted_sha256,
            mime_type=terminal.extracted_mime_type,
            width=terminal.extracted_width,
            height=terminal.extracted_height,
            size_bytes=terminal.extracted_size_bytes,
        ),
        VideoImageReferenceBinding(
            role="last_frame",
            asset_id=endpoint.asset_id,
            asset_sha256=endpoint.asset_sha256,
            mime_type=endpoint.asset_mime_type,
            width=endpoint.asset_width,
            height=endpoint.asset_height,
            size_bytes=endpoint.asset_size_bytes,
        ),
        VideoImageReferenceBinding(
            role="reference",
            asset_id=identity.asset_id,
            asset_sha256=identity.asset_sha256,
            mime_type=identity.asset_mime_type,
            width=identity.asset_width,
            height=identity.asset_height,
            size_bytes=identity.asset_size_bytes,
        ),
    )
    media_bindings = (
        VideoMediaReferenceBinding(
            kind="video",
            role="reference_video",
            asset_id=tail.extracted_asset_id,
            asset_sha256=tail.extracted_sha256,
            mime_type=tail.extracted_mime_type,
            duration_millis=tail.extracted_duration_milliseconds,
            size_bytes=tail.extracted_size_bytes,
            width=tail.extracted_width,
            height=tail.extracted_height,
            fps=tail.extracted_fps_numerator // tail.extracted_fps_denominator,
        ),
    )
    lineage = {
        "schema": "ai-video-m0-quality-request-lineage/1",
        "profile_document_hash": sources.profile_document_hash,
        "p0_receipt_hash": profile.prepared_receipt_hash,
        "c4_binding_hash": c4.binding_hash,
    }
    requirement_hash = canonical_sha256(lineage)
    provider_bound_request_hash = canonical_sha256(
        {
            **lineage,
            "requirement_hash": requirement_hash,
            "generation_id": generation_id,
        }
    )
    projection = VideoGenerationRequestCompilation.create(
        compilation_kind="c4_qualification",
        generation_id=generation_id,
        provider_name=profile.provider_kind,
        provider_kind=profile.provider_kind,
        model_id=profile.model_id,
        provider_profile=ProviderProfilePointer(
            profile_id=profile.candidate_id,
            profile_version=f"v{profile.contract_version}",
            profile_path=Path(
                f"provider-profiles/{sources.profile_document_hash}.json"
            ),
            profile_sha256=sources.profile_document_hash,
        ),
        requirement_hash=requirement_hash,
        provider_bound_request_hash=provider_bound_request_hash,
        adapter_compiler_id="ai-video-m0-c4-qualification",
        adapter_compiler_version="1",
        adapter_compiler_hash=sources.materialization.compiler_hash,
        execution_stack_hash=execution_stack_hash,
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        target_asset_role="approved_endpoint",
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        prompt_text=prompt,
        negative_prompt_text="",
        image_bindings=image_bindings,
        c4_multi_anchor_binding=c4,
        seal_terminal_frame=True,
        media_bindings=media_bindings,
        output_requirement=output,
        seed=profile.sealed_seed,
        base_project=project.manifest.active_project,
        base_registry=project.manifest.active_registry,
        base_dependency_graph=project.manifest.active_dependency_graph,
        input_artifact_ids=tuple(
            sorted(
                {
                    target.shot_id,
                    terminal.source_shot_id,
                    terminal.source_video_asset_id,
                    terminal.extracted_asset_id,
                    terminal.source_provenance_receipt_id,
                    terminal.extraction_receipt_id,
                    terminal_asset.creation_receipt_id,
                    identity.asset_id,
                    identity.source_provenance_receipt_id,
                    identity.materialization_receipt_id,
                    endpoint.asset_id,
                    endpoint.source_provenance_receipt_id,
                    endpoint.materialization_receipt_id,
                    feasibility.receipt_id,
                    feasibility.human_approval_receipt_id,
                    tail.extracted_asset_id,
                    tail.source_p6_acceptance_evidence_id,
                    tail.extraction_receipt_id,
                    tail.materialization_receipt_id,
                }
            )
        ),
        output_asset_id=output_asset_id,
    )
    request = compile_video_generation_request(projection)
    capability = VideoCapabilityVariant(
        capability_id=profile.capability_id,
        provider_kind=profile.provider_kind,
        model_id=profile.model_id,
        profile_version=f"v{profile.contract_version}",
        execution_kind=VideoExecutionKind.LOCAL,
        billing_kind=BillingKind.LOCAL_UNMETERED,
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        output_capability=VideoOutputCapability(
            min_duration_seconds=1,
            max_duration_seconds=60,
            provider_selected_duration=False,
            timing_modes=("frame_count",),
            frame_count_min=profile.frame_count,
            frame_count_max=profile.frame_count,
            frame_count_step=1,
            frame_count_remainder=0,
            dimension_modes=("exact",),
            min_width=profile.width,
            max_width=profile.width,
            min_height=profile.height,
            max_height=profile.height,
            dimension_multiple=1,
            resolution_labels=("h3_native",),
            ratios=("adaptive",),
            fps_values=(profile.fps,),
            containers=("mp4",),
            native_audio_options=(profile.native_audio,),
        ),
        allowed_image_roles=("first_frame", "last_frame", "reference"),
        required_first_frame=True,
        max_reference_count=1,
        allowed_image_mime_types=("image/png",),
        max_image_bytes=max(item.size_bytes for item in image_bindings),
        min_image_width=1,
        min_image_height=1,
        media_capabilities=(
            VideoMediaCapability(
                kind="video",
                roles=("reference_video",),
                min_count=1,
                max_count=1,
                allowed_mime_types=("video/mp4",),
                max_size_bytes=tail.extracted_size_bytes,
                min_duration_millis=M0_REFERENCE_VIDEO_MIN_DURATION_MILLISECONDS,
                max_duration_millis=M0_REFERENCE_VIDEO_MAX_DURATION_MILLISECONDS,
            ),
        ),
        negative_prompt_supported=False,
        seed_supported=True,
        fps_supported=True,
        idempotent_submit=False,
        lookup_supported=False,
        binding_cardinality_constraints=(
            VideoBindingCardinalityConstraint(
                roles=("first_frame",), min_count=1, max_count=1
            ),
            VideoBindingCardinalityConstraint(
                roles=("last_frame",), min_count=1, max_count=1
            ),
            VideoBindingCardinalityConstraint(
                roles=("reference",), min_count=1, max_count=1
            ),
            VideoBindingCardinalityConstraint(
                roles=("reference_video",), min_count=1, max_count=1
            ),
            VideoBindingCardinalityConstraint(
                roles=("reference_audio",), min_count=0, max_count=0
            ),
            VideoBindingCardinalityConstraint(
                roles=(
                    "first_frame",
                    "last_frame",
                    "reference",
                    "reference_video",
                    "reference_audio",
                ),
                min_count=4,
                max_count=4,
            ),
        ),
    )
    return ResolvedVideoGenerationRequest.create(
        request=request,
        capability=capability,
        effective_output=output,
        effective_seed=profile.sealed_seed,
        effective_negative_prompt_text="",
    )


def _quality_policy(committer: Any, quality_sources) -> M0ValidationPolicy:
    _, stacks, _, _, inputs = committer.reopen_p0_qualification_prepared(
        required_materialized_candidates=("m0",)
    )
    rubric_hash = next(
        item.content_hash for item in inputs if item.input_kind == "rubric"
    )
    return M0ValidationPolicy.create(
        policy_id=M0ValidationPolicyId.QUALITY_V1,
        profile_document_hash=quality_sources.profile_document_hash,
        execution_stack_hash=stacks[0].execution_stack_hash,
        rubric_hash=rubric_hash,
        conclusion_scope="m0_qualification",
        conclusion_capability_id=quality_sources.profile.capability_id,
    )


def _runtime_revisions(inputs: tuple[Any, ...]) -> tuple[tuple[str, str], ...]:
    try:
        inventory = next(item for item in inputs if item.input_kind == "inventory")
        payload = inventory.payload
        revisions = (
            ("comfyui", payload["comfyui"]["commit"]),
            ("minimax-h3-audio-t8", payload["t8_plugin"]["commit"]),
            ("videohelpersuite", payload["videohelpersuite_commit"]),
        )
        if (
            payload["remote_provider_enabled"] is not False
            or payload["cloud_fallback_enabled"] is not False
            or any(
                len(revision) != 40
                or any(character not in "0123456789abcdef" for character in revision)
                for _, revision in revisions
            )
        ):
            raise ValueError("runtime inventory is not exact and local-only")
    except (KeyError, StopIteration, TypeError, ValueError) as exc:
        raise _invalid("M0 runtime inventory is incomplete.") from exc
    return revisions


def _accepted_upstream_reopener(root: Path, committer: Any):
    def reopen(*, project, source_video_asset_id: str, motion_tail_asset_id: str):
        receipt = validate_m0_motion_tail(root, project, motion_tail_asset_id)
        tail_asset = _asset(project, receipt.tail_asset_id)
        source_stacks = committer.reopen_p0_qualification_source_stacks(
            require_materialized=True
        )
        if (
            receipt.source_video_asset_id != source_video_asset_id
            or len(source_stacks) != 1
        ):
            raise _invalid("M0 accepted upstream selector changed.")
        return M0AcceptedUpstreamSnapshot(
            terminal_evidence_hash=receipt.terminal_frame_evidence.content_hash,
            source_shot_id=receipt.source_shot_id,
            source_shot_revision=receipt.source_shot_revision,
            source_shot_content_hash=receipt.source_shot_content_hash,
            source_video_asset_id=receipt.source_video_asset_id,
            source_video_sha256=receipt.source_video_sha256,
            source_registry_revision_id=receipt.source_registry_revision_id,
            source_generation_id=receipt.source_generation_id,
            source_request_input_hash=receipt.source_request_input_hash,
            source_resolved_generation_hash=receipt.source_resolved_generation_hash,
            source_execution_stack_hash=source_stacks[0].execution_stack_hash,
            source_provenance_receipt_id=receipt.source_provenance_receipt_id,
            source_provenance_receipt_sha256=receipt.source_provenance_receipt_sha256,
            source_p6_acceptance_evidence_id=receipt.source_p6_acceptance_evidence_id,
            source_p6_acceptance_evidence_sha256=receipt.source_p6_acceptance_evidence_sha256,
            motion_tail_registry_revision_id=project.registry.revision_id,
            motion_tail_extraction_receipt_id=receipt.content_hash,
            motion_tail_extraction_receipt_sha256=receipt.content_hash,
            motion_tail_materialization_receipt_id=receipt.content_hash,
            motion_tail_materialization_receipt_sha256=receipt.content_hash,
            motion_tail_asset_id=receipt.tail_asset_id,
            motion_tail_asset_sha256=tail_asset.sha256,
        )

    return reopen


def _feasibility_approval_reopener(root: Path):
    def reopen(*, project, content_hash: str):
        return reopen_m0_endpoint_feasibility_approval(
            root, content_hash, project=project
        )

    return reopen


@dataclass(frozen=True)
class ShotContinuityM0Operator:
    project_root: Path
    committer: Any
    provider: M0QualificationProvider
    caller: M0QualificationCaller
    request: ResolvedVideoGenerationRequest
    attempt_id: str

    def status(self) -> dict[str, object]:
        manifest = self.committer._read_manifest()
        attempt = next(
            (item for item in manifest.attempts if item.attempt_id == self.attempt_id),
            None,
        )
        present = attempt is not None
        if present:
            state = getattr(attempt, "video_generation_state", None)
            if (
                getattr(attempt, "operation", None) != "video_generation"
                or state is None
                or self.committer._reopen_video_request(
                    state.request
                ).resolved_generation_hash
                != self.request.resolved_generation_hash
            ):
                raise _invalid("M0 existing attempt does not match the exact request.")
        next_action = (
            VideoGenerationService(
                committer=self.committer, provider=self.provider
            ).resume_next_action(attempt_id=self.attempt_id)
            if present
            else "submit"
        )
        return {
            "attempt_id": self.attempt_id,
            "attempt_present": present,
            "manifest_revision": manifest.manifest_revision,
            "request_hash": self.request.resolved_generation_hash,
            "next_action": next_action,
        }

    def preflight(self) -> dict[str, object]:
        snapshot = self.caller.validate_pre_effect(
            attempt_id=self.attempt_id,
            resolved_request=self.request,
        )
        return {
            **self.status(),
            "policy": M0ValidationPolicyId.QUALITY_V1.value,
            "sealed_seed": snapshot.sources.profile.sealed_seed,
            "source_video_sha256": snapshot.source_video_sha256,
            "input_sha256": tuple(item.file_sha256 for item in snapshot.uploads),
        }

    def submit(self):
        if self.status()["next_action"] != "submit":
            raise _invalid("M0 submit is not the next durable action.")
        return self.caller.qualify(
            attempt_id=self.attempt_id,
            resolved_request=self.request,
        )

    def poll(self):
        if self.status()["next_action"] != "poll":
            raise _invalid("M0 poll is not the next durable action.")
        return VideoGenerationService(
            committer=self.committer, provider=self.provider
        ).refresh_local_once(attempt_id=self.attempt_id)

    def fetch(self) -> FetchedVideoCandidate:
        if self.status()["next_action"] != "fetch":
            raise _invalid("M0 fetch is not the next durable action.")
        return VideoGenerationService(
            committer=self.committer, provider=self.provider
        ).fetch_local_once(attempt_id=self.attempt_id)


def open_m0_quality_operator(
    *,
    project_root: str | Path,
    artifact_root: str | Path,
    comfy_root: str | Path,
    profile_path: str | Path,
    generation_id: str,
    output_asset_id: str,
    attempt_id: str,
    identity_asset_id: str,
    endpoint_asset_id: str,
    motion_tail_asset_id: str,
    feasibility_approval_hash: str,
    transport: Any | None = None,
) -> ShotContinuityM0Operator:
    root = Path(project_root).resolve(strict=True)
    artifacts = Path(artifact_root).resolve(strict=True)
    project = load_production_project(root / "project.yaml")
    committer = make_source_production_committer(root, project)
    sources = load_m0_qualification_execution_sources(
        profile_path=profile_path,
        artifact_root=artifacts,
    )
    _, stacks, _, _, inputs = committer.reopen_p0_qualification_prepared(
        required_materialized_candidates=("m0",)
    )
    prompt = next(
        item.payload["prompt"]
        for item in inputs
        if item.input_kind == "calibration_fixture"
    )
    approval = reopen_m0_endpoint_feasibility_approval(
        root, feasibility_approval_hash, project=project
    )
    request = build_m0_quality_request(
        project=project,
        sources=sources,
        prompt=prompt,
        attempt_id=attempt_id,
        generation_id=generation_id,
        output_asset_id=output_asset_id,
        identity_asset_id=identity_asset_id,
        endpoint_asset_id=endpoint_asset_id,
        motion_tail_asset_id=motion_tail_asset_id,
        feasibility_approval=approval,
        execution_stack_hash=stacks[0].execution_stack_hash,
    )
    selected_transport = transport or ComfySourceQualificationTransport()
    provider = M0QualificationProvider(
        profile_path=profile_path,
        artifact_root=artifacts,
        input_root=root / "assets",
        transport=selected_transport,
        asset_resolver=lambda asset_id, asset_sha256: project.asset_paths[asset_id],
        m0_policy_id=M0ValidationPolicyId.QUALITY_V1,
        comfy_root=comfy_root,
        runtime_revisions=_runtime_revisions(inputs),
    )
    selected_policy = _quality_policy(committer, sources)
    caller = M0QualificationCaller(
        committer=committer,
        provider=provider,
        profile_path=profile_path,
        artifact_root=artifacts,
        project_loader=lambda: load_production_project(root / "project.yaml"),
        accepted_upstream_reopener=_accepted_upstream_reopener(root, committer),
        feasibility_approval_reopener=_feasibility_approval_reopener(root),
        selected_policy=selected_policy,
    )
    return ShotContinuityM0Operator(
        project_root=root,
        committer=committer,
        provider=provider,
        caller=caller,
        request=request,
        attempt_id=attempt_id,
    )


__all__ = [
    "ShotContinuityM0Operator",
    "build_m0_quality_request",
    "open_m0_quality_operator",
]
