from collections import UserDict
from pathlib import Path
from typing import get_args

import pytest
from pydantic import ValidationError

import ai_video.production as production
import ai_video.production.models as production_models
import ai_video.production.paths as production_paths
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256, seal_artifact, verify_artifact_hash
from ai_video.production.models import (
    AUDIO_KIND_TO_ASSET_TYPE,
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    AudioAssetMetadata,
    AudioChannelLayout,
    AudioKind,
    AudioLoudnessMetadata,
    AudioSource,
    AudioTrackSpec,
    CaptionAssetMetadata,
    CaptionSegment,
    CaptionSegmentationPolicy,
    CaptionStyleReference,
    CaptionStyleBindingContract,
    CaptionTrack,
    CaptionTrackBinding,
    CaptionWord,
    CompositionLayerSpec,
    CompositionSpec,
    CompositionDirective,
    DeliveryProfile,
    DependencyEdge,
    DependencyGraphSnapshot,
    DependencyGraphSnapshotPointer,
    DependencyGraphTransition,
    DependencyLifecycle,
    DependencyNode,
    DependencyNodeKind,
    DependencyNodeState,
    DependencyReason,
    DependencySemanticRole,
    DurationPolicy,
    FingerprintContribution,
    FinalAcceptanceState,
    LoadedProductionProject,
    MeasuredRenderMetadata,
    MeasuredAudioRenderMetadata,
    MotionDirective,
    ProductionManifest,
    QaLayer,
    QaPolicyPointer,
    QaVerdict,
    ProjectDependencyEvidence,
    ProjectSnapshotPointer,
    RecoveryDisposition,
    RecoveryItem,
    RecoveryReport,
    ReviewLayerState,
    ReviewLifecycle,
    RegistryDependencyEvidence,
    RegistrySnapshotPointer,
    RenderArtifactPointer,
    RenderDependencyEvidence,
    RenderOutputPointer,
    RenderReceipt,
    RendererAudioBinding,
    RendererCaptionBinding,
    RendererAssetBinding,
    RendererCheckReceipt,
    RendererIdentity,
    RendererPolicy,
    RendererSelectionReceipt,
    RendererSourceReceipt,
    RenderSourceBundlePointer,
    RenderSourceFilePointer,
    RenderStateSnapshot,
    RenderStateSnapshotPointer,
    ResolvedTimeline,
    ResolvedCaptionCue,
    ResolvedDuckingSpec,
    ResolvedAudioSpan,
    ResolvedVisualSpan,
    SourceReference,
    StateCommitAttempt,
    StateCommitStatus,
    Story,
    StoryBeat,
    ToolIdentity,
    VoiceRequestReceipt,
)


ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64
TWO_HASH = "2" * 64
THREE_HASH = "3" * 64
FOUR_HASH = "4" * 64
FIVE_HASH = "5" * 64
SIX_HASH = "6" * 64
SEVEN_HASH = "7" * 64
EIGHT_HASH = "8" * 64
NINE_HASH = "9" * 64


def make_audio_source() -> AudioSource:
    return AudioSource(
        kind="generated",
        provider_or_tool=ToolIdentity(name="fake-voice", version="1.0"),
        input_artifact_ids=("script-1",),
        input_fingerprint=ONE_HASH,
        original_reference="fixture://dialogue-1",
    )


def make_audio_metadata(kind: AudioKind = AudioKind.DIALOGUE) -> AudioAssetMetadata:
    speech = kind in {AudioKind.DIALOGUE, AudioKind.NARRATION}
    return AudioAssetMetadata(
        audio_kind=kind,
        source=make_audio_source(),
        speaker_id="speaker-1" if kind is AudioKind.DIALOGUE else None,
        voice_id="voice-1" if speech else None,
        language="en" if speech else None,
        script_hash=TWO_HASH if speech else None,
        duration_samples=96_000,
        sample_rate_hz=48_000,
        channels=1,
        channel_layout=AudioChannelLayout.MONO,
        codec_name="pcm_s16le",
        loudness=AudioLoudnessMetadata(
            integrated_lufs_milli=-23_000,
            true_peak_dbfs_milli=-1_000,
            measurement_standard="ebu_r128",
        ),
        provenance_receipt_id="provenance-1",
        alignment_receipt_id="alignment-1" if speech else None,
    )


def make_asset_record(
    *,
    asset_type: AssetType = AssetType.VOICE,
    audio_metadata: AudioAssetMetadata | None = None,
    caption_metadata: CaptionAssetMetadata | None = None,
    remote: bool = False,
) -> AssetRecord:
    egress: dict[str, object]
    if remote:
        egress = {
            "remote": True,
            "destination": "https://api.elevenlabs.io",
            "authorization_receipt_id": "egress-1",
            "request_fingerprint": THREE_HASH,
            "payload_fingerprint": FOUR_HASH,
            "retention_mode": "provider_standard",
            "provider_policy_snapshot_id": "policy-2026-08-10",
        }
    else:
        egress = {
            "remote": False,
            "destination": None,
            "authorization_receipt_id": None,
        }
    return AssetRecord(
        asset_id="asset-1",
        asset_type=asset_type,
        artifact_path=Path(f"assets/files/{FIVE_HASH}.wav"),
        sha256=FIVE_HASH,
        size_bytes=64,
        mime_type="audio/wav" if asset_type is not AssetType.CAPTION else "application/json",
        duration_seconds=2.0 if asset_type is not AssetType.CAPTION else None,
        source_kind=AssetSourceKind.GENERATED,
        tool=ToolIdentity(name="fixture", version="1"),
        input_fingerprint=SIX_HASH,
        creation_receipt_id="creation-1",
        usage_license="fixture-only",
        egress=egress,
        audio_metadata=audio_metadata,
        caption_metadata=caption_metadata,
    )


def make_caption_track(*, style_reference_id: str | None = "style-1") -> CaptionTrack:
    return CaptionTrack(
        **versioned_fields("caption-track-1", SEVEN_HASH),
        schema_version="2.1",
        caption_track_id="caption-track-1",
        language="en",
        script_hash=TWO_HASH,
        transcript_hash=THREE_HASH,
        source_audio_asset_id="asset-1",
        source_audio_sha256=FIVE_HASH,
        source_sample_rate_hz=48_000,
        segments=(
            CaptionSegment(
                segment_id="segment-1",
                text="Hello world",
                start_sample=0,
                end_sample=48_000,
                speaker_id="speaker-1",
                words=(
                    CaptionWord(
                        text="Hello",
                        start_sample=0,
                        end_sample=20_000,
                        speaker_id="speaker-1",
                        confidence_milli=990,
                    ),
                    CaptionWord(
                        text="world",
                        start_sample=22_000,
                        end_sample=48_000,
                        speaker_id="speaker-1",
                        confidence_milli=None,
                    ),
                ),
                confidence_milli=980,
            ),
        ),
        segmentation_policy=CaptionSegmentationPolicy(
            policy_id="sentence-v1",
            policy_version="1",
            max_characters=42,
            max_lines=2,
            break_strategy="sentence",
        ),
        alignment_provider="fake",
        alignment_model=None,
        alignment_receipt_id="alignment-1",
        style_reference_id=style_reference_id,
        timing_fingerprint=EIGHT_HASH,
    )


def make_caption_metadata(*, with_style: bool = True) -> CaptionAssetMetadata:
    return CaptionAssetMetadata(
        caption_track_id="caption-track-1",
        language="en",
        source_audio_asset_id="asset-1",
        source_audio_sha256=FIVE_HASH,
        script_hash=TWO_HASH,
        transcript_hash=THREE_HASH,
        segment_count=1,
        word_count=2,
        segmentation_policy_id="sentence-v1",
        segmentation_policy_version="1",
        alignment_receipt_id="alignment-1",
        timing_fingerprint=EIGHT_HASH,
        style_reference_id="style-1" if with_style else None,
        style_reference_revision=1 if with_style else None,
        style_content_hash=NINE_HASH if with_style else None,
    )


def make_project_pointer() -> ProjectSnapshotPointer:
    return ProjectSnapshotPointer(
        path=Path("project.yaml"),
        revision=1,
        content_hash=ZERO_HASH,
        file_sha256=ONE_HASH,
    )


def make_registry_pointer() -> RegistrySnapshotPointer:
    return RegistrySnapshotPointer(
        path=Path(f"assets/registry.{ZERO_HASH}.json"),
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        file_sha256=ONE_HASH,
    )


def make_canonical_project_pointer(
    *, content_hash: str = ZERO_HASH, file_sha256: str = ONE_HASH
) -> ProjectSnapshotPointer:
    return ProjectSnapshotPointer(
        path=Path(f"state/projects/project.1.{content_hash}.yaml"),
        revision=1,
        content_hash=content_hash,
        file_sha256=file_sha256,
    )


def make_alternate_registry_pointer() -> RegistrySnapshotPointer:
    return RegistrySnapshotPointer(
        path=Path(f"assets/registry.{TWO_HASH}.json"),
        revision_id=TWO_HASH,
        content_hash=TWO_HASH,
        file_sha256=THREE_HASH,
    )


def make_render_state_pointer(content_hash: str = THREE_HASH) -> RenderStateSnapshotPointer:
    return RenderStateSnapshotPointer(
        path=Path(f"state/render/states/{content_hash}.json"),
        revision=1,
        content_hash=content_hash,
        file_sha256=ZERO_HASH,
    )


def make_state_manifest(**overrides: object) -> ProductionManifest:
    data: dict[str, object] = {
        "project_id": "comic-demo",
        "manifest_revision": 1,
        "active_project": make_project_pointer(),
        "active_registry": make_registry_pointer(),
    }
    data.update(overrides)
    return ProductionManifest(**data)


def versioned_fields(artifact_id: str, content_hash: str) -> dict[str, object]:
    return {
        "artifact_id": artifact_id,
        "revision": 1,
        "content_hash": content_hash,
        "creation_receipt_id": f"receipt-{artifact_id}",
        "source_provenance": (
            SourceReference(kind="derived", reference="p3-test-fixture"),
        ),
    }


def make_renderer_selection() -> RendererSelectionReceipt:
    return RendererSelectionReceipt(
        receipt_id="select-1",
        attempt_id="attempt-1",
        requested_kind="hyperframes",
        selected_kinds=("hyperframes",),
        renderer_version="0.7.103",
        timeline_fingerprint=FOUR_HASH,
        current_project=make_project_pointer(),
        current_registry=make_registry_pointer(),
    )


def make_resolved_timeline() -> ResolvedTimeline:
    return ResolvedTimeline(
        **versioned_fields("timeline-1", TWO_HASH),
        timeline_id="timeline-1",
        composition_spec_id="composition-1",
        composition_spec_revision=1,
        composition_spec_hash=THREE_HASH,
        delivery_profile=DeliveryProfile(width=320, height=180, fps=24),
        sample_rate=48_000,
        renderer=RendererIdentity(kind="hyperframes", version="0.7.103"),
        visual_spans=(
            ResolvedVisualSpan(
                layer_id="layer-1",
                shot_id="shot-1",
                asset_role="primary_image",
                asset_id="asset-1",
                asset_sha256=FIVE_HASH,
                asset_mime_type="image/png",
                materialized_path=Path(f"assets/files/{FIVE_HASH}.png"),
                start_frame=0,
                duration_frames=48,
                start_sample=0,
                duration_samples=96_000,
                trim_start_frame=0,
                transform={},
                opacity_milli=1000,
                z_index=0,
            ),
        ),
        total_frames=48,
        total_samples=96_000,
        composition_fingerprint=FOUR_HASH,
    )


def make_source_bundle() -> RenderSourceBundlePointer:
    root = Path(f"state/render/sources/{SIX_HASH}")
    return RenderSourceBundlePointer(
        root_path=root,
        bundle_sha256=SIX_HASH,
        index=RenderSourceFilePointer(
            path=root / "index.html",
            file_sha256=SEVEN_HASH,
            size_bytes=100,
        ),
        assets=(
            RenderSourceFilePointer(
                path=root / "assets" / f"{FIVE_HASH}.png",
                file_sha256=FIVE_HASH,
                size_bytes=10,
            ),
        ),
    )


def make_source_receipt() -> RendererSourceReceipt:
    return RendererSourceReceipt(
        **versioned_fields("source-receipt-1", EIGHT_HASH),
        attempt_id="attempt-1",
        renderer=RendererIdentity(kind="hyperframes", version="0.7.103"),
        timeline_fingerprint=FOUR_HASH,
        source_bundle=make_source_bundle(),
        source_sha256=SEVEN_HASH,
        asset_bindings=(
            RendererAssetBinding(
                asset_id="asset-1",
                asset_sha256=FIVE_HASH,
                asset_mime_type="image/png",
                materialized_path=Path(
                    f"state/render/sources/{SIX_HASH}/assets/{FIVE_HASH}.png"
                ),
            ),
        ),
        checks=(
            RendererCheckReceipt(
                command="lint",
                tool_version="0.7.103",
                exit_code=0,
                stdout_sha256=ZERO_HASH,
                stderr_sha256=ZERO_HASH,
                error_count=0,
                warning_count=0,
            ),
            RendererCheckReceipt(
                command="check",
                tool_version="0.7.103",
                exit_code=0,
                stdout_sha256=ZERO_HASH,
                stderr_sha256=ZERO_HASH,
                error_count=0,
                warning_count=0,
            ),
        ),
    )


def make_render_receipt() -> RenderReceipt:
    return RenderReceipt(
        **versioned_fields("render-receipt-1", NINE_HASH),
        attempt_id="attempt-1",
        renderer=RendererIdentity(kind="hyperframes", version="0.7.103"),
        timeline_fingerprint=FOUR_HASH,
        source_sha256=SEVEN_HASH,
        source_bundle_sha256=SIX_HASH,
        asset_hashes=(FIVE_HASH,),
        output_path=Path(f"state/render/outputs/{ONE_HASH}.mp4"),
        output_sha256=ONE_HASH,
        output_size_bytes=200,
        measured=MeasuredRenderMetadata(
            width=320,
            height=180,
            fps_num=24,
            fps_den=1,
            duration_frames=48,
            codec_name="h264",
        ),
        decoded_frame_fingerprint=TWO_HASH,
    )


def make_render_state_snapshot() -> RenderStateSnapshot:
    return RenderStateSnapshot(
        **versioned_fields("render-state-1", THREE_HASH),
        attempt_id="attempt-1",
        project=make_project_pointer(),
        registry=make_registry_pointer(),
        renderer_selection=make_renderer_selection(),
        renderer=RendererIdentity(kind="hyperframes", version="0.7.103"),
        timeline_fingerprint=FOUR_HASH,
        source_sha256=SEVEN_HASH,
        source_bundle_sha256=SIX_HASH,
        asset_hashes=(FIVE_HASH,),
        timeline=RenderArtifactPointer(
            path=Path(f"state/render/timelines/{TWO_HASH}.json"),
            revision=1,
            content_hash=TWO_HASH,
            file_sha256=ZERO_HASH,
        ),
        source_bundle=make_source_bundle(),
        source_receipt=RenderArtifactPointer(
            path=Path(f"state/render/source-receipts/{EIGHT_HASH}.json"),
            revision=1,
            content_hash=EIGHT_HASH,
            file_sha256=ZERO_HASH,
        ),
        render_receipt=RenderArtifactPointer(
            path=Path(f"state/render/render-receipts/{NINE_HASH}.json"),
            revision=1,
            content_hash=NINE_HASH,
            file_sha256=ZERO_HASH,
        ),
        output=RenderOutputPointer(
            path=Path(f"state/render/outputs/{ONE_HASH}.mp4"),
            file_sha256=ONE_HASH,
            size_bytes=200,
        ),
    )


def test_p4_audio_kinds_have_exact_registry_mapping():
    assert {item.value for item in AudioKind} == {
        "dialogue",
        "narration",
        "ambience",
        "sfx",
        "bgm",
    }
    assert AUDIO_KIND_TO_ASSET_TYPE == {
        AudioKind.DIALOGUE: AssetType.VOICE,
        AudioKind.NARRATION: AssetType.VOICE,
        AudioKind.AMBIENCE: AssetType.SFX,
        AudioKind.SFX: AssetType.SFX,
        AudioKind.BGM: AssetType.MUSIC,
    }
    assert "audio" not in {item.value for item in AssetType}


def test_audio_metadata_uses_measured_integer_samples_and_fixed_point_loudness():
    metadata = make_audio_metadata()
    assert metadata.duration_samples == 96_000
    assert metadata.loudness.integrated_lufs_milli == -23_000

    data = metadata.model_dump(mode="python")
    data["duration_samples"] = 1.5
    with pytest.raises(ValidationError):
        AudioAssetMetadata.model_validate(data)

    data = metadata.model_dump(mode="python")
    data["channels"] = 2
    with pytest.raises(ValidationError, match="layout"):
        AudioAssetMetadata.model_validate(data)

    data = metadata.model_dump(mode="python")
    data["loudness"] = {
        "integrated_lufs_milli": -23.5,
        "true_peak_dbfs_milli": None,
        "measurement_standard": "ebu_r128",
    }
    with pytest.raises(ValidationError):
        AudioAssetMetadata.model_validate(data)


