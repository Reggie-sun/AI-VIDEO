"""Remote image effects through the canonical committer and strict project reader."""

import hashlib
import base64
import httpx
from io import BytesIO

from PIL import Image
import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.image import (
    ImageGenerationRequest, ImageGenerationPreview, ImageGenerationAuthorization,
    ImageProviderParameters, ImageProviderResult, ImageLocalResourceEvidence,
)
from ai_video.production.models import ToolIdentity
from ai_video.production.paid_provider import (
    PaidProviderCallPreview, PaidProviderSubmitReceipt, PaidProviderSubmitOutcome,
    PaidProviderEgressItem,
)
from ai_video.production.remote_image import (
    RemoteImageAuthorization, RemoteImageEvidence, remote_image_permit_binding,
)
from ai_video.production.grok_image_bytes import decode_grok_image
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
import production_project_factory as factory
from test_production_state_commit import make_image_call_bundle
from test_grok_subscription import binding, NOW
from test_grok_subscription_lifecycle import subscription_call, subscription_authorization


def remote_bundle(root):
    original, _, _ = make_image_call_bundle(root)
    values = {key: getattr(original, key) for key in ImageGenerationRequest.model_fields
        if key not in {"request_id", "request_fingerprint", "output_asset_id"}}
    values.update(provider_kind="grok", model_id="grok-imagine-image-2.0", negative_prompt_text="",
        parameters=ImageProviderParameters(seed=None, width=None, height=None, output_format="png", generation_revision=1))
    request = ImageGenerationRequest.create(**values)
    loaded = load_production_project(root / "project.yaml")
    assets = {a.asset_id: a for a in loaded.registry.assets}
    p = subscription_call().model_dump(mode="python", exclude={"preview_fingerprint"})
    p.update(attempt_id=request.attempt_id, operation="image_generation", model_id=request.model_id,
        request_fingerprint=request.request_fingerprint, subscription_binding=binding(model_id=request.model_id),
        egress_items=(PaidProviderEgressItem(item_id="prompt", sha256=hashlib.sha256(request.prompt_text.encode()).hexdigest(),
            size_bytes=len(request.prompt_text.encode()), mime_type="text/plain", purpose="prompt"),
            *(PaidProviderEgressItem(item_id=f"{r.role}:{r.asset_id}", sha256=r.asset_sha256,
                size_bytes=assets[r.asset_id].size_bytes, mime_type=assets[r.asset_id].mime_type, purpose="reference")
                for r in request.references)))
    paid = PaidProviderCallPreview.create(**p)
    auth = subscription_authorization(paid, 2)
    preview = ImageGenerationPreview.create(request=request,
        reference_total_bytes=sum(assets[r.asset_id].size_bytes for r in request.references), remote_call=paid)
    authorization = ImageGenerationAuthorization.create(request=request, preview=preview,
        usage_license="fixture-only", policy_receipt_id="fake-included-only",
        remote_binding=RemoteImageAuthorization(preview=paid, authorization=auth))
    return request, preview, authorization


class FakeRemoteImage:
    """Fake effect executor; its test authority cannot assert live eligibility."""
    def __init__(self, *, fail=False, format="JPEG"):
        self.calls = 0
        self.fail = fail
        raw = BytesIO()
        Image.new("RGB", (2, 1), (30, 60, 90)).save(raw, format=format)
        self.wire = raw.getvalue()

    def preflight(self, request, authorization):
        assert authorization.remote_binding is not None

    def generate(self, request, authorization, permit, *, gate_receipt):
        assert permit._consume_paid_provider_operation_permit(**remote_image_permit_binding(authorization.remote_binding))
        self.calls += 1
        if self.fail:
            raise AiVideoError(code=ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN, user_message="response lost")
        png, mime, conversion = decode_grok_image(self.wire)
        receipt = PaidProviderSubmitReceipt.create(attempt_id=request.attempt_id,
            request_fingerprint=request.request_fingerprint,
            preview_fingerprint=authorization.remote_binding.preview.preview_fingerprint,
            gate_receipt_fingerprint=gate_receipt.gate_receipt_fingerprint,
            reservation_id=gate_receipt.reservation_id, outcome=PaidProviderSubmitOutcome.ACCEPTED,
            external_effect_id="fake-grok-content", recorded_at=NOW)
        return ImageProviderResult.create(request=request, authorization=authorization, image_bytes=png,
            content_type="image/png", provider_request_id=receipt.external_effect_id,
            adapter=ToolIdentity(name="grok", version="fixture-v1"),
            resource_evidence=ImageLocalResourceEvidence(elapsed_milliseconds=1, device_kind="unknown"),
            wire_image_bytes=self.wire, remote_evidence=RemoteImageEvidence(submit_receipt=receipt,
                wire_sha256=hashlib.sha256(self.wire).hexdigest(), wire_size_bytes=len(self.wire),
                wire_mime_type=mime, conversion=conversion))


