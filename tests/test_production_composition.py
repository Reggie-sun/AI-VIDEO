from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.composition import resolve_composition
from ai_video.production.models import (
    AssetRoleRequirement,
    AssetType,
    CompositionLayerSpec,
    CompositionSpec,
    DurationPolicy,
    MotionDirective,
    RendererKind,
    TransitionKind,
    VisualStrategy,
)
from ai_video.production.paths import (
    _copy_held_fd_to_regular_file_nofollow,
    _create_directory_nofollow,
    _create_regular_file_nofollow,
    _list_regular_files_nofollow,
    _read_regular_file_nofollow,
)
from production_project_factory import (
    make_composition_spec,
    make_loaded_project_and_spec,
    write_and_load_two_shot_project,
)


def _assert_invalid(project, spec) -> AiVideoError:
    with pytest.raises(AiVideoError) as caught:
        resolve_composition(project, spec, renderer_version="0.7.103")
    assert caught.value.code is ErrorCode.COMPOSITION_INVALID
    assert caught.value.retryable is False
    return caught.value


def _replace_shot(project, index: int, **changes):
    shots = list(project.shots)
    shots[index] = shots[index].model_copy(update=changes)
    return project.model_copy(update={"shots": tuple(shots)})


def _replace_asset(project, index: int, **changes):
    assets = list(project.registry.assets)
    assets[index] = assets[index].model_copy(update=changes)
    return project.model_copy(
        update={"registry": project.registry.model_copy(update={"assets": tuple(assets)})}
    )


def test_resolver_uses_explicit_shot_order_not_filename_or_mtime(tmp_path):
    loaded = write_and_load_two_shot_project(
        tmp_path, filenames=("z.png", "a.png")
    )
    spec = make_composition_spec(shot_ids=("shot-2", "shot-1"))
    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")
    assert [span.shot_id for span in timeline.visual_spans] == ["shot-2", "shot-1"]


def test_fixed_seconds_round_up_once_at_shot_boundary(tmp_path):
    loaded = write_and_load_two_shot_project(
        tmp_path, seconds=(1.001, 2.0), fps=24
    )
    timeline = resolve_composition(loaded, make_composition_spec(), "0.7.103")
    assert [(span.start_frame, span.duration_frames) for span in timeline.visual_spans] == [
        (0, 25),
        (25, 48),
    ]


def test_cut_keeps_integer_frame_and_sample_boundaries(tmp_path):
    timeline = resolve_composition(
        write_and_load_two_shot_project(tmp_path, seconds=(2.0, 2.0), fps=24),
        make_composition_spec(sample_rate=48_000),
        "0.7.103",
    )
    assert timeline.visual_spans[1].start_frame == 48
    assert timeline.visual_spans[1].start_sample == 96_000
    assert timeline.total_frames == 96
    assert timeline.total_samples == 192_000


