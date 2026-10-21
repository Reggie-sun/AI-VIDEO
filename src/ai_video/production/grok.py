"""SuperGrok subscription-backed video Provider adapter."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import BinaryIO, Literal, Protocol
from urllib.parse import quote, unquote, urlsplit

import httpx
from pydantic_core import PydanticSerializationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.grok_download import (
    parse_grok_result_url,
    stream_public_grok_video,
)
from ai_video.production.grok_profile import (
    GROK_VIDEO_MODEL,
    GrokProviderProfile,
    grok_capabilities,
)
from ai_video.production.grok_video_request import (
    MAX_GROK_POST_BODY_BYTES,
    build_grok_video_operation,
    grok_endpoint_for_mode,
    grok_egress_inputs,
    validate_grok_video_request,
)
from ai_video.production.grok_subscription import (
    GROK_CREDENTIAL_REFERENCE,
    GrokSubscriptionBinding,
    reject_unverified_included_only,
    require_current_subscription,
)
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
    validate_paid_provider_authorization,
)
from ai_video.production.remote_media import RemoteMediaMaterializationReceipt
from ai_video.production.shot_router import ProviderBoundVideoRequest
from ai_video.production.state_commit import _DurablePaidProviderSubmitPermit
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoFetchReceipt,
    VideoFlexibleOutputRequirement,
    VideoGenerationMode,
    VideoGenerationPreview,
    VideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoMediaReferenceBinding,
    VideoProviderCapabilities,
    VideoProviderTaskBinding,
    VideoSubmission,
    VideoSubmitResult,
    VideoTaskObservation,
    VideoTaskState,
    build_video_paid_permit_binding,
)
from ai_video.production.video_compiler import (
    ProviderNativePrompt,
    ProviderRequestCompilationResult,
    ProviderRequirementUnsupported,
    ProviderRequirementUnsupportedReason,
    compile_provider_video_request,
)
from ai_video.production.video_requirement import ProviderNeutralVideoRequirement


_API_BASE = "https://cli-chat-proxy.grok.com/v1"
_API_ORIGIN = "https://cli-chat-proxy.grok.com"
_MAX_JSON_BYTES = 1_000_000
_MAX_BODY_BYTES = MAX_GROK_POST_BODY_BYTES
_SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_KNOWN_SUBMIT_REJECTIONS = frozenset({400, 401, 403, 404, 405, 413, 415, 422})


def _error(
    message: str,
    code: ErrorCode = ErrorCode.VIDEO_PROVIDER_FAILED,
    *,
    retryable: bool = False,
) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, retryable=retryable)


def _identifier(value: object) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None or value in {".", ".."}:
        raise _error("Grok response identity is invalid.")
    return value


def _json_object(body: bytes) -> dict[str, object]:
    if len(body) > _MAX_JSON_BYTES:
        raise _error("Grok JSON response exceeds the size limit.")
    try:
        value = json.loads(body)
    except (ValueError, UnicodeError, TypeError):
        raise _error("Grok response is not valid JSON.") from None
    if not isinstance(value, dict):
        raise _error("Grok response must be an object.")
    return value


@dataclass(frozen=True)
class GrokTransportRequest:
    method: Literal["GET", "POST"]
    url: str = field(repr=False)
    headers: Mapping[str, str] = field(repr=False)
    body: bytes = field(default=b"", repr=False)


@dataclass(frozen=True)
class GrokTransportResponse:
    status_code: int
    headers: Mapping[str, str] = field(repr=False)
    body: bytes = field(repr=False)


class GrokStreamResponse(Protocol):
    status_code: int
    headers: Mapping[str, str]

    def iter_bytes(self) -> Iterator[bytes]: ...


class GrokTransport(Protocol):
    def request(self, request: GrokTransportRequest) -> GrokTransportResponse: ...

    def stream(
        self, request: GrokTransportRequest
    ) -> AbstractContextManager[GrokStreamResponse]: ...


class HttpxGrokTransport:
    """Exact-origin API transport and credential-free pinned result streaming."""

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        self._client = client or httpx.Client(
            timeout=timeout_seconds, follow_redirects=False
        )
        self._owns_client = client is None
        self._timeout = httpx.Timeout(timeout_seconds)
        self._download_timeout = timeout_seconds

    def request(self, request: GrokTransportRequest) -> GrokTransportResponse:
        self._validate_api_request(request)
        with self._api_stream(request) as response:
            body = bytearray()
            for chunk in response.iter_bytes():
                if len(body) + len(chunk) > _MAX_JSON_BYTES:
                    raise _error("Grok JSON response exceeds the size limit.")
                body.extend(chunk)
            return GrokTransportResponse(
                response.status_code, dict(response.headers), bytes(body)
            )

    @contextmanager
    def stream(
        self, request: GrokTransportRequest
    ) -> Iterator[GrokStreamResponse]:
        if request.method != "GET" or request.body or dict(request.headers) != {"accept": "*/*"}:
            raise _error(
                "Grok result downloads must be credential-free GETs.",
                ErrorCode.VIDEO_ARTIFACT_INVALID,
            )
        parse_grok_result_url(request.url)
        with stream_public_grok_video(
            request.url, timeout_seconds=self._download_timeout
        ) as response:
            yield response

    @staticmethod
    def _validate_api_request(request: GrokTransportRequest) -> None:
        try:
            parsed = urlsplit(request.url)
            origin = f"{parsed.scheme}://{parsed.netloc}"
        except (TypeError, ValueError):
            raise _error("Grok API destination is invalid.", ErrorCode.VIDEO_REQUEST_INVALID) from None
        if (
            request.method not in {"GET", "POST"}
            or origin != _API_ORIGIN
            or parsed.path.startswith("/") is False
            or parsed.query
            or parsed.fragment
            or parsed.username is not None
            or parsed.password is not None
            or (
                request.method == "POST"
                and parsed.path not in {
                    "/v1/videos/generations",
                    "/v1/videos/edits",
                    "/v1/videos/extensions",
                }
            )
            or (
                request.method == "GET"
                and (not parsed.path.startswith("/v1/videos/")
                     or parsed.path.count("/") != 3)
            )
            or len(request.body) > _MAX_BODY_BYTES
        ):
            raise _error("Grok API request is outside the sealed endpoint.", ErrorCode.VIDEO_REQUEST_INVALID)
        expected_headers = (
            {"authorization", "content-type", "accept"}
            if request.method == "POST"
            else {"authorization", "accept"}
        )
        if {key.lower() for key in request.headers} != expected_headers:
            raise _error("Grok API request headers are invalid.", ErrorCode.VIDEO_REQUEST_INVALID)
        if request.method == "GET":
            segment = parsed.path.rsplit("/", 1)[1]
            try:
                task_id = _identifier(unquote(segment))
            except AiVideoError:
                raise _error("Grok task query identity is invalid.", ErrorCode.VIDEO_REQUEST_INVALID) from None
            if segment != quote(task_id, safe=""):
                raise _error("Grok task query identity is not canonical.", ErrorCode.VIDEO_REQUEST_INVALID)

    @contextmanager
    def _api_stream(self, request: GrokTransportRequest) -> Iterator[httpx.Response]:
        exact = httpx.Request(
            request.method,
            request.url,
            headers=dict(request.headers),
            content=request.body,
            extensions={"timeout": self._timeout.as_dict()},
        )
        response = self._client.send(
            exact, auth=None, follow_redirects=False, stream=True
        )
        try:
            yield response
        finally:
            response.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


class GrokVideoProvider:
    causal_expression_grammar = "remote-video-prose-v1"

    def __init__(
        self,
        *,
        profile: GrokProviderProfile,
        credential: Callable[[], str],
        subscription_guard: Callable[[GrokSubscriptionBinding], object]
        | None = None,
        transport: GrokTransport | None = None,
        image_resolver: Callable[[VideoImageReferenceBinding], bytes] | None = None,
        media_resolver: Callable[[VideoMediaReferenceBinding], bytes] | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._profile = profile
        self._credential = credential
        self._subscription_guard = subscription_guard or reject_unverified_included_only
        self._transport = transport or HttpxGrokTransport()
        self._image_resolver = image_resolver
        self._media_resolver = media_resolver
        self._now = now or (lambda: datetime.now(UTC))

    def capabilities(self) -> VideoProviderCapabilities:
        return grok_capabilities(self._profile)

    def _target_id(self, model_id: str, mode: VideoGenerationMode) -> str:
        endpoint = grok_endpoint_for_mode(mode)
        return f"{_API_BASE}/videos/{endpoint}/{self._profile.pointer().profile_sha256}/{model_id}"

    def compile_request(
        self,
        provider_bound: ProviderBoundVideoRequest,
        requirement: ProviderNeutralVideoRequirement,
        *,
        continuity_expression=None,
    ) -> ProviderRequestCompilationResult:
        try:
            ProviderBoundVideoRequest.model_validate(
                provider_bound.model_dump(mode="python")
            )
            ProviderNeutralVideoRequirement.model_validate(
                requirement.model_dump(mode="python")
            )
        except (PydanticSerializationError, ValueError):
            return ProviderRequirementUnsupported(
                requirement_hash=requirement.requirement_hash,
                provider_bound_request_hash=provider_bound.provider_bound_request_hash,
                selected_capability_id=provider_bound.capability_id,
                reason=ProviderRequirementUnsupportedReason.LINEAGE_MISMATCH,
                unsupported_field_paths=("requirement_hash",),
            )

        from ai_video.production._remote_video_native_prompt import (
            RemoteVideoPromptCompilation,
            compile_remote_video_prompt,
        )

        prompt = compile_remote_video_prompt(
            requirement,
            voice_route=provider_bound.voice_route,
            provider_bound=provider_bound,
            continuity_expression=continuity_expression,
        )
        if not isinstance(prompt, RemoteVideoPromptCompilation):
            return ProviderRequirementUnsupported(
                requirement_hash=requirement.requirement_hash,
                provider_bound_request_hash=provider_bound.provider_bound_request_hash,
                selected_capability_id=provider_bound.capability_id,
                reason=ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED,
                unsupported_field_paths=prompt.unsupported_field_paths,
            )
        return compile_provider_video_request(
            provider_bound=provider_bound,
            requirement=requirement,
            compiler_id="grok-video-compiler",
            compiler_version="1",
            capabilities=self.capabilities(),
            continuity_expression=continuity_expression,
            native_prompt=ProviderNativePrompt(
                grammar_contract=self.causal_expression_grammar,
                prompt_text=prompt.prompt_text,
                prompt_sha256=prompt.prompt_sha256,
                expressed_control_paths=prompt.expressed_control_paths,
            ),
        )

    def resolve(self, request: VideoGenerationRequest) -> ResolvedVideoGenerationRequest:
        output = request.output_requirement
        capabilities = self.capabilities()
        if (
            request.provider_name != "grok"
            or request.provider_kind != "grok"
            or request.provider_profile != self._profile.pointer()
            or request.model_id not in {variant.model_id for variant in capabilities.variants}
            or not isinstance(output, VideoFlexibleOutputRequirement)
            or request.negative_prompt_text
            or request.seed is not None
            or output.fps is not None
        ):
            raise _error(
                "Grok request does not match the sealed video profile.",
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
            )
        variants = tuple(
            variant
            for variant in capabilities.variants
            if variant.model_id == request.model_id
            and variant.mode is request.mode
            and variant.output_capability is not None
            and variant.output_capability.supports(output)
        )
        if not variants:
            raise _error(
                "Grok request does not match a documented video capability.",
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
            )
        compatible: list[ResolvedVideoGenerationRequest] = []
        for variant in variants:
            try:
                resolved = ResolvedVideoGenerationRequest.create(
                    request=request,
                    capability=variant,
                    effective_output=output,
                    effective_seed=None,
                    effective_negative_prompt_text="",
                    provider_task_binding=VideoProviderTaskBinding(
                        request_target_id=self._target_id(request.model_id, request.mode),
                        response_model_id=request.model_id,
                    ),
                )
                validate_grok_video_request(
                    resolved,
                    profile=self._profile,
                    capabilities=capabilities,
                    variant=variant,
                )
            except AiVideoError:
                continue
            compatible.append(resolved)
        if len(compatible) != 1:
            raise _error(
                "Grok request does not identify exactly one supported model and operation shape.",
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
            )
        return compatible[0]

    def preview(self, request: ResolvedVideoGenerationRequest) -> VideoGenerationPreview:
        if (
            request.activation_scope is None
            or self.resolve(request.activation_scope.request) != request
            or request.provider_name != "grok"
            or request.provider_kind != "grok"
            or request.provider_profile != self._profile.pointer()
            or request.capability_id
            not in {variant.capability_id for variant in self.capabilities().variants}
        ):
            raise _error("Grok resolved request does not match its profile.", ErrorCode.VIDEO_REQUEST_INVALID)
        return VideoGenerationPreview.create(
            resolved=request,
            estimated_cost_upper_bound_microunits=0,
            currency="USD",
            destination=self._profile.origin,
            egress_item_ids=(
                "prompt",
                *(item.asset_id for item in grok_egress_inputs(request)),
            ),
        )

    def _headers(self, *, method: Literal["GET", "POST"]) -> dict[str, str]:
        try:
            secret = self._credential()
        except Exception:
            raise _error(
                "Grok credential is unavailable.",
                ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED,
            ) from None
        if (
            not isinstance(secret, str)
            or not secret
            or not secret.isascii()
            or any(ord(char) < 33 or ord(char) > 126 for char in secret)
        ):
            raise _error(
                "Grok credential is invalid.",
                ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED,
            )
        headers = {"authorization": f"Bearer {secret}", "accept": "application/json"}
        if method == "POST":
            headers["content-type"] = "application/json"
        return headers

    def _subscription_binding(
        self,
        request: ResolvedVideoGenerationRequest,
        paid_preview: PaidProviderCallPreview,
    ) -> GrokSubscriptionBinding:
        binding = paid_preview.subscription_binding
        operation_path = f"/v1/videos/{grok_endpoint_for_mode(request.mode)}"
        legacy_generation_binding = (
            request.model_id == GROK_VIDEO_MODEL
            and operation_path == "/v1/videos/generations"
            and getattr(binding, "operation_path", None) is None
        )
        if (
            paid_preview.billing_mode != "remote_subscription"
            or binding is None
            or paid_preview.provider_kind != "grok"
            or paid_preview.operation != "video_generation"
            or paid_preview.model_id != request.model_id
            or paid_preview.destination != self._profile.origin
            or paid_preview.currency != "USD"
            or paid_preview.estimated_cost_upper_bound_microunits != 0
            or binding.account_fingerprint != self._profile.account_fingerprint
            or binding.model_id != request.model_id
            or binding.destination != self._profile.origin
            or binding.credential_reference_id != GROK_CREDENTIAL_REFERENCE
            or (
                getattr(binding, "operation_path", None) != operation_path
                and not legacy_generation_binding
            )
            or paid_preview.secret_reference.kind != "secret_store"
            or paid_preview.secret_reference.reference_id != GROK_CREDENTIAL_REFERENCE
            or paid_preview.subscription_binding != binding
        ):
            raise _error(
                "Grok subscription preview does not match the selected account and model.",
                ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            )
        return binding

    def _require_current_subscription(
        self,
        request: ResolvedVideoGenerationRequest,
        binding: GrokSubscriptionBinding,
    ) -> None:
        now = self._now()
        require_current_subscription(
            binding,
            account_fingerprint=self._profile.account_fingerprint,
            model_id=request.model_id,
            destination=self._profile.origin,
            operation_path=f"/v1/videos/{grok_endpoint_for_mode(request.mode)}",
            now=now,
        )
        try:
            admitted = self._subscription_guard(binding)
        except AiVideoError:
            raise
        except Exception:
            raise _error(
                "Grok included-only subscription authority could not be verified.",
                ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            ) from None
        if admitted is False:
            raise _error(
                "Grok included-only subscription authority was denied.",
                ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            )

    def _validate_egress(self, request, paid_preview: PaidProviderCallPreview) -> None:
        prompt = request.prompt_text.encode("utf-8")
        expected = {
            "prompt": (
                hashlib.sha256(prompt).hexdigest(), len(prompt), "text/plain", "prompt"
            )
        }
        exact_inputs = grok_egress_inputs(request)
        expected.update({
            item.asset_id: (
                item.asset_sha256,
                item.size_bytes,
                item.mime_type,
                "reference",
            )
            for item in exact_inputs
        })
        actual = {
            item.item_id: (item.sha256, item.size_bytes, item.mime_type, item.purpose)
            for item in paid_preview.egress_items
        }
        if (
            actual != expected
            or len(actual) != len(paid_preview.egress_items)
            or tuple(item.item_id for item in paid_preview.egress_items)
            != ("prompt", *(item.asset_id for item in exact_inputs))
        ):
            raise _error("Grok egress does not bind exact input bytes.", ErrorCode.VIDEO_REQUEST_INVALID)

    def submit(
        self,
        request: ResolvedVideoGenerationRequest,
        video_preview: VideoGenerationPreview,
        paid_preview: PaidProviderCallPreview | None,
        authorization: PaidProviderAuthorizationDecision | None,
        permit: object | None,
    ) -> VideoSubmitResult:
        if video_preview != self.preview(request):
            raise _error("Grok preview mismatch.", ErrorCode.VIDEO_REQUEST_INVALID)
        if (
            paid_preview is None
            or authorization is None
            or type(permit) is not _DurablePaidProviderSubmitPermit
        ):
            raise _error(
                "Grok submit requires a durable subscription permit.",
                ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
            )
        validate_paid_provider_authorization(
            paid_preview, authorization, now=self._now()
        )
        binding = self._subscription_binding(request, paid_preview)
        if authorization.subscription_submit_limit is None:
            raise _error(
                "Grok subscription submit count is not bounded.",
                ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            )
        self._validate_egress(request, paid_preview)
        permit_binding = build_video_paid_permit_binding(
            request, video_preview, paid_preview, authorization
        )
        if not permit._validate_paid_provider_operation_permit(**permit_binding):
            raise _error(
                "Grok submit permit is invalid.",
                ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
            )

        self._require_current_subscription(request, binding)
        operation = build_grok_video_operation(
            request,
            profile=self._profile,
            capabilities=self.capabilities(),
            image_resolver=self._image_resolver,
            media_resolver=self._media_resolver,
        )
        body = operation.body
        headers = self._headers(method="POST")
        validate_paid_provider_authorization(
            paid_preview, authorization, now=self._now()
        )
        self._require_current_subscription(request, binding)
        if video_preview != self.preview(request):
            raise _error("Grok preview changed before submit.", ErrorCode.VIDEO_REQUEST_INVALID)
        if not permit._consume_paid_provider_operation_permit(**permit_binding):
            raise _error(
                "Grok submit permit is consumed.",
                ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
            )
        try:
            validate_paid_provider_authorization(
                paid_preview, authorization, now=self._now()
            )
            self._require_current_subscription(request, binding)
        except AiVideoError:
            raise _error("Grok authorization is no longer current before POST.") from None

        transport_request = GrokTransportRequest(
            "POST", f"{_API_BASE}/videos/{operation.endpoint}", headers, body
        )
        try:
            response = self._transport.request(transport_request)
        except Exception:
            raise _error(
                "Grok submit outcome is unknown.",
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
            ) from None
        if response.status_code in _KNOWN_SUBMIT_REJECTIONS:
            raise _error(f"Grok submit was rejected with HTTP {response.status_code}.")
        if not 200 <= response.status_code < 300:
            raise _error(
                "Grok submit outcome is unknown.",
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
            )
        try:
            payload = _json_object(response.body)
            task_id = _identifier(payload.get("request_id"))
        except (AiVideoError, TypeError, ValueError):
            raise _error(
                "Grok submit outcome is unknown.",
                ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
            ) from None
        return VideoSubmitResult.create(
            resolved=request, external_effect_id=task_id, submitted_at=self._now()
        )

    def _submission(
        self,
        submission: VideoSubmission,
        receipt: PaidProviderSubmitReceipt,
    ) -> str:
        task_binding = submission.provider_task_binding
        allowed_targets = {
            self._target_id(variant.model_id, variant.mode)
            for variant in self.capabilities().variants
        }
        if (
            receipt.outcome is not PaidProviderSubmitOutcome.ACCEPTED
            or receipt.submit_receipt_fingerprint
            != submission.paid_submit_receipt_fingerprint
            or receipt.request_fingerprint != submission.resolved_generation_hash
            or task_binding is None
            or task_binding.request_target_id not in allowed_targets
            or not any(
                variant.model_id == task_binding.response_model_id
                and self._target_id(variant.model_id, variant.mode)
                == task_binding.request_target_id
                for variant in self.capabilities().variants
            )
        ):
            raise _error("Grok submission evidence does not match.", ErrorCode.VIDEO_REQUEST_INVALID)
        return _identifier(receipt.external_effect_id)

    def _query(self, task_id: str, model_id: str) -> tuple[VideoTaskState, str | None]:
        request = GrokTransportRequest(
            "GET",
            f"{_API_BASE}/videos/{quote(task_id, safe='')}",
            self._headers(method="GET"),
        )
        try:
            response = self._transport.request(request)
        except Exception:
            raise _error("Grok task query failed.", retryable=True) from None
        if not 200 <= response.status_code < 300:
            raise _error(
                f"Grok task query returned HTTP {response.status_code}.",
                retryable=response.status_code == 429 or response.status_code >= 500,
            )
        payload = _json_object(response.body)
        if (
            payload.get("request_id", task_id) != task_id
            or payload.get("model", model_id) != model_id
        ):
            raise _error("Grok task response identity changed.")
        status = payload.get("status")
        if status == "pending":
            return VideoTaskState.RUNNING, None
        if status == "failed":
            return VideoTaskState.FAILED, None
        if status != "done" or payload.get("model") != model_id:
            raise _error("Grok completed task response is invalid.")
        video = payload.get("video")
        if not isinstance(video, dict) or video.get("respect_moderation") is not True:
            raise _error("Grok completed video is missing moderation evidence.")
        url = video.get("url")
        if not isinstance(url, str):
            raise _error("Grok completed video URL is missing.")
        parse_grok_result_url(url)
        return VideoTaskState.SUCCEEDED, url

    @staticmethod
    def _file_id(task_id: str, model_id: str) -> str:
        digest = hashlib.sha256(f"{model_id}\0{task_id}".encode("utf-8")).hexdigest()
        return f"grok-video-{digest}"

    def get_status(
        self,
        submission: VideoSubmission,
        submit_receipt: PaidProviderSubmitReceipt,
    ) -> VideoTaskObservation:
        task_id = self._submission(submission, submit_receipt)
        model_id = submission.provider_task_binding.response_model_id
        state, _ = self._query(task_id, model_id)
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
            provider_file_id=(self._file_id(task_id, model_id)
                              if state is VideoTaskState.SUCCEEDED else None),
        )

    def _stream_mp4(self, url: str, sink: BinaryIO) -> tuple[str, int]:
        parse_grok_result_url(url)
        request = GrokTransportRequest("GET", url, {"accept": "*/*"})
        size = 0
        prefix = bytearray()
        digest = hashlib.sha256()
        declared: str | None = None
        try:
            with self._transport.stream(request) as response:
                headers = {key.lower(): value for key, value in response.headers.items()}
                if response.status_code != 200:
                    raise _error(
                        "Grok video download must return HTTP 200.",
                        ErrorCode.VIDEO_ARTIFACT_INVALID,
                    )
                declared = headers.get("content-length")
                for chunk in response.iter_bytes():
                    prefix.extend(chunk[:max(0, 32 - len(prefix))])
                    sink.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
                sink.flush()
        except AiVideoError:
            raise
        except Exception:
            raise _error("Grok video download failed.", retryable=True) from None
        declared_size: int | None = None
        if declared is not None:
            if not declared.isascii() or not declared.isdecimal():
                raise _error("Grok video download length is invalid.", ErrorCode.VIDEO_ARTIFACT_INVALID)
            declared_size = int(declared)
        if (
            size < 12
            or prefix[4:8] != b"ftyp"
            or (declared_size is not None and declared_size != size)
        ):
            raise _error("Grok video download is not a complete MP4.", ErrorCode.VIDEO_ARTIFACT_INVALID)
        return digest.hexdigest(), size

    def fetch(
        self,
        submission: VideoSubmission,
        submit_receipt: PaidProviderSubmitReceipt,
        observation: VideoTaskObservation,
        sink: BinaryIO,
    ) -> VideoFetchReceipt:
        task_id = self._submission(submission, submit_receipt)
        if (
            observation.submission_fingerprint != submission.submission_fingerprint
            or observation.paid_submit_receipt_fingerprint
            != submission.paid_submit_receipt_fingerprint
            or observation.state is not VideoTaskState.SUCCEEDED
        ):
            raise _error("Grok fetch observation does not match submission.", ErrorCode.VIDEO_REQUEST_INVALID)
        model_id = submission.provider_task_binding.response_model_id
        state, url = self._query(task_id, model_id)
        if (
            state is not VideoTaskState.SUCCEEDED
            or url is None
            or self._file_id(task_id, model_id) != observation.provider_file_id
        ):
            raise _error("Grok result identity changed before download.")
        artifact_sha256, size = self._stream_mp4(url, sink)
        fetched_at = self._now()
        result_locator = parse_grok_result_url(url)
        materialization = RemoteMediaMaterializationReceipt.create(
            transport_kind=("provider_output_https" if result_locator.scheme == "https"
                            else "provider_output_http"),
            provider_kind="grok",
            model_id=model_id,
            submission_fingerprint=submission.submission_fingerprint,
            paid_submit_receipt_fingerprint=submission.paid_submit_receipt_fingerprint,
            provider_file_id=observation.provider_file_id,
            remote_origin=result_locator.origin,
            remote_locator_sha256=hashlib.sha256(url.encode("utf-8")).hexdigest(),
            artifact_sha256=artifact_sha256,
            artifact_size_bytes=size,
            artifact_mime_type="video/mp4",
            accessibility_verification="exact_get",
            verified_at=fetched_at,
        )
        return VideoFetchReceipt.create(
            submission=submission,
            observation=observation,
            content_type="video/mp4",
            size_bytes=size,
            artifact_sha256=artifact_sha256,
            fetched_at=fetched_at,
            remote_materialization=materialization,
        )


__all__ = [
    "GrokTransportRequest",
    "GrokTransportResponse",
    "GrokVideoProvider",
    "HttpxGrokTransport",
]
