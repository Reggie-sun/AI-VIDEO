"""Materialize the approved episode through the canonical bootstrap writer."""
import hashlib
import json
from pathlib import Path

import yaml

from ai_video.production import models
from ai_video.production.hashing import seal_artifact, verify_artifact_hash
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import ProductionStateCommitter

REPO = Path(__file__).resolve().parents[2]
ROOT = Path(__file__).resolve().parent / "production-s01-repair-v1"
SOURCE = REPO / "docs/superpowers/artifacts/drama/jieshi-episode-01"
SOURCE_SHA = "d0a373ce062564cc5ca64f075db38cbdc1f295063a27dbbeacaf982ca12de921"


def main():
    proposal = SOURCE / "episode-01.proposed.json"
    assert hashlib.sha256(proposal.read_bytes()).hexdigest() == SOURCE_SHA
    snapshot = json.loads((SOURCE / "creative-artifacts.json").read_text())
    assert snapshot["source_sha256"] == SOURCE_SHA
    ROOT.mkdir(exist_ok=False)
    writer = ProductionStateCommitter(ROOT)
    refs, prepared = {}, []
    types = {
        "brief": models.ProductionBrief, "story": models.Story,
        "characters": models.Character, "scenes": models.Scene,
        "storyboard": models.Storyboard, "shots": models.Shot,
    }
    for key, cls in types.items():
        rows = snapshot["artifacts"][key]
        plural = isinstance(rows, list)
        if key == "shots":
            rows = [row for row in rows if row["shot_id"] == "S01"]
        group = []
        for row in rows if plural else (rows,):
            artifact = cls.model_validate(row)
            assert verify_artifact_hash(artifact)
            if key == "storyboard":
                beats = tuple(beat.model_copy(update={"shot_ids": ("S01",)})
                              for beat in artifact.beats if "S01" in beat.shot_ids)
                artifact = seal_artifact(artifact.model_copy(update={
                    "revision": artifact.revision + 1, "beats": beats,
                    "creation_receipt_id": "jieshi-e01-first-shot-projection",
                }))
            if key == "shots":
                artifact = seal_artifact(artifact.model_copy(update={
                    "revision": artifact.revision + 1,
                    "creation_receipt_id": "jieshi-e01-pending-video-bootstrap",
                    "required_asset_roles": (models.AssetRoleRequirement(
                        role="final_visual", asset_ids=(),
                        allowed_asset_types=(models.AssetType.VIDEO,),
                    ),),
                }))
                artifact = cls.model_validate(artifact.model_dump(mode="json"))
            path = Path("creative") / key / f"{artifact.artifact_id}-r{artifact.revision}.yaml"
            group.append(models.ArtifactReference(
                artifact_id=artifact.artifact_id, revision=artifact.revision,
                content_hash=artifact.content_hash, path=path,
            ))
            payload = yaml.safe_dump(artifact.model_dump(mode="json"),
                                     allow_unicode=True, sort_keys=True).encode()
            prepared.append(writer.prepare_artifact("jieshi-e01-repair25-bootstrap", path, payload))
        refs[key] = tuple(group) if plural else group[0]
    project = seal_artifact(models.ProductionProject(
        artifact_id="jieshi-e01-s01-repair25-project", revision=1, content_hash="0" * 64,
        creation_receipt_id="jieshi-e01-pending-video-bootstrap",
        source_provenance=(models.SourceReference(
            kind="derived", reference=str(proposal.relative_to(REPO)), content_hash=SOURCE_SHA,
        ),),
        project_id="jieshi-e01-s01-repair25", title="界蚀：不存在的终点站／开场首镜2.5修复", default_language="zh-CN",
        delivery_profile=models.DeliveryProfile(width=1080, height=1920, fps=24),
        renderer_policy=models.RendererPolicy(), artifacts=models.ProjectArtifactRefs(**refs),
    ))
    registry = models.AssetRegistrySnapshot(
        schema_version="2.2", revision_id="0" * 64, content_hash="0" * 64, assets=(),
    )
    digest = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": digest, "content_hash": digest})
    writer.bootstrap_initial_state(attempt_id="jieshi-e01-repair25-bootstrap", project=project,
                                   registry=registry, artifacts=tuple(prepared))
    loaded = load_production_project(ROOT / "project.yaml")
    assert len(loaded.shots) == 1 and len(loaded.registry.assets) == 0
    assert loaded.project.delivery_profile.width == 1080
    print(json.dumps({"status": "canonical_bootstrap_reopened", "shots": len(loaded.shots),
                      "assets": 0, "project_hash": loaded.project.content_hash,
                      "manifest_revision": loaded.manifest.manifest_revision}))


if __name__ == "__main__":
    main()
