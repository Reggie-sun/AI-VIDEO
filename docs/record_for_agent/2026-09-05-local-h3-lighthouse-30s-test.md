---
record_kind: media_experiment
topic_id: local-h3-lighthouse-30s
learning_eligibility: eligible
evidence_index_version: "1"
---

# Local H3 Lighthouse 30s Test

Date: 2026-09-05

## Learning Adoption — 2026-09-05

用户在收到 exact candidate 与唯一目标预览后回复“可以”。确认于
`2026-09-05T20:16:26+08:00` 记录：candidate commit
`63ea712ae2b968f670392b781609fb689f278864`，committed bytes SHA-256
`567d7fa9c73447515d1ad9d6f4c1f5ae249f9fb49729dedd6b124b199f8a9a19`。
采纳前与 current pending bytes 核对一致。本次不同于之前只批准补评估的确认。

当前为 `ADOPTED`（active v1，pending version 0）；唯一目标为 `.agents/skills/h3-video/SKILL.md` C 节，
只增加 Shot-local 可见状态与 palette/lighting/materials/camera subject/endpoints 的一致性
检查，以及 actual compiled prompt 回查和既有 Gate 不变的边界。下方 `pending_candidate`
与未采纳描述保留为先前评估阶段的历史，不再表示当前采用状态。

Target commit `5d17c05864b588d1d893f66a3b8b28be4340e3a6` 仅新增 17 行；target bytes SHA-256
`79dfdb27e4fe4e511f9fb4bcd65c1d8914601515a214d8f3f62bdd0a7a5fd67a`。
18 项 focused Node assertions 确认 scoped 指导和旧内容完整保留；documentation/policy checks、
runtime boundary 2 tests、local supervisor 17 tests、Harness 205 tests 均 PASS。
目标 receipt `.agent/harness/runs/h3-shot-local-adoption-target-20260905-v1/receipt.json`
已验证 fresh/integrity/snapshot/scope 全部通过。未用测试证明模型质量提升。

按 `record-ai-video-session` 同步主记录、旧记录与 claim lifecycle；本次文档收尾 receipt 为
`.agent/harness/runs/h3-shot-local-adoption-record-20260905-v1/receipt.json`。
`distill-ai-video-learning` 收尾评估为 `no_candidate`：本轮只采纳已确认 v1，没有新增 empirical
evidence，不另造候选，也不改变其他已采纳 claim。用户对 30s 成片的整体认可与原 Gate 均不变。

采纳 preflight 实际执行 `experience` 检索 `h3-shot-local-visible-context candidate adoption`，
返回含 stale-tagged 的旧 experience；决策基于重新核对的 exact committed candidate，
不根据历史摘要改变范围。CLI 自行排队派生索引刷新；未手工重建/等待，不声称新 active 状态已入索引。
本轮未调用 Provider、生成媒体或写 Product state；保留 unrelated dirty/index work，未 push/release。

## Learning Reassessment — 2026-09-05

用户确认补全跨实验复核后，本轮结果为 `pending_candidate`：
[H3 Shot-Local Visible Context Consistency](learning/h3-shot-local-visible-context.md)。
它只提出 H3 T2VA authoring 的跨字段一致性检查，不证明 prompt repair 的因果效力或成功率。
下方各历史 `no_candidate` 保留，但不再代表本主题已经完整复核后的当前结论。
先前“同一叙事链 + seed 改变，因此没有候选”的理由不充分：不同 request 可以构成不同
execution unit；seed 混杂排除严格 prompt-only 因果比较，不自动排除重复的有限观察。

本轮重开两个短片 attempt 与本 run 十个 source 的 resolved request、逐项 Gate，重算十二个
MP4 SHA-256，全部与既存 Evidence Index 相符；另读主要支持的 compiled prompt 与 MCP
frame-review sidecars。没有重新生成/解码/分析媒体，没有改变旧 Gate 或用户认可。

| Evidence group | Reassessment / counting |
| --- | --- |
| Shot01 initial + Shot05 initial | 两个不同 request 分别含暗灯/amber palette、sea-only/lighthouse camera subject 冲突，且对应 required finding FAIL；是同一窄问题的两个主要支持 unit |
| Shot01/05 repairs | 相关字段修正后的新 request 均 PASS；seed 同时改变且文字有多个相关变化，保留为相邻观察，不宣称固定 seed A/B 或成功率 |
| Shot04/06 initial + repairs | 四个独立 execution，pan 可读性与 extreme-wide framing 各有 FAIL→PASS；目标不同，不为当前 context 冲突 claim 扩大支持数 |
| Shot02/03 | 两个初次 PASS，作为边界：不是所有 Shot 都失败或必须预防性补拍 |
| 旧短片001/002 | 两个 distinct request；002解决可见点灯，但扫光 FAIL。反对“修好局部即可通过整镜”的过宽解释 |
| Final render + technical/visual/user proof | 同一组合成片的新 proof layers，不计为新的生成实验；用户整体认可不变 |

