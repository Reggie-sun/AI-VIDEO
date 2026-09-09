"""Real durable lifecycle with scripted MCP/evaluator results, no live analysis."""
import asyncio

import pytest

from ai_video.production.generation_evaluation import GenerationEvaluationSource, GenerationObservation
from ai_video.production.video_generation import VideoGenerationService
from ai_video_mcp.generation_feedback import review_generation_attempt
from test_production_local_video_state import _runtime


class Session:
    def __init__(self, *, fail=False, alter=None):
        self.calls = 0
        self.fail = fail
        self.alter = alter

    async def call_tool(self, name, arguments):
        from pathlib import Path
        from types import SimpleNamespace
        self.calls += 1
        assert name == "video_analyze"
        path = Path(arguments["video_path"])
        payload = {"video_path": str(path), "probe": {"file": {"size_bytes": path.stat().st_size}},
                   "analysis_summary": {"fixture": True}}
        if self.alter:
            self.alter(path)
        return SimpleNamespace(model_dump=lambda **_: {
            "isError": self.fail, "content": [], "structuredContent": payload})


def adjudicate(review):
    return (GenerationEvaluationSource(request_hash=review.request.request_input_hash,
        artifact_sha256=review.analysis.artifact_sha256, rubric_hash=review.recipe.rubric_hash,
        qa_policy_content_hash=review.qa_policy.content_hash,
        analysis_evidence=review.analysis,
        evaluator=review.qa_policy.semantic_authorities[0], proof="technical",
        observations=(GenerationObservation(requirement_id="duration", verdict="FAIL",
            observation="Explicit offline evaluator FAIL, not inferred from MCP success"),)),)


def fetched(tmp_path):
    _, provider, request, binding, committer = _runtime(tmp_path)
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(attempt_id="review", request=request, execution_binding=binding)
    service.submit_local_once(attempt_id="review")
    service.refresh_local_once(attempt_id="review")
    service.fetch_local_once(attempt_id="review")
    return provider, committer


def test_mcp_review_persists_exact_source_and_restart_replay_has_zero_effects(tmp_path):
    from ai_video.production.state_commit import ProductionStateCommitter
    provider, committer = fetched(tmp_path)
    session = Session()
    diagnosis = asyncio.run(review_generation_attempt(committer=committer, attempt_id="review",
        session=session, adjudicate=adjudicate))
    assert diagnosis.failure_classes == ("QUALITY_FAILURE",)
    experience = committer.read_generation_experiences()[0]
    source = experience.evaluation_sources[0]
    assert source.analysis_evidence is not None
    assert experience.evidence[0].findings[0].source_sha256 == source.source_sha256
    revision = committer._read_manifest().manifest_revision
    replay = asyncio.run(review_generation_attempt(committer=ProductionStateCommitter(tmp_path),
        attempt_id="review", session=None, adjudicate=None))
    assert replay == diagnosis
    assert session.calls == 1
    assert committer._read_manifest().manifest_revision == revision
    assert provider.submit_calls == provider.status_calls == provider.fetch_calls == 1


@pytest.mark.parametrize("mode", ["missing", "error", "changed_bytes"])
def test_missing_failed_or_changed_analysis_never_records_pass(tmp_path, mode):
    provider, committer = fetched(tmp_path)
    session = None if mode == "missing" else Session(fail=mode == "error",
        alter=(lambda path: path.write_bytes(b"changed")) if mode == "changed_bytes" else None)
    with pytest.raises(ValueError):
        asyncio.run(review_generation_attempt(committer=committer, attempt_id="review",
            session=session, adjudicate=adjudicate))
    assert committer.read_generation_experiences() == ()
    assert provider.submit_calls == 1


