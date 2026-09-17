"""Exact local-video materialization for Seedance HTTPS references.

The durable contracts never retain presigned URLs. A short-lived in-memory
grant uploads one authorized non-identity-bearing video and verifies the exact
bytes through the corresponding HTTPS read locator before a resolver can hand
that locator to the Seedance adapter.
"""

from __future__ import annotations

import hashlib
import re
import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, Protocol
from urllib.parse import urlsplit

import httpx
from pydantic import ConfigDict, Field, field_validator, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoGenerationRequest,
    VideoMediaReferenceBinding,
)


_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,511}$")
_SHA256 = r"^[0-9a-f]{64}$"
_MAX_LEASE = timedelta(minutes=5)
_VERSION_HEADER_BY_PROVIDER = {
    "volcengine_tos": "x-tos-version-id",
}
_MP4_MAJOR_BRANDS = {
    b"M4V ",
    b"avc1",
    b"iso2",
    b"iso5",
    b"iso6",
    b"isom",
    b"mp41",
    b"mp42",
}


def _error(code: ErrorCode, message: str) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, retryable=False)


def _canonical_https_origin(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("local video materialization origin must be HTTPS") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("local video materialization origin must be HTTPS")
    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    canonical = f"https://{host}"
    if port is not None and port != 443:
        canonical = f"{canonical}:{port}"
    if value != canonical:
        raise ValueError("local video materialization origin must be canonical")
    return value


def _url_origin(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("local video materialization URL is invalid") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or not parsed.path
        or parsed.fragment
    ):
        raise ValueError("local video materialization URL is invalid")
    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    origin = f"https://{host}"
    if port is not None and port != 443:
        origin = f"{origin}:{port}"
    return origin


def _is_mp4(prefix: bytes, size_bytes: int) -> bool:
    if len(prefix) < 16 or prefix[4:8] != b"ftyp":
        return False
    box_size = int.from_bytes(prefix[:4], "big")
    return 16 <= box_size <= size_bytes and prefix[8:12] in _MP4_MAJOR_BRANDS


class _LocalVideoStrictModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class SeedanceLocalVideoMaterializationPreview(_LocalVideoStrictModel):
    """Durable exact preview for one bounded local-video upload."""

    schema_version: Literal["1"] = "1"
    attempt_id: str = Field(pattern=_SAFE_ID.pattern)
    task_scope_id: str = Field(pattern=_SAFE_ID.pattern)
    target_provider_kind: Literal["volcengine_ark_seedance"]
    target_model_id: str = Field(pattern=_SAFE_ID.pattern)
    target_request_fingerprint: str = Field(pattern=_SHA256)
    source_asset_id: str = Field(pattern=_SAFE_ID.pattern)
    source_registry_revision_id: str = Field(pattern=_SHA256)
    source_asset_sha256: str = Field(pattern=_SHA256)
    source_mime_type: Literal["video/mp4"]
    source_size_bytes: int = Field(strict=True, gt=0)
    source_width: int = Field(strict=True, gt=0)
    source_height: int = Field(strict=True, gt=0)
    source_fps: int = Field(strict=True, ge=24, le=60)
    source_duration_millis: int = Field(strict=True, gt=0)
    classification: Literal[
        "synthetic_non_identity_bearing_video",
        "ordinary_non_character_video",
    ]
    storage_provider: str = Field(pattern=_SAFE_ID.pattern)
    storage_account_scope: str = Field(pattern=_SAFE_ID.pattern)
    storage_bucket: str = Field(pattern=_SAFE_ID.pattern)
    storage_object_key_sha256: str = Field(pattern=_SHA256)
    upload_origin: str
    read_origin: str
    credential_reference_kind: Literal["environment", "secret_store"]
    credential_reference_id: str = Field(pattern=_SAFE_ID.pattern)
    retention_mode: Literal["task_transient"]
    created_at: datetime
    expires_at: datetime
    preview_fingerprint: str = Field(pattern=_SHA256)

    @field_validator("upload_origin", "read_origin")
    @classmethod
    def _origin_is_canonical(cls, value: str) -> str:
        return _canonical_https_origin(value)

    @model_validator(mode="after")
    def _validate_seal(self) -> "SeedanceLocalVideoMaterializationPreview":
        if (
            self.created_at.tzinfo is None
            or self.expires_at.tzinfo is None
            or self.expires_at <= self.created_at
        ):
            raise ValueError("local video materialization preview time is invalid")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"preview_fingerprint"})
        )
        if self.preview_fingerprint != expected:
            raise ValueError("local video materialization preview seal does not match")
        return self

    @classmethod
    def create(cls, **values: object) -> "SeedanceLocalVideoMaterializationPreview":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.pop("preview_fingerprint", None)
        candidate = cls.model_construct(**data, preview_fingerprint="0" * 64)
        data["preview_fingerprint"] = canonical_sha256(
            candidate.model_dump(
                mode="json", exclude={"preview_fingerprint"}, warnings=False
            )
        )
        return cls.model_validate(data)


