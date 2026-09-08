"""Generic sealed policy binding for one selected domain acceptance profile."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Any, Literal

from pydantic import (
    Field,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
    model_validator,
)

from ai_video.production._immutable_models import ImmutableDict
from ai_video.production.artifact_contracts import StrictModel, ToolIdentity
from ai_video.production.hashing import canonical_sha256
from ai_video.production.final_output_contracts import FinalOutputContract
from ai_video.production.source_use_evidence import (
    SourceUseEvidence,
    require_source_use_evidence_authority,
)


def _deep_immutable_json(value: object) -> object:
    if isinstance(value, dict):
        return ImmutableDict(
            {key: _deep_immutable_json(item) for key, item in value.items()}
        )
    if isinstance(value, list | tuple):
        return tuple(_deep_immutable_json(item) for item in value)
    return value


class QaLayer(str, Enum):
    TECHNICAL = "technical"
    LAYOUT = "layout"
    CAPTION = "caption"
    STRATEGY = "strategy"
    SEMANTIC = "semantic"
    FINAL_ACCEPTANCE = "final_acceptance"


class DomainAcceptancePolicy(StrictModel):
    """Bind a content-addressed domain profile into the selected QA policy."""

    domain_id: str = Field(min_length=1)
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    profile_payload: dict[str, Any]
    measurement_contract_version: str = Field(min_length=1)
    required_requirement_ids: tuple[str, ...] = Field(min_length=1)

    @field_validator("profile_payload")
    @classmethod
    def _freeze_profile_payload(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _deep_immutable_json(value)  # type: ignore[return-value]

    @model_validator(mode="after")
    def _validate_profile_binding(self) -> "DomainAcceptancePolicy":
        requirement_ids = self.required_requirement_ids
        if any(not item.strip() for item in requirement_ids):
            raise ValueError("Domain acceptance requirement IDs must be nonblank")
        if len(set(requirement_ids)) != len(requirement_ids):
            raise ValueError("Domain acceptance requirement IDs must be unique")

        payload = dict(self.profile_payload)
        declared_hash = payload.pop("content_hash", None)
        if declared_hash != self.profile_content_hash:
            raise ValueError("Domain acceptance profile hash does not match payload")
        if canonical_sha256(payload) != self.profile_content_hash:
            raise ValueError("Domain acceptance profile payload is not sealed")
        expected_identity = {
            "domain_id": self.domain_id,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "measurement_contract_version": self.measurement_contract_version,
        }
        if any(self.profile_payload.get(key) != value for key, value in expected_identity.items()):
            raise ValueError("Domain acceptance profile identity does not match policy")
        if tuple(self.profile_payload.get("required_requirement_ids", ())) != requirement_ids:
            raise ValueError("Domain acceptance requirement coverage does not match profile")
        return self


class GenerationEvaluationAuthority(StrictModel):
    evaluator: ToolIdentity
    proof: Literal["technical", "analyzer", "human"]


def _require_generation_inventory(policy: DomainAcceptancePolicy) -> None:
    """Verify that a component's raw rubric names a sealed rule inventory."""
    inventory = policy.profile_payload.get("generation_requirements")
    if not isinstance(inventory, tuple) or not inventory:
        raise ValueError("Component generation acceptance requires a sealed generation inventory")
    requirement_ids: list[str] = []
    for item in inventory:
        if not isinstance(item, Mapping):
            raise ValueError("Component generation inventory entries must be mappings")
        requirement_id = item.get("requirement_id")
        if not isinstance(requirement_id, str) or not requirement_id.strip():
            raise ValueError("Component generation inventory requirement IDs must be nonblank")
        requirement_ids.append(requirement_id)
    if len(set(requirement_ids)) != len(requirement_ids):
        raise ValueError("Component generation inventory requirement IDs must be unique")
    if not set(policy.required_requirement_ids) <= set(requirement_ids):
        raise ValueError("Component generation inventory omits accepted requirements")


