"""Immutable content-addressed storage for Quality Experience v1 records."""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import secrets
import stat
import unicodedata
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Iterator

from pydantic import ValidationError

from ai_video.quality_intelligence.models import (
    HistoricalImportPointer,
    HistoricalQualityExperienceImportV1,
    PilotAttemptRosterPointer,
    PilotAttemptRosterV1,
    PilotCaptureCohortPointer,
    PilotCaptureCohortV1,
    PilotDatasetIndexV1,
    PilotDatasetPointer,
    QualityExperienceRecordV1,
    QualityRecordPointer,
)


class QualityExperienceError(Exception):
    """Sanitized typed base failure for the advisory Q0 data plane."""

    code = "QUALITY_EXPERIENCE_ERROR"


class QualityExperienceConflict(QualityExperienceError):
    code = "QUALITY_EXPERIENCE_ATTEMPT_CONFLICT"


class QualityExperienceIntegrityError(QualityExperienceError):
    code = "QUALITY_EXPERIENCE_INTEGRITY_INVALID"


class QualityExperienceRootError(QualityExperienceError):
    code = "QUALITY_EXPERIENCE_ROOT_INVALID"


class QualityExperienceNotFound(QualityExperienceError):
    code = "QUALITY_EXPERIENCE_NOT_FOUND"


class QualityExperienceAmbiguous(QualityExperienceError):
    code = "QUALITY_EXPERIENCE_AMBIGUOUS"


def _normalized_json(value: object) -> object:
    if isinstance(value, dict):
        return {key: _normalized_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalized_json(item) for item in value]
    if isinstance(value, str):
        normalized = unicodedata.normalize("NFC", value)
        if normalized != value:
            raise QualityExperienceIntegrityError("integrity verification failed")
        return value
    if isinstance(value, float) and not math.isfinite(value):
        raise QualityExperienceIntegrityError("integrity verification failed")
    return value


def _canonical_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            _normalized_json(payload),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _seal_record(
    record: QualityExperienceRecordV1,
) -> tuple[QualityExperienceRecordV1, bytes, str]:
    try:
        record = QualityExperienceRecordV1.model_validate(record.model_dump(mode="json"))
    except Exception:
        raise QualityExperienceIntegrityError("integrity verification failed") from None
    unsealed = record.model_copy(update={"content_hash": None})
    semantic_payload = unsealed.model_dump(mode="json", exclude={"content_hash"})
    content_hash = hashlib.sha256(_canonical_bytes(semantic_payload)).hexdigest()
    sealed = unsealed.model_copy(update={"content_hash": content_hash})
    final_bytes = _canonical_bytes(sealed.model_dump(mode="json"))
    return sealed, final_bytes, hashlib.sha256(final_bytes).hexdigest()


def _seal_import(
    imported: HistoricalQualityExperienceImportV1,
) -> tuple[HistoricalQualityExperienceImportV1, bytes, str]:
    try:
        imported = HistoricalQualityExperienceImportV1.model_validate(
            imported.model_dump(mode="json")
        )
    except Exception:
        raise QualityExperienceIntegrityError("integrity verification failed") from None
    unsealed = imported.model_copy(update={"content_hash": None})
    content_hash = hashlib.sha256(
        _canonical_bytes(unsealed.model_dump(mode="json", exclude={"content_hash"}))
    ).hexdigest()
    sealed = unsealed.model_copy(update={"content_hash": content_hash})
    final_bytes = _canonical_bytes(sealed.model_dump(mode="json"))
    return sealed, final_bytes, hashlib.sha256(final_bytes).hexdigest()


def _seal_content_model(model):
    try:
        model = type(model).model_validate(model.model_dump(mode="json"))
    except Exception:
        raise QualityExperienceIntegrityError("integrity verification failed") from None
    unsealed = model.model_copy(update={"content_hash": None})
    content_hash = hashlib.sha256(
        _canonical_bytes(unsealed.model_dump(mode="json", exclude={"content_hash"}))
    ).hexdigest()
    sealed = unsealed.model_copy(update={"content_hash": content_hash})
    final_bytes = _canonical_bytes(sealed.model_dump(mode="json"))
    return sealed, final_bytes, hashlib.sha256(final_bytes).hexdigest()


