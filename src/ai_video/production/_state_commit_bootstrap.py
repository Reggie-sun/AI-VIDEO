from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    AssetRegistrySnapshot,
    ProductionManifest,
    ProductionProject,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    canonical_project_snapshot_path,
    canonical_registry_snapshot_path,
)
from ai_video.production.project import (
    load_production_project,
    load_production_project_candidate,
)
from ai_video.production.registry import registry_semantic_sha256

from ._state_commit_common import (
    _canonical_json_bytes,
    _canonical_yaml_bytes,
    _outcome_unknown,
    _state_invalid,
)
from ._state_commit_contracts import PreparedArtifact


_MANIFEST_SCHEMA_ORDER = (
    "2.0",
    "2.1",
    "2.2",
    "2.3",
    "2.4",
    "2.5",
    "2.6",
    "2.7",
    "2.8",
    "2.9",
    "2.10",
)


class _StateCommitBootstrapMixin:
    def upgrade_manifest_schema(
        self,
        target_schema_version: str,
        *,
        expected_manifest_revision: int,
    ) -> ProductionManifest:
        """Advance only the selected Manifest schema through the canonical writer."""

        if target_schema_version not in _MANIFEST_SCHEMA_ORDER:
            raise _state_invalid("Target Production Manifest schema is unsupported.")
        manifest_replaced = [False]
        try:
            with self._exclusive_lock():
                current = self._read_manifest()
                if current.schema_version == target_schema_version:
                    if expected_manifest_revision not in {
                        current.manifest_revision,
                        current.manifest_revision - 1,
                    }:
                        raise _state_invalid(
                            "Production Manifest schema replay revision changed."
                        )
                    reopened = load_production_project(
                        self._project_root / "project.yaml"
                    )
                    if reopened.manifest != current:
                        raise _state_invalid(
                            "Production Manifest schema replay did not reopen safely."
                        )
                    return current
                if current.manifest_revision != expected_manifest_revision:
                    raise _state_invalid(
                        "Production Manifest schema upgrade base revision changed."
                    )
                if _MANIFEST_SCHEMA_ORDER.index(target_schema_version) < (
                    _MANIFEST_SCHEMA_ORDER.index(current.schema_version)
                ):
                    raise _state_invalid(
                        "Production Manifest schema cannot be downgraded."
                    )
                updated = ProductionManifest.model_validate(
                    current.model_copy(
                        update={
                            "schema_version": target_schema_version,
                            "manifest_revision": current.manifest_revision + 1,
                        }
                    ).model_dump(mode="python")
                )
                self._write_manifest_atomic(
                    updated,
                    on_replace=lambda: manifest_replaced.__setitem__(0, True),
                )
                reopened = load_production_project(
                    self._project_root / "project.yaml"
                )
                if reopened.manifest != updated:
                    raise _state_invalid(
                        "Upgraded Production Manifest did not reopen exactly."
                    )
                return updated
        except Exception as exc:
            if manifest_replaced[0]:
                raise _outcome_unknown(exc) from exc
            raise
        except BaseException as exc:
            if manifest_replaced[0]:
                exc.add_note(
                    "Production Manifest schema upgrade outcome may be committed or unknown."
                )
            raise

    def bootstrap_initial_state(
        self,
        *,
        attempt_id: str,
        project: ProductionProject,
        registry: AssetRegistrySnapshot,
        artifacts: tuple[PreparedArtifact, ...],
    ) -> ProductionManifest:
        """Create or exactly replay the first canonical Production bundle."""

        if not attempt_id:
            raise _state_invalid("Production bootstrap attempt ID is required.")
        if not verify_artifact_hash(project):
            raise _state_invalid("Initial Production Project hash is invalid.")
        registry_hash = registry_semantic_sha256(registry)
        if (
            registry.revision_id != registry_hash
            or registry.content_hash != registry_hash
        ):
            raise _state_invalid("Initial Asset Registry hash is invalid.")

        required_paths = {
            project.artifacts.brief.path,
            project.artifacts.story.path,
            project.artifacts.storyboard.path,
            *(item.path for item in project.artifacts.characters),
            *(item.path for item in project.artifacts.scenes),
            *(item.path for item in project.artifacts.shots),
            *(item.artifact_path for item in registry.assets),
        }
        supplied_paths = tuple(item.relative_path for item in artifacts)
        supplied_path_set = set(supplied_paths)
        if len(supplied_paths) != len(supplied_path_set):
            raise _state_invalid(
                "Production bootstrap contains duplicate caller artifact paths."
            )
        if supplied_path_set != required_paths:
            missing = sorted(
                (path.as_posix() for path in required_paths - supplied_path_set)
            )
            extra = sorted(
                (path.as_posix() for path in supplied_path_set - required_paths)
            )
            raise _state_invalid(
                "Production bootstrap artifacts must exactly match the referenced bundle.",
                f"missing={missing}; extra={extra}",
            )

        project_payload = _canonical_yaml_bytes(project)
        registry_payload = _canonical_json_bytes(registry)
        project_path = canonical_project_snapshot_path(
            project.revision, project.content_hash
        )
        registry_path = canonical_registry_snapshot_path(registry.revision_id)
        project_artifact = PreparedArtifact(
            relative_path=project_path,
            payload=project_payload,
            file_sha256=hashlib.sha256(project_payload).hexdigest(),
        )
        registry_artifact = PreparedArtifact(
            relative_path=registry_path,
            payload=registry_payload,
            file_sha256=hashlib.sha256(registry_payload).hexdigest(),
        )
        entrypoint_artifact = PreparedArtifact(
            relative_path=Path("project.yaml"),
            payload=project_payload,
            file_sha256=project_artifact.file_sha256,
        )
        prepared = (*artifacts, project_artifact, registry_artifact, entrypoint_artifact)
        paths = tuple(item.relative_path for item in prepared)
        if len(paths) != len(set(paths)):
            raise _state_invalid("Production bootstrap contains duplicate artifact paths.")
        for artifact in prepared:
            self._validate_artifact_path(artifact.relative_path)
            if hashlib.sha256(artifact.payload).hexdigest() != artifact.file_sha256:
                raise _state_invalid("Prepared artifact hash does not match its payload.")

        manifest = ProductionManifest(
            schema_version="2.0",
            project_id=project.project_id,
            manifest_revision=1,
            active_project=ProjectSnapshotPointer(
                path=project_path,
                revision=project.revision,
                content_hash=project.content_hash,
                file_sha256=project_artifact.file_sha256,
            ),
            active_registry=RegistrySnapshotPointer(
                path=registry_path,
                revision_id=registry.revision_id,
                content_hash=registry.content_hash,
                file_sha256=registry_artifact.file_sha256,
            ),
        )

        try:
            with tempfile.TemporaryDirectory(
                prefix="ai-video-production-bootstrap-"
            ) as temporary:
                validation_root = Path(temporary)
                for artifact in prepared:
                    path = validation_root / artifact.relative_path
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(artifact.payload)
                validation_manifest = validation_root / "state/manifest.json"
                validation_manifest.parent.mkdir(parents=True, exist_ok=True)
                validation_manifest.write_bytes(_canonical_json_bytes(manifest))
                loaded = load_production_project(validation_root / "project.yaml")
                if loaded.manifest != manifest:
                    raise ValueError("bootstrap validation manifest mismatch")
        except Exception as exc:
            raise _state_invalid(
                "Initial Production bundle did not pass strict preflight.",
                str(exc),
            ) from exc

        manifest_replaced = [False]
        try:
            with self._exclusive_lock():
                if (self._project_root / "state/manifest.json").exists():
                    current = self._read_manifest()
                    if current != manifest:
                        raise _state_invalid(
                            "Production state is already initialized with different inputs."
                        )
                    for artifact in prepared:
                        path = self._project_root / artifact.relative_path
                        self._validate_artifact_path(artifact.relative_path)
                        try:
                            actual_sha256 = self._ops.sha256_file(path)
                        except OSError as exc:
                            raise _state_invalid(
                                "Exact Production bootstrap replay could not reopen an artifact.",
                                str(exc),
                            ) from exc
                        if actual_sha256 != artifact.file_sha256:
                            raise _state_invalid(
                                "Exact Production bootstrap replay found changed artifact bytes."
                            )
                    reopened = load_production_project(
                        self._project_root / "project.yaml"
                    )
                    if reopened.manifest != current:
                        raise _state_invalid(
                            "Exact Production bootstrap replay did not reopen safely."
                        )
                    return current
                for artifact in sorted(
                    prepared, key=lambda item: item.relative_path.as_posix()
                ):
                    self._write_immutable_artifact(
                        artifact,
                        attempt_id=attempt_id,
                    )
                load_production_project_candidate(
                    self._project_root,
                    manifest,
                    manifest.active_project.path,
                    manifest.active_registry.path,
                )
                self._write_manifest_atomic(
                    manifest,
                    on_replace=lambda: manifest_replaced.__setitem__(0, True),
                )
                reopened = load_production_project(
                    self._project_root / "project.yaml"
                )
                if reopened.manifest != manifest:
                    raise _state_invalid(
                        "Initial Production Manifest did not reopen exactly."
                    )
        except Exception as exc:
            if manifest_replaced[0]:
                raise _outcome_unknown(exc) from exc
            raise
        except BaseException as exc:
            if manifest_replaced[0]:
                exc.add_note("Production bootstrap outcome may be committed or unknown.")
            raise
        return manifest
