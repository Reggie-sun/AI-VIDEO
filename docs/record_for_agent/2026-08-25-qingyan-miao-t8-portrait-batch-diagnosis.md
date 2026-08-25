# Qingyan Miao T8 Portrait Batch Diagnosis Record

Date: 2026-08-25

> **2026-08-26 supersession notice:** 本记录的原批次、拒绝镜头与历史 final candidate 仍是
> 有效诊断 evidence，但不再是青颜广告的 current-facing delivery。新的严格串行重生成使用
> 5 条独立 T8 Turbo4 portrait outputs，每条在下一次 submit 前完成 exact-file post-media
> Gate，且以新的 28 秒成片替换当前交付；见
> `2026-08-26-qingyan-t8-regeneration-post-media-gate.md`。本 notice 不推翻旧 rejected
> attempts，也不把新 development candidate 升级为 P6 或 Final Acceptance。

## Purpose

本文记录 `qingyan-miao-ad-20260825` 的第二次、独立于前一条中断尝试的
Local MiniMax H3 T8 原生 portrait I2VA 批处理结果。目标是判断批处理是否真实
完成、哪些镜头可作为后续剪辑候选，以及为什么当前不能把终端里的“开始合成”当作
本批次的 28 秒成片事实。

本记录是 development media diagnosis，不是 Production Provider evidence、P6
判定或 Final Acceptance。

> **2026-08-25 later checkpoint:** 本记录最初写入时“没有新的 composition output”属实，
> 但已被同一 task 后续的 allow-list composition evidence supersede。当前存在新的 28 秒
> T8-dynamic media candidate；下方 `Composition Boundary` 保留的是诊断时点历史，当前事实见
> `Final Composition Follow-up`。

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

上述段落描述记录创建时的 exact checkpoint；它不再是本 task 的 current-facing final-output
状态。后续 composition 由独立脚本显式完成，而不是由 batch runner 隐式产生。

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

后续又执行一次新的、独立 output identity `03b_product_use_clean`，seed `8252208`。该 clip
technical completion通过，前48帧 flow-P90 median/max为`0.527/1.457`；但 sampled strip仍显示
画面右侧出现不属于主体的额外手，因此同样拒绝进入 composition。该次 local submit为1，
retry/fallback/remote为`0/0/0`。

粗粒度 192x336 下采样 motion statistics 仅作诊断辅助，不是质量阈值：
`03_product_use` 的 flow-P90 max 为 `3.976`（最大跃迁在 frame 26），而
`07_social回眸` 为 `0.688`、median 为 `0.333`。这些数字不能替代真人 1.0x
播放、产品真值或 P6 adjudication。

所有 7 条 MP4 都含 AAC；这只证明 Provider 输出容器含音轨，不证明该音轨已进入
P4 `ResolvedTimeline`、HyperFrames 或任何最终成片。`volumedetect` 的电平读数也
不能证明“可听见”或混音质量。

## Final Composition Follow-up

后续创建并执行：

```text
artifacts/qingyan-miao-ad-20260825/compose_t8_dynamic.sh
```

脚本使用显式 allow-list：

- `01_concern` frames `0..35`；
- `02_product_lift` frames `0..47`；
- `04_walk_forward` frames `0..41`；
- `05_walk_smile` frames `0..29`；
- `06_social_turn` frames `0..47`；
- 真实 `product-packshot.jpg`、golden-fluid graphic与既有source stills。

`03_product_use`、`03b_product_use_clean`和`07_social回眸`均未进入 composition。T8 portrait
canvas先中心裁成exact `756x1344`，再Lanczos scale到`1080x1920`；没有直接把`768x1344`
非exact画幅拉伸成9:16。商品可读镜头与end card继续消费用户source packshot真实pixels，
generated hand-held bottle不作为label fidelity证据。

最终 media candidate：

```text
artifacts/qingyan-miao-ad-20260825/final/青颜_苗家女孩T8动态广告_28s_9x16.mp4
```

- SHA-256 `26eebbb3f1cc6fc9cccb6d5bfddf60107b604c6ebfee3cbb13e508f73ed8cfcd`；
- `14,777,454` bytes；H.264 High、`1080x1920`、24 fps、672/672 decoded frames；
- video duration `28.000s`，container duration `28.022s`；
- AAC 48 kHz stereo，audio duration `28.000s`；mean/max volume `-21.5/-1.8 dB`；
- video full decode、audio full decode与written sidecar SHA check均通过；
- final contact sheet与keyframes确认真实黄色盒体/标签、白色瓶盖、现代苗家女孩、商业copy
  hierarchy与end-card composition存在；抽查两个局部motion peaks未见hard jump。

本次直接FFmpeg composition是development-side media candidate，不是canonical Production
Manifest/Registry/ResolvedTimeline/HyperFrames activation。T8 native AAC被丢弃，最终声音来自
显式BGM/SFX mix；这同样不升级为P4 Production evidence。

## Assessment

运行层面：**批处理及独立补镜头真实完成，且没有 retry/fallback/remote side effect。**

创意/媒体层面：**8条attempt中3条明确不合格（`03_product_use`、
`03b_product_use_clean`、`07_social回眸`）；最终allow-list composition已经存在。**
technical container verdict为PASS，sampled visual review没有发现入片镜头的额外肢体或hard jump；
这不等于human 1.0x、P6或Final Acceptance。

## Remaining Risks Or Next Work

Remaining risk是用户/人工1.0x整片播放、完整听感、Douyin UI实机safe-area、BGM/SFX商业授权，
以及平台审核/投放表现。当前没有旁白；“先喷青颜”由产品举起的使用暗示、紧随其后的真实packshot
与喷雾transition SFX表达，没有伪装成真实可见喷雾。若用户要求literal nozzle/mist action，必须先取得
无额外肢体且包装不漂移的新media evidence，不能恢复两个已拒绝clip。

## Agent Guardrails

- `status=completed`、56 frames、24 fps、one scene 或 unique-frame statistics 只证明
  容器/批处理事实，不证明动作流畅、产品 fidelity 或 Final Acceptance。
- 不把 `03_product_use` 的额外手臂解释成可接受的“动作创意”；不把 `07_social回眸`
  的近静止解释成已完成回眸动作。
- 不把旧 `compose.sh` 的 28 秒静态输出与本批次 `runtime/t8_portrait_ad` 混为同一
  composition lineage。
- 不把新的development FFmpeg candidate描述成Production HyperFrames render、P6或Final Acceptance。
- 不把 Provider native AAC 直接当作 P4 audio；最终 audio 仍归 canonical
  `ResolvedTimeline -> HyperFrames` 路径。
