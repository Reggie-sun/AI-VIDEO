from __future__ import annotations

import base64
import binascii
import hashlib
import json
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel


_IDENTITY_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"
_SHA_OR_NONE_PATTERN = r"^(?:[0-9a-f]{64}|none)$"


class _ExecutionStackModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class StackComponentIdentity(_ExecutionStackModel):
    ordinal: int = Field(strict=True, ge=0)
    kind: Literal["checkpoint", "artifact", "lora"]
    component_id: str = Field(pattern=_IDENTITY_PATTERN)
    presence: Literal["present", "absent"] = "present"
    content_hash: str = Field(pattern=_SHA_OR_NONE_PATTERN)

    @model_validator(mode="after")
    def _validate_presence(self) -> "StackComponentIdentity":
        if self.presence == "absent" and self.content_hash != "none":
            raise ValueError("absent execution stack component must use content_hash=none")
        if self.presence == "present" and self.content_hash == "none":
            raise ValueError("present execution stack component requires a content hash")
        return self


class RuntimeSeal(_ExecutionStackModel):
    name: str = Field(pattern=_IDENTITY_PATTERN)
    version: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _reject_path_or_secret_material(self) -> "RuntimeSeal":
        if any(token in self.version for token in ("/", "\\", "api_key=", "secret=")):
            raise ValueError("runtime seal version cannot contain paths or secret material")
        return self


class ExecutionStackRuntimeReseal(_ExecutionStackModel):
    """One exact runtime identity replacement for a materialized stack reseal."""

    candidate_label: Literal["m0"]
    source_execution_stack_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    runtime_name: Literal["comfyui"]
    source_seal: RuntimeSeal
    target_seal: RuntimeSeal

    @model_validator(mode="after")
    def _validate_exact_replacement(self) -> "ExecutionStackRuntimeReseal":
        if (
            self.source_seal.name != self.runtime_name
            or self.target_seal.name != self.runtime_name
        ):
            raise ValueError("runtime reseal names must match the selected runtime")
        if (
            self.source_seal.version == self.target_seal.version
            or self.source_seal.content_hash == self.target_seal.content_hash
        ):
            raise ValueError("runtime reseal must replace both version and content identity")
        return self


class ExecutionStackMaterialization(_ExecutionStackModel):
    """Exact, candidate-neutral artifact hashes supplied by local preflight."""

    candidate_label: Literal["source", "m0", "m1"]
    profile_bytes: bytes = Field(min_length=1)
    compiler_bytes: bytes = Field(min_length=1)
    workflow_bytes: bytes = Field(min_length=1)
    profile_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    compiler_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    workflow_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_artifact_hashes(self) -> "ExecutionStackMaterialization":
        expected = (
            hashlib.sha256(self.profile_bytes).hexdigest(),
            hashlib.sha256(self.compiler_bytes).hexdigest(),
            hashlib.sha256(self.workflow_bytes).hexdigest(),
        )
        if (self.profile_hash, self.compiler_hash, self.workflow_hash) != expected:
            raise ValueError("execution stack materialization hashes do not match artifact bytes")
        return self

    @classmethod
    def from_bytes(
        cls,
        *,
        candidate_label: Literal["source", "m0", "m1"],
        profile_bytes: bytes,
        compiler_bytes: bytes,
        workflow_bytes: bytes,
    ) -> "ExecutionStackMaterialization":
        return cls(
            candidate_label=candidate_label,
            profile_bytes=profile_bytes,
            compiler_bytes=compiler_bytes,
            workflow_bytes=workflow_bytes,
            profile_hash=hashlib.sha256(profile_bytes).hexdigest(),
            compiler_hash=hashlib.sha256(compiler_bytes).hexdigest(),
            workflow_hash=hashlib.sha256(workflow_bytes).hexdigest(),
        )

    def profile_runtime_seals(self) -> tuple[RuntimeSeal, ...]:
        """Reopen runtime seals from the exact hashed profile source envelope."""

        try:
            envelope = json.loads(self.profile_bytes)
            if not isinstance(envelope, dict) or envelope.get("schema_version") != "1":
                raise ValueError("profile source envelope is invalid")
            profile_bytes = base64.b64decode(
                envelope["profile_bytes_base64"],
                validate=True,
            )
            profile = json.loads(profile_bytes)
            runtime_seals = profile["runtime_seals"]
            if not isinstance(runtime_seals, list):
                raise ValueError("profile runtime seals are invalid")
            return tuple(RuntimeSeal.model_validate(item) for item in runtime_seals)
        except (
            binascii.Error,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "execution stack profile runtime seals could not be reopened"
            ) from exc


