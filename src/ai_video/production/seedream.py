"""One original Ark Seedream PNG through the shared paid image owner."""

from __future__ import annotations

import base64
import hashlib
import json
import time
from contextlib import contextmanager
from datetime import UTC, datetime

import httpx
from pydantic import ConfigDict, Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._state_commit_contracts import _DurablePaidProviderSubmitPermit
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel, ToolIdentity
from ai_video.production.image import (
    ImageGenerationRequest, ImageGenerationPreview, ImageGenerationAuthorization,
    ImageProviderResult, ImageLocalResourceEvidence, _measure_png,
)
from ai_video.production.paid_provider import (
    PaidProviderCallPreview, PaidProviderEgressItem, PaidProviderGateReceipt,
    PaidProviderSubmitReceipt, PaidProviderSubmitOutcome, SecretReference,
    validate_paid_provider_authorization,
)
from ai_video.production.remote_image import RemoteImageEvidence, remote_image_permit_binding


SEEDREAM_MODEL = "doubao-seedream-5-0-pro-260628"
SEEDREAM_ORIGIN = "https://ark.cn-beijing.volces.com"
SEEDREAM_URL = SEEDREAM_ORIGIN + "/api/v3/images/generations"
SEEDREAM_VERSION = "seedream-original-png/1"
MAX_JSON_BYTES = 40 * 1024 * 1024


