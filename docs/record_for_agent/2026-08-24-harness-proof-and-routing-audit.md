# Harness Proof and Routing Audit

## Session Boundary

- Date: `2026-08-24`
- Repository: `/home/reggie/vscode_folder/AI-VIDEO`
- Audit mode: strict read-only architecture verification；本文件是 Stop checkpoint 要求的 durable session record，也是本轮唯一新增的 repository artifact。
- Reviewer snapshot: `72919593b9e7734d73bdf7e13aa37fdf408335be`
- Record-time `HEAD`: `9c8bd37299e573f9c82fa2dc8afbb13a3cf57498`
- 从 reviewer snapshot 到 record-time `HEAD`，本次审计涉及的 Harness、runtime guard 与 Provider Console test-routing surfaces 没有 diff。
- 未运行 pytest、Harness verification、build、Provider、ComfyUI、媒体生成或网络调用；未读取 credential，未发生付费行为。
- 现有 unrelated dirty work 全部保留，未修改、stage 或纳入本记录。

## Executive Decision

当前 Harness 的主架构方向合理，不需要推倒重做：exact staged/commit-range scope、detached worktree、fail-safe fallback、same-run coverage dedup、credential/proxy environment stripping，以及 Development Governance 与 Product Runtime 分离，都应继续保留。

但当前 Harness **验证偏重且 completion proof 存在两个 correctness blocker**，因此不能把现有 `verify-receipt` 结果单独视为完整、独立的 canonical completion proof。优先级应是先补 proof correctness 和漏测，再优化 suite routing；不应先做大规模测试重组。

## Confirmed Strengths

- Completion scope 要求 non-empty exact staged snapshot 或 exact commit range，并绑定 Git identity。
- Checks 在 detached temporary worktree 中执行，不把 unrelated working-tree changes 带入 execution tree。
- Unknown/unmapped owned paths fail safe 到 `full_tests` 与 task Architecture Gate。
- `covered_by_check_ids` 只有在同一轮 covering checks 全部通过后才允许 skip，被覆盖检查不会仅凭声明静默消失。
- Harness 清理 credential、proxy 与 tool-injection environment，并使用 process-group cleanup 处理 timeout。
- `scope_diff_check`、`docs_contract_check` 与 task Architecture Gate 本身很轻，不是当前时延主因。
- 未发现 Product Runtime 反向依赖 Harness；Harness 仍属于 Development Governance，不拥有 Manifest、lifecycle、Provider execution、activation、recovery 或 QA truth。

## Blocking Correctness Gaps

### 1. Receipt completeness is not independently verified

`scripts/agent_harness.py::receipt_freshness()` 当前校验 receipt hash、policy hash、HEAD/index snapshot 与 freshness，但不会从 exact scope 重新计算：

- changed paths；
- matched categories；
- selected mandatory checks；
- check-record completeness；
- argv、status 与 coverage closure 是否对应当前 policy。

`tests/test_agent_harness.py` 中已有测试用一个没有 `checks` 的 receipt 断言 `fresh is True`。本轮还以内存对象复现：正确 self-hash、policy hash 与 HEAD，加上假的 `changed_paths` 和空 `checks`，仍得到全部 freshness booleans 为 true。

结论：当前 receipt self-hash 能证明 self-consistency，不能证明 authenticity，也不能证明 mandatory checks 实际完整执行。`verify-receipt` 必须明确区分“artifact 未漂移”和“completion proof 完整”。

### 2. Provider Console mandatory route omits tracked behavior tests

`.agent/harness/policy.yaml` 的 Provider Console Node check 只运行：

- `provider-console/tests/runs-api.test.mjs`
- `provider-console/tests/continuity-review-contract.test.mjs`

但 `provider-console/package.json` 的正式 scripts 还包含：

- `provider-console/tests/continuity-review.test.mjs`
- `provider-console/tests/sites-worker.test.mjs`

因此 continuity rendering/decision behavior 可以在 Harness PASS 时回归；Sites worker、packaging 或 build surfaces 也没有 path-sensitive executable gate。依据 `provider-console/AGENTS.md`，Sites build/test 只需在 Sites handoff 强制，合理方案是拆分 ordinary console gate 与 `provider_console_sites` gate，而不是让所有 UI change 都跑完整 Sites build。

