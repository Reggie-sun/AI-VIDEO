"""Deterministic no-network tests for the MiniMax Hailuo-2.3 V1 video adapter."""

from __future__ import annotations

import hashlib
import json
import socket
from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path

import httpx
import pytest

import ai_video.production as production_root
import ai_video.production.minimax_hailuo as hailuo_module
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.minimax_hailuo import (
    HttpxMiniMaxHailuoTransport,
    MiniMaxHailuoTransportRequest,
    MiniMaxHailuoTransportResponse,
    MiniMaxHailuoVideoProvider,
)
from ai_video.production._state_commit_contracts import (
    _PAID_PROVIDER_PERMIT_TOKEN,
    _DurablePaidProviderSubmitPermit,
)
from ai_video.production.models import (
    ActorIdentity,
    DependencyGraphSnapshotPointer,
    ProductionManifest,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderEgressItem,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
    SecretReference,
)
from ai_video.production.video import (
    BillingKind,
    ProviderProfilePointer,
    ResolvedVideoGenerationRequest,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoGenerationPreview,
    VideoGenerationRequest,
    VideoOutputRequirement,
    VideoProviderCapabilities,
    VideoSubmission,
    VideoTaskObservation,
    VideoTaskState,
    VideoImageReferenceBinding,
    build_video_paid_permit_binding,
)
from ai_video.production.video_generation import VideoGenerationService
from production_project_factory import (
    make_manifest_23_project,
    write_production_project,
)


HASH_A = "a" * 64
PROMPT_TEXT = "An astronaut rides a horse on the moon"
SECRET_TEXT = "TOP-SECRET-MINIMAX-TOKEN"
SIGNED_URL = "https://signed.cdn.minimax.io/asset/abc123.mp4?token=short-lived"
FILE_ID = "file-hailuo-1"
TASK_ID = "task-hailuo-1"
_FIXED_NOW = datetime(2026, 8, 18, 12, 1, tzinfo=UTC)


def _project_pointer() -> ProjectSnapshotPointer:
    return ProjectSnapshotPointer(
        path=Path("project.yaml"),
        revision=1,
        content_hash=HASH_A,
        file_sha256=HASH_A,
    )


def _registry_pointer() -> RegistrySnapshotPointer:
    return RegistrySnapshotPointer(
        path=Path(f"assets/registry.{HASH_A}.json"),
        revision_id=HASH_A,
        content_hash=HASH_A,
        file_sha256=HASH_A,
    )


def _graph_pointer() -> DependencyGraphSnapshotPointer:
    return DependencyGraphSnapshotPointer(
        path=Path(f"state/dependency_graph.{HASH_A}.json"),
        revision_id=HASH_A,
        content_hash=HASH_A,
        file_sha256=HASH_A,
    )


def _profile() -> ProviderProfilePointer:
    return ProviderProfilePointer(
        profile_id="minimax-hailuo-default",
        profile_version="hailuo-2.3-v1",
        profile_path=Path(f"provider-profiles/{HASH_A}.json"),
        profile_sha256=HASH_A,
    )


def _output() -> VideoOutputRequirement:
    return VideoOutputRequirement(
        duration_seconds=6,
        width=1366,
        height=768,
        fps=None,
        container="mp4",
        mime_type="video/mp4",
        native_audio=False,
    )


def _request(**changes: object) -> VideoGenerationRequest:
    values: dict[str, object] = {
        "generation_id": "generation-hailuo-1",
        "provider_name": "minimax_hailuo",
        "provider_kind": "minimax_hailuo",
        "model_id": "MiniMax-Hailuo-2.3",
        "provider_profile": _profile(),
        "target_shot_id": "shot-hailuo-1",
        "target_shot_revision": 1,
        "target_shot_content_hash": HASH_A,
        "target_asset_role": "primary_visual",
        "target_visual_strategy": "generated_video",
        "mode": VideoGenerationMode.TEXT_TO_VIDEO,
        "prompt_text": PROMPT_TEXT,
        "negative_prompt_text": "",
        "image_bindings": (),
        "output_requirement": _output(),
        "seed": None,
        "base_project": _project_pointer(),
        "base_registry": _registry_pointer(),
        "base_dependency_graph": _graph_pointer(),
        "input_artifact_ids": ("shot-hailuo-1",),
        "output_asset_id": "output-asset-hailuo-1",
    }
    values.update(changes)
    return VideoGenerationRequest.create(**values)


def _fixed_now() -> datetime:
    return _FIXED_NOW


class _SecretResolver:
    def __init__(self, value: str = SECRET_TEXT) -> None:
        self._value = value
        self.invocations = 0

    def __call__(self) -> str:
        self.invocations += 1
        return self._value


class _StreamResponse:
    def __init__(self, response: MiniMaxHailuoTransportResponse) -> None:
        self.status_code = response.status_code
        self.headers = response.headers
        self._body = response.body

    def __enter__(self) -> _StreamResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def iter_bytes(self):
        midpoint = len(self._body) // 2
        yield self._body[:midpoint]
        yield self._body[midpoint:]


