"""Seedream original PNG effects use the shared paid image lifecycle."""

import base64
import json
from datetime import timedelta
from io import BytesIO

import httpx
import pytest
from PIL import Image

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.image import ImageGenerationRequest, ImageGenerationAuthorization, ImageProviderParameters
from ai_video.production.paid_provider import PaidProviderAuthorizationDecision
from ai_video.production.remote_image import RemoteImageAuthorization
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.image_candidate import make_image_candidate_preparer
from ai_video.production.seedream import SeedreamImageProvider, SeedreamProfile, HttpxSeedreamImageTransport, SEEDREAM_MODEL
from paid_provider_support import NOW, paid_authorization
from test_production_state_commit import make_image_call_bundle
import production_project_factory as factory


def setup(root, respond, *, canvas=False):
    factory.write_production_project(root)
    inputs = factory.make_p7_image_generation_base(root, decodable_pngs=True)
    original, _, _ = make_image_call_bundle(root)
    values = {key: getattr(original, key) for key in ImageGenerationRequest.model_fields
        if key not in {"request_id", "request_fingerprint", "output_asset_id"}}
    values.update(provider_kind="seedream", model_id=SEEDREAM_MODEL, references=(),
        negative_prompt_text="", parameters=ImageProviderParameters(seed=None, width=2048,
            height=1152, output_format="png", generation_revision=1))
    request = ImageGenerationRequest.create(**values)
    client = httpx.Client(transport=httpx.MockTransport(respond), headers={"X-Forbidden": "inherited"})
    provider = SeedreamImageProvider(SeedreamProfile(upper_bound_microunits=50_000_000,
        observed_at=NOW, expires_at=NOW + timedelta(hours=1)),
        HttpxSeedreamImageTransport(client=client), lambda: "test-private-key", now=lambda: NOW)
    preview = provider.preview(request)
    values = paid_authorization(preview.remote_call).model_dump(mode="python", exclude={"authorization_fingerprint"})
    values.update(budget_currency="CNY", per_call_ceiling_microunits=50_000_000,
        project_budget_ceiling_microunits=150_000_000)
    paid = PaidProviderAuthorizationDecision.create(**values)
    authorization = ImageGenerationAuthorization.create(request=request, preview=preview,
        usage_license="fixture-only", policy_receipt_id="fixture-asset-first",
        remote_binding=RemoteImageAuthorization(preview=preview.remote_call, authorization=paid))
    from ai_video.canvas_image import canvas_image_candidate_preparer
    writer = ProductionStateCommitter(root,
        image_candidate_preparer=canvas_image_candidate_preparer() if canvas else make_image_candidate_preparer(inputs),
        paid_provider_authorizer=lambda p: paid if p == preview.remote_call else None,
        paid_provider_clock=lambda: NOW)
    return writer, (request, preview, authorization), provider, client


def png():
    out = BytesIO()
    Image.new("RGB", (2048, 1152), (30, 60, 90)).save(out, format="PNG")
    return out.getvalue()


def test_original_png_paid_activation_reopen_replay_and_wire_tamper(tmp_path):
    wire, calls = png(), []
    def respond(req):
        calls.append(req)
        assert req.url == "https://ark.cn-beijing.volces.com/api/v3/images/generations"
        assert "x-forbidden" not in req.headers
        assert json.loads(req.content) == dict(model=SEEDREAM_MODEL,
            prompt=bundle[0].prompt_text, size="2048x1152", output_format="png",
            response_format="b64_json", watermark=True)
        return httpx.Response(200, json={"model": SEEDREAM_MODEL,
            "data": [{"b64_json": base64.b64encode(wire).decode(), "size": "2048x1152"}]})
    writer, bundle, provider, client = setup(tmp_path, respond)
    with client:
        final = writer.generate_remote_image_asset(*bundle, provider)
        loaded = load_production_project(tmp_path / "project.yaml")
        assert loaded.manifest == final
        asset = next(a for a in loaded.registry.assets if a.asset_id == bundle[0].output_asset_id)
        assert asset.tool.name == "seedream" and asset.egress.remote
        assert (tmp_path / asset.artifact_path).read_bytes() == wire
        from ai_video.canvas_image_provenance import require_generated_canvas_selection
        require_generated_canvas_selection(asset=asset, snapshot="0" * 64, node_id="image-node",
            resource_id=asset.asset_id, previous=loaded)
        with pytest.raises(ValueError):
            require_generated_canvas_selection(asset=asset, snapshot="0" * 64, node_id="image-node",
                resource_id="wrong-source", previous=loaded)
        assert writer.generate_remote_image_asset(*bundle, provider) == final
        assert len(calls) == 1
        paths = list((tmp_path / "assets/files/seedream-wire").iterdir())
        assert len(paths) == 1 and paths[0].read_bytes() == wire
        paths[0].write_bytes(b"tamper")
        with pytest.raises(AiVideoError):
            load_production_project(tmp_path / "project.yaml")


