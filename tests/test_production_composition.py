from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.captions import CaptionImportRequest, caption_timing_fingerprint
from ai_video.production.composition import resolve_composition
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AudioKind,
    AudioTrackSpec,
    AssetRoleRequirement,
    AssetType,
    CaptionTrack,
    CaptionTrackBinding,
    CompositionLayerSpec,
    CompositionSpec,
    DurationPolicy,
    DuckingSpec,
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
    make_p4_composition_fixture,
    write_and_load_two_shot_project,
)


def _assert_invalid(project, spec) -> AiVideoError:
    with pytest.raises(AiVideoError) as caught:
        resolve_composition(project, spec, renderer_version="0.7.103")
    assert caught.value.code is ErrorCode.COMPOSITION_INVALID
    assert caught.value.retryable is False
    return caught.value


def _assert_error(project, spec, code: ErrorCode) -> AiVideoError:
    with pytest.raises(AiVideoError) as caught:
        resolve_composition(project, spec, renderer_version="0.7.103")
    assert caught.value.code is code
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


def _with_overlapping_caption_binding(root, loaded, spec):
    source_asset = loaded.registry.assets[-1]
    source_path = loaded.asset_paths[source_asset.asset_id]
    track = CaptionTrack.model_validate_json(source_path.read_bytes())
    segments = tuple(
        segment.model_copy(update={"segment_id": f"second-{segment.segment_id}"})
        for segment in track.segments
    )
    second_track = track.model_copy(
        update={
            "artifact_id": "caption-artifact-2",
            "content_hash": "0" * 64,
            "creation_receipt_id": "receipt-caption-2",
            "caption_track_id": "caption-track-2",
            "segments": segments,
            "timing_fingerprint": "0" * 64,
        }
    )
    second_track = second_track.model_copy(
        update={"timing_fingerprint": caption_timing_fingerprint(second_track)}
    )
    second_track = CaptionTrack.model_validate(
        seal_artifact(second_track).model_dump(mode="python")
    )
    style = spec.caption_tracks[0].style_reference
    assert style is not None
    style_bytes = (root / style.path).read_bytes()
    imported = CaptionImportRequest.create(
        caption_track=second_track,
        style_reference=style,
        style_bytes=style_bytes,
    )
    second_path = root / "assets/files/caption-track-2.json"
    second_path.write_bytes(imported.track_bytes)
    metadata = source_asset.caption_metadata
    assert metadata is not None
    second_asset = source_asset.model_copy(
        update={
            "asset_id": "caption-asset-2",
            "artifact_path": second_path.relative_to(root),
            "sha256": hashlib.sha256(imported.track_bytes).hexdigest(),
            "size_bytes": len(imported.track_bytes),
            "creation_receipt_id": "receipt-caption-asset-2",
            "caption_metadata": metadata.model_copy(
                update={
                    "caption_track_id": second_track.caption_track_id,
                    "timing_fingerprint": second_track.timing_fingerprint,
                }
            ),
        }
    )
    assets = (*loaded.registry.assets, second_asset)
    paths = dict(loaded.asset_paths)
    paths[second_asset.asset_id] = second_path
    loaded = loaded.model_copy(
        update={
            "registry": loaded.registry.model_copy(update={"assets": assets}),
            "asset_paths": paths,
        }
    )
    second_binding = CaptionTrackBinding(
        binding_id="captions-dialogue-2",
        caption_asset_id=second_asset.asset_id,
        source_audio_track_id="dialogue",
        shot_id="shot-1",
        style_reference=style,
    )
    spec = seal_artifact(
        spec.model_copy(
            update={
                "content_hash": "0" * 64,
                "caption_tracks": (*spec.caption_tracks, second_binding),
            }
        )
    )
    return loaded, spec


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


def test_p4_resolves_all_audio_kinds_and_captions_in_one_timeline(tmp_path):
    loaded, spec = make_p4_composition_fixture(tmp_path)
    timeline = resolve_composition(loaded, spec, "0.7.103")

    assert timeline.schema_version == "2.1"
    assert {span.audio_kind for span in timeline.audio_spans} == set(AudioKind)
    assert [(span.track_id, span.start_sample) for span in timeline.audio_spans] == [
        ("dialogue", 0),
        ("narration", 96_000),
        ("ambience", 0),
        ("sfx", 100_000),
        ("bgm", 0),
    ]
    bgm = next(span for span in timeline.audio_spans if span.track_id == "bgm")
    assert (bgm.gain_millidb, bgm.fade_in_samples, bgm.fade_out_samples) == (
        -6_000,
        2_000,
        2_000,
    )
    assert bgm.ducking is not None
    assert bgm.ducking.sidechain_track_ids == ("dialogue", "narration")
    assert [
        (cue.start_sample, cue.end_sample, cue.start_frame, cue.end_frame_exclusive)
        for cue in timeline.caption_cues
    ] == [(1_000, 23_000, 0, 12), (24_000, 47_000, 12, 24)]
    assert timeline.caption_cues[0].style_reference_id == "caption-style-1"


