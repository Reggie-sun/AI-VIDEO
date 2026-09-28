from __future__ import annotations

import copy
import hashlib
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.comfy_t8_native_turbo_profile import (
    load_t8_native_turbo_binding,
    load_t8_native_turbo_execution_profile,
    validate_native_turbo_workflow,
)
from ai_video.production.comfy_t8_native_turbo_video import (
    ComfyUIT8NativeTurboVideoProvider,
    render_t8_native_turbo_workflow,
    t8_native_turbo_capabilities,
    _long_reference_prompt,
)
from ai_video.production._h3_prompt import H3PromptCompilation
from ai_video.production.video import ProviderProfilePointer, VideoGenerationRequest
from ai_video.production.local_h3_provider_family import LocalH3VideoProviderFamily
from ai_video.production.local_video import LocalVideoSubmitIntent
from ai_video.production.comfy_t8_native_turbo_profile import T8NativeTurboRuntimeInspection
from ai_video.workflow_loader import load_workflow_template
from test_production_comfy_t8_native_turbo_video import REPO_ROOT, _image, _load, _request


LONG_PATH = REPO_ROOT / "workflows/profiles/minimax_h3_t8_ref2va_turbo_native_17s_v3.json"


def _long():
    return load_t8_native_turbo_execution_profile(LONG_PATH, artifact_root=REPO_ROOT)


def _long_request(profile):
    request = _request(profile, image_bindings=(_image("reference", "scene", "a"),))
    values = request.model_dump(mode="python", exclude={"request_input_hash"})
    values["provider_profile"] = ProviderProfilePointer(
        profile_id=profile.capability_id,
        profile_version=profile.profile_version,
        profile_path=Path(f"provider-profiles/{profile.profile_content_hash}.json"),
        profile_sha256=profile.profile_content_hash,
    )
    values["output_requirement"] = request.output_requirement.model_copy(
        update={"frame_count": 408}
    )
    return VideoGenerationRequest.create(**values)


def _provider(profile, tmp_path):
    return ComfyUIT8NativeTurboVideoProvider(
        profile, artifact_root=REPO_ROOT, comfy_root=tmp_path,
        input_root=tmp_path, asset_resolver=lambda _: None,
        runtime_inspector=lambda: pytest.fail("resolve must not inspect runtime"),
    )


def test_long_output_is_exact_17_seconds_and_old_lane_is_unchanged():
    short, long = _load("Ref2VA"), _long()
    assert short.frame_count == 124
    assert short.profile_content_hash == "0bb8ebf9688369f89d959d8273a81f73dcc6e02e96c1a20a52110583ace7db9d"
    assert long.frame_count == 408 and long.sampling_frame_count == 413
    assert long.frame_count / long.fps == 17
    assert long.schema_version == "3" and long.profile_version == "v3"
    assert long.capability_id != short.capability_id
    capability = t8_native_turbo_capabilities(long).variants[0]
    assert capability.output_capability.frame_count_min == 408
    assert capability.output_capability.frame_count_max == 408
    assert capability.output_capability.supports(_long_request(long).output_requirement)


def test_long_render_samples_once_and_trims_both_av_streams(tmp_path):
    profile = _long()
    provider = _provider(profile, tmp_path)
    request = provider.resolve(_long_request(profile))
    template = load_workflow_template(REPO_ROOT / profile.workflow_path)
    binding = load_t8_native_turbo_binding((REPO_ROOT / profile.binding_path).read_bytes())
    rendered = render_t8_native_turbo_workflow(
        template=template, binding=binding, request=request, profile=profile,
        uploaded_images=("scene.png", "coco.png", "nosha.png"),
        uploaded_videos=(), uploaded_audios=("voice.mp3",),
    )
    assert rendered["6"]["inputs"]["length"] == 413
    assert rendered["13"]["inputs"] == {
        "frames": ["11", 0], "audio": ["11", 1],
        "start_seconds": 0.0, "duration_seconds": 17.0, "fps": 24.0,
    }
    assert rendered["12"]["inputs"]["images"] == ["13", 0]
    assert rendered["12"]["inputs"]["audio"] == ["13", 1]
    assert rendered["6"]["inputs"]["ref_images.ref_image_0"] == ["14", 0]
    assert rendered["6"]["inputs"]["ref_audios.ref_audio_0"] == ["17", 0]
    assert sum(n["class_type"] == "SamplerCustomAdvanced" for n in rendered.values()) == 1


