"""Remote image orchestration owned exclusively by ProductionStateCommitter."""

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import StateCommitStatus
from ai_video.production.paid_provider import PaidProviderSubmitReceipt, PaidProviderSubmitOutcome
from ai_video.production.remote_image import remote_image_permit_binding
from ai_video.production._remote_image_reader import verify_remote_image_submit
from ai_video.production._state_commit_common import _canonical_json_bytes, _state_invalid, _timestamp, _validated_transition

_REMOTE_IMAGE_ACTIVATION_TOKEN = object()


class _DurableRemoteImageActivationPermit:
    """Post-submit activation proof; cannot authorize generation or another POST."""

    def __init__(self, token, *, fingerprint, validator):
        if token is not _REMOTE_IMAGE_ACTIVATION_TOKEN:
            raise TypeError("remote image activation proof belongs to the committer")
        self._fingerprint = fingerprint
        self._validator = validator

    def _image_generation_was_consumed(self, *, request_fingerprint):
        return request_fingerprint == self._fingerprint and self._validator()

    def __reduce__(self):
        raise TypeError("remote image activation proof cannot be serialized")


class _StateCommitRemoteImageMixin:
    def close_remote_image_materialization_failure(self, *, attempt_id,
            expected_manifest_revision, result_fingerprint, image_receipt_hash,
            actor_id, reason):
        """Explicitly reject an exact retained result, without any paid replay."""
        from datetime import datetime
        from ai_video.production.image_materialization_failure import (
            ImageMaterializationFailure, ImageMaterializationFailurePointer,
            load_retained_remote_image_result, verify_image_materialization_failure,
        )
        from ai_video.production.project import load_production_project
        with self._exclusive_lock():
            loaded = load_production_project(self._project_root / "project.yaml")
            manifest = loaded.manifest
            attempt = next((a for a in manifest.attempts if a.attempt_id == attempt_id), None)
            if attempt is None or attempt.operation != "image_generation":
                raise _state_invalid("Remote image materialization attempt is missing.")
            try:
                pointer = attempt.image_materialization_failure
                if pointer is not None:
                    verify_image_materialization_failure(loaded, attempt)
                    receipt = ImageMaterializationFailure.model_validate_json(
                        (self._project_root / pointer.path).read_bytes())
                    if (receipt.expected_manifest_revision != expected_manifest_revision
                            or receipt.result_fingerprint != result_fingerprint
                            or receipt.image_receipt_hash != image_receipt_hash
                            or receipt.actor_id != actor_id or receipt.reason != reason):
                        raise ValueError("closure replay differs")
                    return manifest
                if (manifest.manifest_revision != expected_manifest_revision
                        or attempt.status is not StateCommitStatus.OUTCOME_UNKNOWN
                        or attempt.image_phase != "materialize"
                        or any(value is not None for value in (attempt.candidate_project,
                            attempt.candidate_registry, attempt.candidate_dependency_graph,
                            attempt.candidate_dependency_states_hash))
                        or attempt.candidate_image_asset_ids
                        or (manifest.active_project, manifest.active_registry,
                            manifest.active_dependency_graph) != (attempt.base_project,
                            attempt.base_registry, attempt.base_dependency_graph)):
                    raise ValueError("closure context is not exact")
                request, preview, auth, result, measured, provenance = load_retained_remote_image_result(
                    self._project_root, attempt, result_fingerprint, image_receipt_hash)
                if self._image_receipt(request, preview, auth) != attempt.image_request:
                    raise ValueError("request summary differs")
                receipt = ImageMaterializationFailure.create(project_id=manifest.project_id,
                    attempt_id=attempt_id, expected_manifest_revision=expected_manifest_revision,
                    request_fingerprint=request.request_fingerprint,
                    result_fingerprint=result_fingerprint, image_receipt_hash=provenance.content_hash,
                    output_sha256=measured.sha256,
                    paid_submit_fingerprint=result.remote_evidence.submit_receipt.submit_receipt_fingerprint,
                    base_project_hash=attempt.base_project.content_hash,
                    base_registry_hash=attempt.base_registry.content_hash,
                    base_graph_hash=attempt.base_dependency_graph.content_hash,
                    actor_id=actor_id, reason=reason, recorded_at=datetime.fromisoformat(_timestamp()))
            except Exception:
                raise _state_invalid("Remote image failure closure evidence is not exact.") from None
            from pathlib import Path
            artifact = self.prepare_artifact(attempt_id,
                Path(f"state/images/materialization-failures/{receipt.content_hash}.json"),
                _canonical_json_bytes(receipt))
            pointer = ImageMaterializationFailurePointer(path=artifact.relative_path,
                content_hash=receipt.content_hash, file_sha256=artifact.file_sha256)
            failed = _validated_transition(attempt, {"status": StateCommitStatus.FAILED,
                "image_materialization_failure": pointer,
                "provider_request_id": result.provider_request_id,
                "finished_at": receipt.recorded_at.isoformat(),
                "error_code": ErrorCode.IMAGE_REQUEST_INVALID.value,
                "error_message": "Retained remote PNG rejected after local materialization failure."})
            updated = _validated_transition(manifest, {
                "manifest_revision": manifest.manifest_revision + 1,
                "attempts": tuple(failed if a.attempt_id == attempt_id else a for a in manifest.attempts)})
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            verify_image_materialization_failure(loaded.model_copy(update={"manifest": updated}), failed)
            self._write_manifest_atomic(updated)
            reopened = load_production_project(self._project_root / "project.yaml").manifest
            if reopened != updated:
                raise _state_invalid("Remote image failure closure reopen differs.")
            return reopened

    def generate_remote_image_asset(self, request, preview, authorization, provider):
        replay = self._exact_image_replay(request, preview, authorization)
        if replay is not None:
            return replay
        remote = authorization.remote_binding
        if remote is None or authorization.local_only:
            raise _state_invalid("remote image generation requires exact paid image authority")
        if self._image_candidate_preparer is None:
            raise _state_invalid("remote image generation requires its deterministic candidate preparer before submission")
        provider.preflight(request, authorization)
        self.begin_image_generation(request, preview, authorization)
        self.record_image_submit_intent(request, preview, authorization)
        permit = self.record_paid_provider_submit_intent(remote.preview,
            reservation_id=f"image-{request.attempt_id}")
        manifest = self._read_manifest()
        attempt = next(a for a in manifest.attempts if a.attempt_id == request.attempt_id)
        gate = self._reopen_paid_gate(attempt.paid_provider_state.gate_receipt)
        binding = remote_image_permit_binding(remote)
        try:
            result = provider.generate(request, authorization, permit, gate_receipt=gate)
            if not permit._paid_provider_operation_was_consumed(**binding):
                raise _state_invalid("remote image provider did not consume its exact paid permit")
            from ai_video.production.image import validate_image_result
            validate_image_result(request, authorization, result)
            if result.remote_evidence is None:
                raise _state_invalid("remote image result has no remote evidence")
        except Exception as exc:
            known = isinstance(exc, AiVideoError) and exc.code is ErrorCode.IMAGE_PROVIDER_FAILED
            self.record_paid_provider_submit_receipt(PaidProviderSubmitReceipt.create(
                attempt_id=request.attempt_id, request_fingerprint=request.request_fingerprint,
                preview_fingerprint=remote.preview.preview_fingerprint,
                gate_receipt_fingerprint=gate.gate_receipt_fingerprint,
                reservation_id=gate.reservation_id,
                outcome=(PaidProviderSubmitOutcome.KNOWN_NO_EFFECT if known else PaidProviderSubmitOutcome.OUTCOME_UNKNOWN),
                external_effect_id=None, recorded_at=self._paid_provider_clock()))
            raise AiVideoError(code=(ErrorCode.IMAGE_PROVIDER_FAILED if known else ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN),
                user_message="Remote image submit failed; the durable outcome forbids automatic retry.") from None
        self.record_paid_provider_submit_receipt(result.remote_evidence.submit_receipt)
        def current():
            try:
                m = self._read_manifest()
                a = next(a for a in m.attempts if a.attempt_id == request.attempt_id)
                if (a.status is not StateCommitStatus.RUNNING or a.image_phase != "submit_intent"
                        or m.active_project != request.base_project or m.active_registry != request.base_registry
                        or m.active_dependency_graph != request.base_dependency_graph):
                    return False
                verify_remote_image_submit(self._project_root, a, authorization, result.remote_evidence)
                self._validate_image_request_context(m, request, preview)
                self._reopen_image_evidence(request, preview, authorization, include_intent=True)
                return True
            except Exception:
                return False
        activation = _DurableRemoteImageActivationPermit(_REMOTE_IMAGE_ACTIVATION_TOKEN,
            fingerprint=request.request_fingerprint, validator=current)
        return self.activate_image_asset(request, preview, authorization, result, activation)