def test_pre_authored_verdict_cannot_be_relabelled_as_current_analysis(tmp_path):
    _, committer = fetched(tmp_path)
    def unbound(review):
        return tuple(s.model_copy(update={"analysis_evidence": None}) for s in adjudicate(review))
    with pytest.raises(ValueError, match="explicitly bind"):
        asyncio.run(review_generation_attempt(committer=committer, attempt_id="review",
            session=Session(), adjudicate=unbound))
    assert committer.read_generation_experiences() == ()


def test_evaluator_cannot_mutate_retained_raw_analysis(tmp_path):
    _, committer = fetched(tmp_path)
    def mutate(review):
        review.analysis.response["structuredContent"]["analysis_summary"]["fixture"] = "tampered"
        return adjudicate(review)
    asyncio.run(review_generation_attempt(committer=committer, attempt_id="review",
        session=Session(), adjudicate=mutate))
    source = committer.read_generation_experiences()[0].evaluation_sources[0]
    assert source.analysis_evidence.response["structuredContent"]["analysis_summary"]["fixture"] is True


def test_imported_analysis_cannot_create_completed_review_without_bridge(tmp_path):
    from ai_video.errors import AiVideoError
    from ai_video.production.generation_feedback import record_attempt_evaluation
    _, committer = fetched(tmp_path)
    review = asyncio.run(review_generation_attempt(committer=committer, attempt_id="review",
        session=Session(), adjudicate=None, analysis_only=True))
    with pytest.raises(AiVideoError, match="bridge recording proof"):
        record_attempt_evaluation(committer=committer, attempt_id="review",
                                  evaluation_sources=adjudicate(review))
    assert committer.read_generation_experiences() == ()


def test_recording_proof_is_one_use_exact_and_cannot_be_copied():
    import copy
    from ai_video.production.generation_evaluation import _seal_analysis_recording
    from test_generation_evaluation import fixture
    _, source, _ = fixture()
    proof = _seal_analysis_recording(attempt_id="a", sources=(source,))
    assert not copy.copy(proof).consume(attempt_id="a", sources=(source,))
    assert not copy.deepcopy(proof).consume(attempt_id="a", sources=(source,))
    assert proof.consume(attempt_id="a", sources=(source,))
    assert not proof.consume(attempt_id="a", sources=(source,))
    changed = _seal_analysis_recording(attempt_id="a", sources=(source,))
    assert not changed.consume(attempt_id="b", sources=(source,))
    assert not changed.consume(attempt_id="a", sources=(source,))


@pytest.mark.parametrize("response", [
    {"structuredContent": {"video_path": "a", "analysis_summary": {}, "probe": None}},
    {"structuredContent": {"video_path": "a", "analysis_summary": {}, "probe": {"file": None}}},
    {"content": None}, {"content": [None]}, {"content": [{"type": "text"}]},
])
def test_malformed_analysis_is_a_validation_error(response):
    import json
    from ai_video.production.generation_evaluation import GenerationAnalysisEvidence
    with pytest.raises(ValueError):
        GenerationAnalysisEvidence(artifact_sha256="a" * 64, size_bytes=1,
                                   response_json=json.dumps(response))


def marked_fetched(tmp_path, monkeypatch, *, measurement_spec=None):
    """Install prospective QA through the normal fixture committer before submit."""
    import production_generation_execution_factory as factory
    from test_requirement_semantics import semantic_rule, marked_policy

    original = factory.fixture_generation_expression
    def expression(output):
        base = original(output)
        payload = {**base.model_dump(mode="python"),
            "semantics": semantic_rule("duration", "governance")["semantics"]}
        if measurement_spec is not None:
            payload.update(measurement_spec=measurement_spec, tolerance=measurement_spec.tolerance_text,
                           measurement=measurement_spec.measurement_text, observable=measurement_spec.event_definition)
        return type(base).model_validate(payload)
    monkeypatch.setattr(factory, "fixture_generation_expression", expression)
    monkeypatch.setattr(factory, "acceptance_policy", lambda rules: marked_policy(
        [r.model_dump(mode="json", exclude={"native_text"}) for r in rules]))
    return fetched(tmp_path)


