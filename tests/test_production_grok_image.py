from __future__ import annotations

import base64
import hashlib
import io
import json
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from PIL import Image

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._state_commit_contracts import (
    _DurablePaidProviderSubmitPermit,
    _PAID_PROVIDER_PERMIT_TOKEN,
)
from ai_video.production.artifact_contracts import ToolIdentity
from ai_video.production.grok_auth import GrokCredential, SECRET_REFERENCE
from ai_video.production.grok_profile import GROK_IMAGE_MODEL, GROK_PROFILE_VERSION, GrokProviderProfile
from ai_video.production.grok_subscription import (
    GROK_SUBSCRIPTION_ORIGIN,
    GrokSubscriptionBinding,
    reject_unverified_included_only,
)
from ai_video.production.image import (
    ImageGenerationAuthorization,
    ImageGenerationRequest,
    ImageProviderParameters,
    ImageReferenceBinding,
)
from ai_video.production.models import (
    ActorIdentity,
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderGateReceipt,
)
from ai_video.production.remote_image import RemoteImageAuthorization, remote_image_permit_binding
from ai_video.production.grok_image import (
    GROK_IMAGE_EDIT_URL,
    GrokImageProvider,
    HttpxGrokImageTransport,
)


NOW = datetime(2026, 10, 12, 5, 0, tzinfo=UTC)
ACCOUNT = "a" * 64


def _image_bytes(fmt: str, color: tuple[int, int, int] = (20, 40, 60)) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (8, 6), color).save(out, format=fmt)
    return out.getvalue()


CHARACTER = _image_bytes("PNG")
SCENE = _image_bytes("PNG", (80, 30, 10))
JPEG_OUTPUT = _image_bytes("JPEG", (200, 100, 50))


def _request(*, seed=None, width=None, height=None, negative=""):
    refs = (CHARACTER, SCENE)
    values = {
        "attempt_id": "grok-image-attempt-1",
        "provider_kind": "grok",
        "model_id": GROK_IMAGE_MODEL,
        "target_shot_id": "shot-1",
        "target_asset_role": "hero",
        "prompt_text": "Place the character in the scene",
        "negative_prompt_text": negative,
        "parameters": ImageProviderParameters(
            seed=seed,
            width=width,
            height=height,
            output_format="png",
            generation_revision=1,
        ),
        "references": (
            ImageReferenceBinding(
                role="character",
                creative_artifact_id="character-1",
                creative_revision=1,
                creative_content_hash="1" * 64,
                asset_id="asset-character",
                asset_sha256=hashlib.sha256(refs[0]).hexdigest(),
            ),
            ImageReferenceBinding(
                role="scene",
                creative_artifact_id="scene-1",
                creative_revision=1,
                creative_content_hash="2" * 64,
                asset_id="asset-scene",
                asset_sha256=hashlib.sha256(refs[1]).hexdigest(),
            ),
        ),
        "base_project": ProjectSnapshotPointer(
            path=Path(f"state/projects/project.1.{'3' * 64}.yaml"),
            revision=1,
            content_hash="3" * 64,
            file_sha256="4" * 64,
        ),
        "base_registry": RegistrySnapshotPointer(
            path=Path(f"assets/registry.{'5' * 64}.json"),
            revision_id="5" * 64,
            content_hash="5" * 64,
            file_sha256="6" * 64,
        ),
        "base_dependency_graph": DependencyGraphSnapshotPointer(
            revision_id="7" * 64,
            content_hash="7" * 64,
            path=Path(f"state/dependency_graph.{'7' * 64}.json"),
            file_sha256="8" * 64,
        ),
    }
    return ImageGenerationRequest.create(**values)


def _subscription():
    return GrokSubscriptionBinding(
        account_fingerprint=ACCOUNT,
        credential_reference_id="GROK_OAUTH",
        destination=GROK_SUBSCRIPTION_ORIGIN,
        model_id=GROK_IMAGE_MODEL,
        quota_observed_at=NOW - timedelta(seconds=30),
        quota_expires_at=NOW + timedelta(minutes=3),
        period_end=NOW + timedelta(days=20),
        used_percent=12.5,
        included_only_evidence_id="fixture-included-only",
    )


class _Response:
    def __init__(self, status_code: int, body: bytes):
        self.status_code = status_code
        self.headers = {"content-type": "application/json"}
        self._body = body

    def iter_bytes(self):
        yield self._body


