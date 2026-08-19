"""MiniMax Hailuo-2.3 V1 video Provider adapter.

The adapter is deliberately explicit: it implements two 768P/6s sealed
variants against the official Chinese V1 dialect (``api.minimaxi.com``):

* ``TEXT_TO_VIDEO`` with no image bindings;
* ``IMAGE_TO_VIDEO`` with exactly one ``first_frame`` binding (no
  ``last_frame`` and no extra references).

Both variants consume the existing Paid Provider permit immediately
before submit and never persist the signed result URL returned by
MiniMax. Provider-specific image byte resolution, base64 encoding and
``first_frame_image`` payload mapping happen inside the adapter and
never enter the provider-neutral core contracts.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import BinaryIO, Literal, Protocol
from urllib.parse import quote, urlsplit

import httpx

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
    validate_paid_provider_authorization,
)
from ai_video.production.state_commit import _DurablePaidProviderSubmitPermit
from ai_video.production.video import (
    BillingKind,
    ResolvedVideoGenerationRequest,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoFetchReceipt,
    VideoGenerationMode,
    VideoGenerationPreview,
    VideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoOutputRequirement,
    VideoProviderCapabilities,
    VideoSubmission,
    VideoSubmitResult,
    VideoTaskObservation,
    VideoTaskState,
    build_video_paid_permit_binding,
)
from ai_video.production.video_contracts import (
    VideoFlexibleOutputRequirement,
    VideoOutputCapability,
)

_ORIGIN = "https://api.minimaxi.com"
_SUBMIT_URL = f"{_ORIGIN}/v1/video_generation"
_QUERY_URL = f"{_ORIGIN}/v1/query/video_generation"
_FILE_RETRIEVE_URL = f"{_ORIGIN}/v1/files/retrieve"
_MODEL_ID = "MiniMax-Hailuo-2.3"
_PROVIDER_NAME = "minimax_hailuo"
_PROVIDER_KIND = "minimax_hailuo"
_PROFILE_VERSION = "hailuo-2.3-v1"
_CAPABILITY_ID = "minimax-hailuo-2.3-v1-t2v-768p-6s-16x9"
_I2V_CAPABILITY_ID = "minimax-hailuo-2.3-v1-i2v-768p-6s-first_frame"
_FILE_ID_PREFIX = "hailuo-content-"
_MAX_JSON_BYTES = 1_000_000
_MAX_PROMPT_CHARACTERS = 2_000
_MAX_VIDEO_BYTES = 256 * 1024 * 1024
_SECRET_REFERENCE_KIND = "secret_store"
_SECRET_REFERENCE_ID = "MINIMAX_API_KEY"
_SAFE_TASK_ID = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_SAFE_FILE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_DEFINITIVE_REJECTION_HTTP_STATUSES = frozenset(
    {400, 401, 403, 404, 405, 413, 415, 422}
)
_TRANSIENT_PROVIDER_CODES = frozenset(
    {1000, 1001, 1002, 1024, 1033, 1039, 1041, 2045, 2056}
)
_FIRST_FRAME_EGRESS_ITEM_ID = "first_frame_image"
_PROMPT_EGRESS_ITEM_ID = "prompt"
_I2V_IMAGE_MIME_TYPES = ("image/jpeg", "image/png", "image/webp")
_MAX_I2V_IMAGE_BYTES = 20 * 1024 * 1024 - 1
_MIN_I2V_IMAGE_DIMENSION = 301


def _error(
    code: ErrorCode,
    message: str,
    *,
    retryable: bool = False,
    technical_detail: str | None = None,
) -> AiVideoError:
    return AiVideoError(
        code=code,
        user_message=message,
        technical_detail=technical_detail,
        retryable=retryable,
    )


def _unknown_submit() -> AiVideoError:
    return _error(
        ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
        "MiniMax Hailuo submit outcome is unknown after permit consumption.",
    )


@dataclass(frozen=True)
class MiniMaxHailuoTransportRequest:
    method: Literal["GET", "POST"]
    url: str
    headers: Mapping[str, str] = field(repr=False)
    body: bytes = field(default=b"", repr=False)


@dataclass(frozen=True)
class MiniMaxHailuoTransportResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes = field(repr=False)


class MiniMaxHailuoStreamResponse(Protocol):
    status_code: int
    headers: Mapping[str, str]

    def iter_bytes(self) -> Iterator[bytes]: ...


class MiniMaxHailuoTransport(Protocol):
    def request(
        self, request: MiniMaxHailuoTransportRequest
    ) -> MiniMaxHailuoTransportResponse: ...

    def stream(
        self, request: MiniMaxHailuoTransportRequest
    ) -> AbstractContextManager[MiniMaxHailuoStreamResponse]: ...


class HttpxMiniMaxHailuoTransport:
    """Small synchronous transport; request representations redact credentials."""

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        self._client = client or httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
        )
        self._owns_client = client is None

    def request(
        self, request: MiniMaxHailuoTransportRequest
    ) -> MiniMaxHailuoTransportResponse:
        response = self._client.request(
            request.method,
            request.url,
            headers=dict(request.headers),
            content=request.body,
            follow_redirects=False,
        )
        return MiniMaxHailuoTransportResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=response.content,
        )

    def stream(
        self, request: MiniMaxHailuoTransportRequest
    ) -> AbstractContextManager[MiniMaxHailuoStreamResponse]:
        return self._client.stream(
            request.method,
            request.url,
            headers=dict(request.headers),
            content=request.body,
            follow_redirects=False,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


CredentialResolver = Callable[[], str]
ImageResolver = Callable[[VideoImageReferenceBinding], bytes]


_I2V_OUTPUT_CAPABILITY = VideoOutputCapability(
    min_duration_seconds=6,
    max_duration_seconds=6,
    provider_selected_duration=False,
    timing_modes=("frame_count",),
    frame_count_min=141,
    frame_count_max=141,
    frame_count_step=1,
    frame_count_remainder=0,
    dimension_modes=("exact",),
    resolution_labels=("768P",),
    ratios=("16:9",),
    fps_values=(24,),
    containers=("mp4",),
    native_audio_options=(False,),
)
_OUTPUT = VideoOutputRequirement(
    duration_seconds=6,
    width=1366,
    height=768,
    fps=None,
    container="mp4",
    mime_type="video/mp4",
    native_audio=False,
)
_VARIANT = VideoCapabilityVariant(
    capability_id=_CAPABILITY_ID,
    provider_kind=_PROVIDER_KIND,
    model_id=_MODEL_ID,
    profile_version=_PROFILE_VERSION,
    execution_kind=VideoExecutionKind.REMOTE,
    billing_kind=BillingKind.METERED,
    mode=VideoGenerationMode.TEXT_TO_VIDEO,
    output=_OUTPUT,
    allowed_image_roles=(),
    required_first_frame=False,
    max_reference_count=0,
    allowed_image_mime_types=(),
    max_image_bytes=1,
    min_image_width=1,
    min_image_height=1,
    negative_prompt_supported=False,
    seed_supported=False,
    fps_supported=False,
    idempotent_submit=False,
    lookup_supported=True,
)
_I2V_OUTPUT = VideoFlexibleOutputRequirement(
    timing_mode="frame_count",
    frame_count=141,
    dimension_mode="exact",
    width=1366,
    height=768,
    resolution_label="768P",
    ratio="16:9",
    fps=24,
    container="mp4",
    mime_type="video/mp4",
    native_audio=False,
)
_I2V_VARIANT = VideoCapabilityVariant(
    capability_id=_I2V_CAPABILITY_ID,
    provider_kind=_PROVIDER_KIND,
    model_id=_MODEL_ID,
    profile_version=_PROFILE_VERSION,
    execution_kind=VideoExecutionKind.REMOTE,
    billing_kind=BillingKind.METERED,
    mode=VideoGenerationMode.IMAGE_TO_VIDEO,
    output_capability=_I2V_OUTPUT_CAPABILITY,
    allowed_image_roles=("first_frame",),
    required_first_frame=True,
    max_reference_count=0,
    allowed_image_mime_types=_I2V_IMAGE_MIME_TYPES,
    max_image_bytes=_MAX_I2V_IMAGE_BYTES,
    min_image_width=_MIN_I2V_IMAGE_DIMENSION,
    min_image_height=_MIN_I2V_IMAGE_DIMENSION,
    negative_prompt_supported=False,
    seed_supported=False,
    fps_supported=True,
    idempotent_submit=False,
    lookup_supported=True,
)
_CAPABILITIES = VideoProviderCapabilities.create(
    provider_name=_PROVIDER_NAME,
    variants=(_VARIANT, _I2V_VARIANT),
)


def _json_object(body: bytes, *, surface: str) -> dict[str, object]:
    if len(body) > _MAX_JSON_BYTES:
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED, f"MiniMax Hailuo {surface} is too large."
        )
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED,
            f"MiniMax Hailuo {surface} is not valid JSON.",
        ) from None
    if not isinstance(value, dict):
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED,
            f"MiniMax Hailuo {surface} must be a JSON object.",
        )
    return value


def _base_resp_status(payload: dict[str, object], *, surface: str) -> int:
    base_resp = payload.get("base_resp")
    if not isinstance(base_resp, dict):
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED,
            f"MiniMax Hailuo {surface} base_resp is missing.",
        )
    status_code = base_resp.get("status_code")
    if (
        not isinstance(status_code, int)
        or isinstance(status_code, bool)
        or status_code < 0
        or status_code > 99_999
    ):
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED,
            f"MiniMax Hailuo {surface} base_resp status_code is invalid.",
        )
    return status_code


def _provider_status_error(*, surface: str, provider_code: int) -> AiVideoError:
    return _error(
        ErrorCode.VIDEO_PROVIDER_FAILED,
        f"MiniMax Hailuo {surface} was rejected by the Provider.",
        retryable=provider_code in _TRANSIENT_PROVIDER_CODES,
        technical_detail=f"provider_code={provider_code}",
    )


def _task_id(value: object, *, surface: str) -> str:
    if not isinstance(value, str) or _SAFE_TASK_ID.fullmatch(value) is None:
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED,
            f"MiniMax Hailuo {surface} contains an invalid task ID.",
        )
    return value


def _file_id(value: object, *, surface: str) -> str:
    if isinstance(value, int) and not isinstance(value, bool):
        if 0 < value <= 9_223_372_036_854_775_807:
            return str(value)
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED,
            f"MiniMax Hailuo {surface} contains an invalid file ID.",
        )
    if not isinstance(value, str) or _SAFE_FILE_ID.fullmatch(value) is None:
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED,
            f"MiniMax Hailuo {surface} contains an invalid file ID.",
        )
    return value


def _signed_https_url(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED, "MiniMax Hailuo result URL is missing."
        )
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError:
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED, "MiniMax Hailuo result URL is invalid."
        ) from None
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or not parsed.path
        or parsed.fragment
    ):
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED,
            "MiniMax Hailuo result URL must be HTTPS without credentials or fragments.",
        )
    return value


def _provider_file_id(file_id: str) -> str:
    return _FILE_ID_PREFIX + hashlib.sha256(file_id.encode("utf-8")).hexdigest()


def _permit_is_valid(permit: object, binding: dict[str, str]) -> bool:
    if type(permit) is not _DurablePaidProviderSubmitPermit:
        return False
    try:
        return permit._validate_paid_provider_operation_permit(**binding) is True
    except Exception:
        return False


def _consume_permit(permit: object, binding: dict[str, str]) -> bool:
    if type(permit) is not _DurablePaidProviderSubmitPermit:
        return False
    try:
        return permit._consume_paid_provider_operation_permit(**binding) is True
    except Exception:
        return False


def _validate_submission(
    submission: VideoSubmission,
    receipt: PaidProviderSubmitReceipt,
) -> str:
    if (
        receipt.outcome is not PaidProviderSubmitOutcome.ACCEPTED
        or receipt.submit_receipt_fingerprint != submission.paid_submit_receipt_fingerprint
        or receipt.request_fingerprint != submission.resolved_generation_hash
        or receipt.external_effect_id is None
    ):
        raise _error(
            ErrorCode.VIDEO_REQUEST_INVALID,
            "MiniMax Hailuo evidence does not match the submitted generation.",
        )
    return _task_id(receipt.external_effect_id, surface="submit receipt")


class MiniMaxHailuoVideoProvider:
    def __init__(
        self,
        *,
        transport: MiniMaxHailuoTransport,
        credential: CredentialResolver,
        image_resolver: ImageResolver | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._transport = transport
        self._credential = credential
        self._image_resolver = image_resolver
        self._now = now or (lambda: datetime.now(UTC))

    def capabilities(self) -> VideoProviderCapabilities:
        return _CAPABILITIES

    def resolve(self, request: VideoGenerationRequest) -> ResolvedVideoGenerationRequest:
        if (
            request.provider_name != _PROVIDER_NAME
            or request.provider_kind != _PROVIDER_KIND
            or request.model_id != _MODEL_ID
            or request.provider_profile.profile_version != _PROFILE_VERSION
            or request.negative_prompt_text
            or request.seed is not None
        ):
            raise _error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "MiniMax Hailuo request does not match the sealed 768P capability.",
            )
        if len(request.prompt_text) > _MAX_PROMPT_CHARACTERS:
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax Hailuo prompt exceeds 2000 characters.",
            )
        if request.mode is VideoGenerationMode.TEXT_TO_VIDEO:
            if request.image_bindings or request.output_requirement != _OUTPUT:
                raise _error(
                    ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                    "MiniMax Hailuo T2V request must not include image bindings.",
                )
            return ResolvedVideoGenerationRequest.create(
                request=request,
                capability=_VARIANT,
                effective_output=_OUTPUT,
                effective_seed=None,
                effective_negative_prompt_text="",
            )
        if request.mode is VideoGenerationMode.IMAGE_TO_VIDEO:
            if request.output_requirement != _I2V_OUTPUT:
                raise _error(
                    ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                    "MiniMax Hailuo I2V request does not match the sealed 768P output.",
                )
            if len(request.image_bindings) != 1:
                raise _error(
                    ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                    "MiniMax Hailuo I2V request requires exactly one first_frame binding.",
                )
            binding = request.image_bindings[0]
            if binding.role != "first_frame":
                raise _error(
                    ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                    "MiniMax Hailuo I2V does not support last_frame or reference roles.",
                )
            if (
                binding.mime_type not in _I2V_IMAGE_MIME_TYPES
                or binding.size_bytes is None
                or binding.size_bytes <= 0
                or binding.size_bytes > _MAX_I2V_IMAGE_BYTES
                or binding.width < _MIN_I2V_IMAGE_DIMENSION
                or binding.height < _MIN_I2V_IMAGE_DIMENSION
                or binding.width * 5 < binding.height * 2
                or binding.width * 2 > binding.height * 5
            ):
                raise _error(
                    ErrorCode.VIDEO_REQUEST_INVALID,
                    "MiniMax Hailuo I2V first-frame image does not match the sealed geometry/MIME/size.",
                )
            return ResolvedVideoGenerationRequest.create(
                request=request,
                capability=_I2V_VARIANT,
                effective_output=_I2V_OUTPUT,
                effective_seed=None,
                effective_negative_prompt_text="",
            )
        raise _error(
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
            "MiniMax Hailuo request does not match a sealed capability variant.",
        )

    def preview(self, request: ResolvedVideoGenerationRequest) -> VideoGenerationPreview:
        if (
            request.provider_name != _PROVIDER_NAME
            or request.provider_kind != _PROVIDER_KIND
            or request.model_id != _MODEL_ID
        ):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax Hailuo resolved request is invalid.",
            )
        if request.capability_id == _CAPABILITY_ID:
            if request.effective_output != _OUTPUT:
                raise _error(
                    ErrorCode.VIDEO_REQUEST_INVALID,
                    "MiniMax Hailuo resolved T2V request is invalid.",
                )
            return VideoGenerationPreview.create(
                resolved=request,
                estimated_cost_upper_bound_microunits=2_000_000,
                currency="CNY",
                destination=_ORIGIN,
                egress_item_ids=(_PROMPT_EGRESS_ITEM_ID,),
            )
        if request.capability_id == _I2V_CAPABILITY_ID:
            if request.effective_output != _I2V_OUTPUT:
                raise _error(
                    ErrorCode.VIDEO_REQUEST_INVALID,
                    "MiniMax Hailuo resolved I2V request is invalid.",
                )
            return VideoGenerationPreview.create(
                resolved=request,
                estimated_cost_upper_bound_microunits=3_000_000,
                currency="CNY",
                destination=_ORIGIN,
                egress_item_ids=(
                    _PROMPT_EGRESS_ITEM_ID,
                    request.image_bindings[0].asset_id,
                ),
            )
        raise _error(
            ErrorCode.VIDEO_REQUEST_INVALID,
            "MiniMax Hailuo resolved request is invalid.",
        )

    def _validate_i2v_egress(
        self,
        prompt_items: tuple[object, ...],
        request: ResolvedVideoGenerationRequest,
        prompt_bytes: bytes,
    ) -> None:
        if len(prompt_items) != 2:
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax Hailuo I2V paid preview must bind prompt and first_frame_image.",
            )
        items_by_id = {
            getattr(item, "item_id", None): item for item in prompt_items
        }
        prompt_item = items_by_id.get(_PROMPT_EGRESS_ITEM_ID)
        image_item = items_by_id.get(request.image_bindings[0].asset_id)
        if prompt_item is None or image_item is None:
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax Hailuo I2V paid preview must bind prompt and first_frame_image.",
            )
        if (
            getattr(prompt_item, "sha256", None)
            != hashlib.sha256(prompt_bytes).hexdigest()
            or getattr(prompt_item, "size_bytes", None) != len(prompt_bytes)
            or getattr(prompt_item, "mime_type", None) != "text/plain"
            or getattr(prompt_item, "purpose", None) != "prompt"
        ):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax Hailuo I2V paid preview does not bind the exact prompt.",
            )
        binding = request.image_bindings[0]
        if (
            getattr(image_item, "sha256", None) != binding.asset_sha256
            or getattr(image_item, "size_bytes", None) != binding.size_bytes
            or getattr(image_item, "mime_type", None) != binding.mime_type
            or getattr(image_item, "purpose", None) != "reference"
        ):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax Hailuo I2V paid preview does not bind the exact first-frame image.",
            )

    def _encode_first_frame(
        self, request: ResolvedVideoGenerationRequest
    ) -> str:
        if self._image_resolver is None:
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax Hailuo I2V requires an image byte resolver.",
            )
        binding = request.image_bindings[0]
        try:
            image_bytes = self._image_resolver(binding)
        except Exception:
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax Hailuo I2V first-frame image could not be resolved.",
            ) from None
        if not isinstance(image_bytes, (bytes, bytearray)):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax Hailuo I2V first-frame image bytes are invalid.",
            )
        image_bytes = bytes(image_bytes)
        if (
            hashlib.sha256(image_bytes).hexdigest() != binding.asset_sha256
            or len(image_bytes) != binding.size_bytes
        ):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax Hailuo I2V first-frame image bytes do not match binding.",
            )
        encoded = base64.b64encode(image_bytes).decode("ascii")
        return f"data:{binding.mime_type};base64,{encoded}"

    def _credential_headers(self, *, json_body: bool) -> dict[str, str]:
        try:
            secret = self._credential()
        except Exception:
            raise _error(
                ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED,
                "MiniMax Hailuo credential is unavailable.",
            ) from None
        if not isinstance(secret, str) or not secret or not secret.isascii():
            raise _error(
                ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED,
                "MiniMax Hailuo credential is unavailable.",
            )
        headers = {"accept": "application/json", "authorization": f"Bearer {secret}"}
        if json_body:
            headers["content-type"] = "application/json"
        return headers

    def _query(self, task_id: str) -> tuple[VideoTaskState, str | None]:
        url = f"{_QUERY_URL}?task_id={quote(task_id, safe='')}"
        request = MiniMaxHailuoTransportRequest(
            method="GET",
            url=url,
            headers=self._credential_headers(json_body=False),
        )
        try:
            response = self._transport.request(request)
        except Exception:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "MiniMax Hailuo task query transport failed.",
                retryable=True,
            ) from None
        if not 200 <= response.status_code < 300:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                f"MiniMax Hailuo task query returned HTTP {response.status_code}.",
                retryable=response.status_code >= 500 or response.status_code == 429,
            )
        payload = _json_object(response.body, surface="query response")
        provider_code = _base_resp_status(payload, surface="query response")
        if provider_code != 0:
            raise _provider_status_error(
                surface="query response", provider_code=provider_code
            )
        if _task_id(payload.get("task_id"), surface="query response") != task_id:
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax Hailuo query task ID changed.",
            )
        status = payload.get("status")
        if status == "Queueing":
            return VideoTaskState.QUEUED, None
        if status == "Preparing":
            return VideoTaskState.RUNNING, None
        if status == "Processing":
            return VideoTaskState.RUNNING, None
        if status == "Fail":
            return VideoTaskState.FAILED, None
        if status != "Success":
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "MiniMax Hailuo query status is invalid.",
            )
        file_id = _file_id(payload.get("file_id"), surface="query response")
        return VideoTaskState.SUCCEEDED, file_id

    def _file_retrieve(self, file_id: str) -> str:
        url = f"{_FILE_RETRIEVE_URL}?file_id={quote(file_id, safe='')}"
        request = MiniMaxHailuoTransportRequest(
            method="GET",
            url=url,
            headers=self._credential_headers(json_body=False),
        )
        try:
            response = self._transport.request(request)
        except Exception:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "MiniMax Hailuo file retrieve transport failed.",
                retryable=True,
            ) from None
        if not 200 <= response.status_code < 300:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                f"MiniMax Hailuo file retrieve returned HTTP {response.status_code}.",
                retryable=response.status_code >= 500 or response.status_code == 429,
            )
        payload = _json_object(response.body, surface="file retrieve response")
        provider_code = _base_resp_status(payload, surface="file retrieve response")
        if provider_code != 0:
            raise _provider_status_error(
                surface="file retrieve response", provider_code=provider_code
            )
        file = payload.get("file")
        if not isinstance(file, dict):
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "MiniMax Hailuo file retrieve file object is missing.",
            )
        if _file_id(file.get("file_id"), surface="file retrieve response") != file_id:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "MiniMax Hailuo file retrieve identity changed.",
            )
        return _signed_https_url(file.get("download_url"))

    def submit(
        self,
        request: ResolvedVideoGenerationRequest,
        video_preview: VideoGenerationPreview,
        paid_preview: PaidProviderCallPreview | None,
        authorization: PaidProviderAuthorizationDecision | None,
        permit: object | None,
    ) -> VideoSubmitResult:
        if video_preview != self.preview(request):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID, "MiniMax Hailuo preview mismatch."
            )
        if paid_preview is None or authorization is None or permit is None:
            raise _error(
                ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                "MiniMax Hailuo submit requires Paid Provider authorization.",
            )
        validate_paid_provider_authorization(paid_preview, authorization, now=self._now())
        binding = build_video_paid_permit_binding(
            request, video_preview, paid_preview, authorization
        )
        prompt_bytes = request.prompt_text.encode("utf-8")
        prompt_items = paid_preview.egress_items
        if (
            paid_preview.secret_reference.kind != _SECRET_REFERENCE_KIND
            or paid_preview.secret_reference.reference_id != _SECRET_REFERENCE_ID
        ):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax Hailuo paid preview does not bind the exact credential.",
            )
        if not _permit_is_valid(permit, binding):
            raise _error(
                ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                "MiniMax Hailuo submit permit is invalid.",
            )
        is_i2v = request.capability_id == _I2V_CAPABILITY_ID
        if is_i2v:
            self._validate_i2v_egress(prompt_items, request, prompt_bytes)
            first_frame_b64 = self._encode_first_frame(request)
            body = json.dumps(
                {
                    "model": _MODEL_ID,
                    "prompt": request.prompt_text,
                    "duration": 6,
                    "resolution": "768P",
                    _FIRST_FRAME_EGRESS_ITEM_ID: first_frame_b64,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        else:
            if (
                len(prompt_items) != 1
                or prompt_items[0].item_id != _PROMPT_EGRESS_ITEM_ID
                or prompt_items[0].sha256
                != hashlib.sha256(prompt_bytes).hexdigest()
                or prompt_items[0].size_bytes != len(prompt_bytes)
                or prompt_items[0].mime_type != "text/plain"
                or prompt_items[0].purpose != "prompt"
            ):
                raise _error(
                    ErrorCode.VIDEO_REQUEST_INVALID,
                    "MiniMax Hailuo paid preview does not bind the exact prompt and credential.",
                )
            body = json.dumps(
                {
                    "model": _MODEL_ID,
                    "prompt": request.prompt_text,
                    "duration": 6,
                    "resolution": "768P",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        transport_request = MiniMaxHailuoTransportRequest(
            method="POST",
            url=_SUBMIT_URL,
            headers=self._credential_headers(json_body=True),
            body=body,
        )
        if not _consume_permit(permit, binding):
            raise _error(
                ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                "MiniMax Hailuo submit permit is already consumed.",
            )
        try:
            response = self._transport.request(transport_request)
        except Exception:
            raise _unknown_submit() from None
        if not 200 <= response.status_code < 300:
            if response.status_code in _DEFINITIVE_REJECTION_HTTP_STATUSES:
                raise _error(
                    ErrorCode.VIDEO_PROVIDER_FAILED,
                    f"MiniMax Hailuo submit was rejected with HTTP {response.status_code}.",
                )
            raise _unknown_submit()
        try:
            payload = _json_object(response.body, surface="submit response")
            provider_code = _base_resp_status(payload, surface="submit response")
        except AiVideoError:
            raise _unknown_submit() from None
        if provider_code != 0:
            raise _provider_status_error(
                surface="submit response", provider_code=provider_code
            )
        try:
            task_id = _task_id(payload.get("task_id"), surface="submit response")
        except AiVideoError:
            raise _unknown_submit() from None
        return VideoSubmitResult.create(
            resolved=request,
            external_effect_id=task_id,
            submitted_at=self._now(),
        )

    def get_status(
        self,
        submission: VideoSubmission,
        submit_receipt: PaidProviderSubmitReceipt,
    ) -> VideoTaskObservation:
        task_id = _validate_submission(submission, submit_receipt)
        state, file_id = self._query(task_id)
        return VideoTaskObservation.create(
            submission=submission,
            state=state,
            observed_at=self._now(),
            progress_milli={
                VideoTaskState.QUEUED: 0,
                VideoTaskState.RUNNING: 500,
                VideoTaskState.SUCCEEDED: 1000,
                VideoTaskState.FAILED: 1000,
            }[state],
            provider_file_id=(
                _provider_file_id(file_id)
                if state is VideoTaskState.SUCCEEDED and file_id is not None
                else None
            ),
        )

    def fetch(
        self,
        submission: VideoSubmission,
        submit_receipt: PaidProviderSubmitReceipt,
        observation: VideoTaskObservation,
        sink: BinaryIO,
    ) -> VideoFetchReceipt:
        task_id = _validate_submission(submission, submit_receipt)
        if (
            observation.submission_fingerprint != submission.submission_fingerprint
            or observation.paid_submit_receipt_fingerprint
            != submission.paid_submit_receipt_fingerprint
            or observation.state is not VideoTaskState.SUCCEEDED
            or observation.provider_file_id is None
        ):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax Hailuo fetch evidence mismatch.",
            )
        state, file_id = self._query(task_id)
        if state is not VideoTaskState.SUCCEEDED or file_id is None:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "MiniMax Hailuo task is not fetchable.",
            )
        if _provider_file_id(file_id) != observation.provider_file_id:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "MiniMax Hailuo result identity changed.",
            )
        signed_url = self._file_retrieve(file_id)
        request = MiniMaxHailuoTransportRequest(
            method="GET",
            url=signed_url,
            headers={"accept": "video/mp4"},
        )
        digest = hashlib.sha256()
        size = 0
        try:
            with self._transport.stream(request) as response:
                if not 200 <= response.status_code < 300:
                    raise _error(
                        ErrorCode.VIDEO_PROVIDER_FAILED,
                        f"MiniMax Hailuo download returned HTTP {response.status_code}.",
                        retryable=response.status_code >= 500 or response.status_code == 429,
                    )
                content_type = response.headers.get("content-type", "")
                if not content_type.lower().startswith("video/mp4"):
                    raise _error(
                        ErrorCode.VIDEO_ARTIFACT_INVALID,
                        "MiniMax Hailuo download is not video/mp4.",
                    )
                content_length = response.headers.get("content-length")
                if content_length is not None:
                    try:
                        declared_size = int(content_length)
                    except ValueError:
                        raise _error(
                            ErrorCode.VIDEO_ARTIFACT_INVALID,
                            "MiniMax Hailuo download Content-Length is invalid.",
                        ) from None
                    if declared_size < 0 or declared_size > _MAX_VIDEO_BYTES:
                        raise _error(
                            ErrorCode.VIDEO_ARTIFACT_INVALID,
                            "MiniMax Hailuo download exceeds the size limit.",
                        )
                for chunk in response.iter_bytes():
                    if not chunk:
                        continue
                    if size + len(chunk) > _MAX_VIDEO_BYTES:
                        raise _error(
                            ErrorCode.VIDEO_ARTIFACT_INVALID,
                            "MiniMax Hailuo download exceeds the size limit.",
                        )
                    sink.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
        except AiVideoError:
            raise
        except Exception:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "MiniMax Hailuo download transport failed.",
                retryable=True,
            ) from None
        if size == 0:
            raise _error(
                ErrorCode.VIDEO_ARTIFACT_INVALID, "MiniMax Hailuo download is empty."
            )
        if content_length is not None and size != declared_size:
            raise _error(
                ErrorCode.VIDEO_ARTIFACT_INVALID,
                "MiniMax Hailuo download size does not match Content-Length.",
            )
        sink.flush()
        return VideoFetchReceipt.create(
            submission=submission,
            observation=observation,
            content_type="video/mp4",
            size_bytes=size,
            artifact_sha256=digest.hexdigest(),
            fetched_at=self._now(),
        )


__all__ = [
    "HttpxMiniMaxHailuoTransport",
    "MiniMaxHailuoStreamResponse",
    "MiniMaxHailuoTransport",
    "MiniMaxHailuoTransportRequest",
    "MiniMaxHailuoTransportResponse",
    "MiniMaxHailuoVideoProvider",
]
