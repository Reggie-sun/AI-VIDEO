from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from ai_video.errors import AiVideoError
from ai_video.production._state_commit_common import _canonical_json_bytes
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity, PaidProviderBudgetSnapshotPointer
from ai_video.production.paid_provider import PaidProviderBudgetSnapshot
from ai_video.production.paid_provider_budget_extension import PaidProviderBudgetCeilingExtension
from ai_video.production.paths import canonical_paid_provider_budget_path
from ai_video.production.state_commit import ProductionStateCommitter
from test_production_paid_provider_state import NOW


def _ledger(tmp_path):
    from test_generation_quality_rejection import ACTOR, _fetched_experience
    committer, _, manifest, attempt = _fetched_experience(tmp_path)
    state = attempt.video_generation_state
    committer.reject_video_generation(
        attempt_id="p8-generated-video-e2e",
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    )
    manifest = committer._read_manifest()
    pointer = manifest.active_paid_provider_budget
    return committer, manifest, pointer, committer._reopen_paid_budget(pointer)


def _entry(manifest, pointer, budget, *, extension_id="s01-one", now=None):
    now = now or datetime.now(timezone.utc)
    return PaidProviderBudgetCeilingExtension.create(
        extension_id=extension_id, project_id=manifest.project_id,
        actor=ActorIdentity(actor_id="human-owner", actor_kind="human"),
        explicit_opt_in=True, authorization_receipt_id="s01-extension-opt-in",
        expected_manifest_revision=manifest.manifest_revision, base_budget=pointer,
        policy_id=budget.policy_id, currency=budget.currency,
        old_ceiling_microunits=budget.project_ceiling_microunits,
        new_ceiling_microunits=budget.project_ceiling_microunits * 2, issued_at=now, expires_at=now + timedelta(minutes=5),
    )


def test_empty_extension_serialization_preserves_legacy_budget_hash():
    budget = PaidProviderBudgetSnapshot.create(
        revision=1, policy_id="budget-1", currency="USD",
        project_ceiling_microunits=3_000_000, reservations=(), blocked=False,
    )
    assert "ceiling_extensions" not in budget.model_dump(mode="json")
    assert budget.content_hash == canonical_sha256({
        "schema_version": "1", "revision": 1, "policy_id": "budget-1",
        "currency": "USD", "project_ceiling_microunits": 3_000_000,
        "reservations": (), "blocked": False,
    })


def test_explicit_extension_updates_only_active_budget_and_replays(tmp_path):
    committer, manifest, pointer, budget = _ledger(tmp_path)
    entry = _entry(manifest, pointer, budget)
    closed = committer.extend_paid_provider_budget(entry)
    assert closed.active_paid_provider_budget != pointer
    reopened = committer._reopen_paid_budget(closed.active_paid_provider_budget)
    assert reopened.project_ceiling_microunits == budget.project_ceiling_microunits * 2
    assert reopened.ceiling_extensions == (entry,)
    assert committer.extend_paid_provider_budget(entry) == closed


def test_stale_or_conflicting_extension_refuses_before_write(tmp_path):
    committer, manifest, pointer, budget = _ledger(tmp_path)
    entry = _entry(manifest, pointer, budget)
    stale = entry.model_copy(update={"expected_manifest_revision": manifest.manifest_revision + 1})
    with pytest.raises(AiVideoError):
        committer.extend_paid_provider_budget(stale)
    assert committer._read_manifest() == manifest


@pytest.mark.parametrize("change", [
    {"project_id": "wrong-project"}, {"policy_id": "wrong-policy"},
    {"currency": "EUR"}, {"expires_at": NOW},
])
def test_invalid_extension_identity_or_window_has_no_write(tmp_path, change):
    committer, manifest, pointer, budget = _ledger(tmp_path)
    entry = _entry(manifest, pointer, budget).model_copy(update=change)
    before = (tmp_path / "state/manifest.json").read_bytes()
    with pytest.raises(AiVideoError):
        committer.extend_paid_provider_budget(entry)
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_extension_preserves_closed_accepted_reservation_and_old_gate(tmp_path):
    from test_generation_quality_rejection import ACTOR, _fetched_experience

    committer, _, manifest, attempt = _fetched_experience(tmp_path)
    state = attempt.video_generation_state
    committer.reject_video_generation(
        attempt_id="p8-generated-video-e2e",
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
    )
    before = committer._read_manifest()
    old_pointer = before.active_paid_provider_budget
    old_budget = committer._reopen_paid_budget(old_pointer)
    assert old_budget.reservations and old_budget.reservations[0].status.value == "reserved"
    extended = committer.extend_paid_provider_budget(_entry(
        before, old_pointer, old_budget, now=datetime.now(timezone.utc)
    ))
    assert committer._reopen_paid_budget(extended.active_paid_provider_budget).reservations == old_budget.reservations
    from ai_video.production.project import load_production_project
    load_production_project(tmp_path / "project.yaml")


