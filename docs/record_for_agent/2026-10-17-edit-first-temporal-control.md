---
record_kind: architecture_implementation
topic_id: edit-first-temporal-control
learning_eligibility: ineligible
---

# Edit-First Temporal Control Record

Date: 2026-10-17

## Purpose

记录通用制作路径中“先评估既有素材能否经剪辑满足目标，再决定是否生成”的实现与当前本地证据。目标是把可编辑的时间偏差交给既有 Production planning 和唯一 `ResolvedTimeline`，避免把编辑问题直接送回 Provider。

本记录对应 [spec](../superpowers/specs/2026-10-17-edit-first-temporal-control.md)、[plan](../superpowers/plans/2026-10-17-edit-first-temporal-control.md) 与 [workflow owner](../canvas-production-harness.md#edit-first-temporal-control)。Spec/Plan 说明完整契约；本文只固定本次实现与开发预览的实证边界。

## Implemented Direction

默认 `production-strategy/2` 在 qualified reuse 下优先评估生成次数更少、仅缺用途证据的源候选；显式 `/1` 保留原兼容语义。`video-time-map/1` 使用相对源 trim 的递增整数帧锚点，`CompositionSpec/ResolvedTimeline 2.3` 独占 source trim、output frame/sample 与分段解析。非一比一段按每个输出帧的 floor source coordinate 展开为一帧 source span，由既有 HyperFrames 0.7.103 逐段读取 1x 窗口；实现不依赖该导出忽略的 `data-playback-rate`，也未增加 renderer、timeline、状态库或依赖。

首个运行边界为同帧率、显式静音的视觉剪辑。现有源音频、同 Shot/全局音轨与字幕、同 Shot voice source 没有可用的对应 sample map 时必须明确拒绝；独立其他 Shot 音频与最终验收仍由原 P4/QA owner 管理。减速重复采样源帧，不做光流补帧。用途证据绑定 exact map 和源身份；未变速的 PASS 不沿用为变速用途 PASS。已失败素材只经原 `bootstrap_repair_input` 路径进入 `development_preview`，资产保持 UNBOUND、qualification 为 NOT_EVALUATED，不能 activation；不改变原失败、rejection、STOP 或源 Production lifecycle。

现有普通 qualified 视频也由同一上层策略评估是否剪辑或变速；没有故事专属分支。完整字段、失败路径与 authoring 限制见 workflow、spec 和 plan。

## Retained Source And Preview

本地预览使用既有几何人物 R2V 源 MP4 `0a7e9072f5bbce23f78ead55dc6ebefb477ded1d6e9518cb6a42ce19f5049bc9`，attempt `canvas-50d9e7ad76b42064d3c5a34647c05feacd271dda`。源生成结果原 QA 保持 **0 PASS / 2 FAIL / 5 NOT_EVALUATED**，候选已 abandon。早先唯一获准的 robot Provider pilot 已消费 1 次；此次编辑新增 Provider POST 为 0，不能把整个窗口描述为零调用。

`runs/edit-first-temporal-control-20261017-001/robot-retimed-preview/render-002/verified.mp4` 的 SHA-256 为 `8ca3e974b686711a970698f802a0f40dc2a564f3fe72d0a5db824719de15962b`。输出为 1344×768（7:4）、24fps、120 帧 / 5 秒、H.264、无音轨。使用的映射为 `(0,0) → (66,48) → (96,84) → (120,120)`，`audio_policy=mute`。原 robot Manifest SHA-256 `f46f55ea6779a6222ade1670a74aef6a06d1e17b4bd5b0583134d23ce6f6a36e` 与《界蚀》原始 Manifest SHA-256 `1ece69263041eb06d345e5673f010a2b209e67a1e2fea82c2002e12a2b982e60` 均保持不变；预览记录确认 `original_state_unchanged=true`。

| Proof layer | Evidence | Result and limit |
| --- | --- | --- |
| Renderer frame identity | `runs/edit-first-temporal-control-20261017-001/renderer-fixture/sampled-011/frame-identity-comparison.json` | 11 个选定输出帧均匹配预期 source frame；测试覆盖 2x、0.5x 与 1x 分段。证明该 pinned renderer 实际消费正确源帧，不证明画面质量。 |
| Historical renderer counterexample | `runs/edit-first-temporal-control-20261017-001/renderer-fixture/run-007/frame-identity-comparison-posthoc.json` | 旧 `data-playback-rate` 属性路径发生帧错配，`all_expected_frames_match=false`；保留为负面 proof，不用后续结果覆盖。 |
| Edited media observation | `runs/edit-first-temporal-control-20261017-001/robot-retimed-preview/observations.json` | project-local `video-analysis` MCP 加 Agent 抽查：2.0s 样帧手臂垂下、3.5s 样帧左臂水平，两项仅对编辑后的离散时点为 PASS。 |
| Other media requirements | 同上 | 转身幅度与整段动作自然度、原音频保留、Production qualification、人工完整 1x 观看均为 NOT_EVALUATED。此 preview 不构成完整 QA 或交付。 |

原源的失败 required findings、rejection、消费和 STOP 均未改写。编辑预览不是新生成实验，也不与其源素材构成独立样本。

## Engineering Verification Status

已发布源码为 `43b58d62e55fbcba8021002667f3042be584a6c2`，tree `138cb4ec4af83a61486edb1c2eec01d3c5f21583`，remote main SHA 已核验一致。此前实现提交 `1b55a25783ca9cb7831e504cb912605bf122fbd1`，whitespace 修复 `1c04a57fa8b70cb8b53f9214290bc79a46e779fb`，旧格式 trim 兼容修复 `84706114beb93fa4ea3cfcd0917755438106ac54`；工程 Harness 与必需复审已完成，媒体质量和人工验收不由源码发布代替。

| Scope | Receipt and proof | Result |
| --- | --- | --- |
| `3da65f0..1c04a57` | `.agent/harness/runs/edit-first-temporal-control-20261017-r2/receipt.json`；`runs/edit-first-temporal-control-20261017-001/harness-r2-source-verification.json` | 22 selected，21 PASS / 1 covered SKIP，无 fallback；Architecture 0 findings，Production contract 4101 PASS / 4 SKIP、Canvas workflow 278 PASS；integrity/freshness/complete_completion_proof 在 exact `1c04a57` 快照核验通过。 |
| `1c04a57..8470611` | `.agent/harness/runs/edit-first-temporal-control-20261017-r3/receipt.json`；`runs/edit-first-temporal-control-20261017-001/harness-r3-source-verification.json` | 7/7 PASS；composition/audio 1024 PASS / 4 SKIP；Architecture 0 findings，integrity/freshness/complete_completion_proof 在 exact `8470611` 核验通过。 |
| `8470611..43b58d6` | `.agent/harness/runs/edit-first-temporal-control-20261017-r4/receipt.json`；`runs/edit-first-temporal-control-20261017-001/harness-r4-source-verification.json` | 14/14 PASS，无 fallback；Architecture 0 findings；generation feedback 523 PASS / 1 SKIP、voice routing 47 PASS、strategy 75 PASS、Shot router 372 PASS、composition/audio 1026 PASS / 4 SKIP、Canvas workflow 290 PASS；integrity/freshness/complete_completion_proof 在 exact `43b58d6` 核验通过。 |
| Actual pinned export | `runs/edit-first-temporal-control-20261017-001/renderer-fixture/sampled-011/`；`tests/test_production_video_retime_render.py` opt-in | 1 PASS；11/11 真实输出帧匹配，namespace 仅 `lo`。普通 Harness 跳过此 opt-in，不将默认 SKIP 当作实际执行。 |

Harness r1 仅因新测试文件末尾额外空行失败，失败 receipt 保留。增量只修复旧 `ResolvedVisualSpan.trim_duration_frames=None` 被误拒绝的问题；新增边界测试修复前 1 失败 / 2 通过，修复后 retime/Canvas 相关 25 项通过。实际 renderer 及 robot 预览使用显式整数 trim，后续兼容修复不改变这些 span 的行为；4101 项完整契约证明属于 `1c04a57`，不冒称全部在新候选重复执行。

Risk Gate 为 `NATIVE_REVIEW_REQUIRED`：已失败媒体可经 sealed capture 进入 composition，跨 Registry、exact target/use 与 activation 的 join/alias 若缺保护，可能把已知失败提升为 Production；fixture 覆盖之外仍需独立检查该语义边界。round 1 由 read-only `/root/edit_first_review`、实际 profile `reviewer_xhigh` 审查 `8470611`，返回两项 `blocking_candidate`，Parent 均裁决 `CONFIRMED`。修复在 `43b58d6`，公开入口及相关 focused suite 为 **56 PASS**，applicable Harness 已完成；同一 reviewer 的 round 2 full re-review finding set 为空。Parent 结合当前源码、公开入口测试及 Harness 关闭两项问题，没有 unresolved blocker。轮次及裁决证据为 `runs/edit-first-temporal-control-20261017-001/review-round-1.json`、`review-round-2.json`：

- `EF-001`：Canvas 通过 `model_copy` 追加 P4 后没有重新校验完整 CompositionSpec，同镜未映射声音可漏过 muted 约束。公开入口有效音轨用例复现，后续修复同时封住全局音轨/字幕，保留其他镜头独立 P4 的正常用途。
- `EF-002`：父镜被替换为 production components 后，position 继续寻找旧父镜，导致材料化后的 qualified reuse/edit 无法接回标准 compose/render 或推进后续 occurrence。修复从已验证 lineage 重开 source-backed family，接回公开 compose/render，并从实际首末子镜的 ResolvedTimeline 提取外部切点；正反顺序、普通镜头混合、P4、pending/unqualified/unknown 均有相关用例。首版不自动续接 `source=None` 动态生成组件，仍归既有 generation owner；旧无 ProductionIntent 的 Canvas 路径保持可用。

## Assessment And Remaining Limits

当前有据的结论是：ResolvedTimeline 的确定性整数映射可在 pinned HyperFrames 导出中选到预期源帧；同一既有 robot 视频可以生成一个静音的本地开发预览，在 2.0s 与 3.5s 样帧满足对应的局部姿势检查。它没有证明原 H3 输出本身满足动作时点，也没有证明变速后的完整运动自然、精确转向、声音、其他来源迁移或正常速度人工质量。

该开发预览没有 Production qualification，未 activation 或采用，最终验收仍未评估。独立的历史 H3 三镜案例曾因 retime 减慢/冻结步态并迫使下一镜重启而拒绝该方案（[历史记录](../../runs/t8-h3-seedance-3shot-continuity-20260822-v8/SUMMARY.md)）；本次单源局部观察不能推翻该反例，变速后仍须核验步态、镜间衔接和所有原已满足要求。完整 QA 与最终人工观看仍未评估；源音频 sample mapping 尚未实现，当前须显式静音或拒绝，不能称为已验证的声音保留。未知项不得由技术帧匹配或局部分析提升。

## Learning Eligibility

按 `distill-ai-video-learning` 完成 automatic evaluation：`no_candidate`，不创建占位 claim。`learning_eligibility: ineligible`；这是确定性工程实现及单一来源的编辑预览，不是独立或重复的模型质量实验。11 个 renderer 帧检查和两个观察时点不能拆成多条独立模型质量证据。相关 experience 检索已使用已有 stale-last-good 结果并核对 exact source；本 topic 的既有 learning claims 无匹配，历史 retime 反例未被覆盖或升级为新结论。工程合同按本任务明确授权实现，不标记任何实验 Learning Claim 为 ADOPTED，不刷新 RAG。

## Publication And Retrieval State

源码 `43b58d6` 已 push main，并经 `git ls-remote` 核验 exact SHA；记录收尾为 docs-only checkpoint，适用 receipt 为 `.agent/harness/runs/edit-first-temporal-control-record-20261017-r1/receipt.json`，不以文档证明替代源码或媒体证明。收尾仅澄清上述运行范围、保留历史 verdict 与证据，未再改源码语义；最终文档提交及远端 SHA 由 Git 与完成回报核验，不在本文自嵌包含自身的 commit hash。

本记录只保存于 repository 文档，不刷新 RAG index。此次剪辑修复未进行新的媒体 Provider 调用或媒体上传；开发预览使用既有本地源文件，源 Production Manifest 未变且没有 activation 或 adoption。已有 foreign staged/dirty 文件及其 index patch 经 hash 核对保持不变。
