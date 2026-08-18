"""MiniMax H3 V2 text-to-video Provider adapter.

The adapter is deliberately explicit: it implements one 768P/4s/16:9 T2V
profile, consumes the existing Paid Provider permit immediately before submit,
and never persists the signed result URL returned by MiniMax.
"""

from __future__ import annotations

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
    VideoOutputRequirement,
    VideoProviderCapabilities,
    VideoSubmission,
    VideoSubmitResult,
    VideoTaskObservation,
    VideoTaskState,
    build_video_paid_permit_binding,
)

_ORIGIN = "https://api.minimaxi.com"
_SUBMIT_URL = f"{_ORIGIN}/v2/video_generation"
_QUERY_URL = f"{_ORIGIN}/v2/query/video_generation/{{task_id}}"
_MODEL_ID = "MiniMax-H3"
_PROVIDER_NAME = "minimax_h3"
_PROVIDER_KIND = "minimax_h3"
_PROFILE_VERSION = "h3-v2"
_CAPABILITY_ID = "minimax-h3-v2-t2v-768p-4s-16x9"
_FILE_ID_PREFIX = "h3-content-"
_MAX_JSON_BYTES = 1_000_000
_MAX_PROMPT_CHARACTERS = 2_000
_MAX_VIDEO_BYTES = 256 * 1024 * 1024
_SECRET_REFERENCE_KIND = "secret_store"
_SECRET_REFERENCE_ID = "MINIMAX_API_KEY"
_SAFE_TASK_ID = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")


def _error(code: ErrorCode, message: str, *, retryable: bool = False) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, retryable=retryable)


def _unknown_submit() -> AiVideoError:
    return _error(
        ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
        "MiniMax H3 submit outcome is unknown after permit consumption.",
    )


@dataclass(frozen=True)
class MiniMaxH3TransportRequest:
    method: Literal["GET", "POST"]
    url: str
    headers: Mapping[str, str] = field(repr=False)
    body: bytes = field(default=b"", repr=False)


@dataclass(frozen=True)
class MiniMaxH3TransportResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes = field(repr=False)


class MiniMaxH3StreamResponse(Protocol):
    status_code: int
    headers: Mapping[str, str]

    def iter_bytes(self) -> Iterator[bytes]: ...


class MiniMaxH3Transport(Protocol):
    def request(self, request: MiniMaxH3TransportRequest) -> MiniMaxH3TransportResponse: ...

    def stream(
        self, request: MiniMaxH3TransportRequest
    ) -> AbstractContextManager[MiniMaxH3StreamResponse]: ...


class HttpxMiniMaxH3Transport:
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

    def request(self, request: MiniMaxH3TransportRequest) -> MiniMaxH3TransportResponse:
        response = self._client.request(
            request.method,
            request.url,
            headers=dict(request.headers),
            content=request.body,
            follow_redirects=False,
        )
        return MiniMaxH3TransportResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=response.content,
        )

    def stream(
        self, request: MiniMaxH3TransportRequest
    ) -> AbstractContextManager[MiniMaxH3StreamResponse]:
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


_OUTPUT = VideoOutputRequirement(
    duration_seconds=4,
    width=1366,
    height=768,
    fps=None,
    container="mp4",
    mime_type="video/mp4",
    native_audio=True,
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
_CAPABILITIES = VideoProviderCapabilities.create(
    provider_name=_PROVIDER_NAME,
    variants=(_VARIANT,),
)


def _json_object(body: bytes, *, surface: str) -> dict[str, object]:
    if len(body) > _MAX_JSON_BYTES:
        raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, f"MiniMax H3 {surface} is too large.")
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED,
            f"MiniMax H3 {surface} is not valid JSON.",
        ) from None
    if not isinstance(value, dict):
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED,
            f"MiniMax H3 {surface} must be a JSON object.",
        )
    return value


def _task_id(value: object, *, surface: str) -> str:
    if not isinstance(value, str) or _SAFE_TASK_ID.fullmatch(value) is None:
        raise _error(
            ErrorCode.VIDEO_PROVIDER_FAILED,
            f"MiniMax H3 {surface} contains an invalid task ID.",
        )
    return value


def _signed_https_url(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "MiniMax H3 result URL is missing.")
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError:
        raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "MiniMax H3 result URL is invalid.") from None
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
            "MiniMax H3 result URL must be HTTPS without credentials or fragments.",
        )
    return value


def _provider_file_id(task_id: str) -> str:
    return _FILE_ID_PREFIX + hashlib.sha256(task_id.encode("utf-8")).hexdigest()


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
            "MiniMax H3 evidence does not match the submitted generation.",
        )
    return _task_id(receipt.external_effect_id, surface="submit receipt")


