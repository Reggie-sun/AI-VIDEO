"""Imported legacy evidence stays distinct from new execution authority."""

import hashlib

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator, RegisteredGenerationTarget
from ai_video.production.generation_history_import import ImportedGenerationSourceDocument, ImportedGenerationEvaluationSourceAttribution
from ai_video.production.models import ActorIdentity, ProductionManifest
from ai_video.production.project import load_production_project
from ai_video.production.video_generation import VideoGenerationService
from test_generation_history_import_receipt import _legacy_source
from test_production_generated_video_e2e import ATTEMPT_ID, _runtime


def _setup(tmp_path):
    source_root, target_root = tmp_path / "source", tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    source, experience, policy, evaluation = _legacy_source(source_root)
    _, provider, request, template, preview, writer = _runtime(target_root)
    loaded = load_production_project(target_root / "project.yaml")
    if loaded.qa_policy != policy:
        writer.activate_qa_policy(policy, expected_manifest_revision=loaded.manifest.manifest_revision,
                                  attempt_id="select-retrospective-qa")
    raw = "Historical evaluation: exact fetched result FAIL."
    (source_root / "original-review.txt").write_text(raw)
    document = ImportedGenerationSourceDocument(kind="historical", relative_path="original-review.txt",
        sha256=hashlib.sha256(raw.encode()).hexdigest(), text=raw)
    kwargs = dict(
        expected_manifest_revision=writer._read_manifest().manifest_revision,
        expected_source_manifest_sha256=hashlib.sha256((source_root / "state/manifest.json").read_bytes()).hexdigest(),
        import_id="import-legacy", source_attempt_id=ATTEMPT_ID,
        experience=experience, source_documents=(document,), evidence_root=source_root,
        evaluation_source_attributions=(ImportedGenerationEvaluationSourceAttribution(
            evaluation_source_sha256=evaluation.source_sha256, document_sha256s=(document.sha256,)),),
        actor=ActorIdentity(actor_id="test-importer", actor_kind="automation"),
    )
    return source_root, target_root, source, provider, request, template, preview, writer, kwargs


def test_import_retains_failure_without_source_mutation_and_replays_without_writes(tmp_path, monkeypatch):
    src, root, source, provider, _, _, _, writer, kwargs = _setup(tmp_path)
    before = writer._read_manifest()
    source_bytes = (src / "state/manifest.json").read_bytes()
    imported = writer.import_generation_experience(src, **kwargs)
    assert imported.manifest_revision == before.manifest_revision + 1
    assert imported.attempts == before.attempts
    assert imported.active_paid_provider_budget == before.active_paid_provider_budget
    assert (src / "state/manifest.json").read_bytes() == source_bytes
    assert load_production_project(root / "project.yaml").manifest == imported
    assert writer.read_generation_experiences() == (kwargs["experience"],)
    assert writer.read_generation_experiences()[0].evidence[0].findings[0].verdict == "FAIL"
    assert provider.call_counts.submit == provider.call_counts.status == provider.call_counts.fetch == 0

    def no_write(*args, **kwargs):
        pytest.fail("exact import replay must not write")

    monkeypatch.setattr(writer, "_write_immutable_artifact", no_write)
    monkeypatch.setattr(writer, "_write_manifest_atomic", no_write)
    assert writer.import_generation_experience(src / "unavailable", **kwargs) == imported
    with pytest.raises(AiVideoError, match="replay differs"):
        writer.import_generation_experience(src, **{**kwargs, "expected_source_manifest_sha256": "0" * 64})


def test_imported_media_tamper_blocks_standard_project_reopen(tmp_path):
    src, root, _, _, _, _, _, writer, kwargs = _setup(tmp_path)
    writer.import_generation_experience(src, **kwargs)
    media, = (root / "state/video-generation/imported-media").glob("*.mp4")
    media.write_bytes(b"tampered")
    with pytest.raises(AiVideoError):
        load_production_project(root / "project.yaml")


def test_import_rejects_duplicate_source_and_late_history_insertion(tmp_path):
    src, _, _, provider, request, template, _, writer, kwargs = _setup(tmp_path)
    writer.import_generation_experience(src, **kwargs)
    with pytest.raises(AiVideoError, match="already imported"):
        writer.import_generation_experience(src, **{**kwargs, "import_id": "renamed",
            "expected_manifest_revision": writer._read_manifest().manifest_revision})
    VideoGenerationService(committer=writer, provider=provider).start(
        attempt_id="new-prepared", request=request, execution_binding=template)
    with pytest.raises(AiVideoError, match="precede new video"):
        writer.import_generation_experience(src, **{**kwargs, "import_id": "late",
            "expected_manifest_revision": writer._read_manifest().manifest_revision})


