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
    assert controls["whitebox_motion"]["mechanism"] == "UNBOUND"
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


def test_reference_preview_is_per_requirement_and_legacy_input_coverage_stays_unknown():
    from ai_video.production.video_reference_controls import prepared_generation_report
    from test_generation_feedback import feedback_setup

    setup, _, _, _, orchestrator = feedback_setup()
    prepared = orchestrator.prepare(limits=setup["inputs"].limits)
    selected = next(c for c in prepared.inputs.candidates
                    if c.candidate_id == prepared.decision.selected_candidate_id)
    report = prepared_generation_report(prepared)["reference_control"]

    objectives = report["objectives"]
    assert [row["requirement_id"] for row in objectives] == [
        rule.requirement_id for rule in selected.recipe.expressions]
    for row, rule in zip(objectives, selected.recipe.expressions, strict=True):
        assert row["observable"] == rule.observable
        assert row["level"] == rule.level
        assert row["stage"] == rule.stage
        assert row["proof"] == rule.proof
        assert row["measurement"] == rule.measurement
        assert row["tolerance"] == rule.tolerance
        assert row["intent_paths"] == list(rule.intent_paths)
        assert row["native_text"] == list(rule.native_text)
        assert row["native_text_present"] is all(text in prepared.resolved_request.prompt_text
                                                   for text in rule.native_text)
        assert row["input_coverage"] == "NOT_EVALUATED"
        assert row["actual_quality"] == "NOT_EVALUATED"

    assert report["controls_scope"] == "MODE_OVERVIEW_ONLY"
    assert len(report["controls"]) == 6
    assert all(row["actual_quality"] == "NOT_EVALUATED" for row in report["controls"])


def test_reference_preview_reads_nested_action_and_motion_intent_paths():
    from ai_video.production.video_reference_controls import video_reference_control_report
    from test_generation_feedback import feedback_setup

    setup, _, _, _, orchestrator = feedback_setup()
    prepared = orchestrator.prepare(limits=setup["inputs"].limits)
    requirement = prepared.execution_binding.projection.requirement
    intent = requirement.generation_intent
    source = prepared.inputs.candidates[0].recipe.expressions[0]
    rule = source.model_copy(update={"intent_paths": (
        "generation_intent.subject_action.endpoint", "generation_intent.motion_envelope",
        "generation_intent.pacing"), "native_text": ("Generate 4 seconds.",)})
    report = video_reference_control_report(request=prepared.resolved_request,
        requirement=requirement, expressions=(rule,))

    row = report["objectives"][0]
    assert row["intent_values"]["generation_intent.subject_action.endpoint"] == \
        intent.subject_action.endpoint.model_dump(mode="json")
    assert row["intent_values"]["generation_intent.motion_envelope"] == \
        intent.motion_envelope.model_dump(mode="json")
    assert row["intent_values"]["generation_intent.pacing"] == intent.pacing.model_dump(mode="json")


def test_reference_preview_resolves_numeric_intent_path_segments():
    from types import SimpleNamespace

    from ai_video.production.video_reference_controls import video_reference_control_report
    from test_generation_feedback import feedback_setup

    setup, _, _, _, orchestrator = feedback_setup()
    prepared = orchestrator.prepare(limits=setup["inputs"].limits)
    requirement = SimpleNamespace(requirement_hash=prepared.resolved_request.requirement_hash,
        asset_evidence=(), characters=(), generation_intent={"subjects": [{"name": "Courier"}]})
    source = prepared.inputs.candidates[0].recipe.expressions[0]
    rule = source.model_copy(update={"intent_paths": ("generation_intent.subjects.0.name",)})

    row = video_reference_control_report(request=prepared.resolved_request,
        requirement=requirement, expressions=(rule,))["objectives"][0]
    assert row["intent_values"] == {"generation_intent.subjects.0.name": "Courier"}


