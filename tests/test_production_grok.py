"""Offline Grok video Provider lifecycle and transport tests."""

from __future__ import annotations

import base64
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from io import BytesIO
import hashlib
import json
from pathlib import Path

import httpx
import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.grok import (
    GrokVideoProvider,
    GrokTransportRequest,
    GrokTransportResponse,
    HttpxGrokTransport,
)
from ai_video.production._state_commit_contracts import (
    _DurablePaidProviderSubmitPermit,
    _PAID_PROVIDER_PERMIT_TOKEN,
)
from ai_video.production.grok_profile import (
    GROK_VIDEO_MODEL,
    GROK_VIDEO_MODEL_CLASSIC,
    GROK_VIDEO_MODEL_LITE,
    GrokProviderProfile,
)
from ai_video.production.grok_video_request import grok_endpoint_for_mode, grok_egress_inputs
from ai_video.production.grok_subscription import GrokSubscriptionBinding
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderEgressItem,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
    SecretReference,
)
from ai_video.production.models import (
    ActorIdentity,
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)
from ai_video.production.video import (
    VideoFlexibleOutputRequirement,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoOutputRecoveryStrategy,
    VideoProviderRegistry,
    VideoSubmission,
    VideoTaskState,
    build_video_paid_permit_binding,
)


NOW = datetime(2026, 10, 12, 12, tzinfo=UTC)
ACCOUNT = "a" * 64
IMAGE = b"grok first frame"
IMAGE_SHA256 = hashlib.sha256(IMAGE).hexdigest()
MP4 = b"\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isomiso2"
VIDEO_URL = "https://vidgen.x.ai/output/video.mp4?token=short-lived"


class FakeTransport:
    def __init__(self) -> None:
        self.calls = []
        self.downloads = []
        self.submit_status = 200
        self.submit_payload = {"request_id": "request-1"}
        self.query_status = 200
        self.query_payload = {
            "status": "done",
            "model": GROK_VIDEO_MODEL,
            "request_id": "request-1",
            "video": {"url": VIDEO_URL, "respect_moderation": True},
        }
        self.download_status = 200
        self.download_headers = {"content-type": "video/mp4", "content-length": str(len(MP4))}
        self.download_body = MP4
        self.error: Exception | None = None

    def request(self, request):
        self.calls.append(request)
        if self.error is not None:
            raise self.error
        if request.method == "POST":
            return GrokTransportResponse(
                self.submit_status, {"content-type": "application/json"},
                json.dumps(self.submit_payload).encode(),
            )
        return GrokTransportResponse(
            self.query_status, {"content-type": "application/json"},
            json.dumps(self.query_payload).encode(),
        )

    @contextmanager
    def stream(self, request):
        self.downloads.append(request)
        yield self

    @property
    def status_code(self):
        return self.download_status

    @property
    def headers(self):
        return self.download_headers

    def iter_bytes(self):
        for offset in range(0, len(self.download_body), 3):
            yield self.download_body[offset:offset + 3]


def _profile(**changes):
    values = {"account_fingerprint": ACCOUNT}
    values.update(changes)
    return GrokProviderProfile(**values)


def _binding(profile=None, **changes):
    profile = profile or _profile()
    values = dict(
        account_fingerprint=profile.account_fingerprint,
        credential_reference_id="GROK_OAUTH",
        destination=profile.origin,
        model_id=GROK_VIDEO_MODEL,
        quota_observed_at=NOW,
        quota_expires_at=NOW + timedelta(minutes=5),
        period_end=NOW + timedelta(days=1),
        used_percent=20,
        included_only_evidence_id="test-boundary-1",
    )
    values.update(changes)
    return GrokSubscriptionBinding(**values)


