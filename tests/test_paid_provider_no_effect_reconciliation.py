from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ai_video.errors import AiVideoError
from ai_video.production._state_commit_contracts import CommitPhase, PreparedArtifact
from ai_video.production.models import (
    ActorIdentity,
    PaidProviderAttemptPhase,
    PaidProviderBudgetSnapshotPointer,
    StateCommitStatus,
)
from ai_video.production.paid_provider import (
    BudgetReservationStatus,
    PaidProviderBudgetReservation,
    PaidProviderBudgetSnapshot,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
)
from ai_video.production.paid_provider_no_effect_reconciliation import (
    PaidProviderNoEffectEvidencePointer,
    PaidProviderNoEffectReconciliation,
    canonical_paid_provider_no_effect_evidence_path,
)
from ai_video.production.project import load_production_project
from ai_video.production._state_commit_common import _canonical_json_bytes
from ai_video.production.paths import canonical_paid_provider_budget_path
from ai_video.production.generation_feedback import record_attempt_evaluation
from ai_video.production.generation_diagnosis import AttemptEvidence
from ai_video.production.generation_experience import GenerationExperience
from ai_video.production.shot_router import VideoGenerationResolver

from test_production_video_state_recovery import ATTEMPT_ID, _runtime


def _unknown_runtime(tmp_path: Path):
    committer, service, provider, resolved, execution_binding, preview = _runtime(tmp_path)
    service.start(
        attempt_id=ATTEMPT_ID,
        request=resolved,
        execution_binding=execution_binding,
    )
    committer.record_paid_provider_submit_intent(
        preview, reservation_id="video-reservation-1"
    )
    manifest = committer._read_manifest()
    state = manifest.attempts[-1].paid_provider_state
    assert state is not None
    committer.record_paid_provider_submit_receipt(
        PaidProviderSubmitReceipt.create(
            attempt_id=preview.attempt_id,
            request_fingerprint=preview.request_fingerprint,
            preview_fingerprint=preview.preview_fingerprint,
            gate_receipt_fingerprint=state.gate_receipt.gate_receipt_fingerprint,
            reservation_id=state.reservation_id,
            outcome=PaidProviderSubmitOutcome.OUTCOME_UNKNOWN,
            external_effect_id=None,
            recorded_at=committer._paid_provider_clock(),
        )
    )
    unknown = committer._read_manifest()
    return committer, unknown, provider, execution_binding


def _unknown(tmp_path: Path):
    committer, unknown, _, _ = _unknown_runtime(tmp_path)
    return committer, unknown


def _ordinary_failed_runtime(tmp_path: Path):
    committer, service, _, resolved, binding, preview = _runtime(tmp_path)
    service.start(
        attempt_id=ATTEMPT_ID,
        request=resolved,
        execution_binding=binding,
    )
    committer.record_paid_provider_submit_intent(
        preview, reservation_id="video-reservation-1"
    )
    state = committer._read_manifest().attempts[-1].paid_provider_state
    assert state is not None
    committer.record_paid_provider_submit_receipt(
        PaidProviderSubmitReceipt.create(
            attempt_id=preview.attempt_id,
            request_fingerprint=preview.request_fingerprint,
            preview_fingerprint=preview.preview_fingerprint,
            gate_receipt_fingerprint=state.gate_receipt.gate_receipt_fingerprint,
            reservation_id=state.reservation_id,
            outcome=PaidProviderSubmitOutcome.KNOWN_NO_EFFECT,
            external_effect_id=None,
            recorded_at=committer._paid_provider_clock(),
        )
    )
    return committer, committer._read_manifest(), binding