class _Transport:
    def __init__(self, response: _Response | None = None, error: Exception | None = None):
        self.response = response or _Response(200, b'{"data":[{"b64_json":"' + base64.b64encode(JPEG_OUTPUT) + b'"}]}')
        self.error = error
        self.calls = []

    @contextmanager
    def stream(self, method, url, *, headers, content, follow_redirects):
        self.calls.append((method, url, headers, content, follow_redirects))
        if self.error is not None:
            raise self.error
        yield self.response


class _LocalPermit:
    pass


def _setup(*, guard=lambda _binding: None, response=None, error=None):
    images = {"asset-character": CHARACTER, "asset-scene": SCENE}
    transport = _Transport(response=response, error=error)
    provider = GrokImageProvider(
        GrokProviderProfile(account_fingerprint=ACCOUNT),
        transport,
        lambda expected: GrokCredential(
            access_token="synthetic-test-token",
            account_fingerprint=expected,
            expires_at=NOW + timedelta(hours=1),
        ),
        lambda binding: images[binding.asset_id],
        subscription_guard=guard,
        now=lambda: NOW,
    )
    request = _request()
    subscription = _subscription()
    preview = provider.preview(request, subscription)
    paid_preview = preview.remote_call
    decision = PaidProviderAuthorizationDecision.create(
        attempt_id=request.attempt_id,
        preview_fingerprint=paid_preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="fixture", actor_kind="codex"),
        opt_in_policy_receipt_id="fixture-opt-in",
        budget_policy_id="fixture-budget",
        budget_currency="USD",
        project_budget_ceiling_microunits=0,
        per_call_ceiling_microunits=0,
        subscription_submit_limit=1,
        egress_authorized=True,
        egress_policy_receipt_id="fixture-egress",
        live_test_authorized=True,
        live_authorization_receipt_id="fixture-live",
        issued_at=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(minutes=4),
        max_submit_count=1,
    )
    remote = RemoteImageAuthorization(preview=paid_preview, authorization=decision)
    authorization = ImageGenerationAuthorization.create(
        request=request,
        preview=preview,
        usage_license="fixture-license",
        policy_receipt_id="fixture-image-policy",
        remote_binding=remote,
    )
    gate = PaidProviderGateReceipt.create(
        preview=paid_preview,
        authorization=decision,
        reservation_id="grok-image-reservation-1",
        budget_snapshot_revision=1,
        budget_snapshot_content_hash="9" * 64,
        budget_snapshot_file_sha256="a" * 64,
    )
    return provider, transport, request, authorization, gate


def _permit(authorization):
    remote = authorization.remote_binding
    binding = remote_image_permit_binding(remote)
    binding["authorization_fingerprint"] = remote.authorization.authorization_fingerprint
    return _DurablePaidProviderSubmitPermit(
        _PAID_PROVIDER_PERMIT_TOKEN,
        binding=binding,
        durability_validator=lambda: True,
    )


def test_default_included_only_guard_blocks_preflight_before_post():
    provider, transport, request, authorization, _gate = _setup(
        guard=reject_unverified_included_only,
    )

    with pytest.raises(AiVideoError) as caught:
        provider.preflight(request, authorization)

    assert caught.value.code is ErrorCode.PAID_PROVIDER_BUDGET_REJECTED
    assert transport.calls == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": 7},
        {"negative": "avoid blur"},
        {"width": 512, "height": 512},
    ],
)
def test_unsupported_controls_are_rejected_without_post(kwargs):
    provider, transport, _request_value, authorization, _gate = _setup()
    request = _request(**kwargs)

    with pytest.raises(AiVideoError) as caught:
        provider.preflight(request, authorization)

    assert caught.value.code is ErrorCode.IMAGE_REQUEST_INVALID
    assert transport.calls == []


def test_local_image_permit_is_rejected_without_post():
    provider, transport, request, authorization, gate = _setup()

    with pytest.raises(AiVideoError) as caught:
        provider.generate(request, authorization, _LocalPermit(), gate_receipt=gate)

    assert caught.value.code is ErrorCode.IMAGE_PROVIDER_FAILED
    assert transport.calls == []


def test_jpeg_wire_bytes_are_preserved_and_losslessly_converted_to_png():
    provider, transport, request, authorization, gate = _setup()
    permit = _permit(authorization)

    result = provider.generate(request, authorization, permit, gate_receipt=gate)

    assert result.image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert result.wire_image_bytes == JPEG_OUTPUT
    assert result.remote_evidence.wire_mime_type == "image/jpeg"
    assert result.remote_evidence.conversion == "pillow-lossless-png"
    method, url, headers, body, follow_redirects = transport.calls[0]
    assert method == "POST"
    assert url == f"{GROK_SUBSCRIPTION_ORIGIN}/v1/images/edits"
    assert follow_redirects is False
    assert headers["Authorization"] == "Bearer synthetic-test-token"
    payload = json.loads(body)
    assert payload["model"] == GROK_IMAGE_MODEL
    assert payload["n"] == 1
    assert payload["response_format"] == "b64_json"
    assert payload["resolution"] == "1k"
    assert len(payload["images"]) == 2
    assert payload["images"][0]["url"] == "data:image/png;base64," + base64.b64encode(CHARACTER).decode()
    assert permit._paid_provider_operation_was_consumed(
        **remote_image_permit_binding(authorization.remote_binding)
    )


