from __future__ import annotations

import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("run", ["jieshi-e01-seedance20-20260905-001", "jieshi-e01-seedance25-20260905-repair01"])
@pytest.mark.parametrize("script", ["prepare_request.py", "live_first_shot.py"])
def test_run_entry_works_by_path_without_repo_on_pythonpath(run, script, tmp_path):
    import os
    import subprocess
    import sys
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run([sys.executable, "-B", str(ROOT / "runs" / run / script), "--help"],
        cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "--config" in result.stdout


def _driver():
    return importlib.import_module("scripts.generation_feedback_driver")


def test_driver_import_is_effect_free_and_config_is_required():
    driver = _driver()
    with pytest.raises(FileNotFoundError):
        driver.load_configuration(ROOT / "missing-driver-config.json")


def test_execute_rejects_missing_exact_ready_binding_before_effect():
    driver = _driver()
    with pytest.raises(ValueError, match="exact freshly prepared"):
        driver.execute_prepared(project_root=ROOT, prepared=object(), provider=object(),
            paid_preview=object(), authorization=object(), attempt_id="offline", reservation_id="offline")


def test_configuration_prepares_from_current_project_and_rejects_stale_plan(tmp_path):
    from dataclasses import replace
    from ai_video.errors import AiVideoError
    from ai_video.planning import VideoPlanningRequest, VideoPlanner, ShotIntentEvidence, ProductionPolicyInput
    from ai_video.production.project import load_production_project
    from ai_video.production.seedance import SeedanceVideoProvider
    from ai_video.production.video_requirement import ProviderNeutralGenerationIntentProjection, GenerationOperation
    from production_remote_generation_factory import prepare_remote_generation
    from test_production_seedance import _profile, _request, _FakeTransport, _provider_asset_reference, FIXED_NOW

    driver = _driver()
    profile = _profile()
    transport = _FakeTransport()
    provider = SeedanceVideoProvider(profile=profile, transport=transport,
        credential=lambda: pytest.fail("preparation cannot access credentials"),
        input_reference=_provider_asset_reference, now=lambda: FIXED_NOW)
    template = prepare_remote_generation(root=tmp_path, provider=provider, request=_request(profile),
                                        compiler_id="seedance-video-compiler")
    loaded = load_production_project(tmp_path / "project.yaml")
    binding = template.execution_binding
    requirement = binding.projection.requirement
    shot = loaded.shots[0]
    scene = next(s for s in loaded.scenes if s.scene_id == shot.scene_id)
    request = VideoPlanningRequest.create(request_id="driver-current-plan", planning_contract_version="video-planner/3",
        target_shot=shot, scene_context=scene,
        character_context=tuple(c for c in loaded.characters if c.character_id in shot.character_ids),
        available_assets=(), previous_shot_state=None, review_decision=None,
        generation_intent=ProviderNeutralGenerationIntentProjection.create(
            generation_intent=requirement.generation_intent, output_need=requirement.output_need,
            audio_need=requirement.audio_need, quality_need=requirement.quality_need,
            generation_operation=GenerationOperation.TEXT_TO_VIDEO),
        shot_intent_evidence=ShotIntentEvidence(target_shot_id=shot.shot_id,
            target_shot_content_hash=shot.content_hash, character_action_required=True, state_change_required=True),
        production_policy=ProductionPolicyInput(remote_authorized=True, budget_authorized=True))
    plan = VideoPlanner().plan(request)
    context = binding.context.model_copy(update={"storyboard_revision": loaded.storyboard.revision,
        "storyboard_content_hash": loaded.storyboard.content_hash})
    configuration = driver.DriverConfiguration(request, plan, context, binding.policy, binding.lifecycle,
        binding.inputs.policy, binding.inputs.limits, profile, template.resolved_request.effective_output)
    configuration = driver.DriverConfiguration.from_json({
        "schema_version": "generation-feedback-driver/1",
        **{key: value.model_dump(mode="json") for key, value in {
            "planning_request": request, "video_plan": plan, "context": context,
            "routing_policy": binding.policy, "lifecycle": binding.lifecycle,
            "decision_policy": binding.inputs.policy, "execution_limits": binding.inputs.limits,
            "seedance_profile": profile, "output_requirement": configuration.output,
        }.items()},
    })
    current = driver.prepare_configuration(project_root=tmp_path, configuration=configuration, provider=provider)
    assert current.execution_binding is not None, current.decision
    assert current.inputs.evidence == ()
    assert current.resolved_request.adapter_compiler_version == "2"
    assert len(current.inputs.candidates) == len(provider.capabilities().variants)
    with pytest.raises((ValueError, AiVideoError)):
        driver.prepare_configuration(project_root=tmp_path,
            configuration=replace(configuration, video_plan=plan.model_copy(update={"plan_hash": "f" * 64})),
            provider=provider)
    assert transport.requests == []


def test_driver_executes_real_seedance_compiler_committer_and_scripted_transport(tmp_path, monkeypatch):
    import hashlib
    from types import SimpleNamespace
    from ai_video.production.paid_provider import PaidProviderCallPreview, PaidProviderEgressItem
    from ai_video.production.seedance import SeedanceVideoProvider
    from ai_video.production.state_commit import ProductionStateCommitter
    from production_remote_generation_factory import prepare_remote_generation
    from test_production_seedance import (_profile, _request, _FakeTransport, _json_response,
        _paid_preview, _authorization, _provider_asset_reference, FIXED_NOW)

    driver = _driver()
    transport = _FakeTransport()
    profile = _profile()
    provider = SeedanceVideoProvider(profile=profile, transport=transport,
        credential=lambda: "offline-fixture-secret", input_reference=_provider_asset_reference,
        now=lambda: FIXED_NOW)
    prepared = prepare_remote_generation(root=tmp_path, provider=provider, request=_request(profile),
                                        compiler_id="seedance-video-compiler")
    request = prepared.resolved_request
    original = _paid_preview(request, provider.preview(request))
    data = original.model_dump(mode="python", exclude={"preview_fingerprint"})
    data["egress_items"] = (PaidProviderEgressItem(item_id="prompt",
        sha256=hashlib.sha256(request.prompt_text.encode()).hexdigest(),
        size_bytes=len(request.prompt_text.encode()), mime_type="text/plain", purpose="prompt"),)
    preview = PaidProviderCallPreview.create(**data)
    authorization = _authorization(preview)
    monkeypatch.setattr(driver, "datetime", SimpleNamespace(now=lambda _: FIXED_NOW))
    monkeypatch.setattr(driver, "ProductionStateCommitter", lambda root, **kwargs:
        ProductionStateCommitter(root, paid_provider_clock=lambda: FIXED_NOW, **kwargs))
    completed = {"id": "driver-task", "model": request.model_id,
                 "status": "succeeded", "content": {"video_url": "https://media.example/result.mp4"}}
    transport.responses.extend((_json_response({"id": "driver-task"}),
                                _json_response(completed), _json_response(completed)))
    result = driver.execute_prepared(project_root=tmp_path, prepared=prepared, provider=provider,
        paid_preview=preview, authorization=authorization, attempt_id=preview.attempt_id,
        reservation_id="driver-reservation", max_polls=1, poll_interval_seconds=0)
    assert result["evaluation_required"]
    assert sum(r.method == "POST" for r in transport.requests) == 1
    committer = ProductionStateCommitter(tmp_path)
    assert committer._read_manifest().attempts[-1].video_generation_state.fetch_receipt is not None
    from ai_video_mcp.generation_feedback import review_generation_attempt
    from test_generation_feedback_review import Session, adjudicate
    import asyncio
    diagnosis = asyncio.run(review_generation_attempt(committer=committer,
        attempt_id=preview.attempt_id, session=Session(), adjudicate=adjudicate))
    assert "QUALITY_FAILURE" in diagnosis.failure_classes
    assert len(committer.read_generation_experiences()) == 1
    assert sum(r.method == "POST" for r in transport.requests) == 1
