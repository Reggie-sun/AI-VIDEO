from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.models import (
    CharacterProfile,
    ClipArtifact,
    ClipOutputBinding,
    DefaultsConfig,
    ShotSpec,
    WorkflowBinding,
)


@dataclass
class RenderedWorkflow:
    workflow: dict[str, Any]
    positive_prompt: str
    negative_prompt: str
    seed: int


def _fail(code: ErrorCode, message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, technical_detail=detail, retryable=False)


def validate_api_workflow(workflow: Mapping[str, Any]) -> None:
    if "nodes" in workflow and isinstance(workflow["nodes"], list):
        raise _fail(
            ErrorCode.WORKFLOW_INVALID,
            "Workflow must be ComfyUI API-format JSON, not UI workflow JSON.",
        )
    if not workflow:
        raise _fail(ErrorCode.WORKFLOW_INVALID, "Workflow JSON is empty.")
    for node_id, node in workflow.items():
        if not isinstance(node_id, str) or not isinstance(node, Mapping):
            raise _fail(ErrorCode.WORKFLOW_INVALID, "Workflow nodes must be keyed objects.")
        if "class_type" not in node or "inputs" not in node:
            raise _fail(
                ErrorCode.WORKFLOW_INVALID,
                f"Workflow node {node_id} is missing class_type or inputs.",
            )


def _get_path(root: Any, path: list[str | int], field_name: str) -> Any:
    current = root
    for part in path:
        if isinstance(current, list) and isinstance(part, int):
            try:
                current = current[part]
            except IndexError as exc:
                raise _fail(
                    ErrorCode.BINDING_INVALID,
                    f"Binding path for {field_name} has missing index {part}.",
                    str(path),
                ) from exc
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise _fail(
                ErrorCode.BINDING_INVALID,
                f"Binding path for {field_name} is invalid at {part!r}.",
                str(path),
            )
    return current


def _set_path(root: Any, path: list[str | int], value: Any, field_name: str) -> None:
    if not path:
        raise _fail(ErrorCode.BINDING_INVALID, f"Binding path for {field_name} is empty.")
    parent = _get_path(root, path[:-1], field_name) if len(path) > 1 else root
    key = path[-1]
    if isinstance(parent, list) and isinstance(key, int):
        if key >= len(parent):
            raise _fail(ErrorCode.BINDING_INVALID, f"Binding path for {field_name} has missing index {key}.")
        parent[key] = value
    elif isinstance(parent, dict) and key in parent:
        parent[key] = value
    else:
        raise _fail(
            ErrorCode.BINDING_INVALID,
            f"Binding path for {field_name} is invalid at {key!r}.",
            str(path),
        )


def _binding_paths(binding: JsonPathBinding, field_name: str) -> list[list[str | int]]:
    paths = binding.all_paths()
    if not paths:
        raise _fail(ErrorCode.BINDING_INVALID, f"Binding path for {field_name} is empty.")
    return paths


def _set_binding_value(root: Any, binding: JsonPathBinding, value: Any, field_name: str) -> None:
    for path in _binding_paths(binding, field_name):
        _set_path(root, path, value, field_name)


def _default_init_image_values(template: dict[str, Any], binding: WorkflowBinding) -> list[str]:
    if binding.init_image is None:
        return []
    values: list[str] = []
    for path in _binding_paths(binding.init_image, "init_image"):
        value = _get_path(template, path, "init_image")
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    return values


def derive_seed(default_seed: int, shot_seed: int | None, shot_index: int) -> int:
    return shot_seed if shot_seed is not None else default_seed + shot_index


def _join_prompt(parts: list[str]) -> str:
    return ", ".join(part.strip() for part in parts if part and part.strip())


def compose_prompt(
    defaults: DefaultsConfig,
    shot: ShotSpec,
    characters: Mapping[str, CharacterProfile],
) -> tuple[str, str]:
    character_parts = [
        characters[character_id].description
        for character_id in shot.characters
        if character_id in characters and characters[character_id].description
    ]
    positive = _join_prompt(
        [defaults.style_prompt, *character_parts, shot.prompt, shot.continuity_note]
    )
    negative = _join_prompt([defaults.negative_prompt, shot.negative_prompt])
    return positive, negative


