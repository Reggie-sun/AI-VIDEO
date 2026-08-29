"""Seedance reference-duration policy with exact provider-output provenance."""

from __future__ import annotations

from typing import Protocol

from ai_video.production.video import VideoMediaReferenceBinding


class SeedanceNominalDurationResolver(Protocol):
    def verified_nominal_duration_millis(
        self,
        binding: VideoMediaReferenceBinding,
        *,
        family_limit_millis: int,
    ) -> int | None: ...


def seedance_reference_media_within_family_limit(
    model_id: str,
    bindings: tuple[VideoMediaReferenceBinding, ...],
    *,
    nominal_duration_resolver: SeedanceNominalDurationResolver | None,
) -> bool:
    """Apply per-kind family totals without replacing exact media measurements."""

    family_limit_millis = (
        30_000
        if model_id == "doubao-seedance-2-5-260628"
        else 15_000
        if model_id.startswith("doubao-seedance-2-0")
        else None
    )
    if family_limit_millis is None:
        return True
    for kind in ("video", "audio"):
        total_duration = 0
        for binding in bindings:
            if binding.kind != kind:
                continue
            duration = binding.duration_millis
            if kind == "video" and nominal_duration_resolver is not None:
                duration = (
                    nominal_duration_resolver.verified_nominal_duration_millis(
                        binding,
                        family_limit_millis=family_limit_millis,
                    )
                )
            if duration is None:
                return False
            total_duration += duration
        if total_duration > family_limit_millis:
            return False
    return True