class GenerationExecutionStackIdentity(_ExecutionStackModel):
    schema_version: Literal["1"] = "1"
    status: Literal["qualification_candidate"] = "qualification_candidate"
    materialization_status: Literal["unmaterialized", "materialized"]
    candidate_id: str = Field(pattern=_IDENTITY_PATTERN)
    contract_version: str = Field(pattern=_IDENTITY_PATTERN)
    provider_kind: str = Field(pattern=_IDENTITY_PATTERN)
    deployment_identity: str = Field(pattern=_IDENTITY_PATTERN)
    model_id: str = Field(pattern=_IDENTITY_PATTERN)
    capability_id: str = Field(pattern=_IDENTITY_PATTERN)
    profile_hash: str = Field(pattern=_SHA_OR_NONE_PATTERN)
    compiler_hash: str = Field(pattern=_SHA_OR_NONE_PATTERN)
    workflow_hash: str = Field(pattern=_SHA_OR_NONE_PATTERN)
    components: tuple[StackComponentIdentity, ...] = Field(min_length=1)
    sampler_identity: str = Field(pattern=_IDENTITY_PATTERN)
    scheduler_identity: str = Field(pattern=_IDENTITY_PATTERN)
    runtime_seals: tuple[RuntimeSeal, ...] = Field(min_length=1)
    output_contract_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_stack_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_canonical_identity(self) -> "GenerationExecutionStackIdentity":
        if self.materialization_status == "unmaterialized" and (
            self.profile_hash != "none"
            or self.compiler_hash != "none"
            or self.workflow_hash != "none"
        ):
            raise ValueError(
                "unmaterialized execution stack must use canonical empty profile/compiler/workflow identities"
            )
        if self.materialization_status == "materialized" and (
            self.profile_hash == "none" or self.compiler_hash == "none"
        ):
            raise ValueError(
                "materialized execution stack requires profile and compiler hashes"
            )
        ordinals = tuple(item.ordinal for item in self.components)
        if ordinals != tuple(range(len(self.components))):
            raise ValueError("execution stack component ordinals must be contiguous")
        component_keys = tuple(
            (item.kind, item.component_id, item.presence, item.content_hash)
            for item in self.components
        )
        if len(component_keys) != len(set(component_keys)):
            raise ValueError("execution stack components must be unique")
        runtime_keys = tuple(
            (item.name, item.version, item.content_hash) for item in self.runtime_seals
        )
        if runtime_keys != tuple(sorted(runtime_keys)):
            raise ValueError("runtime seals must be canonically ordered")
        if len(runtime_keys) != len(set(runtime_keys)):
            raise ValueError("runtime seals must be unique")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"execution_stack_hash"})
        )
        if self.execution_stack_hash != expected:
            raise ValueError("execution_stack_hash does not match stack identity")
        return self

    @classmethod
    def create(cls, **values: object) -> "GenerationExecutionStackIdentity":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.setdefault("status", "qualification_candidate")
        data.pop("execution_stack_hash", None)
        provisional = cls.model_construct(**data, execution_stack_hash="0" * 64)
        data["execution_stack_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"execution_stack_hash"})
        )
        return cls.model_validate(data)

    def materialize(
        self,
        materialization: ExecutionStackMaterialization,
    ) -> "GenerationExecutionStackIdentity":
        if self.materialization_status == "materialized":
            if (
                self.profile_hash,
                self.compiler_hash,
                self.workflow_hash,
            ) == (
                materialization.profile_hash,
                materialization.compiler_hash,
                materialization.workflow_hash,
            ):
                return self
            raise ValueError("materialized execution stack cannot drift")
        values = {
            "schema_version": self.schema_version,
            "status": self.status,
            "materialization_status": "materialized",
            "candidate_id": self.candidate_id,
            "contract_version": self.contract_version,
            "provider_kind": self.provider_kind,
            "deployment_identity": self.deployment_identity,
            "model_id": self.model_id,
            "capability_id": self.capability_id,
            "profile_hash": materialization.profile_hash,
            "compiler_hash": materialization.compiler_hash,
            "workflow_hash": materialization.workflow_hash,
            "components": self.components,
            "sampler_identity": self.sampler_identity,
            "scheduler_identity": self.scheduler_identity,
            "runtime_seals": self.runtime_seals,
            "output_contract_hash": self.output_contract_hash,
        }
        return self.create(**values)
