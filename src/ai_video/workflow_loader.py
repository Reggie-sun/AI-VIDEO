from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_video.errors import AiVideoError, ErrorCode


VIRTUAL_NODE_TYPES = {"Anything Everywhere", "GetNode", "SetNode"}
SKIPPED_NODE_TYPES = {"PlaySound|pysssss"}

ARRAY_WIDGET_NAME_MAP: dict[str, list[str | None]] = {
    "LoadImage": ["image", None],
    "Textbox": ["text"],
    "mxSlider": ["Xi", "Xf", "isfloatX"],
    "PrimitiveInt": ["value"],
    "WanVideoTextEncode": [
        "positive_prompt",
        "negative_prompt",
        "force_offload",
        "use_disk_cache",
        "device",
    ],
    "WanVideoDecode": [
        "enable_vae_tiling",
        "tile_x",
        "tile_y",
        "tile_stride_x",
        "tile_stride_y",
        "normalization",
    ],
    "CRT_QuantizeAndCropImage": ["max_side_length"],
    "WanVideoImageToVideoEncode": [
        "width",
        "height",
        "num_frames",
        "noise_aug_strength",
        "start_latent_strength",
        "end_latent_strength",
        "force_offload",
        "fun_or_fl2v_model",
        "tiled_vae",
        "augment_empty_frames",
    ],
    "WanVideoBlockSwap": [
        "blocks_to_swap",
        "offload_img_emb",
        "offload_txt_emb",
        "use_non_blocking",
        "vace_blocks_to_swap",
        "prefetch_blocks",
        "block_swap_debug",
    ],
    "WanVideoTorchCompileSettings": [
        "backend",
        "fullgraph",
        "mode",
        "dynamic",
        "dynamo_cache_size_limit",
        "compile_transformer_blocks_only",
        "dynamo_recompile_limit",
        "force_parameter_static_shapes",
        "allow_unmerged_lora_compile",
    ],
    "WanVideoLoraSelectMulti": [
        "lora_0",
        "strength_0",
        "lora_1",
        "strength_1",
        "lora_2",
        "strength_2",
        "lora_3",
        "strength_3",
        "lora_4",
        "strength_4",
        "low_mem_load",
        "merge_loras",
    ],
}

SUBGRAPH_WIDGET_NAME_MAP: dict[str, list[str]] = {
    "2dce7e0e-33e8-4256-aa71-145b48c2f9d6": [
        "model",
        "model_1",
        "model_name",
        "model_name_1",
        "quantization",
        "attention_mode",
    ],
    "7546269c-e8cb-4705-9545-0b6b7caf99c6": ["seed", "steps", "scheduler"],
}


