"""The native compiler receives only objectives owned by raw generation."""

from types import SimpleNamespace

import pytest


def test_expression_projection_keeps_only_raw_non_diagnostic_intent_fragments():
    from ai_video.production.generation_feedback import _expressions
    from test_production_generation_decision import setup_decision

    requirement = setup_decision()["projection"].requirement
    intent = requirement.generation_intent.model_copy(update={
        "subject_action": requirement.generation_intent.subject_action.model_copy(update={
            "progression": "A courier places a parcel on the counter, then steps back.",
        }),
    })
    requirement = requirement.model_copy(update={"generation_intent": intent})
    shared = {
        "dimension": "action_timing",
        "observable": "The authored target remains available for its owning stage.",
        "tolerance": "preserve the authored target",
        "measurement": "inspect the exact input for the owning stage",
        "proof": "technical",
        "intent_paths": ["generation_intent.subject_action.progression"],
        "native_text": [],
        "production_owner": "qa_acceptance",
    }
    inventory = (
        {**shared, "requirement_id": "raw-action", "level": "acceptance", "stage": "raw_generation"},
        {**shared, "requirement_id": "raw-preference", "level": "recipe_hint", "stage": "raw_generation"},
        {**shared, "requirement_id": "editorial-cut", "level": "acceptance", "stage": "shot_editorial"},
        {**shared, "requirement_id": "final-review", "level": "diagnostic", "stage": "final_composition"},
        {**shared, "requirement_id": "raw-diagnostic", "level": "diagnostic", "stage": "raw_generation"},
    )
    acceptance = SimpleNamespace(profile_payload={"generation_requirements": inventory})

    projected = {rule.requirement_id: rule for rule in _expressions(acceptance, requirement)}

    authored_action = "A courier places a parcel on the counter, then steps back."
    assert projected["raw-action"].native_text == (authored_action,)
    assert projected["raw-preference"].native_text == (authored_action,)
    assert projected["editorial-cut"].native_text == ()
    assert projected["final-review"].native_text == ()
    assert projected["raw-diagnostic"].native_text == ()


def _with_final_preference(acceptance):
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.hashing import canonical_sha256

    payload = dict(acceptance.profile_payload)
    payload.pop("content_hash", None)
    payload["requirement_semantics_version"] = "requirement-semantics/1"

    def semantics(rule):
        requirement_id = rule["requirement_id"]
        source_hash = canonical_sha256({"fixture_source": requirement_id})
        source_ref = {
            "source_hash": source_hash,
            "locator": f"fixture/{requirement_id}",
            "intent_item_id": requirement_id,
            "quote": f"Fixture intent for {requirement_id}.",
            "origin": "explicit_user",
        }
        if rule["level"] == "acceptance":
            return {
                "version": "requirement-semantics/1",
                "category": "quality_critical",
                "intent_role": "must_happen",
                "source_refs": [source_ref],
                "hard_basis": {
                    "kind": "explicit_user",
                    "source_hash": source_hash,
                    "locator": source_ref["locator"],
                    "necessity": f"The fixture checks {requirement_id} as a required result.",
                },
                "derived_from": [],
            }
        return {
            "version": "requirement-semantics/1",
            "category": "directional_preference",
            "intent_role": "acceptable_variation",
            "source_refs": [{**source_ref, "origin": "director_choice"}],
            "hard_basis": None,
            "derived_from": [],
        }

    payload["generation_requirements"] = tuple(
        {**dict(rule), "semantics": semantics(rule)}
        for rule in payload["generation_requirements"]
    )
    preference = {
        "requirement_id": "final-transition-preference",
        "level": "recipe_hint",
        "stage": "final_composition",
        "dimension": "editorial_transition",
        "observable": "Prefer a cut at the authored transition.",
        "tolerance": "directional preference only",
        "measurement": "review the assembled sequence",
        "proof": "human",
        "intent_paths": ["generation_intent.subject_action.progression"],
        "native_text": [],
        "production_owner": "final_output",
    }
    preference["semantics"] = semantics(preference)
    payload["generation_requirements"] = tuple(sorted(
        (*payload["generation_requirements"], preference), key=lambda item: item["requirement_id"]
    ))
    digest = canonical_sha256(payload)
    fields = acceptance.model_dump(mode="python")
    fields.update(profile_content_hash=digest, profile_payload={**payload, "content_hash": digest})
    return DomainAcceptancePolicy.model_validate(fields)


