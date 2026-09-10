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
from ai_video.production.models import ToolIdentity, QaPolicy
from ai_video.production.generation_evaluation_criteria import (
    PresentationEvidence, TemporalMeasurement, evaluation_items, temporal_verdict,
    require_canonical_observation_basis,
)
from ai_video.production.requirement_semantics import validate_semantic_inventory


class GenerationObservation(StrictModel):
    requirement_id: str = Field(min_length=1)
    verdict: Literal["PASS", "FAIL", "NOT_EVALUATED"]
    observation: str = Field(min_length=1)
    span_millis: tuple[int, int] | None = None
    evaluation_item_hash: str | None = Field(default=None, pattern=SHA256)
    question_text: str | None = None
    presentation_ref: str | None = None
    answer_ref: str | None = None
    measurement_result: TemporalMeasurement | None = None

    @model_serializer(mode="wrap")
    def _legacy_fields(self, handler):
        data = handler(self)
        for name in ("evaluation_item_hash", "question_text", "presentation_ref", "answer_ref", "measurement_result"):
            if getattr(self, name) is None:
                data.pop(name, None)
        return data


class AdvisoryObservation(StrictModel):
    requirement_id: str = Field(min_length=1)
    observation: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)


class UnresolvedQualityObservation(StrictModel):
    observation_id: str = Field(min_length=1)
    original_answer: str = Field(min_length=1)
    visible_problem: str = Field(min_length=1)
    quality_basis: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    answer_ref: str = Field(min_length=1)


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


_PRESENTATION_TOKEN = object()
_PRESENTATION_RECORDINGS = WeakKeyDictionary()


@dataclass(frozen=True, init=False, eq=False)
class _PresentationRecordingProof:
    """Separate one-use proof of a verifier-controlled presentation/answer call."""

    def __init__(self, token, *, attempt_id, sources):
        if token is not _PRESENTATION_TOKEN:
            raise TypeError("presentation proof requires the review host verifier")
        _PRESENTATION_RECORDINGS[self] = (attempt_id, tuple(s.source_sha256 for s in sources))

    def consume(self, *, attempt_id, sources):
        return _PRESENTATION_RECORDINGS.pop(self, None) == (attempt_id, tuple(s.source_sha256 for s in sources))


def _seal_presentation_recording(*, attempt_id, sources):
    return _PresentationRecordingProof(_PRESENTATION_TOKEN, attempt_id=attempt_id, sources=sources)


