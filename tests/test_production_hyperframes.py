from __future__ import annotations

import hashlib
import json
import math
import os
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.composition import timeline_fingerprint
from ai_video.production.hashing import seal_artifact
from ai_video.production.hyperframes import (
    _capture_safe_boundary_percent,
    _css_visibility_keyframes,
    _parse_source_document,
    _seconds,
    audit_hyperframes_source,
    materialize_hyperframes_source,
)
from ai_video.production.models import (
    DeliveryProfile,
    FixedTransform,
    RendererIdentity,
    RendererKind,
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
        .a{background:url('style.png')}@import "import.css";
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
    assert parsed.css_imports == ("import.css",)


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
