"""Sealed source parts and a partial, source-grounded Seedance projection."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_serializer, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash


_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"
_DIMENSION = Literal[
    "character_presence",
    "prop_identity",
    "prop_holder",
    "hand_contact",
    "prop_functional_state",
    "action_phase",
    "gaze_target",
    "dialogue_turn",
    "screen_motion_axis",
    "audio_bridge",
]
_ASSET_ROLE = Literal["identity", "scene", "first_frame", "last_frame", "video_reference"]
_GROUNDABLE_REFERENCE_DIMENSIONS = {"character_presence", "prop_identity"}
_SOURCE_COMPILER_IDENTITIES = {
    ("seedance", "seedance-video-compiler", "3"): "seedance-preserved-source-v1",
    ("metaso_h3", "metaso-h3-video-compiler", "1"): "metaso-h3-preserved-source-v1",
}


def is_preserved_source_grammar_contract(value: str) -> bool:
    return value in _SOURCE_COMPILER_IDENTITIES.values()


class SourceTextPart(StrictModel):
    type: Literal["text"] = "text"
    text: str


class SourceReferenceMaterial(StrictModel):
    asset_id: str = Field(pattern=_SAFE_ID)
    asset_sha256: str = Field(pattern=_SHA256)
    role: _ASSET_ROLE


class SourceReferencePart(StrictModel):
    type: Literal["reference"] = "reference"
    slot_id: str = Field(pattern=_SAFE_ID)
    materials: tuple[SourceReferenceMaterial, ...] = Field(min_length=1)


class SourceImageAlias(StrictModel):
    """Approved literal media label mapped to the original tray's materials."""

    label: str = Field(pattern=r"^(?:(?:图|图片|视频)(?:[1-9][0-9]*|[一二三四五六七八九十]+))$")
    asset_ids: tuple[str, ...] = Field(min_length=1)


SourcePart = Annotated[
    SourceTextPart | SourceReferencePart,
    Field(discriminator="type"),
]


