"""Immutable execution binding for a selected generation decision.

The Router remains the selection owner.  This module only seals the exact
pure inputs, result, and compiled request that may cross into a Provider
effect boundary.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import hashlib
from typing import Literal

from pydantic import Field, PrivateAttr, model_validator

from ai_video.production._shot_router_contracts import (
    ContinuityProviderRouteBinding,
    ShotRoutingContext,
    VideoGenerationLifecycleEnvelope,
    VideoRoutingPolicy,
)
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.generation_decision import DecisionInputs, GenerationDecision
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import AssetType, VisualStrategy
from ai_video.production.shot_router import VideoGenerationResolver
from ai_video.production.video import ResolvedVideoGenerationRequest
from ai_video.production.video_requirement import VerifiedGenerationRequirementProjection


_SHA256 = r"^[0-9a-f]{64}$"
_QUALIFICATION_MINT_TOKEN = object()


def _json_safe(value):
    if isinstance(value, bytes):
        return {"bytes_sha256": hashlib.sha256(value).hexdigest()}
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return tuple(_json_safe(item) for item in value)
    return value


class GenerationDecisionExecutionBinding(StrictModel):
    """A replayable decision and the one compiled request it authorized."""

    schema_version: Literal["1"] = "1"
    projection: VerifiedGenerationRequirementProjection
    context: ShotRoutingContext
    policy: VideoRoutingPolicy
    lifecycle: VideoGenerationLifecycleEnvelope
    inputs: DecisionInputs
    decision: GenerationDecision
    continuity_routing: ContinuityProviderRouteBinding | None = None
    compiled_request: ResolvedVideoGenerationRequest
    binding_hash: str = Field(pattern=_SHA256)

    @staticmethod
    def _payload(values: dict[str, object]) -> dict[str, object]:
        return {
            "schema": "generation-decision-execution-binding/1",
            **{name: value for name, value in values.items() if name != "binding_hash"},
        }

    @model_validator(mode="after")
    def _validate_binding(self) -> "GenerationDecisionExecutionBinding":
        expected_hash = canonical_sha256(
            self._payload(self.model_dump(mode="json", exclude={"binding_hash"}))
        )
        if self.binding_hash != expected_hash:
            raise ValueError("generation execution binding hash is invalid")
        expected = VideoGenerationResolver().resolve_requirement(
            projection=self.projection,
            context=self.context,
            policy=self.policy,
            lifecycle=self.lifecycle,
            inputs=self.inputs,
            continuity_routing=self.continuity_routing,
        )
        if expected != self.decision:
            raise ValueError("generation execution decision is stale or altered")
        if (
            self.decision.disposition != "GENERATE_ONCE"
            or self.decision.selected_candidate_id is None
            or self.decision.routing is None
            or self.decision.routing.provider_bound_request is None
        ):
            raise ValueError("generation execution binding requires one submit decision")
        bound = self.decision.routing.provider_bound_request
        request = self.compiled_request
        selected = next(
            (item for item in self.inputs.candidates if item.candidate_id == self.decision.selected_candidate_id),
            None,
        )
        if selected is None or (
            request.generation_id != self.lifecycle.generation_id
            or request.output_asset_id != self.lifecycle.output_asset_id
            or request.requirement_hash != self.projection.requirement.requirement_hash
            or request.provider_bound_request_hash != bound.provider_bound_request_hash
            or request.provider_name != bound.provider_name
            or request.provider_kind != bound.provider_kind
            or request.model_id != bound.model_id
            or request.provider_profile != bound.provider_profile
            or request.capability_id != bound.capability_id
            or request.mode is not bound.mode
            or request.effective_output != bound.output_requirement
            or request.adapter_compiler_id != selected.compiler_contract.compiler_id
            or request.adapter_compiler_version != selected.compiler_contract.compiler_version
            or request.adapter_compiler_hash != selected.compiler_contract.compiler_hash
        ):
            raise ValueError("compiled request does not match the selected decision")
        recipe = bound.generation_recipe
        sealed = request.activation_scope.request if request.activation_scope else None
        if sealed is None:
            raise ValueError("production execution binding requires an activation scope")
        if recipe is not None:
            expected_seed = recipe.seed.value
            if request.effective_seed != expected_seed or sealed.seed != expected_seed:
                raise ValueError("compiled request seed does not match the selected recipe")
            if recipe.comparison is not None:
                from ai_video.production.generation_diagnosis import (
                    compiled_comparison_errors,
                )

                if compiled_comparison_errors(recipe.comparison, sealed):
                    raise ValueError("compiled request delta does not match the intervention")
        return self

    @classmethod
    def create(
        cls,
        *,
        projection: VerifiedGenerationRequirementProjection,
        context: ShotRoutingContext,
        policy: VideoRoutingPolicy,
        lifecycle: VideoGenerationLifecycleEnvelope,
        inputs: DecisionInputs,
        decision: GenerationDecision,
        compiled_request: ResolvedVideoGenerationRequest,
        continuity_routing: ContinuityProviderRouteBinding | None = None,
    ) -> "GenerationDecisionExecutionBinding":
        values: dict[str, object] = {
            "schema_version": "1",
            "projection": projection,
            "context": context,
            "policy": policy,
            "lifecycle": lifecycle,
            "inputs": inputs,
            "decision": decision,
            "continuity_routing": continuity_routing,
            "compiled_request": compiled_request,
        }
        provisional = cls.model_construct(**values, binding_hash="0" * 64)
        values["binding_hash"] = canonical_sha256(
            cls._payload(
                provisional.model_dump(mode="json", exclude={"binding_hash"})
            )
        )
        return cls.model_validate(values)

    def validate_request(self, request: ResolvedVideoGenerationRequest) -> None:
        if request != self.compiled_request:
            raise ValueError("generation execution request is stale or altered")

    def validate_current_project(self, project) -> None:
        """Bind a self-consistent decision to the currently loaded source bytes."""

        if self.inputs.policy.version != "3":
            raise ValueError("new execution requires final-output no-regression decision policy/3")
        if project.qa_policy is None:
            raise ValueError("generation execution requires a current QA policy")
        if any(candidate.final_output_goal != project.qa_policy.final_output
               for candidate in self.inputs.candidates):
            raise ValueError("generation final-output goal differs from the current QA owner")
        request = self.compiled_request
        scope = request.activation_scope
        if scope is None:
            raise ValueError("production execution binding requires an activation scope")
        sealed = scope.request
        if (
            sealed.base_project != project.manifest.active_project
            or sealed.base_registry != project.manifest.active_registry
            or sealed.base_dependency_graph != project.manifest.active_dependency_graph
            or sealed.target_shot_id != self.context.target_shot_id
            or sealed.target_shot_revision != self.context.target_shot_revision
            or sealed.target_shot_content_hash != self.context.target_shot_content_hash
            or sealed.target_asset_role != self.lifecycle.target_asset_role
        ):
            raise ValueError("generation execution binding has stale project lineage")
        shots = tuple(
            shot for shot in project.shots if shot.shot_id == sealed.target_shot_id
        )
        if len(shots) != 1:
            raise ValueError("generation execution target Shot is not current and unique")
        shot = shots[0]
        roles = tuple(
            role
            for role in shot.required_asset_roles
            if role.role == sealed.target_asset_role
        )
        if (
            shot.revision != sealed.target_shot_revision
            or shot.content_hash != sealed.target_shot_content_hash
            or shot.visual_strategy is not VisualStrategy.GENERATED_VIDEO
            or len(roles) != 1
            or roles[0].asset_ids
            or roles[0].allowed_asset_types != (AssetType.VIDEO,)
        ):
            raise ValueError("generation execution target Shot or role is stale")
        assets = {asset.asset_id: asset for asset in project.registry.assets}
        for binding in request.image_bindings:
            asset = assets.get(binding.asset_id)
            if (
                asset is None
                or asset.asset_type is not AssetType.IMAGE
                or asset.sha256 != binding.asset_sha256
                or asset.mime_type != binding.mime_type
                or asset.width != binding.width
                or asset.height != binding.height
                or (
                    binding.size_bytes is not None
                    and asset.size_bytes != binding.size_bytes
                )
                or binding.asset_id not in project.asset_paths
            ):
                raise ValueError("generation execution image reference is not current")
        for binding in request.media_bindings:
            asset = assets.get(binding.asset_id)
            if (
                asset is None
                or asset.sha256 != binding.asset_sha256
                or asset.mime_type != binding.mime_type
                or asset.size_bytes != binding.size_bytes
                or binding.asset_id not in project.asset_paths
            ):
                raise ValueError("generation execution media reference is not current")


class _QualificationExecutionBinding(StrictModel):
    """Private service proof for the two existing qualification callers."""

    schema_version: Literal["1"] = "1"
    qualification_kind: Literal["source_boundary", "m0"]
    request_input_hash: str = Field(pattern=_SHA256)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    closure_hash: str = Field(pattern=_SHA256)
    binding_hash: str = Field(pattern=_SHA256)
    _mint_token: object | None = PrivateAttr(default=None)

    @model_validator(mode="after")
    def _validate_binding(self) -> "_QualificationExecutionBinding":
        expected = canonical_sha256(
            {
                "schema": "qualification-execution-binding/1",
                **self.model_dump(mode="json", exclude={"binding_hash"}),
            }
        )
        if self.binding_hash != expected:
            raise ValueError("qualification execution binding hash is invalid")
        return self

    @classmethod
    def create(cls, *, qualification_kind: Literal["source_boundary", "m0"], request, closure) -> "_QualificationExecutionBinding":
        try:
            closure_payload = (
                closure.model_dump(mode="json")
                if hasattr(closure, "model_dump")
                else asdict(closure)
                if is_dataclass(closure)
                else None
            )
            if closure_payload is None:
                raise ValueError("qualification closure proof is not serializable")
            closure_hash = canonical_sha256(_json_safe(closure_payload))
            request_input_hash = request.request_input_hash
            resolved_generation_hash = request.resolved_generation_hash
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("qualification requires typed request and closure proof") from exc
        values = {
            "schema_version": "1",
            "qualification_kind": qualification_kind,
            "request_input_hash": request_input_hash,
            "resolved_generation_hash": resolved_generation_hash,
            "closure_hash": closure_hash,
        }
        values["binding_hash"] = canonical_sha256(
            {"schema": "qualification-execution-binding/1", **values}
        )
        return cls.model_validate(values)

    def validate_request(self, request) -> None:
        if (
            request.request_input_hash != self.request_input_hash
            or request.resolved_generation_hash != self.resolved_generation_hash
        ):
            raise ValueError("qualification execution request is stale or altered")

    def _consume_fresh_mint(self) -> bool:
        if self._mint_token is not _QUALIFICATION_MINT_TOKEN:
            return False
        self._mint_token = None
        return True


def _mint_qualification_execution_binding(
    *, qualification_kind: Literal["source_boundary", "m0"], request, proof
) -> _QualificationExecutionBinding:
    """Consume an owner-issued proof after its dedicated closure reopen.

    A preflight snapshot is data, not authority.  Only the concrete source or
    M0 owner may issue the one-use proof after reopening its own profile,
    compiler, stack, project and input closure.
    """

    if qualification_kind == "source_boundary":
        from ai_video.production.shot_continuity_source_qualification import (
            _SourceQualificationExecutionProof,
        )

        if type(proof) is not _SourceQualificationExecutionProof:
            raise ValueError("source qualification requires an owner-issued closure proof")
    else:
        from ai_video.production.shot_continuity_m0_caller import (
            _M0QualificationExecutionProof,
        )

        if type(proof) is not _M0QualificationExecutionProof:
            raise ValueError("M0 qualification requires an owner-issued closure proof")
    closure = proof._consume_for_binding(request)
    if any(
        not hasattr(request, field)
        for field in (
            "request_input_hash",
            "resolved_generation_hash",
            "execution_stack_hash",
            "capability_id",
            "effective_seed",
        )
    ):
        raise ValueError("qualification mint requires the exact reopened closure")
    binding = _QualificationExecutionBinding.create(
        qualification_kind=qualification_kind,
        request=request,
        closure=closure,
    )
    binding._mint_token = _QUALIFICATION_MINT_TOKEN
    return binding
