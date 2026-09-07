"""Pure diagnosis of exact attempt evidence; never adjudicates or repairs media."""

from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.generation_recipe import SHA256, Proof, Stage, GenerationRecipe
from ai_video.production.hashing import canonical_sha256


class Finding(StrictModel):
    requirement_id: str
    rubric_hash: str = Field(pattern=SHA256)
    stage: Stage
    proof: Proof
    verdict: Literal["PASS", "FAIL", "NOT_EVALUATED"]
    source_sha256: str = Field(pattern=SHA256)
    observation: str = Field(min_length=1)
    span_millis: tuple[int, int] | None = None

    @model_validator(mode="after")
    def _span(self):
        if self.span_millis is not None:
            start, end = self.span_millis
            if start < 0 or end < start:
                raise ValueError("invalid failure span")
        return self


class AttemptEvidence(StrictModel):
    task_id: str = Field(min_length=1)
    shot_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    recipe_scope_hash: str = Field(pattern=SHA256)
    facts_hash: str = Field(pattern=SHA256)
    rubric_hash: str = Field(pattern=SHA256)
    request_hash: str = Field(pattern=SHA256)
    artifact_sha256: str | None = Field(default=None, pattern=SHA256)
    outcome: Literal["media", "runtime_failure", "unknown_outcome", "not_submitted"]
    stage: Stage = "raw_generation"
    findings: tuple[Finding, ...] = ()
    runtime_reason: str | None = None
    intervention_id: str | None = None
    intervention_semantic_hash: str | None = Field(default=None, pattern=SHA256)
    actual_delta: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _evidence_shape(self):
        if (self.outcome == "media") != (self.artifact_sha256 is not None):
            raise ValueError("media outcome must identify exact artifact bytes")
        if self.outcome != "media" and self.findings:
            raise ValueError("no-media outcome cannot have media findings")
        if self.outcome == "runtime_failure" and not self.runtime_reason:
            raise ValueError("runtime failure requires an execution reason")
        return self

    @property
    def evidence_hash(self):
        return canonical_sha256(self.model_dump(mode="json"))


class Diagnosis(StrictModel):
    failure_classes: tuple[str, ...]
    failed_requirements: tuple[str, ...] = ()
    preserved_requirements: tuple[str, ...] = ()
    evidence_hashes: tuple[str, ...]
    next_owner: str
    # This is deliberately not a Gate PASS or an acceptance receipt.
    all_required_observed_pass: bool = False


def diagnose_attempt(attempt: AttemptEvidence, recipe: GenerationRecipe) -> Diagnosis:
    attempt = AttemptEvidence.model_validate(attempt.model_dump(mode="python"))
    recipe = GenerationRecipe.model_validate(recipe.model_dump(mode="python"))
    classes = set()
    failed, preserved = set(), set()
    if attempt.outcome == "unknown_outcome":
        classes.add("UNKNOWN_OUTCOME")
    elif attempt.outcome == "runtime_failure":
        classes.add("RUNTIME_FAILURE")
    elif attempt.outcome == "not_submitted":
        classes.add("NOT_SUBMITTED")
    else:
        if attempt.rubric_hash != recipe.rubric_hash:
            classes.add("RUBRIC_OR_STAGE_ERROR")
        rules = {r.requirement_id: r for r in recipe.expressions}
        for finding in attempt.findings:
            rule = rules.get(finding.requirement_id)
            if (rule is None or finding.rubric_hash != recipe.rubric_hash
                    or finding.stage != attempt.stage or finding.stage != rule.stage
                    or rule.level != "acceptance"):
                classes.add("RUBRIC_OR_STAGE_ERROR")
        for rule in recipe.expressions:
            if rule.level != "acceptance" or rule.stage != attempt.stage:
                continue
            observations = tuple(f for f in attempt.findings
                                 if f.requirement_id == rule.requirement_id
                                 and f.proof == rule.proof
                                 and f.stage == rule.stage
                                 and f.rubric_hash == recipe.rubric_hash)
            if not observations or any(f.verdict == "NOT_EVALUATED" for f in observations):
                classes.add("EVIDENCE_GAP")
            if any(f.verdict == "FAIL" for f in observations):
                classes.add("QUALITY_FAILURE")
                failed.add(rule.requirement_id)
            elif observations and all(f.verdict == "PASS" for f in observations):
                preserved.add(rule.requirement_id)
        # An actual viewing rejection remains evidence even beside technical PASS.
        if any(f.proof == "human" and f.verdict == "FAIL" for f in attempt.findings):
            classes.add("QUALITY_FAILURE")
            failed.update(f.requirement_id for f in attempt.findings
                          if f.proof == "human" and f.verdict == "FAIL")
    owner = "review_owner"
    for label, next_owner in (
        ("QUALITY_FAILURE", "shot_router"),
        ("EVIDENCE_GAP", "evidence_owner"),
        ("RUBRIC_OR_STAGE_ERROR", "acceptance_owner"),
        ("RUNTIME_FAILURE", "runtime_owner"),
        ("UNKNOWN_OUTCOME", "explicit_recovery"),
    ):
        if label in classes:
            owner = next_owner
    return Diagnosis(failure_classes=tuple(sorted(classes)),
                     failed_requirements=tuple(sorted(failed)),
                     preserved_requirements=tuple(sorted(preserved - failed)),
                     evidence_hashes=(attempt.evidence_hash,), next_owner=owner,
                     all_required_observed_pass=bool(preserved) and not classes)


