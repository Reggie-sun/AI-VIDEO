"""Per-cut review packets bind human editing decisions to resolved composition."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from ai_video.production.composition import resolve_composition
from ai_video.production.hashing import seal_artifact, verify_artifact_hash
from ai_video.production.models import ResolvedTimeline
from scripts.visual_quality_report import check, prepare, reopen, write_json
from test_creative_goal_binding import goal_inputs
from test_production_composition import _with_video_layer
from production_project_factory import make_composition_spec, make_loaded_project_and_spec, make_p4_composition_fixture
from test_visual_quality_report import complete_goal


TIMELINE_FIXTURE = Path(__file__).parent / "fixtures/hyperframes/silent_image/timeline.json"


def _make_video(path: Path, frames: int = 10, fps: int = 24) -> None:
    subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-f", "lavfi", "-i",
         f"color=c=orange:s=320x180:r={fps}", "-frames:v", str(frames),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)],
        check=True,
        capture_output=True,
    )


def _report(video: Path, timeline: ResolvedTimeline, *, fps: int | None = None, frames: int | None = None) -> dict:
    output_hash = hashlib.sha256(video.read_bytes()).hexdigest()
    rate = fps or timeline.delivery_profile.fps
    count = frames or timeline.total_frames
    return {
        "output": str(video.resolve()),
        "sha256": output_hash,
        "size_bytes": video.stat().st_size,
        "measured": {
            "width": timeline.delivery_profile.width,
            "height": timeline.delivery_profile.height,
            "fps_num": rate,
            "fps_den": 1,
            "duration_frames": count,
            "codec_name": "h264",
        },
        "timeline_fingerprint": timeline.composition_fingerprint,
        "timeline_frames": timeline.total_frames,
        "checks": [
            {"command": command, "tool_version": timeline.renderer.version,
             "exit_code": 0, "error_count": 0, "warning_count": 0}
            for command in ("lint", "check")
        ],
        "usage_scope": "development_audio_preview",
    }


@pytest.fixture
def v4_packet(tmp_path):
    video = tmp_path / "source.mp4"
    _make_video(video)
    timeline_bytes = TIMELINE_FIXTURE.read_bytes()
    timeline = ResolvedTimeline.model_validate_json(timeline_bytes)
    assert verify_artifact_hash(timeline)
    timeline_path = tmp_path / "timeline.json"
    timeline_path.write_bytes(timeline_bytes)
    report_path = tmp_path / "render-report.json"
    write_json(report_path, _report(video, timeline))

    authored, goal = complete_goal("advertising")
    goal = goal.model_copy(update={"requirements": (*goal.requirements[:-1],
        goal.requirements[-1].model_copy(update={"proof": "human"}))})
    binding, _, _, _ = goal_inputs(tmp_path / "authoring", kind="advertising", contract=goal)
    output = tmp_path / "review"
    result = prepare(
        video,
        authored,
        output,
        (0, 200),
        final_output_contract=goal,
        goal_binding=binding,
        timeline=timeline_path,
        render_report=report_path,
    )
    assert result["verdict"] == "not_evaluated"
    return output


def _answers(output: Path) -> Path:
    packet = json.loads((output / "packet.json").read_text(encoding="utf-8"))
    data = json.loads((output / "observations.template.json").read_text(encoding="utf-8"))
    data["evaluator_name"] = "Human full playback fixture"
    data["strength"] = "human"
    data["observation"]["viewing_mode"] = "full_playback"
    data["observation"]["viewing_speed_milli"] = 1000
    frame = {key: value for key, value in packet["frames"][0].items() if key != "path"}
    for finding in data["observation"]["findings"]:
        finding.update(
            verdict="pass",
            observation="Human reviewed the exact full-length output at normal speed.",
            visual_frames=[frame],
        )
    if packet["schema_version"] == "visual-review-packet/4":
        data["junction_findings"] = [
            {
                "junction_id": junction["junction_id"],
                "inventory_sha256": packet["junction_inventory_sha256"],
                "edit_decision": "retain_with_reason",
                "edit_reason": "动作在切点前收住，下一镜主体与视线自然接上。",
                "visual_verdict": "pass",
                "visual_observation": "正常速度播放时没有重复、停顿或跳帧。",
                "audio_verdict": "pass",
                "audio_observation": "该接点听起来没有重复音或突然截断。",
                "audio_basis": "actual_listening",
                "audio_reason": None,
                "viewing_mode": "full_playback",
                "viewing_speed_milli": 1000,
            }
            for junction in packet["junction_inventory"]
        ]
    path = output / "answers.json"
    write_json(path, data)
    return path


def test_full_contract_requires_timeline_and_render_report_before_media_effects(tmp_path, monkeypatch):
    authored, goal = complete_goal("advertising")

    def forbidden(*args, **kwargs):
        pytest.fail("Full-contract binding must be rejected before media probing or extraction")

    monkeypatch.setattr(subprocess, "run", forbidden)
    output = tmp_path / "review"
    with pytest.raises(ValueError, match="ResolvedTimeline and HyperFrames render report"):
        prepare(tmp_path / "missing.mp4", authored, output, (0,), final_output_contract=goal)
    assert not output.exists()


def test_inventory_uses_only_resolved_transitions_and_deduplicates_overlay_layers(tmp_path):
    from ai_video.production.junction_review import derive_junction_inventory

    loaded, spec = make_loaded_project_and_spec(tmp_path / "overlay-project")
    base = next(layer for layer in spec.layers if layer.shot_id == "shot-2")
    overlay = base.model_copy(update={"layer_id": "layer-shot-2-overlay", "z_index": 5, "opacity_milli": 600})
    spec = seal_artifact(spec.model_copy(update={"content_hash": "0" * 64, "layers": (*spec.layers, overlay)}))
    timeline = resolve_composition(loaded, spec, "0.7.103")
    inventory = derive_junction_inventory(timeline)

    assert len(inventory) == 1
    cut = inventory[0]
    assert (cut.from_shot_id, cut.to_shot_id, cut.frame) == ("shot-1", "shot-2", 48)
    assert {span.layer_id for span in cut.visual_spans if span.shot_id == "shot-2"} == {
        "layer-shot-2", "layer-shot-2-overlay"
    }
    assert all(len(span.asset_sha256) == 64 for span in cut.visual_spans)
    assert all(span.trim_start_frame >= 0 for span in cut.visual_spans)


def test_audio_inventory_captures_resolved_sample_placement_trim_and_fade(tmp_path):
    from ai_video.production.junction_review import derive_junction_inventory

    loaded, spec = make_p4_composition_fixture(tmp_path / "audio-project")
    timeline = resolve_composition(loaded, spec, "0.7.103")
    inventory = derive_junction_inventory(timeline)

    assert len(inventory) == 1
    assert inventory[0].audio_window_end_sample > inventory[0].audio_window_start_sample
    assert inventory[0].audio_spans
    assert all(len(span.asset_sha256) == 64 for span in inventory[0].audio_spans)
    assert all(span.source_duration_samples > 0 for span in inventory[0].audio_spans)
    assert all(span.fade_in_samples >= 0 and span.fade_out_samples >= 0 for span in inventory[0].audio_spans)


def test_v4_snapshots_exact_timeline_and_render_report_and_templates_every_cut(v4_packet):
    packet, contract = reopen(v4_packet)

    assert packet["schema_version"] == "visual-review-packet/4"
    timeline_path = v4_packet / packet["timeline_snapshot"]["path"]
    report_path = v4_packet / packet["render_report_snapshot"]["path"]
    assert hashlib.sha256(timeline_path.read_bytes()).hexdigest() == packet["timeline_snapshot"]["sha256"]
    assert hashlib.sha256(report_path.read_bytes()).hexdigest() == packet["render_report_snapshot"]["sha256"]
    assert packet["timeline_snapshot"]["content_hash"] == packet["timeline_snapshot"]["composition_fingerprint"] or len(packet["timeline_snapshot"]["content_hash"]) == 64
    assert packet["render_report_snapshot"]["timeline_fingerprint"] == packet["timeline_snapshot"]["composition_fingerprint"]
    template = json.loads((v4_packet / "observations.template.json").read_text(encoding="utf-8"))
    assert len(template["junction_findings"]) == len(packet["junction_inventory"]) == 1
    assert template["junction_findings"][0]["visual_verdict"] == "not_evaluated"
    assert template["junction_findings"][0]["audio_verdict"] == "not_evaluated"
    assert template["junction_findings"][0]["junction_id"] == packet["junction_inventory"][0]["junction_id"]
    assert contract.contract_hash


@pytest.mark.parametrize("mutation", ["duration", "frame_rate", "timeline", "failed_check"])
def test_prepare_rejects_stale_or_failed_render_report_before_media_probe(v4_packet, tmp_path, monkeypatch, mutation):
    from ai_video.production.final_output_contracts import FinalOutputContract

    packet = json.loads((v4_packet / "packet.json").read_text(encoding="utf-8"))
    report_path = tmp_path / "invalid-render-report.json"
    report = json.loads((v4_packet / packet["render_report_snapshot"]["path"]).read_text(encoding="utf-8"))
    if mutation == "duration":
        report["measured"]["duration_frames"] += 1
    elif mutation == "frame_rate":
        report["measured"]["fps_num"] = 12
    elif mutation == "timeline":
        report["timeline_fingerprint"] = "f" * 64
    else:
        report["checks"][0]["warning_count"] = 1
    write_json(report_path, report)

    def forbidden(*args, **kwargs):
        pytest.fail("A stale or failed render report must be rejected before ffprobe/ffmpeg")

    monkeypatch.setattr(subprocess, "run", forbidden)
    authored, goal = complete_goal("advertising")
    goal = goal.model_copy(update={"requirements": (*goal.requirements[:-1],
        goal.requirements[-1].model_copy(update={"proof": "human"}))})
    output = tmp_path / "rejected-review"
    with pytest.raises(ValueError, match="HyperFrames"):
        prepare(
            Path(packet["video_path"]), authored, output, (0, 200),
            final_output_contract=FinalOutputContract.model_validate(packet["contract"]),
            timeline=v4_packet / packet["timeline_snapshot"]["path"],
            render_report=report_path,
        )
    assert not output.exists()


def test_retain_with_reason_can_pass_but_trim_recommendation_cannot(v4_packet):
    answers = _answers(v4_packet)
    assert check(v4_packet, answers)["verdict"] == "pass"

    data = json.loads(answers.read_text(encoding="utf-8"))
    data["junction_findings"][0]["edit_decision"] = "trim"
    data["junction_findings"][0]["edit_reason"] = "切点前保留了多余停顿。"
    write_json(answers, data)
    result = check(v4_packet, answers)
    assert result["verdict"] == "fail"
    assert result["junction_review"]["cuts"][0]["verdict"] == "fail"


@pytest.mark.parametrize(
    "mutation",
    ["not_listened", "sampled_frames", "wrong_speed", "model_audio_claim", "missing_cut"],
)
def test_cut_review_without_exact_normal_speed_human_audio_evidence_stays_not_evaluated(v4_packet, mutation):
    answers = _answers(v4_packet)
    data = json.loads(answers.read_text(encoding="utf-8"))
    if mutation == "not_listened":
        data["junction_findings"][0]["audio_basis"] = "not_listened"
    elif mutation == "sampled_frames":
        data["junction_findings"][0]["viewing_mode"] = "sampled_frames"
    elif mutation == "wrong_speed":
        data["junction_findings"][0]["viewing_speed_milli"] = 2000
    elif mutation == "model_audio_claim":
        data["strength"] = "explicit_evaluator"
    else:
        data["junction_findings"].clear()
    write_json(answers, data)

    result = check(v4_packet, answers)
    assert result["verdict"] == "not_evaluated"
    assert result["junction_review"]["verdict"] == "not_evaluated"


@pytest.mark.parametrize("mutation", ["duplicate", "unknown", "stale_inventory"])
def test_invalid_junction_ids_or_inventory_binding_never_pass(v4_packet, mutation):
    answers = _answers(v4_packet)
    data = json.loads(answers.read_text(encoding="utf-8"))
    if mutation == "duplicate":
        data["junction_findings"].append(data["junction_findings"][0])
    elif mutation == "unknown":
        data["junction_findings"][0]["junction_id"] = "f" * 64
    else:
        data["junction_findings"][0]["inventory_sha256"] = "f" * 64
    write_json(answers, data)

    if mutation == "stale_inventory":
        result = check(v4_packet, answers)
        assert result["verdict"] == "not_evaluated"
    else:
        with pytest.raises(ValueError):
            check(v4_packet, answers)
        assert not (v4_packet / "result.json").exists()


@pytest.mark.parametrize("tamper", ["timeline", "render_report", "video"])
def test_v4_reopen_rechecks_exact_snapshot_and_video_bindings(v4_packet, tamper):
    packet = json.loads((v4_packet / "packet.json").read_text(encoding="utf-8"))
    if tamper == "timeline":
        target = v4_packet / packet["timeline_snapshot"]["path"]
        target.write_bytes(target.read_bytes() + b" ")
    elif tamper == "render_report":
        target = v4_packet / packet["render_report_snapshot"]["path"]
        target.write_bytes(target.read_bytes() + b" ")
    else:
        target = Path(packet["video_path"])
        with target.open("ab") as stream:
            stream.write(b"changed")
    with pytest.raises(ValueError):
        reopen(v4_packet)


def test_single_clip_v4_packet_has_a_valid_empty_cut_inventory(tmp_path):
    from ai_video.production.junction_review import derive_junction_inventory

    loaded, _ = make_loaded_project_and_spec(tmp_path / "single-project")
    spec = make_composition_spec(shot_ids=("shot-1",))
    timeline = resolve_composition(loaded, spec, "0.7.103")
    assert verify_artifact_hash(timeline)
    assert derive_junction_inventory(timeline) == ()
    timeline_path = tmp_path / "single-timeline.json"
    timeline_path.write_text(timeline.model_dump_json(indent=2), encoding="utf-8")
    video = tmp_path / "single-source.mp4"
    fps = timeline.delivery_profile.fps
    subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-f", "lavfi", "-i",
         f"color=c=orange:s={timeline.delivery_profile.width}x{timeline.delivery_profile.height}:r={fps}",
         "-frames:v", str(timeline.total_frames), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)],
        check=True,
        capture_output=True,
    )
    report_path = tmp_path / "single-render-report.json"
    write_json(report_path, _report(video, timeline))
    authored, goal = complete_goal("advertising")
    output = tmp_path / "single-review"
    prepare(video, authored, output, (0,), final_output_contract=goal,
        timeline=timeline_path, render_report=report_path)

    packet = json.loads((output / "packet.json").read_text(encoding="utf-8"))
    template = json.loads((output / "observations.template.json").read_text(encoding="utf-8"))
    assert packet["schema_version"] == "visual-review-packet/4"
    assert packet["junction_inventory"] == []
    assert template["junction_findings"] == []


def test_implicit_cuts_are_reviewed_even_when_composition_omits_transition_labels(tmp_path):
    from ai_video.production.junction_review import derive_junction_inventory

    loaded, spec = make_loaded_project_and_spec(tmp_path / "implicit-project")
    spec = seal_artifact(spec.model_copy(update={"transitions": ()}))
    timeline = resolve_composition(loaded, spec, "0.7.103")
    assert all(span.incoming_transition is None for span in timeline.visual_spans)
    inventory = derive_junction_inventory(timeline)
    assert len(inventory) == 1
    assert (inventory[0].from_shot_id, inventory[0].to_shot_id) == ("shot-1", "shot-2")
    destination = next(span for span in timeline.visual_spans if span.shot_id == "shot-2")
    assert inventory[0].frame == destination.start_frame
    assert inventory[0].sample == destination.start_sample


@pytest.mark.parametrize("mutation", ["evaluator", "wrong_speed", "not_listened"])
def test_observed_audio_failure_is_preserved_even_without_pass_eligibility(v4_packet, mutation):
    answers = _answers(v4_packet)
    data = json.loads(answers.read_text())
    cut = data["junction_findings"][0]
    cut.update(audio_verdict="fail", audio_observation="接点可听到对白重复，需剪辑修复。")
    if mutation == "evaluator":
        data["strength"] = "explicit_evaluator"
    elif mutation == "wrong_speed":
        cut["viewing_speed_milli"] = 2000
    else:
        cut["audio_basis"] = "not_listened"
    write_json(answers, data)
    result = check(v4_packet, answers)
    assert result["verdict"] == "fail"
    assert result["junction_review"]["cuts"][0]["audio_verdict"] == "fail"
    assert result["completion_summary"]["junctions_to_address"][0]["next_action"] == "repair"
