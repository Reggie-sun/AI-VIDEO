"""Exact causal opening expression, with standard scripted source lifecycle.

Scripted source media/QA is offline evidence, not real media qualification.
The target compiler is pure and never submits, polls, fetches or reads secrets.
"""

from dataclasses import replace
import hashlib

import pytest

from ai_video.planning import VideoPlanner, VideoPlanningRequest, require_current_video_plan
from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import (
    AmbienceIntent, ContinuityStateKind, Pacing, ProviderNeutralGenerationIntentProjection,
    TypedStateReference,
)
from ai_video.production._remote_video_native_prompt import compile_remote_video_prompt


def canonical_expression_fixture(tmp_path, *, exact_terminal=False, source=None, duration=1, close_hash=False,
                                 equal_close=False, arbitrary_close=False):
    import test_planning_sequence_continuity as s
    import test_production_shot_router as r
    from test_production_video_intent_validation import _complete_intent, _compatible_fl2va
    from ai_video.production.project import load_production_project
    from ai_video.production.video_requirement import ConditioningLane

    source = source or s._activated_source(tmp_path)
    inputs = s._edge_inputs(source, **({"boundary": s.BoundaryKind.WITHIN_CONTINUOUS_TAKE}
                                     if exact_terminal else {}))
    seed = inputs["current_request"]
    # New authored target fixture: opening is sealed causal truth; closing is
    # separately authored text. Existing source and historical fixtures stay intact.
    intent = _complete_intent().model_copy(update={
        "open_state": seed.generation_intent.generation_intent.open_state,
        "close_state": TypedStateReference(kind="typed_hash", state_hash=s.causal_state_column_hash(
            s.causal_changes(), endpoint="source_close")) if close_hash else TypedStateReference(
            kind="typed_text", state_text="actors continue along the right path"),
        "pacing": Pacing(shot_duration_seconds=duration),
        "ambience_intent": AmbienceIntent(environment_bed="none", explicitly_silent=True),
    })
    if equal_close:
        intent = intent.model_copy(update={"close_state": intent.open_state})
    elif arbitrary_close:
        intent = intent.model_copy(update={"close_state": TypedStateReference(kind="typed_hash", state_hash="f" * 64)})
    first = next(a for a in seed.available_assets if a.role.value == (
        "previous_shot_terminal" if exact_terminal else "approved_keyframe"))
    authored = ProviderNeutralGenerationIntentProjection.create(**{
        **{n: getattr(seed.generation_intent, n) for n in type(seed.generation_intent).model_fields if n != "projection_hash"},
        "generation_intent": intent,
        "semantic_reference_roles": () if exact_terminal else seed.generation_intent.semantic_reference_roles,
        "conditioning_compatibility": _compatible_fl2va().model_copy(update={
            "lane": ConditioningLane.I2VA, "first_anchor_id": first.asset_id,
            "last_anchor_id": None, "available_duration_seconds": duration,
        }),
    })
    inputs["current_request"] = VideoPlanningRequest.create(**{
        **{n: getattr(seed, n) for n in type(seed).model_fields if n != "request_content_hash"},
        "generation_intent": authored,
    })
    request, routing = s.build_sequence_video_planning_request(**inputs)
    plan = VideoPlanner().plan(request)
    projection = require_current_video_plan(current_request=request, plan=plan)
    loaded = load_production_project(tmp_path / "project.yaml")
    context = s._context(loaded, request, plan, source["terminal"])
    bound = r.VideoGenerationResolver()._bind_requirement(
        projection=projection, context=context, policy=r._policy(remote_authorized=True, budget_authorized=True),
        lifecycle=inputs["lifecycle"], continuity_routing=routing,
        provider_profile=source["route"].provider_profile,
        capabilities=source["provider"].capabilities(),
        selected_capability_id=source["route"].capability_id,
        output_requirement=source["binding"].compiled_request.effective_output,
        compiler_contract=source["route"].compiler_contract,
    ).provider_bound_request
    assert bound is not None
    return dict(source=source, loaded=loaded, requirement=projection.requirement,
                provider_bound=bound, routing=routing, request=request, projection=projection)


