---
record_kind: media_experiment
topic_id: jieshi-s01-first-last-repair
learning_eligibility: eligible
evidence_index_version: "1"
---

# S01 Broadcast Onset Repair

Date: 2026-09-06

## Verdict Correction — 2026-09-06

后续继续时重新核对封存request：要求第2秒前达到末帧姿态并保持，08在2秒仍掌心朝镜头、约3秒才转正。此前以before3s抬起判PASS遗漏了更严格时序，整体结论应为 **FAIL / ACTION_ENDPOINT_TIMING**，下文NOT_EVALUATED为被纠正的历史评估。广播0–2.14秒及原MP4数据不变；纠正未激活状态，后续attempt09仅改动作表述。

## Outcome

用户在07后要求继续，完成一次新Vidu Q3 Pro首尾帧attempt08。唯一创作变量为广播从第0秒起声、连续偏快播报、目标2.2秒前结束；句子内容、动作、相机、已批准双图、compiler2、4秒1080p、audio=true及is_rec=false保持原样。reviewer_xhigh pre-submit accept；未固定seed，单次结果不证明因果保证。

Request `65958875804c478f4094e57f6f60ebe5dd976a930e92f9a0969d6a71b9272bc7`，preview `f84ed73f4c1fdadf702774665ef258d4a59794833aa69ba45e5396d765e2459e`，POST body `7fcfbb100f8b4252942802bbc0dd9847af96cf1ba913daa4ca71645d0484ac56`。

Exact MP4 `cc522e481994be961e585a95b618887a4f06b192fa9ae85b1c359e87474c194e`，3,232,566 bytes，1080×1920、24fps、97帧、4.042秒、AAC48k stereo。一次POST成功；首次fetch被public HTTPS DNS guard阻断，既有GET-only public-DNS恢复下载同一结果，没有第二次生成。严格reader复核phase=validate、文件SHA和单POST事件通过。未activation、未S02。

## Media Evidence

Exact落盘立即project-local video_analyze，随后video_transcribe(word_timestamps=true)及dense extraction；Agent查看9张640px大图、ffmpeg顺序97帧的5张contact sheets。粗ASR为0–2秒，复核segment为0–2.14秒，“林燕,請在終點站下車”。MCP未暴露逐词数组，只能报告segment对齐，不能冒称人工听过或已得到每字时间。

本版广播前三秒完成在自动分析层PASS，替代07的晚结束作为当前候选观察。相机固定、七人保留、真实左手、右手手机、可见范围无对应倒影、无烧字PASS。2秒手掌朝镜头，随后翻腕，约3秒转为手背朝镜头；全速自然度尚无确认。约2cm间隙、胸牌细节、全速音频听感和canonical final narrative subtitle仍NOT_EVALUATED。因此**整体Gate NOT_EVALUATED**，不是成功验收。

完整逐项表与分析原始结构在`runs/jieshi-e01-i2v-20260906-attempt08/preparation-v1/`；MP4、contact sheets和完整runtime state留在local runs。没有为保存记录额外调用Provider或生成媒体。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s01-onset-repair-gate | request:65958875804c478f4094e57f6f60ebe5dd976a930e92f9a0969d6a71b9272bc7 | jieshi-s01-first-last-repair | jieshi-e01-s01-vidu-i2v-attempt08 | N/A | cc522e481994be961e585a95b618887a4f06b192fa9ae85b1c359e87474c194e | AGENT_REVIEW_OF_MCP | NOT_EVALUATED | REQUIRED_EVIDENCE_INCOMPLETE | NEW_ATTEMPT | NONE | runs/jieshi-e01-i2v-20260906-attempt08/preparation-v1/shot-01-gate.md |

## Verification And Learning

四个attempt脚本AST parse、canonical bootstrap/strict reopen、pre-submit independent review、最终strict phase/hash/POST count及diff check。未改产品core或新增依赖；未运行额外产品测试，用户禁止worktree，无fresh isolated Harness receipt。保留七个unrelated staged files，未push。

按record-ai-video-session执行distill-ai-video-learning评估：`no_candidate`。新广播起声表达只有一次样本且没有固定seed的controlled arms，07提供旧表达的超时counter；不能推出该改写稳定保证达标。head-tail多例无烧字仍不改变既有first-frame-only pending claim的限定范围，未采纳任何target。沿用已完成experience检索的stale advisory结果，当前判断依据exact文件，未刷新RAG。

## Next Boundary

本次max_submit_count=1已消费。保留08候选，先请求对exact MP4的全速动作和广播听感判断，并补足其余required evidence；不能把静帧/ASR通过转换成human acceptance，也不能因缺证据自动重抽或提交S02。旧07失败及其历史数据不变。