@pytest.mark.parametrize("field,value", [("frame_count", 413), ("sampling_frame_count", 408), ("profile_version", "v2"), ("task_type", "I2VA")])
def test_resealed_long_contract_cannot_change_timing_or_identity(field, value):
    profile = _long()
    values = profile.model_dump(mode="python", exclude={"profile_content_hash"})
    values[field] = value
    with pytest.raises(ValueError):
        type(profile).create(**values)


@pytest.mark.parametrize("node,field,value", [
    ("13", "start_seconds", 1.0), ("13", "duration_seconds", 15.0),
    ("13", "audio", ["11", 0]), ("12", "images", ["11", 0]),
    ("12", "audio", ["11", 1]), ("6", "length", 124),
])
def test_long_topology_cannot_bypass_or_shift_output_padding_trim(node, field, value):
    profile = _long()
    workflow = copy.deepcopy(load_workflow_template(REPO_ROOT / profile.workflow_path))
    binding = load_t8_native_turbo_binding((REPO_ROOT / profile.binding_path).read_bytes())
    workflow[node]["inputs"][field] = value
    with pytest.raises(AiVideoError):
        validate_native_turbo_workflow(profile, workflow, binding)


def test_long_request_cannot_resolve_through_short_adapter(tmp_path):
    with pytest.raises(AiVideoError):
        _provider(_load("Ref2VA"), tmp_path).resolve(_long_request(_long()))


def test_short_request_cannot_resolve_through_long_adapter(tmp_path):
    with pytest.raises(AiVideoError):
        _provider(_long(), tmp_path).resolve(
            _request(_load("Ref2VA"), image_bindings=(_image("reference", "scene", "a"),))
        )


def test_explicit_family_routes_short_and_long_by_exact_identity(tmp_path):
    family = LocalH3VideoProviderFamily(
        (_provider(_load("Ref2VA"), tmp_path), _provider(_long(), tmp_path))
    )
    request = _long_request(_long())
    resolved = family.resolve(request)
    assert resolved.capability_id == _long().capability_id
    assert resolved.effective_output.frame_count == 408
    assert family.preview(resolved).resolved_generation_hash == resolved.resolved_generation_hash


def test_long_submit_consumes_exact_permit_before_any_upload(tmp_path, monkeypatch):
    import test_production_comfy_t8_native_turbo_video as helpers

    original_load = helpers._load
    monkeypatch.setattr(helpers, "_load", lambda task: _long() if task == "Ref2VA" else original_load(task))
    profile, comfy_root, input_root, schemas = helpers._live_ready_sandbox(tmp_path, "Ref2VA")
    payload = b"\x89PNG\r\n\x1a\nsealed-long-reference"
    frame = input_root / "scene.png"
    frame.write_bytes(payload)
    request = _long_request(profile)
    values = request.model_dump(mode="python", exclude={"request_input_hash"})
    values["image_bindings"] = (request.image_bindings[0].model_copy(update={
        "asset_sha256": hashlib.sha256(payload).hexdigest(), "size_bytes": len(payload),
    }),)
    request = VideoGenerationRequest.create(**values)
    transport = helpers._NoEffectTransport()
    transport.get_object_info = lambda: schemas
    provider = ComfyUIT8NativeTurboVideoProvider(
        profile, artifact_root=REPO_ROOT, comfy_root=comfy_root, input_root=input_root,
        asset_resolver=lambda *_: frame, transport=transport,
        runtime_inspector=lambda: T8NativeTurboRuntimeInspection(
            comfyui_commit=profile.comfyui_commit, t8_commit=profile.t8_commit,
            t8_version=profile.t8_version, videohelpersuite_commit=profile.videohelpersuite_commit,
            sageattention_version=profile.sageattention_version, launch_capabilities=("sage_attention",),
        ),
    )
    resolved = provider.resolve(request)
    preview = provider.preview(resolved)
    intent = LocalVideoSubmitIntent.create(
        attempt_id="long-attempt", request=resolved, preview=preview,
        recorded_at=datetime.now(UTC),
    )
    bad = helpers._Permit("0" * 64, resolved.resolved_generation_hash)
    with pytest.raises(AiVideoError):
        provider.submit_local(resolved, preview, intent, bad)
    assert transport.uploads == transport.posts == []
    permit = helpers._Permit(intent.intent_fingerprint, resolved.resolved_generation_hash)
    provider.submit_local(resolved, preview, intent, permit)
    assert permit.consumed
    assert len(transport.posts) == 1
    assert transport.posts[0]["6"]["inputs"]["length"] == 413
    # Durable permit owner denies consumption after use; the adapter must honor it.
    monkeypatch.setattr(permit, "_consume_local_video_submit_permit", lambda **_: False)
    with pytest.raises(AiVideoError):
        provider.submit_local(resolved, preview, intent, permit)
    assert len(transport.posts) == 1 and len(transport.uploads) == 1


