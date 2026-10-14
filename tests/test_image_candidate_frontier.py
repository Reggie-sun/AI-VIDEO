"""Bootstrap asset projections must not look like unrelated image mutations."""
import base64
from datetime import timedelta

import httpx

from ai_video.canvas_production import CanvasProductionService
from ai_video.canvas_image import canvas_image_candidate_preparer
from ai_video.production.image import ImageGenerationRequest, ImageGenerationAuthorization, ImageProviderParameters
from ai_video.production.paid_provider import PaidProviderAuthorizationDecision
from ai_video.production.remote_image import RemoteImageAuthorization
from ai_video.production.project import load_production_project
from ai_video.production.seedream import SeedreamImageProvider, SeedreamProfile, HttpxSeedreamImageTransport, SEEDREAM_MODEL
from ai_video.production.state_commit import ProductionStateCommitter
from scripts.canvas_sequence_packet import build_sequence_packet
from paid_provider_support import NOW, paid_authorization
from test_canvas_authoring import direction
from test_canvas_render import _policy
from test_canvas_sequence_packet import document
from test_seedream_remote_image import png


def test_bootstrap_other_shot_image_does_not_block_paid_image_activation(tmp_path):
    source = document()
    source["nodes"].insert(0, {"id": "other", "type": "image", "data": {"resourceId": "other-resource"}})
    for node in source["nodes"]:
        draft = node.get("data", {}).get("generationDraft")
        if draft:
            draft["references"].append({"slotId": "other-slot", "nodeId": "other", "role": "reference"})
            draft["parts"].append({"type": "extension", "extension_type": "node", "object_id": "other-slot"})
            source["edges"].append({"id": "other-" + node["id"], "source": "other", "target": node["id"], "type": "reference"})
    director = direction()
    director["scenes"][0]["visual_reference_asset_ids"] = ["room-image", "other-image"]
    for item, identity in zip(director["shots"], ("room-image", "other-image")):
        item["shot"]["required_asset_roles"].append({"role": "first_frame", "asset_ids": [identity], "allowed_asset_types": ["image"]})
    raw = png()
    local = tmp_path / "reference.png"
    local.write_bytes(raw)
    service = CanvasProductionService(committer=ProductionStateCommitter(tmp_path),
        packet=build_sequence_packet(source, {"node_ids": ["a", "b"]}), direction=director)
    authored = service.author(png_selections=[
        {"asset_id": "room-image", "node_id": "room", "resource_id": "room-resource", "path": local, "usage_license": "fixture-only"},
        {"asset_id": "other-image", "node_id": "other", "resource_id": "other-resource", "path": local, "usage_license": "fixture-only"},
    ], allowed_asset_root=tmp_path)
    service.approve_authoring(bundle=authored, attempt_id="bootstrap", qa_policy=_policy())
    base = load_production_project(tmp_path / "project.yaml")
    other_shot = base.shots[1]
    assert "asset:other-image" not in {s.node_id for s in base.manifest.dependency_states}
    request = ImageGenerationRequest.create(attempt_id="bootstrap-image", provider_kind="seedream", model_id=SEEDREAM_MODEL,
        target_shot_id="one", target_asset_role="first_frame", prompt_text="Static preparation.", references=(), negative_prompt_text="",
        parameters=ImageProviderParameters(seed=None, width=2048, height=1152, output_format="png", generation_revision=1),
        base_project=base.manifest.active_project, base_registry=base.manifest.active_registry,
        base_dependency_graph=base.manifest.active_dependency_graph)
    calls = []
    def respond(req):
        calls.append(req)
        return httpx.Response(200, json={"model": SEEDREAM_MODEL, "data": [{"b64_json": base64.b64encode(raw).decode()}]})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        provider = SeedreamImageProvider(SeedreamProfile(upper_bound_microunits=50_000_000,
            observed_at=NOW, expires_at=NOW + timedelta(hours=1)), HttpxSeedreamImageTransport(client=client), lambda: "fixture-private", now=lambda: NOW)
        preview = provider.preview(request)
        values = paid_authorization(preview.remote_call).model_dump(mode="python", exclude={"authorization_fingerprint"})
        values.update(budget_currency="CNY", per_call_ceiling_microunits=50_000_000, project_budget_ceiling_microunits=150_000_000)
        paid = PaidProviderAuthorizationDecision.create(**values)
        auth = ImageGenerationAuthorization.create(request=request, preview=preview, usage_license="fixture-only", policy_receipt_id="fixture-image",
            remote_binding=RemoteImageAuthorization(preview=preview.remote_call, authorization=paid))
        writer = ProductionStateCommitter(tmp_path, image_candidate_preparer=canvas_image_candidate_preparer(),
            paid_provider_authorizer=lambda p: paid if p == preview.remote_call else None, paid_provider_clock=lambda: NOW)
        writer.generate_remote_image_asset(request, preview, auth, provider)
        reopened = load_production_project(tmp_path / "project.yaml")
        assert reopened.shots[1] == other_shot
        assert reopened.asset_paths["other-image"].read_bytes() == raw
        assert len(calls) == 1
        assert next(a for a in reopened.manifest.attempts if a.attempt_id == request.attempt_id).status.value == "succeeded"
