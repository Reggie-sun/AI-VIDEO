from __future__ import annotations

import importlib
from pathlib import Path


def _effective_loc(path: Path) -> int:
    return sum(
        1
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def test_contracts_and_prepare_helpers_are_owned_by_private_modules() -> None:
    facade = importlib.import_module("ai_video.production.state_commit")
    contracts = importlib.import_module("ai_video.production._state_commit_contracts")
    common = importlib.import_module("ai_video.production._state_commit_common")
    contract_names = (
        "PreparedArtifact", "StateCommitRequest", "BeginRenderAttemptRequest",
        "RecordRenderFailureRequest", "ActivateRenderStateRequest",
        "RenderAttemptPaths", "VoiceAttemptPaths", "PreparedVoiceCandidate",
        "CommitPhase", "CrashInjector", "NoopCrashInjector",
        "_DurableReviewAnalysisPermit", "_DurableVoiceSubmitPermit",
    )
    helper_names = (
        "_owned_temp_name", "_canonical_json_bytes", "_canonical_yaml_bytes",
        "_candidate_artifacts_hash", "_dependency_states_hash",
        "prepare_project_registry_commit", "prepare_audio_registry_commit",
        "prepare_dependency_graph_transition",
    )
    for name in contract_names:
        assert getattr(facade, name) is getattr(contracts, name)
    for name in helper_names:
        assert getattr(facade, name) is getattr(common, name)


def test_generic_transaction_and_io_methods_have_private_owners() -> None:
    facade = importlib.import_module("ai_video.production.state_commit")
    io = importlib.import_module("ai_video.production._state_commit_io")
    transaction = importlib.import_module("ai_video.production._state_commit_transaction")
    assert facade._NativeFileOps is io._NativeFileOps
    assert facade.ProductionStateCommitter._commit_locked.__module__ == transaction.__name__
    assert facade.ProductionStateCommitter._write_mutable_atomic.__module__ == io.__name__
    assert facade.ProductionStateCommitter._write_immutable_artifact.__module__ == io.__name__
    assert facade.ProductionStateCommitter._exclusive_lock.__module__ == facade.__name__


def test_review_repair_and_dependency_methods_have_domain_owners() -> None:
    facade = importlib.import_module("ai_video.production.state_commit")
    review = importlib.import_module("ai_video.production._state_commit_review")
    repair = importlib.import_module("ai_video.production._state_commit_repair")
    dependency = importlib.import_module("ai_video.production._state_commit_dependency")
    committer = facade.ProductionStateCommitter
    assert committer.activate_qa_policy.__module__ == review.__name__
    assert committer.record_final_acceptance.__module__ == review.__name__
    assert committer.record_approved_repair_receipt.__module__ == repair.__name__
    assert committer.record_repair_outcome.__module__ == repair.__name__
    assert committer.bootstrap_dependency_graph.__module__ == dependency.__name__
    assert committer.record_dependency_node_failed.__module__ == dependency.__name__


def test_review_and_repair_modules_stay_focused() -> None:
    production = Path(__file__).parents[1] / "src/ai_video/production"
    assert _effective_loc(production / "_state_commit_review.py") <= 800
    assert _effective_loc(production / "_state_commit_repair.py") <= 800
