#!/usr/bin/env python3
"""Write one preview-approval.json per approved unit from a user-approved preview page; local only.

  uv run python outputs/ai-city-takeover/ep01/v4/gen/excerpt_approvals.py [--set excerpt|v4r1] \
      --question "<the question the user was asked>" --quote "<the user's words, verbatim>" --approved-at <UTC ISO> \
      [--units MO04 SG02 ...]

--set excerpt (default): pilot/excerpt/ page and inputs → pilot/sd-<UNIT>/. Every excerpt unit is superseded now (MO06
by v4r1, SG04 / MO07 by round 2, MO04 / SG02 / MO05 by the 2026-11-20 opening set, see pilot/opening/RUNBOOK.md).
--set v4r1: v4 round 1 (2026-11-18, excerpt/flash/v4r1.html, 「s011 选 1，s012 选 1，开拍」) → pilot/sd-MO06-w1/ and
pilot/sd-SG03-w1/ with the exact approved short prompts held in V4R1 below, the W1 plates p011-w1 / p012-w1 (the same
bytes as excerpt/flash/v4r1/V11a-1.png / V12a-1.png), 4k, 1 generation, 0 retries, ceilings MO06 600 / SG03 700 CRD.
--set v4r1b: MO06 only → pilot/sd-MO06-w1b/. The continuity supervisor blocked V11a-1 (bare RIGHT shoulder; every other
W1 still bares the LEFT one); on excerpt/flash/shoulder.html the user chose 「改用 s011-2 (Recommended)」: plate p011-w1b
(= V11a-2.png), the same approved round-1 prompt, 4k, 1 generation, 0 retries, ceiling 600 CRD. The approval also names
the round-1 approval it replaces (pilot/sd-MO06-w1/preview-approval.json, left untouched).
--set sg03c: SG03C only → pilot/sd-SG03C/. The s012 redesign's closed-eye singing close-up (2026-11-19): plate p012c-w1
(= excerpt/flash/design/D1-b.png), the prompt shown on excerpt/flash/closeup.html, vocal pilot/audio/SG03C.wav (sealed
window 46.93-50.93), 4k, 1 generation, 0 retries, ceiling 400 CRD. The user delegated the call to the main session after
seeing that page (「没有我只是让你自己判断」).
--set sg03c-b: SG03C → pilot/sd-SG03C-b/ after the plate swap: the continuity supervisor blocked D1-b (RIGHT shoulder
bare, strap reversed vs the accepted SG03-w1); the main session, under the same delegation, remade it as plate p012c-w1b
(= design/D2-b.png). Same prompt and vocal, 4k, 1 generation, 0 retries, ceiling 400 CRD; names the replaced approval
pilot/sd-SG03C/preview-approval.json (left untouched).
--set sg03c-c: SG03C → pilot/sd-SG03C-c/ after the second swap: D2-b was blocked too (no black turtleneck vs SG03-w1);
plate p012c-w1c (= design/D3-b.png). The user saw it beside SG03-w1 f12 on excerpt/flash/closeup2.html and approved
「可以，拍 (Recommended)」. Same prompt and vocal, 4k, 1 generation, 0 retries, ceiling 400 CRD; names the replaced
approval pilot/sd-SG03C-b/preview-approval.json (left untouched). It also seals `bound_ids` (iris-sg03c-c-source-001 /
iris-sg03c-c-reservation-001): lint.py requires the unit's operator-bound.json to use exactly these, and the writer refuses
when any existing pilot bound already uses them, so this take never shares an attempt id with a superseded folder.
--set sg03c-d1 / --set sg03c-d2: SG03C → pilot/sd-SG03C-d1/ and pilot/sd-SG03C-d2/, two takes under ONE approval. The
SG03C-c take failed its Gate (camera orbited, the foreground engineer was lost, the venue differed, early mouth, empty
mouthing); plate p012c-w1d (= design/D4/D4-a.png, an edit of the SG03-w1 4K frame) and a new prompt, both on
excerpt/flash/closeup3.html, approved 「D4-a，拍 (Recommended)」 for 2 takes from the same first frame (pick the best).
Each folder: 4k, multimodal, 4 s, 1 generation, 0 retries, ceiling 400 CRD; replaces pilot/sd-SG03C-c's approval;
bound ids iris-sg03c-d1-* / iris-sg03c-d2-*; a `takes` block names both folders as the same approval's two takes. Each
folder needs its own fresh canvas node (addnode.cjs per folder); lint.py refuses a node another pilot folder already uses.
--set sg04-r2-1 / sg04-r2-2 / mo07-r2-1 / mo07-r2-2: round 2 (W1), 「s013 用 b、s014 用 c，拍 (Recommended)」 on
excerpt/flash/round2.html, two takes per unit from the same first frame, the same way as sg03c-d1/-d2: SG04 → plate
p013-w1 (= design/R2/S13-b.png), multimodal 5 s with the sealed pilot/audio/SG04.wav; MO07 → plate p014-w1
(= design/R2/S14-c.png), first_frame 5 s. Each folder (pilot/sd-<UNIT>-r2-<n>/): 4k, 1 generation, 0 retries, ceiling
400 CRD; replaces the excerpt approval pilot/sd-<UNIT>/preview-approval.json (left untouched); bound ids
iris-<unit>-r2-<n>-*; a `takes` block. The excerpt set refuses SG04 / MO07 now (superseded).
--set mo06-s-1 / mo06-s-2 / mo07-s-1 / mo07-s-2: the strap fix (2026-11-19), 「两镜都用 b，拍 (Recommended)」 on
excerpt/flash/strapfix.html: the first frames of s011 / s014 re-edited so the strap runs right shoulder -> left hip
(MO06 → p011-w1c = design/STRAP/s011-b.png, MO07 → p014-w1b = design/STRAP/s014-b.png), the prompts unchanged (MO06:
the v4r1 text, MO07: the round-2 text). Two takes each, pilot/sd-<UNIT>-s-<n>/, 4k, first_frame 5 s, 1 generation,
0 retries, ceiling 400 CRD; replaces pilot/sd-MO06-w1b/ (MO06) and pilot/sd-MO07-r2-1/ (MO07); bound ids
iris-<unit>-s-<n>-*. The superseded sets (v4r1b, mo07-r2-*) refuse because the spec plates changed.

Run only after the user approved the excerpt page (pilot/excerpt/index.html) and its inputs
(pilot/excerpt/preview-inputs.json); the question, quote and time are the main session's record of that answer.
Each approval has exactly the shape unit.py draft reads: preview_page and preview_inputs with their sha256,
preview_artifacts = the clip's plate (role "<unit> first frame" or "<unit> reference image") plus, for a multimodal unit,
its sealed vocal window (role "<unit> vocal"), the approved prompt with its sha256, generation = the unit.py spec's
generation (Seedance 2.0 VIP 4k), budget = 1 generation, 0 retries, 800 CRD per unit and 800 cumulative per unit folder,
identity_waivers ["IRIS"]. Refuses before writing anything when any input differs from what the page and the spec say
(plate or vocal bytes, prompt sha, mode, seconds) or when any target approval already exists; it never overwrites.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

P = Path(__file__).resolve().parent
REPO = P.parents[4]
sys.path.insert(0, str(P))

import unit as U  # noqa: E402

PILOT = REPO / "outputs/ai-city-takeover/ep01/v4/pilot"
EXCERPT = PILOT / "excerpt"
BUDGET = {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": 800, "cumulative_CRD": 800}
SUPERSEDED = {"MO06": "superseded by v4 round 1 (W1 plate p011-w1b); use --set v4r1b",
              "SG04": "superseded by round 2 (W1 plate p013-w1); use --set sg04-r2-1 / sg04-r2-2",
              "MO07": "superseded by round 2 (W1 plate p014-w1); use --set mo07-r2-1 / mo07-r2-2",
              **{unit: f"superseded by the opening set (2026-11-20, W1 plate {plate}); the main session writes "
                       "pilot/sd-<UNIT>-o-<n>/preview-approval.json per pilot/opening/RUNBOOK.md"
                 for unit, plate in (("MO04", "p007-w1"), ("SG02", "p008-w1"), ("MO05", "p010-w1"))}}
FLASH = REPO / "outputs/ai-city-takeover/ep01/v4/excerpt/flash"
V4R1 = {   # the exact texts the user approved on excerpt/flash/v4r1.html; plate = the still the user picked ("选 1")
    "MO06": {"still": FLASH / "v4r1/V11a-1.png", "sha256": "778664284bccb297561bfa0c4d1ab11c0676827f74eaf496dea968d5506f2799",
             "ceiling": 600, "prompt": "镜头固定，低机位，从侧前方拍。地下停车场改成的秀场，她沿着湿的水泥走秀台大步向前走，"
             "抬起的那只靴子落地，重心越过支撑脚，长的那只袖子随后摆回；面无表情，带着一点好奇看着前方；两边前排的值班工程师一个接一个"
             "站起来。"},
    "SG03": {"still": FLASH / "v4r1/V12a-1.png", "sha256": "720e8f3cb1bbea1ca82c451a7c87a9f410ff0d38f97ffe2ce761d9894acec9f8",
             "ceiling": 700, "prompt": "{{image:0}}中的她对着值班工程师唱歌，口型与{{audio:1}}里的人声逐字精确同步。中近景，"
             "嘴前没有任何遮挡。镜头全程锁定，一镜到底。"},
}


class Refused(ValueError):
    pass


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _answer(question: str, quote: str, approved_at: str) -> None:
    if not question.strip() or not quote.strip():
        raise Refused("question and quote must be the recorded, non-empty text")
    if datetime.fromisoformat(approved_at).tzinfo is None:
        raise Refused("approved_at must be an ISO time with a timezone (UTC)")


def _vocal(unit: str, spec: dict, vocal: str | None, vocals: dict) -> dict:
    window = vocals.get(unit) or {}
    if vocal != spec["audio"]["path"] or window.get("path") != vocal or sha(REPO / vocal) != window.get("sha256"):
        raise Refused(f"{unit}: vocal {vocal} is not the window sealed in {U.VOCALS}")
    return {"path": vocal, "sha256": window["sha256"], "role": f"{unit} vocal"}


def approvals(question: str, quote: str, approved_at: str, units: list[str] | None = None,
              pilot: Path = PILOT) -> dict[Path, dict]:
    """The excerpt approvals to write, keyed by target path; raises Refused on any mismatch. Writes nothing."""
    _answer(question, quote, approved_at)
    page, inputs = EXCERPT / "index.html", EXCERPT / "preview-inputs.json"
    excerpt = json.loads(inputs.read_text(encoding="utf-8"))
    rows = {row["clip"]: row for row in excerpt["units"]}
    chosen = units or [unit for unit in rows if unit not in SUPERSEDED]
    vocals = json.loads((REPO / U.VOCALS).read_text(encoding="utf-8"))["windows"]
    out = {}
    for unit in chosen:
        if unit in SUPERSEDED:
            raise Refused(f"{unit}: {SUPERSEDED[unit]}")
        row, spec = rows.get(unit), U.SPECS.get(unit)
        if row is None or spec is None:
            raise Refused(f"{unit}: not both an excerpt unit and a unit.py spec")
        mode, label = spec["input_mode"], U.APPROVAL_ROLE[spec["input_mode"]]
        if (row["mode"], row["seconds"]) != (mode, spec["duration"]):
            raise Refused(f"{unit}: page says {row['mode']} {row['seconds']} s, spec says {mode} {spec['duration']} s")
        plate = REPO / row["plate"]["path"]
        if row["plate"]["path"] != spec["image"][1] or not sha(plate) == row["plate"]["sha256"] == spec["plate_sha256"]:
            raise Refused(f"{unit}: plate {row['plate']['path']} is not the approved, pinned bytes")
        if hashlib.sha256(row["prompt"].encode()).hexdigest() != row["prompt_sha256"]:
            raise Refused(f"{unit}: approved prompt text differs from its sha256")
        artifacts = [{"path": row["plate"]["path"], "sha256": row["plate"]["sha256"], "role": f"{unit} {label}"}]
        if mode == "multimodal":
            artifacts.append(_vocal(unit, spec, (row.get("audio") or {}).get("path"), vocals))
        target = pilot / f"sd-{unit}" / "preview-approval.json"
        if target.exists():
            raise Refused(f"{rel(target)} already exists; an approval is never overwritten")
        out[target] = {
            "schema": "iris-v4-preview-approval/1", "unit_group": f"v4-excerpt-{unit}", "question": question,
            "user_quote": quote, "approved_at": approved_at,
            "preview_page": {"path": rel(page), "sha256": sha(page)},
            "preview_inputs": {"path": rel(inputs), "sha256": sha(inputs)},
            "preview_artifacts": artifacts,
            "prompts": {unit: {"text": row["prompt"], "sha256": row["prompt_sha256"]}},
            "generation": dict(spec["generation"]), "budget": dict(BUDGET), "identity_waivers": ["IRIS"],
            "identity_waiver_basis": f"{label}（{Path(row['plate']['path']).name}）承担 IRIS（v4 锚点 F1a）的身份，"
                                     "使用者在节选预览页上看过并认可；不附身份图"}
    return out


V4R1B = {"MO06": {**V4R1["MO06"], "still": FLASH / "v4r1/V11a-2.png",
                  "sha256": "d262a4ecf248c186953a7a9bb78c4ad51f67eac1cd1c699721bca371039a3f6c"}}   # same prompt, still 2
SG03C = {"SG03C": {"still": FLASH / "design/D1-b.png",
                   "sha256": "fddf927a65eedf558b85ac501580f7f32f297dec8c9754f9672f635d14939fc7", "ceiling": 400,
                   "prompt": "{{image:0}}中的她闭着眼睛唱歌，口型与{{audio:1}}里的人声逐字精确同步。近景，前排笔记本屏幕的光"
                             "照着她的脸，嘴前没有任何遮挡。镜头全程锁定，一镜到底。"}}
SG03C_B = {"SG03C": {**SG03C["SG03C"], "still": FLASH / "design/D2-b.png",
                     "sha256": "dca4dab5e8ee17f1a11e2918436138338e03995105117dfd6c71cfdf48c4cb3d"}}   # same prompt, D2
SG03C_C = {"SG03C": {**SG03C["SG03C"], "still": FLASH / "design/D3-b.png",
                     "sha256": "779b1414e29914a33b96a0489295c6c89338df44badcad1a38192a6f27f40687",
                     "bound_ids": {"attempt_id": "iris-sg03c-c-source-001", "policy_id": "iris-sg03c-c-source-001",
                                   "reservation_id": "iris-sg03c-c-reservation-001"}}}
SG03C_D = {"still": FLASH / "design/D4/D4-a.png", "ceiling": 400,          # the PNG the page's D4-a-1080.jpg shows
           "sha256": "21c5f96a6cdbdf4f39d99b9137e4092776d4f3b4d77adba4178532c473682c48",
           "prompt": "{{image:0}}中的她闭着眼睛唱歌，口型与{{audio:1}}里的人声逐字精确同步。近景，机头直闪。左前景的工程师一直在"
                     "画面里。镜头固定不动，不推不拉不摇不环绕，一镜到底。嘴前没有任何遮挡。"}
SG03C_D_TAKES = {"approval": "one approval, two takes from the same first frame; the best one is picked after both Gates",
                 "folders": ["sd-SG03C-d1", "sd-SG03C-d2"], "generations_per_take": 1, "total_generations": 2,
                 "total_ceiling_CRD": 800}


def _take(n: int) -> dict:
    return {"SG03C": {**SG03C_D, "bound_ids": {"attempt_id": f"iris-sg03c-d{n}-source-001",
                                               "policy_id": f"iris-sg03c-d{n}-source-001",
                                               "reservation_id": f"iris-sg03c-d{n}-reservation-001"}}}


R2 = FLASH / "design/R2"
ROUND2 = {   # the exact prompts on excerpt/flash/round2.html; stills = the PNGs its S13-b / S14-c 1080 JPEGs show
    "SG04": {"still": R2 / "S13-b.png", "ceiling": 400,
             "sha256": "2f159721e0da2b9e2247a32fadd14ec79b3628152c911f07cee5c2c4dd1f3f21",
             "prompt": "{{image:0}}中的她低头看着镜头唱歌，口型与{{audio:1}}里的人声逐字精确同步。仰拍中近景，"
                       "机头直闪。手机一直拿在胸口下方，不举到脸边。镜头固定不动，不推不拉不摇不环绕，一镜到底。"
                       "嘴前没有任何遮挡。"},
    "MO07": {"still": R2 / "S14-c.png", "ceiling": 400,
             "sha256": "db997e4fe7d1704f96605bbfd4ad07dce38fac0e4fb345e8b9cb522775037950",
             "prompt": "长焦全身远景，镜头固定不动。她走到走秀台尽头，重心落在前脚，一个干脆的急转身，"
                       "长袖和外套下摆甩成一个圆再落下；转身后她头也不回，一只手按住腰间震动的黑色寻呼机，"
                       "朝画面右侧走开。两侧的值班工程师抬头看着她。"},
}


def _two_takes(unit: str, row: dict, round_: str, n: int, page: Path, replaces: Path) -> dict:
    tag = f"iris-{unit.lower()}-{round_}-{n}"
    return {"rows": {unit: {**row, "bound_ids": {"attempt_id": f"{tag}-source-001", "policy_id": f"{tag}-source-001",
                                                 "reservation_id": f"{tag}-reservation-001"}}},
            "suffix": f"{round_}-{n}", "page": page, "replaces": replaces,
            "takes": {"approval": "one approval, two takes per unit from the same first frame; the best one is picked "
                                  "after both Gates", "folders": [f"sd-{unit}-{round_}-1", f"sd-{unit}-{round_}-2"],
                      "generations_per_take": 1, "total_generations": 2, "total_ceiling_CRD": 800}}


def _round2(unit: str, n: int) -> dict:
    return _two_takes(unit, ROUND2[unit], "r2", n, FLASH / "round2.html", PILOT / f"sd-{unit}" / "preview-approval.json")


STRAP = FLASH / "design/STRAP"
STRAPFIX = {   # strapfix.html: the same approved prompts, first frames re-edited so the strap runs right shoulder -> left hip
    "MO06": ({**V4R1["MO06"], "still": STRAP / "s011-b.png", "ceiling": 400,
              "sha256": "22492025abac1e542346b54a26a0cfa19f78c00bb39a7448234618ff6e786b26"},
             PILOT / "sd-MO06-w1b" / "preview-approval.json"),
    "MO07": ({**ROUND2["MO07"], "still": STRAP / "s014-b.png", "ceiling": 400,
              "sha256": "c85aa47e12686ccdd6421bcae732eecd2862f43e736b62c33547b766c7f3ace8"},
             PILOT / "sd-MO07-r2-1" / "preview-approval.json"),
}


SETS = {"v4r1": {"rows": V4R1, "suffix": "w1", "page": FLASH / "v4r1.html", "replaces": None},
        "sg03c": {"rows": SG03C, "suffix": "", "page": FLASH / "closeup.html", "replaces": None},
        "sg03c-b": {"rows": SG03C_B, "suffix": "b", "page": FLASH / "closeup.html",
                    "replaces": PILOT / "sd-SG03C" / "preview-approval.json"},
        "sg03c-c": {"rows": SG03C_C, "suffix": "c", "page": FLASH / "closeup2.html",
                    "replaces": PILOT / "sd-SG03C-b" / "preview-approval.json"},
        "v4r1b": {"rows": V4R1B, "suffix": "w1b", "page": FLASH / "shoulder.html",
                  "replaces": PILOT / "sd-MO06-w1" / "preview-approval.json"},
        **{f"sg03c-d{n}": {"rows": _take(n), "suffix": f"d{n}", "page": FLASH / "closeup3.html",
                           "replaces": PILOT / "sd-SG03C-c" / "preview-approval.json", "takes": SG03C_D_TAKES}
           for n in (1, 2)},
        **{f"{unit.lower()}-r2-{n}": _round2(unit, n) for unit in ("SG04", "MO07") for n in (1, 2)},
        **{f"{unit.lower()}-s-{n}": _two_takes(unit, row, "s", n, FLASH / "strapfix.html", replaced)
           for unit, (row, replaced) in STRAPFIX.items() for n in (1, 2)}}


def v4r1_approvals(question: str, quote: str, approved_at: str, units: list[str] | None = None,
                   pilot: Path = PILOT, which: str = "v4r1") -> dict[Path, dict]:
    """The v4 round-1 approvals (pilot/sd-<UNIT>-w1/, or -w1b for v4r1b); raises Refused on any mismatch. Writes nothing."""
    _answer(question, quote, approved_at)
    rows, suffix, page, replaces = (SETS[which][k] for k in ("rows", "suffix", "page", "replaces"))
    if replaces is not None and not replaces.is_file():
        raise Refused(f"the approval this one replaces is missing: {rel(replaces)}")
    vocals = json.loads((REPO / U.VOCALS).read_text(encoding="utf-8"))["windows"]
    out = {}
    for unit in units or list(rows):
        row, spec = rows.get(unit), U.SPECS.get(unit)
        if row is None or spec is None:
            raise Refused(f"{unit}: not a {which} unit")
        plate = REPO / spec["image"][1]
        if spec["look"] != "W1" or not sha(row["still"]) == sha(plate) == row["sha256"] == spec["plate_sha256"]:
            raise Refused(f"{unit}: the spec's plate {spec['image'][1]} is not the approved still {rel(row['still'])}")
        label = U.APPROVAL_ROLE[spec["input_mode"]]
        artifacts = [{"path": spec["image"][1], "sha256": row["sha256"], "role": f"{unit} {label}"}]
        if spec["input_mode"] == "multimodal":
            artifacts.append(_vocal(unit, spec, spec["audio"]["path"], vocals))
        folder = f"sd-{unit}-{suffix}" if suffix else f"sd-{unit}"
        target = pilot / folder / "preview-approval.json"
        if target.exists():
            raise Refused(f"{rel(target)} already exists; an approval is never overwritten")
        out[target] = {
            "schema": "iris-v4-preview-approval/1",
            "unit_group": f"v4-{which}-{unit}", "question": question,
            "user_quote": quote, "approved_at": approved_at,
            "preview_page": {"path": rel(page), "sha256": sha(page)},
            "preview_artifacts": artifacts,
            "prompts": {unit: {"text": row["prompt"], "sha256": hashlib.sha256(row["prompt"].encode()).hexdigest()}},
            "generation": dict(spec["generation"]),
            "budget": {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": row["ceiling"],
                       "cumulative_CRD": row["ceiling"]},
            "identity_waivers": ["IRIS"],
            "identity_waiver_basis": f"{label}（{Path(spec['image'][1]).name}，与 {rel(row['still'])} 逐字节相同）"
                                     "承担 IRIS（v4 锚点 F1a，造型 W1）的身份；不附身份图"}
        if replaces is not None:                  # the round-1 approval this one replaces (kept as it is)
            out[target]["replaces_approval"] = {"path": rel(replaces), "sha256": sha(replaces)}
        if row.get("bound_ids"):                  # ids no existing pilot bound uses; lint.py holds the bound to them
            used = {json.loads(b.read_text(encoding="utf-8")).get(k) for b in pilot.glob("sd-*/*/operator-bound.json")
                    for k in ("attempt_id", "policy_id", "reservation_id")}
            taken = sorted(set(row["bound_ids"].values()) & used)
            if taken:
                raise Refused(f"{unit}: bound ids already used by an existing pilot bound: {taken}")
            out[target]["bound_ids"] = dict(row["bound_ids"])
        if SETS[which].get("takes"):              # one approval, several independent takes (each its own folder/node)
            out[target]["takes"] = {**SETS[which]["takes"], "this_take": folder}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", choices=["excerpt", *SETS], default="excerpt")
    ap.add_argument("--question", required=True)
    ap.add_argument("--quote", required=True)
    ap.add_argument("--approved-at", required=True)
    ap.add_argument("--units", nargs="*")
    args = ap.parse_args()
    try:
        if args.set == "excerpt":
            planned = approvals(args.question, args.quote, args.approved_at, args.units)
        else:
            planned = v4r1_approvals(args.question, args.quote, args.approved_at, args.units, which=args.set)
    except Refused as error:
        print(json.dumps({"refused": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    for target, value in planned.items():                       # every check passed before the first write
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(value, ensure_ascii=False, indent=1) + "\n")
        print(json.dumps({"unit": next(iter(value["prompts"])), "approval": rel(target), "sha256": sha(target)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
