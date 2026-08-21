from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    ProductionManifest,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    StateCommitAttempt,
    VideoGenerationAttemptState,
    VideoRequestReceiptPointer,
)
from ai_video.quality_intelligence.models import QualityExperienceRecordV1
from ai_video.quality_intelligence.store import (
    QualityExperienceAmbiguous,
    QualityExperienceIntegrityError,
    QualityExperienceNotFound,
    QualityExperienceStore,
)


FIXTURES = Path(__file__).parent / "fixtures" / "quality_experience" / "v1"
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _dataset_api():
    return importlib.import_module("ai_video.quality_intelligence.dataset")


def _project_pointer() -> ProjectSnapshotPointer:
    return ProjectSnapshotPointer(
        path=Path(f"state/projects/project.1.{HASH_A}.yaml"),
        revision=1,
        content_hash=HASH_A,
        file_sha256=HASH_B,
    )


def _registry_pointer() -> RegistrySnapshotPointer:
    return RegistrySnapshotPointer(
        path=Path(f"assets/registry.{HASH_A}.json"),
        revision_id=HASH_A,
        content_hash=HASH_A,
        file_sha256=HASH_B,
    )


def _graph_pointer() -> DependencyGraphSnapshotPointer:
    return DependencyGraphSnapshotPointer(
        path=Path(f"state/dependency_graph.{HASH_A}.json"),
        revision_id=HASH_A,
        content_hash=HASH_A,
        file_sha256=HASH_B,
    )


def _attempt(
    attempt_id: str,
    *,
    shot_id: str = "shot_001",
    generation_id: str | None = None,
    operation: str = "video_generation",
) -> StateCommitAttempt:
    common = dict(
        attempt_id=attempt_id,
        operation=operation,
        status="failed",
        base_manifest_revision=1,
        base_project=_project_pointer(),
        base_registry=_registry_pointer(),
        candidate_artifacts_hash=HASH_C,
        started_at="2026-08-21T00:00:00Z",
        finished_at="2026-08-21T00:01:00Z",
        error_code="VIDEO_PROVIDER_FAILED",
        error_message="sanitized failure",
    )
    if operation != "video_generation":
        return StateCommitAttempt(**common)
    generation = generation_id or f"generation_{shot_id}"
    fingerprint = hashlib.sha256(attempt_id.encode()).hexdigest()
    request = VideoRequestReceiptPointer(
        path=Path(f"state/video-generation/requests/{fingerprint}.json"),
        request_receipt_fingerprint=fingerprint,
        generation_id=generation,
        request_input_hash=HASH_A,
        resolved_generation_hash=HASH_B,
        output_asset_id=f"output_{shot_id}",
        file_sha256=HASH_C,
    )
    return StateCommitAttempt(
        **common,
        base_dependency_graph=_graph_pointer(),
        video_generation_state=VideoGenerationAttemptState(
            request=request,
            generation_id=generation,
            resolved_generation_hash=HASH_B,
            phase="request",
        ),
    )


def _manifest(
    *, revision: int, attempts: tuple[StateCommitAttempt, ...] = ()
) -> ProductionManifest:
    return ProductionManifest(
        schema_version="2.7",
        project_id="project_001",
        manifest_revision=revision,
        active_project=_project_pointer(),
        active_registry=_registry_pointer(),
        active_dependency_graph=_graph_pointer(),
        attempts=attempts,
    )


def _write_manifest(root: Path, manifest: ProductionManifest) -> bytes:
    raw = manifest.model_dump_json().encode("utf-8")
    path = root / "state" / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


def _shot_keys(count: int):
    LogicalShotKey = getattr(_dataset_api(), "LogicalShotKey")
    return tuple(
        LogicalShotKey(
            project_id="project_001",
            scene_id="scene_001",
            shot_id=f"shot_{index:03d}",
        )
        for index in range(1, count + 1)
    )