## Validation Weight Evidence

现有 receipts 与 JUnit timing 显示，主要重量来自重复执行 global lifecycle crash matrix，而不是 Harness 自身：

| Evidence | Observed cost | Finding |
| --- | ---: | --- |
| `production_video_provider_tests` | about `292s` | 其中 `test_production_state_recovery` 约 `223.6s`，`test_production_state_commit` 约 `31.7s`，两者合计约占 `87%` |
| `production_state_tests` + `production_video_provider_tests` in one run | about `277s + 294s` | 两个 category 重复运行同一 state/unknown-outcome/recovery core |
| `agent_memory_dev_tool` routed to `full_tests` | about `534s` | Agent Memory 自身 focused tests 约 `13s`，当前 route 明显过宽 |
| `scope_diff_check` | about `0.003s` | 很轻 |
| `docs_contract_check` | about `0.112s` | 很轻 |
| task Architecture Gate | about `0.59s` | 很轻，但常被排在数分钟 tests 之后 |
| Harness tests | about `2.5s` | 很轻 |

`production_state_tests` 与 `production_video_provider_tests` 共享 heavyweight files，导致 cross-category duplication。对 capability/profile/workflow 等 narrow Provider changes，理论上移除 global lifecycle cohorts 后的 provider-specific portion 约 `35s`；这说明可减少约 `88%` 的该 route wall time，但不能简单删除 crash/recovery tests。正确做法是把 global lifecycle core 与 video/provider-specific behavior 分开路由。

Selection 当前按 always checks、category checks、fallback checks 排列，execution 又严格遵循该顺序。因此 Architecture Gate 可能在五到九分钟后才发现本可在不到一秒内发现的失败。若 known category 与 fallback path 同时出现，category pytest suites 先执行，随后 `full_tests` 再覆盖性重跑；`full_tests` 还没有被声明为所有 Python pytest checks 的 covering owner。

## Partition and Audit Gaps

本轮运行只读 `python scripts/agent_harness.py policy-audit`，结果为：

```text
candidate_count: 369
docs_contract_diagnostics: []
missing_check_test_paths: []
unmapped_paths: []
unverified_paths: []
```

该结果不能解释为整个 repository 已得到语义充分的 routing coverage：

- audit candidate 来自人工 allowlist，而不是全部 tracked executable/config/test surfaces；
- “verified”只要求命中一个非 scope/architecture check，不验证该 check 与 path 的行为相关性；
- missing-test inventory 只识别 argv 中显式列出的 Python `tests/*.py`，看不到 Node tests、build scripts 或 broad selector omissions。

对全部 tracked paths 做静态 `inspect_paths` 时仍发现 `38` 个 fallback paths，包括 `pyproject.toml`、root `package.json` / `package-lock.json`、`.codex/config.toml`、`.mcp.json`、example configs、fixtures 与 `.workflow/**`。这些对象不应全部使用同一策略：dependency/control-plane files 需要 ecosystem-specific checks；非权威 development artifacts 应获得 explicit exemption 或轻量 category，避免无意义触发完整 Python suite。

## Safety Boundary Still Missing

`scripts/agent_harness_runtime.py` 明确记录 `subprocess_network_isolation: false`。当前 Python guard 通过 monkeypatch `socket` 约束 pytest process，但 Node checks 与测试启动的 subprocess 仍可能访问网络或用户目录配置。

因此当前可以准确声明“清理已知 credential/proxy environment，并禁止 Harness policy 主动安排 live Provider/media checks”，但不能机械证明“所有 child processes 绝无网络能力”。如果后者要成为 hard guarantee，需要 process-level network sandbox；不应靠文案或环境变量清理替代。

Receipt environment fingerprint 也尚未绑定 Python dependency set、Node/npm/toolchain versions。Receipt self-hash 是完整性线索，不是签名或 trust anchor。

## Recommended Sequence

### P0 — Correctness before optimization

