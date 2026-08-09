from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
    model_validator,
)


class _ImmutableDict(dict):
    def _reject_mutation(self, *args: object, **kwargs: object) -> None:
        raise TypeError("Production model mappings are immutable.")

    __setitem__ = _reject_mutation
    __delitem__ = _reject_mutation
    clear = _reject_mutation
    pop = _reject_mutation
    popitem = _reject_mutation
    setdefault = _reject_mutation
    update = _reject_mutation
    __ior__ = _reject_mutation


def _immutable_mapping(value: dict) -> _ImmutableDict:
    return _ImmutableDict(value)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _require_clean_relative_file_path(value: Path, label: str) -> Path:
    if value.is_absolute() or ".." in value.parts or value == Path("."):
        raise ValueError(
            f"{label} path must be clean and project-relative file path"
        )
    return value


def canonical_project_snapshot_path(revision: int, content_hash: str) -> Path:
    return Path(f"state/projects/project.{revision}.{content_hash}.yaml")


def canonical_registry_snapshot_path(revision_id: str) -> Path:
    return Path(f"assets/registry.{revision_id}.json")


def require_canonical_project_snapshot_path(
    value: Path,
    revision: int,
    content_hash: str,
    *,
    allow_entrypoint: bool,
) -> Path:
    value = _require_clean_relative_file_path(value, "snapshot")
    if allow_entrypoint and value == Path("project.yaml"):
        return value
    if value != canonical_project_snapshot_path(revision, content_hash):
        raise ValueError("snapshot path must be the canonical project snapshot path")
    return value


def require_canonical_registry_snapshot_path(
    value: Path, revision_id: str
) -> Path:
    value = _require_clean_relative_file_path(value, "snapshot")
    if value != canonical_registry_snapshot_path(revision_id):
        raise ValueError("snapshot path must be the canonical registry snapshot path")
    return value


class SourceReference(StrictModel):
    kind: Literal["user_input", "imported", "derived"]
    reference: str
    content_hash: str | None = None


class VersionedArtifact(StrictModel):
    artifact_id: str = Field(min_length=1)
    schema_version: Literal["2.0"] = "2.0"
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    creation_receipt_id: str = Field(min_length=1)
    source_provenance: tuple[SourceReference, ...] = Field(min_length=1)