def _cohort(root: Path, *, count: int = 4):
    api = _dataset_api()
    base = _manifest(revision=1, attempts=(_attempt("bootstrap", operation="bootstrap"),))
    _write_manifest(root, base)
    return api.create_pilot_capture_cohort(
        production_root=root,
        manifest=base,
        pilot_id="pilot_a",
        purpose="passive capture completeness",
        hypothesis="all exact attempts remain represented",
        authorization_boundary="q0_passive_capture_only",
        capture_contract_version="qer_v1",
        rubric_id="visual_quality_v1",
        rubric_version="1.0.0",
        rubric_hash=HASH_A,
        repository_commit="0" * 40,
        shot_keys=_shot_keys(count),
    )


def _request_for(attempt: StateCommitAttempt, shot_id: str):
    assert attempt.video_generation_state is not None
    return SimpleNamespace(
        generation_id=attempt.video_generation_state.generation_id,
        activation_scope=SimpleNamespace(
            request=SimpleNamespace(
                generation_id=attempt.video_generation_state.generation_id,
                target_shot_id=shot_id,
                target_shot_revision=1,
                target_shot_content_hash=HASH_A,
            )
        ),
    )


def _roster(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    shot_count: int = 4,
    extra_first_shot_attempt: bool = False,
):
    api = _dataset_api()
    cohort = _cohort(root, count=shot_count)
    store = QualityExperienceStore(root.parent / "dataset")
    cohort_pointer = store.write_cohort(cohort)
    video_attempts = [
        (
            _attempt(f"attempt_{index:03d}", shot_id=f"shot_{index:03d}"),
            f"shot_{index:03d}",
        )
        for index in range(1, shot_count + 1)
    ]
    if extra_first_shot_attempt:
        video_attempts.append(
            (
                _attempt(
                    "attempt_001_retry",
                    shot_id="shot_001",
                    generation_id="generation_shot_001_retry",
                ),
                "shot_001",
            )
        )
    attempts = (_attempt("bootstrap", operation="bootstrap"),) + tuple(
        item for item, _shot_id in video_attempts
    )
    terminal = _manifest(revision=2, attempts=attempts)
    _write_manifest(root, terminal)
    by_fingerprint = {
        item.video_generation_state.request.request_receipt_fingerprint: _request_for(
            item, shot_id
        )
        for item, shot_id in video_attempts
        if item.video_generation_state is not None
    }

    def fake_load(_root, pointer):
        return by_fingerprint[pointer.request_receipt_fingerprint]

    monkeypatch.setattr(api, "load_video_request_receipt", fake_load)
    roster = api.build_pilot_attempt_roster(
        production_root=root,
        terminal_manifest=terminal,
        store=store,
        cohort_pointer=cohort_pointer,
    )
    return store, cohort, cohort_pointer, roster


def _record_for(
    entry, *, terminal_manifest=None, pilot_id: str = "pilot_a"
) -> QualityExperienceRecordV1:
    payload = json.loads((FIXTURES / "prospective_success.json").read_text())
    payload["pilot_id"] = pilot_id
    payload["identity"].update(
        {
            "project_artifact_id": entry.shot.project_id,
            "manifest_observation_revision": (
                terminal_manifest.manifest_revision if terminal_manifest else 2
            ),
            "manifest_observation_file_hash": (
                terminal_manifest.file_sha256 if terminal_manifest else HASH_B
            ),
            "scene_id": entry.shot.scene_id,
            "shot_id": entry.shot.shot_id,
            "shot_revision": entry.shot_revision,
            "shot_content_hash": entry.shot_content_hash,
            "generation_id": entry.attempt_identity_key.generation_id,
            "attempt_id": entry.attempt_identity_key.attempt_id,
        }
    )
    payload["lineage"]["attempt_sequence"] = entry.attempt_sequence
    payload["continuity"]["target_shot_id"] = entry.shot.shot_id
    payload["artifact_evidence"]["relative_path"] = (
        f"shots/{entry.shot.shot_id}/{entry.attempt_identity_key.attempt_id}.mp4"
    )
    payload["artifact_evidence"]["asset_id"] = (
        f"asset_{entry.attempt_identity_key.attempt_id}"
    )
    payload["artifact_evidence"]["file_sha256"] = f"{entry.attempt_sequence:064x}"
    payload["analyzer"]["evidence"][0]["subject_id"] = (
        payload["artifact_evidence"]["asset_id"]
    )
    return QualityExperienceRecordV1.model_validate(payload)


