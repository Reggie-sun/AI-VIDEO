# Qingyan V5 Dialogue Seam Continuity Repair Record

Date: 2026-08-26

## Purpose

本文记录青颜 30 秒竖屏广告在用户明确给出 v4 human `FAIL` 后的 bounded repair。三个 blocker 是：
没有推广对话、clone-frame seam/stutter 严重、跨镜头画面不连贯。本轮只新增一条本地 T8 native-audio
对白 Shot，并用已接受素材与 source packshot 重做 deterministic composition；没有 remote、paid、retry、
fallback、Production Manifest mutation、P6、Final Acceptance、push 或 release。

V4 的 exact artifact 与 human `FAIL` 保持历史有效；v5 仅替换 current local development delivery routing。
本记录的 requirement-level `PASS` 不能替代用户对 exact v5 MP4 的 uninterrupted 1.0x human acceptance。

## Repair Contract

authoring truth 与 compositor 位于：

```text
artifacts/qingyan-miao-ad-20260826-v5/ecommerce-input.json
artifacts/qingyan-miao-ad-20260826-v5/authoring-contract.md
artifacts/qingyan-miao-ad-20260826-v5/compose_t8_canvas_v5.sh
```

推广句固定为：

```text
出门前用青颜，抑汗净味，清爽舒适。
```

单一 `(S1)` 为 22 岁中国女性、普通话、画内本人。copy 不扩写医疗、量化、永久、全天或绝对功效。
T8/H3 直接使用 `768x1344` portrait canvas；Composition 再中央裁为 exact 9:16 并以 Lanczos 输出
`1080x1920`。这验证的是 current development runner 的动态 portrait input，不改变 shipped Production
profile 或 canonical Provider routing。

时间轴由 10 个 segment 的 `774` source/animated frames 与 9 个 `6-frame` dissolve 组成：
`774 - 54 = 720`。所有 live-action 只消费真实 source frames；脚本不含 `tpad`、clone、reverse loop
或 duplicated-frame extension。原 `01_concern` 开头 8 个静止帧被直接丢弃，时长转移到 animated
end card。两个独立户外动作之间插入 animated scenario card，明确重置空间，不再把不同脚步/尺度
硬拼成同一动作。

## Single Local T8 Dialogue Shot

唯一新提交为：

```text
artifacts/qingyan-miao-ad-20260826-v5/runtime/t8_portrait_ad/03_spoken_recommendation.mp4
SHA-256 43a3838e3d002567c58abbc0d0ee4647996d236600d0023e40e03fd7332b3b72
```

current runtime identity 与 graph facts：

- ComfyUI commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；
- T8 checkout commit `28cb160827c245b2d6a37539df30c1d7c5e7aecd`；
- direct T8 quality graph，无 LoRA/Turbo node；I2VA、`768x1344`、124 frames、24 fps、20 steps；
- sampler/scheduler 为 `res_multistep` / `simple`，native audio；seed `8262703`；
- exact submitted graph SHA-256
  `44231883b810cc9cd606ebd3c3dce47f67c6bb9d27cad0933e7d4def6d5a1756`；
- local submit count `1`，retry/fallback/remote count `0/0/0`；prompt id
  `83bd9a9d-8882-46b3-a341-25bb02c24728`；generation elapsed `392.345s`。

receipt 与逐 Shot Gate：

```text
artifacts/qingyan-miao-ad-20260826-v5/runtime/t8_portrait_ad/03_spoken_recommendation.receipt.json
artifacts/qingyan-miao-ad-20260826-v5/runtime/t8_portrait_ad/03_spoken_recommendation.gate.json
```

exact MP4 落盘后，在任何下一次 submit 前显式调用 project-local `video-analysis`。`video_probe` 实测
5.167 秒、`768x1344`、24 fps、124 frames、H.264 High 与 AAC stereo。dense contact sheet 显示同一
人物、稳定服饰/面部/两手、连续嘴部发声与产品举起动作；full video/audio decode 通过。逐 Shot
requirement-level verdict 为 `PASS`，之后没有再提交模型。由本轮启动的 owned ComfyUI unit 在 queue
清空后停止；最终无 `:8188` listener。

## Exact V5 Output

current local output：

```text
artifacts/qingyan-miao-ad-20260826-v5/final/青颜_苗家女孩T8对白修复广告_30s_9x16_v5.mp4
SHA-256 3e8f46318a273e410d7360cc19b8b5acd5cd081d146463ee2e182ee72dedbfe9
```

