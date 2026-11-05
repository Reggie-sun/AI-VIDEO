from dataclasses import replace
import hashlib
from types import SimpleNamespace

import pytest

from ai_video.production.generation_decision import DecisionPolicy, ExecutionLimits
from ai_video.production.shot_router import RouterPolicyIdentity, VideoRoutingPolicy
from scripts import jimeng_feedback_driver as driver
from test_production_jimeng import setup


def configuration():
    profile = setup(model_id="seedance_2.0_vip")[0]._profile
    return driver.DriverConfiguration.from_json({
        "schema_version": "jimeng-feedback-driver/1",
        "row": {"shot": {"shot_id": "shot-1"}, "generation": {}},
        "jimeng_profile": profile.model_dump(mode="json"),
        "routing_policy": VideoRoutingPolicy(
            identity=RouterPolicyIdentity(policy_id="driver-test", policy_version="1", policy_sha256="1" * 64),
            local_resources_available=False, remote_authorized=True,
            budget_authorized=True, execution_purpose="qualification").model_dump(mode="json"),
        "decision_policy": DecisionPolicy(max_resamples=0, allow_bounded_exploration=True).model_dump(mode="json"),
        "execution_limits": ExecutionLimits(task_id="driver-test", generation_forbidden=False,
            allowed_remote_candidates=("jimeng/" + profile.capability_id,), paid_submit_ceiling=1,
            paid_submits_used=0, local_batch_limit=1, local_batch_used=0,
            local_total_used=0, local_resource_available=False).model_dump(mode="json"),
    })


@pytest.mark.parametrize("change", [
    {"paid_submit_ceiling": 2}, {"paid_submits_used": 2},
    {"allowed_remote_candidates": ("jimeng/another-profile",)},
])
def test_factory_revalidates_direct_configuration_before_any_state(tmp_path, change):
    config = configuration()
    invalid = replace(config, execution_limits=config.execution_limits.model_copy(update=change))
    with pytest.raises(ValueError, match="one exact candidate"):
        driver.create_runtime(project_root=tmp_path, configuration=invalid)
    assert list(tmp_path.iterdir()) == []


def test_factory_rejects_resamples_and_config_cannot_supply_authorization(tmp_path):
    config = configuration()
    with pytest.raises(ValueError, match="no resamples"):
        driver.create_runtime(project_root=tmp_path, configuration=replace(config,
            decision_policy=DecisionPolicy(max_resamples=1)))
    with pytest.raises(ValueError, match="fields or version"):
        driver.DriverConfiguration.from_json({"schema_version": "jimeng-feedback-driver/1", "authorization": {}})


def test_offline_runtime_has_no_lifecycle_effect_and_rejects_live_operations(tmp_path):
    runtime = driver.create_runtime(project_root=tmp_path, configuration=configuration())
    assert runtime.provider._transport is None
    assert runtime.provider._committer is runtime.committer
    assert list(tmp_path.iterdir()) == []
    with pytest.raises(ValueError, match="live transport"):
        runtime.submit_once(attempt_id="offline", paid_preview=object(), reservation_id="offline")
    with pytest.raises(ValueError, match="live transport"):
        runtime.refresh_once(attempt_id="offline")
    with pytest.raises(ValueError, match="live transport"):
        runtime.fetch_once(attempt_id="offline")
    with pytest.raises(ValueError, match="exact prepared"):
        runtime.start(prepared=object(), attempt_id="offline")
    assert list(tmp_path.iterdir()) == []


def test_prepare_rejects_stale_reference_before_returning_executable_result(tmp_path, monkeypatch):
    runtime = driver.create_runtime(project_root=tmp_path, configuration=configuration())
    binding = SimpleNamespace(asset_id="exact")
    prepared = SimpleNamespace(resolved_request=SimpleNamespace(image_bindings=(binding,), media_bindings=()))
    monkeypatch.setattr(runtime.orchestrator, "prepare", lambda **kwargs: prepared)
    seen = []
    def resolve(value):
        seen.append(value)
        raise ValueError("stale exact reference")
    runtime = replace(runtime, reference_resolver=resolve)
    with pytest.raises(ValueError, match="stale exact"):
        runtime.prepare()
    assert seen == [binding]
    assert list(tmp_path.iterdir()) == []


def test_reference_resolver_reopens_real_canonical_project_and_rejects_byte_tampering(tmp_path):
    from production_project_factory import make_p4_composition_fixture

    loaded, _ = make_p4_composition_fixture(tmp_path)
    asset = next(a for a in loaded.registry.assets if a.mime_type == "image/png")
    binding = SimpleNamespace(asset_id=asset.asset_id, asset_sha256=asset.sha256, size_bytes=asset.size_bytes)
    resolver = driver.registered_reference_resolver(tmp_path)
    assert hashlib.sha256(resolver(binding)).hexdigest() == asset.sha256
    with pytest.raises(ValueError, match="resolved binding"):
        resolver(SimpleNamespace(asset_id=asset.asset_id, asset_sha256="0" * 64, size_bytes=asset.size_bytes))
    loaded.asset_paths[asset.asset_id].write_bytes(b"tampered")
    from ai_video.errors import AiVideoError
    with pytest.raises((AiVideoError, ValueError)):
        resolver(binding)


def test_live_calls_delegate_once_without_a_poll_or_retry_loop(tmp_path):
    runtime = driver.create_runtime(project_root=tmp_path, configuration=configuration(), transport=object())
    calls = []
    service = SimpleNamespace(
        submit_once=lambda **kw: calls.append(("submit", kw)) or "submitted",
        refresh_once=lambda **kw: calls.append(("refresh", kw)) or "observed",
        fetch_once=lambda **kw: calls.append(("fetch", kw)) or "fetched")
    runtime = replace(runtime, service=service)
    preview = object()
    assert runtime.submit_once(attempt_id="one", paid_preview=preview, reservation_id="one") == "submitted"
    assert runtime.refresh_once(attempt_id="one") == "observed"
    assert runtime.fetch_once(attempt_id="one") == "fetched"
    assert [kind for kind, _ in calls] == ["submit", "refresh", "fetch"]
    assert calls[0][1]["paid_preview"] is preview
