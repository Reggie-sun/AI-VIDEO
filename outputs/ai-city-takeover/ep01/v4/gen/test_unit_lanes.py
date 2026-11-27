"""Focused offline tests for the v4 lanes: SG03 multimodal lip-sync, MO06 first frame, the v4 pins, SD_TRIAL routing,
cut_audio.py and units.py.

  PYTHONDONTWRITEBYTECODE=1 uv run pytest -p no:cacheprovider outputs/ai-city-takeover/ep01/v4/gen/test_unit_lanes.py

unit.py runs in-process against a tmp trial folder whose director coverage (a fresh build_coverage.py build), vocal
windows and unit folders are tmp files; nothing is written under the repo and nothing is called.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
from pathlib import Path
import subprocess
import sys
import wave

import pytest

GEN = Path(__file__).resolve().parent
REPO = GEN.parents[4]
SG03_PLATE = "outputs/ai-city-takeover/ep01/v4/board/plates/p012-w1.png"
MO06_PLATE = "outputs/ai-city-takeover/ep01/v4/board/plates/p011-w1c.png"   # V11a-2 with the strap fixed (STRAP s011-b)
V4R1_PAGE = REPO / "outputs/ai-city-takeover/ep01/v4/excerpt/flash/v4r1.html"   # v4 round 1, 「s011 选 1，s012 选 1，开拍」
V3_COVERAGE = REPO / "outputs/ai-city-takeover/ep01/v3/director-coverage.json"
V3_STEM = REPO / "outputs/ai-city-takeover/ep01/v2/song-v3/stems/htdemucs_ft/IRIS-01-T4/vocals.wav"
V3_U021 = REPO / "outputs/ai-city-takeover/ep01/v3/pilot/audio/U021.wav"
# the exact v4 round-1 prompts the user approved (2026-11-18) for the W1 plates p012-w1 / p011-w1
SG03_PROMPT = ("{{image:0}}中的她对着值班工程师唱歌，口型与{{audio:1}}里的人声逐字精确同步。中近景，嘴前没有任何遮挡。"
               "镜头全程锁定，一镜到底。")
MO06_PROMPT = ("镜头固定，低机位，从侧前方拍。地下停车场改成的秀场，她沿着湿的水泥走秀台大步向前走，抬起的那只靴子落地，"
               "重心越过支撑脚，长的那只袖子随后摆回；面无表情，带着一点好奇看着前方；两边前排的值班工程师一个接一个站起来。")
SG03C_PROMPT = ("{{image:0}}中的她闭着眼睛唱歌，口型与{{audio:1}}里的人声逐字精确同步。近景，机头直闪。左前景的工程师一直在"
                "画面里。镜头固定不动，不推不拉不摇不环绕，一镜到底。嘴前没有任何遮挡。")   # approved on closeup3.html (D4-a)
SG04_PROMPT = ("{{image:0}}中的她低头看着镜头唱歌，口型与{{audio:1}}里的人声逐字精确同步。仰拍中近景，机头直闪。手机一直拿在胸口"
               "下方，不举到脸边。镜头固定不动，不推不拉不摇不环绕，一镜到底。嘴前没有任何遮挡。")   # round2.html (S13-b)
MO07_PROMPT = ("长焦全身远景，镜头固定不动。她走到走秀台尽头，重心落在前脚，一个干脆的急转身，"
               "长袖和外套下摆甩成一个圆再落下；转身后她头也不回，一只手按住腰间震动的黑色寻呼机，"
               "朝画面右侧走开。两侧的值班工程师抬头看着她。")   # round2.html (S14-c)
# MO07 r3 retake (2026-11-21, 「按 v2 做，s014 开拍 (Recommended)」 on pilot/opening/plan/v2.html): engineers keep their heads
# down, the pager lights no red; unit.py's MO07 spec now requires these phrases (the s-2 wording is MO07_PROMPT above).
MO07_R3_PROMPT = ("长焦全身远景，镜头固定不动。她走到走秀台尽头，重心落在前脚，一个干脆的急转身，"
                  "长袖和外套下摆甩成一个圆再落下；转身后她头也不回，一只手按住腰间震动的黑色寻呼机，朝画面右侧走开。"
                  "两侧的值班工程师一直低头盯着自己腿上的笔记本电脑，全程不抬头，身体保持不动。"
                  "她腰间的寻呼机不亮任何红灯。除了她左耳耳挂上的小红灯，画面里没有任何红色。画面中不得出现任何文字。")
MO07_R3_TEMPLATE = REPO / "outputs/ai-city-takeover/ep01/v4/pilot/opening/MO07-r3-approval.template.json"
# MO07 r4 retake (2026-11-21, 「用 a 拍 (Recommended)」 on pilot/opening/review-s014r4/index.html): first frame p014-w1c
# (engineers all heads down; the r3 Gate failed because p014-w1b already had them looking up) and one added sentence.
MO07_R4_PROMPT = MO07_R3_PROMPT.replace("朝画面右侧走开。", "朝画面右侧走开。她始终完整在画面里，头顶不出画。")
MO07_R4_TEMPLATE = REPO / "outputs/ai-city-takeover/ep01/v4/pilot/opening/MO07-r4-approval.template.json"
# MO07 r5 retake (2026-11-21, 「按页面改 prompt 拍 r5 (Recommended)」 on pilot/opening/review-s014r5/index.html): both r4
# takes walked toward the camera first and lost the top of her head; same plate, she starts already stopped and exits away.
MO07_R5_PROMPT = MO07_R4_PROMPT.replace("她走到走秀台尽头，重心落在前脚，一个干脆的急转身",
                                        "她已经停在走秀台尽头，不再往前走，站在原地一个干脆的急转身").replace(
    "朝画面右侧走开。", "背对镜头朝画面右侧走开，越走越远。")
MO07_R5_TEMPLATE = REPO / "outputs/ai-city-takeover/ep01/v4/pilot/opening/MO07-r5-approval.template.json"
# MO07 r6 retake (2026-11-21, 「按页面拍 r6 (Recommended)」 on pilot/opening/review-s014r6/index.html): both r5 takes moved the
# pager to her back after the turn; the right-hand press comes before the turn and pager and badge stay on the front chain.
MO07_R6_PROMPT = MO07_R5_PROMPT.replace("不再往前走，站在原地一个干脆的急转身",
                                        "不再往前走，先低头用右手按住身前腰链上震动的黑色寻呼机，然后松开手，站在原地一个干脆的急转身").replace(
    "转身后她头也不回，一只手按住腰间震动的黑色寻呼机，背对镜头朝画面右侧走开，越走越远。",
    "转身后她头也不回，背对镜头朝画面右侧走开，越走越远。寻呼机和工牌一直挂在她身前的腰链上，背对镜头时看不见。")
MO07_R6_TEMPLATE = REPO / "outputs/ai-city-takeover/ep01/v4/pilot/opening/MO07-r6-approval.template.json"
PROFILE = {"model_id": "seedance_2.0_vip", "account_sha256": "72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe",
           "project_id": "829df260-5a63-4f0d-8265-8353dc693b3b", "resolution": "4k", "aspect_ratio": "16:9",
           "benefit_type": "seedance_20_pro_4k_output"}


def load(name: str):
    spec = importlib.util.spec_from_file_location(f"iris_v4_gen_{name}", GEN / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


U, C, L, B, E = load("unit"), load("cut_audio"), load("units"), load("build_coverage"), load("excerpt_approvals")
EXCERPT = REPO / "outputs/ai-city-takeover/ep01/v4/pilot/excerpt/preview-inputs.json"   # user-approved excerpt units


def sha(path) -> str:
    return hashlib.sha256((REPO / path).read_bytes()).hexdigest()


def frames(path: Path) -> tuple[bytes, int, int, int]:
    with wave.open(str(path)) as wav:
        return wav.readframes(wav.getnframes()), wav.getframerate(), wav.getnchannels(), wav.getsampwidth()


@pytest.fixture
def lane(tmp_path, monkeypatch):
    """A tmp trial folder: coverage with the clip ids, SG03's vocal cut by cut_audio.py, approval written per test."""
    (tmp_path / "director-coverage.json").write_text(json.dumps(B.build(), ensure_ascii=False), encoding="utf-8")
    audio = tmp_path / "audio"
    C.cut("SG03", out=audio)
    monkeypatch.setattr(U, "COVERAGE", tmp_path / "director-coverage.json")
    monkeypatch.setattr(U, "VOCALS", str(audio / "windows.json"))
    monkeypatch.setitem(U.SPECS["SG03"]["audio"], "path", str(audio / "SG03.wav"))
    for name, value in (("PILOT", tmp_path), ("UNITS", tmp_path), ("APPROVAL", tmp_path / "preview-approval.json"),
                        ("REPORT", tmp_path / "continuity-report.json")):
        monkeypatch.setattr(U, name, value)
    return tmp_path


def sg03_approval(lane: Path, prompt: str = SG03_PROMPT) -> dict:
    vocal = str(lane / "audio" / "SG03.wav")
    return {"schema": "iris-v4-preview-approval/1", "unit_group": "sg03-lipsync", "question": "test", "user_quote": "test",
            "approved_at": "2026-11-17T00:00:00+00:00",
            "preview_artifacts": [{"path": SG03_PLATE, "sha256": sha(SG03_PLATE), "role": "SG03 reference image"},
                                  {"path": vocal, "sha256": sha(vocal), "role": "SG03 vocal"}],
            "prompts": {"SG03": {"text": prompt, "sha256": hashlib.sha256(prompt.encode()).hexdigest()}},
            "generation": {"model": "seedance_2.0_vip", "mode": "multimodal", "seconds": 6, "resolution": "4k",
                           "aspect": "16:9", "audio": "reference_audio"},
            "budget": {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 200, "cumulative_CRD": 200},
            "identity_waivers": ["IRIS"]}


def mo06_approval(prompt: str = MO06_PROMPT) -> dict:
    return {"schema": "iris-v4-preview-approval/1", "unit_group": "mo06-first-frame", "question": "test",
            "user_quote": "test", "approved_at": "2026-11-17T00:00:00+00:00",
            "preview_artifacts": [{"path": MO06_PLATE, "sha256": sha(MO06_PLATE), "role": "MO06 first frame"}],
            "prompts": {"MO06": {"text": prompt, "sha256": hashlib.sha256(prompt.encode()).hexdigest()}},
            "generation": {"model": "seedance_2.0_vip", "mode": "first_frame", "seconds": 5, "resolution": "4k",
                           "aspect": "16:9", "audio": None},
            "budget": {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 165, "cumulative_CRD": 165},
            "identity_waivers": ["IRIS"]}


def approve(lane: Path, value: dict) -> None:
    (lane / "preview-approval.json").write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def blocked(unit: str) -> str:
    with pytest.raises(U.Blocked) as error:
        U.draft(unit)
    return str(error.value)


def materialize(lane: Path, unit: str, profile: dict, capsys) -> dict:
    U.draft(unit)
    path = lane / unit / "profile.json"
    path.write_text(json.dumps(PROFILE | profile))
    U.materialize(unit, path)
    capsys.readouterr()
    U.show(unit)
    return json.loads(capsys.readouterr().out)


# ---------------------------------------------------------------- unit.py
def test_sg03_multimodal_resolves_the_expected_request(lane, capsys):
    approve(lane, sg03_approval(lane))
    request = materialize(lane, "SG03", {"input_mode": "multimodal", "node_id": "node_dryrunsg03", "duration_seconds": 6,
                                         "benefit_amount": 6, "credit_upper_bound": 200}, capsys)
    assert (request["model"], request["input_mode"], request["request_mode"], request["seconds"], request["resolution"],
            request["aspect"], request["native_audio"]) == (
        "seedance_2.0_vip", "multimodal", "reference_to_video", 6, "4k", "16:9", True)
    assert request["image_bindings"] == [{"role": "reference", "asset_id": "iris-c-v4-sg03-reference",
        "asset_sha256": sha(SG03_PLATE), "mime_type": "image/png", "width": 1672, "height": 941}]
    assert request["media_bindings"] == [{"kind": "audio", "role": "reference_audio", "asset_id": "iris-c-v4-sg03-vocal",
        "asset_sha256": sha(lane / "audio" / "SG03.wav"), "mime_type": "audio/wav", "duration_millis": 5991}]
    assert request["prompt"] == SG03_PROMPT                  # the approved text is the native text, markers included
    character = json.loads((lane / "SG03" / "character.json").read_text())
    assert character["identity"].startswith("IRIS v4 身份锚点 F1a")


def test_mo06_first_frame_resolves_the_expected_request(lane, capsys):
    approve(lane, mo06_approval())
    request = materialize(lane, "MO06", {"input_mode": "first_frame", "node_id": "node_dryrunmo06", "duration_seconds": 5,
                                         "benefit_amount": 5, "credit_upper_bound": 165}, capsys)
    assert (request["model"], request["input_mode"], request["seconds"], request["native_audio"]) == (
        "seedance_2.0_vip", "first_frame", 5, True)
    assert [(b["asset_id"], b["asset_sha256"], b["width"], b["height"]) for b in request["image_bindings"]] == [
        ("iris-c-v4-mo06-first-frame", sha(MO06_PLATE), 1672, 941)]
    assert request["media_bindings"] == []
    assert request["prompt"] == MO06_PROMPT


@pytest.mark.parametrize("unit,prompt,ceiling,which,shown", [("MO06", MO06_PROMPT, 400, "mo06-s-1", "v4r1.html"),
                                                             ("SG03", SG03_PROMPT, 700, "v4r1", "v4r1.html"),
                                                             ("SG03C", SG03C_PROMPT, 400, "sg03c-d1", "closeup3.html"),
                                                             ("SG04", SG04_PROMPT, 400, "sg04-r2-1", "round2.html")])
def test_v4r1_approved_prompts_pass_draft_and_lint(lane, monkeypatch, capsys, unit, prompt, ceiling, which, shown):
    """The exact round-1 texts (on the page the user saw) hold every required phrase and resolve a 4k request."""
    page = (E.FLASH / shown).read_text(encoding="utf-8")         # the page on which the user saw this exact text
    assert prompt in page and E.SETS[which]["rows"][unit]["prompt"] == prompt
    spec = U.SPECS[unit]
    literals = [spec["image"][4], *spec["intent"]["open_event"], *spec["intent"]["close_event"], *spec["intent"]["natural"]]
    assert [x for x in literals if x not in prompt] == []
    assert U.prompt_language_ok(spec, prompt) and spec["look"] == "W1"
    monkeypatch.setattr(U, "VOCALS", "outputs/ai-city-takeover/ep01/v4/pilot/audio/windows.json")   # sealed SG03
    monkeypatch.setitem(U.SPECS["SG03"]["audio"], "path", "outputs/ai-city-takeover/ep01/v4/pilot/audio/SG03.wav")
    (target, value), = E.v4r1_approvals("q", "s011 选 1，s012 选 1，开拍", "2026-11-18T00:00:00+00:00", [unit],
                                         pilot=lane / "approvals", which=which).items()
    suffix = E.SETS[which]["suffix"]
    assert target == lane / "approvals" / (f"sd-{unit}-{suffix}" if suffix else f"sd-{unit}") / "preview-approval.json"
    assert value["budget"] == {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": ceiling,
                               "cumulative_CRD": ceiling}
    assert value["generation"]["resolution"] == "4k" and value["prompts"][unit]["text"] == prompt
    approve(lane, value)
    secs = spec["duration"]
    request = materialize(lane, unit, {"input_mode": spec["input_mode"], "node_id": "node_dryrun" + unit.lower(),
                                       "duration_seconds": secs, "benefit_amount": secs, "credit_upper_bound": ceiling},
                          capsys)
    assert (request["seconds"], request["resolution"], request["prompt"]) == (secs, "4k", prompt)
    assert [b["asset_sha256"] for b in request["image_bindings"]] == [sha(E.SETS[which]["rows"][unit]["still"])]
    character = json.loads((lane / unit / "character.json").read_text())
    assert (character["appearance_bible"], character["wardrobe"]) == (U.W1_NEAR, [U.W1_WARDROBE])


def _without_vocal(value, lane):
    value["preview_artifacts"] = value["preview_artifacts"][:1]


def _vocal_sha(value, lane):
    value["preview_artifacts"][1]["sha256"] = "0" * 64


def _other_vocal(value, lane):
    C.cut("SG04", out=lane / "audio")
    other = str(lane / "audio" / "SG04.wav")
    value["preview_artifacts"][1] |= {"path": other, "sha256": sha(other)}


def _extra_input(value, lane):
    value["preview_artifacts"].append({"path": SG03_PLATE, "sha256": sha(SG03_PLATE), "role": "SG03 first frame"})


def _first_frame_generation(value, lane):
    value["generation"] |= {"mode": "first_frame", "audio": None}


def _five_seconds(value, lane):
    value["generation"]["seconds"] = 5


@pytest.mark.parametrize("mutate,reason", [
    (_without_vocal, "exactly one preview artifact with role 'SG03 vocal'"),
    (_vocal_sha, "approved vocal changed since the approval"),
    (_other_vocal, "is not the window this unit was written for"),
    (_extra_input, "inputs this unit does not send"),
    (_first_frame_generation, "approval generation must be exactly"),
    (_five_seconds, "approval generation must be exactly"),
])
def test_sg03_blocks_anything_the_approval_does_not_hold(lane, mutate, reason):
    value = sg03_approval(lane)
    mutate(value, lane)
    approve(lane, value)
    assert reason in blocked("SG03")


@pytest.mark.parametrize("prompt", [SG03_PROMPT.replace("{{image:0}}", "{{image:1}}"),     # 1-based markers do not bind
                                    SG03_PROMPT.replace("{{audio:1}}", "人声"),
                                    SG03_PROMPT.replace("中近景", "MCU"),
                                    SG03_PROMPT.replace("嘴前没有任何遮挡。", "")])       # a required phrase dropped
def test_sg03_prompt_lint(lane, prompt):
    approve(lane, sg03_approval(lane, prompt))
    assert "native prompt" in blocked("SG03")


def test_board_pin_blocks_a_changed_board(lane, monkeypatch):
    approve(lane, mo06_approval())
    monkeypatch.setattr(U, "BOARD_SHA256", "0" * 64)
    assert "board/shots.json changed since this lane was written" in blocked("MO06")
    assert not (lane / "MO06").exists()                     # nothing written before the pin passes


def test_plate_pin_blocks_a_changed_plate(lane, monkeypatch):
    approve(lane, mo06_approval())
    monkeypatch.setitem(U.SPECS["MO06"], "plate_sha256", "0" * 64)
    assert "plate changed since this unit was written" in blocked("MO06")


def test_anchor_pin_blocks_a_changed_anchor(lane, monkeypatch):
    approve(lane, mo06_approval())
    monkeypatch.setattr(U, "ANCHOR_SHA256", "0" * 64)
    assert "identity anchor changed" in blocked("MO06")


def test_spec_must_match_the_board_clip(lane, monkeypatch):
    approve(lane, mo06_approval())
    monkeypatch.setitem(U.SPECS["MO06"], "plate", "p012")
    assert "is not the board clip" in blocked("MO06")