def _clean_pointer_path(pointer: QualityRecordPointer) -> PurePosixPath:
    try:
        checked = QualityRecordPointer.model_validate(pointer.model_dump(mode="json"))
    except ValidationError:
        raise QualityExperienceIntegrityError("integrity verification failed") from None
    relative = PurePosixPath(checked.relative_path)
    expected = PurePosixPath(
        f"records/sha256/{checked.file_sha256[:2]}/{checked.file_sha256}.json"
    )
    if relative != expected:
        raise QualityExperienceIntegrityError("integrity verification failed")
    return relative


def _has_symlink_component(path: Path) -> bool:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if (current.exists() or current.is_symlink()) and current.is_symlink():
            return True
    return False


def _validate_dataset_root(path: Path) -> Path:
    if _has_symlink_component(path):
        raise QualityExperienceRootError("expected an explicit non-Production dataset root")
    absolute = path.absolute()
    parts = absolute.parts
    if any(part in {"state", "assets", "creative", "runs"} for part in parts):
        raise QualityExperienceRootError("expected an explicit non-Production dataset root")
    if any(
        parts[index : index + 3] == (".agent", "memory", "index")
        for index in range(len(parts) - 2)
    ):
        raise QualityExperienceRootError("expected an explicit non-Production dataset root")
    return absolute


def _relative_to_root(root: Path, target: Path) -> Path:
    try:
        return target.absolute().relative_to(root.absolute())
    except ValueError:
        raise QualityExperienceIntegrityError("integrity verification failed") from None


def _ensure_safe_directory(root: Path, target: Path) -> None:
    relative = _relative_to_root(root, target)
    current = root.absolute()
    if current.is_symlink() or not current.is_dir():
        raise QualityExperienceIntegrityError("integrity verification failed")
    for part in relative.parts:
        current /= part
        try:
            current.mkdir()
        except FileExistsError:
            pass
        try:
            mode = os.lstat(current).st_mode
        except OSError:
            raise QualityExperienceIntegrityError("integrity verification failed") from None
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise QualityExperienceIntegrityError("integrity verification failed")


def _require_safe_existing_parent(root: Path, path: Path) -> None:
    relative = _relative_to_root(root, path)
    current = root.absolute()
    for part in relative.parts[:-1]:
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except OSError:
            raise QualityExperienceIntegrityError("integrity verification failed") from None
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise QualityExperienceIntegrityError("integrity verification failed")


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
        raise QualityExperienceIntegrityError("integrity verification failed") from None
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _promote_immutable(root: Path, path: Path, payload: bytes) -> None:
    _ensure_safe_directory(root, path.parent)
    temporary_root = root / ".tmp"
    _ensure_safe_directory(root, temporary_root)
    temporary = temporary_root / f"{path.name}.tmp.{os.getpid()}.{secrets.token_hex(8)}"
    descriptor = -1
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        view = memoryview(payload)
        while view:
            view = view[os.write(descriptor, view) :]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError:
            if _read_regular_nofollow(path) != payload:
                raise QualityExperienceIntegrityError("integrity verification failed")
        _fsync_directory(path.parent)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