def _with_unmarked_raw_diagnostic(acceptance):
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.hashing import canonical_sha256

    payload = dict(acceptance.profile_payload)
    payload.pop("content_hash", None)
    assert "requirement_semantics_version" not in payload
    diagnostic = {
        "requirement_id": "diagnostic-action-observation",
        "level": "diagnostic",
        "stage": "raw_generation",
        "dimension": "action_observation",
        "observable": "Observe how the camera moves in the generated result.",
        "tolerance": "observation only",
        "measurement": "inspect the submitted source frames",
        "proof": "analyzer",
        "intent_paths": ["generation_intent.camera_intent.movement"],
        "native_text": [],
        "production_owner": "diagnostic_observation",
    }
    payload["generation_requirements"] = tuple(sorted(
        (*payload["generation_requirements"], diagnostic), key=lambda item: item["requirement_id"]
    ))
    digest = canonical_sha256(payload)
    fields = acceptance.model_dump(mode="python")
    fields.update(profile_content_hash=digest, profile_payload={**payload, "content_hash": digest})
    return DomainAcceptancePolicy.model_validate(fields)


def _prepared_with_acceptance(service, limits, acceptance):
    orchestrator = service._orchestrator(service.direction["shots"][0])
    current = orchestrator.context_loader()
    orchestrator.context_loader = lambda: {**current, "acceptance": acceptance}
    return orchestrator.prepare(limits=limits)


@pytest.mark.parametrize("provider_family", ["h3-max", "seedance"])
def test_unmarked_raw_diagnostic_does_not_block_or_become_native_input_or_required(
    tmp_path, provider_family
):
    from test_generation_input_control import _canvas_control_service
    from ai_video.production.generation_recipe import expression_errors
    from ai_video.production.video_reference_controls import prepared_generation_report

    service, limits, _, _, _ = _canvas_control_service(
        tmp_path,
        scenario=("Courier", "sets a parcel down", "a station platform"),
        provider_family=provider_family,
    )
    current = service._orchestrator(service.direction["shots"][0]).context_loader()
    acceptance = _with_unmarked_raw_diagnostic(current["acceptance"])
    before_attempts = tuple(item.attempt_id for item in service._load().manifest.attempts)

    prepared = _prepared_with_acceptance(service, limits, acceptance)

    assert prepared.compilation.outcome == "compiled"
    recipe = prepared.execution_binding.decision.routing.provider_bound_request.generation_recipe
    diagnostic = next(item for item in recipe.expressions
                      if item.requirement_id == "diagnostic-action-observation")
    assert diagnostic.level == "diagnostic"
    assert diagnostic.native_text == ()
    assert diagnostic.requirement_id not in acceptance.required_requirement_ids
    assert expression_errors(
        SimpleNamespace(expressions=(diagnostic,)),
        prepared.execution_binding.projection.requirement,
        prepared.resolved_request.prompt_text,
        control_paths=("generation_intent.pacing.shot_duration_seconds",),
    ) == ()
    assert prepared.resolved_request.prompt_text == service.direction["shots"][0]["shot"]["intent"]
    row = next(item for item in prepared_generation_report(prepared)["reference_control"]["objectives"]
               if item["requirement_id"] == diagnostic.requirement_id)
    assert row["raw_acceptance_required"] is False
    assert row["raw_input_expected"] is False
    assert not any(item.operation == "video_generation" for item in service._load().manifest.attempts)
    assert tuple(item.attempt_id for item in service._load().manifest.attempts) == before_attempts


