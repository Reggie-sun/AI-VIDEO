from __future__ import annotations

from collections.abc import Callable, Mapping
from decimal import Decimal
from typing import Any


def validate_egress_metadata(
    metadata: Any,
    *,
    require_canonical_origin: Callable[[str, str], str],
) -> None:
    remote_fields = (
        metadata.destination,
        metadata.authorization_receipt_id,
        metadata.request_fingerprint,
        metadata.payload_fingerprint,
        metadata.retention_mode,
        metadata.provider_policy_snapshot_id,
    )
    if not metadata.remote:
        if any(value is not None for value in remote_fields):
            raise ValueError("local egress metadata cannot contain remote fields")
        return
    if any(value is None for value in remote_fields):
        raise ValueError("remote egress metadata requires complete authorization")
    require_canonical_origin(metadata.destination, "remote destination")


def serialize_egress_metadata(
    metadata: Any, data: dict[str, object]
) -> dict[str, object]:
    if not metadata.remote:
        for field in (
            "request_fingerprint",
            "payload_fingerprint",
            "retention_mode",
            "provider_policy_snapshot_id",
        ):
            data.pop(field, None)
    return data


def validate_asset_record(
    record: Any,
    *,
    audio_kind_to_asset_type: Mapping[Any, Any],
    audio_types: frozenset[Any],
    caption_type: Any,
    video_type: Any,
    voice_type: Any,
    generated_source: Any,
) -> None:
    if record.audio_metadata is not None:
        if record.asset_type not in audio_types:
            raise ValueError("non-audio assets cannot contain audio metadata")
        if (
            audio_kind_to_asset_type[record.audio_metadata.audio_kind]
            != record.asset_type
        ):
            raise ValueError("audio kind does not match registry asset type")
        if record.duration_seconds is not None:
            measured_seconds = Decimal(
                record.audio_metadata.duration_samples
            ) / Decimal(record.audio_metadata.sample_rate_hz)
            display_seconds = Decimal(str(record.duration_seconds))
            tolerance = Decimal(1) / Decimal(record.audio_metadata.sample_rate_hz)
            if abs(measured_seconds - display_seconds) > tolerance:
                raise ValueError("duration_seconds does not match measured samples")
    if record.caption_metadata is not None and record.asset_type is not caption_type:
        raise ValueError("non-caption assets cannot contain caption metadata")
    if record.asset_type is caption_type and record.audio_metadata is not None:
        raise ValueError("caption assets cannot contain audio metadata")
    if record.video_metadata is not None:
        if record.asset_type is not video_type:
            raise ValueError("non-video assets cannot contain video metadata")
        if record.mime_type != "video/mp4":
            raise ValueError("video metadata requires video/mp4")
        if (record.width, record.height) != (
            record.video_metadata.width,
            record.video_metadata.height,
        ):
            raise ValueError("video dimensions do not match measured metadata")
        if record.duration_seconds is not None and abs(
            Decimal(str(record.duration_seconds))
            - Decimal(record.video_metadata.duration_milliseconds) / Decimal(1000)
        ) > Decimal("0.001"):
            raise ValueError("video duration does not match measured metadata")
    if record.egress.remote and not (
        record.asset_type in {voice_type, video_type}
        and record.source_kind is generated_source
    ):
        raise ValueError(
            "remote egress is restricted to generated voice/video assets"
        )


def serialize_asset_record(
    record: Any, data: dict[str, object]
) -> dict[str, object]:
    for field in ("audio_metadata", "caption_metadata", "video_metadata"):
        if getattr(record, field) is None:
            data.pop(field, None)
    return data


def reject_explicit_p4_registry_fields(value: object) -> object:
    if not isinstance(value, Mapping) or value.get("schema_version", "2.0") != "2.0":
        return value
    for asset in value.get("assets", ()):
        if isinstance(asset, Mapping) and {
            "audio_metadata",
            "caption_metadata",
        }.intersection(asset):
            raise ValueError("Asset Registry 2.0 cannot contain explicit P4 fields")
        if isinstance(asset, Mapping):
            egress = asset.get("egress")
            if isinstance(egress, Mapping) and {
                "request_fingerprint",
                "payload_fingerprint",
                "retention_mode",
                "provider_policy_snapshot_id",
            }.intersection(egress):
                raise ValueError(
                    "Asset Registry 2.0 cannot contain explicit P4 egress fields"
                )
    return value


def reject_explicit_p8_registry_fields(value: object) -> object:
    if not isinstance(value, Mapping) or value.get("schema_version", "2.0") == "2.2":
        return value
    for asset in value.get("assets", ()):
        if isinstance(asset, Mapping) and "video_metadata" in asset:
            raise ValueError(
                f"Asset Registry {value.get('schema_version', '2.0')} "
                "cannot contain explicit video metadata"
            )
    return value


def validate_registry_snapshot(
    registry: Any,
    *,
    audio_types: frozenset[Any],
    caption_type: Any,
    video_type: Any,
    generated_source: Any,
) -> None:
    if registry.schema_version == "2.0":
        if any(
            asset.audio_metadata is not None
            or asset.caption_metadata is not None
            or asset.egress.remote
            for asset in registry.assets
        ):
            raise ValueError("Asset Registry 2.0 cannot contain P4 metadata")
        return
    for asset in registry.assets:
        if asset.asset_type in audio_types:
            if asset.audio_metadata is None:
                raise ValueError(
                    "Asset Registry 2.1 audio assets require audio metadata"
                )
        elif asset.audio_metadata is not None:
            raise ValueError("non-audio assets cannot contain audio metadata")
        if asset.asset_type is caption_type:
            if asset.caption_metadata is None:
                raise ValueError(
                    "Asset Registry 2.1 caption assets require caption metadata"
                )
        elif asset.caption_metadata is not None:
            raise ValueError("non-caption assets cannot contain caption metadata")
        if registry.schema_version == "2.1":
            if asset.video_metadata is not None or (
                asset.asset_type is video_type and asset.egress.remote
            ):
                raise ValueError(
                    "Asset Registry 2.1 cannot contain P8 video metadata"
                )
        elif (
            asset.asset_type is video_type
            and asset.source_kind is generated_source
            and asset.video_metadata is None
        ):
            raise ValueError(
                "Asset Registry 2.2 generated video assets require video metadata"
            )
        if (
            registry.schema_version == "2.2"
            and asset.asset_type is video_type
            and asset.source_kind is generated_source
            and asset.egress.remote
        ):
            if asset.cost_receipt_id is None:
                raise ValueError(
                    "Asset Registry 2.2 remote generated video requires a cost receipt"
                )
            assert asset.video_metadata is not None
            if (
                asset.egress.request_fingerprint
                != asset.video_metadata.resolved_generation_hash
            ):
                raise ValueError(
                    "remote generated video egress request identity must match "
                    "its resolved generation"
                )