class _FakeTransport:
    def __init__(
        self,
        *,
        submit_response: MiniMaxHailuoTransportResponse | None = None,
        query_response: MiniMaxHailuoTransportResponse | None = None,
        file_retrieve_response: MiniMaxHailuoTransportResponse | None = None,
        download_response: MiniMaxHailuoTransportResponse | None = None,
        submit_error: Exception | None = None,
        stream_error: Exception | None = None,
    ) -> None:
        self.submit_response = submit_response
        self.query_response = query_response
        self.file_retrieve_response = file_retrieve_response
        self.download_response = download_response
        self.submit_error = submit_error
        self.stream_error = stream_error
        self.calls: list[MiniMaxHailuoTransportRequest] = []
        self.stream_calls: list[MiniMaxHailuoTransportRequest] = []

    def request(
        self, request: MiniMaxHailuoTransportRequest
    ) -> MiniMaxHailuoTransportResponse:
        self.calls.append(request)
        if request.method == "POST":
            if self.submit_error is not None:
                raise self.submit_error
            assert self.submit_response is not None, "submit response was not configured"
            return self.submit_response
        if "/v1/query/" in request.url:
            assert self.query_response is not None, "query response was not configured"
            return self.query_response
        if "/v1/files/retrieve" in request.url:
            assert (
                self.file_retrieve_response is not None
            ), "file retrieve response was not configured"
            return self.file_retrieve_response
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    def stream(
        self, request: MiniMaxHailuoTransportRequest
    ) -> AbstractContextManager[_StreamResponse]:
        self.stream_calls.append(request)
        if self.stream_error is not None:
            raise self.stream_error
        assert self.download_response is not None, "download response was not configured"
        return _StreamResponse(self.download_response)


def _submit_response(
    *, status: int = 200, body: dict | None = None
) -> MiniMaxHailuoTransportResponse:
    if body is None:
        body = {
            "task_id": TASK_ID,
            "base_resp": {"status_code": 0, "status_msg": "ok"},
        }
    return MiniMaxHailuoTransportResponse(
        status_code=status,
        headers={"content-type": "application/json"},
        body=json.dumps(body).encode(),
    )


def _query_response(
    *, status: str = "Success", body: dict | None = None
) -> MiniMaxHailuoTransportResponse:
    if body is None:
        body = {
            "task_id": TASK_ID,
            "status": status,
            "file_id": FILE_ID,
            "base_resp": {"status_code": 0, "status_msg": "ok"},
        }
        if status != "Success":
            body.pop("file_id", None)
    return MiniMaxHailuoTransportResponse(
        status_code=200,
        headers={"content-type": "application/json"},
        body=json.dumps(body).encode(),
    )


def _file_retrieve_response(
    *,
    status: int = 200,
    body: dict | None = None,
) -> MiniMaxHailuoTransportResponse:
    if body is None:
        body = {
            "file": {"file_id": FILE_ID, "download_url": SIGNED_URL},
            "base_resp": {"status_code": 0, "status_msg": "ok"},
        }
    else:
        body = {
            **body,
            "base_resp": {"status_code": 0, "status_msg": "ok"},
        }
    return MiniMaxHailuoTransportResponse(
        status_code=status,
        headers={"content-type": "application/json"},
        body=json.dumps(body).encode(),
    )


def _download_response(
    *,
    status: int = 200,
    body: bytes = b"\x00\x00\x00\x18ftypisom",
    content_type: str = "video/mp4",
) -> MiniMaxHailuoTransportResponse:
    return MiniMaxHailuoTransportResponse(
        status_code=status,
        headers={"content-type": content_type},
        body=body,
    )


class _PermitDouble:
    def __init__(self, binding: dict[str, str]) -> None:
        self.binding = dict(binding)
        self.consumed = False

    def _validate_paid_provider_operation_permit(self, **binding: str) -> bool:
        return not self.consumed and binding == self.binding

    def _consume_paid_provider_operation_permit(self, **binding: str) -> bool:
        if not self._validate_paid_provider_operation_permit(**binding):
            return False
        self.consumed = True
        return True


def _real_permit(binding: dict[str, str]) -> _DurablePaidProviderSubmitPermit:
    return _DurablePaidProviderSubmitPermit(
        _PAID_PROVIDER_PERMIT_TOKEN,
        binding=binding,
        durability_validator=lambda: True,
    )


def _preview(resolved: ResolvedVideoGenerationRequest) -> VideoGenerationPreview:
    return VideoGenerationPreview.create(
        resolved=resolved,
        estimated_cost_upper_bound_microunits=2_000_000,
        currency="CNY",
        destination="https://api.minimaxi.com",
        egress_item_ids=("prompt",),
    )


def _paid_preview(
    resolved: ResolvedVideoGenerationRequest,
    *,
    attempt_id: str = "attempt-hailuo-1",
    video_preview: VideoGenerationPreview | None = None,
) -> PaidProviderCallPreview:
    preview = video_preview or _preview(resolved)
    return PaidProviderCallPreview.create(
        attempt_id=attempt_id,
        operation="video_generation",
        provider_kind=resolved.provider_kind,
        model_id=resolved.model_id,
        request_fingerprint=resolved.resolved_generation_hash,
        billing_mode="remote_metered",
        currency=preview.currency,
        estimated_cost_upper_bound_microunits=(
            preview.estimated_cost_upper_bound_microunits
        ),
        destination=preview.destination,
        method="POST",
        egress_items=(
            PaidProviderEgressItem(
                item_id="prompt",
                sha256=hashlib.sha256(PROMPT_TEXT.encode("utf-8")).hexdigest(),
                size_bytes=len(PROMPT_TEXT.encode("utf-8")),
                mime_type="text/plain",
                purpose="prompt",
            ),
        ),
        retention_mode="provider_standard",
        provider_policy_snapshot_id="minimax-hailuo-policy-1",
        secret_reference=SecretReference(
            kind="secret_store",
            reference_id="MINIMAX_API_KEY",
        ),
    )


