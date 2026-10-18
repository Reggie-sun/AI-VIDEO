"""Responsibility previews use approved owners without changing production state."""

import json

import pytest

from ai_video.production.generation_recipe import RequirementExpression
from ai_video.production_planning import ProductionPlanningService
from production_strategy_factory import make_persisted_strategy_fixture
from test_requirement_semantics import marked_policy, semantic_rule
from test_production_requirement_allocation import _qa_policy


@pytest.mark.parametrize("subject,action,space", [
    ("Courier", "hands over a letter", "a platform"),
    ("Mechanic", "sets down a wrench", "a workshop"),
    ("Cook", "pours water", "a kitchen"),
])
def test_preview_preserves_fixed_results_and_bounds_model_freedom(subject, action, space):
    from ai_video.production.production_responsibility import requirement_responsibility

    required = semantic_rule()
    required["observable"] = f"{subject} {action} in {space}"
    required["semantics"]["source_refs"][0].update(origin="explicit_user", fixed=True)
    required["semantics"]["hard_basis"]["kind"] = "explicit_user"
    variation = semantic_rule("gesture", "directional_preference", "recipe_hint")
    variation["semantics"]["intent_role"] = "acceptable_variation"
    variation["observable"] = "Any natural free-hand gesture"
    rows = [requirement_responsibility(RequirementExpression.model_validate(rule))
            for rule in (required, variation)]

    assert rows[0]["model_freedom"] == "MUST_SATISFY"
    assert rows[0]["fixed_source_refs"][0]["fixed"] is True
    assert rows[0]["raw_acceptance_required"] is True
    assert rows[1]["model_freedom"] == "ALLOWED_WITHIN_AUTHORED_SCOPE"
    assert rows[1]["raw_acceptance_required"] is False
    assert rows[1]["semantics"]["intent_role"] == "acceptable_variation"


def test_legacy_missing_semantics_does_not_infer_permission_to_vary():
    from ai_video.production.production_responsibility import requirement_responsibility

    rule = semantic_rule()
    rule.pop("semantics")
    report = requirement_responsibility(RequirementExpression.model_validate(rule))
    assert report["model_freedom"] == "NOT_EVALUATED"
    assert report["raw_acceptance_required"] is True


def test_incomplete_legacy_rule_is_visible_without_inventing_executable_semantics():
    from ai_video.production.production_responsibility import production_responsibility_report
    from test_production_responsibility_admission import _acceptance

    legacy = _acceptance("legacy", ("result",), rows=({"requirement_id": "result"},))
    report = production_responsibility_report(qa_policy=_qa_policy(domain=legacy),
        qa_authority="selected_policy")
    assert report["requirements"][0]["requirement_definition"] == "NOT_EVALUATED"
    assert report["requirements"][0]["input_issues"] == ["invalid_rule_shape"]
    assert report["actual_quality"] == "NOT_EVALUATED"


def test_direct_preflight_does_not_assign_global_qa_when_no_authored_shots_are_supplied():
    from ai_video.canvas_preflight import canvas_reference_preflight
    from scripts.canvas_production_source import inspect_canvas_source
    from test_canvas_project_data import text_data

    source, definition = text_data()
    inspection = inspect_canvas_source(source, definition["selection"])
    packet = inspection["selection"]["sequence_packet"]
    # The normal authoring fixture supplies already validated source/direction.
    from test_canvas_authoring import direction
    from ai_video.canvas_authoring import author_canvas_project

    data = direction()
    bundle = author_canvas_project(packet=packet, direction=data)
    report = canvas_reference_preflight(packet=packet, direction=data, registry=bundle.registry,
        qa_policy=_qa_policy(domain=marked_policy()))
    assert all(row["production_control"]["binding"] == "REQUIRES_PRODUCTION_INTENT"
               for row in report["shots"])
    assert all(row["production_control"]["requirements"] == [] for row in report["shots"])


@pytest.mark.parametrize("stage", ["shot_editorial", "final_composition"])
def test_post_result_remains_required_without_claiming_model_input(stage):
    from ai_video.production.production_responsibility import requirement_responsibility

    rule = semantic_rule("cut-time")
    rule.update(stage=stage, observable="The action completes before the final cut")
    report = requirement_responsibility(RequirementExpression.model_validate(rule))
    assert report["model_freedom"] == "MUST_SATISFY"
    assert report["raw_input_expected"] is False
    assert report["raw_acceptance_required"] is False
    assert report["responsibility_stage"] == stage