def _request(profile=None, *, images=False, **changes):
    profile = profile or _profile()
    model_id = changes.pop("model_id", GROK_VIDEO_MODEL)
    image_bindings = ()
    input_artifact_ids = ("shot",)
    if images:
        image_bindings = (VideoImageReferenceBinding(
            role="first_frame", asset_id="first-frame", asset_sha256=IMAGE_SHA256,
            mime_type="image/png", size_bytes=len(IMAGE), width=1280, height=720,
        ),)
        input_artifact_ids = ("shot", "first-frame")
    values = dict(
        generation_id="grok-generation",
        provider_name="grok",
        provider_kind="grok",
        model_id=model_id,
        provider_profile=profile.pointer(),
        target_shot_id="shot",
        target_shot_revision=1,
        target_shot_content_hash="b" * 64,
        target_asset_role="primary_visual",
        target_visual_strategy="generated_video",
        mode=changes.pop(
            "mode",
            VideoGenerationMode.IMAGE_TO_VIDEO if images else VideoGenerationMode.TEXT_TO_VIDEO,
        ),
        prompt_text="A paper boat drifts down a quiet stream.",
        negative_prompt_text="",
        image_bindings=image_bindings,
        output_requirement=VideoFlexibleOutputRequirement(
            timing_mode="nominal_seconds", duration_seconds=5,
            dimension_mode="adaptive", width=None, height=None,
            resolution_label="720p", ratio="adaptive", fps=None,
            container="mp4", mime_type="video/mp4", native_audio=False,
        ),
        seed=None,
        base_project=ProjectSnapshotPointer(
            path=Path("project.yaml"), revision=1, content_hash="c" * 64,
            file_sha256="c" * 64,
        ),
        base_registry=RegistrySnapshotPointer(
            path=Path("assets/registry." + "d" * 64 + ".json"),
            revision_id="d" * 64, content_hash="d" * 64, file_sha256="d" * 64,
        ),
        base_dependency_graph=DependencyGraphSnapshotPointer(
            path=Path("state/dependency_graph." + "e" * 64 + ".json"),
            revision_id="e" * 64, content_hash="e" * 64, file_sha256="e" * 64,
        ),
        input_artifact_ids=input_artifact_ids,
        output_asset_id="grok-video-output",
    )
    values.update(changes)
    return VideoGenerationRequest.create(**values)


def _setup(*, request=None, profile=None, binding=None, guard=True, now=None,
           credential=None, transport=None, image_resolver=None, media_resolver=None):
    profile = profile or _profile()
    request = request or _request(profile)
    operation_path = f"/v1/videos/{grok_endpoint_for_mode(request.mode)}"
    legacy_generation_binding = (
        request.model_id == GROK_VIDEO_MODEL
        and operation_path == "/v1/videos/generations"
    )
    subscription = binding or _binding(
        profile,
        model_id=request.model_id,
        **({} if legacy_generation_binding else {"operation_path": operation_path}),
    )
    transport = transport or FakeTransport()
    clock = [NOW]
    guard_calls = []

    def check_subscription(exact):
        guard_calls.append(exact)
        if guard is True:
            from ai_video.production.grok_subscription import require_current_subscription

            require_current_subscription(
                exact, account_fingerprint=profile.account_fingerprint,
                model_id=request.model_id, destination=profile.origin,
                operation_path=operation_path,
                now=now() if now is not None else clock[0],
            )
        elif callable(guard):
            guard(exact)

    provider = GrokVideoProvider(
        profile=profile, transport=transport,
        credential=credential or (lambda: "private-grok-access-token"),
        subscription_guard=check_subscription if guard is not None else None,
        image_resolver=image_resolver or (lambda _binding: IMAGE),
        media_resolver=media_resolver,
        now=now or (lambda: clock[0]),
    )
    resolved = provider.resolve(request)
    preview = provider.preview(resolved)
    prompt = resolved.prompt_text.encode("utf-8")
    egress = [PaidProviderEgressItem(
        item_id="prompt", sha256=hashlib.sha256(prompt).hexdigest(),
        size_bytes=len(prompt), mime_type="text/plain", purpose="prompt",
    )]
    egress.extend(PaidProviderEgressItem(
        item_id=b.asset_id, sha256=b.asset_sha256, size_bytes=b.size_bytes,
        mime_type=b.mime_type, purpose="reference",
    ) for b in grok_egress_inputs(resolved))
    paid = PaidProviderCallPreview.create(
        attempt_id="grok-attempt-1", operation="video_generation",
        provider_kind="grok", model_id=resolved.model_id,
        request_fingerprint=resolved.resolved_generation_hash,
        billing_mode="remote_subscription", subscription_binding=subscription,
        currency="USD", estimated_cost_upper_bound_microunits=0,
        destination=profile.origin, method="POST", egress_items=tuple(egress),
        retention_mode="provider_standard", provider_policy_snapshot_id="grok-policy",
        secret_reference=SecretReference(kind="secret_store", reference_id="GROK_OAUTH"),
    )
    authorization = PaidProviderAuthorizationDecision.create(
        attempt_id=paid.attempt_id, preview_fingerprint=paid.preview_fingerprint,
        explicit_opt_in=True, actor=ActorIdentity(actor_id="test-user", actor_kind="human"),
        opt_in_policy_receipt_id="grok-opt-in", budget_policy_id="grok-zero-cash",
        budget_currency="USD", project_budget_ceiling_microunits=0,
        per_call_ceiling_microunits=0, subscription_submit_limit=1,
        egress_authorized=True, egress_policy_receipt_id="grok-egress",
        live_test_authorized=True, live_authorization_receipt_id="grok-live-test",
        issued_at=NOW - timedelta(seconds=1), expires_at=NOW + timedelta(minutes=30),
        max_submit_count=1,
    )
    permit_binding = build_video_paid_permit_binding(resolved, preview, paid, authorization)
    permit = _DurablePaidProviderSubmitPermit(
        _PAID_PROVIDER_PERMIT_TOKEN, binding=permit_binding,
        durability_validator=lambda: True,
    )
    return provider, transport, (resolved, preview, paid, authorization, permit), subscription, guard_calls, clock