class SeedanceLocalVideoMaterializationAuthorization(_LocalVideoStrictModel):
    """Explicit one-upload authorization bound to one exact preview."""

    schema_version: Literal["1"] = "1"
    attempt_id: str = Field(pattern=_SAFE_ID.pattern)
    preview_fingerprint: str = Field(pattern=_SHA256)
    explicit_opt_in: Literal[True]
    actor: ActorIdentity
    egress_authorized: Literal[True]
    egress_policy_receipt_id: str = Field(pattern=_SAFE_ID.pattern)
    live_test_authorized: Literal[True]
    live_authorization_receipt_id: str = Field(pattern=_SAFE_ID.pattern)
    issued_at: datetime
    expires_at: datetime
    max_upload_count: Literal[1]
    authorization_fingerprint: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "SeedanceLocalVideoMaterializationAuthorization":
        if (
            self.actor.actor_kind != "human"
            or self.issued_at.tzinfo is None
            or self.expires_at.tzinfo is None
            or self.expires_at <= self.issued_at
        ):
            raise ValueError("local video materialization authorization is invalid")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"authorization_fingerprint"})
        )
        if self.authorization_fingerprint != expected:
            raise ValueError("local video materialization authorization seal does not match")
        return self

    @classmethod
    def create(
        cls, **values: object
    ) -> "SeedanceLocalVideoMaterializationAuthorization":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.pop("authorization_fingerprint", None)
        candidate = cls.model_construct(**data, authorization_fingerprint="0" * 64)
        data["authorization_fingerprint"] = canonical_sha256(
            candidate.model_dump(
                mode="json", exclude={"authorization_fingerprint"}, warnings=False
            )
        )
        return cls.model_validate(data)


@dataclass(frozen=True, slots=True, repr=False)
class SeedanceLocalVideoUploadGrant:
    """Process-local presigned PUT/GET capability; never serialize or log."""

    upload_url: str
    read_url: str
    storage_provider: str
    storage_account_scope: str
    storage_bucket: str
    storage_object_key_sha256: str
    not_after: datetime

    def __post_init__(self) -> None:
        for value in (
            self.storage_provider,
            self.storage_account_scope,
            self.storage_bucket,
        ):
            if _SAFE_ID.fullmatch(value) is None:
                raise ValueError("local video upload grant identity is invalid")
        if re.fullmatch(_SHA256, self.storage_object_key_sha256) is None:
            raise ValueError("local video upload object identity is invalid")
        _url_origin(self.upload_url)
        _url_origin(self.read_url)
        if self.not_after.tzinfo is None:
            raise ValueError("local video upload grant expiry is invalid")

    def __reduce__(self) -> object:
        raise TypeError("local video upload grants cannot be serialized")


@dataclass(frozen=True, slots=True)
class SeedanceLocalVideoTransportRequest:
    method: Literal["PUT", "GET"]
    url: str = field(repr=False)
    headers: Mapping[str, str] = field(repr=False)


class SeedanceLocalVideoUploadResponse(Protocol):
    status_code: int
    headers: Mapping[str, str]


class SeedanceLocalVideoStreamResponse(Protocol):
    status_code: int
    headers: Mapping[str, str]

    def iter_bytes(self) -> Iterator[bytes]: ...