@pytest.mark.parametrize("kind", [AudioKind.DIALOGUE, AudioKind.NARRATION])
def test_speech_audio_requires_language_and_script_hash(kind):
    data = make_audio_metadata(kind).model_dump(mode="python")
    data["language"] = None
    with pytest.raises(ValidationError, match="language.*script_hash"):
        AudioAssetMetadata.model_validate(data)

    data = make_audio_metadata(kind).model_dump(mode="python")
    data["script_hash"] = None
    with pytest.raises(ValidationError, match="language.*script_hash"):
        AudioAssetMetadata.model_validate(data)


def test_generated_speech_requires_voice_id_but_imported_speech_may_omit_it():
    generated = make_audio_metadata().model_dump(mode="python")
    generated["voice_id"] = None
    with pytest.raises(ValidationError, match="generated speech.*voice_id"):
        AudioAssetMetadata.model_validate(generated)

    imported = make_audio_metadata().model_dump(mode="python")
    imported["voice_id"] = None
    imported["source"]["kind"] = "imported"
    assert AudioAssetMetadata.model_validate(imported).voice_id is None


@pytest.mark.parametrize("kind", [AudioKind.AMBIENCE, AudioKind.SFX, AudioKind.BGM])
def test_non_speech_audio_rejects_voice_identity(kind):
    data = make_audio_metadata(kind).model_dump(mode="python")
    data["voice_id"] = "voice-forbidden"
    with pytest.raises(ValidationError, match="voice identity"):
        AudioAssetMetadata.model_validate(data)


def test_registry_21_requires_exact_audio_or_caption_metadata():
    voice = make_asset_record(audio_metadata=make_audio_metadata())
    registry = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=(voice,),
    )
    assert registry.assets[0].audio_metadata == make_audio_metadata()

    with pytest.raises(ValidationError, match="audio metadata"):
        AssetRegistrySnapshot(
            schema_version="2.1",
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            assets=(make_asset_record(),),
        )

    caption = make_asset_record(
        asset_type=AssetType.CAPTION,
        caption_metadata=make_caption_metadata(),
    )
    assert AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=(caption,),
    ).assets == (caption,)

    with pytest.raises(ValidationError, match="non-audio"):
        make_asset_record(
            asset_type=AssetType.IMAGE,
            audio_metadata=make_audio_metadata(),
        )


def test_registry_20_preserves_generic_records_and_rejects_p4_fields():
    legacy = make_asset_record()
    registry = AssetRegistrySnapshot(
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=(legacy,),
    )
    dumped = registry.model_dump(mode="json")
    assert dumped["schema_version"] == "2.0"
    assert "audio_metadata" not in dumped["assets"][0]
    assert "caption_metadata" not in dumped["assets"][0]

    with pytest.raises(ValidationError, match="2.0"):
        AssetRegistrySnapshot(
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            assets=(make_asset_record(audio_metadata=make_audio_metadata()),),
        )


def test_registry_22_requires_measured_metadata_for_generated_video():
    assert hasattr(production_models, "VideoAssetMetadata")
    metadata = production_models.VideoAssetMetadata(
        container_name="mp4",
        codec_name="h264",
        width=1280,
        height=720,
        fps_numerator=24,
        fps_denominator=1,
        duration_milliseconds=3000,
        frame_count=72,
        probe_receipt_id="probe-1",
        request_receipt_fingerprint=ONE_HASH,
        resolved_generation_hash=TWO_HASH,
        provenance_receipt_id="provenance-1",
    )
    record = AssetRecord(
        asset_id="video-1",
        asset_type=AssetType.VIDEO,
        artifact_path=Path(f"assets/video/{FIVE_HASH}.mp4"),
        sha256=FIVE_HASH,
        size_bytes=64,
        mime_type="video/mp4",
        duration_seconds=3.0,
        width=1280,
        height=720,
        source_kind=AssetSourceKind.GENERATED,
        tool=ToolIdentity(name="fixture", version="1"),
        input_fingerprint=SIX_HASH,
        creation_receipt_id="creation-video-1",
        usage_license="fixture-only",
        video_metadata=metadata,
    )
    registry = AssetRegistrySnapshot(
        schema_version="2.2",
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=(record,),
    )
    assert registry.assets[0].video_metadata == metadata

    with pytest.raises(ValidationError, match="generated video"):
        AssetRegistrySnapshot(
            schema_version="2.2",
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            assets=(record.model_copy(update={"video_metadata": None}),),
        )


def test_registry_22_remote_generated_video_requires_cost_and_exact_egress_identity():
    metadata = production_models.VideoAssetMetadata(
        container_name="mp4",
        codec_name="h264",
        width=1280,
        height=720,
        fps_numerator=24,
        fps_denominator=1,
        duration_milliseconds=3000,
        frame_count=72,
        probe_receipt_id="probe-1",
        request_receipt_fingerprint=ONE_HASH,
        resolved_generation_hash=TWO_HASH,
        provenance_receipt_id="provenance-1",
    )
    record = AssetRecord(
        asset_id="video-remote-1",
        asset_type=AssetType.VIDEO,
        artifact_path=Path(f"assets/files/{FIVE_HASH}.mp4"),
        sha256=FIVE_HASH,
        size_bytes=64,
        mime_type="video/mp4",
        duration_seconds=3.0,
        width=1280,
        height=720,
        source_kind=AssetSourceKind.GENERATED,
        tool=ToolIdentity(name="fixture", version="1"),
        input_fingerprint=SIX_HASH,
        creation_receipt_id="creation-video-remote-1",
        usage_license="fixture-only",
        egress=production_models.EgressMetadata(
            remote=True,
            destination="https://api.minimax.io",
            authorization_receipt_id="authorization-1",
            request_fingerprint=TWO_HASH,
            payload_fingerprint=THREE_HASH,
            retention_mode="provider_standard",
            provider_policy_snapshot_id="policy-1",
        ),
        video_metadata=metadata,
    )
    with pytest.raises(ValidationError, match="cost receipt"):
        AssetRegistrySnapshot(
            schema_version="2.2",
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            assets=(record,),
        )
    with pytest.raises(ValidationError, match="request identity"):
        AssetRegistrySnapshot(
            schema_version="2.2",
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            assets=(
                record.model_copy(
                    update={
                        "cost_receipt_id": "cost-1",
                        "egress": record.egress.model_copy(
                            update={"request_fingerprint": FOUR_HASH}
                        ),
                    }
                ),
            ),
        )


@pytest.mark.parametrize("schema_version", ["2.0", "2.1"])
def test_pre_22_registry_rejects_explicit_video_metadata(schema_version):
    assert hasattr(production_models, "VideoAssetMetadata")
    payload = AssetRegistrySnapshot(
        schema_version=schema_version,
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=(make_asset_record(asset_type=AssetType.IMAGE),),
    ).model_dump(mode="python")
    payload["assets"][0]["video_metadata"] = {
        "container_name": "mp4",
        "codec_name": "h264",
        "width": 1280,
        "height": 720,
        "fps_numerator": 24,
        "fps_denominator": 1,
        "duration_milliseconds": 3000,
        "frame_count": 72,
        "probe_receipt_id": "probe-1",
        "request_receipt_fingerprint": ONE_HASH,
        "resolved_generation_hash": TWO_HASH,
        "provenance_receipt_id": "provenance-1",
    }
    with pytest.raises(ValidationError, match="2.2|video metadata"):
        AssetRegistrySnapshot.model_validate(payload)


def _make_video_generation_attempt_state():
    required = (
        "VideoRequestReceiptPointer",
        "VideoStatusReceiptPointer",
        "VideoGenerationAttemptState",
    )
    assert all(hasattr(production_models, name) for name in required)
    submit = production_models.PaidProviderSubmitReceiptPointer(
        path=Path(f"state/paid-provider/submits/{FOUR_HASH}.json"),
        submit_receipt_fingerprint=FOUR_HASH,
        file_sha256=FIVE_HASH,
    )
    request = production_models.VideoRequestReceiptPointer(
        path=Path(f"state/video-generation/requests/{ONE_HASH}.json"),
        request_receipt_fingerprint=ONE_HASH,
        generation_id="generation-1",
        request_input_hash=SIX_HASH,
        resolved_generation_hash=TWO_HASH,
        output_asset_id="video-1",
        file_sha256=SEVEN_HASH,
    )
    observation = production_models.VideoStatusReceiptPointer(
        path=Path(f"state/video-generation/status/{THREE_HASH}.json"),
        observation_fingerprint=THREE_HASH,
        request_receipt_fingerprint=ONE_HASH,
        paid_submit_receipt_fingerprint=FOUR_HASH,
        file_sha256=EIGHT_HASH,
    )
    return production_models.VideoGenerationAttemptState(
        request=request,
        generation_id="generation-1",
        resolved_generation_hash=TWO_HASH,
        phase="polling",
        paid_submit_receipt=submit,
        latest_observation=observation,
    )


def test_manifest_27_accepts_gate_bound_video_attempt_without_external_task_id():
    video_state = _make_video_generation_attempt_state()
    submit = video_state.paid_submit_receipt
    assert submit is not None
    attempt = StateCommitAttempt(
        attempt_id="video-attempt-1",
        operation="video_generation",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        base_dependency_graph=make_dependency_graph_snapshot_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        video_generation_state=video_state,
        paid_provider_state=production_models.PaidProviderAttemptState(
            gate_receipt=production_models.PaidProviderGateReceiptPointer(
                path=Path(f"state/paid-provider/gates/{NINE_HASH}.json"),
                gate_receipt_fingerprint=NINE_HASH,
                file_sha256=ZERO_HASH,
            ),
            reservation_id="reservation-video-1",
            phase="accepted",
            submit_receipt=submit,
        ),
        started_at="2026-08-18T00:00:00Z",
    )
    manifest = make_state_manifest(
        schema_version="2.7",
        active_dependency_graph=make_dependency_graph_snapshot_pointer(),
        active_paid_provider_budget=production_models.PaidProviderBudgetSnapshotPointer(
            path=Path(f"state/paid-provider/budgets/{ZERO_HASH}.json"),
            revision=1,
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        ),
        attempts=(attempt,),
    )
    dumped = manifest.model_dump(mode="json")
    assert dumped["attempts"][0]["video_generation_state"]["generation_id"] == "generation-1"
    assert "active_dependency_graph" in dumped
    assert "active_paid_provider_budget" in dumped
    assert "external_task_id" not in str(dumped)


def test_manifest_27_allows_durable_video_request_before_paid_gate():
    video_state = _make_video_generation_attempt_state().model_copy(
        update={
            "phase": production_models.VideoAttemptPhase.REQUEST,
            "paid_submit_receipt": None,
            "latest_observation": None,
        }
    )
    attempt = StateCommitAttempt(
        attempt_id="video-request-attempt-1",
        operation="video_generation",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        base_dependency_graph=make_dependency_graph_snapshot_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        video_generation_state=video_state,
        started_at="2026-08-18T00:00:00Z",
    )
    manifest = make_state_manifest(
        schema_version="2.7",
        active_dependency_graph=make_dependency_graph_snapshot_pointer(),
        attempts=(attempt,),
    )
    assert manifest.attempts[0].paid_provider_state is None


@pytest.mark.parametrize(
    ("paid_phase", "outer_status"),
    [
        ("known_no_effect", StateCommitStatus.FAILED),
        ("outcome_unknown", StateCommitStatus.OUTCOME_UNKNOWN),
    ],
)
def test_manifest_27_preserves_terminal_paid_submit_outcome_without_video_task(
    paid_phase,
    outer_status,
):
    base_state = _make_video_generation_attempt_state()
    video_state = base_state.model_copy(
        update={
            "phase": production_models.VideoAttemptPhase.SUBMIT_INTENT,
            "paid_submit_receipt": None,
            "latest_observation": None,
        }
    )
    paid_state = production_models.PaidProviderAttemptState(
        gate_receipt=production_models.PaidProviderGateReceiptPointer(
            path=Path(f"state/paid-provider/gates/{NINE_HASH}.json"),
            gate_receipt_fingerprint=NINE_HASH,
            file_sha256=ZERO_HASH,
        ),
        reservation_id="reservation-video-terminal-1",
        phase=paid_phase,
        submit_receipt=base_state.paid_submit_receipt,
    )
    attempt = StateCommitAttempt(
        attempt_id="video-terminal-attempt-1",
        operation="video_generation",
        status=outer_status,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        base_dependency_graph=make_dependency_graph_snapshot_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        video_generation_state=video_state,
        paid_provider_state=paid_state,
        started_at="2026-08-18T00:00:00Z",
        finished_at="2026-08-18T00:00:01Z",
        error_code="paid_provider_submit_outcome",
        error_message="paid Provider submit reached a terminal outcome",
    )
    assert attempt.status is outer_status


@pytest.mark.parametrize(
    ("paid_phase", "wrong_status"),
    [
        ("known_no_effect", StateCommitStatus.OUTCOME_UNKNOWN),
        ("outcome_unknown", StateCommitStatus.FAILED),
    ],
)
def test_manifest_27_rejects_terminal_paid_submit_outcome_with_wrong_outer_status(
    paid_phase,
    wrong_status,
):
    base_state = _make_video_generation_attempt_state()
    video_state = base_state.model_copy(
        update={
            "phase": production_models.VideoAttemptPhase.SUBMIT_INTENT,
            "paid_submit_receipt": None,
            "latest_observation": None,
        }
    )
    paid_state = production_models.PaidProviderAttemptState(
        gate_receipt=production_models.PaidProviderGateReceiptPointer(
            path=Path(f"state/paid-provider/gates/{NINE_HASH}.json"),
            gate_receipt_fingerprint=NINE_HASH,
            file_sha256=ZERO_HASH,
        ),
        reservation_id="reservation-video-terminal-1",
        phase=paid_phase,
        submit_receipt=base_state.paid_submit_receipt,
    )
    with pytest.raises(ValidationError, match="status|phase"):
        StateCommitAttempt(
            attempt_id="video-terminal-attempt-1",
            operation="video_generation",
            status=wrong_status,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            base_dependency_graph=make_dependency_graph_snapshot_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            video_generation_state=video_state,
            paid_provider_state=paid_state,
            started_at="2026-08-18T00:00:00Z",
            finished_at="2026-08-18T00:00:01Z",
            error_code="paid_provider_submit_outcome",
            error_message="paid Provider submit reached a terminal outcome",
        )


@pytest.mark.parametrize(
    ("video_phase", "paid_phase", "include_submit"),
    [
        ("submit_intent", "accepted", True),
        ("submitted", "submit_intent", False),
        ("polling", "known_no_effect", True),
        ("fetch", "outcome_unknown", True),
    ],
)
def test_manifest_27_rejects_video_phase_mismatched_to_paid_gate_phase(
    video_phase,
    paid_phase,
    include_submit,
):
    video_state = _make_video_generation_attempt_state().model_copy(
        update={
            "phase": production_models.VideoAttemptPhase(video_phase),
            "paid_submit_receipt": (
                _make_video_generation_attempt_state().paid_submit_receipt
                if include_submit
                else None
            ),
            "latest_observation": (
                _make_video_generation_attempt_state().latest_observation
                if video_phase in {"polling", "fetch"}
                else None
            ),
        }
    )
    submit = video_state.paid_submit_receipt
    paid_state = production_models.PaidProviderAttemptState(
        gate_receipt=production_models.PaidProviderGateReceiptPointer(
            path=Path(f"state/paid-provider/gates/{NINE_HASH}.json"),
            gate_receipt_fingerprint=NINE_HASH,
            file_sha256=ZERO_HASH,
        ),
        reservation_id="reservation-video-1",
        phase=paid_phase,
        submit_receipt=submit,
    )
    with pytest.raises(ValidationError, match="video.*paid Provider|phase"):
        StateCommitAttempt(
            attempt_id="video-mismatch-attempt-1",
            operation="video_generation",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            base_dependency_graph=make_dependency_graph_snapshot_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            video_generation_state=video_state,
            paid_provider_state=paid_state,
            started_at="2026-08-18T00:00:00Z",
        )


@pytest.mark.parametrize("schema_version", ["2.0", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6"])
def test_pre_27_manifest_rejects_explicit_video_attempt_fields(schema_version):
    payload = make_state_manifest(schema_version="2.0").model_dump(mode="python")
    payload["schema_version"] = schema_version
    payload["attempts"] = ({
        "attempt_id": "video-attempt-1",
        "operation": "video_generation",
        "status": "running",
        "base_manifest_revision": 1,
        "base_project": make_project_pointer().model_dump(mode="python"),
        "base_registry": make_registry_pointer().model_dump(mode="python"),
        "candidate_artifacts_hash": ZERO_HASH,
        "video_generation_state": _make_video_generation_attempt_state().model_dump(mode="python"),
        "started_at": "2026-08-18T00:00:00Z",
    },)
    with pytest.raises(ValidationError, match="2.7|video"):
        ProductionManifest.model_validate(payload)


def test_video_attempt_schema_rejects_duplicate_external_task_identity():
    data = _make_video_generation_attempt_state().model_dump(mode="python")
    data["external_task_id"] = "must-live-only-in-gate-receipt"
    with pytest.raises(ValidationError, match="extra"):
        production_models.VideoGenerationAttemptState.model_validate(data)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("request_fingerprint", None),
        ("payload_fingerprint", None),
        ("retention_mode", None),
        ("provider_policy_snapshot_id", None),
    ],
)
def test_registry_20_rejects_explicit_p4_egress_keys_even_when_null(field, value):
    legacy = AssetRegistrySnapshot(
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=(make_asset_record(),),
    ).model_dump(mode="python")
    legacy["assets"][0]["egress"][field] = value

    with pytest.raises(ValidationError, match="explicit P4 egress"):
        AssetRegistrySnapshot.model_validate(legacy)


