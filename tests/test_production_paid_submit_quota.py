"""Explicit additional submit authorization on the original durable task."""
from datetime import timedelta
from dataclasses import replace

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
from ai_video.production.models import ActorIdentity
from ai_video.production.project import load_production_project
from ai_video.production.shot_router import VideoGenerationResolver
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video import VideoGenerationRequest
from ai_video.production.video_generation import VideoGenerationService
from test_production_paid_budget_extension import _bytes, _entry as _money_entry
import test_production_generated_video_e2e as e2e


NEXT = "quota-next"


def _pending(tmp_path, *, used=1, local_batch_limit=1):
    _, provider, resolved, committer = e2e._reach_fetch(tmp_path, activate_second_shot=True)
    VideoGenerationService(committer=committer, provider=provider).fetch_and_activate(attempt_id=e2e.ATTEMPT_ID)
    selected = load_production_project(tmp_path / "project.yaml")
    base = committer._reopen_paid_budget(selected.manifest.active_paid_provider_budget)
    money = _money_entry(selected.manifest, selected.manifest.active_paid_provider_budget, base,
                         now=committer._paid_provider_clock())
    committer.extend_paid_provider_budget(money)
    selected = load_production_project(tmp_path / "project.yaml")
    prior = next(a for a in selected.manifest.attempts if a.attempt_id == e2e.ATTEMPT_ID)
    prior_binding = committer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    values = resolved.activation_scope.request.model_dump(mode="python", exclude={"request_input_hash"})
    shot = selected.shots[1]
    values.update(generation_id=NEXT, output_asset_id="quota-next-video",
                  target_shot_id=shot.shot_id, target_shot_revision=shot.revision,
                  target_shot_content_hash=shot.content_hash, target_asset_role=shot.required_asset_roles[0].role,
                  base_project=selected.manifest.active_project, base_registry=selected.manifest.active_registry,
                  base_dependency_graph=selected.manifest.active_dependency_graph,
                  input_artifact_ids=(shot.artifact_id, selected.registry.assets[0].asset_id))
    prepared = e2e.prepare_generation_execution(project=selected, provider=provider,
        request=provider.resolve(VideoGenerationRequest.create(**values)), task_id=prior_binding.inputs.limits.task_id,
        compiler_id="generated-video-e2e-fixture", compiler_version="1")
    old = prepared.binding
    limits = old.inputs.limits.model_copy(update={"paid_submit_ceiling": 2, "paid_submits_used": used,
                                                "local_batch_limit": local_batch_limit})
    inputs = old.inputs.model_copy(update={"limits": limits})
    decision = VideoGenerationResolver().resolve_requirement(projection=old.projection, context=old.context,
        policy=old.policy, lifecycle=old.lifecycle, inputs=inputs)
    compiled = provider.compile_request(decision.routing.provider_bound_request, old.projection.requirement)
    request = provider.resolve(compiled.request)
    binding = GenerationDecisionExecutionBinding.create(projection=old.projection, context=old.context,
        policy=old.policy, lifecycle=old.lifecycle, inputs=inputs, decision=decision, compiled_request=request)
    preview = e2e._paid_preview(request, attempt_id=NEXT, video_preview=provider.preview(request))
    authorization = e2e._paid_authorization(preview)
    from ai_video.production.paid_provider import PaidProviderAuthorizationDecision
    auth_values = authorization.model_dump(mode="python", exclude={"authorization_fingerprint"})
    auth_values["project_budget_ceiling_microunits"] = money.new_ceiling_microunits
    authorization = PaidProviderAuthorizationDecision.create(**auth_values)
    writer = ProductionStateCommitter(tmp_path,
        paid_provider_authorizer=lambda exact: authorization if exact == preview else None,
        paid_provider_clock=lambda: authorization.issued_at)
    service = VideoGenerationService(committer=writer, provider=provider)
    service.start(attempt_id=NEXT, request=request, execution_binding=binding)
    provider._scenario = replace(provider._scenario, external_effect_id="quota-next-effect")
    return writer, service, preview, prior


