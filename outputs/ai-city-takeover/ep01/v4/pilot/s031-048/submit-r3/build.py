#!/usr/bin/env python3
"""Build the s031-s048 r3 pre-submit pack for SG12, SG15, SG16, SG17, SG18 and SG20 (no Provider, no browser, no canonical
writes).

  uv run python outputs/ai-city-takeover/ep01/v4/pilot/s031-048/submit-r3/build.py [--check]

r3 supersedes r2 (pilot/s031-048/r2, never applied): SG12 a-3 came back speaking Chinese after its prompt quoted a Chinese
rendering of the lyric; the user ruled 「删掉译文、精简动作后重拍 (Recommended)」 (logs/decisions.md 2026-11-25). Spoken /
sung prompts quote no lyric text or translation and bind actions by ordinal only; SG12 keeps only the belt cinch on the
first word and is re-shot in new take folders sd-SG12-b-1|2; SG15 / SG17 / SG20 carry the r2 changes.

Run it only where gen/unit.py and board/shots.json carry pilot/s031-048/r3/PATCH.md (the scratch copy before the patch is
applied, or the repository after it): it asserts every first frame equals its spec's plate sha. --check rebuilds in memory
and compares with the files on disk (exit 1 on any difference); without it, writes:
- pilot/s031-048/submit-r3/preview-inputs.json   the six units (first frame, exact r3 draft prompt, previous prompt, the
  sentences of each vocal window, mode, seconds, plan rows, risks, cost) and the r2 s047 still
- pilot/s031-048/submit-r3/index.html            the pack page the approvals bind
- pilot/s031-048/r3/index.html                   the user's re-approval page (prompt diffs, sentence lists, cost)
- pilot/s031-048/r3/<UNIT>-approval.template.json  take <tag>-1 (<tag>-2 differs as its _template_notes say)

Reuses pilot/s031-048/submit/build.py (plan rows, lessons, notes, cost rule) and submit-r2/build.py (s047 still, r2
notes) read-only; neither pack nor its templates change. Writes no approval.
"""
from __future__ import annotations

import difflib
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent            # pilot/s031-048/submit-r3
GROUP = HERE.parent                               # pilot/s031-048
R3 = GROUP / "r3"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)               # read-only reuse; importing writes nothing
    return module


B = _load("s3148_submit_build", GROUP / "submit/build.py")
B2 = _load("s3148_submit_r2_build", GROUP / "submit-r2/build.py")
U, REPO, sha, rel = B.U, B.REPO, B.sha, B.rel

PROMPTS = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/s031-048-seedance-r3.md"
BASE_PROMPTS = B.PROMPTS                          # s031-048-seedance.md (SG12 / SG16 / SG18 start here)
R2_PROMPTS = B2.PROMPTS                           # s031-048-seedance-r2.md (SG15 / SG17 / SG20 start here)
WORDS = "outputs/ai-city-takeover/ep01/v4/song/timing/words.json"
PAGE = rel(HERE / "index.html")
INPUTS = rel(HERE / "preview-inputs.json")
REVIEW = rel(R3 / "index.html")
PATCH = rel(R3 / "PATCH.md")
UNITS = ["SG12", "SG15", "SG16", "SG17", "SG18", "SG20"]
FROM_R2 = ("SG15", "SG17", "SG20")
TAGS = {"SG12": "b"}                              # SG12 a-1 / a-2 / a-3 are used; the others reuse their empty a folders
FRAMES = {"SG12": "P031/a", "SG15": "P036/x", "SG16": "CONT1124/p037-mw-b-comp", "SG17": "P039/b", "SG18": "P041/c",
          "SG20": "CONT1124/p048-arm-b-comp"}
# the action each prompt binds, by ordinal of the sentences in its own vocal window: (ordinal, its first word, prompt text)
ORDINALS = {"SG15": (3, "Out", "说到第三句时"), "SG16": (4, "Killed", "说到第四句时"), "SG17": (2, "They", "说到第二句时"),
            "SG18": (3, "October", "唱到第三句刚开口时")}
