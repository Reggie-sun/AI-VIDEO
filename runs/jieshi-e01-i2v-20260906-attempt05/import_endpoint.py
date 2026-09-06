"""Import the exact approved endpoint through the existing canonical P5 seam."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path

from ai_video.production.dependency import desired_fingerprints, resolve_dependency_state
from ai_video.production.hashing import seal_artifact
from ai_video.production.image_import import HumanImageImportReceipt, human_image_import_asset, prepare_human_image_import_commit
from ai_video.production.models import ArtifactReference
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter, prepare_dependency_graph_transition, prepare_project_registry_commit
from ai_video.production._state_commit_common import _canonical_yaml_bytes
from ai_video.production.video_pre_generation import VideoPreGenerationDependencyInputs, build_video_pre_generation_dependency_graph, build_video_pre_generation_applied_evidence
from prepare_i2v import planning, SOURCE_SHA

RUN = Path(__file__).resolve().parent
ROOT = RUN / "production-s01-v5"
EXPECTED = "059bb2b261883190168057b35baafc90011866acba9fb64b1c9c186122861330"


def main():
    receipt_path = RUN / "endpoint-import-receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError("Exact endpoint human input-use approval and receipt are required")
    receipt = HumanImageImportReceipt.model_validate_json(receipt_path.read_bytes())
    raw = (RUN / "shot-01-last-frame-v1.png").read_bytes()
    if (receipt.output_sha256 != EXPECTED or hashlib.sha256(raw).hexdigest() != EXPECTED
        or receipt.source_surface != "codex_imagegen_tool" or receipt.target_asset_role != "last_frame"
        or receipt.target_artifact_id != "jieshi-e01-S01" or receipt.target_kind != "repair_replacement"):
        raise RuntimeError("Endpoint receipt differs from the reviewed candidate")
    loaded = load_production_project(ROOT / "project.yaml")
    asset = human_image_import_asset(receipt)
    if asset.asset_id in {a.asset_id for a in loaded.registry.assets}:
        raise RuntimeError("Existing import requires explicit recovery, not another import")
    shot = seal_artifact(loaded.shots[0].model_copy(update={
        "revision": loaded.shots[0].revision + 1, "creation_receipt_id": receipt.content_hash,
        "required_asset_roles": tuple(r.model_copy(update={"asset_ids": (asset.asset_id,)})
            if r.role == "last_frame" else r for r in loaded.shots[0].required_asset_roles),
    }))
    path = Path(f"creative/shots/{shot.artifact_id}-r{shot.revision}.yaml")
    project = seal_artifact(loaded.project.model_copy(update={
        "revision": loaded.project.revision + 1, "creation_receipt_id": receipt.content_hash,
        "artifacts": loaded.project.artifacts.model_copy(update={"shots": (
            ArtifactReference(artifact_id=shot.artifact_id, revision=shot.revision,
                content_hash=shot.content_hash, path=path),)}),
    }))
    registry = loaded.registry.model_copy(update={"assets": (*loaded.registry.assets, asset),
        "revision_id": "0" * 64, "content_hash": "0" * 64})
    digest = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": digest, "content_hash": digest})
    commit = prepare_project_registry_commit(manifest=loaded.manifest, project=project, registry=registry,
        attempt_id="jieshi-s01-endpoint-import05")
    payload = _canonical_yaml_bytes(shot)
    commit = replace(commit, artifacts=(*commit.artifacts, PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest())))
    candidate = loaded.model_copy(update={"project": project, "shots": (shot,), "registry": registry,
        "asset_paths": {**loaded.asset_paths, asset.asset_id: ROOT / asset.artifact_path},
        "manifest": loaded.manifest.model_copy(update={"active_project": commit.next_project, "active_registry": commit.next_registry})})
    source, = (a for a in registry.assets if a.sha256 == SOURCE_SHA)
    request, _, verified = planning(candidate, source)
    inputs = VideoPreGenerationDependencyInputs(project=candidate, target_shot_id="S01", target_asset_role="final_visual",
        requirement_hash=verified.requirement.requirement_hash, planning_request_hash=request.request_content_hash,
        verified_projection_hash=verified.projection_hash)
    graph = build_video_pre_generation_dependency_graph(inputs)
    states = resolve_dependency_state(graph, build_video_pre_generation_applied_evidence(inputs)).states
    transition = prepare_dependency_graph_transition(expected_manifest_revision=loaded.manifest.manifest_revision,
        base_dependency_graph=loaded.manifest.active_dependency_graph, candidate_graph=graph,
        candidate_dependency_states=states, expected_desired_fingerprints=desired_fingerprints(graph))
    graph_payload = (json.dumps(graph.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    commit = replace(commit, dependency_graph_transition=transition, artifacts=(*commit.artifacts,
        PreparedArtifact(transition.candidate_dependency_graph.path, graph_payload, hashlib.sha256(graph_payload).hexdigest())))
    commit = prepare_human_image_import_commit(base=loaded, receipt=receipt, image_bytes=raw,
        candidate_target=shot, candidate_project=project, base_commit=commit)
    ProductionStateCommitter(ROOT).commit(commit)
    reopened = load_production_project(ROOT / "project.yaml")
    assert asset.asset_id in next(r.asset_ids for r in reopened.shots[0].required_asset_roles if r.role == "last_frame")
    print("Canonical approved endpoint import PASS")


if __name__ == "__main__":
    main()
