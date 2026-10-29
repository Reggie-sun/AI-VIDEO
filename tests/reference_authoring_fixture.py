"""Synthetic, explicitly authored Director reference planning for generation fixtures.

Mirrors ``performance_fixture``: tests that exercise a fresh generation declare
the Director layer instead of relying on the legacy advisory path.
"""

from __future__ import annotations

from ai_video.production.hashing import canonical_sha256
from ai_video.production.reference_planning_contracts import ReferencePlanningIntent

FIXTURE_UNIT_ID = "fixture-unit"
FIXTURE_REVEAL = {"event_id": "fixture-camera-purpose", "kind": "composition", "phase": "end",
                  "visual_state": "Generate 4 seconds.", "purpose": "Generate 4 seconds."}


def fixture_director_coverage(*, duration_seconds: float = 4.0) -> dict:
    """A minimal valid single-take v3 Director coverage for drama fixtures."""

    return {
        "schema_version": "3",
        "request": {
            "creative_input_kind": "missing", "creative_input_evidence": None, "creative_constraints": [],
            "target_duration_seconds": duration_seconds, "coverage_strategy": "single_take",
            "strategy_source": "agent_directed",
            "director_decision_rationale": "One fixture camera trajectory carries the whole synthetic beat.",
            "strategy_request_evidence": None, "director_skill": "open-video",
        },
        "coverage_units": [{
            "unit_id": FIXTURE_UNIT_ID, "duration_seconds": duration_seconds, "beat_function": "establish",
            "objective": "Show the synthetic fixture subject.", "open_state": "The fixture opens.",
            "close_state": "The fixture closes.", "shot_scale": "medium", "camera_treatment": "static",
            "camera_intent": "Hold on the fixture subject.", "visible_change": "The fixture beat completes.",
            "transition_out": "end", "constraint_ids": [],
        }],
    }


def fixture_director_coverage_binding(coverage: dict | None = None) -> dict:
    coverage = coverage or fixture_director_coverage()
    return {"coverage_hash": canonical_sha256(coverage), "unit_id": FIXTURE_UNIT_ID}


def fixture_director_coverage_artifact(coverage: dict | None = None):
    """Sealable authoring input for an existing authoring/bootstrap owner."""

    from ai_video.production.reference_authoring import director_coverage_authoring_input

    return director_coverage_authoring_input(coverage or fixture_director_coverage())[1]


def _camera_purpose(intent):
    """Reuse text the fixture already authors for its camera, never invent new prose."""

    camera = getattr(intent, "camera_intent", None)
    action = getattr(intent, "subject_action", None)
    for text in (getattr(camera, "framing_intent", None), getattr(camera, "movement", None),
                 getattr(action, "progression", None)):
        if text and text != "unspecified":
            return text
    return FIXTURE_REVEAL["visual_state"]


def fixture_reference_planning(*, camera_moves: bool | None = None, ecommerce: bool = False,
                               intent=None, **planning) -> ReferencePlanningIntent:
    """Declare a stable fixture Shot; moving cameras state what the move shows."""

    planning.setdefault("facets", ("stable",))
    if camera_moves is None:
        from ai_video.production.reference_authoring import _camera_moves

        camera_moves = intent is not None and _camera_moves(intent)
    if camera_moves and not any(e.get("kind") == "composition" for e in planning.get("events", ())):
        text = _camera_purpose(intent)
        planning["events"] = (*planning.get("events", ()),
                              {**FIXTURE_REVEAL, "visual_state": text, "purpose": text})
    if not ecommerce:
        planning.setdefault("director_coverage", fixture_director_coverage_binding())
    return ReferencePlanningIntent.model_validate(planning)


def with_fixture_reference_planning(intent, **kwargs):
    """Return the same GenerationIntent with explicitly declared fixture planning."""

    if intent.reference_planning is not None:
        return intent
    return intent.model_copy(update={"reference_planning": fixture_reference_planning(intent=intent, **kwargs)})


__all__ = [
    "FIXTURE_UNIT_ID",
    "fixture_director_coverage",
    "fixture_director_coverage_artifact",
    "fixture_director_coverage_binding",
    "fixture_reference_planning",
    "with_fixture_reference_planning",
]
