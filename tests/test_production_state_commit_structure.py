from __future__ import annotations

import importlib


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