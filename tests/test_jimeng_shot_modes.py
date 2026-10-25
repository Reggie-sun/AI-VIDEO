"""Jimeng mode profiles preserve a selected native Shot input contract."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_video.production.jimeng_contracts import JimengProfile
from ai_video.production.jimeng_models import JIMENG_MODEL_SPECS
from ai_video.production.video import VideoGenerationMode


MODEL_IDS = tuple(JIMENG_MODEL_SPECS)
INPUT_MODES = (
    ("text_to_video", 1, VideoGenerationMode.TEXT_TO_VIDEO, (), "firstLastFrame"),
    ("first_frame", 2, VideoGenerationMode.IMAGE_TO_VIDEO, ("first_frame",), "firstLastFrame"),
    ("first_last_frame", 3, VideoGenerationMode.IMAGE_TO_VIDEO,
     ("first_frame", "last_frame"), "firstLastFrame"),
    ("multimodal", 4, VideoGenerationMode.REFERENCE_TO_VIDEO, ("reference",), "multiModal"),
)


def _profile(model_id: str, input_mode: str) -> JimengProfile:
    spec = JIMENG_MODEL_SPECS[model_id]
    return JimengProfile(
        model_id=model_id,
        input_mode=input_mode,
        account_sha256="a" * 64,
        project_id="f0ed223b-090e-4ed6-b394-283f8b7dbd07",
        node_id="node_bq6wajb5xe",
        duration_seconds=min(5, spec.max_seconds),
        resolution=spec.resolutions[0],
        aspect_ratio="16:9",
        benefit_amount=min(5, spec.max_seconds),
        benefit_type="selected_output",
        credit_upper_bound=500,
    )


@pytest.mark.parametrize("model_id", MODEL_IDS)
@pytest.mark.parametrize("input_mode,native_mode,request_mode,roles,editor_mode", INPUT_MODES)
def test_each_model_declares_all_verified_shot_modes(
    model_id, input_mode, native_mode, request_mode, roles, editor_mode,
):
    from ai_video.production.jimeng import JimengVideoProvider

    profile = _profile(model_id, input_mode)
    provider = JimengVideoProvider(
        profile=profile, transport=object(), reference_resolver=lambda _: b"", committer=object()
    )
    capability = provider.capabilities().variants[0]

    assert profile.native_mode == native_mode
    assert capability.mode is request_mode
    assert capability.allowed_image_roles == roles
    assert capability.production_qualification == "UNQUALIFIED"
    if input_mode in {"first_frame", "first_last_frame"}:
        import hashlib

        from ai_video.production.video import VideoImageReferenceBinding
        from test_production_minimax_h3 import _request

        images = tuple(VideoImageReferenceBinding(
            role=role, asset_id=role,
            asset_sha256=hashlib.sha256(role.encode()).hexdigest(),
            size_bytes=len(role), mime_type="image/png", width=720, height=1280,
        ) for role in roles)
        request = _request(
            provider_name="jimeng", provider_kind="jimeng", model_id=model_id,
            provider_profile=profile.pointer(), mode=request_mode,
            prompt_text="从首帧开始，保持人物与动作连续，到达真实尾帧。",
            image_bindings=images, media_bindings=(), output_requirement=profile.output(),
        )
        assert tuple(binding.role for binding in provider.resolve(request).image_bindings) == roles


@pytest.mark.parametrize("model_id", MODEL_IDS)
@pytest.mark.parametrize("input_mode,native_mode,request_mode,roles,editor_mode", INPUT_MODES)
def test_native_commercial_and_editor_modes_match_sealed_profile(
    model_id, input_mode, native_mode, request_mode, roles, editor_mode,
):
    worker = Path(__file__).parents[1] / "src/ai_video/production/jimeng_browser.cjs"
    script = """
      const {buildVideoAction, buildVideoEditorDraft}=require(process.argv[1]);
      const x=JSON.parse(process.argv[2]);
      const action=buildVideoAction({model_id:x.model_id,input_mode:x.input_mode,
        duration_seconds:5,benefit_amount:5,resolution:'720p'},
        x.materials);
      const draft=buildVideoEditorDraft(null,{mode:x.native_mode,model_name:x.model_id,
        aspect_ratio:'16:9',resolution:'720p',duration_ms:5000});
      console.log(JSON.stringify({action,draft}));
    """
    result = subprocess.run(
        ["node", "-e", script, str(worker), json.dumps({
            "model_id": model_id, "input_mode": input_mode, "native_mode": native_mode,
            "materials": [
                {"kind": "image", "image_role": None if role == "reference" else role}
                if role in {"reference", "first_frame", "last_frame"}
                else {"kind": "video" if role == "reference_video" else "audio", "image_role": None}
                for role in roles
            ],
        })],
        check=True, capture_output=True, text=True,
    )
    data = json.loads(result.stdout)
    expected_commerce = {
        1: "t2v", 2: "i2v", 3: "first_last_frame", 4: "multi_modal",
    }[native_mode]
    assert data["action"]["options"]["videoMode"] == expected_commerce
    assert data["draft"]["contentSettings"]["mode"] == editor_mode


def test_native_editor_defaults_missing_mode_to_legacy_multimodal():
    worker = Path(__file__).parents[1] / "src/ai_video/production/jimeng_browser.cjs"
    result = subprocess.run(
        ["node", "-e", "const {buildVideoEditorDraft}=require(process.argv[1]);"
         "console.log(buildVideoEditorDraft(null,{model_name:'seedance_2.0_mini',"
         "aspect_ratio:'16:9',resolution:'720p',duration_ms:5000})"
         ".contentSettings.mode);", str(worker)],
        check=True, capture_output=True, text=True,
    )
    assert result.stdout.strip() == "multiModal"


def test_all_models_allow_empty_material_text_request_but_reject_a_hidden_reference():
    from ai_video.production.jimeng import JimengVideoProvider
    from ai_video.production.video import VideoImageReferenceBinding
    from pydantic import ValidationError
    from test_production_minimax_h3 import _request

    for model_id in MODEL_IDS:
        profile = _profile(model_id, "text_to_video")
        provider = JimengVideoProvider(
            profile=profile, transport=object(), reference_resolver=lambda _: b"", committer=object()
        )
        request = _request(
            provider_name="jimeng", provider_kind="jimeng", model_id=model_id,
            provider_profile=profile.pointer(), mode=VideoGenerationMode.TEXT_TO_VIDEO,
            prompt_text="室内自然光下，主角从桌边走向窗户。", image_bindings=(), media_bindings=(),
            output_requirement=profile.output(),
        )
        assert provider.resolve(request).image_bindings == ()
        assert provider.capabilities().variants[0].max_reference_count == 0

        image = VideoImageReferenceBinding(
            role="reference", asset_id="hidden-image", asset_sha256="d" * 64,
            size_bytes=1, mime_type="image/png", width=640, height=640,
        )
        with pytest.raises(ValidationError):
            _request(
                provider_name="jimeng", provider_kind="jimeng", model_id=model_id,
                provider_profile=profile.pointer(), mode=VideoGenerationMode.TEXT_TO_VIDEO,
                prompt_text="{{image:0}}", image_bindings=(image,), media_bindings=(),
                output_requirement=profile.output(),
            )


def test_text_to_video_empty_material_dispatch_poll_and_fetch_preserve_identity():
    from io import BytesIO

    from ai_video.production.jimeng import JimengVideoProvider
    from ai_video.production.jimeng_contracts import dispatch_matches_request
    from ai_video.production.paid_provider import (
        PaidProviderAuthorizationDecision,
        PaidProviderCallPreview,
    )
    from ai_video.production.video import VideoSubmission, VideoTaskState, build_video_paid_permit_binding
    from test_production_jimeng import RESOURCE_ID, TASK_ID, accepted_receipt, setup
    from test_production_minimax_h3 import _real_permit, _request

    old_provider, _, _, old_paid, old_auth, _, browser, committer, raw = setup(
        model_id="seedance_2.0_vip"
    )
    profile = JimengProfile.model_validate({
        **old_provider._profile.model_dump(mode="json"),
        "input_mode": "text_to_video",
        "benefit_amount": 5,
    })
    provider = JimengVideoProvider(
        profile=profile, transport=browser,
        reference_resolver=lambda binding: raw[binding.asset_id],
        committer=committer, now=lambda: old_provider._now(),
    )
    request = _request(
        provider_name="jimeng", provider_kind="jimeng", model_id=profile.model_id,
        provider_profile=profile.pointer(), mode=VideoGenerationMode.TEXT_TO_VIDEO,
        prompt_text="一位女性从桌边走向窗边，镜头轻轻跟随。",
        image_bindings=(), media_bindings=(), output_requirement=profile.output(),
    )
    resolved = provider.resolve(request)
    video_preview = provider.preview(resolved)
    paid_values = old_paid.model_dump(mode="python", exclude={"preview_fingerprint"})
    paid_values.update(
        request_fingerprint=resolved.resolved_generation_hash,
        egress_items=provider.egress_items(resolved),
    )
    paid = PaidProviderCallPreview.create(**paid_values)
    auth_values = old_auth.model_dump(mode="python", exclude={"authorization_fingerprint"})
    auth_values["preview_fingerprint"] = paid.preview_fingerprint
    auth = PaidProviderAuthorizationDecision.create(**auth_values)
    permit = _real_permit(build_video_paid_permit_binding(resolved, video_preview, paid, auth))

    submitted = provider.submit(resolved, video_preview, paid, auth, permit)
    assert browser.uploads == []
    assert browser.params["mode"] == 1
    assert browser.params["materials"] == []
    assert "meta_list" not in browser.params
    assert committer.dispatch.materials == ()
    assert dispatch_matches_request(committer.dispatch, resolved)
    assert submitted.external_effect_id == f"{RESOURCE_ID}:{TASK_ID}"

    receipt = accepted_receipt(resolved, paid)
    submission = VideoSubmission.from_paid_submit_receipt(resolved=resolved, receipt=receipt)
    assert provider.get_status(submission, receipt).state is VideoTaskState.RUNNING
    browser.status = 1000
    observation = provider.get_status(submission, receipt)
    sink = BytesIO()
    fetched = provider.fetch(submission, receipt, observation, sink)
    assert fetched.artifact_sha256 == hashlib.sha256(browser.video_bytes).hexdigest()
    assert sink.getvalue() == browser.video_bytes


def _prompt_bound(model_id, input_mode, roles=(), asset_ids=()):
    from ai_video.production.jimeng_models import (
        jimeng_capability_id, jimeng_profile_compiler_id, jimeng_profile_version,
    )

    profile = _profile(model_id, input_mode)
    compiler_id = profile.compiler_id
    pairs = tuple((role, SimpleNamespace(asset_id=asset_id))
                  for role, asset_id in zip(roles, asset_ids, strict=True))
    return compiler_id, SimpleNamespace(
        requirement_hash="b" * 64,
        provider_bound_request_hash="c" * 64,
        provider_name="jimeng",
        provider_kind="jimeng",
        model_id=model_id,
        provider_profile=SimpleNamespace(profile_id="jimeng",
                                         profile_version=jimeng_profile_version(model_id, input_mode)),
        capability_id=jimeng_capability_id(model_id, input_mode),
        mode=VideoGenerationMode(JIMENG_INPUT_MODES_BY_NAME[input_mode][2]),
        compiler_contract=SimpleNamespace(compiler_id=compiler_id, compiler_version="1"),
        binding_roles=roles,
        input_assets=tuple(asset for _, asset in pairs),
        generation_recipe=None,
    )


JIMENG_INPUT_MODES_BY_NAME = {
    "text_to_video": (1, "", "text_to_video"),
    "first_frame": (2, "first-frame", "image_to_video"),
    "first_last_frame": (3, "first-last-frame", "image_to_video"),
    "multimodal": (4, "multimodal", "reference_to_video"),
}


def _mock_remote_prompt(monkeypatch, prompt):
    from ai_video.production import _remote_video_native_prompt as remote
    from ai_video.production._remote_video_native_prompt import RemoteVideoPromptCompilation

    calls = []

    def compile_prompt(requirement, **kwargs):
        calls.append(kwargs)
        return RemoteVideoPromptCompilation(
            prompt_text=prompt,
            prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        )

    monkeypatch.setattr(remote, "compile_remote_video_prompt", compile_prompt)
    return calls


@pytest.mark.parametrize("roles,asset_ids,expected", [
    (("reference",), ("image-1",), "\\n参考素材1 {{image:0}}"),
    (("reference_video",), ("video-1",), "\\n参考素材1 {{video:0}}"),
    (("reference_video", "reference_audio", "reference"),
     ("video-1", "audio-1", "image-1"),
     "\\n参考素材1 {{image:0}}\\n参考素材2 {{audio:1}}\\n参考素材3 {{video:2}}"),
])
def test_multimodal_reference_markers_follow_native_binding_order(monkeypatch, roles, asset_ids, expected):
    from ai_video.production.jimeng_prompt import compile_jimeng_native_prompt

    compiler_id, bound = _prompt_bound("seedance_2.0_vip", "multimodal", roles, asset_ids)
    calls = _mock_remote_prompt(monkeypatch, "描述画面")
    result = compile_jimeng_native_prompt(
        compiler_id=compiler_id, compiler_version="1", requirement=object(), provider_bound=bound,
    )

    assert result.prompt_text.endswith(expected.replace("\\n", "\n"))
    assert calls[0]["max_prompt_characters"] is None


def test_jimeng_prompt_limit_counts_final_native_utf16_units_including_markers(monkeypatch):
    from ai_video.production.jimeng_prompt import compile_jimeng_native_prompt
    from ai_video.production.video_compiler import ProviderRequirementUnsupported

    compiler_id, bound = _prompt_bound("seedance_2.0_vip", "multimodal",
                                       ("reference",), ("image-1",))
    _mock_remote_prompt(monkeypatch, "😀" * 1992)
    result = compile_jimeng_native_prompt(
        compiler_id=compiler_id, compiler_version="1", requirement=object(), provider_bound=bound,
    )
    assert isinstance(result, ProviderRequirementUnsupported)
    assert result.unsupported_field_paths == ("native_prompt.prompt_text.length",)


def test_jimeng_prompt_recompile_rejects_compiler_label_with_wrong_bound_model(monkeypatch):
    from ai_video.production.jimeng_prompt import compile_jimeng_native_prompt
    from ai_video.production.video_compiler import ProviderRequirementUnsupported

    compiler_id, bound = _prompt_bound("seedance_2.0_vip", "first_frame",
                                       ("first_frame",), ("frame-1",))
    bound.model_id = "seedance_2.5"
    _mock_remote_prompt(monkeypatch, "描述画面")
    result = compile_jimeng_native_prompt(
        compiler_id=compiler_id, compiler_version="1", requirement=object(), provider_bound=bound,
    )
    assert isinstance(result, ProviderRequirementUnsupported)
    assert result.unsupported_field_paths == ("selected_jimeng_mode_identity",)
