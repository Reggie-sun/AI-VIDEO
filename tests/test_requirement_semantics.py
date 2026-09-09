"""Simulated non-S01, provider-independent requirement admission regressions."""

import copy

import pytest

from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.hashing import canonical_sha256


def semantic_rule(requirement_id="signal", category="narrative_critical", level="acceptance"):
    hard = level == "acceptance"
    return dict(
        requirement_id=requirement_id, level=level, stage="raw_generation",
        dimension="signal", observable="The rescue signal is visible",
        tolerance="Any clear signal", measurement="Inspect source frames", proof="analyzer",
        intent_paths=[], production_owner="qa_acceptance",
        semantics=dict(version="requirement-semantics/1", category=category,
            intent_role="must_happen" if hard else "timing_target",
            source_refs=[dict(source_hash="a" * 64, locator="brief/rescue", intent_item_id="rescue",
                              quote="Show the rescue signal", origin="director_choice")],
            hard_basis=dict(kind="approved_narrative", source_hash="a" * 64,
                            locator="brief/rescue", necessity="The rescue must be understandable") if hard else None,
            derived_from=[]),
    )


def marked_policy(rules=None, **updates):
    rules = copy.deepcopy(rules or [semantic_rule()])
    payload = dict(domain_id="simulation", profile_id="rescue", profile_version="2",
        measurement_contract_version="1", requirement_semantics_version="requirement-semantics/1",
        generation_requirements=rules,
        required_requirement_ids=[r["requirement_id"] for r in rules if r["level"] == "acceptance"])
    payload.update(updates)
    digest = canonical_sha256(payload)
    return DomainAcceptancePolicy(**{k: payload[k] for k in (
        "domain_id", "profile_id", "profile_version", "measurement_contract_version", "required_requirement_ids")},
        profile_content_hash=digest, profile_payload={**payload, "content_hash": digest})


def test_marked_qa_accepts_complete_simulated_inventory():
    assert marked_policy().required_requirement_ids == ("signal",)


@pytest.mark.parametrize("mutation", ["missing", "unknown_version", "margin", "wrong_level", "omit_hard"])
def test_marked_qa_rejects_semantics_admission_gaps(mutation):
    rule = semantic_rule()
    updates = {}
    if mutation == "missing":
        rule.pop("semantics")
    elif mutation == "unknown_version":
        updates["requirement_semantics_version"] = "requirement-semantics/999"
    elif mutation == "margin":
        rule["semantics"]["source_refs"][0]["origin"] = "repair_margin"
    elif mutation == "wrong_level":
        rule["semantics"]["category"] = "directional_preference"
    else:
        updates["required_requirement_ids"] = ["unrelated"]
    with pytest.raises(ValueError):
        marked_policy([rule], **updates)


def test_removing_marker_does_not_enable_semantic_metadata_in_legacy_policy():
    with pytest.raises(ValueError):
        marked_policy(requirement_semantics_version=None)


def test_explicit_fixed_user_requirement_cannot_become_preference():
    rule = semantic_rule("early", "directional_preference", "recipe_hint")
    rule["semantics"]["source_refs"][0].update(origin="explicit_user", fixed=True)
    with pytest.raises(ValueError):
        marked_policy([semantic_rule(), rule])


def test_compound_atoms_keep_lineage_without_inheriting_verdicts():
    from ai_video.production.generation_recipe import RequirementExpression

    rules = [semantic_rule(), semantic_rule("motion", "quality_critical"),
             semantic_rule("early", "directional_preference", "recipe_hint"),
             semantic_rule("onset", "diagnostic_observation", "diagnostic"),
             semantic_rule("format", "governance")]
    for rule in rules:
        rule["semantics"]["derived_from"] = [dict(source_hash="b" * 64, locator="old/compound")]
    policy = marked_policy(rules)
    assert set(policy.required_requirement_ids) == {"signal", "motion", "format"}
    for rule in policy.profile_payload["generation_requirements"]:
        parsed = RequirementExpression.model_validate(rule)
        assert parsed.semantics.derived_from[0].locator == "old/compound"


