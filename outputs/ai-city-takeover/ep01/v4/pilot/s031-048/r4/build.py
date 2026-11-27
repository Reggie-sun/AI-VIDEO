#!/usr/bin/env python3
"""Build the r4 short-window lip-sync pack for s031-s048 (SG16x, SG16y, SG18x, SG18y, SG20x). Local only, no calls.

  uv run python outputs/ai-city-takeover/ep01/v4/pilot/s031-048/r4/build.py

Basis: 「s039 拼切；剩下照这个写法拍，上限提到 15,000 (Recommended)」 (logs/decisions.md 2026-11-25, after the SG17 A/B
probe). For each unit of gen/unit.py R4_UNITS:
  1. pilot/audio/<UNIT>p.wav = the Demucs vocal stem's exact samples over the unit's song_window (cut_audio.cut_window:
     no fade, floor((L+R+1)/2) downmix) + digital zeros at the end to exactly the take's seconds; sealed in windows.json
     (`plays` = the edit span it serves). An existing wav or windows.json entry with other bytes is never overwritten.
  2. r4/<UNIT>-approval.template.json (the probe's template shape, take r-1; r-2 per its _template_notes).
  3. the empty take folders pilot/sd-<UNIT>-r-1|2.
and one approval page r4/index.html (first frame, vocal player, exact prompt, window, span, seconds, cost, vocal checks).
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import sys
import wave

import numpy as np

HERE = Path(__file__).resolve().parent
V4 = HERE.parents[2]
REPO = HERE.parents[6]
sys.path.insert(0, str(V4 / "gen"))
import cut_audio as C  # noqa: E402
import unit as U  # noqa: E402

AUDIO = V4 / "pilot/audio"
BOOK = AUDIO / "windows.json"
MASTER = V4 / "song/master/all-hands-r4-edc6c6bf.wav"
PAGE = HERE / "index.html"
URL = "http://127.0.0.1:8769/pilot/s031-048/r4/index.html"
QUOTE = "「s039 拼切；剩下照这个写法拍，上限提到 15,000 (Recommended)」"
# the edit spans of pilot/s031-048/plan/index.html (song s) and what each covers there
SPANS = {"s037b": (161.413, 163.701, "Stop it? Let it stay? It doesn't"), "s037d": (165.071, 166.476, "at twelve thirty-four."),
         "s041a": (178.329, 181.023, "the lights go low"), "s041c": (183.763, 185.585, "show … Octo-"),
         "s048": (205.241, 209.339, "they were told which crack.（208.80 后静止闭嘴到 All hands!）")}
# local Whisper large-v3 on each <UNIT>p.wav (2026-11-25, `whisper <wav> --model large-v3`): the reference vocal's own
# baseline for judging a take's words; no foreign words, no next-line onset heard
WHISPER = {"SG16x": "en：Stop it, let it stay / It doesn't（0–2.18 s）", "SG16y": "en：1234（0–1.22 s）",
           "SG18x": "en：Days the lights go low（0–2.24 s）", "SG18y": "en：show october（0–1.84 s）",
           "SG20x": "en：They were told which crack, crack, crack.（0–2.92 s；重复的 crack 是 Whisper 的常见幻听，原声只有一次）"}
CRD_PER_S, TAKES = 80, 2
CEILING_OLD, CEILING_NEW = 12800, 15000
# spent in s031-s048 so far by the task ledger, item by item from logs/decisions.md (2026-11-25 entries)
SPENT = [("SG12（a-1 720 + a-3 720 + b-1|2 1,440）", 2880), ("INS33", 640), ("INS37", 640), ("INS41", 640),
         ("SG19（a-2；a-1 known_no_effect）", 400), ("MO15（任务账）", 960), ("SG15", 800), ("SG17 A/B 探针", 1600)]
LOST = [
    ("s037d（SG16y）", "“说到第四句时微波炉的灯熄灭、转盘停下，她把碗放到台面上”不再写进 prompt：她会一直捧着碗；首帧 p037-c2 的微波炉亮着在转，"
     "而 INS37 刚拔掉插头。剪辑处理：s037d 里微波炉炉窗做后期局部压暗（转盘若可见则冻结该区域）；放碗这一拍丢失。"),
    ("s037b（SG16x）", "无动作要求，不丢拍；末 0.18 s（163.52–163.70）母带里是 “stop” 的 s- 起音，这段 take 嘴在收，切 INS37 盖住。"),
    ("s041c（SG18y）", "“Octo- 时一只手从布里抓住胸前布边”丢失（使用者已定：布一直裹着、不伸手）；手的那一拍由 INS41 与 185.585 的剪切承担。"),
    ("s041a（SG18x）", "无动作要求；射灯每拍暗一盏本来就是后期。"),
    ("s048（SG20x）", "无动作；“说完静止闭嘴”保留在 prompt 里。窗口从 “they” 前 0.3 s 起（205.819），s048 入点 205.241 早 0.578 s："
     "按探针的嘴晚 0.6–1.0 s 对齐时 take 开头正好盖住入点；若这条嘴不晚，入点后最多 0.578 s 用第 0 帧（闭嘴静止）顶上。"),
]


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def load(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path)) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, ch).astype(float).mean(1)
    return x / 32768, sr


def db(x: np.ndarray, sr: int, a: float, b: float) -> float:
    seg = x[round(a * sr):round(b * sr)]
    return round(float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)), 1)


def checks(t0: float, t1: float, words: list, stem, master, band) -> dict:
    """Dry vocal and clean edges: music bleed (the vocal stem projected on the band = Demucs bass + drums + other over the
    window, relative to the vocal), the band's own level there, the quietest 100 ms inside (stem vs master), the edges and
    the neighbouring words."""
    (v, sr), (m, srm) = stem, master
    hop, n = int(0.02 * sr), int(0.1 * sr)
    seg, acc = v[round(t0 * sr):round(t1 * sr)], band[round(t0 * sr):round(t1 * sr)]
    bleed = abs(float(seg @ acc)) / float(np.linalg.norm(acc) * np.linalg.norm(seg))       # |cos| = projection / vocal
    i = int(np.argmin([np.sqrt(np.mean(seg[k:k + n] ** 2)) for k in range(0, len(seg) - n, hop)]))
    q = round(t0 + i * hop / sr, 3)
    before = max((w for w in words if w["end"] <= t0 + C.TOLERANCE), key=lambda w: w["end"])
    after = min((w for w in words if w["start"] >= t1), key=lambda w: w["start"])
    return {"music_bleed_db": round(20 * np.log10(bleed + 1e-9), 1), "vocal_db": db(v, sr, t0, t1), "band_db": db(band, sr, t0, t1),
            "quietest_100ms": {"at": q, "vocal_db": db(v, sr, q, q + 0.1), "master_db": db(m, srm, q, q + 0.1)},
            "first_20ms_db": db(v, sr, t0, t0 + 0.02), "last_20ms_db": db(v, sr, t1 - 0.02, t1),
            "previous_word": [before["text"], before["end"]], "next_word": [after["text"], after["start"]],
            "next_word_gap_s": round(after["start"] - t1, 3)}


def main() -> None:
    words_book = json.loads(C.WORDS.read_text(encoding="utf-8"))
    words = [w for line in words_book["lines"] for w in line["words"]]
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    stem, master = load(C.STEM), load(MASTER)
    band = sum(load(C.STEM.with_name(f"{x}.wav"))[0] for x in ("bass", "drums", "other"))
    rows = []
    for unit, (clip, span, (t0, t1), secs, lines, _, _) in U.R4_UNITS.items():
        spec = U.SPECS[unit]
        if C.inside_word(t0, words_book) or C.inside_word(t1, words_book):
            raise SystemExit(f"{unit}: window {t0}-{t1} cuts inside a word")
        heard = " ".join(w["text"] for w in words if t0 <= w["start"] < t1)
        if heard != lines or spec["braced_line"] != lines:
            raise SystemExit(f"{unit}: braced line {lines!r} is not the window's words {heard!r}")
        voice, sr, n = C.cut_window(C.STEM, t0, t1)
        total = secs * sr
        payload = C.wav_bytes(voice + b"\x00\x00" * (total - n), sr)
        target = AUDIO / f"{unit}p.wav"
        if target.exists() and target.read_bytes() != payload:
            raise SystemExit(f"{rel(target)} exists with other bytes; never overwritten")
        a, b, _ = SPANS[span]
        entry = {"path": rel(target), "song_window": [t0, t1], "plays": [a, b], "samples": total, "sample_rate_hz": sr,
                 "seconds": float(secs), "sha256": sha_bytes(payload),
                 "padded": {"from": "stem", "from_sha256": book["source_sha256"], "voice_samples": n, "silence_samples": total - n,
                            "silence": "digital zeros appended at the end", "to_seconds": float(secs), "serves": span,
                            "basis": f"2026-11-25 r4 short windows, audio length = generation length ({QUOTE}, logs/decisions.md)"}}
        if book["windows"].get(f"{unit}p", entry) != entry:
            raise SystemExit(f"windows.json already seals another {unit}p window")
        if not target.exists():
            target.write_bytes(payload)
        book["windows"][f"{unit}p"] = entry
        prompt = U.r4_prompt(unit)
        rows.append({"unit": unit, "clip": clip, "span": span, "span_s": [a, b], "window": [t0, t1], "voice_s": round(n / sr, 3),
                     "seconds": secs, "lines": lines, "prompt": prompt, "prompt_sha256": sha_bytes(prompt.encode()),
                     "plate": spec["plate"], "plate_path": spec["image"][1], "plate_sha256": spec["plate_sha256"],
                     "vocal": entry, "est": secs * CRD_PER_S, "ceiling": -(-secs * 8 // 10) * 100,
                     "checks": checks(t0, t1, words, stem, master, band), "verb": "唱" if clip == "SG18" else "说"})
    BOOK.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    PAGE.write_text(page(rows), encoding="utf-8")
    page_ref = {"path": rel(PAGE), "sha256": sha_bytes(PAGE.read_bytes())}
    for row in rows:
        (HERE / f"{row['unit']}-approval.template.json").write_text(
            json.dumps(template(row, rows, page_ref), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        for k in (1, 2):
            (V4 / f"pilot/sd-{row['unit']}-r-{k}").mkdir(exist_ok=True)
    print(json.dumps({"page": page_ref, "units": {r["unit"]: [r["window"], r["seconds"], r["vocal"]["sha256"]] for r in rows}},
                     ensure_ascii=False))


def totals(rows: list) -> dict:
    est = sum(r["est"] for r in rows) * TAKES
    spent = sum(x for _, x in SPENT)
    return {"seconds": sum(r["seconds"] for r in rows), "est": est, "ceiling": sum(r["ceiling"] for r in rows) * TAKES,
            "spent": spent, "after": spent + est}


def page(rows: list) -> str:
    t = totals(rows)
    e = html.escape
    out = [f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>s031–s048 r4 短窗口对口型（SG16x、SG16y、SG18x、SG18y、SG20x）</title>
<style>
body{{font:15px/1.6 system-ui,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:#222}}
.q{{background:#fff4d6;border:2px solid #e0a800;padding:12px 16px;border-radius:8px}}
.q ol{{margin:6px 0 0}} pre{{white-space:pre-wrap;background:#f6f6f6;padding:10px;border-radius:6px}}
ins{{background:#c8f7c5;text-decoration:none}} img{{max-width:100%}}
table{{border-collapse:collapse}} td,th{{border:1px solid #ccc;padding:4px 8px;vertical-align:top}} code{{font-size:13px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}} .unit{{border-top:3px solid #888;margin-top:28px}}
</style></head><body>
<div class="q"><b>问题：</b>按下面 5 条 exact prompt 与人声短窗口拍 r4（SG16x、SG16y、SG18x、SG18y、SG20x 各 2 条，共 10 条，约 {t['est']:,} 积分；
本段上限 {CEILING_NEW:,}，旧上限 {CEILING_OLD:,}）吗？
<ol><li>按这 5 条开拍 (Recommended)</li><li>先改 prompt 或窗口再看</li><li>先不拍</li></ol>
审片地址：{URL}</div>

<h2>依据</h2>
<p>使用者原话{e(QUOTE)}（logs/decisions.md 2026-11-25 最后一条）。SG17 A/B 探针：B 臂（{{英文原台词}}）词准 80–90%，A 臂 30–50%；
四条都重新配音（copy=false），开口晚 0.6–1.0 s。本轮照 B 臂写法：每个剪辑段一个短窗口，prompt 含 {{该窗口的英文原词}}，每窗口 2 条，跨条量、剪、盖。</p>
<ul>
<li>窗口：剪辑段第一个词前约 0.3 s 起；落在上一个词里就从上一个词结束处起，且不晚于入点；止于剪辑段最后一个词结束。人声后补数字静音到整秒（≥4 s），音频长度 = 生成时长。</li>
<li>生成时长 = max(4, ⌈剪辑段结束 − 窗口起点 + 1.0 s⌉)：1.0 s 是探针里最晚的开口延迟，保证嘴晚 1 s 时 take 仍盖住整段。SG20x 因此 5 s，其余 4 s。</li>
<li>prompt：从 r3 的首帧状态句起，照探针 A/B 的精简写法（对镜头说/唱 + 口型逐字同步 + {{英文}} + 镜头固定 + 她在原地 + 本镜必需的空白/红色/文字规则）；不写任何绑台词的动作。</li>
<li>首帧与 r3 相同：p037-c2、p041-c1、p048-w2。</li>
</ul>

<h2>花费</h2>
<table>
<tr><th>单元</th><th>秒</th><th>每条（80 积分/秒）</th><th>2 条</th><th>每条上限</th></tr>"""]
    for r in rows:
        out.append(f"<tr><td>{r['unit']}</td><td>{r['seconds']}</td><td>{r['est']}</td><td>{r['est'] * TAKES:,}</td><td>{r['ceiling']}</td></tr>")
    out.append(f"""<tr><th>合计</th><th>{t['seconds']}</th><th></th><th>{t['est']:,}</th><th>{t['ceiling']:,}（10 条上限）</th></tr></table>
<p>本段已花（任务账，按 logs/decisions.md 逐条）：{"；".join(f"{e(k)} {v:,}" for k, v in SPENT)}，合计 <b>{t['spent']:,}</b>。
交接里写的约 10,840 与 decisions.md 逐条之和差 {10840 - t['spent']:,}，待主会话对账。</p>
<p>拍完 r4 后预计：{t['spent']:,} + {t['est']:,} = <b>{t['after']:,}</b>（按 10,840 算为 {10840 + t['est']:,}；10 条全按上限为 {t['spent'] + t['ceiling']:,} / {10840 + t['ceiling']:,}）。
本段上限 <b>{CEILING_NEW:,}</b>（新）；旧上限 {CEILING_OLD:,} 并存记录。</p>

<h2>会丢的方案节拍（剪辑处理或使用者知悉）</h2><ul>""")
    out += [f"<li><b>{e(k)}</b>：{e(v)}</li>" for k, v in LOST]
    out.append("</ul>")
    for r in rows:
        a, b = r["span_s"]
        c = r["checks"]
        q = c["quietest_100ms"]
        braced = e(f"她用英文{r['verb']}：{{{r['lines']}}}不增不减，不翻译。")
        prompt = e(r["prompt"]).replace(braced, f"<ins>{braced}</ins>")
        out.append(f"""
<div class="unit"><h2>{r['unit']} · {r['span']}（{r['clip']} 的一个剪辑段）</h2>
<table>
<tr><td>剪辑段（方案）</td><td>{r['span']} {a:.3f}–{b:.3f}（{b - a:.2f} s）：{e(SPANS[r['span']][2])}</td></tr>
<tr><td>人声窗口（歌曲 s）</td><td>{r['window'][0]:.3f}–{r['window'][1]:.3f}（人声 {r['voice_s']:.3f} s）+ 数字静音 → {r['seconds']:.3f} s</td></tr>
<tr><td>窗口里的词（words.json）</td><td><code>{e(r['lines'])}</code></td></tr>
<tr><td>生成</td><td>Seedance 2.0 VIP · multimodal（图 + 音频）· {r['seconds']} s · 4K · 16:9 · reference_audio</td></tr>
<tr><td>花费</td><td>80 积分/秒 × {r['seconds']} s × 2 条 = {r['est'] * TAKES:,}（每条上限 {r['ceiling']}）</td></tr>
<tr><td>take 文件夹</td><td>sd-{r['unit']}-r-1、sd-{r['unit']}-r-2</td></tr>
<tr><td>提交</td><td><code>VOCAL={r['unit']}p</code>，<code>T0 = {r['window'][0]}</code></td></tr>
</table>
<div class="grid"><div><p>首帧（与 r3 相同）<br><code>{e(r['plate_path'])}</code><br>sha256 <code>{r['plate_sha256']}</code></p>
<img src="../../../board/plates/{r['plate']}.png" alt="{r['plate']}"></div>
<div><p>人声 {r['unit']}p.wav（{r['seconds']:.3f} s = 生成时长）<br><code>{e(r['vocal']['path'])}</code><br>sha256 <code>{r['vocal']['sha256']}</code></p>
<audio controls preload="metadata" src="../../audio/{r['unit']}p.wav"></audio>
<p>人声检查：干声——窗口内人声轨 {c['vocal_db']} dB、伴奏三轨（bass+drums+other）{c['band_db']} dB，人声轨里与伴奏相关的成分比人声低 {-c['music_bleed_db']} dB
（最静的 100 ms 在 {q['at']:.3f}：人声轨 {q['vocal_db']} dB，母带 {q['master_db']} dB），判断无可闻音乐串音；
开头 20 ms {c['first_20ms_db']} dB（上一个词 “{e(c['previous_word'][0])}” 止于 {c['previous_word'][1]}），
结尾 20 ms {c['last_20ms_db']} dB；下一个词 “{e(c['next_word'][0])}” 在 {c['next_word'][1]} 才开始（窗口后 {c['next_word_gap_s']:.3f} s），窗口里没有下一句的起音。</p>
<p>本地 Whisper large-v3（参考人声本身的基线）：{e(WHISPER[r['unit']])}</p></div></div>
<h3>exact prompt</h3><p>sha256 <code>{r['prompt_sha256']}</code>（绿色为 {{英文原词}} 一句）</p><pre>{prompt}</pre></div>""")
    out.append("""
<h2>每条量什么（逐镜 Gate 之前与之中）</h2>
<ol><li>语言：英语；逐词准确度对照 {} 里的原词。</li><li>copy、lag / ncc、spans（sync_check.py，T0 = 窗口起点）：开口延迟与同步区间换算到歌曲时间，看能否盖住剪辑段。</li>
<li>静音补齐段嘴唇闭合（会念进去的话按 lag 截掉）。</li><li>逐镜 Gate（video-analysis MCP）：脸与身份、首帧构图不变、镜头固定、她在原地、空白/红色/文字规则、口型按词对齐；只验收本单元服务的剪辑段。</li></ol>
</body></html>
""")
    return "\n".join(out)


