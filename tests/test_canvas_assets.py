"""Ordinary file selections compute Registry identity, never platform adoption."""
import pytest

from ai_video.canvas_assets import prepare_canvas_png_assets
from ai_video.canvas_production import CanvasProductionService
from ai_video.production.state_commit import ProductionStateCommitter
from test_canvas_authoring import packet, direction
from production_project_factory import _p7_png


def test_png_selection_measures_bytes_and_bootstraps_without_manual_hashes(tmp_path):
    source = tmp_path / "reference.png"
    source.write_bytes(_p7_png(rgba=b"\x11\x22\x33\xff"))
    selections = [{"asset_id": "room-reference", "node_id": "room", "resource_id": "room-resource",
                   "path": source, "usage_license": "fixture-only"}]
    registry, artifacts = prepare_canvas_png_assets(packet=packet(), selections=selections,
                                                   allowed_asset_root=tmp_path)
    assert registry.assets[0].creation_receipt_id.endswith(":room:room-resource")
    assert registry.assets[0].tool.name == "canvas-local-png-selection"
    assert registry.assets[0].width == 2
    (tmp_path / "project").mkdir()
    service = CanvasProductionService(committer=ProductionStateCommitter(tmp_path / "project"),
                                      packet=packet(), direction=direction())
    bundle = service.author(png_selections=selections, allowed_asset_root=tmp_path)
    bundle.bootstrap(committer=service.committer, attempt_id="canvas-import-bootstrap")
    assert service._load().registry == registry


@pytest.mark.parametrize("damage", ["resource", "node", "symlink", "outside", "duplicate"])
def test_png_selection_rejects_wrong_identity_or_file_boundary(tmp_path, damage):
    source = tmp_path / "reference.png"
    source.write_bytes(_p7_png(rgba=b"\x11\x22\x33\xff"))
    selection = {"asset_id": "room-reference", "node_id": "room", "resource_id": "room-resource",
                 "path": source, "usage_license": "fixture-only"}
    root = tmp_path
    if damage == "resource": selection["resource_id"] = "different-version"
    elif damage == "node": selection["node_id"] = "voice"
    elif damage == "symlink":
        link = tmp_path / "link.png"
        link.symlink_to(source)
        selection["path"] = link
    elif damage == "outside":
        root = tmp_path / "allowed"
        root.mkdir()
    selections = [selection, selection] if damage == "duplicate" else [selection]
    with pytest.raises((ValueError, OSError)):
        prepare_canvas_png_assets(packet=packet(), selections=selections, allowed_asset_root=root)


def subject_selections(tmp_path):
    source = packet()
    source["assets"].append({"id": "robot", "type": "subject", "data": {
        "title": "Robot", "main": {"refType": "resource_snapshot", "resourceId": "robot-front"},
        "auxiliaries": [{"refType": "resource_snapshot", "resourceId": "robot-back"}],
        "provenance": {"origin_subject_id": "original-robot"},
    }})
    selections = []
    for index, resource in enumerate(("robot-front", "robot-back")):
        path = tmp_path / f"{resource}.png"
        path.write_bytes(_p7_png(rgba=bytes((index, 32, 48, 255))))
        selections.append({"asset_id": resource, "node_id": "robot", "resource_id": resource,
                           "path": path, "usage_license": "fixture-only"})
    return source, selections


def test_subject_png_selection_keeps_exact_main_and_auxiliary_resources(tmp_path):
    source, selections = subject_selections(tmp_path)
    registry, artifacts = prepare_canvas_png_assets(packet=source, selections=selections,
                                                   allowed_asset_root=tmp_path)
    assert {a.asset_id for a in registry.assets} == {"robot-front", "robot-back"}
    assert len(artifacts) == 2
    assert len({a.input_fingerprint for a in registry.assets}) == 2
    assert {a.creation_receipt_id.rsplit(":", 1)[1] for a in registry.assets} == {"robot-front", "robot-back"}


@pytest.mark.parametrize("damage", ["omit_aux", "duplicate_main", "wrong_resource", "unknown_ref_type"])
def test_subject_png_selection_rejects_lost_or_changed_bundle_identity(tmp_path, damage):
    source, selections = subject_selections(tmp_path)
    if damage == "omit_aux":
        selections.pop()
    elif damage == "duplicate_main":
        selections[1]["resource_id"] = selections[0]["resource_id"]
    elif damage == "wrong_resource":
        selections[1]["resource_id"] = "unselected-version"
    else:
        source["assets"][-1]["data"]["main"]["refType"] = "live_subject"
    with pytest.raises(ValueError):
        prepare_canvas_png_assets(packet=source, selections=selections, allowed_asset_root=tmp_path)


def generated_selection(tmp_path):
    import hashlib
    import json
    source = tmp_path / "generated.png"
    payload = _p7_png(rgba=b"\x11\x22\x33\xff")
    source.write_bytes(payload)
    record = {"sha256": hashlib.sha256(payload).hexdigest(), "size_bytes": len(payload),
              "width": 2, "height": 1, "status": "PENDING_HUMAN_APPROVAL"}
    evidence = tmp_path / "generation-record.json"
    evidence.write_text(json.dumps(record))
    selection = {"asset_id": "room-reference", "node_id": "room", "resource_id": "room-resource",
        "path": source, "usage_license": "project-owned-synthetic", "generated_source": {
            "record_path": "generation-record.json",
            "record_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
            "tool": {"name": "external-image-tool", "version": "not-recorded"}}}
    return selection, evidence


