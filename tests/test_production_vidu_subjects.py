"""Named Vidu references retain canonical owners and legacy replay identity."""

import hashlib
import json

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import seal_artifact
from ai_video.production.shot_router import AdapterCompilerContract, MotionRequirement, VideoGenerationResolver
from ai_video.production.video import VideoGenerationRequest, ResolvedVideoGenerationRequest
from ai_video.production.video_compiler import CompiledProviderVideoRequest
from ai_video.production.video_requirement import AssetEvidence, AudioNeed, GenerationMode, OutputNeed, SemanticReferenceRole
from tests.fixtures.planning_factory import make_character, make_scene
from test_production_provider_neutral_adapters import _replace_requirement
from test_production_shot_router import _asset, _context, _lifecycle, _policy, _verified_requirement
from test_production_vidu import _native_prompt_intent, _profile, _request, _setup


def _named_route(*, compiler_version="4", capability_id="viduq3-r2v-subjects-v1", expect_blocked=False, complete=False, setup=False):
    raw = {"asset-COCO": b"coco-image", "asset-Nosha": b"nosha-image", "asset-room": b"scene-image"}
    characters = tuple(seal_artifact(make_character(character_id=name).model_copy(update={
        "name": name, "reference_asset_ids": (f"asset-{name}",),
    })) for name in ("COCO", "Nosha"))
    scene = seal_artifact(make_scene(scene_id="room").model_copy(update={
        "participant_ids": ("COCO", "Nosha"), "visual_reference_asset_ids": ("asset-room",),
    }))
    refs = tuple(_asset("character_reference", character.character_id,
        hashlib.sha256(raw[f"asset-{character.character_id}"]).hexdigest(),
        size_bytes=len(raw[f"asset-{character.character_id}"]), width=1280, height=720,
        canonical_owner_id=character.character_id, canonical_owner_content_hash=character.content_hash)
        for character in characters)
    scene_ref = _asset("scene_reference", "room", hashlib.sha256(raw["asset-room"]).hexdigest(),
        size_bytes=len(raw["asset-room"]), width=1280, height=720,
        canonical_owner_id=scene.scene_id, canonical_owner_content_hash=scene.content_hash)
    context = _context(motion=MotionRequirement.FREE_COMPLEX, scene_id="room",
        important_character_ids=("COCO", "Nosha"), character_bible_hashes=tuple(c.content_hash for c in characters),
        character_references=refs, scene_reference=scene_ref, scene_content_hash=scene.content_hash)
    assets = (*refs, scene_ref)
    roles = (SemanticReferenceRole.IDENTITY, SemanticReferenceRole.IDENTITY, SemanticReferenceRole.SCENE)
    evidence = tuple(AssetEvidence(role=role, asset_id=a.asset_id, asset_sha256=a.asset_sha256,
        mime_type=a.mime_type, width=a.width, height=a.height, size_bytes=a.size_bytes,
        canonical_owner_id=a.canonical_owner_id, canonical_owner_content_hash=a.canonical_owner_content_hash)
        for role, a in zip(roles, assets, strict=True))
    output = _request().output_requirement
    intent = _native_prompt_intent("room")
    if complete:
        from tests.test_production_video_intent_validation import _complete_intent
        from ai_video.production.video_requirement import Pacing
        intent = _complete_intent().model_copy(update={
            "pacing": Pacing(shot_duration_seconds=5),
            "camera_subject_relation": _complete_intent().camera_subject_relation.model_copy(update={"subject_id": "COCO"}),
        })
    projection = _replace_requirement(_verified_requirement(context), scene=scene, characters=characters,
        contract_version="provider-neutral-video-requirement/4" if complete else "provider-neutral-video-requirement/1",
        generation_mode=GenerationMode.REFERENCE_TO_VIDEO,
        generation_intent=intent, asset_evidence=evidence,
        semantic_reference_roles=(SemanticReferenceRole.IDENTITY, SemanticReferenceRole.SCENE),
        output_need=OutputNeed(duration_seconds=5, width=1280, height=720, aspect_ratio="16:9", fps=24,
            container_mime="video/mp4"), audio_need=AudioNeed.REQUIRED)
    provider, _, _ = _setup()
    lifecycle = _lifecycle(context).model_copy(update={"input_artifact_ids": (context.target_shot_id, *(a.asset_id for a in assets))})
    if setup:
        return provider, projection, context, lifecycle
    routing = VideoGenerationResolver()._bind_requirement(projection=projection, context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True), provider_profile=_profile().pointer(),
        capabilities=provider.capabilities(), selected_capability_id=capability_id, output_requirement=output,
        lifecycle=lifecycle,
        compiler_contract=AdapterCompilerContract.create(compiler_id="vidu-video-compiler", compiler_version=compiler_version))
    if expect_blocked:
        assert routing.provider_bound_request is None
        return routing
    assert routing.provider_bound_request is not None, routing.decision.model_dump_json()
    return provider, routing.provider_bound_request, projection.requirement, raw


