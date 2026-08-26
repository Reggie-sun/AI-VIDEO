# Qingyan V9 Before-After And Later-Voice Repair Record

Date: 2026-08-26

## Purpose

本文记录用户对 exact v8 的下一轮 human `FAIL` 及 deterministic replacement。四个可观察缺陷为：
开场约一秒静止；所谓“产品表现”没有落实为同一腋下的使用前后对比；14 秒附近把 175-frame
出门镜头光流拉长到 270 frames，产生门框与人物形变；后段商业字幕没有对应声音。

本轮没有新的 T8 / ComfyUI submit、remote / paid Provider、fallback 或 retry。修复只消费已经通过
per-Shot Gate 的 v8 source bytes，输出新的 repository-untracked、local-only composition。

## Root Cause And Retired Paths

1. `F-PERFORMANCE / opening stillness`：accepted Shot 01 的前 25 frames为 low-motion setup；v8 从
   frame 0 开始。v9 永久裁除 source frames `0..24`，从可见喷雾/气流运动开始。
2. `F-CUT / missing comparison`：v8 只有生成 Shot中的颜色变化，没有 typed `before / after` comparison
   beat。v9 采用 `before-after-slider-scrub` 运动语法，使用同一年轻女孩、同一腋下构图的两个 accepted
   source states；不使用 packshot asset。
3. `F-CONTINUITY / optical retime`：v8 通过 `minterpolate + setpts` 将 Shot 03 从 175 frames拉到
   270 frames。v9 完全删除该路径，Shot 03 按 native 175 frames / 24fps播放。
4. `F-AUDIO-MIX / subtitle-only promotion`：v8 只在前段保留 H3 dialogue audio。v9 从 exact accepted
   Shot 02 bytes提取并清理已有三段 speech，在 comparison、benefit card与product hero显式编排；
   户外段删除无声推销字幕，保持无 speech。

## Exact Timeline And Output

authoring/compositor：

```text
artifacts/qingyan-miao-ad-20260826-v9/authoring-contract.md
artifacts/qingyan-miao-ad-20260826-v9/compose_v9.sh
```

timeline：

| Segment | Frames | Time | Current behavior |
| --- | ---: | --- | --- |
| underarm motion hook | 150 | `0.000-6.250s` | v8 Shot 01 frames 25-174；frame one已有可见 airflow movement |
| elder dialogue | 155 | `6.250-12.708s` | 三轮在镜对白与烧录字幕 |
| underarm before/after | 120 | `12.708-17.708s` | `使用前 汗湿闷热 / 使用后 清爽舒适`动态拉杆；无 packshot |
| leave together | 175 | `17.708-25.000s` | native timing；无 optical interpolation；无推销字幕 |
| benefit card | 60 | `25.000-27.500s` | 一次 fixed graphic；可听“清爽舒适，难怪这么自在” |
| product hero | 60 | `27.500-30.000s` | 一次 exact packshot；可听产品名与“清爽舒适” |

exact local candidate：

```text
artifacts/qingyan-miao-ad-20260826-v9/final/青颜_苗家腋下使用前后对比广告_30s_9x16_v9.mp4
SHA-256 f0014c5907b8426a6f453cc6373532a16596dfb25b145f3cc3fa23c000f75568
```

## Verification And Evidence

- SHA sidecar校验通过；H.264 High、`1080x1920`、24fps、720 frames；video/audio streams均
  `30.000s`，container `30.022s`；AAC 48kHz stereo。
- `freezedetect=n=0.002:d=0.35` 在 `0.000-12.708s` 无事件，证明 v8 opening freeze不在新 final中。
  comparison内部的短暂停顿是拉杆“快甩→阅读→慢扫”语法；不是 Shot seam或光流卡帧。
- 14.000s 位于 comparison reveal；native outdoor segment到 `17.708s` 才开始。compositor不包含
  `minterpolate`、`setpts` duration stretch、`xfade`或white flash。
- project-local `video_probe`绑定 exact final；`video_review` 返回 `issues: []`，1437 sampled frames
  unique ratio `0.999`。
- 对 exact subclips逐段运行 project-local Whisper medium：comparison=`清爽舒适`；outdoor为空；
  benefit=`清爽舒适 难怪这么自在`；product hero检出产品名同音字和`清爽舒适`。ASR可证明声序/覆盖，
  不能证明品牌 spelling 或 human voice quality。
- integrated loudness `-18.2 LUFS`，true peak `-1.7 dBFS`。
- Gate与review derivatives：
  `artifacts/qingyan-miao-ad-20260826-v9/review/final/final-gate.json`、
  `contact-1fps.jpg`、`comparison-4fps.jpg`、`boundaries.jpg`。

## Assessment And Remaining Boundary

current status 为 `TARGETED_AGENT_GATE_PASS / NEW_HUMAN_VERDICT_PENDING / LOCAL_CANDIDATE_ONLY`。
这只证明用户点名的四条旧 implementation path 已被替换并有 exact-media evidence；不代表
Ecommerce Gate 2、P6、Final Acceptance、publication、广告合规或市场表现。

使用前后素材来自同一 accepted Shot的不同时间点，人物与腋下状态一致，但不是受控临床或实验数据；
只能作为创意演示，不得扩张为定量功效证明。用户仍需 1.0x完整观看，判断 comparison wipe、重复一次的
brand closure voice、人物口型与整体节奏。若再次 human `FAIL`，必须继续 supersede exact v9，不得以
generic `video_review issues=[]`覆盖。

项目 Agent Memory初始 query返回 `[]`并排队 stale shard detached refresh；基于最终 v9 changed variables的
follow-up query也返回 `[]`。本轮没有前台 rebuild，Markdown record本身不会刷新 RAG。
