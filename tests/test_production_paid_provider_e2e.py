from __future__ import annotations

from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    PaidProviderAttemptPhase,
    ProductionManifest,
    StateCommitAttempt,
    StateCommitStatus,
    VoiceRequestReceipt,
)
from ai_video.production.paid_provider import (
    PaidProviderBudgetSnapshot,
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
)
from ai_video.production.paths import canonical_paid_provider_budget_path
from ai_video.production._state_commit_common import _canonical_json_bytes
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter

import production_project_factory as project_factory
from paid_provider_support import (
    NOW,
    ScriptedFakePaidProviderTransport,
    paid_authorization,
    paid_preview,
)


def _setup(tmp_path: Path):
    project_factory.write_production_project(tmp_path)
    base = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_bytes()
    )
    preview = paid_preview(attempt_id="paid-attempt-1")
    attempt = StateCommitAttempt(
        attempt_id=preview.attempt_id,
        operation="voice_generation",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=base.manifest_revision,
        base_project=base.active_project,
        base_registry=base.active_registry,
        candidate_artifacts_hash="0" * 64,
        voice_request=VoiceRequestReceipt(
            request_id=preview.request_fingerprint,
            attempt_id=preview.attempt_id,
            request_fingerprint=preview.request_fingerprint,
            script_hash="1" * 64,
            provider_kind=preview.provider_kind,
            model_id=preview.model_id,
            voice_id="fixture-voice",
            language="en",
            pricing_snapshot_id="pricing-1",
            budget_reservation_receipt_id="budget-1",
            egress_authorization_receipt_id="egress-1",
            destination=preview.destination,
        ),
        voice_phase="submit_intent",
        started_at=NOW.isoformat(),
    )
    manifest = ProductionManifest.model_validate(
        {
            **base.model_dump(mode="python"),
            "schema_version": "2.6",
            "attempts": base.attempts + (attempt,),
        }
    )
    authorization = paid_authorization(preview)
    committer = ProductionStateCommitter(
        tmp_path,
        paid_provider_authorizer=lambda exact: authorization if exact == preview else None,
        paid_provider_clock=lambda: NOW,
    )
    committer._write_manifest_atomic(manifest)
    return committer, preview


def test_fake_paid_flow_is_durable_exact_and_replay_safe(tmp_path: Path):
    committer, preview = _setup(tmp_path)
    transport = ScriptedFakePaidProviderTransport()
    permit = committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
    )
    intent = committer._read_manifest().attempts[-1].paid_provider_state
    assert intent is not None

    effect_id = transport.submit(
        permit,
        preview,
        intent.gate_receipt.gate_receipt_fingerprint,
        intent.reservation_id,
    )
    receipt = PaidProviderSubmitReceipt.create(
        attempt_id=preview.attempt_id,
        request_fingerprint=preview.request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        gate_receipt_fingerprint=intent.gate_receipt.gate_receipt_fingerprint,
        reservation_id=intent.reservation_id,
        outcome=PaidProviderSubmitOutcome.ACCEPTED,
        external_effect_id=effect_id,
        recorded_at=NOW,
    )
    committer.record_paid_provider_submit_receipt(receipt)
    committer.settle_paid_provider_reservation(
        attempt_id=preview.attempt_id, actual_cost_microunits=1_500_000
    )

    loaded = load_production_project(tmp_path / "project.yaml")
    restarted = ProductionStateCommitter(tmp_path)
    assert loaded.manifest == restarted._read_manifest()
    with pytest.raises(PermissionError):
        transport.submit(
            permit,
            preview,
            intent.gate_receipt.gate_receipt_fingerprint,
            intent.reservation_id,
        )
    assert transport.calls == 1


def test_reader_rejects_tampered_gate_receipt(tmp_path: Path):
    committer, preview = _setup(tmp_path)
    committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
    )
    state = committer._read_manifest().attempts[-1].paid_provider_state
    assert state is not None
    gate_path = tmp_path / state.gate_receipt.path
    gate_path.write_bytes(gate_path.read_bytes() + b" ")

    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")


def test_reader_reopens_the_exact_historical_gate_budget(tmp_path: Path):
    committer, preview = _setup(tmp_path)
    committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
    )
    state = committer._read_manifest().attempts[-1].paid_provider_state
    assert state is not None
    gate = committer._reopen_paid_gate(state.gate_receipt)
    historical_budget = (
        tmp_path
        / "state/paid-provider/budgets"
        / f"{gate.budget_snapshot_content_hash}.json"
    )
    historical_budget.write_bytes(historical_budget.read_bytes() + b" ")

    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")


