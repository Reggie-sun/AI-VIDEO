"""Sole-committer runtime-repair registration and one-use validation."""
from __future__ import annotations

import hashlib

from ai_video.production._lifecycle_schema import RuntimeRepairAuthorizationPointer
from ai_video.production._state_commit_common import (
    _canonical_json_bytes, _state_invalid, _validated_transition,
)
from ai_video.production._state_commit_contracts import PreparedArtifact
from ai_video.production.generation_runtime_repair import (
    LocalRuntimeRepairExtension,
    PaidKnownFailureRetarget,
    PaidNoEffectRetarget,
)
from ai_video.production.models import StateCommitStatus


def _artifact(path, model):
    payload = _canonical_json_bytes(model)
    return PreparedArtifact(relative_path=path, payload=payload,
                            file_sha256=hashlib.sha256(payload).hexdigest())


def register_runtime_repair_authorization(
    self,
    *,
    attempt_id: str,
    repair_basis: str,
    actor,
    evidence_hash: str | None = None,
    local_extension: LocalRuntimeRepairExtension | None = None,
    paid_no_effect_retarget: PaidNoEffectRetarget | None = None,
    paid_known_failure_retarget: PaidKnownFailureRetarget | None = None,
) -> RuntimeRepairAuthorizationPointer:
    """Authorize one bounded re-execution after a repaired local runtime failure.

    The attempt must be FAILED with durable ``runtime_failure`` evidence; the
    grant is per-Shot capped and one-use (consumed by the replacement submit
    intent inside the same atomic write).  Re-recording the same evidence
    returns the existing pointer unchanged.
    """

    from ai_video.production.generation_runtime_repair import (
        MAX_RUNTIME_REPAIRS_PER_SHOT,
        RuntimeRepairAuthorization,
        runtime_repair_artifact_path,
    )

    if not isinstance(repair_basis, str) or not repair_basis.strip():
        raise _state_invalid("Runtime repair requires an explicit repair basis.")
    if paid_no_effect_retarget is not None:
        if (not isinstance(paid_no_effect_retarget, PaidNoEffectRetarget)
                or local_extension is not None or paid_known_failure_retarget is not None):
            raise _state_invalid("Paid retarget requires its exact typed scope and no local extension.")
        paid_no_effect_retarget = PaidNoEffectRetarget.model_validate_json(
            paid_no_effect_retarget.model_dump_json())
    if paid_known_failure_retarget is not None:
        if (not isinstance(paid_known_failure_retarget, PaidKnownFailureRetarget)
                or local_extension is not None or paid_no_effect_retarget is not None):
            raise _state_invalid(
                "Paid known-failure retarget requires its exact typed scope and no other repair mode."
            )
        try:
            paid_known_failure_retarget = PaidKnownFailureRetarget.model_validate_json(
                paid_known_failure_retarget.model_dump_json())
        except ValueError:
            raise _state_invalid("Paid known-failure retarget must be typed and exact.") from None
    if local_extension is not None:
        if not isinstance(local_extension, LocalRuntimeRepairExtension):
            raise _state_invalid("Runtime repair extension must be typed and exact.")
        try:
            local_extension = LocalRuntimeRepairExtension.model_validate_json(
                local_extension.model_dump_json())
        except ValueError:
            raise _state_invalid("Runtime repair extension must be typed and exact.") from None
    with self._exclusive_lock():
        manifest = self._read_manifest()
        attempt = self._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if attempt.status is not StateCommitStatus.FAILED or state is None:
            raise _state_invalid("Runtime repair requires a failed video attempt.")
        if not state.generation_experiences:
            raise _state_invalid(
                "Runtime repair requires durable runtime failure evidence."
            )
        experience = self._reopen_generation_experience(
            state.generation_experiences[-1]
        )
        failures = [
            e for e in experience.evidence if e.outcome == "runtime_failure"
        ]
        if not failures:
            raise _state_invalid(
                "Runtime repair requires a runtime_failure outcome evidence."
            )
        failure = failures[-1]
        if paid_no_effect_retarget is not None:
            receipt = closed_paid_no_effect_receipt(self, attempt)
            request = self._reopen_video_request(state.request)
            binding = self._reopen_generation_execution_binding(state.execution_binding)
            if (receipt.submit_receipt_fingerprint != paid_no_effect_retarget.submit_receipt_fingerprint
                    or failure.attempt_id != attempt_id
                    or failure.request_hash != request.request_input_hash
                    or failure.task_id != binding.inputs.limits.task_id
                    or failure.shot_id != binding.context.target_shot_id):
                raise _state_invalid("Paid retarget does not match the exact failed receipt and evidence.")
            _require_latest_local_failure(self, manifest, attempt_id, failure.shot_id)
        if paid_known_failure_retarget is not None:
            receipt, _submission, observation, request = closed_paid_known_failure_proof(
                self, attempt
            )
            binding = self._reopen_generation_execution_binding(state.execution_binding)
            binding.validate_request(request)
            if (
                receipt.submit_receipt_fingerprint
                    != paid_known_failure_retarget.paid_submit_receipt_fingerprint
                or observation.observation_fingerprint
                    != paid_known_failure_retarget.failed_observation_fingerprint
                or failure.attempt_id != attempt_id
                or failure.request_hash != request.request_input_hash
                or failure.task_id != binding.inputs.limits.task_id
                or failure.shot_id != binding.context.target_shot_id
            ):
                raise _state_invalid(
                    "Paid known-failure retarget does not match the exact accepted task and failure evidence."
                )
            _require_latest_same_shot_attempt(
                self, manifest, attempt_id, binding.context.target_shot_id
            )
        if evidence_hash is not None and evidence_hash != failure.evidence_hash:
            raise _state_invalid(
                "Runtime repair evidence hash does not match the durable runtime failure."
            )
        for item in manifest.attempts:
            prior = item.video_generation_state
            if prior is None:
                continue
            for pointer in prior.runtime_repairs:
                if pointer.evidence_hash == failure.evidence_hash:
                    if local_extension is not None or paid_no_effect_retarget is not None:
                        existing = self._reopen_runtime_repair_authorization(pointer)
                        if (existing.local_extension != local_extension
                                or existing.paid_no_effect_retarget != paid_no_effect_retarget
                                or existing.paid_known_failure_retarget != paid_known_failure_retarget
                                or existing.actor != actor or existing.repair_basis != repair_basis):
                            raise _state_invalid("Runtime repair extension replay identity mismatch.")
                    if paid_known_failure_retarget is not None:
                        existing = self._reopen_runtime_repair_authorization(pointer)
                        if (existing.paid_known_failure_retarget != paid_known_failure_retarget
                                or existing.actor != actor or existing.repair_basis != repair_basis):
                            raise _state_invalid("Paid known-failure retarget replay identity mismatch.")
                    return pointer
        request = self._reopen_video_request(state.request)
        scope = request.activation_scope
        if scope is None:
            raise _state_invalid("Runtime repair requires a verifiable Shot scope.")
        grants = []
        for item in manifest.attempts:
            prior = item.video_generation_state
            if prior is None or not prior.runtime_repairs:
                continue
            prior_request = self._reopen_video_request(prior.request)
            prior_scope = prior_request.activation_scope
            if (
                prior_scope is None
                or prior_scope.request.target_shot_id != scope.request.target_shot_id
            ):
                continue
            grants.extend(prior.runtime_repairs)
        granted = len(grants)
        ceiling = MAX_RUNTIME_REPAIRS_PER_SHOT
        if local_extension is not None:
            if granted != local_extension.ceiling - 1:
                raise _state_invalid("Runtime repair budget is exhausted or extension is premature.")
            if state.execution_binding is None:
                raise _state_invalid("Runtime repair extension requires a sealed execution binding.")
            binding = self._reopen_generation_execution_binding(state.execution_binding)
            binding.validate_request(request)
            require_local_extension_scope(local_extension, binding)
            if (local_extension.failed_binding_hash != binding.binding_hash
                    or local_extension.expected_manifest_revision != manifest.manifest_revision):
                raise _state_invalid("Runtime repair extension binding or Manifest revision mismatch.")
            if (failure.task_id != local_extension.task_id
                    or failure.shot_id != local_extension.shot_id
                    or failure.attempt_id != attempt_id
                    or any(not p.consumed for p in grants)
                    or any(self._reopen_runtime_repair_authorization(p).actor != actor for p in grants)):
                raise _state_invalid("Runtime repair extension evidence, actor or prior grants mismatch.")
            for grant in grants:
                prior_state = self._video_attempt(manifest, grant.attempt_id).video_generation_state
                if prior_state.execution_binding is None:
                    raise _state_invalid("Runtime repair extension prior task binding is missing.")
                prior_binding = self._reopen_generation_execution_binding(prior_state.execution_binding)
                require_local_extension_scope(local_extension, prior_binding)
            _require_latest_local_failure(self, manifest, attempt_id, local_extension.shot_id)
            ceiling = local_extension.ceiling
        if granted >= ceiling:
            raise _state_invalid("Runtime repair budget is exhausted for this Shot.")
        authorization = RuntimeRepairAuthorization.create(
            schema_version=("runtime-repair/4" if paid_known_failure_retarget is not None else
                "runtime-repair/3" if paid_no_effect_retarget is not None else
                "runtime-repair/2" if local_extension is not None else "runtime-repair/1"),
            local_extension=local_extension,
            paid_no_effect_retarget=paid_no_effect_retarget,
            paid_known_failure_retarget=paid_known_failure_retarget,
            attempt_id=attempt_id,
            evidence_hash=failure.evidence_hash,
            repair_basis=repair_basis,
            actor=actor,
            expected_manifest_revision=manifest.manifest_revision + 1,
        )
        artifact = _artifact(
            runtime_repair_artifact_path(authorization.content_hash), authorization
        )
        pointer = RuntimeRepairAuthorizationPointer(
            path=artifact.relative_path,
            content_hash=authorization.content_hash,
            attempt_id=attempt_id,
            evidence_hash=failure.evidence_hash,
            consumed=False,
            file_sha256=artifact.file_sha256,
        )
        self._write_immutable_artifact(artifact, attempt_id=attempt_id)
        next_state = state.model_copy(
            update={"runtime_repairs": (*state.runtime_repairs, pointer)}
        )
        next_attempt = _validated_transition(
            attempt, {"video_generation_state": next_state}
        )
        next_manifest = _validated_transition(
            manifest,
            {
                "manifest_revision": manifest.manifest_revision + 1,
                "attempts": tuple(
                    next_attempt if item.attempt_id == attempt_id else item
                    for item in manifest.attempts
                ),
            },
        )
        self._write_manifest_atomic(next_manifest)
        self._reopen_runtime_repair_authorization(pointer)
        return pointer

