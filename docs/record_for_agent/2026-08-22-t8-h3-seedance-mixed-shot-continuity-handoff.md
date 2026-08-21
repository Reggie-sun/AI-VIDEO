# T8 H3 Seedance Mixed Shot Continuity Handoff Record

Date: 2026-08-22

## Purpose

本文记录本窗口已经稳定确认的三镜混合 Provider continuity contract，供下一窗口执行一次 bounded runtime smoke：

```text
T8 Turbo T2VA Shot 1 -> exact terminal frame -> 原生 H3 FL2VA Shot 2 -> exact terminal frame -> Seedance 2.0 Mini I2V Shot 3
```

本记录是 execution handoff 与 architecture/runtime boundary note，不表示三镜混合 live run 已完成，也不授权新的 implementation、Provider submit、上传或 release。

## Current Runtime Truth

当前 AI-VIDEO T8 adapter identity 是 `comfy-local-h3-t8`，已实现的 T8 quality 与 Turbo lanes 都是 T2VA：

- `minimax-h3-t8-t2va-quality-v1` / `minimax-h3-t8-t2va-quality`
- `minimax-h3-t8-t2va-turbo-v1` / `minimax-h3-t8-t2va-turbo`

这些 T8 requests 只消费文字和 provider-bound request，不能消费上一镜的 `first_frame` 或 image reference。因此在要求 exact terminal-frame continuity 的三镜链中，T8 必须作为第一镜。将 T8 放在后续镜头只能得到 prompt-level semantic continuity，不应标记为 exact continuation。

原生本地 H3 lane 的当前 FL2VA capability 是 `minimax-h3-fl2va-local-v1`，可以消费 required `first_frame`。Seedance model identity 是 `doubao-seedance-2-0-mini-260615`，其 I2V contract 也要求 image reference；当前 accepted input boundary 仍由 `SeedanceAssetMaterializationReceipt` 与 `SeedanceAssetReferenceResolver` 负责，local Registry ID 不得伪装成 Ark `asset://` identity。

本地 loopback ComfyUI Provider 在当前 task scope 内不需要重复授权；这只适用于 local、unmetered、no-cloud-egress execution，仍必须经过 sealed profile、local permit、唯一 committer、state/status/fetch 和 recovery contracts。

Seedance 属于 paid/cloud execution。稳定 credential reference 仍是 `ARK_API_KEY`，实际 lookup 必须走既有 credential supplier 和 Secret Service contract；记录中不得出现 raw secret。下一窗口最多允许一次明确的 Seedance submit，必须先完成 exact preview、finite budget、durable intent、cloud-egress 与 one-use permit；unknown outcome 只能走 explicit recovery，不能 blind retry 或 fallback。

## Session Work And Decisions

本窗口解决了“为什么 T8 不能放在后续 Shot”的歧义：不是 T8 模型永远不支持 I2V，而是当前 AI-VIDEO 已 sealed 的 T8 adapter 只暴露 T2VA。上游或未来新增 T8 I2V adapter 不能被当前任务隐式假定，也不能静默替换现有 T8 identity/profile。

下一窗口的最小连续性场景保持不变：同一雨夜蓝调站台、短黑 bob 女性、mustard-yellow raincoat、red satchel，始终 screen-left 到 screen-right；第一镜建立行走，第二镜从第一镜实际末帧继续经过长椅，第三镜从第二镜实际末帧继续到站钟附近减速停下。

优先复用已经存在的本地 T8 Turbo Shot 1 artifact，以减少重复 local generation；复用前必须重新验证 artifact bytes、尺寸、帧数和最终 `*-audio.mp4` 语义。然后只生成一个原生 H3 Shot 2，并从其实际 decoded terminal frame 形成 Seedance Shot 3 的 `first_frame` 输入。

Seedance image-input materialization 是下一窗口的首要 gate。用户提供的 session `01a023c4-2403-7e41-bbb0-bf43bb00261e` 只有在其修复已经进入当前 HEAD 并有可验证 code/tests 时才能使用；不得直接依赖未知 dirty edits、猜测 Ark upload endpoint 或伪造 materialization receipt。若正式 materialization seam 不成立，应在 paid POST 前 fail closed，而不是把第三镜降级为 T2V。

## Verification And Evidence