QUOTES = "「」『』“”‘’\"'"
R3_RISK = "a-3 说成中文：prompt 引了歌词译文。r3 起不引任何歌词原文或译文、不加引号，动作只按句序写；Gate 先听她说的是不是英语"
LESSONS = {
    "SG12": [R3_RISK, *(r for r in B.LESSONS["SG12"] if not r.startswith("收腰带")),
             "收腰带的手离嘴近；r3 去掉塞纸币和瞟眼，纸币一直捏在腰前，看向售货机交给剪辑",
             "a-1 首词疑唱错、s031a 段嘴晚约 4 帧；a-1 / a-3 第四句后转头不回——r3 写明一直看着镜头，不转头"],
    "SG15": [R3_RISK, *B2.LESSONS["SG15"][:-1], "“最后一句”有歧义（窗口尾巴带下一句 Ten）；r3 绑“说到第三句时”（Out of my way，片内约 2.79 s）"],
    "SG16": [R3_RISK, *B.LESSONS["SG16"][:-1],
             "首帧加了 S037A 那台微波炉：灯要在第四句（Killed at twelve thirty-four，片内约 3.49 s）熄灭，接 INS37 拔插头；显示屏会长数字"],
    "SG17": [R3_RISK, *B2.LESSONS["SG17"][:-1], "r3 绑“说到第二句时”（They found a gap instead，片内约 2.04 s；开头的 more. 尾巴不算一句）"],
    "SG18": [R3_RISK, *B.LESSONS["SG18"], "抓布边绑“唱到第三句刚开口时”：第三句在本窗口只露出第一个词（October，片内约 7.50 s）"],
    "SG20": [R3_RISK, *B2.LESSONS["SG20"]],
}
NOTES = {
    "SG12": [*B.NOTES["SG12"],
             "2026-11-25 a-1（2a8b972e…）Gate FAIL；a-2 known_no_effect；a-3（9e5230d5…）Gate FAIL：原生音轨与口型是中文",
             "2026-11-25 r3：使用者「删掉译文、精简动作后重拍 (Recommended)」：删掉塞纸币与瞟眼（看向售货机交给剪辑），只留说第一个词时收腰带，纸币一直捏在腰前；"
             "不引歌词译文；重拍 2 条，take 文件夹 sd-SG12-b-1|2；首帧、秒数、人声不变"],
    "SG15": [*B2.NOTES["SG15"], "2026-11-25 r3：去掉引号里的歌词译文，改写“说到第三句时”；首帧、秒数、人声不变"],
    "SG16": [*B.NOTES["SG16"], "2026-11-25 r3：去掉引号里的歌词译文，灯灭放碗改写“说到第四句时”（窗口内第四句 Killed at twelve thirty-four.）；"
             "首帧、秒数、人声不变；本 a-1 / a-2 文件夹里上一批的 approval 由本模板取代"],
    "SG17": [*B2.NOTES["SG17"], "2026-11-25 r3：去掉引号里的歌词译文，改写“说到第二句时”；首帧、秒数、人声不变"],
    "SG18": [*B.NOTES["SG18"], "2026-11-25 r3：去掉引号里的歌词译文，抓布边改写“唱到第三句刚开口时”（窗口内第三句只到 October）；"
             "首帧、秒数、人声不变；本 a-1 / a-2 文件夹里上一批的 approval 由本模板取代"],
    "SG20": [*B2.NOTES["SG20"], "2026-11-25 r3：prompt 与 r2 相同（本来就没有引号或译文）"],
}
KNOWN_ISSUES = [
    ("范围", "本包只有 SG12、SG15、SG16、SG17、SG18、SG20；INS33、INS37、INS41、SG19、MO15 仍按 submit/ 包与 s031-048-seedance.md 提交，本包不改它们。"
     "submit-r2/ 包与 r2.patch 作废（r2 的改动都在 r3.patch 里）。", "—"),
    ("应用顺序", "本包的 board sha 是 r3/PATCH.md 应用之后的值；当前一批提交完、PATCH 应用前不要写这六条的 approval。",
     "当前一批提交完 → 应用 PATCH.md → 跑本脚本 --check 与测试 → 写 approval。"),
    ("SG16 / SG18 旧 approval", "sd-SG16-a-1|2、sd-SG18-a-1|2 里还躺着上一批（引译文的 prompt）写好的 preview-approval.json，未提交。",
     "应用 PATCH 时改名为 preview-approval.held-r3.json（保留不删），再按 r3 模板重写；continuity-report.json 也要按 r3 prompt 重出。"),
    ("s047 静图", "沿用 r2：s047 改用 CONT1124/p047-rb-c-2944（左臂裸露）；它是静图，不生成，只影响剪辑取图。", "剪辑时用新图。"),
]


