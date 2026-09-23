"""Offline Ecommerce Job integration through the canonical Production owners."""

from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
from types import SimpleNamespace

from ai_video.production.ad_creative import (
    compile_ad_creative_handoff,
    create_ad_creative_plan,
)
from ai_video.production.ad_creative_types import AdSoundCue
from ai_video.production.artifact_contracts import SourceReference
from ai_video.production.captions import (
    CaptionImportRequest,
    caption_style_fingerprint,
    caption_timing_fingerprint,
)
from ai_video.production._caption_quality_p6 import CaptionReviewExecution
from ai_video.production.caption_quality_contracts import (
    CaptionEvidenceStrength,
    CaptionFindingReasonCode,
    CaptionRequirementGroup,
)
from ai_video.production.commercial_graphics import AdSoundRole
from ai_video.production.composition_contracts import (
    AudioKind,
    AudioTrackSpec,
    CaptionTrackBinding,
    RendererIdentity,
    RendererKind,
)
from ai_video.production.composition import resolve_composition
from ai_video.production.dependency import (
    ProductionDependencyInputs,
    build_production_dependency_graph,
    resolve_dependency_state,
)
from ai_video.production.ecommerce_job import (
    EcommerceProductionJobService,
    EcommerceShotExecutionPlan,
)
from ai_video.production.ecommerce_job_review import (
    EcommerceDeliveryExecutionPlan,
    EcommerceFinalReviewFrontier,
    EcommercePostMediaExecutionPlan,
)
from ai_video.production.ecommerce_job_compiler import (
    bootstrap_ecommerce_production_project,
    compile_ecommerce_production_handoff,
)
from ai_video.production.ecommerce_job_contracts import (
    EcommerceJobNextAction,
    EcommerceProductionHandoff,
)
from ai_video.production.final_output_contracts import (
    FinalOutputContract,
    FinalOutputRequirement,
)
from ai_video.production.final_output_review import (
    FinalOutputFinding,
    FinalOutputObservation,
)
from ai_video.production.ecommerce_quality_gate import EcommerceWholeAdEvaluationPayload
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetRoleRequirement,
    AssetSourceKind,
    AssetType,
    CaptionAssetMetadata,
    CaptionSegment,
    CaptionSegmentationPolicy,
    CaptionStyleReference,
    CaptionTrack,
    DeliveryProfile,
    EgressMetadata,
    QaLayer,
    QaVerdict,
    ToolIdentity,
    VisualStrategy,
)
from ai_video.production.paths import canonical_image_asset_path
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    prepare_audio_registry_commit,
)
from ai_video.production.video import VideoOutputRequirement
from ai_video.production.video_candidate_composition import (
    build_video_candidate_composition_spec,
)
from production_project_factory import (
    _make_audio_asset,
    _p7_png,
    _refresh_p7_ready_project_registry_nodes,
    make_composition_spec,
)
from production_e2e_support import (
    CAPTION_EVALUATOR_TOOL,
    make_caption_quality_policy,
    passing_caption_evidence_payload,
)
from production_ecommerce_job_render_support import prepare_offline_ecommerce_render
from ai_video.production.quality_gate_coordinator import (
    UniversalHardCheck,
    UniversalQaApplicability,
    UniversalQaCheckOutcome,
    UniversalQaProfile,
)
from test_production_ecommerce_job import (
    _activate_offline_ecommerce_policy,
    _real_input,
    _request,
    _two_shot_runtime_handoff,
)
from test_production_ecommerce_post_media_e2e import _passing_payload
from test_production_review import _Manifest25ReviewFixture
from test_production_commercial_visual_review import REVIEW_TOOL


VIDEO = Path(__file__).parent / "fixtures/ecommerce_job/vertical-3s.mp4"
FINAL_VIDEO = Path(__file__).parent / "fixtures/ecommerce_job/vertical-6s-audio.mp4"
CAPTION_STYLE_BYTES = b'{"font_family":"Inter","schema_version":"1"}'
CAPTION_STYLE_HASH = hashlib.sha256(CAPTION_STYLE_BYTES).hexdigest()
CAPTION_STYLE = CaptionStyleReference(
    artifact_id="ecommerce-offline-caption-style",
    revision=1,
    content_hash=CAPTION_STYLE_HASH,
    path=Path(f"assets/styles/{CAPTION_STYLE_HASH}.json"),
)
CAPTION_STYLE_FINGERPRINTS = (
    (
        CAPTION_STYLE.artifact_id,
        caption_style_fingerprint(CAPTION_STYLE, CAPTION_STYLE_BYTES),
    ),
)
OUTPUT = VideoOutputRequirement(
    duration_seconds=3,
    width=1080,
    height=1920,
    fps=24,
    container="mp4",
    mime_type="video/mp4",
    native_audio=False,
)


def _measured_technical_windows(_request, evidence):
    payload = dict(evidence.measured_payload)
    payload["windows"] = [
        {
            **window,
            "unique_frame_count": (
                72 if window["visual_strategy"] == VisualStrategy.GENERATED_VIDEO.value else 1
            ),
        }
        for window in payload["windows"]
    ]
    return seal_artifact(
        evidence.model_copy(
            update={"content_hash": "0" * 64, "measured_payload": payload}
        )
    )


