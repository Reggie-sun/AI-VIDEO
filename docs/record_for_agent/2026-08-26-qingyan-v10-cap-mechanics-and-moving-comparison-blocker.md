# Qingyan V10 Cap Mechanics And Moving Comparison Blocker Record

Date: 2026-08-26

## Purpose

本文记录 exact v9 的新一轮 human `FAIL`、v10 opening replacement 的已完成本地生成，以及
`video-analysis` MCP 不可用后触发的 fail-closed checkpoint。用户点名的四个缺陷为：开头人物表情
不对；大盖未打开就喷；喷前没有先表现腋下困扰；约 13 秒开始的静态使用前后 Shot 僵硬且不连贯。

本 checkpoint 不是完成的 30 秒 v10 candidate。只有 opening Shot 01A 已生成；后续 re-cap / elder
entrance Shot、deterministic composition、voice timeline 与 final MP4 均未执行。

## Replacement Contract

v10 删除独立的 5 秒静态 before/after slider。`使用前 / 使用后`应由同一连续 opening action 表达：

1. 女主先皱眉并触碰被衣物覆盖的腋下区域，建立汗湿不适；
2. 瓶子保持单一且大盖清楚可见；
3. 女主完整拔下同一个大盖，并把它放到右下桌面；
4. 只有小喷头完全露出后才允许喷雾；
5. 喷后由不适表情转为放松，暖黄色不适 haze 转为淡蓝白清爽空气；
6. 下一连续 Shot 才负责停止喷洒、拿回同一个盖子、重新盖好并让老人自然入场；
7. 13 秒附近应落在真实双人 dialogue movement，不再落入静态 comparison。

对应 H3/T8 prompts：

```text
artifacts/qingyan-miao-ad-20260826-v10/prompts/01a_problem_open_cap_spray.txt
artifacts/qingyan-miao-ad-20260826-v10/prompts/01b_recap_elder_enters.txt
```

## Exact Inputs And Local Submit

两张首尾控制图通过 built-in `imagegen` 生成并绑定到项目 artifact：

| Role | Path | SHA-256 |
| --- | --- | --- |
| problem / cap-on first frame | `artifacts/qingyan-miao-ad-20260826-v10/assets/01-problem-reaction-cap-on.png` | `3525bc8bc4c20e87626536f9e32e9056a05e35b0d7856e0f3575a500bd9a94d6` |
| relief / cap-off last frame | `artifacts/qingyan-miao-ad-20260826-v10/assets/01-relief-spray-cap-off.png` | `7b564604ddf17ad6705ef597e63417fbbf2af08ce9dca49d5b3ec56a69f79522` |

Shot 01A 使用本机 H3/T8 `FL2VA` 单次生成：ComfyUI
`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`、T8
`28cb160827c245b2d6a37539df30c1d7c5e7aecd`、`768x1344`、175 frames、24fps、20 steps、
`res_multistep` + `simple`、无 LoRA。没有 retry、fallback 或 remote Provider submit。

exact output：

```text
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/01_problem_open_cap_spray.mp4
SHA-256 d33a0a8fd1c1dd3a56183886dc554cacdd8452b5cb6e2fdb3ac4522f387e536e
3,551,638 bytes; 768x1344; 24fps; 175 frames; 7.292s; audio stream present
```

生成 receipt 与 exact submitted graph：

```text
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/01_problem_open_cap_spray.receipt.json
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/01_problem_open_cap_spray.submitted-workflow.json
```

## Post-Media Gate Blocker

exact MP4 落盘后，Agent 在提交 Shot 01B 前显式调用 project-local `video-analysis` MCP：

- `video_analyze`：`Transport closed`；
- 轻量 `video_probe` 连通复核：`Transport closed`。

因此所有 required findings 均为 `NOT_EVALUATED`，不是 `PASS` 或内容 `FAIL`。阻断 receipt：

```text
artifacts/qingyan-miao-ad-20260826-v10/runtime/t8_portrait_ad/01_problem_open_cap_spray.gate.json
```

本地 2fps contact sheet 只作为 advisory diagnosis：可见人物先检查腋下衣料、拔下白色大盖、将单一
盖子放到桌上、露出喷头后才喷，并从顾虑表情转为微笑；没有右下角产品 thumbnail。该观察不能替代
required MCP evidence，也不能将 Gate 改判为 `PASS`。

Gate 失败关闭后没有提交 Shot 01B。ComfyUI 已通过 supervisor 停止，并验证 loopback listener 不再响应。

## Current Assessment And Next Work

current status：

```text
OPENING_SOURCE_GENERATED / POST_MEDIA_NOT_EVALUATED /
NEXT_SHOT_BLOCKED / NO_V10_FINAL / HUMAN_VERDICT_PENDING
```

恢复条件不是 blind retry H3，而是先恢复 project-local `video-analysis` MCP；随后必须对上述 exact MP4
和 exact SHA 重新完成 requirement-level Gate。只有全部 required findings 为 `PASS`，才允许单次提交
`01b_recap_elder_enters`，然后再次逐 Shot Gate。通过后才可制作新的 720-frame / 30 秒 composition，
并把 13 秒落在有真实身体与表情运动的 elder dialogue，而非静态 before/after card。

项目 Agent Memory 初始 symptom query 返回 `[]`并排队 detached refresh；基于最终 blocker 的 focused
follow-up query命中既有 post-media Gate经验记录，确认 `MCP unavailable -> NOT_EVALUATED -> stop`
边界。本记录本身不会刷新 RAG index。

## Agent Guardrails

- 不得把 contact sheet、FFmpeg metadata、successful local submit 或 H3 receipt当作 per-Shot Gate `PASS`。
- 不得在 exact Shot 01A 未完成 Gate 前提交 Shot 01B、合成 v10 final 或宣称 13 秒问题已在成片修复。
- 不得覆盖或 blind retry exact `01_problem_open_cap_spray` durable state；若内容后来被判为 `FAIL`，必须
  以新 Shot identity和新的 exact receipt处理。
- v9 技术 measurements保留为历史 evidence，但其 human verdict 已是 `FAIL`。
- repository artifacts保持 local-only、untracked；本记录不声明 Production activation、P6、Final
  Acceptance、publication、平台审核或投放效果。
