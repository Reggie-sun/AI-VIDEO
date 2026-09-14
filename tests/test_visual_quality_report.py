"""Actual extraction, report rendering, and exact-media tamper regressions."""

import json
from pathlib import Path
import subprocess

import pytest

from scripts.visual_quality_report import check, prepare, write_json
from test_production_visual_quality import direction


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
