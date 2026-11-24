#!/usr/bin/env python3
"""Listening-check page for the chosen take + lyric page v5.

  python3 -I outputs/ai-city-takeover/ep01/v4/song/build_review.py

Writes song/review/index.html: the song with word-by-word highlight from timing/words.json, sections on the bar grid
from music-map.json, the words that still need an ear check (timing/listen.json) in orange, click any word to jump.
Also rewrites lyrics/index.html as the v5 lyric with Chinese glosses (lyrics/glosses-v5.json); Chinese is for the
director only, never on screen.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V4 = HERE.parent

PAGE = """<!doctype html><meta charset="utf-8"><title>听歌对时 · All Hands r4</title>
<style>
body{background:#0b0d12;color:#dfe6ee;font:15px/1.6 system-ui,sans-serif;margin:0}
header{position:sticky;top:0;background:#0b0d12f0;padding:14px 24px;border-bottom:1px solid #223;z-index:2}
audio{width:100%}
#map{display:flex;height:22px;margin-top:8px;cursor:pointer}
#map div{border-right:1px solid #0b0d12;font-size:11px;overflow:hidden;white-space:nowrap;padding:2px 4px;color:#0b0d12}
main{max-width:1100px;margin:0 24px 200px}
.sec{color:#7f93a8;font-size:13px;margin-top:22px}
.ln{display:flex;gap:18px;padding:3px 0}
.en{flex:0 0 560px;color:#9aa6b2;font-size:17px}
.zh{color:#6f7d8b;font-size:14px}
.w{cursor:pointer;border-radius:3px;padding:0 1px}
.w.on{color:#0b0d12;background:#f3d9a8}
.w.done{color:#f3d9a8}
.w.chk{text-decoration:underline wavy #ff8a3d}
.ln.cur .zh{color:#c7d2dd}
p.note{color:#9aa6b2;max-width:900px}
b.o{color:#ff8a3d}
</style>
<header>
<div>IRIS EP01《All Hands》· Suno take r4 · __BPM__ BPM · __DUR__ · <span id="clock">0.00</span>s · 小节 <span id="bar">1</span></div>
<audio id="a" controls preload="auto" src="../master/all-hands-r4-preview.m4a"></audio>
<div id="map"></div>
</header>
<main>
<p class="note">这一页用来用耳朵核对逐字时间：播放时唱到哪个词，哪个词就亮。点任何一个词会跳到那里。
<b class="o">橙色波浪线</b>的 __NLISTEN__ 个词是三路对时（CTC、Suno、Whisper）对不上的，请重点听：亮的时候是不是正好唱到它。
其余 __NOK__ 个词至少两路一致。中文只给你看意思，画面里不会出现。</p>
<div id="lyr"></div>
</main>
<script>
const W=__WORDS__, M=__MAP__, CHK=new Set(__CHK__);
const a=document.getElementById('a'), lyr=document.getElementById('lyr'), map=document.getElementById('map');
const COL={Chorus:'#f3d9a8','Final Chorus':'#ffb36b','Post-Chorus':'#d98bff',Bridge:'#7fc8ff',Outro:'#8fa3b5'};
const secs=[M.pre].concat(M.sections);
secs.forEach(s=>{const d=document.createElement('div');d.style.flex=(s.t1-s.t0);d.style.background=COL[s.section]||'#4d6a85';
 d.textContent=s.section;d.title=`${s.section} 小节 ${s.bar}，${s.bars} 小节，${s.t0}s`;d.onclick=()=>{a.currentTime=s.t0;a.play()};map.appendChild(d)});
const spans=[];let last=null;
W.lines.forEach((l,li)=>{
 if(l.section!==last){const h=document.createElement('div');h.className='sec';const s=M.sections.find(s=>s.section===l.section&&l.start<s.t1+1);
  h.textContent=`[${l.section}]`+(s?`  小节 ${s.bar} · ${s.bars} 小节 · ${s.t0}s`:'');lyr.appendChild(h);last=l.section}
 const r=document.createElement('div');r.className='ln';const en=document.createElement('div');en.className='en';
 l.words.forEach((w,wi)=>{const s=document.createElement('span');s.className='w'+(CHK.has(li+':'+wi)?' chk':'');s.textContent=w.text;
  s.title=`${w.start.toFixed(2)}s · ${w.src}`;s.onclick=()=>{a.currentTime=Math.max(0,w.start-1.0);a.play()};
  en.appendChild(s);en.appendChild(document.createTextNode(' '));spans.push({s,w,r})});
 const zh=document.createElement('div');zh.className='zh';zh.textContent=l.zh||'';r.appendChild(en);r.appendChild(zh);lyr.appendChild(r)});
let cur=null;
function tick(){const t=a.currentTime;document.getElementById('clock').textContent=t.toFixed(2);
 document.getElementById('bar').textContent=1+Math.max(0,Math.floor((t-M.sections[0].t0)/M.bar_s)+M.sections[0].bar-1);
 for(const o of spans){const on=t>=o.w.start&&t<Math.max(o.w.end,o.w.start+0.15);o.s.classList.toggle('on',on);o.s.classList.toggle('done',t>=o.w.end&&!on);
  if(on&&cur!==o.r){if(cur)cur.classList.remove('cur');cur=o.r;cur.classList.add('cur');
   const y=o.r.getBoundingClientRect().top;if(y<160||y>innerHeight-120)o.r.scrollIntoView({block:'center',behavior:'smooth'})}}
 requestAnimationFrame(tick)}
requestAnimationFrame(tick);
</script>
"""

LYR = """<!doctype html><meta charset="utf-8"><title>歌词 v5</title>
<style>body{background:#0b0d12;color:#dfe6ee;font:15px/1.6 system-ui,sans-serif;margin:24px;max-width:1300px}td{padding:3px 12px;vertical-align:top}.en{color:#f3d9a8;font-size:16px;white-space:nowrap}.t td{color:#7f93a8;padding-top:14px;font-size:13px}</style>
<h1>IRIS EP01《All Hands》歌词 v5（已做成歌：Suno take r4）</h1>
<p>四个写手 → 评审合并 → 批评修改 → 换副歌（All hands! All night!）。打分：音节 86，押韵 84（作者 EV 是 75／39）；Suno 歌词栏 3,013 字符。
听歌对时页：<a style="color:#7fc8ff" href="../song/review/">../song/review/</a>。中文只是给你看的意思，画面里不出现中文。</p>
<table>__ROWS__</table>
"""


def main() -> None:
    words = json.loads((HERE / "timing/words.json").read_text())
    mm = json.loads((HERE / "music-map.json").read_text())
    listen = json.loads((HERE / "timing/listen.json").read_text())["words"]
    gl = json.loads((V4 / "lyrics/glosses-v5.json").read_text())
    chk, nw = [], 0
    for li, ln in enumerate(words["lines"]):
        ln["zh"] = gl.get(ln["en"], "")
        for wi, w in enumerate(ln["words"]):
            nw += 1
            if any(abs(w["start"] - x["t"]) < 0.01 and w["text"] == x["word"] and ln["en"] == x["line"] for x in listen):
                chk.append(f"{li}:{wi}")
    slim = {"lines": [{"en": l["en"], "zh": l["zh"], "section": l["section"], "start": l["start"],
                       "words": [{k: w[k] for k in ("text", "start", "end", "src")} for w in l["words"]]} for l in words["lines"]]}
    dur = mm["duration"]
    page = (PAGE.replace("__WORDS__", json.dumps(slim, ensure_ascii=False)).replace("__MAP__", json.dumps(mm))
            .replace("__CHK__", json.dumps(chk)).replace("__BPM__", str(mm["bpm_global"]))
            .replace("__DUR__", f"{int(dur // 60)}:{int(dur % 60):02d}").replace("__NLISTEN__", str(len(chk)))
            .replace("__NOK__", str(nw - len(chk))))
    (HERE / "review").mkdir(exist_ok=True)
    (HERE / "review/index.html").write_text(page)

    fields = json.loads((HERE / "fields-r4-industrial.json").read_text())["lyrics"]
    rows = []
    for raw in fields.split("\n"):
        line = raw.strip()
        if line.startswith("["):
            rows.append(f'<tr class="t"><td colspan=2>{html.escape(line)}</td></tr>')
        elif line:
            rows.append(f'<tr><td class="en">{html.escape(line)}</td><td>{html.escape(gl.get(line, ""))}</td></tr>')
    (V4 / "lyrics/index.html").write_text(LYR.replace("__ROWS__", "".join(rows)))
    print(json.dumps({"lines": len(slim["lines"]), "words": nw, "check": len(chk)}))


if __name__ == "__main__":
    main()
