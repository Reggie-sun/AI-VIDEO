---
record_kind: architecture_implementation
topic_id: harness-three-level-verification
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Harness Three-Level Verification

Date: 2026-10-25

## Decision And Runtime

用户要求按阶段区分验证：修改后精准测试、功能完成后相关回归、合并或发布前完整回归。旧路径选测没有级别；本次在既有 Harness 增加 `--level focused|related|full`，默认 `related` 保持旧入口兼容。

- `make harness-focused`：消费各 category 的显式 `focused_check_ids`，不加入全局 always/fallback checks；命中多个模块取并集。无精准映射停止并报告，不静默扩成全套。Python toolchain 和全局 fixture 明确没有精准映射。
- `make harness-related`：保留既有模块及接口契约选测、unknown-path fallback、同轮覆盖与失败停止语义。
- `make harness-full`：选择全部 policy checks，Python 全套通过后才允许跳过其覆盖的局部 suites；Node tests、前端 build、repository architecture 仍实际执行。

三个入口使用 exact staged snapshot；commit range 使用 `make harness-verify-range BASE_REF=... LEVEL=...`。只读预览可用 `inspect --path ... --level ...`，显式路径不能生成 completion proof。

receipt 绑定 `verification_level`；`focused` 不关闭 engineering completion。校验器按 receipt 级别重新计算选测，`full_regression_passed` 仅在完整 scope、checks、artifacts 和 freshness 都成立时为 true；旧 receipt 缺字段按 `related` 解释。CI 显式 inspect/verify `full`，并用 `--require-level full` 拒绝较低级别 proof。

CLI 参数/调度移至 `scripts/agent_harness_cli.py`，runner、scope 与 receipt owner 保持在既有模块，避免继续扩张已超 800 effective LOC 的主文件。本次主文件降至 749 effective LOC。未改变 Product、Provider、凭据、费用、逐 Shot MCP 或媒体验收。

## Verification

新增 14 项分级/未知映射/错误配置/跨级冒充/真实子进程 receipt 用例，先观察失败，再实现；直接局部验证 355 项通过。随后真实 `related` 执行 10 个 checks、423 项测试全部通过，receipt `fresh=true`、`full_regression_passed=false`；对该真实 receipt 执行 `verify-receipt --require-level full` 返回 1，正确拒绝跨级放行。文档、rules、policy audit 与 task architecture 检查均通过。

实现验证基线 `2d17c49e0f22ce2ffb44a713b25c81ef7a546aa6`；完整回归绑定的 implementation tree 为 `da95a695c48e44468a3c9779e62211fad36957ae`，与本工作区仅暂存本任务代码/配置/操作文档的 tree 一致。本记录及历史 supersession notice 另做文档验证，不将其描述为全量测试的输入。

完整回归的 Python 全套执行 5153.95 秒：7507 passed、11 failed、48 skipped；其中本地多语言语料校准耗时 757.14 秒。Harness 按既有失败停止规则停止后续 checks，Node tests/build 未执行，完整回归为 `FAILED`，不能合并或发布。首轮仅因 playbook 文档预算失败，压缩本次文字后才开始上述全量执行，没有扩大原预算或隐藏失败。

对未包含本次改动的基线 `2d17c49` 保持全测试 collection，仅选择候选失败用例复现，14.95 秒得到同样 11 个失败、7541 deselected；JUnit node IDs 完全一致。失败分组如下，均未在本任务内修改其 Product owner 或已有断言：

| Existing Failure | Count | Evidence |
| --- | --- | --- |
| Learning routing 旧文档断言 | 1 | 基线已缺少 `## Experience Learning Routing` |
| Handoff schema 与 runtime 不一致 | 1 | checked-in JSON 不等于 exporter schema |
| Commercial E2E 缺表演验收 | 7 | `talent-presenter.acceptance` 被既有 gate 拒绝 |
| libass 原生依赖 | 1 | `libharfbuzz.so.0: undefined symbol: FT_Get_Transform` |
| Seedream source revision | 1 | `source revision required for a changed prompt input` |

证据均保存在 repository 内，复制时未修改原 receipt 或 artifacts：

- `.agent/harness/runs/harness-three-levels-related-20261025/receipt.json`
- `.agent/harness/runs/harness-three-levels-full-20261025/receipt.json`（首轮预算失败）
- `.agent/harness/runs/harness-three-levels-full-20261025-r2/receipt.json`
- `.agent/harness/runs/harness-three-levels-baseline-repro-20261025/comparison.json` 及基线 JUnit/log、真实跨级拒绝 probe。

上述 receipts 在其隔离 snapshot 校验；不冒充当前含其他未提交修改工作区的 fresh/full PASS。最小发布恢复条件是由相关 owner 修复五组既有问题，再对修复后的稳定 snapshot 取得 fresh full PASS，不豁免或重写旧失败。

## Publication State

实现已在本地提交 `5daa3d6`，其 Git tree 与上述 implementation tree 完全一致。因第三级失败，未 push、未合并、未发布；本记录与旧记录 supersession notice 单独提交，不把文档记录描述为上述全量输入。其他窗口的未提交修改未夹带。

## Ownership And Review

用户明确允许只修改并提交 policy/AGENTS 的本任务 hunks；原 Seedance fidelity 测试引用、出片优先规则及其他工作区改动保留。Parent self-review：改动限 Development Governance，主要失败路径由分级、兼容、receipt 防冒充和隔离快照测试覆盖；无具体关键凭据/越权/持久化损坏路径或实质语义缺口触发独立审查，`NATIVE_REVIEW_NOT_REQUIRED`。

自动评估 `distill-ai-video-learning`：`no_candidate`。这是用户直接要求的验证流程修改，没有跨实验媒体质量结论，不创建 Learning Claim。未主动重建 RAG；检索返回 stale advisory，并由 CLI 排队后台刷新，未核验刷新结果。未调用 Provider 或生成媒体。
