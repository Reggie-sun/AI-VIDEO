"""Shot Router's pure generation policy over explicit immutable snapshots."""

from typing import Literal

from pydantic import Field, model_serializer, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production._shot_router_contracts import (
    AdapterCompilerContract, RequirementRoutingResult, RoutingOutcome,
)
from ai_video.production.generation_diagnosis import (
    AttemptEvidence, Diagnosis, Intervention, diagnose_exact_result,
    intervention_prediction_outcome,
)
from ai_video.production.generation_recipe import GenerationRecipe, SHA256
from ai_video.production.hashing import canonical_sha256
from ai_video.production.final_output_contracts import FinalOutputContract
from ai_video.production.generation_rejection import (
    GenerationQualityRejectionReceipt, validate_abandoned_result,
)
from ai_video.production.video import (
    ProviderProfilePointer, VideoGenerationRequest, VideoOutputRequirement, VideoProviderCapabilities,
)
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement


class GenerationCandidate(StrictModel):
    candidate_id: str = Field(min_length=1)
    provider_profile: ProviderProfilePointer
    capabilities: VideoProviderCapabilities
    capability_id: str = Field(min_length=1)
    compiler_contract: AdapterCompilerContract
    output_requirement: VideoOutputRequirement | VideoFlexibleOutputRequirement
    recipe: GenerationRecipe
    final_output_goal: FinalOutputContract | None = None

    @model_serializer(mode="wrap")
    def _serialize_goal(self, handler):
        result = handler(self)
        if self.final_output_goal is None:
            result.pop("final_output_goal", None)
        return result

    @model_validator(mode="after")
    def _identity(self):
        if (self.recipe.profile_sha256 != self.provider_profile.profile_sha256
                or self.recipe.compiler_hash != self.compiler_contract.compiler_hash):
            raise ValueError("recipe profile/compiler identity mismatch")
        variants = tuple(v for v in self.capabilities.variants
                         if v.capability_id == self.capability_id)
        if len(variants) != 1:
            raise ValueError("candidate must name one exact registered capability")
        if self.recipe.seed.kind != "uncontrolled" and not variants[0].seed_supported:
            raise ValueError("controlled recipe requires a seed-supported capability")
        return self

    @property
    def scope_hash(self):
        payload = {"provider": self.capabilities.provider_name,
                                 "capability": self.capability_id,
                                 "capabilities": self.capabilities.capabilities_fingerprint,
                                 "recipe": self.recipe.fit_hash,
                                 "output": self.output_requirement.model_dump(mode="json")}
        if self.final_output_goal is not None:
            payload["final_output_goal"] = self.final_output_goal.contract_hash
        return canonical_sha256(payload)


class ExecutionLimits(StrictModel):
    """Current orchestration projection; no reservation or authorization writer."""

    task_id: str = Field(min_length=1)
    generation_forbidden: bool
    allowed_remote_candidates: tuple[str, ...] = ()
    paid_submit_ceiling: int = Field(strict=True, ge=0)
    paid_submits_used: int = Field(strict=True, ge=0)
    local_batch_limit: int = Field(strict=True, gt=0)
    local_batch_used: int = Field(strict=True, ge=0)
    local_total_limit: int | None = Field(default=None, strict=True, gt=0)
    local_total_used: int = Field(strict=True, ge=0)
    local_resource_available: bool
    batch_review_evidence_hash: str | None = Field(default=None, pattern=SHA256)


class DecisionPolicy(StrictModel):
    policy_id: Literal["generation-decision"] = "generation-decision"
    # Version 1 remains readable for sealed historical inputs.  Version 2
    # moves the resample ceiling to policy so a new proposal cannot expand it.
    version: Literal["1", "2", "3"] = "3"
    repeated_failure_threshold: int = Field(default=3, strict=True, ge=2)
    max_resamples: int = Field(default=1, strict=True, ge=0)
    allow_bounded_exploration: bool = False

    @property
    def content_hash(self):
        return canonical_sha256(self.model_dump(mode="json"))


