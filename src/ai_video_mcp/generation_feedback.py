"""Explicit per-attempt MCP analysis -> selected evaluator -> durable feedback.

MCP supplies raw observations, never a human verdict. The caller injects the
selected evaluator and an initialized project-local MCP session. No Provider,
retry, activation, or implicit recovery is performed here.
"""
from __future__ import annotations

import inspect
import json
import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from ai_video.production.generation_diagnosis import diagnose_exact_result
from ai_video.production.generation_evaluation import (
    GenerationAnalysisEvidence, GenerationEvaluationSource, _seal_analysis_recording,
)
from ai_video.production.generation_feedback import record_attempt_evaluation
from ai_video.production.models import StateCommitStatus
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.project import load_production_project
from ai_video.production.video_generation import VideoGenerationService


@dataclass(frozen=True)
class GenerationReviewInput:
    request: object
    projection: object
    recipe: object
    qa_policy: object
    analysis: GenerationAnalysisEvidence


class ProjectAnalysisSession:
    """Use the installed isolated MCP runtime without adding a production SDK."""

    def __init__(self, python):
        self.python = str(Path(python).resolve(strict=True))

    async def call_tool(self, name, arguments):
        if name != "video_analyze":
            raise ValueError("generation review only calls video_analyze")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
        process = await asyncio.create_subprocess_exec(
            self.python, "-m", "ai_video_mcp.analysis_client", arguments["video_path"],
            env=env, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=300)
        except BaseException:
            if process.returncode is None:
                process.kill()
            await process.wait()
            raise
        if process.returncode:
            raise ValueError("EVIDENCE_REPAIR_FIRST: isolated MCP analysis failed")
        result = json.loads(stdout)
        return SimpleNamespace(model_dump=lambda **_: result)


def _diagnosis(committer, experience):
    entry = experience.evidence[-1]
    history = tuple(e for x in committer.read_generation_experiences() for e in x.evidence)
    return diagnose_exact_result(entry, history, experience.candidate.recipe)


async def review_generation_attempt(*, committer, attempt_id, session, adjudicate,
                                    repair_evidence=False, analysis_only=False):
    """Review one exact fetched result; exact completed replay has zero effects.

    Missing analysis/evaluator results raise before feedback persistence. The
    still-unevaluated attempt blocks further submit in the existing decision
    guard. Explicit evidence repair analyzes these same bytes, never resubmits.
    """
    attempt, state = VideoGenerationService(committer=committer, provider=None)._state(attempt_id)
    if state.execution_binding is None:
        raise ValueError("review requires a durable generation decision")
    if attempt.status is StateCommitStatus.FAILED and state.quality_rejection is not None:
        if repair_evidence or analysis_only:
            raise ValueError("closed quality rejection cannot be reanalyzed or repaired")
        return _diagnosis(committer, record_attempt_evaluation(
            committer=committer, attempt_id=attempt_id))
    if attempt.status in {StateCommitStatus.FAILED, StateCommitStatus.OUTCOME_UNKNOWN}:
        if analysis_only:
            raise ValueError("runtime outcome requires explicit resolution before media analysis")
        return _diagnosis(committer, record_attempt_evaluation(
            committer=committer, attempt_id=attempt_id))
    binding = committer._reopen_generation_execution_binding(state.execution_binding)
    request = committer._reopen_video_request(state.request)
    pointer = state.local_fetch_receipt or state.fetch_receipt
    if pointer is None:
        raise ValueError("review requires fetched media; no analysis or new submit is allowed")
    loaded = load_production_project(committer.project_root / "project.yaml")
    if loaded.qa_policy is None:
        raise ValueError("review requires a current QA policy")
    # Reopen receipt and physically remeasure bytes even on an exact replay.
    receipt = (committer._reopen_local_video_fetch(pointer) if state.local_fetch_receipt
               else committer._reopen_video_fetch(pointer))
    path = committer.project_root / pointer.artifact_path

    def measure():
        raw = _read_regular_file_nofollow(path, contained_by=committer.project_root)
        if (raw.file_sha256 != receipt.artifact_sha256
                or len(raw.data) != receipt.size_bytes):
            raise ValueError("fetched media changed before or during evaluation")
        return raw

    measure()
    existing = [x for x in committer.read_generation_experiences()
                if any(e.attempt_id == attempt_id and e.outcome == "media" for e in x.evidence)]
    if existing and not repair_evidence and not analysis_only:
        current = existing[-1]
        if (all(s.qa_policy_content_hash == loaded.qa_policy.content_hash
                for s in current.evaluation_sources)
                and any(s.analysis_evidence is not None for s in current.evaluation_sources)):
            return _diagnosis(committer, current)
    if session is None or (adjudicate is None and not analysis_only):
        raise ValueError("EVIDENCE_REPAIR_FIRST: project-local MCP and selected evaluator are required")
    result = await session.call_tool("video_analyze", {
        "video_path": str(path), "extract_frames": True,
        "transcribe_audio": False, "detect_scenes": True,
    })
    response = result.model_dump(mode="json")
    analysis = GenerationAnalysisEvidence(artifact_sha256=receipt.artifact_sha256,
        size_bytes=receipt.size_bytes, response_json=json.dumps(response, sort_keys=True, separators=(",", ":")))
    if analysis.payload["video_path"] != str(path):
        raise ValueError("EVIDENCE_REPAIR_FIRST: analysis identifies different media")
    measure()
    candidate = next(c for c in binding.inputs.candidates
                     if c.candidate_id == binding.decision.selected_candidate_id)
    review_input = GenerationReviewInput(request, binding.projection, candidate.recipe,
                                        loaded.qa_policy, analysis)
    if analysis_only:
        return review_input
    sources = adjudicate(review_input)
    if inspect.isawaitable(sources):
        sources = await sources
    documents = []
    for source in sources:
        source = GenerationEvaluationSource.model_validate(source.model_dump(mode="python"))
        if source.analysis_evidence != analysis:
            raise ValueError("evaluator must explicitly bind the exact analysis evidence")
        documents.append(source)
    measure()
    experience = record_attempt_evaluation(committer=committer, attempt_id=attempt_id,
        evaluation_sources=tuple(documents),
        analysis_proof=_seal_analysis_recording(attempt_id=attempt_id, sources=tuple(documents)))
    return _diagnosis(committer, experience)
