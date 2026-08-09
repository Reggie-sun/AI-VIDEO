from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


class ProductionManifest(StrictModel):
    schema_version: Literal["2.0"] = "2.0"
    project_id: str
    active_project_revision: int = Field(ge=1)
    active_project_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    active_registry_revision: str = Field(pattern=r"^[0-9a-f]{64}$")


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