def _compiled():
    provider, bound, requirement, raw = _named_route()
    result = provider.compile_request(bound, requirement)
    assert isinstance(result, CompiledProviderVideoRequest), result.model_dump_json()
    return provider, bound, requirement, result.request, raw


def test_named_prompt_rejects_overlong_text_after_subject_labels(monkeypatch):
    from ai_video.production import _vidu_prompt
    from ai_video.production.video_compiler import ProviderRequirementUnsupported, ProviderRequirementUnsupportedReason

    provider, bound, requirement, _ = _named_route()
    base_text = "x" * 4990
    base = _vidu_prompt.ViduPromptCompilation(
        prompt_text=base_text, prompt_sha256=hashlib.sha256(base_text.encode()).hexdigest(),
    )
    monkeypatch.setattr(_vidu_prompt, "compile_vidu_prompt", lambda _: base)

    result = provider.compile_request(bound, requirement)
    assert isinstance(result, ProviderRequirementUnsupported)
    assert result.reason is ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED
    assert result.unsupported_field_paths == ("generation_intent",)


def test_standard_router_compiler_resolve_and_submit_preserve_named_image_owners():
    _, _, requirement, request, raw = _compiled()
    subjects = request.subject_bindings
    assert len(subjects) == 3
    by_owner = {s.canonical_owner_id: s for s in subjects}
    for owner in (*requirement.characters, requirement.scene):
        owner_id = getattr(owner, "character_id", getattr(owner, "scene_id", None))
        assert by_owner[owner_id].canonical_owner_content_hash == owner.content_hash
        assert f"@{by_owner[owner_id].name}" in request.prompt_text
    assert by_owner["COCO"].image_asset_ids == ("asset-COCO",)
    assert by_owner["Nosha"].image_asset_ids == ("asset-Nosha",)
    provider, transport, args = _setup(request, image_resolver=lambda b: raw[b.asset_id])
    assert args[0].capability_id == "viduq3-r2v-subjects-v1"
    assert args[0].subject_bindings == subjects
    assert ResolvedVideoGenerationRequest.model_validate_json(args[0].model_dump_json()) == args[0]
    transport.submit["model"] = "viduq3"
    provider.submit(*args)
    payload = json.loads(transport.calls[0].body)
    assert "images" not in payload
    assert payload["auto_subjects"] is False
    assert [s["name"] for s in payload["subjects"]] == [s.name for s in subjects]
    for subject, posted in zip(subjects, payload["subjects"], strict=True):
        import base64
        assert [base64.b64decode(image.split(",", 1)[1]) for image in posted["images"]] == [raw[a] for a in subject.image_asset_ids]
        assert "voice_id" not in posted
    assert transport.calls[0].url.endswith("/reference2video")
    assert payload["model"] == "viduq3"


def test_old_requests_and_resolved_hashes_remain_exact():
    request = _request()
    _, _, args = _setup()
    assert "subject_bindings" not in request.model_dump(mode="json")
    assert request.request_input_hash == "db0303b13bb18ba4c96085b1734e2e044e6d93efa1640eaf9249ff761bb643b7"
    assert args[0].resolved_generation_hash == "4a7e30a2b0c62d18294ec9a217eb7ade8f797519dbbd25bbcbf1855b64c47a7f"
    assert VideoGenerationRequest.model_validate_json(request.model_dump_json()) == request


