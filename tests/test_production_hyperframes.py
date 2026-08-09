from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

import pytest

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
    _seconds,
    _validate_local_relative_url,
    audit_hyperframes_source,
    materialize_hyperframes_source,
)
from ai_video.production.models import (
    DeliveryProfile,
    FixedTransform,
    RendererIdentity,
    RendererKind,
    RendererSelectionReceipt,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    ResolvedTimeline,
    ResolvedVisualSpan,
    SourceReference,
    TransitionKind,
    TransitionSpec,
)


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