def test_p4_resolution_is_independent_of_audio_and_caption_input_order(tmp_path):
    loaded, spec = make_p4_composition_fixture(tmp_path)
    first = resolve_composition(loaded, spec, "0.7.103")
    reordered = seal_artifact(
        spec.model_copy(
            update={
                "content_hash": "0" * 64,
                "audio_tracks": tuple(reversed(spec.audio_tracks)),
                "caption_tracks": tuple(reversed(spec.caption_tracks)),
            }
        )
    )
    second = resolve_composition(loaded, reordered, "0.7.103")
    assert second.audio_spans == first.audio_spans
    assert second.caption_cues == first.caption_cues
    assert second.composition_fingerprint == first.composition_fingerprint


def test_overlapping_caption_tracks_are_canonical_and_input_order_independent(tmp_path):
    loaded, spec = make_p4_composition_fixture(tmp_path)
    loaded, spec = _with_overlapping_caption_binding(tmp_path, loaded, spec)
    first = resolve_composition(loaded, spec, "0.7.103")
    assert len(first.caption_cues) == 4
    assert first.caption_cues[0].start_sample == first.caption_cues[1].start_sample
    assert [cue.caption_track_id for cue in first.caption_cues[:2]] == [
        "caption-track-1",
        "caption-track-2",
    ]

    reversed_spec = seal_artifact(
        spec.model_copy(
            update={
                "content_hash": "0" * 64,
                "caption_tracks": tuple(reversed(spec.caption_tracks)),
            }
        )
    )
    second = resolve_composition(loaded, reversed_spec, "0.7.103")
    assert second.caption_cues == first.caption_cues
    assert second.composition_fingerprint == first.composition_fingerprint


def test_p4_trim_gain_fade_and_short_audio_silence_pad_are_deterministic(tmp_path):
    loaded, spec = make_p4_composition_fixture(tmp_path)
    dialogue = spec.audio_tracks[0].model_copy(
        update={
            "trim_start_sample": 2_000,
            "trim_duration_samples": 40_000,
            "gain_millidb": -1_500,
            "fade_in_samples": 1_000,
            "fade_out_samples": 2_000,
        }
    )
    no_captions = seal_artifact(
        spec.model_copy(
            update={
                "content_hash": "0" * 64,
                "audio_tracks": (dialogue,),
                "caption_tracks": (),
            }
        )
    )
    timeline = resolve_composition(loaded, no_captions, "0.7.103")
    assert timeline.total_samples == 192_000
    span = timeline.audio_spans[0]
    assert (
        span.source_start_sample,
        span.source_duration_samples,
        span.duration_samples,
        span.gain_millidb,
        span.fade_in_samples,
        span.fade_out_samples,
    ) == (2_000, 40_000, 40_000, -1_500, 1_000, 2_000)

    late_trimmed = dialogue.model_copy(
        update={"start_sample": 150_000, "trim_duration_samples": 40_000}
    )
    trimmed_timeline = resolve_composition(
        loaded,
        seal_artifact(
            spec.model_copy(
                update={
                    "content_hash": "0" * 64,
                    "audio_tracks": (late_trimmed,),
                    "caption_tracks": (),
                }
            )
        ),
        "0.7.103",
    )
    assert trimmed_timeline.audio_spans[0].start_sample == 150_000
    assert trimmed_timeline.audio_spans[0].duration_samples == 40_000


def test_p4_rejects_sample_rate_mismatch_and_untrimmed_overrun(tmp_path):
    loaded, spec = make_p4_composition_fixture(tmp_path)
    mismatched = _replace_asset(
        loaded,
        2,
        audio_metadata=loaded.registry.assets[2].audio_metadata.model_copy(
            update={"sample_rate_hz": 44_100}
        ),
    )
    _assert_error(mismatched, spec, ErrorCode.AUDIO_TIMELINE_INVALID)

    overrun = spec.audio_tracks[0].model_copy(update={"start_sample": 150_000})
    _assert_error(
        loaded,
        seal_artifact(
            spec.model_copy(
                update={
                    "content_hash": "0" * 64,
                    "audio_tracks": (overrun,),
                    "caption_tracks": (),
                }
            )
        ),
        ErrorCode.AUDIO_TIMELINE_INVALID,
    )


