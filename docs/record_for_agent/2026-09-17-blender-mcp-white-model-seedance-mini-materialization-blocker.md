---
record_kind: media_experiment
topic_id: blender-mcp-white-model-seedance-mini-reference
learning_eligibility: eligible
evidence_index_version: "1"
---

# Blender MCP White-Model To Seedance Mini Materialization Blocker Record

Date: 2026-09-17

## Purpose

本文记录用户纠正测试意图后的一次 bounded execution：白模不是由 Seedance 生成，而是由
`blender-mcp 1.8.7` 控制本地 Blender 5.2.1 LTS 制作；只有 exact local MP4 通过 Gate 后，才准备
交给 `doubao-seedance-2-0-mini-260615` 的 AI-VIDEO project API
`reference_to_video` path。

本记录证明本地 MCP authoring、render、asset validation 与 exact-byte source Gate 已完成，也记录
为什么项目在 paid Provider submit 前 fail closed。它不证明 Seedance 已接受本次白模 reference，
不构成 Provider capability PASS、candidate activation、P6、Final Acceptance 或 publication evidence。

## Corrected Execution Contract

- Source owner：local Blender MCP；Seedance 不生成白模。
- Blender transport：`blender-mcp 1.8.7`，addon protocol `4`，Blender `5.2.1 LTS`；telemetry disabled。
- Source action：opening hold -> subject-right arm lateral raise to shoulder height -> torso/head turn
  subject-right while the arm remains raised。
- Camera/scene：locked orthographic camera、head-to-toe framing、neutral studio floor、single matte-white
  articulated geometric mannequin、无文字、无音频。
- Target Provider/model/mode：`volcengine_ark_seedance` /
  `doubao-seedance-2-0-mini-260615` / `reference_to_video`。
- Reference job：只 transfer 动作节奏、肢体轨迹、站位与固定机位；不得 transfer 白模材质、方块
  比例、neutral background 或 silence。
- Remote submit ceiling：本 corrected task 最多一个 target POST；没有 retry 或 fallback。由于
  materialization preflight 未通过，实际 POST 为 `0`。

## Blender MCP Execution

正式 run 为 `runs/seedance-blender-white-model-r2v-20260917-001/`。

MCP status 证据确认 addon 与 server protocol 一致，并暴露 `execute_blender_code`、
`get_scene_info`、`get_object_info` 与 viewport screenshot 等能力。建模与渲染代码通过
`execute_blender_code` 进入 Blender，不是以 headless CLI authoring 冒充 MCP control。

第一版 diagnostic render 暴露人物 framing 缺陷：抬臂后人物偏左，头顶和脚部被裁切。随后只调整
orthographic camera framing，并重新执行 MCP create/render。最终 source：

- `.blend`：`runs/seedance-blender-white-model-r2v-20260917-001/source/white-model-motion.blend`
- `.blend` SHA-256：
  `ae4d1cbd4416d0cb988020862ac43019ba82185c2edecc98b7501084b504113d`
- MP4：`runs/seedance-blender-white-model-r2v-20260917-001/source/white-model-motion.mp4`
- MP4 SHA-256：
  `b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1`
- measured bytes：`58,505`
- measured media：H.264 High、`1280x720`、`yuv420p`、24fps、120 frames、`5.000s`、无音轨
- source contact sheet：
  `runs/seedance-blender-white-model-r2v-20260917-001/evidence/source-contact-sheet.jpg`
- contact-sheet SHA-256：
  `ce826a425421c4e543510c0f47bd5e53a97cd643de8ffa8735e13fe94f5aaa2d`

Blender Agent Studio fresh-process inspection 报告 `hard_gate_pass=true`，没有 asset issue，并确认
`HeadTurnPivot`、`RightShoulderPivot`、`TorsoTurnPivot` 三条 action 覆盖 frame 1-120。标准 multiview
与 critical-frame evidence 位于 `evidence/multiview/`。

## Exact-Byte Source Gate

project-local `video-analysis` 对 exact MP4 的 probe、scene detection 与 sampled-frame review 均已执行。
`evidence/local-source-gate.json` 的 required findings：

| Required finding | Verdict | Exact evidence |
| --- | --- | --- |
| `technical_output` | `PASS` | exact MP4 可解码；H.264 High、`1280x720`、24fps、120 frames、`5.000s`、无音轨。 |
| `white_model_subject` | `PASS` | critical frames 均为单个 matte-white articulated geometric mannequin 与 neutral studio floor。 |
| `motion_sequence` | `PASS` | frame 1/48 hold；frame 84 完成 subject-right arm raise；frame 120 保持抬臂并完成 subject-right torso/head turn。 |
| `fixed_full_body_camera` | `PASS` | head、hands、feet、全部肢体、floor contact 与 headroom 在四个 critical frames 中持续可见。 |
| `no_text_or_cuts` | `PASS` | scene detection 为 1 scene；visual inspection 未见文字、字幕或 logo。 |
| `reference_readiness` | `PASS` | exact local MP4 可作为 motion-only reference；本结论不证明 Provider transport acceptance。 |

