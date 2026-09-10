"""Development admission preserves failures; it never qualifies or activates media."""

import hashlib
import json
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.project import load_production_project
from ai_video.production.hashing import seal_artifact
from ai_video.production.state_commit import ProductionStateCommitter
from test_generation_quality_rejection import _fetched_experience, ACTOR
from test_production_bootstrap import _bootstrap_inputs
from test_production_generated_video_e2e import ATTEMPT_ID


def _files(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def _inputs(tmp_path, *, close=True):
    source = tmp_path / "source"
    source.mkdir()
    committer, experience, manifest, attempt = _fetched_experience(source)
    if close:
        committer.reject_video_generation(attempt_id=ATTEMPT_ID,
            expected_manifest_revision=manifest.manifest_revision,
            experience_content_hash=attempt.video_generation_state.generation_experiences[-1].content_hash,
            actor=ACTOR)
    template = tmp_path / "template"
    template.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    writer = ProductionStateCommitter(target)
    project, registry, artifacts = _bootstrap_inputs(template, writer)
    project = seal_artifact(project.model_copy(update={"project_id": "repair-development"}))
    return source, target, writer, dict(attempt_id="repair-input-bootstrap", project=project,
        registry=registry, artifacts=artifacts, source_root=source,
        source_attempt_id=ATTEMPT_ID, source_sha256=experience.evidence[0].artifact_sha256,
        asset_id="failed-source", usage_license="development fixture only")


def test_admit_exact_failure_is_unbound_and_replay_adds_no_writes(tmp_path):
    from ai_video.production.repair_input_admission import verify_repair_input
    from ai_video.production.generation_rejection import GenerationQualityRejectionReceipt

    source, target, writer, args = _inputs(tmp_path)
    before = _files(source)
    manifest = writer.bootstrap_repair_input(**args)
    loaded = load_production_project(target / "project.yaml")
    asset = next(a for a in loaded.registry.assets if a.asset_id == "failed-source")
    assert asset.source_kind.value == "imported"
    assert asset.sha256 == args["source_sha256"]
    assert hashlib.sha256(loaded.asset_paths[asset.asset_id].read_bytes()).hexdigest() == asset.sha256
    assert manifest.attempts == ()
    assert manifest.imported_generation_experiences == ()
    assert manifest.active_paid_provider_budget is None
    assert loaded.qa_policy is None
    receipt = verify_repair_input(asset, target)
    documents = {d.path: d.text for d in receipt.documents}
    source_manifest = ProductionStateCommitter(source)._read_manifest()
    state = next(a for a in source_manifest.attempts if a.attempt_id == ATTEMPT_ID).video_generation_state
    rejection = GenerationQualityRejectionReceipt.model_validate_json(documents[state.quality_rejection.path])
    assert rejection.qa_policy.path in documents
    assert not any(asset.asset_id in r.asset_ids for s in loaded.shots for r in s.required_asset_roles)
    assert _files(source) == before
    admitted = _files(target)
    assert writer.bootstrap_repair_input(**args) == manifest
    assert _files(target) == admitted
    assert _files(source) == before


@pytest.mark.parametrize("invalid", ["running", "sha", "overlap"])
def test_invalid_source_rejected_before_any_target_write(tmp_path, invalid):
    source, target, writer, args = _inputs(tmp_path, close=invalid != "running")
    before = _files(source)
    if invalid == "sha":
        args["source_sha256"] = "0" * 64
    if invalid == "overlap":
        writer = ProductionStateCommitter(source)
    with pytest.raises(AiVideoError):
        writer.bootstrap_repair_input(**args)
    assert _files(source) == before
    assert _files(target) == {}


def test_strict_reader_rejects_tampered_admission_receipt(tmp_path):
    from ai_video.production.repair_input_admission import repair_input_receipt_path

    _, target, writer, args = _inputs(tmp_path)
    writer.bootstrap_repair_input(**args)
    loaded = load_production_project(target / "project.yaml")
    asset = next(a for a in loaded.registry.assets if a.asset_id == "failed-source")
    path = target / repair_input_receipt_path(asset.creation_receipt_id)
    path.write_bytes(path.read_bytes().replace(b'"NOT_EVALUATED"', b'"PASS"', 1))
    with pytest.raises(AiVideoError):
        load_production_project(target / "project.yaml")


def test_development_input_cannot_be_bound_as_production_visual(tmp_path):
    from ai_video.production.models import AssetRoleRequirement, AssetType, VisualStrategy
    from ai_video.production.validation import validate_shot_strategy

    _, target, writer, args = _inputs(tmp_path)
    writer.bootstrap_repair_input(**args)
    loaded = load_production_project(target / "project.yaml")
    shot = seal_artifact(loaded.shots[0].model_copy(update={
        "visual_strategy": VisualStrategy.EXISTING_VIDEO,
        "required_asset_roles": (AssetRoleRequirement(role="final_visual", asset_ids=("failed-source",),
            allowed_asset_types=(AssetType.VIDEO,)),),
    }))
    with pytest.raises(AiVideoError, match="repair input"):
        validate_shot_strategy(shot, {a.asset_id: a for a in loaded.registry.assets})


def test_admission_cannot_be_claimed_by_another_project(tmp_path):
    from ai_video.production.validation import validate_project_references

    _, target, writer, args = _inputs(tmp_path)
    writer.bootstrap_repair_input(**args)
    loaded = load_production_project(target / "project.yaml")
    other = seal_artifact(loaded.project.model_copy(update={"project_id": "other-project"}))
    with pytest.raises(AiVideoError, match="repair input"):
        validate_project_references(loaded.model_copy(update={"project": other}))


def test_import_marker_cannot_be_removed_to_skip_provenance(tmp_path):
    from ai_video.production.models import ToolIdentity
    from ai_video.production.registry import _verify_asset

    _, target, writer, args = _inputs(tmp_path)
    writer.bootstrap_repair_input(**args)
    loaded = load_production_project(target / "project.yaml")
    asset = next(a for a in loaded.registry.assets if a.asset_id == "failed-source")
    disguised = asset.model_copy(update={"tool": ToolIdentity(name="ordinary-import", version="1")})
    with pytest.raises(AiVideoError):
        _verify_asset(disguised, target, target / "assets")


@pytest.mark.parametrize("corruption", ["qa_hash", "request_id", "fetch_size"])
def test_resealed_capture_cannot_hide_inner_identity_mismatch(tmp_path, corruption):
    from ai_video.production.hashing import canonical_sha256
    from ai_video.production.repair_input_admission import verify_repair_input, RepairInputAdmissionReceipt

    _, target, writer, args = _inputs(tmp_path)
    writer.bootstrap_repair_input(**args)
    loaded = load_production_project(target / "project.yaml")
    asset = next(a for a in loaded.registry.assets if a.asset_id == "failed-source")
    payload = verify_repair_input(asset, target).model_dump(mode="json")
    manifest = json.loads(payload["source_manifest_json"])
    state = next(a for a in manifest["attempts"] if a["attempt_id"] == ATTEMPT_ID)["video_generation_state"]
    if corruption == "qa_hash":
        rejection_doc = next(d for d in payload["documents"] if d["path"] == state["quality_rejection"]["path"])
        rejection = json.loads(rejection_doc["text"])
        qa_doc = next(d for d in payload["documents"] if d["path"] == rejection["qa_policy"]["path"])
        qa = json.loads(qa_doc["text"])
        qa["policy_id"] = "changed-with-stale-semantic-hash"
        qa_doc["text"] = json.dumps(qa)
        qa_doc["file_sha256"] = hashlib.sha256(qa_doc["text"].encode()).hexdigest()
        rejection["qa_policy"]["file_sha256"] = qa_doc["file_sha256"]
        rejection["qa_policy"]["policy_id"] = qa["policy_id"]
        rejection["content_hash"] = canonical_sha256(rejection)
        rejection_doc["text"] = json.dumps(rejection)
        rejection_doc["file_sha256"] = hashlib.sha256(rejection_doc["text"].encode()).hexdigest()
        old_path = rejection_doc["path"]
        rejection_doc["path"] = old_path.replace(state["quality_rejection"]["content_hash"], rejection["content_hash"])
        state["quality_rejection"].update(path=rejection_doc["path"],
            content_hash=rejection["content_hash"], file_sha256=rejection_doc["file_sha256"])
    elif corruption == "request_id":
        state["request"]["generation_id"] = "another-generation"
        state["generation_id"] = "another-generation"
    else:
        state["fetch_receipt"]["artifact_size_bytes"] += 1
    payload["source_manifest_json"] = json.dumps(manifest)
    payload["source_manifest_sha256"] = hashlib.sha256(payload["source_manifest_json"].encode()).hexdigest()
    payload["content_hash"] = canonical_sha256(payload)
    with pytest.raises(ValueError):
        RepairInputAdmissionReceipt.model_validate(payload)