def setup(root):
    factory.write_production_project(root)
    inputs = factory.make_p7_image_generation_base(root, decodable_pngs=True)
    request, preview, authorization = remote_bundle(root)
    writer = ProductionStateCommitter(root, image_candidate_preparer=factory.make_p7_image_candidate_preparer(inputs),
        paid_provider_authorizer=lambda p: authorization.remote_binding.authorization,
        paid_provider_clock=lambda: NOW)
    return writer, (request, preview, authorization)


@pytest.mark.parametrize("format", ["PNG", "JPEG", "WEBP"])
def test_remote_image_activation_retains_wire_egress_paid_and_exact_replay(tmp_path, format):
    writer, bundle = setup(tmp_path)
    provider = FakeRemoteImage(format=format)
    final = writer.generate_remote_image_asset(*bundle, provider)
    loaded = load_production_project(tmp_path / "project.yaml")
    asset = next(a for a in loaded.registry.assets if a.asset_id == bundle[0].output_asset_id)
    assert asset.egress.remote and asset.cost_receipt_id is not None
    assert loaded.manifest == final
    assert writer.generate_remote_image_asset(*bundle, provider) == final
    assert provider.calls == 1
    paths = list((tmp_path / "assets/files/grok-wire").iterdir())
    assert len(paths) == 1 and paths[0].read_bytes() == provider.wire
    paths[0].write_bytes(b"tampered")
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")
    with pytest.raises(AiVideoError):
        writer.generate_remote_image_asset(*bundle, provider)
    assert provider.calls == 1


def test_unknown_image_submit_is_durable_and_never_retried(tmp_path):
    writer, bundle = setup(tmp_path)
    provider = FakeRemoteImage(fail=True)
    with pytest.raises(AiVideoError):
        writer.generate_remote_image_asset(*bundle, provider)
    loaded = load_production_project(tmp_path / "project.yaml")
    attempt = next(a for a in loaded.manifest.attempts if a.attempt_id == bundle[0].attempt_id)
    assert attempt.status.value == "outcome_unknown"
    assert attempt.paid_provider_state.phase.value == "outcome_unknown"
    with pytest.raises(AiVideoError):
        writer.generate_remote_image_asset(*bundle, provider)
    assert provider.calls == 1


def test_remote_image_cannot_consume_local_generation_seam(tmp_path):
    writer, bundle = setup(tmp_path)
    provider = FakeRemoteImage()
    before = (tmp_path / "state/manifest.json").read_bytes()
    with pytest.raises(AiVideoError):
        writer.generate_image_asset(*bundle, provider)
    assert provider.calls == 0 and (tmp_path / "state/manifest.json").read_bytes() == before


@pytest.mark.parametrize("admitted", [False, True])
def test_real_grok_image_adapter_uses_canonical_writer_with_default_gate_closed(tmp_path, admitted):
    from datetime import timedelta
    from ai_video.production.grok_auth import GrokCredential
    from ai_video.production.grok_profile import GrokProviderProfile
    from ai_video.production.grok_image import GrokImageProvider, HttpxGrokImageTransport

    original_writer, (request, _, _) = setup(tmp_path)
    loaded = load_production_project(tmp_path / "project.yaml")
    assets = {a.asset_id: a for a in loaded.registry.assets}
    wire = FakeRemoteImage().wire
    calls = []
    def respond(req):
        calls.append(req)
        assert req.method == "POST"
        return httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(wire).decode()}]})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        provider = GrokImageProvider(GrokProviderProfile(account_fingerprint="a" * 64),
            HttpxGrokImageTransport(client=client),
            lambda account: GrokCredential(access_token="test-only", account_fingerprint=account,
                expires_at=NOW + timedelta(hours=1)),
            lambda ref: (tmp_path / assets[ref.asset_id].artifact_path).read_bytes(),
            now=lambda: NOW, **({"subscription_guard": lambda b: None} if admitted else {}))
        preview = provider.preview(request, binding(model_id=request.model_id))
        paid_auth = subscription_authorization(preview.remote_call, 2)
        authorization = ImageGenerationAuthorization.create(request=request, preview=preview,
            usage_license="fixture-only", policy_receipt_id="fake-included-only",
            remote_binding=RemoteImageAuthorization(preview=preview.remote_call, authorization=paid_auth))
        writer = ProductionStateCommitter(tmp_path,
            image_candidate_preparer=original_writer._image_candidate_preparer,
            paid_provider_authorizer=lambda p: paid_auth if p == preview.remote_call else None,
            paid_provider_clock=lambda: NOW)
        before = (tmp_path / "state/manifest.json").read_bytes()
        if not admitted:
            with pytest.raises(AiVideoError) as error:
                writer.generate_remote_image_asset(request, preview, authorization, provider)
            assert error.value.code is ErrorCode.PAID_PROVIDER_BUDGET_REJECTED
            assert calls == [] and (tmp_path / "state/manifest.json").read_bytes() == before
        else:
            final = writer.generate_remote_image_asset(request, preview, authorization, provider)
            assert load_production_project(tmp_path / "project.yaml").manifest == final
            assert writer.generate_remote_image_asset(request, preview, authorization, provider) == final
            assert len(calls) == 1
