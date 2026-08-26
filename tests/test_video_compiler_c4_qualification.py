from __future__ import annotations

import pytest

from ai_video.production.video_compiler import (
    VideoGenerationRequestCompilation,
    compile_video_generation_request,
)


def _projection_values():
    from test_production_video import _c4_binding, _c4_request

    binding = _c4_binding(tier="motion_boundary")
    request = _c4_request(
        binding=binding,
        seal_terminal_frame=True,
        execution_stack_hash="e" * 64,
        seed=7,
        negative_prompt_text="",
    )
    return {
        "generation_id": request.generation_id,
        "provider_name": request.provider_name,
        "provider_kind": request.provider_kind,
        "model_id": request.model_id,
        "provider_profile": request.provider_profile,
        "requirement_hash": "a" * 64,
        "provider_bound_request_hash": "b" * 64,
        "adapter_compiler_id": "m0-c4-qualification",
        "adapter_compiler_version": "1",
        "adapter_compiler_hash": "c" * 64,
        "execution_stack_hash": "e" * 64,
        "target_shot_id": request.target_shot_id,
        "target_shot_revision": request.target_shot_revision,
        "target_shot_content_hash": request.target_shot_content_hash,
        "target_asset_role": request.target_asset_role,
        "mode": request.mode,
        "prompt_text": request.prompt_text,
        "negative_prompt_text": "",
        "image_bindings": request.image_bindings,
        "c4_multi_anchor_binding": request.c4_multi_anchor_binding,
        "seal_terminal_frame": True,
        "media_bindings": request.media_bindings,
        "output_requirement": request.output_requirement,
        "seed": 7,
        "base_project": request.base_project,
        "base_registry": request.base_registry,
        "base_dependency_graph": request.base_dependency_graph,
        "input_artifact_ids": request.input_artifact_ids,
        "output_asset_id": request.output_asset_id,
    }


def test_c4_qualification_compilation_is_a_distinct_exact_shape() -> None:
    projection = VideoGenerationRequestCompilation.create(
        compilation_kind="c4_qualification",
        **_projection_values(),
    )

    request = compile_video_generation_request(projection)

    assert request.c4_multi_anchor_binding is not None
    assert tuple(item.role for item in request.image_bindings) == (
        "first_frame",
        "last_frame",
        "reference",
    )
    assert tuple(item.role for item in request.media_bindings) == (
        "reference_video",
    )


def test_source_qualification_kind_cannot_be_reused_for_c4() -> None:
    with pytest.raises(ValueError, match="FL2VA"):
        VideoGenerationRequestCompilation.create(
            compilation_kind="qualification",
            **_projection_values(),
        )


def test_c4_qualification_rejects_missing_motion_tail() -> None:
    values = _projection_values()
    values["media_bindings"] = ()

    with pytest.raises(ValueError, match="four-anchor"):
        VideoGenerationRequestCompilation.create(
            compilation_kind="c4_qualification",
            **values,
        )
