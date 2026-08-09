from __future__ import annotations

import hashlib
import json
from typing import Any, TypeVar

from pydantic import BaseModel

ArtifactT = TypeVar("ArtifactT", bound=BaseModel)


def _semantic_data(value: BaseModel | dict[str, Any]) -> dict[str, Any]:
    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else dict(value)
    data.pop("content_hash", None)
    return data


def canonical_sha256(value: BaseModel | dict[str, Any]) -> str:
    payload = json.dumps(
        _semantic_data(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def seal_artifact(artifact: ArtifactT) -> ArtifactT:
    return artifact.model_copy(update={"content_hash": canonical_sha256(artifact)})


def verify_artifact_hash(artifact: BaseModel) -> bool:
    expected = getattr(artifact, "content_hash", None)
    return (
        isinstance(expected, str)
        and len(expected) == 64
        and expected == canonical_sha256(artifact)
    )
