"""Ephemeral expression evidence issued by the existing sequence owner.

This is not a serialized state contract or an acceptance/selection authority.
Only current opening facts are exposed to the native grammar.
"""

from dataclasses import dataclass
from weakref import WeakKeyDictionary

from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import ContinuityStateKind
from ai_video.production.video_transition import CausalStateChange


_ISSUER = object()
_ISSUED = WeakKeyDictionary()


@dataclass(frozen=True, eq=False)
class VerifiedCausalOpeningExpression:
    requirement_hash: str
    provider_bound_request_hash: str
    policy_hash: str
    route_binding_hash: str
    source_close_state_hash: str
    changes: tuple[CausalStateChange, ...]
    _seal: str
    _issuer: object | None = None

    def _payload(self):
        return {
            "requirement_hash": self.requirement_hash,
            "provider_bound_request_hash": self.provider_bound_request_hash,
            "policy_hash": self.policy_hash,
            "route_binding_hash": self.route_binding_hash,
            "source_close_state_hash": self.source_close_state_hash,
            "changes": [c.model_dump(mode="json") for c in self.changes],
        }

    def opening_facts(self, requirement, provider_bound):
        """Revalidate exact immutable issuance and both column seals per use."""
        from ai_video.production._sequence_source import causal_state_column_hash
        from ai_video.production._shot_router_contracts import ProviderBoundVideoRequest
        from ai_video.production.video_requirement import ProviderNeutralVideoRequirement

        requirement = ProviderNeutralVideoRequirement.model_validate(requirement.model_dump(mode="python"))
        provider_bound = ProviderBoundVideoRequest.model_validate(provider_bound.model_dump(mode="python"))
        if (_ISSUED.get(self) != self._seal or self._issuer is not _ISSUER
                or self._seal != canonical_sha256(self._payload())
                or self.requirement_hash != requirement.requirement_hash
                or self.provider_bound_request_hash != provider_bound.provider_bound_request_hash
                or provider_bound.requirement_hash != requirement.requirement_hash):
            raise ValueError("causal opening expression has no exact owner-issued lineage")
        changes = tuple(CausalStateChange.model_validate(c.model_dump(mode="python")) for c in self.changes)
        opening = requirement.generation_intent.open_state
        if (opening.kind is not ContinuityStateKind.TYPED_HASH
                or causal_state_column_hash(changes, endpoint="target_open") != opening.state_hash
                or causal_state_column_hash(changes, endpoint="source_close") != self.source_close_state_hash):
            raise ValueError("causal opening expression column seal is stale")
        return tuple((c.dimension, c.target_open) for c in sorted(changes, key=lambda c: c.dimension.value))


def _issue_causal_opening_expression(*, requirement, provider_bound, routing, source_intent):
    """Private constructor called only after the sequence owner reopens proof."""
    from dataclasses import replace

    candidate = VerifiedCausalOpeningExpression(
        requirement_hash=requirement.requirement_hash,
        provider_bound_request_hash=provider_bound.provider_bound_request_hash,
        policy_hash=routing.transition_policy.policy_hash, route_binding_hash=routing.binding_hash,
        source_close_state_hash=source_intent.close_state.state_hash,
        changes=routing.transition_policy.causal_state_changes, _seal="", _issuer=_ISSUER)
    sealed = replace(candidate, _seal=canonical_sha256(candidate._payload()))
    _ISSUED[sealed] = sealed._seal
    return sealed
