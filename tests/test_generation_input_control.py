"""Generation input controls survive typed projection without rewriting authorship."""

from types import SimpleNamespace

import pytest


def _rule(requirement_id, *, control=None, native_text=(), intent_paths=None, level="acceptance"):
    from ai_video.production.generation_recipe import RequirementExpression

    return RequirementExpression(
        requirement_id=requirement_id,
        level=level,
        stage="raw_generation",
        dimension="action_and_time",
        observable="The authored action and input duties are preserved.",
        tolerance="as authored",
        measurement="inspect the exact compiler input",
        proof="technical",
        intent_paths=intent_paths or ("generation_intent.subject_action.progression",),
        native_text=tuple(native_text),
        production_owner="qa_acceptance",
        input_control=control,
    )


def _asset(asset_id, *, role="identity", sha256="a" * 64, owner="person-a",
           mime_type="image/png", size_bytes=32):
    from ai_video.production.video_requirement import AssetEvidence, SemanticReferenceRole

    return AssetEvidence(
        role=SemanticReferenceRole(role),
        asset_id=asset_id,
        asset_sha256=sha256,
        canonical_owner_id=owner,
        mime_type=mime_type,
        width=320 if mime_type.startswith("image/") else 1280 if mime_type.startswith("video/") else None,
        height=240 if mime_type.startswith("image/") else 720 if mime_type.startswith("video/") else None,
        size_bytes=size_bytes,
        duration_millis=4000 if mime_type.startswith(("video/", "audio/")) else None,
        fps=24 if mime_type.startswith("video/") else None,
    )


def _requirement_with_assets(*assets):
    from ai_video.production.video_requirement import SemanticReferenceRole
    from test_production_generation_decision import setup_decision

    requirement = setup_decision()["projection"].requirement
    roles = tuple(sorted({item.role for item in assets}, key=lambda role: role.value))
    return requirement.model_copy(update={"asset_evidence": tuple(assets),
                                         "semantic_reference_roles": roles})


def _duty(asset, *, purpose="identity", scope="Use this reference only for identity.",
          independent_identity=False, role=None, sha256=None, owner=None):
    from ai_video.production.generation_input_control import ReferenceDuty

    return ReferenceDuty(
        asset_id=asset.asset_id,
        asset_sha256=sha256 or asset.asset_sha256,
        role=role or asset.role.value,
        purpose=purpose,
        scope_text=scope,
        canonical_owner_id=asset.canonical_owner_id if owner is None else owner,
        independent_identity=independent_identity,
    )


def _reference_expression(requirement_id, duties, *, text=None):
    from ai_video.production.generation_input_control import GenerationInputControl

    scope_text = tuple(duty.scope_text for duty in duties if duty.scope_text is not None)
    native_text = tuple(text) if text is not None else scope_text
    return _rule(requirement_id, control=GenerationInputControl(
        mechanism="reference_guidance", references=tuple(duties)), native_text=native_text)


def _sealed_acceptance(expressions):
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.hashing import canonical_sha256

    expressions = tuple(sorted(expressions, key=lambda item: item.requirement_id))
    ids = tuple(item.requirement_id for item in expressions if item.level == "acceptance")
    payload = {
        "domain_id": "input-control-test",
        "profile_id": "input-control-test-rubric",
        "profile_version": "1",
        "measurement_contract_version": "1",
        "required_requirement_ids": ids,
        "generation_requirements": tuple(item.model_dump(mode="json") for item in expressions),
    }
    digest = canonical_sha256(payload)
    return DomainAcceptancePolicy(
        domain_id=payload["domain_id"],
        profile_id=payload["profile_id"],
        profile_version=payload["profile_version"],
        profile_content_hash=digest,
        measurement_contract_version=payload["measurement_contract_version"],
        required_requirement_ids=ids,
        profile_payload={**payload, "content_hash": digest},
    )