class DeliveryProfile(StrictModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps: int = Field(gt=0)
    codec_profile: str = "h264"


class VoiceProfile(StrictModel):
    language: str
    voice_hint: str
    notes: str = ""


class DurationPolicy(StrictModel):
    mode: Literal["fixed", "voice_driven", "content_driven"]
    seconds: float | None = Field(default=None, gt=0)
    minimum_seconds: float | None = Field(default=None, gt=0)
    maximum_seconds: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _validate_bounds(self) -> "DurationPolicy":
        if self.mode == "fixed" and self.seconds is None:
            raise ValueError("fixed duration policy requires seconds")
        if (
            self.minimum_seconds is not None
            and self.maximum_seconds is not None
            and self.minimum_seconds > self.maximum_seconds
        ):
            raise ValueError("minimum_seconds cannot exceed maximum_seconds")
        return self


class CompositionDirective(StrictModel):
    kind: Literal["fit", "position", "crop", "text", "transition_hint"]
    parameters: dict[str, float | int | str | bool] = Field(
        default_factory=_ImmutableDict
    )

    _freeze_parameters = field_validator("parameters")(_immutable_mapping)


class RendererPolicy(StrictModel):
    allowed: tuple[Literal["hyperframes", "remotion"], ...] = ("hyperframes",)
    default_preference: Literal["hyperframes", "remotion"] = "hyperframes"

    @model_validator(mode="after")
    def _default_is_allowed(self) -> "RendererPolicy":
        if self.default_preference not in self.allowed:
            raise ValueError("renderer default_preference must be present in allowed")
        return self


class ArtifactReference(StrictModel):
    artifact_id: str = Field(min_length=1)
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    path: Path


class ProjectArtifactRefs(StrictModel):
    brief: ArtifactReference
    story: ArtifactReference
    characters: tuple[ArtifactReference, ...]
    scenes: tuple[ArtifactReference, ...]
    storyboard: ArtifactReference
    shots: tuple[ArtifactReference, ...]


class ProductionBrief(VersionedArtifact):
    title: str
    objective: str
    audience: str
    format: str
    language: str
    constraints: tuple[str, ...] = ()


class StoryBeat(StrictModel):
    beat_id: str
    summary: str


class Story(VersionedArtifact):
    language: str
    logline: str
    synopsis: str
    beats: tuple[StoryBeat, ...] = Field(min_length=1)
    source_references: tuple[str, ...] = ()


class Character(VersionedArtifact):
    character_id: str
    name: str
    identity: str
    appearance_bible: str
    wardrobe: tuple[str, ...] = ()
    voice_profile: VoiceProfile | None = None
    reference_asset_ids: tuple[str, ...] = ()
    allowed_variations: tuple[str, ...] = ()


class Scene(VersionedArtifact):
    scene_id: str
    location: str
    time: str
    mood: str
    participant_ids: tuple[str, ...] = ()
    continuity_constraints: tuple[str, ...] = ()
    visual_reference_asset_ids: tuple[str, ...] = ()


class StoryboardBeat(StrictModel):
    beat_id: str
    scene_id: str
    shot_ids: tuple[str, ...] = Field(min_length=1)
    narrative_intent: str


class Storyboard(VersionedArtifact):
    beats: tuple[StoryboardBeat, ...] = Field(min_length=1)


class VisualStrategy(str, Enum):
    STATIC_IMAGE = "static_image"
    IMAGE_MOTION = "image_motion"
    MOTION_GRAPHICS = "motion_graphics"
    GENERATED_VIDEO = "generated_video"
    EXISTING_VIDEO = "existing_video"
    HYBRID = "hybrid"


class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    VOICE = "voice"
    MUSIC = "music"
    SFX = "sfx"
    CAPTION = "caption"
    COMPOSITION_SOURCE = "composition_source"
    RENDER = "render"
    REVIEW_EVIDENCE = "review_evidence"


class AssetRoleRequirement(StrictModel):
    role: str
    asset_ids: tuple[str, ...] = Field(min_length=1)
    allowed_asset_types: tuple[AssetType, ...] = Field(min_length=1)


class MotionDirective(StrictModel):
    kind: Literal[
        "pan",
        "zoom",
        "parallax",
        "reveal",
        "layered",
        "animate",
        "particles",
        "transition",
    ]
    parameters: dict[str, float | int | str] = Field(min_length=1)

    @field_validator("parameters", mode="before")
    @classmethod
    def _reject_boolean_parameters(cls, value: object) -> object:
        if isinstance(value, Mapping) and any(
            isinstance(item, bool) for item in value.values()
        ):
            raise ValueError("motion parameters cannot use boolean numeric values")
        return value

    _freeze_parameters = field_validator("parameters")(_immutable_mapping)


class HybridLayer(StrictModel):
    role: str
    asset_role: str
    asset_id: str
    z_index: int


class ReviewPolicy(StrictModel):
    required_checks: tuple[str, ...] = ()


class Shot(VersionedArtifact):
    shot_id: str
    scene_id: str
    storyboard_beat_id: str
    intent: str
    dialogue: str = ""
    narration: str = ""
    duration_policy: DurationPolicy
    character_ids: tuple[str, ...] = ()
    continuity_constraints: tuple[str, ...] = ()
    visual_strategy: VisualStrategy
    required_asset_roles: tuple[AssetRoleRequirement, ...] = ()
    motion_directives: tuple[MotionDirective, ...] = ()
    generated_video_rationale: str | None = None
    hybrid_layers: tuple[HybridLayer, ...] = ()
    composition_directives: tuple[CompositionDirective, ...] = ()
    review_policy: ReviewPolicy = Field(default_factory=ReviewPolicy)


class AssetSourceKind(str, Enum):
    IMPORTED = "imported"
    GENERATED = "generated"
    DERIVED = "derived"


class ToolIdentity(StrictModel):
    name: str
    version: str


class EgressMetadata(StrictModel):
    remote: Literal[False] = False
    destination: None = None
    authorization_receipt_id: None = None


class AssetRecord(StrictModel):
    asset_id: str
    asset_type: AssetType
    artifact_path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    mime_type: str
    duration_seconds: float | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    source_kind: AssetSourceKind
    tool: ToolIdentity
    input_artifact_ids: tuple[str, ...] = ()
    input_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    creation_receipt_id: str
    usage_license: str
    egress: EgressMetadata = Field(default_factory=EgressMetadata)
    cost_receipt_id: str | None = None


class AssetRegistrySnapshot(StrictModel):
    schema_version: Literal["2.0"] = "2.0"
    revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    assets: tuple[AssetRecord, ...]


class ProjectSnapshotPointer(StrictModel):
    path: Path
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("path")
    @classmethod
    def _require_clean_relative_path(cls, value: Path) -> Path:
        return _require_clean_relative_file_path(value, "snapshot")

    @model_validator(mode="after")
    def _path_matches_identity(self) -> "ProjectSnapshotPointer":
        require_canonical_project_snapshot_path(
            self.path,
            self.revision,
            self.content_hash,
            allow_entrypoint=True,
        )
        return self


class RegistrySnapshotPointer(StrictModel):
    path: Path
    revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("path")
    @classmethod
    def _require_clean_relative_path(cls, value: Path) -> Path:
        return _require_clean_relative_file_path(value, "snapshot")

    @model_validator(mode="after")
    def _revision_matches_content_hash(self) -> "RegistrySnapshotPointer":
        if self.revision_id != self.content_hash:
            raise ValueError("registry revision_id must match content_hash")
        require_canonical_registry_snapshot_path(self.path, self.revision_id)
        return self


class RendererKind(str, Enum):
    HYPERFRAMES = "hyperframes"
    REMOTION = "remotion"


class TransitionKind(str, Enum):
    CUT = "cut"
    CROSSFADE = "crossfade"


class FixedTransform(StrictModel):
    translate_x_px: int = 0
    translate_y_px: int = 0
    scale_x_milli: int = Field(default=1000, gt=0)
    scale_y_milli: int = Field(default=1000, gt=0)
    rotation_millidegrees: int = 0


class CompositionLayerSpec(StrictModel):
    layer_id: str = Field(min_length=1)
    shot_id: str = Field(min_length=1)
    asset_role: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    trim_start_frame: int = Field(default=0, ge=0)
    trim_duration_frames: int | None = Field(default=None, gt=0)
    transform: FixedTransform = Field(default_factory=FixedTransform)
    opacity_milli: int = Field(default=1000, ge=0, le=1000)
    z_index: int = 0


class TransitionSpec(StrictModel):
    from_shot_id: str
    to_shot_id: str
    kind: TransitionKind
    duration_frames: int = Field(ge=0)


class CompositionSpec(VersionedArtifact):
    composition_id: str
    shot_ids: tuple[str, ...] = Field(min_length=1)
    layers: tuple[CompositionLayerSpec, ...] = Field(min_length=1)
    transitions: tuple[TransitionSpec, ...] = ()
    delivery_profile: DeliveryProfile
    sample_rate: int = Field(default=48_000, gt=0)
    requested_renderer: RendererKind = RendererKind.HYPERFRAMES


class RendererIdentity(StrictModel):
    kind: RendererKind
    version: str = Field(min_length=1)


class ResolvedVisualSpan(StrictModel):
    layer_id: str
    shot_id: str
    asset_role: str
    asset_id: str
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_mime_type: Literal["image/png", "image/jpeg", "image/webp"]
    materialized_path: Path
    start_frame: int = Field(ge=0)
    duration_frames: int = Field(gt=0)
    start_sample: int = Field(ge=0)
    duration_samples: int = Field(ge=0)
    trim_start_frame: int = Field(ge=0)
    trim_duration_frames: int | None = Field(default=None, gt=0)
    transform: FixedTransform
    opacity_milli: int = Field(ge=0, le=1000)
    z_index: int
    incoming_transition: TransitionSpec | None = None


class ResolvedTimeline(VersionedArtifact):
    timeline_id: str
    composition_spec_id: str
    composition_spec_revision: int = Field(ge=1)
    composition_spec_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    delivery_profile: DeliveryProfile
    sample_rate: int = Field(gt=0)
    renderer: RendererIdentity
    visual_spans: tuple[ResolvedVisualSpan, ...] = Field(min_length=1)
    total_frames: int = Field(gt=0)
    total_samples: int = Field(ge=0)
    composition_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class RendererSelectionReceipt(StrictModel):
    receipt_id: str
    attempt_id: str
    requested_kind: RendererKind
    selected_kinds: tuple[RendererKind, ...] = Field(min_length=1, max_length=1)
    renderer_version: str
    timeline_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    current_project: ProjectSnapshotPointer
    current_registry: RegistrySnapshotPointer

    @model_validator(mode="after")
    def _selected_renderer_matches_request(self) -> "RendererSelectionReceipt":
        if self.selected_kinds != (self.requested_kind,):
            raise ValueError("selected renderer must match the requested renderer")
        return self


class RendererCheckReceipt(StrictModel):
    command: Literal["lint", "check"]
    tool_version: str
    exit_code: int
    stdout_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stderr_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    error_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)