def prompts(path: str) -> dict:
    text = (REPO / path).read_text(encoding="utf-8")
    found = re.findall(r"^## (s\d{3}) · (\w+) · .*?\n\n```prompt\n(.*?)\n```", text, re.S | re.M)
    return {unit: (shot, prompt) for shot, unit, prompt in found}


def sentences(unit: str, t0: float, t1: float) -> list[dict]:
    """The sentences heard in a vocal window: spoken lines split at . ? !, sung lines are one sentence each; a tail of the
    previous sentence (words starting before t0) is not counted; times are in-take seconds; complete = it ends inside."""
    out = []
    for line in json.loads((REPO / WORDS).read_text(encoding="utf-8"))["lines"]:
        current: list = []
        for i, w in enumerate(line["words"]):
            ends = i == len(line["words"]) - 1 or (line["mode"] == "spoken" and w["text"][-1] in ".?!")
            if t0 <= w["start"] < t1:
                current.append(w)
            if ends and current:
                out.append((current, ends and w is current[-1] and w["end"] <= t1 + 0.05))   # a word ending within 50 ms past the cut is said
                current = []
        if current:
            out.append((current, False))
    return [{"text": " ".join(w["text"] for w in s), "start": round(s[0]["start"] - t0, 2), "end": round(s[-1]["end"] - t0, 2),
             "complete": complete} for s, complete in out]