def test_p4_rejects_unknown_wrong_type_wrong_hash_and_invalid_ducking(tmp_path):
    loaded, spec = make_p4_composition_fixture(tmp_path)
    dialogue = spec.audio_tracks[0]
    cases = (
        dialogue.model_copy(update={"asset_id": "missing"}),
        dialogue.model_copy(update={"asset_id": "image-shot-1"}),
        dialogue.model_copy(update={"audio_kind": AudioKind.BGM}),
    )
    for track in cases:
        _assert_error(
            loaded,
            seal_artifact(
                spec.model_copy(
                    update={
                        "content_hash": "0" * 64,
                        "audio_tracks": (track,),
                        "caption_tracks": (),
                    }
                )
            ),
            ErrorCode.AUDIO_TIMELINE_INVALID,
        )
    _assert_error(
        _replace_asset(loaded, 2, sha256="f" * 64),
        spec,
        ErrorCode.AUDIO_TIMELINE_INVALID,
    )

    bgm = spec.audio_tracks[-1].model_copy(
        update={
            "ducking": spec.audio_tracks[-1].ducking.model_copy(
                update={"sidechain_track_ids": ("missing",)}
            )
        }
    )
    _assert_error(
        loaded,
        seal_artifact(
            spec.model_copy(
                update={
                    "content_hash": "0" * 64,
                    "audio_tracks": (bgm,),
                    "caption_tracks": (),
                }
            )
        ),
        ErrorCode.AUDIO_TIMELINE_INVALID,
    )

    dialogue_ducks_bgm = dialogue.model_copy(
        update={
            "ducking": DuckingSpec(
                sidechain_track_ids=("bgm",),
                attenuation_millidb=-3_000,
                attack_samples=0,
                release_samples=0,
            )
        }
    )
    bgm_ducks_dialogue = spec.audio_tracks[-1].model_copy(
        update={
            "ducking": spec.audio_tracks[-1].ducking.model_copy(
                update={"sidechain_track_ids": ("dialogue",)}
            )
        }
    )
    _assert_error(
        loaded,
        seal_artifact(
            spec.model_copy(
                update={
                    "content_hash": "0" * 64,
                    "audio_tracks": (dialogue_ducks_bgm, bgm_ducks_dialogue),
                    "caption_tracks": (),
                }
            )
        ),
        ErrorCode.AUDIO_TIMELINE_INVALID,
    )


def test_voice_driven_uses_one_frame_snapped_speech_driver_and_bounds(tmp_path):
    loaded, spec = make_p4_composition_fixture(tmp_path)
    loaded = _replace_shot(
        loaded,
        0,
        duration_policy=DurationPolicy(
            mode="voice_driven", minimum_seconds=1.0, maximum_seconds=2.0
        ),
    )
    spec = seal_artifact(
        spec.model_copy(
            update={
                "content_hash": "0" * 64,
                "audio_tracks": (spec.audio_tracks[0],),
                "caption_tracks": (),
            }
        )
    )
    timeline = resolve_composition(loaded, spec, "0.7.103")
    assert timeline.visual_spans[0].duration_frames == 48
    assert timeline.visual_spans[1].start_sample == 96_000

    two_drivers = seal_artifact(
        spec.model_copy(
            update={
                "content_hash": "0" * 64,
                "audio_tracks": (
                    spec.audio_tracks[0],
                    spec.audio_tracks[0].model_copy(update={"track_id": "driver-2"}),
                ),
            }
        )
    )
    _assert_error(loaded, two_drivers, ErrorCode.AUDIO_TIMELINE_INVALID)
    too_short = _replace_shot(
        loaded,
        0,
        duration_policy=DurationPolicy(mode="voice_driven", minimum_seconds=2.1),
    )
    _assert_error(too_short, spec, ErrorCode.AUDIO_TIMELINE_INVALID)


