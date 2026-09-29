"""Immutable named-reference projections, separate from creative ownership."""

from typing import Literal

from pydantic import ConfigDict, Field, SerializerFunctionWrapHandler, model_serializer, model_validator

from ai_video.production.commercial_video_contracts import CommercialVideoBindingMixin
from ai_video.production.models import StrictModel

_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"


class VideoSubjectBinding(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    name: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
    canonical_owner_kind: Literal["character", "scene"]
    canonical_owner_id: str = Field(pattern=_SAFE_ID)
    canonical_owner_content_hash: str = Field(pattern=_SHA256)
    image_asset_ids: tuple[str, ...] = Field(min_length=1)
    voice_id: str | None = Field(default=None, min_length=1, max_length=256)
    voice_reference_asset_id: str | None = Field(default=None, pattern=_SAFE_ID)
    voice_reference_sha256: str | None = Field(default=None, pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_identity(self):
        if self.image_asset_ids != tuple(sorted(set(self.image_asset_ids))):
            raise ValueError("subject image IDs must be unique and ordered")
        if (self.voice_reference_asset_id is None) != (self.voice_reference_sha256 is None):
            raise ValueError("subject voice reference identity must be paired")
        if self.canonical_owner_kind == "scene" and any(value is not None for value in (
            self.voice_id, self.voice_reference_asset_id, self.voice_reference_sha256,
        )):
            raise ValueError("scene subjects cannot own a speaker voice")
        return self


class VideoSubjectCapability(StrictModel):
    max_subjects: int = Field(strict=True, gt=0)
    max_images_per_subject: int = Field(strict=True, gt=0)
    max_total_images: int = Field(strict=True, gt=0)
    voice_ids_supported: bool = Field(default=False, strict=True)


class VideoSubjectBindingMixin(CommercialVideoBindingMixin):
    subject_bindings: tuple[VideoSubjectBinding, ...] = ()

    @model_serializer(mode="wrap")
    def _serialize_optional_commercial_binding(self, handler: SerializerFunctionWrapHandler):
        data = super()._serialize_optional_commercial_binding(handler)
        if not self.subject_bindings:
            data.pop("subject_bindings", None)
        return data

    @model_validator(mode="after")
    def _validate_subject_partition(self):
        subjects = self.subject_bindings
        if not subjects:
            return self
        images = self.image_bindings
        ids = tuple(asset_id for subject in subjects for asset_id in subject.image_asset_ids)
        owners = tuple((s.canonical_owner_kind, s.canonical_owner_id) for s in subjects)
        if (
            self.mode.value != "reference_to_video"
            or self.media_bindings
            or any(image.role != "reference" for image in images)
            or len(set(ids)) != len(ids)
            or set(ids) != {image.asset_id for image in images}
            or len(ids) != len(images)
            or len(set(owners)) != len(owners)
            or tuple(s.name for s in subjects) != tuple(sorted({s.name for s in subjects}))
        ):
            raise ValueError("subjects require one complete unique named reference partition")
        return self


def subject_capability_errors(subjects, capability) -> tuple[str, ...]:
    contract = capability.subject_reference_capability
    if not subjects:
        return ("subject_bindings",) if contract is not None else ()
    if contract is None or len(subjects) > contract.max_subjects or (
        sum(len(s.image_asset_ids) for s in subjects) > contract.max_total_images
        or any(len(s.image_asset_ids) > contract.max_images_per_subject for s in subjects)
    ):
        return ("subject_bindings",)
    if not contract.voice_ids_supported and any(
        s.voice_id is not None or s.voice_reference_asset_id is not None for s in subjects
    ):
        return ("subject_bindings.voice_id",)
    return ()