class ComponentRequirementAllocation(StrictModel):
    """Explicit raw-generation responsibility for one production component."""

    component_id: str = Field(min_length=1)
    requirement_ids: tuple[str, ...] = Field(min_length=1)
    generation_acceptance: DomainAcceptancePolicy | None = None

    @model_validator(mode="after")
    def _validate_component_requirements(self) -> "ComponentRequirementAllocation":
        if any(not item.strip() for item in self.requirement_ids):
            raise ValueError("Component allocation requirement IDs must be nonblank")
        if len(set(self.requirement_ids)) != len(self.requirement_ids):
            raise ValueError("Component allocation requirement IDs must be unique")
        if self.generation_acceptance is not None:
            _require_generation_inventory(self.generation_acceptance)
            if not set(self.generation_acceptance.required_requirement_ids) <= set(
                self.requirement_ids
            ):
                raise ValueError(
                    "Component generation acceptance requirements must be a subset of the component allocation"
                )
        return self


class ProductionRequirementAllocation(StrictModel):
    """Immutable allocation from a parent Shot acceptance profile to production work."""

    allocation_id: str = Field(min_length=1)
    parent_shot_id: str = Field(min_length=1)
    parent_shot_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    task_id: str = Field(min_length=1)
    parent_acceptance_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    parent_requirement_ids: tuple[str, ...] = Field(min_length=1)
    components: tuple[ComponentRequirementAllocation, ...] = ()
    assembly_requirement_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _validate_requirement_coverage(self) -> "ProductionRequirementAllocation":
        parent_ids = self.parent_requirement_ids
        if any(not item.strip() for item in parent_ids):
            raise ValueError("Production allocation parent requirement IDs must be nonblank")
        if len(set(parent_ids)) != len(parent_ids):
            raise ValueError("Production allocation parent requirement IDs must be unique")
        component_ids = tuple(item.component_id for item in self.components)
        if len(set(component_ids)) != len(component_ids):
            raise ValueError("Production allocation component IDs must be unique")
        if any(not item.strip() for item in self.assembly_requirement_ids):
            raise ValueError("Production allocation assembly requirement IDs must be nonblank")
        if len(set(self.assembly_requirement_ids)) != len(self.assembly_requirement_ids):
            raise ValueError("Production allocation assembly requirement IDs must be unique")

        parent_id_set = set(parent_ids)
        component_requirement_ids = {
            requirement_id
            for component in self.components
            for requirement_id in component.requirement_ids
        }
        assembly_id_set = set(self.assembly_requirement_ids)
        if not component_requirement_ids <= parent_id_set:
            raise ValueError("Production allocation component requirements must be parent requirements")
        if not assembly_id_set <= parent_id_set:
            raise ValueError("Production allocation assembly requirements must be parent requirements")
        if component_requirement_ids | assembly_id_set != parent_id_set:
            raise ValueError("Production allocation must cover every parent requirement")
        return self

    @property
    def allocation_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))


