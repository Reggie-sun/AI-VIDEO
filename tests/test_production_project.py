from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
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
from ai_video.production.dependency import (
    build_applied_dependency_evidence,
    build_dependency_graph,
    build_production_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
)
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
    DependencyLifecycle,
    DependencyEdge,
    DependencyGraphSnapshotPointer,
    DependencyNode,
    DependencyNodeKind,
    DependencyNodeState,
    DependencyReason,
    DependencySemanticRole,
    MeasuredAudioRenderMetadata,
    MeasuredRenderMetadata,
    EgressMetadata,
    EvidenceStrength,
    FinalAcceptanceReceipt,
    FinalAcceptanceReceiptPointer,
    FinalAcceptanceState,
    ProductionManifest,
    ProductionProject,
    QaLayer,
    QaVerdict,
    ProjectDependencyEvidence,
    ProjectSnapshotPointer,
    FingerprintContribution,
    RegistrySnapshotPointer,
    RegistryDependencyEvidence,
    RendererCheckReceipt,
    RendererIdentity,
    RendererKind,
    RendererSelectionReceipt,
    RendererSourceReceipt,
    RenderDependencyEvidence,
    RenderStateSnapshotPointer,
    ReviewEvidence,
    ReviewEvidencePointer,
    ReviewLayerState,
    ReviewLifecycle,
    ReviewReceipt,
    ReviewReceiptPointer,
    ReviewRequest,
    ReviewRequestPointer,
    ResolvedTimeline,
    ResolvedVisualSpan,
    SourceReference,
    StateCommitAttempt,
    StateCommitStatus,
    TechnicalReviewContext,
    TechnicalReviewWindow,
    ToolIdentity,
    canonical_project_snapshot_path,
    canonical_registry_snapshot_path,
)
from ai_video.production.paths import (
    canonical_dependency_graph_snapshot_path,
    canonical_final_acceptance_receipt_path,
    canonical_render_state_path,
    canonical_review_evidence_path,
    canonical_review_receipt_path,
    canonical_review_request_path,
)
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import (
    ActivateRenderStateRequest,
    BeginRenderAttemptRequest,
    PreparedArtifact,
    _canonical_json_bytes,
    prepare_dependency_graph_transition,
)
from ai_video.production.project import (
    _render_source_payload_matches,
    _verify_dependency_project_evidence,
    load_production_project_candidate,
)
from ai_video.production._project_dependency_evidence import (
    verify_active_versioned_artifact_evidence,
)
from ai_video.production._image_project_reader import verify_active_image_evidence
from production_project_factory import (
    add_p6_policy_to_p7_project,
    append_p7_committed_candidate,
    attach_p5_dependency_transition,
    load_revision_two_models,
    make_manifest_23_project,
    make_p7_committed_project,
    make_p4_composition_fixture,
    make_p8_video_evidence,
    make_voice_activation_request,
    make_voice_preview_and_authorization,
    make_voice_request,
    mutate_p7_evidence,
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


def _select_manifest_23_graph(root: Path, graph, states) -> ProductionManifest:
    payload = (
        json.dumps(
            graph.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    path = root / canonical_dependency_graph_snapshot_path(graph.revision_id)
    path.write_bytes(payload)
    pointer = DependencyGraphSnapshotPointer(
        revision_id=graph.revision_id,
        content_hash=graph.content_hash,
        path=path.relative_to(root),
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    manifest = _manifest(root).model_copy(
        update={
            "schema_version": "2.3",
            "manifest_revision": _manifest(root).manifest_revision + 1,
            "active_dependency_graph": pointer,
            "dependency_states": tuple(sorted(states, key=lambda state: state.node_id)),
        }
    )
    _write_manifest(root, manifest)
    return manifest


def _commit_revision_two(
    root: Path, *, attempt_id: str = "loader-revision-two"
) -> ProductionProject:
    manifest = _manifest(root)
    project, registry = load_revision_two_models(root)
    request = prepare_project_registry_commit(
        manifest=manifest,
        project=project,
        registry=registry,
        attempt_id=attempt_id,
    )
    if manifest.schema_version == "2.3":
        request, _ = attach_p5_dependency_transition(root, request)
    ProductionStateCommitter(root).commit(request)
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
    root: Path,
    attempt_id: str = "reader-render",
    *,
    p4: bool = False,
    initialize: bool = True,
    dependency_inputs=None,
):
    if dependency_inputs is not None:
        loaded = load_production_project(root / "project.yaml")
        spec = dependency_inputs.composition_spec
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
        for track in spec.caption_tracks:
            if track.style_reference is not None:
                sources[track.style_reference.artifact_id] = (
                    root / track.style_reference.path
                )
        before = loaded.manifest
    elif p4:
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
        if initialize:
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
    if not p4 and dependency_inputs is None:
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
                    if p4 or dependency_inputs is not None
                    else None
                ),
            ),
            decoded_frame_fingerprint="2" * 64,
            decoded_audio_fingerprint=(
                "3" * 64 if p4 or dependency_inputs is not None else None
            ),
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
    if dependency_inputs is not None:
        candidate_bundle = loaded.model_copy(
            update={
                "manifest": begun,
                "dependency_graph": None,
                "render_state": None,
            }
        )
        graph = build_production_dependency_graph(
            replace(
                dependency_inputs,
                project=candidate_bundle,
                voice_requests=(),
            )
        )
        desired = desired_fingerprints(graph)
        states = []
        for node in graph.nodes:
            if node.kind is DependencyNodeKind.CREATIVE_ARTIFACT:
                evidence = ProjectDependencyEvidence(
                    owner="project_snapshot",
                    pointer=request.current_project,
                    artifact_id=node.artifact_id,
                    artifact_fingerprint=desired[node.node_id],
                )
            elif node.kind is DependencyNodeKind.ASSET:
                evidence = RegistryDependencyEvidence(
                    owner="registry_snapshot",
                    pointer=request.current_registry,
                    artifact_id=node.artifact_id,
                    artifact_fingerprint=desired[node.node_id],
                )
            else:
                evidence = RenderDependencyEvidence(
                    owner="render_state",
                    pointer=request.next_render_state,
                    artifact_id=node.artifact_id,
                    artifact_fingerprint=desired[node.node_id],
                )
            states.append(
                DependencyNodeState(
                    node_id=node.node_id,
                    graph_revision_id=graph.revision_id,
                    desired_fingerprint=desired[node.node_id],
                    applied_fingerprint=desired[node.node_id],
                    lifecycle=DependencyLifecycle.FRESH,
                    applied_evidence=evidence,
                )
            )
        transition = prepare_dependency_graph_transition(
            expected_manifest_revision=request.expected_manifest_revision,
            base_dependency_graph=begun.active_dependency_graph,
            candidate_graph=graph,
            candidate_dependency_states=tuple(states),
            expected_desired_fingerprints=desired,
        )
        graph_payload = _canonical_json_bytes(graph)
        graph_artifact = PreparedArtifact(
            transition.candidate_dependency_graph.path,
            graph_payload,
            hashlib.sha256(graph_payload).hexdigest(),
        )
        request = replace(
            request,
            artifacts=tuple(
                sorted(
                    (*request.artifacts, graph_artifact),
                    key=lambda item: item.relative_path.as_posix(),
                )
            ),
            dependency_graph_transition=transition,
        )
    activated = committer.activate_render_state(request)
    return activated, durable, request


def _activate_fake_voice(root: Path, *, include_caption: bool = True):
    project_path = write_production_project(root)
    request, committed, audio_ids, caption_ids = _append_fake_voice(
        root, attempt_id="reader-voice", include_caption=include_caption
    )
    return project_path, request, committed, audio_ids, caption_ids


def _activate_manifest_25_graph_voice(root: Path):
    project_path = write_production_project(root)
    make_manifest_23_project(root)
    _write_manifest(
        root,
        _manifest(root).model_copy(update={"schema_version": "2.5"}),
    )
    request = make_voice_request(root, attempt_id="reader-voice-graph-25")
    preview, authorization = make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(root)
    writer.begin_voice_generation(
        request,
        preview,
        authorization,
        dependency_transition_preparer_available=True,
    )
    writer.record_voice_submit_intent(request, preview, authorization)
    activation, audio_ids = make_voice_activation_request(
        root,
        request,
        authorization,
        expected_manifest_revision=_manifest(root).manifest_revision,
        include_caption=True,
    )
    activation, _ = attach_p5_dependency_transition(root, activation)
    committed = writer.activate_voice_assets(
        activation,
        audio_asset_ids=audio_ids,
        caption_asset_ids=(f"caption-{request.attempt_id}",),
    )
    return project_path, request, committed


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


def _select_p7_later_voice_caption_registry_extension(
    root: Path,
    fixture: dict[str, object],
    *,
    changed_prefix: bool = False,
) -> tuple[RegistrySnapshotPointer, tuple[str, str]]:
    candidate = fixture["candidate_project"].registry
    voice = next(item for item in candidate.assets if item.asset_id == "voice-dialogue")
    caption = next(
        item for item in candidate.assets if item.asset_id == "caption-asset-1"
    )
    voice_extension = voice.model_copy(
        update={
            "asset_id": "voice-later-phase",
            "creation_receipt_id": "receipt-voice-later-phase",
        }
    )
    caption_extension = caption.model_copy(
        update={
            "asset_id": "caption-later-phase",
            "creation_receipt_id": "receipt-caption-later-phase",
        }
    )
    prefix = candidate.assets
    if changed_prefix:
        prefix = (
            prefix[0].model_copy(update={"usage_license": "changed-later-prefix"}),
            *prefix[1:],
        )
    provisional = candidate.model_copy(
        update={
            "revision_id": "0" * 64,
            "content_hash": "0" * 64,
            "assets": (*prefix, voice_extension, caption_extension),
        }
    )
    digest = registry_semantic_sha256(provisional)
    extended = provisional.model_copy(
        update={"revision_id": digest, "content_hash": digest}
    )
    payload = extended.model_dump_json(indent=2).encode("utf-8")
    path = canonical_registry_snapshot_path(digest)
    (root / path).write_bytes(payload)
    pointer = RegistrySnapshotPointer(
        path=path,
        revision_id=digest,
        content_hash=digest,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    manifest = _manifest(root)
    _write_manifest(
        root,
        manifest.model_copy(
            update={
                "manifest_revision": manifest.manifest_revision + 1,
                "active_registry": pointer,
            }
        ),
    )
    return pointer, (voice_extension.asset_id, caption_extension.asset_id)


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


def test_reader_reopens_manifest_25_voice_candidate_dependency_graph(tmp_path):
    project_path, request, committed = _activate_manifest_25_graph_voice(tmp_path)
    before = _tree_snapshot(tmp_path)

    loaded = load_production_project(project_path)

    attempt = next(
        item for item in loaded.manifest.attempts if item.attempt_id == request.attempt_id
    )
    assert attempt.candidate_dependency_graph == committed.active_dependency_graph
    assert loaded.dependency_graph is not None
    assert (
        loaded.dependency_graph.revision_id
        == attempt.candidate_dependency_graph.revision_id
    )
    assert _tree_snapshot(tmp_path) == before


def test_reader_rejects_tampered_manifest_25_voice_candidate_graph_pointer(tmp_path):
    project_path, request, committed = _activate_manifest_25_graph_voice(tmp_path)
    attempt = next(
        item for item in committed.attempts if item.attempt_id == request.attempt_id
    )
    assert attempt.candidate_dependency_graph is not None
    forged_attempt = attempt.model_copy(
        update={
            "candidate_dependency_graph": attempt.candidate_dependency_graph.model_copy(
                update={"file_sha256": "f" * 64}
            )
        }
    )
    _write_manifest(
        tmp_path,
        committed.model_copy(
            update={
                "attempts": tuple(
                    forged_attempt if item.attempt_id == request.attempt_id else item
                    for item in committed.attempts
                )
            }
        ),
    )

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(project_path)

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert exc_info.value.user_message == "Active P4 voice candidate history is invalid."
    assert exc_info.value.technical_detail == "file hash mismatch"


@pytest.mark.parametrize(
    ("mutation", "expected_detail"),
    (
        ("bytes", "file hash mismatch"),
        ("semantic_identity", "revision_id="),
    ),
)
def test_reader_rejects_tampered_manifest_25_voice_candidate_graph(
    tmp_path,
    mutation,
    expected_detail,
):
    project_path, request, committed = _activate_manifest_25_graph_voice(tmp_path)
    attempt = next(
        item for item in committed.attempts if item.attempt_id == request.attempt_id
    )
    assert attempt.candidate_dependency_graph is not None
    graph_path = tmp_path / attempt.candidate_dependency_graph.path
    if mutation == "bytes":
        graph_path.write_bytes(graph_path.read_bytes() + b" ")
    else:
        graph_data = json.loads(graph_path.read_bytes())
        graph_data["nodes"][0]["contributions"][0]["fingerprint"] = "f" * 64
        graph_payload = (
            json.dumps(
                graph_data,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        graph_path.write_bytes(graph_payload)
        forged_pointer = attempt.candidate_dependency_graph.model_copy(
            update={"file_sha256": hashlib.sha256(graph_payload).hexdigest()}
        )
        forged_attempt = attempt.model_copy(
            update={"candidate_dependency_graph": forged_pointer}
        )
        _write_manifest(
            tmp_path,
            committed.model_copy(
                update={
                    "active_dependency_graph": forged_pointer,
                    "attempts": tuple(
                        forged_attempt
                        if item.attempt_id == request.attempt_id
                        else item
                        for item in committed.attempts
                    ),
                }
            ),
        )

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(project_path)

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert exc_info.value.user_message == "Active P4 voice candidate history is invalid."
    assert expected_detail in (exc_info.value.technical_detail or "")


@pytest.fixture
def p7_committed_project(tmp_path):
    return make_p7_committed_project(tmp_path)


def test_loader_reopens_selected_p7_image_receipt_and_exact_png(
    tmp_path, p7_committed_project, monkeypatch
):
    before = _tree_snapshot(tmp_path)

    def reject_network(*_args, **_kwargs):
        raise AssertionError("read-only P7 project load attempted network access")

    monkeypatch.setattr(socket, "create_connection", reject_network)
    loaded = load_production_project(p7_committed_project["project_path"])
    image = next(
        item
        for item in loaded.registry.assets
        if item.asset_id == p7_committed_project["image_record"].asset_id
    )

    assert image.source_kind is AssetSourceKind.GENERATED
    assert image.creation_receipt_id == p7_committed_project["receipt"].content_hash
    assert _tree_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "artifact_key",
    ("preview_path", "authorization_path", "submit_intent_path"),
)
@pytest.mark.parametrize("mutation", ("missing", "tampered"))
def test_loader_rejects_missing_or_tampered_p7_submit_audit_evidence(
    tmp_path, p7_committed_project, artifact_key, mutation
):
    artifact_path = tmp_path / p7_committed_project[artifact_key]
    if mutation == "missing":
        artifact_path.unlink()
    else:
        artifact_path.write_bytes(artifact_path.read_bytes() + b" ")
    before = _tree_snapshot(tmp_path)

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(p7_committed_project["project_path"])

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert _tree_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "mutation",
    [
        "receipt_hash",
        "png_bytes",
        "request_id",
        "result_request_id",
        "candidate_pointer",
    ],
)
def test_loader_rejects_tampered_p7_evidence(
    tmp_path, p7_committed_project, mutation
):
    mutate_p7_evidence(tmp_path, p7_committed_project, mutation)

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(p7_committed_project["project_path"])

    assert exc_info.value.retryable is False


def test_loader_rejects_tampered_p7_candidate_artifacts_hash(
    tmp_path, p7_committed_project
):
    mutate_p7_evidence(
        tmp_path, p7_committed_project, "candidate_artifacts_hash"
    )

    with pytest.raises(AiVideoError, match="candidate history"):
        load_production_project(p7_committed_project["project_path"])


def test_loader_rejects_noncanonical_p7_candidate_shot_reference(tmp_path):
    fixture = make_p7_committed_project(
        tmp_path, noncanonical_candidate_shot_path=True
    )

    with pytest.raises(AiVideoError, match="candidate history") as exc_info:
        load_production_project(fixture["project_path"])

    assert "not canonical" in (exc_info.value.technical_detail or "")


def test_p7_fixture_preserves_base_and_candidate_shot_revisions(
    tmp_path, p7_committed_project
):
    base_path = tmp_path / "creative/shots/shot-1.yaml"
    candidate_shot = p7_committed_project["candidate_project"].shots[0]
    candidate_path = tmp_path / Path(
        "creative/shots/"
        f"shot.{candidate_shot.revision}.{candidate_shot.content_hash}.yaml"
    )

    base_payload = yaml.safe_load(base_path.read_text(encoding="utf-8"))
    candidate_payload = yaml.safe_load(candidate_path.read_text(encoding="utf-8"))
    assert base_payload["revision"] == candidate_shot.revision - 1
    assert candidate_payload["revision"] == candidate_shot.revision
    assert base_path.read_bytes() != candidate_path.read_bytes()


def test_loader_reopens_exact_p7_base_registry(tmp_path, p7_committed_project):
    attempt = _manifest(tmp_path).attempts[0]
    base_path = tmp_path / attempt.base_registry.path
    base_path.write_bytes(base_path.read_bytes() + b" ")

    with pytest.raises(AiVideoError, match="candidate history"):
        load_production_project(p7_committed_project["project_path"])


def _write_p7_historical_projection_states(root: Path, fixture, states) -> None:
    states_payload = json.dumps(
        [item.model_dump(mode="json") for item in states],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    attempt = fixture["attempt"].model_copy(
        update={
            "candidate_dependency_states_hash": hashlib.sha256(
                states_payload
            ).hexdigest()
        }
    )
    _write_manifest(
        root,
        fixture["manifest"].model_copy(
            update={"dependency_states": states, "attempts": (attempt,)}
        ),
    )


def _p7_historical_projection_fixture(root: Path):
    fixture = make_p7_committed_project(root)
    candidate_inputs = fixture["candidate_inputs"]
    candidate_graph = fixture["candidate_graph"]
    request = fixture["request"]
    manifest = fixture["manifest"]
    base_project = load_production_project_candidate(
        root,
        manifest,
        request.base_project.path,
        request.base_registry.path,
    )
    base_project = base_project.model_copy(
        update={
            "manifest": manifest.model_copy(
                update={
                    "active_project": request.base_project,
                    "active_registry": request.base_registry,
                    "active_dependency_graph": request.base_dependency_graph,
                }
            )
        }
    )
    base_inputs = replace(candidate_inputs, project=base_project)
    base_graph = build_production_dependency_graph(base_inputs)
    base_applied = build_applied_dependency_evidence(base_inputs, None)
    base_states = resolve_dependency_state(base_graph, base_applied).states
    candidate_states = resolve_dependency_state(candidate_graph, base_states).states
    _write_p7_historical_projection_states(root, fixture, candidate_states)
    return fixture, candidate_graph, candidate_states


def test_loader_verifies_historical_shot_projection_evidence_after_p7_replacement(
    tmp_path,
):
    fixture, _, _ = _p7_historical_projection_fixture(tmp_path)

    loaded = load_production_project(fixture["project_path"])
    target = {
        state.node_id: state
        for state in loaded.manifest.dependency_states
        if state.node_id.startswith("creative:shot:shot-1:")
    }

    assert target["creative:shot:shot-1:composition"].lifecycle is DependencyLifecycle.FRESH
    assert target["creative:shot:shot-1:voice"].lifecycle is DependencyLifecycle.FRESH
    assert target["creative:shot:shot-1:visual"].lifecycle is DependencyLifecycle.STALE


def test_loader_rejects_forged_historical_shot_projection_fingerprint(tmp_path):
    fixture, _, states = _p7_historical_projection_fixture(tmp_path)
    visual = next(
        state
        for state in states
        if state.node_id == "creative:shot:shot-1:visual"
    )
    forged_fingerprint = "f" * 64
    assert visual.applied_evidence is not None
    forged = visual.model_copy(
        update={
            "applied_fingerprint": forged_fingerprint,
            "applied_evidence": visual.applied_evidence.model_copy(
                update={"artifact_fingerprint": forged_fingerprint}
            ),
        }
    )
    forged_states = tuple(
        forged if state.node_id == forged.node_id else state for state in states
    )
    _write_p7_historical_projection_states(tmp_path, fixture, forged_states)

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(fixture["project_path"])

    assert "Historical Shot dependency evidence" in (
        exc_info.value.technical_detail or exc_info.value.user_message
    )


def test_historical_shot_projection_rejects_changed_current_incoming(tmp_path):
    fixture, graph, _ = _p7_historical_projection_fixture(tmp_path)
    loaded = load_production_project(fixture["project_path"])
    state = next(
        item
        for item in loaded.manifest.dependency_states
        if item.node_id == "creative:shot:shot-1:visual"
    )
    node = next(item for item in graph.nodes if item.node_id == state.node_id)
    scene = next(
        item
        for item in graph.nodes
        if item.node_id.startswith("creative:scene:")
    )
    changed_scene = scene.model_copy(
        update={
            "contributions": tuple(
                item.model_copy(update={"fingerprint": "f" * 64})
                for item in scene.contributions
            )
        }
    )
    changed_graph = build_dependency_graph(
        tuple(
            changed_scene if item.node_id == scene.node_id else item
            for item in graph.nodes
        ),
        graph.edges,
    )
    changed_desired = desired_fingerprints(changed_graph)
    changed_state = state.model_copy(
        update={
            "graph_revision_id": changed_graph.revision_id,
            "desired_fingerprint": changed_desired[state.node_id],
        }
    )
    assert changed_state.applied_evidence is not None

    with pytest.raises(AiVideoError, match="Historical Shot dependency evidence"):
        _verify_dependency_project_evidence(
            loaded,
            changed_state.applied_evidence,
            node,
            (changed_graph, changed_state),
        )


@pytest.mark.parametrize("revision_offset", [0, 1])
def test_historical_shot_projection_rejects_nonhistorical_project_evidence(
    tmp_path, revision_offset
):
    fixture, graph, _ = _p7_historical_projection_fixture(tmp_path)
    loaded = load_production_project(fixture["project_path"])
    request = fixture["request"]
    origin = load_production_project_candidate(
        tmp_path,
        loaded.manifest,
        request.base_project.path,
        request.base_registry.path,
    )
    nonhistorical_project = seal_artifact(
        origin.project.model_copy(
            update={
                "revision": loaded.project.revision + revision_offset,
                "content_hash": "0" * 64,
            }
        )
    )
    nonhistorical_bytes = yaml.safe_dump(
        nonhistorical_project.model_dump(mode="json"),
        sort_keys=True,
        allow_unicode=True,
    ).encode("utf-8")
    nonhistorical_path = canonical_project_snapshot_path(
        nonhistorical_project.revision, nonhistorical_project.content_hash
    )
    (tmp_path / nonhistorical_path).write_bytes(nonhistorical_bytes)
    nonhistorical_pointer = ProjectSnapshotPointer(
        path=nonhistorical_path,
        revision=nonhistorical_project.revision,
        content_hash=nonhistorical_project.content_hash,
        file_sha256=hashlib.sha256(nonhistorical_bytes).hexdigest(),
    )
    state = next(
        item
        for item in loaded.manifest.dependency_states
        if item.node_id == "creative:shot:shot-1:visual"
    )
    node = next(item for item in graph.nodes if item.node_id == state.node_id)
    assert state.applied_evidence is not None
    nonhistorical_evidence = state.applied_evidence.model_copy(
        update={"pointer": nonhistorical_pointer}
    )
    nonhistorical_state = state.model_copy(
        update={"applied_evidence": nonhistorical_evidence}
    )

    with pytest.raises(AiVideoError, match="chronology"):
        _verify_dependency_project_evidence(
            loaded,
            nonhistorical_evidence,
            node,
            (graph, nonhistorical_state),
        )


@pytest.mark.parametrize("revision_offset", [0, 1])
def test_reader_rejects_character_evidence_from_future_or_alternate_project(
    tmp_path, revision_offset
):
    graph = make_manifest_23_project(tmp_path)
    loaded = load_production_project(tmp_path / "project.yaml")
    state = next(
        item
        for item in loaded.manifest.dependency_states
        if item.node_id.startswith("creative:character:")
    )
    assert state.applied_evidence is not None
    forged_project = seal_artifact(
        loaded.project.model_copy(
            update={
                "revision": loaded.project.revision + revision_offset,
                "content_hash": "0" * 64,
                "creation_receipt_id": "forged-character-project",
            }
        )
    )
    payload = yaml.safe_dump(
        forged_project.model_dump(mode="json"),
        sort_keys=True,
        allow_unicode=True,
    ).encode("utf-8")
    path = canonical_project_snapshot_path(
        forged_project.revision, forged_project.content_hash
    )
    (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / path).write_bytes(payload)
    pointer = ProjectSnapshotPointer(
        path=path,
        revision=forged_project.revision,
        content_hash=forged_project.content_hash,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    forged_state = state.model_copy(
        update={
            "applied_evidence": state.applied_evidence.model_copy(
                update={"pointer": pointer}
            )
        }
    )
    states = tuple(
        forged_state if item.node_id == state.node_id else item
        for item in loaded.manifest.dependency_states
    )
    _write_manifest(
        tmp_path, loaded.manifest.model_copy(update={"dependency_states": states})
    )

    with pytest.raises(AiVideoError, match="state binding"):
        load_production_project(tmp_path / "project.yaml")

    assert any(item.node_id == state.node_id for item in graph.nodes)


def test_character_evidence_rejects_same_revision_different_content(tmp_path):
    graph = make_manifest_23_project(tmp_path)
    loaded = load_production_project(tmp_path / "project.yaml")
    state = next(
        item
        for item in loaded.manifest.dependency_states
        if item.node_id.startswith("creative:character:")
    )
    node = next(item for item in graph.nodes if item.node_id == state.node_id)
    assert state.applied_evidence is not None
    current = loaded.characters[0]
    forged_origin = seal_artifact(
        current.model_copy(
            update={
                "content_hash": "0" * 64,
                "appearance_bible": current.appearance_bible + " forged",
            }
        )
    )

    with pytest.raises(AiVideoError, match="state binding"):
        verify_active_versioned_artifact_evidence(
            loaded,
            state.applied_evidence,
            node,
            graph,
            state,
            forged_origin,
            current,
            graph,
        )


def test_loader_rejects_unrelated_p7_candidate_registry_suffix(tmp_path):
    fixture = make_p7_committed_project(
        tmp_path, unrelated_candidate_suffix=True
    )

    with pytest.raises(AiVideoError, match="candidate history"):
        load_production_project(fixture["project_path"])


def test_loader_rejects_changed_p7_candidate_registry_prefix(tmp_path):
    fixture = make_p7_committed_project(
        tmp_path, changed_candidate_prefix=True
    )

    with pytest.raises(AiVideoError, match="candidate history"):
        load_production_project(fixture["project_path"])


def test_loader_accepts_p7_image_history_after_voice_registry_extension(tmp_path):
    fixture = make_p7_committed_project(tmp_path)
    image_attempt = fixture["attempt"]
    pointer, extension_ids = _select_p7_later_voice_caption_registry_extension(
        tmp_path, fixture
    )
    before = _tree_snapshot(tmp_path)

    loaded = load_production_project(fixture["project_path"])
    candidate_registry = AssetRegistrySnapshot.model_validate_json(
        (tmp_path / image_attempt.candidate_registry.path).read_bytes()
    )

    assert loaded.manifest.active_project == image_attempt.candidate_project
    assert pointer != image_attempt.candidate_registry
    assert loaded.registry.assets[: len(candidate_registry.assets)] == (
        candidate_registry.assets
    )
    assert {item.asset_id for item in loaded.registry.assets}.issuperset(
        {*extension_ids, fixture["image_record"].asset_id}
    )
    assert _tree_snapshot(tmp_path) == before


def test_image_reader_accepts_active_p7_image_after_later_manifest_28_project(
    tmp_path,
):
    fixture = make_p7_committed_project(tmp_path)
    loaded = load_production_project(fixture["project_path"])
    later_project = seal_artifact(
        loaded.project.model_copy(
            update={
                "revision": loaded.project.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": "unrelated-later-project-activation",
            }
        )
    )
    later_bytes = yaml.safe_dump(
        later_project.model_dump(mode="json"),
        sort_keys=True,
        allow_unicode=True,
    ).encode("utf-8")
    later_path = canonical_project_snapshot_path(
        later_project.revision, later_project.content_hash
    )
    (tmp_path / later_path).write_bytes(later_bytes)
    later_pointer = ProjectSnapshotPointer(
        path=later_path,
        revision=later_project.revision,
        content_hash=later_project.content_hash,
        file_sha256=hashlib.sha256(later_bytes).hexdigest(),
    )
    advanced = loaded.model_copy(
        update={
            "project": later_project,
            "manifest": loaded.manifest.model_copy(
                update={
                    "schema_version": "2.8",
                    "manifest_revision": loaded.manifest.manifest_revision + 1,
                    "active_project": later_pointer,
                }
            ),
        }
    )

    verify_active_image_evidence(advanced)


def test_p7_reader_rejects_changed_candidate_prefix_after_voice_registry_extension(
    tmp_path,
):
    fixture = make_p7_committed_project(tmp_path)
    pointer, _ = _select_p7_later_voice_caption_registry_extension(
        tmp_path,
        fixture,
        changed_prefix=True,
    )
    assert pointer != fixture["attempt"].candidate_registry

    with pytest.raises(AiVideoError, match="candidate history"):
        load_production_project(fixture["project_path"])


@pytest.mark.parametrize(
    "mutation",
    [
        "stale_creative_revision",
        "stale_creative_hash",
        "wrong_membership",
        "wrong_reference_hash",
    ],
)
def test_loader_rejects_p7_reference_not_bound_to_base_project(
    tmp_path, mutation
):
    fixture = make_p7_committed_project(
        tmp_path, reference_mutation=mutation
    )

    with pytest.raises(AiVideoError, match="reference"):
        load_production_project(fixture["project_path"])


def test_loader_rejects_p7_style_reference_even_when_scene_backed(tmp_path):
    fixture = make_p7_committed_project(
        tmp_path, reference_mutation="style_scene_binding"
    )

    with pytest.raises(AiVideoError, match="reference"):
        load_production_project(fixture["project_path"])


def test_loader_accepts_two_sequential_selected_p7_candidates_without_writes(
    tmp_path,
):
    first = make_p7_committed_project(tmp_path)
    first_asset_id = first["image_record"].asset_id
    fixture = append_p7_committed_candidate(tmp_path, first)
    before = _tree_snapshot(tmp_path)

    loaded = load_production_project(fixture["project_path"])

    assert {first_asset_id, fixture["image_record"].asset_id}.issubset(
        {item.asset_id for item in loaded.registry.assets}
    )
    assert len(
        [
            item
            for item in loaded.manifest.attempts
            if item.operation == "image_generation"
        ]
    ) == 2
    assert _tree_snapshot(tmp_path) == before


def test_loader_rejects_old_image_placed_in_another_shot_after_replacement(
    tmp_path,
):
    first = make_p7_committed_project(tmp_path)
    fixture = append_p7_committed_candidate(
        tmp_path,
        first,
        target_shot_id="shot-1",
        extra_old_placement_shot_id="shot-2",
    )
    manifest_path = tmp_path / "state/manifest.json"
    before = manifest_path.read_bytes()

    with pytest.raises(AiVideoError) as load_error:
        load_production_project(fixture["project_path"])
    with pytest.raises(AiVideoError) as exc_info:
        ProductionStateCommitter(tmp_path).recover()

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert "placement provenance" in (load_error.value.technical_detail or "")
    assert manifest_path.read_bytes() == before


def test_loader_reopens_first_base_registry_in_two_p7_candidate_history(
    tmp_path,
):
    first = make_p7_committed_project(tmp_path)
    fixture = append_p7_committed_candidate(tmp_path, first)
    first_attempt = _manifest(tmp_path).attempts[0]
    base_path = tmp_path / first_attempt.base_registry.path
    base_path.write_bytes(base_path.read_bytes() + b" ")

    with pytest.raises(AiVideoError, match="candidate history"):
        load_production_project(fixture["project_path"])


def test_loader_ignores_newer_p7_receipt_decoy(tmp_path, p7_committed_project):
    decoy = tmp_path / "state/images/receipts" / f"{'f' * 64}.json"
    decoy.write_text('{"decoy":true}\n', encoding="utf-8")
    decoy.touch()
    before = _tree_snapshot(tmp_path)

    loaded = load_production_project(p7_committed_project["project_path"])

    assert p7_committed_project["image_record"].asset_id in loaded.asset_paths
    assert _tree_snapshot(tmp_path) == before


def _write_p6_artifact(root: Path, path: Path, artifact) -> str:
    payload = _canonical_json_bytes(artifact)
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _make_complete_p6_p7_project(root: Path) -> dict[str, object]:
    fixture = make_p7_committed_project(root)
    image_manifest = _manifest(root)
    image_attempts = image_manifest.attempts
    _write_manifest(
        root,
        image_manifest.model_copy(
            update={"schema_version": "2.3", "attempts": ()}
        ),
    )
    request = fixture["request"]
    image_record = fixture["image_record"]
    inputs = fixture["candidate_inputs"]
    spec = inputs.composition_spec
    spec = seal_artifact(
        spec.model_copy(
            update={
                "revision": spec.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": fixture["receipt"].content_hash,
                "layers": tuple(
                    item.model_copy(update={"asset_id": image_record.asset_id})
                    if item.shot_id == request.target_shot_id
                    and item.asset_role == request.target_asset_role
                    else item
                    for item in spec.layers
                ),
            }
        )
    )
    rendered, _, _ = _activate_fake_render(
        root,
        attempt_id="reader-p6-p7-render",
        initialize=False,
        dependency_inputs=replace(inputs, composition_spec=spec),
    )
    _write_manifest(
        root,
        rendered.model_copy(
            update={
                "schema_version": "2.5",
                "attempts": (*image_attempts, *rendered.attempts),
            }
        ),
    )
    add_p6_policy_to_p7_project(root)
    manifest = _manifest(root)
    loaded = load_production_project(fixture["project_path"])
    render = loaded.render_state
    assert render is not None
    assert manifest.active_qa_policy is not None
    assert manifest.active_dependency_graph is not None

    dependency_states_hash = canonical_sha256(
        {
            "dependency_states": [
                item.model_dump(mode="json")
                for item in manifest.dependency_states
            ]
        }
    )
    tool = ToolIdentity(name="video-analysis", version="1")
    review_request = seal_artifact(
        ReviewRequest(
            artifact_id="review-request-p6-p7",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id="review-request-p6-p7",
            source_provenance=(
                SourceReference(kind="derived", reference="p6-p7-reader-fixture"),
            ),
            request_id="review-request-p6-p7",
            base_manifest_revision=manifest.manifest_revision,
            dependency_graph=manifest.active_dependency_graph,
            dependency_states_hash=dependency_states_hash,
            render_state=manifest.active_render_state,
            render_output_sha256=render.output.file_sha256,
            timeline_fingerprint=render.timeline_fingerprint,
            qa_policy=manifest.active_qa_policy,
            requested_layers=(QaLayer.TECHNICAL,),
            evidence_tool_identities=(tool,),
            technical_context=TechnicalReviewContext(
                render_output_sha256=render.output.file_sha256,
                timeline_fingerprint=render.timeline_fingerprint,
                windows=(
                    TechnicalReviewWindow(
                        shot_id=request.target_shot_id,
                        visual_strategy=next(
                            item.visual_strategy
                            for item in loaded.shots
                            if item.shot_id == request.target_shot_id
                        ),
                        start_frame=0,
                        end_frame_exclusive=1,
                        expects_audio=True,
                        visual_span_ids=("layer-shot-1",),
                    ),
                ),
                measurement_contract_version="1",
            ),
        )
    )
    request_path = canonical_review_request_path(review_request.content_hash)
    request_file_hash = _write_p6_artifact(root, request_path, review_request)
    request_pointer = ReviewRequestPointer(
        path=request_path,
        request_id=review_request.request_id,
        content_hash=review_request.content_hash,
        file_sha256=request_file_hash,
    )
    evidence = seal_artifact(
        ReviewEvidence(
            artifact_id="technical-evidence-p6-p7",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id="technical-evidence-p6-p7",
            source_provenance=(
                SourceReference(kind="derived", reference="video-analysis"),
            ),
            evidence_id="technical-evidence-p6-p7",
            layer=QaLayer.TECHNICAL,
            strength=EvidenceStrength.MEASURED,
            render_output_sha256=render.output.file_sha256,
            timeline_fingerprint=render.timeline_fingerprint,
            dependency_graph_revision_id=manifest.active_dependency_graph.revision_id,
            tool_identity=tool,
            measurement_contract_version="1",
            subject_ids=(request.target_shot_id,),
            measured_payload={"coverage_complete": True, "issue_count": 0},
        )
    )
    evidence_path = canonical_review_evidence_path(evidence.content_hash)
    evidence_file_hash = _write_p6_artifact(root, evidence_path, evidence)
    evidence_pointer = ReviewEvidencePointer(
        path=evidence_path,
        evidence_id=evidence.evidence_id,
        layer=evidence.layer,
        strength=evidence.strength,
        content_hash=evidence.content_hash,
        file_sha256=evidence_file_hash,
    )
    receipt = seal_artifact(
        ReviewReceipt(
            artifact_id="technical-review-p6-p7",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id="technical-review-p6-p7",
            source_provenance=(
                SourceReference(kind="derived", reference=evidence.evidence_id),
            ),
            review_id="technical-review-p6-p7",
            layer=QaLayer.TECHNICAL,
            review_request=request_pointer,
            render_state=manifest.active_render_state,
            render_output_sha256=render.output.file_sha256,
            timeline_fingerprint=render.timeline_fingerprint,
            dependency_graph_revision_id=manifest.active_dependency_graph.revision_id,
            qa_policy=manifest.active_qa_policy,
            evidence=(evidence_pointer,),
            evidence_ids=(evidence.evidence_id,),
            tool_identities=(tool,),
            verdict=QaVerdict.PASS,
        )
    )
    receipt_path = canonical_review_receipt_path(receipt.content_hash)
    receipt_file_hash = _write_p6_artifact(root, receipt_path, receipt)
    receipt_pointer = ReviewReceiptPointer(
        path=receipt_path,
        review_id=receipt.review_id,
        layer=receipt.layer,
        content_hash=receipt.content_hash,
        file_sha256=receipt_file_hash,
    )
    acceptance = seal_artifact(
        FinalAcceptanceReceipt(
            artifact_id="final-acceptance-p6-p7",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id="final-acceptance-p6-p7",
            source_provenance=(
                SourceReference(kind="derived", reference=receipt.review_id),
            ),
            acceptance_id="final-acceptance-p6-p7",
            dependency_graph=manifest.active_dependency_graph,
            dependency_states_hash=dependency_states_hash,
            render_state=manifest.active_render_state,
            render_output_sha256=render.output.file_sha256,
            timeline_fingerprint=render.timeline_fingerprint,
            qa_policy=manifest.active_qa_policy,
            required_review_receipts=(receipt_pointer,),
            verdict=QaVerdict.PASS,
        )
    )
    acceptance_path = canonical_final_acceptance_receipt_path(
        acceptance.content_hash
    )
    acceptance_file_hash = _write_p6_artifact(
        root, acceptance_path, acceptance
    )
    acceptance_pointer = FinalAcceptanceReceiptPointer(
        path=acceptance_path,
        acceptance_id=acceptance.acceptance_id,
        content_hash=acceptance.content_hash,
        file_sha256=acceptance_file_hash,
    )
    review_fingerprint = canonical_sha256(
        {"review": receipt.content_hash, "policy": manifest.active_qa_policy.content_hash}
    )
    acceptance_fingerprint = canonical_sha256(
        {"acceptance": acceptance.content_hash}
    )
    final_manifest = manifest.model_copy(
        update={
            "manifest_revision": manifest.manifest_revision + 1,
            "active_review_receipts": (receipt_pointer,),
            "review_states": (
                ReviewLayerState(
                    layer=QaLayer.TECHNICAL,
                    desired_fingerprint=review_fingerprint,
                    applied_fingerprint=review_fingerprint,
                    lifecycle=ReviewLifecycle.FRESH,
                    active_receipt=receipt_pointer,
                ),
            ),
            "final_acceptance_state": FinalAcceptanceState(
                desired_fingerprint=acceptance_fingerprint,
                applied_fingerprint=acceptance_fingerprint,
                lifecycle=ReviewLifecycle.FRESH,
                active_receipt=acceptance_pointer,
            ),
        }
    )
    _write_manifest(root, final_manifest)
    return {
        **fixture,
        "evidence_path": evidence_path,
        "review_receipt": receipt_pointer,
        "acceptance_receipt": acceptance_pointer,
    }


def test_loader_reopens_complete_p6_p7_review_and_final_acceptance(tmp_path):
    fixture = _make_complete_p6_p7_project(tmp_path)
    before = _tree_snapshot(tmp_path)

    loaded = load_production_project(fixture["project_path"])

    assert loaded.qa_policy is not None
    assert loaded.render_state is not None
    assert loaded.manifest.active_review_receipts == (fixture["review_receipt"],)
    assert loaded.manifest.final_acceptance_state is not None
    assert (
        loaded.manifest.final_acceptance_state.active_receipt
        == fixture["acceptance_receipt"]
    )
    assert all(
        item.lifecycle is DependencyLifecycle.FRESH
        for item in loaded.manifest.dependency_states
    )
    assert _tree_snapshot(tmp_path) == before


def test_loader_rejects_tampered_non_policy_p6_evidence_in_p7_project(tmp_path):
    fixture = _make_complete_p6_p7_project(tmp_path)
    evidence_path = tmp_path / fixture["evidence_path"]
    evidence_path.write_bytes(evidence_path.read_bytes() + b" ")

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(fixture["project_path"])

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_loader_runs_p6_verification_for_manifest_25_with_p7_state(
    tmp_path, p7_committed_project
):
    policy_path = add_p6_policy_to_p7_project(tmp_path)
    loaded = load_production_project(p7_committed_project["project_path"])
    assert loaded.qa_policy is not None

    policy_path.write_bytes(policy_path.read_bytes() + b" ")
    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(p7_committed_project["project_path"])
    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_loader_runs_p6_verification_for_manifest_27(tmp_path):
    fixture = _make_complete_p6_p7_project(tmp_path)
    manifest = _manifest(tmp_path)
    _write_manifest(root=tmp_path, manifest=manifest.model_copy(update={"schema_version": "2.7"}))
    evidence_path = tmp_path / fixture["evidence_path"]
    evidence_path.write_bytes(evidence_path.read_bytes() + b" ")

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(fixture["project_path"])

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


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


def test_reader_selects_exact_manifest_graph_without_scan_repair_or_write(tmp_path):
    graph = make_manifest_23_project(tmp_path)
    before = _tree_snapshot(tmp_path)

    loaded = load_production_project(tmp_path / "project.yaml")

    assert loaded.dependency_graph == graph
    assert loaded.manifest.active_dependency_graph is not None
    assert (
        loaded.dependency_graph.content_hash
        == loaded.manifest.active_dependency_graph.content_hash
    )
    assert _tree_snapshot(tmp_path) == before


def test_reader_rejects_tampered_manifest_selected_dependency_graph(tmp_path):
    make_manifest_23_project(tmp_path)
    manifest = _manifest(tmp_path)
    assert manifest.active_dependency_graph is not None
    graph_path = tmp_path / manifest.active_dependency_graph.path
    graph_path.write_bytes(graph_path.read_bytes() + b" ")

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_reader_rejects_missing_active_dependency_state(tmp_path):
    make_manifest_23_project(tmp_path)
    manifest = _manifest(tmp_path)
    _write_manifest(
        tmp_path,
        manifest.model_copy(update={"dependency_states": manifest.dependency_states[1:]}),
    )

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_reader_rejects_illegal_dependency_blocked_by(tmp_path):
    make_manifest_23_project(tmp_path)
    manifest = _manifest(tmp_path)
    target = next(
        state for state in manifest.dependency_states if state.lifecycle.value == "stale"
    )
    unrelated = next(
        state.node_id
        for state in manifest.dependency_states
        if state.node_id != target.node_id
    )
    states = tuple(
        state.model_copy(
            update={"lifecycle": DependencyLifecycle.BLOCKED, "blocked_by": (unrelated,)}
        )
        if state.node_id == target.node_id
        else state
        for state in manifest.dependency_states
    )
    _write_manifest(tmp_path, manifest.model_copy(update={"dependency_states": states}))

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_reader_rejects_dependency_graph_symlink_and_does_not_scan_decoy(tmp_path):
    make_manifest_23_project(tmp_path)
    manifest = _manifest(tmp_path)
    assert manifest.active_dependency_graph is not None
    selected = tmp_path / manifest.active_dependency_graph.path
    payload = selected.read_bytes()
    selected.unlink()
    decoy = selected.with_name("dependency_graph.decoy.json")
    decoy.write_bytes(payload)
    selected.symlink_to(decoy)

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_reader_reopens_superseded_project_evidence_from_origin_revision(tmp_path):
    graph = make_manifest_23_project(tmp_path)
    original = _manifest(tmp_path)
    removed_state = next(
        state
        for state in original.dependency_states
        if state.applied_evidence is not None
        and state.applied_evidence.owner == "project_snapshot"
    )
    _commit_revision_two(tmp_path, attempt_id="reader-superseded-origin")
    remaining_nodes = tuple(
        node for node in graph.nodes if node.node_id != removed_state.node_id
    )
    remaining_edges = tuple(
        edge
        for edge in graph.edges
        if removed_state.node_id
        not in {edge.source_node_id, edge.target_node_id}
    )
    next_graph = build_dependency_graph(remaining_nodes, remaining_edges)
    next_states = resolve_dependency_state(next_graph, original.dependency_states).states
    _select_manifest_23_graph(tmp_path, next_graph, next_states)

    loaded = load_production_project(tmp_path / "project.yaml")

    superseded = next(
        state
        for state in loaded.manifest.dependency_states
        if state.node_id == removed_state.node_id
    )
    assert superseded.lifecycle is DependencyLifecycle.SUPERSEDED
    assert superseded.graph_revision_id == graph.revision_id
    assert superseded.applied_evidence == removed_state.applied_evidence


def test_loader_rejects_forged_historical_shot_projection_when_only_upstream_changes(
    tmp_path,
):
    graph = make_manifest_23_project(tmp_path)
    original = _manifest(tmp_path)
    removed_state = next(
        state
        for state in original.dependency_states
        if state.applied_evidence is not None
        and state.applied_evidence.owner == "project_snapshot"
        and not state.node_id.startswith("creative:shot:")
    )
    _commit_revision_two(tmp_path, attempt_id="reader-forged-upstream-origin")
    next_graph = build_dependency_graph(
        tuple(node for node in graph.nodes if node.node_id != removed_state.node_id),
        tuple(
            edge
            for edge in graph.edges
            if removed_state.node_id
            not in {edge.source_node_id, edge.target_node_id}
        ),
    )
    next_states = resolve_dependency_state(next_graph, original.dependency_states).states
    blocked = next(
        state
        for state in next_states
        if state.node_id == "creative:shot:shot-1:composition"
        and state.lifecycle is DependencyLifecycle.BLOCKED
    )
    forged_fingerprint = "f" * 64
    assert blocked.applied_evidence is not None
    forged = blocked.model_copy(
        update={
            "applied_fingerprint": forged_fingerprint,
            "applied_evidence": blocked.applied_evidence.model_copy(
                update={"artifact_fingerprint": forged_fingerprint}
            ),
        }
    )
    forged_states = tuple(
        forged if state.node_id == forged.node_id else state for state in next_states
    )
    _select_manifest_23_graph(tmp_path, next_graph, forged_states)

    with pytest.raises(AiVideoError, match="Historical Shot dependency evidence"):
        load_production_project(tmp_path / "project.yaml")


@pytest.mark.parametrize("owner", ["project", "registry"])
def test_reader_rejects_self_consistent_graph_with_forged_owner_projection(
    tmp_path, owner
):
    loaded = load_production_project(write_production_project(tmp_path))
    if owner == "project":
        artifact = loaded.brief
        node = DependencyNode(
            node_id=f"creative:brief:{artifact.artifact_id}",
            kind=DependencyNodeKind.CREATIVE_ARTIFACT,
            semantic_role=DependencySemanticRole.NONE,
            artifact_id=artifact.artifact_id,
            artifact_revision=artifact.revision,
            contributions=(
                FingerprintContribution(
                    key="brief.semantic", fingerprint="f" * 64
                ),
            ),
        )
    else:
        artifact = loaded.registry.assets[0]
        node = DependencyNode(
            node_id=f"asset:{artifact.asset_id}",
            kind=DependencyNodeKind.ASSET,
            semantic_role=DependencySemanticRole.VISUAL,
            artifact_id=artifact.asset_id,
            contributions=(
                FingerprintContribution(key="asset.bytes", fingerprint=artifact.sha256),
                FingerprintContribution(
                    key="asset.inputs", fingerprint="f" * 64
                ),
            ),
        )
    graph = build_dependency_graph((node,), ())
    fingerprint = desired_fingerprints(graph)[node.node_id]
    evidence = (
        ProjectDependencyEvidence(
            owner="project_snapshot",
            pointer=loaded.manifest.active_project,
            artifact_id=node.artifact_id,
            artifact_fingerprint=fingerprint,
        )
        if owner == "project"
        else RegistryDependencyEvidence(
            owner="registry_snapshot",
            pointer=loaded.manifest.active_registry,
            artifact_id=node.artifact_id,
            artifact_fingerprint=fingerprint,
        )
    )
    state = DependencyNodeState(
        node_id=node.node_id,
        graph_revision_id=graph.revision_id,
        desired_fingerprint=fingerprint,
        applied_fingerprint=fingerprint,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=evidence,
    )
    _select_manifest_23_graph(tmp_path, graph, (state,))

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


@pytest.mark.parametrize(
    ("asset_id", "mutation"),
    [
        ("image-shot-1", "missing-bytes"),
        ("caption-asset-1", "caption-style"),
        ("image-shot-1", "extra-key"),
    ],
)
def test_reader_rejects_noncanonical_registry_contribution_sets(
    tmp_path, asset_id, mutation
):
    graph = make_manifest_23_project(tmp_path)
    manifest = _manifest(tmp_path)
    original = next(node for node in graph.nodes if node.artifact_id == asset_id)
    contributions = list(original.contributions)
    if mutation == "missing-bytes":
        contributions = [item for item in contributions if item.key != "asset.bytes"]
    elif mutation == "caption-style":
        contributions = [
            item.model_copy(update={"fingerprint": "f" * 64})
            if item.key == "caption.style"
            else item
            for item in contributions
        ]
    else:
        contributions.append(
            FingerprintContribution(key="zz.extra", fingerprint="f" * 64)
        )
    node = original.model_copy(
        update={"contributions": tuple(sorted(contributions, key=lambda item: item.key))}
    )
    forged = build_dependency_graph((node,), ())
    fingerprint = desired_fingerprints(forged)[node.node_id]
    state = DependencyNodeState(
        node_id=node.node_id,
        graph_revision_id=forged.revision_id,
        desired_fingerprint=fingerprint,
        applied_fingerprint=fingerprint,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=RegistryDependencyEvidence(
            owner="registry_snapshot",
            pointer=manifest.active_registry,
            artifact_id=node.artifact_id,
            artifact_fingerprint=fingerprint,
        ),
    )
    _select_manifest_23_graph(tmp_path, forged, (state,))

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_reader_rejects_forged_voice_semantic_projection(tmp_path):
    _, request, _, audio_ids, _ = _activate_fake_voice(tmp_path)
    loaded = load_production_project(tmp_path / "project.yaml")
    asset = next(item for item in loaded.registry.assets if item.asset_id == audio_ids[0])
    assert asset.audio_metadata is not None

    def contribution(key: str, schema: str, value: object):
        return FingerprintContribution(
            key=key,
            fingerprint=canonical_sha256({"schema": schema, "value": value}),
        )

    node = DependencyNode(
        node_id=f"asset:{asset.asset_id}",
        kind=DependencyNodeKind.ASSET,
        semantic_role=DependencySemanticRole.VOICE,
        artifact_id=asset.asset_id,
        contributions=tuple(
            sorted(
                (
                    contribution(
                        "asset.inputs",
                        "ai-video-asset-inputs/1",
                        {
                            "input_artifact_ids": request.input_artifact_ids,
                            "input_fingerprint": request.input_fingerprint,
                        },
                    ),
                    contribution(
                        "audio.contract",
                        "ai-video-audio-contract/1",
                        {
                            "audio_kind": request.audio_kind.value,
                            "script_hash": request.script_hash,
                            "voice_id": request.voice_id,
                            "language": request.language,
                            "sample_rate_hz": request.output_sample_rate_hz,
                            "channels": request.output_channels,
                            "input_artifact_ids": request.input_artifact_ids,
                            "input_fingerprint": request.input_fingerprint,
                        },
                    ),
                    FingerprintContribution(
                        key="voice.semantic", fingerprint="f" * 64
                    ),
                ),
                key=lambda item: item.key,
            )
        ),
    )
    graph = build_dependency_graph((node,), ())
    fingerprint = desired_fingerprints(graph)[node.node_id]
    state = DependencyNodeState(
        node_id=node.node_id,
        graph_revision_id=graph.revision_id,
        desired_fingerprint=fingerprint,
        applied_fingerprint=fingerprint,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=RegistryDependencyEvidence(
            owner="registry_snapshot",
            pointer=loaded.manifest.active_registry,
            artifact_id=node.artifact_id,
            artifact_fingerprint=fingerprint,
        ),
    )
    _select_manifest_23_graph(tmp_path, graph, (state,))

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_reader_rejects_active_render_evidence_pointer_split_brain(tmp_path):
    activated, _, _ = _activate_fake_render(tmp_path)
    evidence_pointer = activated.active_render_state
    assert evidence_pointer is not None
    loaded = load_production_project(tmp_path / "project.yaml")
    assert loaded.render_state is not None
    replacement = seal_artifact(
        loaded.render_state.model_copy(
            update={
                "revision": loaded.render_state.revision + 1,
                "content_hash": "0" * 64,
            }
        )
    )
    payload = replacement.model_dump_json(indent=2).encode("utf-8")
    replacement_path = tmp_path / canonical_render_state_path(
        replacement.content_hash
    )
    replacement_path.write_bytes(payload)
    selected_pointer = RenderStateSnapshotPointer(
        path=replacement_path.relative_to(tmp_path),
        revision=replacement.revision,
        content_hash=replacement.content_hash,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    graph, states = _historical_render_graph_states(evidence_pointer)
    manifest = _select_manifest_23_graph(tmp_path, graph, states).model_copy(
        update={"active_render_state": selected_pointer}
    )
    _write_manifest(tmp_path, manifest)

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def _historical_render_graph_states(render_pointer):
    source = DependencyNode(
        node_id="renderer-source:composition-reader",
        kind=DependencyNodeKind.RENDERER_SOURCE,
        semantic_role=DependencySemanticRole.RENDERER_SOURCE,
        artifact_id="composition-reader",
        contributions=(
            FingerprintContribution(key="source.contract", fingerprint="1" * 64),
        ),
    )
    render = DependencyNode(
        node_id="render:composition-reader",
        kind=DependencyNodeKind.RENDER,
        semantic_role=DependencySemanticRole.RENDER,
        artifact_id="composition-reader",
        contributions=(
            FingerprintContribution(key="render.contract", fingerprint="2" * 64),
        ),
    )
    edge = DependencyEdge(
        source_node_id=source.node_id,
        target_node_id=render.node_id,
        reason=DependencyReason.RENDER_EXECUTION,
        contribution=FingerprintContribution(
            key="render.source", fingerprint="3" * 64
        ),
    )
    graph = build_dependency_graph((source, render), (edge,))
    desired = desired_fingerprints(graph)
    previous = tuple(
        DependencyNodeState(
            node_id=node.node_id,
            graph_revision_id=graph.revision_id,
            desired_fingerprint=desired[node.node_id],
            applied_fingerprint=fingerprint,
            lifecycle=DependencyLifecycle.STALE,
            applied_evidence=RenderDependencyEvidence(
                owner="render_state",
                pointer=render_pointer,
                artifact_id=node.artifact_id,
                artifact_fingerprint=fingerprint,
            ),
        )
        for node, fingerprint in ((source, "a" * 64), (render, "b" * 64))
    )
    return graph, resolve_dependency_state(graph, previous).states


def _composition_dependency_graph(content_hash: str):
    node = DependencyNode(
        node_id="composition:reader",
        kind=DependencyNodeKind.COMPOSITION_SPEC,
        semantic_role=DependencySemanticRole.COMPOSITION,
        artifact_id="composition-reader",
        artifact_revision=1,
        contributions=(
            FingerprintContribution(
                key="composition.content",
                fingerprint=content_hash,
            ),
        ),
    )
    return build_dependency_graph((node,), ())


def test_manifest_23_reader_rejects_old_render_evidence_for_new_composition(
    tmp_path,
):
    activated, _, _ = _activate_fake_render(tmp_path)
    render_pointer = activated.active_render_state
    assert render_pointer is not None
    graph = _composition_dependency_graph("9" * 64)
    desired = desired_fingerprints(graph)
    node = graph.nodes[0]
    state = DependencyNodeState(
        node_id=node.node_id,
        graph_revision_id=graph.revision_id,
        desired_fingerprint=desired[node.node_id],
        applied_fingerprint=desired[node.node_id],
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=RenderDependencyEvidence(
            owner="render_state",
            pointer=render_pointer,
            artifact_id=node.artifact_id,
            artifact_fingerprint=desired[node.node_id],
        ),
    )
    manifest = _select_manifest_23_graph(tmp_path, graph, (state,)).model_copy(
        update={"active_render_state": render_pointer}
    )
    _write_manifest(tmp_path, manifest)

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_node_applied_rejects_composition_render_evidence_outside_atomic_unit(
    tmp_path,
):
    activated, _, _ = _activate_fake_render(tmp_path)
    render_pointer = activated.active_render_state
    assert render_pointer is not None
    graph = _composition_dependency_graph("1" * 64)
    desired = desired_fingerprints(graph)
    node = graph.nodes[0]
    stale = DependencyNodeState(
        node_id=node.node_id,
        graph_revision_id=graph.revision_id,
        desired_fingerprint=desired[node.node_id],
        applied_fingerprint="a" * 64,
        lifecycle=DependencyLifecycle.STALE,
        applied_evidence=RenderDependencyEvidence(
            owner="render_state",
            pointer=render_pointer,
            artifact_id=node.artifact_id,
            artifact_fingerprint="a" * 64,
        ),
    )
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=activated.manifest_revision,
        base_dependency_graph=None,
        candidate_graph=graph,
        candidate_dependency_states=(stale,),
        expected_desired_fingerprints=desired,
    )
    committer = ProductionStateCommitter(tmp_path)
    committed = committer.bootstrap_dependency_graph(
        attempt_id="reader-composition-bootstrap",
        graph=graph,
        transition=transition,
        expected_desired_fingerprints=desired,
    )
    evidence = RenderDependencyEvidence(
        owner="render_state",
        pointer=render_pointer,
        artifact_id=node.artifact_id,
        artifact_fingerprint=desired[node.node_id],
    )

    with pytest.raises(AiVideoError) as exc_info:
        committer.record_dependency_node_applied(
            expected_manifest_revision=committed.manifest_revision,
            active_dependency_graph=committed.active_dependency_graph,
            candidate_dependency_graph=committed.active_dependency_graph,
            node_id=node.node_id,
            desired_fingerprint=desired[node.node_id],
            evidence=evidence,
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def _advance_active_project_and_registry(root: Path, attempt_id: str) -> None:
    _commit_revision_two(root, attempt_id=attempt_id)
    manifest = _manifest(root)
    registry = AssetRegistrySnapshot.model_validate_json(
        (root / manifest.active_registry.path).read_bytes()
    )
    first = registry.assets[0].model_copy(update={"usage_license": "test-revision-2"})
    _select_resealed_registry(
        root,
        registry.model_copy(update={"assets": (first, *registry.assets[1:])}),
    )


@pytest.mark.parametrize("schema_version", ["2.3", "2.5"])
def test_manifest_23_reader_reopens_historical_render_pair_for_stale_evidence(
    tmp_path, schema_version
):
    activated, _, _ = _activate_fake_render(tmp_path)
    old_render = activated.active_render_state
    assert old_render is not None
    _advance_active_project_and_registry(tmp_path, "reader-new-active-pair")
    graph, states = _historical_render_graph_states(old_render)
    manifest = _select_manifest_23_graph(tmp_path, graph, states).model_copy(
        update={
            "schema_version": schema_version,
            "active_render_state": old_render,
        }
    )
    _write_manifest(tmp_path, manifest)

    loaded = load_production_project(tmp_path / "project.yaml")

    assert loaded.render_state is not None
    assert loaded.render_state.project != loaded.manifest.active_project
    assert loaded.render_state.registry != loaded.manifest.active_registry
    assert loaded.manifest.dependency_states[-1].lifecycle in {
        DependencyLifecycle.STALE,
        DependencyLifecycle.BLOCKED,
    }


@pytest.mark.parametrize("owner", ["project", "registry", "render"])
def test_manifest_23_reader_rejects_tampered_historical_render_pair(
    tmp_path, owner
):
    activated, _, _ = _activate_fake_render(tmp_path)
    old_render = activated.active_render_state
    assert old_render is not None
    old_state = load_production_project(tmp_path / "project.yaml").render_state
    assert old_state is not None
    _advance_active_project_and_registry(tmp_path, "reader-new-pair-tamper")
    graph, states = _historical_render_graph_states(old_render)
    manifest = _select_manifest_23_graph(tmp_path, graph, states).model_copy(
        update={"active_render_state": old_render}
    )
    _write_manifest(tmp_path, manifest)
    path = {
        "project": old_state.project.path,
        "registry": old_state.registry.path,
        "render": old_render.path,
    }[owner]
    target = tmp_path / path
    target.write_bytes(target.read_bytes() + b" ")

    with pytest.raises(AiVideoError) as exc_info:
        load_production_project(tmp_path / "project.yaml")

    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_p8_video_evidence_reopens_receipts_with_exact_content_hash(tmp_path):
    from ai_video.production._video_project_reader import (
        load_video_request_receipt,
        load_video_status_receipt,
    )

    fixture = make_p8_video_evidence(tmp_path)
    resolved = load_video_request_receipt(tmp_path, fixture["request_pointer"])
    observation = load_video_status_receipt(tmp_path, fixture["status_pointer"])

    assert resolved == fixture["resolved"]
    assert observation == fixture["observation"]


@pytest.mark.parametrize("owner", ["request", "status"])
def test_p8_video_evidence_rejects_tampered_receipt_bytes(tmp_path, owner):
    from ai_video.production._video_project_reader import (
        load_video_request_receipt,
        load_video_status_receipt,
    )

    fixture = make_p8_video_evidence(tmp_path)
    target = fixture[f"{owner}_path"]
    target.write_bytes(target.read_bytes() + b" ")
    loader = {
        "request": load_video_request_receipt,
        "status": load_video_status_receipt,
    }[owner]
    with pytest.raises(AiVideoError) as exc_info:
        loader(tmp_path, fixture[f"{owner}_pointer"])
    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


@pytest.mark.parametrize("owner", ["request", "status"])
def test_p8_video_evidence_refuses_to_follow_receipt_symlinks(tmp_path, owner):
    from ai_video.production._video_project_reader import (
        load_video_request_receipt,
        load_video_status_receipt,
    )

    fixture = make_p8_video_evidence(tmp_path)
    target = fixture[f"{owner}_path"]
    outside = tmp_path / f"outside-{owner}.json"
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)
    loader = {
        "request": load_video_request_receipt,
        "status": load_video_status_receipt,
    }[owner]
    with pytest.raises(AiVideoError) as exc_info:
        loader(tmp_path, fixture[f"{owner}_pointer"])
    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_p8_video_evidence_binds_observation_to_its_attempt_request(tmp_path):
    from ai_video.production._video_project_reader import verify_video_evidence

    fixture = make_p8_video_evidence(tmp_path)
    state = fixture["attempt_state"]
    verify_video_evidence(tmp_path, (state,))

    foreign = state.request.model_copy(
        update={
            "generation_id": "generation-002",
            "request_input_hash": "9" * 64,
        }
    )
    with pytest.raises(AiVideoError) as exc_info:
        verify_video_evidence(
            tmp_path, (state.model_copy(update={"request": foreign}),)
        )
    assert exc_info.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_p8_video_evidence_binds_observation_to_exact_gate_submission(tmp_path):
    from ai_video.production._video_project_reader import verify_video_evidence
    from ai_video.production.hashing import canonical_sha256

    fixture = make_p8_video_evidence(tmp_path)
    observation = fixture["observation"]
    data = observation.model_dump(
        mode="json",
        exclude={"observation_fingerprint"},
    )
    data["submission_fingerprint"] = "9" * 64
    data["observation_fingerprint"] = canonical_sha256(data)
    foreign = type(observation).model_validate(data)
    path = tmp_path / (
        "state/video-generation/status/"
        f"{foreign.observation_fingerprint}.json"
    )
    path.write_bytes(foreign.model_dump_json().encode("utf-8"))
    pointer = fixture["status_pointer"].model_copy(
        update={
            "path": path.relative_to(tmp_path),
            "observation_fingerprint": foreign.observation_fingerprint,
            "file_sha256": sha256_file(path),
        }
    )
    state = fixture["attempt_state"].model_copy(
        update={"latest_observation": pointer}
    )

    with pytest.raises(AiVideoError, match="submission"):
        verify_video_evidence(tmp_path, (state,))


def test_p8_candidate_evidence_requires_succeeded_observation(tmp_path):
    from ai_video.production._video_project_reader import verify_video_evidence
    from ai_video.production.video import VideoSubmission, VideoTaskObservation

    fixture = make_p8_video_evidence(tmp_path)
    submission = VideoSubmission.from_paid_submit_receipt(
        resolved=fixture["resolved"],
        receipt=fixture["submit_receipt"],
    )
    failed = VideoTaskObservation.create(
        submission=submission,
        state="failed",
        observed_at=fixture["observation"].observed_at,
    )
    path = tmp_path / (
        "state/video-generation/status/"
        f"{failed.observation_fingerprint}.json"
    )
    path.write_bytes(failed.model_dump_json().encode("utf-8"))
    pointer = fixture["status_pointer"].model_copy(
        update={
            "path": path.relative_to(tmp_path),
            "observation_fingerprint": failed.observation_fingerprint,
            "file_sha256": sha256_file(path),
        }
    )
    state = fixture["attempt_state"].model_copy(
        update={
            "phase": "candidate",
            "latest_observation": pointer,
            "provider_file_id": None,
            "candidate_video_asset_ids": (
                fixture["attempt_state"].request.output_asset_id,
            ),
        }
    )

    with pytest.raises(AiVideoError, match="succeeded"):
        verify_video_evidence(tmp_path, (state,))