def _validate_binding_paths(template: dict[str, Any], binding: WorkflowBinding) -> None:
    for path in _binding_paths(binding.positive_prompt, "positive_prompt"):
        _get_path(template, path, "positive_prompt")
    if binding.negative_prompt is not None:
        for path in _binding_paths(binding.negative_prompt, "negative_prompt"):
            _get_path(template, path, "negative_prompt")
    for path in _binding_paths(binding.seed, "seed"):
        _get_path(template, path, "seed")
    if binding.init_image is not None:
        for path in _binding_paths(binding.init_image, "init_image"):
            _get_path(template, path, "init_image")
    if binding.resolution is not None:
        for path in _binding_paths(binding.resolution, "resolution"):
            _get_path(template, path, "resolution")
    if binding.frame_count is not None:
        for path in _binding_paths(binding.frame_count, "frame_count"):
            _get_path(template, path, "frame_count")
    if binding.frame_rate is not None:
        for path in _binding_paths(binding.frame_rate, "frame_rate"):
            _get_path(template, path, "frame_rate")
    if binding.output_prefix is not None:
        for path in _binding_paths(binding.output_prefix, "output_prefix"):
            _get_path(template, path, "output_prefix")
    for ref in binding.character_refs:
        _get_path(template, ref.image_path, f"character_refs.{ref.character}.image")
        if ref.weight_path is not None:
            _get_path(template, ref.weight_path, f"character_refs.{ref.character}.weight")


def render_workflow(
    *,
    template: dict[str, Any],
    binding: WorkflowBinding,
    shot: ShotSpec,
    defaults: DefaultsConfig,
    characters: Mapping[str, CharacterProfile],
    shot_index: int,
    chain_image_name: str | None,
    character_image_names: Mapping[str, str],
    output_prefix: str,
) -> RenderedWorkflow:
    validate_api_workflow(template)
    _validate_binding_paths(template, binding)
    workflow = deepcopy(template)
    positive, negative = compose_prompt(defaults, shot, characters)
    seed = derive_seed(defaults.seed, shot.seed, shot_index)
    width = shot.width or defaults.width
    height = shot.height or defaults.height
    fps = shot.fps or defaults.fps
    clip_seconds = shot.clip_seconds or defaults.clip_seconds
    resolution = max(width, height)
    frame_count = max(1, fps * clip_seconds + 1)

    if binding.init_image is not None and chain_image_name is None:
        default_values = _default_init_image_values(template, binding)
        if default_values:
            raise _fail(
                ErrorCode.CONFIG_INVALID,
                f"Shot {shot.id} requires init_image or an upstream chain frame.",
                f"Template init_image would fall back to: {', '.join(default_values)}",
            )

    _set_binding_value(workflow, binding.positive_prompt, positive, "positive_prompt")
    if binding.negative_prompt is not None:
        _set_binding_value(workflow, binding.negative_prompt, negative, "negative_prompt")
    _set_binding_value(workflow, binding.seed, seed, "seed")
    if binding.init_image is not None and chain_image_name is not None:
        _set_binding_value(workflow, binding.init_image, chain_image_name, "init_image")
    if binding.resolution is not None:
        _set_binding_value(workflow, binding.resolution, resolution, "resolution")
    if binding.frame_count is not None:
        _set_binding_value(workflow, binding.frame_count, frame_count, "frame_count")
    if binding.frame_rate is not None:
        _set_binding_value(workflow, binding.frame_rate, fps, "frame_rate")
    if binding.output_prefix is not None:
        _set_binding_value(workflow, binding.output_prefix, output_prefix, "output_prefix")

    for ref in binding.character_refs:
        image_name = character_image_names.get(ref.character)
        if image_name is not None:
            _set_path(workflow, ref.image_path, image_name, f"character_refs.{ref.character}.image")
        if ref.weight_path is not None and ref.character in characters:
            _set_path(
                workflow,
                ref.weight_path,
                characters[ref.character].ipadapter.weight,
                f"character_refs.{ref.character}.weight",
            )

    return RenderedWorkflow(
        workflow=workflow,
        positive_prompt=positive,
        negative_prompt=negative,
        seed=seed,
    )


def collect_clip_artifact(history: dict[str, Any], clip_output: ClipOutputBinding) -> ClipArtifact:
    outputs = history.get("outputs", {})
    node_output = outputs.get(clip_output.node)
    if not isinstance(node_output, dict) or clip_output.kind not in node_output:
        raise _fail(
            ErrorCode.COMFY_OUTPUT_MISSING,
            f"ComfyUI history is missing output {clip_output.node}.{clip_output.kind}.",
        )

    candidates = []
    for item in node_output[clip_output.kind]:
        filename = item.get("filename", "")
        extension = Path(filename).suffix.lower()
        if extension in clip_output.extensions:
            candidates.append(
                ClipArtifact(
                    filename=filename,
                    subfolder=item.get("subfolder", ""),
                    type=item.get("type", "output"),
                    extension=extension,
                    source_node=clip_output.node,
                )
            )
    if not candidates:
        raise _fail(
            ErrorCode.COMFY_OUTPUT_MISSING,
            f"No video artifact matched extensions: {', '.join(clip_output.extensions)}",
        )
    return candidates[0] if clip_output.select == "first" else candidates[-1]
