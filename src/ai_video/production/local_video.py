from __future__ import annotations

from datetime import datetime
from typing import BinaryIO, Protocol

from pydantic import Field, field_validator, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoGenerationPreview,
    VideoGenerationRequest,
    VideoProviderCapabilities,
    VideoTaskState,
)


_SHA256 = r"^[0-9a-f]{64}$"
_SAFE_ID = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$"


def _aware(value: datetime, label: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value


class LocalVideoSubmitResult(StrictModel):
    generation_id: str = Field(pattern=_SAFE_ID)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    provider_request_id: str = Field(pattern=_SAFE_ID)
    submitted_at: datetime
    result_fingerprint: str = Field(pattern=_SHA256)

    @field_validator("submitted_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return _aware(value, "local video submit timestamp")

    @model_validator(mode="after")
    def _validate_seal(self) -> "LocalVideoSubmitResult":
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"result_fingerprint"})
        )
        if self.result_fingerprint != expected:
            raise ValueError("local video submit result fingerprint is invalid")
        return self

    @classmethod
    def create(
        cls,
        *,
        resolved: ResolvedVideoGenerationRequest,
        provider_request_id: str,
        submitted_at: datetime,
    ) -> "LocalVideoSubmitResult":
        data = {
            "generation_id": resolved.generation_id,
            "resolved_generation_hash": resolved.resolved_generation_hash,
            "provider_request_id": provider_request_id,
            "submitted_at": submitted_at,
        }
        candidate = cls.model_construct(**data, result_fingerprint="0" * 64)
        return cls.model_validate(
            {
                **data,
                "result_fingerprint": canonical_sha256(
                    candidate.model_dump(
                        mode="json", exclude={"result_fingerprint"}
                    )
                ),
            }
        )


class LocalVideoSubmitIntent(StrictModel):
    attempt_id: str = Field(pattern=_SAFE_ID)
    request_fingerprint: str = Field(pattern=_SHA256)
    preview_fingerprint: str = Field(pattern=_SHA256)
    recorded_at: datetime
    intent_fingerprint: str = Field(pattern=_SHA256)

    @field_validator("recorded_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return _aware(value, "local video submit intent timestamp")

    @model_validator(mode="after")
    def _validate_seal(self) -> "LocalVideoSubmitIntent":
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"intent_fingerprint"})
        )
        if self.intent_fingerprint != expected:
            raise ValueError("local video submit intent fingerprint is invalid")
        return self

    @classmethod
    def create(
        cls,
        *,
        attempt_id: str,
        request: ResolvedVideoGenerationRequest,
        preview: VideoGenerationPreview,
        recorded_at: datetime,
    ) -> "LocalVideoSubmitIntent":
        if (
            preview.resolved_generation_hash != request.resolved_generation_hash
            or preview.execution_kind.value != "local"
            or preview.billing_kind.value != "local_unmetered"
        ):
            raise ValueError("local video preview does not match the request")
        data = {
            "attempt_id": attempt_id,
            "request_fingerprint": request.resolved_generation_hash,
            "preview_fingerprint": preview.preview_fingerprint,
            "recorded_at": recorded_at,
        }
        candidate = cls.model_construct(**data, intent_fingerprint="0" * 64)
        return cls.model_validate(
            {
                **data,
                "intent_fingerprint": canonical_sha256(
                    candidate.model_dump(
                        mode="json", exclude={"intent_fingerprint"}
                    )
                ),
            }
        )


class DurableLocalVideoSubmitPermit(Protocol):
    def _consume_local_video_submit_permit(
        self,
        *,
        intent_fingerprint: str,
        request_fingerprint: str,
    ) -> bool: ...


class LocalVideoSubmission(StrictModel):
    generation_id: str = Field(pattern=_SAFE_ID)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    submit_result_fingerprint: str = Field(pattern=_SHA256)
    provider_request_id: str = Field(pattern=_SAFE_ID)
    submitted_at: datetime
    submission_fingerprint: str = Field(pattern=_SHA256)

    @field_validator("submitted_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return _aware(value, "local video submission timestamp")

    @model_validator(mode="after")
    def _validate_seal(self) -> "LocalVideoSubmission":
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"submission_fingerprint"})
        )
        if self.submission_fingerprint != expected:
            raise ValueError("local video submission fingerprint is invalid")
        return self

    @classmethod
    def from_submit_result(
        cls,
        *,
        resolved: ResolvedVideoGenerationRequest,
        result: LocalVideoSubmitResult,
    ) -> "LocalVideoSubmission":
        if (
            result.generation_id != resolved.generation_id
            or result.resolved_generation_hash != resolved.resolved_generation_hash
        ):
            raise ValueError("local video submit result does not match request")
        data = {
            "generation_id": resolved.generation_id,
            "resolved_generation_hash": resolved.resolved_generation_hash,
            "submit_result_fingerprint": result.result_fingerprint,
            "provider_request_id": result.provider_request_id,
            "submitted_at": result.submitted_at,
        }
        candidate = cls.model_construct(**data, submission_fingerprint="0" * 64)
        return cls.model_validate(
            {
                **data,
                "submission_fingerprint": canonical_sha256(
                    candidate.model_dump(
                        mode="json", exclude={"submission_fingerprint"}
                    )
                ),
            }
        )


