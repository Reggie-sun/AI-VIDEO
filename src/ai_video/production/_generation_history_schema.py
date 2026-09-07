"""Additive Manifest contract for explicitly imported generation observations."""

from collections.abc import Mapping

from pydantic import model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production._lifecycle_schema import ImportedGenerationExperienceReceiptPointer
from ai_video.production.manifest_schema import ManifestCapability, manifest_supports


class GenerationHistoryManifestMixin(StrictModel):
    imported_generation_experiences: tuple[ImportedGenerationExperienceReceiptPointer, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _reject_unsupported_imported_history(cls, value):
        if (isinstance(value, Mapping) and "imported_generation_experiences" in value
                and not manifest_supports(value.get("schema_version", "2.0"),
                                          ManifestCapability.VIDEO_GENERATION)):
            raise ValueError("Imported generation history requires video-generation capability")
        return value

    @model_validator(mode="after")
    def _validate_imported_history(self):
        imports = self.imported_generation_experiences
        if imports and not manifest_supports(self.schema_version, ManifestCapability.VIDEO_GENERATION):
            raise ValueError("Imported generation history requires video-generation capability")
        if len({p.content_hash for p in imports}) != len(imports) or len(
            {p.request_fingerprint for p in imports}
        ) != len(imports):
            raise ValueError("Imported generation histories must have unique source requests")
        return self

    def _serialize_imported_history(self, data):
        if not self.imported_generation_experiences:
            data.pop("imported_generation_experiences", None)
        return data
