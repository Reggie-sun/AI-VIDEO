from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_video.production.models import ActorIdentity
from ai_video.production.hashing import canonical_sha256
from ai_video.production.project import load_production_project
import ai_video.production.shot_continuity_m0_operator as operator_module
from ai_video.production.shot_continuity_m0_feasibility import (
    M0EndpointFeasibilityHumanDecision,
    m0_endpoint_feasibility_scope_fingerprint,
    prepare_m0_endpoint_feasibility_approval_commit,
)
from ai_video.production.shot_continuity_terminal_motion_tail import (
    prepare_terminal_motion_tail_commit,
)


def _operator_fixture(tmp_path):
    from test_shot_continuity_motion_tail import _accepted_source

    root, committer, source_attempt_id, loaded = _accepted_source(tmp_path)
    target = next(item for item in loaded.shots if item.shot_id == "rainy-station-4")
    endpoint_id = next(
        role.asset_ids[0]
        for role in target.required_asset_roles
        if role.role == "approved_endpoint"
    )
    identity_id = loaded.characters[0].reference_asset_ids[0]
    prepared_tail = prepare_terminal_motion_tail_commit(
        project_root=root,
        committer=committer,
        project=loaded,
        attempt_id="m0-operator-tail-v1",
        source_attempt_id=source_attempt_id,
        tail_asset_id="video-shot-rainy-station-3-motion-tail-operator-v1",
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        continuity_constraint_snapshot_hash=operator_module._m0_constraints(
            loaded
        ).content_hash,
        provider_min_duration_milliseconds=2_000,
        provider_max_duration_milliseconds=15_000,
    )
    assert prepared_tail.commit_request is not None
    committer.commit(prepared_tail.commit_request)
    after_tail = load_production_project(root / "project.yaml")
    qualification_attempt_id = "m0-quality-v1-attempt"
    generation_id = "m0-quality-v1-generation"
    output_asset_id = "video-shot-rainy-station-4-m0-quality-v1"
    execution_stack_hash = "4" * 64
    profile_document_hash = "2" * 64
    scope_fingerprint = m0_endpoint_feasibility_scope_fingerprint(
        project_root=root,
        project=after_tail,
        qualification_attempt_id=qualification_attempt_id,
        generation_id=generation_id,
        output_asset_id=output_asset_id,
        execution_stack_hash=execution_stack_hash,
        profile_document_hash=profile_document_hash,
        target_shot_id=target.shot_id,
        output_duration_milliseconds=5_167,
        identity_asset_id=identity_id,
        endpoint_asset_id=endpoint_id,
        motion_tail_asset_id=prepared_tail.tail_asset.asset_id,
    )
    human_decision = M0EndpointFeasibilityHumanDecision.create(
        decision_id="user-chat-a4-authorized-operator-v1",
        reviewer=ActorIdentity(actor_id="reggie", actor_kind="human"),
        decided_at="2026-08-26T12:00:00+08:00",
        evidence_source_id="test-human-review-a4-operator-v1",
        evidence_source_sha256=canonical_sha256(
            {"evidence": "test-only exact A4 operator feasibility review"}
        ),
        scope_fingerprint=scope_fingerprint,
        axis_check="PASS",
        screen_direction_check="PASS",
        subject_scale_check="PASS",
        fov_check="PASS",
        reachable_displacement_check="PASS",
        no_teleport_check="PASS",
    )
    prepared_approval = prepare_m0_endpoint_feasibility_approval_commit(
        project_root=root,
        committer=committer,
        project=after_tail,
        attempt_id="m0-operator-feasibility-v1",
        human_decision=human_decision,
        qualification_attempt_id=qualification_attempt_id,
        generation_id=generation_id,
        output_asset_id=output_asset_id,
        execution_stack_hash=execution_stack_hash,
        profile_document_hash=profile_document_hash,
        target_shot_id=target.shot_id,
        output_duration_milliseconds=5_167,
        identity_asset_id=identity_id,
        endpoint_asset_id=endpoint_id,
        motion_tail_asset_id=prepared_tail.tail_asset.asset_id,
    )
    assert prepared_approval.commit_request is not None
    committer.commit(prepared_approval.commit_request)
    project = load_production_project(root / "project.yaml")
    prompt = "exact M0 C4 quality-v1 prompt"
    profile = SimpleNamespace(
        project_content_hash=project.project.content_hash,
        registry_content_hash=project.registry.content_hash,
        prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        frame_count=124,
        fps=24,
        capability_id="minimax-h3-t8-c4-m0-quality-v1",
        provider_kind="minimax_h3_local",
        model_id="MiniMax-Hailuo-02",
        contract_version=1,
        candidate_id="m0-quality-v1",
        native_audio=True,
        width=1344,
        height=768,
        sealed_seed=352_289_518_598_474_554,
        prepared_receipt_hash="1" * 64,
    )
    sources = SimpleNamespace(
        profile=profile,
        profile_document_hash=profile_document_hash,
        materialization=SimpleNamespace(compiler_hash="3" * 64),
    )
    return (
        root,
        committer,
        project,
        sources,
        prompt,
        identity_id,
        endpoint_id,
        prepared_tail,
        prepared_approval,
    )


