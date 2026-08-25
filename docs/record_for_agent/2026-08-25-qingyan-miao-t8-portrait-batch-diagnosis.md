# Qingyan Miao T8 Portrait Batch Diagnosis Record

Date: 2026-08-25

## Purpose

本文记录 `qingyan-miao-ad-20260825` 的第二次、独立于前一条中断尝试的
Local MiniMax H3 T8 原生 portrait I2VA 批处理结果。目标是判断批处理是否真实
完成、哪些镜头可作为后续剪辑候选，以及为什么当前不能把终端里的“开始合成”当作
本批次的 28 秒成片事实。

本记录是 development media diagnosis，不是 Production Provider evidence、P6
判定或 Final Acceptance。

## Current Runtime Truth

批处理脚本为
`artifacts/qingyan-miao-ad-20260825/runtime/execute_t8_portrait_ad_batch.py`。
它只执行 7 次串行的 loopback `ComfyClient` submit/poll/fetch，并在每个 clip
旁写入 `.receipt.json` 与 `.state.json`；脚本在第 7 个 receipt 写完后结束，不包含
48-frame 裁剪、concat、28 秒 composition 或 final delivery writer。

2026-08-25 19:50:37–19:54:53 之间，7 条均已完成并闭合：

- 每条 `status=completed`，且 MP4、receipt、state 三者都存在；
- 每条 `local_submit_count=1`、`retry_count=0`、`fallback_count=0`、
  `remote_submit_count=0`；
- 每条为 `768x1344`、56 frames、24 fps、约 2.334 s、H.264 + AAC 32 kHz stereo；
- ComfyUI commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；T8 checkout
  commit `28cb160827c245b2d6a37539df30c1d7c5e7aecd`；
- 复核时 `http://127.0.0.1:8188/queue` 的 running/pending 均为空。

MP4 与 receipt 的路径均在：
`artifacts/qingyan-miao-ad-20260825/runtime/t8_portrait_ad/`。

## Composition Boundary

当前目录没有新的裁剪、concat 或 composition output。现有
`artifacts/qingyan-miao-ad-20260825/final/` 下的两条 28 秒 MP4 在 18:38:07
已落盘，且 `compose.sh` 明确读取 `assets/*.png`、生成 `work/01-hook.mp4` …
`work/08-close.mp4`；它们是更早的静态 picture-track composition，不消费
`runtime/t8_portrait_ad/*.mp4`。因此终端里“完成后立即统一裁到 48 帧并开始 28 秒合成”
不是当前批处理脚本已经产生的 runtime evidence。

## Media Review

对现有 review strips、7 条 MP4 的 frame samples 和 project-local
`video-analysis` 结果进行检查后，得到以下 development-side 分层结论：

| Shot | 观察 | 后续 disposition |
| --- | --- | --- |
| `01_concern` | 手部从腋侧检查到放下的动作可见，人物/背景整体稳定；未见足以直接淘汰的明显解剖伪影。 | 候选，需正常速度人工复核 |
| `02_product_lift` | 黄色瓶体被举到胸前，动作语义基本兑现；瓶体与手指仍需逐帧检查。 | 候选，需产品 fidelity 复核 |
| `03_product_use` | 中段开始从画面两侧出现不属于主体的多只手/手臂，违反“不增加人物/手指”的 prompt 约束。 | **拒绝进入 composition** |
| `04_walk_forward` | 有向前行走与双脚交替的可见进展，但不能仅凭 strip 判定脚步连续或无 foot skating。 | 候选，需 1.0x 人工复核 |
| `05_walk_smile` | 行走与朝镜头微笑的语义较清楚；仍未完成 full-speed human acceptance。 | 候选，需正常速度人工复核 |
| `06_social_turn` | 三人和场景大体稳定，转向幅度偏轻；未证明社交回应的完整时序。 | 候选，需正常速度人工复核 |
| `07_social回眸` | 画面几乎保持静止，没有清楚兑现“迈步后回眸”；粗采样光流也为 7 条中最低。 | **拒绝进入 composition** |

粗粒度 192x336 下采样 motion statistics 仅作诊断辅助，不是质量阈值：
`03_product_use` 的 flow-P90 max 为 `3.976`（最大跃迁在 frame 26），而
`07_social回眸` 为 `0.688`、median 为 `0.333`。这些数字不能替代真人 1.0x
播放、产品真值或 P6 adjudication。

所有 7 条 MP4 都含 AAC；这只证明 Provider 输出容器含音轨，不证明该音轨已进入
P4 `ResolvedTimeline`、HyperFrames 或任何最终成片。`volumedetect` 的电平读数也
不能证明“可听见”或混音质量。

## Assessment

运行层面：**批处理真实完成，且没有 retry/fallback/remote side effect。**

创意/媒体层面：**7 条中至少 2 条明确不合格（`03_product_use`、
`07_social回眸`），其余 5 条只是候选，不能直接拼成 28 秒广告。** 当前没有新的
portrait composition output；旧的 28 秒 final 不能冒充本批次成片。

## Remaining Risks Or Next Work

下一步应先对 5 条候选做正常速度人工播放，逐条确认身份、产品形状、脚步连续性、
社交回应和 audible playback；在这一步之前，不应重新批量换 seed，也不应把失败镜头
用时间重映射或静态帧隐藏。若要 composition，必须建立明确的 input allow-list，只消费
人工接受的候选，并为新 composition 生成独立 receipt；不得复用旧 `final/` receipt
或将 development clip 激活为 Production candidate。

## Agent Guardrails

- `status=completed`、56 frames、24 fps、one scene 或 unique-frame statistics 只证明
  容器/批处理事实，不证明动作流畅、产品 fidelity 或 Final Acceptance。
- 不把 `03_product_use` 的额外手臂解释成可接受的“动作创意”；不把 `07_social回眸`
  的近静止解释成已完成回眸动作。
- 不把旧 `compose.sh` 的 28 秒静态输出与本批次 `runtime/t8_portrait_ad` 混为同一
  composition lineage。
- 不把 Provider native AAC 直接当作 P4 audio；最终 audio 仍归 canonical
  `ResolvedTimeline -> HyperFrames` 路径。
