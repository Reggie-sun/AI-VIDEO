from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, Literal, Union
from urllib.parse import urlsplit

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


def _require_canonical_https_origin(value: str, label: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"{label} must be a canonical HTTPS origin") from exc
    host = parsed.hostname
    if host is None:
        raise ValueError(f"{label} must be a canonical HTTPS origin")
    host_token = f"[{host}]" if ":" in host else host
    if port == 443:
        raise ValueError(
            f"{label} must be a canonical HTTPS origin and omit default port 443"
        )
    expected = f"https://{host_token}"
    if port is not None:
        expected = f"{expected}:{port}"
    if not (
        parsed.scheme == "https"
        and parsed.username is None
        and parsed.password is None
        and parsed.path == ""
        and not parsed.query
        and not parsed.fragment
        and value == expected
    ):
        raise ValueError(f"{label} must be a canonical HTTPS origin")
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


class AudioKind(str, Enum):
    DIALOGUE = "dialogue"
    NARRATION = "narration"
    AMBIENCE = "ambience"
    SFX = "sfx"
    BGM = "bgm"


AUDIO_KIND_PRIORITY: Mapping[AudioKind, int] = MappingProxyType(
    {kind: priority for priority, kind in enumerate(AudioKind)}
)


AUDIO_KIND_TO_ASSET_TYPE: Mapping[AudioKind, AssetType] = MappingProxyType(
    {
        AudioKind.DIALOGUE: AssetType.VOICE,
        AudioKind.NARRATION: AssetType.VOICE,
        AudioKind.AMBIENCE: AssetType.SFX,
        AudioKind.SFX: AssetType.SFX,
        AudioKind.BGM: AssetType.MUSIC,
    }
)


class AudioChannelLayout(str, Enum):
    MONO = "mono"
    STEREO = "stereo"


class AudioSource(StrictModel):
    kind: AssetSourceKind
    provider_or_tool: ToolIdentity
    input_artifact_ids: tuple[str, ...] = ()
    input_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    original_reference: str | None = None


class AudioLoudnessMetadata(StrictModel):
    integrated_lufs_milli: int | None = Field(default=None, strict=True)
    true_peak_dbfs_milli: int | None = Field(default=None, strict=True)
    measurement_standard: Literal["ebu_r128"] | None = None

    @model_validator(mode="after")
    def _require_consistent_measurement(self) -> "AudioLoudnessMetadata":
        measured = (
            self.integrated_lufs_milli is not None
            or self.true_peak_dbfs_milli is not None
        )
        if measured != (self.measurement_standard is not None):
            raise ValueError("loudness values and measurement standard must agree")
        return self


class AudioAssetMetadata(StrictModel):
    audio_kind: AudioKind
    source: AudioSource
    speaker_id: str | None = None
    voice_id: str | None = None
    language: str | None = None
    script_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    duration_samples: int = Field(strict=True, gt=0)
    sample_rate_hz: int = Field(strict=True, gt=0)
    channels: int = Field(strict=True, ge=1, le=2)
    channel_layout: AudioChannelLayout
    codec_name: str = Field(min_length=1)
    loudness: AudioLoudnessMetadata
    provenance_receipt_id: str = Field(min_length=1)
    alignment_receipt_id: str | None = None

    @model_validator(mode="after")
    def _validate_audio_identity(self) -> "AudioAssetMetadata":
        if (self.channels, self.channel_layout) not in {
            (1, AudioChannelLayout.MONO),
            (2, AudioChannelLayout.STEREO),
        }:
            raise ValueError("audio channels and channel layout must agree")
        speech = self.audio_kind in {AudioKind.DIALOGUE, AudioKind.NARRATION}
        if speech and (not self.language or self.script_hash is None):
            raise ValueError("speech audio requires language and script_hash")
        if (
            speech
            and self.source.kind is AssetSourceKind.GENERATED
            and not self.voice_id
        ):
            raise ValueError("generated speech audio requires non-empty voice_id")
        if not speech and any(
            value is not None
            for value in (
                self.speaker_id,
                self.voice_id,
                self.language,
                self.script_hash,
                self.alignment_receipt_id,
            )
        ):
            raise ValueError("non-speech audio cannot contain voice identity")
        return self


class CaptionAssetMetadata(StrictModel):
    caption_track_id: str = Field(min_length=1)
    language: str = Field(min_length=1)
    source_audio_asset_id: str = Field(min_length=1)
    source_audio_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    script_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    transcript_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    segment_count: int = Field(strict=True, ge=0)
    word_count: int = Field(strict=True, ge=0)
    segmentation_policy_id: str = Field(min_length=1)
    segmentation_policy_version: str = Field(min_length=1)
    alignment_receipt_id: str = Field(min_length=1)
    timing_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    style_reference_id: str | None = None
    style_content_hash: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )

    @model_validator(mode="after")
    def _validate_style_identity(self) -> "CaptionAssetMetadata":
        if (self.style_reference_id is None) != (self.style_content_hash is None):
            raise ValueError("caption style identity must be all-or-none")
        return self


