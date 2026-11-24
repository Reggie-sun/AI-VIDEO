#!/usr/bin/env python3
"""Checkpoint 3 review page: face/index.html with each test plate's a/b next to the old v3 identity anchor.

  python3 -I outputs/ai-city-takeover/ep01/v4/face/build_page.py
"""
from __future__ import annotations

import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = {"F1-window": "清晨窗边，刚被值班电话叫醒（正脸，认脸用）",
         "F2-singing": "深夜空办公室，举着手机放声唱（唱歌的嘴型）",
         "F3-runway": "地下停车场里的时装秀 T 台（全身、造型）",
         "F4-profile": "无人出租车后座，纯侧面（左耳装置、左右规则）"}


def main() -> None:
    book = (HERE / "prompts.md").read_text(encoding="utf-8")
    secs = []
    for key, label in NAMES.items():
        prompt = re.search(rf"^## {key}\b.*?```prompt\n(.*?)\n```", book, re.S | re.M).group(1)
        figs = "".join(
            f'<figure><a href="raw/{key}-{v}.png"><img src="raw/{key}-{v}.png"></a><figcaption>{key}-{v}</figcaption></figure>'
            if (HERE / f"raw/{key}-{v}.png").exists() else f'<figure class="todo"><figcaption>{key}-{v}（没出来）</figcaption></figure>'
            for v in "ab")
        secs.append(f"<section><h2>{key} · {html.escape(label)}</h2><div class=g>{figs}</div>"
                    f"<details><summary>提示词</summary><p>{html.escape(prompt)}</p></details></section>")
    (HERE / "index.html").write_text(f"""<!doctype html><meta charset="utf-8"><title>检查点 3 · 认脸</title>
<style>body{{background:#0b0d12;color:#dfe6ee;font:15px/1.6 system-ui,sans-serif;margin:24px;max-width:1500px}}
.g{{display:flex;gap:12px}}figure{{margin:0;flex:1}}img{{width:100%;display:block}}figcaption{{color:#7f93a8;font-size:13px}}
.todo{{background:#151a22;min-height:200px}}details p{{color:#9aa6b2;font-size:13px}}h2{{font-size:17px;margin-top:28px}}
.old img{{width:360px}}</style>
<h1>检查点 3 · 认脸</h1>
<p>用 Codex 出图，提示词按作者的写法写（景别 → 她的固定外形 → 服装 → 在哪里做什么 → 留白 → 胶片风格词 → 不要文字）。外形文字原样取自定稿 v4。
没有挂参考图，所以同一段文字下脸会有出入：每张出了 a、b 两版。你选中的那张脸，以后全片每张底片都拿它做身份参考。</p>
<p>旧的身份锚点（v3 时期，CG 质感）：</p>
<div class="g old"><figure><img src="old-E3-close-a.png"></figure></div>
{''.join(secs)}
""")


if __name__ == "__main__":
    main()