1. 让 receipt verifier 从 exact scope 与当前 policy 重算 categories、selected checks 和 coverage closure，并要求 check records 完整一致。
2. 在 API/输出中区分 `self_consistent`、`fresh_for_snapshot` 与 `complete_completion_proof`；不要继续把三者合并为一个 `fresh` 结论。
3. Provider Console ordinary route 补入 `continuity-review.test.mjs`；为 worker/build/package/Sites paths 建立独立 Sites gate。
4. 把 `scope_diff_check`、`docs_contract_check` 与 task Architecture Gate 置于 expensive suites 之前，fail fast。

### P1 — Reduce duplicate cost without weakening contracts

1. 将 Production validation 拆为 global lifecycle core、domain-specific state behavior、provider-specific behavior。
2. 只有 committer/shared lifecycle/schema/recovery surfaces 触发 heavyweight crash matrix；capability/profile/workflow adapter changes 运行 provider-specific suite。
3. 当 `full_tests` 被选中时，使其成为所有 Python pytest checks 的 covering owner并只运行一次；Node/build checks保持独立。
4. 为 Agent Memory 建立 focused suite；扩大 policy audit 到 tracked executable/config/lock/test surfaces，并审计 check relevance。

### P2 — Hard isolation and reproducibility

1. 如果产品要求 Harness 对所有 child processes 提供 no-network mechanical guarantee，引入 process-level network sandbox。
2. 将 dependency/toolchain identity 纳入 environment fingerprint，并继续把 CI fresh execution 作为信任边界。

## Start and Completion Gates

应该在 **下一次计划修改 Harness policy/verifier 之前** 开始 P0；不需要等待新的 Provider slice，也不应让更多历史 receipts 依赖当前不完整 verifier。P1 应在 P0 的 receipt completeness regression tests 通过后开始，避免同时改变 proof semantics 与 test partition，导致无法判断 PASS 的含义。P2 仅在团队明确需要 hard no-network guarantee 时启动。

本项工作只有同时满足以下条件才可标记完成：

- 恶意或残缺 receipt（空 checks、错误 changed paths、缺 mandatory check、错误 coverage closure）被 verifier fail closed；
- Provider Console ordinary 与 Sites surfaces 分别命中正确 executable checks；
- cheap gates 在 expensive suites 前 fail fast；
- representative Provider、state、Agent Memory、fallback 与 mixed-category path matrices 不漏测且不重复运行被覆盖的 Python suites；
- policy audit 能发现未登记 Node test、重要 dependency/control-plane fallback 与 irrelevant check mapping；
- exact staged/commit-range Harness tests 与 documentation contract checks通过；
- 若声称 hard no-network，则必须有 child-process/Node/subprocess 层面的 executable evidence；否则文档继续明确其限制。

这些 gates 只证明 Harness routing/proof correctness，不证明 live Provider、媒体质量、creative acceptance、production activation 或 release readiness。

## Agent Evidence

- External explorer: `Role=explorer`，scope 为 Harness routing、weight 与 coverage gaps；runner 为 `MiniMax-M3` high、external CLI transport，status 为 `DONE_WITH_CONCERNS`，无 retry/fallback。Parent 接受其 duplication、audit 与 subprocess-isolation evidence，但拒绝把 narrow Production reader route 扩大到完整 Production suite，因为现有 timing 表明这会加重而非修复 over-validation。
- Independent native review: `reviewer_xhigh`，read-only，verdict `reject`；blocking reasons 为 receipt completeness defect 与 Provider Console mandatory coverage omission。
- Parent verification 使用 Git/path inspection、policy selection、tracked-path scan、现有 receipts/JUnit timing 聚合、source/tests 对照，以及不落盘的 receipt object reproduction；未把 subagent summary 当作唯一证据。

## Explicit Non-Claims

- 本记录没有修改 Harness implementation 或 policy。
- 本记录没有创建 implementation spec/plan，也不授权下一阶段代码修改。
- 本记录没有生成 fresh passing Harness receipt；本轮严格审计没有运行那些 checks。
- 本记录不改变 `ProductionStateCommitter`、Provider、Manifest、activation、recovery、QA 或 release ownership。
- 本记录不证明任何 live Provider、ComfyUI、Seedance、媒体或 creative result。
