"""Runtime-neutral contracts for one Shot Continuity source qualification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ai_video.comfy_client import JobResult

from ai_video.production.shot_continuity_m0_qualification import (
    M0ValidationPreflightSnapshot,
)


@dataclass(frozen=True)
class SourceQualificationInput:
    file_name: str
    data: bytes
    file_sha256: str
    size_bytes: int


@dataclass(frozen=True)
class SourceQualificationPreflightSnapshot:
    qualification_profile_hash: str
    sealed_seed: int
    p0: M0ValidationPreflightSnapshot
    source_execution_stack_hash: str
    source_profile_hash: str
    source_compiler_hash: str
    source_workflow_hash: str
    project_content_hash: str
    registry_content_hash: str
    dependency_graph_content_hash: str
    m0_node_schema_hashes: tuple[tuple[str, str], ...]
    source_node_schema_hashes: tuple[tuple[str, str], ...]
    component_hashes: tuple[tuple[str, str], ...]
    inputs: tuple[SourceQualificationInput, SourceQualificationInput]


@dataclass(frozen=True)
class ShotContinuitySourceQualificationOutcome:
    attempt_id: str
    provider_request_id: str
    source_execution_stack_hash: str
    sealed_seed: int


class SourceQualificationTransport(Protocol):
    deployment_identity: str
    base_url: str

    def get_object_info(self) -> dict[str, Any]: ...

    def upload_input(self, item: SourceQualificationInput) -> str: ...

    def submit_prompt(self, workflow: dict[str, Any]) -> str: ...

    def poll_job(
        self,
        prompt_id: str,
        *,
        poll_interval_seconds: float,
        timeout_seconds: float,
    ) -> JobResult: ...

    def fetch_artifact_bytes(
        self,
        *,
        filename: str,
        subfolder: str,
        type_: str,
    ) -> bytes: ...


__all__ = [
    "ShotContinuitySourceQualificationOutcome",
    "SourceQualificationInput",
    "SourceQualificationPreflightSnapshot",
    "SourceQualificationTransport",
]
