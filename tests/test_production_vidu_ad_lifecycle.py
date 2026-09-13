from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import ActorIdentity
from ai_video.production.paid_provider import PaidProviderAuthorizationDecision
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.vidu import ViduTransportResponse, ViduVideoProvider
from ai_video.production.vidu_ad_contracts import AdGenerationRequest, AdImageBinding
from ai_video.production.vidu_profile import ViduAdProviderProfile
from production_project_factory import write_production_project


NOW = datetime(2026, 9, 13, tzinfo=UTC)
MP4 = b"\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isomiso2"
URL = "https://media.vidu.example/output.mp4?signature=sealed"


class AdTransport:
    def __init__(self) -> None:
        self.calls = []
        self.downloads = []
        self.submit = {"task_id": "ad-task-1", "state": "created"}
        self.queries = [{
            "id": "ad-task-1", "state": "success",
            "creations": [{"id": "creation-1", "url": URL}],
        }]
        self.body = MP4
        self.headers = {"content-type": "video/mp4", "content-length": str(len(MP4))}

    def request(self, request):
        self.calls.append(request)
        if request.method == "POST":
            return ViduTransportResponse(200, {}, json.dumps(self.submit).encode())
        query = self.queries.pop(0) if len(self.queries) > 1 else self.queries[0]
        return ViduTransportResponse(200, {}, json.dumps(query).encode())

    @contextmanager
    def stream(self, request):
        self.downloads.append(request)
        yield self

    @property
    def status_code(self):
        return 200

    def iter_bytes(self):
        yield self.body


def _profile() -> ViduAdProviderProfile:
    return ViduAdProviderProfile(
        origin="https://api.vidu.cn",
        result_origins=("https://media.vidu.example",),
        cost_upper_bound_microunits=10_000_000,
        pricing_observed_at=NOW - timedelta(minutes=1),
        pricing_expires_at=NOW + timedelta(days=1),
    )


def _provider(root: Path, transport: AdTransport, profile: ViduAdProviderProfile) -> ViduVideoProvider:
    raw = (root / "assets/files/hero.png").read_bytes()
    return ViduVideoProvider(
        profile=profile,
        transport=transport,
        credential=lambda: "PRIVATE-KEY",
        image_resolver=lambda _: raw,
        now=lambda: NOW,
    )


def _request(root: Path, profile: ViduAdProviderProfile, *, attempt: str = "ad-attempt-1",
             task_id: str = "ad-task-1", submit_limit: int = 1, prompt: str = "Show the product.") -> AdGenerationRequest:
    loaded = load_production_project(root / "project.yaml")
    image = next(asset for asset in loaded.registry.assets if asset.asset_id == "image-hero-1")
    return AdGenerationRequest.create(
        task_id=task_id,
        submit_limit=submit_limit,
        project_id=loaded.manifest.project_id,
        project_hash=loaded.manifest.active_project.content_hash,
        registry_hash=loaded.manifest.active_registry.content_hash,
        profile_hash=profile.pointer().profile_sha256,
        images=(AdImageBinding(
            asset_id=image.asset_id,
            sha256=image.sha256,
            size_bytes=image.size_bytes,
            mime_type=image.mime_type,
            width=image.width,
            height=image.height,
        ),),
        prompt=prompt,
        duration=28,
        aspect_ratio="9:16",
        language="zh",
        creative=True,
        policy_id="ad-policy-1",
        expires_at=NOW + timedelta(minutes=30),
    )


def _authorization(preview):
    return PaidProviderAuthorizationDecision.create(
        attempt_id=preview.attempt_id,
        preview_fingerprint=preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="tester", actor_kind="human"),
        opt_in_policy_receipt_id="opt-in",
        budget_policy_id="budget",
        budget_currency=preview.currency,
        project_budget_ceiling_microunits=100_000_000,
        per_call_ceiling_microunits=preview.estimated_cost_upper_bound_microunits,
        egress_authorized=True,
        egress_policy_receipt_id="egress",
        live_test_authorized=True,
        live_authorization_receipt_id="live",
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
        max_submit_count=1,
    )


def _committer(root: Path) -> ProductionStateCommitter:
    return ProductionStateCommitter(
        root,
        paid_provider_authorizer=_authorization,
        paid_provider_clock=lambda: NOW,
    )


def _prepared(root: Path, *, attempt: str = "ad-attempt-1", task_id: str = "ad-task-1",
              submit_limit: int = 1, prompt: str = "Show the product."):
    transport = AdTransport()
    profile = _profile()
    provider = _provider(root, transport, profile)
    request = _request(root, profile, attempt=attempt, task_id=task_id,
                       submit_limit=submit_limit, prompt=prompt)
    committer = _committer(root)
    state = committer.prepare_ad_generation(attempt_id=attempt, request=request, provider=provider)
    return committer, provider, transport, request, state