def _handoff_and_compiled(*, with_caption: bool = False):
    original = _two_shot_runtime_handoff()
    first, second = original.artifact_proposals.shots
    first = seal_artifact(
        first.model_copy(
            update={
                "revision": first.revision + 1,
                "content_hash": "0" * 64,
                "visual_strategy": VisualStrategy.STATIC_IMAGE,
                "required_asset_roles": (
                    AssetRoleRequirement(
                        role="final_visual",
                        asset_ids=("hero-still",),
                        allowed_asset_types=(AssetType.IMAGE,),
                    ),
                    AssetRoleRequirement(
                        role="product_overlay",
                        asset_ids=("asset-product",),
                        allowed_asset_types=(AssetType.IMAGE,),
                    ),
                ),
                "generated_video_rationale": None,
            }
        )
    )
    layout = original.layout_plan
    layout_values = {
        name: getattr(layout, name)
        for name in type(layout).model_fields
        if name != "layout_plan_id"
    }
    layout = type(layout).create(
        **{
            **layout_values,
            "shots": (
                layout.shots[0].model_copy(
                    update={"visual_strategy": VisualStrategy.STATIC_IMAGE}
                ),
                layout.shots[1],
            ),
        }
    )
    profile = original.compile_profile
    profile_values = {
        name: getattr(profile, name)
        for name in type(profile).model_fields
        if name != "profile_id"
    }
    profile = type(profile).create(
        **{
            **profile_values,
            "layout_plan_id": layout.layout_plan_id,
            "requirement_resolutions": tuple(
                item.model_copy(
                    update={
                        "evidence_ids": (
                            original.delivery_profile.profile_id,
                            original.visual_system_profile.profile_id,
                            layout.layout_plan_id,
                        )
                    }
                )
                for item in profile.requirement_resolutions
            ),
        }
    )
    handoff_values = {
        name: getattr(original, name)
        for name in EcommerceProductionHandoff.model_fields
        if name != "handoff_id"
    }
    proposal = original.ad_creative_plan_proposal
    sound_cues = proposal.sound_cues
    if with_caption:
        sound_cues = (
            *sound_cues,
            AdSoundCue(
                cue_id="sound-dialogue",
                role=AdSoundRole.DIALOGUE,
                audio_track_id="audio-dialogue",
                synchronized_event_id="presentation-hero",
            ),
        )
    handoff = EcommerceProductionHandoff.create(
        **{
            **handoff_values,
            "layout_plan": layout,
            "compile_profile": profile,
            "artifact_proposals": original.artifact_proposals.model_copy(
                update={"shots": (first, second)}
            ),
            "ad_creative_plan_proposal": proposal.model_copy(
                update={
                    "ad_arc": (
                        proposal.ad_arc[0].model_copy(
                            update={"shot_ids": ("shot-hero", "shot-proof")}
                        ),
                        *proposal.ad_arc[1:],
                    ),
                    "sound_cues": sound_cues,
                }
            ),
        }
    )
    plan = create_ad_creative_plan(
        handoff.ad_creative_plan_proposal,
        artifact_id="ecommerce-offline-e2e-plan",
        revision=1,
        creation_receipt_id="ecommerce-offline-e2e-plan",
        source_provenance=(
            SourceReference(
                kind="derived",
                reference=f"ecommerce-handoff:{handoff.handoff_id}",
                content_hash=handoff.handoff_id,
            ),
            SourceReference(
                kind="derived",
                reference=f"ecommerce-compile-profile:{profile.profile_id}",
                content_hash=profile.profile_id,
            ),
        ),
    )
    composition = make_composition_spec(shot_ids=("shot-hero", "shot-proof"))
    base_layer = composition.layers[0]
    composition = seal_artifact(
        composition.model_copy(
            update={
                "schema_version": "2.1",
                "revision": composition.revision + 1,
                "content_hash": "0" * 64,
                "delivery_profile": DeliveryProfile(width=1080, height=1920, fps=24),
                "layers": (
                    base_layer.model_copy(
                        update={
                            "layer_id": "layer-primary",
                            "asset_role": "final_visual",
                            "asset_id": "hero-still",
                        }
                    ),
                    base_layer.model_copy(
                        update={
                            "layer_id": "layer-product",
                            "asset_role": "product_overlay",
                            "asset_id": "asset-product",
                            "z_index": 10,
                        }
                    ),
                    composition.layers[1].model_copy(
                        update={
                            "asset_role": "final_visual",
                            "asset_id": "proof-pre-generation-source",
                        }
                    ),
                ),
                "audio_tracks": (
                    AudioTrackSpec(
                        track_id="audio-music",
                        audio_kind=AudioKind.BGM,
                        asset_id="audio-music-asset",
                        start_sample=0,
                    ),
                    *(
                        (
                            AudioTrackSpec(
                                track_id="audio-dialogue",
                                audio_kind=AudioKind.DIALOGUE,
                                asset_id="audio-dialogue-asset",
                                shot_id="shot-hero",
                                start_sample=24_000,
                            ),
                        )
                        if with_caption
                        else ()
                    ),
                ),
                "caption_tracks": (
                    (
                        CaptionTrackBinding(
                            binding_id="caption-dialogue",
                            caption_asset_id="caption-dialogue-asset",
                            source_audio_track_id="audio-dialogue",
                            shot_id="shot-hero",
                            style_reference=CAPTION_STYLE,
                        ),
                    )
                    if with_caption
                    else ()
                ),
            }
        )
    )
    return handoff, plan, compile_ad_creative_handoff(plan, composition)