class RendererAssetBinding(StrictModel):
    asset_id: str
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_mime_type: Literal["image/png", "image/jpeg", "image/webp"]
    materialized_path: Path


class RenderSourceFilePointer(StrictModel):
    path: Path
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0)

    @field_validator("path")
    @classmethod
    def _require_clean_relative_path(cls, value: Path) -> Path:
        return _require_clean_relative_file_path(value, "render source")


class RenderSourceBundlePointer(StrictModel):
    root_path: Path
    bundle_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    index: RenderSourceFilePointer
    assets: tuple[RenderSourceFilePointer, ...] = Field(min_length=1)

    @field_validator("root_path")
    @classmethod
    def _require_clean_relative_root(cls, value: Path) -> Path:
        return _require_clean_relative_file_path(value, "render source bundle")

    @model_validator(mode="after")
    def _validate_bundle_paths(self) -> "RenderSourceBundlePointer":
        expected_root = Path(f"state/render/sources/{self.bundle_sha256}")
        if self.root_path != expected_root:
            raise ValueError("render source bundle root path must be canonical")
        if self.index.path != expected_root / "index.html":
            raise ValueError("render source bundle index path must be canonical")
        for asset in self.assets:
            if asset.path.parent != expected_root / "assets":
                raise ValueError("render source bundle asset path must be canonical")
            if asset.path.stem != asset.file_sha256 or asset.path.suffix not in {
                ".png",
                ".jpg",
                ".webp",
            }:
                raise ValueError("render source bundle asset path must match its hash")
        return self


