"""Canonical dependency node identities and fingerprint primitives."""

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import FingerprintContribution


def creative_node_id(artifact_kind: str, artifact_id: str) -> str:
    if not artifact_kind or not artifact_id:
        raise ValueError("creative_node_id requires non-empty kind and id")
    return f"creative:{artifact_kind}:{artifact_id}"


def shot_projection_node_id(shot_id: str, semantic_role: str) -> str:
    if not shot_id or not semantic_role:
        raise ValueError("shot_projection_node_id requires non-empty shot id and role")
    return f"creative:shot:{shot_id}:{semantic_role}"


def fingerprint_value(schema: str, value: object) -> str:
    return canonical_sha256({"schema": schema, "value": value})


def fingerprint_items(**values: str) -> tuple[FingerprintContribution, ...]:
    return tuple(
        FingerprintContribution(key=key, fingerprint=fingerprint)
        for key, fingerprint in sorted(values.items())
    )