def _entry(writer, prior):
    from ai_video.production.paid_provider_submit_quota import PaidProviderSubmitQuotaExtension
    manifest = writer._read_manifest()
    target = next(a for a in manifest.attempts if a.attempt_id == NEXT)
    binding = writer._reopen_generation_execution_binding(target.video_generation_state.execution_binding)
    now = writer._paid_provider_clock()
    return PaidProviderSubmitQuotaExtension.create(
        extension_id="quota-one-more", project_id=manifest.project_id,
        actor=ActorIdentity(actor_id="human-owner", actor_kind="human"), explicit_opt_in=True,
        authorization_receipt_id="user-one-additional-submit", expected_manifest_revision=manifest.manifest_revision,
        base_budget=manifest.active_paid_provider_budget, target_attempt_id=NEXT,
        target_binding=target.video_generation_state.execution_binding, prior_attempt_id=prior.attempt_id,
        prior_binding=prior.video_generation_state.execution_binding, task_id=binding.inputs.limits.task_id,
        old_paid_submit_ceiling=1, new_paid_submit_ceiling=2, issued_at=now, expires_at=now + timedelta(minutes=5))


def test_same_task_extension_resumes_pending_request_and_preserves_durable_used_count(tmp_path):
    writer, service, preview, prior = _pending(tmp_path)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError, match="ceilings cannot expand"):
        service.submit_once(attempt_id=NEXT, paid_preview=preview, reservation_id="quota-reservation")
    assert _bytes(tmp_path) == before

    entry = _entry(writer, prior)
    old_manifest = writer._read_manifest()
    old_budget = writer._reopen_paid_budget(old_manifest.active_paid_provider_budget)
    amended = writer.extend_paid_provider_submit_quota(entry)
    assert amended.attempts == old_manifest.attempts
    budget = writer._reopen_paid_budget(amended.active_paid_provider_budget)
    assert budget.project_ceiling_microunits == old_budget.project_ceiling_microunits
    assert budget.reservations == old_budget.reservations
    assert budget.ceiling_extensions == old_budget.ceiling_extensions
    assert budget.submit_quota_extensions == (entry,)
    service.submit_once(attempt_id=NEXT, paid_preview=preview, reservation_id="quota-reservation")
    selected = load_production_project(tmp_path / "project.yaml")
    current = writer._reopen_paid_budget(selected.manifest.active_paid_provider_budget)
    assert len(current.reservations) == len(old_budget.reservations) + 1
    assert current.reservations[:-1] == old_budget.reservations
    assert current.submit_quota_extensions == (entry,)
    replay = ProductionStateCommitter(tmp_path, paid_provider_clock=lambda: entry.expires_at + timedelta(days=1))
    before = _bytes(tmp_path)
    assert replay.extend_paid_provider_submit_quota(entry) == selected.manifest
    assert _bytes(tmp_path) == before
    with pytest.raises(AiVideoError):
        service.submit_once(attempt_id=NEXT, paid_preview=preview, reservation_id="quota-reservation-other")
    assert _bytes(tmp_path) == before


@pytest.mark.parametrize("field,value", [
    ("project_id", "foreign"), ("task_id", "foreign"),
    ("target_attempt_id", "foreign"), ("prior_attempt_id", "foreign"),
    ("expected_manifest_revision", 999),
])
def test_resealed_wrong_authorization_refuses_without_writes(tmp_path, field, value):
    from ai_video.production.paid_provider_submit_quota import PaidProviderSubmitQuotaExtension
    writer, _, _, prior = _pending(tmp_path)
    values = _entry(writer, prior).model_dump(mode="python", exclude={"content_hash"})
    values[field] = value
    entry = PaidProviderSubmitQuotaExtension.create(**values)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        writer.extend_paid_provider_submit_quota(entry)
    assert _bytes(tmp_path) == before


def test_expired_and_missing_opt_in_are_not_authorization(tmp_path):
    from ai_video.production.paid_provider_submit_quota import PaidProviderSubmitQuotaExtension
    writer, _, _, prior = _pending(tmp_path)
    entry = _entry(writer, prior)
    expired = ProductionStateCommitter(tmp_path, paid_provider_clock=lambda: entry.expires_at)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        expired.extend_paid_provider_submit_quota(entry)
    values = entry.model_dump(mode="python", exclude={"content_hash"})
    values["explicit_opt_in"] = False
    with pytest.raises(ValueError):
        PaidProviderSubmitQuotaExtension.create(**values)
    assert _bytes(tmp_path) == before


