"""Review-owned raw generation observations, before acceptance or activation.

The evaluator supplies this document. Projection preserves its bytes identity;
the decision caller cannot substitute findings or invent an evaluator receipt.
"""

from __future__ import annotations

from typing import Literal
import json
from dataclasses import dataclass
from weakref import WeakKeyDictionary

from pydantic import Field, model_serializer, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.generation_diagnosis import Finding
from ai_video.production.generation_recipe import Proof, SHA256
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ToolIdentity


class GenerationObservation(StrictModel):
    requirement_id: str = Field(min_length=1)
    verdict: Literal["PASS", "FAIL", "NOT_EVALUATED"]
    observation: str = Field(min_length=1)
    span_millis: tuple[int, int] | None = None


class GenerationAnalysisEvidence(StrictModel):
    """Original MCP response, bound to measured fetched bytes by the bridge."""

    tool_name: Literal["video_analyze"] = "video_analyze"
    artifact_sha256: str = Field(pattern=SHA256)
    size_bytes: int = Field(strict=True, gt=0)
    response_json: str = Field(min_length=1)

    @model_validator(mode="after")
    def _response(self):
        response = json.loads(self.response_json)
        if not isinstance(response, dict) or response.get("isError"):
            raise ValueError("analysis response must be a successful MCP document")
        payload = response.get("structuredContent")
        if payload is None:
            content = response.get("content")
            if not isinstance(content, list) or any(not isinstance(item, dict) for item in content):
                raise ValueError("analysis content must be MCP blocks")
            texts = [item.get("text") for item in content if item.get("type") == "text"]
            if any(not isinstance(text, str) for text in texts):
                raise ValueError("analysis text must be a JSON string")
            payload = json.loads(texts[0]) if len(texts) == 1 else None
        if (not isinstance(payload, dict) or payload.get("error")
                or not isinstance(payload.get("video_path"), str)
                or "analysis_summary" not in payload
                or not isinstance(payload.get("probe"), dict)
                or not isinstance(payload["probe"].get("file"), dict)
                or payload["probe"]["file"].get("size_bytes") != self.size_bytes):
            raise ValueError("analysis response has no exact successful video analysis")
        return self

    @property
    def response(self):
        # A fresh view; an evaluator cannot mutate the retained source bytes.
        return json.loads(self.response_json)

    @property
    def payload(self):
        response = self.response
        if response.get("structuredContent") is not None:
            return response["structuredContent"]
        return json.loads(next(item["text"] for item in response["content"] if item.get("type") == "text"))


_ANALYSIS_RECORDING_TOKEN = object()
_ANALYSIS_RECORDINGS = WeakKeyDictionary()


@dataclass(frozen=True, init=False, eq=False)
class _AnalysisRecordingProof:
    """One-use in-process bridge proof; never accepted from a JSON document."""
    attempt_id: str
    source_hashes: tuple[str, ...]

    def __init__(self, token, *, attempt_id, sources):
        if token is not _ANALYSIS_RECORDING_TOKEN:
            raise TypeError("analysis recording proof is issued by the analysis bridge")
        object.__setattr__(self, "attempt_id", attempt_id)
        object.__setattr__(self, "source_hashes", tuple(s.source_sha256 for s in sources))
        _ANALYSIS_RECORDINGS[self] = (attempt_id, self.source_hashes)

    def consume(self, *, attempt_id, sources):
        issued = _ANALYSIS_RECORDINGS.pop(self, None)
        return issued == (attempt_id, tuple(s.source_sha256 for s in sources))


def _seal_analysis_recording(*, attempt_id, sources):
    """Internal bridge handoff after MCP and evaluator identity verification."""
    return _AnalysisRecordingProof(_ANALYSIS_RECORDING_TOKEN, attempt_id=attempt_id, sources=sources)


class GenerationEvaluationSource(StrictModel):
    """A sealed evaluator document; no model-quality or human verdict is inferred."""

    schema_version: Literal["generation-evaluation/1"] = "generation-evaluation/1"
    request_hash: str = Field(pattern=SHA256)
    artifact_sha256: str = Field(pattern=SHA256)
    rubric_hash: str = Field(pattern=SHA256)
    qa_policy_content_hash: str = Field(pattern=SHA256)
    evaluator: ToolIdentity
    proof: Proof
    observations: tuple[GenerationObservation, ...] = Field(min_length=1)
    analysis_evidence: GenerationAnalysisEvidence | None = None

    @model_serializer(mode="wrap")
    def _serialize(self, handler):
        result = handler(self)
        if self.analysis_evidence is None:
            result.pop("analysis_evidence", None)
        return result

    @property
    def source_sha256(self):
        return canonical_sha256(self.model_dump(mode="json"))

    def project_findings(self) -> tuple[Finding, ...]:
        return tuple(Finding(
            **item.model_dump(mode="python"), rubric_hash=self.rubric_hash,
            stage="raw_generation", proof=self.proof,
            source_sha256=self.source_sha256,
        ) for item in self.observations)


def require_generation_evaluation_authorities(qa_policy, acceptance):
    """A required proof layer needs an explicitly configured owner before submit."""
    required = {item["proof"] for item in acceptance.profile_payload["generation_requirements"]
                if item["level"] == "acceptance" and item["stage"] == "raw_generation"}
    configured = {item.proof for item in qa_policy.generation_evaluation_authorities}
    if not required <= configured:
        raise ValueError("current QA policy has no authority for required generation proof")


def validate_generation_evaluation_sources(*, sources, evidence, qa_policy, loaded=None):
    """Reopen exact source identity and the current policy-selected authority."""
    if not sources:
        raise ValueError("media evaluation requires the original evaluator sources")
    acceptance = qa_policy.selected_generation_acceptance()
    if loaded is not None:
        from ai_video.production.production_strategy_reader import selected_shot_generation_acceptance

        if loaded.qa_policy != qa_policy:
            raise ValueError("generation evaluation QA differs from selected project policy")
        acceptance = selected_shot_generation_acceptance(loaded, evidence.shot_id)
    if acceptance is None or acceptance.profile_content_hash != evidence.rubric_hash:
        raise ValueError("generation evaluation rubric is not selected by current QA policy")
    projected = []
    for source in sources:
        source = GenerationEvaluationSource.model_validate(source.model_dump(mode="python"))
        if (source.request_hash != evidence.request_hash
                or source.artifact_sha256 != evidence.artifact_sha256
                or source.rubric_hash != evidence.rubric_hash
                or source.qa_policy_content_hash != qa_policy.content_hash):
            raise ValueError("evaluation source does not match exact media, request or current QA policy")
        if (source.analysis_evidence is not None
                and source.analysis_evidence.artifact_sha256 != source.artifact_sha256):
            raise ValueError("analysis evidence does not match exact media")
        if source.evaluator not in qa_policy.semantic_authorities:
            raise ValueError("generation evaluator is not a policy-selected authority")
        if not any(item.evaluator == source.evaluator and item.proof == source.proof
                   for item in qa_policy.generation_evaluation_authorities):
            raise ValueError("generation evaluator is not authorized for this proof kind")
        projected.extend(source.project_findings())
    if tuple(projected) != evidence.findings:
        raise ValueError("generation findings differ from original evaluator sources")
