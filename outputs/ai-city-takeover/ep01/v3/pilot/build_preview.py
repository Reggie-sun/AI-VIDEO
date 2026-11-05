#!/usr/bin/env python3
"""Stage-7 pilot reference package -> pilot/preview-inputs.json + pilot/preview.html (nothing is submitted from here).

  python3 outputs/ai-city-takeover/ep01/v3/pilot/build_preview.py

Pilot = board v2 units U020–U029 (song 54.69–89.52 s: pre-chorus 1 + chorus 1) plus a separate crowd test U045.
Paid units: five digital-human singing takes (Jimeng 数字人 · 大师模式) and two Seedance 2.0 first-frame shots;
U024 U026 U028 U029 stay code shots from the animatic. Every model input is listed with its SHA-256 so the user's
approval can be sealed against exact bytes; prompts are pure Chinese.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
V3 = HERE.parent
sha = lambda p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
PL = "outputs/ai-city-takeover/ep01/v3/plates/raw/"
windows = json.loads((HERE / "audio/windows.json").read_text())["windows"]
board = {s["unit"]: s for s in json.loads((V3 / "shots-map.json").read_text())["shots"]}

OH = {   # unit: (base still, action description) — each take has its own body beat (Codex review #1), all start mouth-closed
    "U020": ("P-gap-face-shut-b", "镜头固定近景。她冷静而克制地对着镜头低声耳语，嘴随歌词轻轻张合，眼神从下往上看着镜头，头几乎不动；唱最后那个长音时下巴慢慢抬起，眉头放松。"),
    "U021": ("P-gap-mcu-shut-b", "镜头固定中景。她冷静但投入地对着镜头唱歌，嘴随歌词自然张合，肩膀放松，重心落在后脚，句尾轻轻吸一口气，眉头放松，眼睛向上直视镜头，双手自然垂在身侧。"),
    "U022": ("P-gap-34-shut-b", "镜头固定近景。她冷静但投入地对着镜头唱歌，嘴随歌词自然张合，唱到最后的长音时身体向镜头前倾，眼睛微微眯起，眉头放松，眼神始终看着镜头。"),
    "U025": ("P-gap-mcu-turn-shut-b", "镜头固定中景。开始时她侧头看着画面右侧的门缝；唱第一个长音时慢慢把头转回来，直视镜头；两个长音之间换一口气，再唱第二个长音，长音时嘴张开并保持，眉头放松。"),
    "U027": ("P-gap-face-shut-b", "镜头固定近景。她冷静但投入地对着镜头唱歌，嘴随歌词自然张合，唱完最后一个字后嘴慢慢合上，停住不动，眉头放松，眼神始终直视镜头。"),
}
SD = {   # unit: (first frame, prompt)
    "U023": ("P-city-gap-a", "镜头固定。首帧是从一扇只开着一指宽的黑色门缝向外看出去的画面：门缝两侧是黑暗的门板边缘，缝里是凌晨三点雾中的城市。门不动，门缝始终只有一指宽。缝外的城市在动：高架桥上的车灯缓缓流过，远处高楼的窗灯安静地亮着，雾气慢慢飘过。城市的光是冷白和钢蓝色。画面里没有人。"),
    "U045": ("P-floor-line-at-a", "镜头固定。她从一排闭着眼睛、一动不动的副本中间，一步跨过地面上的白色标线，停在线外，冰灰色的眼睛直视镜头，神情平静而带着压迫感。她身边的副本始终闭着眼睛，一动不动，身上的灯都是熄灭的。冷蓝的光雾贴着湿润的地面缓缓流动。"),
}
ACCEPT_OH = ["正常速度和原曲合在一起看，她是在唱：每一句的嘴都在动、句中没有冻住的脸（口型大致同步即可，不要求逐字极准）", "身份符合 canon v4：银白眉睫、冰灰眼；正面时耳挂与立领红线在画面右侧", "没有凭空出现的手或物体、没有牙齿碎裂、没有身份漂移", "背景与机位稳定（不漂、不晃）", "表演克制、不做作：不皱眉、不夸张张嘴；动作按描述（呼吸、重心、视线）有变化"]
EXTRA_OH = {"U020": ["耳语明显比副歌轻，最后的长音时下巴抬起、嘴型保持"], "U025": ["开始看着门缝，第一个长音中把头转回镜头", "两个长音之间有一次换气，每个长音期间嘴保持张开"], "U027": ["唱完后嘴自然合上并停住"]}
ACCEPT_SD = {"U023": ["5 s 里至少有连续 2.67 s 可用：门缝宽度不变、门没有打开或变宽、车灯在流动", "镜头固定", "没有人、没有红色、没有任何文字或标识"],
             "U045": ["5 s 里有一段约 2.53 s：开始时她脚尖贴着标线，结束时她已站在线外并停下直视镜头", "副本全程闭眼、静止、灯灭、银发同款，不变形、不移动", "镜头固定", "身份符合 canon v4，耳挂与立领红线在画面右侧", "跨线不完整或任何副本动了，就算失败"]}
for t in [p for _, p in OH.values()] + [p for _, p in SD.values()]:
    assert not re.findall(r"[A-Za-z]", t), t


def main() -> None:
    oh = {}
    for u, (still, text) in OH.items():
        w = windows[u]
        oh[u] = {"image": {"path": PL + still + ".png", "sha256": sha(PL + still + ".png")},
                 "audio": {"path": w["path"], "sha256": w["sha256"], "seconds": w["seconds"], "song_window": w["song_window"]},
                 "action_prompt": text, "action_prompt_sha256": hashlib.sha256(text.encode()).hexdigest(),
                 "edit_window": board[u]["t0"], "lyric": board[u]["lyric"], "accept": ACCEPT_OH + EXTRA_OH.get(u, [])}
    sd = {}
    for u, (still, text) in SD.items():
        sd[u] = {"first_frame": {"path": PL + still + ".png", "sha256": sha(PL + still + ".png")},
                 "prompt": text, "prompt_sha256": hashlib.sha256(text.encode()).hexdigest(),
                 "edit_window": [board[u]["t0"], board[u]["t1"]], "accept": ACCEPT_SD[u]}
    doc = {"about": "IRIS EP01 board v2 · stage 7 representative pilot. Nothing is submitted before the user approves this exact package; the approval is then sealed per lane.",
           "segment": {"units": "U020–U029", "song": [54.69, 89.52], "crowd_test": "U045 (song 144.80–147.33)"},
           "code_units": ["U024", "U026", "U028", "U029"],
           "digital_human": {"mode": "即梦 数字人 · 大师模式 · output size follows the still (16:9 still → 1920×1088 last time)", "takes": oh},
           "seedance": {"generation": {"model": "Seedance 2.0 VIP", "mode": "first_frame", "seconds": 5, "resolution": "1080p", "ratio": "16:9", "audio": None},
                        "identity_waivers": ["IRIS"], "units": sd},
           "order": "one at a time: submit → fetch → per-shot gate (shot-gate-reviewer, video-analysis MCP) → next; continuity report (continuity-supervisor) and lint before each submit",
           "placement": {"digital_human": "clip second 0 = song time of the audio window start (unit start − 0.3 s); after fetch, align the clip's own audio to the vocal stem by cross-correlation (motion-kit/tools/sync_check.py) and use only the aligned [unit start, unit end]; the page may round the audio length to mm:ss (floor or ceiling); a clip longer than its audio (5.00 s → 5.13 s last time) is trimmed by the alignment; judge it composited with the original song at normal speed",
                         "seedance": "generate 5 s, choose the usable window inside it per the unit's acceptance list (U023 2.67 s, U045 2.53 s); the film keeps the T4 master as its only audio"},
           "budget": {"digital_human": {"takes": 5, "retries": 0, "cap_per_take": 165, "last_seen_price_5s": 30},
                      "seedance": {"takes": 2, "retries": 0, "cap_per_take": 165},
                      "total_cap": 1155, "cap_note": "1155 credits is the reserved ceiling for the seven takes, not a quote or a settled price",
                      "rule": "read the page price, duration and exact balance before and after each submit; any unknown outcome stops the pilot"},
           "stop": ["the digital-human entry review refuses the new face: stop, no preprocessing to get past it",
                    "a take repeats a frozen face, broken teeth, extra hands or identity drift: stop that lane and report, no extra take",
                    "the page shows an audio length that is neither the floor nor the ceiling of the file length: stop"]}
    (HERE / "preview-inputs.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")

    def card(u, img, body):
        return f'<section><h3>{u} · {board[u]["t0"]:.2f}–{board[u]["t1"]:.2f} · {html.escape(board[u]["lyric"])}</h3><img src="../plates/raw/{Path(img).name}">{body}</section>'
    rows = []
    for u, t in oh.items():
        rows.append(card(u, t["image"]["path"], f'<audio controls src="audio/{u}.wav"></audio><p class="p">{html.escape(t["action_prompt"])}</p>'
                         f'<ul>{"".join(f"<li>{html.escape(a)}</li>" for a in t["accept"])}</ul>'))
    for u, t in sd.items():
        rows.append(card(u, t["first_frame"]["path"], f'<p class="p">{html.escape(t["prompt"])}</p><ul>{"".join(f"<li>{html.escape(a)}</li>" for a in t["accept"])}</ul>'))
    page = f"""<!doctype html><meta charset="utf-8"><title>IRIS EP01 · 试拍参考包</title>
