"""Compose attested images, original audio, and exact-readback HTTPS video.

This is input materialization, not Ark asset-library admission or output
activation. Locators remain process-local and never enter durable evidence.
"""
from __future__ import annotations

import base64
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
class _VerifiedAudio:
    binding: VideoMediaReferenceBinding
    registry_sha256: str
    attested_by: ActorIdentity
    _bytes: bytes = field(repr=False)
    _token: object = field(repr=False)

    def __reduce__(self):
        raise TypeError("verified reference audio cannot be serialized")

    def evidence(self) -> dict:
        return {"binding": self.binding.model_dump(mode="json"),
                "registry_sha256": self.registry_sha256,
                "attested_by": self.attested_by.model_dump(mode="json"),
                "verification": "exact_registry_bytes", "transport": "inline_base64"}


def verify_reference_audio(*, binding: VideoMediaReferenceBinding, source_bytes: bytes,
                           registry_snapshot_bytes: bytes, attested_by: ActorIdentity):
    """Pin original WAV/MP3 bytes to an exact Registry; no upload or reencoding.

    Duration comes from the measured Registry asset, not from this signature
    check. Selected capability and full paid egress remain submit prerequisites.
    """
    if (type(binding) is not VideoMediaReferenceBinding or binding.kind != "audio"
            or binding.role != "reference_audio" or attested_by.actor_kind != "human"
            or binding.mime_type not in {"audio/wav", "audio/mpeg"}
            or type(source_bytes) is not bytes
            or len(source_bytes) != binding.size_bytes
            or hashlib.sha256(source_bytes).hexdigest() != binding.asset_sha256):
        raise _invalid("Seedance reference audio source identity does not match.")
    is_wav = source_bytes[:4] == b"RIFF" and source_bytes[8:12] == b"WAVE"
    is_mp3 = (source_bytes.startswith(b"ID3") or
              len(source_bytes) >= 2 and source_bytes[0] == 255 and source_bytes[1] & 224 == 224)
    if not (is_wav if binding.mime_type == "audio/wav" else is_mp3):
        raise _invalid("Seedance reference audio format does not match.")
    registry = _reopen_registry_snapshot(registry_snapshot_bytes)
    matches = [r for r in registry.assets if r.asset_id == binding.asset_id]
    if len(matches) != 1:
        raise _invalid("Seedance reference audio is absent from the exact Registry.")
    record = matches[0]
    if (record.asset_type not in {AssetType.VOICE, AssetType.MUSIC, AssetType.SFX}
            or record.sha256 != binding.asset_sha256 or record.size_bytes != binding.size_bytes
            or record.mime_type != binding.mime_type or record.duration_seconds is None
            or round(record.duration_seconds * 1000) != binding.duration_millis):
        raise _invalid("Seedance reference audio Registry identity does not match.")
    return _VerifiedAudio(binding, hashlib.sha256(registry_snapshot_bytes).hexdigest(),
                          attested_by, source_bytes, _TOKEN)


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
                 videos: tuple[_VerifiedVideo, ...] = (),
                 audios: tuple[_VerifiedAudio, ...] = (), now: Callable[[], datetime]):
        if type(images) is not SeedanceSyntheticImageReferenceResolver or not (videos or audios):
            raise _invalid("Seedance mixed references require sealed images and media.")
        if any(type(v) is not _VerifiedVideo or v._token is not _TOKEN for v in videos):
            raise _invalid("Seedance mixed video reference has no readback proof.")
        if any(type(a) is not _VerifiedAudio or a._token is not _TOKEN for a in audios):
            raise _invalid("Seedance mixed audio reference has no exact Registry proof.")
        media = (*videos, *audios)
        if len({v.binding.asset_id for v in media}) != len(media):
            raise _invalid("Seedance mixed media references are ambiguous.")
        self._images, self._videos, self._audios, self._now = images, videos, audios, now

    def validate_submit(self, request, preview, authorization):
        media = (*self._videos, *self._audios)
        verified = {v.binding.asset_id: v.binding for v in media}
        bindings = tuple(verified.get(b.asset_id) for b in request.media_bindings)
        if len(bindings) != len(verified) or any(b is None for b in bindings):
            raise _invalid("Seedance mixed reference set does not match the request.")
        scope = request.activation_scope
        if (scope is None or any(v.registry_sha256 != scope.request.base_registry.file_sha256
                                for v in media)):
            raise _invalid("Seedance mixed media references target another Registry.")
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
        for audio in self._audios:
            if audio.binding == binding:
                subtype = "mp3" if binding.mime_type == "audio/mpeg" else "wav"
                return f"data:audio/{subtype};base64,{base64.b64encode(audio._bytes).decode('ascii')}"
        raise _invalid("Seedance mixed input has no exact reference binding.")