def test_marked_compiler_skips_only_unexpressed_advisory_not_authored_intent():
    from ai_video.production.generation_feedback import _expressions
    from ai_video.production.generation_recipe import GenerationRecipe, expression_errors
    from test_production_generation_decision import setup_decision

    setup = setup_decision()
    requirement = setup["projection"].requirement
    hard = semantic_rule()
    hard["intent_paths"] = ["output_need.duration_seconds"]
    diagnostic = semantic_rule("onset", "diagnostic_observation", "diagnostic")
    diagnostic["intent_paths"] = ["not.a.provider.control"]
    hint = semantic_rule("early", "directional_preference", "recipe_hint")
    policy = marked_policy([hint, diagnostic, hard])
    recipe = setup["inputs"].candidates[0].recipe.model_copy(update=dict(
        acceptance_policy=policy, rubric_hash=policy.profile_content_hash,
        expressions=_expressions(policy, requirement)))
    recipe = GenerationRecipe.model_validate(recipe.model_dump(mode="python"))
    assert expression_errors(recipe, requirement, "") == ()
    bad = hard | {"intent_paths": ["missing.hard.path"]}
    policy = marked_policy([bad])
    recipe = recipe.model_copy(update=dict(acceptance_policy=policy, rubric_hash=policy.profile_content_hash,
                                         expressions=_expressions(policy, requirement)))
    assert "signal" in expression_errors(recipe, requirement, "")


@pytest.mark.parametrize("change", ["none", "observable", "proof", "reference"])
def test_marked_final_items_must_match_existing_final_owner(change):
    from ai_video.production.models import QaPolicy
    from test_production_final_output import viewing_policy

    qa = viewing_policy()
    rule = semantic_rule("natural", "quality_critical")
    rule.update(stage="final_composition", observable=qa.final_output.requirements[1].observable, proof="human")
    rule["semantics"]["source_refs"].append(dict(source_hash=qa.final_output.contract_hash, locator="natural",
        intent_item_id="natural", quote=rule["observable"], origin="director_choice"))
    if change == "observable":
        rule["observable"] = "A different predicate"
    elif change == "proof":
        rule["proof"] = "technical"
    elif change == "reference":
        rule["semantics"]["source_refs"][-1]["source_hash"] = "f" * 64
    payload = {**qa.model_dump(mode="json"), "generation_acceptance": marked_policy([rule])}
    if change == "none":
        assert QaPolicy.model_validate(payload).final_output == qa.final_output
        payload["final_output"] = None
    with pytest.raises(ValueError):
        QaPolicy.model_validate(payload)


def test_time_prose_cannot_disagree_with_typed_window_before_fetch():
    from test_generation_evaluation_binding import time_window

    spec = time_window()
    rule = semantic_rule()
    rule.update(measurement_spec=spec.model_dump(mode="json"), tolerance=spec.tolerance_text,
                measurement=spec.measurement_text)
    assert marked_policy([rule])
    assert "artifact_sha256" not in rule["measurement_spec"]
    rule["tolerance"] = "Before 2.2s"
    with pytest.raises(ValueError, match="canonical structured"):
        marked_policy([rule])


@pytest.mark.parametrize("shape", ["no_lineage", "no_hint_basis", "explicit_false"])
def test_optional_metadata_shapes_survive_qa_to_recipe_projection(shape):
    from ai_video.production.generation_feedback import _expressions
    from ai_video.production.generation_recipe import GenerationRecipe
    from test_production_generation_decision import setup_decision

    setup = setup_decision()
    rules = [semantic_rule("signal"), semantic_rule("early", "directional_preference", "recipe_hint")]
    if shape == "no_lineage":
        rules[0]["semantics"].pop("derived_from")
    elif shape == "no_hint_basis":
        rules[1]["semantics"].pop("hard_basis")
    else:
        rules[0]["semantics"]["source_refs"][0]["fixed"] = False
    policy = marked_policy(sorted(rules, key=lambda r: r["requirement_id"]))
    base = setup["inputs"].candidates[0].recipe
    recipe = GenerationRecipe.model_validate({**base.model_dump(mode="python"),
        "acceptance_policy": policy, "rubric_hash": policy.profile_content_hash,
        "expressions": _expressions(policy, setup["projection"].requirement)})
    assert recipe.acceptance_policy.model_dump(mode="json") == policy.model_dump(mode="json")