def build() -> dict:
    board = json.loads((REPO / U.BOARD).read_bytes())
    assert hashlib.sha256((REPO / U.BOARD).read_bytes()).hexdigest() == U.BOARD_SHA256, "apply r3/PATCH.md first"
    shots = {s["id"]: s for s in board["shots"]}
    clips = {c["clip"]: c for c in board["clips"]}
    windows = json.loads((REPO / U.VOCALS).read_text(encoding="utf-8"))["windows"]
    segs, unit_rows = B.plan_rows()
    new, base, r2 = prompts(PROMPTS), prompts(BASE_PROMPTS), prompts(R2_PROMPTS)
    assert list(new) == UNITS, list(new)
    units = []
    for unit in UNITS:
        shot, prompt = new[unit]
        prev_path, prev = (R2_PROMPTS, r2[unit][1]) if unit in FROM_R2 else (BASE_PROMPTS, base[unit][1])
        assert base[unit][0] == shot
        spec, clip = U.SPECS[unit], clips[unit]
        assert clip["used_by"] == [shot] and shots[shot]["plate"] == clip["start_frame"] == spec["plate"]
        frame = B.DESIGN + FRAMES[unit] + ".png"
        plate = U.PLATES + spec["plate"] + ".png"
        assert sha(frame) == sha(plate) == spec["plate_sha256"]
        literals = [spec["image"][4], *spec["intent"]["open_event"], *spec["intent"]["close_event"], *spec["intent"]["natural"]]
        assert [x for x in literals if x not in prompt] == [] and U.prompt_language_ok(spec, prompt)
        assert "最后" not in prompt and not [q for q in QUOTES if q in prompt], unit
        window = windows[spec["audio"]["window"]]
        assert window["path"] == spec["audio"]["path"] and sha(window["path"]) == window["sha256"]
        heard = sentences(unit, *window["song_window"])
        if unit in ORDINALS:                       # the bound ordinal is a sentence of this window, starting where said
            n, first, words = ORDINALS[unit]
            assert words in prompt and heard[n - 1]["text"].split()[0] == first, (unit, heard)
        secs = spec["duration"]
        uses = [seg for seg in segs if seg[:4] == shot and unit in segs[seg]["kind"]]
        d = spec["dialogue"]
        units.append({
            "shot": shot, "unit": unit, "clip": unit, "mode": spec["input_mode"], "look": spec["look"], "take_tag": TAGS.get(unit, "a"),
            "song_span_s": [clip["plays"]["t0"], clip["plays"]["t1"]],
            "generation_window_s": [clip["window"]["t0"], clip["window"]["t1"]],
            "first_frame": {"path": plate, "sha256": spec["plate_sha256"], "design_frame": frame},
            "prompt": prompt, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "previous_prompt": {"path": prev_path, "sha256": hashlib.sha256(prev.encode()).hexdigest()},
            "base_prompt": {"path": BASE_PROMPTS, "sha256": hashlib.sha256(base[unit][1].encode()).hexdigest()},
            "ordinal_binding": ({"ordinal": ORDINALS[unit][0], "text": ORDINALS[unit][2], "sentence_starts_with": ORDINALS[unit][1]}
                                if unit in ORDINALS else None),
            "required_phrases": literals,
            "seconds": secs, "take_margin_seconds": spec.get("take_margin_seconds", 0), "resolution": "4k", "aspect": "16:9",
            "takes": B.TAKES, "est_cost_per_take_CRD": secs * B.RATE, "ceiling_per_take_CRD": B.ceiling(secs),
            "plan": {seg: segs[seg] for seg in uses}, "plan_unit": unit_rows[unit], "lesson_risks": LESSONS[unit],
            "vocal": {"path": window["path"], "sha256": window["sha256"], "seconds": window["seconds"],
                      "song_window_s": window["song_window"], "clip_words": clip["words"], "sentences": heard,
                      "lyric_text": d["verbatim_text"], "dialogue_s": [d["start_seconds"], d["end_seconds"]]}})
    stills = [{"segment": seg, "frames": [{"path": B.DESIGN + f + ".png", "sha256": sha(B.DESIGN + f + ".png")} for f in frames],
               "replaces": {"path": B.DESIGN + B2.OLD_STILL + ".png", "sha256": sha(B.DESIGN + B2.OLD_STILL + ".png")},
               "plan": segs[seg]} for seg, frames in B2.STILLS.items()]
    est = sum(u["est_cost_per_take_CRD"] for u in units) * B.TAKES
    ceil_sum = sum(u["ceiling_per_take_CRD"] for u in units)
    sg12 = next(u for u in units if u["unit"] == "SG12")
    return {"schema": "iris-v4-preview-inputs/s031-048-r3-1", "range_s": [shots["s031"]["t0"], shots["s048"]["t1"]],
            "method": "Seedance 2.0 VIP 4k（使用者 2026-11-17：画质最高/积分随便用）",
            "director_plan": {"path": B.PLAN, "sha256": sha(B.PLAN)},
            "first_frame_preview": {"path": B.PREVIEW, "sha256": sha(B.PREVIEW)},
            "base_pack": {"path": B.INPUTS, "sha256": sha(B.INPUTS)},
            "supersedes": {"path": B2.INPUTS, "sha256": sha(B2.INPUTS)},
            "source_prompt_file": PROMPTS, "source_prompt_file_sha256": sha(PROMPTS),
            "board": {"path": U.BOARD, "sha256": U.BOARD_SHA256}, "patch": PATCH,
            "plan": "每 unit 同一首帧拍 2 条，过逐镜 Gate 后挑一条；每条一次不重试",
            "cost_basis": f"4k 每秒 {B.RATE} 积分；单条上限 = 该价向上取整到百（与 submit/ 包同一口径，秒数不变）",
            "total_seconds_per_take_set": sum(u["seconds"] for u in units),
            "estimated_total_CRD": est, "ceiling_per_take_sum_CRD": ceil_sum, "ceiling_total_CRD": ceil_sum * B.TAKES,
            "new_over_plan": {"unit": "SG12", "estimated_CRD": sg12["est_cost_per_take_CRD"] * B.TAKES,
                              "ceiling_CRD": sg12["ceiling_per_take_CRD"] * B.TAKES,
                              "why": "SG12 原计划的 2 条已用掉（a-1 720、a-3 720；a-2 known_no_effect 未扣费），b-1 / b-2 是新增"},
            "units": units, "stills": stills,
            "known_issues": [{"where": w, "issue": i, "proposal": p} for w, i, p in KNOWN_ISSUES]}