def _entry(committer, manifest, *, payload: bytes = b'{"event":"pre-http-key-error"}\n'):
    attempt = manifest.attempts[-1]
    state = attempt.paid_provider_state
    assert state is not None and state.submit_receipt is not None
    digest = hashlib.sha256(payload).hexdigest()
    evidence = PreparedArtifact(
        relative_path=canonical_paid_provider_no_effect_evidence_path(digest),
        payload=payload,
        file_sha256=digest,
    )
    now = committer._paid_provider_clock()
    actor = ActorIdentity(actor_id="human-owner", actor_kind="human")
    return (
        PaidProviderNoEffectReconciliation.create(
            project_id=manifest.project_id,
            attempt_id=attempt.attempt_id,
            actor=actor,
            explicit_user_authorization_receipt_id="user-authorized-s02-recovery",
            prior_submit_receipt=state.submit_receipt,
            base_budget=manifest.active_paid_provider_budget,
            expected_manifest_revision=manifest.manifest_revision,
            evidence=(
                PaidProviderNoEffectEvidencePointer(
                    path=evidence.relative_path,
                    file_sha256=digest,
                    size_bytes=len(payload),
                ),
            ),
            reason="verified_pre_transport_failure",
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        ),
        evidence,
        actor,
    )


def test_legacy_submit_receipt_hash_is_unchanged_when_reconciliation_is_absent():
    receipt = PaidProviderSubmitReceipt.create(
        attempt_id="attempt-1",
        request_fingerprint="1" * 64,
        preview_fingerprint="2" * 64,
        gate_receipt_fingerprint="3" * 64,
        reservation_id="reservation-1",
        outcome=PaidProviderSubmitOutcome.OUTCOME_UNKNOWN,
        external_effect_id=None,
        recorded_at=datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc),
    )
    assert receipt.submit_receipt_fingerprint == (
        "e5445d4babbb3c4951511ffb1f4731e29fe2cf8548b63180323f5d2346ece38c"
    )
    assert "no_effect_reconciliation" not in receipt.model_dump(mode="json")


def test_reconciliation_releases_exact_unknown_and_replay_is_read_only(tmp_path: Path):
    committer, unknown = _unknown(tmp_path)
    state = unknown.attempts[-1].paid_provider_state
    assert state is not None and state.submit_receipt is not None
    old_bytes = (tmp_path / state.submit_receipt.path).read_bytes()
    entry, evidence, actor = _entry(committer, unknown)
    calls = 0

    def authorize(exact, artifacts):
        nonlocal calls
        calls += 1
        return actor if exact == entry and artifacts == (evidence,) else None

    reconciled = committer.reconcile_paid_provider_no_effect(
        entry, evidence_artifacts=(evidence,), authorizer=authorize
    )
    attempt = reconciled.attempts[-1]
    assert attempt.status is StateCommitStatus.FAILED
    assert attempt.paid_provider_state is not None
    assert attempt.paid_provider_state.phase is PaidProviderAttemptPhase.KNOWN_NO_EFFECT
    assert (tmp_path / state.submit_receipt.path).read_bytes() == old_bytes
    assert calls == 1
    loaded = load_production_project(tmp_path / "project.yaml")
    assert loaded.manifest == reconciled

    committer._paid_provider_clock = lambda: entry.expires_at + timedelta(seconds=1)
    assert committer.reconcile_paid_provider_no_effect(
        entry, evidence_artifacts=(evidence,), authorizer=authorize
    ) == reconciled
    assert calls == 1


@pytest.mark.parametrize("kind", ["denied", "wrong-bytes", "wrong-base", "wrong-attempt"])
def test_reconciliation_rejects_untrusted_or_mismatched_input_without_mutation(
    tmp_path: Path, kind: str
):
    committer, unknown = _unknown(tmp_path)
    entry, evidence, actor = _entry(committer, unknown)
    before = (tmp_path / "state/manifest.json").read_bytes()
    if kind == "denied":
        authorizer = lambda exact, artifacts: None
        artifacts = (evidence,)
    elif kind == "wrong-bytes":
        authorizer = lambda exact, artifacts: actor
        artifacts = (
            PreparedArtifact(
                relative_path=evidence.relative_path,
                payload=b"wrong\n",
                file_sha256=hashlib.sha256(b"wrong\n").hexdigest(),
            ),
        )
    else:
        authorizer = lambda exact, artifacts: actor
        entry = entry.model_copy(update={
            "base_budget": unknown.active_paid_provider_budget.model_copy(update={"revision": 1})
        }) if kind == "wrong-base" else entry.model_copy(update={"attempt_id": "other-attempt"})
        artifacts = (evidence,)
    with pytest.raises(AiVideoError):
        committer.reconcile_paid_provider_no_effect(
            entry, evidence_artifacts=artifacts, authorizer=authorizer
        )
    assert (tmp_path / "state/manifest.json").read_bytes() == before


