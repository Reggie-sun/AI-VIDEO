from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_video.errors import AiVideoError
from ai_video.manifest import RunManifest, ShotRecord
from ai_video import provider_console, provider_console_continuity
from ai_video.production._video_continuity import (
    ContinuityArtifactIdentity,
    ContinuityConstraintSet,
)
from ai_video.production.models import (
    StateCommitStatus,
    ToolIdentity,
    VideoAttemptPhase,
)


ZERO = "0" * 64
ONE = "1" * 64
AUTOMATIC = ToolIdentity(name="continuity-cuda", version="1")
HUMAN = ToolIdentity(name="continuity-human", version="1")


def _write(path: Path, data: bytes = b"{}") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _production_workspace(root: Path, relative: str) -> Path:
    project = _write(root / relative / "project.yaml", b"project_id: demo\n")
    _write(project.parent / "state" / "manifest.json")
    return project


def _ns(**values):
    return SimpleNamespace(**values)


def test_catalog_is_bounded_deterministic_and_does_not_follow_symlinks(tmp_path: Path):
    runs = tmp_path / "runs"
    older = _production_workspace(runs, "run-b/project")
    newer = _production_workspace(runs, "run-a/project")
    legacy_path = runs / "legacy" / "manifest.json"
    _write(
        legacy_path,
        RunManifest(run_id="legacy", updated_at="2026-08-21T01:02:03+00:00").model_dump_json().encode(),
    )
    os.utime(older, ns=(1_000_000_000, 1_000_000_000))
    os.utime(older.parent / "state" / "manifest.json", ns=(1_000_000_000, 1_000_000_000))
    os.utime(newer, ns=(2_000_000_000, 2_000_000_000))
    os.utime(newer.parent / "state" / "manifest.json", ns=(2_000_000_000, 2_000_000_000))
    os.utime(legacy_path, ns=(3_000_000_000, 3_000_000_000))
    outside = _production_workspace(tmp_path, "outside")
    (runs / "linked").symlink_to(outside.parent, target_is_directory=True)
    _production_workspace(runs, "too/deep/for/the/catalog/limit")

    result = provider_console.catalog_runs(runs, max_workspaces=2, max_depth=4)

    assert result["boundary"] == {
        "read_only": True,
        "local_only": True,
        "network": False,
    }
    assert [item["workspace"] for item in result["workspaces"]] == [
        "legacy/manifest.json",
        "run-a/project/project.yaml",
    ]
    assert all("linked" not in item["workspace"] for item in result["workspaces"])


def test_catalog_and_detail_support_nested_legacy_output_manifests(tmp_path: Path):
    runs = tmp_path / "runs"
    manifest_path = runs / "legacy-capture" / "output" / "take-r2" / "manifest.json"
    production_state = runs / "legacy-capture" / "output" / "state" / "manifest.json"
    _write(
        manifest_path,
        RunManifest(
            run_id="legacy-run",
            status="failed",
            shots=[ShotRecord(shot_id="shot-1", status="failed")],
        ).model_dump_json().encode(),
    )
    _write(
        production_state,
        RunManifest(run_id="not-a-legacy-workspace").model_dump_json().encode(),
    )

    catalog = provider_console.catalog_runs(runs)

    assert [item["workspace"] for item in catalog["workspaces"]] == [
        "legacy-capture/output/take-r2/manifest.json"
    ]
    detail = provider_console.project_workspace_detail(
        runs, "legacy-capture/output/take-r2/manifest.json"
    )
    assert detail["kind"] == "legacy"
    assert detail["run_id"] == "legacy-run"
    assert detail["shots"] == [
        {"shot_id": "shot-1", "status": "failed", "active_attempt": 0}
    ]
    assert "legacy-capture/output/state/manifest.json" not in {
        item["workspace"] for item in catalog["workspaces"]
    }
    with pytest.raises(ValueError, match="workspace"):
        provider_console.project_workspace_detail(
            runs, "legacy-capture/output/state/manifest.json"
        )


def test_catalog_rejects_missing_or_symlink_runs_root(tmp_path: Path):
    with pytest.raises(ValueError, match="runs root"):
        provider_console.catalog_runs(tmp_path / "missing")
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="runs root"):
        provider_console.catalog_runs(alias)


