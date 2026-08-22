from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_execution_stack_materialization_source_path,
)
from ai_video.production.video_execution_stack import (
    ExecutionStackMaterialization,
    GenerationExecutionStackIdentity,
)


ExecutionStackSourceKind = Literal["profile", "compiler", "workflow"]


@dataclass(frozen=True)
class ExecutionStackSourceArtifact:
    relative_path: Path
    payload: bytes
    file_sha256: str


def prepare_execution_stack_source_artifacts(
    materializations: tuple[ExecutionStackMaterialization, ...],
) -> tuple[ExecutionStackSourceArtifact, ...]:
    """Prepare deduplicated immutable source bytes for one stack materialization."""

    prepared: dict[Path, ExecutionStackSourceArtifact] = {}
    for materialization in materializations:
        for kind in ("profile", "compiler", "workflow"):
            source_kind: ExecutionStackSourceKind = kind
            payload = getattr(materialization, f"{source_kind}_bytes")
            content_hash = getattr(materialization, f"{source_kind}_hash")
            if hashlib.sha256(payload).hexdigest() != content_hash:
                raise ValueError(
                    "execution stack source bytes do not match their materialized hash"
                )
            relative_path = canonical_execution_stack_materialization_source_path(
                source_kind,
                content_hash,
            )
            artifact = ExecutionStackSourceArtifact(
                relative_path=relative_path,
                payload=payload,
                file_sha256=content_hash,
            )
            existing = prepared.get(relative_path)
            if existing is not None and existing != artifact:
                raise ValueError("execution stack source path has conflicting bytes")
            prepared[relative_path] = artifact
    return tuple(prepared[path] for path in sorted(prepared, key=Path.as_posix))


def verify_execution_stack_source_artifacts(
    project_root: Path,
    stacks: tuple[GenerationExecutionStackIdentity, ...],
) -> None:
    """Reopen every materialized source without following links and rehash it."""

    for stack in stacks:
        if stack.materialization_status != "materialized":
            raise ValueError("execution stack source cannot verify an unmaterialized stack")
        for kind in ("profile", "compiler", "workflow"):
            source_kind: ExecutionStackSourceKind = kind
            content_hash = getattr(stack, f"{source_kind}_hash")
            if content_hash == "none":
                raise ValueError("materialized execution stack source hash is missing")
            path = project_root / canonical_execution_stack_materialization_source_path(
                source_kind,
                content_hash,
            )
            try:
                reopened = _read_regular_file_nofollow(
                    path,
                    contained_by=project_root,
                )
            except (OSError, ValueError) as exc:
                raise ValueError(
                    f"execution stack {source_kind} source could not be reopened"
                ) from exc
            if reopened.file_sha256 != content_hash:
                raise ValueError(
                    f"execution stack {source_kind} source hash does not match"
                )
