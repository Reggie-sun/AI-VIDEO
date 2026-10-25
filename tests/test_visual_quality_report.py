"""Actual extraction, report rendering, and exact-media tamper regressions."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts.visual_quality_report import check, prepare, write_json
from test_production_visual_quality import direction


TIMELINE_FIXTURE = Path(__file__).parent / "fixtures/hyperframes/silent_image/timeline.json"


def full_contract_media(tmp_path):
    """Use the existing canonical two-image CUT timeline for contract packets."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    video = tmp_path / "full-contract-source.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-f", "lavfi", "-i",
        "color=c=orange:s=320x180:r=24", "-frames:v", "10", "-c:v", "libx264",
        "-pix_fmt", "yuv420p", str(video)], check=True, capture_output=True)
    timeline = json.loads(TIMELINE_FIXTURE.read_text(encoding="utf-8"))
    report_path = tmp_path / "render-report.json"
    write_json(report_path, {
        "output": str(video.resolve()),
        "sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
        "size_bytes": video.stat().st_size,
        "measured": {
            "width": timeline["delivery_profile"]["width"],
            "height": timeline["delivery_profile"]["height"],
            "fps_num": timeline["delivery_profile"]["fps"],
            "fps_den": 1,
            "duration_frames": timeline["total_frames"],
            "codec_name": "h264",
        },
        "timeline_fingerprint": timeline["composition_fingerprint"],
        "timeline_frames": timeline["total_frames"],
        "checks": [
            {"command": command, "tool_version": timeline["renderer"]["version"],
             "exit_code": 0, "error_count": 0, "warning_count": 0}
            for command in ("lint", "check")
        ],
        "usage_scope": "development_audio_preview",
    })
    return video, TIMELINE_FIXTURE, report_path


@pytest.fixture
def packet(tmp_path):
    video = tmp_path / "source.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-f", "lavfi", "-i",
        "color=c=orange:s=96x160:r=2:d=2", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)],
        check=True, capture_output=True)
    output = tmp_path / "review"
    result = prepare(video, direction(), output, (0, 1000))
    assert result["verdict"] == "not_evaluated"
    return output