def test_catalog_enforces_workspace_and_entry_scan_budgets(tmp_path: Path):
    runs = tmp_path / "runs"
    for index in range(6):
        _production_workspace(runs, f"run-{index}/project")

    workspace_limited = provider_console.catalog_runs(
        runs, max_workspaces=10, max_scanned_workspaces=2, max_entries=100,
    )
    assert workspace_limited["scan"]["workspaces"] <= 2
    assert workspace_limited["truncated"] is True

    entry_limited = provider_console.catalog_runs(
        runs, max_workspaces=10, max_scanned_workspaces=10, max_entries=2,
    )
    assert entry_limited["scan"]["entries"] <= 2
    assert entry_limited["truncated"] is True


def test_catalog_entry_budget_limits_scandir_consumption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    runs = tmp_path / "runs"
    for index in range(20):
        (runs / f"directory-{index}").mkdir(parents=True)
    real_scandir = os.scandir
    consumed = 0

    class CountingScandir:
        def __init__(self, path):
            self._iterator = real_scandir(path)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self._iterator.close()

        def __iter__(self):
            return self

        def __next__(self):
            nonlocal consumed
            consumed += 1
            return next(self._iterator)

    monkeypatch.setattr(provider_console.os, "scandir", CountingScandir)

    result = provider_console.catalog_runs(runs, max_entries=2)

    assert result["truncated"] is True
    assert result["scan"]["entries"] == 2
    assert consumed <= 3


