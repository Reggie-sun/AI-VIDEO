from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    ProductionManifest,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)
from ai_video.production.state_commit import (
    CommitPhase,
    NoopCrashInjector,
    PreparedArtifact,
    ProductionStateCommitter,
    StateCommitRequest,
    _NativeFileOps,
    _canonical_json_bytes,
    _canonical_yaml_bytes,
    _owned_temp_name,
)


ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64


class _RecordingHandle:
    def __init__(self, events: list[str], display_path: str) -> None:
        self._events = events
        self._display_path = display_path

    def __enter__(self) -> "_RecordingHandle":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def write(self, payload: bytes) -> int:
        self._events.append(f"write:{self._display_path}")
        return len(payload)

    def flush(self) -> None:
        self._events.append(f"flush:{self._display_path}")

    def fileno(self) -> int:
        return 1


class RecordingFileOps:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.events: list[str] = []

    def _display(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def open_exclusive(self, path: Path) -> _RecordingHandle:
        return _RecordingHandle(self.events, self._display(path))

    def fsync_file(self, handle: object, path: Path) -> None:
        self.events.append(f"fsync_file:{self._display(path)}")

    def replace(self, source: Path, destination: Path) -> None:
        self.events.append(f"replace:{self._display(source)}->{self._display(destination)}")

    def fsync_directory(self, path: Path) -> None:
        self.events.append(f"fsync_dir:{self._display(path)}")

    def mkdir(self, path: Path) -> bool:
        if path.exists():
            return False
        path.mkdir()
        return True


class _RecordingNativeHandle:
    def __init__(self, events: list[str], display_path: str, handle: object) -> None:
        self._events = events
        self._display_path = display_path
        self._handle = handle

    def __enter__(self) -> "_RecordingNativeHandle":
        self._handle.__enter__()
        return self

    def __exit__(self, *args: object) -> None:
        self._handle.__exit__(*args)

    def write(self, payload: bytes) -> int:
        self._events.append(f"write:{self._display_path}")
        return self._handle.write(payload)

    def flush(self) -> None:
        self._events.append(f"flush:{self._display_path}")
        self._handle.flush()

    def fileno(self) -> int:
        return self._handle.fileno()


class RecordingNativeFileOps:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.events: list[str] = []
        self._native = _NativeFileOps()

    def _display(self, path: Path) -> str:
        relative = path.relative_to(self.root)
        return relative.as_posix() if relative != Path(".") else "."

    def mkdir(self, path: Path) -> bool:
        created = self._native.mkdir(path)
        if created:
            self.events.append(f"mkdir:{self._display(path)}")
        return created

    def open_exclusive(self, path: Path) -> _RecordingNativeHandle:
        self.events.append(f"open:{self._display(path)}")
        return _RecordingNativeHandle(
            self.events, self._display(path), self._native.open_exclusive(path)
        )

    def fsync_file(self, handle: object, path: Path) -> None:
        self.events.append(f"fsync_file:{self._display(path)}")
        self._native.fsync_file(handle, path)

    def replace(self, source: Path, destination: Path) -> None:
        self.events.append(f"replace:{self._display(source)}->{self._display(destination)}")
        self._native.replace(source, destination)

    def fsync_directory(self, path: Path) -> None:
        self.events.append(f"fsync_dir:{self._display(path)}")
        self._native.fsync_directory(path)

    def stat(self, path: Path) -> object:
        self.events.append(f"stat:{self._display(path)}")
        return path.stat()

    def link(self, source: Path, destination: Path) -> None:
        self.events.append(f"link:{self._display(source)}->{self._display(destination)}")
        self._native.link(source, destination)

    def sha256_file(self, path: Path) -> str:
        self.events.append(f"sha:{self._display(path)}")
        return self._native.sha256_file(path)

    def unlink(self, path: Path, *, missing_ok: bool = False) -> None:
        self.events.append(f"unlink:{self._display(path)}")
        self._native.unlink(path, missing_ok=missing_ok)


class CorruptingRecordingNativeFileOps(RecordingNativeFileOps):
    def link(self, source: Path, destination: Path) -> None:
        super().link(source, destination)
        destination.write_bytes(b"corrupt")


class FailingFirstParentFsyncOps(RecordingNativeFileOps):
    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self._fail_next_root_fsync = True

    def fsync_directory(self, path: Path) -> None:
        self.events.append(f"fsync_dir:{self._display(path)}")
        if path == self.root and self._fail_next_root_fsync:
            self._fail_next_root_fsync = False
            raise OSError("injected parent fsync failure")
        self._native.fsync_directory(path)


class FailingLinkedParentFsyncOps(RecordingNativeFileOps):
    def __init__(self, root: Path, linked_parent: Path) -> None:
        super().__init__(root)
        self._linked_parent = linked_parent
        self._fail_once = True

    def fsync_directory(self, path: Path) -> None:
        self.events.append(f"fsync_dir:{self._display(path)}")
        if path == self._linked_parent and self._fail_once:
            self._fail_once = False
            raise OSError("injected linked-parent fsync failure")
        self._native.fsync_directory(path)


class _FakeFcntl:
    LOCK_EX = 1
    LOCK_NB = 2
    LOCK_UN = 8

    def __init__(self, *, busy: bool = False, unlock_error: bool = False) -> None:
        self.busy = busy
        self.unlock_error = unlock_error
        self.calls: list[int] = []

    def flock(self, descriptor: int, operation: int) -> None:
        self.calls.append(operation)
        if operation == self.LOCK_EX | self.LOCK_NB and self.busy:
            raise BlockingIOError("injected busy lock")
        if operation == self.LOCK_UN and self.unlock_error:
            raise OSError("injected unlock failure")


class _FakeLockHandle:
    def __init__(self, *, close_error: bool = False) -> None:
        self.close_error = close_error
        self.closed = False

    def fileno(self) -> int:
        return 7

    def close(self) -> None:
        self.closed = True
        if self.close_error:
            raise OSError("injected close failure")


class _SwapStateAfterManifestFsync:
    def __init__(self, root: Path, outside: Path) -> None:
        self.root = root
        self.outside = outside

    def checkpoint(self, phase: CommitPhase) -> None:
        if phase is CommitPhase.AFTER_MANIFEST_FILE_FSYNC:
            temp_path = self.root / "state/.p2a-manifest.tmp"
            temp_path.unlink()
            (self.root / "state").rmdir()
            (self.root / "state").symlink_to(self.outside, target_is_directory=True)
            (self.outside / temp_path.name).write_bytes(b"external state temp")


class _SwapArtifactParentAfterFileFsync:
    def __init__(self, root: Path, outside: Path) -> None:
        self.root = root
        self.outside = outside

    def checkpoint(self, phase: CommitPhase) -> None:
        if phase is CommitPhase.AFTER_ARTIFACT_FILE_FSYNC:
            temp_path = next((self.root / "creative").glob(".p2a-*.tmp"))
            temp_path.unlink()
            (self.root / "creative").rmdir()
            (self.root / "creative").symlink_to(self.outside, target_is_directory=True)
            (self.outside / temp_path.name).write_bytes(b"external artifact temp")


def make_manifest() -> ProductionManifest:
    return ProductionManifest(
        project_id="comic-demo",
        manifest_revision=1,
        active_project=ProjectSnapshotPointer(
            path=Path("project.yaml"),
            revision=1,
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        ),
        active_registry=RegistrySnapshotPointer(
            path=Path(f"assets/registry.{ZERO_HASH}.json"),
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        ),
    )


def make_committer(
    tmp_path: Path, ops: object | None = None, injector: object | None = None
) -> ProductionStateCommitter:
    return ProductionStateCommitter(tmp_path, file_ops=ops, crash_injector=injector)


def test_commit_contract_types_are_frozen_and_expose_all_phases() -> None:
    artifact = PreparedArtifact(Path("creative/brief.yaml"), b"brief", "x" * 64)
    request = StateCommitRequest(
        attempt_id="attempt-1",
        operation="commit_project_registry",
        expected_manifest_revision=1,
        artifacts=(artifact,),
        next_project=make_manifest().active_project,
        next_registry=make_manifest().active_registry,
    )

    assert request.artifacts == (artifact,)
    with pytest.raises(AttributeError):
        request.operation = "other"  # type: ignore[misc]
    assert tuple(CommitPhase) == (
        CommitPhase.AFTER_ATTEMPT_STARTED,
        CommitPhase.AFTER_ARTIFACT_TEMP_WRITE,
        CommitPhase.AFTER_ARTIFACT_FILE_FSYNC,
        CommitPhase.AFTER_ARTIFACT_PROMOTION,
        CommitPhase.AFTER_ARTIFACT_DIRECTORY_FSYNC,
        CommitPhase.AFTER_ARTIFACT_VERIFICATION,
        CommitPhase.AFTER_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_MANIFEST_FILE_FSYNC,
        CommitPhase.AFTER_MANIFEST_REPLACE,
        CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC,
    )
    assert NoopCrashInjector().checkpoint(CommitPhase.AFTER_ATTEMPT_STARTED) is None


def test_atomic_manifest_write_orders_file_and_directory_durability(tmp_path: Path) -> None:
    (tmp_path / "state").mkdir()
    ops = RecordingFileOps(tmp_path)
    writer = make_committer(tmp_path, ops)

    writer._write_manifest_atomic(make_manifest())

    assert ops.events == [
        "fsync_dir:.",
        "fsync_dir:.",
        "write:state/.p2a-manifest.tmp",
        "flush:state/.p2a-manifest.tmp",
        "fsync_file:state/.p2a-manifest.tmp",
        "fsync_dir:.",
        "replace:state/.p2a-manifest.tmp->state/manifest.json",
        "fsync_dir:state",
    ]


def test_first_state_directory_creation_fsyncs_project_root_before_manifest_write(
    tmp_path: Path,
) -> None:
    ops = RecordingNativeFileOps(tmp_path)

    make_committer(tmp_path, ops)._write_manifest_atomic(make_manifest())

    assert ops.events[:2] == ["mkdir:state", "fsync_dir:."]


def test_existing_directory_retries_parent_fsync_after_prior_creation_failure(
    tmp_path: Path,
) -> None:
    ops = FailingFirstParentFsyncOps(tmp_path)
    writer = make_committer(tmp_path, ops)
    composition = tmp_path / "composition"

    with pytest.raises(AiVideoError) as exc:
        writer._ensure_parent_directory(composition)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert composition.is_dir()
    assert ops.events == ["mkdir:composition", "fsync_dir:."]

    writer._ensure_parent_directory(composition)

    assert ops.events == [
        "mkdir:composition",
        "fsync_dir:.",
        "fsync_dir:.",
    ]


def test_canonical_serialization_is_sort_stable_and_uses_required_newlines() -> None:
    manifest = make_manifest()

    assert _canonical_json_bytes(manifest) == (
        b'{"active_project":{"content_hash":"0000000000000000000000000000000000000000000000000000000000000000",'
        b'"file_sha256":"1111111111111111111111111111111111111111111111111111111111111111",'
        b'"path":"project.yaml","revision":1},"active_registry":{"content_hash":"0000000000000000000000000000000000000000000000000000000000000000",'
        b'"file_sha256":"1111111111111111111111111111111111111111111111111111111111111111",'
        b'"path":"assets/registry.0000000000000000000000000000000000000000000000000000000000000000.json",'
        b'"revision_id":"0000000000000000000000000000000000000000000000000000000000000000"},'
        b'"attempts":[],"manifest_revision":1,"project_id":"comic-demo","schema_version":"2.0"}\n'
    )
    assert _canonical_yaml_bytes(manifest) == (
        b"active_project:\n"
        b"  content_hash: '0000000000000000000000000000000000000000000000000000000000000000'\n"
        b"  file_sha256: '1111111111111111111111111111111111111111111111111111111111111111'\n"
        b"  path: project.yaml\n"
        b"  revision: 1\n"
        b"active_registry:\n"
        b"  content_hash: '0000000000000000000000000000000000000000000000000000000000000000'\n"
        b"  file_sha256: '1111111111111111111111111111111111111111111111111111111111111111'\n"
        b"  path: assets/registry.0000000000000000000000000000000000000000000000000000000000000000.json\n"
        b"  revision_id: '0000000000000000000000000000000000000000000000000000000000000000'\n"
        b"attempts: []\n"
        b"manifest_revision: 1\n"
        b"project_id: comic-demo\n"
        b"schema_version: '2.0'\n"
    )


def test_prepare_artifact_computes_sha256_from_payload(tmp_path: Path) -> None:
    artifact = make_committer(tmp_path).prepare_artifact(
        attempt_id="attempt-1",
        relative_path=Path("creative/brief.yaml"),
        payload=b"authoritative payload",
    )

    assert artifact.file_sha256 == hashlib.sha256(b"authoritative payload").hexdigest()
    assert artifact.payload == b"authoritative payload"


@pytest.mark.parametrize(
    "relative_path",
    [
        Path(""),
        Path("."),
        Path("/tmp/escape.yaml"),
        Path("creative/../escape.yaml"),
        Path("state/manifest.json"),
        Path("state/commit.lock"),
        Path("runs/forbidden.yaml"),
        Path(".workflow/forbidden.yaml"),
    ],
)
def test_prepare_artifact_rejects_unsafe_or_reserved_targets(
    tmp_path: Path, relative_path: Path
) -> None:
    with pytest.raises(AiVideoError) as exc:
        make_committer(tmp_path).prepare_artifact(
            attempt_id="attempt-1", relative_path=relative_path, payload=b"forbidden"
        )

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_prepare_artifact_rejects_symlink_component_and_containment_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / "creative").symlink_to(outside, target_is_directory=True)

    with pytest.raises(AiVideoError, match="symlink") as exc:
        make_committer(tmp_path).prepare_artifact(
            attempt_id="attempt-1",
            relative_path=Path("creative/brief.yaml"),
            payload=b"project",
        )

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_owned_temp_name_sanitizes_attempt_id_in_final_parent(tmp_path: Path) -> None:
    final_path = tmp_path / "state/projects/project.2.yaml"
    temp_name = _owned_temp_name("attempt:/ 2", final_path)

    assert temp_name.startswith(".p2a-attempt___2-")
    assert temp_name.endswith(".tmp")
    assert "/" not in temp_name and ":" not in temp_name
    assert final_path.parent / temp_name == tmp_path / "state/projects" / temp_name