@pytest.mark.parametrize("used,local_batch_limit", [(0, 1), (1, 2)])
def test_quota_cannot_reset_counters_or_raise_local_limits(tmp_path, used, local_batch_limit):
    writer, service, preview, prior = _pending(tmp_path, used=used, local_batch_limit=local_batch_limit)
    entry = _entry(writer, prior)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        writer.extend_paid_provider_submit_quota(entry)
        service.submit_once(attempt_id=NEXT, paid_preview=preview, reservation_id="quota-reservation")
    if used == 0:
        assert _bytes(tmp_path) == before
    else:
        target = next(a for a in writer._read_manifest().attempts if a.attempt_id == NEXT)
        assert target.paid_provider_state is None


def test_quota_base_raw_tamper_blocks_standard_reader_and_replay(tmp_path):
    writer, _, _, prior = _pending(tmp_path)
    entry = _entry(writer, prior)
    writer.extend_paid_provider_submit_quota(entry)
    base = tmp_path / entry.base_budget.path
    base.write_bytes(base.read_bytes() + b" ")
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")
    with pytest.raises(AiVideoError):
        writer.extend_paid_provider_submit_quota(entry)
    assert _bytes(tmp_path) == before


def test_current_reservation_cannot_discard_quota_lineage(tmp_path):
    import hashlib
    from ai_video.production._state_commit_common import _canonical_json_bytes
    from ai_video.production.models import PaidProviderBudgetSnapshotPointer
    from ai_video.production.paid_provider import PaidProviderBudgetSnapshot
    from ai_video.production.paths import canonical_paid_provider_budget_path
    writer, service, preview, prior = _pending(tmp_path)
    entry = _entry(writer, prior)
    writer.extend_paid_provider_submit_quota(entry)
    service.submit_once(attempt_id=NEXT, paid_preview=preview, reservation_id="quota-reservation")
    manifest = writer._read_manifest()
    current = writer._reopen_paid_budget(manifest.active_paid_provider_budget)
    values = current.model_dump(mode="python", exclude={"content_hash"})
    values["submit_quota_extensions"] = ()
    forged = PaidProviderBudgetSnapshot.create(**values)
    raw = _canonical_json_bytes(forged)
    pointer = PaidProviderBudgetSnapshotPointer(path=canonical_paid_provider_budget_path(forged.content_hash),
        revision=forged.revision, content_hash=forged.content_hash, file_sha256=hashlib.sha256(raw).hexdigest())
    (tmp_path / pointer.path).write_bytes(raw)
    writer._write_manifest_atomic(manifest.model_copy(update={"active_paid_provider_budget": pointer}))
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")


@pytest.mark.parametrize("published", [False, True])
def test_quota_publication_fault_replays_exactly_once(tmp_path, monkeypatch, published):
    writer, _, _, prior = _pending(tmp_path)
    entry = _entry(writer, prior)
    original_manifest = writer._read_manifest()
    publish = writer._write_manifest_atomic
    def fault(manifest):
        if published:
            publish(manifest)
        raise OSError("quota publication fault")
    monkeypatch.setattr(writer, "_write_manifest_atomic", fault)
    with pytest.raises(OSError, match="quota publication fault"):
        writer.extend_paid_provider_submit_quota(entry)
    monkeypatch.setattr(writer, "_write_manifest_atomic", publish)
    completed = writer.extend_paid_provider_submit_quota(entry)
    assert completed.manifest_revision == original_manifest.manifest_revision + 1
    assert load_production_project(tmp_path / "project.yaml").manifest == completed
    before = _bytes(tmp_path)
    assert writer.extend_paid_provider_submit_quota(entry) == completed
    assert _bytes(tmp_path) == before


def test_new_quota_after_submit_intent_is_rejected(tmp_path):
    from ai_video.production.paid_provider_submit_quota import PaidProviderSubmitQuotaExtension
    writer, _, preview, prior = _pending(tmp_path)
    entry = _entry(writer, prior)
    writer.extend_paid_provider_submit_quota(entry)
    writer.record_paid_provider_submit_intent(preview, reservation_id="quota-reservation")
    values = entry.model_dump(mode="python", exclude={"content_hash"})
    manifest = writer._read_manifest()
    values.update(extension_id="another-extension", expected_manifest_revision=manifest.manifest_revision,
                  base_budget=manifest.active_paid_provider_budget)
    new = PaidProviderSubmitQuotaExtension.create(**values)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        writer.extend_paid_provider_submit_quota(new)
    assert _bytes(tmp_path) == before