def _submission(provider, transport, args):
    result = provider.submit(*args)
    resolved, _, paid, _, _ = args
    receipt = PaidProviderSubmitReceipt.create(
        attempt_id=paid.attempt_id,
        request_fingerprint=resolved.resolved_generation_hash,
        preview_fingerprint=paid.preview_fingerprint,
        gate_receipt_fingerprint="f" * 64,
        reservation_id="grok-reservation-1",
        outcome=PaidProviderSubmitOutcome.ACCEPTED,
        external_effect_id=result.external_effect_id,
        recorded_at=NOW,
    )
    return VideoSubmission.from_paid_submit_receipt(resolved=resolved, receipt=receipt), receipt


def test_registry_and_capabilities_expose_only_documented_video_modes():
    profile = _profile()
    provider = GrokVideoProvider(
        profile=profile, transport=FakeTransport(), credential=lambda: "unused",
        subscription_guard=lambda _binding: None, now=lambda: NOW,
    )
    assert VideoProviderRegistry((("grok", provider),)).resolve("grok") is provider
    variants = provider.capabilities().variants
    assert {item.mode for item in variants} == {
        VideoGenerationMode.TEXT_TO_VIDEO,
        VideoGenerationMode.IMAGE_TO_VIDEO,
        VideoGenerationMode.REFERENCE_TO_VIDEO,
        VideoGenerationMode.VIDEO_EDIT,
        VideoGenerationMode.VIDEO_EXTEND,
    }
    assert {item.model_id for item in variants} == {
        GROK_VIDEO_MODEL, GROK_VIDEO_MODEL_CLASSIC, GROK_VIDEO_MODEL_LITE,
    }
    assert all(item.output_capability.fps_values == (None,) for item in variants)
    assert all(
        item.output_recovery_strategy is VideoOutputRecoveryStrategy.REQUERY_BY_EFFECT_ID
        for item in variants
    )


@pytest.mark.parametrize("changes", [
    {"seed": 3},
    {"negative_prompt_text": "do not show rain"},
    {"output_requirement": VideoFlexibleOutputRequirement(
        timing_mode="nominal_seconds", duration_seconds=5,
        dimension_mode="adaptive", width=None, height=None,
        resolution_label="720p", ratio="adaptive", fps=24,
        container="mp4", mime_type="video/mp4", native_audio=False,
    )},
])
def test_resolve_rejects_controls_without_documented_grok_video_support(changes):
    provider, _, _, _, _, _ = _setup()
    with pytest.raises(AiVideoError):
        provider.resolve(_request(**changes))