def test_production_detail_uses_strict_readers_and_returns_only_whitelisted_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    runs = tmp_path / "runs"
    project_path = _production_workspace(runs, "demo/project")
    first_frame = _write(project_path.parent / "assets" / "first.png", b"image")
    candidate = _write(project_path.parent / "assets" / "candidate.mp4", b"video-bytes")
    first_record = _ns(
        asset_id="first-frame", asset_type=_ns(value="image"), mime_type="image/png",
        size_bytes=5, width=1280, height=720, duration_seconds=None, video_metadata=None,
        sha256=ZERO, egress=_ns(remote=False), artifact_path=Path("assets/first.png"),
    )
    video_metadata = _ns(
        frame_count=124, fps_numerator=24, fps_denominator=1,
        duration_milliseconds=5167, codec_name="h264", container_name="mp4",
    )
    video_record = _ns(
        asset_id="video-output", asset_type=_ns(value="video"), mime_type="video/mp4",
        size_bytes=11, width=1344, height=672, duration_seconds=5.167,
        video_metadata=video_metadata, sha256=ONE, egress=_ns(remote=False),
        artifact_path=Path("assets/candidate.mp4"),
    )
    request_pointer = _ns(
        path=Path("state/video-generation/requests/request.json"), file_sha256=ZERO,
        request_receipt_fingerprint=ONE, generation_id="generation-1",
        request_input_hash=ZERO, resolved_generation_hash=ONE, output_asset_id="video-output",
    )
    state = _ns(
        request=request_pointer, phase=_ns(value="activate"), generation_id="generation-1",
        candidate_video_asset_ids=("video-output",), terminal_frame_evidence=None,
        paid_submit_receipt=None, local_submit_receipt=_ns(path=Path("state/local.json")),
    )
    attempt = _ns(
        attempt_id="attempt-1", operation="video_generation", status=_ns(value="succeeded"),
        started_at="2026-08-21T01:00:00+00:00", finished_at="2026-08-21T01:01:00+00:00",
        video_generation_state=state, error_code=None, error_message="raw secret error",
    )
    shot = _ns(
        shot_id="shot-12", scene_id="cafe", intent="Alice enters", visual_strategy=_ns(value="generated_video"),
        duration_policy=_ns(model_dump=lambda **_: {"mode": "fixed", "seconds": 5.0}), revision=3,
        content_hash=ZERO,
    )
    loaded = _ns(
        root=project_path.parent,
        project=_ns(project_id="demo", title="Demo", revision=7, content_hash=ZERO),
        manifest=_ns(schema_version="2.8", manifest_revision=34, attempts=(attempt,)),
        shots=(shot,), scenes=(_ns(scene_id="cafe", title="Cafe"),),
        registry=_ns(assets=(first_record, video_record)),
        asset_paths={"first-frame": first_frame, "video-output": candidate},
    )
    binding = _ns(
        role="first_frame", asset_id="first-frame", mime_type="image/png", width=1280,
        height=720, size_bytes=5, sha256=ZERO,
    )
    original_request = _ns(target_shot_id="shot-12", target_asset_role="generated_video")
    request = _ns(
        provider_name="comfy-local-h3", provider_kind="minimax_h3_fl2va", model_id="minimax-h3-fl2va",
        provider_profile=_ns(profile_id="quality", profile_version="v1", profile_sha256=ZERO),
        capability_id="minimax-h3-local-v1", execution_kind=_ns(value="local"),
        billing_kind=_ns(value="local_unmetered"), mode=_ns(value="image_to_video"),
        effective_output=_ns(model_dump=lambda **_: {
            "duration_seconds": 5, "width": 1344, "height": 672, "fps": 24,
            "container": "mp4", "mime_type": "video/mp4", "native_audio": True,
        }),
        image_bindings=(binding,), continuity_binding=None, activation_scope=_ns(request=original_request),
        generation_id="generation-1", request_input_hash=ZERO, resolved_generation_hash=ONE,
        desired_generation_fingerprint=ONE, output_asset_id="video-output",
        prompt_text="Alice walks into the cafe.",
        effective_negative_prompt_text="DO NOT LEAK NEGATIVE",
        provider_task_binding=_ns(provider_task_id="signed-url-secret"),
    )
    calls: list[object] = []
    monkeypatch.setattr(provider_console, "load_production_project", lambda path: calls.append(path) or loaded)
    monkeypatch.setattr(
        provider_console, "load_video_request_receipt",
        lambda root, pointer: calls.append((root, pointer)) or request,
    )

    before = {path: (path.stat().st_size, path.stat().st_mtime_ns) for path in runs.rglob("*") if path.is_file()}
    result = provider_console.project_workspace_detail(runs, "demo/project/project.yaml")
    after = {path: (path.stat().st_size, path.stat().st_mtime_ns) for path in runs.rglob("*") if path.is_file()}

    assert calls[0] == project_path
    assert calls[1] == (project_path.parent, request_pointer)
    assert before == after
    assert result["project"] == {
        "project_id": "demo", "title": "Demo", "revision": 7, "content_hash": ZERO,
    }
    assert result["attempts"][0]["provider"]["name"] == "comfy-local-h3"
    assert result["attempts"][0]["target_shot_id"] == "shot-12"
    assert result["attempts"][0]["mode"] == "image_to_video"
    assert result["attempts"][0]["generation_type"] == "I2V"
    assert result["attempts"][0]["prompt_text"] == "Alice walks into the cafe."
    assert [item["role"] for item in result["attempts"][0]["input_bindings"]] == [
        "first_frame"
    ]
    assert result["attempts"][0]["input_bindings"][0]["media"]["token"]
    assert result["attempts"][0]["first_frame_media"]["token"]
    assert result["attempts"][0]["candidate_media"]["token"]
    assert [item["asset_id"] for item in result["workspace_media"]] == [
        "first-frame",
        "video-output",
    ]
    assert result["workspace_media_truncated"] is False
    assert result["operation_summary"] == [
        {"operation": "video_generation", "count": 1}
    ]
    assert set(result["_media"]) == {
        result["attempts"][0]["first_frame_media"]["token"],
        result["attempts"][0]["candidate_media"]["token"],
    }
    serialized_public = json.dumps({key: value for key, value in result.items() if key != "_media"})
    assert str(tmp_path) not in serialized_public
    assert "DO NOT LEAK NEGATIVE" not in serialized_public
    assert "signed-url-secret" not in serialized_public
    assert "raw secret error" not in serialized_public


