"""Offline contract tests for the Jimeng canvas Provider."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.jimeng import JimengVideoProvider, jimeng_meta_list
from ai_video.production.jimeng_contracts import (
    JimengProfile, dispatch_matches_request,
)
from ai_video.production.models import ActorIdentity
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision, PaidProviderCallPreview,
    PaidProviderSubmitOutcome, PaidProviderSubmitReceipt, SecretReference,
)
from ai_video.production.video import (
    VideoGenerationMode, VideoImageReferenceBinding, VideoMediaReferenceBinding,
    VideoSubmission, VideoTaskState, build_video_paid_permit_binding,
)
from test_production_minimax_h3 import _real_permit, _request


NOW = datetime(2026, 10, 21, 10, 0, tzinfo=UTC)
SUBMIT_ID = "cedcb4bc-5bb5-4c8e-9c10-278f4f388518"
RESOURCE_ID = "71949d15-dac1-4642-b83c-24f238650876"
TASK_ID = "23681081680140"


class FakeCommitter:
    def __init__(self):
        self.dispatch = None
        self.canvas = None

    def record_jimeng_dispatch(self, value):
        if self.dispatch is not None:
            raise ValueError("duplicate dispatch")
        self.dispatch = value

    def read_jimeng_dispatch(self, attempt_id):
        assert self.dispatch.attempt_id == attempt_id
        return self.dispatch

    def read_jimeng_canvas_snapshot(self, attempt_id, *, required=True):
        return self.canvas

    def record_jimeng_canvas_snapshot(self, value):
        assert self.canvas is None
        self.canvas = value
        return value


class FakeBrowser:
    def __init__(self):
        self.uploads = []
        self.params = None
        self.calls = 0
        self.status = 200
        self.fail_after_admit = False
        self.fail_read = False
        self.fail_canvas = False
        self.on_upload = None
        self.on_dispatch = None
        self.video_bytes = b"\x00\x00\x00\x18ftypmp42" + b"video bytes"

    def upload(self, *, profile, kind, payload, mime_type):
        self.uploads.append((kind, payload, mime_type))
        if self.on_upload is not None:
            self.on_upload()
        return f"stored-{kind}-{len(self.uploads)}"

    def submit_native(self, *, profile, video_params, materials, admit):
        self.calls += 1
        self.params = video_params
        self.materials = materials
        if self.on_dispatch is not None:
            self.on_dispatch()
        admit(SUBMIT_ID, RESOURCE_ID)
        if self.fail_after_admit:
            raise TimeoutError("response lost")
        return {"submit_id": SUBMIT_ID, "resource_id": RESOURCE_ID, "task_id": TASK_ID}

    def read_resource(self, *, profile, resource_id):
        if self.fail_read:
            raise TimeoutError("read unavailable")
        assert resource_id == RESOURCE_ID
        return {"resource_id": resource_id, "submit_id": SUBMIT_ID,
                "project_id": profile.project_id, "task_id": TASK_ID,
                "status": self.status,
                "video": {"gen": self.params, "vid": "video-123"},
                "download_url": "https://example.invalid/fresh-url"}

    def read_saved_canvas(self, *, profile, resource_id):
        if self.fail_canvas:
            raise TimeoutError("canvas save unavailable")
        return {"draft_version": 4, "head_draft_version": 4,
                "draft_json": json.dumps({"draftVersion": 4, "edges": [],
                    "nodes": [{"id": profile.node_id,
                               "data": {"resourceId": resource_id}}]})}

    def download(self, *, url, sink):
        assert url == "https://example.invalid/fresh-url"
        sink.write(self.video_bytes)
        return len(self.video_bytes), hashlib.sha256(self.video_bytes).hexdigest()


def setup(prompt="Scene {{image:0}} voice {{audio:1}} motion {{video:2}}", *, model_id="seedance_2.5"):
    raw = {"image-a": b"image bytes", "audio-a": b"audio bytes", "video-a": b"video bytes"}
    image = VideoImageReferenceBinding(role="reference", asset_id="image-a",
        asset_sha256=hashlib.sha256(raw["image-a"]).hexdigest(), mime_type="image/png",
        width=1280, height=720, size_bytes=len(raw["image-a"]))
    video = VideoMediaReferenceBinding(kind="video", role="reference_video",
        asset_id="video-a", asset_sha256=hashlib.sha256(raw["video-a"]).hexdigest(),
        mime_type="video/mp4", duration_millis=17_056 if model_id == "seedance_2.5" else 2500, size_bytes=len(raw["video-a"]),
        width=1280, height=720, fps=24)
    audio = VideoMediaReferenceBinding(kind="audio", role="reference_audio",
        asset_id="audio-a", asset_sha256=hashlib.sha256(raw["audio-a"]).hexdigest(),
        mime_type="audio/wav", duration_millis=6_504, size_bytes=len(raw["audio-a"]))
    profile = JimengProfile(model_id=model_id, account_sha256="a" * 64,
        project_id="f0ed223b-090e-4ed6-b394-283f8b7dbd07",
        node_id="node_bq6wajb5xe", duration_seconds=17 if model_id == "seedance_2.5" else 5, resolution="720p",
        aspect_ratio="16:9", benefit_amount=34 if model_id == "seedance_2.5" else 8,
        benefit_type="seedance_25_720p_output", credit_upper_bound=884)
    browser, committer = FakeBrowser(), FakeCommitter()
    provider = JimengVideoProvider(profile=profile, transport=browser,
        reference_resolver=lambda binding: raw[binding.asset_id], committer=committer,
        now=lambda: NOW)
    request = _request(provider_name="jimeng", provider_kind="jimeng",
        model_id=model_id, provider_profile=profile.pointer(),
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO, prompt_text=prompt,
        image_bindings=(image,), media_bindings=(video, audio),
        output_requirement=profile.output())
    resolved = provider.resolve(request)
    video_preview = provider.preview(resolved)
    paid = PaidProviderCallPreview.create(attempt_id="attempt-jimeng-1",
        operation="video_generation", provider_kind="jimeng", model_id=model_id,
        request_fingerprint=resolved.resolved_generation_hash,
        billing_mode="remote_metered", currency="CRD",
        estimated_cost_upper_bound_microunits=884_000_000,
        destination="https://jimeng.jianying.com", method="POST",
        egress_items=provider.egress_items(resolved),
        retention_mode="provider_standard",
        provider_policy_snapshot_id="jimeng-test",
        secret_reference=SecretReference(kind="secret_store",
            reference_id="JIMENG_BROWSER_SESSION"))
    auth = PaidProviderAuthorizationDecision.create(
        attempt_id=paid.attempt_id, preview_fingerprint=paid.preview_fingerprint,
        explicit_opt_in=True, actor=ActorIdentity(actor_id="test-owner", actor_kind="human"),
        opt_in_policy_receipt_id="opt-in-jimeng", budget_policy_id="budget-jimeng",
        budget_currency="CRD", project_budget_ceiling_microunits=884_000_000,
        per_call_ceiling_microunits=884_000_000,
        egress_authorized=True, egress_policy_receipt_id="egress-jimeng",
        live_test_authorized=True, live_authorization_receipt_id="live-jimeng",
        issued_at=NOW - timedelta(minutes=1), expires_at=NOW + timedelta(minutes=10),
        max_submit_count=1)
    permit = _real_permit(build_video_paid_permit_binding(resolved, video_preview, paid, auth))
    return provider, resolved, video_preview, paid, auth, permit, browser, committer, raw


def accepted_receipt(request, paid):
    return PaidProviderSubmitReceipt.create(attempt_id=paid.attempt_id,
        request_fingerprint=request.resolved_generation_hash,
        preview_fingerprint=paid.preview_fingerprint,
        gate_receipt_fingerprint="f" * 64, reservation_id="reservation-jimeng-1",
        outcome=PaidProviderSubmitOutcome.ACCEPTED,
        external_effect_id=f"{RESOURCE_ID}:{TASK_ID}", recorded_at=NOW)


MODEL_CASES = (
    ("seedance_2.5", 30, ("480p", "720p", "1080p"), 30, 10),
    ("seedance_2.0_mini", 15, ("720p",), 9, 3),
    ("seedance_2.0_vip", 15, ("720p", "1080p", "4k"), 9, 3),
    ("seedance_2.0_fast_vip", 15, ("720p",), 9, 3),
)


@pytest.mark.parametrize("model_id,duration,resolutions,images,media", MODEL_CASES)
def test_model_family_has_independent_unqualified_contract(model_id, duration, resolutions, images, media):
    provider, *_ = setup()
    data = provider._profile.model_dump(mode="python")
    pointers = []
    for resolution in resolutions:
        provider._profile = JimengProfile.model_validate({**data, "model_id": model_id,
            "duration_seconds": duration, "resolution": resolution})
        profile = provider._profile
        cap = provider.capabilities().variants[0]
        assert cap.model_id == model_id
        assert cap.production_qualification == "UNQUALIFIED"
        assert cap.output_capability.max_duration_seconds == duration
        assert cap.output_capability.resolution_labels == resolutions
        assert cap.max_reference_count == images
        assert {x.max_count for x in cap.media_capabilities} == {media}
        assert JimengProfile.model_validate_json(profile.model_dump_json()) == profile
        pointers.append(profile.pointer().profile_sha256)
    assert len(set(pointers)) == len(resolutions)


@pytest.mark.parametrize("model_id", [row[0] for row in MODEL_CASES])
def test_unqualified_model_is_blocked_by_standard_router(model_id):
    from test_production_shot_router import _context, _policy
    from ai_video.production.shot_router import VideoGenerationResolver, RoutingOutcome, RouterReasonCode
    provider, *_, browser, _, _ = setup()
    provider._profile = JimengProfile.model_validate({**provider._profile.model_dump(),
        "model_id": model_id, "duration_seconds": 5, "benefit_amount": 5})
    result = VideoGenerationResolver().inspect_capability(context=_context(), policy=_policy(),
        provider_profile=provider._profile.pointer(), capabilities=provider.capabilities(),
        selected_capability_id=provider._profile.capability_id,
        output_requirement=provider._profile.output())
    assert result.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert result.reason_codes == (RouterReasonCode.MODEL_UNQUALIFIED,)
    assert result.selected_mode is None
    assert browser.calls == 0 and browser.uploads == []


@pytest.mark.parametrize("model_id,duration,resolutions,images,media", MODEL_CASES)
def test_model_limits_match_sanitized_native_read_only_evidence(model_id, duration, resolutions, images, media):
    from pathlib import Path
    from ai_video.production.jimeng_models import JIMENG_MODEL_SPECS
    observed = json.loads((Path(__file__).parent / "fixtures/generated_video/jimeng-native-models-20261022.json").read_text())["models"][model_id]
    spec = JIMENG_MODEL_SPECS[model_id]
    native, refs = observed["mode4"], observed["references"]
    assert max(native["duration"]["valuesMs"]) == duration * 1000
    assert tuple(native["resolutions"]) == resolutions
    assert set(spec.ratios).issubset(native["aspectRatios"])
    assert native["promptMaxCharacters"] == spec.prompt_max_characters
    assert native["materials"]["maxCount"] == spec.max_materials == refs["maxTotalCount"]
    assert refs["perType"]["2"]["maxCount"] == images
    assert refs["perType"]["3"]["maxCount"] == refs["perType"]["4"]["maxCount"] == media
    assert spec.image_bytes <= refs["perType"]["2"]["maxFileSizeBytes"]
    assert spec.video_bytes <= refs["perType"]["3"]["maxFileSizeBytes"]
    assert spec.audio_bytes == refs["perType"]["4"]["maxFileSizeBytes"]
    assert spec.min_media_millis == refs["perType"]["3"]["minDurationSeconds"] * 1000
    assert spec.max_audio_millis == refs["maxTotalAudioDurationSeconds"] * 1000
    assert spec.max_video_millis == refs["maxTotalVideoDurationSeconds"] * 1000
    assert observed["validation_status"] == "valid"
    assert observed["trimodal_validation"] == [
        {"resolution": resolution, "status": "valid"} for resolution in resolutions]
    # This observed admission is neither a paid permit nor generation evidence.
    assert observed["read_only_checks"]["state_status"] == "allowed"


@pytest.mark.parametrize("model_id", [row[0] for row in MODEL_CASES])
@pytest.mark.parametrize("fault", ["prompt", "image_geometry", "video_geometry", "audio_total", "wrong_model"])
def test_exact_model_bounds_fail_before_upload(model_id, fault):
    from ai_video.production.jimeng_models import JIMENG_MODEL_SPECS
    provider, original, *_, browser, _, _ = setup()
    spec = JIMENG_MODEL_SPECS[model_id]
    provider._profile = JimengProfile.model_validate({**provider._profile.model_dump(),
        "model_id": model_id, "duration_seconds": 5, "benefit_amount": 8})
    image = original.image_bindings[0]
    audio = next(x for x in original.media_bindings if x.kind == "audio").model_copy(update={"duration_millis": 2500})
    video = next(x for x in original.media_bindings if x.kind == "video").model_copy(update={"duration_millis": 2500})
    values = {**original.activation_scope.request.model_dump(exclude={"request_input_hash"}),
        "model_id": model_id, "provider_profile": provider._profile.pointer(),
        "output_requirement": provider._profile.output(), "image_bindings": (image,),
        "media_bindings": (video, audio)}
    if fault == "prompt":
        values["prompt_text"] = "😀" * (spec.prompt_max_characters // 2) + "{{image:0}}{{audio:1}}{{video:2}}"
    elif fault == "image_geometry":
        values["image_bindings"] = (image.model_copy(update={"width": spec.max_image_dimension + 1}),)
    elif fault == "video_geometry":
        values["media_bindings"] = (video.model_copy(update={"width": spec.min_video_dimension - 1}), audio)
    elif fault == "audio_total":
        values["media_bindings"] = (video, audio.model_copy(update={"duration_millis": spec.max_audio_millis + 1}))
    else:
        values["model_id"] = "seedance_2.0_mini" if model_id != "seedance_2.0_mini" else "seedance_2.5"
    with pytest.raises(AiVideoError) as failure:
        provider.resolve(_request(**values))
    assert failure.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED
    assert browser.calls == 0 and not browser.uploads


def test_qualification_is_sealed_and_legacy_capability_bytes_are_preserved():
    from test_production_shot_router import _variant, _capabilities
    from ai_video.production.video import VideoCapabilityVariant, VideoProviderCapabilities
    from ai_video.production._video_capability_fingerprint import capability_variant_fingerprint
    cap = _variant(VideoGenerationMode.TEXT_TO_VIDEO)
    assert "production_qualification" not in cap.model_dump()
    assert "subject_reference_capability" not in cap.model_dump()
    assert "output_recovery_strategy" not in cap.model_dump()
    assert VideoCapabilityVariant.model_validate(cap.model_dump()) == cap
    qualified = cap.model_copy(update={"production_qualification": "QUALIFIED"})
    unqualified = cap.model_copy(update={"production_qualification": "UNQUALIFIED"})
    assert len({capability_variant_fingerprint(x) for x in (cap, qualified, unqualified)}) == 3
    data = _capabilities(unqualified).model_dump(mode="json")
    data["variants"][0]["production_qualification"] = "QUALIFIED"
    with pytest.raises(ValueError):
        VideoProviderCapabilities.model_validate(data)


@pytest.mark.parametrize("model_id,resolution,seconds", [
    ("seedance_2.5", "4k", 5), ("seedance_2.0_mini", "1080p", 5),
    ("seedance_2.0_fast_vip", "1080p", 5), ("seedance_2.0_vip", "480p", 5),
    ("seedance_2.0_mini", "720p", 16), ("seedance_2.0_vip", "720p", 16),
    ("seedance_2.0_fast_vip", "720p", 16), ("seedance_2.0", "720p", 5),
])
def test_invalid_model_or_output_is_rejected_without_replacement(model_id, resolution, seconds):
    provider, *_ = setup()
    with pytest.raises(ValueError):
        JimengProfile.model_validate({**provider._profile.model_dump(),
            "model_id": model_id, "resolution": resolution, "duration_seconds": seconds})


@pytest.mark.parametrize("model_id", [row[0] for row in MODEL_CASES])
def test_worker_native_action_preserves_exact_model_and_video_billing(model_id):
    import subprocess
    from pathlib import Path
    script = """
      const {buildVideoAction,buildVideoCommerceContext,buildVideoEditorDraft}=require(process.argv[1]);
      const profile={model_id:process.argv[2],resolution:'720p',duration_seconds:5,benefit_amount:8};
      const action=buildVideoAction(profile,[{kind:'image'},{kind:'audio'},{kind:'video',duration_millis:2500}]);
      const context=buildVideoCommerceContext(action,2500);
      const draft=buildVideoEditorDraft(null,{model_name:profile.model_id,duration_ms:5000,resolution:'720p',aspect_ratio:'16:9'});
      let rejected=false;try{buildVideoAction({...profile,model_id:'seedance_2.0'},[])}catch{rejected=true}
      console.log(JSON.stringify({action,context,draft,rejected}));
    """
    worker = Path(__file__).parents[1] / "src/ai_video/production/jimeng_browser.cjs"
    result = json.loads(subprocess.run(["node", "-e", script, str(worker), model_id],
        capture_output=True, check=True, text=True).stdout)
    assert result["action"]["options"]["model"] == model_id
    assert result["action"]["options"]["benefitAmount"] == 8
    assert result["action"]["options"]["inputVideoDuration"] == 3
    assert result["context"]["inputVideoDurationMs"] == 2500
    assert result["draft"]["contentSettings"]["modelName"] == model_id
    assert result["rejected"] is True


@pytest.mark.parametrize("model_id", [row[0] for row in MODEL_CASES])
def test_multimodal_mapping_paid_permit_poll_and_fetch(model_id):
    provider, request, preview, paid, auth, permit, browser, committer, raw = setup(model_id=model_id)
    assert provider.capabilities().variants[0].production_qualification == "UNQUALIFIED"
    result = provider.submit(request, preview, paid, auth, permit)
    assert result.external_effect_id == f"{RESOURCE_ID}:{TASK_ID}"
    assert browser.params["model_name"] == model_id
    assert [kind for kind, _, _ in browser.uploads] == ["image", "audio", "video"]
    assert [x["type"] for x in browser.params["materials"]] == [2, 4, 3]
    assert browser.params["materials"][2]["role"] == 3
    assert [(x["type"], x.get("material_idx")) for x in browser.params["meta_list"]
            if x["type"] != 1] == [(2, 0), (4, 1), (3, 2)]
    assert tuple(x.asset_id for x in committer.dispatch.materials) == (
        "image-a", "audio-a", "video-a")
    assert committer.dispatch.params_sha256
    assert committer.canvas.resource_id == RESOURCE_ID
    assert committer.canvas.dispatch_hash == committer.dispatch.content_hash
    receipt = accepted_receipt(request, paid)
    submission = VideoSubmission.from_paid_submit_receipt(resolved=request, receipt=receipt)
    assert provider.get_status(submission, receipt).state is VideoTaskState.RUNNING
    browser.status = 1000
    observation = provider.get_status(submission, receipt)
    assert observation.provider_file_id == "video-123"
    sink = BytesIO()
    fetched = provider.fetch(submission, receipt, observation, sink)
    assert fetched.artifact_sha256 == hashlib.sha256(browser.video_bytes).hexdigest()
    assert sink.getvalue() == browser.video_bytes
    with pytest.raises(AiVideoError):
        provider.submit(request, preview, paid, auth, permit)
    assert browser.calls == 1


@pytest.mark.parametrize("prompt", [
    "Scene {{image:0}} voice {{audio:2}} motion {{video:1}}",
    "Scene {{image:0}} voice {{audio:1}}",
    "Scene {{image:0}} voice {{audio:1}} motion {{video:99}}",
    "Scene {{image:0}} voice {{audio:1}} motion {{video:x}}",
])
def test_reference_index_mismatch_fails_before_any_effect(prompt):
    raw = {"image-a": b"image bytes", "audio-a": b"audio bytes", "video-a": b"video bytes"}
    with pytest.raises(AiVideoError) as exc:
        setup(prompt=prompt)
    assert exc.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_response_loss_preserves_dispatch_and_refuses_repeat():
    provider, request, preview, paid, auth, permit, browser, committer, _ = setup()
    browser.fail_after_admit = True
    with pytest.raises(AiVideoError) as exc:
        provider.submit(request, preview, paid, auth, permit)
    assert exc.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert committer.dispatch.resource_id == RESOURCE_ID
    with pytest.raises(AiVideoError):
        provider.submit(request, preview, paid, auth, permit)
    assert browser.calls == 1


def test_unconfirmed_canvas_save_keeps_paid_submit_unknown():
    provider, request, preview, paid, auth, permit, browser, committer, _ = setup()
    browser.fail_canvas = True
    with pytest.raises(AiVideoError) as exc:
        provider.submit(request, preview, paid, auth, permit)
    assert exc.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert committer.dispatch.resource_id == RESOURCE_ID
    assert committer.canvas is None
    assert browser.calls == 1


def test_authorization_expiring_during_upload_blocks_native_submit():
    provider, request, preview, paid, auth, permit, browser, _, _ = setup()
    current = [NOW]
    provider._now = lambda: current[0]
    browser.on_upload = lambda: current.__setitem__(0, NOW + timedelta(minutes=11))
    with pytest.raises(AiVideoError) as exc:
        provider.submit(request, preview, paid, auth, permit)
    assert exc.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    assert browser.calls == 0


def test_authorization_expiring_at_admission_keeps_unknown_without_dispatch():
    provider, request, preview, paid, auth, permit, browser, committer, _ = setup()
    current = [NOW]
    provider._now = lambda: current[0]
    browser.on_dispatch = lambda: current.__setitem__(0, NOW + timedelta(minutes=11))
    with pytest.raises(AiVideoError) as exc:
        provider.submit(request, preview, paid, auth, permit)
    assert exc.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert browser.calls == 1
    assert committer.dispatch is None


def test_sealed_benefit_mismatch_blocks_before_upload_or_submit():
    provider, request, _, _, _, _, browser, _, _ = setup()
    provider._profile = provider._profile.model_copy(update={"benefit_amount": 35})
    original = request.activation_scope.request
    changed = _request(**{**original.model_dump(exclude={"request_input_hash"}),
                          "provider_profile": provider._profile.pointer()})
    with pytest.raises(AiVideoError) as exc:
        provider.resolve(changed)
    assert exc.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED
    assert browser.uploads == []
    assert browser.calls == 0


def test_resource_identity_or_parameters_drift_blocks_poll():
    provider, request, preview, paid, auth, permit, browser, _, _ = setup()
    provider.submit(request, preview, paid, auth, permit)
    receipt = accepted_receipt(request, paid)
    submission = VideoSubmission.from_paid_submit_receipt(resolved=request, receipt=receipt)
    browser.params = {**browser.params, "duration_ms": 18000}
    with pytest.raises(AiVideoError) as exc:
        provider.get_status(submission, receipt)
    assert exc.value.code is ErrorCode.VIDEO_PROVIDER_FAILED


def test_dispatch_materials_remain_bound_to_resolved_request():
    provider, request, preview, paid, auth, permit, _, committer, _ = setup()
    provider.submit(request, preview, paid, auth, permit)
    dispatch = committer.dispatch
    assert dispatch_matches_request(dispatch, request)
    altered = dispatch.model_copy(update={
        "materials": (dispatch.materials[0].model_copy(
            update={"asset_id": "unregistered-asset"}), *dispatch.materials[1:]),
    })
    assert not dispatch_matches_request(altered, request)


@pytest.mark.parametrize("lose_response,missing", [
    (False, None), (False, "dispatch"), (False, "canvas"),
    (False, "tampered_dispatch"), (False, "tampered_canvas"),
    (True, None), (True, "settled"), (True, "canvas"),
    (True, "tampered_canvas"),
    (True, "dispatch"), (True, "prior_receipt"), (True, "base_budget"),
    (True, "tampered_unknown_dispatch"),
    (False, "abandoned_intent"),
    (False, "standard_recover_abandoned"),
    (False, "abandoned_no_dispatch"),
    (False, "standard_recover_no_dispatch"),
    (False, "tampered_unknown_canvas"),
    (False, "failed_task"), (True, "failed_task"),
    (False, "pre_native_failure"), (False, "unknown_status"),
    (False, "missing_vid"), (True, "concurrent_recovery"),
])
@pytest.mark.parametrize("model_id", [row[0] for row in MODEL_CASES])
def test_standard_production_service_owns_paid_submit_and_reopen(tmp_path, monkeypatch, lose_response, missing, model_id):
    from production_remote_generation_factory import prepare_remote_generation
    from ai_video.production.project import load_production_project
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_generation import VideoGenerationService

    provider, request, _, _, _, _, browser, _, raw = setup()
    original = request.activation_scope.request
    profile_data = provider._profile.model_dump(mode="python")
    profile_data["benefit_amount"] = 17
    if model_id != "seedance_2.5":
        profile_data.update(model_id=model_id, duration_seconds=5,
                            benefit_amount=5, credit_upper_bound=30)
    provider._profile = JimengProfile.model_validate(profile_data)
    # Simulated eligibility ONLY for offline state/paid tests. Actual providers
    # always declare UNQUALIFIED; the independent route-denial test uses them.
    from ai_video.production.video import VideoProviderCapabilities
    declared = provider.capabilities()
    synthetic = VideoProviderCapabilities.create(provider_name="jimeng", variants=tuple(
        cap.model_copy(update={"production_qualification": "QUALIFIED"}) for cap in declared.variants))
    monkeypatch.setattr(provider, "capabilities", lambda: synthetic)
    image_only = _request(**{**original.model_dump(exclude={"request_input_hash"}),
                            "provider_profile": provider._profile.pointer(),
                            "model_id": model_id,
                            "output_requirement": provider._profile.output(),
                            "image_bindings": original.image_bindings,
                            "media_bindings": (),
                            "prompt_text": "The room reference {{image:0}}"})
    prepared = prepare_remote_generation(root=tmp_path, provider=provider,
        request=image_only, compiler_id=provider._profile.compiler_id,
        compiler_version="1", input_bytes={"image-a": raw["image-a"]},
        requirement_timing_mode="content_driven")
    resolved = prepared.resolved_request
    video_preview = provider.preview(resolved)
    paid = PaidProviderCallPreview.create(attempt_id="attempt-jimeng-1",
        operation="video_generation", provider_kind="jimeng", model_id=model_id,
        request_fingerprint=resolved.resolved_generation_hash,
        billing_mode="remote_metered", currency="CRD",
        estimated_cost_upper_bound_microunits=provider._profile.credit_upper_bound * 1_000_000,
        destination="https://jimeng.jianying.com", method="POST",
        egress_items=provider.egress_items(resolved),
        retention_mode="provider_standard", provider_policy_snapshot_id="jimeng-test",
        secret_reference=SecretReference(kind="secret_store",
            reference_id="JIMENG_BROWSER_SESSION"))
    auth = PaidProviderAuthorizationDecision.create(
        attempt_id=paid.attempt_id, preview_fingerprint=paid.preview_fingerprint,
        explicit_opt_in=True, actor=ActorIdentity(actor_id="test-owner", actor_kind="human"),
        opt_in_policy_receipt_id="opt-in-jimeng", budget_policy_id="budget-jimeng",
        budget_currency="CRD", project_budget_ceiling_microunits=provider._profile.credit_upper_bound * 1_000_000,
        per_call_ceiling_microunits=provider._profile.credit_upper_bound * 1_000_000,
        egress_authorized=True, egress_policy_receipt_id="egress-jimeng",
        live_test_authorized=True, live_authorization_receipt_id="live-jimeng",
        issued_at=NOW - timedelta(minutes=1), expires_at=NOW + timedelta(minutes=10),
        max_submit_count=1)
    committer = ProductionStateCommitter(tmp_path, paid_provider_authorizer=lambda _: auth,
                                         paid_provider_clock=lambda: NOW)
    provider._committer = committer
    browser.fail_after_admit = lose_response
    if missing == "failed_task":
        browser.status = 1001
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(attempt_id=paid.attempt_id, request=resolved,
                  execution_binding=prepared.execution_binding)
    if missing == "pre_native_failure":
        from ai_video.production.jimeng_contracts import JimengSubmitNotDispatched
        def fail(**kwargs):
            raise JimengSubmitNotDispatched()
        browser.submit_native = fail
        with pytest.raises(JimengSubmitNotDispatched):
            service.submit_once(attempt_id=paid.attempt_id, paid_preview=paid,
                                reservation_id="jimeng-reservation-1")
        loaded = load_production_project(tmp_path / "project.yaml")
        current = loaded.manifest.attempts[-1]
        receipt = committer._reopen_paid_submit(current.paid_provider_state.submit_receipt)
        assert receipt.outcome is PaidProviderSubmitOutcome.KNOWN_NO_EFFECT
        assert committer.read_jimeng_dispatch(paid.attempt_id, required=False) is None
        assert browser.calls == 0
        return
    if missing in {"abandoned_no_dispatch", "standard_recover_no_dispatch"}:
        committer.record_paid_provider_submit_intent(
            paid, reservation_id="jimeng-reservation-1")
        committer = ProductionStateCommitter(tmp_path, paid_provider_clock=lambda: NOW)
        if missing == "standard_recover_no_dispatch":
            committer.recover()
        provider._committer = committer
        service = VideoGenerationService(committer=committer, provider=provider)
        with pytest.raises(AiVideoError) as absent:
            service.recover_jimeng_unknown_once(attempt_id=paid.attempt_id)
        assert absent.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
        assert committer._read_manifest().attempts[-1].status.value == "outcome_unknown"
        assert browser.calls == 0
        return
    if missing in {"abandoned_intent", "standard_recover_abandoned",
                   "tampered_unknown_canvas"}:
        permit = committer.record_paid_provider_submit_intent(
            paid, reservation_id="jimeng-reservation-1")
        provider.submit(resolved, video_preview, paid, auth, permit)
        assert committer._read_manifest().attempts[-1].paid_provider_state.phase.value == "submit_intent"
        if missing == "tampered_unknown_canvas":
            from ai_video.production.jimeng_contracts import (
                JimengCanvasSnapshot, canvas_snapshot_path,
            )
            committer.latch_jimeng_abandoned_intent(paid.attempt_id)
            old = committer.read_jimeng_canvas_snapshot(paid.attempt_id)
            draft = json.loads(old.draft_json)
            draft["tampered"] = True
            altered = JimengCanvasSnapshot.create(**old.model_dump(
                mode="python", exclude={"content_hash", "draft_sha256", "draft_json"}),
                draft_json=json.dumps(draft))
            (tmp_path / canvas_snapshot_path(old.content_hash)).unlink()
            (tmp_path / canvas_snapshot_path(altered.content_hash)).write_text(
                altered.model_dump_json())
            with pytest.raises(AiVideoError) as tampered:
                load_production_project(tmp_path / "project.yaml")
            assert tampered.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
            assert committer._read_manifest().attempts[-1].status.value == "outcome_unknown"
            assert browser.calls == 1
            return
        committer = ProductionStateCommitter(tmp_path, paid_provider_clock=lambda: NOW)
        if missing == "standard_recover_abandoned":
            committer.recover()
            unknown = committer._read_manifest().attempts[-1].paid_provider_state
            receipt = committer._reopen_paid_submit(unknown.submit_receipt)
            assert receipt.jimeng_unknown_dispatch_hash == committer.read_jimeng_dispatch(
                paid.attempt_id).content_hash
            assert receipt.jimeng_unknown_canvas_hash == committer.read_jimeng_canvas_snapshot(
                paid.attempt_id).content_hash
        provider._committer = committer
        service = VideoGenerationService(committer=committer, provider=provider)
        submission = service.recover_jimeng_unknown_once(attempt_id=paid.attempt_id)
    elif lose_response:
        with pytest.raises(AiVideoError) as exc:
            service.submit_once(attempt_id=paid.attempt_id, paid_preview=paid,
                                reservation_id="jimeng-reservation-1")
        assert exc.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
        assert committer._read_manifest().attempts[-1].status.value == "outcome_unknown"
        committer = ProductionStateCommitter(tmp_path, paid_provider_clock=lambda: NOW)
        provider._committer = committer
        service = VideoGenerationService(committer=committer, provider=provider)
        browser.fail_read = True
        with pytest.raises(AiVideoError) as read_exc:
            service.recover_jimeng_unknown_once(attempt_id=paid.attempt_id)
        assert read_exc.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
        assert committer._read_manifest().attempts[-1].status.value == "outcome_unknown"
        browser.fail_read = False
        if missing == "tampered_unknown_dispatch":
            from ai_video.production.jimeng_contracts import JimengDispatchIntent, dispatch_path
            old = committer.read_jimeng_dispatch(paid.attempt_id)
            altered = JimengDispatchIntent.create(**old.model_dump(
                mode="python", exclude={"content_hash", "materials"}),
                materials=(old.materials[0].model_copy(
                    update={"asset_id": "unregistered-asset"}), *old.materials[1:]))
            (tmp_path / dispatch_path(old.content_hash)).unlink()
            (tmp_path / dispatch_path(altered.content_hash)).write_text(altered.model_dump_json())
            with pytest.raises(AiVideoError) as tampered:
                service.recover_jimeng_unknown_once(attempt_id=paid.attempt_id)
            assert tampered.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
            assert committer._read_manifest().attempts[-1].status.value == "outcome_unknown"
            assert browser.calls == 1
            return
        if missing == "concurrent_recovery":
            from concurrent.futures import ThreadPoolExecutor
            from threading import Barrier
            barrier = Barrier(2)
            read = browser.read_resource
            def concurrent_read(**kwargs):
                resource = read(**kwargs)
                barrier.wait(timeout=5)
                return resource
            browser.read_resource = concurrent_read
            def recover():
                try:
                    return service.recover_jimeng_unknown_once(attempt_id=paid.attempt_id)
                except AiVideoError as error:
                    return error
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: recover(), range(2)))
            assert sum(isinstance(result, VideoSubmission) for result in results) == 1
            browser.read_resource = read
            before = load_production_project(tmp_path / "project.yaml").manifest
            with pytest.raises(AiVideoError):
                service.recover_jimeng_unknown_once(attempt_id=paid.attempt_id)
            assert load_production_project(tmp_path / "project.yaml").manifest == before
            assert browser.calls == 1
            return
        submission = service.recover_jimeng_unknown_once(attempt_id=paid.attempt_id)
    else:
        submission = service.submit_once(attempt_id=paid.attempt_id, paid_preview=paid,
                                         reservation_id="jimeng-reservation-1")
    assert submission.resolved_generation_hash == resolved.resolved_generation_hash
    assert browser.calls == 1
    assert committer.read_jimeng_dispatch(paid.attempt_id).resource_id == RESOURCE_ID
    canvas = committer.read_jimeng_canvas_snapshot(paid.attempt_id)
    assert canvas.resource_id == RESOURCE_ID
    assert json.loads(canvas.draft_json)["nodes"][0]["data"]["resourceId"] == RESOURCE_ID
    loaded = load_production_project(tmp_path / "project.yaml")
    assert loaded.manifest.attempts[-1].paid_provider_state.phase.value == "accepted"
    if missing in {"unknown_status", "missing_vid"}:
        browser.status = 98765 if missing == "unknown_status" else 1000
        read = browser.read_resource
        if missing == "missing_vid":
            def without_vid(**kwargs):
                resource = read(**kwargs)
                resource["video"]["vid"] = None
                return resource
            browser.read_resource = without_vid
        before = loaded.manifest
        with pytest.raises(AiVideoError):
            service.refresh_once(attempt_id=paid.attempt_id)
        assert load_production_project(tmp_path / "project.yaml").manifest == before
        assert browser.calls == 1
        return
    observation = service.refresh_once(attempt_id=paid.attempt_id)
    assert observation.state is (VideoTaskState.FAILED if missing == "failed_task" else VideoTaskState.RUNNING)
    if missing == "failed_task":
        closed = load_production_project(tmp_path / "project.yaml")
        assert closed.manifest.attempts[-1].status.value == "failed"
        assert closed.manifest.attempts[-1].paid_provider_state.phase.value == "accepted"
        assert observation.provider_file_id is None
        with pytest.raises(AiVideoError):
            service.fetch_once(attempt_id=paid.attempt_id)
        assert browser.calls == 1
    if missing == "settled":
        committer.settle_paid_provider_reservation(
            attempt_id=paid.attempt_id,
            actual_cost_microunits=min(442_000_000, provider._profile.credit_upper_bound * 1_000_000))
        settled = load_production_project(tmp_path / "project.yaml")
        assert settled.manifest.attempts[-1].paid_provider_state.phase.value == "settled"
    if missing in {"tampered_dispatch", "tampered_canvas"}:
        from ai_video.production.jimeng_contracts import (
            JimengCanvasSnapshot, JimengDispatchIntent, canvas_snapshot_path,
            dispatch_path,
        )
        old_canvas = committer.read_jimeng_canvas_snapshot(paid.attempt_id)
        if missing == "tampered_dispatch":
            old_dispatch = committer.read_jimeng_dispatch(paid.attempt_id)
            altered_materials = (old_dispatch.materials[0].model_copy(
                update={"asset_id": "unregistered-asset"}), *old_dispatch.materials[1:])
            changed_dispatch = JimengDispatchIntent.create(**old_dispatch.model_dump(
                mode="python", exclude={"content_hash", "materials"}),
                materials=altered_materials)
            (tmp_path / dispatch_path(old_dispatch.content_hash)).unlink()
            (tmp_path / dispatch_path(changed_dispatch.content_hash)).write_text(
                changed_dispatch.model_dump_json())
            changed_canvas = JimengCanvasSnapshot.create(**old_canvas.model_dump(
                mode="python", exclude={"content_hash", "draft_sha256", "dispatch_hash"}),
                dispatch_hash=changed_dispatch.content_hash)
        else:
            draft = json.loads(old_canvas.draft_json)
            draft["tampered"] = True
            changed_canvas = JimengCanvasSnapshot.create(**old_canvas.model_dump(
                mode="python", exclude={"content_hash", "draft_sha256", "draft_json"}),
                draft_json=json.dumps(draft))
        (tmp_path / canvas_snapshot_path(old_canvas.content_hash)).unlink()
        (tmp_path / canvas_snapshot_path(changed_canvas.content_hash)).write_text(
            changed_canvas.model_dump_json())
        with pytest.raises(AiVideoError) as reopen_error:
            load_production_project(tmp_path / "project.yaml")
        assert reopen_error.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    if missing in {"dispatch", "canvas", "prior_receipt", "base_budget"}:
        from ai_video.production.jimeng_contracts import canvas_snapshot_path, dispatch_path
        from ai_video.production.paths import (
            canonical_paid_provider_budget_path, canonical_paid_provider_submit_path,
        )
        current = committer._paid_attempt(committer._read_manifest(), paid.attempt_id)
        accepted = committer._reopen_paid_submit(current.paid_provider_state.submit_receipt)
        proof = accepted.jimeng_accepted_effect
        relative = (dispatch_path(committer.read_jimeng_dispatch(paid.attempt_id).content_hash)
                    if missing == "dispatch"
                    else canvas_snapshot_path(committer.read_jimeng_canvas_snapshot(
                        paid.attempt_id).content_hash) if missing == "canvas"
                    else canonical_paid_provider_submit_path(
                        proof.prior_unknown_receipt_fingerprint) if missing == "prior_receipt"
                    else canonical_paid_provider_budget_path(proof.base_budget_hash))
        (tmp_path / relative).unlink()
        with pytest.raises(AiVideoError) as reopen_error:
            load_production_project(tmp_path / "project.yaml")
        assert reopen_error.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_mini_profile_has_distinct_identity_and_rejects_unsupported_specs():
    from pydantic import ValidationError
    from ai_video.production.hashing import canonical_sha256

    provider, *_ = setup()
    old = provider._profile
    legacy_data = old.model_dump(mode="json")
    assert "model_id" not in legacy_data
    assert old.pointer().profile_sha256 == canonical_sha256(legacy_data)
    data = {**legacy_data, "model_id": "seedance_2.0_mini",
            "duration_seconds": 5, "benefit_amount": 5, "credit_upper_bound": 30}
    mini = JimengProfile.model_validate(data)
    assert mini.pointer() != old.pointer()
    assert JimengProfile.model_validate_json(mini.model_dump_json()) == mini
    assert mini.model_id == "seedance_2.0_mini"
    for update in ({"duration_seconds": 16}, {"resolution": "480p"}):
        with pytest.raises(ValidationError):
            JimengProfile.model_validate({**data, **update})


def test_native_action_uses_base_shape_without_video_and_exact_mini_model():
    import subprocess
    from pathlib import Path

    worker = Path(__file__).parents[1] / "src/ai_video/production/jimeng_browser.cjs"
    result = subprocess.run(["node", "-e", """
        const {buildVideoAction,buildVideoCommerceContext}=require(process.argv[1]);
        const profile={model_id:'seedance_2.0_mini',resolution:'720p',
            duration_seconds:5,benefit_amount:5};
        const image=buildVideoAction(profile,[{kind:'image'}]);
        const mixed=buildVideoAction({...profile,benefit_amount:8},
            [{kind:'image'},{kind:'video',duration_millis:3000}]);
        console.log(JSON.stringify({image,mixed,
            imageContext:buildVideoCommerceContext(image,0),
            mixedContext:buildVideoCommerceContext(mixed,3000)}));
    """, str(worker)], capture_output=True, text=True, check=True)
    actions = json.loads(result.stdout)
    assert actions["image"]["options"]["model"] == "seedance_2.0_mini"
    assert set(actions["image"]["options"]) == {
        "model", "resolution", "durationSeconds", "outputCount", "videoMode",
        "hasInputVideo", "isLongVideo", "materialTypes"}
    assert actions["mixed"]["options"]["chargeInputVideoDuration"] is True
    assert actions["mixed"]["options"]["benefitAmount"] == 8
    assert actions["imageContext"] == {"hasInputVideo": False}
    assert actions["mixedContext"] == {"hasInputVideo": True, "inputVideoDurationMs": 3000}


@pytest.mark.parametrize("exit_code", [0, 7])
def test_browser_submit_protocol_closes_stdin_after_ack(tmp_path, monkeypatch, exit_code):
    """An acknowledged Node worker must get EOF before the host waits for exit."""
    import subprocess
    import sys
    from ai_video.production.jimeng_browser import JimengBrowserTransport

    provider, *_ = setup()
    transport = JimengBrowserTransport(profile_dir=tmp_path, timeout_seconds=2)
    script = f'''
import json, sys
json.loads(sys.stdin.readline())
print(json.dumps({{"event":"dispatch","submit_id":"{SUBMIT_ID}","resource_id":"{RESOURCE_ID}"}}),flush=True)
assert json.loads(sys.stdin.readline())["approved"] is True
print(json.dumps({{"ok":True,"submit_id":"{SUBMIT_ID}","resource_id":"{RESOURCE_ID}","task_id":"{TASK_ID}"}}),flush=True)
sys.stdin.read()
sys.exit({exit_code})
'''
    monkeypatch.setattr(transport, "_process", lambda: subprocess.Popen(
        [sys.executable, "-u", "-c", script], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1))
    admitted = []
    def submit():
        return transport.submit_native(profile=provider._profile, video_params={}, materials=(),
            admit=lambda submit_id, resource_id: admitted.append((submit_id, resource_id)))
    if exit_code:
        with pytest.raises(AiVideoError) as error:
            submit()
        assert error.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    else:
        assert submit()["task_id"] == TASK_ID
    assert admitted == [(SUBMIT_ID, RESOURCE_ID)]


def test_native_editor_selection_matches_request_without_reordering_draft_inputs():
    import subprocess
    from pathlib import Path

    worker = Path(__file__).parents[1] / "src/ai_video/production/jimeng_browser.cjs"
    result = subprocess.run(["node", "-e", """
        const assert=require('node:assert/strict');
        const {buildVideoEditorDraft}=require(process.argv[1]);
        const previous={kind:'video',parts:[{type:'text',text:'existing input'}],
          references:[{id:'image-b'},{id:'image-a'}],outputCount:1,
          contentSettings:{modelName:'seedance_2.0_vip',durationSeconds:4,
            mode:'multiModal',aspectRatio:'1:1',resolution:'720p',isLongVideo:false}};
        const frozen=JSON.stringify(previous);
        const params={model_name:'seedance_2.0_mini',duration_ms:5000,
          aspect_ratio:'16:9',resolution:'720p'};
        const next=buildVideoEditorDraft(previous,params);
        assert.equal(JSON.stringify(previous),frozen);
        assert.deepEqual(next.parts,previous.parts);
        assert.deepEqual(next.references,previous.references);
        assert.deepEqual(next.contentSettings,{modelName:'seedance_2.0_mini',
          durationSeconds:5,mode:'multiModal',aspectRatio:'16:9',resolution:'720p',isLongVideo:false});
        assert.equal(buildVideoEditorDraft(null,params).kind,'video');
        assert.throws(()=>buildVideoEditorDraft({kind:'image'},params));
    """, str(worker)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("scenario", ["timeout_late_send", "timeout_late_fetch", "timeout_late_replaced_http", "identity_drift", "ambiguous_page", "concurrent",
    "success", "native_no_quote", "duplicate_post", "host_reject", "after_approval_identity_drift",
    "quote_change", "mutated_request", "preflight_cleanup", "quote_precondition_changed", "duplicate_wire", "replaced_http", "binding_unavailable"])
def test_shipped_worker_fault_boundaries(scenario):
    import subprocess
    from pathlib import Path

    root = Path(__file__).parents[1]
    result = subprocess.run(["node", str(root / "tests/fixtures/generated_video/jimeng_worker_faults.cjs"),
        str(root / "src/ai_video/production/jimeng_browser.cjs"), scenario],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("scenario", ["mutated_request", "quote_precondition_changed",
    "host_reject", "response_lost", "guard_rejection_pending", "unknown_native_error",
    "replaced_http", "guard_rejection_owner_changed", "guard_rejection_instance_changed",
    "guard_rejection_account_changed"])
def test_worker_terminal_protocol_requires_positive_pre_dispatch_proof(scenario):
    import subprocess
    from pathlib import Path

    root = Path(__file__).parents[1]
    result = subprocess.run(["node", str(root / "tests/fixtures/generated_video/jimeng_worker_faults.cjs"),
        str(root / "src/ai_video/production/jimeng_browser.cjs"), "protocol_" + scenario],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_native_quote_binding_preserves_params_and_rejects_supplied_drift():
    import subprocess
    from pathlib import Path

    worker = Path(__file__).parents[1] / "src/ai_video/production/jimeng_browser.cjs"
    result = subprocess.run(["node", "-e", """
        const assert=require('node:assert/strict');
        const bind=require(process.argv[1]).createVideoQuoteBinder();
        const profile={benefit_type:'selected',benefit_amount:12,credit_upper_bound:500};
        const params=Object.freeze({mode:4,materials:[{type:2,image_uri:'exact-image'}]});
        const selection=Object.freeze({benefit_type:'selected'});
        const row=Object.freeze({type:2,params:{video_params:params},commerce_selection:selection});
        const body=Object.freeze({initial:Object.freeze({items:Object.freeze([row])})});
        const sealed=bind(body,profile,240);
        assert.equal(sealed.initial.items[0].params.video_params,params);
        assert.equal(selection.quote_precondition,undefined);
        assert.deepEqual(sealed.initial.items[0].commerce_selection.quote_precondition,
          {expected_benefit_amount:12,expected_credits_amount:240});
        assert.deepEqual(bind(sealed,profile,240),sealed);
        for(const supplied of [null,{}, {expected_benefit_amount:12,expected_credits_amount:241},
            {expected_benefit_amount:13,expected_credits_amount:240},
            {expected_benefit_amount:12,expected_credits_amount:240,extra:1}]) {
          assert.throws(()=>bind({initial:{items:[{...row,commerce_selection:{
            ...selection,quote_precondition:supplied}}]}},profile,240));
        }
        for(const credits of [0,501,240.5,NaN]) assert.throws(()=>bind(body,profile,credits));
    """, str(worker)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('frame', ['partial', 'no_effect', 'abrupt', 'duplicate', 'response_lost'])
def test_browser_protocol_faults_preserve_outcome_and_bound_deadline(tmp_path, monkeypatch, frame):
    import subprocess
    import sys
    import time
    from ai_video.production.jimeng_browser import JimengBrowserTransport
    from ai_video.production.jimeng_contracts import JimengSubmitNotDispatched

    provider, *_ = setup()
    transport = JimengBrowserTransport(profile_dir=tmp_path, timeout_seconds=0.25)
    dispatch = json.dumps({'event': 'dispatch', 'submit_id': SUBMIT_ID, 'resource_id': RESOURCE_ID})
    script = 'import json,sys,time\njson.loads(sys.stdin.readline())\n'
    if frame == 'partial':
        script += "sys.stdout.write('{');sys.stdout.flush();time.sleep(5)\n"
    elif frame == 'no_effect':
        script += "print(json.dumps({'ok':False,'no_effect':True}),flush=True)\nsys.stdin.read()\nsys.exit(1)\n"
    elif frame == 'abrupt':
        script += 'sys.exit(7)\n'
    else:
        script += f'print({dispatch!r},flush=True)\nassert json.loads(sys.stdin.readline())["approved"]\n'
        script += f'print({dispatch!r},flush=True)\n' if frame == 'duplicate' else 'time.sleep(5)\n'
    children = []
    def process():
        child = subprocess.Popen([sys.executable, '-u', '-c', script], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        children.append(child)
        return child
    monkeypatch.setattr(transport, '_process', process)
    admitted = []
    started = time.monotonic()
    with pytest.raises(AiVideoError) as error:
        transport.submit_native(profile=provider._profile, video_params={}, materials=(),
            admit=lambda *ids: admitted.append(ids))
    assert time.monotonic() - started < 2
    assert children[0].poll() is not None
    if frame == 'no_effect':
        assert isinstance(error.value, JimengSubmitNotDispatched)
        assert not admitted
    else:
        assert error.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert len(admitted) == (1 if frame in {'duplicate', 'response_lost'} else 0)


@pytest.mark.parametrize('after_dispatch', [False, True])
def test_only_proven_pre_native_failure_is_known_no_effect(after_dispatch):
    from ai_video.production.jimeng_contracts import JimengSubmitNotDispatched
    provider, request, preview, paid, auth, permit, browser, committer, _ = setup()
    def fail(**kwargs):
        if after_dispatch:
            kwargs['admit'](SUBMIT_ID, RESOURCE_ID)
        raise JimengSubmitNotDispatched()
    browser.submit_native = fail
    with pytest.raises(AiVideoError) as error:
        provider.submit(request, preview, paid, auth, permit)
    assert error.value.code is (ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
        if after_dispatch else ErrorCode.VIDEO_PROVIDER_FAILED)
    assert (committer.dispatch is not None) == after_dispatch


def test_actual_worker_preflight_failure_exits_and_is_not_dispatched(tmp_path):
    from ai_video.production.jimeng_browser import JimengBrowserTransport
    from ai_video.production.jimeng_contracts import JimengSubmitNotDispatched
    provider, *_ = setup()
    transport = JimengBrowserTransport(profile_dir=tmp_path,
        playwright_module=str(tmp_path / 'missing-playwright'), timeout_seconds=2)
    with pytest.raises(JimengSubmitNotDispatched):
        transport.submit_native(profile=provider._profile, video_params={}, materials=(),
            admit=lambda *_: pytest.fail('preflight must not dispatch'))


def test_browser_executable_failure_uses_typed_sanitized_errors(tmp_path):
    from ai_video.production.jimeng_browser import JimengBrowserTransport
    from ai_video.production.jimeng_contracts import JimengSubmitNotDispatched
    provider, *_ = setup()
    transport = JimengBrowserTransport(profile_dir=tmp_path, node_binary=str(tmp_path / 'missing-node'))
    with pytest.raises(JimengSubmitNotDispatched):
        transport.submit_native(profile=provider._profile, video_params={}, materials=(), admit=lambda *_: None)
    with pytest.raises(AiVideoError) as error:
        transport.read_resource(profile=provider._profile, resource_id=RESOURCE_ID)
    assert error.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    assert str(tmp_path) not in str(error.value)


@pytest.mark.parametrize('phase', ['admission', 'after_approval', 'single'])
@pytest.mark.parametrize('cancel', [KeyboardInterrupt, SystemExit])
def test_cancellation_reaps_worker_and_preserves_exception(tmp_path, monkeypatch, phase, cancel):
    import subprocess
    import sys
    from ai_video.production import jimeng_browser as module
    provider, *_ = setup()
    transport = module.JimengBrowserTransport(profile_dir=tmp_path, timeout_seconds=2)
    dispatch = json.dumps({'event': 'dispatch', 'submit_id': SUBMIT_ID, 'resource_id': RESOURCE_ID})
    marker = tmp_path / 'simulated-post-after-cancel'
    script = ('import sys,time,json\nfrom pathlib import Path\njson.loads(sys.stdin.readline())\n'
        f'print({dispatch!r},flush=True)\njson.loads(sys.stdin.readline())\ntime.sleep(0.2)\n'
        f'Path({str(marker)!r}).touch()\ntime.sleep(5)\n')
    child = subprocess.Popen([sys.executable, '-u', '-c', script], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
    monkeypatch.setattr(transport, '_process', lambda: child)
    def interrupt(*args, **kwargs):
        raise cancel('cancelled')
    def admit(*_):
        if phase == 'admission':
            interrupt()
    selector_factory = module.selectors.DefaultSelector
    if phase == 'after_approval':
        selector = selector_factory()
        select = selector.select
        count = 0
        def select_once(timeout):
            nonlocal count
            count += 1
            return select(timeout) if count == 1 else interrupt()
        monkeypatch.setattr(selector, 'select', select_once)
        monkeypatch.setattr(module.selectors, 'DefaultSelector', lambda: selector)
    if phase == 'single':
        monkeypatch.setattr(child, 'communicate', interrupt)
    with pytest.raises(cancel, match='cancelled'):
        if phase == 'single':
            transport.read_resource(profile=provider._profile, resource_id=RESOURCE_ID)
        else:
            transport.submit_native(profile=provider._profile, video_params={}, materials=(), admit=admit)
    assert child.poll() is not None
    assert child.stdin.closed and child.stdout.closed
    assert not marker.exists()


# Frame conditioning regression coverage.
from pathlib import Path
import subprocess

def _frame_conditioned(mode, *, model_id="seedance_2.0_vip"):
    legacy = setup(model_id=model_id)[0]._profile
    profile = JimengProfile.model_validate({**legacy.model_dump(mode="json"),
        "input_mode": mode, "benefit_amount": legacy.duration_seconds})
    roles = ("first_frame", "last_frame") if mode == "first_last_frame" else ("first_frame",)
    raw = {role: role.encode() for role in roles}
    images = tuple(VideoImageReferenceBinding(role=role, asset_id=role,
        asset_sha256=hashlib.sha256(raw[role]).hexdigest(), size_bytes=len(raw[role]),
        mime_type="image/png", width=720, height=1280) for role in roles)
    browser = FakeBrowser()
    provider = JimengVideoProvider(profile=profile, transport=browser,
        reference_resolver=lambda binding: raw[binding.asset_id], committer=FakeCommitter(),
        now=lambda: NOW)
    request = _request(provider_name="jimeng", provider_kind="jimeng",
        model_id=profile.model_id, provider_profile=profile.pointer(),
        mode=VideoGenerationMode.IMAGE_TO_VIDEO, image_bindings=images,
        media_bindings=(), prompt_text="从真实首帧继续伸手拿起瓶子，最后到达指定尾帧。",
        output_requirement=profile.output())
    return profile, provider, request


@pytest.mark.parametrize("mode,count,native", [("first_frame", 1, 2), ("first_last_frame", 2, 3)])
def test_frame_mode_has_exact_profile_and_capability(mode, count, native):
    profile, provider, request = _frame_conditioned(mode)
    capability = provider.capabilities().variants[0]
    assert profile.native_mode == native
    assert capability.mode is VideoGenerationMode.IMAGE_TO_VIDEO
    assert capability.required_first_frame
    bounds = {c.roles: (c.min_count, c.max_count) for c in capability.binding_cardinality_constraints}
    assert bounds[("first_frame",)] == (1, 1)
    assert bounds[("last_frame",)] == ((1, 1) if count == 2 else (0, 0))
    assert capability.allowed_image_roles == (("first_frame", "last_frame") if count == 2 else ("first_frame",))
    assert provider.resolve(request).image_bindings == request.image_bindings


def test_existing_reference_profile_bytes_and_identity_unchanged():
    profile = setup()[0]._profile
    payload = profile.model_dump(mode="json")
    assert "input_mode" not in payload
    assert "model_id" not in payload
    assert profile.capability_id == "jimeng-seedance-2.5-multimodal-v1"
    assert profile.pointer() == JimengProfile.model_validate(payload).pointer()


def test_frame_profile_rejects_reference_only_request_without_fallback():
    _, provider, request = _frame_conditioned("first_frame")
    reference = request.image_bindings[0].model_copy(update={"role": "reference"})
    with pytest.raises(AiVideoError):
        provider.resolve(_request(provider_name="jimeng", provider_kind="jimeng",
            model_id=provider._profile.model_id, provider_profile=provider._profile.pointer(),
            mode=VideoGenerationMode.REFERENCE_TO_VIDEO, image_bindings=(reference,),
            media_bindings=(), output_requirement=provider._profile.output()))


def test_last_frame_profile_cannot_silently_drop_endpoint():
    _, provider, request = _frame_conditioned("first_last_frame")
    with pytest.raises(AiVideoError):
        provider.resolve(_request(provider_name="jimeng", provider_kind="jimeng",
            model_id=provider._profile.model_id, provider_profile=provider._profile.pointer(),
            mode=VideoGenerationMode.IMAGE_TO_VIDEO, image_bindings=request.image_bindings[:1],
            media_bindings=(), output_requirement=provider._profile.output()))


@pytest.mark.parametrize("mode,native,roles,commerce", [
    ("first_frame", 2, ["first_frame"], "i2v"),
    ("first_last_frame", 3, ["first_frame", "last_frame"], "first_last_frame"),
])
def test_browser_frame_mode_commercial_action_and_editor_agree(mode, native, roles, commerce):
    worker = Path(__file__).resolve().parents[1] / "src/ai_video/production/jimeng_browser.cjs"
    code = """
      const {buildVideoAction,buildVideoEditorDraft}=require(process.argv[1]);
      const data=JSON.parse(process.argv[2]);
      const action=buildVideoAction({model_id:'seedance_2.0_vip',input_mode:data.mode,
        duration_seconds:8,benefit_amount:8,resolution:'720p'},
        data.roles.map(image_role=>({kind:'image',image_role})));
      const draft=buildVideoEditorDraft(null,{mode:data.native,model_name:'seedance_2.0_vip',
        aspect_ratio:'9:16',resolution:'720p',duration_ms:8000});
      console.log(JSON.stringify({action,draft}));
    """
    result = json.loads(subprocess.check_output(["node", "-e", code, str(worker),
        json.dumps(dict(mode=mode, native=native, roles=roles))], text=True))
    assert result["action"]["options"]["videoMode"] == commerce
    assert result["draft"]["contentSettings"]["mode"] == "firstLastFrame"


@pytest.mark.parametrize("mode,native", [("first_frame", 2), ("first_last_frame", 3)])
def test_paid_dispatch_retains_native_frame_roles_without_prompt_markers(mode, native):
    from ai_video.production.paid_provider import PaidProviderCallPreview, PaidProviderAuthorizationDecision
    from ai_video.production.video import build_video_paid_permit_binding
    from ai_video.production.jimeng_contracts import dispatch_matches_request
    profile, provider, request = _frame_conditioned(mode)
    resolved = provider.resolve(request)
    video_preview = provider.preview(resolved)
    legacy = setup(model_id="seedance_2.0_vip")
    values = legacy[3].model_dump(mode="python", exclude={"preview_fingerprint"})
    values.update(request_fingerprint=resolved.resolved_generation_hash,
        egress_items=provider.egress_items(resolved))
    paid = PaidProviderCallPreview.create(**values)
    values = legacy[4].model_dump(mode="python", exclude={"authorization_fingerprint"})
    values["preview_fingerprint"] = paid.preview_fingerprint
    auth = PaidProviderAuthorizationDecision.create(**values)
    permit = _real_permit(build_video_paid_permit_binding(resolved, video_preview, paid, auth))
    provider.submit(resolved, video_preview, paid, auth, permit)
    assert provider._transport.params["mode"] == native
    assert [item["role"] for item in provider._transport.params["materials"]] == list(range(1, len(request.image_bindings) + 1))
    assert "meta_list" not in provider._transport.params
    assert [m.image_role for m in provider._transport.materials] == [b.role for b in request.image_bindings]
    assert dispatch_matches_request(provider._committer.dispatch, resolved)


@pytest.mark.parametrize("mode", ["first_frame", "first_last_frame"])
@pytest.mark.parametrize("model_id,untimed", [("seedance_2.0_vip", False), ("seedance_2.0_vip", True), ("seedance_2.5", True)])
def test_frame_conditioning_survives_requirement_router_compiler_and_resolve(mode, monkeypatch, model_id, untimed):
    from test_production_shot_router import (
        _asset, _context, _first_frame_projection, _reseal_projection, _policy, _lifecycle,
    )
    from test_production_video_intent_validation import _complete_intent, _compatible_fl2va
    from ai_video.production.shot_router import VideoGenerationResolver, AdapterCompilerContract
    from ai_video.production._video_intent_validation import ConditioningLane
    from ai_video.production.video_requirement import (
        AssetEvidence, SemanticReferenceRole, CapabilityNeed, AudioNeed, OutputNeed, DialogueIntent,
    )
    profile, provider, expected = _frame_conditioned(mode, model_id=model_id)
    assets = tuple(_asset(binding.role, binding.asset_id, binding.asset_sha256,
        width=binding.width, height=binding.height, size_bytes=binding.size_bytes)
        for binding in expected.image_bindings)
    context = _context(keyframe=assets[0], last_frame=assets[-1] if len(assets) == 2 else None)
    intent = _complete_intent()
    if untimed:
        intent = intent.model_copy(update={"dialogue_intent": DialogueIntent.model_validate({
            "mode": "conversation", "language": "zh", "turns": [
                {"speaker_id": "hero", "verbatim_text": "有人吗？", "on_screen": True,
                 "lip_sync_required": True, "response_obligation": "等待画外人回答。"},
                {"speaker_id": "clerk", "verbatim_text": "慢点，里面烫。", "on_screen": False,
                 "lip_sync_required": False, "response_obligation": "主角听完再收手。"},
            ]})})
    projection = _reseal_projection(_first_frame_projection(context),
        contract_version="provider-neutral-video-requirement/4",
        generation_mode="first_last_frame_video" if len(assets) == 2 else "image_to_video",
        conditioning_compatibility=_compatible_fl2va().model_copy(update={
            "lane": ConditioningLane.FL2VA if len(assets) == 2 else ConditioningLane.I2VA,
            "first_anchor_id": assets[0].asset_id,
            "last_anchor_id": assets[-1].asset_id if len(assets) == 2 else None,
            "available_duration_seconds": profile.duration_seconds}),
        generation_intent=intent.model_copy(update={"pacing":
            _complete_intent().pacing.model_copy(update={"shot_duration_seconds": profile.duration_seconds})}),
        audio_need=AudioNeed.REQUIRED,
        output_need=OutputNeed(timing_mode="content_driven", duration_seconds=profile.duration_seconds,
            geometry_policy="adaptive", aspect_ratio=profile.aspect_ratio, container_mime="video/mp4"),
        semantic_reference_roles=tuple(SemanticReferenceRole(a.role) for a in assets),
        asset_evidence=tuple(AssetEvidence(role=SemanticReferenceRole(a.role),
            asset_id=a.asset_id, asset_sha256=a.asset_sha256, mime_type=a.mime_type,
            width=a.width, height=a.height, size_bytes=a.size_bytes) for a in assets),
        capability_need=CapabilityNeed(needs_first_frame=True, needs_last_frame=len(assets) == 2))
    policy = _policy(remote_authorized=True, budget_authorized=True)
    # Qualification is deliberately unchanged. Only this offline fixture is
    # qualified, matching the existing lifecycle fixtures above.
    from ai_video.production.video import VideoProviderCapabilities
    declared = provider.capabilities()
    assert declared.variants[0].production_qualification == "UNQUALIFIED"
    qualified = VideoProviderCapabilities.create(provider_name=declared.provider_name,
        variants=tuple(v.model_copy(update={"production_qualification": "QUALIFIED"})
                       for v in declared.variants))
    monkeypatch.setattr(provider, "capabilities", lambda: qualified)
    result = VideoGenerationResolver()._bind_requirement(projection=projection,
        context=context, policy=policy, provider_profile=profile.pointer(),
        capabilities=provider.capabilities(), selected_capability_id=profile.capability_id,
        output_requirement=profile.output(), lifecycle=_lifecycle(context).model_copy(update={
            "input_artifact_ids": (context.target_shot_id, *(a.asset_id for a in assets))}),
        compiler_contract=AdapterCompilerContract.create(compiler_id=profile.compiler_id, compiler_version="1"))
    assert result.provider_bound_request is not None, json.dumps(result.decision.model_dump(mode="json"))
    compiled = provider.compile_request(result.provider_bound_request, projection.requirement)
    assert compiled.outcome == "compiled", compiled
    resolved = provider.resolve(compiled.request)
    assert [(b.role, b.asset_id, b.asset_sha256) for b in resolved.image_bindings] == [
        (a.role, a.asset_id, a.asset_sha256) for a in assets]
    assert resolved.mode is VideoGenerationMode.IMAGE_TO_VIDEO
    assert "{{image:" not in resolved.prompt_text
    if untimed:
        assert resolved.prompt_text.index("有人吗？") < resolved.prompt_text.index("慢点，里面烫。")
        assert "Dialogue timing:" not in resolved.prompt_text
        from ai_video.production.jimeng_prompt import compile_jimeng_native_prompt
        native = compile_jimeng_native_prompt(compiler_id=profile.compiler_id, compiler_version="1",
            requirement=projection.requirement, provider_bound=result.provider_bound_request)
        assert "generation_intent.dialogue_intent.turns" in native.expressed_control_paths
        # A caller cannot fall back to the neutral grammar and lose the turns.
        from ai_video.production.video_compiler import compile_provider_video_request
        neutral = compile_provider_video_request(provider_bound=result.provider_bound_request,
            requirement=projection.requirement, compiler_id=profile.compiler_id,
            compiler_version="1", capabilities=provider.capabilities())
        assert neutral.outcome == "unsupported"
        assert "generation_intent.dialogue_intent.mode" in neutral.unsupported_field_paths
        for corrupted in (
            native.prompt_text.replace("慢点，里面烫。", "慢点。"),
            native.prompt_text.replace("（clerk）", "（hero）"),
            native.prompt_text.replace("有人吗？", "__temporary_turn__")
                .replace("慢点，里面烫。", "有人吗？")
                .replace("__temporary_turn__", "慢点，里面烫。"),
        ):
            assert corrupted != native.prompt_text
            resealed = native.model_copy(update={"prompt_text": corrupted,
                "prompt_sha256": hashlib.sha256(corrupted.encode()).hexdigest()})
            rejected = compile_provider_video_request(provider_bound=result.provider_bound_request,
                requirement=projection.requirement, compiler_id=profile.compiler_id,
                compiler_version="1", capabilities=provider.capabilities(), native_prompt=resealed)
            assert rejected.outcome == "unsupported"
            assert "generation_intent.dialogue_intent.turns" in rejected.unsupported_field_paths


@pytest.mark.parametrize('host,allowed', [
    ('tos-lq-x.bytedancevod.com', True),
    ('tos-d-x-hl.snssdk.com', True),
    ('tos-lq-x.bytedancevod.com.attacker.invalid', False),
    ('attacker-tos-lq-x.bytedancevod.com', False),
    ('other.bytedancevod.com', False),
    ('127.0.0.1', False),
])
def test_shipped_upload_checks_delegated_host_before_sending_bytes(tmp_path, host, allowed):
    import subprocess
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    image = tmp_path / 'reference.png'
    image.write_bytes(b'exact fixture image bytes')
    result = json.loads(subprocess.check_output([
        'node', str(root / 'tests/fixtures/generated_video/jimeng_upload_host.cjs'),
        str(root / 'src/ai_video/production/jimeng_browser.cjs'), host, str(image),
    ], text=True))
    assert result['ok'] is allowed
    assert result['binaryPosts'] == int(allowed)
    assert result['commits'] == int(allowed)
    assert result['cleaned'] is True
    if not allowed:
        assert result['error'] == 'upload destination invalid'
