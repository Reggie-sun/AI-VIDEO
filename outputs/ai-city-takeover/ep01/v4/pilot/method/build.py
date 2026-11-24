#!/usr/bin/env python3
"""Checkpoint 5 · method test on one shot (SG03): preview inputs + page.

  python3 -I outputs/ai-city-takeover/ep01/v4/pilot/method/build.py

Writes preview-inputs.json (exact plate, vocal window, both prompts, with sha256) and index.html for the user.
Two lanes on the same plate and vocal: Jimeng digital human (OmniHuman 1.5, master mode) and Seedance 2.0 VIP
multimodal lip-sync (one image + one vocal reference). Nothing is submitted by this script.
"""
import hashlib, html, json
from pathlib import Path

H = Path(__file__).resolve().parent
REPO = H.parents[5]
V4 = H.parents[1]
sha = lambda p: hashlib.sha256((REPO / p).read_bytes()).hexdigest()
PLATE = "outputs/ai-city-takeover/ep01/v4/board/plates/p012.png"
AUDIO = "outputs/ai-city-takeover/ep01/v4/pilot/audio/SG03.wav"
OH = ("镜头固定中景。她弯腰凑在坐着的值班工程师脸前，一只手撑在他的椅背上。开头她嘴唇轻轻合上，静静看着他；"
      "唱第一个字时张开嘴，冷静而投入地对着他唱，嘴随歌词自然张合，神情平静，眉头舒展；唱完最后一个字，她慢慢直起身。"
      "他抱着笔记本电脑往后缩，攥着椅子扶手。")
SD = ("{{image:0}}中的她弯腰凑在坐着的值班工程师脸前，一只手撑在他的椅背上，对着他唱歌，口型与{{audio:1}}里的人声逐字精确同步。"
      "中景，开头她嘴唇轻轻合上，静静看着他；唱第一个字时张开嘴，冷静而投入地唱，神情平静；唱完最后一个字，她慢慢直起身，"
      "他还攥着椅子扶手。他抱着笔记本电脑往后缩。镜头全程锁定，一镜到底。")
win = json.loads((V4 / "pilot/audio/windows.json").read_text())
inputs = {
    "schema": "iris-v4-preview-inputs/method-1", "unit": "SG03", "shot": "s012",
    "lyric": "hold on tight / I'm the reason you're awake",
    "image": {"path": PLATE, "sha256": sha(PLATE), "note": "closed-mouth start (0.68 s silence before 'hold')"},
    "audio": {"path": AUDIO, "sha256": sha(AUDIO), "seconds": 5.99, "song_window": [44.9422, 50.933]},
    "board": {"path": "outputs/ai-city-takeover/ep01/v4/board/shots.json", "sha256": sha("outputs/ai-city-takeover/ep01/v4/board/shots.json")},
    "digital_human": {"mode": "即梦 数字人 · 大师模式（OmniHuman 1.5）", "action_prompt": OH,
                      "action_prompt_sha256": hashlib.sha256(OH.encode()).hexdigest()},
    "seedance_multimodal": {"model": "seedance_2.0_vip", "mode": "multimodal", "seconds": 6, "resolution": "1080p",
                            "prompt": SD, "prompt_sha256": hashlib.sha256(SD.encode()).hexdigest()},
    "technical_differences_from_board": [
        "board camera '锁定中景，48.17 小节线上 4% 推近' → generated take locked; the 4% push is done in the edit (v3: 4 of 5 Seedance takes with camera moves failed)",
        "plate p012 changed from open mouth to closed-mouth start (v3 r3b gate FAIL: open mouth frozen through silence)",
        "no exact timestamps in prompts (Seedance 2.0 does not reliably follow precise timing); relative order only"],
    "budget": {"generations": 2, "retries": 0, "ceiling_per_take_CRD": {"digital_human": 165, "seedance_multimodal": 200},
               "cumulative_CRD": 365, "observed_reference": "v3 digital human 4.37 s take cost 24 CRD"},
    "accept": ["正常速度和原曲合在一起看，她在唱，口型逐字大致同步，无声处嘴合着",
               "脸是 F1-a，耳挂与立领红线在画面右侧且一直亮着",
               "神情平静、不喊、不发空，从头到尾同一种情绪",
               "动作：凑近唱 → 唱完慢慢直起身；他往后缩",
               "没有凭空出现的手或物体、没有牙齿碎裂、背景与机位稳定"],
}
(H / "preview-inputs.json").write_text(json.dumps(inputs, ensure_ascii=False, indent=1) + "\n")
e = html.escape
(H / "index.html").write_text(f"""<!doctype html><meta charset="utf-8"><title>检查点 5 · 一个镜头上找方法（SG03）</title>
<style>body{{background:#0b0d12;color:#dfe6ee;font:15px/1.7 system-ui,sans-serif;margin:24px auto;max-width:1200px;padding:0 24px}}
img{{width:100%}}.box{{background:#11151c;padding:12px 16px;border-radius:6px;margin:10px 0}}code{{color:#f3d9a8}}h2{{font-size:18px;margin-top:26px}}</style>
<h1>检查点 5 · 花钱前：先在一个镜头上找到唱歌的方法</h1>
<p>镜头 s012（副歌 1，44.94–50.93 s）：她凑到值班工程师脸前唱 <b>hold on tight / I'm the reason you're awake</b>。
同一张首帧、同一段人声，两条生成路线各拍一条，你看哪条唱得像真的，样片就用哪条方法。</p>
<h2>首帧（嘴先合着：这段人声开头有 0.68 s 空白）</h2><img src="../../board/plates/p012.png">
<h2>人声（只有她的声音，从分轨切出）与原曲同一段</h2>
<div class="box">人声：<audio controls src="../audio/SG03.wav"></audio>　原曲：<audio controls src="SG03-mix.m4a"></audio></div>
<h2>A · 即梦数字人（大师模式）动作描述</h2><div class="box">{e(OH)}</div>
<h2>B · Seedance 2.0 全能参考（一张图＋一段人声）提示词</h2><div class="box">{e(SD).replace('{{','<code>{{').replace('}}','}}</code>')}</div>
<h2>和分镜不同的地方（技术原因）</h2><ul>{''.join(f'<li>{e(x)}</li>' for x in inputs['technical_differences_from_board'])}</ul>
<h2>费用</h2><div class="box">两条各一次，不重试。上限：数字人每条 165 积分，Seedance 每条 200 积分，合计不超过 365。参考：v3 数字人一条 4.4 秒花了 24 积分。实际花费出片后如实报。</div>
<h2>出片后我先查（逐镜 Gate），再给你看</h2><ul>{''.join(f'<li>{e(x)}</li>' for x in inputs['accept'])}</ul>
<p>好不好看、像不像在唱，由你判。选定方法后，再按同样方式给你看样片其余 6 个片段（26–59 s）的 prompt 和费用。</p>
""")
print(inputs["image"]["sha256"], inputs["audio"]["sha256"])