def _paid_authorization(
    preview: PaidProviderCallPreview,
) -> PaidProviderAuthorizationDecision:
    issued_at = _FIXED_NOW - timedelta(minutes=1)
    return PaidProviderAuthorizationDecision.create(
        attempt_id=preview.attempt_id,
        preview_fingerprint=preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="test-owner", actor_kind="human"),
        opt_in_policy_receipt_id="opt-in-hailuo",
        budget_policy_id="budget-hailuo",
        budget_currency=preview.currency,
        project_budget_ceiling_microunits=10_000_000,
        per_call_ceiling_microunits=max(
            1, preview.estimated_cost_upper_bound_microunits
        ),
        egress_authorized=True,
        egress_policy_receipt_id="egress-hailuo",
        live_test_authorized=True,
        live_authorization_receipt_id="live-hailuo",
        issued_at=issued_at,
        expires_at=issued_at + timedelta(minutes=10),
        max_submit_count=1,
    )


def _paid_submit_receipt(
    resolved: ResolvedVideoGenerationRequest,
    preview: PaidProviderCallPreview,
    *,
    external_effect_id: str = TASK_ID,
) -> PaidProviderSubmitReceipt:
    return PaidProviderSubmitReceipt.create(
        attempt_id=preview.attempt_id,
        request_fingerprint=resolved.resolved_generation_hash,
        preview_fingerprint=preview.preview_fingerprint,
        gate_receipt_fingerprint=HASH_A,
        reservation_id="reservation-hailuo-1",
        outcome=PaidProviderSubmitOutcome.ACCEPTED,
        external_effect_id=external_effect_id,
        recorded_at=datetime(2026, 8, 18, 12, 5, tzinfo=UTC),
    )


def _build_submit_inputs(
    *,
    transport: _FakeTransport | None = None,
) -> tuple[
    MiniMaxHailuoVideoProvider,
    ResolvedVideoGenerationRequest,
    VideoGenerationPreview,
    PaidProviderCallPreview,
    PaidProviderAuthorizationDecision,
    dict[str, str],
    _FakeTransport,
    _SecretResolver,
]:
    transport_obj = transport or _FakeTransport(submit_response=_submit_response())
    secret = _SecretResolver()
    provider = MiniMaxHailuoVideoProvider(
        transport=transport_obj,
        credential=secret,
        now=_fixed_now,
    )
    resolved = provider.resolve(_request())
    video_preview = _preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    authorization = _paid_authorization(paid_preview)
    binding = build_video_paid_permit_binding(
        resolved, video_preview, paid_preview, authorization
    )
    return (
        provider,
        resolved,
        video_preview,
        paid_preview,
        authorization,
        binding,
        transport_obj,
        secret,
    )


def _block_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: None)
    monkeypatch.setattr(socket.socket, "connect", lambda *a, **k: None)


def _provider_file_id(file_id: str = FILE_ID) -> str:
    return "hailuo-content-" + hashlib.sha256(file_id.encode("utf-8")).hexdigest()


def test_module_is_not_exported_from_package_root():
    for name in ("MiniMaxHailuoVideoProvider", "MiniMaxHailuoTransport"):
        assert not hasattr(production_root, name)


def test_capabilities_seal_minimal_t2v_only_profile():
    provider = MiniMaxHailuoVideoProvider(
        transport=_FakeTransport(), credential=_SecretResolver()
    )
    capabilities = provider.capabilities()
    assert capabilities.provider_name == "minimax_hailuo"
    assert len(capabilities.variants) == 1
    variant = capabilities.variants[0]
    assert variant.capability_id == "minimax-hailuo-2.3-v1-t2v-768p-6s-16x9"
    assert variant.execution_kind is VideoExecutionKind.REMOTE
    assert variant.billing_kind is BillingKind.METERED
    assert variant.mode is VideoGenerationMode.TEXT_TO_VIDEO
    assert variant.output.duration_seconds == 6
    assert variant.output.native_audio is False
    assert variant.output.fps is None
    assert variant.allowed_image_roles == ()
    assert variant.negative_prompt_supported is False
    assert variant.seed_supported is False
    assert variant.fps_supported is False
    assert variant.lookup_supported is True


def test_resolve_rejects_seed_and_negative_prompt_and_image_bindings():
    provider = MiniMaxHailuoVideoProvider(
        transport=_FakeTransport(),
        credential=_SecretResolver(),
    )
    binding = VideoImageReferenceBinding(
        role="first_frame",
        asset_id="image-1",
        asset_sha256=HASH_A,
        mime_type="image/png",
        width=1024,
        height=576,
    )
    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(_request(seed=42))
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED

    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(_request(negative_prompt_text="flicker"))
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED

    base = _request()
    fields = {
        name: getattr(base, name)
        for name in VideoGenerationRequest.model_fields
        if name != "image_bindings"
    }
    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(
            VideoGenerationRequest.model_construct(
                **fields, image_bindings=(binding,)
            )
        )
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


def test_preview_seals_destination_currency_and_upper_bound():
    provider = MiniMaxHailuoVideoProvider(
        transport=_FakeTransport(),
        credential=_SecretResolver(),
    )
    resolved = provider.resolve(_request())
    preview = provider.preview(resolved)
    assert preview.destination == "https://api.minimaxi.com"
    assert preview.currency == "CNY"
    assert preview.estimated_cost_upper_bound_microunits == 2_000_000
    assert preview.egress_item_ids == ("prompt",)
    assert preview.billing_kind is BillingKind.METERED


