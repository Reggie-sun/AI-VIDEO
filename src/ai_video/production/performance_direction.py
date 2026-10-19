"""Typed, per-character acting direction for a single generated shot."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import (
    Field,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
    model_validator,
)

from ai_video.production.artifact_contracts import StrictModel


_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"
_PLACEHOLDERS = {
    "-",
    "...",
    "?",
    "n/a",
    "na",
    "none",
    "not applicable",
    "placeholder",
    "tbd",
    "todo",
    "unknown",
    "unspecified",
}
_PHASE_ORDER = {"opening": 0, "response": 1, "settle": 2}
_TEXT_FIELDS = (
    "trigger",
    "emotion",
    "facial_expression",
    "gaze_target",
    "breathing",
    "body_behavior",
)


def _authored_text(value: object) -> object:
    if not isinstance(value, str):
        return value
    text = unicodedata.normalize("NFC", value.strip())
    folded = text.casefold()
    if (
        not text
        or folded in _PLACEHOLDERS
        or re.fullmatch(_SHA256, folded) is not None
        or not any(character.isalnum() for character in text)
    ):
        raise ValueError("performance direction text must contain authored detail")
    return text


class PerformanceBeat(StrictModel):
    """One authored stage of a visible character's performance."""

    phase: Literal["opening", "response", "settle", "throughout"]
    trigger: str
    emotion: str
    intensity: Literal["none", "subtle", "moderate", "strong"]
    facial_expression: str
    gaze_target: str
    breathing: str
    body_behavior: str

    @field_validator(*_TEXT_FIELDS, mode="before")
    @classmethod
    def _validate_authored_text(cls, value: object) -> object:
        return _authored_text(value)


class CharacterPerformanceDirection(StrictModel):
    """A shot-local direction bound to one canonical character identity."""

    character_id: str = Field(pattern=_SAFE_ID)
    screen_identity: str
    role: Literal["principal", "supporting", "background"]
    visibility: Literal["visible", "offscreen"]
    offscreen_reason: str | None = None
    beats: tuple[PerformanceBeat, ...] = Field(default=(), max_length=3)

    @field_validator("character_id", mode="before")
    @classmethod
    def _validate_character_id(cls, value: object) -> object:
        if isinstance(value, str) and value.strip().casefold() in _PLACEHOLDERS:
            raise ValueError("character_id must bind a real authored Character")
        return value

    @field_validator("screen_identity", "offscreen_reason", mode="before")
    @classmethod
    def _validate_authored_identity_text(cls, value: object) -> object:
        return None if value is None else _authored_text(value)

    @model_validator(mode="after")
    def _validate_visibility_and_beats(self) -> "CharacterPerformanceDirection":
        if self.visibility == "visible":
            if not self.beats:
                raise ValueError("visible characters require at least one performance beat")
            if self.offscreen_reason is not None:
                raise ValueError("visible characters cannot carry an offscreen reason")
        else:
            if self.offscreen_reason is None:
                raise ValueError("offscreen characters require an authored reason")
            if self.beats:
                raise ValueError("offscreen characters cannot carry visible performance beats")

        phases = tuple(beat.phase for beat in self.beats)
        if "throughout" in phases:
            if len(phases) != 1:
                raise ValueError("the throughout phase must stand alone")
        else:
            if len(set(phases)) != len(phases):
                raise ValueError("performance beat phases must be unique")
            if phases != tuple(sorted(phases, key=_PHASE_ORDER.__getitem__)):
                raise ValueError("performance beats must be ordered opening, response, settle")
        return self


class PerformanceIntent(StrictModel):
    trigger: str = Field(min_length=1)
    visible_response: str = Field(min_length=1)
    gaze_target: str = Field(min_length=1)
    body_behavior: str = Field(min_length=1)
    hand_behavior: str = Field(min_length=1)
    terminal_performance_state: str = Field(min_length=1)
    character_directions: tuple[CharacterPerformanceDirection, ...] = Field(
        default=(), max_length=16
    )

    @model_validator(mode="after")
    def _validate_unique_character_directions(self) -> "PerformanceIntent":
        character_ids = tuple(
            direction.character_id for direction in self.character_directions
        )
        if len(character_ids) != len(set(character_ids)):
            raise ValueError("character performance directions require unique character IDs")
        return self

    @model_serializer(mode="wrap")
    def _serialize_legacy_performance_shape(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if not self.character_directions:
            data.pop("character_directions", None)
        return data


def performance_direction_issues(intent: object, characters) -> tuple[str, ...]:
    """Return missing or unbound actor paths for a fresh generation boundary.

    ``characters`` accepts canonical Character objects or their already-bound IDs,
    which lets read-only authoring preflight use the same check without materializing
    the Character artifacts.
    """

    performance = getattr(intent, "performance_intent", intent)
    directions = tuple(getattr(performance, "character_directions", ()) or ())
    character_ids = tuple(
        sorted(
            {
                value
                if isinstance(value, str)
                else str(getattr(value, "character_id"))
                for value in (characters or ())
            }
        )
    )
    directed_ids = tuple(sorted(str(item.character_id) for item in directions))
    character_set = set(character_ids)
    directed_set = set(directed_ids)
    prefix = "generation_intent.performance_intent.character_directions"
    issues = [f"{prefix}[{character_id}]" for character_id in sorted(character_set - directed_set)]
    issues.extend(
        f"{prefix}[{character_id}].character_id"
        for character_id in sorted(directed_set - character_set)
    )
    issues.extend(
        f"{prefix}[{character_id}].character_id"
        for character_id in sorted(
            {character_id for character_id in directed_ids if directed_ids.count(character_id) > 1}
        )
    )
    return tuple(issues)


def render_performance_direction(performance: object) -> str:
    """Render authored acting direction as readable native prompt prose."""

    performance = getattr(performance, "performance_intent", performance)
    directions = tuple(getattr(performance, "character_directions", ()) or ())
    if not directions:
        return ""

    actors: list[str] = []
    for direction in directions:
        actor = (
            f"For {direction.screen_identity} ({direction.role}, {direction.visibility})"
        )
        if direction.visibility == "offscreen":
            actors.append(f"{actor}: remains offscreen because {direction.offscreen_reason}.")
            continue

        phase_labels = {
            "opening": "At the opening",
            "response": "In the response",
            "settle": "As the performance settles",
            "throughout": "Throughout the shot",
        }
        intensity_labels = {
            "none": "with no emotional emphasis",
            "subtle": "with subtle intensity",
            "moderate": "with moderate intensity",
            "strong": "with strong intensity",
        }
        beats = []
        for beat in direction.beats:
            beats.append(
                f"{phase_labels[beat.phase]}, after {beat.trigger}, show {beat.emotion} "
                f"{intensity_labels[beat.intensity]}; facial expression: "
                f"{beat.facial_expression}; gaze target: {beat.gaze_target}; "
                f"breathing: {beat.breathing}; body behavior: {beat.body_behavior}."
            )
        actors.append(f"{actor}: " + " ".join(beats))

    return "Character performance directions. " + " ".join(actors)


__all__ = [
    "CharacterPerformanceDirection",
    "PerformanceBeat",
    "PerformanceIntent",
    "performance_direction_issues",
    "render_performance_direction",
]
