#!/usr/bin/env python3
"""Stills gallery for review at checkpoint B: every still the v2 shots-map uses, in film order, with its units and prompt.

  python3 outputs/ai-city-takeover/ep01/v3/build_plates_index.py   ->  ep01/v3/plates/index.html
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
m = json.loads((HERE / "shots-map.json").read_text())
book = (HERE / "plates/prompts.md").read_text()


def prompt_of(key: str) -> str:
    name = re.sub(r"-a$", "", key)
    hit = re.search(rf"^## {re.escape(name)}\n.*?```prompt\n(.*?)\n```", book, re.S | re.M)
    return hit.group(1) if hit else "（提示词在 casting 或 v1 记录里）"


order, uses = [], {}
for s in m["shots"]:
    for p in s["plates"]:
        key = Path(p["plate"]).stem
        if key not in uses:
            order.append((key, p["plate"]))
            uses[key] = []
        uses[key].append(f'{s["unit"]} {s["t0"]:.2f}–{s["t1"]:.2f} {s["lyric"]}')

cards = []
for key, rel in order:
    src = "raw/" + Path(rel).name if rel.startswith("ep01/v3/plates/") else "../../../" + rel
    units = "<br>".join(html.escape(u) for u in uses[key])
    cards.append(f'<figure><a href="{src}" target="_blank"><img src="{src}" loading="lazy"></a><figcaption><b>{html.escape(key)}</b>'
                 f'<div class="u">{units}</div><details><summary>提示词</summary>{html.escape(prompt_of(key))}</details></figcaption></figure>')
page = f"""<!doctype html><meta charset="utf-8"><title>IRIS EP01 · 分镜 v2 静图</title>
<style>body{{background:#0b0d12;color:#dfe6ee;font:14px/1.5 system-ui,sans-serif;margin:24px}}h1{{font-size:20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(440px,1fr));gap:18px}}figure{{margin:0;background:#141821;padding:10px;border-radius:6px}}
img{{width:100%;display:block;border-radius:4px}}.u{{color:#9fb0c4;font-size:12px;margin:4px 0}}details{{color:#8796a8;font-size:12px}}</style>
<h1>IRIS EP01 · 分镜 v2 用到的静图（{len(order)} 张，按出场顺序）</h1>
<p>这些是动画分镜的静图替身，也是之后生成视频的首帧与数字人底图候选。点图看原图。</p>
<div class="grid">{''.join(cards)}</div>"""
(HERE / "plates/index.html").write_text(page)
print(len(order), "stills")
