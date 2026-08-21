from __future__ import annotations

from ai_video.errors import ErrorCode
from ai_video.production.models import (
    ProductionManifest,
    RecoveryDisposition,
    RecoveryItem,
    StateCommitAttempt,
    StateCommitStatus,
    VideoAttemptPhase,
)

from ._state_commit_common import (
    _dependency_states_hash,
    _state_invalid,
    _timestamp,
    _validated_transition,
)
from ._state_commit_video_candidate import resolve_video_activation_dependency_state


class _StateCommitVideoRecoveryMixin:
    """Preserve post-fetch P8 evidence without selecting an inactive candidate."""

    def _recover_attempts(
        self, manifest: ProductionManifest
    ) -> tuple[list[StateCommitAttempt], bool, list[RecoveryItem]]:
        protected_validate: dict[str, StateCommitAttempt] = {}
        candidate_items: list[RecoveryItem] = []
        candidate_changed = False
        preprocessed: list[StateCommitAttempt] = []

        for attempt in manifest.attempts:
            state = attempt.video_generation_state
            if (
                attempt.operation != "video_generation"
                or attempt.status
                not in {StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN}
                or state is None
                or state.phase
                not in {VideoAttemptPhase.VALIDATE, VideoAttemptPhase.CANDIDATE}
            ):
                preprocessed.append(attempt)
                continue

            if state.phase is VideoAttemptPhase.VALIDATE:
                fetch_pointer = state.local_fetch_receipt or state.fetch_receipt
                if fetch_pointer is None:
                    raise _state_invalid(
                        "Recoverable video validation has no fetch receipt."
                    )
                if state.local_fetch_receipt is not None:
                    self._reopen_local_video_fetch(state.local_fetch_receipt)
                else:
                    self._reopen_video_fetch(state.fetch_receipt)
                if state.terminal_frame_extraction is not None:
                    self._reopen_terminal_frame_extraction(
                        state.terminal_frame_extraction
                    )
                if state.continuity_evaluation is not None:
                    continuity_intent = self._reopen_continuity_evaluation_intent(
                        state.continuity_evaluation.intent
                    )
                    if state.continuity_evaluation.evidence is not None:
                        continuity_evidence = (
                            self._reopen_generated_shot_continuity_evidence(
                                state.continuity_evaluation.evidence
                            )
                        )
                        if (
                            continuity_evidence.evaluation_fingerprint
                            != continuity_intent.evaluation_fingerprint
                        ):
                            raise _state_invalid(
                                "Recoverable continuity evidence does not match its intent."
                            )
                protected_validate[attempt.attempt_id] = attempt
                # The generic recovery owner must not reinterpret a safely
                # persisted post-fetch phase.  Restore this exact attempt below.
                preprocessed.append(
                    attempt.model_copy(update={"status": StateCommitStatus.INTERRUPTED})
                )
                candidate_items.append(
                    RecoveryItem(
                        path=fetch_pointer.path,
                        disposition=RecoveryDisposition.ACTIVE,
                        sha256=fetch_pointer.file_sha256,
                    )
                )
                continue

            if (
                attempt.candidate_project is None
                or attempt.candidate_registry is None
                or attempt.candidate_dependency_graph is None
                or attempt.candidate_dependency_states_hash is None
                or state.candidate_video_asset_ids != (state.request.output_asset_id,)
                or manifest.active_project != attempt.base_project
                or manifest.active_registry != attempt.base_registry
                or manifest.active_dependency_graph != attempt.base_dependency_graph
            ):
                raise _state_invalid(
                    "Interrupted video activation candidate identity is incomplete."
                )
            graph = self._reopen_dependency_graph(attempt.candidate_dependency_graph)
            request = self._reopen_video_request(state.request)
            scope = request.activation_scope
            if scope is None:
                raise _state_invalid(
                    "Interrupted video candidate request has no durable scope."
                )
            expected_continuity_ids = (
                (f"{request.output_asset_id}:terminal-frame",)
                if scope.request.seal_terminal_frame
                else ()
            )
            if state.candidate_continuity_asset_ids != expected_continuity_ids or (
                (state.terminal_frame_evidence is None)
                != (not scope.request.seal_terminal_frame)
            ):
                raise _state_invalid(
                    "Interrupted video continuity candidate identity is incomplete."
                )
            self._reopen_terminal_frame_chain(
                state, request, source_registry=attempt.candidate_registry
            )
            resolution = resolve_video_activation_dependency_state(
                graph=graph,
                base_states=manifest.dependency_states,
                project_pointer=attempt.candidate_project,
                registry_pointer=attempt.candidate_registry,
                target_shot_id=scope.request.target_shot_id,
                output_asset_id=request.output_asset_id,
                continuity_asset_id=(
                    expected_continuity_ids[0]
                    if expected_continuity_ids
                    else None
                ),
            )
            if (
                _dependency_states_hash(resolution.states)
                != attempt.candidate_dependency_states_hash
            ):
                raise _state_invalid(
                    "Interrupted video candidate dependency state hash is invalid."
                )
            verification_attempt = _validated_transition(
                attempt,
                {
                    "status": StateCommitStatus.SUCCEEDED,
                    "video_generation_state": state.model_copy(
                        update={"phase": VideoAttemptPhase.ACTIVATE}
                    ),
                    "finished_at": _timestamp(),
                    "error_code": None,
                    "error_message": None,
                },
            )
            self._verify_dependency_candidate(
                manifest,
                graph,
                resolution.states,
                project_pointer=attempt.candidate_project,
                registry_pointer=attempt.candidate_registry,
                attempts=tuple(
                    verification_attempt
                    if item.attempt_id == attempt.attempt_id
                    else item
                    for item in manifest.attempts
                ),
            )
            replacement = _validated_transition(
                attempt,
                {
                    "status": StateCommitStatus.INTERRUPTED,
                    "finished_at": _timestamp(),
                    "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                    "error_message": (
                        "Video candidate is durable but was not activated; explicit "
                        "activation remains required."
                    ),
                },
            )
            preprocessed.append(replacement)
            candidate_items.append(
                RecoveryItem(
                    path=attempt.candidate_dependency_graph.path,
                    disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                    sha256=attempt.candidate_dependency_graph.file_sha256,
                )
            )
            candidate_changed = True

        delegated_manifest = manifest.model_copy(
            update={"attempts": tuple(preprocessed)}
        )
        repaired, changed, items = super()._recover_attempts(delegated_manifest)
        repaired = [
            protected_validate.get(attempt.attempt_id, attempt)
            for attempt in repaired
        ]
        return repaired, changed or candidate_changed, [*items, *candidate_items]