def test_egress_metadata_has_strict_local_and_remote_variants():
    local = make_asset_record(audio_metadata=make_audio_metadata())
    assert local.egress.remote is False
    assert local.model_dump(mode="json")["egress"] == {
        "remote": False,
        "destination": None,
        "authorization_receipt_id": None,
    }

    remote = make_asset_record(
        audio_metadata=make_audio_metadata(),
        remote=True,
    )
    assert remote.egress.destination == "https://api.elevenlabs.io"

    data = remote.model_dump(mode="python")
    data["egress"]["destination"] = "https://api.elevenlabs.io/v1/tts"
    with pytest.raises(ValidationError, match="HTTPS origin"):
        AssetRecord.model_validate(data)

    data = local.model_dump(mode="python")
    data["egress"]["destination"] = "https://api.elevenlabs.io"
    with pytest.raises(ValidationError, match="local egress"):
        AssetRecord.model_validate(data)


@pytest.mark.parametrize(
    "destination",
    [
        "https://api.elevenlabs.io:garbage",
        "https://[::1]:bad",
        "https://API.ELEVENLABS.IO",
        "https://api.elevenlabs.io:443",
    ],
)
def test_remote_egress_and_voice_receipt_share_canonical_https_origin_policy(
    destination,
):
    remote = make_asset_record(
        audio_metadata=make_audio_metadata(),
        remote=True,
    ).model_dump(mode="python")
    remote["egress"]["destination"] = destination
    with pytest.raises(ValidationError, match="canonical HTTPS origin"):
        AssetRecord.model_validate(remote)

    voice = {
        "request_id": "request-1",
        "attempt_id": "attempt-1",
        "request_fingerprint": ONE_HASH,
        "script_hash": TWO_HASH,
        "provider_kind": "fake",
        "model_id": "fake-v1",
        "voice_id": "voice-1",
        "language": "en",
        "pricing_snapshot_id": "pricing-1",
        "budget_reservation_receipt_id": "budget-1",
        "egress_authorization_receipt_id": "egress-1",
        "destination": destination,
    }
    with pytest.raises(ValidationError, match="canonical HTTPS origin"):
        VoiceRequestReceipt.model_validate(voice)


def test_caption_track_enforces_monotonic_segments_and_word_containment():
    track = make_caption_track()
    assert track.segments[0].words is not None

    data = track.model_dump(mode="python")
    data["segments"] = (
        data["segments"][0],
        {
            **data["segments"][0],
            "segment_id": "segment-2",
            "start_sample": 47_999,
            "end_sample": 60_000,
            "words": None,
        },
    )
    with pytest.raises(ValidationError, match="monotonic"):
        CaptionTrack.model_validate(data)

    data = track.model_dump(mode="python")
    data["segments"][0]["words"][0]["end_sample"] = 48_001
    with pytest.raises(ValidationError, match="contained"):
        CaptionTrack.model_validate(data)


@pytest.mark.parametrize(
    "model",
    [
        lambda: CaptionWord(text="Cafe\u0301", start_sample=0, end_sample=1),
        lambda: CaptionSegment(
            segment_id="segment-nfd",
            text="Cafe\u0301",
            start_sample=0,
            end_sample=1,
        ),
    ],
)
def test_caption_text_identity_requires_nfc(model):
    with pytest.raises(ValidationError, match="NFC"):
        model()


def test_caption_style_identity_is_all_or_none_and_path_is_canonical():
    metadata = make_caption_metadata()
    assert metadata.style_reference_id == "style-1"
    data = metadata.model_dump(mode="python")
    data["style_content_hash"] = None
    with pytest.raises(ValidationError, match="style identity"):
        CaptionAssetMetadata.model_validate(data)

    assert metadata.model_dump(mode="json")["style_reference_revision"] == 1
    legacy = metadata.model_copy(update={"style_reference_revision": None})
    assert "style_reference_revision" not in legacy.model_dump(mode="json")

    style = CaptionStyleReference(
        artifact_id="style-1",
        revision=1,
        content_hash=NINE_HASH,
        path=Path(f"assets/styles/{NINE_HASH}.json"),
    )
    binding = CaptionTrackBinding(
        binding_id="caption-binding-1",
        caption_asset_id="caption-asset-1",
        source_audio_track_id="dialogue-track-1",
        shot_id="shot-1",
        style_reference=style,
    )
    assert binding.style_reference == style
    assert make_caption_track(style_reference_id=None).timing_fingerprint == (
        make_caption_track(style_reference_id="style-1").timing_fingerprint
    )

    with pytest.raises(ValidationError, match="canonical"):
        CaptionStyleReference(
            artifact_id="style-1",
            revision=1,
            content_hash=NINE_HASH,
            path=Path("styles/default.json"),
        )


def test_caption_style_binding_contract_requires_three_way_exact_identity():
    track = make_caption_track()
    metadata = make_caption_metadata()
    style = CaptionStyleReference(
        artifact_id="style-1",
        revision=1,
        content_hash=NINE_HASH,
        path=Path(f"assets/styles/{NINE_HASH}.json"),
    )
    binding = CaptionTrackBinding(
        binding_id="caption-binding-1",
        caption_asset_id="caption-asset-1",
        source_audio_track_id="dialogue-track-1",
        shot_id="shot-1",
        style_reference=style,
    )
    contract = CaptionStyleBindingContract(
        caption_track=track,
        caption_metadata=metadata,
        binding=binding,
    )
    assert contract.binding.style_reference == style

    with pytest.raises(ValidationError, match="three-way"):
        CaptionStyleBindingContract(
            caption_track=track.model_copy(update={"style_reference_id": "style-other"}),
            caption_metadata=metadata,
            binding=binding,
        )

    with pytest.raises(ValidationError, match="three-way"):
        CaptionStyleBindingContract(
            caption_track=track,
            caption_metadata=metadata.model_copy(
                update={"style_content_hash": EIGHT_HASH}
            ),
            binding=binding,
        )

    with pytest.raises(ValidationError, match="three-way"):
        CaptionStyleBindingContract(
            caption_track=make_caption_track(style_reference_id=None),
            caption_metadata=make_caption_metadata(with_style=False),
            binding=binding,
        )


def test_audio_track_and_resolved_ducking_use_integer_sample_policy():
    track = AudioTrackSpec(
        track_id="bgm-track-1",
        audio_kind="bgm",
        asset_id="music-1",
        shot_id=None,
        start_sample=0,
        trim_start_sample=0,
        trim_duration_samples=96_000,
        gain_millidb=-3_000,
        fade_in_samples=4_800,
        fade_out_samples=4_800,
        ducking=None,
    )
    assert track.start_sample == 0
    ducking = ResolvedDuckingSpec(
        sidechain_track_ids=("dialogue-track-1",),
        attenuation_millidb=-9_000,
        attack_samples=480,
        release_samples=4_800,
    )
    assert ducking.attack_samples == 480

    data = track.model_dump(mode="python")
    data["fade_in_samples"] = 1.5
    with pytest.raises(ValidationError):
        AudioTrackSpec.model_validate(data)


def test_composition_and_timeline_versions_reject_p4_fields_in_20_and_omit_defaults():
    layer = CompositionLayerSpec(
        layer_id="layer-1",
        shot_id="shot-1",
        asset_role="primary_image",
        asset_id="asset-1",
    )
    spec = CompositionSpec(
        **versioned_fields("composition-1", THREE_HASH),
        composition_id="composition-1",
        shot_ids=("shot-1",),
        layers=(layer,),
        delivery_profile=DeliveryProfile(width=320, height=180, fps=24),
    )
    assert "audio_tracks" not in spec.model_dump(mode="json")
    assert "caption_tracks" not in spec.model_dump(mode="json")

    data = spec.model_dump(mode="python")
    data["audio_tracks"] = (
        AudioTrackSpec(
            track_id="dialogue-track-1",
            audio_kind="dialogue",
            asset_id="voice-1",
            shot_id="shot-1",
            start_sample=None,
            trim_start_sample=0,
            trim_duration_samples=None,
            gain_millidb=0,
            fade_in_samples=0,
            fade_out_samples=0,
            ducking=None,
        ),
    )
    with pytest.raises(ValidationError, match="2.0"):
        CompositionSpec.model_validate(data)

    timeline = make_resolved_timeline()
    assert canonical_sha256(timeline.model_dump(mode="json")) == (
        "20c7ad8c70f327dd1547b649d697fbaa3312fb93f215c75c237c5958c5c039f8"
    )
    assert "audio_spans" not in timeline.model_dump(mode="json")
    assert "caption_cues" not in timeline.model_dump(mode="json")

    explicit_empty_spec = spec.model_dump(mode="python")
    explicit_empty_spec["audio_tracks"] = ()
    with pytest.raises(ValidationError, match="explicit P4"):
        CompositionSpec.model_validate(explicit_empty_spec)

    explicit_empty_timeline = timeline.model_dump(mode="python")
    explicit_empty_timeline["caption_cues"] = ()
    with pytest.raises(ValidationError, match="explicit P4"):
        ResolvedTimeline.model_validate(explicit_empty_timeline)


def test_composition_21_rejects_bound_caption_without_style_reference():
    layer = CompositionLayerSpec(
        layer_id="layer-1",
        shot_id="shot-1",
        asset_role="primary_image",
        asset_id="asset-1",
    )
    binding = CaptionTrackBinding(
        binding_id="caption-binding-1",
        caption_asset_id="caption-asset-1",
        source_audio_track_id="dialogue-track-1",
        shot_id="shot-1",
        style_reference=None,
    )
    with pytest.raises(ValidationError, match="bound caption.*style"):
        CompositionSpec(
            **versioned_fields("composition-1", THREE_HASH),
            schema_version="2.1",
            composition_id="composition-1",
            shot_ids=("shot-1",),
            layers=(layer,),
            delivery_profile=DeliveryProfile(width=320, height=180, fps=24),
            caption_tracks=(binding,),
        )

    style = CaptionStyleReference(
        artifact_id="style-1",
        revision=1,
        content_hash=NINE_HASH,
        path=Path(f"assets/styles/{NINE_HASH}.json"),
    )
    assert CompositionSpec(
        **versioned_fields("composition-1", THREE_HASH),
        schema_version="2.1",
        composition_id="composition-1",
        shot_ids=("shot-1",),
        layers=(layer,),
        delivery_profile=DeliveryProfile(width=320, height=180, fps=24),
        caption_tracks=(binding.model_copy(update={"style_reference": style}),),
    ).caption_tracks[0].style_reference == style


def test_resolved_timeline_requires_canonical_unique_audio_span_order():
    span_a = ResolvedAudioSpan(
        track_id="a-track",
        audio_kind="dialogue",
        asset_id="voice-a",
        asset_sha256=ONE_HASH,
        start_sample=0,
        duration_samples=48_000,
        source_start_sample=0,
        source_duration_samples=48_000,
        gain_millidb=0,
        fade_in_samples=0,
        fade_out_samples=0,
        ducking=None,
    )
    span_b = span_a.model_copy(
        update={
            "track_id": "b-track",
            "asset_id": "voice-b",
            "asset_sha256": TWO_HASH,
            "start_sample": 48_000,
        }
    )
    base = make_resolved_timeline().model_dump(mode="python")
    base["schema_version"] = "2.1"
    base["audio_spans"] = (span_a, span_b)
    timeline = ResolvedTimeline.model_validate(base)
    assert tuple(item.track_id for item in timeline.audio_spans) == ("a-track", "b-track")

    base["audio_spans"] = (span_b, span_a)
    with pytest.raises(ValidationError, match="canonical"):
        ResolvedTimeline.model_validate(base)

    base["audio_spans"] = (span_a, span_a)
    with pytest.raises(ValidationError, match="unique"):
        ResolvedTimeline.model_validate(base)


def test_resolved_timeline_accepts_overlapping_cues_but_requires_canonical_unique_order():
    cue_a = ResolvedCaptionCue(
        caption_asset_id="caption-a",
        caption_asset_sha256=ONE_HASH,
        caption_track_id="caption-track-a",
        caption_timing_fingerprint=TWO_HASH,
        segment_id="segment-1",
        text="A",
        start_sample=1_000,
        end_sample=20_000,
        start_frame=0,
        end_frame_exclusive=10,
        style_reference_id="style-1",
        style_content_hash=THREE_HASH,
    )
    cue_b = cue_a.model_copy(
        update={
            "caption_asset_id": "caption-b",
            "caption_asset_sha256": FOUR_HASH,
            "caption_track_id": "caption-track-b",
            "caption_timing_fingerprint": FIVE_HASH,
            "text": "B",
        }
    )
    base = make_resolved_timeline().model_dump(mode="python")
    base["schema_version"] = "2.1"
    base["caption_cues"] = (cue_a, cue_b)
    timeline = ResolvedTimeline.model_validate(base)
    assert timeline.caption_cues == (cue_a, cue_b)

    base["caption_cues"] = (cue_b, cue_a)
    with pytest.raises(ValidationError, match="canonical"):
        ResolvedTimeline.model_validate(base)

    base["caption_cues"] = (cue_a, cue_a)
    with pytest.raises(ValidationError, match="unique"):
        ResolvedTimeline.model_validate(base)


def test_render_schema_21_seals_structured_audio_caption_and_measured_evidence():
    audio_binding = RendererAudioBinding(
        asset_id="voice-1",
        asset_sha256=ONE_HASH,
        asset_mime_type="audio/wav",
        materialized_path=Path(f"state/render/sources/{SIX_HASH}/assets/{ONE_HASH}.wav"),
        sample_rate_hz=48_000,
        channels=1,
        duration_samples=96_000,
        resolved_track_ids=("dialogue-track-1",),
    )
    caption_binding = RendererCaptionBinding(
        caption_track_id="caption-track-1",
        caption_asset_sha256=TWO_HASH,
        materialized_path=Path(f"state/render/sources/{SIX_HASH}/assets/{TWO_HASH}.json"),
        style_reference_id="style-1",
        style_content_hash=THREE_HASH,
        style_materialized_path=Path(f"state/render/sources/{SIX_HASH}/assets/{THREE_HASH}.json"),
        resolved_cue_ids=("segment-1",),
    )
    assert audio_binding.duration_samples == 96_000
    assert caption_binding.resolved_cue_ids == ("segment-1",)

    measured_audio = MeasuredAudioRenderMetadata(
        stream_count=1,
        codec_name="aac",
        sample_rate_hz=48_000,
        channels=1,
        channel_layout="mono",
        decoded_samples=96_000,
        encoder_priming_samples=1024,
        encoder_padding_samples=128,
        measurement_method="ffprobe+decoded_pcm_sha256",
    )
    receipt_data = make_render_receipt().model_dump(mode="python")
    receipt_data["schema_version"] = "2.1"
    receipt_data["measured"]["audio"] = measured_audio
    receipt_data["decoded_audio_fingerprint"] = FOUR_HASH
    receipt = RenderReceipt.model_validate(receipt_data)
    assert receipt.measured.audio == measured_audio

    old_dump = make_render_receipt().model_dump(mode="json")
    assert "decoded_audio_fingerprint" not in old_dump
    assert "audio" not in old_dump["measured"]

    bad = receipt.model_dump(mode="python")
    bad["schema_version"] = "2.0"
    with pytest.raises(ValidationError, match="2.0"):
        RenderReceipt.model_validate(bad)

    explicit_old = make_render_receipt().model_dump(mode="python")
    explicit_old["decoded_audio_fingerprint"] = None
    with pytest.raises(ValidationError, match="explicit P4"):
        RenderReceipt.model_validate(explicit_old)


def test_renderer_bindings_require_mime_hash_and_exact_suffix_mapping():
    audio = {
        "asset_id": "voice-1",
        "asset_sha256": ONE_HASH,
        "asset_mime_type": "audio/wav",
        "materialized_path": Path(
            f"state/render/sources/{SIX_HASH}/assets/{ONE_HASH}.json"
        ),
        "sample_rate_hz": 48_000,
        "channels": 1,
        "duration_samples": 96_000,
        "resolved_track_ids": ("dialogue-track-1",),
    }
    with pytest.raises(ValidationError, match="suffix"):
        RendererAudioBinding.model_validate(audio)

    caption = {
        "caption_track_id": "caption-track-1",
        "caption_asset_sha256": TWO_HASH,
        "materialized_path": Path(
            f"state/render/sources/{SIX_HASH}/assets/{TWO_HASH}.wav"
        ),
        "style_reference_id": None,
        "style_content_hash": None,
        "style_materialized_path": None,
        "resolved_cue_ids": ("segment-1",),
    }
    with pytest.raises(ValidationError, match="JSON"):
        RendererCaptionBinding.model_validate(caption)

    audio["materialized_path"] = Path(
        f"state/render/sources/{SIX_HASH}/assets/{ONE_HASH}.wav"
    )
    audio["resolved_track_ids"] = ("dialogue-track-1", "dialogue-track-1")
    with pytest.raises(ValidationError, match="unique"):
        RendererAudioBinding.model_validate(audio)

    caption["materialized_path"] = Path(
        f"state/render/sources/{SIX_HASH}/assets/{TWO_HASH}.json"
    )
    caption["resolved_cue_ids"] = ("segment-1", "segment-1")
    with pytest.raises(ValidationError, match="unique"):
        RendererCaptionBinding.model_validate(caption)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("channels", True),
        ("sample_rate_hz", True),
        ("duration_samples", True),
    ],
)
def test_audio_measured_integer_fields_reject_bool(field, value):
    data = make_audio_metadata().model_dump(mode="python")
    data[field] = value
    with pytest.raises(ValidationError):
        AudioAssetMetadata.model_validate(data)


