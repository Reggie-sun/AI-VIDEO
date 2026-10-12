"""Grok model inventory, output modes, and sealed hard-control tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_video.production._video_capability_fingerprint import (
    binding_roles_satisfy_variant,
    c4_exact_cardinality_grammar_satisfies_variant,
)
from ai_video.production.grok_profile import (
    GROK_VIDEO_MODEL_CLASSIC,
    GROK_VIDEO_MODEL_FULL,
    GROK_VIDEO_MODEL_LITE,
    GROK_VIDEO_MODELS,
    GrokProviderProfile,
    grok_capabilities,
)
from ai_video.production.grok_video_controls import GrokTimedKeyframe
from ai_video.production.video import VideoGenerationMode


ACCOUNT = "a" * 64
KEYFRAME_A = GrokTimedKeyframe(
    asset_id="keyframe-a", asset_sha256="b" * 64, timestamp_ticks=3
)
KEYFRAME_B = GrokTimedKeyframe(
    asset_id="keyframe-b", asset_sha256="c" * 64, timestamp_ticks=6
)


def _profile(**changes: object) -> GrokProviderProfile:
    return GrokProviderProfile(account_fingerprint=ACCOUNT, **changes)


def _variant(model_id: str, mode: VideoGenerationMode, *, profile=None):
    return next(
        item for item in grok_capabilities(profile).variants
        if item.model_id == model_id and item.mode is mode
    )


def test_default_profile_keeps_legacy_dump_and_content_addressed_hash():
    profile = _profile()

    assert "keyframes" not in profile.model_dump(mode="json")
    assert "reference_voices" not in profile.model_dump(mode="json")
    assert profile.pointer().profile_sha256 == (
        "12ac64f979fd0f61f00bf4265e3c3988b10647bf0a15035d57561dab2ac38193"
    )


def test_all_public_model_modes_have_explicit_capabilities():
    capabilities = grok_capabilities()
    expected = {
        GROK_VIDEO_MODEL_CLASSIC: {
            VideoGenerationMode.TEXT_TO_VIDEO,
            VideoGenerationMode.IMAGE_TO_VIDEO,
            VideoGenerationMode.REFERENCE_TO_VIDEO,
            VideoGenerationMode.VIDEO_EDIT,
            VideoGenerationMode.VIDEO_EXTEND,
        },
        GROK_VIDEO_MODEL_FULL: {
            VideoGenerationMode.TEXT_TO_VIDEO,
            VideoGenerationMode.IMAGE_TO_VIDEO,
            VideoGenerationMode.REFERENCE_TO_VIDEO,
        },
        GROK_VIDEO_MODEL_LITE: {
            VideoGenerationMode.TEXT_TO_VIDEO,
            VideoGenerationMode.IMAGE_TO_VIDEO,
        },
    }

    assert GROK_VIDEO_MODELS == tuple(expected)
    assert {
        model_id: {item.mode for item in capabilities.variants if item.model_id == model_id}
        for model_id in GROK_VIDEO_MODELS
    } == expected
    for item in capabilities.variants:
        assert item.output_capability is not None
        assert item.output_capability.fps_values == (None,)
        assert item.seed_supported is False
        assert item.negative_prompt_supported is False


def test_full_15_inventory_exposes_ratios_references_last_frame_and_static_c4():
    capabilities = grok_capabilities()
    ratio_variants = [
        item for item in capabilities.variants
        if item.model_id == GROK_VIDEO_MODEL_FULL
    ]
    official_ratios = {
        "21:9", "16:9", "4:3", "1:1", "3:4", "9:16", "3:2", "2:3", "5:2",
    }
    for item in ratio_variants:
        if item.mode is VideoGenerationMode.IMAGE_TO_VIDEO:
            assert item.output_capability.ratios == ("adaptive",)
        else:
            assert official_ratios <= set(item.output_capability.ratios)

    i2v = _variant(GROK_VIDEO_MODEL_FULL, VideoGenerationMode.IMAGE_TO_VIDEO)
    last_frame = next(
        item for item in ratio_variants
        if item.capability_id == "grok-imagine-video-1.5-i2v-last-frame-v1"
    )
    static_c4 = next(
        item for item in ratio_variants
        if item.capability_id == "grok-imagine-video-1.5-i2v-c4-static-v1"
    )
    r2v = _variant(GROK_VIDEO_MODEL_FULL, VideoGenerationMode.REFERENCE_TO_VIDEO)

    assert i2v.capability_id == "grok-imagine-video-1.5-i2v-v1"
    assert i2v.output_capability.resolution_labels == ("480p", "720p", "1080p")
    assert last_frame.allowed_image_roles == ("first_frame", "last_frame")
    assert last_frame.max_reference_count == 0
    assert static_c4.max_reference_count == 1
    assert static_c4.output_capability.resolution_labels == ("480p", "720p")
    assert static_c4.output_capability.timing_modes == ("exact_seconds",)
    assert not binding_roles_satisfy_variant(r2v, ("first_frame",))
    assert c4_exact_cardinality_grammar_satisfies_variant(static_c4, motion=False)
    assert not c4_exact_cardinality_grammar_satisfies_variant(i2v, motion=False)
    assert r2v.max_reference_count == 14
    assert r2v.output_capability.max_duration_seconds == 15
    assert set(r2v.allowed_image_roles) == {"first_frame", "last_frame", "reference"}
    assert binding_roles_satisfy_variant(r2v, ("last_frame",))
    assert binding_roles_satisfy_variant(r2v, ("first_frame", "reference"))
    assert binding_roles_satisfy_variant(
        r2v, ("first_frame", "last_frame", "reference")
    )
    assert not binding_roles_satisfy_variant(r2v, ())
    assert not binding_roles_satisfy_variant(r2v, ("reference",) * 15)


def test_classic_reference_edit_and_extension_bounds_are_explicit():
    capabilities = grok_capabilities()
    classic = [item for item in capabilities.variants if item.model_id == GROK_VIDEO_MODEL_CLASSIC]
    r2v = next(item for item in classic if item.mode is VideoGenerationMode.REFERENCE_TO_VIDEO)
    edit = next(item for item in classic if item.mode is VideoGenerationMode.VIDEO_EDIT)
    extend = next(item for item in classic if item.mode is VideoGenerationMode.VIDEO_EXTEND)

    assert r2v.max_reference_count == 7
    assert r2v.output_capability.max_duration_seconds == 10
    assert edit.media_capabilities[0].max_duration_millis == 8_700
    assert edit.media_capabilities[0].max_size_bytes == 128 * 1024 * 1024
    assert edit.output_capability.timing_modes == ("nominal_seconds", "provider_selected")
    assert edit.output_capability.max_duration_seconds == 9
    assert edit.output_capability.resolution_labels == ("source", "480p", "720p")
    assert edit.output_capability.native_audio_options == (True,)
    assert extend.media_capabilities[0].min_duration_millis == 2_000
    assert extend.media_capabilities[0].max_duration_millis == 15_000
    assert extend.output_capability.min_duration_seconds == 4
    assert extend.output_capability.max_duration_seconds == 25
    assert extend.output_capability.native_audio_options == (True,)
    assert edit.output_capability.ratios == ("adaptive",)
    assert extend.output_capability.ratios == ("adaptive",)
    assert all(
        item.output_capability.ratios == ("adaptive",)
        for item in classic if item.mode is VideoGenerationMode.IMAGE_TO_VIDEO
    )


def test_full_video_profile_controls_change_hash_and_limit_variant_inventory():
    baseline = _profile()
    keyed = _profile(keyframes=(KEYFRAME_A, KEYFRAME_B))
    voiced = _profile(reference_voices=("ara", "rex", "eve"))

    assert keyed.pointer().profile_sha256 != baseline.pointer().profile_sha256
    assert voiced.pointer().profile_sha256 != baseline.pointer().profile_sha256
    assert {
        item.model_id for item in grok_capabilities(keyed).variants
    } == {GROK_VIDEO_MODEL_FULL}
    assert {
        item.model_id for item in grok_capabilities(voiced).variants
    } == {GROK_VIDEO_MODEL_FULL}
    assert all(
        item.output_capability.resolution_labels == ("480p", "720p")
        for item in grok_capabilities(keyed).variants
    )
    assert all(
        item.output_capability.resolution_labels == ("480p", "720p")
        for item in grok_capabilities(voiced).variants
    )
    assert all(
        item.output_capability.native_audio_options == (True,)
        for item in grok_capabilities(voiced).variants
    )
    assert not any(
        item.mode is VideoGenerationMode.TEXT_TO_VIDEO
        for item in grok_capabilities(keyed).variants
    )
    keyed_i2v = next(
        item for item in grok_capabilities(keyed).variants
        if item.mode is VideoGenerationMode.IMAGE_TO_VIDEO
        and "last-frame" not in item.capability_id
    )
    keyed_r2v = next(
        item for item in grok_capabilities(keyed).variants
        if item.mode is VideoGenerationMode.REFERENCE_TO_VIDEO
    )
    assert keyed_i2v.max_reference_count == 16
    assert keyed_r2v.max_reference_count == 16
    assert next(
        item.min_count for item in keyed_i2v.binding_cardinality_constraints
        if item.roles == ("reference",)
    ) == 2
    assert binding_roles_satisfy_variant(keyed_r2v, ("reference", "reference"))
    assert binding_roles_satisfy_variant(
        keyed_r2v, ("last_frame", "reference", "reference")
    )
    assert binding_roles_satisfy_variant(
        keyed_r2v, ("first_frame", "reference", "reference")
    )
    assert not binding_roles_satisfy_variant(keyed_r2v, ("reference",))
    assert not binding_roles_satisfy_variant(keyed_r2v, ())
    assert next(
        item.min_count for item in keyed_r2v.binding_cardinality_constraints
        if item.roles == ("reference",)
    ) == 2


def test_voice_conditioned_r2v_may_omit_images_but_unconditioned_r2v_cannot():
    baseline_r2v = _variant(GROK_VIDEO_MODEL_FULL, VideoGenerationMode.REFERENCE_TO_VIDEO)
    voice_r2v = _variant(
        GROK_VIDEO_MODEL_FULL,
        VideoGenerationMode.REFERENCE_TO_VIDEO,
        profile=_profile(reference_voices=("ara",)),
    )

    assert not binding_roles_satisfy_variant(baseline_r2v, ())
    assert binding_roles_satisfy_variant(voice_r2v, ())
    assert binding_roles_satisfy_variant(voice_r2v, ("last_frame",))


@pytest.mark.parametrize(
    "keyframes",
    [
        (KEYFRAME_B, KEYFRAME_A),
        (KEYFRAME_A, GrokTimedKeyframe(
            asset_id="keyframe-c", asset_sha256="d" * 64, timestamp_ticks=3,
        )),
        (KEYFRAME_A, GrokTimedKeyframe(asset_id=KEYFRAME_A.asset_id,
            asset_sha256="f" * 64, timestamp_ticks=4)),
        tuple(
            GrokTimedKeyframe(
                asset_id=f"keyframe-{index}",
                asset_sha256=f"{index:x}" * 64,
                timestamp_ticks=index,
            )
            for index in range(1, 6)
        ),
    ],
)
def test_invalid_keyframe_order_identity_or_count_is_rejected(keyframes):
    with pytest.raises(ValidationError):
        _profile(keyframes=keyframes)


@pytest.mark.parametrize("voices", [("Ara",), ("voice one",), ("声音",), ("ara", "ara"),
                                    ("a", "b", "c", "d")])
def test_noncanonical_duplicate_or_excess_voice_ids_are_rejected(voices):
    with pytest.raises(ValidationError):
        _profile(reference_voices=voices)


def test_keyframe_timestamp_requires_a_positive_strict_integer():
    with pytest.raises(ValidationError):
        GrokTimedKeyframe(asset_id="key", asset_sha256="a" * 64, timestamp_ticks=True)
    with pytest.raises(ValidationError):
        GrokTimedKeyframe(asset_id="key", asset_sha256="a" * 64, timestamp_ticks=0)
    with pytest.raises(ValidationError):
        GrokTimedKeyframe(asset_id="key", asset_sha256="a" * 64, timestamp_ticks=45)
