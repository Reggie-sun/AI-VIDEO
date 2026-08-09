from __future__ import annotations

import hashlib
import inspect
import json
import math
import os
import shutil
import subprocess
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

import pytest
import ai_video.production as production

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.composition import timeline_fingerprint
from ai_video.production.hashing import seal_artifact
from ai_video.production.hyperframes import (
    OFFLINE_ENV,
    HyperFramesAdapter,
    HyperFramesRenderAttempt,
    RendererAttemptError,
    RendererCommandResult,
    _NetworkIsolatedHyperFramesRunner,
    _capture_safe_boundary_percent,
    _controlled_env,
    _css_visibility_keyframes,
    _parse_source_document,
    _render_with_hyperframes,
    _renderer_tool_root,
    _sealed_json_bytes,
    _seconds,
    _validate_local_relative_url,
    audit_hyperframes_source,
    materialize_hyperframes_source,
    prepare_durable_render_artifacts,
)
from ai_video.production.models import (
    DeliveryProfile,
    FixedTransform,
    RendererIdentity,
    RendererKind,
    RendererSourceReceipt,
    RendererSelectionReceipt,
    RenderReceipt,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    ResolvedTimeline,
    ResolvedVisualSpan,
    SourceReference,
    TransitionKind,
    TransitionSpec,
)
from ai_video.production.paths import (
    _copy_held_fd_to_regular_file_nofollow,
    canonical_render_state_path,
    canonical_renderer_source_receipt_path,
)
from ai_video.production.state_commit import PreparedArtifact
from ai_video.production.state_commit import (
    ActivateRenderStateRequest,
    BeginRenderAttemptRequest,
    CommitPhase,
    ProductionStateCommitter,
    RecordRenderFailureRequest,
    StateCommitRequest,
    prepare_project_registry_commit,
)
from ai_video.production.project import load_production_project
from ai_video.production.models import ProductionManifest, StateCommitStatus
import production_project_factory as project_factory


FIXTURE_ROOT = Path(__file__).parent / "fixtures/hyperframes/silent_image"
RED_PNG = (
    FIXTURE_ROOT
    / "source/assets/1ac67c3a1c909b3356cf6ff490c0f88b8a30ef4c28ca579657f6007146abe71c.png"
).read_bytes()
BLUE_PNG = (
    FIXTURE_ROOT
    / "source/assets/a99284a70ff9a9ab8aec0eed52c3b9bf7a243628820814d0e6bca45445ce2e3f.png"
).read_bytes()
RED_HASH = hashlib.sha256(RED_PNG).hexdigest()
BLUE_HASH = hashlib.sha256(BLUE_PNG).hexdigest()


def _span(
    *,
    layer_id: str,
    shot_id: str,
    asset_id: str,
    digest: str,
    start_frame: int,
    z_index: int = 0,
    opacity_milli: int = 1000,
) -> ResolvedVisualSpan:
    return ResolvedVisualSpan(
        layer_id=layer_id,
        shot_id=shot_id,
        asset_role="still",
        asset_id=asset_id,
        asset_sha256=digest,
        asset_mime_type="image/png",
        materialized_path=Path(f"assets/{digest}.png"),
        start_frame=start_frame,
        duration_frames=5,
        start_sample=start_frame * 2_000,
        duration_samples=10_000,
        trim_start_frame=0,
        trim_duration_frames=None,
        transform=FixedTransform(
            translate_x_px=3 if start_frame else 0,
            translate_y_px=4 if start_frame else 0,
            scale_x_milli=900 if start_frame else 1000,
            scale_y_milli=800 if start_frame else 1000,
            rotation_millidegrees=1250 if start_frame else 0,
        ),
        opacity_milli=opacity_milli,
        z_index=z_index,
        incoming_transition=(
            TransitionSpec(
                from_shot_id="shot-1",
                to_shot_id="shot-2",
                kind=TransitionKind.CUT,
                duration_frames=0,
            )
            if start_frame
            else None
        ),
    )


def make_resolved_timeline(
    *, order: tuple[str, ...] = ("shot-1", "shot-2"), same_asset: bool = False
) -> ResolvedTimeline:
    by_shot = {
        "shot-1": _span(
            layer_id="layer-red",
            shot_id="shot-1",
            asset_id="image-red",
            digest=RED_HASH,
            start_frame=0,
            z_index=1,
        ),
        "shot-2": _span(
            layer_id="layer-blue",
            shot_id="shot-2",
            asset_id="image-blue" if not same_asset else "image-red-copy",
            digest=BLUE_HASH if not same_asset else RED_HASH,
            start_frame=5,
            z_index=2,
            opacity_milli=750,
        ),
    }
    spans = tuple(by_shot[item] for item in order)
    provisional = ResolvedTimeline(
        artifact_id="timeline-main",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="resolve-composition-main",
        source_provenance=(SourceReference(kind="derived", reference="composition-main"),),
        timeline_id="timeline-main-r1",
        composition_spec_id="composition-main",
        composition_spec_revision=1,
        composition_spec_hash="1" * 64,
        delivery_profile=DeliveryProfile(width=320, height=180, fps=24),
        sample_rate=48_000,
        renderer=RendererIdentity(kind=RendererKind.HYPERFRAMES, version="0.7.103"),
        visual_spans=spans,
        total_frames=10,
        total_samples=20_000,
        composition_fingerprint="0" * 64,
    )
    return seal_artifact(
        provisional.model_copy(
            update={"composition_fingerprint": timeline_fingerprint(provisional)}
        )
    )


def _reseal_timeline(
    timeline: ResolvedTimeline, **changes: object
) -> ResolvedTimeline:
    provisional = timeline.model_copy(
        update={
            **changes,
            "content_hash": "0" * 64,
            "composition_fingerprint": "0" * 64,
        }
    )
    return seal_artifact(
        provisional.model_copy(
            update={"composition_fingerprint": timeline_fingerprint(provisional)}
        )
    )


def make_asset_sources(tmp_path: Path, timeline: ResolvedTimeline) -> dict[str, Path]:
    assets = tmp_path / "inputs"
    assets.mkdir(parents=True, exist_ok=True)
    red = assets / "red.png"
    blue = assets / "blue.png"
    red.write_bytes(RED_PNG)
    blue.write_bytes(BLUE_PNG)
    return {
        span.asset_id: red if span.asset_sha256 == RED_HASH else blue
        for span in timeline.visual_spans
    }


def _materialize(tmp_path: Path, timeline: ResolvedTimeline | None = None):
    timeline = timeline or make_resolved_timeline()
    return materialize_hyperframes_source(
        timeline,
        asset_sources=make_asset_sources(tmp_path, timeline),
        allowed_asset_root=tmp_path,
        staging_root=tmp_path / "staging",
        allowed_staging_parent=tmp_path,
    )


def _assert_source_invalid(call) -> AiVideoError:
    with pytest.raises(AiVideoError) as caught:
        call()
    assert caught.value.code is ErrorCode.RENDERER_SOURCE_INVALID
    assert caught.value.retryable is False
    return caught.value


def test_source_is_materialized_only_from_timeline_and_bound_assets(tmp_path):
    timeline = make_resolved_timeline(order=("shot-2", "shot-1"))
    result = _materialize(tmp_path, timeline)
    assert result.source_sha256 == hashlib.sha256(result.index_path.read_bytes()).hexdigest()
    html = result.index_path.read_text(encoding="utf-8")
    parsed = _parse_source_document(html)
    assert parsed.stage_attributes["data-no-timeline"] is None
    assert parsed.stage_attributes["data-start"] == "0"
    assert parsed.stage_attributes["data-duration"] == _seconds(10, 24)
    assert [attrs["data-shot-id"] for attrs in parsed.clip_attributes] == [
        "shot-2",
        "shot-1",
    ]
    assert all("data-start" not in attrs for attrs in parsed.clip_attributes)
    assert all("data-duration" not in attrs for attrs in parsed.clip_attributes)
    assert html.count("animation-duration:") == 2
    assert html.count("@keyframes p3-layer-") == 2


def test_materializer_validates_target_containment_before_any_mkdir_or_copy(tmp_path):
    timeline = make_resolved_timeline()
    sources = make_asset_sources(tmp_path, timeline)
    unsafe = timeline.model_copy(
        update={
            "visual_spans": (
                timeline.visual_spans[0],
                timeline.visual_spans[1].model_copy(
                    update={"materialized_path": Path("../escape.png")}
                ),
            )
        }
    )
    _assert_source_invalid(
        lambda: materialize_hyperframes_source(
            unsafe,
            asset_sources=sources,
            allowed_asset_root=tmp_path,
            staging_root=tmp_path / "staging",
            allowed_staging_parent=tmp_path,
        )
    )
    assert not (tmp_path / "staging").exists()


def test_materializer_rejects_unsealed_timeline_and_existing_staging_before_writes(
    tmp_path,
):
    timeline = make_resolved_timeline()
    sources = make_asset_sources(tmp_path, timeline)
    invalid = timeline.model_copy(update={"content_hash": "f" * 64})
    _assert_source_invalid(
        lambda: materialize_hyperframes_source(
            invalid,
            asset_sources=sources,
            allowed_asset_root=tmp_path,
            staging_root=tmp_path / "staging",
            allowed_staging_parent=tmp_path,
        )
    )
    assert not (tmp_path / "staging").exists()
    (tmp_path / "staging").mkdir()
    _assert_source_invalid(
        lambda: materialize_hyperframes_source(
            timeline,
            asset_sources=sources,
            allowed_asset_root=tmp_path,
            staging_root=tmp_path / "staging",
            allowed_staging_parent=tmp_path,
        )
    )
    assert list((tmp_path / "staging").iterdir()) == []


def test_conflicting_repeated_asset_id_is_rejected_before_staging_exists(tmp_path):
    timeline = make_resolved_timeline()
    conflicting = timeline.visual_spans[1].model_copy(
        update={"asset_id": timeline.visual_spans[0].asset_id}
    )
    timeline = _reseal_timeline(
        timeline,
        visual_spans=(timeline.visual_spans[0], conflicting),
    )
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    red = inputs / "red.png"
    red.write_bytes(RED_PNG)
    _assert_source_invalid(
        lambda: materialize_hyperframes_source(
            timeline,
            asset_sources={"image-red": red},
            allowed_asset_root=tmp_path,
            staging_root=tmp_path / "staging",
            allowed_staging_parent=tmp_path,
        )
    )
    assert not (tmp_path / "staging").exists()


def test_quantized_seek_failure_is_rejected_before_staging_exists(tmp_path):
    total_frames = 99_998_442_844_803
    frame = 99_998_442_844_801
    timeline = make_resolved_timeline()
    span = timeline.visual_spans[0].model_copy(
        update={"start_frame": frame, "duration_frames": 1}
    )
    timeline = _reseal_timeline(
        timeline,
        delivery_profile=timeline.delivery_profile.model_copy(update={"fps": 23}),
        visual_spans=(span,),
        total_frames=total_frames,
        total_samples=0,
    )
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    red = inputs / "red.png"
    red.write_bytes(RED_PNG)
    _assert_source_invalid(
        lambda: materialize_hyperframes_source(
            timeline,
            asset_sources={"image-red": red},
            allowed_asset_root=tmp_path,
            staging_root=tmp_path / "staging",
            allowed_staging_parent=tmp_path,
        )
    )
    assert not (tmp_path / "staging").exists()


def test_materializer_maps_raster_validation_failure_to_renderer_source_invalid(
    tmp_path,
):
    timeline = make_resolved_timeline()
    sources = make_asset_sources(tmp_path, timeline)
    wrong_suffix = sources["image-red"].with_suffix(".jpg")
    sources["image-red"].rename(wrong_suffix)
    sources["image-red"] = wrong_suffix
    _assert_source_invalid(
        lambda: materialize_hyperframes_source(
            timeline,
            asset_sources=sources,
            allowed_asset_root=tmp_path,
            staging_root=tmp_path / "staging",
            allowed_staging_parent=tmp_path,
        )
    )
    assert not (tmp_path / "staging").exists()


@pytest.mark.parametrize("location", ["contained", "external"])
def test_materializer_rejects_asset_symlink_without_following_it(tmp_path, location):
    timeline = make_resolved_timeline()
    sources = make_asset_sources(tmp_path, timeline)
    target = tmp_path / "inputs/red.png"
    backing = (tmp_path / "inputs/backing.png") if location == "contained" else (tmp_path.parent / f"{tmp_path.name}-external.png")
    backing.write_bytes(RED_PNG)
    target.unlink()
    target.symlink_to(backing)
    _assert_source_invalid(
        lambda: materialize_hyperframes_source(
            timeline,
            asset_sources=sources,
            allowed_asset_root=tmp_path,
            staging_root=tmp_path / "staging",
            allowed_staging_parent=tmp_path,
        )
    )
    assert not (tmp_path / "staging").exists()


def test_nofollow_reader_detects_inode_swap_between_lstat_and_open(
    tmp_path, monkeypatch
):
    from ai_video.production.paths import _read_regular_file_nofollow

    source = tmp_path / "asset.png"
    source.write_bytes(RED_PNG)
    original_open = os.open
    swapped = False

    def swap_then_open(path, flags, *args, **kwargs):
        nonlocal swapped
        if path == source.name and kwargs.get("dir_fd") is not None and not swapped:
            swapped = True
            source.rename(tmp_path / "detached.png")
            source.write_bytes(BLUE_PNG)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", swap_then_open)
    with pytest.raises(ValueError, match="changed during open"):
        _read_regular_file_nofollow(source, contained_by=tmp_path)