def _unmarked_acceptance(raw_rule):
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.hashing import canonical_sha256

    payload = {
        "domain_id": "input-control-test",
        "profile_id": "input-control-test-rubric",
        "profile_version": "1",
        "measurement_contract_version": "1",
        "required_requirement_ids": (raw_rule["requirement_id"],),
        "generation_requirements": (raw_rule,),
    }
    digest = canonical_sha256(payload)
    return DomainAcceptancePolicy.model_validate({
        "domain_id": payload["domain_id"],
        "profile_id": payload["profile_id"],
        "profile_version": payload["profile_version"],
        "profile_content_hash": digest,
        "measurement_contract_version": payload["measurement_contract_version"],
        "required_requirement_ids": payload["required_requirement_ids"],
        "profile_payload": {**payload, "content_hash": digest},
    })


def test_requirement_expression_accepts_typed_input_control_and_omits_legacy_none():
    from ai_video.production.generation_input_control import GenerationInputControl
    from ai_video.production.generation_recipe import RequirementExpression

    deadline = "Finish the action by 2.5 seconds and hold through the cut."
    control = GenerationInputControl(mechanism="prompt_guidance", references=())
    rule = RequirementExpression(
        requirement_id="action-deadline",
        level="acceptance",
        stage="raw_generation",
        dimension="timing",
        observable="The action finishes before the adopted cut.",
        tolerance="finish by the authored deadline",
        measurement="Inspect the exact compiled prompt and source frames",
        proof="technical",
        intent_paths=("generation_intent.subject_action.progression",),
        native_text=(deadline,),
        production_owner="qa_acceptance",
        input_control=control,
    )

    reopened = RequirementExpression.model_validate(rule.model_dump(mode="json"))
    assert reopened.input_control == control
    assert reopened.native_text == (deadline,)

    legacy = RequirementExpression(
        requirement_id="legacy-duration",
        level="acceptance",
        stage="raw_generation",
        dimension="timing",
        observable="The generated output is five seconds.",
        tolerance="exact",
        measurement="Probe the output duration",
        proof="technical",
        intent_paths=("generation_intent.subject_action.progression",),
        native_text=(),
        production_owner="qa_acceptance",
    )
    assert "input_control" not in legacy.model_dump(mode="json")


@pytest.mark.parametrize("invalid_control", [
    {"contract_version": "generation-input-control/1", "mechanism": "guess_mode", "references": []},
    {"contract_version": "generation-input-control/1", "mechanism": "reference_guidance",
     "references": [{"asset_id": "person-ref", "asset_sha256": "a" * 64, "role": "identity",
                     "purpose": "identity", "canonical_owner_id": "person-a"}]},
])
def test_unmarked_qa_rejects_malformed_typed_input_control_at_seal(invalid_control):
    from pydantic import ValidationError

    raw_rule = {
        "requirement_id": "typed-input",
        "level": "acceptance",
        "stage": "raw_generation",
        "dimension": "input_control",
        "observable": "The typed input control is well-formed.",
        "tolerance": "exact",
        "measurement": "validate its authored shape",
        "proof": "technical",
        "intent_paths": ["generation_intent.subject_action.progression"],
        "native_text": ["Finish by the cut."],
        "production_owner": "qa_acceptance",
        "input_control": invalid_control,
    }

    with pytest.raises(ValidationError):
        _unmarked_acceptance(raw_rule)