def test_accepted_submit_emits_exact_request_payload_and_task_id_without_revealing_secret(
    monkeypatch: pytest.MonkeyPatch,
):
    _block_socket(monkeypatch)
    (
        provider,
        resolved,
        video_preview,
        paid_preview,
        authorization,
        binding,
        transport,
        secret,
    ) = _build_submit_inputs()
    permit = _real_permit(binding)

    result = provider.submit(
        resolved, video_preview, paid_preview, authorization, permit
    )

    assert len(transport.calls) == 1
    sent = transport.calls[0]
    assert sent.method == "POST"
    assert sent.url == "https://api.minimaxi.com/v1/video_generation"
    assert sent.headers == {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {SECRET_TEXT}",
    }
    payload = json.loads(sent.body)
    assert payload == {
        "model": "MiniMax-Hailuo-2.3",
        "prompt": PROMPT_TEXT,
        "duration": 6,
        "resolution": "768P",
    }
    assert payload["prompt"] == PROMPT_TEXT
    assert result.external_effect_id == TASK_ID
    assert result.resolved_generation_hash == resolved.resolved_generation_hash
    assert secret.invocations == 1

    assert SECRET_TEXT not in repr(provider)
    assert SECRET_TEXT not in str(sent.body)
    assert SECRET_TEXT not in repr(transport.calls)
    assert SECRET_TEXT not in repr(paid_preview)
    assert SECRET_TEXT not in repr(authorization)


def test_submit_authorization_header_uses_bearer_and_is_never_persisted(monkeypatch):
    _block_socket(monkeypatch)
    (
        provider,
        resolved,
        video_preview,
        paid_preview,
        authorization,
        binding,
        transport,
        _,
    ) = _build_submit_inputs()
    provider.submit(
        resolved, video_preview, paid_preview, authorization, _real_permit(binding)
    )
    sent = transport.calls[0]
    assert sent.headers["authorization"].startswith("Bearer ")
    assert SECRET_TEXT in sent.headers["authorization"]
    assert SECRET_TEXT not in repr(transport.calls[0])


def test_foreign_duck_typed_permit_is_rejected_before_transport(monkeypatch):
    _block_socket(monkeypatch)
    (
        provider,
        resolved,
        video_preview,
        paid_preview,
        authorization,
        binding,
        transport,
        _,
    ) = _build_submit_inputs()

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            video_preview,
            paid_preview,
            authorization,
            _PermitDouble(binding),
        )

    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED
    assert transport.calls == []


def test_real_committer_permit_drives_exactly_one_submit(tmp_path: Path):
    write_production_project(tmp_path)
    make_manifest_23_project(tmp_path)
    manifest_path = tmp_path / "state/manifest.json"
    manifest = ProductionManifest.model_validate_json(manifest_path.read_bytes())
    manifest_path.write_text(
        manifest.model_copy(update={"schema_version": "2.7"}).model_dump_json(
            indent=2
        ),
        encoding="utf-8",
    )
    transport = _FakeTransport(submit_response=_submit_response())
    provider = MiniMaxHailuoVideoProvider(
        transport=transport,
        credential=_SecretResolver(),
        now=_fixed_now,
    )
    resolved = provider.resolve(_request())
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    authorization = _paid_authorization(paid_preview)
    committer = ProductionStateCommitter(
        tmp_path,
        paid_provider_authorizer=(
            lambda exact: authorization if exact == paid_preview else None
        ),
        paid_provider_clock=_fixed_now,
    )
    service = VideoGenerationService(committer=committer, provider=provider)

    service.start(attempt_id=paid_preview.attempt_id, request=resolved)
    submission = service.submit_once(
        attempt_id=paid_preview.attempt_id,
        paid_preview=paid_preview,
        reservation_id="reservation-hailuo-real-1",
    )

    assert submission.resolved_generation_hash == resolved.resolved_generation_hash
    persisted = committer._read_manifest().attempts[-1]
    assert persisted.paid_provider_state is not None
    assert persisted.paid_provider_state.submit_receipt is not None
    receipt = committer._reopen_paid_submit(
        persisted.paid_provider_state.submit_receipt
    )
    assert receipt.external_effect_id == TASK_ID
    assert len(transport.calls) == 1
    assert transport.calls[0].method == "POST"


def test_paid_preview_must_bind_exact_prompt_and_secret_reference(monkeypatch):
    _block_socket(monkeypatch)
    (
        provider,
        resolved,
        video_preview,
        paid_preview,
        authorization,
        binding,
        transport,
        _,
    ) = _build_submit_inputs()
    wrong_item = paid_preview.egress_items[0].model_copy(update={"sha256": HASH_A})
    wrong_preview = PaidProviderCallPreview.create(
        **{
            **paid_preview.model_dump(
                exclude={"preview_fingerprint", "egress_items"}
            ),
            "egress_items": (wrong_item,),
        }
    )
    wrong_authorization = _paid_authorization(wrong_preview)
    wrong_binding = build_video_paid_permit_binding(
        resolved, video_preview, wrong_preview, wrong_authorization
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved,
            video_preview,
            wrong_preview,
            wrong_authorization,
            _real_permit(wrong_binding),
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert transport.calls == []


def test_httpx_transport_never_follows_submit_redirect():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            307,
            headers={"location": "https://api.minimaxi.com/redirected"},
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )
    transport = HttpxMiniMaxHailuoTransport(client=client)
    response = transport.request(
        MiniMaxHailuoTransportRequest(
            method="POST",
            url="https://api.minimaxi.com/v1/video_generation",
            headers={"authorization": f"Bearer {SECRET_TEXT}"},
            body=b"{}",
        )
    )

    assert response.status_code == 307
    assert len(calls) == 1