def test_declared_input_mapping_uses_shared_issues_without_claiming_quality():
    from ai_video.production.generation_input_control import GenerationInputControl
    from ai_video.production.video_reference_controls import video_reference_control_report
    from test_generation_feedback import feedback_setup

    setup, _, _, _, orchestrator = feedback_setup()
    prepared = orchestrator.prepare(limits=setup["inputs"].limits)
    requirement = prepared.execution_binding.projection.requirement
    source = prepared.inputs.candidates[0].recipe.expressions[0]
    exact_text = prepared.resolved_request.prompt_text
    control = GenerationInputControl(mechanism="prompt_guidance")
    rule = source.model_copy(update={"intent_paths": ("generation_intent.pacing",),
        "native_text": (exact_text,), "input_control": control})

    report = video_reference_control_report(request=prepared.resolved_request,
        requirement=requirement, expressions=(rule,))
    row = report["objectives"][0]
    assert row["input_coverage"] == "EXPRESSED_INPUT_ONLY"
    assert row["input_issues"] == []
    assert row["mechanism"] == "MODEL_GUIDANCE"
    assert row["native_text_present"] is True
    assert row["actual_quality"] == "NOT_EVALUATED"

    missing = rule.model_copy(update={"native_text": ("uncompiled invented clause",)})
    rejected = video_reference_control_report(request=prepared.resolved_request,
        requirement=requirement, expressions=(missing,))["objectives"][0]
    assert rejected["input_coverage"] == "UNSUPPORTED_INPUT"
    assert rejected["input_issues"] == ["MISSING_NATIVE_FRAGMENT"]
    assert rejected["actual_quality"] == "NOT_EVALUATED"


def test_reference_duty_joins_exact_asset_hash_binding_and_semantic_owner(tmp_path):
    from ai_video.production.generation_input_control import GenerationInputControl, ReferenceDuty
    from ai_video.production.video_reference_controls import prepared_generation_report
    from test_canvas_source_expression import subject_service

    service, limits = subject_service(tmp_path)
    prepared = service.prepare(limits=limits)
    requirement = prepared.execution_binding.projection.requirement
    reference = next(e for e in requirement.asset_evidence
        if e.role.value == "scene" and any(
            b.asset_id == e.asset_id and b.asset_sha256 == e.asset_sha256
            for b in prepared.resolved_request.image_bindings))
    prompt = prepared.resolved_request.prompt_text
    duty = ReferenceDuty(asset_id=reference.asset_id, asset_sha256=reference.asset_sha256,
        role=reference.role.value, purpose="whitebox", scope_text=prompt,
        canonical_owner_id=reference.canonical_owner_id)
    selected = next(c for c in prepared.inputs.candidates
        if c.candidate_id == prepared.decision.selected_candidate_id)
    source = selected.recipe.expressions[0]
    rule = source.model_copy(update={"intent_paths": ("generation_intent.subject_action.progression",),
        "native_text": (prompt,), "input_control": GenerationInputControl(
            mechanism="reference_guidance", references=(duty,))})
    selected = selected.model_copy(update={"recipe": selected.recipe.model_copy(
        update={"expressions": (rule,)})})
    inputs = prepared.inputs.model_copy(update={"candidates": (selected,)})
    decision = prepared.decision.model_copy(update={"selected_candidate_id": selected.candidate_id})
    prepared = replace(prepared, inputs=inputs, decision=decision)

    report = prepared_generation_report(prepared)["reference_control"]
    row = report["objectives"][0]
    reference_row = row["reference_duties"][0]
    assert row["input_coverage"] == "EXPRESSED_INPUT_ONLY"
    assert row["mechanism"] == "MODEL_REFERENCE"
    assert reference_row["asset_id"] == reference.asset_id
    assert reference_row["asset_sha256"] == reference.asset_sha256
    assert len(reference_row["native_bindings"]) == 1
    assert reference_row["native_bindings"][0]["native_path"].startswith("content[")
    assert reference_row["native_bindings"][0]["mime_type"] == "image/png"
    assert reference_row["scope_text"] == prompt
    assert reference_row["whitebox_disposition"] == "MODEL_REFERENCE"
    assert reference_row["mime_types"] == ["image/png"]
    assert reference_row["whitebox_intent"] == "STATIC_LAYOUT"
    assert reference_row["whitebox_quality"] == "NOT_EVALUATED"
    assert reference_row["semantic_evidence"][0]["canonical_owner_id"] == reference.canonical_owner_id
    assert next(row for row in report["controls"] if row["target"] == "whitebox_motion")[
        "mechanism"] == "UNBOUND"