class SeedanceLocalVideoMaterializationTransport(Protocol):
    def upload(
        self, request: SeedanceLocalVideoTransportRequest, source_bytes: bytes
    ) -> SeedanceLocalVideoUploadResponse: ...

    def stream(
        self, request: SeedanceLocalVideoTransportRequest
    ) -> AbstractContextManager[SeedanceLocalVideoStreamResponse]: ...


@dataclass(frozen=True, slots=True)
class _HttpxUploadResponse:
    status_code: int
    headers: Mapping[str, str]


class _HttpxStreamResponse:
    def __init__(self, response: httpx.Response) -> None:
        self.status_code = response.status_code
        self.headers = response.headers
        self._response = response

    def iter_bytes(self) -> Iterator[bytes]:
        yield from self._response.iter_bytes()


class HttpxSeedanceLocalVideoMaterializationTransport:
    """No-redirect HTTP transport for presigned object PUT and exact GET."""

    def __init__(self, *, timeout_seconds: float = 120.0) -> None:
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
        )

    def upload(
        self, request: SeedanceLocalVideoTransportRequest, source_bytes: bytes
    ) -> SeedanceLocalVideoUploadResponse:
        if request.method != "PUT":
            raise ValueError("local video upload transport requires PUT")
        response = self._client.put(
            request.url,
            headers=dict(request.headers),
            content=source_bytes,
        )
        return _HttpxUploadResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    @contextmanager
    def stream(
        self, request: SeedanceLocalVideoTransportRequest
    ) -> Iterator[SeedanceLocalVideoStreamResponse]:
        if request.method != "GET":
            raise ValueError("local video readback transport requires GET")
        with self._client.stream(
            request.method,
            request.url,
            headers=dict(request.headers),
        ) as response:
            yield _HttpxStreamResponse(response)

    def close(self) -> None:
        self._client.close()


_MATERIALIZATION_PERMIT_TOKEN = object()


class _SeedanceLocalVideoMaterializationPermit:
    __slots__ = ("_binding", "_durability_validator", "_consumed", "_lock")

    def __init__(
        self,
        token: object,
        *,
        preview_fingerprint: str,
        authorization_fingerprint: str,
        durability_validator: Callable[[], bool],
    ) -> None:
        if token is not _MATERIALIZATION_PERMIT_TOKEN:
            raise TypeError("local video permits are minted only from exact authorization")
        self._binding = (preview_fingerprint, authorization_fingerprint)
        self._durability_validator = durability_validator
        self._consumed = False
        self._lock = threading.Lock()

    def _consume(
        self, *, preview_fingerprint: str, authorization_fingerprint: str
    ) -> bool:
        with self._lock:
            if (
                self._consumed
                or self._binding
                != (preview_fingerprint, authorization_fingerprint)
                or not self._durability_validator()
            ):
                return False
            self._consumed = True
            return True

    def _durability_is_current(self) -> bool:
        return self._consumed and self._durability_validator()

    def __reduce__(self) -> object:
        raise TypeError("local video materialization permits cannot be serialized")


def _validate_authorization(
    *,
    preview: SeedanceLocalVideoMaterializationPreview,
    authorization: SeedanceLocalVideoMaterializationAuthorization,
    now: datetime,
) -> None:
    if (
        authorization.attempt_id != preview.attempt_id
        or authorization.preview_fingerprint != preview.preview_fingerprint
        or now.tzinfo is None
        or now < authorization.issued_at
        or now >= authorization.expires_at
    ):
        raise _error(
            ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
            "Local video materialization authorization is not current or exact.",
        )


def issue_seedance_local_video_materialization_permit(
    *,
    preview: SeedanceLocalVideoMaterializationPreview,
    authorization: SeedanceLocalVideoMaterializationAuthorization,
    durability_validator: Callable[[], bool],
    now: datetime,
) -> _SeedanceLocalVideoMaterializationPermit:
    """Mint one process-local permit after an exact durable intent is visible."""

    _validate_authorization(preview=preview, authorization=authorization, now=now)
    if not durability_validator():
        raise _error(
            ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
            "Local video materialization intent is not durable.",
        )
    return _SeedanceLocalVideoMaterializationPermit(
        _MATERIALIZATION_PERMIT_TOKEN,
        preview_fingerprint=preview.preview_fingerprint,
        authorization_fingerprint=authorization.authorization_fingerprint,
        durability_validator=durability_validator,
    )


