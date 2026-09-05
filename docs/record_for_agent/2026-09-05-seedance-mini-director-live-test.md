---
record_kind: media_experiment
topic_id: raw-creative-director-seedance-mini
learning_eligibility: eligible
evidence_index_version: "1"
---

# Seedance Mini Director Live Test

Date: 2026-09-05

## Purpose And Scope

用户认可上一条 Seedance 2.5 温室实片后要求“再测试下用mini”。沿用铜制机械萤火虫
苏醒、飞行、接触铜花、光波激活温室的原创故事。`retrieve-ai-video-memory` 先检索历史
Mini evidence，再由 `open-video` 调整 pacing、`seedance-authoring` 应用 Mini 2.0 overlay。
原始创意来源保留 `missing`，策略为 `agent_directed / multi_shot`；不是按时长阈值强制拆镜。
四个 coverage units 编入单个 Production Shot、单次 Provider POST。

本次 selected model 为 `doubao-seedance-2-0-mini-260615`，official Ark / T2V / 720p / 24fps /
native audio。Mini 当前原生上限 15s，已向用户披露将同故事压缩为目标 15s、3/4/3/5s coverage。
它与前次 30s 2.5 并非同 prompt、等时长的受控 A/B，不据此宣称模型整体优劣。

## Preflight And Execution

- `runs/director-seedance-mini-greenhouse-20260905-001/` 的 nominal 15s 离线预检被 Router
  `blocked_capability` 阻断：当前 `OutputNeed` 无 `nominal_seconds`，
  `_video_requirement_routing.py::requirement_output_matches` 无该 timing mapping。
  该 run 零 POST，保留证据；本轮没有修改产品代码来修复此接口缺口。
- 新独立 run `runs/director-seedance-mini-greenhouse-20260905-002/` 使用已支持的
  `provider_selected`，effective duration=null、actual payload duration=-1；15s 是创作目标，
  不是伪造 exact-duration lineage。正式 Planner / verified requirement / pre-generation graph /
  Router / compiler / resolved / paid gate 保持完整，Router 实际 selected。
- 离线核对 actual payload 等于 sealed preview、完整 Director 文本进入编译 prompt、
  `verify_current_video_generation_lineage`、egress 与 authorization，均通过。
  native `reviewer_xhigh` 对 `002` 的独立预提交复核 verdict 为 `accept`。
- 用户本次请求提供 task-scoped opt-in；8 CNY 单调用/项目 reservation，max POST=1。
  仅传原创文本及生成设置，无参考媒体上传；credential 仅由 injected supplier 读取，不落盘不回显。
- 07:33:55 UTC 的唯一 POST 返回 200；07:37:35 UTC 的 GET 观察到 succeeded；
  07:37:36 UTC canonical fetch 完成。无 retry、fallback、追加 variant 或 activation。

## Exact Evidence

以下相对路径均以 `runs/director-seedance-mini-greenhouse-20260905-002/` 为根：

- Authoring：`director-coverage.json`、`prompt.txt`、`authoring.md`。
- Sealed lineage：`planning.json`、`plan.json`、`projection.json`、`routing.json`、`compiled.json`、
  `resolved.json`、`expected-payload.json`、`paid-preview.json`、`authorization.json`。
- Resolved request hash：`a8fe8c538200fb9a16ec1f82cb1dfbfd15b26d3b42d57f7222d5e72f5627d0ff`。
- Attempt：`greenhouse-mini-video-002`；generation：`greenhouse-mini-generation-002`。
- Paid submit receipt：`production/state/paid-provider/submits/5fc530881f773e5ce83179db63c156b27ffdf8ecab82c32ce6a975af32e92894.json`。
- Exact MP4：`production/state/video-generation/fetch/files/1c033786221ed269f4872be4d9fdef61ccc75b378d04095a044a0809df57b564.mp4`。
- SHA-256：`1c033786221ed269f4872be4d9fdef61ccc75b378d04095a044a0809df57b564`；9,746,506 bytes，fetch receipt 与现场 hash 一致。
- 检查 sidecars：`fetched.json`、`mcp-probe.json`、`mcp-review.json`、`mcp-frame-index.json`、`media-gate.json`。

## Measured Results

Project-local `video-analysis` MCP 实际测得 H264 High、1280x720、24fps、361 frames、
container duration 15.104s，AAC 32000Hz stereo。原始文件音频 mean -23.3dBFS、peak -4.0dBFS。
Agent 检查 1s 抽帧及剪切/接触区间的 0.25s 密集帧，不声称逐帧动作或 anatomy 全检。

