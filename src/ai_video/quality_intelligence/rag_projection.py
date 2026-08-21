"""Pure, deterministic advisory projection for future curated RAG use."""

from __future__ import annotations

from ai_video.quality_intelligence.models import PilotDatasetIndexV1
from ai_video.quality_intelligence.store import (
    QualityExperienceIntegrityError,
    _seal_content_model,
)


def render_rag_projection(index: PilotDatasetIndexV1) -> bytes:
    """Return sanitized Markdown bytes without writing or searching any index."""

    try:
        checked = PilotDatasetIndexV1.model_validate(index.model_dump(mode="json"))
    except Exception:
        raise QualityExperienceIntegrityError("projection input is invalid") from None
    if checked.content_hash is None:
        raise QualityExperienceIntegrityError("projection requires a sealed dataset")
    sealed, _, _ = _seal_content_model(checked)
    if checked.content_hash != sealed.content_hash:
        raise QualityExperienceIntegrityError("projection dataset seal is invalid")
    lines = [
        "# Quality Experience Dataset Projection",
        "",
        "authority = advisory_experience",
        "evidence_boundary = exact_typed_projection_only",
        f"pilot_id = {checked.pilot_id}",
        f"dataset_content_hash = {checked.content_hash}",
        f"cohort_file_sha256 = {checked.cohort.file_sha256}",
        f"roster_file_sha256 = {checked.roster.file_sha256}",
        f"rubric_id = {checked.rubric_id}",
        f"rubric_version = {checked.rubric_version}",
        f"capture_contract_version = {checked.capture_contract_version}",
        "",
        "## Exact records",
        "",
    ]
    for entry in checked.entries:
        lines.extend(
            (
                f"- record_file_sha256 = {entry.record.file_sha256}",
                f"  record_content_hash = {entry.record.content_hash}",
                f"  project = {entry.project_id}",
                f"  scene = {entry.scene_id}",
                f"  shot = {entry.shot_id}",
                f"  attempt = {entry.attempt_id}",
                f"  generation = {entry.generation_id}",
                f"  provider = {entry.provider_name}",
                f"  profile = {entry.profile_id}",
                f"  capability = {entry.capability_id}",
                f"  model = {entry.model_id}",
                f"  outcome = {entry.outcome}",
                f"  human_verdict = {entry.human_verdict.value}",
                f"  coverage = {','.join(entry.coverage_tags)}",
            )
        )
    lines.extend(
        (
            "",
            "This projection is advisory only. It does not establish QA, acceptance, "
            "training readiness, Provider selection, or repair authority.",
            "",
        )
    )
    return "\n".join(lines).encode("utf-8")
