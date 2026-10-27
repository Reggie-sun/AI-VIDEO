"""Assembly evidence checks reuse resolved cuts; fixtures never prove media quality."""

import copy
import json
from pathlib import Path

import pytest

from ai_video.production.composition import resolve_composition
from production_project_factory import make_loaded_project_and_spec
from scripts import agent_harness
from scripts.agent_harness_assembly import prepare_assembly, verify_assembly
from test_junction_review_gate import _make_video, _report


@pytest.fixture
def assembly(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path / "project")
    timeline = resolve_composition(loaded, spec, "0.7.103")
    video = tmp_path / "output.mp4"
    # Decoder/visual quality is outside this read-only evidence check.
    _make_video(video, frames=timeline.total_frames)
    timeline_path = tmp_path / "timeline.json"
    timeline_path.write_text(timeline.model_dump_json())
    report = _report(video, timeline)
    report.pop("timeline_frames")  # Real native-join exports use measured.duration_frames.
    report_path = tmp_path / "render-report.json"
    report_path.write_text(json.dumps(report))
    return dict(video=video, timeline=timeline_path, render_report=report_path)


def answers(assembly, tmp_path):
    data = prepare_assembly(**assembly)
    data["evaluator_name"] = "Human playback test fixture, not an actual acceptance"
    data["strength"] = "human"
    for finding in data["junction_findings"]:
        finding.update(edit_decision="retain_with_reason", edit_reason="完整动作只发生一次",
            visual_verdict="pass", visual_observation="接点正常",
            audio_verdict="pass", audio_observation="没有重复或截断", audio_basis="actual_listening",
            viewing_mode="full_playback", viewing_speed_milli=1000)
        for value in finding["action_review"].values():
            value.update(verdict="pass", observation="正常速度核对此项，未见问题")
        finding["editing_intent"] = editing_intent()
        for value in finding["editing_review"].values():
            value.update(verdict="pass", observation="显式离线夹具，非真实媒体验收")
    path = tmp_path / "answers.json"
    path.write_text(json.dumps(data))
    return path, data


def test_missing_answers_and_unreviewed_template_cannot_pass(assembly, tmp_path):
    assert verify_assembly(**assembly)["verdict"] == "not_evaluated"
    template = prepare_assembly(**assembly)
    assert len(template["junction_findings"]) == 1
    cut = template["junction_findings"][0]
    assert set(cut["action_review"]) == {"repetition", "state_continuity", "pacing"}
    path = tmp_path / "template.json"
    path.write_text(json.dumps(template))
    result = verify_assembly(**assembly, answers=path)
    assert result["verdict"] == "not_evaluated"
    assert result["production_acceptance"] == "NOT_EVALUATED"


def test_complete_per_cut_evidence_can_verify_without_product_acceptance(assembly, tmp_path):
    path, _ = answers(assembly, tmp_path)
    result = verify_assembly(**assembly, answers=path)
    assert result["verdict"] == "pass"
    assert result["authority"] == "development_only"
    assert result["production_acceptance"] == "NOT_EVALUATED"


@pytest.mark.parametrize("mutation", ["missing_cut", "missing_actions", "missing_repetition",
    "sampled_frames", "wrong_speed", "not_listened", "machine_claim"])
def test_incomplete_or_ineligible_observation_stays_unverified(assembly, tmp_path, mutation):
    path, data = answers(assembly, tmp_path)
    cut = data["junction_findings"][0]
    if mutation == "missing_cut": data["junction_findings"] = []
    elif mutation == "missing_actions": cut.pop("action_review")
    elif mutation == "missing_repetition": cut["action_review"]["repetition"]["verdict"] = "not_evaluated"
    elif mutation == "sampled_frames": cut["viewing_mode"] = "sampled_frames"
    elif mutation == "wrong_speed": cut["viewing_speed_milli"] = 2000
    elif mutation == "not_listened": cut["audio_basis"] = "not_listened"
    else: data["strength"] = "explicit_evaluator"
    path.write_text(json.dumps(data))
    assert verify_assembly(**assembly, answers=path)["verdict"] == "not_evaluated"


@pytest.mark.parametrize("criterion", ["repetition", "state_continuity", "pacing"])
def test_explicit_action_failure_blocks_even_when_other_evidence_is_missing(assembly, tmp_path, criterion):
    path, data = answers(assembly, tmp_path)
    cut = data["junction_findings"][0]
    cut["action_review"][criterion].update(verdict="fail", observation="前后镜重复扫瓶，需要修剪")
    cut["audio_basis"] = "not_listened"
    data["strength"] = "explicit_evaluator"
    path.write_text(json.dumps(data))
    result = verify_assembly(**assembly, answers=path)
    assert result["verdict"] == "fail"
    assert f"action_{criterion}_failed" in result["junction_review"]["evidence_gaps"]


