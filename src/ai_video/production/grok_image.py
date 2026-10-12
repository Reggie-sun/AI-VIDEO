"""Subscription-bound synchronous Grok multi-image editing."""

from __future__ import annotations

import base64
import hashlib
import json
import time
import warnings
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from datetime import UTC, datetime
from io import BytesIO
from typing import Protocol

import httpx
from PIL import Image

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._state_commit_contracts import _DurablePaidProviderSubmitPermit
from ai_video.production.artifact_contracts import ToolIdentity
from ai_video.production.grok_auth import GrokCredential, SECRET_REFERENCE
from ai_video.production.grok_image_bytes import decode_grok_image
from ai_video.production.grok_profile import GROK_IMAGE_MODEL, GROK_PROFILE_VERSION, GrokProviderProfile
from ai_video.production.grok_subscription import (
    GROK_CREDENTIAL_REFERENCE,
    GROK_SUBSCRIPTION_ORIGIN,
    GrokSubscriptionBinding,
    reject_unverified_included_only,
    require_current_subscription,
)
from ai_video.production.image import (
    ImageGenerationAuthorization,
    ImageGenerationPreview,
    ImageGenerationRequest,
    ImageLocalResourceEvidence,
    ImageProviderResult,
    ImageReferenceBinding,
)
from ai_video.production.paid_provider import (
    PaidProviderCallPreview,
    PaidProviderEgressItem,
    PaidProviderGateReceipt,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
    validate_paid_provider_authorization,
)
from ai_video.production.remote_image import (
    RemoteImageAuthorization,
    RemoteImageEvidence,
    remote_image_permit_binding,
)


GROK_IMAGE_EDIT_URL = GROK_SUBSCRIPTION_ORIGIN + "/v1/images/edits"
MAX_GROK_IMAGE_JSON_BYTES = 40 * 1024 * 1024
MAX_GROK_REFERENCE_PIXELS = 40_000_000


class _ImageResponse(Protocol):
    status_code: int

    def iter_bytes(self) -> Iterator[bytes]: ...


class _ImageTransport(Protocol):
    def stream(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        content: bytes,
        follow_redirects: bool,
    ) -> AbstractContextManager[_ImageResponse]: ...


class HttpxGrokImageTransport:
    """Exact-endpoint image transport that ignores injected client credentials."""

    def __init__(self, *, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=30.0, follow_redirects=False)
        self._owns_client = client is None
        self._timeout = httpx.Timeout(30.0)

    @contextmanager
    def stream(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        content: bytes,
        follow_redirects: bool,
    ) -> Iterator[_ImageResponse]:
        normalized = {key.lower(): value for key, value in headers.items()}
        authorization = normalized.get("authorization", "")
        token = authorization.removeprefix("Bearer ")
        if (
            method != "POST"
            or url != GROK_IMAGE_EDIT_URL
            or follow_redirects is not False
            or len(headers) != 2
            or set(normalized) != {"authorization", "content-type"}
            or not authorization.startswith("Bearer ")
            or not token
            or any(char.isspace() for char in token)
            or normalized.get("content-type") != "application/json"
            or not isinstance(content, bytes)
            or len(content) > MAX_GROK_IMAGE_JSON_BYTES
        ):
            raise ValueError("Grok image transport request is invalid.")
        try:
            exact = httpx.Request(
                "POST",
                GROK_IMAGE_EDIT_URL,
                headers={
                    "Authorization": authorization,
                    "Content-Type": "application/json",
                },
                content=content,
                extensions={"timeout": self._timeout.as_dict()},
            )
            response = self._client.send(
                exact, auth=None, follow_redirects=False, stream=True
            )
        except Exception:
            raise RuntimeError("Grok image transport failed.") from None
        try:
            try:
                yield response
            except httpx.HTTPError:
                raise RuntimeError("Grok image transport failed.") from None
        finally:
            try:
                response.close()
            except Exception:
                pass

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


ImageResolver = Callable[[ImageReferenceBinding], bytes]
CredentialSupplier = Callable[[str], GrokCredential]
SubscriptionGuard = Callable[[GrokSubscriptionBinding], object]


def _error(code: ErrorCode, message: str) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, retryable=False)


def _request_invalid() -> AiVideoError:
    return _error(ErrorCode.IMAGE_REQUEST_INVALID, "Grok image request does not match the supported profile.")


def _known_failure() -> AiVideoError:
    return _error(ErrorCode.IMAGE_PROVIDER_FAILED, "Grok image submission was rejected before producing an image.")


def _unknown_outcome() -> AiVideoError:
    return _error(ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN,
        "Grok image submission outcome is unknown; automatic retry is forbidden.")