def test_manifest_observation_seals_exact_bytes_without_lifecycle_copy(tmp_path: Path) -> None:
    api = _dataset_api()
    manifest = _manifest(revision=4, attempts=(_attempt("bootstrap", operation="bootstrap"),))
    raw = _write_manifest(tmp_path, manifest)
    observation = api.observe_manifest(tmp_path, manifest)
    assert observation.file_sha256 == hashlib.sha256(raw).hexdigest()
    assert observation.manifest_revision == 4
    assert observation.attempt_count == 1
    assert not hasattr(observation, "active_project")


def test_pilot_cohort_and_roster_fixtures_are_strict() -> None:
    api = _dataset_api()
    cohort = api.PilotCaptureCohortV1.model_validate_json(
        (FIXTURES / "pilot_cohort.json").read_bytes()
    )
    roster = api.PilotAttemptRosterV1.model_validate_json(
        (FIXTURES / "pilot_attempt_roster.json").read_bytes()
    )
    assert len(cohort.shot_keys) == 4
    assert tuple(item.attempt_sequence for item in roster.entries) == (2, 3, 4, 5)


@pytest.mark.parametrize("count", [3, 9])
def test_cohort_rejects_shot_count_outside_four_to_eight(tmp_path: Path, count: int) -> None:
    with pytest.raises(Exception):
        _cohort(tmp_path, count=count)


def test_roster_uses_exact_terminal_suffix_order_and_request_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _store, _cohort_model, _pointer, roster = _roster(tmp_path, monkeypatch)
    assert tuple(item.attempt_sequence for item in roster.entries) == (2, 3, 4, 5)
    assert tuple(item.shot.shot_id for item in roster.entries) == (
        "shot_001",
        "shot_002",
        "shot_003",
        "shot_004",
    )


def test_roster_rejects_terminal_shorter_than_base(tmp_path: Path) -> None:
    api = _dataset_api()
    base = _manifest(
        revision=2,
        attempts=(
            _attempt("bootstrap", operation="bootstrap"),
            _attempt("preexisting", operation="bootstrap"),
        ),
    )
    _write_manifest(tmp_path, base)
    cohort = api.create_pilot_capture_cohort(
        production_root=tmp_path,
        manifest=base,
        pilot_id="pilot_a",
        purpose="passive capture completeness",
        hypothesis="all exact attempts remain represented",
        authorization_boundary="q0_passive_capture_only",
        capture_contract_version="qer_v1",
        rubric_id="visual_quality_v1",
        rubric_version="1.0.0",
        rubric_hash=HASH_A,
        repository_commit="0" * 40,
        shot_keys=_shot_keys(4),
    )
    store = QualityExperienceStore(tmp_path.parent / "dataset")
    pointer = store.write_cohort(cohort)
    terminal = _manifest(
        revision=3, attempts=(_attempt("bootstrap", operation="bootstrap"),)
    )
    _write_manifest(tmp_path, terminal)
    with pytest.raises(QualityExperienceIntegrityError):
        api.build_pilot_attempt_roster(
            production_root=tmp_path,
            terminal_manifest=terminal,
            store=store,
            cohort_pointer=pointer,
        )


def test_roster_rejects_nonexact_base_prefix(tmp_path: Path) -> None:
    api = _dataset_api()
    cohort = _cohort(tmp_path)
    store = QualityExperienceStore(tmp_path.parent / "dataset")
    pointer = store.write_cohort(cohort)
    terminal = _manifest(
        revision=2, attempts=(_attempt("different", operation="bootstrap"),)
    )
    _write_manifest(tmp_path, terminal)
    with pytest.raises(QualityExperienceIntegrityError):
        api.build_pilot_attempt_roster(
            production_root=tmp_path,
            terminal_manifest=terminal,
            store=store,
            cohort_pointer=pointer,
        )


