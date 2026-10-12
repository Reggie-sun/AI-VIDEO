import pytest

from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.grok_profile import grok_capabilities


def output(**changes):
    return VideoFlexibleOutputRequirement(timing_mode="nominal_seconds", duration_seconds=4,
        dimension_mode="adaptive", width=None, height=None, resolution_label="720p",
        ratio="adaptive", fps=None, container="mp4", mime_type="video/mp4",
        native_audio=False, **changes)


def test_unknown_fps_is_explicit_and_does_not_claim_exact_frame_count():
    value = output()
    assert all(v.output_capability.supports(value) for v in grok_capabilities().variants)
    assert value.matches_timing_measurement(duration_milliseconds=4000, frame_count=120)
    assert value.matches_timing_measurement(duration_milliseconds=4000, frame_count=96)
    assert not value.matches_timing_measurement(duration_milliseconds=5000, frame_count=120)


def test_frame_count_cannot_be_declared_without_fps():
    with pytest.raises(ValueError):
        VideoFlexibleOutputRequirement(timing_mode="frame_count", frame_count=120,
            dimension_mode="adaptive", width=None, height=None, fps=None, container="mp4",
            mime_type="video/mp4", native_audio=False)
