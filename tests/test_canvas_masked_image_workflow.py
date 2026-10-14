"""Shared masked-image preparation and canonical lifecycle, with scripted media."""
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path

from PIL import Image, ImageDraw
import pytest

from ai_video.canvas_production import CanvasProductionService
from ai_video.canvas_image import canvas_image_candidate_preparer
from ai_video.canvas_dependencies import initialize_canvas_graph
from ai_video.errors import AiVideoError
from ai_video.production.image import (
    ImageGenerationAuthorization, ImageGenerationRequest, ImageGenerationPreview, ImageProviderResult,
    ImageLocalResourceEvidence,
)
from ai_video.production.models import (
    AssetRecord, AssetRegistrySnapshot, AssetSourceKind, AssetType, ToolIdentity,
    StateCommitStatus,
)
from ai_video.production.paths import canonical_image_asset_path
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter
from test_canvas_authoring import packet, direction


ROOT = Path(__file__).parents[1]
PROFILE = ROOT / "workflows/profiles/p7_1_qwen_masked_edit.json"


def png(image):
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def runtime(tmp_path):
    data = direction()
    data["characters"] = [{"character_id": "hero", "name": "Fixture actor",
        "identity": "fictional", "appearance_bible": "Blue jacket",
        "reference_asset_ids": ["character"]}]
    data["scenes"][0]["visual_reference_asset_ids"] = ["scene", "edit-mask"]
    for row in data["shots"]:
        row["shot"]["required_asset_roles"].append({"role": "first_frame",
            "asset_ids": ["scene"], "allowed_asset_types": ["image"]})
    source = Image.new("RGB", (256, 256), (30, 60, 90))
    mask = Image.new("L", source.size, 0)
    ImageDraw.Draw(mask).rectangle((80, 80, 120, 120), fill=255)
    payloads = {"character": png(Image.new("RGB", source.size, (90, 30, 60))),
                "scene": png(source), "edit-mask": png(mask)}
    assets, artifacts = [], []
    for aid, payload in payloads.items():
        sha = hashlib.sha256(payload).hexdigest()
        path = canonical_image_asset_path(sha)
        assets.append(AssetRecord(asset_id=aid, asset_type=AssetType.IMAGE,
            artifact_path=path, sha256=sha, size_bytes=len(payload), mime_type="image/png",
            width=256, height=256, source_kind=AssetSourceKind.IMPORTED,
            tool=ToolIdentity(name="scripted-input", version="1"), input_artifact_ids=(),
            input_fingerprint=sha, creation_receipt_id="scripted-input", usage_license="fixture"))
        artifacts.append(PreparedArtifact(path, payload, sha))
    registry = AssetRegistrySnapshot(revision_id="0" * 64, content_hash="0" * 64,
        assets=tuple(sorted(assets, key=lambda a: a.asset_id)))
    sha = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": sha, "content_hash": sha})
    writer = ProductionStateCommitter(tmp_path,
        image_candidate_preparer=canvas_image_candidate_preparer())
    service = CanvasProductionService(committer=writer, packet=packet(), direction=data)
    bundle = service.author(registry=registry, asset_artifacts=tuple(artifacts))
    bundle.bootstrap(committer=writer, attempt_id="masked-author")
    initialize_canvas_graph(writer, "masked-author-graph")
    return service, payloads, source


def prepare(service):
    return service.prepare_image_workflow(attempt_id="masked-local", shot_id="one",
        target_asset_role="first_frame", character_id="hero", character_asset_id="character",
        source_asset_id="scene", mask_asset_id="edit-mask", seed=7,
        prompt_text="Change only the selected region.", negative_prompt_text="",
        profile_path=PROFILE, artifact_root=ROOT)