| Requirement | Verdict | Evidence |
| --- | --- | --- |
| Technical output | PASS | 可解码，尺寸/帧率/原生音轨与目标相符；时长为实测值 |
| Narrative progression | PASS | 苏醒 → 飞行 → 接触 → 根部光波与温室绽放均可见 |
| Camera coverage | PASS | 剪切在 `(4.5,4.75]`、`(6.5,6.75]`、`(9.5,9.75]`；微距、跟拍、接触近景、全景后拉 |
| Subject identity | PASS | 抽样保持铜色身体、透明翅膀、琥珀腹部；不是遮挡下全部肢体数量保证 |
| Physical action | PASS | 起飞、飞行、下降接触动作在抽样中可读 |
| Authored flower state | PASS | 8s 接触时主体花苞仍闭合，8.5–9.25s 打开；底座外层瓣原本外翻不等于主体花苞提前绽放 |
| Visible payoff | PASS | 接触后根丝逐步亮起，11–15s 周围花卉相继绽放 |
| Exclusions | PASS | 检查画面未发现人、文字、商标或主体替换 |
| Native audio track | PASS | 存在非静音 AAC stereo |
| Audio intent | NOT_EVALUATED | 当前模型不能听验；ASR estimated speaking duration=0 不能证明音效贴合或绝对无对白 |

整体 Agent gate 为 `NOT_EVALUATED`，未声称全项通过。核心自主导演覆盖在本条实片得到支持。
自动 scene_count=1、issues=[] 不作为语义结论；实际抽帧显示三次剪切。自动 quality metrics
的 sampled_frame_count=487 与源视频 361 frames 不同口径，不据此声称逐源帧检测。
上一条铜花提前张开的偏差在本条未复现，但不同模型/时长/prompt 的变化不能隔离原因。

## Cost And Lifecycle Boundary

现场核对官方[价格页](https://docs.volcengine.com/docs/82379/1544106?lang=zh)：Mini 无视频输入
原价 23 CNY/million tokens，页面同时显示限时4折。成功结果 usage.completion_tokens=324900，
按原价换算 **7.4727 CNY**；这不是已核对账单，也没有用估价伪造 actual-cost settlement。
8 CNY 本地 reservation 不等于服务端财务硬上限。没有新的 paid call 发生在记录阶段。

fetch 后保留 canonical Manifest 的 video `VALIDATE` / paid `ACCEPTED`，未激活 candidate、
未签发 P6 或 Final Acceptance。原始 MP4 不是 P4 composition 或已验收交付状态。
本轮仅产生 task-owned 本地 run artifacts 与 Git 文档记录；没有 Product source change。
未提交运行脚本/媒体、未触碰 unrelated 工作、未 push/release，也未单独刷新 RAG index。

## Learning Evaluation

`distill-ai-video-learning`: `no_candidate`。已检索并重新打开上一条 2.5 实片记录和历史 Mini
continuity evidence，检查当前 learning 目录；没有同范围 active claim 需要 material update。
两条温室样本支持“本次方案能输出多景别”的窄观察，但没有旧路径对照、等时长同 prompt
控制或新的可归因 adoption action，不能推出 Mini 更好、修复必然提高质量或固定时长拆镜规则。
名义时长路由缺口仅一次离线复现；花状态有前次 counter evidence，音效仍未听验。保留记录，
不创建泛化质量 claim 或自动修改 Skill/Preflight/Gate。

## Verification And Publication

Director schema-v3 validator、canonical preflight、单次 live submit/fetch 与上述 MCP 检查已实际执行。
记录按 documentation-only scope 做 evidence identity、docs contract 与 whitespace 校验，
并由 Harness 对 exact staged snapshot 执行该类别 mandatory checks；不增加 Provider、媒体或完整测试。
上一条记录仅补充用户正面反馈及本次独立实验链接，保留其历史 FAIL / NOT_EVALUATED。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mini-provider | seedance-mini:a8fe8c538200fb9a16ec1f82cb1dfbfd15b26d3b42d57f7222d5e72f5627d0ff | raw-director-mini-greenhouse-20260905 | greenhouse-mini-video-002 | N/A | 1c033786221ed269f4872be4d9fdef61ccc75b378d04095a044a0809df57b564 | PROVIDER_TECHNICAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-seedance-mini-greenhouse-20260905-002/fetched.json |
| mini-agent-media | seedance-mini:a8fe8c538200fb9a16ec1f82cb1dfbfd15b26d3b42d57f7222d5e72f5627d0ff | raw-director-mini-greenhouse-20260905 | greenhouse-mini-video-002 | N/A | 1c033786221ed269f4872be4d9fdef61ccc75b378d04095a044a0809df57b564 | AGENT_VISUAL | NOT_EVALUATED | AUDIO_INTENT_NOT_EVALUATED | SAME_EVIDENCE_NEW_PROOF_LAYER | mini-provider | runs/director-seedance-mini-greenhouse-20260905-002/media-gate.json |
