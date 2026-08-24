"""Qualification-only caller for the Shot Continuity upstream source video."""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Literal, Mapping

from pydantic import Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.comfy_image import (
    _missing_required_node_inputs,
    validate_loopback_endpoint,
)
from ai_video.production.comfy_video import render_h3_workflow
from ai_video.production.hashing import canonical_sha256
from ai_video.production.local_video import (
    DurableLocalVideoSubmitPermit,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
)
from ai_video.production.models import StrictModel
from ai_video.production.paths import (
    _open_regular_file_nofollow,
    _read_regular_file_nofollow,
)
from ai_video.production.shot_continuity_m0_qualification import (
    M0ValidationPreflightSnapshot,
    load_m0_qualification_execution_sources,
    m0_node_schema_seals,
    reopen_m0_validation_preflight,
    validate_m0_live_node_schemas,
)
from ai_video.production.shot_continuity_source_stack import (
    ShotContinuitySourceExecutionSources,
    reopen_materialized_shot_continuity_source_execution_sources,
)
from ai_video.production.shot_continuity_source_contracts import (
    ShotContinuitySourceQualificationOutcome,
    SourceQualificationInput,
    SourceQualificationPreflightSnapshot,
    SourceQualificationTransport,
)
from ai_video.production.shot_continuity_source_schema import (
    SOURCE_REQUIRED_NODES,
    SourceQualificationNodeSchemaSeal,
    source_node_schema_seals,
)
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoGenerationPreview,
)
from ai_video.production.video_generation import VideoGenerationService


_SHA256 = r"^[0-9a-f]{64}$"
_MAX_SEED = (1 << 63) - 1
_COMPONENT_DIRS = {
    "diffusion": Path("models/diffusion_models"),
    "text_encoder": Path("models/text_encoders"),
    "video_vae": Path("models/vae"),
    "audio_vae": Path("models/vae"),
}
_SEED_FIELDS = (
    "source_execution_stack_hash",
    "p0_qualification_receipt_hash",
    "m0_execution_stack_hash",
    "project_content_hash",
    "registry_content_hash",
    "target_shot_content_hash",
    "first_frame_sha256",
    "last_frame_sha256",
    "prompt_sha256",
    "output_contract_hash",
)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _value(value: object) -> object:
    return getattr(value, "value", value)


def derive_source_qualification_seed(values: Mapping[str, object]) -> int:
    try:
        payload = {field: values[field] for field in _SEED_FIELDS}
    except KeyError as exc:
        raise ValueError("source qualification seed closure is incomplete") from exc
    digest = canonical_sha256(
        {"schema": "ai-video-source-qualification-seed/1", **payload}
    )
    return int(digest[:16], 16) & _MAX_SEED


