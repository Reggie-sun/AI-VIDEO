---
record_kind: session_summary
topic_id: jieshi-s01-first-frame-readiness
learning_eligibility: ineligible
---

# Jieshi S01 First-Frame Readiness Block

Date: 2026-09-06

## Supersession Notice

本记录的“readiness阻塞、未有新提交”已由[后续有界修复与Vidu逐镜证据](2026-09-06-jieshi-s01-vidu-i2v-live-gate.md)取代。
`80b5ffe` 修复首镜显式first_frame，已完成唯一一次Vidu I2V提交、下载和MCP分析；
当前停止原因是媒体Gate FAIL，不再是输入接入阻塞。以下保留历史准备过程。

## Scope And Result

继续既有《界蚀》第一集 52 Shot / 300 秒创作包，只处理 S01 首帧驱动请求。新准备目录为 `runs/jieshi-e01-i2v-20260906-attempt01/`；详细事实与准确 evidence 文件见其 [README](../../runs/jieshi-e01-i2v-20260906-attempt01/README.md)。本轮停于真实 `ShotReadinessGate`，没有新的生成提交、MP4、intent、permit、candidate activation 或 S02 submit。

## Verified Evidence

原首帧 SHA-256 `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb` 与用户提供值一致，实测 941×1672、2,064,319 bytes。Agent 查看了身份、七个倒影和构图；白工牌缺少可读头像/姓名，未把它标为完整人物素材验收。

通过现有 bootstrap 和 `prepare_human_image_import_commit()` / `ProductionStateCommitter.commit()` 登记为 SC01 场景参考，`load_production_project()` 已重开 exact bytes。用户本轮明确指定该 PNG 并要求检查后 import，receipt 只记录该 import 指令，不代表用户亲自视觉验收或 Ark observation。没有创建 Seedance synthetic human egress receipt。

首次将 pending video Shot 增加空图片 role 的 bootstrap 被 `validation.validate_shot_strategy()` 拒绝，未产生有效 project。其准备目录保留；有效 project 明确为 `production-s01-v1/project.yaml`。首版 Planner 调用把 scene-owned 输入误投影为 approved keyframe，未通过；v2 已按真实 `scene_reference` 更正，保留原诊断而不覆盖。

## Current Workflow Blocker

`src/ai_video/planning/video_planner.py::_dynamic_decision()` 对 `AUTO + FIRST_FRAME` 且人物非空的首镜强制添加 IDENTITY/SCENE，AUTO 返回 R2V。当前非商业 I2V 仅存在真实 `EXACT_TERMINAL` 分支；初始 approved-keyframe I2V 分支属于 commercial projection，不能套用本剧。

`planning/_asset_readiness.py::_is_shot_bound_final_visual()` 的非商业 approved keyframe 要求当前 Shot `final_visual` 绑定 IMAGE；`production/validation.py::validate_shot_strategy()` 同时要求 pending generated-video Shot 只有一个空 VIDEO role。因此，仅导入图片或修改 owner 标签不能形成合法 S01 I2V 请求。

实际 `readiness-v2.json`：request/plan binding PASS、已声明 scene reference readiness PASS、plan eligibility BLOCKED，`verified_generation_requirement=null`。主线程 codegraph 与 native `code_mapper` 的独立只读核对确认没有可直接沿用的非商业首镜路径；未进行 runtime code 改动。

## Refreshed Provider Conditions

Seedance receipt 对象接受 project-owned photorealistic evidence 的读取，不代表 egress 放行：当前 `SeedanceSyntheticImageAuthorizer` 与 `SeedanceSyntheticImageReferenceResolver.validate_submit()` 都在 POST 前调用 `_deny_photorealistic_person_like_egress()`。本 PNG 属于写实人物画面，未用普通风景/动漫分类冒充。

Vidu `authenticated_task` 的 CDN 条件已经解除。新的 proposed profile 使用国内 API、`viduq3-pro` I2V、4 秒、1080p、24fps、silent；geometry 为 adaptive，最终交付尺寸仍需实测。一次只读定价 API 查询返回 HTTP 200、96 积分；按官方公开换算约 ¥3.00。这不是 generation POST，也不是 model entitlement 或 live output proof。新预算未授权；旧 85 元一次提交授权不复用。

## Verification And Boundary

已执行 exact PNG/hash 核验、canonical import / strict reopen、真实 Planner/readiness 复现和 codegraph 调用关系核验。没有新 MP4，所以没有调用 project-local `video-analysis` 或给出逐镜 PASS。

本任务只有新增 run evidence 和记录，不修改 runtime code。用户明确禁止 worktree，因而不运行会创建 detached worktree 的 exact-snapshot Harness；普通检查不能替代 fresh Harness receipt。既有 staged run patch SHA-256 保持 `5e6c24dd5a82a3e9f66a79781d234e63491b97293e28716ddbda3f7db611a639`；其他会话的 dirty/提交未纳入本任务，无 push。

本轮普通文档检查：`docs_contract_gate check` PASS，`agent_harness policy-audit` 无 diagnostics，`tests/test_runtime_skill_boundary.py` 2 passed，task-owned diff whitespace 检查通过。这些在当前共享 checkout 运行，不作为 exact-snapshot Harness receipt。

## Remaining Work And Learning

下一步需要对非商业首镜 I2V 的 Planner/readiness/source binding 做有界修复，保持 canonical owner、人物、最终交付、paid gates 和逐镜 Gate。修复后才能产出可提交的 exact ProviderBound request；不得用 direct Provider、fake prior terminal、commercial identity 或 T2V 绕行。

已执行 `retrieve-ai-video-memory`，初次返回 tagged stale advisory fragments，不替代 current code。创作指导使用 `seedance-authoring`；Vidu 提案采用 `higgsfield` / `higgsfield-prompt` 的起始帧、单一动作及固定摄影指导，不引入其 runtime 或改写剧本。`distill-ai-video-learning` 自动评估为 `no_candidate`：本轮是确定性接入阻塞，没有新的独立媒体实验。