STYLE = B2.STYLE.replace("</style>", ".sl{font-size:14px;color:#c9d4df}.sl b{color:#a8f0bf}.sl .t{color:#7f8b97}"
                         ".ask h2{margin:4px 0}.opt{font-size:15px}</style>")
up = B2.up
diff_html = B2.diff_html


def sentence_list(u: dict) -> str:
    esc = html.escape
    bound = (u["ordinal_binding"] or {}).get("ordinal")
    items = []
    for i, s in enumerate(u["vocal"]["sentences"], 1):
        text = f'{"①②③④⑤⑥"[i - 1]} {esc(s["text"])} <span class="t">（{s["start"]:.2f}–{s["end"]:.2f} s{"" if s["complete"] else "，切点截断、没说完"}）</span>'
        items.append(f"<li><b>{text}　← 动作绑这一句</b></li>" if i == bound else f"<li>{text}</li>")
    return '<ol class="sl" style="list-style:none;padding-left:0">' + "".join(items) + "</ol>"


WINDOW_NOTE = {
    "SG12": "动作只绑“说出第一个词”（September，0.30 s）；第⑤句是下一句开头 It asked，被切点截断，约 0.21 s。",
    "SG15": "第④句只露出 Ten 一个词（约 0.06 s，切点截断），所以 r2 之前写的“最后一句”有歧义。",
    "SG16": "",
    "SG17": "窗口开头还带上一句 more. 的尾巴（到 0.03 s），不算一句。",
    "SG18": "唱段按歌词行分句；第③句在本窗口只唱到第一个词，后半句在 SG19。",
    "SG20": "只有一句，说完静止；不绑句序。",
}


def pack_page(data: dict) -> str:
    esc = html.escape
    out = ['<!doctype html><meta charset="utf-8"><title>IRIS EP01 s031–s048 r3 提交包（SG12 · SG15 · SG16 · SG17 · SG18 · SG20）</title>', STYLE,
           "<h1>IRIS EP01 s031–s048 r3 · SG12 · SG15 · SG16 · SG17 · SG18 · SG20 · Seedance 2.0 VIP 4k 提交包</h1>",
           f"<p>6 条念白 / 唱段（multimodal：首帧 + 人声），每条同一首帧拍 {B.TAKES} 次、每次不重试。每套 {data['total_seconds_per_take_set']} 秒，"
           f"<b>预计 {data['estimated_total_CRD']:,} 积分</b>，<b>上限 {data['ceiling_total_CRD']:,}</b>；其中 SG12 b-1 / b-2 的 "
           f"{data['new_over_plan']['estimated_CRD']:,}（上限 {data['new_over_plan']['ceiling_CRD']:,}）是原 10,400 之外新增，其余 5 条秒数不变、已算在原计划里。"
           f"认可页：<a href=\"../r3/index.html\">r3/index.html</a>。本页没有提交任何东西。</p>",
           f"<p class=\"d\">board sha {data['board']['sha256'][:12]}…（{esc(data['patch'])} 应用之后）· prompt 来源 "
           f"{esc(data['source_prompt_file'].split('ep01/v4/')[1])} sha {data['source_prompt_file_sha256'][:12]}…</p>"]
    for u in data["units"]:
        plan = " ／ ".join(f"{seg} {r['time']}｜{r['lyric']}｜{r['picture']}" for seg, r in u["plan"].items())
        v = u["vocal"]
        cost = (f"{u['seconds']} s · 4k · 16:9 · {u['mode']} · {u['takes']} 条 × {u['seconds']} s × {B.RATE} = "
                f"{u['est_cost_per_take_CRD'] * u['takes']} 积分（单条上限 {u['ceiling_per_take_CRD']}） · take 文件夹 "
                f"sd-{u['unit']}-{u['take_tag']}-1|2 · prompt sha {u['prompt_sha256'][:12]}…")
        risks = "".join(f"<li>{esc(r)}</li>" for r in u["lesson_risks"])
        out.append(f'<div class="card"><div class="im"><img src="{up(u["first_frame"]["path"])}"><div class="d">'
                   f'{Path(u["first_frame"]["path"]).name} = {esc(u["first_frame"]["design_frame"].split("S31-48/")[1])}'
                   f' · sha {u["first_frame"]["sha256"][:12]}…</div></div><div class="tx">'
                   f'<h3>{u["shot"]} · {u["unit"]} · {u["mode"]} · 造型 {u["look"]} · 剪辑 {u["song_span_s"][0]:.3f}–{u["song_span_s"][1]:.3f} s</h3>'
                   f'<p class="pl">方案：{esc(plan)}</p><p class="d">Gate 只验收：{esc(u["plan_unit"]["gate"])}</p>'
                   f'<p class="n">人声窗口 {v["song_window_s"][0]}–{v["song_window_s"][1]} s（{v["seconds"]} s，口型 {v["dialogue_s"][0]}–'
                   f'{v["dialogue_s"][1]} s）</p>{sentence_list(u)}<audio controls preload="none" src="{up(v["path"])}"></audio>'
                   f'<p class="pr">{esc(u["prompt"])}</p><p class="d">{esc(cost)}</p>'
                   f'<div class="rk">风险（教训）：<ul>{risks}</ul></div></div></div>')
    out.append("<h2>静图（不生成，沿用 r2）</h2><table><tr><th>段</th><th>时间 s</th><th>新</th><th>原</th></tr>")
    for s in data["stills"]:
        f = s["frames"][0]
        out.append(f'<tr><td>{s["segment"]}</td><td>{esc(s["plan"]["time"])}</td><td><img src="{up(f["path"])}" width="360"><br>'
                   f'{esc(f["path"].split("S31-48/")[1])}</td><td><img src="{up(s["replaces"]["path"])}" width="360"><br>'
                   f'{esc(s["replaces"]["path"].split("S31-48/")[1])}</td></tr>')
    out.append("</table><h2>费用</h2>" + cost_table(data) + "<h2>已知问题</h2><ul>")
    out += [f'<li><b>{esc(k["where"])}</b>：{esc(k["issue"])}<br><span class="d">{esc(k["proposal"])}</span></li>' for k in data["known_issues"]]
    return "\n".join(out) + "</ul>\n"


