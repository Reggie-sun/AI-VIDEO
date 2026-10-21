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


def setup(prompt="Scene {{image:0}} voice {{audio:1}} motion {{video:2}}"):
    raw = {"image-a": b"image bytes", "audio-a": b"audio bytes", "video-a": b"video bytes"}
    image = VideoImageReferenceBinding(role="reference", asset_id="image-a",
        asset_sha256=hashlib.sha256(raw["image-a"]).hexdigest(), mime_type="image/png",
        width=1280, height=720, size_bytes=len(raw["image-a"]))
    video = VideoMediaReferenceBinding(kind="video", role="reference_video",
        asset_id="video-a", asset_sha256=hashlib.sha256(raw["video-a"]).hexdigest(),
        mime_type="video/mp4", duration_millis=17_056, size_bytes=len(raw["video-a"]),
        width=1280, height=720, fps=24)
    audio = VideoMediaReferenceBinding(kind="audio", role="reference_audio",
        asset_id="audio-a", asset_sha256=hashlib.sha256(raw["audio-a"]).hexdigest(),
        mime_type="audio/wav", duration_millis=6_504, size_bytes=len(raw["audio-a"]))
    profile = JimengProfile(account_sha256="a" * 64,
        project_id="f0ed223b-090e-4ed6-b394-283f8b7dbd07",
        node_id="node_bq6wajb5xe", duration_seconds=17, resolution="720p",
        aspect_ratio="16:9", benefit_amount=34,
        benefit_type="seedance_25_720p_output", credit_upper_bound=884)
    browser, committer = FakeBrowser(), FakeCommitter()
    provider = JimengVideoProvider(profile=profile, transport=browser,
        reference_resolver=lambda binding: raw[binding.asset_id], committer=committer,
        now=lambda: NOW)
    request = _request(provider_name="jimeng", provider_kind="jimeng",
        model_id="seedance_2.5", provider_profile=profile.pointer(),
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO, prompt_text=prompt,
        image_bindings=(image,), media_bindings=(video, audio),
        output_requirement=profile.output())
    resolved = provider.resolve(request)
    video_preview = provider.preview(resolved)
    paid = PaidProviderCallPreview.create(attempt_id="attempt-jimeng-1",
        operation="video_generation", provider_kind="jimeng", model_id="seedance_2.5",
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


def test_multimodal_mapping_paid_permit_poll_and_fetch():
    provider, request, preview, paid, auth, permit, browser, committer, raw = setup()
    result = provider.submit(request, preview, paid, auth, permit)
    assert result.external_effect_id == f"{RESOURCE_ID}:{TASK_ID}"
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
    (False, "abandoned_no_dispatch"),
    (False, "tampered_unknown_canvas"),
])
def test_standard_production_service_owns_paid_submit_and_reopen(tmp_path, lose_response, missing):
    from production_remote_generation_factory import prepare_remote_generation
    from ai_video.production.project import load_production_project
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_generation import VideoGenerationService

    provider, request, _, _, _, _, browser, _, raw = setup()
    original = request.activation_scope.request
    provider._profile = provider._profile.model_copy(update={"benefit_amount": 17})
    image_only = _request(**{**original.model_dump(exclude={"request_input_hash"}),
                            "provider_profile": provider._profile.pointer(),
                            "image_bindings": original.image_bindings,
                            "media_bindings": (),
                            "prompt_text": "The room reference {{image:0}}"})
    prepared = prepare_remote_generation(root=tmp_path, provider=provider,
        request=image_only, compiler_id="jimeng-seedance-2.5-video-compiler",
        compiler_version="1", input_bytes={"image-a": raw["image-a"]},
        requirement_timing_mode="content_driven")
    resolved = prepared.resolved_request
    video_preview = provider.preview(resolved)
    paid = PaidProviderCallPreview.create(attempt_id="attempt-jimeng-1",
        operation="video_generation", provider_kind="jimeng", model_id="seedance_2.5",
        request_fingerprint=resolved.resolved_generation_hash,
        billing_mode="remote_metered", currency="CRD",
        estimated_cost_upper_bound_microunits=884_000_000,
        destination="https://jimeng.jianying.com", method="POST",
        egress_items=provider.egress_items(resolved),
        retention_mode="provider_standard", provider_policy_snapshot_id="jimeng-test",
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
    committer = ProductionStateCommitter(tmp_path, paid_provider_authorizer=lambda _: auth,
                                         paid_provider_clock=lambda: NOW)
    provider._committer = committer
    browser.fail_after_admit = lose_response
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(attempt_id=paid.attempt_id, request=resolved,
                  execution_binding=prepared.execution_binding)
    if missing == "abandoned_no_dispatch":
        committer.record_paid_provider_submit_intent(
            paid, reservation_id="jimeng-reservation-1")
        committer = ProductionStateCommitter(tmp_path, paid_provider_clock=lambda: NOW)
        provider._committer = committer
        service = VideoGenerationService(committer=committer, provider=provider)
        with pytest.raises(AiVideoError) as absent:
            service.recover_jimeng_unknown_once(attempt_id=paid.attempt_id)
        assert absent.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
        assert committer._read_manifest().attempts[-1].status.value == "outcome_unknown"
        assert browser.calls == 0
        return
    if missing in {"abandoned_intent", "tampered_unknown_canvas"}:
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
    assert service.refresh_once(attempt_id=paid.attempt_id).state is VideoTaskState.RUNNING
    if missing == "settled":
        committer.settle_paid_provider_reservation(
            attempt_id=paid.attempt_id, actual_cost_microunits=442_000_000)
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