class SeedanceLocalVideoMaterializationReceipt(_LocalVideoStrictModel):
    """Durable source-to-object exact-byte proof without either signed URL."""

    schema_version: Literal["1"] = "1"
    preview_fingerprint: str = Field(pattern=_SHA256)
    authorization_fingerprint: str = Field(pattern=_SHA256)
    target_provider_kind: Literal["volcengine_ark_seedance"]
    target_model_id: str = Field(pattern=_SAFE_ID.pattern)
    target_request_fingerprint: str = Field(pattern=_SHA256)
    source_asset_id: str = Field(pattern=_SAFE_ID.pattern)
    source_registry_revision_id: str = Field(pattern=_SHA256)
    source_asset_sha256: str = Field(pattern=_SHA256)
    source_mime_type: Literal["video/mp4"]
    source_size_bytes: int = Field(strict=True, gt=0)
    source_width: int = Field(strict=True, gt=0)
    source_height: int = Field(strict=True, gt=0)
    source_fps: int = Field(strict=True, ge=24, le=60)
    source_duration_millis: int = Field(strict=True, gt=0)
    classification: Literal[
        "synthetic_non_identity_bearing_video",
        "ordinary_non_character_video",
    ]
    storage_provider: str = Field(pattern=_SAFE_ID.pattern)
    storage_account_scope: str = Field(pattern=_SAFE_ID.pattern)
    storage_bucket: str = Field(pattern=_SAFE_ID.pattern)
    storage_object_key_sha256: str = Field(pattern=_SHA256)
    storage_object_version_id: str = Field(pattern=_SAFE_ID.pattern)
    upload_origin: str
    read_origin: str
    remote_locator_sha256: str = Field(pattern=_SHA256)
    upload_response_identity_sha256: str = Field(pattern=_SHA256)
    readback_sha256: str = Field(pattern=_SHA256)
    readback_size_bytes: int = Field(strict=True, gt=0)
    accessibility_verification: Literal["exact_get"]
    credential_reference_kind: Literal["environment", "secret_store"]
    credential_reference_id: str = Field(pattern=_SAFE_ID.pattern)
    verified_at: datetime
    locator_not_after: datetime
    content_hash: str = Field(pattern=_SHA256)

    @field_validator("upload_origin", "read_origin")
    @classmethod
    def _origin_is_canonical(cls, value: str) -> str:
        return _canonical_https_origin(value)

    @model_validator(mode="after")
    def _validate_seal(self) -> "SeedanceLocalVideoMaterializationReceipt":
        if (
            self.verified_at.tzinfo is None
            or self.locator_not_after.tzinfo is None
            or self.locator_not_after <= self.verified_at
            or self.source_asset_sha256 != self.readback_sha256
            or self.source_size_bytes != self.readback_size_bytes
        ):
            raise ValueError("local video materialization exact-byte proof is invalid")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        )
        if self.content_hash != expected:
            raise ValueError("local video materialization receipt seal does not match")
        return self

    @classmethod
    def create(cls, **values: object) -> "SeedanceLocalVideoMaterializationReceipt":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.pop("content_hash", None)
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            candidate.model_dump(mode="json", exclude={"content_hash"}, warnings=False)
        )
        return cls.model_validate(data)


_REFERENCE_LEASE_TOKEN = object()


