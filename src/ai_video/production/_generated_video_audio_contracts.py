"""Immutable contracts for audio derived from a settled generated-video fetch."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, model_validator

from ai_video.production.audio import AudioProbeResult
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    AudioAssetMetadata,
    PaidProviderBudgetSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    StrictModel,
    ToolIdentity,
)
from ai_video.production.paid_provider import (
    PaidProviderBudgetReservation,
    PaidProviderBudgetSnapshot,
    PaidProviderGateReceipt,
    PaidProviderSubmitReceipt,
)
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoFetchReceipt,
    VideoTaskObservation,
)


def canonical_generated_video_audio_receipt_path(file_sha256: str) -> Path:
    return Path(f"state/generated-video-audio/receipts/{file_sha256}.json")


class GeneratedVideoAudioReceipt(StrictModel):
    derivation_identity: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_project_id: str = Field(min_length=1)
    target_attempt_id: str = Field(min_length=1)
    target_asset_id: str = Field(min_length=1)
    target_base_project: ProjectSnapshotPointer
    target_base_registry: RegistrySnapshotPointer
    target_audio_metadata: AudioAssetMetadata
    target_usage_license: str = Field(min_length=1)
    source_project_id: str = Field(min_length=1)
    source_attempt_id: str = Field(min_length=1)
    source_request: ResolvedVideoGenerationRequest
    source_observation: VideoTaskObservation
    source_fetch: VideoFetchReceipt
    source_gate: PaidProviderGateReceipt
    source_submit: PaidProviderSubmitReceipt
    source_budget_pointer: PaidProviderBudgetSnapshotPointer
    source_budget: PaidProviderBudgetSnapshot
    source_reservation: PaidProviderBudgetReservation
    extraction_ffmpeg: ToolIdentity
    probe_ffprobe: ToolIdentity
    probe: AudioProbeResult
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _require_content_hash(self) -> "GeneratedVideoAudioReceipt":
        expected = canonical_sha256(self.model_dump(mode="json", exclude={"content_hash"}))
        if self.content_hash != expected:
            raise ValueError("generated video audio receipt content hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "GeneratedVideoAudioReceipt":
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {
                **values,
                "content_hash": canonical_sha256(
                    provisional.model_dump(mode="json", exclude={"content_hash"})
                ),
            }
        )


def generated_video_audio_derivation_identity(
    *,
    target_project_id: str,
    target_attempt_id: str,
    target_asset_id: str,
    target_base_project: ProjectSnapshotPointer,
    target_base_registry: RegistrySnapshotPointer,
    target_audio_metadata: AudioAssetMetadata,
    target_usage_license: str,
    source_project_id: str,
    source_attempt_id: str,
    source_request: ResolvedVideoGenerationRequest,
    source_observation: VideoTaskObservation,
    source_fetch: VideoFetchReceipt,
    source_gate: PaidProviderGateReceipt,
    source_submit: PaidProviderSubmitReceipt,
    source_budget_pointer: PaidProviderBudgetSnapshotPointer,
    source_budget: PaidProviderBudgetSnapshot,
    source_reservation: PaidProviderBudgetReservation,
    extraction_ffmpeg: ToolIdentity,
    probe_ffprobe: ToolIdentity,
) -> str:
    metadata = target_audio_metadata.model_dump(mode="json")
    metadata.pop("provenance_receipt_id")
    return canonical_sha256(
        {
            "schema": "generated-video-audio/2",
            "target": {
                "project_id": target_project_id,
                "attempt_id": target_attempt_id,
                "asset_id": target_asset_id,
                "base_project": target_base_project.model_dump(mode="json"),
                "base_registry": target_base_registry.model_dump(mode="json"),
                "audio_metadata": metadata,
                "usage_license": target_usage_license,
            },
            "source": {
                "project_id": source_project_id,
                "attempt_id": source_attempt_id,
                "request": source_request.model_dump(mode="json"),
                "observation": source_observation.model_dump(mode="json"),
                "fetch": source_fetch.model_dump(mode="json"),
                "gate": source_gate.model_dump(mode="json"),
                "submit": source_submit.model_dump(mode="json"),
                "budget_pointer": source_budget_pointer.model_dump(mode="json"),
                "budget": source_budget.model_dump(mode="json"),
                "reservation": source_reservation.model_dump(mode="json"),
            },
            "ffmpeg": extraction_ffmpeg.model_dump(mode="json"),
            "ffprobe": probe_ffprobe.model_dump(mode="json"),
        }
    )