真实 `experience` RAG 首查 `H3 T2VA lighthouse prompt camera framing repair seed` 返回
stale-tagged experience 与单独 fresh 的 V8 run summary；发现跨字段冲突后 focused 查询
`H3 shot-local palette camera subject offscreen state conflict` 返回 M6 fresh 对照片段。
已重开 exact 当前 source；未以 RAG score、片段数量或旧 no_candidate 自证结论。
CLI 首查自行排队派生索引刷新；未手工重建或等待，也不声称新增候选已可检索。

历史对照覆盖旧灯塔、Drama v1/v2、M6、T8 upstream、V8 summary 与 Turbo comparison。
Drama 同 profile 的局部 framing PASS 不能覆盖其 overall audio FAIL；M6/V8/upstream 的
FL2VA/Long Video 与 Turbo recipe 不并入当前 T2VA support。现有 learning 目录仅见
无关的 HyperFrames caption adopted claim，保持不变。一个 native read-only explorer
独立检查历史边界，parent 重开关键原文复核；没有让历史摘要代替本次 exact evidence。

唯一拟采纳目标为 `.agents/skills/h3-video/SKILL.md` 的现有 authoring 指导；本轮未修改它。
候选状态 `SUPPORTED / PENDING_CONFIRMATION / NOT_ADOPTED`；用户本次确认仅批准评估，
不授权采纳尚未展示 exact commit/hash 的新候选。本轮记录按 `record-ai-video-session`
完成并由 `distill-ai-video-learning` 生成一个候选，不另造同题记录。

本轮验证 receipt 分别为
`.agent/harness/runs/h3-learning-reassessment-record-20260905-v1/receipt.json` 与
`.agent/harness/runs/h3-shot-local-visible-context-candidate-20260905-v1/receipt.json`。
只执行本次文档/learning delta 的 policy checks；无 Provider/media/cloud/paid 调用，
无 Product state 写入，保留 unrelated dirty/index work，未 push/release。

## User Acceptance — 2026-09-05

交付下方 exact 30s 成片后，用户回复“确认可以”。本次记录为该版本的整体用户认可，
绑定 MP4 SHA-256 `3749b1e53c4fe674279b7bf50b8c496b67daa66428569e8f25c77d397c83bd38`；
不再等待整体认可，也不再生成新版本。用户未说明播放方式或逐项听验结果，因此不将该反馈
扩张为 full-speed/listening rubric 全项 PASS、精确建筑一致性或 P6 / Final Acceptance。
下方 `final-render-human` 与 `final-media-gate.json` 保留为交付时的历史未评估证据；
本次新增独立的整体认可 proof layer，不修改媒体、原 Gate 或 Production state。

`distill-ai-video-learning` 本次评估仍为 `no_candidate`：同一 exact 成片的用户反馈
没有增加独立实验，也未形成新的受控比较或同范围 existing claim 更新。
仅补记本文件；未新增 Provider/media/network 调用，未刷新 RAG index，未 push/release。
本次 documentation 验证 receipt：
`.agent/harness/runs/h3-lighthouse-30s-user-acceptance-20260905-v1/receipt.json`。

## Current Checkpoint — Completed Render After One Approved Renewal

用户在原9次预算停止后明确同意：只给最后 Shot06追加1次补拍，通过后合成。原
`budget.json` bytes未改，新增`budget-renewal-shot-06.json`绑定原hash
`7855d73bbde634c993bcafadf92ddd44434ab96bba93a40d53708449b1785404`，
仅对`shot-06-repair-01`开放total10，其他per-Shot/time/GPU/unknown-outcome限制不变。
原FAIL Gate保留；这不是复用旧permit或重新解释旧attempt。Native reviewer_xhigh限定审查通过。

