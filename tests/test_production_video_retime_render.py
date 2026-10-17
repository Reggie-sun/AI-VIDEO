from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from ai_video.production import render_with_hyperframes
from ai_video.production.composition import resolve_composition
from ai_video.production.hashing import seal_artifact
from ai_video.production.hyperframes import (
    _controlled_env,
    audit_hyperframes_source,
)
from ai_video.production.models import (
    AssetRecord,
    AssetRoleRequirement,
    AssetSourceKind,
    AssetType,
    ArtifactReference,
    CompositionSpec,
    DurationPolicy,
    FixedTransform,
    RendererKind,
    RendererAssetBinding,
    RendererSelectionReceipt,
    ToolIdentity,
    VideoAssetMetadata,
    VisualStrategy,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.paths import canonical_video_asset_path
from ai_video.production.state_commit import (
    BeginRenderAttemptRequest,
    ProductionStateCommitter,
    prepare_project_registry_commit,
)
from ai_video.production.video_retime import VideoTimeMap, VideoTimePoint
from production_project_factory import (
    _write_yaml,
    make_composition_spec,
    write_and_load_two_shot_project,
)


def _required_path(
    name: str, *, lock_symlink: bool = False, directory: bool = False
) -> Path:
    value = os.environ.get(name)
    assert value, f"{name} is required when AI_VIDEO_VIDEO_RETIME_RENDERER_GATE=1"
    path = Path(value)
    assert path.is_absolute() and ".." not in path.parts
    resolved = path.resolve(strict=True)
    if lock_symlink:
        assert path == Path(__file__).resolve().parents[1] / "node_modules/.bin/hyperframes"
        assert path.is_symlink() and resolved.is_file()
    elif directory:
        assert path == resolved and path.is_dir() and not path.is_symlink()
    else:
        assert path == resolved and not path.is_symlink() and os.access(path, os.X_OK)
    return path


def _json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _frame_color(frame: int) -> tuple[int, int, int]:
    levels = (20, 74, 128, 182, 236)
    return (
        levels[frame % 5],
        levels[(frame // 5) % 5],
        levels[(frame // 25) % 5],
    )


def _run(
    argv: list[str],
    *,
    timeout: int = 120,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        argv,
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
        env=env,
    )
    assert result.returncode == 0, (
        f"command failed ({result.returncode}): {argv!r}\n"
        f"{result.stderr.decode('utf-8', errors='replace')}"
    )
    return result


def _extract_center_pixels(
    ffmpeg: Path,
    video: Path,
    *,
    width: int,
    height: int,
    frames: tuple[int, ...] | None = None,
) -> tuple[tuple[int, int, int], ...]:
    filters = []
    if frames is not None:
        filters.append("select='" + "+".join(f"eq(n,{frame})" for frame in frames) + "'")
    filters.extend(
        (
            "format=rgb24",
            f"crop=1:1:{width // 2}:{height // 2}",
        )
    )
    result = _run(
        [
            str(ffmpeg),
            "-v",
            "error",
            "-i",
            str(video),
            "-vf",
            ",".join(filters),
            "-fps_mode",
            "passthrough",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ],
        timeout=180,
    )
    assert len(result.stdout) % 3 == 0
    return tuple(
        (result.stdout[offset], result.stdout[offset + 1], result.stdout[offset + 2])
        for offset in range(0, len(result.stdout), 3)
    )


def _closest_source_frame(
    pixel: tuple[int, int, int],
    source_pixels: tuple[tuple[int, int, int], ...],
) -> tuple[int, int, int]:
    ranked = sorted(
        (
            sum((actual - expected) ** 2 for actual, expected in zip(pixel, color)),
            index,
        )
        for index, color in enumerate(source_pixels)
    )
    return ranked[0][1], ranked[0][0], ranked[1][0]


def _retimed_fixture(
    project_root: Path,
    source_video: Path,
    source_sha256: str,
    probe: dict[str, object],
):
    loaded = write_and_load_two_shot_project(
        project_root,
        seconds=(2.0, 5.0),
        decodable_pngs=True,
    )
    stream_list = probe["streams"]
    assert isinstance(stream_list, list)
    video_streams = [item for item in stream_list if item["codec_type"] == "video"]
    assert len(video_streams) == 1
    stream = video_streams[0]
    video_id = "video-retime-fixture"
    source_bytes = source_video.read_bytes()
    artifact_path = canonical_video_asset_path(source_sha256)
    (project_root / artifact_path).write_bytes(source_bytes)
    metadata = VideoAssetMetadata(
        container_name="mp4",
        codec_name=str(stream["codec_name"]),
        width=int(stream["width"]),
        height=int(stream["height"]),
        fps_numerator=24,
        fps_denominator=1,
        duration_milliseconds=5000,
        frame_count=120,
        probe_receipt_id=hashlib.sha256(source_bytes + b"probe").hexdigest(),
        request_receipt_fingerprint=hashlib.sha256(source_bytes + b"request").hexdigest(),
        resolved_generation_hash=hashlib.sha256(source_bytes + b"resolved").hexdigest(),
        provenance_receipt_id=hashlib.sha256(source_bytes + b"provenance").hexdigest(),
    )
    video_asset = AssetRecord(
        asset_id=video_id,
        asset_type=AssetType.VIDEO,
        artifact_path=artifact_path,
        sha256=source_sha256,
        size_bytes=len(source_bytes),
        mime_type="video/mp4",
        duration_seconds=5.0,
        width=64,
        height=64,
        source_kind=AssetSourceKind.IMPORTED,
        tool=ToolIdentity(name="renderer-frame-fixture", version="1"),
        input_fingerprint=source_sha256,
        creation_receipt_id=metadata.provenance_receipt_id,
        usage_license="test-only",
        video_metadata=metadata,
    )
    registry = loaded.registry.model_copy(
        update={
            "schema_version": "2.2",
            "revision_id": "0" * 64,
            "content_hash": "0" * 64,
            "assets": (*loaded.registry.assets, video_asset),
        }
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )

    original_shot = loaded.shots[1]
    video_shot = seal_artifact(
        original_shot.model_copy(
            update={
                "revision": original_shot.revision + 1,
                "content_hash": "0" * 64,
                "duration_policy": DurationPolicy(mode="fixed", seconds=5.0),
                "visual_strategy": VisualStrategy.EXISTING_VIDEO,
                "required_asset_roles": (
                    AssetRoleRequirement(
                        role="video",
                        asset_ids=(video_id,),
                        allowed_asset_types=(AssetType.VIDEO,),
                    ),
                ),
            }
        )
    )
    shot_path = Path("creative/shots/shot-2-video-fixture.yaml")
    _write_yaml(project_root / shot_path, video_shot)
    shot_references = list(loaded.project.artifacts.shots)
    shot_references[1] = ArtifactReference(
        artifact_id=video_shot.artifact_id,
        revision=video_shot.revision,
        content_hash=video_shot.content_hash,
        path=shot_path,
    )
    project = seal_artifact(
        loaded.project.model_copy(
            update={
                "revision": loaded.project.revision + 1,
                "content_hash": "0" * 64,
                "artifacts": loaded.project.artifacts.model_copy(
                    update={"shots": tuple(shot_references)}
                ),
            }
        )
    )

    committer = ProductionStateCommitter(project_root)
    committed = committer.commit(
        prepare_project_registry_commit(
            manifest=loaded.manifest,
            project=project,
            registry=registry,
            attempt_id="video-retime-fixture-import",
        )
    )
    reopened = load_production_project(project_root / "project.yaml")
    assert reopened.manifest == committed
    spec = make_composition_spec()
    time_map = VideoTimeMap(
        points=(
            VideoTimePoint(source_frame=0, output_frame=0),
            VideoTimePoint(source_frame=48, output_frame=24),
            VideoTimePoint(source_frame=72, output_frame=72),
            VideoTimePoint(source_frame=120, output_frame=120),
        ),
        audio_policy="mute",
    )
    layers = list(spec.layers)
    layers[1] = layers[1].model_copy(
        update={
            "asset_role": "video",
            "asset_id": video_id,
            "trim_start_frame": 0,
            "trim_duration_frames": 120,
            "transform": FixedTransform(video_fit="cover"),
            "source_time_map": time_map,
        }
    )
    spec_candidate = spec.model_copy(
        update={
            "schema_version": "2.3",
            "content_hash": "0" * 64,
            "layers": tuple(layers),
        }
    )
    spec = CompositionSpec.model_validate(
        seal_artifact(spec_candidate).model_dump(mode="python")
    )
    timeline = resolve_composition(reopened, spec, renderer_version="0.7.103")
    return reopened, spec, timeline, video_asset, committer


@pytest.mark.skipif(
    os.environ.get("AI_VIDEO_VIDEO_RETIME_RENDERER_GATE") != "1",
    reason="requires the explicit pinned offline HyperFrames render gate",
)
def test_pinned_hyperframes_selects_source_frames_from_piecewise_time_map(
    tmp_path: Path,
):
    repository = Path(__file__).resolve().parents[1]
    binary = _required_path("RETIME_BINARY", lock_symlink=True)
    browser = _required_path("RETIME_BROWSER_PATH")
    unshare = _required_path("RETIME_UNSHARE_PATH")
    ip_path = _required_path("RETIME_IP_PATH")
    bash = _required_path("RETIME_BASH_PATH")
    ffmpeg = _required_path("RETIME_FFMPEG_PATH")
    ffprobe = _required_path("RETIME_FFPROBE_PATH")
    evidence_root = Path(
        _required_path("RETIME_EVIDENCE_ROOT", directory=True)
    )
    assert evidence_root.is_relative_to(repository / "runs")
    run_id = os.environ.get("RETIME_RUN_ID", "retime-proof-001")
    assert run_id and all(char.isalnum() or char in "-_." for char in run_id)
    run_root = evidence_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)

    colors = tuple(_frame_color(index) for index in range(120))
    raw_path = run_root / "source-frames.rgb"
    raw_path.write_bytes(
        b"".join(bytes(color) * (64 * 64) for color in colors)
    )
    source_video = run_root / "source-120f-24fps.mp4"
    encode = _run(
        [
            str(ffmpeg),
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-video_size",
            "64x64",
            "-framerate",
            "24",
            "-i",
            str(raw_path),
            "-frames:v",
            "120",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "0",
            "-pix_fmt",
            "yuv420p",
            "-x264-params",
            "bframes=0:keyint=1:min-keyint=1:scenecut=0",
            "-movflags",
            "+faststart",
            str(source_video),
        ],
        timeout=180,
    )
    probe_result = _run(
        [
            str(ffprobe),
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(source_video),
        ]
    )
    source_probe = json.loads(probe_result.stdout)
    stream_list = source_probe["streams"]
    video_streams = [item for item in stream_list if item["codec_type"] == "video"]
    assert len(video_streams) == 1
    assert int(video_streams[0]["nb_frames"]) == 120
    assert (int(video_streams[0]["width"]), int(video_streams[0]["height"])) == (64, 64)
    source_sha256 = hashlib.sha256(source_video.read_bytes()).hexdigest()
    source_pixels = _extract_center_pixels(
        ffmpeg, source_video, width=64, height=64
    )
    assert len(source_pixels) == 120

    production_root = tmp_path / "production-project"
    loaded, spec, timeline, video_asset, committer = _retimed_fixture(
        production_root, source_video, source_sha256, source_probe
    )
    shot_spans = tuple(
        span for span in timeline.visual_spans if span.shot_id == "shot-2"
    )
    assert timeline.schema_version == "2.3"
    assert [(s.start_frame, s.trim_start_frame) for s in shot_spans[:24]] == [
        (48 + n, 2 * n) for n in range(24)]
    assert [(s.start_frame, s.trim_start_frame) for s in shot_spans[24:72]] == [
        (72 + n, 48 + n // 2) for n in range(48)]
    assert all(s.duration_frames == s.trim_duration_frames == 1 for s in shot_spans[:72])
    assert (shot_spans[-1].start_frame, shot_spans[-1].duration_frames,
            shot_spans[-1].trim_start_frame, shot_spans[-1].trim_duration_frames) == (120, 48, 72, 48)
    assert timeline.total_frames == 168

    _json(run_root / "composition-spec.json", spec.model_dump(mode="json"))
    _json(run_root / "resolved-timeline.json", timeline.model_dump(mode="json"))
    _json(
        run_root / "source-asset-registration.json",
        video_asset.model_dump(mode="json"),
    )
    _json(
        run_root / "source-probe.json",
        {
            "source_sha256": source_sha256,
            "size_bytes": source_video.stat().st_size,
            "probe": source_probe,
            "ffmpeg": str(ffmpeg),
            "ffmpeg_version": _run([str(ffmpeg), "-version"]).stdout.decode().splitlines()[0],
            "encoder_stderr": encode.stderr.decode("utf-8", errors="replace"),
        },
    )

    asset_sources = {
        span.asset_id: loaded.asset_paths[span.asset_id]
        for span in timeline.visual_spans
    }
    selection = RendererSelectionReceipt(
        receipt_id="selection-video-retime-fixture",
        attempt_id="render-video-retime-fixture",
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=loaded.manifest.active_project,
        current_registry=loaded.manifest.active_registry,
    )
    begin_request = BeginRenderAttemptRequest(
        loaded.manifest.manifest_revision,
        None,
        selection,
    )

    namespace = _run(
        [
            str(unshare),
            "--user",
            "--map-root-user",
            "--net",
            "--pid",
            "--fork",
            "--mount-proc",
            str(bash),
            "-ceu",
            '"$P3_IP_PATH" link set lo up; "$P3_IP_PATH" -json addr show',
            "retime-network-audit",
        ],
        timeout=30,
        env=_controlled_env(browser, ip_path),
    )
    namespace_interfaces = json.loads(namespace.stdout)
    assert [item["ifname"] for item in namespace_interfaces] == ["lo"]
    _json(
        run_root / "network-audit.json",
        {"interfaces": namespace_interfaces, "outside_network": "unavailable"},
    )

    activated = render_with_hyperframes(
        committer=committer,
        begin_request=begin_request,
        timeline=timeline,
        asset_sources=asset_sources,
        allowed_asset_root=production_root,
        binary_path=binary,
        browser_path=browser,
        unshare_path=unshare,
        ip_path=ip_path,
        bash_path=bash,
        ffmpeg_path=ffmpeg,
        ffprobe_path=ffprobe,
    )
    assert activated.active_render_state is not None
    final_loaded = load_production_project(production_root / "project.yaml")
    assert final_loaded.render_state is not None
    state = final_loaded.render_state
    paths = committer.render_attempt_paths(selection.attempt_id)
    shutil.copytree(paths.source_root, run_root / "render-source")
    output_path = production_root / state.output.path
    saved_output = run_root / "rendered.mp4"
    shutil.copyfile(output_path, saved_output)

    source_receipt_path = production_root / state.source_receipt.path
    render_receipt_path = production_root / state.render_receipt.path
    source_receipt = json.loads(source_receipt_path.read_text(encoding="utf-8"))
    render_receipt = json.loads(render_receipt_path.read_text(encoding="utf-8"))
    staging_bindings = {
        span.asset_id: RendererAssetBinding(
            asset_id=span.asset_id,
            asset_sha256=span.asset_sha256,
            asset_mime_type=span.asset_mime_type,
            materialized_path=span.materialized_path,
        )
        for span in timeline.visual_spans
    }
    audit_hyperframes_source(
        paths.source_root / "index.html",
        expected_assets=tuple(
            staging_bindings[key] for key in sorted(staging_bindings)
        ),
        expected_timeline=timeline,
    )
    _json(run_root / "renderer-source-receipt.json", source_receipt)
    _json(run_root / "render-receipt.json", render_receipt)
    _json(
        run_root / "render-state.json",
        state.model_dump(mode="json"),
    )
    _json(
        run_root / "renderer-toolchain.json",
        {
            "hyperframes_version": _run([str(binary), "--version"]).stdout.decode().strip(),
            "binary_path": str(binary),
            "binary_target": str(binary.resolve(strict=True)),
            "browser_path": str(browser),
            "ffmpeg_path": str(ffmpeg),
            "ffprobe_path": str(ffprobe),
            "source_sha256": source_sha256,
            "render_sha256": hashlib.sha256(saved_output.read_bytes()).hexdigest(),
            "render_bytes": saved_output.stat().st_size,
            "activated_render_attempt": selection.attempt_id,
            "manifest_render_state_active": True,
            "media_quality_acceptance": "not evaluated",
        },
    )

    local_samples = (0, 1, 23, 24, 26, 70, 71, 72, 73, 95, 119)
    output_indices = tuple(48 + frame for frame in local_samples)
    output_probe_result = _run(
        [
            str(ffprobe),
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(saved_output),
        ]
    )
    output_probe = json.loads(output_probe_result.stdout)
    output_streams = [
        item for item in output_probe["streams"] if item["codec_type"] == "video"
    ]
    assert len(output_streams) == 1
    assert int(output_streams[0]["nb_frames"]) == timeline.total_frames
    output_pixels = _extract_center_pixels(
        ffmpeg,
        saved_output,
        width=int(output_streams[0]["width"]),
        height=int(output_streams[0]["height"]),
        frames=output_indices,
    )
    assert len(output_pixels) == len(local_samples)
    observed = []
    for local_frame, output_frame, pixel in zip(
        local_samples, output_indices, output_pixels
    ):
        if local_frame <= 24:
            expected_source_frame = local_frame * 2
        elif local_frame <= 72:
            expected_source_frame = 48 + (local_frame - 24) // 2
        else:
            expected_source_frame = 72 + local_frame - 72
        actual_source_frame, best_distance, next_distance = _closest_source_frame(
            pixel, source_pixels
        )
        observed.append(
            {
                "output_frame": output_frame,
                "video_local_output_frame": local_frame,
                "expected_source_frame": expected_source_frame,
                "observed_source_frame": actual_source_frame,
                "output_center_rgb": list(pixel),
                "best_squared_rgb_distance": best_distance,
                "next_best_squared_rgb_distance": next_distance,
                "match": actual_source_frame == expected_source_frame,
            }
        )
    _json(
        run_root / "frame-identity-comparison.json",
        {
            "sampling": "ffmpeg decoded center pixels classified against all decoded source frame colors",
            "source_frames": 120,
            "output_frames": timeline.total_frames,
            "segment_anchors_source_output": [[0, 0], [48, 24], [72, 72], [120, 120]],
            "observations": observed,
        },
    )
    assert all(item["match"] for item in observed), observed
