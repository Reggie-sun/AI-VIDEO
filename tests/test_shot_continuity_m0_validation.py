from __future__ import annotations

import copy
from pathlib import Path
from types import SimpleNamespace

import ai_video.production.shot_continuity_m0_qualification as m0_qualification
import pytest

from ai_video.errors import AiVideoError
from ai_video.production.video_execution_stack import (
    GenerationExecutionStackIdentity,
    StackComponentIdentity,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / (
    "workflows/qualification/"
    "minimax_h3_t8_c4_m0_candidate_v1_profile.json"
)


def _materialized_m0(sources) -> GenerationExecutionStackIdentity:
    profile = sources.profile
    unmaterialized = GenerationExecutionStackIdentity.create(
        materialization_status="unmaterialized",
        candidate_id=profile.candidate_id,
        contract_version=profile.contract_version,
        provider_kind=profile.provider_kind,
        deployment_identity=profile.deployment_identity,
        model_id=profile.model_id,
        capability_id=profile.capability_id,
        profile_hash="none",
        compiler_hash="none",
        workflow_hash="none",
        components=tuple(
            StackComponentIdentity(
                ordinal=ordinal,
                kind=item.kind,
                component_id=item.component_id,
                content_hash=item.sha256,
            )
            for ordinal, item in enumerate(profile.components)
        ),
        sampler_identity=profile.sampler,
        scheduler_identity=profile.scheduler,
        runtime_seals=profile.runtime_seals,
        output_contract_hash=profile.output_contract_hash,
    )
    assert unmaterialized.execution_stack_hash == profile.initial_execution_stack_hash
    return unmaterialized.materialize(sources.materialization)


def _bundle(sources):
    profile = sources.profile
    m0 = _materialized_m0(sources)
    m1 = SimpleNamespace(
        execution_stack_hash=profile.m1_execution_stack_hash,
        materialization_status="unmaterialized",
        components=(
            SimpleNamespace(
                component_id="hybrid-artifact-candidate-v1",
                presence="absent",
                content_hash="none",
            ),
        ),
    )
    receipt = SimpleNamespace(
        content_hash="a" * 64,
        project=SimpleNamespace(content_hash=profile.project_content_hash),
        registry=SimpleNamespace(content_hash=profile.registry_content_hash),
    )
    policies = (
        SimpleNamespace(policy_hash="b" * 64),
        SimpleNamespace(policy_hash="c" * 64),
        SimpleNamespace(policy_hash="d" * 64),
    )
    validation_set = SimpleNamespace(content_hash="e" * 64)
    calibration = SimpleNamespace(
        input_kind="calibration_fixture",
        content_hash="f" * 64,
        execution_stack_hashes=(m0.execution_stack_hash,),
        payload={
            "prompt_sha256": profile.prompt_sha256,
            "task_type": profile.task_type,
            "steps": profile.steps,
            "sampler": profile.sampler,
            "scheduler": profile.scheduler,
            "turbo_lora": profile.turbo_lora,
        },
    )
    inputs = (
        calibration,
        SimpleNamespace(
            input_kind="effect_budget",
            content_hash="1" * 64,
            execution_stack_hashes=(m0.execution_stack_hash,),
            payload={},
        ),
    )
    return receipt, (m0, m1), policies, validation_set, inputs


class _ReadOnlyCommitter:
    def __init__(self, bundle) -> None:
        self.bundle = bundle
        self.reopen_calls: list[tuple[str, ...]] = []

    def reopen_p0_qualification_prepared(
        self, *, required_materialized_candidates: tuple[str, ...]
    ):
        self.reopen_calls.append(required_materialized_candidates)
        return self.bundle


def test_m0_validation_preflight_reopens_and_consumes_exact_materialized_hashes() -> None:
    sources = m0_qualification.load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    committer = _ReadOnlyCommitter(_bundle(sources))
    preflight_owner = getattr(
        m0_qualification,
        "reopen_m0_validation_preflight",
        None,
    )

    assert preflight_owner is not None, (
        "M0 Validation V1 requires one guarded pre-effect reopen owner"
    )
    first = preflight_owner(
        committer=committer,
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    replay = preflight_owner(
        committer=committer,
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )

    assert first == replay
    assert first.candidate_label == "m0"
    assert first.execution_stack_hash == committer.bundle[1][0].execution_stack_hash
    assert first.profile_hash == sources.materialization.profile_hash
    assert first.compiler_hash == sources.materialization.compiler_hash
    assert first.workflow_hash == sources.materialization.workflow_hash
    assert first.qualification_receipt_hash == committer.bundle[0].content_hash
    assert first.validation_set_hash == committer.bundle[3].content_hash
    assert first.policy_hashes == tuple(
        item.policy_hash for item in committer.bundle[2]
    )
    assert first.qualification_input_hashes == tuple(
        (item.input_kind, item.content_hash) for item in committer.bundle[4]
    )
    assert committer.reopen_calls == [("m0",), ("m0",)]


@pytest.mark.parametrize(
    "drift",
    (
        "project",
        "registry",
        "m1_hash",
        "m1_materialized",
        "hybrid_present",
        "calibration_prompt",
        "dependent_input_stack",
    ),
)
def test_m0_validation_preflight_denies_frozen_target_drift(drift: str) -> None:
    sources = m0_qualification.load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    bundle = copy.deepcopy(_bundle(sources))
    receipt, stacks, _, _, inputs = bundle
    if drift == "project":
        receipt.project.content_hash = "0" * 64
    elif drift == "registry":
        receipt.registry.content_hash = "0" * 64
    elif drift == "m1_hash":
        stacks[1].execution_stack_hash = "0" * 64
    elif drift == "m1_materialized":
        stacks[1].materialization_status = "materialized"
    elif drift == "hybrid_present":
        stacks[1].components[0].presence = "present"
        stacks[1].components[0].content_hash = "0" * 64
    elif drift == "calibration_prompt":
        inputs[0].payload["prompt_sha256"] = "0" * 64
    else:
        inputs[1].execution_stack_hashes = ("0" * 64,)
    committer = _ReadOnlyCommitter(bundle)

    with pytest.raises(AiVideoError, match="frozen qualification"):
        m0_qualification.reopen_m0_validation_preflight(
            committer=committer,
            profile_path=PROFILE_PATH,
            artifact_root=REPO_ROOT,
        )

    assert committer.reopen_calls == [("m0",)]


@pytest.mark.parametrize("missing", ("calibration", "hybrid"))
def test_m0_validation_preflight_denies_incomplete_target(missing: str) -> None:
    sources = m0_qualification.load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    receipt, stacks, policies, validation_set, inputs = _bundle(sources)
    if missing == "calibration":
        inputs = tuple(
            item for item in inputs if item.input_kind != "calibration_fixture"
        )
    else:
        stacks[1].components = ()
    committer = _ReadOnlyCommitter(
        (receipt, stacks, policies, validation_set, inputs)
    )

    with pytest.raises(AiVideoError, match="incomplete"):
        m0_qualification.reopen_m0_validation_preflight(
            committer=committer,
            profile_path=PROFILE_PATH,
            artifact_root=REPO_ROOT,
        )

    assert committer.reopen_calls == [("m0",)]
