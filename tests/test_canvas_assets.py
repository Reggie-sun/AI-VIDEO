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


def local_video_packet():
    from scripts.canvas_sequence_packet import build_sequence_packet

    graph = {"nodes": [
        {"id": "target", "type": "video", "data": {"resourceId": "target-output",
            "generationDraft": {"parts": [
                {"type": "text", "text": "固定机位，演员举手停在玻璃前。"},
                {"type": "extension", "extension_type": "node", "object_id": "guide-slot"}],
                "contentSettings": {"resolution": "720p", "durationSeconds": 4},
                "references": [{"slotId": "guide-slot", "nodeId": "guide",
                    "role": "reference", "type": "extension", "extensionType": "node"}]}}},
        {"id": "guide", "type": "video", "data": {"resourceId": "guide-resource",
            "title": "S01 white model"}},
    ], "edges": [{"id": "guide-target", "source": "guide", "target": "target",
        "type": "reference"}]}
    return build_sequence_packet(graph, {"node_ids": ["target"]})


def local_video_selection(tmp_path):
    source = tmp_path / "guide.mp4"
    source.write_bytes(b"test-only-mp4-bytes")
    return {"asset_id": "guide-video", "node_id": "guide", "resource_id": "guide-resource",
        "path": source, "usage_license": "project-owned-white-model-reference",
        "tool": {"name": "blender", "version": "4.5.3"},
        "input_artifact_ids": ("blend-sha256:" + "a" * 64,)}


def fake_local_video_probe(monkeypatch):
    import ai_video.canvas_video_assets as video_assets

    def measured(payload, ffprobe_executable):
        from ai_video.production.hashing import canonical_sha256
        import hashlib
        values = {
        "container_name": "mp4", "codec_name": "h264", "width": 960, "height": 540,
        "fps_numerator": 24, "fps_denominator": 1, "duration_milliseconds": 4000,
        "frame_count": 96, "ffprobe_sha256": "b" * 64,
        "probe_config_sha256": "c" * 64, "measurement_sha256": "d" * 64,
        }
        fields = {key: values[key] for key in ("container_name", "codec_name", "width", "height",
            "fps_numerator", "fps_denominator", "duration_milliseconds", "frame_count")}
        values["measurement_sha256"] = canonical_sha256({"kind": "canvas-local-video-measurement/1",
            "input_sha256": hashlib.sha256(payload).hexdigest(), "input_size_bytes": len(payload),
            "ffprobe_sha256": values["ffprobe_sha256"], "probe_config_sha256": values["probe_config_sha256"],
            "measured": fields})
        return values
    monkeypatch.setattr(video_assets, "_probe_canvas_mp4", measured)
    return video_assets.prepare_canvas_video_assets


def test_video_selection_measures_exact_local_bytes_and_emits_import_provenance(tmp_path, monkeypatch):
    prepare = fake_local_video_probe(monkeypatch)
    selection = local_video_selection(tmp_path)
    registry, artifacts = prepare(packet=local_video_packet(), selections=[selection],
        allowed_asset_root=tmp_path, ffprobe_executable="/usr/bin/ffprobe")

    asset = registry.assets[0]
    assert asset.asset_type.value == "video"
    assert asset.mime_type == "video/mp4"
    assert asset.video_metadata.width == 960 and asset.video_metadata.height == 540
    assert asset.video_metadata.frame_count == 96
    assert asset.video_metadata.fps_numerator == 24 and asset.video_metadata.fps_denominator == 1
    assert asset.tool.name == "blender" and asset.tool.version == "4.5.3"
    assert asset.creation_receipt_id.startswith("canvas-local-video-selection:")
    assert type(registry).model_validate_json(registry.model_dump_json()) == registry
    assert len(artifacts) == 2
    media = next(a for a in artifacts if a.relative_path.suffix == ".mp4")
    receipt = next(a for a in artifacts if a.relative_path.suffix == ".json")
    assert media.payload == selection["path"].read_bytes()
    assert receipt.relative_path.as_posix().startswith("evidence/authoring-input/")
    assert b"canvas-local-video-selection/1" in receipt.payload
    assert b'"provider_generation":"NOT_CLAIMED"' in receipt.payload