def test_extension_publication_fault_retains_exact_orphan_for_retry(tmp_path, monkeypatch):
    committer, manifest, pointer, budget = _ledger(tmp_path)
    entry = _entry(manifest, pointer, budget)
    original = committer._write_manifest_atomic
    monkeypatch.setattr(
        committer, "_write_manifest_atomic",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("extension publish fault")),
    )
    with pytest.raises(OSError, match="publish fault"):
        committer.extend_paid_provider_budget(entry)
    assert committer._read_manifest() == manifest
    monkeypatch.setattr(committer, "_write_manifest_atomic", original)
    assert committer.extend_paid_provider_budget(entry).active_paid_provider_budget != pointer


def _bytes(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_extension_replays_after_real_later_reservation_and_expiry(tmp_path):
    import test_production_generated_video_e2e as e2e
    from ai_video.production.project import load_production_project
    from ai_video.production.video import VideoGenerationRequest
    from ai_video.production.video_generation import VideoGenerationService
    from ai_video.production.paid_provider import PaidProviderAuthorizationDecision

    _, provider, resolved, committer = e2e._reach_fetch(tmp_path, activate_second_shot=True)
    VideoGenerationService(committer=committer, provider=provider).fetch_and_activate(attempt_id=e2e.ATTEMPT_ID)
    selected = load_production_project(tmp_path / 'project.yaml')
    pointer = selected.manifest.active_paid_provider_budget
    budget = committer._reopen_paid_budget(pointer)
    entry = _entry(selected.manifest, pointer, budget, now=committer._paid_provider_clock())
    committer.extend_paid_provider_budget(entry)
    selected = load_production_project(tmp_path / 'project.yaml')
    values = resolved.activation_scope.request.model_dump(mode='python', exclude={'request_input_hash'})
    shot = selected.shots[1]
    values.update(generation_id='budget-extension-next-generation', output_asset_id='budget-extension-next-video',
                  target_shot_id=shot.shot_id, target_shot_revision=shot.revision,
                  target_shot_content_hash=shot.content_hash, target_asset_role=shot.required_asset_roles[0].role,
                  base_project=selected.manifest.active_project, base_registry=selected.manifest.active_registry,
                  base_dependency_graph=selected.manifest.active_dependency_graph,
                  input_artifact_ids=(shot.artifact_id, selected.registry.assets[0].asset_id))
    prepared = e2e.prepare_generation_execution(project=selected, provider=provider,
        request=provider.resolve(VideoGenerationRequest.create(**values)), task_id='budget-extension-later',
        compiler_id='generated-video-e2e-fixture', compiler_version='1')
    preview = e2e._paid_preview(prepared.resolved, attempt_id='budget-extension-next',
                               video_preview=provider.preview(prepared.resolved))
    auth_data = e2e._paid_authorization(preview).model_dump(mode='python', exclude={'authorization_fingerprint'})
    auth_data['project_budget_ceiling_microunits'] = entry.new_ceiling_microunits
    authorization = PaidProviderAuthorizationDecision.create(**auth_data)
    next_committer = ProductionStateCommitter(tmp_path,
        paid_provider_authorizer=lambda exact: authorization if exact == preview else None,
        paid_provider_clock=lambda: authorization.issued_at)
    VideoGenerationService(committer=next_committer, provider=provider).start(
        attempt_id='budget-extension-next', request=prepared.resolved, execution_binding=prepared.binding)
    next_committer.record_paid_provider_submit_intent(preview, reservation_id='budget-extension-next-reservation')
    advanced = load_production_project(tmp_path / 'project.yaml')
    current = next_committer._reopen_paid_budget(advanced.manifest.active_paid_provider_budget)
    assert current.reservations[:-1] == budget.reservations
    assert current.ceiling_extensions == (entry,)
    replay_writer = ProductionStateCommitter(tmp_path, paid_provider_clock=lambda: entry.expires_at + timedelta(days=1))
    before = _bytes(tmp_path)
    assert replay_writer.extend_paid_provider_budget(entry) == advanced.manifest
    assert _bytes(tmp_path) == before
    # Current reservation does not make the original extension proof disposable.
    extension_snapshot = PaidProviderBudgetSnapshot.create(revision=budget.revision + 1,
        policy_id=budget.policy_id, currency=budget.currency, reservations=budget.reservations,
        project_ceiling_microunits=entry.new_ceiling_microunits, blocked=False, ceiling_extensions=(entry,))
    (tmp_path / canonical_paid_provider_budget_path(extension_snapshot.content_hash)).unlink()
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / 'project.yaml')