def expression_context(fixture):
    from ai_video.production._sequence_source import build_verified_causal_opening_expression

    return build_verified_causal_opening_expression(
        loaded=fixture["loaded"], routing=fixture["routing"],
        requirement=fixture["requirement"], provider_bound=fixture["provider_bound"])


@pytest.fixture
def causal_fixture(tmp_path):
    return canonical_expression_fixture(tmp_path)


def compile_fixture(fixture, evidence=None):
    return compile_remote_video_prompt(fixture["requirement"],
        provider_bound=fixture["provider_bound"],
        continuity_expression=evidence if evidence is not None else expression_context(fixture))


def test_arbitrary_hash_and_typed_ref_stay_unsupported(causal_fixture):
    requirement = causal_fixture["requirement"]
    result = compile_remote_video_prompt(requirement)
    assert result.outcome == "unsupported"
    assert result.unsupported_field_paths == ("generation_intent.open_state",)
    from ai_video.production.video_requirement import ProviderNeutralVideoRequirement
    ref_intent = requirement.generation_intent.model_copy(update={
        "open_state": TypedStateReference(kind="typed_ref", state_ref="authored-state-reference")})
    ref = ProviderNeutralVideoRequirement.create(**{
        **requirement.model_dump(mode="python", exclude={"requirement_id", "requirement_hash"}),
        "generation_intent": ref_intent})
    assert compile_remote_video_prompt(ref).outcome == "unsupported"


@pytest.mark.parametrize("exact_terminal", [False, True])
def test_verified_sequence_opening_is_deterministic_endpoint_exact(tmp_path, exact_terminal):
    fixture = canonical_expression_fixture(tmp_path, exact_terminal=exact_terminal)
    evidence = expression_context(fixture)
    result = compile_fixture(fixture, evidence)
    assert result.outcome == "compiled", result
    assert result == compile_fixture(fixture, evidence)
    for change in fixture["routing"].transition_policy.causal_state_changes:
        assert change.target_open in result.prompt_text
    assert fixture["requirement"].generation_intent.open_state.state_hash not in result.prompt_text
    assert "generation_intent.open_state.state_hash" in result.expressed_control_paths
    assert "actors continue along the right path" in result.prompt_text
    assert "generation_intent.close_state.state_hash" not in result.expressed_control_paths


def test_current_close_hash_is_not_previous_close_or_opening(tmp_path):
    fixture = canonical_expression_fixture(tmp_path, close_hash=True)
    result = compile_fixture(fixture)
    assert result.outcome == "unsupported"
    assert result.unsupported_field_paths == ("generation_intent.close_state",)


@pytest.mark.parametrize("mutation", ["hash", "intent", "target", "policy_hash", "binding_hash", "missing", "duplicate", "carry", "preimage"])
def test_owner_rejects_mismatched_or_incomplete_evidence(causal_fixture, mutation):
    fixture = dict(causal_fixture)
    routing = fixture["routing"]
    policy = routing.transition_policy
    if mutation in {"hash", "intent", "target"}:
        requirement = fixture["requirement"]
        if mutation == "hash":
            opening = requirement.generation_intent.open_state.model_copy(update={"state_hash": "f" * 64})
            intent = requirement.generation_intent.model_copy(update={"open_state": opening})
            fixture["requirement"] = requirement.model_copy(update={"generation_intent": intent})
        elif mutation == "intent":
            fixture["requirement"] = requirement.model_copy(update={"generation_intent_hash": "f" * 64})
        else:
            fixture["requirement"] = requirement.model_copy(update={
                "target_shot": requirement.target_shot.model_copy(update={"shot_id": "other-shot"})})
    elif mutation == "binding_hash":
        fixture["routing"] = routing.model_copy(update={"binding_hash": "f" * 64})
    elif mutation == "preimage":
        fixture["routing"] = routing.model_copy(update={"destination_planning_request": None})
    else:
        changes = policy.causal_state_changes
        updates = {"policy_hash": "f" * 64}
        if mutation == "missing":
            updates = {"causal_state_changes": changes[:-1]}
        elif mutation == "duplicate":
            updates = {"causal_state_changes": (*changes, changes[0])}
        elif mutation == "carry":
            updates = {"causal_state_changes": (changes[0].model_copy(update={"target_open": "changed without permission"}), *changes[1:])}
        fixture["routing"] = routing.model_copy(update={"transition_policy": policy.model_copy(update=updates)})
    with pytest.raises(ValueError):
        expression_context(fixture)


