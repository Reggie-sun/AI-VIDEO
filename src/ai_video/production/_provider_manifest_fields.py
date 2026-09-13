"""Version admission for explicit commercial and paid Provider Manifest fields."""

from collections.abc import Mapping

from ai_video.production._commercial_source_state import reject_explicit_commercial_source_fields
from ai_video.production._lifecycle_schema import (
    reject_explicit_p0_fields,
    reject_explicit_paid_provider_fields,
)
from ai_video.production.manifest_schema import ManifestCapability, manifest_supports


def reject_unsupported_provider_fields(value: object) -> object:
    if isinstance(value, Mapping) and not manifest_supports(
        value.get("schema_version", "2.0"), ManifestCapability.AD_GENERATION
    ):
        for attempt in value.get("attempts", ()):
            if isinstance(attempt, Mapping):
                has_ad = "ad_generation_state" in attempt or attempt.get("operation") == "ad_generation"
            else:
                has_ad = (getattr(attempt, "ad_generation_state", None) is not None
                          or getattr(attempt, "operation", None) == "ad_generation")
            if has_ad:
                raise ValueError("ad generation state requires Manifest 2.16")
    return reject_explicit_p0_fields(
        reject_explicit_paid_provider_fields(reject_explicit_commercial_source_fields(value))
    )
