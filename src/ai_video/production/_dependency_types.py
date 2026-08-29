"""Dependency graph type identities shared by immutable models and builders."""

from enum import Enum


class DependencyNodeKind(str, Enum):
    CREATIVE_ARTIFACT = "creative_artifact"
    GENERATION_TARGET = "generation_target"
    ASSET = "asset"
    COMPOSITION_SPEC = "composition_spec"
    RESOLVED_TIMELINE = "resolved_timeline"
    RENDERER_SOURCE = "renderer_source"
    RENDER = "render"
