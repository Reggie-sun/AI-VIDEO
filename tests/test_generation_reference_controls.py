"""Offline control previews use the exact adapter parameters without effects."""

import base64
import hashlib
import json
from dataclasses import replace

import pytest


def test_h3_reference_preview_reveals_alias_bytes_and_native_control_limits():
    from ai_video.production.video import VideoGenerationRequest
    from ai_video.production.video_reference_controls import video_reference_control_report
    from test_production_minimax_h3_max import _setup

    provider, resolved, _, transport, raw = _setup()
    original = resolved.activation_scope.request
    alias = original.image_bindings[0].model_copy(update={"asset_id": "second-character"})
    request = VideoGenerationRequest.create(**original.model_dump(mode="python",
        exclude={"request_input_hash", "image_bindings"}),
        image_bindings=tuple(sorted((*original.image_bindings, alias), key=lambda b: b.asset_id)))
    resolved = provider.resolve(request)
    raw[alias.asset_id] = raw[original.image_bindings[0].asset_id]
    native = json.loads(provider.native_payload(resolved))
    provider._credential = lambda: pytest.fail("credential lookup")
    provider._reference_resolver = lambda _: pytest.fail("reference materialization")
    report = video_reference_control_report(request=resolved,
        native_parameters=provider.native_control_parameters(resolved))
    assert report["native_parameters"]["ratio"] == "16:9"
    assert report["reference_summary"]["binding_count"] == 2
    assert report["reference_summary"]["unique_byte_count"] == 1
    assert [r["native_path"] for r in report["references"]] == ["content[1]", "content[2]"]
    assert {r["native_role"] for r in report["references"]} == {"reference_image"}
    for row, content in zip(report["references"], native["content"][1:], strict=True):
        assert row["native_role"] == content["role"]
        assert row["asset_sha256"] == hashlib.sha256(
            base64.b64decode(content["image_url"]["url"].split(",", 1)[1])).hexdigest()
    controls = {r["target"]: r for r in report["controls"]}
    assert controls["opening_frame"]["mechanism"] == "MODEL_GUIDANCE"
    assert controls["action_timing"]["mechanism"] == "MODEL_GUIDANCE"
    assert controls["whitebox_motion"]["mechanism"] == "UNBOUND"
    assert report["actual_quality"] == "NOT_EVALUATED"
    assert report["materialization"] == "NOT_EVALUATED"
    assert transport.calls == []


@pytest.mark.parametrize("provider_kind", ["h3", "seedance"])
def test_native_control_parameters_match_actual_payload_without_reading_inputs(provider_kind):
    if provider_kind == "h3":
        from test_production_minimax_h3_max import _setup
        provider, request, _, transport, _ = _setup()
        payload = json.loads(provider.native_payload(request))
    else:
        from test_production_seedance import SeedanceVideoProvider, _profile, _request
        profile = _profile()
        provider = SeedanceVideoProvider(profile=profile, transport=object(),
            credential=lambda: pytest.fail("credential lookup"), input_reference=object())
        request = provider.resolve(_request(profile))
        payload = provider._payload(request)
    provider._credential = lambda: pytest.fail("credential lookup")
    provider._reference_resolver = lambda _: pytest.fail("reference resolver")
    provider._asset_reference = lambda _: pytest.fail("reference materialization")
    assert provider.native_control_parameters(request) == {
        key: value for key, value in payload.items() if key != "content"}


def test_prepare_cli_projection_does_not_serialize_runtime_provider():
    from ai_video.production.video_reference_controls import prepared_generation_report
    from test_generation_feedback import feedback_setup

    setup, provider, _, _, orchestrator = feedback_setup()
    prepared = orchestrator.prepare(limits=setup["inputs"].limits)
    class OpaqueRuntime:
        def __deepcopy__(self, memo):
            pytest.fail("runtime provider copied")
    prepared = replace(prepared, provider=OpaqueRuntime())
    report = prepared_generation_report(prepared)
    assert "provider" not in report
    assert report["reference_control"]["selected_route"]["model_id"] == prepared.resolved_request.model_id
    assert report["reference_control"]["native_parameters"] == "NOT_EVALUATED"
    assert json.loads(json.dumps(report))["production_acceptance"] == "NOT_EVALUATED"
    assert provider.call_counts.submit == provider.call_counts.fetch == 0


def test_no_selected_request_does_not_invent_a_route_or_native_control():
    from ai_video.production.generation_feedback import PreparedGeneration
    from ai_video.production.video_reference_controls import prepared_generation_report
    from test_generation_feedback import feedback_setup

    setup, _, _, _, orchestrator = feedback_setup()
    prepared = orchestrator.prepare(limits=setup["inputs"].limits)
    stopped = PreparedGeneration(prepared.inputs, prepared.decision)
    report = prepared_generation_report(stopped)["reference_control"]
    assert report["selected_route"] == "NOT_EVALUATED"
    assert report["actual_quality"] == "NOT_EVALUATED"


