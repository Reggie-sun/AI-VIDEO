from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import AssetRoleRequirement, AssetSourceKind, AssetType, VisualStrategy
from ai_video.production.paths import canonical_video_fetch_artifact_path
from ai_video.production.project import load_production_project
from ai_video.production.repair_input_admission import repair_input_receipt_path, verify_repair_input
from ai_video.production.validation import validate_project_references, validate_shot_strategy
from ai_video.production.video_cleanup_contracts import (
    CleanPlateFrame,
    CleanPlatePatch,
    VideoCleanupPlan,
)
from ai_video.production.video_cleanup_media import (
    CleanupFrameProof,
    PreparedVideoCleanup,
    VideoCleanupReceipt,
)
from ai_video.production.video_cleanup_admission import CleanedRepairInputAdmissionReceipt
from test_repair_input_admission import _files, _inputs, _preview_arguments


_CLEANED_BYTES = b"cleaned-fixture-video"


def _plan(source_sha256: str) -> VideoCleanupPlan:
    return VideoCleanupPlan(
        contract_version="video-clean-plate/1",
        source_sha256=source_sha256,
        frames=(
            CleanPlateFrame(
                frame_index=1,
                patches=(
                    CleanPlatePatch(
                        plate_frame=0,
                        polygons=(((8, 8), (20, 8), (20, 20), (8, 20)),),
                    ),
                ),
            ),
        ),
    )


def _prepared_cleanup(plan: VideoCleanupPlan, probe) -> PreparedVideoCleanup:
    source = probe.measured
    output_sha256 = hashlib.sha256(_CLEANED_BYTES).hexdigest()
    output = source.model_copy(
        update={"artifact_sha256": output_sha256, "size_bytes": len(_CLEANED_BYTES)}
    )
    proofs = tuple(
        CleanupFrameProof(
            input_rgb_sha256=hashlib.sha256(f"input:{index}".encode()).hexdigest(),
            output_rgb_sha256=hashlib.sha256(
                (f"output:{index}" if index == 1 else f"input:{index}").encode()
            ).hexdigest(),
            effective_mask_sha256=hashlib.sha256(f"mask:{index}".encode()).hexdigest(),
            protected_rgb_sha256=hashlib.sha256(f"protected:{index}".encode()).hexdigest(),
            changed_pixel_count=5 if index == 1 else 0,
            protected_pixel_changes=0,
        )
        for index in range(source.frame_count)
    )
    frame_times = tuple(round(index * 1_000_000 / 24) for index in range(source.frame_count))
    audio_hash = "b" * 64 if source.audio_stream_count else None
    audio_signature = (
        {
            "codec_name": "aac",
            "sample_rate": 32000,
            "channels": 2,
            "time_base": "1/32000",
            "start_pts": 0,
            "duration_ts": 64000,
        }
        if source.audio_stream_count
        else None
    )
    receipt_values = {
        "plan": plan,
        "source": source,
        "output": output,
        "ffmpeg_sha256": "c" * 64,
        "ffprobe_sha256": "d" * 64,
        "source_frame_times": frame_times,
        "output_frame_times": frame_times,
        "input_audio_sha256": audio_hash,
        "output_audio_sha256": audio_hash,
        "input_audio_signature": audio_signature,
        "output_audio_signature": audio_signature,
        "frame_proofs": proofs,
        "content_hash": "0" * 64,
    }
    provisional = VideoCleanupReceipt.model_construct(**receipt_values)
    receipt = VideoCleanupReceipt.model_validate(
        {
            **provisional.model_dump(mode="json"),
            "content_hash": canonical_sha256(provisional),
        }
    )
    return PreparedVideoCleanup(media_bytes=_CLEANED_BYTES, receipt=receipt)


def _case(tmp_path, monkeypatch):
    source_root, target, writer, args = _inputs(
        tmp_path, close=True, abandon=True
    )
    preview_use, preview_probe, shot = _preview_arguments(source_root, args)
    plan = _plan(args["source_sha256"])
    prepared = _prepared_cleanup(plan, preview_probe)
    processor = Mock(return_value=prepared)
    from ai_video.production import video_cleanup_admission

    monkeypatch.setattr(video_cleanup_admission, "prepare_video_cleanup", processor)
    cleanup_tools = object()
    bootstrap_args = {
        **args,
        "preview_use": preview_use,
        "preview_probe": preview_probe,
        "cleanup_plan": plan,
        "cleanup_tools": cleanup_tools,
    }
    return source_root, target, writer, args, shot, plan, prepared, processor, bootstrap_args


