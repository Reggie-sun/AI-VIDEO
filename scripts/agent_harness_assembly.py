"""Read-only assembly evidence entry; the existing junction Gate owns verdicts.

No decoder, generation, timeline derivation or Product state mutation. This
checks an existing renderer's exact output binding and explicit observations;
it cannot establish whether a declared human playback actually happened.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import Field

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.junction_review import (
    JunctionFinding, derive_junction_inventory, evaluate_junction_review,
    junction_inventory_sha256, validate_timeline_and_report,
)
from ai_video.production.models import EvidenceStrength


class AssemblyReviewAnswers(StrictModel):
    schema_version: Literal["assembly-review/1"] = "assembly-review/1"
    authority: Literal["development_only"] = "development_only"
    video_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    timeline_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    render_report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluator_name: str = Field(min_length=1)
    strength: EvidenceStrength
    junction_findings: tuple[JunctionFinding, ...] = ()


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _video_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _current(*, video: Path, timeline: Path, render_report: Path):
    video = video.resolve(strict=True)
    video_sha = _video_hash(video)
    timeline_bytes, report_bytes = timeline.read_bytes(), render_report.read_bytes()
    resolved, _ = validate_timeline_and_report(timeline_bytes, report_bytes,
        video_path=video, video_sha256=video_sha, video_size_bytes=video.stat().st_size)
    cuts = derive_junction_inventory(resolved)
    identity = dict(video_sha256=video_sha, timeline_sha256=_hash(timeline_bytes),
        render_report_sha256=_hash(report_bytes), inventory_sha256=junction_inventory_sha256(cuts))
    return identity, cuts


def prepare_assembly(*, video: Path, timeline: Path, render_report: Path) -> dict:
    identity, cuts = _current(video=video, timeline=timeline, render_report=render_report)
    action_instructions = {
        "repetition": "检查前后完整动作是否重复；对有意复现记录叙事理由。",
        "state_continuity": "检查动作阶段、人物视线、持物与接触支撑是否合理衔接。",
        "pacing": "检查动作速度、重复停顿、响应时机及切镜节奏。",
    }
    findings = tuple(JunctionFinding(
        junction_id=cut.junction_id, inventory_sha256=identity["inventory_sha256"],
        edit_decision=None, edit_reason="待审看后决定修剪或说明保留理由",
        visual_verdict="not_evaluated", visual_observation="待正常速度观看前后完整行动与反应",
        audio_verdict="not_evaluated", audio_observation="待实际聆听接点是否重复、截断或跳变",
        audio_basis="not_listened", action_review={key: dict(verdict="not_evaluated", observation=value)
            for key, value in action_instructions.items()}) for cut in cuts)
    return AssemblyReviewAnswers(**identity, evaluator_name="pending",
        strength=EvidenceStrength.EXPLICIT_EVALUATOR, junction_findings=findings).model_dump(mode="json")


def verify_assembly(*, video: Path, timeline: Path, render_report: Path,
                    answers: Path | None = None) -> dict:
    paths = dict(video=video, timeline=timeline, render_report=render_report)
    identity, cuts = _current(**paths)
    if answers is None:
        strength, findings = EvidenceStrength.EXPLICIT_EVALUATOR, ()
        answers_sha, evaluator = None, None
    else:
        answer_bytes = answers.read_bytes()
        answers_sha = _hash(answer_bytes)
        review = AssemblyReviewAnswers.model_validate_json(answer_bytes)
        if any(getattr(review, key) != value for key, value in identity.items()):
            raise ValueError("Assembly observations do not bind the current exact output")
        strength, findings = review.strength, review.junction_findings
        evaluator = review.evaluator_name
    result = evaluate_junction_review(cuts, findings,
        inventory_sha256=identity["inventory_sha256"], strength=strength, require_action_review=True)
    # Reopen current bytes again; a concurrent export cannot inherit an old result.
    if _current(**paths)[0] != identity:
        raise ValueError("Assembly inputs changed during verification")
    if answers is not None and _hash(answers.read_bytes()) != answers_sha:
        raise ValueError("Assembly observations changed during verification")
    verdict = result.verdict
    if answers is None and not cuts:
        verdict = "not_evaluated"
    return dict(authority="development_only", purpose="assembly_review_evidence",
        verdict=verdict, production_acceptance="NOT_EVALUATED", **identity,
        answers_sha256=answers_sha, evaluator_name=evaluator, strength=strength.value,
        junction_review=result.model_dump(mode="json"),
        limitation="Validates exact bindings and declared evidence, not semantic detection or human acceptance")