def test_source_bundle_accepts_only_hash_named_media_suffixes_and_exact_bindings():
    root = Path(f"state/render/sources/{SIX_HASH}")
    bundle = RenderSourceBundlePointer(
        root_path=root,
        bundle_sha256=SIX_HASH,
        index=RenderSourceFilePointer(
            path=root / "index.html", file_sha256=SEVEN_HASH, size_bytes=100
        ),
        assets=(
            RenderSourceFilePointer(
                path=root / "assets" / f"{ONE_HASH}.wav",
                file_sha256=ONE_HASH,
                size_bytes=64,
            ),
            RenderSourceFilePointer(
                path=root / "assets" / f"{TWO_HASH}.json",
                file_sha256=TWO_HASH,
                size_bytes=64,
            ),
            RenderSourceFilePointer(
                path=root / "assets" / f"{THREE_HASH}.mp4",
                file_sha256=THREE_HASH,
                size_bytes=64,
            ),
        ),
    )
    assert len(bundle.assets) == 3

    data = bundle.model_dump(mode="python")
    data["assets"][0]["path"] = root / "assets" / f"{ONE_HASH}.exe"
    with pytest.raises(ValidationError, match="hash"):
        RenderSourceBundlePointer.model_validate(data)

    explicit_old_receipt = make_source_receipt().model_dump(mode="python")
    explicit_old_receipt["audio_bindings"] = ()
    with pytest.raises(ValidationError, match="explicit P4"):
        RendererSourceReceipt.model_validate(explicit_old_receipt)


def test_old_silent_source_and_render_receipt_hashes_are_unchanged():
    assert canonical_sha256(make_source_receipt().model_dump(mode="json")) == (
        "ff00cc8d68a86d6bf4a289de2c1a0496dce6204561f25a9aafe633e0ccc6d788"
    )
    assert canonical_sha256(make_render_receipt().model_dump(mode="json")) == (
        "24ff05848dbe2046e15c7bd6b4474d093a8ff17f2d2a4ee34f100ecd17ca3199"
    )


def test_voice_attempt_fields_are_manifest_22_only_and_serializer_compatible():
    request = VoiceRequestReceipt(
        request_id="request-1",
        attempt_id="attempt-voice-1",
        request_fingerprint=ONE_HASH,
        script_hash=TWO_HASH,
        provider_kind="fake",
        model_id="fake-v1",
        voice_id="voice-1",
        language="en",
        pricing_snapshot_id="pricing-1",
        budget_reservation_receipt_id="budget-1",
        egress_authorization_receipt_id="egress-1",
        destination="https://api.elevenlabs.io",
    )
    attempt = StateCommitAttempt(
        attempt_id="attempt-voice-1",
        operation="voice_generation",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        voice_request=request,
        voice_phase="request",
        provider_request_id="voice-job-1",
        started_at="2026-08-10T00:00:00+00:00",
    )
    manifest = make_state_manifest(schema_version="2.2", attempts=(attempt,))
    assert manifest.attempts[0].voice_request == request
    assert manifest.model_dump(mode="json")["attempts"][0]["provider_request_id"] == (
        "voice-job-1"
    )

    with pytest.raises(ValidationError, match="2.1"):
        make_state_manifest(schema_version="2.1", attempts=(attempt,))

    old_attempt = StateCommitAttempt(
        attempt_id="attempt-custom",
        operation="historical_custom_commit",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-10T00:00:00+00:00",
    )
    assert not {
        "voice_request",
        "voice_phase",
        "provider_request_id",
        "candidate_audio_asset_ids",
        "candidate_caption_asset_ids",
    }.intersection(old_attempt.model_dump(mode="json"))


@pytest.mark.parametrize(
    ("status", "phase"),
    [
        (StateCommitStatus.SUCCEEDED, "request"),
        (StateCommitStatus.OUTCOME_UNKNOWN, "request"),
        (StateCommitStatus.INTERRUPTED, "submit_intent"),
        (StateCommitStatus.INTERRUPTED, "provider_call"),
    ],
)
def test_voice_attempt_terminal_status_requires_plan_consistent_phase(status, phase):
    data = make_state_manifest(schema_version="2.2").model_dump(mode="python")
    request = VoiceRequestReceipt(
        request_id="request-1",
        attempt_id="attempt-voice-1",
        request_fingerprint=ONE_HASH,
        script_hash=TWO_HASH,
        provider_kind="fake",
        model_id="fake-v1",
        voice_id="voice-1",
        language="en",
        pricing_snapshot_id="pricing-1",
        budget_reservation_receipt_id="budget-1",
        egress_authorization_receipt_id="egress-1",
        destination="https://api.elevenlabs.io",
    )
    attempt = {
        "attempt_id": "attempt-voice-1",
        "operation": "voice_generation",
        "status": status,
        "base_manifest_revision": 1,
        "base_project": make_project_pointer(),
        "base_registry": make_registry_pointer(),
        "candidate_artifacts_hash": ZERO_HASH,
        "voice_request": request,
        "voice_phase": phase,
        "started_at": "2026-08-10T00:00:00+00:00",
        "finished_at": "2026-08-10T00:00:01+00:00",
        "error_code": None if status is StateCommitStatus.SUCCEEDED else "typed",
        "error_message": None if status is StateCommitStatus.SUCCEEDED else "safe",
    }
    data["attempts"] = (attempt,)
    with pytest.raises(ValidationError, match="phase"):
        ProductionManifest.model_validate(data)


@pytest.mark.parametrize(
    ("code", "value"),
    [
        (ErrorCode.AUDIO_ASSET_INVALID, "audio_asset_invalid"),
        (ErrorCode.AUDIO_PROBE_FAILED, "audio_probe_failed"),
        (ErrorCode.AUDIO_TIMELINE_INVALID, "audio_timeline_invalid"),
        (ErrorCode.CAPTION_ALIGNMENT_INVALID, "caption_alignment_invalid"),
        (ErrorCode.CAPTION_TRACK_INVALID, "caption_track_invalid"),
        (ErrorCode.VOICE_REQUEST_INVALID, "voice_request_invalid"),
        (ErrorCode.VOICE_BUDGET_REJECTED, "voice_budget_rejected"),
        (ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED, "voice_egress_not_authorized"),
        (ErrorCode.VOICE_PROVIDER_FAILED, "voice_provider_failed"),
        (ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN, "voice_provider_outcome_unknown"),
    ],
)
def test_p4_error_codes_are_typed_and_non_retryable_by_default(code, value):
    assert code.value == value
    assert AiVideoError(code=code, user_message="safe").retryable is False


def test_resolved_timeline_requires_integer_boundaries():
    timeline = make_resolved_timeline()

    assert timeline.visual_spans[0].start_frame == 0
    assert timeline.visual_spans[0].duration_frames == 48
    assert timeline.visual_spans[0].start_sample == 0
    assert timeline.visual_spans[0].duration_samples == 96_000

    data = timeline.model_dump(mode="json")
    data["visual_spans"][0]["start_frame"] = 0.5
    with pytest.raises(ValidationError):
        ResolvedTimeline.model_validate(data)


def test_render_receipt_rejects_unknown_fields():
    data = make_render_receipt().model_dump(mode="json")
    data["renderer_fallback"] = "remotion"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RenderReceipt.model_validate(data)


def test_renderer_source_receipt_fixes_index_and_check_identity():
    receipt = make_source_receipt()

    assert receipt.source_sha256 == receipt.source_bundle.index.file_sha256
    assert tuple(item.command for item in receipt.checks) == ("lint", "check")


def test_renderer_selection_allows_one_selected_renderer():
    with pytest.raises(ValidationError):
        RendererSelectionReceipt(
            receipt_id="select-1",
            attempt_id="attempt-1",
            requested_kind="hyperframes",
            selected_kinds=("hyperframes", "remotion"),
            renderer_version="0.7.103",
            timeline_fingerprint=FOUR_HASH,
            current_project=make_project_pointer(),
            current_registry=make_registry_pointer(),
        )


def test_renderer_selection_rejects_a_selected_renderer_other_than_requested():
    data = make_renderer_selection().model_dump(mode="python")
    data["requested_kind"] = "remotion"

    with pytest.raises(ValidationError, match="requested"):
        RendererSelectionReceipt.model_validate(data)


def test_render_attempt_requires_selection_attempt_id_to_match():
    selection = make_renderer_selection().model_copy(
        update={"attempt_id": "attempt-other"}
    )

    with pytest.raises(ValidationError, match="attempt identity"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="render_state",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            renderer_selection=selection,
            started_at="2026-08-09T00:00:00+00:00",
        )


@pytest.mark.parametrize(
    "candidate_fields",
    [
        {"candidate_render_state": make_render_state_pointer()},
        {"candidate_project": make_canonical_project_pointer()},
        {"candidate_registry": make_registry_pointer()},
        {
            "candidate_render_state": make_render_state_pointer(),
            "candidate_project": make_canonical_project_pointer(),
        },
        {
            "candidate_render_state": make_render_state_pointer(),
            "candidate_registry": make_registry_pointer(),
        },
        {
            "candidate_project": make_canonical_project_pointer(),
            "candidate_registry": make_registry_pointer(),
        },
    ],
)
def test_render_attempt_rejects_partial_candidate_bundle(candidate_fields):
    with pytest.raises(ValidationError, match="candidate bundle"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="render_state",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            base_project=make_canonical_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            renderer_selection=make_renderer_selection().model_copy(
                update={"current_project": make_canonical_project_pointer()}
            ),
            started_at="2026-08-09T00:00:00+00:00",
            **candidate_fields,
        )


def test_render_attempt_candidate_bundle_requires_activate_phase():
    with pytest.raises(ValidationError, match="activate"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="render_state",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            base_project=make_canonical_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_project=make_canonical_project_pointer(),
            candidate_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            candidate_render_state=make_render_state_pointer(),
            renderer_selection=make_renderer_selection().model_copy(
                update={"current_project": make_canonical_project_pointer()}
            ),
            render_phase="render",
            started_at="2026-08-09T00:00:00+00:00",
        )


def test_render_attempt_accepts_complete_activate_candidate_bundle():
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="render_state",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_canonical_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_project=make_canonical_project_pointer(),
        candidate_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        candidate_render_state=make_render_state_pointer(),
        renderer_selection=make_renderer_selection().model_copy(
            update={"current_project": make_canonical_project_pointer()}
        ),
        render_phase="activate",
        started_at="2026-08-09T00:00:00+00:00",
    )

    assert attempt.candidate_render_state == make_render_state_pointer()


def test_render_attempt_accepts_active_project_entrypoint_as_unchanged_candidate():
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="render_state",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_project=make_project_pointer(),
        candidate_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        candidate_render_state=make_render_state_pointer(),
        renderer_selection=make_renderer_selection(),
        render_phase="activate",
        started_at="2026-08-09T00:00:00+00:00",
    )

    assert attempt.candidate_project.path == Path("project.yaml")


def test_non_render_attempt_still_rejects_project_entrypoint_candidate():
    with pytest.raises(ValidationError, match="canonical project snapshot path"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="commit_project_registry",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_project=make_project_pointer(),
            candidate_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            started_at="2026-08-09T00:00:00+00:00",
        )


@pytest.mark.parametrize("mismatch", ["project", "registry", "render_state"])
def test_manifest_running_render_attempt_requires_current_base_identity(mismatch):
    active_render = make_render_state_pointer()
    base_project = make_project_pointer()
    base_registry = make_registry_pointer()
    base_render = active_render
    if mismatch == "project":
        base_project = make_canonical_project_pointer(
            content_hash=TWO_HASH, file_sha256=THREE_HASH
        )
    elif mismatch == "registry":
        base_registry = make_alternate_registry_pointer()
    else:
        base_render = make_render_state_pointer(FOUR_HASH)
    selection = make_renderer_selection().model_copy(
        update={
            "current_project": base_project,
            "current_registry": base_registry,
        }
    )
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="render_state",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=base_project,
        base_registry=base_registry,
        base_render_state=base_render,
        candidate_artifacts_hash=ZERO_HASH,
        renderer_selection=selection,
        render_phase="selection",
        started_at="2026-08-09T00:00:00+00:00",
    )

    with pytest.raises(ValidationError, match="active identity"):
        make_state_manifest(
            schema_version="2.1",
            active_render_state=active_render,
            attempts=(attempt,),
        )


def test_manifest_allows_historical_terminal_render_attempt_from_an_old_base():
    old_project = make_canonical_project_pointer(
        content_hash=TWO_HASH, file_sha256=THREE_HASH
    )
    old_registry = make_alternate_registry_pointer()
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="render_state",
        status=StateCommitStatus.FAILED,
        base_manifest_revision=1,
        base_project=old_project,
        base_registry=old_registry,
        base_render_state=make_render_state_pointer(FOUR_HASH),
        candidate_artifacts_hash=ZERO_HASH,
        renderer_selection=make_renderer_selection().model_copy(
            update={
                "current_project": old_project,
                "current_registry": old_registry,
            }
        ),
        render_phase="selection",
        started_at="2026-08-09T00:00:00+00:00",
        finished_at="2026-08-09T00:00:01+00:00",
        error_code="renderer_unavailable",
        error_message="safe",
    )

    manifest = make_state_manifest(
        schema_version="2.1",
        active_render_state=make_render_state_pointer(),
        attempts=(attempt,),
    )

    assert manifest.attempts == (attempt,)


def test_manifest_20_rejects_render_state_and_render_attempts():
    render_pointer = RenderStateSnapshotPointer(
        path=Path(f"state/render/states/{THREE_HASH}.json"),
        revision=1,
        content_hash=THREE_HASH,
        file_sha256=ZERO_HASH,
    )
    with pytest.raises(ValidationError, match="2.0"):
        make_state_manifest(active_render_state=render_pointer)

    render_attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="render_state",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-09T00:00:00+00:00",
        renderer_selection=make_renderer_selection(),
    )
    with pytest.raises(ValidationError, match="2.0"):
        make_state_manifest(attempts=(render_attempt,))


def test_manifest_20_preserves_historical_custom_nonempty_operation_without_rewrite():
    attempt = StateCommitAttempt(
        attempt_id="attempt-custom",
        operation="historical_custom_commit",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-09T00:00:00+00:00",
    )

    manifest = make_state_manifest(attempts=(attempt,))

    assert manifest.schema_version == "2.0"
    assert manifest.attempts[0].operation == "historical_custom_commit"
    assert manifest.model_dump(mode="json")["attempts"][0]["operation"] == (
        "historical_custom_commit"
    )
    assert "active_render_state" not in manifest.model_dump(mode="json")
    assert not {
        "base_render_state",
        "candidate_render_state",
        "renderer_selection",
        "render_phase",
    }.intersection(manifest.model_dump(mode="json")["attempts"][0])


def test_manifest_21_accepts_none_or_one_render_state_pointer():
    empty = make_state_manifest(schema_version="2.1", active_render_state=None)
    pointer = RenderStateSnapshotPointer(
        path=Path(f"state/render/states/{THREE_HASH}.json"),
        revision=1,
        content_hash=THREE_HASH,
        file_sha256=ZERO_HASH,
    )
    active = make_state_manifest(schema_version="2.1", active_render_state=pointer)

    assert empty.active_render_state is None
    assert active.active_render_state == pointer


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("attempt_id", "attempt-other"),
        (
            "renderer",
            RendererIdentity(kind="hyperframes", version="0.7.102"),
        ),
        ("timeline_fingerprint", ZERO_HASH),
        ("source_sha256", ZERO_HASH),
        ("source_bundle_sha256", ZERO_HASH),
        ("asset_hashes", (ZERO_HASH,)),
        (
            "output",
            {
                "path": Path(f"state/render/outputs/{ONE_HASH}.mp4"),
                "file_sha256": ZERO_HASH,
                "size_bytes": 200,
            },
        ),
    ],
)
def test_render_state_snapshot_rejects_mixed_attempt_renderer_timeline_source_asset_or_output_identity(
    field, replacement
):
    data = make_render_state_snapshot().model_dump(mode="python")
    data[field] = replacement

    with pytest.raises(ValidationError, match="identity|canonical"):
        RenderStateSnapshot.model_validate(data)


@pytest.mark.parametrize("field", ["asset_role", "asset_id"])
def test_composition_layer_requires_exact_declared_asset_role_and_id(field):
    data = {
        "layer_id": "layer-1",
        "shot_id": "shot-1",
        "asset_role": "primary_image",
        "asset_id": "asset-1",
    }
    data[field] = ""

    with pytest.raises(ValidationError):
        CompositionLayerSpec.model_validate(data)

    layer = CompositionLayerSpec.model_validate(
        {
            "layer_id": "layer-1",
            "shot_id": "shot-1",
            "asset_role": "primary_image",
            "asset_id": "asset-1",
        }
    )
    spec = CompositionSpec(
        **versioned_fields("composition-1", THREE_HASH),
        composition_id="composition-1",
        shot_ids=("shot-1",),
        layers=(layer,),
        delivery_profile=DeliveryProfile(width=320, height=180, fps=24),
    )
    assert (spec.layers[0].asset_role, spec.layers[0].asset_id) == (
        "primary_image",
        "asset-1",
    )


