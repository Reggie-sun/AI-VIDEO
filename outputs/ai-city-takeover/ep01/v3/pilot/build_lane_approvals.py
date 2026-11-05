"""Write the pilot's lane approvals and package revision r2 from the user's exact answers (2026-11-04).

- r2 = the package approved at checkpoint B (preview-inputs.json, left unchanged on disk) plus the two digital-human
  action-text rewrites the user approved (「同意这两处改写」) -> preview-inputs-r2.json. U045 is postponed: the user
  chose 「改用多参考模式」 (redesign with an IRIS identity sheet, new preview, new approval).
- pilot/oh/preview-approval.json (iris-v3-preview-approval/1, five digital-human takes, read by gen/omnihuman.py) and
  pilot/sd/preview-approval.json (U023 only, read by gen/unit.py and gen/lint.py). No identity waiver anywhere.
- preview-approval-r2.json (user-preview-approval/1) for the six r2 units.
Every approved input is re-read and must still match its recorded SHA-256. Existing files are never overwritten.
Run from the repository root: uv run python outputs/ai-city-takeover/ep01/v3/pilot/build_lane_approvals.py
"""
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ai_video.production.preview_approval import KIND, preview_approval_authoring_input
from ai_video.production.reference_authoring import director_coverage_authoring_input

PILOT = Path(__file__).resolve().parent
V3 = PILOT.parent
REPO = V3.parents[3]
REL = "outputs/ai-city-takeover/ep01/v3/pilot/"

Q_B = ("动画分镜 a2：http://127.0.0.1:8768/review/animatic-a2.html\n试拍参考包：http://127.0.0.1:8768/pilot/preview.html\n"
       "（a1 对照：http://127.0.0.1:8768/review/animatic-a1.html）\n\n这是检查点 B：请以正常速度带声音看完 a2，再看试拍参考包"
       "（5 条数字人唱段 + 2 条 Seedance 首帧镜头）。你认可后我把它封存为 preview_approval，改掉上面三处小问题，做提交前连续性报告，"
       "再进入阶段 7 付费试拍（预留上限 1155 积分，不是报价）。怎么处理？")
A_B = "认可，进入试拍"
Q_TEXT = ("试拍参考包：http://127.0.0.1:8768/pilot/preview.html\n\n数字人动作描述要求只写正向动作。U020 里有「头几乎不动」，"
          "U027 里有「唱完最后一个字后嘴慢慢合上，停住不动」；上次同类否定说法（SC4「几乎不笑」）被场记判为不可提交。"
          "改成正向说法可以吗？U020 改为「头部保持平稳」；U027 改为「唱完最后一个字后嘴慢慢合上，静静停住」。其余文字不变。")
A_TEXT = "同意这两处改写"
Q_U045 = ("试拍参考包：http://127.0.0.1:8768/pilot/preview.html\n\nU045（群像里她跨过地上白线）用 Seedance 首帧模式，只能带一张首帧图，"
          "没法另附 IRIS 的身份设定图；参考包页面也没问过你这一点。项目规定这种情况要你明确同意才能提交。怎么处理？")
A_U045 = "改用多参考模式"
REWRITES = {"U020": ("头几乎不动", "头部保持平稳"),
            "U027": ("唱完最后一个字后嘴慢慢合上，停住不动", "唱完最后一个字后嘴慢慢合上，静静停住")}


def sha_file(rel: str) -> str:
    return hashlib.sha256((REPO / rel).read_bytes()).hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def checked(entry: dict) -> dict:
    if sha_file(entry["path"]) != entry["sha256"]:
        raise SystemExit(f"{entry['path']} changed since the user approved it")
    return entry


def write_new(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=1)
        handle.write("\n")