@pytest.mark.parametrize("permit_kind", ["none", "mismatched", "consumed"])
def test_invalid_permits_are_rejected_before_transport(
    monkeypatch: pytest.MonkeyPatch, permit_kind: str
):
    _block_socket(monkeypatch)
    (
        provider,
        resolved,
        video_preview,
        paid_preview,
        authorization,
        binding,
        transport,
        _,
    ) = _build_submit_inputs()
    if permit_kind == "none":
        candidate = None
    elif permit_kind == "mismatched":
        candidate = _PermitDouble({**binding, "request_fingerprint": "f" * 64})
    else:
        first_permit = _real_permit(binding)
        provider.submit(
            resolved, video_preview, paid_preview, authorization, first_permit
        )
        transport.calls.clear()
        candidate = first_permit

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved, video_preview, paid_preview, authorization, candidate
        )
    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED
    assert transport.calls == []


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
def test_pre_acceptance_4xx_is_fail_closed_without_task_identity(
    monkeypatch: pytest.MonkeyPatch, status: int
):
    _block_socket(monkeypatch)
    (
        provider,
        resolved,
        video_preview,
        paid_preview,
        authorization,
        binding,
        transport,
        _,
    ) = _build_submit_inputs()
    transport.submit_response = _submit_response(
        status=status, body={"error": "TOP-SECRET-MINIMAX-BODY"}
    )
    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved, video_preview, paid_preview, authorization, _real_permit(binding)
        )
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    assert "TOP-SECRET-MINIMAX-BODY" not in str(exc_info.value)
    assert "TOP-SECRET-MINIMAX-BODY" not in repr(exc_info.value)
    assert len(transport.calls) == 1


def test_http_408_after_permit_consumption_is_outcome_unknown(monkeypatch):
    _block_socket(monkeypatch)
    (
        provider,
        resolved,
        video_preview,
        paid_preview,
        authorization,
        binding,
        transport,
        _,
    ) = _build_submit_inputs()
    transport.submit_response = _submit_response(
        status=408, body={"error": "TOP-SECRET-MINIMAX-BODY"}
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved, video_preview, paid_preview, authorization, _real_permit(binding)
        )

    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert "TOP-SECRET-MINIMAX-BODY" not in str(exc_info.value)
    assert len(transport.calls) == 1


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_5xx_after_permit_consumption_is_outcome_unknown_without_retry(
    monkeypatch: pytest.MonkeyPatch, status: int
):
    _block_socket(monkeypatch)
    (
        provider,
        resolved,
        video_preview,
        paid_preview,
        authorization,
        binding,
        transport,
        _,
    ) = _build_submit_inputs()
    transport.submit_response = _submit_response(
        status=status, body={"error": "TOP-SECRET-MINIMAX-BODY"}
    )
    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved, video_preview, paid_preview, authorization, _real_permit(binding)
        )
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert exc_info.value.retryable is False
    assert "TOP-SECRET-MINIMAX-BODY" not in str(exc_info.value)
    assert len(transport.calls) == 1


def test_transport_exception_after_permit_consumption_is_outcome_unknown(monkeypatch):
    _block_socket(monkeypatch)
    (
        provider,
        resolved,
        video_preview,
        paid_preview,
        authorization,
        binding,
        transport,
        _,
    ) = _build_submit_inputs()
    transport.submit_error = TimeoutError("TOP-SECRET-MINIMAX-TIMEOUT")
    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved, video_preview, paid_preview, authorization, _real_permit(binding)
        )
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert "TOP-SECRET-MINIMAX-TIMEOUT" not in str(exc_info.value)
    assert "TOP-SECRET-MINIMAX-TIMEOUT" not in repr(exc_info.value)
    assert len(transport.calls) == 1


@pytest.mark.parametrize(
    "body",
    [
        b"not-json",
        b"",
        b"{}",
        b'{"task_id":"abc","base_resp":{}}',
        b'{"task_id":"abc"}',
        b'{"base_resp":{"status_code":0,"status_msg":"ok"}}',
        b'{"task_id":123,"base_resp":{"status_code":0,"status_msg":"ok"}}',
    ],
)
def test_malformed_2xx_submit_is_outcome_unknown_without_retry(
    monkeypatch: pytest.MonkeyPatch, body: bytes
):
    _block_socket(monkeypatch)
    (
        provider,
        resolved,
        video_preview,
        paid_preview,
        authorization,
        binding,
        transport,
        _,
    ) = _build_submit_inputs()
    transport.submit_response = MiniMaxHailuoTransportResponse(
        status_code=200,
        headers={"content-type": "application/json"},
        body=body,
    )
    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved, video_preview, paid_preview, authorization, _real_permit(binding)
        )
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert len(transport.calls) == 1


def test_structured_submit_rejection_is_known_no_effect_and_sanitized(monkeypatch):
    _block_socket(monkeypatch)
    (
        provider,
        resolved,
        video_preview,
        paid_preview,
        authorization,
        binding,
        transport,
        _,
    ) = _build_submit_inputs()
    transport.submit_response = _submit_response(
        body={
            "base_resp": {
                "status_code": 2013,
                "status_msg": "TOP-SECRET-MINIMAX-BODY",
            }
        }
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.submit(
            resolved, video_preview, paid_preview, authorization, _real_permit(binding)
        )

    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    assert exc_info.value.retryable is False
    assert exc_info.value.technical_detail == "provider_code=2013"
    assert "TOP-SECRET-MINIMAX-BODY" not in str(exc_info.value)
    assert len(transport.calls) == 1


@pytest.mark.parametrize(
    ("raw_status", "expected_state"),
    [
        ("Queueing", VideoTaskState.QUEUED),
        ("Preparing", VideoTaskState.RUNNING),
        ("Processing", VideoTaskState.RUNNING),
        ("Success", VideoTaskState.SUCCEEDED),
        ("Fail", VideoTaskState.FAILED),
    ],
)
def test_status_maps_queueing_preparing_processing_success_and_fail(
    monkeypatch: pytest.MonkeyPatch, raw_status: str, expected_state: VideoTaskState
):
    _block_socket(monkeypatch)
    transport = _FakeTransport(query_response=_query_response(status=raw_status))
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=_SecretResolver(),
        now=_fixed_now,
    )
    resolved = provider.resolve(_request())
    video_preview = _preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    submit_receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )
    observation = provider.get_status(submission, submit_receipt)
    assert observation.state is expected_state
    if expected_state is VideoTaskState.SUCCEEDED:
        assert observation.provider_file_id is not None
        assert observation.provider_file_id.startswith("hailuo-content-")
        assert SIGNED_URL not in repr(observation)
        assert SIGNED_URL not in repr(submission)
        assert SIGNED_URL not in repr(submit_receipt)
        assert FILE_ID not in repr(observation)
        assert FILE_ID not in repr(submission)
    else:
        assert observation.provider_file_id is None