def test_materializer_deduplicates_physical_hash_path_but_preserves_bindings(tmp_path):
    timeline = make_resolved_timeline(same_asset=True)
    result = _materialize(tmp_path, timeline)
    assert [item.asset_id for item in result.asset_bindings] == [
        "image-red",
        "image-red-copy",
    ]
    assert len({item.materialized_path for item in result.asset_bindings}) == 1
    assert len(tuple((result.root / "assets").iterdir())) == 1


def test_multiple_same_shot_layers_share_interval_and_keep_opacity_and_z_order(
    tmp_path,
):
    timeline = make_resolved_timeline()
    extra = timeline.visual_spans[0].model_copy(
        update={"layer_id": "layer-red-overlay", "opacity_milli": 500, "z_index": 3}
    )
    timeline = _reseal_timeline(
        timeline,
        visual_spans=(timeline.visual_spans[0], extra, timeline.visual_spans[1]),
    )
    result = _materialize(tmp_path, timeline)
    parsed = _parse_source_document(result.index_path.read_text(encoding="utf-8"))
    assert [item["data-start-frame"] for item in parsed.clip_attributes] == [
        "0",
        "0",
        "5",
    ]
    html = result.index_path.read_text(encoding="utf-8")
    assert 'style="z-index:3"' in html
    assert "{opacity:0.5}" in html


def test_source_snapshot_applies_transform_origin_opacity_and_z_index_exactly(tmp_path):
    result = _materialize(tmp_path)
    html = result.index_path.read_text(encoding="utf-8")
    assert "translate(3px,4px) scale(0.9,0.8) rotate(1.25deg)" in html
    assert "transform-origin:0 0" in html
    assert 'style="z-index:2"' in html
    assert "{opacity:0.75}" in html


def test_static_source_root_uses_boolean_data_no_timeline_contract(tmp_path):
    result = _materialize(tmp_path)
    parsed = _parse_source_document(result.index_path.read_text(encoding="utf-8"))
    assert parsed.stage_attributes["data-no-timeline"] is None
    source = result.index_path.read_text(encoding="utf-8").replace(
        "data-no-timeline ", 'data-no-timeline="false" '
    )
    result.index_path.write_text(source, encoding="utf-8")
    _assert_source_invalid(
        lambda: audit_hyperframes_source(
            result.index_path,
            expected_assets=result.asset_bindings,
            expected_timeline=result.timeline,
        )
    )


def test_capture_safe_cut_10_frames_at_24fps_maps_between_frame_4_and_5():
    duration = _seconds(10, 24)
    offset = _capture_safe_boundary_percent(
        5, total_frames=10, fps=24, serialized_duration=duration
    )
    assert duration == "0.416666667"
    assert offset == "44.999999964%"
    mapped = Decimal(offset.removesuffix("%")) * Decimal(duration) / Decimal(100)
    assert Decimal(4) / Decimal(24) < mapped < Decimal(5) / Decimal(24)
    duration_ms = float(duration) * 1000.0
    previous = (math.floor((4 / 24) * 24 + 1e-9) / 24 * 1000.0) / duration_ms
    current = (math.floor((5 / 24) * 24 + 1e-9) / 24 * 1000.0) / duration_ms
    assert previous < float(offset.removesuffix("%")) / 100.0 < current


@pytest.mark.parametrize(
    ("start_frame", "end_frame"), [(0, 5), (5, 10), (10, 15)]
)
def test_capture_safe_keyframes_cover_first_middle_last_intervals(
    start_frame, end_frame
):
    source = _css_visibility_keyframes(
        "layer",
        start_frame=start_frame,
        end_frame=end_frame,
        total_frames=15,
        fps=24,
        serialized_duration=_seconds(15, 24),
        target_opacity="0.75",
    )
    assert source.startswith("@keyframes layer{")
    assert "opacity:0.75" in source
    if start_frame:
        start = _capture_safe_boundary_percent(
            start_frame,
            total_frames=15,
            fps=24,
            serialized_duration=_seconds(15, 24),
        )
        assert source.count(start) == 2
    if end_frame < 15:
        end = _capture_safe_boundary_percent(
            end_frame,
            total_frames=15,
            fps=24,
            serialized_duration=_seconds(15, 24),
        )
        assert source.count(end) == 2


def test_capture_safe_boundary_prior_seconds_order_counterexample_still_fails_closed():
    total_frames, fps, frame = 99_998_442_844_803, 23, 99_998_442_844_801
    duration = _seconds(total_frames, fps)
    target = (Decimal(frame) - Decimal("0.5")) / Decimal(fps)
    offset = (target * Decimal(100) / Decimal(duration)).quantize(
        Decimal("0.000000000001"), rounding=ROUND_HALF_EVEN
    )
    assert duration == "4347758384556.652173913"
    assert format(offset, "f") == "99.999999999997"
    _assert_source_invalid(
        lambda: _capture_safe_boundary_percent(
            frame, total_frames=total_frames, fps=fps, serialized_duration=duration
        )
    )


@pytest.mark.parametrize(
    ("total_frames", "fps", "frame", "expected_duration", "expected_offset"),
    [
        (571_645_132_898_494, 102, 238_889_121_248_512, "5604364048024.450980392", "41.789758628266"),
        (233_828_343_456_133, 115, 129_039_679_542_247, "2033289943096.808695652", "55.18564500563"),
        (5_474_664_941_385_873, 178, 1_884_030_073_746_253, "30756544614527.376404494", "34.413614237903"),
    ],
)
def test_capture_safe_boundary_hyperframes_quantized_seek_counterexamples_fail_closed(
    total_frames, fps, frame, expected_duration, expected_offset
):
    duration = _seconds(total_frames, fps)
    target = (Decimal(frame) - Decimal("0.5")) / Decimal(fps)
    offset = (target * Decimal(100) / Decimal(duration)).quantize(
        Decimal("0.000000000001"), rounding=ROUND_HALF_EVEN
    )
    assert duration == expected_duration
    assert format(offset, "f").rstrip("0").rstrip(".") == expected_offset
    _assert_source_invalid(
        lambda: _capture_safe_boundary_percent(
            frame, total_frames=total_frames, fps=fps, serialized_duration=duration
        )
    )


@pytest.mark.parametrize(
    "replacement",
    [
        ('src="assets/', 'src="https://example.invalid/'),
        ('src="assets/', 'src="../assets/'),
        ('src="assets/', 'src="data:image/png;base64,'),
        ('<style>', '<style>@import "evil.css";'),
        ('</body>', '<script>fetch("https://example.invalid")</script></body>'),
        ('<head>', '<head><link rel="stylesheet" href="evil.css">'),
        ('data-no-timeline ', ''),
        ('data-start-frame="0"', 'data-start="0" data-start-frame="0"'),
        ('data-duration-frames="5"', 'data-duration="1" data-duration-frames="5"'),
        ('data-start-sample="0"', 'data-start-sample="1"'),
        ('animation-fill-mode:both', 'animation-fill-mode:none'),
        ('animation-play-state:paused', 'animation-play-state:running'),
        ('animation-timing-function:step-end', 'animation-timing-function:linear'),
        ('data-timeline-fingerprint="', 'data-timeline-fingerprint="f'),
    ],
)
def test_source_audit_rejects_structural_url_timing_and_animation_drift(
    tmp_path, replacement
):
    old, new = replacement
    result = _materialize(tmp_path)
    source = result.index_path.read_text(encoding="utf-8")
    assert old in source
    result.index_path.write_text(source.replace(old, new, 1), encoding="utf-8")
    _assert_source_invalid(
        lambda: audit_hyperframes_source(
            result.index_path,
            expected_assets=result.asset_bindings,
            expected_timeline=result.timeline,
        )
    )


@pytest.mark.parametrize(
    "forbidden",
    ["http://", "//cdn.invalid", "fetch(", "XMLHttpRequest", "WebSocket(", "Math.random(", "Date.now(", "new Date(", "performance.now("],
)
def test_source_audit_rejects_network_and_wall_clock_inputs(tmp_path, forbidden):
    result = _materialize(tmp_path)
    source = result.index_path.read_text(encoding="utf-8").replace(
        "</body>", f"<!-- {forbidden} --></body>"
    )
    result.index_path.write_text(source, encoding="utf-8")
    _assert_source_invalid(
        lambda: audit_hyperframes_source(
            result.index_path,
            expected_assets=result.asset_bindings,
            expected_timeline=result.timeline,
        )
    )


def test_parser_enumerates_every_url_bearing_surface():
    parsed = _parse_source_document(
        """<!doctype html><html><head><style>
        .a{background:url('style.png')}
        </style></head><body><div id="stage" data-no-timeline>
        <img class="clip" src="src.png" srcset="one.png 1x, two.png 2x"
             poster="poster.png" style="background:url(inline.png)">
        <a href="href.png"></a></div></body></html>"""
    )
    assert parsed.media_urls == {
        "src.png",
        "one.png",
        "two.png",
        "poster.png",
    }
    assert parsed.all_urls == {
        "src.png",
        "one.png",
        "two.png",
        "poster.png",
        "inline.png",
        "href.png",
        "style.png",
    }
    assert parsed.css_imports == ()


def test_source_audit_rejects_spaced_quoted_css_import(tmp_path):
    result = _materialize(tmp_path)
    source = result.index_path.read_text(encoding="utf-8").replace(
        "<style>", '<style>@import "../../secret file.css";'
    )
    result.index_path.write_text(source, encoding="utf-8")
    _assert_source_invalid(
        lambda: audit_hyperframes_source(
            result.index_path,
            expected_assets=result.asset_bindings,
            expected_timeline=result.timeline,
        )
    )


@pytest.mark.parametrize(
    "url",
    [
        "assets/%2e%2e/secret.png",
        "assets/%2Fsecret.png",
        "assets/%5csecret.png",
        "assets/%252e%252e/secret.png",
        "assets/image.png%00.css",
        "assets/image\x00.png",
    ],
)
def test_local_url_validation_rejects_encoded_or_nul_noncanonical_forms(url):
    _assert_source_invalid(lambda: _validate_local_relative_url(url))


def test_source_audit_rejects_declared_binding_not_present_in_timeline(tmp_path):
    result = _materialize(tmp_path)
    foreign = result.asset_bindings[0].model_copy(update={"asset_id": "foreign"})
    bindings = (foreign, *result.asset_bindings[1:])
    _assert_source_invalid(
        lambda: audit_hyperframes_source(
            result.index_path,
            expected_assets=bindings,
            expected_timeline=result.timeline,
        )
    )


def test_source_audit_rejects_undeclared_missing_changed_and_symlink_files(tmp_path):
    for mutation in ("extra", "missing", "changed", "symlink"):
        root = tmp_path / mutation
        root.mkdir()
        result = _materialize(root)
        red_binding = next(
            item for item in result.asset_bindings if item.asset_sha256 == RED_HASH
        )
        blue_binding = next(
            item for item in result.asset_bindings if item.asset_sha256 == BLUE_HASH
        )
        target = result.root / red_binding.materialized_path
        if mutation == "extra":
            (result.root / "extra.txt").write_text("extra", encoding="utf-8")
        elif mutation == "missing":
            target.unlink()
        elif mutation == "changed":
            target.write_bytes(BLUE_PNG)
        else:
            target.unlink()
            target.symlink_to(result.root / blue_binding.materialized_path)
        _assert_source_invalid(
            lambda: audit_hyperframes_source(
                result.index_path,
                expected_assets=result.asset_bindings,
                expected_timeline=result.timeline,
            )
        )


def test_public_boundaries_map_filesystem_and_decode_errors_to_source_invalid(tmp_path):
    timeline = make_resolved_timeline()
    _assert_source_invalid(
        lambda: materialize_hyperframes_source(
            timeline,
            asset_sources={span.asset_id: tmp_path / "missing.png" for span in timeline.visual_spans},
            allowed_asset_root=tmp_path,
            staging_root=tmp_path / "staging",
            allowed_staging_parent=tmp_path,
        )
    )
    root = tmp_path / "bad-source"
    root.mkdir()
    index = root / "index.html"
    index.write_bytes(b"\xff")
    _assert_source_invalid(
        lambda: audit_hyperframes_source(
            index, expected_assets=(), expected_timeline=timeline
        )
    )


def test_css_animation_source_hash_is_deterministic_for_identical_integer_timeline(tmp_path):
    first = _materialize(tmp_path / "one")
    second = _materialize(tmp_path / "two")
    assert first.source_sha256 == second.source_sha256
    assert first.bundle_sha256 == second.bundle_sha256


