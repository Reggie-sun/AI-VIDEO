"""Decision observations are not source qualification or workflow acceptance."""

from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.generation_feedback import RegisteredGenerationTarget
from production_strategy_factory import make_persisted_strategy_fixture
from test_generation_feedback import NativeFixtureProvider
from test_generation_quality_rejection import _fetched_mixed_failure
from test_production_generated_video_e2e import ATTEMPT_ID


def _files(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def _case(root):
    committer, experience, _, attempt = _fetched_mixed_failure(root)
    binding = committer._reopen_generation_execution_binding(
        attempt.video_generation_state.execution_binding,
    )
    candidate = experience.candidate
    provider = NativeFixtureProvider(capabilities=candidate.capabilities, artifact_bytes=b"unused")
    target = RegisteredGenerationTarget(provider, candidate.provider_profile,
        candidate.compiler_contract, candidate.output_requirement)

    def context(loaded):
        return dict(projection=binding.projection, context=binding.context,
                    policy=binding.policy, lifecycle=binding.lifecycle)

    args = dict(project_root=root, shot_id=binding.context.target_shot_id,
        source_attempt_id=ATTEMPT_ID, source_sha256=experience.evidence[-1].artifact_sha256,
        targets=(target,), context_loader=context, limits=binding.inputs.limits.model_copy(update={
            "allowed_remote_candidates": (f"{candidate.capabilities.provider_name}/{candidate.capability_id}",)}),
        generation_policy=binding.inputs.policy)
    return committer, experience, args


def test_missing_authoring_preserves_real_feedback_gap_without_claiming_workflow_pass(tmp_path):
    from scripts.s01_strategy_regression import inspect_recovery

    _, experience, args = _case(tmp_path)
    before = _files(tmp_path)
    report = inspect_recovery(**args)
    assert report["status"] == "integration_incomplete"
    assert report["strategy"]["decision"] is None
    assert "missing_production_intent" in report["strategy"]["blockers"]
    assert report["feedback"]["disposition"] == "EVIDENCE_GAP"
    assert report["feedback"]["latest_attempt_hash"] == experience.evidence[-1].evidence_hash
    assert report["feedback"]["paid_submits_used"] == 1
    assert report["feedback"]["execution_limits_authority"] == "supplied_snapshot_not_current_authorization"
    assert report["budget_observation"]["content_hash"]
    assert report["budget_observation"]["available_microunits"] == 9_000_000
    assert report["feedback"]["current_authorization_verified"] is False
    assert report["source"]["diagnosis"]["failure_classes"] == ["EVIDENCE_GAP", "QUALITY_FAILURE"]
    assert report["source"]["qualified_reuse"] is None
    assert report["workflow_acceptance"] == "not_evaluated"
    assert _files(tmp_path) == before


def test_source_sha_or_target_mismatch_is_not_an_executor_gap(tmp_path):
    from scripts.s01_strategy_regression import inspect_recovery

    _, _, args = _case(tmp_path)
    before = _files(tmp_path)
    with pytest.raises(AiVideoError):
        inspect_recovery(**{**args, "source_sha256": "0" * 64})
    with pytest.raises(AiVideoError):
        inspect_recovery(**{**args, "shot_id": "another-shot"})
    assert _files(tmp_path) == before


@pytest.mark.parametrize("verdict,expected", [("PASS", "selected"), ("FAIL", "evidence_required")])
def test_persisted_strategy_control_returns_actual_owner_decision(tmp_path, verdict, expected):
    from scripts.s01_strategy_regression import inspect_strategy

    fixture = make_persisted_strategy_fixture(tmp_path, source_verdict=verdict)
    before = _files(tmp_path)
    result = inspect_strategy(committer=fixture.committer, shot_id=fixture.parent_shot_id, targets=())
    assert result["decision"]["disposition"] == expected
    if verdict == "PASS":
        assert result["decision"]["selected_generation_count"] == 0
    else:
        assert "evidence_required:source_fail" in result["decision"]["reasons"]
    assert result["generation_available"] is False
    assert _files(tmp_path) == before


def test_empty_generation_registration_is_not_a_successful_recovery(tmp_path):
    from scripts.s01_strategy_regression import inspect_recovery

    _, _, args = _case(tmp_path)
    report = inspect_recovery(**{**args, "targets": ()})
    assert report["status"] == "integration_incomplete"
    assert report["feedback"]["disposition"] is None
    assert report["feedback"]["blockers"] == ["no_registered_generation_targets"]
    assert report["workflow_acceptance"] == "not_evaluated"


def test_full_generation_control_is_not_rewritten_into_a_local_edit_gap(tmp_path):
    from scripts.s01_strategy_regression import inspect_strategy
    from test_production_planning_generation import _generation_target

    fixture = make_persisted_strategy_fixture(tmp_path, generation_only=True)
    before = _files(tmp_path)
    result = inspect_strategy(committer=fixture.committer, shot_id=fixture.parent_shot_id,
                              targets=(_generation_target(),))
    assert result["generation_available"] is True
    assert result["decision"]["disposition"] == "selected"
    assert result["decision"]["selected_generation_count"] == 1
    assert result["decision"]["candidates"][0]["blockers"] == []
    assert _files(tmp_path) == before


def test_harness_routes_driver_and_controls_without_unmapped_fallback():
    from scripts.agent_harness import inspect_paths, load_policy

    policy = load_policy(Path(__file__).resolve().parents[1] / ".agent/harness/policy.yaml")
    inspection = inspect_paths(["scripts/s01_strategy_regression.py",
                               "tests/test_s01_strategy_regression.py"], policy)
    assert inspection["fallback_paths"] == []
    assert "s01_strategy_regression_tests" in inspection["check_ids"]


def test_cli_rejects_missing_inputs_without_revealing_paths_or_creating_project(tmp_path, capsys):
    from scripts.s01_strategy_regression import main

    args = []
    for name in ("project-root", "planning-request", "provider-profile"):
        args.extend(("--" + name, str(tmp_path / "missing-private-input")))
    args.extend(("--source-attempt", "old", "--source-sha256", "0" * 64,
                 "--context-attempt", "latest"))
    assert main(args) == 2
    output = capsys.readouterr().out
    assert "invalid_input" in output
    assert "private-input" not in output
    assert list(tmp_path.iterdir()) == []


def test_context_mismatch_is_rejected_without_writes(tmp_path):
    from scripts.s01_strategy_regression import inspect_recovery

    _, _, args = _case(tmp_path)
    original = args["context_loader"]
    before = _files(tmp_path)

    def wrong_context(project):
        value = original(project)
        value["context"] = value["context"].model_copy(update={"target_shot_id": "another-shot"})
        return value

    with pytest.raises(AiVideoError, match="another Shot"):
        inspect_recovery(**{**args, "context_loader": wrong_context})
    assert _files(tmp_path) == before


def test_manifest_change_invalidates_observation_without_retry(tmp_path, monkeypatch):
    from scripts.s01_strategy_regression import (
        inspect_recovery, ProductionStateCommitter, GenerationFeedbackOrchestrator,
    )

    _, _, args = _case(tmp_path)
    original = ProductionStateCommitter._read_manifest
    before = _files(tmp_path)
    prepare = GenerationFeedbackOrchestrator.prepare
    # Inject drift after successful Feedback preparation, before the final state check.
    def changed(committer):
        manifest = original(committer)
        return manifest.model_copy(update={"manifest_revision": manifest.manifest_revision + 1})

    def prepared_then_changed(orchestrator, **kwargs):
        result = prepare(orchestrator, **kwargs)
        monkeypatch.setattr(ProductionStateCommitter, "_read_manifest", changed)
        return result

    monkeypatch.setattr(GenerationFeedbackOrchestrator, "prepare", prepared_then_changed)
    with pytest.raises(AiVideoError, match="state changed"):
        inspect_recovery(**args)
    assert _files(tmp_path) == before