def test_roster_rejects_nonforward_manifest_revision(tmp_path: Path) -> None:
    api = _dataset_api()
    cohort = _cohort(tmp_path)
    store = QualityExperienceStore(tmp_path.parent / "dataset")
    pointer = store.write_cohort(cohort)
    terminal = _manifest(
        revision=1,
        attempts=(_attempt("bootstrap", operation="bootstrap"),),
    )
    _write_manifest(tmp_path, terminal)

    with pytest.raises(QualityExperienceIntegrityError):
        api.build_pilot_attempt_roster(
            production_root=tmp_path,
            terminal_manifest=terminal,
            store=store,
            cohort_pointer=pointer,
        )


def test_roster_rejects_wrong_project_terminal_manifest(tmp_path: Path) -> None:
    api = _dataset_api()
    cohort = _cohort(tmp_path)
    store = QualityExperienceStore(tmp_path.parent / "dataset")
    pointer = store.write_cohort(cohort)
    terminal = _manifest(revision=2).model_copy(update={"project_id": "project_002"})
    _write_manifest(tmp_path, terminal)

    with pytest.raises(QualityExperienceIntegrityError):
        api.build_pilot_attempt_roster(
            production_root=tmp_path,
            terminal_manifest=terminal,
            store=store,
            cohort_pointer=pointer,
        )


def test_roster_rejects_forged_cohort_pointer(tmp_path: Path) -> None:
    api = _dataset_api()
    cohort = _cohort(tmp_path)
    store = QualityExperienceStore(tmp_path.parent / "dataset")
    pointer = store.write_cohort(cohort)
    forged = pointer.model_copy(update={"file_sha256": "f" * 64})

    with pytest.raises(QualityExperienceIntegrityError):
        api.build_pilot_attempt_roster(
            production_root=tmp_path,
            terminal_manifest=_manifest(revision=2),
            store=store,
            cohort_pointer=forged,
        )


def test_roster_sanitizes_missing_request_without_echoing_provider_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _dataset_api()
    cohort = _cohort(tmp_path)
    store = QualityExperienceStore(tmp_path.parent / "dataset")
    pointer = store.write_cohort(cohort)
    terminal = _manifest(
        revision=2,
        attempts=(
            _attempt("bootstrap", operation="bootstrap"),
            _attempt("attempt_001", shot_id="shot_001"),
        ),
    )
    _write_manifest(tmp_path, terminal)

    def fail_reopen(*_args):
        raise RuntimeError("https://signed.example/?token=raw-secret")

    monkeypatch.setattr(api, "load_video_request_receipt", fail_reopen)
    with pytest.raises(QualityExperienceIntegrityError) as exc_info:
        api.build_pilot_attempt_roster(
            production_root=tmp_path,
            terminal_manifest=terminal,
            store=store,
            cohort_pointer=pointer,
        )
    assert "signed.example" not in str(exc_info.value)
    assert "raw-secret" not in repr(exc_info.value)


def test_roster_rejects_request_generation_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _dataset_api()
    cohort = _cohort(tmp_path)
    store = QualityExperienceStore(tmp_path.parent / "dataset")
    pointer = store.write_cohort(cohort)
    terminal = _manifest(
        revision=2,
        attempts=(
            _attempt("bootstrap", operation="bootstrap"),
            _attempt("attempt_001", shot_id="shot_001"),
        ),
    )
    _write_manifest(tmp_path, terminal)

    def mismatched_request(_root, _pointer):
        return SimpleNamespace(
            generation_id="generation_wrong",
            activation_scope=SimpleNamespace(
                request=SimpleNamespace(
                    generation_id="generation_wrong",
                    target_shot_id="shot_001",
                    target_shot_revision=1,
                    target_shot_content_hash=HASH_A,
                )
            ),
        )

    monkeypatch.setattr(api, "load_video_request_receipt", mismatched_request)
    with pytest.raises(QualityExperienceIntegrityError):
        api.build_pilot_attempt_roster(
            production_root=tmp_path,
            terminal_manifest=terminal,
            store=store,
            cohort_pointer=pointer,
        )