补拍仅增强原extreme-wide目标的完整塔身/塔基、远处屏幕占比和海岸边界表达；
small slow backward camera、amber灯和雨夜均保留。新resolved request
`ccb7306a28874982f144a5aaa891dd6d39e818551dd61d5dcf0a76d887f48277`，
submit 11:10:32 UTC，succeeded 11:15:42 UTC。MP4
`84c20601b55bfb74dfd00ea715944bc9aec350607ae0b769b36e506c53fa4cc8`，
1790565bytes；MCP probe、0–5s抽样和完整AV decode通过。完整塔身与塔基全程入画，
塔体随拉远缩小，海岸主导画面；原required findings全部PASS。
“约五分之一”属于构图引导而非精确像素约束，不声称逐帧达到该比例。

六段选择为`shot-01-repair-01, shot-02, shot-03, shot-04-repair-01,
shot-05-repair-01, shot-06-repair-01`。通过真实import和唯一committer创建final project，
实际`compose_final.py prepare`与`render`完成，不再只是静态脚本证据。
`ResolvedTimeline`为720frames/1440000samples，六段各取前120frames，HyperFrames 0.7.103。
最终canonical render：

```text
runs/director-h3-lighthouse-30s-20260905-001/final-production/state/render/outputs/3749b1e53c4fe674279b7bf50b8c496b67daa66428569e8f25c77d397c83bd38.mp4
```

SHA-256与文件名一致，18956501bytes，H.264 High、1344×768（实际7:4）、24fps、720frames；
video/audio stream durations均30.000s，container duration30.022s包含AAC framing。
AAC为48kHz stereo。最终MP4完整AV decode通过；显式MCP probe和30张抽帧中的18张
实看片（时间0至29.021s）确认六个叙事段落、动作完成与收尾均保留，没有用循环/慢放凑时长。
证据：run下`final-render-result.json`、`final-mcp-probe.json`、
`final-mcp-frame-review.json`、`final-media-gate.json`及六份`import-*.json`。

P4唯一音轨确实覆盖1440000samples；source HTML六个video均muted，
canonical mixed WAV hash为`be1d4c6d3cd28dee74ed8362f68e1f2c8e072c46e9263e873a81f9e3c5f7f20a`。
初次无seek解码与reference零偏移相关度-0.2606；检查first AAC packet发现pts=-1024、
SkipSamples=1024。仅将验证命令改为`ffmpeg -ss0`按presentation start解码，未改MP4，
对应波形相关度0.999891498。比对1439744samples；decode尾部少256samples（5.333ms），
处于最终fade，未比对reference尾峰值0.000244；encoded stream与canonical timeline仍为30s。
最终RMS -28.46dBFS / peak -13.97dBFS。此为音源路由/编码技术证据，不等于无损PCM一致、
sample-perfect解码或human听验。详见`final-audio-verification.json`。

Development required technical/sampled-visual Gate为PASS，**human full-speed/listening、
P6及Final Acceptance未执行**。首尾塔的窗格、栏杆、附属建筑仍有可见差异；
仅宣称已选定的bounded semantic/color/archetype continuity，不宣称建筑精确一致。
交付为可供用户观看/听验的30s本地成片。没有更多Provider调用、cloud/paid执行或发布。

续期前做了真实RAG `H3 extreme wide shot scale full subject framing cropped`：
返回旧三镜头run summary与stale-tagged M6片段，未命中直接可复用的当前T2VA修复配方；
重开相关run原文，未手动刷新索引。自动`distill-ai-video-learning`仍为`no_candidate`：
新增补拍与render只扩展同一链，seed混杂未消除，无同范围existing claim可更新，
不以文档/片段/多proof层数量冒充独立实验。

本次更新使用documentation exact-staged Harness：
`.agent/harness/runs/h3-lighthouse-30s-final-20260905-v1/receipt.json`。
记录期间无额外Provider/media/network；保留其他窗口工作，未push/release。
下方Budget-stop、Audio/Composition和Resume段落均保留为**续期前历史状态**，
已由本节实际成片证据取代；各旧source FAIL本身仍有效。

## Historical Budget-stop Status

用户要求真实本地 H3 30s 视频。本次封存的 9 次生成全部完成并 fetched，但只完成五个 Shot 的 required Gate：
`shot-01-repair-01 → shot-02 → shot-03 → shot-04-repair-01 → shot-05-repair-01`。
这五段可各取 5s，即 25s 素材；尚未生成最终 30s composition。

Shot 06 的拉远、灯光和基本塔型可读，但起始与终止画面主要是灯塔上半部，未达到 sealed
`shot_scale=extreme_wide`，Gate 为 `FAIL`。不放宽原 requirement，不把五段 PASS 或第六段技术成功称为成片成功。
本 checkpoint 是 `BUDGET_EXHAUSTED / STOP_BEFORE_FINAL_COMPOSITION`，不是 Provider unknown outcome。