@pytest.mark.parametrize("tampered", ["evidence", "prior", "base"])
def test_reader_rejects_tampered_reconciliation_history(tmp_path: Path, tampered: str):
    committer, unknown = _unknown(tmp_path)
    entry, evidence, actor = _entry(committer, unknown)
    committer.reconcile_paid_provider_no_effect(
        entry,
        evidence_artifacts=(evidence,),
        authorizer=lambda exact, artifacts: actor,
    )
    state = unknown.attempts[-1].paid_provider_state
    assert state is not None and state.submit_receipt is not None
    target = {
        "evidence": evidence.relative_path,
        "prior": state.submit_receipt.path,
        "base": entry.base_budget.path,
    }[tampered]
    (tmp_path / target).write_bytes(b"tampered\n")
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")


def test_crash_before_manifest_leaves_unknown_reopenable(tmp_path: Path):
    committer, unknown = _unknown(tmp_path)
    entry, evidence, actor = _entry(committer, unknown)
    before = (tmp_path / "state/manifest.json").read_bytes()

    class Crash:
        def checkpoint(self, phase):
            if phase is CommitPhase.AFTER_ARTIFACT_TEMP_WRITE:
                raise RuntimeError("crash")

    committer._crash_injector = Crash()
    with pytest.raises(AiVideoError):
        committer.reconcile_paid_provider_no_effect(
            entry,
            evidence_artifacts=(evidence,),
            authorizer=lambda exact, artifacts: actor,
        )
    assert (tmp_path / "state/manifest.json").read_bytes() == before
    assert load_production_project(tmp_path / "project.yaml").manifest == unknown


