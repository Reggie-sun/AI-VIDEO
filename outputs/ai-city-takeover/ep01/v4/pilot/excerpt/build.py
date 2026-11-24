#!/usr/bin/env python3
"""Checkpoint 5 (part 2): the 26–59 s excerpt (Verse 1 + Chorus 1) on the method the user chose (Seedance 2.0 VIP, 4k).

  python3 -I outputs/ai-city-takeover/ep01/v4/pilot/excerpt/build.py

Writes preview-inputs.json and index.html. SG03 is already made (the method take). s009 is a 2.5D plate (no clip).
Rules carried from earlier takes: camera locked in every generated take (camera moves are done in the edit), no
exact timestamps, no "红" in prompts, sung/spoken windows use image + the clip's exact vocal window.
"""
import hashlib, html, json
from pathlib import Path

H = Path(__file__).resolve().parent
REPO = H.parents[5]
V4 = H.parents[1]
sha = lambda p: hashlib.sha256((REPO / p).read_bytes()).hexdigest()
board = json.loads((V4 / "board/shots.json").read_text())
clips = {c.get("clip") or c.get("id"): c for c in board["clips"]}
shots = {s["id"]: s for s in board["shots"]}
P = {
 "MO04": ("s007", "first_frame", "镜头固定，全身远景。夜里潮湿的人行道，她站在树下，伸手把一根挡在面前的树枝往下拽，眯眼往上看树后那块发着白光的巨大广告牌；"
          "她松开手，树枝弹回去轻轻晃动，广告牌的白光整片打到她脸上，她不躲，从外套口袋里掏出一张空白的姓名贴。路灯和远处的车灯安静地亮着。"),
 "SG02": ("s008", "multimodal", "{{image:0}}中的她对着镜头平平地说话，口型与{{audio:1}}里的人声逐字精确同步。近景，她用拇指把胸口那张空白姓名贴按平，"
          "神情冷淡；说完最后几个字，她转身往画面右边迈出半步。镜头全程锁定，一镜到底。"),
 "MO05": ("s010", "first_frame", "镜头固定，长焦侧拍。夜里，她双臂搭在天桥的铁丝网护栏上，往下看高速公路上流过的车灯；她抬脚踹了一下护栏，整片铁丝网震动起来；"
          "然后她两手插进裤兜，转身沿着天桥往远处走，外套下摆还在晃。远处城市的灯安静地亮着。"),
 "MO06": ("s011", "first_frame", "长焦正面，全身远景，镜头固定。地下停车场改成的秀场，她从走秀台远端快步走向镜头，步子很大，面无表情，外套肩线一颠一颠；"
          "两边前排工程师们一个接一个站起来；她走到走秀台中段。头顶一排排日光灯管亮着，湿的水泥地面反着光。"),
 "SG04": ("s013", "multimodal", "{{image:0}}中的她低头看着手里亮着的手机，对着值班工程师唱歌，口型与{{audio:1}}里的人声逐字精确同步。近景，她唱到一半把手机扔回他怀里，"
          "手机始终在她胸口以下，不挡住嘴；唱最后两个字时她转过身去。镜头全程锁定，一镜到底。"),
 "MO07": ("s014", "first_frame", "长焦，镜头固定。秀场走秀台的尽头，她一个急转身，外套下摆甩开成一个圆；转完她头也不回地用一只手按住腰间正在震动的寻呼机，"
          "朝画面右侧的侧门走去。两边观众举着手机拍她，手机屏幕的光点点亮着。"),
}
NOTES = {
 "MO06": "分镜写“重音上全场日光灯一排排亮起”，但首帧里灯已亮着，首帧生视频做不出“亮起”：亮灯放到剪辑里做（曝光从暗拉亮，卡 40.786 s 重音）。",
 "SG04": "首帧里手机已经在她手里（分镜的“从他手里抽走手机”由上一镜的切点省略）；手机写明不挡嘴。",
 "SG02": "念白口型窗：她对镜头平平地说 A I: Average Individual. That's me. Bus stop:；首帧里姓名贴已经贴在胸口，动作改为按平。",
}
units, total_s = [], 0
for cid, (sid, mode, prompt) in P.items():
    c, s = clips[cid], shots[sid]
    secs = -(-c["seconds"] // 1) if isinstance(c["seconds"], int) else int(-(-c["seconds"] // 1))
    plate = f"outputs/ai-city-takeover/ep01/v4/board/plates/{c['start_frame']}.png"
    u = {"clip": cid, "shot": sid, "mode": mode, "seconds": secs, "window": [c["window"]["t0"], c["window"]["t1"]],
         "words": c.get("words"), "plate": {"path": plate, "sha256": sha(plate)}, "prompt": prompt,
         "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "board_action": s["action"], "board_camera": s["camera"],
         "note": NOTES.get(cid)}
    if mode == "multimodal":
        u["audio"] = {"path": f"outputs/ai-city-takeover/ep01/v4/pilot/audio/{cid}.wav"}
    units.append(u); total_s += secs
inputs = {"schema": "iris-v4-preview-inputs/excerpt-1", "range_s": [26.0528, 59.2341], "method": "Seedance 2.0 VIP 4k (user: 不拍 A 了，就用 Seedance)",
          "already_made": {"SG03": "pilot/sd-SG03 (fee974f0…)"}, "plate3d": ["s009"], "units": units,
          "budget": {"generations": len(units), "retries": 0, "price_reference": "SG03: 6 s 4k = 480 CRD (80/s)",
                     "estimate_CRD": total_s * 80, "ceiling_per_unit_CRD": 800, "cumulative_CRD": 4000}}
(H / "preview-inputs.json").write_text(json.dumps(inputs, ensure_ascii=False, indent=1) + "\n")
e = html.escape
cards = "".join(f"""<div class="card"><img src="../../board/plates/{Path(u['plate']['path']).name}"><div>
<h3>{u['clip']} · {u['shot']} · {fmt}</h3><p class="w">{e(' '.join(u['words'] or []))}</p>
<p class="pr">{e(u['prompt'])}</p>{f'<p class="n">{e(u["note"])}</p>' if u['note'] else ''}<p class="d">分镜动作：{e(u['board_action'])}</p></div></div>"""
                for u in units for fmt in [f"{'唱/念口型' if u['mode']=='multimodal' else '动作'} · {u['seconds']} s · {u['window'][0]:.2f}–{u['window'][1]:.2f}"])
(H / "index.html").write_text(f"""<!doctype html><meta charset="utf-8"><title>检查点 5 · 样片 26–59 s</title>
<style>body{{background:#0b0d12;color:#dfe6ee;font:15px/1.7 system-ui,sans-serif;margin:24px auto;max-width:1300px;padding:0 24px}}
.card{{display:flex;gap:16px;border-bottom:1px solid #1b2230;padding:14px 0}}.card img{{width:420px;flex:0 0 420px}}h3{{margin:0;font-size:16px;color:#f3d9a8}}
.w{{color:#9fb4c7}}.pr{{background:#11151c;padding:8px 12px;border-radius:6px}}.n{{color:#ff8a3d}}.d{{color:#7f8b97;font-size:13px}}</style>
<h1>检查点 5 · 样片：主歌 1 + 副歌 1（26–59 s）</h1>
<p>方法用你选的 Seedance 2.0 VIP 4k。SG03 已经拍好；s009 是 2.5D 底片，不生成。下面 6 条要生成，每条一次、不重试。
费用估算：共 {total_s} 秒 × 约 80 积分/秒 ≈ {total_s*80} 积分（参考 SG03 6 秒 480）。每条上限 800，合计上限 4000。
每条出片后先过逐镜 Gate；全部出完我按分镜把这 33 秒剪成样片，配上歌词字和图形给你看。</p>
{cards}""")
print(total_s, total_s * 80)