def test_owned_temp_name_disambiguates_sanitized_attempt_ids(tmp_path: Path) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    slash_name = _owned_temp_name("attempt/a", final_path)
    colon_name = _owned_temp_name("attempt:a", final_path)
    crafted_safe_name = _owned_temp_name("attempt_a-5e93177664e1", final_path)
    safe_name = _owned_temp_name("attempt-1", final_path)

    assert slash_name != colon_name
    assert slash_name != crafted_safe_name
    assert hashlib.sha256(b"attempt-1").hexdigest()[:12] in safe_name
    assert slash_name.startswith(".p2a-attempt_a-")
    assert colon_name.startswith(".p2a-attempt_a-")
    assert slash_name.endswith("-brief.yaml.tmp")
    assert colon_name.endswith("-brief.yaml.tmp")
    assert "/" not in slash_name + colon_name
    assert ":" not in slash_name + colon_name
    assert slash_name == _owned_temp_name("attempt/a", final_path)


def test_owned_temp_name_is_bounded_for_long_attempt_and_final_names(tmp_path: Path) -> None:
    final_path = tmp_path / ("final-" + "x" * 1000 + ".yaml")
    name = _owned_temp_name("attempt-" + "a" * 1000, final_path)

    assert len(name.encode("utf-8")) <= 240
    assert name.startswith(".p2a-") and name.endswith(".tmp")
    assert "/" not in name and ":" not in name
    assert name == _owned_temp_name("attempt-" + "a" * 1000, final_path)