def test_submit_posts_exact_subscription_request_and_hides_credential():
    provider, transport, args, binding, guard_calls, _ = _setup()
    result = provider.submit(*args)
    request = transport.calls[0]
    payload = json.loads(request.body)
    assert request.method == "POST"
    assert request.url == "https://cli-chat-proxy.grok.com/v1/videos/generations"
    assert payload == {
        "model": GROK_VIDEO_MODEL,
        "prompt": "A paper boat drifts down a quiet stream.",
        "duration": 5,
        "resolution": "720p",
        "generate_audio": False,
    }
    assert "authorization" in request.headers
    assert len(guard_calls) == 3 and all(item == binding for item in guard_calls)
    assert result.external_effect_id == "request-1"
    assert "private-grok-access-token" not in repr(request)


def test_i2v_posts_exact_bound_first_image_as_data_uri():
    request = _request(images=True)
    provider, transport, args, _, _, _ = _setup(
        request=request, image_resolver=lambda binding: IMAGE,
    )
    provider.submit(*args)
    payload = json.loads(transport.calls[0].body)
    assert payload["image"] == {
        "url": "data:image/png;base64," + base64.b64encode(IMAGE).decode("ascii"),
    }
    assert "first_image" not in payload
    assert "type" not in payload["image"]


def test_default_unverified_subscription_authority_blocks_before_secret_or_post():
    profile = _profile()
    secret_reads = []
    provider, transport, args, _, _, _ = _setup(
        profile=profile, guard=None,
        credential=lambda: secret_reads.append(True) or "token",
    )
    with pytest.raises(AiVideoError):
        provider.submit(*args)
    assert not secret_reads
    assert not transport.calls
    resolved, preview, paid, auth, permit = args
    binding = build_video_paid_permit_binding(resolved, preview, paid, auth)
    assert permit._validate_paid_provider_operation_permit(**binding)


@pytest.mark.parametrize("permit", [None, object()])
def test_submit_requires_durable_permit_before_secret_or_post(permit):
    secret_reads = []
    provider, transport, args, _, _, _ = _setup(
        credential=lambda: secret_reads.append(True) or "token",
    )
    request, video_preview, paid_preview, authorization, _ = args
    with pytest.raises(AiVideoError) as error:
        provider.submit(request, video_preview, paid_preview, authorization, permit)
    assert error.value.code is ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED
    assert not secret_reads
    assert not transport.calls


@pytest.mark.parametrize("binding_changes", [
    {"account_fingerprint": "b" * 64},
    {"quota_observed_at": NOW - timedelta(minutes=4),
     "quota_expires_at": NOW - timedelta(minutes=1)},
])
def test_stale_or_wrong_account_binding_blocks_before_post(binding_changes):
    profile = _profile()
    provider, transport, args, _, _, _ = _setup(
        profile=profile, binding=_binding(profile, **binding_changes),
    )
    with pytest.raises(AiVideoError):
        provider.submit(*args)
    assert not transport.calls


def test_subscription_authority_is_rechecked_after_durable_permit_consumption():
    profile = _profile()
    current = [NOW]
    binding = _binding(profile)
    guard_calls = []

    def guard(exact):
        guard_calls.append(exact)
        from ai_video.production.grok_subscription import require_current_subscription

        require_current_subscription(exact, account_fingerprint=profile.account_fingerprint,
            model_id=GROK_VIDEO_MODEL, destination=profile.origin, now=current[0])
        if len(guard_calls) == 2:
            current[0] = binding.quota_expires_at

    provider, transport, args, _, _, _ = _setup(
        profile=profile, binding=binding, guard=guard, now=lambda: current[0]
    )
    with pytest.raises(AiVideoError):
        provider.submit(*args)
    assert len(guard_calls) == 2
    assert not transport.calls
    resolved, preview, paid, authorization, permit = args
    permit_binding = build_video_paid_permit_binding(
        resolved, preview, paid, authorization
    )
    assert not permit._validate_paid_provider_operation_permit(**permit_binding)


