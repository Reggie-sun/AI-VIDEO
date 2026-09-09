"""Immutable recipe semantics, independent of attempt and audit identities."""

from typing import Literal

from pydantic import Field, model_serializer, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.requirement_semantics import RequirementExpressionFields, validate_semantic_inventory

SHA256 = r"^[0-9a-f]{64}$"
Stage = Literal["raw_generation", "shot_editorial", "final_composition"]
Proof = Literal["technical", "analyzer", "human"]


class SeedPolicy(StrictModel):
    kind: Literal["fixed", "paired", "randomized", "uncontrolled"]
    value: int | None = Field(default=None, strict=True, ge=0)

    @model_validator(mode="after")
    def _explicit_seed(self):
        if (self.kind == "uncontrolled") != (self.value is None):
            raise ValueError("controlled seed policies require an explicit sampled value")
        return self


class RequirementExpression(RequirementExpressionFields):
    """An acceptance-owner projection; recipe hints cannot become findings."""


class CompiledComparison(StrictModel):
    """Exact baseline projection for compiler-enforced intervention deltas."""

    request_hash: str = Field(pattern=SHA256)
    baseline_seed_controlled: bool
    variable_hashes: tuple[tuple[str, str], ...]
    changed_variables: tuple[str, ...]
    held_constants: tuple[str, ...]
    uncontrolled_variables: tuple[str, ...]
    target_variable_hashes: tuple[tuple[str, str], ...] = ()

    @model_serializer(mode="wrap")
    def _preserve_legacy_comparison(self, handler):
        data = handler(self)
        if not self.target_variable_hashes:
            data.pop("target_variable_hashes", None)
        return data

    @model_validator(mode="after")
    def _shape(self):
        names = tuple(k for k, _ in self.variable_hashes)
        if names != tuple(sorted(set(names))):
            raise ValueError("baseline variable identities must be unique and sorted")
        if any(len(value) != 64 or any(c not in "0123456789abcdef" for c in value)
               for _, value in self.variable_hashes):
            raise ValueError("baseline values must be exact SHA-256 hashes")
        if set(self.changed_variables) & set(self.held_constants):
            raise ValueError("comparison delta and held constants overlap")
        target_names = tuple(name for name, _ in self.target_variable_hashes)
        if len(set(target_names)) != len(target_names) or not set(target_names) <= set(self.changed_variables):
            raise ValueError("target values must uniquely identify changed variables")
        if any(len(value) != 64 or any(c not in "0123456789abcdef" for c in value)
               for _, value in self.target_variable_hashes):
            raise ValueError("target values must be exact SHA-256 hashes")
        return self


class GenerationRecipe(StrictModel):
    contract_version: Literal["generation-recipe/1"] = "generation-recipe/1"
    seed: SeedPolicy
    # Profile owns workflow, sampler, LoRA and native hard controls. Never copied
    # into a second mutable control map here.
    profile_sha256: str = Field(pattern=SHA256)
    compiler_hash: str = Field(pattern=SHA256)
    requirement_hash: str = Field(pattern=SHA256)
    rubric_hash: str = Field(pattern=SHA256)
    acceptance_policy: DomainAcceptancePolicy
    expressions: tuple[RequirementExpression, ...] = Field(min_length=1)
    editorial_operations: tuple[Literal["trim", "mix", "compose"], ...] = ()
    comparison: CompiledComparison | None = None

    @model_validator(mode="after")
    def _unique_requirements(self):
        ids = tuple(item.requirement_id for item in self.expressions)
        if ids != tuple(sorted(set(ids))):
            raise ValueError("recipe expressions must have unique sorted requirement IDs")
        if self.rubric_hash != self.acceptance_policy.profile_content_hash:
            raise ValueError("recipe must bind the selected acceptance profile")
        required_ids = {r.requirement_id for r in self.expressions if r.level == "acceptance"}
        if required_ids != set(self.acceptance_policy.required_requirement_ids):
            raise ValueError("recipe omits or adds an accepted requirement")
        inventory = self.acceptance_policy.profile_payload.get("generation_requirements")
        marked_rules = validate_semantic_inventory(self.acceptance_policy.profile_payload,
                                                  self.acceptance_policy.required_requirement_ids)
        if marked_rules:
            # Compare the QA owner's typed projection, including optional-field
            # defaults, while retaining the original sealed profile/hash verbatim.
            inventory = tuple(r.model_dump(mode="json", exclude={"native_text"}) for r in marked_rules)
        actual = tuple(r.model_dump(mode="json", exclude={"native_text"}) for r in self.expressions)
        if inventory is None or canonical_sha256({"rules": inventory}) != canonical_sha256({"rules": actual}):
            raise ValueError("recipe needs the complete versioned acceptance-owner projection")
        for item in self.expressions:
            if item.stage == "shot_editorial" and not self.editorial_operations:
                raise ValueError("editorial requirements need accepted editorial operations")
        return self

    @property
    def recipe_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))

    @property
    def fit_hash(self) -> str:
        # A different sampled seed is not a different model/recipe quality scope.
        payload = self.model_dump(mode="json")
        payload["seed"] = {"kind": self.seed.kind}
        payload.pop("comparison")
        return canonical_sha256(payload)


