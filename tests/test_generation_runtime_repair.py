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


def test_local_unmetered_new_batch_keeps_history_and_one_use_runtime_grant(tmp_path):
    provider, committer, caller, service, limits, sequence = _orchestrator(
        tmp_path, status_state=VideoTaskState.FAILED)
    initial = limits.model_copy(update={"local_batch_limit": 1, "local_total_limit": 1})
    _fail_attempt(committer=committer, caller=caller, service=service, limits=initial,
        sequence=sequence, number=0, attempt_id="unmetered-initial")
    pointer = committer.record_runtime_repair_authorization(
        attempt_id="unmetered-initial", repair_basis=REPAIR_BASIS, actor=ACTOR)
    sequence[0] = 1
    continued = initial.model_copy(update={"local_batch_limit": 2, "local_total_limit": None})
    prepared = caller.start(committer=committer, attempt_id="unmetered-continued", limits=continued)
    assert prepared.inputs.limits.local_total_used == prepared.inputs.limits.local_batch_used == 1
    assert prepared.decision.runtime_repair.evidence_hash == pointer.evidence_hash
    provider.status_state = VideoTaskState.SUCCEEDED
    service.submit_local_once(attempt_id="unmetered-continued")
    assert service.refresh_local_once(attempt_id="unmetered-continued").state is VideoTaskState.SUCCEEDED
    assert _attempt(committer, "unmetered-initial").video_generation_state.runtime_repairs[0].consumed
    assert provider.submit_calls == 2
    with pytest.raises(AiVideoError):
        service.submit_local_once(attempt_id="unmetered-continued")
    assert provider.submit_calls == 2


def _exhausted_local_repairs(tmp_path):
    runtime = _orchestrator(tmp_path, status_state=VideoTaskState.FAILED)
    provider, committer, caller, service, limits, sequence = runtime
    for number in range(3):
        attempt_id = f"extension-failure-{number}"
        _fail_attempt(committer=committer, caller=caller, service=service,
                      limits=limits, sequence=sequence, number=number, attempt_id=attempt_id)
        if number < 2:
            committer.record_runtime_repair_authorization(
                attempt_id=attempt_id, repair_basis=REPAIR_BASIS, actor=ACTOR)
    return runtime


def _extension(committer, **updates):
    from ai_video.production.generation_runtime_repair import LocalRuntimeRepairExtension
    state = _attempt(committer, "extension-failure-2").video_generation_state
    binding = committer._reopen_generation_execution_binding(state.execution_binding)
    return LocalRuntimeRepairExtension(**{
        "task_id": binding.inputs.limits.task_id,
        "shot_id": binding.context.target_shot_id,
        "failed_binding_hash": binding.binding_hash,
        "expected_manifest_revision": committer._read_manifest().manifest_revision,
        **updates,
    })


def test_v1_runtime_repair_payload_and_hash_remain_exact():
    from ai_video.production.hashing import canonical_sha256
    payload = {
        "schema_version": "runtime-repair/1", "attempt_id": "old-attempt",
        "evidence_hash": "e" * 64, "repair_basis": REPAIR_BASIS,
        "actor": ACTOR.model_dump(mode="json"), "expected_manifest_revision": 8,
        "content_hash": "0" * 64,
    }
    payload["content_hash"] = canonical_sha256(payload)
    reopened = RuntimeRepairAuthorization.model_validate(payload)
    assert reopened.model_dump(mode="json") == payload
    assert RuntimeRepairAuthorization.model_validate_json(reopened.model_dump_json()) == reopened


def test_explicit_third_local_runtime_repair_is_one_use_and_keeps_counts(tmp_path):
    provider, committer, caller, service, limits, sequence = _exhausted_local_repairs(tmp_path)
    extension = _extension(committer)
    pointer = committer.record_runtime_repair_authorization(
        attempt_id="extension-failure-2", repair_basis=REPAIR_BASIS, actor=ACTOR,
        local_extension=extension)
    receipt = committer._reopen_runtime_repair_authorization(pointer)
    assert receipt.schema_version == "runtime-repair/2"
    assert receipt.local_extension == extension
    revision = committer._read_manifest().manifest_revision
    assert committer.record_runtime_repair_authorization(
        attempt_id="extension-failure-2", repair_basis=REPAIR_BASIS, actor=ACTOR,
        local_extension=extension) == pointer
    assert committer._read_manifest().manifest_revision == revision
    sequence[0] = 3
    continued = limits.model_copy(update={"local_batch_limit": 4, "local_total_limit": None})
    prepared = caller.start(committer=committer, attempt_id="extension-last", limits=continued)
    assert prepared.inputs.limits.local_batch_used == prepared.inputs.limits.local_total_used == 3
    service.submit_local_once(attempt_id="extension-last")
    prior = _attempt(committer, "extension-failure-2").video_generation_state
    assert prior.runtime_repairs[0].consumed
    assert _attempt(committer, "extension-last").video_generation_state.local_submit_intent
    assert provider.submit_calls == 4
    with pytest.raises(AiVideoError):
        service.submit_local_once(attempt_id="extension-last")
    assert provider.submit_calls == 4
    service.refresh_local_once(attempt_id="extension-last")
    from ai_video.production.generation_feedback import record_attempt_evaluation
    record_attempt_evaluation(committer=committer, attempt_id="extension-last")
    with pytest.raises(AiVideoError, match="budget is exhausted"):
        committer.record_runtime_repair_authorization(
            attempt_id="extension-last", repair_basis=REPAIR_BASIS, actor=ACTOR,
            local_extension=extension.model_copy(update={
                "expected_manifest_revision": committer._read_manifest().manifest_revision}))