def test_subject_identity_tampering_cannot_reopen_old_seal():
    _, _, _, request, _ = _compiled()
    data = request.model_dump(mode="json")
    data["subject_bindings"][0]["canonical_owner_content_hash"] = "e" * 64
    with pytest.raises(ValidationError):
        VideoGenerationRequest.model_validate(data)


@pytest.mark.parametrize("mutation", ["missing", "duplicated", "non_reference", "duplicate_name"])
def test_subject_images_are_one_complete_unique_partition(mutation):
    _, _, _, request, _ = _compiled()
    values = request.model_dump(mode="python", exclude={"request_input_hash"})
    subjects = list(request.subject_bindings)
    if mutation == "missing":
        subjects.pop()
    elif mutation == "duplicated":
        subjects[1] = subjects[1].model_copy(update={"image_asset_ids": subjects[0].image_asset_ids})
    elif mutation == "duplicate_name":
        subjects[1] = subjects[1].model_copy(update={"name": subjects[0].name})
    else:
        values["image_bindings"] = (request.image_bindings[0].model_copy(update={"role": "first_frame"}), *request.image_bindings[1:])
    values["subject_bindings"] = tuple(subjects)
    with pytest.raises(ValidationError):
        VideoGenerationRequest.create(**values)


def test_q3_voice_id_is_rejected_before_transport_or_credential_read():
    provider, _, _, request, _ = _compiled()
    values = request.model_dump(mode="python", exclude={"request_input_hash"})
    subjects = tuple(s.model_copy(update={"voice_id": "coco-original"}) if s.canonical_owner_id == "COCO" else s for s in request.subject_bindings)
    values["subject_bindings"] = subjects
    request = VideoGenerationRequest.create(**values)
    with pytest.raises(AiVideoError) as exc:
        provider.resolve(request)
    assert exc.value.code == ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED


def test_compiler_rejects_owner_and_authored_membership_substitution():
    from ai_video.production._vidu_subjects import derive_vidu_subjects
    _, bound, requirement, _, _ = _compiled()
    with pytest.raises(ValueError):
        derive_vidu_subjects(requirement, bound.model_copy(update={
            "input_assets": (bound.input_assets[0].model_copy(update={"canonical_owner_content_hash": "e" * 64}), *bound.input_assets[1:]),
        }))
    with pytest.raises(ValueError):
        derive_vidu_subjects(requirement.model_copy(update={"characters": tuple(c.model_copy(update={"reference_asset_ids": ()}) for c in requirement.characters)}), bound)


@pytest.mark.parametrize("version,capability", [("3", "viduq3-r2v-subjects-v1"), ("4", "viduq3-r2v-v1")])
def test_subject_compiler_and_capability_must_be_selected_together(version, capability):
    _named_route(compiler_version=version, capability_id=capability, expect_blocked=True)


