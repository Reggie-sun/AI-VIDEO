"""Immutable authorization for one bounded re-execution after a local runtime failure.

A runtime repair is not a quality intervention: it authorizes the exact same
provider/prompt/seed-scope strategy once the environmental runtime failure
(VRAM exhaustion, missing local runtime, interrupted worker, ...) has been
diagnosed and fixed by the runtime owner.  The decision engine consumes it only
while the Shot's latest evidence is exactly ``RUNTIME_FAILURE``; the committer
marks it consumed inside the same atomic write as the replacement submit
intent, so a repaired outcome can never be re-authorized from the same
evidence.
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


class PaidKnownFailureRetarget(StrictModel):
    """Explicit image-input retarget after one accepted task is observed FAILED."""

    paid_submit_receipt_fingerprint: str = Field(pattern=_SHA256)
    failed_observation_fingerprint: str = Field(pattern=_SHA256)
    target_scope_hash: str = Field(pattern=_SHA256)


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

    @model_serializer(mode="wrap")
    def _serialize_version(self, handler):
        result = handler(self)
        if self.schema_version == "runtime-repair/1":
            result.pop("local_extension", None)
        if self.schema_version != "runtime-repair/3":
            result.pop("paid_no_effect_retarget", None)
        if self.schema_version != "runtime-repair/4":
            result.pop("paid_known_failure_retarget", None)
        return result

    @model_validator(mode="after")
    def _exact_runtime_repair(self) -> "RuntimeRepairAuthorization":
        if (self.schema_version == "runtime-repair/2") != (self.local_extension is not None):
            raise ValueError("runtime repair version and local extension do not match")
        if (self.schema_version == "runtime-repair/3") != (self.paid_no_effect_retarget is not None):
            raise ValueError("runtime repair version and paid retarget do not match")
        if (self.schema_version == "runtime-repair/4") != (self.paid_known_failure_retarget is not None):
            raise ValueError("runtime repair version and paid known-failure retarget do not match")
        if (self.local_extension is not None and self.expected_manifest_revision
                != self.local_extension.expected_manifest_revision + 1):
            raise ValueError("runtime repair extension revision is invalid")
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


def retarget_preserves_strategy(old, target):
    """Model/profile recovery cannot edit frozen intent, acceptance or audio."""
    previous = next(v for v in old.capabilities.variants if v.capability_id == old.capability_id)
    current = next(v for v in target.capabilities.variants if v.capability_id == target.capability_id)
    return (old.capabilities.provider_name == target.capabilities.provider_name
        and previous.mode == current.mode
        and previous.execution_kind.value == current.execution_kind.value == "remote"
        and previous.billing_kind.value == current.billing_kind.value == "metered"
        and old.recipe.model_dump(mode="json", exclude={"profile_sha256", "compiler_hash", "comparison"})
            == target.recipe.model_dump(mode="json", exclude={"profile_sha256", "compiler_hash", "comparison"})
        and old.output_requirement.model_dump(mode="json", exclude={"width", "height"})
            == target.output_requirement.model_dump(mode="json", exclude={"width", "height"})
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