class QualityExperienceStore:
    """The sole writer for an explicit non-Production Q0 dataset root."""

    def __init__(self, pilot_dataset_root: Path) -> None:
        dataset_root = _validate_dataset_root(Path(pilot_dataset_root))
        dataset_root.mkdir(parents=True, exist_ok=True)
        self.root = dataset_root / "quality-experience" / "v1"
        _ensure_safe_directory(dataset_root, self.root)
        for directory in (
            self.root / "records" / "sha256",
            self.root / "imports" / "sha256",
            self.root / "cohorts",
            self.root / "rosters",
            self.root / "datasets",
            self.root / ".tmp",
        ):
            _ensure_safe_directory(self.root, directory)
        self._lock_path = self.root / "store.lock"

    @contextmanager
    def _exclusive_lock(self) -> Iterator[None]:
        try:
            _require_safe_existing_parent(self.root, self._lock_path)
            descriptor = os.open(
                self._lock_path,
                os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
        except OSError:
            raise QualityExperienceIntegrityError("integrity verification failed") from None
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def _pointer_for(
        self, record: QualityExperienceRecordV1, file_sha256: str
    ) -> QualityRecordPointer:
        if record.content_hash is None:
            raise QualityExperienceIntegrityError("integrity verification failed")
        return QualityRecordPointer(
            record_kind=record.record_kind,
            schema_version=record.schema_version,
            relative_path=f"records/sha256/{file_sha256[:2]}/{file_sha256}.json",
            content_hash=record.content_hash,
            file_sha256=file_sha256,
            recorded_sequence=record.lineage.attempt_sequence,
            recorded_attempt_id=record.identity.attempt_id,
        )

    def _load_path(
        self, path: Path, pointer: QualityRecordPointer | None = None
    ) -> tuple[QualityExperienceRecordV1, QualityRecordPointer, bytes]:
        try:
            _require_safe_existing_parent(self.root, path)
            raw = _read_regular_nofollow(path)
            file_sha256 = hashlib.sha256(raw).hexdigest()
            record = QualityExperienceRecordV1.model_validate(
                json.loads(raw.decode("utf-8"))
            )
            sealed, canonical, expected_file_hash = _seal_record(record)
            actual_pointer = self._pointer_for(sealed, file_sha256)
            if (
                canonical != raw
                or expected_file_hash != file_sha256
                or record.content_hash != sealed.content_hash
                or path != self.root / actual_pointer.relative_path
                or (pointer is not None and actual_pointer != pointer)
            ):
                raise QualityExperienceIntegrityError("integrity verification failed")
            return record, actual_pointer, raw
        except QualityExperienceIntegrityError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError, ValidationError, ValueError):
            raise QualityExperienceIntegrityError("integrity verification failed") from None

    def _scan_attempt_bindings(
        self,
    ) -> dict[str, tuple[QualityRecordPointer, bytes]]:
        bindings: dict[str, tuple[QualityRecordPointer, bytes]] = {}
        records = self.root / "records" / "sha256"
        _require_safe_existing_parent(self.root, records / ".sentinel")
        for directory, directory_names, file_names in os.walk(records, followlinks=False):
            base = Path(directory)
            if any((base / name).is_symlink() for name in directory_names):
                raise QualityExperienceIntegrityError("integrity verification failed")
            for name in file_names:
                path = base / name
                if path.is_symlink() or path.suffix != ".json":
                    raise QualityExperienceIntegrityError("integrity verification failed")
                record, pointer, raw = self._load_path(path)
                key = record.attempt_identity_key.identity_hash
                previous = bindings.get(key)
                if previous is not None and previous[0] != pointer:
                    raise QualityExperienceIntegrityError("integrity verification failed")
                bindings[key] = (pointer, raw)
        return bindings

    def write_record(
        self, record: QualityExperienceRecordV1
    ) -> QualityRecordPointer:
        sealed, payload, file_sha256 = _seal_record(record)
        pointer = self._pointer_for(sealed, file_sha256)
        key = sealed.attempt_identity_key.identity_hash
        with self._exclusive_lock():
            existing = self._scan_attempt_bindings().get(key)
            if existing is not None:
                if existing[1] == payload:
                    return existing[0]
                raise QualityExperienceConflict("attempt identity conflict")
            path = self.root / pointer.relative_path
            _promote_immutable(self.root, path, payload)
            reopened, reopened_pointer, _ = self._load_path(path, pointer)
            if reopened.content_hash != sealed.content_hash:
                raise QualityExperienceIntegrityError("integrity verification failed")
            return reopened_pointer

    def load_record(self, pointer: QualityRecordPointer) -> QualityExperienceRecordV1:
        try:
            relative = _clean_pointer_path(pointer)
            record, _, _ = self._load_path(self.root / relative, pointer)
            return record
        except QualityExperienceIntegrityError:
            raise
        except Exception:
            raise QualityExperienceIntegrityError("integrity verification failed") from None

    def get_by_record_sha256(
        self, file_sha256: str
    ) -> tuple[QualityRecordPointer, QualityExperienceRecordV1]:
        if len(file_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in file_sha256
        ):
            raise QualityExperienceIntegrityError("record hash is invalid")
        path = self.root / "records" / "sha256" / file_sha256[:2] / f"{file_sha256}.json"
        if not path.exists():
            raise QualityExperienceNotFound("record hash was not found")
        record, pointer, _ = self._load_path(path)
        return pointer, record

    def write_import(
        self, imported: HistoricalQualityExperienceImportV1
    ) -> HistoricalImportPointer:
        sealed, payload, file_sha256 = _seal_import(imported)
        if sealed.content_hash is None:
            raise QualityExperienceIntegrityError("integrity verification failed")
        pointer = HistoricalImportPointer(
            schema_version=sealed.schema_version,
            relative_path=f"imports/sha256/{file_sha256[:2]}/{file_sha256}.json",
            content_hash=sealed.content_hash,
            file_sha256=file_sha256,
        )
        with self._exclusive_lock():
            path = self.root / pointer.relative_path
            _promote_immutable(self.root, path, payload)
            reopened = self.load_import(pointer)
            if reopened.content_hash != sealed.content_hash:
                raise QualityExperienceIntegrityError("integrity verification failed")
        return pointer

    def load_import(
        self, pointer: HistoricalImportPointer
    ) -> HistoricalQualityExperienceImportV1:
        try:
            checked = HistoricalImportPointer.model_validate(
                pointer.model_dump(mode="json")
            )
            expected = PurePosixPath(
                f"imports/sha256/{checked.file_sha256[:2]}/{checked.file_sha256}.json"
            )
            if PurePosixPath(checked.relative_path) != expected:
                raise QualityExperienceIntegrityError("integrity verification failed")
            path = self.root / expected
            _require_safe_existing_parent(self.root, path)
            raw = _read_regular_nofollow(path)
            if hashlib.sha256(raw).hexdigest() != checked.file_sha256:
                raise QualityExperienceIntegrityError("integrity verification failed")
            imported = HistoricalQualityExperienceImportV1.model_validate(
                json.loads(raw.decode("utf-8"))
            )
            sealed, canonical, expected_file_hash = _seal_import(imported)
            if (
                canonical != raw
                or expected_file_hash != checked.file_sha256
                or sealed.content_hash != checked.content_hash
                or imported.content_hash != checked.content_hash
            ):
                raise QualityExperienceIntegrityError("integrity verification failed")
            return imported
        except QualityExperienceIntegrityError:
            raise
        except Exception:
            raise QualityExperienceIntegrityError("integrity verification failed") from None

    def _write_named_content(self, model, *, directory: str, name: str, pointer_type):
        sealed, payload, file_sha256 = _seal_content_model(model)
        if sealed.content_hash is None:
            raise QualityExperienceIntegrityError("integrity verification failed")
        relative_path = f"{directory}/{sealed.pilot_id}/{name}.{file_sha256}.json"
        pointer = pointer_type(
            schema_version=sealed.schema_version,
            pilot_id=sealed.pilot_id,
            relative_path=relative_path,
            content_hash=sealed.content_hash,
            file_sha256=file_sha256,
        )
        with self._exclusive_lock():
            path = self.root / relative_path
            _promote_immutable(self.root, path, payload)
            reopened = self._load_named_content(
                pointer,
                directory=directory,
                name=name,
                model_type=type(sealed),
                pointer_type=pointer_type,
            )
            if reopened.content_hash != sealed.content_hash:
                raise QualityExperienceIntegrityError("integrity verification failed")
        return pointer

    def _load_named_content(
        self,
        pointer,
        *,
        directory: str,
        name: str,
        model_type,
        pointer_type,
    ):
        try:
            checked = pointer_type.model_validate(pointer.model_dump(mode="json"))
            expected = PurePosixPath(
                f"{directory}/{checked.pilot_id}/{name}.{checked.file_sha256}.json"
            )
            if PurePosixPath(checked.relative_path) != expected:
                raise QualityExperienceIntegrityError("integrity verification failed")
            path = self.root / expected
            _require_safe_existing_parent(self.root, path)
            raw = _read_regular_nofollow(path)
            if hashlib.sha256(raw).hexdigest() != checked.file_sha256:
                raise QualityExperienceIntegrityError("integrity verification failed")
            model = model_type.model_validate(json.loads(raw.decode("utf-8")))
            sealed, canonical, expected_file_hash = _seal_content_model(model)
            if (
                canonical != raw
                or expected_file_hash != checked.file_sha256
                or sealed.content_hash != checked.content_hash
                or model.content_hash != checked.content_hash
                or model.pilot_id != checked.pilot_id
            ):
                raise QualityExperienceIntegrityError("integrity verification failed")
            return model
        except QualityExperienceIntegrityError:
            raise
        except Exception:
            raise QualityExperienceIntegrityError("integrity verification failed") from None

    def write_cohort(
        self, cohort: PilotCaptureCohortV1
    ) -> PilotCaptureCohortPointer:
        return self._write_named_content(
            cohort,
            directory="cohorts",
            name="cohort",
            pointer_type=PilotCaptureCohortPointer,
        )

    def load_cohort(
        self, pointer: PilotCaptureCohortPointer
    ) -> PilotCaptureCohortV1:
        return self._load_named_content(
            pointer,
            directory="cohorts",
            name="cohort",
            model_type=PilotCaptureCohortV1,
            pointer_type=PilotCaptureCohortPointer,
        )

    def write_roster(
        self, roster: PilotAttemptRosterV1
    ) -> PilotAttemptRosterPointer:
        return self._write_named_content(
            roster,
            directory="rosters",
            name="roster",
            pointer_type=PilotAttemptRosterPointer,
        )

    def load_roster(
        self, pointer: PilotAttemptRosterPointer
    ) -> PilotAttemptRosterV1:
        roster = self._load_named_content(
            pointer,
            directory="rosters",
            name="roster",
            model_type=PilotAttemptRosterV1,
            pointer_type=PilotAttemptRosterPointer,
        )
        cohort = self.load_cohort(roster.cohort)
        if cohort.pilot_id != roster.pilot_id:
            raise QualityExperienceIntegrityError("integrity verification failed")
        return roster

    def write_dataset(self, index: PilotDatasetIndexV1) -> PilotDatasetPointer:
        try:
            checked = PilotDatasetIndexV1.model_validate(index.model_dump(mode="json"))
        except Exception:
            raise QualityExperienceIntegrityError("integrity verification failed") from None
        self._validate_dataset_closure(checked)
        return self._write_named_content(
            checked,
            directory="datasets",
            name="index",
            pointer_type=PilotDatasetPointer,
        )

    def load_dataset(self, pointer: PilotDatasetPointer) -> PilotDatasetIndexV1:
        index = self._load_named_content(
            pointer,
            directory="datasets",
            name="index",
            model_type=PilotDatasetIndexV1,
            pointer_type=PilotDatasetPointer,
        )
        self._validate_dataset_closure(index)
        return index

    def _validate_dataset_closure(self, index: PilotDatasetIndexV1) -> None:
        cohort = self.load_cohort(index.cohort)
        roster = self.load_roster(index.roster)
        if (
            roster.cohort != index.cohort
            or cohort.pilot_id != index.pilot_id
            or roster.pilot_id != index.pilot_id
            or cohort.shot_keys != index.shot_keys
            or cohort.rubric_id != index.rubric_id
            or cohort.rubric_version != index.rubric_version
            or cohort.rubric_hash != index.rubric_hash
            or cohort.capture_contract_version != index.capture_contract_version
        ):
            raise QualityExperienceIntegrityError("integrity verification failed")
        roster_by_key = {
            item.attempt_identity_key.identity_hash: item for item in roster.entries
        }
        record_keys: list[str] = []
        for entry in index.entries:
            record = self.load_record(entry.record)
            record_key = record.attempt_identity_key.identity_hash
            record_keys.append(record_key)
            roster_entry = roster_by_key.get(record_key)
            if roster_entry is None:
                raise QualityExperienceIntegrityError("integrity verification failed")
            model_id = record.provider.model_id.value
            coverage = tuple(
                sorted(
                    {
                        f"outcome:{record.outcome.variant}",
                        f"provider:{record.provider.kind}",
                        f"runtime:{record.canonical_runtime_boundary.value}",
                    }
                )
            )
            if (
                record.experiment_id != entry.experiment_id
                or record.pilot_id != entry.pilot_id
                or record.pilot_id != cohort.pilot_id
                or record.canonical_runtime_boundary.value != "production_manifest"
                or record.identity.project_artifact_id != entry.project_id
                or record.identity.scene_id != entry.scene_id
                or record.identity.shot_id != entry.shot_id
                or record.identity.attempt_id != entry.attempt_id
                or record.identity.generation_id != entry.generation_id
                or record.lineage.attempt_sequence != entry.attempt_sequence
                or record.provider.name != entry.provider_name
                or record.provider.kind != entry.provider_kind
                or record.provider.profile_id != entry.profile_id
                or record.provider.capability_id != entry.capability_id
                or model_id != entry.model_id
                or record.outcome.variant != entry.outcome
                or record.human_review.status != entry.human_verdict
                or coverage != entry.coverage_tags
                or record.identity.project_artifact_id
                != roster_entry.shot.project_id
                or record.identity.scene_id != roster_entry.shot.scene_id
                or record.identity.shot_id != roster_entry.shot.shot_id
                or record.identity.shot_revision != roster_entry.shot_revision
                or record.identity.shot_content_hash != roster_entry.shot_content_hash
                or record.identity.attempt_id
                != roster_entry.attempt_identity_key.attempt_id
                or record.identity.generation_id
                != roster_entry.attempt_identity_key.generation_id
                or record.lineage.attempt_sequence != roster_entry.attempt_sequence
                or record.identity.manifest_observation_revision
                != roster.terminal_manifest.manifest_revision
                or record.identity.manifest_observation_file_hash
                != roster.terminal_manifest.file_sha256
            ):
                raise QualityExperienceIntegrityError("integrity verification failed")
        roster_keys = [
            item.attempt_identity_key.identity_hash for item in roster.entries
        ]
        if (
            len(record_keys) != len(set(record_keys))
            or set(record_keys) != set(roster_keys)
            or {
                (entry.project_id, entry.scene_id, entry.shot_id)
                for entry in index.entries
            }
            != {shot.sort_key for shot in cohort.shot_keys}
        ):
            raise QualityExperienceIntegrityError("integrity verification failed")

    def list_dataset_pointers(self, pilot_id: str) -> tuple[PilotDatasetPointer, ...]:
        directory = self.root / "datasets" / pilot_id
        if not directory.exists():
            return ()
        _require_safe_existing_parent(self.root, directory / ".sentinel")
        if directory.is_symlink() or not directory.is_dir():
            raise QualityExperienceIntegrityError("integrity verification failed")
        pointers: list[PilotDatasetPointer] = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.is_symlink() or not path.name.startswith("index.") or path.suffix != ".json":
                raise QualityExperienceIntegrityError("integrity verification failed")
            file_sha256 = path.name.removeprefix("index.").removesuffix(".json")
            raw = _read_regular_nofollow(path)
            try:
                index = PilotDatasetIndexV1.model_validate_json(raw)
            except Exception:
                raise QualityExperienceIntegrityError("integrity verification failed") from None
            if index.content_hash is None:
                raise QualityExperienceIntegrityError("integrity verification failed")
            pointer = PilotDatasetPointer(
                schema_version=index.schema_version,
                pilot_id=pilot_id,
                relative_path=f"datasets/{pilot_id}/{path.name}",
                content_hash=index.content_hash,
                file_sha256=file_sha256,
            )
            self.load_dataset(pointer)
            pointers.append(pointer)
        return tuple(pointers)
