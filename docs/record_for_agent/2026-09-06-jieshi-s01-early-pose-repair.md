---
record_kind: media_experiment
topic_id: jieshi-s01-first-last-repair
learning_eligibility: eligible
evidence_index_version: "1"
---

# S01 Early Pose Repair And Gate Correction

Date: 2026-09-06

## Outcome

用户继续后先核对08封存请求，发现此前Gate仅按“3秒前抬起”判PASS，遗漏了请求中“2秒前达到末帧姿态并保持”。根据已查看的2秒掌心朝镜头、3秒才转正证据，把08整体NOT_EVALUATED纠正为FAIL。更新08 Gate、README及[08记录](2026-09-06-jieshi-s01-broadcast-onset-repair.md)，保留原媒体和请求。

新attempt09仅修改subject_action.progression：左手预先转为掌心朝玻璃，再连续抬起，1.5秒前到位并保持。same双图、广播、camera、compiler2、Vidu Q3 Pro、4秒1080p、audio=true和is_rec=false。Parent及reviewer_xhigh独立验证替回旧progression后完整prompt与08一致；pre-submit accept。未固定seed。

一次POST成功。Exact MP4 `7b249ddc7c535b36447b0804909059f2e54a74d0a73328dafe409db16a759302`，3,476,468 bytes；实测1080×1920、24fps、97帧、4.042秒、AAC48k stereo。初次下载public HTTPS DNS guard停止，既有GET-only恢复同一结果；无第二次生成。

Request `4aa13578f273965fe32ef02c82c90a1c9dbee9f8ea79cbbd0c92038f70c55911`，preview `4c676904169862a0eec2d3e9a036fb81582cafc2ec62fcfbe5adb30ce306bd4a`，POST body `966d267e4bf7525c7d54722d3a61ee0d21607a8b451345624693f21f5d0ac9e5`。

## Media Gate

Exact落盘立即调用project-local video_analyze并查看9张640px图，另video_transcribe请求word_timestamps；响应仍仅segment数组。广播为“林燕請在終點站下車”，0–2.24秒，前三秒完成的自动分析项PASS，不能冒称人工听觉验收或逐字时间。

1.5秒尚在抬起；2–3秒掌心朝镜头，末尾才转正。**整体FAIL / ACTION_ENDPOINT_TIMING与PALM_ORIENTATION**。其余逐项结果见`runs/jieshi-e01-i2v-20260906-attempt09/preparation-v1/shot-01-gate.md`。抽样未见对应倒影、构图漂移或烧字；不外推全帧或human quality。明确失败不需要继续增加dense evidence，也不进入S02、P6或activation。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s01-early-pose-gate | request:4aa13578f273965fe32ef02c82c90a1c9dbee9f8ea79cbbd0c92038f70c55911 | jieshi-s01-first-last-repair | jieshi-e01-s01-vidu-i2v-attempt09 | N/A | 7b249ddc7c535b36447b0804909059f2e54a74d0a73328dafe409db16a759302 | AGENT_REVIEW_OF_MCP | FAIL | ACTION_ENDPOINT_TIMING_AND_PALM_ORIENTATION | NEW_ATTEMPT | NONE | runs/jieshi-e01-i2v-20260906-attempt09/preparation-v1/shot-01-gate.md |

## Verification And Learning

Canonical bootstrap与strict reopen、typed profile/授权/双图receipt检查、唯一prompt变量断言、四脚本AST及diff check；结束复核MP4 SHA、phase=validate及单POST总数。未改core/依赖、未跑额外产品测试；用户禁止worktree，无fresh isolated Harness receipt。精确保存task-owned证据，保留七个unrelated staged files，未push。

按record-ai-video-session与distill-ai-video-learning完成评估：`no_candidate`。08/09出现同类提前到位失败，07是到位时间较早的counter，既有逐镜Gate已经要求按sealed intent实际时刻核验；当前问题是本次评估遗漏严格条目。没有证据支持进一步的通用重试/强制换模型规则，也不需要重复创建既有Gate的adoption owner。保留实测历史，未修改既有烧字pending claim。沿用已完成的experience stale advisory检索，不重试RAG或刷新索引。

## Next Boundary

本次max_submit_count=1已消费，known outcome。不得反复同类提示词重抽、复用permit或把末帧正确当成3秒剪辑可用；下一方案需解决动作轨迹/到位时间控制，并准备新exact请求及适用授权。记录阶段未额外调用Provider、生成媒体或运行测试。