def test_cleaned_admission_reopens_both_lineages_unbound_and_replays_without_writes(
    tmp_path, monkeypatch
):
    source_root, target, writer, args, _, plan, prepared, processor, bootstrap_args = _case(
        tmp_path, monkeypatch
    )
    original_files = _files(source_root)

    manifest = writer.bootstrap_repair_input(**bootstrap_args)
    loaded = load_production_project(target / "project.yaml")
    source_asset = next(asset for asset in loaded.registry.assets if asset.asset_id == "failed-source-source")
    output_asset = next(asset for asset in loaded.registry.assets if asset.asset_id == "failed-source")
    receipt = verify_repair_input(output_asset, target)

    assert isinstance(receipt, CleanedRepairInputAdmissionReceipt)
    assert receipt.contract_version == "development-repair-input/4"
    assert receipt.qualification == "NOT_EVALUATED"
    assert receipt.cleanup == prepared.receipt
    assert receipt.cleanup.plan == plan
    assert receipt.cleanup.content_hash == canonical_sha256(receipt.cleanup)
    assert source_asset.source_kind is AssetSourceKind.IMPORTED
    assert source_asset.sha256 == args["source_sha256"]
    original_measurement = receipt.preview_probe.measured
    for field in (
        "container_name",
        "codec_name",
        "width",
        "height",
        "fps_numerator",
        "fps_denominator",
        "duration_milliseconds",
        "frame_count",
    ):
        assert getattr(source_asset.video_metadata, field) == getattr(original_measurement, field)
    assert source_asset.video_metadata.probe_receipt_id == receipt.preview_probe.content_hash
    assert source_asset.video_metadata.provenance_receipt_id == source_asset.creation_receipt_id
    assert (target / loaded.asset_paths[source_asset.asset_id]).read_bytes() == (
        source_root / canonical_video_fetch_artifact_path(args["source_sha256"])
    ).read_bytes()
    assert output_asset.source_kind is AssetSourceKind.DERIVED
    assert output_asset.sha256 == prepared.receipt.output.artifact_sha256
    assert output_asset.input_artifact_ids == (source_asset.asset_id,)
    assert output_asset.input_fingerprint == receipt.content_hash
    assert (target / loaded.asset_paths[output_asset.asset_id]).read_bytes() == _CLEANED_BYTES
    assert output_asset.size_bytes == len(_CLEANED_BYTES)
    for field in (
        "container_name",
        "codec_name",
        "width",
        "height",
        "fps_numerator",
        "fps_denominator",
        "duration_milliseconds",
        "frame_count",
    ):
        assert getattr(output_asset.video_metadata, field) == getattr(
            prepared.receipt.output, field
        )
    assert prepared.receipt.source.audio_stream_count == original_measurement.audio_stream_count
    assert prepared.receipt.output.audio_stream_count == original_measurement.audio_stream_count
    assert output_asset.duration_seconds == prepared.receipt.output.duration_milliseconds / 1000
    assert output_asset.video_metadata.probe_receipt_id == prepared.receipt.content_hash
    assert output_asset.video_metadata.request_receipt_fingerprint == (
        receipt.preview_probe.request_receipt_fingerprint
    )
    assert output_asset.video_metadata.resolved_generation_hash == (
        receipt.preview_probe.resolved_generation_hash
    )
    assert output_asset.video_metadata.provenance_receipt_id == receipt.content_hash
    assert loaded.manifest == manifest
    assert loaded.manifest.attempts == ()
    assert loaded.manifest.imported_generation_experiences == ()
    assert loaded.manifest.active_paid_provider_budget is None
    assert loaded.qa_policy is None
    assert not any(
        asset.asset_id in role.asset_ids
        for shot in loaded.shots
        for role in shot.required_asset_roles
        for asset in (source_asset, output_asset)
    )
    assert _files(source_root) == original_files
    assert processor.call_count == 1
    assert processor.call_args.kwargs["plan"] == plan
    assert processor.call_args.kwargs["source_bytes"] == (
        source_root / canonical_video_fetch_artifact_path(args["source_sha256"])
    ).read_bytes()

    target_files = _files(target)
    replayed = writer.bootstrap_repair_input(**bootstrap_args)
    assert replayed == manifest
    assert _files(target) == target_files
    assert _files(source_root) == original_files
    assert processor.call_count == 2


