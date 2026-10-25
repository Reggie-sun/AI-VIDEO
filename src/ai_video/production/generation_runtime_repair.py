"""Immutable authorization for one bounded runtime or paid no-effect recovery.

A runtime repair is not a quality intervention. It authorizes one exact
strategy after a diagnosed runtime failure, or one paid no-effect retarget
after canonical reconciliation proves a pre-transport failure. The committer
marks the grant consumed in the same atomic write as the replacement submit
intent, so the same evidence cannot authorize another attempt.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import Field, model_serializer, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity

_SHA256 = r"^[0-9a-f]{64}$"

MAX_RUNTIME_REPAIRS_PER_SHOT = 2

RUNTIME_REPAIR_ARTIFACT_PREFIX = "state/video-generation/runtime-repair"


def runtime_repair_artifact_path(content_hash: str) -> Path:
    return Path(f"{RUNTIME_REPAIR_ARTIFACT_PREFIX}/{content_hash}.json")


class LocalRuntimeRepairExtension(StrictModel):
    """Explicit third through sixth ceiling for one exact local task/Shot failure."""

    task_id: str = Field(min_length=1)
    shot_id: str = Field(min_length=1)
    failed_binding_hash: str = Field(pattern=_SHA256)
    expected_manifest_revision: int = Field(strict=True, ge=0)
    ceiling: Literal[3, 4, 5, 6] = 3


class PaidNoEffectRetarget(StrictModel):
    """Explicit replacement strategy after one exact paid no-effect rejection."""

    submit_receipt_fingerprint: str = Field(pattern=_SHA256)
    target_scope_hash: str = Field(pattern=_SHA256)


class PaidNoEffectRepairExtension(StrictModel):
    """Explicit bounded paid no-effect repair ceiling for one exact task and Shot."""

    task_id: str = Field(min_length=1)
    shot_id: str = Field(min_length=1)
    failed_binding_hash: str = Field(pattern=_SHA256)
    expected_manifest_revision: int = Field(strict=True, ge=0)
    ceiling: Literal[3, 4] = 3
    authorization_receipt_id: str = Field(min_length=1)


class PaidKnownFailureRetarget(StrictModel):
    """Explicit image-input retarget after one accepted task is observed FAILED."""

    paid_submit_receipt_fingerprint: str = Field(pattern=_SHA256)
    failed_observation_fingerprint: str = Field(pattern=_SHA256)
    target_scope_hash: str = Field(pattern=_SHA256)


class PaidCrossProviderNoEffectRetarget(StrictModel):
    """Exact cross-provider scope after a canonical paid no-effect rejection."""

    submit_receipt_fingerprint: str = Field(pattern=_SHA256)
    source_scope_hash: str = Field(pattern=_SHA256)
    source_provider_name: str = Field(min_length=1)
    source_requirement_hash: str = Field(pattern=_SHA256)
    target_scope_hash: str = Field(pattern=_SHA256)
    target_provider_name: str = Field(min_length=1)
    target_requirement_hash: str = Field(pattern=_SHA256)
    output_requirement_id: str = Field(min_length=1)
    source_resolution_label: Literal["480p"]
    target_resolution_label: Literal["768P"]


class RuntimeRepairAuthorization(StrictModel):
    """One-use authorization to re-execute after a repaired runtime failure.

    It is not a quality verdict, not a retry permit for unknown outcomes, and
    not candidate activation.  The committer is the only writer of this
    receipt.
    """

    schema_version: Literal[
        "runtime-repair/1",
        "runtime-repair/2",
        "runtime-repair/3",
        "runtime-repair/4",
        "runtime-repair/5",
        "runtime-repair/6",
    ] = "runtime-repair/1"
    attempt_id: str = Field(min_length=1)
    evidence_hash: str = Field(pattern=_SHA256)
    repair_basis: str = Field(min_length=1)
    actor: ActorIdentity
    expected_manifest_revision: int = Field(strict=True, ge=0)
    content_hash: str = Field(pattern=_SHA256)
    local_extension: LocalRuntimeRepairExtension | None = None
    paid_no_effect_retarget: PaidNoEffectRetarget | None = None
    paid_known_failure_retarget: PaidKnownFailureRetarget | None = None
    paid_cross_provider_no_effect_retarget: PaidCrossProviderNoEffectRetarget | None = None
    paid_no_effect_extension: PaidNoEffectRepairExtension | None = None

    @model_serializer(mode="wrap")
    def _serialize_version(self, handler):
        result = handler(self)
        if self.schema_version == "runtime-repair/1":
            result.pop("local_extension", None)
        if self.schema_version not in {"runtime-repair/3", "runtime-repair/6"}:
            result.pop("paid_no_effect_retarget", None)
        if self.schema_version != "runtime-repair/4":
            result.pop("paid_known_failure_retarget", None)
        if self.schema_version != "runtime-repair/5":
            result.pop("paid_cross_provider_no_effect_retarget", None)
        if self.schema_version != "runtime-repair/6":
            result.pop("paid_no_effect_extension", None)
        return result

    @model_validator(mode="after")
    def _exact_runtime_repair(self) -> "RuntimeRepairAuthorization":
        if (self.schema_version == "runtime-repair/2") != (self.local_extension is not None):
            raise ValueError("runtime repair version and local extension do not match")
        if (self.schema_version in {"runtime-repair/3", "runtime-repair/6"}) != (
            self.paid_no_effect_retarget is not None
        ):
            raise ValueError("runtime repair version and paid retarget do not match")
        if (self.schema_version == "runtime-repair/4") != (self.paid_known_failure_retarget is not None):
            raise ValueError("runtime repair version and paid known-failure retarget do not match")
        if (self.schema_version == "runtime-repair/5") != (
            self.paid_cross_provider_no_effect_retarget is not None
        ):
            raise ValueError("runtime repair version and cross-provider no-effect retarget do not match")
        if (self.schema_version == "runtime-repair/6") != (
            self.paid_no_effect_extension is not None
        ):
            raise ValueError("runtime repair version and paid no-effect extension do not match")
        if (self.local_extension is not None and self.expected_manifest_revision
                != self.local_extension.expected_manifest_revision + 1):
            raise ValueError("runtime repair extension revision is invalid")
        if (self.paid_no_effect_extension is not None
                and self.expected_manifest_revision
                    != self.paid_no_effect_extension.expected_manifest_revision + 1):
            raise ValueError("paid no-effect repair extension revision is invalid")
        if self.content_hash != canonical_sha256(self.model_dump(mode="json")):
            raise ValueError("runtime repair authorization content hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "RuntimeRepairAuthorization":
        data = dict(values)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(provisional.model_dump(mode="json"))
        return cls(**data)


@dataclass(frozen=True)
class RuntimeRepairGrant:
    """Manifest-registered authorization paired with its consumption state.

    The immutable receipt never carries lifecycle state; ``consumed`` lives only
    on the manifest pointer so one-use semantics stay with the committer.
    """

    authorization: RuntimeRepairAuthorization
    consumed: bool


def is_paid_no_effect_repair_grant_for_evidence(
    grant, evidence, *, require_unconsumed: bool = True,
) -> bool:
    """Match an exact paid no-effect grant, requiring it open by default."""

    authorization = grant.authorization
    extension = authorization.paid_no_effect_extension
    return (
        (not require_unconsumed or not grant.consumed)
        and authorization.schema_version in {"runtime-repair/3", "runtime-repair/6"}
        and authorization.paid_no_effect_retarget is not None
        and authorization.attempt_id == evidence.attempt_id
        and authorization.evidence_hash == evidence.evidence_hash
        and evidence.outcome == "not_submitted"
        and (authorization.schema_version != "runtime-repair/6" or (
            extension is not None
            and extension.task_id == evidence.task_id
            and extension.shot_id == evidence.shot_id
        ))
    )


def effective_latest_generation_evidence(evidence, runtime_repairs=()):
    """Keep submitted history authoritative unless its exact no-effect repair is open."""

    matching = tuple(evidence)
    if not matching:
        return None
    latest = matching[-1]
    if latest.outcome == "not_submitted" and any(
        is_paid_no_effect_repair_grant_for_evidence(grant, latest)
        for grant in runtime_repairs
    ):
        return latest
    submitted = tuple(item for item in matching if item.outcome != "not_submitted")
    return submitted[-1] if submitted else latest


def retarget_preserves_strategy(old, target):
    """Recovery freezes intent/QA/audio; a provider switch also freezes geometry."""
    previous = next(v for v in old.capabilities.variants if v.capability_id == old.capability_id)
    current = next(v for v in target.capabilities.variants if v.capability_id == target.capability_id)
    geometry_fields = ({"width", "height"}
        if old.capabilities.provider_name == target.capabilities.provider_name else set())
    return (previous.mode == current.mode
        and previous.execution_kind.value == current.execution_kind.value == "remote"
        and previous.billing_kind.value == current.billing_kind.value == "metered"
        and old.recipe.model_dump(mode="json", exclude={"profile_sha256", "compiler_hash", "comparison"})
            == target.recipe.model_dump(mode="json", exclude={"profile_sha256", "compiler_hash", "comparison"})
        and old.output_requirement.model_dump(mode="json", exclude=geometry_fields)
            == target.output_requirement.model_dump(mode="json", exclude=geometry_fields)
        and old.final_output_goal == target.final_output_goal
        and old.voice_route == target.voice_route)


def paid_failure_retarget_preserves_strategy(old, target):
    """Allow only the same remote/metered model to switch T2V input to I2V."""
    from ai_video.production.video import VideoGenerationMode

    previous = next(v for v in old.capabilities.variants if v.capability_id == old.capability_id)
    current = next(v for v in target.capabilities.variants if v.capability_id == target.capability_id)

    def requirement_contract(recipe):
        contract = []
        for expression in recipe.expressions:
            data = expression.model_dump(mode="json")
            data.pop("native_text", None)
            semantics = data.get("semantics")
            if semantics is not None:
                for reference in semantics.get("source_refs", ()):
                    reference.pop("source_hash", None)
                hard_basis = semantics.get("hard_basis")
                if hard_basis is not None:
                    hard_basis.pop("source_hash", None)
                for reference in semantics.get("derived_from", ()):
                    reference.pop("source_hash", None)
            contract.append(data)
        return tuple(contract)

    old_acceptance = old.recipe.acceptance_policy
    target_acceptance = target.recipe.acceptance_policy
    return (
        old.capabilities.provider_name == target.capabilities.provider_name
        and previous.model_id == current.model_id
        and previous.provider_kind == current.provider_kind
        and previous.mode is VideoGenerationMode.TEXT_TO_VIDEO
        and current.mode is VideoGenerationMode.IMAGE_TO_VIDEO
        and previous.execution_kind.value == current.execution_kind.value == "remote"
        and previous.billing_kind.value == current.billing_kind.value == "metered"
        and old.provider_profile.profile_id == target.provider_profile.profile_id
        and old.provider_profile.profile_version == target.provider_profile.profile_version
        and old.compiler_contract.compiler_hash == target.compiler_contract.compiler_hash
        and old.recipe.seed == target.recipe.seed
        and old.recipe.editorial_operations == target.recipe.editorial_operations
        and requirement_contract(old.recipe) == requirement_contract(target.recipe)
        and old_acceptance.domain_id == target_acceptance.domain_id
        and old_acceptance.measurement_contract_version
            == target_acceptance.measurement_contract_version
        and old_acceptance.required_requirement_ids
            == target_acceptance.required_requirement_ids
        and old.output_requirement == target.output_requirement
        and old.final_output_goal == target.final_output_goal
        and old.voice_route == target.voice_route
    )


def cross_provider_candidate_preserves_strategy(old, target, adaptation):
    """Permit only the explicit Seedance-to-H3 candidate adaptation.

    Provider/profile/compiler identity may change.  The frozen recipe, source
    bindings, shot semantics, final goal, voice route, duration, frame rate,
    container and native audio remain exact.  The only allowed requirement
    delta is geometry; H3's declared output contract is nominal 4s, adaptive
    768P at 24fps with native audio.
    """
    from ai_video.production.video import VideoGenerationMode
    from ai_video.production.video_contracts import VideoFlexibleOutputRequirement

    def selected_variant(candidate):
        return next((v for v in candidate.capabilities.variants
                     if v.capability_id == candidate.capability_id), None)

    def output_contract(candidate):
        output = candidate.output_requirement
        if not isinstance(output, VideoFlexibleOutputRequirement):
            return None
        return output.model_dump(mode="json")

    def replace_requirement_observable(value):
        if not isinstance(value, dict):
            return False
        expressions = value.get("expressions")
        if not isinstance(expressions, list | tuple):
            return False
        matches = [item for item in expressions
                   if isinstance(item, dict)
                   and item.get("requirement_id") == adaptation.output_requirement_id]
        if len(matches) != 1:
            return False
        observable = matches[0].get("observable")
        if (not isinstance(observable, str)
                or observable.count(adaptation.source_resolution_label) != 1):
            return False
        matches[0]["observable"] = observable.replace(
            adaptation.source_resolution_label,
            adaptation.target_resolution_label,
            1,
        )
        return True

    def replace_policy_observable(policy_payload):
        if not isinstance(policy_payload, dict):
            return False
        inventory = policy_payload.get("generation_requirements")
        if not isinstance(inventory, list | tuple):
            return False
        matches = [item for item in inventory
                   if isinstance(item, dict)
                   and item.get("requirement_id") == adaptation.output_requirement_id]
        if len(matches) != 1:
            return False
        observable = matches[0].get("observable")
        if (not isinstance(observable, str)
                or observable.count(adaptation.source_resolution_label) != 1):
            return False
        matches[0]["observable"] = observable.replace(
            adaptation.source_resolution_label,
            adaptation.target_resolution_label,
            1,
        )
        return True

    def transformed_acceptance_policy(source, current):
        source_data = source.model_dump(mode="json")
        current_data = current.model_dump(mode="json")
        source_payload = source_data.get("profile_payload")
        current_payload = current_data.get("profile_payload")
        source_hash = source_data.get("profile_content_hash")
        current_hash = current_data.get("profile_content_hash")
        if not replace_policy_observable(source_payload):
            return False
        source_payload.pop("content_hash", None)
        current_payload.pop("content_hash", None)
        if source_payload != current_payload:
            return False
        return (
            {key: value for key, value in source_data.items()
             if key not in {"profile_content_hash", "profile_payload"}}
            == {key: value for key, value in current_data.items()
                if key not in {"profile_content_hash", "profile_payload"}}
            and canonical_sha256(source_payload) == current_hash
            and source_hash != current_hash
        )

    def transformed_final_goal(source, current):
        if source is None or current is None:
            return source is current
        if source == current:
            return True
        source_data = source.model_dump(mode="json")
        current_data = current.model_dump(mode="json")
        source_requirements = source_data.get("requirements")
        current_requirements = current_data.get("requirements")
        if not isinstance(source_requirements, list) or not isinstance(current_requirements, list):
            return False
        if source_data.get("goal_version") == current_data.get("goal_version"):
            return False
        source_matches = [item for item in source_requirements
                          if item.get("requirement_id") == adaptation.output_requirement_id]
        current_matches = [item for item in current_requirements
                           if item.get("requirement_id") == adaptation.output_requirement_id]
        if len(source_matches) != 1 or len(current_matches) != 1:
            return False
        source_observable = source_matches[0].get("observable")
        if (not isinstance(source_observable, str)
                or source_observable.count(adaptation.source_resolution_label) != 1):
            return False
        source_matches[0]["observable"] = source_observable.replace(
            adaptation.source_resolution_label,
            adaptation.target_resolution_label,
            1,
        )
        source_data["goal_version"] = current_data["goal_version"]
        return source_data == current_data

    try:
        previous, current = selected_variant(old), selected_variant(target)
        previous_output = output_contract(old)
        current_output = output_contract(target)
        if previous is None or current is None or previous_output is None or current_output is None:
            return False
        allowed_output_fields = {
            "timing_mode", "dimension_mode", "width", "height",
            "resolution_label", "ratio",
        }
        previous_frozen = {k: v for k, v in previous_output.items() if k not in allowed_output_fields}
        current_frozen = {k: v for k, v in current_output.items() if k not in allowed_output_fields}
        source_recipe = old.recipe.model_dump(mode="json")
        target_recipe = target.recipe.model_dump(mode="json")
        if not replace_requirement_observable(source_recipe):
            return False
        if not transformed_acceptance_policy(
            old.recipe.acceptance_policy, target.recipe.acceptance_policy
        ):
            return False
        source_recipe["acceptance_policy"] = target_recipe["acceptance_policy"]
        source_recipe["profile_sha256"] = target_recipe["profile_sha256"]
        source_recipe["compiler_hash"] = target_recipe["compiler_hash"]
        source_recipe["requirement_hash"] = target_recipe["requirement_hash"]
        source_recipe["rubric_hash"] = target_recipe["rubric_hash"]
        if source_recipe != target_recipe:
            return False
        goal_matches = transformed_final_goal(old.final_output_goal, target.final_output_goal)
        return (
            old.capabilities.provider_name != target.capabilities.provider_name
            and old.capabilities.provider_name == "seedance"
            and target.capabilities.provider_name == "metaso_h3"
            and previous.provider_kind == "volcengine_ark_seedance"
            and current.provider_kind == "metaso_h3"
            and current.model_id == "MiniMax-H3"
            and target.provider_profile.profile_id == "metaso_h3"
            and target.provider_profile.profile_version == "metaso-h3-ref2va-v1"
            and current.capability_id == "metaso-h3-fl2va-v1"
            and previous.mode is VideoGenerationMode.IMAGE_TO_VIDEO
            and current.mode is VideoGenerationMode.IMAGE_TO_VIDEO
            and previous.execution_kind.value == current.execution_kind.value == "remote"
            and previous.billing_kind.value == current.billing_kind.value == "metered"
            and previous_frozen == current_frozen
            and previous_output["timing_mode"] == current_output["timing_mode"] == "nominal_seconds"
            and previous_output["duration_seconds"] == current_output["duration_seconds"] == 4
            and previous_output["dimension_mode"] == "exact"
            and previous_output["resolution_label"] == adaptation.source_resolution_label
            and previous_output["width"] is not None
            and previous_output["height"] is not None
            and current_output["dimension_mode"] == "adaptive"
            and current_output["width"] is None
            and current_output["height"] is None
            and current_output["resolution_label"] == adaptation.target_resolution_label
            and current_output["ratio"] == "adaptive"
            and previous_output["fps"] == current_output["fps"] == 24
            and previous_output["native_audio"] is current_output["native_audio"] is True
            and previous_output["container"] == current_output["container"] == "mp4"
            and previous_output["mime_type"] == current_output["mime_type"] == "video/mp4"
            and goal_matches
            and old.voice_route == target.voice_route
        )
    except (AttributeError, KeyError, StopIteration, TypeError, ValueError):
        return False


def cross_provider_no_effect_retarget_preserves_strategy(
    old, target, source_requirement, target_requirement, adaptation
):
    """Bind the exact prepared candidates to a neutral-preserving requirement pair."""
    try:
        from ai_video.production.video_requirement import ProviderNeutralVideoRequirement

        source_requirement = ProviderNeutralVideoRequirement.model_validate(
            source_requirement.model_dump(mode="python")
        )
        target_requirement = ProviderNeutralVideoRequirement.model_validate(
            target_requirement.model_dump(mode="python")
        )
        source = source_requirement.model_dump(mode="json")
        current = target_requirement.model_dump(mode="json")
        source_output = source.get("output_need")
        target_output = current.get("output_need")
        old_candidate_output = old.output_requirement.model_dump(mode="json")
        if not isinstance(source_output, dict) or not isinstance(target_output, dict):
            return False
        if (
            source_output.get("geometry_policy") != "exact"
            or source_output.get("width") != old_candidate_output.get("width")
            or source_output.get("height") != old_candidate_output.get("height")
            or target_output.get("geometry_policy") != "adaptive"
            or target_output.get("width") is not None
            or target_output.get("height") is not None
            or source_output.get("aspect_ratio") != target_output.get("aspect_ratio")
        ):
            return False
        source_shot = source.get("target_shot")
        target_shot = current.get("target_shot")
        if not isinstance(source_shot, dict) or not isinstance(target_shot, dict):
            return False
        if (
            source_shot.get("artifact_id") != target_shot.get("artifact_id")
            or source_shot.get("shot_id") != target_shot.get("shot_id")
            or target_shot.get("revision") != source_shot.get("revision", -2) + 1
            or source_shot.get("content_hash") == target_shot.get("content_hash")
        ):
            return False
        source_assets = source.get("asset_evidence")
        target_assets = current.get("asset_evidence")
        if (not isinstance(source_assets, list) or not isinstance(target_assets, list)
                or len(source_assets) != len(target_assets)):
            return False
        for source_asset, target_asset in zip(source_assets, target_assets, strict=True):
            if not isinstance(source_asset, dict) or not isinstance(target_asset, dict):
                return False
            source_owner_hash = source_asset.get("canonical_owner_content_hash")
            target_owner_hash = target_asset.get("canonical_owner_content_hash")
            if source_owner_hash != target_owner_hash:
                if (
                    source_asset.get("role") != "first_frame"
                    or target_asset.get("role") != "first_frame"
                    or source_asset.get("canonical_owner_id") != source_shot.get("shot_id")
                    or target_asset.get("canonical_owner_id") != target_shot.get("shot_id")
                    or source_owner_hash != source_shot.get("content_hash")
                    or target_owner_hash != target_shot.get("content_hash")
                ):
                    return False
                target_asset["canonical_owner_content_hash"] = source_owner_hash
        for payload in (source, current):
            payload.pop("requirement_id", None)
            payload.pop("requirement_hash", None)
            # These identities are recomputed by the canonical Planner when the
            # exact output geometry and authoring revision change. All source
            # semantics that feed them remain compared below.
            for field in (
                "source_request_content_hash",
                "intent_evidence_hash",
                "generation_intent_hash",
            ):
                payload.pop(field, None)
            output = payload.get("output_need")
            if not isinstance(output, dict):
                return False
            for field in ("geometry_policy", "width", "height"):
                output.pop(field, None)
            shot = payload.get("target_shot")
            if not isinstance(shot, dict):
                return False
            for field in ("revision", "content_hash", "creation_receipt_id", "source_provenance"):
                shot.pop(field, None)
        return (
            old.recipe.requirement_hash == source_requirement.requirement_hash
            and target.recipe.requirement_hash == target_requirement.requirement_hash
            and source == current
            and cross_provider_candidate_preserves_strategy(old, target, adaptation)
        )
    except (AttributeError, TypeError, ValueError):
        return False