def test_index_requires_exact_roster_record_key_set_including_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _dataset_api()
    store, cohort, cohort_pointer, roster = _roster(tmp_path / "production", monkeypatch)
    roster_pointer = store.write_roster(roster)
    pointers = tuple(
        store.write_record(_record_for(item, terminal_manifest=roster.terminal_manifest))
        for item in roster.entries
    )
    with pytest.raises(QualityExperienceIntegrityError):
        api.build_pilot_dataset_index(
            store=store,
            cohort=cohort,
            cohort_pointer=cohort_pointer,
            roster=roster,
            roster_pointer=roster_pointer,
            record_pointers=pointers[:-1],
            dataset_purpose="closed Q0 comparison",
            created_at="2026-08-21T12:00:00Z",
            repository_commit="0" * 40,
            coverage_tags=("baseline",),
            known_confounders=(),
        )


def test_index_rejects_wrong_terminal_manifest_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _dataset_api()
    store, cohort, cohort_pointer, roster = _roster(tmp_path / "production", monkeypatch)
    roster_pointer = store.write_roster(roster)
    records = [
        _record_for(item, terminal_manifest=roster.terminal_manifest)
        for item in roster.entries
    ]
    payload = records[0].model_dump(mode="json")
    payload["identity"]["manifest_observation_file_hash"] = "f" * 64
    records[0] = QualityExperienceRecordV1.model_validate(payload)
    pointers = tuple(store.write_record(item) for item in records)
    with pytest.raises(QualityExperienceIntegrityError):
        api.build_pilot_dataset_index(
            store=store,
            cohort=cohort,
            cohort_pointer=cohort_pointer,
            roster=roster,
            roster_pointer=roster_pointer,
            record_pointers=pointers,
            dataset_purpose="closed Q0 comparison",
            created_at="2026-08-21T12:00:00Z",
            repository_commit="0" * 40,
            coverage_tags=("baseline",),
            known_confounders=(),
        )


@pytest.mark.parametrize("mismatch", ("pilot", "project", "shot", "generation"))
def test_index_rejects_record_identity_outside_exact_roster(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mismatch: str,
) -> None:
    api = _dataset_api()
    store, cohort, cohort_pointer, roster = _roster(tmp_path / "production", monkeypatch)
    roster_pointer = store.write_roster(roster)
    records = [
        _record_for(item, terminal_manifest=roster.terminal_manifest)
        for item in roster.entries
    ]
    payload = records[0].model_dump(mode="json")
    if mismatch == "pilot":
        payload["pilot_id"] = "pilot_foreign"
    elif mismatch == "project":
        payload["identity"]["project_artifact_id"] = "project_002"
    elif mismatch == "shot":
        payload["identity"]["shot_id"] = "shot_999"
        payload["continuity"]["target_shot_id"] = "shot_999"
    else:
        payload["identity"]["generation_id"] = "generation_wrong"
    records[0] = QualityExperienceRecordV1.model_validate(payload)
    pointers = tuple(store.write_record(record) for record in records)

    with pytest.raises(QualityExperienceIntegrityError):
        api.build_pilot_dataset_index(
            store=store,
            cohort=cohort,
            cohort_pointer=cohort_pointer,
            roster=roster,
            roster_pointer=roster_pointer,
            record_pointers=pointers,
            dataset_purpose="closed Q0 comparison",
            created_at="2026-08-21T12:00:00Z",
            repository_commit="0" * 40,
            coverage_tags=("baseline",),
            known_confounders=(),
        )