def test_complete_intent_reopens_execution_binding_and_rejects_resealed_subject_swap():
    from ai_video.planning.video_planner import VideoPlanner
    from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
    from ai_video.production.generation_decision import DecisionInputs, GenerationCandidate
    from ai_video.production.generation_recipe import GenerationRecipe, SeedPolicy
    from production_generation_execution_factory import fixture_generation_expression
    from test_production_generation_decision import acceptance_policy, setup_decision
    provider, projection, context, lifecycle = _named_route(complete=True, setup=True)
    compiler = AdapterCompilerContract.create(compiler_id="vidu-video-compiler", compiler_version="4")
    output = _request().output_requirement
    expression = fixture_generation_expression(output)
    acceptance = acceptance_policy((expression,))
    recipe = GenerationRecipe(seed=SeedPolicy(kind="fixed", value=42), profile_sha256=_profile().pointer().profile_sha256,
        compiler_hash=compiler.compiler_hash, requirement_hash=projection.requirement.requirement_hash,
        rubric_hash=acceptance.profile_content_hash, acceptance_policy=acceptance, expressions=(expression,))
    candidate = GenerationCandidate(candidate_id="one", provider_profile=_profile().pointer(),
        capabilities=provider.capabilities(), capability_id="viduq3-r2v-subjects-v1",
        compiler_contract=compiler, output_requirement=output, recipe=recipe)
    base = setup_decision(remote=True)["inputs"]
    inputs = DecisionInputs.model_validate({**base.model_dump(mode="python"),
        "projection_hash": projection.projection_hash,
        "facts_hash": VideoPlanner.generation_difficulty(projection)["facts_hash"],
        "rubric_hash": acceptance.profile_content_hash, "candidates": (candidate,),
        "limits": base.limits.model_copy(update={"allowed_remote_candidates": ("one",)}),
    })
    values = dict(projection=projection, context=context, policy=_policy(remote_authorized=True, budget_authorized=True),
                  lifecycle=lifecycle, inputs=inputs)
    decision = VideoGenerationResolver().resolve_requirement(**values)
    assert decision.disposition == "GENERATE_ONCE", decision.rationale
    compiled = provider.compile_request(decision.routing.provider_bound_request, projection.requirement)
    assert isinstance(compiled, CompiledProviderVideoRequest), compiled
    resolved = provider.resolve(compiled.request)
    binding = GenerationDecisionExecutionBinding.create(**values, decision=decision, compiled_request=resolved)
    assert GenerationDecisionExecutionBinding.model_validate_json(binding.model_dump_json()) == binding
    changed = compiled.request.model_dump(mode="python", exclude={"request_input_hash"})
    subjects = list(compiled.request.subject_bindings)
    first, second = subjects[:2]
    subjects[0] = first.model_copy(update={"image_asset_ids": second.image_asset_ids})
    subjects[1] = second.model_copy(update={"image_asset_ids": first.image_asset_ids})
    changed["subject_bindings"] = tuple(subjects)
    swapped = provider.resolve(VideoGenerationRequest.create(**changed))
    assert swapped.resolved_generation_hash != resolved.resolved_generation_hash
    with pytest.raises(ValidationError, match="canonical inputs"):
        GenerationDecisionExecutionBinding.create(**values, decision=decision, compiled_request=swapped)


def test_subject_prompt_assigns_one_dialogue_speaker_without_repeating_script():
    from types import SimpleNamespace
    from ai_video.production._vidu_prompt import compile_vidu_subject_prompt
    from ai_video.production._vidu_subjects import derive_vidu_subjects
    from ai_video.production.video_requirement import DialogueIntent
    _, bound, requirement, _ = _named_route(complete=True)
    subjects = derive_vidu_subjects(requirement, bound)
    line = "Nosha, press the transparent spiral button once."
    dialogue = DialogueIntent(mode="dialogue", speaker_id="COCO", language="en-US", verbatim_text=line,
        start_seconds=1, end_seconds=4, on_screen=True, lip_sync_required=True,
        response_obligation="Nosha presses the button once")
    requirement = requirement.model_copy(update={
        "generation_intent": requirement.generation_intent.model_copy(update={"dialogue_intent": dialogue}),
        "voice_routing": SimpleNamespace(speakers=(SimpleNamespace(speaker_id="COCO"),)),
    })
    prompt = compile_vidu_subject_prompt(requirement, bound, subjects)
    assert prompt.outcome == "compiled"
    assert prompt.prompt_text.count(line) == 1
    coco = next(s for s in subjects if s.canonical_owner_id == "COCO")
    assert f"Dialogue speaker: @{coco.name}." in prompt.prompt_text


@pytest.mark.parametrize("voice", [False, True])
def test_q3_subject_capability_declares_bounds_and_no_voice_claim(voice):
    from ai_video.production.video_subjects import subject_capability_errors
    provider, _, _, request, _ = _compiled()
    capability = next(v for v in provider.capabilities().variants if v.capability_id == "viduq3-r2v-subjects-v1")
    assert capability.subject_reference_capability.voice_ids_supported is False
    subjects = (request.subject_bindings[0].model_copy(update={
        "image_asset_ids": ("a", "b", "c", "d") if not voice else ("a",),
        "voice_id": "original" if voice else None,
    }),)
    assert subject_capability_errors(subjects, capability)