@dataclass(frozen=True, slots=True, init=False)
class SeedanceLocalVideoReferenceLease:
    materialization_receipt_id: str
    remote_locator_sha256: str
    read_origin: str
    issued_at: datetime
    not_after: datetime
    _url: str = field(repr=False)
    _durability_validator: Callable[[], bool] = field(repr=False)

    def __init__(
        self,
        token: object,
        *,
        receipt: SeedanceLocalVideoMaterializationReceipt,
        url: str,
        issued_at: datetime,
        not_after: datetime,
        durability_validator: Callable[[], bool],
    ) -> None:
        if token is not _REFERENCE_LEASE_TOKEN:
            raise TypeError("local video reference leases are minted only after exact readback")
        if (
            not_after <= issued_at
            or not_after - issued_at > _MAX_LEASE
            or not_after > receipt.locator_not_after
            or _url_origin(url) != receipt.read_origin
            or hashlib.sha256(url.encode()).hexdigest()
            != receipt.remote_locator_sha256
        ):
            raise ValueError("local video reference lease is invalid")
        object.__setattr__(self, "materialization_receipt_id", receipt.content_hash)
        object.__setattr__(self, "remote_locator_sha256", receipt.remote_locator_sha256)
        object.__setattr__(self, "read_origin", receipt.read_origin)
        object.__setattr__(self, "issued_at", issued_at)
        object.__setattr__(self, "not_after", not_after)
        object.__setattr__(self, "_url", url)
        object.__setattr__(self, "_durability_validator", durability_validator)

    def resolve(
        self, *, receipt: SeedanceLocalVideoMaterializationReceipt, now: datetime
    ) -> str:
        if (
            receipt.content_hash != self.materialization_receipt_id
            or receipt.remote_locator_sha256 != self.remote_locator_sha256
            or receipt.read_origin != self.read_origin
            or _url_origin(self._url) != self.read_origin
            or hashlib.sha256(self._url.encode()).hexdigest()
            != self.remote_locator_sha256
            or now.tzinfo is None
            or now < self.issued_at
            or now >= self.not_after
            or not self._durability_validator()
        ):
            raise ValueError("local video reference lease is not current")
        return self._url

    def __reduce__(self) -> object:
        raise TypeError("local video reference leases cannot be serialized")


@dataclass(frozen=True, slots=True)
class SeedanceLocalVideoMaterialization:
    receipt: SeedanceLocalVideoMaterializationReceipt
    lease: SeedanceLocalVideoReferenceLease


