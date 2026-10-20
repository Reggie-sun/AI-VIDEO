"""Visual-style binding is exact; its report never claims aesthetic acceptance."""

from copy import deepcopy

import pytest


def _declare_style(row, registry):
    assets = {asset.asset_id: asset for asset in registry.assets}
    for reference in row["generation"]["references"]:
        reference.setdefault("owner_id", "robot" if reference["role"] == "character_reference" else "road")
    anchor = assets["robot-main"]
    row["visual_style"] = {
        "contract_version": "canvas-visual-style/1",
        "source": {"asset_id": anchor.asset_id, "asset_sha256": anchor.sha256},
        "reviews": [
            {"asset_id": reference["asset_id"],
             "asset_sha256": assets[reference["asset_id"]].sha256,
             "role": reference["role"], "owner_id": reference["owner_id"],
             "current_style_sha256": anchor.sha256,
             "disposition": "current_style", "observation": "Reviewed against the selected style anchor."}
            for reference in row["generation"]["references"]
            if assets[reference["asset_id"]].mime_type.startswith("image/")
        ],
    }
    return assets, anchor


def _canvas_inputs(tmp_path):
    from test_canvas_source_expression import subject_source

    packet, direction, registry, _ = subject_source(tmp_path)
    row = direction["shots"][0]
    assets, anchor = _declare_style(row, registry)
    return packet, direction, registry, row, assets, anchor


def _prepared_style(tmp_path, provider_family="seedance"):
    from test_canvas_source_expression import subject_service

    service, limits = subject_service(tmp_path, provider_family=provider_family,
        generation_output_duration_seconds=5)
    prepared = service.prepare(limits=limits)
    row = deepcopy(service.direction["shots"][0])
    _declare_style(row, service._load().registry)
    return row, prepared


def _scene_only_style(row, assets):
    room = assets["room"]
    row["generation"]["references"] = [{
        "role": "scene_reference", "asset_id": room.asset_id, "owner_id": "road",
    }]
    row["visual_style"] = {
        "contract_version": "canvas-visual-style/1",
        "source": {"asset_id": room.asset_id, "asset_sha256": room.sha256},
        "reviews": [{
            "asset_id": room.asset_id, "asset_sha256": room.sha256,
            "role": "scene_reference", "owner_id": "road",
            "current_style_sha256": room.sha256,
            "disposition": "current_style", "observation": "Reviewed against the selected style anchor.",
        }],
    }


def _performance_direction(row, *, offscreen_reason):
    row["generation"]["generation_intent"]["performance_intent"] = {
        "trigger": "the authored action begins",
        "visible_response": "the authored character response is directed",
        "gaze_target": "the authored action target",
        "body_behavior": "the character stays outside the shot",
        "hand_behavior": "no visible hand behavior",
        "terminal_performance_state": "the character remains outside the shot",
        "character_directions": [{
            "character_id": "robot", "screen_identity": "the authored robot character",
            "role": "principal", "visibility": "offscreen",
            "offscreen_reason": offscreen_reason, "beats": [],
        }],
    }


def test_legacy_canvas_shot_preflight_reports_visual_style_not_declared(tmp_path):
    from ai_video.canvas_preflight import canvas_reference_preflight
    from test_canvas_source_expression import subject_source

    packet, direction, registry, _ = subject_source(tmp_path)

    report = canvas_reference_preflight(packet=packet, direction=direction, registry=registry)
    control = report["shots"][0]["visual_style_control"]

    assert control["coverage"] == "NOT_DECLARED"
    assert control["source"] is None
    assert control["aesthetic_acceptance"] == "NOT_EVALUATED"
    assert control["source_consumption"] == "NOT_EVALUATED"


def test_missing_declaration_remains_compatible_and_is_not_required(tmp_path):
    from ai_video.canvas_visual_style import require_canvas_visual_style, visual_style_report

    _, direction, registry, row, _, _ = _canvas_inputs(tmp_path)
    row.pop("visual_style")

    report = visual_style_report(row, registry)
    required = require_canvas_visual_style(row, registry)

    assert report["coverage"] == "NOT_DECLARED"
    assert report["source"] is None
    assert required == report