<style>body{{background:#0b0d12;color:#dfe6ee;font:14px/1.6 system-ui,sans-serif;margin:24px;max-width:1500px}}
section{{display:grid;grid-template-columns:560px 1fr;gap:6px 18px;background:#141821;padding:12px;margin:14px 0;border-radius:6px}}
h3{{grid-column:1/-1;margin:0;font-size:15px}}img{{width:560px;border-radius:4px;grid-row:span 3}}.p{{color:#f3d9a8}}ul{{color:#9fb0c4;margin:0}}</style>
<h1>试拍参考包（阶段 7）：U020–U029（54.69–89.52 s）＋ 群像测试 U045</h1>
<p>数字人 5 条（即梦数字人 · 大师模式，底图为闭嘴版、音频为该句人声分轨前后各留 0.3 s）、Seedance 2.0 首帧 2 条；U024 U026 U028 U029 用动画分镜里的代码镜头。逐条执行：提交 → 取回 → 逐镜 Gate → 下一条。预留上限：每条 165 积分、合计 1155（上限，不是报价；每条提交前读页面价格、时长与余额），不重试；上次数字人 5 秒网页价 30。数字人片段的第 0 秒对应该句音频窗口的起点，取回后按自带音轨对齐，只取本单元那一段，和原曲合在一起按正常速度审看。</p>
<p>动画分镜里的这一段：<a href="../review/animatic-a1.html#t=54.69">review/animatic-a1.html</a></p>
{''.join(rows)}"""
    (HERE / "preview.html").write_text(page)
    print(json.dumps({"oh": list(oh), "sd": list(sd)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