def test_generated_source_copy_seals_exact_record_without_claiming_acceptance(tmp_path):
    import json
    selection, evidence = generated_selection(tmp_path)
    registry, artifacts = prepare_canvas_png_assets(packet=packet(), selections=[selection],
        allowed_asset_root=tmp_path)
    asset = registry.assets[0]
    assert asset.source_kind.value == "derived"
    assert asset.tool.name == "canvas-generated-image-source"
    assert asset.creation_receipt_id.startswith("canvas-generated-image-source:")
    records = [json.loads(a.payload) for a in artifacts if a.relative_path.suffix == ".json"]
    original = next(r for r in records if r["kind"] == "canvas-generated-source-record/1")
    assert original["record_utf8"].encode() == evidence.read_bytes()
    receipt = next(r for r in records if r["kind"] == "canvas-generated-image-source/1")
    assert receipt["platform_adoption"] == "NOT_EVALUATED"
    assert receipt["platform_bytes_verified"] is False
    assert receipt["generated_source"]["record_sha256"] == selection["generated_source"]["record_sha256"]
    (tmp_path / "project").mkdir()
    service = CanvasProductionService(committer=ProductionStateCommitter(tmp_path / "project"),
        packet=packet(), direction=direction())
    bundle = service.author(registry=registry, asset_artifacts=artifacts)
    bundle.bootstrap(committer=service.committer, attempt_id="generated-copy")
    assert service._load().registry == registry
    assert all((service.committer.project_root / a.relative_path).read_bytes() == a.payload for a in artifacts)
    receipt_artifact = next(a for a in artifacts if a.relative_path.suffix == ".json")
    (service.committer.project_root / receipt_artifact.relative_path).write_bytes(receipt_artifact.payload + b" ")
    with pytest.raises(Exception):
        service._load()


@pytest.mark.parametrize("damage", ["hash", "image", "size", "width", "missing", "symlink", "outside", "unknown"])
def test_generated_source_requires_exact_record_and_containment(tmp_path, damage):
    import hashlib
    import json
    selection, evidence = generated_selection(tmp_path)
    declared = selection["generated_source"]
    if damage == "hash":
        declared["record_sha256"] = "0" * 64
    elif damage in {"image", "size", "width"}:
        data = json.loads(evidence.read_bytes())
        data[{"image": "sha256", "size": "size_bytes", "width": "width"}[damage]] = "0" * 64 if damage == "image" else 7
        evidence.write_text(json.dumps(data))
        declared["record_sha256"] = hashlib.sha256(evidence.read_bytes()).hexdigest()
    elif damage == "missing":
        evidence.unlink()
    elif damage == "symlink":
        link = tmp_path / "record-link.json"
        link.symlink_to(evidence)
        declared["record_path"] = "record-link.json"
    elif damage == "outside":
        declared["record_path"] = "../outside.json"
    else:
        declared["source_kind"] = "generated"
    with pytest.raises((ValueError, OSError)):
        prepare_canvas_png_assets(packet=packet(), selections=[selection], allowed_asset_root=tmp_path)


def test_generated_source_registry_is_eligible_for_existing_synthetic_resolver(tmp_path):
    import hashlib
    import importlib
    from ai_video.production.authoring_input import authoring_input_payload
    from ai_video.production.video import VideoImageReferenceBinding, VideoGenerationMode
    from test_production_seedance import _synthetic_receipt, _synthetic_policy_receipt, _synthetic_evidence_source
    module = importlib.import_module("ai_video.production.seedance_asset")
    selection, _ = generated_selection(tmp_path)
    registry, artifacts = prepare_canvas_png_assets(packet=packet(), selections=[selection],
        allowed_asset_root=tmp_path)
    asset = registry.assets[0]
    png = selection["path"].read_bytes()
    binding = VideoImageReferenceBinding(role="reference", asset_id=asset.asset_id,
        asset_sha256=asset.sha256, size_bytes=asset.size_bytes, width=asset.width,
        height=asset.height, mime_type=asset.mime_type)
    digest = asset.creation_receipt_id.split(":", 1)[1]
    source = next(a.payload for a in artifacts if a.relative_path.name == f"{digest}.json")
    receipt = _synthetic_receipt(module, binding, mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        classification="synthetic_photorealistic_person", registry_revision_id=registry.revision_id,
        permitted_use="project-owned-fictional-no-protected-identity:seedance-r2v",
        source_record_id=asset.creation_receipt_id, source_tool=asset.tool,
        source_evidence_sha256=hashlib.sha256(source).hexdigest())
    child = module.SeedanceSyntheticImageReceiptBinding(role="reference", asset_id=asset.asset_id,
        receipt_content_hash=receipt.content_hash)
    aggregate = _synthetic_policy_receipt(module, child, mode=VideoGenerationMode.REFERENCE_TO_VIDEO)
    resolver = module.SeedanceSyntheticImageReferenceResolver((receipt,), policy_receipt=aggregate,
        image_bytes={asset.asset_id: png}, registry_snapshot_bytes=authoring_input_payload(registry.model_dump(mode="json")),
        evidence_source=_synthetic_evidence_source(module, (receipt,), aggregate,
            source_records={asset.creation_receipt_id: source}))
    assert resolver(binding).startswith("data:image/png;base64,")
