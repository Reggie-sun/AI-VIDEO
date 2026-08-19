"""Provider-neutral hard-cut continuity contracts and lineage validation."""

from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING, Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    AssetSourceKind,
    AssetType,
    LoadedProductionProject,
    RegistrySnapshotPointer,
    StrictModel,
)


if TYPE_CHECKING:
    from ai_video.production.video import VideoGenerationRequest


_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"


class _ContinuityStrictModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class ContinuityArtifactIdentity(_ContinuityStrictModel):
    artifact_id: str = Field(pattern=_SAFE_ID)
    revision: int = Field(strict=True, ge=1)
    content_hash: str = Field(pattern=_SHA256)


class ContinuityConstraintSet(_ContinuityStrictModel):
    scene_identity: ContinuityArtifactIdentity
    character_identities: tuple[ContinuityArtifactIdentity, ...] = Field(
        min_length=1
    )
    camera_axis: str = Field(min_length=1)
    framing: str = Field(min_length=1)
    lighting: str = Field(min_length=1)
    color: str = Field(min_length=1)
    motion_direction: str = Field(min_length=1)
    exit_state: str = Field(min_length=1)
    entrance_state: str = Field(min_length=1)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "ContinuityConstraintSet":
        identities = tuple(
            (item.artifact_id, item.revision, item.content_hash)
            for item in self.character_identities
        )
        if identities != tuple(sorted(identities)) or len(identities) != len(
            set(identities)
        ):
            raise ValueError("continuity character identities must be unique and ordered")
        text_values = (
            self.camera_axis,
            self.framing,
            self.lighting,
            self.color,
            self.motion_direction,
            self.exit_state,
            self.entrance_state,
        )
        if any(unicodedata.normalize("NFC", value) != value for value in text_values):
            raise ValueError("continuity constraint text must use Unicode NFC normalization")
        expected = canonical_sha256(
            {
                "schema": "ai-video-continuity-constraints/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        )
        if self.content_hash != expected:
            raise ValueError("continuity constraint hash does not match content")
        return self

    @classmethod
    def create(cls, **values: object) -> "ContinuityConstraintSet":
        data = dict(values)
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            {
                "schema": "ai-video-continuity-constraints/1",
                **candidate.model_dump(
                    mode="json", exclude={"content_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


class TerminalFrameEvidence(_ContinuityStrictModel):
    source_shot_id: str = Field(pattern=_SAFE_ID)
    source_shot_revision: int = Field(strict=True, ge=1)
    source_shot_content_hash: str = Field(pattern=_SHA256)
    source_video_asset_id: str = Field(pattern=_SAFE_ID)
    source_video_sha256: str = Field(pattern=_SHA256)
    source_generation_id: str = Field(pattern=_SAFE_ID)
    source_request_input_hash: str = Field(pattern=_SHA256)
    source_resolved_generation_hash: str = Field(pattern=_SHA256)
    source_provenance_receipt_id: str = Field(pattern=_SAFE_ID)
    extraction_receipt_id: str = Field(pattern=_SHA256)
    source_registry: RegistrySnapshotPointer
    source_container_name: Literal["mp4"]
    source_codec_name: str = Field(min_length=1)
    source_width: int = Field(strict=True, gt=0)
    source_height: int = Field(strict=True, gt=0)
    source_fps_numerator: int = Field(strict=True, gt=0)
    source_fps_denominator: int = Field(strict=True, gt=0)
    source_duration_milliseconds: int = Field(strict=True, gt=0)
    source_frame_count: int = Field(strict=True, gt=0)
    frame_index: int = Field(strict=True, ge=0)
    timestamp_numerator: int = Field(strict=True, ge=0)
    timestamp_denominator: int = Field(strict=True, gt=0)
    selection_rule: Literal["generated_candidate_terminal", "resolved_trim_out"]
    extraction_contract_version: str = Field(pattern=_SAFE_ID)
    extractor_name: str = Field(pattern=_SAFE_ID)
    extractor_version: str = Field(pattern=_SAFE_ID)
    extracted_asset_id: str = Field(pattern=_SAFE_ID)
    extracted_sha256: str = Field(pattern=_SHA256)
    extracted_mime_type: Literal["image/png"]
    extracted_size_bytes: int = Field(strict=True, gt=0)
    extracted_width: int = Field(strict=True, gt=0)
    extracted_height: int = Field(strict=True, gt=0)
    extracted_color_space: str = Field(pattern=_SAFE_ID)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "TerminalFrameEvidence":
        if self.frame_index >= self.source_frame_count:
            raise ValueError("terminal frame index is outside source video")
        if (
            self.selection_rule == "generated_candidate_terminal"
            and self.frame_index != self.source_frame_count - 1
        ):
            raise ValueError("generated candidate terminal frame must be the last frame")
        if (
            self.timestamp_numerator * 1000
            >= self.source_duration_milliseconds * self.timestamp_denominator
        ):
            raise ValueError("terminal frame timestamp is outside source duration")
        expected = canonical_sha256(
            {
                "schema": "ai-video-terminal-frame-evidence/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        )
        if self.content_hash != expected:
            raise ValueError("terminal frame evidence hash does not match content")
        return self

    @classmethod
    def create(cls, **values: object) -> "TerminalFrameEvidence":
        data = dict(values)
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            {
                "schema": "ai-video-terminal-frame-evidence/1",
                **candidate.model_dump(
                    mode="json", exclude={"content_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


def validate_terminal_frame_evidence_against_project(
    terminal: TerminalFrameEvidence,
    project: LoadedProductionProject,
) -> None:
    assets = {item.asset_id: item for item in project.registry.assets}
    shots = {item.shot_id: item for item in project.shots}
    source_video = assets.get(terminal.source_video_asset_id)
    terminal_asset = assets.get(terminal.extracted_asset_id)
    source_shot = shots.get(terminal.source_shot_id)
    metadata = source_video.video_metadata if source_video is not None else None
    matching_attempts = []
    for attempt in project.manifest.attempts:
        if attempt.operation != "video_generation":
            continue
        state = attempt.video_generation_state
        if (
            attempt.status.value == "succeeded"
            and state is not None
            and state.phase.value == "activate"
            and state.terminal_frame_evidence is not None
            and state.terminal_frame_extraction is not None
            and state.terminal_frame_evidence.content_hash == terminal.content_hash
            and state.terminal_frame_evidence.extracted_asset_id
            == terminal.extracted_asset_id
            and state.terminal_frame_evidence.extracted_sha256
            == terminal.extracted_sha256
            and state.terminal_frame_extraction.content_hash
            == terminal.extraction_receipt_id
            and state.terminal_frame_extraction.extracted_asset_id
            == terminal.extracted_asset_id
            and state.terminal_frame_extraction.extracted_sha256
            == terminal.extracted_sha256
            and state.request.generation_id == terminal.source_generation_id
            and state.request.request_input_hash == terminal.source_request_input_hash
            and state.request.resolved_generation_hash
            == terminal.source_resolved_generation_hash
            and state.candidate_video_asset_ids == (terminal.source_video_asset_id,)
            and state.candidate_continuity_asset_ids
            == (terminal.extracted_asset_id,)
            and attempt.candidate_registry == terminal.source_registry
        ):
            matching_attempts.append(attempt)
    if (
        len(matching_attempts) != 1
        or source_shot is None
        or not any(
            terminal.source_video_asset_id in role.asset_ids
            for role in source_shot.required_asset_roles
        )
        or source_video is None
        or source_video.asset_type is not AssetType.VIDEO
        or source_video.source_kind is not AssetSourceKind.GENERATED
        or source_video.sha256 != terminal.source_video_sha256
        or source_video.input_fingerprint != terminal.source_resolved_generation_hash
        or source_video.creation_receipt_id != terminal.source_provenance_receipt_id
        or metadata is None
        or metadata.container_name != terminal.source_container_name
        or metadata.codec_name != terminal.source_codec_name
        or metadata.width != terminal.source_width
        or metadata.height != terminal.source_height
        or metadata.fps_numerator != terminal.source_fps_numerator
        or metadata.fps_denominator != terminal.source_fps_denominator
        or metadata.duration_milliseconds != terminal.source_duration_milliseconds
        or metadata.frame_count != terminal.source_frame_count
        or terminal_asset is None
        or terminal_asset.asset_type is not AssetType.IMAGE
        or terminal_asset.source_kind is not AssetSourceKind.DERIVED
        or terminal_asset.sha256 != terminal.extracted_sha256
        or terminal_asset.size_bytes != terminal.extracted_size_bytes
        or terminal_asset.mime_type != terminal.extracted_mime_type
        or terminal_asset.width != terminal.extracted_width
        or terminal_asset.height != terminal.extracted_height
        or terminal_asset.input_artifact_ids != (terminal.source_video_asset_id,)
        or terminal_asset.input_fingerprint != terminal.extraction_receipt_id
        or terminal_asset.creation_receipt_id != terminal.extraction_receipt_id
    ):
        raise ValueError(
            "terminal frame evidence does not match an exact succeeded source activation"
        )


class ContinuityReferenceBinding(_ContinuityStrictModel):
    role: Literal["first_frame"]
    terminal_frame: TerminalFrameEvidence
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    constraints: ContinuityConstraintSet
    binding_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "ContinuityReferenceBinding":
        expected = canonical_sha256(
            {
                "schema": "ai-video-continuity-reference-binding/1",
                **self.model_dump(mode="json", exclude={"binding_hash"}),
            }
        )
        if self.binding_hash != expected:
            raise ValueError("continuity binding hash does not match content")
        return self

    @classmethod
    def create(cls, **values: object) -> "ContinuityReferenceBinding":
        data = dict(values)
        candidate = cls.model_construct(**data, binding_hash="0" * 64)
        data["binding_hash"] = canonical_sha256(
            {
                "schema": "ai-video-continuity-reference-binding/1",
                **candidate.model_dump(
                    mode="json", exclude={"binding_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


class HardCutKeyframeBinding(_ContinuityStrictModel):
    role: Literal["hard_cut_keyframe"]
    terminal_frame: TerminalFrameEvidence
    keyframe_asset_id: str = Field(pattern=_SAFE_ID)
    keyframe_asset_sha256: str = Field(pattern=_SHA256)
    keyframe_mime_type: Literal["image/png"]
    keyframe_width: int = Field(strict=True, gt=0)
    keyframe_height: int = Field(strict=True, gt=0)
    keyframe_size_bytes: int = Field(strict=True, gt=0)
    keyframe_request_fingerprint: str = Field(pattern=_SHA256)
    keyframe_provenance_receipt_id: str = Field(pattern=_SAFE_ID)
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    constraints: ContinuityConstraintSet
    binding_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "HardCutKeyframeBinding":
        if (
            self.keyframe_asset_id == self.terminal_frame.extracted_asset_id
            or self.keyframe_asset_sha256 == self.terminal_frame.extracted_sha256
        ):
            raise ValueError(
                "hard-cut keyframe identity and bytes must be distinct from the terminal frame"
            )
        if self.target_shot_id == self.terminal_frame.source_shot_id:
            raise ValueError("hard-cut keyframe must target a downstream Shot")
        expected = canonical_sha256(
            {
                "schema": "ai-video-hard-cut-keyframe-binding/1",
                **self.model_dump(mode="json", exclude={"binding_hash"}),
            }
        )
        if self.binding_hash != expected:
            raise ValueError("hard-cut keyframe binding hash does not match content")
        return self

    @classmethod
    def create(cls, **values: object) -> "HardCutKeyframeBinding":
        data = dict(values)
        candidate = cls.model_construct(**data, binding_hash="0" * 64)
        data["binding_hash"] = canonical_sha256(
            {
                "schema": "ai-video-hard-cut-keyframe-binding/1",
                **candidate.model_dump(
                    mode="json", exclude={"binding_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


def validate_hard_cut_keyframe_binding_against_project(
    request: VideoGenerationRequest,
    project: LoadedProductionProject,
    *,
    require_active_base: bool = True,
) -> None:
    binding = request.hard_cut_keyframe_binding
    if binding is None:
        return
    terminal = binding.terminal_frame
    validate_terminal_frame_evidence_against_project(terminal, project)
    assets = {item.asset_id: item for item in project.registry.assets}
    shots = {item.shot_id: item for item in project.shots}
    scenes = {item.artifact_id: item for item in project.scenes}
    characters = {item.artifact_id: item for item in project.characters}
    keyframe = assets.get(binding.keyframe_asset_id)
    target_shot = shots.get(binding.target_shot_id)
    scene_identity = binding.constraints.scene_identity
    scene = scenes.get(scene_identity.artifact_id)
    image_attempts = tuple(
        attempt
        for attempt in project.manifest.attempts
        if attempt.operation == "image_generation"
        and attempt.status.value == "succeeded"
        and attempt.image_phase == "activate"
        and attempt.image_request is not None
        and attempt.image_request.request_fingerprint
        == binding.keyframe_request_fingerprint
        and attempt.image_request.output_asset_id == binding.keyframe_asset_id
        and attempt.image_request.target_shot_id == binding.target_shot_id
        and attempt.candidate_image_asset_ids == (binding.keyframe_asset_id,)
        and attempt.candidate_project == request.base_project
        and attempt.candidate_registry == request.base_registry
        and attempt.candidate_dependency_graph == request.base_dependency_graph
    )
    if (
        require_active_base
        and (
            request.base_project != project.manifest.active_project
            or request.base_registry != project.manifest.active_registry
            or request.base_dependency_graph
            != project.manifest.active_dependency_graph
        )
        or keyframe is None
        or keyframe.asset_type is not AssetType.IMAGE
        or keyframe.source_kind is not AssetSourceKind.GENERATED
        or keyframe.sha256 != binding.keyframe_asset_sha256
        or keyframe.size_bytes != binding.keyframe_size_bytes
        or keyframe.mime_type != binding.keyframe_mime_type
        or keyframe.width != binding.keyframe_width
        or keyframe.height != binding.keyframe_height
        or keyframe.input_fingerprint != binding.keyframe_request_fingerprint
        or keyframe.creation_receipt_id != binding.keyframe_provenance_receipt_id
        or len(image_attempts) != 1
        or terminal.extracted_asset_id not in keyframe.input_artifact_ids
        or target_shot is None
        or require_active_base
        and (
            target_shot.revision != binding.target_shot_revision
            or target_shot.content_hash != binding.target_shot_content_hash
        )
        or scene is None
        or scene.revision != scene_identity.revision
        or scene.content_hash != scene_identity.content_hash
    ):
        raise ValueError("hard-cut keyframe lineage does not match the active project")
    for identity in binding.constraints.character_identities:
        character = characters.get(identity.artifact_id)
        if (
            character is None
            or character.revision != identity.revision
            or character.content_hash != identity.content_hash
            or identity.artifact_id not in keyframe.input_artifact_ids
        ):
            raise ValueError(
                "hard-cut keyframe character lineage does not match the active project"
            )
