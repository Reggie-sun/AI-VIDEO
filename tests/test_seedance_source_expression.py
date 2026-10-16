"""Source-part Seedance compilation stays exact and only attests grounded facts."""

import hashlib
from types import SimpleNamespace

import pytest

from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.seedance_source_expression import (
    PreservedSourceExpression,
    SourceReferenceMaterial,
    SourceReferencePart,
    SourceImageAlias,
    SourceStateGrounding,
    SourceTextPart,
    _adapt_source_text,
    _image_indices,
    compile_preserved_seedance_source,
    source_parts_sha256,
    source_state_facts,
)


def _expression(parts, *, implicit_references=(), opening=(), closing=()):
    return PreservedSourceExpression(
        source_sha256=source_parts_sha256(parts, implicit_references),
        parts=parts,
        implicit_references=implicit_references,
        opening=opening,
        closing=closing,
    )


@pytest.mark.parametrize("changed", ["slot_bytes", "asset_role"])
def test_v2_repeated_material_conflicts_fail_closed(changed):
    material = SourceReferenceMaterial(asset_id="same", asset_sha256="a" * 64, role="identity")
    other = material.model_copy(update={"asset_sha256": "b" * 64} if changed == "slot_bytes"
        else {"role": "scene"})
    parts = (SourceReferencePart(slot_id="slot", materials=(material,)),
        SourceReferencePart(slot_id="slot" if changed == "slot_bytes" else "other", materials=(other,)))
    with pytest.raises(ValueError, match="repeated source"):
        PreservedSourceExpression(contract_version="seedance-preserved-source/2",
            source_sha256=source_parts_sha256(parts), parts=parts)
    # Historical /1 still rejects even an identical repeated chip.
    duplicate = (parts[0], parts[0])
    with pytest.raises(ValueError, match="slots must be unique"):
        _expression(duplicate)


def test_v2_explicit_literal_alias_uses_actual_native_index_and_preserves_source():
    parts = (SourceTextPart(text="图1 locks the device; 图10 is unrelated prose."),)
    implicit = (SourceReferenceMaterial(asset_id="device", asset_sha256="a" * 64, role="scene"),)
    expression = PreservedSourceExpression(contract_version="seedance-preserved-source/2",
        source_sha256=source_parts_sha256(parts, implicit), parts=parts, implicit_references=implicit,
        image_aliases=(SourceImageAlias(label="图1", asset_ids=("device",)),))
    assert _adapt_source_text(expression, {("scene", "device", "a" * 64): 2}) == (
        "图片2 locks the device; 图10 is unrelated prose.")
    assert expression.parts[0].text == parts[0].text
    with pytest.raises(ValueError, match="exact selected materials"):
        PreservedSourceExpression.model_validate(expression.model_dump(mode="python") | {
            "image_aliases": [{"label": "图1", "asset_ids": ["other"]}]})
    assert "image_aliases" not in _expression((SourceTextPart(text="Legacy"),)).model_dump()


def test_source_video_reference_uses_its_own_video_number_and_preserved_literal():
    from ai_video.production.video_requirement import SemanticReferenceRole

    digest = "c" * 64
    scene = SourceReferenceMaterial(asset_id="scene-still", asset_sha256="d" * 64, role="scene")
    material = SourceReferenceMaterial(asset_id="accepted-a", asset_sha256=digest, role="video_reference")
    parts = (SourceTextPart(text="图片1继续动作。"),
             SourceReferencePart(slot_id="media", materials=(scene, material)))
    expression = PreservedSourceExpression(contract_version="seedance-preserved-source/2",
        source_sha256=source_parts_sha256(parts), parts=parts,
        image_aliases=(SourceImageAlias(label="图片1", asset_ids=("accepted-a",)),))
    requirement = SimpleNamespace(asset_evidence=(
        SimpleNamespace(role=SemanticReferenceRole.SCENE, asset_id="scene-still", asset_sha256="d" * 64),
        SimpleNamespace(role=SemanticReferenceRole.VIDEO_REFERENCE, asset_id="accepted-a", asset_sha256=digest)))
    bound = SimpleNamespace(binding_roles=("reference", "reference_video"), input_assets=(
        SimpleNamespace(asset_id="scene-still", asset_sha256="d" * 64, role="scene_reference"),
        SimpleNamespace(asset_id="accepted-a", asset_sha256=digest, role="reference_video")))

    indices = _image_indices(bound, requirement, expression)

    assert indices == {("scene", "scene-still", "d" * 64): 1,
                       ("video_reference", "accepted-a", digest): 1}
    assert _adapt_source_text(expression, indices) == "视频1继续动作。图片1、视频1"


