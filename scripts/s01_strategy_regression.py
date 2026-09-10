"""Private read-only S01 recovery observation; never a workflow PASS oracle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.planning.production_strategy import ProductionStrategyPolicy
from ai_video.production.generation_diagnosis import diagnose_exact_result
from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator
from ai_video.production.hashing import canonical_sha256
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production_planning import ProductionPlanningService


def _invalid(message):
    return AiVideoError(code=ErrorCode.PRODUCTION_PROJECT_INVALID, user_message=message)


def inspect_strategy(*, committer, shot_id, targets):
    """Observe the real selected authoring; do not create missing input or evidence."""
    loaded = load_production_project(committer.project_root / "project.yaml")
    shot = next((s for s in loaded.shots if s.shot_id == shot_id), None)
    if shot is None:
        raise _invalid("Recovery target is not a selected Shot.")
    service = ProductionPlanningService(committer=committer, targets=targets,
        policy=ProductionStrategyPolicy(allow_generation_exploration=True))
    capabilities = service._capabilities()
    result = {"entrypoint": "ProductionPlanningService.prepare",
        "generation_available": capabilities.generation_available,
        "generation_targets_hash": capabilities.generation_targets_hash,
        "decision": None, "blockers": []}
    if shot.production_intent is None and shot.production_lineage is None:
        result["blockers"].append("missing_production_intent")
        return result
    decision = service.prepare(parent_shot_id=shot_id)
    result["decision"] = {
        "input_hash": decision.input_hash, "decision_hash": decision.decision_hash,
        "disposition": decision.disposition, "reasons": list(decision.reasons),
        "selected_candidate_hash": decision.selected.candidate_hash if decision.selected else None,
        "selected_generation_count": decision.selected.new_generation_count if decision.selected else None,
        "candidates": [{"candidate_hash": c.candidate_hash,
            "coverage_id": c.coverage.coverage_id,
            "operations": [o.value for o in c.operations], "blockers": list(c.blockers),
            "new_generation_count": c.new_generation_count,
            "units": [{"component_id": u.component.component_id,
                "requirement_ids": list(u.component.requirement_ids),
                "source": u.source.model_dump(mode="json") if u.source else None}
                for u in c.units]} for c in decision.candidates],
    }
    return result


def inspect_recovery(*, project_root, shot_id, source_attempt_id, source_sha256,
                     targets, context_loader, limits, generation_policy):
    """Read exact source facts and current Feedback, independently of source selection.

    The caller supplies current authoring through the existing Feedback seam.
    This diagnostic does not mint input qualifications or automatically accept
    a workflow. In particular, a valid source history is not SourceUseEvidence.
    """
    committer = ProductionStateCommitter(Path(project_root))
    loaded = load_production_project(committer.project_root / "project.yaml")
    before = loaded.manifest
    budget = (committer._reopen_paid_budget(before.active_paid_provider_budget)
              if before.active_paid_provider_budget else None)
    shot = next((s for s in loaded.shots if s.shot_id == shot_id), None)
    if shot is None:
        raise _invalid("Recovery target is not a selected Shot.")
    attempt = committer._video_attempt(before, source_attempt_id)
    state = attempt.video_generation_state
    pointer = state.local_fetch_receipt or state.fetch_receipt
    if pointer is None or pointer.artifact_sha256 != source_sha256:
        raise _invalid("Recovery source does not match exact fetched bytes.")
    experiences = committer.read_generation_experiences()
    evidence = tuple(e for x in experiences for e in x.evidence)
    source_pairs = [(x, e) for x in experiences for e in x.evidence
        if e.attempt_id == source_attempt_id and e.shot_id == shot_id
        and e.outcome == "media" and e.artifact_sha256 == source_sha256]
    if not source_pairs:
        raise _invalid("Recovery source has no exact canonical media evaluation.")
    source_experience, source_evidence = source_pairs[-1]
    diagnosis = diagnose_exact_result(source_evidence, evidence, source_experience.candidate.recipe)
    assets = [a.asset_id for a in loaded.registry.assets if a.sha256 == source_sha256]
    strategy = inspect_strategy(committer=committer, shot_id=shot_id, targets=targets)
    feedback = {"entrypoint": "GenerationFeedbackOrchestrator.for_project.prepare",
                "disposition": None, "blockers": [],
                "execution_limits_authority": "supplied_snapshot_not_current_authorization",
                "current_authorization_verified": False,
                "supplied_limits_hash": canonical_sha256(limits.model_dump(mode="json")),
                "supplied_policy_hash": canonical_sha256(generation_policy.model_dump(mode="json"))}
    recovery_required = any(a.status.value in {"outcome_unknown", "interrupted"}
                            for a in before.attempts)
    if recovery_required:
        feedback["blockers"].append("canonical_recovery_required")
    elif not targets:
        feedback["blockers"].append("no_registered_generation_targets")
    elif shot.production_intent is not None:
        feedback["blockers"].append("production_parent_requires_materialized_component")
    else:
        def current(project):
            context = dict(context_loader(project))
            if context["context"].target_shot_id != shot_id:
                raise _invalid("Feedback context identifies another Shot.")
            return context

        prepared = GenerationFeedbackOrchestrator.for_project(committer=committer,
            targets=targets, context_loader=current, policy=generation_policy).prepare(limits=limits)
        inputs, decision = prepared.inputs, prepared.decision
        latest = next((e for e in inputs.evidence if e.evidence_hash == inputs.latest_attempt_hash), None)
        feedback.update({
            "disposition": decision.disposition, "decision_hash": decision.decision_hash,
            "input_hash": inputs.snapshot_hash, "rationale": list(decision.rationale),
            "latest_attempt_hash": inputs.latest_attempt_hash,
            "latest_attempt_id": latest.attempt_id if latest else None,
            "baseline_request_hash": inputs.baseline_request.request_input_hash if inputs.baseline_request else None,
            "evidence_hashes": [e.evidence_hash for e in inputs.evidence],
            "paid_submits_used": inputs.limits.paid_submits_used,
            "paid_submit_ceiling": inputs.limits.paid_submit_ceiling,
            "generation_forbidden": inputs.limits.generation_forbidden,
            "diagnosis": decision.diagnosis.model_dump(mode="json") if decision.diagnosis else None,
            "assessments": [a.model_dump(mode="json") for a in decision.assessments],
        })
    # A changed live root invalidates this observation; do not repair or retry it.
    if committer._read_manifest() != before:
        raise _invalid("Production state changed during recovery observation.")
    return {
        "status": "recovery_required" if recovery_required else
            "integration_incomplete" if strategy["blockers"] or feedback["blockers"] else "decision_observed",
        "workflow_acceptance": "not_evaluated",
        "budget_observation": {"content_hash": budget.content_hash,
            "available_microunits": budget.available_microunits,
            "blocked": budget.blocked} if budget else None,
        "manifest_revision": before.manifest_revision,
        "manifest_hash": canonical_sha256(before.model_dump(mode="json")),
        "parent_shot_hash": shot.content_hash,
        "qa_policy_hash": loaded.qa_policy.content_hash if loaded.qa_policy else None,
        "production_allocations": len(loaded.qa_policy.production_allocations) if loaded.qa_policy else 0,
        "production_source_evidence": len(loaded.qa_policy.production_source_evidence) if loaded.qa_policy else 0,
        "source": {"attempt_id": source_attempt_id, "artifact_sha256": source_sha256,
            "status": attempt.status.value, "registered_asset_ids": assets,
            "qualified_reuse": None, "diagnosis": diagnosis.model_dump(mode="json"),
            "evidence": [{"evidence_hash": e.evidence_hash,
                "findings": [f.model_dump(mode="json") for f in e.findings]} for _, e in source_pairs]},
        "strategy": strategy, "feedback": feedback,
    }


def _forbidden(*args, **kwargs):
    raise _invalid("Recovery observation forbids transport, credentials and media access.")


class _NoTransport:
    request = staticmethod(_forbidden)
    stream = staticmethod(_forbidden)


def main(argv=None):
    """Explicit configuration; no implicit renewal, upload or execution flags."""
    from ai_video.planning import VideoPlanner, VideoPlanningRequest
    from ai_video.planning.generation_feedback_context import require_feedback_context
    from ai_video.production.generation_feedback import RegisteredGenerationTarget
    from ai_video.production.vidu import ViduVideoProvider
    from ai_video.production.vidu_profile import ViduProviderProfile

    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("project-root", "source-attempt", "source-sha256", "context-attempt",
                 "planning-request", "provider-profile"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--shot-id", default="S01")
    args = parser.parse_args(argv)
    try:
        committer = ProductionStateCommitter(Path(args.project_root))
        loaded = load_production_project(committer.project_root / "project.yaml")
        state = committer._video_attempt(loaded.manifest, args.context_attempt).video_generation_state
        if state.execution_binding is None:
            raise _invalid("Context attempt has no canonical generation binding.")
        binding = committer._reopen_generation_execution_binding(state.execution_binding)
        request = VideoPlanningRequest.model_validate_json(Path(args.planning_request).read_bytes())
        plan = VideoPlanner().plan(request)
        profile = ViduProviderProfile.model_validate_json(Path(args.provider_profile).read_bytes())
        candidate = next(c for c in binding.inputs.candidates
                         if c.candidate_id == binding.decision.selected_candidate_id)
        if profile.pointer() != candidate.provider_profile:
            raise _invalid("Provider profile differs from the exact context binding.")
        provider = ViduVideoProvider(profile=profile, transport=_NoTransport(), credential=_forbidden,
                                     image_resolver=_forbidden)
        target = RegisteredGenerationTarget(provider, profile.pointer(), candidate.compiler_contract,
                                            candidate.output_requirement)

        def context(project):
            value = require_feedback_context(loaded=project, planning_request=request, video_plan=plan,
                context=binding.context, routing_policy=binding.policy, lifecycle=binding.lifecycle)
            if value["projection"] != binding.projection:
                raise _invalid("Planning request differs from the canonical context binding.")
            if binding.continuity_routing is not None:
                value["continuity_routing"] = binding.continuity_routing
            return value

        report = inspect_recovery(project_root=args.project_root, shot_id=args.shot_id,
            source_attempt_id=args.source_attempt, source_sha256=args.source_sha256,
            targets=(target,), context_loader=context, limits=binding.inputs.limits,
            generation_policy=binding.inputs.policy)
        report["context_provenance"] = {
            "attempt_id": args.context_attempt,
            "binding": state.execution_binding.model_dump(mode="json"),
            "limits_policy_routing_source": "stored_context_attempt_binding",
            "current_authorization_verified": False,
        }
    except (AiVideoError, ValueError, OSError, StopIteration):
        print(json.dumps({"status": "invalid_input", "workflow_acceptance": "not_evaluated"}))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