@pytest.mark.parametrize(
    ("mode", "roles", "media_roles", "expected_generation_type"),
    [
        ("text_to_video", (), (), "T2V"),
        ("image_to_video", ("first_frame",), (), "I2V"),
        ("image_to_video", ("first_frame", "last_frame"), (), "FL2V"),
        (
            "reference_to_video",
            ("reference",),
            (("video", "reference_video"),),
            "R2V",
        ),
    ],
)
def test_production_detail_projects_mode_specific_prompt_and_image_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    roles: tuple[str, ...],
    media_roles: tuple[tuple[str, str], ...],
    expected_generation_type: str,
):
    runs = tmp_path / "runs"
    project_path = _production_workspace(runs, f"mode-{expected_generation_type.lower()}")
    assets = []
    asset_paths = {}
    bindings = []
    media_bindings = []
    for index, role in enumerate(roles):
        asset_id = f"{role}-{index}"
        payload = f"{role}-{index}".encode()
        asset_path = _write(project_path.parent / "assets" / f"{asset_id}.png", payload)
        assets.append(
            _ns(
                asset_id=asset_id,
                asset_type=_ns(value="image"),
                mime_type="image/png",
                size_bytes=len(payload),
                width=1280,
                height=720,
                duration_seconds=None,
                video_metadata=None,
                sha256=f"{index + 2:064x}",
                egress=_ns(remote=False),
            )
        )
        asset_paths[asset_id] = asset_path
        bindings.append(_ns(role=role, asset_id=asset_id, mime_type="image/png"))
    for index, (kind, role) in enumerate(media_roles, start=len(roles)):
        asset_id = f"{role}-{index}"
        payload = f"{role}-{index}".encode()
        asset_path = _write(project_path.parent / "assets" / f"{asset_id}.mp4", payload)
        assets.append(
            _ns(
                asset_id=asset_id,
                asset_type=_ns(value="video"),
                mime_type="video/mp4",
                size_bytes=len(payload),
                width=1280,
                height=720,
                duration_seconds=5,
                video_metadata=_ns(
                    frame_count=120,
                    fps_numerator=24,
                    fps_denominator=1,
                ),
                sha256=f"{index + 2:064x}",
                egress=_ns(remote=False),
            )
        )
        asset_paths[asset_id] = asset_path
        media_bindings.append(
            _ns(kind=kind, role=role, asset_id=asset_id, mime_type="video/mp4")
        )
    state = _ns(
        request=_ns(path=Path("state/video-generation/requests/request.json")),
        phase=_ns(value="submit_intent"),
        generation_id=f"generation-{expected_generation_type.lower()}",
        candidate_video_asset_ids=(),
    )
    attempt = _ns(
        attempt_id=f"attempt-{expected_generation_type.lower()}",
        operation="video_generation",
        status=_ns(value="running"),
        started_at="2026-08-22T01:00:00+00:00",
        finished_at=None,
        video_generation_state=state,
    )
    loaded = _ns(
        root=project_path.parent,
        project=_ns(
            project_id=f"mode-{expected_generation_type.lower()}",
            title=f"Mode {expected_generation_type}",
            revision=1,
            content_hash=ZERO,
        ),
        manifest=_ns(schema_version="2.8", manifest_revision=1, attempts=(attempt,)),
        shots=(_ns(shot_id="shot-mode"),),
        registry=_ns(assets=tuple(assets)),
        asset_paths=asset_paths,
    )
    request = _ns(
        provider_name="provider-mode-test",
        provider_kind="provider-mode-test",
        model_id="model-mode-test",
        provider_profile=_ns(
            profile_id="profile-mode-test",
            profile_version="v1",
            profile_sha256=ZERO,
        ),
        capability_id="capability-mode-test",
        execution_kind=_ns(value="local"),
        billing_kind=_ns(value="local_unmetered"),
        mode=_ns(value=mode),
        prompt_text=f"Prompt for {expected_generation_type}",
        image_bindings=tuple(bindings),
        media_bindings=tuple(media_bindings),
        effective_output=_ns(
            model_dump=lambda **_: {
                "duration_seconds": 5,
                "width": 1280,
                "height": 720,
                "container": "mp4",
                "mime_type": "video/mp4",
                "native_audio": False,
            }
        ),
        continuity_binding=None,
        activation_scope=None,
        output_asset_id="generated-output",
    )
    monkeypatch.setattr(provider_console, "load_production_project", lambda _path: loaded)
    monkeypatch.setattr(
        provider_console,
        "load_video_request_receipt",
        lambda _root, _pointer: request,
    )

    result = provider_console.project_workspace_detail(
        runs, f"mode-{expected_generation_type.lower()}/project.yaml"
    )
    projected = result["attempts"][0]

    assert projected["mode"] == mode
    assert projected["generation_type"] == expected_generation_type
    assert projected["prompt_text"] == f"Prompt for {expected_generation_type}"
    assert [item["role"] for item in projected["input_bindings"]] == [
        *roles,
        *(role for _kind, role in media_roles),
    ]
    assert [item["kind"] for item in projected["input_bindings"]] == [
        *("image" for _role in roles),
        *(kind for kind, _role in media_roles),
    ]
    assert [item["mime_type"] for item in projected["input_bindings"]] == [
        *("image/png" for _role in roles),
        *("video/mp4" for _kind, _role in media_roles),
    ]
    assert all(item["media"]["token"] for item in projected["input_bindings"])
    assert [item["media"]["mime_type"] for item in projected["input_bindings"]] == [
        *("image/png" for _role in roles),
        *("video/mp4" for _kind, _role in media_roles),
    ]