@pytest.mark.parametrize(
    "path",
    [
        Path("state/render/outputs/render.mp4"),
        Path(f"state/render/outputs/{ZERO_HASH}.mov"),
        Path(f"state/render/outputs/{ZERO_HASH[:32]}.mp4"),
        Path(f"state/render/outputs/{TWO_HASH}.mp4"),
    ],
)
def test_render_receipt_requires_canonical_durable_output_path(path):
    data = make_render_receipt().model_dump(mode="python")
    data["output_path"] = path

    with pytest.raises(ValidationError, match="canonical"):
        RenderReceipt.model_validate(data)


@pytest.mark.parametrize("field", ["project", "registry"])
def test_render_state_snapshot_fixes_project_registry_and_source_bundle_provenance(
    field,
):
    data = make_render_state_snapshot().model_dump(mode="python")
    if field == "project":
        data[field] = make_project_pointer().model_copy(
            update={"file_sha256": TWO_HASH}
        )
    else:
        data[field] = make_registry_pointer().model_copy(
            update={"file_sha256": TWO_HASH}
        )

    with pytest.raises(ValidationError, match="identity"):
        RenderStateSnapshot.model_validate(data)


def test_render_models_are_frozen_and_forbid_extra_fields():
    state = make_render_state_snapshot()
    with pytest.raises(ValidationError, match="Instance is frozen"):
        state.attempt_id = "attempt-other"  # type: ignore[misc]
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RenderStateSnapshot.model_validate(
            {**state.model_dump(mode="python"), "unexpected": True}
        )


def test_package_exports_only_the_stable_p3_schema_surface():
    stable_p3_exports = {
        "CompositionSpec",
        "ResolvedTimeline",
        "resolve_composition",
        "RendererSelectionReceipt",
        "RendererSourceReceipt",
        "RenderReceipt",
        "RenderArtifactPointer",
        "RenderSourceFilePointer",
        "RenderSourceBundlePointer",
        "RenderOutputPointer",
        "RenderStateSnapshot",
        "RenderStateSnapshotPointer",
    }

    assert stable_p3_exports <= set(production.__all__)
    assert callable(production.resolve_composition)
    assert {
        "HyperFramesAdapter",
        "RendererRunner",
        "VerifiedRenderFile",
    }.isdisjoint(production.__all__)


def test_production_manifest_has_one_project_and_registry_pointer_owner():
    manifest = make_state_manifest()

    assert manifest.active_project.path == Path("project.yaml")
    assert manifest.active_registry.revision_id == ZERO_HASH
    assert not hasattr(manifest, "active_project_revision")
    assert not hasattr(manifest, "active_project_content_hash")
    assert not hasattr(manifest, "active_registry_revision")


@pytest.mark.parametrize(
    ("code", "name", "value"),
    [
        (ErrorCode.PRODUCTION_STATE_INVALID, "PRODUCTION_STATE_INVALID", "production_state_invalid"),
        (ErrorCode.PRODUCTION_STATE_BUSY, "PRODUCTION_STATE_BUSY", "production_state_busy"),
        (
            ErrorCode.PRODUCTION_STATE_COMMIT_FAILED,
            "PRODUCTION_STATE_COMMIT_FAILED",
            "production_state_commit_failed",
        ),
        (
            ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED,
            "PRODUCTION_STATE_RECOVERY_FAILED",
            "production_state_recovery_failed",
        ),
        (
            ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
            "PRODUCTION_STATE_OUTCOME_UNKNOWN",
            "production_state_outcome_unknown",
        ),
        (
            ErrorCode.PRODUCTION_STATE_UNSUPPORTED,
            "PRODUCTION_STATE_UNSUPPORTED",
            "production_state_unsupported",
        ),
    ],
)
def test_production_state_error_codes_are_non_retryable_by_default(code, name, value):
    assert code.name == name
    assert code.value == value
    assert AiVideoError(code=code, user_message="safe").retryable is False


@pytest.mark.parametrize(
    ("code", "value"),
    [
        (ErrorCode.COMPOSITION_INVALID, "composition_invalid"),
        (ErrorCode.RENDERER_UNAVAILABLE, "renderer_unavailable"),
        (ErrorCode.RENDERER_SOURCE_INVALID, "renderer_source_invalid"),
        (ErrorCode.RENDER_FAILED, "render_failed"),
    ],
)
def test_p3_error_codes_are_typed_and_non_retryable_by_default(code, value):
    assert code.value == value
    assert AiVideoError(code=code, user_message="safe").retryable is False


@pytest.mark.parametrize(
    ("pointer_type", "data"),
    [
        (
            ProjectSnapshotPointer,
            {
                "revision": 1,
                "content_hash": ZERO_HASH,
                "file_sha256": ONE_HASH,
            },
        ),
        (
            RegistrySnapshotPointer,
            {
                "revision_id": ZERO_HASH,
                "content_hash": ZERO_HASH,
                "file_sha256": ONE_HASH,
            },
        ),
    ],
)
@pytest.mark.parametrize(
    "path",
    [
        Path("/tmp/snapshot.yaml"),
        Path("state/../snapshot.yaml"),
        Path(""),
        Path("."),
    ],
)
def test_snapshot_pointers_reject_absolute_or_parent_relative_paths(pointer_type, data, path):
    with pytest.raises(ValidationError, match="clean and project-relative"):
        pointer_type(path=path, **data)


def test_registry_snapshot_pointer_requires_revision_to_match_content_hash():
    with pytest.raises(ValidationError, match="revision_id"):
        RegistrySnapshotPointer(
            path=Path("assets/registry.json"),
            revision_id=ZERO_HASH,
            content_hash=ONE_HASH,
            file_sha256=ONE_HASH,
        )


@pytest.mark.parametrize(
    "path",
    [
        Path("state/projects/arbitrary.yaml"),
        Path(f"state/projects/project.2.{ONE_HASH}.yaml"),
    ],
)
def test_project_snapshot_pointer_requires_entrypoint_or_identity_path(path):
    with pytest.raises(ValidationError, match="canonical project snapshot path"):
        ProjectSnapshotPointer(
            path=path,
            revision=2,
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        )


@pytest.mark.parametrize(
    "path",
    [
        Path("assets/registry.json"),
        Path(f"assets/registry.{ONE_HASH}.json"),
    ],
)
def test_registry_snapshot_pointer_requires_identity_path(path):
    with pytest.raises(ValidationError, match="canonical registry snapshot path"):
        RegistrySnapshotPointer(
            path=path,
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        )


def test_p2a_models_are_frozen_and_forbid_extra_fields():
    pointer = make_project_pointer()
    with pytest.raises(ValidationError, match="Instance is frozen"):
        pointer.revision = 2
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ProjectSnapshotPointer.model_validate(
            {**pointer.model_dump(), "unexpected": True}
        )


def test_state_attempt_rejects_unknown_fallback_pointer():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        StateCommitAttempt.model_validate(
            {
                "attempt_id": "attempt-1",
                "operation": "commit_project_registry",
                "status": "running",
                "base_manifest_revision": 1,
                "base_project": make_project_pointer().model_dump(mode="python"),
                "base_registry": make_registry_pointer().model_dump(mode="python"),
                "candidate_artifacts_hash": ZERO_HASH,
                "started_at": "2026-08-09T00:00:00+00:00",
                "fallback_manifest": "state/manifest.backup.json",
            }
        )


def test_state_attempt_requires_base_snapshot_pair():
    with pytest.raises(ValidationError, match="base_project"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="commit_project_registry",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            candidate_artifacts_hash=ZERO_HASH,
            started_at="2026-08-09T00:00:00+00:00",
        )
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="commit_project_registry",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-09T00:00:00+00:00",
    )
    with pytest.raises(ValidationError, match="Instance is frozen"):
        attempt.base_project = make_project_pointer()  # type: ignore[misc]


def test_state_attempt_base_snapshot_pointers_must_be_clean():
    with pytest.raises(ValidationError, match="clean and project-relative"):
        StateCommitAttempt.model_validate(
            {
                "attempt_id": "attempt-1",
                "operation": "commit_project_registry",
                "status": "running",
                "base_manifest_revision": 1,
                "base_project": {
                    **make_project_pointer().model_dump(mode="json"),
                    "path": "state/../project.yaml",
                },
                "base_registry": make_registry_pointer().model_dump(mode="json"),
                "candidate_artifacts_hash": ZERO_HASH,
                "started_at": "2026-08-09T00:00:00+00:00",
            }
        )


@pytest.mark.parametrize(
    "status",
    [
        StateCommitStatus.FAILED,
        StateCommitStatus.INTERRUPTED,
        StateCommitStatus.OUTCOME_UNKNOWN,
    ],
)
def test_terminal_state_attempts_require_sanitized_typed_error_fields(status):
    with pytest.raises(ValidationError, match="typed error fields"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="commit_project_registry",
            status=status,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            started_at="2026-08-09T00:00:00+00:00",
            finished_at="2026-08-09T00:00:01+00:00",
        )


def test_succeeded_state_attempt_requires_finished_at():
    with pytest.raises(ValidationError, match="require finished_at"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="commit_project_registry",
            status=StateCommitStatus.SUCCEEDED,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            started_at="2026-08-09T00:00:00+00:00",
        )


def test_production_manifest_rejects_duplicate_attempt_ids():
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="commit_project_registry",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-09T00:00:00+00:00",
    )
    with pytest.raises(ValidationError, match="attempt IDs must be unique"):
        make_state_manifest(attempts=(attempt, attempt))


def test_recovery_models_are_strict_and_immutable():
    item = RecoveryItem(
        path=Path("state/.p2a-attempt-1-project.tmp"),
        disposition=RecoveryDisposition.PARTIAL_REMOVED,
        sha256=ZERO_HASH,
    )
    report = RecoveryReport(
        manifest_revision_before=1,
        manifest_revision_after=2,
        items=(item,),
    )
    assert report.items == (item,)
    with pytest.raises(ValidationError, match="Instance is frozen"):
        report.manifest_revision_after = 3


@pytest.mark.parametrize(
    "path",
    [
        Path("/tmp/recovery.tmp"),
        Path("state/../recovery.tmp"),
        Path(""),
        Path("."),
    ],
)
def test_recovery_item_rejects_non_file_or_non_relative_paths(path):
    with pytest.raises(ValidationError, match="clean and project-relative"):
        RecoveryItem(path=path, disposition=RecoveryDisposition.PARTIAL_REMOVED)


@pytest.mark.parametrize("sha256", ["A" * 64, "0" * 63, "g" * 64])
def test_recovery_item_sha256_must_be_lowercase_hex(sha256):
    with pytest.raises(ValidationError):
        RecoveryItem(
            path=Path("state/.p2a-attempt-1-project.tmp"),
            disposition=RecoveryDisposition.PARTIAL_REMOVED,
            sha256=sha256,
        )


@pytest.mark.parametrize("before, after", [(0, 1), (1, 0), (2, 1)])
def test_recovery_report_requires_ordered_positive_manifest_revisions(before, after):
    with pytest.raises(ValidationError):
        RecoveryReport(
            manifest_revision_before=before,
            manifest_revision_after=after,
            items=(),
        )


def test_recovery_report_allows_an_unchanged_manifest_revision():
    report = RecoveryReport(
        manifest_revision_before=1,
        manifest_revision_after=1,
        items=(),
    )
    assert report.manifest_revision_after == report.manifest_revision_before


@pytest.mark.parametrize(
    "contradictory_fields",
    [
        {"finished_at": "2026-08-09T00:00:01+00:00"},
        {"error_code": "production_state_commit_failed"},
        {"error_message": "safe"},
    ],
)
def test_running_state_attempt_rejects_terminal_fields(contradictory_fields):
    with pytest.raises(ValidationError):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="commit_project_registry",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            started_at="2026-08-09T00:00:00+00:00",
            **contradictory_fields,
        )


def test_succeeded_state_attempt_rejects_error_fields():
    with pytest.raises(ValidationError):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="commit_project_registry",
            status=StateCommitStatus.SUCCEEDED,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            started_at="2026-08-09T00:00:00+00:00",
            finished_at="2026-08-09T00:00:01+00:00",
            error_code="production_state_commit_failed",
            error_message="safe",
        )


def test_state_attempt_requires_immutable_canonical_artifact_set_hash():
    artifact_hash = "a" * 64
    attempt = StateCommitAttempt(
        attempt_id="attempt-artifacts",
        operation="commit_project_registry",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=artifact_hash,
        started_at="2026-08-09T00:00:00+00:00",
    )

    assert attempt.candidate_artifacts_hash == artifact_hash
    with pytest.raises(ValidationError, match="Instance is frozen"):
        attempt.candidate_artifacts_hash = "b" * 64  # type: ignore[misc]
    with pytest.raises(ValidationError):
        StateCommitAttempt(
            attempt_id="invalid-artifacts",
            operation="commit_project_registry",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash="INVALID",
            started_at="2026-08-09T00:00:00+00:00",
        )


def make_story() -> Story:
    return Story(
        artifact_id="story-main",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="receipt-story-1",
        source_provenance=[SourceReference(kind="user_input", reference="brief-1")],
        language="zh-CN",
        logline="一位侦探追查失踪的记忆。",
        synopsis="侦探在三幕故事中找到真相。",
        beats=[StoryBeat(beat_id="beat-1", summary="案件出现")],
        source_references=["source-novel-1"],
    )


def test_semantic_hash_ignores_mapping_order_and_content_hash():
    assert canonical_sha256({"b": 2, "a": 1, "content_hash": "x"}) == canonical_sha256(
        {"content_hash": "y", "a": 1, "b": 2}
    )


def test_sealed_artifact_detects_content_change():
    sealed = seal_artifact(make_story())
    assert verify_artifact_hash(sealed)
    assert not verify_artifact_hash(sealed.model_copy(update={"logline": "不同内容"}))


def test_artifact_hash_covers_receipt_and_provenance_envelope():
    sealed = seal_artifact(make_story())
    assert not verify_artifact_hash(
        sealed.model_copy(update={"creation_receipt_id": "receipt-story-2"})
    )


def test_domain_models_reject_unknown_fields():
    data = make_story().model_dump()
    data["unexpected"] = True
    with pytest.raises(ValidationError):
        Story.model_validate(data)


def test_domain_models_are_frozen():
    story = make_story()
    with pytest.raises(ValidationError, match="Instance is frozen"):
        story.logline = "不允许就地修改"


@pytest.mark.parametrize(
    "directive",
    [
        CompositionDirective(kind="fit", parameters={"mode": "cover"}),
        MotionDirective(kind="pan", parameters={"x": 1}),
    ],
)
def test_parameter_mappings_are_immutable(directive):
    with pytest.raises(TypeError, match="immutable"):
        directive.parameters["changed"] = 1


def test_default_parameter_mapping_is_immutable():
    directive = CompositionDirective(kind="fit")
    with pytest.raises(TypeError, match="immutable"):
        directive.parameters["mode"] = "cover"


def test_motion_parameters_reject_boolean_as_numeric_value():
    with pytest.raises(ValidationError, match="boolean"):
        MotionDirective(kind="pan", parameters={"x": True})


def test_motion_parameters_reject_boolean_from_generic_mapping():
    with pytest.raises(ValidationError, match="boolean"):
        MotionDirective(kind="pan", parameters=UserDict({"x": True}))


def test_fixed_duration_requires_seconds():
    with pytest.raises(ValidationError, match="requires seconds"):
        DurationPolicy(mode="fixed")


def test_duration_bounds_must_be_ordered():
    with pytest.raises(ValidationError, match="cannot exceed"):
        DurationPolicy(mode="content_driven", minimum_seconds=5, maximum_seconds=4)


def test_renderer_default_must_be_allowed():
    with pytest.raises(ValidationError, match="must be present"):
        RendererPolicy(allowed=["remotion"], default_preference="hyperframes")


# ---------------------------------------------------------------------------
# P5 Dependency Graph and Manifest 2.3 strict/frozen schema tests
# ---------------------------------------------------------------------------


def make_dependency_node(
    *,
    node_id: str = "creative:story:story-1",
    kind: DependencyNodeKind = DependencyNodeKind.CREATIVE_ARTIFACT,
    semantic_role: DependencySemanticRole = DependencySemanticRole.NONE,
    artifact_id: str = "story-1",
    artifact_revision: int | None = 1,
    contributions: tuple[FingerprintContribution, ...] = (
        FingerprintContribution(key="story.body", fingerprint=ZERO_HASH),
    ),
) -> DependencyNode:
    return DependencyNode(
        node_id=node_id,
        kind=kind,
        semantic_role=semantic_role,
        artifact_id=artifact_id,
        artifact_revision=artifact_revision,
        contributions=contributions,
    )


def make_dependency_graph_snapshot_pointer(
    *,
    revision_id: str = ZERO_HASH,
    file_sha256: str = ONE_HASH,
) -> DependencyGraphSnapshotPointer:
    return DependencyGraphSnapshotPointer(
        revision_id=revision_id,
        content_hash=revision_id,
        path=Path(f"state/dependency_graph.{revision_id}.json"),
        file_sha256=file_sha256,
    )


def make_dependency_graph_snapshot() -> DependencyGraphSnapshot:
    return DependencyGraphSnapshot(
        schema_version="2.0",
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        nodes=(
            make_dependency_node(
                node_id="creative:story:story-1",
                kind=DependencyNodeKind.CREATIVE_ARTIFACT,
                semantic_role=DependencySemanticRole.NONE,
                artifact_id="story-1",
            ),
        ),
        edges=(),
    )