def test_exact_image_references_and_owner_coverage_are_complete(tmp_path):
    from ai_video.canvas_visual_style import require_canvas_visual_style, visual_style_report

    _, _, registry, row, _, anchor = _canvas_inputs(tmp_path)

    report = visual_style_report(row, registry)

    assert require_canvas_visual_style(row, registry) == report
    assert report["coverage"] == "COMPLETE"
    assert report["source"] == {
        "source_kind": "selected_reference_anchor",
        "asset_id": anchor.asset_id,
        "asset_sha256": anchor.sha256,
    }
    assert report["target_owners"] == {
        "characters": 1, "required_visible_characters": 1, "scenes": 1,
    }
    assert report["reference_counts"] == {"selected_images": 3, "reviewed_images": 3}
    assert report["aesthetic_acceptance"] == "NOT_EVALUATED"
    assert report["source_consumption"] == "NOT_EVALUATED"
    assert report["exclusions"] == []


@pytest.mark.parametrize("damage,issue", [
    ("asset_bytes", "review_asset_sha_mismatch"),
    ("style_hash", "stale_style_review"),
])
def test_stale_asset_or_style_hash_blocks_complete_coverage(tmp_path, damage, issue):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    if damage == "asset_bytes":
        old = row["visual_style"]["reviews"][1]["asset_sha256"]
        changed = next(asset for asset in registry.assets if asset.sha256 == old)
        registry = registry.model_copy(update={"assets": tuple(
            item.model_copy(update={"sha256": "f" * 64}) if item.asset_id == changed.asset_id else item
            for item in registry.assets)})
    else:
        row["visual_style"]["reviews"][1]["current_style_sha256"] = "f" * 64

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert issue in report["issues"]


def test_source_anchor_must_be_an_exact_selected_registered_image(tmp_path):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    row["visual_style"]["source"]["asset_sha256"] = "f" * 64

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert report["source"] is None
    assert "source_anchor_sha_mismatch" in report["issues"]


def test_registered_source_image_that_is_not_selected_cannot_be_the_anchor(tmp_path):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    row["generation"]["references"] = [
        reference for reference in row["generation"]["references"]
        if reference["asset_id"] != "robot-main"
    ]
    row["visual_style"]["reviews"] = [
        review for review in row["visual_style"]["reviews"]
        if review["asset_id"] != "robot-main"
    ]

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert report["source"] is None
    assert "source_anchor_not_selected" in report["issues"]


def test_style_anchor_itself_cannot_be_downgraded_to_layout_only(tmp_path):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    anchor_review = row["visual_style"]["reviews"][0]
    anchor_review.update(disposition="identity_layout_only", scope_text="图片2",
        reason="The anchor is retained only for layout.")

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert "source_anchor_not_current_style" in report["issues"]


def test_every_character_scene_and_auxiliary_image_reference_is_covered(tmp_path):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    row["generation"]["references"] = [
        reference for reference in row["generation"]["references"]
        if reference["asset_id"] != "room"
    ]
    row["visual_style"]["reviews"] = [
        review for review in row["visual_style"]["reviews"]
        if review["asset_id"] != "robot-aux"
    ]

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert "missing_scene_reference" in report["issues"]
    assert "missing_review" in report["issues"]


def test_handoff_with_stale_style_review_stops_before_registry_commit(tmp_path):
    from copy import deepcopy
    from ai_video.errors import AiVideoError
    from test_canvas_continuity import state_target, accept_current, reference_gate

    service, provider, limits, auth, asset_id = state_target(tmp_path)
    loaded = service._load()
    asset = next(a for a in loaded.registry.assets if a.asset_id == asset_id)
    target = service.direction["shots"][1]
    target["generation"]["references"][0]["owner_id"] = "after"
    target["visual_style"] = {"contract_version": "canvas-visual-style/1",
        "source": {"asset_id": asset_id, "asset_sha256": asset.sha256},
        "reviews": [{"asset_id": asset_id, "asset_sha256": asset.sha256,
            "role": "scene_reference", "owner_id": "after", "current_style_sha256": asset.sha256,
            "disposition": "current_style", "observation": "Offline fixture identity review only."}]}
    service.revise_authoring(attempt_id="declare-handoff-reference-style")
    accept_current(service, provider, limits, auth)
    before = (service.committer.project_root / "state/manifest.json").read_bytes()
    direction_before = deepcopy(service.direction)
    with pytest.raises(AiVideoError, match="visual-style"):
        service.handoff_reference(source_shot_id="one", target_occurrence_id="b", frame_index=7,
            replace_asset_id=asset_id, usage_license="fixture-only", **reference_gate(service))
    assert (service.committer.project_root / "state/manifest.json").read_bytes() == before
    assert service.direction == direction_before
    assert provider.call_counts.submit == 1