@pytest.mark.parametrize("provider_family", ["h3-max", "seedance"])
def test_unmarked_diagnostic_does_not_hide_missing_raw_fragment(
    tmp_path, provider_family
):
    from test_generation_input_control import _canvas_control_service
    from ai_video.production.video_compiler import (
        ProviderRequirementUnsupported,
        ProviderRequirementUnsupportedReason,
    )

    service, limits, _, _, _ = _canvas_control_service(
        tmp_path,
        scenario=("Courier", "sets a parcel down", "a station platform"),
        provider_family=provider_family,
        missing_fragment=True,
    )
    current = service._orchestrator(service.direction["shots"][0]).context_loader()
    acceptance = _with_unmarked_raw_diagnostic(current["acceptance"])

    prepared = _prepared_with_acceptance(service, limits, acceptance)

    assert isinstance(prepared.compilation, ProviderRequirementUnsupported)
    assert prepared.compilation.reason is ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED
    assert prepared.compilation.unsupported_field_paths == ("action-deadline",)
    assert prepared.execution_binding is None
    assert not any(item.operation == "video_generation" for item in service._load().manifest.attempts)


@pytest.mark.parametrize("scenario", [
    ("Courier", "sets a parcel down", "a station platform"),
    ("Mechanic", "tightens a valve and checks it", "an engine room"),
    ("Cook", "pours tea into a cup", "a small kitchen"),
])
@pytest.mark.parametrize("provider_family", ["h3-max", "seedance"])
def test_nonraw_preference_stays_out_of_prepared_native_compilation(
    tmp_path, scenario, provider_family
):
    from test_generation_input_control import _canvas_control_service

    service, limits, _, _, raw_fragments = _canvas_control_service(
        tmp_path, scenario=scenario, provider_family=provider_family
    )
    row = service.direction["shots"][0]
    orchestrator = service._orchestrator(row)
    current = orchestrator.context_loader()
    acceptance = _with_final_preference(current["acceptance"])
    orchestrator.context_loader = lambda: {**current, "acceptance": acceptance}

    before_attempts = tuple(item.attempt_id for item in service._load().manifest.attempts)
    prepared = orchestrator.prepare(limits=limits)

    assert prepared.compilation.outcome == "compiled"
    assert prepared.resolved_request.prompt_text == service.direction["shots"][0]["shot"]["intent"]
    assert "Prefer a cut at the authored transition." not in prepared.resolved_request.prompt_text
    assert prepared.resolved_request.adapter_compiler_id == (
        "minimax-h3-max-video-compiler" if provider_family == "h3-max" else "seedance-video-compiler"
    )
    recipe = prepared.execution_binding.decision.routing.provider_bound_request.generation_recipe
    rules = {item.requirement_id: item for item in recipe.expressions}
    assert rules["action-deadline"].native_text == raw_fragments["action-deadline"]
    assert rules["main-identity"].input_control.references[0].asset_id == "robot-main"
    assert rules["aux-identity"].input_control.references[0].asset_id == "robot-aux"
    assert rules["space-layout"].input_control.references[0].asset_id == "room"
    advisory = rules["final-transition-preference"]
    assert advisory.level == "recipe_hint"
    assert advisory.stage == "final_composition"
    assert advisory.native_text == ()
    assert advisory.requirement_id not in acceptance.required_requirement_ids
    from ai_video.production.video_reference_controls import prepared_generation_report

    objective = next(row for row in prepared_generation_report(prepared)["reference_control"]["objectives"]
                     if row["requirement_id"] == advisory.requirement_id)
    assert objective["model_freedom"] == "ALLOWED_WITHIN_AUTHORED_SCOPE"
    assert objective["raw_input_expected"] is False
    assert objective["raw_acceptance_required"] is False
    assert tuple(item.attempt_id for item in service._load().manifest.attempts) == before_attempts
    assert not any(item.operation == "video_generation" for item in service._load().manifest.attempts)