def test_unmarked_valid_input_control_keeps_its_sealed_hash_and_legacy_hash_stays_stable():
    from ai_video.production.generation_input_control import GenerationInputControl
    from ai_video.production.hashing import canonical_sha256

    raw_rule = {
        "requirement_id": "typed-input",
        "level": "acceptance",
        "stage": "raw_generation",
        "dimension": "action_timing",
        "observable": "The typed input control is preserved.",
        "tolerance": "exact",
        "measurement": "validate its authored shape",
        "proof": "technical",
        "intent_paths": ["generation_intent.subject_action.progression"],
        "native_text": ["Finish by the cut."],
        "production_owner": "qa_acceptance",
        "input_control": {
            "contract_version": "generation-input-control/1",
            "mechanism": "prompt_guidance",
            "references": [],
        },
    }

    accepted = _unmarked_acceptance(raw_rule)
    payload = {
        "domain_id": "input-control-test",
        "profile_id": "input-control-test-rubric",
        "profile_version": "1",
        "measurement_contract_version": "1",
        "required_requirement_ids": ("typed-input",),
        "generation_requirements": (raw_rule,),
    }

    assert accepted.profile_content_hash == canonical_sha256(payload)
    assert GenerationInputControl.model_validate(
        accepted.profile_payload["generation_requirements"][0]["input_control"]
    ) == GenerationInputControl.model_validate(raw_rule["input_control"])


def test_generation_projection_preserves_explicit_native_text_for_opted_rule():
    from ai_video.production.generation_feedback import _expressions
    from test_production_generation_decision import setup_decision

    deadline = "Finish the action by 2.5 seconds and hold through the cut."
    setup = setup_decision()
    requirement = setup["projection"].requirement
    acceptance = SimpleNamespace(profile_payload={"generation_requirements": ({
        "requirement_id": "action-deadline",
        "level": "acceptance",
        "stage": "raw_generation",
        "dimension": "timing",
        "observable": "The action finishes before the adopted cut.",
        "tolerance": "finish by the authored deadline",
        "measurement": "Inspect the exact compiled prompt and source frames",
        "proof": "technical",
        "intent_paths": ["generation_intent.subject_action.progression"],
        "native_text": [deadline],
        "production_owner": "qa_acceptance",
        "input_control": {
            "contract_version": "generation-input-control/1",
            "mechanism": "prompt_guidance",
            "references": [],
        },
    },)})

    projected = _expressions(acceptance, requirement)

    assert projected[0].native_text == (deadline,)


def test_legacy_recipe_hash_is_unchanged_when_input_control_is_omitted():
    from test_production_generation_decision import setup_decision

    recipe = setup_decision()["inputs"].candidates[0].recipe

    assert recipe.recipe_hash == "fe1a5cc5cba36b686e8da4e9c2c7ec367afeedb06106b871830396403180ff1a"
    assert "input_control" not in recipe.model_dump(mode="json")


def test_generation_input_control_shapes_separate_guidance_endpoints_and_native_output():
    from pydantic import ValidationError

    from ai_video.production.generation_input_control import GenerationInputControl
    from ai_video.production.generation_recipe import RequirementExpression

    with pytest.raises(ValidationError, match="reference guidance requires"):
        GenerationInputControl(mechanism="reference_guidance")
    with pytest.raises(ValidationError, match="endpoint input requires"):
        GenerationInputControl(mechanism="first_frame")
    with pytest.raises(ValidationError, match="endpoint input requires"):
        GenerationInputControl(mechanism="last_frame", references=(
            {"asset_id": "opening", "asset_sha256": "a" * 64, "role": "first_frame",
             "purpose": "opening"},))

    output_control = GenerationInputControl(mechanism="native_output")
    RequirementExpression(
        requirement_id="native-duration", level="acceptance", stage="raw_generation",
        dimension="timing", observable="The output is five seconds.", tolerance="exact",
        measurement="probe output", proof="technical", intent_paths=("output_need.duration_seconds",),
        native_text=(), production_owner="qa_acceptance", input_control=output_control)
    with pytest.raises(ValidationError, match="native output control requires"):
        RequirementExpression(
            requirement_id="wrong-native-duration", level="acceptance", stage="raw_generation",
            dimension="timing", observable="The action is complete.", tolerance="exact",
            measurement="inspect prompt", proof="technical",
            intent_paths=("generation_intent.subject_action.progression",), native_text=(),
            production_owner="qa_acceptance", input_control=output_control)
    with pytest.raises(ValidationError, match="guidance input control requires authored generation intent"):
        RequirementExpression(
            requirement_id="prompt-without-intent", level="acceptance", stage="raw_generation",
            dimension="timing", observable="The action is complete.", tolerance="exact",
            measurement="inspect prompt", proof="technical", intent_paths=("output_need.duration_seconds",),
            native_text=("Finish by the cut.",), production_owner="qa_acceptance",
            input_control=GenerationInputControl(mechanism="prompt_guidance"))
    with pytest.raises(ValidationError, match="text/output input controls cannot claim reference duties"):
        GenerationInputControl(mechanism="native_output", references=(
            {"asset_id": "opening", "asset_sha256": "a" * 64, "role": "identity",
             "purpose": "identity"},))


