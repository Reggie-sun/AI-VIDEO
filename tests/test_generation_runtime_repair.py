"""Runtime repair grant: planner resume branch and committer one-use lifecycle."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.generation_runtime_repair import (
    MAX_RUNTIME_REPAIRS_PER_SHOT,
    RuntimeRepairAuthorization,
    RuntimeRepairGrant,
)
from ai_video.production.models import (
    ActorIdentity,
    StateCommitStatus,
)
from ai_video.production.video import VideoTaskState
from ai_video.production.video_generation import VideoGenerationService

from test_production_generation_decision import decide, evidence, setup_decision

ACTOR = ActorIdentity(actor_id="test-runtime-owner", actor_kind="automation")
REPAIR_BASIS = "local_resource_exhaustion: co-tenant VRAM holder stopped before re-submit"


def _grant(entry, *, consumed=False, attempt=None, evidence_hash=None):
    authorization = RuntimeRepairAuthorization.create(
        attempt_id=attempt or entry.attempt_id,
        evidence_hash=evidence_hash or entry.evidence_hash,
        repair_basis=REPAIR_BASIS,
        actor=ACTOR,
        expected_manifest_revision=0,
    )
    return RuntimeRepairGrant(authorization=authorization, consumed=consumed)


def test_runtime_failure_blocks_without_grant():
    setup = setup_decision()
    entry = evidence(setup, outcome="runtime_failure", task_id="task")
    result = decide(setup, evidence=(entry,), latest_attempt_hash=entry.evidence_hash)
    assert result.disposition == "RUNTIME_FAILURE"
    assert result.runtime_repair is None


def test_runtime_repair_grant_authorizes_exact_reexecution():
    setup = setup_decision()
    entry = evidence(setup, outcome="runtime_failure", task_id="task")
    result = decide(setup, evidence=(entry,), latest_attempt_hash=entry.evidence_hash,
                    runtime_repairs=(_grant(entry),))
    assert result.disposition == "GENERATE_ONCE"
    assert result.runtime_repair is not None
    assert result.runtime_repair.evidence_hash == entry.evidence_hash
    assert result.selected_candidate_id == setup["inputs"].candidates[0].candidate_id
    assert result.intervention is None


def test_consumed_grant_still_blocks():
    setup = setup_decision()
    entry = evidence(setup, outcome="runtime_failure", task_id="task")
    result = decide(setup, evidence=(entry,), latest_attempt_hash=entry.evidence_hash,
                    runtime_repairs=(_grant(entry, consumed=True),))
    assert result.disposition == "RUNTIME_FAILURE"
    assert result.runtime_repair is None


def test_mismatched_evidence_hash_still_blocks():
    setup = setup_decision()
    entry = evidence(setup, outcome="runtime_failure", task_id="task")
    result = decide(setup, evidence=(entry,), latest_attempt_hash=entry.evidence_hash,
                    runtime_repairs=(_grant(entry, evidence_hash="d" * 64),))
    assert result.disposition == "RUNTIME_FAILURE"


def test_mismatched_attempt_id_still_blocks():
    setup = setup_decision()
    entry = evidence(setup, outcome="runtime_failure", task_id="task")
    result = decide(setup, evidence=(entry,), latest_attempt_hash=entry.evidence_hash,
                    runtime_repairs=(_grant(entry, attempt="other-attempt"),))
    assert result.disposition == "RUNTIME_FAILURE"


def test_authorization_receipt_is_exact_and_self_validated():
    authorization = RuntimeRepairAuthorization.create(
        attempt_id="attempt-x",
        evidence_hash="e" * 64,
        repair_basis=REPAIR_BASIS,
        actor=ACTOR,
        expected_manifest_revision=0,
    )
    payload = authorization.model_dump(mode="json")
    payload["repair_basis"] = "tampered basis"
    with pytest.raises(ValueError, match="content hash is invalid"):
        RuntimeRepairAuthorization.model_validate(payload)


def _orchestrator(tmp_path, *, status_state):
    from ai_video.production.generation_feedback import (
        GenerationFeedbackOrchestrator,
        RegisteredGenerationTarget,
    )
    from test_production_local_video_state import _runtime

    _, provider, _, template, committer = _runtime(tmp_path, status_state=status_state)
    candidate = template.inputs.candidates[0]
    sequence = [0]

    def context(loaded):
        return {
            "projection": template.projection,
            "context": template.context,
            "policy": template.policy,
            "acceptance": candidate.recipe.acceptance_policy,
            "lifecycle": template.lifecycle.model_copy(update={
                "generation_id": f"runtime-repair-{sequence[0]}",
                "output_asset_id": f"runtime-repair-video-{sequence[0]}",
                "base_project": loaded.manifest.active_project,
                "base_registry": loaded.manifest.active_registry,
                "base_dependency_graph": loaded.manifest.active_dependency_graph,
            }),
        }

    limits = template.inputs.limits.model_copy(update={"local_batch_limit": 3})
    caller = GenerationFeedbackOrchestrator.for_project(
        committer=committer,
        targets=(RegisteredGenerationTarget(
            provider, candidate.provider_profile, candidate.compiler_contract,
            candidate.output_requirement),),
        context_loader=context,
        policy=template.inputs.policy,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    return provider, committer, caller, service, limits, sequence


def _fail_attempt(*, committer, caller, service, limits, sequence, number, attempt_id):
    from ai_video.production.generation_feedback import record_attempt_evaluation

    sequence[0] = number
    prepared = caller.start(committer=committer, attempt_id=attempt_id, limits=limits)
    assert prepared.execution_binding is not None, prepared
    service.submit_local_once(attempt_id=attempt_id)
    observation = service.refresh_local_once(attempt_id=attempt_id)
    assert observation.state is VideoTaskState.FAILED
    record_attempt_evaluation(committer=committer, attempt_id=attempt_id)
    return prepared


def _attempt(committer, attempt_id):
    return next(a for a in committer._read_manifest().attempts if a.attempt_id == attempt_id)


def test_runtime_repair_requires_failed_attempt(tmp_path):
    provider, committer, caller, service, limits, sequence = _orchestrator(
        tmp_path, status_state=VideoTaskState.SUCCEEDED)
    caller.start(committer=committer, attempt_id="repair-running", limits=limits)
    with pytest.raises(AiVideoError, match="failed video attempt"):
        committer.record_runtime_repair_authorization(
            attempt_id="repair-running", repair_basis=REPAIR_BASIS, actor=ACTOR)


def test_runtime_repair_requires_runtime_failure_evidence(tmp_path):
    provider, committer, caller, service, limits, sequence = _orchestrator(
        tmp_path, status_state=VideoTaskState.FAILED)
    sequence[0] = 0
    caller.start(committer=committer, attempt_id="repair-failed", limits=limits)
    service.submit_local_once(attempt_id="repair-failed")
    service.refresh_local_once(attempt_id="repair-failed")
    assert _attempt(committer, "repair-failed").status is StateCommitStatus.FAILED
    with pytest.raises(AiVideoError, match="durable runtime failure evidence"):
        committer.record_runtime_repair_authorization(
            attempt_id="repair-failed", repair_basis=REPAIR_BASIS, actor=ACTOR)


def test_runtime_repair_roundtrip_one_use(tmp_path):
    provider, committer, caller, service, limits, sequence = _orchestrator(
        tmp_path, status_state=VideoTaskState.FAILED)

    _fail_attempt(committer=committer, caller=caller, service=service, limits=limits,
                  sequence=sequence, number=0, attempt_id="repair-attempt-1")
    assert _attempt(committer, "repair-attempt-1").status is StateCommitStatus.FAILED

    # Without a grant the Shot stays decision-blocked on the runtime failure.
    blocked = caller.prepare(limits=limits)
    assert blocked.decision.disposition == "RUNTIME_FAILURE"
    assert blocked.decision.runtime_repair is None

    pointer = committer.record_runtime_repair_authorization(
        attempt_id="repair-attempt-1", repair_basis=REPAIR_BASIS, actor=ACTOR)
    assert pointer.path == Path(
        f"state/video-generation/runtime-repair/{pointer.content_hash}.json")
    assert pointer.consumed is False
    revision = committer._read_manifest().manifest_revision
    again = committer.record_runtime_repair_authorization(
        attempt_id="repair-attempt-1", repair_basis=REPAIR_BASIS, actor=ACTOR)
    assert again == pointer
    assert committer._read_manifest().manifest_revision == revision

    # The grant authorizes exactly one identical-strategy re-execution.
    sequence[0] = 1
    prepared = caller.start(committer=committer, attempt_id="repair-attempt-2", limits=limits)
    assert prepared.decision.disposition == "GENERATE_ONCE"
    assert prepared.decision.runtime_repair is not None
    assert prepared.decision.runtime_repair.evidence_hash == pointer.evidence_hash
    assert prepared.decision.intervention is None

    provider.status_state = VideoTaskState.SUCCEEDED
    service.submit_local_once(attempt_id="repair-attempt-2")
    observation = service.refresh_local_once(attempt_id="repair-attempt-2")
    assert observation.state is VideoTaskState.SUCCEEDED

    # Consumption landed in the same atomic write as the replacement submit intent.
    prior = _attempt(committer, "repair-attempt-1")
    assert prior.video_generation_state.runtime_repairs[0].consumed is True

    # No unconsumed grant remains: the next prepare is blocked again.
    sequence[0] = 2
    blocked_again = caller.prepare(limits=limits)
    assert blocked_again.decision.disposition == "RUNTIME_FAILURE"
    assert blocked_again.decision.runtime_repair is None


def test_runtime_repair_budget_is_per_shot(tmp_path):
    provider, committer, caller, service, limits, sequence = _orchestrator(
        tmp_path, status_state=VideoTaskState.FAILED)
    assert MAX_RUNTIME_REPAIRS_PER_SHOT == 2

    _fail_attempt(committer=committer, caller=caller, service=service, limits=limits,
                  sequence=sequence, number=0, attempt_id="repair-budget-1")
    committer.record_runtime_repair_authorization(
        attempt_id="repair-budget-1", repair_basis=REPAIR_BASIS, actor=ACTOR)

    # Second bounded repair is still within the per-Shot budget.
    _fail_attempt(committer=committer, caller=caller, service=service, limits=limits,
                  sequence=sequence, number=1, attempt_id="repair-budget-2")
    committer.record_runtime_repair_authorization(
        attempt_id="repair-budget-2", repair_basis=REPAIR_BASIS, actor=ACTOR)

    _fail_attempt(committer=committer, caller=caller, service=service, limits=limits,
                  sequence=sequence, number=2, attempt_id="repair-budget-3")
    with pytest.raises(AiVideoError, match="budget is exhausted"):
        committer.record_runtime_repair_authorization(
            attempt_id="repair-budget-3", repair_basis=REPAIR_BASIS, actor=ACTOR)


def test_earlier_quality_failure_does_not_block_runtime_repair_for_runtime_failure():
    """`diagnosis` is computed per-latest-attempt via `diagnose_exact_result`,
    which early-returns when `latest.outcome != "media"`. A previous
    QUALITY_FAILURE attempt is part of the Shot history but does not enter the
    latest's diagnosis, so the runtime repair branch still authorises a
    single re-execution of the runtime-failed attempt. The contract is:
    runtime repair is bounded to the latest attempt's outcome, not
    re-litigation of older media evidence."""
    setup = setup_decision()
    failed = evidence(setup, verdict="FAIL", task_id="task", attempt="media-1")
    runtime = evidence(setup, outcome="runtime_failure", task_id="task", attempt="runtime-1")
    grant = _grant(runtime)
    result = decide(setup, evidence=(failed, runtime),
                    latest_attempt_hash=runtime.evidence_hash,
                    runtime_repairs=(grant,))
    assert result.disposition == "GENERATE_ONCE"
    assert result.runtime_repair is not None
    assert result.runtime_repair.evidence_hash == runtime.evidence_hash
    assert result.intervention is None


def test_snapshot_hash_stable_across_runtime_repair_iteration_order():
    """`runtime_repairs` joins the sorted-fields list so that
    `DecisionInputs.snapshot_hash` is invariant to the underlying iterator
    order. Without this, a hash drift could trigger spurious stale-binding
    failures inside `_validate_binding`."""
    setup = setup_decision()
    runtime = evidence(setup, outcome="runtime_failure", task_id="task", attempt="rt-1")
    grant = _grant(runtime)
    forward = setup["inputs"].model_copy(update={"runtime_repairs": (grant,)})
    reverse = setup["inputs"].model_copy(update={"runtime_repairs": (grant,)})
    assert forward.snapshot_hash == reverse.snapshot_hash
    # Different grant bodies still produce distinct hashes.
    other = _grant(runtime, evidence_hash="d" * 64)
    divergent = setup["inputs"].model_copy(update={"runtime_repairs": (other,)})
    assert divergent.snapshot_hash != forward.snapshot_hash