def test_preview_carries_exact_edit_map_without_recomputing_timing(tmp_path):
    from ai_video.production.production_responsibility import production_responsibility_report
    from test_production_strategy_materialization import _loaded_with_mapped_video
    from test_production_strategy_resolver import resolve

    loaded, time_map = _loaded_with_mapped_video(tmp_path)
    decision = resolve(loaded)
    report = production_responsibility_report(qa_policy=loaded.qa_policy, shot=loaded.shots[0],
        decision=decision, qa_authority="selected_policy")
    assert report["strategy"]["units"][0]["source"]["source_time_map"] == time_map.model_dump(mode="json")
    assert "EDIT_EXISTING_VIDEO" in report["strategy"]["candidates"][0]["operations"]
    assert report["actual_quality"] == "NOT_EVALUATED"


def test_preview_keeps_unsupported_repair_as_capability_blocker(tmp_path):
    from ai_video.production.production_responsibility import production_responsibility_report
    from ai_video.production.production_strategy_contracts import ProductionOperation as Op
    from test_production_strategy_resolver import qualified_context, resolve

    loaded = qualified_context(tmp_path)
    parent = loaded.shots[0]
    intent = parent.production_intent
    coverage = intent.coverage_options[0]
    unit = coverage.units[0].model_copy(update={"required_operations": (Op.MASK_COMPOSITE,)})
    parent = parent.model_copy(update={"production_intent": intent.model_copy(update={
        "allowed_operations": (*intent.allowed_operations, Op.MASK_COMPOSITE),
        "coverage_options": (coverage.model_copy(update={"units": (unit,)}),)})})
    loaded = loaded.model_copy(update={"shots": (parent, *loaded.shots[1:])})
    decision = resolve(loaded)
    report = production_responsibility_report(qa_policy=loaded.qa_policy, shot=parent, decision=decision)
    assert report["strategy"]["selected_candidate_hash"] is None
    assert any("MASK_COMPOSITE" in reason for reason in report["strategy"]["reasons"])
    assert report["actual_quality"] == "NOT_EVALUATED"


def test_prepare_control_envelope_retains_exact_decision_and_manifest(tmp_path):
    fixture = make_persisted_strategy_fixture(tmp_path)
    service = ProductionPlanningService(committer=fixture.committer)
    before = (tmp_path / "state/manifest.json").read_bytes()
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)

    result = service.prepare(parent_shot_id=fixture.parent_shot_id, include_control_report=True)

    assert result["decision"] == decision.model_dump(mode="json")
    control = result["production_control"]
    assert control["qa_authority"] == "selected_policy"
    assert control["binding"] == "DECLARED_PRODUCTION_INTENT"
    assert control["allocations"][0]["issues"] == []
    assert control["strategy"]["selected_candidate_hash"] == decision.selected.candidate_hash
    assert control["strategy"]["units"][0]["source"] == decision.selected.units[0].source.model_dump(mode="json")
    assert control["actual_quality"] == "NOT_EVALUATED"
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_preflight_candidate_qa_is_unapproved_and_not_assigned_to_every_shot(tmp_path):
    from scripts.canvas_production import run
    from test_canvas_project_data import text_data

    source, definition = text_data()
    (tmp_path / "source.json").write_text(json.dumps(source))
    (tmp_path / "project.json").write_text(json.dumps(definition))
    qa = _qa_policy(domain=marked_policy())
    (tmp_path / "qa.json").write_text(qa.model_dump_json())
    root = tmp_path / "production"
    root.mkdir()

    report = run(data_path=tmp_path / "project.json", project_root=root, action="preflight",
        runtime_factory="never_imported:provider", arguments={"qa_policy": "qa.json"})

    assert report["production_control"]["qa_authority"] == "candidate_not_approved"
    assert report["production_control"]["requirements"][0]["requirement_id"] == "signal"
    assert all(row["production_control"]["binding"] == "REQUIRES_PRODUCTION_INTENT"
               for row in report["shots"])
    assert all(row["production_control"]["requirements"] == [] for row in report["shots"])
    assert list(root.iterdir()) == []


def test_preflight_does_not_allow_candidate_qa_path_to_escape_data_root(tmp_path):
    from scripts.canvas_production import run
    from test_canvas_project_data import text_data

    source, definition = text_data()
    data = tmp_path / "data"
    data.mkdir()
    (data / "source.json").write_text(json.dumps(source))
    (data / "project.json").write_text(json.dumps(definition))
    (tmp_path / "qa.json").write_text(_qa_policy(domain=marked_policy()).model_dump_json())
    root = tmp_path / "production"
    root.mkdir()
    with pytest.raises((ValueError, OSError)):
        run(data_path=data / "project.json", project_root=root, action="preflight",
            arguments={"qa_policy": "../qa.json"})
    assert list(root.iterdir()) == []
