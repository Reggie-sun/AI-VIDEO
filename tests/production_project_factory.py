from __future__ import annotations

import hashlib
import io
import json
import struct
import zlib
from datetime import date
import wave
from dataclasses import replace
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
                style_reference_id=track.style_reference_id,
                style_content_hash=(
                    prepared_caption.style_reference.content_hash
                    if prepared_caption.style_reference is not None
                    else None
                ),
                style_reference_revision=(
                    prepared_caption.style_reference.revision
                    if prepared_caption.style_reference is not None
                    else None
                ),
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
            style_reference_revision=style_reference.revision,
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


def make_p5_selective_rebuild_fixture(root: Path):
    """Build the complete two-Shot offline fixture for the P5 mutation matrix."""

    from types import SimpleNamespace

    from ai_video.production.composition import resolve_composition
    from ai_video.production.dependency import AppliedProductionEvidence
    from ai_video.production.models import (
        RenderReceipt,
        RendererSourceReceipt,
        RenderStateSnapshot,
        RenderStateSnapshotPointer,
    )

    inputs = make_p5_dependency_inputs(root)
    source_audio = next(
        asset
        for asset in inputs.project.registry.assets
        if asset.asset_id == "voice-narration"
    )
    assert source_audio.audio_metadata is not None

    style_bytes = b'{"font_family":"Fixture Serif","schema_version":"1"}'
    style_hash = hashlib.sha256(style_bytes).hexdigest()
    style_path = root / "assets/styles" / f"{style_hash}.json"
    style_path.write_bytes(style_bytes)
    style_reference = CaptionStyleReference(
        artifact_id="caption-style-2",
        revision=1,
        content_hash=style_hash,
        path=style_path.relative_to(root),
    )
    track = CaptionTrack(
        artifact_id="caption-artifact-2",
        schema_version="2.1",
        revision=1,
        content_hash=ZERO_HASH,
        creation_receipt_id="receipt-caption-2",
        source_provenance=(
            SourceReference(kind="derived", reference="alignment-narration"),
        ),
        caption_track_id="caption-track-2",
        language="en",
        script_hash=source_audio.audio_metadata.script_hash,
        transcript_hash=hashlib.sha256(b"Second shot").hexdigest(),
        source_audio_asset_id=source_audio.asset_id,
        source_audio_sha256=source_audio.sha256,
        source_sample_rate_hz=48_000,
        segments=(
            CaptionSegment(
                segment_id="segment-3",
                text="Second",
                start_sample=1_000,
                end_sample=20_000,
                speaker_id="speaker-1",
            ),
            CaptionSegment(
                segment_id="segment-4",
                text="shot",
                start_sample=22_000,
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
        alignment_receipt_id="alignment-narration",
        style_reference_id=style_reference.artifact_id,
        timing_fingerprint=ZERO_HASH,
    )
    track = track.model_copy(
        update={"timing_fingerprint": caption_timing_fingerprint(track)}
    )
    track = CaptionTrack.model_validate(seal_artifact(track).model_dump(mode="python"))
    caption_import = CaptionImportRequest.create(
        caption_track=track,
        style_reference=style_reference,
        style_bytes=style_bytes,
    )
    caption_path = root / "assets/files/caption-track-2.json"
    caption_path.write_bytes(caption_import.track_bytes)
    caption_asset = AssetRecord(
        asset_id="caption-asset-2",
        asset_type=AssetType.CAPTION,
        artifact_path=caption_path.relative_to(root),
        sha256=sha256_file(caption_path),
        size_bytes=caption_path.stat().st_size,
        mime_type="application/json",
        source_kind=AssetSourceKind.DERIVED,
        tool=ToolIdentity(name="fixture", version="1"),
        input_artifact_ids=(source_audio.asset_id,),
        input_fingerprint=source_audio.sha256,
        creation_receipt_id="receipt-caption-asset-2",
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
            style_reference_revision=style_reference.revision,
            style_content_hash=style_reference.content_hash,
        ),
    )
    registry = inputs.project.registry.model_copy(
        update={
            "revision_id": ZERO_HASH,
            "content_hash": ZERO_HASH,
            "assets": (*inputs.project.registry.assets, caption_asset),
        }
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    registry_payload = (
        json.dumps(
            registry.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    registry_path = root / f"assets/registry.{registry_hash}.json"
    registry_path.write_bytes(registry_payload)
    registry_pointer = RegistrySnapshotPointer(
        path=registry_path.relative_to(root),
        revision_id=registry_hash,
        content_hash=registry_hash,
        file_sha256=hashlib.sha256(registry_payload).hexdigest(),
    )
    project = inputs.project.model_copy(
        update={
            "manifest": inputs.project.manifest.model_copy(
                update={"active_registry": registry_pointer}
            ),
            "registry": registry,
            "asset_paths": {
                **inputs.project.asset_paths,
                caption_asset.asset_id: caption_path,
            },
        }
    )
    binding = CaptionTrackBinding(
        binding_id="captions-narration",
        caption_asset_id=caption_asset.asset_id,
        source_audio_track_id="narration",
        shot_id="shot-2",
        style_reference=style_reference,
    )
    composition_spec = seal_artifact(
        inputs.composition_spec.model_copy(
            update={
                "content_hash": ZERO_HASH,
                "caption_tracks": (*inputs.composition_spec.caption_tracks, binding),
            }
        )
    )
    inputs = replace(
        inputs,
        project=project,
        composition_spec=composition_spec,
        caption_style_fingerprints=(
            *inputs.caption_style_fingerprints,
            (
                style_reference.artifact_id,
                caption_style_fingerprint(style_reference, style_bytes),
            ),
        ),
    )

    timeline = resolve_composition(project, composition_spec, "0.7.103")
    source_sha256 = hashlib.sha256(b"p5-fixture-source").hexdigest()
    bundle_sha256 = hashlib.sha256(b"p5-fixture-bundle").hexdigest()
    output_sha256 = hashlib.sha256(b"p5-fixture-output").hexdigest()
    source_bundle = SimpleNamespace(bundle_sha256=bundle_sha256)
    render_state = RenderStateSnapshot.model_construct(
        project=project.manifest.active_project,
        registry=project.manifest.active_registry,
        timeline_fingerprint=timeline.composition_fingerprint,
        source_sha256=source_sha256,
        source_bundle=source_bundle,
        source_bundle_sha256=bundle_sha256,
        output=SimpleNamespace(file_sha256=output_sha256),
    )
    source_receipt = RendererSourceReceipt.model_construct(
        timeline_fingerprint=timeline.composition_fingerprint,
        source_sha256=source_sha256,
        source_bundle=source_bundle,
    )
    render_receipt = RenderReceipt.model_construct(
        timeline_fingerprint=timeline.composition_fingerprint,
        source_sha256=source_sha256,
        source_bundle_sha256=bundle_sha256,
        output_sha256=output_sha256,
    )
    render_pointer_hash = hashlib.sha256(b"p5-fixture-render-state").hexdigest()
    render_pointer = RenderStateSnapshotPointer(
        path=Path(f"state/render/states/{render_pointer_hash}.json"),
        revision=1,
        content_hash=render_pointer_hash,
        file_sha256=hashlib.sha256(b"p5-fixture-render-state-file").hexdigest(),
    )
    render_project = project.model_copy(
        update={
            "manifest": project.manifest.model_copy(
                update={"active_render_state": render_pointer}
            ),
            "render_state": render_state,
        }
    )
    inputs = replace(inputs, project=render_project)
    applied = AppliedProductionEvidence(
        timeline=timeline,
        source_receipt=source_receipt,
        render_receipt=render_receipt,
        render_state=render_state,
    )
    return inputs, applied


def make_manifest_23_project(root: Path):
    """Materialize a deterministic pre-render Manifest 2.3 graph fixture."""

    from ai_video.production.dependency import (
        build_applied_dependency_evidence,
        build_production_dependency_graph,
        resolve_dependency_state,
    )
    from ai_video.production.models import DependencyGraphSnapshotPointer
    from ai_video.production.paths import canonical_dependency_graph_snapshot_path

    inputs = make_p5_dependency_inputs(root)
    graph = build_production_dependency_graph(inputs)
    applied = build_applied_dependency_evidence(inputs, None)
    states = resolve_dependency_state(graph, applied).states
    graph_payload = (
        json.dumps(
            graph.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    graph_path = root / canonical_dependency_graph_snapshot_path(graph.revision_id)
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_bytes(graph_payload)
    graph_pointer = DependencyGraphSnapshotPointer(
        revision_id=graph.revision_id,
        content_hash=graph.content_hash,
        path=graph_path.relative_to(root),
        file_sha256=hashlib.sha256(graph_payload).hexdigest(),
    )
    manifest = inputs.project.manifest.model_copy(
        update={
            "schema_version": "2.3",
            "manifest_revision": inputs.project.manifest.manifest_revision + 1,
            "active_registry": inputs.project.manifest.active_registry,
            "active_dependency_graph": graph_pointer,
            "dependency_states": states,
        }
    )
    (root / "state/manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    return graph


def make_p5_bootstrap_transition(root: Path):
    """Build the exact deterministic transition from the current 2.x Manifest."""

    from ai_video.production.dependency import (
        build_applied_dependency_evidence,
        build_production_dependency_graph,
        desired_fingerprints,
        resolve_dependency_state,
    )
    from ai_video.production.state_commit import prepare_dependency_graph_transition

    inputs = make_p5_dependency_inputs(root)
    manifest_path = root / "state/manifest.json"
    manifest = ProductionManifest.model_validate_json(manifest_path.read_bytes()).model_copy(
        update={"active_registry": inputs.project.manifest.active_registry}
    )
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    graph = build_production_dependency_graph(inputs)
    states = resolve_dependency_state(
        graph, build_applied_dependency_evidence(inputs, None)
    ).states
    desired = desired_fingerprints(graph)
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=manifest.manifest_revision,
        base_dependency_graph=manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=states,
        expected_desired_fingerprints=desired,
    )
    return graph, transition, desired


def attach_p5_render_dependency_transition(root: Path, activation):
    """Bind one durable render candidate to an exact Manifest 2.3 graph."""

    from ai_video.production.dependency import (
        build_production_dependency_graph,
        desired_fingerprints,
    )
    from ai_video.production.models import (
        DependencyLifecycle,
        DependencyNodeKind,
        DependencyNodeState,
        ProjectDependencyEvidence,
        RegistryDependencyEvidence,
        RenderDependencyEvidence,
    )
    from ai_video.production.state_commit import (
        PreparedArtifact,
        prepare_dependency_graph_transition,
    )

    manifest_path = root / "state/manifest.json"
    manifest_payload = manifest_path.read_bytes()
    manifest = ProductionManifest.model_validate_json(manifest_payload)
    inputs = make_p5_dependency_inputs(root)
    manifest_path.write_bytes(manifest_payload)
    candidate_bundle = inputs.project.model_copy(
        update={
            "manifest": manifest,
            "dependency_graph": None,
            "render_state": None,
        }
    )
    graph = build_production_dependency_graph(
        replace(inputs, project=candidate_bundle, voice_requests=())
    )
    desired = desired_fingerprints(graph)
    states: list[DependencyNodeState] = []
    for node in graph.nodes:
        if node.kind is DependencyNodeKind.CREATIVE_ARTIFACT:
            evidence = ProjectDependencyEvidence(
                owner="project_snapshot",
                pointer=activation.current_project,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node.node_id],
            )
        elif node.kind is DependencyNodeKind.ASSET:
            evidence = RegistryDependencyEvidence(
                owner="registry_snapshot",
                pointer=activation.current_registry,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node.node_id],
            )
        else:
            evidence = RenderDependencyEvidence(
                owner="render_state",
                pointer=activation.next_render_state,
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
        expected_manifest_revision=activation.expected_manifest_revision,
        base_dependency_graph=manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=tuple(states),
        expected_desired_fingerprints=desired,
    )
    payload = (
        json.dumps(
            graph.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    graph_artifact = PreparedArtifact(
        transition.candidate_dependency_graph.path,
        payload,
        hashlib.sha256(payload).hexdigest(),
    )
    return replace(
        activation,
        artifacts=tuple(
            sorted(
                (*activation.artifacts, graph_artifact),
                key=lambda item: item.relative_path.as_posix(),
            )
        ),
        dependency_graph_transition=transition,
    )


def attach_p5_dependency_transition(root: Path, request):
    """Attach one exact candidate graph/state transition to a commit request."""

    from ai_video.production.dependency import (
        build_applied_dependency_evidence,
        build_production_dependency_graph,
        desired_fingerprints,
        resolve_dependency_state,
    )
    from ai_video.production.state_commit import (
        PreparedArtifact,
        prepare_dependency_graph_transition,
    )

    manifest_path = root / "state/manifest.json"
    manifest_payload = manifest_path.read_bytes()
    manifest = ProductionManifest.model_validate_json(manifest_payload)
    project_artifact = next(
        item for item in request.artifacts if item.relative_path == request.next_project.path
    )
    registry_artifact = next(
        item for item in request.artifacts if item.relative_path == request.next_registry.path
    )
    project = ProductionProject.model_validate(yaml.safe_load(project_artifact.payload))
    registry = AssetRegistrySnapshot.model_validate_json(registry_artifact.payload)
    inputs = make_p5_dependency_inputs(root)
    manifest_path.write_bytes(manifest_payload)
    candidate_manifest = manifest.model_copy(
        update={
            "active_project": request.next_project,
            "active_registry": request.next_registry,
        }
    )
    candidate_bundle = inputs.project.model_copy(
        update={
            "manifest": candidate_manifest,
            "project": project,
            "registry": registry,
            "dependency_graph": None,
            "render_state": None,
        }
    )
    candidate_inputs = replace(inputs, project=candidate_bundle)
    if request.operation == "voice_generation":
        from ai_video.production.audio import VoiceGenerationRequest
        from ai_video.production.state_commit import ProductionStateCommitter

        voice_request_path = ProductionStateCommitter(root).voice_attempt_paths(
            request.attempt_id
        ).request_path
        voice_request_artifact = next(
            item
            for item in request.artifacts
            if item.relative_path == voice_request_path.relative_to(root)
        )
        candidate_inputs = replace(
            candidate_inputs,
            voice_requests=(
                VoiceGenerationRequest.model_validate_json(
                    voice_request_artifact.payload
                ),
            ),
        )
    graph = build_production_dependency_graph(candidate_inputs)
    applied = build_applied_dependency_evidence(candidate_inputs, None)
    states = resolve_dependency_state(graph, applied).states
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=request.expected_manifest_revision,
        base_dependency_graph=manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    graph_payload = (
        json.dumps(
            graph.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    graph_artifact = PreparedArtifact(
        transition.candidate_dependency_graph.path,
        graph_payload,
        hashlib.sha256(graph_payload).hexdigest(),
    )
    artifacts = tuple(
        sorted(
            (*request.artifacts, graph_artifact),
            key=lambda item: item.relative_path.as_posix(),
        )
    )
    return replace(
        request,
        artifacts=artifacts,
        dependency_graph_transition=transition,
    ), graph


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
            style_reference_revision=style.revision,
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


def _p7_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _p7_png(width: int = 2, height: int = 1) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", checksum)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    row = b"\x00" + (b"\x11\x22\x33\xff" * width)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(row * height))
        + chunk(b"IEND", b"")
    )


def make_p7_image_candidate_preparer(base_inputs):
    """Return a deterministic, write-free Task 9 image candidate preparer."""

    from ai_video.production.dependency import (
        build_production_dependency_graph,
        resolve_dependency_state,
    )
    from ai_video.production.models import DependencyGraphSnapshotPointer
    from ai_video.production.paths import (
        canonical_dependency_graph_snapshot_path,
        canonical_image_asset_path,
        canonical_image_shot_revision_path,
    )

    def prepare(
        base_project,
        request,
        authorization,
        result,
        measured,
        receipt,
    ):
        from ai_video.production._state_commit_contracts import PreparedImageCandidate

        live_base_inputs = replace(base_inputs, project=base_project)
        image_record = AssetRecord(
            asset_id=request.output_asset_id,
            asset_type=AssetType.IMAGE,
            artifact_path=canonical_image_asset_path(measured.sha256),
            sha256=measured.sha256,
            size_bytes=measured.size_bytes,
            mime_type=measured.mime_type,
            width=measured.width,
            height=measured.height,
            source_kind=AssetSourceKind.GENERATED,
            tool=result.adapter,
            input_artifact_ids=(
                next(
                    item.artifact_id
                    for item in base_project.shots
                    if item.shot_id == request.target_shot_id
                ),
                *(
                    identity
                    for item in request.references
                    for identity in (item.creative_artifact_id, item.asset_id)
                ),
            ),
            input_fingerprint=request.request_fingerprint,
            creation_receipt_id=receipt.content_hash,
            usage_license=authorization.usage_license,
            egress=EgressMetadata(remote=False),
        )
        candidate_registry = base_project.registry.model_copy(
            update={
                "revision_id": ZERO_HASH,
                "content_hash": ZERO_HASH,
                "assets": (*base_project.registry.assets, image_record),
            }
        )
        registry_hash = registry_semantic_sha256(candidate_registry)
        candidate_registry = candidate_registry.model_copy(
            update={"revision_id": registry_hash, "content_hash": registry_hash}
        )
        registry_bytes = _p7_json_bytes(candidate_registry.model_dump(mode="json"))
        registry_path = Path(f"assets/registry.{registry_hash}.json")
        registry_pointer = RegistrySnapshotPointer(
            path=registry_path,
            revision_id=registry_hash,
            content_hash=registry_hash,
            file_sha256=hashlib.sha256(registry_bytes).hexdigest(),
        )

        base_shot = next(
            item for item in base_project.shots if item.shot_id == request.target_shot_id
        )
        candidate_shot = seal_artifact(
            base_shot.model_copy(
                update={
                    "revision": base_shot.revision + 1,
                    "content_hash": ZERO_HASH,
                    "creation_receipt_id": receipt.content_hash,
                    "required_asset_roles": tuple(
                        role.model_copy(update={"asset_ids": (request.output_asset_id,)})
                        if role.role == request.target_asset_role
                        else role
                        for role in base_shot.required_asset_roles
                    ),
                }
            )
        )
        candidate_shot_path = canonical_image_shot_revision_path(
            candidate_shot.revision, candidate_shot.content_hash
        )
        candidate_project_artifact = seal_artifact(
            base_project.project.model_copy(
                update={
                    "revision": base_project.project.revision + 1,
                    "content_hash": ZERO_HASH,
                    "creation_receipt_id": receipt.content_hash,
                    "artifacts": base_project.project.artifacts.model_copy(
                        update={
                            "shots": tuple(
                                ArtifactReference(
                                    artifact_id=candidate_shot.artifact_id,
                                    revision=candidate_shot.revision,
                                    content_hash=candidate_shot.content_hash,
                                    path=candidate_shot_path,
                                )
                                if item.artifact_id == candidate_shot.artifact_id
                                else item
                                for item in base_project.project.artifacts.shots
                            )
                        }
                    ),
                }
            )
        )
        project_bytes = yaml.safe_dump(
            candidate_project_artifact.model_dump(mode="json"),
            sort_keys=True,
            allow_unicode=True,
        ).encode("utf-8")
        project_path = Path(
            f"state/projects/project.{candidate_project_artifact.revision}."
            f"{candidate_project_artifact.content_hash}.yaml"
        )
        project_pointer = ProjectSnapshotPointer(
            path=project_path,
            revision=candidate_project_artifact.revision,
            content_hash=candidate_project_artifact.content_hash,
            file_sha256=hashlib.sha256(project_bytes).hexdigest(),
        )
        candidate_project = base_project.model_copy(
            update={
                "project": candidate_project_artifact,
                "shots": tuple(
                    candidate_shot if item.shot_id == candidate_shot.shot_id else item
                    for item in base_project.shots
                ),
                "registry": candidate_registry,
                "asset_paths": {
                    **base_project.asset_paths,
                    image_record.asset_id: base_project.root / image_record.artifact_path,
                },
                "manifest": base_project.manifest.model_copy(
                    update={
                        "active_project": project_pointer,
                        "active_registry": registry_pointer,
                    }
                ),
            }
        )
        candidate_inputs = replace(live_base_inputs, project=candidate_project)
        candidate_graph = build_production_dependency_graph(candidate_inputs)
        graph_bytes = _p7_json_bytes(candidate_graph.model_dump(mode="json"))
        graph_path = canonical_dependency_graph_snapshot_path(candidate_graph.revision_id)
        graph_pointer = DependencyGraphSnapshotPointer(
            revision_id=candidate_graph.revision_id,
            content_hash=candidate_graph.content_hash,
            path=graph_path,
            file_sha256=hashlib.sha256(graph_bytes).hexdigest(),
        )
        candidate_project = candidate_project.model_copy(
            update={
                "manifest": candidate_project.manifest.model_copy(
                    update={"active_dependency_graph": graph_pointer}
                ),
                "dependency_graph": candidate_graph,
            }
        )
        candidate_inputs = replace(candidate_inputs, project=candidate_project)
        resolution = resolve_dependency_state(
            candidate_graph, base_project.manifest.dependency_states
        )
        return PreparedImageCandidate(
            base_inputs=live_base_inputs,
            candidate_project=candidate_project,
            candidate_registry=candidate_registry,
            candidate_inputs=candidate_inputs,
            candidate_graph=candidate_graph,
            resolution=resolution,
            candidate_project_pointer=project_pointer,
            candidate_registry_pointer=registry_pointer,
            candidate_graph_pointer=graph_pointer,
            candidate_project_bytes=project_bytes,
            candidate_registry_bytes=registry_bytes,
            candidate_graph_bytes=graph_bytes,
        )

    return prepare


def make_p7_image_generation_base(root: Path):
    """Materialize the exact fresh P5 base used by Task 9 orchestration tests."""

    from ai_video.production.dependency import (
        build_production_dependency_graph,
        desired_fingerprints,
        resolve_dependency_state,
    )
    from ai_video.production.models import (
        DependencyGraphSnapshotPointer,
        DependencyLifecycle,
        DependencyNodeKind,
        DependencyNodeState,
        ProjectDependencyEvidence,
        RegistryDependencyEvidence,
    )
    from ai_video.production.paths import canonical_dependency_graph_snapshot_path
    from ai_video.production.project import load_production_project

    inputs = replace(make_p5_dependency_inputs(root), voice_requests=())
    graph = build_production_dependency_graph(inputs)
    graph_bytes = _p7_json_bytes(graph.model_dump(mode="json"))
    graph_path = canonical_dependency_graph_snapshot_path(graph.revision_id)
    (root / graph_path).parent.mkdir(parents=True, exist_ok=True)
    (root / graph_path).write_bytes(graph_bytes)
    graph_pointer = DependencyGraphSnapshotPointer(
        revision_id=graph.revision_id,
        content_hash=graph.content_hash,
        path=graph_path,
        file_sha256=hashlib.sha256(graph_bytes).hexdigest(),
    )
    manifest_path = root / "state/manifest.json"
    manifest = ProductionManifest.model_validate_json(manifest_path.read_bytes())
    desired = desired_fingerprints(graph)
    existing = {
        item.node_id: item for item in resolve_dependency_state(graph, ()).states
    }
    states = []
    for node in graph.nodes:
        if node.node_id in {
            "asset:image-shot-1",
            "creative:shot:shot-1:visual",
        }:
            states.append(existing[node.node_id])
            continue
        if node.kind is DependencyNodeKind.CREATIVE_ARTIFACT:
            evidence = ProjectDependencyEvidence(
                owner="project_snapshot",
                pointer=manifest.active_project,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node.node_id],
            )
        elif node.kind is DependencyNodeKind.ASSET:
            evidence = RegistryDependencyEvidence(
                owner="registry_snapshot",
                pointer=inputs.project.manifest.active_registry,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node.node_id],
            )
        else:
            states.append(existing[node.node_id])
            continue
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
    manifest_path.write_text(
        manifest.model_copy(
            update={
                "schema_version": "2.3",
                "manifest_revision": manifest.manifest_revision + 1,
                "active_registry": inputs.project.manifest.active_registry,
                "active_dependency_graph": graph_pointer,
                "dependency_states": resolve_dependency_state(
                    graph, tuple(sorted(states, key=lambda item: item.node_id))
                ).states,
            }
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )
    loaded = load_production_project(root / "project.yaml")
    assert build_production_dependency_graph(replace(inputs, project=loaded)) == graph
    return replace(inputs, project=loaded)


def make_p7_committed_project(
    root: Path,
    *,
    reference_mutation: str | None = None,
    unrelated_candidate_suffix: bool = False,
    changed_candidate_prefix: bool = False,
    noncanonical_candidate_shot_path: bool = False,
) -> dict[str, object]:
    """Materialize one exact Manifest 2.5 image activation without a writer."""
    from ai_video.production.dependency import (
        build_production_dependency_graph,
        resolve_dependency_state,
    )
    from ai_video.production.image import (
        ImageGenerationAuthorization,
        ImageGenerationPreview,
        ImageGenerationRequest,
        ImageLocalResourceEvidence,
        ImageProviderParameters,
        ImageProviderResult,
        ImageReferenceBinding,
        validate_image_result,
    )
    from ai_video.production.models import (
        DependencyGraphSnapshotPointer,
        StateCommitAttempt,
        StateCommitStatus,
    )
    from ai_video.production.paths import (
        canonical_dependency_graph_snapshot_path,
        canonical_image_asset_path,
        canonical_image_receipt_path,
        canonical_image_request_path,
        canonical_image_result_path,
        canonical_image_shot_revision_path,
    )

    base_inputs = make_p5_dependency_inputs(root)
    base_project = base_inputs.project
    base_graph = build_production_dependency_graph(base_inputs)
    base_states = resolve_dependency_state(base_graph, ()).states
    base_graph_bytes = _p7_json_bytes(base_graph.model_dump(mode="json"))
    base_graph_path = canonical_dependency_graph_snapshot_path(base_graph.revision_id)
    (root / base_graph_path).write_bytes(base_graph_bytes)
    base_graph_pointer = DependencyGraphSnapshotPointer(
        revision_id=base_graph.revision_id,
        content_hash=base_graph.content_hash,
        path=base_graph_path,
        file_sha256=hashlib.sha256(base_graph_bytes).hexdigest(),
    )
    base_manifest = base_project.manifest.model_copy(
        update={
            "schema_version": "2.3",
            "manifest_revision": base_project.manifest.manifest_revision + 1,
            "active_dependency_graph": base_graph_pointer,
            "dependency_states": base_states,
        }
    )
    base_project = base_project.model_copy(
        update={"manifest": base_manifest, "dependency_graph": base_graph}
    )
    base_inputs = replace(base_inputs, project=base_project)

    assets = {item.asset_id: item for item in base_project.registry.assets}
    character = base_project.characters[0]
    scene = base_project.scenes[0]
    character_asset_id = character.reference_asset_ids[0]
    scene_asset_id = scene.visual_reference_asset_ids[0]
    references = [
        ImageReferenceBinding(
            role="character",
            creative_artifact_id=character.artifact_id,
            creative_revision=character.revision,
            creative_content_hash=character.content_hash,
            asset_id=character_asset_id,
            asset_sha256=assets[character_asset_id].sha256,
        ),
        ImageReferenceBinding(
            role="scene",
            creative_artifact_id=scene.artifact_id,
            creative_revision=scene.revision,
            creative_content_hash=scene.content_hash,
            asset_id=scene_asset_id,
            asset_sha256=assets[scene_asset_id].sha256,
        ),
    ]
    if reference_mutation == "stale_creative_revision":
        references[0] = references[0].model_copy(
            update={"creative_revision": references[0].creative_revision + 1}
        )
    elif reference_mutation == "stale_creative_hash":
        references[0] = references[0].model_copy(
            update={"creative_content_hash": "f" * 64}
        )
    elif reference_mutation == "wrong_membership":
        wrong = assets["image-shot-2"]
        references[0] = references[0].model_copy(
            update={"asset_id": wrong.asset_id, "asset_sha256": wrong.sha256}
        )
    elif reference_mutation == "wrong_reference_hash":
        references[0] = references[0].model_copy(
            update={"asset_sha256": "f" * 64}
        )
    elif reference_mutation == "style_scene_binding":
        references.append(references[1].model_copy(update={"role": "style"}))
    elif reference_mutation is not None:
        raise ValueError(f"unsupported P7 reference mutation: {reference_mutation}")

    request = ImageGenerationRequest.create(
        attempt_id="image-reader-attempt-1",
        provider_kind="fake-local",
        model_id="fixture-image-model-1",
        target_shot_id="shot-1",
        target_asset_role="still",
        prompt_text="Hero enters the archive room",
        negative_prompt_text="blur, watermark",
        parameters=ImageProviderParameters(
            seed=7,
            width=2,
            height=1,
            output_format="png",
            generation_revision=1,
        ),
        references=tuple(references),
        base_project=base_manifest.active_project,
        base_registry=base_manifest.active_registry,
        base_dependency_graph=base_graph_pointer,
    )
    preview = ImageGenerationPreview.create(
        request=request,
        reference_total_bytes=sum(
            assets[item.asset_id].size_bytes for item in request.references
        ),
    )
    authorization = ImageGenerationAuthorization.create(
        request=request,
        preview=preview,
        usage_license="fixture-only",
        policy_receipt_id="fixture-local-image-policy",
    )
    png_bytes = _p7_png()
    result = ImageProviderResult.create(
        request=request,
        authorization=authorization,
        image_bytes=png_bytes,
        content_type="image/png",
        provider_request_id="fixture-local-image-1",
        adapter=ToolIdentity(name="fake-local-image", version="1"),
        resource_evidence=ImageLocalResourceEvidence(
            elapsed_milliseconds=3,
            device_kind="cpu",
            measured_peak_memory_bytes=4096,
        ),
    )
    measured, receipt = validate_image_result(request, authorization, result)
    image_record = AssetRecord(
        asset_id=request.output_asset_id,
        asset_type=AssetType.IMAGE,
        artifact_path=canonical_image_asset_path(measured.sha256),
        sha256=measured.sha256,
        size_bytes=measured.size_bytes,
        mime_type=measured.mime_type,
        width=measured.width,
        height=measured.height,
        source_kind=AssetSourceKind.GENERATED,
        tool=result.adapter,
        input_artifact_ids=(
            base_project.shots[0].artifact_id,
            *(
                identity
                for item in request.references
                for identity in (item.creative_artifact_id, item.asset_id)
            ),
        ),
        input_fingerprint=request.request_fingerprint,
        creation_receipt_id=receipt.content_hash,
        usage_license=authorization.usage_license,
        egress=EgressMetadata(remote=False),
    )
    candidate_assets = list(base_project.registry.assets)
    if changed_candidate_prefix:
        candidate_assets[0] = candidate_assets[0].model_copy(
            update={"usage_license": "changed-prefix"}
        )
    if unrelated_candidate_suffix:
        candidate_assets.append(
            base_project.registry.assets[0].model_copy(
                update={"asset_id": "image-unrelated-candidate-suffix"}
            )
        )
    candidate_assets.append(image_record)
    candidate_registry = base_project.registry.model_copy(
        update={
            "revision_id": ZERO_HASH,
            "content_hash": ZERO_HASH,
            "assets": tuple(candidate_assets),
        }
    )
    registry_hash = registry_semantic_sha256(candidate_registry)
    candidate_registry = candidate_registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    registry_bytes = _p7_json_bytes(candidate_registry.model_dump(mode="json"))
    registry_path = Path(f"assets/registry.{registry_hash}.json")
    registry_pointer = RegistrySnapshotPointer(
        path=registry_path,
        revision_id=registry_hash,
        content_hash=registry_hash,
        file_sha256=hashlib.sha256(registry_bytes).hexdigest(),
    )

    base_shot = next(item for item in base_project.shots if item.shot_id == "shot-1")
    candidate_shot = seal_artifact(
        base_shot.model_copy(
            update={
                "revision": base_shot.revision + 1,
                "content_hash": ZERO_HASH,
                "creation_receipt_id": receipt.content_hash,
                "required_asset_roles": tuple(
                    role.model_copy(update={"asset_ids": (request.output_asset_id,)})
                    if role.role == request.target_asset_role
                    else role
                    for role in base_shot.required_asset_roles
                ),
            }
        )
    )
    candidate_shot_path = (
        Path("creative/shots/noncanonical-image-candidate.yaml")
        if noncanonical_candidate_shot_path
        else canonical_image_shot_revision_path(
            candidate_shot.revision, candidate_shot.content_hash
        )
    )
    candidate_project_artifact = seal_artifact(
        base_project.project.model_copy(
            update={
                "revision": base_project.project.revision + 1,
                "content_hash": ZERO_HASH,
                "creation_receipt_id": receipt.content_hash,
                "artifacts": base_project.project.artifacts.model_copy(
                    update={
                        "shots": tuple(
                            ArtifactReference(
                                artifact_id=candidate_shot.artifact_id,
                                revision=candidate_shot.revision,
                                content_hash=candidate_shot.content_hash,
                                path=candidate_shot_path,
                            )
                            if item.artifact_id == candidate_shot.artifact_id
                            else item
                            for item in base_project.project.artifacts.shots
                        )
                    }
                ),
            }
        )
    )
    project_bytes = yaml.safe_dump(
        candidate_project_artifact.model_dump(mode="json"),
        sort_keys=True,
        allow_unicode=True,
    ).encode("utf-8")
    project_path = Path(
        f"state/projects/project.{candidate_project_artifact.revision}."
        f"{candidate_project_artifact.content_hash}.yaml"
    )
    project_pointer = ProjectSnapshotPointer(
        path=project_path,
        revision=candidate_project_artifact.revision,
        content_hash=candidate_project_artifact.content_hash,
        file_sha256=hashlib.sha256(project_bytes).hexdigest(),
    )
    candidate_project = base_project.model_copy(
        update={
            "project": candidate_project_artifact,
            "shots": tuple(
                candidate_shot if item.shot_id == candidate_shot.shot_id else item
                for item in base_project.shots
            ),
            "registry": candidate_registry,
            "asset_paths": {
                **base_project.asset_paths,
                image_record.asset_id: root / image_record.artifact_path,
            },
            "manifest": base_manifest.model_copy(
                update={
                    "active_project": project_pointer,
                    "active_registry": registry_pointer,
                }
            ),
        }
    )
    candidate_inputs = replace(base_inputs, project=candidate_project)
    candidate_graph = build_production_dependency_graph(candidate_inputs)
    graph_bytes = _p7_json_bytes(candidate_graph.model_dump(mode="json"))
    graph_path = canonical_dependency_graph_snapshot_path(candidate_graph.revision_id)
    graph_pointer = DependencyGraphSnapshotPointer(
        revision_id=candidate_graph.revision_id,
        content_hash=candidate_graph.content_hash,
        path=graph_path,
        file_sha256=hashlib.sha256(graph_bytes).hexdigest(),
    )
    candidate_states = resolve_dependency_state(candidate_graph, base_states).states
    states_hash = hashlib.sha256(
        json.dumps(
            [item.model_dump(mode="json") for item in candidate_states],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    request_path = canonical_image_request_path(request.request_fingerprint)
    result_path = canonical_image_result_path(result.result_fingerprint)
    receipt_path = canonical_image_receipt_path(receipt.content_hash)
    request_bytes = _p7_json_bytes(request.model_dump(mode="json"))
    result_bytes = _p7_json_bytes(
        result.model_dump(mode="json", exclude={"image_bytes"})
    )
    receipt_bytes = _p7_json_bytes(receipt.model_dump(mode="json"))
    shot_bytes = yaml.safe_dump(
        candidate_shot.model_dump(mode="json"),
        sort_keys=True,
        allow_unicode=True,
    ).encode("utf-8")
    evidence = {
        request_path: request_bytes,
        result_path: result_bytes,
        receipt_path: receipt_bytes,
        image_record.artifact_path: png_bytes,
        project_path: project_bytes,
        registry_path: registry_bytes,
        graph_path: graph_bytes,
        candidate_shot_path: shot_bytes,
    }
    for relative_path, payload in evidence.items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    artifact_pairs = sorted(
        (path.as_posix(), hashlib.sha256(payload).hexdigest())
        for path, payload in evidence.items()
    )
    attempt = StateCommitAttempt(
        attempt_id=request.attempt_id,
        operation="image_generation",
        status=StateCommitStatus.SUCCEEDED,
        base_manifest_revision=base_manifest.manifest_revision,
        base_project=base_manifest.active_project,
        base_registry=base_manifest.active_registry,
        candidate_project=project_pointer,
        candidate_registry=registry_pointer,
        candidate_artifacts_hash=hashlib.sha256(
            json.dumps(artifact_pairs, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        image_request={
            "request_id": request.request_id,
            "attempt_id": request.attempt_id,
            "request_fingerprint": request.request_fingerprint,
            "provider_kind": request.provider_kind,
            "model_id": request.model_id,
            "target_shot_id": request.target_shot_id,
            "target_asset_role": request.target_asset_role,
            "output_asset_id": request.output_asset_id,
            "preview_fingerprint": preview.preview_fingerprint,
            "authorization_fingerprint": authorization.authorization_fingerprint,
            "policy_receipt_id": authorization.policy_receipt_id,
            "usage_license": authorization.usage_license,
        },
        image_phase="activate",
        provider_request_id=result.provider_request_id,
        candidate_image_asset_ids=(request.output_asset_id,),
        base_dependency_graph=base_graph_pointer,
        candidate_dependency_graph=graph_pointer,
        candidate_dependency_states_hash=states_hash,
        started_at="2026-08-18T00:00:00+00:00",
        finished_at="2026-08-18T00:00:01+00:00",
    )
    manifest = base_manifest.model_copy(
        update={
            "schema_version": "2.5",
            "manifest_revision": base_manifest.manifest_revision + 1,
            "active_project": project_pointer,
            "active_registry": registry_pointer,
            "active_dependency_graph": graph_pointer,
            "dependency_states": candidate_states,
            "attempts": (attempt,),
        }
    )
    (root / "state/manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    return {
        "project_path": root / "project.yaml",
        "request": request,
        "result": result,
        "receipt": receipt,
        "image_record": image_record,
        "request_path": request_path,
        "result_path": result_path,
        "receipt_path": receipt_path,
        "image_path": image_record.artifact_path,
        "candidate_inputs": candidate_inputs,
        "candidate_project": candidate_project,
        "candidate_graph": candidate_graph,
        "candidate_states": candidate_states,
        "attempt": attempt,
        "manifest": manifest,
    }


def append_p7_committed_candidate(
    root: Path,
    fixture: dict[str, object],
) -> dict[str, object]:
    """Append a second exact selected image candidate to the P7 fixture."""
    from ai_video.production.dependency import (
        build_production_dependency_graph,
        resolve_dependency_state,
    )
    from ai_video.production.image import (
        ImageGenerationAuthorization,
        ImageGenerationPreview,
        ImageGenerationRequest,
        ImageLocalResourceEvidence,
        ImageProviderParameters,
        ImageProviderResult,
        ImageReferenceBinding,
        validate_image_result,
    )
    from ai_video.production.models import (
        DependencyGraphSnapshotPointer,
        StateCommitAttempt,
        StateCommitStatus,
    )
    from ai_video.production.paths import (
        canonical_dependency_graph_snapshot_path,
        canonical_image_asset_path,
        canonical_image_receipt_path,
        canonical_image_request_path,
        canonical_image_result_path,
        canonical_image_shot_revision_path,
    )

    current_manifest = fixture["manifest"]
    current_project = fixture["candidate_project"].model_copy(
        update={
            "manifest": current_manifest,
            "dependency_graph": fixture["candidate_graph"],
        }
    )
    current_inputs = replace(fixture["candidate_inputs"], project=current_project)
    assets = {item.asset_id: item for item in current_project.registry.assets}
    character = current_project.characters[0]
    scene = current_project.scenes[0]
    character_asset_id = character.reference_asset_ids[0]
    scene_asset_id = scene.visual_reference_asset_ids[0]
    request = ImageGenerationRequest.create(
        attempt_id="image-reader-attempt-2",
        provider_kind="fake-local",
        model_id="fixture-image-model-1",
        target_shot_id="shot-2",
        target_asset_role="still",
        prompt_text="Hero leaves the archive room",
        negative_prompt_text="blur, watermark",
        parameters=ImageProviderParameters(
            seed=8,
            width=2,
            height=1,
            output_format="png",
            generation_revision=1,
        ),
        references=(
            ImageReferenceBinding(
                role="character",
                creative_artifact_id=character.artifact_id,
                creative_revision=character.revision,
                creative_content_hash=character.content_hash,
                asset_id=character_asset_id,
                asset_sha256=assets[character_asset_id].sha256,
            ),
            ImageReferenceBinding(
                role="scene",
                creative_artifact_id=scene.artifact_id,
                creative_revision=scene.revision,
                creative_content_hash=scene.content_hash,
                asset_id=scene_asset_id,
                asset_sha256=assets[scene_asset_id].sha256,
            ),
        ),
        base_project=current_manifest.active_project,
        base_registry=current_manifest.active_registry,
        base_dependency_graph=current_manifest.active_dependency_graph,
    )
    preview = ImageGenerationPreview.create(
        request=request,
        reference_total_bytes=sum(
            assets[item.asset_id].size_bytes for item in request.references
        ),
    )
    authorization = ImageGenerationAuthorization.create(
        request=request,
        preview=preview,
        usage_license="fixture-only",
        policy_receipt_id="fixture-local-image-policy",
    )
    png_bytes = _p7_png()
    result = ImageProviderResult.create(
        request=request,
        authorization=authorization,
        image_bytes=png_bytes,
        content_type="image/png",
        provider_request_id="fixture-local-image-2",
        adapter=ToolIdentity(name="fake-local-image", version="1"),
        resource_evidence=ImageLocalResourceEvidence(
            elapsed_milliseconds=4,
            device_kind="cpu",
            measured_peak_memory_bytes=4096,
        ),
    )
    measured, receipt = validate_image_result(request, authorization, result)
    target_shot = next(item for item in current_project.shots if item.shot_id == "shot-2")
    image_record = AssetRecord(
        asset_id=request.output_asset_id,
        asset_type=AssetType.IMAGE,
        artifact_path=canonical_image_asset_path(measured.sha256),
        sha256=measured.sha256,
        size_bytes=measured.size_bytes,
        mime_type=measured.mime_type,
        width=measured.width,
        height=measured.height,
        source_kind=AssetSourceKind.GENERATED,
        tool=result.adapter,
        input_artifact_ids=(
            target_shot.artifact_id,
            *(
                identity
                for item in request.references
                for identity in (item.creative_artifact_id, item.asset_id)
            ),
        ),
        input_fingerprint=request.request_fingerprint,
        creation_receipt_id=receipt.content_hash,
        usage_license=authorization.usage_license,
        egress=EgressMetadata(remote=False),
    )
    candidate_registry = current_project.registry.model_copy(
        update={
            "revision_id": ZERO_HASH,
            "content_hash": ZERO_HASH,
            "assets": (*current_project.registry.assets, image_record),
        }
    )
    registry_hash = registry_semantic_sha256(candidate_registry)
    candidate_registry = candidate_registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    registry_bytes = _p7_json_bytes(candidate_registry.model_dump(mode="json"))
    registry_path = Path(f"assets/registry.{registry_hash}.json")
    registry_pointer = RegistrySnapshotPointer(
        path=registry_path,
        revision_id=registry_hash,
        content_hash=registry_hash,
        file_sha256=hashlib.sha256(registry_bytes).hexdigest(),
    )
    candidate_shot = seal_artifact(
        target_shot.model_copy(
            update={
                "revision": target_shot.revision + 1,
                "content_hash": ZERO_HASH,
                "creation_receipt_id": receipt.content_hash,
                "required_asset_roles": tuple(
                    role.model_copy(update={"asset_ids": (request.output_asset_id,)})
                    if role.role == request.target_asset_role
                    else role
                    for role in target_shot.required_asset_roles
                ),
            }
        )
    )
    candidate_shot_path = canonical_image_shot_revision_path(
        candidate_shot.revision, candidate_shot.content_hash
    )
    candidate_project_artifact = seal_artifact(
        current_project.project.model_copy(
            update={
                "revision": current_project.project.revision + 1,
                "content_hash": ZERO_HASH,
                "creation_receipt_id": receipt.content_hash,
                "artifacts": current_project.project.artifacts.model_copy(
                    update={
                        "shots": tuple(
                            ArtifactReference(
                                artifact_id=candidate_shot.artifact_id,
                                revision=candidate_shot.revision,
                                content_hash=candidate_shot.content_hash,
                                path=candidate_shot_path,
                            )
                            if item.artifact_id == candidate_shot.artifact_id
                            else item
                            for item in current_project.project.artifacts.shots
                        )
                    }
                ),
            }
        )
    )
    project_bytes = yaml.safe_dump(
        candidate_project_artifact.model_dump(mode="json"),
        sort_keys=True,
        allow_unicode=True,
    ).encode("utf-8")
    project_path = Path(
        f"state/projects/project.{candidate_project_artifact.revision}."
        f"{candidate_project_artifact.content_hash}.yaml"
    )
    project_pointer = ProjectSnapshotPointer(
        path=project_path,
        revision=candidate_project_artifact.revision,
        content_hash=candidate_project_artifact.content_hash,
        file_sha256=hashlib.sha256(project_bytes).hexdigest(),
    )
    candidate_project = current_project.model_copy(
        update={
            "project": candidate_project_artifact,
            "shots": tuple(
                candidate_shot if item.shot_id == candidate_shot.shot_id else item
                for item in current_project.shots
            ),
            "registry": candidate_registry,
            "asset_paths": {
                **current_project.asset_paths,
                image_record.asset_id: root / image_record.artifact_path,
            },
            "manifest": current_manifest.model_copy(
                update={
                    "active_project": project_pointer,
                    "active_registry": registry_pointer,
                }
            ),
        }
    )
    candidate_inputs = replace(current_inputs, project=candidate_project)
    candidate_graph = build_production_dependency_graph(candidate_inputs)
    graph_bytes = _p7_json_bytes(candidate_graph.model_dump(mode="json"))
    graph_path = canonical_dependency_graph_snapshot_path(candidate_graph.revision_id)
    graph_pointer = DependencyGraphSnapshotPointer(
        revision_id=candidate_graph.revision_id,
        content_hash=candidate_graph.content_hash,
        path=graph_path,
        file_sha256=hashlib.sha256(graph_bytes).hexdigest(),
    )
    candidate_states = resolve_dependency_state(
        candidate_graph, fixture["candidate_states"]
    ).states
    states_hash = hashlib.sha256(
        json.dumps(
            [item.model_dump(mode="json") for item in candidate_states],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    request_path = canonical_image_request_path(request.request_fingerprint)
    result_path = canonical_image_result_path(result.result_fingerprint)
    receipt_path = canonical_image_receipt_path(receipt.content_hash)
    request_bytes = _p7_json_bytes(request.model_dump(mode="json"))
    result_bytes = _p7_json_bytes(result.model_dump(mode="json", exclude={"image_bytes"}))
    receipt_bytes = _p7_json_bytes(receipt.model_dump(mode="json"))
    shot_bytes = yaml.safe_dump(
        candidate_shot.model_dump(mode="json"), sort_keys=True, allow_unicode=True
    ).encode("utf-8")
    evidence = {
        request_path: request_bytes,
        result_path: result_bytes,
        receipt_path: receipt_bytes,
        image_record.artifact_path: png_bytes,
        project_path: project_bytes,
        registry_path: registry_bytes,
        graph_path: graph_bytes,
        candidate_shot_path: shot_bytes,
    }
    for relative_path, payload in evidence.items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    artifact_pairs = sorted(
        (path.as_posix(), hashlib.sha256(payload).hexdigest())
        for path, payload in evidence.items()
    )
    attempt = StateCommitAttempt(
        attempt_id=request.attempt_id,
        operation="image_generation",
        status=StateCommitStatus.SUCCEEDED,
        base_manifest_revision=current_manifest.manifest_revision,
        base_project=current_manifest.active_project,
        base_registry=current_manifest.active_registry,
        candidate_project=project_pointer,
        candidate_registry=registry_pointer,
        candidate_artifacts_hash=hashlib.sha256(
            json.dumps(artifact_pairs, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        image_request={
            "request_id": request.request_id,
            "attempt_id": request.attempt_id,
            "request_fingerprint": request.request_fingerprint,
            "provider_kind": request.provider_kind,
            "model_id": request.model_id,
            "target_shot_id": request.target_shot_id,
            "target_asset_role": request.target_asset_role,
            "output_asset_id": request.output_asset_id,
            "preview_fingerprint": preview.preview_fingerprint,
            "authorization_fingerprint": authorization.authorization_fingerprint,
            "policy_receipt_id": authorization.policy_receipt_id,
            "usage_license": authorization.usage_license,
        },
        image_phase="activate",
        provider_request_id=result.provider_request_id,
        candidate_image_asset_ids=(request.output_asset_id,),
        base_dependency_graph=current_manifest.active_dependency_graph,
        candidate_dependency_graph=graph_pointer,
        candidate_dependency_states_hash=states_hash,
        started_at="2026-08-18T00:01:00+00:00",
        finished_at="2026-08-18T00:01:01+00:00",
    )
    manifest = current_manifest.model_copy(
        update={
            "manifest_revision": current_manifest.manifest_revision + 1,
            "active_project": project_pointer,
            "active_registry": registry_pointer,
            "active_dependency_graph": graph_pointer,
            "dependency_states": candidate_states,
            "attempts": (*current_manifest.attempts, attempt),
        }
    )
    (root / "state/manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    return {
        **fixture,
        "request": request,
        "result": result,
        "receipt": receipt,
        "image_record": image_record,
        "request_path": request_path,
        "result_path": result_path,
        "receipt_path": receipt_path,
        "image_path": image_record.artifact_path,
        "candidate_inputs": candidate_inputs,
        "candidate_project": candidate_project,
        "candidate_graph": candidate_graph,
        "candidate_states": candidate_states,
        "attempt": attempt,
        "manifest": manifest,
    }


def mutate_p7_evidence(root: Path, fixture: dict[str, object], mutation: str) -> None:
    if mutation == "png_bytes":
        path = root / fixture["image_path"]
        path.write_bytes(path.read_bytes()[:-1])
        return
    if mutation == "candidate_pointer":
        path = root / "state/manifest.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["attempts"][0]["candidate_dependency_graph"]["file_sha256"] = "f" * 64
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return
    if mutation == "candidate_artifacts_hash":
        path = root / "state/manifest.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["attempts"][0]["candidate_artifacts_hash"] = "f" * 64
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return
    key, field = {
        "receipt_hash": ("receipt_path", "content_hash"),
        "request_id": ("request_path", "request_id"),
        "result_request_id": ("result_path", "request_id"),
    }[mutation]
    path = root / fixture[key]
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[field] = "f" * 64
    path.write_bytes(_p7_json_bytes(payload))


def add_p6_policy_to_p7_project(root: Path) -> Path:
    from ai_video.production.models import (
        QaLayoutRules,
        QaLayer,
        QaPolicy,
        QaPolicyPointer,
        QaTechnicalThresholds,
    )
    from ai_video.production.paths import canonical_qa_policy_path

    policy = seal_artifact(
        QaPolicy(
            artifact_id="qa-policy-p7-reader",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="qa-policy-p7-reader",
            source_provenance=(
                SourceReference(kind="derived", reference="p7-reader-fixture"),
            ),
            policy_id="qa-p7-reader",
            policy_version="1",
            required_layers=(QaLayer.TECHNICAL,),
            technical_thresholds=QaTechnicalThresholds(
                black_luma_max_milli=10,
                silence_peak_max_millidb=-60_000,
                clipping_peak_min_millidb=-100,
            ),
            layout_rules=QaLayoutRules(
                safe_area_inset_milli=50,
                caption_overflow_tolerance_milli=0,
            ),
            strategy_rules_version="1",
            semantic_requirement="optional",
        )
    )
    payload = _p7_json_bytes(policy.model_dump(mode="json"))
    path = canonical_qa_policy_path(policy.content_hash)
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    pointer = QaPolicyPointer(
        path=path,
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        content_hash=policy.content_hash,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    manifest_path = root / "state/manifest.json"
    manifest = ProductionManifest.model_validate_json(manifest_path.read_bytes())
    manifest_path.write_text(
        manifest.model_copy(
            update={
                "manifest_revision": manifest.manifest_revision + 1,
                "active_qa_policy": pointer,
            }
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )
    return target
