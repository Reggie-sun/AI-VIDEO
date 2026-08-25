from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class GraphicRole(str, Enum):
    DIALOGUE_SUBTITLE = "dialogue_subtitle"
    HEADLINE = "headline"
    BENEFIT_CALLOUT = "benefit_callout"
    PRODUCT_LABEL = "product_label"
    PROOF_LABEL = "proof_label"
    CTA = "cta"
    BRAND_END_CARD = "brand_end_card"


class GraphicAnimation(str, Enum):
    NONE = "none"
    FADE = "fade"
    SLIDE_UP = "slide_up"
    SCALE_IN = "scale_in"


class AdSoundRole(str, Enum):
    DIALOGUE = "dialogue"
    VOICE_OVER = "voice_over"
    MUSIC = "music"
    SFX = "sfx"
    REVEAL_HIT = "reveal_hit"
    INTENTIONAL_SILENCE = "intentional_silence"


class GraphicSafeAreaInsets(_StrictModel):
    top_milli: int = Field(default=0, strict=True, ge=0, le=1000)
    right_milli: int = Field(default=0, strict=True, ge=0, le=1000)
    bottom_milli: int = Field(default=0, strict=True, ge=0, le=1000)
    left_milli: int = Field(default=0, strict=True, ge=0, le=1000)

    @model_validator(mode="after")
    def _validate_non_empty_safe_area(self) -> "GraphicSafeAreaInsets":
        if self.left_milli + self.right_milli >= 1000:
            raise ValueError("horizontal safe-area insets leave no drawable width")
        if self.top_milli + self.bottom_milli >= 1000:
            raise ValueError("vertical safe-area insets leave no drawable height")
        return self


class GraphicKeywordEmphasis(_StrictModel):
    text: str = Field(min_length=1)
    brand_token_id: str = Field(min_length=1)


class AdvertisingSoundCueProjection(_StrictModel):
    cue_id: str = Field(min_length=1)
    role: AdSoundRole
    audio_track_id: str | None = None
    synchronized_event_id: str | None = None


class GraphicLayerAnimation(_StrictModel):
    layer_id: str = Field(min_length=1)
    entrance: GraphicAnimation = GraphicAnimation.NONE
    exit: GraphicAnimation = GraphicAnimation.NONE


class GraphicTreatment(_StrictModel):
    graphic_id: str = Field(min_length=1)
    role: GraphicRole
    text: str = Field(min_length=1)
    shot_id: str = Field(min_length=1)
    start_frame_offset: int = Field(strict=True, ge=0)
    duration_frames: int = Field(strict=True, gt=0)
    x_milli: int = Field(strict=True, ge=0, le=1000)
    y_milli: int = Field(strict=True, ge=0, le=1000)
    width_milli: int = Field(strict=True, gt=0, le=1000)
    font_size_px: int = Field(strict=True, gt=0, le=512)
    text_color: str = Field(pattern=r"^#[0-9A-Fa-f]{8}$|^#[0-9A-Fa-f]{6}$")
    background_color: str | None = Field(
        default=None, pattern=r"^#[0-9A-Fa-f]{8}$|^#[0-9A-Fa-f]{6}$"
    )
    claim_reference_ids: tuple[str, ...] = ()
    safe_area: GraphicSafeAreaInsets = Field(default_factory=GraphicSafeAreaInsets)
    avoidance_target_ids: tuple[str, ...] = ()
    keyword_emphasis: tuple[GraphicKeywordEmphasis, ...] = ()
    brand_token_ids: tuple[str, ...] = ()
    synchronized_event_id: str | None = None
    sound_cue_ids: tuple[str, ...] = ()
    entrance: GraphicAnimation = GraphicAnimation.NONE
    exit: GraphicAnimation = GraphicAnimation.NONE
    z_index: int = Field(strict=True)
    caption_binding_id: str | None = None

    @model_validator(mode="after")
    def _separate_subtitles_from_commercial_graphics(self) -> "GraphicTreatment":
        if self.role is GraphicRole.DIALOGUE_SUBTITLE:
            if self.caption_binding_id is None:
                raise ValueError("dialogue subtitle requires a CaptionTrack binding")
        elif self.caption_binding_id is not None:
            raise ValueError("commercial graphics cannot use CaptionTrack bindings")
        if self.x_milli < self.safe_area.left_milli:
            raise ValueError("commercial graphic starts outside horizontal safe area")
        if self.x_milli + self.width_milli > 1000 - self.safe_area.right_milli:
            raise ValueError("commercial graphic exceeds horizontal safe area")
        if self.y_milli < self.safe_area.top_milli:
            raise ValueError("commercial graphic starts outside vertical safe area")
        emphasis_tokens = {item.brand_token_id for item in self.keyword_emphasis}
        if not emphasis_tokens.issubset(self.brand_token_ids):
            raise ValueError("keyword emphasis must reference declared brand tokens")
        emphasis_text = tuple(item.text for item in self.keyword_emphasis)
        if len(emphasis_text) != len(set(emphasis_text)):
            raise ValueError("keyword emphasis text must be unique")
        if any(item not in self.text for item in emphasis_text):
            raise ValueError("keyword emphasis text must occur in graphic text")
        if any(
            left in right or right in left
            for index, left in enumerate(emphasis_text)
            for right in emphasis_text[index + 1 :]
        ):
            raise ValueError("keyword emphasis text cannot overlap")
        return self


class ResolvedCommercialGraphic(_StrictModel):
    graphic_id: str = Field(min_length=1)
    role: GraphicRole
    text: str = Field(min_length=1)
    shot_id: str = Field(min_length=1)
    start_frame: int = Field(strict=True, ge=0)
    end_frame_exclusive: int = Field(strict=True, gt=0)
    start_sample: int = Field(strict=True, ge=0)
    end_sample: int = Field(strict=True, gt=0)
    x_milli: int = Field(strict=True, ge=0, le=1000)
    y_milli: int = Field(strict=True, ge=0, le=1000)
    width_milli: int = Field(strict=True, gt=0, le=1000)
    font_size_px: int = Field(strict=True, gt=0, le=512)
    text_color: str = Field(pattern=r"^#[0-9A-Fa-f]{8}$|^#[0-9A-Fa-f]{6}$")
    background_color: str | None = Field(
        default=None, pattern=r"^#[0-9A-Fa-f]{8}$|^#[0-9A-Fa-f]{6}$"
    )
    claim_reference_ids: tuple[str, ...] = ()
    safe_area: GraphicSafeAreaInsets = Field(default_factory=GraphicSafeAreaInsets)
    avoidance_target_ids: tuple[str, ...] = ()
    keyword_emphasis: tuple[GraphicKeywordEmphasis, ...] = ()
    brand_token_ids: tuple[str, ...] = ()
    synchronized_event_id: str | None = None
    sound_cue_ids: tuple[str, ...] = ()
    entrance: GraphicAnimation
    exit: GraphicAnimation
    z_index: int = Field(strict=True)

    @model_validator(mode="after")
    def _validate_resolved_window(self) -> "ResolvedCommercialGraphic":
        if self.role is GraphicRole.DIALOGUE_SUBTITLE:
            raise ValueError("dialogue subtitle cannot enter commercial graphics")
        if self.end_frame_exclusive <= self.start_frame:
            raise ValueError("commercial graphic frame end must follow start")
        if self.end_sample <= self.start_sample:
            raise ValueError("commercial graphic sample end must follow start")
        return self
