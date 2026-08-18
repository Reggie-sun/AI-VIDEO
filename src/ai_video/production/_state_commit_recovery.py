from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    ApprovedRepairReceipt,
    AssetRegistrySnapshot,
    ProductionManifest,
    ProductionProject,
    RecoveryDisposition,
    RecoveryItem,
    RecoveryReport,
    RenderStateSnapshot,
    RenderStateSnapshotPointer,
    StateCommitAttempt,
    StateCommitStatus,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_dependency_graph_snapshot_path,
    canonical_repair_request_path,
)
from ai_video.production.project import (
    _load_exact_render_state,
    load_production_project_candidate,
    load_review_receipt,
)
from ai_video.production.registry import registry_semantic_sha256

from ._state_commit_common import (
    _candidate_artifacts_hash,
    _dependency_states_hash,
    _owned_temp_name,
    _state_invalid,
    _state_recovery_failed,
    _validated_transition,
)
from ._state_commit_contracts import PreparedArtifact


class _StateCommitRecoveryMixin:
    def recover(self) -> RecoveryReport:
        """Repair interrupted P2A attempts without selecting unreferenced snapshots."""
        try:
            return self._recover_locked()
        except AiVideoError as exc:
            if exc.code in {
                ErrorCode.PRODUCTION_STATE_BUSY,
                ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED,
            }:
                raise
            raise _state_recovery_failed(
                "Could not recover production state.", exc.technical_detail or str(exc)
            ) from exc
        except Exception as exc:
            raise _state_recovery_failed("Could not recover production state.", str(exc)) from exc

    def _recover_locked(self) -> RecoveryReport:
        with self._exclusive_lock():
            manifest = self._read_manifest()
            revision_before = manifest.manifest_revision
            manifest, paid_items = self._recover_paid_provider_intents(manifest)
            items = list(self._active_recovery_items(manifest))
            items.extend(paid_items)
            attempts_before_recovery = list(manifest.attempts)
            attempts, changed, interrupted_items = self._recover_attempts(manifest)

            items.extend(self._remove_fixed_manifest_temp())
            items.extend(self._remove_unrecorded_image_request_temps())
            items.extend(self._remove_owned_attempt_temps(attempts_before_recovery))
            items.extend(self._remove_render_attempt_scratch(attempts_before_recovery))
            if changed:
                manifest = _validated_transition(
                    manifest,
                    {
                        "manifest_revision": manifest.manifest_revision + 1,
                        "attempts": tuple(attempts),
                    },
                )
                self._write_manifest_atomic(manifest)
            items.extend(interrupted_items)
            items.extend(self._preserved_orphan_items(manifest, attempts))
            return RecoveryReport(
                manifest_revision_before=revision_before,
                manifest_revision_after=manifest.manifest_revision,
                items=tuple(items),
            )

    def _active_recovery_items(self, manifest: ProductionManifest) -> tuple[RecoveryItem, ...]:
        project_path = self._validate_recovery_project_pointer(manifest.active_project)
        registry_path = self._validate_recovery_registry_pointer(manifest.active_registry)
        project_hash = self._require_recovery_file_hash(
            project_path, manifest.active_project.file_sha256
        )
        registry_hash = self._require_recovery_file_hash(
            registry_path, manifest.active_registry.file_sha256
        )
        if manifest.schema_version in {"2.5", "2.6"}:
            loaded = self._load_production_project(
                self._project_root / "project.yaml"
            )
            if loaded.manifest != manifest:
                raise _state_invalid("Active P7 recovery bundle is not exact.")
        registry_snapshot = _read_regular_file_nofollow(
            registry_path, contained_by=self._project_root
        )
        try:
            active_registry = AssetRegistrySnapshot.model_validate_json(
                registry_snapshot.data
            )
        except (ValidationError, ValueError) as exc:
            raise _state_invalid("Active registry recovery parse failed.", str(exc)) from exc
        p4_asset_items: tuple[RecoveryItem, ...] = ()
        if active_registry.schema_version == "2.1":
            if (
                active_registry.revision_id != manifest.active_registry.revision_id
                or active_registry.content_hash != manifest.active_registry.content_hash
                or registry_semantic_sha256(active_registry) != active_registry.content_hash
            ):
                raise _state_invalid("Active P4 registry recovery identity is invalid.")
            project_snapshot = _read_regular_file_nofollow(
                project_path, contained_by=self._project_root
            )
            try:
                active_project = ProductionProject.model_validate(
                    yaml.safe_load(project_snapshot.data.decode("utf-8"))
                )
            except (UnicodeDecodeError, ValidationError, ValueError, yaml.YAMLError) as exc:
                raise _state_invalid("Active project recovery parse failed.", str(exc)) from exc
            if (
                active_project.project_id != manifest.project_id
                or active_project.revision != manifest.active_project.revision
                or active_project.content_hash != manifest.active_project.content_hash
                or not verify_artifact_hash(active_project)
            ):
                raise _state_invalid("Active project recovery identity is invalid.")
            asset_items: list[RecoveryItem] = []
            for record in active_registry.assets:
                snapshot = _read_regular_file_nofollow(
                    self._project_root / record.artifact_path,
                    contained_by=self._project_root,
                )
                if snapshot.file_sha256 != record.sha256 or len(snapshot.data) != record.size_bytes:
                    raise _state_invalid("Active P4 asset recovery identity is invalid.")
                asset_items.append(
                    RecoveryItem(
                        path=record.artifact_path,
                        disposition=RecoveryDisposition.ACTIVE,
                        sha256=snapshot.file_sha256,
                    )
                )
            p4_asset_items = tuple(asset_items)
        else:
            bundle = load_production_project_candidate(
                self._project_root,
                manifest,
                manifest.active_project.path,
                manifest.active_registry.path,
            )
            self._require_loaded_pointer_identity(
                bundle, manifest.active_project, manifest.active_registry
            )
        self._require_recovery_file_hash(project_path, manifest.active_project.file_sha256)
        self._require_recovery_file_hash(registry_path, manifest.active_registry.file_sha256)
        items = [
            RecoveryItem(
                path=manifest.active_project.path,
                disposition=RecoveryDisposition.ACTIVE,
                sha256=project_hash,
            ),
            RecoveryItem(
                path=manifest.active_registry.path,
                disposition=RecoveryDisposition.ACTIVE,
                sha256=registry_hash,
            ),
        ]
        items.extend(p4_asset_items)
        items.extend(self._active_image_recovery_items(manifest))
        if manifest.active_dependency_graph is not None:
            graph = self._reopen_dependency_graph(manifest.active_dependency_graph)
            self._verify_dependency_candidate(
                manifest, graph, manifest.dependency_states
            )
            items.append(
                RecoveryItem(
                    path=manifest.active_dependency_graph.path,
                    disposition=RecoveryDisposition.ACTIVE,
                    sha256=manifest.active_dependency_graph.file_sha256,
                )
            )
        if manifest.active_render_state is not None:
            if manifest.schema_version in {"2.3", "2.4", "2.5", "2.6"}:
                bundle = load_production_project_candidate(
                    self._project_root,
                    manifest,
                    manifest.active_project.path,
                    manifest.active_registry.path,
                )
                state = _load_exact_render_state(
                    bundle, manifest.active_render_state
                )
            else:
                state = self._load_verified_render_state(
                    self._project_root,
                    manifest.active_render_state,
                    project=manifest.active_project,
                    registry=manifest.active_registry,
                )
            items.extend(
                self._render_graph_recovery_items(
                    state,
                    manifest.active_render_state,
                    RecoveryDisposition.ACTIVE,
                )
            )
        items.extend(self._p6_active_recovery_items(manifest))
        if manifest.active_paid_provider_budget is not None:
            budget = self._reopen_paid_budget(manifest.active_paid_provider_budget)
            items.append(
                RecoveryItem(
                    path=manifest.active_paid_provider_budget.path,
                    disposition=RecoveryDisposition.ACTIVE,
                    sha256=manifest.active_paid_provider_budget.file_sha256,
                )
            )
            reservation_ids = {item.reservation_id for item in budget.reservations}
            for attempt in manifest.attempts:
                state = attempt.paid_provider_state
                if state is None:
                    continue
                if state.reservation_id not in reservation_ids:
                    raise _state_invalid("Paid Provider recovery reservation is missing.")
                self._reopen_paid_gate(state.gate_receipt)
                items.append(
                    RecoveryItem(
                        path=state.gate_receipt.path,
                        disposition=RecoveryDisposition.ACTIVE,
                        sha256=state.gate_receipt.file_sha256,
                    )
                )
                if state.submit_receipt is not None:
                    self._reopen_paid_submit(state.submit_receipt)
                    items.append(
                        RecoveryItem(
                            path=state.submit_receipt.path,
                            disposition=RecoveryDisposition.ACTIVE,
                            sha256=state.submit_receipt.file_sha256,
                        )
                    )
        return tuple(items)

    def _p6_active_recovery_items(
        self, manifest: ProductionManifest
    ) -> tuple[RecoveryItem, ...]:
        if (
            manifest.schema_version not in {"2.4", "2.5", "2.6"}
            or manifest.active_qa_policy is None
        ):
            return ()
        pointers: dict[Path, str] = {
            manifest.active_qa_policy.path: manifest.active_qa_policy.file_sha256,
        }
        for receipt_pointer in manifest.active_review_receipts:
            receipt = load_review_receipt(self._project_root, receipt_pointer)
            pointers[receipt_pointer.path] = receipt_pointer.file_sha256
            for evidence_pointer in receipt.evidence:
                pointers[evidence_pointer.path] = evidence_pointer.file_sha256
        if manifest.active_approved_repair is not None:
            pointer = manifest.active_approved_repair
            pointers[pointer.path] = pointer.file_sha256
            snapshot = _read_regular_file_nofollow(
                self._project_root / pointer.path,
                contained_by=self._project_root / "state",
            )
            approved = ApprovedRepairReceipt.model_validate_json(snapshot.data)
            request_path = canonical_repair_request_path(
                approved.request_content_hash
            )
            request_snapshot = _read_regular_file_nofollow(
                self._project_root / request_path,
                contained_by=self._project_root / "state",
            )
            pointers[request_path] = request_snapshot.file_sha256
        for pointer in manifest.repair_outcome_receipts:
            pointers[pointer.path] = pointer.file_sha256
        if (
            manifest.final_acceptance_state is not None
            and manifest.final_acceptance_state.active_receipt is not None
        ):
            pointer = manifest.final_acceptance_state.active_receipt
            pointers[pointer.path] = pointer.file_sha256
        for attempt in manifest.attempts:
            if attempt.review_request is not None:
                pointers[attempt.review_request.path] = attempt.review_request.file_sha256
        items: list[RecoveryItem] = []
        for path, expected_hash in sorted(pointers.items()):
            actual_hash = self._require_recovery_file_hash(
                self._project_root / path, expected_hash
            )
            items.append(
                RecoveryItem(
                    path=path,
                    disposition=RecoveryDisposition.ACTIVE,
                    sha256=actual_hash,
                )
            )
        return tuple(items)

    def _recovery_dependency_outcome(
        self,
        manifest: ProductionManifest,
        attempt: StateCommitAttempt,
    ) -> Literal["legacy", "base", "candidate"]:
        graph_fields = (
            attempt.base_dependency_graph,
            attempt.candidate_dependency_graph,
            attempt.candidate_dependency_states_hash,
        )
        if all(item is None for item in graph_fields):
            return "legacy"
        if (
            manifest.schema_version not in {"2.3", "2.4", "2.5", "2.6"}
            or attempt.candidate_dependency_graph is None
            or attempt.candidate_dependency_states_hash is None
        ):
            raise _state_invalid(
                "Interrupted P5 attempt dependency identity is incomplete."
            )
        active_graph = manifest.active_dependency_graph
        active_states_hash = _dependency_states_hash(manifest.dependency_states)
        if (
            active_graph == attempt.candidate_dependency_graph
            and active_states_hash == attempt.candidate_dependency_states_hash
        ):
            graph = self._reopen_dependency_graph(
                attempt.candidate_dependency_graph
            )
            self._verify_dependency_candidate(
                manifest, graph, manifest.dependency_states
            )
            return "candidate"
        if active_graph == attempt.base_dependency_graph:
            try:
                self._reopen_dependency_graph(attempt.candidate_dependency_graph)
            except AiVideoError:
                candidate_absent = self._dependency_graph_candidate_is_absent(
                    attempt
                )
                recoverable_absence = (
                    attempt.operation in {"commit_project_registry", "audio_import"}
                    and candidate_absent
                )
                if (
                    not (
                        candidate_absent
                        and self._has_owned_dependency_graph_temp(attempt)
                    )
                    and not recoverable_absence
                ):
                    raise
            return "base"
        raise _state_invalid(
            "Production Manifest selects a mixed interrupted dependency graph."
        )

    def _interrupted_dependency_graph_item(
        self,
        manifest: ProductionManifest,
        attempt: StateCommitAttempt,
    ) -> RecoveryItem | None:
        candidate = attempt.candidate_dependency_graph
        if candidate is None or candidate == manifest.active_dependency_graph:
            return None
        if self._dependency_graph_candidate_is_absent(attempt):
            return None
        self._reopen_dependency_graph(candidate)
        return RecoveryItem(
            path=candidate.path,
            disposition=RecoveryDisposition.INTERRUPTED_RECORDED,
            sha256=candidate.file_sha256,
        )

    def _has_owned_dependency_graph_temp(
        self, attempt: StateCommitAttempt
    ) -> bool:
        candidate = attempt.candidate_dependency_graph
        if candidate is None or attempt.status is not StateCommitStatus.RUNNING:
            return False
        expected_path = canonical_dependency_graph_snapshot_path(
            candidate.revision_id
        )
        if candidate.path != expected_path:
            raise _state_invalid(
                "Interrupted dependency graph path is noncanonical."
            )
        final_path = self._project_root / expected_path
        temp_path = final_path.parent / _owned_temp_name(
            attempt.attempt_id, final_path
        )
        try:
            self._recovery_file_digest(temp_path)
        except FileNotFoundError:
            return False
        return True

    def _dependency_graph_candidate_is_absent(
        self, attempt: StateCommitAttempt
    ) -> bool:
        candidate = attempt.candidate_dependency_graph
        if candidate is None or attempt.status is not StateCommitStatus.RUNNING:
            return False
        expected_path = canonical_dependency_graph_snapshot_path(
            candidate.revision_id
        )
        if candidate.path != expected_path:
            raise _state_invalid(
                "Interrupted dependency graph path is noncanonical."
            )
        try:
            self._recovery_file_digest(self._project_root / expected_path)
        except FileNotFoundError:
            return True
        return False

    @staticmethod
    def _candidate_hash_with_optional_graph(
        artifacts: tuple[PreparedArtifact, ...],
        attempt: StateCommitAttempt,
    ) -> tuple[str, ...]:
        hashes = [_candidate_artifacts_hash(artifacts)]
        graph = attempt.candidate_dependency_graph
        if graph is not None and all(
            item.relative_path != graph.path for item in artifacts
        ):
            hashes.append(
                _candidate_artifacts_hash(
                    (
                        *artifacts,
                        PreparedArtifact(graph.path, b"", graph.file_sha256),
                    )
                )
            )
        return tuple(hashes)

    @staticmethod
    def _render_graph_recovery_items(
        state: RenderStateSnapshot,
        pointer: RenderStateSnapshotPointer,
        disposition: RecoveryDisposition,
    ) -> tuple[RecoveryItem, ...]:
        pairs = [
            (state.timeline.path, state.timeline.file_sha256),
            (state.source_bundle.index.path, state.source_bundle.index.file_sha256),
            *((item.path, item.file_sha256) for item in state.source_bundle.assets),
            (state.source_receipt.path, state.source_receipt.file_sha256),
            (state.render_receipt.path, state.render_receipt.file_sha256),
            (state.output.path, state.output.file_sha256),
            (pointer.path, pointer.file_sha256),
        ]
        return tuple(
            RecoveryItem(path=path, disposition=disposition, sha256=digest)
            for path, digest in sorted(pairs, key=lambda item: item[0].as_posix())
        )