def test_reference_guidance_requires_owner_and_explicit_scope():
    from pydantic import ValidationError

    from ai_video.production.generation_input_control import GenerationInputControl, ReferenceDuty

    with pytest.raises(ValidationError, match="reference guidance requires"):
        GenerationInputControl(mechanism="reference_guidance", references=(
            ReferenceDuty(asset_id="person-ref", asset_sha256="a" * 64, role="identity",
                          purpose="identity"),))
    with pytest.raises(ValidationError, match="explicit identity owner"):
        ReferenceDuty(asset_id="person-ref", asset_sha256="a" * 64, role="identity",
                      purpose="identity", canonical_owner_id=None, independent_identity=True)
    with pytest.raises(ValidationError, match="explicit identity owner"):
        ReferenceDuty(asset_id="room-ref", asset_sha256="b" * 64, role="scene",
                      purpose="layout", scope_text="Use this reference for layout.",
                      canonical_owner_id="room", independent_identity=True)


def test_reference_duties_bind_role_bytes_owner_and_exact_prompt_scope():
    from ai_video.production.generation_input_control import input_control_issues

    asset = _asset("person-main", owner="person-a")
    requirement = _requirement_with_assets(asset)
    scope = "Use person-main only for identity."
    valid = _reference_expression("identity", (_duty(asset, scope=scope),))
    assert input_control_issues((valid,), requirement, scope) == {}

    wrong_identity = (
        _reference_expression("bad-role", (_duty(asset, purpose="layout", scope=scope,
                                                   role="scene"),)),
        _reference_expression("bad-id", (_duty(asset, scope=scope).model_copy(
            update={"asset_id": "different-ref"}),)),
        _reference_expression("bad-sha", (_duty(asset, scope=scope, sha256="f" * 64),)),
        _reference_expression("bad-owner", (_duty(asset, scope=scope, owner="person-b"),)),
    )
    for expression in wrong_identity:
        assert "REFERENCE_IDENTITY_MISMATCH" in input_control_issues(
            (expression,), requirement, scope)[expression.requirement_id]

    missing_scope = "This instruction is absent from the exact prompt."
    missing = _reference_expression("missing-scope", (_duty(asset, scope=missing_scope),))
    errors = input_control_issues((missing,), requirement, "Use person-main only for identity.")[
        "missing-scope"]
    assert {"MISSING_NATIVE_FRAGMENT", "REFERENCE_SCOPE_NOT_EXPRESSED"} <= set(errors)


def test_opening_and_closing_endpoints_require_their_native_roles():
    from ai_video.production.generation_input_control import (
        GenerationInputControl,
        input_control_issues,
    )

    opening_asset = _asset("opening-frame", role="first_frame", owner=None)
    closing_asset = _asset("closing-frame", role="last_frame", owner=None, sha256="b" * 64)
    opening_requirement = _requirement_with_assets(opening_asset)
    closing_requirement = _requirement_with_assets(closing_asset)
    opening_duty = _duty(opening_asset, purpose="opening", scope=None)
    closing_duty = _duty(closing_asset, purpose="closing", scope=None)
    opening = _rule("opening", control=GenerationInputControl(
        mechanism="first_frame", references=(opening_duty,)), native_text=())
    closing = _rule("closing", control=GenerationInputControl(
        mechanism="last_frame", references=(closing_duty,)), native_text=())
    assert input_control_issues((opening,), opening_requirement, "") == {}
    assert input_control_issues((closing,), closing_requirement, "") == {}

    generic_asset = _asset("generic-image")
    generic_requirement = _requirement_with_assets(generic_asset)
    generic_opening = _duty(generic_asset, purpose="opening", scope=None)
    wrong_endpoint = _rule("wrong-opening", control=GenerationInputControl(
        mechanism="first_frame", references=(generic_opening,)), native_text=())
    assert input_control_issues((wrong_endpoint,), generic_requirement, "")[
        "wrong-opening"] == ("ENDPOINT_ROLE_MISMATCH",)


