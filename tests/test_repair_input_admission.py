"""Development admission preserves failures; it never qualifies or activates media."""

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from ai_video.errors import AiVideoError
from ai_video.production.project import load_production_project
from ai_video.production.hashing import seal_artifact
from ai_video.production.state_commit import ProductionStateCommitter
from test_generation_quality_rejection import _fetched_experience, ACTOR
from test_production_bootstrap import _bootstrap_inputs
from test_production_generated_video_e2e import ATTEMPT_ID


def _files(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def _inputs(tmp_path, *, close=True, abandon=False):
    source = tmp_path / "source"
    source.mkdir(parents=True)
    if abandon:
        from test_generation_quality_rejection import _fetched_mixed_failure

        committer, experience, manifest, attempt = _fetched_mixed_failure(source)
    else:
        committer, experience, manifest, attempt = _fetched_experience(source)
    if close:
        if abandon:
            committer.abandon_video_generation(
                attempt_id=ATTEMPT_ID,
                expected_manifest_revision=manifest.manifest_revision,
                experience_content_hash=attempt.video_generation_state.generation_experiences[-1].content_hash,
                actor=ACTOR,
                reason="Retain the exact failed result while testing a muted preview.",
            )
        else:
            committer.reject_video_generation(attempt_id=ATTEMPT_ID,
                expected_manifest_revision=manifest.manifest_revision,
                experience_content_hash=attempt.video_generation_state.generation_experiences[-1].content_hash,
                actor=ACTOR)
    template = tmp_path / "template"
    template.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    writer = ProductionStateCommitter(target)
    project, registry, artifacts = _bootstrap_inputs(template, writer)
    project = seal_artifact(project.model_copy(update={"project_id": "repair-development"}))
    return source, target, writer, dict(attempt_id="repair-input-bootstrap", project=project,
        registry=registry, artifacts=artifacts, source_root=source,
        source_attempt_id=ATTEMPT_ID, source_sha256=experience.evidence[0].artifact_sha256,
        asset_id="failed-source", usage_license="development fixture only")


def _preview_arguments(source, args):
    from ai_video.production.composition_contracts import FixedTransform
    from ai_video.production.models import Shot
    from ai_video.production.video import ResolvedVideoGenerationRequest, VideoFetchReceipt
    from ai_video.production.video_artifact import MeasuredVideoMetadata, VideoProbeReceipt
    from ai_video.production.paths import canonical_video_fetch_artifact_path
    from ai_video.production.video_retime import VideoTimeMap

    manifest = ProductionStateCommitter(source)._read_manifest()
    attempt = next(item for item in manifest.attempts if item.attempt_id == ATTEMPT_ID)
    state = attempt.video_generation_state
    request = ResolvedVideoGenerationRequest.model_validate_json(
        (source / state.request.path).read_bytes()
    )
    fetch = VideoFetchReceipt.model_validate_json(
        (source / state.fetch_receipt.path).read_bytes()
    )
    source_bytes = (source / canonical_video_fetch_artifact_path(args["source_sha256"])).read_bytes()
    measured = MeasuredVideoMetadata(
        container_name="mp4",
        codec_name="h264",
        width=640,
        height=360,
        fps_numerator=24,
        fps_denominator=1,
        duration_milliseconds=2000,
        frame_count=48,
        audio_stream_count=1,
        size_bytes=len(source_bytes),
        artifact_sha256=args["source_sha256"],
    )
    probe = VideoProbeReceipt.create(request=request, fetch_receipt=fetch, measured=measured)
    shot_refs = {item.path for item in args["project"].artifacts.shots}
    shot = next(
        Shot.model_validate(yaml.safe_load(item.payload))
        for item in args["artifacts"]
        if item.relative_path in shot_refs
    )
    time_map = VideoTimeMap.model_validate({
        "points": [
            {"source_frame": 0, "output_frame": 0},
            {"source_frame": 24, "output_frame": 18},
            {"source_frame": 48, "output_frame": 40},
        ],
        "audio_policy": "mute",
    })
    preview_use = {
        "shot_id": shot.shot_id,
        "asset_role": "final_visual",
        "trim_start_frame": 0,
        "trim_duration_frames": 48,
        "source_time_map": time_map,
        "transform": FixedTransform(),
        "scope": "muted_visual_preview",
    }
    return preview_use, probe, shot


def test_admit_exact_failure_is_unbound_and_replay_adds_no_writes(tmp_path):
    from ai_video.production.repair_input_admission import verify_repair_input
    from ai_video.production.generation_rejection import GenerationQualityRejectionReceipt

    source, target, writer, args = _inputs(tmp_path)
    before = _files(source)
    manifest = writer.bootstrap_repair_input(**args)
    loaded = load_production_project(target / "project.yaml")
    asset = next(a for a in loaded.registry.assets if a.asset_id == "failed-source")
    assert asset.source_kind.value == "imported"
    assert asset.sha256 == args["source_sha256"]
    assert hashlib.sha256(loaded.asset_paths[asset.asset_id].read_bytes()).hexdigest() == asset.sha256
    assert manifest.attempts == ()
    assert manifest.imported_generation_experiences == ()
    assert manifest.active_paid_provider_budget is None
    assert loaded.qa_policy is None
    receipt = verify_repair_input(asset, target)
    documents = {d.path: d.text for d in receipt.documents}
    source_manifest = ProductionStateCommitter(source)._read_manifest()
    state = next(a for a in source_manifest.attempts if a.attempt_id == ATTEMPT_ID).video_generation_state
    rejection = GenerationQualityRejectionReceipt.model_validate_json(documents[state.quality_rejection.path])
    assert rejection.qa_policy.path in documents
    assert not any(asset.asset_id in r.asset_ids for s in loaded.shots for r in s.required_asset_roles)
    assert _files(source) == before
    admitted = _files(target)
    assert writer.bootstrap_repair_input(**args) == manifest
    assert _files(target) == admitted
    assert _files(source) == before


@pytest.mark.parametrize("invalid", ["running", "sha", "overlap"])
def test_invalid_source_rejected_before_any_target_write(tmp_path, invalid):
    source, target, writer, args = _inputs(tmp_path, close=invalid != "running")
    before = _files(source)
    if invalid == "sha":
        args["source_sha256"] = "0" * 64
    if invalid == "overlap":
        writer = ProductionStateCommitter(source)
    with pytest.raises(AiVideoError):
        writer.bootstrap_repair_input(**args)
    assert _files(source) == before
    assert _files(target) == {}


def test_strict_reader_rejects_tampered_admission_receipt(tmp_path):
    from ai_video.production.repair_input_admission import repair_input_receipt_path

    _, target, writer, args = _inputs(tmp_path)
    writer.bootstrap_repair_input(**args)
    loaded = load_production_project(target / "project.yaml")
    asset = next(a for a in loaded.registry.assets if a.asset_id == "failed-source")
    path = target / repair_input_receipt_path(asset.creation_receipt_id)
    path.write_bytes(path.read_bytes().replace(b'"NOT_EVALUATED"', b'"PASS"', 1))
    with pytest.raises(AiVideoError):
        load_production_project(target / "project.yaml")


def test_development_input_cannot_be_bound_as_production_visual(tmp_path):
    from ai_video.production.models import AssetRoleRequirement, AssetType, VisualStrategy
    from ai_video.production.validation import validate_shot_strategy

    _, target, writer, args = _inputs(tmp_path)
    writer.bootstrap_repair_input(**args)
    loaded = load_production_project(target / "project.yaml")
    shot = seal_artifact(loaded.shots[0].model_copy(update={
        "visual_strategy": VisualStrategy.EXISTING_VIDEO,
        "required_asset_roles": (AssetRoleRequirement(role="final_visual", asset_ids=("failed-source",),
            allowed_asset_types=(AssetType.VIDEO,)),),
    }))
    with pytest.raises(AiVideoError, match="repair input"):
        validate_shot_strategy(shot, {a.asset_id: a for a in loaded.registry.assets})


def test_admission_cannot_be_claimed_by_another_project(tmp_path):
    from ai_video.production.validation import validate_project_references

    _, target, writer, args = _inputs(tmp_path)
    writer.bootstrap_repair_input(**args)
    loaded = load_production_project(target / "project.yaml")
    other = seal_artifact(loaded.project.model_copy(update={"project_id": "other-project"}))
    with pytest.raises(AiVideoError, match="repair input"):
        validate_project_references(loaded.model_copy(update={"project": other}))


def test_import_marker_cannot_be_removed_to_skip_provenance(tmp_path):
    from ai_video.production.models import ToolIdentity
    from ai_video.production.registry import _verify_asset

    _, target, writer, args = _inputs(tmp_path)
    writer.bootstrap_repair_input(**args)
    loaded = load_production_project(target / "project.yaml")
    asset = next(a for a in loaded.registry.assets if a.asset_id == "failed-source")
    disguised = asset.model_copy(update={"tool": ToolIdentity(name="ordinary-import", version="1")})
    with pytest.raises(AiVideoError):
        _verify_asset(disguised, target, target / "assets")


@pytest.mark.parametrize("corruption", ["qa_hash", "request_id", "fetch_size"])
def test_resealed_capture_cannot_hide_inner_identity_mismatch(tmp_path, corruption):
    from ai_video.production.hashing import canonical_sha256
    from ai_video.production.repair_input_admission import verify_repair_input, RepairInputAdmissionReceipt

    _, target, writer, args = _inputs(tmp_path)
    writer.bootstrap_repair_input(**args)
    loaded = load_production_project(target / "project.yaml")
    asset = next(a for a in loaded.registry.assets if a.asset_id == "failed-source")
    payload = verify_repair_input(asset, target).model_dump(mode="json")
    manifest = json.loads(payload["source_manifest_json"])
    state = next(a for a in manifest["attempts"] if a["attempt_id"] == ATTEMPT_ID)["video_generation_state"]
    if corruption == "qa_hash":
        rejection_doc = next(d for d in payload["documents"] if d["path"] == state["quality_rejection"]["path"])
        rejection = json.loads(rejection_doc["text"])
        qa_doc = next(d for d in payload["documents"] if d["path"] == rejection["qa_policy"]["path"])
        qa = json.loads(qa_doc["text"])
        qa["policy_id"] = "changed-with-stale-semantic-hash"
        qa_doc["text"] = json.dumps(qa)
        qa_doc["file_sha256"] = hashlib.sha256(qa_doc["text"].encode()).hexdigest()
        rejection["qa_policy"]["file_sha256"] = qa_doc["file_sha256"]
        rejection["qa_policy"]["policy_id"] = qa["policy_id"]
        rejection["content_hash"] = canonical_sha256(rejection)
        rejection_doc["text"] = json.dumps(rejection)
        rejection_doc["file_sha256"] = hashlib.sha256(rejection_doc["text"].encode()).hexdigest()
        old_path = rejection_doc["path"]
        rejection_doc["path"] = old_path.replace(state["quality_rejection"]["content_hash"], rejection["content_hash"])
        state["quality_rejection"].update(path=rejection_doc["path"],
            content_hash=rejection["content_hash"], file_sha256=rejection_doc["file_sha256"])
    elif corruption == "request_id":
        state["request"]["generation_id"] = "another-generation"
        state["generation_id"] = "another-generation"
    else:
        state["fetch_receipt"]["artifact_size_bytes"] += 1
    payload["source_manifest_json"] = json.dumps(manifest)
    payload["source_manifest_sha256"] = hashlib.sha256(payload["source_manifest_json"].encode()).hexdigest()
    payload["content_hash"] = canonical_sha256(payload)
    with pytest.raises(ValueError):
        RepairInputAdmissionReceipt.model_validate(payload)


def test_abandoned_failure_is_available_only_for_its_sealed_muted_preview(tmp_path):
    from ai_video.production.composition_contracts import CompositionLayerSpec
    from ai_video.production.repair_input_admission import (
        RepairPreviewUse,
        allows_repair_preview_layer,
        verify_repair_input,
    )

    source, target, writer, args = _inputs(tmp_path, close=True, abandon=True)
    source_before = _files(source)
    preview_use, preview_probe, shot = _preview_arguments(source, args)
    manifest = writer.bootstrap_repair_input(
        **args, preview_use=preview_use, preview_probe=preview_probe
    )
    loaded = load_production_project(target / "project.yaml")
    asset = next(item for item in loaded.registry.assets if item.asset_id == "failed-source")
    receipt = verify_repair_input(asset, target)
    assert receipt.contract_version == "development-repair-input/2"
    assert receipt.qualification == "NOT_EVALUATED"
    assert receipt.preview_use == RepairPreviewUse.model_validate(preview_use)
    assert asset.video_metadata.probe_receipt_id == preview_probe.content_hash
    assert asset.video_metadata.provenance_receipt_id == receipt.content_hash
    assert asset.artifact_path == Path("assets/files") / f"{asset.sha256}.mp4"
    assert loaded.manifest == manifest
    assert manifest.attempts == ()
    assert manifest.imported_generation_experiences == ()
    assert not any(asset.asset_id in role.asset_ids for shot_item in loaded.shots
                   for role in shot_item.required_asset_roles)
    with pytest.raises(ValueError, match="preview"):
        verify_repair_input(asset.model_copy(update={
            "video_metadata": asset.video_metadata.model_copy(update={"frame_count": 49})
        }), target)
    from ai_video.production.models import ToolIdentity
    from ai_video.production.registry import _verify_asset

    disguised = asset.model_copy(update={"tool": ToolIdentity(name="ordinary-import", version="1")})
    with pytest.raises(AiVideoError, match="provenance"):
        _verify_asset(disguised, target, target / "assets/files")

    layer = CompositionLayerSpec(
        layer_id="preview-layer",
        shot_id=shot.shot_id,
        asset_role=preview_use["asset_role"],
        asset_id=asset.asset_id,
        trim_start_frame=preview_use["trim_start_frame"],
        trim_duration_frames=preview_use["trim_duration_frames"],
        source_time_map=preview_use["source_time_map"],
        transform=preview_use["transform"],
    )
    assert allows_repair_preview_layer(loaded, layer, shot) is True
    from ai_video.production.models import AssetRoleRequirement, AssetType, VisualStrategy
    from ai_video.production.validation import validate_shot_strategy, validate_project_references
    from ai_video.production.repair_input_admission import require_production_render_sources
    bound = shot.model_copy(update={"visual_strategy": VisualStrategy.EXISTING_VIDEO,
        "required_asset_roles": (AssetRoleRequirement(role=layer.asset_role, asset_ids=(asset.asset_id,),
            allowed_asset_types=(AssetType.VIDEO,)),)})
    with pytest.raises(AiVideoError, match="repair input"):
        validate_shot_strategy(bound, {a.asset_id: a for a in loaded.registry.assets})
    other = seal_artifact(loaded.project.model_copy(update={"project_id": "another-preview-project"}))
    with pytest.raises(AiVideoError, match="another project"):
        validate_project_references(loaded.model_copy(update={"project": other}))
    from types import SimpleNamespace
    disguised_timeline = SimpleNamespace(usage_scope="production", visual_spans=(
        SimpleNamespace(asset_sha256=asset.sha256),))
    with pytest.raises(ValueError, match="preview bytes cannot be activated"):
        require_production_render_sources(target, loaded.manifest.active_registry, disguised_timeline)
    assert _files(source) == source_before

    mismatches = (
        layer.model_copy(update={"shot_id": "another-shot"}),
        layer.model_copy(update={"asset_role": "character-reference"}),
        layer.model_copy(update={"trim_start_frame": 1}),
        layer.model_copy(update={"trim_duration_frames": 47}),
        layer.model_copy(update={"source_time_map": preview_use["source_time_map"].model_copy(
            update={"points": (
                preview_use["source_time_map"].points[0],
                preview_use["source_time_map"].points[-1],
            )}
        )}),
        layer.model_copy(update={"transform": layer.transform.model_copy(
            update={"translate_x_px": 1}
        )}),
    )
    for mismatched in mismatches:
        with pytest.raises(ValueError, match="preview"):
            allows_repair_preview_layer(loaded, mismatched, shot)


def test_preview_capture_requires_closed_known_failure_and_exact_probe(tmp_path):
    source, _, writer, args = _inputs(tmp_path, close=False)
    preview_use, preview_probe, _ = _preview_arguments(source, args)
    with pytest.raises(AiVideoError):
        writer.bootstrap_repair_input(
            **args, preview_use=preview_use, preview_probe=preview_probe
        )

    source, _, writer, args = _inputs(tmp_path / "rejected", close=True)
    preview_use, preview_probe, _ = _preview_arguments(source, args)
    writer.bootstrap_repair_input(**args, preview_use=preview_use, preview_probe=preview_probe)
    source, _, writer, args = _inputs(tmp_path / "abandoned", close=True, abandon=True)
    preview_use, preview_probe, _ = _preview_arguments(source, args)
    bad_probe = preview_probe.model_copy(update={
        "measured": preview_probe.measured.model_copy(update={"artifact_sha256": "0" * 64}),
        "content_hash": "0" * 64,
    })
    with pytest.raises(AiVideoError):
        writer.bootstrap_repair_input(
            **args, preview_use=preview_use, preview_probe=bad_probe
        )


def test_native_av_preview_v3_reopens_exact_audio_and_stays_unbound(tmp_path):
    from types import SimpleNamespace

    from ai_video.production.composition_contracts import CompositionLayerSpec
    from ai_video.production.repair_input_admission import (
        RepairAudioPreviewInputAdmissionReceipt,
        allows_repair_preview_layer,
        require_production_render_sources,
        verify_repair_input,
    )
    from ai_video.production.video_retime import VideoTimeMap, VideoTimePoint

    source, target, writer, args = _inputs(tmp_path, close=True, abandon=True)
    source_before = _files(source)
    preview_use, preview_probe, shot = _preview_arguments(source, args)
    preview_use.update(
        scope="retimed_av_preview",
        source_time_map=VideoTimeMap(
            contract_version="video-time-map/2",
            points=(
                VideoTimePoint(source_frame=0, output_frame=0),
                VideoTimePoint(source_frame=24, output_frame=18),
                VideoTimePoint(source_frame=48, output_frame=40),
            ),
            audio_policy="retime_preserve_pitch",
        ),
    )
    manifest = writer.bootstrap_repair_input(
        **args, preview_use=preview_use, preview_probe=preview_probe
    )

    loaded = load_production_project(target / "project.yaml")
    asset = next(item for item in loaded.registry.assets if item.asset_id == "failed-source")
    receipt = verify_repair_input(asset, target)
    assert isinstance(receipt, RepairAudioPreviewInputAdmissionReceipt)
    assert receipt.contract_version == "development-repair-input/3"
    assert receipt.qualification == "NOT_EVALUATED"
    assert receipt.preview_use.scope == "retimed_av_preview"
    assert receipt.preview_probe.measured.audio_stream_count == 1
    assert asset.tool.version == "3"
    assert loaded.manifest == manifest
    assert manifest.attempts == ()
    assert not any(
        asset.asset_id in role.asset_ids
        for shot_item in loaded.shots
        for role in shot_item.required_asset_roles
    )

    layer = CompositionLayerSpec(
        layer_id="preview-layer",
        shot_id=shot.shot_id,
        asset_role=preview_use["asset_role"],
        asset_id=asset.asset_id,
        trim_start_frame=preview_use["trim_start_frame"],
        trim_duration_frames=preview_use["trim_duration_frames"],
        source_time_map=preview_use["source_time_map"],
        transform=preview_use["transform"],
    )
    assert allows_repair_preview_layer(loaded, layer, shot) is True
    with pytest.raises(ValueError, match="preview bytes cannot be activated"):
        require_production_render_sources(
            target,
            loaded.manifest.active_registry,
            SimpleNamespace(
                visual_spans=(SimpleNamespace(asset_sha256=asset.sha256),)
            ),
        )
    from ai_video.production.registry import _verify_asset
    from ai_video.production.models import ToolIdentity

    with pytest.raises(AiVideoError, match="provenance"):
        _verify_asset(
            asset.model_copy(update={"tool": ToolIdentity(name="ordinary-import", version="1")}),
            target,
            target / "assets/files",
        )
    assert _files(source) == source_before


def test_native_av_preview_v3_rejects_missing_stream_and_v2_cannot_carry_map2(tmp_path):
    from pydantic import ValidationError

    from ai_video.production.repair_input_admission import RepairPreviewUse
    from ai_video.production.video_artifact import VideoProbeReceipt
    from ai_video.production.video_retime import VideoTimeMap, VideoTimePoint
    from ai_video.production.hashing import canonical_sha256

    source, target, writer, args = _inputs(tmp_path, close=True, abandon=True)
    preview_use, preview_probe, _ = _preview_arguments(source, args)
    preview_use.update(
        scope="retimed_av_preview",
        source_time_map=VideoTimeMap(
            contract_version="video-time-map/2",
            points=(
                VideoTimePoint(source_frame=0, output_frame=0),
                VideoTimePoint(source_frame=48, output_frame=40),
            ),
            audio_policy="retime_preserve_pitch",
        ),
    )
    candidate = preview_probe.model_copy(update={
        "measured": preview_probe.measured.model_copy(update={"audio_stream_count": 0}),
        "content_hash": "0" * 64,
    })
    no_audio_probe = VideoProbeReceipt.model_validate({
        **candidate.model_dump(mode="json"),
        "content_hash": canonical_sha256(
            candidate.model_dump(mode="json", exclude={"content_hash"})
        ),
    })
    with pytest.raises(AiVideoError):
        writer.bootstrap_repair_input(
            **args, preview_use=preview_use, preview_probe=no_audio_probe
        )
    assert _files(target) == {}

    with pytest.raises(ValidationError):
        RepairPreviewUse.model_validate({
            **preview_use,
            "scope": "muted_visual_preview",
        })


def test_legacy_repair_input_remains_unusable_for_retimed_preview(tmp_path):
    from ai_video.production.composition_contracts import CompositionLayerSpec
    from ai_video.production.repair_input_admission import allows_repair_preview_layer

    source, target, writer, args = _inputs(tmp_path)
    writer.bootstrap_repair_input(**args)
    loaded = load_production_project(target / "project.yaml")
    preview_use, _, shot = _preview_arguments(source, args)
    layer = CompositionLayerSpec(
        layer_id="legacy-preview",
        shot_id=shot.shot_id,
        asset_role=preview_use["asset_role"],
        asset_id="failed-source",
        trim_start_frame=preview_use["trim_start_frame"],
        trim_duration_frames=preview_use["trim_duration_frames"],
        source_time_map=preview_use["source_time_map"],
        transform=preview_use["transform"],
    )
    with pytest.raises(ValueError, match="(?i)legacy"):
        allows_repair_preview_layer(loaded, layer, shot)


def test_preview_probe_or_source_byte_tampering_is_rejected(tmp_path):
    from ai_video.production.repair_input_admission import repair_input_receipt_path

    source, target, writer, args = _inputs(tmp_path, close=True, abandon=True)
    preview_use, preview_probe, _ = _preview_arguments(source, args)
    writer.bootstrap_repair_input(
        **args, preview_use=preview_use, preview_probe=preview_probe
    )
    loaded = load_production_project(target / "project.yaml")
    asset = next(item for item in loaded.registry.assets if item.asset_id == "failed-source")
    path = target / repair_input_receipt_path(asset.creation_receipt_id)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["preview_probe"]["measured"]["width"] += 1
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(AiVideoError):
        load_production_project(target / "project.yaml")

    _, target, writer, args = _inputs(tmp_path / "source-tamper", close=True, abandon=True)
    preview_use, preview_probe, _ = _preview_arguments(args["source_root"], args)
    writer.bootstrap_repair_input(
        **args, preview_use=preview_use, preview_probe=preview_probe
    )
    loaded = load_production_project(target / "project.yaml")
    asset = next(item for item in loaded.registry.assets if item.asset_id == "failed-source")
    media = target / loaded.asset_paths[asset.asset_id]
    media.write_bytes(media.read_bytes() + b"tamper")
    with pytest.raises(AiVideoError):
        load_production_project(target / "project.yaml")