measured facts：

- file size `24,260,773` bytes；container duration `30.022s`；video duration `30.000s`；
- H.264 High、`1080x1920`、24 fps、720 frames、`yuv420p`；
- AAC 48 kHz stereo；integrated loudness `-22.7 LUFS`；true peak `-8.6 dBFS`；
- full video/audio decode `PASS`；`silencedetect=-42dB:d=0.35` 无 silence event；
- project `video_review` 抽取 30 frames，1437/1437 sampled frames unique，`issues: []`；
- project scene detector 在 threshold `0.08` 未识别 hard cut；九处 boundary contact sampling 显示
  dissolve 中间态，没有瞬时脚步/姿态硬拼；
- `freezedetect=-45dB:d=0.25` 在全部 live-action windows 中为 0 events。短静止检测只落在
  intentional scenario/product/end cards，最长 `0.458333s`，不是人物 clone padding。

Whisper medium 对最终成片检出 4.12–9.16 秒单一普通话句：

```text
出门前用清盐 意旱净味 清爽舒适
```

`青颜/清盐` 与 `抑汗/意旱` 是普通话同音字的 ASR orthography ambiguity；声学锚点、`净味`、
`清爽舒适` 与句序完整。画面在同一窗口烧录 exact correct caption
`出门前用青颜，抑汗净味，清爽舒适。`。因此这是可听推广句的 requirement-level `PASS`，但没有把
ASR 同音字误写伪装成 exact character transcription。

## Requirement-Level Gate

current evidence：

```text
artifacts/qingyan-miao-ad-20260826-v5/review/final/video-analysis-summary.json
artifacts/qingyan-miao-ad-20260826-v5/review/final/final-media-gate.json
artifacts/qingyan-miao-ad-20260826-v5/review/final/contact.jpg
artifacts/qingyan-miao-ad-20260826-v5/review/final/boundary-contact.jpg
```

`ad.audio.product_recommendation`、`ad.audio.voice_continuity`、
`ad.motion.required_windows`、`ad.edit.pacing`、character/spatial-temporal continuity、
packaging consistency、claim compliance 与 duration/aspect 均为 `PASS`。可读产品镜头继续使用 source
packshot SHA-256 `03d27bd46be48082b6d5ac737fbbb1f6cdca68b891d6c7d7c58eaa2c1c14f078`；generated
hand-held bottle 只承担 coarse identity。

这是绑定 exact local MP4 bytes 的 Agent requirement-level Gate。它没有运行或冒充 canonical
`Universal Gate 1 -> Ecommerce Gate 2 -> P6`，没有写 Manifest、激活 candidate 或产生
`PACKAGE_READY`。

## Assessment And Remaining Boundary

在 technical/Agent media proof layer，v4 的三个 blocker 已被具体替换：新增可听推广对白；删除约
5.67 秒 clone padding 并移除源开头静止帧；所有换景使用短 dissolve 或 explicit scene reset，人物动作
不再硬拼。current v5 status 为 `LOCAL_REQUIREMENT_GATE_PASS / HUMAN_ACCEPTANCE_PENDING`。

剩余边界：

- 用户仍需播放 exact SHA 的 MP4 做 uninterrupted 1.0x 主观验收；Agent 抽帧、ASR、freeze/scene metric
  与 MCP `issues: []` 均不能代替该 verdict；
- 尚未在真实 Douyin UI overlay 下做 device/account-specific safe-area preview；
- BGM/SFX 的商业投放 license provenance 未在 artifact 中闭合；
- 没有 literal nozzle/mist macro shot，人物手持继续只作产品 coarse identity；
- artifacts 全部 repository-untracked、local-only；没有 Production activation、push、release 或平台投放。

## Agent Guardrails

- 不得把 v5 requirement-level `PASS` 改写成用户 human `PASS`、P6 或 Final Acceptance。
- 不得用 generic `video_review issues: []` 单独覆盖对话、seam 或 continuity requirement；必须保留
  exact ASR、freeze window、boundary sampling 与 artifact identity。
- 不得把 product card 的 intentional low-motion interval 重新描述成 live-action clone padding，也不得
  把两者混为一个总“流畅度分数”。
- 不得把 source packshot 的 readable text truth 外推到 generated hand-held label。
- development FFmpeg composition 不是 canonical HyperFrames render，local ComfyUI submit 也不是
  Production Provider activation。
