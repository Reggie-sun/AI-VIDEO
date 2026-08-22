"""Deterministic, development-only Composition Playbook validation."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping, Sequence
from enum import Enum
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PLAYBOOK_ROOT = PROJECT_ROOT / ".agent" / "playbooks" / "composition"
SCHEMA_PATH = CANONICAL_PLAYBOOK_ROOT / "schema.json"
_SRC_ROOT = PROJECT_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from ai_video.planning._planner_models import ContinuityMode, GenerationMode

PLAYBOOK_ID_PATTERN = r"^[a-z][a-z0-9_]{2,63}$"
_SEMVER = r"^[1-9][0-9]*\.[0-9]+\.[0-9]+$"
_WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")
_FORBIDDEN_FIELDS = frozenset(
    {
        "active_output",
        "asset_identity",
        "budget_reservation",
        "dependency_state",
        "final_acceptance",
        "manifest_state",
        "model_id",
        "permit",
        "profile_id",
        "provider",
        "provider_name",
        "provider_task_id",
        "qa_verdict",
        "registry_revision",
        "resolved_timeline",
        "task_id",
    }
)

NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]


class PlaybookValidationError(ValueError):
    """Raised when a Playbook file or registry violates advisory boundaries."""


class RequiredInput(str, Enum):
    TARGET_SHOT = "target_shot"
    SHOT_INTENT = "shot_intent"
    MOTION_REQUIREMENT = "motion_requirement"
    PREVIOUS_SHOT_TERMINAL = "previous_shot_terminal"
    CHARACTER_REFERENCES = "character_references"
    SCENE_REFERENCE = "scene_reference"
    APPROVED_KEYFRAME = "approved_keyframe"
    CONTINUITY_STATE = "continuity_state"
    NARRATION_TRACK = "narration_track"
    CAPTION_TRACK = "caption_track"


class ForbiddenFallback(str, Enum):
    UNANCHORED_TEXT_TO_VIDEO = "unanchored_text_to_video"
    SILENT_STATIC_SUBSTITUTION = "silent_static_substitution"
    SILENT_IMAGE_MOTION_SUBSTITUTION = "silent_image_motion_substitution"
    REUSE_REFERENCE_AS_FINAL_VISUAL = "reuse_reference_as_final_visual"
    ALL_SHOTS_GENERATED_VIDEO = "all_shots_generated_video"
    AUTOMATIC_PROVIDER_FALLBACK = "automatic_provider_fallback"
    PROVIDER_SPECIFIC_HARD_BINDING = "provider_specific_hard_binding"


class EvidenceRequirement(str, Enum):
    TARGET_SHOT_IDENTITY = "target_shot_identity"
    SHOT_INTENT_EVIDENCE = "shot_intent_evidence"
    MOTION_REQUIREMENT = "motion_requirement"
    PREVIOUS_TERMINAL_BYTES = "previous_terminal_bytes"
    CHARACTER_IDENTITY_REFERENCES = "character_identity_references"
    SCENE_REFERENCE = "scene_reference"
    APPROVED_KEYFRAME = "approved_keyframe"
    CONTINUITY_STATE = "continuity_state"
    NARRATION_TIMING = "narration_timing"
    HUMAN_CONTINUITY_REVIEW = "human_continuity_review"


class ExpectedFailureMode(str, Enum):
    IDENTITY_DRIFT = "identity_drift"
    POSE_DISCONTINUITY = "pose_discontinuity"
    SPATIAL_DISCONTINUITY = "spatial_discontinuity"
    CAMERA_ANGLE_MISMATCH = "camera_angle_mismatch"
    MULTI_CHARACTER_OCCLUSION = "multi_character_occlusion"
    FRAMING_MISMATCH = "framing_mismatch"
    STATIC_FEEL = "static_feel"
    MOTION_ARTIFACT = "motion_artifact"
    COST_OVERUSE = "cost_overuse"
    REFERENCE_LEAKAGE = "reference_leakage"
    TIMING_MISMATCH = "timing_mismatch"


class ReviewRequirement(str, Enum):
    CONTINUITY = "continuity"
    IDENTITY = "identity"
    POSE = "pose"
    SPATIAL_LAYOUT = "spatial_layout"
    CAMERA_AXIS = "camera_axis"
    FRAMING = "framing"
    OCCLUSION = "occlusion"
    MOTION_NEED = "motion_need"
    COST_FIT = "cost_fit"
    VOICE_CAPTION_TIMELINE = "voice_caption_timeline"


class RepairAction(str, Enum):
    RECHECK_TERMINAL_LINEAGE = "recheck_terminal_lineage"
    REQUEST_SHOT_SPECIFIC_KEYFRAME = "request_shot_specific_keyframe"
    STRENGTHEN_IDENTITY_REFERENCES = "strengthen_identity_references"
    REDUCE_REFERENCE_SET = "reduce_reference_set"
    SPLIT_OCCLUDED_CHARACTERS = "split_occluded_characters"
    RELAX_EXACT_TERMINAL_TO_REFERENCE = "relax_exact_terminal_to_reference"
    REASSESS_MOTION_NEED = "reassess_motion_need"
    DOWNGRADE_TO_IMAGE_MOTION = "downgrade_to_image_motion"
    DOWNGRADE_TO_STATIC_IMAGE = "downgrade_to_static_image"
    ESCALATE_HERO_SHOT_TO_GENERATED_VIDEO = "escalate_hero_shot_to_generated_video"
    REQUIRE_HUMAN_REVIEW = "require_human_review"


def _unique_field(default: object = ...) -> object:
    kwargs = {
        "min_length": 1,
        "json_schema_extra": {"uniqueItems": True},
    }
    if default is ...:
        return Field(**kwargs)
    return Field(default=default, **kwargs)


class PlaybookDocument(BaseModel):
    """Strict advisory schema mirrored by ``schema.json``."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    version: str = Field(pattern=_SEMVER)
    playbook_id: str = Field(pattern=PLAYBOOK_ID_PATTERN)
    description: NonEmptyText
    applicable_when: tuple[NonEmptyText, ...] = _unique_field()
    required_inputs: tuple[RequiredInput, ...] = _unique_field()
    preferred_strategies: tuple[GenerationMode, ...] = _unique_field()
    forbidden_fallbacks: tuple[ForbiddenFallback, ...] = _unique_field()
    evidence_required: tuple[EvidenceRequirement, ...] = _unique_field()
    known_limitations: tuple[NonEmptyText, ...] = _unique_field()
    expected_failure_modes: tuple[ExpectedFailureMode, ...] = _unique_field()
    review_requirements: tuple[ReviewRequirement, ...] = _unique_field()
    repair_playbook: tuple[RepairAction, ...] = _unique_field()
    continuity_preferences: tuple[ContinuityMode, ...] = Field(
        default=(),
        json_schema_extra={"uniqueItems": True},
    )
    quality_notes: tuple[NonEmptyText, ...] = Field(
        default=(),
        json_schema_extra={"uniqueItems": True},
    )

    @model_validator(mode="after")
    def _validate_unique_collections(self) -> "PlaybookDocument":
        for field_name in (
            "applicable_when",
            "required_inputs",
            "preferred_strategies",
            "forbidden_fallbacks",
            "evidence_required",
            "known_limitations",
            "expected_failure_modes",
            "review_requirements",
            "repair_playbook",
            "continuity_preferences",
            "quality_notes",
        ):
            values = getattr(self, field_name)
            if len(set(values)) != len(values):
                raise ValueError(f"{field_name} values must be unique")
        return self


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise PlaybookValidationError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _walk_values(value: object) -> Sequence[object]:
    if isinstance(value, Mapping):
        return tuple(value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _validate_advisory_boundary(value: object) -> None:
    if isinstance(value, Mapping):
        for key in value:
            normalized = str(key).strip().lower()
            if normalized in _FORBIDDEN_FIELDS:
                raise PlaybookValidationError(f"forbidden field: {key}")
    if isinstance(value, str):
        normalized = value.strip()
        if (
            normalized.startswith(("/", "~/", "~\\", "\\\\"))
            or _WINDOWS_ABSOLUTE_PATH.match(normalized)
        ):
            raise PlaybookValidationError(f"absolute path is forbidden: {value}")
    for child in _walk_values(value):
        _validate_advisory_boundary(child)


def expected_json_schema() -> dict[str, object]:
    return PlaybookDocument.model_json_schema(mode="validation")


def validate_checked_in_schema() -> None:
    try:
        checked_in = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PlaybookValidationError(f"invalid checked-in schema: {exc}") from exc
    if checked_in != expected_json_schema():
        raise PlaybookValidationError(
            "schema.json does not match the deterministic Playbook model schema"
        )


def load_composition_playbook(path: Path) -> PlaybookDocument:
    validate_checked_in_schema()
    if not path.is_file() or path.is_symlink():
        raise PlaybookValidationError(f"playbook must be a regular file: {path}")
    try:
        payload = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except PlaybookValidationError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise PlaybookValidationError(f"invalid Playbook YAML: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise PlaybookValidationError("Playbook YAML root must be a mapping")
    _validate_advisory_boundary(payload)
    return PlaybookDocument.model_validate(payload)


def load_composition_playbooks(
    root: Path = CANONICAL_PLAYBOOK_ROOT,
) -> tuple[PlaybookDocument, ...]:
    if not root.is_dir() or root.is_symlink():
        raise PlaybookValidationError(f"playbook root must be a directory: {root}")
    paths = tuple(sorted(root.glob("*.yaml"), key=lambda path: path.name))
    if not paths:
        raise PlaybookValidationError("playbook root contains no YAML playbooks")
    playbooks = tuple(load_composition_playbook(path) for path in paths)
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    for playbook in playbooks:
        if playbook.playbook_id in seen_ids:
            raise PlaybookValidationError(
                f"duplicate playbook_id: {playbook.playbook_id}"
            )
        if playbook.name in seen_names:
            raise PlaybookValidationError(f"duplicate playbook name: {playbook.name}")
        seen_ids.add(playbook.playbook_id)
        seen_names.add(playbook.name)
    return playbooks
