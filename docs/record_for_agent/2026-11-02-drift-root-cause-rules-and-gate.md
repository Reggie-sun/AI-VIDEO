---
record_kind: session_summary
topic_id: drift-root-cause-rules-and-gate
learning_eligibility: ineligible
---

# Drift Root Cause: Preview Approval And Identity Gate

Date: 2026-11-02 (work began 2026-10-30)

## Trigger

用户看完调度蒙太奇现场画面评价“这不是明显是一拖史吗……反思下”，指出“为什么都是1,2张referces”，并要求“除了长期记忆……修改下规则和程序，得先修复你跑偏的原因”。

## Root Causes (Parent self-diagnosis)

- 纸上定稿（分镜文字 + 只读文字的 Concept Check）后直接付费生成，用户从未先看到可视预览。
- 每镜只用 1–2 张参考，把“不为填满上限追加”误读成越少越好；未用身份/分镜参考 Skill。
- Planner 要求身份参考时，把可见表演者移出 `identity_continuity` 绕过门禁。
- 逐镜 Gate 把未达成项写成“PASS 但有偏差”继续推进；画面异常只靠台词，人物全背对、不反应。

## Changes (commit 64da83d; partial state earlier in 43c330b)

- 程序：剧情新生成须绑定封存的 `reference_planning.preview_approval`（`user-preview-approval/1`：coverage hash、unit、预览图 path/sha、用户原话、可选 `identity_waivers`）；所有领域可见表演者须在 `identity_continuity`、有 `priority=required` 的身份 anchor，或有 `identity_waivers` 且该豁免列入用户认可的预览；optional anchor 不能降级已声明的身份义务。新字段为空不序列化，历史 hash 不变。
- 规则：AGENTS.md（剧情付费前先交预览取得认可；封存要求未达即 FAIL、改判须用户决定、观感不由 Agent 判）、open-video、creative-completion、seedance-authoring、shot-reference-planning（参考包组成与已知缺口）、contract matrix；Harness 映射新模块（并按用户决定一并提交另一会话的 dotenv 映射）。
- 独立审查（sonnet code-reviewer）首轮 REQUEST_CHANGES（preferred anchor 绕过、豁免无用户约束等），修复后验证通过。

## Verification

Harness focused `.agent/harness/runs/20261102T055224283437Z/receipt.json`、related `.agent/harness/runs/20261102T062042437796Z/receipt.json`、full `.agent/harness/runs/20261102T070028676620Z/receipt.json`，均 passed，exact staged snapshot。

## Coordination Notes

- 16:05 的 “all” 提交（43c330b）把本任务未完成的中间态连同 1,128 个其他文件推上 main，期间 main 上大量 fresh-generation 测试失败，由 64da83d 修复；未改写历史。
- 另一并行会话（可能为 Codex）在同一审查意见上修改了 reference_planning.py 等文件并改动两个测试 hash；用户决定由 Parent 以实测值更新。混合文件只提交本任务行，其他会话的未提交段落已原样还原。

## Remaining Risks / Next

- 已知缺口：身份义务未与 Shot `character_ids` 交叉核对；预览图 sha 未与实际送模参考核对；执行绑定无 Project 时仅结构检查。
- `docs/canvas-projects/subject-reference/project.json` 无预览认可，真实运行会被门禁拦下；不得伪造用户认可。
- 调度蒙太奇创作需按新流程重做：先出参考包关键帧预览给用户。

`record-ai-video-session`：recorded；`distill-ai-video-learning`：no_candidate（规则已由用户直接要求修订）。
