# AOCI Cognition Maintenance

Date: 2026-10-27

## Scope And Evidence

用户明确要求维护 AOCI。本次沿项目 MCP `0.1.0-rc14` 的 Rules、Overview、Maintain、完整候选批次 Update 和官方 Scope acknowledge 流程操作；没有改动业务源码、Scope policy、Meta 字典或 Product authority。

初始 19 个 stale indexed owners、803 个 observe pending。Parent 与两个只读 mapper 复核 361 个文档/配置/资产、265 个运行实现、177 个测试/fixture；另一名只读 reviewer 完整阅读 15 个 Python indexed owners，Parent 阅读 4 个文档/配置 owner。维护期间新增及继续修改的 `2026-10-27-shizhen-B-motion.md` 已补读并保留 observe。没有通过缩小范围、自动生成语义或忽略未读变化解除阻断。

19 个条目由模型依据源码创作，正式工具绑定 candidate/source SHA 后批量写入。随后通过官方定向完整替换批次修正两个关系路径和一个文件规模标签。内容涵盖 Reference Planning seal、native audio/retime 与同一混音、fresh Seedance 与历史 replay、mixed references、三种计费语义及只读 Console 边界。AOCI 仍为 advisory，不能取代源码、测试、运行证据或真实媒体验收。

## Verification

- 官方 Verify：`structure_valid=true`、`governance_aligned=true`。
- Aggregate Check：`ok=true`，无 findings。
- Guide：`complete=true`、`next_action=none`；33 个 indexed owners，missing/stale/orphan/unbaselined/pending review 均为零，无 recovery 或第三方正式资产冲突。
- Code volume SHA256：`445450d74dd4259e94131ddf44bcd29ff89398ec5441a9eb54735e4189b8ff36`。
- Composite identity：`35a0d839db41edb099d1a5b4cf34aa39c9078219d7260e83415f19acfb2e1b32`。
- `python -m pytest -p no:cacheprovider tests/test_aoci_project_cognition.py -q`：2 passed；owned diff whitespace 检查通过。
- staged focused Harness：文档检查通过，AOCI 测试 1 passed / 1 failed。官方 acknowledge 将 28 个其他任务尚未纳入 Git 的 observe 文件纳入 Baseline；隔离 staged checkout 缺少这些文件，`test_aoci_manifest_and_baseline_reference_contained_existing_files` 因此失败。这是本次可移植性阻断，不能当作既有无关失败忽略；没有修改测试或删除 Baseline 记录来过关。最终 receipt：`.agent/harness/runs/aoci-maintenance-final-focused-20261027/receipt.json`。
- 官方结果保存在 `.agent/harness/runs/aoci-maintenance-20261027/aoci-{verify,check,guide}.json`；记录写入后再次 acknowledge 和核验，最终结果覆盖同一位置。

恢复上下文时完整交付33条索引并通过 Challenge 10/10；该次读取仍是更新前索引，不能用它证明更新后 strict cognition。最终治理对齐与模型认知自报是不同证据。

## Publication And Limits

本次四个 owned paths 为 `aoci.code.txt`、`.aoci/baseline.json` 和本任务两份工作记录。由于 staged portability 检查失败，当前均 local-only，未 commit/push；没有夹带其他任务文件。官方 Scope acknowledge 不提供仅排除 untracked 的选项，修改 Scope 或手改 Baseline 以隐藏缺口不属于本次修复。待相关文件由其 owner 正式提交，或有独立授权处理 portable Baseline 合同后，再对稳定 snapshot 验证与提交。

本次 Baseline 绑定当前共享工作区，包括其他任务尚未提交的源码及 observe 文件；远端 clean checkout 不保证相同 source bytes、文件存在性或 aligned 状态，后续变更需要重新核验。专用测试通过不等于整个仓库回归或真实视频质量通过。没有付费调用、生成媒体或 Production mutation，没有刷新 RAG。

使用 `record-ai-video-session` 并评估 `distill-ai-video-learning`：`no_candidate`，本次是认知治理维护，不是可支持模型质量结论的独立媒体实验。
