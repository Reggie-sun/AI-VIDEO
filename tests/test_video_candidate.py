"""Production tests for the deterministic video candidate preparer."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_video.production.composition import resolve_composition
from ai_video.production.dependency import (
    asset_node_id,
    composition_node_id,
    renderer_source_node_id,
)
from ai_video.production.models import (
    AssetSourceKind,
    AssetType,
    DependencyReason,
    VideoAssetMetadata,
)
from ai_video.production.video_candidate import make_video_candidate_preparer
from production_project_factory import (
    make_p8_video_generation_base,
)


@pytest.fixture
def candidate_inputs(tmp_path: Path):
    base_inputs = make_p8_video_generation_base(tmp_path, schema_version="2.8")
    base_project = base_inputs.project
    target_shot = base_project.shots[0]
    request = SimpleNamespace(
        activation_scope=SimpleNamespace(
            request=SimpleNamespace(
                target_shot_id=target_shot.shot_id,
                target_asset_role=target_shot.required_asset_roles[0].role,
            )
        ),
        output_asset_id="video-output-t1",
        generation_id="t1-generation",
    )
    provenance = SimpleNamespace(content_hash="a" * 64)
    video_bytes = (
        b"\x00\x00\x00\x14ftypisom\x00\x00\x00\x00isom"
        b"\x00\x00\x00\x08moov"
    )
    video_path = tmp_path / "assets/files/video-output-t1.mp4"
    video_path.parent.mkdir(parents=True, exist_ok=True)
    video_path.write_bytes(video_bytes)
    asset_record = base_project.registry.assets[0].model_copy(
        update={
            "asset_id": request.output_asset_id,
            "asset_type": AssetType.VIDEO,
            "source_kind": AssetSourceKind.GENERATED,
            "artifact_path": Path("assets/files/video-output-t1.mp4"),
            "sha256": hashlib.sha256(video_bytes).hexdigest(),
            "size_bytes": len(video_bytes),
            "mime_type": "video/mp4",
            "duration_seconds": 2.0,
            "width": 1280,
            "height": 720,
            "input_fingerprint": "e" * 64,
            "video_metadata": VideoAssetMetadata(
                container_name="mp4",
                codec_name="h264",
                width=1280,
                height=720,
                fps_numerator=24,
                fps_denominator=1,
                duration_milliseconds=60_000,
                frame_count=1_440,
                probe_receipt_id="probe-t1",
                request_receipt_fingerprint="d" * 64,
                resolved_generation_hash="e" * 64,
                provenance_receipt_id="provenance-t1",
            ),
        }
    )
    continuity_asset_record = base_project.registry.assets[0].model_copy(
        update={
            "asset_id": f"{request.output_asset_id}:terminal-frame",
            "artifact_path": Path("assets/files/video-output-t1-terminal.png"),
            "sha256": "c" * 64,
        }
    )
    return (
        base_inputs,
        base_project,
        request,
        provenance,
        asset_record,
        continuity_asset_record,
    )


@pytest.mark.parametrize("with_continuity", (False, True))
def test_production_preparer_builds_deterministic_candidate_contract(
    candidate_inputs,
    with_continuity: bool,
) -> None:
    (
        base_inputs,
        base_project,
        request,
        provenance,
        asset_record,
        continuity_asset_record,
    ) = candidate_inputs
    continuity = continuity_asset_record if with_continuity else None
    args = (
        base_project,
        request,
        None,
        None,
        provenance,
        asset_record,
        continuity,
    )

    prepared = make_video_candidate_preparer(base_inputs)(*args)
    assert prepared.base_inputs.project == base_project
    assert prepared.candidate_project.manifest.active_project is not None
    assert prepared.candidate_project.manifest.active_registry is not None
    assert prepared.candidate_project.manifest.active_dependency_graph is not None
    assert (
        prepared.candidate_project_pointer.file_sha256
        == hashlib.sha256(prepared.candidate_project_bytes).hexdigest()
    )
    assert (
        prepared.candidate_registry_pointer.file_sha256
        == hashlib.sha256(prepared.candidate_registry_bytes).hexdigest()
    )
    assert (
        prepared.candidate_graph_pointer.file_sha256
        == hashlib.sha256(prepared.candidate_graph_bytes).hexdigest()
    )
    expected_asset_ids = {asset_record.asset_id}
    if continuity is not None:
        expected_asset_ids.add(continuity.asset_id)
    assert expected_asset_ids.issubset(prepared.candidate_project.asset_paths)
    target_shot_id = request.activation_scope.request.target_shot_id
    target_role = request.activation_scope.request.target_asset_role
    candidate_layers = tuple(
        layer
        for layer in prepared.candidate_inputs.composition_spec.layers
        if layer.shot_id == target_shot_id and layer.asset_role == target_role
    )
    assert len(candidate_layers) == 1
    assert candidate_layers[0].asset_id == request.output_asset_id
    timeline = resolve_composition(
        prepared.candidate_project,
        prepared.candidate_inputs.composition_spec,
        prepared.candidate_inputs.renderer.version,
    )
    assert next(
        span for span in timeline.visual_spans if span.shot_id == target_shot_id
    ).asset_id == request.output_asset_id
    graph_edges = {
        (edge.source_node_id, edge.target_node_id, edge.reason)
        for edge in prepared.candidate_graph.edges
    }
    composition = composition_node_id(
        prepared.candidate_inputs.composition_spec.composition_id
    )
    source = renderer_source_node_id(
        prepared.candidate_inputs.composition_spec.composition_id
    )
    output = asset_node_id(request.output_asset_id)
    assert (output, composition, DependencyReason.ASSET_BINDING) in graph_edges
    assert (output, source, DependencyReason.ASSET_BINDING) in graph_edges


def test_test_factory_compatibility_name_delegates_to_production_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ai_video.production.video_candidate as candidate_module
    from production_project_factory import make_p8_video_candidate_preparer

    sentinel = object()
    monkeypatch.setattr(
        candidate_module,
        "make_video_candidate_preparer",
        lambda base_inputs: sentinel if base_inputs == "inputs" else None,
    )

    assert make_p8_video_candidate_preparer("inputs") is sentinel


def test_preparer_is_write_free_and_requires_activation_scope(
    candidate_inputs,
) -> None:
    base_inputs, base_project, request, provenance, asset_record, _ = candidate_inputs
    before = base_project.model_dump(mode="json")
    request.activation_scope = None

    with pytest.raises(ValueError, match="activation_scope"):
        make_video_candidate_preparer(base_inputs)(
            base_project,
            request,
            None,
            None,
            provenance,
            asset_record,
        )

    assert base_project.model_dump(mode="json") == before
