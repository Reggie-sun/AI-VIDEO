---
record_kind: session_summary
topic_id: shot-whitebox-reference-default
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Per-Shot Whitebox Reference Default

Date: 2026-10-16

## Authority And Scope

用户在一次S01白模参考实证后明确要求：“所有镜头都要有白膜参考，除非模型不支持或者真的没必要（比如景色环境这种）”。这是新的Agent制作规则，不是从单例推导的模型质量结论；本记录不把旧S01失败改为PASS，也不增加生成、上传、预算、重抽或模型切换授权。

`AGENTS.md`用一句话规定所有Shot默认制作、核验、实际绑定白模，仅两类逐镜有依据例外。详细步骤归既有 `docs/canvas-production-harness.md#per-shot-whitebox-reference`；Creative Preflight与 `docs/blender-routing.md`只作入口和Skill路由。复用 `scenario-blender-expert`、`scenario-blender-previs-storyboard`及按需animation/rigging，不新建Skill、故事脚本、Product schema、状态库或timeline。

## Operational Contract

- 每镜明确制作/复用，或记录所选exact模型不支持、具体无必要的依据；未知、缺上传/准入/runtime、赶时间和已有prompt不构成有效例外。纯环境不是整类豁免，复杂运镜/空间/事件仍默认需要。
- 白模保持原文、角色/道具职责、解剖左右、人数、动作/接触、空间、镜头/画幅、fps和采用接点；原图负责身份与质感，声音/对白/字幕合同保留。动态guide须是真实连续动作，不以定格storyboard代签。
- 白模先看实际渲染/关键帧与正常速度动作，经exact参考核验后沿现有Registry/author/Planner/Router/adapter绑定；提交前核对真实native image/media输入，不能只写prompt或登记文件。生成输出仍独立走原逐镜MCP/全要求QA，白模成功不代验收。
- 同场景资产可以复用，各镜条件仍重验；前镜实际accepted state独占后镜交接，不强制换成白模末帧。`ResolvedTimeline`仍独占最终timing/trim，Blender只制作参考。

## Verification And Boundaries

文档自审覆盖动态人物、简单静态环境、复杂环境运镜、模型不支持、准入缺失、未实际绑定及输出失败七种情形；这是Parent语义核对，不冒充程序化case execution。实际运行既有agent-rules/docs-contract检查及exact commit-range Harness，receipt为 `.agent/harness/runs/shot-whitebox-default-20261016-r1/receipt.json`；结果以实际receipt为准。Risk Gate不要求独立review：只改Agent指导及路由，没有Product执行/权限/付费/状态writer变化；不声称程序已自动拦截所有Agent工具调用。

本次不生成或分析新媒体、不调用Provider、不修改Production或旧QA；前轮S01仍4PASS/2FAIL/9NOT_EVALUATED，canonical failed/STOP，S02未提交。相关实证与历史反例沿原记录保留，详见 `2026-10-13-jieshi-original-s01-s02-candidate.md` 的Current Whitebox Reference Result。工作流规则不证明白模保证质量、跨模型可用或后续正常速度human验收。

两文件原有staged native-reviewer修改按此前用户A授权保留，仅本次新增/替换hunks独立提交；其他foreign dirty保留，未创建development worktree。提交/push按项目规则执行，最终SHA与receipt另由Git/Harness核验。

`record-ai-video-session`已评估为有持久价值的规则checkpoint；`distill-ai-video-learning`为 **no_candidate**：当前是在实施用户明确的制作偏好，不形成新的经验性Learning Claim/adoption，不把单个白模attempt或历史工具成功计为普遍效果证据，也不修改全局memory或前台刷新RAG。