def test_image_reference_requires_explicit_owner_binding(tmp_path):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    row["generation"]["references"][0].pop("owner_id")

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert "image_reference_owner_missing" in report["issues"]


def test_extra_review_is_rejected_even_when_other_bindings_are_complete(tmp_path):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    row["visual_style"]["reviews"].append({
        **row["visual_style"]["reviews"][0], "role": "scene_reference", "owner_id": "road"
    })

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert "extra_review" in report["issues"]


@pytest.mark.parametrize("duplicate,issue", [
    ("generation_reference", "duplicate_image_reference"),
    ("review", "duplicate_review"),
])
def test_duplicate_image_bindings_or_reviews_are_rejected(tmp_path, duplicate, issue):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    if duplicate == "generation_reference":
        row["generation"]["references"].append(dict(row["generation"]["references"][0]))
    else:
        row["visual_style"]["reviews"].append(dict(row["visual_style"]["reviews"][0]))

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert issue in report["issues"]


@pytest.mark.parametrize("scope,reason,expected_issue", [
    ("not in the prompt", "retained layout only", "identity_layout_scope_not_in_intent"),
    ("图片1", " ", "identity_layout_reason_missing"),
])
def test_identity_layout_exclusion_requires_literal_scope_and_reason(
    tmp_path, scope, reason, expected_issue
):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    review = row["visual_style"]["reviews"][1]
    review.update(disposition="identity_layout_only", scope_text=scope, reason=reason)

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert expected_issue in report["issues"]
    assert report["exclusions"] == []


def test_identity_layout_exclusion_reports_only_its_exact_bounded_scope(tmp_path):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    review = row["visual_style"]["reviews"][1]
    review.update(disposition="identity_layout_only", scope_text="图片1",
        reason="This historical reference is retained only for layout.")
    row["visual_style"].update(scope="mixed_reference_guidance",
        mixed_reference_reason="The auxiliary image is retained only for identity and layout.")

    report = visual_style_report(row, registry)

    assert report["coverage"] == "COMPLETE"
    assert report["exclusions"] == [{"asset_id": review["asset_id"], "role": review["role"],
        "owner_id": review["owner_id"], "scope_text": "图片1",
        "reason": "This historical reference is retained only for layout."}]
    assert report["style_application"] == "PARTIAL_REFERENCE_STYLE"
    assert "intent" not in report


def test_whole_shot_style_scope_rejects_any_layout_only_reference(tmp_path):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    row["visual_style"]["reviews"][1].update(
        disposition="identity_layout_only", scope_text="图片1", reason="Retained for layout."
    )

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert "whole_shot_style_incomplete" in report["issues"]
    assert report["style_application"] == "WHOLE_SHOT_STYLE_INCOMPLETE"


def test_mixed_reference_style_requires_an_explicit_reason(tmp_path):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    row["visual_style"]["scope"] = "mixed_reference_guidance"

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert "mixed_reference_reason_missing" in report["issues"]
    assert report["style_application"] == "PARTIAL_REFERENCE_STYLE"


def test_visible_character_without_selected_image_reference_fails(tmp_path):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, assets, _ = _canvas_inputs(tmp_path)
    _scene_only_style(row, assets)

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert report["target_owners"] == {
        "characters": 1, "required_visible_characters": 1, "scenes": 1,
    }
    assert "missing_character_reference" in report["issues"]