def test_bundle_hash_covers_exact_ordered_file_set(tmp_path):
    result = _materialize(tmp_path)
    paths = {
        Path("index.html"),
        *(item.materialized_path for item in result.asset_bindings),
    }
    entries = [
        (
            path.as_posix(),
            hashlib.sha256((result.root / path).read_bytes()).hexdigest(),
        )
        for path in sorted(paths, key=lambda item: item.as_posix())
    ]
    expected = hashlib.sha256(
        json.dumps(entries, ensure_ascii=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert result.bundle_sha256 == expected


def test_index_replacement_between_audit_and_bundle_hash_fails_closed(
    tmp_path, monkeypatch
):
    import ai_video.production.hyperframes as hyperframes

    real_audit = hyperframes.audit_hyperframes_source

    def audit_then_replace(index_path, **kwargs):
        real_audit(index_path, **kwargs)
        path = Path(index_path)
        path.write_text(
            path.read_text(encoding="utf-8") + "<!-- replaced after audit -->\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(hyperframes, "audit_hyperframes_source", audit_then_replace)
    _assert_source_invalid(lambda: _materialize(tmp_path))


def test_committed_fixture_matches_exact_materialized_source_and_hashes(tmp_path):
    result = _materialize(tmp_path)
    assert RED_HASH == "1ac67c3a1c909b3356cf6ff490c0f88b8a30ef4c28ca579657f6007146abe71c"
    assert BLUE_HASH == "a99284a70ff9a9ab8aec0eed52c3b9bf7a243628820814d0e6bca45445ce2e3f"
    assert result.index_path.read_bytes() == (FIXTURE_ROOT / "source/index.html").read_bytes()
    assert result.timeline.model_dump_json(indent=2) + "\n" == (FIXTURE_ROOT / "timeline.json").read_text(encoding="utf-8")
    for digest, payload in ((RED_HASH, RED_PNG), (BLUE_HASH, BLUE_PNG)):
        fixture = FIXTURE_ROOT / f"source/assets/{digest}.png"
        assert fixture.read_bytes() == payload
        assert payload.startswith(b"\x89PNG\r\n\x1a\n")


@dataclass(frozen=True)
class _FakeCall:
    command: str
    args: tuple[str, ...]
    cwd: Path | None
    env: dict[str, str]


def _doctor_json() -> dict[str, object]:
    return {
        "ok": False,
        "checks": [
            {"name": "Node.js", "ok": True},
            {"name": "FFmpeg", "ok": True},
            {"name": "FFprobe", "ok": True},
            {"name": "Chrome", "ok": True},
            {"name": "Whisper", "ok": False},
        ],
    }


def _check_json() -> dict[str, object]:
    payload: dict[str, object] = {"ok": True}
    for section in ("lint", "runtime", "layout", "motion", "contrast"):
        payload[section] = {"errorCount": 0, "warningCount": 0}
    return payload


class FakeRunner:
    def __init__(
        self,
        *,
        version: str = "0.7.103",
        fail_at: str | None = None,
        doctor_payload: object | None = None,
        lint_payload: object | None = None,
        check_payload: object | None = None,
        mutate_after: str | None = None,
    ) -> None:
        self.tool_version = version
        self.fail_at = fail_at
        self.doctor_payload = doctor_payload or _doctor_json()
        self.lint_payload = lint_payload or {"errorCount": 0, "warningCount": 1}
        self.check_payload = check_payload or _check_json()
        self.mutate_after = mutate_after
        self.calls: list[_FakeCall] = []

    def version(self, *, env: dict[str, str]) -> str:
        self.calls.append(_FakeCall("version", (), None, dict(env)))
        return self.tool_version

    def doctor(self, *, env: dict[str, str]) -> RendererCommandResult:
        self.calls.append(_FakeCall("doctor", (), None, dict(env)))
        return RendererCommandResult(
            returncode=int(self.fail_at == "doctor"),
            stdout=json.dumps(self.doctor_payload),
            stderr="token=private" if self.fail_at == "doctor" else "",
        )

    def run(self, command, args, *, cwd, env, timeout_seconds):
        del timeout_seconds
        self.calls.append(_FakeCall(command, args, cwd, dict(env)))
        if self.mutate_after == command:
            (cwd / "index.html").write_text("changed", encoding="utf-8")
        if command == "render" and self.fail_at != "render":
            output = Path(args[args.index("-o") + 1])
            output.write_bytes(b"fake-mp4")
        payload = self.lint_payload if command == "lint" else self.check_payload
        return RendererCommandResult(
            returncode=int(self.fail_at == command),
            stdout="" if command == "render" else json.dumps(payload),
            stderr="authorization=private" if self.fail_at == command else "",
        )


def _write_executable(path: Path) -> Path:
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o700)
    return path


def _selection(timeline, kind=RendererKind.HYPERFRAMES):
    zero, one = "0" * 64, "1" * 64
    return RendererSelectionReceipt(
        receipt_id="selection-1",
        attempt_id="attempt-1",
        requested_kind=kind,
        selected_kinds=(kind,),
        renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=ProjectSnapshotPointer(
            path=Path("project.yaml"), revision=1, content_hash=zero, file_sha256=one
        ),
        current_registry=RegistrySnapshotPointer(
            path=Path(f"assets/registry.{zero}.json"),
            revision_id=zero,
            content_hash=zero,
            file_sha256=one,
        ),
    )


def make_render_attempt(tmp_path, renderer_kind=RendererKind.HYPERFRAMES):
    timeline = make_resolved_timeline()
    root = tmp_path / "attempt"
    root.mkdir(mode=0o700)
    return HyperFramesRenderAttempt(
        attempt_id="attempt-1",
        selection=_selection(timeline, renderer_kind),
        timeline=timeline,
        asset_sources=make_asset_sources(tmp_path, timeline),
        allowed_asset_root=tmp_path,
        staging_root=root / "source",
        allowed_staging_parent=root,
        output_path=root / "output/render.mp4",
        verification_snapshot_path=root / "verified.mp4",
    )


def _adapter(tmp_path, runner, **overrides):
    tmp_path.mkdir(parents=True, exist_ok=True)
    browser = _write_executable(tmp_path / "chrome")
    ip_path = _write_executable(tmp_path / "ip")
    kwargs = {
        "probe": lambda fd: {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 320,
                    "height": 180,
                    "r_frame_rate": "24/1",
                    "nb_frames": "10",
                    "codec_name": "h264",
                }
            ]
        },
        "decoded_frames": lambda fd: hashlib.sha256(
            os.pread(fd, os.fstat(fd).st_size, 0)
        ).hexdigest(),
    }
    kwargs.update(overrides)
    return HyperFramesAdapter(
        runner=runner,
        expected_version="0.7.103",
        browser_path=browser,
        ip_path=ip_path,
        **kwargs,
    )


def test_adapter_runs_one_pinned_renderer_in_order(tmp_path):
    runner = FakeRunner()
    result = _adapter(tmp_path, runner).render(make_render_attempt(tmp_path))
    assert [call.command for call in runner.calls] == [
        "version",
        "doctor",
        "lint",
        "check",
        "render",
    ]
    assert all(call.env["HYPERFRAMES_NO_UPDATE_CHECK"] == "1" for call in runner.calls)
    assert all(call.env["P3_IP_PATH"] == str(tmp_path / "ip") for call in runner.calls)
    assert (
        result.output.output_sha256
        == hashlib.sha256(result.output.verified_bytes).hexdigest()
    )
    assert result.output.output_size_bytes == len(result.output.verified_bytes)


def test_adapter_rejects_remotion_without_fallback(tmp_path):
    runner = FakeRunner()
    with pytest.raises(AiVideoError) as caught:
        _adapter(tmp_path, runner).render(
            make_render_attempt(tmp_path, RendererKind.REMOTION)
        )
    assert caught.value.code is ErrorCode.RENDERER_UNAVAILABLE
    assert runner.calls == []


@pytest.mark.parametrize("failed_phase", ["lint", "check", "render"])
def test_adapter_reports_typed_phase_failure_without_next_command(
    tmp_path, failed_phase
):
    runner = FakeRunner(fail_at=failed_phase)
    with pytest.raises(RendererAttemptError) as caught:
        _adapter(tmp_path, runner).render(make_render_attempt(tmp_path))
    assert caught.value.phase == failed_phase
    assert caught.value.retryable is False
    assert runner.calls[-1].command == failed_phase


@pytest.mark.parametrize("required", ["Node.js", "FFmpeg", "FFprobe", "Chrome"])
def test_doctor_json_requires_each_named_runtime_check_ok(tmp_path, required):
    payload = _doctor_json()
    payload["checks"] = [item for item in payload["checks"] if item["name"] != required]
    runner = FakeRunner(doctor_payload=payload)
    with pytest.raises(AiVideoError) as caught:
        _adapter(tmp_path, runner).render(make_render_attempt(tmp_path))
    assert caught.value.code is ErrorCode.RENDERER_UNAVAILABLE
    assert [item.command for item in runner.calls] == ["version", "doctor"]


def test_doctor_ignores_top_level_and_optional_failure(tmp_path):
    _adapter(tmp_path, FakeRunner()).render(make_render_attempt(tmp_path))


@pytest.mark.parametrize(
    ("command", "payload"),
    [
        ("lint", {"errorCount": True, "warningCount": 0}),
        ("lint", {"errorCount": "0", "warningCount": 0}),
        ("check", {"ok": 1}),
    ],
)
def test_lint_check_json_requires_exact_integer_and_boolean_types(
    tmp_path, command, payload
):
    runner = FakeRunner(
        lint_payload=payload if command == "lint" else None,
        check_payload=payload if command == "check" else None,
    )
    with pytest.raises(RendererAttemptError) as caught:
        _adapter(tmp_path, runner).render(make_render_attempt(tmp_path))
    assert (caught.value.code, caught.value.phase) == (
        ErrorCode.RENDERER_SOURCE_INVALID,
        command,
    )


def test_source_mutation_after_lint_fails_closed(tmp_path):
    runner = FakeRunner(mutate_after="lint")
    with pytest.raises(RendererAttemptError) as caught:
        _adapter(tmp_path, runner).render(make_render_attempt(tmp_path))
    assert (caught.value.code, caught.value.phase) == (
        ErrorCode.RENDERER_SOURCE_INVALID,
        "source",
    )


def test_controlled_env_is_exact_and_includes_validated_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", "/safe/bin")
    monkeypatch.setenv("TMPDIR", "/safe/tmp")
    monkeypatch.setenv("HTTPS_PROXY", "http://must-not-leak")
    browser = _write_executable(tmp_path / "chrome")
    ip_path = _write_executable(tmp_path / "ip")
    assert _controlled_env(browser, ip_path) == {
        "PATH": "/safe/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TMPDIR": "/safe/tmp",
        **OFFLINE_ENV,
        "HYPERFRAMES_BROWSER_PATH": str(browser),
        "P3_IP_PATH": str(ip_path),
    }


@pytest.mark.parametrize("bad_kind", ["relative", "symlink", "nonexec"])
def test_controlled_env_rejects_invalid_ip_before_invocation(tmp_path, bad_kind):
    browser = _write_executable(tmp_path / "chrome")
    target = tmp_path / "ip-real"
    target.write_text("x", encoding="utf-8")
    if bad_kind == "relative":
        ip_path = Path("ip")
    elif bad_kind == "symlink":
        target.chmod(0o700)
        ip_path = tmp_path / "ip"
        ip_path.symlink_to(target)
    else:
        ip_path = target
    with pytest.raises(AiVideoError) as caught:
        _controlled_env(browser, ip_path)
    assert caught.value.code is ErrorCode.RENDERER_UNAVAILABLE


@pytest.mark.parametrize(
    "failure", [RuntimeError("probe"), AiVideoError(ErrorCode.FFMPEG_FAILED, "ffmpeg")]
)
def test_verify_boundary_normalizes_probe_failures(tmp_path, failure):
    def fail(_fd):
        raise failure

    with pytest.raises(RendererAttemptError) as caught:
        _adapter(tmp_path, FakeRunner(), probe=fail).render(
            make_render_attempt(tmp_path)
        )
    assert (caught.value.code, caught.value.phase, caught.value.retryable) == (
        ErrorCode.RENDER_FAILED,
        "verify",
        False,
    )


def test_production_runner_builds_exact_unshare_argv_and_fixed_exec_wrapper(tmp_path):
    runner = object.__new__(_NetworkIsolatedHyperFramesRunner)
    runner._unshare = Path("/usr/bin/unshare")
    runner._bash = Path("/usr/bin/bash")
    runner._binary = tmp_path / "node_modules/.bin/hyperframes"
    assert runner._namespace_argv("lint", "/source", "--json") == [
        "/usr/bin/unshare",
        "--user",
        "--map-root-user",
        "--net",
        "--pid",
        "--fork",
        "--mount-proc",
        "/usr/bin/bash",
        "-ceu",
        '"$P3_IP_PATH" link set lo up; exec "$@"',
        "p3-hyperframes",
        str(runner._binary),
        "lint",
        "/source",
        "--json",
    ]
    with pytest.raises(ValueError, match="requires --json"):
        runner._namespace_argv("render", "/source")


def test_production_runner_subprocess_is_closed_and_bounded(tmp_path, monkeypatch):
    runner = object.__new__(_NetworkIsolatedHyperFramesRunner)
    runner._unshare = Path("/usr/bin/unshare")
    runner._bash = Path("/usr/bin/bash")
    runner._binary = tmp_path / "node_modules/.bin/hyperframes"
    runner._project_root = tmp_path
    runner._env = {"P3_IP_PATH": "/usr/bin/ip"}
    observed = {}

    def fake_run(argv, **kwargs):
        observed.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    runner._invoke("--version", timeout_seconds=5)
    assert observed["stdin"] is subprocess.DEVNULL
    assert observed["stdout"] is subprocess.PIPE
    assert observed["stderr"] is subprocess.PIPE
    assert observed["close_fds"] is True
    assert observed["shell"] is False