def test_p5_error_codes_are_typed_and_non_retryable_by_default():
    assert ErrorCode.DEPENDENCY_GRAPH_INVALID.value == "dependency_graph_invalid"
    assert (
        ErrorCode.DEPENDENCY_RESOLUTION_INVALID.value
        == "dependency_resolution_invalid"
    )
    assert AiVideoError(
        code=ErrorCode.DEPENDENCY_GRAPH_INVALID, user_message="safe"
    ).retryable is False
    assert AiVideoError(
        code=ErrorCode.DEPENDENCY_RESOLUTION_INVALID, user_message="safe"
    ).retryable is False


def test_dependency_node_kind_enum_values_are_exact():
    assert {item.value for item in DependencyNodeKind} == {
        "creative_artifact",
        "asset",
        "composition_spec",
        "resolved_timeline",
        "renderer_source",
        "render",
    }


def test_dependency_semantic_role_enum_values_are_exact():
    assert {item.value for item in DependencySemanticRole} == {
        "none",
        "voice",
        "visual",
        "audio",
        "caption",
        "composition",
        "timeline",
        "renderer_source",
        "render",
    }


def test_dependency_reason_enum_values_are_exact():
    assert {item.value for item in DependencyReason} == {
        "authoring_input",
        "generation_input",
        "asset_binding",
        "audio_source",
        "alignment_timing",
        "caption_style",
        "composition_resolution",
        "timeline_materialization",
        "render_execution",
    }


def test_dependency_lifecycle_enum_values_are_exact():
    assert {item.value for item in DependencyLifecycle} == {
        "fresh",
        "stale",
        "failed",
        "blocked",
        "superseded",
    }


def test_fingerprint_contribution_rejects_non_sha256_fingerprint():
    with pytest.raises(ValidationError, match="pattern"):
        FingerprintContribution(key="voice.request", fingerprint="not-hex")


def test_fingerprint_contribution_rejects_lowercase_violation():
    bad = FingerprintContribution(key="x", fingerprint=ZERO_HASH)
    data = bad.model_dump(mode="python")
    data["fingerprint"] = "Z" * 64
    with pytest.raises(ValidationError):
        FingerprintContribution.model_validate(data)


def test_fingerprint_contribution_rejects_empty_key():
    with pytest.raises(ValidationError):
        FingerprintContribution(key="", fingerprint=ZERO_HASH)


def test_fingerprint_contribution_rejects_unknown_fields():
    bad = FingerprintContribution(key="k", fingerprint=ZERO_HASH)
    data = bad.model_dump(mode="python")
    data["unexpected"] = 1
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        FingerprintContribution.model_validate(data)


def test_dependency_node_rejects_duplicate_contribution_keys():
    with pytest.raises(ValidationError, match="unique"):
        DependencyNode(
            node_id="asset:voice-1",
            kind=DependencyNodeKind.ASSET,
            semantic_role=DependencySemanticRole.VOICE,
            artifact_id="asset-1",
            artifact_revision=1,
            contributions=(
                FingerprintContribution(key="voice.bytes", fingerprint=ZERO_HASH),
                FingerprintContribution(key="voice.bytes", fingerprint=ONE_HASH),
            ),
        )


def test_dependency_node_requires_canonical_contribution_order_by_key():
    with pytest.raises(ValidationError, match="ordered"):
        DependencyNode(
            node_id="asset:voice-1",
            kind=DependencyNodeKind.ASSET,
            semantic_role=DependencySemanticRole.VOICE,
            artifact_id="asset-1",
            artifact_revision=1,
            contributions=(
                FingerprintContribution(key="voice.b", fingerprint=ZERO_HASH),
                FingerprintContribution(key="voice.a", fingerprint=ONE_HASH),
            ),
        )


def test_dependency_node_requires_non_empty_contributions():
    with pytest.raises(ValidationError):
        DependencyNode(
            node_id="asset:voice-1",
            kind=DependencyNodeKind.ASSET,
            semantic_role=DependencySemanticRole.VOICE,
            artifact_id="asset-1",
            artifact_revision=1,
            contributions=(),
        )


def test_dependency_node_rejects_zero_artifact_revision():
    with pytest.raises(ValidationError):
        DependencyNode(
            node_id="asset:voice-1",
            kind=DependencyNodeKind.ASSET,
            semantic_role=DependencySemanticRole.VOICE,
            artifact_id="asset-1",
            artifact_revision=0,
            contributions=(FingerprintContribution(key="k", fingerprint=ZERO_HASH),),
        )


def test_dependency_node_rejects_unknown_fields():
    node = make_dependency_node()
    data = node.model_dump(mode="python")
    data["status"] = "fresh"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        DependencyNode.model_validate(data)


def test_dependency_edge_rejects_unknown_fields():
    edge = DependencyEdge(
        source_node_id="creative:shot:shot-1:voice",
        target_node_id="asset:voice-1",
        reason=DependencyReason.GENERATION_INPUT,
        contribution=FingerprintContribution(
            key="voice.semantic", fingerprint=ZERO_HASH
        ),
    )
    data = edge.model_dump(mode="python")
    data["extra"] = True
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        DependencyEdge.model_validate(data)


def test_dependency_graph_snapshot_schema_version_must_be_two_point_zero():
    with pytest.raises(ValidationError):
        DependencyGraphSnapshot(
            schema_version="2.1",
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            nodes=(),
            edges=(),
        )


def test_dependency_graph_snapshot_rejects_unknown_fields():
    snapshot = make_dependency_graph_snapshot()
    data = snapshot.model_dump(mode="python")
    data["fresh"] = True
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        DependencyGraphSnapshot.model_validate(data)


def test_dependency_graph_snapshot_has_no_mutable_status_or_lifecycle_fields():
    snapshot = make_dependency_graph_snapshot()
    dumped = snapshot.model_dump(mode="json")
    assert set(dumped.keys()) == {
        "schema_version",
        "revision_id",
        "content_hash",
        "nodes",
        "edges",
    }
    forbidden = {
        "fresh",
        "stale",
        "failed",
        "blocked",
        "superseded",
        "desired_fingerprint",
        "applied_fingerprint",
        "lifecycle",
        "blocked_by",
        "error_code",
        "error_message",
        "status",
        "attempt_id",
        "started_at",
        "finished_at",
    }
    def nested_keys(value):
        if isinstance(value, dict):
            for key, nested in value.items():
                yield key
                yield from nested_keys(nested)
        elif isinstance(value, list):
            for nested in value:
                yield from nested_keys(nested)

    assert forbidden.isdisjoint(nested_keys(dumped))


def test_dependency_graph_snapshot_rejects_duplicate_node_ids():
    with pytest.raises(ValidationError, match="unique"):
        DependencyGraphSnapshot(
            schema_version="2.0",
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            nodes=(
                make_dependency_node(node_id="creative:story:story-1"),
                make_dependency_node(node_id="creative:story:story-1"),
            ),
            edges=(),
        )


def test_dependency_graph_snapshot_requires_canonical_node_id_order():
    with pytest.raises(ValidationError, match="ordered"):
        DependencyGraphSnapshot(
            schema_version="2.0",
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            nodes=(
                make_dependency_node(node_id="creative:story:story-2"),
                make_dependency_node(node_id="creative:story:story-1"),
            ),
            edges=(),
        )


def test_dependency_graph_snapshot_rejects_duplicate_edge_identity():
    with pytest.raises(ValidationError, match="unique"):
        DependencyGraphSnapshot(
            schema_version="2.0",
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            nodes=(
                make_dependency_node(
                    node_id="asset:voice-1",
                    kind=DependencyNodeKind.ASSET,
                    semantic_role=DependencySemanticRole.VOICE,
                    artifact_id="asset-1",
                ),
                make_dependency_node(node_id="creative:shot:shot-1:voice"),
            ),
            edges=(
                DependencyEdge(
                    source_node_id="creative:shot:shot-1:voice",
                    target_node_id="asset:voice-1",
                    reason=DependencyReason.GENERATION_INPUT,
                    contribution=FingerprintContribution(
                        key="voice.semantic", fingerprint=ZERO_HASH
                    ),
                ),
                DependencyEdge(
                    source_node_id="creative:shot:shot-1:voice",
                    target_node_id="asset:voice-1",
                    reason=DependencyReason.GENERATION_INPUT,
                    contribution=FingerprintContribution(
                        key="voice.semantic", fingerprint=ZERO_HASH
                    ),
                ),
            ),
        )


def test_dependency_graph_snapshot_requires_canonical_edge_order():
    with pytest.raises(ValidationError, match="canonical"):
        DependencyGraphSnapshot(
            schema_version="2.0",
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            nodes=(
                make_dependency_node(
                    node_id="asset:voice-1",
                    kind=DependencyNodeKind.ASSET,
                    semantic_role=DependencySemanticRole.VOICE,
                    artifact_id="asset-1",
                ),
                make_dependency_node(node_id="creative:shot:shot-1:voice"),
            ),
            edges=(
                DependencyEdge(
                    source_node_id="creative:shot:shot-1:voice",
                    target_node_id="asset:voice-1",
                    reason=DependencyReason.GENERATION_INPUT,
                    contribution=FingerprintContribution(
                        key="voice.b", fingerprint=ONE_HASH
                    ),
                ),
                DependencyEdge(
                    source_node_id="creative:shot:shot-1:voice",
                    target_node_id="asset:voice-1",
                    reason=DependencyReason.GENERATION_INPUT,
                    contribution=FingerprintContribution(
                        key="voice.a", fingerprint=ZERO_HASH
                    ),
                ),
            ),
        )


def test_dependency_graph_snapshot_requires_revision_id_equal_content_hash():
    with pytest.raises(ValidationError, match="revision_id"):
        DependencyGraphSnapshot(
            schema_version="2.0",
            revision_id=ZERO_HASH,
            content_hash=ONE_HASH,
            nodes=(),
            edges=(),
        )


def test_dependency_graph_snapshot_pointer_requires_canonical_state_path():
    with pytest.raises(ValidationError, match="canonical"):
        DependencyGraphSnapshotPointer(
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            path=Path(f"state/other/{ZERO_HASH}.json"),
            file_sha256=ONE_HASH,
        )


def test_dependency_graph_snapshot_pointer_rejects_mismatched_revision_and_content_hash():
    with pytest.raises(ValidationError, match="content_hash"):
        DependencyGraphSnapshotPointer(
            revision_id=ZERO_HASH,
            content_hash=ONE_HASH,
            path=Path(f"state/dependency_graph.{ZERO_HASH}.json"),
            file_sha256=ONE_HASH,
        )


@pytest.mark.parametrize(
    "path",
    [
        Path("state/../dependency_graph.bypass.json"),
        Path("/tmp/dependency_graph.json"),
        Path("."),
    ],
)
def test_dependency_graph_snapshot_pointer_rejects_non_relative_clean_path(path):
    with pytest.raises(ValidationError):
        DependencyGraphSnapshotPointer(
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            path=path,
            file_sha256=ONE_HASH,
        )


def test_dependency_graph_snapshot_pointer_requires_independent_file_sha256():
    pointer = DependencyGraphSnapshotPointer(
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        path=Path(f"state/dependency_graph.{ZERO_HASH}.json"),
        file_sha256=ONE_HASH,
    )
    assert pointer.file_sha256 == ONE_HASH
    assert pointer.file_sha256 != pointer.revision_id
    assert pointer.file_sha256 != pointer.content_hash


def test_dependency_graph_snapshot_pointer_rejects_invalid_file_sha256():
    with pytest.raises(ValidationError):
        DependencyGraphSnapshotPointer(
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            path=Path(f"state/dependency_graph.{ZERO_HASH}.json"),
            file_sha256="not-a-hash",
        )


def test_project_dependency_evidence_rejects_wrong_owner():
    with pytest.raises(ValidationError):
        ProjectDependencyEvidence(
            owner="registry_snapshot",
            pointer=make_project_pointer(),
            artifact_id="story-main",
            artifact_fingerprint=ZERO_HASH,
        )


def test_registry_dependency_evidence_rejects_wrong_owner():
    with pytest.raises(ValidationError):
        RegistryDependencyEvidence(
            owner="project_snapshot",
            pointer=make_registry_pointer(),
            artifact_id="asset-1",
            artifact_fingerprint=ZERO_HASH,
        )


def test_render_dependency_evidence_rejects_wrong_owner():
    with pytest.raises(ValidationError):
        RenderDependencyEvidence(
            owner="project_snapshot",
            pointer=make_render_state_pointer(),
            artifact_id="render-1",
            artifact_fingerprint=ZERO_HASH,
        )


def test_dependency_node_state_fresh_requires_applied_fingerprint():
    with pytest.raises(ValidationError, match="applied_fingerprint"):
        DependencyNodeState(
            node_id="asset:voice-1",
            graph_revision_id=ZERO_HASH,
            desired_fingerprint=ZERO_HASH,
            lifecycle=DependencyLifecycle.FRESH,
        )


def test_dependency_node_state_fresh_requires_applied_fingerprint_equal_desired():
    with pytest.raises(ValidationError, match="applied_fingerprint"):
        DependencyNodeState(
            node_id="asset:voice-1",
            graph_revision_id=ZERO_HASH,
            desired_fingerprint=ZERO_HASH,
            applied_fingerprint=ONE_HASH,
            lifecycle=DependencyLifecycle.FRESH,
            applied_evidence=RegistryDependencyEvidence(
                owner="registry_snapshot",
                pointer=make_registry_pointer(),
                artifact_id="asset-1",
                artifact_fingerprint=ONE_HASH,
            ),
        )


def test_dependency_node_state_fresh_requires_applied_evidence():
    with pytest.raises(ValidationError, match="applied_evidence"):
        DependencyNodeState(
            node_id="asset:voice-1",
            graph_revision_id=ZERO_HASH,
            desired_fingerprint=ZERO_HASH,
            applied_fingerprint=ZERO_HASH,
            lifecycle=DependencyLifecycle.FRESH,
        )


def test_dependency_node_state_fresh_requires_evidence_fingerprint_match_applied():
    with pytest.raises(ValidationError, match="artifact_fingerprint"):
        DependencyNodeState(
            node_id="asset:voice-1",
            graph_revision_id=ZERO_HASH,
            desired_fingerprint=ZERO_HASH,
            applied_fingerprint=ZERO_HASH,
            lifecycle=DependencyLifecycle.FRESH,
            applied_evidence=RegistryDependencyEvidence(
                owner="registry_snapshot",
                pointer=make_registry_pointer(),
                artifact_id="asset-1",
                artifact_fingerprint=ONE_HASH,
            ),
        )


def test_dependency_node_state_fresh_rejects_blocked_by():
    with pytest.raises(ValidationError, match="blocked_by"):
        DependencyNodeState(
            node_id="asset:voice-1",
            graph_revision_id=ZERO_HASH,
            desired_fingerprint=ZERO_HASH,
            applied_fingerprint=ZERO_HASH,
            lifecycle=DependencyLifecycle.FRESH,
            applied_evidence=RegistryDependencyEvidence(
                owner="registry_snapshot",
                pointer=make_registry_pointer(),
                artifact_id="asset-1",
                artifact_fingerprint=ZERO_HASH,
            ),
            blocked_by=("creative:shot:shot-1:voice",),
        )


def test_dependency_node_state_fresh_rejects_error_fields():
    with pytest.raises(ValidationError, match="error"):
        DependencyNodeState(
            node_id="asset:voice-1",
            graph_revision_id=ZERO_HASH,
            desired_fingerprint=ZERO_HASH,
            applied_fingerprint=ZERO_HASH,
            lifecycle=DependencyLifecycle.FRESH,
            applied_evidence=RegistryDependencyEvidence(
                owner="registry_snapshot",
                pointer=make_registry_pointer(),
                artifact_id="asset-1",
                artifact_fingerprint=ZERO_HASH,
            ),
            error_code="voice_artifact",
            error_message="oops",
        )


def test_dependency_node_state_failed_requires_typed_error_fields():
    with pytest.raises(ValidationError, match="error"):
        DependencyNodeState(
            node_id="asset:voice-1",
            graph_revision_id=ZERO_HASH,
            desired_fingerprint=ZERO_HASH,
            lifecycle=DependencyLifecycle.FAILED,
        )


def test_dependency_node_state_failed_rejects_blocked_by():
    with pytest.raises(ValidationError, match="blocked_by"):
        DependencyNodeState(
            node_id="asset:voice-1",
            graph_revision_id=ZERO_HASH,
            desired_fingerprint=ZERO_HASH,
            lifecycle=DependencyLifecycle.FAILED,
            error_code="voice_provider_failed",
            error_message="safe",
            blocked_by=("creative:shot:shot-1:voice",),
        )


def test_dependency_node_state_blocked_requires_non_empty_blocked_by():
    with pytest.raises(ValidationError, match="blocked_by"):
        DependencyNodeState(
            node_id="asset:voice-1",
            graph_revision_id=ZERO_HASH,
            desired_fingerprint=ZERO_HASH,
            lifecycle=DependencyLifecycle.BLOCKED,
        )


def test_dependency_node_state_blocked_requires_canonical_blocked_by_order():
    with pytest.raises(ValidationError, match="sorted"):
        DependencyNodeState(
            node_id="asset:caption-1",
            graph_revision_id=ZERO_HASH,
            desired_fingerprint=ZERO_HASH,
            lifecycle=DependencyLifecycle.BLOCKED,
            blocked_by=(
                "creative:shot:shot-1:voice",
                "creative:shot:shot-1:visual",
            ),
        )


