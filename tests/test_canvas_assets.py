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