@pytest.mark.parametrize("changed", ["video", "timeline", "render_report"])
def test_changed_input_invalidates_previous_answers(assembly, tmp_path, changed):
    path, _ = answers(assembly, tmp_path)
    assembly[changed].write_bytes(assembly[changed].read_bytes() + b" ")
    with pytest.raises(ValueError):
        verify_assembly(**assembly, answers=path)


@pytest.mark.parametrize("mutation", ["wrong_sha", "wrong_inventory", "duplicate_cut", "unknown_cut"])
def test_conflicting_identity_or_cut_inventory_never_passes(assembly, tmp_path, mutation):
    path, data = answers(assembly, tmp_path)
    if mutation == "wrong_sha": data["video_sha256"] = "a" * 64
    elif mutation == "wrong_inventory": data["inventory_sha256"] = "b" * 64
    elif mutation == "duplicate_cut": data["junction_findings"].append(copy.deepcopy(data["junction_findings"][0]))
    else: data["junction_findings"][0]["junction_id"] = "c" * 64
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        verify_assembly(**assembly, answers=path)


def test_render_report_explicit_frame_conflict_still_rejected(assembly):
    data = json.loads(assembly["render_report"].read_text())
    data["timeline_frames"] = data["measured"]["duration_frames"] + 1
    assembly["render_report"].write_text(json.dumps(data))
    with pytest.raises(ValueError): prepare_assembly(**assembly)