class RendererSourceReceipt(VersionedArtifact):
    attempt_id: str
    renderer: RendererIdentity
    timeline_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_bundle: RenderSourceBundlePointer
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_bindings: tuple[RendererAssetBinding, ...] = Field(min_length=1)
    checks: tuple[RendererCheckReceipt, RendererCheckReceipt]

    @model_validator(mode="after")
    def _validate_source_identity(self) -> "RendererSourceReceipt":
        if self.source_sha256 != self.source_bundle.index.file_sha256:
            raise ValueError("renderer source identity does not match its index")
        if tuple(item.command for item in self.checks) != ("lint", "check"):
            raise ValueError("renderer source checks must contain lint then check")
        if any(item.tool_version != self.renderer.version for item in self.checks):
            raise ValueError("renderer source check identity does not match renderer")
        return self


class MeasuredRenderMetadata(StrictModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps_num: int = Field(gt=0)
    fps_den: int = Field(gt=0)
    duration_frames: int = Field(gt=0)
    codec_name: str


def _require_canonical_render_output_path(value: Path, file_sha256: str) -> Path:
    value = _require_clean_relative_file_path(value, "render output")
    if value != Path(f"state/render/outputs/{file_sha256}.mp4"):
        raise ValueError("render output path must be the canonical durable output path")
    return value


class RenderReceipt(VersionedArtifact):
    attempt_id: str
    renderer: RendererIdentity
    timeline_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_bundle_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_hashes: tuple[str, ...] = Field(min_length=1)
    output_path: Path
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_size_bytes: int = Field(gt=0)
    measured: MeasuredRenderMetadata
    decoded_frame_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("asset_hashes")
    @classmethod
    def _validate_asset_hashes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(
            len(item) != 64 or any(char not in "0123456789abcdef" for char in item)
            for item in value
        ):
            raise ValueError("render asset hashes must be lowercase SHA-256 values")
        return value

    @model_validator(mode="after")
    def _validate_output_path(self) -> "RenderReceipt":
        _require_canonical_render_output_path(self.output_path, self.output_sha256)
        return self


class RenderArtifactPointer(StrictModel):
    path: Path
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "RenderArtifactPointer":
        value = _require_clean_relative_file_path(self.path, "render artifact")
        canonical_paths = {
            Path(f"state/render/timelines/{self.content_hash}.json"),
            Path(f"state/render/source-receipts/{self.content_hash}.json"),
            Path(f"state/render/render-receipts/{self.content_hash}.json"),
        }
        if value not in canonical_paths:
            raise ValueError("render artifact path must be canonical")
        return self


class RenderOutputPointer(StrictModel):
    path: Path
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0)

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "RenderOutputPointer":
        _require_canonical_render_output_path(self.path, self.file_sha256)
        return self