def _bootstrap(
    root: Path,
    handoff: EcommerceProductionHandoff,
    composition_spec,
    *,
    with_caption: bool = False,
):
    compiled = compile_ecommerce_production_handoff(
        handoff,
        expected_project_id="project-product-one",
    )
    image_payloads = (
        ("hero-still", _p7_png(1080, 1920)),
        ("asset-product", _p7_png(1080, 1920, rgba=b"\x20\x40\x60\xff")),
        (
            "proof-pre-generation-source",
            _p7_png(1080, 1920, rgba=b"\x30\x50\x70\xff"),
        ),
    )
    records = []
    prepared = []
    for asset_id, payload in image_payloads:
        digest = hashlib.sha256(payload).hexdigest()
        path = canonical_image_asset_path(digest)
        records.append(
            AssetRecord(
                asset_id=asset_id,
                asset_type=AssetType.IMAGE,
                artifact_path=path,
                sha256=digest,
                size_bytes=len(payload),
                mime_type="image/png",
                width=1080,
                height=1920,
                source_kind=AssetSourceKind.IMPORTED,
                tool=ToolIdentity(name="offline-fixture", version="1"),
                input_fingerprint=digest,
                creation_receipt_id=f"offline-{asset_id}",
                usage_license="fixture",
                egress=EgressMetadata(remote=False),
            )
        )
        prepared.append(PreparedArtifact(path, payload, digest))
    (root / "assets/files").mkdir(parents=True, exist_ok=True)
    music, path = _make_audio_asset(
        root,
        asset_id="audio-music-asset",
        audio_kind=AudioKind.BGM,
        duration_samples=288_000,
    )
    records.append(music)
    prepared.append(PreparedArtifact(music.artifact_path, path.read_bytes(), music.sha256))
    caption_record = None
    caption_artifacts = ()
    if with_caption:
        dialogue, dialogue_path = _make_audio_asset(
            root,
            asset_id="audio-dialogue-asset",
            audio_kind=AudioKind.DIALOGUE,
            duration_samples=96_000,
        )
        assert dialogue.audio_metadata is not None
        story_id = compiled.project.artifacts.story.artifact_id
        dialogue = dialogue.model_copy(
            update={
                "input_artifact_ids": (story_id,),
                "audio_metadata": dialogue.audio_metadata.model_copy(
                    update={
                        "source": dialogue.audio_metadata.source.model_copy(
                            update={"input_artifact_ids": (story_id,)}
                        )
                    }
                ),
            }
        )
        records.append(dialogue)
        prepared.append(
            PreparedArtifact(
                dialogue.artifact_path,
                dialogue_path.read_bytes(),
                dialogue.sha256,
            )
        )
        script_hash = dialogue.audio_metadata.script_hash
        assert script_hash is not None
        track = CaptionTrack(
            artifact_id="ecommerce-offline-caption-track",
            schema_version="2.1",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id="ecommerce-offline-caption-track",
            source_provenance=(
                SourceReference(kind="derived", reference="fixture-alignment"),
            ),
            caption_track_id="ecommerce-offline-caption-track",
            language="en",
            script_hash=script_hash,
            transcript_hash=hashlib.sha256(b"Product One").hexdigest(),
            source_audio_asset_id=dialogue.asset_id,
            source_audio_sha256=dialogue.sha256,
            source_sample_rate_hz=48_000,
            segments=(
                CaptionSegment(
                    segment_id="caption-intro",
                    text="Product One",
                    start_sample=1_000,
                    end_sample=95_000,
                    speaker_id="speaker-1",
                ),
            ),
            segmentation_policy=CaptionSegmentationPolicy(
                policy_id="ecommerce-offline-segments",
                policy_version="1",
                max_characters=42,
                max_lines=2,
                break_strategy="provider_segments",
            ),
            alignment_provider="offline-fixture",
            alignment_model="1",
            alignment_receipt_id="fixture-alignment",
            style_reference_id=CAPTION_STYLE.artifact_id,
            timing_fingerprint="0" * 64,
        )
        track = track.model_copy(
            update={"timing_fingerprint": caption_timing_fingerprint(track)}
        )
        track = CaptionTrack.model_validate(seal_artifact(track).model_dump(mode="python"))
        imported = CaptionImportRequest.create(
            caption_track=track,
            style_reference=CAPTION_STYLE,
            style_bytes=CAPTION_STYLE_BYTES,
        )
        caption_path = Path(f"assets/captions/{imported.track_sha256}.json")
        caption = AssetRecord(
            asset_id="caption-dialogue-asset",
            asset_type=AssetType.CAPTION,
            artifact_path=caption_path,
            sha256=imported.track_sha256,
            size_bytes=len(imported.track_bytes),
            mime_type="application/json",
            source_kind=AssetSourceKind.DERIVED,
            tool=ToolIdentity(name="offline-fixture", version="1"),
            input_artifact_ids=(dialogue.asset_id,),
            input_fingerprint=dialogue.sha256,
            creation_receipt_id=track.creation_receipt_id,
            usage_license="fixture",
            caption_metadata=CaptionAssetMetadata(
                caption_track_id=track.caption_track_id,
                language=track.language,
                source_audio_asset_id=dialogue.asset_id,
                source_audio_sha256=dialogue.sha256,
                script_hash=track.script_hash,
                transcript_hash=track.transcript_hash,
                segment_count=1,
                word_count=0,
                segmentation_policy_id=track.segmentation_policy.policy_id,
                segmentation_policy_version=track.segmentation_policy.policy_version,
                alignment_receipt_id=track.alignment_receipt_id,
                timing_fingerprint=track.timing_fingerprint,
                style_reference_id=CAPTION_STYLE.artifact_id,
                style_reference_revision=CAPTION_STYLE.revision,
                style_content_hash=CAPTION_STYLE.content_hash,
            ),
        )
        caption_record = caption
        caption_artifacts = (
            PreparedArtifact(
                caption_path, imported.track_bytes, imported.track_sha256
            ),
            PreparedArtifact(
                CAPTION_STYLE.path, CAPTION_STYLE_BYTES, CAPTION_STYLE_HASH
            ),
        )
    registry = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id="0" * 64,
        content_hash="0" * 64,
        assets=tuple(records),
    )
    digest = registry_semantic_sha256(registry)
    compiled = replace(
        compiled,
        registry=registry.model_copy(
            update={"revision_id": digest, "content_hash": digest}
        ),
        artifacts=(*compiled.artifacts, *prepared),
    )
    bootstrap_ecommerce_production_project(
        root,
        attempt_id="ecommerce-offline-e2e-bootstrap",
        compiled=compiled,
    )
    if with_caption:
        assert caption_record is not None
        committer = ProductionStateCommitter(root)
        manifest = committer._read_manifest()
        loaded = load_production_project(root / "project.yaml")
        candidate = AssetRegistrySnapshot(
            schema_version="2.1",
            revision_id="0" * 64,
            content_hash="0" * 64,
            assets=loaded.registry.assets + (caption_record,),
        )
        candidate_hash = registry_semantic_sha256(candidate)
        candidate = candidate.model_copy(
            update={"revision_id": candidate_hash, "content_hash": candidate_hash}
        )
        project_bytes = (root / manifest.active_project.path).read_bytes()
        committer.commit(
            prepare_audio_registry_commit(
                manifest=manifest,
                project=loaded.project,
                base_registry=loaded.registry,
                registry=candidate,
                attempt_id="ecommerce-offline-e2e-caption-import",
                artifacts=caption_artifacts,
                active_project_artifact=PreparedArtifact(
                    manifest.active_project.path,
                    project_bytes,
                    manifest.active_project.file_sha256,
                ),
            )
        )
    inputs = ProductionDependencyInputs(
        project=load_production_project(root / "project.yaml"),
        composition_spec=composition_spec,
        renderer=RendererIdentity(kind=RendererKind.HYPERFRAMES, version="0.7.103"),
        voice_requests=(),
        resolver_contract_fingerprint="1" * 64,
        source_materializer_contract_fingerprint="2" * 64,
        render_contract_fingerprint="3" * 64,
        caption_style_fingerprints=(
            CAPTION_STYLE_FINGERPRINTS if with_caption else ()
        ),
    )
    final_output = FinalOutputContract(
        goal_id="ecommerce-offline-e2e-final-output",
        goal_version="1",
        user_goal="Deliver the exact accepted offline Ecommerce ad.",
        requirements=tuple(
            FinalOutputRequirement(
                requirement_id=item.requirement_id,
                observable=item.description,
                proof="evaluator",
            )
            for item in handoff.acceptance_requirements
            if item.scope == "FINAL_OUTPUT"
        ),
    )
    caption_policy = None
    if with_caption:
        preview = seal_artifact(
            composition_spec.model_copy(
                update={
                    "revision": composition_spec.revision + 1,
                    "content_hash": "0" * 64,
                    "shot_ids": ("shot-hero",),
                    "layers": tuple(
                        layer
                        for layer in composition_spec.layers
                        if layer.shot_id == "shot-hero"
                    ),
                    "transitions": (),
                    "audio_tracks": tuple(
                        track.model_copy(
                            update={"trim_duration_samples": 144_000}
                        )
                        if track.track_id == "audio-music"
                        else track
                        for track in composition_spec.audio_tracks
                    ),
                    "commercial_graphics": tuple(
                        graphic
                        for graphic in composition_spec.commercial_graphics
                        if graphic.shot_id == "shot-hero"
                    ),
                }
            )
        )
        loaded = load_production_project(root / "project.yaml")
        preview_timeline = resolve_composition(
            loaded, preview, renderer_version="0.7.103"
        )
        assert len(preview_timeline.caption_cues) == 1
        caption_policy = make_caption_quality_policy(loaded, preview_timeline)
    _activate_offline_ecommerce_policy(
        root,
        inputs,
        output=OUTPUT,
        final_output=final_output,
        required_layers=(
            (QaLayer.TECHNICAL, QaLayer.LAYOUT, QaLayer.CAPTION, QaLayer.SEMANTIC)
            if with_caption
            else (QaLayer.TECHNICAL, QaLayer.LAYOUT, QaLayer.SEMANTIC)
        ),
        caption_policy=caption_policy,
    )


