"""Pure selected-QA evaluation views and bounded source-time predicates."""

from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256
from ai_video.production.requirement_semantics import EventTimeWindow, SHA256, validate_semantic_inventory


class EvaluationItem(StrictModel):
    template_version: Literal["generation-question/1"] = "generation-question/1"
    qa_policy_content_hash: str = Field(pattern=SHA256)
    rubric_hash: str = Field(pattern=SHA256)
    request_hash: str = Field(pattern=SHA256)
    artifact_sha256: str = Field(pattern=SHA256)
    size_bytes: int = Field(strict=True, gt=0)
    requirement_id: str
    category: str
    level: Literal["acceptance"] = "acceptance"
    stage: Literal["raw_generation"] = "raw_generation"
    proof: Literal["technical", "analyzer", "human"]
    observable: str
    tolerance: str
    measurement: str
    measurement_spec: EventTimeWindow | None = None

    @property
    def question_text(self):
        return (f"[{self.requirement_id}] {self.observable}\nAcceptable variation: {self.tolerance}\n"
                f"Measurement: {self.measurement}\nStage: {self.stage}; proof: {self.proof}.\n"
                "Report PASS, FAIL or NOT_EVALUATED for this criterion and cite the observed evidence.")

    @property
    def evaluation_item_hash(self):
        return canonical_sha256({**self.model_dump(mode="json"), "question_text": self.question_text})


def evaluation_items(*, acceptance, qa_policy_content_hash, request_hash, artifact_sha256, size_bytes):
    rules = validate_semantic_inventory(acceptance.profile_payload, acceptance.required_requirement_ids)
    return tuple(EvaluationItem(qa_policy_content_hash=qa_policy_content_hash,
        rubric_hash=acceptance.profile_content_hash, request_hash=request_hash,
        artifact_sha256=artifact_sha256, size_bytes=size_bytes, requirement_id=r.requirement_id,
        category=r.semantics.category, proof=r.proof, observable=r.observable,
        tolerance=r.tolerance, measurement=r.measurement, measurement_spec=r.measurement_spec)
        for r in rules if r.level == "acceptance" and r.stage == "raw_generation")


class TemporalMeasurement(StrictModel):
    artifact_sha256: str = Field(pattern=SHA256)
    size_bytes: int = Field(strict=True, gt=0)
    evaluation_item_hash: str = Field(pattern=SHA256)
    event_id: str = Field(min_length=1)
    boundary: Literal["start", "end", "completion"]
    timebase: Literal["source_media_millis"]
    interval_millis: tuple[int, int] | None
    method: str = Field(min_length=1)
    coverage_millis: tuple[int, int]
    evidence_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _interval(self):
        for interval in (self.interval_millis, self.coverage_millis):
            if interval is not None and (any(type(x) is not int for x in interval)
                                         or interval[0] < 0 or interval[1] < interval[0]):
                raise ValueError("invalid measurement interval")
        if any(not ref.strip() for ref in self.evidence_refs):
            raise ValueError("measurement needs evidence references")
        return self


def temporal_verdict(spec, result):
    if (result.event_id != spec.event_id or result.boundary != spec.boundary
            or result.timebase != spec.timebase):
        raise ValueError("measurement answers a different event")
    if (result.interval_millis is None or result.method not in spec.allowed_methods
            or result.coverage_millis[0] > spec.required_coverage[0]
            or result.coverage_millis[1] < spec.required_coverage[1]):
        return "NOT_EVALUATED"
    low, high = result.interval_millis
    if low < result.coverage_millis[0] or high > result.coverage_millis[1]:
        return "NOT_EVALUATED"
    below = high < spec.lower_millis or high == spec.lower_millis and not spec.lower_inclusive
    above = low > spec.upper_millis or low == spec.upper_millis and not spec.upper_inclusive
    if below or above:
        return "FAIL"
    inside_low = low > spec.lower_millis or low == spec.lower_millis and spec.lower_inclusive
    inside_high = high < spec.upper_millis or high == spec.upper_millis and spec.upper_inclusive
    return "PASS" if inside_low and inside_high else "NOT_EVALUATED"


class PresentationEvidence(StrictModel):
    """Retained controlled invocation, admitted only by a live verifier proof.

    Offline validation checks the immutable transaction's captured events, not
    caller timestamps. This is local host provenance, not remote attestation.
    """

    namespace: Literal["controlled-evaluator/1"]
    interaction_ref: str = Field(min_length=1)
    presentation_ref: str = Field(min_length=1)
    answer_ref: str = Field(min_length=1)
    event_order: tuple[Literal["presentation"], Literal["answer"]]
    actor_name: str = Field(min_length=1)
    actor_version: str = Field(min_length=1)
    items: tuple[EvaluationItem, ...]
    answers_json: str = Field(min_length=1)

    @model_validator(mode="after")
    def _events(self):
        if self.presentation_ref == self.answer_ref:
            raise ValueError("presentation and answer must be distinct correlated events")
        if len({i.requirement_id for i in self.items}) != len(self.items):
            raise ValueError("presentation has duplicate items")
        return self