def require_runtime_repair_grant(self, manifest, binding):
    repair = binding.decision.runtime_repair
    if repair is None:
        return None
    prior = self._video_attempt(manifest, repair.attempt_id)
    prior_state = prior.video_generation_state
    pointer = next(
        (
            p
            for p in (prior_state.runtime_repairs if prior_state else ())
            if p.attempt_id == repair.attempt_id
            and p.evidence_hash == repair.evidence_hash
        ),
        None,
    )
    if pointer is None or pointer.consumed:
        raise _state_invalid("Runtime repair grant is unavailable.")
    if pointer.content_hash != repair.content_hash:
        raise _state_invalid("Runtime repair grant identity mismatch.")
    if self._reopen_runtime_repair_authorization(pointer) != repair:
        raise _state_invalid(
            "Runtime repair grant does not match the durable receipt."
        )
    if repair.paid_no_effect_retarget is not None:
        from ai_video.production.generation_runtime_repair import retarget_preserves_strategy
        receipt = closed_paid_no_effect_receipt(self, prior)
        old_binding = self._reopen_generation_execution_binding(prior_state.execution_binding)
        old = next(c for c in old_binding.inputs.candidates
                   if c.candidate_id == old_binding.decision.selected_candidate_id)
        target = next(c for c in binding.inputs.candidates
                      if c.candidate_id == binding.decision.selected_candidate_id)
        if (receipt.submit_receipt_fingerprint != repair.paid_no_effect_retarget.submit_receipt_fingerprint
                or target.scope_hash != repair.paid_no_effect_retarget.target_scope_hash
                or old_binding.inputs.limits.task_id != binding.inputs.limits.task_id
                or old_binding.context.target_shot_id != binding.context.target_shot_id
                or binding.inputs.latest_attempt_hash != repair.evidence_hash
                or not retarget_preserves_strategy(old, target)):
            raise _state_invalid("Paid retarget does not match the exact authorized strategy and failure.")
        _require_latest_local_failure(self, manifest, prior.attempt_id, binding.context.target_shot_id)
    if repair.paid_known_failure_retarget is not None:
        from ai_video.production.generation_runtime_repair import (
            paid_failure_retarget_preserves_strategy,
        )

        receipt, _submission, observation, request = closed_paid_known_failure_proof(
            self, prior
        )
        old_binding = self._reopen_generation_execution_binding(prior_state.execution_binding)
        old = next(c for c in old_binding.inputs.candidates
                   if c.candidate_id == old_binding.decision.selected_candidate_id)
        target = next(c for c in binding.inputs.candidates
                      if c.candidate_id == binding.decision.selected_candidate_id)
        if (
            receipt.submit_receipt_fingerprint
                != repair.paid_known_failure_retarget.paid_submit_receipt_fingerprint
            or observation.observation_fingerprint
                != repair.paid_known_failure_retarget.failed_observation_fingerprint
            or target.scope_hash != repair.paid_known_failure_retarget.target_scope_hash
            or old_binding.inputs.limits.task_id != binding.inputs.limits.task_id
            or old_binding.context.target_shot_id != binding.context.target_shot_id
            or binding.inputs.latest_attempt_hash != repair.evidence_hash
            or not paid_failure_retarget_preserves_strategy(old, target)
        ):
            raise _state_invalid(
                "Paid known-failure retarget does not match the exact authorized strategy and failure."
            )
        _require_latest_same_shot_attempt(
            self, manifest, prior.attempt_id, binding.context.target_shot_id,
            successor_binding=binding,
        )
    if repair.local_extension is not None:
        require_local_extension_scope(repair.local_extension, binding)
        if (prior.status is not StateCommitStatus.FAILED
                or prior_state.execution_binding is None
                or prior_state.execution_binding.binding_hash != repair.local_extension.failed_binding_hash):
            raise _state_invalid("Runtime repair extension source failure binding mismatch.")
    return repair