def test_canonical_two_shot_job_closes_offline_and_replays_without_effect(
    tmp_path: Path,
    monkeypatch,
) -> None:
    handoff, plan, compiled = _handoff_and_compiled()
    request = _request(tmp_path, handoff)
    assert (
        EcommerceProductionJobService().inspect(request, handoff).next_action
        is EcommerceJobNextAction.BOOTSTRAP_PROJECT
    )
    assert tuple(
        (item.target_shot_id, item.invoke_video_provider)
        for item in compiled.commercial_execution_projections
    ) == (("shot-hero", False), ("shot-proof", True))
    _bootstrap(tmp_path, handoff, compiled.composition_spec)
    execution, provider = _real_input(
        root=tmp_path,
        execution=SimpleNamespace(handoff=compiled),
        shot_id="shot-proof",
        composition_spec=compiled.composition_spec,
        output=OUTPUT,
        artifact_bytes=VIDEO.read_bytes(),
    )
    shots = EcommerceShotExecutionPlan(
        handoff=compiled,
        plan=plan,
        shots=(execution,),
    )
    job = EcommerceProductionJobService()

    projected = job.inspect(request, handoff, shot_execution=shots)
    advanced = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=shots,
    )
    assert projected.next_action is EcommerceJobNextAction.GENERATE_SHOT
    assert projected.next_shot_id == "shot-proof"
    assert advanced.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION, advanced
    assert provider.submit_calls == 1
    assert provider.fetch_calls == 1
    _refresh_p7_ready_project_registry_nodes(
        tmp_path, ProductionStateCommitter(tmp_path)
    )

    final_spec = build_video_candidate_composition_spec(
        compiled.composition_spec,
        target_shot_id="shot-proof",
        target_asset_role="final_visual",
        output_asset_id="canonical-ecommerce-shot-proof-video",
    )
    final_handoff = compiled.model_copy(update={"composition_spec": final_spec})
    composition, prepared, fixture = prepare_offline_ecommerce_render(
        tmp_path,
        monkeypatch,
        handoff,
        plan,
        final_handoff,
        attempt_id="ecommerce-offline-e2e-render",
        media_path=FINAL_VIDEO,
    )
    prepared_projection = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PREPARE_COMPOSITION,
        shot_execution=shots,
        composition_execution=composition,
    )
    rendered = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.RENDER_FINAL,
        shot_execution=shots,
        composition_execution=composition,
    )

    assert prepared_projection.next_action is EcommerceJobNextAction.RENDER_FINAL
    assert rendered.next_action is EcommerceJobNextAction.REVIEW_FINAL, rendered
    assert fixture.runner.calls
    assert load_production_project(tmp_path / "project.yaml").manifest.active_render_state

    loaded = load_production_project(tmp_path / "project.yaml")
    policy = loaded.qa_policy
    assert policy is not None and policy.final_output is not None
    for layer in (QaLayer.TECHNICAL, QaLayer.LAYOUT):
        _Manifest25ReviewFixture(
            root=tmp_path,
            committer=ProductionStateCommitter(tmp_path),
            timeline=prepared.timeline,
            policy=policy,
            review_layer=layer,
            review_attempt_id=f"ecommerce-offline-e2e-{layer.value}",
            evidence_factory=(
                _measured_technical_windows if layer is QaLayer.TECHNICAL else None
            ),
        ).run_required_review()
    universal = UniversalQaProfile.create(
        profile_id="ecommerce-offline-e2e",
        profile_version="1",
        delivery_profile=prepared.timeline.delivery_profile,
        applicability=UniversalQaApplicability(
            has_audio=True,
            has_graphics=True,
            has_safe_area_requirements=True,
            has_transitions=True,
        ),
        required_hard_checks=(
            UniversalHardCheck.ASSET_PROVENANCE,
            UniversalHardCheck.MEDIA_DECODE,
            UniversalHardCheck.TIMELINE_BINDING,
            UniversalHardCheck.RENDER_OUTPUT,
            UniversalHardCheck.AUDIO_CAPTION_BINDING,
        ),
        required_review_layers=(QaLayer.TECHNICAL, QaLayer.LAYOUT),
    )
    review = EcommercePostMediaExecutionPlan(
        handoff=final_handoff,
        plan=plan,
        shot_facades=shots.build_facades(handoff, project_root=tmp_path),
        committer=ProductionStateCommitter(tmp_path),
        universal_profile=universal,
        run_hard_check=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS, current=True
        ),
        run_review_layer=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS, current=True
        ),
        tool_identity=REVIEW_TOOL,
        evaluate=lambda target, _profile: EcommerceWholeAdEvaluationPayload(
            domain_acceptance=_passing_payload(),
            final_output=FinalOutputObservation(
                contract_hash=policy.final_output.contract_hash,
                review_request_content_hash=target.review_request_content_hash,
                findings=tuple(
                    FinalOutputFinding(
                        requirement_id=item.requirement_id,
                        verdict="pass",
                        observation="Observed on exact offline final candidate.",
                    )
                    for item in policy.final_output.requirements
                ),
            ),
        ),
        review_attempt_id="ecommerce-offline-e2e-semantic",
        review_request_id="ecommerce-offline-e2e-semantic-request",
        evidence_id="ecommerce-offline-e2e-semantic-evidence",
        review_id="ecommerce-offline-e2e-semantic-review",
        final_acceptance_id="ecommerce-offline-e2e-acceptance",
    )
    reviewed = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.REVIEW_FINAL,
        shot_execution=shots,
        composition_execution=composition,
        review_execution=review,
    )
    assert reviewed.next_action is EcommerceJobNextAction.PACKAGE_DELIVERY, reviewed

    delivery = EcommerceDeliveryExecutionPlan(
        delivery_root=tmp_path / "deliveries",
        plan=plan,
        compiled_handoff=final_handoff,
        exported_at="2026-09-19T12:00:00+00:00",
        tool_identity=ToolIdentity(name="ecommerce-offline-packager", version="1"),
    )
    delivered = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PACKAGE_DELIVERY,
        shot_execution=shots,
        composition_execution=composition,
        review_execution=review,
        delivery_execution=delivery,
    )
    assert delivered.next_action is EcommerceJobNextAction.COMPLETE, delivered
    packaged = delivery.inspect(
        handoff, project_root=tmp_path, job_id=request.job_id
    )
    assert packaged is not None
    assert packaged.render_output_sha256 == hashlib.sha256(
        FINAL_VIDEO.read_bytes()
    ).hexdigest()
    manifest_before = (tmp_path / "state/manifest.json").read_bytes()
    files_before = {
        path.relative_to(delivery.delivery_root): (
            path.read_bytes(),
            path.stat().st_mtime_ns,
        )
        for path in delivery.delivery_root.rglob("*")
        if path.is_file()
    }
    render_call_count = len(fixture.runner.calls)
    replay = EcommerceProductionJobService().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PACKAGE_DELIVERY,
        shot_execution=shots,
        composition_execution=composition,
        review_execution=review,
        delivery_execution=delivery,
    )
    assert replay.next_action is EcommerceJobNextAction.COMPLETE
    assert delivery.inspect(
        handoff, project_root=tmp_path, job_id=request.job_id
    ) == packaged
    assert (tmp_path / "state/manifest.json").read_bytes() == manifest_before
    assert len(fixture.runner.calls) == render_call_count
    assert (provider.submit_calls, provider.fetch_calls) == (1, 1)
    assert {
        path.relative_to(delivery.delivery_root): (
            path.read_bytes(),
            path.stat().st_mtime_ns,
        )
        for path in delivery.delivery_root.rglob("*")
        if path.is_file()
    } == files_before