def test_identical_bytes_are_rejected_only_for_distinct_independent_identity_aliases():
    from ai_video.production.generation_input_control import input_control_issues

    first = _asset("person-a-ref", owner="person-a", sha256="c" * 64,
                   mime_type="image/png", size_bytes=32)
    second = _asset("person-b-ref", owner="person-b", sha256="c" * 64,
                    mime_type="image/jpeg", size_bytes=80)
    requirement = _requirement_with_assets(first, second)
    duties = (_duty(first, purpose="identity", scope="Use person-a-ref for person-a.",
                    independent_identity=True),
              _duty(second, purpose="identity", scope="Use person-b-ref for person-b.",
                    independent_identity=True))
    prompt = " ".join(duty.scope_text for duty in duties)
    aliases = _reference_expression("two-people", duties)

    assert "INDEPENDENT_REFERENCE_BYTES_REUSED" in input_control_issues(
        (aliases,), requirement, prompt)["two-people"]

    # Reusing one exact binding for two duties does not invent a second person.
    repeated = _reference_expression("one-binding", (duties[0], duties[0]))
    assert input_control_issues((repeated,), requirement, prompt) == {}


def test_unmapped_raw_requirement_is_not_silently_legacy_once_contract_is_opted_in():
    from ai_video.production.generation_input_control import (
        GenerationInputControl,
        input_control_issues,
    )

    asset = _asset("person-main")
    requirement = _requirement_with_assets(asset)
    control = GenerationInputControl(mechanism="prompt_guidance")
    mapped = _rule("mapped", control=control, native_text=("Finish before the cut.",))
    unmapped = _rule("unmapped")

    assert input_control_issues((mapped, unmapped), requirement,
                                "Finish before the cut.") == {"unmapped": ("UNMAPPED_CONTROL",)}
    assert input_control_issues((unmapped,), requirement, "") == {}


def test_ordinary_video_motion_reference_is_not_inferred_to_be_whitebox():
    from ai_video.production.generation_input_control import input_control_issues

    video = _asset("motion-ref", role="video_reference", owner=None,
                   mime_type="video/mp4", size_bytes=96)
    requirement = _requirement_with_assets(video)
    scope = "Use motion-ref to guide movement timing."
    duty = _duty(video, purpose="motion", scope=scope)
    expression = _reference_expression("motion-only", (duty,))
    assert input_control_issues((expression,), requirement, scope) == {}

    still = _asset("whitebox-layout", role="scene", owner="room")
    still_requirement = _requirement_with_assets(still)
    still_scope = "Use whitebox-layout as a static spatial layout reference."
    static_whitebox = _reference_expression("static-whitebox", (
        _duty(still, purpose="whitebox", scope=still_scope),))
    assert input_control_issues((static_whitebox,), still_requirement, still_scope) == {}

    audio = _asset("whitebox-audio", role="audio_reference", owner=None, mime_type="audio/wav")
    audio_requirement = _requirement_with_assets(audio)
    audio_scope = "Use whitebox-audio only to guide the room layout."
    false_whitebox = _reference_expression("audio-whitebox", (
        _duty(audio, purpose="whitebox", scope=audio_scope),))
    assert "WHITEBOX_MEDIA_REQUIRED" in input_control_issues(
        (false_whitebox,), audio_requirement, audio_scope)["audio-whitebox"]


