"""The single typed prose-and-material compiler for Jimeng native modes."""

from __future__ import annotations

import hashlib
from typing import Any

from ai_video.production.jimeng_models import (
    JIMENG_INPUT_MODE_SPECS,
    JIMENG_MODEL_SPECS,
    jimeng_capability_id,
    jimeng_profile_compiler_id,
    jimeng_profile_version,
)
from ai_video.production.video import VideoGenerationMode

# ECMAScript WhiteSpace + LineTerminator, used by the native client's trim().
# Explicit characters avoid Python strip() also removing U+0085/U+001C..1F.
_NATIVE_TRIM_CHARACTERS = (
    "\t\v\f \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006"
    "\u2007\u2008\u2009\u200a\u202f\u205f\u3000\ufeff\n\r\u2028\u2029"
)


def normalize_jimeng_prompt_text(text: str) -> str:
    """Match the native client's ECMAScript trim without changing internal text."""
    return text.strip(_NATIVE_TRIM_CHARACTERS)


def _unsupported(provider_bound: Any, reason: str) -> Any:
    from ai_video.production.video_compiler import (
        ProviderRequirementUnsupported,
        ProviderRequirementUnsupportedReason,
    )

    return ProviderRequirementUnsupported(
        requirement_hash=provider_bound.requirement_hash,
        provider_bound_request_hash=provider_bound.provider_bound_request_hash,
        selected_capability_id=provider_bound.capability_id,
        reason=ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED,
        unsupported_field_paths=(reason,),
    )


def _authored_reference_text(provider_bound, requirement, rows, base_prompt, expressed_control_paths):
    """Project sealed raw fragments and explicit duties, never infer a use."""
    from ai_video.production._video_requirement_routing import native_binding_role
    from ai_video.production.video_requirement import SemanticReferenceRole

    recipe = provider_bound.generation_recipe
    if recipe is None:
        return ""
    from ai_video.production._causal_state_expression import native_recipe_expression_view

    recipe = native_recipe_expression_view(recipe, requirement, expressed_control_paths)
    pairs = tuple(zip(provider_bound.binding_roles, provider_bound.input_assets, strict=True))
    evidence = {(asset.role.value, asset.asset_id, asset.asset_sha256): asset
                for asset in requirement.asset_evidence}
    fragments = []
    for expression in recipe.expressions:
        if expression.stage != "raw_generation" or expression.level == "diagnostic":
            continue
        for fragment in expression.native_text:
            if fragment not in base_prompt and fragment not in fragments:
                fragments.append(fragment)
        control = expression.input_control
        for duty in (() if control is None else control.references):
            semantic = evidence.get((duty.role, duty.asset_id, duty.asset_sha256))
            role = native_binding_role(SemanticReferenceRole(duty.role))
            matching = [asset for binding_role, asset in pairs
                        if binding_role == role and asset.asset_id == duty.asset_id
                        and asset.asset_sha256 == duty.asset_sha256]
            if (semantic is None or len(matching) != 1
                    or duty.canonical_owner_id is not None
                    and duty.canonical_owner_id != semantic.canonical_owner_id):
                raise ValueError("authored reference duty differs from its selected material")
            if duty.scope_text is None:
                continue
            number = next((index + 1 for index, row in enumerate(rows)
                           if row == (role, duty.asset_id)), None)
            label = f"参考素材{number}" if number is not None else role
            owner = f"，主体 {duty.canonical_owner_id}" if duty.canonical_owner_id else ""
            text = f"{label}职责（{duty.purpose}{owner}）：{duty.scope_text}"
            if text not in fragments:
                fragments.append(text)
    return "".join(f"\n{fragment}" for fragment in fragments)


