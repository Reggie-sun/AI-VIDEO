"""Deterministic ElevenLabs input compilation, never transcript or timing repair.

Tags are sealed synthesis controls, not spoken dialogue. Alignment still must
match the original script exactly; that check does not establish tag silence.
"""
from __future__ import annotations

import unicodedata


def validate_audio_tags(tags: tuple[str, ...]) -> tuple[str, ...]:
    if len(tags) > 3:
        raise ValueError("At most three audio tags are supported")
    for tag in tags:
        if (not tag or tag != tag.strip() or len(tag) > 120
                or unicodedata.normalize("NFC", tag) != tag
                or any(c in "[]" or unicodedata.category(c).startswith("C") for c in tag)):
            raise ValueError("Audio tags must be bounded NFC text without brackets or controls")
    return tags


def compile_synthesis_text(script_text: str, audio_tags: tuple[str, ...]) -> str:
    """Preserve the exact legacy wire text when no controls are selected."""
    if not audio_tags:
        return script_text
    return " ".join(f"[{tag}]" for tag in audio_tags) + " " + script_text
