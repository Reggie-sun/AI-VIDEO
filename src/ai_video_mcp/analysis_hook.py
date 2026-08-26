from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from ai_video_mcp.serialization import serialization_state_root, serialized_execution


PROJECT_ROOT = Path(__file__).resolve().parents[2]
JOB_SCHEMA = "ai-video-analysis-hook/1"
RESULT_SCHEMA = "ai-video-analysis-hook-result/1"
ANALYSIS_PROFILE_REVISION = "automatic-video-analyze/1"
MAXIMUM_HOOK_INPUT_BYTES = 1_000_000
MAXIMUM_TOOL_OUTPUT_BYTES = 1_000_000
MAXIMUM_JOBS_PER_EVENT = 64
MAXIMUM_SOURCE_AGE_SECONDS = 600
MAXIMUM_FUTURE_SKEW_SECONDS = 30
SUCCESS_STATUSES = frozenset({"completed", "fetched", "generated", "success", "succeeded"})
PATH_KEYS = frozenset(
    {"artifact_path", "final_output", "local_path", "output_path", "video_path"}
)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def default_state_root(project_root: Path = PROJECT_ROOT) -> Path:
    return serialization_state_root(project_root)


def _ensure_private_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink() or not path.is_dir():
        raise OSError(f"unsafe hook state directory: {path}")
    os.chmod(path, 0o700)


def _write_json_exclusive(path: Path, payload: Mapping[str, Any]) -> bool:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    try:
        fd = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
    except FileExistsError:
        return False
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb", closefd=False) as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(fd)
    return True


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    fd = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb", closefd=False) as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(fd)
    os.replace(temporary, path)


def _json_objects(value: object) -> Iterable[object]:
    if isinstance(value, Mapping):
        yield value
        for key in ("content", "output", "stdout", "text"):
            nested = value.get(key)
            if isinstance(nested, (Mapping, list, str)):
                yield from _json_objects(nested)
        return
    if isinstance(value, list):
        for nested in value:
            yield from _json_objects(nested)
        return
    if not isinstance(value, str) or len(value.encode("utf-8")) > MAXIMUM_TOOL_OUTPUT_BYTES:
        return
    stripped = value.strip()
    if not stripped:
        return
    candidates = [stripped, *reversed(stripped.splitlines())]
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, (Mapping, list)):
            yield parsed


def _successful_paths(value: object, inherited_status: str | None = None) -> Iterable[str]:
    if isinstance(value, Mapping):
        raw_status = value.get("status")
        status = raw_status.lower() if isinstance(raw_status, str) else inherited_status
        if status in SUCCESS_STATUSES:
            for key in PATH_KEYS:
                path = value.get(key)
                if isinstance(path, str) and path:
                    yield path
        for nested in value.values():
            if isinstance(nested, (Mapping, list)):
                yield from _successful_paths(nested, status)
    elif isinstance(value, list):
        for nested in value:
            yield from _successful_paths(nested, inherited_status)


def _tool_response_paths(tool_response: object) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for payload in _json_objects(tool_response):
        for path in _successful_paths(payload):
            if path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def _event_cwd(event: Mapping[str, Any], project_root: Path) -> Path | None:
    cwd = event.get("cwd")
    if not isinstance(cwd, str):
        return None
    try:
        resolved = Path(cwd).resolve(strict=True)
    except OSError:
        return None
    return resolved if _is_relative_to(resolved, project_root) else None


def _fresh_local_mp4(
    raw_path: str,
    *,
    base_dir: Path,
    project_root: Path,
    now_ns: int,
) -> tuple[Path, os.stat_result] | None:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    try:
        if candidate.is_symlink():
            return None
        resolved = candidate.resolve(strict=True)
        metadata = resolved.stat()
    except OSError:
        return None
    if (
        not _is_relative_to(resolved, project_root)
        or resolved.suffix.lower() != ".mp4"
        or not stat.S_ISREG(metadata.st_mode)
    ):
        return None
    age_ns = now_ns - metadata.st_mtime_ns
    if age_ns > MAXIMUM_SOURCE_AGE_SECONDS * 1_000_000_000:
        return None
    if age_ns < -MAXIMUM_FUTURE_SKEW_SECONDS * 1_000_000_000:
        return None
    return resolved, metadata