def compile_jimeng_native_prompt(
    *,
    compiler_id: str,
    compiler_version: str,
    requirement: Any,
    provider_bound: Any,
    continuity_expression: Any = None,
) -> Any:
    """Compile the selected exact model/mode into hash-bound native prose.

    The sealed compiler ID chooses the Jimeng input mode. Text prose is built
    by the shared remote grammar or explicitly QA-mapped final Shot text.
    Canonical native markers are added only for mode 4. Length is checked once on the final JavaScript UTF-16
    string, including the explicit material markers.
    """

    from ai_video.production._remote_video_native_prompt import (
        RemoteVideoPromptCompilation,
        compile_remote_video_prompt,
    )
    from ai_video.production.video_compiler import (
        ProviderNativePrompt,
        ProviderRequirementUnsupported,
        ProviderRequirementUnsupportedReason,
    )

    exact_modes = tuple(
        (model_id, input_mode)
        for model_id in JIMENG_MODEL_SPECS
        for input_mode in JIMENG_INPUT_MODE_SPECS
        if jimeng_profile_compiler_id(model_id, input_mode) == compiler_id
    )
    if compiler_version not in {"1", "2"} or len(exact_modes) != 1:
        return _unsupported(provider_bound, "adapter_compiler_id")
    model_id, input_mode = exact_modes[0]
    mode = JIMENG_INPUT_MODE_SPECS[input_mode]

    # The label alone is insufficient. Rebind the selected compiler to the
    # exact provider, model, capability, profile version, and request mode.
    if (
        provider_bound.provider_name != "jimeng"
        or provider_bound.provider_kind != "jimeng"
        or provider_bound.model_id != model_id
        or provider_bound.provider_profile.profile_id != "jimeng"
        or provider_bound.provider_profile.profile_version
        != jimeng_profile_version(model_id, input_mode)
        or provider_bound.capability_id != jimeng_capability_id(model_id, input_mode)
        or provider_bound.mode is not VideoGenerationMode(mode.generation_mode)
        or provider_bound.compiler_contract.compiler_id != compiler_id
        or provider_bound.compiler_contract.compiler_version != compiler_version
    ):
        return _unsupported(provider_bound, "selected_jimeng_mode_identity")

    from ai_video.production.jimeng_authored_prompt import has_authored_text, compile_authored_text

    authored_final = has_authored_text(provider_bound)
    if authored_final:
        native = compile_authored_text(provider_bound, requirement,
            continuity_expression=continuity_expression)
        if isinstance(native, ProviderRequirementUnsupported):
            return native
        prose = RemoteVideoPromptCompilation(prompt_text=native.prompt_text,
            prompt_sha256=native.prompt_sha256,
            expressed_control_paths=native.expressed_control_paths)
    else:
        prose = compile_remote_video_prompt(
            requirement,
            provider_bound=provider_bound,
            continuity_expression=continuity_expression,
            max_prompt_characters=None,
        )
    if not isinstance(prose, RemoteVideoPromptCompilation):
        return ProviderRequirementUnsupported(
            requirement_hash=provider_bound.requirement_hash,
            provider_bound_request_hash=provider_bound.provider_bound_request_hash,
            selected_capability_id=provider_bound.capability_id,
            reason=ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED,
            unsupported_field_paths=prose.unsupported_field_paths,
        )

    if input_mode == "text_to_video":
        if (provider_bound.binding_roles or provider_bound.input_assets
                or "{{" in prose.prompt_text or "}}" in prose.prompt_text):
            return _unsupported(provider_bound, "input_assets")
        rows: list[tuple[str, str]] = []
    elif input_mode in {"first_frame", "first_last_frame"}:
        if tuple(provider_bound.binding_roles) != mode.image_roles:
            return _unsupported(provider_bound, "binding_roles")
        rows = []
    else:
        pairs = tuple(zip(provider_bound.binding_roles, provider_bound.input_assets, strict=True))
        if any(role not in {"reference", "reference_audio", "reference_video"}
               for role, _ in pairs):
            return _unsupported(provider_bound, "binding_roles")
        if not pairs:
            return _unsupported(provider_bound, "input_assets")
        role_order = {"reference": 0, "reference_audio": 1, "reference_video": 2}
        rows = [(role, asset.asset_id) for role, asset in sorted(
            pairs, key=lambda pair: (role_order[pair[0]], pair[1].asset_id))]

    marker_kind = {
        "reference": "image",
        "reference_audio": "audio",
        "reference_video": "video",
    }
    markers = "".join(
        f"\n参考素材{index + 1} {{{{{marker_kind[role]}:{index}}}}}"
        for index, (role, _) in enumerate(rows)
        if not authored_final or f"{{{{{marker_kind[role]}:{index}}}}}" not in prose.prompt_text
    )
    try:
        authored = "" if authored_final else _authored_reference_text(
            provider_bound, requirement, rows, prose.prompt_text, prose.expressed_control_paths)
    except ValueError:
        return _unsupported(provider_bound, "generation_recipe.reference_duties")
    prompt = prose.prompt_text + markers + authored
    if compiler_version == "2":
        # Seal the actual native bytes before request/preview/permit creation.
        # Version 1 remains byte-for-byte compatible with historical receipts.
        prompt = normalize_jimeng_prompt_text(prompt)
        if not prompt:
            return _unsupported(provider_bound, "native_prompt.prompt_text")
    spec = JIMENG_MODEL_SPECS[model_id]
    if len(prompt.encode("utf-16-le", errors="surrogatepass")) // 2 > spec.prompt_max_characters:
        return ProviderRequirementUnsupported(
            requirement_hash=provider_bound.requirement_hash,
            provider_bound_request_hash=provider_bound.provider_bound_request_hash,
            selected_capability_id=provider_bound.capability_id,
            reason=ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED,
            unsupported_field_paths=("native_prompt.prompt_text.length",),
        )

    grammar = {
        "text_to_video": "jimeng-text-to-video-v1",
        "first_frame": "jimeng-frame-conditioned-v1",
        "first_last_frame": "jimeng-frame-conditioned-v1",
        "multimodal": "jimeng-explicit-reference-v1",
    }[input_mode]
    if authored_final:
        grammar = grammar.replace("-v1", "-authored-v2")
    return ProviderNativePrompt(
        grammar_contract=grammar,
        prompt_text=prompt,
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        expressed_control_paths=prose.expressed_control_paths,
    )
