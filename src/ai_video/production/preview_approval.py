"""User approval of a cheap visual preview before paid drama generation.

The Director shows the user the decisive keyframes (the same reference package
the generation will use) and records the user's exact words. This module only
checks that such evidence is well formed and sealed; it cannot prove the quote
was spoken, judge the preview or replace the user's normal-speed review.
"""
from __future__ import annotations

import re

KIND = "user-preview-approval/1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FIELDS = {"kind", "coverage_hash", "unit_ids", "preview_artifacts", "user_quote"}
_ARTIFACT_FIELDS = {"path", "sha256", "role"}


class PreviewApprovalError(ValueError):
    pass


def validate_preview_approval(payload) -> None:
    if not isinstance(payload, dict) or set(payload) != _FIELDS or payload["kind"] != KIND:
        raise PreviewApprovalError("preview approval must use the exact user-preview-approval/1 fields")
    if not isinstance(payload["coverage_hash"], str) or not _SHA256.fullmatch(payload["coverage_hash"]):
        raise PreviewApprovalError("coverage_hash must bind exact Director coverage")
    units = payload["unit_ids"]
    if (not isinstance(units, list) or not units or len(set(units)) != len(units)
            or not all(isinstance(unit, str) and unit.strip() for unit in units)):
        raise PreviewApprovalError("unit_ids must list the approved coverage units once each")
    artifacts = payload["preview_artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise PreviewApprovalError("preview_artifacts must list the images the user actually saw")
    for artifact in artifacts:
        if (not isinstance(artifact, dict) or set(artifact) != _ARTIFACT_FIELDS
                or not all(isinstance(artifact[key], str) and artifact[key].strip() for key in _ARTIFACT_FIELDS)
                or not _SHA256.fullmatch(artifact["sha256"])):
            raise PreviewApprovalError("each preview artifact needs path, exact sha256 and its role")
    quote = payload["user_quote"]
    if not isinstance(quote, str) or not quote.strip():
        raise PreviewApprovalError("user_quote must be the user's exact approval words")


def preview_approval_authoring_input(payload):
    """Validate and return (approval_hash, sealable artifact) for an authoring owner."""

    import hashlib
    from pathlib import Path

    from ai_video.production.authoring_input import authoring_input_payload, authoring_input_reference
    from ai_video.production.state_commit import PreparedArtifact

    validate_preview_approval(payload)
    reference = authoring_input_reference(payload)
    data = authoring_input_payload(payload)
    return reference.content_hash, PreparedArtifact(Path(reference.reference), data, hashlib.sha256(data).hexdigest())


__all__ = ["KIND", "PreviewApprovalError", "preview_approval_authoring_input", "validate_preview_approval"]
