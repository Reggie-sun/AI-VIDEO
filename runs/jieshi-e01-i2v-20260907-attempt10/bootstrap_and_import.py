"""Create a fresh repair project and import the exact user-approved endpoint."""
from dataclasses import replace
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

from ai_video.production.hashing import seal_artifact
from ai_video.production.dependency import desired_fingerprints, resolve_dependency_state
from ai_video.production.video_pre_generation import VideoPreGenerationDependencyInputs, build_video_pre_generation_dependency_graph, build_video_pre_generation_applied_evidence
from ai_video.production.state_commit import prepare_dependency_graph_transition
from planning import planning, SOURCE_SHA
from ai_video.production.image_import import (
    HumanImageImportReceipt, ShotEndpointImageImportReferenceBinding,
    human_image_import_asset, prepare_human_image_import_commit,
)
from ai_video.production.models import ActorIdentity, ArtifactReference
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter, prepare_project_registry_commit
from ai_video.production._state_commit_common import _canonical_yaml_bytes

RUN = Path(__file__).resolve().parent
SOURCE = RUN.parent / "jieshi-e01-i2v-20260906-attempt09/production-s01-v9"
ROOT = RUN / "production-s01-v10"
IMAGE = RUN.parent / "jieshi-s01-hand-repair-20260906-001/endpoint-repair-03.png"
EXPECTED = "d9a21860e91cadc7cf4cfe0ce74a44b57c2aa6d600b8c8cc06dc17e4fb4cd1da"


def artifact(path, payload):
    return PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest())


