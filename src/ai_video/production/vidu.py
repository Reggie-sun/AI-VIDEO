"""Explicit Vidu Q3 video Provider behind the shared paid lifecycle gates."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import BinaryIO, Literal, Protocol
from urllib.parse import quote

import httpx

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision, PaidProviderCallPreview,
    PaidProviderSubmitOutcome, PaidProviderSubmitReceipt,
    validate_paid_provider_authorization,
)
from ai_video.production.shot_router import ProviderBoundVideoRequest
from ai_video.production.remote_media import RemoteMediaMaterializationReceipt
from ai_video.production.state_commit import _DurablePaidProviderSubmitPermit
from ai_video.production.video import (
    ResolvedVideoGenerationRequest, VideoFetchReceipt, VideoFlexibleOutputRequirement,
    VideoGenerationMode, VideoGenerationPreview, VideoGenerationRequest,
    VideoImageReferenceBinding, VideoMediaReferenceBinding, VideoProviderCapabilities, VideoProviderTaskBinding,
    VideoSubmission, VideoSubmitResult, VideoTaskObservation, VideoTaskState,
    build_video_paid_permit_binding,
)
from ai_video.production.video_compiler import (
    ProviderRequestCompilationResult, compile_provider_video_request,
)
from ai_video.production.video_requirement import ProviderNeutralVideoRequirement
from ai_video.production.vidu_profile import (
    VIDU_MODEL_IDS, VIDU_REFERENCE_MODEL_IDS, VIDU_EXTEND_MODEL_IDS, ViduProviderProfile, vidu_capabilities,
)
from ai_video.production.vidu_source import ViduExtensionSource
from ai_video.production.vidu_download import parse_result_url, stream_public_video


_MAX_JSON_BYTES = 1_000_000
_MAX_BODY_BYTES = 20 * 1024 * 1024
_SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_REJECTIONS = frozenset({400, 401, 403, 404, 405, 413, 415, 422})
_STATES = {
    "created": VideoTaskState.QUEUED, "queueing": VideoTaskState.QUEUED,
    "processing": VideoTaskState.RUNNING, "success": VideoTaskState.SUCCEEDED,
    "failed": VideoTaskState.FAILED,
}


def _error(message: str, code: ErrorCode = ErrorCode.VIDEO_PROVIDER_FAILED,
           *, retryable: bool = False) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, retryable=retryable)


def _identifier(value: object) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise _error("Vidu response identity is invalid.")
    return value


def _json_object(body: bytes) -> dict[str, object]:
    if len(body) > _MAX_JSON_BYTES:
        raise _error("Vidu JSON response exceeds the size limit.")
    try:
        value = json.loads(body)
    except (ValueError, UnicodeError):
        raise _error("Vidu response is not valid JSON.") from None
    if not isinstance(value, dict):
        raise _error("Vidu response must be an object.")
    return value


@dataclass(frozen=True)
class ViduTransportRequest:
    method: Literal["GET", "POST"]
    url: str = field(repr=False)
    headers: Mapping[str, str] = field(repr=False)
    body: bytes = field(default=b"", repr=False)


@dataclass(frozen=True)
class ViduTransportResponse:
    status_code: int
    headers: Mapping[str, str] = field(repr=False)
    body: bytes = field(repr=False)


class ViduStreamResponse(Protocol):
    status_code: int
    headers: Mapping[str, str]

    def iter_bytes(self) -> Iterator[bytes]: ...


class ViduTransport(Protocol):
    def request(self, request: ViduTransportRequest) -> ViduTransportResponse: ...

    def stream(self, request: ViduTransportRequest) -> AbstractContextManager[ViduStreamResponse]: ...


class HttpxViduTransport:
    def __init__(self, *, client: httpx.Client | None = None,
                 timeout_seconds: float = 60.0) -> None:
        self._client = client or httpx.Client(timeout=timeout_seconds, follow_redirects=False)
        self._owns_client = client is None
        self._timeout = httpx.Timeout(timeout_seconds)
        self._download_timeout = timeout_seconds

    def request(self, request: ViduTransportRequest) -> ViduTransportResponse:
        with self._api_stream(request) as response:
            body = bytearray()
            for chunk in response.iter_bytes():
                if len(body) + len(chunk) > _MAX_JSON_BYTES:
                    raise _error("Vidu JSON response exceeds the size limit.")
                body.extend(chunk)
            return ViduTransportResponse(response.status_code, dict(response.headers), bytes(body))

    @contextmanager
    def stream(self, request: ViduTransportRequest) -> Iterator[ViduStreamResponse]:
        if request.method != "GET" or request.body or dict(request.headers) != {"accept": "video/mp4"}:
            raise _error("Vidu result transport only accepts credential-free video GET.")
        with stream_public_video(request.url, timeout_seconds=self._download_timeout) as response:
            yield response

    @contextmanager
    def _api_stream(self, request: ViduTransportRequest) -> Iterator[ViduStreamResponse]:
        exact = httpx.Request(
            request.method, request.url, headers=dict(request.headers), content=request.body,
            extensions={"timeout": self._timeout.as_dict()},
        )
        response = self._client.send(exact, auth=None, follow_redirects=False, stream=True)
        try:
            yield response
        finally:
            response.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


class _SourceVerificationSink:
    def write(self, chunk: bytes) -> int:
        return len(chunk)

    def flush(self) -> None:
        pass


class ViduVideoProvider:
    def __init__(self, *, profile: ViduProviderProfile, transport: ViduTransport,
                 credential: Callable[[], str],
                 image_resolver: Callable[[VideoImageReferenceBinding], bytes] | None = None,
                 extension_source: Callable[[VideoMediaReferenceBinding], ViduExtensionSource] | None = None,
                 now: Callable[[], datetime] | None = None) -> None:
        self._profile = profile
        self._transport = transport
        self._credential = credential
        self._image_resolver = image_resolver
        self._extension_source = extension_source
        self._now = now or (lambda: datetime.now(UTC))

    def capabilities(self) -> VideoProviderCapabilities:
        return vidu_capabilities()

    def _target_id(self, model_id: str) -> str:
        return f"{self._profile.origin}/{self._profile.pointer().profile_sha256}/{model_id}"

    def compile_request(self, provider_bound: ProviderBoundVideoRequest,
                        requirement: ProviderNeutralVideoRequirement) -> ProviderRequestCompilationResult:
        return compile_provider_video_request(
            provider_bound=provider_bound, requirement=requirement,
            compiler_id="vidu-video-compiler", compiler_version="1",
            capabilities=self.capabilities(),
        )

    def resolve(self, request: VideoGenerationRequest) -> ResolvedVideoGenerationRequest:
        output = request.output_requirement
        if (
            request.provider_name != "vidu" or request.provider_kind != "vidu"
            or request.provider_profile != self._profile.pointer()
            or not isinstance(output, VideoFlexibleOutputRequirement)
            or request.negative_prompt_text
            or len(request.prompt_text) > (2000 if request.mode in (
                VideoGenerationMode.REFERENCE_TO_VIDEO, VideoGenerationMode.VIDEO_EXTEND,
            ) else 5000)
            or (request.seed is not None and not 1 <= request.seed <= 2_147_483_647)
        ):
            raise _error("Vidu request does not match the sealed profile.", ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED)
        variants = tuple(v for v in self.capabilities().variants
                         if v.model_id == request.model_id and v.mode is request.mode
                         and v.output_capability.supports(output))
        if len(variants) != 1:
            raise _error("Vidu request does not match one capability.", ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED)
        if request.mode in (VideoGenerationMode.TEXT_TO_VIDEO, VideoGenerationMode.REFERENCE_TO_VIDEO):
            width, height = (int(value) for value in output.ratio.split(":"))
            if (output.width * height != output.height * width
                    or min(output.width, output.height) != int(output.resolution_label[:-1])):
                raise _error("Vidu output geometry is unsupported.", ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED)
        if request.mode is VideoGenerationMode.VIDEO_EXTEND:
            if (len(request.media_bindings) != 1 or request.media_bindings[0].kind != "video"
                    or request.seed is not None):
                raise _error("Vidu extension requires one video and no seed.", ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED)
            source = request.media_bindings[0]
            extension_millis = output.duration_seconds * 1000 - source.duration_millis
            if (source.duration_millis % 1000 or not 1000 <= extension_millis <= 7000
                    or source.fps != output.fps):
                raise _error("Vidu extension requires 1-7 added seconds and matching FPS.", ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED)
        if any(b.size_bytes is None or b.size_bytes <= 0 or not 0.25 < b.width / b.height < 4
               for b in request.image_bindings):
            raise _error("Vidu input requires exact image bytes and supported geometry.", ErrorCode.VIDEO_REQUEST_INVALID)
        return ResolvedVideoGenerationRequest.create(
            request=request, capability=variants[0], effective_output=output,
            effective_seed=request.seed, effective_negative_prompt_text="",
            provider_task_binding=VideoProviderTaskBinding(
                request_target_id=self._target_id(request.model_id), response_model_id=request.model_id,
            ),
        )

    def preview(self, request: ResolvedVideoGenerationRequest) -> VideoGenerationPreview:
        if request.activation_scope is None or self.resolve(request.activation_scope.request) != request:
            raise _error("Vidu resolved request does not match canonical resolution.", ErrorCode.VIDEO_REQUEST_INVALID)
        if (request.provider_name != "vidu" or request.provider_kind != "vidu"
                or request.provider_profile != self._profile.pointer()
                or request.capability_id not in {v.capability_id for v in self.capabilities().variants}):
            raise _error("Vidu resolved request does not match profile.", ErrorCode.VIDEO_REQUEST_INVALID)
        if not self._profile.pricing_observed_at <= self._now() < self._profile.pricing_expires_at:
            raise _error("Vidu pricing ceiling is not current.", ErrorCode.PAID_PROVIDER_BUDGET_REJECTED)
        return VideoGenerationPreview.create(
            resolved=request, estimated_cost_upper_bound_microunits=self._profile.cost_upper_bound_microunits,
            currency=self._profile.currency, destination=self._profile.origin,
            egress_item_ids=("prompt", *(b.asset_id for b in request.image_bindings),
                             *(b.asset_id for b in request.media_bindings)),
        )

    def _headers(self) -> dict[str, str]:
        try:
            secret = self._credential()
        except Exception:
            raise _error("Vidu credential is unavailable.", ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED) from None
        if not isinstance(secret, str) or not secret or not secret.isascii() or any(ord(c) < 33 or ord(c) > 126 for c in secret):
            raise _error("Vidu credential is invalid.", ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED)
        return {"authorization": f"Token {secret}", "content-type": "application/json", "accept": "application/json"}

    def _payload(self, request: ResolvedVideoGenerationRequest) -> tuple[str, bytes]:
        output = request.effective_output
        payload = dict(model=request.model_id, prompt=request.prompt_text,
                       duration=output.duration_seconds, resolution=output.resolution_label,
                       audio=output.native_audio, off_peak=False)
        if request.effective_seed is not None:
            payload["seed"] = request.effective_seed
        endpoint = {
            VideoGenerationMode.TEXT_TO_VIDEO: "text2video",
            VideoGenerationMode.IMAGE_TO_VIDEO: "img2video",
            VideoGenerationMode.REFERENCE_TO_VIDEO: "reference2video",
            VideoGenerationMode.VIDEO_EXTEND: "extend",
        }[request.mode]
        if request.mode is VideoGenerationMode.VIDEO_EXTEND:
            source = request.media_bindings[0]
            payload["duration"] = output.duration_seconds - source.duration_millis // 1000
            payload["video_creation_id"] = self._extension_creation(source)
            del payload["audio"]
            del payload["off_peak"]
        if request.image_bindings:
            images = []
            for binding in sorted(request.image_bindings, key=lambda b: b.role != "first_frame"):
                try:
                    raw = self._image_resolver(binding) if self._image_resolver else None
                except Exception:
                    raise _error("Vidu image bytes are unavailable.", ErrorCode.VIDEO_REQUEST_INVALID) from None
                if (not isinstance(raw, bytes) or len(raw) != binding.size_bytes
                        or hashlib.sha256(raw).hexdigest() != binding.asset_sha256):
                    raise _error("Vidu image bytes do not match binding.", ErrorCode.VIDEO_REQUEST_INVALID)
                images.append(f"data:{binding.mime_type};base64," + base64.b64encode(raw).decode("ascii"))
            payload["images"] = images
            if request.mode is VideoGenerationMode.IMAGE_TO_VIDEO and len(images) == 2:
                endpoint = "start-end2video"
        if request.mode in (VideoGenerationMode.TEXT_TO_VIDEO, VideoGenerationMode.REFERENCE_TO_VIDEO):
            payload["aspect_ratio"] = output.ratio
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(body) > _MAX_BODY_BYTES:
            raise _error("Vidu request exceeds the body size limit.", ErrorCode.VIDEO_REQUEST_INVALID)
        return endpoint, body

    def _extension_creation(self, binding: VideoMediaReferenceBinding) -> str:
        try:
            source = self._extension_source(binding) if self._extension_source else None
            if not isinstance(source, ViduExtensionSource):
                raise ValueError()
            source = ViduExtensionSource.model_validate_json(source.model_dump_json())
            if not source.matches(binding):
                raise ValueError()
        except Exception:
            raise _error("Vidu extension source evidence is unavailable or mismatched.", ErrorCode.VIDEO_REQUEST_INVALID) from None
        task_id = self._submission(source.submission, source.submit_receipt)
        state, creation_id, _ = self._query(task_id, source.submission.provider_task_binding.response_model_id)
        if (state is not VideoTaskState.SUCCEEDED or creation_id is None
                or self._file_id(task_id, creation_id) != source.fetch_receipt.provider_file_id):
            raise _error("Vidu extension source creation changed.", ErrorCode.VIDEO_REQUEST_INVALID)
        observation = VideoTaskObservation.create(
            submission=source.submission, state=state, observed_at=self._now(), progress_milli=1000,
            provider_file_id=source.fetch_receipt.provider_file_id,
        )
        fetched = self.fetch(source.submission, source.submit_receipt, observation, _SourceVerificationSink())
        if (fetched.artifact_sha256 != binding.asset_sha256 or fetched.size_bytes != binding.size_bytes):
            raise _error("Vidu extension source bytes changed.", ErrorCode.VIDEO_REQUEST_INVALID)
        return creation_id

    def submit(self, request: ResolvedVideoGenerationRequest, video_preview: VideoGenerationPreview,
               paid_preview: PaidProviderCallPreview | None,
               authorization: PaidProviderAuthorizationDecision | None, permit: object | None) -> VideoSubmitResult:
        if video_preview != self.preview(request):
            raise _error("Vidu preview mismatch.", ErrorCode.VIDEO_REQUEST_INVALID)
        if paid_preview is None or authorization is None or type(permit) is not _DurablePaidProviderSubmitPermit:
            raise _error("Vidu submit requires a durable paid permit.", ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED)
        validate_paid_provider_authorization(paid_preview, authorization, now=self._now())
        binding = build_video_paid_permit_binding(request, video_preview, paid_preview, authorization)
        if (paid_preview.secret_reference.kind != "secret_store"
                or paid_preview.secret_reference.reference_id != "VIDU_API_KEY"):
            raise _error("Vidu credential reference mismatch.", ErrorCode.VIDEO_REQUEST_INVALID)
        prompt = request.prompt_text.encode("utf-8")
        expected = {"prompt": (hashlib.sha256(prompt).hexdigest(), len(prompt), "text/plain", "prompt")}
        expected.update({b.asset_id: (b.asset_sha256, b.size_bytes, b.mime_type, "reference") for b in request.image_bindings})
        expected.update({b.asset_id: (b.asset_sha256, b.size_bytes, b.mime_type, "reference") for b in request.media_bindings})
        actual = {i.item_id: (i.sha256, i.size_bytes, i.mime_type, i.purpose) for i in paid_preview.egress_items}
        if actual != expected or len(actual) != len(paid_preview.egress_items):
            raise _error("Vidu egress does not bind exact input bytes.", ErrorCode.VIDEO_REQUEST_INVALID)
        if not permit._validate_paid_provider_operation_permit(**binding):
            raise _error("Vidu permit is invalid.", ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED)
        endpoint, body = self._payload(request)
        transport_request = ViduTransportRequest("POST", f"{self._profile.origin}/ent/v2/{endpoint}", self._headers(), body)
        # Source lookup and input/secret suppliers may outlive the initial authorization.
        validate_paid_provider_authorization(paid_preview, authorization, now=self._now())
        if video_preview != self.preview(request):
            raise _error("Vidu preview changed before submit.", ErrorCode.VIDEO_REQUEST_INVALID)
        if not permit._consume_paid_provider_operation_permit(**binding):
            raise _error("Vidu permit is consumed.", ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED)
        try:
            response = self._transport.request(transport_request)
        except Exception:
            raise _error("Vidu submit outcome is unknown.", ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN) from None
        if response.status_code in _REJECTIONS:
            raise _error(f"Vidu submit rejected with HTTP {response.status_code}.")
        try:
            if not 200 <= response.status_code < 300:
                raise ValueError()
            payload = _json_object(response.body)
            task_id = _identifier(payload.get("task_id"))
            if payload.get("model") != request.model_id or payload.get("state") not in _STATES:
                raise ValueError()
        except (AiVideoError, ValueError, TypeError):
            raise _error("Vidu submit outcome is unknown.", ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN) from None
        return VideoSubmitResult.create(resolved=request, external_effect_id=task_id, submitted_at=self._now())

    def _submission(self, submission: VideoSubmission, receipt: PaidProviderSubmitReceipt) -> str:
        task_binding = submission.provider_task_binding
        if (receipt.outcome is not PaidProviderSubmitOutcome.ACCEPTED
                or receipt.submit_receipt_fingerprint != submission.paid_submit_receipt_fingerprint
                or receipt.request_fingerprint != submission.resolved_generation_hash
                or task_binding is None
                or task_binding.response_model_id not in (*VIDU_MODEL_IDS, *VIDU_REFERENCE_MODEL_IDS, *VIDU_EXTEND_MODEL_IDS)
                or task_binding.request_target_id != self._target_id(task_binding.response_model_id)):
            raise _error("Vidu submission evidence mismatch.", ErrorCode.VIDEO_REQUEST_INVALID)
        return _identifier(receipt.external_effect_id)

    def _query(self, task_id: str, model_id: str) -> tuple[VideoTaskState, str | None, str | None]:
        request = ViduTransportRequest("GET", f"{self._profile.origin}/ent/v2/tasks/{quote(task_id, safe='')}/creations", self._headers())
        try:
            response = self._transport.request(request)
        except Exception:
            raise _error("Vidu query transport failed.", retryable=True) from None
        if not 200 <= response.status_code < 300:
            raise _error(f"Vidu query returned HTTP {response.status_code}.", retryable=response.status_code == 429 or response.status_code >= 500)
        payload = _json_object(response.body)
        if any(payload.get(key, expected) != expected for key, expected in (("id", task_id), ("task_id", task_id), ("model", model_id))):
            raise _error("Vidu query identity changed.")
        state = _STATES.get(payload.get("state")) if isinstance(payload.get("state"), str) else None
        if state is None:
            raise _error("Vidu query state is invalid.")
        if state is not VideoTaskState.SUCCEEDED:
            return state, None, None
        creations = payload.get("creations")
        if not isinstance(creations, list) or len(creations) != 1 or not isinstance(creations[0], dict):
            raise _error("Vidu result must contain exactly one creation.")
        creation = creations[0]
        creation_id = _identifier(creation.get("id"))
        url = creation.get("url")
        if not isinstance(url, str):
            raise _error("Vidu result URL is missing.")
        return state, creation_id, url

    @staticmethod
    def _file_id(task_id: str, creation_id: str) -> str:
        return "vidu-content-" + hashlib.sha256(json.dumps([task_id, creation_id]).encode()).hexdigest()

    def get_status(self, submission: VideoSubmission, submit_receipt: PaidProviderSubmitReceipt) -> VideoTaskObservation:
        task_id = self._submission(submission, submit_receipt)
        state, creation_id, _ = self._query(task_id, submission.provider_task_binding.response_model_id)
        return VideoTaskObservation.create(
            submission=submission, state=state, observed_at=self._now(),
            progress_milli={VideoTaskState.QUEUED: 0, VideoTaskState.RUNNING: 500,
                            VideoTaskState.SUCCEEDED: 1000, VideoTaskState.FAILED: 1000}[state],
            provider_file_id=self._file_id(task_id, creation_id) if creation_id is not None else None,
        )

    def _result_url(self, url: str) -> str:
        locator = parse_result_url(url)
        if self._profile.result_trust == "fixed_origins" and locator.origin not in self._profile.result_origins:
            raise _error("Vidu result URL is outside the sealed origins.")
        return url

    def fetch(self, submission: VideoSubmission, submit_receipt: PaidProviderSubmitReceipt,
              observation: VideoTaskObservation, sink: BinaryIO) -> VideoFetchReceipt:
        task_id = self._submission(submission, submit_receipt)
        if (observation.submission_fingerprint != submission.submission_fingerprint
                or observation.paid_submit_receipt_fingerprint != submission.paid_submit_receipt_fingerprint
                or observation.state is not VideoTaskState.SUCCEEDED):
            raise _error("Vidu fetch evidence mismatch.", ErrorCode.VIDEO_REQUEST_INVALID)
        state, creation_id, url = self._query(task_id, submission.provider_task_binding.response_model_id)
        if (state is not VideoTaskState.SUCCEEDED or creation_id is None or url is None
                or self._file_id(task_id, creation_id) != observation.provider_file_id):
            raise _error("Vidu result identity changed.")
        request = ViduTransportRequest("GET", self._result_url(url), {"accept": "video/mp4"})
        size, prefix, digest = 0, bytearray(), hashlib.sha256()
        declared = None
        try:
            with self._transport.stream(request) as response:
                headers = {k.lower(): v for k, v in response.headers.items()}
                if response.status_code != 200 or headers.get("content-type", "").split(";", 1)[0].strip().lower() != "video/mp4":
                    raise _error("Vidu download must be an HTTP 200 MP4.", ErrorCode.VIDEO_ARTIFACT_INVALID)
                if "content-length" in headers:
                    value = headers["content-length"]
                    if not value.isascii() or not value.isdecimal():
                        raise _error("Vidu download length is invalid.", ErrorCode.VIDEO_ARTIFACT_INVALID)
                    declared = int(value)
                    if not 0 < declared <= self._profile.max_download_bytes:
                        raise _error("Vidu download length exceeds limit.", ErrorCode.VIDEO_ARTIFACT_INVALID)
                for chunk in response.iter_bytes():
                    if size + len(chunk) > self._profile.max_download_bytes:
                        raise _error("Vidu download exceeds limit.", ErrorCode.VIDEO_ARTIFACT_INVALID)
                    prefix.extend(chunk[:max(0, 32 - len(prefix))])
                    sink.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
        except AiVideoError:
            raise
        except Exception:
            raise _error("Vidu download transport failed.", retryable=True) from None
        if (size < 12 or prefix[4:8] != b"ftyp" or bytes(prefix[8:12]) not in {b"isom", b"iso2", b"mp41", b"mp42", b"avc1"}
                or (declared is not None and declared != size)):
            raise _error("Vidu download is not a complete MP4.", ErrorCode.VIDEO_ARTIFACT_INVALID)
        sink.flush()
        fetched_at = self._now()
        materialization = None
        if self._profile.result_trust == "authenticated_task":
            materialization = RemoteMediaMaterializationReceipt.create(
                transport_kind="provider_output_https", provider_kind="vidu",
                model_id=submission.provider_task_binding.response_model_id,
                submission_fingerprint=submission.submission_fingerprint,
                paid_submit_receipt_fingerprint=submission.paid_submit_receipt_fingerprint,
                provider_file_id=observation.provider_file_id,
                remote_origin=parse_result_url(url).origin,
                remote_locator_sha256=hashlib.sha256(url.encode()).hexdigest(),
                artifact_sha256=digest.hexdigest(), artifact_size_bytes=size,
                artifact_mime_type="video/mp4", accessibility_verification="exact_get",
                verified_at=fetched_at,
            )
        return VideoFetchReceipt.create(
            submission=submission, observation=observation, content_type="video/mp4",
            size_bytes=size, artifact_sha256=digest.hexdigest(), fetched_at=fetched_at,
            remote_materialization=materialization,
        )
