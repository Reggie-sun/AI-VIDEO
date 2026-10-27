"""Authored Shot semantics and derived reference advice, not asset/state authority."""

from enum import Enum
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator, model_validator, model_serializer

from ai_video.production.artifact_contracts import StrictModel

Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9._:/-]{1,256}$")]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ReferenceRole(str, Enum):
    IDENTITY = "identity"
    PRODUCT = "product_object"
    SCENE = "scene_environment"
    STYLE = "style_lighting"
    COMPOSITION = "composition"
    KEYFRAME = "temporal_keyframe"
    POSE = "action_pose"
    MOTION = "motion_camera_video"
    BLOCKING = "physical_previsualization"
    GRAPHICS = "postproduction_graphics"


class ShotFacet(str, Enum):
    STABLE = "stable"
    SLOW_CAMERA = "slow_camera"
    COMPLEX_CAMERA = "complex_camera"
    DIALOGUE = "dialogue"
    EMOTIONAL_CHANGE = "emotional_change"
    BLOCKING = "multi_subject_blocking"
    OCCLUSION = "occlusion_change"
    HIGH_SPEED = "high_speed"
    CONTACT = "contact_timing"
    SUSTAINED_CONTACT = "sustained_contact"
    SUPPORT_TRANSFER = "support_transfer"
    PHYSICS = "continuous_physics"
    TRANSFORMATION = "visual_transformation"
    DISAPPEARANCE = "disappearance"
    ENVIRONMENT_CHANGE = "environment_change"
    PRODUCT = "product_accuracy"
    PRODUCT_ROTATION = "product_rotation"
    EXACT_GRAPHICS = "exact_graphics"
    IDENTITY = "identity_consistency"
    SPATIAL = "spatial_precision"


class ReferenceEvent(StrictModel):
    event_id: Identifier
    kind: Literal["composition", "performance", "blocking", "occlusion", "contact",
                  "force", "impact", "state_change", "appearance", "disappearance",
                  "graphic", "cut", "transition"]
    visual_state: Text
    purpose: Text
    phase: Literal["start", "interior", "end"] = "interior"
    segment_id: Identifier | None = None
    at_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    after_event_ids: tuple[Identifier, ...] = ()
    control: Literal["review_only", "model_guidance", "endpoint", "exact_time"] = "review_only"
    priority: Literal["required", "preferred"] = "preferred"

    @model_validator(mode="after")
    def _timing(self):
        if self.control == "endpoint" and self.phase == "interior":
            raise ValueError("endpoint control requires start or end phase")
        if self.control == "exact_time" and self.at_seconds is None:
            raise ValueError("exact_time requires an authored time")
        if self.phase == "start" and self.segment_id is None and self.at_seconds not in {None, 0}:
            raise ValueError("start event cannot have a nonzero time")
        return self


class ReferenceAnchor(StrictModel):
    anchor_id: Identifier
    role: ReferenceRole
    purpose: Text
    owner_id: Identifier | None = None
    priority: Literal["required", "preferred"] = "required"

    @model_validator(mode="after")
    def _persistent_role(self):
        if self.role not in {ReferenceRole.IDENTITY, ReferenceRole.PRODUCT,
                             ReferenceRole.SCENE, ReferenceRole.STYLE, ReferenceRole.COMPOSITION,
                             ReferenceRole.POSE}:
            raise ValueError("persistent anchor cannot claim temporal, motion or postproduction duty")
        if self.role is ReferenceRole.IDENTITY and self.owner_id is None:
            raise ValueError("identity anchor requires its canonical character owner")
        return self


class ReferenceSelection(StrictModel):
    need_id: Identifier
    asset_id: Identifier