def test_shared_source_media_indexing_preserves_native_order_and_separate_media_ordinals():
    from ai_video.production import seedance_source_expression as source_expression

    media = (
        ("reference", "scene-a", "a" * 64, "scene"),
        ("reference", "character-b", "b" * 64, "identity"),
        ("first_frame", "opening", "c" * 64, "first_frame"),
        ("reference_video", "video-z", "d" * 64, "video_reference"),
        ("reference_video", "video-a", "e" * 64, "video_reference"),
    )

    index_media = getattr(source_expression, "_source_media_indices", lambda _: {})
    assert index_media(media) == {
        ("first_frame", "opening", "c" * 64): 1,
        ("identity", "character-b", "b" * 64): 2,
        ("scene", "scene-a", "a" * 64): 3,
        ("video_reference", "video-a", "e" * 64): 1,
        ("video_reference", "video-z", "d" * 64): 2,
    }


def _rebind_source_expression(bound, requirement, expression, prompt):
    from ai_video.production.shot_router import ProviderBoundVideoRequest
    from ai_video.production.video_requirement import ProviderNeutralVideoRequirement

    shot = seal_artifact(
        requirement.target_shot.model_copy(
            update={"intent": prompt, "preserved_source_expression": expression}
        )
    )
    rewritten_requirement = ProviderNeutralVideoRequirement.create(
        **{
            **requirement.model_dump(
                mode="python", exclude={"requirement_id", "requirement_hash"}
            ),
            "target_shot": shot,
        }
    )
    bound_data = {
        name: getattr(bound, name)
        for name in ProviderBoundVideoRequest.model_fields
        if name != "provider_bound_request_hash"
    }
    bound_data.update(
        requirement_hash=rewritten_requirement.requirement_hash,
        target_shot_content_hash=shot.content_hash,
        generation_recipe=bound.generation_recipe.model_copy(
            update={"requirement_hash": rewritten_requirement.requirement_hash}
        ),
    )
    rewritten_bound = ProviderBoundVideoRequest.create(**bound_data)
    return rewritten_bound, rewritten_requirement


def test_preserved_source_hash_and_partial_facts_keep_source_order_and_dimensions():
    from ai_video.production.video_transition import CausalDimension

    parts = (
        SourceTextPart(text="蚂蚁围绕瓶子行走。"),
        SourceReferencePart(
            slot_id="subject",
            materials=(
                SourceReferenceMaterial(
                    asset_id="identity-main",
                    asset_sha256="a" * 64,
                    role="identity",
                ),
                SourceReferenceMaterial(
                    asset_id="identity-aux",
                    asset_sha256="b" * 64,
                    role="identity",
                ),
            ),
        ),
    )
    expression = _expression(
        parts,
        opening=(
            SourceStateGrounding(
                dimension="prop_identity", kind="reference", fact="瓶子",
                asset_id="identity-main", asset_sha256="a" * 64,
            ),
            SourceStateGrounding(
                dimension="action_phase", kind="quote", fact="围绕瓶子行走",
            ),
        ),
    )

    assert expression.parts == parts
    assert expression.source_sha256 == source_parts_sha256(parts)
    assert tuple(item.dimension for item in expression.opening) == (
        "action_phase", "prop_identity"
    )
    facts = source_state_facts(expression, "opening")
    assert facts == {
        CausalDimension.ACTION_PHASE: "围绕瓶子行走",
        CausalDimension.PROP_IDENTITY: "瓶子",
    }
    with pytest.raises(ValueError, match="parts hash"):
        PreservedSourceExpression(source_sha256="0" * 64, parts=parts)


@pytest.mark.parametrize(
    "grounding_values",
    [
        {"dimension": "action_phase", "kind": "quote", "fact": "未出现的动作"},
        {
            "dimension": "action_phase", "kind": "reference", "fact": "动作",
            "asset_id": "selected", "asset_sha256": "a" * 64,
        },
        {
            "dimension": "prop_identity", "kind": "reference", "fact": "瓶子",
            "asset_id": "selected", "asset_sha256": "b" * 64,
        },
    ],
)
def test_groundings_require_literal_quotes_or_exact_static_identity_images(grounding_values):
    parts = (
        SourceTextPart(text="瓶子保持在画面里。"),
        SourceReferencePart(
            slot_id="identity",
            materials=(SourceReferenceMaterial(
                asset_id="selected", asset_sha256="a" * 64, role="identity"
            ),),
        ),
    )
    with pytest.raises(ValueError):
        grounding = SourceStateGrounding(**grounding_values)
        _expression(parts, opening=(grounding,))