def template(row: dict, rows: list, page_ref: dict) -> dict:
    unit, ident = row["unit"], f"iris-{row['unit'].lower()}-r-1"
    r3 = json.loads((HERE.parent / f"r3/{row['clip']}-approval.template.json").read_text(encoding="utf-8"))
    return {
        "schema": "iris-v4-preview-approval/1",
        "unit_group": f"v4-{row['span']}-r4-{unit}-r-1",
        "question": f"<主会话问使用者的原问题，逐字（认可页 {page_ref['path']}）>",
        "user_quote": "<使用者原话，逐字>",
        "approved_at": "<UTC ISO 时间，带时区>",
        "preview_page": page_ref,
        "preview_artifacts": [{"path": row["plate_path"], "sha256": row["plate_sha256"], "role": f"{unit} reference image"},
                              {"path": row["vocal"]["path"], "sha256": row["vocal"]["sha256"], "role": f"{unit} vocal"}],
        "prompts": {unit: {"text": row["prompt"], "sha256": row["prompt_sha256"]}},
        "generation": U.SPECS[unit]["generation"],
        "budget": {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": row["ceiling"], "cumulative_CRD": row["ceiling"]},
        "identity_waivers": ["IRIS"],
        "identity_waiver_basis": r3["identity_waiver_basis"],
        "bound_ids": {"attempt_id": f"{ident}-source-001", "policy_id": f"{ident}-source-001",
                      "reservation_id": f"{ident}-reservation-001"},
        "takes": {"approval": "one approval, two takes per unit from the same first frame and vocal; spans measured, cut and "
                              "covered across takes after both Gates",
                  "folders": [f"sd-{unit}-r-1", f"sd-{unit}-r-2"], "generations_per_take": 1, "total_generations": 2,
                  "total_ceiling_CRD": 2 * row["ceiling"], "this_take": f"sd-{unit}-r-1",
                  "r4": {"units": [r["unit"] for r in rows], "total_takes": TAKES * len(rows),
                         "total_ceiling_CRD": TAKES * sum(r["ceiling"] for r in rows),
                         "section_ceiling_CRD": CEILING_NEW, "previous_section_ceiling_CRD": CEILING_OLD}},
        "decision_notes": [
            f"使用者原话{QUOTE}（logs/decisions.md 2026-11-25）：SG16、SG20、SG18 改写为 prompt 含 {{英文原台词}}、按剪辑段拆 4–5 s 短窗口、"
            "每窗口 2 条、跨条量剪盖；本段上限 12,800 → 15,000。",
            f"{unit} 服务 {row['span']}（{row['span_s'][0]}–{row['span_s'][1]}）；人声 {unit}p.wav = 人声轨 {row['window'][0]}–{row['window'][1]}"
            f"（{row['voice_s']} s）逐样本 + 末尾数字静音，共 {row['seconds']} s；花括号内为该窗口 words.json 的原词。",
            "prompt 不写任何绑台词的动作（放碗、微波炉熄灯、伸手抓布）；丢失的节拍见认可页“会丢的方案节拍”。",
            f"旧 sd-{row['clip']}-a-1|2 的审批原样挂起，不因 r4 改动。"],
        "_template_notes": [
            f"本文件是 {unit} 的 r-1 模板；使用者在认可页认可后，写成 pilot/sd-{unit}-r-1/preview-approval.json：删除本 _template_notes "
            "字段并填好 question / user_quote / approved_at 三个占位，其余逐字不变。",
            f"r-2：unit_group 末尾 r-1→r-2；bound_ids 三个 id 中 -r-1- → -r-2-；takes.this_take → sd-{unit}-r-2（takes.folders 保持 "
            "[r-1, r-2]）；其余逐字相同。",
            f"prep_unit.sh 命令（主会话执行）：TRIAL_DIR=outputs/ai-city-takeover/ep01/v4/pilot/sd-{unit}-r-<k> bash "
            f"outputs/ai-city-takeover/ep01/v4/gen/prep_unit.sh {unit} {row['seconds']} multimodal {row['ceiling']}；run_unit.sh 用 "
            f"VOCAL={unit}p，T0 = {row['window'][0]}"],
    }


if __name__ == "__main__":
    main()