def test_lock_is_persistent_nonblocking_and_held_for_context_lifetime(tmp_path: Path) -> None:
    writer = make_committer(tmp_path)

    with writer._exclusive_lock() as lock_handle:
        assert lock_handle is not None
        assert (tmp_path / "state/commit.lock").is_file()
        with pytest.raises(AiVideoError) as exc:
            with make_committer(tmp_path)._exclusive_lock():
                pass
        assert exc.value.code is ErrorCode.PRODUCTION_STATE_BUSY

    with make_committer(tmp_path)._exclusive_lock():
        pass


def test_lock_maps_missing_posix_fcntl_to_unsupported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import ai_video.production.state_commit as state_commit

    monkeypatch.setattr(state_commit, "fcntl", None)

    with pytest.raises(AiVideoError) as exc:
        with make_committer(tmp_path)._exclusive_lock():
            pass

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_UNSUPPORTED


def test_lock_preserves_body_exception_when_unlock_and_close_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai_video.production.state_commit as state_commit

    fake_fcntl = _FakeFcntl(unlock_error=True)
    handle = _FakeLockHandle(close_error=True)
    monkeypatch.setattr(state_commit, "fcntl", fake_fcntl)
    monkeypatch.setattr(Path, "open", lambda *_args, **_kwargs: handle)

    with pytest.raises(RuntimeError, match="body failure") as exc:
        with make_committer(tmp_path)._exclusive_lock():
            raise RuntimeError("body failure")

    assert fake_fcntl.calls == [fake_fcntl.LOCK_EX | fake_fcntl.LOCK_NB, fake_fcntl.LOCK_UN]
    assert handle.closed is True
    assert any("unlock" in note or "close" in note for note in exc.value.__notes__)