def _fail(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.WORKFLOW_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def load_workflow_template(path: str | Path) -> dict[str, Any]:
    template_path = Path(path)
    try:
        raw = json.loads(template_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise _fail(f"Could not read workflow template: {template_path}", str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise _fail(f"Workflow template is not valid JSON: {template_path}", str(exc)) from exc

    if _looks_like_api_workflow(raw):
        return raw
    if _looks_like_ui_workflow(raw):
        return UiWorkflowConverter(raw).convert()
    raise _fail("Workflow JSON is neither ComfyUI API-format nor UI workflow JSON.")


def _looks_like_api_workflow(value: Any) -> bool:
    return isinstance(value, dict) and "nodes" not in value


def _looks_like_ui_workflow(value: Any) -> bool:
    return isinstance(value, dict) and isinstance(value.get("nodes"), list)


class UiWorkflowConverter:
    def __init__(self, workflow: dict[str, Any]):
        self.workflow = workflow
        self.nodes: list[dict[str, Any]] = workflow.get("nodes", [])
        self.node_by_id = {int(node["id"]): node for node in self.nodes}
        self.link_by_id = {int(link[0]): link for link in workflow.get("links", [])}
        self.ue_link_by_target = {
            (int(link["downstream"]), int(link["downstream_slot"])): (
                str(link["upstream"]),
                int(link["upstream_slot"]),
            )
            for link in workflow.get("extra", {}).get("ue_links", [])
        }
        self.set_source_by_name = self._build_set_source_map()

    def convert(self) -> dict[str, Any]:
        prompt: dict[str, Any] = {}
        for node in self.nodes:
            node_type = str(node["type"])
            if node_type in VIRTUAL_NODE_TYPES or node_type in SKIPPED_NODE_TYPES:
                continue

            prompt[str(node["id"])] = {
                "class_type": node_type,
                "inputs": self._build_inputs(node),
                "_meta": {"title": node.get("title") or node_type},
            }
        return prompt

    def _build_set_source_map(self) -> dict[str, tuple[str, int]]:
        source_map: dict[str, tuple[str, int]] = {}
        for node in self.nodes:
            if node.get("type") != "SetNode":
                continue
            name = self._virtual_node_name(node)
            inputs = node.get("inputs") or []
            if not name or not inputs or inputs[0].get("link") is None:
                continue
            source_map[name] = self._resolve_link_id(int(inputs[0]["link"]))
        return source_map

    def _build_inputs(self, node: dict[str, Any]) -> dict[str, Any]:
        inputs: dict[str, Any] = {}
        widget_values = self._widget_values(node)
        consumed_widget_names: set[str] = set()

        for slot_index, input_def in enumerate(node.get("inputs") or []):
            input_name = str(input_def["name"])
            resolved_link = self._resolve_input_link(node, slot_index, input_def)
            if resolved_link is not None:
                inputs[input_name] = resolved_link
                continue
            widget_name = input_def.get("widget", {}).get("name")
            if widget_name and widget_name in widget_values:
                inputs[widget_name] = widget_values[widget_name]
                consumed_widget_names.add(widget_name)

        for widget_name, value in widget_values.items():
            if widget_name not in consumed_widget_names and widget_name not in inputs:
                inputs[widget_name] = value

        return inputs

    def _resolve_input_link(
        self, node: dict[str, Any], slot_index: int, input_def: dict[str, Any]
    ) -> list[Any] | None:
        link_id = input_def.get("link")
        if link_id is not None:
            upstream_id, upstream_slot = self._resolve_link_id(int(link_id))
            return [upstream_id, upstream_slot]

        ue_link = self.ue_link_by_target.get((int(node["id"]), slot_index))
        if ue_link is not None:
            upstream_id, upstream_slot = self._resolve_upstream_ref(ue_link[0], ue_link[1])
            return [upstream_id, upstream_slot]
        return None

    def _resolve_link_id(self, link_id: int) -> tuple[str, int]:
        try:
            _, origin_id, origin_slot, _, _, _ = self.link_by_id[link_id]
        except KeyError as exc:
            raise _fail("Workflow link reference is missing.", str(link_id)) from exc
        return self._resolve_upstream_ref(str(origin_id), int(origin_slot))

    def _resolve_upstream_ref(self, node_id: str, origin_slot: int) -> tuple[str, int]:
        base_id = int(str(node_id).split(":")[0])
        try:
            upstream_node = self.node_by_id[base_id]
        except KeyError as exc:
            raise _fail("Workflow references an unknown upstream node.", str(node_id)) from exc

        node_type = str(upstream_node["type"])
        if node_type == "GetNode":
            name = self._virtual_node_name(upstream_node)
            source = self.set_source_by_name.get(name)
            if source is None:
                raise _fail("GetNode could not be resolved to a matching SetNode.", name)
            return source
        if node_type in VIRTUAL_NODE_TYPES:
            raise _fail(
                "Workflow contains an unsupported virtual upstream node.",
                f"{node_type} ({node_id})",
            )
        return str(node_id), origin_slot

    def _widget_values(self, node: dict[str, Any]) -> dict[str, Any]:
        values = node.get("widgets_values")
        if values is None:
            return {}
        if isinstance(values, dict):
            clean = dict(values)
            clean.pop("videopreview", None)
            return clean
        if not isinstance(values, list):
            return {}

        widget_names = self._widget_names(node)
        if len(values) > len(widget_names):
            if str(node["type"]) == "PrimitiveInt":
                values = values[:1]
            else:
                raise _fail(
                    "Workflow node has more widget values than supported widget names.",
                    f'{node["type"]} ({node["id"]})',
                )

        resolved: dict[str, Any] = {}
        for index, name in enumerate(widget_names):
            if name is None or index >= len(values):
                continue
            resolved[name] = values[index]
        return resolved

    def _widget_names(self, node: dict[str, Any]) -> list[str | None]:
        node_type = str(node["type"])
        if node_type in ARRAY_WIDGET_NAME_MAP:
            return ARRAY_WIDGET_NAME_MAP[node_type]
        if node_type in SUBGRAPH_WIDGET_NAME_MAP:
            return SUBGRAPH_WIDGET_NAME_MAP[node_type]

        input_widget_names = [
            input_def.get("widget", {}).get("name")
            for input_def in node.get("inputs") or []
            if input_def.get("widget")
        ]
        if input_widget_names:
            return input_widget_names
        raise _fail(
            "Workflow contains a node type whose widget mapping is not supported yet.",
            f'{node_type} ({node["id"]})',
        )

    def _virtual_node_name(self, node: dict[str, Any]) -> str:
        widgets = node.get("widgets_values")
        if isinstance(widgets, list) and widgets:
            return str(widgets[0])
        return str(node.get("title") or node["id"])