def test_status_query_path_contains_exact_task_id_and_bearer(monkeypatch):
    _block_socket(monkeypatch)
    task_id = "abc.def-123_xyz"
    query_body = {
        "task_id": task_id,
        "status": "Queueing",
        "base_resp": {"status_code": 0, "status_msg": "ok"},
    }
    transport = _FakeTransport(
        query_response=MiniMaxHailuoTransportResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body=json.dumps(query_body).encode(),
        )
    )
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=_SecretResolver(),
        now=_fixed_now,
    )
    resolved = provider.resolve(_request())
    video_preview = _preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    submit_receipt = _paid_submit_receipt(
        resolved, paid_preview, external_effect_id=task_id
    )
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )
    provider.get_status(submission, submit_receipt)
    query_call = transport.calls[0]
    assert query_call.method == "GET"
    assert query_call.url == (
        "https://api.minimaxi.com/v1/query/video_generation?task_id=abc.def-123_xyz"
    )
    assert query_call.headers["authorization"] == f"Bearer {SECRET_TEXT}"


def test_status_query_5xx_is_typed_provider_failure(monkeypatch):
    _block_socket(monkeypatch)
    transport = _FakeTransport(
        query_response=MiniMaxHailuoTransportResponse(
            status_code=500,
            headers={},
            body=b"TOP-SECRET-MINIMAX-BODY",
        )
    )
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=_SecretResolver(),
        now=_fixed_now,
    )
    resolved = provider.resolve(_request())
    video_preview = _preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    submit_receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )
    with pytest.raises(AiVideoError) as exc_info:
        provider.get_status(submission, submit_receipt)
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    assert exc_info.value.retryable is True
    assert "TOP-SECRET-MINIMAX-BODY" not in str(exc_info.value)
    assert len(transport.calls) == 1


@pytest.mark.parametrize(
    ("provider_code", "expected_retryable"),
    [
        (1000, True),
        (1001, True),
        (1002, True),
        (1024, True),
        (1033, True),
        (1039, True),
        (1041, True),
        (2045, True),
        (2056, True),
        (1004, False),
        (1008, False),
        (1026, False),
        (1027, False),
        (1042, False),
        (2013, False),
        (2049, False),
    ],
)
def test_status_query_normalizes_official_base_resp_codes(
    monkeypatch, provider_code: int, expected_retryable: bool
):
    _block_socket(monkeypatch)
    transport = _FakeTransport(
        query_response=MiniMaxHailuoTransportResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body=json.dumps(
                {
                    "base_resp": {
                        "status_code": provider_code,
                        "status_msg": "TOP-SECRET-MINIMAX-BODY",
                    }
                }
            ).encode(),
        )
    )
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=_SecretResolver(), now=_fixed_now
    )
    resolved = provider.resolve(_request())
    paid_preview = _paid_preview(resolved)
    submit_receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.get_status(submission, submit_receipt)

    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    assert exc_info.value.retryable is expected_retryable
    assert exc_info.value.technical_detail == f"provider_code={provider_code}"
    assert "TOP-SECRET-MINIMAX-BODY" not in str(exc_info.value)


def test_credential_resolver_exception_is_sanitized_before_transport(monkeypatch):
    _block_socket(monkeypatch)

    def broken_credential() -> str:
        raise RuntimeError("TOP-SECRET-CREDENTIAL-DIAGNOSTIC")

    transport = _FakeTransport(query_response=_query_response(status="Queueing"))
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=broken_credential, now=_fixed_now
    )
    resolved = provider.resolve(_request())
    paid_preview = _paid_preview(resolved)
    submit_receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.get_status(submission, submit_receipt)

    assert exc_info.value.code is ErrorCode.PAID_PROVIDER_EGRESS_NOT_AUTHORIZED
    assert "TOP-SECRET-CREDENTIAL-DIAGNOSTIC" not in str(exc_info.value)
    assert "TOP-SECRET-CREDENTIAL-DIAGNOSTIC" not in repr(exc_info.value)
    assert transport.calls == []


