---
record_kind: session_summary
topic_id: video-library-browsing-and-comparison
learning_eligibility: ineligible
---

# Video Library Specification Record

Date: 2026-09-05

## Scope And Decision

用户在确认两个 greenhouse 视频能通过 Runs 入口播放后，指出当前展示不够好，随后批准编写
轻量 spec；认可“浏览与比较视频为默认，排障详情为次级入口”的产品方向。

唯一 target contract 是
[Video Library Browsing And Comparison](../superpowers/specs/2026-09-05-ai-video-video-library-browsing-and-comparison.md)。
本轮没有 implementation plan 或代码变更，也没有修改 run、媒体、Manifest、Registry 和 Provider。

## Verified Evidence And Boundaries

当前 `VideoLibraryRail` 在 `all` 下隐藏其他 workspace 入口；external `run_outputs` 扫描不覆盖
Production fetch。标准 catalog/detail 已能投影两个 greenhouse run 的 `fetched_media`。
本会话通过独立 Chrome 浏览器选择两项目并等待各自 exact token 后，验证了 15.104 秒与 30.08 秒
媒体解码及播放进度，均为 1280×720。Chrome MCP profile 占用，不能声称本次使用其完成了截图或播放验证。

浏览播放证据不改变真实 `running / validate`，不等于 candidate activation、P6 或 Final Acceptance。
历史 greenhouse Provider/quality records 的 verdict 本轮没有变化，故不需要质量结论 supersession。
截图仅作为本会话临时审阅材料，持久规格依据是上述 current code、exact identities 和可复现场景。

统一展示与 canonical ownership 分离；同名独立 Projects 不自动成为版本。
第一轮允许临时双视频比较，不持久化跨 Project 关系。这是展示设计约束，不是新的生产关系 schema。

独立 `reviewer_high` 指出旧 Runs spec 的 selected-only sealed Prompt 条款与全库 Prompt 搜索要求
存在冲突；当前 media index 已有 cross-workspace Prompt projection，属于既有文档/实现 drift。
本 spec 收窄第一轮搜索为身份与展示字段，不新增全库 Prompt 搜索要求，也不借本任务扩大暴露边界。
版本归组补充 exact Project/Shot key 和 verified revision/content-hash prerequisites。

## Verification And Learning Evaluation

两个新增 Markdown paths 经 Harness inspection 归为 `documentation`，无 fallback paths。
Exact staged Harness 的 scope diff、docs contract、policy audit 和 Product Runtime/Skill boundary
checks 全部通过（boundary tests：2 passed）；receipt 经 `verify-receipt` 验证 integrity、scope 和 freshness。
最终 snapshot receipt：`.agent/harness/runs/video-library-spec-reviewed-20260905/receipt.json`。
未实施的 A1–A10 全部保留为未来验收要求。

按 `record-ai-video-session` 和 `distill-ai-video-learning` 评估为 `no_candidate`：
本记录是单次 UI 问题与产品方向的 specification checkpoint，不是两次独立模型实验或受控多臂证据，
也不实质更新现有 Learning Claim；不创建占位 claim，不修改 Skill/Policy/Gate target。

## Remaining Work

Spec 状态为 proposed、implementation not started。下一阶段才落实 read-only projection 的最小
补充、布局与测试；本轮不声称 UI 已修复，不 push/release，不刷新独立 RAG index。
