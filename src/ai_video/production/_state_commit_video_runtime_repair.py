"""Sole-committer runtime-repair registration and one-use validation."""
from __future__ import annotations

import hashlib

from ai_video.production._lifecycle_schema import RuntimeRepairAuthorizationPointer
from ai_video.production._state_commit_common import (
    _canonical_json_bytes, _state_invalid, _validated_transition,
)
from ai_video.production._state_commit_contracts import PreparedArtifact
from ai_video.production.generation_runtime_repair import LocalRuntimeRepairExtension
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
                    if local_extension is not None:
                        existing = self._reopen_runtime_repair_authorization(pointer)
                        if (existing.local_extension != local_extension
                                or existing.actor != actor or existing.repair_basis != repair_basis):
                            raise _state_invalid("Runtime repair extension replay identity mismatch.")
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
            schema_version="runtime-repair/2" if local_extension is not None else "runtime-repair/1",
            local_extension=local_extension,
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
    if repair.local_extension is not None:
        require_local_extension_scope(repair.local_extension, binding)
        if (prior.status is not StateCommitStatus.FAILED
                or prior_state.execution_binding is None
                or prior_state.execution_binding.binding_hash != repair.local_extension.failed_binding_hash):
            raise _state_invalid("Runtime repair extension source failure binding mismatch.")
    return repair

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
        if state.local_submit_intent is not None or state.paid_submit_receipt is not None:
            submitted.append(attempt.attempt_id)
    if not submitted or submitted[-1] != attempt_id:
        raise _state_invalid("Runtime repair extension requires the latest known local failure.")