@pytest.mark.parametrize('field,value', [('project_id','foreign'), ('policy_id','foreign'), ('currency','EUR')])
def test_resealed_foreign_extension_refuses_without_artifacts(tmp_path, field, value):
    committer, manifest, pointer, budget = _ledger(tmp_path)
    values = _entry(manifest, pointer, budget).model_dump(mode='python', exclude={'content_hash'})
    values[field] = value
    entry = PaidProviderBudgetCeilingExtension.create(**values)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        committer.extend_paid_provider_budget(entry)
    assert _bytes(tmp_path) == before


def test_expiration_boundary_and_missing_opt_in_refuse_without_writes(tmp_path):
    _, manifest, pointer, budget = _ledger(tmp_path)
    entry = _entry(manifest, pointer, budget)
    committer = ProductionStateCommitter(tmp_path, paid_provider_clock=lambda: entry.expires_at)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        committer.extend_paid_provider_budget(entry)
    values = entry.model_dump(mode='python', exclude={'content_hash'})
    values['explicit_opt_in'] = False
    with pytest.raises(ValueError):
        PaidProviderBudgetCeilingExtension.create(**values)
    assert _bytes(tmp_path) == before


def test_base_raw_bytes_tamper_blocks_standard_reader_and_replay(tmp_path):
    from ai_video.production.project import load_production_project
    committer, manifest, pointer, budget = _ledger(tmp_path)
    entry = _entry(manifest, pointer, budget)
    committer.extend_paid_provider_budget(entry)
    path = tmp_path / pointer.path
    path.write_bytes(path.read_bytes() + b' ')
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / 'project.yaml')
    with pytest.raises(AiVideoError):
        committer.extend_paid_provider_budget(entry)
    assert _bytes(tmp_path) == before


def test_postpublication_fault_replays_without_second_increase(tmp_path, monkeypatch):
    committer, manifest, pointer, budget = _ledger(tmp_path)
    entry = _entry(manifest, pointer, budget)
    original = committer._write_manifest_atomic
    def published_then_failed(value):
        original(value)
        raise OSError('after publication')
    monkeypatch.setattr(committer, '_write_manifest_atomic', published_then_failed)
    with pytest.raises(OSError, match='after publication'):
        committer.extend_paid_provider_budget(entry)
    before = _bytes(tmp_path)
    assert committer.extend_paid_provider_budget(entry).manifest_revision == manifest.manifest_revision + 1
    assert _bytes(tmp_path) == before


def test_running_attempt_and_budget_overrun_cannot_be_unblocked_by_extension(tmp_path):
    from test_generation_quality_rejection import ACTOR, _fetched_experience
    committer, _, manifest, attempt = _fetched_experience(tmp_path)
    pointer = manifest.active_paid_provider_budget
    budget = committer._reopen_paid_budget(pointer)
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        committer.extend_paid_provider_budget(_entry(manifest, pointer, budget))
    assert _bytes(tmp_path) == before
    committer.reject_video_generation(attempt_id=attempt.attempt_id,
        expected_manifest_revision=manifest.manifest_revision,
        experience_content_hash=attempt.video_generation_state.generation_experiences[-1].content_hash,
        actor=ACTOR)
    committer.settle_paid_provider_reservation(attempt_id=attempt.attempt_id,
        actual_cost_microunits=budget.project_ceiling_microunits + 1)
    manifest = committer._read_manifest()
    pointer = manifest.active_paid_provider_budget
    budget = committer._reopen_paid_budget(pointer)
    assert budget.blocked
    before = _bytes(tmp_path)
    with pytest.raises(AiVideoError):
        committer.extend_paid_provider_budget(_entry(manifest, pointer, budget))
    assert _bytes(tmp_path) == before


@pytest.mark.parametrize('strip_lineage', [False, True])
def test_rehashed_budget_cannot_increase_beyond_authorized_extension(tmp_path, strip_lineage):
    from ai_video.production.project import load_production_project
    committer, manifest, pointer, budget = _ledger(tmp_path)
    extended = committer.extend_paid_provider_budget(_entry(manifest, pointer, budget))
    current = committer._reopen_paid_budget(extended.active_paid_provider_budget)
    values = current.model_dump(mode='python', exclude={'content_hash'})
    values['project_ceiling_microunits'] += 1
    if strip_lineage:
        values['ceiling_extensions'] = ()
    tampered = PaidProviderBudgetSnapshot.create(**values)
    raw = _canonical_json_bytes(tampered)
    pointer = PaidProviderBudgetSnapshotPointer(path=canonical_paid_provider_budget_path(tampered.content_hash),
        revision=tampered.revision, content_hash=tampered.content_hash, file_sha256=hashlib.sha256(raw).hexdigest())
    (tmp_path / pointer.path).write_bytes(raw)
    committer._write_manifest_atomic(extended.model_copy(update={'active_paid_provider_budget':pointer}))
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / 'project.yaml')
