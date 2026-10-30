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


def _approval(coverage=None, unit_ids=("shot-01",)):
    coverage = coverage or _payload()
    return {"kind": "user-preview-approval/1", "coverage_hash": canonical_sha256(coverage),
            "unit_ids": list(unit_ids),
            "preview_artifacts": [{"path": "preview/keyframe-01.png", "sha256": "a" * 64, "role": "decisive beat"}],
            "user_quote": "这版分镜可以，生成吧"}


def _approval_binding(approval=None):
    return {"approval_hash": canonical_sha256(approval or _approval())}


def _intent(camera=None, events=(), binding=None, planning=True, approval=True):
    data = {"primary_camera_motion": camera}
    if planning:
        data["reference_planning"] = {"facets": ["identity_consistency"], "events": list(events),
                                      **({"director_coverage": binding} if binding else {}),
                                      **({"preview_approval": _approval_binding()} if approval else {})}
    return GenerationIntent.model_validate({k: v for k, v in data.items() if v is not None})


def _seal(tmp_path: Path, payload):
    reference = authoring_input_reference(payload)
    target = tmp_path / reference.reference
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(authoring_input_payload(payload))
    return reference


def _project(tmp_path: Path, coverage, *, sealed=True, approval=None):
    references = (_seal(tmp_path, coverage), _seal(tmp_path, approval or _approval(coverage)))
    return SimpleNamespace(root=tmp_path, shots=(),
                           project=SimpleNamespace(source_provenance=references if sealed else ()))


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
    assert "preview_approval" not in ReferencePlanningIntent(facets=("stable",)).model_dump(mode="json")
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
    file.write_bytes(file.read_bytes().replace(b"shot-01", b"shot-07", 1))
    assert director_coverage_evidence_issues(binding, tampered) == (path,)
    invalid = dict(coverage, coverage_units=[])
    invalid_binding = ReferencePlanningIntent(director_coverage=_binding(invalid)).director_coverage
    assert director_coverage_evidence_issues(invalid_binding, _project(tmp_path / "c", invalid)) == (path,)


def test_drama_requires_sealed_user_preview_approval_for_the_exact_unit(tmp_path):
    coverage = _payload()
    binding = _binding(coverage)
    assert reference_authoring_issues(_intent(binding=binding, approval=False)) == (
        "generation_intent.reference_planning.preview_approval",)
    requirement = SimpleNamespace(generation_intent=_intent(binding=binding))
    require_reference_authoring(requirement, project=_project(tmp_path / "ok", coverage))
    other_unit = _project(tmp_path / "unit", coverage, approval=_approval(coverage, ("shot-09",)))
    with pytest.raises(AiVideoError, match=r"preview_approval\[coverage_unit\]"):
        require_reference_authoring(SimpleNamespace(generation_intent=_intent(
            binding=binding).model_copy(update={"reference_planning": _intent(binding=binding).reference_planning.model_copy(
            update={"preview_approval": ReferencePlanningIntent.model_validate(
                {"preview_approval": _approval_binding(_approval(coverage, ("shot-09",)))}).preview_approval})})),
            project=other_unit)
    unsealed = SimpleNamespace(root=tmp_path / "ok", shots=(), project=SimpleNamespace(
        source_provenance=(authoring_input_reference(coverage),)))
    with pytest.raises(AiVideoError, match="preview_approval.approval_hash"):
        require_reference_authoring(requirement, project=unsealed)


def test_preview_approval_payload_must_name_what_the_user_saw():
    from ai_video.production.preview_approval import PreviewApprovalError, validate_preview_approval
    validate_preview_approval(_approval())
    for broken in ({**_approval(), "preview_artifacts": []}, {**_approval(), "user_quote": " "},
                   {**_approval(), "unit_ids": []}, {**_approval(), "extra": 1}):
        with pytest.raises(PreviewApprovalError):
            validate_preview_approval(broken)


_PERFORMANCE = {"trigger": "回到原层", "visible_response": "停住", "gaze_target": "灭火器", "body_behavior": "停住",
                "hand_behavior": "垂下", "terminal_performance_state": "盯着灭火器"}