Run root：`runs/director-h3-lighthouse-30s-20260905-001/`。本轮 task artifacts、脚本与视频为 local ignored outputs，不进入产品源码。
旧 5.167s 测试记录 `2026-09-05-local-h3-lighthouse-director-test.md` 的独立 artifact FAIL / NOT_EVALUATED
仍有效；本次新 run 不覆盖其历史判定。

## Director And Runtime Boundary

`open-video` schema3 coverage 已实际验证：`direction`、`agent_directed`、六个 units、30s、`multi_shot`。
分镜依据因果信息与视角变化选择：暗塔与海浪、手轮动作、灯亮、雨窗扫光、海面扫光、远景收尾；
不是按“超过15s”或有无 prompt 强制拆分。

已批准的 viewpoint cuts 使用六个独立 T2VA sources，保持 bounded semantic/color/object-archetype continuity；
不声称 exact tower geometry、terminal-frame continuity 或连续单 take。没有自动切换 I2V/Ref2VA。

每个 source 使用既有 `ProductionStateCommitter` bootstrap、正式 Planner/Router/compiler3、
`VideoGenerationService.submit_local_once`、poll/fetch。Profile：
`workflows/profiles/minimax_h3_t8_t2va_quality.json`，hash
`4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7`。
T8 `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40` / `1.36.2`；
ComfyUI `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；
VHS `4ee72c065db22c9d96c2427954dc69e7b908444b`、SageAttention `2.2.0`。
Exact request 为 quality20，未使用 Turbo LoRA，严格 loopback、无 cloud/paid call。

9 次均由 canonical service 记录 known succeeded；第一 submit 为 09:22:06 UTC，
最后 succeeded 为 10:56:51 UTC。首个预提交 draft 保留在 `preflight-shot-01/`，没有 submit，不计生成次数。
`budget.json` 限制 total9、每Shot2、elapsed14400s、GPU10800s；总次数已耗尽。
共享 ComfyUI 曾被其他任务使用；本任务未取消其他 job。停止生成时队列空，但不因记录停止共享 service。

## Media Findings And Repairs

每段 exact MP4 均调用 project-local `video-analysis.video_probe` 与
`video_extract_frames`，0–5s 每秒抽样；按 source intent 分项 Gate。后续 submit 重新绑定前序
PASS Gate 与 exact MP4 SHA-256。Probe sidecar 移除了 embedded prompt metadata。

| Shot | Initial finding | Repair variable / result |
| --- | --- | --- |
| 01 | 应保持暗灯，但初始视频已亮灯：FAIL | 移除首段未来 amber 状态泄漏，明确未亮窗室；repair PASS |
| 02 | 手轮顺时针约四分之一圈并保持，固定近景：PASS | 无补拍 |
| 03 | 正面 Fresnel lens 暗到 amber 并稳定，推近：PASS | 无补拍 |
| 04 | 扫光完成，但右摇不明显：FAIL | 增强相邻窗格的 camera endpoints 与可读幅度；repair PASS |
| 05 | 扫光完成，但灯塔建筑占左侧，违背 sea-only：FAIL | 可见 context 只留海水/礁石，将光源放在画外；repair PASS |
| 06 | 灯塔/灯光/拉远通过，但构图未达 extreme-wide：FAIL | 总预算耗尽，未补拍 |

所有九个 raw MP4 技术 probe 为 H.264 High、1344×768、24fps、124frames、5.167s、AAC 32kHz stereo；
完整 AV decode 检查通过。技术 PASS 与上表语义 finding 分开，不证明逐帧 anatomy、human full-speed
perceptual quality、精确跨镜头建筑一致性、P6 或 Final Acceptance。

Repairs 保持同 profile/mode/duration，但新 exact request 派生了新 seed；
它们是 evidence-backed bounded attempts，不是固定 seed 的受控因果比较。

## Audio And Composition State Before Renewal

用户同意统一后期音轨，所有 source 声明 `GENERATED + REPLACE`，同时请求 native audio=true。
Raw Gate 只证明 native route 与显式 P4 0–30s coverage 已声明，不证明最终替换已经发生。

`soundtrack.wav` 是本地原创合成 wind/surf texture 与低音持续音，非 literal synchronized foley；
SHA-256 `d1dffdcf00fe8d9996ec9a331053843832dc073e7796c2d494f6a1b36f16181a`，
48kHz stereo PCM16、1440000samples。源测量 mean -34.4dBFS / peak -19.9dBFS；
task composer 声明 P4 +6000millidB gain。尚未混入成片，human listening 为 NOT_EVALUATED。

`compose_final.py` 已静态审查，要求显式六个全 PASS 的 `selected-sources.json`，
真实 imported video assets、唯一 `ResolvedTimeline`、720frames/1440000samples 与 HyperFrames。
当前没有 selection、final bootstrap 或 render，没有 P8 source activation、P6 或 Final Acceptance。
不能用 direct concat、重复片段、慢放或移除 source muted 绕过未关闭的 Gate。

## RAG And Learning Evaluation

真实项目 RAG 在开始时检索 `H3 30s multi shot canonical source audio replace P4 continuity`，
命中旧三镜头 run summary；随后针对 `H3 camera pan ignored locked camera endpoint repair` 检索。
后者包含 stale-tagged 旧 M6/V13 经验，已重开当前原文；没有可直接复用的当前 T8 T2VA 右摇修复配方。
历史材料仅为 advisory，不代替当前 Gate；未等待或手工重建 RAG index。

`distill-ai-video-learning` 自动评估：`no_candidate`。
已检索当前 learning 目录中的 lighthouse/灯塔/camera endpoint/画外/offscreen，未发现同范围 claim；
并核对旧灯塔测试及 M6 的失败/后续 supersession 作为 counter-context。
本次只有一个六段叙事链，各段目标不同，三次 repair 均混有 seed 变化；
不能据此提出“增强 prompt 必然修复”或 H3 model-wide quality/continuity 规则。未修改 adoption targets。

## Historical Resume And Verification Boundary

如用户选择继续最小补拍，应先显式续封有限预算，仅重做 Shot06：
让 whole tower、base 与 coast 的可见 endpoints 明确，小尺寸塔体完整入画，保留 backward camera、
amber lamp 与 rainy coast；新 identity/intent/permit 后完整重验。不得修改现有 FAIL Gate 或旧预算 bytes
来伪装尚未耗尽；当前 driver 的预算来源需要明确续期方案。

只有第六段 PASS 后才能调用 task composer，经正式 import、timeline preview、render，再验最终30s
实际裁切与 P4替换音轨。当前 prepared composer 只有静态证据，不声称实际 runtime/render PASS。

本记录按 documentation 类别进行 exact staged Harness checks，receipt 位置：
`.agent/harness/runs/h3-lighthouse-30s-budget-stop-20260905-v1/receipt.json`；
只有实际 fresh PASS receipt 才构成验证证据。本次不为记录执行额外 Provider/media、network 或 full suite。
未改动其他窗口文件，未 push/release；其他窗口在本任务期间自行推进 main，不计入本次工作。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| shot-01-media | h3:a213b70147300fda55b2d1f82913de72656a2154608b49267561cb7469619f22 | lighthouse-30s-20260905 | shot-01-video-30s | N/A | a2625cc547a90a3fa4e5d33da79060fcd7c195295fad13da09f07eed1b3a4f73 | AGENT_VISUAL | FAIL | DARK_LANTERN | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-01/media-gate.json |
| shot-01-repair-01-media | h3:44f92d833a47b5a175d491fd2dabcaa0049cc6ac0341b90e9e3b69d4e5875fc2 | lighthouse-30s-20260905 | shot-01-repair-01-video-30s | N/A | bf82c78ac79b9bec701e390494e03bd3f764079f98d92ed8c58baa6bb44c2fc9 | AGENT_VISUAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-01-repair-01/media-gate.json |
| shot-02-media | h3:2e04687f4023e53719350f5644a671a91ca3c8c591b2a5733582bc4294f106a9 | lighthouse-30s-20260905 | shot-02-video-30s | N/A | ecb88f58b8aef00affff61d7b3eae128783eab7cfa2e1e82d943316c4de0686c | AGENT_VISUAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-02/media-gate.json |
| shot-03-media | h3:ec5d0b7e62510c90f44e89110d789fbdd81f092adb6984071007e30e2c13679c | lighthouse-30s-20260905 | shot-03-video-30s | N/A | 4f9e36c22cf19ce15a4a26d4487ef78c2b94fde88c52ed9681cc9a230cfd4ec6 | AGENT_VISUAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-03/media-gate.json |
| shot-04-media | h3:63184b05fb934bbf77ac778b1e54c6e1bf62b9263b3880fe2cf30f3f76f804a8 | lighthouse-30s-20260905 | shot-04-video-30s | N/A | 05fc29db6bffa334c34ef3730b82ed7729f4708553c367e4c249322f5a460e4f | AGENT_VISUAL | FAIL | CAMERA_PAN | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-04/media-gate.json |
| shot-04-repair-01-media | h3:06312e1b86960e8b1356bf8ee303acdfc35e762f5dbe50e163f5cbafb4e9dc57 | lighthouse-30s-20260905 | shot-04-repair-01-video-30s | N/A | 6cd8ac78ef1b4e311c0b8b9e418964bf7b2a74e3836e791cd029bdf07651b47d | AGENT_VISUAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-04-repair-01/media-gate.json |
| shot-05-media | h3:04014045bb2758574974f1563ef9142763f5a23f10973296e137663d11b8b05b | lighthouse-30s-20260905 | shot-05-video-30s | N/A | 73937df49aaf0977c53e017849891245d957c8390cb61d0a550b6cb6413e1dfd | AGENT_VISUAL | FAIL | OFFSCREEN_ARCHITECTURE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-05/media-gate.json |
| shot-05-repair-01-media | h3:77bf42aeb183f2fadafa884ff18f88d7150dca6a075d10fc2197e0cb00bf9063 | lighthouse-30s-20260905 | shot-05-repair-01-video-30s | N/A | 0fe033bb5189ec4c339e27789fd84763826a90ace7e9daccda740f9021ca8476 | AGENT_VISUAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-05-repair-01/media-gate.json |
| shot-06-media | h3:2d7f875c2b2a2f4948e43c04b5332ce633f5af4ac3237dfe27ba730ced2975c3 | lighthouse-30s-20260905 | shot-06-video-30s | N/A | 272dd8b34ab8f0bd2bbb7a14394ffa708d7e72277f25dd1ef177b527dbb3c861 | AGENT_VISUAL | FAIL | SHOT_SCALE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-06/media-gate.json |
| shot-06-repair-01-media | h3:ccb7306a28874982f144a5aaa891dd6d39e818551dd61d5dcf0a76d887f48277 | lighthouse-30s-20260905 | shot-06-repair-01-video-30s | N/A | 84c20601b55bfb74dfd00ea715944bc9aec350607ae0b769b36e506c53fa4cc8 | AGENT_VISUAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-06-repair-01/media-gate.json |
| final-render-technical | render:86f9f69f61aad5a9eb031a0c20d88deeae6331c38f464feb8860cf899bdb6c5c | lighthouse-30s-composition-20260905 | lighthouse-30s-final-render | N/A | 3749b1e53c4fe674279b7bf50b8c496b67daa66428569e8f25c77d397c83bd38 | RENDER_TECHNICAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/final-render-result.json |
| final-render-media | render:86f9f69f61aad5a9eb031a0c20d88deeae6331c38f464feb8860cf899bdb6c5c | lighthouse-30s-composition-20260905 | lighthouse-30s-final-render | N/A | 3749b1e53c4fe674279b7bf50b8c496b67daa66428569e8f25c77d397c83bd38 | AGENT_VISUAL | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | final-render-technical | runs/director-h3-lighthouse-30s-20260905-001/final-media-gate.json |
| final-render-human | render:86f9f69f61aad5a9eb031a0c20d88deeae6331c38f464feb8860cf899bdb6c5c | lighthouse-30s-composition-20260905 | lighthouse-30s-final-render | N/A | 3749b1e53c4fe674279b7bf50b8c496b67daa66428569e8f25c77d397c83bd38 | HUMAN | NOT_EVALUATED | HUMAN_REVIEW_PENDING | SAME_EVIDENCE_NEW_PROOF_LAYER | final-render-technical | runs/director-h3-lighthouse-30s-20260905-001/final-media-gate.json |
| final-render-user-acceptance | render:86f9f69f61aad5a9eb031a0c20d88deeae6331c38f464feb8860cf899bdb6c5c | lighthouse-30s-composition-20260905 | lighthouse-30s-final-render | N/A | 3749b1e53c4fe674279b7bf50b8c496b67daa66428569e8f25c77d397c83bd38 | USER_OVERALL_ACCEPTANCE | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | final-render-technical | docs/record_for_agent/2026-09-05-local-h3-lighthouse-30s-test.md#user-acceptance--2026-09-05 |