def cost_table(data: dict) -> str:
    rows = ["<table><tr><th>unit</th><th>秒</th><th>take</th><th>单条约</th><th>2 条约</th><th>单条上限</th><th>算在哪</th></tr>"]
    for u in data["units"]:
        where = "<b>新增</b>（原计划的 2 条已用掉）" if u["unit"] == "SG12" else "原 10,400 计划内（还没拍）"
        rows.append(f'<tr><td>{u["shot"]} {u["unit"]}</td><td>{u["seconds"]}</td><td>{u["take_tag"]}-1 / {u["take_tag"]}-2</td>'
                    f'<td>{u["est_cost_per_take_CRD"]}</td><td>{u["est_cost_per_take_CRD"] * u["takes"]:,}</td>'
                    f'<td>{u["ceiling_per_take_CRD"]}</td><td>{where}</td></tr>')
    n = data["new_over_plan"]
    rows.append(f'<tr><td><b>合计</b></td><td>{data["total_seconds_per_take_set"]}</td><td></td><td></td>'
                f'<td><b>{data["estimated_total_CRD"]:,}</b></td><td>{data["ceiling_per_take_sum_CRD"]:,}×2 = {data["ceiling_total_CRD"]:,}</td>'
                f'<td>新增 {n["estimated_CRD"]:,}（上限 {n["ceiling_CRD"]:,}）+ 计划内 {data["estimated_total_CRD"] - n["estimated_CRD"]:,}</td></tr></table>')
    rows.append(f'<p class="d">s031–s048 全段：原计划 10,400（上限 11,200）＋ SG12 新增 {n["estimated_CRD"]:,}（上限 {n["ceiling_CRD"]:,}）'
                f'＝ 约 {10400 + n["estimated_CRD"]:,}（上限 {11200 + n["ceiling_CRD"]:,}）。SG12 已花 1,440（a-1 720、a-3 720；a-2 未扣费）。</p>')
    return "".join(rows)