def test_shared_preparation_is_exact_readonly_and_preserves_authoring(tmp_path):
    service, payloads, _ = runtime(tmp_path)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    original = deepcopy(service.direction)
    result = prepare(service)
    request, preview = result["request"], result["preview"]
    assert tuple(r.role for r in request.references) == ("character", "scene", "edit_mask")
    assert request._fingerprint_payload(request.model_dump(mode="json"))["schema"] == "ai-video-image-request/6"
    assert preview.reference_asset_ids == ("character", "scene", "edit-mask")
    assert preview.reference_total_bytes == sum(map(len, payloads.values()))
    assert result["input_validation"] == "PASS"
    assert result["runtime_readiness"] == result["production_acceptance"] == "NOT_EVALUATED"
    assert service.direction == original
    assert before == {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


@pytest.mark.parametrize("provider", ["grok", "seedream", "fake-local"])
def test_masked_request_cannot_cross_to_another_provider(tmp_path, provider):
    service, _, _ = runtime(tmp_path)
    values = prepare(service)["request"].model_dump(mode="json",
        exclude={"request_id", "request_fingerprint", "output_asset_id"})
    values["provider_kind"] = provider
    with pytest.raises(ValueError, match="comfyui_local"):
        ImageGenerationRequest.create(**values)


def test_unselected_mask_rejected_before_any_intent(tmp_path):
    service, _, _ = runtime(tmp_path)
    before = service._load().manifest
    with pytest.raises(AiVideoError):
        service.prepare_image_workflow(attempt_id="unselected", shot_id="one",
            target_asset_role="first_frame", character_id="hero", character_asset_id="character",
            source_asset_id="scene", mask_asset_id="character", seed=7, prompt_text="Edit",
            profile_path=PROFILE, artifact_root=ROOT)
    assert service._load().manifest == before


def test_pixel_preparation_revises_current_registry_and_reopens_exact_lineage(tmp_path):
    from ai_video.production.image_preparation import CanvasImagePreparationOperation
    service, _, _ = runtime(tmp_path)
    before = service._load()
    source = next(a for a in before.registry.assets if a.asset_id == "scene")
    operation = CanvasImagePreparationOperation(kind="crop", source_asset_id="scene",
        source_sha256=source.sha256, new_asset_id="identity-crop",
        usage_license="fixture explicit local crop", crop_box=(32, 32, 128, 160))
    prepared = service.prepare_image_assets(operations=[operation])
    assert service._load().manifest == before.manifest
    assert all(a in prepared.registry.assets for a in before.registry.assets)
    data = deepcopy(service.direction)
    data["characters"][0]["reference_asset_ids"].append("identity-crop")
    service.direction = data
    service.revise_authoring(attempt_id="prepared-crop-revision", registry=prepared.registry,
        asset_artifacts=prepared.artifacts)
    after = service._load()
    assert all(a in after.registry.assets for a in before.registry.assets)
    assert after.characters[0].revision == before.characters[0].revision + 1
    assert after.characters[0].reference_asset_ids[-1] == "identity-crop"
    assert after.manifest.attempts[:len(before.manifest.attempts)] == before.manifest.attempts
    assert after.asset_paths[source.asset_id].read_bytes() == before.asset_paths[source.asset_id].read_bytes()
    receipt = next(a for a in prepared.artifacts if a.relative_path.suffix == ".json")
    (tmp_path / receipt.relative_path).write_bytes(b"{}")
    with pytest.raises(AiVideoError, match="Prepared image evidence"):
        load_production_project(tmp_path / "project.yaml")


class ScriptedProvider:
    def __init__(self, profile, image_bytes):
        self.profile, self.image_bytes = profile, image_bytes
        self.calls = 0

    def preflight(self, request):
        assert request.model_id == self.profile.profile_id

    def generate(self, request, authorization, permit):
        assert permit._consume_image_generation_permit(request_fingerprint=request.request_fingerprint)
        self.calls += 1
        return ImageProviderResult.create(request=request, authorization=authorization,
            image_bytes=self.image_bytes, content_type="image/png", provider_request_id="scripted-masked",
            adapter=ToolIdentity(name="comfyui-local-image", version=self.profile.profile_content_hash[:16]),
            resource_evidence=ImageLocalResourceEvidence(elapsed_milliseconds=1,
                device_kind="cpu", measured_peak_memory_bytes=None))


def generated_runtime(tmp_path):
    service, _, source = runtime(tmp_path)
    prepared = prepare(service)
    profile, request, preview = (prepared[k] for k in ("execution_profile", "request", "preview"))
    edited = source.copy()
    edited.putpixel((100, 100), (255, 0, 0))
    provider = ScriptedProvider(profile, png(edited))
    authorization = ImageGenerationAuthorization.create(request=request, preview=preview,
        usage_license="scripted-only", policy_receipt_id="scripted-mask-policy")
    service.committer.generate_image_asset(request, preview, authorization, provider,
        execution_profile=profile)
    return service, request


def prepared_authoring(service, *, legacy_sort=False, mutation=None, attempt_id="post-image-preparation"):
    from ai_video.production.image_preparation import CanvasImagePreparationOperation
    before = service._load()
    source = next(a for a in before.registry.assets if a.asset_id == "scene")
    prepared = service.prepare_image_assets(operations=[CanvasImagePreparationOperation(
        kind="crop", source_asset_id="scene", source_sha256=source.sha256,
        new_asset_id=f"crop-{attempt_id}", usage_license="fixture explicit crop",
        crop_box=(32, 32, 128, 160))])
    data = deepcopy(service.direction)
    data["characters"][0]["reference_asset_ids"].append(prepared.assets[0].asset_id)
    service.direction = data
    records = prepared.registry.assets
    if legacy_sort:
        records = tuple(sorted(records, key=lambda a: a.asset_id))
    if mutation:
        records = mutation(records)
        available = {a.asset_id for a in records}
        data["characters"][0]["reference_asset_ids"] = [
            aid for aid in data["characters"][0]["reference_asset_ids"] if aid in available]
        service.direction = data
    registry = prepared.registry.model_copy(update={"assets": records})
    digest = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": digest, "content_hash": digest})
    service.revise_authoring(attempt_id=attempt_id, registry=registry,
        asset_artifacts=prepared.artifacts)
    return before, prepared


def test_preparation_after_generation_preserves_exact_registry_prefix(tmp_path):
    service, request = generated_runtime(tmp_path)
    before, _ = prepared_authoring(service)
    after = service._load()
    assert after.registry.assets[:len(before.registry.assets)] == before.registry.assets
    assert after.asset_paths[request.output_asset_id].read_bytes() == before.asset_paths[request.output_asset_id].read_bytes()


def test_legacy_sorted_authoring_reopens_without_rewriting_state_or_history(tmp_path):
    service, request = generated_runtime(tmp_path)
    before, _ = prepared_authoring(service, legacy_sort=True)
    frozen = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    after = service._load()
    assert after.registry.assets[:len(before.registry.assets)] != before.registry.assets
    assert after.manifest.attempts[:len(before.manifest.attempts)] == before.manifest.attempts
    assert after.asset_paths[request.output_asset_id].read_bytes() == before.asset_paths[request.output_asset_id].read_bytes()
    assert frozen == {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


def test_registry_authoring_chain_reopens_multiple_exact_edges(tmp_path):
    service, _ = generated_runtime(tmp_path)
    prepared_authoring(service, legacy_sort=True, attempt_id="first-edge")
    first = service._load()
    prepared_authoring(service, legacy_sort=True, attempt_id="second-edge")
    after = service._load()
    assert all(record in after.registry.assets for record in first.registry.assets)
    assert after.manifest.manifest_revision == first.manifest.manifest_revision + 2


def test_restored_prefix_allows_next_generation_without_extending_reorder_exception(tmp_path):
    service, _ = generated_runtime(tmp_path)
    before, _ = prepared_authoring(service, legacy_sort=True)
    current = service._load()
    retained = {a.asset_id for a in before.registry.assets}
    records = (*before.registry.assets,
               *(a for a in current.registry.assets if a.asset_id not in retained))
    registry = current.registry.model_copy(update={"assets": records})
    digest = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": digest, "content_hash": digest})
    service.revise_authoring(attempt_id="restore-registry-order", registry=registry)
    restored = service._load()
    assert restored.registry.assets[:len(before.registry.assets)] == before.registry.assets
    prepared = prepare(service)
    request = prepared["request"].model_copy()
    values = request.model_dump(mode="json", exclude={"request_id", "request_fingerprint", "output_asset_id"})
    values["attempt_id"] = "next-masked-local"
    request = ImageGenerationRequest.create(**values)
    preview = ImageGenerationPreview.create(request=request,
        reference_total_bytes=prepared["preview"].reference_total_bytes)
    source = Image.open(BytesIO(restored.asset_paths["scene"].read_bytes())).convert("RGB")
    source.putpixel((100, 100), (0, 255, 0))
    provider = ScriptedProvider(prepared["execution_profile"], png(source))
    authorization = ImageGenerationAuthorization.create(request=request, preview=preview,
        usage_license="scripted-only", policy_receipt_id="scripted-mask-policy")
    service.committer.generate_image_asset(request, preview, authorization, provider,
        execution_profile=prepared["execution_profile"])
    assert load_production_project(tmp_path / "project.yaml").manifest.attempts[-1].status is StateCommitStatus.SUCCEEDED


@pytest.mark.parametrize("change", ["record-mutation", "record-deletion", "unreferenced-addition"])
def test_registry_reorder_cannot_hide_old_record_changes_or_unreferenced_additions(tmp_path, change):
    service, _ = generated_runtime(tmp_path)
    def mutation(records):
        if change == "record-mutation":
            return tuple(a.model_copy(update={"usage_license": "changed"})
                if a.asset_id == "character" else a for a in records)
        if change == "record-deletion":
            return tuple(a for a in records if a.asset_id != "character")
        record = next(a for a in records if a.asset_id == "character")
        return (*records, record.model_copy(update={"asset_id": "unused-reference"}))
    with pytest.raises(AiVideoError):
        prepared_authoring(service, legacy_sort=True, mutation=mutation)
        load_production_project(tmp_path / "project.yaml")


@pytest.mark.parametrize("change", ["missing-edge", "wrong-operation", "broken-base", "snapshot-bytes"])
def test_registry_reorder_requires_exact_succeeded_authoring_chain(tmp_path, change):
    service, _ = generated_runtime(tmp_path)
    prepared_authoring(service, legacy_sort=True)
    path = tmp_path / "state/manifest.json"
    from ai_video.production.models import ProductionManifest
    manifest = ProductionManifest.model_validate_json(path.read_bytes())
    edge = manifest.attempts[-1]
    if change == "snapshot-bytes":
        snapshot = tmp_path / edge.base_registry.path
        snapshot.write_bytes(snapshot.read_bytes() + b" ")
    else:
        if change == "missing-edge":
            attempts = manifest.attempts[:-1]
        elif change == "wrong-operation":
            attempts = (*manifest.attempts[:-1], edge.model_copy(update={"operation": "repair"}))
        else:
            attempts = (*manifest.attempts[:-1], edge.model_copy(update={
                "base_registry": manifest.attempts[0].base_registry}))
        manifest = manifest.model_copy(update={"attempts": attempts})
        path.write_text(manifest.model_dump_json())
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")


def test_canonical_generation_reopens_mask_lineage_and_replays_without_provider(tmp_path):
    service, _, source = runtime(tmp_path)
    prepared = prepare(service)
    profile, request, preview = (prepared[k] for k in ("execution_profile", "request", "preview"))
    edited = source.copy()
    edited.putpixel((100, 100), (255, 0, 0))
    provider = ScriptedProvider(profile, png(edited))
    authorization = ImageGenerationAuthorization.create(request=request, preview=preview,
        usage_license="scripted-only", policy_receipt_id="scripted-mask-policy")
    manifest = service.committer.generate_image_asset(request, preview, authorization, provider,
        execution_profile=profile)
    assert manifest.attempts[-1].status is StateCommitStatus.SUCCEEDED
    loaded = load_production_project(tmp_path / "project.yaml")
    output = next(a for a in loaded.registry.assets if a.asset_id == request.output_asset_id)
    assert "edit-mask" in output.input_artifact_ids
    assert loaded.asset_paths[output.asset_id].read_bytes() == png(edited)
    assert service.committer.generate_image_asset(request, preview, authorization, provider,
        execution_profile=profile) == manifest
    assert provider.calls == 1


def test_protected_pixel_change_never_activates_even_if_provider_claims_success(tmp_path):
    service, _, source = runtime(tmp_path)
    prepared = prepare(service)
    profile, request, preview = (prepared[k] for k in ("execution_profile", "request", "preview"))
    before = service._load().manifest
    edited = source.copy()
    edited.putpixel((0, 0), (255, 0, 0))
    provider = ScriptedProvider(profile, png(edited))
    authorization = ImageGenerationAuthorization.create(request=request, preview=preview,
        usage_license="scripted-only", policy_receipt_id="scripted-mask-policy")
    with pytest.raises(AiVideoError):
        service.committer.generate_image_asset(request, preview, authorization, provider,
            execution_profile=profile)
    loaded = load_production_project(tmp_path / "project.yaml")
    assert loaded.manifest.active_project == before.active_project
    assert loaded.manifest.active_registry == before.active_registry
    assert all(a.asset_id != request.output_asset_id for a in loaded.registry.assets)


def test_cli_preparation_never_loads_operator_runtime(tmp_path, monkeypatch):
    import scripts.canvas_production as entry
    from test_canvas_project_data import text_data
    source, definition = text_data()
    (tmp_path / "source.json").write_text(json.dumps(source))
    data_path = tmp_path / "data.json"
    data_path.write_text(json.dumps(definition))
    (tmp_path / "production").mkdir()
    service, _, _ = runtime(tmp_path / "production")
    monkeypatch.setattr(entry, "open_canvas_project", lambda **kw: (service, None, ()))
    result = entry.run(data_path=data_path, project_root=tmp_path / "production",
        action="prepare_image_workflow", runtime_factory="must_not_exist:must_not_load",
        arguments={"attempt_id": "masked-local", "shot_id": "one", "target_asset_role": "first_frame",
            "character_id": "hero", "character_asset_id": "character", "source_asset_id": "scene",
            "mask_asset_id": "edit-mask", "seed": 7, "prompt_text": "Change selected region.",
            "profile_path": PROFILE, "artifact_root": ROOT})
    assert result["input_validation"] == "PASS"
    assert result["runtime_readiness"] == "NOT_EVALUATED"
