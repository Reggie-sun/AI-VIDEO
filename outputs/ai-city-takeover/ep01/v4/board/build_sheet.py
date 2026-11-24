#!/usr/bin/env python3
"""Board review sheet (author's "one card per shot") -> board/index.html.

  python3 -I outputs/ai-city-takeover/ep01/v4/board/build_sheet.py

Cover: board.md rendered (treatment, device, chapter map, type system, looks, open questions, self-check).
Then one card per shot of shots.json, grouped by chapter: id, time, section, the lyric it types, framing, what moves,
the place, the action, the explaining graphics, the chrome, where it came from. Plate images appear on a card when
plates/<plate>.png exists (none yet: the board is reviewed before plates are made).
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIER = {"sung": "口型片段", "motion": "动作片段", "plate3d": "2.5D 底片", "still": "静帧"}


def inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def md(text: str) -> str:
    out, i, lines = [], 0, text.split("\n")
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("#"):
            n = len(ln) - len(ln.lstrip("#"))
            out.append(f"<h{n + 1}>{inline(ln[n:].strip())}</h{n + 1}>")
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[\s\-:|]+\|$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            out.append("<table>" + "".join(
                "<tr>" + "".join(f"<{'th' if r == 0 else 'td'}>{inline(c)}</{'th' if r == 0 else 'td'}>" for c in row) + "</tr>"
                for r, row in enumerate(rows)) + "</table>")
            continue
        elif re.match(r"^\s*(\d+\.|-)\s", ln):
            items = []
            while i < len(lines) and re.match(r"^\s*(\d+\.|-)\s", lines[i]):
                items.append(re.sub(r"^\s*(\d+\.|-)\s", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue
        elif ln.strip():
            out.append(f"<p>{inline(ln)}</p>")
        i += 1
    return "\n".join(out)


def fmt(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:05.2f}"


def device_text(d: dict) -> str:
    p = json.dumps(d.get("params") or {}, ensure_ascii=False)
    texts = re.findall(r'"(?:text|title|label|value|rows|sub|source)":\s*"([^"]+)"', p)
    body = " · ".join(dict.fromkeys(texts))[:220]
    line = f"（第 {d['line']} 行）" if d.get("line") is not None else ""
    return f"<b>{html.escape(str(d.get('kind')))}</b>{line} {html.escape(body)}"


def main() -> None:
    board = json.loads((HERE / "shots.json").read_text())
    cover = md((HERE / "board.md").read_text())
    chapters = {c["id"]: c for c in board["chapters"]}
    cards, cur = [], None
    for s in board["shots"]:
        if s.get("chapter") != cur:
            cur = s.get("chapter")
            c = chapters.get(cur, {})
            cards.append(f'<h2 class="ch">{html.escape(c.get("name", str(cur)))} · {fmt(c.get("t0", s["t0"]))}–{fmt(c.get("t1", s["t1"]))}</h2>')
        img = HERE / "plates" / f"{s.get('plate')}.png"
        pic = (f'<img src="plates/{s["plate"]}.png">' if img.exists()
               else f'<div class="np">{html.escape((s.get("prompt") or "（纯图形）")[:90])}…</div>')
        lyr = "<br>".join(html.escape(t.get("text", "")) for t in s.get("type") or []) or '<span class="dim">（无歌词）</span>'
        devs = "".join(f"<li>{device_text(d)}</li>" for d in s.get("devices") or [])
        cards.append(f"""<div class="card"><div class="pic">{pic}</div><div class="meta">
<div class="hd"><b>{s['id']}</b> {fmt(s['t0'])}–{fmt(s['t1'])} · {s['t1'] - s['t0']:.1f}s · {html.escape(s.get('section') or '')} ·
{html.escape(s.get('framing') or '')} · <span class="tier {s.get('motion_tier')}">{TIER.get(s.get('motion_tier'), s.get('motion_tier'))}</span>
{'' if s.get('lead_on_screen') else '<span class="ins">插入镜头</span>'}</div>
<div class="lyr">{lyr}</div>
<div><span class="k">地点</span>{html.escape(s.get('set') or '')}</div>
<div><span class="k">动作</span>{html.escape(s.get('action') or '')}</div>
<div><span class="k">机位</span>{html.escape(s.get('camera') or '')}</div>
<div><span class="k">图形</span><ul>{devs}</ul></div>
<div class="dim"><span class="k">常驻</span>{html.escape(s.get('chrome') or '')}</div>
<div class="dim"><span class="k">出处</span>{html.escape(s.get('notes') or '')}</div>
</div></div>""")
    (HERE / "index.html").write_text(f"""<!doctype html><meta charset="utf-8"><title>检查点 4 · 分镜</title>
<style>
body{{background:#0b0d12;color:#dfe6ee;font:14px/1.6 system-ui,sans-serif;margin:24px auto;max-width:1400px;padding:0 24px}}
h1{{font-size:24px}}h2{{font-size:19px;margin-top:30px;color:#f3d9a8}}h3{{font-size:16px}}
table{{border-collapse:collapse;margin:8px 0}}td,th{{border:1px solid #263040;padding:4px 8px;vertical-align:top}}th{{color:#9fb4c7}}
code{{color:#f3d9a8}}details.cover{{background:#11151c;padding:8px 16px;border-radius:6px}}summary{{cursor:pointer;font-size:16px}}
.ch{{border-bottom:1px solid #263040;padding-bottom:4px}}
.card{{display:flex;gap:16px;border-bottom:1px solid #1b2230;padding:12px 0}}
.pic{{flex:0 0 320px}}.pic img{{width:320px}}.np{{width:300px;height:160px;background:#151a22;color:#6f7d8b;font-size:12px;padding:10px;overflow:hidden}}
.meta{{flex:1}}.hd{{color:#9fb4c7}}.lyr{{color:#f3d9a8;font-size:16px;margin:4px 0}}
.k{{display:inline-block;width:40px;color:#6f7d8b}}.dim{{color:#7f8b97;font-size:13px}}ul{{margin:2px 0 2px 40px;padding:0}}
.tier{{padding:0 6px;border-radius:3px;color:#0b0d12}}.sung{{background:#f3d9a8}}.motion{{background:#7fc8ff}}.plate3d{{background:#9be3a0}}.still{{background:#aaa}}
.ins{{background:#553;padding:0 6px;border-radius:3px}}
</style>
<h1>IRIS EP01《All Hands》· 检查点 4 · 分镜（{len(board['shots'])} 镜）</h1>
<p>三位导演（时装片、梗密度、叙事）各出一版 → 三位评审打分（时装片 241、梗密度 231、叙事 229）→ 总导演以时装片为底合并 → 审计全过。
卡片还没有底片，左边是 prompt 开头；底片在分镜认可后出。请按镜头编号（如 s017）提意见：脸、重复、无聊的段落、故事逻辑、颜色。</p>
<details class="cover" open><summary>设计总览（treatment、贯穿装置、章节、字体、造型、开放问题、自查数据）</summary>{cover}</details>
{''.join(cards)}
""")
    print(len(board["shots"]), "cards")


if __name__ == "__main__":
    main()
