from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


JsonPath = list[str | int]


class ComfyConfig(BaseModel):
    base_url: str = "http://127.0.0.1:8188"
    allow_non_local: bool = False


class WorkflowConfig(BaseModel):
    template: Path
    binding: Path


class OutputConfig(BaseModel):
    root: Path = Path("runs")
    min_free_gb: float = 1.0


class DefaultsConfig(BaseModel):
    width: int = 512
    height: int = 512
    fps: int = 16
    clip_seconds: int = 2
    seed: int = 1
    seed_policy: str = "derived"
    negative_prompt: str = ""
    style_prompt: str = ""
    max_attempts: int = 2
    poll_interval_seconds: float = 2.0
    job_timeout_seconds: float = 1800.0


class IPAdapterConfig(BaseModel):
    weight: float = 1.0
    start_at: float | None = None
    end_at: float | None = None


class FutureLoraConfig(BaseModel):
    path: Path | None = None
    weight: float | None = None


class CharacterProfile(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    name: str
    description: str = ""
    reference_images: list[Path] = Field(default_factory=list)
    ipadapter: IPAdapterConfig = Field(default_factory=IPAdapterConfig)
    future_lora: FutureLoraConfig = Field(default_factory=FutureLoraConfig)


class ProjectConfig(BaseModel):
    project_name: str
    comfy: ComfyConfig = Field(default_factory=ComfyConfig)
    workflow: WorkflowConfig
    output: OutputConfig = Field(default_factory=OutputConfig)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    characters: list[CharacterProfile] = Field(default_factory=list)


class ShotSpec(BaseModel):
    id: str
    prompt: str
    negative_prompt: str = ""
    characters: list[str] = Field(default_factory=list)
    seed: int | None = None
    clip_seconds: int | None = None
    fps: int | None = None
    width: int | None = None
    height: int | None = None
    init_image: Path | None = None
    continuity_note: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ShotList(BaseModel):
    shots: list[ShotSpec]


class JsonPathBinding(BaseModel):
    path: JsonPath | None = None
    paths: list[JsonPath] = Field(default_factory=list)

    @model_validator(mode="after")
    def _require_at_least_one_path(self) -> "JsonPathBinding":
        if self.path is None and not self.paths:
            raise ValueError("JsonPathBinding requires path or paths")
        return self

    def all_paths(self) -> list[JsonPath]:
        resolved: list[JsonPath] = []
        if self.path is not None:
            resolved.append(self.path)
        resolved.extend(self.paths)
        return resolved


class CharacterRefBinding(BaseModel):
    character: str
    image_path: JsonPath
    weight_path: JsonPath | None = None


class ClipOutputBinding(BaseModel):
    node: str
    kind: str
    extensions: list[str] = Field(default_factory=lambda: [".mp4"])
    select: Literal["first", "last"] = "first"


class WorkflowBinding(BaseModel):
    positive_prompt: JsonPathBinding
    negative_prompt: JsonPathBinding | None = None
    seed: JsonPathBinding
    init_image: JsonPathBinding | None = None
    resolution: JsonPathBinding | None = None
    frame_count: JsonPathBinding | None = None
    frame_rate: JsonPathBinding | None = None
    output_prefix: JsonPathBinding | None = None
    character_refs: list[CharacterRefBinding] = Field(default_factory=list)
    clip_output: ClipOutputBinding


class ClipArtifact(BaseModel):
    filename: str
    subfolder: str = ""
    type: str = "output"
    extension: str
    source_node: str
