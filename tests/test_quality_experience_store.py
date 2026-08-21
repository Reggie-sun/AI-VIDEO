"""T2/T3 tests for the immutable Quality Experience v1 store."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
from pathlib import Path

import pytest

from ai_video.quality_intelligence.models import (
    ArtifactEvidenceNotPresent,
    BoundedFreeText,
    QualityExperienceRecordV1,
    QualityRecordPointer,
)
from ai_video.quality_intelligence import models as quality_models


from ai_video.quality_intelligence.store import (
    QualityExperienceConflict,
    QualityExperienceIntegrityError,
    QualityExperienceRootError,
    QualityExperienceStore,
)


FIXTURES = Path(__file__).parent / "fixtures" / "quality_experience" / "v1"


def _record(name: str = "prospective_success.json") -> QualityExperienceRecordV1:
    return QualityExperienceRecordV1.model_validate(
        json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    )


def _historical_model():
    model = getattr(quality_models, "HistoricalQualityExperienceImportV1", None)
    if model is None:
        pytest.fail("historical import behavior is not implemented")
    return model


def _process_write(root: str, purpose: str, queue: multiprocessing.Queue) -> None:
    try:
        store = QualityExperienceStore(Path(root))
        record = _record().model_copy(update={"purpose": BoundedFreeText(value=purpose)})
        pointer = store.write_record(record)
        queue.put(("ok", pointer.file_sha256))
    except QualityExperienceConflict:
        queue.put(("conflict", None))


def test_store_writes_content_addressed_record_and_reopens_exactly(tmp_path: Path) -> None:
    store = QualityExperienceStore(tmp_path / "dataset")
    pointer = store.write_record(_record())

    path = store.root / pointer.relative_path
    raw = path.read_bytes()
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    assert hashlib.sha256(raw).hexdigest() == pointer.file_sha256
    assert pointer.relative_path == (
        f"records/sha256/{pointer.file_sha256[:2]}/{pointer.file_sha256}.json"
    )
    assert store.load_record(pointer) == _record().model_copy(
        update={"content_hash": pointer.content_hash}
    )


def test_store_replay_is_zero_write(tmp_path: Path) -> None:
    store = QualityExperienceStore(tmp_path / "dataset")
    first = store.write_record(_record())
    path = store.root / first.relative_path
    before = path.stat().st_mtime_ns

    second = store.write_record(_record())

    assert second == first
    assert path.stat().st_mtime_ns == before
    assert len(list((store.root / "records").rglob("*.json"))) == 1


def test_same_attempt_with_different_bytes_is_typed_conflict(tmp_path: Path) -> None:
    store = QualityExperienceStore(tmp_path / "dataset")
    store.write_record(_record())
    changed = _record().model_copy(
        update={"purpose": BoundedFreeText(value="a different bounded purpose")}
    )

    with pytest.raises(QualityExperienceConflict, match="attempt identity conflict"):
        store.write_record(changed)


def test_store_revalidates_model_copy_before_sealing(tmp_path: Path) -> None:
    store = QualityExperienceStore(tmp_path / "dataset")
    invalid = _record().model_copy(
        update={
            "artifact_evidence": ArtifactEvidenceNotPresent(
                state="not_present", reason_code="forged"
            )
        }
    )

    with pytest.raises(QualityExperienceIntegrityError):
        store.write_record(invalid)


def test_q0_store_does_not_invoke_provider_analyzer_recovery_or_activation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_generation import VideoGenerationService

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Q0 passive capture invoked a Production side effect")

    for name in ("recover", "run_review_analysis", "activate_video_candidate"):
        monkeypatch.setattr(ProductionStateCommitter, name, forbidden)
    for name in ("submit_once", "fetch_once", "fetch_and_activate"):
        monkeypatch.setattr(VideoGenerationService, name, forbidden)

    store = QualityExperienceStore(tmp_path / "dataset")
    pointer = store.write_record(_record())
    assert store.load_record(pointer).identity.attempt_id == "attempt_001"


def test_store_lock_serializes_cross_process_conflict(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    ctx = multiprocessing.get_context("fork")
    queue = ctx.Queue()
    workers = [
        ctx.Process(target=_process_write, args=(str(dataset), purpose, queue))
        for purpose in ("first process purpose", "second process purpose")
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=10)
        assert worker.exitcode == 0

    results = sorted(queue.get(timeout=2)[0] for _ in workers)
    assert results == ["conflict", "ok"]
    assert len(list((dataset / "quality-experience/v1/records").rglob("*.json"))) == 1


def test_tampered_record_fails_exact_reopen(tmp_path: Path) -> None:
    store = QualityExperienceStore(tmp_path / "dataset")
    pointer = store.write_record(_record())
    path = store.root / pointer.relative_path
    path.write_bytes(path.read_bytes().replace(b"pilot_a", b"pilot_b"))

    with pytest.raises(QualityExperienceIntegrityError, match="integrity verification failed"):
        store.load_record(pointer)


def test_symlink_record_fails_closed(tmp_path: Path) -> None:
    store = QualityExperienceStore(tmp_path / "dataset")
    pointer = store.write_record(_record())
    path = store.root / pointer.relative_path
    target = tmp_path / "copy.json"
    target.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(target)

    with pytest.raises(QualityExperienceIntegrityError, match="integrity verification failed"):
        store.load_record(pointer)


def test_pointer_traversal_fails_closed(tmp_path: Path) -> None:
    store = QualityExperienceStore(tmp_path / "dataset")
    pointer = store.write_record(_record())
    unsafe = pointer.model_copy(update={"relative_path": "../outside.json"})

    with pytest.raises(QualityExperienceIntegrityError, match="integrity verification failed"):
        store.load_record(unsafe)


@pytest.mark.parametrize(
    "relative",
    ("state", "assets", "creative", "runs", ".agent/memory/index"),
)
def test_store_rejects_production_or_derived_roots(
    tmp_path: Path, relative: str
) -> None:
    with pytest.raises(QualityExperienceRootError, match="non-Production dataset root"):
        QualityExperienceStore(tmp_path / relative)


def test_store_rejects_symlink_dataset_root(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "dataset"
    link.symlink_to(real, target_is_directory=True)

    with pytest.raises(QualityExperienceRootError, match="non-Production dataset root"):
        QualityExperienceStore(link)


def test_store_rejects_nested_record_parent_symlink(tmp_path: Path) -> None:
    store = QualityExperienceStore(tmp_path / "dataset")
    sha_root = store.root / "records" / "sha256"
    sha_root.rmdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    sha_root.symlink_to(outside, target_is_directory=True)

    with pytest.raises(QualityExperienceIntegrityError):
        store.write_record(_record())
    assert list(outside.rglob("*")) == []


def test_store_rejects_nested_pilot_parent_symlink(tmp_path: Path) -> None:
    from ai_video.quality_intelligence.models import PilotCaptureCohortV1

    store = QualityExperienceStore(tmp_path / "dataset")
    outside = tmp_path / "outside"
    outside.mkdir()
    (store.root / "cohorts" / "pilot_a").symlink_to(
        outside, target_is_directory=True
    )
    cohort = PilotCaptureCohortV1.model_validate_json(
        (FIXTURES / "pilot_cohort.json").read_bytes()
    )

    with pytest.raises(QualityExperienceIntegrityError):
        store.write_cohort(cohort)
    assert list(outside.rglob("*")) == []


def test_store_rejects_nested_import_parent_symlink(tmp_path: Path) -> None:
    store = QualityExperienceStore(tmp_path / "dataset")
    sha_root = store.root / "imports" / "sha256"
    sha_root.rmdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    sha_root.symlink_to(outside, target_is_directory=True)
    historical = _historical_model().model_validate(
        json.loads((FIXTURES / "legacy_incomplete.json").read_text())
    )

    with pytest.raises(QualityExperienceIntegrityError):
        store.write_import(historical)
    assert list(outside.rglob("*")) == []


def test_post_promotion_temp_orphan_does_not_hide_attempt_binding(
    tmp_path: Path,
) -> None:
    store = QualityExperienceStore(tmp_path / "dataset")
    pointer = store.write_record(_record())
    final_path = store.root / pointer.relative_path
    orphan = store.root / ".tmp" / f"{final_path.name}.tmp.1234.deadbeef"
    orphan.write_bytes(final_path.read_bytes())

    assert QualityExperienceStore(tmp_path / "dataset").write_record(_record()) == pointer


def test_store_never_writes_outside_explicit_dataset_root(tmp_path: Path) -> None:
    production = tmp_path / "production"
    (production / "state").mkdir(parents=True)
    marker = production / "state" / "manifest.json"
    marker.write_text("unchanged\n", encoding="utf-8")
    before = (marker.read_bytes(), marker.stat().st_mtime_ns)

    store = QualityExperienceStore(tmp_path / "dataset")
    store.write_record(_record())

    assert (marker.read_bytes(), marker.stat().st_mtime_ns) == before
    assert store.root == (tmp_path / "dataset" / "quality-experience/v1").resolve()


def test_legacy_incomplete_fixture_preserves_tagged_evidence() -> None:
    historical = _historical_model().model_validate(
        json.loads((FIXTURES / "legacy_incomplete.json").read_text(encoding="utf-8"))
    )
    states = {item.field_name: item.evidence.state.value for item in historical.fields}
    assert states == {
        "effective_seed": "unknown",
        "human_verdict": "incomplete",
        "paid_cost": "not_applicable",
        "provider_name": "known",
    }


def test_historical_known_field_requires_exact_source_span() -> None:
    payload = json.loads((FIXTURES / "legacy_incomplete.json").read_text())
    known = next(item for item in payload["fields"] if item["field_name"] == "provider_name")
    known["evidence"].pop("source_span")
    with pytest.raises(Exception):
        _historical_model().model_validate(payload)


def test_historical_fields_reject_unsorted_or_duplicate_names() -> None:
    payload = json.loads((FIXTURES / "legacy_incomplete.json").read_text())
    payload["fields"] = [payload["fields"][3], payload["fields"][0]]
    with pytest.raises(Exception):
        _historical_model().model_validate(payload)


def test_historical_import_cannot_become_prospective_record() -> None:
    historical = _historical_model().model_validate(
        json.loads((FIXTURES / "legacy_incomplete.json").read_text())
    )
    assert historical.record_kind == "historical_quality_experience_import"
    assert not hasattr(historical, "attempt_identity_key")
    assert not hasattr(historical, "to_prospective_record")


def test_store_writes_and_reopens_historical_import(tmp_path: Path) -> None:
    store = QualityExperienceStore(tmp_path / "dataset")
    assert hasattr(store, "write_import") and hasattr(store, "load_import")
    historical = _historical_model().model_validate(
        json.loads((FIXTURES / "legacy_incomplete.json").read_text())
    )
    pointer = store.write_import(historical)
    assert pointer.relative_path == (
        f"imports/sha256/{pointer.file_sha256[:2]}/{pointer.file_sha256}.json"
    )
    assert store.load_import(pointer) == historical.model_copy(
        update={"content_hash": pointer.content_hash}
    )
