"""Whole-ad methods delegated by the existing Vidu transport owner."""

import hashlib
import json
from urllib.parse import quote

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.paid_provider import (
    PaidProviderCallPreview, PaidProviderEgressItem, SecretReference,
    validate_paid_provider_authorization,
)
from ai_video.production.vidu_ad_contracts import AdGenerationRequest
from ai_video.production.vidu_ad_wire import encode_create, parse_submission, parse_status
from ai_video.production.vidu_profile import ViduAdProviderProfile


def ad_preview(request, profile, attempt_id):
    request = AdGenerationRequest.model_validate_json(request.model_dump_json())
    profile = ViduAdProviderProfile.model_validate_json(profile.model_dump_json())
    if request.profile_hash != profile.pointer().profile_sha256:
        raise AiVideoError(code=ErrorCode.VIDEO_REQUEST_INVALID, user_message="Ad profile identity changed.")
    prompt = request.prompt.encode()
    settings = json.dumps(request.model_dump(mode="json", exclude={"prompt", "images"}),
                          sort_keys=True, separators=(",", ":")).encode()
    items = [PaidProviderEgressItem(item_id="prompt", sha256=hashlib.sha256(prompt).hexdigest(),
             size_bytes=len(prompt), mime_type="text/plain", purpose="prompt"),
             PaidProviderEgressItem(item_id="settings", sha256=hashlib.sha256(settings).hexdigest(),
             size_bytes=len(settings), mime_type="application/json", purpose="settings")]
    items.extend(PaidProviderEgressItem(item_id=f"image-{i}", sha256=x.sha256,
                 size_bytes=x.size_bytes, mime_type=x.mime_type, purpose="reference")
                 for i, x in enumerate(request.images))
    return PaidProviderCallPreview.create(
        attempt_id=attempt_id, operation="ad_generation", provider_kind="vidu", model_id="ad-one-click",
        request_fingerprint=request.content_hash, billing_mode="remote_metered", currency="CNY",
        estimated_cost_upper_bound_microunits=profile.cost_upper_bound_microunits,
        destination=profile.origin, method="POST", egress_items=tuple(items), retention_mode="provider_standard",
        provider_policy_snapshot_id=request.policy_id,
        secret_reference=SecretReference(kind="secret_store", reference_id="VIDU_API_KEY"),
    )


class _ViduAdMethods:
    def ad_preview(self, request, attempt_id):
        from ai_video.production.vidu import _error
        if not isinstance(self._profile, ViduAdProviderProfile):
            raise _error("Ad generation requires an explicit ad service profile.", ErrorCode.VIDEO_REQUEST_INVALID)
        if not self._profile.pricing_observed_at <= self._now() < min(
            self._profile.pricing_expires_at, request.expires_at
        ):
            raise _error("Ad request or operator ceiling expired.", ErrorCode.PAID_PROVIDER_BUDGET_REJECTED)
        return ad_preview(request, self._profile, attempt_id)

    def _ad_body(self, request):
        from ai_video.production.vidu import _error
        images = []
        for binding in request.images:
            try:
                raw = self._image_resolver(binding) if self._image_resolver else None
            except Exception:
                raise _error("Ad image bytes are unavailable.", ErrorCode.VIDEO_REQUEST_INVALID) from None
            if (not isinstance(raw, bytes) or len(raw) != binding.size_bytes
                    or hashlib.sha256(raw).hexdigest() != binding.sha256):
                raise _error("Ad image bytes changed.", ErrorCode.VIDEO_REQUEST_INVALID)
            images.append((binding.mime_type, raw))
        return encode_create(prompt=request.prompt, duration=request.duration,
                             aspect_ratio=request.aspect_ratio, language=request.language,
                             creative=request.creative, images=tuple(images))

    def submit_ad(self, request, preview, authorization, permit):
        from ai_video.production.vidu import ViduTransportRequest, _error, _REJECTIONS
        from ai_video.production._state_commit_contracts import _DurablePaidProviderSubmitPermit
        if not isinstance(permit, _DurablePaidProviderSubmitPermit):
            raise _error("Ad submit requires a durable permit.", ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED)
        body = self._ad_body(request)
        headers = self._headers()
        if self.ad_preview(request, preview.attempt_id) != preview:
            raise _error("Ad preview changed.", ErrorCode.VIDEO_REQUEST_INVALID)
        validate_paid_provider_authorization(preview, authorization, now=self._now())
        binding = dict(
            attempt_id=preview.attempt_id, operation=preview.operation,
            request_fingerprint=preview.request_fingerprint, destination=preview.destination,
            provider_kind=preview.provider_kind, model_id=preview.model_id, currency=preview.currency,
            estimated_cost_upper_bound_microunits=str(preview.estimated_cost_upper_bound_microunits),
            provider_policy_snapshot_id=preview.provider_policy_snapshot_id, retention_mode=preview.retention_mode,
            secret_reference_kind=preview.secret_reference.kind,
            secret_reference_id=preview.secret_reference.reference_id,
            authorization_fingerprint=authorization.authorization_fingerprint,
        )
        if not permit._consume_paid_provider_operation_permit(**binding):
            raise _error("Ad permit is stale or consumed.", ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED)
        try:
            response = self._transport.request(ViduTransportRequest(
                "POST", f"{self._profile.origin}/ent/v2/ad-one-click", headers, body
            ))
        except Exception:
            raise _error("Ad submit outcome is unknown.", ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN) from None
        if response.status_code in _REJECTIONS:
            raise _error("Ad submit was rejected without effect.", ErrorCode.PAID_PROVIDER_KNOWN_NO_EFFECT)
        if not 200 <= response.status_code < 300:
            raise _error("Ad submit outcome is unknown.", ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN)
        try:
            return parse_submission(response.body)
        except AiVideoError:
            raise _error("Ad submit outcome is unknown.", ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN) from None

    def _ad_status(self, task_id):
        from ai_video.production.vidu import ViduTransportRequest, _identifier, _error
        _identifier(task_id)
        try:
            response = self._transport.request(ViduTransportRequest(
                "GET", f"{self._profile.origin}/ent/v2/tasks/{quote(task_id, safe='')}/creations", self._headers()
            ))
        except Exception:
            raise _error("Ad status query failed.", retryable=True) from None
        if response.status_code != 200:
            raise _error("Ad status query failed.", retryable=True)
        return parse_status(response.body, task_id=task_id)