class SeedanceLocalVideoMaterializer:
    def __init__(
        self,
        *,
        transport: SeedanceLocalVideoMaterializationTransport,
        now: Callable[[], datetime],
    ) -> None:
        self._transport = transport
        self._now = now

    def materialize(
        self,
        *,
        binding: VideoMediaReferenceBinding,
        source_path: Path,
        preview: SeedanceLocalVideoMaterializationPreview,
        authorization: SeedanceLocalVideoMaterializationAuthorization,
        permit: object,
        grant: SeedanceLocalVideoUploadGrant,
    ) -> SeedanceLocalVideoMaterialization:
        now = self._now()
        _validate_authorization(preview=preview, authorization=authorization, now=now)
        if (
            type(binding) is not VideoMediaReferenceBinding
            or binding.kind != "video"
            or binding.role != "reference_video"
            or preview.source_asset_id != binding.asset_id
            or preview.source_asset_sha256 != binding.asset_sha256
            or preview.source_mime_type != binding.mime_type
            or preview.source_size_bytes != binding.size_bytes
            or preview.source_width != binding.width
            or preview.source_height != binding.height
            or preview.source_fps != binding.fps
            or preview.source_duration_millis != binding.duration_millis
        ):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "Local video materialization preview does not match the exact binding.",
            )
        if (
            grant.storage_provider != preview.storage_provider
            or grant.storage_account_scope != preview.storage_account_scope
            or grant.storage_bucket != preview.storage_bucket
            or grant.storage_object_key_sha256 != preview.storage_object_key_sha256
            or _url_origin(grant.upload_url) != preview.upload_origin
            or _url_origin(grant.read_url) != preview.read_origin
            or grant.not_after != preview.expires_at
            or now < preview.created_at
            or now >= preview.expires_at
        ):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "Local video upload grant does not match the exact preview.",
            )
        try:
            source_stat = source_path.stat()
            source_bytes = source_path.read_bytes()
        except OSError:
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "Local video source is unavailable.",
            ) from None
        if (
            not source_path.is_file()
            or source_stat.st_size != binding.size_bytes
            or len(source_bytes) != binding.size_bytes
            or hashlib.sha256(source_bytes).hexdigest() != binding.asset_sha256
            or not _is_mp4(source_bytes[:32], len(source_bytes))
        ):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "Local video source bytes do not match the exact MP4 binding.",
            )
        if type(permit) is not _SeedanceLocalVideoMaterializationPermit or not (
            permit._consume(
                preview_fingerprint=preview.preview_fingerprint,
                authorization_fingerprint=authorization.authorization_fingerprint,
            )
        ):
            raise _error(
                ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                "Local video materialization permit is invalid or already consumed.",
            )
        upload_request = SeedanceLocalVideoTransportRequest(
            method="PUT",
            url=grant.upload_url,
            headers={
                "content-type": binding.mime_type,
                "content-length": str(binding.size_bytes),
            },
        )
        try:
            upload_response = self._transport.upload(upload_request, source_bytes)
        except Exception:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                "Local video upload outcome is unknown after permit consumption.",
            ) from None
        if not 200 <= upload_response.status_code < 300:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "Local video object storage rejected the upload.",
            )
        etag = upload_response.headers.get("etag")
        version_header = _VERSION_HEADER_BY_PROVIDER.get(preview.storage_provider)
        version_id = (
            upload_response.headers.get(version_header)
            if version_header is not None
            else None
        )
        if not etag or not version_id or _SAFE_ID.fullmatch(version_id) is None:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                "Local video upload response identity is incomplete.",
            )
        read_request = SeedanceLocalVideoTransportRequest(
            method="GET", url=grant.read_url, headers={"accept": binding.mime_type}
        )
        digest = hashlib.sha256()
        size = 0
        prefix = bytearray()
        try:
            with self._transport.stream(read_request) as response:
                if not 200 <= response.status_code < 300:
                    raise ValueError("readback failed")
                response_mime_type = (
                    response.headers.get("content-type", "").split(";", 1)[0].strip()
                )
                if response_mime_type != binding.mime_type:
                    raise ValueError("readback content type changed")
                for chunk in response.iter_bytes():
                    if not isinstance(chunk, bytes) or not chunk:
                        continue
                    size += len(chunk)
                    if size > binding.size_bytes:
                        raise ValueError("readback size changed")
                    digest.update(chunk)
                    if len(prefix) < 32:
                        prefix.extend(chunk[: 32 - len(prefix)])
        except Exception:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                "Local video exact-byte readback failed after upload.",
            ) from None
        readback_sha256 = digest.hexdigest()
        if (
            size != binding.size_bytes
            or readback_sha256 != binding.asset_sha256
            or not _is_mp4(bytes(prefix), size)
        ):
            raise _error(
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                "Local video readback bytes changed after upload.",
            )
        verified_at = self._now()
        receipt = SeedanceLocalVideoMaterializationReceipt.create(
            preview_fingerprint=preview.preview_fingerprint,
            authorization_fingerprint=authorization.authorization_fingerprint,
            target_provider_kind=preview.target_provider_kind,
            target_model_id=preview.target_model_id,
            target_request_fingerprint=preview.target_request_fingerprint,
            source_asset_id=preview.source_asset_id,
            source_registry_revision_id=preview.source_registry_revision_id,
            source_asset_sha256=preview.source_asset_sha256,
            source_mime_type=preview.source_mime_type,
            source_size_bytes=preview.source_size_bytes,
            source_width=preview.source_width,
            source_height=preview.source_height,
            source_fps=preview.source_fps,
            source_duration_millis=preview.source_duration_millis,
            classification=preview.classification,
            storage_provider=preview.storage_provider,
            storage_account_scope=preview.storage_account_scope,
            storage_bucket=preview.storage_bucket,
            storage_object_key_sha256=preview.storage_object_key_sha256,
            storage_object_version_id=version_id,
            upload_origin=preview.upload_origin,
            read_origin=preview.read_origin,
            remote_locator_sha256=hashlib.sha256(grant.read_url.encode()).hexdigest(),
            upload_response_identity_sha256=hashlib.sha256(etag.encode()).hexdigest(),
            readback_sha256=readback_sha256,
            readback_size_bytes=size,
            accessibility_verification="exact_get",
            credential_reference_kind=preview.credential_reference_kind,
            credential_reference_id=preview.credential_reference_id,
            verified_at=verified_at,
            locator_not_after=grant.not_after,
        )
        lease = SeedanceLocalVideoReferenceLease(
            _REFERENCE_LEASE_TOKEN,
            receipt=receipt,
            url=grant.read_url,
            issued_at=verified_at,
            not_after=min(verified_at + _MAX_LEASE, grant.not_after),
            durability_validator=permit._durability_is_current,
        )
        return SeedanceLocalVideoMaterialization(receipt=receipt, lease=lease)