class GenerationEvaluationSource(StrictModel):
    """A sealed evaluator document; no model-quality or human verdict is inferred."""

    schema_version: Literal["generation-evaluation/1", "generation-evaluation/2"] = "generation-evaluation/1"
    request_hash: str = Field(pattern=SHA256)
    artifact_sha256: str = Field(pattern=SHA256)
    rubric_hash: str = Field(pattern=SHA256)
    qa_policy_content_hash: str = Field(pattern=SHA256)
    evaluator: ToolIdentity
    proof: Proof
    observations: tuple[GenerationObservation, ...]
    analysis_evidence: GenerationAnalysisEvidence | None = None
    size_bytes: int | None = Field(default=None, strict=True, gt=0)
    qa_policy_snapshot: QaPolicy | None = None
    presentation_evidence: PresentationEvidence | None = None
    advisory_observations: tuple[AdvisoryObservation, ...] = ()
    unresolved_quality_observations: tuple[UnresolvedQualityObservation, ...] = ()

    @model_validator(mode="after")
    def _version(self):
        if self.schema_version == "generation-evaluation/1":
            if (not self.observations or self.size_bytes is not None or self.qa_policy_snapshot is not None
                    or self.presentation_evidence is not None or self.advisory_observations
                    or self.unresolved_quality_observations or any(
                        o.evaluation_item_hash is not None or o.question_text is not None
                        or o.presentation_ref is not None or o.answer_ref is not None
                        or o.measurement_result is not None for o in self.observations)):
                raise ValueError("legacy evaluation cannot carry /2 fields")
        elif (self.size_bytes is None or self.qa_policy_snapshot is None
              or self.qa_policy_snapshot.content_hash != self.qa_policy_content_hash
              or canonical_sha256(self.qa_policy_snapshot) != self.qa_policy_content_hash):
            raise ValueError("/2 evaluation requires exact size and sealed QA snapshot")
        return self

    @model_serializer(mode="wrap")
    def _serialize(self, handler):
        result = handler(self)
        if self.analysis_evidence is None:
            result.pop("analysis_evidence", None)
        for name in ("size_bytes", "qa_policy_snapshot", "presentation_evidence",
                     "advisory_observations", "unresolved_quality_observations"):
            if getattr(self, name) is None or getattr(self, name) == ():
                result.pop(name, None)
        return result

    @property
    def source_sha256(self):
        return canonical_sha256(self.model_dump(mode="json"))

    def project_findings(self) -> tuple[Finding, ...]:
        return tuple(Finding(
            **item.model_dump(mode="python", include={"requirement_id", "verdict", "observation", "span_millis"}), rubric_hash=self.rubric_hash,
            stage="raw_generation", proof=self.proof,
            source_sha256=self.source_sha256,
        ) for item in self.observations)

    def answer_payload(self):
        return {name: [item.model_dump(mode="json") for item in getattr(self, name)] for name in (
            "observations", "advisory_observations", "unresolved_quality_observations")}

    def unresolved_refs(self):
        return tuple(canonical_sha256({"source_hash": self.source_sha256, "entry": item.model_dump(mode="json")})
                     for item in self.unresolved_quality_observations)


def _validate_marked_source(source, acceptance):
    rules = validate_semantic_inventory(acceptance.profile_payload, acceptance.required_requirement_ids)
    marked = bool(rules)
    if marked != (source.schema_version == "generation-evaluation/2"):
        raise ValueError("selected QA semantics require the matching evaluation version")
    if not marked:
        return
    items = evaluation_items(acceptance=acceptance, qa_policy_content_hash=source.qa_policy_content_hash,
        request_hash=source.request_hash, artifact_sha256=source.artifact_sha256, size_bytes=source.size_bytes)
    by_id = {item.requirement_id: item for item in items}
    rule_by_id = {r.requirement_id: r for r in rules}
    ids = [o.requirement_id for o in (*source.observations, *source.advisory_observations)]
    if len(set(ids)) != len(ids):
        raise ValueError("evaluation contains duplicate items")
    unresolved_ids = [o.observation_id for o in source.unresolved_quality_observations]
    if len(set(unresolved_ids)) != len(unresolved_ids):
        raise ValueError("evaluation contains duplicate unresolved quality observations")
    presentation = source.presentation_evidence
    if presentation is not None:
        if (presentation.actor_name != source.evaluator.name or presentation.actor_version != source.evaluator.version
                or presentation.items != tuple(i for i in items if i.proof == source.proof)
                or json.loads(presentation.answers_json) != source.answer_payload()):
            raise ValueError("presentation or answer differs from canonical evaluation items")
        if source.proof == "human":
            raise ValueError("controlled evaluator invocation does not establish human presentation")
    for observation in source.observations:
        item = by_id.get(observation.requirement_id)
        if (item is None or item.proof != source.proof
                or observation.evaluation_item_hash != item.evaluation_item_hash
                or observation.question_text != item.question_text):
            raise ValueError("observation answers a different criterion, stage or proof")
        require_canonical_observation_basis(item, observation)
        if presentation is None:
            if observation.verdict != "NOT_EVALUATED":
                raise ValueError("EVIDENCE_GAP: no verified presentation and answer evidence")
        elif (observation.presentation_ref != presentation.presentation_ref
              or observation.answer_ref != presentation.answer_ref):
            raise ValueError("observation does not bind the presented question and answer")
        result = observation.measurement_result
        if item.measurement_spec is not None:
            verdict = "NOT_EVALUATED" if result is None else temporal_verdict(item.measurement_spec, result)
            if result is not None and (result.artifact_sha256 != item.artifact_sha256
                    or result.size_bytes != item.size_bytes or result.evaluation_item_hash != item.evaluation_item_hash):
                raise ValueError("measurement does not match the exact media and item")
            if observation.verdict != verdict:
                raise ValueError("time verdict contradicts canonical measurement predicate")
        elif result is not None:
            raise ValueError("untyped criterion cannot accept a typed time measurement")
    for observation in source.advisory_observations:
        rule = rule_by_id.get(observation.requirement_id)
        if rule is None or rule.level == "acceptance" or rule.stage != "raw_generation" or rule.proof != source.proof:
            raise ValueError("advisory must reference a current non-acceptance raw item and proof")
    for observation in source.unresolved_quality_observations:
        if presentation is None or observation.answer_ref != presentation.answer_ref:
            raise ValueError("unresolved quality requires verified original answer evidence")


