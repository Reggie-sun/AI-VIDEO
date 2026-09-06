"""Bootstrap an independent repair experiment from exact registered source bytes."""
import hashlib
from pathlib import Path

from ai_video.production.project import load_production_project
from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import ArtifactReference, AssetRoleRequirement, AssetType
from ai_video.production._state_commit_common import _canonical_yaml_bytes

RUN = Path(__file__).resolve().parent
SOURCE = RUN.parent / "jieshi-e01-i2v-20260906-attempt04" / "production-s01-v4"
ROOT = RUN / "production-s01-v5"


def main():
    source = load_production_project(SOURCE / "project.yaml")
    refs = source.project.artifacts
    paths = {refs.brief.path, refs.story.path, refs.storyboard.path}
    paths.update(ref.path for ref in (*refs.characters, *refs.scenes))
    paths.update(asset.artifact_path for asset in source.registry.assets)
    paths.add(Path("state/images/import-receipts/89318576d4eed1eafaaba834f57b832f8376168d25ac735125791966ad9109b1.json"))
    artifacts = []
    for path in sorted(paths):
        payload = (SOURCE / path).read_bytes()
        artifacts.append(PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest()))
    shot = seal_artifact(source.shots[0].model_copy(update={
        "revision": source.shots[0].revision + 1,
        "creation_receipt_id": "jieshi-s01-repair05-endpoint-role",
        "required_asset_roles": (*source.shots[0].required_asset_roles,
            AssetRoleRequirement(role="last_frame",
                asset_ids=next(r.asset_ids for r in source.shots[0].required_asset_roles if r.role == "first_frame"),
                allowed_asset_types=(AssetType.IMAGE,))),
    }))
    shot_path = Path(f"creative/shots/{shot.artifact_id}-r{shot.revision}.yaml")
    project = seal_artifact(source.project.model_copy(update={
        "revision": source.project.revision + 1, "creation_receipt_id": "jieshi-s01-repair05-endpoint-role",
        "artifacts": source.project.artifacts.model_copy(update={"shots": (
            ArtifactReference(artifact_id=shot.artifact_id, revision=shot.revision,
                content_hash=shot.content_hash, path=shot_path),)}),
    }))
    payload = _canonical_yaml_bytes(shot)
    artifacts.append(PreparedArtifact(shot_path, payload, hashlib.sha256(payload).hexdigest()))
    if ROOT.exists() and any(ROOT.iterdir()):
        raise RuntimeError("Existing bootstrap evidence requires explicit recovery")
    ROOT.mkdir(exist_ok=True)
    writer = ProductionStateCommitter(ROOT)
    manifest = writer.bootstrap_initial_state(
        attempt_id="jieshi-s01-repair05-bootstrap",
        project=project, registry=source.registry, artifacts=tuple(artifacts),
    )
    writer.upgrade_manifest_schema("2.7", expected_manifest_revision=manifest.manifest_revision)
    loaded = load_production_project(ROOT / "project.yaml")
    assert loaded.project == project and loaded.registry == source.registry
    assert not loaded.manifest.attempts
    print("Canonical independent bootstrap PASS; previous Manifest untouched")


if __name__ == "__main__":
    main()
