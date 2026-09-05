---
record_kind: media_experiment
topic_id: raw-creative-director-seedance25
learning_eligibility: eligible
evidence_index_version: "1"
---

# Seedance 2.5 Director Live Test

Date: 2026-09-05

## Purpose

用户要求“真实视频生成测试”，沿用对话中的 Seedance / 30s / 无 creative prompt 场景。
本次实测 `open-video -> approved Character / Scene / Shot -> seedance-authoring ->
canonical Planner / Router / compiler -> VideoGenerationService`，验证自主导演设计是否真正进入画面。
前序 deterministic 修复见 `2026-08-30-promptless-long-form-director-preflight.md`；它当时未生成媒体的
历史边界仍然成立。本次是后续单案例 live evidence，不是所有 raw-input 类型的质量验收。

## Scope And Execution

- 原创内容：铜制机械萤火虫苏醒、穿越藤蔓、触碰中心铜花、温室随光脉冲复苏。
- `creative_input_kind=missing`，`coverage_strategy=multi_shot`，`strategy_source=agent_directed`。
  四段 coverage 源于信息尺度与因果推进，不源于时长阈值；6/8/7/9s 是 authored pacing。
- 四段画面 coverage 编入一个包含明确剪切的 `greenhouse-01` Production Shot；不是四次 Provider submit。
- Model `doubao-seedance-2-5-260628`，official Ark，T2V，30s，1280x720，24fps，native audio。
- 用户当前 live-test 请求提供 task-scoped opt-in；Agent 设置单调用/项目 ceiling 50 CNY，max POST=1。
  只传原创文本，没有素材上传。Credential 只通过 injected Secret Service supplier，不记录值。
- 正式 Planner / verified projection / Router / compiler 保持完整 lineage。Director 文本进入
  `SubjectAction.progression`，不在编译后替换 prompt。使用 semantic `CameraIntent`，没有声称 v4 native camera control。
- 独立 `reviewer_xhigh` 给出 `accept with concerns`；已隔离非关键 transport 日志写入失败，避免截断已收到的响应。
- 仅一次 POST：06:18:23 UTC 开始，06:26:42 UTC 轮询观察到 `succeeded`，随后 canonical fetch。
  没有 retry、fallback、第二版生成、activation、P6 或 Final Acceptance。

## Artifacts And Provenance

Run root：`runs/director-seedance25-greenhouse-20260905-001/`。

- 原创 authoring：`director-coverage.json`、`authoring.md`、`prompt.txt`。
- 可追溯执行：`planning.json`、`plan.json`、`projection.json`、`routing.json`、`compiled.json`、
  `resolved.json`、`paid-preview.json`、`authorization.json`、`post-started.json`。
- Resolved request hash：`e46e4e8f49ef20fd78ed43e35eb414afe0a0126ef0cdfee90b4826b46772e97e`。
- Exact POST body SHA-256：`e116cef35a62d321c92ea10db88b906d2ef03d3a3b314b55efa77fb537c89435`。
- MP4：`production/state/video-generation/fetch/files/26a38204acef51d48bfe92f0d337bfee885629932efedd788358c91367c8679a.mp4`。
- MP4 SHA-256：`26a38204acef51d48bfe92f0d337bfee885629932efedd788358c91367c8679a`；40,462,083 bytes。
- Paid submit receipt：`production/state/paid-provider/submits/3e70204754678234aa8f9493bc78b7c601ca80128bca2267e3f2a755a4b062a5.json`。
- Paid gate：`production/state/paid-provider/gates/9e03ff969b9e3818e4d8eba7137c0c6f363a4724af049ede77644a6a84185bce.json`。
- 媒体证据：`fetched.json`、`mcp-review.json`、`mcp-frame-index.json`、`media-gate.json`。
  `review-audio.wav` 只是原始 MP4 的检查派生，不是 P4 composition / activated audio。

## Measured Results

Project-local `video-analysis` MCP probe 测得 H264 High / 1280x720 / 24fps / 721 frames，
container duration 30.08s，AAC 32000Hz stereo。音频电平 mean -30.9dBFS、peak -10.3dBFS。