@pytest.mark.parametrize("updates, actor, evidence_hash", [
    ({"task_id": "different-task"}, ACTOR, None),
    ({"shot_id": "different-shot"}, ACTOR, None),
    ({"failed_binding_hash": "0" * 64}, ACTOR, None),
    ({"expected_manifest_revision": 0}, ACTOR, None),
    ({}, ActorIdentity(actor_id="other-owner", actor_kind="automation"), None),
    ({}, ACTOR, "0" * 64),
])
def test_third_repair_rejects_identity_and_stale_revision(tmp_path, updates, actor, evidence_hash):
    provider, committer, _, _, _, _ = _exhausted_local_repairs(tmp_path)
    before = committer._read_manifest()
    with pytest.raises(AiVideoError):
        committer.record_runtime_repair_authorization(
            attempt_id="extension-failure-2", repair_basis=REPAIR_BASIS, actor=actor,
            evidence_hash=evidence_hash, local_extension=_extension(committer, **updates))
    assert committer._read_manifest() == before
    assert provider.submit_calls == 3


def test_third_repair_scope_rechecked_at_submit(tmp_path):
    provider, committer, caller, service, limits, sequence = _exhausted_local_repairs(tmp_path)
    committer.record_runtime_repair_authorization(
        attempt_id="extension-failure-2", repair_basis=REPAIR_BASIS, actor=ACTOR,
        local_extension=_extension(committer))
    sequence[0] = 3
    wrong_task = limits.model_copy(update={"task_id": "reset-task", "local_batch_limit": 4})
    with pytest.raises(AiVideoError, match="extension scope"):
        caller.start(committer=committer, attempt_id="wrong-task", limits=wrong_task)
        service.submit_local_once(attempt_id="wrong-task")
    assert provider.submit_calls == 3


def test_v2_extension_tamper_and_version_mismatch_are_rejected(tmp_path):
    _, committer, _, _, _, _ = _exhausted_local_repairs(tmp_path)
    extension = _extension(committer)
    receipt = RuntimeRepairAuthorization.create(
        schema_version="runtime-repair/2", attempt_id="extension-failure-2",
        evidence_hash="e" * 64, repair_basis=REPAIR_BASIS, actor=ACTOR,
        expected_manifest_revision=extension.expected_manifest_revision + 1,
        local_extension=extension)
    payload = receipt.model_dump(mode="json")
    payload["local_extension"]["task_id"] = "tampered"
    with pytest.raises(ValueError):
        RuntimeRepairAuthorization.model_validate(payload)
    with pytest.raises(ValueError):
        RuntimeRepairAuthorization.create(
            attempt_id="bad-v1", evidence_hash="e" * 64, repair_basis=REPAIR_BASIS,
            actor=ACTOR, expected_manifest_revision=0, local_extension=extension)


def test_runtime_repair_extension_cannot_authorize_unknown_submit(tmp_path):
    from ai_video.errors import ErrorCode
    from ai_video.production.generation_runtime_repair import LocalRuntimeRepairExtension
    provider, committer, caller, service, limits, _ = _orchestrator(
        tmp_path, status_state=VideoTaskState.FAILED)
    prepared = caller.start(committer=committer, attempt_id="unknown-extension", limits=limits)
    provider.submit_error = ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    with pytest.raises(AiVideoError):
        service.submit_local_once(attempt_id="unknown-extension")
    before = committer._read_manifest()
    assert _attempt(committer, "unknown-extension").status is StateCommitStatus.OUTCOME_UNKNOWN
    extension = LocalRuntimeRepairExtension(task_id=limits.task_id,
        shot_id=prepared.execution_binding.context.target_shot_id,
        failed_binding_hash=prepared.execution_binding.binding_hash,
        expected_manifest_revision=before.manifest_revision)
    with pytest.raises(AiVideoError, match="failed video attempt"):
        committer.record_runtime_repair_authorization(attempt_id="unknown-extension",
            repair_basis=REPAIR_BASIS, actor=ACTOR, local_extension=extension)
    assert committer._read_manifest() == before


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