def test_video_binding_is_whitebox_only_with_explicit_whitebox_duty():
    from types import SimpleNamespace

    from ai_video.production.generation_input_control import GenerationInputControl, ReferenceDuty
    from ai_video.production.video import VideoGenerationMode, VideoGenerationRequest, VideoMediaReferenceBinding
    from ai_video.production.video_reference_controls import video_reference_control_report
    from ai_video.production.video_requirement import AssetEvidence
    from ai_video.production.generation_recipe import RequirementExpression
    from test_production_minimax_h3_max import _setup

    provider, resolved, _, _, _ = _setup(aspect_ratio="adaptive")
    original = resolved.activation_scope.request
    binding = VideoMediaReferenceBinding(kind="video", role="reference_video",
        asset_id="layout-motion", asset_sha256="d" * 64, mime_type="video/mp4",
        size_bytes=128, duration_millis=4000, width=1280, height=720, fps=24)
    request = VideoGenerationRequest.create(**original.model_dump(mode="python",
        exclude={"request_input_hash", "image_bindings", "media_bindings", "mode", "prompt_text"}),
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO, image_bindings=original.image_bindings,
        media_bindings=(binding,), prompt_text="A camera glides past the empty room.")
    request = provider.resolve(request)
    evidence = AssetEvidence(role="video_reference", asset_id=binding.asset_id,
        asset_sha256=binding.asset_sha256, mime_type=binding.mime_type, size_bytes=binding.size_bytes,
        width=binding.width, height=binding.height, duration_millis=binding.duration_millis,
        fps=binding.fps)
    requirement = SimpleNamespace(requirement_hash=request.requirement_hash,
        asset_evidence=(evidence,), characters=(), generation_intent=SimpleNamespace(
            performance_intent=None, model_dump=lambda mode: {}))
    prompt = request.prompt_text

    def report(purpose, role="video_reference"):
        duty = ReferenceDuty(asset_id=binding.asset_id, asset_sha256=binding.asset_sha256,
            role=role, purpose=purpose, scope_text=prompt)
        rule = RequirementExpression(requirement_id="camera-motion", level="acceptance",
            stage="raw_generation", dimension="camera", observable="camera motion follows the reference",
            tolerance="same direction", measurement="frame review", proof="human",
            intent_paths=("generation_intent.subject_action.progression",), native_text=(prompt,),
            production_owner="shot_authoring", input_control=GenerationInputControl(
                mechanism="reference_guidance", references=(duty,)))
        return video_reference_control_report(request=request, requirement=requirement,
            expressions=(rule,))

    ordinary_video = report("motion")
    assert ordinary_video["controls"][5]["mechanism"] == "UNBOUND"
    assert ordinary_video["objectives"][0]["input_coverage"] == "EXPRESSED_INPUT_ONLY"

    explicit_whitebox = report("whitebox")
    assert explicit_whitebox["controls"][5]["mechanism"] == "MODEL_REFERENCE"
    assert explicit_whitebox["objectives"][0]["reference_duties"][0]["native_bindings"][0][
        "native_role"] == "reference_video"

    wrong_semantic_role = report("whitebox", role="scene")["objectives"][0]
    assert wrong_semantic_role["input_coverage"] == "UNSUPPORTED_INPUT"
    assert wrong_semantic_role["reference_duties"][0]["native_bindings"] == []


