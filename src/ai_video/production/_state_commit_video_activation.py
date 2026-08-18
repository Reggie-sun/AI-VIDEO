from __future__ import annotations

from ai_video.production.models import (
    StateCommitStatus,
    VideoAttemptPhase,
)
from ._state_commit_video_candidate import resolve_video_activation_dependency_state

from ._state_commit_common import (
    _dependency_states_hash,
    _state_invalid,
    _timestamp,
    _validated_transition,
)


class _StateCommitVideoActivationMixin:
    def activate_video_candidate(self, *, attempt_id: str):
        """Atomically select one fully persisted P8 candidate tuple."""

        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = self._video_attempt(manifest, attempt_id)
            state = attempt.video_generation_state
            if (
                attempt.status not in {
                    StateCommitStatus.RUNNING,
                    StateCommitStatus.INTERRUPTED,
                }
                or state is None
                or state.phase is not VideoAttemptPhase.CANDIDATE
                or attempt.candidate_project is None
                or attempt.candidate_registry is None
                or attempt.candidate_dependency_graph is None
                or attempt.candidate_dependency_states_hash is None
                or state.candidate_video_asset_ids != (state.request.output_asset_id,)
            ):
                raise _state_invalid("Video activation candidate identity is incomplete.")
            if (
                manifest.active_project != attempt.base_project
                or manifest.active_registry != attempt.base_registry
                or manifest.active_dependency_graph != attempt.base_dependency_graph
            ):
                raise _state_invalid(
                    "Video activation base tuple is no longer current."
                )
            graph = self._reopen_dependency_graph(
                attempt.candidate_dependency_graph
            )
            request = self._reopen_video_request(state.request)
            scope = request.activation_scope
            if scope is None:
                raise _state_invalid("Video activation request has no durable scope.")
            resolution = resolve_video_activation_dependency_state(
                graph=graph,
                base_states=manifest.dependency_states,
                project_pointer=attempt.candidate_project,
                registry_pointer=attempt.candidate_registry,
                target_shot_id=scope.request.target_shot_id,
                output_asset_id=request.output_asset_id,
            )
            if (
                _dependency_states_hash(resolution.states)
                != attempt.candidate_dependency_states_hash
            ):
                raise _state_invalid("Video candidate dependency state hash is invalid.")
            active_state = state.model_copy(
                update={"phase": VideoAttemptPhase.ACTIVATE}
            )
            succeeded_attempt = _validated_transition(
                attempt,
                {
                    "status": StateCommitStatus.SUCCEEDED,
                    "video_generation_state": active_state,
                    "finished_at": _timestamp(),
                    "error_code": None,
                    "error_message": None,
                },
            )
            verification_attempts = tuple(
                succeeded_attempt if item.attempt_id == attempt_id else item
                for item in manifest.attempts
            )
            self._verify_dependency_candidate(
                manifest,
                graph,
                resolution.states,
                project_pointer=attempt.candidate_project,
                registry_pointer=attempt.candidate_registry,
                attempts=verification_attempts,
            )
            final = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "active_project": attempt.candidate_project,
                    "active_registry": attempt.candidate_registry,
                    "active_dependency_graph": attempt.candidate_dependency_graph,
                    "dependency_states": resolution.states,
                    "attempts": verification_attempts,
                },
            )
            self._write_manifest_atomic(final)
            reopened = self._read_manifest()
            if reopened != final:
                raise _state_invalid("Video final Manifest reopen verification failed.")
            selected = self._load_production_project(
                self._project_root / "project.yaml"
            )
            if selected.manifest != final or selected.dependency_graph != graph:
                raise _state_invalid("Video selected bundle is not the exact candidate.")
            return reopened

    def replay_active_video_generation(self, *, attempt_id: str):
        manifest = self._read_manifest()
        attempt = self._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if (
            attempt.status is not StateCommitStatus.SUCCEEDED
            or state is None
            or state.phase is not VideoAttemptPhase.ACTIVATE
            or attempt.candidate_project != manifest.active_project
            or attempt.candidate_registry != manifest.active_registry
            or attempt.candidate_dependency_graph
            != manifest.active_dependency_graph
            or state.candidate_video_asset_ids != (state.request.output_asset_id,)
        ):
            raise _state_invalid("Video generation success is not exact active evidence.")
        self._load_production_project(self._project_root / "project.yaml")
        return manifest