def review_page(data: dict, pack_sha: str, inputs_sha: str) -> str:
    esc = html.escape
    base, r2 = prompts(BASE_PROMPTS), prompts(R2_PROMPTS)
    n = data["new_over_plan"]
    out = ['<!doctype html><meta charset="utf-8"><title>IRIS EP01 s031–s048 r3 重新认可（去掉歌词译文）</title>', STYLE,
           '<div class="ask"><h2>要你定的（一件）</h2>'
           "<p class=\"opt\"><b>这六条按本页的新 prompt 开拍吗？</b>所有念白 / 唱段 prompt 去掉了歌词译文和引号，动作只写“说到第几句时”；"
           "SG12 只留开口时收腰带（纸币一直捏在腰前，不塞、不瞟眼，看售货机交给剪辑），用新文件夹 b-1 / b-2 重拍 2 条，"
           f"<b>新增约 {n['estimated_CRD']:,} 积分</b>（上限 {n['ceiling_CRD']:,}）；SG15、SG16、SG17、SG18、SG20 秒数和花费不变，仍按原计划各拍 2 条。"
           "<br>选项：<b>按 r3 开拍 (Recommended)</b> ／ SG12 还要改 ／ 先不拍。</p>"
           "<p class=\"d\">什么都没提交、没付费、没写 approval、没 commit；unit.py / shots.json 等当前一批（INS33、INS37、INS41、SG19、MO15）提交完再按 PATCH.md 改。</p></div>",
           "<h1>s031–s048 r3：去掉歌词译文，动作只按句序</h1>",
           "<p>原因：SG12 a-3 原生音轨和口型都是中文（Whisper 听出来的是中文）。prompt 里写了“说第四句”加上那句歌词的中文译文，"
           "模型照着译文改说中文。使用者定了「删掉译文、精简动作后重拍 (Recommended)」。r3 起念白 / 唱段 prompt 不写任何歌词原文或译文，也不加引号；"
           "句序按每条人声窗口里实际听到的句子数（下面逐条列出，words.json 时间并用本地 Whisper 复听核对）。</p>",
           "<h2>1 · 六条 prompt 改动（红删绿增）</h2>"]
    for u in data["units"]:
        unit = u["unit"]
        prev_label = "r2 版（已认可、未应用）" if unit in FROM_R2 else "原版 s031-048-seedance.md"
        prev = r2[unit][1] if unit in FROM_R2 else base[unit][1]
        change = "与 r2 相同，没有改动（本来就没有引号或译文）" if prev == u["prompt"] else ""
        out.append(f'<h3>{u["shot"]} · {unit} · {u["seconds"]} s · take {u["take_tag"]}-1 / {u["take_tag"]}-2</h3>'
                   f'<p class="d">人声窗口 {u["vocal"]["song_window_s"][0]}–{u["vocal"]["song_window_s"][1]} s 里的句子：</p>'
                   f'{sentence_list(u)}<p class="d">{esc(WINDOW_NOTE[unit])}</p>'
                   f'<p class="d">旧 = {prev_label} → 新 = r3{("：" + change) if change else ""}</p>'
                   f'<p class="pr">{diff_html(prev, u["prompt"])}</p>')
        if unit in FROM_R2:
            out.append(f'<details><summary class="d">相对原版 s031-048-seedance.md（含 r2 的改动）</summary>'
                       f'<p class="pr">{diff_html(base[unit][1], u["prompt"])}</p></details>')
        out.append(f'<p class="d">旧 sha {u["previous_prompt"]["sha256"][:12]}… → 新 {u["prompt_sha256"][:12]}… · '
                   f'人声 <audio controls preload="none" src="{up(u["vocal"]["path"])}" style="width:320px;vertical-align:middle"></audio></p>')
    out.append("<h2>2 · 花费</h2>" + cost_table(data))
    out.append("<h2>3 · 其他</h2><ul>"
               "<li>SG20 首帧仍用 r2 认可的 p048-w2（左臂裸露），s047 静图仍用 r2 认可的 p047-rb-c；r2 的这些改动都并进 r3.patch，r2.patch 作废。</li>"
               "<li>INS33、INS37、INS41、SG19、MO15 的 prompt 里没有引号、歌词原文或译文，照原认可在当前一批提交，不改。</li>"
               "<li>sd-SG16-a-1|2、sd-SG18-a-1|2 里上一批写好的 approval（引译文的 prompt）还没提交；应用 PATCH 时改名为 held-r3 保留，按 r3 模板重写。</li></ul>")
    out.append(f'<p class="d">提交包：<a href="../submit-r3/index.html">submit-r3/index.html</a>（sha {pack_sha[:12]}…；'
               f'preview-inputs sha {inputs_sha[:12]}…）· 应用步骤：{esc(PATCH.split("ep01/v4/")[1])} · '
               f'approval 模板：pilot/s031-048/r3/&lt;UNIT&gt;-approval.template.json</p>')
    return "\n".join(out) + "\n"


