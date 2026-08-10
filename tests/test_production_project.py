from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket

import pytest
import yaml

from ai_video.config import load_project, sha256_file
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.captions import (
    _canonical_track_bytes,
    caption_timing_fingerprint,
)
from ai_video.production import (
    ProductionStateCommitter,
    load_production_project,
    prepare_project_registry_commit,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.hashing import canonical_sha256
from ai_video.production.composition import resolve_composition, timeline_fingerprint
from ai_video.production.hyperframes import (
    HyperFramesRenderResult,
    VerifiedRenderOutput,
    materialize_hyperframes_source,
    prepare_durable_render_artifacts,
)
from ai_video.production.models import (
    AssetRegistrySnapshot,
    AssetSourceKind,
    DeliveryProfile,
    FixedTransform,
    AudioChannelLayout,
    CaptionTrack,
    MeasuredAudioRenderMetadata,
    MeasuredRenderMetadata,
    EgressMetadata,
    ProductionManifest,
    ProductionProject,
    RegistrySnapshotPointer,
    RendererCheckReceipt,
    RendererIdentity,
    RendererKind,
    RendererSelectionReceipt,
    RendererSourceReceipt,
    ResolvedTimeline,
    ResolvedVisualSpan,
    SourceReference,
    StateCommitAttempt,
    StateCommitStatus,
    canonical_project_snapshot_path,
    canonical_registry_snapshot_path,
)
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import (
    ActivateRenderStateRequest,
    BeginRenderAttemptRequest,
)
from ai_video.production.project import _render_source_payload_matches
from production_project_factory import (
    load_revision_two_models,
    make_p4_composition_fixture,
    make_voice_activation_request,
    make_voice_preview_and_authorization,
    make_voice_request,
    write_production_project,
)


def _manifest(root: Path) -> ProductionManifest:
    return ProductionManifest.model_validate_json(
        (root / "state/manifest.json").read_text(encoding="utf-8")
    )


def _write_manifest(root: Path, manifest: ProductionManifest) -> None:
    (root / "state/manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )


def _commit_revision_two(
    root: Path, *, attempt_id: str = "loader-revision-two"
) -> ProductionProject:
    manifest = _manifest(root)
    project, registry = load_revision_two_models(root)
    ProductionStateCommitter(root).commit(
        prepare_project_registry_commit(
            manifest=manifest,
            project=project,
            registry=registry,
            attempt_id=attempt_id,
        )
    )
    return project


def _corrupt_active_project(root: Path, project_data: dict[str, object]) -> None:
    manifest = _manifest(root)
    replacement = seal_artifact(ProductionProject.model_validate(project_data))
    snapshot_path = root / manifest.active_project.path
    snapshot_path.write_text(
        yaml.safe_dump(
            replacement.model_dump(mode="json"),
            sort_keys=True,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    pointer = manifest.active_project.model_copy(
        update={
            "content_hash": replacement.content_hash,
            "file_sha256": sha256_file(snapshot_path),
        }
    )
    _write_manifest(root, manifest.model_copy(update={"active_project": pointer}))


def _tree_snapshot(root: Path) -> dict[Path, tuple[bytes, int]]:
    return {
        path.relative_to(root): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*")
        if path.is_file()
    }


def _activate_fake_render(
    root: Path, attempt_id: str = "reader-render", *, p4: bool = False
):
    if p4:
        loaded, spec = make_p4_composition_fixture(root)
        spec = seal_artifact(
            spec.model_copy(
                update={
                    "content_hash": "0" * 64,
                    "shot_ids": ("shot-1",),
                    "layers": (spec.layers[0],),
                    "transitions": (),
                    "audio_tracks": (spec.audio_tracks[0],),
                }
            )
        )
        committed = ProductionStateCommitter(root).commit(
            prepare_project_registry_commit(
                manifest=loaded.manifest,
                project=loaded.project,
                registry=loaded.registry,
                attempt_id="reader-p4-registry",
            )
        )
        loaded = load_production_project(root / "project.yaml")
        timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")
        sources = {
            item.asset_id: loaded.asset_paths[item.asset_id]
            for item in (*timeline.visual_spans, *timeline.audio_spans)
        }
        sources.update(
            {
                item.caption_asset_id: loaded.asset_paths[item.caption_asset_id]
                for item in timeline.caption_cues
            }
        )
        style = spec.caption_tracks[0].style_reference
        assert style is not None
        sources[style.artifact_id] = root / style.path
        before = committed
    else:
        write_production_project(root)
        before = _manifest(root)
    png = (
        Path(__file__).parent / "fixtures/hyperframes/silent_image/source/assets/"
        "1ac67c3a1c909b3356cf6ff490c0f88b8a30ef4c28ca579657f6007146abe71c.png"
    ).read_bytes()
    digest = hashlib.sha256(png).hexdigest()
    source_path = root / "reader-input/red.png"
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(png)
    provisional = ResolvedTimeline(
        artifact_id="timeline-reader",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="resolve-reader",
        source_provenance=(
            SourceReference(kind="derived", reference="reader-fixture"),
        ),
        timeline_id="timeline-reader-r1",
        composition_spec_id="composition-reader",
        composition_spec_revision=1,
        composition_spec_hash="1" * 64,
        delivery_profile=DeliveryProfile(width=1280, height=720, fps=24),
        sample_rate=48_000,
        renderer=RendererIdentity(kind=RendererKind.HYPERFRAMES, version="0.7.103"),
        visual_spans=(
            ResolvedVisualSpan(
                layer_id="layer-reader",
                shot_id="shot-1",
                asset_role="hero_still",
                asset_id="reader-red",
                asset_sha256=digest,
                asset_mime_type="image/png",
                materialized_path=Path(f"assets/{digest}.png"),
                start_frame=0,
                duration_frames=10,
                start_sample=0,
                duration_samples=20_000,
                trim_start_frame=0,
                trim_duration_frames=None,
                transform=FixedTransform(),
                opacity_milli=1000,
                z_index=0,
                incoming_transition=None,
            ),
        ),
        total_frames=10,
        total_samples=20_000,
        composition_fingerprint="0" * 64,
    )
    if not p4:
        timeline = seal_artifact(
            provisional.model_copy(
                update={"composition_fingerprint": timeline_fingerprint(provisional)}
            )
        )
        sources = {"reader-red": source_path}
    selection = RendererSelectionReceipt(
        receipt_id=f"selection-{attempt_id}",
        attempt_id=attempt_id,
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=before.active_project,
        current_registry=before.active_registry,
    )
    materialized = materialize_hyperframes_source(
        timeline,
        asset_sources=sources,
        allowed_asset_root=root,
        staging_root=root / "reader-source",
        allowed_staging_parent=root,
    )
    checks = tuple(
        RendererCheckReceipt(
            command=command,
            tool_version="0.7.103",
            exit_code=0,
            stdout_sha256="0" * 64,
            stderr_sha256="0" * 64,
            error_count=0,
            warning_count=0,
        )
        for command in ("lint", "check")
    )
    output = b"fake-mp4"
    result = HyperFramesRenderResult(
        materialized=materialized,
        checks=checks,  # type: ignore[arg-type]
        output=VerifiedRenderOutput(
            untrusted_staged_path=root / "unused-staged.mp4",
            verification_snapshot_path=root / "unused-verified.mp4",
            verified_bytes=output,
            output_sha256=hashlib.sha256(output).hexdigest(),
            output_size_bytes=len(output),
            measured=MeasuredRenderMetadata(
                width=timeline.delivery_profile.width,
                height=timeline.delivery_profile.height,
                fps_num=timeline.delivery_profile.fps,
                fps_den=1,
                duration_frames=timeline.total_frames,
                codec_name="h264",
                audio=(
                    MeasuredAudioRenderMetadata(
                        stream_count=1,
                        codec_name="aac",
                        sample_rate_hz=timeline.sample_rate,
                        channels=2,
                        channel_layout=AudioChannelLayout.STEREO,
                        decoded_samples=timeline.total_samples,
                        encoder_priming_samples=0,
                        encoder_padding_samples=0,
                        measurement_method="fake-held-fd",
                    )
                    if p4
                    else None
                ),
            ),
            decoded_frame_fingerprint="2" * 64,
            decoded_audio_fingerprint="3" * 64 if p4 else None,
        ),
    )
    committer = ProductionStateCommitter(root)
    begun = committer.begin_render_attempt(
        BeginRenderAttemptRequest(before.manifest_revision, None, selection)
    )
    durable = prepare_durable_render_artifacts(
        result,
        timeline=timeline,
        renderer_selection=selection,
        current_project=begun.active_project,
        current_registry=begun.active_registry,
    )
    request = ActivateRenderStateRequest(
        attempt_id=attempt_id,
        expected_manifest_revision=begun.manifest_revision,
        current_project=begun.active_project,
        current_registry=begun.active_registry,
        base_render_state=None,
        renderer_selection=selection,
        artifacts=durable.artifacts,
        next_render_state=durable.next_render_state,
    )
    activated = committer.activate_render_state(request)
    return activated, durable, request


def _activate_fake_voice(root: Path, *, include_caption: bool = True):
    project_path = write_production_project(root)
    request, committed, audio_ids, caption_ids = _append_fake_voice(
        root, attempt_id="reader-voice", include_caption=include_caption
    )
    return project_path, request, committed, audio_ids, caption_ids


def _append_fake_voice(root: Path, *, attempt_id: str, include_caption: bool = True):
    request = make_voice_request(root, attempt_id=attempt_id)
    preview, authorization = make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(root)
    writer.begin_voice_generation(request, preview, authorization)
    writer.record_voice_submit_intent(request, preview, authorization)
    activation, audio_ids = make_voice_activation_request(
        root,
        request,
        authorization,
        expected_manifest_revision=_manifest(root).manifest_revision,
        include_caption=include_caption,
    )
    caption_ids = (f"caption-{request.attempt_id}",) if include_caption else ()
    committed = writer.activate_voice_assets(
        activation,
        audio_asset_ids=audio_ids,
        caption_asset_ids=caption_ids,
    )
    return request, committed, audio_ids, caption_ids


def _select_resealed_registry(root: Path, registry: AssetRegistrySnapshot) -> None:
    provisional = registry.model_copy(
        update={"revision_id": "0" * 64, "content_hash": "0" * 64}
    )
    digest = registry_semantic_sha256(provisional)
    sealed = provisional.model_copy(
        update={"revision_id": digest, "content_hash": digest}
    )
    payload = sealed.model_dump_json(indent=2).encode("utf-8")
    path = canonical_registry_snapshot_path(digest)
    (root / path).write_bytes(payload)
    pointer = RegistrySnapshotPointer(
        path=path,
        revision_id=digest,
        content_hash=digest,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    manifest = _manifest(root)
    _write_manifest(root, manifest.model_copy(update={"active_registry": pointer}))


def _rebind_voice_candidate_to_selected_graph(root: Path, attempt_id: str) -> None:
    manifest = _manifest(root)
    attempt = next(item for item in manifest.attempts if item.attempt_id == attempt_id)
    candidate_pointer = manifest.active_registry
    base = AssetRegistrySnapshot.model_validate_json(
        (root / attempt.base_registry.path).read_bytes()
    )
    candidate = AssetRegistrySnapshot.model_validate_json(
        (root / candidate_pointer.path).read_bytes()
    )
    pairs = [
        (
            attempt.base_project.path.as_posix(),
            sha256_file(root / attempt.base_project.path),
        ),
        (candidate_pointer.path.as_posix(), candidate_pointer.file_sha256),
    ]
    for record in candidate.assets[len(base.assets) :]:
        pairs.append(
            (record.artifact_path.as_posix(), sha256_file(root / record.artifact_path))
        )
        if record.caption_metadata is not None:
            style_hash = record.caption_metadata.style_content_hash
            if style_hash is not None:
                style_path = Path(f"assets/styles/{style_hash}.json")
                pairs.append((style_path.as_posix(), sha256_file(root / style_path)))
    paths = ProductionStateCommitter(root).voice_attempt_paths(attempt_id)
    for evidence in (
        paths.request_path,
        paths.preview_path,
        paths.authorization_path,
        paths.submit_intent_path,
        paths.alignment_path,
        paths.cost_path,
        paths.provenance_path,
        paths.outcome_path,
    ):
        pairs.append((evidence.relative_to(root).as_posix(), sha256_file(evidence)))
    candidate_hash = hashlib.sha256(
        json.dumps(sorted(pairs), separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    changed_attempt = attempt.model_copy(
        update={
            "candidate_registry": candidate_pointer,
            "candidate_artifacts_hash": candidate_hash,
        }
    )
    _write_manifest(
        root,
        manifest.model_copy(
            update={
                "attempts": tuple(
                    changed_attempt if item.attempt_id == attempt_id else item
                    for item in manifest.attempts
                )
            }
        ),
    )


def _replace_selected_voice_asset(root: Path, attempt_id: str, replacement) -> None:
    manifest = _manifest(root)
    registry = AssetRegistrySnapshot.model_validate_json(
        (root / manifest.active_registry.path).read_bytes()
    )
    _select_resealed_registry(
        root,
        registry.model_copy(
            update={
                "assets": tuple(
                    replacement if item.asset_id == replacement.asset_id else item
                    for item in registry.assets
                )
            }
        ),
    )
    _rebind_voice_candidate_to_selected_graph(root, attempt_id)


def _rewrite_voice_semantic_evidence(root: Path, request, mutation: str) -> None:
    from ai_video.production.audio import (
        VoiceCallAuthorization,
        VoiceCostReceipt,
        VoiceGenerationPreview,
        VoiceProvenanceReceipt,
    )

    paths = ProductionStateCommitter(root).voice_attempt_paths(request.attempt_id)
    preview = VoiceGenerationPreview.model_validate_json(
        paths.preview_path.read_bytes()
    )
    authorization = VoiceCallAuthorization.model_validate_json(
        paths.authorization_path.read_bytes()
    )
    cost = VoiceCostReceipt.model_validate_json(paths.cost_path.read_bytes())
    provenance = VoiceProvenanceReceipt.model_validate_json(
        paths.provenance_path.read_bytes()
    )
    result_request_id = request.request_id
    result_request_fingerprint = request.voice_request_fingerprint
    result_preview_fingerprint = preview.preview_fingerprint
    result_authorization_fingerprint = authorization.authorization_fingerprint
    if mutation == "pricing_snapshot":
        cost = cost.model_copy(update={"pricing_snapshot_id": "wrong-pricing"})
    elif mutation == "cost_currency":
        cost = cost.model_copy(update={"currency": "EUR"})
    elif mutation == "measured_units":
        cost = cost.model_copy(
            update={"measured_billable_units": preview.billable_units_upper_bound + 1}
        )
    elif mutation == "estimated_cost":
        cost = cost.model_copy(
            update={
                "estimated_cost_upper_bound_microunits": (
                    cost.estimated_cost_upper_bound_microunits + 1
                )
            }
        )
    elif mutation == "reported_cost_ceiling":
        cost = cost.model_copy(
            update={
                "provider_reported_cost_microunits": (
                    authorization.cost_ceiling_microunits + 1
                )
            }
        )
    elif mutation == "result_request_id":
        result_request_id = "wrong-request"
        cost = cost.model_copy(update={"request_id": result_request_id})
        provenance = provenance.model_copy(update={"request_id": result_request_id})
    elif mutation == "result_request_fingerprint":
        result_request_fingerprint = "e" * 64
        provenance = provenance.model_copy(
            update={"request_fingerprint": result_request_fingerprint}
        )
    elif mutation == "preview_fingerprint":
        result_preview_fingerprint = "d" * 64
    elif mutation == "authorization_fingerprint":
        result_authorization_fingerprint = "c" * 64
    elif mutation == "output_sample_rate":
        provenance = provenance.model_copy(
            update={"output_sample_rate_hz": request.output_sample_rate_hz + 1}
        )
    elif mutation == "output_channels":
        provenance = provenance.model_copy(
            update={"output_channels": 2 if request.output_channels == 1 else 1}
        )
    elif mutation == "output_container":
        provenance = provenance.model_copy(update={"output_container": "mp3"})
    elif mutation == "output_codec":
        provenance = provenance.model_copy(update={"output_codec": "mp3"})
    else:
        field, value = {
            "provider_kind": ("provider_kind", "wrong-provider"),
            "model_id": ("model_id", "wrong-model"),
            "voice_id": ("voice_id", "wrong-voice"),
            "language": ("language", "fr"),
            "script_hash": ("script_hash", "f" * 64),
            "egress_authorization": (
                "egress_authorization_receipt_id",
                "wrong-egress",
            ),
        }[mutation]
        provenance = provenance.model_copy(update={field: value})
    alignment = paths.alignment_path.read_bytes()
    manifest = _manifest(root)
    registry = AssetRegistrySnapshot.model_validate_json(
        (root / manifest.active_registry.path).read_bytes()
    )
    audio_record = next(
        item
        for item in registry.assets
        if item.asset_id == f"voice-{request.attempt_id}"
    )
    outcome = json.loads(paths.outcome_path.read_bytes())
    fingerprint_payload = {
        "request_id": result_request_id,
        "request_fingerprint": result_request_fingerprint,
        "audio_sha256": audio_record.sha256,
        "content_type": audio_record.mime_type,
        "provider_request_id": outcome["provider_request_id"],
        "provider_trace_id": outcome["provider_trace_id"],
        "alignment_receipt_sha256": hashlib.sha256(alignment).hexdigest(),
        "cost_receipt": cost.model_dump(mode="python"),
        "provenance_receipt": provenance.model_dump(mode="python"),
        "terminal_status": "succeeded",
        "preview_fingerprint": result_preview_fingerprint,
        "authorization_fingerprint": result_authorization_fingerprint,
    }
    result_fingerprint = canonical_sha256(fingerprint_payload)

    def canonical_model_bytes(model) -> bytes:
        return (
            json.dumps(
                model.model_dump(mode="json"),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")

    cost_bytes = canonical_model_bytes(cost)
    provenance_bytes = canonical_model_bytes(provenance)
    paths.cost_path.write_bytes(cost_bytes)
    paths.provenance_path.write_bytes(provenance_bytes)
    outcome["request_id"] = result_request_id
    outcome["request_fingerprint"] = result_request_fingerprint
    outcome["preview_fingerprint"] = result_preview_fingerprint
    outcome["authorization_fingerprint"] = result_authorization_fingerprint
    outcome["result_fingerprint"] = result_fingerprint
    paths.outcome_path.write_bytes(
        (json.dumps(outcome, sort_keys=True, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
    )
    assert audio_record.audio_metadata is not None
    changed = audio_record.model_copy(
        update={
            "creation_receipt_id": f"voice-result-{result_fingerprint}",
            "cost_receipt_id": f"cost-{hashlib.sha256(cost_bytes).hexdigest()}",
            "audio_metadata": audio_record.audio_metadata.model_copy(
                update={
                    "provenance_receipt_id": (
                        f"provenance-{hashlib.sha256(provenance_bytes).hexdigest()}"
                    )
                }
            ),
        }
    )
    _select_resealed_registry(
        root,
        registry.model_copy(
            update={
                "assets": tuple(
                    changed if item.asset_id == changed.asset_id else item
                    for item in registry.assets
                )
            }
        ),
    )
    _rebind_voice_candidate_to_selected_graph(root, request.attempt_id)


def test_load_production_project_returns_verified_bundle(tmp_path):
    project_path = write_production_project(tmp_path)
    loaded = load_production_project(project_path)
    assert loaded.project.project_id == "comic-demo"
    assert loaded.project.revision == 1
    assert loaded.shots[0].visual_strategy.value == "static_image"
    assert loaded.asset_paths["image-hero-1"].is_relative_to(tmp_path.resolve())


def test_load_selects_committed_revision_two_not_root_project(tmp_path):
    project_path = write_production_project(tmp_path)
    root_project_bytes = project_path.read_bytes()
    revision_two = _commit_revision_two(tmp_path)

    loaded = load_production_project(project_path)

    assert loaded.project.revision == 2
    assert loaded.project.content_hash == revision_two.content_hash
    assert loaded.project.title == "Comic Demo Revision 2"
    assert project_path.read_bytes() == root_project_bytes
    assert loaded.manifest.active_project.path != Path("project.yaml")


def test_load_requires_existing_regular_project_entrypoint(tmp_path):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    project_path.unlink()

    with pytest.raises(AiVideoError, match="entry point"):
        load_production_project(project_path)


def test_load_rejects_directory_project_entrypoint(tmp_path):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    project_path.unlink()
    project_path.mkdir()

    with pytest.raises(AiVideoError, match="regular file"):
        load_production_project(project_path)


@pytest.mark.parametrize("outside", [False, True])
def test_load_rejects_symlink_project_entrypoint(tmp_path, outside):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    original = project_path.read_bytes()
    project_path.unlink()
    target = (
        tmp_path.parent / "outside-project.yaml"
        if outside
        else tmp_path / "creative/entrypoint.yaml"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(original)
    project_path.symlink_to(target)

    with pytest.raises(AiVideoError, match="symlink"):
        load_production_project(project_path)


def test_load_rejects_manifest_project_id_mismatch(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = _manifest(tmp_path).model_copy(update={"project_id": "other-project"})
    _write_manifest(tmp_path, manifest)

    with pytest.raises(AiVideoError, match="project_id"):
        load_production_project(project_path)


def test_load_uses_manifest_pointer_not_decoy_filename_or_mtime(tmp_path):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    decoy = tmp_path / "state/projects/project.999.decoy.yaml"
    decoy.write_text("not: a production project\n", encoding="utf-8")
    decoy.touch()
    registry_decoy = tmp_path / f"assets/registry.{'f' * 64}.json"
    registry_decoy.write_text("not json", encoding="utf-8")
    registry_decoy.touch()

    loaded = load_production_project(project_path)

    assert loaded.project.revision == 2
    assert loaded.manifest.active_project.path.name != decoy.name
    assert loaded.manifest.active_registry.path.name != registry_decoy.name


def test_load_rejects_active_project_file_hash_mismatch(tmp_path):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    manifest = _manifest(tmp_path).model_copy(
        update={
            "active_project": _manifest(tmp_path).active_project.model_copy(
                update={"file_sha256": "f" * 64}
            )
        }
    )
    _write_manifest(tmp_path, manifest)

    with pytest.raises(AiVideoError, match="file hash"):
        load_production_project(project_path)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("revision", 999, "project revision"),
        ("content_hash", "f" * 64, "project content hash"),
    ],
)
def test_load_rejects_active_project_pointer_identity_mismatch(
    tmp_path, field, value, message
):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    manifest = _manifest(tmp_path)
    active_project = manifest.active_project.model_copy(update={field: value})
    active_project = active_project.model_copy(
        update={
            "path": canonical_project_snapshot_path(
                active_project.revision, active_project.content_hash
            )
        }
    )
    target = tmp_path / active_project.path
    target.write_bytes((tmp_path / manifest.active_project.path).read_bytes())
    _write_manifest(
        tmp_path,
        manifest.model_copy(update={"active_project": active_project}),
    )

    with pytest.raises(AiVideoError, match=message):
        load_production_project(project_path)


def test_load_rejects_active_registry_file_hash_mismatch(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = _manifest(tmp_path).model_copy(
        update={
            "active_registry": _manifest(tmp_path).active_registry.model_copy(
                update={"file_sha256": "f" * 64}
            )
        }
    )
    _write_manifest(tmp_path, manifest)

    with pytest.raises(AiVideoError, match="file hash"):
        load_production_project(project_path)


def test_load_rejects_active_registry_identity_mismatch_without_fallback(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = _manifest(tmp_path)
    active_registry = manifest.active_registry.model_copy(
        update={
            "path": canonical_registry_snapshot_path("f" * 64),
            "revision_id": "f" * 64,
            "content_hash": "f" * 64,
        }
    )
    (tmp_path / active_registry.path).write_bytes(
        (tmp_path / manifest.active_registry.path).read_bytes()
    )
    _write_manifest(
        tmp_path, manifest.model_copy(update={"active_registry": active_registry})
    )

    with pytest.raises(AiVideoError, match="filename does not match revision_id"):
        load_production_project(project_path)


def test_load_rejects_tampered_active_registry_without_root_fallback(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = _manifest(tmp_path)
    registry_path = tmp_path / manifest.active_registry.path
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    data["assets"][0]["sha256"] = "1" * 64
    registry_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(AiVideoError) as exc:
        load_production_project(project_path)
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


@pytest.mark.parametrize(
    "stored", ["../story.yaml", "/tmp/story.yaml", "other/story.yaml"]
)
def test_load_rejects_unsafe_creative_reference_path(tmp_path, stored):
    project_path = write_production_project(tmp_path)
    project_data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    project_data["artifacts"]["story"]["path"] = stored
    _corrupt_active_project(tmp_path, project_data)

    with pytest.raises(AiVideoError, match="contained"):
        load_production_project(project_path)


@pytest.mark.parametrize("asset_root", ["../outside", "creative"])
def test_load_rejects_unsafe_asset_root(tmp_path, asset_root):
    project_path = write_production_project(tmp_path)
    project_data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    project_data["asset_root"] = asset_root
    _corrupt_active_project(tmp_path, project_data)

    with pytest.raises(AiVideoError, match="contained"):
        load_production_project(project_path)


@pytest.mark.parametrize("path", [Path("../outside.yaml"), Path("/tmp/outside.yaml")])
def test_load_rejects_unsafe_active_project_pointer_before_read(tmp_path, path):
    project_path = write_production_project(tmp_path)
    manifest_data = json.loads(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    manifest_data["active_project"]["path"] = str(path)
    (tmp_path / "state/manifest.json").write_text(
        json.dumps(manifest_data), encoding="utf-8"
    )

    with pytest.raises(AiVideoError, match="Could not load production state"):
        load_production_project(project_path)


@pytest.mark.parametrize(
    ("pointer_name", "path"),
    [
        ("active_project", "state/projects/arbitrary.yaml"),
        ("active_registry", "assets/arbitrary.json"),
    ],
)
def test_load_rejects_noncanonical_manifest_snapshot_pointer(
    tmp_path, pointer_name, path
):
    project_path = write_production_project(tmp_path)
    manifest_path = tmp_path / "state/manifest.json"
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_path = tmp_path / manifest_data[pointer_name]["path"]
    target_path = tmp_path / path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(source_path.read_bytes())
    manifest_data[pointer_name]["path"] = path
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    with pytest.raises(AiVideoError, match="Could not load production state"):
        load_production_project(project_path)


def test_load_rejects_active_project_symlink_escape(tmp_path):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    manifest = _manifest(tmp_path)
    outside = tmp_path.parent / "outside-project.yaml"
    target = tmp_path / manifest.active_project.path
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)

    with pytest.raises(AiVideoError, match="contained"):
        load_production_project(project_path)


def test_manifest_symlink_cannot_escape_state_root(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = tmp_path / "state/manifest.json"
    relocated = tmp_path / "creative/manifest.json"
    manifest.rename(relocated)
    manifest.symlink_to(relocated)

    with pytest.raises(AiVideoError, match="contained"):
        load_production_project(project_path)


def test_project_root_symlink_loop_returns_typed_project_error(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.symlink_to(second.name)
    second.symlink_to(first.name)

    with pytest.raises(AiVideoError) as exc:
        load_production_project(first / "project.yaml")
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_load_runs_full_creative_validation_for_selected_snapshot(tmp_path):
    project_path = write_production_project(tmp_path)
    story_path = tmp_path / "creative/story.yaml"
    data = yaml.safe_load(story_path.read_text(encoding="utf-8"))
    data["logline"] = "tampered"
    story_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(AiVideoError, match="content hash"):
        load_production_project(project_path)


def test_loader_creates_no_directories_preserves_inputs_and_does_not_recover(tmp_path):
    project_path = write_production_project(tmp_path)
    orphan = tmp_path / "state/projects/project.99.orphan.yaml"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_text("untracked", encoding="utf-8")
    files_before = {
        path.relative_to(tmp_path): (path.stat().st_mtime_ns, path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    directories_before = {
        path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_dir()
    }

    load_production_project(project_path)

    files_after = {
        path.relative_to(tmp_path): (path.stat().st_mtime_ns, path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    directories_after = {
        path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_dir()
    }
    assert files_after == files_before
    assert directories_after == directories_before


def test_loader_requires_canonical_project_entrypoint_name(tmp_path):
    project_path = write_production_project(tmp_path)
    with pytest.raises(AiVideoError, match="must be named project.yaml"):
        load_production_project(project_path.with_name("other.yaml"))


def test_legacy_project_loader_remains_unchanged():
    project = load_project("configs/wan22_fast.project.yaml")
    assert project.project_name == "wan22-fast-demo"


def test_reader_loads_20_historical_custom_operation_without_rewrite(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = _manifest(tmp_path)
    historical = StateCommitAttempt(
        attempt_id="historical-custom",
        operation="historical_custom_operation",
        status=StateCommitStatus.SUCCEEDED,
        base_manifest_revision=manifest.manifest_revision,
        base_project=manifest.active_project,
        base_registry=manifest.active_registry,
        candidate_artifacts_hash="0" * 64,
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:00:01+00:00",
    )
    _write_manifest(
        tmp_path,
        manifest.model_copy(update={"attempts": (historical,)}),
    )
    before = _tree_snapshot(tmp_path)

    loaded = load_production_project(project_path)

    assert loaded.manifest.schema_version == "2.0"
    assert loaded.manifest.attempts[-1].operation == "historical_custom_operation"
    assert loaded.render_state is None
    assert _tree_snapshot(tmp_path) == before


def test_reader_loads_21_with_none_render_state_without_rewrite(tmp_path):
    project_path = write_production_project(tmp_path)
    _write_manifest(
        tmp_path,
        _manifest(tmp_path).model_copy(update={"schema_version": "2.1"}),
    )
    before = _tree_snapshot(tmp_path)

    loaded = load_production_project(project_path)

    assert loaded.manifest.schema_version == "2.1"
    assert loaded.render_state is None
    assert _tree_snapshot(tmp_path) == before


def test_reader_reopens_exact_generated_voice_graph_without_writes_or_network(
    tmp_path, monkeypatch
):
    project_path, request, committed, audio_ids, caption_ids = _activate_fake_voice(
        tmp_path
    )
    before = _tree_snapshot(tmp_path)

    def reject_network(*_args, **_kwargs):
        raise AssertionError("read-only project load attempted network access")

    monkeypatch.setattr(socket, "create_connection", reject_network)
    loaded = load_production_project(project_path)

    assert loaded.manifest.active_registry == committed.active_registry
    assert loaded.manifest.active_render_state is None
    assert {item.asset_id for item in loaded.registry.assets}.issuperset(
        {*audio_ids, *caption_ids}
    )
    attempt = next(
        item
        for item in loaded.manifest.attempts
        if item.attempt_id == request.attempt_id
    )
    assert attempt.voice_phase == "activate"
    assert _tree_snapshot(tmp_path) == before


def test_reader_rejects_generated_voice_resealed_as_local_egress(tmp_path):
    project_path, request, _, _, _ = _activate_fake_voice(
        tmp_path, include_caption=False
    )
    manifest = _manifest(tmp_path)
    registry = AssetRegistrySnapshot.model_validate_json(
        (tmp_path / manifest.active_registry.path).read_bytes()
    )
    audio_id = f"voice-{request.attempt_id}"
    changed_assets = tuple(
        item.model_copy(update={"egress": EgressMetadata()})
        if item.asset_id == audio_id
        else item
        for item in registry.assets
    )
    _select_resealed_registry(
        tmp_path, registry.model_copy(update={"assets": changed_assets})
    )
    _rebind_voice_candidate_to_selected_graph(tmp_path, request.attempt_id)

    with pytest.raises(AiVideoError, match="remote egress evidence"):
        load_production_project(project_path)


@pytest.mark.parametrize(
    "mutation",
    [
        "pricing_snapshot",
        "cost_currency",
        "measured_units",
        "estimated_cost",
        "reported_cost_ceiling",
        "result_request_id",
        "result_request_fingerprint",
        "preview_fingerprint",
        "authorization_fingerprint",
        "output_sample_rate",
        "output_channels",
        "output_container",
        "output_codec",
        "provider_kind",
        "model_id",
        "voice_id",
        "language",
        "script_hash",
        "egress_authorization",
    ],
)
def test_reader_rejects_resealed_voice_receipt_semantic_contradictions(
    tmp_path, mutation
):
    project_path, request, _, _, _ = _activate_fake_voice(
        tmp_path, include_caption=False
    )
    _rewrite_voice_semantic_evidence(tmp_path, request, mutation)

    with pytest.raises(AiVideoError, match="voice evidence graph"):
        load_production_project(project_path)


@pytest.mark.parametrize("artifact", ["provenance", "cost", "alignment"])
def test_reader_rejects_tampered_selected_voice_evidence_without_recovery(
    tmp_path, artifact
):
    project_path, request, _, _, _ = _activate_fake_voice(tmp_path)
    writer = ProductionStateCommitter(tmp_path)
    paths = writer.voice_attempt_paths(request.attempt_id)
    selected = {
        "provenance": paths.provenance_path,
        "cost": paths.cost_path,
        "alignment": paths.alignment_path,
    }
    target = selected[artifact]
    payload = target.read_bytes()
    target.write_bytes(b"x" * len(payload))
    manifest_before = (tmp_path / "state/manifest.json").read_bytes()

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(project_path)

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert (tmp_path / "state/manifest.json").read_bytes() == manifest_before


def test_reader_rejects_selected_registry_that_removes_succeeded_voice_candidate(
    tmp_path,
):
    project_path, request, _, _, _ = _activate_fake_voice(
        tmp_path, include_caption=False
    )
    attempt = next(
        item
        for item in _manifest(tmp_path).attempts
        if item.attempt_id == request.attempt_id
    )
    base = AssetRegistrySnapshot.model_validate_json(
        (tmp_path / attempt.base_registry.path).read_bytes()
    )
    _select_resealed_registry(tmp_path, base)

    with pytest.raises(AiVideoError, match="candidate history"):
        load_production_project(project_path)


@pytest.mark.parametrize("mutation", ["delete", "mutate"])
def test_reader_reopens_succeeded_voice_base_registry(tmp_path, mutation):
    project_path, request, _, _, _ = _activate_fake_voice(
        tmp_path, include_caption=False
    )
    attempt = next(
        item
        for item in _manifest(tmp_path).attempts
        if item.attempt_id == request.attempt_id
    )
    base_path = tmp_path / attempt.base_registry.path
    if mutation == "delete":
        base_path.unlink()
    else:
        base_path.write_bytes(b"x" * base_path.stat().st_size)

    with pytest.raises(AiVideoError, match="candidate history"):
        load_production_project(project_path)


def test_reader_rejects_selected_registry_with_changed_voice_base_prefix(tmp_path):
    project_path, _, _, _, _ = _activate_fake_voice(tmp_path, include_caption=False)
    manifest = _manifest(tmp_path)
    registry = AssetRegistrySnapshot.model_validate_json(
        (tmp_path / manifest.active_registry.path).read_bytes()
    )
    first = registry.assets[0].model_copy(update={"usage_license": "changed"})
    _select_resealed_registry(
        tmp_path,
        registry.model_copy(update={"assets": (first, *registry.assets[1:])}),
    )

    with pytest.raises(AiVideoError, match="candidate history"):
        load_production_project(project_path)


def test_reader_rejects_tampered_voice_candidate_artifact_graph(tmp_path):
    project_path, request, _, _, _ = _activate_fake_voice(
        tmp_path, include_caption=False
    )
    manifest = _manifest(tmp_path)
    attempts = tuple(
        item.model_copy(update={"candidate_artifacts_hash": "f" * 64})
        if item.attempt_id == request.attempt_id
        else item
        for item in manifest.attempts
    )
    _write_manifest(tmp_path, manifest.model_copy(update={"attempts": attempts}))

    with pytest.raises(AiVideoError, match="candidate history"):
        load_production_project(project_path)


def test_reader_accepts_two_append_only_voice_candidates_without_writes(tmp_path):
    project_path = write_production_project(tmp_path)
    first, _, first_audio, first_captions = _append_fake_voice(
        tmp_path, attempt_id="reader-voice-1", include_caption=True
    )
    second, _, second_audio, second_captions = _append_fake_voice(
        tmp_path, attempt_id="reader-voice-2", include_caption=False
    )
    before = _tree_snapshot(tmp_path)

    loaded = load_production_project(project_path)

    assert {item.asset_id for item in loaded.registry.assets}.issuperset(
        {*first_audio, *first_captions, *second_audio, *second_captions}
    )
    assert {
        item.attempt_id
        for item in loaded.manifest.attempts
        if item.operation == "voice_generation"
    } == {first.attempt_id, second.attempt_id}
    assert _tree_snapshot(tmp_path) == before


def test_reader_rejects_voice_candidate_id_claimed_by_two_attempts(tmp_path):
    project_path = write_production_project(tmp_path)
    first, _, first_audio, _ = _append_fake_voice(
        tmp_path, attempt_id="reader-voice-1", include_caption=False
    )
    second, _, _, _ = _append_fake_voice(
        tmp_path, attempt_id="reader-voice-2", include_caption=False
    )
    manifest = _manifest(tmp_path)
    attempts = tuple(
        item.model_copy(update={"candidate_audio_asset_ids": first_audio})
        if item.attempt_id == second.attempt_id
        else item
        for item in manifest.attempts
    )
    _write_manifest(tmp_path, manifest.model_copy(update={"attempts": attempts}))

    with pytest.raises(AiVideoError, match="candidate history"):
        load_production_project(project_path)

    assert first.attempt_id != second.attempt_id


@pytest.mark.parametrize(
    "mutation",
    [
        "audio_metadata_source_kind",
        "audio_asset_inputs",
        "caption_source_kind",
        "caption_transcript",
        "caption_track_creation_receipt",
        "caption_track_source_provenance",
    ],
)
def test_reader_rejects_resealed_voice_asset_semantic_contradictions(
    tmp_path, mutation
):
    project_path, request, _, audio_ids, caption_ids = _activate_fake_voice(tmp_path)
    manifest = _manifest(tmp_path)
    registry = AssetRegistrySnapshot.model_validate_json(
        (tmp_path / manifest.active_registry.path).read_bytes()
    )
    audio = next(item for item in registry.assets if item.asset_id == audio_ids[0])
    caption = next(item for item in registry.assets if item.asset_id == caption_ids[0])
    if mutation == "audio_metadata_source_kind":
        assert audio.audio_metadata is not None
        replacement = audio.model_copy(
            update={
                "audio_metadata": audio.audio_metadata.model_copy(
                    update={
                        "source": audio.audio_metadata.source.model_copy(
                            update={"kind": AssetSourceKind.IMPORTED}
                        )
                    }
                )
            }
        )
    elif mutation == "audio_asset_inputs":
        replacement = audio.model_copy(
            update={
                "input_artifact_ids": ("story-main",),
                "input_fingerprint": "f" * 64,
            }
        )
    elif mutation == "caption_source_kind":
        replacement = caption.model_copy(
            update={"source_kind": AssetSourceKind.GENERATED}
        )
    else:
        track = CaptionTrack.model_validate_json(
            (tmp_path / caption.artifact_path).read_bytes()
        )
        track_updates = {
            "caption_transcript": {"transcript_hash": "f" * 64},
            "caption_track_creation_receipt": {
                "creation_receipt_id": "caption-result-forged"
            },
            "caption_track_source_provenance": {
                "source_provenance": (
                    SourceReference(
                        kind="derived", reference="alignment-forged-receipt"
                    ),
                )
            },
        }[mutation]
        changed = track.model_copy(
            update={
                **track_updates,
                "timing_fingerprint": "0" * 64,
                "content_hash": "0" * 64,
            }
        )
        changed = changed.model_copy(
            update={"timing_fingerprint": caption_timing_fingerprint(changed)}
        )
        changed = CaptionTrack.model_validate(
            seal_artifact(changed).model_dump(mode="python")
        )
        payload = _canonical_track_bytes(changed)
        digest = hashlib.sha256(payload).hexdigest()
        artifact_path = Path(f"assets/captions/{digest}.json")
        (tmp_path / artifact_path).write_bytes(payload)
        assert caption.caption_metadata is not None
        replacement = caption.model_copy(
            update={
                "artifact_path": artifact_path,
                "sha256": digest,
                "size_bytes": len(payload),
                "caption_metadata": caption.caption_metadata.model_copy(
                    update={
                        "transcript_hash": changed.transcript_hash,
                        "timing_fingerprint": changed.timing_fingerprint,
                    }
                ),
            }
        )
    _replace_selected_voice_asset(tmp_path, request.attempt_id, replacement)

    with pytest.raises(AiVideoError, match="voice evidence graph"):
        load_production_project(project_path)


def test_reader_verifies_selected_render_graph_exactly_without_rewrite(tmp_path):
    _, durable, _ = _activate_fake_render(tmp_path)
    before = _tree_snapshot(tmp_path)

    loaded = load_production_project(tmp_path / "project.yaml")

    assert loaded.render_state == durable.state
    assert loaded.manifest.active_render_state == durable.next_render_state
    assert _tree_snapshot(tmp_path) == before


def test_reader_verifies_p4_audio_caption_and_style_binding_set_without_rewrite(
    tmp_path,
):
    _, durable, _ = _activate_fake_render(tmp_path, p4=True)
    before = _tree_snapshot(tmp_path)

    loaded = load_production_project(tmp_path / "project.yaml")
    source = json.loads((tmp_path / durable.state.source_receipt.path).read_bytes())
    bundle_paths = {item.path.as_posix() for item in durable.state.source_bundle.assets}
    binding_paths = {
        *(item["materialized_path"] for item in source["asset_bindings"]),
        *(item["materialized_path"] for item in source["audio_bindings"]),
        *(item["materialized_path"] for item in source["caption_bindings"]),
        *(
            item["style_materialized_path"]
            for item in source["caption_bindings"]
            if item["style_materialized_path"] is not None
        ),
    }

    assert loaded.render_state == durable.state
    assert source["schema_version"] == "2.1"
    assert bundle_paths == binding_paths
    assert len(source["audio_bindings"]) == 1
    assert len(source["caption_bindings"]) == 1
    assert _tree_snapshot(tmp_path) == before


@pytest.mark.parametrize("mutation", ["text", "timing"])
def test_shared_project_state_verifier_rejects_resealed_caption_semantic_drift(
    tmp_path, mutation
):
    _, durable, _ = _activate_fake_render(tmp_path, p4=True)
    timeline = ResolvedTimeline.model_validate_json(
        (tmp_path / durable.state.timeline.path).read_bytes()
    )
    source = RendererSourceReceipt.model_validate_json(
        (tmp_path / durable.state.source_receipt.path).read_bytes()
    )
    binding = source.caption_bindings[0]
    track = CaptionTrack.model_validate_json(
        (tmp_path / binding.materialized_path).read_bytes()
    )
    segment = track.segments[0]
    changed_segment = segment.model_copy(
        update=(
            {"text": "different"}
            if mutation == "text"
            else {"start_sample": segment.start_sample + 1}
        )
    )
    changed = track.model_copy(
        update={
            "segments": (changed_segment, *track.segments[1:]),
            "timing_fingerprint": "0" * 64,
            "content_hash": "0" * 64,
        }
    )
    changed = changed.model_copy(
        update={"timing_fingerprint": caption_timing_fingerprint(changed)}
    )
    changed = CaptionTrack.model_validate(
        seal_artifact(changed).model_dump(mode="python")
    )
    payload = _canonical_track_bytes(changed)
    digest = hashlib.sha256(payload).hexdigest()
    changed_binding = binding.model_copy(
        update={
            "caption_asset_sha256": digest,
            "materialized_path": Path(f"assets/{digest}.json"),
        }
    )
    before = _tree_snapshot(tmp_path)

    assert not _render_source_payload_matches(
        payload,
        suffix=".json",
        role="caption",
        binding=changed_binding,
        timeline=timeline,
    )
    assert _tree_snapshot(tmp_path) == before


@pytest.mark.parametrize("binding_kind", ["audio", "caption", "caption_style"])
def test_reader_rejects_tampered_p4_bound_source_without_fallback(
    tmp_path, binding_kind
):
    _, durable, _ = _activate_fake_render(tmp_path, p4=True)
    source = json.loads((tmp_path / durable.state.source_receipt.path).read_bytes())
    caption = source["caption_bindings"][0]
    relative = {
        "audio": source["audio_bindings"][0]["materialized_path"],
        "caption": caption["materialized_path"],
        "caption_style": caption["style_materialized_path"],
    }[binding_kind]
    target = tmp_path / relative
    target.write_bytes(b"x" * target.stat().st_size)

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_reader_rejects_tampered_selected_render_output_without_fallback(tmp_path):
    _, durable, _ = _activate_fake_render(tmp_path)
    (tmp_path / durable.state.output.path).write_bytes(b"tampered")

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_reader_rejects_mixed_selected_render_pointer_identity(tmp_path):
    _, durable, _ = _activate_fake_render(tmp_path)
    manifest = _manifest(tmp_path)
    mixed = durable.next_render_state.model_copy(
        update={"revision": durable.next_render_state.revision + 1}
    )
    _write_manifest(
        tmp_path, manifest.model_copy(update={"active_render_state": mixed})
    )

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def _render_graph_path(durable, label: str) -> Path:
    state = durable.state
    return {
        "state": durable.next_render_state.path,
        "timeline": state.timeline.path,
        "index": state.source_bundle.index.path,
        "asset": state.source_bundle.assets[0].path,
        "source_receipt": state.source_receipt.path,
        "render_receipt": state.render_receipt.path,
        "output": state.output.path,
    }[label]


@pytest.mark.parametrize(
    "label",
    [
        "state",
        "timeline",
        "index",
        "asset",
        "source_receipt",
        "render_receipt",
        "output",
    ],
)
@pytest.mark.parametrize("outside", [False, True])
def test_reader_rejects_every_render_artifact_symlink(tmp_path, label, outside):
    _, durable, _ = _activate_fake_render(tmp_path)
    target = tmp_path / _render_graph_path(durable, label)
    payload = target.read_bytes()
    target.unlink()
    backing = (
        tmp_path.parent / f"{tmp_path.name}-{label}-outside.bin"
        if outside
        else tmp_path / f"contained-{label}.bin"
    )
    backing.write_bytes(payload)
    target.symlink_to(backing)

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_reader_rejects_render_artifact_inode_swap_between_stat_and_open(
    tmp_path, monkeypatch
):
    _, durable, _ = _activate_fake_render(tmp_path)
    target = tmp_path / durable.state.output.path
    payload = target.read_bytes()
    original_open = os.open
    swapped = False

    def swap_then_open(path, flags, *args, **kwargs):
        nonlocal swapped
        if path == target.name and kwargs.get("dir_fd") is not None and not swapped:
            swapped = True
            target.rename(target.with_name("detached-output.mp4"))
            target.write_bytes(payload)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", swap_then_open)

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