def test_adapter_uses_exact_lint_check_render_argv_and_static_root(tmp_path):
    runner = FakeRunner()
    attempt = make_render_attempt(tmp_path)
    _adapter(tmp_path, runner).render(attempt)
    lint, check, render = runner.calls[2:]
    assert lint.args == (str(attempt.staging_root), "--json")
    assert check.args == (str(attempt.staging_root), "--json")
    assert render.args == (
        str(attempt.staging_root),
        "-o",
        str(attempt.output_path),
        "--json",
    )
    parsed = _parse_source_document((attempt.staging_root / "index.html").read_text())
    assert parsed.stage_attributes["data-no-timeline"] is None


@pytest.mark.parametrize(
    ("version", "doctor_payload", "fail_at"),
    [
        ("0.7.104", None, None),
        ("0.7.103", {"checks": "not-a-list"}, None),
        ("0.7.103", None, "doctor"),
    ],
)
def test_version_and_doctor_fail_before_materialization(
    tmp_path, version, doctor_payload, fail_at
):
    runner = FakeRunner(version=version, doctor_payload=doctor_payload, fail_at=fail_at)
    with pytest.raises(AiVideoError) as caught:
        _adapter(tmp_path, runner).render(make_render_attempt(tmp_path))
    assert caught.value.code is ErrorCode.RENDERER_UNAVAILABLE
    assert not (tmp_path / "attempt/source").exists()


def test_check_warnings_are_recorded_but_errors_fail(tmp_path):
    warning = _check_json()
    warning["layout"] = {"errorCount": 0, "warningCount": 2}
    result = _adapter(tmp_path, FakeRunner(check_payload=warning)).render(
        make_render_attempt(tmp_path)
    )
    assert result.checks[1].warning_count == 2

    error = _check_json()
    error["motion"] = {"errorCount": 1, "warningCount": 0}
    with pytest.raises(RendererAttemptError) as caught:
        _adapter(tmp_path / "second", FakeRunner(check_payload=error)).render(
            make_render_attempt(tmp_path / "second")
        )
    assert (caught.value.code, caught.value.phase) == (
        ErrorCode.RENDERER_SOURCE_INVALID,
        "check",
    )


@pytest.mark.parametrize(
    "bad_path",
    [
        lambda root: root.parent / "sibling.mp4",
        lambda root: Path("/tmp/p3-external.mp4"),
        lambda root: root / "../escape.mp4",
        lambda root: root / "nested/deeper/render.mp4",
    ],
)
def test_output_escape_is_rejected_before_materialization_or_render(tmp_path, bad_path):
    from dataclasses import replace

    runner = FakeRunner()
    attempt = make_render_attempt(tmp_path)
    attempt = replace(attempt, output_path=bad_path(attempt.allowed_staging_parent))
    with pytest.raises(RendererAttemptError) as caught:
        _adapter(tmp_path, runner).render(attempt)
    assert (caught.value.code, caught.value.phase) == (
        ErrorCode.RENDER_FAILED,
        "verify",
    )
    assert runner.calls == []
    assert not attempt.staging_root.exists()


def test_output_symlink_is_rejected_before_render(tmp_path):
    runner = FakeRunner()
    attempt = make_render_attempt(tmp_path)
    attempt.output_path.parent.mkdir(mode=0o700)
    backing = tmp_path / "backing.mp4"
    backing.write_bytes(b"backing")
    attempt.output_path.symlink_to(backing)
    with pytest.raises(RendererAttemptError) as caught:
        _adapter(tmp_path, runner).render(attempt)
    assert caught.value.phase == "verify"
    assert runner.calls == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("width", 321),
        ("height", 181),
        ("r_frame_rate", "25/1"),
        ("nb_frames", "11"),
    ],
)
def test_measured_output_must_match_timeline(tmp_path, field, value):
    def probe(_fd):
        stream = {
            "codec_type": "video",
            "width": 320,
            "height": 180,
            "r_frame_rate": "24/1",
            "nb_frames": "10",
            "codec_name": "h264",
        }
        stream[field] = value
        return {"streams": [stream]}

    with pytest.raises(RendererAttemptError) as caught:
        _adapter(tmp_path, FakeRunner(), probe=probe).render(
            make_render_attempt(tmp_path)
        )
    assert (caught.value.code, caught.value.phase) == (
        ErrorCode.RENDER_FAILED,
        "verify",
    )


def test_measured_output_rejects_audio_stream(tmp_path):
    def probe(_fd):
        return {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 320,
                    "height": 180,
                    "r_frame_rate": "24/1",
                    "nb_frames": "10",
                    "codec_name": "h264",
                },
                {"codec_type": "audio"},
            ]
        }

    with pytest.raises(RendererAttemptError) as caught:
        _adapter(tmp_path, FakeRunner(), probe=probe).render(
            make_render_attempt(tmp_path)
        )
    assert caught.value.phase == "verify"


def test_empty_or_missing_output_is_typed_verify_failure(tmp_path):
    runner = FakeRunner()
    runner.run = lambda command, args, **kwargs: RendererCommandResult(
        0,
        json.dumps(runner.lint_payload if command == "lint" else runner.check_payload)
        if command != "render"
        else "",
        "",
    )
    with pytest.raises(RendererAttemptError) as caught:
        _adapter(tmp_path, runner).render(make_render_attempt(tmp_path))
    assert (caught.value.code, caught.value.phase) == (
        ErrorCode.RENDER_FAILED,
        "verify",
    )


def test_ffprobe_and_framemd5_use_exact_held_fd_argv(tmp_path, monkeypatch):
    import ai_video.production.hyperframes as hyperframes

    media = tmp_path / "media.mp4"
    media.write_bytes(b"media")
    descriptor = os.open(media, os.O_RDONLY)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        if argv[0] == "ffprobe":
            stdout = json.dumps({"streams": []})
        else:
            stdout = "# header\n0, 0, 0, 1, deadbeef\n"
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(hyperframes.subprocess, "run", fake_run)
    try:
        probe_result = hyperframes.probe_clip_fd(descriptor)
        assert probe_result == {"streams": []}
        assert len(hyperframes.decoded_frame_sha256_fd(descriptor)) == 64
    finally:
        os.close(descriptor)
    for argv, kwargs in calls:
        passed = kwargs["pass_fds"]
        assert len(passed) == 1
        assert f"/proc/self/fd/{passed[0]}" in argv
        assert kwargs["shell"] is False
        assert kwargs["close_fds"] is True


def test_staged_path_swap_after_secure_open_cannot_change_evidence(tmp_path):
    attempt = make_render_attempt(tmp_path)

    def probe(fd):
        attempt.output_path.unlink()
        attempt.output_path.write_bytes(b"replacement")
        assert os.pread(fd, os.fstat(fd).st_size, 0) == b"fake-mp4"
        return {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 320,
                    "height": 180,
                    "r_frame_rate": "24/1",
                    "nb_frames": "10",
                    "codec_name": "h264",
                }
            ]
        }

    with pytest.raises(RendererAttemptError) as caught:
        _adapter(tmp_path, FakeRunner(), probe=probe).render(attempt)
    assert (caught.value.code, caught.value.phase) == (
        ErrorCode.RENDER_FAILED,
        "verify",
    )
    assert attempt.output_path.read_bytes() == b"replacement"


def test_verification_path_swaps_never_mix_held_fd_evidence(tmp_path):
    attempt = make_render_attempt(tmp_path)

    def swap(path: Path, payload: bytes) -> None:
        detached = path.with_name(f"detached-{len(payload)}.mp4")
        if path.exists():
            path.rename(detached)
        path.write_bytes(payload)

    def probe(fd):
        swap(attempt.verification_snapshot_path, b"probe-replacement")
        assert os.pread(fd, os.fstat(fd).st_size, 0) == b"fake-mp4"
        return {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 320,
                    "height": 180,
                    "r_frame_rate": "24/1",
                    "nb_frames": "10",
                    "codec_name": "h264",
                }
            ]
        }

    def decoded(fd):
        swap(attempt.verification_snapshot_path, b"decoded-replacement")
        return hashlib.sha256(os.pread(fd, os.fstat(fd).st_size, 0)).hexdigest()

    result = _adapter(
        tmp_path, FakeRunner(), probe=probe, decoded_frames=decoded
    ).render(attempt)
    assert result.output.verified_bytes == b"fake-mp4"
    assert result.output.output_sha256 == hashlib.sha256(b"fake-mp4").hexdigest()


def test_verification_path_swap_immediately_after_copy_yield_uses_created_fd(
    tmp_path, monkeypatch
):
    from contextlib import contextmanager
    import ai_video.production.hyperframes as hyperframes

    attempt = make_render_attempt(tmp_path)
    real_copy = hyperframes._copy_held_fd_to_regular_file_nofollow

    @contextmanager
    def copy_then_swap(*args, **kwargs):
        with real_copy(*args, **kwargs) as verification:
            verification.path.rename(verification.path.with_name("detached.mp4"))
            verification.path.write_bytes(b"replacement")
            yield verification

    monkeypatch.setattr(
        hyperframes, "_copy_held_fd_to_regular_file_nofollow", copy_then_swap
    )
    result = _adapter(tmp_path, FakeRunner()).render(attempt)
    assert result.output.verified_bytes == b"fake-mp4"
    assert attempt.verification_snapshot_path.read_bytes() == b"replacement"


def test_verification_snapshot_is_exact_0600_despite_process_umask(tmp_path):
    source = tmp_path / "source.mp4"
    destination = tmp_path / "verified.mp4"
    source.write_bytes(b"fake-mp4")

    source_fd = os.open(source, os.O_RDONLY)
    previous_umask = os.umask(0o777)
    try:
        with _copy_held_fd_to_regular_file_nofollow(
            source_fd,
            destination,
            contained_by=tmp_path,
            mode=0o600,
        ) as verification:
            assert os.stat(verification.fd).st_mode & 0o777 == 0o600
        assert destination.stat().st_mode & 0o777 == 0o600
    finally:
        os.umask(previous_umask)
        os.close(source_fd)


def test_namespace_capability_failure_has_no_host_fallback(tmp_path, monkeypatch):
    runner = object.__new__(_NetworkIsolatedHyperFramesRunner)
    runner._unshare = Path("/usr/bin/unshare")
    runner._bash = Path("/usr/bin/bash")
    runner._project_root = tmp_path
    runner._env = {"P3_IP_PATH": "/usr/bin/ip"}
    calls = []

    def unavailable(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="denied")

    monkeypatch.setattr(subprocess, "run", unavailable)
    with pytest.raises(AiVideoError) as caught:
        runner._probe_namespace()
    assert caught.value.code is ErrorCode.RENDERER_UNAVAILABLE
    assert len(calls) == 1
    assert calls[0][0][0] == "/usr/bin/unshare"


def test_production_runner_accepts_only_lock_owned_binary_and_validated_tools(
    tmp_path, monkeypatch
):
    project_root = Path(__file__).parents[1]
    browser = _write_executable(tmp_path / "chrome")
    ip_path = _write_executable(tmp_path / "ip")
    unshare = _write_executable(tmp_path / "unshare")
    bash = _write_executable(tmp_path / "bash")
    monkeypatch.setattr(
        _NetworkIsolatedHyperFramesRunner, "_probe_namespace", lambda self: None
    )
    runner = _NetworkIsolatedHyperFramesRunner(
        project_root=project_root,
        binary=project_root / "node_modules/.bin/hyperframes",
        browser_path=browser,
        ip_path=ip_path,
        unshare_path=unshare,
        bash_path=bash,
    )
    assert runner._binary == project_root / "node_modules/.bin/hyperframes"
    with pytest.raises(AiVideoError) as caught:
        _NetworkIsolatedHyperFramesRunner(
            project_root=project_root,
            binary=project_root / "node_modules/hyperframes/bin/hyperframes.mjs",
            browser_path=browser,
            ip_path=ip_path,
            unshare_path=unshare,
            bash_path=bash,
        )
    assert caught.value.code is ErrorCode.RENDERER_UNAVAILABLE


def test_runner_timeout_is_typed_and_redacted(tmp_path, monkeypatch):
    runner = object.__new__(_NetworkIsolatedHyperFramesRunner)
    runner._unshare = Path("/usr/bin/unshare")
    runner._bash = Path("/usr/bin/bash")
    runner._binary = tmp_path / "node_modules/.bin/hyperframes"
    runner._project_root = tmp_path
    runner._env = {"P3_IP_PATH": "/usr/bin/ip"}

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            args[0], kwargs["timeout"], stderr="token=hidden"
        )

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(RendererAttemptError) as caught:
        runner._invoke(
            "render", "/source", "-o", "/output.mp4", "--json", timeout_seconds=1
        )
    assert (caught.value.code, caught.value.phase) == (
        ErrorCode.RENDER_FAILED,
        "render",
    )
    assert "hidden" not in (caught.value.technical_detail or "")


def test_renderer_failure_stderr_is_bounded_and_redacted(tmp_path):
    runner = FakeRunner(fail_at="render")
    with pytest.raises(RendererAttemptError) as caught:
        _adapter(tmp_path, runner).render(make_render_attempt(tmp_path))
    assert "private" not in (caught.value.technical_detail or "")
    assert "[REDACTED]" in (caught.value.technical_detail or "")


