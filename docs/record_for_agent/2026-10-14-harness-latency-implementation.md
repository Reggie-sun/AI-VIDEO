---
record_kind: architecture_implementation
topic_id: production-workflow-latency-audit
learning_eligibility: ineligible
---

# Harness Latency Implementation

Date: 2026-10-14

## Scope And Current Behavior

用户在 [latency audit](2026-10-13-production-workflow-latency-audit.md) 后要求修改，并选择 A 等待另一窗口提交冲突文件。
另一窗口的 `c8eeaf5` 已提交；本任务保留其 Seedream 实现及其余 dirty work，只拥有本轮 Harness/scripts/tests、spec/plan、matrix/context 与本记录。

- 项目 README 只走文档检查；其他 Canvas inputs 委托 canonical read-only author/preflight，实际重开 source、图片与 project schema，拒绝丢失定义/输入、扩写 source 与 path/symlink escape。无 runtime factory、Provider 或 Production activation。
- image 全域保留 136 项本域/adapter/E2E，加原 reader/state/dependency 中 60/118/2 项 `image or p7` 边界测试。完整 owner 同轮通过才 skip 对应子集，不复用跨 snapshot 结果。
- `_image_project_reader.py`、仅由其调用的 `_image_video_lineage.py` 改动走完整 reader；共享 schema/committer、未知路径仍走原 broad/fallback checks。其他 category independently selected checks 保留。
- 每项 check 前使用既有 exact snapshot callback 检查 drift/读取失败，停止剩余 checks并保留 failed receipt；最后仍核对 snapshot。迭代用 focused tests，稳定 owned bytes 后才运行最终 Harness。
- settled bounded tasks 不再因 Harness、多文件、文档或配置类别强制 full workflow；authorized written spec 的 plan trigger、必要 gates 与 Risk Gate 保留。制作对象先绑定用户原 source 和声画 AC。

## Verification And Evidence

在同一当前测试 corpus 上比较旧 policy 与新 selectors；不是重跑历史成片/Provider，也不能从数量直接推算总墙钟提速。
完整 collection、JUnit、stdout/stderr 与 native measurements 保存在 `.agent/harness/runs/harness-latency-20261014-native/`。

| Boundary | Executed evidence |
| --- | --- |
| Image domain | 136 PASS，50.439 s |
| Image reader/state/dependency subsets | 60/118/2 PASS，5.419/179.483/1.270 s；全部为完整 owner node-ID 子集，missing set 为空 |
| Full reader | 569 PASS，21.881 s；包含 image/P7 reopen 与 strict evidence |
| Real project data | 三个现有项目经 CLI author/preflight PASS；精确时间见 `canvas-data-native.json`，不证明 Provider admission 或媒体质量 |
| Harness behavior | 首项前、项间、末项后 drift、snapshot 读取错误、routing exclusions、argv literal paths、receipt proof 与 unknown/shared fallback 均有 executable tests |

旧 image check 1,288 项；新四项合计 316 项且无交集，native 合计 236.611 s。118 项状态测试仍含真实 process-crash matrix，不能为了秒级结果删除。
历史 asset-first scope 当前仍选完整 reader/state，其通过后抑制对应 60/118 子集，只执行 image domain 与 dependency 子集；历史 lineage scope 保留 reader/Seedream，移除 image generation/crash suites。
原剧本数据/source 修订 scope 改走数据检查，保留 `canvas_preserved_source_tests`；runtime Canvas 改动仍走完整 workflow。

最终 source/scope/policy/check artifacts 以 `.agent/harness/runs/harness-latency-20261014-published/receipt.json` 的 exact commit range 为准。
此前两次早期候选因 context 超出既有文档预算在 `agent_rules_check` 立即失败；已精简重复 workflow/cognition 说明，保持 210 行/18,000 bytes 上限，不调大预算或隐藏失败。

## Managed Analysis And Parent Adjudication

稳定候选 `6d8ac85dcfa076dbb6ee70b243e4735a99b88746` 先通过全部 10 个 Harness checks与 fresh receipt；Risk Gate 为 `KIMI_REVIEW_NOT_REQUIRED`：本任务不修改 Product writer、Provider 或媒体逻辑，routing/coverage/failure/proof seams已有 native evidence，无关键直接后果或剩余重大语义验证缺口。
standing route 使用一次受管 Kimi `test-investigator`，不是额外 implementation acceptance review。
invocation `fbb69f5c-e4b8-4994-90e2-f751a4a2d577`、seal `e3bd4b47-390b-42ef-a329-222acecd4659`：两次 authenticated `k3/max`，411.191 s，PARSED/exit0；read hashes、task/session identity 与 report SHA-256 `033758da5335616da4b47a59bb3d5e0147673e2e8c67872140e4d7cc504d5c56` 已核验。停止操作前已自行完成，没有取消或重试。filtered receipt/report 位于 native evidence directory。

Parent确认子集/计数/same-run skip 结论；dependency 的两项具体为 `test_generated_image_record_uses_generic_future_extension_seam` 与 `test_scope_boundaries_remain_absent_and_generated_image_uses_asset_seam`，JUnit均通过。
报告因 package 未含 trigger/alias/JUnit 内容保留的 uncertainty，分别由当前 `inspect_paths` fallback、`coverage_groups as _coverage_groups` import 和实际 XML 关闭；其疑问“source dialogue/expression无对应suite”不成立，`canvas_preserved_source_tests` 明确包含二者。
分析后补强 `--paths=<literal>` repeated arguments并验证 45 项相关 tests；这是 Parent 的 CLI boundary修正，不改变分析所绑定的 policy/check selectors。最终候选由最新 native Harness 判定，不把 PARSED 或旧 snapshot 称为 acceptance。

## Boundaries And Completion

未生成媒体、调用媒体 Provider、改变 paid/unknown/recovery/per-shot/final acceptance。全局 mandatory Kimi 与 installed maximum policy 未修改；本次 411 s 是仍存在的固定流程成本，不伪称已解决。
按 `record-ai-video-session` 主动记录；`distill-ai-video-learning` 为 `no_candidate`：这是同一工程演进链的确定性实现验证，不制造跨实验学习/adoption confirmation。Git publication 与最新 SHA 由最终交付核验报告；无关 dirty paths 保留。
