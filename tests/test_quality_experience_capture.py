from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import EvidenceStrength, ToolIdentity
from ai_video.production.project import (
    load_production_project,
)
from ai_video.production._video_project_reader import (
    load_generated_shot_continuity_evidence,
)
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.review import (
    ContinuityHumanFallbackEvidence,
    GeneratedShotContinuityEvidence,
)
from ai_video.production.video_generation import VideoGenerationService
from ai_video.quality_intelligence.capture import (
    CaptureErrorCode,
    PostQaAnalyzerDocument,
    PostQaHumanReviewDocument,
    PostQaHumanReviewMetadata,
    PostQaQ0CaptureRequest,
    QualityExperienceCaptureError,
    capture_post_qa_quality_experience,
)
from ai_video.quality_intelligence._capture_p6 import reopen_p6_pointers
from ai_video.quality_intelligence.models import (
    AnalyzerBinding,
    AnalyzerEvidenceItem,
    AnalyzerMeasurements,
    AttemptKind,
    BooleanAnalyzerMeasurement,
    BoundedFreeText,
    CountAnalyzerMeasurement,
    EvidenceHex64,
    EvidenceState,
    EvidenceString,
    EvidenceTimestamp,
    InterventionBinding,
    KnownBooleanMeasurement,
    KnownCountMeasurement,
    KnownRatioMeasurement,
    NamedParameters,
    PlanningBinding,
    RatioAnalyzerMeasurement,
    RubricItem,
    RubricItems,
)
from ai_video.quality_intelligence.store import QualityExperienceStore
from ai_video.quality_intelligence.store import QualityExperienceConflict
from production_project_factory import make_p8_video_candidate_preparer
from test_production_generated_video_e2e import (
    ATTEMPT_ID,
    CONTINUITY_EVALUATOR,
    _CountingDurableContinuityReviewer,
    _reach_fetch,
)
from test_production_repair import make_manifest_25_failed_layout_review_fixture


HASHES = tuple(f"{value:02x}" * 32 for value in range(1, 30))


def _not_applicable_string(reason: str) -> EvidenceString:
    return EvidenceString(state=EvidenceState.NOT_APPLICABLE, reason=reason)


def _not_applicable_hex(reason: str) -> EvidenceHex64:
    return EvidenceHex64(state=EvidenceState.NOT_APPLICABLE, reason=reason)


def _analyzer(asset_id: str, continuity_score: float, artifact_sha256: str):
    source = "analysis/existing-video-analysis.json"
    measurements = AnalyzerMeasurements(
        parameters=(
            BooleanAnalyzerMeasurement(
                key="audio_integrity",
                value=KnownBooleanMeasurement(
                    state="known",
                    value=True,
                    source_document=source,
                    source_span="measurements.audio_integrity",
                ),
            ),
            RatioAnalyzerMeasurement(
                key="black_ratio",
                value=KnownRatioMeasurement(
                    state="known",
                    value=0.0,
                    source_document=source,
                    source_span="measurements.black_ratio",
                ),
            ),
            RatioAnalyzerMeasurement(
                key="continuity_score",
                value=KnownRatioMeasurement(
                    state="known",
                    value=continuity_score,
                    source_document=source,
                    source_span="measurements.continuity_score",
                ),
            ),
            RatioAnalyzerMeasurement(
                key="detail_score",
                value=KnownRatioMeasurement(
                    state="known",
                    value=0.8,
                    source_document=source,
                    source_span="measurements.detail_score",
                ),
            ),
            RatioAnalyzerMeasurement(
                key="freeze_ratio",
                value=KnownRatioMeasurement(
                    state="known",
                    value=0.0,
                    source_document=source,
                    source_span="measurements.freeze_ratio",
                ),
            ),
            CountAnalyzerMeasurement(
                key="scene_change_count",
                value=KnownCountMeasurement(
                    state="known",
                    value=0,
                    source_document=source,
                    source_span="measurements.scene_change_count",
                ),
            ),
        )
    )
    measurements_hash = canonical_sha256(measurements.model_dump(mode="json"))
    span_hash = canonical_sha256(
        {
            "domain": "ai-video.q0.analyzer-span/v1",
            "artifact_sha256": artifact_sha256,
            "sources": tuple(
                (item.value.source_document, item.value.source_span)
                for item in measurements.parameters
            ),
        }
    )
    evidence_id = "existing-video-analysis"
    evidence_hash = canonical_sha256(
        {
            "domain": "ai-video.q0.analyzer-evidence/v1",
            "evidence_id": evidence_id,
            "tool_name": "video_analysis",
            "tool_version": "1.0.0",
            "measurement_contract_version": "q0_v1",
            "subject_id": asset_id,
            "artifact_sha256": artifact_sha256,
            "span_hash": span_hash,
            "measurements_hash": measurements_hash,
        }
    )
    return AnalyzerBinding(
        state="known",
        evidence=(
            AnalyzerEvidenceItem(
                evidence_id=evidence_id,
                evidence_hash=evidence_hash,
                tool_name="video_analysis",
                tool_version="1.0.0",
                measurement_contract_version="q0_v1",
                subject_id=asset_id,
                span_hash=span_hash,
                measurements_hash=measurements_hash,
                measurements=measurements,
            ),
        ),
    )