def diagnose_exact_result(attempt: AttemptEvidence, evidence: tuple[AttemptEvidence, ...],
                          recipe: GenerationRecipe) -> Diagnosis:
    """Combine proof layers for one exact result without rewriting source evidence."""
    attempt = AttemptEvidence.model_validate(attempt.model_dump(mode="python"))
    if attempt.outcome != "media":
        return diagnose_attempt(attempt, recipe)
    identity_fields = ("task_id", "shot_id", "request_hash", "artifact_sha256",
                       "recipe_scope_hash", "facts_hash", "rubric_hash", "stage")
    records = {attempt.evidence_hash: attempt}
    for entry in evidence:
        entry = AttemptEvidence.model_validate(entry.model_dump(mode="python"))
        if entry.outcome == "media" and all(getattr(entry, name) == getattr(attempt, name)
                                            for name in identity_fields):
            records[entry.evidence_hash] = entry
    findings = {canonical_sha256(f.model_dump(mode="json")): f
                for entry in records.values() for f in entry.findings}
    def proof_key(finding):
        return (finding.requirement_id, finding.rubric_hash, finding.stage, finding.proof)
    observed = {proof_key(f) for f in findings.values() if f.verdict != "NOT_EVALUATED"}
    # Completed observations can fill a missing proof layer. Explicit rejections
    # remain present even alongside a PASS; this helper cannot overturn verdicts.
    combined = tuple(f for _, f in sorted(findings.items())
                     if f.verdict != "NOT_EVALUATED" or proof_key(f) not in observed)
    diagnosis = diagnose_attempt(attempt.model_copy(update={"findings": combined}), recipe)
    return diagnosis.model_copy(update={"evidence_hashes": tuple(sorted(records))})


class Intervention(StrictModel):
    intervention_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    purpose: Literal["diagnostic", "production_repair", "resample"]
    disposition: Literal["GENERATE_ONCE", "SPLIT_SHOT", "CHANGE_GENERATION_STRATEGY",
                         "CHANGE_PROVIDER_MODEL", "CHANGE_REFERENCE_STRATEGY",
                         "CAPABILITY_BOUNDARY"]
    closes: tuple[str, ...] = Field(min_length=1)
    protected_requirements: tuple[str, ...] = ()
    support: tuple[str, ...] = Field(min_length=1)
    counterevidence: tuple[str, ...] = ()
    changed_variables: tuple[str, ...]
    held_constants: tuple[str, ...]
    uncontrolled_variables: tuple[str, ...]
    regression_risks: tuple[str, ...]
    hypothesis: str = Field(min_length=1)
    confidence_basis: str = Field(min_length=1)
    improvement_prediction: str = Field(min_length=1)
    falsification_prediction: str = Field(min_length=1)
    insufficient_evidence_condition: str = Field(min_length=1)
    # Optional hashes bind the intended values of declared controlled variables
    # without making explanatory wording a new experiment.
    semantic_variable_hashes: tuple[tuple[str, str], ...] = ()
    resample_limit: int | None = Field(default=None, strict=True, gt=0)

    @model_validator(mode="after")
    def _comparison(self):
        if self.purpose == "diagnostic" and len(self.changed_variables) != 1:
            raise ValueError("diagnostic comparison must isolate one declared variable")
        if set(self.changed_variables) & set(self.held_constants):
            raise ValueError("changed variables cannot also be held constant")
        if set(self.closes) & set(self.protected_requirements):
            raise ValueError("targeted requirements cannot also be protected requirements")
        semantic_names = [name for name, _ in self.semantic_variable_hashes]
        if len(semantic_names) != len(set(semantic_names)):
            raise ValueError("duplicate semantic variable hash")
        if not set(semantic_names) <= set(self.changed_variables):
            raise ValueError("semantic variable hash must name a changed variable")
        if any(len(value) != 64 or any(char not in "0123456789abcdef" for char in value)
               for _, value in self.semantic_variable_hashes):
            raise ValueError("semantic variable hash must be SHA-256")
        if (self.disposition == "GENERATE_ONCE" and self.purpose != "resample"
                and not self.changed_variables):
            raise ValueError("non-resample generation repair must change a declared variable")
        if (self.disposition == "GENERATE_ONCE" and self.purpose != "resample"
                and set(self.changed_variables) == {"seed"}):
            raise ValueError("seed-only changes must use the bounded resample policy")
        if self.purpose == "resample" and self.resample_limit is None:
            raise ValueError("resampling requires its own finite limit")
        return self

    @property
    def semantic_hash(self):
        """Stable identity for one controlled experiment, not its explanation.

        Proposal IDs, evidence citations, confidence prose, predictions and the
        caller-provided resample ceiling are audit context.  They must never
        turn the same controlled action into a new experiment.
        """
        return canonical_sha256({
            "schema": "generation-intervention-semantic/3",
            "purpose": self.purpose,
            "disposition": self.disposition,
            "changed_variables": tuple(sorted(self.changed_variables)),
            "uncontrolled_variables": tuple(sorted(self.uncontrolled_variables)),
            "semantic_variable_hashes": tuple(sorted(self.semantic_variable_hashes)),
        })


