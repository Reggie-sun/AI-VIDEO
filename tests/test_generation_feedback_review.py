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
