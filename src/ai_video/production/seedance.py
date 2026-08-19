"""Volcano Ark Seedance generated-video Provider adapter.

The adapter owns Ark payload/status/download mapping only. It consumes the
shared Paid Provider permit immediately before its single submit POST and
keeps credentials, provider asset references, result URLs, and raw responses
out of durable production contracts.
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
from ai_video.production.seedance_capabilities import (
    SEEDANCE_MODEL_IDS,
    SeedanceCapabilityProfile,
    SeedanceOutputRaster,
)
from ai_video.production.seedance_profile import (
    SEEDANCE_ORIGIN,
    SeedancePricingSnapshot,
    SeedanceProviderProfile,
)
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
    VideoSubmission,
    VideoSubmitResult,
    VideoTaskObservation,
    VideoTaskState,
    VideoProviderTaskBinding,
    build_video_paid_permit_binding,
)


ARK_API_KEY_REFERENCE = "ARK_API_KEY"

_SUBMIT_URL = f"{SEEDANCE_ORIGIN}/api/v3/contents/generations/tasks"
_QUERY_URL = f"{SEEDANCE_ORIGIN}/api/v3/contents/generations/tasks/{{task_id}}"
_PROVIDER_NAME = "seedance"
_PROVIDER_KIND = "volcengine_ark_seedance"
_MAX_JSON_BYTES = 1_000_000
_SAFE_TASK_ID = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_SAFE_ASSET_REFERENCE = re.compile(r"^asset://[A-Za-z0-9._:/-]{1,256}$")
_FILE_ID_PREFIX = "seedance-content-"
_MP4_MAJOR_BRANDS = {
    b"M4V ",
    b"avc1",
    b"iso2",
    b"iso5",
    b"iso6",
    b"isom",
    b"mp41",
    b"mp42",
}


def _error(code: ErrorCode, message: str, *, retryable: bool = False) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, retryable=retryable)


def _matches_iso_bmff_container(
    *, content_type: str, prefix: bytes, size_bytes: int
) -> bool:
    if len(prefix) < 16 or prefix[4:8] != b"ftyp":
        return False
    box_size = int.from_bytes(prefix[:4], "big")
    if box_size < 16 or box_size > size_bytes:
        return False
    major_brand = prefix[8:12]
    if content_type == "video/quicktime":
        return major_brand == b"qt  "
    return major_brand in _MP4_MAJOR_BRANDS


def _unknown_submit() -> AiVideoError:
    return _error(
        ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
        "Seedance submit outcome is unknown after permit consumption.",
    )


@dataclass(frozen=True)
class SeedanceTransportRequest:
    method: Literal["GET", "POST"]
    url: str = field(repr=False)
    headers: Mapping[str, str] = field(repr=False)
    body: bytes = field(default=b"", repr=False)


@dataclass(frozen=True)
class SeedanceTransportResponse:
    status_code: int
    headers: Mapping[str, str] = field(repr=False)
    body: bytes = field(repr=False)


class SeedanceStreamResponse(Protocol):
    status_code: int
    headers: Mapping[str, str]

    def iter_bytes(self) -> Iterator[bytes]: ...


class SeedanceTransport(Protocol):
    def request(self, request: SeedanceTransportRequest) -> SeedanceTransportResponse: ...

    def stream(
        self, request: SeedanceTransportRequest
    ) -> AbstractContextManager[SeedanceStreamResponse]: ...


class HttpxSeedanceTransport:
    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        self._client = client or httpx.Client(
            timeout=httpx.Timeout(timeout_seconds), follow_redirects=False
        )
        self._owns_client = client is None

    def request(self, request: SeedanceTransportRequest) -> SeedanceTransportResponse:
        response = self._client.request(
            request.method,
            request.url,
            headers=dict(request.headers),
            content=request.body,
            follow_redirects=False,
        )
        return SeedanceTransportResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=response.content,
        )

    def stream(
        self, request: SeedanceTransportRequest
    ) -> AbstractContextManager[SeedanceStreamResponse]:
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


InputReferenceResolver = Callable[
    [VideoImageReferenceBinding | VideoMediaReferenceBinding], str
]
CredentialResolver = Callable[[], str]


def _json_object(body: bytes, *, surface: str) -> dict[str, object]:
    if len(body) > _MAX_JSON_BYTES:
        raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, f"Seedance {surface} is too large.")
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, f"Seedance {surface} is invalid.") from None
    if not isinstance(value, dict):
        raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, f"Seedance {surface} is invalid.")
    return value


def _task_id(value: object, *, surface: str) -> str:
    if not isinstance(value, str) or _SAFE_TASK_ID.fullmatch(value) is None:
        raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, f"Seedance {surface} task ID is invalid.")
    return value


def _provider_file_id(task_id: str) -> str:
    return _FILE_ID_PREFIX + hashlib.sha256(task_id.encode()).hexdigest()


def _validate_submission(
    submission: VideoSubmission, receipt: PaidProviderSubmitReceipt
) -> str:
    if (
        receipt.outcome is not PaidProviderSubmitOutcome.ACCEPTED
        or receipt.submit_receipt_fingerprint != submission.paid_submit_receipt_fingerprint
        or receipt.request_fingerprint != submission.resolved_generation_hash
        or receipt.external_effect_id is None
    ):
        raise _error(
            ErrorCode.VIDEO_REQUEST_INVALID,
            "Seedance evidence does not match the submitted generation.",
        )
    return _task_id(receipt.external_effect_id, surface="submit receipt")


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


class SeedanceVideoProvider:
    def __init__(
        self,
        *,
        profile: SeedanceProviderProfile,
        transport: SeedanceTransport,
        credential: CredentialResolver,
        input_reference: InputReferenceResolver,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._profile = profile
        self._transport = transport
        self._credential = credential
        self._input_reference = input_reference
        self._now = now or (lambda: datetime.now(UTC))
        self._profiles_by_capability = {
            entry.variant.capability_id: entry for entry in profile.capabilities
        }
        self._capabilities = VideoProviderCapabilities.create(
            provider_name=_PROVIDER_NAME,
            variants=tuple(entry.variant for entry in profile.capabilities),
        )

    def capabilities(self) -> VideoProviderCapabilities:
        return self._capabilities

    def resolve(self, request: VideoGenerationRequest) -> ResolvedVideoGenerationRequest:
        if (
            request.provider_name != _PROVIDER_NAME
            or request.provider_kind != _PROVIDER_KIND
            or request.model_id not in SEEDANCE_MODEL_IDS
            or request.provider_profile != self._profile.pointer()
            or not isinstance(request.output_requirement, VideoFlexibleOutputRequirement)
        ):
            raise _error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Seedance request does not match the sealed provider profile.",
            )
        matches = tuple(
            entry
            for entry in self._profile.capabilities
            if entry.variant.model_id == request.model_id
            and entry.variant.mode is request.mode
            and entry.variant.output_capability is not None
            and entry.variant.output_capability.supports(request.output_requirement)
        )
        if len(matches) != 1:
            raise _error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Seedance request does not match exactly one capability variant.",
            )
        selected_profile = matches[0]
        output = request.output_requirement
        if output.dimension_mode == "exact" and not any(
            raster.resolution_label == output.resolution_label
            and raster.ratio == output.ratio
            and raster.width == output.width
            and raster.height == output.height
            for raster in selected_profile.output_rasters
        ):
            raise _error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Seedance exact output pixels do not match the official model mapping.",
            )
        if any(binding.size_bytes is None for binding in request.image_bindings):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "Seedance image references require measured byte sizes.",
            )
        if request.seed is not None and request.seed > 2_147_483_647:
            raise _error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Seedance seed is outside the supported legacy range.",
            )
        if any(
            binding.width > 6000
            or binding.height > 6000
            or not 0.4 <= binding.width / binding.height <= 2.5
            for binding in request.image_bindings
        ):
            raise _error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Seedance image geometry is outside the supported range.",
            )
        videos = tuple(
            binding for binding in request.media_bindings if binding.kind == "video"
        )
        if any(
            binding.width is None
            or binding.height is None
            or binding.fps is None
            or not 300 <= binding.width <= 6000
            or not 300 <= binding.height <= 6000
            or not 0.4 <= binding.width / binding.height <= 2.5
            or not 407_696 <= binding.width * binding.height <= 8_295_044
            or not 24 <= binding.fps <= 60
            for binding in videos
        ):
            raise _error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Seedance reference-video measurements are outside the supported range.",
            )
        family_total_limit = (
            30_000
            if request.model_id == "doubao-seedance-2-5-260628"
            else 15_000
            if request.model_id.startswith("doubao-seedance-2-0")
            else None
        )
        if family_total_limit is not None and any(
            sum(
                binding.duration_millis
                for binding in request.media_bindings
                if binding.kind == kind
            )
            > family_total_limit
            for kind in ("video", "audio")
        ):
            raise _error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Seedance reference media exceeds the family total-duration limit.",
            )
        if (
            request.model_id.startswith("doubao-seedance-2-0")
            and any(binding.kind == "audio" for binding in request.media_bindings)
            and not request.image_bindings
            and not any(binding.kind == "video" for binding in request.media_bindings)
        ):
            raise _error(
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
                "Seedance 2.0 audio references require an image or video reference.",
            )
        return ResolvedVideoGenerationRequest.create(
            request=request,
            capability=selected_profile.variant,
            effective_output=request.output_requirement,
            effective_seed=request.seed,
            effective_negative_prompt_text=request.negative_prompt_text,
            provider_task_binding=VideoProviderTaskBinding(
                request_target_id=selected_profile.api_model_id,
                response_model_id=selected_profile.variant.model_id,
            ),
        )

    def preview(self, request: ResolvedVideoGenerationRequest) -> VideoGenerationPreview:
        if request.capability_id not in self._profiles_by_capability:
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Seedance capability is not in profile.")
        now = self._now()
        if now < self._profile.pricing.observed_at or now >= self._profile.pricing.expires_at:
            raise _error(
                ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
                "Seedance pricing snapshot is not current.",
            )
        upper_bound = self._profile.pricing.upper_bound_for(request.model_id)
        if upper_bound is None:
            raise _error(
                ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
                "Seedance pricing does not cover the requested model.",
            )
        return VideoGenerationPreview.create(
            resolved=request,
            estimated_cost_upper_bound_microunits=upper_bound,
            currency="CNY",
            destination=self._profile.origin,
            egress_item_ids=(
                "prompt",
                *(binding.asset_id for binding in request.image_bindings),
                *(binding.asset_id for binding in request.media_bindings),
            ),
        )

    def _credential_headers(self, *, json_body: bool) -> dict[str, str]:
        try:
            secret = self._credential()
        except Exception:
            raise _error(
                ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED,
                "Seedance credential is unavailable.",
            ) from None
        if not isinstance(secret, str) or not secret or not secret.isascii():
            raise _error(
                ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED,
                "Seedance credential is unavailable.",
            )
        headers = {"accept": "application/json", "authorization": f"Bearer {secret}"}
        if json_body:
            headers["content-type"] = "application/json"
        return headers

    def _egress_matches(
        self,
        request: ResolvedVideoGenerationRequest,
        preview: PaidProviderCallPreview,
    ) -> bool:
        expected = [
            (
                "prompt",
                hashlib.sha256(request.prompt_text.encode()).hexdigest(),
                len(request.prompt_text.encode()),
                "text/plain",
                "prompt",
            )
        ]
        expected.extend(
            (
                binding.asset_id,
                binding.asset_sha256,
                binding.size_bytes,
                binding.mime_type,
                "reference",
            )
            for binding in (*request.image_bindings, *request.media_bindings)
        )
        actual = [
            (item.item_id, item.sha256, item.size_bytes, item.mime_type, item.purpose)
            for item in preview.egress_items
        ]
        return bool(
            actual == expected
            and preview.secret_reference.kind == "secret_store"
            and preview.secret_reference.reference_id == ARK_API_KEY_REFERENCE
        )

    def _asset_reference(
        self, binding: VideoImageReferenceBinding | VideoMediaReferenceBinding
    ) -> str:
        try:
            value = self._input_reference(binding)
        except Exception:
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "Seedance input reference is unavailable.",
            ) from None
        if not isinstance(value, str) or _SAFE_ASSET_REFERENCE.fullmatch(value) is None:
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "Seedance input reference must be an explicit provider asset reference.",
            )
        return value

    def _payload(self, request: ResolvedVideoGenerationRequest) -> dict[str, object]:
        profile = self._profiles_by_capability[request.capability_id]
        output = request.effective_output
        if not isinstance(output, VideoFlexibleOutputRequirement):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Seedance output contract is invalid.")
        content: list[dict[str, object]] = [{"type": "text", "text": request.prompt_text}]
        for binding in request.image_bindings:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": self._asset_reference(binding)},
                    "role": "reference_image" if binding.role == "reference" else binding.role,
                }
            )
        for binding in request.media_bindings:
            content.append(
                {
                    "type": f"{binding.kind}_url",
                    f"{binding.kind}_url": {"url": self._asset_reference(binding)},
                    "role": binding.role,
                }
            )
        payload: dict[str, object] = {
            "model": profile.api_model_id,
            "content": content,
            "resolution": output.resolution_label,
            "ratio": output.ratio,
            "generate_audio": output.native_audio,
        }
        if profile.watermark:
            payload["watermark"] = True
        if profile.return_last_frame:
            payload["return_last_frame"] = True
        if profile.service_tier != "default":
            payload["service_tier"] = profile.service_tier
        if output.container != "mp4":
            payload["output_format"] = output.container
        if output.timing_mode == "exact_seconds":
            payload["duration"] = output.duration_seconds
        elif output.timing_mode == "provider_selected":
            payload["duration"] = -1
        else:
            payload["frames"] = output.frame_count
        if request.effective_seed is not None:
            payload["seed"] = request.effective_seed
        if profile.camera_fixed:
            payload["camera_fixed"] = True
        if profile.draft:
            payload["draft"] = True
        if profile.priority not in {None, 0}:
            payload["priority"] = profile.priority
        if profile.omni_reference_task_type is not None:
            payload["omni_reference_task_type"] = profile.omni_reference_task_type
        return payload

    def submit(
        self,
        request: ResolvedVideoGenerationRequest,
        video_preview: VideoGenerationPreview,
        paid_preview: PaidProviderCallPreview | None,
        authorization: PaidProviderAuthorizationDecision | None,
        permit: object | None,
    ) -> VideoSubmitResult:
        if video_preview != self.preview(request):
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Seedance preview mismatch.")
        if paid_preview is None or authorization is None or permit is None:
            raise _error(
                ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                "Seedance submit requires Paid Provider authorization.",
            )
        validate_paid_provider_authorization(paid_preview, authorization, now=self._now())
        binding = build_video_paid_permit_binding(
            request, video_preview, paid_preview, authorization
        )
        if not self._egress_matches(request, paid_preview):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "Seedance paid preview does not bind the exact egress and credential.",
            )
        if not _permit_is_valid(permit, binding):
            raise _error(
                ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                "Seedance submit permit is invalid.",
            )
        body = json.dumps(
            self._payload(request), ensure_ascii=False, separators=(",", ":")
        ).encode()
        transport_request = SeedanceTransportRequest(
            method="POST",
            url=_SUBMIT_URL,
            headers=self._credential_headers(json_body=True),
            body=body,
        )
        if not _consume_permit(permit, binding):
            raise _error(
                ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
                "Seedance submit permit is already consumed.",
            )
        try:
            response = self._transport.request(transport_request)
        except Exception:
            raise _unknown_submit() from None
        if not 200 <= response.status_code < 300:
            if 400 <= response.status_code < 500 and response.status_code != 429:
                raise _error(
                    ErrorCode.VIDEO_PROVIDER_FAILED,
                    f"Seedance submit was rejected with HTTP {response.status_code}.",
                )
            raise _unknown_submit()
        try:
            task_id = _task_id(
                _json_object(response.body, surface="submit response").get("id"),
                surface="submit response",
            )
        except AiVideoError:
            raise _unknown_submit() from None
        return VideoSubmitResult.create(
            resolved=request, external_effect_id=task_id, submitted_at=self._now()
        )

    def _query(
        self, task_id: str, *, expected_model_id: str
    ) -> tuple[VideoTaskState, str | None]:
        request = SeedanceTransportRequest(
            method="GET",
            url=_QUERY_URL.format(task_id=quote(task_id, safe="")),
            headers=self._credential_headers(json_body=False),
        )
        try:
            response = self._transport.request(request)
        except Exception:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "Seedance task query transport failed.",
                retryable=True,
            ) from None
        if not 200 <= response.status_code < 300:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                f"Seedance task query returned HTTP {response.status_code}.",
                retryable=response.status_code == 429 or response.status_code >= 500,
            )
        payload = _json_object(response.body, surface="query response")
        if _task_id(payload.get("id"), surface="query response") != task_id:
            raise _error(ErrorCode.VIDEO_REQUEST_INVALID, "Seedance query task ID changed.")
        model = payload.get("model")
        if model != expected_model_id:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Seedance query model changed.")
        status = payload.get("status")
        if status == "queued":
            return VideoTaskState.QUEUED, None
        if status == "running":
            return VideoTaskState.RUNNING, None
        if status in {"failed", "cancelled", "expired"}:
            return VideoTaskState.FAILED, None
        if status != "succeeded":
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Seedance query status is invalid.")
        content = payload.get("content")
        if not isinstance(content, dict) or not isinstance(content.get("video_url"), str):
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Seedance result URL is missing.")
        return VideoTaskState.SUCCEEDED, content["video_url"]

    def get_status(
        self,
        submission: VideoSubmission,
        submit_receipt: PaidProviderSubmitReceipt,
    ) -> VideoTaskObservation:
        task_id = _validate_submission(submission, submit_receipt)
        if submission.provider_task_binding is None:
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "Seedance submission is missing its exact provider task binding.",
            )
        state, result_url = self._query(
            task_id,
            expected_model_id=submission.provider_task_binding.response_model_id,
        )
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
                if state is VideoTaskState.SUCCEEDED and result_url is not None
                else None
            ),
        )

    def _result_url(self, value: str) -> str:
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "Seedance result URL is invalid.",
            ) from None
        if (
            parsed.scheme != "https"
            or parsed.hostname is None
            or parsed.username is not None
            or parsed.password is not None
            or not parsed.path
            or parsed.fragment
        ):
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Seedance result URL is invalid.")
        host = parsed.hostname.lower()
        origin = f"https://{host}"
        if port is not None and port != 443:
            origin = f"{origin}:{port}"
        if origin not in self._profile.result_origins:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Seedance result origin is not allowed.")
        return value

    def fetch(
        self,
        submission: VideoSubmission,
        submit_receipt: PaidProviderSubmitReceipt,
        observation: VideoTaskObservation,
        sink: BinaryIO,
    ) -> VideoFetchReceipt:
        task_id = _validate_submission(submission, submit_receipt)
        if submission.provider_task_binding is None:
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "Seedance submission is missing its exact provider task binding.",
            )
        if (
            observation.submission_fingerprint != submission.submission_fingerprint
            or observation.paid_submit_receipt_fingerprint
            != submission.paid_submit_receipt_fingerprint
            or observation.state is not VideoTaskState.SUCCEEDED
            or observation.provider_file_id != _provider_file_id(task_id)
        ):
            raise _error(
                ErrorCode.VIDEO_REQUEST_INVALID,
                "Seedance fetch evidence does not match the same succeeded task.",
            )
        state, result_url = self._query(
            task_id,
            expected_model_id=submission.provider_task_binding.response_model_id,
        )
        if state is not VideoTaskState.SUCCEEDED or result_url is None:
            raise _error(ErrorCode.VIDEO_PROVIDER_FAILED, "Seedance task is not fetchable.")
        request = SeedanceTransportRequest(
            method="GET",
            url=self._result_url(result_url),
            headers={"accept": "video/mp4, video/quicktime"},
        )
        digest = hashlib.sha256()
        size = 0
        prefix = bytearray()
        try:
            with self._transport.stream(request) as response:
                if not 200 <= response.status_code < 300:
                    raise _error(
                        ErrorCode.VIDEO_PROVIDER_FAILED,
                        f"Seedance download returned HTTP {response.status_code}.",
                    )
                raw_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                if raw_type not in {"video/mp4", "video/quicktime"}:
                    raise _error(
                        ErrorCode.VIDEO_ARTIFACT_INVALID,
                        "Seedance download content type is not an accepted video container.",
                    )
                if (
                    submission.expected_content_type is not None
                    and raw_type != submission.expected_content_type
                ):
                    raise _error(
                        ErrorCode.VIDEO_ARTIFACT_INVALID,
                        "Seedance download container does not match the durable submit intent.",
                    )
                for chunk in response.iter_bytes():
                    if not isinstance(chunk, bytes) or not chunk:
                        continue
                    size += len(chunk)
                    if size > self._profile.max_download_bytes:
                        raise _error(
                            ErrorCode.VIDEO_ARTIFACT_INVALID,
                            "Seedance download exceeds the configured byte ceiling.",
                        )
                    if len(prefix) < 64:
                        prefix.extend(chunk[: 64 - len(prefix)])
                    digest.update(chunk)
                    sink.write(chunk)
        except AiVideoError:
            raise
        except Exception:
            raise _error(
                ErrorCode.VIDEO_PROVIDER_FAILED,
                "Seedance download transport failed.",
                retryable=True,
            ) from None
        if not _matches_iso_bmff_container(
            content_type=raw_type,
            prefix=bytes(prefix),
            size_bytes=size,
        ):
            raise _error(
                ErrorCode.VIDEO_ARTIFACT_INVALID,
                "Seedance download is not a measured MP4/MOV artifact.",
            )
        return VideoFetchReceipt.create(
            submission=submission,
            observation=observation,
            content_type=raw_type,  # type: ignore[arg-type]
            size_bytes=size,
            artifact_sha256=digest.hexdigest(),
            fetched_at=self._now(),
        )


__all__ = [
    "ARK_API_KEY_REFERENCE",
    "HttpxSeedanceTransport",
    "SEEDANCE_MODEL_IDS",
    "SeedanceCapabilityProfile",
    "SeedanceOutputRaster",
    "SeedancePricingSnapshot",
    "SeedanceProviderProfile",
    "SeedanceTransportRequest",
    "SeedanceTransportResponse",
    "SeedanceVideoProvider",
]