class MiniMaxH3VideoProvider:
    def __init__(
        self,
        *,
        transport: MiniMaxH3Transport,
        credential: CredentialResolver,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._transport = transport
        self._credential = credential
        self._now = now or (lambda: datetime.now(UTC))

    def capabilities(self) -> VideoProviderCapabilities:
        return _CAPABILITIES

    def resolve(self, request: VideoGenerationRequest) -> ResolvedVideoGenerationRequest:
        if (
            request.provider_name != _PROVIDER_NAME
            or request.provider_kind != _PROVIDER_KIND
            or request.model_id != _MODEL_ID
            or request.provider_profile.profile_version != _PROFILE_VERSION
            or request.mode is not VideoGenerationMode.TEXT_TO_VIDEO
            or request.image_bindings
            or request.negative_prompt_text
            or request.seed is not None
            or request.output_requirement != _OUTPUT
        ):
            raise _error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "MiniMax H3 request does not match the sealed 768P T2V capability.",
            )
        if len(request.prompt_text) > _MAX_PROMPT_CHARACTERS:
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax H3 prompt exceeds 2000 characters.",
            )
        return ResolvedVideoGenerationRequest.create(
            request=request,
            capability=_VARIANT,
            effective_output=_OUTPUT,
            effective_seed=None,
            effective_negative_prompt_text="",
        )

    def preview(self, request: ResolvedVideoGenerationRequest) -> VideoGenerationPreview:
        if (
            request.provider_name != _PROVIDER_NAME
            or request.capability_id != _CAPABILITY_ID
            or request.effective_output != _OUTPUT
        ):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "MiniMax H3 resolved request is invalid.")
        return VideoGenerationPreview.create(
            resolved=request,
            estimated_cost_upper_bound_microunits=2_000_000,
            currency="CNY",
            destination=_ORIGIN,
            egress_item_ids=("prompt",),
        )

    def _credential_headers(self, *, json_body: bool) -> dict[str, str]:
        secret = self._credential()
        if not isinstance(secret, str) or not secret or not secret.isascii():
            raise _error(
                ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED,
                "MiniMax H3 credential is unavailable.",
            )
        headers = {"accept": "application/json", "authorization": f"Bearer {secret}"}
        if json_body:
            headers["content-type"] = "application/json"
        return headers

    def _query(self, task_id: str) -> tuple[VideoTaskState, str | None]:
        request = MiniMaxH3TransportRequest(
            method="GET",
            url=_QUERY_URL.format(task_id=quote(task_id, safe="")),
            headers=self._credential_headers(json_body=False),
        )
        try:
            response = self._transport.request(request)
        except Exception:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "MiniMax H3 task query transport failed.",
                retryable=True,
            ) from None
        if not 200 <= response.status_code < 300:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                f"MiniMax H3 task query returned HTTP {response.status_code}.",
                retryable=response.status_code >= 500 or response.status_code == 429,
            )
        payload = _json_object(response.body, surface="query response")
        task = payload.get("task")
        if not isinstance(task, dict):
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "MiniMax H3 query task is missing.")
        if _task_id(task.get("id"), surface="query response") != task_id:
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "MiniMax H3 query task ID changed.")
        if task.get("model") != _MODEL_ID:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "MiniMax H3 query model changed.")
        if (
            task.get("resolution") != "768P"
            or task.get("duration") != 4
            or task.get("ratio") != "16:9"
        ):
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "MiniMax H3 query output profile changed.",
            )
        status = task.get("status")
        if status == "queued":
            return VideoTaskState.QUEUED, None
        if status == "running":
            return VideoTaskState.RUNNING, None
        if status in {"failed", "cancelled"}:
            return VideoTaskState.FAILED, None
        if status != "succeeded":
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "MiniMax H3 query status is invalid.")
        content = task.get("content")
        if not isinstance(content, dict):
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "MiniMax H3 result content is missing.")
        return VideoTaskState.SUCCEEDED, _signed_https_url(content.get("url"))

    def submit(
        self,
        request: ResolvedVideoGenerationRequest,
        video_preview: VideoGenerationPreview,
        paid_preview: PaidProviderCallPreview | None,
        authorization: PaidProviderAuthorizationDecision | None,
        permit: object | None,
    ) -> VideoSubmitResult:
        if video_preview != self.preview(request):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "MiniMax H3 preview mismatch.")
        if paid_preview is None or authorization is None or permit is None:
            raise _error(
                ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                "MiniMax H3 submit requires Paid Provider authorization.",
            )
        validate_paid_provider_authorization(paid_preview, authorization, now=self._now())
        binding = build_video_paid_permit_binding(
            request, video_preview, paid_preview, authorization
        )
        prompt_bytes = request.prompt_text.encode("utf-8")
        prompt_items = paid_preview.egress_items
        if (
            len(prompt_items) != 1
            or prompt_items[0].item_id != "prompt"
            or prompt_items[0].sha256 != hashlib.sha256(prompt_bytes).hexdigest()
            or prompt_items[0].size_bytes != len(prompt_bytes)
            or prompt_items[0].mime_type != "text/plain"
            or prompt_items[0].purpose != "prompt"
            or paid_preview.secret_reference.kind != _SECRET_REFERENCE_KIND
            or paid_preview.secret_reference.reference_id != _SECRET_REFERENCE_ID
        ):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "MiniMax H3 paid preview does not bind the exact prompt and credential.",
            )
        if not _permit_is_valid(permit, binding):
            raise _error(
                ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                "MiniMax H3 submit permit is invalid.",
            )
        body = json.dumps(
            {
                "model": _MODEL_ID,
                "content": [{"type": "text", "text": request.prompt_text}],
                "resolution": "768P",
                "duration": 4,
                "ratio": "16:9",
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        transport_request = MiniMaxH3TransportRequest(
            method="POST",
            url=_SUBMIT_URL,
            headers=self._credential_headers(json_body=True),
            body=body,
        )
        if not _consume_permit(permit, binding):
            raise _error(
                ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                "MiniMax H3 submit permit is already consumed.",
            )
        try:
            response = self._transport.request(transport_request)
        except Exception:
            raise _unknown_submit() from None
        if not 200 <= response.status_code < 300:
            if 400 <= response.status_code < 500 and response.status_code != 429:
                raise _error(
                    ErrorCode.VIDEO_PROVIDER_FAILED,
                    f"MiniMax H3 submit was rejected with HTTP {response.status_code}.",
                )
            raise _unknown_submit()
        try:
            task_id = _task_id(
                _json_object(response.body, surface="submit response").get("task_id"),
                surface="submit response",
            )
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
        state, signed_url = self._query(task_id)
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
                _provider_file_id(task_id)
                if state is VideoTaskState.SUCCEEDED and signed_url is not None
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
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "MiniMax H3 fetch evidence mismatch.")
        state, signed_url = self._query(task_id)
        if state is not VideoTaskState.SUCCEEDED or signed_url is None:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "MiniMax H3 task is not fetchable.")
        if _provider_file_id(task_id) != observation.provider_file_id:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "MiniMax H3 result identity changed.")
        request = MiniMaxH3TransportRequest(
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
                        f"MiniMax H3 download returned HTTP {response.status_code}.",
                        retryable=response.status_code >= 500 or response.status_code == 429,
                    )
                content_type = response.headers.get("content-type", "")
                if not content_type.lower().startswith("video/mp4"):
                    raise _error(
                        ErrorCode.VIDEO_ARTIFACT_INVALID,
                        "MiniMax H3 download is not video/mp4.",
                    )
                content_length = response.headers.get("content-length")
                if content_length is not None:
                    try:
                        declared_size = int(content_length)
                    except ValueError:
                        raise _error(
                            ErrorCode.VIDEO_ARTIFACT_INVALID,
                            "MiniMax H3 download Content-Length is invalid.",
                        ) from None
                    if declared_size < 0 or declared_size > _MAX_VIDEO_BYTES:
                        raise _error(
                            ErrorCode.VIDEO_ARTIFACT_INVALID,
                            "MiniMax H3 download exceeds the size limit.",
                        )
                for chunk in response.iter_bytes():
                    if not chunk:
                        continue
                    if size + len(chunk) > _MAX_VIDEO_BYTES:
                        raise _error(
                            ErrorCode.VIDEO_ARTIFACT_INVALID,
                            "MiniMax H3 download exceeds the size limit.",
                        )
                    sink.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
        except AiVideoError:
            raise
        except Exception:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "MiniMax H3 download transport failed.",
                retryable=True,
            ) from None
        if size == 0:
            raise _error(ErrorCode.VIDEO_ARTIFACT_INVALID, "MiniMax H3 download is empty.")
        if content_length is not None and size != declared_size:
            raise _error(
                ErrorCode.VIDEO_ARTIFACT_INVALID,
                "MiniMax H3 download size does not match Content-Length.",
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
    "HttpxMiniMaxH3Transport",
    "MiniMaxH3Transport",
    "MiniMaxH3TransportRequest",
    "MiniMaxH3TransportResponse",
    "MiniMaxH3VideoProvider",
]
