---
record_kind: session_summary
topic_id: fanxiang-v36-v37-production-loop
learning_eligibility: ineligible
---

# Fanxiang Blender To H3 Request Preview

Date: 2026-10-07

## Status And Scope

本轮达到请求预览 checkpoint，未生成候选。用户要求将指定 v06 白模替换 Video 1，
保留既有4图和职责，经已确认 `metaso_h3 / MiniMax-H3 / REFERENCE_TO_VIDEO` 测试完整
“挥击→接触→头部受力→长颈缩回”，最多1候选、不自动重试，沿用付费确认流程。
旧 I2V 的已使用/过期许可不授权新 Ref2VA 请求。当前没有新 authorization、execution binding 或 permit。

独立目录 `R = runs/fanxiang-blender-h3-transfer-20261007-007/`，交付入口为
`R/REQUEST_PREVIEW.md`、`R/review-inputs.html`、`R/paid-preview.json`。
本次 H3 physical submits / reference uploads 均为0。原片、原候选和指定白模未覆盖；产品代码与主生成流程未修改。

## Inputs And Actual Visual Review

指定白模 `runs/fanxiang-blender-motion-reference-20261006-006/fanxiang-keyboard-contact-v06.mp4`
SHA `867d931b4f6ff44cbfd02fa6e477da7bd26c1ac433c611889d9e54a64bab1620`，
201723bytes、2.000s、24fps、48frames、1280×720、H264/yuv420p、无音轨。
4张图的bytes、顺序、roles与 predecessor `fanxiang-motion-reference-preflight-20261006-005/reference-list.json`
逐项重验一致，见 `R/reference-list.json` 与实际 native payload 的 `R/preview-validation.json`。
Image 1小龙身份/黑衣；Image 2狗哥外观/长颈；Image 3电脑键盘形状/厚度；Image 4原片场景、机位与空间。
Image 4仍是 `reference_image`，文件名 `first-frame.png` 不授予 first_frame conditioning。

本轮新建 Chrome 1×取证，播放白模、完整13.875s基线、B03与原recoil；
`R/input-playback.json` 绑定 exact SHA、播放时间、ended、rate和丢帧。
白模首次播放有3播放器丢帧，保留该观测；project-local video-analysis probe与0.083s密集样本补充接触观察，
见 `R/mcp-input-evidence.json`。基线SHA仍为
`48f94931e2bc09ee52dc9c049f1cbf91aae2df5668a6aab98cf8ba256917d27e`，再次核验源文件未变。
原片两段 source实际播放了全段，记录中的start是请求seek，不据其声明精确播放裁剪。
本轮为静音视觉观看，不声称听音验收。

Parent实际查看连续播放帧板和密集接触帧：右侧人物向左上挥击，接触后头部受力，再带相连长颈向右上原门洞退出。
两素材轴线可用于迁移，白模景别较近，指令用Image 4保留原室内侧宽构图和左侧潘子，
Video 1只提供运动、接触、节奏、相对方向，不继承灰色造型、材质、简化场景或背景人物缺失。
没有发现需要回Blender改动的明显方向冲突，v06未修改。原片直接接触缺失和recoil头颈跳变的未通过结论保持。
旧006目录辅助文件有其他窗口混写记录，本轮不依赖其历史辅助验收，而独立重验 exact MP4 和新播放/MCP证据。

## Request And Execution Boundary

请求4s / 768P / adaptive / native audio / `context_ir=false`，4s来自现有接口最短输出时长，
而非直接照搬2s参考。实际输出时长仍待fetch/probe。预估费用上限 `CNY2 / 2000000 microunits`
来自现有 operator profile，不是官方报价或已观察账单，实际扣费未知。
外发目标 `https://metaso.cn`，内容为 exact 编译提示词和4图+1视频，retention为 `provider_standard`。

原角色清单含4个角色，当前4图只分别提供小龙/狗哥的独立identity references；
现有Planner阻断missing references。经独立预览project的既有committer修正主动动作角色为小龙/狗哥，
潘子继续作为Image 4背景保留，不添加曾亮或新图。重新取得readiness三项PASS。
重复文本超出现有5000字符原生语法上限后，精简为3444字符，完整动作链、职责和方向保持。
这些是任务内素材/creative authoring修正，没有修改compiler、gate或通用模型。

预览经现有 full project reader、Planner/Readiness、Router requirement binding、adapter compile/resolve、
`PaidProviderCallPreview` 完成，native body中的每个参考role、bytes与SHA逐项相符。
request fingerprint `9d9f578f804ed03e37040b6da6471f42beb3181022c6c87fc461426095e68bf4`；
paid preview fingerprint `2df05f098e5a4bdf9eff447b4ac7385747a12335d62039fe7895d8ca57daab27`；
native body SHA `d12d827da67a2671990ffcd4220847ecfe6e47ea6faf3b55cc36a64b37e66707`。

完整 `GenerationFeedbackOrchestrator.for_project` 准备过程在重复重开immutable paid-budget/history时长时间占用CPU，
已停止该本地尝试，trace存于 `R/prepare-preview.log`。未丢弃/重置历史或改动reader。
请求预览不代签generation decision、remaining bounds、execution binding、paid authorization或one-use permit；
提交前这些现有检查仍必须完成，且实际外发payload必须匹配已批准素材、提示、model、时长和费用边界。

## Verification And Remaining Work

- 当前 H3 adapter 相关测试：58 passed，`R/metaso-adapter-verification.log`；仅证明所测接口行为。
- readonly受管Kimi deep/max输入审查：invocation `4c3d1b7a-b585-4c5b-a9ee-830f31282db6`，2 wire requests；
  canonical receipt、report SHA与observed Read SHA在修正前核验。Parent采纳多余角色和明确axis policy意见，
  后续中文精简由Parent与原生compiler验证。审查不证明最终请求执行或H3视觉效果。
- Chrome预览页面实际加载：2个视频和4图均可读，`R/review-entry-check.json`、`R/request-preview.png`。
- 文档checkpoint的检查receipt owner：`.agent/harness/runs/fanxiang-blender-h3-preview-record-20261007/receipt.json`；
  其status与freshness以实际receipt为准，不认证视频质量。

当前 `generated_candidate_improvement = NOT_EVALUATED`，没有候选或候选接入对比MP4。
获得本次有效付费确认后才进入单次执行，保留raw。生成后实际播放并显式MCP核验接触、方向和头颈连接；
通过现有CompositionSpec→ResolvedTimeline→HyperFrames/P4制作独立接入与对比预览，保留原开头/拾键盘和声音。
候选覆盖完整接触与缩回，完整退出后才接旧空窗，不用旧recoil、切镜或变速掩盖问题。失败指出主要问题并停止。

`record-ai-video-session`为本地预览checkpoint；自动learning evaluation为 `no_candidate`：
没有独立H3迁移结果，素材/预览/技术检查不能作为改善证据。没有新Learning Claim、Skill/Policy/Gate adoption。
本文仅新增owned documentation checkpoint；媒体与请求local-only，不上传、不发布、不push其他窗口历史。
`AGENTS.md`、`skills-lock.json`、安装中的skill目录和其他窗口record保持其ownership。