def _queue_identity(path: Path, metadata: os.stat_result) -> str:
    material = "\0".join(
        (
            str(path),
            str(metadata.st_dev),
            str(metadata.st_ino),
            str(metadata.st_size),
            str(metadata.st_mtime_ns),
        )
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _spawn_worker(job_path: Path) -> None:
    subprocess.Popen(
        [sys.executable, "-m", "ai_video_mcp.analysis_hook", "worker", "--job", str(job_path)],
        cwd=str(PROJECT_ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        start_new_session=True,
    )


def process_post_tool_event(
    event: Mapping[str, Any],
    *,
    project_root: Path = PROJECT_ROOT,
    state_root: Path | None = None,
    spawn_worker: Callable[[Path], object] = _spawn_worker,
    now_ns: int | None = None,
) -> dict[str, object]:
    if event.get("hook_event_name") != "PostToolUse":
        return {"continue": True}
    tool_name = event.get("tool_name")
    if not isinstance(tool_name, str):
        return {"continue": True}
    normalized_tool = tool_name.lower().replace("_", "-")
    if "video-analysis" in normalized_tool or "ai-video-mcp" in normalized_tool:
        return {"continue": True}
    project_root = project_root.resolve()
    event_cwd = _event_cwd(event, project_root)
    if event_cwd is None:
        return {"continue": True}

    accepted: list[tuple[Path, os.stat_result]] = []
    accepted_paths: set[Path] = set()
    current_ns = time.time_ns() if now_ns is None else now_ns
    for raw_path in _tool_response_paths(event.get("tool_response")):
        candidate = _fresh_local_mp4(
            raw_path,
            base_dir=event_cwd,
            project_root=project_root,
            now_ns=current_ns,
        )
        if candidate is None or candidate[0] in accepted_paths:
            continue
        accepted.append(candidate)
        accepted_paths.add(candidate[0])
    if not accepted:
        return {"continue": True}

    resolved_state_root = state_root or default_state_root(project_root)
    queue_root = resolved_state_root / "queue"
    try:
        _ensure_private_directory(resolved_state_root)
        _ensure_private_directory(queue_root)
    except OSError:
        return {"continue": True}

    queued: list[Path] = []
    queued_payloads: dict[Path, dict[str, object]] = {}
    deferred = 0
    seen_identities: set[str] = set()
    for path, metadata in accepted:
        identity = _queue_identity(path, metadata)
        if identity in seen_identities:
            continue
        seen_identities.add(identity)
        job_path = queue_root / f"{identity}.json"
        if job_path.exists():
            continue
        if len(queued) >= MAXIMUM_JOBS_PER_EVENT:
            deferred += 1
            continue
        payload = {
            "schema": JOB_SCHEMA,
            "created_at_ns": current_ns,
            "project_root": str(project_root),
            "source_dev": metadata.st_dev,
            "source_ino": metadata.st_ino,
            "source_mtime_ns": metadata.st_mtime_ns,
            "source_path": str(path),
            "source_size": metadata.st_size,
            "tool_name": tool_name,
        }
        try:
            created = _write_json_exclusive(job_path, payload)
        except OSError:
            continue
        if not created:
            continue
        queued.append(job_path)
        queued_payloads[job_path] = payload

    if not queued:
        return {"continue": True}
    batch_entry = queued[0]
    batch_payload = {
        **queued_payloads[batch_entry],
        "batch_job_paths": [str(path) for path in queued],
    }
    try:
        _write_json_atomic(batch_entry, batch_payload)
        spawn_worker(batch_entry)
    except OSError:
        for path in queued:
            path.unlink(missing_ok=True)
        return {"continue": True}
    deferred_message = ""
    if deferred:
        deferred_message = (
            f" {deferred} additional generated MP4 file(s) were deferred by the "
            "per-event queue cap and remain eligible on a repeated event."
        )
    return {
        "continue": True,
        "systemMessage": (
            "Queued background video analysis for "
            f"{len(queued)} generated local MP4 file(s) in one detached batch; "
            "advisory jobs: "
            + ", ".join(str(path) for path in queued)
            + deferred_message
        ),
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        with os.fdopen(fd, "rb", closefd=False) as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
    finally:
        os.close(fd)
    return digest.hexdigest()


def _default_analyze(path: str) -> dict:
    from ai_video_mcp.cache import AnalysisCache
    from ai_video_mcp.config import get_config
    from ai_video_mcp.tools.analyze import video_analyze

    config = get_config()
    cache = AnalysisCache(max_size=config.cache_max_size, ttl_seconds=config.cache_ttl_seconds)
    return video_analyze(
        path,
        config,
        cache,
        extract_frames=True,
        max_frames=min(config.max_frames, 4),
        transcribe_audio=False,
        detect_scenes=True,
    )


def _analysis_profile_fingerprint() -> str:
    from ai_video_mcp.config import get_config

    config = get_config()
    profile = {
        "revision": ANALYSIS_PROFILE_REVISION,
        "detect_scenes": True,
        "extract_frames": True,
        "transcribe_audio": False,
        "frame_interval": config.frame_interval,
        "max_frames": min(config.max_frames, 4),
        "frame_width": config.frame_width,
        "frame_quality": config.frame_quality,
        "frame_format": config.frame_format,
        "scene_threshold": config.scene_threshold,
        "min_scene_length_seconds": config.min_scene_length_seconds,
        "max_video_duration_seconds": config.max_video_duration_seconds,
        "max_video_file_size_mb": config.max_video_file_size_mb,
    }
    encoded = json.dumps(profile, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_job(job_path: Path) -> dict[str, Any]:
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != JOB_SCHEMA:
        raise ValueError("invalid analysis hook job")
    return payload


def _source_matches_job(path: Path, payload: Mapping[str, Any]) -> bool:
    try:
        if path.is_symlink():
            return False
        metadata = path.stat()
    except OSError:
        return False
    return _metadata_matches_job(metadata, payload)


def _metadata_matches_job(
    metadata: os.stat_result,
    payload: Mapping[str, Any],
) -> bool:
    return all(
        (
            metadata.st_dev == payload.get("source_dev"),
            metadata.st_ino == payload.get("source_ino"),
            metadata.st_size == payload.get("source_size"),
            metadata.st_mtime_ns == payload.get("source_mtime_ns"),
        )
    )


def _snapshot_source(
    path: Path,
    payload: Mapping[str, Any],
    state_root: Path,
) -> tuple[Path, str] | None:
    snapshot_root = state_root / "snapshots"
    try:
        _ensure_private_directory(snapshot_root)
    except OSError:
        return None
    snapshot_path = snapshot_root / f"snapshot-{os.getpid()}-{time.time_ns()}.mp4"
    source_fd = -1
    snapshot_fd = -1
    completed = False
    try:
        source_fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        if not _metadata_matches_job(os.fstat(source_fd), payload):
            return None
        snapshot_fd = os.open(
            snapshot_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        digest = hashlib.sha256()
        with (
            os.fdopen(source_fd, "rb", closefd=False) as source,
            os.fdopen(snapshot_fd, "wb", closefd=False) as snapshot,
        ):
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
                snapshot.write(chunk)
            snapshot.flush()
            os.fsync(snapshot.fileno())
        if not _metadata_matches_job(os.fstat(source_fd), payload):
            return None
        os.fchmod(snapshot_fd, 0o400)
        completed = True
        return snapshot_path, digest.hexdigest()
    except OSError:
        return None
    finally:
        if source_fd >= 0:
            os.close(source_fd)
        if snapshot_fd >= 0:
            os.close(snapshot_fd)
        if not completed:
            snapshot_path.unlink(missing_ok=True)


def _rebind_snapshot_paths(
    value: object,
    *,
    snapshot_path: Path,
    source_path: Path,
) -> object:
    if isinstance(value, str):
        return str(source_path) if value == str(snapshot_path) else value
    if isinstance(value, Mapping):
        return {
            key: _rebind_snapshot_paths(
                nested,
                snapshot_path=snapshot_path,
                source_path=source_path,
            )
            for key, nested in value.items()
        }
    if isinstance(value, list):
        return [
            _rebind_snapshot_paths(
                nested,
                snapshot_path=snapshot_path,
                source_path=source_path,
            )
            for nested in value
        ]
    return value


def _failure_receipt(
    state_root: Path,
    job_path: Path,
    *,
    status_value: str,
    source_path: str | None,
) -> Path:
    failure_root = state_root / "failures"
    _ensure_private_directory(failure_root)
    target = failure_root / job_path.name
    _write_json_atomic(
        target,
        {
            "schema": RESULT_SCHEMA,
            "status": status_value,
            "advisory_only": True,
            "production_verdict": None,
            "source_path": source_path,
            "analysis": None,
        },
    )
    return target


def process_job(
    job_path: Path,
    *,
    analyze: Callable[[str], dict] = _default_analyze,
    analysis_profile_fingerprint: str | None = None,
) -> Path:
    job_path = job_path.resolve(strict=True)
    payload = _load_job(job_path)
    state_root = job_path.parent.parent
    _ensure_private_directory(state_root)
    with serialized_execution(state_root / "worker.lock"):
        return _process_job_locked(
            job_path,
            payload,
            state_root,
            analyze,
            analysis_profile_fingerprint or _analysis_profile_fingerprint(),
        )


def _process_job_locked(
    job_path: Path,
    payload: Mapping[str, Any],
    state_root: Path,
    analyze: Callable[[str], dict],
    analysis_profile_fingerprint: str,
) -> Path:
    source_value = payload.get("source_path")
    project_value = payload.get("project_root")
    if not isinstance(source_value, str) or not isinstance(project_value, str):
        return _failure_receipt(
            state_root, job_path, status_value="invalid_job", source_path=None
        )
    source_path = Path(source_value)
    project_root = Path(project_value).resolve()
    try:
        resolved_source = source_path.resolve(strict=True)
    except OSError:
        resolved_source = source_path
    if (
        not _is_relative_to(resolved_source, project_root)
        or resolved_source.suffix.lower() != ".mp4"
        or not _source_matches_job(resolved_source, payload)
    ):
        return _failure_receipt(
            state_root,
            job_path,
            status_value="stale_source",
            source_path=str(resolved_source),
        )

    result_root = state_root / "results"
    lock_root = state_root / "locks"
    try:
        _ensure_private_directory(result_root)
        _ensure_private_directory(lock_root)
    except OSError:
        return _failure_receipt(
            state_root,
            job_path,
            status_value="analysis_failed",
            source_path=str(resolved_source),
        )
    snapshot = _snapshot_source(resolved_source, payload, state_root)
    if snapshot is None:
        return _failure_receipt(
            state_root,
            job_path,
            status_value="stale_source",
            source_path=str(resolved_source),
        )
    snapshot_path, source_sha256 = snapshot
    result_identity = f"{source_sha256}.{analysis_profile_fingerprint}"
    result_path = result_root / f"{result_identity}.json"
    lock_path = lock_root / f"{result_identity}.lock"
    lock_fd = -1
    try:
        try:
            initial_source_sha256 = _sha256_file(resolved_source)
        except OSError:
            initial_source_sha256 = None
        if initial_source_sha256 != source_sha256 or not _source_matches_job(
            resolved_source, payload
        ):
            return _failure_receipt(
                state_root,
                job_path,
                status_value="stale_source",
                source_path=str(resolved_source),
            )
        lock_fd = os.open(
            lock_path,
            os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        os.fchmod(lock_fd, 0o600)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        if result_path.is_file():
            return result_path
        if not _source_matches_job(resolved_source, payload):
            return _failure_receipt(
                state_root,
                job_path,
                status_value="stale_source",
                source_path=str(resolved_source),
            )
        try:
            analysis = analyze(str(snapshot_path))
        except Exception:
            return _failure_receipt(
                state_root,
                job_path,
                status_value="analysis_failed",
                source_path=str(resolved_source),
            )
        try:
            final_snapshot_sha256 = _sha256_file(snapshot_path)
        except OSError:
            final_snapshot_sha256 = None
        if final_snapshot_sha256 != source_sha256 or not _source_matches_job(
            resolved_source, payload
        ):
            return _failure_receipt(
                state_root,
                job_path,
                status_value="stale_source",
                source_path=str(resolved_source),
            )
        try:
            final_sha256 = _sha256_file(resolved_source)
        except OSError:
            final_sha256 = None
        if (
            final_sha256 != source_sha256
            or not _source_matches_job(resolved_source, payload)
        ):
            return _failure_receipt(
                state_root,
                job_path,
                status_value="stale_source",
                source_path=str(resolved_source),
            )
        _write_json_atomic(
            result_path,
            {
                "schema": RESULT_SCHEMA,
                "status": "succeeded",
                "advisory_only": True,
                "production_verdict": None,
                "source_path": str(resolved_source),
                "source_sha256": source_sha256,
                "source_size": payload["source_size"],
                "analysis_profile_fingerprint": analysis_profile_fingerprint,
                "analysis": _rebind_snapshot_paths(
                    analysis,
                    snapshot_path=snapshot_path,
                    source_path=resolved_source,
                ),
            },
        )
        return result_path
    finally:
        if lock_fd >= 0:
            os.close(lock_fd)
        snapshot_path.unlink(missing_ok=True)


def process_job_batch(
    job_path: Path,
    *,
    analyze: Callable[[str], dict] = _default_analyze,
    analysis_profile_fingerprint: str | None = None,
) -> list[Path]:
    resolved_job = job_path.resolve(strict=True)
    payload = _load_job(resolved_job)
    raw_paths = payload.get("batch_job_paths")
    if not isinstance(raw_paths, list):
        return [
            process_job(
                resolved_job,
                analyze=analyze,
                analysis_profile_fingerprint=analysis_profile_fingerprint,
            )
        ]
    queue_root = resolved_job.parent.resolve()
    job_paths: list[Path] = []
    for value in raw_paths[:MAXIMUM_JOBS_PER_EVENT]:
        if not isinstance(value, str):
            continue
        try:
            candidate = Path(value).resolve(strict=True)
        except OSError:
            continue
        if candidate.parent == queue_root and candidate.suffix == ".json":
            job_paths.append(candidate)
    if not job_paths:
        job_paths = [resolved_job]
    return [
        process_job(
            candidate,
            analyze=analyze,
            analysis_profile_fingerprint=analysis_profile_fingerprint,
        )
        for candidate in job_paths
    ]


def _post_tool_main() -> int:
    raw = sys.stdin.buffer.read(MAXIMUM_HOOK_INPUT_BYTES + 1)
    if len(raw) > MAXIMUM_HOOK_INPUT_BYTES:
        print(json.dumps({"continue": True}))
        return 0
    try:
        event = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        print(json.dumps({"continue": True}))
        return 0
    if not isinstance(event, Mapping):
        print(json.dumps({"continue": True}))
        return 0
    print(json.dumps(process_post_tool_event(event), sort_keys=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Queue generated-video MCP analysis.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("post-tool-use")
    worker = subparsers.add_parser("worker")
    worker.add_argument("--job", required=True)
    arguments = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if arguments.command == "post-tool-use":
        return _post_tool_main()
    process_job_batch(Path(arguments.job))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