class RenderStateSnapshot(VersionedArtifact):
    attempt_id: str = Field(min_length=1)
    project: ProjectSnapshotPointer
    registry: RegistrySnapshotPointer
    renderer_selection: RendererSelectionReceipt
    renderer: RendererIdentity
    timeline_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_bundle_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_hashes: tuple[str, ...] = Field(min_length=1)
    timeline: RenderArtifactPointer
    source_bundle: RenderSourceBundlePointer
    source_receipt: RenderArtifactPointer
    render_receipt: RenderArtifactPointer
    output: RenderOutputPointer

    @model_validator(mode="after")
    def _validate_embedded_identity(self) -> "RenderStateSnapshot":
        selection = self.renderer_selection
        identities_match = (
            self.attempt_id == selection.attempt_id
            and self.project == selection.current_project
            and self.registry == selection.current_registry
            and self.timeline_fingerprint == selection.timeline_fingerprint
            and self.renderer.kind == selection.selected_kinds[0]
            and self.renderer.version == selection.renderer_version
            and self.source_sha256 == self.source_bundle.index.file_sha256
            and self.source_bundle_sha256 == self.source_bundle.bundle_sha256
            and self.asset_hashes
            == tuple(item.file_sha256 for item in self.source_bundle.assets)
        )
        if not identities_match:
            raise ValueError("render state embedded identity does not match")
        return self


class RenderStateSnapshotPointer(StrictModel):
    path: Path
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "RenderStateSnapshotPointer":
        value = _require_clean_relative_file_path(self.path, "render state")
        if value != Path(f"state/render/states/{self.content_hash}.json"):
            raise ValueError("render state path must be canonical")
        return self


class StateCommitStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    OUTCOME_UNKNOWN = "outcome_unknown"


