"""Canonical Canvas authoring reaches exact selected native input without effects."""
from copy import deepcopy

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.performance_direction import render_performance_direction
from ai_video.production.video_reference_controls import prepared_generation_report
from test_canvas_source_expression import subject_service


@pytest.mark.parametrize("provider_family", ["seedance", "h3-max"])
@pytest.mark.parametrize("scenario", [
    ("Robot", "raises both arms", "an atrium"),
    ("Courier", "sets a parcel down", "a station platform"),
    ("Scientist", "turns toward the window", "a narrow cabin"),
])
def test_agent_authored_performance_reaches_actual_selected_compiler(tmp_path, provider_family, scenario):
    from ai_video.production.project import load_production_project
    from ai_video.canvas_preflight import canvas_reference_preflight

    service, limits = subject_service(tmp_path, scenario=scenario, provider_family=provider_family,
        generation_output_duration_seconds=5)
    loaded = load_production_project(service.committer.project_root / "project.yaml")
    preview = canvas_reference_preflight(packet=service.packet, direction=service.direction,
        registry=loaded.registry, authored_shots=loaded.shots)
    assert preview["shots"][0]["performance_control"]["authoring_status"] == "AUTHORED"
    before = (service.committer.project_root / "state/manifest.json").read_bytes()
    prepared = service.prepare(limits=limits)
    assert prepared.execution_binding is not None, prepared.compilation
    intent = prepared.execution_binding.projection.requirement.generation_intent
    assert intent.performance_intent.character_directions[0].screen_identity == scenario[0]
    block = render_performance_direction(intent)
    assert block in prepared.resolved_request.prompt_text
    report = prepared_generation_report(prepared)["reference_control"]["performance_control"]
    assert report["input_expression"] == "LEXICALLY_EXPRESSED"
    assert report["acceptance_mapping"] == "DECLARED"
    assert report["actual_quality"] == "NOT_EVALUATED"
    assert (service.committer.project_root / "state/manifest.json").read_bytes() == before


@pytest.mark.parametrize("damage", ["missing", "background_missing", "unexpressed"])
def test_missing_or_unexpressed_actor_direction_stops_before_any_effect(tmp_path, damage):
    service, limits = subject_service(tmp_path)
    data = deepcopy(service.direction)
    if damage == "missing":
        data["shots"][0]["generation"]["generation_intent"].pop("performance_intent")
    elif damage == "background_missing":
        data["characters"].append({"character_id": "visitor", "name": "Visitor",
            "identity": "a visitor by the doorway", "appearance_bible": "a gray coat"})
        data["shots"][0]["shot"]["character_ids"].append("visitor")
    else:
        data["shots"][0]["generation"]["generation_intent"]["performance_intent"][
            "character_directions"][0]["beats"][0]["facial_expression"] = "new eye lights deliberately dim"
    service.direction = data
    service.revise_authoring(attempt_id="performance-authored-revision")
    if damage == "background_missing":
        from ai_video.canvas_preflight import canvas_reference_preflight

        loaded = service._load()
        preview = canvas_reference_preflight(packet=service.packet, direction=service.direction,
            registry=loaded.registry, authored_shots=loaded.shots)
        control = preview["shots"][0]["performance_control"]
        assert control["authoring_status"] == "INCOMPLETE"
        assert any("visitor" in issue for issue in control["issues"])
    before = (service.committer.project_root / "state/manifest.json").read_bytes()
    # The new visitor also lacks identity input, so the existing Planner may
    # reject it first; preflight above must still identify the acting gap.
    with pytest.raises(AiVideoError, match=None if damage == "background_missing" else "performance"):
        service.prepare(limits=limits)
    assert (service.committer.project_root / "state/manifest.json").read_bytes() == before


def test_authored_parameter_without_selected_performance_acceptance_cannot_generate(tmp_path):
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.generation_recipe import RequirementExpression
    from test_production_generation_decision import acceptance_policy

    service, limits = subject_service(tmp_path)
    loaded = service._load()
    acceptance = loaded.qa_policy.selected_generation_acceptance()
    duration = next(rule for rule in acceptance.profile_payload["generation_requirements"]
        if rule["requirement_id"] == "duration")
    revised = seal_artifact(loaded.qa_policy.model_copy(update={
        "revision": loaded.qa_policy.revision + 1, "content_hash": "0" * 64,
        "generation_acceptance": acceptance_policy((RequirementExpression.model_validate(duration),)),
    }))
    service.committer.activate_qa_policy(revised, attempt_id="remove-acting-acceptance",
        expected_manifest_revision=loaded.manifest.manifest_revision)
    before = (service.committer.project_root / "state/manifest.json").read_bytes()
    with pytest.raises(AiVideoError, match="acceptance"):
        service.prepare(limits=limits)
    assert (service.committer.project_root / "state/manifest.json").read_bytes() == before
