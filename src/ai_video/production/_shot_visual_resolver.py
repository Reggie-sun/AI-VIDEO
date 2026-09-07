"""Retired authoring selector; immutable historical proposal types remain readable."""


class ShotVisualResolver:
    """Compatibility tombstone for callers of the former strategy selector."""

    def resolve(self, context, policy):
        raise ValueError(
            "ShotVisualResolver selection is retired; author ProductionIntent and "
            "use Planning ProductionStrategyResolver before generation routing."
        )