def test_lock_acquisition_failure_skips_unlock_and_preserves_busy_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai_video.production.state_commit as state_commit

    fake_fcntl = _FakeFcntl(busy=True)
    handle = _FakeLockHandle(close_error=True)
    monkeypatch.setattr(state_commit, "fcntl", fake_fcntl)
    monkeypatch.setattr(Path, "open", lambda *_args, **_kwargs: handle)

    with pytest.raises(AiVideoError) as exc:
        with make_committer(tmp_path)._exclusive_lock():
            pass

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_BUSY
    assert fake_fcntl.calls == [fake_fcntl.LOCK_EX | fake_fcntl.LOCK_NB]
    assert handle.closed is True
    assert any("close" in note for note in exc.value.__notes__)


def test_lock_cleanup_failure_after_success_is_typed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import ai_video.production.state_commit as state_commit

    fake_fcntl = _FakeFcntl(unlock_error=True)
    handle = _FakeLockHandle(close_error=True)
    monkeypatch.setattr(state_commit, "fcntl", fake_fcntl)
    monkeypatch.setattr(Path, "open", lambda *_args, **_kwargs: handle)

    with pytest.raises(AiVideoError) as exc:
        with make_committer(tmp_path)._exclusive_lock():
            pass

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert "lock cleanup" in exc.value.user_message.lower()