def marked_adjudicate(review, *, verdict="PASS", unresolved=True):
    item = review.evaluation_items[0]
    return (GenerationEvaluationSource(schema_version="generation-evaluation/2",
        request_hash=review.request.request_input_hash, artifact_sha256=review.analysis.artifact_sha256,
        size_bytes=review.analysis.size_bytes, rubric_hash=review.recipe.rubric_hash,
        qa_policy_content_hash=review.qa_policy.content_hash, qa_policy_snapshot=review.qa_policy,
        analysis_evidence=review.analysis, evaluator=review.qa_policy.semantic_authorities[0], proof="technical",
        observations=(GenerationObservation(requirement_id=item.requirement_id, verdict=verdict,
            observation="Controlled offline fixture answer", evaluation_item_hash=item.evaluation_item_hash,
            question_text=item.question_text, presentation_ref=review.presentation_ref, answer_ref=review.answer_ref),),
        unresolved_quality_observations=([dict(observation_id="cut-discontinuity", original_answer="Visible fixture discontinuity",
            visible_problem="Background discontinuity", quality_basis="Continuity floor needs QA coverage",
            evidence_refs=["fixture/frame"], answer_ref=review.answer_ref)] if unresolved else [])),)


@pytest.mark.parametrize("verdict", ["PASS", "FAIL"])
def test_marked_review_reopens_unresolved_and_preserves_mixed_hard_failure(tmp_path, monkeypatch, verdict):
    from ai_video_mcp.generation_feedback import ControlledPresentationVerifier
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.project import load_production_project

    provider, committer = marked_fetched(tmp_path, monkeypatch)
    qa = load_production_project(tmp_path / "project.yaml").qa_policy
    verifier = ControlledPresentationVerifier(evaluator=qa.semantic_authorities[0], proof="technical",
        adjudicate=lambda review: marked_adjudicate(review, verdict=verdict))
    session = Session()
    result = asyncio.run(review_generation_attempt(committer=committer, attempt_id="review", session=session,
        adjudicate=None, presentation_verifier=verifier))
    assert "RUBRIC_OR_STAGE_ERROR" in result.failure_classes
    assert ("QUALITY_FAILURE" in result.failure_classes) == (verdict == "FAIL")
    original = committer.read_generation_experiences()[0]
    assert len(original.evidence[0].unresolved_quality_refs) == 1
    revision = committer._read_manifest().manifest_revision
    load_production_project(tmp_path / "project.yaml")
    reopened = ProductionStateCommitter(tmp_path)
    assert reopened.read_generation_experiences()[0] == original
    replay = asyncio.run(review_generation_attempt(committer=reopened, attempt_id="review",
        session=None, adjudicate=None))
    assert replay == result
    assert reopened._read_manifest().manifest_revision == revision
    assert provider.submit_calls == provider.fetch_calls == session.calls == 1
    later_verifier = ControlledPresentationVerifier(evaluator=qa.semantic_authorities[0], proof="technical",
        adjudicate=lambda review: marked_adjudicate(review, verdict="PASS", unresolved=False))
    later = asyncio.run(review_generation_attempt(committer=reopened, attempt_id="review", session=session,
        adjudicate=None, presentation_verifier=later_verifier, repair_evidence=True))
    assert "RUBRIC_OR_STAGE_ERROR" in later.failure_classes
    assert ("QUALITY_FAILURE" in later.failure_classes) == (verdict == "FAIL")
    assert len(reopened.read_generation_experiences()) == 2
    replay = asyncio.run(review_generation_attempt(committer=ProductionStateCommitter(tmp_path), attempt_id="review",
                                                   session=None, adjudicate=None))
    assert replay == later