def test_reviewed_full_frame_can_cover_cast_and_scene_without_forcing_reference_route(tmp_path):
    from ai_video.canvas_visual_style import require_canvas_visual_style

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    row["generation"]["references"] = [{"role": "approved_keyframe",
        "asset_id": "robot-main", "owner_id": "one"}]
    review = row["visual_style"]["reviews"][0]
    review.update(role="approved_keyframe", owner_id="one", covered_owner_ids=["robot", "road"])
    row["visual_style"]["reviews"] = [review]

    report = require_canvas_visual_style(row, registry)

    assert report["coverage"] == "COMPLETE"
    assert report["aesthetic_acceptance"] == "NOT_EVALUATED"


def test_identity_image_cannot_claim_to_be_a_review_of_the_entire_cast(tmp_path):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    row["visual_style"]["reviews"][0]["covered_owner_ids"] = ["robot", "road"]

    assert visual_style_report(row, registry)["coverage"] == "INCOMPLETE"


def test_typed_offscreen_character_does_not_require_an_image_reference(tmp_path):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, assets, _ = _canvas_inputs(tmp_path)
    _scene_only_style(row, assets)
    _performance_direction(row, offscreen_reason="The speaker remains outside the frame.")

    report = visual_style_report(row, registry)

    assert report["coverage"] == "COMPLETE"
    assert report["target_owners"] == {
        "characters": 1, "required_visible_characters": 0, "scenes": 1,
    }


def test_untyped_or_invalid_offscreen_reason_does_not_exempt_character(tmp_path):
    from ai_video.canvas_visual_style import visual_style_report

    _, _, registry, row, assets, _ = _canvas_inputs(tmp_path)
    _scene_only_style(row, assets)
    _performance_direction(row, offscreen_reason=None)

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert report["target_owners"]["required_visible_characters"] == 1
    assert "missing_character_reference" in report["issues"]


@pytest.mark.parametrize("provider_family", ["seedance", "h3-max"])
def test_prepared_request_must_consume_every_reviewed_image(tmp_path, provider_family):
    from ai_video.canvas_visual_style import require_prepared_visual_style

    row, prepared = _prepared_style(tmp_path, provider_family=provider_family)

    assert prepared.execution_binding is not None
    assert require_prepared_visual_style(row, prepared) is None


@pytest.mark.parametrize("provider_family", ["seedance", "h3-max"])
def test_canonical_style_revision_prepares_and_blocks_bad_inputs_before_start(
    tmp_path, monkeypatch, provider_family
):
    from dataclasses import replace
    from types import SimpleNamespace
    from ai_video.errors import AiVideoError
    from test_canvas_source_expression import subject_service

    service, limits = subject_service(tmp_path, provider_family=provider_family,
        generation_output_duration_seconds=5)
    registry = service._load().registry
    _declare_style(service.direction["shots"][0], registry)
    service.revise_authoring(attempt_id="declare-current-style", registry=registry)
    prepared = service.prepare(limits=limits)
    assert prepared.execution_binding is not None
    assert {image.asset_id for image in prepared.resolved_request.image_bindings} == {
        "robot-main", "robot-aux", "room"}
    before = (service.committer.project_root / "state/manifest.json").read_bytes()
    request = prepared.resolved_request.model_copy(update={
        "image_bindings": prepared.resolved_request.image_bindings[:-1]})
    bad = replace(prepared, resolved_request=request)
    # Only inject a defective compiler result; authoring, current-state loading
    # and the pre-start barrier are the actual application path.
    monkeypatch.setattr(service, "_orchestrator", lambda row: SimpleNamespace(prepare=lambda **_: bad))
    with pytest.raises(AiVideoError, match="visual-style binding"):
        service.prepare(limits=limits)
    with pytest.raises(AiVideoError, match="visual-style binding"):
        service.start(limits=limits)
    assert (service.committer.project_root / "state/manifest.json").read_bytes() == before


