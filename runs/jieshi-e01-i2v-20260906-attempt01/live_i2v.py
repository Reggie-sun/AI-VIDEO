"""One S01 Vidu I2V submit through the paid lifecycle; stop after exact fetch."""
import base64
import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ai_video.errors import AiVideoError
from ai_video.production.models import ActorIdentity
from ai_video.production.paid_provider import PaidProviderAuthorizationDecision, PaidProviderCallPreview, PaidProviderEgressItem, SecretReference
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video import ResolvedVideoGenerationRequest, VideoTaskState
from ai_video.production.video_generation import VideoGenerationService
from ai_video.production.vidu import HttpxViduTransport, ViduVideoProvider
from ai_video.production.vidu_profile import ViduProviderProfile

RUN = Path(__file__).resolve().parent
ROOT = RUN / "production-s01-v1"
PREP = RUN / "preparation-v7"
ATTEMPT = "jieshi-e01-s01-vidu-i2v-attempt01"
EXPECTED = "7db8e13b87b2cea7fe5f961ee8aeb633c98f2d4f68c922c3635018c77bd552cc"


def event(kind, **fields):
    row = {"at": datetime.now(UTC).isoformat(), "kind": kind, **fields}
    encoded = json.dumps(row, ensure_ascii=False, sort_keys=True)
    with (PREP / "live-events.jsonl").open("a") as handle:
        handle.write(encoded + "\n")
    print(encoded, flush=True)


def credential():
    result = subprocess.run(["secret-tool", "lookup", "application", "ai-video", "provider", "vidu", "credential", "VIDU_API_KEY"], capture_output=True, timeout=15)
    if result.returncode or not result.stdout.strip():
        raise RuntimeError("Credential supplier unavailable")
    return result.stdout.decode().strip()


class AuditedTransport:
    def __init__(self, resolved):
        self.inner = HttpxViduTransport(timeout_seconds=45)
        self.resolved = resolved
        self.posts = 0

    def request(self, request):
        if request.method == "POST":
            if self.posts:
                raise RuntimeError("Task submit ceiling is one")
            payload = json.loads(request.body)
            assert request.url == "https://api.vidu.cn/ent/v2/img2video"
            assert payload["model"] == "viduq3-pro" and payload["prompt"] == self.resolved.prompt_text
            assert payload["resolution"] == "1080p" and payload["duration"] == 4
            assert payload["audio"] is False and payload["off_peak"] is False
            assert len(payload["images"]) == 1
            prefix, encoded = payload["images"][0].split(",", 1)
            assert prefix == "data:image/png;base64"
            raw = base64.b64decode(encoded, validate=True)
            binding, = self.resolved.image_bindings
            assert len(raw) == binding.size_bytes and hashlib.sha256(raw).hexdigest() == binding.asset_sha256
            self.posts += 1
            event("submit_transport_started", body_sha256=hashlib.sha256(request.body).hexdigest(), first_frame_sha256=binding.asset_sha256, first_frame_bytes=len(raw))
        response = self.inner.request(request)
        event("http_response", method=request.method, status=response.status_code, response_sha256=hashlib.sha256(response.body).hexdigest())
        return response

    def stream(self, request):
        return self.inner.stream(request)

    def close(self):
        self.inner.close()


