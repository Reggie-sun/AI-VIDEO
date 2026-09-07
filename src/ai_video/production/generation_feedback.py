"""Common input producer for the Router's one-attempt generation decision.

Adapters expose capabilities and compile the chosen request. They do not choose
repairs. Evaluation remains an injected exact-evidence owner; this module never
invents a finding, human approval, execution permit, or activation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ai_video.production.generation_decision import (
    DecisionInputs, DecisionPolicy, ExecutionLimits, GenerationCandidate, InputConflict,
)
from ai_video.production.generation_diagnosis import (
    AttemptEvidence, Finding, Intervention, diagnose_exact_result, compare_compiled_requests,
)
from ai_video.production.generation_experience import (
    GenerationExperience, bind_experience_models, empirical_assessment, extract_generation_features,
)
from ai_video.production.generation_recipe import GenerationRecipe, RequirementExpression, SeedPolicy
from ai_video.production.hashing import canonical_sha256
from ai_video.production.shot_router import VideoGenerationResolver
from ai_video.production.video_compiler import ProviderRequirementUnsupported

bind_experience_models(GenerationCandidate)


@dataclass(frozen=True)
class RegisteredGenerationTarget:
    """Operator registration, not a per-Shot selected capability.

    Each entry exposes all its adapter's variants. Profile/compiler/output are
    existing sealed adapter contracts, never inferred from marketing names.
    """

    provider: object
    profile: object
    compiler_contract: object
    output_requirement: object


@dataclass(frozen=True)
class GenerationHistory:
    experiences: tuple[GenerationExperience, ...] = ()
    latest_attempt_hash: str | None = None
    baseline_request: object | None = None


@dataclass(frozen=True)
class PreparedGeneration:
    inputs: DecisionInputs
    decision: object
    compilation: object | None = None
    resolved_request: object | None = None
    provider: object | None = None
    execution_binding: object | None = None
    target_shot_id: str | None = None


def _expressions(acceptance, requirement):
    inventory = acceptance.profile_payload.get("generation_requirements")
    if not inventory:
        raise ValueError("selected acceptance owner has no generation requirement projection")
    payload = requirement.model_dump(mode="json")
    result = []
    for raw in inventory:
        rule = RequirementExpression.model_validate(raw)
        expressions = []
        for path in rule.intent_paths:
            if path.startswith("output_need.") or path == "audio_need":
                continue
            value = payload
            try:
                for key in path.split("."):
                    value = value[int(key)] if isinstance(value, list) else value[key]
            except (KeyError, IndexError, TypeError, ValueError):
                continue  # The compiler rejects the unsupported path.
            if isinstance(value, str) and value not in {"", "unspecified"}:
                expressions.append(value)
        result.append(rule.model_copy(update={"native_text": tuple(expressions)}))
    return tuple(sorted(result, key=lambda rule: rule.requirement_id))


def create_generation_candidates(*, projection, targets, acceptance, baseline=None):
    """Enumerate actual registered variants; Router owns compatibility/ranking."""
    expressions = _expressions(acceptance, projection.requirement)
    candidates = []
    providers = {}
    for target in targets:
        capabilities = target.provider.capabilities()
        for variant in capabilities.variants:
            candidate_id = f"{capabilities.provider_name}/{variant.capability_id}"
            if candidate_id in providers:
                raise ValueError("duplicate registered generation candidate")
            providers[candidate_id] = target.provider
            seed = int(canonical_sha256({"requirement": projection.requirement.requirement_hash,
                                         "candidate": candidate_id})[:8], 16) % (2**31 - 1)
            if (baseline is not None and baseline.provider_name == capabilities.provider_name
                    and baseline.model_id == variant.model_id and baseline.mode == variant.mode
                    and baseline.seed is not None and baseline.seed >= 0):
                seed = (baseline.seed + 1) % (2**31 - 1)
            recipe = GenerationRecipe(
                seed=SeedPolicy(kind="paired", value=seed) if variant.seed_supported
                else SeedPolicy(kind="uncontrolled"),
                profile_sha256=target.profile.profile_sha256,
                compiler_hash=target.compiler_contract.compiler_hash,
                requirement_hash=projection.requirement.requirement_hash,
                rubric_hash=acceptance.profile_content_hash, acceptance_policy=acceptance,
                expressions=expressions,
            )
            candidates.append(GenerationCandidate(
                candidate_id=candidate_id, provider_profile=target.profile,
                capabilities=capabilities, capability_id=variant.capability_id,
                compiler_contract=target.compiler_contract,
                output_requirement=target.output_requirement, recipe=recipe))
    if not candidates:
        raise ValueError("no video capabilities registered; use the non-video production path")
    return tuple(candidates), providers


def derive_generation_interventions(*, projection, candidates, history, policy):
    """Version 1: bounded sampling or evidence-backed reassessment, never prose repair.

    A reference incompatibility is a typed authoring fact. Empirical failures
    support boundary/strategy hypotheses; they do not prove a prompt fix.
    """
    evidence = tuple(e for experience in history.experiences for e in experience.evidence)
    latest = next((e for e in evidence if e.evidence_hash == history.latest_attempt_hash), None)
    conflicts = ()
    conditioning = projection.requirement.conditioning_compatibility
    if conditioning is not None:
        failed = tuple(name for name, value in conditioning.model_dump().items() if value is False)
        if failed:
            conflicts = (InputConflict(kind="reference", source_sha256=projection.projection_hash,
                         observation="conditioning compatibility failed: " + ", ".join(failed),
                         affected_requirements=tuple(r.requirement_id for r in candidates[0].recipe.expressions
                                                     if r.level == "acceptance"), next_owner="shot_authoring"),)
    if latest is None:
        return (), conflicts
    prior = next(x for x in history.experiences if latest in x.evidence)
    diagnosis = diagnose_exact_result(latest, evidence, prior.candidate.recipe)
    if not diagnosis.failed_requirements:
        return (), conflicts
    features = extract_generation_features(projection)
    estimates = [(c, empirical_assessment(c, features, history.experiences)) for c in candidates]
    current = next((c for c in candidates
                    if c.capabilities.provider_name == prior.candidate.capabilities.provider_name
                    and c.capability_id == prior.candidate.capability_id), None)
    if current is None:
        return (), conflicts
    current_estimate = next(e for c, e in estimates if c == current)
    # Cohort failures from other Shots inform ranking, not this Shot's retry
    # streak. A completed PASS breaks the streak; incomplete proof cannot be
    # counted as another quality failure.
    failure_streak = 0
    seen_attempts = set()
    comparable = set(current_estimate.evidence_hashes)
    for experience in reversed(history.experiences):
        for entry in reversed(experience.evidence):
            identity = (entry.task_id, entry.attempt_id, entry.request_hash)
            if entry.shot_id != latest.shot_id or identity in seen_attempts:
                continue
            seen_attempts.add(identity)
            if entry.evidence_hash not in comparable:
                break
            result = diagnose_exact_result(entry, evidence, experience.candidate.recipe)
            if "QUALITY_FAILURE" not in result.failure_classes:
                break
            failure_streak += 1
        else:
            continue
        break
    alternatives = [(c, e) for c, e in estimates if c != current and e.interval_95 is not None
                    and e.supported_artifacts and (current_estimate.interval_95 is None
                        or e.interval_95[0] > current_estimate.interval_95[1])]
    disposition = "GENERATE_ONCE"
    candidate = current
    purpose = "resample"
    changed = ("seed",) if current.recipe.seed.kind != "uncontrolled" else ()
    hypothesis = "One bounded independent sample tests whether this failure recurs; no prompt repair is inferred."
    if alternatives:
        # Selection between proposed Providers remains the Router's job. Emit
        # all evidence-backed alternatives; ties stop in the existing resolver.
        selected = alternatives
    else:
        selected = [(current, current_estimate)]
    proposals = []
    for candidate, estimate in selected:
        if alternatives:
            disposition, purpose, changed = "CHANGE_PROVIDER_MODEL", "production_repair", ("provider_name", "model_id")
            hypothesis = "A comparable Provider/model cohort has a higher observed whole-result success interval."
        elif failure_streak >= policy.repeated_failure_threshold:
            failed_dimensions = {r.dimension for r in current.recipe.expressions
                                 if r.requirement_id in current_estimate.failed_requirements}
            disposition = "SPLIT_SHOT" if len(failed_dimensions) > 1 else "CAPABILITY_BOUNDARY"
            purpose, changed = "production_repair", ("generation_strategy",)
            hypothesis = "Repeated comparable failures require authoring/recipe feasibility review before another sample."
        elif history.baseline_request is None:
            return (), conflicts
        proposals.append(Intervention(
            intervention_id="feedback-v1-" + canonical_sha256({"candidate": candidate.candidate_id,
                                "disposition": disposition, "closes": diagnosis.failed_requirements})[:20],
            candidate_id=candidate.candidate_id, purpose=purpose, disposition=disposition,
            closes=diagnosis.failed_requirements,
            protected_requirements=diagnosis.preserved_requirements,
            support=tuple(sorted({latest.evidence_hash, *estimate.evidence_hashes})),
            changed_variables=changed, held_constants=(),
            uncontrolled_variables=("seed",) if prior.candidate.recipe.seed.kind == "uncontrolled"
                or candidate.recipe.seed.kind == "uncontrolled" else (),
            regression_risks=diagnosis.preserved_requirements,
            hypothesis=hypothesis, confidence_basis="generation-feedback-policy/1; exact evaluator observations",
            improvement_prediction="Target requirements become PASS with required proof; all protected requirements remain PASS.",
            falsification_prediction="Any target remains FAIL or a protected requirement becomes FAIL.",
            insufficient_evidence_condition="Missing/stale/stage-incompatible proof is undetermined, never a successful repair.",
            resample_limit=1 if purpose == "resample" else None,
        ))
    return tuple(proposals), conflicts


class GenerationFeedbackOrchestrator:
    """Reopen canonical context/history for every decision, compile only its winner."""

    def __init__(self, *, targets, context_loader: Callable, history_loader: Callable,
                 policy: DecisionPolicy):
        self.targets = tuple(targets)
        self.context_loader = context_loader
        self.history_loader = history_loader
        self.policy = policy

    def prepare(self, *, limits: ExecutionLimits) -> PreparedGeneration:
        # The existing authoring/reader owner supplies projection/context,
        # routing policy, lifecycle and active acceptance; never cached here.
        current = self.context_loader()
        if current.get("production_task_id", limits.task_id) != limits.task_id:
            raise ValueError("production component cannot reset its parent task identity")
        history = self.history_loader()
        submitted = {"local": set(), "remote": set()}
        for experience in history.experiences:
            variant = next(v for v in experience.candidate.capabilities.variants
                           if v.capability_id == experience.candidate.capability_id)
            for entry in experience.evidence:
                if entry.task_id == limits.task_id and entry.outcome != "not_submitted":
                    submitted[variant.execution_kind.value].add((entry.attempt_id, entry.request_hash))
        # Reopened history can tighten an external limit projection, never
        # silently reset it. The existing paid/local guards remain authoritative.
        limits = limits.model_copy(update={
            "paid_submits_used": max(limits.paid_submits_used, len(submitted["remote"])),
            "local_total_used": max(limits.local_total_used, len(submitted["local"])),
            "local_batch_used": max(limits.local_batch_used, len(submitted["local"]))
                if limits.batch_review_evidence_hash is None else limits.local_batch_used,
        })
        candidates, providers = create_generation_candidates(
            projection=current["projection"], targets=self.targets,
            acceptance=current["acceptance"], baseline=history.baseline_request)
        interventions, conflicts = derive_generation_interventions(
            projection=current["projection"], candidates=candidates, history=history, policy=self.policy)
        evidence = {e.evidence_hash: e for x in history.experiences for e in x.evidence}
        historical = {x.candidate.scope_hash: x.candidate for x in history.experiences}
        projection = current["projection"]
        inputs = DecisionInputs(
            projection_hash=projection.projection_hash,
            facts_hash=canonical_sha256(projection.requirement.model_dump(
                mode="json", exclude={"requirement_id", "requirement_hash"})),
            rubric_hash=current["acceptance"].profile_content_hash, policy=self.policy, limits=limits,
            candidates=candidates, evidence=tuple(evidence.values()), latest_attempt_hash=history.latest_attempt_hash,
            interventions=interventions, conflicts=conflicts, historical_recipes=tuple(historical.values()),
            baseline_request=history.baseline_request,
            experiences=history.experiences, feature_scope=extract_generation_features(projection),
        )
        arguments = {name: current[name] for name in ("projection", "context", "policy", "lifecycle")}
        if "continuity_routing" in current:
            arguments["continuity_routing"] = current["continuity_routing"]
        decision = VideoGenerationResolver().resolve_requirement(**arguments, inputs=inputs)
        if decision.disposition != "GENERATE_ONCE":
            return PreparedGeneration(inputs, decision, target_shot_id=current["context"].target_shot_id)
        provider = providers[decision.selected_candidate_id]
        compilation = provider.compile_request(decision.routing.provider_bound_request, projection.requirement)
        if isinstance(compilation, ProviderRequirementUnsupported):
            return PreparedGeneration(inputs, decision, compilation=compilation,
                                      target_shot_id=current["context"].target_shot_id)
        resolved = provider.resolve(compilation.request)
        from ai_video.production.generation_execution import GenerationDecisionExecutionBinding

        binding = GenerationDecisionExecutionBinding.create(
            **arguments, inputs=inputs, decision=decision, compiled_request=resolved)
        return PreparedGeneration(inputs, decision, compilation, resolved, provider, binding,
                                  current["context"].target_shot_id)

    def start(self, *, committer, attempt_id, limits):
        """Prepare from fresh inputs, then enter the sole durable execution owner.

        This persists a request only. Submit still needs the existing local or
        paid gates and an exact one-use permit; no automatic Provider effect.
        """
        from ai_video.production.video_generation import VideoGenerationService

        prepared = self.prepare(limits=limits)
        if prepared.execution_binding is not None:
            VideoGenerationService(committer=committer, provider=prepared.provider).start(
                attempt_id=attempt_id, request=prepared.resolved_request,
                execution_binding=prepared.execution_binding)
        return prepared

    @classmethod
    def for_project(cls, *, committer, targets, context_loader, policy):
        """Use the standard project loader and committer's durable feedback store.

        The authoring adapter receives the freshly loaded canonical project and
        returns its verified planning projection and routing context. Creative
        choices and evaluator findings are never reconstructed from filenames.
        """
        from ai_video.production.project import load_production_project

        def current():
            loaded = load_production_project(committer.project_root / "project.yaml")
            result = dict(context_loader(loaded))
            from ai_video.production.production_strategy_reader import selected_shot_generation_acceptance

            target_id = result["context"].target_shot_id
            acceptance = selected_shot_generation_acceptance(loaded, target_id)
            shot = next(s for s in loaded.shots if s.shot_id == target_id)
            if shot.production_intent is not None:
                raise ValueError("production intent must be resolved before generation planning")
            if shot.production_lineage is not None:
                result["production_task_id"] = shot.production_lineage.task_id
            if acceptance is None or not acceptance.profile_payload.get("generation_requirements"):
                raise ValueError("current QA owner has no generation requirement projection")
            if result.get("acceptance", acceptance) != acceptance:
                raise ValueError("generation acceptance differs from current QA owner")
            from ai_video.production.generation_evaluation import require_generation_evaluation_authorities

            require_generation_evaluation_authorities(loaded.qa_policy, acceptance)
            result["acceptance"] = acceptance
            return result

        def history():
            experiences = committer.read_generation_experiences()
            current_context = current()
            shot_id = current_context["context"].target_shot_id
            matching = [e for x in experiences for e in x.evidence if e.shot_id == shot_id]
            submitted = [e for e in matching if e.outcome != "not_submitted"]
            effective = submitted or matching
            latest = effective[-1] if effective else None
            # The persisted binding is the compiled baseline owner. Never
            # synthesize a baseline from the current prompt or recipe.
            baseline = None
            if latest is not None:
                _, state = VideoGenerationService(committer=committer, provider=None)._state(latest.attempt_id)
                request = committer._reopen_video_request(state.request)
                if request.activation_scope is not None:
                    baseline = request.activation_scope.request
            return GenerationHistory(experiences, latest.evidence_hash if latest else None, baseline)

        from ai_video.production.video_generation import VideoGenerationService

        return cls(targets=targets, context_loader=current, history_loader=history, policy=policy)

    @staticmethod
    def record_evaluation(*, committer, prepared, attempt_id, outcome, artifact_sha256=None,
                          evaluation_sources=(), runtime_reason=None):
        """Persist exact evaluator proof for automatic reuse on the next prepare."""
        evidence = project_attempt_evidence(
            prepared=prepared, task_id=prepared.inputs.limits.task_id,
            shot_id=prepared.execution_binding.context.target_shot_id,
            attempt_id=attempt_id, outcome=outcome, artifact_sha256=artifact_sha256,
            findings=tuple(f for source in evaluation_sources for f in source.project_findings()),
            runtime_reason=runtime_reason)
        candidate = next(c for c in prepared.inputs.candidates
                         if c.candidate_id == prepared.decision.selected_candidate_id)
        experience = GenerationExperience(projection=prepared.execution_binding.projection,
                                         candidate=candidate, evidence=(evidence,),
                                         evaluation_sources=tuple(evaluation_sources))
        return committer.record_generation_experience(attempt_id=attempt_id, experience=experience)


def project_attempt_evidence(*, prepared, task_id, shot_id, attempt_id, outcome,
                             artifact_sha256=None, findings: tuple[Finding, ...] = (), runtime_reason=None):
    """Join an exact evaluator result to the actual compiled attempt identity."""
    if prepared.compilation is None or isinstance(prepared.compilation, ProviderRequirementUnsupported):
        raise ValueError("attempt evidence requires an actual compiled request")
    request = prepared.compilation.request
    if request.target_shot_id != shot_id or prepared.inputs.limits.task_id != task_id:
        raise ValueError("evaluation target does not match compiled attempt")
    candidate = next(c for c in prepared.inputs.candidates if c.candidate_id == prepared.decision.selected_candidate_id)
    intervention = prepared.decision.intervention
    return AttemptEvidence(
        task_id=task_id, shot_id=shot_id, attempt_id=attempt_id,
        recipe_scope_hash=candidate.scope_hash, facts_hash=prepared.inputs.facts_hash,
        rubric_hash=prepared.inputs.rubric_hash, request_hash=request.request_input_hash,
        artifact_sha256=artifact_sha256, outcome=outcome, findings=findings, runtime_reason=runtime_reason,
        intervention_id=intervention.intervention_id if intervention else None,
        intervention_semantic_hash=intervention.semantic_hash if intervention else None,
        actual_delta=compare_compiled_requests(prepared.inputs.baseline_request, request)["changed_variables"]
            if intervention and prepared.inputs.baseline_request is not None else (),
    )


def record_attempt_evaluation(*, committer, attempt_id, evaluation_sources=(), analysis_proof=None):
    """Join evaluation to a reopened attempt, including after process restart.

    Runtime outcome comes from the Manifest; sources cannot relabel UNKNOWN as
    a quality failure. This function neither calls a Provider nor activates media.
    """
    from ai_video.production.models import StateCommitStatus, VideoAttemptPhase
    from ai_video.production.video_generation import VideoGenerationService

    attempt, state = VideoGenerationService(committer=committer, provider=None)._state(attempt_id)
    if state.execution_binding is None:
        raise ValueError("feedback requires a durable generation decision")
    binding = committer._reopen_generation_execution_binding(state.execution_binding)
    resolved = committer._reopen_video_request(state.request)
    candidate = next(c for c in binding.inputs.candidates
                     if c.candidate_id == binding.decision.selected_candidate_id)
    pointer = state.local_fetch_receipt or state.fetch_receipt
    artifact_sha256 = None
    reason = None
    if attempt.status is StateCommitStatus.OUTCOME_UNKNOWN:
        outcome = "unknown_outcome"
    elif attempt.status is StateCommitStatus.FAILED:
        outcome, reason = "runtime_failure", "Durable video attempt failed; inspect its execution receipts."
    elif pointer is not None:
        outcome = "media"
        artifact_sha256 = pointer.artifact_sha256
    elif state.phase is VideoAttemptPhase.REQUEST:
        outcome = "not_submitted"
    else:
        raise ValueError("unfinished generation requires its next durable action, not evaluation")
    if outcome != "media" and evaluation_sources:
        raise ValueError("no-media attempt cannot consume evaluator findings")
    intervention = binding.decision.intervention
    evidence = AttemptEvidence(
        task_id=binding.inputs.limits.task_id, shot_id=binding.context.target_shot_id,
        attempt_id=attempt_id, recipe_scope_hash=candidate.scope_hash,
        facts_hash=binding.inputs.facts_hash, rubric_hash=binding.inputs.rubric_hash,
        request_hash=resolved.request_input_hash, artifact_sha256=artifact_sha256,
        outcome=outcome, runtime_reason=reason,
        findings=tuple(f for source in evaluation_sources for f in source.project_findings()),
        intervention_id=intervention.intervention_id if intervention else None,
        intervention_semantic_hash=intervention.semantic_hash if intervention else None,
        actual_delta=compare_compiled_requests(binding.inputs.baseline_request,
            resolved.activation_scope.request)["changed_variables"]
            if intervention and binding.inputs.baseline_request is not None else (),
    )
    experience = GenerationExperience(projection=binding.projection, candidate=candidate,
        evidence=(evidence,), evaluation_sources=tuple(evaluation_sources))
    committer.record_generation_experience(attempt_id=attempt_id, experience=experience, analysis_proof=analysis_proof)
    return experience