def test_context_is_owner_issued_and_sealed(causal_fixture):
    evidence = expression_context(causal_fixture)
    changed = replace(evidence, requirement_hash="f" * 64)
    assert compile_fixture(causal_fixture, changed).outcome == "unsupported"
    assert compile_fixture(causal_fixture, replace(evidence, _issuer=None)).outcome == "unsupported"
    # Even a resealed copy retaining a token is not a fresh owner issuance.
    clone = replace(evidence)
    clone = replace(clone, _seal=canonical_sha256(clone._payload()))
    assert compile_fixture(causal_fixture, clone).outcome == "unsupported"


@pytest.mark.parametrize("mutation", ["context", "nested"])
def test_original_context_cannot_be_mutated_and_resealed(causal_fixture, mutation):
    from ai_video.production._sequence_source import causal_state_column_hash
    from ai_video.production.video_requirement import ProviderNeutralVideoRequirement
    from ai_video.production._shot_router_contracts import ProviderBoundVideoRequest

    fixture = dict(causal_fixture)
    evidence = expression_context(fixture)
    if mutation == "context":
        changes = tuple(c.model_copy(update={"source_close": "unverified invented fact",
            "target_open": "unverified invented fact"}) for c in evidence.changes)
    else:
        changes = evidence.changes
        for change in changes:
            change.__dict__.update(source_close="unverified invented fact", target_open="unverified invented fact")
    requirement = fixture["requirement"]
    intent = requirement.generation_intent.model_copy(update={"open_state": TypedStateReference(
        kind="typed_hash", state_hash=causal_state_column_hash(changes, endpoint="target_open"))})
    requirement = ProviderNeutralVideoRequirement.create(**{
        **requirement.model_dump(mode="python", exclude={"requirement_id", "requirement_hash"}),
        "generation_intent": intent})
    bound = fixture["provider_bound"]
    bound = ProviderBoundVideoRequest.create(**{
        **{n: getattr(bound, n) for n in type(bound).model_fields if n != "provider_bound_request_hash"},
        "requirement_hash": requirement.requirement_hash})
    evidence.__dict__.update(changes=changes, requirement_hash=requirement.requirement_hash,
        provider_bound_request_hash=bound.provider_bound_request_hash,
        source_close_state_hash=causal_state_column_hash(changes, endpoint="source_close"))
    evidence.__dict__["_seal"] = canonical_sha256(evidence._payload())
    fixture.update(requirement=requirement, provider_bound=bound)
    assert compile_fixture(fixture, evidence).outcome == "unsupported"


def test_resealed_target_column_hash_mismatch_is_blocked(causal_fixture):
    from ai_video.production.video_requirement import ProviderNeutralVideoRequirement
    from ai_video.production._shot_router_contracts import ProviderBoundVideoRequest
    fixture = dict(causal_fixture)
    requirement = fixture["requirement"]
    intent = requirement.generation_intent.model_copy(update={
        "open_state": TypedStateReference(kind="typed_hash", state_hash="f" * 64)})
    requirement = ProviderNeutralVideoRequirement.create(**{
        **requirement.model_dump(mode="python", exclude={"requirement_id", "requirement_hash"}),
        "generation_intent": intent})
    bound = fixture["provider_bound"]
    fixture.update(requirement=requirement, provider_bound=ProviderBoundVideoRequest.create(**{
        **{n: getattr(bound, n) for n in type(bound).model_fields if n != "provider_bound_request_hash"},
        "requirement_hash": requirement.requirement_hash}))
    with pytest.raises(ValueError, match="source close / target open"):
        expression_context(fixture)


