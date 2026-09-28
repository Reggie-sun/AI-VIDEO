# Local Unmetered Limits Implementation Plan

## Goal And Scope

落实[用户已澄清的 local limits contract](../specs/2026-09-28-local-unmetered-generation-limits.md)，解除本地永久累计额度误判，继续原 COCO／诺萨 17 s 任务。Native Codex 串行执行；只改 committer 原 submit-limits 方法与直接回归 tests，不引入 local ledger 或 schema migration。

## Ownership And Milestones

1. **Reproduction and correction.** `tests/test_generation_execution_guards.py` 覆盖 local-unmetered 可更新 finite batch/可选总上限，remote/metered 和 paid quota 不得扩张、当前 finite limits 仍有效。`tests/test_generation_runtime_repair.py` 走真实 project/orchestrator/service/committer、scripted transport，复现同 task 第二次 submit、history counters 与 one-use grant/permit。RED 后只修改 `src/ai_video/production/_state_commit_video.py::_require_persisted_generation_limits`：先读取 sealed selected variant，local/unmetered 才从 prior-local monotonic-ceiling gate 豁免；其他 checks 与当前 limits 保持。
2. **Verification and review.** policy 的 generation-feedback、Provider/local state、paid quota、docs 与 related routing checks在 exact staged snapshot执行；user no-worktree 优先，无 canonical Harness receipt 时明确报告直接检查边界。stable final code candidate 由受管 read-only Kimi deep 独立 T2 review，保存 source hashes、receipt、findings 与 Parent 裁决；这是新增 quota-fix scope，不重置旧 duration implementation 的 review rounds。同步 matrix / runtime baseline 的真实行为，旧 proposed renewal 文档标 superseded，不删除历史。
3. **Media continuation.** 保留旧两次 failed submits和 prepared-only attempt-03；新 run `runs/coco-nosha-local-unmetered-20260928-003/` 封存 next-attempt finite budget，same task、used=2、batch bound=3、total=None。重验原素材/model/profile、已测 isolated kernel bytes、服务 PID/InvocationID/queue，临时启用已有 Triton flag；orchestrator 编译新 attempt-04/request，采用原 unconsumed grant和新 one-use permit。known runtime failure停止本轮，unknown停止显式恢复；MP4后调用 MCP Gate并如实交付，恢复原服务。
4. **Checkpoint.** 更新同一 primary record 与 baseline，评估 learning，检查 task-only diff与 policy evidence，specific-path commit；不动 unrelated `.codex/config.toml`。

## Verification And Rollback

focused command：`python -m pytest -p no:cacheprovider tests/test_generation_execution_guards.py tests/test_generation_runtime_repair.py tests/test_production_paid_submit_quota.py -q`，再执行 policy对真实 staged paths选出的mandatory commands。补充测试不冒充媒体接受；runtime patch保留在任务overlay，installed package未改。回滚 source fix不会删除任何 prepared/consumed/history evidence，不能恢复旧 permit；媒体运行结束只恢复服务参数。

## Self Review

四个milestones覆盖 source gate、direct and integration failure paths、paid/remote isolation、same-task counters、independent review、真实媒体与恢复；旧 public schema/API/CLI与canonical owners不变。local no-total-quota和finite next batch分别表达，不假设已生成或通过声线/画质验收。