def test_prepare_durable_render_artifacts_builds_exact_n_plus_6_set_from_verified_bytes(
    tmp_path,
):
    attempt = make_render_attempt(tmp_path)
    result = _adapter(tmp_path, FakeRunner()).render(attempt)
    attempt.verification_snapshot_path.write_bytes(b"untrusted-replacement")

    durable = prepare_durable_render_artifacts(
        result,
        timeline=attempt.timeline,
        renderer_selection=attempt.selection,
        current_project=attempt.selection.current_project,
        current_registry=attempt.selection.current_registry,
    )

    assert len(durable.artifacts) == 8
    assert all(isinstance(item, PreparedArtifact) for item in durable.artifacts)
    assert tuple(item.relative_path for item in durable.artifacts) == tuple(
        sorted(item.relative_path for item in durable.artifacts)
    )
    output = next(
        item
        for item in durable.artifacts
        if item.relative_path.parts[:3] == ("state", "render", "outputs")
    )
    assert output.payload == b"fake-mp4"
    assert output.file_sha256 == hashlib.sha256(b"fake-mp4").hexdigest()
    assert durable.next_render_state.path in {
        item.relative_path for item in durable.artifacts
    }


def test_package_root_exports_lifecycle_and_only_durable_renderer_execution_api():
    required = {
        "BeginRenderAttemptRequest",
        "RecordRenderFailureRequest",
        "ActivateRenderStateRequest",
        "RenderAttemptPaths",
        "RenderArtifactPointer",
        "RenderSourceFilePointer",
        "RenderSourceBundlePointer",
        "RenderOutputPointer",
        "RenderStateSnapshot",
        "RenderStateSnapshotPointer",
        "ProductionStateCommitter",
        "render_with_hyperframes",
    }
    forbidden = {
        "HyperFramesAdapter",
        "RendererRunner",
        "_NetworkIsolatedHyperFramesRunner",
        "HyperFramesRenderAttempt",
        "HyperFramesRenderResult",
        "VerifiedRenderFile",
    }
    assert required <= set(production.__all__)
    assert forbidden.isdisjoint(production.__all__)
    parameters = inspect.signature(production.render_with_hyperframes).parameters
    assert "runner" not in parameters
    assert "adapter" not in parameters


def test_renderer_tool_root_is_separate_from_production_root_and_fails_closed(
    tmp_path,
):
    production_root = tmp_path / "production"
    tool_root = tmp_path / "renderer-tool"
    binary = tool_root / "node_modules/.bin/hyperframes"

    assert production_root != tool_root
    assert _renderer_tool_root(binary) == tool_root

    malformed = (
        tmp_path / "renderer-tool/node_modules/hyperframes/bin/hyperframes.mjs"
    )
    with pytest.raises(AiVideoError) as exc_info:
        _renderer_tool_root(malformed)
    assert exc_info.value.code is ErrorCode.RENDERER_UNAVAILABLE

    with pytest.raises(AiVideoError) as exc_info:
        _renderer_tool_root(Path("node_modules/.bin/hyperframes"))
    assert exc_info.value.code is ErrorCode.RENDERER_UNAVAILABLE


def test_public_renderer_constructs_runner_from_binary_tool_root(
    tmp_path, monkeypatch
):
    import ai_video.production.hyperframes as hyperframes

    production_root = tmp_path / "production"
    production_root.mkdir()
    tool_root = tmp_path / "renderer-tool"
    binary = tool_root / "node_modules/.bin/hyperframes"
    captured: dict[str, object] = {}
    sentinel = object()

    def fake_runner(**kwargs):
        captured.update(kwargs)
        return object()

    def fake_orchestration(**kwargs):
        kwargs["runner_factory"]()
        return sentinel

    monkeypatch.setattr(hyperframes, "_NetworkIsolatedHyperFramesRunner", fake_runner)
    monkeypatch.setattr(hyperframes, "_render_with_hyperframes", fake_orchestration)
    executable = tmp_path / "placeholder-executable"

    result = production.render_with_hyperframes(
        committer=ProductionStateCommitter(production_root),
        begin_request=object(),  # type: ignore[arg-type]
        timeline=object(),  # type: ignore[arg-type]
        asset_sources={},
        allowed_asset_root=production_root,
        binary_path=binary,
        browser_path=executable,
        unshare_path=executable,
        ip_path=executable,
        bash_path=executable,
    )

    assert result is sentinel
    assert captured["project_root"] == tool_root
    assert captured["project_root"] != production_root
    assert captured["binary"] == binary


def test_public_renderer_wrong_binary_structure_is_terminal_source_failure(tmp_path):
    project_factory.write_production_project(tmp_path)
    before = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    timeline = make_resolved_timeline()
    selection = RendererSelectionReceipt(
        receipt_id="selection-invalid-tool-root",
        attempt_id="invalid-tool-root",
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=before.active_project,
        current_registry=before.active_registry,
    )
    executable = tmp_path / "placeholder-executable"

    with pytest.raises(AiVideoError) as exc_info:
        production.render_with_hyperframes(
            committer=ProductionStateCommitter(tmp_path),
            begin_request=BeginRenderAttemptRequest(
                before.manifest_revision, None, selection
            ),
            timeline=timeline,
            asset_sources=make_asset_sources(tmp_path, timeline),
            allowed_asset_root=tmp_path,
            binary_path=tmp_path / "renderer-tool/hyperframes",
            browser_path=executable,
            unshare_path=executable,
            ip_path=executable,
            bash_path=executable,
        )

    assert exc_info.value.code is ErrorCode.RENDERER_UNAVAILABLE
    failed = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    assert failed.manifest_revision == before.manifest_revision + 2
    assert failed.attempts[-1].status is StateCommitStatus.FAILED
    assert failed.attempts[-1].render_phase == "source"


@pytest.mark.skipif(
    os.environ.get("P3_LIVE_RENDERER") != "1",
    reason="requires the explicit Task 6 live renderer gate",
)
def test_live_committed_fixture_render_state_lifecycle(tmp_path):
    def required_absolute_env(name: str) -> Path:
        value = os.environ.get(name)
        assert value, f"{name} is required when P3_LIVE_RENDERER=1"
        path = Path(value)
        assert path.is_absolute(), f"{name} must be absolute"
        return path

    binary = required_absolute_env("P3_BINARY")
    evidence_root = required_absolute_env("P3_INTEGRATION_EVIDENCE")
    browser = required_absolute_env("HYPERFRAMES_BROWSER_PATH")
    ip_path = required_absolute_env("P3_IP_PATH")
    unshare_name = shutil.which("unshare")
    bash_name = shutil.which("bash")
    assert unshare_name is not None
    assert bash_name is not None
    unshare = Path(unshare_name).resolve(strict=True)
    bash = Path(bash_name).resolve(strict=True)
    assert evidence_root.is_dir()
    ffprobe_name = shutil.which("ffprobe")
    ffmpeg_name = shutil.which("ffmpeg")
    assert ffprobe_name is not None
    assert ffmpeg_name is not None
    ffprobe = Path(ffprobe_name).resolve(strict=True)
    ffmpeg = Path(ffmpeg_name).resolve(strict=True)

    def probe_output(path: Path) -> dict[str, object]:
        completed = subprocess.run(
            [
                str(ffprobe),
                "-v",
                "error",
                "-show_streams",
                "-of",
                "json",
                str(path),
            ],
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
            timeout=120,
        )
        assert completed.returncode == 0, completed.stderr
        return json.loads(completed.stdout)

    def center_pixel(path: Path, frame: int) -> tuple[int, int, int]:
        completed = subprocess.run(
            [
                str(ffmpeg),
                "-v",
                "error",
                "-i",
                str(path),
                "-vf",
                    f"select=eq(n\\,{frame}),format=rgb24,crop=1:1:160:90",
                "-frames:v",
                "1",
                "-f",
                "rawvideo",
                "-",
            ],
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
        )
        assert completed.returncode == 0, completed.stderr.decode(
            "utf-8", errors="replace"
        )
        assert len(completed.stdout) == 3
        return tuple(completed.stdout)  # type: ignore[return-value]

    timeline = make_resolved_timeline()
    cases: list[
        tuple[
            Path,
            ProductionStateCommitter,
            BeginRenderAttemptRequest,
            dict[str, Path],
            Path,
        ]
    ] = []
    expected_argv: list[list[str]] = []
    for ordinal in (1, 2):
        root = tmp_path / f"production-{ordinal}"
        project_factory.write_production_project(root)
        manifest = ProductionManifest.model_validate_json(
            (root / "state/manifest.json").read_text(encoding="utf-8")
        )
        selection = RendererSelectionReceipt(
            receipt_id=f"selection-live-{ordinal}",
            attempt_id=f"live-render-{ordinal}",
            requested_kind=RendererKind.HYPERFRAMES,
            selected_kinds=(RendererKind.HYPERFRAMES,),
            renderer_version="0.7.103",
            timeline_fingerprint=timeline.composition_fingerprint,
            current_project=manifest.active_project,
            current_registry=manifest.active_registry,
        )
        committer = ProductionStateCommitter(root)
        request = BeginRenderAttemptRequest(
            manifest.manifest_revision, None, selection
        )
        paths = committer.render_attempt_paths(selection.attempt_id)
        binary_text = str(binary)
        source_text = str(paths.source_root)
        expected_argv.extend(
            [
                [binary_text, "--version"],
                [binary_text, "doctor", "--json"],
                [binary_text, "lint", source_text, "--json"],
                [binary_text, "check", source_text, "--json"],
                [
                    binary_text,
                    "render",
                    source_text,
                    "-o",
                    str(paths.staged_output_path),
                    "--json",
                ],
            ]
        )
        cases.append(
            (
                root,
                committer,
                request,
                make_asset_sources(root, timeline),
                paths.verification_snapshot_path,
            )
        )

    expected_path = evidence_root / "expected-argv.json"
    expected_path.write_text(
        json.dumps(
            {"argv": expected_argv}, sort_keys=True, separators=(",", ":")
        )
        + "\n",
        encoding="utf-8",
    )

    decoded_fingerprints: list[str] = []
    for root, committer, request, asset_sources, verification_snapshot in cases:
        activated = production.render_with_hyperframes(
            committer=committer,
            begin_request=request,
            timeline=timeline,
            asset_sources=asset_sources,
            allowed_asset_root=root,
            binary_path=binary,
            browser_path=browser,
            unshare_path=unshare,
            ip_path=ip_path,
            bash_path=bash,
        )
        assert activated.active_render_state is not None
        assert activated.attempts[-1].status is StateCommitStatus.SUCCEEDED
        loaded = load_production_project(root / "project.yaml")
        state = loaded.render_state
        assert state is not None
        assert state.timeline.revision == timeline.revision
        assert state.timeline.content_hash == timeline.content_hash
        assert state.project == activated.active_project
        assert state.registry == activated.active_registry
        assert state.renderer_selection == request.renderer_selection
        assert state.timeline_fingerprint == timeline.composition_fingerprint
        assert state.source_bundle_sha256 == state.source_bundle.bundle_sha256
        assert state.asset_hashes == tuple(
            item.file_sha256 for item in state.source_bundle.assets
        )

        source = RendererSourceReceipt.model_validate_json(
            (root / state.source_receipt.path).read_bytes()
        )
        render = RenderReceipt.model_validate_json(
            (root / state.render_receipt.path).read_bytes()
        )
        assert source.attempt_id == request.renderer_selection.attempt_id
        assert render.attempt_id == request.renderer_selection.attempt_id
        assert source.timeline_fingerprint == state.timeline_fingerprint
        assert render.timeline_fingerprint == state.timeline_fingerprint
        assert source.source_bundle == state.source_bundle
        assert render.source_bundle_sha256 == state.source_bundle_sha256
        assert render.asset_hashes == state.asset_hashes
        receipt_text = json.dumps(
            [source.model_dump(mode="json"), render.model_dump(mode="json")],
            sort_keys=True,
        )
        assert "state/render/attempts/" not in receipt_text
        assert str(root) not in receipt_text

        assert (root / state.source_bundle.index.path).read_bytes() == (
            FIXTURE_ROOT / "source/index.html"
        ).read_bytes()
        for asset in state.source_bundle.assets:
            assert (root / asset.path).read_bytes() == (
                FIXTURE_ROOT / f"source/assets/{asset.path.name}"
            ).read_bytes()

        output_path = root / state.output.path
        output_bytes = output_path.read_bytes()
        assert hashlib.sha256(output_bytes).hexdigest() == state.output.file_sha256
        assert output_bytes == verification_snapshot.read_bytes()
        probe = probe_output(output_path)
        streams = probe["streams"]
        assert isinstance(streams, list)
        video = [item for item in streams if item["codec_type"] == "video"]
        audio = [item for item in streams if item["codec_type"] == "audio"]
        assert len(video) == 1
        assert audio == []
        assert int(video[0]["nb_frames"]) == 10
        assert render.measured.duration_frames == 10
        frame_four = center_pixel(output_path, 4)
        frame_five = center_pixel(output_path, 5)
        assert frame_four[0] > frame_four[1] and frame_four[0] > frame_four[2]
        assert frame_five[2] > frame_five[0] and frame_five[2] > frame_five[1]
        assert frame_four != frame_five
        decoded_fingerprints.append(render.decoded_frame_fingerprint)

    assert len(expected_argv) == 10
    assert decoded_fingerprints[0] == decoded_fingerprints[1]