def test_build_and_open_m0_quality_operator_bind_exact_approval_without_fast_lane(
    tmp_path, monkeypatch
) -> None:
    (
        root,
        committer,
        project,
        sources,
        prompt,
        identity_id,
        endpoint_id,
        tail,
        approval,
    ) = _operator_fixture(tmp_path)
    request = operator_module.build_m0_quality_request(
        project=project,
        sources=sources,
        prompt=prompt,
        attempt_id="m0-quality-v1-attempt",
        generation_id="m0-quality-v1-generation",
        output_asset_id="video-shot-rainy-station-4-m0-quality-v1",
        identity_asset_id=identity_id,
        endpoint_asset_id=endpoint_id,
        motion_tail_asset_id=tail.tail_asset.asset_id,
        feasibility_approval=approval.approval,
        execution_stack_hash="4" * 64,
    )
    feasibility = request.c4_multi_anchor_binding.approved_endpoint.feasibility_receipt
    assert feasibility.receipt_id == approval.approval.content_hash
    assert feasibility.human_approval_receipt_id == approval.approval.content_hash
    assert len(request.image_bindings) == 3
    assert len(request.media_bindings) == 1
    assert tail.tail_asset.sha256 != tail.receipt.source_video_sha256
    assert request.media_bindings[0].asset_sha256 == tail.tail_asset.sha256

    stack = SimpleNamespace(execution_stack_hash="4" * 64)
    inputs = (
        SimpleNamespace(
            input_kind="inventory",
            payload={
                "comfyui": {"commit": "a" * 40},
                "t8_plugin": {"commit": "b" * 40},
                "videohelpersuite_commit": "c" * 40,
                "remote_provider_enabled": False,
                "cloud_fallback_enabled": False,
            },
            content_hash="9" * 64,
        ),
        SimpleNamespace(
            input_kind="calibration_fixture",
            payload={"prompt": prompt},
            content_hash="5" * 64,
        ),
        SimpleNamespace(input_kind="rubric", payload={}, content_hash="6" * 64),
    )

    class FakeCommitter:
        project_root = root

        def _read_manifest(self):
            return project.manifest

        def reopen_p0_qualification_prepared(self, **_kwargs):
            return SimpleNamespace(), (stack,), (), SimpleNamespace(), inputs

        def reopen_p0_qualification_source_stacks(self, **_kwargs):
            return (SimpleNamespace(execution_stack_hash="7" * 64),)

    fake_committer = FakeCommitter()
    monkeypatch.setattr(
        operator_module, "make_source_production_committer", lambda *_args: fake_committer
    )
    monkeypatch.setattr(
        operator_module,
        "load_m0_qualification_execution_sources",
        lambda **_kwargs: sources,
    )
    monkeypatch.setattr(
        operator_module,
        "build_m0_quality_request",
        lambda **_kwargs: request,
    )
    artifact_root = tmp_path / "artifact-root"
    artifact_root.mkdir()
    opened = operator_module.open_m0_quality_operator(
        project_root=root,
        artifact_root=artifact_root,
        comfy_root=tmp_path,
        profile_path=tmp_path / "quality-profile.json",
        generation_id="m0-quality-v1-generation",
        output_asset_id="video-shot-rainy-station-4-m0-quality-v1",
        attempt_id="m0-quality-v1-attempt",
        identity_asset_id=identity_id,
        endpoint_asset_id=endpoint_id,
        motion_tail_asset_id=tail.tail_asset.asset_id,
        feasibility_approval_hash=approval.approval.content_hash,
        transport=SimpleNamespace(),
    )
    assert opened.status()["next_action"] == "submit"
    assert opened.request == request