已存在的 T8 Turbo continuity smoke artifact 位于：

```text
runs/t8-turbo-3shot-continuity-20260821-v1/
```

其中包含 `raw/shot-01-audio.mp4`、`raw/shot-02-audio.mp4`、`raw/shot-03-audio.mp4`、junction PNG、contact sheets 和 `generation-evidence.json`。下一窗口只能把它作为可复核的本地 artifact 候选，不能据文件名直接推断新的混合 Provider run 已完成。

此前的 H3-only 三段 review derivative 位于：

```text
runs/h3-terminal-chain-3shot-20260821-v1/evidence/continuity-review.mp4
```

它证明过 exact terminal-frame handoff 的本地 smoke 方向，但由三个独立 project/Manifest 产生并用 hard concat 形成 review derivative；不能表述成单一 canonical 三 Shot Production run、Final Acceptance 或无缝音频成片。已有 review 还指出全速人工播放和听觉切点审查不能由抽帧/ffprobe 代替。

下一窗口的 fresh evidence 至少应包括：

1. 三个 source clip 的 `ffprobe` codec、尺寸、fps、decoded frame count、duration 和 audio stream facts；
2. 两个 handoff PNG 的 source artifact SHA-256、实际 decoded frame index、PNG SHA-256；
3. H3 与 Seedance request 中确实绑定相应 exact terminal frame/asset 的 request/receipt evidence；
4. 两个 junction 的末帧/首帧比较、SSIM 或等价边界测量，以及 contact sheet；
5. 完整 decode、black/freeze/duplicate-frame checks 和一次全速人工 visual review；
6. 明确区分 raw Provider artifact、review derivative、activation、technical acceptance、subjective quality acceptance 与 P4 final composition。

当前窗口没有执行新的 ComfyUI generation、Seedance submit、Ark upload、付费调用或媒体质量验收。

## Assessment

当前最可靠的连续性拓扑是 `T2VA -> FL2VA -> I2V`。它利用每个已实现 Provider 的真实输入能力：T8 负责 text-origin shot，原生 H3 和 Seedance 负责 terminal-conditioned continuation。任何 `T8` 后置方案在没有新增并 sealed T8 I2V capability 的情况下都只能算 semantic continuity experiment。

这是一份稳定的 handoff boundary，不是三镜混合 runtime 完成声明。尤其 Seedance 的 exact terminal PNG 是否已经拥有可信 Ark materialization receipt，仍需下一窗口依据当前 HEAD、tests 和真实 receipts 判断。

## Remaining Risks Or Next Work

1. 验证 session `01a023c4-2403-7e41-bbb0-bf43bb00261e` 的修复是否已 committed；若未 committed，不能把 dirty implementation 当作正式能力。
2. 验证 H3 terminal PNG 到 Seedance `first_frame` 的 bytes identity 和 egress evidence；不能用相似图片或 local Registry ID 代替。
3. Seedance cloud submit 必须保持单次、预算有限、可恢复；若 output duration/frame contract 失败，保留 fetched evidence 并报告 fail-closed 状态，不放宽 validator 伪造成功。
4. 最终三镜 hard concat 只能作为 review derivative；如需 Production-level 三 Shot completion，仍需在真实 canonical project/Manifest 和 P4 `ResolvedTimeline -> HyperFrames` composition 中单独完成。
5. 本记录不恢复 `.agent/context/session-handoff.md` 中旧的 5-minute rough-cut。

## Agent Guardrails

- 不修改 `ProductionProject`、Manifest schema、Provider-neutral requirement 或 canonical timeline/audio owner。
- 不改变现有 `comfy-local-h3-t8`、`comfy-local-h3` 或 Seedance profile identity，不添加隐式 fallback。
- 不将 `T2VA` 描述成可消费 reference 的 I2V；不将 Seedance T2V 描述成连续 I2V。
- `first_frame` 必须绑定上一个 Shot 的实际 decoded terminal bytes；不得使用预选 bridge frame。
- 不读取、打印、保存或写入 raw credential；只保留 `ARK_API_KEY` reference。
- 不覆盖、stage 或 commit 当前 working tree 中其他 session 的 dirty/staged files。
- 记录本身不触发新的 tests、generation、upload、Provider call、release 或 push。
