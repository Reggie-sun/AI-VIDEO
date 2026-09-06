"""Bootstrap only selected creative inputs and both existing import receipts."""
from pathlib import Path
import hashlib
from ai_video.production.image_import import HumanImageImportReceipt, ShotEndpointImageImportReferenceBinding
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter

RUN = Path(__file__).resolve().parent
SOURCE = RUN.parent / "jieshi-e01-i2v-20260906-attempt05" / "production-s01-v5"
ROOT = RUN / "production-s01-v6"

def main():
    source = load_production_project(SOURCE / "project.yaml")
    refs = source.project.artifacts
    paths = {refs.brief.path, refs.story.path, refs.storyboard.path}
    paths.update(r.path for r in (*refs.characters, *refs.scenes, *refs.shots))
    paths.update(a.artifact_path for a in source.registry.assets)
    for asset in source.registry.assets:
        path = Path("state/images/import-receipts") / f"{asset.creation_receipt_id}.json"
        receipt = HumanImageImportReceipt.model_validate_json((SOURCE / path).read_bytes())
        paths.add(path)
        paths.update(r.creative_artifact_path for r in receipt.references if isinstance(r, ShotEndpointImageImportReferenceBinding))
    artifacts = tuple(PreparedArtifact(p, (SOURCE / p).read_bytes(), hashlib.sha256((SOURCE / p).read_bytes()).hexdigest()) for p in sorted(paths))
    if ROOT.exists() and any(ROOT.iterdir()):
        raise RuntimeError("Existing bootstrap evidence requires explicit recovery")
    ROOT.mkdir(exist_ok=True)
    writer = ProductionStateCommitter(ROOT)
    manifest = writer.bootstrap_initial_state(attempt_id="jieshi-s01-repair06-bootstrap", project=source.project, registry=source.registry, artifacts=artifacts)
    writer.upgrade_manifest_schema("2.7", expected_manifest_revision=manifest.manifest_revision)
    loaded = load_production_project(ROOT / "project.yaml")
    assert loaded.registry == source.registry and loaded.shots == source.shots
    assert not loaded.manifest.attempts
    print("Canonical bootstrap with both approved images PASS")

if __name__ == "__main__":
    main()