def main(execute):
    resolved = ResolvedVideoGenerationRequest.model_validate_json((PREP / "resolved-request.json").read_bytes())
    profile = ViduProviderProfile.model_validate_json((PREP / "provider-profile.json").read_bytes())
    assert resolved.resolved_generation_hash == EXPECTED and resolved.provider_profile == profile.pointer()
    assert resolved.mode.value == "image_to_video" and len(resolved.image_bindings) == 1 and not resolved.media_bindings
    loaded = load_production_project(ROOT / "project.yaml")
    original = resolved.activation_scope.request
    assert original.base_project == loaded.manifest.active_project
    assert original.base_registry == loaded.manifest.active_registry
    assert original.base_dependency_graph == loaded.manifest.active_dependency_graph
    assert not any(a.attempt_id == ATTEMPT for a in loaded.manifest.attempts), "Existing attempt needs explicit recovery"
    assets = {a.asset_id: a for a in loaded.registry.assets}

    def image_resolver(binding):
        asset = assets[binding.asset_id]
        assert asset.sha256 == binding.asset_sha256 and asset.mime_type == binding.mime_type
        raw = (ROOT / asset.artifact_path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == binding.asset_sha256 and len(raw) == binding.size_bytes
        return raw

    transport = AuditedTransport(resolved)
    try:
        provider = ViduVideoProvider(profile=profile, transport=transport, credential=credential, image_resolver=image_resolver)
        assert provider.resolve(original) == resolved
        vp = provider.preview(resolved)
        prompt = resolved.prompt_text.encode()
        preview = PaidProviderCallPreview.create(
            attempt_id=ATTEMPT, operation="video_generation", provider_kind=resolved.provider_kind, model_id=resolved.model_id,
            request_fingerprint=EXPECTED, billing_mode="remote_metered", currency=profile.currency,
            estimated_cost_upper_bound_microunits=vp.estimated_cost_upper_bound_microunits,
            destination=vp.destination, method="POST",
            egress_items=(PaidProviderEgressItem(item_id="prompt", sha256=hashlib.sha256(prompt).hexdigest(), size_bytes=len(prompt), mime_type="text/plain", purpose="prompt"),
                *(PaidProviderEgressItem(item_id=b.asset_id, sha256=b.asset_sha256, size_bytes=b.size_bytes, mime_type=b.mime_type, purpose="reference") for b in resolved.image_bindings)),
            retention_mode="provider_standard", provider_policy_snapshot_id="jieshi-s01-vidu-i2v-user-20260906",
            secret_reference=SecretReference(kind="secret_store", reference_id="VIDU_API_KEY"),
        )
        authorization_path = PREP / "authorization.json"
        if authorization_path.exists():
            decision = PaidProviderAuthorizationDecision.model_validate_json(authorization_path.read_bytes())
            assert decision.preview_fingerprint == preview.preview_fingerprint
        else:
            now = datetime.now(UTC)
            decision = PaidProviderAuthorizationDecision.create(
                attempt_id=ATTEMPT, preview_fingerprint=preview.preview_fingerprint, explicit_opt_in=True,
                actor=ActorIdentity(actor_id="reggie", actor_kind="human"),
                opt_in_policy_receipt_id="user-jieshi-fix-then-execute-20260906",
                budget_policy_id="jieshi-s01-vidu-submit-count-one-20260906", budget_currency=profile.currency,
                project_budget_ceiling_microunits=profile.cost_upper_bound_microunits,
                per_call_ceiling_microunits=profile.cost_upper_bound_microunits,
                egress_authorized=True, egress_policy_receipt_id="user-jieshi-first-frame-vidu-20260906",
                live_test_authorized=True, live_authorization_receipt_id="user-jieshi-fix-then-execute-20260906",
                issued_at=now, expires_at=min(now + timedelta(hours=1), profile.pricing_expires_at), max_submit_count=1,
            )
            authorization_path.write_text(decision.model_dump_json(indent=2) + "\n")
            (PREP / "paid-preview.json").write_text(preview.model_dump_json(indent=2) + "\n")
        if not execute:
            event("paid_preview_ready_no_submit", preview_hash=preview.preview_fingerprint, max_submit_count=1)
            return
        credential()
        writer = ProductionStateCommitter(ROOT, paid_provider_authorizer=lambda exact: decision if exact == preview else None)
        service = VideoGenerationService(committer=writer, provider=provider)
        service.start(attempt_id=ATTEMPT, request=resolved)
        submission = service.submit_once(attempt_id=ATTEMPT, paid_preview=preview, reservation_id="jieshi-s01-vidu-i2v-reservation01")
        event("submit_accepted", submission_fingerprint=submission.submission_fingerprint)
        for ordinal in range(90):
            observation = service.refresh_once(attempt_id=ATTEMPT)
            event("poll", ordinal=ordinal, state=observation.state.value)
            if observation.state is VideoTaskState.FAILED:
                event("generation_failed_no_retry")
                return
            if observation.state is VideoTaskState.SUCCEEDED:
                break
            time.sleep(10)
        else:
            event("poll_limit_reached_requires_explicit_resume")
            return
        fetched = service.fetch_once(attempt_id=ATTEMPT)
        path = ROOT / fetched.relative_path
        event("fetched_unactivated", path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size_bytes=path.stat().st_size,
              next_action="exact MP4 project-local video-analysis Gate")
        event("reservation_retained_no_actual_billing_evidence")
    finally:
        transport.close()


if __name__ == "__main__":
    try:
        main(execute=sys.argv[1:] == ["--execute"])
    except AiVideoError as exc:
        event("stopped", error_code=exc.code.value, message=exc.user_message)
        sys.exit(1)
    except Exception as exc:
        event("stopped", error_type=type(exc).__name__)
        sys.exit(1)
