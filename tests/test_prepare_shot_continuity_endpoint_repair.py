from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from ai_video.errors import AiVideoError
from ai_video.production.image_import import HumanImageImportReceipt
from ai_video.production.paths import canonical_human_image_import_receipt_path
from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_source_runtime import build_source_closure
from scripts.prepare_shot_continuity_p0 import prepare as prepare_p0


SOURCE_REFERENCE_SHOT_ARTIFACT_IDS = (
    "shot-rainy-station-2",
    "shot-rainy-station-3",
)


def _input_image(root: Path, name: str, color: tuple[int, int, int]) -> Path:
    directory = root / name
    directory.mkdir(parents=True)
    path = directory / f"{name}.png"
    Image.new("RGB", (1659, 948), color).save(path)
    (directory / "metadata.json").write_text(
        json.dumps(
            {
                "backend": "chatgpt-web",
                "mode": "direct-typescript-browser",
                "prompt": f"rainy-station-{name}",
                "created_at": "2026-08-23T01:00:00+08:00",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _prepare_source_root(tmp_path: Path, name: str = "source") -> Path:
    inputs = tmp_path / "inputs"
    images = tuple(
        _input_image(inputs, f"a{index}", (index * 20, index * 30, index * 40))
        for index in range(1, 5)
    )
    source_root = tmp_path / name
    prepare_p0(
        argparse.Namespace(
            root=source_root,
            a1=images[0],
            a2=images[1],
            a3=images[2],
            a4=images[3],
            approved_at="2026-08-23T01:10:00+08:00",
            imported_at="2026-08-23T01:20:00+08:00",
        )
    )
    return source_root


def _run_repair(
    *,
    source_root: Path,
    target_root: Path,
    candidate: Path,
    prompt_fingerprint: str = "3" * 64,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (
            sys.executable,
            "scripts/prepare_shot_continuity_endpoint_repair.py",
            "--source-root",
            str(source_root),
            "--root",
            str(target_root),
            "--a3",
            str(candidate),
            "--prompt-fingerprint",
            prompt_fingerprint,
            "--imported-at",
            "2026-08-25T20:43:02+08:00",
            "--approved-at",
            "2026-08-25T20:52:24+08:00",
        ),
        check=False,
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
    )


def _endpoint_asset_id(shot) -> str:
    role = next(item for item in shot.required_asset_roles if item.role == "approved_endpoint")
    assert len(role.asset_ids) == 1
    return role.asset_ids[0]


def _tree_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_endpoint_repair_clones_creative_bundle_and_changes_only_a3(tmp_path: Path) -> None:
    source_root = _prepare_source_root(tmp_path)
    source = load_production_project(source_root / "project.yaml")
    source_tree_before = _tree_snapshot(source_root)

    candidate = tmp_path / "approved-motion-endpoint.png"
    Image.new("RGB", (1659, 948), (90, 100, 110)).save(candidate)
    candidate_bytes = candidate.read_bytes()
    target_root = tmp_path / "target"
    prompt_fingerprint = "3" * 64

    completed = _run_repair(
        source_root=source_root,
        target_root=target_root,
        candidate=candidate,
        prompt_fingerprint=prompt_fingerprint,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    repaired = load_production_project(target_root / "project.yaml")
    source_shots_by_id = {shot.artifact_id: shot for shot in source.shots}
    repaired_shots_by_id = {shot.artifact_id: shot for shot in repaired.shots}

    assert _tree_snapshot(source_root) == source_tree_before
    assert repaired.project.revision == source.project.revision + 1
    assert repaired.manifest.schema_version == "2.11"
    assert repaired.manifest.active_dependency_graph is not None
    assert not any(
        attempt.operation == "video_generation"
        for attempt in repaired.manifest.attempts
    )
    assert all(
        repaired_shots_by_id[artifact_id].content_hash
        == source_shots_by_id[artifact_id].content_hash
        for artifact_id in (
            "shot-rainy-station-1",
            "shot-rainy-station-2",
            "shot-rainy-station-4",
        )
    )
    assert repaired.brief == source.brief
    assert repaired.story == source.story
    assert repaired.storyboard == source.storyboard
    assert repaired.characters == source.characters
    assert repaired.scenes == source.scenes
    assert (
        repaired_shots_by_id["shot-rainy-station-3"].revision
        == source_shots_by_id["shot-rainy-station-3"].revision + 1
    )
    assert (
        repaired_shots_by_id["shot-rainy-station-3"].content_hash
        != source_shots_by_id["shot-rainy-station-3"].content_hash
    )
    assert len(repaired.registry.assets) == len(source.registry.assets) + 1
    endpoint_asset_id = _endpoint_asset_id(
        repaired_shots_by_id["shot-rainy-station-3"]
    )
    endpoint_asset = next(
        item for item in repaired.registry.assets if item.asset_id == endpoint_asset_id
    )
    assert endpoint_asset.sha256 == hashlib.sha256(candidate_bytes).hexdigest()
    assert endpoint_asset.tool.name == "codex-imagegen-import"
    assert endpoint_asset.input_fingerprint == prompt_fingerprint
    receipt = HumanImageImportReceipt.model_validate_json(
        (
            target_root
            / canonical_human_image_import_receipt_path(
                endpoint_asset.creation_receipt_id
            )
        ).read_bytes()
    )
    assert tuple(
        (
            reference.role,
            reference.creative_artifact_id,
            reference.creative_revision,
            reference.creative_content_hash,
            reference.asset_id,
            reference.asset_sha256,
        )
        for reference in receipt.references
    ) == tuple(
        (
            "shot_endpoint",
            shot.artifact_id,
            shot.revision,
            shot.content_hash,
            _endpoint_asset_id(shot),
            next(
                asset.sha256
                for asset in source.registry.assets
                if asset.asset_id == _endpoint_asset_id(shot)
            ),
        )
        for shot in (
            source_shots_by_id[artifact_id]
            for artifact_id in SOURCE_REFERENCE_SHOT_ARTIFACT_IDS
        )
    )
    assert endpoint_asset.input_artifact_ids == tuple(
        identity
        for shot in (
            source_shots_by_id[artifact_id]
            for artifact_id in SOURCE_REFERENCE_SHOT_ARTIFACT_IDS
        )
        for identity in (shot.artifact_id, _endpoint_asset_id(shot))
    )
    closure = build_source_closure(repaired)
    assert repaired.dependency_graph == closure.graph
    assert repaired.manifest.active_dependency_graph is not None
    assert (
        repaired.manifest.active_dependency_graph.content_hash
        == closure.graph.content_hash
    )
    target_layer = next(
        layer
        for layer in closure.inputs.composition_spec.layers
        if layer.shot_id == "rainy-station-3"
    )
    assert target_layer.asset_id == endpoint_asset.asset_id
    source_a3_reference = receipt.references[1]
    referenced_shot_path = target_root / source_a3_reference.creative_artifact_path
    referenced_shot_bytes = referenced_shot_path.read_bytes()
    referenced_shot_path.write_bytes(referenced_shot_bytes + b"\n")
    with pytest.raises(AiVideoError):
        load_production_project(target_root / "project.yaml")
    referenced_shot_path.write_bytes(referenced_shot_bytes)
    assert load_production_project(target_root / "project.yaml") == repaired
    assert result["claims"] == {
        "final_acceptance": False,
        "p6_pass": False,
        "video_generated": False,
        "winner_selected": False,
    }


def test_endpoint_repair_output_can_be_repaired_again(tmp_path: Path) -> None:
    source_root = _prepare_source_root(tmp_path)
    first_candidate = tmp_path / "first-approved-endpoint.png"
    Image.new("RGB", (1659, 948), (90, 100, 110)).save(first_candidate)
    first_target = tmp_path / "first-target"
    first = _run_repair(
        source_root=source_root,
        target_root=first_target,
        candidate=first_candidate,
    )
    assert first.returncode == 0, first.stderr
    first_manifest_before = (first_target / "state/manifest.json").read_bytes()

    second_candidate = tmp_path / "second-approved-endpoint.png"
    Image.new("RGB", (1659, 948), (120, 130, 140)).save(second_candidate)
    second_target = tmp_path / "second-target"
    second = _run_repair(
        source_root=first_target,
        target_root=second_target,
        candidate=second_candidate,
        prompt_fingerprint="4" * 64,
    )

    assert second.returncode == 0, second.stderr
    assert (first_target / "state/manifest.json").read_bytes() == first_manifest_before
    twice_repaired = load_production_project(second_target / "project.yaml")
    assert twice_repaired.project.revision == 3
    assert twice_repaired.shots[2].revision == 3


def test_endpoint_repair_rejects_target_nested_inside_source(tmp_path: Path) -> None:
    source_root = _prepare_source_root(tmp_path)
    candidate = tmp_path / "approved-endpoint.png"
    Image.new("RGB", (1659, 948), (90, 100, 110)).save(candidate)
    nested_target = source_root / "nested-target"

    completed = _run_repair(
        source_root=source_root,
        target_root=nested_target,
        candidate=candidate,
    )

    assert completed.returncode != 0
    assert not nested_target.exists()