class GrokImageProvider:
    """One-shot multi-image editor; only a durable Production paid permit can submit."""

    def __init__(
        self,
        profile: GrokProviderProfile,
        transport: _ImageTransport,
        credential: CredentialSupplier,
        image_resolver: ImageResolver,
        subscription_guard: SubscriptionGuard = reject_unverified_included_only,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._profile = profile
        self._transport = transport
        self._credential = credential
        self._image_resolver = image_resolver
        self._subscription_guard = subscription_guard
        self._now = now or (lambda: datetime.now(UTC))

    def preview(
        self,
        request: ImageGenerationRequest,
        subscription_binding: GrokSubscriptionBinding,
    ) -> ImageGenerationPreview:
        checked, binding, references = self._prepare(request, subscription_binding)
        return self._build_preview(checked, binding, references)

    def _build_preview(self, checked, binding, references) -> ImageGenerationPreview:
        items = [
            PaidProviderEgressItem(
                item_id="prompt",
                sha256=hashlib.sha256(checked.prompt_text.encode("utf-8")).hexdigest(),
                size_bytes=len(checked.prompt_text.encode("utf-8")),
                mime_type="text/plain",
                purpose="prompt",
            ),
            PaidProviderEgressItem(
                item_id="settings",
                sha256=hashlib.sha256(self._settings_bytes()).hexdigest(),
                size_bytes=len(self._settings_bytes()),
                mime_type="application/json",
                purpose="settings",
            ),
        ]
        items.extend(
            PaidProviderEgressItem(
                item_id=f"reference-{index}-{reference.role}",
                sha256=hashlib.sha256(raw).hexdigest(),
                size_bytes=len(raw),
                mime_type=mime,
                purpose="reference",
            )
            for index, (reference, raw, mime) in enumerate(references)
        )
        paid_preview = PaidProviderCallPreview.create(
            attempt_id=checked.attempt_id,
            operation="image_generation",
            provider_kind="grok",
            model_id=GROK_IMAGE_MODEL,
            request_fingerprint=checked.request_fingerprint,
            billing_mode="remote_subscription",
            subscription_binding=binding,
            currency="USD",
            estimated_cost_upper_bound_microunits=0,
            destination=GROK_SUBSCRIPTION_ORIGIN,
            method="POST",
            egress_items=tuple(items),
            retention_mode="provider_standard",
            provider_policy_snapshot_id=self._profile.pointer().profile_sha256,
            secret_reference=SECRET_REFERENCE,
        )
        return ImageGenerationPreview.create(
            request=checked,
            reference_total_bytes=sum(len(raw) for _reference, raw, _mime in references),
            remote_call=paid_preview,
        )

    def preflight(
        self,
        request: ImageGenerationRequest,
        authorization: ImageGenerationAuthorization,
    ) -> ImageGenerationPreview:
        checked_request, checked_authorization, remote, image_preview, _references = self._preflight_data(
            request, authorization,
        )
        del checked_request, checked_authorization, remote
        return image_preview

    def generate(
        self,
        request: ImageGenerationRequest,
        authorization: ImageGenerationAuthorization,
        permit: object,
        *,
        gate_receipt: PaidProviderGateReceipt,
    ) -> ImageProviderResult:
        started = time.monotonic()
        try:
            checked_request, checked_authorization, remote, _image_preview, references = self._preflight_data(
                request, authorization,
            )
            gate = PaidProviderGateReceipt.model_validate_json(gate_receipt.model_dump_json())
            if gate != gate_receipt or (
                gate.preview != remote.preview
                or gate.authorization != remote.authorization
                or gate.preview.request_fingerprint != checked_request.request_fingerprint
            ):
                raise _known_failure()
            payload = {
                "model": GROK_IMAGE_MODEL,
                "prompt": checked_request.prompt_text,
                "images": [
                    {
                        "type": "image_url",
                        "url": f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}",
                    }
                    for _reference, raw, mime in references
                ],
                "response_format": "b64_json",
                "n": 1,
                "resolution": self._profile.image_resolution,
            }
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            if len(body) > MAX_GROK_IMAGE_JSON_BYTES:
                raise _known_failure()
            # Recheck quota and time after reference resolution and immediately before permit consumption.
            self._check_subscription(remote.preview.subscription_binding)
            validate_paid_provider_authorization(remote.preview, remote.authorization, now=self._current_time())
            if type(permit) is not _DurablePaidProviderSubmitPermit:
                raise _known_failure()
            binding = remote_image_permit_binding(remote)
            binding["authorization_fingerprint"] = remote.authorization.authorization_fingerprint
            if not permit._consume_paid_provider_operation_permit(**binding):
                raise _known_failure()
        except AiVideoError as exc:
            if exc.code in {ErrorCode.IMAGE_PROVIDER_FAILED, ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN}:
                raise
            raise _known_failure() from None
        except Exception:
            raise _known_failure() from None

        # A credential failure after consuming the durable one-use permit is conservatively unknown.
        try:
            credential = self._credential(self._profile.account_fingerprint)
            now = self._current_time()
            if (
                not isinstance(credential, GrokCredential)
                or credential.account_fingerprint != self._profile.account_fingerprint
                or credential.secret_reference != SECRET_REFERENCE
                or not isinstance(credential.access_token, str)
                or not credential.access_token.strip()
                or credential.expires_at.tzinfo is None
                or credential.expires_at.utcoffset() is None
                or now >= credential.expires_at
            ):
                raise ValueError("credential invalid")
        except Exception:
            raise _unknown_outcome() from None

        # Credential lookup may take time. Revalidate quota, access, and token expiry
        # after it and before the first network side effect; this path is known-no-effect.
        try:
            self._check_subscription(remote.preview.subscription_binding)
            now = self._current_time()
            validate_paid_provider_authorization(remote.preview, remote.authorization, now=now)
            if now >= credential.expires_at:
                raise ValueError("credential expired")
        except Exception:
            raise _known_failure() from None

        try:
            with self._transport.stream(
                "POST",
                GROK_IMAGE_EDIT_URL,
                headers={
                    "Authorization": f"Bearer {credential.access_token}",
                    "Content-Type": "application/json",
                },
                content=body,
                follow_redirects=False,
            ) as response:
                status = response.status_code
                if status != 200:
                    if 400 <= status < 500 and status not in {408, 425, 429}:
                        raise _known_failure()
                    raise _unknown_outcome()
                response_body = self._read_bounded_response(response)
        except AiVideoError:
            raise
        except Exception:
            raise _unknown_outcome() from None

        try:
            document = json.loads(response_body)
            if isinstance(document, dict) and document.get("model", GROK_IMAGE_MODEL) != GROK_IMAGE_MODEL:
                raise ValueError("image response model does not match the request")
            rows = document.get("data") if isinstance(document, dict) else None
            if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
                raise ValueError("invalid image response")
            encoded = rows[0].get("b64_json")
            if not isinstance(encoded, str) or not encoded or len(encoded) > MAX_GROK_IMAGE_JSON_BYTES:
                raise ValueError("invalid image response")
            wire = base64.b64decode(encoded, validate=True)
            png, wire_mime, conversion = decode_grok_image(wire)
            wire_sha = hashlib.sha256(wire).hexdigest()
            # This is output content identity, not a server-issued request or job ID.
            effect_digest = hashlib.sha256(
                f"{checked_request.request_fingerprint}{wire_sha}".encode("ascii")
            ).hexdigest()
            effect_id = f"grok-content:{effect_digest}"
            recorded_at = self._current_time()
            receipt = PaidProviderSubmitReceipt.create(
                attempt_id=checked_request.attempt_id,
                request_fingerprint=checked_request.request_fingerprint,
                preview_fingerprint=remote.preview.preview_fingerprint,
                gate_receipt_fingerprint=gate.gate_receipt_fingerprint,
                reservation_id=gate.reservation_id,
                outcome=PaidProviderSubmitOutcome.ACCEPTED,
                external_effect_id=effect_id,
                recorded_at=recorded_at,
            )
            evidence = RemoteImageEvidence(
                submit_receipt=receipt,
                wire_sha256=wire_sha,
                wire_size_bytes=len(wire),
                wire_mime_type=wire_mime,
                conversion=conversion,
            )
            elapsed = max(0, int((time.monotonic() - started) * 1000))
            return ImageProviderResult.create(
                request=checked_request,
                authorization=checked_authorization,
                image_bytes=png,
                content_type="image/png",
                provider_request_id=effect_id,
                adapter=ToolIdentity(name="grok", version=GROK_PROFILE_VERSION),
                resource_evidence=ImageLocalResourceEvidence(
                    elapsed_milliseconds=elapsed,
                    device_kind="unknown",
                ),
                remote_evidence=evidence,
                wire_image_bytes=wire,
            )
        except Exception:
            raise _unknown_outcome() from None

    def _preflight_data(self, request, authorization):
        try:
            checked_request = ImageGenerationRequest.model_validate_json(request.model_dump_json())
            checked_authorization = ImageGenerationAuthorization.model_validate_json(
                authorization.model_dump_json(),
            )
            remote = checked_authorization.remote_binding
            if remote is None or checked_authorization.local_only:
                raise ValueError("remote image authority required")
            remote = RemoteImageAuthorization.model_validate_json(remote.model_dump_json())
            binding = remote.preview.subscription_binding
            if binding is None:
                raise ValueError("subscription binding required")
            checked_request, binding, references = self._prepare(checked_request, binding)
            preview = self._build_preview(checked_request, binding, references)
            if (
                remote.preview != preview.remote_call
                or checked_authorization.request_fingerprint != checked_request.request_fingerprint
                or checked_authorization.preview_fingerprint != preview.preview_fingerprint
            ):
                raise ValueError("remote image preview does not match exact request")
            validate_paid_provider_authorization(remote.preview, remote.authorization, now=self._current_time())
            self._check_subscription(binding)
            return checked_request, checked_authorization, remote, preview, references
        except AiVideoError:
            raise
        except Exception:
            raise _request_invalid() from None

    def _prepare(self, request, subscription_binding):
        try:
            checked_profile = GrokProviderProfile.model_validate_json(self._profile.model_dump_json())
            checked_request = ImageGenerationRequest.model_validate_json(request.model_dump_json())
            binding = GrokSubscriptionBinding.model_validate_json(subscription_binding.model_dump_json())
            if (
                checked_profile != self._profile
                or checked_profile.origin != GROK_SUBSCRIPTION_ORIGIN
                or binding.account_fingerprint != checked_profile.account_fingerprint
                or binding.credential_reference_id != GROK_CREDENTIAL_REFERENCE
                or binding.destination != GROK_SUBSCRIPTION_ORIGIN
                or binding.model_id != GROK_IMAGE_MODEL
                or checked_request.provider_kind != "grok"
                or checked_request.model_id != GROK_IMAGE_MODEL
                or checked_request.parameters.seed is not None
                or checked_request.parameters.width is not None
                or checked_request.parameters.height is not None
                or checked_request.parameters.output_format != "png"
                or checked_request.negative_prompt_text != ""
                or not 2 <= len(checked_request.references) <= 5
                or not {"character", "scene"}.issubset({item.role for item in checked_request.references})
            ):
                raise ValueError("unsupported image request")
            references = self._resolved_references(checked_request)
            return checked_request, binding, references
        except AiVideoError:
            raise
        except Exception:
            raise _request_invalid() from None

    def _resolved_references(self, request):
        resolved = []
        for reference in request.references:
            if not isinstance(reference, ImageReferenceBinding):
                raise _request_invalid()
            try:
                raw = self._image_resolver(reference)
            except Exception:
                raise _request_invalid() from None
            if (
                not isinstance(raw, bytes)
                or not raw
                or hashlib.sha256(raw).hexdigest() != reference.asset_sha256
            ):
                raise _request_invalid()
            mime = self._reference_mime(raw)
            resolved.append((reference, raw, mime))
        return tuple(resolved)

    @staticmethod
    def _reference_mime(raw: bytes) -> str:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            try:
                with Image.open(BytesIO(raw)) as image:
                    mime = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}.get(image.format)
                    if (
                        mime is None
                        or image.width * image.height > MAX_GROK_REFERENCE_PIXELS
                        or getattr(image, "n_frames", 1) != 1
                    ):
                        raise ValueError("unsupported reference image")
                    image.load()
                    return mime
            except Exception:
                raise _request_invalid() from None

    def _check_subscription(self, binding: GrokSubscriptionBinding | None) -> None:
        if binding is None:
            raise _error(ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
                "SuperGrok included-only media billing is not verified; generation is blocked.")
        try:
            now = self._current_time()
            require_current_subscription(
                binding,
                account_fingerprint=self._profile.account_fingerprint,
                model_id=GROK_IMAGE_MODEL,
                destination=GROK_SUBSCRIPTION_ORIGIN,
                now=now,
            )
            if self._subscription_guard(binding) is False:
                raise ValueError("included-only authority was rejected")
        except AiVideoError:
            raise
        except Exception:
            raise _error(ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
                "SuperGrok subscription authority is not current.") from None

    def _current_time(self) -> datetime:
        current = self._now()
        if not isinstance(current, datetime) or current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("current time must be timezone-aware")
        return current

    def _settings_bytes(self) -> bytes:
        return json.dumps(
            {
                "model": GROK_IMAGE_MODEL,
                "n": 1,
                "resolution": self._profile.image_resolution,
                "response_format": "b64_json",
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    @staticmethod
    def _read_bounded_response(response: _ImageResponse) -> bytes:
        body = bytearray()
        for chunk in response.iter_bytes():
            if not isinstance(chunk, bytes) or len(body) + len(chunk) > MAX_GROK_IMAGE_JSON_BYTES:
                raise _unknown_outcome()
            body.extend(chunk)
        if not body:
            raise _unknown_outcome()
        return bytes(body)


__all__ = ["GROK_IMAGE_EDIT_URL", "GrokImageProvider", "HttpxGrokImageTransport"]