def test_missing_or_foreign_coverage_blocks(lane, monkeypatch):
    approve(lane, mo06_approval())
    monkeypatch.setattr(U, "COVERAGE", lane / "nope.json")
    assert "no v4 director coverage" in blocked("MO06")
    coverage = json.loads(V3_COVERAGE.read_text(encoding="utf-8"))
    (lane / "v3.json").write_text(json.dumps(coverage, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(U, "COVERAGE", lane / "v3.json")
    assert "MO06 is not a unit of the v4 director coverage" in blocked("MO06")


def test_vocal_must_be_the_sealed_board_window(lane):
    book = lane / "audio" / "windows.json"
    value = json.loads(book.read_text())
    value["windows"]["SG03"]["song_window"] = [44.9, 50.933]
    book.write_text(json.dumps(value))
    approve(lane, sg03_approval(lane))
    assert "is not the board clip window" in blocked("SG03")


def test_specs_agree_with_the_board_and_the_lyric_timing():
    board = json.loads((REPO / U.BOARD).read_bytes())
    assert hashlib.sha256((REPO / U.BOARD).read_bytes()).hexdigest() == U.BOARD_SHA256
    words = [w for line in json.loads(C.WORDS.read_text())["lines"] for w in line["words"]]
    for unit, spec in U.SPECS.items():
        unit = spec.get("clip", unit)                            # the SG17A / SG17B probe arms are the board clip SG17
        clip = next(c for c in board["clips"] if c["clip"] == unit)
        assert sha(U.PLATES + clip["start_frame"] + ".png") == spec["plate_sha256"]
        if spec.get("song_window"):                              # r4 short windows: test_r4_windows_* check their own
            continue
        margin = spec.get("take_margin_seconds", 0)              # SG05 m: one second over its window for the lead-in
        assert spec["generation"]["seconds"] == spec["duration"] >= clip["seconds"] + margin > spec["duration"] - 1
        if spec.get("dialogue"):
            t0 = clip["window"]["t0"]
            inside = [w for w in words if t0 <= w["start"] < clip["window"]["t1"]]
            assert spec["dialogue"]["verbatim_text"] == " ".join(clip["words"]) == " ".join(w["text"] for w in inside)
            assert spec["dialogue"]["start_seconds"] == round(inside[0]["start"] - t0, 2)
            # a last word that runs past the take (SG08, SG09) ends where the take ends: the vocal window is cut there
            # ... and, for the m re-windowed units, never past the vocal window's end (SG09 m: 4.543 s window, 5 s take)
            # ... and so for every s031-s048 spoken / sung unit (SG20: 3.56 s vocal, 6 s take)
            window_end = round(clip["window"]["t1"] - t0, 2) if unit in S1530_M[1:] + S3148_LIPSYNC else spec["duration"]
            assert spec["dialogue"]["end_seconds"] == min(round(inside[-1]["end"] - t0, 2), window_end, spec["duration"])


@pytest.mark.parametrize("env,pilot,units", [
    ({}, "outputs/ai-city-takeover/ep01/v4/pilot/sd", "outputs/ai-city-takeover/ep01/v4/gen"),
    ({"SD_TRIAL": "outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03"}, "outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03",
     "outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03"),
    ({"SD_TRIAL": "outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03", "SD_UNITS": "/tmp/units"},
     "outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03", "/tmp/units"),
])
def test_sd_trial_routing(env, pilot, units):
    code = ("import json, sys; sys.path.insert(0, sys.argv[1]); import unit as U; "
            "print(json.dumps([str(U.PILOT), str(U.UNITS), str(U.APPROVAL), str(U.REPORT)]))")
    base = {k: v for k, v in os.environ.items() if k not in {"SD_TRIAL", "SD_PILOT", "SD_UNITS"}}
    out = subprocess.run([sys.executable, "-c", code, str(GEN)], cwd=REPO, capture_output=True, text=True, check=True,
                         env=base | {"PYTHONDONTWRITEBYTECODE": "1"} | env).stdout
    assert json.loads(out) == [str(REPO / pilot), str(REPO / units), str(REPO / pilot / "preview-approval.json"),
                               str(REPO / pilot / "continuity-report.json")]


# ---------------------------------------------------------------- cut_audio.py
def test_cut_reproduces_the_v3_pilot_cut_exactly():
    data, sr, n = C.cut_window(V3_STEM, 60.2, 64.56)      # v3 pilot/audio/windows.json: U021 song_window
    want, want_sr, channels, width = frames(V3_U021)
    assert (sr, n, channels, width) == (want_sr, 192276, 1, 2)
    assert data == want                                  # same samples, same downmix, no fade


def test_cut_sg03_is_the_exact_clip_window(tmp_path):
    result = C.cut("SG03", out=tmp_path)
    data, sr, channels, width = frames(tmp_path / "SG03.wav")
    n = round(50.933 * 44100) - round(44.9422 * 44100)
    assert (sr, channels, width, len(data) // 2) == (44100, 1, 2, n)
    assert result["seconds"] == 5.99 == round(n / sr, 2)
    assert result["sha256"] == hashlib.sha256((tmp_path / "SG03.wav").read_bytes()).hexdigest()
    assert data == C.cut_window(C.STEM, 44.9422, 50.933)[0]
    book = json.loads((tmp_path / "windows.json").read_text())
    assert book["source"] == "outputs/ai-city-takeover/ep01/v4/song/stems/htdemucs_ft/all-hands-r4-edc6c6bf/vocals.wav"
    assert book["windows"]["SG03"] | {} == {"path": str(tmp_path / "SG03.wav"), "song_window": [44.9422, 50.933],
        "plays": [44.9422, 49.087], "samples": n, "sample_rate_hz": 44100, "seconds": 5.99, "sha256": result["sha256"]}
    assert C.cut("SG03", out=tmp_path) == result          # re-running is a no-op


def test_cut_never_overwrites_other_bytes(tmp_path):
    (tmp_path / "SG03.wav").write_bytes(b"other")
    with pytest.raises(C.Refused, match="never overwritten"):
        C.cut("SG03", out=tmp_path)


def test_cut_refuses_a_motion_clip(tmp_path):
    with pytest.raises(C.Refused, match="motion clip"):
        C.cut("MO06", out=tmp_path)
    assert not any(tmp_path.iterdir())


@pytest.mark.parametrize("t0,refused", [(45.8, True),      # inside "hold" (45.625-45.986)
                                        (45.66, False),    # 0.035 s after its start: within the 0.05 s tolerance
                                        (44.9422, False)])
def test_cut_refuses_a_window_that_starts_inside_a_word(tmp_path, monkeypatch, t0, refused):
    board = json.loads(C.BOARD.read_text())
    clip = next(c for c in board["clips"] if c["clip"] == "SG03")
    clip["window"]["t0"] = t0
    (tmp_path / "shots.json").write_text(json.dumps(board, ensure_ascii=False))
    monkeypatch.setattr(C, "BOARD", tmp_path / "shots.json")
    if refused:
        with pytest.raises(C.Refused, match="inside the word"):
            C.cut("SG03", out=tmp_path / "audio")
        assert not (tmp_path / "audio").exists()
    else:
        assert C.cut("SG03", out=tmp_path / "audio")["window"] == [t0, 50.933]


# ---------------------------------------------------------------- units.py
def test_units_lists_the_preview_pack_inputs(tmp_path):
    C.cut("SG03", out=tmp_path)
    result = L.pack(["SG03", "MO06"], audio=tmp_path)
    assert result["missing"] == []
    assert result["board"]["sha256"] == U.BOARD_SHA256
    sg03, mo06 = result["clips"]
    assert sg03["plate"] == {"path": SG03_PLATE, "sha256": sha(SG03_PLATE), "size": [1672, 941]}
    assert sg03["audio"] | {} == {"path": str(tmp_path / "SG03.wav"), "sha256": sha(tmp_path / "SG03.wav"),
                                  "seconds": 5.99, "channels": 1, "sample_rate_hz": 44100, "sealed_window": True}
    assert (sg03["window"], sg03["seedance_seconds"]) == ({"t0": 44.9422, "t1": 50.933}, 6)
    assert [w["text"] for w in sg03["timed_words"]] == sg03["board_words"]
    assert sg03["timed_words"][0]["at"] == 0.683
    assert sg03["shots"][0]["id"] == "s012" and "弯腰凑到那个值班工程师脸前" in sg03["shots"][0]["action"]
    assert "4% 推近" in sg03["shots"][0]["camera"]
    assert "audio" not in mo06 and mo06["seedance_seconds"] == 5 and mo06["plate"]["sha256"] == sha(MO06_PLATE)


def test_units_reports_missing_inputs(tmp_path):
    not_cut = f"SG03: vocal {tmp_path / 'SG03.wav'} not cut or not the sealed window"
    assert L.pack(["SG03", "XX99"], audio=tmp_path)["missing"] == [not_cut, "XX99: not a clip of the board"]
    C.cut("SG03", out=tmp_path)
    (tmp_path / "windows.json").unlink()                 # cut but not sealed
    assert L.pack(["SG03"], audio=tmp_path)["missing"] == [not_cut]
    code = subprocess.run([sys.executable, str(GEN / "units.py"), "SG03", "--audio", str(tmp_path)], cwd=REPO,
                          capture_output=True, env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1"}).returncode
    assert code == 2


# ---------------------------------------------------------------- build_coverage.py
def test_coverage_is_valid_one_unit_per_clip_and_matches_the_file():
    from ai_video.production.reference_authoring import director_coverage_authoring_input

    coverage = B.build()
    director_coverage_authoring_input(coverage)          # the repo owner's validator; raises when invalid
    board = json.loads(B.BOARD.read_bytes())
    units = coverage["coverage_units"]
    assert [u["unit_id"] for u in units] == [c["clip"] for c in board["clips"]]
    assert [u["duration_seconds"] for u in units] == [c["seconds"] for c in board["clips"]]
    assert [u["transition_out"] for u in units] == ["cut"] * (len(units) - 1) + ["end"]
    evidence = coverage["request"]["creative_input_evidence"]
    assert evidence.endswith("先出底片贴上卡片再审 (Recommended)\n可以，按这个往下做")
    sing = next(c["constraint_id"] for c in coverage["request"]["creative_constraints"] if c["source_text"] == B.SING)
    assert all((sing in u["constraint_ids"]) == u["unit_id"].startswith("SG") for u in units)
    sg03 = next(u for u in units if u["unit_id"] == "SG03")
    assert (sg03["shot_scale"], sg03["camera_treatment"], sg03["close_state"]) == ("medium", "push_in",
                                                                                   "她直起身，他还攥着椅子扶手")
    assert B.OUT.read_text(encoding="utf-8") == json.dumps(coverage, ensure_ascii=False, indent=1) + "\n"


# ---------------------------------------------------------------- excerpt units (pilot/excerpt) + excerpt_approvals.py
EXCERPT_UNITS = [row["clip"] for row in json.loads(EXCERPT.read_text(encoding="utf-8"))["units"]]
LIVE_EXCERPT_UNITS = [unit for unit in EXCERPT_UNITS if unit not in E.SUPERSEDED]     # empty: every excerpt unit is superseded


def test_excerpt_units_have_specs():
    assert EXCERPT_UNITS == ["MO04", "SG02", "MO05", "MO06", "SG04", "MO07"]
    assert set(EXCERPT_UNITS) <= set(U.SPECS)


def test_excerpt_set_is_superseded():
    """Every excerpt unit is superseded (MO06 by v4r1, SG04 / MO07 by round 2, MO04 / SG02 / MO05 by the 2026-11-20
    opening set): the excerpt writer plans nothing and refuses each unit by name."""
    assert LIVE_EXCERPT_UNITS == []
    assert E.approvals("q", "原话", "2026-11-17T08:00:00+00:00", pilot=REPO / "nonexistent") == {}
    for unit, why in (("MO04", "opening set"), ("SG02", "opening set"), ("MO05", "opening set"), ("MO06", "v4 round 1"),
                      ("SG04", "round 2"), ("MO07", "round 2")):
        with pytest.raises(E.Refused, match=f"superseded by (the )?{why}"):
            E.approvals("q", "原话", "2026-11-17T08:00:00+00:00", [unit], pilot=REPO / "nonexistent")


def test_excerpt_approvals_refuse(tmp_path):
    with pytest.raises(E.Refused, match="non-empty"):
        E.approvals("q", " ", "2026-11-17T08:00:00+00:00", pilot=tmp_path)
    with pytest.raises(E.Refused, match="timezone"):
        E.approvals("q", "原话", "2026-11-17T08:00:00", pilot=tmp_path)
    with pytest.raises(E.Refused, match="not both"):
        E.approvals("q", "原话", "2026-11-17T08:00:00+00:00", ["SG03"], pilot=tmp_path)
    assert not any(tmp_path.iterdir())


def test_v4r1_approvals_refuse(tmp_path, monkeypatch):
    (tmp_path / "sd-SG03-w1").mkdir()
    (tmp_path / "sd-SG03-w1" / "preview-approval.json").write_text("{}")
    with pytest.raises(E.Refused, match="never overwritten"):
        E.v4r1_approvals("q", "原话", "2026-11-18T00:00:00+00:00", ["SG03"], pilot=tmp_path)
    with pytest.raises(E.Refused, match="not a v4r1 unit"):
        E.v4r1_approvals("q", "原话", "2026-11-18T00:00:00+00:00", ["MO04"], pilot=tmp_path)
    with pytest.raises(E.Refused, match="not the approved still"):    # V11a-1 / p011-w1 was replaced
        E.v4r1_approvals("q", "原话", "2026-11-18T00:00:00+00:00", ["MO06"], pilot=tmp_path)
    monkeypatch.setitem(E.V4R1B["MO06"], "sha256", "0" * 64)
    with pytest.raises(E.Refused, match="not the approved still"):
        E.v4r1_approvals("q", "原话", "2026-11-18T00:00:00+00:00", ["MO06"], pilot=tmp_path, which="v4r1b")
    with pytest.raises(E.Refused, match="not a v4r1b unit"):
        E.v4r1_approvals("q", "原话", "2026-11-18T00:00:00+00:00", ["SG03"], pilot=tmp_path, which="v4r1b")


def test_strapfix_approvals_shape(tmp_path):
    """Strap fix: MO06 (p011-w1c) and MO07 (p014-w1b), unchanged prompts, strapfix.html, two takes each, fresh ids.
    Since the 2026-11-21 r4 retake the MO07 spec is on p014-w1c, so the MO07 strap-fix approvals are refused like r2."""
    page = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/strapfix.html"
    assert sha(page) == "188c99d4b4f72064130fc18d80529ad61dcefef9c8e4c6a4d4885a3bd3bb2ffa"
    cases = {"MO06": ("p011-w1c", "22492025abac1e542346b54a26a0cfa19f78c00bb39a7448234618ff6e786b26", MO06_PROMPT,
                      "sd-MO06-w1b")}
    ids = []
    for unit, (plate, digest, prompt, old) in cases.items():
        replaced = f"outputs/ai-city-takeover/ep01/v4/pilot/{old}/preview-approval.json"
        assert json.loads((REPO / replaced).read_text())["prompts"][unit]["text"] == prompt   # the prompt is unchanged
        for n in (1, 2):
            (target, value), = E.v4r1_approvals("q", "两镜都用 b，拍 (Recommended)", "2026-11-19T17:54:00Z",
                                                 pilot=tmp_path, which=f"{unit.lower()}-s-{n}").items()
            assert target == tmp_path / f"sd-{unit}-s-{n}" / "preview-approval.json" and not target.exists()
            path = f"outputs/ai-city-takeover/ep01/v4/board/plates/{plate}.png"
            assert sha(path) == digest
            assert value["preview_artifacts"] == [{"path": path, "sha256": digest, "role": f"{unit} first frame"}]
            assert value["preview_page"] == {"path": page, "sha256": sha(page)}
            assert value["prompts"][unit]["text"] == prompt
            assert value["replaces_approval"] == {"path": replaced, "sha256": sha(replaced)}
            assert value["generation"] == {"model": "seedance_2.0_vip", "mode": "first_frame", "seconds": 5,
                                           "resolution": "4k", "aspect": "16:9", "audio": None}
            assert value["budget"] == {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 400,
                                       "cumulative_CRD": 400}
            tag = f"iris-{unit.lower()}-s-{n}"
            assert value["bound_ids"] == {"attempt_id": f"{tag}-source-001", "policy_id": f"{tag}-source-001",
                                          "reservation_id": f"{tag}-reservation-001"}
            assert value["takes"]["folders"] == [f"sd-{unit}-s-1", f"sd-{unit}-s-2"]
            ids += value["bound_ids"].values()
    assert len(set(ids)) == 4
    for old in ("v4r1b", "mo07-r2-1", "mo07-r2-2", "mo07-s-1", "mo07-s-2"):   # first frames the spec no longer uses
        with pytest.raises(E.Refused, match="not the approved still"):
            E.v4r1_approvals("q", "原话", "2026-11-19T00:00:00+00:00", pilot=tmp_path, which=old)


def mo07_r3_take(n: int) -> dict:
    """The approval template for take n (the template's own _template_notes: unit_group, the three ids, this_take)."""
    value = json.loads(MO07_R3_TEMPLATE.read_text(encoding="utf-8"))
    assert len(value.pop("_template_notes")) == 3
    swap = lambda text: text.replace("-r3-1", f"-r3-{n}")
    value["unit_group"] = swap(value["unit_group"])
    value["bound_ids"] = {k: swap(v) for k, v in value["bound_ids"].items()}
    value["takes"]["this_take"] = swap(value["takes"]["this_take"])
    return value


def test_mo07_r3_spec_and_template_shape():
    """r3 retake: the spec's required phrases are literal substrings of the r3 prompt (and of the s014-r3 source and the
    v2 page the user approved), the old looking-up phrase is gone, plate and 5 s unchanged, template shapes both takes."""
    source = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/s014-r3-seedance.md"
    page = "outputs/ai-city-takeover/ep01/v4/pilot/opening/plan/v2.html"
    block = re.search(r"```prompt\n(.*?)\n```", (REPO / source).read_text(encoding="utf-8"), re.S).group(1)
    assert block == MO07_R3_PROMPT and MO07_R3_PROMPT in (REPO / page).read_text(encoding="utf-8")
    # r3 is history since r4 (2026-11-21): the live spec moved to p014-w1c; the r3 plate and template stay as they were.
    r3_plate = "outputs/ai-city-takeover/ep01/v4/board/plates/p014-w1b.png"
    spec = {"image": [None, r3_plate], "plate_sha256": "c85aa47e12686ccdd6421bcae732eecd2862f43e736b62c33547b766c7f3ace8",
            "generation": {"model": "seedance_2.0_vip", "mode": "first_frame", "seconds": 5, "resolution": "4k",
                           "aspect": "16:9", "audio": None}}
    assert sha(r3_plate) == spec["plate_sha256"]
    old = "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-s-2/preview-approval.json"
    ids = []
    for n in (1, 2):
        value = mo07_r3_take(n)
        assert sorted(placeholders(value)) == sorted([value["question"], value["user_quote"], value["approved_at"]])
        assert value["preview_page"] == {"path": page, "sha256": sha(page)}
        assert value["prompt_source"] == {"path": source, "sha256": sha(source)}
        assert value["prompts"]["MO07"] == {"text": MO07_R3_PROMPT,
                                            "sha256": hashlib.sha256(MO07_R3_PROMPT.encode()).hexdigest()}
        assert value["preview_artifacts"] == [{"path": spec["image"][1], "sha256": spec["plate_sha256"],
                                               "role": "MO07 first frame"}]
        assert value["generation"] == spec["generation"] == {"model": "seedance_2.0_vip", "mode": "first_frame", "seconds": 5,
                                                              "resolution": "4k", "aspect": "16:9", "audio": None}
        assert value["budget"] == {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 400, "cumulative_CRD": 400}
        assert value["replaces_approval"]["path"] == old and value["replaces_approval"]["sha256"] == sha(old)
        assert value["takes"]["folders"] == ["sd-MO07-r3-1", "sd-MO07-r3-2"] and value["takes"]["this_take"] == f"sd-MO07-r3-{n}"
        assert (REPO / "outputs/ai-city-takeover/ep01/v4/pilot" / f"sd-MO07-r3-{n}").is_dir()
        tag = f"iris-mo07-r3-{n}"
        assert value["bound_ids"] == {"attempt_id": f"{tag}-source-001", "policy_id": f"{tag}-source-001",
                                      "reservation_id": f"{tag}-reservation-001"}
        ids += value["bound_ids"].values()
    used = {json.loads(b.read_text()).get(k) for b in (REPO / "outputs/ai-city-takeover/ep01/v4/pilot").glob(
        "sd-*/*/operator-bound.json") if "-r3-" not in b.parent.parent.name for k in ("attempt_id", "policy_id", "reservation_id")}
    assert len(set(ids)) == 4 and not set(ids) & used          # fresh ids, never an earlier take's


@pytest.mark.parametrize("n", [1, 2])
def test_mo07_r6_approval_passes_draft_materialize_and_lint(lane, capsys, n):
    """The written r6 approval drafts, resolves the 4k request with the r6 prompt and passes every lint check (tmp lane,
    MO01-style profile and bound; the continuity verdict is the only thing faked); the r3 template no longer drafts."""
    approve(lane, mo07_r3_take(n) | {"question": "q", "user_quote": "按 v2 做，s014 开拍 (Recommended)",
                                     "approved_at": "2026-11-21T08:00:00Z"})
    with pytest.raises(U.Blocked, match="not the still this unit was written for"):
        U.draft("MO07")
    value = json.loads((REPO / f"outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r6-{n}/preview-approval.json").read_text(
        encoding="utf-8"))
    approve(lane, value)
    U.draft("MO07")
    node = f"node_dryrunmo07r6{n}"
    profile = runbook_template("profile", "MO01") | {"node_id": node}
    path = lane / "MO07" / "profile.json"
    path.write_text(json.dumps(profile))
    U.materialize("MO07", path)
    capsys.readouterr()
    U.show("MO07")
    request = json.loads(capsys.readouterr().out)
    assert (request["model"], request["input_mode"], request["seconds"], request["resolution"], request["aspect"],
            request["prompt"]) == ("seedance_2.0_vip", "first_frame", 5, "4k", "16:9", MO07_R6_PROMPT)
    assert [b["asset_sha256"] for b in request["image_bindings"]] == [U.SPECS["MO07"]["plate_sha256"]] and not request["media_bindings"]
    bound = runbook_template("bound", "MO01") | {
        "unit": "MO07", "task": f"IRIS EP01 v4 MO07（s014，r6-{n}）; Seedance 2.0 VIP first_frame, 5 s 4k 16:9, no reference audio",
        "user_quote": value["user_quote"], "preview_approval": str(lane / "preview-approval.json"),
        "issued_at": "2026-11-21T08:30:00+00:00", "expires_at": "2026-11-21T14:30:00+00:00", **value["bound_ids"]}
    assert placeholders(bound) == []
    (lane / "MO07" / "operator-bound.json").write_text(json.dumps(bound, ensure_ascii=False))
    (lane / "MO07" / "node-created.json").write_text(json.dumps({"node_id": node, "empty": True}))
    (lane / "continuity-report.json").write_text(json.dumps({"units": {"MO07": {"verdict": "ready"}}}))
    code = "import json, sys; sys.path.insert(0, sys.argv[1]); import lint; print(json.dumps(lint.lint(sys.argv[2])['checks']))"
    env = {k: v for k, v in os.environ.items() if k not in {"SD_PILOT", "SD_UNITS"}} | {
        "SD_TRIAL": str(lane), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONWARNINGS": "ignore"}
    out = subprocess.run([sys.executable, "-c", code, str(GEN), "MO07"], cwd=REPO, capture_output=True, text=True, env=env,
                         check=True).stdout
    checks = json.loads(out.strip().splitlines()[-1])
    assert [k for k, v in checks.items() if not v] == []


def test_sg03c_d_approvals_shape(tmp_path):
    """Two takes under one approval: p012c-w1d (= D4-a), sealed vocal, closeup3.html, 4k, 400 CRD each, distinct ids."""
    question = "重做的首帧：http://127.0.0.1:8769/excerpt/flash/closeup3.html\n\n用哪张？"
    page = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/closeup3.html"
    assert SG03C_PROMPT in (REPO / page).read_text(encoding="utf-8")
    vocal = "outputs/ai-city-takeover/ep01/v4/pilot/audio/SG03C.wav"
    replaced = "outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03C-c/preview-approval.json"
    ids = []
    for n in (1, 2):
        (target, value), = E.v4r1_approvals(question, "D4-a，拍 (Recommended)", "2026-11-19T15:09:00Z", pilot=tmp_path,
                                             which=f"sg03c-d{n}").items()
        assert target == tmp_path / f"sd-SG03C-d{n}" / "preview-approval.json" and not target.exists()
        assert value["question"] == question and value["user_quote"] == "D4-a，拍 (Recommended)"
        assert value["preview_artifacts"] == [
            {"path": "outputs/ai-city-takeover/ep01/v4/board/plates/p012c-w1d.png",
             "sha256": "21c5f96a6cdbdf4f39d99b9137e4092776d4f3b4d77adba4178532c473682c48", "role": "SG03C reference image"},
            {"path": vocal, "sha256": sha(vocal), "role": "SG03C vocal"}]
        assert value["preview_page"] == {"path": page, "sha256": sha(page)}
        assert value["generation"] == {"model": "seedance_2.0_vip", "mode": "multimodal", "seconds": 4, "resolution": "4k",
                                       "aspect": "16:9", "audio": "reference_audio"}
        assert value["budget"] == {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 400,
                                   "cumulative_CRD": 400}
        assert value["prompts"]["SG03C"]["text"] == SG03C_PROMPT
        assert value["replaces_approval"] == {"path": replaced, "sha256": sha(replaced)}
        assert value["bound_ids"] == {"attempt_id": f"iris-sg03c-d{n}-source-001",
                                      "policy_id": f"iris-sg03c-d{n}-source-001",
                                      "reservation_id": f"iris-sg03c-d{n}-reservation-001"}
        assert value["takes"]["folders"] == ["sd-SG03C-d1", "sd-SG03C-d2"] and value["takes"]["this_take"] == f"sd-SG03C-d{n}"
        ids += value["bound_ids"].values()
    per_set = [set(row["bound_ids"].values()) for cfg in E.SETS.values() for row in cfg["rows"].values()
               if row.get("bound_ids")]                  # attempt_id == policy_id within a set, as in every bound
    assert len(set(ids)) == 4 and sum(map(len, per_set)) == len(set().union(*per_set))   # no two sets share an id
    for old in ("sg03c", "sg03c-b", "sg03c-c"):          # D1-b / D2-b / D3-b no longer match the spec
        with pytest.raises(E.Refused, match="not the approved still"):
            E.v4r1_approvals("q", "原话", "2026-11-19T00:00:00+00:00", pilot=tmp_path, which=old)


def test_sg03c_d_refuses_bound_ids_already_in_use(tmp_path):
    (tmp_path / "sd-SG03C-d1" / "SG03C").mkdir(parents=True)
    (tmp_path / "sd-SG03C-d1" / "SG03C" / "operator-bound.json").write_text(
        json.dumps({"attempt_id": "iris-sg03c-d2-source-001", "policy_id": "p", "reservation_id": "r"}))
    with pytest.raises(E.Refused, match="bound ids already used"):
        E.v4r1_approvals("q", "D4-a，拍 (Recommended)", "2026-11-19T15:09:00Z", pilot=tmp_path, which="sg03c-d2")


def test_lint_holds_the_bound_ids_and_a_fresh_node(lane, monkeypatch, capsys):
    """lint.py: reused bound ids or a canvas node another pilot folder holds fail; the sealed ids and a fresh node pass."""
    monkeypatch.setattr(U, "VOCALS", "outputs/ai-city-takeover/ep01/v4/pilot/audio/windows.json")
    (_, value), = E.v4r1_approvals("q", "D4-a，拍 (Recommended)", "2026-11-19T15:09:00Z", pilot=lane / "approvals",
                                   which="sg03c-d1").items()
    approve(lane, value)
    materialize(lane, "SG03C", {"input_mode": "multimodal", "node_id": "node_dryrunsg03cd1", "duration_seconds": 4,
                                "benefit_amount": 4, "credit_upper_bound": 400}, capsys)
    bound = {"schema_version": "iris-v4-unit/1", "unit": "SG03C", "user_quote": value["user_quote"],
             "preview_approval": str(lane / "preview-approval.json"), "max_submit_count": 1, "automatic_retries": 0,
             "operator_currency": "CRD", "operator_ceiling": 400, "ledger": "ledger.json", "cumulative_submit_ceiling": 1,
             "cumulative_operator_credit_ceiling": 400}
    code = "import json, sys; sys.path.insert(0, sys.argv[1]); import lint; print(json.dumps(lint.lint('SG03C')['checks']))"
    env = {k: v for k, v in os.environ.items() if k not in {"SD_PILOT", "SD_UNITS"}} | {
        "SD_TRIAL": str(lane), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONWARNINGS": "ignore"}

    def checks(ids: dict, node: str) -> dict:
        (lane / "SG03C" / "operator-bound.json").write_text(json.dumps(bound | ids))
        profile = json.loads((lane / "SG03C" / "profile.json").read_text())
        (lane / "SG03C" / "profile.json").write_text(json.dumps(profile | {"node_id": node}))
        (lane / "SG03C" / "node-created.json").write_text(json.dumps({"node_id": node, "empty": True}))
        out = subprocess.run([sys.executable, "-c", code, str(GEN)], cwd=REPO, capture_output=True, text=True,
                             env=env, check=True).stdout
        return json.loads(out.strip().splitlines()[-1])

    old_ids = {"attempt_id": "iris-sg03c-source-001", "policy_id": "iris-sg03c-source-001",
               "reservation_id": "iris-sg03c-reservation-001"}
    used = json.loads((REPO / "outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03C-c/SG03C/node-created.json").read_text())
    stale = checks(old_ids, used["node_id"])             # a superseded take's ids and its canvas node
    assert stale["bound_ids_match_approval"] is False and stale["fresh_canvas_node"] is False
    fresh = checks(value["bound_ids"], "node_dryrunsg03cd1")
    assert fresh["bound_ids_match_approval"] is True and fresh["fresh_canvas_node"] is True
    assert fresh["bound_matches_approval"] is True


def test_cut_resealing_ignores_plays_but_not_the_window(tmp_path):
    C.cut("SG03", out=tmp_path)
    book = tmp_path / "windows.json"
    value = json.loads(book.read_text())
    value["windows"]["SG03"]["plays"] = [44.9422, 50.933]          # the edit's span moved (s012 split at 48.17)
    book.write_text(json.dumps(value))
    assert C.cut("SG03", out=tmp_path)["sha256"] == value["windows"]["SG03"]["sha256"]
    assert json.loads(book.read_text())["windows"]["SG03"]["plays"] == [44.9422, 49.087]
    value = json.loads(book.read_text())
    value["windows"]["SG03"]["song_window"] = [44.9, 50.933]
    book.write_text(json.dumps(value))
    with pytest.raises(C.Refused, match="already seals another SG03 window"):
        C.cut("SG03", out=tmp_path)


def test_round2_approvals_shape(tmp_path):
    """Round 2: two takes each for SG04 (p013-w1, sealed vocal) and MO07 (p014-w1), round2.html, 4k, 400 CRD, fresh ids."""
    page = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/round2.html"
    text = (REPO / page).read_text(encoding="utf-8")
    assert SG04_PROMPT in text and MO07_PROMPT in text
    plates = {"SG04": ("outputs/ai-city-takeover/ep01/v4/board/plates/p013-w1.png",
                       "2f159721e0da2b9e2247a32fadd14ec79b3628152c911f07cee5c2c4dd1f3f21"),
              "MO07": ("outputs/ai-city-takeover/ep01/v4/board/plates/p014-w1.png",
                       "db997e4fe7d1704f96605bbfd4ad07dce38fac0e4fb345e8b9cb522775037950")}
    ids = []
    for unit, mode, prompt in (("SG04", "multimodal", SG04_PROMPT),):     # MO07: superseded by the strap fix
        for n in (1, 2):
            (target, value), = E.v4r1_approvals("q", "s013 用 b、s014 用 c，拍 (Recommended)", "2026-11-19T17:13:30Z",
                                                 pilot=tmp_path, which=f"{unit.lower()}-r2-{n}").items()
            assert target == tmp_path / f"sd-{unit}-r2-{n}" / "preview-approval.json" and not target.exists()
            path, digest = plates[unit]
            artifacts = [{"path": path, "sha256": digest, "role": f"{unit} {U.APPROVAL_ROLE[mode]}"}]
            if mode == "multimodal":
                vocal = "outputs/ai-city-takeover/ep01/v4/pilot/audio/SG04.wav"
                assert sha(vocal) == "055dd8719d0d773173c351b1d7e9d25ca6f3760957e4b6f3071195a1055afd91"
                artifacts.append({"path": vocal, "sha256": sha(vocal), "role": "SG04 vocal"})
            assert sha(path) == digest and value["preview_artifacts"] == artifacts
            assert value["preview_page"] == {"path": page, "sha256": sha(page)}
            assert (value["generation"]["mode"], value["generation"]["seconds"], value["generation"]["resolution"]) == (
                mode, 5, "4k")
            assert value["budget"] == {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 400,
                                       "cumulative_CRD": 400}
            assert value["prompts"][unit]["text"] == prompt
            replaced = f"outputs/ai-city-takeover/ep01/v4/pilot/sd-{unit}/preview-approval.json"
            assert value["replaces_approval"] == {"path": replaced, "sha256": sha(replaced)}
            tag = f"iris-{unit.lower()}-r2-{n}"
            assert value["bound_ids"] == {"attempt_id": f"{tag}-source-001", "policy_id": f"{tag}-source-001",
                                          "reservation_id": f"{tag}-reservation-001"}
            assert value["takes"]["folders"] == [f"sd-{unit}-r2-1", f"sd-{unit}-r2-2"]
            assert value["takes"]["this_take"] == f"sd-{unit}-r2-{n}"
            ids += value["bound_ids"].values()
    assert len(set(ids)) == 4
    per_set = [set(row["bound_ids"].values()) for cfg in E.SETS.values() for row in cfg["rows"].values()
               if row.get("bound_ids")]
    assert sum(map(len, per_set)) == len(set().union(*per_set))      # no two sets share an id
    for unit in ("SG04", "MO07"):                        # the excerpt (L1) approvals for these clips are superseded
        with pytest.raises(E.Refused, match="superseded by round 2"):
            E.approvals("q", "原话", "2026-11-17T08:00:00+00:00", [unit], pilot=tmp_path)


# ---------------------------------------------------------------- opening s001-s010 (2026-11-20, pilot/opening)
OPENING = REPO / "outputs/ai-city-takeover/ep01/v4/pilot/opening/preview-inputs.json"   # 「按页面拍 (Recommended)」
RUNBOOK = REPO / "outputs/ai-city-takeover/ep01/v4/pilot/opening/RUNBOOK.md"
OPENING_NEW_CLIPS = {"s003": "MO19", "s005": "MO20", "s009": "MO21"}       # plate3d stills turned into motion clips
# 2026-11-20: MO21's first frame is the user-approved fix OP09-fix-c (plate p009-w1b, only the ear region changed; the original
# p009-w1 / OP09-a stays in preview-inputs.json and in the superseded approvals); its approval template is the fix template.
OPENING_FIX_TEMPLATES = {"MO21": REPO / "outputs/ai-city-takeover/ep01/v4/pilot/opening/MO21-fix-approval.template.json"}
OPENING_FIX_FRAME = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/OPEN/OP09-fix-c.png"
OPENING_ROWS = {OPENING_NEW_CLIPS.get(row["shot"], row["unit"]): row
                for row in json.loads(OPENING.read_text(encoding="utf-8"))["units"]}


def runbook_template(kind: str, unit: str) -> dict:
    """The exact JSON template RUNBOOK.md gives the main session for this unit's o-1 take."""
    found = re.findall(rf"<!-- {kind}:{unit} -->\n[^\n]*\n\n```json\n(.*?)\n```", RUNBOOK.read_text(encoding="utf-8"), re.S)
    assert len(found) == 1, (kind, unit)
    return json.loads(found[0])


def approval_template(unit: str) -> dict:
    """The o-1 approval template for this unit: the RUNBOOK's, or the fix template of a unit whose first frame was replaced."""
    if unit not in OPENING_FIX_TEMPLATES:
        return runbook_template("approval", unit)
    value = json.loads(OPENING_FIX_TEMPLATES[unit].read_text(encoding="utf-8"))
    assert len(value.pop("_template_notes")) == 2
    return value


def take(value: dict, n: int) -> dict:
    """The RUNBOOK's documented o-1 → o-n edits (approval: unit_group, bound_ids, takes.this_take; bound: task,
    preview_approval, the three ids); every other field stays as the template has it."""
    out = json.loads(json.dumps(value, ensure_ascii=False))
    swap = lambda text: text.replace("-o-1", f"-o-{n}").replace("opening o-1", f"opening o-{n}")
    for key in ("unit_group", "task", "preview_approval", "attempt_id", "policy_id", "reservation_id"):
        if key in out:
            out[key] = swap(out[key])
    if "bound_ids" in out:
        out["bound_ids"] = {k: swap(v) for k, v in out["bound_ids"].items()}
    if "takes" in out:
        out["takes"]["this_take"] = swap(out["takes"]["this_take"])
    return out


def placeholders(value) -> list:
    if isinstance(value, dict):
        return [x for v in value.values() for x in placeholders(v)]
    if isinstance(value, list):
        return [x for v in value for x in placeholders(v)]
    return [value] if isinstance(value, str) and value.startswith("<") else []


def test_opening_inputs_are_the_board_plates_and_the_specs():
    """Each approved first frame is the board plate byte for byte; mode, seconds and required phrases agree with the
    approved prompt; s003 / s005 / s009 are 4 s motion clips from their cut."""
    inputs = json.loads(OPENING.read_text(encoding="utf-8"))
    source = (REPO / inputs["source_prompt_file"]).read_text(encoding="utf-8")
    assert sha(inputs["source_prompt_file"]) == inputs["source_prompt_file_sha256"]
    board = json.loads((REPO / U.BOARD).read_bytes())
    shots = {s["id"]: s for s in board["shots"]}
    assert list(OPENING_ROWS) == ["MO01", "MO02", "MO19", "SG01", "MO20", "MO03", "MO04", "SG02", "MO21", "MO05"]
    for unit, row in OPENING_ROWS.items():
        spec, shot = U.SPECS[unit], shots[row["shot"]]
        clip = next(c for c in board["clips"] if c["clip"] == unit)
        plate = f"p{row['shot'][1:]}-w1" + ("b" if unit in OPENING_FIX_TEMPLATES else "")
        assert shot["plate"] == clip["start_frame"] == clip["plate"] == plate and shot["clip"] == unit
        assert spec["image"][1] == U.PLATES + plate + ".png" and spec["look"] == "W1"
        if unit in OPENING_FIX_TEMPLATES:             # replaced first frame: the plate is the fix, the row still names the old one
            assert sha(spec["image"][1]) == sha(OPENING_FIX_FRAME) == spec["plate_sha256"] != row["first_frame"]["sha256"]
            assert sha(row["first_frame"]["path"]) == row["first_frame"]["sha256"]
        else:
            assert sha(spec["image"][1]) == sha(row["first_frame"]["path"]) == row["first_frame"]["sha256"] == spec["plate_sha256"]
        assert (row["mode"], row["seconds"]) == (spec["input_mode"], spec["duration"]) == (
            spec["input_mode"], spec["generation"]["seconds"])
        assert hashlib.sha256(row["prompt"].encode()).hexdigest() == row["prompt_sha256"] and row["prompt"] in source
        assert U.prompt_language_ok(spec, row["prompt"])
        literals = [spec["image"][4], *spec["intent"]["open_event"], *spec["intent"]["close_event"], *spec["intent"]["natural"]]
        assert 6 <= len(set(literals)) == len(literals) <= 7 and [x for x in literals if x not in row["prompt"]] == []
        if spec["input_mode"] == "multimodal":
            assert {"逐字精确同步", "嘴前没有任何遮挡"} <= set(literals)
            assert row["vocal"]["path"] == spec["audio"]["path"] and sha(row["vocal"]["path"]) == row["vocal"]["sha256"]
        if row["shot"] in OPENING_NEW_CLIPS:
            assert shot["motion_tier"] == clip["tier"] == "motion"
            assert clip["window"] == {"t0": shot["t0"], "t1": round(shot["t0"] + 4.0, 3)} and clip["seconds"] == 4.0
            assert clip["plays"] == {"t0": shot["t0"], "t1": shot["t1"]} and clip["used_by"] == [row["shot"]]
    used = {json.loads(b.read_text()).get(k) for b in (REPO / "outputs/ai-city-takeover/ep01/v4/pilot").glob(
        "sd-*/*/operator-bound.json") if "-o-" not in b.parent.parent.name for k in ("attempt_id", "policy_id", "reservation_id")}
    ours = {v for unit in OPENING_ROWS for n in (1, 2)
            for v in take(approval_template(unit), n)["bound_ids"].values()}
    assert len(ours) == 40 and not ours & used          # fresh ids, never a superseded take's


@pytest.mark.parametrize("n", [1, 2])
@pytest.mark.parametrize("unit", list(OPENING_ROWS))
def test_opening_runbook_templates_pass_draft_materialize_and_lint(lane, monkeypatch, capsys, unit, n):
    """The RUNBOOK approval / profile / bound templates, with only their placeholders filled, draft, resolve the
    approved 4k request and pass every lint check for both takes (tmp lane; nothing is written under the repo)."""
    monkeypatch.setattr(U, "VOCALS", "outputs/ai-city-takeover/ep01/v4/pilot/audio/windows.json")   # sealed SG01 / SG02
    row, spec = OPENING_ROWS[unit], U.SPECS[unit]
    value = take(approval_template(unit), n)
    if unit in OPENING_FIX_TEMPLATES:                 # the fix approval seals the new frame and names the approval it replaces
        assert [(a["path"], a["sha256"]) for a in value["preview_artifacts"]] == [(spec["image"][1], spec["plate_sha256"])]
        old = value["replaces_approval"]
        assert old["path"].endswith("sd-MO21-o-1/preview-approval.superseded-2026-11-20.json") and sha(old["path"]) == old["sha256"]
        assert sha(old["replaced_first_frame"]["path"]) == old["replaced_first_frame"]["sha256"] == row["first_frame"]["sha256"]
    assert sorted(placeholders(value)) == sorted([value["question"], value["user_quote"], value["approved_at"]])
    value |= {"question": "q", "user_quote": "按页面拍 (Recommended)", "approved_at": "2026-11-20T19:16:00Z"}
    assert value["prompts"][unit]["text"] == row["prompt"] and value["generation"] == spec["generation"]
    assert value["takes"]["this_take"] == f"sd-{unit}-o-{n}" and value["bound_ids"]["attempt_id"] == (
        f"iris-{unit.lower()}-o-{n}-source-001") and value["takes"]["folders"] == [f"sd-{unit}-o-1", f"sd-{unit}-o-2"]
    approve(lane, value)
    U.draft(unit)
    node = f"node_dryrunopen{unit.lower()}o{n}"
    profile = runbook_template("profile", unit) | {"node_id": node}
    assert placeholders(profile) == []
    path = lane / unit / "profile.json"
    path.write_text(json.dumps(profile))
    U.materialize(unit, path)
    capsys.readouterr()
    U.show(unit)
    request = json.loads(capsys.readouterr().out)
    assert (request["model"], request["input_mode"], request["seconds"], request["resolution"], request["aspect"],
            request["prompt"]) == ("seedance_2.0_vip", spec["input_mode"], spec["duration"], "4k", "16:9", row["prompt"])
    assert [b["asset_sha256"] for b in request["image_bindings"]] == [spec["plate_sha256"]]
    assert [b["asset_sha256"] for b in request["media_bindings"]] == (
        [row["vocal"]["sha256"]] if spec["input_mode"] == "multimodal" else [])
    bound = take(runbook_template("bound", unit), n)
    assert bound["preview_approval"] == f"outputs/ai-city-takeover/ep01/v4/pilot/sd-{unit}-o-{n}/preview-approval.json"
    bound |= {"user_quote": value["user_quote"], "preview_approval": str(lane / "preview-approval.json"),
              "issued_at": "2026-11-20T19:30:00+00:00", "expires_at": "2026-11-20T22:30:00+00:00"}
    assert placeholders(bound) == []
    (lane / unit / "operator-bound.json").write_text(json.dumps(bound, ensure_ascii=False))
    (lane / unit / "node-created.json").write_text(json.dumps({"node_id": node, "empty": True}))
    (lane / "continuity-report.json").write_text(json.dumps({"units": {unit: {"verdict": "ready"}}}))
    code = "import json, sys; sys.path.insert(0, sys.argv[1]); import lint; print(json.dumps(lint.lint(sys.argv[2])['checks']))"
    env = {k: v for k, v in os.environ.items() if k not in {"SD_PILOT", "SD_UNITS"}} | {
        "SD_TRIAL": str(lane), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONWARNINGS": "ignore"}
    out = subprocess.run([sys.executable, "-c", code, str(GEN), unit], cwd=REPO, capture_output=True, text=True, env=env,
                         check=True).stdout
    checks = json.loads(out.strip().splitlines()[-1])
    assert [k for k, v in checks.items() if not v] == []


def test_mo07_r4_spec_template_and_approvals():
    """r4 retake: spec required phrases are literal substrings of the r4 prompt (= r3 + one sentence), plate p014-w1c is
    the approved S14r4-a still, the template shapes both takes, the two written approvals carry the exact user quote and
    fresh ids, and each replaces the r3-1 approval."""
    source = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/s014-r4-seedance.md"
    page = "outputs/ai-city-takeover/ep01/v4/pilot/opening/review-s014r4/index.html"
    plate = "outputs/ai-city-takeover/ep01/v4/board/plates/p014-w1c.png"
    block = re.search(r"```prompt\n(.*?)\n```", (REPO / source).read_text(encoding="utf-8"), re.S).group(1)
    assert block == MO07_R4_PROMPT and MO07_R4_PROMPT.count("她始终完整在画面里，头顶不出画。") == 1
    assert sha(plate) == sha("outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/S14r4/a.png") == (
        "ae34b54393afe1df4e15f35326de17752734af1f3661b2c4a307adec89f74374")
    # r4 is history since r5 (same plate, new action sentences); the live spec is checked by the r5 test.
    spec = {"generation": {"model": "seedance_2.0_vip", "mode": "first_frame", "seconds": 5, "resolution": "4k",
                           "aspect": "16:9", "audio": None}}
    template = json.loads(MO07_R4_TEMPLATE.read_text(encoding="utf-8"))
    assert len(template.pop("_template_notes")) == 3
    assert sorted(placeholders(template)) == sorted([template["question"], template["user_quote"], template["approved_at"]])
    old = "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r3-1/preview-approval.json"
    ids = []
    for n in (1, 2):
        value = json.loads((REPO / f"outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r4-{n}/preview-approval.json").read_text(
            encoding="utf-8"))
        assert placeholders(value) == [] and value["user_quote"] == "用 a 拍 (Recommended)"
        assert value["question"].startswith("审看页：http://127.0.0.1:8769/pilot/opening/review-s014r4/index.html")
        assert "她始终完整在画面里，头顶不出画。" in value["question"] and value["question"].endswith("用 a 拍吗？")
        swap = lambda text: text.replace("-r4-1", f"-r4-{n}")
        expect = {**template, "unit_group": swap(template["unit_group"]),
                  "bound_ids": {k: swap(v) for k, v in template["bound_ids"].items()},
                  "takes": {**template["takes"], "this_take": f"sd-MO07-r4-{n}"},
                  "question": value["question"], "user_quote": value["user_quote"], "approved_at": value["approved_at"]}
        assert value == expect
        assert value["preview_page"] == {"path": page, "sha256": sha(page)}
        assert value["prompt_source"] == {"path": source, "sha256": sha(source)}
        assert value["prompts"]["MO07"] == {"text": MO07_R4_PROMPT,
                                            "sha256": hashlib.sha256(MO07_R4_PROMPT.encode()).hexdigest()}
        assert value["preview_artifacts"] == [{"path": plate, "sha256": sha(plate), "role": "MO07 first frame"}]
        assert value["generation"] == spec["generation"]
        assert value["budget"] == {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 400, "cumulative_CRD": 400}
        assert value["replaces_approval"]["path"] == old and value["replaces_approval"]["sha256"] == sha(old)
        assert value["takes"]["folders"] == ["sd-MO07-r4-1", "sd-MO07-r4-2"]
        ids += value["bound_ids"].values()
    used = {json.loads(b.read_text()).get(k) for b in (REPO / "outputs/ai-city-takeover/ep01/v4/pilot").glob(
        "sd-*/*/operator-bound.json") if "-r4-" not in b.parent.parent.name for k in ("attempt_id", "policy_id", "reservation_id")}
    assert len(set(ids)) == 4 and not set(ids) & used



def test_mo07_r5_spec_template_and_approvals():
    """r5 retake: spec required phrases are literal substrings of the r5 prompt (r4 with the approach removed), plate
    p014-w1c unchanged, the template shapes both takes, the two written approvals carry the exact user quote and fresh
    ids, and each replaces the r4-1 approval."""
    source = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/s014-r5-seedance.md"
    page = "outputs/ai-city-takeover/ep01/v4/pilot/opening/review-s014r5/index.html"
    plate = "outputs/ai-city-takeover/ep01/v4/board/plates/p014-w1c.png"
    block = re.search(r"```prompt\n(.*?)\n```", (REPO / source).read_text(encoding="utf-8"), re.S).group(1)
    assert block == MO07_R5_PROMPT and MO07_R5_PROMPT in (REPO / page).read_text(encoding="utf-8")
    assert sha(plate) == sha("outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/S14r4/a.png") == (
        "ae34b54393afe1df4e15f35326de17752734af1f3661b2c4a307adec89f74374")
    # r5 is history since r6 (same plate, the pager press moved before the turn); the live spec is checked by the r6 test.
    spec = {"generation": {"model": "seedance_2.0_vip", "mode": "first_frame", "seconds": 5, "resolution": "4k",
                           "aspect": "16:9", "audio": None}}
    template = json.loads(MO07_R5_TEMPLATE.read_text(encoding="utf-8"))
    assert len(template.pop("_template_notes")) == 3
    assert sorted(placeholders(template)) == sorted([template["question"], template["user_quote"], template["approved_at"]])
    old = "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r4-1/preview-approval.json"
    ids = []
    for n in (1, 2):
        value = json.loads((REPO / f"outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r5-{n}/preview-approval.json").read_text(
            encoding="utf-8"))
        assert placeholders(value) == [] and value["user_quote"] == "按页面改 prompt 拍 r5 (Recommended)"
        assert value["question"].startswith("审看页：http://127.0.0.1:8769/pilot/opening/review-s014r5/index.html")
        assert value["question"].endswith("怎么做？")
        swap = lambda text: text.replace("-r5-1", f"-r5-{n}")
        expect = {**template, "unit_group": swap(template["unit_group"]),
                  "bound_ids": {k: swap(v) for k, v in template["bound_ids"].items()},
                  "takes": {**template["takes"], "this_take": f"sd-MO07-r5-{n}"},
                  "question": value["question"], "user_quote": value["user_quote"], "approved_at": value["approved_at"]}
        assert value == expect
        assert value["preview_page"] == {"path": page, "sha256": sha(page)}
        assert value["prompt_source"] == {"path": source, "sha256": sha(source)}
        assert value["prompts"]["MO07"] == {"text": MO07_R5_PROMPT,
                                            "sha256": hashlib.sha256(MO07_R5_PROMPT.encode()).hexdigest()}
        assert value["preview_artifacts"] == [{"path": plate, "sha256": sha(plate), "role": "MO07 first frame"}]
        assert value["generation"] == spec["generation"]
        assert value["budget"] == {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 400, "cumulative_CRD": 400}
        assert value["replaces_approval"]["path"] == old and value["replaces_approval"]["sha256"] == sha(old)
        assert value["takes"]["folders"] == ["sd-MO07-r5-1", "sd-MO07-r5-2"]
        ids += value["bound_ids"].values()
    used = {json.loads(b.read_text()).get(k) for b in (REPO / "outputs/ai-city-takeover/ep01/v4/pilot").glob(
        "sd-*/*/operator-bound.json") if "-r5-" not in b.parent.parent.name for k in ("attempt_id", "policy_id", "reservation_id")}
    assert len(set(ids)) == 4 and not set(ids) & used



def test_mo07_r6_spec_template_and_approvals():
    """r6 retake: spec required phrases are literal substrings of the r6 prompt (the pager press before the turn, pager
    and badge kept in front), plate p014-w1c unchanged, the template shapes both takes, the two written approvals carry
    the exact user quote and fresh ids, and each replaces the r5-1 approval."""
    source = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/s014-r6-seedance.md"
    page = "outputs/ai-city-takeover/ep01/v4/pilot/opening/review-s014r6/index.html"
    plate = "outputs/ai-city-takeover/ep01/v4/board/plates/p014-w1c.png"
    block = re.search(r"```prompt\n(.*?)\n```", (REPO / source).read_text(encoding="utf-8"), re.S).group(1)
    assert block == MO07_R6_PROMPT and MO07_R6_PROMPT in (REPO / page).read_text(encoding="utf-8")
    assert sha(plate) == sha("outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/S14r4/a.png") == (
        "ae34b54393afe1df4e15f35326de17752734af1f3661b2c4a307adec89f74374")
    spec = U.SPECS["MO07"]
    literals = [spec["image"][4], *spec["intent"]["open_event"], *spec["intent"]["close_event"], *spec["intent"]["natural"]]
    assert [x for x in literals if x not in MO07_R6_PROMPT] == [] and "她走到走秀台尽头" not in MO07_R6_PROMPT
    assert "一只手按住腰间震动的黑色寻呼机" not in MO07_R6_PROMPT
    assert {"不再往前走", "然后松开手", "寻呼机和工牌一直挂在她身前的腰链上，背对镜头时看不见", "站在原地一个干脆的急转身", "背对镜头朝画面右侧走开，越走越远", "两侧的值班工程师一直低头盯着自己腿上的笔记本电脑",
            "她腰间的寻呼机不亮任何红灯", "她始终完整在画面里，头顶不出画"} <= set(literals)
    assert U.prompt_language_ok(spec, MO07_R6_PROMPT) and spec["look"] == "W1"
    assert (spec["duration"], spec["plate_sha256"], spec["image"][1]) == (5, sha(plate), plate)
    template = json.loads(MO07_R6_TEMPLATE.read_text(encoding="utf-8"))
    assert len(template.pop("_template_notes")) == 3
    assert sorted(placeholders(template)) == sorted([template["question"], template["user_quote"], template["approved_at"]])
    old = "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r5-1/preview-approval.json"
    ids = []
    for n in (1, 2):
        value = json.loads((REPO / f"outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r6-{n}/preview-approval.json").read_text(
            encoding="utf-8"))
        assert placeholders(value) == [] and value["user_quote"] == "按页面拍 r6 (Recommended)"
        assert value["question"].startswith("审看页：http://127.0.0.1:8769/pilot/opening/review-s014r6/index.html")
        assert value["question"].endswith("怎么做？")
        swap = lambda text: text.replace("-r6-1", f"-r6-{n}")
        expect = {**template, "unit_group": swap(template["unit_group"]),
                  "bound_ids": {k: swap(v) for k, v in template["bound_ids"].items()},
                  "takes": {**template["takes"], "this_take": f"sd-MO07-r6-{n}"},
                  "question": value["question"], "user_quote": value["user_quote"], "approved_at": value["approved_at"]}
        assert value == expect
        assert value["preview_page"] == {"path": page, "sha256": sha(page)}
        assert value["prompt_source"] == {"path": source, "sha256": sha(source)}
        assert value["prompts"]["MO07"] == {"text": MO07_R6_PROMPT,
                                            "sha256": hashlib.sha256(MO07_R6_PROMPT.encode()).hexdigest()}
        assert value["preview_artifacts"] == [{"path": plate, "sha256": sha(plate), "role": "MO07 first frame"}]
        assert value["generation"] == spec["generation"]
        assert value["budget"] == {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 400, "cumulative_CRD": 400}
        assert value["replaces_approval"]["path"] == old and value["replaces_approval"]["sha256"] == sha(old)
        assert value["takes"]["folders"] == ["sd-MO07-r6-1", "sd-MO07-r6-2"]
        ids += value["bound_ids"].values()
    used = {json.loads(b.read_text()).get(k) for b in (REPO / "outputs/ai-city-takeover/ep01/v4/pilot").glob(
        "sd-*/*/operator-bound.json") if "-r6-" not in b.parent.parent.name for k in ("attempt_id", "policy_id", "reservation_id")}
    assert len(set(ids)) == 4 and not set(ids) & used


# ---------------------------------------------------------------- s015-s030 (2026-11-22, pilot/s015-030/submit)
S1530 = REPO / "outputs/ai-city-takeover/ep01/v4/pilot/s015-030"
S1530_UNITS = ["SG05", "SG06", "INS16", "SG07", "MO08", "MO09", "MO10", "SG08", "SG09", "MO11", "SG10", "MO12", "MO13", "SG11"]
S1530_ROWS = {row["unit"]: row for row in json.loads((S1530 / "submit/preview-inputs.json").read_text(encoding="utf-8"))["units"]}


S1530_M = ("SG05", "SG06", "SG07", "SG08", "SG09", "SG10", "SG11")
S1530_BOARD_SHA256 = "b5f599322f7f19daea1b7eb1f132bf640fdec4712c1cdf5da097ced5cfbe0107"   # board/shots.json of the last pack build


def s1530_tag(unit: str) -> str:
    """Take-folder tag: n for the first round; m for SG05's retake after its failed Gate and for SG06-SG11 re-windowed by
    the s015 lesson (2026-11-22)."""
    return "p" if unit in ("SG06", "MO12") else "m" if unit in S1530_M else "n"     # p: a retake after a failed Gate


SEALS = ("preview_page", "preview_inputs", "prompt_source")
AUDIT = ("审看页：http://127.0.0.1:8769/pilot/s015-030/audit/index.html", "照页面改 (Recommended)", "2026-11-22T23:03:07Z")


def unsealed(value: dict) -> dict:
    """An approval without the page / inputs / prompt-file shas: the pack is rebuilt after an approval is written (no
    reader checks those three), so a written approval is compared with today's template on everything else."""
    return {k: ({**v, "sha256": None} if k in SEALS else v) for k, v in value.items()}


def s1530_take(unit: str, n: int) -> dict:
    """The unit's <tag>-1 approval template turned into take n as its _template_notes say (placeholders left in)."""
    value = json.loads((S1530 / f"{unit}-approval.template.json").read_text(encoding="utf-8"))
    assert len(value.pop("_template_notes")) == 3
    tag = s1530_tag(unit)
    swap = lambda text: text.replace(f"-{tag}-1", f"-{tag}-{n}")
    value["unit_group"] = swap(value["unit_group"])
    value["bound_ids"] = {k: swap(v) for k, v in value["bound_ids"].items()}
    value["takes"]["this_take"] = swap(value["takes"]["this_take"])
    return value


def test_s1530_pack_is_the_board_plates_the_drafts_and_the_specs():
    """Each first frame is the board plate and the chosen design frame byte for byte; mode, seconds (ceil of the coverage
    unit), prompt (verbatim draft block), required phrases, vocal window and lyric agree with the spec; cost 80 CRD/s."""
    inputs = json.loads((S1530 / "submit/preview-inputs.json").read_text(encoding="utf-8"))
    assert sha(inputs["source_prompt_file"]) == inputs["source_prompt_file_sha256"]
    # the s015-s030 pack is frozen at the board it was last built from (its generation ended 2026-11-23); later segments
    # change the board (s031-s048, 2026-11-24) without touching any s015-s030 shot or clip, which the rows below still check
    assert inputs["board"]["sha256"] == S1530_BOARD_SHA256 and sha(U.BOARD) == U.BOARD_SHA256
    blocks = dict(re.findall(r"^## s\d{3} · (\w+) · .*?\n\n```prompt\n(.*?)\n```",
                             (REPO / inputs["source_prompt_file"]).read_text(encoding="utf-8"), re.S | re.M))
    assert list(blocks) == list(S1530_ROWS) == S1530_UNITS
    board = json.loads((REPO / U.BOARD).read_bytes())
    shots, clips = {s["id"]: s for s in board["shots"]}, {c["clip"]: c for c in board["clips"]}
    coverage = {u["unit_id"]: u for u in json.loads(U.COVERAGE.read_text(encoding="utf-8"))["coverage_units"]}
    windows = json.loads((REPO / U.VOCALS).read_text(encoding="utf-8"))["windows"]
    for unit, row in S1530_ROWS.items():
        spec, clip, shot = U.SPECS[unit], clips[unit], shots[row["shot"]]
        suffix = {"SG09": "-b2", "SG07": "-w2b", "INS16": "-ins16", "MO12": "-b3"}.get(unit, {"W1": "-w1", "B": "-b1"}[spec["look"]])
        # s024 car remade; s017 pickup turned; INS16 is an insert clip of s016 with its own plate (the shot keeps SG06's)
        assert clip["start_frame"] == clip["plate"] == spec["plate"] == f"p{row['shot'][1:]}{suffix}"
        assert clip["used_by"] == [row["shot"]] and (shot["clip"], shot["plate"]) == (
            ("SG06", "p016-w1") if unit == "INS16" else (unit, spec["plate"]))
        assert spec["image"][1] == row["first_frame"]["path"] == U.PLATES + spec["plate"] + ".png"
        assert sha(row["first_frame"]["path"]) == sha(row["first_frame"]["design_frame"]) == spec["plate_sha256"]
        assert (row["mode"], row["seconds"]) == (spec["input_mode"], spec["duration"]) == (
            spec["generation"]["mode"], spec["generation"]["seconds"])
        assert spec["duration"] == math.ceil(coverage[unit]["duration_seconds"]) + spec.get("take_margin_seconds", 0) and spec["input_mode"] == (
            "multimodal" if unit.startswith("SG") else "first_frame")
        assert row["prompt"] == blocks[unit] and hashlib.sha256(row["prompt"].encode()).hexdigest() == row["prompt_sha256"]
        assert U.prompt_language_ok(spec, row["prompt"])
        literals = [spec["image"][4], *spec["intent"]["open_event"], *spec["intent"]["close_event"], *spec["intent"]["natural"]]
        assert row["required_phrases"] == literals and len(set(literals)) == len(literals) >= 6
        assert [x for x in literals if x not in row["prompt"]] == []
        assert (row["est_cost_per_take_CRD"], row["ceiling_per_take_CRD"]) == (
            spec["duration"] * 80, math.ceil(spec["duration"] * 0.8) * 100)
        if spec["input_mode"] == "multimodal":
            assert {"逐字精确同步", "嘴前没有任何遮挡"} <= set(literals)
            assert set(U.MARKERS.findall(row["prompt"])) == {"{{image:0}}", "{{audio:1}}"}
            vocal, window = row["vocal"], windows[spec["audio"]["window"]]
            assert vocal["path"] == spec["audio"]["path"] == window["path"] and sha(vocal["path"]) == vocal["sha256"] == window["sha256"]
            assert window["song_window"] == vocal["song_window_s"] == [clip["window"]["t0"], clip["window"]["t1"]]
            assert vocal["lyric_text"] == spec["dialogue"]["verbatim_text"] == " ".join(clip["words"])
        else:
            assert not U.MARKERS.findall(row["prompt"]) and "vocal" not in row
    assert clips["SG10"]["window"] == {"t0": 109.56, "t1": 116.123}      # m: 0.3 s before "I'm" 109.86; covers the s026a 109.72 cut
    # SG05 m: 8 s; SG06-SG11 m: +1 s each, SG09 +2 s (main session: a full second over its 4.543 s window); INS16 4 s
    assert inputs["total_seconds_per_take_set"] == 87 and inputs["estimated_total_CRD"] == 87 * 80 * 2 == 13920
    assert inputs["ceiling_total_CRD"] == 15200
    for still in inputs["stills"]:                      # stills and inserts are not generated
        assert still["shot"] in ("s021", "s023", "s030") and shots[still["shot"]]["clip"] is None
        assert sha(still["plate"]) == still["sha256"] and (still["design_frame"] is None or sha(still["design_frame"]) == still["sha256"])


def test_s1530_sg09_mo13_revision_and_their_approvals():
    """2026-11-22 after the continuity check: s024 plate p024-b2 (= P024R/b, 「用 b (Recommended)」) and the s028 prompt
    of the issues page (「按问题页改 (Recommended)」). Both takes' approvals are the current template with the question,
    quote and time of the answer that made the change; no placeholder left."""
    assert S1530_ROWS["SG09"]["first_frame"]["design_frame"].endswith("design/S15-30/P024R/b.png")
    assert U.SPECS["SG09"]["plate_sha256"] == "d13da23ff4ecb4079a855d78ce19fe7c786eec9fbe38bec04700c5b7765b738f"
    mo13 = S1530_ROWS["MO13"]
    # the issues-page text, as amended by the pre-shoot audit (turn to frame right; no bag; blank pager screen)
    assert mo13["prompt"] == ("镜头固定不动。她转身朝画面右侧，沿台阶往上走，走到一半低头看一眼身前腰带上的黑色寻呼机，寻呼机的液晶屏发出"
                              "灰绿色的光，再接着往上走，从画面右上方走出去。背后没有包，也没有任何挂件。寻呼机屏幕只有灰绿底光，没有数字和字。"
                              "池底干燥，没有水。除了她左耳耳挂上的小红灯，画面里没有任何红色。画面中不得出现任何文字。")
    assert not [x for x in mo13["required_phrases"] if "长焦" in x or "跳板中段" in x]
    answers = {"SG09": ("审看页：http://127.0.0.1:8769/pilot/s015-030/p024r/index.html", "用 b (Recommended)",
                        "2026-11-22T18:03:19Z"),
               "MO13": AUDIT}                       # MO13 n now carries the later audit decision (its prompt changed again)
    for unit, (question, quote, at) in answers.items():
        for n in (1, 2):
            value = json.loads((S1530.parent / f"sd-{unit}-n-{n}/preview-approval.json").read_text(encoding="utf-8"))
            assert value["question"].startswith(question) and (value["user_quote"], value["approved_at"]) == (quote, at)
            assert not placeholders(value)
            if unit == "MO13":
                assert unsealed(value) == unsealed(s1530_take(unit, n) | {k: value[k] for k in ("question", "user_quote", "approved_at")})
            else:                                   # SG09 n is replaced by m (new vocal window); its p024-b2 approval stays
                assert value["preview_artifacts"][0]["sha256"] == U.SPECS["SG09"]["plate_sha256"]


def test_s1530_sg05_retake_m():
    """2026-11-22 SG05 Gate FAIL on n-1 / n-2, 「按页面重拍 (Recommended)」 on gate/sg05: same plate; vocal SG05m.wav cut from
    58.70-65.666 (the whole "Ten oh two" phrase; SG05.wav, the n cut, kept); an 8 s take (window + 1 s); the parked-cars
    sentence required; m-1 / m-2 approvals with fresh ids that replace the n-1 approval and name the Gate reasons."""
    spec, row = U.SPECS["SG05"], S1530_ROWS["SG05"]
    windows = json.loads((REPO / U.VOCALS).read_text(encoding="utf-8"))["windows"]
    assert windows["SG05"]["sha256"] == "848c964e0e8262ece595d4de0d640de0ddefe49c63ddcf471b3937d36b1adca0" == sha(windows["SG05"]["path"])
    assert windows["SG05m"]["song_window"] == [58.7, 65.666] and spec["audio"]["path"].endswith("pilot/audio/SG05m.wav")
    assert (spec["duration"], spec["take_margin_seconds"], row["ceiling_per_take_CRD"]) == (8, 1, 700)
    words = [w for line in json.loads((REPO / "outputs/ai-city-takeover/ep01/v4/song/timing/words.json").read_text())["lines"]
             for w in line["words"] if 58.7 <= w["start"] < 65.666]
    assert " ".join(w["text"] for w in words) == spec["dialogue"]["verbatim_text"] and words[0]["text"] == "Ten"
    assert (spec["dialogue"]["start_seconds"], spec["dialogue"]["end_seconds"]) == (
        round(words[0]["start"] - 58.7, 2), round(max(w["end"] for w in words) - 58.7, 2))
    assert "街上的车灯只有白色和琥珀色。街上只有停着的车，没有行驶的车。" in row["prompt"]
    assert "街上只有停着的车，没有行驶的车" in row["required_phrases"]
    replaced = "outputs/ai-city-takeover/ep01/v4/pilot/sd-SG05-n-1/preview-approval.json"
    for n in (1, 2):
        value = json.loads((S1530.parent / f"sd-SG05-m-{n}/preview-approval.json").read_text(encoding="utf-8"))
        assert value["question"].startswith("审看页：http://127.0.0.1:8769/pilot/s015-030/gate/sg05/index.html")
        assert (value["user_quote"], value["approved_at"]) == ("按页面重拍 (Recommended)", "2026-11-22T18:41:14Z")
        assert unsealed(value) == unsealed(s1530_take("SG05", n) | {k: value[k] for k in ("question", "user_quote", "approved_at")})
        assert value["replaces_approval"]["path"] == replaced and value["replaces_approval"]["sha256"] == sha(replaced)
        assert "Gate 不通过" in value["replaces_approval"]["reason"] and not placeholders(value)
    used = {json.loads(b.read_text()).get(k) for b in (REPO / "outputs/ai-city-takeover/ep01/v4/pilot").glob(
        "sd-*/*/operator-bound.json") if not b.parent.parent.name.startswith("sd-SG05-m-")
        for k in ("attempt_id", "policy_id", "reservation_id")}
    assert not {f"iris-sg05-m-{n}-{k}-001" for n in (1, 2) for k in ("source", "reservation")} & used


def test_s1530_sg06_sg11_rewindowed_m():
    """2026-11-22 「照 s015 的教训改 (Recommended)」: each vocal window starts at least ~0.3 s before the phrase's first word
    (0.24 s for SG09, bounded by "guests."; SG08 kept, its plays start inside "instead." and 0.3 s earlier is inside "apps"),
    the take is the old seconds + 1, plays and prompts unchanged, old wavs untouched; m-1 / m-2 approvals replace n-1."""
    old = {"SG06": (65.666, 6, "13e67197524e8fb79bdec74725b6710df33dcadd0b7f83d7f384f86a71c68cb1"),
           "SG07": (71.1808, 8, "95e8b29ecb421ccaf057c447b9b7d8be1ed4f4d2a671bd991e45a0d61580d697"),
           "SG08": (94.507, 7, "e56666227990e6fe0463d3ee0d668dda53423aeb43dd25c6417600962e2d8ec7"),
           "SG09": (103.183, 4, "0e15e4286ad2f7a5fb2bd3b8390cd41c501262540ebd4c0d07ef88cd9b672939"),
           "SG10": (109.7027, 7, "1f1ff6544d88b1c6167bb0ced95457e287c56f51f11b557f06d2f7b6a56f6d0a"),
           "SG11": (125.7244, 6, "7b556199a076a35a674c1f12ec8a5fec42c1ec1521c47c16688819fb2d8e6699")}
    new_t0 = {"SG06": 65.517, "SG07": 71.1808, "SG08": 94.507, "SG09": 102.64, "SG10": 109.56, "SG11": 125.608}
    board = json.loads((REPO / U.BOARD).read_bytes())
    clips = {c["clip"]: c for c in board["clips"]}
    windows = json.loads((REPO / U.VOCALS).read_text(encoding="utf-8"))["windows"]
    words = [w for line in json.loads(C.WORDS.read_text())["lines"] for w in line["words"]]
    question = ("还有 6 条唱段没拍", "照 s015 的教训改 (Recommended)", "2026-11-22T19:38:19Z")
    noturn = ("审看页：http://127.0.0.1:8769/pilot/s015-030/gate/sg06/index.html", "按页面重拍，唱段不转身 (Recommended)",
              "2026-11-22T20:44:44Z")
    assert U.SPECS["SG07"]["plate_sha256"] == "0a75579f7d5b709d4b81499470f61e5531e5d9cf465570bdbf761204f56b0e60"
    assert S1530_ROWS["SG07"]["first_frame"]["design_frame"].endswith("design/S15-30/CARS/p017-w2b.png")
    for unit, (t0_old, secs_old, wav_sha) in old.items():
        spec, clip, row = U.SPECS[unit], clips[unit], S1530_ROWS[unit]
        assert sha(f"outputs/ai-city-takeover/ep01/v4/pilot/audio/{unit}.wav") == windows[unit]["sha256"] == wav_sha
        assert clip["window"]["t0"] == new_t0[unit] and spec["duration"] == secs_old + (2 if unit == "SG09" else 1) == row["seconds"]
        assert spec["duration"] - math.ceil(clip["seconds"]) == spec["take_margin_seconds"] == 1
        first = next(w for w in words if w["start"] >= clip["window"]["t0"])
        lead = first["start"] - clip["window"]["t0"]
        assert lead >= 0.3 - 1e-6 or (unit, round(lead, 3)) in {("SG09", 0.242), ("SG08", 0.05)}
        assert clip["plays"]["t0"] >= clip["window"]["t0"] and spec["audio"]["window"] == (unit + "m" if t0_old != new_t0[unit] else unit)
        assert row["ceiling_per_take_CRD"] == math.ceil(spec["duration"] * 0.8) * 100
        for n in (1, 2):
            value = json.loads((S1530.parent / f"sd-{unit}-m-{n}/preview-approval.json").read_text(encoding="utf-8"))
            if unit == "SG06":                                 # shot and failed its Gate; replaced by p (no-turn test below)
                assert value["question"].startswith(question[0]) and value["bound_ids"]["attempt_id"] == f"iris-sg06-m-{n}-source-001"
                continue
            # each approval carries the latest decision on its unit: SG07 no exit, SG08-SG11 the pre-shoot audit
            asked = noturn if unit == "SG07" else AUDIT if unit in ("SG08", "SG09", "SG10", "SG11") else question
            assert value["question"].startswith(asked[0]) and (value["user_quote"], value["approved_at"]) == asked[1:]
            assert unsealed(value) == unsealed(s1530_take(unit, n) | {k: value[k] for k in ("question", "user_quote", "approved_at")})
            replaced = f"outputs/ai-city-takeover/ep01/v4/pilot/sd-{unit}-n-1/preview-approval.json"
            assert value["replaces_approval"]["path"] == replaced and value["replaces_approval"]["sha256"] == sha(replaced)
            assert value["replaces_approval"]["reason"].startswith("人声窗口与余量按 s015 教训调整")
            assert not placeholders(value)


def test_s1530_no_turn_in_sung_takes():
    """2026-11-22 「按页面重拍，唱段不转身 (Recommended)」 on gate/sg06: SG06 ends standing in place looking at the camera, SG07
    only straightens up; no exit is required or written. SG06 p-1 / p-2 replace the failed m-1 approval; SG07 m approvals
    carry this decision and name all three (window, car, no exit)."""
    rows = S1530_ROWS
    assert "唱最后一句时她松开手，听筒顺着金属电话线垂下去来回晃，她仍站在原地看着镜头。" in rows["SG06"]["prompt"]
    assert rows["SG07"]["prompt"].count("然后直起身。") == 1 and "走出画面" not in rows["SG07"]["prompt"]
    for unit in ("SG06", "SG07"):
        assert not [x for x in rows[unit]["required_phrases"] if "走开" in x or "走出" in x]
        assert "走开" not in U.SPECS[unit]["intent"]["close"] and "走出" not in U.SPECS[unit]["intent"]["close"]
    assert "她仍站在原地看着镜头" in rows["SG06"]["required_phrases"] and "然后直起身" in rows["SG07"]["required_phrases"]
    spec = U.SPECS["SG06"]
    assert (spec["duration"], spec["audio"]["window"], rows["SG06"]["ceiling_per_take_CRD"]) == (7, "SG06m", 600)
    asked = ("审看页：http://127.0.0.1:8769/pilot/s015-030/gate/sg06/index.html", "按页面重拍，唱段不转身 (Recommended)",
             "2026-11-22T20:44:44Z")
    replaced = "outputs/ai-city-takeover/ep01/v4/pilot/sd-SG06-m-1/preview-approval.json"
    for n in (1, 2):
        value = json.loads((S1530.parent / f"sd-SG06-p-{n}/preview-approval.json").read_text(encoding="utf-8"))
        assert value["question"].startswith(asked[0]) and (value["user_quote"], value["approved_at"]) == asked[1:]
        assert unsealed(value) == unsealed(s1530_take("SG06", n) | {k: value[k] for k in ("question", "user_quote", "approved_at")})
        assert value["bound_ids"]["attempt_id"] == f"iris-sg06-p-{n}-source-001" and not placeholders(value)
        assert value["replaces_approval"]["path"] == replaced and value["replaces_approval"]["sha256"] == sha(replaced)
        assert "Gate 不通过" in value["replaces_approval"]["reason"]
        sg07 = json.loads((S1530.parent / f"sd-SG07-m-{n}/preview-approval.json").read_text(encoding="utf-8"))
        assert all(x in sg07["replaces_approval"]["reason"] for x in ("s015", "p017-w2b", "然后直起身"))


def test_s1530_ins16_no_person_insert():
    """2026-11-22 「用 d 拍 (Recommended)」 on ins16: the s016 handset insert, no person (4 s: the Jimeng minimum). The spec takes unit.py's no-person
    path (iris False: no Character, no identity waiver, no IRIS performance direction); the board clip carries its own
    insert text, which the coverage reads; 4 s first_frame, ceiling 400; the prompt is INS16/prompt.md verbatim."""
    spec, row = U.SPECS["INS16"], S1530_ROWS["INS16"]
    assert (spec["iris"], spec["identity_waiver"], spec["input_mode"], spec["duration"], row["ceiling_per_take_CRD"]) == (
        False, None, "first_frame", 4, 400)       # user saw 3 s; JimengProfile minimum 4 s (main session, 3 -> 4 s)
    assert spec["take_margin_seconds"] == 2 and "4 s" in " ".join(json.loads(
        (S1530 / "INS16-approval.template.json").read_text(encoding="utf-8"))["decision_notes"])
    assert "character_directions" not in spec["performance"] and "红" not in spec["scene"]["mood"]
    book = (REPO / "outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/S15-30/INS16/prompt.md").read_text(encoding="utf-8")
    assert row["prompt"] == re.search(r"```prompt\n(.*?)\n```", book, re.S).group(1) and "耳挂" not in row["prompt"]
    assert sha(row["first_frame"]["path"]) == "0cfbef8556488bc840ee8002ec5c75b87cbb7d8628957f4db2df6f195479b0f0"
    clip = next(c for c in json.loads((REPO / U.BOARD).read_bytes())["clips"] if c["clip"] == "INS16")
    assert clip["plays"] == {"t0": 69.4, "t1": 71.1808} and clip["tier"] == "motion" and "insert" in clip
    unit = next(u for u in json.loads(U.COVERAGE.read_text(encoding="utf-8"))["coverage_units"] if u["unit_id"] == "INS16")
    assert unit["visible_change"] == clip["insert"]["action"] and unit["shot_scale"] == "close_up"
    for n in (1, 2):
        value = json.loads((S1530.parent / f"sd-INS16-n-{n}/preview-approval.json").read_text(encoding="utf-8"))
        assert value["question"].startswith("审看页：http://127.0.0.1:8769/pilot/s015-030/ins16/index.html")
        assert (value["user_quote"], value["approved_at"]) == ("用 d 拍 (Recommended)", "2026-11-22T22:06:49Z")
        assert unsealed(value) == unsealed(s1530_take("INS16", n) | {k: value[k] for k in ("question", "user_quote", "approved_at")})
        assert value["identity_waivers"] == [] and not placeholders(value)


def test_s1530_pre_shoot_audit():
    """2026-11-22 「照页面改 (Recommended)」 on audit: every new sentence of the page is in its unit's prompt and the deleted
    ones are gone; the approvals of MO09 / MO10 / MO11 / MO13 (n) and SG08-SG11 (m) carry this decision with their ids;
    MO12's approval waits for its new first frame."""
    page = (S1530 / "audit/index.html").read_text(encoding="utf-8")
    shots = {"s019": "MO09", "s020": "MO10", "s022": "SG08", "s024": "SG09", "s025": "MO11", "s026": "SG10", "s027": "MO12",
             "s028": "MO13", "s029": "SG11"}
    rows = re.findall(r"<tr><td>(s\d{3})[^<]*(?:<br><b>[^<]*</b>)?</td>(.*?)</tr>", page, re.S)
    assert [s for s, _ in rows] == list(shots)
    for shot, body in rows:
        prompt = S1530_ROWS[shots[shot]]["prompt"]
        for old in re.findall(r'<span class="o">(.*?)</span>', body) if shot != "s027" else ():
            assert not [x for x in old.split("…") if x and x in prompt], (shot, old)
        for new in re.findall(r'<span class="n">(.*?)</span>', body):
            parts = [x for x in new.removeprefix("加：").split("…") if x]
            if shot == "s027":                              # replaced by the back-view prompt (see the MO12 back-view test)
                continue
            if shot == "s019":                              # later decision: 「她的头顶始终不出画。」 (see the MO09 test)
                parts = [x.replace("她始终完整在画面里，头顶不出画。", "她的头顶始终不出画。") for x in parts]
            if shot == "s020":                              # page lists two fragments; each is in the prompt
                parts = [x for part in parts for x in part.split("；梯子上的工人") if x]
            assert [x for x in parts if x.rstrip("。") not in prompt] == [], (shot, parts)
    for unit, tag in (("MO10", "n"), ("MO11", "n"), ("MO13", "n"), ("SG08", "m"), ("SG09", "m"), ("SG10", "m"),
                      ("SG11", "m")):
        for n in (1, 2):
            value = json.loads((S1530.parent / f"sd-{unit}-{tag}-{n}/preview-approval.json").read_text(encoding="utf-8"))
            assert value["question"].startswith(AUDIT[0]) and (value["user_quote"], value["approved_at"]) == AUDIT[1:]
            assert unsealed(value) == unsealed(s1530_take(unit, n) | {k: value[k] for k in ("question", "user_quote", "approved_at")})
            assert value["bound_ids"]["attempt_id"] == f"iris-{unit.lower()}-{tag}-{n}-source-001" and not placeholders(value)
    # MO12 n (p027-b2, 「用 a」) was shot and failed its Gate; its approvals stay as history (the back-view p take replaces it)
    for n in (1, 2):
        value = json.loads((S1530.parent / f"sd-MO12-n-{n}/preview-approval.json").read_text(encoding="utf-8"))
        assert value["question"].startswith("审看页：http://127.0.0.1:8769/pilot/s015-030/p027r/index.html")
        assert (value["user_quote"], value["bound_ids"]["attempt_id"]) == ("用 a (Recommended)", f"iris-mo12-n-{n}-source-001")


def test_s1530_mo09_head_in_frame():
    """2026-11-22 「改成「头顶始终不出画」 (Recommended)」: MO09 asks only that her head stays in frame (the plate cuts her at the
    thighs; "完整" could pull the camera back); the approvals carry this decision and name the audit too."""
    prompt = S1530_ROWS["MO09"]["prompt"]
    assert "她的头顶始终不出画。" in prompt and "完整" not in prompt
    assert "她的头顶始终不出画" in S1530_ROWS["MO09"]["required_phrases"]
    for n in (1, 2):
        value = json.loads((S1530.parent / f"sd-MO09-n-{n}/preview-approval.json").read_text(encoding="utf-8"))
        assert value["question"].startswith("s019（换装）开拍前还有一处要定。")
        assert (value["user_quote"], value["approved_at"]) == ("改成「头顶始终不出画」 (Recommended)", "2026-11-22T23:34:55Z")
        assert unsealed(value) == unsealed(s1530_take("MO09", n) | {k: value[k] for k in ("question", "user_quote", "approved_at")})
        assert value["bound_ids"]["attempt_id"] == f"iris-mo09-n-{n}-source-001" and not placeholders(value)
        assert "照页面改" in value["decision_notes"][0] and "她的头顶始终不出画" in value["decision_notes"][1]


def test_s1530_mo12_back_view():
    """2026-11-23 「A 重做背影首帧再拍 (Recommended)」 then 「用 b (Recommended)」 on p027b: plate p027-b3 (= P027B/b.png, camera
    behind her), prompt = P027B/prompt.md verbatim (walks away, gets smaller; no exit, no turn, no walking at the lens);
    p-1 / p-2 with fresh ids replace the n-1 approval and name the Gate reasons."""
    spec, row = U.SPECS["MO12"], S1530_ROWS["MO12"]
    assert (spec["plate"], spec["plate_sha256"]) == ("p027-b3", "942eac1020263ff3ab6df31411132bae5c781c34a90fb5b2f565424e83b5d88b")
    assert row["first_frame"]["design_frame"].endswith("design/S15-30/P027B/b.png")
    book = (REPO / "outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/S15-30/P027B/prompt.md").read_text(encoding="utf-8")
    assert row["prompt"] == re.search(r"```prompt\n(.*?)\n```", book, re.S).group(1)
    assert "越走越小" in row["required_phrases"] and not [x for x in ("走出", "转身", "朝镜头") if x in row["prompt"]]
    replaced = "outputs/ai-city-takeover/ep01/v4/pilot/sd-MO12-n-1/preview-approval.json"
    for n in (1, 2):
        value = json.loads((S1530.parent / f"sd-MO12-p-{n}/preview-approval.json").read_text(encoding="utf-8"))
        assert value["question"].startswith("审看页：http://127.0.0.1:8769/pilot/s015-030/p027b/index.html")
        assert (value["user_quote"], value["approved_at"]) == ("用 b (Recommended)", "2026-11-23T06:51:04Z")
        assert unsealed(value) == unsealed(s1530_take("MO12", n) | {k: value[k] for k in ("question", "user_quote", "approved_at")})
        assert value["bound_ids"]["attempt_id"] == f"iris-mo12-p-{n}-source-001" and not placeholders(value)
        assert value["replaces_approval"]["path"] == replaced and value["replaces_approval"]["sha256"] == sha(replaced)
        assert "Gate 不通过" in value["replaces_approval"]["reason"] and "decision_notes" not in value


def test_s1530_templates_shape_both_takes_with_fresh_ids():
    page = "outputs/ai-city-takeover/ep01/v4/pilot/s015-030/submit/index.html"
    inputs = "outputs/ai-city-takeover/ep01/v4/pilot/s015-030/submit/preview-inputs.json"
    used = {json.loads(b.read_text()).get(k) for b in (REPO / "outputs/ai-city-takeover/ep01/v4/pilot").glob(
        "sd-*/*/operator-bound.json") if not re.search(r"-[nmp]-\d$", b.parent.parent.name)        # this lane's own takes
        for k in ("attempt_id", "policy_id", "reservation_id")}
    ids = []
    for unit, row in S1530_ROWS.items():
        spec = U.SPECS[unit]
        for n in (1, 2):
            value = s1530_take(unit, n)
            assert sorted(placeholders(value)) == sorted([value["question"], value["user_quote"], value["approved_at"]])
            assert value["preview_page"] == {"path": page, "sha256": sha(page)}
            assert value["preview_inputs"] == {"path": inputs, "sha256": sha(inputs)}
            assert value["prompts"] == {unit: {"text": row["prompt"], "sha256": row["prompt_sha256"]}}
            artifacts = [{"path": spec["image"][1], "sha256": spec["plate_sha256"], "role": f"{unit} {U.APPROVAL_ROLE[spec['input_mode']]}"}]
            if spec.get("audio"):
                artifacts.append({"path": spec["audio"]["path"], "sha256": sha(spec["audio"]["path"]), "role": f"{unit} vocal"})
            assert value["preview_artifacts"] == artifacts and value["generation"] == spec["generation"]
            ceiling = row["ceiling_per_take_CRD"]
            assert value["budget"] == {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": ceiling,
                                       "cumulative_CRD": ceiling}
            t = s1530_tag(unit)
            assert value["takes"]["folders"] == [f"sd-{unit}-{t}-1", f"sd-{unit}-{t}-2"] and value["takes"]["this_take"] == f"sd-{unit}-{t}-{n}"
            assert ("replaces_approval" in value) == (t in ("m", "p"))
            tag = f"iris-{unit.lower()}-{t}-{n}"
            assert value["bound_ids"] == {"attempt_id": f"{tag}-source-001", "policy_id": f"{tag}-source-001",
                                          "reservation_id": f"{tag}-reservation-001"}
            ids += value["bound_ids"].values()
    assert len(set(ids)) == 14 * 2 * 2 and not set(ids) & used         # attempt_id == policy_id within a take


@pytest.mark.parametrize("unit", S1530_UNITS)
def test_s1530_templates_pass_draft_materialize_and_lint(lane, monkeypatch, capsys, unit):
    """The n-1 template with only its placeholders filled drafts, resolves the 4k request with the exact prompt, image
    and vocal, and passes every lint check (tmp lane; nothing is written under the repo, nothing is called)."""
    monkeypatch.setattr(U, "VOCALS", "outputs/ai-city-takeover/ep01/v4/pilot/audio/windows.json")
    row, spec = S1530_ROWS[unit], U.SPECS[unit]
    value = s1530_take(unit, 1) | {"question": "q", "user_quote": "按页面拍 (Recommended)", "approved_at": "2026-11-22T08:00:00Z"}
    approve(lane, value)
    U.draft(unit)
    node = f"node_dryrun1530{unit.lower()}"
    ceiling = row["ceiling_per_take_CRD"]
    profile = PROFILE | {"input_mode": spec["input_mode"], "node_id": node, "duration_seconds": spec["duration"],
                         "benefit_amount": spec["duration"], "credit_upper_bound": ceiling}
    path = lane / unit / "profile.json"
    path.write_text(json.dumps(profile))
    U.materialize(unit, path)
    capsys.readouterr()
    U.show(unit)
    request = json.loads(capsys.readouterr().out)
    assert (request["model"], request["input_mode"], request["seconds"], request["resolution"], request["aspect"],
            request["prompt"]) == ("seedance_2.0_vip", spec["input_mode"], spec["duration"], "4k", "16:9", row["prompt"])
    assert [b["asset_sha256"] for b in request["image_bindings"]] == [spec["plate_sha256"]]
    assert [b["asset_sha256"] for b in request["media_bindings"]] == (
        [row["vocal"]["sha256"]] if spec["input_mode"] == "multimodal" else [])
    bound = {"schema_version": "iris-v4-unit/1", "unit": unit, "task": f"IRIS EP01 v4 {unit}（{row['shot']}，n-1）",
             "user_quote": value["user_quote"], "preview_approval": str(lane / "preview-approval.json"), **value["bound_ids"],
             "max_submit_count": 1, "automatic_retries": 0, "operator_currency": "CRD", "operator_ceiling": ceiling,
             "ledger": "ledger.json", "cumulative_submit_ceiling": 1, "cumulative_operator_credit_ceiling": ceiling,
             "issued_at": "2026-11-22T08:30:00+00:00", "expires_at": "2026-11-22T11:30:00+00:00", "stop_on_unknown": True}
    (lane / unit / "operator-bound.json").write_text(json.dumps(bound, ensure_ascii=False))
    (lane / unit / "node-created.json").write_text(json.dumps({"node_id": node, "empty": True}))
    (lane / "continuity-report.json").write_text(json.dumps({"units": {unit: {"verdict": "ready"}}}))
    code = "import json, sys; sys.path.insert(0, sys.argv[1]); import lint; print(json.dumps(lint.lint(sys.argv[2])['checks']))"
    env = {k: v for k, v in os.environ.items() if k not in {"SD_PILOT", "SD_UNITS"}} | {
        "SD_TRIAL": str(lane), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONWARNINGS": "ignore"}
    out = subprocess.run([sys.executable, "-c", code, str(GEN), unit], cwd=REPO, capture_output=True, text=True, env=env,
                         check=True).stdout
    checks = json.loads(out.strip().splitlines()[-1])
    assert [k for k, v in checks.items() if not v] == []


# ---------------------------------------------------------------- s031-s048 (2026-11-24, pilot/s031-048/submit)
S3148 = REPO / "outputs/ai-city-takeover/ep01/v4/pilot/s031-048"
S3148_UNITS = ["SG12", "INS33", "SG15", "SG16", "INS37", "SG17", "SG18", "INS41", "SG19", "MO15", "SG20"]
S3148_LIPSYNC = ("SG12", "SG15", "SG16", "SG17", "SG18", "SG19", "SG20")
S3148_ROWS = {row["unit"]: row for row in json.loads((S3148 / "submit/preview-inputs.json").read_text(encoding="utf-8"))["units"]}
# 2026-11-25 r3 (pilot/s031-048/r3/PATCH.md; supersedes r2, which was never applied): SG12 a-3 spoke Chinese after its prompt
# quoted a Chinese rendering of the lyric (「删掉译文、精简动作后重拍 (Recommended)」). SG12 / SG15 / SG16 / SG17 / SG18 / SG20 are
# re-approved from pilot/s031-048/submit-r3 (prompts excerpt/flash/s031-048-seedance-r3.md: no lyric text or translation, no
# quote marks, actions bound by ordinal only; SG12 only the belt cinch, re-shot in sd-SG12-b-1|2; SG15 / SG17 / SG20 carry r2:
# SG20 first frame p048-w2 with the W1 left arm bare). The base pack and its templates stay frozen at the board they were
# built from; INS33 / INS37 / INS41 / SG19 / MO15 were submitted from them.
S3148_R3 = ("SG12", "SG15", "SG16", "SG17", "SG18", "SG20")
S3148_TAGS = {"SG12": "b"}                                     # SG12 a-1 / a-2 / a-3 are used; the others reuse a-1|2
S3148_BOARD_SHA256 = "e981c8f27d770cbb99b8aa15f72cc6fd4633300e46f359b44af6b153c39da41c"   # board/shots.json of the base pack build
S3148_R3_INPUTS = json.loads((S3148 / "submit-r3/preview-inputs.json").read_text(encoding="utf-8"))
S3148_ROWS.update({row["unit"]: row for row in S3148_R3_INPUTS["units"]})
# the user's picks on pilot/s031-048/preview (「全按推荐 (Recommended)」, logs/decisions.md 2026-11-24): unit -> (plate, design frame);
# SG16 / INS37 / SG19 / MO15 replaced by the 2026-11-24 pre-submit continuity fixes (CONT1124, pilot/s031-048/issues, pending)
S3148_PLATES = {"SG12": ("p031-c1", "P031/a"), "INS33": ("p033-ins33", "INS33/b"), "SG15": ("p036-c1", "P036/x"),
                "SG16": ("p037-c2", "CONT1124/p037-mw-b-comp"), "INS37": ("p037-ins37b", "CONT1124/ins37-flip"),
                "SG17": ("p039-c1", "P039/b"), "SG18": ("p041-c1", "P041/c"), "INS41": ("p041-ins41", "INS41/b"),
                "SG19": ("p042-w2", "CONT1124/p042-knee-b-comp"), "MO15": ("p046-w2", "CONT1124/p046-kh-b-comp"),
                "SG20": ("p048-w2", "CONT1124/p048-arm-b-comp")}     # r2 / r3: W1 left arm bare (p048-w1 had it sleeved)


def s3148_take(unit: str, n: int) -> dict:
    """The unit's <tag>-1 approval template turned into take n as its _template_notes say (placeholders left in)."""
    value = json.loads(((S3148 / "r3") if unit in S3148_R3 else S3148).joinpath(f"{unit}-approval.template.json").read_text(
        encoding="utf-8"))
    assert len(value.pop("_template_notes")) == 3
    tag = S3148_TAGS.get(unit, "a")
    swap = lambda text: text.replace(f"-{tag}-1", f"-{tag}-{n}")
    value["unit_group"] = swap(value["unit_group"])
    value["bound_ids"] = {k: swap(v) for k, v in value["bound_ids"].items()}
    value["takes"]["this_take"] = swap(value["takes"]["this_take"])
    return value


def test_s3148_pack_is_the_board_plates_the_drafts_and_the_specs():
    """Each first frame is a NEW board plate (no earlier plate overwritten) and the chosen design frame byte for byte; mode,
    seconds, prompt (verbatim draft block), required phrases, vocal window and lyric agree with the spec; 80 CRD/s × 2."""
    inputs = json.loads((S3148 / "submit/preview-inputs.json").read_text(encoding="utf-8"))
    # the base pack is frozen at its build's board; the r3 pack (its six units) is built from the current board
    assert inputs["board"]["sha256"] == S3148_BOARD_SHA256 and S3148_R3_INPUTS["board"]["sha256"] == U.BOARD_SHA256 == sha(U.BOARD)
    blocks = {}
    for pack in (inputs, S3148_R3_INPUTS):                # r3 blocks replace the base drafts of its six units
        assert sha(pack["source_prompt_file"]) == pack["source_prompt_file_sha256"]
        blocks.update(re.findall(r"^## s\d{3} · (\w+) · .*?\n\n```prompt\n(.*?)\n```",
                                 (REPO / pack["source_prompt_file"]).read_text(encoding="utf-8"), re.S | re.M))
    assert list(blocks) == list(S3148_ROWS) == S3148_UNITS and [r["unit"] for r in S3148_R3_INPUTS["units"]] == list(S3148_R3)
    board = json.loads((REPO / U.BOARD).read_bytes())
    shots, clips = {s["id"]: s for s in board["shots"]}, {c["clip"]: c for c in board["clips"]}
    coverage = {u["unit_id"]: u for u in json.loads(U.COVERAGE.read_text(encoding="utf-8"))["coverage_units"]}
    windows = json.loads((REPO / U.VOCALS).read_text(encoding="utf-8"))["windows"]
    before = json.loads((REPO / "outputs/ai-city-takeover/ep01/v4/board/shots.json.before-s031-048-2026-11-24").read_bytes())
    old_plates = {c["start_frame"] for c in before["clips"]} | {s["plate"] for s in before["shots"]}
    for unit, row in S3148_ROWS.items():
        spec, clip, shot = U.SPECS[unit], clips[unit], shots[row["shot"]]
        plate, frame = S3148_PLATES[unit]
        assert clip["start_frame"] == clip["plate"] == spec["plate"] == plate and plate not in old_plates
        insert = unit.startswith("INS")
        assert clip["used_by"] == [row["shot"]] and ("insert" in clip) == insert
        assert insert or shot["plate"] == plate              # an insert keeps its shot's own plate
        assert spec["image"][1] == row["first_frame"]["path"] == U.PLATES + plate + ".png"
        assert row["first_frame"]["design_frame"].endswith(f"design/S31-48/{frame}.png")
        assert sha(row["first_frame"]["path"]) == sha(row["first_frame"]["design_frame"]) == spec["plate_sha256"]
        assert (row["mode"], row["seconds"]) == (spec["input_mode"], spec["duration"]) == (
            spec["generation"]["mode"], spec["generation"]["seconds"])
        assert spec["duration"] == max(4, math.ceil(coverage[unit]["duration_seconds"]) + spec.get("take_margin_seconds", 0))
        assert 4 <= spec["duration"] <= 15 and spec["input_mode"] == ("multimodal" if unit in S3148_LIPSYNC else "first_frame")
        assert row["prompt"] == blocks[unit] and hashlib.sha256(row["prompt"].encode()).hexdigest() == row["prompt_sha256"]
        assert U.prompt_language_ok(spec, row["prompt"])
        literals = [spec["image"][4], *spec["intent"]["open_event"], *spec["intent"]["close_event"], *spec["intent"]["natural"]]
        assert row["required_phrases"] == literals and len(set(literals)) == len(literals) >= 6
        assert [x for x in literals if x not in row["prompt"]] == []
        assert (row["est_cost_per_take_CRD"], row["ceiling_per_take_CRD"]) == (
            spec["duration"] * 80, math.ceil(spec["duration"] * 0.8) * 100)
        assert row["lesson_risks"] and row["plan_unit"]["gate"]
        if spec["input_mode"] == "multimodal":
            assert {"逐字精确同步", "嘴前没有任何遮挡"} <= set(literals)
            assert set(U.MARKERS.findall(row["prompt"])) == {"{{image:0}}", "{{audio:1}}"}
            vocal, window = row["vocal"], windows[spec["audio"]["window"]]
            assert spec["audio"]["window"] == unit and vocal["path"].endswith(f"pilot/audio/{unit}.wav")
            assert vocal["path"] == spec["audio"]["path"] == window["path"] and sha(vocal["path"]) == vocal["sha256"] == window["sha256"]
            assert window["song_window"] == vocal["song_window_s"] == [clip["window"]["t0"], clip["window"]["t1"]]
            assert vocal["lyric_text"] == spec["dialogue"]["verbatim_text"] == " ".join(clip["words"])
            assert window["seconds"] <= spec["duration"]
        else:
            assert not U.MARKERS.findall(row["prompt"]) and "vocal" not in row
    # 9 + 4 + 5 + 7 + 4 + 5 + 10 + 4 + 5 + 6 + 6 s; 80 CRD/s, two takes each
    assert inputs["total_seconds_per_take_set"] == 65 and inputs["estimated_total_CRD"] == 65 * 80 * 2 == 10400
    assert inputs["ceiling_total_CRD"] == 11200
    for still in inputs["stills"]:                    # stills are the preview's recommended design frames, not generated
        assert all(sha(f["path"]) == f["sha256"] for f in still["frames"]) and still["plan"]["cls"] == "s"
    # r3 keeps every unit's seconds: 9 + 5 + 7 + 5 + 10 + 6 s, two takes each; SG12's two b takes are new over the 10,400 plan
    # (its planned two were spent on a-1 and a-3), the other five were inside it
    r3 = S3148_R3_INPUTS
    assert (r3["total_seconds_per_take_set"], r3["estimated_total_CRD"], r3["ceiling_total_CRD"]) == (42, 42 * 80 * 2, 7000)
    assert {k: r3["new_over_plan"][k] for k in ("unit", "estimated_CRD", "ceiling_CRD")} == {"unit": "SG12", "estimated_CRD": 1440,
                                                                                              "ceiling_CRD": 1600}
    for key, pack in (("base_pack", "submit"), ("supersedes", "submit-r2")):
        path = f"outputs/ai-city-takeover/ep01/v4/pilot/s031-048/{pack}/preview-inputs.json"
        assert r3[key] == {"path": path, "sha256": sha(path)}
    [still] = r3["stills"]                            # r2's s047, remade with the W1 left arm bare
    assert still["segment"] == "s047" and still["frames"][0]["path"].endswith("CONT1124/p047-rb-c-2944.png")
    assert sha(still["frames"][0]["path"]) == still["frames"][0]["sha256"] and sha(still["replaces"]["path"]) == still["replaces"]["sha256"]
    r2_blocks = dict(re.findall(r"^## s\d{3} · (\w+) · .*?\n\n```prompt\n(.*?)\n```",
                                (REPO / "outputs/ai-city-takeover/ep01/v4/excerpt/flash/s031-048-seedance-r2.md").read_text(
                                    encoding="utf-8"), re.S | re.M))
    for unit in S3148_R3:                             # the previous prompt is r2's for SG15 / SG17 / SG20, else the base draft
        base = next(r for r in inputs["units"] if r["unit"] == unit)
        row = S3148_ROWS[unit]
        previous = hashlib.sha256(r2_blocks[unit].encode()).hexdigest() if unit in ("SG15", "SG17", "SG20") else base["prompt_sha256"]
        assert row["previous_prompt"]["sha256"] == previous and row["base_prompt"]["sha256"] == base["prompt_sha256"]
        assert (row["prompt_sha256"] == previous) == (unit == "SG20") and row["prompt_sha256"] != base["prompt_sha256"]


def test_s3148_vocal_windows():
    """Each vocal window starts ~0.3 s before its phrase; where that point is inside the previous word (cut_audio refuses)
    it starts where that word ends, never after the edit's in-point (SG08 / SG09m precedent). Take = ceil(window) + 1 s;
    SG20's vocal stops before "All" and its take covers the edit to 209.34 + 1 s. The wavs are cut_audio cuts, sealed."""
    board = json.loads((REPO / U.BOARD).read_bytes())
    clips = {c["clip"]: c for c in board["clips"]}
    words = [w for line in json.loads(C.WORDS.read_text())["lines"] for w in line["words"]]
    windows = json.loads((REPO / U.VOCALS).read_text(encoding="utf-8"))["windows"]
    bounded = {"SG15": 0.123, "SG16": 0.04, "SG17": 0.195, "SG18": 0.222}      # previous word's end or the in-point
    for unit in S3148_LIPSYNC:
        spec, clip = U.SPECS[unit], clips[unit]
        t0, t1 = clip["window"]["t0"], clip["window"]["t1"]
        assert C.inside_word(t0, json.loads(C.WORDS.read_text())) == []
        first = next(w for w in words if w["start"] >= t0)
        lead = round(first["start"] - t0, 3)
        assert lead >= 0.3 - 1e-6 or bounded[unit] == lead
        if unit in bounded and unit != "SG17":
            prev = max((w for w in words if w["end"] <= t0 + 1e-6), key=lambda w: w["end"])
            assert prev["end"] == t0 and first["start"] - 0.3 < prev["end"]
        assert clip["plays"]["t0"] >= t0 and spec["dialogue"]["start_seconds"] == round(first["start"] - t0, 2)
        margin = 2 if unit == "SG20" else 1
        assert spec["take_margin_seconds"] == margin and spec["duration"] == math.ceil(clip["seconds"]) + margin
        assert clip["plays"]["t1"] - t0 + 1 <= spec["duration"]           # every edit span has a second of handle
        rel = f"outputs/ai-city-takeover/ep01/v4/pilot/audio/{unit}.wav"
        assert windows[unit]["path"] == rel and windows[unit]["song_window"] == [t0, t1] and sha(rel) == windows[unit]["sha256"]
        frames_, sr, ch, width = frames(REPO / rel)
        payload, _, n = C.cut_window(C.STEM, t0, t1)
        assert (frames_, sr, ch, width) == (payload, 44100, 1, 2) and n == windows[unit]["samples"]
    assert clips["SG20"]["window"]["t1"] == 208.8 < next(w["start"] for w in words if w["text"] == "All" and w["start"] > 208)
    assert clips["SG17"]["window"]["t0"] == clips["SG17"]["plays"]["t0"] == 170.1094


def test_s3148_prompts_follow_the_lessons():
    """The binding lessons: no turning in spoken / sung takes, no walking at the lens and no exit, blank / unlit things,
    one face, s039 only the door-crack red line, MO15 left hand, s041 wrapped, the duplicate never shows its face."""
    rows = S3148_ROWS
    for unit, row in rows.items():
        prompt = row["prompt"]
        assert all(prompt[i - 1] == "不" for i in (m.start() for m in re.finditer("转身|转头|走出|起身", prompt))), unit
        assert not [x for x in ("走向镜头", "朝镜头走", "出画", "走出画面", "走开", "离开画面") if x in prompt], unit
        assert prompt.endswith("画面中不得出现任何文字。")
        if unit == "SG17":
            assert "画面里除了她左耳耳挂上的小红灯和门缝下那一线红光，没有任何别的红色" in prompt
            assert "除了她左耳耳挂上的小红灯，画面里没有任何红色" not in prompt and "门缝" in U.SPECS[unit]["palette"]
        elif unit.startswith("INS") or unit == "MO15":
            assert "画面里没有任何红色。" in prompt and "耳挂" not in prompt
        else:
            assert "除了她左耳耳挂上的小红灯，画面里没有任何红色。" in prompt
    assert "左手搭在杆上那一排衣架上" in rows["MO15"]["prompt"] and "她用左手一把把所有衣架" in rows["MO15"]["prompt"]
    assert "右手" not in rows["MO15"]["prompt"] and "不露出头和脸" in rows["MO15"]["prompt"]
    assert "从肩到脚裹在同一种本白粗亚麻防尘布里" in rows["SG18"]["prompt"] and "看不见布下面的衣服" in rows["SG18"]["prompt"]
    assert "看不到他的脸" in rows["SG16"]["prompt"] and "没有五官" in rows["INS41"]["prompt"]
    blank = {"SG12": "售货机的小显示屏是黑的，不亮", "INS33": "没有任何刻字、刻度、数字或铭牌", "SG15": "寻呼机屏幕没有数字和字，不亮红灯",
             "SG16": "咖啡机和水壶上没有亮灯，也没有显示屏", "INS37": "显示屏始终是黑的，不亮任何数字", "SG17": "门上没有门牌、号码或标志",
             "SG19": "工牌是空白的", "MO15": "秒表表盘空白，没有数字", "SG20": "工牌是空白的"}
    for unit, phrase in blank.items():
        assert phrase in rows[unit]["prompt"], unit
    for unit in ("INS33", "INS37", "INS41"):              # hand-only inserts take unit.py's no-person path, as INS16
        spec = U.SPECS[unit]
        assert (spec["iris"], spec["identity_waiver"], spec["duration"]) == (False, None, 4)
        assert "character_directions" not in spec["performance"]
    assert U.SPECS["SG18"]["look"] == "C" and "裹在防尘布里" in U.SPECS["SG18"]["identity_continuity"]
    # r3: every action is bound by ordinal (no "last sentence": SG15's window ends on the next line's "Ten"); SG12 keeps only
    # the belt cinch on the first word (no banknote tuck, no eye flick); SG20 states the W1 left arm bare (r2)
    assert all("最后" not in rows[unit]["prompt"] for unit in S3148_R3)
    assert "说到第三句时她只垂下眼睛看那位读者，不转头" in rows["SG15"]["prompt"]
    assert "说到第四句时，微波炉的灯熄灭、转盘停下，她把碗放到身边的台面上" in rows["SG16"]["prompt"]
    assert "说到第二句时她把右手手掌平按进那道红光里" in rows["SG17"]["prompt"]
    assert "唱到第三句刚开口时，她的一只手从胸前的布缝里伸出来" in rows["SG18"]["prompt"]
    assert "她的左肩和整条左臂一直裸露，灰色外套只有右臂一只长袖" in rows["SG20"]["prompt"]
    sg12 = rows["SG12"]["prompt"]
    assert "说出第一个词的同时用左手把风衣腰带一拉收紧" in sg12 and "右手一直捏着纸币垂在腰前" in sg12
    assert not [x for x in ("塞进", "口袋", "瞟", "第四句") if x in sg12]



# Chinese renderings the s031-s048 drafts once quoted for a lyric line (SG12 a-3 then spoke Chinese); r3 bans them outright
S3148_RETIRED_RENDERINGS = ("运气不好", "让开", "找到了一道缝", "十二点三十四分", "十月")
S3148_ORDINALS = {"SG15": ("说到第三句时", 3, "Out"), "SG16": ("说到第四句时", 4, "Killed"), "SG17": ("说到第二句时", 2, "They"),
                  "SG18": ("唱到第三句刚开口时", 3, "October")}


def s3148_sentences(t0: float, t1: float) -> list[list[str]]:
    """The sentences heard in a vocal window (words.json): spoken lines split at . ? !, a sung line is one sentence; a tail
    of the previous sentence (words starting before t0) does not count."""
    out = []
    for line in json.loads(C.WORDS.read_text())["lines"]:
        current = []
        for i, w in enumerate(line["words"]):
            if t0 <= w["start"] < t1:
                current.append(w["text"])
            if current and (i == len(line["words"]) - 1 or (line["mode"] == "spoken" and w["text"][-1] in ".?!")):
                out.append(current)
                current = []
    return out


def test_s3148_spoken_and_sung_prompts_quote_no_lyric():
    """No spoken or sung prompt quotes lyric text or any translation of it (SG12 a-3 re-voiced its line in Chinese after the
    prompt quoted 「运气不好」; 「删掉译文、精简动作后重拍 (Recommended)」, logs/decisions.md 2026-11-25): no quote marks at all,
    no Latin letters, no fragment of the line's Chinese gloss (lyrics/glosses-v5.json), none of the retired renderings.
    Actions bind by ordinal only, and each ordinal names a sentence that starts inside the unit's own vocal window."""
    glosses = json.loads((REPO / "outputs/ai-city-takeover/ep01/v4/lyrics/glosses-v5.json").read_text(encoding="utf-8"))
    lines = json.loads(C.WORDS.read_text())["lines"]
    windows = json.loads((REPO / U.VOCALS).read_text(encoding="utf-8"))["windows"]
    prompts = {unit: S3148_ROWS[unit]["prompt"] for unit in S3148_LIPSYNC} | SG17_PROBE_PROMPTS | R4_PROMPTS
    # The one exemption: SG17B (「先用 SG17 做 A/B 对照 (Recommended)」, logs/decisions.md 2026-11-25: "B=A+英文原台词入 {} …
    # B 臂豁免“prompt 不写英文”") and the r4 units (「s039 拼切；剩下照这个写法拍，上限提到 15,000 (Recommended)」). Exactly the
    # window's English words, once, inside {}; with that sentence removed the prompt must pass every check below.
    assert [unit for unit, spec in U.SPECS.items() if spec.get("braced_line")] == ["SG17B", *R4]
    for unit in ("SG17B", *R4):
        braced = "{" + U.SPECS[unit]["braced_line"] + "}"
        assert U.SPECS[unit]["braced_line"] == U.SPECS[unit]["dialogue"]["verbatim_text"] and prompts[unit].count(braced) == 1
        assert not U.prompt_language_ok(U.SPECS["SG17A"], prompts[unit])      # the exemption does not reach any other spec
        assert not U.prompt_language_ok(U.SPECS[U.SPECS[unit].get("clip", unit)], prompts[unit])
        prompts[unit] = prompts[unit].replace(braced, "", 1)
    for unit, prompt in prompts.items():
        spec = U.SPECS[unit]
        t0, t1 = windows[spec["audio"]["window"]]["song_window"]
        assert not [q for q in "「」『』“”‘’\"'" if q in prompt], unit
        assert U.prompt_language_ok(spec, prompt) and not [x for x in S3148_RETIRED_RENDERINGS if x in prompt], unit
        heard = [g for line in lines if line["end"] > t0 and line["start"] < t1 for g in [glosses.get(line["en"], "")]]
        fragments = {f for g in heard for f in re.split(r"[，。：；！？、“”「」（）\s,.:;!?()]+", re.sub(r"（[^）]*）", "", g))
                     if len(f) >= 3 and not re.search("[A-Za-z0-9]", f)}
        assert heard and not [f for f in fragments if f in prompt], unit
        literals = [spec["image"][4], *spec["intent"]["open_event"], *spec["intent"]["close_event"], *spec["intent"]["natural"]]
        assert not [x for x in literals if re.search("[「」『』“”‘’\"']", x)], unit
        said = s3148_sentences(t0, t1)
        if unit in S3148_ORDINALS:
            words, n, first = S3148_ORDINALS[unit]
            assert words in prompt and said[n - 1][0] == first, (unit, said)
        bound = [re.search("第.+?句", S3148_ORDINALS[unit][0]).group(0)] if unit in S3148_ORDINALS else []
        assert re.findall("第[一二三四五六七八九十]+句", prompt) == bound, unit      # the one bound ordinal, nothing else
    assert [s[0] for s in s3148_sentences(*windows["SG12"]["song_window"])] == ["September", "The", "Google,", "No", "It"]
    assert "说出第一个词的同时" in S3148_ROWS["SG12"]["prompt"]                    # SG12 binds only its first word

def test_s3148_templates_shape_both_takes_with_fresh_ids():
    """Fresh ids per take, never another take's; an approval the main session already wrote (and its operator bound) carries
    exactly its own template's pack, prompt and ids. The r3 units bind the submit-r3 pack; SG12's r3 takes are b-1|2 (a
    superseded approval stays only as preview-approval.held-r2|r3.json)."""
    packs = {False: "outputs/ai-city-takeover/ep01/v4/pilot/s031-048/submit/",
             True: "outputs/ai-city-takeover/ep01/v4/pilot/s031-048/submit-r3/"}
    own = {f"sd-{unit}-{S3148_TAGS.get(unit, 'a')}-{n}" for unit in S3148_UNITS for n in (1, 2)}
    bound = {b.parent.parent.name: json.loads(b.read_text()) for b in (REPO / "outputs/ai-city-takeover/ep01/v4/pilot").glob(
        "sd-*/*/operator-bound.json")}
    used = {value.get(k) for name, value in bound.items() if name not in own for k in ("attempt_id", "policy_id", "reservation_id")}
    ids = []
    for unit, row in S3148_ROWS.items():
        spec = U.SPECS[unit]
        page, inputs = packs[unit in S3148_R3] + "index.html", packs[unit in S3148_R3] + "preview-inputs.json"
        tag = S3148_TAGS.get(unit, "a")
        for n in (1, 2):
            value = s3148_take(unit, n)
            assert sorted(placeholders(value)) == sorted([value["question"], value["user_quote"], value["approved_at"]])
            assert value["preview_page"] == {"path": page, "sha256": sha(page)}
            assert value["preview_inputs"] == {"path": inputs, "sha256": sha(inputs)}
            assert value["prompts"] == {unit: {"text": row["prompt"], "sha256": row["prompt_sha256"]}}
            artifacts = [{"path": spec["image"][1], "sha256": spec["plate_sha256"], "role": f"{unit} {U.APPROVAL_ROLE[spec['input_mode']]}"}]
            if spec.get("audio"):
                artifacts.append({"path": spec["audio"]["path"], "sha256": sha(spec["audio"]["path"]), "role": f"{unit} vocal"})
            assert value["preview_artifacts"] == artifacts and value["generation"] == spec["generation"]
            ceiling = row["ceiling_per_take_CRD"]
            assert value["budget"] == {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": ceiling,
                                       "cumulative_CRD": ceiling}
            assert value["identity_waivers"] == (["IRIS"] if spec["iris"] else [])
            assert value["takes"]["folders"] == [f"sd-{unit}-{tag}-1", f"sd-{unit}-{tag}-2"]
            assert value["takes"]["this_take"] == f"sd-{unit}-{tag}-{n}" and "replaces_approval" not in value
            ident = f"iris-{unit.lower()}-{tag}-{n}"
            assert value["bound_ids"] == {"attempt_id": f"{ident}-source-001", "policy_id": f"{ident}-source-001",
                                          "reservation_id": f"{ident}-reservation-001"}
            ids += value["bound_ids"].values()
            folder = S3148.parent / f"sd-{unit}-{tag}-{n}"     # a folders exist (b: the main session makes them); approvals are its own
            assert folder.is_dir() or tag == "b"
            written = folder / "preview-approval.json"
            if written.exists():
                approval = json.loads(written.read_text(encoding="utf-8"))
                keys = ("preview_page", "preview_inputs", "prompt_source", "preview_artifacts", "prompts", "generation", "bound_ids")
                assert {k: approval[k] for k in keys} == {k: value[k] for k in keys}, folder.name
            if folder.name in bound:
                assert {k: bound[folder.name][k] for k in value["bound_ids"]} == value["bound_ids"], folder.name
    assert len(set(ids)) == 11 * 2 * 2 and not set(ids) & used


@pytest.mark.parametrize("unit", S3148_UNITS)
def test_s3148_templates_pass_draft_materialize_and_lint(lane, monkeypatch, capsys, unit):
    """The a-1 template with only its placeholders filled drafts, resolves the 4k request with the exact prompt, image
    and vocal, and passes every lint check (tmp lane; nothing is written under the repo, nothing is called)."""
    monkeypatch.setattr(U, "VOCALS", "outputs/ai-city-takeover/ep01/v4/pilot/audio/windows.json")
    row, spec = S3148_ROWS[unit], U.SPECS[unit]
    value = s3148_take(unit, 1) | {"question": "q", "user_quote": "按页面拍 (Recommended)", "approved_at": "2026-11-24T08:00:00Z"}
    approve(lane, value)
    U.draft(unit)
    node = f"node_dryrun3148{unit.lower()}"
    ceiling = row["ceiling_per_take_CRD"]
    profile = PROFILE | {"input_mode": spec["input_mode"], "node_id": node, "duration_seconds": spec["duration"],
                         "benefit_amount": spec["duration"], "credit_upper_bound": ceiling}
    path = lane / unit / "profile.json"
    path.write_text(json.dumps(profile))
    U.materialize(unit, path)
    capsys.readouterr()
    U.show(unit)
    request = json.loads(capsys.readouterr().out)
    assert (request["model"], request["input_mode"], request["seconds"], request["resolution"], request["aspect"],
            request["prompt"]) == ("seedance_2.0_vip", spec["input_mode"], spec["duration"], "4k", "16:9", row["prompt"])
    assert [b["asset_sha256"] for b in request["image_bindings"]] == [spec["plate_sha256"]]
    assert [b["asset_sha256"] for b in request["media_bindings"]] == (
        [row["vocal"]["sha256"]] if spec["input_mode"] == "multimodal" else [])
    bound = {"schema_version": "iris-v4-unit/1", "unit": unit, "task": f"IRIS EP01 v4 {unit}（{row['shot']}，a-1）",
             "user_quote": value["user_quote"], "preview_approval": str(lane / "preview-approval.json"), **value["bound_ids"],
             "max_submit_count": 1, "automatic_retries": 0, "operator_currency": "CRD", "operator_ceiling": ceiling,
             "ledger": "ledger.json", "cumulative_submit_ceiling": 1, "cumulative_operator_credit_ceiling": ceiling,
             "issued_at": "2026-11-24T08:30:00+00:00", "expires_at": "2026-11-24T14:30:00+00:00", "stop_on_unknown": True}
    (lane / unit / "operator-bound.json").write_text(json.dumps(bound, ensure_ascii=False))
    (lane / unit / "node-created.json").write_text(json.dumps({"node_id": node, "empty": True}))
    (lane / "continuity-report.json").write_text(json.dumps({"units": {unit: {"verdict": "ready"}}}))
    code = "import json, sys; sys.path.insert(0, sys.argv[1]); import lint; print(json.dumps(lint.lint(sys.argv[2])['checks']))"
    env = {k: v for k, v in os.environ.items() if k not in {"SD_PILOT", "SD_UNITS"}} | {
        "SD_TRIAL": str(lane), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONWARNINGS": "ignore"}
    out = subprocess.run([sys.executable, "-c", code, str(GEN), unit], cwd=REPO, capture_output=True, text=True, env=env,
                         check=True).stdout
    checks = json.loads(out.strip().splitlines()[-1])
    assert [k for k, v in checks.items() if not v] == []


# ---------------------------------------------------------------- SG17 A/B lip-sync probe (2026-11-25, pilot/s031-048/probe)
# 「先用 SG17 做 A/B 对照 (Recommended)」 (logs/decisions.md 2026-11-25, after the model-researcher summary): two arms on s039,
# two takes each, 5 s 4k multimodal, first frame p039-c1, one shared vocal SG17p (SG17.wav + digital silence at the end to
# exactly 5.000 s). A = the first-frame state, then only speech in word-for-word sync; B = A + the exact English lines in {}.
SG17_PROBE = REPO / "outputs/ai-city-takeover/ep01/v4/pilot/s031-048/probe"
SG17_START = ("{{image:0}}中的她蹲在一扇关着的深色木门前，低机位，门缝下透进来的一线红光贴着地面，横在她右手指尖前；"
              "她的左臂搭在膝上，看着镜头，嘴唇闭着。")
SG17A_PROMPT = (SG17_START + "她对着镜头说话，口型与{{audio:1}}里的人声逐字精确同步。镜头固定不动，她一直蹲在原地。"
                "门上没有门牌、号码或标志。画面里除了她左耳耳挂上的小红灯和门缝下那一线红光，没有任何别的红色；红光不照到她的脸上。"
                "画面中不得出现任何文字。")
SG17B_SENTENCE = "她用英文说：{Bet it couldn't reach outside. They found a gap instead.}不增不减，不翻译。"
SG17B_PROMPT = SG17A_PROMPT.replace("逐字精确同步。", "逐字精确同步。" + SG17B_SENTENCE)
SG17_PROBE_PROMPTS = {"SG17A": SG17A_PROMPT, "SG17B": SG17B_PROMPT}
# anything she could do besides speaking (the r3 hand press 按 / 手掌 and the usual drift: standing, turning, leaning, gestures)
SG17_ACTIONS = ("按", "手", "伸", "抬", "举", "放", "拿", "推", "拉", "摸", "碰", "握", "攥", "收", "起", "站", "走", "转", "低头",
                "点头", "摇头", "挥", "指向", "前倾", "靠", "眨", "笑", "张开", "合上", "移", "挪", "动作", "打开", "开门", "回头")


def sg17_take(unit: str, n: int) -> dict:
    """The arm's p-1 approval template turned into take n as its _template_notes say (placeholders left in)."""
    value = json.loads((SG17_PROBE / f"{unit}-approval.template.json").read_text(encoding="utf-8"))
    assert len(value.pop("_template_notes")) == 3
    swap = lambda text: text.replace("-p-1", f"-p-{n}")
    value["unit_group"] = swap(value["unit_group"])
    value["bound_ids"] = {k: swap(v) for k, v in value["bound_ids"].items()}
    value["takes"]["this_take"] = swap(value["takes"]["this_take"])
    return value


def test_sg17_probe_arm_a_only_speaks_and_b_adds_only_the_braced_lines():
    """A holds the first-frame state, then no action but speaking (the hand press and every other action removed) and the
    kept blank / red / no-text rules; B is A plus exactly the {} sentence after the sync sentence, nothing else."""
    assert SG17A_PROMPT.startswith(SG17_START)
    rest = SG17A_PROMPT[len(SG17_START):]
    assert [x for x in SG17_ACTIONS if x in rest] == [] and "说话" in rest and "逐字精确同步" in rest
    assert not [x for x in ("按", "手掌", "平按") if x in SG17A_PROMPT]           # no hand action anywhere, start state included
    for kept in ("镜头固定不动", "她一直蹲在原地", "门上没有门牌", "画面里除了她左耳耳挂上的小红灯和门缝下那一线红光，没有任何别的红色",
                 "红光不照到她的脸上", "画面中不得出现任何文字。"):
        assert kept in SG17A_PROMPT, kept
    assert len(re.findall("[A-Za-z]", SG17A_PROMPT.replace("{{image:0}}", "").replace("{{audio:1}}", ""))) == 0
    i = SG17B_PROMPT.index(SG17B_SENTENCE)
    assert SG17B_PROMPT[:i] + SG17B_PROMPT[i + len(SG17B_SENTENCE):] == SG17A_PROMPT and SG17B_PROMPT.count("{") == SG17A_PROMPT.count("{") + 1
    assert SG17B_PROMPT[i - len("逐字精确同步。"):i] == "逐字精确同步。"
    assert "{" + U.SG17_LINES + "}" in SG17B_SENTENCE and U.SG17_LINES == U.SPECS["SG17"]["dialogue"]["verbatim_text"]
    for unit, prompt in SG17_PROBE_PROMPTS.items():
        spec = U.SPECS[unit]
        literals = [spec["image"][4], *spec["intent"]["open_event"], *spec["intent"]["close_event"], *spec["intent"]["natural"]]
        assert [x for x in literals if x not in prompt] == [] and U.prompt_language_ok(spec, prompt)
        assert set(U.MARKERS.findall(prompt)) == {"{{image:0}}", "{{audio:1}}"}
    assert not U.prompt_language_ok(U.SPECS["SG17A"], SG17B_PROMPT)


def test_sg17_probe_specs_vocal_and_folders():
    """Both arms are the board clip SG17 (no new board clip), first frame p039-c1, 5 s multimodal with vocal SG17p: SG17.wav's
    exact samples + digital zeros at the end to 5.000 s, sealed with SG17's song window; SG17.wav itself and the old
    sd-SG17-a-1|2 approvals are untouched; the arms differ only by name and braced_line."""
    windows = json.loads((REPO / U.VOCALS).read_text(encoding="utf-8"))["windows"]
    sg17, padded = windows["SG17"], windows["SG17p"]
    assert sha(sg17["path"]) == sg17["sha256"] == "ae7ab1b7d5037f877dfb44ada668b7d83445a1caf1f512235989727a7921a6bd"
    voice, sr, ch, width = frames(REPO / sg17["path"])
    data, sr_p, ch_p, width_p = frames(REPO / padded["path"])
    assert (sr_p, ch_p, width_p) == (sr, ch, width) == (44100, 1, 2) and len(data) == 2 * 5 * sr == 2 * padded["samples"]
    assert data == voice + b"\x00\x00" * (5 * sr - sg17["samples"]) and sha(padded["path"]) == padded["sha256"]
    assert padded["path"] == "outputs/ai-city-takeover/ep01/v4/pilot/audio/SG17p.wav" and padded["seconds"] == 5.0
    assert padded["song_window"] == sg17["song_window"] == [170.1094, 173.7781]
    assert padded["padded"]["silence_samples"] == 5 * sr - sg17["samples"] == 58711 and padded["padded"]["from_sha256"] == sg17["sha256"]
    a, b = U.SPECS["SG17A"], U.SPECS["SG17B"]
    for unit, spec in (("SG17A", a), ("SG17B", b)):
        assert (spec["clip"], spec["coverage_unit"], spec["plate"], spec["plate_sha256"]) == (
            "SG17", "SG17", "p039-c1", U.SPECS["SG17"]["plate_sha256"])
        assert spec["generation"] == {**U.GENERATION_LIPSYNC, "seconds": 5} and spec["duration"] == 5
        assert spec["audio"] == {"asset_id": f"iris-c-v4-{unit.lower()}-vocal", "path": padded["path"], "window": "SG17p"}
        assert spec["dialogue"] == U.SPECS["SG17"]["dialogue"] | {"response_obligation": "对着镜头说出这两句，口型与参考人声逐字同步"}
        assert "按" not in json.dumps(spec["performance"], ensure_ascii=False) + json.dumps(spec["intent"], ensure_ascii=False)
    same = lambda spec: {k: v for k, v in spec.items() if k not in ("shot_id", "beat", "audio", "image", "braced_line")}
    assert same(a) == same(b) and "braced_line" not in a and b["braced_line"] == U.SG17_LINES
    for unit in ("SG17A", "SG17B"):
        for n in (1, 2):
            assert (SG17_PROBE.parent.parent / f"sd-{unit}-p-{n}").is_dir()
    for n in (1, 2):                                    # the held r3 SG17 approvals stay as they were
        old = json.loads((SG17_PROBE.parent.parent / f"sd-SG17-a-{n}/preview-approval.json").read_text(encoding="utf-8"))
        assert list(old["prompts"]) == ["SG17"] and old["preview_artifacts"][1]["path"].endswith("pilot/audio/SG17.wav")
        assert (SG17_PROBE.parent.parent / f"sd-SG17-a-{n}/preview-approval.held-r2.json").is_file()


def test_sg17_probe_page_and_templates():
    """The page asks one question first, shows the first frame, the SG17p player, both exact prompts and the diff, the cost
    (4 × 400 = 1,600) and what is measured; each arm's template shapes both takes with fresh ids and the exact prompt."""
    page = (SG17_PROBE / "index.html").read_text(encoding="utf-8")
    body = page[page.index("<body>"):]
    assert body.index('class="q"') < body.index("<h2>") and body.count("问题：") == 1 and "(Recommended)" in body
    assert 'src="../../../board/plates/p039-c1.png"' in page and 'src="../../audio/SG17p.wav"' in page
    import html
    for prompt in SG17_PROBE_PROMPTS.values():                  # verbatim (B's added sentence is marked <ins> as the diff)
        assert html.escape(prompt) in page.replace("<ins>", "").replace("</ins>", "")
        assert hashlib.sha256(prompt.encode()).hexdigest() in page
    assert page.count(f"<ins>{html.escape(SG17B_SENTENCE)}</ins>") == 2 and "4 条 × 400 = 1,600" in page
    for measured in ("语言", "逐词准确度", "copy", "lag / ncc", "spans", "逐镜 Gate"):
        assert measured in page, measured
    ids, bound = [], {b.parent.parent.name: json.loads(b.read_text()) for b in (REPO / "outputs/ai-city-takeover/ep01/v4/pilot").glob(
        "sd-*/*/operator-bound.json")}
    own = {f"sd-{unit}-p-{n}" for unit in SG17_PROBE_PROMPTS for n in (1, 2)}
    used = {v.get(k) for name, v in bound.items() if name not in own for k in ("attempt_id", "policy_id", "reservation_id")}
    for unit, prompt in SG17_PROBE_PROMPTS.items():
        spec = U.SPECS[unit]
        for n in (1, 2):
            value = sg17_take(unit, n)
            assert sorted(placeholders(value)) == sorted([value["question"], value["user_quote"], value["approved_at"]])
            page_rel = "outputs/ai-city-takeover/ep01/v4/pilot/s031-048/probe/index.html"
            assert value["preview_page"] == {"path": page_rel, "sha256": sha(page_rel)}
            assert value["prompts"] == {unit: {"text": prompt, "sha256": hashlib.sha256(prompt.encode()).hexdigest()}}
            assert value["preview_artifacts"] == [
                {"path": spec["image"][1], "sha256": spec["plate_sha256"], "role": f"{unit} reference image"},
                {"path": spec["audio"]["path"], "sha256": sha(spec["audio"]["path"]), "role": f"{unit} vocal"}]
            assert value["generation"] == spec["generation"] and value["identity_waivers"] == ["IRIS"]
            assert value["budget"] == {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 400, "cumulative_CRD": 400}
            assert value["takes"]["folders"] == [f"sd-{unit}-p-1", f"sd-{unit}-p-2"] and value["takes"]["this_take"] == f"sd-{unit}-p-{n}"
            assert value["takes"]["probe"]["total_ceiling_CRD"] == 4 * 400
            ident = f"iris-{unit.lower()}-p-{n}"
            assert value["bound_ids"] == {"attempt_id": f"{ident}-source-001", "policy_id": f"{ident}-source-001",
                                          "reservation_id": f"{ident}-reservation-001"}
            ids += value["bound_ids"].values()
            written = SG17_PROBE.parent.parent / f"sd-{unit}-p-{n}" / "preview-approval.json"
            if written.exists():                                   # the main session wrote it after 「按页面开拍 (Recommended)」
                approval = json.loads(written.read_text(encoding="utf-8"))
                keys = ("preview_page", "preview_artifacts", "prompts", "generation", "budget", "bound_ids", "takes")
                assert {k: approval[k] for k in keys} == {k: value[k] for k in keys}, written.parent.name
            if written.parent.name in bound:                       # its operator bound exactly the template's ids
                assert {k: bound[written.parent.name][k] for k in value["bound_ids"]} == value["bound_ids"]
    assert len(set(ids)) == 4 * 2 and not set(ids) & used          # attempt_id = policy_id, as every earlier take


@pytest.mark.parametrize("unit", ["SG17A", "SG17B"])
def test_sg17_probe_templates_pass_draft_materialize_and_lint(lane, monkeypatch, capsys, unit):
    """The p-1 template with only its placeholders filled drafts, resolves the 4k 5 s request with the exact prompt, p039-c1
    and SG17p, and passes every lint check (tmp lane; nothing is written under the repo, nothing is called)."""
    monkeypatch.setattr(U, "VOCALS", "outputs/ai-city-takeover/ep01/v4/pilot/audio/windows.json")
    spec = U.SPECS[unit]
    value = sg17_take(unit, 1) | {"question": "q", "user_quote": "按这两条 prompt 开拍 (Recommended)", "approved_at": "2026-11-25T08:00:00Z"}
    approve(lane, value)
    U.draft(unit)
    node = f"node_dryrunprobe{unit.lower()}"
    profile = PROFILE | {"input_mode": "multimodal", "node_id": node, "duration_seconds": 5, "benefit_amount": 5,
                         "credit_upper_bound": 400}
    path = lane / unit / "profile.json"
    path.write_text(json.dumps(profile))
    U.materialize(unit, path)
    capsys.readouterr()
    U.show(unit)
    request = json.loads(capsys.readouterr().out)
    assert (request["model"], request["input_mode"], request["seconds"], request["resolution"], request["aspect"],
            request["prompt"]) == ("seedance_2.0_vip", "multimodal", 5, "4k", "16:9", SG17_PROBE_PROMPTS[unit])
    assert [b["asset_sha256"] for b in request["image_bindings"]] == [spec["plate_sha256"]]
    assert [b["asset_sha256"] for b in request["media_bindings"]] == [sha(spec["audio"]["path"])]
    bound = {"schema_version": "iris-v4-unit/1", "unit": unit, "task": f"IRIS EP01 v4 {unit}（s039，p-1）",
             "user_quote": value["user_quote"], "preview_approval": str(lane / "preview-approval.json"), **value["bound_ids"],
             "max_submit_count": 1, "automatic_retries": 0, "operator_currency": "CRD", "operator_ceiling": 400,
             "ledger": "ledger.json", "cumulative_submit_ceiling": 1, "cumulative_operator_credit_ceiling": 400,
             "issued_at": "2026-11-25T08:30:00+00:00", "expires_at": "2026-11-25T14:30:00+00:00", "stop_on_unknown": True}
    (lane / unit / "operator-bound.json").write_text(json.dumps(bound, ensure_ascii=False))
    (lane / unit / "node-created.json").write_text(json.dumps({"node_id": node, "empty": True}))
    (lane / "continuity-report.json").write_text(json.dumps({"units": {unit: {"verdict": "ready"}}}))
    code = "import json, sys; sys.path.insert(0, sys.argv[1]); import lint; print(json.dumps(lint.lint(sys.argv[2])['checks']))"
    env = {k: v for k, v in os.environ.items() if k not in {"SD_PILOT", "SD_UNITS"}} | {
        "SD_TRIAL": str(lane), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONWARNINGS": "ignore"}
    out = subprocess.run([sys.executable, "-c", code, str(GEN), unit], cwd=REPO, capture_output=True, text=True, env=env,
                         check=True).stdout
    checks = json.loads(out.strip().splitlines()[-1])
    assert [k for k, v in checks.items() if not v] == []


# ---------------------------------------------------------------- r4 short lip-sync windows (2026-11-25, pilot/s031-048/r4)
# 「s039 拼切；剩下照这个写法拍，上限提到 15,000 (Recommended)」 (logs/decisions.md 2026-11-25, last entry, after the SG17 A/B
# probe: B's {English lines} gave much better words; every take re-voiced, mouth onset 0.6-1.0 s late). SG16 / SG18 / SG20
# re-cut into one short window per edit span of pilot/s031-048/plan (SG16x s037b, SG16y s037d, SG18x s041a, SG18y s041c,
# SG20x s048), each with the probe's B prompt shape; two takes each, measured, cut and covered across takes.
R4 = tuple(U.R4_UNITS)
R4_DIR = REPO / "outputs/ai-city-takeover/ep01/v4/pilot/s031-048/r4"
R4_PROMPTS = {unit: U.r4_prompt(unit) for unit in R4}
R4_PROMPT_SHA256 = {"SG16x": "ac5c511f77e1fc6163d55f8ae83d20e00d83d5566cef708d79af1598152fa871",
                    "SG16y": "f1ea02b6e15b4e696a00573e33018696e44e303ca2bef5483b7c5e0b94f43fec",
                    "SG18x": "c814ce793e232d923ed2730c78801a8d1feddcab94851856d582712f79882f2c",
                    "SG18y": "03601c4eefac00a0f7c9964c8a0c009fb9c5b5394a2a1a41cd04e63e9f922def",
                    "SG20x": "1146eec4f25897bb4d2c4907388d924625c9f9f9de4c8e30e7e5ebb774ca08c4"}
# the edit span (plan) each serves; the r3 first frame of its board clip
R4_SPANS = {"SG16x": ("s037b", 161.413, 163.701), "SG16y": ("s037d", 165.071, 166.476), "SG18x": ("s041a", 178.329, 181.023),
            "SG18y": ("s041c", 183.763, 185.585), "SG20x": ("s048", 205.241, 209.339)}
R4_PLATES = {"SG16": "p037-c2", "SG18": "p041-c1", "SG20": "p048-w2"}
# window starts that are not simply "first word - 0.3 s": the end of the previous word when that point is inside it
# (SG16x "up.", SG18x "Eleven"), the in-point when the previous word ends after it (SG16y "Killed" 165.086 > 165.071),
# and SG18y 183.66, where the sung "no" rings past its 183.46 word end to the dip before "show" (measured below)
R4_START = {"SG16x": "previous_word_end", "SG16y": "in_point", "SG18x": "previous_word_end", "SG18y": "acoustic_dip",
            "SG20x": "first_word_minus_0.3"}


def r4_words(t0: float, t1: float) -> list[dict]:
    return [w for line in json.loads(C.WORDS.read_text())["lines"] for w in line["words"] if t0 <= w["start"] < t1]


def r4_take(unit: str, n: int) -> dict:
    """The unit's r-1 approval template turned into take n as its _template_notes say (placeholders left in)."""
    value = json.loads((R4_DIR / f"{unit}-approval.template.json").read_text(encoding="utf-8"))
    assert len(value.pop("_template_notes")) == 3
    swap = lambda text: text.replace("-r-1", f"-r-{n}")
    value["unit_group"] = swap(value["unit_group"])
    value["bound_ids"] = {k: swap(v) for k, v in value["bound_ids"].items()}
    value["takes"]["this_take"] = swap(value["takes"]["this_take"])
    return value


def test_r4_windows_cover_one_edit_span_each_and_are_padded_stem_cuts():
    """Each window: starts ~0.3 s before its span's first word (or as R4_START says, never inside a word, never after the
    in-point except SG20x, whose span opens on her still, closed mouth), ends at the span's last word end (SG20x at 208.80,
    before "All"), no next word inside; the wav is the stem's exact samples + digital zeros to exactly the take; take =
    max(4, ceil(span end - window start + 1.0 s)) so a 1 s late mouth still covers the span; sealed in windows.json."""
    plan = (REPO / "outputs/ai-city-takeover/ep01/v4/pilot/s031-048/plan/index.html").read_text(encoding="utf-8")
    book = json.loads((REPO / U.VOCALS).read_text(encoding="utf-8"))
    words_book = json.loads(C.WORDS.read_text())
    every = [w for line in words_book["lines"] for w in line["words"]]
    board = {c["clip"]: c for c in json.loads((REPO / U.BOARD).read_bytes())["clips"]}
    for unit, (clip, span, (t0, t1), secs, lines, d0, d1) in U.R4_UNITS.items():
        spec, (name, a, b) = U.SPECS[unit], R4_SPANS[unit]
        assert span == name and f"{span}</td><td>{a:.3f}–{b:.3f}" in plan and board[clip]["plays"]["t0"] <= a + 0.001 < b
        assert spec["song_window"] == [t0, t1] and spec["duration"] == secs == spec["generation"]["seconds"]
        assert secs == max(4, math.ceil(b - t0 + 1.0)) and 4 <= secs <= 5
        assert C.inside_word(t0, words_book) == [] == C.inside_word(t1, words_book)
        inside = r4_words(t0, t1)
        first, last = inside[0], inside[-1]
        prev = max((w for w in every if w["end"] <= first["start"] and w is not first), key=lambda w: w["end"])
        nxt = min((w for w in every if w["start"] >= t1), key=lambda w: w["start"])
        # every word heard in the span for at least 0.1 s is in the window (s048 holds her still, mouth closed, over the
        # "All" that starts at 208.929); the next word starts after the window ends
        heard = [w for w in every if min(w["end"], b) - max(w["start"], a) >= 0.1 and not (unit == "SG20x" and w["start"] > t1)]
        assert [w["text"] for w in heard if w not in inside] == [] and nxt["start"] > t1 and nxt not in heard
        rule = R4_START[unit]
        if rule == "first_word_minus_0.3":
            assert t0 == round(first["start"] - 0.3, 3) and prev["end"] < t0
        elif rule == "previous_word_end":
            assert t0 == prev["end"] and first["start"] - 0.3 < prev["end"] <= a
        elif rule == "in_point":
            assert t0 == a and first["start"] - 0.3 < prev["end"] and prev["end"] > a
        else:
            assert prev["end"] < first["start"] - 0.3 < t0 < first["start"]
        assert t0 <= a or unit == "SG20x"
        assert t1 == (208.8 if unit == "SG20x" else last["end"]) and (unit != "SG20x" or (last["end"] < t1 < nxt["start"]
                                                                                         and nxt["text"] == "All"))
        assert spec["dialogue"]["verbatim_text"] == lines == " ".join(w["text"] for w in inside)
        assert (spec["dialogue"]["start_seconds"], spec["dialogue"]["end_seconds"]) == (
            d0, d1) == (round(first["start"] - t0, 2), min(round(last["end"] - t0, 2), round(t1 - t0, 2)))
        entry, rel = book["windows"][f"{unit}p"], f"outputs/ai-city-takeover/ep01/v4/pilot/audio/{unit}p.wav"
        assert spec["audio"] == {"asset_id": f"iris-c-v4-{unit.lower()}-vocal", "path": rel, "window": f"{unit}p"}
        assert entry["path"] == rel and entry["song_window"] == [t0, t1] and entry["plays"] == [a, b] and sha(rel) == entry["sha256"]
        data, sr, ch, width = frames(REPO / rel)
        voice, sr_v, n = C.cut_window(C.STEM, t0, t1)
        assert (sr, ch, width) == (sr_v, 1, 2) == (44100, 1, 2) and entry["samples"] == secs * sr == len(data) // 2
        assert data == voice + b"\x00\x00" * (secs * sr - n) and entry["seconds"] == float(secs)
        assert entry["padded"] == {"from": "stem", "from_sha256": book["source_sha256"], "voice_samples": n,
                                        "silence_samples": secs * sr - n, "silence": "digital zeros appended at the end",
                                        "to_seconds": float(secs), "serves": span, "basis": entry["padded"]["basis"]}
    # SG18y: the sung "no" (183.36-183.46 in words.json) rings on in the stem; 183.66 is the dip before "show" (183.781)
    voice, sr, _ = C.cut_window(C.STEM, 183.46, 183.80)

    def level(t: float) -> float:                    # dB of the 20 ms from t (mono stem cut)
        i = round((t - 183.46) * sr)
        x = [int.from_bytes(voice[2 * k:2 * k + 2], "little", signed=True) for k in range(i, i + round(0.02 * sr))]
        return 20 * math.log10(math.sqrt(sum(v * v for v in x) / len(x)) / 32768 + 1e-9)

    assert level(183.48) > -23 and level(183.58) > -26 and level(183.66) < level(183.64) and level(183.66) < level(183.70)
    # the old r3 windows and their wavs are untouched
    old = json.loads((REPO / "outputs/ai-city-takeover/ep01/v4/pilot/audio/windows.json.before-r4-2026-11-25").read_text())
    assert {k: v for k, v in book["windows"].items() if not k.endswith("p") or k == "SG17p"} == old["windows"]
    assert all(sha(v["path"]) == v["sha256"] for v in old["windows"].values())


def test_r4_specs_are_the_board_clip_with_their_own_window():
    """SG16x/y, SG18x/y, SG20x are the board clips SG16 / SG18 / SG20 (no new clip, coverage unit = the clip), the r3
    first frame, look, scene and rules; multimodal 4k with the padded vocal; braced_line = the window's words."""
    for unit, (clip, *_rest) in U.R4_UNITS.items():
        spec, r3 = U.SPECS[unit], U.SPECS[clip]
        assert (spec["clip"], spec["coverage_unit"], spec["plate"], spec["plate_sha256"]) == (
            clip, clip, R4_PLATES[clip], r3["plate_sha256"]) and r3["plate"] == R4_PLATES[clip]
        assert (spec["look"], spec["scene"], spec["rules"], spec["relation"]) == (r3["look"], r3["scene"], r3["rules"], r3["relation"])
        assert spec["generation"] == {**U.GENERATION_LIPSYNC, "seconds": spec["duration"]} and spec["input_mode"] == "multimodal"
        assert spec["braced_line"] == spec["dialogue"]["verbatim_text"] and "take_margin_seconds" not in spec
        assert spec["dialogue"]["language"] == "en" and spec["iris"] is True
    assert [u for u in U.SPECS if u.startswith(("SG16", "SG18", "SG20"))] == ["SG16", "SG18", "SG20", *R4]


def test_r4_prompts_are_the_probe_shape_from_the_r3_first_frame():
    """Each prompt = the r3 prompt's first-frame sentence, then speak / sing to camera in word-for-word sync, the one {}
    sentence with exactly its window's words, camera fixed, she stays put, the shot's blank / red / text rules; no action
    bound to a line (no bowl, microwave going dark, hand) and no other action; SG18 wrapped with no hand, SG20 the bare
    left arm and the still, closed mouth after the line."""
    r3 = dict(re.findall(r"^## s\d{3} · (\w+) · .*?\n\n```prompt\n(.*?)\n```",
                         (REPO / "outputs/ai-city-takeover/ep01/v4/excerpt/flash/s031-048-seedance-r3.md").read_text(
                             encoding="utf-8"), re.S | re.M))
    allowed = ("工程师一直举着手机贴在耳边", "手机背面", "微波炉的显示屏是黑的", "也看不见她的手", "说完嘴闭上，一动不动")   # states
    for unit, prompt in R4_PROMPTS.items():
        spec, clip = U.SPECS[unit], U.R4_UNITS[unit][0]
        assert hashlib.sha256(prompt.encode()).hexdigest() == R4_PROMPT_SHA256[unit]
        start = r3[clip][:r3[clip].index("。") + 1]
        assert prompt.startswith(start) and "嘴唇闭着" in start
        verb = "唱" if clip == "SG18" else "说"
        sync = f"她对着镜头{'说话' if verb == '说' else verb}，口型与{{{{audio:1}}}}里的人声逐字精确同步。"
        braced = f"她用英文{verb}：{{{spec['braced_line']}}}不增不减，不翻译。"
        stay = f"镜头固定不动，{U.R4_SCENE[clip][3]}。"
        assert prompt.index(sync) == len(start) and prompt.index(braced) == len(start) + len(sync)
        assert prompt.index(stay) == len(start) + len(sync) + len(braced) and prompt.endswith("画面中不得出现任何文字。")
        assert prompt.count("{") == 5 and set(U.MARKERS.findall(prompt)) == {"{{image:0}}", "{{audio:1}}"}
        assert spec["braced_line"] == " ".join(w["text"] for w in r4_words(*spec["song_window"]))
        rest = prompt[len(start):].replace(braced, "").replace(stay, "")         # 站 / 坐 / 跪 在原地 is staying put
        for phrase in allowed:
            rest = re.sub(phrase + "[^。]*。", "", rest)
        assert [x for x in SG17_ACTIONS if x in rest] == [], unit
        assert not [x for x in ("碗", "熄灭", "转盘停", "布缝", "伸出", "抓住", "第") if x in prompt[len(start):]], unit
        assert len(re.findall("[A-Za-z]", prompt.replace(braced, "").replace("{{image:0}}", "").replace("{{audio:1}}", ""))) == 0
        assert U.prompt_language_ok(spec, prompt) and not U.prompt_language_ok(U.SPECS[clip], prompt)
        assert all(rule in prompt for rule in U.R4_SCENE[clip][4]) and "除了她左耳耳挂上的小红灯，画面里没有任何红色。" in prompt
        literals = [spec["image"][4], *spec["intent"]["open_event"], *spec["intent"]["close_event"], *spec["intent"]["natural"]]
        assert [x for x in literals if x not in prompt] == []
    for unit in ("SG16x", "SG16y"):
        assert "看不到他的脸" in R4_PROMPTS[unit] and "微波炉的显示屏是黑的" in R4_PROMPTS[unit]
    for unit in ("SG18x", "SG18y"):
        assert "防尘布一直裹到下巴，看不见布下面的衣服，也看不见她的手" in R4_PROMPTS[unit] and "射灯亮度不变" in R4_PROMPTS[unit]
    assert "她的左肩和整条左臂一直裸露，灰色外套只有右臂一只长袖" in R4_PROMPTS["SG20x"] and "工牌是空白的" in R4_PROMPTS["SG20x"]
    assert "她用英文唱：" in R4_PROMPTS["SG18x"] and "她用英文说：" in R4_PROMPTS["SG20x"]


def test_r4_page_and_templates():
    """The page asks one question first, shows each unit's first frame, vocal player, exact prompt, window, span, seconds and
    cost (80 CRD/s × 2), the total and the section ceiling 15,000 (previous 12,800); each template shapes r-1|2 with fresh
    ids, the exact prompt, plate and padded vocal; approvals written after 「按 r4 开拍」 match the templates."""
    import html
    page = (R4_DIR / "index.html").read_text(encoding="utf-8")
    body = page[page.index("<body>"):]
    assert body.index('class="q"') < body.index("<h2>") and body.count("问题：") == 1 and body.count("(Recommended)") == 2
    assert "http://127.0.0.1:8769/pilot/s031-048/r4/index.html" in body and "15,000" in body and "12,800" in body
    est = sum(80 * U.SPECS[u]["duration"] * 2 for u in R4)
    assert est == 3360 and f"约 {est:,} 积分" in body and "8,560" in body and "10,840" in body
    for unit in R4:
        spec, (span, a, b) = U.SPECS[unit], R4_SPANS[unit]
        t0, t1 = spec["song_window"]
        assert f'src="../../../board/plates/{spec["plate"]}.png"' in page and f'src="../../audio/{unit}p.wav"' in page
        assert html.escape(R4_PROMPTS[unit]) in page.replace("<ins>", "").replace("</ins>", "") and R4_PROMPT_SHA256[unit] in page
        assert f"{span} {a:.3f}–{b:.3f}" in page and f"{t0:.3f}–{t1:.3f}" in page and f"{spec['duration']:.3f} s" in page
        assert f"80 积分/秒 × {spec['duration']} s × 2 条 = {80 * spec['duration'] * 2:,}" in page
        assert f"<code>VOCAL={unit}p</code>，<code>T0 = {t0}</code>" in page
    for beat in ("s037d（SG16y）", "放碗这一拍丢失", "s041c（SG18y）", "INS41"):
        assert beat in page
    bound = {b.parent.parent.name: json.loads(b.read_text()) for b in (REPO / "outputs/ai-city-takeover/ep01/v4/pilot").glob(
        "sd-*/*/operator-bound.json")}
    own = {f"sd-{u}-r-{k}" for u in R4 for k in (1, 2, 3)}       # r4's own takes (SG18y r-3 replaced a no-effect r-1)
    used = {v.get(k) for name, v in bound.items() if name not in own for k in ("attempt_id", "policy_id", "reservation_id")}
    ids, page_rel = [], "outputs/ai-city-takeover/ep01/v4/pilot/s031-048/r4/index.html"
    for unit in R4:
        spec = U.SPECS[unit]
        for n in (1, 2):
            value = r4_take(unit, n)
            assert sorted(placeholders(value)) == sorted([value["question"], value["user_quote"], value["approved_at"]])
            assert value["preview_page"] == {"path": page_rel, "sha256": sha(page_rel)}
            assert value["prompts"] == {unit: {"text": R4_PROMPTS[unit], "sha256": R4_PROMPT_SHA256[unit]}}
            assert value["preview_artifacts"] == [
                {"path": spec["image"][1], "sha256": spec["plate_sha256"], "role": f"{unit} reference image"},
                {"path": spec["audio"]["path"], "sha256": sha(spec["audio"]["path"]), "role": f"{unit} vocal"}]
            assert value["generation"] == spec["generation"] and value["identity_waivers"] == ["IRIS"]
            assert value["budget"] == {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 400, "cumulative_CRD": 400}
            assert value["takes"]["folders"] == [f"sd-{unit}-r-1", f"sd-{unit}-r-2"] and value["takes"]["this_take"] == f"sd-{unit}-r-{n}"
            assert value["takes"]["r4"] == {"units": list(R4), "total_takes": 10, "total_ceiling_CRD": 4000,
                                            "section_ceiling_CRD": 15000, "previous_section_ceiling_CRD": 12800}
            ident = f"iris-{unit.lower()}-r-{n}"
            assert value["bound_ids"] == {"attempt_id": f"{ident}-source-001", "policy_id": f"{ident}-source-001",
                                          "reservation_id": f"{ident}-reservation-001"}
            ids += value["bound_ids"].values()
            folder = REPO / "outputs/ai-city-takeover/ep01/v4/pilot" / f"sd-{unit}-r-{n}"
            written = folder / "preview-approval.json"
            assert folder.is_dir()
            if written.exists():                                   # the main session wrote it after 「按 r4 开拍 (Recommended)」
                approval = json.loads(written.read_text(encoding="utf-8"))
                keys = ("preview_page", "preview_artifacts", "prompts", "generation", "budget", "bound_ids", "takes")
                assert {k: approval[k] for k in keys} == {k: value[k] for k in keys}, folder.name
            if folder.name in bound:                               # its operator bound exactly the template's ids
                assert {k: bound[folder.name][k] for k in value["bound_ids"]} == value["bound_ids"]
    assert len(set(ids)) == 5 * 2 * 2 and not set(ids) & used


@pytest.mark.parametrize("unit", R4)
def test_r4_templates_pass_draft_materialize_and_lint(lane, monkeypatch, capsys, unit):
    """The r-1 template with only its placeholders filled drafts, resolves the 4k request with the exact prompt, first frame
    and padded vocal, and passes every lint check (tmp lane; nothing is written under the repo, nothing is called)."""
    monkeypatch.setattr(U, "VOCALS", "outputs/ai-city-takeover/ep01/v4/pilot/audio/windows.json")
    spec = U.SPECS[unit]
    value = r4_take(unit, 1) | {"question": "q", "user_quote": "按这 5 条开拍 (Recommended)", "approved_at": "2026-11-25T08:00:00Z"}
    approve(lane, value)
    U.draft(unit)
    node = f"node_dryrunr4{unit.lower()}"
    secs = spec["duration"]
    profile = PROFILE | {"input_mode": "multimodal", "node_id": node, "duration_seconds": secs, "benefit_amount": secs,
                         "credit_upper_bound": 400}
    path = lane / unit / "profile.json"
    path.write_text(json.dumps(profile))
    U.materialize(unit, path)
    capsys.readouterr()
    U.show(unit)
    request = json.loads(capsys.readouterr().out)
    assert (request["model"], request["input_mode"], request["seconds"], request["resolution"], request["aspect"],
            request["prompt"]) == ("seedance_2.0_vip", "multimodal", secs, "4k", "16:9", R4_PROMPTS[unit])
    assert [b["asset_sha256"] for b in request["image_bindings"]] == [spec["plate_sha256"]]
    assert [b["asset_sha256"] for b in request["media_bindings"]] == [sha(spec["audio"]["path"])]
    bound = {"schema_version": "iris-v4-unit/1", "unit": unit, "task": f"IRIS EP01 v4 {unit}（{U.R4_UNITS[unit][1]}，r-1）",
             "user_quote": value["user_quote"], "preview_approval": str(lane / "preview-approval.json"), **value["bound_ids"],
             "max_submit_count": 1, "automatic_retries": 0, "operator_currency": "CRD", "operator_ceiling": 400,
             "ledger": "ledger.json", "cumulative_submit_ceiling": 1, "cumulative_operator_credit_ceiling": 400,
             "issued_at": "2026-11-25T08:30:00+00:00", "expires_at": "2026-11-25T14:30:00+00:00", "stop_on_unknown": True}
    (lane / unit / "operator-bound.json").write_text(json.dumps(bound, ensure_ascii=False))
    (lane / unit / "node-created.json").write_text(json.dumps({"node_id": node, "empty": True}))
    (lane / "continuity-report.json").write_text(json.dumps({"units": {unit: {"verdict": "ready"}}}))
    code = "import json, sys; sys.path.insert(0, sys.argv[1]); import lint; print(json.dumps(lint.lint(sys.argv[2])['checks']))"
    env = {k: v for k, v in os.environ.items() if k not in {"SD_PILOT", "SD_UNITS"}} | {
        "SD_TRIAL": str(lane), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONWARNINGS": "ignore"}
    out = subprocess.run([sys.executable, "-c", code, str(GEN), unit], cwd=REPO, capture_output=True, text=True, env=env,
                         check=True).stdout
    checks = json.loads(out.strip().splitlines()[-1])
    assert [k for k, v in checks.items() if not v] == []


def test_r4_draft_blocks_a_window_or_padding_that_is_not_the_spec(lane, monkeypatch):
    """The own-window path still fails closed: a sealed window other than the spec's, or a vocal not padded to the take."""
    monkeypatch.setattr(U, "VOCALS", "outputs/ai-city-takeover/ep01/v4/pilot/audio/windows.json")
    approve(lane, r4_take("SG16x", 1) | {"question": "q", "user_quote": "q (Recommended)", "approved_at": "2026-11-25T08:00:00Z"})
    monkeypatch.setitem(U.SPECS["SG16x"], "song_window", [161.338, 163.6])
    assert "is not the board clip window" in blocked("SG16x")
    monkeypatch.setitem(U.SPECS["SG16x"], "song_window", [161.338, 163.523])
    monkeypatch.setitem(U.SPECS["SG16x"], "duration", 5)
    monkeypatch.setitem(U.SPECS["SG16x"], "generation", {**U.SPECS["SG16x"]["generation"], "seconds": 5})
    approve(lane, r4_take("SG16x", 1) | {"question": "q", "user_quote": "q (Recommended)", "approved_at": "2026-11-25T08:00:00Z",
                                         "generation": U.SPECS["SG16x"]["generation"]})
    assert "padded vocal is 4000 ms; it must be exactly the 5 s take" in blocked("SG16x")
