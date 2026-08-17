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


def test_render_methods_have_domain_owners() -> None:
    facade = importlib.import_module("ai_video.production.state_commit")
    lifecycle = importlib.import_module(
        "ai_video.production._state_commit_render_lifecycle"
    )
    support = importlib.import_module("ai_video.production._state_commit_render_support")
    committer = facade.ProductionStateCommitter
    assert committer.activate_render_state.__module__ == lifecycle.__name__
    assert committer._write_render_immutable_artifact.__module__ == support.__name__
    assert committer._validate_render_artifacts.__module__ == support.__name__


def test_voice_methods_have_domain_owners_and_one_permit_identity() -> None:
    facade = importlib.import_module("ai_video.production.state_commit")
    contracts = importlib.import_module("ai_video.production._state_commit_contracts")
    intent = importlib.import_module("ai_video.production._state_commit_voice_intent")
    candidate = importlib.import_module("ai_video.production._state_commit_voice_candidate")
    activation = importlib.import_module("ai_video.production._state_commit_voice_activation")
    committer = facade.ProductionStateCommitter
    assert facade._DurableVoiceSubmitPermit is contracts._DurableVoiceSubmitPermit
    assert committer.record_voice_submit_intent.__module__ == intent.__name__
    assert committer._prepare_voice_activation_request.__module__ == candidate.__name__
    assert committer.generate_voice_asset.__module__ == activation.__name__


def test_recovery_methods_have_domain_owners() -> None:
    facade = importlib.import_module("ai_video.production.state_commit")
    recovery = importlib.import_module("ai_video.production._state_commit_recovery")
    attempts = importlib.import_module("ai_video.production._state_commit_recovery_attempts")
    recovery_fs = importlib.import_module("ai_video.production._state_commit_recovery_fs")
    committer = facade.ProductionStateCommitter
    assert committer.recover.__module__ == recovery.__name__
    assert committer._recover_attempts.__module__ == attempts.__name__
    assert committer._remove_recovery_temp.__module__ == recovery_fs.__name__
    assert committer._require_recovery_file_hash.__module__ == recovery_fs.__name__


def test_committer_mro_preserves_approved_domain_order() -> None:
    facade = importlib.import_module("ai_video.production.state_commit")
    assert tuple(
        owner.__name__ for owner in facade.ProductionStateCommitter.__mro__[1:-1]
    ) == (
        "_StateCommitReviewMixin",
        "_StateCommitRepairMixin",
        "_StateCommitVoiceIntentMixin",
        "_StateCommitVoiceCandidateMixin",
        "_StateCommitVoiceActivationMixin",
        "_StateCommitRenderLifecycleMixin",
        "_StateCommitRenderSupportMixin",
        "_StateCommitDependencyMixin",
        "_StateCommitRecoveryMixin",
        "_StateCommitRecoveryAttemptsMixin",
        "_StateCommitRecoveryFsMixin",
        "_StateCommitTransactionMixin",
        "_StateCommitIoMixin",
    )


def test_review_and_repair_modules_stay_focused() -> None:
    production = Path(__file__).parents[1] / "src/ai_video/production"
    assert _effective_loc(production / "_state_commit_review.py") <= 800
    assert _effective_loc(production / "_state_commit_repair.py") <= 800


def test_render_modules_stay_focused() -> None:
    production = Path(__file__).parents[1] / "src/ai_video/production"
    assert _effective_loc(production / "_state_commit_render_lifecycle.py") <= 800
    assert _effective_loc(production / "_state_commit_render_support.py") <= 800


def test_voice_modules_stay_focused() -> None:
    production = Path(__file__).parents[1] / "src/ai_video/production"
    assert _effective_loc(production / "_state_commit_voice_intent.py") <= 800
    assert _effective_loc(production / "_state_commit_voice_candidate.py") <= 800
    assert _effective_loc(production / "_state_commit_voice_activation.py") <= 800


def test_recovery_modules_stay_focused() -> None:
    production = Path(__file__).parents[1] / "src/ai_video/production"
    assert _effective_loc(production / "_state_commit_recovery.py") <= 800
    assert _effective_loc(production / "_state_commit_recovery_attempts.py") <= 800
    assert _effective_loc(production / "_state_commit_recovery_fs.py") <= 800
