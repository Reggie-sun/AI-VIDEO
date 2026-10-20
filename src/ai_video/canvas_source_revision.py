"""Reviewable current-input revisions above the verbatim source compiler.

The director supplies complete current sections and dispositions, not an edit
instruction for a model. Old input stays in immutable authoring provenance.
This validates declared replacement and exact bytes, not semantic equivalence.
"""
from collections import Counter
from typing import Literal

from pydantic import Field, field_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256


class CurrentSourceSection(StrictModel):
    section_id: str = Field(pattern=r"^[A-Za-z0-9._-]{1,128}$")
    parts: tuple[dict, ...] = Field(min_length=1)


class SourcePartDisposition(StrictModel):
    part_index: int = Field(ge=0, strict=True)
    part_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    disposition: Literal["retained", "superseded"]
    reason: str = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def _reason(cls, value):
        if not value.strip():
            raise ValueError("source revision requires a reason")
        return value


class CanvasSourceRevision(StrictModel):
    contract_version: Literal["canvas-source-revision/1"] = "canvas-source-revision/1"
    baseline_source_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_prompt_parts_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_effective_prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reason: str = Field(min_length=1)
    sections: tuple[CurrentSourceSection, ...] = Field(min_length=1)
    dispositions: tuple[SourcePartDisposition, ...] = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def _reason(cls, value):
        if not value.strip():
            raise ValueError("source revision requires a reason")
        return value


def _previous_director(previous, *, required=True):
    from ai_video.production.authoring_input import PREFIX, reopen_authoring_input

    source = next((s for s in previous.project.source_provenance
                   if s.reference == "canvas-director-data"), None)
    reference = next((s for s in previous.project.source_provenance
        if source is not None and s.reference.startswith(PREFIX)
        and s.content_hash == source.content_hash), None)
    if reference is None:
        if not required:
            return None
        raise ValueError("source revision requires canonical baseline director input")
    return reopen_authoring_input(previous.root, reference)


def _prompt_parts(unit):
    parts = unit["prompt_source"].get("parts")
    if parts is not None:
        return parts
    # Observed Canvas packets retain prose rather than structured draft parts.
    text = unit["prompt_source"].get("prompt", unit["source_text"])
    if not isinstance(text, str) or text != unit["source_text"]:
        raise ValueError("source revision observed prompt differs from inspected source text")
    return [{"type": "text", "text": text}]


def _effective_prompt(row):
    result = {"intent": row["shot"]["intent"],
        "preserved_source_expression": row["shot"].get("preserved_source_expression")}
    intent = row.get("generation", {}).get("generation_intent")
    if result["preserved_source_expression"] is None and intent is not None:
        from ai_video.production.video_requirement import GenerationIntent
        result["generation_intent"] = GenerationIntent.model_validate(intent).model_dump(mode="json")
    return result


def effective_prompt_sha256(row):
    """Hash the approved prose/compiler route and typed legacy prompt controls."""
    return canonical_sha256(_effective_prompt(row))


def _contains_text(value, text):
    if isinstance(value, str):
        return text in value
    if isinstance(value, dict):
        return any(_contains_text(item, text) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_text(item, text) for item in value)
    return False


def retained_source_revision(*, previous, packet, row, reason):
    """Declare an explicit mechanical handoff while retaining inspected source."""
    baseline = _previous_director(previous)
    old_row = next(r for r in baseline["direction"]["shots"]
        if r["shot"]["shot_id"] == row["shot"]["shot_id"])
    old_unit = next(u for u in baseline["packet"]["units"]
        if u["occurrence_id"] == old_row["occurrence_id"])
    unit = next(u for u in packet["units"] if u["occurrence_id"] == row["occurrence_id"])
    parts = _prompt_parts(unit)
    if parts != _prompt_parts(old_unit) or unit["source_text"] != old_unit["source_text"]:
        raise ValueError("source revision handoff must retain the inspected source")
    return CanvasSourceRevision(
        baseline_source_snapshot_sha256=baseline["packet"]["source_snapshot_sha256"],
        baseline_prompt_parts_sha256=canonical_sha256({"parts": parts}),
        baseline_effective_prompt_sha256=effective_prompt_sha256(old_row), reason=reason,
        sections=(CurrentSourceSection(section_id="retained-source", parts=parts),),
        dispositions=tuple(SourcePartDisposition(part_index=index,
            part_sha256=canonical_sha256(part), disposition="retained", reason=reason)
            for index, part in enumerate(parts))).model_dump(mode="json")