def test_imported_failure_is_the_baseline_and_cannot_be_omitted_at_submit(tmp_path):
    src, root, _, provider, request, template, preview, writer, kwargs = _setup(tmp_path)
    writer.import_generation_experience(src, **kwargs)
    candidate = template.inputs.candidates[0]

    def context(loaded):
        return dict(projection=template.projection, context=template.context,
                    policy=template.policy, lifecycle=template.lifecycle)

    caller = GenerationFeedbackOrchestrator.for_project(
        committer=writer, targets=(RegisteredGenerationTarget(provider, candidate.provider_profile,
            candidate.compiler_contract, candidate.output_requirement),),
        context_loader=context, policy=template.inputs.policy)
    limits = template.inputs.limits.model_copy(update={"task_id": "newly-authorized-repair",
        "allowed_remote_candidates": (f"{candidate.capabilities.provider_name}/{candidate.capability_id}",)})
    prepared = caller.prepare(limits=limits)
    assert prepared.inputs.latest_attempt_hash == kwargs["experience"].evidence[0].evidence_hash
    assert prepared.inputs.baseline_request.request_input_hash == kwargs["experience"].evidence[0].request_hash
    assert prepared.inputs.limits.paid_submits_used == 0
    assert prepared.decision.diagnosis.failed_requirements
    assert prepared.decision.disposition == "GENERATE_ONCE"
    assert prepared.execution_binding is not None
    service = VideoGenerationService(committer=writer, provider=provider)
    service.start(attempt_id="repair", request=prepared.resolved_request,
                  execution_binding=prepared.execution_binding)
    _, state = service._state("repair")
    writer._require_submit_execution_binding(writer._read_manifest(), state, prepared.resolved_request)
    assert provider.call_counts.submit == provider.call_counts.status == provider.call_counts.fetch == 0


def test_old_first_attempt_binding_cannot_omit_imported_history(tmp_path):
    src, _, _, provider, request, template, _, writer, kwargs = _setup(tmp_path)
    writer.import_generation_experience(src, **kwargs)
    service = VideoGenerationService(committer=writer, provider=provider)
    service.start(attempt_id="omitted", request=request, execution_binding=template)
    _, state = service._state("omitted")
    with pytest.raises(AiVideoError, match="history"):
        writer._require_submit_execution_binding(writer._read_manifest(), state, request)
    assert provider.call_counts.submit == 0


def test_empty_history_keeps_old_manifest_serialization(tmp_path):
    _, _, _, _, _, _, _, writer, _ = _setup(tmp_path)
    manifest = writer._read_manifest()
    raw = manifest.model_dump(mode="json")
    assert "imported_generation_experiences" not in raw
    assert ProductionManifest.model_validate(raw) == manifest


def test_failed_manifest_publication_preserves_source_and_requires_explicit_import_retry(tmp_path, monkeypatch):
    src, root, _, provider, _, _, _, writer, kwargs = _setup(tmp_path)
    original = writer._write_manifest_atomic
    before = writer._read_manifest()
    source_bytes = (src / "state/manifest.json").read_bytes()

    def fail_manifest(*args, **kwargs):
        raise OSError("injected publication failure")

    monkeypatch.setattr(writer, "_write_manifest_atomic", fail_manifest)
    with pytest.raises(OSError, match="publication failure"):
        writer.import_generation_experience(src, **kwargs)
    assert load_production_project(root / "project.yaml").manifest == before
    assert (src / "state/manifest.json").read_bytes() == source_bytes
    assert writer.read_generation_experiences() == ()
    monkeypatch.setattr(writer, "_write_manifest_atomic", original)
    result = writer.import_generation_experience(src, **kwargs)
    assert len(result.imported_generation_experiences) == 1
    assert provider.call_counts.submit == 0


def test_failure_after_manifest_publication_replays_without_duplicate_import(tmp_path, monkeypatch):
    src, root, _, _, _, _, _, writer, kwargs = _setup(tmp_path)
    original = writer._write_manifest_atomic

    def publish_then_fail(manifest):
        original(manifest)
        raise OSError("injected post-publication failure")

    monkeypatch.setattr(writer, "_write_manifest_atomic", publish_then_fail)
    with pytest.raises(OSError, match="post-publication"):
        writer.import_generation_experience(src, **kwargs)
    current = load_production_project(root / "project.yaml").manifest
    assert len(current.imported_generation_experiences) == 1
    assert writer.import_generation_experience(src / "unavailable", **kwargs) == current
