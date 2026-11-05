"""Focused offline tests for the v3 Seedance lane: U021 multimodal lip-sync take, U023 first frame, SD_TRIAL routing.

  PYTHONDONTWRITEBYTECODE=1 uv run pytest -p no:cacheprovider outputs/ai-city-takeover/ep01/v3/gen/test_unit_lanes.py

Every case runs unit.py in a subprocess against a tmp trial folder; nothing is written under the repo and nothing is called.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

GEN = Path(__file__).resolve().parent
REPO = GEN.parents[4]
PLATE = "outputs/ai-city-takeover/ep01/v3/plates/raw/P-gap-mcu-sing.png"
VOCAL = "outputs/ai-city-takeover/ep01/v3/pilot/audio/U021.wav"
PROMPT = ("{{image:0}}中的她对着镜头唱歌，口型与{{audio:1}}里的人声逐字精确同步。中近景，她闭着眼睛投入地唱，神情平静，面无表情，"
          "眉头舒展；唱到句尾慢慢睁开眼睛，平静地看着镜头。镜头全程锁定，一镜到底。")   # user-confirmed text, 2026-11-04
PROFILE = {"model_id": "seedance_2.0_vip", "account_sha256": "72af2f312b64012199e6eb0453d72b268e08bc104629637afcc59d36f50e3bbe",
           "project_id": "829df260-5a63-4f0d-8265-8353dc693b3b", "duration_seconds": 5, "resolution": "1080p",
           "aspect_ratio": "16:9", "benefit_amount": 5, "benefit_type": "seedance_20_pro_1080p_output"}
U023_REQUEST_HASH = "dfbca2663c81274d1b45d8c0a2b9e3ba97367ebf9fb5aa1577f92848f45cae98"   # original lane, node_dryrun0001


def sha(rel: str) -> str:
    return hashlib.sha256((REPO / rel).read_bytes()).hexdigest()


def approval(prompt: str = PROMPT) -> dict:
    return {"schema": "iris-v3-preview-approval/1", "unit_group": "pilot-seedance-lipsync-r3", "question": "test",
            "user_quote": "test", "approved_at": "2026-11-04T00:00:00+00:00",
            "preview_artifacts": [{"path": PLATE, "sha256": sha(PLATE), "role": "U021 reference image"},
                                  {"path": VOCAL, "sha256": sha(VOCAL), "role": "U021 vocal"}],
            "prompts": {"U021": {"text": prompt, "sha256": hashlib.sha256(prompt.encode()).hexdigest()}},
            "generation": {"model": "seedance_2.0_vip", "mode": "multimodal", "seconds": 5, "resolution": "1080p",
                           "aspect": "16:9", "audio": "reference_audio"},
            "budget": {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 200, "cumulative_CRD": 200},
            "identity_waivers": ["IRIS"]}


def run(*args: str, **env: str) -> subprocess.CompletedProcess:
    base = {k: v for k, v in os.environ.items() if k not in {"SD_TRIAL", "SD_PILOT", "SD_UNITS"}}
    return subprocess.run([sys.executable, str(GEN / "unit.py"), *args], cwd=REPO, capture_output=True, text=True,
                          env=base | {"PYTHONDONTWRITEBYTECODE": "1"} | env)


def trial(tmp_path: Path, value: dict) -> Path:
    (tmp_path / "preview-approval.json").write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def blocked(result: subprocess.CompletedProcess) -> str:
    assert result.returncode == 2, result.stderr
    return json.loads(result.stderr.strip().splitlines()[-1])["reason"]


def test_u021_multimodal_resolves_the_expected_request(tmp_path):
    folder = trial(tmp_path, approval())
    (folder / "U021").mkdir()
    profile = folder / "U021" / "profile.json"
    profile.write_text(json.dumps(PROFILE | {"input_mode": "multimodal", "node_id": "node_dryrun0021",
                                             "credit_upper_bound": 200}))
    assert run("draft", "U021", SD_TRIAL=str(folder)).returncode == 0
    done = run("materialize", "U021", "--profile", str(profile), SD_TRIAL=str(folder))
    assert done.returncode == 0, done.stderr
    shown = run("show", "U021", SD_TRIAL=str(folder))
    request = json.loads(shown.stdout)
    assert (request["model"], request["input_mode"], request["request_mode"], request["seconds"], request["resolution"],
            request["aspect"], request["native_audio"]) == (
        "seedance_2.0_vip", "multimodal", "reference_to_video", 5, "1080p", "16:9", True)
    assert request["image_bindings"] == [{"role": "reference", "asset_id": "iris-c-v3-u021-reference",
        "asset_sha256": sha(PLATE), "mime_type": "image/png", "width": 1672, "height": 941}]
    assert request["media_bindings"] == [{"kind": "audio", "role": "reference_audio", "asset_id": "iris-c-v3-u021-vocal",
        "asset_sha256": sha(VOCAL), "mime_type": "audio/wav", "duration_millis": 4360}]
    assert request["prompt"] == PROMPT                       # the approved text is the native text, markers included


def _without_vocal(value):
    value["preview_artifacts"] = value["preview_artifacts"][:1]


def _vocal_sha(value):
    value["preview_artifacts"][1]["sha256"] = "0" * 64


def _other_vocal(value):
    other = "outputs/ai-city-takeover/ep01/v3/pilot/audio/U022.wav"
    value["preview_artifacts"][1] |= {"path": other, "sha256": sha(other)}


def _extra_input(value):
    value["preview_artifacts"].append({"path": PLATE, "sha256": sha(PLATE), "role": "U021 first frame"})


def _first_frame_generation(value):
    value["generation"] |= {"mode": "first_frame", "audio": None}


@pytest.mark.parametrize("mutate,reason", [
    (_without_vocal, "exactly one preview artifact with role 'U021 vocal'"),
    (_vocal_sha, "approved vocal changed since the approval"),
    (_other_vocal, "is not the window this unit was written for"),
    (_extra_input, "inputs this unit does not send"),
    (_first_frame_generation, "approval generation must be exactly"),
])
def test_u021_blocks_anything_the_approval_does_not_hold(tmp_path, mutate, reason):
    value = approval()
    mutate(value)
    assert reason in blocked(run("draft", "U021", SD_TRIAL=str(trial(tmp_path, value))))


@pytest.mark.parametrize("prompt", [PROMPT.replace("{{image:0}}", "{{image:1}}"),     # 1-based markers do not bind
                                    PROMPT.replace("{{audio:1}}", "人声"),
                                    PROMPT.replace("中近景", "MCU"),
                                    PROMPT.replace("唱到句尾慢慢睁开眼睛，", "")])    # a required phrase dropped
def test_u021_prompt_lint(tmp_path, prompt):
    reason = blocked(run("draft", "U021", SD_TRIAL=str(trial(tmp_path, approval(prompt)))))
    assert "native prompt" in reason


def test_u023_first_frame_request_is_unchanged(tmp_path):
    (tmp_path / "U023").mkdir()
    profile = tmp_path / "U023" / "profile.json"
    profile.write_text(json.dumps(PROFILE | {"input_mode": "first_frame", "node_id": "node_dryrun0001",
                                             "credit_upper_bound": 165}))
    assert run("draft", "U023", SD_UNITS=str(tmp_path)).returncode == 0     # approval: the real pilot/sd/
    done = run("materialize", "U023", "--profile", str(profile), SD_UNITS=str(tmp_path))
    assert done.returncode == 0, done.stderr
    result = json.loads((tmp_path / "U023" / "materialization-result.json").read_text())
    assert result["request_hash"] == U023_REQUEST_HASH
    assert json.loads((tmp_path / "U023" / "prepare-result.json").read_text())["resolved_request"]["media_bindings"] == []


@pytest.mark.parametrize("env,pilot,units", [
    ({}, "outputs/ai-city-takeover/ep01/v3/pilot/sd", "outputs/ai-city-takeover/ep01/v3/gen"),
    ({"SD_TRIAL": "outputs/ai-city-takeover/ep01/v3/pilot/sd-r3"}, "outputs/ai-city-takeover/ep01/v3/pilot/sd-r3",
     "outputs/ai-city-takeover/ep01/v3/pilot/sd-r3"),
    ({"SD_TRIAL": "outputs/ai-city-takeover/ep01/v3/pilot/sd-r3", "SD_UNITS": "/tmp/units"},
     "outputs/ai-city-takeover/ep01/v3/pilot/sd-r3", "/tmp/units"),
])
def test_sd_trial_routing(env, pilot, units):
    code = ("import json, sys; sys.path.insert(0, sys.argv[1]); import unit as U; "
            "print(json.dumps([str(U.PILOT), str(U.UNITS), str(U.APPROVAL), str(U.REPORT)]))")
    base = {k: v for k, v in os.environ.items() if k not in {"SD_TRIAL", "SD_PILOT", "SD_UNITS"}}
    out = subprocess.run([sys.executable, "-c", code, str(GEN)], cwd=REPO, capture_output=True, text=True, check=True,
                         env=base | {"PYTHONDONTWRITEBYTECODE": "1"} | env).stdout
    assert json.loads(out) == [str(REPO / pilot), str(REPO / units), str(REPO / pilot / "preview-approval.json"),
                               str(REPO / pilot / "continuity-report.json")]