def _capture_request(
    project_root: Path,
    pilot_root: Path,
    *,
    continuity_score: float,
    human_review: PostQaHumanReviewMetadata | None = None,
) -> PostQaQ0CaptureRequest:
    bundle = load_production_project(project_root / "project.yaml")
    attempt = next(item for item in bundle.manifest.attempts if item.attempt_id == ATTEMPT_ID)
    state = attempt.video_generation_state
    assert state is not None and state.continuity_evaluation is not None
    request = ProductionStateCommitter(project_root)._reopen_video_request(state.request)
    analyzer = _analyzer(
        request.output_asset_id,
        continuity_score,
        state.continuity_evaluation.probe.artifact_sha256,
    )
    analyzer_path = project_root / "analysis/existing-video-analysis.json"
    analyzer_path.parent.mkdir(parents=True, exist_ok=True)
    analyzer_bytes = json.dumps(
        analyzer.evidence[0].model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    analyzer_path.write_bytes(analyzer_bytes)
    human_document = None
    if human_review is not None:
        evaluation = state.continuity_evaluation
        evidence = load_generated_shot_continuity_evidence(
            project_root, evaluation.evidence
        )
        raw_measurements = evidence.raw_measurements
        fallback = getattr(raw_measurements, "fallback_evidence", None)
        review_path = project_root / "reviews/q0-human.json"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_bytes = json.dumps(
            human_review.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        review_path.write_bytes(review_bytes)
        human_document = PostQaHumanReviewDocument(
            relative_path="reviews/q0-human.json",
            file_sha256=hashlib.sha256(review_bytes).hexdigest(),
            evaluation_fingerprint=evidence.evaluation_fingerprint,
            human_fallback_hash=(
                fallback.content_hash if fallback is not None else HASHES[24]
            ),
        )
    return PostQaQ0CaptureRequest(
        project_root=project_root,
        attempt_id=ATTEMPT_ID,
        pilot_dataset_root=pilot_root,
        experiment_id="continuity-capture-v1",
        pilot_id="offline-fixture",
        captured_at="2026-08-22T12:00:00Z",
        repository_commit="d9dcdbe572050fbacb28ca5147c84b996445f8bf",
        purpose=BoundedFreeText(value="capture exact post-QA continuity evidence"),
        hypothesis=BoundedFreeText(value="durable evidence projects without rerunning QA"),
        capture_actor="codex",
        authorization_boundary="local_offline_task",
        attempt_sequence=1,
        attempt_kind=AttemptKind.INITIAL,
        analyzer=analyzer,
        analyzer_documents=(
            PostQaAnalyzerDocument(
                relative_path="analysis/existing-video-analysis.json",
                file_sha256=hashlib.sha256(analyzer_bytes).hexdigest(),
                artifact_sha256=(
                    state.continuity_evaluation.probe.artifact_sha256
                ),
                evidence_id=analyzer.evidence[0].evidence_id,
            ),
        ),
        human_review=human_review,
        human_review_document=human_document,
        intervention=InterventionBinding(
            kind="none",
            failure_taxonomy=_not_applicable_string("no_intervention"),
            changed_variables=NamedParameters(),
            unchanged_controls=NamedParameters(),
            confounders=(),
            rationale=BoundedFreeText(value="no intervention applied"),
        ),
        allowed_conclusions=(
            BoundedFreeText(
                value="this exact generated Shot continuity verdict is represented"
            ),
        ),
        forbidden_extrapolations=(
            BoundedFreeText(
                value="does not establish overall visual quality or Provider ranking"
            ),
            BoundedFreeText(
                value="does not establish Final Acceptance or training readiness"
            ),
        ),
    )


def _check(status: str) -> dict[str, object]:
    return {
        "status": status,
        "expected": "expected",
        "observed": "observed",
        "confidence_milli": 1000,
        "rationale": "exact fixture review",
    }


class _TrackedFallbackReviewer(_CountingDurableContinuityReviewer):
    def __init__(self, *, reject_motion: bool = False) -> None:
        super().__init__()
        self.reject_motion = reject_motion

    def __call__(self, held_fd, request, measured, qa_policy_content_hash):
        del held_fd
        self.calls += 1
        assert self.intent is not None
        binding = request.continuity_binding
        original = request.activation_scope.request
        assert binding is not None
        values = {
            "source_shot_id": binding.terminal_frame.source_shot_id,
            "target_shot_id": original.target_shot_id,
            "target_shot_content_hash": original.target_shot_content_hash,
            "resolved_generation_hash": request.resolved_generation_hash,
            "artifact_sha256": measured.artifact_sha256,
            "continuity_constraints_hash": binding.constraints.content_hash,
            "qa_policy_content_hash": qa_policy_content_hash,
            "evaluator": CONTINUITY_EVALUATOR,
            "strength": EvidenceStrength.HUMAN,
            "coverage_complete": True,
            "identity_match": True,
            "camera_axis_match": True,
            "framing_match": True,
            "motion_direction_match": not self.reject_motion,
            "entrance_state_match": True,
            "exit_state_match": True,
            "unexpected_reentry": False,
            "rationale": "Human fallback reviewed every exact continuity dimension.",
        }
        fallback = ContinuityHumanFallbackEvidence.from_generated(
            GeneratedShotContinuityEvidence.create(**values)
        )
        indices = (0, measured.frame_count - 1)
        raw = {
            "measurement_contract_version": "tracked-continuity-evaluator/1",
            "sampler": {"name": "fixture-frame-sampler", "version": "1"},
            "evaluator_profile_content_hash": "f" * 64,
            "artifact_sha256": measured.artifact_sha256,
            "sample_width": measured.width,
            "sample_height": measured.height,
            "sampled_frames": tuple(
                {
                    "frame_index": index,
                    "frame_sha256": canonical_sha256(
                        {"domain": "fixture-frame", "index": index}
                    ),
                }
                for index in indices
            ),
            "subject_track": tuple(
                {"frame_index": index, "state": "ambiguous"}
                for index in indices
            ),
            "fallback_evidence": fallback,
            "identity": _check("match"),
            "camera_axis": _check("match"),
            "framing": _check("match"),
            "motion_direction": _check(
                "mismatch" if self.reject_motion else "match"
            ),
            "entrance_state": _check("match"),
            "exit_state": _check("match"),
            "unexpected_reentry": _check("match"),
        }
        return GeneratedShotContinuityEvidence.create(
            **values,
            raw_measurements=raw,
        )


def _human_metadata(*, reject_motion: bool = False) -> PostQaHumanReviewMetadata:
    verdicts = {
        "camera_axis": "pass",
        "entrance_state": "pass",
        "exit_state": "pass",
        "framing": "pass",
        "identity": "pass",
        "motion_direction": "fail" if reject_motion else "pass",
        "unexpected_reentry": "pass",
    }
    return PostQaHumanReviewMetadata(
        reviewer_id=EvidenceString(
            state=EvidenceState.KNOWN,
            value="reviewer-pseudonym-7",
            source_document="reviews/q0-human.json",
            source_span="reviewer.id",
        ),
        reviewer_kind=EvidenceString(
            state=EvidenceState.KNOWN,
            value="human",
            source_document="reviews/q0-human.json",
            source_span="reviewer.kind",
        ),
        rubric_id="continuity-fallback-v1",
        rubric_version="1",
        rubric_hash=HASHES[22],
        watched_at=EvidenceTimestamp(
            state="known",
            value="2026-08-22T11:59:00Z",
            source_document="reviews/q0-human.json",
            source_span="watched_at",
        ),
        items=RubricItems(
            items=tuple(
                RubricItem(item_id=key, verdict=value)
                for key, value in sorted(verdicts.items())
            )
        ),
    )


def test_capture_continuity_pass_reopens_and_writes_score_one(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    inputs, provider, _, committer = _reach_fetch(project_root, continuity=True)
    service = VideoGenerationService(committer=committer, provider=provider)
    service.fetch_once(attempt_id=ATTEMPT_ID)
    VideoGenerationService(
        committer=ProductionStateCommitter(
            project_root,
            video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        ),
        provider=provider,
    ).fetch_and_activate(
        attempt_id=ATTEMPT_ID,
        continuity_reviewer=_CountingDurableContinuityReviewer(),
    )
    pilot_root = tmp_path / "pilot"

    pointer = capture_post_qa_quality_experience(
        _capture_request(project_root, pilot_root, continuity_score=1.0)
    )
    record = QualityExperienceStore(pilot_root).load_record(pointer)
    score = next(
        item.value.value
        for item in record.analyzer.evidence[0].measurements.parameters
        if item.key == "continuity_score"
    )

    assert score == 1.0
    assert record.schema_version == "1.1"
    assert record.continuity_evidence.evidence.kind == "continuity_evidence"
    assert record.outcome_boundary.p6_state == "not_present"
    assert record.outcome_boundary.p6_observations == ()
    assert record.identity.attempt_id == ATTEMPT_ID
    assert record.routing.selected_capability_id == record.provider.capability_id
    assert record.planning.planning_request_hash.state is EvidenceState.NOT_APPLICABLE
    assert record.provider.adapter_compiler_id.state is EvidenceState.NOT_APPLICABLE
    assert record.inputs.items[0].creation_receipt_hash.state is EvidenceState.NOT_APPLICABLE
    assert record.artifact_evidence.file_sha256 == hashlib.sha256(
        (project_root / record.artifact_evidence.relative_path).read_bytes()
    ).hexdigest()


def test_capture_p6_projection_marks_historical_repair_outcome_stale_and_reopens(
    tmp_path: Path,
) -> None:
    fixture = make_manifest_25_failed_layout_review_fixture(tmp_path)
    before = fixture.load_manifest()
    approved = fixture.committer.record_approved_repair_receipt(
        fixture.repair_request,
        fixture.approval,
        expected_manifest_revision=before.manifest_revision,
        attempt_id="q0-p6-repair-approval",
    )
    approved_pointer = approved.active_approved_repair
    assert approved_pointer is not None
    fixture.committer.commit(fixture.state_commit_request(approved_pointer))
    fixture.rerender()
    fresh_review = fixture.run_fresh_layout_review()
    outcome = fixture.outcome(approved_pointer, fresh_review)
    closed = fixture.committer.record_repair_outcome(
        outcome,
        expected_manifest_revision=fixture.load_manifest().manifest_revision,
        attempt_id="q0-p6-repair-outcome",
    )

    pointers = reopen_p6_pointers(tmp_path, closed)
    repair_pointer = next(
        item for item in pointers if item.kind == "repair_outcome"
    )

    assert repair_pointer.freshness == "stale"
    assert any(
        item.kind == "review_receipt" and item.freshness == "fresh"
        for item in pointers
    )

    (tmp_path / repair_pointer.relative_path).write_bytes(b"{}")
    with pytest.raises(ValidationError):
        reopen_p6_pointers(tmp_path, closed)


def _checkpoint(
    project_root: Path,
    reviewer: _CountingDurableContinuityReviewer,
    *,
    activate: bool,
):
    inputs, provider, _, committer = _reach_fetch(project_root, continuity=True)
    VideoGenerationService(committer=committer, provider=provider).fetch_once(
        attempt_id=ATTEMPT_ID
    )
    service = VideoGenerationService(
        committer=ProductionStateCommitter(
            project_root,
            video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        ),
        provider=provider,
    )
    if activate:
        service.fetch_and_activate(
            attempt_id=ATTEMPT_ID,
            continuity_reviewer=reviewer,
        )
    else:
        with pytest.raises(AiVideoError):
            service.fetch_and_activate(
                attempt_id=ATTEMPT_ID,
                continuity_reviewer=reviewer,
            )
    return provider


def _continuity_score(record) -> float:
    return next(
        item.value.value
        for item in record.analyzer.evidence[0].measurements.parameters
        if item.key == "continuity_score"
    )


def test_capture_automatic_mismatch_writes_zero_and_not_reviewed(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    _checkpoint(
        project_root,
        _CountingDurableContinuityReviewer(identity_match=False),
        activate=False,
    )
    pilot_root = tmp_path / "pilot"

    pointer = capture_post_qa_quality_experience(
        _capture_request(project_root, pilot_root, continuity_score=0.0)
    )
    record = QualityExperienceStore(pilot_root).load_record(pointer)

    assert _continuity_score(record) == 0.0
    assert record.human_review.status.value == "NOT_REVIEWED"
    assert record.outcome.terminal_boundary == "fetched"


def test_capture_complete_human_fallback_pass_preserves_hash_and_go(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    _checkpoint(
        project_root,
        _TrackedFallbackReviewer(),
        activate=True,
    )
    pilot_root = tmp_path / "pilot"

    pointer = capture_post_qa_quality_experience(
        _capture_request(
            project_root,
            pilot_root,
            continuity_score=1.0,
            human_review=_human_metadata(),
        )
    )
    record = QualityExperienceStore(pilot_root).load_record(pointer)

    assert record.human_review.status.value == "GO"
    assert record.continuity_evidence is not None
    assert record.continuity_evidence.human_fallback_hash.state is EvidenceState.KNOWN
    assert record.continuity_evidence.evaluation_fingerprint
    assert record.outcome_boundary.p6_state == "not_present"
    assert _continuity_score(record) == 1.0


def test_capture_human_rejection_is_no_go_and_automatic_cannot_override(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    _checkpoint(
        project_root,
        _TrackedFallbackReviewer(reject_motion=True),
        activate=False,
    )
    pilot_root = tmp_path / "pilot"

    pointer = capture_post_qa_quality_experience(
        _capture_request(
            project_root,
            pilot_root,
            continuity_score=0.0,
            human_review=_human_metadata(reject_motion=True),
        )
    )
    record = QualityExperienceStore(pilot_root).load_record(pointer)

    assert record.human_review.status.value == "NO_GO"
    assert _continuity_score(record) == 0.0


def test_capture_automatic_mismatch_rejects_unbound_later_human_input(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    _checkpoint(
        project_root,
        _CountingDurableContinuityReviewer(identity_match=False),
        activate=False,
    )
    pilot_root = tmp_path / "pilot"

    with pytest.raises(QualityExperienceCaptureError) as rejected:
        capture_post_qa_quality_experience(
            _capture_request(
                project_root,
                pilot_root,
                continuity_score=0.0,
                human_review=_human_metadata(),
            )
        )

    assert rejected.value.code == CaptureErrorCode.BINDING_INVALID.value
    assert not pilot_root.exists()


@pytest.mark.parametrize("tamper", ("rubric", "watched_at", "reviewer_source"))
def test_capture_human_metadata_requires_exact_document_binding(
    tmp_path: Path,
    tamper: str,
) -> None:
    project_root = tmp_path / "project"
    _checkpoint(project_root, _TrackedFallbackReviewer(), activate=True)
    pilot_root = tmp_path / "pilot"
    request = _capture_request(
        project_root,
        pilot_root,
        continuity_score=1.0,
        human_review=_human_metadata(),
    )
    assert request.human_review is not None
    metadata = request.human_review
    if tamper == "rubric":
        metadata = metadata.model_copy(update={"rubric_hash": HASHES[23]})
    elif tamper == "watched_at":
        metadata = metadata.model_copy(
            update={
                "watched_at": metadata.watched_at.model_copy(
                    update={"value": "2026-08-22T11:58:00Z"}
                )
            }
        )
    else:
        metadata = metadata.model_copy(
            update={
                "reviewer_id": metadata.reviewer_id.model_copy(
                    update={"source_span": "reviewer.alias"}
                )
            }
        )
    request = request.model_copy(update={"human_review": metadata})

    with pytest.raises(QualityExperienceCaptureError):
        capture_post_qa_quality_experience(request)

    assert not pilot_root.exists()


@pytest.mark.parametrize(
    "tamper", ("missing", "document_bytes", "fingerprint", "fallback_hash")
)
def test_capture_human_review_document_pointer_is_exact(
    tmp_path: Path,
    tamper: str,
) -> None:
    project_root = tmp_path / "project"
    _checkpoint(project_root, _TrackedFallbackReviewer(), activate=True)
    pilot_root = tmp_path / "pilot"
    request = _capture_request(
        project_root,
        pilot_root,
        continuity_score=1.0,
        human_review=_human_metadata(),
    )
    assert request.human_review_document is not None
    document = request.human_review_document
    review_path = project_root / document.relative_path
    if tamper == "missing":
        review_path.unlink()
    elif tamper == "document_bytes":
        review_path.write_bytes(b"{}")
    elif tamper == "fingerprint":
        request = request.model_copy(
            update={
                "human_review_document": document.model_copy(
                    update={"evaluation_fingerprint": HASHES[25]}
                )
            }
        )
    else:
        request = request.model_copy(
            update={
                "human_review_document": document.model_copy(
                    update={"human_fallback_hash": HASHES[26]}
                )
            }
        )

    with pytest.raises(QualityExperienceCaptureError) as rejected:
        capture_post_qa_quality_experience(request)

    assert rejected.value.code == CaptureErrorCode.BINDING_INVALID.value
    assert not pilot_root.exists()


def test_capture_not_evaluated_and_intent_only_are_zero_write(tmp_path: Path) -> None:
    not_evaluated_root = tmp_path / "not-evaluated"
    _checkpoint(
        not_evaluated_root,
        _CountingDurableContinuityReviewer(coverage_complete=False),
        activate=False,
    )
    pilot_root = tmp_path / "pilot"
    request = _capture_request(
        not_evaluated_root, pilot_root, continuity_score=0.0
    )

    with pytest.raises(QualityExperienceCaptureError) as not_ready:
        capture_post_qa_quality_experience(request)
    assert not_ready.value.code == CaptureErrorCode.NOT_READY.value
    assert not pilot_root.exists()

    intent_root = tmp_path / "intent-only"
    inputs, provider, _, committer = _reach_fetch(intent_root, continuity=True)
    del inputs
    service = VideoGenerationService(committer=committer, provider=provider)
    service.fetch_once(attempt_id=ATTEMPT_ID)
    with pytest.raises(AiVideoError):
        service.fetch_and_activate(
            attempt_id=ATTEMPT_ID,
            continuity_reviewer=_CountingDurableContinuityReviewer(
                fail_during_evaluation=True
            ),
        )
    bundle = load_production_project(intent_root / "project.yaml")
    state = bundle.manifest.attempts[-1].video_generation_state
    assert state is not None and state.continuity_evaluation is not None
    assert state.continuity_evaluation.phase.value == "intent"
    raw_request = request.model_dump(mode="python")
    raw_request["project_root"] = intent_root
    with pytest.raises(QualityExperienceCaptureError) as intent_not_ready:
        capture_post_qa_quality_experience(
            PostQaQ0CaptureRequest.model_validate(raw_request)
        )
    assert intent_not_ready.value.code == CaptureErrorCode.NOT_READY.value
    assert not pilot_root.exists()


def test_capture_exact_replay_is_same_pointer_and_production_zero_write(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    provider = _checkpoint(
        project_root,
        _CountingDurableContinuityReviewer(),
        activate=True,
    )
    pilot_root = tmp_path / "pilot"
    request = _capture_request(project_root, pilot_root, continuity_score=1.0)
    production_before = tuple(
        sorted(
            (
                path.relative_to(project_root).as_posix(),
                path.stat().st_mtime_ns,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            for path in project_root.rglob("*")
            if path.is_file()
        )
    )
    provider_before = provider.call_counts

    first = capture_post_qa_quality_experience(request)
    second = capture_post_qa_quality_experience(request)

    production_after = tuple(
        sorted(
            (
                path.relative_to(project_root).as_posix(),
                path.stat().st_mtime_ns,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            for path in project_root.rglob("*")
            if path.is_file()
        )
    )
    assert second == first
    assert production_after == production_before
    assert provider.call_counts == provider_before


def test_capture_same_attempt_different_advisory_bytes_conflicts(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    _checkpoint(
        project_root,
        _CountingDurableContinuityReviewer(),
        activate=True,
    )
    pilot_root = tmp_path / "pilot"
    request = _capture_request(project_root, pilot_root, continuity_score=1.0)
    capture_post_qa_quality_experience(request)
    changed = request.model_copy(
        update={"purpose": BoundedFreeText(value="different advisory purpose")}
    )

    with pytest.raises(QualityExperienceConflict):
        capture_post_qa_quality_experience(changed)


def test_capture_request_rejects_caller_runtime_projection_overrides(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    _checkpoint(
        project_root,
        _CountingDurableContinuityReviewer(),
        activate=True,
    )
    request = _capture_request(
        project_root, tmp_path / "pilot", continuity_score=1.0
    )
    payload = request.model_dump(mode="python")
    payload["planning"] = PlanningBinding(
        planning_request_hash=HASHES[0],
        plan_hash=HASHES[1],
        requirement_hash=HASHES[2],
        readiness_request_hash=HASHES[3],
        readiness_result_hash=HASHES[4],
        readiness_state="READY",
        check_reason_codes=("bindings_valid",),
    )

    with pytest.raises(ValidationError):
        PostQaQ0CaptureRequest.model_validate(payload)


@pytest.mark.parametrize(
    "tamper",
    (
        "wrong_attempt",
        "artifact",
        "terminal_frame",
        "profile",
        "evaluation_fingerprint",
        "policy",
        "constraints",
        "target_shot",
    ),
)
def test_capture_stale_or_tampered_runtime_binding_is_zero_write(
    tmp_path: Path,
    tamper: str,
) -> None:
    project_root = tmp_path / "project"
    _checkpoint(
        project_root,
        _CountingDurableContinuityReviewer(),
        activate=True,
    )
    pilot_root = tmp_path / "pilot"
    request = _capture_request(project_root, pilot_root, continuity_score=1.0)
    bundle = load_production_project(project_root / "project.yaml")
    attempt = next(item for item in bundle.manifest.attempts if item.attempt_id == ATTEMPT_ID)
    state = attempt.video_generation_state
    assert state is not None and state.continuity_evaluation is not None

    if tamper == "wrong_attempt":
        request = request.model_copy(update={"attempt_id": "wrong-attempt"})
    elif tamper == "artifact":
        fetch_pointer = state.local_fetch_receipt or state.fetch_receipt
        assert fetch_pointer is not None
        (project_root / fetch_pointer.artifact_path).write_bytes(b"tampered-mp4")
    else:
        selected_path = (
            state.continuity_evaluation.evidence.path
            if tamper == "evaluation_fingerprint"
            else bundle.manifest.active_qa_policy.path
            if tamper == "policy"
            else state.request.path
        )
        payload = json.loads((project_root / selected_path).read_text(encoding="utf-8"))
        if tamper == "terminal_frame":
            payload["continuity_binding"]["terminal_frame"]["extracted_sha256"] = "0" * 64
        elif tamper == "profile":
            payload["provider_profile"]["profile_sha256"] = "0" * 64
        elif tamper == "evaluation_fingerprint":
            payload["evaluation_fingerprint"] = "0" * 64
        elif tamper == "policy":
            payload["content_hash"] = "0" * 64
        elif tamper == "constraints":
            payload["continuity_binding"]["constraints"]["content_hash"] = "0" * 64
        elif tamper == "target_shot":
            payload["continuity_binding"]["target_shot_content_hash"] = "0" * 64
        (project_root / selected_path).write_text(
            json.dumps(payload), encoding="utf-8"
        )

    with pytest.raises(QualityExperienceCaptureError) as rejected:
        capture_post_qa_quality_experience(request)

    assert rejected.value.code in {
        CaptureErrorCode.BINDING_INVALID.value,
        CaptureErrorCode.NOT_READY.value,
    }
    assert not pilot_root.exists()


def test_capture_missing_or_contradictory_analyzer_evidence_is_zero_write(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    _checkpoint(
        project_root,
        _CountingDurableContinuityReviewer(),
        activate=True,
    )
    pilot_root = tmp_path / "pilot"
    complete = _capture_request(project_root, pilot_root, continuity_score=1.0)
    missing = complete.model_copy(
        update={
            "analyzer": AnalyzerBinding(
                state="not_applicable", reason_code="missing_existing_analysis"
            )
        }
    )
    wrong_score = complete.model_copy(
        update={
            "analyzer": _analyzer(
                complete.analyzer.evidence[0].subject_id,
                0.0,
                load_production_project(
                    project_root / "project.yaml"
                ).manifest.attempts[-1].video_generation_state.continuity_evaluation.probe.artifact_sha256,
            )
        }
    )

    for candidate in (missing, wrong_score):
        with pytest.raises(QualityExperienceCaptureError):
            capture_post_qa_quality_experience(candidate)
    assert not pilot_root.exists()


@pytest.mark.parametrize("mutation", ("missing", "tampered"))
def test_capture_analyzer_document_must_strictly_reopen(
    tmp_path: Path,
    mutation: str,
) -> None:
    project_root = tmp_path / "project"
    _checkpoint(
        project_root,
        _CountingDurableContinuityReviewer(),
        activate=True,
    )
    pilot_root = tmp_path / "pilot"
    request = _capture_request(project_root, pilot_root, continuity_score=1.0)
    document = project_root / request.analyzer_documents[0].relative_path
    if mutation == "missing":
        document.unlink()
    else:
        document.write_bytes(b"{}")

    with pytest.raises(QualityExperienceCaptureError) as rejected:
        capture_post_qa_quality_experience(request)

    assert rejected.value.code == CaptureErrorCode.BINDING_INVALID.value
    assert not pilot_root.exists()


@pytest.mark.parametrize(
    "sensitive",
    (
        "[prompt begin] raw prompt",
        "[response begin] raw Provider response",
        "https://signed.example/video?token=secret",
        "api_key=super-secret",
        "/home/reggie/private/file.mp4",
        "reviewer@example.com",
    ),
)
def test_capture_request_privacy_rejection_is_sanitized(sensitive: str) -> None:
    with pytest.raises(ValidationError) as rejected:
        BoundedFreeText(value=sensitive)

    rendered = f"{rejected.value!r} {rejected.value}"
    assert sensitive not in rendered
    assert "super-secret" not in rendered
    assert "/home/reggie" not in rendered


@pytest.mark.parametrize(
    ("field", "sensitive"),
    (
        ("purpose", "[prompt begin] raw prompt"),
        ("purpose", "[response begin] raw Provider response"),
        ("purpose", "https://signed.example/video?token=secret"),
        ("purpose", "api_key=super-secret"),
        ("purpose", "/home/reggie/private/file.mp4"),
        ("capture_actor", "reviewer@example.com"),
    ),
)
def test_complete_capture_request_privacy_error_is_sanitized(
    tmp_path: Path,
    field: str,
    sensitive: str,
) -> None:
    project_root = tmp_path / "project"
    _checkpoint(
        project_root,
        _CountingDurableContinuityReviewer(),
        activate=True,
    )
    request = _capture_request(
        project_root, tmp_path / "pilot", continuity_score=1.0
    )
    payload = request.model_dump(mode="python")
    payload[field] = {"value": sensitive} if field == "purpose" else sensitive

    with pytest.raises(ValidationError) as rejected:
        PostQaQ0CaptureRequest.model_validate(payload)

    rendered = f"{rejected.value!r} {rejected.value}"
    assert sensitive not in rendered
    assert "super-secret" not in rendered
    assert "/home/reggie" not in rendered


def test_production_package_does_not_import_quality_intelligence() -> None:
    production_root = Path(__file__).parents[1] / "src/ai_video/production"
    offenders = tuple(
        path
        for path in production_root.rglob("*.py")
        if "quality_intelligence" in path.read_text(encoding="utf-8")
    )
    assert offenders == ()