class StateCommitAttempt(StrictModel):
    attempt_id: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    status: StateCommitStatus
    base_manifest_revision: int = Field(ge=1)
    base_project: ProjectSnapshotPointer
    base_registry: RegistrySnapshotPointer
    candidate_project: ProjectSnapshotPointer | None = None
    candidate_registry: RegistrySnapshotPointer | None = None
    candidate_artifacts_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    base_render_state: RenderStateSnapshotPointer | None = None
    candidate_render_state: RenderStateSnapshotPointer | None = None
    renderer_selection: RendererSelectionReceipt | None = None
    render_phase: (
        Literal["selection", "source", "lint", "check", "render", "verify", "activate"]
        | None
    ) = None
    started_at: str
    finished_at: str | None = None
    error_code: str | None = None
    error_message: str | None = None

    @model_validator(mode="after")
    def _validate_terminal_error(self) -> "StateCommitAttempt":
        if self.candidate_project is not None:
            require_canonical_project_snapshot_path(
                self.candidate_project.path,
                self.candidate_project.revision,
                self.candidate_project.content_hash,
                allow_entrypoint=self.operation == "render_state",
            )
        if self.status is StateCommitStatus.RUNNING and any(
            value is not None
            for value in (self.finished_at, self.error_code, self.error_message)
        ):
            raise ValueError("running state commit attempts cannot contain terminal fields")
        if self.status is StateCommitStatus.SUCCEEDED:
            if self.finished_at is None:
                raise ValueError("succeeded state commit attempts require finished_at")
            if self.error_code is not None or self.error_message is not None:
                raise ValueError("succeeded state commit attempts cannot contain error fields")
        terminal_error = self.status in {
            StateCommitStatus.FAILED,
            StateCommitStatus.INTERRUPTED,
            StateCommitStatus.OUTCOME_UNKNOWN,
        }
        if terminal_error and (not self.error_code or not self.error_message):
            raise ValueError("terminal state commit attempts require typed error fields")
        render_fields = (
            self.base_render_state,
            self.candidate_render_state,
            self.renderer_selection,
            self.render_phase,
        )
        if self.operation != "render_state" and any(
            value is not None for value in render_fields
        ):
            raise ValueError("non-render operations cannot contain render fields")
        if self.operation == "render_state":
            if self.renderer_selection is None:
                raise ValueError("render_state attempts require renderer selection")
            if self.attempt_id != self.renderer_selection.attempt_id:
                raise ValueError("render_state attempt identity does not match selection")
            if (
                self.base_project != self.renderer_selection.current_project
                or self.base_registry != self.renderer_selection.current_registry
            ):
                raise ValueError(
                    "render_state attempt identity does not match selection"
                )
            if self.candidate_project not in (None, self.base_project):
                raise ValueError(
                    "render_state candidate project identity does not match"
                )
            if self.candidate_registry not in (None, self.base_registry):
                raise ValueError(
                    "render_state candidate registry identity does not match"
                )
            candidate_bundle = (
                self.candidate_render_state,
                self.candidate_project,
                self.candidate_registry,
            )
            if any(item is not None for item in candidate_bundle) and not all(
                item is not None for item in candidate_bundle
            ):
                raise ValueError("render_state candidate bundle must be all-or-none")
            if all(item is not None for item in candidate_bundle) and (
                self.render_phase != "activate"
            ):
                raise ValueError("render_state candidate bundle requires activate phase")
        return self

    @model_serializer(mode="wrap")
    def _serialize_without_unused_render_fields(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.operation != "render_state":
            for field in (
                "base_render_state",
                "candidate_render_state",
                "renderer_selection",
                "render_phase",
            ):
                data.pop(field, None)
        return data


class RecoveryDisposition(str, Enum):
    ACTIVE = "active"
    PARTIAL_REMOVED = "partial_removed"
    ORPHAN_PRESERVED = "orphan_preserved"
    INTERRUPTED_RECORDED = "interrupted_recorded"


class RecoveryItem(StrictModel):
    path: Path
    disposition: RecoveryDisposition
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator("path")
    @classmethod
    def _require_clean_relative_path(cls, value: Path) -> Path:
        return _require_clean_relative_file_path(value, "recovery item")


class RecoveryReport(StrictModel):
    manifest_revision_before: int = Field(ge=1)
    manifest_revision_after: int = Field(ge=1)
    items: tuple[RecoveryItem, ...]

    @model_validator(mode="after")
    def _require_non_decreasing_manifest_revision(self) -> "RecoveryReport":
        if self.manifest_revision_after < self.manifest_revision_before:
            raise ValueError("recovery manifest revision cannot decrease")
        return self


class ProductionManifest(StrictModel):
    schema_version: Literal["2.0", "2.1"] = "2.0"
    project_id: str
    manifest_revision: int = Field(ge=1)
    active_project: ProjectSnapshotPointer
    active_registry: RegistrySnapshotPointer
    active_render_state: RenderStateSnapshotPointer | None = None
    attempts: tuple[StateCommitAttempt, ...] = ()

    @model_validator(mode="after")
    def _validate_unique_attempt_ids(self) -> "ProductionManifest":
        attempt_ids = [item.attempt_id for item in self.attempts]
        if len(attempt_ids) != len(set(attempt_ids)):
            raise ValueError("Production Manifest attempt IDs must be unique")
        if self.schema_version == "2.0":
            if self.active_render_state is not None or any(
                item.operation == "render_state" for item in self.attempts
            ):
                raise ValueError("Production Manifest 2.0 cannot contain render state")
        for attempt in self.attempts:
            if (
                attempt.operation == "render_state"
                and attempt.status is StateCommitStatus.RUNNING
                and (
                    attempt.base_project != self.active_project
                    or attempt.base_registry != self.active_registry
                    or attempt.base_render_state != self.active_render_state
                )
            ):
                raise ValueError(
                    "running render_state attempt base must match active identity"
                )
        return self

    @model_serializer(mode="wrap")
    def _serialize_compatible_schema(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.schema_version == "2.0" and self.active_render_state is None:
            data.pop("active_render_state", None)
        return data


class ProductionProject(VersionedArtifact):
    project_id: str
    title: str
    default_language: str
    delivery_profile: DeliveryProfile
    renderer_policy: RendererPolicy
    artifacts: ProjectArtifactRefs
    asset_root: Path = Path("assets/files")


class LoadedProductionProject(StrictModel):
    root: Path
    project: ProductionProject
    manifest: ProductionManifest
    brief: ProductionBrief
    story: Story
    characters: tuple[Character, ...]
    scenes: tuple[Scene, ...]
    storyboard: Storyboard
    shots: tuple[Shot, ...]
    registry: AssetRegistrySnapshot
    asset_paths: dict[str, Path]

    _freeze_asset_paths = field_validator("asset_paths")(_immutable_mapping)