@pytest.mark.parametrize("family", ["h3", "seedance-2.0", "seedance-2.5"])
@pytest.mark.parametrize("scenario,mode", [
    ("A potter in a workshop turns a bowl, then holds it still.", "first"),
    ("An empty courtyard: camera tracks from the gate to the fountain.", "first_last"),
    ("Two divers pass a yellow lamp in a flooded cave.", "reference_video"),
])
def test_reusable_mode_matrix_is_exact_and_zero_effect(family, scenario, mode):
    from ai_video.production.video import VideoGenerationMode, VideoGenerationRequest, VideoMediaReferenceBinding
    from ai_video.production.video_reference_controls import video_reference_control_report
    from test_production_minimax_h3_max import _setup
    h3, resolved, _, _, _ = _setup(aspect_ratio="adaptive")
    original = resolved.activation_scope.request
    first = original.image_bindings[0].model_copy(update={"role": "first_frame"})
    images = ((first,) if mode == "first" else
        (first, first.model_copy(update={"role": "last_frame", "asset_id": "terminal-frame"}))
        if mode == "first_last" else original.image_bindings)
    videos = () if mode != "reference_video" else (VideoMediaReferenceBinding(
        kind="video", role="reference_video", asset_id="motion-layout", asset_sha256="d" * 64,
        mime_type="video/mp4", size_bytes=32, duration_millis=4000,
        width=1280, height=720, fps=24),)
    selected_mode = VideoGenerationMode.REFERENCE_TO_VIDEO if videos else VideoGenerationMode.IMAGE_TO_VIDEO
    if family == "h3":
        provider = h3
        request = VideoGenerationRequest.create(**original.model_dump(mode="python",
            exclude={"request_input_hash", "image_bindings", "media_bindings", "mode", "prompt_text"}),
            mode=selected_mode, prompt_text=scenario, image_bindings=images, media_bindings=videos)
    else:
        from test_production_seedance import SeedanceVideoProvider, _profile, _request
        from ai_video.production.video import VideoFlexibleOutputRequirement
        images = tuple(b.model_copy(update={"width": 512, "height": 512}) for b in images)
        profile = _profile()
        provider = SeedanceVideoProvider(profile=profile, transport=object(),
            credential=lambda: pytest.fail("credential lookup"), input_reference=object())
        model = "doubao-seedance-2-0-260128" if family.endswith("2.0") else "doubao-seedance-2-5-260628"
        output = VideoFlexibleOutputRequirement(timing_mode="exact_seconds", duration_seconds=5,
            dimension_mode="adaptive", resolution_label="720p", ratio="adaptive", fps=24,
            container="mp4", mime_type="video/mp4", native_audio=True)
        base = _request(profile, model_id=model, mode=selected_mode,
            image_bindings=images, media_bindings=videos, output=output)
        request = VideoGenerationRequest.create(**base.model_dump(mode="python",
            exclude={"request_input_hash", "prompt_text"}), prompt_text=scenario)
    provider._reference_resolver = lambda _: pytest.fail("reference lookup")
    provider._asset_reference = lambda _: pytest.fail("reference lookup")
    resolved = provider.resolve(request)
    report = video_reference_control_report(request=resolved,
        native_parameters=provider.native_control_parameters(resolved))
    controls = {r["target"]: r for r in report["controls"]}
    assert controls["opening_frame"]["mechanism"] == (
        "MODEL_GUIDANCE" if videos else "API_ENDPOINT_INPUT")
    assert controls["closing_frame"]["mechanism"] == (
        "API_ENDPOINT_INPUT" if mode == "first_last" else "MODEL_GUIDANCE")
    assert controls["whitebox_motion"]["mechanism"] == ("MODEL_REFERENCE" if videos else "UNBOUND")
    assert report["prompt"]["text"] == scenario
    assert report["selected_route"]["mode"] == selected_mode.value
    if family == "seedance-2.5" and videos:
        assert report["native_parameters"]["omni_reference_task_type"] == "reference"
    assert report["actual_quality"] == "NOT_EVALUATED"


def test_canvas_cli_serializes_prepare_without_copying_provider(monkeypatch, tmp_path, capsys):
    from scripts import canvas_production
    from test_generation_feedback import feedback_setup
    setup, _, _, _, orchestrator = feedback_setup()
    prepared = orchestrator.prepare(limits=setup["inputs"].limits)
    class OpaqueRuntime:
        def __deepcopy__(self, memo):
            pytest.fail("runtime provider copied")
    monkeypatch.setattr(canvas_production, "run", lambda **_: replace(prepared, provider=OpaqueRuntime()))
    assert canvas_production.main(["prepare", "--data", str(tmp_path / "data.json"),
        "--project-root", str(tmp_path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["reference_control"]["actual_quality"] == "NOT_EVALUATED"
    assert "provider" not in result


def test_exact_prepare_joins_semantic_references_to_native_indices(tmp_path):
    from ai_video.production.video_reference_controls import prepared_generation_report
    from test_canvas_source_expression import subject_service
    service, limits = subject_service(tmp_path)
    prepared = service.prepare(limits=limits)
    report = prepared_generation_report(prepared)["reference_control"]
    assert prepared.execution_binding is not None
    assert {e["role"] for row in report["references"] for e in row["semantic_evidence"]} == {"identity", "scene"}
    assert [r["asset_id"] for r in report["references"]] == [b.asset_id for b in prepared.resolved_request.image_bindings]
    assert report["acceptance_requirements"]
    assert report["selected_route"]["resolved_generation_hash"] == prepared.resolved_request.resolved_generation_hash
    assert report["actual_quality"] == "NOT_EVALUATED"
    from test_production_seedance import _sealed_asset_resolver
    prepared.provider._input_reference = _sealed_asset_resolver(*prepared.resolved_request.image_bindings)
    native = prepared.provider._payload(prepared.resolved_request)
    assert [r["native_role"] for r in report["references"]] == [r["role"] for r in native["content"][1:]]


def test_reference_report_rejects_mismatched_requirement():
    from ai_video.production.video_reference_controls import video_reference_control_report
    from test_generation_feedback import feedback_setup
    setup, _, _, _, orchestrator = feedback_setup()
    prepared = orchestrator.prepare(limits=setup["inputs"].limits)
    wrong = prepared.execution_binding.projection.requirement.model_copy(update={"requirement_hash": "f" * 64})
    with pytest.raises(ValueError, match="exact compiled requirement"):
        video_reference_control_report(request=prepared.resolved_request, requirement=wrong)
