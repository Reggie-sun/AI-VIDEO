"""Whole-ad source lifecycle owned exclusively by ProductionStateCommitter."""

import hashlib
from io import BytesIO

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.manifest_schema import ManifestCapability, require_manifest_version_for
from ai_video.production.models import StateCommitAttempt, StateCommitStatus
from ai_video.production.paid_provider import PaidProviderSubmitOutcome, PaidProviderSubmitReceipt
from ai_video.production.project import load_production_project
from ai_video.production.vidu_ad_contracts import AdGenerationRequest, AdGenerationState, AdSourceCandidate
from ai_video.production.vidu_ad_reader import validate_ad_images
from ai_video.production.vidu_download import parse_result_url
from ._state_commit_common import _canonical_json_bytes, _state_invalid, _timestamp, _validated_transition
from ._state_commit_contracts import PreparedArtifact


class _StateCommitAdMixin:
    def _ad_current(self, attempt_id, provider=None):
        loaded = load_production_project(self._project_root / "project.yaml")
        attempt = next((x for x in loaded.manifest.attempts if x.attempt_id == attempt_id), None)
        if attempt is None or attempt.ad_generation_state is None:
            raise _state_invalid("Whole-ad attempt does not exist.")
        if provider is not None and provider._profile.pointer().profile_sha256 != attempt.ad_generation_state.request.profile_hash:
            raise _state_invalid("Whole-ad Provider profile changed.")
        return loaded.manifest, attempt

    def _ad_replace(self, manifest, attempt, **updates):
        current = self._read_manifest()
        if current != manifest:
            raise _state_invalid("Whole-ad Manifest changed during the operation.")
        replacement = _validated_transition(attempt, updates)
        updated = _validated_transition(manifest, {
            "manifest_revision": manifest.manifest_revision + 1,
            "attempts": tuple(replacement if a.attempt_id == attempt.attempt_id else a for a in manifest.attempts),
        })
        self._write_manifest_atomic(updated)
        return replacement

    def prepare_ad_generation(self, *, attempt_id, request, provider):
        """Persist exact registered inputs and an explicit whole-ad task quota; no network."""
        request = AdGenerationRequest.model_validate_json(request.model_dump_json())
        with self._exclusive_lock():
            loaded = load_production_project(self._project_root / "project.yaml")
            manifest = loaded.manifest
            existing = next((a for a in manifest.attempts if a.attempt_id == attempt_id), None)
            if existing is not None:
                if (existing.ad_generation_state is None or existing.ad_generation_state.request != request
                        or provider._profile.pointer().profile_sha256 != request.profile_hash):
                    raise _state_invalid("Whole-ad attempt ID already belongs to different inputs.")
                return existing.ad_generation_state
            preview = provider.ad_preview(request, attempt_id)
            # Resolve and check the complete upload before recording an intent.
            provider._ad_body(request)
            if (request.project_id != manifest.project_id or request.project_hash != manifest.active_project.content_hash
                    or request.registry_hash != manifest.active_registry.content_hash):
                raise _state_invalid("Whole-ad request does not bind the selected project and registry.")
            state = AdGenerationState(request=request, preview_fingerprint=preview.preview_fingerprint)
            attempt = StateCommitAttempt(
                attempt_id=attempt_id, operation="ad_generation", status=StateCommitStatus.RUNNING,
                base_manifest_revision=manifest.manifest_revision, base_project=manifest.active_project,
                base_registry=manifest.active_registry, candidate_artifacts_hash=request.content_hash,
                ad_generation_state=state, started_at=_timestamp(),
            )
            try:
                validate_ad_images(self._project_root, attempt)
            except ValueError as exc:
                raise _state_invalid("Whole-ad image binding does not match registered evidence.") from exc
            siblings = [a.ad_generation_state.request for a in manifest.attempts
                        if a.ad_generation_state is not None and a.ad_generation_state.request.task_id == request.task_id]
            if any((r.submit_limit, r.policy_id) != (request.submit_limit, request.policy_id) for r in siblings):
                raise _state_invalid("Whole-ad task quota cannot be changed by a new attempt.")
            for path, model in ((request.path, request),
                                (provider._profile.pointer().profile_path, provider._profile)):
                raw = _canonical_json_bytes(model)
                self._write_immutable_artifact(PreparedArtifact(relative_path=path, payload=raw,
                    file_sha256=hashlib.sha256(raw).hexdigest()), attempt_id=attempt_id)
            updated = _validated_transition(manifest, {
                "schema_version": require_manifest_version_for(manifest.schema_version, ManifestCapability.AD_GENERATION),
                "manifest_revision": manifest.manifest_revision + 1,
                "attempts": manifest.attempts + (attempt,),
            })
            self._write_manifest_atomic(updated)
            return state

    def submit_ad_generation(self, *, attempt_id, provider):
        """At most one POST for this durable attempt, including across restarts."""
        _, attempt = self._ad_current(attempt_id, provider)
        paid = attempt.paid_provider_state
        if paid is not None:
            if paid.phase.value in {"accepted", "settled"} and paid.submit_receipt is not None:
                return self._reopen_paid_submit(paid.submit_receipt).external_effect_id
            raise _state_invalid("Whole-ad submit already has an intent or terminal outcome; do not retry.")
        if attempt.status is not StateCommitStatus.RUNNING:
            raise _state_invalid("Whole-ad attempt is not runnable.")
        request = attempt.ad_generation_state.request
        preview = provider.ad_preview(request, attempt_id)
        provider._ad_body(request)
        permit = self.record_paid_provider_submit_intent(preview, reservation_id=f"ad-{attempt_id}")
        _, current = self._ad_current(attempt_id, provider)
        paid = current.paid_provider_state
        gate = self._reopen_paid_gate(paid.gate_receipt)
        task_id = None
        failure = None
        try:
            task_id = provider.submit_ad(request, preview, gate.authorization, permit)
            outcome = PaidProviderSubmitOutcome.ACCEPTED
        except Exception as exc:
            failure = exc
            # Only an explicit provider rejection proves no effect. All other
            # exceptions keep the reserved budget and block resubmission.
            outcome = (PaidProviderSubmitOutcome.KNOWN_NO_EFFECT if isinstance(exc, AiVideoError)
                       and exc.code == ErrorCode.PAID_PROVIDER_KNOWN_NO_EFFECT
                       else PaidProviderSubmitOutcome.OUTCOME_UNKNOWN)
        receipt = PaidProviderSubmitReceipt.create(
            attempt_id=attempt_id, request_fingerprint=request.content_hash,
            preview_fingerprint=preview.preview_fingerprint,
            gate_receipt_fingerprint=gate.gate_receipt_fingerprint,
            reservation_id=paid.reservation_id, outcome=outcome, external_effect_id=task_id,
            recorded_at=self._paid_provider_clock(),
        )
        self.record_paid_provider_submit_receipt(receipt)
        if failure is not None:
            raise AiVideoError(code=(ErrorCode.PAID_PROVIDER_KNOWN_NO_EFFECT
                              if outcome is PaidProviderSubmitOutcome.KNOWN_NO_EFFECT
                              else ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN),
                               user_message="Whole-ad submit did not complete; automatic retry is forbidden.") from None
        return task_id

    def query_ad_generation(self, *, attempt_id, provider):
        """One explicit query; known provider failure remains a consumed paid request."""
        with self._exclusive_lock():
            manifest, attempt = self._ad_current(attempt_id, provider)
            state = attempt.ad_generation_state
            if state.candidate is not None or attempt.status is StateCommitStatus.FAILED:
                return state
            paid = attempt.paid_provider_state
            if paid is None or paid.phase.value not in {"accepted", "settled"} or paid.submit_receipt is None:
                raise _state_invalid("Whole-ad query requires a known accepted task.")
            receipt = self._reopen_paid_submit(paid.submit_receipt)
            observation, _, _ = provider._ad_status(receipt.external_effect_id)
            updates = {"ad_generation_state": state.model_copy(update={"observation": observation})}
            if observation == "failed":
                updates.update(status=StateCommitStatus.FAILED, finished_at=_timestamp(),
                               error_code=ErrorCode.VIDEO_PROVIDER_FAILED.value,
                               error_message="Whole-ad Provider task failed after acceptance.")
            if observation == state.observation:
                return state
            return self._ad_replace(manifest, attempt, **updates).ad_generation_state

    def fetch_ad_generation(self, *, attempt_id, provider):
        """Fetch an exact result as immutable, unaccepted source bytes, never activate."""
        with self._exclusive_lock():
            manifest, attempt = self._ad_current(attempt_id, provider)
            state = attempt.ad_generation_state
            if state.candidate is not None:
                return state.candidate
            paid = attempt.paid_provider_state
            if (attempt.status is not StateCommitStatus.RUNNING or paid is None
                    or paid.phase.value not in {"accepted", "settled"} or paid.submit_receipt is None):
                raise _state_invalid("Whole-ad fetch requires a known accepted task.")
            receipt = self._reopen_paid_submit(paid.submit_receipt)
            task_id = receipt.external_effect_id
            observation, creation_id, url = provider._ad_status(task_id)
            if observation != "success" or creation_id is None or url is None:
                raise _state_invalid("Whole-ad task has no successful result to fetch.")
            with BytesIO() as sink:
                digest, size = provider._stream_mp4(url, sink)
                # Re-query identity before publication; signed URL rotation is allowed.
                after, after_id, _ = provider._ad_status(task_id)
                if (after, after_id) != ("success", creation_id):
                    raise _state_invalid("Whole-ad creation changed during download.")
                candidate = AdSourceCandidate(
                    request_hash=state.request.content_hash, submit_receipt_hash=receipt.submit_receipt_fingerprint,
                    task_id=task_id, creation_id=creation_id, sha256=digest, size_bytes=size,
                    locator_sha256=hashlib.sha256(url.encode()).hexdigest(),
                    remote_origin=parse_result_url(url).origin, downloaded_at=self._paid_provider_clock(),
                )
                self._write_immutable_artifact(PreparedArtifact(relative_path=candidate.path,
                    payload=sink.getvalue(), file_sha256=digest), attempt_id=attempt_id)
                evidence = _canonical_json_bytes(candidate)
                self._write_immutable_artifact(PreparedArtifact(relative_path=candidate.receipt_path,
                    payload=evidence, file_sha256=hashlib.sha256(evidence).hexdigest()), attempt_id=attempt_id)
            updated_state = state.model_copy(update={"observation": "success", "candidate": candidate})
            self._ad_replace(manifest, attempt, ad_generation_state=updated_state,
                             status=StateCommitStatus.SUCCEEDED, finished_at=_timestamp())
            return candidate