def test_production_detail_keeps_valid_workspace_readable_without_video_attempts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    runs = tmp_path / "runs"
    project_path = _production_workspace(runs, "still-images/project")
    image_path = _write(project_path.parent / "assets" / "scene.png", b"scene-image")
    image_record = _ns(
        asset_id="scene-image",
        asset_type=_ns(value="image"),
        mime_type="image/png",
        size_bytes=11,
        width=1280,
        height=720,
        duration_seconds=None,
        video_metadata=None,
        sha256=ZERO,
        egress=_ns(remote=False),
    )
    image_attempt = _ns(operation="image_generation")
    loaded = _ns(
        root=project_path.parent,
        project=_ns(
            project_id="still-images",
            title="Still Images",
            revision=2,
            content_hash=ZERO,
        ),
        manifest=_ns(
            schema_version="2.8",
            manifest_revision=4,
            attempts=(image_attempt,),
        ),
        shots=(_ns(shot_id="shot-1"),),
        registry=_ns(assets=(image_record,)),
        asset_paths={"scene-image": image_path},
    )
    monkeypatch.setattr(provider_console, "load_production_project", lambda _path: loaded)

    result = provider_console.project_workspace_detail(
        runs, "still-images/project/project.yaml"
    )

    assert result["status"] == "valid"
    assert result["attempts"] == []
    assert result["operation_summary"] == [
        {"operation": "image_generation", "count": 1}
    ]
    assert [item["asset_id"] for item in result["workspace_media"]] == [
        "scene-image"
    ]
    assert result["workspace_media_truncated"] is False
    serialized_public = json.dumps(
        {key: value for key, value in result.items() if key != "_media"}
    )
    assert str(tmp_path) not in serialized_public


def test_production_workspace_media_projection_is_bounded_and_sanitized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    runs = tmp_path / "runs"
    project_path = _production_workspace(runs, "large-registry/project")
    assets = []
    asset_paths = {}
    for index in range(33):
        asset_id = f"image-{index:02d}"
        payload = f"asset-{index:02d}".encode()
        asset_path = _write(project_path.parent / "assets" / f"{asset_id}.png", payload)
        assets.append(
            _ns(
                asset_id=asset_id,
                asset_type=_ns(value="image"),
                mime_type="image/png",
                size_bytes=len(payload),
                width=640,
                height=360,
                duration_seconds=None,
                video_metadata=None,
                sha256=f"{index:064x}",
                egress=_ns(remote=False),
            )
        )
        asset_paths[asset_id] = asset_path
    loaded = _ns(
        root=project_path.parent,
        project=_ns(
            project_id="large-registry",
            title="Large Registry",
            revision=1,
            content_hash=ONE,
        ),
        manifest=_ns(
            schema_version="2.8",
            manifest_revision=9,
            attempts=(_ns(operation="asset_registration"),),
        ),
        shots=(),
        registry=_ns(assets=tuple(reversed(assets))),
        asset_paths=asset_paths,
    )
    monkeypatch.setattr(provider_console, "load_production_project", lambda _path: loaded)

    result = provider_console.project_workspace_detail(
        runs, "large-registry/project/project.yaml"
    )

    assert result["status"] == "valid"
    assert result["attempts"] == []
    assert result["operation_summary"] == [
        {"operation": "asset_registration", "count": 1}
    ]
    assert len(result["workspace_media"]) == 32
    assert [item["asset_id"] for item in result["workspace_media"]] == [
        f"image-{index:02d}" for index in range(32)
    ]
    assert result["workspace_media_truncated"] is True
    serialized_public = json.dumps(
        {key: value for key, value in result.items() if key != "_media"}
    )
    assert str(tmp_path) not in serialized_public