def test_cli_is_fail_closed_and_does_not_load_engineering_policy(assembly, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(agent_harness, "load_policy", lambda: pytest.fail("Not engineering scope"))
    flags = [flag for name, value in assembly.items() for flag in ("--" + name.replace("_", "-"), str(value))]
    target = tmp_path / "template.json"
    assert agent_harness.main(["prepare-assembly-review", *flags, "--output", str(target)]) == 0
    assert json.loads(capsys.readouterr().out)["verdict"] == "not_evaluated"
    assert agent_harness.main(["verify-assembly", *flags]) == 1
    capsys.readouterr()
    assert agent_harness.main(["verify-assembly", *flags, "--answers", str(target)]) == 1
    capsys.readouterr()
    path, _ = answers(assembly, tmp_path)
    assert agent_harness.main(["verify-assembly", *flags, "--answers", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["production_acceptance"] == "NOT_EVALUATED"
    target.write_text("PRIVATE_INVALID_PAYLOAD")
    assert agent_harness.main(["verify-assembly", *flags, "--answers", str(target)]) == 2
    assert "PRIVATE_INVALID_PAYLOAD" not in capsys.readouterr().out


def test_template_creation_never_overwrites_existing_files(assembly, tmp_path, capsys):
    flags = [flag for name, value in assembly.items() for flag in ("--" + name.replace("_", "-"), str(value))]
    original = assembly["video"].read_bytes()
    assert agent_harness.main(["prepare-assembly-review", *flags, "--output", str(assembly["video"])]) == 2
    assert assembly["video"].read_bytes() == original


def test_answer_changed_during_verification_is_rejected(assembly, tmp_path, monkeypatch):
    from scripts import agent_harness_assembly as owner

    path, _ = answers(assembly, tmp_path)
    evaluate = owner.evaluate_junction_review

    def changed(*args, **kwargs):
        result = evaluate(*args, **kwargs)
        path.write_bytes(path.read_bytes() + b" ")
        return result

    monkeypatch.setattr(owner, "evaluate_junction_review", changed)
    with pytest.raises(ValueError, match="observations changed"):
        owner.verify_assembly(**assembly, answers=path)


def test_success_binds_exact_answer_bytes_and_evaluator(assembly, tmp_path):
    import hashlib

    path, data = answers(assembly, tmp_path)
    result = verify_assembly(**assembly, answers=path)
    assert result["answers_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert result["evaluator_name"] == data["evaluator_name"]
    assert result["strength"] == "human"


def editing_intent():
    return dict(narrative_type="drama", technique="cut_on_action",
        reason="切到接收者确认交接", expected_effect="观众理解支撑已转移",
        outgoing_phase="原持有者松手", incoming_phase="接收者承重后收手",
        axis_eyeline_space="保持柜台两侧和对视关系，不能只比较脸朝向",
        scale_reaction="中景到手部近景，保留接收者确认反应",
        rhythm_reveal="动作完成后留出理解时间，不按固定秒数切镜",
        continuity_risks=["可能重复交接"], audio_treatment="sync",
        audio_reason="保留完整原句和环境声", audio_track_ids=[], pickup_requirement=None)


def test_new_template_exposes_source_in_out_and_missing_intent_cannot_pass(assembly, tmp_path):
    template = prepare_assembly(**assembly)
    assert template["schema_version"] == "assembly-review/2"
    assert template["junction_findings"][0]["source_selection"] is not None
    path, data = answers(assembly, tmp_path)
    data["junction_findings"][0]["editing_intent"] = None
    path.write_text(json.dumps(data))
    result = verify_assembly(**assembly, answers=path)
    assert result["verdict"] == "not_evaluated"
    assert "missing_editing_intent" in result["junction_review"]["evidence_gaps"]


@pytest.mark.parametrize("mutation", ["source_out", "source_in", "source_sha", "audio_bridge", "pickup", "axis_fail"])
def test_editing_intent_is_bound_to_real_sources_audio_and_findings(assembly, tmp_path, mutation):
    path, data = answers(assembly, tmp_path)
    cut = data["junction_findings"][0]
    if mutation == "source_out": cut["source_selection"]["source_out_frame_exclusive"] += 1
    elif mutation == "source_in": cut["source_selection"]["source_in_frame"] += 1
    elif mutation == "source_sha": cut["source_selection"]["outgoing"]["asset_sha256"] = "f" * 64
    elif mutation == "audio_bridge":
        cut["editing_intent"].update(audio_treatment="j_cut", audio_track_ids=["nonexistent"])
    elif mutation == "pickup": cut["editing_intent"]["pickup_requirement"] = "缺少松手到承重衔接镜，须回Director"
    else: cut["editing_review"]["axis_eyeline_space"]["verdict"] = "fail"
    path.write_text(json.dumps(data))
    result = verify_assembly(**assembly, answers=path)
    assert result["verdict"] == "fail"


@pytest.mark.parametrize("mutation", ["missing_review", "unevaluated_axis", "missing_sources", "legacy_version"])
def test_new_editing_requirements_cannot_be_waived_by_old_or_incomplete_answers(assembly, tmp_path, mutation):
    path, data = answers(assembly, tmp_path)
    cut = data["junction_findings"][0]
    if mutation == "missing_review": cut.pop("editing_review")
    elif mutation == "unevaluated_axis": cut["editing_review"]["axis_eyeline_space"]["verdict"] = "not_evaluated"
    elif mutation == "missing_sources": cut.pop("source_selection")
    else:
        data["schema_version"] = "assembly-review/1"
        for key in ("editing_review", "editing_intent", "source_selection"): cut.pop(key)
    path.write_text(json.dumps(data))
    assert verify_assembly(**assembly, answers=path)["verdict"] == "not_evaluated"


def test_real_resolved_crossing_audio_is_necessary_but_not_semantic_proof(assembly, tmp_path):
    from ai_video.production.junction_review import derive_junction_inventory
    from ai_video.production.models import ResolvedTimeline
    from production_project_factory import make_p4_composition_fixture
    loaded, spec = make_p4_composition_fixture(tmp_path / "with-audio")
    timeline = resolve_composition(loaded, spec, "0.7.103")
    _make_video(tmp_path / "with-audio.mp4", frames=timeline.total_frames)
    assembly["video"] = tmp_path / "with-audio.mp4"
    assembly["timeline"].write_text(timeline.model_dump_json())
    assembly["render_report"].write_text(json.dumps(_report(assembly["video"], timeline)))
    timeline = ResolvedTimeline.model_validate_json(assembly["timeline"].read_bytes())
    cut = derive_junction_inventory(timeline)[0]
    crossing = [s.track_id for s in cut.audio_spans if s.start_sample < cut.sample < s.start_sample + s.duration_samples]
    assert crossing, "standard Composition fixture must provide the global music crossing"
    path, data = answers(assembly, tmp_path)
    finding = data["junction_findings"][0]
    finding["editing_intent"].update(audio_treatment="sound_bridge", audio_track_ids=crossing)
    path.write_text(json.dumps(data))
    assert verify_assembly(**assembly, answers=path)["verdict"] == "pass"
    finding["editing_review"]["sound_bridge"]["verdict"] = "not_evaluated"
    path.write_text(json.dumps(data))
    assert verify_assembly(**assembly, answers=path)["verdict"] == "not_evaluated"
