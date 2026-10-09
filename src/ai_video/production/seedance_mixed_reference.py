"""Compose attested inline images with exact-readback HTTPS video references.

This is input materialization, not Ark asset-library admission or output
activation. Locators remain process-local and never enter durable evidence.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable
from urllib.parse import urlsplit

from ai_video.production.models import ActorIdentity, AssetType
from ai_video.production.seedance_asset import (
    SeedanceSyntheticImageReferenceResolver, _invalid, _reopen_registry_snapshot,
)
from ai_video.production.video import VideoImageReferenceBinding, VideoMediaReferenceBinding

_TOKEN = object()


@dataclass(frozen=True, repr=False)
class _VerifiedVideo:
    binding: VideoMediaReferenceBinding
    registry_sha256: str
    locator_sha256: str
    verified_at: datetime
    not_after: datetime
    attested_by: ActorIdentity
    _url: str = field(repr=False)
    _token: object = field(repr=False)

    def __reduce__(self):
        raise TypeError("verified reference locators cannot be serialized")

    def evidence(self) -> dict:
        return {"binding": self.binding.model_dump(mode="json"),
                "registry_sha256": self.registry_sha256,
                "locator_sha256": self.locator_sha256,
                "verified_at": self.verified_at.isoformat(),
                "not_after": self.not_after.isoformat(),
                "attested_by": self.attested_by.model_dump(mode="json"),
                "verification": "exact_https_get"}


def verify_reference_video(*, binding: VideoMediaReferenceBinding, url: str,
                           allowed_origin: str, source_bytes: bytes,
                           registry_snapshot_bytes: bytes, attested_by: ActorIdentity,
                           locator_not_after: datetime, transport, now: Callable[[], datetime]):
    """Verify one already-uploaded, authorized video. No upload or retry."""
    from ai_video.production.seedance_local_video import SeedanceLocalVideoTransportRequest

    parsed = urlsplit(url)
    if (type(binding) is not VideoMediaReferenceBinding or binding.kind != "video"
            or binding.role != "reference_video" or binding.mime_type != "video/mp4"
            or attested_by.actor_kind != "human"
            or parsed.scheme != "https" or parsed.username or parsed.password
            or parsed.fragment or not parsed.path
            or f"https://{parsed.netloc}" != allowed_origin):
        raise _invalid("Seedance reference video identity or origin is invalid.")
    if (hashlib.sha256(source_bytes).hexdigest() != binding.asset_sha256
            or len(source_bytes) != binding.size_bytes
            or source_bytes[4:8] != b"ftyp"):
        raise _invalid("Seedance reference video source bytes do not match.")
    registry = _reopen_registry_snapshot(registry_snapshot_bytes)
    matches = [r for r in registry.assets if r.asset_id == binding.asset_id]
    if len(matches) != 1:
        raise _invalid("Seedance reference video is absent from the exact Registry.")
    record = matches[0]
    if (record.asset_type is not AssetType.VIDEO or record.sha256 != binding.asset_sha256
            or record.size_bytes != binding.size_bytes or record.mime_type != binding.mime_type
            or record.width != binding.width or record.height != binding.height
            or record.duration_seconds is None
            or round(record.duration_seconds * 1000) != binding.duration_millis):
        raise _invalid("Seedance reference video Registry identity does not match.")
    started = now()
    if (started.tzinfo is None or locator_not_after.tzinfo is None
            or locator_not_after <= started):
        raise _invalid("Seedance reference video locator is expired.")
    digest, size = hashlib.sha256(), 0
    try:
        request = SeedanceLocalVideoTransportRequest(method="GET", url=url,
                                                     headers={"accept": "video/mp4"})
        with transport.stream(request) as response:
            if (response.status_code != 200
                    or response.headers.get("content-type", "").split(";", 1)[0] != "video/mp4"):
                raise ValueError("reference readback failed")
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > binding.size_bytes:
                    raise ValueError("reference readback exceeds exact source")
                digest.update(chunk)
    except Exception:
        raise _invalid("Seedance reference video exact readback failed.") from None
    if size != binding.size_bytes or digest.hexdigest() != binding.asset_sha256:
        raise _invalid("Seedance reference video readback bytes changed.")
    verified_at = now()
    if verified_at >= locator_not_after:
        raise _invalid("Seedance reference video locator expired during verification.")
    return _VerifiedVideo(binding, hashlib.sha256(registry_snapshot_bytes).hexdigest(),
                          hashlib.sha256(url.encode()).hexdigest(), verified_at,
                          min(locator_not_after, verified_at + timedelta(minutes=5)),
                          attested_by, url, _TOKEN)


class SeedanceMixedReferenceResolver:
    """An exact mixed input set; the image policy pins the full paid preview."""

    def __init__(self, *, images: SeedanceSyntheticImageReferenceResolver,
                 videos: tuple[_VerifiedVideo, ...], now: Callable[[], datetime]):
        if type(images) is not SeedanceSyntheticImageReferenceResolver or not videos:
            raise _invalid("Seedance mixed references require sealed images and videos.")
        if any(type(v) is not _VerifiedVideo or v._token is not _TOKEN for v in videos):
            raise _invalid("Seedance mixed video reference has no readback proof.")
        if len({v.binding.asset_id for v in videos}) != len(videos):
            raise _invalid("Seedance mixed video references are ambiguous.")
        self._images, self._videos, self._now = images, videos, now

    def validate_submit(self, request, preview, authorization):
        bindings = tuple(v.binding for v in self._videos)
        scope = request.activation_scope
        if (scope is None or any(v.registry_sha256 != scope.request.base_registry.file_sha256
                                for v in self._videos)):
            raise _invalid("Seedance mixed video references target another Registry.")
        self._images.validate_submit(request, preview, authorization,
                                     verified_media_bindings=bindings)
        for binding in bindings:
            self(binding)

    def __call__(self, binding):
        if type(binding) is VideoImageReferenceBinding:
            return self._images(binding)
        for video in self._videos:
            if video.binding == binding:
                if not video.verified_at <= self._now() < video.not_after:
                    raise _invalid("Seedance verified video reference is expired.")
                return video._url
        raise _invalid("Seedance mixed input has no exact reference binding.")