def test_public_lifecycle_persists_unaccepted_mp4_source_candidate(tmp_path):
    write_production_project(tmp_path)
    committer, provider, transport, request, state = _prepared(tmp_path)
    assert state.observation == "unsubmitted" and not transport.calls

    assert committer.submit_ad_generation(attempt_id="ad-attempt-1", provider=provider) == "ad-task-1"
    assert committer.query_ad_generation(attempt_id="ad-attempt-1", provider=provider).observation == "success"
    candidate = committer.fetch_ad_generation(attempt_id="ad-attempt-1", provider=provider)

    assert (tmp_path / candidate.path).read_bytes() == MP4
    assert candidate.acceptance == "not_evaluated"
    assert candidate.sha256 == hashlib.sha256(MP4).hexdigest()
    loaded = load_production_project(tmp_path / "project.yaml")
    attempt = next(item for item in loaded.manifest.attempts if item.attempt_id == "ad-attempt-1")
    assert attempt.status.value == "succeeded"
    assert attempt.ad_generation_state.candidate == candidate
    assert attempt.candidate_project is attempt.candidate_registry is None
    assert sum(call.method == "POST" for call in transport.calls) == 1


def test_restart_submit_replay_reuses_accepted_task_without_network_or_write(tmp_path):
    write_production_project(tmp_path)
    committer, provider, transport, _, _ = _prepared(tmp_path)
    assert committer.submit_ad_generation(attempt_id="ad-attempt-1", provider=provider) == "ad-task-1"
    before = (tmp_path / "state/manifest.json").read_bytes()
    calls = len(transport.calls)

    restarted = _committer(tmp_path)
    assert restarted.submit_ad_generation(attempt_id="ad-attempt-1", provider=provider) == "ad-task-1"

    assert len(transport.calls) == calls
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_task_submit_limit_counts_accepted_attempts_across_attempt_ids(tmp_path):
    write_production_project(tmp_path)
    committer, provider, transport, _, _ = _prepared(tmp_path)
    committer.submit_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    second = _request(tmp_path, _profile(), attempt="ad-attempt-2")
    committer.prepare_ad_generation(attempt_id="ad-attempt-2", request=second, provider=provider)

    with pytest.raises(AiVideoError) as exc_info:
        committer.submit_ad_generation(attempt_id="ad-attempt-2", provider=provider)

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert sum(call.method == "POST" for call in transport.calls) == 1


def test_prepare_rejects_altered_input_for_existing_attempt_without_network(tmp_path):
    write_production_project(tmp_path)
    committer, provider, transport, _, _ = _prepared(tmp_path)
    changed = _request(tmp_path, _profile(), prompt="Different sealed advertisement.")

    with pytest.raises(AiVideoError) as exc_info:
        committer.prepare_ad_generation(attempt_id="ad-attempt-1", request=changed, provider=provider)

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert not transport.calls


def test_malformed_submit_is_outcome_unknown_and_never_retries(tmp_path):
    write_production_project(tmp_path)
    committer, provider, transport, _, _ = _prepared(tmp_path)
    transport.submit = {"task_id": "ad-task-1", "state": "not-valid"}

    with pytest.raises(AiVideoError) as first:
        committer.submit_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    assert first.value.code is ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN

    with pytest.raises(AiVideoError) as retry:
        _committer(tmp_path).submit_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    assert retry.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert sum(call.method == "POST" for call in transport.calls) == 1


def test_accepted_remote_failure_remains_a_consumed_paid_request(tmp_path):
    write_production_project(tmp_path)
    committer, provider, transport, _, _ = _prepared(tmp_path)
    committer.submit_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    transport.queries = [{"id": "ad-task-1", "state": "failed"}]

    state = committer.query_ad_generation(attempt_id="ad-attempt-1", provider=provider)

    assert state.observation == "failed"
    attempt = load_production_project(tmp_path / "project.yaml").manifest.attempts[-1]
    assert attempt.status.value == "failed"
    assert attempt.paid_provider_state.phase.value == "accepted"


def test_query_identity_mismatch_preserves_durable_attempt(tmp_path):
    write_production_project(tmp_path)
    committer, provider, transport, _, _ = _prepared(tmp_path)
    committer.submit_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    transport.queries = [{"id": "other-task", "state": "processing"}]

    with pytest.raises(AiVideoError):
        committer.query_ad_generation(attempt_id="ad-attempt-1", provider=provider)

    attempt = load_production_project(tmp_path / "project.yaml").manifest.attempts[-1]
    assert attempt.ad_generation_state.observation == "unsubmitted"
    assert attempt.paid_provider_state.phase.value == "accepted"