def test_dependency_node_state_blocked_by_must_be_unique():
    with pytest.raises(ValidationError, match="sorted"):
        DependencyNodeState(
            node_id="asset:caption-1",
            graph_revision_id=ZERO_HASH,
            desired_fingerprint=ZERO_HASH,
            lifecycle=DependencyLifecycle.BLOCKED,
            blocked_by=(
                "creative:shot:shot-1:voice",
                "creative:shot:shot-1:voice",
            ),
        )


def test_dependency_node_state_blocked_rejects_error_fields():
    with pytest.raises(ValidationError, match="error"):
        DependencyNodeState(
            node_id="asset:caption-1",
            graph_revision_id=ZERO_HASH,
            desired_fingerprint=ZERO_HASH,
            lifecycle=DependencyLifecycle.BLOCKED,
            blocked_by=("creative:shot:shot-1:voice",),
            error_code="voice_provider_failed",
            error_message="safe",
        )


def test_dependency_node_state_superseded_allows_never_applied_state():
    state = DependencyNodeState(
        node_id="asset:voice-1",
        graph_revision_id=ONE_HASH,
        desired_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.SUPERSEDED,
    )
    assert state.applied_fingerprint is None
    assert state.applied_evidence is None


@pytest.mark.parametrize(
    "lifecycle",
    [DependencyLifecycle.STALE, DependencyLifecycle.SUPERSEDED],
)
def test_dependency_node_state_non_blocked_lifecycle_rejects_blocked_by(lifecycle):
    with pytest.raises(ValidationError, match="blocked_by"):
        DependencyNodeState(
            node_id="asset:voice-1",
            graph_revision_id=ONE_HASH,
            desired_fingerprint=ZERO_HASH,
            lifecycle=lifecycle,
            blocked_by=("creative:shot:shot-1:voice",),
        )


def test_dependency_node_state_stale_rejects_error_fields():
    with pytest.raises(ValidationError, match="error"):
        DependencyNodeState(
            node_id="asset:voice-1",
            graph_revision_id=ZERO_HASH,
            desired_fingerprint=ZERO_HASH,
            lifecycle=DependencyLifecycle.STALE,
            error_code="voice_provider_failed",
            error_message="safe",
        )


def test_dependency_node_state_discriminator_picks_project_variant():
    state = DependencyNodeState(
        node_id="creative:story:story-1",
        graph_revision_id=ZERO_HASH,
        desired_fingerprint=ZERO_HASH,
        applied_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence={
            "owner": "project_snapshot",
            "pointer": make_project_pointer().model_dump(mode="python"),
            "artifact_id": "story-1",
            "artifact_fingerprint": ZERO_HASH,
        },
    )
    assert isinstance(state.applied_evidence, ProjectDependencyEvidence)


def test_dependency_node_state_discriminator_picks_registry_variant():
    state = DependencyNodeState(
        node_id="asset:voice-1",
        graph_revision_id=ZERO_HASH,
        desired_fingerprint=ZERO_HASH,
        applied_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence={
            "owner": "registry_snapshot",
            "pointer": make_registry_pointer().model_dump(mode="python"),
            "artifact_id": "asset-1",
            "artifact_fingerprint": ZERO_HASH,
        },
    )
    assert isinstance(state.applied_evidence, RegistryDependencyEvidence)


def test_dependency_node_state_discriminator_picks_render_variant():
    state = DependencyNodeState(
        node_id="render:final",
        graph_revision_id=ZERO_HASH,
        desired_fingerprint=ZERO_HASH,
        applied_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence={
            "owner": "render_state",
            "pointer": make_render_state_pointer().model_dump(mode="python"),
            "artifact_id": "render-1",
            "artifact_fingerprint": ZERO_HASH,
        },
    )
    assert isinstance(state.applied_evidence, RenderDependencyEvidence)


def test_dependency_node_state_rejects_unknown_owner_discriminator():
    with pytest.raises(ValidationError):
        DependencyNodeState.model_validate(
            {
                "node_id": "asset:voice-1",
                "graph_revision_id": ZERO_HASH,
                "desired_fingerprint": ZERO_HASH,
                "lifecycle": "fresh",
                "applied_evidence": {
                    "owner": "unknown_owner",
                    "pointer": make_registry_pointer().model_dump(mode="python"),
                    "artifact_id": "asset-1",
                    "artifact_fingerprint": ZERO_HASH,
                },
            }
        )


def make_dependency_graph_transition() -> DependencyGraphTransition:
    return DependencyGraphTransition(
        expected_manifest_revision=1,
        base_dependency_graph=None,
        candidate_dependency_graph=make_dependency_graph_snapshot_pointer(),
        candidate_dependency_states=(),
        candidate_dependency_states_hash=ZERO_HASH,
    )


def test_dependency_graph_transition_declares_required_fields():
    assert set(DependencyGraphTransition.model_fields.keys()) == {
        "expected_manifest_revision",
        "base_dependency_graph",
        "candidate_dependency_graph",
        "candidate_dependency_states",
        "candidate_dependency_states_hash",
    }


def test_dependency_graph_transition_strict_and_frozen():
    transition = make_dependency_graph_transition()
    assert transition.expected_manifest_revision == 1
    assert transition.base_dependency_graph is None
    assert transition.candidate_dependency_graph == make_dependency_graph_snapshot_pointer()
    assert transition.candidate_dependency_states == ()
    assert transition.candidate_dependency_states_hash == ZERO_HASH

    with pytest.raises((ValidationError, TypeError)):
        transition.candidate_dependency_states_hash = ONE_HASH


def test_dependency_graph_transition_rejects_zero_expected_manifest_revision():
    with pytest.raises(ValidationError):
        DependencyGraphTransition(
            expected_manifest_revision=0,
            candidate_dependency_graph=make_dependency_graph_snapshot_pointer(),
            candidate_dependency_states_hash=ZERO_HASH,
        )

def test_dependency_graph_transition_rejects_state_graph_revision_mismatch():
    state = DependencyNodeState(
        node_id="asset:voice-1",
        graph_revision_id=ONE_HASH,
        desired_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.STALE,
    )
    with pytest.raises(ValidationError, match="graph_revision_id"):
        DependencyGraphTransition(
            expected_manifest_revision=1,
            candidate_dependency_graph=make_dependency_graph_snapshot_pointer(),
            candidate_dependency_states=(state,),
            candidate_dependency_states_hash=ZERO_HASH,
        )


def test_dependency_graph_transition_accepts_superseded_origin_revision():
    state = DependencyNodeState(
        node_id="asset:retired",
        graph_revision_id=ONE_HASH,
        desired_fingerprint=ONE_HASH,
        lifecycle=DependencyLifecycle.SUPERSEDED,
    )
    transition = DependencyGraphTransition(
        expected_manifest_revision=1,
        candidate_dependency_graph=make_dependency_graph_snapshot_pointer(),
        candidate_dependency_states=(state,),
        candidate_dependency_states_hash=ZERO_HASH,
    )
    assert transition.candidate_dependency_states == (state,)


def test_dependency_graph_transition_rejects_duplicate_state_node_ids():
    state_a = DependencyNodeState(
        node_id="asset:voice-1",
        graph_revision_id=ZERO_HASH,
        desired_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.STALE,
    )
    state_b = DependencyNodeState(
        node_id="asset:voice-1",
        graph_revision_id=ZERO_HASH,
        desired_fingerprint=ONE_HASH,
        lifecycle=DependencyLifecycle.STALE,
    )
    with pytest.raises(ValidationError, match="unique"):
        DependencyGraphTransition(
            expected_manifest_revision=1,
            candidate_dependency_graph=make_dependency_graph_snapshot_pointer(),
            candidate_dependency_states=(state_a, state_b),
            candidate_dependency_states_hash=ZERO_HASH,
        )


def test_dependency_graph_transition_requires_canonical_state_order():
    state_first = DependencyNodeState(
        node_id="asset:voice-1",
        graph_revision_id=ZERO_HASH,
        desired_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.STALE,
    )
    state_second = DependencyNodeState(
        node_id="creative:shot:shot-1:voice",
        graph_revision_id=ZERO_HASH,
        desired_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.STALE,
    )
    with pytest.raises(ValidationError, match="ordered"):
        DependencyGraphTransition(
            expected_manifest_revision=1,
            candidate_dependency_graph=make_dependency_graph_snapshot_pointer(),
            candidate_dependency_states=(state_second, state_first),
            candidate_dependency_states_hash=ZERO_HASH,
        )


def test_dependency_graph_transition_accepts_canonical_state_order():
    state_first = DependencyNodeState(
        node_id="asset:voice-1",
        graph_revision_id=ZERO_HASH,
        desired_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.STALE,
    )
    state_second = DependencyNodeState(
        node_id="creative:shot:shot-1:voice",
        graph_revision_id=ZERO_HASH,
        desired_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.STALE,
    )
    transition = DependencyGraphTransition(
        expected_manifest_revision=1,
        candidate_dependency_graph=make_dependency_graph_snapshot_pointer(),
        candidate_dependency_states=(state_first, state_second),
        candidate_dependency_states_hash=ZERO_HASH,
    )
    assert transition.candidate_dependency_states == (state_first, state_second)


# ---------------------------------------------------------------------------
# Manifest 2.3 P5 graph lifecycle ownership tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("version", ["2.0", "2.1", "2.2"])
def test_manifest_20_22_omit_dependency_graph_fields_from_serialization(version):
    manifest = make_state_manifest(schema_version=version)
    data = manifest.model_dump(mode="json")
    assert "active_dependency_graph" not in data
    assert "dependency_states" not in data


@pytest.mark.parametrize("version", ["2.0", "2.1", "2.2"])
def test_manifest_20_22_reject_active_dependency_graph(version):
    with pytest.raises(ValidationError, match="2.3|graph"):
        make_state_manifest(
            schema_version=version,
            active_dependency_graph=make_dependency_graph_snapshot_pointer(),
        )


@pytest.mark.parametrize("version", ["2.0", "2.1", "2.2"])
def test_manifest_20_22_reject_dependency_states(version):
    state = DependencyNodeState(
        node_id="asset:voice-1",
        graph_revision_id=ZERO_HASH,
        desired_fingerprint=ZERO_HASH,
        applied_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=RegistryDependencyEvidence(
            owner="registry_snapshot",
            pointer=make_registry_pointer(),
            artifact_id="asset-1",
            artifact_fingerprint=ZERO_HASH,
        ),
    )
    with pytest.raises(ValidationError, match="2.3|graph"):
        make_state_manifest(
            schema_version=version,
            active_dependency_graph=make_dependency_graph_snapshot_pointer(),
            dependency_states=(state,),
        )


def test_manifest_23_accepts_active_dependency_graph_and_empty_states():
    manifest = make_state_manifest(
        schema_version="2.3",
        active_dependency_graph=make_dependency_graph_snapshot_pointer(),
        dependency_states=(),
    )
    assert manifest.active_dependency_graph is not None
    assert manifest.dependency_states == ()


def test_manifest_23_requires_active_dependency_graph_when_states_present():
    state = DependencyNodeState(
        node_id="asset:voice-1",
        graph_revision_id=ZERO_HASH,
        desired_fingerprint=ZERO_HASH,
        applied_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=RegistryDependencyEvidence(
            owner="registry_snapshot",
            pointer=make_registry_pointer(),
            artifact_id="asset-1",
            artifact_fingerprint=ZERO_HASH,
        ),
    )
    with pytest.raises(ValidationError, match="active_dependency_graph"):
        make_state_manifest(
            schema_version="2.3",
            dependency_states=(state,),
        )


def test_manifest_23_requires_state_graph_revision_to_match_active_graph():
    state = DependencyNodeState(
        node_id="asset:voice-1",
        graph_revision_id=ONE_HASH,
        desired_fingerprint=ZERO_HASH,
        applied_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=RegistryDependencyEvidence(
            owner="registry_snapshot",
            pointer=make_registry_pointer(),
            artifact_id="asset-1",
            artifact_fingerprint=ZERO_HASH,
        ),
    )
    with pytest.raises(ValidationError, match="graph_revision_id"):
        make_state_manifest(
            schema_version="2.3",
            active_dependency_graph=make_dependency_graph_snapshot_pointer(),
            dependency_states=(state,),
        )


def test_manifest_23_accepts_superseded_state_origin_revision():
    state = DependencyNodeState(
        node_id="asset:retired",
        graph_revision_id=ONE_HASH,
        desired_fingerprint=ONE_HASH,
        lifecycle=DependencyLifecycle.SUPERSEDED,
    )
    manifest = make_state_manifest(
        schema_version="2.3",
        active_dependency_graph=make_dependency_graph_snapshot_pointer(),
        dependency_states=(state,),
    )
    assert manifest.dependency_states == (state,)


def test_manifest_23_requires_unique_state_node_ids():
    state = DependencyNodeState(
        node_id="asset:voice-1",
        graph_revision_id=ZERO_HASH,
        desired_fingerprint=ZERO_HASH,
        applied_fingerprint=ZERO_HASH,
        lifecycle=DependencyLifecycle.FRESH,
        applied_evidence=RegistryDependencyEvidence(
            owner="registry_snapshot",
            pointer=make_registry_pointer(),
            artifact_id="asset-1",
            artifact_fingerprint=ZERO_HASH,
        ),
    )
    with pytest.raises(ValidationError, match="unique"):
        make_state_manifest(
            schema_version="2.3",
            active_dependency_graph=make_dependency_graph_snapshot_pointer(),
            dependency_states=(state, state),
        )


def test_manifest_23_serializes_new_graph_fields():
    manifest = make_state_manifest(
        schema_version="2.3",
        active_dependency_graph=make_dependency_graph_snapshot_pointer(),
        dependency_states=(),
    )
    data = manifest.model_dump(mode="json")
    assert "active_dependency_graph" in data
    assert "dependency_states" in data


def test_manifest_23_omits_active_dependency_graph_when_none():
    manifest = make_state_manifest(schema_version="2.3")
    data = manifest.model_dump(mode="json")
    assert "active_dependency_graph" not in data
    assert "dependency_states" not in data


def test_manifest_20_bytes_does_not_contain_p5_fields():
    data = make_state_manifest(schema_version="2.0").model_dump(mode="json")
    forbidden_bytes = (
        b"active_dependency_graph",
        b"dependency_states",
        b"base_dependency_graph",
        b"candidate_dependency_graph",
        b"candidate_dependency_states_hash",
    )
    import json as _json

    encoded = _json.dumps(data).encode("utf-8")
    for token in forbidden_bytes:
        assert token not in encoded


# ---------------------------------------------------------------------------
# StateCommitAttempt graph fields tests
# ---------------------------------------------------------------------------


def test_state_commit_attempt_omits_graph_fields_for_old_operation():
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="commit_project_registry",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-11T00:00:00+00:00",
    )
    data = attempt.model_dump(mode="json")
    assert "base_dependency_graph" not in data
    assert "candidate_dependency_graph" not in data
    assert "candidate_dependency_states_hash" not in data


def test_state_commit_attempt_p5_operation_accepts_graph_fields():
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="bootstrap_dependency_graph",
        status=StateCommitStatus.SUCCEEDED,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        base_dependency_graph=make_dependency_graph_snapshot_pointer(),
        candidate_dependency_graph=make_dependency_graph_snapshot_pointer(),
        candidate_dependency_states_hash=ZERO_HASH,
        started_at="2026-08-11T00:00:00+00:00",
        finished_at="2026-08-11T00:00:01+00:00",
    )
    assert attempt.base_dependency_graph is not None
    assert attempt.candidate_dependency_graph is not None
    assert attempt.candidate_dependency_states_hash == ZERO_HASH
    data = attempt.model_dump(mode="json")
    assert "base_dependency_graph" in data
    assert "candidate_dependency_graph" in data
    assert "candidate_dependency_states_hash" in data


def test_state_commit_attempt_p5_operation_omits_unset_graph_fields():
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="bootstrap_dependency_graph",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-11T00:00:00+00:00",
    )
    data = attempt.model_dump(mode="json")
    assert "base_dependency_graph" not in data
    assert "candidate_dependency_graph" not in data
    assert "candidate_dependency_states_hash" not in data


def test_state_commit_attempt_non_p5_operation_rejects_graph_fields():
    with pytest.raises(ValidationError, match="graph"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="historical_custom_commit",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            base_dependency_graph=make_dependency_graph_snapshot_pointer(),
            started_at="2026-08-11T00:00:00+00:00",
        )


def test_state_commit_attempt_rejects_invalid_candidate_dependency_states_hash():
    with pytest.raises(ValidationError):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="bootstrap_dependency_graph",
            status=StateCommitStatus.SUCCEEDED,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            candidate_dependency_graph=make_dependency_graph_snapshot_pointer(),
            candidate_dependency_states_hash="not-a-hash",
            started_at="2026-08-11T00:00:00+00:00",
            finished_at="2026-08-11T00:00:01+00:00",
        )


def test_manifest_22_rejects_state_commit_attempt_with_graph_fields():
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="bootstrap_dependency_graph",
        status=StateCommitStatus.SUCCEEDED,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        base_dependency_graph=make_dependency_graph_snapshot_pointer(),
        candidate_dependency_graph=make_dependency_graph_snapshot_pointer(),
        candidate_dependency_states_hash=ZERO_HASH,
        started_at="2026-08-11T00:00:00+00:00",
        finished_at="2026-08-11T00:00:01+00:00",
    )
    with pytest.raises(ValidationError, match="graph"):
        make_state_manifest(schema_version="2.2", attempts=(attempt,))


