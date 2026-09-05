"""Contract checks for the versioned Shot 01 source-binding loader."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1"
    / "shot01_authoring_source_binding_v3.py"
)


def _module():
    spec = importlib.util.spec_from_file_location("shot01_source_binding_v3_test", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _binding(graph_hash: str = "a95a916f26b53f4a2437d90860a13910fa458e33735507963148360062e8742a"):
    return {
        "accepted_package_acceptance_path": "docs/a.json",
        "accepted_package_acceptance_sha256": "a" * 64,
        "accepted_package_payload_path": "docs/b.json",
        "accepted_package_payload_commit": "a" * 40,
        "accepted_package_payload_sha256": "b" * 64,
        "accepted_fixture_payload_path": "docs/c.json",
        "accepted_fixture_payload_commit": "b" * 40,
        "accepted_fixture_payload_sha256": "c" * 64,
        "canonical_materialization_path": "runs/evidence.json",
        "canonical_materialization_sha256": "d" * 64,
        "project_content_hash": "e" * 64,
        "registry_content_hash": "f" * 64,
        "active_pre_generation_graph_hash": graph_hash,
        "historical_request_hash": "1" * 64,
        "historical_requirement_hash": "2" * 64,
    }


def _payload(binding: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "schema_version": "drama-shot-source-binding/1",
        "record_kind": "drama_shot_source_binding",
        "overlay_id": "drama.execution-intent.key-at-the-waiting-room.shot-01",
        "binding_version": 3,
        "status": "proposed",
        "domain_id": "drama",
        "lane_id": "M6-D",
        "references": {
            name: {"path": f"docs/{name}.json", "commit": "c" * 40, "sha256": "d" * 64}
            for name in (
                "semantic_overlay_acceptance",
                "timing_repair_acceptance",
                "source_audio_policy_acceptance",
                "graph_transition_evidence",
            )
        },
        "canonical_source_binding": binding or _binding(),
    }


def test_reopen_requires_explicit_acceptance_sha_and_source_commit() -> None:
    module = _module()

    with pytest.raises(TypeError):
        module.reopen_exact_request()
    with pytest.raises(RuntimeError):
        module.reopen_exact_request(
            expected_acceptance_sha256="a" * 64,
            source_commit="not-a-commit",
        )
    with pytest.raises(RuntimeError):
        module.reopen_exact_request(
            expected_acceptance_sha256="a" * 64,
            source_commit="a" * 40,
            binding_version=2,
        )


def test_binding_payload_rejects_v1_v2_unknown_or_semantic_replacement() -> None:
    module = _module()
    original = _binding("761c92a0a8507ae2b8f14de5338b337e0d567e78b654e36403d3428a0da47ff1")

    assert module._validate_binding_payload(_payload(), original) == _binding()
    for mutate in (
        lambda value: value.update(binding_version=2),
        lambda value: value.update(generation_intent={}),
        lambda value: value["canonical_source_binding"].update(project_content_hash="0" * 64),
        lambda value: value["canonical_source_binding"].update(active_pre_generation_graph_hash="0" * 64),
        lambda value: value["references"].pop("source_audio_policy_acceptance"),
    ):
        value = _payload()
        mutate(value)
        with pytest.raises(RuntimeError):
            module._validate_binding_payload(value, original)


def test_accepted_binding_payload_requires_fixed_path_and_exact_sha(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _module()
    proposed = tmp_path / "v3.proposed.json"
    accepted = tmp_path / "v3.accepted.json"
    payload = b'{"stable":true}\n'
    proposed.write_bytes(payload)
    payload_sha = module._sha256(payload)
    accepted.write_text(
        module._canonical_json(
            {
                "schema_version": "drama-shot-source-binding-acceptance/1",
                "record_kind": "drama_shot_source_binding_acceptance",
                "overlay_id": "drama.execution-intent.key-at-the-waiting-room.shot-01",
                "binding_version": 3,
                "status": "accepted",
                "domain_id": "drama",
                "lane_id": "M6-D",
                "authority": "CURRENT_USER_METADATA_BINDING_AND_LOADER_AUTHORIZATION",
                "accepted_scope": "Metadata-only graph source-binding supersession; original v1 semantics and v2 timing repair remain immutable",
                "execution_authority": False,
                "runtime_readiness": "NOT_EVALUATED",
                "provider_submit": False,
                "candidate_activation": False,
                "m6_d": "NOT_EVALUATED",
                "next_shot_submit_allowed": False,
                "accepted_binding_payload": {
                    "path": proposed.name,
                    "commit": "c" * 40,
                    "git_blob_oid": "d" * 40,
                    "byte_size": len(payload),
                    "sha256": payload_sha,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "PROPOSAL_PATH", Path(proposed.name))
    monkeypatch.setattr(module, "ACCEPTANCE_PATH", Path(accepted.name))
    monkeypatch.setattr(module, "_git_blob", lambda commit, path: payload)
    monkeypatch.setattr(module, "_git_blob_oid", lambda commit, path: "d" * 40)

    binding, identity = module._load_accepted_binding(module._sha256(accepted.read_bytes()))
    assert binding == {"stable": True}
    assert identity["payload_sha256"] == payload_sha

    with pytest.raises(RuntimeError):
        module._load_accepted_binding("0" * 64)
    proposed.write_bytes(b'{"drift":true}\n')
    with pytest.raises(RuntimeError):
        module._load_accepted_binding(module._sha256(accepted.read_bytes()))


def test_acceptance_rejects_proposed_or_execution_authority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _module()
    proposal = tmp_path / "v3.proposed.json"
    acceptance = tmp_path / "v3.accepted.json"
    payload = b"{}\n"
    proposal.write_bytes(payload)
    record = {
        "schema_version": "drama-shot-source-binding-acceptance/1",
        "record_kind": "drama_shot_source_binding_acceptance",
        "overlay_id": "drama.execution-intent.key-at-the-waiting-room.shot-01",
        "binding_version": 3,
        "status": "accepted",
        "domain_id": "drama",
        "lane_id": "M6-D",
        "authority": "CURRENT_USER_METADATA_BINDING_AND_LOADER_AUTHORIZATION",
        "accepted_scope": "Metadata-only graph source-binding supersession; original v1 semantics and v2 timing repair remain immutable",
        "execution_authority": False,
        "runtime_readiness": "NOT_EVALUATED",
        "provider_submit": False,
        "candidate_activation": False,
        "m6_d": "NOT_EVALUATED",
        "next_shot_submit_allowed": False,
        "accepted_binding_payload": {
            "path": proposal.name,
            "commit": "c" * 40,
            "git_blob_oid": "d" * 40,
            "byte_size": len(payload),
            "sha256": module._sha256(payload),
        },
    }
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "PROPOSAL_PATH", Path(proposal.name))
    monkeypatch.setattr(module, "ACCEPTANCE_PATH", Path(acceptance.name))
    monkeypatch.setattr(module, "_git_blob", lambda commit, path: payload)
    monkeypatch.setattr(module, "_git_blob_oid", lambda commit, path: "d" * 40)
    for key, value in (("status", "proposed"), ("execution_authority", True)):
        candidate = {**record, key: value}
        acceptance.write_text(json.dumps(candidate), encoding="utf-8")
        with pytest.raises(RuntimeError):
            module._load_accepted_binding(module._sha256(acceptance.read_bytes()))


def test_graph_and_audio_facts_fail_closed() -> None:
    module = _module()
    with pytest.raises(RuntimeError):
        module._verify_reference(
            "source_audio_policy_acceptance",
            {"path": "docs/v1-audio.json", "commit": "a" * 40, "sha256": "b" * 64},
        )
    graph = {
        "graph_pointer": {"content_hash": module.ACTIVE_GRAPH_HASH},
        "new_request_identity": {key: "a" * 64 for key in module.REQUEST_IDENTITY_KEYS},
        "planning_request_hash": "b" * 64,
        "requirement_hash": "c" * 64,
        "verified_projection_hash": "d" * 64,
        "prompt_sha256": "e" * 64,
        "source_audio_policy": {"identity": {"authority_status": "ACCEPTED_AND_SEALED"}, "selection": "GENERATED + KEEP", "native_audio": True, "sound_facts_match": True},
    }
    assert module._validate_graph_evidence(graph)["graph_pointer"]["content_hash"] == module.ACTIVE_GRAPH_HASH
    graph["new_request_identity"]["preview_fingerprint"] = "bad"
    with pytest.raises(RuntimeError):
        module._validate_graph_evidence(graph)
    with pytest.raises(RuntimeError):
        module._assert_audio_policy(
            {"source_audio_policy": {"source_type": "GENERATED", "policy": "DROP"}},
            {"identity": {}, "selection": "GENERATED + KEEP", "native_audio": True, "sound_facts_match": True},
            object(),
            object(),
        )


def test_helper_rehashes_immediately_before_exec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _module()
    helper = tmp_path / "helper.py"
    helper.write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)

    with pytest.raises(RuntimeError, match="pinned helper drift before import"):
        module._load_pinned_module({"helper.py": "0" * 64}, "drifted_helper", "helper.py")