def _prepared_activation_request(
    tmp_path: Path, attempt_id: str, *, versioned_pair: bool = False
):
    before, timeline, begin_request, browser, ip_path = _replay_inputs(
        tmp_path, attempt_id
    )
    committer = ProductionStateCommitter(tmp_path)
    if versioned_pair:
        project, registry = project_factory.load_revision_two_models(tmp_path)
        before = committer.commit(
            prepare_project_registry_commit(
                manifest=before,
                project=project,
                registry=registry,
                attempt_id=f"{attempt_id}-project-r2",
            )
        )
        selection = begin_request.renderer_selection.model_copy(
            update={
                "current_project": before.active_project,
                "current_registry": before.active_registry,
            }
        )
        begin_request = BeginRenderAttemptRequest(
            before.manifest_revision, None, selection
        )
    begun = committer.begin_render_attempt(begin_request)
    paths = committer.render_attempt_paths(attempt_id)
    paths.attempt_root.mkdir(parents=True, mode=0o700)
    result = _adapter(tmp_path / "activation-tools", FakeRunner()).render(
        HyperFramesRenderAttempt(
            attempt_id=attempt_id,
            selection=begin_request.renderer_selection,
            timeline=timeline,
            asset_sources=make_asset_sources(tmp_path, timeline),
            allowed_asset_root=tmp_path,
            staging_root=paths.source_root,
            allowed_staging_parent=paths.attempt_root,
            output_path=paths.staged_output_path,
            verification_snapshot_path=paths.verification_snapshot_path,
        )
    )
    durable = prepare_durable_render_artifacts(
        result,
        timeline=timeline,
        renderer_selection=begin_request.renderer_selection,
        current_project=begun.active_project,
        current_registry=begun.active_registry,
    )
    request = ActivateRenderStateRequest(
        attempt_id=attempt_id,
        expected_manifest_revision=begun.manifest_revision,
        current_project=begun.active_project,
        current_registry=begun.active_registry,
        base_render_state=None,
        renderer_selection=begin_request.renderer_selection,
        artifacts=durable.artifacts,
        next_render_state=durable.next_render_state,
    )
    return before, committer, request


def test_activation_duplicate_artifacts_terminalizes_owned_r1_as_r2(tmp_path):
    before, committer, request = _prepared_activation_request(
        tmp_path, "duplicate-artifacts"
    )
    duplicate = request.artifacts[0]
    invalid = ActivateRenderStateRequest(
        **{
            **request.__dict__,
            "artifacts": (duplicate, duplicate, *request.artifacts[1:]),
        }
    )

    with pytest.raises(AiVideoError) as exc_info:
        committer.activate_render_state(invalid)

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    terminal = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    assert terminal.manifest_revision == before.manifest_revision + 2
    assert terminal.active_render_state is None
    attempt = terminal.attempts[-1]
    assert attempt.status is StateCommitStatus.FAILED
    assert attempt.render_phase == "activate"
    assert attempt.candidate_render_state == request.next_render_state
    assert attempt.candidate_artifacts_hash != hashlib.sha256(b"[]").hexdigest()


def _with_mismatched_binding_hash(
    request: ActivateRenderStateRequest,
) -> ActivateRenderStateRequest:
    artifacts = {item.relative_path: item for item in request.artifacts}
    state = production.RenderStateSnapshot.model_validate_json(
        artifacts[request.next_render_state.path].payload
    )
    source = RendererSourceReceipt.model_validate_json(
        artifacts[state.source_receipt.path].payload
    )
    binding = source.asset_bindings[0]
    bad_source = seal_artifact(
        source.model_copy(
            update={
                "content_hash": "0" * 64,
                "asset_bindings": (
                    binding.model_copy(update={"asset_sha256": "f" * 64}),
                    *source.asset_bindings[1:],
                ),
            }
        )
    )
    source_payload = _sealed_json_bytes(bad_source)
    source_pointer = production.RenderArtifactPointer(
        path=canonical_renderer_source_receipt_path(bad_source.content_hash),
        revision=bad_source.revision,
        content_hash=bad_source.content_hash,
        file_sha256=hashlib.sha256(source_payload).hexdigest(),
    )
    bad_state = seal_artifact(
        state.model_copy(
            update={
                "content_hash": "0" * 64,
                "source_receipt": source_pointer,
            }
        )
    )
    state_payload = _sealed_json_bytes(bad_state)
    state_pointer = production.RenderStateSnapshotPointer(
        path=canonical_render_state_path(bad_state.content_hash),
        revision=bad_state.revision,
        content_hash=bad_state.content_hash,
        file_sha256=hashlib.sha256(state_payload).hexdigest(),
    )
    del artifacts[state.source_receipt.path]
    del artifacts[request.next_render_state.path]
    for path, payload in (
        (source_pointer.path, source_payload),
        (state_pointer.path, state_payload),
    ):
        artifacts[path] = PreparedArtifact(
            path, payload, hashlib.sha256(payload).hexdigest()
        )
    return ActivateRenderStateRequest(
        **{
            **request.__dict__,
            "artifacts": tuple(artifacts[path] for path in sorted(artifacts)),
            "next_render_state": state_pointer,
        }
    )


def test_activation_explicitly_rejects_binding_hash_not_matching_bundle_pointer(
    tmp_path,
):
    _, committer, request = _prepared_activation_request(
        tmp_path, "binding-hash-activation"
    )
    invalid = _with_mismatched_binding_hash(request)

    with pytest.raises(AiVideoError, match="binding"):
        committer._validate_render_artifacts(invalid)


def test_reader_explicitly_rejects_binding_hash_without_source_audit_dependency(
    tmp_path, monkeypatch
):
    import ai_video.production.hyperframes as hyperframes

    before, _, request = _prepared_activation_request(
        tmp_path, "binding-hash-reader"
    )
    invalid = _with_mismatched_binding_hash(request)
    for artifact in invalid.artifacts:
        path = tmp_path / artifact.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(artifact.payload)
    manifest = before.model_copy(
        update={
            "schema_version": "2.1",
            "manifest_revision": before.manifest_revision + 1,
            "active_render_state": invalid.next_render_state,
        }
    )
    (tmp_path / "state/manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    monkeypatch.setattr(hyperframes, "audit_hyperframes_source", lambda *a, **k: None)

    with pytest.raises(AiVideoError, match="binding"):
        load_production_project(tmp_path / "project.yaml")


def test_activate_render_state_commits_r1_r2_r3_and_exact_replay(tmp_path):
    project_factory.write_production_project(tmp_path)
    manifest = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    timeline = make_resolved_timeline()
    selection = RendererSelectionReceipt(
        receipt_id="selection-render-1",
        attempt_id="render-1",
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=manifest.active_project,
        current_registry=manifest.active_registry,
    )
    committer = ProductionStateCommitter(tmp_path)
    begun = committer.begin_render_attempt(
        BeginRenderAttemptRequest(manifest.manifest_revision, None, selection)
    )
    paths = committer.render_attempt_paths(selection.attempt_id)
    paths.attempt_root.mkdir(parents=True, mode=0o700)
    attempt = HyperFramesRenderAttempt(
        attempt_id=selection.attempt_id,
        selection=selection,
        timeline=timeline,
        asset_sources=make_asset_sources(tmp_path, timeline),
        allowed_asset_root=tmp_path,
        staging_root=paths.source_root,
        allowed_staging_parent=paths.attempt_root,
        output_path=paths.staged_output_path,
        verification_snapshot_path=paths.verification_snapshot_path,
    )
    result = _adapter(tmp_path / "tools", FakeRunner()).render(attempt)
    durable = prepare_durable_render_artifacts(
        result,
        timeline=timeline,
        renderer_selection=selection,
        current_project=begun.active_project,
        current_registry=begun.active_registry,
    )
    request = ActivateRenderStateRequest(
        attempt_id=selection.attempt_id,
        expected_manifest_revision=begun.manifest_revision,
        current_project=begun.active_project,
        current_registry=begun.active_registry,
        base_render_state=None,
        renderer_selection=selection,
        artifacts=durable.artifacts,
        next_render_state=durable.next_render_state,
    )

    activated = committer.activate_render_state(request)
    replay = committer.activate_render_state(request)

    assert activated == replay
    assert activated.manifest_revision == manifest.manifest_revision + 3
    assert activated.active_render_state == durable.next_render_state
    assert activated.attempts[-1].status is StateCommitStatus.SUCCEEDED
    assert all((tmp_path / item.relative_path).read_bytes() == item.payload for item in durable.artifacts)
    loaded = load_production_project(tmp_path / "project.yaml")
    assert loaded.render_state == durable.state

    render_bytes = {
        item.relative_path: (tmp_path / item.relative_path).read_bytes()
        for item in durable.artifacts
    }
    next_project, next_registry = project_factory.load_revision_two_models(tmp_path)
    switched = committer.commit(
        prepare_project_registry_commit(
            manifest=activated,
            project=next_project,
            registry=next_registry,
            attempt_id="project-revision-2-after-render",
        )
    )
    assert switched.active_render_state is None
    assert all((tmp_path / path).read_bytes() == data for path, data in render_bytes.items())


def _same_pair_request(
    root: Path, manifest: ProductionManifest, attempt_id: str
) -> StateCommitRequest:
    artifacts = tuple(
        PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest())
        for path in sorted(
            (manifest.active_project.path, manifest.active_registry.path)
        )
        for payload in ((root / path).read_bytes(),)
    )
    return StateCommitRequest(
        attempt_id=attempt_id,
        operation="same_pair_probe",
        expected_manifest_revision=manifest.manifest_revision,
        artifacts=artifacts,
        next_project=manifest.active_project,
        next_registry=manifest.active_registry,
    )


def test_same_pair_commit_retains_only_fully_verified_render_state(tmp_path):
    _, committer, activation = _prepared_activation_request(
        tmp_path, "same-pair-retain", versioned_pair=True
    )
    activated = committer.activate_render_state(activation)

    retained = committer.commit(
        _same_pair_request(tmp_path, activated, "same-pair-ok")
    )

    assert retained.active_render_state == activated.active_render_state


def test_success_replay_after_same_pair_commit_returns_current_manifest_without_runner(
    tmp_path,
):
    _, committer, activation = _prepared_activation_request(
        tmp_path, "success-before-same-pair", versioned_pair=True
    )
    activated = committer.activate_render_state(activation)
    retained = committer.commit(
        _same_pair_request(tmp_path, activated, "same-pair-after-success")
    )
    begin_request = BeginRenderAttemptRequest(
        activation.expected_manifest_revision - 1,
        activation.base_render_state,
        activation.renderer_selection,
    )
    manifest_path = tmp_path / "state/manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    runner_calls = 0

    def forbidden_runner():
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("historical success replay must not construct a runner")

    replay = _call_fake_render(
        tmp_path,
        request=begin_request,
        timeline=make_resolved_timeline(),
        browser=tmp_path / "tools/chrome",
        ip_path=tmp_path / "tools/ip",
        runner_factory=forbidden_runner,
        committer=committer,
    )

    assert replay == retained
    assert replay.active_render_state == activated.active_render_state
    assert replay.manifest_revision == retained.manifest_revision
    assert manifest_path.read_bytes() == manifest_bytes
    assert runner_calls == 0


def test_failed_replay_after_same_pair_commit_returns_current_base_manifest(
    tmp_path,
):
    _, committer, activation = _prepared_activation_request(
        tmp_path, "failed-before-same-pair", versioned_pair=True
    )
    failed = committer.record_render_failure(
        RecordRenderFailureRequest(
            attempt_id=activation.attempt_id,
            expected_manifest_revision=activation.expected_manifest_revision,
            current_project=activation.current_project,
            current_registry=activation.current_registry,
            base_render_state=activation.base_render_state,
            renderer_selection=activation.renderer_selection,
            phase="render",
            error_code=ErrorCode.RENDER_FAILED.value,
            error_message="expected render failure",
        )
    )
    retained = committer.commit(
        _same_pair_request(tmp_path, failed, "same-pair-after-failure")
    )
    begin_request = BeginRenderAttemptRequest(
        activation.expected_manifest_revision - 1,
        activation.base_render_state,
        activation.renderer_selection,
    )
    runner_calls = 0

    def forbidden_runner():
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("historical failure replay must not construct a runner")

    replay = _call_fake_render(
        tmp_path,
        request=begin_request,
        timeline=make_resolved_timeline(),
        browser=tmp_path / "tools/chrome",
        ip_path=tmp_path / "tools/ip",
        runner_factory=forbidden_runner,
        committer=committer,
    )

    assert replay == retained
    assert replay.active_render_state is None
    assert runner_calls == 0


def test_same_pair_commit_rejects_tampered_render_without_manifest_mutation(tmp_path):
    _, committer, activation = _prepared_activation_request(
        tmp_path, "same-pair-tamper", versioned_pair=True
    )
    activated = committer.activate_render_state(activation)
    manifest_path = tmp_path / "state/manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    output_path = tmp_path / activation.next_render_state.path
    state = production.RenderStateSnapshot.model_validate_json(output_path.read_bytes())
    (tmp_path / state.output.path).write_bytes(b"tampered-output")

    with pytest.raises(AiVideoError) as exc_info:
        committer.commit(
            _same_pair_request(tmp_path, activated, "same-pair-reject")
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert manifest_path.read_bytes() == manifest_bytes


def test_succeeded_activation_replay_reopens_graph_and_rejects_tamper(tmp_path):
    _, committer, activation = _prepared_activation_request(
        tmp_path, "succeeded-replay-tamper"
    )
    activated = committer.activate_render_state(activation)
    manifest_path = tmp_path / "state/manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    state = production.RenderStateSnapshot.model_validate_json(
        (tmp_path / activation.next_render_state.path).read_bytes()
    )
    (tmp_path / state.output.path).write_bytes(b"tampered-output")

    with pytest.raises(AiVideoError) as exc_info:
        committer.activate_render_state(activation)

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert manifest_path.read_bytes() == manifest_bytes
    assert activated.active_render_state == activation.next_render_state