class ShotContinuitySourceQualificationProfile(StrictModel):
    """Content-addressed request and P0 closure for one upstream source attempt."""

    schema_version: Literal["1"]
    status: Literal["qualification_only"]
    provider_name: Literal["comfy-local-h3"]
    provider_kind: Literal["minimax_h3_fl2va"]
    deployment_identity: Literal["loopback-127.0.0.1-8188"]
    loopback_endpoint: Literal["http://127.0.0.1:8188"]
    model_id: Literal["minimax-h3-fl2va"]
    capability_id: Literal["minimax-h3-fl2va-local-v1"]
    candidate_id: Literal["minimax-h3-fl2va-rainy-station-source-v1"]
    contract_version: Literal["1"]
    provider_profile_sha256: str = Field(pattern=_SHA256)
    adapter_compiler_id: Literal["comfy-local-h3-video-compiler"]
    adapter_compiler_version: Literal["1"]
    source_execution_stack_hash: str = Field(pattern=_SHA256)
    source_profile_hash: str = Field(pattern=_SHA256)
    source_compiler_hash: str = Field(pattern=_SHA256)
    source_workflow_hash: str = Field(pattern=_SHA256)
    source_node_schema_status: Literal["unsealed", "sealed"]
    source_node_schema_seals: tuple[SourceQualificationNodeSchemaSeal, ...] = ()
    p0_qualification_receipt_hash: str = Field(pattern=_SHA256)
    m0_execution_stack_hash: str = Field(pattern=_SHA256)
    m0_profile_hash: str = Field(pattern=_SHA256)
    m0_compiler_hash: str = Field(pattern=_SHA256)
    m0_workflow_hash: str = Field(pattern=_SHA256)
    p0_validation_set_hash: str = Field(pattern=_SHA256)
    p0_policy_hashes: tuple[str, ...] = Field(min_length=1)
    p0_input_hashes: tuple[tuple[str, str], ...] = Field(min_length=1)
    project_content_hash: str = Field(pattern=_SHA256)
    registry_content_hash: str = Field(pattern=_SHA256)
    target_shot_id: Literal["rainy-station-3"]
    target_shot_revision: Literal[1]
    target_shot_content_hash: str = Field(pattern=_SHA256)
    target_asset_role: Literal["approved_endpoint"]
    output_asset_id: Literal["video-shot-rainy-station-3-source-v1"]
    first_frame_asset_id: str = Field(min_length=1)
    first_frame_sha256: str = Field(pattern=_SHA256)
    first_frame_size_bytes: int = Field(strict=True, gt=0)
    first_frame_width: Literal[1659]
    first_frame_height: Literal[948]
    last_frame_asset_id: str = Field(min_length=1)
    last_frame_sha256: str = Field(pattern=_SHA256)
    last_frame_size_bytes: int = Field(strict=True, gt=0)
    last_frame_width: Literal[1659]
    last_frame_height: Literal[948]
    prompt: str = Field(min_length=1)
    prompt_sha256: str = Field(pattern=_SHA256)
    seed_derivation: Literal["source-qualification-closure-sha256-low63-v1"]
    sealed_seed: int = Field(strict=True, ge=0, le=_MAX_SEED)
    width: Literal[1344]
    height: Literal[768]
    frame_count: Literal[124]
    fps: Literal[24]
    native_audio: Literal[True]
    output_container: Literal["mp4"]
    output_contract_hash: str = Field(pattern=_SHA256)
    remote_provider_enabled: Literal[False]
    cloud_fallback_enabled: Literal[False]
    retry_enabled: Literal[False]
    profile_content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seals(self) -> "ShotContinuitySourceQualificationProfile":
        sealed_names = tuple(item.node_name for item in self.source_node_schema_seals)
        if self.source_node_schema_status == "unsealed":
            if sealed_names:
                raise ValueError("unsealed source profile cannot carry schema seals")
        elif sealed_names != SOURCE_REQUIRED_NODES:
            raise ValueError("source node schema seals must cover the workflow exactly")
        if hashlib.sha256(self.prompt.encode("utf-8")).hexdigest() != self.prompt_sha256:
            raise ValueError("source qualification prompt hash does not match")
        if self.sealed_seed != derive_source_qualification_seed(
            self.model_dump(mode="python")
        ):
            raise ValueError("source qualification sealed seed does not match")
        expected_output = canonical_sha256(
            {
                "width": self.width,
                "height": self.height,
                "frame_count": self.frame_count,
                "fps": self.fps,
                "container": self.output_container,
                "native_audio": self.native_audio,
            }
        )
        if self.output_contract_hash != expected_output:
            raise ValueError("source qualification output contract hash does not match")
        expected_profile = canonical_sha256(
            self.model_dump(mode="json", exclude={"profile_content_hash"})
        )
        if self.profile_content_hash != expected_profile:
            raise ValueError("source qualification profile hash does not match")
        return self

    @classmethod
    def create(cls, **values: object) -> "ShotContinuitySourceQualificationProfile":
        data = dict(values)
        data["source_node_schema_seals"] = tuple(
            item
            if isinstance(item, SourceQualificationNodeSchemaSeal)
            else SourceQualificationNodeSchemaSeal.model_validate(item)
            for item in data.get("source_node_schema_seals", ())
        )
        data["prompt_sha256"] = hashlib.sha256(
            str(data["prompt"]).encode("utf-8")
        ).hexdigest()
        data["output_contract_hash"] = canonical_sha256(
            {
                "width": data["width"],
                "height": data["height"],
                "frame_count": data["frame_count"],
                "fps": data["fps"],
                "container": data["output_container"],
                "native_audio": data["native_audio"],
            }
        )
        data["sealed_seed"] = derive_source_qualification_seed(data)
        provisional = cls.model_construct(**data, profile_content_hash="0" * 64)
        data["profile_content_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"profile_content_hash"})
        )
        return cls.model_validate(data)