def test_file_retrieve_emits_exact_endpoint_with_bearer(monkeypatch):
    _block_socket(monkeypatch)
    download_body = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 32
    expected_digest = hashlib.sha256(download_body).hexdigest()
    transport = _FakeTransport(
        query_response=_query_response(status="Success"),
        file_retrieve_response=_file_retrieve_response(),
        download_response=_download_response(body=download_body),
    )
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=_SecretResolver(),
        now=_fixed_now,
    )
    resolved = provider.resolve(_request())
    video_preview = _preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    submit_receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )
    observation = VideoTaskObservation.create(
        submission=submission,
        state=VideoTaskState.SUCCEEDED,
        observed_at=datetime(2026, 8, 18, 12, 5, tzinfo=UTC),
        progress_milli=1000,
        provider_file_id=_provider_file_id(),
    )
    sink = BytesIO()
    fetch_receipt = provider.fetch(submission, submit_receipt, observation, sink)

    assert fetch_receipt.size_bytes == len(download_body)
    assert fetch_receipt.artifact_sha256 == expected_digest
    assert fetch_receipt.content_type == "video/mp4"
    assert fetch_receipt.provider_file_id == _provider_file_id()
    assert sink.getvalue() == download_body

    retrieve_calls = [
        call for call in transport.calls if "/v1/files/retrieve" in call.url
    ]
    assert len(retrieve_calls) == 1
    assert retrieve_calls[0].method == "GET"
    assert retrieve_calls[0].url == (
        f"https://api.minimaxi.com/v1/files/retrieve?file_id={FILE_ID}"
    )
    assert retrieve_calls[0].headers["authorization"] == f"Bearer {SECRET_TEXT}"
    assert [call.url for call in transport.stream_calls] == [SIGNED_URL]
    assert "authorization" not in transport.stream_calls[0].headers


def test_fetch_canonicalizes_retrieve_int64_file_id_to_query_string(monkeypatch):
    _block_socket(monkeypatch)
    numeric_file_id = "176844028768320"
    transport = _FakeTransport(
        query_response=_query_response(
            body={
                "task_id": TASK_ID,
                "status": "Success",
                "file_id": numeric_file_id,
                "base_resp": {"status_code": 0, "status_msg": "ok"},
            }
        ),
        file_retrieve_response=_file_retrieve_response(
            body={
                "file": {
                    "file_id": int(numeric_file_id),
                    "download_url": SIGNED_URL,
                }
            }
        ),
        download_response=_download_response(body=b"canonical-id-video"),
    )
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=_SecretResolver(), now=_fixed_now
    )
    resolved = provider.resolve(_request())
    paid_preview = _paid_preview(resolved)
    submit_receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )
    observation = VideoTaskObservation.create(
        submission=submission,
        state=VideoTaskState.SUCCEEDED,
        observed_at=datetime(2026, 8, 18, 12, 5, tzinfo=UTC),
        progress_milli=1000,
        provider_file_id=_provider_file_id(numeric_file_id),
    )

    receipt = provider.fetch(submission, submit_receipt, observation, BytesIO())

    assert receipt.provider_file_id == _provider_file_id(numeric_file_id)
    assert len(transport.stream_calls) == 1


def test_file_retrieve_transient_base_resp_is_retryable_without_download(monkeypatch):
    _block_socket(monkeypatch)
    transport = _FakeTransport(
        query_response=_query_response(status="Success"),
        file_retrieve_response=MiniMaxHailuoTransportResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body=json.dumps(
                {
                    "base_resp": {
                        "status_code": 1033,
                        "status_msg": "TOP-SECRET-MINIMAX-BODY",
                    }
                }
            ).encode(),
        ),
        download_response=_download_response(body=b"must-not-download"),
    )
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=_SecretResolver(), now=_fixed_now
    )
    resolved = provider.resolve(_request())
    paid_preview = _paid_preview(resolved)
    submit_receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )
    observation = VideoTaskObservation.create(
        submission=submission,
        state=VideoTaskState.SUCCEEDED,
        observed_at=datetime(2026, 8, 18, 12, 5, tzinfo=UTC),
        progress_milli=1000,
        provider_file_id=_provider_file_id(),
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.fetch(submission, submit_receipt, observation, BytesIO())

    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    assert exc_info.value.retryable is True
    assert exc_info.value.technical_detail == "provider_code=1033"
    assert "TOP-SECRET-MINIMAX-BODY" not in str(exc_info.value)
    assert transport.stream_calls == []


def test_fetch_signed_url_is_never_persisted_in_repr_or_receipt(monkeypatch):
    _block_socket(monkeypatch)
    transport = _FakeTransport(
        query_response=_query_response(status="Success"),
        file_retrieve_response=_file_retrieve_response(),
        download_response=_download_response(body=b"some-mp4-bytes"),
    )
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=_SecretResolver(),
        now=_fixed_now,
    )
    resolved = provider.resolve(_request())
    video_preview = _preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    submit_receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )
    observation = VideoTaskObservation.create(
        submission=submission,
        state=VideoTaskState.SUCCEEDED,
        observed_at=datetime(2026, 8, 18, 12, 5, tzinfo=UTC),
        progress_milli=1000,
        provider_file_id=_provider_file_id(),
    )
    fetch_receipt = provider.fetch(
        submission, submit_receipt, observation, BytesIO()
    )
    targets = [
        repr(observation),
        repr(submission),
        repr(submit_receipt),
        repr(fetch_receipt),
        str(observation),
        str(submission),
        str(submit_receipt),
        str(fetch_receipt),
        observation.model_dump_json(),
        submission.model_dump_json(),
        submit_receipt.model_dump_json(),
        fetch_receipt.model_dump_json(),
    ]
    for target in targets:
        assert SIGNED_URL not in target
        assert "signed.cdn.minimax.io" not in target


