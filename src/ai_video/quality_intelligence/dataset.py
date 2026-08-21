"""Manifest-derived Pilot closure and exact Quality Experience lookup."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

from ai_video.production._video_project_reader import load_video_request_receipt
from ai_video.production.models import ProductionManifest
from ai_video.quality_intelligence.models import (
    AttemptIdentityKey,
    BoundedFreeText,
    CanonicalRuntimeBoundary,
    EvidenceState,
    LogicalShotKey,
    ManifestObservationV1,
    PilotAttemptRosterEntry,
    PilotAttemptRosterPointer,
    PilotAttemptRosterV1,
    PilotCaptureCohortPointer,
    PilotCaptureCohortV1,
    PilotDatasetIndexEntry,
    PilotDatasetIndexV1,
    QualityRecordPointer,
)
from ai_video.quality_intelligence.store import (
    QualityExperienceAmbiguous,
    QualityExperienceIntegrityError,
    QualityExperienceNotFound,
    QualityExperienceStore,
)


def _canonical_hash(payload: object) -> str:
    encoded = (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def ordered_attempt_ids_hash(attempt_ids: tuple[str, ...]) -> str:
    """Hash an ordered attempt-ID sequence under a v1-specific domain."""

    return _canonical_hash(
        {
            "domain": "ai-video.quality-experience.manifest-attempt-prefix/v1",
            "attempt_ids": list(attempt_ids),
        }
    )


def _read_regular_nofollow(path: Path) -> bytes:
    descriptor = -1
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError("not a regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    except OSError:
        raise QualityExperienceIntegrityError("Manifest observation is invalid") from None
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def observe_manifest(
    production_root: str | Path, manifest: ProductionManifest
) -> ManifestObservationV1:
    """Bind a typed Manifest to the exact live ``state/manifest.json`` bytes."""

    if manifest.schema_version not in {"2.7", "2.8"}:
        raise QualityExperienceIntegrityError("Manifest schema is not Q0-compatible")
    raw = _read_regular_nofollow(Path(production_root) / "state" / "manifest.json")
    try:
        reopened = ProductionManifest.model_validate_json(raw)
    except Exception:
        raise QualityExperienceIntegrityError("Manifest observation is invalid") from None
    if reopened != manifest:
        raise QualityExperienceIntegrityError("Manifest observation changed")
    attempt_ids = tuple(item.attempt_id for item in manifest.attempts)
    return ManifestObservationV1(
        project_id=manifest.project_id,
        manifest_revision=manifest.manifest_revision,
        file_sha256=hashlib.sha256(raw).hexdigest(),
        attempt_count=len(attempt_ids),
        ordered_attempt_ids_hash=ordered_attempt_ids_hash(attempt_ids),
    )


def create_pilot_capture_cohort(
    *,
    production_root: str | Path,
    manifest: ProductionManifest,
    pilot_id: str,
    purpose: str,
    hypothesis: str,
    authorization_boundary: str,
    capture_contract_version: str,
    rubric_id: str,
    rubric_version: str,
    rubric_hash: str,
    repository_commit: str,
    shot_keys: tuple[LogicalShotKey, ...],
) -> PilotCaptureCohortV1:
    return PilotCaptureCohortV1(
        pilot_id=pilot_id,
        purpose=BoundedFreeText(value=purpose),
        hypothesis=BoundedFreeText(value=hypothesis),
        authorization_boundary=authorization_boundary,
        capture_contract_version=capture_contract_version,
        rubric_id=rubric_id,
        rubric_version=rubric_version,
        rubric_hash=rubric_hash,
        repository_commit=repository_commit,
        base_manifest=observe_manifest(production_root, manifest),
        shot_keys=shot_keys,
    )


def build_pilot_attempt_roster(
    *,
    production_root: str | Path,
    terminal_manifest: ProductionManifest,
    store: QualityExperienceStore,
    cohort_pointer: PilotCaptureCohortPointer,
) -> PilotAttemptRosterV1:
    cohort = store.load_cohort(cohort_pointer)
    terminal = observe_manifest(production_root, terminal_manifest)
    base = cohort.base_manifest
    if (
        terminal.project_id != base.project_id
        or terminal.manifest_revision <= base.manifest_revision
        or terminal.attempt_count < base.attempt_count
    ):
        raise QualityExperienceIntegrityError("Manifest delta is not a forward closure")
    terminal_ids = tuple(item.attempt_id for item in terminal_manifest.attempts)
    if (
        ordered_attempt_ids_hash(terminal_ids[: base.attempt_count])
        != base.ordered_attempt_ids_hash
    ):
        raise QualityExperienceIntegrityError("Manifest base attempt prefix changed")
    shots_by_id: dict[str, list[LogicalShotKey]] = {}
    for shot in cohort.shot_keys:
        shots_by_id.setdefault(shot.shot_id, []).append(shot)
    entries: list[PilotAttemptRosterEntry] = []
    for sequence, attempt in enumerate(
        terminal_manifest.attempts[base.attempt_count :],
        start=base.attempt_count + 1,
    ):
        if attempt.operation != "video_generation":
            continue
        state = attempt.video_generation_state
        if state is None:
            raise QualityExperienceIntegrityError("video attempt request is missing")
        try:
            reopened = load_video_request_receipt(production_root, state.request)
        except Exception:
            raise QualityExperienceIntegrityError("video attempt request could not reopen") from None
        scope = reopened.activation_scope
        if scope is None:
            raise QualityExperienceIntegrityError("video attempt request lacks activation scope")
        request = scope.request
        if (
            reopened.generation_id != state.generation_id
            or request.generation_id != state.generation_id
        ):
            raise QualityExperienceIntegrityError("video attempt generation identity is invalid")
        candidates = shots_by_id.get(request.target_shot_id, [])
        if not candidates:
            continue
        if len(candidates) != 1:
            raise QualityExperienceIntegrityError("video attempt Shot identity is ambiguous")
        shot = candidates[0]
        entries.append(
            PilotAttemptRosterEntry(
                attempt_identity_key=AttemptIdentityKey.from_components(
                    canonical_runtime_boundary=CanonicalRuntimeBoundary.PRODUCTION_MANIFEST,
                    project_id=terminal.project_id,
                    attempt_id=attempt.attempt_id,
                    generation_id=state.generation_id,
                ),
                shot=shot,
                shot_revision=request.target_shot_revision,
                shot_content_hash=request.target_shot_content_hash,
                attempt_sequence=sequence,
            )
        )
    covered = {item.shot.sort_key for item in entries}
    if covered != {item.sort_key for item in cohort.shot_keys}:
        raise QualityExperienceIntegrityError("cohort attempt roster is incomplete")
    try:
        return PilotAttemptRosterV1(
            pilot_id=cohort.pilot_id,
            cohort=cohort_pointer,
            terminal_manifest=terminal,
            entries=tuple(entries),
        )
    except Exception:
        raise QualityExperienceIntegrityError("attempt roster is invalid") from None


def _entry_from_record(
    pointer: QualityRecordPointer,
    record,
) -> PilotDatasetIndexEntry:
    model_id = record.provider.model_id
    if model_id.state is not EvidenceState.KNOWN or model_id.value is None:
        raise QualityExperienceIntegrityError("record model identity is incomplete")
    coverage = tuple(
        sorted(
            {
                f"outcome:{record.outcome.variant}",
                f"provider:{record.provider.kind}",
                f"runtime:{record.canonical_runtime_boundary.value}",
            }
        )
    )
    return PilotDatasetIndexEntry(
        record=pointer,
        experiment_id=record.experiment_id,
        pilot_id=record.pilot_id,
        project_id=record.identity.project_artifact_id,
        scene_id=record.identity.scene_id,
        shot_id=record.identity.shot_id,
        attempt_id=record.identity.attempt_id,
        generation_id=record.identity.generation_id,
        attempt_sequence=record.lineage.attempt_sequence,
        provider_name=record.provider.name,
        provider_kind=record.provider.kind,
        profile_id=record.provider.profile_id,
        capability_id=record.provider.capability_id,
        model_id=model_id.value,
        outcome=record.outcome.variant,
        human_verdict=record.human_review.status,
        coverage_tags=coverage,
    )


def build_pilot_dataset_index(
    *,
    store: QualityExperienceStore,
    cohort: PilotCaptureCohortV1,
    cohort_pointer: PilotCaptureCohortPointer,
    roster: PilotAttemptRosterV1,
    roster_pointer: PilotAttemptRosterPointer,
    record_pointers: tuple[QualityRecordPointer, ...],
    dataset_purpose: str,
    created_at: str,
    repository_commit: str,
    coverage_tags: tuple[str, ...],
    known_confounders: tuple[str, ...],
) -> PilotDatasetIndexV1:
    reopened_cohort = store.load_cohort(cohort_pointer)
    reopened_roster = store.load_roster(roster_pointer)
    if (
        reopened_cohort.model_dump(exclude={"content_hash"})
        != cohort.model_dump(exclude={"content_hash"})
        or reopened_roster.model_dump(exclude={"content_hash"})
        != roster.model_dump(exclude={"content_hash"})
    ):
        raise QualityExperienceIntegrityError("dataset owner pointers are invalid")
    cohort = reopened_cohort
    roster = reopened_roster
    if cohort.pilot_id != roster.pilot_id:
        raise QualityExperienceIntegrityError("dataset pilot identity is invalid")
    records = tuple(store.load_record(pointer) for pointer in record_pointers)
    if any(
        record.canonical_runtime_boundary is not CanonicalRuntimeBoundary.PRODUCTION_MANIFEST
        or record.record_kind != "prospective_q0_attempt"
        for record in records
    ):
        raise QualityExperienceIntegrityError("dataset record boundary is invalid")
    record_keys = tuple(record.attempt_identity_key.identity_hash for record in records)
    roster_keys = tuple(item.attempt_identity_key.identity_hash for item in roster.entries)
    if len(record_keys) != len(set(record_keys)) or set(record_keys) != set(roster_keys):
        raise QualityExperienceIntegrityError("dataset does not exactly close the attempt roster")
    roster_by_key = {
        item.attempt_identity_key.identity_hash: item for item in roster.entries
    }
    entries: list[PilotDatasetIndexEntry] = []
    for pointer, record in zip(record_pointers, records, strict=True):
        roster_entry = roster_by_key[record.attempt_identity_key.identity_hash]
        identity = record.identity
        if (
            record.pilot_id != cohort.pilot_id
            or identity.project_artifact_id != roster_entry.shot.project_id
            or identity.scene_id != roster_entry.shot.scene_id
            or identity.shot_id != roster_entry.shot.shot_id
            or identity.shot_revision != roster_entry.shot_revision
            or identity.shot_content_hash != roster_entry.shot_content_hash
            or identity.generation_id
            != roster_entry.attempt_identity_key.generation_id
            or identity.attempt_id != roster_entry.attempt_identity_key.attempt_id
            or record.lineage.attempt_sequence != roster_entry.attempt_sequence
            or identity.manifest_observation_revision
            != roster.terminal_manifest.manifest_revision
            or identity.manifest_observation_file_hash
            != roster.terminal_manifest.file_sha256
        ):
            raise QualityExperienceIntegrityError("dataset record projection is invalid")
        entries.append(_entry_from_record(pointer, record))
    entries.sort(key=lambda item: item.sort_key)
    covered = {
        (item.project_id, item.scene_id, item.shot_id) for item in entries
    }
    if covered != {item.sort_key for item in cohort.shot_keys}:
        raise QualityExperienceIntegrityError("dataset Shot coverage is incomplete")
    try:
        return PilotDatasetIndexV1(
            pilot_id=cohort.pilot_id,
            dataset_purpose=BoundedFreeText(value=dataset_purpose),
            rubric_id=cohort.rubric_id,
            rubric_version=cohort.rubric_version,
            rubric_hash=cohort.rubric_hash,
            capture_contract_version=cohort.capture_contract_version,
            created_at=created_at,
            repository_commit=repository_commit,
            cohort=cohort_pointer,
            roster=roster_pointer,
            shot_keys=cohort.shot_keys,
            entries=tuple(entries),
            coverage_tags=tuple(coverage_tags),
            known_confounders=tuple(
                BoundedFreeText(value=item) for item in known_confounders
            ),
        )
    except Exception:
        raise QualityExperienceIntegrityError("dataset index is invalid") from None


def exact_lookup(
    index: PilotDatasetIndexV1,
    *,
    experiment_id: str | None = None,
    project_id: str | None = None,
    scene_id: str | None = None,
    shot_id: str | None = None,
    attempt_id: str | None = None,
    generation_id: str | None = None,
    provider_name: str | None = None,
    provider_kind: str | None = None,
    profile_id: str | None = None,
    capability_id: str | None = None,
    model_id: str | None = None,
    outcome: str | None = None,
    human_verdict: str | None = None,
) -> PilotDatasetIndexEntry:
    try:
        index = PilotDatasetIndexV1.model_validate(index.model_dump(mode="json"))
    except Exception:
        raise QualityExperienceIntegrityError("exact dataset lookup input is invalid") from None
    filters = {
        "experiment_id": experiment_id,
        "project_id": project_id,
        "scene_id": scene_id,
        "shot_id": shot_id,
        "attempt_id": attempt_id,
        "generation_id": generation_id,
        "provider_name": provider_name,
        "provider_kind": provider_kind,
        "profile_id": profile_id,
        "capability_id": capability_id,
        "model_id": model_id,
        "outcome": outcome,
        "human_verdict": human_verdict,
    }
    matches = tuple(
        entry
        for entry in index.entries
        if all(
            expected is None or getattr(entry, field) == expected
            for field, expected in filters.items()
        )
    )
    if not matches:
        raise QualityExperienceNotFound("exact dataset lookup found no record")
    if len(matches) != 1:
        raise QualityExperienceAmbiguous("exact dataset lookup is ambiguous")
    return matches[0]
