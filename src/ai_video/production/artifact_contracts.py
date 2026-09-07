from __future__ import annotations

from typing import Literal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ToolIdentity(StrictModel):
    name: str
    version: str


class SourceReference(StrictModel):
    kind: Literal["user_input", "imported", "derived"]
    reference: str
    content_hash: str | None = None


class ArtifactReference(StrictModel):
    artifact_id: str = Field(min_length=1)
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    path: Path


class QaPolicyPointer(StrictModel):
    path: Path
    policy_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _canonical_pointer(self):
        if self.path != Path(f"state/reviews/policy.{self.content_hash}.json"):
            raise ValueError("QA policy pointer path must be canonical")
        return self


class VersionedArtifact(StrictModel):
    artifact_id: str = Field(min_length=1)
    schema_version: Literal["2.0"] = "2.0"
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    creation_receipt_id: str = Field(min_length=1)
    source_provenance: tuple[SourceReference, ...] = Field(min_length=1)