def require_canvas_source_revision(*, packet, unit, row, previous=None):
    """Validate an explicit current draft against the reopened approved baseline."""
    data = row.get("source_revision")
    current = _prompt_parts(unit)
    if data is None and previous is None:
        return
    baseline = None if previous is None else _previous_director(previous,
        required=data is not None or row.get("visual_style") is not None)
    old_row = None if baseline is None else next((r for r in baseline["direction"]["shots"]
        if r["shot"]["shot_id"] == row["shot"]["shot_id"]), None)
    old_unit = None if old_row is None else next((u for u in baseline["packet"]["units"]
        if u["occurrence_id"] == old_row["occurrence_id"]), None)
    old_parts = None if old_unit is None else _prompt_parts(old_unit)
    changed = old_unit is not None and (old_parts != current
        or old_unit["source_text"] != unit["source_text"]
        or _effective_prompt(old_row) != _effective_prompt(row))
    if old_row is not None:
        if old_row.get("visual_style") is not None and row.get("visual_style") is None:
            raise ValueError("source revision cannot discard the approved visual-style declaration")
        if old_row.get("source_revision") is not None and data is None:
            raise ValueError("source revision declaration cannot be discarded")
    if data is None:
        if changed:
            raise ValueError("source revision required for a changed prompt input")
        return
    try:
        revision = CanvasSourceRevision.model_validate(data)
    except ValueError as error:
        raise ValueError("source revision declaration is invalid") from error
    ids = [section.section_id for section in revision.sections]
    declared = [part for section in revision.sections for part in section.parts]
    if len(set(ids)) != len(ids) or declared != current:
        raise ValueError("source revision current sections differ from inspected prompt parts")
    # Exact re-authoring of already approved input must remain idempotent. Its
    # original baseline is retained by the canonical authoring-input artifacts.
    if (old_row is not None and old_row.get("source_revision") == data
            and old_unit is not None and not changed):
        return
    if (old_unit is None or baseline["packet"]["source_snapshot_sha256"]
            != revision.baseline_source_snapshot_sha256):
        raise ValueError("source revision baseline snapshot is not the approved input")
    if canonical_sha256({"parts": old_parts}) != revision.baseline_prompt_parts_sha256:
        raise ValueError("source revision baseline parts changed")
    if effective_prompt_sha256(old_row) != revision.baseline_effective_prompt_sha256:
        raise ValueError("source revision baseline effective prompt changed")
    indices = [decision.part_index for decision in revision.dispositions]
    if sorted(indices) != list(range(len(old_parts))):
        raise ValueError("source revision must account for each baseline part exactly once")
    retained = Counter()
    current_counts = Counter(canonical_sha256(part) for part in current)
    current_text = "".join(part["text"] for part in current if part.get("type") == "text")
    effective_text = {"intent": row["shot"]["intent"],
        "generation_intent": _effective_prompt(row).get("generation_intent")}
    for decision in revision.dispositions:
        part = old_parts[decision.part_index]
        if canonical_sha256(part) != decision.part_sha256:
            raise ValueError("source revision baseline part identity changed")
        if decision.disposition == "retained":
            retained[decision.part_sha256] += 1
        elif (part.get("type") == "text" and part["text"].strip()
              and (part["text"] in current_text or _contains_text(effective_text, part["text"]))) \
                or current_counts[decision.part_sha256]:
            raise ValueError("source revision superseded history remains in the current input")
    if any(current_counts[digest] < count for digest, count in retained.items()):
        raise ValueError("source revision removed a retained baseline part")
