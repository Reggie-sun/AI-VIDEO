from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_video.production.audio import (
    AudioProbeToolchain,
    ClaimedAudioMetadata,
    PreparedAudioImport,
    materialize_audio_candidate,
    probe_audio_candidate,
)
from ai_video.production.captions import (
    CaptionImportRequest,
    normalize_character_alignment,
    segment_caption_track,
)
from ai_video.production.models import (
    AssetRecord,
    AssetSourceKind,
    AssetType,
    CaptionAssetMetadata,
    CaptionSegmentationPolicy,
    CaptionStyleReference,
    EgressMetadata,
    SourceReference,
)
from ai_video.production.state_commit import (
    PreparedVoiceCandidate,
)


def make_deterministic_voice_candidate_preparer(
    root: Path,
    toolchain: AudioProbeToolchain,
):
    """Build the shared deterministic P4 voice/caption candidate preparer."""

    def prepare(request, preview, authorization, result, paths):
        del preview
        snapshot = materialize_audio_candidate(
            result.audio_bytes,
            candidate_path=paths.audio_candidate_path,
            project_root=root,
            attempt_id=request.attempt_id,
        )
        assert snapshot.data == result.audio_bytes
        with paths.audio_candidate_path.open("rb") as source:
            probe = probe_audio_candidate(
                source.fileno(),
                mime_type=result.content_type,
                toolchain=toolchain,
                claimed_metadata=ClaimedAudioMetadata(
                    codec_name=request.output_codec,
                    duration_samples=96_000,
                    sample_rate_hz=request.output_sample_rate_hz,
                    channels=request.output_channels,
                ),
                measure_loudness=False,
            )
        provenance_bytes = (
            json.dumps(
                result.provenance_receipt.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode()
        cost_bytes = (
            json.dumps(
                result.cost_receipt.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode()
        audio_id = f"voice-{request.attempt_id}"
        audio_record = AssetRecord(
            asset_id=audio_id,
            asset_type=AssetType.VOICE,
            artifact_path=Path(f"assets/audio/{result.audio_sha256}.wav"),
            sha256=result.audio_sha256,
            size_bytes=len(result.audio_bytes),
            mime_type=result.content_type,
            source_kind=AssetSourceKind.GENERATED,
            tool=result.provenance_receipt.adapter,
            input_artifact_ids=request.input_artifact_ids,
            input_fingerprint=request.input_fingerprint,
            creation_receipt_id=f"voice-result-{result.result_fingerprint}",
            usage_license=result.provenance_receipt.license_policy_decision,
            egress=EgressMetadata(
                remote=True,
                destination=authorization.destination,
                authorization_receipt_id=request.egress_authorization_receipt_id,
                request_fingerprint=request.voice_request_fingerprint,
                payload_fingerprint=request.script_hash,
                retention_mode=result.provenance_receipt.retention_mode,
                provider_policy_snapshot_id=result.provenance_receipt.policy_receipt_id,
            ),
            cost_receipt_id=f"cost-{hashlib.sha256(cost_bytes).hexdigest()}",
            audio_metadata={
                "audio_kind": request.audio_kind,
                "source": {
                    "kind": "generated",
                    "provider_or_tool": result.provenance_receipt.adapter,
                    "input_artifact_ids": request.input_artifact_ids,
                    "input_fingerprint": request.input_fingerprint,
                },
                "speaker_id": request.speaker_id,
                "voice_id": request.voice_id,
                "language": request.language,
                "script_hash": request.script_hash,
                "duration_samples": probe.duration_samples,
                "sample_rate_hz": probe.sample_rate_hz,
                "channels": probe.channels,
                "channel_layout": probe.channel_layout,
                "codec_name": probe.codec_name,
                "loudness": probe.loudness,
                "provenance_receipt_id": (
                    f"provenance-{hashlib.sha256(provenance_bytes).hexdigest()}"
                ),
                "alignment_receipt_id": (
                    f"alignment-{result.alignment_receipt_sha256}"
                ),
            },
        )

        alignment = normalize_character_alignment(
            json.loads(result.alignment_receipt_bytes),
            sample_rate_hz=probe.sample_rate_hz,
            duration_samples=probe.duration_samples,
            speaker_id=request.speaker_id,
        )
        style_bytes = b'{"font_family":"Fixture Sans","schema_version":"1"}'
        style_hash = hashlib.sha256(style_bytes).hexdigest()
        style = CaptionStyleReference(
            artifact_id="caption-style-e2e",
            revision=1,
            content_hash=style_hash,
            path=Path(f"assets/styles/{style_hash}.json"),
        )
        track = segment_caption_track(
            alignment,
            artifact_id=f"caption-track-{request.attempt_id}",
            revision=1,
            creation_receipt_id=f"caption-result-{result.result_fingerprint}",
            source_provenance=(
                SourceReference(
                    kind="derived",
                    reference=f"alignment-{result.alignment_receipt_sha256}",
                ),
            ),
            caption_track_id=f"caption-track-{request.attempt_id}",
            language=request.language,
            script_text=request.script_text,
            transcript_text=request.script_text,
            source_audio_asset_id=audio_id,
            source_audio_sha256=result.audio_sha256,
            source_sample_rate_hz=probe.sample_rate_hz,
            source_duration_samples=probe.duration_samples,
            segmentation_policy=CaptionSegmentationPolicy(
                policy_id="e2e-sentence",
                policy_version="1",
                max_characters=80,
                max_lines=2,
                break_strategy="sentence",
            ),
            alignment_provider=request.provider_kind,
            alignment_model=request.model_id,
            alignment_receipt_id=f"alignment-{result.alignment_receipt_sha256}",
            style_reference_id=style.artifact_id,
        )
        caption = CaptionImportRequest.create(
            caption_track=track,
            style_reference=style,
            style_bytes=style_bytes,
        ).prepare()
        caption_record = AssetRecord(
            asset_id=f"caption-{request.attempt_id}",
            asset_type=AssetType.CAPTION,
            artifact_path=Path(f"assets/captions/{caption.track_sha256}.json"),
            sha256=caption.track_sha256,
            size_bytes=len(caption.track_bytes),
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
                segment_count=len(track.segments),
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
        return PreparedVoiceCandidate(
            audio=PreparedAudioImport(
                payload=result.audio_bytes,
                probe=probe,
                asset_record=audio_record,
            ),
            caption=caption,
            caption_asset_record=caption_record,
        )

    return prepare