## Project API Materialization Blocker

Current code 只实现两条 Seedance video-reference lane：

1. `SeedanceAssetMaterializationReceipt -> SeedanceAssetReferenceResolver -> asset://...`，要求 exact
   local binding 已由 Ark Console `Active` asset 和 human-observed confirmation evidence 封存。
2. `RemoteMediaMaterializationReceipt -> SeedanceRemoteReferenceLease -> exact HTTPS locator`，仅接受
   Seedance 自己已 fetch 的 provider output，并要求 current active source、one-use refresh permit、
   locator origin/expiry 与 exact bytes revalidation。

Current runtime 没有 local MP4 object-storage upload、Ark `CreateAsset` automation、general Files API、
presigned URL publisher 或另一条可把本次 Blender bytes 物化为受支持 identity 的 canonical path。
登录状态、Experience 临时上传、本地 path 或任意 public URL 都不能替代 receipt，也不能绕过
`SeedanceVideoProvider` 的 exact resolver type checks。

因此本轮以 `BLOCKED_BEFORE_PAID_SUBMIT` 停止：

- Ark/Seedance upload：`0`
- Seedance generation POST：`0`
- poll/fetch：`0`
- Provider MP4：`NONE`
- candidate/activation/P6/Final Acceptance：`NONE`
- outcome unknown：`false`
- blind retry/fallback/browser generation submit：`false`

这不是“Seedance Mini 拒绝白模”的 empirical verdict；它是当前项目缺少 exact local-video
materialization seam 的 deterministic blocker。

## Assessment

用户纠正的 Blender-first source path 已完成，且相对于同日两个误解后的 Seedance T2V attempts，
本次不再消耗 Provider 调用来生成白模。能够继续的最小下一动作不是再次 T2V，也不是在 Experience
页面直接生成，而是取得本次 exact MP4 的 `Active asset://...` materialization receipt，或另行批准并
实现受约束的 local-video publisher/materializer contract。

在任一路径完成前，不能把 local Gate `PASS` 转换为 Seedance reference acceptance。即使未来 Provider
submit succeeded，仍需下载 exact output 并执行新的 post-media Gate，才能评估 motion transfer。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| blender-mcp-white-model-source | blender-mcp:white-model:b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1 | seedance-blender-white-model-r2v-20260917-001 | blender-mcp-white-model-source-attempt | local-source | b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1 | LOCAL_MCP_AUTHORING_AND_EXACT_MEDIA_GATE | PASS | NONE | NEW_ATTEMPT | NONE | runs/seedance-blender-white-model-r2v-20260917-001/evidence/local-source-gate.json |
| seedance-mini-local-video-materialization | blender-mcp:white-model:b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1 | seedance-blender-white-model-r2v-20260917-001 | blender-mcp-white-model-source-attempt | local-source | b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1 | PROJECT_API_MATERIALIZATION_PREFLIGHT | BLOCKED | LOCAL_VIDEO_MATERIALIZER_NOT_IMPLEMENTED | SAME_EVIDENCE_NEW_PROOF_LAYER | blender-mcp-white-model-source | runs/seedance-blender-white-model-r2v-20260917-001/evidence/materialization-preflight.json |

## Learning Evaluation

`distill-ai-video-learning`: `no_candidate`。本次 correction 只有一个新的 independence unit；本地
source Gate PASS 与 materialization blocker 是同一 attempt 的不同 proof layers，不能当作两个独立
实验。关于“本地素材 path 不能冒充 Ark/provider identity”的规则已经由 current exact resolver 与
repository invariants 直接拥有，不需要另建 Learning Claim。

## Agent Guardrails

- 不得回到 Seedance T2V 生成白模；这不是用户当前 intent。
- 不得把 Blender MCP/local Gate success 描述成 Seedance input acceptance。
- 不得用 Experience page generation、匿名临时 host、local path 或 local Registry ID 绕过 project API
  materialization contract。
- 不得伪造 human-observed `Active` Ark asset receipt，或把 login state 当成 materialization evidence。
- materialization 完成后仍只能执行一个 task-scoped Mini target submit；结果必须按 exact MP4 Gate
  重新验证，不能从 Provider `succeeded` 推导 quality acceptance。