def test_recovery_converts_unresolved_submit_intent_to_unknown_without_call(tmp_path: Path):
    committer, preview = _setup(tmp_path)
    committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
    )
    transport = ScriptedFakePaidProviderTransport()

    report = ProductionStateCommitter(tmp_path).recover()
    manifest = ProductionStateCommitter(tmp_path)._read_manifest()
    state = manifest.attempts[-1].paid_provider_state

    assert report.manifest_revision_after == report.manifest_revision_before + 1
    assert state is not None
    assert state.phase.value == "outcome_unknown"
    assert state.submit_receipt is not None
    assert transport.calls == 0


def test_recovery_preserves_complete_unselected_paid_evidence(tmp_path: Path):
    committer, preview = _setup(tmp_path)
    committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
    )
    orphan = PaidProviderBudgetSnapshot.create(
        revision=99,
        policy_id="orphan-policy",
        currency="USD",
        project_ceiling_microunits=1,
        reservations=(),
        blocked=False,
    )
    orphan_path = tmp_path / canonical_paid_provider_budget_path(orphan.content_hash)
    orphan_path.parent.mkdir(parents=True, exist_ok=True)
    orphan_path.write_bytes(_canonical_json_bytes(orphan))

    report = ProductionStateCommitter(tmp_path).recover()

    orphan_item = next(item for item in report.items if item.path == orphan_path.relative_to(tmp_path))
    assert orphan_item.disposition.value == "orphan_preserved"


def test_reader_rejects_terminal_phase_mixed_with_another_submit_outcome(
    tmp_path: Path,
):
    committer, preview = _setup(tmp_path)
    committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
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
            recorded_at=NOW,
        )
    )
    manifest = committer._read_manifest()
    attempt = manifest.attempts[-1]
    assert attempt.paid_provider_state is not None
    mixed_attempt = attempt.model_copy(
        update={
            "paid_provider_state": attempt.paid_provider_state.model_copy(
                update={"phase": PaidProviderAttemptPhase.ACCEPTED}
            )
        }
    )
    committer._write_manifest_atomic(
        manifest.model_copy(
            update={
                "manifest_revision": manifest.manifest_revision + 1,
                "attempts": manifest.attempts[:-1] + (mixed_attempt,),
            }
        )
    )

    with pytest.raises(AiVideoError, match="inconsistent"):
        load_production_project(tmp_path / "project.yaml")


@pytest.mark.parametrize(
    ("outcome", "effect_id", "invalid_status"),
    [
        (PaidProviderSubmitOutcome.ACCEPTED, "fixture-effect-1", StateCommitStatus.FAILED),
        (PaidProviderSubmitOutcome.KNOWN_NO_EFFECT, None, StateCommitStatus.RUNNING),
        (PaidProviderSubmitOutcome.OUTCOME_UNKNOWN, None, StateCommitStatus.RUNNING),
    ],
)
def test_reader_rejects_paid_phase_with_impossible_outer_attempt_status(
    tmp_path: Path,
    outcome: PaidProviderSubmitOutcome,
    effect_id: str | None,
    invalid_status: StateCommitStatus,
):
    committer, preview = _setup(tmp_path)
    committer.record_paid_provider_submit_intent(
        preview, reservation_id="reservation-1"
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
            outcome=outcome,
            external_effect_id=effect_id,
            recorded_at=NOW,
        )
    )
    manifest = committer._read_manifest()
    attempt = manifest.attempts[-1]
    terminal = invalid_status is StateCommitStatus.FAILED
    invalid_attempt = attempt.model_copy(
        update={
            "status": invalid_status,
            "finished_at": NOW.isoformat() if terminal else None,
            "error_code": ErrorCode.PAID_PROVIDER_KNOWN_NO_EFFECT.value if terminal else None,
            "error_message": "fixture invalid status" if terminal else None,
        }
    )
    committer._write_manifest_atomic(
        manifest.model_copy(
            update={
                "manifest_revision": manifest.manifest_revision + 1,
                "attempts": manifest.attempts[:-1] + (invalid_attempt,),
            }
        )
    )

    with pytest.raises(AiVideoError, match="status is inconsistent"):
        load_production_project(tmp_path / "project.yaml")
