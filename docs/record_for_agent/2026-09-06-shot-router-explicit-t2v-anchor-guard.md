---
record_kind: architecture_implementation
topic_id: shot-router-explicit-t2v-anchor-guard
learning_eligibility: ineligible
---

# Shot Router Explicit T2V Anchor Guard Record

Date: 2026-09-06

## Problem And Scope

《界蚀》S01 的既有执行脚本在 `important_character_ids` 非空时仍预设 `TEXT_TO_VIDEO`，以空素材输入调用 `resolve_requirement()`。公共 resolver 优先消费 verified requirement 的 mode，跳过后续人物参考推导分支，导致原本应阻断的请求得到 `ProviderBoundVideoRequest`。用户明确要求补齐验证并纳入 Harness。

## Current Runtime Truth

- 修复提交：`b304141`。唯一行为 owner 仍为 `VideoGenerationResolver._resolve_capability()`；在 mode 解析后统一检查重要人物与 T2V 的冲突，返回 `BLOCKED_POLICY / IMPORTANT_CHARACTER_REQUIRES_VISUAL_ANCHOR`，不生成 bound request、不自动 fallback。
- `resolve()` 显式 mode 参数与 `resolve_requirement()` 均受保护。仅在 context 存在而没有被请求消费的参考图不能使 T2V 放行。
- 重要人物由既有 `important_character_ids` 契约声明；本修复不从 prose 推断身份，也不把所有 semantic Character 自动视为重要人物。合法 I2V/R2V、无重要人物约束 T2V、Provider selection 与 immutable schema/hash 的既有边界保持。
- 没有改写已有生成脚本、失败媒体或 Production state；没有进行 Provider、上传、生成、activation 或质量验收。

## Verification And Evidence

- 修复前，两公开入口乘以有/无可用参考的四个测试均复现错误放行。修复后扩展为六个回归组合，包含真实 `VideoPlanner -> require_current_video_plan -> resolve_requirement`。
- 主线程 focused suite：255 passed。独立 `reviewer_xhigh`：accept，12 个 scoped 检查通过，无 blocking issues。
- `tests/test_agent_harness.py::test_shot_router_routes_to_exact_contract_suite`：1 passed。已有 policy 将源文件和回归测试映射到 `production_shot_router_tests` 与 `provider_neutral_video_requirement_tests`，无需重复创建检查 owner。
- Exact commit-range Harness：`b304141^..b304141`；Router 契约组 284 passed，neutral requirement 契约组 377 passed，runtime skill boundary 2 passed；架构、文档与 policy audit 通过。测试组有重叠，不累加为独立测试总数。
- Receipt：`.agent/harness/runs/router-important-character-t2v-20260906/receipt.json`；`verify-receipt` 通过。证据只证明这次离线路由修复，不证明媒体质量。

## Remaining Work And Publication

《界蚀》S01 仍需以合适且真实可用的视觉参考路线生成或修复，并通过逐镜媒体 Gate。本修复不解决 Ark/其他 Provider 素材接入，也不追认两次失败产物。

修复只提交到本地，未 push/release。既有七个 staged run 文件的 staged patch SHA-256 在修复提交前后均为 `5e6c24dd5a82a3e9f66a79781d234e63491b97293e28716ddbda3f7db611a639`；其他会话的 `provider-console/tests/library-browser.test.mjs` 修改未纳入本任务。

## Learning Evaluation

`distill-ai-video-learning`：`no_candidate`。这是一个代码回归及其边界测试，不是两次独立模型实验；既有两次 S01 失败不能据此证明 T2V 是画面失败的唯一原因。RAG 本轮返回 tagged stale advisory fragments，未用其替代 current code/tests，未主动重建索引。