@pytest.mark.parametrize("variant", ("duplicate", "extra"))
def test_index_rejects_duplicate_or_extra_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    variant: str,
) -> None:
    api = _dataset_api()
    store, cohort, cohort_pointer, roster = _roster(tmp_path / "production", monkeypatch)
    roster_pointer = store.write_roster(roster)
    pointers = tuple(
        store.write_record(_record_for(item, terminal_manifest=roster.terminal_manifest))
        for item in roster.entries
    )
    if variant == "duplicate":
        candidate_pointers = (*pointers, pointers[0])
    else:
        payload = _record_for(
            roster.entries[0], terminal_manifest=roster.terminal_manifest
        ).model_dump(mode="json")
        payload["identity"]["attempt_id"] = "attempt_extra"
        payload["identity"]["generation_id"] = "generation_extra"
        payload["lineage"]["attempt_sequence"] = len(roster.entries) + 2
        payload["artifact_evidence"]["asset_id"] = "asset_attempt_extra"
        payload["artifact_evidence"]["relative_path"] = "shots/shot_001/attempt_extra.mp4"
        payload["analyzer"]["evidence"][0]["subject_id"] = "asset_attempt_extra"
        extra = store.write_record(QualityExperienceRecordV1.model_validate(payload))
        candidate_pointers = (*pointers, extra)

    with pytest.raises(QualityExperienceIntegrityError):
        api.build_pilot_dataset_index(
            store=store,
            cohort=cohort,
            cohort_pointer=cohort_pointer,
            roster=roster,
            roster_pointer=roster_pointer,
            record_pointers=candidate_pointers,
            dataset_purpose="closed Q0 comparison",
            created_at="2026-08-21T12:00:00Z",
            repository_commit="0" * 40,
            coverage_tags=("baseline",),
            known_confounders=(),
        )


def test_index_accepts_eight_shots_and_multiple_attempts_per_shot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _dataset_api()
    store, cohort, cohort_pointer, roster = _roster(
        tmp_path / "production",
        monkeypatch,
        shot_count=8,
        extra_first_shot_attempt=True,
    )
    roster_pointer = store.write_roster(roster)
    pointers = tuple(
        store.write_record(_record_for(item, terminal_manifest=roster.terminal_manifest))
        for item in roster.entries
    )
    index = api.build_pilot_dataset_index(
        store=store,
        cohort=cohort,
        cohort_pointer=cohort_pointer,
        roster=roster,
        roster_pointer=roster_pointer,
        record_pointers=pointers,
        dataset_purpose="closed Q0 comparison",
        created_at="2026-08-21T12:00:00Z",
        repository_commit="0" * 40,
        coverage_tags=("baseline",),
        known_confounders=(),
    )
    assert len(index.shot_keys) == 8
    assert len(index.entries) == 9
    assert sum(entry.shot_id == "shot_001" for entry in index.entries) == 2


def test_index_rejects_historical_or_lab_only_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _dataset_api()
    store, cohort, cohort_pointer, roster = _roster(tmp_path / "production", monkeypatch)
    roster_pointer = store.write_roster(roster)
    records = [
        _record_for(item, terminal_manifest=roster.terminal_manifest)
        for item in roster.entries
    ]
    payload = records[0].model_dump(mode="json")
    payload["canonical_runtime_boundary"] = "lab_only"
    payload["artifact_evidence"]["boundary"] = "lab"
    records[0] = QualityExperienceRecordV1.model_validate(payload)
    pointers = tuple(store.write_record(item) for item in records)
    with pytest.raises(QualityExperienceIntegrityError):
        api.build_pilot_dataset_index(
            store=store,
            cohort=cohort,
            cohort_pointer=cohort_pointer,
            roster=roster,
            roster_pointer=roster_pointer,
            record_pointers=pointers,
            dataset_purpose="closed Q0 comparison",
            created_at="2026-08-21T12:00:00Z",
            repository_commit="0" * 40,
            coverage_tags=("baseline",),
            known_confounders=(),
        )


