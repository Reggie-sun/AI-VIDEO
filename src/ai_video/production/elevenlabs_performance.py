"""Deterministic ElevenLabs input compilation, never transcript or timing repair.

Tags are sealed synthesis controls, not spoken dialogue. Alignment still must
match the original script exactly; that check does not establish tag silence.
"""
from __future__ import annotations

import unicodedata
import hashlib

from ai_video.errors import AiVideoError, ErrorCode


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


def project_synthesis_alignment(
    script_text: str, audio_tags: tuple[str, ...],
    alignment: dict[str, object], normalized_alignment: dict[str, object],
) -> dict[str, object]:
    """Project only an exact compiled prefix from already-validated arrays.

    This preserves provider timestamps and raw evidence. It is not evidence that
    control text was silent; listening acceptance remains a separate boundary.
    """
    try:
        validate_audio_tags(audio_tags)
    except ValueError:
        raise AiVideoError(ErrorCode.VOICE_PROVIDER_FAILED,
            "ElevenLabs synthesis controls are invalid.", retryable=False) from None
    receipt = {"alignment": alignment, "normalized_alignment": normalized_alignment}
    if not audio_tags:
        return receipt
    synthesis = compile_synthesis_text(script_text, audio_tags)
    prefix = synthesis[:-len(script_text)] if script_text else ""
    if not prefix:
        raise AiVideoError(ErrorCode.VOICE_PROVIDER_FAILED,
            "An exact nonempty synthesis prefix is required.", retryable=False)
    mapped = False
    for name, raw in tuple(receipt.items()):
        characters = raw["characters"]
        if "".join(characters) != synthesis:
            continue
        offset = 0
        boundary = None
        for index, character in enumerate(characters):
            offset += len(character)
            if offset == len(prefix):
                boundary = index + 1
                break
            if offset > len(prefix):
                break
        if boundary is None or "".join(characters[boundary:]) != script_text:
            raise AiVideoError(ErrorCode.VOICE_PROVIDER_FAILED,
                "ElevenLabs synthesis prefix does not end at an alignment boundary.",
                retryable=False)
        receipt[name] = {key: values[boundary:] for key, values in raw.items()}
        mapped = True
    if mapped:
        receipt["synthesis_alignment"] = {
            "mapping_kind": "sealed-prefix-projection/1",
            "prefix": prefix,
            "synthesis_text_sha256": hashlib.sha256(synthesis.encode("utf-8")).hexdigest(),
            "raw_alignment": alignment,
            "raw_normalized_alignment": normalized_alignment,
        }
    return receipt