def load_source_qualification_profile(
    path: str | Path,
    *,
    artifact_root: str | Path,
) -> tuple[ShotContinuitySourceQualificationProfile, str]:
    root = Path(artifact_root).resolve(strict=True)
    requested = Path(path)
    if not requested.is_absolute():
        requested = root / requested
    try:
        snapshot = _read_regular_file_nofollow(
            requested.resolve(strict=True),
            contained_by=root,
        )
        profile = ShotContinuitySourceQualificationProfile.model_validate_json(
            snapshot.data
        )
    except (OSError, ValueError) as exc:
        raise _invalid("Source qualification profile is invalid.", str(exc)) from exc
    return profile, snapshot.file_sha256


def _validate_p0(
    profile: ShotContinuitySourceQualificationProfile,
    snapshot: M0ValidationPreflightSnapshot,
) -> None:
    if (
        snapshot.qualification_receipt_hash
        != profile.p0_qualification_receipt_hash
        or snapshot.execution_stack_hash != profile.m0_execution_stack_hash
        or snapshot.source_execution_stack_hash
        != profile.source_execution_stack_hash
        or snapshot.profile_hash != profile.m0_profile_hash
        or snapshot.compiler_hash != profile.m0_compiler_hash
        or snapshot.workflow_hash != profile.m0_workflow_hash
        or snapshot.validation_set_hash != profile.p0_validation_set_hash
        or snapshot.policy_hashes != profile.p0_policy_hashes
        or snapshot.qualification_input_hashes != profile.p0_input_hashes
    ):
        raise _invalid("Source qualification P0 closure does not match.")