class DomainAcceptanceQaPolicyMixin:
    """Pydantic mixin that keeps the generic QA model domain-neutral."""

    domain_acceptance: DomainAcceptancePolicy | None = None
    final_output: FinalOutputContract | None = None
    generation_acceptance: DomainAcceptancePolicy | None = None
    generation_evaluation_authorities: tuple[GenerationEvaluationAuthority, ...] = ()
    production_allocations: tuple[ProductionRequirementAllocation, ...] = ()
    production_source_evidence: tuple[SourceUseEvidence, ...] = ()

    def selected_generation_acceptance(self) -> DomainAcceptancePolicy | None:
        """Select the generation rubric without replacing final domain acceptance.

        Older combined policies remain exact-readable; a whole-output rubric
        without a sealed generation inventory is never implicitly projected.
        """
        if self.generation_acceptance is not None:
            return self.generation_acceptance
        if (self.domain_acceptance is not None
                and self.domain_acceptance.profile_payload.get("generation_requirements")):
            return self.domain_acceptance
        return None

    def require_production_allocation(
        self,
        *,
        allocation_hash: str,
        parent_shot_id: str,
        parent_shot_content_hash: str,
        task_id: str,
    ) -> ProductionRequirementAllocation:
        for allocation in self.production_allocations:
            if allocation.allocation_hash != allocation_hash:
                continue
            if (
                allocation.parent_shot_id != parent_shot_id
                or allocation.parent_shot_content_hash != parent_shot_content_hash
                or allocation.task_id != task_id
            ):
                raise ValueError("Production allocation does not match the requested parent identity")
            return allocation
        raise ValueError("Production allocation was not found")

    def selected_component_generation_acceptance(
        self,
        *,
        allocation_hash: str,
        component_id: str,
        parent_shot_id: str,
        parent_shot_content_hash: str,
        task_id: str,
    ) -> DomainAcceptancePolicy | None:
        allocation = self.require_production_allocation(
            allocation_hash=allocation_hash,
            parent_shot_id=parent_shot_id,
            parent_shot_content_hash=parent_shot_content_hash,
            task_id=task_id,
        )
        for component in allocation.components:
            if component.component_id == component_id:
                return component.generation_acceptance
        raise ValueError("Production allocation component was not found")

    @model_validator(mode="after")
    def _validate_domain_acceptance_policy(self):
        if self.final_output is not None and (
            self.semantic_requirement != "required"
            or QaLayer.SEMANTIC not in self.required_layers
        ):
            raise ValueError("Final-output contract requires the semantic layer and authority")
        if any(item.evaluator not in self.semantic_authorities for item in self.generation_evaluation_authorities):
            raise ValueError("generation proof authority must be a policy-selected evaluator")
        if (self.generation_acceptance is not None
                and not self.generation_acceptance.profile_payload.get("generation_requirements")):
            raise ValueError("Generation acceptance requires a sealed generation inventory")
        allocation_ids = tuple(item.allocation_id for item in self.production_allocations)
        if len(set(allocation_ids)) != len(allocation_ids):
            raise ValueError("Production allocation IDs must be unique")
        source_evidence_ids = tuple(item.evidence_id for item in self.production_source_evidence)
        if len(set(source_evidence_ids)) != len(source_evidence_ids):
            raise ValueError("Production source-use evidence IDs must be unique")
        parent_acceptance = (
            self.domain_acceptance
            if self.domain_acceptance is not None
            else self.selected_generation_acceptance()
        )
        if self.production_allocations and parent_acceptance is None:
            raise ValueError("Production allocations require a current acceptance policy")
        if self.production_source_evidence and parent_acceptance is None:
            raise ValueError("Production source-use evidence requires a current acceptance policy")
        if parent_acceptance is not None:
            for allocation in self.production_allocations:
                if allocation.parent_acceptance_hash != parent_acceptance.profile_content_hash:
                    raise ValueError("Production allocation acceptance hash is stale")
                if allocation.parent_requirement_ids != parent_acceptance.required_requirement_ids:
                    raise ValueError("Production allocation parent requirements are stale")
            for evidence in self.production_source_evidence:
                require_source_use_evidence_authority(self, evidence)
                if evidence.acceptance_profile_hash != parent_acceptance.profile_content_hash:
                    raise ValueError("Production source-use evidence acceptance hash is stale")
                if not {
                    requirement_id for requirement_id, _ in evidence.observations
                } <= set(parent_acceptance.required_requirement_ids):
                    raise ValueError("Production source-use evidence has unaccepted requirements")
        if self.domain_acceptance is None and self.generation_acceptance is None:
            return self
        if self.semantic_requirement != "required":
            raise ValueError("Domain acceptance requires semantic QA")
        if QaLayer.SEMANTIC not in self.required_layers:
            raise ValueError("Domain acceptance requires the semantic layer")
        return self

    @model_serializer(mode="wrap")
    def _serialize_optional_domain_acceptance(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.domain_acceptance is None:
            data.pop("domain_acceptance", None)
        if self.final_output is None:
            data.pop("final_output", None)
        if self.generation_acceptance is None:
            data.pop("generation_acceptance", None)
        if data.get("caption_policy") is None:
            data.pop("caption_policy", None)
        if not data.get("generation_evaluation_authorities"):
            data.pop("generation_evaluation_authorities", None)
        if not data.get("production_allocations"):
            data.pop("production_allocations", None)
        if not data.get("production_source_evidence"):
            data.pop("production_source_evidence", None)
        return data