def main() -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    page = {"path": REL + "preview.html", "sha256": sha_file(REL + "preview.html")}
    inputs_b = {"path": REL + "preview-inputs.json", "sha256": sha_file(REL + "preview-inputs.json")}
    sealed_b = json.loads((PILOT / "preview-approval.json").read_text(encoding="utf-8"))
    seen_b = {a["path"]: a["sha256"] for a in sealed_b["preview_artifacts"]}
    if seen_b.get(page["path"]) != page["sha256"] or seen_b.get(inputs_b["path"]) != inputs_b["sha256"]:
        raise SystemExit("the package page or inputs changed since checkpoint B")

    # ---- package revision r2: only the two approved phrases change
    base = json.loads((REPO / inputs_b["path"]).read_text(encoding="utf-8"))
    r2 = copy.deepcopy(base)
    changes = []
    for unit, (old, new) in REWRITES.items():
        take = r2["digital_human"]["takes"][unit]
        if take["action_prompt"].count(old) != 1 or sha_text(take["action_prompt"]) != take["action_prompt_sha256"]:
            raise SystemExit(f"{unit}: approved action text not as shown to the user")
        take["action_prompt"] = take["action_prompt"].replace(old, new)
        take["action_prompt_sha256"] = sha_text(take["action_prompt"])
        changes.append({"unit": unit, "from": old, "to": new})
    r2["seedance"]["units"]["U045"]["status"] = f"postponed: the user chose 「{A_U045}」 (redesign with an IRIS identity sheet, new preview, new approval)"
    r2["revision"] = {"id": "r2", "of": inputs_b, "changes": changes, "question": Q_TEXT, "user_quote": A_TEXT,
                      "u045": {"question": Q_U045, "user_quote": A_U045}, "recorded_at": now}
    write_new(PILOT / "preview-inputs-r2.json", r2)
    inputs_r2 = {"path": REL + "preview-inputs-r2.json", "sha256": sha_file(REL + "preview-inputs-r2.json")}
    package = [dict(page, role="package page reviewed at checkpoint B"), dict(inputs_b, role="package inputs approved at checkpoint B"),
               dict(inputs_r2, role="package revision r2: the two action-text rewrites the user approved")]

    # ---- digital-human lane approval (five takes, texts from r2)
    takes, artifacts = {}, {}
    for unit, t in r2["digital_human"]["takes"].items():
        image, audio = checked(dict(t["image"])), checked(dict(t["audio"]))
        takes[unit] = {"image": {"path": image["path"], "sha256": image["sha256"]},
                       "audio": {"path": audio["path"], "sha256": audio["sha256"], "seconds": audio["seconds"]},
                       "action_prompt": t["action_prompt"], "action_prompt_sha256": t["action_prompt_sha256"]}
        artifacts.setdefault(image["path"], {"path": image["path"], "sha256": image["sha256"], "role": []})["role"].append(f"{unit} still")
        artifacts.setdefault(audio["path"], {"path": audio["path"], "sha256": audio["sha256"], "role": []})["role"].append(f"{unit} vocal")
    oh = {"schema": "iris-v3-preview-approval/1", "unit_group": "pilot-digital-human",
          "question": Q_B + "\n\n---\n\n" + Q_TEXT, "user_quote": f"{A_B} ／ {A_TEXT}", "approved_at": now,
          "approved_at_basis": "time the main session recorded both answers, minutes after the user gave them in this session",
          "preview_page": page, "preview_inputs": inputs_r2,
          "preview_artifacts": [dict(a, role="; ".join(a["role"])) for a in artifacts.values()] + package,
          "takes": takes, "mode": r2["digital_human"]["mode"],
          "budget": {"generations": 5, "retries": 0, "operator_ceiling_per_take_CRD": 165, "cumulative_CRD": 825}}
    write_new(PILOT / "oh/preview-approval.json", oh)

    # ---- Seedance lane approval (U023 only; U045 postponed)
    u023 = base["seedance"]["units"]["U023"]
    first = checked(dict(u023["first_frame"]))
    if sha_text(u023["prompt"]) != u023["prompt_sha256"]:
        raise SystemExit("U023: approved prompt text not as shown to the user")
    sd = {"schema": "iris-v3-preview-approval/1", "unit_group": "pilot-seedance", "question": Q_B, "user_quote": A_B,
          "approved_at": now, "approved_at_basis": oh["approved_at_basis"], "preview_page": page, "preview_inputs": inputs_b,
          "preview_artifacts": [{"path": first["path"], "sha256": first["sha256"], "role": "U023 first frame"}] + package[:2],
          "prompts": {"U023": {"text": u023["prompt"], "sha256": u023["prompt_sha256"]}},
          "generation": {"model": "seedance_2.0_vip", "mode": "first_frame", "seconds": 5, "resolution": "1080p",
                         "aspect": "16:9", "audio": None},
          "budget": {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 165, "cumulative_CRD": 165}}
    write_new(PILOT / "sd/preview-approval.json", sd)

    # ---- r2 sealed approval (user-preview-approval/1) for the six units still in the pilot
    coverage_hash, _ = director_coverage_authoring_input(json.loads((V3 / "director-coverage.json").read_text(encoding="utf-8")))
    sealed = [dict(a) for a in oh["preview_artifacts"]] + [sd["preview_artifacts"][0]]
    sealed += [{"path": a["path"], "sha256": a["sha256"], "role": a["role"]} for a in sealed_b["preview_artifacts"]
               if a["path"].endswith("animatic-a2-review.mp4")]
    payload = {"kind": KIND, "coverage_hash": coverage_hash, "unit_ids": sorted([*takes, "U023"]),
               "preview_artifacts": sealed, "user_quote": f"{A_B} ／ {A_TEXT}"}
    approval_hash, _ = preview_approval_authoring_input(payload)
    write_new(PILOT / "preview-approval-r2.json", payload)
    print(json.dumps({"r2_inputs": inputs_r2["sha256"], "oh_approval": sha_file(REL + "oh/preview-approval.json"),
                      "sd_approval": sha_file(REL + "sd/preview-approval.json"), "r2_approval_hash": approval_hash,
                      "units": payload["unit_ids"], "changes": changes}, ensure_ascii=False))


if __name__ == "__main__":
    main()