def test_exact_lookup_does_not_require_agent_memory_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _dataset_api()
    store, cohort, cohort_pointer, roster = _roster(tmp_path / "production", monkeypatch)
    roster_pointer = store.write_roster(roster)
    pointers = tuple(
        store.write_record(_record_for(item, terminal_manifest=roster.terminal_manifest))
        for item in roster.entries
    )
    index = api.build_pilot_dataset_index(
        store=store,
        cohort=cohort,
        cohort_pointer=cohort_pointer,
        roster=roster,
        roster_pointer=roster_pointer,
        record_pointers=pointers,
        dataset_purpose="closed Q0 comparison",
        created_at="2026-08-21T12:00:00Z",
        repository_commit="0" * 40,
        coverage_tags=("baseline",),
        known_confounders=(),
    )
    pointer = store.write_dataset(index)
    assert not (tmp_path / ".agent" / "memory" / "index").exists()
    assert store.list_dataset_pointers("pilot_a") == (pointer,)
    selected = api.exact_lookup(index, shot_id="shot_003")
    assert selected.shot_id == "shot_003"
    for field in (
        "experiment_id",
        "project_id",
        "scene_id",
        "attempt_id",
        "generation_id",
        "provider_name",
        "provider_kind",
        "profile_id",
        "capability_id",
        "model_id",
        "outcome",
        "human_verdict",
    ):
        expected = getattr(selected, field)
        assert api.exact_lookup(
            index, shot_id="shot_003", **{field: expected}
        ) == selected
        with pytest.raises(QualityExperienceNotFound):
            api.exact_lookup(
                index, shot_id="shot_003", **{field: "definitely_not_a_match"}
            )
    with pytest.raises(QualityExperienceNotFound):
        api.exact_lookup(index, provider_name="missing")
    with pytest.raises(QualityExperienceAmbiguous):
        api.exact_lookup(index, scene_id="scene_001")


def test_dataset_reopen_rejects_projected_field_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _dataset_api()
    store, cohort, cohort_pointer, roster = _roster(tmp_path / "production", monkeypatch)
    roster_pointer = store.write_roster(roster)
    pointers = tuple(
        store.write_record(_record_for(item, terminal_manifest=roster.terminal_manifest))
        for item in roster.entries
    )
    index = api.build_pilot_dataset_index(
        store=store,
        cohort=cohort,
        cohort_pointer=cohort_pointer,
        roster=roster,
        roster_pointer=roster_pointer,
        record_pointers=pointers,
        dataset_purpose="closed Q0 comparison",
        created_at="2026-08-21T12:00:00Z",
        repository_commit="0" * 40,
        coverage_tags=("baseline",),
        known_confounders=(),
    )
    drifted_entry = index.entries[0].model_copy(update={"profile_id": "forged_profile"})
    drifted = index.model_copy(update={"entries": (drifted_entry, *index.entries[1:])})
    with pytest.raises(QualityExperienceIntegrityError):
        store.write_dataset(drifted)


def test_store_rejects_direct_dataset_write_that_omits_roster_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _dataset_api()
    store, cohort, cohort_pointer, roster = _roster(tmp_path / "production", monkeypatch)
    roster_pointer = store.write_roster(roster)
    pointers = tuple(
        store.write_record(_record_for(item, terminal_manifest=roster.terminal_manifest))
        for item in roster.entries
    )
    index = api.build_pilot_dataset_index(
        store=store,
        cohort=cohort,
        cohort_pointer=cohort_pointer,
        roster=roster,
        roster_pointer=roster_pointer,
        record_pointers=pointers,
        dataset_purpose="closed Q0 comparison",
        created_at="2026-08-21T12:00:00Z",
        repository_commit="0" * 40,
        coverage_tags=("baseline",),
        known_confounders=(),
    )
    incomplete = index.model_copy(update={"entries": index.entries[:-1]})

    with pytest.raises(QualityExperienceIntegrityError):
        store.write_dataset(incomplete)
