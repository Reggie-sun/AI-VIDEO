"""The explicit committer-owned close for known raw-media quality failure."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ai_video.errors import ErrorCode
from ai_video.production._lifecycle_schema import GenerationQualityRejectionReceiptPointer
from ai_video.production._state_commit_common import (
    _canonical_json_bytes,
    _state_invalid,
    _timestamp,
    _validated_transition,
)
from ai_video.production.generation_rejection import (
    GenerationQualityRejectionReceipt,
    validate_quality_rejection_experience,
    unresolved_generation_requirements,
)
from ai_video.production.models import StateCommitStatus, VideoAttemptPhase

from ._state_commit_contracts import PreparedArtifact


def _artifact(path: Path, model) -> PreparedArtifact:
    payload = _canonical_json_bytes(model)
    return PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest())


class _StateCommitGenerationRejectionMixin:
    def _reopen_generation_quality_rejection(self, pointer):
        from ai_video.production._generation_feedback_reader import (
            load_generation_quality_rejection,
        )

        return load_generation_quality_rejection(self._project_root, pointer)

    def reject_video_generation(
        self,
        *,
        attempt_id: str,
        expected_manifest_revision: int,
        experience_content_hash: str,
        actor,
    ):
        """Close only a current fetched media quality failure with exact evidence."""

        return self._close_video_quality_result(attempt_id=attempt_id,
            expected_manifest_revision=expected_manifest_revision,
            experience_content_hash=experience_content_hash, actor=actor, reason=None)

    def abandon_video_generation(
        self, *, attempt_id: str, expected_manifest_revision: int,
        experience_content_hash: str, actor, reason: str,
    ):
        """Explicitly discard failed media after same-bytes proof repair is exhausted.

        The actor supplies the exhaustion rationale; no finding is changed and
        this closure does not authorize another submit or imply acceptance.
        """
        if not isinstance(reason, str) or not reason.strip():
            raise _state_invalid("Abandonment requires an explicit evidence-repair exhaustion reason.")
        return self._close_video_quality_result(attempt_id=attempt_id,
            expected_manifest_revision=expected_manifest_revision,
            experience_content_hash=experience_content_hash, actor=actor, reason=reason)

    def _close_video_quality_result(
        self, *, attempt_id, expected_manifest_revision, experience_content_hash, actor, reason,
    ):

        from ai_video.production.project import load_production_project

        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._video_attempt(manifest, attempt_id)
            state = attempt.video_generation_state
            if state is None:
                raise _state_invalid("Video generation state is missing.")
            if state.quality_rejection is not None:
                # This one standard-reader seam verifies status, exact media,
                # execution binding, evaluator source identity and diagnosis.
                load_production_project(self._project_root / "project.yaml")
                receipt = self._reopen_generation_quality_rejection(state.quality_rejection)
                if (
                    expected_manifest_revision != receipt.expected_manifest_revision
                    or receipt.experience_content_hash != experience_content_hash
                    or receipt.actor != actor
                    or receipt.abandonment_reason != reason
                ):
                    raise _state_invalid("Quality rejection replay differs from retained evidence.")
                return manifest
            if expected_manifest_revision != manifest.manifest_revision:
                raise _state_invalid("Quality rejection Manifest revision is stale.")
            if (
                attempt.status is not StateCommitStatus.RUNNING
                or state.phase is not VideoAttemptPhase.VALIDATE
                or state.execution_binding is None
                or state.fetch_receipt is None and state.local_fetch_receipt is None
                or state.candidate_video_asset_ids
                or state.candidate_continuity_asset_ids
            ):
                raise _state_invalid("Quality rejection requires a running fetched validate attempt.")
            if not state.generation_experiences or (
                state.generation_experiences[-1].content_hash != experience_content_hash
            ):
                raise _state_invalid("Quality rejection requires the latest durable experience receipt.")
            request = self._reopen_video_request(state.request)
            binding = self._reopen_generation_execution_binding(state.execution_binding)
            experiences = self.read_generation_experiences()
            history = tuple(item for stored in experiences for item in stored.evidence)
            sources = tuple(source for stored in experiences for source in stored.evaluation_sources)
            try:
                binding.validate_request(request)
            except ValueError as exc:
                raise _state_invalid("Quality rejection execution binding is not exact.", str(exc)) from exc
            experience = self._reopen_generation_experience(state.generation_experiences[-1])
            evidence = experience.evidence[-1]
            pointer = state.local_fetch_receipt or state.fetch_receipt
            assert pointer is not None
            fetch = (
                self._reopen_local_video_fetch(pointer)
                if state.local_fetch_receipt is not None
                else self._reopen_video_fetch(pointer)
            )
            loaded = load_production_project(self._project_root / "project.yaml")
            if loaded.qa_policy is None or loaded.manifest.active_qa_policy is None:
                raise _state_invalid("Quality rejection requires a selected QA policy.")
            from ai_video.production.production_strategy_reader import (
                selected_shot_generation_acceptance,
            )

            if (
                selected_shot_generation_acceptance(loaded, evidence.shot_id)
                != loaded.qa_policy.selected_generation_acceptance()
            ):
                raise _state_invalid(
                    "Quality rejection does not support component QA authority."
                )
            try:
                diagnosis = validate_quality_rejection_experience(
                    binding=binding,
                    experience=experience,
                    evidence=evidence,
                    request=request,
                    attempt_id=attempt_id,
                    artifact_sha256=fetch.artifact_sha256,
                    qa_policy=loaded.qa_policy,
                    history=history,
                    evaluation_sources=sources,
                )
            except (AttributeError, ValueError) as exc:
                raise _state_invalid("Quality rejection evidence is invalid.", str(exc)) from exc
            if reason is not None and diagnosis.failure_classes != ("EVIDENCE_GAP", "QUALITY_FAILURE"):
                raise _state_invalid("Abandonment requires a known quality failure with unresolved evidence.")
            if reason is None and diagnosis.failure_classes != ("QUALITY_FAILURE",):
                raise _state_invalid("Quality rejection requires a complete known quality failure.")
            try:
                unresolved = unresolved_generation_requirements(
                    evidence, history, experience.candidate.recipe,
                    evaluation_sources=sources) if reason is not None else ()
            except ValueError as exc:
                raise _state_invalid("Abandonment evidence is invalid.", str(exc)) from exc
            receipt = GenerationQualityRejectionReceipt.create(
                schema_version="generation-quality-rejection/2" if reason is not None else "generation-quality-rejection/1",
                abandonment_reason=reason,
                unresolved_requirements=unresolved,
                attempt_id=attempt_id,
                actor=actor,
                request_fingerprint=request.request_input_hash,
                artifact_sha256=fetch.artifact_sha256,
                artifact_size_bytes=fetch.size_bytes,
                experience_content_hash=experience_content_hash,
                evidence_hash=evidence.evidence_hash,
                qa_policy=loaded.manifest.active_qa_policy,
                expected_manifest_revision=expected_manifest_revision,
                diagnosis=diagnosis,
            )
            artifact = _artifact(
                Path("state/video-generation/rejections") / f"{receipt.content_hash}.json",
                receipt,
            )
            rejection = GenerationQualityRejectionReceiptPointer(
                path=artifact.relative_path,
                content_hash=receipt.content_hash,
                attempt_id=attempt_id,
                request_fingerprint=request.request_input_hash,
                artifact_sha256=fetch.artifact_sha256,
                experience_content_hash=experience_content_hash,
                file_sha256=artifact.file_sha256,
            )
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            next_state = state.model_copy(update={"quality_rejection": rejection})
            next_attempt = _validated_transition(
                attempt,
                {
                    "status": StateCommitStatus.FAILED,
                    "finished_at": _timestamp(),
                    "error_code": ErrorCode.VIDEO_QUALITY_REJECTED.value,
                    "error_message": "Generated video failed explicit quality evaluation.",
                    "video_generation_state": next_state,
                },
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
            self._reopen_generation_quality_rejection(rejection)
            return self._read_manifest()
