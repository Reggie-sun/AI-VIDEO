"""Sealed, explicit one-step paid Provider submit-quota extensions."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    ActorIdentity,
    GenerationExecutionBindingPointer,
    PaidProviderBudgetSnapshotPointer,
    StrictModel,
)


_HASH = r"^[0-9a-f]{64}$"


class PaidProviderSubmitQuotaExtension(StrictModel):
    """One explicit additional remote submission on one existing task."""

    schema_version: Literal["paid-provider-submit-quota-extension/1"] = (
        "paid-provider-submit-quota-extension/1"
    )
    extension_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    project_id: str = Field(min_length=1)
    actor: ActorIdentity
    explicit_opt_in: Literal[True]
    authorization_receipt_id: str = Field(min_length=1)
    expected_manifest_revision: int = Field(strict=True, ge=1)
    base_budget: PaidProviderBudgetSnapshotPointer
    target_attempt_id: str = Field(min_length=1)
    target_binding: GenerationExecutionBindingPointer
    prior_attempt_id: str = Field(min_length=1)
    prior_binding: GenerationExecutionBindingPointer
    task_id: str = Field(min_length=1)
    old_paid_submit_ceiling: int = Field(strict=True, ge=0)
    new_paid_submit_ceiling: int = Field(strict=True, ge=1)
    issued_at: datetime
    expires_at: datetime
    content_hash: str = Field(pattern=_HASH)

    @model_validator(mode="after")
    def _validate_seal_and_window(self) -> "PaidProviderSubmitQuotaExtension":
        if self.target_attempt_id == self.prior_attempt_id:
            raise ValueError("submit quota extension must bind distinct attempts")
        if self.new_paid_submit_ceiling != self.old_paid_submit_ceiling + 1:
            raise ValueError("submit quota extension must increase the ceiling by exactly one")
        if (
            self.issued_at.tzinfo is None
            or self.expires_at.tzinfo is None
            or self.expires_at <= self.issued_at
        ):
            raise ValueError("submit quota extension window is invalid")
        if self.content_hash != canonical_sha256(self.model_dump(mode="json")):
            raise ValueError("submit quota extension content hash is invalid")
        return self

    @classmethod
    def create(cls, **values):
        data = dict(values)
        trial = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(trial.model_dump(mode="json"))
        return cls.model_validate(data)

    def valid_at(self, now: datetime) -> bool:
        return now.tzinfo is not None and self.issued_at <= now < self.expires_at


def _artifact(path, model):
    import hashlib

    from ai_video.production._state_commit_common import _canonical_json_bytes
    from ai_video.production._state_commit_contracts import PreparedArtifact

    payload = _canonical_json_bytes(model)
    return PreparedArtifact(
        relative_path=path, payload=payload, file_sha256=hashlib.sha256(payload).hexdigest()
    )


def _extend_paid_provider_submit_quota(committer, entry):
    """Atomically retain one explicit additional same-task paid submit."""
    from ai_video.production._state_commit_common import _state_invalid, _validated_transition
    from ai_video.production.models import StateCommitStatus, VideoAttemptPhase
    from ai_video.production.paid_provider import PaidProviderBudgetSnapshot
    from ai_video.production.paths import canonical_paid_provider_budget_path
    from ai_video.production.project import load_production_project

    if not isinstance(entry, PaidProviderSubmitQuotaExtension):
        raise _state_invalid("Paid Provider submit quota extension is invalid.")
    try:
        entry = PaidProviderSubmitQuotaExtension.model_validate_json(
            entry.model_dump_json()
        )
    except ValueError as exc:
        raise _state_invalid("Paid Provider submit quota extension seal is invalid.", str(exc)) from exc
    with committer._exclusive_lock():
        manifest = committer._read_manifest()
        current = manifest.active_paid_provider_budget
        if current is None:
            raise _state_invalid("Paid Provider submit quota extension requires an active ledger.")
        try:
            loaded = load_production_project(committer._project_root / "project.yaml")
            if loaded.manifest != manifest:
                raise ValueError("Manifest changed during submit quota extension validation")
        except Exception as exc:
            raise _state_invalid("Paid Provider submit quota extension requires a standard project reopen.", str(exc)) from exc
        budget = committer._reopen_paid_budget(current)
        existing = next(
            (item for item in budget.submit_quota_extensions
             if item.extension_id == entry.extension_id),
            None,
        )
        if existing is not None:
            if existing != entry:
                raise _state_invalid("Paid Provider submit quota extension ID collision differs.")
            return manifest
        if (
            entry.project_id != manifest.project_id
            or entry.explicit_opt_in is not True
            or not entry.authorization_receipt_id
            or entry.expected_manifest_revision != manifest.manifest_revision
            or entry.base_budget != current
            or not entry.valid_at(committer._paid_provider_clock())
            or budget.blocked
            or any(item.status.value == "unsettled" for item in budget.reservations)
        ):
            raise _state_invalid("Paid Provider submit quota extension preconditions are not current.")
        target = committer._video_attempt(manifest, entry.target_attempt_id)
        prior = committer._video_attempt(manifest, entry.prior_attempt_id)
        target_state = target.video_generation_state
        prior_state = prior.video_generation_state
        if (
            target.status is not StateCommitStatus.RUNNING
            or target_state is None
            or target_state.phase is not VideoAttemptPhase.REQUEST
            or target_state.execution_binding != entry.target_binding
            or target.paid_provider_state is not None
            or target_state.paid_submit_receipt is not None
            or target_state.local_submit_intent is not None
            or target_state.local_submit_receipt is not None
            or target_state.local_latest_observation is not None
            or target_state.local_fetch_receipt is not None
            or prior_state is None
            or prior_state.execution_binding != entry.prior_binding
            or any(
                item.attempt_id != entry.target_attempt_id
                and item.status in {
                    StateCommitStatus.RUNNING,
                    StateCommitStatus.OUTCOME_UNKNOWN,
                }
                for item in manifest.attempts
            )
            or any(
                item.attempt_id == entry.target_attempt_id
                for item in budget.reservations
            )
        ):
            raise _state_invalid("Paid Provider submit quota extension target is not an unsubmitted request.")
        try:
            target_binding = committer._reopen_generation_execution_binding(entry.target_binding)
            prior_binding = committer._reopen_generation_execution_binding(entry.prior_binding)
            target_binding.validate_request(committer._reopen_video_request(target_state.request))
            prior_binding.validate_request(committer._reopen_video_request(prior_state.request))
            target_limits = target_binding.inputs.limits
            prior_limits = prior_binding.inputs.limits
            same_task_limits = []
            durable_remote = set()
            for item in manifest.attempts:
                state = item.video_generation_state
                if state is None or state.execution_binding is None:
                    continue
                binding = committer._reopen_generation_execution_binding(state.execution_binding)
                limits = binding.inputs.limits
                if limits.task_id != entry.task_id:
                    continue
                if item.attempt_id != entry.target_attempt_id:
                    same_task_limits.append(limits.paid_submit_ceiling)
                if (
                    state.paid_submit_receipt is not None
                    or (
                        item.paid_provider_state is not None
                        and (
                            item.paid_provider_state.submit_receipt is not None
                            or item.paid_provider_state.phase.value == "submit_intent"
                        )
                    )
                ):
                    durable_remote.add(item.attempt_id)
            if (
                target_limits.task_id != entry.task_id
                or prior_limits.task_id != entry.task_id
                or target_limits.paid_submit_ceiling != entry.new_paid_submit_ceiling
                or prior_limits.paid_submit_ceiling != entry.old_paid_submit_ceiling
                or not same_task_limits
                or max(same_task_limits) != entry.old_paid_submit_ceiling
                or target_limits.paid_submits_used != len(durable_remote)
                or prior_limits.paid_submits_used > len(durable_remote)
            ):
                raise ValueError("same-task submit quota does not match durable bindings")
        except Exception as exc:
            raise _state_invalid("Paid Provider submit quota extension bindings are invalid.", str(exc)) from exc
        updated = PaidProviderBudgetSnapshot.create(
            revision=budget.revision + 1,
            policy_id=budget.policy_id,
            currency=budget.currency,
            project_ceiling_microunits=budget.project_ceiling_microunits,
            reservations=budget.reservations,
            ceiling_extensions=budget.ceiling_extensions,
            submit_quota_extensions=(*budget.submit_quota_extensions, entry),
            blocked=False,
        )
        artifact = _artifact(canonical_paid_provider_budget_path(updated.content_hash), updated)
        pointer = PaidProviderBudgetSnapshotPointer(
            path=artifact.relative_path,
            revision=updated.revision,
            content_hash=updated.content_hash,
            file_sha256=artifact.file_sha256,
        )
        committer._write_immutable_artifact(artifact, attempt_id=entry.extension_id)
        next_manifest = _validated_transition(manifest, {
            "manifest_revision": manifest.manifest_revision + 1,
            "active_paid_provider_budget": pointer,
        })
        committer._write_manifest_atomic(next_manifest)
        committer._reopen_paid_budget(pointer)
        return committer._read_manifest()