def test_orchestrator_persists_selection_before_runner_and_activates_once(tmp_path):
    project_factory.write_production_project(tmp_path)
    before = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    timeline = make_resolved_timeline()
    selection = RendererSelectionReceipt(
        receipt_id="selection-orchestrated",
        attempt_id="orchestrated-1",
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=before.active_project,
        current_registry=before.active_registry,
    )
    runner = FakeRunner()
    observed: list[str] = []
    real_version = runner.version

    def version(*, env):
        manifest = ProductionManifest.model_validate_json(
            (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
        )
        assert manifest.attempts[-1].status is StateCommitStatus.RUNNING
        observed.append("version")
        return real_version(env=env)

    runner.version = version  # type: ignore[method-assign]
    tools = tmp_path / "tools"
    tools.mkdir()
    browser = _write_executable(tools / "chrome")
    ip_path = _write_executable(tools / "ip")
    result = _render_with_hyperframes(
        committer=ProductionStateCommitter(tmp_path),
        begin_request=BeginRenderAttemptRequest(before.manifest_revision, None, selection),
        timeline=timeline,
        asset_sources=make_asset_sources(tmp_path, timeline),
        allowed_asset_root=tmp_path,
        runner_factory=lambda: runner,
        browser_path=browser,
        ip_path=ip_path,
        expected_version="0.7.103",
        probe=lambda fd: {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 320,
                    "height": 180,
                    "r_frame_rate": "24/1",
                    "nb_frames": "10",
                    "codec_name": "h264",
                }
            ]
        },
        decoded_frames=lambda fd: hashlib.sha256(
            os.pread(fd, os.fstat(fd).st_size, 0)
        ).hexdigest(),
    )
    assert observed == ["version"]
    assert result.active_render_state is not None
    assert result.attempts[-1].status is StateCommitStatus.SUCCEEDED


def test_orchestrator_records_wrong_version_as_terminal_source_failure(tmp_path):
    project_factory.write_production_project(tmp_path)
    before = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    timeline = make_resolved_timeline()
    selection = RendererSelectionReceipt(
        receipt_id="selection-version-failure",
        attempt_id="version-failure",
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=before.active_project,
        current_registry=before.active_registry,
    )
    tools = tmp_path / "tools"
    tools.mkdir()
    browser = _write_executable(tools / "chrome")
    ip_path = _write_executable(tools / "ip")
    with pytest.raises(AiVideoError) as caught:
        _render_with_hyperframes(
            committer=ProductionStateCommitter(tmp_path),
            begin_request=BeginRenderAttemptRequest(before.manifest_revision, None, selection),
            timeline=timeline,
            asset_sources=make_asset_sources(tmp_path, timeline),
            allowed_asset_root=tmp_path,
            runner_factory=lambda: FakeRunner(version="0.7.102"),
            browser_path=browser,
            ip_path=ip_path,
            expected_version="0.7.103",
        )
    assert caught.value.code is ErrorCode.RENDERER_UNAVAILABLE
    failed = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    assert failed.attempts[-1].status is StateCommitStatus.FAILED
    assert failed.attempts[-1].render_phase == "source"


def _replay_inputs(tmp_path: Path, attempt_id: str):
    project_factory.write_production_project(tmp_path)
    before = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    timeline = make_resolved_timeline()
    selection = RendererSelectionReceipt(
        receipt_id=f"selection-{attempt_id}",
        attempt_id=attempt_id,
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=before.active_project,
        current_registry=before.active_registry,
    )
    tools = tmp_path / "tools"
    tools.mkdir()
    browser = _write_executable(tools / "chrome")
    ip_path = _write_executable(tools / "ip")
    return (
        before,
        timeline,
        BeginRenderAttemptRequest(before.manifest_revision, None, selection),
        browser,
        ip_path,
    )


def _fake_probe(fd: int) -> dict[str, object]:
    del fd
    return {
        "streams": [
            {
                "codec_type": "video",
                "width": 320,
                "height": 180,
                "r_frame_rate": "24/1",
                "nb_frames": "10",
                "codec_name": "h264",
            }
        ]
    }


def _fake_decoded_frames(fd: int) -> str:
    return hashlib.sha256(os.pread(fd, os.fstat(fd).st_size, 0)).hexdigest()


def _call_fake_render(
    tmp_path: Path,
    *,
    request: BeginRenderAttemptRequest,
    timeline: ResolvedTimeline,
    browser: Path,
    ip_path: Path,
    runner_factory,
    committer: ProductionStateCommitter | None = None,
):
    return _render_with_hyperframes(
        committer=committer or ProductionStateCommitter(tmp_path),
        begin_request=request,
        timeline=timeline,
        asset_sources=make_asset_sources(tmp_path, timeline),
        allowed_asset_root=tmp_path,
        runner_factory=runner_factory,
        browser_path=browser,
        ip_path=ip_path,
        expected_version="0.7.103",
        probe=_fake_probe,
        decoded_frames=_fake_decoded_frames,
    )


def test_orchestrator_success_replay_returns_without_runner_or_artifact_rewrite(
    tmp_path,
):
    before, timeline, request, browser, ip_path = _replay_inputs(
        tmp_path, "success-replay"
    )
    first = _call_fake_render(
        tmp_path,
        request=request,
        timeline=timeline,
        browser=browser,
        ip_path=ip_path,
        runner_factory=FakeRunner,
    )
    manifest_path = tmp_path / "state/manifest.json"
    before_manifest_bytes = manifest_path.read_bytes()
    durable = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (tmp_path / "state/render").rglob("*")
        if path.is_file() and "attempts" not in path.parts
    }
    runner_calls = 0

    def forbidden_runner():
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("success replay must not construct a runner")

    replay = _call_fake_render(
        tmp_path,
        request=request,
        timeline=timeline,
        browser=browser,
        ip_path=ip_path,
        runner_factory=forbidden_runner,
    )

    assert replay == first
    assert replay.manifest_revision == before.manifest_revision + 3
    assert manifest_path.read_bytes() == before_manifest_bytes
    assert runner_calls == 0
    assert {
        path: (path.read_bytes(), path.stat().st_mtime_ns) for path in durable
    } == durable


def test_orchestrator_failed_replay_returns_terminal_without_runner(tmp_path):
    before, timeline, request, browser, ip_path = _replay_inputs(
        tmp_path, "failed-replay"
    )
    with pytest.raises(AiVideoError):
        _call_fake_render(
            tmp_path,
            request=request,
            timeline=timeline,
            browser=browser,
            ip_path=ip_path,
            runner_factory=lambda: FakeRunner(version="0.7.102"),
        )
    failed_bytes = (tmp_path / "state/manifest.json").read_bytes()
    runner_calls = 0

    def forbidden_runner():
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("failed replay must not construct a runner")

    replay = _call_fake_render(
        tmp_path,
        request=request,
        timeline=timeline,
        browser=browser,
        ip_path=ip_path,
        runner_factory=forbidden_runner,
    )

    assert replay.manifest_revision == before.manifest_revision + 2
    assert replay.attempts[-1].status is StateCommitStatus.FAILED
    assert (tmp_path / "state/manifest.json").read_bytes() == failed_bytes
    assert runner_calls == 0