@pytest.mark.parametrize("mutation", ["missing", "carry", "target_intent", "target_shot"])
def test_resealed_policy_semantics_are_rejected(causal_fixture, mutation):
    from ai_video.production._video_intent_validation import validate_causal_transition_intent
    fixture = dict(causal_fixture)
    routing = fixture["routing"]
    policy = routing.transition_policy
    changes = policy.causal_state_changes
    updates = {"causal_state_changes": changes[:-1]} if mutation == "missing" else (
        {"causal_state_changes": (changes[0].model_copy(update={"target_open": "unauthorized change"}), *changes[1:])}
        if mutation == "carry" else {"target_generation_intent_hash": "f" * 64}
        if mutation == "target_intent" else {"target_shot": policy.target_shot.model_copy(update={"revision": policy.target_shot.revision + 1})})
    policy = type(policy).create(**{
        **{n: getattr(policy, n) for n in type(policy).model_fields if n != "policy_hash"}, **updates})
    assert validate_causal_transition_intent(policy, requirement=fixture["requirement"])
    fixture["routing"] = type(routing).create(**{
        **{n: getattr(routing, n) for n in type(routing).model_fields if n != "binding_hash"}, "transition_policy": policy})
    with pytest.raises(ValueError):
        expression_context(fixture)


def test_text_bytes_unchanged_with_no_hash_path(causal_fixture):
    from ai_video.production.video_requirement import ProviderNeutralVideoRequirement
    requirement = causal_fixture["requirement"]
    text_intent = requirement.generation_intent.model_copy(update={
        "open_state": TypedStateReference(kind="typed_text", state_text="actors already walking toward screen right")})
    text = ProviderNeutralVideoRequirement.create(**{
        **requirement.model_dump(mode="python", exclude={"requirement_id", "requirement_hash"}),
        "generation_intent": text_intent})
    result = compile_remote_video_prompt(text)
    assert result.outcome == "compiled"
    assert result.prompt_sha256 == hashlib.sha256(result.prompt_text.encode()).hexdigest()
    assert result == compile_remote_video_prompt(text, provider_bound=causal_fixture["provider_bound"])
    # Baseline golden was measured before adding the hash expression path.
    assert result.prompt_sha256 == "79551dcfe71dd0e72005c4c65cc38dea3bed5daf73cfcdd3dbe3cc05f4fba209"


def test_normal_metaso_ref2va_native_body_hash_is_unchanged():
    from test_production_metaso_h3 import setup

    provider, request, *_ = setup()
    assert hashlib.sha256(provider.native_payload(request)).hexdigest() == (
        "4e78bc70637ffdba99da736288776f5529fdfc2dc6dcd2da11af32c6ef849cbc")


