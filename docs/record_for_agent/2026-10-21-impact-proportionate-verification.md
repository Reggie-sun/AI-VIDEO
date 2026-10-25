---
record_kind: architecture_implementation
topic_id: impact-proportionate-verification
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Impact-Proportionate Verification

Date: 2026-10-21

## Supersession — 2026-10-25

用户后续要求由 [Harness Three-Level Verification](2026-10-25-harness-three-level-verification.md) 落实到 runtime/CI：修改后精准测试、功能完成相关回归、合并/发布前完整回归。下文保留 2026-10-21 的 docs-only 调整与当时证据；当前执行入口和 receipt 级别以新记录及 canonical owners 为准。

## Decision

用户在Seedance Prompt限制调整后明确要求优化验证策略。旧要求强制完成全部路径选测并取得fresh receipt；共享compiler及相关tests命中宽泛类别，选择18个checks，其中generation_feedback_tests耗时627.372秒。历史记录保留在`.agent/harness/runs/seedance-prompt-length-20261021/receipt.json`，该完整run中断，不能宣称整体通过。

`AGENTS.md`、control-plane playbook和primary contract matrix统一改为按实际行为影响和失败风险选择最小充分验证；局部改动不再因共享文件、提交、记录或追求receipt自动触发整组回归。跨模块行为、授权/凭据/持久化/恢复语义、影响无法界定或用户要求完整验证时扩大到适用exact Harness。耗时明显不相称时评估停止冗余检查，如实保留中断和未验证项。

## Boundaries

仅修改Agent验证决策与相关文档入口，未修改Harness runtime、policy.yaml、CI、路径映射、receipt校验或Product/媒体验收。直接运行完整Harness仍执行其selected checks；局部验证不能据此获得完整Harness PASS。观看体验收益是避免局部工程调整挤占创作和审片时间，不把节省测试时间描述为作品质量改善。

Parent self-review：这是用户明确授权的流程调整，未改变Provider授权、预算、安全或Product state路径，无具体关键运行风险或实质验证缺口触发独立review；不新增Agent或通用验证系统。保留既有AGENTS和matrix非本任务hunks及其他窗口staged内容。

## Verification

`python -m scripts.docs_contract_gate check`通过。`python -m scripts.agent_rules_gate`首次指出playbook超出原文档预算，已压缩本次新增措辞，复验通过；不扩大预算、不启动大范围回归、不生成媒体或调用Provider。最终做owned diff与格式检查。

自动评估`distill-ai-video-learning`：`no_candidate`。这是直接获授权的流程策略修改，不是跨实验媒体质量Learning Claim，不创建待批准占位文件。
