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
from uuid import uuid4

from ai_video.production.generation_diagnosis import diagnose_exact_result
from ai_video.production.generation_evaluation import (
    GenerationAnalysisEvidence, GenerationEvaluationSource, _seal_analysis_recording,
    _seal_presentation_recording, project_generation_evaluation_sources,
)
from ai_video.production.generation_evaluation_criteria import evaluation_items, PresentationEvidence
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
    evaluation_items: tuple = ()
    interaction_ref: str | None = None
    presentation_ref: str | None = None
    answer_ref: str | None = None


@dataclass(frozen=True)
class VerifiedEvaluationBinding:
    sources: tuple
    recording_proof: object


class ControlledPresentationVerifier:
    """A registered analyzer/technical callable receives the actual canonical items.

    The host registers its evaluator identity and invokes that callable here;
    returned JSON cannot claim a prior presentation. Human viewing needs a
    different trusted host integration and is deliberately unsupported.
    """

    def __init__(self, *, evaluator, proof, adjudicate):
        if proof not in {"technical", "analyzer"}:
            raise ValueError("EVIDENCE_GAP: no human presentation host integration")
        self.evaluator, self.proof, self.adjudicate = evaluator, proof, adjudicate

    async def present_and_verify(self, *, review_input, attempt_id):
        from dataclasses import replace

        if not any(a.evaluator == self.evaluator and a.proof == self.proof
                   for a in review_input.qa_policy.generation_evaluation_authorities):
            raise ValueError("presentation evaluator is not selected by QA")
        interaction = uuid4().hex
        presented = replace(review_input,
            evaluation_items=tuple(i for i in review_input.evaluation_items if i.proof == self.proof),
            interaction_ref=interaction, presentation_ref=f"{interaction}/request", answer_ref=f"{interaction}/response")
        # These are the actual immutable request items, fixed before the call.
        answers = self.adjudicate(presented)
        if inspect.isawaitable(answers):
            answers = await answers
        documents = []
        for source in answers:
            source = GenerationEvaluationSource.model_validate(source.model_dump(mode="python"))
            if (source.evaluator != self.evaluator or source.proof != self.proof
                    or source.presentation_evidence is not None
                    or source.analysis_evidence != review_input.analysis):
                raise ValueError("controlled response cannot supply another actor or a prior presentation")
            captured = PresentationEvidence(namespace="controlled-evaluator/1", interaction_ref=interaction,
                presentation_ref=presented.presentation_ref, answer_ref=presented.answer_ref,
                event_order=("presentation", "answer"), actor_name=self.evaluator.name,
                actor_version=self.evaluator.version, items=presented.evaluation_items,
                answers_json=json.dumps(source.answer_payload(), sort_keys=True, separators=(",", ":")))
            bound = source.model_copy(update={"presentation_evidence": captured})
            project_generation_evaluation_sources(sources=(bound,), acceptance=review_input.recipe.acceptance_policy)
            documents.append(bound)
        sources = tuple(documents)
        if not sources:
            raise ValueError("EVIDENCE_GAP: evaluator returned no answer evidence")
        return VerifiedEvaluationBinding(sources, _seal_presentation_recording(attempt_id=attempt_id, sources=sources))


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
                                    repair_evidence=False, analysis_only=False, presentation_verifier=None):
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
    if session is None or (adjudicate is None and presentation_verifier is None and not analysis_only):
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
    items = evaluation_items(acceptance=candidate.recipe.acceptance_policy,
        qa_policy_content_hash=loaded.qa_policy.content_hash, request_hash=request.request_input_hash,
        artifact_sha256=receipt.artifact_sha256, size_bytes=receipt.size_bytes)
    review_input = GenerationReviewInput(request, binding.projection, candidate.recipe,
                                        loaded.qa_policy, analysis, items)
    if analysis_only:
        return review_input
    presentation_proof = None
    if candidate.recipe.acceptance_policy.profile_payload.get("requirement_semantics_version"):
        if presentation_verifier is None:
            raise ValueError("EVIDENCE_GAP: marked QA requires a trusted presentation verifier")
        verified = await presentation_verifier.present_and_verify(review_input=review_input, attempt_id=attempt_id)
        if not isinstance(verified, VerifiedEvaluationBinding):
            raise ValueError("presentation verifier must return exact bound sources and recording proof")
        sources, presentation_proof = verified.sources, verified.recording_proof
    else:
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
        analysis_proof=_seal_analysis_recording(attempt_id=attempt_id, sources=tuple(documents)),
        presentation_proof=presentation_proof)
    return _diagnosis(committer, experience)