def test_recipe_rejects_resealed_native_text_that_differs_from_selected_qa_owner():
    from ai_video.production.generation_input_control import GenerationInputControl
    from ai_video.production.generation_recipe import GenerationRecipe
    from test_production_generation_decision import setup_decision

    control = GenerationInputControl(mechanism="prompt_guidance")
    authored = _rule("authored-deadline", control=control,
                     native_text=("Finish by 2.5 seconds.",))
    acceptance = _sealed_acceptance((authored,))
    baseline = setup_decision()["inputs"].candidates[0].recipe
    recipe = GenerationRecipe.model_validate({
        **baseline.model_dump(mode="python"),
        "acceptance_policy": acceptance,
        "rubric_hash": acceptance.profile_content_hash,
        "expressions": (authored,),
    })
    changed = recipe.expressions[0].model_copy(update={
        "native_text": ("Finish at the cut.",),
    })

    with pytest.raises(ValueError, match="authored input control fragment"):
        GenerationRecipe.model_validate({
            **recipe.model_dump(mode="python"),
            "expressions": (changed,),
        })


def _activate_canvas_control_acceptance(service, *, control=None, native_text=(), rules=None):
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.hashing import canonical_sha256
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.models import SourceReference

    loaded = service._load()
    qa = loaded.qa_policy
    selected = qa.selected_generation_acceptance()
    payload = dict(selected.profile_payload)
    payload.pop("content_hash", None)
    baseline_rule = dict(payload["generation_requirements"][0])
    if rules is None:
        rules = ({
            "requirement_id": "authored-input",
            "dimension": "action_and_time",
            "observable": "The authored action deadline and reference scopes reach the compiler.",
            "intent_paths": ["generation_intent.subject_action.progression"],
            "native_text": list(native_text),
            "input_control": control.model_dump(mode="json"),
        },)
    rules = tuple(sorted(rules, key=lambda spec: spec["requirement_id"]))
    inventory = []
    for spec in rules:
        raw = dict(baseline_rule)
        raw.update(
            requirement_id=spec["requirement_id"],
            level="acceptance",
            stage="raw_generation",
            dimension=spec["dimension"],
            observable=spec["observable"],
            tolerance="preserve the authored target and its mapped inputs",
            measurement="inspect the exact compiler input and native bindings",
            proof=spec.get("proof", "technical"),
            intent_paths=list(spec["intent_paths"]),
            native_text=list(spec["native_text"]),
            production_owner="qa_acceptance",
            input_control=spec["input_control"],
        )
        inventory.append(raw)
    payload["generation_requirements"] = tuple(inventory)
    payload["required_requirement_ids"] = tuple(spec["requirement_id"] for spec in rules)
    digest = canonical_sha256(payload)
    acceptance_fields = selected.model_dump(mode="python")
    acceptance_fields.update(
        required_requirement_ids=tuple(spec["requirement_id"] for spec in rules),
        profile_content_hash=digest,
        profile_payload={**payload, "content_hash": digest},
    )
    acceptance = DomainAcceptancePolicy.model_validate(acceptance_fields)
    acceptance_field = next(name for name in ("generation_acceptance", "domain_acceptance")
        if getattr(qa, name) is selected)
    qa_fields = qa.model_dump(mode="python")
    qa_fields.update(
        {acceptance_field: acceptance,
         "revision": qa.revision + 1,
         "content_hash": "0" * 64,
         "creation_receipt_id": "generation-input-control-test",
         "source_provenance": (SourceReference(kind="derived", reference="generation-input-control-test"),)}
    )
    updated_qa = type(qa).model_validate(qa_fields)
    manifest = service.committer._read_manifest()
    service.committer.activate_qa_policy(
        seal_artifact(updated_qa),
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="activate-generation-input-control-test",
    )