def project_generation_evaluation_sources(*, sources, acceptance):
    """The sole source-to-findings/refs projection, shared by all entrypoints."""
    findings, refs = [], []
    for source in sources:
        source = GenerationEvaluationSource.model_validate(source.model_dump(mode="python"))
        _validate_marked_source(source, acceptance)
        findings.extend(source.project_findings())
        refs.extend(source.unresolved_refs())
    return tuple(findings), tuple(sorted(set(refs)))


def require_generation_evaluation_authorities(qa_policy, acceptance):
    """A required proof layer needs an explicitly configured owner before submit."""
    required = {item["proof"] for item in acceptance.profile_payload["generation_requirements"]
                if item["level"] == "acceptance" and item["stage"] == "raw_generation"}
    configured = {item.proof for item in qa_policy.generation_evaluation_authorities}
    if not required <= configured:
        raise ValueError("current QA policy has no authority for required generation proof")


def validate_generation_evaluation_sources(*, sources, evidence, qa_policy, loaded=None, size_bytes=None,
                                          acceptance=None):
    """Reopen exact source identity and the current policy-selected authority."""
    if not sources:
        raise ValueError("media evaluation requires the original evaluator sources")
    if acceptance is None:
        acceptance = qa_policy.selected_generation_acceptance()
    else:
        # Strict historical reopen may use a component's originally sealed rubric.
        policies = [qa_policy.selected_generation_acceptance()]
        policies.extend(c.generation_acceptance for a in qa_policy.production_allocations for c in a.components)
        if acceptance not in policies:
            raise ValueError("experience rubric was not part of its sealed QA snapshot")
    if loaded is not None:
        from ai_video.production.production_strategy_reader import selected_shot_generation_acceptance

        if loaded.qa_policy != qa_policy:
            raise ValueError("generation evaluation QA differs from selected project policy")
        acceptance = selected_shot_generation_acceptance(loaded, evidence.shot_id)
    if acceptance is None or acceptance.profile_content_hash != evidence.rubric_hash:
        raise ValueError("generation evaluation rubric is not selected by current QA policy")
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
        if source.schema_version == "generation-evaluation/2" and (
            size_bytes is not None and source.size_bytes != size_bytes
            or source.analysis_evidence is not None and source.analysis_evidence.size_bytes != source.size_bytes
        ):
            raise ValueError("evaluation source size differs from exact fetched media")
        if source.evaluator not in qa_policy.semantic_authorities:
            raise ValueError("generation evaluator is not a policy-selected authority")
        if not any(item.evaluator == source.evaluator and item.proof == source.proof
                   for item in qa_policy.generation_evaluation_authorities):
            raise ValueError("generation evaluator is not authorized for this proof kind")
    projected, refs = project_generation_evaluation_sources(sources=sources, acceptance=acceptance)
    if tuple(projected) != evidence.findings or refs != getattr(evidence, "unresolved_quality_refs", ()):
        raise ValueError("generation findings differ from original evaluator sources")