def main():
    if ROOT.exists():
        raise RuntimeError("Existing project requires explicit recovery")
    source = load_production_project(SOURCE / "project.yaml")
    refs = source.project.artifacts
    paths = {refs.brief.path, refs.story.path, refs.storyboard.path}
    paths.update(r.path for r in (*refs.characters, *refs.scenes, *refs.shots))
    paths.update(a.artifact_path for a in source.registry.assets)
    for asset in source.registry.assets:
        path = Path("state/images/import-receipts") / f"{asset.creation_receipt_id}.json"
        receipt = HumanImageImportReceipt.model_validate_json((SOURCE / path).read_bytes())
        paths.add(path)
        paths.update(r.creative_artifact_path for r in receipt.references
                     if isinstance(r, ShotEndpointImageImportReferenceBinding))
    raw = IMAGE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED and len(raw) == 2051993
    prompt = (RUN / "endpoint-image-prompt.txt").read_text()
    old_shot = source.shots[0]
    old_role = next(r for r in old_shot.required_asset_roles if r.role == "last_frame")
    old_asset = next(a for a in source.registry.assets if a.asset_id in old_role.asset_ids)
    receipt = HumanImageImportReceipt.create(
        schema_version="1", source_surface="codex_imagegen_tool",
        declared_ui_product_label="Codex image_gen.imagegen", original_filename=IMAGE.name,
        output_sha256=EXPECTED, output_size_bytes=len(raw), output_width=941, output_height=1672,
        imported_at=datetime.fromtimestamp(IMAGE.stat().st_mtime, UTC).isoformat(),
        prompt_fingerprint=hashlib.sha256(prompt.encode()).hexdigest(),
        references=(ShotEndpointImageImportReferenceBinding(
            role="shot_endpoint", creative_artifact_id=old_shot.artifact_id,
            creative_revision=old_shot.revision, creative_content_hash=old_shot.content_hash,
            creative_artifact_path=refs.shots[0].path, asset_role="last_frame",
            asset_id=old_asset.asset_id, asset_sha256=old_asset.sha256),),
        target_kind="repair_replacement", target_artifact_id=old_shot.artifact_id,
        target_asset_role="last_frame", human_actor=ActorIdentity(actor_id="reggie", actor_kind="human"),
        approved=True, approved_at=datetime.now(UTC).isoformat(),
        license_source_note="Project fictional still edited with Codex image_gen from the prior registered endpoint. User replied 确认 to endpoint-repair-03.png SHA d9a21860e91c input-use approval on 2026-09-07. Approval time is recorded now; no human video-quality verdict. Exact historical image prompt recovered from its original tool call.",
    )
    ROOT.mkdir()
    writer = ProductionStateCommitter(ROOT)
    manifest = writer.bootstrap_initial_state(
        attempt_id="jieshi-s01-repair10-bootstrap", project=source.project, registry=source.registry,
        artifacts=tuple(artifact(p, (SOURCE / p).read_bytes()) for p in sorted(paths)))
    writer.upgrade_manifest_schema("2.7", expected_manifest_revision=manifest.manifest_revision)
    loaded = load_production_project(ROOT / "project.yaml")
    asset = human_image_import_asset(receipt)
    shot = seal_artifact(old_shot.model_copy(update={
        "revision": old_shot.revision + 1, "creation_receipt_id": receipt.content_hash,
        "required_asset_roles": tuple(r.model_copy(update={"asset_ids": (asset.asset_id,)})
            if r.role == "last_frame" else r for r in old_shot.required_asset_roles)}))
    path = Path(f"creative/shots/{shot.artifact_id}-r{shot.revision}.yaml")
    project = seal_artifact(loaded.project.model_copy(update={
        "revision": loaded.project.revision + 1, "creation_receipt_id": receipt.content_hash,
        "artifacts": loaded.project.artifacts.model_copy(update={"shots": (
            ArtifactReference(artifact_id=shot.artifact_id, revision=shot.revision,
                              content_hash=shot.content_hash, path=path),)})}))
    registry = loaded.registry.model_copy(update={"assets": (*loaded.registry.assets, asset),
                                                 "revision_id": "0" * 64, "content_hash": "0" * 64})
    digest = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": digest, "content_hash": digest})
    commit = prepare_project_registry_commit(manifest=loaded.manifest, project=project,
        registry=registry, attempt_id="jieshi-s01-repair10-endpoint-import")
    commit = replace(commit, artifacts=(*commit.artifacts, artifact(path, _canonical_yaml_bytes(shot))))
    candidate = loaded.model_copy(update={"project": project, "shots": (shot,), "registry": registry,
        "asset_paths": {**loaded.asset_paths, asset.asset_id: ROOT / asset.artifact_path},
        "manifest": loaded.manifest.model_copy(update={"active_project": commit.next_project, "active_registry": commit.next_registry})})
    source_asset, = (a for a in registry.assets if a.sha256 == SOURCE_SHA)
    request, _, verified = planning(candidate, source_asset)
    inputs = VideoPreGenerationDependencyInputs(project=candidate, target_shot_id="S01", target_asset_role="final_visual",
        requirement_hash=verified.requirement.requirement_hash, planning_request_hash=request.request_content_hash,
        verified_projection_hash=verified.projection_hash)
    graph = build_video_pre_generation_dependency_graph(inputs)
    states = resolve_dependency_state(graph, build_video_pre_generation_applied_evidence(inputs)).states
    transition = prepare_dependency_graph_transition(expected_manifest_revision=loaded.manifest.manifest_revision,
        base_dependency_graph=loaded.manifest.active_dependency_graph, candidate_graph=graph,
        candidate_dependency_states=states, expected_desired_fingerprints=desired_fingerprints(graph))
    payload = (json.dumps(graph.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    commit = replace(commit, dependency_graph_transition=transition,
        artifacts=(*commit.artifacts, artifact(transition.candidate_dependency_graph.path, payload)))
    commit = prepare_human_image_import_commit(base=loaded, receipt=receipt, image_bytes=raw,
        candidate_target=shot, candidate_project=project, base_commit=commit)
    writer.commit(commit)
    reopened = load_production_project(ROOT / "project.yaml")
    assert reopened.shots[0] == shot and asset in reopened.registry.assets
    (RUN / "endpoint-import-receipt.json").write_text(receipt.model_dump_json(indent=2) + "\n")
    print(json.dumps({"status": "canonical_approved_endpoint_imported", "receipt_hash": receipt.content_hash,
                      "image_sha256": EXPECTED, "shot_revision": shot.revision}))


if __name__ == "__main__":
    main()