def test_voice_driven_rejects_missing_unaligned_driver_and_content_driven(tmp_path):
    loaded, spec = make_p4_composition_fixture(tmp_path)
    voice_shot = _replace_shot(
        loaded,
        0,
        duration_policy=DurationPolicy(mode="voice_driven", minimum_seconds=1.0),
    )
    without_driver = seal_artifact(
        spec.model_copy(
            update={
                "content_hash": "0" * 64,
                "audio_tracks": (),
                "caption_tracks": (),
            }
        )
    )
    _assert_error(voice_shot, without_driver, ErrorCode.AUDIO_TIMELINE_INVALID)

    metadata = loaded.registry.assets[2].audio_metadata.model_copy(
        update={"duration_samples": 95_999}
    )
    unaligned = _replace_asset(
        loaded,
        2,
        audio_metadata=metadata,
        duration_seconds=95_999 / 48_000,
    )
    one_driver = seal_artifact(
        spec.model_copy(
            update={
                "content_hash": "0" * 64,
                "audio_tracks": (spec.audio_tracks[0],),
                "caption_tracks": (),
            }
        )
    )
    _assert_error(
        _replace_shot(
            unaligned,
            0,
            duration_policy=DurationPolicy(mode="voice_driven", minimum_seconds=1.0),
        ),
        one_driver,
        ErrorCode.AUDIO_TIMELINE_INVALID,
    )
    content = _replace_shot(
        loaded,
        0,
        duration_policy=DurationPolicy(mode="content_driven", minimum_seconds=1.0),
    )
    _assert_invalid(content, spec)


def test_caption_binding_rejects_unknown_type_hash_source_and_style_mismatch(tmp_path):
    loaded, spec = make_p4_composition_fixture(tmp_path)
    binding = spec.caption_tracks[0]
    cases = (
        binding.model_copy(update={"caption_asset_id": "missing"}),
        binding.model_copy(update={"caption_asset_id": "image-shot-1"}),
        binding.model_copy(update={"source_audio_track_id": "narration"}),
    )
    for candidate in cases:
        _assert_error(
            loaded,
            seal_artifact(
                spec.model_copy(
                    update={"content_hash": "0" * 64, "caption_tracks": (candidate,)}
                )
            ),
            ErrorCode.CAPTION_TRACK_INVALID,
        )
    _assert_error(
        _replace_asset(loaded, -1, sha256="f" * 64),
        spec,
        ErrorCode.CAPTION_TRACK_INVALID,
    )
    assert binding.style_reference is not None
    for wrong_style in (
        binding.style_reference.model_copy(update={"content_hash": "f" * 64}),
        binding.style_reference.model_copy(
            update={"path": Path("assets/styles/missing.json")}
        ),
    ):
        _assert_error(
            loaded,
            seal_artifact(
                spec.model_copy(
                    update={
                        "content_hash": "0" * 64,
                        "caption_tracks": (
                            binding.model_copy(update={"style_reference": wrong_style}),
                        ),
                    }
                )
            ),
            ErrorCode.CAPTION_TRACK_INVALID,
        )
    wrong_style = binding.style_reference.model_copy(update={"artifact_id": "wrong"})
    _assert_error(
        loaded,
        seal_artifact(
            spec.model_copy(
                update={
                    "content_hash": "0" * 64,
                    "caption_tracks": (
                        binding.model_copy(update={"style_reference": wrong_style}),
                    ),
                }
            )
        ),
        ErrorCode.CAPTION_TRACK_INVALID,
    )


@pytest.mark.parametrize("mutation", ["mime", "pretty", "reordered", "malformed"])
def test_caption_asset_requires_json_mime_and_exact_canonical_bytes(tmp_path, mutation):
    loaded, spec = make_p4_composition_fixture(tmp_path)
    caption = loaded.registry.assets[-1]
    path = loaded.asset_paths[caption.asset_id]
    if mutation == "mime":
        loaded = _replace_asset(loaded, -1, mime_type="text/plain")
    else:
        original = path.read_bytes()
        parsed = json.loads(original)
        if mutation == "pretty":
            payload = json.dumps(parsed, indent=2).encode("utf-8")
        elif mutation == "reordered":
            payload = json.dumps(
                dict(reversed(tuple(parsed.items()))), separators=(",", ":")
            ).encode("utf-8")
        else:
            payload = b"{malformed"
        path.write_bytes(payload)
        loaded = _replace_asset(
            loaded,
            -1,
            sha256=hashlib.sha256(payload).hexdigest(),
            size_bytes=len(payload),
        )
    _assert_error(loaded, spec, ErrorCode.CAPTION_TRACK_INVALID)


