"""Provider-neutral remote-media materialization and transient refresh authority."""

from __future__ import annotations

import re
import threading
from datetime import datetime
from typing import Callable, Literal
from urllib.parse import urlsplit

from pydantic import ConfigDict, Field, field_validator, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256


_SAFE_ID = re.compile(r"^[A-Za-z0-9._:/-]{1,256}$")
_SHA256 = r"^[0-9a-f]{64}$"


def _canonical_https_origin(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("remote media origin must be a canonical HTTPS origin") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("remote media origin must be a canonical HTTPS origin")
    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    canonical = f"https://{host}"
    if port is not None and port != 443:
        canonical = f"{canonical}:{port}"
    if value != canonical:
        raise ValueError("remote media origin must be a canonical HTTPS origin")
    return value


class _RemoteMediaStrictModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class RemoteMediaMaterializationReceipt(_RemoteMediaStrictModel):
    """Exact remote locator-to-byte binding without persisting the locator."""

    schema_version: Literal["1"] = "1"
    transport_kind: Literal["provider_output_https"]
    provider_kind: str = Field(pattern=_SAFE_ID.pattern)
    model_id: str = Field(pattern=_SAFE_ID.pattern)
    submission_fingerprint: str = Field(pattern=_SHA256)
    paid_submit_receipt_fingerprint: str = Field(pattern=_SHA256)
    provider_file_id: str = Field(pattern=_SAFE_ID.pattern)
    remote_origin: str
    remote_locator_sha256: str = Field(pattern=_SHA256)
    artifact_sha256: str = Field(pattern=_SHA256)
    artifact_size_bytes: int = Field(strict=True, gt=0)
    artifact_mime_type: Literal["video/mp4", "video/quicktime"]
    accessibility_verification: Literal["exact_get"]
    verified_at: datetime
    content_hash: str = Field(pattern=_SHA256)

    @field_validator("remote_origin")
    @classmethod
    def _canonical_origin(cls, value: str) -> str:
        return _canonical_https_origin(value)

    @field_validator("verified_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "remote media materialization timestamp must be timezone-aware"
            )
        return value

    @model_validator(mode="after")
    def _validate_seal(self) -> "RemoteMediaMaterializationReceipt":
        if self.content_hash != canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        ):
            raise ValueError("remote media materialization receipt seal does not match")
        return self

    @classmethod
    def create(cls, **values: object) -> "RemoteMediaMaterializationReceipt":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.pop("content_hash", None)
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            candidate.model_dump(
                mode="json", exclude={"content_hash"}, warnings=False
            )
        )
        return cls.model_validate(data)


_REMOTE_REFERENCE_REFRESH_PERMIT_TOKEN = object()


class _RemoteReferenceRefreshPermit:
    """Process-local one-use proof that Service reopened an activated source."""

    __slots__ = ("_binding", "_durability_validator", "_consumed", "_lock")

    def __init__(
        self,
        token: object,
        *,
        submission_fingerprint: str,
        observation_fingerprint: str,
        fetch_fingerprint: str,
        materialization_receipt_id: str,
        durability_validator: Callable[[], bool],
    ) -> None:
        if token is not _REMOTE_REFERENCE_REFRESH_PERMIT_TOKEN:
            raise TypeError(
                "Remote reference refresh permits are minted only by VideoGenerationService."
            )
        self._binding = (
            submission_fingerprint,
            observation_fingerprint,
            fetch_fingerprint,
            materialization_receipt_id,
        )
        self._durability_validator = durability_validator
        self._consumed = False
        self._lock = threading.Lock()

    def _consume(
        self,
        *,
        submission_fingerprint: str,
        observation_fingerprint: str,
        fetch_fingerprint: str,
        materialization_receipt_id: str,
    ) -> bool:
        binding = (
            submission_fingerprint,
            observation_fingerprint,
            fetch_fingerprint,
            materialization_receipt_id,
        )
        with self._lock:
            if (
                self._consumed
                or binding != self._binding
                or not self._durability_validator()
            ):
                return False
            self._consumed = True
            return True

    def _durability_is_current(self) -> bool:
        return self._consumed and self._durability_validator()

    def __reduce__(self) -> object:
        raise TypeError("Remote reference refresh permits cannot be serialized.")