def test_visible_performer_cannot_be_dropped_from_identity_continuity():
    direction = {"character_id": "resident", "screen_identity": "住户", "role": "principal",
                 "visibility": "visible", "beats": [{"phase": "throughout", "trigger": "回到原层",
                 "emotion": "惊疑", "intensity": "moderate", "facial_expression": "愣住", "gaze_target": "灭火器",
                 "breathing": "屏住", "body_behavior": "停住"}]}
    planning = {"facets": ["stable"], "director_coverage": _binding(), "preview_approval": _approval_binding()}
    dodged = GenerationIntent.model_validate({"reference_planning": planning,
        "performance_intent": {**_PERFORMANCE, "character_directions": [direction]}})
    assert reference_authoring_issues(dodged) == (
        "generation_intent.identity_continuity.character_ids[resident]",)
    covered = dodged.model_copy(update={"identity_continuity": dodged.identity_continuity.model_copy(
        update={"character_ids": ("resident",), "preservation": "exact"})})
    assert reference_authoring_issues(covered) == ()
    offscreen = GenerationIntent.model_validate({"reference_planning": planning, "performance_intent": {**_PERFORMANCE,
        "character_directions": [{**direction, "visibility": "offscreen", "offscreen_reason": "画外声", "beats": []}]}})
    assert reference_authoring_issues(offscreen) == ()


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


@pytest.mark.parametrize("movement", ["unspecified", "locked", "locked-off"])
def test_still_camera_tokens_need_no_composition_without_structured_motion(movement):
    intent = GenerationIntent.model_validate({"camera_intent": {"movement": movement},
        "reference_planning": {"facets": ["stable"], "director_coverage": _binding(),
        "preview_approval": _approval_binding()}})
    assert reference_authoring_issues(intent) == ()


def test_camera_prose_without_structured_motion_must_state_what_it_reveals():
    prose = {"camera_intent": {"movement": "缓慢推进到门口"}}
    intent = GenerationIntent.model_validate({**prose,
        "reference_planning": {"facets": ["stable"], "director_coverage": _binding(),
        "preview_approval": _approval_binding()}})
    assert reference_authoring_issues(intent) == ("generation_intent.reference_planning.events[composition]",)
    with pytest.raises(AiVideoError, match=r"events\[composition\]"):
        require_reference_authoring(SimpleNamespace(generation_intent=intent))
    ecommerce = SimpleNamespace(generation_intent=GenerationIntent.model_validate({**prose,
        "reference_planning": {"facets": ["stable"]}}), commercial_execution_class="product_interaction")
    with pytest.raises(AiVideoError, match=r"events\[composition\]"):
        require_reference_authoring(ecommerce, commercial_binding=SimpleNamespace(ad_creative_plan_hash="a" * 64))
    declared = GenerationIntent.model_validate({**prose,
        "reference_planning": {"facets": ["stable"], "director_coverage": _binding(),
        "preview_approval": _approval_binding(), "events": [REVEAL]}})
    assert reference_authoring_issues(declared) == ()


def test_legacy_v1_route_keeps_locked_camera_and_gates_prose_movement():
    """A real v1 T2VA requirement cannot carry primary_camera_motion; locked stays valid."""
    from tests.test_production_h3_prompt_zh import _legacy_t2va_requirement
    planning = {"facets": ["stable"], "director_coverage": _binding(),
        "preview_approval": _approval_binding()}
    legacy = _legacy_t2va_requirement()
    assert legacy.contract_version == "provider-neutral-video-requirement/1"
    assert legacy.generation_intent.primary_camera_motion is None
    locked = legacy.generation_intent.model_copy(
        update={"reference_planning": ReferencePlanningIntent.model_validate(planning)})
    require_reference_authoring(SimpleNamespace(generation_intent=locked))
    moving = locked.model_copy(update={"camera_intent": locked.camera_intent.model_copy(
        update={"movement": "slow push toward the doorway"})})
    assert reference_authoring_issues(moving) == ("generation_intent.reference_planning.events[composition]",)