def test_subject_main_and_auxiliary_chips_expand_using_common_native_image_order():
    from ai_video.production.video_requirement import SemanticReferenceRole

    expression = _expression(
        (
            SourceTextPart(text="主体："),
            SourceReferencePart(
                slot_id="subject",
                materials=(
                    SourceReferenceMaterial(
                        asset_id="z-main", asset_sha256="b" * 64, role="identity"
                    ),
                    SourceReferenceMaterial(
                        asset_id="a-aux", asset_sha256="a" * 64, role="identity"
                    ),
                ),
            ),
            SourceTextPart(text="。"),
        )
    )
    requirement = SimpleNamespace(
        asset_evidence=(
            SimpleNamespace(
                role=SemanticReferenceRole.IDENTITY,
                asset_id="z-main",
                asset_sha256="b" * 64,
            ),
            SimpleNamespace(
                role=SemanticReferenceRole.IDENTITY,
                asset_id="a-aux",
                asset_sha256="a" * 64,
            ),
        )
    )
    bound = SimpleNamespace(
        binding_roles=("reference", "reference"),
        input_assets=(
            SimpleNamespace(asset_id="z-main", asset_sha256="b" * 64, role="character_reference"),
            SimpleNamespace(asset_id="a-aux", asset_sha256="a" * 64, role="character_reference"),
        ),
    )

    indices = _image_indices(bound, requirement, expression)
    assert indices == {
        ("identity", "a-aux", "a" * 64): 1,
        ("identity", "z-main", "b" * 64): 2,
    }
    assert _adapt_source_text(expression, indices) == "主体：图片2、图片1。"
    bad_bound = SimpleNamespace(
        binding_roles=("reference", "reference"),
        input_assets=(
            SimpleNamespace(asset_id="z-main", asset_sha256="c" * 64, role="character_reference"),
            SimpleNamespace(asset_id="a-aux", asset_sha256="a" * 64, role="character_reference"),
        ),
    )
    with pytest.raises(ValueError, match="exact selected roles and bytes"):
        _image_indices(bad_bound, requirement, expression)


def test_text_to_video_source_compiles_exact_original_text_with_only_grounded_controls():
    from ai_video.production.video_compiler import ProviderNativePrompt
    from test_seedance_source_prompt import _case

    _, bound, requirement, source = _case()
    expression = _expression((SourceTextPart(text=source),))
    rebound, rewritten_requirement = _rebind_source_expression(
        bound, requirement, expression, source
    )

    compiled = compile_preserved_seedance_source(rebound, rewritten_requirement)

    assert isinstance(compiled, ProviderNativePrompt)
    assert compiled.grammar_contract == "seedance-preserved-source-v1"
    assert compiled.prompt_text == source
    assert compiled.prompt_sha256
    assert compiled.expressed_control_paths == (
        "generation_intent.subject_action.progression",
        "generation_intent.pacing.shot_duration_seconds",
    )


def test_i2v_first_frame_is_sealed_as_implicit_reference_without_changing_prose():
    from test_seedance_source_prompt import _case

    _, bound, requirement, source = _case(first_frame=True)
    frame = requirement.asset_evidence[0]
    expression = _expression(
        (SourceTextPart(text=source),),
        implicit_references=(
            SourceReferenceMaterial(
                asset_id=frame.asset_id,
                asset_sha256=frame.asset_sha256,
                role="first_frame",
            ),
        ),
    )
    rebound, rewritten_requirement = _rebind_source_expression(
        bound, requirement, expression, source
    )

    compiled = compile_preserved_seedance_source(rebound, rewritten_requirement)

    assert compiled.prompt_text == source
    assert "图片1" not in compiled.prompt_text