def test_invalid_selected_production_fails_closed_with_sanitized_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    runs = tmp_path / "runs"
    _production_workspace(runs, "broken")

    def fail(_path):
        raise AiVideoError(code="manifest_invalid", user_message="unsafe /private/path", technical_detail="secret", retryable=False)

    monkeypatch.setattr(provider_console, "load_production_project", fail)
    result = provider_console.project_workspace_detail(runs, "broken/project.yaml")
    assert result["status"] == "invalid"
    assert result["error"] == {
        "code": "PRODUCTION_PROJECT_INVALID",
        "message": "该 Production workspace 无法通过严格校验。",
    }
    assert "private" not in json.dumps(result)


def test_invalid_video_request_receipt_fails_closed_instead_of_hiding_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    runs = tmp_path / "runs"
    project_path = _production_workspace(runs, "broken-request")
    request_pointer = _ns(path=Path("state/video-generation/requests/missing.json"))
    state = _ns(request=request_pointer)
    attempt = _ns(operation="video_generation", video_generation_state=state)
    loaded = _ns(
        root=project_path.parent,
        registry=_ns(assets=()),
        manifest=_ns(attempts=(attempt,)),
        asset_paths={},
    )
    monkeypatch.setattr(provider_console, "load_production_project", lambda _path: loaded)
    monkeypatch.setattr(
        provider_console,
        "load_video_request_receipt",
        lambda _root, _pointer: (_ for _ in ()).throw(ValueError("raw /private/request failure")),
    )

    result = provider_console.project_workspace_detail(runs, "broken-request/project.yaml")

    assert result["status"] == "invalid"
    assert result["error"] == {
        "code": "VIDEO_REQUEST_INVALID",
        "message": "该 workspace 的 video request evidence 无法通过严格校验。",
    }
    assert result["attempts"] == []
    assert "private" not in json.dumps(result)


def test_continuity_review_projection_is_exact_sanitized_and_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    runs = tmp_path / "runs"
    project_path = _production_workspace(runs, "continuity/project")
    artifact_bytes = b"exact-fetched-video"
    artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()
    artifact_path = Path(
        f"state/video-generation/fetch/files/{artifact_sha256}.mp4"
    )
    _write(project_path.parent / artifact_path, artifact_bytes)
    constraints = ContinuityConstraintSet.create(
        scene_identity=ContinuityArtifactIdentity(
            artifact_id="scene-cafe", revision=1, content_hash="2" * 64
        ),
        character_identities=(
            ContinuityArtifactIdentity(
                artifact_id="character-alice", revision=1, content_hash="3" * 64
            ),
        ),
        camera_axis="screen left to right",
        framing="medium shot",
        lighting="warm practical light",
        color="amber and teal",
        motion_direction="Alice exits frame right",
        exit_state="Alice is outside the source frame",
        entrance_state="Alice enters target frame from left",
    )
    binding = _ns(
        terminal_frame=_ns(source_shot_id="shot-source"),
        target_shot_id="shot-target",
        target_shot_content_hash="4" * 64,
        constraints=constraints,
    )
    request = _ns(
        continuity_binding=binding,
        activation_scope=_ns(
            request=_ns(
                target_shot_id="shot-target",
                target_shot_content_hash="4" * 64,
            )
        ),
        resolved_generation_hash="5" * 64,
    )
    pointer = _ns(
        artifact_path=artifact_path,
        artifact_sha256=artifact_sha256,
        artifact_size_bytes=len(artifact_bytes),
    )
    state = _ns(
        phase=VideoAttemptPhase.VALIDATE,
        request=object(),
        local_fetch_receipt=pointer,
        fetch_receipt=None,
        continuity_evaluation=None,
    )
    attempt = _ns(
        attempt_id="attempt-1",
        operation="video_generation",
        status=StateCommitStatus.RUNNING,
        video_generation_state=state,
    )
    policy_pointer = _ns(
        policy_id="continuity-policy",
        policy_version="1",
        content_hash="6" * 64,
    )
    policy = _ns(
        policy_id=policy_pointer.policy_id,
        policy_version=policy_pointer.policy_version,
        content_hash=policy_pointer.content_hash,
        semantic_authorities=(AUTOMATIC, HUMAN),
    )
    shots = (
        _ns(
            shot_id="shot-source", scene_id="scene-cafe", intent="Alice exits",
            visual_strategy=_ns(value="generated_video"), duration_policy=None,
            revision=1, content_hash="7" * 64,
        ),
        _ns(
            shot_id="shot-target", scene_id="scene-cafe", intent="Alice enters",
            visual_strategy=_ns(value="generated_video"), duration_policy=None,
            revision=2, content_hash="4" * 64,
        ),
    )
    loaded = _ns(
        root=project_path.parent,
        manifest=_ns(attempts=(attempt,), active_qa_policy=policy_pointer),
        shots=shots,
    )
    monkeypatch.setattr(provider_console, "load_production_project", lambda _path: loaded)
    monkeypatch.setattr(
        provider_console_continuity,
        "load_video_request_receipt",
        lambda _root, _pointer: request,
    )
    monkeypatch.setattr(
        provider_console_continuity,
        "load_local_video_fetch_receipt",
        lambda _root, _pointer: _ns(
            artifact_sha256=artifact_sha256, size_bytes=len(artifact_bytes)
        ),
    )
    monkeypatch.setattr(
        provider_console_continuity, "load_qa_policy", lambda _root, _pointer: policy
    )
    before = {
        path: (path.stat().st_size, path.stat().st_mtime_ns)
        for path in runs.rglob("*") if path.is_file()
    }

    result = provider_console.project_continuity_review(
        runs,
        "continuity/project/project.yaml",
        "attempt-1",
        automatic_evaluator=AUTOMATIC,
        required_reviewer=HUMAN,
    )

    after = {
        path: (path.stat().st_size, path.stat().st_mtime_ns)
        for path in runs.rglob("*") if path.is_file()
    }
    assert before == after
    assert result["review_request"]["attempt_id"] == "attempt-1"
    assert result["review_request"]["required_reviewer"] == HUMAN.model_dump(mode="json")
    assert result["review_request"]["continuity_constraints_hash"] == constraints.content_hash
    assert result["constraints"]["motion_direction"] == "Alice exits frame right"
    assert result["media"]["sha256"] == artifact_sha256
    assert result["media"]["token"] in result["_media"]
    public = json.dumps(
        {key: value for key, value in result.items() if key != "_media"},
        ensure_ascii=False,
    )
    assert str(tmp_path) not in public
    assert "source_path" not in public