class ReferencePlanningIntent(StrictModel):
    contract_version: Literal["shot-reference-intent/1"] = "shot-reference-intent/1"
    facets: tuple[ShotFacet, ...] = ()
    structure: Literal["continuous", "multi_shot"] = "continuous"
    segment_ids: tuple[Identifier, ...] = ()
    events: tuple[ReferenceEvent, ...] = ()
    anchors: tuple[ReferenceAnchor, ...] = ()
    selections: tuple[ReferenceSelection, ...] = ()
    natural_generation: tuple[Text, ...] = ()
    motion_reference_policy: Literal["auto", "required"] = "auto"

    @model_serializer(mode="wrap")
    def _serialize(self, handler):
        payload = handler(self)
        if self.motion_reference_policy == "auto":
            payload.pop("motion_reference_policy", None)
        return payload

    @field_validator("facets")
    @classmethod
    def _facets(cls, value):
        return tuple(sorted(set(value), key=lambda item: item.value))

    @model_validator(mode="after")
    def _structure(self):
        ids = [e.event_id for e in self.events] + [a.anchor_id for a in self.anchors]
        if len(set(ids)) != len(ids) or any(i.startswith("auto:") for i in ids):
            raise ValueError("reference event/anchor IDs must be unique and cannot use auto: prefix")
        if len(set(self.segment_ids)) != len(self.segment_ids):
            raise ValueError("segment IDs must be unique")
        if self.structure == "continuous" and self.segment_ids:
            raise ValueError("continuous Shot cannot declare cut segments")
        if self.structure == "multi_shot" and len(self.segment_ids) < 2:
            raise ValueError("multi-shot generation requires explicit ordered segments")
        seen, last_time, last_segment = set(), -1.0, -1
        phases = {}
        for event in self.events:
            if self.structure == "continuous":
                if event.segment_id is not None or event.kind == "cut":
                    raise ValueError("continuous Shot cannot contain a cut or segment binding")
            else:
                if event.segment_id not in self.segment_ids:
                    raise ValueError("multi-shot event must bind an explicit segment")
                index = self.segment_ids.index(event.segment_id)
                if index < last_segment:
                    raise ValueError("event order contradicts segment order")
                last_segment = index
            phase = {"start": 0, "interior": 1, "end": 2}[event.phase]
            if phase < phases.get(event.segment_id, 0):
                raise ValueError("event phases must follow start/interior/end order")
            phases[event.segment_id] = phase
            if not set(event.after_event_ids).issubset(seen):
                raise ValueError("causal predecessors must precede the event")
            if event.at_seconds is not None:
                if event.at_seconds < last_time:
                    raise ValueError("authored event times contradict event order")
                last_time = event.at_seconds
            seen.add(event.event_id)
        needs = [s.need_id for s in self.selections]
        if len(set(needs)) != len(needs):
            raise ValueError("select at most one exact asset per reference need")
        return self


class ReferenceNeed(StrictModel):
    need_id: Identifier
    role: ReferenceRole
    scope: Literal["persistent", "shot_state", "continuous_motion", "postproduction", "preparation"]
    purpose: Text
    priority: Literal["required", "preferred"]
    mechanism: Literal["review_only", "reference", "first_frame", "last_frame",
                     "reference_video", "exact_time", "composition", "previsualization"]
    event_id: Identifier | None = None
    owner_id: Identifier | None = None
    segment_id: Identifier | None = None
    phase: Literal["start", "interior", "end"] | None = None
    at_seconds: float | None = None
    after_event_ids: tuple[Identifier, ...] = ()


class ShotReferencePlan(StrictModel):
    rule_version: Literal["shot-reference-rules/1", "shot-reference-rules/2"] = "shot-reference-rules/2"
    source_intent_hash: str
    facets: tuple[ShotFacet, ...]
    structure: Literal["continuous", "multi_shot"]
    needs: tuple[ReferenceNeed, ...]
    natural_generation: tuple[str, ...]
    omitted: tuple[str, ...]
    risks: tuple[str, ...]
    alternatives: tuple[str, ...]
    motion_reference_level: Literal["none", "recommended", "previs_priority", "required"] = "none"
    motion_reference_reasons: tuple[str, ...] = ()
    whitebox_decision: Literal["not_needed", "optional_static", "reuse_motion_first"] = "not_needed"
    whitebox_reasons: tuple[str, ...] = ()
    actual_quality: Literal["NOT_EVALUATED"] = "NOT_EVALUATED"

    @property
    def keyframes(self):
        return tuple(n for n in self.needs if n.scope == "shot_state")

    @property
    def image_reference_needed(self):
        return any(n.scope in {"persistent", "shot_state"}
                   and n.mechanism != "review_only" for n in self.needs)