class SeedreamProfile(StrictModel):
    """Operator upper bound, never a market quote or account entitlement."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    upper_bound_microunits: int = Field(strict=True, gt=0)
    observed_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def _validity(self):
        if (self.observed_at.tzinfo is None or self.expires_at.tzinfo is None
                or not 0 < (self.expires_at - self.observed_at).total_seconds() <= 21600):
            raise ValueError("Seedream operator bound needs an aware, bounded validity window")
        return self

    @property
    def content_hash(self):
        return canonical_sha256({"schema": SEEDREAM_VERSION, "model": SEEDREAM_MODEL,
            "origin": SEEDREAM_ORIGIN, **self.model_dump(mode="json")})


def _error(code, message):
    return AiVideoError(code=code, user_message=message, retryable=False)


def _invalid():
    return _error(ErrorCode.IMAGE_REQUEST_INVALID, "Seedream request or exact authority is invalid.")


def _unknown():
    return _error(ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN,
        "Seedream image outcome is unknown; automatic retry is forbidden.")


def _rejected():
    return _error(ErrorCode.IMAGE_PROVIDER_FAILED, "Seedream image submission was rejected.")


class HttpxSeedreamImageTransport:
    """Exact endpoint; no redirects, inherited credentials, or transport retry."""

    def __init__(self, *, client=None):
        self._client = client or httpx.Client(timeout=180.0, follow_redirects=False)
        self._owns_client = client is None

    @contextmanager
    def stream(self, method, url, *, headers, content, follow_redirects):
        normalized = {key.lower(): value for key, value in headers.items()}
        authorization = normalized.get("authorization", "")
        token = authorization.removeprefix("Bearer ")
        if (method != "POST" or url != SEEDREAM_URL or follow_redirects is not False
                or len(headers) != 2 or set(normalized) != {"authorization", "content-type"}
                or not authorization.startswith("Bearer ") or not token
                or any(c.isspace() for c in token) or normalized["content-type"] != "application/json"
                or not isinstance(content, bytes) or len(content) > MAX_JSON_BYTES):
            raise ValueError("Seedream transport request is invalid")
        response = None
        try:
            request = httpx.Request("POST", SEEDREAM_URL, headers=headers, content=content,
                extensions={"timeout": httpx.Timeout(180.0).as_dict()})
            response = self._client.send(request, auth=None, follow_redirects=False, stream=True)
            yield response
        except httpx.HTTPError:
            raise RuntimeError("Seedream image transport failed") from None
        finally:
            if response is not None:
                response.close()

    def close(self):
        if self._owns_client:
            self._client.close()


class SeedreamImageProvider:
    def __init__(self, profile, transport, credential, *, now=None):
        self._profile = SeedreamProfile.model_validate_json(profile.model_dump_json())
        self._transport = transport
        self._credential = credential
        self._now = now or (lambda: datetime.now(UTC))

    def _settings(self, request):
        return dict(model=SEEDREAM_MODEL, size=f"{request.parameters.width}x{request.parameters.height}",
            output_format="png", response_format="b64_json", watermark=True)

    def _check(self, request):
        try:
            checked = ImageGenerationRequest.model_validate_json(request.model_dump_json())
            now = self._now()
            width, height = checked.parameters.width, checked.parameters.height
            if (checked != request or checked.provider_kind != "seedream" or checked.model_id != SEEDREAM_MODEL
                    or checked.references or checked.negative_prompt_text or checked.parameters.seed is not None
                    or checked.parameters.output_format != "png" or width is None or height is None
                    or not 921600 <= width * height <= 4624220 or not 1/16 <= width/height <= 16
                    or not self._profile.observed_at <= now < self._profile.expires_at):
                raise ValueError("unsupported request")
            return checked
        except Exception:
            raise _invalid() from None

    def preview(self, request):
        request = self._check(request)
        items = []
        for name, raw, mime in (("prompt", request.prompt_text.encode(), "text/plain"),
                ("settings", json.dumps(self._settings(request), sort_keys=True,
                    separators=(",", ":")).encode(), "application/json")):
            items.append(PaidProviderEgressItem(item_id=name, sha256=hashlib.sha256(raw).hexdigest(),
                size_bytes=len(raw), mime_type=mime, purpose=name))
        paid = PaidProviderCallPreview.create(attempt_id=request.attempt_id, operation="image_generation",
            provider_kind="seedream", model_id=SEEDREAM_MODEL, request_fingerprint=request.request_fingerprint,
            billing_mode="remote_metered", currency="CNY",
            estimated_cost_upper_bound_microunits=self._profile.upper_bound_microunits,
            destination=SEEDREAM_ORIGIN, method="POST", egress_items=tuple(items),
            retention_mode="provider_standard", provider_policy_snapshot_id=self._profile.content_hash,
            secret_reference=SecretReference(kind="secret_store", reference_id="ARK_API_KEY"))
        return ImageGenerationPreview.create(request=request, reference_total_bytes=0, remote_call=paid)

    def preflight(self, request, authorization):
        try:
            preview = self.preview(request)
            auth = ImageGenerationAuthorization.model_validate_json(authorization.model_dump_json())
            if (auth != authorization or auth.local_only or auth.remote_binding is None
                    or auth.request_fingerprint != request.request_fingerprint
                    or auth.preview_fingerprint != preview.preview_fingerprint
                    or auth.remote_binding.preview != preview.remote_call):
                raise ValueError("authority mismatch")
            validate_paid_provider_authorization(preview.remote_call, auth.remote_binding.authorization,
                now=self._now())
            return preview
        except Exception:
            raise _invalid() from None

    def generate(self, request, authorization, permit, *, gate_receipt):
        started = time.monotonic()
        self.preflight(request, authorization)
        remote = authorization.remote_binding
        try:
            gate = PaidProviderGateReceipt.model_validate_json(gate_receipt.model_dump_json())
            if (gate != gate_receipt or gate.preview != remote.preview or gate.authorization != remote.authorization
                    or type(permit) is not _DurablePaidProviderSubmitPermit):
                raise ValueError("gate mismatch")
            # Resolve only the injected exact supplier; failures here have no network effect.
            key = self._credential()
            if not isinstance(key, str) or not key or any(c.isspace() for c in key):
                raise ValueError("credential unavailable")
            self.preflight(request, authorization)
            body = json.dumps({**self._settings(request), "prompt": request.prompt_text},
                ensure_ascii=False, separators=(",", ":")).encode()
            if len(body) > MAX_JSON_BYTES or not permit._consume_paid_provider_operation_permit(
                    **remote_image_permit_binding(remote)):
                raise ValueError("exact one-use permit required")
        except Exception:
            raise _rejected() from None
        try:
            with self._transport.stream("POST", SEEDREAM_URL,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    content=body, follow_redirects=False) as response:
                if response.status_code != 200:
                    if 400 <= response.status_code < 500 and response.status_code not in {408, 425, 429}:
                        raise _rejected()
                    raise _unknown()
                raw = bytearray()
                for chunk in response.iter_bytes():
                    if not isinstance(chunk, bytes) or len(raw) + len(chunk) > MAX_JSON_BYTES:
                        raise _unknown()
                    raw.extend(chunk)
            document = json.loads(raw)
            if document.get("model") != SEEDREAM_MODEL or len(document.get("data", ())) != 1:
                raise ValueError("unexpected response identity")
            row = document["data"][0]
            wire = base64.b64decode(row["b64_json"], validate=True)
            measured = _measure_png(wire)
            if (measured.width != request.parameters.width or measured.height != request.parameters.height
                    or ("size" in row and row["size"] != self._settings(request)["size"])):
                raise ValueError("unexpected output geometry")
            # Content identity, not an invented server job ID.
            effect_id = "seedream-content:" + hashlib.sha256(
                (request.request_fingerprint + measured.sha256).encode()).hexdigest()
            receipt = PaidProviderSubmitReceipt.create(attempt_id=request.attempt_id,
                request_fingerprint=request.request_fingerprint, preview_fingerprint=remote.preview.preview_fingerprint,
                gate_receipt_fingerprint=gate.gate_receipt_fingerprint, reservation_id=gate.reservation_id,
                outcome=PaidProviderSubmitOutcome.ACCEPTED, external_effect_id=effect_id, recorded_at=self._now())
            return ImageProviderResult.create(request=request, authorization=authorization,
                image_bytes=wire, wire_image_bytes=wire, content_type="image/png", provider_request_id=effect_id,
                adapter=ToolIdentity(name="seedream", version=SEEDREAM_VERSION),
                resource_evidence=ImageLocalResourceEvidence(
                    elapsed_milliseconds=max(0, int((time.monotonic()-started)*1000)), device_kind="unknown"),
                remote_evidence=RemoteImageEvidence(submit_receipt=receipt, wire_sha256=measured.sha256,
                    wire_size_bytes=len(wire), wire_mime_type="image/png", conversion="identity-png"))
        except AiVideoError as exc:
            if exc.code in {ErrorCode.IMAGE_PROVIDER_FAILED, ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN}:
                raise
            raise _unknown() from None
        except Exception:
            raise _unknown() from None