class InputConflict(StrictModel):
    kind: Literal["reference", "intent", "rubric", "evaluator"]
    source_sha256: str = Field(pattern=SHA256)
    observation: str = Field(min_length=1)
    affected_requirements: tuple[str, ...] = Field(min_length=1)
    next_owner: str = Field(min_length=1)


class DecisionInputs(StrictModel):
    projection_hash: str = Field(pattern=SHA256)
    facts_hash: str = Field(pattern=SHA256)
    rubric_hash: str = Field(pattern=SHA256)
    policy: DecisionPolicy
    limits: ExecutionLimits
    candidates: tuple[GenerationCandidate, ...] = Field(min_length=1)
    evidence: tuple[AttemptEvidence, ...] = ()
    latest_attempt_hash: str | None = Field(default=None, pattern=SHA256)
    interventions: tuple[Intervention, ...] = ()
    conflicts: tuple[InputConflict, ...] = ()
    historical_recipes: tuple[GenerationCandidate, ...] = ()
    baseline_request: VideoGenerationRequest | None = None
    user_fixed_candidates: tuple[str, ...] = ()
    experiences: tuple["GenerationExperience", ...] = ()
    feature_scope: "GenerationFeatures | None" = None
    abandoned_result: GenerationQualityRejectionReceipt | None = None

    @model_serializer(mode="wrap")
    def _serialize_abandonment(self, handler):
        data = handler(self)
        if self.abandoned_result is None:
            data.pop("abandoned_result", None)
        return data

    @model_validator(mode="after")
    def _snapshot(self):
        ids = [c.candidate_id for c in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate candidate IDs")
        for candidate in self.candidates:
            variant = next(v for v in candidate.capabilities.variants
                           if v.capability_id == candidate.capability_id)
            if variant.seed_supported and candidate.recipe.seed.kind == "uncontrolled":
                raise ValueError("current candidates require an explicit controlled seed")
        evidence_ids = [e.evidence_hash for e in self.evidence]
        if any(e.evidence_hash not in evidence_ids for experience in self.experiences
               for e in experience.evidence):
            raise ValueError("experience is absent from complete evidence snapshot")
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("duplicate exact evidence projection")
        if self.latest_attempt_hash is not None and self.latest_attempt_hash not in evidence_ids:
            raise ValueError("latest attempt missing from evidence snapshot")
        if not set(self.user_fixed_candidates) <= set(ids):
            raise ValueError("user constraint names an absent candidate")
        if not set(self.limits.allowed_remote_candidates) <= set(ids):
            raise ValueError("execution scope names an absent candidate")
        if len({c.recipe.rubric_hash for c in self.candidates}) != 1:
            raise ValueError("candidates cannot compare different rubrics")
        if len({c.final_output_goal for c in self.candidates}) != 1:
            raise ValueError("candidates cannot compare different final-output goals")
        rubric_projections = {
            canonical_sha256({"expressions": [r.model_dump(mode="json", exclude={"native_text"})
                              for r in c.recipe.expressions]}) for c in self.candidates
        }
        if len(rubric_projections) != 1:
            raise ValueError("candidate recipes must preserve the same acceptance projection")
        return self

    @property
    def snapshot_hash(self):
        payload = self.model_dump(mode="json")
        for field in ("candidates", "evidence", "interventions", "conflicts", "historical_recipes", "experiences"):
            payload[field] = sorted(payload[field], key=canonical_sha256)
        payload["user_fixed_candidates"] = sorted(payload["user_fixed_candidates"])
        payload["limits"]["allowed_remote_candidates"] = sorted(payload["limits"]["allowed_remote_candidates"])
        return canonical_sha256(payload)


class CandidateAssessment(StrictModel):
    candidate_id: str
    scope_hash: str
    fit: Literal["supported", "unknown", "conflicting", "unsupported"]
    compatible: bool
    executable: bool
    supported_dimensions: tuple[str, ...]
    failed_dimensions: tuple[str, ...]
    unknown_dimensions: tuple[str, ...]
    evidence_hashes: tuple[str, ...]
    ignored_evidence_hashes: tuple[str, ...]
    sample_count: int
    pass_count: int
    fail_count: int
    not_evaluated_count: int
    runtime_failure_count: int
    unknown_outcome_count: int
    not_submitted_count: int
    reasons: tuple[str, ...]
    empirical: "EmpiricalEstimate | None" = None


class GenerationDecision(StrictModel):
    snapshot_hash: str
    disposition: str
    selected_candidate_id: str | None = None
    assessments: tuple[CandidateAssessment, ...]
    diagnosis: Diagnosis | None = None
    intervention: Intervention | None = None
    routing: RequirementRoutingResult | None = None
    rationale: tuple[str, ...]
    revalidate_requirements: tuple[str, ...] = ()
    # Recompute selection from current inputs before binding; never consume this
    # advisory result as a submit permit or mutable progress checkpoint.
    @property
    def decision_hash(self):
        return canonical_sha256(self.model_dump(mode="json"))


def _assess(candidate, inputs, routing):
    recipe = candidate.recipe
    relevant = tuple(e for e in inputs.evidence
                     if e.recipe_scope_hash == candidate.scope_hash
                     and e.facts_hash == inputs.facts_hash
                     and e.rubric_hash == inputs.rubric_hash)
    dimensions = {r.dimension for r in recipe.expressions
                  if r.level == "acceptance" and r.stage == "raw_generation"}
    support, failed = set(), set()
    supported_by_artifact: dict[str, set[str]] = {}
    passes, failures, unevaluated = set(), set(), set()
    for e in relevant:
        if e.outcome != "media" or e.stage != "raw_generation":
            continue
        diagnosis = diagnose_exact_result(e, relevant, recipe)
        for rule in recipe.expressions:
            if rule.requirement_id in diagnosis.failed_requirements:
                failed.add(rule.dimension)
            if rule.requirement_id in diagnosis.preserved_requirements:
                supported_by_artifact.setdefault(e.artifact_sha256, set()).add(rule.requirement_id)
        if "QUALITY_FAILURE" in diagnosis.failure_classes:
            failures.add(e.artifact_sha256)
        elif diagnosis.all_required_observed_pass:
            passes.add(e.artifact_sha256)
        else:
            unevaluated.add(e.artifact_sha256)
    # Multiple records/proof layers of the same bytes are never independent wins.
    passes -= failures | unevaluated
    unevaluated -= failures
    for dimension in dimensions:
        required_ids = {r.requirement_id for r in recipe.expressions
                        if r.level == "acceptance" and r.stage == "raw_generation"
                        and r.dimension == dimension}
        # Proof for separate media bytes cannot be pooled into a virtual PASS.
        if any(required_ids <= observed for observed in supported_by_artifact.values()):
            support.add(dimension)
    unknown = dimensions - support - failed
    fit = "unknown"
    if failed:
        fit = ("unsupported" if len(failures) >= inputs.policy.repeated_failure_threshold
               else "conflicting")
    elif dimensions and passes:
        fit = "supported"
    empirical = empirical_assessment(candidate, inputs.feature_scope, inputs.experiences)
    if empirical.failed_artifacts and not empirical.supported_artifacts:
        fit = ("unsupported" if len(empirical.failed_artifacts) >= inputs.policy.repeated_failure_threshold
               else "conflicting")
    elif empirical.supported_artifacts:
        fit = "supported"
    variant = next(v for v in candidate.capabilities.variants if v.capability_id == candidate.capability_id)
    local = variant.execution_kind.value == "local"
    limits = inputs.limits
    reasons = []
    compatible = routing.decision.outcome == RoutingOutcome.SELECTED
    if not compatible:
        reasons.extend(code.value for code in routing.decision.reason_codes)
    if limits.generation_forbidden:
        reasons.append("GENERATION_FORBIDDEN")
    if local:
        if not limits.local_resource_available:
            reasons.append("LOCAL_RESOURCES_UNAVAILABLE")
        if limits.local_batch_used >= limits.local_batch_limit:
            reasons.append("LOCAL_BATCH_REVIEW_REQUIRED")
        if limits.local_total_limit is not None and limits.local_total_used >= limits.local_total_limit:
            reasons.append("LOCAL_TOTAL_LIMIT")
        if (limits.local_total_used > 0 and limits.local_batch_used == 0
                and limits.batch_review_evidence_hash is None):
            reasons.append("LOCAL_BATCH_REVIEW_REQUIRED")
    else:
        if candidate.candidate_id not in limits.allowed_remote_candidates:
            reasons.append("REMOTE_SCOPE_NOT_AUTHORIZED")
        if limits.paid_submits_used >= limits.paid_submit_ceiling:
            reasons.append("TASK_SUBMIT_CEILING")
    if inputs.user_fixed_candidates and candidate.candidate_id not in inputs.user_fixed_candidates:
        reasons.append("USER_ROUTE_CONSTRAINT")
    return CandidateAssessment(
        candidate_id=candidate.candidate_id, scope_hash=candidate.scope_hash, fit=fit,
        compatible=compatible, executable=not reasons,
        supported_dimensions=tuple(sorted(support)), failed_dimensions=tuple(sorted(failed)),
        unknown_dimensions=tuple(sorted(unknown)),
        evidence_hashes=tuple(sorted(e.evidence_hash for e in relevant)),
        ignored_evidence_hashes=tuple(sorted(e.evidence_hash for e in inputs.evidence if e not in relevant)),
        sample_count=len(passes | failures | unevaluated), pass_count=len(passes),
        fail_count=len(failures), not_evaluated_count=len(unevaluated),
        runtime_failure_count=sum(e.outcome == "runtime_failure" for e in relevant),
        unknown_outcome_count=sum(e.outcome == "unknown_outcome" for e in relevant),
        not_submitted_count=sum(e.outcome == "not_submitted" for e in relevant),
        reasons=tuple(reasons), empirical=empirical,
    )


def resolve_generation_decision(resolver, *, projection, context, policy, lifecycle,
                                inputs, continuity_routing=None):
    """Only the Router invokes the exact binder; candidates never execute here."""
    inputs = DecisionInputs.model_validate(inputs.model_dump(mode="python"))
    if inputs.feature_scope is not None and inputs.feature_scope != extract_generation_features(projection):
        raise ValueError("stale generation feature projection")
    if (inputs.projection_hash != projection.projection_hash
            or inputs.facts_hash != canonical_sha256(projection.requirement.model_dump(
                mode="json", exclude={"requirement_id", "requirement_hash"}))):
        raise ValueError("stale generation decision projection or difficulty facts")
    candidates = sorted(inputs.candidates, key=lambda c: c.candidate_id)
    for c in candidates:
        if (c.recipe.requirement_hash != projection.requirement.requirement_hash
                or c.recipe.rubric_hash != inputs.rubric_hash):
            raise ValueError("stale candidate requirement/rubric")
    # Inspect technical compatibility separately from execution authorization.
    # The selected candidate is rebound under the original execution policy.
    compatibility_policy = policy.model_copy(update={"remote_authorized": True,
                                                      "budget_authorized": True,
                                                      "local_resources_available": True})
    bindings = {c.candidate_id: resolver._bind_requirement(
        projection=projection, context=context, policy=compatibility_policy,
        provider_profile=c.provider_profile, capabilities=c.capabilities,
        selected_capability_id=c.capability_id, output_requirement=c.output_requirement,
        lifecycle=lifecycle, compiler_contract=c.compiler_contract,
        continuity_routing=continuity_routing) for c in candidates}
    assessments = tuple(_assess(c, inputs, bindings[c.candidate_id]) for c in candidates)
    base = dict(snapshot_hash=inputs.snapshot_hash, assessments=assessments)
    latest = next((e for e in inputs.evidence if e.evidence_hash == inputs.latest_attempt_hash), None)
    # Task identifiers scope submit quotas, not the Shot's failure/recovery
    # history. Starting a new task must not erase an unfinished exact attempt.
    current_attempts = tuple(e for e in inputs.evidence
                             if e.shot_id == context.target_shot_id)
    def exact_attempt(entry):
        return (entry.task_id, entry.shot_id, entry.attempt_id, entry.request_hash,
                entry.recipe_scope_hash, entry.facts_hash, entry.rubric_hash)

    # A later known outcome for the same exact attempt closes uncertainty, not
    # the historical record. At submit the committer requires this complete
    # persisted history and independently rejects any still-unknown lifecycle;
    # a caller-supplied media claim cannot act as recovery authorization.
    known_attempts = {exact_attempt(e) for e in inputs.evidence
                      if e.outcome in {"media", "runtime_failure"}}
    def unresolved_unknown(entry):
        return entry.outcome == "unknown_outcome" and exact_attempt(entry) not in known_attempts

    if any(unresolved_unknown(e) for e in current_attempts):
        return GenerationDecision(**base, disposition="UNKNOWN_OUTCOME",
                                  rationale=("explicit recovery must close the exact attempt",))
    if current_attempts and latest is None:
        return GenerationDecision(**base, disposition="EVIDENCE_GAP",
                                  rationale=("Shot history requires exact latest attempt identity",))
    if any(e.intervention_id is not None and e.intervention_semantic_hash is None for e in current_attempts):
        return GenerationDecision(**base, disposition="EVIDENCE_GAP",
                                  rationale=("repair semantic identity missing from current attempt history",))
    if latest is not None and latest.outcome == "not_submitted" and any(
        entry.outcome != "not_submitted" for entry in current_attempts
    ):
        return GenerationDecision(**base, disposition="EVIDENCE_GAP",
            rationale=("prepared-only work cannot replace the last submitted outcome and baseline",))
    goal_changed = False
    if inputs.abandoned_result is not None:
        prior = next((x for x in inputs.experiences if latest in x.evidence), None)
        if latest is None or prior is None or inputs.policy.version != "3":
            raise ValueError("abandoned result requires the latest complete experience and current policy")
        validate_abandoned_result(inputs.abandoned_result, experience=prior, evidence=latest,
                                  history=inputs.evidence)
    if latest is not None:
        if latest not in current_attempts:
            raise ValueError("latest attempt is outside current Shot")
        old_recipe = next((c.recipe for c in (*candidates, *inputs.historical_recipes)
                           if c.scope_hash == latest.recipe_scope_hash), None)
        if old_recipe is None:
            return GenerationDecision(**base, disposition="EVIDENCE_GAP",
                                      rationale=("include the prior exact recipe for diagnosis",))
        diagnosis = diagnose_exact_result(latest, inputs.evidence, old_recipe)
        base["diagnosis"] = diagnosis
        if inputs.policy.version == "3" and latest.rubric_hash != inputs.rubric_hash:
            old_goal = next(c.final_output_goal for c in (*candidates, *inputs.historical_recipes)
                if c.scope_hash == latest.recipe_scope_hash)
            new_goal = candidates[0].final_output_goal
            goal_changed = bool(old_goal is not None and new_goal is not None
                and (old_goal.goal_id, old_goal.goal_version) != (new_goal.goal_id, new_goal.goal_version))
            if not goal_changed:
                return GenerationDecision(**base, disposition="RUBRIC_OR_STAGE_ERROR",
                    rationale=("Final-output repair cannot replace its frozen goal requirements; retain the old failure and author a new goal version explicitly",))
        for reason in ("UNKNOWN_OUTCOME", "RUNTIME_FAILURE", "RUBRIC_OR_STAGE_ERROR", "EVIDENCE_GAP"):
            if goal_changed and reason == "EVIDENCE_GAP":
                continue
            if inputs.abandoned_result is not None and reason == "EVIDENCE_GAP":
                continue
            if reason in diagnosis.failure_classes:
                return GenerationDecision(**base, disposition=reason,
                                          rationale=(f"repair via {diagnosis.next_owner} on exact evidence",))
        if (diagnosis.all_required_observed_pass and latest.facts_hash == inputs.facts_hash
                and latest.recipe_scope_hash in {c.scope_hash for c in candidates}
                and not inputs.conflicts):
            return GenerationDecision(**base, disposition="REVIEW_CURRENT_RESULT",
                                      rationale=("current exact result has all applicable observations; use existing acceptance owner, not regeneration",))
    if inputs.conflicts:
        conflict = sorted(inputs.conflicts, key=lambda c: (c.kind, c.source_sha256))[0]
        disposition = {"reference": "CHANGE_REFERENCE_STRATEGY", "intent": "INTENT_OR_REFERENCE_CONFLICT",
                       "rubric": "RUBRIC_OR_STAGE_ERROR", "evaluator": "EVIDENCE_GAP"}[conflict.kind]
        return GenerationDecision(**base, disposition=disposition,
                                  rationale=tuple(f"{c.observation}; owner={c.next_owner}" for c in
                                                  sorted(inputs.conflicts, key=lambda c: (c.kind, c.source_sha256))))
    intervention = None
    if latest is not None and not goal_changed and "QUALITY_FAILURE" in base["diagnosis"].failure_classes:
        evidence_ids = {e.evidence_hash for e in inputs.evidence}
        alternatives = []
        unresolved_prediction = False
        for proposed in inputs.interventions:
            if inputs.policy.version == "3" and (
                proposed.known_requirement_violations
                or not set(base["diagnosis"].preserved_requirements)
                    <= set(proposed.protected_requirements)
                or not set(proposed.closes) <= set(base["diagnosis"].failed_requirements)
            ):
                continue
            if not set(proposed.support + proposed.counterevidence) <= evidence_ids:
                raise ValueError("intervention cites missing evidence")
            if latest.evidence_hash not in proposed.support + proposed.counterevidence:
                continue
            if not set(base["diagnosis"].failed_requirements) & set(proposed.closes):
                continue
            # A semantic experiment survives task/run naming changes.  Only a
            # submitted outcome consumes the shared policy budget; a prepared
            # but unsubmitted request must not do so.
            target = next((c for c in candidates if c.candidate_id == proposed.candidate_id), None)
            previous = tuple(e for e in inputs.evidence
                             if e.shot_id == context.target_shot_id
                             and (e.intervention_semantic_hash == proposed.semantic_hash
                                  or (target is not None and e.intervention_id is not None
                                      and e.recipe_scope_hash == target.scope_hash
                                      and set(e.actual_delta) == set(proposed.changed_variables)))
                             and e.outcome != "not_submitted")
            if proposed.purpose == "resample":
                target = next((c for c in candidates if c.candidate_id == proposed.candidate_id), None)
                if target is None:
                    raise ValueError("resample candidate is absent")
                expected_delta = () if target.recipe.seed.kind == "uncontrolled" else ("seed",)
                if tuple(sorted(proposed.changed_variables)) != expected_delta:
                    continue
                def strategy(candidate):
                    variant = next(v for v in candidate.capabilities.variants
                                   if v.capability_id == candidate.capability_id)
                    return candidate.capabilities.provider_name, variant.model_id, variant.mode
                sampling_history = []
                for entry in inputs.evidence:
                    if (entry.shot_id != context.target_shot_id or entry.intervention_id is None
                            or entry.outcome == "not_submitted" or set(entry.actual_delta) - {"seed"}):
                        continue
                    prior_candidate = next((c for c in (*candidates, *inputs.historical_recipes)
                                            if c.scope_hash == entry.recipe_scope_hash), None)
                    if prior_candidate is None:
                        return GenerationDecision(**base, disposition="EVIDENCE_GAP",
                            rationale=("sampling budget needs the historical generation strategy",))
                    if strategy(prior_candidate) == strategy(target):
                        sampling_history.append(entry)
                # Sampling is bounded per Shot and Provider/model/mode, across
                # task names and proposal wording/held-constant annotations.
                previous = tuple(sampling_history)
            if any(unresolved_unknown(e) for e in previous):
                return GenerationDecision(**base, disposition="UNKNOWN_OUTCOME",
                                          rationale=("explicit recovery must close the prior semantic experiment",))
            previous = tuple(e for e in previous if e.outcome != "unknown_outcome")
            prediction_outcomes = []
            for entry in previous:
                old_recipe = next((c.recipe for c in (*candidates, *inputs.historical_recipes)
                                   if c.scope_hash == entry.recipe_scope_hash), None)
                if old_recipe is None:
                    prediction_outcomes.append("undetermined")
                    continue
                prediction_outcomes.append(intervention_prediction_outcome(
                    proposed, diagnose_exact_result(entry, inputs.evidence, old_recipe),
                    require_all=inputs.policy.version == "3"))
            # A non-resample experiment may run once.  Its observed outcome is
            # retained to distinguish evidence repair from a relabeled retry.
            if previous and proposed.purpose != "resample":
                unresolved_prediction |= all(value == "undetermined" for value in prediction_outcomes)
                continue
            previous_attempts = {(e.task_id, e.shot_id, e.attempt_id, e.request_hash) for e in previous}
            if proposed.purpose == "resample" and len(previous_attempts) >= inputs.policy.max_resamples:
                continue
            alternatives.append(proposed)
        if not alternatives:
            if unresolved_prediction:
                return GenerationDecision(**base, disposition="EVIDENCE_GAP",
                                          rationale=("prior repair prediction remains undetermined; repair exact evidence before another intervention",))
            return GenerationDecision(**base, disposition="REASSESS_FEASIBILITY",
                                      rationale=("no new testable intervention; stop equivalent retries",))
        if len(alternatives) > 1:
            # Prefer hypotheses with independent supporting exact artifacts and
            # fewer recorded counterexamples, not caller proposal order.
            def rank(p):
                supporting = {e.artifact_sha256 for e in inputs.evidence
                              if e.evidence_hash in p.support and e.artifact_sha256 is not None}
                opposing = {e.artifact_sha256 for e in inputs.evidence
                            if e.evidence_hash in p.counterevidence and e.artifact_sha256 is not None}
                return (len(opposing), -len(supporting), len(p.regression_risks))
            alternatives.sort(key=lambda p: (rank(p), p.intervention_id))
            if rank(alternatives[0]) == rank(alternatives[1]):
                return GenerationDecision(**base, disposition="UNRESOLVED_TIE",
                                          rationale=("intervention evidence does not distinguish hypotheses",))
        intervention = alternatives[0]
        if intervention.disposition != "GENERATE_ONCE":
            return GenerationDecision(**base, disposition=intervention.disposition,
                                      intervention=intervention, rationale=(intervention.hypothesis,))
        proposed_candidate = next((c for c in candidates if c.candidate_id == intervention.candidate_id), None)
        if proposed_candidate is None:
            raise ValueError("intervention candidate is absent")
        baseline = inputs.baseline_request
        if baseline is None or baseline.request_input_hash != latest.request_hash:
            return GenerationDecision(**base, disposition="EVIDENCE_GAP",
                                      rationale=("repair needs the exact compiled baseline and actual delta contract",))
        from ai_video.production.generation_diagnosis import seal_intervention_comparison

        comparison = seal_intervention_comparison(intervention, baseline)
        if (proposed_candidate.recipe.comparison is not None
                and proposed_candidate.recipe.comparison != comparison):
            raise ValueError("caller comparison is not derived from exact compiled baseline")
    eligible = [a for a in assessments if a.compatible and a.executable
                and (intervention is not None and a.candidate_id == intervention.candidate_id
                     or intervention is None and (a.fit == "supported" or
                         a.fit == "unknown" and inputs.policy.allow_bounded_exploration))]
    if not eligible:
        resource_stops = {"GENERATION_FORBIDDEN", "TASK_SUBMIT_CEILING", "LOCAL_TOTAL_LIMIT",
                          "LOCAL_BATCH_REVIEW_REQUIRED", "LOCAL_RESOURCES_UNAVAILABLE"}
        supported = [a for a in assessments if a.fit == "supported" and a.compatible
                     and not resource_stops.intersection(a.reasons)]
        if supported:
            disposition = "CHANGE_PROVIDER_MODEL"
        elif any(a.compatible and a.executable for a in assessments):
            disposition = ("CAPABILITY_BOUNDARY" if all(a.fit == "unsupported" for a in assessments
                           if a.compatible and a.executable) else "INSUFFICIENT_EVIDENCE")
        else:
            disposition = "BLOCKED_EXECUTION"
        return GenerationDecision(**base, disposition=disposition,
                                  rationale=tuple(f"{a.candidate_id}: {a.fit}; {','.join(a.reasons)}" for a in assessments))
    def fit_rank(a):
        estimate = a.empirical
        # Observed cohort fit precedes exact-hash coverage. Cold start has no
        # probability; bounds are sampling uncertainty, not model guarantees.
        lower = estimate.interval_95[0] if estimate and estimate.interval_95 is not None else -1.
        return (-lower, len(a.failed_dimensions), len(a.unknown_dimensions))
    eligible.sort(key=lambda a: (fit_rank(a), a.candidate_id))
    if len(eligible) > 1 and fit_rank(eligible[0]) == fit_rank(eligible[1]):
        return GenerationDecision(**base, disposition="UNRESOLVED_TIE",
                                  rationale=("candidate evidence does not establish a unique fit",))
    chosen = next(c for c in candidates if c.candidate_id == eligible[0].candidate_id)
    selected_recipe = chosen.recipe
    if intervention is not None:
        selected_recipe = selected_recipe.model_copy(update={"comparison": comparison})
    elif selected_recipe.comparison is not None:
        raise ValueError("comparison is only valid for a diagnosed intervention")
    routing = resolver._bind_requirement(
        projection=projection, context=context, policy=policy,
        provider_profile=chosen.provider_profile, capabilities=chosen.capabilities,
        selected_capability_id=chosen.capability_id, output_requirement=chosen.output_requirement,
        lifecycle=lifecycle, compiler_contract=chosen.compiler_contract,
        continuity_routing=continuity_routing)
    if routing.provider_bound_request is None:
        return GenerationDecision(**base, disposition="BLOCKED_EXECUTION",
                                  rationale=(routing.decision.rationale,))
    from ai_video.production._shot_router_contracts import ProviderBoundVideoRequest

    bound = ProviderBoundVideoRequest.create(**{
        **{name: getattr(routing.provider_bound_request, name)
           for name in ProviderBoundVideoRequest.model_fields if name != "provider_bound_request_hash"},
        "generation_recipe": selected_recipe,
    })
    routing = RequirementRoutingResult(decision=routing.decision, provider_bound_request=bound)
    return GenerationDecision(**base, disposition="GENERATE_ONCE", selected_candidate_id=chosen.candidate_id,
                              routing=routing, intervention=intervention,
                              rationale=(f"{chosen.candidate_id}: {eligible[0].fit}; one bounded attempt, no quality guarantee",
                                         "explicit goal revision retains the old failed result; it is not a repair success"
                                         if goal_changed else "evidence and policy affect audit identity, not unrelated media semantics"),
                              revalidate_requirements=tuple(r.requirement_id for r in chosen.recipe.expressions
                                                            if r.level == "acceptance"))


from ai_video.production.generation_experience import (
    EmpiricalEstimate, GenerationExperience, GenerationFeatures,
    bind_experience_models, empirical_assessment, extract_generation_features,
)

bind_experience_models(GenerationCandidate)
DecisionInputs.model_rebuild()
CandidateAssessment.model_rebuild()
GenerationDecision.model_rebuild()
