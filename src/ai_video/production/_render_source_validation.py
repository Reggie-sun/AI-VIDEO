"""Validate resolved P4 tracks against the sealed renderer source bundle."""
from ai_video.production.audio_retime_contracts import native_audio_mapping_sha256
from ai_video.production.models import RendererSourceReceipt, ResolvedTimeline


def _validate_source_timeline_bindings(
    source: RendererSourceReceipt, timeline: ResolvedTimeline
) -> None:
    expected_track_ids = tuple(item.track_id for item in timeline.audio_spans)
    if expected_track_ids:
        if len(source.audio_bindings) != 1:
            raise ValueError(
                "P4 render source requires exactly one mixed audio binding"
            )
        audio = source.audio_bindings[0]
        if (
            audio.asset_mime_type != "audio/wav"
            or audio.sample_rate_hz != timeline.sample_rate
            or audio.channels != 2
            or audio.duration_samples != timeline.total_samples
            or audio.resolved_track_ids != expected_track_ids
        ):
            raise ValueError(
                "P4 mixed audio binding does not match the resolved timeline"
            )
        native_spans = tuple(
            item for item in timeline.audio_spans if item.native_audio_retime is not None
        )
        proofs = audio.native_audio_derivations
        if {item.track_id for item in proofs} != {
            item.track_id for item in native_spans
        } or len(proofs) != len(native_spans):
            raise ValueError(
                "native audio derivation proofs do not match resolved native tracks"
            )
        proofs_by_track = {item.track_id: item for item in proofs}
        correction_limit = (
            timeline.sample_rate + timeline.delivery_profile.fps - 1
        ) // timeline.delivery_profile.fps
        for span in native_spans:
            mapping = span.native_audio_retime
            assert mapping is not None
            visual_matches = tuple(
                item
                for item in timeline.visual_spans
                if item.layer_id == mapping.visual_layer_id
            )
            proof = proofs_by_track[span.track_id]
            raw_visual_matches = tuple(
                item
                for item in source.asset_bindings
                if item.asset_id == span.asset_id
            )
            if (
                span.audio_kind.value != "native_video"
                or len(visual_matches) != 1
                or visual_matches[0].asset_id != span.asset_id
                or visual_matches[0].asset_sha256 != span.asset_sha256
                or visual_matches[0].asset_mime_type != "video/mp4"
                or len(raw_visual_matches) != 1
                or raw_visual_matches[0].asset_sha256 != span.asset_sha256
                or raw_visual_matches[0].asset_mime_type != "video/mp4"
                or proof.source_video_asset_id != span.asset_id
                or proof.source_video_sha256 != span.asset_sha256
                or proof.stream_index != mapping.stream_index
                or proof.sample_rate_hz != timeline.sample_rate
                or proof.mapping_sha256 != native_audio_mapping_sha256(mapping)
                or tuple(item.segment for item in proof.segment_results)
                != mapping.segments
                or proof.input_samples
                != max(
                    item.source_start_sample + item.source_duration_samples
                    for item in mapping.segments
                )
                or proof.mapped_samples != span.duration_samples
                or any(
                    max(item.padded_samples, item.trimmed_samples)
                    > correction_limit
                    for item in proof.segment_results
                )
            ):
                raise ValueError(
                    "native audio proof does not match its resolved map and video source"
                )
    elif source.audio_bindings:
        raise ValueError("silent timeline cannot declare a renderer audio binding")

    expected_caption_tracks = {item.caption_track_id for item in timeline.caption_cues}
    actual_caption_tracks = tuple(
        item.caption_track_id for item in source.caption_bindings
    )
    if len(actual_caption_tracks) != len(set(actual_caption_tracks)):
        raise ValueError("renderer caption track bindings must be unique")
    if set(actual_caption_tracks) != expected_caption_tracks:
        raise ValueError("renderer caption bindings do not match the resolved timeline")
    for binding in source.caption_bindings:
        cues = tuple(
            item
            for item in timeline.caption_cues
            if item.caption_track_id == binding.caption_track_id
        )
        style_identities = {
            (item.style_reference_id, item.style_content_hash) for item in cues
        }
        if (
            not cues
            or {item.caption_asset_sha256 for item in cues}
            != {binding.caption_asset_sha256}
            or binding.resolved_cue_ids != tuple(item.segment_id for item in cues)
            or style_identities
            != {(binding.style_reference_id, binding.style_content_hash)}
        ):
            raise ValueError("renderer caption binding does not match resolved cues")
    if (
        timeline.audio_spans or timeline.caption_cues
    ) and source.schema_version != "2.1":
        raise ValueError("P4 timeline requires RendererSourceReceipt 2.1")
