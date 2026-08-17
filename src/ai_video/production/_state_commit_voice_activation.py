from __future__ import annotations

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import (
    VoiceAssetProvider,
    VoiceCallAuthorization,
    VoiceGenerationRequest,
)
from ai_video.production.models import (
    AssetRegistrySnapshot,
    AssetType,
    DependencyGraphSnapshot,
    DependencyGraphTransition,
    ProductionManifest,
    StateCommitStatus,
)

from ._state_commit_common import (
    _candidate_artifacts_hash,
    _outcome_unknown,
    _state_invalid,
    _state_unsupported,
    _timestamp,
    _validated_transition,
)
from ._state_commit_contracts import (
    CommitPhase,
    StateCommitRequest,
    VoiceDependencyTransitionPreparer,
)


class _StateCommitVoiceActivationMixin:
    def activate_voice_assets(
        self,
        request: StateCommitRequest,
        *,
        audio_asset_ids: tuple[str, ...],
        caption_asset_ids: tuple[str, ...] = (),
    ) -> ProductionManifest:
        """Persist R+3 exact candidates, then atomically select R+4 without transport."""

        if request.operation != "voice_generation" or not audio_asset_ids:
            raise _state_invalid("Voice activation request is incomplete.")
        self._validate_request(request)
        registry_artifact = next(
            (
                item
                for item in request.artifacts
                if item.relative_path == request.next_registry.path
            ),
            None,
        )
        if registry_artifact is None:
            raise _state_invalid("Voice activation registry artifact is missing.")
        try:
            candidate_registry = AssetRegistrySnapshot.model_validate_json(
                registry_artifact.payload
            )
        except (ValidationError, ValueError) as exc:
            raise _state_invalid("Voice activation registry artifact is invalid.", str(exc)) from exc
        by_id = {item.asset_id: item for item in candidate_registry.assets}
        if set(audio_asset_ids).intersection(caption_asset_ids) or any(
            asset_id not in by_id
            or by_id[asset_id].asset_type
            not in {AssetType.VOICE, AssetType.MUSIC, AssetType.SFX}
            for asset_id in audio_asset_ids
        ) or any(
            asset_id not in by_id or by_id[asset_id].asset_type is not AssetType.CAPTION
            for asset_id in caption_asset_ids
        ):
            raise _state_invalid("Voice activation asset IDs do not match the candidate registry.")
        candidate_hash = _candidate_artifacts_hash(request.artifacts)
        final_replaced = False
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = next(
                (item for item in manifest.attempts if item.attempt_id == request.attempt_id),
                None,
            )
            if attempt is None or attempt.operation != "voice_generation":
                raise _state_invalid("Voice activation has no matching attempt.")
            graph_transition: DependencyGraphTransition | None = None
            candidate_graph: DependencyGraphSnapshot | None = None
            if attempt.status is StateCommitStatus.SUCCEEDED:
                transition = request.dependency_graph_transition
                if manifest.schema_version in {"2.3", "2.4", "2.5"}:
                    if transition is None or (
                        attempt.base_dependency_graph != transition.base_dependency_graph
                        or attempt.candidate_dependency_graph
                        != transition.candidate_dependency_graph
                        or attempt.candidate_dependency_states_hash
                        != transition.candidate_dependency_states_hash
                        or manifest.active_dependency_graph
                        != transition.candidate_dependency_graph
                        or manifest.dependency_states
                        != transition.candidate_dependency_states
                    ):
                        raise _state_invalid(
                            "Succeeded voice replay dependency transition does not match active state."
                        )
                    graph_transition = transition
                    active_graph = self._reopen_dependency_graph(
                        transition.candidate_dependency_graph
                    )
                    self._verify_dependency_candidate(
                        manifest, active_graph, manifest.dependency_states
                    )
                elif transition is not None:
                    raise _state_invalid(
                        "Dependency graph transition requires Manifest 2.3."
                    )
            else:
                graph_transition, candidate_graph = self._validate_dependency_transition(
                    manifest,
                    expected_manifest_revision=request.expected_manifest_revision,
                    artifacts=request.artifacts,
                    transition=request.dependency_graph_transition,
                )
            if (
                manifest.schema_version not in {"2.3", "2.4", "2.5"}
                and (
                    attempt.status is StateCommitStatus.SUCCEEDED
                    or attempt.voice_phase == "candidate"
                )
            ):
                durable_request = self._reconstruct_voice_activation_request(attempt)
                if durable_request != request:
                    raise _state_invalid(
                        "Voice activation replay does not match the current durable candidate graph."
                    )
            provider_request_id = self._validate_voice_activation_graph(
                request,
                attempt,
                candidate_registry,
                audio_asset_ids,
                caption_asset_ids,
            )
            if attempt.status is StateCommitStatus.SUCCEEDED:
                if (
                    manifest.active_registry == request.next_registry
                    and attempt.candidate_artifacts_hash == candidate_hash
                    and attempt.candidate_audio_asset_ids == audio_asset_ids
                    and attempt.candidate_caption_asset_ids == caption_asset_ids
                ):
                    return manifest
                raise _state_invalid("Succeeded voice replay does not match active state.")
            candidate_exists = attempt.voice_phase == "candidate"
            if candidate_exists:
                if (
                    attempt.status not in {StateCommitStatus.RUNNING, StateCommitStatus.INTERRUPTED}
                    or attempt.candidate_project not in (None, request.next_project)
                    or attempt.candidate_registry != request.next_registry
                    or attempt.candidate_artifacts_hash != candidate_hash
                    or attempt.candidate_audio_asset_ids != audio_asset_ids
                    or attempt.candidate_caption_asset_ids != caption_asset_ids
                    or (
                        graph_transition is not None
                        and (
                            attempt.base_dependency_graph
                            != graph_transition.base_dependency_graph
                            or attempt.candidate_dependency_graph
                            != graph_transition.candidate_dependency_graph
                            or attempt.candidate_dependency_states_hash
                            != graph_transition.candidate_dependency_states_hash
                        )
                    )
                ):
                    raise _state_invalid("Voice candidate replay identity does not match.")
            else:
                if (
                    attempt.status is not StateCommitStatus.RUNNING
                    or attempt.voice_phase not in {
                        "submit_intent", "provider_call", "materialize", "probe", "align"
                    }
                    or manifest.manifest_revision != request.expected_manifest_revision
                    or manifest.active_project != attempt.base_project
                    or manifest.active_registry != attempt.base_registry
                    or request.next_project != attempt.base_project
                ):
                    raise _state_invalid("Voice activation base state or revision is stale.")
                for artifact in sorted(
                    request.artifacts, key=lambda item: item.relative_path.as_posix()
                ):
                    self._write_immutable_artifact(
                        artifact,
                        attempt_id=request.attempt_id,
                        dependency_graph=(
                            graph_transition is not None
                            and artifact.relative_path
                            == graph_transition.candidate_dependency_graph.path
                        ),
                    )
                self._verify_voice_committed_candidates(request)
                candidate_attempt = _validated_transition(
                    attempt,
                    {
                        "candidate_project": None,
                        "candidate_registry": request.next_registry,
                        "candidate_artifacts_hash": candidate_hash,
                        "candidate_audio_asset_ids": audio_asset_ids,
                        "candidate_caption_asset_ids": caption_asset_ids,
                        "provider_request_id": provider_request_id,
                        "voice_phase": "candidate",
                        "base_dependency_graph": (
                            None
                            if graph_transition is None
                            else graph_transition.base_dependency_graph
                        ),
                        "candidate_dependency_graph": (
                            None
                            if graph_transition is None
                            else graph_transition.candidate_dependency_graph
                        ),
                        "candidate_dependency_states_hash": (
                            None
                            if graph_transition is None
                            else graph_transition.candidate_dependency_states_hash
                        ),
                    },
                )
                if graph_transition is not None and candidate_graph is not None:
                    verification_attempt = _validated_transition(
                        candidate_attempt,
                        {
                            "status": StateCommitStatus.SUCCEEDED,
                            "voice_phase": "activate",
                            "finished_at": _timestamp(),
                            "error_code": None,
                            "error_message": None,
                        },
                    )
                    verification_attempts = tuple(
                        verification_attempt
                        if item.attempt_id == request.attempt_id
                        else item
                        for item in manifest.attempts
                    )
                    self._verify_dependency_candidate(
                        manifest,
                        candidate_graph,
                        graph_transition.candidate_dependency_states,
                        project_pointer=request.next_project,
                        registry_pointer=request.next_registry,
                        attempts=verification_attempts,
                    )
                candidate_manifest = _validated_transition(
                    manifest,
                    {
                        "manifest_revision": manifest.manifest_revision + 1,
                        "attempts": tuple(
                            candidate_attempt
                            if item.attempt_id == request.attempt_id
                            else item
                            for item in manifest.attempts
                        ),
                    },
                )
                self._write_manifest_atomic(candidate_manifest)
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_VOICE_CANDIDATE_MANIFEST
                )
                manifest = self._read_manifest()
                attempt = next(
                    item for item in manifest.attempts if item.attempt_id == request.attempt_id
                )
            succeeded = _validated_transition(
                attempt,
                {
                    "status": StateCommitStatus.SUCCEEDED,
                    "voice_phase": "activate",
                    "finished_at": _timestamp(),
                    "error_code": None,
                    "error_message": None,
                },
            )
            final_update: dict[str, object] = {
                "manifest_revision": manifest.manifest_revision + 1,
                "active_project": request.next_project,
                "active_registry": request.next_registry,
                "active_render_state": (
                    manifest.active_render_state
                    if manifest.schema_version in {"2.3", "2.4", "2.5"}
                    else None
                ),
                "attempts": tuple(
                    succeeded if item.attempt_id == request.attempt_id else item
                    for item in manifest.attempts
                ),
            }
            if graph_transition is not None:
                final_update.update(
                    {
                        "active_dependency_graph": graph_transition.candidate_dependency_graph,
                        "dependency_states": graph_transition.candidate_dependency_states,
                    }
                )
            final = _validated_transition(
                manifest,
                final_update,
            )

            def mark_replaced() -> None:
                nonlocal final_replaced
                final_replaced = True
                if graph_transition is not None:
                    self._crash_injector.checkpoint(
                        CommitPhase.AFTER_GRAPH_FINAL_MANIFEST_REPLACE
                    )

            try:
                self._write_manifest_atomic(final, on_replace=mark_replaced)
                self._crash_injector.checkpoint(
                    CommitPhase.AFTER_VOICE_FINAL_MANIFEST_REPLACE
                )
                return self._read_manifest()
            except Exception as exc:
                if final_replaced:
                    raise _outcome_unknown(exc) from exc
                raise

    def generate_voice_asset(
        self,
        request: VoiceGenerationRequest,
        provider: VoiceAssetProvider,
        authorization: VoiceCallAuthorization,
        *,
        dependency_transition_preparer: VoiceDependencyTransitionPreparer | None = None,
    ) -> ProductionManifest:
        """Only public path allowed to invoke one voice provider transport call."""

        preflight_manifest = self._read_manifest()
        if (
            preflight_manifest.schema_version in {"2.3", "2.4", "2.5"}
            and dependency_transition_preparer is None
        ):
            raise _state_invalid(
                "Manifest 2.3 voice generation requires a dependency transition preparer."
            )

        preview = provider.preview(request)
        self.begin_voice_generation(
            request,
            preview,
            authorization,
            dependency_transition_preparer_available=(
                dependency_transition_preparer is not None
            ),
        )
        permit = self.record_voice_submit_intent(request, preview, authorization)
        try:
            result = provider.generate(request, authorization, permit)
        except AiVideoError as exc:
            if exc.code is ErrorCode.VOICE_PROVIDER_FAILED:
                self.record_voice_failure(
                    request.attempt_id,
                    phase="provider_call",
                    error_code=exc.code.value,
                    error_message=exc.user_message,
                )
            else:
                self.record_voice_outcome_unknown(
                    request.attempt_id,
                    phase="provider_call",
                    error_code=exc.code.value,
                    error_message=exc.user_message,
                )
            raise

        except Exception as exc:
            self.record_voice_outcome_unknown(
                request.attempt_id,
                phase="provider_call",
                error_message=f"Voice transport failed after submit intent: {exc}",
            )
            raise
        self._crash_injector.checkpoint(CommitPhase.AFTER_VOICE_PROVIDER_RESULT)
        try:
            self._validate_voice_provider_result(request, preview, authorization, result)
        except Exception as exc:
            self.record_voice_outcome_unknown(
                request.attempt_id,
                phase="provider_call",
                error_message=f"Voice provider returned contradictory durable evidence: {exc}",
            )
            raise
        if self._voice_candidate_preparer is None:
            self.record_voice_outcome_unknown(
                request.attempt_id,
                phase="materialize",
                error_message="Voice result is durable only in process; candidate preparation is unavailable.",
            )
            raise _state_unsupported(
                "Voice candidate preparation requires an injected local deterministic materializer."
            )
        try:
            prepared = self._voice_candidate_preparer(
                request,
                preview,
                authorization,
                result,
                self.voice_attempt_paths(request.attempt_id),
            )
            commit_request, audio_ids, caption_ids = self._prepare_voice_activation_request(
                request, preview, authorization, result, prepared
            )
            if preflight_manifest.schema_version in {"2.3", "2.4", "2.5"}:
                assert dependency_transition_preparer is not None
                prepared_request = dependency_transition_preparer(commit_request)
                if (
                    not isinstance(prepared_request, StateCommitRequest)
                    or prepared_request.attempt_id != commit_request.attempt_id
                    or prepared_request.operation != commit_request.operation
                    or prepared_request.expected_manifest_revision
                    != commit_request.expected_manifest_revision
                    or prepared_request.next_project != commit_request.next_project
                    or prepared_request.next_registry != commit_request.next_registry
                    or prepared_request.dependency_graph_transition is None
                    or not set(commit_request.artifacts).issubset(
                        prepared_request.artifacts
                    )
                ):
                    raise _state_invalid(
                        "Voice dependency transition preparer changed the owned candidate."
                    )
                commit_request = prepared_request
            return self.activate_voice_assets(
                commit_request,
                audio_asset_ids=audio_ids,
                caption_asset_ids=caption_ids,
            )
        except Exception as exc:
            current = self._read_manifest()
            active_attempt = next(
                item for item in current.attempts if item.attempt_id == request.attempt_id
            )
            if active_attempt.status is StateCommitStatus.RUNNING:
                self.record_voice_outcome_unknown(
                    request.attempt_id,
                    phase="materialize",
                    error_message=f"Voice result could not be durably activated: {exc}",
                )
            raise