def test_caption_style_changes_composition_not_timing_fingerprint(tmp_path):
    loaded, spec = make_p4_composition_fixture(tmp_path)
    first = resolve_composition(loaded, spec, "0.7.103")
    binding = spec.caption_tracks[0]
    original = binding.style_reference
    assert original is not None
    revised_bytes = b'{"font_family":"Different","schema_version":"1"}'
    revised_hash = hashlib.sha256(revised_bytes).hexdigest()
    revised_path = tmp_path / "assets/styles" / f"{revised_hash}.json"
    revised_path.write_bytes(revised_bytes)
    revised_style = original.model_copy(
        update={"content_hash": revised_hash, "path": revised_path.relative_to(tmp_path)}
    )
    caption = loaded.registry.assets[-1]
    revised_caption = caption.model_copy(
        update={
            "caption_metadata": caption.caption_metadata.model_copy(
                update={"style_content_hash": revised_hash}
            )
        }
    )
    revised_loaded = _replace_asset(
        loaded,
        -1,
        caption_metadata=revised_caption.caption_metadata,
    )
    revised_spec = seal_artifact(
        spec.model_copy(
            update={
                "content_hash": "0" * 64,
                "caption_tracks": (
                    binding.model_copy(update={"style_reference": revised_style}),
                ),
            }
        )
    )
    second = resolve_composition(revised_loaded, revised_spec, "0.7.103")
    assert (
        second.caption_cues[0].caption_timing_fingerprint
        == first.caption_cues[0].caption_timing_fingerprint
    )
    assert second.composition_fingerprint != first.composition_fingerprint


def test_silent_20_serialization_and_fingerprint_stay_exact(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    timeline = resolve_composition(loaded, spec, "0.7.103")
    payload = timeline.model_dump(mode="json")
    assert timeline.schema_version == "2.0"
    assert "audio_spans" not in payload
    assert "caption_cues" not in payload
    assert timeline.composition_fingerprint == (
        "b77173e6cb88738003a390b2397c797776fc7019b113b491deabb3b30f26da7f"
    )


def test_composition_module_has_no_second_timeline_owner():
    import ai_video.production.composition as composition

    assert not any(
        name.startswith("Resolved") and name.endswith("Timeline")
        for name in vars(composition)
        if name != "ResolvedTimeline"
    )


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
            assert os.lseek(source_fd, 0, os.SEEK_CUR) == 3
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


def test_nofollow_read_rejects_parent_directory_replacement(tmp_path, monkeypatch):
    root = tmp_path / "source"
    parent = root / "nested"
    parent.mkdir(parents=True)
    source = parent / "asset.bin"
    source.write_bytes(b"original")
    real_read = os.read
    replaced = False

    def replace_parent_then_read(descriptor: int, size: int) -> bytes:
        nonlocal replaced
        if not replaced:
            replaced = True
            parent.rename(root / "detached")
            parent.mkdir()
            (parent / "asset.bin").write_bytes(b"replacement")
        return real_read(descriptor, size)

    monkeypatch.setattr(os, "read", replace_parent_then_read)
    with pytest.raises(ValueError, match="directory changed"):
        _read_regular_file_nofollow(source, contained_by=root)


def test_nofollow_read_rejects_symlink_directory_and_fifo(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    target = root / "target.bin"
    target.write_bytes(b"target")
    symlink = root / "link.bin"
    symlink.symlink_to(target)
    directory = root / "directory"
    directory.mkdir()
    fifo = root / "pipe"
    os.mkfifo(fifo)

    for rejected in (symlink, directory, fifo):
        with pytest.raises(ValueError, match="non-symlink regular file"):
            _read_regular_file_nofollow(rejected, contained_by=root)


def test_nofollow_create_rejects_existing_destination(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    destination = root / "existing.bin"
    destination.write_bytes(b"existing")
    with pytest.raises(FileExistsError):
        _create_regular_file_nofollow(
            destination,
            data=b"replacement",
            contained_by=root,
        )
    assert destination.read_bytes() == b"existing"


def test_nofollow_list_rejects_recursive_child_directory_replacement(
    tmp_path, monkeypatch
):
    root = tmp_path / "source"
    child = root / "child"
    child.mkdir(parents=True)
    (child / "original.bin").write_bytes(b"original")
    real_listdir = os.listdir
    list_calls = 0

    def replace_child_after_listing(descriptor: int) -> list[str]:
        nonlocal list_calls
        entries = real_listdir(descriptor)
        list_calls += 1
        if list_calls == 2:
            child.rename(root / "detached")
            child.mkdir()
            (child / "replacement.bin").write_bytes(b"replacement")
        return entries

    monkeypatch.setattr(os, "listdir", replace_child_after_listing)
    with pytest.raises(ValueError, match="source directory changed"):
        _list_regular_files_nofollow(root)
