"""New generation requires Director-declared reference planning; history stays readable."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.authoring_input import authoring_input_payload, authoring_input_reference
from ai_video.production.hashing import canonical_sha256
from ai_video.production.reference_authoring import (
    director_coverage_evidence_issues, reference_authoring_issues, require_reference_authoring,
)
from ai_video.production.reference_planning_contracts import ReferencePlanningIntent
from ai_video.production.video_requirement import GenerationIntent
from tests.test_open_video_skill import _payload

MOVING = {"movement_kind": "dolly_in", "direction": "forward", "amplitude_class": "moderate",
          "speed_class": "slow", "start_motion_state": "in_motion", "end_motion_state": "settled"}
LOCKED = {"movement_kind": "locked", "direction": "none", "amplitude_class": "subtle",
          "speed_class": "very_slow", "start_motion_state": "stationary", "end_motion_state": "settled"}
REVEAL = {"event_id": "reveal", "kind": "composition", "phase": "end",
          "visual_state": "门后的走廊完整露出", "purpose": "推近让观众看清门后已换成另一层"}


def _binding(coverage=None, unit_id="shot-01"):
    coverage = coverage or _payload()
    return {"coverage_hash": canonical_sha256(coverage), "unit_id": unit_id}


def _intent(camera=None, events=(), binding=None, planning=True):
    data = {"primary_camera_motion": camera}
    if planning:
        data["reference_planning"] = {"facets": ["identity_consistency"], "events": list(events),
                                      **({"director_coverage": binding} if binding else {})}
    return GenerationIntent.model_validate({k: v for k, v in data.items() if v is not None})


def _project(tmp_path: Path, coverage, *, sealed=True):
    reference = authoring_input_reference(coverage)
    target = tmp_path / reference.reference
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(authoring_input_payload(coverage))
    return SimpleNamespace(root=tmp_path, shots=(),
                           project=SimpleNamespace(source_provenance=(reference,) if sealed else ()))


def test_missing_reference_planning_blocks_new_generation_without_autofill():
    requirement = SimpleNamespace(generation_intent=_intent(planning=False))
    before = requirement.generation_intent.model_dump(mode="json")
    with pytest.raises(AiVideoError, match="generation_intent.reference_planning"):
        require_reference_authoring(requirement)
    assert requirement.generation_intent.model_dump(mode="json") == before


def test_moving_camera_must_declare_what_the_move_reveals():
    binding = _binding()
    assert reference_authoring_issues(_intent(MOVING, binding=binding)) == (
        "generation_intent.reference_planning.events[composition]",)
    assert reference_authoring_issues(_intent(MOVING, [REVEAL], binding)) == ()
    assert reference_authoring_issues(_intent(LOCKED, binding=binding)) == ()
    assert reference_authoring_issues(_intent(binding=binding)) == ()


def test_director_coverage_binding_is_required_and_omitted_from_legacy_serialization():
    assert reference_authoring_issues(_intent()) == ("generation_intent.reference_planning.director_coverage",)
    legacy = ReferencePlanningIntent(facets=("stable",))
    assert "director_coverage" not in legacy.model_dump(mode="json")
    bound = ReferencePlanningIntent(facets=("stable",), director_coverage=_binding())
    assert bound.model_dump(mode="json")["director_coverage"]["unit_id"] == "shot-01"


def test_exact_sealed_coverage_evidence_is_reopened_and_unit_checked(tmp_path):
    coverage = _payload()
    project = _project(tmp_path, coverage)
    requirement = SimpleNamespace(generation_intent=_intent(MOVING, [REVEAL], _binding(coverage)))
    require_reference_authoring(requirement, project=project)
    planning = requirement.generation_intent.reference_planning
    wrong_unit = planning.director_coverage.model_copy(update={"unit_id": "shot-09"})
    assert director_coverage_evidence_issues(wrong_unit, project) == (
        "generation_intent.reference_planning.director_coverage.unit_id",)


def test_unsealed_tampered_or_invalid_coverage_fails_closed(tmp_path):
    coverage = _payload()
    binding = ReferencePlanningIntent(director_coverage=_binding(coverage)).director_coverage
    path = "generation_intent.reference_planning.director_coverage.coverage_hash"
    assert director_coverage_evidence_issues(binding, _project(tmp_path / "a", coverage, sealed=False)) == (path,)
    tampered = _project(tmp_path / "b", coverage)
    file = tampered.root / authoring_input_reference(coverage).reference
    file.write_bytes(file.read_bytes().replace(b"shot-01", b"shot-07"))
    assert director_coverage_evidence_issues(binding, tampered) == (path,)
    invalid = dict(coverage, coverage_units=[])
    invalid_binding = ReferencePlanningIntent(director_coverage=_binding(invalid)).director_coverage
    assert director_coverage_evidence_issues(invalid_binding, _project(tmp_path / "c", invalid)) == (path,)


def test_ecommerce_uses_its_own_director_layer_not_drama_coverage():
    plan_binding = SimpleNamespace(ad_creative_plan_hash="a" * 64)
    shared = _intent(MOVING, [REVEAL])
    requirement = SimpleNamespace(generation_intent=shared, commercial_execution_class="product_interaction")
    assert reference_authoring_issues(shared, ecommerce=True) == ()
    require_reference_authoring(requirement)  # before compilation the plan binding is not yet known
    require_reference_authoring(requirement, commercial_binding=plan_binding)
    with pytest.raises(AiVideoError, match="commercial_binding.ad_creative_plan_hash"):
        require_reference_authoring(requirement, commercial_binding=None)
    drama_bound = _intent(MOVING, [REVEAL], _binding())
    assert reference_authoring_issues(drama_bound, ecommerce=True) == (
        "generation_intent.reference_planning.director_coverage[ecommerce_uses_ad_creative_plan]",)


def test_shared_reference_planning_still_applies_to_ecommerce():
    requirement = SimpleNamespace(generation_intent=_intent(MOVING), commercial_execution_class="product_interaction")
    with pytest.raises(AiVideoError, match=r"events\[composition\]"):
        require_reference_authoring(requirement, commercial_binding=SimpleNamespace(ad_creative_plan_hash="a" * 64))
    missing = SimpleNamespace(generation_intent=_intent(planning=False), commercial_execution_class="product_interaction")
    with pytest.raises(AiVideoError, match="generation_intent.reference_planning"):
        require_reference_authoring(missing)
