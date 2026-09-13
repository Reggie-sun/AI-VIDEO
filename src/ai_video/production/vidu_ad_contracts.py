"""Sealed whole-ad source requests; no Shot, renderer or acceptance authority."""

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai_video.production.hashing import canonical_sha256


class _AdModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class AdImageBinding(_AdModel):
    asset_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(strict=True, gt=0, le=50 * 1024 * 1024)
    mime_type: Literal["image/png", "image/jpeg", "image/webp"]
    width: int = Field(strict=True, gt=0)
    height: int = Field(strict=True, gt=0)

    @model_validator(mode="after")
    def _ratio(self):
        if not 0.25 < self.width / self.height < 4:
            raise ValueError("ad image ratio is unsupported")
        return self


class AdGenerationRequest(_AdModel):
    contract_version: Literal["vidu-ad-request/1"] = "vidu-ad-request/1"
    task_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    submit_limit: int = Field(strict=True, gt=0)
    project_id: str = Field(min_length=1)
    project_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    registry_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    profile_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    images: tuple[AdImageBinding, ...] = Field(min_length=1, max_length=7)
    prompt: str = Field(min_length=1, max_length=2000, repr=False)
    duration: int = Field(strict=True, ge=8, le=60)
    aspect_ratio: Literal["1:1", "16:9", "9:16"]
    language: Literal["zh", "en"]
    creative: bool = Field(strict=True)
    policy_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    expires_at: datetime
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _seal(self):
        if (not self.prompt.strip() or self.expires_at.utcoffset() is None
                or len({x.asset_id for x in self.images}) != len(self.images)
                or canonical_sha256(self) != self.content_hash):
            raise ValueError("ad request identity or seal is invalid")
        return self

    @classmethod
    def create(cls, **values):
        draft = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate({**draft.model_dump(), "content_hash": canonical_sha256(draft)})

    @property
    def path(self) -> Path:
        return Path(f"state/ad-generation/requests/{self.content_hash}.json")


class AdSourceCandidate(_AdModel):
    """Downloaded bytes only. Media correctness and advertising QA are not evaluated."""

    request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    submit_receipt_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    task_id: str = Field(pattern=r"^[A-Za-z0-9._:-]{1,256}$")
    creation_id: str = Field(pattern=r"^[A-Za-z0-9._:-]{1,256}$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(strict=True, gt=0)
    mime_type: Literal["video/mp4"] = "video/mp4"
    locator_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    remote_origin: str
    downloaded_at: datetime
    acceptance: Literal["not_evaluated"] = "not_evaluated"

    @model_validator(mode="after")
    def _provenance(self):
        from ai_video.production.vidu_download import parse_result_url
        if (self.downloaded_at.utcoffset() is None
                or parse_result_url(self.remote_origin + "/").origin != self.remote_origin):
            raise ValueError("ad download provenance is invalid")
        return self

    @property
    def path(self) -> Path:
        return Path(f"state/ad-generation/candidates/{self.sha256}.mp4")

    @property
    def receipt_path(self) -> Path:
        return Path(f"state/ad-generation/receipts/{canonical_sha256(self)}.json")


class AdGenerationState(_AdModel):
    request: AdGenerationRequest
    preview_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    observation: Literal["unsubmitted", "created", "queueing", "processing", "success", "failed"] = "unsubmitted"
    candidate: AdSourceCandidate | None = None

    @model_validator(mode="after")
    def _candidate(self):
        if self.candidate is not None and (
            self.observation != "success" or self.candidate.request_hash != self.request.content_hash
        ):
            raise ValueError("ad candidate does not match the successful request")
        return self


def validate_ad_attempt(attempt):
    state = attempt.ad_generation_state
    if (attempt.operation == "ad_generation") != (state is not None):
        raise ValueError("ad operation and state must be paired")
    if state is None:
        return
    if (attempt.candidate_project is not None or attempt.candidate_registry is not None
            or state.request.project_hash != attempt.base_project.content_hash
            or state.request.registry_hash != attempt.base_registry.content_hash):
        raise ValueError("ad source attempt cannot activate or change its input identity")
    if state.observation != "unsubmitted" or state.candidate is not None:
        paid = attempt.paid_provider_state
        if paid is None or paid.phase.value not in {"accepted", "settled"}:
            raise ValueError("ad output requires accepted paid submission")
    if (attempt.status.value == "succeeded") != (state.candidate is not None):
        raise ValueError("ad success requires downloaded unaccepted candidate bytes")
