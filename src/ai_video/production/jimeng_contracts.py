"""Sealed technical identities for Jimeng's canvas generation surface."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel
from ai_video.production.video import ProviderProfilePointer, VideoFlexibleOutputRequirement


JIMENG_ORIGIN = "https://jimeng.jianying.com"
JIMENG_MODEL = "seedance_2.5"
JIMENG_PROVIDER = "jimeng"
JIMENG_CAPABILITY = "jimeng-seedance-2.5-multimodal-v1"
JIMENG_COMPILER = "jimeng-seedance-2.5-video-compiler"
JIMENG_PROFILE_VERSION = "canvas-seedance-2.5-v1"


class JimengProfile(StrictModel):
    """One canvas target, account, native output specification and credit bound."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    account_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    project_id: str = Field(pattern=r"^[0-9a-f-]{36}$")
    node_id: str = Field(pattern=r"^node_[A-Za-z0-9]{1,64}$")
    duration_seconds: int = Field(strict=True, ge=4, le=30)
    resolution: Literal["480p", "720p", "1080p"]
    aspect_ratio: Literal["16:9", "9:16", "1:1", "4:3", "3:4"]
    benefit_amount: int = Field(strict=True, gt=0)
    benefit_type: str = Field(pattern=r"^[A-Za-z0-9_]{1,128}$")
    credit_upper_bound: int = Field(strict=True, gt=0)
    # The quote is checked against this operator bound immediately before dispatch.
    # It is not a server-enforced hard spending cap.

    def pointer(self) -> ProviderProfilePointer:
        digest = canonical_sha256(self.model_dump(mode="json"))
        return ProviderProfilePointer(
            profile_id=JIMENG_PROVIDER,
            profile_version=JIMENG_PROFILE_VERSION,
            profile_path=Path(f"provider-profiles/{digest}.json"),
            profile_sha256=digest,
        )

    def output(self) -> VideoFlexibleOutputRequirement:
        return VideoFlexibleOutputRequirement(
            timing_mode="nominal_seconds",
            duration_seconds=self.duration_seconds,
            dimension_mode="adaptive",
            resolution_label=self.resolution,
            ratio=self.aspect_ratio,
            fps=None,
            container="mp4",
            mime_type="video/mp4",
            native_audio=True,
        )


class JimengMaterial(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    index: int = Field(strict=True, ge=0)
    kind: Literal["image", "audio", "video"]
    asset_id: str = Field(min_length=1)
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(strict=True, gt=0)
    duration_millis: int | None = Field(default=None, strict=True, gt=0)
    storage_id: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def _duration(self) -> "JimengMaterial":
        if (self.kind == "image") != (self.duration_millis is None):
            raise ValueError("Jimeng material duration does not match its kind")
        return self


class JimengDispatchIntent(StrictModel):
    """Immutable pre-network identity; it never claims a task was accepted."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal["jimeng-dispatch/1"] = "jimeng-dispatch/1"
    attempt_id: str = Field(pattern=r"^[A-Za-z0-9._:/-]{1,256}$")
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    preview_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    account_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    project_id: str = Field(pattern=r"^[0-9a-f-]{36}$")
    node_id: str = Field(pattern=r"^node_[A-Za-z0-9]{1,64}$")
    submit_id: str = Field(pattern=r"^[0-9a-f-]{36}$")
    resource_id: str = Field(pattern=r"^[0-9a-f-]{36}$")
    params_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    materials: tuple[JimengMaterial, ...] = Field(min_length=1)
    recorded_at: datetime
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _seal(self) -> "JimengDispatchIntent":
        if self.recorded_at.tzinfo is None:
            raise ValueError("Jimeng dispatch time must be timezone-aware")
        if tuple(x.index for x in self.materials) != tuple(range(len(self.materials))):
            raise ValueError("Jimeng materials must retain contiguous native indices")
        if self.content_hash != canonical_sha256(self.model_dump(mode="json", exclude={"content_hash"})):
            raise ValueError("Jimeng dispatch identity hash mismatch")
        return self

    @classmethod
    def create(cls, **values):
        data = dict(values)
        trial = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(trial.model_dump(mode="json", exclude={"content_hash"}))
        return cls.model_validate(data)


def dispatch_path(content_hash: str) -> Path:
    """Content-addressed technical evidence, without lifecycle authority."""

    return Path("artifacts/provider-dispatch/jimeng") / f"{content_hash}.json"


class JimengCanvasSnapshot(StrictModel):
    """Exact server-saved draft containing this submitted output node."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal["jimeng-canvas-snapshot/1"] = "jimeng-canvas-snapshot/1"
    attempt_id: str = Field(pattern=r"^[A-Za-z0-9._:/-]{1,256}$")
    dispatch_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    project_id: str = Field(pattern=r"^[0-9a-f-]{36}$")
    node_id: str = Field(pattern=r"^node_[A-Za-z0-9]{1,64}$")
    resource_id: str = Field(pattern=r"^[0-9a-f-]{36}$")
    draft_version: int = Field(strict=True, ge=0)
    head_draft_version: int = Field(strict=True, ge=0)
    draft_json: str = Field(min_length=1)
    draft_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    recorded_at: datetime
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _seal(self) -> "JimengCanvasSnapshot":
        if self.recorded_at.tzinfo is None or self.draft_version > self.head_draft_version:
            raise ValueError("Jimeng canvas version or time is invalid")
        if hashlib.sha256(self.draft_json.encode("utf-8")).hexdigest() != self.draft_sha256:
            raise ValueError("Jimeng canvas draft bytes changed")
        try:
            draft = json.loads(self.draft_json)
        except ValueError as exc:
            raise ValueError("Jimeng canvas draft JSON is invalid") from exc
        nodes = draft.get("nodes") if isinstance(draft, dict) else None
        if not isinstance(nodes, list) or sum(
            node.get("id") == self.node_id and
            isinstance(node.get("data"), dict) and
            node["data"].get("resourceId") == self.resource_id
            for node in nodes if isinstance(node, dict)
        ) != 1:
            raise ValueError("Jimeng saved draft does not contain the exact output node")
        if self.content_hash != canonical_sha256(self.model_dump(mode="json", exclude={"content_hash"})):
            raise ValueError("Jimeng canvas snapshot hash mismatch")
        return self

    @classmethod
    def create(cls, **values):
        data = dict(values)
        data["draft_sha256"] = hashlib.sha256(data["draft_json"].encode("utf-8")).hexdigest()
        trial = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(trial.model_dump(mode="json", exclude={"content_hash"}))
        return cls.model_validate(data)


def canvas_snapshot_path(content_hash: str) -> Path:
    return Path("artifacts/provider-canvas/jimeng") / f"{content_hash}.json"