def test_native_reference_ordinals_follow_compiler_sorting_and_single_speaker():
    text = (
        "integrated_multimodal_description: [Shot 1] Speaker 1 says <d>[Chinese] 你好</d>\n"
        "overall_soundscape: room\nnon_diegetic_music: none"
    )
    prompt = H3PromptCompilation(prompt_text=text, prompt_sha256=hashlib.sha256(text.encode()).hexdigest())
    asset = lambda aid, kind, owner: SimpleNamespace(
        asset_id=aid, canonical_owner_kind=kind, canonical_owner_id=owner,
    )
    bound = SimpleNamespace(
        binding_roles=("reference", "reference_audio", "reference"),
        input_assets=(asset("z-scene", "scene", "shelter"), asset("voice", None, None), asset("a-coco", "character", "COCO")),
    )
    requirement = SimpleNamespace(generation_intent=SimpleNamespace(
        dialogue_intent=SimpleNamespace(mode="dialogue", speaker_id="COCO"),
    ))
    result = _long_reference_prompt(prompt, bound, requirement)
    assert "<Picture 1> is the character reference for COCO." in result.prompt_text
    assert "<Picture 2> is the scene reference for shelter." in result.prompt_text
    assert "Speaker 1 (S1), COCO, preserves the voice, timbre and pitch range of <Audio 1>." in result.prompt_text
    assert len(result.prompt_text.splitlines()) == 3
    assert result.prompt_text.count("<d>[Chinese] 你好</d>") == 1


@pytest.mark.parametrize("marker", [False, True])
def test_reference_cues_require_native_marker_and_do_not_expose_asset_ids(marker):
    text = "integrated_multimodal_description: " + ("[Shot 1] " if marker else "") + "action\noverall_soundscape: room\nnon_diegetic_music: none"
    prompt = H3PromptCompilation(prompt_text=text, prompt_sha256=hashlib.sha256(text.encode()).hexdigest())
    bound = SimpleNamespace(binding_roles=("reference", "reference_audio"), input_assets=(
        SimpleNamespace(asset_id="opaque-image-id", canonical_owner_kind=None, canonical_owner_id=None),
        SimpleNamespace(asset_id="opaque-audio-id", canonical_owner_kind=None, canonical_owner_id=None),
    ))
    requirement = SimpleNamespace(generation_intent=SimpleNamespace(dialogue_intent=None))
    if not marker:
        with pytest.raises(AiVideoError):
            _long_reference_prompt(prompt, bound, requirement)
        return
    result = _long_reference_prompt(prompt, bound, requirement)
    assert "opaque-image-id" not in result.prompt_text
    assert "opaque-audio-id" not in result.prompt_text
    assert "<Picture 1>" in result.prompt_text and "<Audio 1>" in result.prompt_text