def test_immutable_promotion_is_idempotent_and_does_not_overwrite(tmp_path: Path) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    final_path.parent.mkdir()
    writer = make_committer(tmp_path)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"same")

    assert writer._write_immutable_artifact(artifact, attempt_id="attempt-1") == final_path
    assert final_path.read_bytes() == b"same"
    assert writer._write_immutable_artifact(artifact, attempt_id="attempt-1") == final_path
    assert not list(final_path.parent.glob(".p2a-attempt-1-brief.yaml.tmp"))

    conflict = writer.prepare_artifact("attempt-2", Path("creative/brief.yaml"), b"different")
    with pytest.raises(AiVideoError) as exc:
        writer._write_immutable_artifact(conflict, attempt_id="attempt-2")
    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert final_path.read_bytes() == b"same"


def test_immutable_write_makes_each_new_parent_directory_durable_before_descending(
    tmp_path: Path,
) -> None:
    ops = RecordingNativeFileOps(tmp_path)
    writer = make_committer(tmp_path, ops)
    artifact = writer.prepare_artifact(
        "attempt-1", Path("composition/generated/source.bin"), b"source"
    )
    temp_name = _owned_temp_name("attempt-1", tmp_path / "composition/generated/source.bin")

    writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert ops.events == [
        "mkdir:composition",
        "fsync_dir:.",
        "mkdir:composition/generated",
        "fsync_dir:composition",
        f"open:composition/generated/{temp_name}",
        f"write:composition/generated/{temp_name}",
        f"flush:composition/generated/{temp_name}",
        f"fsync_file:composition/generated/{temp_name}",
        "fsync_dir:.",
        "fsync_dir:composition",
        f"stat:composition/generated/{temp_name}",
        "stat:composition/generated",
        "fsync_dir:.",
        "fsync_dir:composition",
        f"link:composition/generated/{temp_name}->composition/generated/source.bin",
        "fsync_dir:composition/generated",
        "sha:composition/generated/source.bin",
        f"unlink:composition/generated/{temp_name}",
    ]


def test_idempotent_immutable_write_fsyncs_parent_before_success(tmp_path: Path) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    final_path.parent.mkdir()
    final_path.write_bytes(b"same")
    ops = RecordingNativeFileOps(tmp_path)
    writer = make_committer(tmp_path, ops)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"same")
    temp_name = _owned_temp_name("attempt-1", final_path)

    writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert ops.events == [
        "fsync_dir:.",
        f"open:creative/{temp_name}",
        f"write:creative/{temp_name}",
        f"flush:creative/{temp_name}",
        f"fsync_file:creative/{temp_name}",
        "fsync_dir:.",
        f"stat:creative/{temp_name}",
        "stat:creative",
        "fsync_dir:.",
        f"link:creative/{temp_name}->creative/brief.yaml",
        "sha:creative/brief.yaml",
        "fsync_dir:creative",
        "sha:creative/brief.yaml",
        f"unlink:creative/{temp_name}",
    ]
    assert "fsync_dir:creative" in ops.events


