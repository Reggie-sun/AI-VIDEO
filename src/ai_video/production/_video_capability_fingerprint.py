"""Shared backward-compatible capability fingerprint projection.

This module owns the exact projection used by every surface that hashes a
:class:`VideoCapabilityVariant` or a :class:`VideoProviderCapabilities`
snapshot.  The projection is designed so that the frozen v1 legacy hashes
remain bit-for-bit unchanged: when a variant declares no cardinality
constraints, the legacy ``binding_cardinality_constraints`` key is omitted
from the projection entirely, matching the pre-Milestone-1 ``model_dump``
output.

Non-empty constraints are projected with their canonical role tuple and
bound order, and are included under ``binding_cardinality_constraints`` as
a JSON-serialisable list.

The helpers in this module never import :mod:`video` or :mod:`shot_router`
directly; callers pass already-constructed model instances.  This keeps the
projection as a single point of truth and prevents each surface from
re-implementing its own hash surface and drifting from the accepted plan.
"""

from __future__ import annotations

from typing import Any

from ai_video.production.video_contracts import VideoBindingCardinalityConstraint
from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_contracts import binding_counts_satisfy_constraints


def _constraint_projection(
    constraint: VideoBindingCardinalityConstraint,
) -> dict[str, Any]:
    return {
        "roles": list(constraint.roles),
        "min_count": constraint.min_count,
        "max_count": constraint.max_count,
    }


def project_capability_variant(variant: Any) -> dict[str, Any]:
    """Return the canonical projection of a :class:`VideoCapabilityVariant`.

    The legacy v1 hashes depended on the ``model_dump(mode="json")`` payload
    of the variant containing no ``binding_cardinality_constraints`` field.
    To preserve that contract, the field is omitted from the projection
    unless the variant declares at least one constraint.  Non-empty
    constraints are included under the canonical key.
    """

    payload = variant.model_dump(mode="json")
    constraints = getattr(variant, "binding_cardinality_constraints", ()) or ()
    if not constraints:
        payload.pop("binding_cardinality_constraints", None)
        return payload
    payload["binding_cardinality_constraints"] = [
        _constraint_projection(constraint) for constraint in constraints
    ]
    return payload


def project_provider_capabilities(capabilities: Any) -> dict[str, Any]:
    """Return the canonical projection of a :class:`VideoProviderCapabilities`.

    The :class:`VideoProviderCapabilities` seal hashes the set of variants
    excluding the capability fingerprint itself.  This helper applies
    :func:`project_capability_variant` to every nested variant so the
    projection rules apply uniformly to nested capability children.
    """

    payload = capabilities.model_dump(mode="json")
    payload["variants"] = [
        project_capability_variant(variant) for variant in capabilities.variants
    ]
    payload.pop("capabilities_fingerprint", None)
    return payload


def capability_variant_fingerprint(variant: Any) -> str:
    """Hash the one canonical capability projection."""

    return canonical_sha256(project_capability_variant(variant))


def binding_roles_satisfy_variant(
    variant: Any, binding_roles: tuple[str, ...]
) -> bool:
    """Evaluate Router-owned binding roles against an exact variant grammar."""

    constraints = getattr(variant, "binding_cardinality_constraints", ()) or ()
    if not constraints:
        return True
    counts = {
        role: binding_roles.count(role)
        for role in (
            "first_frame",
            "last_frame",
            "reference",
            "reference_video",
            "reference_audio",
        )
    }
    return binding_counts_satisfy_constraints(constraints, counts)


__all__ = [
    "project_capability_variant",
    "project_provider_capabilities",
    "capability_variant_fingerprint",
    "binding_roles_satisfy_variant",
]
