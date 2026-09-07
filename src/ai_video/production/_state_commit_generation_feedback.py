"""Durable evaluator feedback for decision-bound video attempts."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ai_video.production._lifecycle_schema import GenerationExperienceReceiptPointer
from ai_video.production._state_commit_common import (
    _canonical_json_bytes,
    _state_invalid,
    _validated_transition,
)
from ai_video.production.generation_diagnosis import AttemptEvidence
from ai_video.production.generation_experience import GenerationExperience
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StateCommitStatus

from ._state_commit_contracts import PreparedArtifact


def _artifact(path: Path, model: object) -> PreparedArtifact:
    payload = _canonical_json_bytes(model)  # type: ignore[arg-type]
    return PreparedArtifact(
        relative_path=path,
        payload=payload,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )


def _experience_hash(experience: GenerationExperience) -> str:
    return canonical_sha256(experience.model_dump(mode="json"))


class _StateCommitGenerationFeedbackMixin:
    def _reopen_generation_experience(self, pointer):
        from ai_video.production._video_project_reader import (
            load_generation_experience,
        )

        return load_generation_experience(self._project_root, pointer)

    def record_generation_experience(
        self, *, attempt_id: str, experience: GenerationExperience, analysis_proof=None
    ):
        """Persist only evaluation evidence for the exact finished attempt."""

        try:
            from ai_video.production.generation_decision import GenerationCandidate
            from ai_video.production.generation_experience import (
                bind_experience_models,
            )

            bind_experience_models(GenerationCandidate)
            experience = GenerationExperience.model_validate(
                experience.model_dump(mode="python")
            )
        except (AttributeError, ValueError) as exc:
            raise _state_invalid("Generation experience is invalid.", str(exc)) from exc
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._video_attempt(manifest, attempt_id)
            state = attempt.video_generation_state
            if state is None or state.execution_binding is None:
                raise _state_invalid(
                    "Generation experience requires a persisted production decision binding."
                )
            request = self._reopen_video_request(state.request)
            binding = self._reopen_generation_execution_binding(state.execution_binding)
            selected_id = binding.decision.selected_candidate_id
            candidate = next(
                (
                    item
                    for item in binding.inputs.candidates
                    if item.candidate_id == selected_id
                ),
                None,
            )
            if (
                candidate is None
                or experience.projection != binding.projection
                or experience.candidate != candidate
            ):
                raise _state_invalid(
                    "Generation experience does not match the persisted decision."
                )
            for evidence in experience.evidence:
                self._validate_generation_evidence(
                    attempt=attempt,
                    state=state,
                    request=request,
                    binding=binding,
                    evidence=evidence,
                )
                if evidence.outcome == "media":
                    from ai_video.production.generation_evaluation import validate_generation_evaluation_sources
                    from ai_video.production.project import load_production_project

                    loaded = load_production_project(self._project_root / "project.yaml")
                    try:
                        validate_generation_evaluation_sources(
                            sources=experience.evaluation_sources, evidence=evidence,
                            qa_policy=loaded.qa_policy, loaded=loaded)
                    except (AttributeError, ValueError) as exc:
                        raise _state_invalid("Generation evaluation source is invalid.", str(exc)) from exc
            content_hash = _experience_hash(experience)
            artifact = _artifact(
                Path("state/video-generation/experience") / f"{content_hash}.json",
                experience,
            )
            pointer = GenerationExperienceReceiptPointer(
                path=artifact.relative_path,
                content_hash=content_hash,
                request_fingerprint=request.request_input_hash,
                file_sha256=artifact.file_sha256,
            )
            if pointer in state.generation_experiences:
                return manifest
            if any(s.analysis_evidence is not None for s in experience.evaluation_sources):
                from ai_video.production.generation_evaluation import _AnalysisRecordingProof
                if (type(analysis_proof) is not _AnalysisRecordingProof
                        or not analysis_proof.consume(attempt_id=attempt_id, sources=experience.evaluation_sources)):
                    raise _state_invalid("MCP analysis evidence requires a fresh exact bridge recording proof.")
            self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            next_state = state.model_copy(
                update={
                    "generation_experiences": (
                        *state.generation_experiences,
                        pointer,
                    )
                }
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
            self._reopen_generation_experience(pointer)
            return self._read_manifest()

    def _validate_generation_evidence(
        self, *, attempt, state, request, binding, evidence: AttemptEvidence
    ) -> None:
        if (
            evidence.attempt_id != attempt.attempt_id
            or evidence.request_hash != request.request_input_hash
            or evidence.task_id != binding.inputs.limits.task_id
            or evidence.shot_id != binding.context.target_shot_id
        ):
            raise _state_invalid("Generation evidence does not match the durable attempt.")
        intervention = binding.decision.intervention
        if intervention is None:
            if (
                evidence.intervention_id is not None
                or evidence.intervention_semantic_hash is not None
                or evidence.actual_delta
            ):
                raise _state_invalid("Generation evidence invents an unselected intervention.")
        elif (
            evidence.intervention_id != intervention.intervention_id
            or evidence.intervention_semantic_hash != intervention.semantic_hash
            or set(evidence.actual_delta) != set(intervention.changed_variables)
        ):
            raise _state_invalid("Generation evidence does not match the selected intervention.")
        if evidence.outcome == "media":
            pointer = state.local_fetch_receipt or state.fetch_receipt
            if pointer is None or evidence.artifact_sha256 is None:
                raise _state_invalid("Media evidence requires exact fetched video bytes.")
            receipt = (
                self._reopen_local_video_fetch(pointer)
                if state.local_fetch_receipt is not None
                else self._reopen_video_fetch(pointer)
            )
            if receipt.artifact_sha256 != evidence.artifact_sha256:
                raise _state_invalid("Generation evidence artifact does not match fetched bytes.")
        elif evidence.outcome == "runtime_failure":
            if attempt.status is not StateCommitStatus.FAILED:
                raise _state_invalid("Runtime failure evidence requires a durable failed attempt.")
        elif evidence.outcome == "unknown_outcome":
            if attempt.status is not StateCommitStatus.OUTCOME_UNKNOWN:
                raise _state_invalid("Unknown outcome evidence requires a durable unknown attempt.")
        elif evidence.outcome == "not_submitted":
            if state.phase.value != "request":
                raise _state_invalid("Not-submitted evidence requires a request-phase attempt.")
        else:  # Defensive even though AttemptEvidence is a closed schema.
            raise _state_invalid("Generation evidence outcome is unsupported.")

    def read_generation_experiences(self) -> tuple[GenerationExperience, ...]:
        manifest = self._read_manifest()
        from ai_video.production._generation_feedback_reader import load_imported_history

        imported = load_imported_history(self._project_root, manifest)
        receipts = tuple(
            pointer
            for attempt in manifest.attempts
            if attempt.video_generation_state is not None
            for pointer in attempt.video_generation_state.generation_experiences
        )
        return (*tuple(item.experience for item in imported),
                *tuple(self._reopen_generation_experience(pointer) for pointer in receipts))