def test_manifest_23_accepts_state_commit_attempt_with_graph_fields():
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="bootstrap_dependency_graph",
        status=StateCommitStatus.SUCCEEDED,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        base_dependency_graph=make_dependency_graph_snapshot_pointer(),
        candidate_dependency_graph=make_dependency_graph_snapshot_pointer(),
        candidate_dependency_states_hash=ZERO_HASH,
        started_at="2026-08-11T00:00:00+00:00",
        finished_at="2026-08-11T00:00:01+00:00",
    )
    manifest = make_state_manifest(
        schema_version="2.3",
        attempts=(attempt,),
    )
    assert manifest.attempts == (attempt,)


# ---------------------------------------------------------------------------
# LoadedProductionProject.dependency_graph optional seam test
# ---------------------------------------------------------------------------


def test_loaded_production_project_declares_optional_dependency_graph():
    LoadedProductionProject.model_rebuild()
    assert "dependency_graph" in LoadedProductionProject.model_fields
    field = LoadedProductionProject.model_fields["dependency_graph"]
    assert field.default is None
    assert not field.is_required()
    annotation = get_args(field.annotation)
    assert type(None) in annotation


# ---------------------------------------------------------------------------
# P6 Review / Repair / Final Acceptance schema tests
# ---------------------------------------------------------------------------


def make_qa_policy_pointer() -> QaPolicyPointer:
    return QaPolicyPointer(
        path=Path(f"state/reviews/policy.{ZERO_HASH}.json"),
        policy_id="qa-default",
        policy_version="1",
        content_hash=ZERO_HASH,
        file_sha256=ONE_HASH,
    )


def test_p6_layer_and_verdict_values_are_exact():
    assert {item.value for item in QaLayer} == {
        "technical",
        "layout",
        "strategy",
        "semantic",
        "final_acceptance",
    }
    assert {item.value for item in QaVerdict} == {
        "pass",
        "fail",
        "not_evaluated",
    }


def test_qa_policy_pointer_requires_canonical_content_addressed_path():
    assert make_qa_policy_pointer().path == Path(
        f"state/reviews/policy.{ZERO_HASH}.json"
    )
    with pytest.raises(ValidationError):
        QaPolicyPointer(
            path=Path("state/reviews/policy.latest.json"),
            policy_id="qa-default",
            policy_version="1",
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        )


def test_manifest_23_rejects_explicit_p6_fields_and_serializes_unchanged():
    manifest = make_state_manifest(schema_version="2.3")
    dumped = manifest.model_dump(mode="json")
    assert "active_qa_policy" not in dumped
    assert "review_states" not in dumped
    with pytest.raises(ValidationError):
        ProductionManifest.model_validate(
            {
                **dumped,
                "active_qa_policy": make_qa_policy_pointer().model_dump(mode="json"),
            }
        )


def test_manifest_24_requires_selected_qa_policy_and_defaults_empty_review_state():
    manifest = make_state_manifest(
        schema_version="2.4",
        active_qa_policy=make_qa_policy_pointer(),
        active_dependency_graph=make_dependency_graph_snapshot_pointer(),
    )
    assert manifest.active_qa_policy == make_qa_policy_pointer()
    assert manifest.active_review_receipts == ()
    assert manifest.review_states == ()
    assert manifest.repair_outcome_receipts == ()
    assert manifest.final_acceptance_state is None
    with pytest.raises(ValidationError):
        make_state_manifest(
            schema_version="2.4",
            active_dependency_graph=make_dependency_graph_snapshot_pointer(),
        )
    with pytest.raises(ValidationError):
        make_state_manifest(
            schema_version="2.4",
            active_qa_policy=make_qa_policy_pointer(),
        )


def test_p6_error_codes_are_typed_and_non_retryable():
    assert ErrorCode.REVIEW_EVIDENCE_INVALID.value == "review_evidence_invalid"
    assert ErrorCode.REVIEW_NOT_CURRENT.value == "review_not_current"
    assert ErrorCode.REPAIR_AUTHORIZATION_REQUIRED.value == "repair_authorization_required"
    assert ErrorCode.REPAIR_SCOPE_INVALID.value == "repair_scope_invalid"
    assert ErrorCode.FINAL_ACCEPTANCE_INVALID.value == "final_acceptance_invalid"


# ---------------------------------------------------------------------------
# P7 Image Generation / Manifest 2.5 schema composition tests
# ---------------------------------------------------------------------------


def make_image_request_receipt_payload() -> dict[str, object]:
    return {
        "request_id": ZERO_HASH,
        "attempt_id": "image-attempt-1",
        "request_fingerprint": ZERO_HASH,
        "provider_kind": "fake-local",
        "model_id": "fixture-image-model-1",
        "target_shot_id": "shot-1",
        "target_asset_role": "still",
        "output_asset_id": f"image-{ZERO_HASH}",
        "preview_fingerprint": ONE_HASH,
        "authorization_fingerprint": TWO_HASH,
        "policy_receipt_id": "local-policy-1",
        "usage_license": "fixture-only",
    }


def make_image_attempt_payload(
    *,
    phase: str = "request",
    status: str = "running",
    candidate: bool = False,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "attempt_id": "image-attempt-1",
        "operation": "image_generation",
        "status": status,
        "base_manifest_revision": 1,
        "base_project": make_project_pointer().model_dump(mode="json"),
        "base_registry": make_registry_pointer().model_dump(mode="json"),
        "candidate_artifacts_hash": THREE_HASH,
        "image_request": make_image_request_receipt_payload(),
        "image_phase": phase,
        "base_dependency_graph": make_dependency_graph_snapshot_pointer().model_dump(
            mode="json"
        ),
        "started_at": "2026-08-18T00:00:00+00:00",
    }
    if candidate:
        payload.update(
            {
                "candidate_project": make_canonical_project_pointer(
                    content_hash=FOUR_HASH, file_sha256=FIVE_HASH
                ).model_dump(mode="json"),
                "candidate_registry": make_alternate_registry_pointer().model_dump(
                    mode="json"
                ),
                "candidate_dependency_graph": make_dependency_graph_snapshot_pointer(
                    revision_id=SIX_HASH, file_sha256=SEVEN_HASH
                ).model_dump(mode="json"),
                "candidate_dependency_states_hash": EIGHT_HASH,
                "candidate_image_asset_ids": (f"image-{ZERO_HASH}",),
            }
        )
    if status != "running":
        payload["finished_at"] = "2026-08-18T00:00:01+00:00"
    if status in {"failed", "interrupted", "outcome_unknown"}:
        payload["error_code"] = "typed"
        payload["error_message"] = "safe"
    return payload


def make_manifest_25_payload(*, attempt: dict[str, object]) -> dict[str, object]:
    manifest = make_state_manifest(
        schema_version="2.3",
        active_dependency_graph=make_dependency_graph_snapshot_pointer(),
    ).model_dump(mode="json")
    manifest["schema_version"] = "2.5"
    manifest["attempts"] = (attempt,)
    return manifest


def test_manifest_25_accepts_p7_only_state_from_23():
    manifest = ProductionManifest.model_validate(
        make_manifest_25_payload(attempt=make_image_attempt_payload())
    )

    assert manifest.schema_version == "2.5"
    assert manifest.active_qa_policy is None
    assert "active_qa_policy" not in manifest.model_dump(mode="json")


def test_manifest_25_preserves_complete_p6_state():
    p6 = make_state_manifest(
        schema_version="2.4",
        active_dependency_graph=make_dependency_graph_snapshot_pointer(),
        active_qa_policy=make_qa_policy_pointer(),
        review_states=(
            ReviewLayerState(
                layer=QaLayer.TECHNICAL,
                desired_fingerprint=THREE_HASH,
                lifecycle=ReviewLifecycle.STALE,
            ),
        ),
        final_acceptance_state=FinalAcceptanceState(
            desired_fingerprint=FOUR_HASH,
            lifecycle=ReviewLifecycle.STALE,
        ),
    )
    payload = p6.model_dump(mode="json")
    payload["schema_version"] = "2.5"
    payload["attempts"] = (make_image_attempt_payload(),)

    p7 = ProductionManifest.model_validate(payload)

    assert p7.active_qa_policy == p6.active_qa_policy
    assert p7.review_states == p6.review_states
    assert p7.final_acceptance_state == p6.final_acceptance_state


def test_manifest_25_runs_complete_p6_invariants_when_any_p6_field_is_explicit():
    payload = make_manifest_25_payload(attempt=make_image_attempt_payload())
    payload["review_states"] = ()

    with pytest.raises(ValidationError, match="2.5.*active_qa_policy"):
        ProductionManifest.model_validate(payload)


@pytest.mark.parametrize("operation", ["review", "repair"])
def test_manifest_25_p6_attempt_evidence_requires_active_qa_policy(operation):
    payload = make_manifest_25_payload(attempt=make_image_attempt_payload())
    p6_attempt: dict[str, object] = {
        "attempt_id": f"{operation}-attempt-1",
        "operation": operation,
        "status": "running",
        "base_manifest_revision": 1,
        "base_project": make_project_pointer().model_dump(mode="json"),
        "base_registry": make_registry_pointer().model_dump(mode="json"),
        "candidate_artifacts_hash": ZERO_HASH,
        "started_at": "2026-08-18T00:00:00+00:00",
    }
    if operation == "review":
        p6_attempt.update(
            {
                "review_request": {
                    "path": f"state/reviews/request.{ONE_HASH}.json",
                    "request_id": "review-request-1",
                    "content_hash": ONE_HASH,
                    "file_sha256": TWO_HASH,
                },
                "review_phase": "requested",
            }
        )
    else:
        p6_attempt["approved_repair_receipt"] = {
            "path": f"state/repairs/approved.{ONE_HASH}.json",
            "repair_id": "repair-1",
            "content_hash": ONE_HASH,
            "file_sha256": TWO_HASH,
        }
    payload["attempts"] = (*payload["attempts"], p6_attempt)

    with pytest.raises(ValidationError, match="2.5.*active_qa_policy"):
        ProductionManifest.model_validate(payload)


@pytest.mark.parametrize("version", ["2.0", "2.1", "2.2", "2.3", "2.4"])
def test_manifest_20_24_rejects_explicit_image_fields(version):
    payload = make_state_manifest(
        schema_version="2.4" if version == "2.4" else version,
        **(
            {
                "active_dependency_graph": make_dependency_graph_snapshot_pointer(),
                "active_qa_policy": make_qa_policy_pointer(),
            }
            if version == "2.4"
            else {
                "active_dependency_graph": make_dependency_graph_snapshot_pointer()
            }
            if version == "2.3"
            else {}
        ),
    ).model_dump(mode="json")
    payload["attempts"] = (make_image_attempt_payload(),)

    with pytest.raises(ValidationError, match=rf"{version}.*image"):
        ProductionManifest.model_validate(payload)


def test_image_attempt_requires_exact_candidate_graph_bundle():
    missing = make_image_attempt_payload(phase="candidate")
    with pytest.raises(ValidationError, match="candidate.*bundle"):
        ProductionManifest.model_validate(
            make_manifest_25_payload(attempt=missing)
        )

    candidate = ProductionManifest.model_validate(
        make_manifest_25_payload(
            attempt=make_image_attempt_payload(phase="candidate", candidate=True)
        )
    ).attempts[0]
    assert candidate.candidate_image_asset_ids == (f"image-{ZERO_HASH}",)
    assert candidate.candidate_dependency_states_hash == EIGHT_HASH

    succeeded = ProductionManifest.model_validate(
        make_manifest_25_payload(
            attempt=make_image_attempt_payload(
                phase="activate", status="succeeded", candidate=True
            )
        )
    ).attempts[0]
    assert succeeded.status is StateCommitStatus.SUCCEEDED
    assert succeeded.image_phase == "activate"


def test_image_attempt_rejects_candidate_asset_not_sealed_by_request():
    attempt = make_image_attempt_payload(phase="candidate", candidate=True)
    attempt["candidate_image_asset_ids"] = (f"image-{ONE_HASH}",)

    with pytest.raises(ValidationError, match="candidate.*request"):
        ProductionManifest.model_validate(
            make_manifest_25_payload(attempt=attempt)
        )


@pytest.mark.parametrize(
    ("status", "phase"),
    [
        ("succeeded", "candidate"),
        ("interrupted", "submit_intent"),
        ("interrupted", "provider_call"),
        ("outcome_unknown", "request"),
    ],
)
def test_image_attempt_terminal_status_requires_plan_consistent_phase(status, phase):
    with pytest.raises(ValidationError, match="image.*phase"):
        ProductionManifest.model_validate(
            make_manifest_25_payload(
                attempt=make_image_attempt_payload(
                    status=status,
                    phase=phase,
                    candidate=phase in {"candidate", "activate"},
                )
            )
        )


def test_image_attempt_serializes_only_image_fields_and_preserves_voice_provider_id():
    image = ProductionManifest.model_validate(
        make_manifest_25_payload(
            attempt={
                **make_image_attempt_payload(),
                "provider_request_id": "local-job-1",
            }
        )
    ).attempts[0].model_dump(mode="json")
    assert image["image_request"]["request_fingerprint"] == ZERO_HASH
    assert image["provider_request_id"] == "local-job-1"
    assert "voice_request" not in image
    assert "candidate_audio_asset_ids" not in image

    historical = StateCommitAttempt(
        attempt_id="historical-1",
        operation="historical_custom_commit",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-18T00:00:00+00:00",
    ).model_dump(mode="json")
    assert not {
        "image_request",
        "image_phase",
        "provider_request_id",
        "candidate_image_asset_ids",
    }.intersection(historical)


def test_image_request_receipt_and_error_codes_are_typed():
    receipt = production_models.ImageRequestReceipt.model_validate(
        make_image_request_receipt_payload()
    )
    assert receipt.output_asset_id == f"image-{ZERO_HASH}"
    assert ErrorCode.IMAGE_REQUEST_INVALID.value == "image_request_invalid"
    assert ErrorCode.IMAGE_ASSET_INVALID.value == "image_asset_invalid"
    assert ErrorCode.IMAGE_PROVIDER_FAILED.value == "image_provider_failed"
    assert (
        ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN.value
        == "image_provider_outcome_unknown"
    )
    mismatched = make_image_request_receipt_payload()
    mismatched["request_id"] = ONE_HASH
    with pytest.raises(ValidationError, match="request ID"):
        production_models.ImageRequestReceipt.model_validate(mismatched)


def test_image_lifecycle_paths_are_canonical_and_content_addressed():
    assert production_paths.canonical_image_request_path(ZERO_HASH) == Path(
        f"state/images/requests/{ZERO_HASH}.json"
    )
    assert production_paths.canonical_image_preview_path(ONE_HASH) == Path(
        f"state/images/previews/{ONE_HASH}.json"
    )
    assert production_paths.canonical_image_authorization_path(TWO_HASH) == Path(
        f"state/images/authorizations/{TWO_HASH}.json"
    )
    assert production_paths.canonical_image_submit_intent_path(ZERO_HASH) == Path(
        f"state/images/submit-intents/{ZERO_HASH}.json"
    )
    assert production_paths.canonical_image_result_path(THREE_HASH) == Path(
        f"state/images/results/{THREE_HASH}.json"
    )
    assert production_paths.canonical_image_receipt_path(FOUR_HASH) == Path(
        f"state/images/receipts/{FOUR_HASH}.json"
    )
    assert production_paths.canonical_image_asset_path(FIVE_HASH) == Path(
        f"assets/files/{FIVE_HASH}.png"
    )
    with pytest.raises(ValueError, match="SHA-256"):
        production_paths.canonical_image_request_path("latest")


def test_video_lifecycle_paths_are_canonical_and_content_addressed():
    assert production_paths.canonical_video_request_receipt_path(ZERO_HASH) == Path(
        f"state/video-generation/requests/{ZERO_HASH}.json"
    )
    assert production_paths.canonical_video_status_receipt_path(ONE_HASH) == Path(
        f"state/video-generation/status/{ONE_HASH}.json"
    )
    assert production_paths.canonical_video_asset_path(TWO_HASH) == Path(
        f"assets/files/{TWO_HASH}.mp4"
    )
    for factory in (
        production_paths.canonical_video_request_receipt_path,
        production_paths.canonical_video_status_receipt_path,
        production_paths.canonical_video_asset_path,
    ):
        with pytest.raises(ValueError, match="SHA-256"):
            factory("latest")


def test_video_attempt_pointers_reject_non_canonical_paths():
    request = _make_video_generation_attempt_state().request
    data = request.model_dump(mode="python")
    data["path"] = Path("state/video-generation/requests/latest.json")
    with pytest.raises(ValidationError, match="canonical"):
        production_models.VideoRequestReceiptPointer.model_validate(data)

    data = request.model_dump(mode="python")
    data["path"] = Path(f"../state/video-generation/requests/{ONE_HASH}.json")
    with pytest.raises(ValidationError, match="canonical"):
        production_models.VideoRequestReceiptPointer.model_validate(data)

    observation = _make_video_generation_attempt_state().latest_observation
    assert observation is not None
    data = observation.model_dump(mode="python")
    data["path"] = Path(f"/state/video-generation/status/{THREE_HASH}.json")
    with pytest.raises(ValidationError, match="canonical"):
        production_models.VideoStatusReceiptPointer.model_validate(data)