def test_same_resolved_inputs_have_same_fingerprint_after_mtime_change(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    first = resolve_composition(loaded, spec, "0.7.103")
    os.utime(
        loaded.asset_paths[spec.layers[0].asset_id],
        (1_900_000_000, 1_900_000_000),
    )
    second = resolve_composition(loaded, spec, "0.7.103")
    assert second.composition_fingerprint == first.composition_fingerprint


@pytest.mark.parametrize(
    "shot_ids",
    [
        ("shot-1", "shot-1"),
        ("shot-1", "missing-shot"),
    ],
)
def test_rejects_duplicate_or_missing_shot_ids(tmp_path, shot_ids):
    loaded = write_and_load_two_shot_project(tmp_path)
    _assert_invalid(loaded, make_composition_spec().model_copy(update={"shot_ids": shot_ids}))


def test_rejects_empty_model_construct_inputs(tmp_path):
    loaded = write_and_load_two_shot_project(tmp_path)
    valid = make_composition_spec()
    empty_shots = CompositionSpec.model_construct(**{**valid.__dict__, "shot_ids": ()})
    empty_layers = CompositionSpec.model_construct(**{**valid.__dict__, "layers": ()})
    _assert_invalid(loaded, empty_shots)
    _assert_invalid(loaded, empty_layers)
    with pytest.raises(AiVideoError) as caught:
        resolve_composition(loaded, valid, "")
    assert caught.value.code is ErrorCode.COMPOSITION_INVALID


def test_rejects_missing_asset_and_loaded_mapping_mismatch(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    missing = spec.model_copy(
        update={
            "layers": (
                spec.layers[0].model_copy(update={"asset_id": "missing"}),
                spec.layers[1],
            )
        }
    )
    _assert_invalid(loaded, missing)

    swapped_mapping = dict(loaded.asset_paths)
    swapped_mapping["image-shot-1"] = loaded.asset_paths["image-shot-2"]
    _assert_invalid(loaded.model_copy(update={"asset_paths": swapped_mapping}), spec)


def test_rejects_registry_path_mismatch_and_internal_symlink(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    mismatched = _replace_asset(
        loaded,
        0,
        artifact_path=loaded.registry.assets[1].artifact_path,
    )
    _assert_invalid(mismatched, spec)

    asset_dir = tmp_path / "assets/files"
    backing = tmp_path / "assets/backing"
    asset_dir.rename(backing)
    asset_dir.symlink_to(backing, target_is_directory=True)
    _assert_invalid(loaded, spec)


def test_rejects_wrong_asset_hash(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    _assert_invalid(_replace_asset(loaded, 0, sha256="f" * 64), spec)


@pytest.mark.parametrize("mode", ["voice_driven", "content_driven"])
def test_rejects_non_fixed_duration(tmp_path, mode):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    duration = DurationPolicy(mode=mode, minimum_seconds=1.0)
    _assert_invalid(_replace_shot(loaded, 0, duration_policy=duration), spec)


@pytest.mark.parametrize(
    "changes",
    [
        {"trim_start_frame": 1},
        {"trim_duration_frames": 12},
    ],
)
def test_rejects_non_default_trim(tmp_path, changes):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    layers = (spec.layers[0].model_copy(update=changes), spec.layers[1])
    _assert_invalid(loaded, spec.model_copy(update={"layers": layers}))


def test_rejects_duplicate_layer_id_and_duplicate_z_order(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    duplicate_id = spec.layers[0].model_copy(
        update={"shot_id": "shot-2", "asset_id": "image-shot-2"}
    )
    _assert_invalid(loaded, spec.model_copy(update={"layers": (*spec.layers, duplicate_id)}))

    duplicate_z = CompositionLayerSpec(
        layer_id="layer-shot-1-second",
        shot_id="shot-1",
        asset_role="still",
        asset_id="image-shot-1",
        z_index=0,
    )
    _assert_invalid(loaded, spec.model_copy(update={"layers": (*spec.layers, duplicate_z)}))


def test_rejects_layer_shot_role_and_asset_binding_mismatches(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    cases = [
        spec.layers[0].model_copy(update={"shot_id": "unordered"}),
        spec.layers[0].model_copy(update={"asset_role": "undeclared"}),
        spec.layers[0].model_copy(update={"asset_id": "image-shot-2"}),
    ]
    for layer in cases:
        _assert_invalid(
            loaded,
            spec.model_copy(update={"layers": (layer, spec.layers[1])}),
        )


def test_rejects_role_or_asset_that_is_not_image(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    role = AssetRoleRequirement(
        role="still",
        asset_ids=("image-shot-1",),
        allowed_asset_types=(AssetType.VIDEO,),
    )
    _assert_invalid(_replace_shot(loaded, 0, required_asset_roles=(role,)), spec)
    _assert_invalid(_replace_asset(loaded, 0, asset_type=AssetType.VIDEO), spec)


@pytest.mark.parametrize(
    ("filename", "mime_type"),
    [
        ("shot-1.jpg", "image/png"),
        ("shot-1.png", "image/jpeg"),
        ("shot-1.svg", "image/svg+xml"),
        ("shot-1.html", "text/html"),
    ],
)
def test_rejects_non_raster_mime_magic_extension_triples(
    tmp_path, filename, mime_type
):
    loaded = write_and_load_two_shot_project(
        tmp_path, filenames=(filename, "shot-2.png")
    )
    loaded = _replace_asset(loaded, 0, mime_type=mime_type)
    _assert_invalid(loaded, make_composition_spec())


def test_rejects_motion_directives(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    directive = MotionDirective(kind="pan", parameters={"x": 1})
    _assert_invalid(_replace_shot(loaded, 0, motion_directives=(directive,)), spec)


@pytest.mark.parametrize(
    "strategy",
    [
        VisualStrategy.IMAGE_MOTION,
        VisualStrategy.MOTION_GRAPHICS,
        VisualStrategy.GENERATED_VIDEO,
        VisualStrategy.EXISTING_VIDEO,
        VisualStrategy.HYBRID,
    ],
)
def test_rejects_non_static_visual_strategies(tmp_path, strategy):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    _assert_invalid(_replace_shot(loaded, 0, visual_strategy=strategy), spec)


@pytest.mark.parametrize(
    "changes",
    [
        {"kind": TransitionKind.CROSSFADE},
        {"duration_frames": 1},
        {"from_shot_id": "shot-2", "to_shot_id": "shot-1"},
    ],
)
def test_rejects_invalid_transitions(tmp_path, changes):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    transition = spec.transitions[0].model_copy(update=changes)
    _assert_invalid(loaded, spec.model_copy(update={"transitions": (transition,)}))


def test_rejects_unsupported_renderer_and_policy(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    _assert_invalid(
        loaded,
        spec.model_copy(update={"requested_renderer": RendererKind.REMOTION}),
    )
    policy = loaded.project.renderer_policy.model_copy(update={"allowed": ("remotion",)})
    project = loaded.project.model_copy(update={"renderer_policy": policy})
    _assert_invalid(loaded.model_copy(update={"project": project}), spec)


@pytest.mark.parametrize("exception", [OSError("read failed"), ValueError("unsafe")])
def test_maps_path_layer_failures_to_composition_invalid(tmp_path, monkeypatch, exception):
    loaded, spec = make_loaded_project_and_spec(tmp_path)

    def fail(*args, **kwargs):
        raise exception

    monkeypatch.setattr("ai_video.production.composition._read_regular_file_nofollow", fail)
    _assert_invalid(loaded, spec)


def test_materialized_paths_use_full_hash_and_canonical_suffix(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    timeline = resolve_composition(loaded, spec, "0.7.103")
    assert timeline.visual_spans[0].materialized_path == Path(
        f"assets/{loaded.registry.assets[0].sha256}.png"
    )


@pytest.mark.parametrize(
    ("filename", "mime_type", "payload", "canonical_suffix"),
    [
        ("positive.jpeg", "image/jpeg", b"\xff\xd8\xfffixture", ".jpg"),
        ("positive.webp", "image/webp", b"RIFF\x08\x00\x00\x00WEBPfixture", ".webp"),
    ],
)
def test_accepts_registered_jpeg_and_webp_rasters(
    tmp_path, filename, mime_type, payload, canonical_suffix
):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    source = tmp_path / "assets/files" / filename
    source.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    loaded = _replace_asset(
        loaded,
        0,
        artifact_path=source.relative_to(tmp_path),
        sha256=digest,
        size_bytes=len(payload),
        mime_type=mime_type,
    )
    asset_paths = dict(loaded.asset_paths)
    asset_paths["image-shot-1"] = source
    loaded = loaded.model_copy(update={"asset_paths": asset_paths})
    timeline = resolve_composition(loaded, spec, "0.7.103")
    assert timeline.visual_spans[0].materialized_path == Path(
        f"assets/{digest}{canonical_suffix}"
    )


def test_nofollow_primitives_create_list_read_and_hold_verification_fd(tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"source-bytes")
    source_fd = os.open(source, os.O_RDONLY)
    os.lseek(source_fd, 3, os.SEEK_SET)
    try:
        root = _create_directory_nofollow(
            tmp_path / "bundle", contained_by=tmp_path, mode=0o700
        )
        created = _create_regular_file_nofollow(
            root / "created.bin", data=b"created", contained_by=root
        )
        assert created.data == b"created"
        assert _read_regular_file_nofollow(
            root / "created.bin", contained_by=root
        ).file_sha256 == created.file_sha256
        with _copy_held_fd_to_regular_file_nofollow(
            source_fd,
            root / "verified.bin",
            contained_by=root,
        ) as verified:
            assert os.read(verified.fd, 32) == b"source-bytes"
            verified_fd = verified.fd
        assert os.lseek(source_fd, 0, os.SEEK_CUR) == 3
        with pytest.raises(OSError):
            os.fstat(verified_fd)
        assert _list_regular_files_nofollow(root) == {
            Path("created.bin"),
            Path("verified.bin"),
        }
    finally:
        os.close(source_fd)


def test_nofollow_list_rejects_symlink_entries(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "target").write_bytes(b"target")
    (root / "link").symlink_to(root / "target")
    with pytest.raises(ValueError, match="symlink"):
        _list_regular_files_nofollow(root)