def submit_attempts_with_consumed_repair(manifest, next_attempt, repair):
    """Select intent and consume the already verified grant in one Manifest write."""
    attempts = []
    for item in manifest.attempts:
        if item.attempt_id == next_attempt.attempt_id:
            attempts.append(next_attempt)
        elif repair is not None and item.attempt_id == repair.attempt_id:
            state = item.video_generation_state.model_copy(update={"runtime_repairs": tuple(
                p.model_copy(update={"consumed": True})
                if p.content_hash == repair.content_hash else p
                for p in item.video_generation_state.runtime_repairs)})
            attempts.append(_validated_transition(item, {"video_generation_state": state}))
        else:
            attempts.append(item)
    return tuple(attempts)


def closed_paid_no_effect_receipt(committer, attempt):
    """Read canonical terminal proof; a physical rejection remains submitted."""
    from ai_video.production._lifecycle_schema import PaidProviderAttemptPhase
    from ai_video.production.paid_provider import PaidProviderSubmitOutcome

    state, paid = attempt.video_generation_state, attempt.paid_provider_state
    if (attempt.status is not StateCommitStatus.FAILED or state is None or paid is None
            or paid.phase is not PaidProviderAttemptPhase.KNOWN_NO_EFFECT
            or paid.submit_receipt is None
            or state.paid_submit_receipt is not None and state.paid_submit_receipt != paid.submit_receipt
            or state.execution_binding is None or state.quality_rejection is not None
            or any(getattr(state, name) is not None for name in
                ("fetch_receipt", "local_fetch_receipt", "latest_observation", "local_latest_observation",
                 "provider_file_id", "local_submit_intent", "local_submit_receipt"))):
        raise _state_invalid("Paid recovery requires an exact closed known-no-effect attempt.")
    receipt = committer._reopen_paid_submit(paid.submit_receipt)
    request = committer._reopen_video_request(state.request)
    if (receipt.outcome is not PaidProviderSubmitOutcome.KNOWN_NO_EFFECT
            or receipt.external_effect_id is not None or receipt.no_effect_reconciliation is not None
            or receipt.attempt_id != attempt.attempt_id
            or receipt.request_fingerprint != request.resolved_generation_hash):
        raise _state_invalid("Paid recovery receipt does not match the physical failed request.")
    return receipt