def test_continuity_review_projection_rejects_symlinked_media(
    tmp_path: Path
):
    root = tmp_path / "workspace"
    root.mkdir()
    outside = _write(tmp_path / "outside.mp4", b"outside")
    linked = root / "candidate.mp4"
    linked.symlink_to(outside)

    with pytest.raises(ValueError, match="contained"):
        provider_console_continuity.measure_contained_file(linked, root=root)


@pytest.mark.parametrize("workspace", ["../project.yaml", "/tmp/project.yaml", "demo\\project.yaml", "demo/state/manifest.json"])
def test_detail_rejects_unsafe_or_non_workspace_keys(tmp_path: Path, workspace: str):
    runs = tmp_path / "runs"
    runs.mkdir()
    with pytest.raises(ValueError, match="workspace"):
        provider_console.project_workspace_detail(runs, workspace)


def test_legacy_detail_uses_canonical_manifest_and_never_exposes_paths_or_errors(tmp_path: Path):
    runs = tmp_path / "runs"
    manifest_path = runs / "legacy" / "manifest.json"
    manifest = RunManifest(
        run_id="legacy", status="failed", project_config_path="/private/project.yaml",
        final_output="/private/final.mp4",
        shots=[ShotRecord(shot_id="shot-1", status="failed", error={"secret": "raw"})],
    )
    _write(manifest_path, manifest.model_dump_json().encode())

    result = provider_console.project_workspace_detail(runs, "legacy/manifest.json")

    assert result["kind"] == "legacy"
    assert result["run_id"] == "legacy"
    assert result["shots"] == [{"shot_id": "shot-1", "status": "failed", "active_attempt": 0}]
    assert "private" not in json.dumps(result)
    assert "raw" not in json.dumps(result)


def test_cli_writes_one_json_document(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    runs = tmp_path / "runs"
    runs.mkdir()
    assert provider_console.main(["catalog", "--runs-root", str(runs)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["workspaces"] == []


def test_cli_returns_sanitized_json_for_unknown_workspace(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    runs = tmp_path / "runs"
    runs.mkdir()

    assert provider_console.main([
        "detail", "--runs-root", str(runs), "--workspace", "missing/project.yaml",
    ]) == 4
    assert json.loads(capsys.readouterr().out) == {
        "error": {"code": "WORKSPACE_NOT_FOUND", "message": "workspace 不存在。"}
    }