@pytest.mark.parametrize("kind", ["timeout", "malformed", "wrong-model", "jpeg", "rejected"])
def test_failed_response_has_durable_outcome_without_retry(tmp_path, kind):
    calls = []
    def respond(req):
        calls.append(req)
        if kind == "timeout":
            raise httpx.ReadTimeout("private diagnostic")
        if kind == "rejected":
            return httpx.Response(400, json={"error": "private diagnostic"})
        if kind == "malformed":
            return httpx.Response(200, json={"data": []})
        raw = png()
        if kind == "jpeg":
            out = BytesIO()
            Image.new("RGB", (2048, 1152)).save(out, format="JPEG")
            raw = out.getvalue()
        return httpx.Response(200, json={"model": "wrong" if kind == "wrong-model" else SEEDREAM_MODEL,
            "data": [{"b64_json": base64.b64encode(raw).decode()}]})
    writer, bundle, provider, client = setup(tmp_path, respond)
    with client:
        with pytest.raises(AiVideoError) as error:
            writer.generate_remote_image_asset(*bundle, provider)
        expected = ErrorCode.IMAGE_PROVIDER_FAILED if kind == "rejected" else ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN
        assert error.value.code is expected
        assert "private diagnostic" not in str(error.value)
        loaded = load_production_project(tmp_path / "project.yaml")
        attempt = next(a for a in loaded.manifest.attempts if a.attempt_id == bundle[0].attempt_id)
        assert attempt.paid_provider_state.phase.value == ("known_no_effect" if kind == "rejected" else "outcome_unknown")
        with pytest.raises(AiVideoError):
            writer.generate_remote_image_asset(*bundle, provider)
        assert len(calls) == 1


def test_preflight_rejects_unsealed_changed_prompt_before_lookup_or_network(tmp_path):
    writer, bundle, provider, client = setup(tmp_path, lambda req: pytest.fail("network forbidden"))
    request, preview, auth = bundle
    with client, pytest.raises(AiVideoError):
        writer.generate_remote_image_asset(request.model_copy(update={"prompt_text": "changed"}), preview, auth, provider)