@pytest.mark.parametrize("damage", ["node", "resource", "symlink", "outside", "duplicate", "duration", "fps"])
def test_video_selection_rejects_wrong_identity_or_unbounded_mp4(tmp_path, monkeypatch, damage):
    prepare = fake_local_video_probe(monkeypatch)
    packet_value = local_video_packet()
    selection = local_video_selection(tmp_path)
    root = tmp_path
    if damage == "node":
        selection["node_id"] = "target"
    elif damage == "resource":
        selection["resource_id"] = "other-resource"
    elif damage == "symlink":
        link = tmp_path / "link.mp4"
        link.symlink_to(selection["path"])
        selection["path"] = link
    elif damage == "outside":
        root = tmp_path / "allowed"
        root.mkdir()
    elif damage == "duration":
        import ai_video.canvas_video_assets as video_assets
        monkeypatch.setattr(video_assets, "_probe_canvas_mp4", lambda *_: {
            "container_name": "mp4", "codec_name": "h264", "width": 960, "height": 540,
            "fps_numerator": 24, "fps_denominator": 1, "duration_milliseconds": 16000,
            "frame_count": 384, "ffprobe_sha256": "b" * 64, "probe_config_sha256": "c" * 64,
            "measurement_sha256": "d" * 64})
    elif damage == "fps":
        import ai_video.canvas_video_assets as video_assets
        monkeypatch.setattr(video_assets, "_probe_canvas_mp4", lambda *_: {
            "container_name": "mp4", "codec_name": "h264", "width": 960, "height": 540,
            "fps_numerator": 24000, "fps_denominator": 1001, "duration_milliseconds": 4000,
            "frame_count": 96, "ffprobe_sha256": "b" * 64, "probe_config_sha256": "c" * 64,
            "measurement_sha256": "d" * 64})
    selections = [selection, selection] if damage == "duplicate" else [selection]
    with pytest.raises((ValueError, OSError)):
        prepare(packet=packet_value, selections=selections, allowed_asset_root=root,
            ffprobe_executable="/usr/bin/ffprobe")


@pytest.mark.parametrize("damage", [None, "network_container", "multiple_video", "fractional_fps", "duration"])
def test_local_video_probe_is_file_only_and_requires_measured_mp4(tmp_path, monkeypatch, damage):
    import json
    import os
    from types import SimpleNamespace
    import ai_video.canvas_video_assets as module

    executable = tmp_path / "ffprobe"
    executable.write_bytes(b"test-only-probe-identity")
    stream = {"codec_type": "video", "codec_name": "h264", "width": 768, "height": 1344,
        "avg_frame_rate": "48/2", "nb_frames": "96"}
    document = {"format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "4.000"},
        "streams": [stream]}
    if damage == "network_container": document["format"]["format_name"] = "hls"
    elif damage == "multiple_video": document["streams"].append(dict(stream))
    elif damage == "fractional_fps": stream["avg_frame_rate"] = "24000/1001"
    elif damage == "duration": document["format"]["duration"] = "16.000"

    def run(arguments, **kwargs):
        assert arguments[1:11] == ("-v", "error", "-protocol_whitelist", "file",
            "-f", "mov", "-enable_drefs", "0", "-use_absolute_path", "0")
        assert kwargs == {"check": True, "capture_output": True, "timeout": 45,
            "pass_fds": (int(arguments[0].rsplit("/", 1)[1]),)}
        assert os.pread(kwargs["pass_fds"][0], 100, 0) == executable.read_bytes()
        assert module.Path(arguments[-1]).read_bytes() == b"exact-selected-video"
        return SimpleNamespace(stdout=json.dumps(document).encode())

    monkeypatch.setattr(module.subprocess, "run", run)
    if damage:
        with pytest.raises(ValueError): module._probe_canvas_mp4(b"exact-selected-video", executable)
    else:
        measured = module._probe_canvas_mp4(b"exact-selected-video", executable)
        assert (measured["fps_numerator"], measured["fps_denominator"]) == (24, 1)
        assert measured["duration_milliseconds"] == 4000