class SeedanceLocalVideoReferenceResolver:
    """Resolve exact local-video bytes through verified transient HTTPS leases."""

    def __init__(
        self,
        *,
        materializations: tuple[SeedanceLocalVideoMaterialization, ...],
        now: Callable[[], datetime],
    ) -> None:
        by_sha: dict[str, SeedanceLocalVideoMaterialization] = {}
        for materialized in materializations:
            if (
                type(materialized) is not SeedanceLocalVideoMaterialization
                or materialized.receipt.source_asset_sha256 in by_sha
            ):
                raise ValueError("local video materialization identities are ambiguous")
            by_sha[materialized.receipt.source_asset_sha256] = materialized
        self._by_sha = by_sha
        self._now = now

    def validate_request(
        self, request: VideoGenerationRequest | ResolvedVideoGenerationRequest
    ) -> None:
        videos = tuple(
            binding for binding in request.media_bindings if binding.kind == "video"
        )
        if not videos:
            raise ValueError("local video resolver requires a video reference")
        for binding in videos:
            materialized = self._by_sha.get(binding.asset_sha256)
            if materialized is None:
                raise ValueError("local video input has no exact materialization")
            receipt = materialized.receipt
            if (
                receipt.target_provider_kind != request.provider_kind
                or receipt.target_model_id != request.model_id
                or receipt.target_request_fingerprint != request.request_input_hash
            ):
                raise ValueError(
                    "local video materialization targets a different request"
                )

    def __call__(self, binding: VideoMediaReferenceBinding) -> str:
        if (
            type(binding) is not VideoMediaReferenceBinding
            or binding.kind != "video"
            or binding.role != "reference_video"
        ):
            raise ValueError("local video references only support reference video")
        materialized = self._by_sha.get(binding.asset_sha256)
        if materialized is None:
            raise ValueError("local video input has no exact materialization")
        receipt = materialized.receipt
        if (
            receipt.source_asset_id != binding.asset_id
            or receipt.source_size_bytes != binding.size_bytes
            or receipt.source_mime_type != binding.mime_type
            or receipt.source_width != binding.width
            or receipt.source_height != binding.height
            or receipt.source_fps != binding.fps
            or receipt.source_duration_millis != binding.duration_millis
        ):
            raise ValueError("local video materialization does not match exact input")
        return materialized.lease.resolve(receipt=receipt, now=self._now())

    def verified_nominal_duration_millis(
        self,
        binding: VideoMediaReferenceBinding,
        *,
        family_limit_millis: int,
    ) -> int | None:
        materialized = self._by_sha.get(binding.asset_sha256)
        if materialized is None:
            return None
        duration = materialized.receipt.source_duration_millis
        if duration != binding.duration_millis or duration > family_limit_millis:
            return None
        self(binding)
        return duration


__all__ = [
    "HttpxSeedanceLocalVideoMaterializationTransport",
    "SeedanceLocalVideoMaterialization",
    "SeedanceLocalVideoMaterializationAuthorization",
    "SeedanceLocalVideoMaterializationPreview",
    "SeedanceLocalVideoMaterializationReceipt",
    "SeedanceLocalVideoMaterializationTransport",
    "SeedanceLocalVideoMaterializer",
    "SeedanceLocalVideoReferenceLease",
    "SeedanceLocalVideoReferenceResolver",
    "SeedanceLocalVideoStreamResponse",
    "SeedanceLocalVideoTransportRequest",
    "SeedanceLocalVideoUploadGrant",
    "SeedanceLocalVideoUploadResponse",
    "issue_seedance_local_video_materialization_permit",
]