def metaso_canonical_fixture(tmp_path, monkeypatch, *, target_acceptance=False):
    """Actual METASO metadata/compiler; scripted source lifecycle and QA only.

    Source bytes are the existing six-second audiovisual test fixture. No
    synthetic probe metadata, real Provider effects, or quality claim is used.
    """
    from pathlib import Path
    import test_planning_sequence_continuity as s
    import test_production_generated_video_e2e as e
    from types import SimpleNamespace
    from ai_video.production.metaso_h3 import MetasoH3Profile, MetasoH3VideoProvider
    from ai_video.production.project import load_production_project
    from ai_video.production.video import VideoGenerationRequest, VideoImageReferenceBinding
    from ai_video.production.video_requirement import AudioNeed, OutputNeed
    from production_generation_execution_factory import NativeFixtureVideoProvider, prepare_generation_execution

    def forbidden(*args, **kwargs):
        pytest.fail("canonical pre-submit must not access credentials or transport")

    profile = MetasoH3Profile(duration=6, resolution="768P", aspect_ratio="adaptive",
        context_ir=True, cost_upper_bound_microunits=1)
    provider = MetasoH3VideoProvider(profile=profile,
        transport=SimpleNamespace(request=forbidden, stream=forbidden), credential=forbidden,
        reference_resolver=lambda b: load_production_project(tmp_path / "project.yaml").asset_paths[b.asset_id].read_bytes())
    original_runtime, original_planning, original_keyframe = e._runtime, s._planning, s._prepare_keyframe
    original_base = e.make_p8_video_generation_base
    fixture_media = Path(__file__).parent / "fixtures/ecommerce_job/vertical-6s-audio.mp4"

    def planning(*args, **kwargs):
        seed = original_planning(*args, **kwargs)
        intent = seed.generation_intent
        authored = ProviderNeutralGenerationIntentProjection.create(**{
            **{n: getattr(intent, n) for n in type(intent).model_fields if n != "projection_hash"},
            "output_need": OutputNeed(timing_mode="content_driven", duration_seconds=6, geometry_policy="adaptive",
                aspect_ratio="adaptive", fps=24, container_mime="video/mp4"), "audio_need": AudioNeed.REQUIRED})
        return VideoPlanningRequest.create(**{
            **{n: getattr(seed, n) for n in type(seed).model_fields if n != "request_content_hash"},
            "generation_intent": authored})

    def base(root, **kwargs):
        from ai_video.production.registry import registry_semantic_sha256
        from ai_video.production.state_commit import (
            PreparedArtifact, prepare_project_registry_commit, prepare_dependency_graph_transition,
        )
        from ai_video.production.dependency import build_production_dependency_graph, resolve_dependency_state, desired_fingerprints

        inputs = original_base(root, **kwargs)
        loaded = inputs.project
        raw = e._p7_png(512, 288)
        digest = hashlib.sha256(raw).hexdigest()
        frame = loaded.registry.assets[0].model_copy(update={
            "artifact_path": Path(f"assets/files/{digest}.png"), "sha256": digest,
            "size_bytes": len(raw), "width": 512, "height": 288, "mime_type": "image/png"})
        registry = loaded.registry.model_copy(update={"assets": (frame, *loaded.registry.assets[1:]),
            "revision_id": "0" * 64, "content_hash": "0" * 64})
        digest = registry_semantic_sha256(registry)
        registry = registry.model_copy(update={"revision_id": digest, "content_hash": digest})
        commit = prepare_project_registry_commit(manifest=loaded.manifest, project=loaded.project,
            registry=registry, attempt_id="metaso-initial-image-fixture")
        candidate = loaded.model_copy(update={"registry": registry,
            "manifest": loaded.manifest.model_copy(update={"active_registry": commit.next_registry})})
        graph = build_production_dependency_graph(replace(inputs, project=candidate))
        from ai_video.production.models import RegistryDependencyEvidence
        fingerprints = desired_fingerprints(graph)
        states = tuple(state.model_copy(update={
            "applied_fingerprint": fingerprints[state.node_id], "lifecycle": "fresh",
            "applied_evidence": RegistryDependencyEvidence(owner="registry_snapshot",
                pointer=commit.next_registry, artifact_id=frame.asset_id,
                artifact_fingerprint=fingerprints[state.node_id])})
            if state.node_id == f"asset:{frame.asset_id}" else state
            for state in resolve_dependency_state(graph, ()).states)
        transition = prepare_dependency_graph_transition(expected_manifest_revision=loaded.manifest.manifest_revision,
            base_dependency_graph=loaded.manifest.active_dependency_graph, candidate_graph=graph,
            candidate_dependency_states=resolve_dependency_state(graph, states).states,
            expected_desired_fingerprints=fingerprints)
        raw_graph = e._canonical_json_bytes(graph)
        commit = replace(commit, dependency_graph_transition=transition,
            artifacts=(*commit.artifacts, PreparedArtifact(frame.artifact_path, raw, frame.sha256),
                PreparedArtifact(transition.candidate_dependency_graph.path, raw_graph, hashlib.sha256(raw_graph).hexdigest())))
        e.ProductionStateCommitter(root).commit(commit)
        return replace(inputs, project=load_production_project(root / "project.yaml"))

    def runtime(root, **kwargs):
        inputs, _, template, _, *rest = original_runtime(root, **kwargs)
        loaded = load_production_project(root / "project.yaml")
        inputs = replace(inputs, project=loaded)
        frame = loaded.registry.assets[0]
        target = loaded.shots[0]
        sealed = template.activation_scope.request
        source_request = VideoGenerationRequest.create(**{
            **{n: getattr(sealed, n) for n in type(sealed).model_fields if n != "request_input_hash"},
            "provider_name": "metaso_h3", "provider_kind": "metaso_h3", "model_id": "MiniMax-H3",
            "provider_profile": profile.pointer(), "output_requirement": profile.output(),
            "target_shot_id": target.shot_id, "target_shot_revision": target.revision,
            "target_shot_content_hash": target.content_hash,
            "base_project": loaded.manifest.active_project, "base_registry": loaded.manifest.active_registry,
            "base_dependency_graph": loaded.manifest.active_dependency_graph,
            "seed": None, "negative_prompt_text": "", "input_artifact_ids": (target.artifact_id, frame.asset_id),
            "image_bindings": (VideoImageReferenceBinding(role="first_frame", asset_id=frame.asset_id,
                asset_sha256=frame.sha256, mime_type=frame.mime_type, width=frame.width,
                height=frame.height, size_bytes=frame.size_bytes),)})
        scripted = NativeFixtureVideoProvider(native_prompt_text="offline source compiler fixture",
            compiler_id="metaso-h3-video-compiler", capabilities=provider.capabilities(),
            artifact_bytes=fixture_media.read_bytes(), scenario=e.FakeVideoScenario(status_events=(e.VideoTaskState.SUCCEEDED,)))
        scripted.resolve = provider.resolve
        template = scripted.resolve(source_request)
        source_planning = s._fresh_source_planning(loaded, target, s.causal_changes())
        scripted._native_prompt_text = s._source_native_text(source_planning)
        prepared = prepare_generation_execution(project=loaded, provider=scripted, request=template,
            task_id="metaso-scripted-source", compiler_id="metaso-h3-video-compiler", compiler_version="1",
            planning_request=source_planning)
        return inputs, scripted, template, prepared.binding, *rest

    monkeypatch.setattr(e, "_runtime", runtime)
    monkeypatch.setattr(e, "make_p8_video_generation_base", base)
    monkeypatch.setattr(e, "FIXTURE", fixture_media)
    monkeypatch.setattr(s, "_planning", planning)
    monkeypatch.setattr(s, "_prepare_keyframe", lambda source: original_keyframe(source, width=512, height=288))
    source = s._activated_source(tmp_path)
    if target_acceptance:
        from ai_video.production.hashing import seal_artifact
        from ai_video.production.state_commit import ProductionStateCommitter
        from ai_video.production.generation_recipe import RequirementExpression
        from test_production_generation_decision import acceptance_policy

        # A new target rubric is authored in this temporary fixture. The
        # accepted source's old close-hash rubric and evidence stay immutable.
        loaded = load_production_project(tmp_path / "project.yaml")
        duration = source["binding"].inputs.candidates[0].recipe.expressions[-1].model_copy(update={"semantics": None})
        opening = RequirementExpression(requirement_id="opening-causal-state", level="acceptance",
            stage="raw_generation", dimension="causal_state",
            observable=s.causal_state_column_hash(s.causal_changes(), endpoint="target_open"),
            tolerance="exact", measurement="fixture exact opening", proof="human",
            intent_paths=("generation_intent.open_state.state_hash",), production_owner="test_fixture")
        current = loaded.qa_policy
        from ai_video.production.models import GenerationEvaluationAuthority

        updated = seal_artifact(current.model_copy(update={"revision": current.revision + 1,
            "content_hash": "0" * 64, "generation_acceptance": acceptance_policy((duration, opening)),
            "generation_evaluation_authorities": (*current.generation_evaluation_authorities,
                GenerationEvaluationAuthority(evaluator=current.semantic_authorities[0], proof="human"))}))
        ProductionStateCommitter(tmp_path).activate_qa_policy(updated,
            expected_manifest_revision=loaded.manifest.manifest_revision, attempt_id="authored-target-qa")
    return provider, canonical_expression_fixture(tmp_path, source=source, duration=6)


