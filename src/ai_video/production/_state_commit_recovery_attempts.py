from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    AssetRegistrySnapshot,
    DependencyGraphSnapshotPointer,
    ProductionManifest,
    RecoveryDisposition,
    RecoveryItem,
    RenderStateSnapshot,
    RenderStateSnapshotPointer,
    ReviewAttemptPhase,
    StateCommitAttempt,
    StateCommitStatus,
    VideoAttemptPhase,
)
from ai_video.production.paths import _read_regular_file_nofollow

from ._state_commit_common import (
    _candidate_artifacts_hash,
    _dependency_states_hash,
    _state_invalid,
    _timestamp,
    _validated_transition,
)
from ._state_commit_contracts import PreparedArtifact, StateCommitRequest


class _StateCommitRecoveryAttemptsMixin:
    def _recover_attempts(
        self, manifest: ProductionManifest
    ) -> tuple[list[StateCommitAttempt], bool, list[RecoveryItem]]:
        repaired: list[StateCommitAttempt] = []
        items: list[RecoveryItem] = []
        changed = False
        for attempt in manifest.attempts:
            if attempt.status not in {
                StateCommitStatus.RUNNING,
                StateCommitStatus.OUTCOME_UNKNOWN,
            }:
                repaired.append(attempt)
                continue
            if (
                attempt.paid_provider_state is not None
                and attempt.paid_provider_state.phase.value == "outcome_unknown"
            ):
                repaired.append(attempt)
                continue
            if attempt.operation == "image_generation":
                replacement, image_items = self._recover_image_attempt(
                    manifest, attempt
                )
                repaired.append(replacement)
                items.extend(image_items)
                changed = changed or replacement != attempt
                continue
            if attempt.operation == "video_generation":
                state = attempt.video_generation_state
                if state is None:
                    raise _state_invalid(
                        "Interrupted video generation attempt has no state."
                    )
                if state.phase is VideoAttemptPhase.REQUEST:
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.INTERRUPTED,
                            "finished_at": _timestamp(),
                            "error_code": (
                                ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value
                            ),
                            "error_message": (
                                "Video generation was interrupted before durable "
                                "Paid Provider submit intent."
                            ),
                        },
                    )
                    repaired.append(replacement)
                    items.append(
                        RecoveryItem(
                            path=state.request.path,
                            disposition=(
                                RecoveryDisposition.INTERRUPTED_RECORDED
                            ),
                            sha256=state.request.file_sha256,
                        )
                    )
                    changed = True
                    continue
                paid_state = attempt.paid_provider_state
                if (
                    paid_state is not None
                    and paid_state.phase.value in {"accepted", "settled"}
                    and state.phase
                    in {
                        VideoAttemptPhase.SUBMITTED,
                        VideoAttemptPhase.POLLING,
                        VideoAttemptPhase.FETCH,
                    }
                ):
                    repaired.append(attempt)
                    continue
                raise _state_invalid(
                    "Interrupted video generation lifecycle is inconsistent."
                )
            if attempt.operation == "review":
                if attempt.review_request is None:
                    raise _state_invalid("Interrupted review attempt has no request.")
                if attempt.status is StateCommitStatus.RUNNING:
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.OUTCOME_UNKNOWN,
                            "review_phase": ReviewAttemptPhase.EVIDENCE,
                            "finished_at": _timestamp(),
                            "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                            "error_message": "Review evidence outcome is unknown; do not rerun analysis blindly.",
                        },
                    )
                    repaired.append(replacement)
                    items.append(
                        RecoveryItem(
                            path=attempt.review_request.path,
                            disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                            sha256=attempt.review_request.file_sha256,
                        )
                    )
                    changed = True
                else:
                    repaired.append(attempt)
                continue
            if attempt.operation == "bootstrap_dependency_graph":
                if (
                    attempt.base_dependency_graph is None
                    and manifest.schema_version
                    in {"2.3", "2.4", "2.5", "2.6", "2.7"}
                    and manifest.active_dependency_graph is not None
                    and manifest.active_dependency_graph
                    != attempt.candidate_dependency_graph
                ):
                    raise _state_invalid(
                        "Interrupted dependency bootstrap has a mixed active graph."
                    )
                if (
                    attempt.candidate_dependency_graph is None
                    or attempt.candidate_dependency_states_hash is None
                    or attempt.base_project != manifest.active_project
                    or attempt.base_registry != manifest.active_registry
                ):
                    raise _state_invalid(
                        "Interrupted dependency bootstrap identity is incomplete."
                    )
                active_graph = manifest.active_dependency_graph
                candidate = attempt.candidate_dependency_graph
                expected_artifacts_hash = _candidate_artifacts_hash(
                    (
                        PreparedArtifact(
                            candidate.path,
                            b"",
                            candidate.file_sha256,
                        ),
                    )
                )
                if expected_artifacts_hash != attempt.candidate_artifacts_hash:
                    raise _state_invalid(
                        "Interrupted dependency graph artifact hash is invalid."
                    )
                if active_graph == candidate:
                    graph = self._reopen_dependency_graph(candidate)
                    if (
                        _dependency_states_hash(manifest.dependency_states)
                        != attempt.candidate_dependency_states_hash
                    ):
                        raise _state_invalid(
                            "Activated dependency bootstrap state hash is invalid."
                        )
                    self._verify_dependency_candidate(
                        manifest, graph, manifest.dependency_states
                    )
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.SUCCEEDED,
                            "finished_at": _timestamp(),
                            "error_code": None,
                            "error_message": None,
                        },
                    )
                elif active_graph == attempt.base_dependency_graph:
                    try:
                        graph = self._reopen_dependency_graph(candidate)
                    except AiVideoError:
                        if (
                            self._dependency_graph_candidate_is_absent(attempt)
                            and (
                                self._has_owned_dependency_graph_temp(attempt)
                                or attempt.operation
                                == "bootstrap_dependency_graph"
                            )
                        ):
                            graph = None
                        else:
                            raise
                    if graph is not None:
                        items.append(
                            RecoveryItem(
                                path=candidate.path,
                                disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                                sha256=candidate.file_sha256,
                            )
                        )
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.INTERRUPTED,
                            "finished_at": _timestamp(),
                            "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                            "error_message": (
                                "Dependency graph bootstrap was interrupted before activation."
                            ),
                        },
                    )
                else:
                    raise _state_invalid(
                        "Production Manifest selects a mixed interrupted dependency graph."
                    )
                repaired.append(replacement)
                changed = True
                continue
            if attempt.operation == "voice_generation":
                dependency_outcome = self._recovery_dependency_outcome(
                    manifest, attempt
                )
                active_pair = (manifest.active_project, manifest.active_registry)
                base_pair = (attempt.base_project, attempt.base_registry)
                if attempt.voice_phase == "candidate":
                    if attempt.candidate_registry is None:
                        raise _state_invalid("Voice candidate recovery identity is incomplete.")
                    candidate_project = attempt.candidate_project or attempt.base_project
                    self._validate_recovery_project_pointer(candidate_project)
                    self._validate_recovery_registry_pointer(attempt.candidate_registry)
                    replay = self._reconstruct_voice_activation_request(attempt)
                    replay_registry_artifact = next(
                        item
                        for item in replay.artifacts
                        if item.relative_path == replay.next_registry.path
                    )
                    replay_registry = AssetRegistrySnapshot.model_validate_json(
                        replay_registry_artifact.payload
                    )
                    self._validate_voice_activation_graph(
                        replay,
                        attempt,
                        replay_registry,
                        attempt.candidate_audio_asset_ids,
                        attempt.candidate_caption_asset_ids,
                    )
                    if attempt.candidate_artifacts_hash not in (
                        self._candidate_hash_with_optional_graph(
                            replay.artifacts, attempt
                        )
                    ):
                        raise _state_invalid("Voice recovery candidate graph hash is invalid.")
                    candidate_pair = (
                        candidate_project,
                        attempt.candidate_registry,
                    )
                    if active_pair == candidate_pair:
                        if dependency_outcome not in {"legacy", "candidate"}:
                            raise _state_invalid(
                                "Voice recovery selects a mixed candidate graph."
                            )
                        replacement = _validated_transition(
                            attempt,
                            {
                                "status": StateCommitStatus.SUCCEEDED,
                                "voice_phase": "activate",
                                "finished_at": _timestamp(),
                                "error_code": None,
                                "error_message": None,
                            },
                        )
                    elif active_pair == base_pair:
                        if dependency_outcome not in {"legacy", "base"}:
                            raise _state_invalid(
                                "Voice recovery selects a mixed base graph."
                            )
                        replacement = _validated_transition(
                            attempt,
                            {
                                "status": StateCommitStatus.INTERRUPTED,
                                "finished_at": _timestamp(),
                                "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                                "error_message": "Voice candidate is durable but explicit activation is required.",
                            },
                        )
                        items.append(
                            RecoveryItem(
                                path=attempt.candidate_registry.path,
                                disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                            )
                        )
                        dependency_item = self._interrupted_dependency_graph_item(
                            manifest, attempt
                        )
                        if dependency_item is not None:
                            items.append(dependency_item)
                    else:
                        raise _state_invalid(
                            "Production Manifest selects a mixed interrupted voice pair."
                        )
                elif attempt.status is StateCommitStatus.OUTCOME_UNKNOWN:
                    repaired.append(attempt)
                    continue
                elif attempt.voice_phase == "request":
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.INTERRUPTED,
                            "finished_at": _timestamp(),
                            "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                            "error_message": "Voice attempt was interrupted before durable submit intent.",
                        },
                    )
                else:
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.OUTCOME_UNKNOWN,
                            "finished_at": _timestamp(),
                            "error_code": ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN.value,
                            "error_message": "Voice submit outcome is unknown; blind retry is forbidden.",
                        },
                    )
                repaired.append(replacement)
                changed = True
                continue
            if attempt.operation == "render_state":
                dependency_outcome = self._recovery_dependency_outcome(
                    manifest, attempt
                )
                active_pair = (manifest.active_project, manifest.active_registry)
                base_pair = (attempt.base_project, attempt.base_registry)
                if active_pair != base_pair:
                    raise _state_invalid(
                        "Production Manifest selects a mixed interrupted render pair."
                    )
                if attempt.candidate_render_state is None:
                    if (
                        attempt.candidate_project is not None
                        or attempt.candidate_registry is not None
                        or manifest.active_render_state != attempt.base_render_state
                    ):
                        raise _state_invalid(
                            "Interrupted render attempt has a mixed begun identity."
                        )
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.INTERRUPTED,
                            "finished_at": _timestamp(),
                            "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                            "error_message": "Render state attempt was interrupted before authoritative candidate preparation.",
                        },
                    )
                else:
                    if (
                        attempt.candidate_project != attempt.base_project
                        or attempt.candidate_registry != attempt.base_registry
                    ):
                        raise _state_invalid(
                            "Interrupted render candidate changed project or registry."
                        )
                    state = self._load_verified_render_state(
                        self._project_root,
                        attempt.candidate_render_state,
                        project=attempt.base_project,
                        registry=attempt.base_registry,
                    )
                    render_hashes = {
                        self._render_state_artifacts_hash(
                            state, attempt.candidate_render_state
                        )
                    }
                    if attempt.candidate_dependency_graph is not None:
                        render_hashes.add(
                            self._render_state_artifacts_hash(
                                state,
                                attempt.candidate_render_state,
                                graph=attempt.candidate_dependency_graph,
                            )
                        )
                    if attempt.candidate_artifacts_hash not in render_hashes:
                        raise _state_invalid(
                            "Interrupted render candidate artifact hash is invalid."
                        )
                    if manifest.active_render_state == attempt.candidate_render_state:
                        if dependency_outcome not in {"legacy", "candidate"}:
                            raise _state_invalid(
                                "Render recovery selects a mixed candidate graph."
                            )
                        replacement = _validated_transition(
                            attempt,
                            {
                                "status": StateCommitStatus.SUCCEEDED,
                                "finished_at": _timestamp(),
                                "error_code": None,
                                "error_message": None,
                            },
                        )
                    elif manifest.active_render_state == attempt.base_render_state:
                        if dependency_outcome not in {"legacy", "base"}:
                            raise _state_invalid(
                                "Render recovery selects a mixed base graph."
                            )
                        replacement = _validated_transition(
                            attempt,
                            {
                                "status": StateCommitStatus.INTERRUPTED,
                                "finished_at": _timestamp(),
                                "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                                "error_message": "Render state attempt was interrupted before selecting its candidate state.",
                            },
                        )
                        items.append(
                            RecoveryItem(
                                path=attempt.candidate_render_state.path,
                                disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                            )
                        )
                        dependency_item = self._interrupted_dependency_graph_item(
                            manifest, attempt
                        )
                        if dependency_item is not None:
                            items.append(dependency_item)
                    else:
                        raise _state_invalid(
                            "Production Manifest selects a mixed interrupted render state."
                        )
                repaired.append(replacement)
                changed = True
                continue
            if attempt.operation == "audio_import":
                dependency_outcome = self._recovery_dependency_outcome(
                    manifest, attempt
                )
                if (
                    attempt.candidate_project is not None
                    or attempt.candidate_registry is None
                ):
                    raise _state_invalid("Interrupted audio import identity is incomplete.")
                self._validate_recovery_project_pointer(attempt.base_project)
                self._validate_recovery_registry_pointer(attempt.base_registry)
                self._validate_recovery_registry_pointer(attempt.candidate_registry)
                active_pair = (manifest.active_project, manifest.active_registry)
                base_pair = (attempt.base_project, attempt.base_registry)
                candidate_pair = (attempt.base_project, attempt.candidate_registry)
                if active_pair == candidate_pair:
                    if dependency_outcome not in {"legacy", "candidate"}:
                        raise _state_invalid(
                            "Audio recovery selects a mixed candidate graph."
                        )
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.SUCCEEDED,
                            "finished_at": _timestamp(),
                            "error_code": None,
                            "error_message": None,
                        },
                    )
                elif active_pair == base_pair:
                    if dependency_outcome not in {"legacy", "base"}:
                        raise _state_invalid(
                            "Audio recovery selects a mixed base graph."
                        )
                    replacement = _validated_transition(
                        attempt,
                        {
                            "status": StateCommitStatus.INTERRUPTED,
                            "finished_at": _timestamp(),
                            "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                            "error_message": "Audio import was interrupted before registry activation.",
                        },
                    )
                    items.append(
                        RecoveryItem(
                            path=attempt.candidate_registry.path,
                            disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                        )
                    )
                    dependency_item = self._interrupted_dependency_graph_item(
                        manifest, attempt
                    )
                    if dependency_item is not None:
                        items.append(dependency_item)
                else:
                    raise _state_invalid(
                        "Production Manifest selects a mixed interrupted audio import pair."
                    )
                repaired.append(replacement)
                changed = True
                continue
            if attempt.candidate_project is None or attempt.candidate_registry is None:
                raise _state_invalid("Incomplete production state attempt has no candidate snapshots.")
            self._validate_recovery_project_pointer(attempt.candidate_project)
            self._validate_recovery_registry_pointer(attempt.candidate_registry)
            self._validate_recovery_project_pointer(attempt.base_project)
            self._validate_recovery_registry_pointer(attempt.base_registry)
            active_pair = (manifest.active_project, manifest.active_registry)
            candidate_pair = (attempt.candidate_project, attempt.candidate_registry)
            base_pair = (attempt.base_project, attempt.base_registry)
            dependency_outcome = self._recovery_dependency_outcome(
                manifest, attempt
            )
            if active_pair == candidate_pair:
                if dependency_outcome not in {"legacy", "candidate"}:
                    raise _state_invalid(
                        "State recovery selects a mixed candidate graph."
                    )
                replacement = _validated_transition(
                    attempt,
                    {
                        "status": StateCommitStatus.SUCCEEDED,
                        "finished_at": _timestamp(),
                        "error_code": None,
                        "error_message": None,
                    },
                )
            elif active_pair != base_pair:
                raise _state_invalid(
                    "Production Manifest selects a mixed interrupted state commit pair."
                )
            else:
                if dependency_outcome not in {"legacy", "base"}:
                    raise _state_invalid(
                        "State recovery selects a mixed base graph."
                    )
                replacement = _validated_transition(
                    attempt,
                    {
                        "status": StateCommitStatus.INTERRUPTED,
                        "finished_at": _timestamp(),
                        "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                        "error_message": "Production state attempt was interrupted before selecting its candidate snapshots.",
                    },
                )
                items.append(
                    RecoveryItem(
                        path=attempt.candidate_project.path,
                        disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
                    )
                )
                dependency_item = self._interrupted_dependency_graph_item(
                    manifest, attempt
                )
                if dependency_item is not None:
                    items.append(dependency_item)
            repaired.append(replacement)
            changed = True
        return repaired, changed, items

    @staticmethod
    def _render_state_artifacts_hash(
        state: RenderStateSnapshot,
        pointer: RenderStateSnapshotPointer,
        *,
        graph: DependencyGraphSnapshotPointer | None = None,
    ) -> str:
        pairs = [
            (state.timeline.path, state.timeline.file_sha256),
            (state.source_bundle.index.path, state.source_bundle.index.file_sha256),
            *((item.path, item.file_sha256) for item in state.source_bundle.assets),
            (state.source_receipt.path, state.source_receipt.file_sha256),
            (state.render_receipt.path, state.render_receipt.file_sha256),
            (state.output.path, state.output.file_sha256),
            (pointer.path, pointer.file_sha256),
        ]
        if graph is not None:
            pairs.append((graph.path, graph.file_sha256))
        artifacts = tuple(
            PreparedArtifact(path, b"", digest)
            for path, digest in sorted(pairs, key=lambda item: item[0].as_posix())
        )
        return _candidate_artifacts_hash(artifacts)

    def _reconstruct_voice_activation_request(
        self, attempt: StateCommitAttempt
    ) -> StateCommitRequest:
        if attempt.candidate_registry is None:
            raise _state_invalid("Voice candidate registry identity is missing.")
        registry_snapshot = _read_regular_file_nofollow(
            self._project_root / attempt.candidate_registry.path,
            contained_by=self._project_root,
        )
        try:
            registry = AssetRegistrySnapshot.model_validate_json(registry_snapshot.data)
        except (ValidationError, ValueError) as exc:
            raise _state_invalid("Voice candidate registry could not be reopened.", str(exc)) from exc
        candidate_ids = set(attempt.candidate_audio_asset_ids) | set(
            attempt.candidate_caption_asset_ids
        )
        by_id = {item.asset_id: item for item in registry.assets}
        if not candidate_ids or not candidate_ids.issubset(by_id):
            raise _state_invalid("Voice candidate asset identities are incomplete.")
        paths = self.voice_attempt_paths(attempt.attempt_id)
        relative_paths = {
            attempt.base_project.path,
            attempt.candidate_registry.path,
            *(by_id[item].artifact_path for item in candidate_ids),
            *(
                path.relative_to(self._project_root)
                for path in (
                    paths.request_path,
                    paths.preview_path,
                    paths.authorization_path,
                    paths.submit_intent_path,
                    paths.alignment_path,
                    paths.cost_path,
                    paths.provenance_path,
                    paths.outcome_path,
                )
            ),
        }
        relative_paths.update(
            Path(f"assets/styles/{by_id[item].caption_metadata.style_content_hash}.json")
            for item in candidate_ids
            if by_id[item].caption_metadata is not None
            and by_id[item].caption_metadata.style_content_hash is not None
        )
        artifacts = tuple(
            PreparedArtifact(path, snapshot.data, snapshot.file_sha256)
            for path in sorted(relative_paths, key=Path.as_posix)
            for snapshot in (
                _read_regular_file_nofollow(
                    self._project_root / path,
                    contained_by=self._project_root,
                ),
            )
        )
        return StateCommitRequest(
            attempt_id=attempt.attempt_id,
            operation="voice_generation",
            expected_manifest_revision=attempt.base_manifest_revision + 2,
            artifacts=artifacts,
            next_project=attempt.base_project,
            next_registry=attempt.candidate_registry,
        )
