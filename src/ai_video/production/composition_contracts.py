from __future__ import annotations

from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Literal, Mapping

from pydantic import Field, SerializerFunctionWrapHandler, model_serializer, model_validator

from ai_video.production.artifact_contracts import StrictModel, VersionedArtifact
from ai_video.production.commercial_graphics import (
    AdvertisingSoundCueProjection,
    GraphicLayerAnimation,
    GraphicRole,
    GraphicTreatment,
    ResolvedCommercialGraphic,
)


class DeliveryProfile(StrictModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps: int = Field(gt=0)
    codec_profile: str = "h264"


class AudioKind(str, Enum):
    DIALOGUE = "dialogue"
    NARRATION = "narration"
    AMBIENCE = "ambience"
    SFX = "sfx"
    BGM = "bgm"


AUDIO_KIND_PRIORITY: Mapping[AudioKind, int] = MappingProxyType(
    {kind: priority for priority, kind in enumerate(AudioKind)}
)


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


class CaptionStyleReference(StrictModel):
    artifact_id: str = Field(min_length=1)
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    path: Path

    @model_validator(mode="after")
    def _validate_canonical_path(self) -> "CaptionStyleReference":
        if self.path.is_absolute() or ".." in self.path.parts or self.path == Path("."):
            raise ValueError(
                "caption style path must be clean and project-relative file path"
            )
        if self.path != Path(f"assets/styles/{self.content_hash}.json"):
            raise ValueError("caption style path must be canonical")
        return self


class CaptionTrackBinding(StrictModel):
    binding_id: str = Field(min_length=1)
    caption_asset_id: str = Field(min_length=1)
    source_audio_track_id: str = Field(min_length=1)
    shot_id: str | None = None
    style_reference: CaptionStyleReference | None = None


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
    schema_version: Literal["2.0", "2.1", "2.2"] = "2.0"
    composition_id: str
    shot_ids: tuple[str, ...] = Field(min_length=1)
    layers: tuple[CompositionLayerSpec, ...] = Field(min_length=1)
    transitions: tuple[TransitionSpec, ...] = ()
    delivery_profile: DeliveryProfile
    sample_rate: int = Field(default=48_000, gt=0)
    requested_renderer: RendererKind = RendererKind.HYPERFRAMES
    audio_tracks: tuple[AudioTrackSpec, ...] = ()
    caption_tracks: tuple[CaptionTrackBinding, ...] = ()
    graphic_layer_ids: tuple[str, ...] = ()
    graphic_layer_animations: tuple[GraphicLayerAnimation, ...] = ()
    commercial_graphics: tuple[GraphicTreatment, ...] = ()
    advertising_sound_cues: tuple[AdvertisingSoundCueProjection, ...] = ()
    ad_creative_plan_id: str | None = None
    ad_creative_plan_hash: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )

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

    @model_validator(mode="before")
    @classmethod
    def _reject_explicit_ad_fields_before_22(cls, value: object) -> object:
        if (
            isinstance(value, Mapping)
            and value.get("schema_version", "2.0") in {"2.0", "2.1"}
            and {
                "graphic_layer_ids",
                "graphic_layer_animations",
                "commercial_graphics",
                "advertising_sound_cues",
                "ad_creative_plan_id",
                "ad_creative_plan_hash",
            }.intersection(value)
        ):
            raise ValueError("CompositionSpec before 2.2 cannot contain ad graphics")
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
        if self.schema_version != "2.2" and (
            self.graphic_layer_ids
            or self.graphic_layer_animations
            or self.commercial_graphics
            or self.advertising_sound_cues
            or self.ad_creative_plan_id is not None
            or self.ad_creative_plan_hash is not None
        ):
            raise ValueError("CompositionSpec before 2.2 cannot contain ad graphics")
        layer_ids = {item.layer_id for item in self.layers}
        if len(self.graphic_layer_ids) != len(set(self.graphic_layer_ids)):
            raise ValueError("graphic layer IDs must be unique")
        if not set(self.graphic_layer_ids).issubset(layer_ids):
            raise ValueError("graphic layer IDs must reference composition layers")
        animation_layer_ids = tuple(
            item.layer_id for item in self.graphic_layer_animations
        )
        if len(animation_layer_ids) != len(set(animation_layer_ids)):
            raise ValueError("graphic layer animation IDs must be unique")
        if not set(animation_layer_ids).issubset(self.graphic_layer_ids):
            raise ValueError("graphic layer animations must reference graphic layers")
        graphic_ids = tuple(item.graphic_id for item in self.commercial_graphics)
        if len(graphic_ids) != len(set(graphic_ids)):
            raise ValueError("commercial graphic IDs must be unique")
        if any(
            item.role is GraphicRole.DIALOGUE_SUBTITLE
            for item in self.commercial_graphics
        ):
            raise ValueError("dialogue subtitles cannot be commercial graphics")
        sound_cue_ids = tuple(item.cue_id for item in self.advertising_sound_cues)
        if len(sound_cue_ids) != len(set(sound_cue_ids)):
            raise ValueError("advertising sound cue IDs must be unique")
        if (self.ad_creative_plan_id is None) != (self.ad_creative_plan_hash is None):
            raise ValueError("ad creative plan identity must be all-or-none")
        if (
            self.schema_version == "2.2"
            and (
                self.graphic_layer_ids
                or self.commercial_graphics
                or self.advertising_sound_cues
            )
            and self.ad_creative_plan_id is None
        ):
            raise ValueError("ad graphics require exact AdCreativePlan identity")
        return self

    @model_serializer(mode="wrap")
    def _serialize_compatible_tracks(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.schema_version == "2.0":
            data.pop("audio_tracks", None)
            data.pop("caption_tracks", None)
        if self.schema_version != "2.2":
            data.pop("graphic_layer_ids", None)
            data.pop("graphic_layer_animations", None)
            data.pop("commercial_graphics", None)
            data.pop("advertising_sound_cues", None)
            data.pop("ad_creative_plan_id", None)
            data.pop("ad_creative_plan_hash", None)
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
    asset_mime_type: Literal["image/png", "image/jpeg", "image/webp", "video/mp4"]
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
    graphic_animation: GraphicLayerAnimation | None = None

    @model_serializer(mode="wrap")
    def _serialize_optional_graphic_animation(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.graphic_animation is None:
            data.pop("graphic_animation", None)
        return data

    @model_validator(mode="after")
    def _validate_graphic_animation_identity(self) -> "ResolvedVisualSpan":
        if (
            self.graphic_animation is not None
            and self.graphic_animation.layer_id != self.layer_id
        ):
            raise ValueError("graphic animation must match resolved visual layer")
        return self


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
    schema_version: Literal["2.0", "2.1", "2.2"] = "2.0"
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
    commercial_graphics: tuple[ResolvedCommercialGraphic, ...] = ()
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

    @model_validator(mode="before")
    @classmethod
    def _reject_explicit_ad_fields_before_22(cls, value: object) -> object:
        if (
            isinstance(value, Mapping)
            and value.get("schema_version", "2.0") in {"2.0", "2.1"}
            and "commercial_graphics" in value
        ):
            raise ValueError("ResolvedTimeline before 2.2 cannot contain ad graphics")
        return value

    @model_validator(mode="after")
    def _validate_versioned_resolved_tracks(self) -> "ResolvedTimeline":
        if self.schema_version == "2.0" and (self.audio_spans or self.caption_cues):
            raise ValueError("ResolvedTimeline 2.0 cannot contain P4 timing fields")
        if self.schema_version != "2.2" and self.commercial_graphics:
            raise ValueError("ResolvedTimeline before 2.2 cannot contain ad graphics")
        if self.schema_version != "2.2" and any(
            item.graphic_animation is not None for item in self.visual_spans
        ):
            raise ValueError("ResolvedTimeline before 2.2 cannot contain graphic animation")
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
            if (
                cue.end_sample > self.total_samples
                or cue.end_frame_exclusive > self.total_frames
            ):
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
        graphic_ids = tuple(item.graphic_id for item in self.commercial_graphics)
        if len(graphic_ids) != len(set(graphic_ids)):
            raise ValueError("resolved commercial graphic IDs must be unique")
        if any(
            item.end_frame_exclusive > self.total_frames
            or item.end_sample > self.total_samples
            for item in self.commercial_graphics
        ):
            raise ValueError("resolved commercial graphic exceeds timeline")
        canonical_graphics = tuple(
            sorted(
                self.commercial_graphics,
                key=lambda item: (item.start_frame, item.z_index, item.graphic_id),
            )
        )
        if self.commercial_graphics != canonical_graphics:
            raise ValueError("resolved commercial graphics must use canonical order")
        return self

    @model_serializer(mode="wrap")
    def _serialize_compatible_timing(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.schema_version == "2.0":
            data.pop("audio_spans", None)
            data.pop("caption_cues", None)
        if self.schema_version != "2.2":
            data.pop("commercial_graphics", None)
        return data