def test_captioned_job_repairs_timing_via_local_recomposition_without_regeneration(
    tmp_path: Path, monkeypatch
) -> None:
    handoff, plan, compiled = _handoff_and_compiled(with_caption=True)
    request = _request(tmp_path, handoff)
    _bootstrap(tmp_path, handoff, compiled.composition_spec, with_caption=True)
    execution, provider = _real_input(
        root=tmp_path,
        execution=SimpleNamespace(handoff=compiled),
        shot_id="shot-proof",
        composition_spec=compiled.composition_spec,
        output=OUTPUT,
        artifact_bytes=VIDEO.read_bytes(),
        caption_style_fingerprints=CAPTION_STYLE_FINGERPRINTS,
    )
    shots = EcommerceShotExecutionPlan(
        handoff=compiled, plan=plan, shots=(execution,)
    )
    job = EcommerceProductionJobService()
    assert job.inspect(request, handoff, shot_execution=shots).next_action is EcommerceJobNextAction.GENERATE_SHOT
    generated = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=shots,
    )
    assert generated.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION
    assert (provider.submit_calls, provider.fetch_calls) == (1, 1)
    _refresh_p7_ready_project_registry_nodes(
        tmp_path, ProductionStateCommitter(tmp_path)
    )
    final_spec = build_video_candidate_composition_spec(
        compiled.composition_spec,
        target_shot_id="shot-proof",
        target_asset_role="final_visual",
        output_asset_id="canonical-ecommerce-shot-proof-video",
    )
    loaded = load_production_project(tmp_path / "project.yaml")
    timeline = resolve_composition(
        loaded, final_spec, renderer_version="0.7.103"
    )
    assert timeline.caption_cues
    assert loaded.qa_policy is not None
    assert loaded.qa_policy.caption_policy is not None
    final_handoff = compiled.model_copy(update={"composition_spec": final_spec})
    composition, prepared, fixture = prepare_offline_ecommerce_render(
        tmp_path,
        monkeypatch,
        handoff,
        plan,
        final_handoff,
        attempt_id="ecommerce-offline-e2e-caption-render-first",
        media_path=FINAL_VIDEO,
    )
    assert prepared.timeline.caption_cues
    assert job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PREPARE_COMPOSITION,
        shot_execution=shots,
        composition_execution=composition,
    ).next_action is EcommerceJobNextAction.RENDER_FINAL
    assert job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.RENDER_FINAL,
        shot_execution=shots,
        composition_execution=composition,
    ).next_action is EcommerceJobNextAction.REVIEW_FINAL
    assert fixture.runner.calls
    first_render_state = load_production_project(
        tmp_path / "project.yaml"
    ).manifest.active_render_state
    assert first_render_state is not None

    policy = load_production_project(tmp_path / "project.yaml").qa_policy
    assert policy is not None and policy.final_output is not None
    for layer in (QaLayer.TECHNICAL, QaLayer.LAYOUT):
        _Manifest25ReviewFixture(
            root=tmp_path,
            committer=ProductionStateCommitter(tmp_path),
            timeline=prepared.timeline,
            policy=policy,
            review_layer=layer,
            review_attempt_id=f"ecommerce-offline-caption-first-{layer.value}",
            evidence_factory=(
                _measured_technical_windows if layer is QaLayer.TECHNICAL else None
            ),
        ).run_required_review()

    def failing_timing(context, caption_policy):
        payload = passing_caption_evidence_payload(context, caption_policy)
        return payload.model_copy(
            update={
                "findings": tuple(
                    finding.model_copy(
                        update={
                            "verdict": "fail",
                            "reason_code": CaptionFindingReasonCode.TIMING_OUT_OF_BOUNDS,
                            "observation_fingerprint": canonical_sha256(
                                {"cue": finding.covered_subject_ids, "timing": "failed"}
                            ),
                        }
                    )
                    if finding.requirement_group is CaptionRequirementGroup.TIMING_CONTRACT
                    else finding
                    for finding in payload.findings
                )
            }
        )

    universal = UniversalQaProfile.create(
        profile_id="ecommerce-offline-caption",
        profile_version="1",
        delivery_profile=prepared.timeline.delivery_profile,
        applicability=UniversalQaApplicability(
            has_audio=True,
            has_graphics=True,
            has_safe_area_requirements=True,
            has_transitions=True,
            has_captions=True,
        ),
        required_hard_checks=(
            UniversalHardCheck.ASSET_PROVENANCE,
            UniversalHardCheck.MEDIA_DECODE,
            UniversalHardCheck.TIMELINE_BINDING,
            UniversalHardCheck.RENDER_OUTPUT,
            UniversalHardCheck.AUDIO_CAPTION_BINDING,
        ),
        required_review_layers=(QaLayer.TECHNICAL, QaLayer.LAYOUT, QaLayer.CAPTION),
    )
    first_review = EcommercePostMediaExecutionPlan(
        handoff=final_handoff,
        plan=plan,
        shot_facades=shots.build_facades(handoff, project_root=tmp_path),
        committer=ProductionStateCommitter(tmp_path),
        universal_profile=universal,
        run_hard_check=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS, current=True
        ),
        run_review_layer=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS, current=True
        ),
        tool_identity=REVIEW_TOOL,
        evaluate=lambda target, _profile: EcommerceWholeAdEvaluationPayload(
            domain_acceptance=_passing_payload(),
            final_output=FinalOutputObservation(
                contract_hash=policy.final_output.contract_hash,
                review_request_content_hash=target.review_request_content_hash,
                findings=tuple(
                    FinalOutputFinding(
                        requirement_id=item.requirement_id,
                        verdict="pass",
                        observation="Offline fixture observation.",
                    )
                    for item in policy.final_output.requirements
                ),
            ),
        ),
        review_attempt_id="ecommerce-offline-caption-first-semantic",
        review_request_id="ecommerce-offline-caption-first-semantic-request",
        evidence_id="ecommerce-offline-caption-first-semantic-evidence",
        review_id="ecommerce-offline-caption-first-semantic-review",
        final_acceptance_id="ecommerce-offline-caption-first-acceptance",
        caption_review_execution=CaptionReviewExecution(
            evaluator=failing_timing,
            tool_identity=CAPTION_EVALUATOR_TOOL,
            evidence_strength=CaptionEvidenceStrength.EXPLICIT_EVALUATOR,
            attempt_id="ecommerce-offline-caption-first-caption",
            request_id="ecommerce-offline-caption-first-caption-request",
            evidence_id="ecommerce-offline-caption-first-caption-evidence",
            review_id="ecommerce-offline-caption-first-caption-review",
        ),
    )
    failed = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.REVIEW_FINAL,
        shot_execution=shots,
        composition_execution=composition,
        review_execution=first_review,
    )
    assert failed.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION, failed
    assert first_review.inspect_frontier(
        handoff, project_root=tmp_path
    ) is EcommerceFinalReviewFrontier.PREPARE_COMPOSITION

    unchanged = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PREPARE_COMPOSITION,
        shot_execution=shots,
        composition_execution=composition,
        review_execution=first_review,
    )
    assert unchanged.next_action is EcommerceJobNextAction.BLOCKED
    assert unchanged.blocker is not None
    assert unchanged.blocker.blocker_code == "ECOMMERCE_COMPOSITION_REPAIR_UNCHANGED"
    accepted_shot = next(
        item
        for item in load_production_project(tmp_path / "project.yaml").registry.assets
        if item.asset_id == "canonical-ecommerce-shot-proof-video"
    )
    corrected_spec = seal_artifact(
        final_spec.model_copy(
            update={
                "revision": final_spec.revision + 1,
                "content_hash": "0" * 64,
                "audio_tracks": tuple(
                    track.model_copy(update={"start_sample": 25_000})
                    if track.track_id == "audio-dialogue"
                    else track
                    for track in final_spec.audio_tracks
                ),
            }
        )
    )
    repaired_handoff = compiled.model_copy(update={"composition_spec": corrected_spec})
    repaired_composition, repaired_prepared, repaired_fixture = (
        prepare_offline_ecommerce_render(
            tmp_path,
            monkeypatch,
            handoff,
            plan,
            repaired_handoff,
            attempt_id="ecommerce-offline-e2e-caption-render-repair",
            media_path=FINAL_VIDEO,
        )
    )
    loaded = load_production_project(tmp_path / "project.yaml")
    repaired_graph = build_production_dependency_graph(
        ProductionDependencyInputs(
            project=loaded,
            composition_spec=corrected_spec,
            renderer=RendererIdentity(kind=RendererKind.HYPERFRAMES, version="0.7.103"),
            voice_requests=(),
            resolver_contract_fingerprint="1" * 64,
            source_materializer_contract_fingerprint="2" * 64,
            render_contract_fingerprint="3" * 64,
            caption_style_fingerprints=CAPTION_STYLE_FINGERPRINTS,
        )
    )
    repaired_fixture.dependency_graph = repaired_graph
    repaired_fixture.candidate_dependency_states = resolve_dependency_state(
        repaired_graph, loaded.manifest.dependency_states
    ).states
    assert repaired_prepared.timeline.composition_fingerprint != (
        prepared.timeline.composition_fingerprint
    )
    assert repaired_prepared.timeline.caption_cues[0].start_sample == (
        prepared.timeline.caption_cues[0].start_sample + 1_000
    )
    repaired_frontier = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PREPARE_COMPOSITION,
        shot_execution=shots,
        composition_execution=repaired_composition,
        review_execution=first_review,
    )
    assert repaired_frontier.next_action is EcommerceJobNextAction.RENDER_FINAL
    rerendered = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.RENDER_FINAL,
        shot_execution=shots,
        composition_execution=repaired_composition,
        review_execution=first_review,
    )
    assert rerendered.next_action is EcommerceJobNextAction.REVIEW_FINAL, rerendered
    assert repaired_fixture.runner.calls
    assert (provider.submit_calls, provider.fetch_calls) == (1, 1)
    assert load_production_project(
        tmp_path / "project.yaml"
    ).manifest.active_render_state != first_render_state
    assert next(
        item
        for item in load_production_project(tmp_path / "project.yaml").registry.assets
        if item.asset_id == accepted_shot.asset_id
    ) == accepted_shot
    for layer in (QaLayer.TECHNICAL, QaLayer.LAYOUT):
        _Manifest25ReviewFixture(
            root=tmp_path,
            committer=ProductionStateCommitter(tmp_path),
            timeline=repaired_prepared.timeline,
            policy=policy,
            review_layer=layer,
            review_attempt_id=f"ecommerce-offline-caption-repair-{layer.value}",
            evidence_factory=(
                _measured_technical_windows if layer is QaLayer.TECHNICAL else None
            ),
        ).run_required_review()
    repaired_review = replace(
        first_review,
        handoff=repaired_handoff,
        committer=ProductionStateCommitter(tmp_path),
        review_attempt_id="ecommerce-offline-caption-repair-semantic",
        review_request_id="ecommerce-offline-caption-repair-semantic-request",
        evidence_id="ecommerce-offline-caption-repair-semantic-evidence",
        review_id="ecommerce-offline-caption-repair-semantic-review",
        final_acceptance_id="ecommerce-offline-caption-repair-acceptance",
        caption_review_execution=CaptionReviewExecution(
            evaluator=passing_caption_evidence_payload,
            tool_identity=CAPTION_EVALUATOR_TOOL,
            evidence_strength=CaptionEvidenceStrength.EXPLICIT_EVALUATOR,
            attempt_id="ecommerce-offline-caption-repair-caption",
            request_id="ecommerce-offline-caption-repair-caption-request",
            evidence_id="ecommerce-offline-caption-repair-caption-evidence",
            review_id="ecommerce-offline-caption-repair-caption-review",
        ),
    )
    reviewed = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.REVIEW_FINAL,
        shot_execution=shots,
        composition_execution=repaired_composition,
        review_execution=repaired_review,
    )
    assert reviewed.next_action is EcommerceJobNextAction.PACKAGE_DELIVERY, reviewed
    delivery = EcommerceDeliveryExecutionPlan(
        delivery_root=tmp_path / "deliveries",
        plan=plan,
        compiled_handoff=repaired_handoff,
        exported_at="2026-09-19T12:00:00+00:00",
        tool_identity=ToolIdentity(name="ecommerce-offline-packager", version="1"),
    )
    delivered = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PACKAGE_DELIVERY,
        shot_execution=shots,
        composition_execution=repaired_composition,
        review_execution=repaired_review,
        delivery_execution=delivery,
    )
    assert delivered.next_action is EcommerceJobNextAction.COMPLETE, delivered
    packaged = delivery.inspect(handoff, project_root=tmp_path, job_id=request.job_id)
    assert packaged is not None
    final_loaded = load_production_project(tmp_path / "project.yaml")
    assert final_loaded.render_state is not None
    assert packaged.render_output_sha256 == final_loaded.render_state.output.file_sha256
    assert final_loaded.manifest.final_acceptance_state is not None
    assert final_loaded.manifest.final_acceptance_state.active_receipt is not None
    assert packaged.final_acceptance_content_hash == (
        final_loaded.manifest.final_acceptance_state.active_receipt.content_hash
    )
    assert (provider.submit_calls, provider.fetch_calls) == (1, 1)