def _canvas_control_service(tmp_path, *, scenario, provider_family, missing_fragment=False):
    from ai_video.production.generation_input_control import GenerationInputControl, ReferenceDuty
    from test_canvas_source_expression import subject_service

    deadline = "Complete the action by 2.5 seconds, then hold through the cut."
    scopes = {
        "robot-main": "Use the primary identity image only for the main character's identity.",
        "robot-aux": "Use the secondary identity image only for the auxiliary character identity.",
        "room": "Use the room reference only for spatial layout.",
    }
    authored_extra = " ".join((*scopes.values(), deadline))
    service, limits = subject_service(
        tmp_path,
        scenario=scenario,
        authored_deadline_text=authored_extra,
        generation_output_duration_seconds=5,
        provider_family=provider_family,
    )
    baseline = service.prepare(limits=limits)
    assert baseline.execution_binding is not None
    requirement = baseline.execution_binding.projection.requirement
    evidence_by_asset = {evidence.asset_id: evidence for evidence in requirement.asset_evidence}
    assert set(evidence_by_asset) >= set(scopes)
    duties = {asset_id: ReferenceDuty(
        asset_id=evidence.asset_id,
        asset_sha256=evidence.asset_sha256,
        role=evidence.role.value,
        purpose="identity" if evidence.role.value == "identity" else "layout",
        scope_text=scopes[evidence.asset_id],
        canonical_owner_id=evidence.canonical_owner_id,
    ) for asset_id, evidence in evidence_by_asset.items() if asset_id in scopes}
    assert set(duties) == set(scopes)
    action_fragment = ("This clause is absent from the authored prompt." if missing_fragment
                       else deadline)
    expected_text = {
        "action-deadline": (action_fragment,),
        "main-identity": (scopes["robot-main"],),
        "aux-identity": (scopes["robot-aux"],),
        "space-layout": (scopes["room"],),
        "native-duration": (),
    }
    from ai_video.production.performance_direction import render_performance_direction
    expected_text["character-performance"] = (
        render_performance_direction(requirement.generation_intent.performance_intent),
    )
    rules = (
        {"requirement_id": "character-performance", "dimension": "character_performance",
         "observable": "The cast performs the authored expression, gaze and physical response.",
         "proof": "analyzer", "intent_paths": ["generation_intent.performance_intent"],
         "native_text": expected_text["character-performance"],
         "input_control": GenerationInputControl(mechanism="prompt_guidance").model_dump(mode="json")},
        {"requirement_id": "action-deadline", "dimension": "action_timing",
         "observable": "The character completes the authored action by its deadline.",
         "intent_paths": ["generation_intent.subject_action.progression"],
         "native_text": expected_text["action-deadline"],
         "input_control": GenerationInputControl(mechanism="prompt_guidance").model_dump(mode="json")},
        {"requirement_id": "main-identity", "dimension": "character_identity",
         "observable": "The main character identity uses its exact assigned reference.",
         "intent_paths": ["generation_intent.subject_action.progression", "asset_evidence"],
         "native_text": expected_text["main-identity"],
         "input_control": GenerationInputControl(mechanism="reference_guidance",
             references=(duties["robot-main"],)).model_dump(mode="json")},
        {"requirement_id": "aux-identity", "dimension": "character_identity",
         "observable": "The auxiliary identity uses its exact assigned reference.",
         "intent_paths": ["generation_intent.subject_action.progression", "asset_evidence"],
         "native_text": expected_text["aux-identity"],
         "input_control": GenerationInputControl(mechanism="reference_guidance",
             references=(duties["robot-aux"],)).model_dump(mode="json")},
        {"requirement_id": "space-layout", "dimension": "spatial_layout",
         "observable": "The composition uses the assigned spatial layout reference.",
         "intent_paths": ["generation_intent.subject_action.progression", "asset_evidence"],
         "native_text": expected_text["space-layout"],
         "input_control": GenerationInputControl(mechanism="reference_guidance",
             references=(duties["room"],)).model_dump(mode="json")},
        {"requirement_id": "native-duration", "dimension": "output_duration",
         "observable": "The native generated output uses the requested duration.",
         "intent_paths": ["output_need.duration_seconds"], "native_text": (),
         "input_control": GenerationInputControl(mechanism="native_output").model_dump(mode="json")},
    )
    _activate_canvas_control_acceptance(service, rules=rules)
    return service, limits, scopes, deadline, expected_text