def closed_paid_known_failure_proof(committer, attempt):
    """Reopen an accepted paid submit and its exact terminal FAILED observation."""
    from ai_video.production._lifecycle_schema import (
        PaidProviderAttemptPhase,
        VideoAttemptPhase,
    )
    from ai_video.production.paid_provider import PaidProviderSubmitOutcome
    from ai_video.production.video import VideoSubmission, VideoTaskState

    state, paid = attempt.video_generation_state, attempt.paid_provider_state
    if (
        attempt.status is not StateCommitStatus.FAILED
        or state is None
        or paid is None
        or paid.phase not in {
            PaidProviderAttemptPhase.ACCEPTED,
            PaidProviderAttemptPhase.SETTLED,
        }
        or paid.submit_receipt is None
        or state.paid_submit_receipt != paid.submit_receipt
        or state.execution_binding is None
        or state.latest_observation is None
        or state.phase is not VideoAttemptPhase.POLLING
        or state.quality_rejection is not None
        or any(getattr(state, name) is not None for name in (
            "fetch_receipt",
            "local_submit_intent",
            "local_submit_receipt",
            "local_latest_observation",
            "local_fetch_receipt",
            "provider_file_id",
            "terminal_frame_evidence",
            "terminal_frame_extraction",
            "continuity_evaluation",
            "commercial_evaluation",
            "source_boundary_evaluation",
        ))
        or state.candidate_video_asset_ids
        or state.candidate_continuity_asset_ids
    ):
        raise _state_invalid(
            "Paid recovery requires an exact accepted task with a terminal FAILED observation and no output."
        )

    receipt = committer._reopen_paid_submit(paid.submit_receipt)
    request = committer._reopen_video_request(state.request)
    binding = committer._reopen_generation_execution_binding(state.execution_binding)
    binding.validate_request(request)
    if (
        receipt.outcome is not PaidProviderSubmitOutcome.ACCEPTED
        or receipt.external_effect_id is None
        or receipt.attempt_id != attempt.attempt_id
        or receipt.request_fingerprint != request.resolved_generation_hash
    ):
        raise _state_invalid("Paid recovery receipt does not match the accepted video request.")
    try:
        submission = VideoSubmission.from_paid_submit_receipt(
            resolved=request,
            receipt=receipt,
        )
    except Exception as exc:
        raise _state_invalid("Paid video submission could not be reconstructed.", str(exc)) from exc
    observation = committer._reopen_video_status(state.latest_observation)
    pointer = state.latest_observation
    if (
        observation.state is not VideoTaskState.FAILED
        or observation.provider_file_id is not None
        or observation.submission_fingerprint != submission.submission_fingerprint
        or observation.paid_submit_receipt_fingerprint != receipt.submit_receipt_fingerprint
        or pointer.observation_fingerprint != observation.observation_fingerprint
        or pointer.request_receipt_fingerprint != state.request.request_receipt_fingerprint
        or pointer.paid_submit_receipt_fingerprint != receipt.submit_receipt_fingerprint
    ):
        raise _state_invalid("Paid recovery observation is not the exact normalized FAILED result.")
    if not state.generation_experiences:
        raise _state_invalid("Paid recovery has no retained runtime-failure evidence.")
    experience = committer._reopen_generation_experience(state.generation_experiences[-1])
    candidate = next(c for c in binding.inputs.candidates
                     if c.candidate_id == binding.decision.selected_candidate_id)
    if experience.projection != binding.projection or experience.candidate != candidate:
        raise _state_invalid("Paid recovery evaluation differs from the exact failed generation binding.")
    if not experience.evidence:
        raise _state_invalid("Paid recovery has no retained runtime-failure evidence.")
    evidence = experience.evidence[-1]
    if (
        evidence.outcome != "runtime_failure"
        or evidence.attempt_id != attempt.attempt_id
        or evidence.request_hash != request.request_input_hash
        or evidence.task_id != binding.inputs.limits.task_id
        or evidence.shot_id != binding.context.target_shot_id
        or evidence.recipe_scope_hash != candidate.scope_hash
        or evidence.artifact_sha256 is not None
        or evidence.findings
        or evidence.unresolved_quality_refs
        or evidence.facts_hash != binding.inputs.facts_hash
        or evidence.rubric_hash != binding.inputs.rubric_hash
        or experience.evaluation_sources
    ):
        raise _state_invalid("Paid recovery evidence is not the exact media-free failed evaluation.")
    return receipt, submission, observation, request