def test_fetch_accepts_rotated_signed_url_for_same_durable_file(monkeypatch):
    _block_socket(monkeypatch)
    new_url = "https://signed.cdn.minimax.io/asset/rotated.mp4"
    transport = _FakeTransport(
        query_response=_query_response(status="Success"),
        file_retrieve_response=_file_retrieve_response(
            body={"file": {"file_id": FILE_ID, "download_url": new_url}}
        ),
        download_response=_download_response(body=b"any"),
    )
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=_SecretResolver(),
        now=_fixed_now,
    )
    resolved = provider.resolve(_request())
    video_preview = _preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    submit_receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )
    observation = VideoTaskObservation.create(
        submission=submission,
        state=VideoTaskState.SUCCEEDED,
        observed_at=datetime(2026, 8, 18, 12, 5, tzinfo=UTC),
        progress_milli=1000,
        provider_file_id=_provider_file_id(),
    )
    receipt = provider.fetch(submission, submit_receipt, observation, BytesIO())
    assert receipt.provider_file_id == _provider_file_id()
    assert len([c for c in transport.calls if "/v1/files/retrieve" in c.url]) == 1
    assert [call.url for call in transport.stream_calls] == [new_url]


def test_fetch_rejects_file_retrieve_identity_change_before_download(monkeypatch):
    _block_socket(monkeypatch)
    transport = _FakeTransport(
        query_response=_query_response(status="Success"),
        file_retrieve_response=_file_retrieve_response(
            body={"file": {"file_id": "different-file", "download_url": SIGNED_URL}}
        ),
        download_response=_download_response(body=b"must-not-download"),
    )
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=_SecretResolver(), now=_fixed_now
    )
    resolved = provider.resolve(_request())
    video_preview = _preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    submit_receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )
    observation = VideoTaskObservation.create(
        submission=submission,
        state=VideoTaskState.SUCCEEDED,
        observed_at=datetime(2026, 8, 18, 12, 5, tzinfo=UTC),
        progress_milli=1000,
        provider_file_id=_provider_file_id(),
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.fetch(submission, submit_receipt, observation, BytesIO())

    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    assert transport.stream_calls == []


def test_fetch_rejects_wrong_content_type_without_streaming(monkeypatch):
    _block_socket(monkeypatch)
    transport = _FakeTransport(
        query_response=_query_response(status="Success"),
        file_retrieve_response=_file_retrieve_response(),
        download_response=_download_response(
            body=b"definitely-not-mp4", content_type="text/html"
        ),
    )
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=_SecretResolver(),
        now=_fixed_now,
    )
    resolved = provider.resolve(_request())
    video_preview = _preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    submit_receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )
    observation = VideoTaskObservation.create(
        submission=submission,
        state=VideoTaskState.SUCCEEDED,
        observed_at=datetime(2026, 8, 18, 12, 5, tzinfo=UTC),
        progress_milli=1000,
        provider_file_id=_provider_file_id(),
    )
    sink = BytesIO()
    with pytest.raises(AiVideoError) as exc_info:
        provider.fetch(submission, submit_receipt, observation, sink)
    assert exc_info.value.code is ErrorCode.VIDEO_ARTIFACT_INVALID
    assert sink.getvalue() == b""


def test_fetch_rejects_declared_oversize_before_writing(monkeypatch):
    _block_socket(monkeypatch)
    transport = _FakeTransport(
        query_response=_query_response(status="Success"),
        file_retrieve_response=_file_retrieve_response(),
        download_response=MiniMaxHailuoTransportResponse(
            status_code=200,
            headers={
                "content-type": "video/mp4",
                "content-length": str(256 * 1024 * 1024 + 1),
            },
            body=b"small",
        ),
    )
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=_SecretResolver(), now=_fixed_now
    )
    resolved = provider.resolve(_request())
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    submit_receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )
    observation = VideoTaskObservation.create(
        submission=submission,
        state=VideoTaskState.SUCCEEDED,
        observed_at=_FIXED_NOW,
        progress_milli=1000,
        provider_file_id=_provider_file_id(),
    )
    sink = BytesIO()

    with pytest.raises(AiVideoError) as exc_info:
        provider.fetch(submission, submit_receipt, observation, sink)

    assert exc_info.value.code is ErrorCode.VIDEO_ARTIFACT_INVALID
    assert sink.getvalue() == b""


def test_fetch_transport_failure_is_typed_and_sanitized(monkeypatch):
    _block_socket(monkeypatch)
    transport = _FakeTransport(
        query_response=_query_response(status="Success"),
        file_retrieve_response=_file_retrieve_response(),
        download_response=_download_response(body=b"any"),
        stream_error=TimeoutError("download-failed"),
    )
    provider = MiniMaxHailuoVideoProvider(
        transport=transport, credential=_SecretResolver(),
        now=_fixed_now,
    )
    resolved = provider.resolve(_request())
    video_preview = _preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview=video_preview)
    submit_receipt = _paid_submit_receipt(resolved, paid_preview)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=resolved, receipt=submit_receipt
    )
    observation = VideoTaskObservation.create(
        submission=submission,
        state=VideoTaskState.SUCCEEDED,
        observed_at=datetime(2026, 8, 18, 12, 5, tzinfo=UTC),
        progress_milli=1000,
        provider_file_id=_provider_file_id(),
    )
    with pytest.raises(AiVideoError) as exc_info:
        provider.fetch(submission, submit_receipt, observation, BytesIO())
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    assert exc_info.value.retryable is True
    assert "download-failed" not in str(exc_info.value)
    assert "download-failed" not in repr(exc_info.value)


def test_module_does_not_reexport_module_level_sentinel_classes():
    for name in (
        "make_minimax_submit_permit",
        "DurableMiniMaxHailuoSubmitPermit",
        "MiniMaxHailuoSubmitPermit",
    ):
        assert not hasattr(hailuo_module, name)
        assert not hasattr(production_root, name)
