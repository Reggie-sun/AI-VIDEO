"""QA-owned semantics types and validation; no inventory, selection or I/O."""

from collections.abc import Mapping
from typing import Literal

from pydantic import Field, model_serializer, model_validator

from ai_video.production.artifact_contracts import StrictModel

SEMANTICS_VERSION = "requirement-semantics/1"
SHA256 = r"^[0-9a-f]{64}$"


class IntentReference(StrictModel):
    source_hash: str = Field(pattern=SHA256)
    locator: str = Field(min_length=1)


class IntentSourceReference(IntentReference):
    intent_item_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    origin: Literal["explicit_user", "director_choice", "repair_margin"]
    fixed: bool = False

    @model_serializer(mode="wrap")
    def _optional_fixed(self, handler):
        data = handler(self)
        if not self.fixed:
            data.pop("fixed", None)
        return data


class HardBasis(IntentReference):
    kind: Literal["explicit_user", "approved_narrative", "accepted_quality", "production_contract"]
    necessity: str = Field(min_length=1)


class RequirementSemantics(StrictModel):
    version: Literal["requirement-semantics/1"]
    category: Literal["narrative_critical", "quality_critical", "directional_preference",
                      "diagnostic_observation", "governance"]
    intent_role: Literal["must_happen", "must_not_happen", "preferred_performance", "timing_target",
                         "acceptable_variation", "diagnostic", "production_contract"]
    source_refs: tuple[IntentSourceReference, ...] = Field(min_length=1)
    hard_basis: HardBasis | None = None
    derived_from: tuple[IntentReference, ...] = ()

    def require_level(self, level):
        expected = {"directional_preference": "recipe_hint", "diagnostic_observation": "diagnostic"}.get(
            self.category, "acceptance")
        if level != expected:
            raise ValueError("requirement semantic category and level disagree")
        if level == "acceptance":
            if self.hard_basis is None:
                raise ValueError("hard requirement needs an accepted hard_basis")
            matching = [r for r in self.source_refs if r.source_hash == self.hard_basis.source_hash
                        and r.locator == self.hard_basis.locator and r.origin != "repair_margin"]
            if not matching:
                raise ValueError("repair margin alone cannot establish a hard basis")
            if self.hard_basis.kind == "explicit_user" and not any(r.origin == "explicit_user" for r in matching):
                raise ValueError("explicit user basis requires original user evidence")
        elif self.hard_basis is not None or any(r.fixed for r in self.source_refs):
            raise ValueError("fixed requirements cannot be weakened to advisory")


class EventTimeWindow(StrictModel):
    kind: Literal["event_time_window"]
    event_id: str = Field(min_length=1)
    event_definition: str = Field(min_length=1)
    boundary: Literal["start", "end", "completion"]
    timebase: Literal["source_media_millis"]
    source_role: Literal["fetched_raw"]
    selection_rule: Literal["submitted_output"]
    lower_millis: int = Field(strict=True, ge=0)
    upper_millis: int = Field(strict=True, ge=0)
    lower_inclusive: bool
    upper_inclusive: bool
    allowed_methods: tuple[str, ...] = Field(min_length=1)
    required_coverage: tuple[int, int]
    uncertainty: Literal["bounded_interval"]

    @model_validator(mode="after")
    def _window(self):
        if self.lower_millis > self.upper_millis or (
            self.lower_millis == self.upper_millis and not (self.lower_inclusive and self.upper_inclusive)
        ):
            raise ValueError("event time window is empty")
        start, end = self.required_coverage
        if start < 0 or end < start or start > self.lower_millis or end < self.upper_millis:
            raise ValueError("measurement coverage must contain the allowed window")
        if any(not m.strip() for m in self.allowed_methods):
            raise ValueError("measurement methods must be explicit")
        return self

    @property
    def tolerance_text(self):
        left, right = ("[" if self.lower_inclusive else "("), ("]" if self.upper_inclusive else ")")
        return f"{self.event_id}: {left}{self.lower_millis}, {self.upper_millis}{right} source_media_millis"

    @property
    def measurement_text(self):
        return (f"{self.event_definition}; boundary={self.boundary}; "
                f"methods={','.join(self.allowed_methods)}; coverage={self.required_coverage[0]}.."
                f"{self.required_coverage[1]}; uncertainty={self.uncertainty}")


class RequirementExpressionFields(StrictModel):
    """Shared shape at the existing QA inventory and recipe projection boundaries."""

    requirement_id: str = Field(min_length=1)
    level: Literal["acceptance", "recipe_hint", "diagnostic"]
    stage: Literal["raw_generation", "shot_editorial", "final_composition"]
    dimension: str = Field(min_length=1)
    observable: str = Field(min_length=1)
    tolerance: str = Field(min_length=1)
    measurement: str = Field(min_length=1)
    proof: Literal["technical", "analyzer", "human"]
    intent_paths: tuple[str, ...] = ()
    native_text: tuple[str, ...] = ()
    production_owner: str = Field(min_length=1)
    semantics: RequirementSemantics | None = None
    measurement_spec: EventTimeWindow | None = None

    @model_validator(mode="after")
    def _semantic_shape(self):
        if self.semantics is not None:
            self.semantics.require_level(self.level)
        if self.measurement_spec is not None:
            if self.semantics is None or self.stage != "raw_generation":
                raise ValueError("typed source measurement requires marked raw semantics")
            if (self.tolerance != self.measurement_spec.tolerance_text
                    or self.measurement != self.measurement_spec.measurement_text):
                raise ValueError("time predicate prose must match its canonical structured representation")
        return self

    @model_serializer(mode="wrap")
    def _preserve_legacy_fields(self, handler):
        data = handler(self)
        for name in ("semantics", "measurement_spec"):
            if getattr(self, name) is None:
                data.pop(name, None)
        return data


def validate_semantic_inventory(payload, required_ids):
    marker = payload.get("requirement_semantics_version")
    inventory = payload.get("generation_requirements", ())
    if marker is None:
        if "requirement_semantics_version" in payload or any(
            isinstance(item, Mapping) and ("semantics" in item or "measurement_spec" in item)
            for item in inventory
        ):
            raise ValueError("semantic metadata requires the selected QA marker")
        return ()
    if marker != SEMANTICS_VERSION:
        raise ValueError("unknown requirement semantics version")
    if not inventory:
        raise ValueError("marked QA requires a complete inventory")
    rules = tuple(RequirementExpressionFields.model_validate(item) for item in inventory)
    ids = tuple(r.requirement_id for r in rules)
    if len(set(ids)) != len(ids) or any(r.semantics is None for r in rules):
        raise ValueError("marked QA requires unique IDs and complete semantic metadata")
    if {r.requirement_id for r in rules if r.level == "acceptance"} != set(required_ids):
        raise ValueError("marked QA must preserve exact hard requirement coverage")
    return rules


def require_final_contract(rules, final_output):
    for rule in rules:
        if rule.level != "acceptance" or rule.stage != "final_composition":
            continue
        if final_output is None:
            raise ValueError("marked final requirement needs the existing FinalOutputContract")
        expected = next((r for r in final_output.requirements if r.requirement_id == rule.requirement_id), None)
        proof = {"human": "human", "analyzer": "evaluator"}.get(rule.proof)
        if (expected is None or expected.observable != rule.observable or expected.proof != proof
                or not any(ref.source_hash == final_output.contract_hash and ref.locator == rule.requirement_id
                           for ref in rule.semantics.source_refs)):
            raise ValueError("marked final requirement differs from the final owner contract")