def test_fetch_rejects_creation_change_before_candidate_publication(tmp_path):
    write_production_project(tmp_path)
    committer, provider, transport, _, _ = _prepared(tmp_path)
    committer.submit_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    transport.queries = [
        {"id": "ad-task-1", "state": "success", "creations": [{"id": "creation-1", "url": URL}]},
        {"id": "ad-task-1", "state": "success", "creations": [{"id": "creation-2", "url": URL}]},
    ]

    with pytest.raises(AiVideoError) as exc_info:
        committer.fetch_ad_generation(attempt_id="ad-attempt-1", provider=provider)

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    attempt = load_production_project(tmp_path / "project.yaml").manifest.attempts[-1]
    assert attempt.ad_generation_state.candidate is None
    assert not (tmp_path / "state/ad-generation/candidates").exists()


def test_legacy_manifest_roundtrip_does_not_add_ad_state(tmp_path):
    write_production_project(tmp_path)
    before = (tmp_path / "state/manifest.json").read_bytes()

    loaded = load_production_project(tmp_path / "project.yaml")

    assert loaded.manifest.schema_version == "2.0"
    assert "ad_generation_state" not in loaded.manifest.model_dump_json()
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_interrupted_intent_recovery_blocks_submit_without_network(tmp_path):
    write_production_project(tmp_path)
    committer, provider, transport, request, _ = _prepared(tmp_path)
    preview = provider.ad_preview(request, "ad-attempt-1")
    committer.record_paid_provider_submit_intent(preview, reservation_id="ad-intent")
    _committer(tmp_path).recover()
    attempt = load_production_project(tmp_path / "project.yaml").manifest.attempts[-1]
    assert attempt.status.value == "outcome_unknown"
    with pytest.raises(AiVideoError):
        _committer(tmp_path).submit_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    assert not transport.calls


def test_completed_fetch_and_prepare_replay_have_no_effect_after_expiry(tmp_path):
    write_production_project(tmp_path)
    committer, provider, transport, request, _ = _prepared(tmp_path)
    committer.submit_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    candidate = committer.fetch_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    before = (tmp_path / "state/manifest.json").read_bytes()
    calls, downloads = len(transport.calls), len(transport.downloads)
    provider._now = lambda: NOW + timedelta(days=2)
    provider._image_resolver = lambda _: pytest.fail("replay resolved images")
    committer.prepare_ad_generation(attempt_id="ad-attempt-1", request=request, provider=provider)
    assert committer.fetch_ad_generation(attempt_id="ad-attempt-1", provider=provider) == candidate
    assert (len(transport.calls), len(transport.downloads)) == (calls, downloads)
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_reader_rejects_changed_downloaded_bytes_and_source_receipt(tmp_path):
    write_production_project(tmp_path)
    committer, provider, _, _, _ = _prepared(tmp_path)
    committer.submit_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    candidate = committer.fetch_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    (tmp_path / candidate.path).write_bytes(MP4 + b"changed")
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")
    (tmp_path / candidate.path).write_bytes(MP4)
    (tmp_path / candidate.receipt_path).write_text("{}")
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")


def test_expired_request_and_changed_quota_block_before_submit(tmp_path):
    write_production_project(tmp_path)
    committer, provider, transport, _, _ = _prepared(tmp_path)
    changed = _request(tmp_path, _profile(), submit_limit=2)
    with pytest.raises(AiVideoError):
        committer.prepare_ad_generation(attempt_id="ad-attempt-2", request=changed, provider=provider)
    provider._now = lambda: NOW + timedelta(hours=1)
    with pytest.raises(AiVideoError):
        committer.submit_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    assert not transport.calls


def test_old_schema_rejects_typed_ad_attempt(tmp_path):
    from ai_video.production.models import ProductionManifest

    write_production_project(tmp_path)
    _prepared(tmp_path)
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    values = manifest.model_dump(mode="python", exclude_none=True, exclude_defaults=True)
    values["attempts"] = manifest.attempts
    values["schema_version"] = "2.15"
    with pytest.raises(ValueError, match="ad generation"):
        ProductionManifest(**values)
    assert ProductionManifest.model_validate_json(manifest.model_dump_json()) == manifest


def test_credential_failure_after_intent_blocks_retry_without_post(tmp_path):
    write_production_project(tmp_path)
    committer, provider, transport, _, _ = _prepared(tmp_path)

    def unavailable():
        raise RuntimeError("credential unavailable")

    provider._credential = unavailable
    with pytest.raises(AiVideoError) as failure:
        committer.submit_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    assert failure.value.code == ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN
    assert not transport.calls
    attempt = load_production_project(tmp_path / "project.yaml").manifest.attempts[-1]
    assert attempt.paid_provider_state.phase.value == "outcome_unknown"
    with pytest.raises(AiVideoError):
        committer.submit_ad_generation(attempt_id="ad-attempt-1", provider=provider)
    assert not transport.calls