class LocalVideoTaskObservation(StrictModel):
    submission_fingerprint: str = Field(pattern=_SHA256)
    submit_result_fingerprint: str = Field(pattern=_SHA256)
    state: VideoTaskState
    observed_at: datetime
    progress_milli: int | None = Field(default=None, strict=True, ge=0, le=1000)
    provider_file_id: str | None = Field(default=None, pattern=_SAFE_ID)
    observation_fingerprint: str = Field(pattern=_SHA256)

    @field_validator("observed_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return _aware(value, "local video observation timestamp")

    @model_validator(mode="after")
    def _validate_observation(self) -> "LocalVideoTaskObservation":
        if self.state is VideoTaskState.SUCCEEDED and self.provider_file_id is None:
            raise ValueError("succeeded local video observation requires a file ID")
        if self.state is VideoTaskState.FAILED and self.provider_file_id is not None:
            raise ValueError("failed local video observation cannot contain a file ID")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"observation_fingerprint"})
        )
        if self.observation_fingerprint != expected:
            raise ValueError("local video observation fingerprint is invalid")
        return self

    @classmethod
    def create(
        cls,
        *,
        submission: LocalVideoSubmission,
        state: VideoTaskState,
        observed_at: datetime,
        progress_milli: int | None = None,
        provider_file_id: str | None = None,
    ) -> "LocalVideoTaskObservation":
        data = {
            "submission_fingerprint": submission.submission_fingerprint,
            "submit_result_fingerprint": submission.submit_result_fingerprint,
            "state": state,
            "observed_at": observed_at,
            "progress_milli": progress_milli,
            "provider_file_id": provider_file_id,
        }
        candidate = cls.model_construct(**data, observation_fingerprint="0" * 64)
        return cls.model_validate(
            {
                **data,
                "observation_fingerprint": canonical_sha256(
                    candidate.model_dump(
                        mode="json", exclude={"observation_fingerprint"}
                    )
                ),
            }
        )


class LocalVideoFetchReceipt(StrictModel):
    submission_fingerprint: str = Field(pattern=_SHA256)
    observation_fingerprint: str = Field(pattern=_SHA256)
    submit_result_fingerprint: str = Field(pattern=_SHA256)
    provider_file_id: str = Field(pattern=_SAFE_ID)
    content_type: str = Field(pattern=r"^video/mp4$")
    size_bytes: int = Field(strict=True, gt=0)
    artifact_sha256: str = Field(pattern=_SHA256)
    fetched_at: datetime
    fetch_fingerprint: str = Field(pattern=_SHA256)

    @field_validator("fetched_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return _aware(value, "local video fetch timestamp")

    @model_validator(mode="after")
    def _validate_seal(self) -> "LocalVideoFetchReceipt":
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"fetch_fingerprint"})
        )
        if self.fetch_fingerprint != expected:
            raise ValueError("local video fetch fingerprint is invalid")
        return self

    @classmethod
    def create(
        cls,
        *,
        submission: LocalVideoSubmission,
        observation: LocalVideoTaskObservation,
        content_type: str,
        size_bytes: int,
        artifact_sha256: str,
        fetched_at: datetime,
    ) -> "LocalVideoFetchReceipt":
        if (
            observation.submission_fingerprint != submission.submission_fingerprint
            or observation.submit_result_fingerprint
            != submission.submit_result_fingerprint
            or observation.state is not VideoTaskState.SUCCEEDED
            or observation.provider_file_id is None
        ):
            raise ValueError("local video fetch requires the exact succeeded task")
        data = {
            "submission_fingerprint": submission.submission_fingerprint,
            "observation_fingerprint": observation.observation_fingerprint,
            "submit_result_fingerprint": submission.submit_result_fingerprint,
            "provider_file_id": observation.provider_file_id,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "artifact_sha256": artifact_sha256,
            "fetched_at": fetched_at,
        }
        candidate = cls.model_construct(**data, fetch_fingerprint="0" * 64)
        return cls.model_validate(
            {
                **data,
                "fetch_fingerprint": canonical_sha256(
                    candidate.model_dump(
                        mode="json", exclude={"fetch_fingerprint"}
                    )
                ),
            }
        )


class LocalVideoProvider(Protocol):
    def capabilities(self) -> VideoProviderCapabilities: ...

    def resolve(
        self, request: VideoGenerationRequest
    ) -> ResolvedVideoGenerationRequest: ...

    def preview(
        self, request: ResolvedVideoGenerationRequest
    ) -> VideoGenerationPreview: ...

    def submit_local(
        self,
        request: ResolvedVideoGenerationRequest,
        preview: VideoGenerationPreview,
        intent: LocalVideoSubmitIntent,
        permit: DurableLocalVideoSubmitPermit,
    ) -> LocalVideoSubmitResult: ...

    def get_local_status(
        self, submission: LocalVideoSubmission
    ) -> LocalVideoTaskObservation: ...

    def fetch_local(
        self,
        submission: LocalVideoSubmission,
        observation: LocalVideoTaskObservation,
        sink: BinaryIO,
    ) -> LocalVideoFetchReceipt: ...


__all__ = [
    "LocalVideoFetchReceipt",
    "LocalVideoProvider",
    "LocalVideoSubmission",
    "LocalVideoSubmitIntent",
    "DurableLocalVideoSubmitPermit",
    "LocalVideoSubmitResult",
    "LocalVideoTaskObservation",
]
