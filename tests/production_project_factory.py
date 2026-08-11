from __future__ import annotations

import hashlib
import io
import json
import struct
from datetime import date
import wave
from pathlib import Path

import yaml

from ai_video.config import sha256_file
from ai_video.production.captions import (
    CaptionImportRequest,
    caption_style_fingerprint,
    caption_timing_fingerprint,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AudioAssetMetadata,
    AudioChannelLayout,
    AudioKind,
    AudioLoudnessMetadata,
    AudioSource,
    AudioTrackSpec,
    ArtifactReference,
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
    CaptionTrackBinding,
    Character,
    CompositionLayerSpec,
    CompositionSpec,
    DeliveryProfile,
    DurationPolicy,
    EgressMetadata,
    ProductionBrief,
    ProductionManifest,
    ProductionProject,
    ProjectSnapshotPointer,
    ProjectArtifactRefs,
    RendererKind,
    RendererIdentity,
    RendererPolicy,
    RegistrySnapshotPointer,
    Scene,
    Shot,
    SourceReference,
    Story,
    StoryBeat,
    Storyboard,
    StoryboardBeat,
    ToolIdentity,
    TransitionKind,
    TransitionSpec,
    VisualStrategy,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.paths import canonical_audio_asset_path

ZERO_HASH = "0" * 64


def make_voice_request(root: Path, *, attempt_id: str = "voice-attempt-1"):
    from ai_video.production.audio import VoiceGenerationRequest, VoiceProviderParameters

    manifest = ProductionManifest.model_validate_json(
        (root / "state/manifest.json").read_text(encoding="utf-8")
    )
    return VoiceGenerationRequest.create(
        request_id=f"request-{attempt_id}",
        attempt_id=attempt_id,
        provider_kind="fake",
        model_id="fixture-model",
        audio_kind=AudioKind.DIALOGUE,
        script_text="Exact script",
        speaker_id="speaker-1",
        voice_id="voice-1",
        language="en",
        output_container="wav",
        output_codec="pcm_s16le",
        output_sample_rate_hz=48_000,
        output_channels=1,
        provider_parameters=VoiceProviderParameters(stability_milli=500),
        base_project=manifest.active_project,
        base_registry=manifest.active_registry,
        input_artifact_ids=("shot-1",),
        input_fingerprint="1" * 64,
        pricing_snapshot_id="fixture-pricing",
        budget_reservation_receipt_id="budget-1",
        egress_authorization_receipt_id="egress-1",
    )


def make_voice_preview_and_authorization(request):
    from ai_video.production.audio import (
        VoiceCallAuthorization,
        VoicePricingSnapshot,
        build_voice_generation_preview,
    )

    pricing = VoicePricingSnapshot(
        snapshot_id=request.pricing_snapshot_id,
        effective_date=date(2026, 8, 10),
        currency="USD",
        pricing_unit="character",
        unit_price_microunits=1,
        minimum_billable_units=1,
    )
    preview = build_voice_generation_preview(
        request,
        pricing=pricing,
        destination="https://api.fixture.invalid",
        credential_reference_kind="environment",
        timing_supported=True,
        output_supported=True,
    )
    authorization = VoiceCallAuthorization.create(
        request_fingerprint=request.voice_request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        pricing_snapshot_id=request.pricing_snapshot_id,
        budget_reservation_receipt_id=request.budget_reservation_receipt_id,
        egress_authorization_receipt_id=request.egress_authorization_receipt_id,
        destination=preview.destination,
        payload_categories=preview.payload_categories,
        cost_ceiling_microunits=preview.estimated_cost_upper_bound_microunits,
        provider_enabled=True,
    )
    return preview, authorization


def make_voice_provider_result(
    request,
    preview,
    authorization,
    *,
    audio_bytes: bytes | None = None,
    policy_receipt_id: str = "fixture-policy-receipt",
    retention_mode: str = "provider_standard",
):
    from ai_video.production.audio import (
        VoiceCostReceipt,
        VoicePricingSnapshot,
        VoiceProviderResult,
        VoiceProvenanceReceipt,
    )

    payload = audio_bytes or (
        Path(__file__).parent / "fixtures/voice_captions/dialogue-mono-48000.wav"
    ).read_bytes()
    pricing = VoicePricingSnapshot(
        snapshot_id=request.pricing_snapshot_id,
        effective_date=date(2026, 8, 10),
        currency="USD",
        pricing_unit="character",
        unit_price_microunits=1,
        minimum_billable_units=1,
    )
    alignment = json.dumps(
        {"script_hash": request.script_hash, "segments": []},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    provider_request_id = "fixture-provider-request"
    cost = VoiceCostReceipt(
        currency=preview.currency,
        pricing_unit=preview.pricing_unit,
        measured_billable_units=preview.billable_units_upper_bound,
        estimated_cost_upper_bound_microunits=(
            preview.estimated_cost_upper_bound_microunits
        ),
        provider_reported_cost_microunits=None,
        pricing_snapshot_id=preview.pricing_snapshot_id,
        request_id=request.request_id,
        provider_request_id=provider_request_id,
    )
    provenance = VoiceProvenanceReceipt(
        request_id=request.request_id,
        provider_kind=request.provider_kind,
        model_id=request.model_id,
        voice_id=request.voice_id,
        language=request.language,
        request_fingerprint=request.voice_request_fingerprint,
        script_hash=request.script_hash,
        output_container=request.output_container,
        output_codec=request.output_codec,
        output_sample_rate_hz=request.output_sample_rate_hz,
        output_channels=request.output_channels,
        alignment_mode="character",
        adapter=ToolIdentity(name="fake-provider", version="1"),
        egress_authorization_receipt_id=request.egress_authorization_receipt_id,
        license_policy_decision="fixture-only",
        policy_receipt_id=policy_receipt_id,
        retention_mode=retention_mode,
        provider_request_id=provider_request_id,
        provider_trace_id="fixture-provider-trace",
    )
    return VoiceProviderResult.create(
        request=request,
        preview=preview,
        authorization=authorization,
        pricing=pricing,
        audio_bytes=payload,
        content_type="audio/wav",
        provider_request_id=provider_request_id,
        provider_trace_id="fixture-provider-trace",
        alignment_receipt_bytes=alignment,
        cost_receipt=cost,
        provenance_receipt=provenance,
        terminal_status="succeeded",
    )


def make_voice_activation_request(
    root: Path,
    request,
    authorization,
    *,
    expected_manifest_revision: int,
    include_caption: bool = False,
    caption_updates: dict[str, object] | None = None,
    corrupt_caption_timing: bool = False,
    policy_receipt_id: str = "fixture-policy-receipt",
    retention_mode: str = "provider_standard",
):
    from ai_video.production.audio import AudioProbeResult, PreparedAudioImport
    from ai_video.production.state_commit import (
        PreparedVoiceCandidate,
        ProductionStateCommitter,
    )

    payload = (Path(__file__).parent / "fixtures/voice_captions/dialogue-mono-48000.wav").read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    with wave.open(io.BytesIO(payload), "rb") as handle:
        duration_samples = handle.getnframes()
    audio_id = f"voice-{request.attempt_id}"
    record = AssetRecord(
        asset_id=audio_id,
        asset_type=AssetType.VOICE,
        artifact_path=canonical_audio_asset_path(digest),
        sha256=digest,
        size_bytes=len(payload),
        mime_type="audio/wav",
        source_kind=AssetSourceKind.GENERATED,
        tool=ToolIdentity(name="fake-provider", version="1"),
        input_artifact_ids=request.input_artifact_ids,
        input_fingerprint=request.input_fingerprint,
        creation_receipt_id=f"creation-{request.attempt_id}",
        usage_license="fixture-only",
        egress=EgressMetadata(
            remote=True,
            destination=authorization.destination,
            authorization_receipt_id=request.egress_authorization_receipt_id,
            request_fingerprint=request.voice_request_fingerprint,
            payload_fingerprint=request.script_hash,
            retention_mode="zero_retention",
            provider_policy_snapshot_id="fixture-policy",
        ),
        cost_receipt_id=f"cost-{request.attempt_id}",
        audio_metadata=AudioAssetMetadata(
            audio_kind=request.audio_kind,
            source=AudioSource(
                kind=AssetSourceKind.GENERATED,
                provider_or_tool=ToolIdentity(name="fake-provider", version="1"),
                input_artifact_ids=request.input_artifact_ids,
                input_fingerprint=request.input_fingerprint,
            ),
            speaker_id=request.speaker_id,
            voice_id=request.voice_id,
            language=request.language,
            script_hash=request.script_hash,
            duration_samples=duration_samples,
            sample_rate_hz=request.output_sample_rate_hz,
            channels=request.output_channels,
            channel_layout=AudioChannelLayout.MONO,
            codec_name="pcm_s16le",
            loudness=AudioLoudnessMetadata(),
            provenance_receipt_id=f"provenance-{request.attempt_id}",
            alignment_receipt_id=f"alignment-{request.attempt_id}",
        ),
    )
    preview, _ = make_voice_preview_and_authorization(request)
    result = make_voice_provider_result(
        request,
        preview,
        authorization,
        audio_bytes=payload,
        policy_receipt_id=policy_receipt_id,
        retention_mode=retention_mode,
    )
    probe = AudioProbeResult(
        mime_type="audio/wav",
        container_name="wav",
        file_sha256=digest,
        size_bytes=len(payload),
        file_device=0,
        file_inode=0,
        codec_name="pcm_s16le",
        duration_samples=duration_samples,
        sample_rate_hz=request.output_sample_rate_hz,
        channels=request.output_channels,
        channel_layout=AudioChannelLayout.MONO,
        decoded_pcm_sha256=digest,
        loudness=AudioLoudnessMetadata(),
        loudness_receipt_id=digest,
        ffmpeg=ToolIdentity(name="ffmpeg", version="fixture"),
        ffprobe=ToolIdentity(name="ffprobe", version="fixture"),
        content_fingerprint=digest,
    )
    prepared_caption = None
    caption_record = None
    if include_caption:
        alignment_id = f"alignment-{result.alignment_receipt_sha256}"
        track = CaptionTrack(
            artifact_id=f"caption-track-{request.attempt_id}",
            schema_version="2.1",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id=f"caption-result-{result.result_fingerprint}",
            source_provenance=(
                SourceReference(kind="derived", reference=alignment_id),
            ),
            caption_track_id=f"caption-track-{request.attempt_id}",
            language=request.language,
            script_hash=request.script_hash,
            transcript_hash=request.script_hash,
            source_audio_asset_id=audio_id,
            source_audio_sha256=result.audio_sha256,
            source_sample_rate_hz=request.output_sample_rate_hz,
            segments=(
                CaptionSegment(
                    segment_id="segment-0001",
                    text=request.script_text,
                    start_sample=0,
                    end_sample=duration_samples,
                    speaker_id=request.speaker_id,
                ),
            ),
            segmentation_policy=CaptionSegmentationPolicy(
                policy_id="generated-fixture",
                policy_version="1",
                max_characters=80,
                max_lines=2,
                break_strategy="provider_segments",
            ),
            alignment_provider=request.provider_kind,
            alignment_model=request.model_id,
            alignment_receipt_id=alignment_id,
            timing_fingerprint=ZERO_HASH,
        )
        if caption_updates:
            track = track.model_copy(update=caption_updates)
        track = track.model_copy(
            update={"timing_fingerprint": caption_timing_fingerprint(track)}
        )
        if corrupt_caption_timing:
            track = track.model_copy(update={"timing_fingerprint": "f" * 64})
        track = CaptionTrack.model_validate(seal_artifact(track).model_dump(mode="python"))
        prepared_caption = CaptionImportRequest.create(caption_track=track).prepare()
        caption_id = f"caption-{request.attempt_id}"
        caption_record = AssetRecord(
            asset_id=caption_id,
            asset_type=AssetType.CAPTION,
            artifact_path=Path(f"assets/captions/{prepared_caption.track_sha256}.json"),
            sha256=prepared_caption.track_sha256,
            size_bytes=len(prepared_caption.track_bytes),
            mime_type="application/json",
            source_kind=AssetSourceKind.DERIVED,
            tool=result.provenance_receipt.adapter,
            input_artifact_ids=(audio_id,),
            input_fingerprint=result.audio_sha256,
            creation_receipt_id=track.creation_receipt_id,
            usage_license=result.provenance_receipt.license_policy_decision,
            caption_metadata=CaptionAssetMetadata(
                caption_track_id=track.caption_track_id,
                language=track.language,
                source_audio_asset_id=audio_id,
                source_audio_sha256=result.audio_sha256,
                script_hash=track.script_hash,
                transcript_hash=track.transcript_hash,
                segment_count=1,
                word_count=0,
                segmentation_policy_id=track.segmentation_policy.policy_id,
                segmentation_policy_version=track.segmentation_policy.policy_version,
                alignment_receipt_id=track.alignment_receipt_id,
                timing_fingerprint=track.timing_fingerprint,
            ),
        )
    prepared = PreparedVoiceCandidate(
        audio=PreparedAudioImport(payload=payload, probe=probe, asset_record=record),
        caption=prepared_caption,
        caption_asset_record=caption_record,
    )
    commit, audio_ids, _ = ProductionStateCommitter(root)._prepare_voice_activation_request(
        request, preview, authorization, result, prepared
    )
    assert commit.expected_manifest_revision == expected_manifest_revision
    return commit, audio_ids


def _write_yaml(path: Path, model: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = model.model_dump(mode="json")
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _ref(model: object, path: str) -> ArtifactReference:
    return ArtifactReference(
        artifact_id=model.artifact_id,
        revision=model.revision,
        content_hash=model.content_hash,
        path=path,
    )


def write_production_project(
    root: Path,
    *,
    extra_assets: tuple[AssetRecord, ...] = (),
) -> Path:
    provenance = (SourceReference(kind="user_input", reference="brief-input-1"),)
    brief = seal_artifact(
        ProductionBrief(
            artifact_id="brief-main",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-brief-1",
            source_provenance=provenance,
            title="Comic Demo",
            objective="Introduce the hero",
            audience="General",
            format="short comic video",
            language="en",
        )
    )
    story = seal_artifact(
        Story(
            artifact_id="story-main",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-story-1",
            source_provenance=provenance,
            language="en",
            logline="A hero enters a mysterious room.",
            synopsis="The hero enters and discovers a clue.",
            beats=(StoryBeat(beat_id="story-beat-1", summary="The hero enters"),),
        )
    )
    character = seal_artifact(
        Character(
            artifact_id="character-hero",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-character-1",
            source_provenance=provenance,
            character_id="hero",
            name="Hero",
            identity="Lead detective",
            appearance_bible="Blue jacket and silver badge",
            reference_asset_ids=("image-hero-1",),
        )
    )
    scene = seal_artifact(
        Scene(
            artifact_id="scene-room",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-scene-1",
            source_provenance=provenance,
            scene_id="room",
            location="Investigation room",
            time="Night",
            mood="Mysterious",
            participant_ids=("hero",),
            visual_reference_asset_ids=("image-hero-1",),
        )
    )
    shot = seal_artifact(
        Shot(
            artifact_id="shot-artifact-1",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-shot-1",
            source_provenance=provenance,
            shot_id="shot-1",
            scene_id="room",
            storyboard_beat_id="beat-1",
            intent="Introduce the hero in the room",
            duration_policy=DurationPolicy(mode="fixed", seconds=3),
            character_ids=("hero",),
            visual_strategy=VisualStrategy.STATIC_IMAGE,
            required_asset_roles=(
                AssetRoleRequirement(
                    role="hero_still",
                    asset_ids=("image-hero-1",),
                    allowed_asset_types=(AssetType.IMAGE,),
                ),
            ),
        )
    )
    storyboard = seal_artifact(
        Storyboard(
            artifact_id="storyboard-main",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-storyboard-1",
            source_provenance=provenance,
            beats=(
                StoryboardBeat(
                    beat_id="beat-1",
                    scene_id="room",
                    shot_ids=("shot-1",),
                    narrative_intent="Reveal the hero",
                ),
            ),
        )
    )

    asset_path = root / "assets/files/hero.png"
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_bytes(b"fixture-hero-image")
    asset = AssetRecord(
        asset_id="image-hero-1",
        asset_type=AssetType.IMAGE,
        artifact_path="assets/files/hero.png",
        sha256=sha256_file(asset_path),
        size_bytes=asset_path.stat().st_size,
        mime_type="image/png",
        width=1,
        height=1,
        source_kind=AssetSourceKind.IMPORTED,
        tool=ToolIdentity(name="fixture", version="1"),
        input_artifact_ids=(character.artifact_id,),
        input_fingerprint=character.content_hash,
        creation_receipt_id="receipt-image-hero-1",
        usage_license="test-only",
    )
    registry_schema_version = (
        "2.1"
        if any(
            item.audio_metadata is not None or item.caption_metadata is not None
            for item in extra_assets
        )
        else "2.0"
    )
    registry = AssetRegistrySnapshot(
        schema_version=registry_schema_version,
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=(asset, *extra_assets),
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )

    refs = ProjectArtifactRefs(
        brief=_ref(brief, "creative/brief.yaml"),
        story=_ref(story, "creative/story.yaml"),
        characters=(_ref(character, "creative/characters/hero.yaml"),),
        scenes=(_ref(scene, "creative/scenes/room.yaml"),),
        storyboard=_ref(storyboard, "creative/storyboard.yaml"),
        shots=(_ref(shot, "creative/shots/shot-1.yaml"),),
    )
    project = seal_artifact(
        ProductionProject(
            artifact_id="project-comic-demo",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-project-1",
            source_provenance=provenance,
            project_id="comic-demo",
            title="Comic Demo",
            default_language="en",
            delivery_profile=DeliveryProfile(width=1280, height=720, fps=24),
            renderer_policy=RendererPolicy(),
            artifacts=refs,
        )
    )
    _write_yaml(root / "creative/brief.yaml", brief)
    _write_yaml(root / "creative/story.yaml", story)
    _write_yaml(root / "creative/characters/hero.yaml", character)
    _write_yaml(root / "creative/scenes/room.yaml", scene)
    _write_yaml(root / "creative/storyboard.yaml", storyboard)
    _write_yaml(root / "creative/shots/shot-1.yaml", shot)
    project_path = root / "project.yaml"
    _write_yaml(project_path, project)
    registry_path = root / f"assets/registry.{registry.revision_id}.json"
    registry_payload = (
        json.dumps(
            registry.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    registry_path.write_bytes(registry_payload)
    manifest = ProductionManifest(
        project_id=project.project_id,
        manifest_revision=1,
        active_project=ProjectSnapshotPointer(
            path=Path("project.yaml"),
            revision=project.revision,
            content_hash=project.content_hash,
            file_sha256=sha256_file(project_path),
        ),
        active_registry=RegistrySnapshotPointer(
            path=registry_path.relative_to(root),
            revision_id=registry.revision_id,
            content_hash=registry.content_hash,
            file_sha256=sha256_file(registry_path),
        ),
    )
    manifest_path = root / "state/manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return project_path


def write_and_load_two_shot_project(
    root: Path,
    *,
    filenames: tuple[str, str] = ("shot-1.png", "shot-2.png"),
    seconds: tuple[float, float] = (2.0, 2.0),
    fps: int = 24,
):
    """Build a valid two-Shot raster project through the public P2 loader."""
    write_production_project(root)
    project, registry = load_initial_models(root)

    character = Character.model_validate(
        yaml.safe_load((root / "creative/characters/hero.yaml").read_text(encoding="utf-8"))
    )
    character = seal_artifact(
        character.model_copy(
            update={
                "content_hash": ZERO_HASH,
                "reference_asset_ids": ("image-shot-1",),
            }
        )
    )
    scene = Scene.model_validate(
        yaml.safe_load((root / "creative/scenes/room.yaml").read_text(encoding="utf-8"))
    )
    scene = seal_artifact(
        scene.model_copy(
            update={
                "content_hash": ZERO_HASH,
                "visual_reference_asset_ids": ("image-shot-1",),
            }
        )
    )
    base_shot = Shot.model_validate(
        yaml.safe_load((root / "creative/shots/shot-1.yaml").read_text(encoding="utf-8"))
    )
    shots = tuple(
        seal_artifact(
            base_shot.model_copy(
                update={
                    "artifact_id": f"shot-artifact-{index}",
                    "content_hash": ZERO_HASH,
                    "creation_receipt_id": f"receipt-shot-{index}",
                    "shot_id": f"shot-{index}",
                    "duration_policy": DurationPolicy(
                        mode="fixed", seconds=seconds[index - 1]
                    ),
                    "required_asset_roles": (
                        AssetRoleRequirement(
                            role="still",
                            asset_ids=(f"image-shot-{index}",),
                            allowed_asset_types=(AssetType.IMAGE,),
                        ),
                    ),
                }
            )
        )
        for index in (1, 2)
    )
    storyboard = Storyboard.model_validate(
        yaml.safe_load((root / "creative/storyboard.yaml").read_text(encoding="utf-8"))
    )
    storyboard = seal_artifact(
        storyboard.model_copy(
            update={
                "content_hash": ZERO_HASH,
                "beats": (
                    storyboard.beats[0].model_copy(
                        update={"shot_ids": ("shot-1", "shot-2")}
                    ),
                ),
            }
        )
    )

    assets: list[AssetRecord] = []
    for index, filename in enumerate(filenames, start=1):
        if Path(filename).name != filename:
            raise ValueError("composition fixture filenames must be basenames")
        asset_path = root / "assets/files" / filename
        payload = b"\x89PNG\r\n\x1a\n" + f"fixture-raster-{index}".encode()
        asset_path.write_bytes(payload)
        assets.append(
            registry.assets[0].model_copy(
                update={
                    "asset_id": f"image-shot-{index}",
                    "artifact_path": asset_path.relative_to(root),
                    "sha256": sha256_file(asset_path),
                    "size_bytes": len(payload),
                    "mime_type": "image/png",
                    "input_artifact_ids": (character.artifact_id,),
                    "input_fingerprint": character.content_hash,
                    "creation_receipt_id": f"receipt-image-shot-{index}",
                }
            )
        )
    registry = AssetRegistrySnapshot(
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=tuple(assets),
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )

    refs = project.artifacts.model_copy(
        update={
            "characters": (_ref(character, "creative/characters/hero.yaml"),),
            "scenes": (_ref(scene, "creative/scenes/room.yaml"),),
            "storyboard": _ref(storyboard, "creative/storyboard.yaml"),
            "shots": tuple(
                _ref(shot, f"creative/shots/shot-{index}.yaml")
                for index, shot in enumerate(shots, start=1)
            ),
        }
    )
    project = seal_artifact(
        project.model_copy(
            update={
                "content_hash": ZERO_HASH,
                "delivery_profile": project.delivery_profile.model_copy(
                    update={"fps": fps}
                ),
                "artifacts": refs,
            }
        )
    )

    _write_yaml(root / "creative/characters/hero.yaml", character)
    _write_yaml(root / "creative/scenes/room.yaml", scene)
    _write_yaml(root / "creative/storyboard.yaml", storyboard)
    for index, shot in enumerate(shots, start=1):
        _write_yaml(root / f"creative/shots/shot-{index}.yaml", shot)
    project_path = root / "project.yaml"
    _write_yaml(project_path, project)
    registry_path = root / f"assets/registry.{registry.revision_id}.json"
    registry_path.write_text(
        json.dumps(
            registry.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = ProductionManifest(
        project_id=project.project_id,
        manifest_revision=1,
        active_project=ProjectSnapshotPointer(
            path=Path("project.yaml"),
            revision=project.revision,
            content_hash=project.content_hash,
            file_sha256=sha256_file(project_path),
        ),
        active_registry=RegistrySnapshotPointer(
            path=registry_path.relative_to(root),
            revision_id=registry.revision_id,
            content_hash=registry.content_hash,
            file_sha256=sha256_file(registry_path),
        ),
    )
    (root / "state/manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    return load_production_project(project_path)


def make_composition_spec(
    *,
    shot_ids: tuple[str, ...] = ("shot-1", "shot-2"),
    sample_rate: int = 48_000,
) -> CompositionSpec:
    transitions = tuple(
        TransitionSpec(
            from_shot_id=source,
            to_shot_id=target,
            kind=TransitionKind.CUT,
            duration_frames=0,
        )
        for source, target in zip(shot_ids, shot_ids[1:])
    )
    return seal_artifact(
        CompositionSpec(
            artifact_id="composition-main",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="receipt-composition-1",
            source_provenance=(
                SourceReference(kind="user_input", reference="composition-input-1"),
            ),
            composition_id="main",
            shot_ids=shot_ids,
            layers=tuple(
                CompositionLayerSpec(
                    layer_id=f"layer-{shot_id}",
                    shot_id=shot_id,
                    asset_role="still",
                    asset_id=f"image-{shot_id}",
                )
                for shot_id in shot_ids
            ),
            transitions=transitions,
            delivery_profile=DeliveryProfile(width=1280, height=720, fps=24),
            sample_rate=sample_rate,
            requested_renderer=RendererKind.HYPERFRAMES,
        )
    )


def make_loaded_project_and_spec(root: Path):
    loaded = write_and_load_two_shot_project(root)
    return loaded, make_composition_spec()


def _make_audio_asset(
    root: Path,
    *,
    asset_id: str,
    audio_kind: AudioKind,
    duration_samples: int,
    sample_rate_hz: int = 48_000,
) -> tuple[AssetRecord, Path]:
    path = root / "assets/files" / f"{asset_id}.wav"
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate_hz)
        fixture_sample = 600 + sum(asset_id.encode("utf-8")) % 1_200
        output.writeframes(struct.pack("<h", fixture_sample) * duration_samples)
    path.write_bytes(buffer.getvalue())
    speech = audio_kind in {AudioKind.DIALOGUE, AudioKind.NARRATION}
    source = AudioSource(
        kind=AssetSourceKind.IMPORTED,
        provider_or_tool=ToolIdentity(name="fixture", version="1"),
        input_artifact_ids=("story-main",) if speech else (),
        input_fingerprint=hashlib.sha256(asset_id.encode("utf-8")).hexdigest(),
        original_reference=f"fixture://{asset_id}",
    )
    metadata = AudioAssetMetadata(
        audio_kind=audio_kind,
        source=source,
        speaker_id="speaker-1" if speech else None,
        language="en" if speech else None,
        script_hash=(hashlib.sha256(b"fixture script").hexdigest() if speech else None),
        duration_samples=duration_samples,
        sample_rate_hz=sample_rate_hz,
        channels=1,
        channel_layout=AudioChannelLayout.MONO,
        codec_name="pcm_s16le",
        loudness=AudioLoudnessMetadata(),
        provenance_receipt_id=f"receipt-{asset_id}",
        alignment_receipt_id=f"alignment-{asset_id}" if speech else None,
    )
    asset_type = {
        AudioKind.DIALOGUE: AssetType.VOICE,
        AudioKind.NARRATION: AssetType.VOICE,
        AudioKind.AMBIENCE: AssetType.SFX,
        AudioKind.SFX: AssetType.SFX,
        AudioKind.BGM: AssetType.MUSIC,
    }[audio_kind]
    return (
        AssetRecord(
            asset_id=asset_id,
            asset_type=asset_type,
            artifact_path=path.relative_to(root),
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
            mime_type="audio/wav",
            duration_seconds=duration_samples / sample_rate_hz,
            source_kind=AssetSourceKind.IMPORTED,
            tool=ToolIdentity(name="fixture", version="1"),
            input_artifact_ids=source.input_artifact_ids,
            input_fingerprint=source.input_fingerprint,
            creation_receipt_id=f"receipt-{asset_id}",
            usage_license="test-only",
            audio_metadata=metadata,
        ),
        path,
    )


def make_p4_composition_fixture(
    root: Path, *, second_caption_start_sample: int = 24_000
):
    """Build deterministic P4 registry assets around the public P2-loaded project."""
    loaded = write_and_load_two_shot_project(root)
    audio_definitions = (
        ("voice-dialogue", AudioKind.DIALOGUE, 96_000),
        ("voice-narration", AudioKind.NARRATION, 48_000),
        ("ambience-room", AudioKind.AMBIENCE, 192_000),
        ("sfx-hit", AudioKind.SFX, 24_000),
        ("bgm-theme", AudioKind.BGM, 192_000),
    )
    audio_assets: list[AssetRecord] = []
    asset_paths = dict(loaded.asset_paths)
    for asset_id, audio_kind, duration_samples in audio_definitions:
        asset, path = _make_audio_asset(
            root,
            asset_id=asset_id,
            audio_kind=audio_kind,
            duration_samples=duration_samples,
        )
        audio_assets.append(asset)
        asset_paths[asset_id] = path

    style_bytes = b'{"font_family":"Fixture Sans","schema_version":"1"}'
    style_hash = hashlib.sha256(style_bytes).hexdigest()
    style_path = root / "assets/styles" / f"{style_hash}.json"
    style_path.parent.mkdir(parents=True, exist_ok=True)
    style_path.write_bytes(style_bytes)
    style_reference = CaptionStyleReference(
        artifact_id="caption-style-1",
        revision=1,
        content_hash=style_hash,
        path=style_path.relative_to(root),
    )
    source_audio = audio_assets[0]
    assert source_audio.audio_metadata is not None
    track = CaptionTrack(
        artifact_id="caption-artifact-1",
        schema_version="2.1",
        revision=1,
        content_hash=ZERO_HASH,
        creation_receipt_id="receipt-caption-1",
        source_provenance=(
            SourceReference(kind="derived", reference="alignment-dialogue"),
        ),
        caption_track_id="caption-track-1",
        language="en",
        script_hash=source_audio.audio_metadata.script_hash,
        transcript_hash=hashlib.sha256(b"Hello world").hexdigest(),
        source_audio_asset_id=source_audio.asset_id,
        source_audio_sha256=source_audio.sha256,
        source_sample_rate_hz=48_000,
        segments=(
            CaptionSegment(
                segment_id="segment-1",
                text="Hello",
                start_sample=1_000,
                end_sample=23_000,
                speaker_id="speaker-1",
            ),
            CaptionSegment(
                segment_id="segment-2",
                text="world",
                start_sample=second_caption_start_sample,
                end_sample=47_000,
                speaker_id="speaker-1",
            ),
        ),
        segmentation_policy=CaptionSegmentationPolicy(
            policy_id="fixture-segments",
            policy_version="1",
            max_characters=42,
            max_lines=2,
            break_strategy="provider_segments",
        ),
        alignment_provider="fixture",
        alignment_model="fixture-v1",
        alignment_receipt_id="alignment-dialogue",
        style_reference_id=style_reference.artifact_id,
        timing_fingerprint=ZERO_HASH,
    )
    track = track.model_copy(update={"timing_fingerprint": caption_timing_fingerprint(track)})
    track = CaptionTrack.model_validate(seal_artifact(track).model_dump(mode="python"))
    caption_import = CaptionImportRequest.create(
        caption_track=track,
        style_reference=style_reference,
        style_bytes=style_bytes,
    )
    caption_path = root / "assets/files/caption-track-1.json"
    caption_path.write_bytes(caption_import.track_bytes)
    caption_asset = AssetRecord(
        asset_id="caption-asset-1",
        asset_type=AssetType.CAPTION,
        artifact_path=caption_path.relative_to(root),
        sha256=sha256_file(caption_path),
        size_bytes=caption_path.stat().st_size,
        mime_type="application/json",
        source_kind=AssetSourceKind.DERIVED,
        tool=ToolIdentity(name="fixture", version="1"),
        input_artifact_ids=(source_audio.asset_id,),
        input_fingerprint=source_audio.sha256,
        creation_receipt_id="receipt-caption-asset-1",
        usage_license="test-only",
        caption_metadata=CaptionAssetMetadata(
            caption_track_id=track.caption_track_id,
            language=track.language,
            source_audio_asset_id=track.source_audio_asset_id,
            source_audio_sha256=track.source_audio_sha256,
            script_hash=track.script_hash,
            transcript_hash=track.transcript_hash,
            segment_count=len(track.segments),
            word_count=0,
            segmentation_policy_id=track.segmentation_policy.policy_id,
            segmentation_policy_version=track.segmentation_policy.policy_version,
            alignment_receipt_id=track.alignment_receipt_id,
            timing_fingerprint=track.timing_fingerprint,
            style_reference_id=style_reference.artifact_id,
            style_content_hash=style_reference.content_hash,
        ),
    )
    asset_paths[caption_asset.asset_id] = caption_path
    registry = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=(*loaded.registry.assets, *audio_assets, caption_asset),
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    loaded = loaded.model_copy(
        update={"registry": registry, "asset_paths": asset_paths}
    )
    spec = make_composition_spec().model_copy(
        update={
            "schema_version": "2.1",
            "content_hash": ZERO_HASH,
            "audio_tracks": (
                AudioTrackSpec(
                    track_id="dialogue",
                    audio_kind=AudioKind.DIALOGUE,
                    asset_id="voice-dialogue",
                    shot_id="shot-1",
                ),
                AudioTrackSpec(
                    track_id="narration",
                    audio_kind=AudioKind.NARRATION,
                    asset_id="voice-narration",
                    shot_id="shot-2",
                ),
                AudioTrackSpec(
                    track_id="ambience",
                    audio_kind=AudioKind.AMBIENCE,
                    asset_id="ambience-room",
                    start_sample=0,
                    gain_millidb=-2_000,
                    fade_in_samples=1_000,
                ),
                AudioTrackSpec(
                    track_id="sfx",
                    audio_kind=AudioKind.SFX,
                    asset_id="sfx-hit",
                    shot_id="shot-2",
                    start_sample=100_000,
                ),
                AudioTrackSpec(
                    track_id="bgm",
                    audio_kind=AudioKind.BGM,
                    asset_id="bgm-theme",
                    start_sample=0,
                    gain_millidb=-6_000,
                    fade_in_samples=2_000,
                    fade_out_samples=2_000,
                    ducking={
                        "sidechain_track_ids": ("dialogue", "narration"),
                        "attenuation_millidb": -12_000,
                        "attack_samples": 480,
                        "release_samples": 960,
                    },
                ),
            ),
            "caption_tracks": (
                CaptionTrackBinding(
                    binding_id="captions-dialogue",
                    caption_asset_id=caption_asset.asset_id,
                    source_audio_track_id="dialogue",
                    shot_id="shot-1",
                    style_reference=style_reference,
                ),
            ),
        }
    )
    return loaded, seal_artifact(spec)


def make_p5_dependency_inputs(root: Path):
    """Build verified deterministic P2/P3/P4 inputs for P5 graph tests."""

    from ai_video.production.dependency import ProductionDependencyInputs

    loaded, composition_spec = make_p4_composition_fixture(root)
    registry_path = root / f"assets/registry.{loaded.registry.revision_id}.json"
    registry_payload = (
        json.dumps(
            loaded.registry.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    registry_path.write_bytes(registry_payload)
    registry_pointer = RegistrySnapshotPointer(
        path=registry_path.relative_to(root),
        revision_id=loaded.registry.revision_id,
        content_hash=loaded.registry.content_hash,
        file_sha256=hashlib.sha256(registry_payload).hexdigest(),
    )
    loaded = loaded.model_copy(
        update={
            "manifest": loaded.manifest.model_copy(
                update={"active_registry": registry_pointer}
            )
        }
    )
    voice_request = make_voice_request(root)
    style_reference = composition_spec.caption_tracks[0].style_reference
    assert style_reference is not None
    style_bytes = (root / style_reference.path).read_bytes()
    return ProductionDependencyInputs(
        project=loaded,
        composition_spec=composition_spec,
        renderer=RendererIdentity(kind=RendererKind.HYPERFRAMES, version="0.7.103"),
        voice_requests=(voice_request,),
        resolver_contract_fingerprint=hashlib.sha256(
            b"resolve-composition-contract-v1"
        ).hexdigest(),
        source_materializer_contract_fingerprint=hashlib.sha256(
            b"hyperframes-source-contract-v1"
        ).hexdigest(),
        render_contract_fingerprint=hashlib.sha256(
            b"hyperframes-render-contract-v1"
        ).hexdigest(),
        caption_style_fingerprints=(
            (
                style_reference.artifact_id,
                caption_style_fingerprint(style_reference, style_bytes),
            ),
        ),
    )


def load_initial_models(root: Path) -> tuple[ProductionProject, AssetRegistrySnapshot]:
    project = ProductionProject.model_validate(
        yaml.safe_load((root / "project.yaml").read_text(encoding="utf-8"))
    )
    manifest = ProductionManifest.model_validate_json(
        (root / "state/manifest.json").read_text(encoding="utf-8")
    )
    registry = AssetRegistrySnapshot.model_validate_json(
        (root / manifest.active_registry.path).read_text(encoding="utf-8")
    )
    return project, registry


def make_audio_import_upgrade_request(
    root: Path,
    *,
    attempt_id: str = "audio-import-version-upgrade",
    include_assets: bool = False,
):
    from ai_video.production.state_commit import (
        PreparedArtifact,
        prepare_audio_registry_commit,
    )

    manifest = ProductionManifest.model_validate_json(
        (root / "state/manifest.json").read_bytes()
    )
    project, registry = load_initial_models(root)
    if not include_assets:
        upgraded = AssetRegistrySnapshot(
            schema_version="2.1",
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            assets=registry.assets,
        )
        revision = registry_semantic_sha256(upgraded)
        upgraded = upgraded.model_copy(
            update={"revision_id": revision, "content_hash": revision}
        )
        return prepare_audio_registry_commit(
            manifest=manifest,
            project=project,
            base_registry=registry,
            registry=upgraded,
            attempt_id=attempt_id,
            artifacts=(),
            active_project_artifact=PreparedArtifact(
                manifest.active_project.path,
                (root / manifest.active_project.path).read_bytes(),
                manifest.active_project.file_sha256,
            ),
        )
    audio_bytes = (
        Path(__file__).parent / "fixtures/voice_captions/dialogue-mono-48000.wav"
    ).read_bytes()
    audio_hash = hashlib.sha256(audio_bytes).hexdigest()
    with wave.open(io.BytesIO(audio_bytes), "rb") as handle:
        duration_samples = handle.getnframes()
    script_hash = hashlib.sha256(b"Exact import script").hexdigest()
    audio_id = f"voice-{attempt_id}"
    audio_record = AssetRecord(
        asset_id=audio_id,
        asset_type=AssetType.VOICE,
        artifact_path=canonical_audio_asset_path(audio_hash),
        sha256=audio_hash,
        size_bytes=len(audio_bytes),
        mime_type="audio/wav",
        source_kind=AssetSourceKind.IMPORTED,
        tool=ToolIdentity(name="fixture-import", version="1"),
        input_fingerprint=audio_hash,
        creation_receipt_id=f"audio-import-{attempt_id}",
        usage_license="fixture-only",
        audio_metadata=AudioAssetMetadata(
            audio_kind=AudioKind.DIALOGUE,
            source=AudioSource(
                kind=AssetSourceKind.IMPORTED,
                provider_or_tool=ToolIdentity(name="fixture-import", version="1"),
                input_fingerprint=audio_hash,
            ),
            speaker_id="speaker-import",
            voice_id="voice-import",
            language="en",
            script_hash=script_hash,
            duration_samples=duration_samples,
            sample_rate_hz=48_000,
            channels=1,
            channel_layout=AudioChannelLayout.MONO,
            codec_name="pcm_s16le",
            loudness=AudioLoudnessMetadata(),
            provenance_receipt_id=f"provenance-{attempt_id}",
            alignment_receipt_id=f"alignment-{attempt_id}",
        ),
    )
    style_bytes = b'{"font_family":"Fixture Sans","schema_version":"1"}'
    style_hash = hashlib.sha256(style_bytes).hexdigest()
    style = CaptionStyleReference(
        artifact_id=f"style-{attempt_id}",
        revision=1,
        content_hash=style_hash,
        path=Path(f"assets/styles/{style_hash}.json"),
    )
    track = CaptionTrack(
        artifact_id=f"caption-track-{attempt_id}",
        schema_version="2.1",
        revision=1,
        content_hash=ZERO_HASH,
        creation_receipt_id=f"caption-import-{attempt_id}",
        source_provenance=(
            SourceReference(kind="derived", reference=f"alignment-{attempt_id}"),
        ),
        caption_track_id=f"caption-track-{attempt_id}",
        language="en",
        script_hash=script_hash,
        transcript_hash=script_hash,
        source_audio_asset_id=audio_id,
        source_audio_sha256=audio_hash,
        source_sample_rate_hz=48_000,
        segments=(
            CaptionSegment(
                segment_id="segment-0001",
                text="Exact import script",
                start_sample=0,
                end_sample=duration_samples,
                speaker_id="speaker-import",
            ),
        ),
        segmentation_policy=CaptionSegmentationPolicy(
            policy_id="fixture-import",
            policy_version="1",
            max_characters=80,
            max_lines=2,
            break_strategy="provider_segments",
        ),
        alignment_provider="fixture-import",
        alignment_model="1",
        alignment_receipt_id=f"alignment-{attempt_id}",
        style_reference_id=style.artifact_id,
        timing_fingerprint=ZERO_HASH,
    )
    track = track.model_copy(update={"timing_fingerprint": caption_timing_fingerprint(track)})
    track = CaptionTrack.model_validate(seal_artifact(track).model_dump(mode="python"))
    caption_import = CaptionImportRequest.create(
        caption_track=track, style_reference=style, style_bytes=style_bytes
    )
    caption_record = AssetRecord(
        asset_id=f"caption-{attempt_id}",
        asset_type=AssetType.CAPTION,
        artifact_path=Path(f"assets/captions/{caption_import.track_sha256}.json"),
        sha256=caption_import.track_sha256,
        size_bytes=len(caption_import.track_bytes),
        mime_type="application/json",
        source_kind=AssetSourceKind.DERIVED,
        tool=ToolIdentity(name="fixture-import", version="1"),
        input_artifact_ids=(audio_id,),
        input_fingerprint=audio_hash,
        creation_receipt_id=track.creation_receipt_id,
        usage_license="fixture-only",
        caption_metadata=CaptionAssetMetadata(
            caption_track_id=track.caption_track_id,
            language=track.language,
            source_audio_asset_id=audio_id,
            source_audio_sha256=audio_hash,
            script_hash=script_hash,
            transcript_hash=script_hash,
            segment_count=1,
            word_count=0,
            segmentation_policy_id=track.segmentation_policy.policy_id,
            segmentation_policy_version=track.segmentation_policy.policy_version,
            alignment_receipt_id=track.alignment_receipt_id,
            timing_fingerprint=track.timing_fingerprint,
            style_reference_id=style.artifact_id,
            style_content_hash=style.content_hash,
        ),
    )
    upgraded = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=registry.assets
        + tuple(sorted((audio_record, caption_record), key=lambda item: item.asset_id)),
    )
    revision = registry_semantic_sha256(upgraded)
    upgraded = upgraded.model_copy(
        update={"revision_id": revision, "content_hash": revision}
    )
    return prepare_audio_registry_commit(
        manifest=manifest,
        project=project,
        base_registry=registry,
        registry=upgraded,
        attempt_id=attempt_id,
        artifacts=(
            PreparedArtifact(audio_record.artifact_path, audio_bytes, audio_hash),
            PreparedArtifact(
                caption_record.artifact_path,
                caption_import.track_bytes,
                caption_import.track_sha256,
            ),
            PreparedArtifact(style.path, style_bytes, style_hash),
        ),
        active_project_artifact=PreparedArtifact(
            manifest.active_project.path,
            (root / manifest.active_project.path).read_bytes(),
            manifest.active_project.file_sha256,
        ),
    )


def load_revision_two_models(root: Path) -> tuple[ProductionProject, AssetRegistrySnapshot]:
    project, registry = load_initial_models(root)
    revision_two = seal_artifact(
        project.model_copy(
            update={
                "revision": 2,
                "content_hash": ZERO_HASH,
                "title": "Comic Demo Revision 2",
            }
        )
    )
    return revision_two, registry


def make_revision_two_request(root: Path, *, attempt_id: str = "attempt-revision-2") -> object:
    from ai_video.production.state_commit import prepare_project_registry_commit

    manifest = ProductionManifest.model_validate_json(
        (root / "state/manifest.json").read_text(encoding="utf-8")
    )
    project, registry = load_revision_two_models(root)
    return prepare_project_registry_commit(
        manifest=manifest,
        project=project,
        registry=registry,
        attempt_id=attempt_id,
    )