def expression_errors(recipe, requirement, prompt: str, control_paths=()) -> tuple[str, ...]:
    """Conservative lexical coverage, never a claim of model understanding."""
    payload = requirement.model_dump(mode="json")
    errors = []
    for item in recipe.expressions:
        if item.stage != "raw_generation":
            continue
        if item.semantics is not None and (
            item.level == "diagnostic" or item.level == "recipe_hint" and not item.intent_paths
        ):
            continue
        if not item.intent_paths:
            errors.append(item.requirement_id)
            continue
        prompt_paths = []
        for path in item.intent_paths:
            node = payload
            try:
                for key in path.split("."):
                    node = node[key]
            except (KeyError, TypeError):
                errors.append(item.requirement_id)
                break
            if node is None or node == "unspecified":
                errors.append(item.requirement_id)
            if not path.startswith("output_need.") and path != "audio_need":
                prompt_paths.append((path, node))
        # Output/audio controls are validated against the exact request by the
        # existing binder/compiler. They need not be redundantly put in prose.
        if any(path not in control_paths for path, _ in prompt_paths) and not item.native_text:
            errors.append(item.requirement_id)
        if any(not text or text not in prompt for text in item.native_text):
            errors.append(item.requirement_id)
        for path, value in prompt_paths:
            if path not in control_paths and isinstance(value, str) and value not in prompt:
                errors.append(item.requirement_id)
    errors.extend(_unexpressed_authored_text(requirement, prompt, control_paths))
    return tuple(sorted(set(errors)))


def _unexpressed_authored_text(requirement, prompt, control_paths):
    """Conservative raw-intent check in addition to adapter grammar validation."""
    from enum import Enum
    from ai_video.production.video_requirement import GenerationIntent

    defaults = GenerationIntent().model_dump(mode="python")
    errors = []
    normalized_prompt = prompt.replace("_", " ").replace("-", " ").casefold()

    def visit(node, default, path):
        if node is None or node == default:
            return
        if path in control_paths:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                if key.endswith(("_id", "_ids")) or key == "kind":
                    continue
                visit(value, default.get(key) if isinstance(default, dict) else None, f"{path}.{key}")
        elif isinstance(node, (tuple, list)):
            for index, value in enumerate(node):
                visit(value, None, f"{path}.{index}")
        elif isinstance(node, str) and not isinstance(node, Enum):
            if not node or node in {"none", "unspecified"}:
                return
            if path.endswith("dialogue_intent.language"):
                native = {"en": "English", "zh": "Chinese"}.get(node.split("-")[0])
                if native is not None and native in prompt:
                    return
            value = node.replace("_", " ").replace("-", " ").casefold()
            if value not in normalized_prompt:
                errors.append(path)
        elif isinstance(node, (bool, int, float, Enum)):
            # Only the native grammar owner can attest mechanical translation
            # of controls. A caller-supplied phrase is not a control mapping.
            errors.append(path)

    visit(requirement.generation_intent.model_dump(mode="python"), defaults, "generation_intent")
    return errors