def test_authorizer_expiry_race_rejects_without_manifest_write(tmp_path: Path):
    committer, unknown = _unknown(tmp_path)
    entry, evidence, actor = _entry(committer, unknown)
    before = (tmp_path / "state/manifest.json").read_bytes()

    def expires_during_authorization(exact, artifacts):
        committer._paid_provider_clock = lambda: entry.expires_at
        return actor

    with pytest.raises(AiVideoError):
        committer.reconcile_paid_provider_no_effect(
            entry,
            evidence_artifacts=(evidence,),
            authorizer=expires_during_authorization,
        )
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def _select_budget_successor(committer, *, settled: bool):
    manifest = committer._read_manifest()
    budget = committer._reopen_paid_budget(manifest.active_paid_provider_budget)
    reservation = PaidProviderBudgetReservation(
        reservation_id="later-reservation",
        attempt_id="later-attempt",
        request_fingerprint="4" * 64,
        preview_fingerprint="5" * 64,
        upper_bound_microunits=1,
        status=BudgetReservationStatus.SETTLED if settled else BudgetReservationStatus.RESERVED,
        actual_cost_microunits=0 if settled else None,
        submit_receipt_fingerprint="6" * 64 if settled else None,
    )
    successor = PaidProviderBudgetSnapshot.create(
        revision=budget.revision + 1,
        policy_id=budget.policy_id,
        currency=budget.currency,
        project_ceiling_microunits=budget.project_ceiling_microunits,
        reservations=(*budget.reservations, reservation),
        ceiling_extensions=budget.ceiling_extensions,
        submit_quota_extensions=budget.submit_quota_extensions,
        blocked=budget.blocked,
    )
    payload = _canonical_json_bytes(successor)
    artifact = PreparedArtifact(
        relative_path=canonical_paid_provider_budget_path(successor.content_hash),
        payload=payload,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    committer._write_immutable_artifact(artifact, attempt_id="later-attempt")
    pointer = PaidProviderBudgetSnapshotPointer(
        path=artifact.relative_path,
        revision=successor.revision,
        content_hash=successor.content_hash,
        file_sha256=artifact.file_sha256,
    )
    committer._write_manifest_atomic(
        manifest.model_copy(
            update={
                "manifest_revision": manifest.manifest_revision + 1,
                "active_paid_provider_budget": pointer,
            }
        )
    )


@pytest.mark.parametrize("settled", [False, True])
def test_reconciliation_reopens_after_later_budget_successor(tmp_path: Path, settled: bool):
    committer, unknown = _unknown(tmp_path)
    entry, evidence, actor = _entry(committer, unknown)
    committer.reconcile_paid_provider_no_effect(
        entry,
        evidence_artifacts=(evidence,),
        authorizer=lambda exact, artifacts: actor,
    )
    _select_budget_successor(committer, settled=settled)
    assert load_production_project(tmp_path / "project.yaml").manifest == committer._read_manifest()


def test_reconciled_attempt_records_not_submitted_and_allows_next_generation(tmp_path: Path):
    committer, unknown, _, binding = _unknown_runtime(tmp_path)
    entry, evidence, actor = _entry(committer, unknown)
    committer.reconcile_paid_provider_no_effect(
        entry,
        evidence_artifacts=(evidence,),
        authorizer=lambda exact, artifacts: actor,
    )
    experience = record_attempt_evaluation(committer=committer, attempt_id=ATTEMPT_ID)
    assert experience.evidence[0].outcome == "not_submitted"
    assert load_production_project(tmp_path / "project.yaml").manifest == committer._read_manifest()

    limits = binding.inputs.limits.model_copy(
        update={"paid_submit_ceiling": 2, "paid_submits_used": 1}
    )
    inputs = binding.inputs.model_copy(
        update={
            "limits": limits,
            "evidence": experience.evidence,
            "experiences": (experience,),
            "latest_attempt_hash": experience.evidence[0].evidence_hash,
            "historical_recipes": (experience.candidate,),
        }
    )
    decision = VideoGenerationResolver().resolve_requirement(
        projection=binding.projection,
        context=binding.context,
        policy=binding.policy,
        lifecycle=binding.lifecycle,
        inputs=inputs,
    )
    assert decision.disposition == "GENERATE_ONCE"
    assert inputs.limits.paid_submits_used == 1


@pytest.mark.parametrize("outcome", ["unknown", "ordinary_failed"])
def test_forged_not_submitted_is_rejected_for_nonreconciled_paid_attempt(
    tmp_path: Path, outcome: str
):
    if outcome == "ordinary_failed":
        committer, unknown, binding = _ordinary_failed_runtime(tmp_path)
    else:
        committer, unknown, _, binding = _unknown_runtime(tmp_path)
    attempt = committer._read_manifest().attempts[-1]
    state = attempt.video_generation_state
    assert state is not None
    candidate = binding.inputs.candidates[0]
    request = committer._reopen_video_request(state.request)
    evidence = AttemptEvidence(
        task_id=binding.inputs.limits.task_id,
        shot_id=binding.context.target_shot_id,
        attempt_id=ATTEMPT_ID,
        recipe_scope_hash=candidate.scope_hash,
        facts_hash=binding.inputs.facts_hash,
        rubric_hash=binding.inputs.rubric_hash,
        request_hash=request.request_input_hash,
        outcome="not_submitted",
    )
    with pytest.raises(AiVideoError):
        committer.record_generation_experience(
            attempt_id=ATTEMPT_ID,
            experience=GenerationExperience(
                projection=binding.projection,
                candidate=candidate,
                evidence=(evidence,),
            ),
        )
