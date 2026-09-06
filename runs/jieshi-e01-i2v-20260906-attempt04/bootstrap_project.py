"""Bootstrap an independent repair experiment from exact registered source bytes."""
import hashlib
from pathlib import Path

from ai_video.production.project import load_production_project
from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter

RUN = Path(__file__).resolve().parent
SOURCE = RUN.parent / "jieshi-e01-i2v-20260906-attempt03" / "production-s01-v3"
ROOT = RUN / "production-s01-v4"


def main():
    source = load_production_project(SOURCE / "project.yaml")
    refs = source.project.artifacts
    paths = {refs.brief.path, refs.story.path, refs.storyboard.path}
    paths.update(ref.path for ref in (*refs.characters, *refs.scenes, *refs.shots))
    paths.update(asset.artifact_path for asset in source.registry.assets)
    paths.add(Path("state/images/import-receipts/89318576d4eed1eafaaba834f57b832f8376168d25ac735125791966ad9109b1.json"))
    artifacts = []
    for path in sorted(paths):
        payload = (SOURCE / path).read_bytes()
        artifacts.append(PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest()))
    ROOT.mkdir(exist_ok=False)
    writer = ProductionStateCommitter(ROOT)
    manifest = writer.bootstrap_initial_state(
        attempt_id="jieshi-s01-repair04-bootstrap",
        project=source.project, registry=source.registry, artifacts=tuple(artifacts),
    )
    writer.upgrade_manifest_schema("2.7", expected_manifest_revision=manifest.manifest_revision)
    loaded = load_production_project(ROOT / "project.yaml")
    assert loaded.project == source.project and loaded.registry == source.registry
    assert not loaded.manifest.attempts
    print("Canonical independent bootstrap PASS; previous Manifest untouched")


if __name__ == "__main__":
    main()
