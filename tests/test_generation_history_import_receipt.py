"""Strict retrospective import receipt coverage using an offline remote fixture."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ai_video.production._state_commit_common import _canonical_json_bytes
from ai_video.production.generation_diagnosis import AttemptEvidence
from ai_video.production.generation_evaluation import (
    GenerationEvaluationSource,
    GenerationObservation,
)
from ai_video.production.generation_experience import GenerationExperience
from ai_video.production.generation_history_import import (
    ImportedGenerationEvaluationSourceAttribution,
    ImportedGenerationSourceDocument,
    load_imported_generation_experience,
    prepare_generation_history_import,
)
from ai_video.production._lifecycle_schema import ImportedGenerationExperienceReceiptPointer
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity
from ai_video.production.project import load_production_project
from ai_video.production.video import VideoTaskState
from ai_video.production.video_generation import VideoGenerationService

from test_production_generated_video_e2e import ATTEMPT_ID, _runtime


def _document(evidence_root, text: str, *, relative_path=Path("observations/legacy-gate.md")) -> ImportedGenerationSourceDocument:
    path = evidence_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return ImportedGenerationSourceDocument(
        kind="historical",
        relative_path=relative_path,
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        text=text,
    )


def _attribution(source, document):
    return (
        ImportedGenerationEvaluationSourceAttribution(
            evaluation_source_sha256=source.source_sha256,
            document_sha256s=(document.sha256,),
        ),
    )


def _legacy_source(tmp_path, *, strip_binding: bool = True):
    """Materialize a remote fixture then remove its new decision binding."""

    _, provider, request, binding, paid_preview, committer = _runtime(
        tmp_path, status_events=(VideoTaskState.SUCCEEDED,)
    )
    assert binding is not None
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(attempt_id=ATTEMPT_ID, request=request, execution_binding=binding)
    service.submit_once(
        attempt_id=ATTEMPT_ID,
        paid_preview=paid_preview,
        reservation_id="p8-video-reservation-1",
    )
    service.refresh_once(attempt_id=ATTEMPT_ID)
    service.fetch_once(attempt_id=ATTEMPT_ID)

    manifest = committer._read_manifest()
    attempt = next(item for item in manifest.attempts if item.attempt_id == ATTEMPT_ID)
    assert attempt.video_generation_state is not None
    # This mimics an earlier successful remote receipt that predates the
    # decision-binding record; it does not add any lifecycle fields.
    if strip_binding:
        old_state = attempt.video_generation_state.model_copy(
            update={"execution_binding": None, "generation_experiences": ()}
        )
        old_attempt = attempt.model_copy(update={"video_generation_state": old_state})
        old_manifest = manifest.model_copy(
            update={
                "attempts": tuple(
                    old_attempt if item.attempt_id == ATTEMPT_ID else item
                    for item in manifest.attempts
                )
            }
        )
        (tmp_path / "state/manifest.json").write_bytes(_canonical_json_bytes(old_manifest))
    loaded = load_production_project(tmp_path / "project.yaml")
    state = next(
        item for item in loaded.manifest.attempts if item.attempt_id == ATTEMPT_ID
    ).video_generation_state
    assert state is not None
    if strip_binding:
        assert state.execution_binding is None

    candidate = binding.inputs.candidates[0]
    projection = binding.projection
    fetch = committer._reopen_video_fetch(state.fetch_receipt)
    policy = loaded.qa_policy
    source = GenerationEvaluationSource(
        request_hash=request.request_input_hash,
        artifact_sha256=fetch.artifact_sha256,
        rubric_hash=candidate.recipe.rubric_hash,
        qa_policy_content_hash=policy.content_hash,
        evaluator=policy.semantic_authorities[0],
        proof="technical",
        observations=(
            GenerationObservation(
                requirement_id=candidate.recipe.expressions[0].requirement_id,
                verdict="FAIL",
                observation="Historical exact-byte human and analyzer review retained.",
            ),
        ),
    )
    facts_hash = canonical_sha256(
        projection.requirement.model_dump(
            mode="json", exclude={"requirement_id", "requirement_hash"}
        )
    )
    experience = GenerationExperience(
        projection=projection,
        candidate=candidate,
        evidence=(
            AttemptEvidence(
                task_id=binding.inputs.limits.task_id,
                shot_id=projection.target_shot_id,
                attempt_id=ATTEMPT_ID,
                recipe_scope_hash=candidate.scope_hash,
                facts_hash=facts_hash,
                rubric_hash=candidate.recipe.rubric_hash,
                request_hash=request.request_input_hash,
                artifact_sha256=fetch.artifact_sha256,
                outcome="media",
                findings=source.project_findings(),
            ),
        ),
        evaluation_sources=(source,),
    )
    return loaded, experience, policy, source


def test_prepares_and_reopens_a_strict_legacy_remote_snapshot(tmp_path):
    loaded, experience, policy, source = _legacy_source(tmp_path)
    source_payload = source.model_dump(mode="json")
    assert source.schema_version == "generation-evaluation/1"
    assert source.source_sha256 == "19899e8635031be80b9bae82f5e3f69b28a07bc6b7a1cacc8113dc711fe83a31"
    assert experience.evidence[0].evidence_hash == "fcb33d9b3f154c5162f50bc84f9c3a9a700186b5e4f151235e1c4b302dfe565e"
    assert canonical_sha256(experience.model_dump(mode="json")) == "3eed2e3fb476f8a8652e72af33d6233738d83c9c1ea50539ce6a5b7479c7a402"
    assert "analysis_evidence" not in source_payload
    assert GenerationEvaluationSource.model_validate(source_payload).model_dump(mode="json") == source_payload
    expected = hashlib.sha256((tmp_path / "state/manifest.json").read_bytes()).hexdigest()
    evidence_root = tmp_path / "evidence"
    document = _document(evidence_root, "Human review: hand is distorted and gap is unreadable.")
    receipt, media = prepare_generation_history_import(
        tmp_path,
        expected_source_manifest_sha256=expected,
        import_id="legacy-s01-attempt",
        source_attempt_id=ATTEMPT_ID,
        experience=experience,
        evaluation_policy=policy,
        source_documents=(document,),
        evaluation_source_attributions=_attribution(source, document),
        evidence_root=evidence_root,
        actor=ActorIdentity(actor_id="codex-history-import", actor_kind="codex"),
    )
    assert receipt.source_manifest == loaded.manifest
    assert receipt.source_request.request_input_hash == experience.evidence[0].request_hash
    assert receipt.source_fetch.artifact_sha256 == experience.evidence[0].artifact_sha256
    assert receipt.source_status.state is VideoTaskState.SUCCEEDED
    assert hashlib.sha256(media).hexdigest() == receipt.source_fetch.artifact_sha256
    assert receipt.evaluation_policy == policy
    target = tmp_path / "copied-target"
    receipt_path = target / f"state/video-generation/imported-experiences/{receipt.content_hash}.json"
    media_path = target / f"state/video-generation/imported-media/{receipt.source_fetch.artifact_sha256}.mp4"
    receipt_path.parent.mkdir(parents=True)
    media_path.parent.mkdir(parents=True)
    receipt_bytes = _canonical_json_bytes(receipt)
    receipt_path.write_bytes(receipt_bytes)
    media_path.write_bytes(media)
    pointer = ImportedGenerationExperienceReceiptPointer(
        path=Path(f"state/video-generation/imported-experiences/{receipt.content_hash}.json"),
        content_hash=receipt.content_hash,
        request_fingerprint=receipt.source_request.request_input_hash,
        file_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
    )
    assert load_imported_generation_experience(target, pointer) == receipt


def test_rejects_tampered_document_and_manifest_pin(tmp_path):
    _, experience, policy, source = _legacy_source(tmp_path)
    expected = hashlib.sha256((tmp_path / "state/manifest.json").read_bytes()).hexdigest()
    evidence_root = tmp_path / "evidence"
    document = _document(evidence_root, "Human review: hand is distorted and gap is unreadable.")
    with pytest.raises(ValueError, match="document hash"):
        ImportedGenerationSourceDocument(
            kind="historical", relative_path=Path("observations/legacy-gate.md"),
            sha256=document.sha256, text="tampered"
        )
    with pytest.raises(ValueError, match="expected exact raw snapshot"):
        prepare_generation_history_import(
            tmp_path,
            expected_source_manifest_sha256="f" * 64,
            import_id="legacy-s01-attempt",
            source_attempt_id=ATTEMPT_ID,
            experience=experience,
            evaluation_policy=policy,
            source_documents=(document,),
            evaluation_source_attributions=_attribution(source, document),
            evidence_root=evidence_root,
            actor=ActorIdentity(actor_id="codex-history-import", actor_kind="codex"),
        )
    assert expected


def test_rejects_import_of_a_decision_bound_source(tmp_path):
    _, experience, policy, source = _legacy_source(tmp_path, strip_binding=False)
    manifest_path = tmp_path / "state/manifest.json"
    evidence_root = tmp_path / "evidence"
    document = _document(evidence_root, "Human review: hand is distorted and gap is unreadable.")
    manifest = load_production_project(tmp_path / "project.yaml").manifest
    attempt = next(item for item in manifest.attempts if item.attempt_id == ATTEMPT_ID)
    assert attempt.video_generation_state is not None and attempt.video_generation_state.execution_binding is not None
    with pytest.raises(ValueError, match="decision"):
        prepare_generation_history_import(
            tmp_path,
            expected_source_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            import_id="legacy-s01-attempt",
            source_attempt_id=ATTEMPT_ID,
            experience=experience,
            evaluation_policy=policy,
            source_documents=(document,),
            evaluation_source_attributions=_attribution(source, document),
            evidence_root=evidence_root,
            actor=ActorIdentity(actor_id="codex-history-import", actor_kind="codex"),
        )


def test_rejects_missing_tampered_escaped_and_self_provenance_documents(tmp_path):
    _, experience, policy, source = _legacy_source(tmp_path)
    expected = hashlib.sha256((tmp_path / "state/manifest.json").read_bytes()).hexdigest()
    evidence_root = tmp_path / "evidence"
    document = _document(evidence_root, "Human review: hand is distorted and gap is unreadable.")
    arguments = dict(
        expected_source_manifest_sha256=expected,
        import_id="legacy-s01-attempt",
        source_attempt_id=ATTEMPT_ID,
        experience=experience,
        evaluation_policy=policy,
        actor=ActorIdentity(actor_id="codex-history-import", actor_kind="codex"),
        evidence_root=evidence_root,
    )
    (evidence_root / document.relative_path).write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        prepare_generation_history_import(
            tmp_path, source_documents=(document,),
            evaluation_source_attributions=_attribution(source, document), **arguments
        )
    missing = document.model_copy(update={"relative_path": Path("observations/missing.md")})
    with pytest.raises(ValueError):
        prepare_generation_history_import(
            tmp_path, source_documents=(missing,),
            evaluation_source_attributions=_attribution(source, missing), **arguments
        )
    with pytest.raises(ValueError, match="relative and contained"):
        ImportedGenerationSourceDocument(
            kind="historical", relative_path=Path("../escape.md"),
            sha256=document.sha256, text=document.text,
        )
    own = _document(evidence_root, source.model_dump_json(), relative_path=Path("observations/evaluator.json"))
    with pytest.raises(ValueError, match="own sole"):
        prepare_generation_history_import(
            tmp_path, source_documents=(own,),
            evaluation_source_attributions=_attribution(source, own), **arguments
        )
    pretty = _document(
        evidence_root,
        json.dumps(source.model_dump(mode="json"), ensure_ascii=False, indent=2),
        relative_path=Path("observations/evaluator-pretty.json"),
    )
    with pytest.raises(ValueError, match="own sole"):
        prepare_generation_history_import(
            tmp_path, source_documents=(pretty,),
            evaluation_source_attributions=_attribution(source, pretty), **arguments
        )


def test_rejects_new_analysis_bridge_and_unbound_intervention_claims(tmp_path):
    _, experience, policy, source = _legacy_source(tmp_path)
    expected = hashlib.sha256((tmp_path / "state/manifest.json").read_bytes()).hexdigest()
    evidence_root = tmp_path / "evidence"
    document = _document(evidence_root, "Human review: hand is distorted and gap is unreadable.")
    arguments = dict(
        expected_source_manifest_sha256=expected,
        import_id="legacy-s01-attempt",
        source_attempt_id=ATTEMPT_ID,
        evaluation_policy=policy,
        source_documents=(document,),
        evidence_root=evidence_root,
        actor=ActorIdentity(actor_id="codex-history-import", actor_kind="codex"),
    )
    changed = experience.model_copy(update={"evidence": (
        experience.evidence[0].model_copy(update={"actual_delta": ("seed",)}),
    )})
    with pytest.raises(ValueError, match="controlled intervention"):
        prepare_generation_history_import(
            tmp_path, experience=changed,
            evaluation_source_attributions=_attribution(source, document), **arguments
        )
    from ai_video.production.generation_evaluation import GenerationAnalysisEvidence

    analysis = GenerationAnalysisEvidence(
        artifact_sha256=source.artifact_sha256,
        size_bytes=1,
        response_json=json.dumps({"structuredContent": {
            "video_path": "offline.mp4", "analysis_summary": {},
            "probe": {"file": {"size_bytes": 1}},
        }}),
    )
    bridged = source.model_copy(update={"analysis_evidence": analysis})
    bridged_experience = experience.model_copy(update={
        "evaluation_sources": (bridged,),
        "evidence": (experience.evidence[0].model_copy(
            update={"findings": bridged.project_findings()}),),
    })
    with pytest.raises(ValueError, match="analysis bridge"):
        prepare_generation_history_import(
            tmp_path, experience=bridged_experience,
            evaluation_source_attributions=_attribution(bridged, document), **arguments
        )