def test_missing_candidate_preparer_stops_before_any_submit_or_state_change(tmp_path):
    _, bundle, provider, client = setup(tmp_path, lambda req: pytest.fail("network forbidden"))
    writer = ProductionStateCommitter(tmp_path)
    before = (tmp_path / "state/manifest.json").read_bytes()
    with client, pytest.raises(AiVideoError):
        writer.generate_remote_image_asset(*bundle, provider)
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_expired_operator_bound_blocks_before_credential_or_network(tmp_path):
    writer, bundle, provider, client = setup(tmp_path, lambda req: pytest.fail("network forbidden"))
    provider._now = lambda: NOW + timedelta(hours=2)
    provider._credential = lambda: pytest.fail("credential forbidden")
    before = (tmp_path / "state/manifest.json").read_bytes()
    with client, pytest.raises(AiVideoError):
        writer.generate_remote_image_asset(*bundle, provider)
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_seedream_image_activates_in_canvas_authoring_graph(tmp_path):
    from test_canvas_production import runtime
    from ai_video.canvas_image import canvas_image_candidate_preparer
    service, _, _, _ = runtime(tmp_path)
    loaded = service._load()
    root = loaded.root
    calls = []
    def respond(req):
        calls.append(req)
        return httpx.Response(200, json={"model": SEEDREAM_MODEL,
            "data": [{"b64_json": base64.b64encode(png()).decode()}]})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        provider = SeedreamImageProvider(SeedreamProfile(upper_bound_microunits=1_000_000,
            observed_at=NOW, expires_at=NOW + timedelta(hours=1)),
            HttpxSeedreamImageTransport(client=client), lambda: "test-key", now=lambda: NOW)
        request = ImageGenerationRequest.create(attempt_id="canvas-image-1", provider_kind="seedream",
            model_id=SEEDREAM_MODEL, target_shot_id=loaded.shots[0].shot_id, target_asset_role="first_frame",
            prompt_text="A fictional adult at a metro seat.", negative_prompt_text="", references=(),
            parameters=ImageProviderParameters(seed=None, width=2048, height=1152, output_format="png", generation_revision=1),
            base_project=loaded.manifest.active_project, base_registry=loaded.manifest.active_registry,
            base_dependency_graph=loaded.manifest.active_dependency_graph)
        preview = provider.preview(request)
        values = paid_authorization(preview.remote_call).model_dump(mode="python", exclude={"authorization_fingerprint"})
        values["budget_currency"] = "CNY"
        paid = PaidProviderAuthorizationDecision.create(**values)
        auth = ImageGenerationAuthorization.create(request=request, preview=preview,
            usage_license="fixture-only", policy_receipt_id="fixture",
            remote_binding=RemoteImageAuthorization(preview=preview.remote_call, authorization=paid))
        writer = ProductionStateCommitter(root, image_candidate_preparer=canvas_image_candidate_preparer(),
            paid_provider_authorizer=lambda p: paid, paid_provider_clock=lambda: NOW)
        writer.generate_remote_image_asset(request, preview, auth, provider)
        result = load_production_project(root / "project.yaml")
        assert any(a.asset_id == request.output_asset_id for a in result.registry.assets)
        assert len(calls) == 1
        from test_canvas_sequence_packet import document
        from scripts.canvas_sequence_packet import build_sequence_packet
        from ai_video.production.seedance_source_expression import source_parts_sha256
        from ai_video.canvas_source_expression import adapted_canvas_prompt
        source = document()
        source["edges"] = [{"id": "anchor-a", "source": "anchor", "target": "a", "type": "reference"}]
        for node in source["nodes"]:
            draft = node["data"].get("generationDraft")
            if draft is not None:
                draft["parts"] = [{"type": "text", "text": "Enter the road"}]
                draft["references"] = []
                if node["id"] == "a":
                    draft["references"] = [{"slotId": "anchor", "nodeId": "anchor", "role": "firstFrame"}]
        source["nodes"].append({"id": "anchor", "type": "image", "data": {"resourceId": request.output_asset_id}})
        service.packet = build_sequence_packet(source, {"node_ids": ["a", "b"]})
        asset = next(a for a in result.registry.assets if a.asset_id == request.output_asset_id)
        parts = [{"type": "text", "text": "Enter the road"}]
        refs = [{"asset_id": asset.asset_id, "asset_sha256": asset.sha256, "role": "first_frame"}]
        expression = {"contract_version": "seedance-preserved-source/2", "parts": parts,
            "implicit_references": refs, "source_sha256": source_parts_sha256(parts, refs)}
        row = service.direction["shots"][0]
        row["shot"].update(preserved_source_expression=expression, intent=adapted_canvas_prompt(expression))
        row["shot"]["required_asset_roles"][-1]["asset_ids"] = [asset.asset_id]
        row["generation"]["references"] = [{"role": "approved_keyframe", "asset_id": asset.asset_id}]
        before = (root / "state/manifest.json").read_bytes()
        assert service.author(registry=result.registry).registry == result.registry
        assert (root / "state/manifest.json").read_bytes() == before