def test_metaso_canonical_hard_cut_typed_open_reaches_exact_pre_submit(tmp_path, monkeypatch):
    import base64
    import json
    from ai_video.production._sequence_source import compile_with_sequence_expression
    from ai_video.production.video_compiler import require_compiled_provider_request

    provider, fixture = metaso_canonical_fixture(tmp_path, monkeypatch)
    bound, requirement = fixture["provider_bound"], fixture["requirement"]
    assert bound.capability_id == "metaso-h3-fl2va-v1"
    assert fixture["routing"].transition_policy.continuity_obligation.value == "full_continuity"
    assert fixture["routing"].transition_policy.boundary_kind.value == "hard_cut"
    assert bound.lifecycle.hard_cut_keyframe_binding is not None
    result = compile_with_sequence_expression(provider, bound, requirement,
        loaded=fixture["loaded"], routing=fixture["routing"])
    request = require_compiled_provider_request(result).request
    resolved = provider.resolve(request)
    assert provider.preview(resolved).resolved_generation_hash == resolved.resolved_generation_hash
    body = json.loads(provider.native_payload(resolved))
    assert body["content"][0]["text"] == request.prompt_text
    assert len(body["content"]) == 2 and body["content"][1]["role"] == "first_frame"
    frame = bound.input_assets[0]
    assert request.image_bindings[0].asset_id == frame.asset_id
    assert base64.b64decode(body["content"][1]["image_url"]["url"].split(",", 1)[1]) == fixture["loaded"].asset_paths[frame.asset_id].read_bytes()
    assert requirement.generation_intent.open_state.state_hash not in request.prompt_text
    for change in fixture["routing"].transition_policy.causal_state_changes:
        assert change.target_open in request.prompt_text

    # Exercise recipe lexical coverage as well as bare shared prose. The seal
    # stays in the sealed authored recipe; only compiler coverage uses facts.
    from ai_video.production.generation_recipe import GenerationRecipe, RequirementExpression, SeedPolicy
    from ai_video.production.generation_feedback import _expressions
    from test_production_generation_decision import acceptance_policy
    from ai_video.production._shot_router_contracts import ProviderBoundVideoRequest
    from ai_video.production.video_compiler import ProviderRequirementUnsupported, compile_provider_video_request, ProviderNativePrompt

    digest = requirement.generation_intent.open_state.state_hash
    acceptance = acceptance_policy((RequirementExpression(requirement_id="opening-causal-state",
        level="acceptance", stage="raw_generation", dimension="causal_state", observable=digest,
        tolerance="exact", measurement="fixture exact state", proof="human",
        intent_paths=("generation_intent.open_state.state_hash",), production_owner="test_fixture"),))
    recipe = GenerationRecipe(seed=SeedPolicy(kind="uncontrolled"),
        profile_sha256=bound.provider_profile.profile_sha256, compiler_hash=bound.compiler_contract.compiler_hash,
        requirement_hash=requirement.requirement_hash, rubric_hash=acceptance.profile_content_hash,
        acceptance_policy=acceptance, expressions=_expressions(acceptance, requirement))
    assert recipe.expressions[0].native_text == (digest,)
    with_recipe = ProviderBoundVideoRequest.create(**{
        **{n: getattr(bound, n) for n in type(bound).model_fields if n != "provider_bound_request_hash"},
        "generation_recipe": recipe})
    compilation = compile_with_sequence_expression(provider, with_recipe, requirement,
        loaded=fixture["loaded"], routing=fixture["routing"])
    assert require_compiled_provider_request(compilation).request.prompt_text == request.prompt_text
    assert with_recipe.generation_recipe == recipe and recipe.expressions[0].native_text == (digest,)
    # Caller-reported control coverage cannot bypass owner evidence.
    prompt = compile_fixture(fixture)
    arbitrary = compile_provider_video_request(provider_bound=with_recipe, requirement=requirement,
        compiler_id="metaso-h3-video-compiler", compiler_version="1", capabilities=provider.capabilities(),
        native_prompt=ProviderNativePrompt(grammar_contract="remote-video-prose-v1",
            prompt_text=prompt.prompt_text, prompt_sha256=prompt.prompt_sha256,
            expressed_control_paths=prompt.expressed_control_paths))
    assert isinstance(arbitrary, ProviderRequirementUnsupported)
    assert arbitrary.reason.value == "PROMPT_EXPRESSION_UNSUPPORTED"

    # A grammar label cannot give another selected compiler subject privileges.
    evidence = expression_context(fixture)
    altered = prompt.prompt_text.replace("Opening state:", "Unavailable opening state:")
    wrong_grammar = compile_provider_video_request(provider_bound=bound, requirement=requirement,
        compiler_id="metaso-h3-video-compiler", compiler_version="1", capabilities=provider.capabilities(),
        continuity_expression=evidence,
        native_prompt=ProviderNativePrompt(grammar_contract="vidu-subject-prose-v4",
            prompt_text=altered, prompt_sha256=hashlib.sha256(altered.encode()).hexdigest(),
            expressed_control_paths=prompt.expressed_control_paths))
    assert isinstance(wrong_grammar, ProviderRequirementUnsupported)
    assert wrong_grammar.reason.value == "PROMPT_EXPRESSION_UNSUPPORTED"