def test_video_generation_service_uses_one_durable_subscription_permit(tmp_path):
    import production_remote_generation_factory as remote_factory
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_generation import VideoGenerationService

    provider, _, _, _, _, _ = _setup()
    prepared = remote_factory.prepare_remote_generation(
        root=tmp_path,
        provider=provider,
        request=_request(),
        compiler_id="grok-video-compiler",
        compiler_version="1",
        requirement_timing_mode="content_driven",
    )
    provider, transport, args, _, _, _ = _setup(request=prepared.compilation.request)
    resolved, _, paid, authorization, _ = args
    committer = ProductionStateCommitter(
        tmp_path,
        paid_provider_authorizer=lambda exact: authorization if exact == paid else None,
        paid_provider_clock=lambda: NOW,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(
        attempt_id=paid.attempt_id,
        request=resolved,
        execution_binding=prepared.execution_binding,
    )
    submission = service.submit_once(
        attempt_id=paid.attempt_id,
        paid_preview=paid,
        reservation_id="grok-service-reservation",
    )
    assert submission.provider_task_binding.response_model_id == GROK_VIDEO_MODEL
    assert [call.method for call in transport.calls] == ["POST"]

    restarted = VideoGenerationService(
        committer=ProductionStateCommitter(tmp_path, paid_provider_clock=lambda: NOW),
        provider=provider,
    )
    with pytest.raises(AiVideoError):
        restarted.submit_once(
            attempt_id=paid.attempt_id,
            paid_preview=paid,
            reservation_id="grok-service-reservation",
        )
    assert [call.method for call in transport.calls] == ["POST"]


def test_lost_submit_response_is_unknown_and_never_retried():
    provider, transport, args, _, _, _ = _setup()
    transport.error = TimeoutError("connection dropped")
    with pytest.raises(AiVideoError) as error:
        provider.submit(*args)
    assert error.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert len(transport.calls) == 1
    transport.error = None
    with pytest.raises(AiVideoError):
        provider.submit(*args)
    assert len(transport.calls) == 1


@pytest.mark.parametrize("task_id", [".", ".."])
def test_submit_rejects_task_identity_that_would_change_the_query_path(task_id):
    provider, transport, args, _, _, _ = _setup()
    transport.submit_payload = {"request_id": task_id}
    with pytest.raises(AiVideoError) as error:
        provider.submit(*args)
    assert error.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    with pytest.raises(AiVideoError):
        provider.submit(*args)
    assert len(transport.calls) == 1


@pytest.mark.parametrize("mutation", [
    {"model": "other-model"},
    {"request_id": "different-request"},
    {"video": {"url": VIDEO_URL, "respect_moderation": False}},
])
def test_status_requires_exact_model_task_and_moderation(mutation):
    provider, transport, args, _, _, _ = _setup()
    submission, receipt = _submission(provider, transport, args)
    transport.query_payload.update(mutation)
    with pytest.raises(AiVideoError):
        provider.get_status(submission, receipt)


@pytest.mark.parametrize(
    ("provider_status", "expected_state"),
    [("pending", VideoTaskState.RUNNING), ("failed", VideoTaskState.FAILED)],
)
def test_status_maps_pending_and_failed_without_a_media_locator(provider_status, expected_state):
    provider, transport, args, _, _, _ = _setup()
    submission, receipt = _submission(provider, transport, args)
    transport.query_payload = {
        "request_id": "request-1", "model": GROK_VIDEO_MODEL,
        "status": provider_status,
    }
    observation = provider.get_status(submission, receipt)
    assert observation.state is expected_state
    assert observation.provider_file_id is None


def test_fetch_requeries_exact_task_and_seals_locator_to_mp4_bytes():
    provider, transport, args, _, _, _ = _setup()
    submission, receipt = _submission(provider, transport, args)
    observation = provider.get_status(submission, receipt)
    assert observation.state is VideoTaskState.SUCCEEDED
    sink = BytesIO()
    fetched = provider.fetch(submission, receipt, observation, sink)
    assert sink.getvalue() == MP4
    assert fetched.artifact_sha256 == hashlib.sha256(MP4).hexdigest()
    assert fetched.remote_materialization is not None
    assert fetched.remote_materialization.remote_origin == "https://vidgen.x.ai"
    assert fetched.remote_materialization.remote_locator_sha256 == hashlib.sha256(
        VIDEO_URL.encode()
    ).hexdigest()
    assert len([call for call in transport.calls if call.method == "GET"]) == 2
    assert transport.downloads[0].headers == {"accept": "*/*"}


def test_fetch_accepts_mp4_ftyp_with_a_different_major_brand():
    provider, transport, args, _, _, _ = _setup()
    submission, receipt = _submission(provider, transport, args)
    observation = provider.get_status(submission, receipt)
    transport.download_body = MP4[:8] + b"iso6" + MP4[12:]
    transport.download_headers["content-length"] = str(len(transport.download_body))
    fetched = provider.fetch(submission, receipt, observation, BytesIO())
    assert fetched.size_bytes == len(transport.download_body)


def test_fetch_accepts_arbitrary_http_origin_small_legacy_limit_and_misleading_mime():
    profile = _profile(max_download_bytes=12)
    provider, transport, args, _, _, _ = _setup(profile=profile)
    transport.query_payload["video"]["url"] = "http://127.0.0.1:8080/output.mp4?token=short-lived"
    submission, receipt = _submission(provider, transport, args)
    observation = provider.get_status(submission, receipt)
    sink = BytesIO()
    transport.download_headers["content-type"] = "text/plain"
    fetched = provider.fetch(submission, receipt, observation, sink)
    assert sink.getvalue() == MP4
    assert fetched.remote_materialization.remote_origin == "http://127.0.0.1:8080"
    assert fetched.remote_materialization.transport_kind == "provider_output_http"
    assert transport.downloads[0].headers == {"accept": "*/*"}


def test_fetch_writes_complete_bad_media_before_rejecting_it():
    provider, transport, args, _, _, _ = _setup()
    submission, receipt = _submission(provider, transport, args)
    observation = provider.get_status(submission, receipt)
    transport.download_body = b"not an mp4"
    transport.download_headers["content-type"] = "application/octet-stream"
    transport.download_headers["content-length"] = str(len(transport.download_body))
    sink = BytesIO()
    with pytest.raises(AiVideoError):
        provider.fetch(submission, receipt, observation, sink)
    assert sink.getvalue() == transport.download_body


def test_http_transport_does_not_merge_injected_client_auth_or_cookies():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"request_id": "request-1"})

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        auth=("injected-user", "injected-password"),
        cookies={"session": "do-not-send"},
    )
    transport = HttpxGrokTransport(client=client)
    response = transport.request(GrokTransportRequest(
        "POST", "https://cli-chat-proxy.grok.com/v1/videos/generations",
        {"authorization": "Bearer oauth-token", "content-type": "application/json",
         "accept": "application/json"}, b"{}",
    ))
    assert response.status_code == 200
    assert seen[0].headers["authorization"] == "Bearer oauth-token"
    assert "cookie" not in seen[0].headers
    assert "injected-user" not in seen[0].headers.get("authorization", "")
    client.close()


