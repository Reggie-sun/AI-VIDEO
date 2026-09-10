"""Explicit, append-only operator reconciliation of one paid unknown outcome."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    ActorIdentity,
    PaidProviderBudgetSnapshotPointer,
    PaidProviderSubmitReceiptPointer,
    StrictModel,
)


_HASH = r"^[0-9a-f]{64}$"
_SAFE_ID = re.compile(r"^[A-Za-z0-9._:/-]{1,256}$")


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        ErrorCode.PRODUCTION_STATE_INVALID,
        message,
        detail,
        retryable=False,
    )


def canonical_paid_provider_no_effect_reconciliation_path(content_hash: str) -> Path:
    if re.fullmatch(_HASH, content_hash) is None:
        raise ValueError("paid Provider no-effect reconciliation hash is invalid")
    return Path("state/paid-provider/no-effect-reconciliations") / f"{content_hash}.json"


def canonical_paid_provider_no_effect_evidence_path(file_sha256: str) -> Path:
    if re.fullmatch(_HASH, file_sha256) is None:
        raise ValueError("paid Provider no-effect evidence hash is invalid")
    return Path("state/paid-provider/no-effect-evidence") / f"{file_sha256}.json"


class PaidProviderNoEffectEvidencePointer(StrictModel):
    path: Path
    file_sha256: str = Field(pattern=_HASH)
    size_bytes: int = Field(strict=True, gt=0)

    @model_validator(mode="after")
    def _canonical_path(self) -> "PaidProviderNoEffectEvidencePointer":
        if (
            self.path.is_absolute()
            or ".." in self.path.parts
            or self.path != canonical_paid_provider_no_effect_evidence_path(self.file_sha256)
        ):
            raise ValueError("paid Provider no-effect evidence path must be canonical")
        return self


class PaidProviderNoEffectReconciliationPointer(StrictModel):
    path: Path
    content_hash: str = Field(pattern=_HASH)
    file_sha256: str = Field(pattern=_HASH)

    @model_validator(mode="after")
    def _canonical_path(self) -> "PaidProviderNoEffectReconciliationPointer":
        if (
            self.path.is_absolute()
            or ".." in self.path.parts
            or self.path != canonical_paid_provider_no_effect_reconciliation_path(
                self.content_hash
            )
        ):
            raise ValueError("paid Provider no-effect reconciliation path must be canonical")
        return self


class PaidProviderNoEffectReconciliation(StrictModel):
    """One authorized operator attestation of a verified pre-transport failure."""

    schema_version: Literal["paid-provider-no-effect-reconciliation/1"] = (
        "paid-provider-no-effect-reconciliation/1"
    )
    project_id: str = Field(min_length=1)
    attempt_id: str = Field(pattern=_SAFE_ID.pattern)
    actor: ActorIdentity
    explicit_user_authorization_receipt_id: str = Field(pattern=_SAFE_ID.pattern)
    prior_submit_receipt: PaidProviderSubmitReceiptPointer
    base_budget: PaidProviderBudgetSnapshotPointer
    expected_manifest_revision: int = Field(strict=True, ge=1)
    evidence: tuple[PaidProviderNoEffectEvidencePointer, ...] = Field(min_length=1)
    reason: Literal["verified_pre_transport_failure"]
    issued_at: datetime
    expires_at: datetime
    content_hash: str = Field(pattern=_HASH)

    @field_validator("evidence")
    @classmethod
    def _distinct_evidence(
        cls, value: tuple[PaidProviderNoEffectEvidencePointer, ...]
    ) -> tuple[PaidProviderNoEffectEvidencePointer, ...]:
        if len({item.file_sha256 for item in value}) != len(value):
            raise ValueError("paid Provider no-effect evidence must be unique")
        return value

    @model_validator(mode="after")
    def _sealed_window(self) -> "PaidProviderNoEffectReconciliation":
        if (
            self.issued_at.tzinfo is None
            or self.expires_at.tzinfo is None
            or self.expires_at <= self.issued_at
        ):
            raise ValueError("paid Provider no-effect reconciliation window is invalid")
        if self.content_hash != canonical_sha256(self.model_dump(mode="json")):
            raise ValueError("paid Provider no-effect reconciliation content hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "PaidProviderNoEffectReconciliation":
        data = dict(values)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(provisional.model_dump(mode="json"))
        return cls.model_validate(data)

    def valid_at(self, now: datetime) -> bool:
        return now.tzinfo is not None and self.issued_at <= now < self.expires_at


def validate_reconciliation_evidence_artifacts(
    reconciliation: PaidProviderNoEffectReconciliation,
    artifacts: tuple[object, ...],
) -> None:
    """Require supplied immutable bytes to close every sealed evidence pointer."""

    expected = {item.path: item for item in reconciliation.evidence}
    if len(artifacts) != len(expected):
        raise _invalid("Paid Provider no-effect evidence set is incomplete.")
    seen: set[Path] = set()
    for artifact in artifacts:
        path = getattr(artifact, "relative_path", None)
        payload = getattr(artifact, "payload", None)
        file_sha256 = getattr(artifact, "file_sha256", None)
        pointer = expected.get(path)
        if (
            pointer is None
            or path in seen
            or not isinstance(payload, bytes)
            or not isinstance(file_sha256, str)
            or len(payload) != pointer.size_bytes
            or hashlib.sha256(payload).hexdigest() != pointer.file_sha256
            or file_sha256 != pointer.file_sha256
        ):
            raise _invalid("Paid Provider no-effect evidence bytes do not match the receipt.")
        seen.add(path)


def release_unsettled_paid_provider_reservation(
    snapshot, *, prior_receipt, corrective_receipt
):
    """Create the one allowed ledger successor for an attested no-effect close."""

    from ai_video.production.paid_provider import (
        BudgetReservationStatus,
        PaidProviderBudgetReservation,
        PaidProviderBudgetSnapshot,
        PaidProviderSubmitOutcome,
    )

    if corrective_receipt.outcome is not PaidProviderSubmitOutcome.KNOWN_NO_EFFECT:
        raise _invalid("Paid Provider reconciliation requires a known-no-effect receipt.")
    reservation = next(
        (item for item in snapshot.reservations if item.reservation_id == prior_receipt.reservation_id),
        None,
    )
    if (
        reservation is None
        or reservation.attempt_id != prior_receipt.attempt_id
        or reservation.request_fingerprint != prior_receipt.request_fingerprint
        or reservation.preview_fingerprint != prior_receipt.preview_fingerprint
        or reservation.status is not BudgetReservationStatus.UNSETTLED
        or reservation.actual_cost_microunits is not None
        or reservation.submit_receipt_fingerprint != prior_receipt.submit_receipt_fingerprint
        or corrective_receipt.attempt_id != prior_receipt.attempt_id
        or corrective_receipt.request_fingerprint != prior_receipt.request_fingerprint
        or corrective_receipt.preview_fingerprint != prior_receipt.preview_fingerprint
        or corrective_receipt.gate_receipt_fingerprint != prior_receipt.gate_receipt_fingerprint
        or corrective_receipt.reservation_id != prior_receipt.reservation_id
    ):
        raise _invalid("Paid Provider reconciliation does not match the unsettled reservation.")
    released = PaidProviderBudgetReservation.model_validate(
        {
            **reservation.model_dump(mode="python"),
            "status": BudgetReservationStatus.RELEASED,
            "actual_cost_microunits": 0,
            "submit_receipt_fingerprint": corrective_receipt.submit_receipt_fingerprint,
        }
    )
    return PaidProviderBudgetSnapshot.create(
        revision=snapshot.revision + 1,
        policy_id=snapshot.policy_id,
        currency=snapshot.currency,
        project_ceiling_microunits=snapshot.project_ceiling_microunits,
        reservations=tuple(
            released if item.reservation_id == released.reservation_id else item
            for item in snapshot.reservations
        ),
        ceiling_extensions=snapshot.ceiling_extensions,
        submit_quota_extensions=snapshot.submit_quota_extensions,
        blocked=snapshot.blocked,
    )


def is_verified_reconciled_no_effect_video_attempt(
    committer, *, attempt_id: str
) -> bool:
    """Read-only exact check for the one recovered outcome that consumed no submit."""

    from ai_video.production.models import (
        PaidProviderAttemptPhase,
        StateCommitStatus,
        VideoAttemptPhase,
    )
    from ai_video.production.paid_provider import PaidProviderSubmitOutcome
    from ai_video.production.project import load_production_project

    loaded = load_production_project(committer.project_root / "project.yaml")
    loaded_attempt = next(
        (item for item in loaded.manifest.attempts if item.attempt_id == attempt_id),
        None,
    )
    if loaded_attempt is None:
        return False
    loaded_state = loaded_attempt.video_generation_state
    paid = loaded_attempt.paid_provider_state
    if (
        loaded_attempt.status is not StateCommitStatus.FAILED
        or loaded_attempt.operation != "video_generation"
        or loaded_state is None
        or loaded_state.phase is not VideoAttemptPhase.SUBMIT_INTENT
        or loaded_state.paid_submit_receipt is not None
        or loaded_state.latest_observation is not None
        or loaded_state.fetch_receipt is not None
        or loaded_state.provider_file_id is not None
        or loaded_state.local_submit_intent is not None
        or loaded_state.local_submit_receipt is not None
        or loaded_state.local_latest_observation is not None
        or loaded_state.local_fetch_receipt is not None
        or paid is None
        or paid.phase is not PaidProviderAttemptPhase.KNOWN_NO_EFFECT
        or paid.submit_receipt is None
    ):
        return False
    receipt = committer._reopen_paid_submit(paid.submit_receipt)
    pointer = receipt.no_effect_reconciliation
    if (
        receipt.outcome is not PaidProviderSubmitOutcome.KNOWN_NO_EFFECT
        or pointer is None
    ):
        return False
    from ai_video.production._paid_provider_project_reader import (
        _load_paid_provider_no_effect_reconciliation,
    )

    reconciliation = _load_paid_provider_no_effect_reconciliation(
        committer.project_root, pointer
    )
    return (
        reconciliation.reason == "verified_pre_transport_failure"
        and reconciliation.attempt_id == attempt_id
        and reconciliation.project_id == loaded.manifest.project_id
        and reconciliation.prior_submit_receipt != paid.submit_receipt
    )


def reconcile_paid_provider_no_effect(
    committer,
    reconciliation: PaidProviderNoEffectReconciliation,
    *,
    evidence_artifacts: tuple[object, ...],
    authorizer,
):
    """Commit one operator-attested close; replay is read-only and never re-authorizes."""

    from ai_video.production._state_commit_common import (
        _canonical_json_bytes,
        _state_invalid,
        _timestamp,
        _validated_transition,
    )
    from ai_video.production._state_commit_contracts import PreparedArtifact
    from ai_video.production.manifest_schema import ManifestCapability, manifest_supports
    from ai_video.production.models import (
        PaidProviderAttemptPhase,
        PaidProviderBudgetSnapshotPointer,
        PaidProviderSubmitReceiptPointer,
        StateCommitStatus,
        VideoAttemptPhase,
    )
    from ai_video.production.paid_provider import (
        PaidProviderSubmitOutcome,
        PaidProviderSubmitReceipt,
    )
    from ai_video.production.paths import (
        canonical_paid_provider_budget_path,
        canonical_paid_provider_submit_path,
    )
    from ai_video.production.project import load_production_project

    if not isinstance(reconciliation, PaidProviderNoEffectReconciliation):
        raise _state_invalid("Paid Provider no-effect reconciliation is invalid.")
    try:
        reconciliation = PaidProviderNoEffectReconciliation.model_validate_json(
            reconciliation.model_dump_json()
        )
    except ValueError as exc:
        raise _state_invalid("Paid Provider no-effect reconciliation seal is invalid.", str(exc)) from exc
    if authorizer is None:
        raise _state_invalid("Paid Provider no-effect reconciliation authorizer is required.")
    validate_reconciliation_evidence_artifacts(reconciliation, evidence_artifacts)

    def artifact(path: Path, model: object) -> PreparedArtifact:
        payload = _canonical_json_bytes(model)  # type: ignore[arg-type]
        return PreparedArtifact(
            relative_path=path,
            payload=payload,
            file_sha256=hashlib.sha256(payload).hexdigest(),
        )

    reconciliation_artifact = artifact(
        canonical_paid_provider_no_effect_reconciliation_path(reconciliation.content_hash),
        reconciliation,
    )
    reconciliation_ref = PaidProviderNoEffectReconciliationPointer(
        path=reconciliation_artifact.relative_path,
        content_hash=reconciliation.content_hash,
        file_sha256=reconciliation_artifact.file_sha256,
    )
    with committer._exclusive_lock():
        manifest = committer._read_manifest()
        try:
            loaded = load_production_project(committer._project_root / "project.yaml")
            if loaded.manifest != manifest:
                raise ValueError("Manifest changed during no-effect reconciliation validation")
        except Exception as exc:
            raise _state_invalid(
                "Paid Provider no-effect reconciliation requires a standard project reopen.",
                str(exc),
            ) from exc
        attempt = committer._paid_attempt(manifest, reconciliation.attempt_id)
        state = attempt.paid_provider_state
        if (
            state is not None
            and state.phase is PaidProviderAttemptPhase.KNOWN_NO_EFFECT
            and state.submit_receipt is not None
        ):
            current = committer._reopen_paid_submit(state.submit_receipt)
            if current.no_effect_reconciliation == reconciliation_ref:
                return manifest
            raise _state_invalid("Paid Provider no-effect reconciliation ID collision differs.")
        video = attempt.video_generation_state
        if (
            not manifest_supports(manifest.schema_version, ManifestCapability.PAID_PROVIDER)
            or manifest.active_paid_provider_budget is None
            or attempt.operation != "video_generation"
            or attempt.status is not StateCommitStatus.OUTCOME_UNKNOWN
            or state is None
            or state.phase is not PaidProviderAttemptPhase.OUTCOME_UNKNOWN
            or state.submit_receipt != reconciliation.prior_submit_receipt
            or video is None
            or video.phase is not VideoAttemptPhase.SUBMIT_INTENT
            or video.paid_submit_receipt is not None
            or video.latest_observation is not None
            or video.fetch_receipt is not None
            or video.provider_file_id is not None
            or any(
                item is not None
                for item in (
                    video.local_submit_intent,
                    video.local_submit_receipt,
                    video.local_latest_observation,
                    video.local_fetch_receipt,
                )
            )
            or reconciliation.project_id != manifest.project_id
            or reconciliation.expected_manifest_revision != manifest.manifest_revision
            or reconciliation.base_budget != manifest.active_paid_provider_budget
            or not reconciliation.valid_at(committer._paid_provider_clock())
        ):
            raise _state_invalid("Paid Provider no-effect reconciliation is not current.")
        prior = committer._reopen_paid_submit(reconciliation.prior_submit_receipt)
        gate = committer._reopen_paid_gate(state.gate_receipt)
        budget = committer._reopen_paid_budget(manifest.active_paid_provider_budget)
        if (
            prior.outcome is not PaidProviderSubmitOutcome.OUTCOME_UNKNOWN
            or prior.no_effect_reconciliation is not None
            or prior.external_effect_id is not None
            or prior.attempt_id != attempt.attempt_id
            or prior.request_fingerprint != gate.preview.request_fingerprint
            or prior.preview_fingerprint != gate.preview.preview_fingerprint
            or prior.gate_receipt_fingerprint != gate.gate_receipt_fingerprint
            or prior.reservation_id != state.reservation_id
        ):
            raise _state_invalid("Paid Provider prior unknown receipt is not exact.")
        try:
            authorized_actor = authorizer(reconciliation, evidence_artifacts)
        except Exception as exc:
            raise _state_invalid("Paid Provider no-effect reconciliation authorization failed.", str(exc)) from exc
        if authorized_actor != reconciliation.actor:
            raise _state_invalid("Paid Provider no-effect reconciliation was denied.")
        now = committer._paid_provider_clock()
        if not reconciliation.valid_at(now) or now < prior.recorded_at:
            raise _state_invalid("Paid Provider no-effect reconciliation is no longer current.")
        corrective = PaidProviderSubmitReceipt.create(
            attempt_id=prior.attempt_id,
            request_fingerprint=prior.request_fingerprint,
            preview_fingerprint=prior.preview_fingerprint,
            gate_receipt_fingerprint=prior.gate_receipt_fingerprint,
            reservation_id=prior.reservation_id,
            outcome=PaidProviderSubmitOutcome.KNOWN_NO_EFFECT,
            external_effect_id=None,
            no_effect_reconciliation=reconciliation_ref,
            recorded_at=now,
        )
        next_budget = release_unsettled_paid_provider_reservation(
            budget, prior_receipt=prior, corrective_receipt=corrective
        )
        submit_artifact = artifact(
            canonical_paid_provider_submit_path(corrective.submit_receipt_fingerprint),
            corrective,
        )
        budget_artifact = artifact(
            canonical_paid_provider_budget_path(next_budget.content_hash), next_budget
        )
        for evidence in evidence_artifacts:
            committer._write_immutable_artifact(evidence, attempt_id=attempt.attempt_id)
        committer._write_immutable_artifact(
            reconciliation_artifact, attempt_id=attempt.attempt_id
        )
        committer._write_immutable_artifact(submit_artifact, attempt_id=attempt.attempt_id)
        committer._write_immutable_artifact(budget_artifact, attempt_id=attempt.attempt_id)
        submit_pointer = PaidProviderSubmitReceiptPointer(
            path=submit_artifact.relative_path,
            submit_receipt_fingerprint=corrective.submit_receipt_fingerprint,
            file_sha256=submit_artifact.file_sha256,
        )
        budget_pointer = PaidProviderBudgetSnapshotPointer(
            path=budget_artifact.relative_path,
            revision=next_budget.revision,
            content_hash=next_budget.content_hash,
            file_sha256=budget_artifact.file_sha256,
        )
        next_attempt = _validated_transition(
            attempt,
            {
                "status": StateCommitStatus.FAILED,
                "paid_provider_state": state.model_copy(
                    update={
                        "phase": PaidProviderAttemptPhase.KNOWN_NO_EFFECT,
                        "submit_receipt": submit_pointer,
                    }
                ),
                "finished_at": _timestamp(),
                "error_code": ErrorCode.PAID_PROVIDER_KNOWN_NO_EFFECT.value,
                "error_message": "Operator-attested evidence verified a pre-transport failure.",
            },
        )
        next_manifest = _validated_transition(
            manifest,
            {
                "manifest_revision": manifest.manifest_revision + 1,
                "active_paid_provider_budget": budget_pointer,
                "attempts": tuple(
                    next_attempt if item.attempt_id == attempt.attempt_id else item
                    for item in manifest.attempts
                ),
            },
        )
        committer._write_manifest_atomic(next_manifest)
        try:
            reopened = load_production_project(committer._project_root / "project.yaml")
        except Exception as exc:
            raise _state_invalid(
                "Paid Provider no-effect reconciliation could not be reopened.", str(exc)
            ) from exc
        return reopened.manifest