def test_immutable_retry_fsyncs_existing_final_after_prior_link_durability_failure(
    tmp_path: Path,
) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    final_path.parent.mkdir()
    ops = FailingLinkedParentFsyncOps(tmp_path, final_path.parent)
    writer = make_committer(tmp_path, ops)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"same")

    with pytest.raises(AiVideoError) as exc:
        writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert final_path.read_bytes() == b"same"
    first_parent_fsyncs = ops.events.count("fsync_dir:creative")

    writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert ops.events.count("fsync_dir:creative") == first_parent_fsyncs + 1


def test_manifest_replace_revalidates_swapped_state_symlink(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    writer = make_committer(
        tmp_path,
        injector=_SwapStateAfterManifestFsync(tmp_path, outside),
    )

    with pytest.raises(AiVideoError) as exc:
        writer._write_manifest_atomic(make_manifest())

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert not (outside / "manifest.json").exists()
    assert (outside / ".p2a-manifest.tmp").read_bytes() == b"external state temp"


def test_immutable_link_revalidates_swapped_parent_symlink(tmp_path: Path) -> None:
    (tmp_path / "creative").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    writer = make_committer(
        tmp_path,
        injector=_SwapArtifactParentAfterFileFsync(tmp_path, outside),
    )
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"same")

    with pytest.raises(AiVideoError) as exc:
        writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert not (outside / "brief.yaml").exists()
    assert next(outside.glob(".p2a-*.tmp")).read_bytes() == b"external artifact temp"


def test_immutable_verification_mismatch_is_typed_and_cleans_owned_temp(tmp_path: Path) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    final_path.parent.mkdir()
    ops = CorruptingRecordingNativeFileOps(tmp_path)
    writer = make_committer(tmp_path, ops)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"same")
    temp_name = _owned_temp_name("attempt-1", final_path)

    with pytest.raises(AiVideoError) as exc:
        writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert f"unlink:creative/{temp_name}" in ops.events
    assert not list(final_path.parent.glob(temp_name))


def test_immutable_promotion_rejects_cross_device_temp_before_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    final_path.parent.mkdir()
    writer = make_committer(tmp_path)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"same")
    original_stat = Path.stat

    def mismatched_stat(path: Path, *args: object, **kwargs: object) -> object:
        result = original_stat(path, *args, **kwargs)
        if path.name.startswith(".p2a-"):
            return SimpleNamespace(st_dev=result.st_dev + 1)
        return result

    monkeypatch.setattr(Path, "stat", mismatched_stat)
    with pytest.raises(AiVideoError) as exc:
        writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_UNSUPPORTED
    assert not final_path.exists()


def test_immutable_cleanup_failure_keeps_primary_error_and_adds_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    final_path.parent.mkdir()
    final_path.write_bytes(b"existing")
    writer = make_committer(tmp_path)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"different")

    import ai_video.production.state_commit as state_commit

    original_unlink = state_commit._NativeFileOps.unlink

    def failing_unlink(self: object, path: Path, *, missing_ok: bool = False) -> None:
        if path.name.startswith(".p2a-"):
            raise OSError("cleanup failed")
        original_unlink(self, path, missing_ok=missing_ok)

    monkeypatch.setattr(state_commit._NativeFileOps, "unlink", failing_unlink)
    with pytest.raises(AiVideoError) as exc:
        writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert any("cleanup" in note.lower() for note in exc.value.__notes__)
    assert final_path.read_bytes() == b"existing"


def test_mutable_atomic_write_uses_exclusive_temp_and_durable_replace(tmp_path: Path) -> None:
    final_path = tmp_path / "state/manifest.json"
    final_path.parent.mkdir()
    writer = make_committer(tmp_path)

    writer._write_mutable_atomic(final_path, b"first", temp_name=".p2a-manifest.tmp")
    assert final_path.read_bytes() == b"first"

    writer._write_mutable_atomic(final_path, b"second", temp_name=".p2a-manifest.tmp")
    assert final_path.read_bytes() == b"second"
