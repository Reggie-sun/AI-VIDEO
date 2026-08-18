from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable

import yaml
from pydantic import ValidationError

from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    AssetRegistrySnapshot,
    DependencyGraphSnapshot,
    DependencyGraphSnapshotPointer,
    LoadedProductionProject,
    ProductionProject,
    RegistrySnapshotPointer,
    StateCommitAttempt,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_voice_attempt_artifact_path,
)
from ai_video.production.registry import registry_semantic_sha256

DependencyGraphLoader = Callable[
    [Path, DependencyGraphSnapshotPointer], DependencyGraphSnapshot
]


def _read_voice_registry_pointer(
    root: Path, pointer: RegistrySnapshotPointer, label: str
) -> AssetRegistrySnapshot:
    snapshot = _read_regular_file_nofollow(root / pointer.path, contained_by=root)
    if snapshot.file_sha256 != pointer.file_sha256:
        raise ValueError(f"{label} registry file hash mismatch")
    registry = AssetRegistrySnapshot.model_validate_json(snapshot.data)
    if (
        registry.revision_id != pointer.revision_id
        or registry.content_hash != pointer.content_hash
        or registry_semantic_sha256(registry) != pointer.content_hash
    ):
        raise ValueError(f"{label} registry identity mismatch")
    return registry


def verify_voice_candidate_history(
    bundle: LoadedProductionProject,
    attempts: tuple[StateCommitAttempt, ...],
    *,
    load_dependency_graph: DependencyGraphLoader,
) -> dict[str, StateCommitAttempt]:
    """Reopen the read-only P4 voice candidate history proof.

    Dependency graph bytes and semantic identity stay owned by the caller's
    active graph loader, which is injected as a narrow callback.
    """

    claimed: dict[str, StateCommitAttempt] = {}
    current_assets = bundle.registry.assets
    for attempt in attempts:
        if attempt.candidate_registry is None or attempt.candidate_project not in (
            None,
            attempt.base_project,
        ):
            raise ValueError("voice attempt candidate pointers are incomplete")
        project_snapshot = _read_regular_file_nofollow(
            bundle.root / attempt.base_project.path, contained_by=bundle.root
        )
        if project_snapshot.file_sha256 != attempt.base_project.file_sha256:
            raise ValueError("voice base project file hash mismatch")
        try:
            project = ProductionProject.model_validate(
                yaml.safe_load(project_snapshot.data.decode("utf-8"))
            )
        except (UnicodeDecodeError, ValidationError, ValueError, yaml.YAMLError) as exc:
            raise ValueError("voice base project is invalid") from exc
        if (
            project.revision != attempt.base_project.revision
            or project.content_hash != attempt.base_project.content_hash
            or not verify_artifact_hash(project)
        ):
            raise ValueError("voice base project identity mismatch")
        base = _read_voice_registry_pointer(bundle.root, attempt.base_registry, "base")
        candidate = _read_voice_registry_pointer(
            bundle.root, attempt.candidate_registry, "candidate"
        )
        if (
            candidate.schema_version != "2.1"
            or candidate.assets[: len(base.assets)] != base.assets
        ):
            raise ValueError(
                "voice candidate registry does not preserve its base prefix"
            )
        suffix = candidate.assets[len(base.assets) :]
        expected_ids = tuple(
            sorted(
                (
                    *attempt.candidate_audio_asset_ids,
                    *attempt.candidate_caption_asset_ids,
                )
            )
        )
        if (
            tuple(item.asset_id for item in suffix) != expected_ids
            or current_assets[: len(candidate.assets)] != candidate.assets
        ):
            raise ValueError(
                "selected registry does not retain exact voice candidate history"
            )
        pairs: list[tuple[str, str]] = [
            (attempt.base_project.path.as_posix(), project_snapshot.file_sha256),
            (
                attempt.candidate_registry.path.as_posix(),
                attempt.candidate_registry.file_sha256,
            ),
        ]
        if (attempt.base_dependency_graph is None) != (
            attempt.candidate_dependency_graph is None
        ):
            raise ValueError("voice attempt dependency graph pointers are incomplete")
        if attempt.candidate_dependency_graph is not None:
            load_dependency_graph(
                bundle.root,
                attempt.candidate_dependency_graph,
            )
            pairs.append(
                (
                    attempt.candidate_dependency_graph.path.as_posix(),
                    attempt.candidate_dependency_graph.file_sha256,
                )
            )
        for record in suffix:
            if record.asset_id in claimed:
                raise ValueError(
                    "voice candidate asset ID is claimed by multiple attempts"
                )
            claimed[record.asset_id] = attempt
            artifact = _read_regular_file_nofollow(
                bundle.root / record.artifact_path, contained_by=bundle.root
            )
            if (
                artifact.file_sha256 != record.sha256
                or artifact.size_bytes != record.size_bytes
            ):
                raise ValueError("voice candidate asset bytes do not match registry")
            pairs.append((record.artifact_path.as_posix(), artifact.file_sha256))
            metadata = record.caption_metadata
            if metadata is not None and metadata.style_content_hash is not None:
                style_path = Path(f"assets/styles/{metadata.style_content_hash}.json")
                style = _read_regular_file_nofollow(
                    bundle.root / style_path, contained_by=bundle.root
                )
                if style.file_sha256 != metadata.style_content_hash:
                    raise ValueError("voice candidate caption style hash mismatch")
                pairs.append((style_path.as_posix(), style.file_sha256))
        for name in (
            "request.json",
            "preview.json",
            "authorization.json",
            "submit-intent.json",
            "alignment.json",
            "cost.json",
            "provenance.json",
            "outcome.json",
        ):
            evidence_path = canonical_voice_attempt_artifact_path(
                bundle.root, attempt.attempt_id, name
            )
            evidence = _read_regular_file_nofollow(
                evidence_path, contained_by=bundle.root
            )
            pairs.append(
                (
                    evidence_path.relative_to(bundle.root).as_posix(),
                    evidence.file_sha256,
                )
            )
        if len({path for path, _ in pairs}) != len(pairs):
            raise ValueError("voice candidate evidence contains duplicate paths")
        payload = json.dumps(sorted(pairs), separators=(",", ":")).encode("utf-8")
        if hashlib.sha256(payload).hexdigest() != attempt.candidate_artifacts_hash:
            raise ValueError("voice candidate artifact evidence hash mismatch")
    return claimed