def require_local_extension_scope(extension, binding):
    selected = next(c for c in binding.inputs.candidates
                    if c.candidate_id == binding.decision.selected_candidate_id)
    variant = next(v for v in selected.capabilities.variants
                   if v.capability_id == selected.capability_id)
    if (variant.execution_kind.value != "local"
            or variant.billing_kind.value != "local_unmetered"
            or binding.inputs.limits.task_id != extension.task_id
            or binding.context.target_shot_id != extension.shot_id):
        raise _state_invalid("Runtime repair extension scope requires the exact local/unmetered task and Shot.")

def _require_latest_local_failure(self, manifest, attempt_id, shot_id):
    submitted = []
    for attempt in manifest.attempts:
        state = attempt.video_generation_state
        if state is None:
            continue
        request = self._reopen_video_request(state.request)
        scope = request.activation_scope
        if scope is None or scope.request.target_shot_id != shot_id:
            continue
        if (state.local_submit_intent is not None or state.paid_submit_receipt is not None
                or attempt.paid_provider_state is not None):
            submitted.append(attempt.attempt_id)
    if not submitted or submitted[-1] != attempt_id:
        raise _state_invalid("Runtime repair extension requires the latest known local failure.")


def _require_latest_same_shot_attempt(
    self,
    manifest,
    attempt_id,
    shot_id,
    *,
    successor_binding=None,
):
    history = []
    successors = []
    for attempt in manifest.attempts:
        state = attempt.video_generation_state
        if state is None:
            continue
        request = self._reopen_video_request(state.request)
        scope = request.activation_scope
        if scope is None or scope.request.target_shot_id != shot_id:
            continue
        if (successor_binding is not None
                and state.execution_binding is not None
                and state.execution_binding.binding_hash == successor_binding.binding_hash):
            if (attempt.status is not StateCommitStatus.RUNNING
                    or state.phase.value != "request"
                    or state.paid_submit_receipt is not None
                    or state.latest_observation is not None
                    or state.fetch_receipt is not None):
                raise _state_invalid("Paid recovery successor is no longer an unsubmitted task.")
            successors.append(attempt.attempt_id)
        else:
            history.append(attempt.attempt_id)
    if len(successors) > 1 or not history or history[-1] != attempt_id:
        raise _state_invalid("Paid recovery requires the latest attempt for the same Shot.")