@pytest.mark.parametrize("failure", ["missing_verifier", "wrong_question", "prior_presentation", "human"])
def test_marked_review_rejects_untrusted_or_mismatched_presentation(tmp_path, monkeypatch, failure):
    from ai_video_mcp.generation_feedback import ControlledPresentationVerifier
    from ai_video.production.project import load_production_project

    _, committer = marked_fetched(tmp_path, monkeypatch)
    qa = load_production_project(tmp_path / "project.yaml").qa_policy
    def answer(review):
        source = marked_adjudicate(review)[0]
        if failure == "wrong_question":
            source = source.model_copy(update={"observations": (source.observations[0].model_copy(
                update={"question_text": "A different object's question"}),)})
        elif failure == "prior_presentation":
            source = source.model_copy(update={"observations": (source.observations[0].model_copy(
                update={"presentation_ref": "previous/request"}),)})
        return (source,)
    with pytest.raises(ValueError):
        verifier = None if failure == "missing_verifier" else ControlledPresentationVerifier(
            evaluator=qa.semantic_authorities[0], proof="human" if failure == "human" else "technical", adjudicate=answer)
        asyncio.run(review_generation_attempt(committer=committer, attempt_id="review", session=Session(),
            adjudicate=answer, presentation_verifier=verifier))
    assert committer.read_generation_experiences() == ()


def test_direct_committer_cannot_drop_unresolved_refs_or_reuse_presentation_proof(tmp_path, monkeypatch):
    import copy
    from ai_video.errors import AiVideoError
    from ai_video.production.generation_feedback import record_attempt_evaluation
    from ai_video.production.generation_evaluation import _seal_analysis_recording
    from ai_video_mcp.generation_feedback import ControlledPresentationVerifier

    _, committer = marked_fetched(tmp_path, monkeypatch)
    review = asyncio.run(review_generation_attempt(committer=committer, attempt_id="review", session=Session(),
                                                  adjudicate=None, analysis_only=True))
    verifier = ControlledPresentationVerifier(evaluator=review.qa_policy.semantic_authorities[0], proof="technical",
                                             adjudicate=marked_adjudicate)
    verified = asyncio.run(verifier.present_and_verify(review_input=review, attempt_id="review"))
    with pytest.raises(AiVideoError, match="presentation verifier proof"):
        record_attempt_evaluation(committer=committer, attempt_id="review", evaluation_sources=verified.sources,
            analysis_proof=_seal_analysis_recording(attempt_id="review", sources=verified.sources))
    with pytest.raises(AiVideoError, match="presentation verifier proof"):
        record_attempt_evaluation(committer=committer, attempt_id="review", evaluation_sources=verified.sources,
            presentation_proof=copy.copy(verified.recording_proof),
            analysis_proof=_seal_analysis_recording(attempt_id="review", sources=verified.sources))
    experience = record_attempt_evaluation(committer=committer, attempt_id="review", evaluation_sources=verified.sources,
        presentation_proof=verified.recording_proof,
        analysis_proof=_seal_analysis_recording(attempt_id="review", sources=verified.sources))
    assert experience.evidence[0].unresolved_quality_refs
    bad = experience.model_copy(update={"evidence": (experience.evidence[0].model_copy(update={"unresolved_quality_refs": ()}),)})
    with pytest.raises(AiVideoError, match="experience is invalid"):
        committer.record_generation_experience(attempt_id="review", experience=bad)


