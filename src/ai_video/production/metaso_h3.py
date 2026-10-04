"""METASO H3 Ref2VA and frame conditioning using existing execution contracts.

Reference bytes are supplied by the caller's verified Registry resolver. The
adapter never uploads separately, writes lifecycle state, or retries a submit.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from pydantic import ConfigDict, Field
from PIL import Image

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel
from ai_video.production.minimax_h3 import (
    HttpxMiniMaxH3Transport, MiniMaxH3TransportRequest, MiniMaxH3VideoProvider,
    _consume_permit, _error, _json_object, _permit_is_valid, _task_id,
    _unknown_submit,
)
from ai_video.production.paid_provider import (
    PaidProviderEgressItem, validate_paid_provider_authorization,
)
from ai_video.production.video import (
    BillingKind, ProviderProfilePointer, ResolvedVideoGenerationRequest,
    VideoCapabilityVariant, VideoExecutionKind, VideoFlexibleOutputRequirement,
    VideoGenerationMode, VideoGenerationPreview, VideoGenerationRequest,
    VideoMediaCapability, VideoOutputCapability, VideoOutputRecoveryStrategy, VideoProviderCapabilities,
    VideoSubmitResult, VideoTaskState, build_video_paid_permit_binding,
)
from ai_video.production.vidu_download import parse_result_url, stream_public_video

METASO_ORIGIN = "https://metaso.cn"
METASO_BASE_URL = METASO_ORIGIN + "/api/minimax"
METASO_MODEL_ID = "MiniMax-H3"
_NAME = "metaso_h3"
_VERSION = "metaso-h3-ref2va-v1"
_FRAME_CAPABILITY = "metaso-h3-fl2va-v1"
_MAX_BODY_BYTES = 64 * 1024 * 1024


def metaso_environment_credential() -> str:
    """The sole default lookup source; never inspect another secret store."""
    return os.environ.get("METASO_API_KEY", "")


class MetasoH3Profile(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    duration: int = Field(strict=True, ge=4, le=15)
    resolution: Literal["768P", "2K"]
    aspect_ratio: Literal["adaptive", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]
    context_ir: bool = Field(strict=True)
    # An operator bound, never a claim about a published or observed charge.
    cost_upper_bound_microunits: int = Field(strict=True, gt=0)

    def pointer(self) -> ProviderProfilePointer:
        digest = canonical_sha256(self.model_dump(mode="json"))
        return ProviderProfilePointer(
            profile_id=_NAME, profile_version=_VERSION,
            profile_path=Path(f"provider-profiles/{digest}.json"), profile_sha256=digest,
        )

    def output(self) -> VideoFlexibleOutputRequirement:
        return VideoFlexibleOutputRequirement(
            timing_mode="nominal_seconds", duration_seconds=self.duration,
            dimension_mode="adaptive", resolution_label=self.resolution,
            # Pixel geometry is Provider-selected; requested ratio is sealed
            # separately in this profile and the exact native payload.
            ratio="adaptive", fps=24, container="mp4", mime_type="video/mp4",
            native_audio=True,
        )


class HttpxMetasoH3Transport(HttpxMiniMaxH3Transport):
    """API transport plus credential-free, public-address-pinned result GET."""

    @contextmanager
    def stream(self, request):
        if request.method != "GET" or request.body or dict(request.headers) != {"accept": "video/mp4"}:
            raise _error(ErrorCode.VIDEO_ARTIFACT_INVALID, "Invalid METASO download request.")
        with stream_public_video(request.url, timeout_seconds=120) as response:
            # http.client preserves wire casing; the inherited consumer expects
            # httpx-style lowercase lookup for these case-insensitive headers.
            response.headers = {key.lower(): value for key, value in response.headers.items()}
            yield response


class MetasoH3VideoProvider(MiniMaxH3VideoProvider):
    def __init__(self, *, profile: MetasoH3Profile, transport,
                 reference_resolver: Callable, credential=metaso_environment_credential,
                 now: Callable[[], datetime] | None = None):
        super().__init__(transport=transport, credential=credential, now=now)
        self._profile = profile
        self._reference_resolver = reference_resolver

    def capabilities(self) -> VideoProviderCapabilities:
        variant = VideoCapabilityVariant(
            capability_id=_VERSION, provider_kind=_NAME, model_id=METASO_MODEL_ID,
            profile_version=_VERSION, execution_kind=VideoExecutionKind.REMOTE,
            billing_kind=BillingKind.METERED, mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
            output_capability=VideoOutputCapability(
                min_duration_seconds=self._profile.duration, max_duration_seconds=self._profile.duration,
                provider_selected_duration=False, timing_modes=("nominal_seconds",),
                dimension_modes=("adaptive",), resolution_labels=(self._profile.resolution,),
                ratios=("adaptive",), fps_values=(24,), containers=("mp4",),
                native_audio_options=(True,),
            ), allowed_image_roles=("reference",),
            required_first_frame=False, max_reference_count=9,
            allowed_image_mime_types=("image/png", "image/jpeg", "image/webp"),
            max_image_bytes=30 * 1024 * 1024, min_image_width=256, min_image_height=256,
            media_capabilities=tuple(VideoMediaCapability(
                kind=kind, roles=(f"reference_{kind}",), min_count=0, max_count=3,
                allowed_mime_types=mimes,
                max_size_bytes=(15 if kind == "audio" else 50) * 1024 * 1024,
                min_duration_millis=2000, max_duration_millis=15000,
            ) for kind, mimes in (("audio", ("audio/wav", "audio/mpeg")),
                                  ("video", ("video/mp4", "video/quicktime")))),
            negative_prompt_supported=False, seed_supported=False, fps_supported=True,
            idempotent_submit=False, lookup_supported=True,
            output_recovery_strategy=VideoOutputRecoveryStrategy.REQUERY_BY_EFFECT_ID,
        )
        variants = (variant,)
        # Frame mode follows its input images; a fixed profile ratio cannot be
        # silently dropped when the upstream frame API omits the ratio field.
        if self._profile.aspect_ratio == "adaptive":
            variants += (variant.model_copy(update={
                "capability_id": _FRAME_CAPABILITY,
                "mode": VideoGenerationMode.IMAGE_TO_VIDEO,
                "allowed_image_roles": ("first_frame", "last_frame"),
                "required_first_frame": True,
                "max_reference_count": 0,
                "media_capabilities": (),
            }),)
        return VideoProviderCapabilities.create(provider_name=_NAME, variants=variants)

    def compile_request(self, provider_bound, requirement):
        from ai_video.production._remote_video_native_prompt import (
            RemoteVideoPromptCompilation, compile_remote_video_prompt,
        )
        from ai_video.production.video_compiler import (
            ProviderNativePrompt, ProviderRequirementUnsupported,
            ProviderRequirementUnsupportedReason, compile_provider_video_request,
        )
        compiled = compile_remote_video_prompt(requirement)
        if not isinstance(compiled, RemoteVideoPromptCompilation):
            return ProviderRequirementUnsupported(
                requirement_hash=requirement.requirement_hash,
                provider_bound_request_hash=provider_bound.provider_bound_request_hash,
                selected_capability_id=provider_bound.capability_id,
                reason=ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED,
                unsupported_field_paths=compiled.unsupported_field_paths,
            )
        return compile_provider_video_request(
            provider_bound=provider_bound, requirement=requirement,
            compiler_id="metaso-h3-video-compiler", compiler_version="1",
            capabilities=self.capabilities(),
            native_prompt=ProviderNativePrompt(grammar_contract="remote-video-prose-v1",
                prompt_text=compiled.prompt_text, prompt_sha256=compiled.prompt_sha256,
                expressed_control_paths=compiled.expressed_control_paths),
        )

    def resolve(self, request: VideoGenerationRequest) -> ResolvedVideoGenerationRequest:
        capability = next((v for v in self.capabilities().variants if v.mode is request.mode), None)
        if (request.provider_name != _NAME or request.provider_kind != _NAME
                or request.model_id != METASO_MODEL_ID
                or request.provider_profile != self._profile.pointer()
                or capability is None
                or request.output_requirement != self._profile.output()
                or request.subject_bindings or request.c4_multi_anchor_binding is not None
                or len(request.prompt_text) > 7000
                or not (request.image_bindings or any(b.kind == "video" for b in request.media_bindings))):
            raise _error(ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                         "METASO request does not match its sealed profile.")
        if request.mode is VideoGenerationMode.IMAGE_TO_VIDEO and any(
                not b.size_bytes for b in request.image_bindings):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "METASO frame size is missing.")
        for kind in ("audio", "video"):
            refs = tuple(b for b in request.media_bindings if b.kind == kind)
            if sum(b.duration_millis for b in refs) > 15000:
                raise _error(ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                             "METASO reference duration exceeds 15 seconds per media kind.")
        if any(not (256 <= b.width <= 5760 and 256 <= b.height <= 5760
                    and 0.4 <= b.width / b.height <= 2.5)
               for b in (*request.image_bindings,
                         *(b for b in request.media_bindings if b.kind == "video"))):
            raise _error(ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                         "METASO reference aspect ratio is unsupported.")
        if any(b.kind == "video" and not 24 <= b.fps <= 60 for b in request.media_bindings):
            raise _error(ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                         "METASO reference video FPS is unsupported.")
        return ResolvedVideoGenerationRequest.create(
            request=request, capability=capability,
            effective_output=self._profile.output(), effective_seed=None,
            effective_negative_prompt_text="",
        )

    def _validate_resolved(self, request):
        if self.resolve(request.activation_scope.request) != request:
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "METASO resolved request changed.")

    def egress_items(self, request) -> tuple[PaidProviderEgressItem, ...]:
        self._validate_resolved(request)
        raw = request.prompt_text.encode("utf-8")
        items = [PaidProviderEgressItem(item_id="prompt", sha256=hashlib.sha256(raw).hexdigest(),
                    size_bytes=len(raw), mime_type="text/plain", purpose="prompt")]
        for binding in (*request.image_bindings, *request.media_bindings):
            if not binding.size_bytes:
                raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "METASO reference size is missing.")
            items.append(PaidProviderEgressItem(item_id=binding.asset_id,
                sha256=binding.asset_sha256, size_bytes=binding.size_bytes,
                mime_type=binding.mime_type, purpose="reference"))
        return tuple(items)

    def preview(self, request) -> VideoGenerationPreview:
        return VideoGenerationPreview.create(
            resolved=request, estimated_cost_upper_bound_microunits=self._profile.cost_upper_bound_microunits,
            currency="CNY", destination=METASO_ORIGIN,
            egress_item_ids=tuple(i.item_id for i in self.egress_items(request)),
        )

    def native_payload(self, request) -> bytes:
        self._validate_resolved(request)
        content = [{"type": "text", "text": request.prompt_text}]
        # Canonical image/media binding order is also H3's per-kind numbering.
        frame_mode = request.mode is VideoGenerationMode.IMAGE_TO_VIDEO
        for binding in (*request.image_bindings, *request.media_bindings):
            try:
                raw = self._reference_resolver(binding)
            except Exception:
                raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "METASO reference lookup failed.") from None
            if (not isinstance(raw, bytes) or len(raw) != binding.size_bytes
                    or hashlib.sha256(raw).hexdigest() != binding.asset_sha256):
                raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "METASO reference bytes changed.")
            kind = "image" if binding in request.image_bindings else binding.kind
            if frame_mode:
                try:
                    with Image.open(BytesIO(raw)) as image:
                        if (Image.MIME.get(image.format) != binding.mime_type
                                or image.size != (binding.width, binding.height)):
                            raise ValueError("frame metadata mismatch")
                        image.verify()
                except Exception:
                    raise _error(ErrorCode.VIDEO_REQUEST_INVALID,
                                 "METASO frame bytes do not match their image metadata.") from None
            content.append({"type": f"{kind}_url", f"{kind}_url": {
                "url": f"data:{binding.mime_type};base64," + base64.b64encode(raw).decode("ascii")},
                "role": binding.role if frame_mode else f"reference_{kind}"})
        payload = {"model": METASO_MODEL_ID, "content": content,
                   "duration": self._profile.duration, "resolution": self._profile.resolution,
                   "ratio": self._profile.aspect_ratio, "context_ir_enabled": self._profile.context_ir}
        if frame_mode:
            del payload["ratio"]
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        if len(body) > _MAX_BODY_BYTES:
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "METASO request is too large.")
        return body

    def _credential_headers(self, *, json_body):
        try:
            secret = self._credential()
        except Exception:
            raise _error(ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED,
                         "METASO_API_KEY is unavailable.") from None
        if (not isinstance(secret, str) or not secret or not secret.isascii()
                or any(ord(c) < 33 or ord(c) > 126 for c in secret)):
            raise _error(ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED,
                         "METASO_API_KEY is unavailable.")
        headers = {"accept": "application/json", "authorization": f"Bearer {secret}"}
        if json_body:
            headers["content-type"] = "application/json"
        return headers

    def submit(self, request, video_preview, paid_preview, authorization, permit):
        if video_preview != self.preview(request):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "METASO preview mismatch.")
        if paid_preview is None or authorization is None or permit is None:
            raise _error(ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                         "METASO requires durable paid authorization.")
        validate_paid_provider_authorization(paid_preview, authorization, now=self._now())
        binding = build_video_paid_permit_binding(request, video_preview, paid_preview, authorization)
        if (paid_preview.egress_items != self.egress_items(request)
                or paid_preview.secret_reference.kind != "secret_store"
                or paid_preview.secret_reference.reference_id != "METASO_API_KEY"):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "METASO egress or credential reference changed.")
        if not _permit_is_valid(permit, binding):
            raise _error(ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED, "METASO permit is invalid.")
        body = self.native_payload(request)
        transport_request = MiniMaxH3TransportRequest(method="POST",
            url=METASO_BASE_URL + "/v2/video_generation",
            headers=self._credential_headers(json_body=True), body=body)
        # Recheck after potentially expensive reference reads and serialization.
        validate_paid_provider_authorization(paid_preview, authorization, now=self._now())
        if not _consume_permit(permit, binding):
            raise _error(ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED, "METASO permit was consumed.")
        validate_paid_provider_authorization(paid_preview, authorization, now=self._now())
        try:
            response = self._transport.request(transport_request)
        except Exception:
            raise _unknown_submit() from None
        if not 200 <= response.status_code < 300:
            if 400 <= response.status_code < 500 and response.status_code != 429:
                raise _error(ErrorCode.VIDEO_PROVIDER_FAILED,
                             f"METASO rejected submit (HTTP {response.status_code}).")
            raise _unknown_submit()
        try:
            data = _json_object(response.body, surface="METASO submit")
            if (data.get("base_resp") or {}).get("status_code", 0) != 0:
                raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "METASO rejected submit.")
            task_id = _task_id(data.get("task_id"), surface="METASO submit")
        except (AiVideoError, AttributeError):
            # A malformed acknowledgement cannot establish absence of effects.
            raise _unknown_submit() from None
        return VideoSubmitResult.create(resolved=request, external_effect_id=task_id,
                                        submitted_at=self._now())

    def _query(self, task_id):
        task_id = _task_id(task_id, surface="METASO query")
        request = MiniMaxH3TransportRequest(method="GET",
            url=METASO_BASE_URL + "/v2/query/video_generation/" + quote(task_id, safe=""),
            headers=self._credential_headers(json_body=False))
        try:
            response = self._transport.request(request)
        except Exception:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "METASO query transport failed.") from None
        if not 200 <= response.status_code < 300:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, f"METASO query HTTP {response.status_code}.")
        data = _json_object(response.body, surface="METASO query")
        task = data.get("task")
        if (not isinstance(task, dict) or task.get("id") != task_id
                or task.get("model", METASO_MODEL_ID) != METASO_MODEL_ID):
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "METASO query identity mismatch.")
        state = str(task.get("status", "")).lower()
        if state in {"failed", "fail", "cancelled", "canceled", "expired", "error"}:
            return VideoTaskState.FAILED, None
        if state == "queued":
            return VideoTaskState.QUEUED, None
        if state in {"running", "processing"}:
            return VideoTaskState.RUNNING, None
        if state not in {"success", "succeeded", "completed", "done"}:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "METASO query status is unknown.")
        content = task.get("content")
        url = content.get("url") if isinstance(content, dict) else None
        parse_result_url(url)
        return VideoTaskState.SUCCEEDED, url