| Requirement | Verdict | Evidence |
| --- | --- | --- |
| Technical output | PASS | 可解码 MP4，尺寸、帧率、近似时长、音轨符合测试目标 |
| Narrative progression | PASS | 苏醒 → 飞行 → 触碰 → 温室亮起/绽放四阶段均可见 |
| Camera coverage | PASS | 密集抽帧确认剪切落在 `(6.0,6.25]`、`(14.25,14.5]`、`(20.75,21.0]`，含微距、跟随、接触近景、全景升起 |
| Subject identity | PASS | 可辨识抽样画面保持同一铜色主体、透明翅膀、琥珀腹部；遮挡中的肢体数量未穷尽检查 |
| Physical action | PASS | 抽样起飞、穿行、下降/接触可读，未发现严重动作断裂；不是逐帧 anatomy 保证 |
| Visible payoff | PASS | 接触后花芯/根丝发光，再出现周围花卉绽放 |
| Exclusions | PASS | 已检查画面未发现人、字幕、商标或非预期主体替换 |
| Audio intent | NOT_EVALUATED | 有非静音音轨，MCP estimated speaking duration=0；当前模型不能接收音频，未听验声音与动作的对应关系 |
| Authored flower state | FAIL | 铜花在接触前已张开，未保持“闭合直到触碰”的明确创意状态 |

整体 Agent media gate 为 `FAIL`，不是全项验收通过。核心“不是单一简单慢推、具有叙事与景别变化”的
目标在这一条实片上得到支持；不把局部成功掩盖成完全 prompt adherence。

自动 `video_scene_detect` 与 `video_review` 均返回 scene_count=1，但 0.25s MCP 抽帧明确出现三次
剪切。此处以实际画面复核为准，不把自动数值当成语义 truth。`video_review.issues=[]` 同样不等于
所有创意要求通过，也不证明没有人声或声音贴合动作。

## Budget Boundary

本轮现场核对官方[价格页](https://docs.volcengine.com/docs/82379/1544106?lang=zh)：
720p、无输入视频为 70 CNY / million tokens；初估 648000 tokens / 45.36 CNY。
本次成功结果的 `usage.completion_tokens=648900`，乘此单价为 **45.423 CNY**。
这是 usage × public list price，不是已核对账单；本地 50 CNY reservation 也不是服务端财务硬上限。
没有按估价伪造 actual-cost settlement；budget reservation 保持保守记录。

## Verification And Repository Boundary

- Director schema-v3 validator 实际通过：4 units / 30s / missing / agent_directed / multi_shot。
- 离线 exact preflight 实际核对 `_payload(resolved) == expected-payload`、完整 Director 原文包含关系、
  `verify_current_video_generation_lineage`，均通过；这些不代替后续真实媒体证据。
- Provider/Manifest 保持 canonical writer；fetch 后 Manifest 2.7 / revision 17，video phase=`VALIDATE`，
  paid phase=`ACCEPTED`。没有激活 candidate 或将 Agent gate 写成 P6 / human acceptance。
- Run、task-scoped execution scripts、媒体与 sidecars 保持本地 runtime artifacts；本次未修改 Product source。
  本记录是 task-owned Git change；未收录其他窗口的 ComfyUI/compiler/文档修改，未 push、未 release。
  提交调用时 checkout HEAD 为 `4fea4407316793b7e331134c695ab0fba9bdcb9f`。
- 没有为记录额外运行 Provider、媒体或测试；记录的格式/identity 校验不充当新的 Harness / Product regression receipt。

## Learning Evaluation

`distill-ai-video-learning`: `no_candidate`。这是一个独立实片案例，没有旧路径对照臂，不能隔离
“修复”本身的因果效应，也不能外推 vague/draft prompt、其他题材或多次独立 Provider 调用。
检索并检查现有 Director 记录与 learning 目录，未发现可由该证据 material update 的同范围 claim。
铜花提前张开与声音未听验保留为 counter/未验证边界，不为了得到 PASS 改写 frozen intent。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| greenhouse-provider | seedance25:e46e4e8f49ef20fd78ed43e35eb414afe0a0126ef0cdfee90b4826b46772e97e | raw-director-greenhouse-20260905 | greenhouse-video-001 | N/A | 26a38204acef51d48bfe92f0d337bfee885629932efedd788358c91367c8679a | PROVIDER_TECHNICAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-seedance25-greenhouse-20260905-001/fetched.json |
| greenhouse-agent-media | seedance25:e46e4e8f49ef20fd78ed43e35eb414afe0a0126ef0cdfee90b4826b46772e97e | raw-director-greenhouse-20260905 | greenhouse-video-001 | N/A | 26a38204acef51d48bfe92f0d337bfee885629932efedd788358c91367c8679a | AGENT_VISUAL | FAIL | PROMPT_STATE_ADHERENCE | SAME_EVIDENCE_NEW_PROOF_LAYER | greenhouse-provider | runs/director-seedance25-greenhouse-20260905-001/media-gate.json |
