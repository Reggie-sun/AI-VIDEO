"""Reopen Grok's requested resolution and inherited source output contract."""

from ai_video.production.video import VideoGenerationMode


_PURE_I2V_CAPABILITIES = frozenset({
    "grok-imagine-video-1.5-i2v-v1",
    "grok-imagine-video-1.5-i2v-last-frame-v1",
    "grok-imagine-video-1.5-lite-i2v-v1",
    "grok-imagine-video-classic-i2v-v1",
})


def matches_grok_video_measurement(request, measured) -> bool:
    if request.provider_kind != "grok":
        return True
    output = request.effective_output
    if output.resolution_label in {"480p", "720p", "1080p"}:
        if min(measured.width, measured.height) != int(output.resolution_label[:-1]):
            return False
    if request.mode in {VideoGenerationMode.VIDEO_EDIT, VideoGenerationMode.VIDEO_EXTEND}:
        if len(request.media_bindings) != 1:
            return False
        source = request.media_bindings[0]
        if (source.kind != "video" or source.role != "reference_video"
                or (measured.width, measured.height) != (source.width, source.height)):
            return False
        expected_duration = (source.duration_millis if request.mode is VideoGenerationMode.VIDEO_EDIT
            else output.duration_seconds * 1000 if output.duration_seconds is not None else None)
        return measured.duration_milliseconds == expected_duration
    if request.capability_id in _PURE_I2V_CAPABILITIES:
        first = tuple(b for b in request.image_bindings if b.role == "first_frame")
        return (len(first) == 1
            and measured.width * first[0].height == measured.height * first[0].width)
    return True
