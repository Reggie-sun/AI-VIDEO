from __future__ import annotations

from collections import Counter

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production import _paid_provider_project_reader as reader
from ai_video.production.project import load_production_project
from test_production_paid_budget_extension import _entry, _ledger


def _extended_ledger(tmp_path, count=4):
    writer, manifest, pointer, budget = _ledger(tmp_path)
    for index in range(count):
        extension = _entry(manifest, pointer, budget, extension_id=f"traversal-{index}")
        manifest = writer.extend_paid_provider_budget(extension)
        pointer = manifest.active_paid_provider_budget
        budget = writer._reopen_paid_budget(pointer)
    return writer, manifest, budget


def _count_history(monkeypatch):
    calls = Counter()
    original = reader._verify_budget_extensions

    def counted(root, budget, *args, **kwargs):
        calls[budget.content_hash] += 1
        return original(root, budget, *args, **kwargs)

    monkeypatch.setattr(reader, "_verify_budget_extensions", counted)
    return calls


def test_shared_history_is_verified_once_per_budget_read(tmp_path, monkeypatch):
    writer, manifest, budget = _extended_ledger(tmp_path)
    calls = _count_history(monkeypatch)
    assert writer._reopen_paid_budget(manifest.active_paid_provider_budget) == budget
    assert len(calls) == 5
    assert set(calls.values()) == {1}


def test_manifest_roots_share_one_history_traversal(tmp_path, monkeypatch):
    _extended_ledger(tmp_path)
    calls = _count_history(monkeypatch)
    load_production_project(tmp_path / "project.yaml")
    assert set(calls.values()) == {1}


def _mixed_ledger(tmp_path, *, submit=False):
    from test_production_paid_submit_quota import NEXT, _entry as quota_entry, _pending

    writer, service, preview, prior = _pending(tmp_path)
    extension = quota_entry(writer, prior)
    manifest = writer.extend_paid_provider_submit_quota(extension)
    if submit:
        service.submit_once(attempt_id=NEXT, paid_preview=preview, reservation_id="traversal-submit")
        manifest = writer._read_manifest()
    return writer, manifest, extension


def test_mixed_ceiling_quota_and_gate_roots_are_verified_once(tmp_path, monkeypatch):
    _mixed_ledger(tmp_path, submit=True)
    calls = _count_history(monkeypatch)
    selected = load_production_project(tmp_path / "project.yaml")
    assert selected.manifest.active_paid_provider_budget is not None
    # Other standard-loader owners may perform their own fresh public reads.
    calls.clear()
    reader.verify_paid_provider_evidence(tmp_path, selected.manifest)
    assert len(calls) >= 4
    assert set(calls.values()) == {1}


@pytest.mark.parametrize("entrypoint", ["pointer", "content_hash", "project"])
def test_new_read_rechecks_historical_base_bytes(tmp_path, entrypoint):
    writer, manifest, budget = _extended_ledger(tmp_path, count=2)

    def read():
        if entrypoint == "pointer":
            return writer._reopen_paid_budget(manifest.active_paid_provider_budget)
        if entrypoint == "content_hash":
            return reader.load_paid_provider_budget_by_content_hash(tmp_path, budget.content_hash)
        return load_production_project(tmp_path / "project.yaml")

    read()
    base = tmp_path / budget.ceiling_extensions[0].base_budget.path
    base.write_bytes(base.read_bytes() + b" ")
    before = (tmp_path / "state/manifest.json").read_bytes()
    with pytest.raises(AiVideoError) as failure:
        read()
    expected_code = (ErrorCode.PRODUCTION_STATE_INVALID if entrypoint == "pointer"
                     else ErrorCode.PRODUCTION_PROJECT_INVALID)
    assert failure.value.code == expected_code
    assert (tmp_path / "state/manifest.json").read_bytes() == before


@pytest.mark.parametrize("binding_kind", ["target_binding", "prior_binding"])
def test_new_read_rechecks_published_quota_binding_bytes(tmp_path, binding_kind):
    _, _, extension = _mixed_ledger(tmp_path)
    load_production_project(tmp_path / "project.yaml")
    binding = tmp_path / getattr(extension, binding_kind).path
    binding.write_bytes(binding.read_bytes() + b" ")
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")


def test_missing_first_quota_snapshot_is_rejected_after_prior_success(tmp_path):
    from ai_video.production.paths import canonical_paid_provider_budget_path

    writer, manifest, _ = _mixed_ledger(tmp_path, submit=True)
    budget = writer._reopen_paid_budget(manifest.active_paid_provider_budget)
    load_production_project(tmp_path / "project.yaml")
    extension = budget.submit_quota_extensions[0]
    base = writer._reopen_paid_budget(extension.base_budget)
    first = type(budget).create(
        revision=base.revision + 1, policy_id=base.policy_id, currency=base.currency,
        project_ceiling_microunits=base.project_ceiling_microunits,
        reservations=base.reservations, ceiling_extensions=base.ceiling_extensions,
        submit_quota_extensions=(*base.submit_quota_extensions, extension), blocked=False,
    )
    assert first.content_hash != budget.content_hash
    (tmp_path / canonical_paid_provider_budget_path(first.content_hash)).unlink()
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")


@pytest.mark.parametrize("update", [{"file_sha256": "0" * 64}, {"revision": 999}])
def test_pointer_identity_is_checked_on_every_read(tmp_path, update):
    writer, manifest, _ = _extended_ledger(tmp_path, count=2)
    pointer = manifest.active_paid_provider_budget
    writer._reopen_paid_budget(pointer)
    with pytest.raises(AiVideoError):
        reader.load_paid_provider_budget(tmp_path, pointer.model_copy(update=update))


def test_repeated_pointer_visit_rechecks_bytes_within_one_traversal(tmp_path, monkeypatch):
    writer, manifest, budget = _extended_ledger(tmp_path, count=3)
    leaf = budget.ceiling_extensions[0].base_budget
    original = reader._verify_budget_extensions
    changed = False

    def drift_after_leaf(root, current, *args, **kwargs):
        nonlocal changed
        result = original(root, current, *args, **kwargs)
        if current.content_hash == leaf.content_hash and not changed:
            path = tmp_path / leaf.path
            path.write_bytes(path.read_bytes() + b" ")
            changed = True
        return result

    monkeypatch.setattr(reader, "_verify_budget_extensions", drift_after_leaf)
    with pytest.raises(AiVideoError):
        writer._reopen_paid_budget(manifest.active_paid_provider_budget)
    assert changed


def test_active_ancestry_remains_a_cycle_guard(tmp_path):
    _, manifest, _ = _extended_ledger(tmp_path, count=2)
    pointer = manifest.active_paid_provider_budget
    with pytest.raises(AiVideoError, match="cyclic"):
        reader.load_paid_provider_budget(tmp_path, pointer, _seen={pointer.content_hash})
