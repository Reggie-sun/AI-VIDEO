"""Explicit qualification-only operator for the rainy-station source attempt.

This module assembles the sealed source request and exposes one durable action at
a time.  It deliberately does not register an active Provider family, retry, or
fall back. Validation may prepare an inactive candidate, but never activates it.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat
import subprocess
from typing import Any, Callable

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import LoadedProductionProject
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.comfy_image import _git_head
from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_source_qualification import (
    ShotContinuitySourceQualificationCaller,
    ShotContinuitySourceQualificationProfile,
    ShotContinuitySourceQualificationProvider,
    load_source_qualification_profile,
)
from ai_video.production.shot_continuity_source_runtime import (
    make_source_production_committer,
)
from ai_video.production.shot_continuity_source_transport import (
    ComfySourceQualificationTransport,
)
from ai_video.production.shot_continuity_source_contracts import (
    SourceQualificationTransport,
)
from ai_video.production.video_compiler import (
    VideoGenerationRequestCompilation,
    compile_video_generation_request,
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
from ai_video.production.video_contracts import (
    VideoFlexibleOutputRequirement,
    VideoOutputCapability,
)
from ai_video.production.video_generation import (
    FetchedVideoCandidate,
    VideoGenerationService,
)
from ai_video.production.continuity_evaluator import FfmpegRgbFrameSampler
from ai_video.production.shot_continuity_source_review import (
    SourceBoundaryHumanDecisionV1,
    SourceBoundaryMeasurementContractV1,
    SourceBoundaryReviewerV1,
)
from ai_video.production.models import ToolIdentity


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _state_invalid(message: str) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_STATE_INVALID,
        user_message=message,
        retryable=False,
    )


def _source_frames(
    project: LoadedProductionProject,
    profile: ShotContinuitySourceQualificationProfile,
) -> tuple[Any, Any]:
    graph = project.manifest.active_dependency_graph
    if (
        graph is None
        or project.dependency_graph is None
        or project.dependency_graph.content_hash != graph.content_hash
        or project.project.content_hash != profile.project_content_hash
        or project.registry.content_hash != profile.registry_content_hash
    ):
        raise _invalid("Source qualification active project lineage is not exact.")
    try:
        target = next(
            shot for shot in project.shots if shot.shot_id == profile.target_shot_id
        )
        registry = {item.asset_id: item for item in project.registry.assets}
        frames = (
            registry[profile.first_frame_asset_id],
            registry[profile.last_frame_asset_id],
        )
    except (KeyError, StopIteration) as exc:
        raise _invalid(
            "Source qualification target or frame identity is missing.",
            str(exc),
        ) from exc
    if (
        target.revision != profile.target_shot_revision
        or target.content_hash != profile.target_shot_content_hash
    ):
        raise _invalid("Source qualification target Shot identity changed.")
    expected = (
        (
            profile.first_frame_asset_id,
            profile.first_frame_sha256,
            profile.first_frame_size_bytes,
            profile.first_frame_width,
            profile.first_frame_height,
        ),
        (
            profile.last_frame_asset_id,
            profile.last_frame_sha256,
            profile.last_frame_size_bytes,
            profile.last_frame_width,
            profile.last_frame_height,
        ),
    )
    actual = tuple(
        (
            item.asset_id,
            item.sha256,
            item.size_bytes,
            item.width,
            item.height,
        )
        for item in frames
    )
    if actual != expected or any(item.mime_type != "image/png" for item in frames):
        raise _invalid("Source qualification frame Registry lineage changed.")
    return frames


def _qualification_lineage_hashes(
    *,
    project: LoadedProductionProject,
    profile: ShotContinuitySourceQualificationProfile,
    profile_document_hash: str,
) -> tuple[str, str]:
    if len(profile_document_hash) != 64 or any(
        character not in "0123456789abcdef" for character in profile_document_hash
    ):
        raise _invalid("Source qualification profile document hash is invalid.")
    requirement_hash = canonical_sha256(
        {
            "schema": "ai-video-shot-continuity-source-qualification-requirement/1",
            "qualification_profile_document_hash": profile_document_hash,
            "qualification_profile_content_hash": profile.profile_content_hash,
            "project": project.manifest.active_project.model_dump(mode="json"),
            "registry": project.manifest.active_registry.model_dump(mode="json"),
            "dependency_graph": project.manifest.active_dependency_graph.model_dump(
                mode="json"
            ),
            "target_shot_id": profile.target_shot_id,
            "target_shot_revision": profile.target_shot_revision,
            "target_shot_content_hash": profile.target_shot_content_hash,
            "first_frame_asset_id": profile.first_frame_asset_id,
            "first_frame_sha256": profile.first_frame_sha256,
            "last_frame_asset_id": profile.last_frame_asset_id,
            "last_frame_sha256": profile.last_frame_sha256,
            "prompt_sha256": profile.prompt_sha256,
            "sealed_seed": profile.sealed_seed,
            "output_contract_hash": profile.output_contract_hash,
        }
    )
    provider_bound_request_hash = canonical_sha256(
        {
            "schema": "ai-video-shot-continuity-source-qualification-binding/1",
            "requirement_hash": requirement_hash,
            "provider_name": profile.provider_name,
            "provider_kind": profile.provider_kind,
            "model_id": profile.model_id,
            "capability_id": profile.capability_id,
            "candidate_id": profile.candidate_id,
            "provider_profile_sha256": profile.provider_profile_sha256,
            "adapter_compiler_id": profile.adapter_compiler_id,
            "adapter_compiler_version": profile.adapter_compiler_version,
            "source_execution_stack_hash": profile.source_execution_stack_hash,
            "source_profile_hash": profile.source_profile_hash,
            "source_compiler_hash": profile.source_compiler_hash,
            "source_workflow_hash": profile.source_workflow_hash,
        }
    )
    return requirement_hash, provider_bound_request_hash


def build_source_qualification_request(
    *,
    project: LoadedProductionProject,
    profile: ShotContinuitySourceQualificationProfile,
    profile_document_hash: str,
    generation_id: str,
) -> ResolvedVideoGenerationRequest:
    """Build one deterministic qualification request from active sealed truth."""

    frames = _source_frames(project, profile)
    requirement_hash, provider_bound_request_hash = _qualification_lineage_hashes(
        project=project,
        profile=profile,
        profile_document_hash=profile_document_hash,
    )
    output = VideoFlexibleOutputRequirement(
        timing_mode="frame_count",
        duration_seconds=None,
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
    projection = VideoGenerationRequestCompilation.create(
        compilation_kind="qualification",
        generation_id=generation_id,
        provider_name=profile.provider_name,
        provider_kind=profile.provider_kind,
        model_id=profile.model_id,
        provider_profile=ProviderProfilePointer(
            profile_id=profile.candidate_id,
            profile_version=f"v{profile.contract_version}",
            profile_path=Path(
                f"provider-profiles/{profile.provider_profile_sha256}.json"
            ),
            profile_sha256=profile.provider_profile_sha256,
        ),
        requirement_hash=requirement_hash,
        provider_bound_request_hash=provider_bound_request_hash,
        adapter_compiler_id=profile.adapter_compiler_id,
        adapter_compiler_version=profile.adapter_compiler_version,
        adapter_compiler_hash=profile.source_compiler_hash,
        execution_stack_hash=profile.source_execution_stack_hash,
        target_shot_id=profile.target_shot_id,
        target_shot_revision=profile.target_shot_revision,
        target_shot_content_hash=profile.target_shot_content_hash,
        target_asset_role=profile.target_asset_role,
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        prompt_text=profile.prompt,
        negative_prompt_text="",
        image_bindings=tuple(
            VideoImageReferenceBinding(
                role=role,
                asset_id=item.asset_id,
                asset_sha256=item.sha256,
                mime_type=item.mime_type,
                width=item.width,
                height=item.height,
                size_bytes=item.size_bytes,
            )
            for role, item in zip(("first_frame", "last_frame"), frames, strict=True)
        ),
        seal_terminal_frame=True,
        output_requirement=output,
        seed=profile.sealed_seed,
        base_project=project.manifest.active_project,
        base_registry=project.manifest.active_registry,
        base_dependency_graph=project.manifest.active_dependency_graph,
        input_artifact_ids=(
            profile.first_frame_asset_id,
            profile.last_frame_asset_id,
        ),
        output_asset_id=profile.output_asset_id,
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
        allowed_image_roles=("first_frame", "last_frame"),
        required_first_frame=True,
        max_reference_count=0,
        allowed_image_mime_types=("image/png",),
        max_image_bytes=max(item.size_bytes for item in frames),
        min_image_width=1,
        min_image_height=1,
        negative_prompt_supported=False,
        seed_supported=True,
        fps_supported=True,
        idempotent_submit=False,
        lookup_supported=False,
    )
    return ResolvedVideoGenerationRequest.create(
        request=request,
        capability=capability,
        effective_output=output,
        effective_seed=profile.sealed_seed,
        effective_negative_prompt_text="",
    )


def _production_tree_hash(root: Path) -> str:
    """Hash the complete Production bundle with no-follow regular-file reads."""

    bundle_root = root.resolve(strict=True)
    digest = hashlib.sha256()
    try:
        for directory, directory_names, file_names, descriptor in os.fwalk(
            bundle_root,
            topdown=True,
            follow_symlinks=False,
        ):
            current = Path(directory)
            relative_directory = current.relative_to(bundle_root).as_posix()
            directory_names.sort()
            file_names.sort()
            for name in directory_names:
                info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                    raise ValueError("bundle directory is not a regular directory")
                marker = f"d:{relative_directory}/{name}".encode("utf-8")
                digest.update(len(marker).to_bytes(8, "big"))
                digest.update(marker)
            for name in file_names:
                path = current / name
                snapshot = _read_regular_file_nofollow(
                    path,
                    contained_by=bundle_root,
                )
                relative = path.relative_to(bundle_root).as_posix().encode("utf-8")
                digest.update(len(relative).to_bytes(8, "big"))
                digest.update(relative)
                digest.update(snapshot.size_bytes.to_bytes(8, "big"))
                digest.update(bytes.fromhex(snapshot.file_sha256))
    except (OSError, RuntimeError, ValueError) as exc:
        raise _state_invalid(
            "Source qualification Production bundle could not be hashed safely."
        ) from exc
    return digest.hexdigest()


def _preflight_summary(snapshot: Any) -> dict[str, object]:
    """Project a preflight receipt without returning source image bytes."""

    try:
        p0 = snapshot.p0
        return {
            "qualification_profile_hash": snapshot.qualification_profile_hash,
            "sealed_seed": snapshot.sealed_seed,
            "p0": {
                "candidate_label": p0.candidate_label,
                "qualification_receipt_hash": p0.qualification_receipt_hash,
                "execution_stack_hash": p0.execution_stack_hash,
                "source_execution_stack_hash": p0.source_execution_stack_hash,
                "profile_hash": p0.profile_hash,
                "compiler_hash": p0.compiler_hash,
                "workflow_hash": p0.workflow_hash,
                "validation_set_hash": p0.validation_set_hash,
                "policy_hashes": p0.policy_hashes,
                "qualification_input_hashes": p0.qualification_input_hashes,
            },
            "source_execution_stack_hash": snapshot.source_execution_stack_hash,
            "source_profile_hash": snapshot.source_profile_hash,
            "source_compiler_hash": snapshot.source_compiler_hash,
            "source_workflow_hash": snapshot.source_workflow_hash,
            "project_content_hash": snapshot.project_content_hash,
            "registry_content_hash": snapshot.registry_content_hash,
            "dependency_graph_content_hash": snapshot.dependency_graph_content_hash,
            "m0_node_schema_hashes": snapshot.m0_node_schema_hashes,
            "source_node_schema_hashes": snapshot.source_node_schema_hashes,
            "component_hashes": snapshot.component_hashes,
            "inputs": tuple(
                {
                    "file_name": item.file_name,
                    "file_sha256": item.file_sha256,
                    "size_bytes": item.size_bytes,
                }
                for item in snapshot.inputs
            ),
        }
    except AttributeError as exc:
        raise _state_invalid(
            "Source qualification preflight snapshot is incomplete."
        ) from exc


@dataclass(frozen=True)
class ShotContinuitySourceOperator:
    """Expose only explicit durable source-qualification actions."""

    project_root: Path
    committer: Any
    provider: Any
    request: ResolvedVideoGenerationRequest
    attempt_id: str
    profile: ShotContinuitySourceQualificationProfile | None = None
    artifact_root: Path | None = None

    def _attempt_present(self) -> bool:
        manifest = self.committer._read_manifest()
        return any(item.attempt_id == self.attempt_id for item in manifest.attempts)

    def _video_attempt_count(self) -> int:
        manifest = self.committer._read_manifest()
        return sum(
            item.video_generation_state is not None for item in manifest.attempts
        )

    def _require_fresh_bundle(self) -> None:
        if self._video_attempt_count():
            raise _state_invalid(
                "Source qualification bundle already contains a video attempt."
            )

    def status(self) -> dict[str, object]:
        manifest = self.committer._read_manifest()
        present = any(item.attempt_id == self.attempt_id for item in manifest.attempts)
        next_action = (
            VideoGenerationService(
                committer=self.committer,
                provider=self.provider,
            ).resume_next_action(attempt_id=self.attempt_id)
            if present
            else "submit"
        )
        return {
            "attempt_id": self.attempt_id,
            "attempt_present": present,
            "video_attempt_count": sum(
                item.video_generation_state is not None for item in manifest.attempts
            ),
            "manifest_revision": manifest.manifest_revision,
            "request_hash": self.request.resolved_generation_hash,
            "next_action": next_action,
        }

    def preflight(self, *, require_new_attempt: bool = False) -> dict[str, object]:
        if require_new_attempt:
            self._require_fresh_bundle()
        before = _production_tree_hash(self.project_root)
        snapshot = self.provider.validate_pre_effect(self.request)
        after = _production_tree_hash(self.project_root)
        if before != after:
            raise _state_invalid(
                "Source qualification preflight changed durable state."
            )
        return {
            **self.status(),
            "durable_state_hash_before": before,
            "durable_state_hash_after": after,
            "durable_state_unchanged": True,
            "preflight": _preflight_summary(snapshot),
        }

    def submit(self, *, require_new_attempt: bool = False):
        if require_new_attempt:
            self._require_fresh_bundle()
        return ShotContinuitySourceQualificationCaller(
            committer=self.committer,
            provider=self.provider,
        ).qualify(
            attempt_id=self.attempt_id,
            resolved_request=self.request,
        )

    def poll(self):
        if self.status()["next_action"] != "poll":
            raise _state_invalid("Source qualification poll is not the next action.")
        return VideoGenerationService(
            committer=self.committer,
            provider=self.provider,
        ).refresh_local_once(attempt_id=self.attempt_id)

    def fetch(self) -> FetchedVideoCandidate:
        if self.status()["next_action"] != "fetch":
            raise _state_invalid("Source qualification fetch is not the next action.")
        return VideoGenerationService(
            committer=self.committer,
            provider=self.provider,
        ).fetch_local_once(attempt_id=self.attempt_id)

    def upgrade_manifest_214(self):
        current = self.committer._read_manifest()
        return self.committer.upgrade_manifest_schema(
            "2.14", expected_manifest_revision=current.manifest_revision
        )

    def build_source_boundary_reviewer(
        self,
        *,
        human_decision_path: str | Path,
        ffmpeg_path: str | Path,
    ) -> SourceBoundaryReviewerV1:
        profile = self.profile
        artifact_root = self.artifact_root
        if profile is None or artifact_root is None:
            raise _state_invalid(
                "Source boundary reviewer requires the sealed qualification profile."
            )
        manifest = self.committer._read_manifest()
        if manifest.schema_version != "2.14":
            raise _state_invalid(
                "Source boundary reviewer requires Production Manifest 2.14."
            )
        p0_receipt, _, _, _, _ = self.committer.reopen_p0_qualification_prepared()
        decision_path = Path(human_decision_path).resolve(strict=True)
        decision_raw = _read_regular_file_nofollow(
            decision_path, contained_by=artifact_root
        )
        try:
            decision = SourceBoundaryHumanDecisionV1.model_validate_json(
                decision_raw.data
            )
        except ValueError as exc:
            raise _state_invalid("Source boundary human decision is invalid.") from exc
        executable = Path(ffmpeg_path).resolve(strict=True)
        if not executable.is_file():
            raise _state_invalid("Source boundary ffmpeg executable is invalid.")
        try:
            version_line = subprocess.run(
                [str(executable), "-version"],
                check=True,
                capture_output=True,
                text=True,
                env={"LANG": "C", "LC_ALL": "C"},
                timeout=10,
            ).stdout.splitlines()[0]
            version = version_line.split()[2]
        except (IndexError, OSError, subprocess.SubprocessError) as exc:
            raise _state_invalid(
                "Source boundary ffmpeg identity is unreadable."
            ) from exc
        identity = ToolIdentity(name="ffmpeg", version=version)
        contract = SourceBoundaryMeasurementContractV1.create(
            p0_qualification_receipt_hash=p0_receipt.content_hash,
            p0_rubric_hash=p0_receipt.rubric_hash,
            first_frame_asset_id=profile.first_frame_asset_id,
            first_frame_sha256=profile.first_frame_sha256,
            last_frame_asset_id=profile.last_frame_asset_id,
            last_frame_sha256=profile.last_frame_sha256,
            sample_width=profile.width,
            sample_height=profile.height,
            decoder=identity,
        )
        project = load_production_project(self.project_root / "project.yaml")
        try:
            first_path = project.asset_paths[profile.first_frame_asset_id]
            last_path = project.asset_paths[profile.last_frame_asset_id]
            first = _read_regular_file_nofollow(
                first_path, contained_by=self.project_root / "assets"
            )
            last = _read_regular_file_nofollow(
                last_path, contained_by=self.project_root / "assets"
            )
        except (KeyError, OSError, ValueError) as exc:
            raise _state_invalid(
                "Source boundary anchors could not be reopened."
            ) from exc
        return SourceBoundaryReviewerV1(
            source_profile_content_hash=profile.profile_content_hash,
            source_execution_stack_hash=profile.source_execution_stack_hash,
            measurement_contract=contract,
            human_decision=decision,
            evaluator=ToolIdentity(name="ai-video-source-boundary-review", version="1"),
            sampler=FfmpegRgbFrameSampler(
                executable=executable,
                identity=identity,
                sample_width=profile.width,
                sample_height=profile.height,
            ),
            first_anchor_bytes=first.data,
            last_anchor_bytes=last.data,
        )

    def validate(
        self,
        *,
        source_boundary_reviewer=None,
        human_decision_path: str | Path | None = None,
        ffmpeg_path: str | Path | None = None,
        probe=None,
    ):
        if self.status()["next_action"] != "validate":
            raise _state_invalid(
                "Source qualification validate is not the next action."
            )
        reviewer = source_boundary_reviewer
        if reviewer is None:
            if human_decision_path is None or ffmpeg_path is None:
                raise _state_invalid(
                    "Source qualification validate requires exact human decision and ffmpeg inputs."
                )
            reviewer = self.build_source_boundary_reviewer(
                human_decision_path=human_decision_path,
                ffmpeg_path=ffmpeg_path,
            )
        return self.committer.prepare_video_activation_candidate(
            attempt_id=self.attempt_id,
            probe=probe,
            source_boundary_reviewer=reviewer,
        )


def open_source_qualification_operator(
    *,
    project_root: str | Path,
    artifact_root: str | Path,
    comfy_root: str | Path,
    qualification_profile_path: str | Path,
    m0_profile_path: str | Path,
    generation_id: str,
    attempt_id: str,
    transport: SourceQualificationTransport | None = None,
    commit_resolver: Callable[[], str] | None = None,
) -> ShotContinuitySourceOperator:
    """Open the real qualification stack without performing a Provider action."""

    root = Path(project_root).resolve(strict=True)
    artifacts = Path(artifact_root).resolve(strict=True)
    comfy = Path(comfy_root).resolve(strict=True)
    project = load_production_project(root / "project.yaml")
    profile, document_hash = load_source_qualification_profile(
        qualification_profile_path,
        artifact_root=artifacts,
    )
    request = build_source_qualification_request(
        project=project,
        profile=profile,
        profile_document_hash=document_hash,
        generation_id=generation_id,
    )
    committer = make_source_production_committer(root, project)
    selected_transport = transport or ComfySourceQualificationTransport()
    selected_commit_resolver = commit_resolver or (lambda: _git_head(comfy))
    provider = ShotContinuitySourceQualificationProvider(
        committer=committer,
        qualification_profile_path=qualification_profile_path,
        m0_profile_path=m0_profile_path,
        artifact_root=artifacts,
        project_root=root,
        comfy_root=comfy,
        transport=selected_transport,
        project_loader=lambda: load_production_project(root / "project.yaml"),
        commit_resolver=selected_commit_resolver,
    )
    return ShotContinuitySourceOperator(
        project_root=root,
        committer=committer,
        provider=provider,
        request=request,
        attempt_id=attempt_id,
        profile=profile,
        artifact_root=artifacts,
    )


__all__ = [
    "ShotContinuitySourceOperator",
    "build_source_qualification_request",
    "open_source_qualification_operator",
]