@pytest.mark.parametrize("drift", ["source", "policy"])
def test_standard_prepare_and_effect_preflight_reopen_causal_expression(tmp_path, monkeypatch, drift):
    import test_planning_sequence_continuity as s
    from test_production_shot_router import _policy
    from ai_video.errors import AiVideoError
    from ai_video.planning.generation_feedback_context import require_feedback_context
    from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator, RegisteredGenerationTarget
    from ai_video.production.project import load_production_project
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_generation import VideoGenerationService
    from ai_video.production._sequence_source import compile_with_sequence_expression

    provider, fixture = metaso_canonical_fixture(tmp_path, monkeypatch, target_acceptance=True)
    source, request, routing = fixture["source"], fixture["request"], fixture["routing"]
    plan = VideoPlanner().plan(request)
    bound = fixture["provider_bound"]
    committer = ProductionStateCommitter(tmp_path)

    def current(loaded):
        return require_feedback_context(loaded=loaded, planning_request=request, video_plan=plan,
            context=s._context(loaded, request, plan, source["terminal"]),
            routing_policy=_policy(remote_authorized=True, budget_authorized=True),
            lifecycle=bound.lifecycle, continuity_routing=routing)

    prepared = GenerationFeedbackOrchestrator.for_project(committer=committer,
        targets=(RegisteredGenerationTarget(provider=provider, profile=bound.provider_profile,
            compiler_contract=bound.compiler_contract, output_requirement=bound.output_requirement),),
        context_loader=current, policy=source["binding"].inputs.policy).prepare(
            limits=source["binding"].inputs.limits.model_copy(update={"task_id": "native-sequence-target",
                "allowed_remote_candidates": (f"{bound.provider_name}/{bound.capability_id}",)}))
    assert prepared.execution_binding is not None, (prepared.decision, prepared.compilation)
    selected = prepared.decision.routing.provider_bound_request
    exact = compile_with_sequence_expression(provider, selected, fixture["requirement"],
        loaded=load_production_project(tmp_path / "project.yaml"), routing=routing)
    assert exact.request == prepared.compilation.request
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(attempt_id="native-sequence-target", request=prepared.resolved_request,
        execution_binding=prepared.execution_binding)
    loaded = load_production_project(tmp_path / "project.yaml")
    state = next(a.video_generation_state for a in loaded.manifest.attempts if a.attempt_id == "native-sequence-target")
    service._validate_generation_execution_binding(state, prepared.resolved_request)
    # Only temporary fixture bytes are changed; no submit/secret/transport.
    path = (loaded.asset_paths[source["binding"].compiled_request.output_asset_id] if drift == "source"
            else tmp_path / loaded.manifest.active_qa_policy.path)
    path.write_bytes(path.read_bytes() + b"\nfixture drift")
    with pytest.raises(AiVideoError):
        service._validate_generation_execution_binding(state, prepared.resolved_request)