def test_orchestrator_record_entry_uses_identical_refs_projection(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator
    from ai_video.production.generation_evaluation import _seal_analysis_recording
    from ai_video_mcp.generation_feedback import ControlledPresentationVerifier

    _, committer = marked_fetched(tmp_path, monkeypatch)
    review = asyncio.run(review_generation_attempt(committer=committer, attempt_id="review", session=Session(),
                                                  adjudicate=None, analysis_only=True))
    verifier = ControlledPresentationVerifier(evaluator=review.qa_policy.semantic_authorities[0], proof="technical",
                                             adjudicate=marked_adjudicate)
    verified = asyncio.run(verifier.present_and_verify(review_input=review, attempt_id="review"))
    _, state = VideoGenerationService(committer=committer, provider=None)._state("review")
    binding = committer._reopen_generation_execution_binding(state.execution_binding)
    prepared = SimpleNamespace(inputs=binding.inputs, decision=binding.decision, execution_binding=binding,
                               compilation=SimpleNamespace(request=review.request.activation_scope.request))
    GenerationFeedbackOrchestrator.record_evaluation(committer=committer, prepared=prepared, attempt_id="review",
        outcome="media", artifact_sha256=review.analysis.artifact_sha256, evaluation_sources=verified.sources,
        presentation_proof=verified.recording_proof,
        analysis_proof=_seal_analysis_recording(attempt_id="review", sources=verified.sources))
    experience = committer.read_generation_experiences()[0]
    assert experience.evidence[0].unresolved_quality_refs == verified.sources[0].unresolved_refs()


@pytest.mark.parametrize("case,verdict,expected", [
    ("inside", "PASS", ()), ("outside", "FAIL", ("QUALITY_FAILURE",)),
    ("crossing", "NOT_EVALUATED", ("EVIDENCE_GAP",)),
    ("segment", "NOT_EVALUATED", ("EVIDENCE_GAP",)),
    ("wrong_verdict", "FAIL", None), ("wrong_event", "PASS", None),
    ("wrong_media", "PASS", None), ("insufficient_coverage", "PASS", None),
])
def test_typed_time_result_recording_and_strict_reopen(tmp_path, monkeypatch, case, verdict, expected):
    from ai_video.production.generation_evaluation_criteria import TemporalMeasurement
    from ai_video.production.project import load_production_project
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video_mcp.generation_feedback import ControlledPresentationVerifier
    from test_generation_evaluation_binding import time_window

    spec = time_window(upper_millis=700, required_coverage=(0, 1000))
    _, committer = marked_fetched(tmp_path, monkeypatch, measurement_spec=spec)
    qa = load_production_project(tmp_path / "project.yaml").qa_policy
    def answer(review):
        source = marked_adjudicate(review, verdict=verdict, unresolved=False)[0]
        obs = source.observations[0]
        interval = {"outside": (800, 850), "crossing": (690, 710)}.get(case, (640, 660))
        result = TemporalMeasurement(artifact_sha256="f" * 64 if case == "wrong_media" else source.artifact_sha256,
            size_bytes=source.size_bytes, evaluation_item_hash=obs.evaluation_item_hash,
            event_id="other-object" if case == "wrong_event" else spec.event_id, boundary=spec.boundary,
            timebase=spec.timebase, interval_millis=interval,
            method="asr_segment" if case == "segment" else "word_alignment",
            coverage_millis=(200, 700) if case == "insufficient_coverage" else (0, 1000),
            evidence_refs=("offline-fixture-measurement",))
        return (source.model_copy(update={"observations": (obs.model_copy(update={"measurement_result": result}),)}),)
    verifier = ControlledPresentationVerifier(evaluator=qa.semantic_authorities[0], proof="technical", adjudicate=answer)
    def run():
        return asyncio.run(review_generation_attempt(committer=committer, attempt_id="review", session=Session(),
                                                     adjudicate=None, presentation_verifier=verifier))
    if expected is None:
        with pytest.raises(ValueError):
            run()
        assert committer.read_generation_experiences() == ()
    else:
        diagnosis = run()
        assert diagnosis.failure_classes == expected
        load_production_project(tmp_path / "project.yaml")
        stored = ProductionStateCommitter(tmp_path).read_generation_experiences()[0]
        assert stored.evaluation_sources[0].observations[0].measurement_result is not None
        replay = asyncio.run(review_generation_attempt(committer=ProductionStateCommitter(tmp_path),
            attempt_id="review", session=None, adjudicate=None))
        assert replay == diagnosis