PredictionOutcome = Literal["supported", "refuted", "undetermined"]


def intervention_prediction_outcome(intervention: Intervention,
                                    diagnosis: Diagnosis) -> PredictionOutcome:
    """Classify the exact observable result of one intervention.

    This records whether the stated target/protected requirements were observed.
    It deliberately does not claim that the intervention caused the result.
    """
    blocking = {"UNKNOWN_OUTCOME", "RUNTIME_FAILURE", "RUBRIC_OR_STAGE_ERROR", "EVIDENCE_GAP"}
    if blocking.intersection(diagnosis.failure_classes):
        return "undetermined"
    failed = set(diagnosis.failed_requirements)
    preserved = set(diagnosis.preserved_requirements)
    targeted = set(intervention.closes)
    protected = set(intervention.protected_requirements)
    if (targeted | protected) & failed:
        return "refuted"
    if targeted <= preserved and protected <= preserved:
        return "supported"
    return "undetermined"


_COMPARISON_FIELDS = ("provider_name", "provider_kind", "model_id", "provider_profile",
              "mode", "prompt_text", "negative_prompt_text", "image_bindings",
              "media_bindings", "output_requirement", "seed", "execution_stack_hash",
              "adapter_compiler_id", "adapter_compiler_version", "adapter_compiler_hash",
              "c4_multi_anchor_binding", "continuity_binding", "hard_cut_keyframe_binding")


def compiled_variable_hashes(request) -> tuple[tuple[str, str], ...]:
    from ai_video.production.video import VideoGenerationRequest

    request = VideoGenerationRequest.model_validate(request.model_dump(mode="python"))
    payload = request.model_dump(mode="json")
    return tuple((name, canonical_sha256({"value": payload.get(name)})) for name in sorted(_COMPARISON_FIELDS))


def compare_compiled_requests(before, after) -> dict:
    """Compare actual native request semantics, ignoring independent attempt IDs."""
    from ai_video.production.video import VideoGenerationRequest

    before = VideoGenerationRequest.model_validate(before.model_dump(mode="python"))
    after = VideoGenerationRequest.model_validate(after.model_dump(mode="python"))
    left, right = before.model_dump(mode="json"), after.model_dump(mode="json")
    changed = tuple(name for name in _COMPARISON_FIELDS if left.get(name) != right.get(name))
    return {"changed_variables": changed,
            "held_constants": tuple(name for name in _COMPARISON_FIELDS if name not in changed),
            "uncontrolled_stochasticity": before.seed is None or before.seed < 0 or after.seed is None or after.seed < 0,
            "before_request_hash": before.request_input_hash,
            "after_request_hash": after.request_input_hash}


def verify_intervention_comparison(intervention, before, after) -> dict:
    delta = compare_compiled_requests(before, after)
    if set(delta["changed_variables"]) != set(intervention.changed_variables):
        raise ValueError("actual compiled delta differs from declared intervention")
    if not set(intervention.held_constants) <= set(delta["held_constants"]):
        raise ValueError("claimed held constants changed in compiled requests")
    if delta["uncontrolled_stochasticity"] and "seed" not in intervention.uncontrolled_variables:
        raise ValueError("uncontrolled seed must be disclosed")
    actual = dict(compiled_variable_hashes(after))
    if any(actual.get(name) != value for name, value in intervention.semantic_variable_hashes):
        raise ValueError("intended variable value differs from actual compiled request")
    return delta


def seal_intervention_comparison(intervention, baseline):
    from ai_video.production.generation_recipe import CompiledComparison

    return CompiledComparison(request_hash=baseline.request_input_hash,
                              baseline_seed_controlled=baseline.seed is not None and baseline.seed >= 0,
                              variable_hashes=compiled_variable_hashes(baseline),
                              changed_variables=intervention.changed_variables,
                              target_variable_hashes=intervention.semantic_variable_hashes,
                              held_constants=intervention.held_constants,
                              uncontrolled_variables=intervention.uncontrolled_variables)


def compiled_comparison_errors(comparison, request) -> tuple[str, ...]:
    left, right = dict(comparison.variable_hashes), dict(compiled_variable_hashes(request))
    if set(left) != set(right):
        return ("generation_recipe.comparison.baseline",)
    actual = {name for name in left if left[name] != right[name]}
    if actual != set(comparison.changed_variables) or actual & set(comparison.held_constants):
        return ("generation_recipe.comparison.actual_delta",)
    if any(right.get(name) != value for name, value in comparison.target_variable_hashes):
        return ("generation_recipe.comparison.target_values",)
    if (not comparison.baseline_seed_controlled or request.seed is None or request.seed < 0) and "seed" not in comparison.uncontrolled_variables:
        return ("generation_recipe.comparison.uncontrolled_seed",)
    return ()
