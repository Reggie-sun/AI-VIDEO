from __future__ import annotations

from pathlib import Path

from ai_video.errors import ErrorCode
from ai_video.production._image_project_reader import verify_image_attempt_evidence
from ai_video.production.models import (
    ProductionManifest,
    RecoveryDisposition,
    RecoveryItem,
    StateCommitAttempt,
    StateCommitStatus,
)
from ai_video.production.project import load_production_project_candidate

from ._state_commit_common import _state_invalid, _timestamp, _validated_transition


class _StateCommitImageRecoveryMixin:
    """Single P7 recovery owner; it never mints a permit or invokes a Provider."""

    def _active_image_recovery_items(
        self, manifest: ProductionManifest
    ) -> tuple[RecoveryItem, ...]:
        if manifest.schema_version not in {"2.5", "2.6", "2.7", "2.8", "2.9", "2.10"}:
            return ()
        bundle = self._load_production_project(self._project_root / "project.yaml")
        pairs: dict[Path, str] = {}
        for attempt in manifest.attempts:
            if (
                attempt.operation == "image_generation"
                and attempt.status is StateCommitStatus.SUCCEEDED
                and attempt.image_phase == "activate"
            ):
                pairs.update(verify_image_attempt_evidence(bundle, attempt))
        return tuple(
            RecoveryItem(
                path=path,
                disposition=RecoveryDisposition.ACTIVE,
                sha256=digest,
            )
            for path, digest in sorted(
                pairs.items(), key=lambda item: item[0].as_posix()
            )
        )

    def _recover_image_attempt(
        self,
        manifest: ProductionManifest,
        attempt: StateCommitAttempt,
    ) -> tuple[StateCommitAttempt, tuple[RecoveryItem, ...]]:
        if (
            manifest.schema_version not in {"2.5", "2.6", "2.7", "2.8", "2.9", "2.10"}
            or attempt.image_request is None
        ):
            raise _state_invalid("Interrupted P7 image attempt identity is incomplete.")

        if attempt.image_phase == "request":
            return (
                _validated_transition(
                    attempt,
                    {
                        "status": StateCommitStatus.INTERRUPTED,
                        "finished_at": _timestamp(),
                        "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                        "error_message": (
                            "Image attempt was interrupted before durable submit intent."
                        ),
                    },
                ),
                (),
            )

        candidate_fields = (
            attempt.candidate_project,
            attempt.candidate_registry,
            attempt.candidate_dependency_graph,
            attempt.candidate_dependency_states_hash,
        )
        complete_candidate = all(item is not None for item in candidate_fields) and bool(
            attempt.candidate_image_asset_ids
        )
        if not complete_candidate:
            if any(item is not None for item in candidate_fields) or (
                attempt.candidate_image_asset_ids
            ):
                raise _state_invalid("Interrupted P7 image candidate identity is mixed.")
            return (
                _validated_transition(
                    attempt,
                    {
                        "status": StateCommitStatus.OUTCOME_UNKNOWN,
                        "finished_at": attempt.finished_at or _timestamp(),
                        "error_code": ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN.value,
                        "error_message": (
                            "Image Provider or materialization outcome is unknown; "
                            "blind retry is forbidden."
                        ),
                    },
                ),
                (),
            )

        candidate_project = attempt.candidate_project
        candidate_registry = attempt.candidate_registry
        candidate_graph = attempt.candidate_dependency_graph
        if (
            candidate_project is None
            or candidate_registry is None
            or candidate_graph is None
        ):
            raise _state_invalid("Interrupted P7 image candidate identity is incomplete.")
        candidate_bundle = load_production_project_candidate(
            self._project_root,
            manifest,
            candidate_project.path,
            candidate_registry.path,
        )
        pairs = verify_image_attempt_evidence(candidate_bundle, attempt)
        active_tuple = (
            manifest.active_project,
            manifest.active_registry,
            manifest.active_dependency_graph,
        )
        base_tuple = (
            attempt.base_project,
            attempt.base_registry,
            attempt.base_dependency_graph,
        )
        candidate_tuple = (
            candidate_project,
            candidate_registry,
            candidate_graph,
        )
        outcome = self._recovery_dependency_outcome(manifest, attempt)
        if active_tuple == candidate_tuple:
            if outcome != "candidate":
                raise _state_invalid("Image recovery selects a mixed candidate tuple.")
            loaded = self._load_production_project(self._project_root / "project.yaml")
            if loaded.manifest != manifest:
                raise _state_invalid("Recovered active P7 bundle is not exact.")
            replacement = _validated_transition(
                attempt,
                {
                    "status": StateCommitStatus.SUCCEEDED,
                    "image_phase": "activate",
                    "finished_at": attempt.finished_at or _timestamp(),
                    "error_code": None,
                    "error_message": None,
                },
            )
            disposition = RecoveryDisposition.ACTIVE
        elif active_tuple == base_tuple:
            if outcome != "base":
                raise _state_invalid("Image recovery selects a mixed base tuple.")
            replacement = _validated_transition(
                attempt,
                {
                    "status": StateCommitStatus.INTERRUPTED,
                    "image_phase": "candidate",
                    "finished_at": attempt.finished_at or _timestamp(),
                    "error_code": ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN.value,
                    "error_message": (
                        "Image candidate is durable but explicit activation is required."
                    ),
                },
            )
            disposition = RecoveryDisposition.INTERRUPTED_RECORDED
        else:
            raise _state_invalid(
                "Production Manifest selects a mixed interrupted P7 image tuple."
            )
        return (
            replacement,
            tuple(
                RecoveryItem(path=path, disposition=disposition, sha256=digest)
                for path, digest in pairs
            ),
        )