def template(row: dict, page_sha: str, inputs_sha: str, review_sha: str) -> dict:
    unit, tag = row["unit"], row["take_tag"]
    value = B.template(unit, row, page_sha, inputs_sha)
    retag = (lambda text: text.replace(f"-{B.TAG}-", f"-{tag}-")) if tag != B.TAG else (lambda text: text)
    value["unit_group"] = f"v4-s031-048-r3-{unit}-{tag}-1"
    value["question"] = f"<主会话问使用者的原问题，逐字（认可页 {REVIEW}）>"
    value["preview_page"] = {"path": PAGE, "sha256": page_sha}
    value["preview_inputs"] = {"path": INPUTS, "sha256": inputs_sha}
    value["prompt_source"] = {"path": PROMPTS, "sha256": sha(PROMPTS)}
    value["review_page"] = {"path": REVIEW, "sha256": review_sha}
    value["bound_ids"] = {k: retag(v) for k, v in value["bound_ids"].items()}
    value["takes"]["folders"] = [retag(f) for f in value["takes"]["folders"]]
    value["takes"]["this_take"] = retag(value["takes"]["this_take"])
    value["decision_notes"] = NOTES[unit]
    held = {"SG16": "；文件夹里上一批写好的 preview-approval.json 先改名为 preview-approval.held-r3.json（保留不动）",
            "SG18": "；文件夹里上一批写好的 preview-approval.json 先改名为 preview-approval.held-r3.json（保留不动）",
            "SG15": "（同一文件夹里的 preview-approval.held-r2.json 是更早被取代的旧件，保留不动）",
            "SG17": "（同一文件夹里的 preview-approval.held-r2.json 是更早被取代的旧件，保留不动）",
            "SG20": "（同一文件夹里的 preview-approval.held-r2.json 是更早被取代的旧件，保留不动）",
            "SG12": "（新文件夹；sd-SG12-a-1|2|3 是已用掉的旧 take，不动）"}[unit]
    value["_template_notes"] = [
        f"本文件是 r3 的 {tag}-1 模板；先按 {PATCH} 改好 unit.py / shots.json / 测试并跑通，再写成 pilot/sd-{unit}-{tag}-1/preview-approval.json："
        f"删除本 _template_notes 字段并填好 question / user_quote / approved_at 三个占位{held}。",
        f"{tag}-2：unit_group 末尾 {tag}-1→{tag}-2；bound_ids 三个 id 中 -{tag}-1- → -{tag}-2-；takes.this_take → sd-{unit}-{tag}-2"
        f"（takes.folders 保持 [{tag}-1, {tag}-2]）；其余逐字相同。",
        retag(value["_template_notes"][2])]
    return value


def render() -> dict[Path, str]:
    data = build()
    files: dict[Path, str] = {}
    inputs = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    pack = pack_page(data)
    files[HERE / "preview-inputs.json"], files[HERE / "index.html"] = inputs, pack
    h = lambda s: hashlib.sha256(s.encode()).hexdigest()
    review = review_page(data, h(pack), h(inputs))
    files[R3 / "index.html"] = review
    for row in data["units"]:
        value = template(row, h(pack), h(inputs), h(review))
        files[R3 / f"{row['unit']}-approval.template.json"] = json.dumps(value, ensure_ascii=False, indent=1) + "\n"
    return files


def main() -> int:
    files = render()
    if "--check" in sys.argv:
        bad = [rel(p) for p, text in files.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
        print(json.dumps({"matches": not bad, "differs": bad}, ensure_ascii=False))
        return 1 if bad else 0
    R3.mkdir(exist_ok=True)
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    print(json.dumps({rel(p): sha(rel(p)) for p in files}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