def test_partial_typed_close_hash_must_match_its_nonempty_authored_facts():
    from ai_video.production.video_requirement import (
        ProviderNeutralVideoRequirement,
        TypedStateReference,
    )
    from test_seedance_source_prompt import _case

    _, bound, requirement, source = _case()
    fact = source[:4]
    expression = _expression(
        (SourceTextPart(text=source),),
        closing=(
            SourceStateGrounding(
                dimension="action_phase", kind="quote", fact=fact
            ),
        ),
    )
    state_hash = canonical_sha256({"action_phase": fact})
    intent = requirement.generation_intent.model_copy(
        update={
            "close_state": TypedStateReference(
                kind="typed_hash", state_hash=state_hash
            )
        }
    )
    hashed_requirement = ProviderNeutralVideoRequirement.create(
        **{
            **requirement.model_dump(
                mode="python", exclude={"requirement_id", "requirement_hash"}
            ),
            "generation_intent": intent,
        }
    )
    rebound, rewritten_requirement = _rebind_source_expression(
        bound, hashed_requirement, expression, source
    )

    compiled = compile_preserved_seedance_source(rebound, rewritten_requirement)
    assert "generation_intent.close_state.state_hash" in compiled.expressed_control_paths

    wrong_intent = intent.model_copy(
        update={
            "close_state": TypedStateReference(
                kind="typed_hash", state_hash="f" * 64
            )
        }
    )
    wrong_requirement = ProviderNeutralVideoRequirement.create(
        **{
            **requirement.model_dump(
                mode="python", exclude={"requirement_id", "requirement_hash"}
            ),
            "generation_intent": wrong_intent,
        }
    )
    wrong_bound, wrong_requirement = _rebind_source_expression(
        bound, wrong_requirement, expression, source
    )
    with pytest.raises(ValueError, match="closing hash"):
        compile_preserved_seedance_source(wrong_bound, wrong_requirement)


def test_empty_typed_opening_facts_cannot_attest_a_hash():
    from ai_video.production.video_requirement import (
        ProviderNeutralVideoRequirement,
        TypedStateReference,
    )
    from test_seedance_source_prompt import _case

    _, bound, requirement, source = _case()
    expression = _expression((SourceTextPart(text=source),))
    intent = requirement.generation_intent.model_copy(
        update={
            "open_state": TypedStateReference(
                kind="typed_hash", state_hash="e" * 64
            )
        }
    )
    hashed_requirement = ProviderNeutralVideoRequirement.create(
        **{
            **requirement.model_dump(
                mode="python", exclude={"requirement_id", "requirement_hash"}
            ),
            "generation_intent": intent,
        }
    )
    rebound, rewritten_requirement = _rebind_source_expression(
        bound, hashed_requirement, expression, source
    )

    with pytest.raises(ValueError, match="requires authored partial facts"):
        compile_preserved_seedance_source(rebound, rewritten_requirement)


@pytest.mark.parametrize("damage", [None, "text", "claimed_control", "compiler"])
def test_common_compiler_recompiles_source_instead_of_trusting_grammar_claims(damage):
    from ai_video.production.shot_router import AdapterCompilerContract, ProviderBoundVideoRequest
    from ai_video.production.seedance import SeedanceVideoProvider
    from ai_video.production.video_compiler import (
        CompiledProviderVideoRequest, compile_provider_video_request,
    )
    from test_seedance_source_prompt import _case

    profile, bound, requirement, source = _case()
    expression = _expression((SourceTextPart(text=source),))
    bound, requirement = _rebind_source_expression(bound, requirement, expression, source)
    compiler = AdapterCompilerContract.create(compiler_id="seedance-video-compiler", compiler_version="3")
    bound = ProviderBoundVideoRequest.create(**{
        **{key: getattr(bound, key) for key in type(bound).model_fields
           if key != "provider_bound_request_hash"},
        "compiler_contract": compiler,
        "generation_recipe": bound.generation_recipe.model_copy(update={"compiler_hash": compiler.compiler_hash}),
    })
    native = compile_preserved_seedance_source(bound, requirement)
    if damage == "text":
        text = source + " Invented action."
        native = type(native)(prompt_text=text, prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
            expressed_control_paths=native.expressed_control_paths,
            grammar_contract=native.grammar_contract)
    elif damage == "claimed_control":
        native = type(native)(prompt_text=source, prompt_sha256=native.prompt_sha256,
            expressed_control_paths=(*native.expressed_control_paths, "generation_intent.camera_intent.movement"),
            grammar_contract=native.grammar_contract)
    result = compile_provider_video_request(provider_bound=bound, requirement=requirement,
        compiler_id=compiler.compiler_id, compiler_version="2" if damage == "compiler" else "3",
        capabilities=SeedanceVideoProvider(profile=profile, transport=object(),
            credential=lambda: pytest.fail("pure compilation read secret"), input_reference=object()).capabilities(),
        native_prompt=native)
    if damage is None:
        assert isinstance(result, CompiledProviderVideoRequest)
        assert result.request.prompt_text == source
    else:
        assert result.outcome == "unsupported"