def test_uncompiled_selected_candidate_keeps_qa_targets_without_inventing_request():
    from ai_video.production.generation_feedback import PreparedGeneration
    from ai_video.production.video_compiler import ProviderRequirementUnsupported, ProviderRequirementUnsupportedReason
    from ai_video.production.video_reference_controls import prepared_generation_report
    from test_generation_feedback import feedback_setup

    setup, _, _, _, orchestrator = feedback_setup()
    prepared = orchestrator.prepare(limits=setup["inputs"].limits)
    selected = next(c for c in prepared.inputs.candidates
        if c.candidate_id == prepared.decision.selected_candidate_id)
    rule = selected.recipe.expressions[0]
    unsupported_path = rule.requirement_id
    unsupported = ProviderRequirementUnsupported(requirement_hash=selected.recipe.requirement_hash,
        provider_bound_request_hash="c" * 64, selected_capability_id=selected.capability_id,
        reason=ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED,
        unsupported_field_paths=(unsupported_path,))
    stopped = PreparedGeneration(prepared.inputs, prepared.decision, compilation=unsupported)

    result = prepared_generation_report(stopped)
    report = result["reference_control"]
    assert report["selected_route"] == "NOT_EVALUATED"
    assert report["native_parameters"] == "NOT_EVALUATED"
    assert len(report["objectives"]) == len(selected.recipe.expressions)
    affected = next(row for row in report["objectives"] if row["requirement_id"] == rule.requirement_id)
    assert affected["input_coverage"] == "UNSUPPORTED_INPUT"
    assert affected["native_text_present"] == "AUTHORED_NOT_COMPILED"
    assert result["router_assessments"] == [a.model_dump(mode="json") for a in prepared.decision.assessments]


def test_same_asset_opening_and_closing_duties_join_only_their_native_role():
    from types import SimpleNamespace

    from ai_video.production.generation_input_control import GenerationInputControl, ReferenceDuty
    from ai_video.production.generation_recipe import RequirementExpression
    from ai_video.production.video import VideoGenerationMode, VideoGenerationRequest
    from ai_video.production.video_reference_controls import video_reference_control_report
    from ai_video.production.video_requirement import AssetEvidence
    from test_production_minimax_h3_max import _setup

    provider, resolved, _, transport, _ = _setup(aspect_ratio="adaptive")
    original = resolved.activation_scope.request
    first = original.image_bindings[0].model_copy(update={"role": "first_frame"})
    last = first.model_copy(update={"role": "last_frame"})
    request = VideoGenerationRequest.create(**original.model_dump(mode="python",
        exclude={"request_input_hash", "image_bindings", "mode"}),
        image_bindings=(first, last), mode=VideoGenerationMode.IMAGE_TO_VIDEO)
    resolved = provider.resolve(request)
    evidence = tuple(AssetEvidence(**binding.model_dump(mode="python")) for binding in (first, last))
    requirement = SimpleNamespace(requirement_hash=resolved.requirement_hash, asset_evidence=evidence,
        characters=(), generation_intent=None,
        semantic_reference_roles=tuple(item.role for item in evidence))
    rules = tuple(RequirementExpression(requirement_id=role, level="acceptance", stage="raw_generation",
        dimension="composition", observable="The authored endpoint image is supplied.",
        tolerance="exact input", measurement="observe output separately", proof="technical",
        intent_paths=("semantic_reference_roles",), native_text=(), production_owner="qa_acceptance",
        input_control=GenerationInputControl(mechanism=role, references=(ReferenceDuty(
            asset_id=first.asset_id, asset_sha256=first.asset_sha256, role=role, purpose=purpose),)))
        for role, purpose in (("first_frame", "opening"), ("last_frame", "closing")))

    report = video_reference_control_report(request=resolved, requirement=requirement, expressions=rules)

    for position, row in enumerate(report["objectives"], 1):
        bindings = row["reference_duties"][0]["native_bindings"]
        assert [(binding["native_path"], binding["native_role"]) for binding in bindings] == [
            (f"content[{position}]", row["requirement_id"])]
    assert transport.calls == []
