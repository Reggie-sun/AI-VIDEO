"""Pydantic mixins for caption-aware review and Manifest compatibility."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from pydantic import SerializerFunctionWrapHandler, model_serializer, model_validator

from ai_video.production.caption_quality_contracts import (
    CaptionEvidencePayload,
    CaptionQualityPolicy,
    CaptionReviewContext,
)
from ai_video.production.domain_acceptance import QaLayer
from ai_video.production.manifest_schema import ManifestCapability, manifest_supports


class CaptionManifestMixin:
    @model_validator(mode="before")
    @classmethod
    def _reject_caption_state_before_215(cls, value: object) -> object:
        if not isinstance(value, Mapping) or manifest_supports(
            value.get("schema_version", "2.0"), ManifestCapability.CAPTION_REVIEW
        ):
            return value
        items = (*value.get("review_states", ()), *value.get("active_review_receipts", ()))
        if any(
            (item.get("layer") if isinstance(item, Mapping) else getattr(item, "layer", None))
            in {QaLayer.CAPTION, QaLayer.CAPTION.value}
            for item in items
        ):
            raise ValueError(
                f"Production Manifest {value.get('schema_version', '2.0')} cannot contain CAPTION review state"
            )
        return value


class CaptionQaPolicyMixin:
    schema_version: Literal["2.0", "2.1"] = "2.0"
    caption_policy: CaptionQualityPolicy | None = None

    @model_validator(mode="before")
    @classmethod
    def _reject_caption_policy_in_20(cls, value: object) -> object:
        if (
            isinstance(value, Mapping)
            and value.get("schema_version", "2.0") == "2.0"
            and (
                "caption_policy" in value
                or QaLayer.CAPTION.value in value.get("required_layers", ())
            )
        ):
            raise ValueError("QaPolicy 2.0 cannot contain caption QA fields")
        return value

    @model_validator(mode="after")
    def _validate_caption_policy(self):
        caption_aware = self.schema_version == "2.1"
        if caption_aware != (self.caption_policy is not None):
            raise ValueError("QaPolicy 2.1 requires exactly one caption policy")
        if caption_aware != (QaLayer.CAPTION in self.required_layers):
            raise ValueError("QaPolicy caption version and required layer must agree")
        if caption_aware and self.layout_rules.caption_overflow_tolerance_milli != 0:
            raise ValueError(
                "caption-aware policy requires inert legacy layout overflow sentinel"
            )
        return self


class CaptionReviewRequestMixin:
    schema_version: Literal["2.0", "2.1"] = "2.0"
    caption_context: CaptionReviewContext | None = None

    @model_validator(mode="before")
    @classmethod
    def _reject_caption_context_in_20(cls, value: object) -> object:
        if (
            isinstance(value, Mapping)
            and value.get("schema_version", "2.0") == "2.0"
            and (
                "caption_context" in value
                or QaLayer.CAPTION.value in value.get("requested_layers", ())
            )
        ):
            raise ValueError("ReviewRequest 2.0 cannot contain caption QA fields")
        return value

    @model_validator(mode="after")
    def _validate_caption_context(self):
        caption_requested = QaLayer.CAPTION in self.requested_layers
        if caption_requested != (self.schema_version == "2.1"):
            raise ValueError("CAPTION requests require ReviewRequest 2.1")
        if caption_requested != (self.caption_context is not None):
            raise ValueError("CAPTION requests require exact caption context")
        if self.caption_context is not None and (
            self.caption_context.render_output_sha256 != self.render_output_sha256
            or self.caption_context.timeline_fingerprint != self.timeline_fingerprint
            or self.caption_context.dependency_graph_revision_id
            != self.dependency_graph.revision_id
        ):
            raise ValueError("caption context does not match ReviewRequest identity")
        return self

    @model_serializer(mode="wrap")
    def _serialize_optional_caption_context(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.caption_context is None:
            data.pop("caption_context", None)
        return data


class CaptionReviewEvidenceMixin:
    schema_version: Literal["2.0", "2.1"] = "2.0"

    @model_validator(mode="after")
    def _validate_versioned_caption_payload(self):
        caption_layer = self.layer is QaLayer.CAPTION
        if caption_layer != (self.schema_version == "2.1"):
            raise ValueError("CAPTION evidence requires ReviewEvidence 2.1")
        if caption_layer:
            CaptionEvidencePayload.model_validate(dict(self.measured_payload))
        return self


class CaptionReviewReceiptMixin:
    schema_version: Literal["2.0", "2.1"] = "2.0"

    @model_validator(mode="after")
    def _validate_caption_receipt_version(self):
        if (self.layer is QaLayer.CAPTION) != (self.schema_version == "2.1"):
            raise ValueError("CAPTION receipt requires ReviewReceipt 2.1")
        return self


class CaptionRepairOutcomeMixin:
    schema_version: Literal["2.0", "2.1"] = "2.0"

    @model_validator(mode="after")
    def _validate_caption_receipt_version(self):
        if any(item.layer is QaLayer.CAPTION for item in self.fresh_review_receipts):
            if self.schema_version != "2.1":
                raise ValueError("caption repair outcome requires schema 2.1")
        return self


class CaptionFinalAcceptanceMixin:
    schema_version: Literal["2.0", "2.1"] = "2.0"

    @model_validator(mode="after")
    def _validate_caption_receipt_version(self):
        if any(item.layer is QaLayer.CAPTION for item in self.required_review_receipts):
            if self.schema_version != "2.1":
                raise ValueError("caption final acceptance requires schema 2.1")
        return self