def test_http_transport_bounds_json_response_body():
    client = httpx.Client(transport=httpx.MockTransport(
        lambda _request: httpx.Response(200, content=b"{" + b" " * 1_000_001 + b"}")
    ))
    transport = HttpxGrokTransport(client=client)
    with pytest.raises(AiVideoError):
        transport.request(GrokTransportRequest(
            "GET", "https://cli-chat-proxy.grok.com/v1/videos/request-1",
            {"authorization": "Bearer token", "accept": "application/json"},
        ))
    client.close()


@pytest.mark.parametrize("segment", [".", "..", "%2e%2e", "request%2Fother", "request%3a1"])
def test_http_transport_rejects_noncanonical_task_paths_before_network(segment):
    seen = []
    with httpx.Client(transport=httpx.MockTransport(
        lambda request: seen.append(request) or httpx.Response(200, json={})
    )) as client:
        transport = HttpxGrokTransport(client=client)
        with pytest.raises(AiVideoError) as error:
            transport.request(GrokTransportRequest("GET",
                f"https://cli-chat-proxy.grok.com/v1/videos/{segment}",
                {"authorization": "Bearer synthetic-token", "accept": "application/json"}))
        assert error.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert seen == []


def test_http_transport_preserves_canonical_encoded_task_identity():
    seen = []
    with httpx.Client(transport=httpx.MockTransport(
        lambda request: seen.append(request) or httpx.Response(200, json={})
    )) as client:
        transport = HttpxGrokTransport(client=client)
        transport.request(GrokTransportRequest("GET",
            "https://cli-chat-proxy.grok.com/v1/videos/request%3A1",
            {"authorization": "Bearer synthetic-token", "accept": "application/json"}))
    assert str(seen[0].url) == "https://cli-chat-proxy.grok.com/v1/videos/request%3A1"
