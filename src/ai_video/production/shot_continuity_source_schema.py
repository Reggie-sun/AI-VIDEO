"""Exact live-node schema sealing for the Shot Continuity source workflow."""

from __future__ import annotations

import json
from typing import Any

from pydantic import Field

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StrictModel


_SHA256 = r"^[0-9a-f]{64}$"
SOURCE_REQUIRED_NODES = (
    "UNETLoader",
    "CLIPLoader",
    "VAELoader",
    "MiniMaxH3ImageToVideo",
    "RandomNoise",
    "BasicGuider",
    "KSamplerSelect",
    "BasicScheduler",
    "SamplerCustomAdvanced",
    "VAEDecode",
    "VAEDecodeAudio",
    "CreateVideo",
    "SaveVideo",
    "LoadImage",
)
SOURCE_RUNTIME_FILE_CHOOSERS = {
    "UNETLoader": ("unet_name",),
    "CLIPLoader": ("clip_name",),
    "VAELoader": ("vae_name",),
    "LoadImage": ("image",),
}


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class SourceQualificationNodeSchemaSeal(StrictModel):
    node_name: str = Field(min_length=1)
    schema_sha256: str = Field(pattern=_SHA256)


def source_node_schema_seals(
    object_info: dict[str, Any],
) -> tuple[SourceQualificationNodeSchemaSeal, ...]:
    """Seal workflow node schemas while excluding mutable file inventories."""

    result = []
    for node_name in SOURCE_REQUIRED_NODES:
        node = object_info.get(node_name)
        if not isinstance(node, dict):
            raise _invalid("Source ComfyUI node schema is incomplete.", node_name)
        input_schema = json.loads(json.dumps(node.get("input")))
        if not isinstance(input_schema, dict):
            raise _invalid("Source ComfyUI node schema is malformed.", node_name)
        for section in ("required", "optional"):
            fields = input_schema.get(section)
            if not isinstance(fields, dict):
                continue
            for field in SOURCE_RUNTIME_FILE_CHOOSERS.get(node_name, ()):
                field_spec = fields.get(field)
                if (
                    isinstance(field_spec, list)
                    and field_spec
                    and isinstance(field_spec[0], list)
                ):
                    field_spec[0] = ["<runtime-file-inventory>"]
        projection = {
            "input": input_schema,
            "input_order": node.get("input_order"),
            "output_name": node.get("output_name"),
        }
        if not all(projection.values()):
            raise _invalid("Source ComfyUI node schema is malformed.", node_name)
        result.append(
            SourceQualificationNodeSchemaSeal(
                node_name=node_name,
                schema_sha256=canonical_sha256(projection),
            )
        )
    return tuple(result)


__all__ = [
    "SOURCE_REQUIRED_NODES",
    "SOURCE_RUNTIME_FILE_CHOOSERS",
    "SourceQualificationNodeSchemaSeal",
    "source_node_schema_seals",
]