class SourceStateGrounding(StrictModel):
    dimension: _DIMENSION
    kind: Literal["quote", "reference"]
    fact: str = Field(min_length=1)
    asset_id: str | None = Field(default=None, pattern=_SAFE_ID)
    asset_sha256: str | None = Field(default=None, pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_grounding_kind(self) -> "SourceStateGrounding":
        if not self.fact.strip() or unicodedata.normalize("NFC", self.fact) != self.fact:
            raise ValueError("source grounding fact must be nonempty NFC text")
        if self.fact.strip().casefold() == "unspecified":
            raise ValueError("source grounding cannot use an unspecified sentinel")
        if re.fullmatch(_SHA256, self.fact.strip()):
            raise ValueError("source grounding fact cannot be a digest")
        if self.kind == "quote":
            if self.asset_id is not None or self.asset_sha256 is not None:
                raise ValueError("quoted source grounding cannot carry image identity")
        else:
            if self.dimension not in _GROUNDABLE_REFERENCE_DIMENSIONS:
                raise ValueError("source image grounding only supports static identity facts")
            if self.asset_id is None or self.asset_sha256 is None:
                raise ValueError("source image grounding requires exact asset ID and SHA-256")
        return self


def _model_data(value: object) -> dict[str, object]:
    if isinstance(value, StrictModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return dict(value)
    raise TypeError("source parts must be validated models or mappings")


def source_parts_sha256(
    parts: tuple[SourcePart, ...] | list[SourcePart],
    implicit_references: tuple[SourceReferenceMaterial, ...]
    | list[SourceReferenceMaterial] = (),
) -> str:
    """Hash the raw ordered source parts and exact implicit references."""
    return canonical_sha256(
        {
            "parts": [_model_data(part) for part in parts],
            "implicit_references": [
                _model_data(reference) for reference in implicit_references
            ],
        }
    )


class PreservedSourceExpression(StrictModel):
    contract_version: Literal["seedance-preserved-source/1", "seedance-preserved-source/2"] = (
        "seedance-preserved-source/1"
    )
    source_sha256: str = Field(pattern=_SHA256)
    parts: tuple[SourcePart, ...] = Field(min_length=1)
    implicit_references: tuple[SourceReferenceMaterial, ...] = ()
    opening: tuple[SourceStateGrounding, ...] = ()
    closing: tuple[SourceStateGrounding, ...] = ()
    image_aliases: tuple[SourceImageAlias, ...] = ()

    @model_serializer(mode="wrap")
    def _serialize_version(self, handler):
        result = handler(self)
        if self.contract_version == "seedance-preserved-source/1":
            result.pop("image_aliases", None)
        return result

    @field_validator("opening", "closing")
    @classmethod
    def _canonical_groundings(
        cls, value: tuple[SourceStateGrounding, ...]
    ) -> tuple[SourceStateGrounding, ...]:
        dimensions = tuple(item.dimension for item in value)
        if len(dimensions) != len(set(dimensions)):
            raise ValueError("source endpoint dimensions must be unique")
        return tuple(sorted(value, key=lambda item: item.dimension))

    @model_validator(mode="after")
    def _validate_source_expression(self) -> "PreservedSourceExpression":
        if self.source_sha256 != source_parts_sha256(
            self.parts, self.implicit_references
        ):
            raise ValueError("preserved source parts hash does not match")

        slots = tuple(
            part.slot_id for part in self.parts if isinstance(part, SourceReferencePart)
        )
        legacy = self.contract_version == "seedance-preserved-source/1"
        if legacy and len(slots) != len(set(slots)):
            raise ValueError("source reference slots must be unique")
        materials = [
            material
            for part in self.parts
            if isinstance(part, SourceReferencePart)
            for material in part.materials
        ]
        materials.extend(self.implicit_references)
        asset_ids = tuple(material.asset_id for material in materials)
        if legacy and len(asset_ids) != len(set(asset_ids)):
            raise ValueError("preserved source image references must be unique")
        if legacy and any(material.role != "first_frame" for material in self.implicit_references):
            raise ValueError("only first-frame images may be implicit source references")
        if not legacy:
            by_slot, by_asset = {}, {}
            for part in self.parts:
                if isinstance(part, SourceReferencePart):
                    if part.slot_id in by_slot and by_slot[part.slot_id] != part.materials:
                        raise ValueError("repeated source slot changed its exact materials")
                    by_slot[part.slot_id] = part.materials
            for material in materials:
                if material.asset_id in by_asset and by_asset[material.asset_id] != material:
                    raise ValueError("repeated source image changed its role or bytes")
                by_asset[material.asset_id] = material
        if any(
            material.role not in {"identity", "scene", "video_reference"}
            for part in self.parts
            if isinstance(part, SourceReferencePart)
            for material in part.materials
        ):
            raise ValueError("source reference chips only support identity/scene images or video references")

        text_parts = tuple(
            part.text for part in self.parts if isinstance(part, SourceTextPart)
        )
        if legacy and self.image_aliases:
            raise ValueError("image label adaptation requires preserved source /2")
        if len({a.label for a in self.image_aliases}) != len(self.image_aliases):
            raise ValueError("source image aliases must be unique")
        for alias in self.image_aliases:
            if (not any(re.search(re.escape(alias.label) + r"(?![0-9一二三四五六七八九十])", text)
                    for text in text_parts)
                    or len(set(alias.asset_ids)) != len(alias.asset_ids)
                    or not set(alias.asset_ids) <= set(asset_ids)):
                raise ValueError("source image alias requires original text and exact selected materials")
        exact_materials = {
            (material.asset_id, material.asset_sha256, material.role): material
            for material in materials
        }
        for endpoint in (self.opening, self.closing):
            for grounding in endpoint:
                if grounding.kind == "quote":
                    if not any(grounding.fact in text for text in text_parts):
                        raise ValueError("quoted grounding must occur in original source text")
                elif (
                    (grounding.asset_id, grounding.asset_sha256, "identity")
                    not in exact_materials
                ):
                    raise ValueError(
                        "reference grounding must match an exact selected identity image"
                    )
        return self


def source_state_facts(
    expression: PreservedSourceExpression,
    endpoint: Literal["opening", "closing"],
) -> dict[object, str]:
    """Return only authored partial facts, keyed by the existing dimension enum."""
    if endpoint not in {"opening", "closing"}:
        raise ValueError("source endpoint must be opening or closing")
    if type(expression) is not PreservedSourceExpression:
        raise ValueError("source state facts require the exact preserved expression model")
    reopened = PreservedSourceExpression.model_validate(
        expression.model_dump(mode="python")
    )
    from ai_video.production.video_transition import CausalDimension

    return {
        CausalDimension(item.dimension): item.fact
        for item in getattr(reopened, endpoint)
    }


def _validated_source_expression(shot):
    expression = getattr(shot, "preserved_source_expression", None)
    if type(expression) is not PreservedSourceExpression:
        raise ValueError("approved Shot has no preserved Seedance source expression")
    return PreservedSourceExpression.model_validate(
        expression.model_dump(mode="python")
    )


def _source_materials(expression: PreservedSourceExpression):
    materials = tuple(
        material
        for part in expression.parts
        if isinstance(part, SourceReferencePart)
        for material in part.materials
    ) + expression.implicit_references
    if expression.contract_version == "seedance-preserved-source/2":
        return tuple({m.asset_id: m for m in materials}.values())
    return materials


def _image_indices(bound, requirement, expression: PreservedSourceExpression):
    from ai_video.production._video_requirement_routing import (
        context_asset_role,
        native_binding_role,
    )
    from ai_video.production.video_compiler import _MEDIA_ROLE_ORDER, _ROLE_ORDER

    evidence = tuple(requirement.asset_evidence)
    expected = tuple(
        (item.role.value, item.asset_id, item.asset_sha256) for item in evidence
    )
    source = tuple(
        (item.role, item.asset_id, item.asset_sha256)
        for item in _source_materials(expression)
    )
    if len(expected) != len(source) or set(expected) != set(source):
        raise ValueError("source references must exactly match selected media evidence")
    if len(set(expected)) != len(expected):
        raise ValueError("selected source image evidence must be unique")

    if len(bound.binding_roles) != len(bound.input_assets):
        raise ValueError("provider-bound source image roles do not match selected assets")
    paired = tuple(zip(bound.binding_roles, bound.input_assets, strict=True))
    image_pairs = []
    video_pairs = []
    for native_role, asset in paired:
        if native_role not in {*_ROLE_ORDER, "reference_video"}:
            raise ValueError("preserved source does not support audio or other input references")
        matching = tuple(
            item
            for item in evidence
            if item.asset_id == asset.asset_id
            and item.asset_sha256 == asset.asset_sha256
            and native_binding_role(item.role) == native_role
            and context_asset_role(item.role) == asset.role
        )
        if len(matching) != 1:
            raise ValueError("bound source images do not match exact selected roles and bytes")
        pair = (native_role, asset.asset_id, asset.asset_sha256, matching[0].role.value)
        if native_role == "reference_video":
            if matching[0].role.value != "video_reference" or asset.role != "reference_video":
                raise ValueError("bound source videos do not match exact selected video roles and bytes")
            video_pairs.append(pair)
        else:
            if matching[0].role.value == "video_reference" or asset.role == "reference_video":
                raise ValueError("bound source image does not match its selected image role")
            image_pairs.append(pair)
    if len(image_pairs) + len(video_pairs) != len(expected):
        raise ValueError("bound source media does not match selected evidence count")
    bound_keys = tuple((native_role, asset_id, asset_sha256)
        for native_role, asset_id, asset_sha256, _ in (*image_pairs, *video_pairs))
    expected_bound_keys = tuple(
        (native_binding_role(item.role), item.asset_id, item.asset_sha256)
        for item in evidence
    )
    if len(set(bound_keys)) != len(bound_keys) or set(bound_keys) != set(expected_bound_keys):
        raise ValueError("bound source media references must exactly match selected role and byte identities")
    indices = {
        (role, asset_id, asset_sha256): index
        for index, (_, asset_id, asset_sha256, role) in enumerate(
            sorted(image_pairs, key=lambda item: (_ROLE_ORDER[item[0]], item[1])),
            start=1,
        )
    }
    indices.update({
        (role, asset_id, asset_sha256): index
        for index, (_, asset_id, asset_sha256, role) in enumerate(
            sorted(video_pairs, key=lambda item: (_MEDIA_ROLE_ORDER[item[0]], item[1])),
            start=1,
        )
    })
    return indices


def _adapt_source_text(
    expression: PreservedSourceExpression,
    image_indices: dict[tuple[str, str, str], int],
) -> str:
    chunks: list[str] = []
    indices_by_asset = {asset_id: (role, index)
        for (role, asset_id, _), index in image_indices.items()}
    def label(asset_id):
        role, index = indices_by_asset[asset_id]
        return f"视频{index}" if role == "video_reference" else f"图片{index}"
    aliases = {alias.label: "、".join(label(aid) for aid in alias.asset_ids)
        for alias in expression.image_aliases}
    pattern = ("|".join(re.escape(label) for label in sorted(aliases, key=len, reverse=True))
        + r"(?![0-9一二三四五六七八九十])") if aliases else None
    for part in expression.parts:
        if isinstance(part, SourceTextPart):
            chunks.append(re.sub(pattern, lambda match: aliases[match.group()], part.text)
                if pattern else part.text)
        else:
            chunks.append(
                "、".join(
                    label(material.asset_id)
                    for material in part.materials
                )
            )
    return "".join(chunks)


def _require_source_identity(bound, requirement, shot, *, provider_name):
    from ai_video.production.models import Shot
    from ai_video.production.shot_router import ProviderBoundVideoRequest
    from ai_video.production.video_requirement import ProviderNeutralVideoRequirement

    if type(shot) is not Shot or not verify_artifact_hash(shot):
        raise ValueError("preserved source requires an exact sealed approved Shot")
    if type(requirement) is not ProviderNeutralVideoRequirement:
        raise ValueError("preserved source requires a provider-neutral requirement")
    if type(bound) is not ProviderBoundVideoRequest:
        raise ValueError("preserved source requires a provider-bound request")
    reopened_requirement = ProviderNeutralVideoRequirement.model_validate(
        requirement.model_dump(mode="python")
    )
    reopened_bound = ProviderBoundVideoRequest.model_validate(
        bound.model_dump(mode="python")
    )
    if (
        reopened_bound.requirement_hash != reopened_requirement.requirement_hash
        or reopened_bound.provider_name != provider_name
        or reopened_bound.target_shot_id != shot.shot_id
        or reopened_bound.target_shot_revision != shot.revision
        or reopened_bound.target_shot_content_hash != shot.content_hash
        or reopened_requirement.target_shot != shot
    ):
        raise ValueError("preserved source is not bound to the exact approved Shot and Provider")
    if reopened_bound.generation_recipe is None:
        raise ValueError("preserved source requires a sealed generation recipe")
    return reopened_bound, reopened_requirement, reopened_requirement.target_shot


def _source_endpoint_controls(requirement, expression):
    from ai_video.production.video_requirement import ContinuityStateKind

    intent = requirement.generation_intent
    opening = intent.open_state
    opening_facts = source_state_facts(expression, "opening")
    opening_control = "generation_intent.open_state.state_hash"
    if opening.kind is ContinuityStateKind.TYPED_HASH:
        if not opening_facts:
            raise ValueError("typed source opening hash requires authored partial facts")
        if opening.state_hash != canonical_sha256({d.value: fact for d, fact in opening_facts.items()}):
            raise ValueError("typed source opening hash differs from authored facts")
        opening_controls = (opening_control,)
    else:
        if opening.state_ref is not None or opening.state_text is not None:
            raise ValueError("preserved source supports only verified typed-hash openings")
        if opening_facts:
            raise ValueError("source opening facts require a typed-hash opening")
        opening_controls = ()

    closing = intent.close_state
    closing_facts = source_state_facts(expression, "closing")
    closing_control = "generation_intent.close_state.state_hash"
    if closing.kind is ContinuityStateKind.TYPED_HASH:
        if not closing_facts:
            raise ValueError("typed source closing hash requires authored partial facts")
        expected_hash = canonical_sha256(
            {dimension.value: fact for dimension, fact in closing_facts.items()}
        )
        if expected_hash != closing.state_hash:
            raise ValueError("typed source closing hash differs from authored facts")
        closing_controls = (closing_control,)
    else:
        if closing.state_ref is not None or closing.state_text is not None:
            raise ValueError("preserved source supports only grounded typed-hash closings")
        if closing_facts:
            raise ValueError("source closing facts require a typed-hash closing")
        closing_controls = ()

    if intent.close_causal_facts is not None:
        raise ValueError("preserved source uses partial endpoint facts, not close_causal_facts")
    endpoint = intent.subject_action.endpoint
    if endpoint.state_ref is not None or endpoint.state_text is not None or endpoint.state_hash is not None:
        raise ValueError("preserved source does not support typed subject endpoints")
    return opening_controls + closing_controls


def _require_endpoint_groundings(requirement, expression, continuity_expression, bound):
    from ai_video.production._causal_prompt_context import VerifiedCausalOpeningExpression
    from ai_video.production.video_requirement import ContinuityStateKind

    controls = _source_endpoint_controls(requirement, expression)
    if requirement.generation_intent.open_state.kind is ContinuityStateKind.TYPED_HASH:
        if type(continuity_expression) is not VerifiedCausalOpeningExpression:
            raise ValueError("typed source opening requires sequence-issued evidence")
        if dict(continuity_expression.opening_facts(requirement, bound)) != source_state_facts(expression, "opening"):
            raise ValueError("verified opening facts differ from source groundings")
    elif continuity_expression is not None:
        raise ValueError("source opening facts require a typed-hash opening")
    return controls


def _source_projection(bound, requirement, *, provider_name):
    """Reopen source identity, prose and images without minting opening authority."""
    from ai_video.production.video_requirement import GenerationMode

    shot = getattr(requirement, "target_shot", None)
    bound, requirement, shot = _require_source_identity(
        bound, requirement, shot, provider_name=provider_name
    )
    expression = _validated_source_expression(shot)
    if expression.contract_version not in {"seedance-preserved-source/1", "seedance-preserved-source/2"}:
        raise ValueError("unsupported preserved source expression contract")

    if (
        requirement.contract_version == "provider-neutral-video-requirement/4"
        or requirement.generation_mode
        not in {
            GenerationMode.TEXT_TO_VIDEO,
            GenerationMode.IMAGE_TO_VIDEO,
            GenerationMode.REFERENCE_TO_VIDEO,
        }
        or requirement.voice_routing is not None
        or bound.voice_route is not None
        or requirement.conditioning_compatibility is not None
    ):
        raise ValueError("preserved source cannot replace rich, voice, or conditioned intent")
    if bound.mode.value != requirement.generation_mode.value:
        raise ValueError("preserved source mode differs from its provider-bound request")

    mode = requirement.generation_mode
    source_references = tuple(
        material
        for part in expression.parts
        if isinstance(part, SourceReferencePart)
        for material in part.materials
    )
    if mode is GenerationMode.TEXT_TO_VIDEO:
        if source_references or expression.implicit_references:
            raise ValueError("text-to-video source cannot carry selected image references")
    elif mode is GenerationMode.IMAGE_TO_VIDEO:
        roles = tuple(role.value for role in requirement.semantic_reference_roles)
        if (
            roles != ("first_frame",)
            or len(requirement.asset_evidence) != 1
            or requirement.asset_evidence[0].role.value != "first_frame"
            or source_references
            or len(expression.implicit_references) != 1
        ):
            raise ValueError("source I2V requires one implicit first-frame image and no reference chip")
    else:
        if expression.contract_version == "seedance-preserved-source/1" and (
                expression.implicit_references or not source_references):
            raise ValueError("source R2V media must be represented by explicit reference chips")
        if not _source_materials(expression) or any(m.role not in {"identity", "scene", "video_reference"}
                for m in _source_materials(expression)):
            raise ValueError("source R2V requires identity/scene images or video references")

    image_indices = _image_indices(bound, requirement, expression)
    prompt = _adapt_source_text(expression, image_indices)
    if not prompt:
        raise ValueError("preserved source prompt must contain original text")
    if shot.intent != prompt:
        raise ValueError("approved Shot intent must equal mechanically adapted source prose")

    intent = requirement.generation_intent
    if intent.subject_action.progression != prompt:
        raise ValueError("source subject-action progression must equal adapted source prose")
    duration = intent.pacing.shot_duration_seconds
    output_duration = getattr(bound.output_requirement, "duration_seconds", None)
    if duration is None or output_duration is None or duration != output_duration:
        raise ValueError("preserved source pacing duration must equal bound output duration")
    return bound, requirement, expression, prompt


def validate_preserved_source_request(bound, requirement, request):
    """Recheck the final source payload under its exact selected Provider compiler."""
    from ai_video.production.video_compiler import (
        _MEDIA_ROLE_ORDER, _compile_image_bindings, _native_recipe_expression_errors,
        _required_measurement,
    )
    from ai_video.production.video_contracts import VideoMediaReferenceBinding

    compiler = bound.compiler_contract
    grammar = _SOURCE_COMPILER_IDENTITIES.get((
        bound.provider_name, compiler.compiler_id, compiler.compiler_version
    ))
    if grammar is None:
        raise ValueError("preserved source has no exact Provider compiler identity")
    bound, requirement, expression, prompt = _source_projection(
        bound, requirement, provider_name=bound.provider_name
    )
    native = _source_native_prompt(
        bound, requirement, prompt,
        _source_endpoint_controls(requirement, expression), grammar_contract=grammar,
    )
    media_bindings = tuple(sorted((VideoMediaReferenceBinding(
        kind="video", role=role, asset_id=asset.asset_id, asset_sha256=asset.asset_sha256,
        mime_type=asset.mime_type, duration_millis=_required_measurement(asset.duration_millis, "duration_millis"),
        size_bytes=_required_measurement(asset.size_bytes, "size_bytes"), width=asset.width,
        height=asset.height, fps=asset.fps)
        for role, asset in zip(bound.binding_roles, bound.input_assets, strict=True)
        if role == "reference_video"), key=lambda item: (_MEDIA_ROLE_ORDER[item.role], item.asset_id)))
    if _native_recipe_expression_errors(bound, requirement, native):
        raise ValueError("preserved source has unexpressed authored intent")
    if (request.provider_name != bound.provider_name
            or request.adapter_compiler_id != compiler.compiler_id
            or request.adapter_compiler_version != compiler.compiler_version
            or request.prompt_text != prompt
            or request.image_bindings != _compile_image_bindings(bound)
            or request.media_bindings != media_bindings or request.subject_bindings
            or request.effective_negative_prompt_text):
        raise ValueError("compiled request differs from preserved source prose or exact image bindings")


def compile_preserved_source(
    bound, requirement, *, provider_name, compiler_id, compiler_version,
    continuity_expression=None,
):
    """Compile source parts under a fixed, Provider-specific prompt grammar."""
    grammar = _SOURCE_COMPILER_IDENTITIES.get((provider_name, compiler_id, compiler_version))
    if grammar is None:
        raise ValueError("preserved source has no exact Provider compiler identity")
    if (bound.provider_name != provider_name
            or bound.compiler_contract.compiler_id != compiler_id
            or bound.compiler_contract.compiler_version != compiler_version):
        raise ValueError("preserved source Provider/compiler identity changed")
    bound, requirement, expression, prompt = _source_projection(
        bound, requirement, provider_name=provider_name
    )
    endpoint_controls = _require_endpoint_groundings(
        requirement, expression, continuity_expression, bound
    )
    return _source_native_prompt(
        bound, requirement, prompt, endpoint_controls, grammar_contract=grammar
    )


def compile_preserved_seedance_source(bound, requirement, continuity_expression=None):
    """Build the legacy pure source prompt; /3 remains enforced by request compilation."""
    bound, requirement, expression, prompt = _source_projection(
        bound, requirement, provider_name="seedance"
    )
    endpoint_controls = _require_endpoint_groundings(
        requirement, expression, continuity_expression, bound
    )
    return _source_native_prompt(
        bound, requirement, prompt, endpoint_controls,
        grammar_contract="seedance-preserved-source-v1",
    )


def validate_preserved_seedance_request(bound, requirement, request):
    """Compatibility wrapper for existing Seedance execution callers."""
    if bound.provider_name != "seedance":
        raise ValueError("Seedance source validator received another Provider")
    return validate_preserved_source_request(bound, requirement, request)


def _source_native_prompt(
    bound, requirement, prompt, endpoint_controls,
    *, grammar_contract="seedance-preserved-source-v1",
):
    from ai_video.production.video_compiler import ProviderNativePrompt
    from ai_video.production.seedance_source_dialogue import source_dialogue_controls

    intent = requirement.generation_intent
    controls = (
        "generation_intent.subject_action.progression",
        "generation_intent.pacing.shot_duration_seconds",
        *endpoint_controls,
    )
    ambience = intent.ambience_intent
    if ambience is not None and not ambience.explicitly_silent:
        if not bound.output_requirement.native_audio:
            raise ValueError("source sound intent requires native audio output")
        controls += ("generation_intent.ambience_intent.explicitly_silent",)
    dialogue = intent.dialogue_intent
    if dialogue is not None and dialogue.mode == "none":
        controls += ("generation_intent.dialogue_intent.lip_sync_required",)
    controls += source_dialogue_controls(dialogue, prompt, bound.output_requirement)

    return ProviderNativePrompt(
        grammar_contract=grammar_contract,
        prompt_text=prompt,
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        expressed_control_paths=controls,
    )
