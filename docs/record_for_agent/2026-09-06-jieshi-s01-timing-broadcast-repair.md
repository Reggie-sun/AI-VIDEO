---
record_kind: media_experiment
topic_id: jieshi-s01-first-last-repair
learning_eligibility: eligible
evidence_index_version: "1"
---

# S01 Timing And Broadcast Repair

Date: 2026-09-06

## Outcome

用户在attempt05失败后要求“继续”。本轮完成一次新的Vidu Q3 Pro首尾帧提交，exact MP4 `041de54a023082c24cb2d4cced4ba8d068569aebdf3330496f40615eaa9ae2a4`，4,111,052 bytes，1080×1920、24fps、97帧、4.042秒、AAC48k stereo。

落盘立即调用project-local `video_analyze`，9个0.5秒样本、Whisper medium、scene detection。左手约2.5秒达到正确掌向，比05迟到改善；ASR在0–2.6秒识别“林燕,請在終點站下車”，与指定句子读音一致，但未据ASR宣称完整听觉验收。中段机位明显位移/缩放，最右乘客进一步裁切，**Gate FAIL**。无activation、无accepted continuity source、无S02。

## Request And Controlled Scope

- Request `94120c86894dec85b0a4dfdd0dea81f7d17dd6a42d6e1690c976be6dd7638288`。
- Preview `6a9d3787a27b7dd3d4ad0709b10881c77e779c581d7d86212365ccb252952792`。
- POST body `cb0883b014a49665f8f8083ee9a64884a48ac8cccf2fe6a2306ba672b02fb670`。
- 首帧 `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`，末帧 `059bb2b261883190168057b35baafc90011866acba9fb64b1c9c186122861330`，沿用两份真实批准回执，不新造human attestation。
- 保留Provider/model、4秒1080p、native audio、compiler2、`is_rec=false`。变化仅在authored expression：明确0–2秒动作、2–4秒保持，广播原句单独精简。未固定seed，不将变化拆成某一词的因果结论。
- 前置medium ASR复核05得到空转录，仍为NOT_EVALUATED，不代表静音，证据在 `runs/jieshi-e01-i2v-20260906-attempt06/prior-audio-recheck.json`。

## Canonical Execution And Verification

新增attempt06脚本，未修改产品core。Bootstrap首次遗漏末帧receipt引用的历史Shot文件，在写入前typed reject；按既有bootstrap owner要求补齐exact引用bundle，空目录下明确重试后canonical bootstrap/strict reopen PASS，没有media effect或unknown outcome。Planner/readiness→Router→compiler→preview保持原seam。

Native reviewer_xhigh对当前request/preview/Manifest/Registry/receipt/authorization及profile续期独立审查accept；上限金额不变，有效时间真实续期，max_submit_count=1。唯一POST成功，Provider known succeeded。初次下载触发public HTTPS guard后，以既有GET-only DNS recovery取得同一任务文件；没有第二POST。一次submit quota已消费，保持fetched/validate，不复用permit、不增加额度。

四个脚本AST parse、`git diff --check`通过；最终strict loader、exact MP4 SHA及事件POST计数复核。未运行额外单元测试或isolated Harness；用户禁止worktree，不声称fresh Harness receipt。保留七个既有staged run files及其他会话changes，未push。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s01-timing-broadcast-gate | request:94120c86894dec85b0a4dfdd0dea81f7d17dd6a42d6e1690c976be6dd7638288 | jieshi-s01-first-last-repair | jieshi-e01-s01-vidu-i2v-attempt06 | N/A | 041de54a023082c24cb2d4cced4ba8d068569aebdf3330496f40615eaa9ae2a4 | AGENT_REVIEW_OF_MCP | FAIL | CAMERA_FRAMING_DRIFT | NEW_ATTEMPT | NONE | runs/jieshi-e01-i2v-20260906-attempt06/preparation-v1/shot-01-gate.md |

## Learning Evaluation

使用retrieve-ai-video-memory experience scope，得到stale advisory片段；未等待、重试或重建索引。匹配higgsfield-prompt仅作提示词建议，canonical truth保持仓库owner。

按distill-ai-video-learning重新评估：`no_candidate`。两次首尾帧实验的主失败不同（05动作迟到，06机位漂移），05采样机位相对稳定，反对把06现象写成必然行为；广播改善仅此一次，不是受控比较。既有first-frame-only烧字claim的范围不含此endpoint，且此处文字检查未达全帧PASS，因此不伪造counter验收、不更新或采纳其target。记录真实不同结果，保留未验证边界。

## Next Boundary

当前S01仍未完成。后续有界修复应针对中段机位/构图，保持已经改善的动作与广播表达；不能把首尾帧约束当作已实现的全程镜头锁定。任何新调用仍需新exact request/preview/intent/permit及有限quota，下一Shot必须等待全部required findings PASS。