def test_lost_response_is_unknown_and_never_retried():
    provider, transport, request, authorization, gate = _setup(error=TimeoutError("reflected secret"))

    with pytest.raises(AiVideoError) as caught:
        provider.generate(request, authorization, _permit(authorization), gate_receipt=gate)

    assert caught.value.code is ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN
    assert "reflected secret" not in str(caught.value)
    assert len(transport.calls) == 1


def test_response_cannot_report_another_model_as_the_approved_image():
    document = {"model": "another-model", "data": [{"b64_json": base64.b64encode(JPEG_OUTPUT).decode()}]}
    provider, transport, request, authorization, gate = _setup(
        response=_Response(200, json.dumps(document).encode()),
    )

    with pytest.raises(AiVideoError) as caught:
        provider.generate(request, authorization, _permit(authorization), gate_receipt=gate)

    assert caught.value.code is ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN
    assert len(transport.calls) == 1


def test_quota_is_rechecked_after_credential_lookup_before_post():
    guard_calls = 0

    def guard(_binding):
        nonlocal guard_calls
        guard_calls += 1
        if guard_calls == 3:
            raise RuntimeError("quota changed")

    provider, transport, request, authorization, gate = _setup(guard=guard)
    permit = _permit(authorization)

    with pytest.raises(AiVideoError) as caught:
        provider.generate(request, authorization, permit, gate_receipt=gate)

    assert caught.value.code is ErrorCode.IMAGE_PROVIDER_FAILED
    assert guard_calls == 3
    assert transport.calls == []
    assert permit._paid_provider_operation_was_consumed(
        **remote_image_permit_binding(authorization.remote_binding)
    )


def test_httpx_transport_ignores_injected_client_auth_and_cookies():
    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(200, content=b"{}")

    client = httpx.Client(
        auth=httpx.BasicAuth("ambient-user", "ambient-password"),
        cookies={"session": "ambient-cookie"},
        transport=httpx.MockTransport(handle),
    )
    transport = HttpxGrokImageTransport(client=client)
    with transport.stream(
        "POST",
        GROK_IMAGE_EDIT_URL,
        headers={
            "Authorization": "Bearer synthetic-test-token",
            "Content-Type": "application/json",
        },
        content=b"{}",
        follow_redirects=False,
    ) as response:
        assert response.status_code == 200
        assert b"".join(response.iter_bytes()) == b"{}"

    assert len(seen) == 1
    assert seen[0].headers["authorization"] == "Bearer synthetic-test-token"
    assert "cookie" not in seen[0].headers
    assert "synthetic-test-token" not in repr(seen[0])
    assert seen[0].extensions["timeout"] == {
        "connect": 30.0,
        "read": 30.0,
        "write": 30.0,
        "pool": 30.0,
    }
    client.close()


def test_invalid_wire_format_is_unknown_and_reference_bytes_are_bound_before_post():
    bad_response = _Response(200, b'{"data":[{"b64_json":"' + base64.b64encode(b"not an image") + b'"}]}')
    provider, transport, request, authorization, gate = _setup(response=bad_response)

    with pytest.raises(AiVideoError) as caught:
        provider.generate(request, authorization, _permit(authorization), gate_receipt=gate)

    assert caught.value.code is ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN
    assert len(transport.calls) == 1

    _provider, _transport, changed_request, changed_auth, _changed_gate = _setup()
    changed_transport = _Transport()
    changed = GrokImageProvider(
        GrokProviderProfile(account_fingerprint=ACCOUNT),
        changed_transport,
        lambda expected: GrokCredential(
            access_token="synthetic-test-token",
            account_fingerprint=expected,
            expires_at=NOW + timedelta(hours=1),
        ),
        lambda _binding: SCENE,
        subscription_guard=lambda _binding: None,
        now=lambda: NOW,
    )
    with pytest.raises(AiVideoError) as ref_error:
        changed.preflight(changed_request, changed_auth)
    assert ref_error.value.code is ErrorCode.IMAGE_REQUEST_INVALID
    assert changed_transport.calls == []