def _validate_request(
    request: ResolvedVideoGenerationRequest | Any,
    profile: ShotContinuitySourceQualificationProfile,
    sources: ShotContinuitySourceExecutionSources,
) -> None:
    try:
        images = tuple(request.image_bindings)
        scope_request = request.activation_scope.request
        if (
            request.provider_name != profile.provider_name
            or request.provider_kind != profile.provider_kind
            or request.model_id != profile.model_id
            or request.capability_id != profile.capability_id
            or request.provider_profile.profile_id != profile.candidate_id
            or request.provider_profile.profile_version
            != f"v{profile.contract_version}"
            or request.provider_profile.profile_sha256
            != profile.provider_profile_sha256
            or request.adapter_compiler_id != profile.adapter_compiler_id
            or request.adapter_compiler_version != profile.adapter_compiler_version
            or request.adapter_compiler_hash != profile.source_compiler_hash
            or request.execution_stack_hash
            != profile.source_execution_stack_hash
            or sources.materialized_stack.execution_stack_hash
            != request.execution_stack_hash
        ):
            raise _invalid("Source qualification request identity does not match.")
        if (
            _value(request.execution_kind) != "local"
            or _value(request.billing_kind) != "local_unmetered"
            or _value(request.mode) != "image_to_video"
            or request.c4_multi_anchor_binding is not None
            or request.continuity_binding is not None
            or request.hard_cut_keyframe_binding is not None
            or request.media_bindings
            or request.seal_terminal_frame is not True
        ):
            raise _invalid("Source qualification request mode is not exact.")
        if tuple(item.role for item in images) != ("first_frame", "last_frame"):
            raise _invalid("Source qualification requires exact two-frame cardinality.")
        expected_images = (
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
        if tuple(
            (
                item.asset_id,
                item.asset_sha256,
                item.size_bytes,
                item.width,
                item.height,
            )
            for item in images
        ) != expected_images or any(item.mime_type != "image/png" for item in images):
            raise _invalid("Source qualification frame lineage is not exact.")
        if (
            isinstance(request.effective_seed, bool)
            or not isinstance(request.effective_seed, int)
            or request.effective_seed < 0
            or request.effective_seed != profile.sealed_seed
        ):
            raise _invalid("Source qualification requires the sealed seed.")
        if (
            request.prompt_text != profile.prompt
            or hashlib.sha256(request.prompt_text.encode("utf-8")).hexdigest()
            != profile.prompt_sha256
            or request.effective_negative_prompt_text
        ):
            raise _invalid("Source qualification prompt does not match.")
        output = request.effective_output
        if (
            getattr(output, "timing_mode", None) != "frame_count"
            or getattr(output, "frame_count", None) != profile.frame_count
            or getattr(output, "duration_seconds", None) is not None
            or getattr(output, "dimension_mode", None) != "exact"
            or output.width != profile.width
            or output.height != profile.height
            or output.fps != profile.fps
            or output.container != profile.output_container
            or output.mime_type != "video/mp4"
            or output.native_audio is not profile.native_audio
        ):
            raise _invalid("Source qualification output contract does not match.")
        if (
            scope_request.target_shot_id != profile.target_shot_id
            or scope_request.target_shot_revision != profile.target_shot_revision
            or scope_request.target_shot_content_hash
            != profile.target_shot_content_hash
            or request.output_asset_id != profile.output_asset_id
            or scope_request.target_asset_role != profile.target_asset_role
            or tuple(scope_request.input_artifact_ids)
            != (profile.first_frame_asset_id, profile.last_frame_asset_id)
            or scope_request.base_project.content_hash
            != profile.project_content_hash
            or scope_request.base_registry.content_hash
            != profile.registry_content_hash
            or scope_request.base_dependency_graph is None
        ):
            raise _invalid("Source qualification project lineage is not exact.")
    except AttributeError as exc:
        raise _invalid("Source qualification request is incomplete.", str(exc)) from exc


def _hash_component(path: Path, *, root: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    with _open_regular_file_nofollow(path, contained_by=root) as (descriptor, opened):
        while chunk := os.read(descriptor, 8 * 1024 * 1024):
            digest.update(chunk)
        final = os.fstat(descriptor)
        if final.st_size != opened.st_size:
            raise ValueError("component changed while it was hashed")
    return digest.hexdigest(), final.st_size


def _reopen_input(
    *,
    root: Path,
    path: Path,
    expected_sha256: str,
    expected_size: int,
) -> SourceQualificationInput:
    try:
        snapshot = _read_regular_file_nofollow(path, contained_by=root)
    except (OSError, ValueError) as exc:
        raise _invalid("Source qualification frame could not be reopened.", str(exc)) from exc
    if (
        snapshot.file_sha256 != expected_sha256
        or snapshot.size_bytes != expected_size
        or not snapshot.data.startswith(b"\x89PNG\r\n\x1a\n")
    ):
        raise _invalid("Source qualification frame bytes do not match.")
    return SourceQualificationInput(
        file_name=path.name,
        data=snapshot.data,
        file_sha256=snapshot.file_sha256,
        size_bytes=snapshot.size_bytes,
    )


def _reopen_project_inputs(
    *,
    project_loader: Callable[[], Any],
    request: ResolvedVideoGenerationRequest | Any,
    profile: ShotContinuitySourceQualificationProfile,
) -> tuple[str, tuple[SourceQualificationInput, SourceQualificationInput]]:
    """Reject inactive bases before any runtime inspection or large model hash."""

    try:
        project = project_loader()
        manifest = project.manifest
        graph = manifest.active_dependency_graph
        if (
            graph is None
            or project.dependency_graph is None
            or project.dependency_graph.content_hash != graph.content_hash
            or manifest.active_project.content_hash != profile.project_content_hash
            or manifest.active_registry.content_hash != profile.registry_content_hash
            or project.project.content_hash != profile.project_content_hash
            or project.registry.content_hash != profile.registry_content_hash
            or request.activation_scope.request.base_dependency_graph.content_hash
            != graph.content_hash
        ):
            raise ValueError("active project base pointers are not exact")
        shot = next(
            item for item in project.shots if item.shot_id == profile.target_shot_id
        )
        if (
            shot.revision != profile.target_shot_revision
            or shot.content_hash != profile.target_shot_content_hash
        ):
            raise ValueError("target Shot identity changed")
        registry = {item.asset_id: item for item in project.registry.assets}
        first_record = registry[profile.first_frame_asset_id]
        last_record = registry[profile.last_frame_asset_id]
        expected_records = (
            (
                first_record,
                profile.first_frame_sha256,
                profile.first_frame_size_bytes,
                profile.first_frame_width,
                profile.first_frame_height,
            ),
            (
                last_record,
                profile.last_frame_sha256,
                profile.last_frame_size_bytes,
                profile.last_frame_width,
                profile.last_frame_height,
            ),
        )
        if any(
            record.sha256 != digest
            or record.size_bytes != size
            or record.width != width
            or record.height != height
            or record.mime_type != "image/png"
            for record, digest, size, width, height in expected_records
        ):
            raise ValueError("frame Registry lineage changed")
        inputs = (
            _reopen_input(
                root=project.root,
                path=project.asset_paths[profile.first_frame_asset_id],
                expected_sha256=profile.first_frame_sha256,
                expected_size=profile.first_frame_size_bytes,
            ),
            _reopen_input(
                root=project.root,
                path=project.asset_paths[profile.last_frame_asset_id],
                expected_sha256=profile.last_frame_sha256,
                expected_size=profile.last_frame_size_bytes,
            ),
        )
    except (KeyError, OSError, StopIteration, ValueError) as exc:
        raise _invalid(
            "Source qualification active project lineage is not exact.", str(exc)
        ) from exc
    return graph.content_hash, inputs


class ShotContinuitySourceQualificationProvider:
    """One local source attempt; deliberately absent from active provider families."""

    def __init__(
        self,
        *,
        committer: Any,
        qualification_profile_path: str | Path,
        m0_profile_path: str | Path,
        artifact_root: str | Path,
        project_root: str | Path,
        comfy_root: str | Path,
        transport: SourceQualificationTransport,
        project_loader: Callable[[], Any],
        commit_resolver: Callable[[], str],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._committer = committer
        self._qualification_profile_path = qualification_profile_path
        self._m0_profile_path = m0_profile_path
        self._artifact_root = Path(artifact_root).resolve(strict=True)
        self._project_root = Path(project_root).resolve(strict=True)
        self._comfy_root = Path(comfy_root).resolve(strict=True)
        self._transport = transport
        self._project_loader = project_loader
        self._commit_resolver = commit_resolver
        self._clock = clock or (lambda: datetime.now(UTC))

    def _profile(self) -> tuple[ShotContinuitySourceQualificationProfile, str]:
        return load_source_qualification_profile(
            self._qualification_profile_path,
            artifact_root=self._artifact_root,
        )

    def validate_pre_effect(
        self,
        request: ResolvedVideoGenerationRequest | Any,
    ) -> SourceQualificationPreflightSnapshot:
        profile, profile_document_hash = self._profile()
        p0 = reopen_m0_validation_preflight(
            committer=self._committer,
            profile_path=self._m0_profile_path,
            artifact_root=self._artifact_root,
        )
        _validate_p0(profile, p0)
        source_stacks = self._committer.reopen_p0_qualification_source_stacks(
            require_materialized=True
        )
        if len(source_stacks) != 1:
            raise _invalid("Source qualification requires one materialized source stack.")
        sources = reopen_materialized_shot_continuity_source_execution_sources(
            project_root=self._project_root,
            stack=source_stacks[0],
        )
        if (
            sources.materialized_stack.execution_stack_hash
            != profile.source_execution_stack_hash
            or sources.materialization.profile_hash != profile.source_profile_hash
            or sources.materialization.compiler_hash != profile.source_compiler_hash
            or sources.materialization.workflow_hash != profile.source_workflow_hash
        ):
            raise _invalid("Source qualification execution stack does not match.")
        _validate_request(request, profile, sources)
        if profile.source_node_schema_status != "sealed":
            raise _invalid(
                "Source qualification node schemas are not sealed; submit is blocked."
            )
        try:
            transport_endpoint = validate_loopback_endpoint(
                self._transport.base_url
            )
        except (AiVideoError, AttributeError) as exc:
            raise _invalid(
                "Source qualification transport is not bound to loopback.",
                str(exc),
            ) from exc
        if (
            self._transport.deployment_identity != profile.deployment_identity
            or transport_endpoint != profile.loopback_endpoint
        ):
            raise _invalid("Source qualification deployment identity does not match.")
        if self._commit_resolver() != sources.profile.comfyui_commit:
            raise _invalid("Source qualification ComfyUI commit does not match.")

        dependency_graph_hash, inputs = _reopen_project_inputs(
            project_loader=self._project_loader,
            request=request,
            profile=profile,
        )

        object_info = self._transport.get_object_info()
        source_seals = source_node_schema_seals(object_info)
        if source_seals != profile.source_node_schema_seals:
            raise _invalid("Source qualification live node schemas changed.")
        m0_sources = load_m0_qualification_execution_sources(
            profile_path=self._m0_profile_path,
            artifact_root=self._artifact_root,
        )
        validate_m0_live_node_schemas(object_info, m0_sources)
        missing_inputs = _missing_required_node_inputs(sources.workflow, object_info)
        if missing_inputs:
            raise _invalid(
                "Source qualification live node inputs changed.",
                ", ".join(sorted(missing_inputs)),
            )

        component_hashes = []
        for component in sources.profile.components:
            try:
                digest, size = _hash_component(
                    self._comfy_root
                    / _COMPONENT_DIRS[component.role]
                    / component.filename,
                    root=self._comfy_root,
                )
            except (OSError, ValueError) as exc:
                raise _invalid(
                    "Source qualification component could not be reopened.",
                    str(exc),
                ) from exc
            if digest != component.sha256 or size != component.size_bytes:
                raise _invalid("Source qualification component bytes do not match.")
            component_hashes.append((component.role, digest))

        seals = m0_node_schema_seals(object_info)
        return SourceQualificationPreflightSnapshot(
            qualification_profile_hash=profile_document_hash,
            sealed_seed=profile.sealed_seed,
            p0=p0,
            source_execution_stack_hash=profile.source_execution_stack_hash,
            source_profile_hash=profile.source_profile_hash,
            source_compiler_hash=profile.source_compiler_hash,
            source_workflow_hash=profile.source_workflow_hash,
            project_content_hash=profile.project_content_hash,
            registry_content_hash=profile.registry_content_hash,
            dependency_graph_content_hash=dependency_graph_hash,
            m0_node_schema_hashes=tuple(
                (item.node_name, item.schema_sha256) for item in seals
            ),
            source_node_schema_hashes=tuple(
                (item.node_name, item.schema_sha256) for item in source_seals
            ),
            component_hashes=tuple(component_hashes),
            inputs=inputs,
        )

    def preview(
        self, request: ResolvedVideoGenerationRequest | Any
    ) -> VideoGenerationPreview:
        profile, _ = self._profile()
        source_stacks = self._committer.reopen_p0_qualification_source_stacks(
            require_materialized=True
        )
        if len(source_stacks) != 1:
            raise _invalid("Source qualification source stack is not exact.")
        sources = reopen_materialized_shot_continuity_source_execution_sources(
            project_root=self._project_root,
            stack=source_stacks[0],
        )
        _validate_request(request, profile, sources)
        return VideoGenerationPreview.create(
            resolved=request,
            estimated_cost_upper_bound_microunits=None,
            currency=None,
            destination=None,
            egress_item_ids=(),
        )

    def preflight(self, request: ResolvedVideoGenerationRequest | Any) -> None:
        self.validate_pre_effect(request)

    def submit_local(
        self,
        request: ResolvedVideoGenerationRequest | Any,
        preview: VideoGenerationPreview,
        intent: LocalVideoSubmitIntent,
        permit: DurableLocalVideoSubmitPermit,
    ) -> LocalVideoSubmitResult:
        snapshot = self.validate_pre_effect(request)
        if preview != self.preview(request) or (
            intent.request_fingerprint != request.resolved_generation_hash
            or intent.preview_fingerprint != preview.preview_fingerprint
        ):
            raise _invalid("Source qualification preview or intent is invalid.")
        if not permit._consume_local_video_submit_permit(
            intent_fingerprint=intent.intent_fingerprint,
            request_fingerprint=request.resolved_generation_hash,
        ):
            raise _invalid("Source qualification requires one fresh local permit.")
        try:
            uploaded = tuple(
                self._transport.upload_input(item) for item in snapshot.inputs
            )
            source_stack = self._committer.reopen_p0_qualification_source_stacks(
                require_materialized=True
            )[0]
            sources = reopen_materialized_shot_continuity_source_execution_sources(
                project_root=self._project_root,
                stack=source_stack,
            )
            workflow = render_h3_workflow(
                template=sources.workflow,
                binding=sources.binding,
                request=request,
                first_frame_name=uploaded[0],
                last_frame_name=uploaded[1],
                output_prefix=(
                    "video/shot_continuity_source_"
                    f"{request.resolved_generation_hash[:16]}"
                ),
                steps=sources.profile.steps,
                sampler=sources.profile.sampler,
            )
            prompt_id = self._transport.submit_prompt(workflow)
            return LocalVideoSubmitResult.create(
                resolved=request,
                provider_request_id=prompt_id,
                submitted_at=self._clock(),
            )
        except Exception as exc:
            raise AiVideoError(
                code=ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                user_message=(
                    "Source qualification effect outcome is unknown; do not retry "
                    "or fall back."
                ),
                technical_detail=f"{type(exc).__name__}: effect failed",
                retryable=False,
                cause=exc,
            ) from exc


class ShotContinuitySourceQualificationCaller:
    """Reopen the whole closure, persist one request, and submit at most once."""

    def __init__(
        self,
        *,
        committer: Any,
        provider: ShotContinuitySourceQualificationProvider,
    ) -> None:
        self._committer = committer
        self._provider = provider

    def qualify(
        self,
        *,
        attempt_id: str,
        resolved_request: ResolvedVideoGenerationRequest | Any,
    ) -> ShotContinuitySourceQualificationOutcome:
        initial = self._provider.validate_pre_effect(resolved_request)
        expected_hash = resolved_request.resolved_generation_hash
        service = VideoGenerationService(
            committer=self._committer,
            provider=self._provider,
        )
        service.start(attempt_id=attempt_id, request=resolved_request)

        def exact_guard(current: ResolvedVideoGenerationRequest) -> None:
            if current.resolved_generation_hash != expected_hash:
                raise _invalid("Source qualification durable request changed.")
            if self._provider.validate_pre_effect(current) != initial:
                raise _invalid("Source qualification closure drifted before submit.")

        submission = service.submit_local_once(
            attempt_id=attempt_id,
            pre_submit_guard=exact_guard,
        )
        return ShotContinuitySourceQualificationOutcome(
            attempt_id=attempt_id,
            provider_request_id=submission.provider_request_id,
            source_execution_stack_hash=initial.source_execution_stack_hash,
            sealed_seed=initial.sealed_seed,
        )


__all__ = [
    "ShotContinuitySourceQualificationCaller",
    "ShotContinuitySourceQualificationOutcome",
    "ShotContinuitySourceQualificationProfile",
    "ShotContinuitySourceQualificationProvider",
    "SourceQualificationInput",
    "SourceQualificationNodeSchemaSeal",
    "SourceQualificationPreflightSnapshot",
    "SourceQualificationTransport",
    "derive_source_qualification_seed",
    "load_source_qualification_profile",
]