class EgressMetadata(StrictModel):
    remote: bool = Field(default=False, strict=True)
    destination: str | None = None
    authorization_receipt_id: str | None = None
    request_fingerprint: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    payload_fingerprint: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    retention_mode: Literal["provider_standard", "zero_retention"] | None = None
    provider_policy_snapshot_id: str | None = None

    @model_validator(mode="after")
    def _validate_variant(self) -> "EgressMetadata":
        remote_fields = (
            self.destination,
            self.authorization_receipt_id,
            self.request_fingerprint,
            self.payload_fingerprint,
            self.retention_mode,
            self.provider_policy_snapshot_id,
        )
        if not self.remote:
            if any(value is not None for value in remote_fields):
                raise ValueError("local egress metadata cannot contain remote fields")
            return self
        if any(value is None for value in remote_fields):
            raise ValueError("remote egress metadata requires complete authorization")
        assert self.destination is not None
        _require_canonical_https_origin(self.destination, "remote destination")
        return self

    @model_serializer(mode="wrap")
    def _serialize_compatible_local_variant(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if not self.remote:
            for field in (
                "request_fingerprint",
                "payload_fingerprint",
                "retention_mode",
                "provider_policy_snapshot_id",
            ):
                data.pop(field, None)
        return data


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
    audio_metadata: AudioAssetMetadata | None = None
    caption_metadata: CaptionAssetMetadata | None = None

    @model_validator(mode="after")
    def _validate_p4_metadata(self) -> "AssetRecord":
        audio_types = {AssetType.VOICE, AssetType.MUSIC, AssetType.SFX}
        if self.audio_metadata is not None:
            if self.asset_type not in audio_types:
                raise ValueError("non-audio assets cannot contain audio metadata")
            if AUDIO_KIND_TO_ASSET_TYPE[self.audio_metadata.audio_kind] != self.asset_type:
                raise ValueError("audio kind does not match registry asset type")
            if self.duration_seconds is not None:
                measured_seconds = Decimal(self.audio_metadata.duration_samples) / Decimal(
                    self.audio_metadata.sample_rate_hz
                )
                display_seconds = Decimal(str(self.duration_seconds))
                tolerance = Decimal(1) / Decimal(self.audio_metadata.sample_rate_hz)
                if abs(measured_seconds - display_seconds) > tolerance:
                    raise ValueError("duration_seconds does not match measured samples")
        if self.caption_metadata is not None and self.asset_type is not AssetType.CAPTION:
            raise ValueError("non-caption assets cannot contain caption metadata")
        if self.asset_type is AssetType.CAPTION and self.audio_metadata is not None:
            raise ValueError("caption assets cannot contain audio metadata")
        if self.egress.remote and not (
            self.asset_type is AssetType.VOICE
            and self.source_kind is AssetSourceKind.GENERATED
        ):
            raise ValueError("remote egress is restricted to generated voice assets")
        return self

    @model_serializer(mode="wrap")
    def _serialize_compatible_metadata(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.audio_metadata is None:
            data.pop("audio_metadata", None)
        if self.caption_metadata is None:
            data.pop("caption_metadata", None)
        return data


class AssetRegistrySnapshot(StrictModel):
    schema_version: Literal["2.0", "2.1"] = "2.0"
    revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    assets: tuple[AssetRecord, ...]

    @model_validator(mode="before")
    @classmethod
    def _reject_explicit_p4_fields_in_20(cls, value: object) -> object:
        if not isinstance(value, Mapping) or value.get("schema_version", "2.0") != "2.0":
            return value
        for asset in value.get("assets", ()):
            if isinstance(asset, Mapping) and {
                "audio_metadata",
                "caption_metadata",
            }.intersection(asset):
                raise ValueError(
                    "Asset Registry 2.0 cannot contain explicit P4 fields"
                )
            if isinstance(asset, Mapping):
                egress = asset.get("egress")
                if isinstance(egress, Mapping) and {
                    "request_fingerprint",
                    "payload_fingerprint",
                    "retention_mode",
                    "provider_policy_snapshot_id",
                }.intersection(egress):
                    raise ValueError(
                        "Asset Registry 2.0 cannot contain explicit P4 egress fields"
                    )
        return value

    @model_validator(mode="after")
    def _validate_versioned_metadata(self) -> "AssetRegistrySnapshot":
        if self.schema_version == "2.0":
            if any(
                asset.audio_metadata is not None
                or asset.caption_metadata is not None
                or asset.egress.remote
                for asset in self.assets
            ):
                raise ValueError("Asset Registry 2.0 cannot contain P4 metadata")
            return self
        for asset in self.assets:
            if asset.asset_type in {AssetType.VOICE, AssetType.MUSIC, AssetType.SFX}:
                if asset.audio_metadata is None:
                    raise ValueError("Asset Registry 2.1 audio assets require audio metadata")
            elif asset.audio_metadata is not None:
                raise ValueError("non-audio assets cannot contain audio metadata")
            if asset.asset_type is AssetType.CAPTION:
                if asset.caption_metadata is None:
                    raise ValueError("Asset Registry 2.1 caption assets require caption metadata")
            elif asset.caption_metadata is not None:
                raise ValueError("non-caption assets cannot contain caption metadata")
        return self


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


class DuckingSpec(StrictModel):
    sidechain_track_ids: tuple[str, ...] = Field(min_length=1)
    attenuation_millidb: int = Field(strict=True, lt=0)
    attack_samples: int = Field(strict=True, ge=0)
    release_samples: int = Field(strict=True, ge=0)


class AudioTrackSpec(StrictModel):
    track_id: str = Field(min_length=1)
    audio_kind: AudioKind
    asset_id: str = Field(min_length=1)
    shot_id: str | None = None
    start_sample: int | None = Field(default=None, strict=True, ge=0)
    trim_start_sample: int = Field(default=0, strict=True, ge=0)
    trim_duration_samples: int | None = Field(default=None, strict=True, gt=0)
    gain_millidb: int = Field(default=0, strict=True)
    fade_in_samples: int = Field(default=0, strict=True, ge=0)
    fade_out_samples: int = Field(default=0, strict=True, ge=0)
    ducking: DuckingSpec | None = None

    @model_validator(mode="after")
    def _validate_placement_and_ducking(self) -> "AudioTrackSpec":
        if self.audio_kind in {AudioKind.DIALOGUE, AudioKind.NARRATION} and (
            self.shot_id is None
        ):
            raise ValueError("dialogue and narration tracks require shot_id")
        if self.shot_id is None and self.start_sample is None:
            raise ValueError("global audio tracks require explicit start_sample")
        if self.ducking is not None and self.track_id in self.ducking.sidechain_track_ids:
            raise ValueError("audio track cannot duck itself")
        if (
            self.trim_duration_samples is not None
            and self.fade_in_samples + self.fade_out_samples
            > self.trim_duration_samples
        ):
            raise ValueError("audio fades cannot exceed trimmed duration")
        return self


class CaptionWord(StrictModel):
    text: str = Field(min_length=1)
    start_sample: int = Field(strict=True, ge=0)
    end_sample: int = Field(strict=True, gt=0)
    speaker_id: str | None = None
    confidence_milli: int | None = Field(default=None, strict=True, ge=0, le=1000)

    @field_validator("text")
    @classmethod
    def _require_nfc_text(cls, value: str) -> str:
        if not unicodedata.is_normalized("NFC", value):
            raise ValueError("caption word text must use NFC normalization")
        return value

    @model_validator(mode="after")
    def _validate_bounds(self) -> "CaptionWord":
        if self.end_sample <= self.start_sample:
            raise ValueError("caption word end must follow start")
        return self


class CaptionSegment(StrictModel):
    segment_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    start_sample: int = Field(strict=True, ge=0)
    end_sample: int = Field(strict=True, gt=0)
    speaker_id: str | None = None
    words: tuple[CaptionWord, ...] | None = None
    confidence_milli: int | None = Field(default=None, strict=True, ge=0, le=1000)

    @field_validator("text")
    @classmethod
    def _require_nfc_text(cls, value: str) -> str:
        if not unicodedata.is_normalized("NFC", value):
            raise ValueError("caption segment text must use NFC normalization")
        return value

    @model_validator(mode="after")
    def _validate_bounds_and_words(self) -> "CaptionSegment":
        if self.end_sample <= self.start_sample:
            raise ValueError("caption segment end must follow start")
        if self.words is None:
            return self
        previous_end = self.start_sample
        for word in self.words:
            if (
                word.start_sample < self.start_sample
                or word.end_sample > self.end_sample
            ):
                raise ValueError("caption words must be contained in their segment")
            if word.start_sample < previous_end:
                raise ValueError("caption words must be monotonic")
            previous_end = word.end_sample
        return self


class CaptionSegmentationPolicy(StrictModel):
    policy_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    max_characters: int = Field(strict=True, gt=0)
    max_lines: int = Field(strict=True, gt=0)
    break_strategy: Literal["provider_segments", "sentence", "word_window"]


class CaptionTrack(VersionedArtifact):
    schema_version: Literal["2.1"] = "2.1"
    caption_track_id: str = Field(min_length=1)
    language: str = Field(min_length=1)
    script_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    transcript_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_audio_asset_id: str = Field(min_length=1)
    source_audio_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_sample_rate_hz: int = Field(strict=True, gt=0)
    segments: tuple[CaptionSegment, ...]
    segmentation_policy: CaptionSegmentationPolicy
    alignment_provider: str = Field(min_length=1)
    alignment_model: str | None = None
    alignment_receipt_id: str = Field(min_length=1)
    style_reference_id: str | None = None
    timing_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_segment_order(self) -> "CaptionTrack":
        previous_end = 0
        segment_ids: set[str] = set()
        for segment in self.segments:
            if segment.segment_id in segment_ids:
                raise ValueError("caption segment IDs must be unique")
            segment_ids.add(segment.segment_id)
            if segment.start_sample < previous_end:
                raise ValueError("caption segments must be monotonic")
            previous_end = segment.end_sample
        return self


class CaptionStyleReference(StrictModel):
    artifact_id: str = Field(min_length=1)
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    path: Path

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "CaptionStyleReference":
        value = _require_clean_relative_file_path(self.path, "caption style")
        if value != Path(f"assets/styles/{self.content_hash}.json"):
            raise ValueError("caption style path must be canonical")
        return self


class CaptionTrackBinding(StrictModel):
    binding_id: str = Field(min_length=1)
    caption_asset_id: str = Field(min_length=1)
    source_audio_track_id: str = Field(min_length=1)
    shot_id: str | None = None
    style_reference: CaptionStyleReference | None = None


class CaptionStyleBindingContract(StrictModel):
    caption_track: CaptionTrack
    caption_metadata: CaptionAssetMetadata
    binding: CaptionTrackBinding

    @model_validator(mode="after")
    def _validate_three_way_style_identity(self) -> "CaptionStyleBindingContract":
        if self.caption_track.caption_track_id != self.caption_metadata.caption_track_id:
            raise ValueError("caption track and metadata identity must match")
        track_style_id = self.caption_track.style_reference_id
        metadata_style_id = self.caption_metadata.style_reference_id
        metadata_style_hash = self.caption_metadata.style_content_hash
        binding_style = self.binding.style_reference
        if all(
            value is None
            for value in (
                track_style_id,
                metadata_style_id,
                metadata_style_hash,
                binding_style,
            )
        ):
            return self
        if (
            track_style_id is None
            or metadata_style_id is None
            or metadata_style_hash is None
            or binding_style is None
            or track_style_id != metadata_style_id
            or track_style_id != binding_style.artifact_id
            or metadata_style_hash != binding_style.content_hash
        ):
            raise ValueError("caption style three-way identity must match exactly")
        return self


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
    schema_version: Literal["2.0", "2.1"] = "2.0"
    composition_id: str
    shot_ids: tuple[str, ...] = Field(min_length=1)
    layers: tuple[CompositionLayerSpec, ...] = Field(min_length=1)
    transitions: tuple[TransitionSpec, ...] = ()
    delivery_profile: DeliveryProfile
    sample_rate: int = Field(default=48_000, gt=0)
    requested_renderer: RendererKind = RendererKind.HYPERFRAMES
    audio_tracks: tuple[AudioTrackSpec, ...] = ()
    caption_tracks: tuple[CaptionTrackBinding, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _reject_explicit_p4_fields_in_20(cls, value: object) -> object:
        if (
            isinstance(value, Mapping)
            and value.get("schema_version", "2.0") == "2.0"
            and {"audio_tracks", "caption_tracks"}.intersection(value)
        ):
            raise ValueError("CompositionSpec 2.0 cannot contain explicit P4 fields")
        return value

    @model_validator(mode="after")
    def _validate_versioned_tracks(self) -> "CompositionSpec":
        if self.schema_version == "2.0" and (self.audio_tracks or self.caption_tracks):
            raise ValueError("CompositionSpec 2.0 cannot contain P4 tracks")
        audio_ids = tuple(item.track_id for item in self.audio_tracks)
        caption_ids = tuple(item.binding_id for item in self.caption_tracks)
        if len(audio_ids) != len(set(audio_ids)):
            raise ValueError("audio track IDs must be unique")
        if len(caption_ids) != len(set(caption_ids)):
            raise ValueError("caption binding IDs must be unique")
        if any(item.style_reference is None for item in self.caption_tracks):
            raise ValueError("bound caption tracks require a style reference")
        return self

    @model_serializer(mode="wrap")
    def _serialize_compatible_tracks(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.schema_version == "2.0":
            data.pop("audio_tracks", None)
            data.pop("caption_tracks", None)
        return data


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


class ResolvedDuckingSpec(StrictModel):
    sidechain_track_ids: tuple[str, ...] = Field(min_length=1)
    attenuation_millidb: int = Field(strict=True, lt=0)
    attack_samples: int = Field(strict=True, ge=0)
    release_samples: int = Field(strict=True, ge=0)


class ResolvedAudioSpan(StrictModel):
    track_id: str = Field(min_length=1)
    audio_kind: AudioKind
    asset_id: str = Field(min_length=1)
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    start_sample: int = Field(strict=True, ge=0)
    duration_samples: int = Field(strict=True, gt=0)
    source_start_sample: int = Field(strict=True, ge=0)
    source_duration_samples: int = Field(strict=True, gt=0)
    gain_millidb: int = Field(strict=True)
    fade_in_samples: int = Field(strict=True, ge=0)
    fade_out_samples: int = Field(strict=True, ge=0)
    ducking: ResolvedDuckingSpec | None = None

    @model_validator(mode="after")
    def _validate_fades(self) -> "ResolvedAudioSpan":
        if self.fade_in_samples + self.fade_out_samples > self.duration_samples:
            raise ValueError("resolved audio fades cannot exceed duration")
        if self.ducking is not None and self.track_id in self.ducking.sidechain_track_ids:
            raise ValueError("resolved audio track cannot duck itself")
        return self


class ResolvedCaptionCue(StrictModel):
    caption_asset_id: str = Field(min_length=1)
    caption_asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    caption_track_id: str = Field(min_length=1)
    caption_timing_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    segment_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    speaker_id: str | None = None
    start_sample: int = Field(strict=True, ge=0)
    end_sample: int = Field(strict=True, gt=0)
    start_frame: int = Field(strict=True, ge=0)
    end_frame_exclusive: int = Field(strict=True, gt=0)
    style_reference_id: str | None = None
    style_content_hash: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )

    @model_validator(mode="after")
    def _validate_cue_bounds_and_style(self) -> "ResolvedCaptionCue":
        if self.end_sample <= self.start_sample:
            raise ValueError("resolved caption sample end must follow start")
        if self.end_frame_exclusive <= self.start_frame:
            raise ValueError("resolved caption frame end must follow start")
        if (self.style_reference_id is None) != (self.style_content_hash is None):
            raise ValueError("resolved caption style identity must be all-or-none")
        return self


class ResolvedTimeline(VersionedArtifact):
    schema_version: Literal["2.0", "2.1"] = "2.0"
    timeline_id: str
    composition_spec_id: str
    composition_spec_revision: int = Field(ge=1)
    composition_spec_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    delivery_profile: DeliveryProfile
    sample_rate: int = Field(gt=0)
    renderer: RendererIdentity
    visual_spans: tuple[ResolvedVisualSpan, ...] = Field(min_length=1)
    audio_spans: tuple[ResolvedAudioSpan, ...] = ()
    caption_cues: tuple[ResolvedCaptionCue, ...] = ()
    total_frames: int = Field(gt=0)
    total_samples: int = Field(ge=0)
    composition_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="before")
    @classmethod
    def _reject_explicit_p4_fields_in_20(cls, value: object) -> object:
        if (
            isinstance(value, Mapping)
            and value.get("schema_version", "2.0") == "2.0"
            and {"audio_spans", "caption_cues"}.intersection(value)
        ):
            raise ValueError("ResolvedTimeline 2.0 cannot contain explicit P4 fields")
        return value

    @model_validator(mode="after")
    def _validate_versioned_resolved_tracks(self) -> "ResolvedTimeline":
        if self.schema_version == "2.0" and (self.audio_spans or self.caption_cues):
            raise ValueError("ResolvedTimeline 2.0 cannot contain P4 timing fields")
        if any(
            item.start_sample + item.duration_samples > self.total_samples
            for item in self.audio_spans
        ):
            raise ValueError("resolved audio span exceeds timeline")
        track_ids = tuple(item.track_id for item in self.audio_spans)
        span_identities = tuple(
            (
                item.asset_id,
                item.start_sample,
                item.duration_samples,
                item.source_start_sample,
                item.source_duration_samples,
            )
            for item in self.audio_spans
        )
        if len(track_ids) != len(set(track_ids)) or len(span_identities) != len(
            set(span_identities)
        ):
            raise ValueError("resolved audio span identities must be unique")
        canonical_audio_order = tuple(
            sorted(
                self.audio_spans,
                key=lambda item: (
                    AUDIO_KIND_PRIORITY[item.audio_kind],
                    item.track_id,
                    item.start_sample,
                    item.asset_id,
                ),
            )
        )
        if self.audio_spans != canonical_audio_order:
            raise ValueError("resolved audio spans must use canonical mix order")
        cue_identities = tuple(
            (
                cue.caption_asset_id,
                cue.caption_track_id,
                cue.segment_id,
                cue.start_sample,
                cue.end_sample,
            )
            for cue in self.caption_cues
        )
        if len(cue_identities) != len(set(cue_identities)):
            raise ValueError("resolved caption cue identities must be unique")
        for cue in self.caption_cues:
            if cue.end_sample > self.total_samples or cue.end_frame_exclusive > self.total_frames:
                raise ValueError("resolved caption cue exceeds timeline")
        canonical_caption_order = tuple(
            sorted(
                self.caption_cues,
                key=lambda cue: (
                    cue.start_sample,
                    cue.end_sample,
                    cue.caption_track_id,
                    cue.segment_id,
                    cue.caption_asset_id,
                ),
            )
        )
        if self.caption_cues != canonical_caption_order:
            raise ValueError("resolved caption cues must use canonical order")
        return self

    @model_serializer(mode="wrap")
    def _serialize_compatible_timing(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.schema_version == "2.0":
            data.pop("audio_spans", None)
            data.pop("caption_cues", None)
        return data


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


class RendererAudioBinding(StrictModel):
    asset_id: str = Field(min_length=1)
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_mime_type: Literal[
        "audio/wav",
        "audio/mpeg",
        "audio/mp4",
        "audio/aac",
        "audio/flac",
    ]
    materialized_path: Path
    sample_rate_hz: int = Field(strict=True, gt=0)
    channels: int = Field(strict=True, ge=1, le=2)
    duration_samples: int = Field(strict=True, gt=0)
    resolved_track_ids: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_materialized_identity(self) -> "RendererAudioBinding":
        suffix_by_mime = {
            "audio/wav": ".wav",
            "audio/mpeg": ".mp3",
            "audio/mp4": ".m4a",
            "audio/aac": ".aac",
            "audio/flac": ".flac",
        }
        if (
            self.materialized_path.stem != self.asset_sha256
            or self.materialized_path.suffix != suffix_by_mime[self.asset_mime_type]
        ):
            raise ValueError("renderer audio MIME requires exact hash suffix mapping")
        if len(self.resolved_track_ids) != len(set(self.resolved_track_ids)):
            raise ValueError("renderer audio resolved track IDs must be unique")
        return self


class RendererCaptionBinding(StrictModel):
    caption_track_id: str = Field(min_length=1)
    caption_asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    materialized_path: Path
    style_reference_id: str | None = None
    style_content_hash: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    style_materialized_path: Path | None = None
    resolved_cue_ids: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_style_identity(self) -> "RendererCaptionBinding":
        style_values = (
            self.style_reference_id,
            self.style_content_hash,
            self.style_materialized_path,
        )
        if any(value is None for value in style_values) and any(
            value is not None for value in style_values
        ):
            raise ValueError("renderer caption style identity must be all-or-none")
        if (
            self.materialized_path.stem != self.caption_asset_sha256
            or self.materialized_path.suffix != ".json"
        ):
            raise ValueError("renderer caption binding must point to hash-named JSON")
        if self.style_materialized_path is not None:
            assert self.style_content_hash is not None
            if (
                self.style_materialized_path.stem != self.style_content_hash
                or self.style_materialized_path.suffix != ".json"
            ):
                raise ValueError("renderer caption style must point to hash-named JSON")
        if len(self.resolved_cue_ids) != len(set(self.resolved_cue_ids)):
            raise ValueError("renderer caption resolved cue IDs must be unique")
        return self


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
        asset_paths: set[Path] = set()
        for asset in self.assets:
            if asset.path.parent != expected_root / "assets":
                raise ValueError("render source bundle asset path must be canonical")
            if asset.path.stem != asset.file_sha256 or asset.path.suffix not in {
                ".png",
                ".jpg",
                ".webp",
                ".wav",
                ".mp3",
                ".m4a",
                ".aac",
                ".flac",
                ".json",
            }:
                raise ValueError("render source bundle asset path must match its hash")
            if asset.path in asset_paths:
                raise ValueError("render source bundle asset paths must be unique")
            asset_paths.add(asset.path)
        return self


class RendererSourceReceipt(VersionedArtifact):
    schema_version: Literal["2.0", "2.1"] = "2.0"
    attempt_id: str
    renderer: RendererIdentity
    timeline_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_bundle: RenderSourceBundlePointer
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asset_bindings: tuple[RendererAssetBinding, ...] = Field(min_length=1)
    audio_bindings: tuple[RendererAudioBinding, ...] = ()
    caption_bindings: tuple[RendererCaptionBinding, ...] = ()
    checks: tuple[RendererCheckReceipt, RendererCheckReceipt]

    @model_validator(mode="before")
    @classmethod
    def _reject_explicit_p4_fields_in_20(cls, value: object) -> object:
        if (
            isinstance(value, Mapping)
            and value.get("schema_version", "2.0") == "2.0"
            and {"audio_bindings", "caption_bindings"}.intersection(value)
        ):
            raise ValueError(
                "RendererSourceReceipt 2.0 cannot contain explicit P4 fields"
            )
        return value

    @model_validator(mode="after")
    def _validate_source_identity(self) -> "RendererSourceReceipt":
        if self.source_sha256 != self.source_bundle.index.file_sha256:
            raise ValueError("renderer source identity does not match its index")
        if tuple(item.command for item in self.checks) != ("lint", "check"):
            raise ValueError("renderer source checks must contain lint then check")
        if any(item.tool_version != self.renderer.version for item in self.checks):
            raise ValueError("renderer source check identity does not match renderer")
        if self.schema_version == "2.0" and (
            self.audio_bindings or self.caption_bindings
        ):
            raise ValueError("RendererSourceReceipt 2.0 cannot contain P4 bindings")
        bound_paths = {item.materialized_path for item in self.asset_bindings}
        bound_paths.update(item.materialized_path for item in self.audio_bindings)
        for item in self.caption_bindings:
            bound_paths.add(item.materialized_path)
            if item.style_materialized_path is not None:
                bound_paths.add(item.style_materialized_path)
        bundle_paths = {item.path for item in self.source_bundle.assets}
        if bound_paths != bundle_paths:
            raise ValueError("renderer source bindings must match exact bundle assets")
        return self

    @model_serializer(mode="wrap")
    def _serialize_compatible_bindings(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.schema_version == "2.0":
            data.pop("audio_bindings", None)
            data.pop("caption_bindings", None)
        return data


class MeasuredAudioRenderMetadata(StrictModel):
    stream_count: int = Field(strict=True, ge=0)
    codec_name: str = Field(min_length=1)
    sample_rate_hz: int = Field(strict=True, gt=0)
    channels: int = Field(strict=True, ge=1, le=2)
    channel_layout: AudioChannelLayout
    decoded_samples: int = Field(strict=True, ge=0)
    encoder_priming_samples: int = Field(strict=True, ge=0)
    encoder_padding_samples: int = Field(strict=True, ge=0)
    measurement_method: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_stream_layout(self) -> "MeasuredAudioRenderMetadata":
        if self.stream_count != 1:
            raise ValueError("P4 measured audio requires exactly one stream")
        if (self.channels, self.channel_layout) not in {
            (1, AudioChannelLayout.MONO),
            (2, AudioChannelLayout.STEREO),
        }:
            raise ValueError("measured audio channels and layout must agree")
        return self


class MeasuredRenderMetadata(StrictModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps_num: int = Field(gt=0)
    fps_den: int = Field(gt=0)
    duration_frames: int = Field(gt=0)
    codec_name: str
    audio: MeasuredAudioRenderMetadata | None = None


def _require_canonical_render_output_path(value: Path, file_sha256: str) -> Path:
    value = _require_clean_relative_file_path(value, "render output")
    if value != Path(f"state/render/outputs/{file_sha256}.mp4"):
        raise ValueError("render output path must be the canonical durable output path")
    return value


class RenderReceipt(VersionedArtifact):
    schema_version: Literal["2.0", "2.1"] = "2.0"
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
    decoded_audio_fingerprint: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )

    @model_validator(mode="before")
    @classmethod
    def _reject_explicit_p4_fields_in_20(cls, value: object) -> object:
        if not isinstance(value, Mapping) or value.get("schema_version", "2.0") != "2.0":
            return value
        measured = value.get("measured")
        if "decoded_audio_fingerprint" in value or (
            isinstance(measured, Mapping) and "audio" in measured
        ):
            raise ValueError("RenderReceipt 2.0 cannot contain explicit P4 fields")
        return value

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
        if self.schema_version == "2.0" and (
            self.measured.audio is not None
            or self.decoded_audio_fingerprint is not None
        ):
            raise ValueError("RenderReceipt 2.0 cannot contain P4 audio evidence")
        if (self.measured.audio is None) != (
            self.decoded_audio_fingerprint is None
        ):
            raise ValueError("measured audio and decoded audio fingerprint must agree")
        return self

    @model_serializer(mode="wrap")
    def _serialize_compatible_audio(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.schema_version == "2.0":
            data.pop("decoded_audio_fingerprint", None)
            measured = data.get("measured")
            if isinstance(measured, dict):
                measured.pop("audio", None)
        return data


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


class VoiceRequestReceipt(StrictModel):
    request_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    script_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_kind: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    voice_id: str = Field(min_length=1)
    language: str = Field(min_length=1)
    pricing_snapshot_id: str = Field(min_length=1)
    budget_reservation_receipt_id: str = Field(min_length=1)
    egress_authorization_receipt_id: str = Field(min_length=1)
    destination: str = Field(min_length=1)

    @field_validator("destination")
    @classmethod
    def _require_canonical_https_origin(cls, value: str) -> str:
        return _require_canonical_https_origin(value, "voice destination")


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
    voice_request: VoiceRequestReceipt | None = None
    voice_phase: (
        Literal[
            "request",
            "submit_intent",
            "provider_call",
            "materialize",
            "probe",
            "align",
            "candidate",
            "activate",
        ]
        | None
    ) = None
    provider_request_id: str | None = None
    candidate_audio_asset_ids: tuple[str, ...] = ()
    candidate_caption_asset_ids: tuple[str, ...] = ()
    base_dependency_graph: DependencyGraphSnapshotPointer | None = None
    candidate_dependency_graph: DependencyGraphSnapshotPointer | None = None
    candidate_dependency_states_hash: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    started_at: str
    finished_at: str | None = None
    error_code: str | None = None
    error_message: str | None = None

    @model_validator(mode="after")
    def _validate_terminal_error(self) -> "StateCommitAttempt":
        p5_graph_fields_present = any(
            value is not None
            for value in (
                self.base_dependency_graph,
                self.candidate_dependency_graph,
                self.candidate_dependency_states_hash,
            )
        )
        if (
            p5_graph_fields_present
            and self.operation not in _P5_AWARE_OPERATIONS
        ):
            raise ValueError(
                "P5 graph fields are only allowed in P5-aware operations; "
                f"got operation={self.operation!r}"
            )
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
        voice_fields_present = any(
            value is not None
            for value in (
                self.voice_request,
                self.voice_phase,
                self.provider_request_id,
            )
        ) or bool(self.candidate_audio_asset_ids or self.candidate_caption_asset_ids)
        if self.operation != "voice_generation" and voice_fields_present:
            raise ValueError("non-voice operations cannot contain voice fields")
        if self.operation == "voice_generation":
            if self.voice_request is None or self.voice_phase is None:
                raise ValueError("voice_generation attempts require voice request and phase")
            if self.voice_request.attempt_id != self.attempt_id:
                raise ValueError("voice attempt identity does not match request")
            all_voice_phases = {
                "request",
                "submit_intent",
                "provider_call",
                "materialize",
                "probe",
                "align",
                "candidate",
                "activate",
            }
            allowed_terminal_phases = {
                StateCommitStatus.RUNNING: all_voice_phases,
                StateCommitStatus.SUCCEEDED: {"activate"},
                StateCommitStatus.FAILED: all_voice_phases,
                StateCommitStatus.INTERRUPTED: {
                    "request",
                    "materialize",
                    "probe",
                    "align",
                    "candidate",
                },
                StateCommitStatus.OUTCOME_UNKNOWN: {
                    "submit_intent",
                    "provider_call",
                    "materialize",
                    "probe",
                    "align",
                    "candidate",
                    "activate",
                },
            }
            if self.voice_phase not in allowed_terminal_phases[self.status]:
                raise ValueError("voice attempt status and phase are inconsistent")
            if self.candidate_project not in (None, self.base_project):
                raise ValueError("voice candidate project identity does not match")
            if self.voice_phase in {"candidate", "activate"}:
                if self.candidate_registry is None or not self.candidate_audio_asset_ids:
                    raise ValueError("voice candidate phase requires candidate audio bundle")
            elif (
                self.candidate_registry is not None
                or self.candidate_audio_asset_ids
                or self.candidate_caption_asset_ids
            ):
                raise ValueError("voice candidate bundle requires candidate phase")
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
        if self.operation != "voice_generation":
            for field in (
                "voice_request",
                "voice_phase",
                "provider_request_id",
                "candidate_audio_asset_ids",
                "candidate_caption_asset_ids",
            ):
                data.pop(field, None)
        for field in (
            "base_dependency_graph",
            "candidate_dependency_graph",
            "candidate_dependency_states_hash",
        ):
            if data.get(field) is None:
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
    schema_version: Literal["2.0", "2.1", "2.2", "2.3"] = "2.0"
    project_id: str
    manifest_revision: int = Field(ge=1)
    active_project: ProjectSnapshotPointer
    active_registry: RegistrySnapshotPointer
    active_render_state: RenderStateSnapshotPointer | None = None
    active_dependency_graph: DependencyGraphSnapshotPointer | None = None
    dependency_states: tuple[DependencyNodeState, ...] = Field(default=())
    attempts: tuple[StateCommitAttempt, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _reject_explicit_voice_fields_in_old_versions(cls, value: object) -> object:
        if (
            not isinstance(value, Mapping)
            or value.get("schema_version", "2.0") == "2.2"
        ):
            return value
        for attempt in value.get("attempts", ()):
            if isinstance(attempt, Mapping) and {
                "voice_request",
                "voice_phase",
                "provider_request_id",
                "candidate_audio_asset_ids",
                "candidate_caption_asset_ids",
            }.intersection(attempt):
                raise ValueError(
                    f"Production Manifest {value.get('schema_version', '2.0')} "
                    "cannot contain explicit P4 voice fields"
                )
        return value

    @model_validator(mode="before")
    @classmethod
    def _reject_explicit_p5_graph_fields_in_old_versions(
        cls, value: object
    ) -> object:
        if not isinstance(value, Mapping):
            return value
        if value.get("schema_version", "2.0") == "2.3":
            return value
        manifest_version = value.get("schema_version", "2.0")
        if {
            "active_dependency_graph",
            "dependency_states",
        }.intersection(value):
            raise ValueError(
                f"Production Manifest {manifest_version} "
                "cannot contain explicit P5 graph fields"
            )
        for attempt in value.get("attempts", ()):
            if isinstance(attempt, Mapping) and {
                "base_dependency_graph",
                "candidate_dependency_graph",
                "candidate_dependency_states_hash",
            }.intersection(attempt):
                raise ValueError(
                    f"Production Manifest {manifest_version} "
                    "cannot contain P5 graph attempt fields"
                )
        return value

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
        if self.schema_version in {"2.0", "2.1"} and any(
            item.operation == "voice_generation" for item in self.attempts
        ):
            raise ValueError(
                f"Production Manifest {self.schema_version} cannot contain voice attempts"
            )
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
        if self.schema_version == "2.3":
            self._validate_manifest_23_graph_lifecycle()
        else:
            for attempt in self.attempts:
                if (
                    attempt.base_dependency_graph is not None
                    or attempt.candidate_dependency_graph is not None
                    or attempt.candidate_dependency_states_hash is not None
                ):
                    raise ValueError(
                        f"Production Manifest {self.schema_version} "
                        "cannot contain P5 graph attempt fields"
                    )
        return self

    def _validate_manifest_23_graph_lifecycle(self) -> None:
        if self.dependency_states and self.active_dependency_graph is None:
            raise ValueError(
                "Manifest 2.3 with dependency_states requires "
                "active_dependency_graph"
            )
        if self.active_dependency_graph is not None:
            active_revision = self.active_dependency_graph.revision_id
            for state in self.dependency_states:
                if (
                    state.lifecycle is not DependencyLifecycle.SUPERSEDED
                    and state.graph_revision_id != active_revision
                ):
                    raise ValueError(
                        "active dependency state graph_revision_id must "
                        "match active graph revision_id"
                    )
        state_node_ids = [state.node_id for state in self.dependency_states]
        if len(state_node_ids) != len(set(state_node_ids)):
            raise ValueError(
                "Production Manifest dependency state node IDs must be unique"
            )

    @model_serializer(mode="wrap")
    def _serialize_compatible_schema(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.schema_version == "2.0" and self.active_render_state is None:
            data.pop("active_render_state", None)
        if self.schema_version != "2.3" or self.active_dependency_graph is None:
            data.pop("active_dependency_graph", None)
            data.pop("dependency_states", None)
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
    render_state: RenderStateSnapshot | None = None
    dependency_graph: DependencyGraphSnapshot | None = None

    _freeze_asset_paths = field_validator("asset_paths")(_immutable_mapping)


# ---------------------------------------------------------------------------
# P5 Dependency Graph immutable input contracts
#
# Graph snapshots are pure, content-addressed resolver inputs. They MUST NOT
# carry mutable desired/applied fingerprints, lifecycle status, timestamps or
# active selection. Lifecycle ownership belongs to ``ProductionManifest`` 2.3
# and ``StateCommitAttempt`` P5-aware fields; graph validation, DAG traversal,
# topological order, semantic hashing and rebuild decisions are owned by
# ``src/ai_video/production/dependency.py`` (Task 2, not implemented here).
# ---------------------------------------------------------------------------


_P5_AWARE_OPERATIONS: frozenset[str] = frozenset(
    {
        "bootstrap_dependency_graph",
        "commit_project_registry",
        "audio_import",
        "voice_generation",
        "render_state",
    }
)


class DependencyNodeKind(str, Enum):
    CREATIVE_ARTIFACT = "creative_artifact"
    ASSET = "asset"
    COMPOSITION_SPEC = "composition_spec"
    RESOLVED_TIMELINE = "resolved_timeline"
    RENDERER_SOURCE = "renderer_source"
    RENDER = "render"


class DependencySemanticRole(str, Enum):
    NONE = "none"
    VOICE = "voice"
    VISUAL = "visual"
    AUDIO = "audio"
    CAPTION = "caption"
    COMPOSITION = "composition"
    TIMELINE = "timeline"
    RENDERER_SOURCE = "renderer_source"
    RENDER = "render"


class DependencyReason(str, Enum):
    AUTHORING_INPUT = "authoring_input"
    GENERATION_INPUT = "generation_input"
    ASSET_BINDING = "asset_binding"
    AUDIO_SOURCE = "audio_source"
    ALIGNMENT_TIMING = "alignment_timing"
    CAPTION_STYLE = "caption_style"
    COMPOSITION_RESOLUTION = "composition_resolution"
    TIMELINE_MATERIALIZATION = "timeline_materialization"
    RENDER_EXECUTION = "render_execution"


class DependencyLifecycle(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    FAILED = "failed"
    BLOCKED = "blocked"
    SUPERSEDED = "superseded"


class FingerprintContribution(StrictModel):
    key: str = Field(min_length=1)
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


def _canonical_contributions(
    contributions: tuple[FingerprintContribution, ...],
) -> tuple[FingerprintContribution, ...]:
    return tuple(sorted(contributions, key=lambda item: item.key))


class DependencyNode(StrictModel):
    node_id: str = Field(min_length=1)
    kind: DependencyNodeKind
    semantic_role: DependencySemanticRole
    artifact_id: str = Field(min_length=1)
    artifact_revision: int | None = Field(default=None, ge=1)
    contributions: tuple[FingerprintContribution, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _canonical_contributions_unique_and_ordered(
        self,
    ) -> "DependencyNode":
        keys = tuple(item.key for item in self.contributions)
        if len(keys) != len(set(keys)):
            raise ValueError("dependency node contribution keys must be unique")
        canonical = _canonical_contributions(self.contributions)
        if self.contributions != canonical:
            raise ValueError(
                "dependency node contributions must be ordered by key"
            )
        return self


class DependencyEdge(StrictModel):
    source_node_id: str = Field(min_length=1)
    target_node_id: str = Field(min_length=1)
    reason: DependencyReason
    contribution: FingerprintContribution


class DependencyGraphSnapshot(StrictModel):
    schema_version: Literal["2.0"] = "2.0"
    revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    nodes: tuple[DependencyNode, ...]
    edges: tuple[DependencyEdge, ...]

    @model_validator(mode="after")
    def _canonical_graph_structure(self) -> "DependencyGraphSnapshot":
        node_ids = tuple(node.node_id for node in self.nodes)
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("dependency graph node IDs must be unique")
        canonical_nodes = tuple(
            sorted(self.nodes, key=lambda node: node.node_id)
        )
        if self.nodes != canonical_nodes:
            raise ValueError(
                "dependency graph nodes must be ordered by node_id"
            )
        edge_keys = tuple(
            (
                edge.target_node_id,
                edge.source_node_id,
                edge.reason.value,
                edge.contribution.key,
            )
            for edge in self.edges
        )
        if len(edge_keys) != len(set(edge_keys)):
            raise ValueError(
                "dependency graph edges must be unique by "
                "(target_node_id, source_node_id, reason, contribution.key)"
            )
        canonical_edges = tuple(
            sorted(
                self.edges,
                key=lambda edge: (
                    edge.target_node_id,
                    edge.source_node_id,
                    edge.reason.value,
                    edge.contribution.key,
                ),
            )
        )
        if self.edges != canonical_edges:
            raise ValueError(
                "dependency graph edges must use canonical "
                "(target, source, reason, key) order"
            )
        if self.revision_id != self.content_hash:
            raise ValueError(
                "dependency graph revision_id must equal content_hash"
            )
        return self


class DependencyGraphSnapshotPointer(StrictModel):
    revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    path: Path
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _canonical_pointer(self) -> "DependencyGraphSnapshotPointer":
        clean_path = _require_clean_relative_file_path(
            self.path, "dependency graph"
        )
        if self.revision_id != self.content_hash:
            raise ValueError(
                "dependency graph pointer revision_id must match content_hash"
            )
        expected = Path(f"state/dependency_graph.{self.revision_id}.json")
        if clean_path != expected:
            raise ValueError(
                "dependency graph pointer path must be canonical"
            )
        return self


class ProjectDependencyEvidence(StrictModel):
    owner: Literal["project_snapshot"]
    pointer: ProjectSnapshotPointer
    artifact_id: str = Field(min_length=1)
    artifact_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class RegistryDependencyEvidence(StrictModel):
    owner: Literal["registry_snapshot"]
    pointer: RegistrySnapshotPointer
    artifact_id: str = Field(min_length=1)
    artifact_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class RenderDependencyEvidence(StrictModel):
    owner: Literal["render_state"]
    pointer: RenderStateSnapshotPointer
    artifact_id: str = Field(min_length=1)
    artifact_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


DependencyAppliedEvidence = Union[
    ProjectDependencyEvidence,
    RegistryDependencyEvidence,
    RenderDependencyEvidence,
]


class DependencyNodeState(StrictModel):
    node_id: str = Field(min_length=1)
    graph_revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    desired_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    applied_fingerprint: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    lifecycle: DependencyLifecycle
    applied_evidence: DependencyAppliedEvidence | None = Field(
        default=None, discriminator="owner"
    )
    blocked_by: tuple[str, ...] = Field(default=())
    error_code: str | None = None
    error_message: str | None = None

    @model_validator(mode="after")
    def _canonical_blocked_by(self) -> "DependencyNodeState":
        canonical = tuple(sorted(set(self.blocked_by)))
        if self.blocked_by != canonical:
            raise ValueError(
                "dependency node blocked_by must be sorted and unique"
            )
        return self

    @model_validator(mode="after")
    def _validate_local_invariants(self) -> "DependencyNodeState":
        applied_evidence = self.applied_evidence
        if (
            applied_evidence is not None
            and applied_evidence.artifact_fingerprint != self.applied_fingerprint
        ):
            raise ValueError(
                "applied evidence artifact_fingerprint must match "
                "applied_fingerprint"
            )
        if self.lifecycle is DependencyLifecycle.FRESH:
            if self.applied_fingerprint is None:
                raise ValueError(
                    "fresh lifecycle requires applied_fingerprint"
                )
            if self.applied_fingerprint != self.desired_fingerprint:
                raise ValueError(
                    "fresh lifecycle requires "
                    "applied_fingerprint == desired_fingerprint"
                )
            if applied_evidence is None:
                raise ValueError(
                    "fresh lifecycle requires applied_evidence"
                )
            if self.blocked_by:
                raise ValueError(
                    "fresh lifecycle cannot have blocked_by"
                )
            if self.error_code is not None or self.error_message is not None:
                raise ValueError(
                    "fresh lifecycle cannot carry error fields"
                )
        elif self.lifecycle is DependencyLifecycle.STALE:
            if self.blocked_by:
                raise ValueError("stale lifecycle cannot have blocked_by")
            if self.error_code is not None or self.error_message is not None:
                raise ValueError(
                    "stale lifecycle cannot carry error fields"
                )
        elif self.lifecycle is DependencyLifecycle.FAILED:
            if self.error_code is None or self.error_message is None:
                raise ValueError(
                    "failed lifecycle requires typed error fields"
                )
            if self.blocked_by:
                raise ValueError(
                    "failed lifecycle cannot have blocked_by"
                )
        elif self.lifecycle is DependencyLifecycle.BLOCKED:
            if not self.blocked_by:
                raise ValueError(
                    "blocked lifecycle requires non-empty blocked_by"
                )
            if self.error_code is not None or self.error_message is not None:
                raise ValueError(
                    "blocked lifecycle cannot carry error fields"
                )
        elif self.lifecycle is DependencyLifecycle.SUPERSEDED:
            if self.blocked_by:
                raise ValueError("superseded lifecycle cannot have blocked_by")
            if self.error_code is not None or self.error_message is not None:
                raise ValueError(
                    "superseded lifecycle cannot carry error fields"
                )
        return self


class DependencyGraphTransition(StrictModel):
    expected_manifest_revision: int = Field(ge=1)
    base_dependency_graph: DependencyGraphSnapshotPointer | None = None
    candidate_dependency_graph: DependencyGraphSnapshotPointer
    candidate_dependency_states: tuple[DependencyNodeState, ...] = Field(
        default=()
    )
    candidate_dependency_states_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _canonical_states_match_candidate_graph(self) -> "DependencyGraphTransition":
        active_revision = self.candidate_dependency_graph.revision_id
        node_ids = tuple(state.node_id for state in self.candidate_dependency_states)
        if len(node_ids) != len(set(node_ids)):
            raise ValueError(
                "transition candidate_dependency_states node IDs must be unique"
            )
        canonical_states = tuple(
            sorted(self.candidate_dependency_states, key=lambda state: state.node_id)
        )
        if self.candidate_dependency_states != canonical_states:
            raise ValueError(
                "transition candidate_dependency_states must be ordered by node_id"
            )
        for state in self.candidate_dependency_states:
            if (
                state.lifecycle is not DependencyLifecycle.SUPERSEDED
                and state.graph_revision_id != active_revision
            ):
                raise ValueError(
                    "transition active candidate state graph_revision_id must "
                    "match candidate_dependency_graph revision_id"
                )
        return self


LoadedProductionProject.model_rebuild()