@pytest.mark.parametrize("damage", ["missing", "substituted", "extra"])
def test_prepared_request_rejects_missing_substituted_or_extra_image_bindings(
    tmp_path, damage
):
    from dataclasses import replace
    from ai_video.canvas_visual_style import require_prepared_visual_style

    row, prepared = _prepared_style(tmp_path)
    images = prepared.resolved_request.image_bindings
    if damage == "missing":
        changed_images = images[:-1]
    elif damage == "substituted":
        changed_images = (images[0].model_copy(update={"asset_sha256": "f" * 64}), *images[1:])
    else:
        changed_images = (*images, images[0].model_copy(update={"asset_id": "unreviewed-image"}))
    changed_request = prepared.resolved_request.model_copy(update={"image_bindings": changed_images})
    changed_prepared = replace(prepared, resolved_request=changed_request)

    with pytest.raises(ValueError, match="Canvas visual-style binding does not match"):
        require_prepared_visual_style(row, changed_prepared)


def test_prepared_requirement_must_retain_exact_reviewed_identity_evidence(tmp_path):
    from dataclasses import replace
    from ai_video.canvas_visual_style import require_prepared_visual_style

    row, prepared = _prepared_style(tmp_path)
    binding = prepared.execution_binding
    requirement = binding.projection.requirement
    evidence = tuple(
        item.model_copy(update={"canonical_owner_id": "other-character"})
        if item.asset_id == "robot-main" else item
        for item in requirement.asset_evidence
    )
    projection = binding.projection.model_copy(update={
        "requirement": requirement.model_copy(update={"asset_evidence": evidence})
    })
    changed_binding = binding.model_copy(update={"projection": projection})

    with pytest.raises(ValueError, match="Canvas visual-style binding does not match"):
        require_prepared_visual_style(row, replace(prepared, execution_binding=changed_binding))


def test_prepared_request_must_include_declared_style_anchor(tmp_path):
    from dataclasses import replace
    from ai_video.canvas_visual_style import require_prepared_visual_style

    row, prepared = _prepared_style(tmp_path)
    anchor_id = row["visual_style"]["source"]["asset_id"]
    images = tuple(item for item in prepared.resolved_request.image_bindings
        if item.asset_id != anchor_id)
    changed_request = prepared.resolved_request.model_copy(update={"image_bindings": images})

    with pytest.raises(ValueError, match="Canvas visual-style binding does not match"):
        require_prepared_visual_style(row, replace(prepared, resolved_request=changed_request))


def test_prepared_prompt_must_contain_literal_identity_layout_scope(tmp_path):
    from dataclasses import replace
    from ai_video.canvas_visual_style import require_prepared_visual_style

    row, prepared = _prepared_style(tmp_path)
    review = row["visual_style"]["reviews"][1]
    review.update(disposition="identity_layout_only", scope_text="图片1",
        reason="Retained only for layout.")
    row["visual_style"].update(scope="mixed_reference_guidance",
        mixed_reference_reason="This auxiliary reference keeps identity and layout only.")
    changed_request = prepared.resolved_request.model_copy(update={
        "prompt_text": prepared.resolved_request.prompt_text.replace("图片1", "reference")
    })

    with pytest.raises(ValueError, match="Canvas visual-style binding does not match"):
        require_prepared_visual_style(row, replace(prepared, resolved_request=changed_request))


def test_prepared_style_check_is_a_noop_for_legacy_or_unsupported_binding():
    from ai_video.canvas_visual_style import require_prepared_visual_style

    assert require_prepared_visual_style({}, object()) is None


def test_unknown_declaration_fields_fail_safely_without_prompt_text(tmp_path):
    from ai_video.canvas_visual_style import require_canvas_visual_style, visual_style_report

    _, _, registry, row, _, _ = _canvas_inputs(tmp_path)
    row["shot"]["intent"] += " PRIVATE_PROMPT_FRAGMENT"
    row["visual_style"]["unrecognized"] = "PRIVATE_PROMPT_FRAGMENT"

    report = visual_style_report(row, registry)

    assert report["coverage"] == "INCOMPLETE"
    assert report["issues"] == ["invalid_declaration"]
    assert "PRIVATE_PROMPT_FRAGMENT" not in repr(report)
    with pytest.raises(ValueError, match="Canvas visual-style declaration is invalid or incomplete"):
        require_canvas_visual_style(row, registry)