def test_operator_routes_submit_poll_fetch_and_existing_attempt_identity(
    monkeypatch,
) -> None:
    manifest = SimpleNamespace(manifest_revision=1, attempts=())
    state = {"next": "submit"}

    class Committer:
        def _read_manifest(self):
            return manifest

        def _reopen_video_request(self, pointer):
            return pointer

    class Caller:
        def qualify(self, *, attempt_id, resolved_request):
            manifest.attempts = (
                SimpleNamespace(
                    attempt_id=attempt_id,
                    operation="video_generation",
                    video_generation_state=SimpleNamespace(request=resolved_request),
                ),
            )
            state["next"] = "poll"
            return (attempt_id, resolved_request.resolved_generation_hash)

    class Service:
        def __init__(self, **_kwargs):
            pass

        def resume_next_action(self, *, attempt_id):
            assert manifest.attempts[0].attempt_id == attempt_id
            return state["next"]

        def refresh_local_once(self, *, attempt_id):
            state["next"] = "fetch"
            return f"polled:{attempt_id}"

        def fetch_local_once(self, *, attempt_id):
            state["next"] = "done"
            return f"fetched:{attempt_id}"

    monkeypatch.setattr(operator_module, "VideoGenerationService", Service)
    request = SimpleNamespace(resolved_generation_hash="8" * 64)
    operator = operator_module.ShotContinuityM0Operator(
        project_root=Path("/tmp"),
        committer=Committer(),
        provider=SimpleNamespace(),
        caller=Caller(),
        request=request,
        attempt_id="exact-m0-attempt",
    )
    assert operator.submit() == ("exact-m0-attempt", "8" * 64)
    assert operator.status()["next_action"] == "poll"
    assert operator.poll() == "polled:exact-m0-attempt"
    assert operator.status()["next_action"] == "fetch"
    assert operator.fetch() == "fetched:exact-m0-attempt"


def test_operator_rejects_existing_attempt_with_different_request() -> None:
    expected = SimpleNamespace(resolved_generation_hash="8" * 64)
    stored = SimpleNamespace(resolved_generation_hash="9" * 64)
    manifest = SimpleNamespace(
        manifest_revision=2,
        attempts=(
            SimpleNamespace(
                attempt_id="exact-m0-attempt",
                operation="video_generation",
                video_generation_state=SimpleNamespace(request=stored),
            ),
        ),
    )

    class Committer:
        def _read_manifest(self):
            return manifest

        def _reopen_video_request(self, pointer):
            return pointer

    operator = operator_module.ShotContinuityM0Operator(
        project_root=Path("/tmp"),
        committer=Committer(),
        provider=SimpleNamespace(),
        caller=SimpleNamespace(),
        request=expected,
        attempt_id="exact-m0-attempt",
    )
    with pytest.raises(Exception, match="does not match the exact request"):
        operator.status()


def test_operator_preflight_uses_full_caller_guard() -> None:
    manifest = SimpleNamespace(manifest_revision=4, attempts=())
    validated = SimpleNamespace(
        sources=SimpleNamespace(profile=SimpleNamespace(sealed_seed=123)),
        source_video_sha256="a" * 64,
        uploads=(SimpleNamespace(file_sha256="b" * 64),),
    )

    class Committer:
        def _read_manifest(self):
            return manifest

    class Caller:
        def validate_pre_effect(self, *, attempt_id, resolved_request):
            assert attempt_id == "exact-m0-attempt"
            assert resolved_request.resolved_generation_hash == "8" * 64
            return validated

    operator = operator_module.ShotContinuityM0Operator(
        project_root=Path("/tmp"),
        committer=Committer(),
        provider=SimpleNamespace(
            validate_pre_effect=lambda _request: (_ for _ in ()).throw(
                AssertionError("provider-only preflight bypassed caller guard")
            )
        ),
        caller=Caller(),
        request=SimpleNamespace(resolved_generation_hash="8" * 64),
        attempt_id="exact-m0-attempt",
    )

    result = operator.preflight()

    assert result["next_action"] == "submit"
    assert result["sealed_seed"] == 123
    assert result["source_video_sha256"] == "a" * 64
