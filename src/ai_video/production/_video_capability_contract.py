"""Cohesive capability validation and output-recovery compatibility contract."""

from __future__ import annotations

from enum import Enum
from typing import Self

from pydantic import SerializerFunctionWrapHandler, model_serializer, model_validator

from ai_video.production.video_contracts import validate_cardinality_constraints


class VideoOutputRecoveryStrategy(str, Enum):
    """Sealed recovery guarantee for an opaque Provider output handle."""

    DURABLE_FILE_ID = "DURABLE_FILE_ID"
    REQUERY_BY_EFFECT_ID = "REQUERY_BY_EFFECT_ID"
    NON_RECOVERABLE_EPHEMERAL_URL = "NON_RECOVERABLE_EPHEMERAL_URL"


class VideoCapabilityContractMixin:
    """Additive serialization and invariant checks for capability variants."""

    output_recovery_strategy: VideoOutputRecoveryStrategy | None = None

    @model_serializer(mode="wrap")
    def _serialize_additive_output_recovery_strategy(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.output_recovery_strategy is None:
            data.pop("output_recovery_strategy", None)
        return data

    @model_validator(mode="after")
    def _validate_variant(self) -> Self:
        if (self.output is None) == (self.output_capability is None):
            raise ValueError("video capability requires exactly one output contract")
        if len(set(self.allowed_image_roles)) != len(self.allowed_image_roles):
            raise ValueError("video capability image roles must be unique")
        if len(set(self.allowed_image_mime_types)) != len(
            self.allowed_image_mime_types
        ):
            raise ValueError("video capability image MIME types must be unique")
        if self.mode.value == "text_to_video" and (
            self.allowed_image_roles
            or self.required_first_frame
            or self.max_reference_count
            or self.media_capabilities
        ):
            raise ValueError("text-to-video capability cannot declare image bindings")
        if self.required_first_frame and "first_frame" not in self.allowed_image_roles:
            raise ValueError("required first frame must be an allowed image role")
        if (self.execution_kind.value, self.billing_kind.value) not in {
            ("local", "local_unmetered"),
            ("remote", "metered"),
        }:
            raise ValueError(
                "video capability execution and billing kinds must use a supported pair"
            )
        object.__setattr__(
            self,
            "binding_cardinality_constraints",
            validate_cardinality_constraints(self.binding_cardinality_constraints),
        )
        return self


__all__ = ["VideoCapabilityContractMixin", "VideoOutputRecoveryStrategy"]