def answers(output, verdict="pass"):
    packet = json.loads((output / "packet.json").read_text())
    data = json.loads((output / "observations.template.json").read_text())
    data["evaluator_name"] = "Offline declared human fixture"
    data["strength"] = "human"
    data["observation"]["viewing_mode"] = "full_playback"
    data["observation"]["viewing_speed_milli"] = 1000
    frame = {k: v for k, v in packet["frames"][0].items() if k != "path"}
    for finding in data["observation"]["findings"]:
        finding.update(verdict=verdict, observation="Explicit fixture answer", visual_frames=[frame])
    if packet["schema_version"] == "visual-review-packet/4":
        data["junction_findings"] = [
            {
                "junction_id": junction["junction_id"],
                "inventory_sha256": packet["junction_inventory_sha256"],
                "edit_decision": "retain_with_reason",
                "edit_reason": "动作在切点前收住，下一镜主体自然接上。",
                "visual_verdict": "pass",
                "visual_observation": "正常速度播放时没有重复、停顿或跳帧。",
                "audio_verdict": "pass",
                "audio_observation": "实际聆听时没有重复音或突然截断。",
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


def test_report_uses_existing_gate_and_never_claims_production_acceptance(packet):
    result = check(packet, answers(packet))
    assert result["verdict"] == "pass"
    assert result["production_acceptance"] == "not_evaluated"
    html = (packet / "report.html").read_text()
    assert "字体与阅读" in html and "frames/00001000.jpg" in html
    assert "MP4 SHA-256" in html


@pytest.mark.parametrize("mutation", ["video", "frame", "answer_frame", "packet", "unknown", "duplicate", "inventory_duration", "inventory_frames"])
def test_tamper_removes_stale_pass_and_fails_closed(packet, mutation):
    path = answers(packet)
    check(packet, path)
    manifest = json.loads((packet / "packet.json").read_text())
    data = json.loads(path.read_text())
    if mutation == "video":
        with Path(manifest["video_path"]).open("ab") as stream:
            stream.write(b"changed")
    elif mutation == "frame":
        (packet / manifest["frames"][0]["path"]).write_bytes(b"substituted screenshot")
    elif mutation == "packet":
        manifest["contract"]["goal_version"] = "new"
        write_json(packet / "packet.json", manifest)
    elif mutation == "answer_frame":
        data["observation"]["findings"][0]["visual_frames"][0]["frame_sha256"] = "a" * 64
    elif mutation == "unknown":
        data["observation"]["findings"][0]["requirement_id"] = "unknown"
    elif mutation == "inventory_duration":
        data["observation"]["visual_frame_inventory"]["duration_ms"] += 1
    elif mutation == "inventory_frames":
        data["observation"]["visual_frame_inventory"]["frames"].pop()
    else:
        data["observation"]["findings"].append(data["observation"]["findings"][0])
    write_json(path, data)
    with pytest.raises(ValueError):
        check(packet, path)
    assert not (packet / "result.json").exists()
    assert not (packet / "report.html").exists()


def test_sampled_agent_answers_do_not_manufacture_holistic_pass(packet):
    path = answers(packet)
    data = json.loads(path.read_text())
    data["strength"] = "explicit_evaluator"
    data["observation"]["viewing_mode"] = "sampled_frames"
    data["observation"]["viewing_speed_milli"] = None
    write_json(path, data)
    assert check(packet, path)["verdict"] == "not_evaluated"
    data["observation"]["findings"][0]["verdict"] = "fail"
    data["observation"]["findings"][0]["observation"] = "<script>alert(1)</script>"
    write_json(path, data)
    assert check(packet, path)["verdict"] == "fail"
    assert "<script>" not in (packet / "report.html").read_text()


def test_new_cli_requires_explicit_matching_genre_before_media_effects(tmp_path, capsys):
    from scripts.visual_quality_report import main
    config = tmp_path / "direction.json"
    output = tmp_path / "out"
    args = ["prepare", "--video", str(tmp_path / "missing.mp4"), "--direction", str(config),
        "--output", str(output), "--timestamps-ms", "0"]
    write_json(config, {**direction().model_dump(), "content_kind": "advertising"})
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2
    assert main(args + ["--content-kind", "drama"]) == 2
    assert "Explicit content kind must match" in capsys.readouterr().out
    assert not output.exists()
    write_json(config, direction().model_dump())
    assert main(args + ["--content-kind", "advertising"]) == 2
    assert not output.exists()


def test_genre_packet_labels_and_cross_genre_answers(packet, tmp_path):
    from ai_video.production.visual_quality import VisualDirection
    original = json.loads((packet / "packet.json").read_text())
    outputs = []
    for kind in ("advertising", "drama"):
        output = tmp_path / kind
        authored = VisualDirection.model_validate({**direction().model_dump(), "content_kind": kind})
        prepare(Path(original["video_path"]), authored, output, (0, 1000))
        assert json.loads((output / "packet.json").read_text())["content_kind"] == kind
        assert ("电视剧" if kind == "drama" else "广告") in (output / "report.html").read_text()
        outputs.append(output)
    with pytest.raises(ValueError):
        check(outputs[1], answers(outputs[0]))


def test_matching_genre_cli_creates_bound_packet_and_rejects_removed_label(packet, tmp_path):
    from scripts.visual_quality_report import main, reopen
    from ai_video.production.hashing import canonical_sha256
    source = json.loads((packet / "packet.json").read_text())["video_path"]
    config = tmp_path / "ad.json"
    write_json(config, {**direction().model_dump(), "content_kind": "advertising"})
    output = tmp_path / "ad"
    assert main(["prepare", "--video", source, "--direction", str(config), "--content-kind",
        "advertising", "--output", str(output), "--timestamps-ms", "0", "1000"]) == 0
    saved = json.loads((output / "packet.json").read_text())
    assert saved["content_kind"] == "advertising"
    del saved["content_kind"]
    saved["subject_hash"] = canonical_sha256({k: v for k, v in saved.items() if k != "subject_hash"})
    write_json(output / "packet.json", saved)
    with pytest.raises(ValueError, match="Content kind differs"):
        reopen(output)


def complete_goal(kind):
    from ai_video.production.final_output_contracts import FinalOutputContract, FinalOutputRequirement
    from ai_video.production.visual_quality import VisualDirection, visual_requirements

    authored = VisualDirection.model_validate({**direction().model_dump(), "content_kind": kind})
    extra = FinalOutputRequirement(
        requirement_id="product.identity" if kind == "advertising" else "scene.result",
        observable="商品包装文字与真实参考一致" if kind == "advertising" else "观众能看见人物发现信件后改变行动",
        proof="evaluator",
    )
    goal = FinalOutputContract(goal_id="authored-film", goal_version="3",
        user_goal="保留原始完整目标 <不要缩成视觉测试>",
        requirements=(*visual_requirements(authored), extra))
    return authored, goal


@pytest.mark.parametrize("kind", ["advertising", "drama"])
@pytest.mark.parametrize("extra_verdict,expected", [("pass", "pass"), ("fail", "fail"), (None, "not_evaluated")])
def test_complete_goal_cannot_be_replaced_by_visual_pass(packet, tmp_path, kind, extra_verdict, expected):
    from scripts.visual_quality_report import reopen

    authored, goal = complete_goal(kind)
    source, timeline, report = full_contract_media(tmp_path / "complete-inputs")
    output = tmp_path / "complete"
    result = prepare(source, authored, output, (0, 200), final_output_contract=goal,
        timeline=timeline, render_report=report)
    assert result["verdict"] == "not_evaluated"
    assert result["review_scope"] == "full_contract"
    saved, reopened = reopen(output)
    assert saved["schema_version"] == "visual-review-packet/4"
    assert reopened == goal
    assert reopened.contract_hash == goal.contract_hash
    path = answers(output)
    data = json.loads(path.read_text())
    if extra_verdict is None:
        data["observation"]["findings"].pop()
    else:
        data["observation"]["findings"][-1].update(verdict=extra_verdict, observation="Observed <script>defect</script>")
    write_json(path, data)
    checked = check(output, path)
    assert checked["verdict"] == expected
    assert checked["production_acceptance"] == "not_evaluated"
    html = (output / "report.html").read_text()
    assert goal.requirements[-1].requirement_id in html
    assert goal.requirements[-1].observable in html
    assert "保留原始完整目标 &lt;不要缩成视觉测试&gt;" in html
    assert "<script>" not in html


@pytest.mark.parametrize("mutation", ["genre", "visual_text"])
def test_complete_goal_mismatch_rejected_before_media_effects(tmp_path, monkeypatch, mutation):
    authored, goal = complete_goal("advertising")
    if mutation == "genre":
        _, goal = complete_goal("drama")
    else:
        changed = goal.requirements[0].model_copy(update={"observable": "Silently weakened visual requirement"})
        goal = goal.model_copy(update={"requirements": (changed, *goal.requirements[1:])})

    def forbidden(*args, **kwargs):
        pytest.fail("No media probe or extraction before contract validation")

    monkeypatch.setattr(subprocess, "run", forbidden)
    output = tmp_path / "review"
    with pytest.raises(ValueError, match="visual requirements"):
        prepare(tmp_path / "missing.mp4", authored, output, (0,), final_output_contract=goal)
    assert not output.exists()


def test_complete_contract_cli_and_visual_only_scope(packet, tmp_path):
    from scripts.visual_quality_report import main

    authored, goal = complete_goal("drama")
    config, contract = tmp_path / "direction.json", tmp_path / "goal.json"
    write_json(config, authored.model_dump(mode="json"))
    write_json(contract, goal.model_dump(mode="json"))
    source, timeline, report = full_contract_media(tmp_path / "complete-inputs")
    output = tmp_path / "complete"
    assert main(["prepare", "--video", str(source), "--direction", str(config),
        "--content-kind", "drama", "--contract", str(contract), "--output", str(output),
        "--timeline", str(timeline), "--render-report", str(report),
        "--timestamps-ms", "0", "200"]) == 0
    result = json.loads((output / "result.json").read_text())
    assert result["review_scope"] == "full_contract"
    assert result["verdict"] == "not_evaluated"
    assert check(packet, answers(packet))["review_scope"] == "visual_only"


@pytest.fixture
def bound_packet(packet, tmp_path):
    from test_creative_goal_binding import goal_inputs
    from scripts.visual_quality_report import reopen

    authored, goal = complete_goal("drama")
    goal = goal.model_copy(update={"requirements": (*goal.requirements[:-1],
        goal.requirements[-1].model_copy(update={"proof": "human"}))})
    binding, _, _, _ = goal_inputs(tmp_path / "authoring", kind="drama", contract=goal)
    output = tmp_path / "bound-review"
    source, timeline, report = full_contract_media(tmp_path / "complete-inputs")
    prepare(source, authored, output, (0, 200), final_output_contract=goal,
        goal_binding=binding, timeline=timeline, render_report=report)
    return output, binding, goal


def test_goal_binding_python_roundtrip_reopens_only_sealed_inputs(bound_packet):
    from scripts.visual_quality_report import reopen
    output, binding, goal = bound_packet
    packet, reopened = reopen(output)
    assert packet["schema_version"] == "visual-review-packet/4"
    assert reopened == goal
    assert packet["goal_binding"]["path"] == "creative/binding.json"
    for source in binding.parent.iterdir():
        assert (output / "creative" / source.name).read_bytes() == source.read_bytes()
    binding.parent.rename(binding.parent.with_name("moved-original-inputs"))
    assert reopen(output)[1] == goal
    checked = check(output, answers(output))
    assert checked["verdict"] == "pass"
    assert checked["goal_chain"] == "verified"
    assert checked["completion_summary"]["requirements_to_address"] == []
    assert checked["completion_summary"]["user_feedback"]["assessment"] == "parent_review_required"
    assert checked["production_acceptance"] == "not_evaluated"


@pytest.mark.parametrize("version", ["visual-review-packet/2", "visual-review-packet/3"])
def test_legacy_full_contract_packets_reopen_but_need_new_junction_binding(bound_packet, tmp_path, version):
    from ai_video.production.hashing import canonical_sha256
    from scripts.visual_quality_report import reopen

    current, _, _ = bound_packet
    legacy = tmp_path / version.rsplit("/", 1)[1]
    shutil.copytree(current, legacy)
    packet_path = legacy / "packet.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet["schema_version"] = version
    for field in ("timeline_snapshot", "render_report_snapshot", "junction_inventory", "junction_inventory_sha256"):
        packet.pop(field, None)
    if version.endswith("/2"):
        packet.pop("goal_binding", None)
    packet["subject_hash"] = canonical_sha256({key: value for key, value in packet.items() if key != "subject_hash"})
    write_json(packet_path, packet)

    assert reopen(legacy)[0]["schema_version"] == version
    answer_path = answers(legacy)
    data = json.loads(answer_path.read_text(encoding="utf-8"))
    data["observation"]["review_request_content_hash"] = packet["subject_hash"]
    write_json(answer_path, data)
    checked = check(legacy, answer_path)
    assert checked["verdict"] == "not_evaluated"
    assert checked["junction_review"]["verdict"] == "not_evaluated"
    assert "missing_junction_binding" in checked["evidence_gaps"]
    assert "junction_binding" in {
        item["requirement_id"] for item in checked["completion_summary"]["requirements_to_address"]
    }
    assert "衔接范围未知" in (legacy / "report.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("mutation", ["binding", "source", "coverage", "contract", "missing", "symlink", "path_escape"])
def test_goal_snapshot_tampering_removes_old_pass(bound_packet, mutation):
    from ai_video.production.hashing import canonical_sha256
    output, _, _ = bound_packet
    path = answers(output)
    check(output, path)
    packet = json.loads((output / "packet.json").read_text())
    creative = output / "creative"
    target = {"binding": "binding.json", "source": "input.txt", "coverage": "coverage.json",
        "contract": "contract.json"}.get(mutation, "input.txt")
    if mutation == "missing": (creative / target).unlink()
    elif mutation == "symlink":
        (creative / target).rename(creative / "substitute.txt")
        (creative / target).symlink_to(creative / "substitute.txt")
    elif mutation == "path_escape":
        packet["goal_binding"]["path"] = "creative/../creative/binding.json"
        packet["subject_hash"] = canonical_sha256({k: v for k, v in packet.items() if k != "subject_hash"})
        write_json(output / "packet.json", packet)
    else:
        with (creative / target).open("ab") as stream: stream.write(b"changed")
    with pytest.raises(ValueError):
        check(output, path)
    assert not (output / "result.json").exists()
    assert not (output / "report.html").exists()


@pytest.mark.parametrize("mutation", ["missing_contract", "different_contract", "stale_source", "invalid_mapping"])
def test_binding_preflight_runs_before_probe_extraction_or_mkdir(tmp_path, monkeypatch, mutation):
    from test_creative_goal_binding import goal_inputs
    authored, goal = complete_goal("advertising")
    path, envelope, _, _ = goal_inputs(tmp_path / "authoring", contract=goal)
    if mutation == "missing_contract": goal = None
    elif mutation == "different_contract": goal = goal.model_copy(update={"goal_version": "2"})
    elif mutation == "stale_source": (path.parent / "input.txt").write_text("different")
    else:
        envelope["bindings"].pop(0)
        write_json(path, envelope)
    def forbidden(*args, **kwargs):
        pytest.fail("Binding rejection must precede media effects")
    monkeypatch.setattr(subprocess, "run", forbidden)
    output = tmp_path / "review"
    with pytest.raises(ValueError):
        prepare(tmp_path / "missing.mp4", authored, output, (0,), final_output_contract=goal, goal_binding=path)
    assert not output.exists()


def test_snapshot_uses_preflight_bytes_even_if_external_inputs_drift_during_probe(packet, tmp_path, monkeypatch):
    from test_creative_goal_binding import goal_inputs
    from scripts.visual_quality_report import reopen
    authored, goal = complete_goal("advertising")
    binding, _, _, _ = goal_inputs(tmp_path / "authoring", contract=goal)
    video, timeline, report = full_contract_media(tmp_path / "complete-inputs")
    original = (binding.parent / "input.txt").read_bytes()
    real_run = subprocess.run
    def drift(*args, **kwargs):
        (binding.parent / "input.txt").write_bytes(b"changed after validation")
        return real_run(*args, **kwargs)
    monkeypatch.setattr(subprocess, "run", drift)
    output = tmp_path / "frozen"
    prepare(video, authored, output, (0,), final_output_contract=goal, goal_binding=binding,
        timeline=timeline, render_report=report)
    assert (output / "creative/input.txt").read_bytes() == original
    assert reopen(output)[1] == goal


def test_effective_requirement_summary_never_displays_raw_human_pass_as_proven(bound_packet):
    output, _, goal = bound_packet
    path = answers(output)
    raw = json.loads(path.read_text())
    raw["strength"] = "explicit_evaluator"
    raw["observation"].update(viewing_mode="sampled_frames", viewing_speed_milli=None)
    write_json(path, raw)
    result = check(output, path)
    assert all(f["verdict"] == "pass" for f in result["findings"])
    effective = {r["requirement_id"]: r for r in result["effective_requirements"]}
    extra = goal.requirements[-1].requirement_id
    assert effective[extra]["verdict"] == "not_evaluated"
    assert "invalid_human_proof" in effective[extra]["evidence_gaps"]
    assert extra in {r["requirement_id"] for r in result["completion_summary"]["requirements_to_address"]}
    html = (output / "report.html").read_text()
    assert "有效结果" in html and "原始回答" in html and "invalid_human_proof" in html
    assert result["verdict"] == "not_evaluated"


def test_goal_binding_cli_consumes_same_preflight_and_reopen(packet, tmp_path):
    from scripts.visual_quality_report import main, reopen
    from test_creative_goal_binding import goal_inputs
    authored, goal = complete_goal("drama")
    binding, _, _, _ = goal_inputs(tmp_path / "authoring", kind="drama", contract=goal)
    config = tmp_path / "direction.json"
    write_json(config, authored.model_dump(mode="json"))
    output = tmp_path / "cli"
    video, timeline, report = full_contract_media(tmp_path / "complete-inputs")
    args = ["prepare", "--video", str(video), "--direction", str(config),
        "--content-kind", "drama", "--output", str(output), "--timestamps-ms", "0", "200",
        "--goal-binding", str(binding), "--timeline", str(timeline), "--render-report", str(report)]
    assert main(args) == 2
    assert not output.exists()
    assert main(args + ["--contract", str(binding.parent / "contract.json")]) == 0
    assert reopen(output)[0]["schema_version"] == "visual-review-packet/4"
    assert main(["check", "--packet", str(output), "--answers", str(answers(output))]) == 0


@pytest.mark.parametrize("rejected", [False, True])
def test_feedback_revision_is_sealed_new_input_and_never_rewrites_old_report(bound_packet, packet, tmp_path, rejected):
    from scripts.visual_quality_report import reopen
    from test_creative_goal_binding import reseal
    output, binding, goal = bound_packet
    check(output, answers(output))
    old = {p: p.read_bytes() for p in output.rglob("*") if p.is_file()}
    old_subject = reopen(output)[0]["subject_hash"]
    envelope = json.loads(binding.read_text())
    coverage = json.loads((binding.parent / "coverage.json").read_text())
    feedback = "用户拒绝全程单图，要求重新设计。" if rejected else "用户同意当前方案，仍待实际观看。"
    source = (binding.parent / "input.txt").read_text() + feedback + "\n"
    (binding.parent / "input.txt").write_text(source)
    import hashlib
    envelope["creative_input"]["sha256"] = hashlib.sha256(source.encode()).hexdigest()
    coverage["request"]["creative_input_evidence"] = source
    for intent in coverage["intent_items"]:
        intent["source_refs"][0]["source_hash"] = envelope["creative_input"]["sha256"]
    reseal(binding, envelope, "coverage", coverage)
    revision = goal.model_copy(update={"goal_version": "2"})
    reseal(binding, envelope, "final_output_contract", revision.model_dump(mode="json"))
    new = tmp_path / "new-revision"
    authored, _ = complete_goal("drama")
    video, timeline, report = full_contract_media(tmp_path / "new-revision-inputs")
    result = prepare(video, authored, new, (0,), final_output_contract=revision,
        goal_binding=binding, timeline=timeline, render_report=report)
    assert result["subject_hash"] != old_subject
    assert result["completion_summary"]["user_feedback"]["assessment"] == "parent_review_required"
    assert result["completion_summary"]["user_feedback"]["source"]["sha256"] == envelope["creative_input"]["sha256"]
    assert feedback in (new / "creative/input.txt").read_text()
    assert {p: p.read_bytes() for p in output.rglob("*") if p.is_file()} == old
    assert reopen(output)[1] == goal


def test_legacy_packet_reports_absence_of_goal_chain(packet):
    result = check(packet, answers(packet))
    assert result["goal_chain"] == "not_evaluated"
    assert "目标引用链未核对" in (packet / "report.html").read_text()
