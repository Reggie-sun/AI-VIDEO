---
record_kind: media_experiment
topic_id: jieshi-s01-first-last-repair
learning_eligibility: eligible
evidence_index_version: "1"
---

# S01 Camera Constraint Repair

Date: 2026-09-06

## Continuation Notice — 2026-09-06

后续attempt08已完成广播起声修复实验，见[08记录](2026-09-06-jieshi-s01-broadcast-onset-repair.md)。08 ASR segment结束约2.14秒；其整体结论后来因遗漏sealed action时序而纠正为FAIL，attempt09同样动作FAIL，见[09记录](2026-09-06-jieshi-s01-early-pose-repair.md)。下文07的FAIL和测量保留为历史，不代表后续广播仍超时；下文“后续需处理广播启动/结束时间”已由08实验推进。

## Outcome

用户在06失败后要求“jixu”。完成一次Vidu Q3 Pro首尾帧生成并canonical fetch，exact MP4 `88d3a8ed59550c706e176da88e1d7ef89c02a1e60a5f6e1546b112507d0cd93e`，3,350,152 bytes，1080×1920、24fps、97帧、4.042秒、AAC48k stereo。

本次只改camera_intent.stability/framing_intent文字，明确车厢相对固定相机、固定光轴/焦距/裁切/背景位置。独立reviewer_xhigh验证替回两段旧值后完整compiled prompt与06相同；两张已批准图片、动作和广播文字、compiler2、model、audio/is_rec、输出规格保持原样。seed未固定，不证明因果。

Request `593e3c56176d80fc97e3c1bba9c10f9ef4196206b1b4ddbb887fb947ec965c11`，preview `c9d053e3f2821cad9257bba4e9ab3c3508f3f6d87564330e1908c9e341a9b4ea`，POST body `62fe2899d163bf9f970dbca14fb0613efb00995f984539b0613af134c8398139`。新profile仅续期内部上限有效时间，额度1；canonical bootstrap/strict reader与typed授权/receipt关联全部通过，review accept。一次POST成功，首次下载触发public HTTPS guard后GET-only DNS恢复同一任务，未重复生成。

## Media Evidence

Exact落盘立即project-local video_analyze（9帧640px、medium ASR、scene detection）；然后EVIDENCE_REPAIR_FIRST补MCP dense extraction和word_timestamps。顺序97帧另用现有ffmpeg生成5份5×4 contact sheets，Agent全部检查并结合9张大图。旧ffmpeg不支持fps_mode、系统路径不存在、缺默认字体的离线尝试均无输出；改用实际conda binary、vsync0、无字体tile成功，未改变原视频。

机位/构图、约2秒完成的真实左手动作、右手手机位置、七人保留、可见范围无对应人脸/身体/手镜像和无烧字观察PASS。广播粗转录0–4秒，细化后0.84–3.40秒，文字为“林彥,請在終點站下車。”；读音相符但结束超时，**Gate FAIL**。约2cm距离、胸牌、全速混音及final narrative subtitle仍NOT_EVALUATED。不是human acceptance、P6或Final Acceptance；无activation、无S02。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s01-camera-repair-gate | request:593e3c56176d80fc97e3c1bba9c10f9ef4196206b1b4ddbb887fb947ec965c11 | jieshi-s01-first-last-repair | jieshi-e01-s01-vidu-i2v-attempt07 | N/A | 88d3a8ed59550c706e176da88e1d7ef89c02a1e60a5f6e1546b112507d0cd93e | AGENT_REVIEW_OF_MCP | FAIL | BROADCAST_TIMING | NEW_ATTEMPT | NONE | runs/jieshi-e01-i2v-20260906-attempt07/preparation-v1/shot-01-gate.md |

## Verification And Learning

四个脚本AST parse、diff check、canonical strict fetched/validate、exact MP4 SHA、单POST事件复核。未改产品core、未新增测试或依赖；用户禁止worktree，无fresh isolated Harness receipt。保留其他staged/dirty changes，未push。

沿用此前experience检索的stale advisory结果，不为刷新而重试RAG；当前判断来自新exact证据。record-ai-video-session后distill-ai-video-learning评估 `no_candidate`：镜头修复成功仅此一次，06为失败counter，05为另一表达下相对稳定；未固定seed，不能把paired观察写为已证实因果。现有烧字pending claim范围明确为first-frame-only三例，本次head-tail无字样本属于不同endpoint，不擅自扩展其scope或采纳target。完整Gate仍失败，不得提出整体成功claim。

## Remaining Boundary

一次新submit已消费；后续需处理广播启动/结束时间并补其余required evidence。不可把视觉改善视作S01整体接受或自动授权S02，亦不可复用permit、续期重置额度或进行未知结果重试。