@pytest.mark.parametrize("scenario", [
    ("Robot", "raises both arms", "an atrium"),
    ("Courier", "sets a parcel down", "a station platform"),
    ("Scientist", "turns toward the window", "a narrow cabin"),
])
@pytest.mark.parametrize(("provider_family", "provider_name", "compiler_id"), [
    ("seedance", "seedance", "seedance-video-compiler"),
    ("h3-max", "minimax_h3_max", "minimax-h3-max-video-compiler"),
])
def test_reference_guidance_and_authored_deadline_reach_each_shared_native_compiler(
    tmp_path, scenario, provider_family, provider_name, compiler_id
):
    service, limits, scopes, deadline, fragments = _canvas_control_service(
        tmp_path, scenario=scenario, provider_family=provider_family)

    prepared = service.prepare(limits=limits)

    assert prepared.execution_binding is not None
    assert prepared.compilation.outcome == "compiled"
    assert prepared.resolved_request.provider_name == provider_name
    assert prepared.resolved_request.adapter_compiler_id == compiler_id
    assert prepared.resolved_request.prompt_text == service.direction["shots"][0]["shot"]["intent"]
    assert all(fragment in prepared.resolved_request.prompt_text
               for fragment in (*scopes.values(), deadline))
    recipe = prepared.execution_binding.decision.routing.provider_bound_request.generation_recipe
    rules = {rule.requirement_id: rule for rule in recipe.expressions}
    assert set(rules) == set(fragments)
    assert {requirement_id: rule.input_control.mechanism
            for requirement_id, rule in rules.items()} == {
        "action-deadline": "prompt_guidance",
        "main-identity": "reference_guidance",
        "aux-identity": "reference_guidance",
        "space-layout": "reference_guidance",
        "native-duration": "native_output",
        "character-performance": "prompt_guidance",
    }
    assert {requirement_id: rule.native_text for requirement_id, rule in rules.items()} == fragments
    assert {requirement_id: rule.input_control.references[0].asset_id
            for requirement_id, rule in rules.items() if rule.input_control.references} == {
        "main-identity": "robot-main",
        "aux-identity": "robot-aux",
        "space-layout": "room",
    }
    inventory = recipe.acceptance_policy.profile_payload["generation_requirements"]
    assert {rule["requirement_id"] for rule in inventory} == set(fragments)
    assert {rule["requirement_id"]: tuple(rule["native_text"]) for rule in inventory} == fragments
    assert not any(attempt.operation == "video_generation"
                   for attempt in service._load().manifest.attempts)


@pytest.mark.parametrize("provider_family", ["seedance", "h3-max"])
def test_missing_authored_fragment_is_a_typed_compiler_unsupported_result(tmp_path, provider_family):
    from ai_video.production.video_compiler import (
        ProviderRequirementUnsupported,
        ProviderRequirementUnsupportedReason,
    )

    service, limits, _, _, fragments = _canvas_control_service(
        tmp_path, scenario=("Courier", "sets a parcel down", "a station platform"),
        provider_family=provider_family, missing_fragment=True)

    prepared = service.prepare(limits=limits)

    assert isinstance(prepared.compilation, ProviderRequirementUnsupported)
    assert prepared.compilation.reason is ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED
    assert prepared.compilation.unsupported_field_paths == ("action-deadline",)
    assert "action-deadline" in fragments
    assert fragments["action-deadline"][0] not in service.direction["shots"][0]["shot"]["intent"]
    assert prepared.execution_binding is None
    assert not any(attempt.operation == "video_generation"
                   for attempt in service._load().manifest.attempts)