@pytest.mark.parametrize("corruption", ["source_bytes", "output_bytes", "recipe", "proof"])
def test_cleaned_admission_strict_reader_rejects_source_output_recipe_and_proof_tamper(
    tmp_path, monkeypatch, corruption
):
    _, target, writer, _, _, _, _, _, bootstrap_args = _case(tmp_path, monkeypatch)
    writer.bootstrap_repair_input(**bootstrap_args)
    loaded = load_production_project(target / "project.yaml")
    source_asset = next(asset for asset in loaded.registry.assets if asset.asset_id == "failed-source-source")
    output_asset = next(asset for asset in loaded.registry.assets if asset.asset_id == "failed-source")

    if corruption in {"source_bytes", "output_bytes"}:
        asset = source_asset if corruption == "source_bytes" else output_asset
        (target / loaded.asset_paths[asset.asset_id]).write_bytes(b"tampered-media")
    else:
        receipt_path = target / repair_input_receipt_path(output_asset.creation_receipt_id)
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
        if corruption == "recipe":
            payload["cleanup"]["plan"]["frames"][0]["frame_index"] = 2
        else:
            payload["cleanup"]["frame_proofs"][1]["protected_pixel_changes"] = 1
        receipt_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(AiVideoError):
        load_production_project(target / "project.yaml")


def test_cleaned_admission_rejects_a_missing_original_registry_source(tmp_path, monkeypatch):
    _, target, writer, _, _, _, _, _, bootstrap_args = _case(tmp_path, monkeypatch)
    writer.bootstrap_repair_input(**bootstrap_args)
    loaded = load_production_project(target / "project.yaml")
    source_id = "failed-source-source"
    registry_without_source = loaded.registry.model_copy(
        update={
            "assets": tuple(
                asset for asset in loaded.registry.assets if asset.asset_id != source_id
            )
        }
    )

    with pytest.raises(AiVideoError, match="original Registry source"):
        validate_project_references(loaded.model_copy(update={"registry": registry_without_source}))


def test_cleaned_preview_cannot_be_bound_or_used_as_a_production_render_source(
    tmp_path, monkeypatch
):
    _, target, writer, _, _, _, _, _, bootstrap_args = _case(tmp_path, monkeypatch)
    writer.bootstrap_repair_input(**bootstrap_args)
    loaded = load_production_project(target / "project.yaml")
    output_asset = next(asset for asset in loaded.registry.assets if asset.asset_id == "failed-source")
    shot = loaded.shots[0]
    bound = seal_artifact(
        shot.model_copy(
            update={
                "visual_strategy": VisualStrategy.EXISTING_VIDEO,
                "required_asset_roles": (
                    AssetRoleRequirement(
                        role="final_visual",
                        asset_ids=(output_asset.asset_id,),
                        allowed_asset_types=(AssetType.VIDEO,),
                    ),
                ),
            }
        )
    )

    with pytest.raises(AiVideoError, match="cannot be bound for Production"):
        validate_shot_strategy(bound, {asset.asset_id: asset for asset in loaded.registry.assets})

    from ai_video.production.repair_input_admission import require_production_render_sources

    timeline = SimpleNamespace(
        visual_spans=(SimpleNamespace(asset_sha256=output_asset.sha256),)
    )
    with pytest.raises(ValueError, match="cannot be activated for Production"):
        require_production_render_sources(target, loaded.manifest.active_registry, timeline)


def test_cleanup_failure_and_invalid_target_binding_write_nothing_and_skip_adapter(
    tmp_path, monkeypatch
):
    source_root, target, writer, args = _inputs(tmp_path, close=True, abandon=True)
    preview_use, preview_probe, _ = _preview_arguments(source_root, args)
    plan = _plan(args["source_sha256"])
    from ai_video.production import video_cleanup_admission

    processor = Mock(side_effect=ValueError("synthetic media failure"))
    monkeypatch.setattr(video_cleanup_admission, "prepare_video_cleanup", processor)
    bootstrap_args = {
        **args,
        "preview_use": preview_use,
        "preview_probe": preview_probe,
        "cleanup_plan": plan,
        "cleanup_tools": object(),
    }
    source_files = _files(source_root)

    with pytest.raises(AiVideoError):
        writer.bootstrap_repair_input(**bootstrap_args)
    assert _files(target) == {}
    assert _files(source_root) == source_files
    assert processor.call_count == 1

    processor.reset_mock()
    invalid_binding = {**bootstrap_args, "preview_use": {**preview_use, "shot_id": "other-shot"}}
    with pytest.raises(AiVideoError):
        writer.bootstrap_repair_input(**invalid_binding)
    assert processor.call_count == 0
    assert _files(target) == {}
    assert _files(source_root) == source_files