def test_orchestrator_old_failed_attempt_is_not_replayed_after_later_state_change(
    tmp_path,
):
    _, timeline, failed_request, browser, ip_path = _replay_inputs(
        tmp_path, "old-failed-replay"
    )
    with pytest.raises(AiVideoError):
        _call_fake_render(
            tmp_path,
            request=failed_request,
            timeline=timeline,
            browser=browser,
            ip_path=ip_path,
            runner_factory=lambda: FakeRunner(version="0.7.102"),
        )
    current = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    later_selection = failed_request.renderer_selection.model_copy(
        update={
            "receipt_id": "selection-later-success",
            "attempt_id": "later-success",
            "current_project": current.active_project,
            "current_registry": current.active_registry,
        }
    )
    later_request = BeginRenderAttemptRequest(
        current.manifest_revision, None, later_selection
    )
    _call_fake_render(
        tmp_path,
        request=later_request,
        timeline=timeline,
        browser=browser,
        ip_path=ip_path,
        runner_factory=FakeRunner,
    )
    runner_calls = 0

    def forbidden_runner():
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("historical replay must not construct a runner")

    with pytest.raises(AiVideoError) as exc_info:
        _call_fake_render(
            tmp_path,
            request=failed_request,
            timeline=timeline,
            browser=browser,
            ip_path=ip_path,
            runner_factory=forbidden_runner,
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert runner_calls == 0


def test_orchestrator_unresolved_selection_replay_fails_closed_without_runner(
    tmp_path,
):
    before, timeline, request, browser, ip_path = _replay_inputs(
        tmp_path, "unresolved-selection"
    )
    committer = ProductionStateCommitter(tmp_path)
    begun = committer.begin_render_attempt(request)
    runner_calls = 0

    def forbidden_runner():
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("unresolved replay must not construct a runner")

    with pytest.raises(AiVideoError) as exc_info:
        _call_fake_render(
            tmp_path,
            request=request,
            timeline=timeline,
            browser=browser,
            ip_path=ip_path,
            runner_factory=forbidden_runner,
            committer=committer,
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    unchanged = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    assert unchanged == begun
    assert unchanged.manifest_revision == before.manifest_revision + 1
    assert unchanged.attempts[-1].status is StateCommitStatus.RUNNING
    assert runner_calls == 0


def test_orchestrator_candidate_replay_finalizes_without_rerendering_scratch(
    tmp_path,
):
    before, timeline, request, browser, ip_path = _replay_inputs(
        tmp_path, "candidate-replay"
    )
    committer = ProductionStateCommitter(
        tmp_path,
        crash_injector=_RaiseRenderPhaseOnce(
            CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_REPLACE,
            KeyboardInterrupt,
        ),
    )
    with pytest.raises(KeyboardInterrupt):
        _call_fake_render(
            tmp_path,
            request=request,
            timeline=timeline,
            browser=browser,
            ip_path=ip_path,
            runner_factory=FakeRunner,
            committer=committer,
        )
    candidate = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    assert candidate.manifest_revision == before.manifest_revision + 2
    assert candidate.attempts[-1].candidate_render_state is not None
    scratch = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (tmp_path / "state/render/attempts").rglob("*")
        if path.is_file()
    }
    runner_calls = 0

    def forbidden_runner():
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("candidate replay must not construct a runner")

    replay = _call_fake_render(
        tmp_path,
        request=request,
        timeline=timeline,
        browser=browser,
        ip_path=ip_path,
        runner_factory=forbidden_runner,
    )

    assert replay.manifest_revision == before.manifest_revision + 3
    assert replay.attempts[-1].status is StateCommitStatus.SUCCEEDED
    assert runner_calls == 0
    assert {
        path: (path.read_bytes(), path.stat().st_mtime_ns) for path in scratch
    } == scratch


def test_orchestrator_candidate_replay_rejects_tampered_durable_graph(
    tmp_path,
):
    _, timeline, request, browser, ip_path = _replay_inputs(
        tmp_path, "candidate-replay-tamper"
    )
    crashing = ProductionStateCommitter(
        tmp_path,
        crash_injector=_RaiseRenderPhaseOnce(
            CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_REPLACE,
            KeyboardInterrupt,
        ),
    )
    with pytest.raises(KeyboardInterrupt):
        _call_fake_render(
            tmp_path,
            request=request,
            timeline=timeline,
            browser=browser,
            ip_path=ip_path,
            runner_factory=FakeRunner,
            committer=crashing,
        )
    candidate_path = tmp_path / "state/manifest.json"
    candidate_bytes = candidate_path.read_bytes()
    candidate = ProductionManifest.model_validate_json(candidate_bytes)
    pointer = candidate.attempts[-1].candidate_render_state
    assert pointer is not None
    state = production.RenderStateSnapshot.model_validate_json(
        (tmp_path / pointer.path).read_bytes()
    )
    (tmp_path / state.output.path).write_bytes(b"tampered-output")
    runner_calls = 0

    def forbidden_runner():
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("tampered replay must not construct a runner")

    with pytest.raises(AiVideoError):
        _call_fake_render(
            tmp_path,
            request=request,
            timeline=timeline,
            browser=browser,
            ip_path=ip_path,
            runner_factory=forbidden_runner,
        )

    assert candidate_path.read_bytes() == candidate_bytes
    assert runner_calls == 0


def test_orchestrator_records_plain_version_exception_as_source_failure(tmp_path):
    before, timeline, request, browser, ip_path = _replay_inputs(
        tmp_path, "version-exception"
    )

    class VersionExceptionRunner(FakeRunner):
        def version(self, *, env):
            del env
            raise RuntimeError("version probe failed")

    with pytest.raises(RuntimeError, match="version probe"):
        _call_fake_render(
            tmp_path,
            request=request,
            timeline=timeline,
            browser=browser,
            ip_path=ip_path,
            runner_factory=VersionExceptionRunner,
        )

    failed = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    assert failed.manifest_revision == before.manifest_revision + 2
    assert failed.attempts[-1].status is StateCommitStatus.FAILED
    assert failed.attempts[-1].render_phase == "source"


@pytest.mark.parametrize("phase", ["source", "lint", "check", "render", "verify"])
def test_orchestrator_records_every_ordinary_phase_and_never_leaves_running(
    tmp_path, phase
):
    before, timeline, request, browser, ip_path = _replay_inputs(
        tmp_path, f"ordinary-{phase}"
    )
    runner_factory = (
        (lambda: (_ for _ in ()).throw(OSError("source construction failed")))
        if phase == "source"
        else (lambda: FakeRunner(fail_at=phase))
    )
    probe = (
        (lambda fd: (_ for _ in ()).throw(RuntimeError("verify failed")))
        if phase == "verify"
        else _fake_probe
    )

    with pytest.raises(Exception):
        _render_with_hyperframes(
            committer=ProductionStateCommitter(tmp_path),
            begin_request=request,
            timeline=timeline,
            asset_sources=make_asset_sources(tmp_path, timeline),
            allowed_asset_root=tmp_path,
            runner_factory=runner_factory,
            browser_path=browser,
            ip_path=ip_path,
            expected_version="0.7.103",
            probe=probe,
            decoded_frames=_fake_decoded_frames,
        )

    failed = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    assert failed.manifest_revision == before.manifest_revision + 2
    assert failed.attempts[-1].status is StateCommitStatus.FAILED
    assert failed.attempts[-1].render_phase == phase
    assert not any(
        item.status is StateCommitStatus.RUNNING for item in failed.attempts
    )


def test_orchestrator_does_not_retry_outer_failure_after_activation_owns_it(
    tmp_path,
):
    _, timeline, request, browser, ip_path = _replay_inputs(
        tmp_path, "activation-no-outer-retry"
    )
    committer = ProductionStateCommitter(
        tmp_path,
        crash_injector=_RaiseRenderPhaseOnce(
            CommitPhase.BEFORE_RENDER_CANDIDATE_MANIFEST_SERIALIZATION
        ),
    )
    record_calls = 0
    original_record = committer.record_render_failure

    def tracked_record(failure):
        nonlocal record_calls
        record_calls += 1
        return original_record(failure)

    committer.record_render_failure = tracked_record  # type: ignore[method-assign]

    with pytest.raises(AiVideoError):
        _call_fake_render(
            tmp_path,
            request=request,
            timeline=timeline,
            browser=browser,
            ip_path=ip_path,
            runner_factory=FakeRunner,
            committer=committer,
        )

    terminal = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    assert terminal.attempts[-1].status is StateCommitStatus.FAILED
    assert terminal.attempts[-1].render_phase == "activate"
    assert record_calls == 0


class _RaiseRenderPhaseOnce:
    def __init__(
        self, phase: CommitPhase, exception_type: type[BaseException] = OSError
    ) -> None:
        self.phase = phase
        self.exception_type = exception_type
        self.raised = False

    def checkpoint(self, phase: CommitPhase) -> None:
        if phase is self.phase and not self.raised:
            self.raised = True
            raise self.exception_type(f"injected {phase.value}")


def _run_injected_activation(tmp_path: Path, phase: CommitPhase):
    project_factory.write_production_project(tmp_path)
    before = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    timeline = make_resolved_timeline()
    selection = RendererSelectionReceipt(
        receipt_id=f"selection-{phase.value}",
        attempt_id=f"attempt-{phase.value}",
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=before.active_project,
        current_registry=before.active_registry,
    )
    tools = tmp_path / "tools"
    tools.mkdir()
    browser = _write_executable(tools / "chrome")
    ip_path = _write_executable(tools / "ip")
    committer = ProductionStateCommitter(
        tmp_path, crash_injector=_RaiseRenderPhaseOnce(phase)
    )
    with pytest.raises(AiVideoError) as caught:
        _render_with_hyperframes(
            committer=committer,
            begin_request=BeginRenderAttemptRequest(before.manifest_revision, None, selection),
            timeline=timeline,
            asset_sources=make_asset_sources(tmp_path, timeline),
            allowed_asset_root=tmp_path,
            runner_factory=lambda: FakeRunner(),
            browser_path=browser,
            ip_path=ip_path,
            expected_version="0.7.103",
            probe=lambda fd: {
                "streams": [
                    {
                        "codec_type": "video",
                        "width": 320,
                        "height": 180,
                        "r_frame_rate": "24/1",
                        "nb_frames": "10",
                        "codec_name": "h264",
                    }
                ]
            },
            decoded_frames=lambda fd: hashlib.sha256(
                os.pread(fd, os.fstat(fd).st_size, 0)
            ).hexdigest(),
        )
    manifest = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    return before, caught.value, manifest


@pytest.mark.parametrize(
    "phase",
    [
        CommitPhase.BEFORE_RENDER_CANDIDATE_MANIFEST_SERIALIZATION,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_OPEN,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_FILE_FSYNC,
        CommitPhase.BEFORE_RENDER_CANDIDATE_MANIFEST_REPLACE,
    ],
)
def test_activation_candidate_pre_replace_ordinary_failure_is_terminal_r2(
    tmp_path, phase
):
    before, error, manifest = _run_injected_activation(tmp_path, phase)
    assert error.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert manifest.manifest_revision == before.manifest_revision + 2
    attempt = manifest.attempts[-1]
    assert attempt.status is StateCommitStatus.FAILED
    assert attempt.render_phase == "activate"
    assert attempt.candidate_render_state is not None
    assert manifest.active_render_state is None


@pytest.mark.parametrize(
    "phase",
    [
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_REPLACE,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_DIRECTORY_FSYNC,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_VERIFICATION,
    ],
)
def test_activation_candidate_post_replace_ordinary_failure_is_terminal_r3(
    tmp_path, phase
):
    before, error, manifest = _run_injected_activation(tmp_path, phase)
    assert error.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert manifest.manifest_revision == before.manifest_revision + 3
    assert manifest.attempts[-1].status is StateCommitStatus.FAILED
    assert manifest.attempts[-1].candidate_render_state is not None
    assert manifest.active_render_state is None


@pytest.mark.parametrize(
    "phase",
    [
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_FILE_FSYNC,
        CommitPhase.BEFORE_RENDER_FINAL_MANIFEST_REPLACE,
    ],
)
def test_activation_final_pre_replace_ordinary_failure_is_terminal_r3(
    tmp_path, phase
):
    before, error, manifest = _run_injected_activation(tmp_path, phase)
    assert error.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert manifest.manifest_revision == before.manifest_revision + 3
    assert manifest.attempts[-1].status is StateCommitStatus.FAILED
    assert manifest.active_render_state is None


@pytest.mark.parametrize(
    "phase",
    [
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_REPLACE,
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_DIRECTORY_FSYNC,
    ],
)
def test_activation_final_post_replace_ambiguity_is_outcome_unknown(tmp_path, phase):
    before, error, manifest = _run_injected_activation(tmp_path, phase)
    assert error.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    assert manifest.manifest_revision == before.manifest_revision + 3
    assert manifest.attempts[-1].status is StateCommitStatus.SUCCEEDED
    assert manifest.active_render_state is not None


@pytest.mark.parametrize("authoritative", ["r1", "r2"])
def test_candidate_ambiguity_accepts_only_exact_r1_or_r2_identity(
    tmp_path, authoritative
):
    before, committer, request = _prepared_activation_request(
        tmp_path, f"candidate-exact-{authoritative}"
    )
    original = committer._write_render_manifest_atomic

    def ambiguous(manifest, *, candidate, on_replace):
        if candidate and authoritative == "r1":
            raise OSError("ambiguous before candidate replace")
        original(manifest, candidate=candidate, on_replace=on_replace)
        if candidate:
            raise OSError("ambiguous after candidate replace")

    committer._write_render_manifest_atomic = ambiguous  # type: ignore[method-assign]

    with pytest.raises(AiVideoError) as exc_info:
        committer.activate_render_state(request)

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    terminal = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    expected_revision = before.manifest_revision + (2 if authoritative == "r1" else 3)
    assert terminal.manifest_revision == expected_revision
    assert terminal.attempts[-1].status is StateCommitStatus.FAILED


def test_candidate_ambiguity_tampered_r2_is_outcome_unknown_without_overwrite(
    tmp_path,
):
    _, committer, request = _prepared_activation_request(
        tmp_path, "candidate-tampered-r2"
    )
    original = committer._write_render_manifest_atomic

    def tamper_then_raise(manifest, *, candidate, on_replace):
        original(manifest, candidate=candidate, on_replace=on_replace)
        if candidate:
            path = tmp_path / "state/manifest.json"
            current = ProductionManifest.model_validate_json(path.read_text())
            attempt = current.attempts[-1].model_copy(
                update={"candidate_artifacts_hash": "f" * 64}
            )
            tampered = current.model_copy(
                update={"attempts": (*current.attempts[:-1], attempt)}
            )
            path.write_text(tampered.model_dump_json(indent=2), encoding="utf-8")
            raise OSError("candidate identity changed")

    committer._write_render_manifest_atomic = tamper_then_raise  # type: ignore[method-assign]

    with pytest.raises(AiVideoError) as exc_info:
        committer.activate_render_state(request)

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    authoritative = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    assert authoritative.attempts[-1].status is StateCommitStatus.RUNNING
    assert authoritative.attempts[-1].candidate_artifacts_hash == "f" * 64


def test_candidate_ambiguity_mixed_r2_fails_closed_without_terminal_overwrite(
    tmp_path,
):
    _, committer, request = _prepared_activation_request(
        tmp_path, "candidate-mixed-r2"
    )
    original = committer._write_render_manifest_atomic

    def mix_then_raise(manifest, *, candidate, on_replace):
        original(manifest, candidate=candidate, on_replace=on_replace)
        if candidate:
            path = tmp_path / "state/manifest.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["active_render_state"] = request.next_render_state.model_dump(
                mode="json"
            )
            path.write_text(json.dumps(payload), encoding="utf-8")
            raise OSError("candidate active identity mixed")

    committer._write_render_manifest_atomic = mix_then_raise  # type: ignore[method-assign]

    with pytest.raises(AiVideoError) as exc_info:
        committer.activate_render_state(request)

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    raw = json.loads((tmp_path / "state/manifest.json").read_text(encoding="utf-8"))
    assert raw["active_render_state"] == request.next_render_state.model_dump(
        mode="json"
    )
    assert raw["attempts"][-1]["status"] == StateCommitStatus.RUNNING.value


def test_final_ambiguity_malformed_authoritative_manifest_is_outcome_unknown(
    tmp_path,
):
    _, committer, request = _prepared_activation_request(
        tmp_path, "final-malformed-manifest"
    )
    original = committer._write_render_manifest_atomic

    def corrupt_final_then_raise(manifest, *, candidate, on_replace):
        original(manifest, candidate=candidate, on_replace=on_replace)
        if not candidate:
            (tmp_path / "state/manifest.json").write_text("{", encoding="utf-8")
            raise OSError("final authoritative manifest became unreadable")

    committer._write_render_manifest_atomic = corrupt_final_then_raise  # type: ignore[method-assign]

    with pytest.raises(AiVideoError) as exc_info:
        committer.activate_render_state(request)

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    assert (tmp_path / "state/manifest.json").read_text(encoding="utf-8") == "{"


def test_recovery_resolves_candidate_prepared_render_by_exact_old_triple_and_preserves_orphans(
    tmp_path,
):
    project_factory.write_production_project(tmp_path)
    before = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    timeline = make_resolved_timeline()
    selection = RendererSelectionReceipt(
        receipt_id="selection-candidate-crash",
        attempt_id="candidate-crash",
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=before.active_project,
        current_registry=before.active_registry,
    )
    tools = tmp_path / "tools"
    tools.mkdir()
    browser = _write_executable(tools / "chrome")
    ip_path = _write_executable(tools / "ip")
    committer = ProductionStateCommitter(
        tmp_path,
        crash_injector=_RaiseRenderPhaseOnce(
            CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_REPLACE,
            KeyboardInterrupt,
        ),
    )
    with pytest.raises(KeyboardInterrupt):
        _render_with_hyperframes(
            committer=committer,
            begin_request=BeginRenderAttemptRequest(before.manifest_revision, None, selection),
            timeline=timeline,
            asset_sources=make_asset_sources(tmp_path, timeline),
            allowed_asset_root=tmp_path,
            runner_factory=lambda: FakeRunner(),
            browser_path=browser,
            ip_path=ip_path,
            expected_version="0.7.103",
            probe=lambda fd: {
                "streams": [
                    {
                        "codec_type": "video",
                        "width": 320,
                        "height": 180,
                        "r_frame_rate": "24/1",
                        "nb_frames": "10",
                        "codec_name": "h264",
                    }
                ]
            },
            decoded_frames=lambda fd: hashlib.sha256(
                os.pread(fd, os.fstat(fd).st_size, 0)
            ).hexdigest(),
        )
    candidate = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    pointer = candidate.attempts[-1].candidate_render_state
    assert pointer is not None
    assert candidate.active_render_state is None
    assert candidate.attempts[-1].status is StateCommitStatus.RUNNING

    report = committer.recover()
    recovered = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    assert recovered.attempts[-1].status is StateCommitStatus.INTERRUPTED
    assert recovered.active_render_state is None
    assert any(
        item.path == pointer.path and item.disposition.value == "orphan_preserved"
        for item in report.items
    )
    assert not any(
        path.is_file()
        for path in committer.render_attempt_paths(selection.attempt_id).attempt_root.rglob("*")
    )
