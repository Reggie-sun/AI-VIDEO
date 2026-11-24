#!/usr/bin/env python3
"""Write the v4 Director coverage (schema 4) mechanically from the user-approved board; nothing is invented.

  uv run python outputs/ai-city-takeover/ep01/v4/gen/build_coverage.py [--check]

Director authorization: the Director (coordinator) asked for this file on 2026-11-17, written mechanically from the
board the user approved that day (「可以，按这个往下做」 after the plated cards; earlier 「先出底片贴上卡片再审
(Recommended)」, logs/decisions.md and the 2026-11-17 storyboard checkpoint record).

Sources, read as they are:
- request.creative_input_evidence: every 「…」 quote of brief.md "## 使用者原话" in order, then the two board approval
  quotes; one creative constraint per quote (all global except the sing quote, which binds the sung clips).
- coverage_units: one per board clip (board/shots.json clips[], board order), unit_id = clip id, duration = clip seconds,
  from the clip's shot: objective / open_state / close_state / visible_change from `action` (open = its first clause,
  (an insert clip carries its own `insert` {framing, action, camera}, read instead of the shot's; INS16, 2026-11-22)
  close = the text after 结束：), camera_intent = `camera`, shot_scale from `framing`, camera_treatment from the camera
  text's own words, beat_function from the song `section`; transition_out cut (the last clip: end).
- intent_items: one explicit_user item per quote, its statement the quote itself, grouped by the table GROUP below.
target_duration_seconds is the sum of the clip seconds: the units are the generation clips (windows include handles;
plate3d shots are not generated), not the 273.32 s film.

Writes outputs/ai-city-takeover/ep01/v4/director-coverage.json and proves it with the repo's own owner
(ai_video.production.reference_authoring.director_coverage_authoring_input → validate_director_coverage); --check
validates the existing file against a fresh build without writing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

P = Path(__file__).resolve().parent
V4 = P.parent
REPO = P.parents[4]
sys.path.insert(0, str(REPO))

from ai_video.production.reference_authoring import director_coverage_authoring_input  # noqa: E402

BOARD = V4 / "board/shots.json"
BRIEF = V4 / "brief.md"
OUT = V4 / "director-coverage.json"
BOARD_APPROVAL = ["先出底片贴上卡片再审 (Recommended)", "可以，按这个往下做"]   # user, 2026-11-17
SING = "我们只需要让人物真的表现在唱歌就好"                                    # beat-specific: the sung clips
SCALE = {"ECU": "extreme_close_up", "CU": "close_up", "MCU": "close_up", "MS": "medium", "OTS": "medium",
         "MWS": "full", "WS": "wide", "EWS": "extreme_wide"}
BEAT = {"Intro": "establish", "Spoken": "establish", "Verse": "reveal", "Chorus": "escalate", "Post-Chorus": "escalate",
        "Final Chorus": "escalate", "Bridge": "reversal", "Outro": "payoff"}
CAMERA = (("truck", "横移"), ("tracking", "跟拍|跟在|后退"), ("handheld", "手持"), ("push_in", "推近|慢推"))
# quote → intent group (quotes not listed are must_happen)
GROUP = {"这种歌都是要带点不寻常,侵略性,不羁": "preferred_performance", "表情别太刻意了": "preferred_performance",
         "AI 味重，不像真拍的": "must_not_happen", "场景单调，全在机房": "must_not_happen",
         "人物只会摆姿势瞪眼": "must_not_happen", "概念太空太套路": "must_not_happen", "并且歌词太少": "must_not_happen"}


def quotes() -> list[str]:
    text = BRIEF.read_text(encoding="utf-8")
    section = re.search(r"^## 使用者原话[^\n]*\n(.*?)(?=^## )", text, re.S | re.M)
    if not section:
        raise SystemExit("brief.md has no 使用者原话 section")
    found = re.findall(r"「(.+?)」", section.group(1))
    return list(dict.fromkeys(found)) + BOARD_APPROVAL


def beat(section: str) -> str:
    key = next((k for k in sorted(BEAT, key=len, reverse=True) if section.startswith(k)), None)
    if key is None:
        raise SystemExit(f"no beat_function for section {section!r}")
    return BEAT[key]


def treatment(camera: str) -> str:
    kinds = [kind for kind, words in CAMERA if re.search(words, camera)]
    return "compound" if len(kinds) > 1 else kinds[0] if kinds else "static"


def states(action: str) -> tuple[str, str, str]:
    main, _, close = action.partition("结束：")
    main, close = main.strip().rstrip("。"), close.strip().rstrip("。")
    first = re.split(r"[。；]", main, maxsplit=1)[0]
    if not close:                                         # no explicit end state: the last clause of the action
        close = re.split(r"[。；]", main)[-1]
    return main, first, close


def build() -> dict:
    board = json.loads(BOARD.read_bytes())
    shots = {s["id"]: s for s in board["shots"]}
    said = quotes()
    evidence = "\n".join(said)
    evidence_sha = hashlib.sha256(evidence.encode("utf-8")).hexdigest()
    ids = {q: f"C-{i:02d}" for i, q in enumerate(said, 1)}
    constraints = [{"constraint_id": ids[q], "scope": "beat_specific" if q == SING else "global", "source_text": q}
                   for q in said]
    every = [ids[q] for q in said if q != SING]
    units = []
    for index, clip in enumerate(board["clips"]):
        if len(clip["used_by"]) != 1:
            raise SystemExit(f"{clip['clip']} is used by {clip['used_by']}; one shot per clip expected")
        shot = {**shots[clip["used_by"][0]], **clip.get("insert", {})}
        main, first, close = states(shot["action"])
        units.append({"unit_id": clip["clip"], "duration_seconds": clip["seconds"], "beat_function": beat(shot["section"]),
                      "objective": f"{shot['section']} · {clip['clip']}（{shot['id']}）：{main}",
                      "open_state": first, "close_state": close, "shot_scale": SCALE[shot["framing"]],
                      "camera_treatment": treatment(shot["camera"]), "camera_intent": shot["camera"],
                      "visible_change": shot["action"],
                      "transition_out": "end" if index == len(board["clips"]) - 1 else "cut",
                      "constraint_ids": every + ([ids[SING]] if clip["tier"] == "sung" else [])})
    items = [{"intent_item_id": f"I-{ids[q][2:]}", "statement": "使用者原话：" + q,
              "source_refs": [{"source_hash": evidence_sha, "locator": "request.creative_input_evidence",
                               "intent_item_id": f"I-{ids[q][2:]}", "quote": q, "origin": "explicit_user"}],
              "origin": "explicit_user", "related_intent_ids": []} for q in said]
    groups = {g: [] for g in ("must_happen", "must_not_happen", "preferred_performance", "timing_targets",
                              "acceptable_variation")}
    for q, item in zip(said, items):
        groups[GROUP.get(q, "must_happen")].append({"intent_item_id": item["intent_item_id"]})
    board_sha = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    rationale = ("按作者的制作方法：三位导演各出一版分镜（fashion / meme / narrative），三位评审（观众、导演、制片）打分，"
                 "总导演合并成一版，经作者审计表与事实核对后，使用者看过贴了底片的卡片并认可「可以，按这个往下做」。"
                 "一首 4:33 的歌要逐句落在她嘴上、按段落换地点和造型，一条机位轨迹承载不了，所以是多镜头；"
                 f"这里每个覆盖单元就是分镜 board/shots.json（sha256 {board_sha}）的一个生成片段，逐字取自分镜。")
    return {"schema_version": "4",
            "request": {"creative_input_kind": "direction", "creative_input_evidence": evidence,
                        "creative_constraints": constraints,
                        "target_duration_seconds": round(sum(u["duration_seconds"] for u in units), 3),
                        "coverage_strategy": "multi_shot", "strategy_source": "agent_directed",
                        "director_decision_rationale": rationale, "strategy_request_evidence": None,
                        "director_skill": "open-video"},
            "coverage_units": units, "intent_items": items, "intent_groups": groups}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="validate the existing file equals a fresh build; no write")
    args = ap.parse_args()
    coverage = build()
    coverage_hash, _ = director_coverage_authoring_input(coverage)      # raises CoverageValidationError if invalid
    payload = json.dumps(coverage, ensure_ascii=False, indent=1) + "\n"
    if args.check:
        same = OUT.is_file() and OUT.read_text(encoding="utf-8") == payload
        print(json.dumps({"path": str(OUT.relative_to(REPO)), "matches_fresh_build": same, "coverage_hash": coverage_hash}))
        return 0 if same else 2
    OUT.write_text(payload, encoding="utf-8")
    print(json.dumps({"path": str(OUT.relative_to(REPO)), "units": len(coverage["coverage_units"]),
                      "constraints": len(coverage["request"]["creative_constraints"]),
                      "target_duration_seconds": coverage["request"]["target_duration_seconds"],
                      "coverage_hash": coverage_hash, "sha256": hashlib.sha256(payload.encode()).hexdigest()},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
