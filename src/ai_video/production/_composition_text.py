"""The composition owner's only projection of source word times to final frames."""
from __future__ import annotations

from ai_video.production.composition_contracts import ResolvedCaptionWord


def resolve_caption_words(segment, *, audio_start: int, source_start: int, sample_rate: int, fps: int):
    if segment.words is None:
        return None
    result = []
    for word in segment.words:
        start = audio_start + word.start_sample - source_start
        end = audio_start + word.end_sample - source_start
        result.append(ResolvedCaptionWord(
            text=word.text, start_sample=start, end_sample=end,
            start_frame=(start * fps + sample_rate - 1) // sample_rate,
            end_frame_exclusive=(end * fps + sample_rate - 1) // sample_rate,
        ))
    return tuple(result)