def _viewing_case(tmp_path, monkeypatch):
    from ai_video.production import video_cleanup_viewing_admission
    from ai_video.production.video_cleanup_viewing import CleanupViewingProxyReceipt, PreparedCleanupViewingProxy

    case = _case(tmp_path, monkeypatch)
    cleaned = case[6].receipt
    raw = b"browser-compatible-viewing-fixture"
    values = dict(source=cleaned.output, output=cleaned.output.model_copy(update={
        "artifact_sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}),
        source_pixel_format="gbrp", ffmpeg_sha256="c" * 64, ffprobe_sha256="d" * 64,
        source_frame_times=cleaned.output_frame_times, output_frame_times=cleaned.output_frame_times,
        input_audio_sha256=cleaned.output_audio_sha256, output_audio_sha256=cleaned.output_audio_sha256,
        input_audio_signature=cleaned.output_audio_signature, output_audio_signature=cleaned.output_audio_signature)
    provisional = CleanupViewingProxyReceipt.model_construct(**values, content_hash="0" * 64)
    receipt = CleanupViewingProxyReceipt.model_validate({**provisional.model_dump(mode="python"),
        "content_hash": canonical_sha256(provisional)})
    processor = Mock(return_value=PreparedCleanupViewingProxy(raw, receipt))
    monkeypatch.setattr(video_cleanup_viewing_admission, "prepare_cleanup_viewing_proxy", processor)
    arguments = {**case[-1], "cleanup_viewing_proxy": True}
    return case, processor, arguments


def test_viewing_admission_keeps_raw_master_proxy_unbound_and_projects_the_actual_viewing_asset(tmp_path, monkeypatch):
    from ai_video import provider_console
    from ai_video.production.repair_input_admission import require_production_render_sources

    case, processor, arguments = _viewing_case(tmp_path, monkeypatch)
    source_root, target, writer = case[:3]
    before_source = _files(source_root)
    writer.bootstrap_repair_input(**arguments)
    loaded = load_production_project(target / "project.yaml")
    assets = {item.asset_id: item for item in loaded.registry.assets}
    master, view = assets["failed-source"], assets["failed-source-viewing"]
    admission = verify_repair_input(view, target)
    assert admission.contract_version == "development-repair-input/5"
    assert admission.master_asset == master
    assert admission.source_asset == assets["failed-source-source"]
    assert admission.viewing.source == verify_repair_input(master, target).cleanup.output
    assert view.input_artifact_ids == (master.asset_id,)
    assert view.tool.version == "5"
    assert admission.qualification == "NOT_EVALUATED"
    assert loaded.manifest.attempts == () and loaded.qa_policy is None
    assert _files(source_root) == before_source
    snapshot = _files(target)
    writer.bootstrap_repair_input(**arguments)
    assert _files(target) == snapshot and processor.call_count == 2

    projected = provider_console.project_workspace_detail(target.parent, target.name + "/project.yaml")
    viewing_media = next(item for item in projected["workspace_media"] if item["sha256"] == view.sha256)
    assert projected["status"] == "valid"
    assert viewing_media["source_kind"] == "viewing_proxy"
    assert viewing_media["source_master_sha256"] == master.sha256
    assert any(item.get("source_kind") == "cleanup_master" for item in projected["workspace_media"])
    assert str(tmp_path) not in json.dumps({key: value for key, value in projected.items() if key != "_media"})
    with pytest.raises(ValueError, match="cannot be activated for Production"):
        require_production_render_sources(target, loaded.manifest.active_registry,
            SimpleNamespace(visual_spans=(SimpleNamespace(asset_sha256=view.sha256),)))
    registry = loaded.registry.model_copy(update={"assets": tuple(item for item in loaded.registry.assets if item != master)})
    with pytest.raises(AiVideoError, match="cleanup master in Registry"):
        validate_project_references(loaded.model_copy(update={"registry": registry}))


@pytest.mark.parametrize("changed", ["master", "viewing", "viewing_receipt"])
def test_viewing_reader_rejects_changed_master_proxy_and_color_evidence(tmp_path, monkeypatch, changed):
    case, _, arguments = _viewing_case(tmp_path, monkeypatch)
    target, writer = case[1:3]
    writer.bootstrap_repair_input(**arguments)
    loaded = load_production_project(target / "project.yaml")
    assets = {item.asset_id: item for item in loaded.registry.assets}
    view = assets["failed-source-viewing"]
    if changed == "viewing_receipt":
        path = target / repair_input_receipt_path(view.creation_receipt_id)
        values = json.loads(path.read_text());values["viewing"]["output_color_space"] = "unknown"
        path.write_text(json.dumps(values))
    else:
        asset = assets["failed-source"] if changed == "master" else view
        (target / asset.artifact_path).write_bytes(b"corrupt")
    with pytest.raises(AiVideoError):
        load_production_project(target / "project.yaml")


def test_viewing_preparation_failure_writes_nothing(tmp_path, monkeypatch):
    case, processor, arguments = _viewing_case(tmp_path, monkeypatch)
    source_root, target, writer = case[:3]
    before = _files(source_root)
    processor.side_effect = ValueError("synthetic viewing failure")
    with pytest.raises(AiVideoError):
        writer.bootstrap_repair_input(**arguments)
    assert _files(target) == {} and _files(source_root) == before
    assert processor.call_count == 1
