---
record_kind: architecture_implementation
topic_id: harness-policy-granularity
learning_eligibility: ineligible
---

# Harness Policy Granularity Record

Date: 2026-10-05

## Current Snapshot Notice

最终核验时，并发 owner 已将 review 规则同步提交为
`c698ecd95d22c47fab45042bfd813d06c281b27c`。本任务六个 reviewed 文件的 SHA-256 均未变，
但 HEAD/index tree 已变化；原 receipt 保留 `passed` / artifact integrity，当前
`verify-receipt` 为 `fresh=false`、`snapshot_matches=false`。下方 passing/freshness 与
双独立 review 是原冻结 snapshot 的历史证据，不是当前 HEAD 的 completion proof。
本任务 commit/push 仍 blocked；依赖提交后须在最终稳定 snapshot 运行 policy checks。

## Purpose And Authority

用户要求执行 Harness policy 细化，并明确接管 `policy.yaml`、保留其已有 staged 修改，
旧验证自然结束。本 session 只修改 Development Governance，不接受另一任务的 Product
实现，不改变媒体质量、授权、预算、unknown outcome 或逐 Shot Gate。
适用 [spec](../superpowers/specs/2026-10-05-harness-policy-granularity.md) 与
[plan](../superpowers/plans/2026-10-05-harness-policy-granularity.md) 已由 Parent self-review。

## Implementation And Boundaries

- causal-expression helper/test 路径使用专用 suite，并保留 Planner、neutral requirement、
  Router、Provider、Vidu 和 final-output 边界；不再选择 `full_tests` 或完整 repair suite。
  feedback owner 改动继续选择完整 repair/history 回归。
- 复用既有同 run PASS 后覆盖跳过：完整 feedback suite 覆盖专用 expression check；
  quality intelligence suite 完整包含 memory suite。未增加跨 run cache acceptance。
- 大测试组增加 pytest durations；full suite 增加 verbose node ID 和内建 stack dump。
  Harness 每 check 开始前 flush ID/timeout，结束后输出 status/duration。子进程 stdout
  仍在 suite 结束后交付，没有逐 test 实时流式输出。
- 为保留历史 policy argv 重建，诊断 flags 写入 policy，`_check_argv` 本身未修改；这是
  对原 plan 中该 symbol 定位的兼容性调整。full timeout `7200` 是保留的 producer 修改，
  本 session 没有上调该预算。
- 新增 `tests/test_agent_harness_policy.py`，验证 narrow selection、完整覆盖顺序、未知 /
  infrastructure fallback、历史 argv、START 日志与真实 pytest duration/JUnit 输出。

## Exact Snapshot And Verification

HEAD：`d3cdc4cd708e72fd106d23a1477bca0b277648b0`。
验证 index tree：`fc6143a17a0c183685b9f4bdcacda6eb68000c69`。
policy SHA-256：`ca01b388b67e2e5f9e9db8d6356dd62c0180eaf1bed167fe6546939aabfd8e9d`。
该 snapshot 包含保留的 producer staged paths；receipt 不授予其 Product acceptance。

- focused Harness/policy/docs/rules/hook/adapter 回归：307 passed，9.81 秒。
- exact-staged receipt：
  `.agent/harness/runs/harness-policy-granularity-20261005-final/receipt.json`。
  18 checks PASS；2 checks 由同 run 实际 PASS 覆盖。总 wall time 1839.962 秒。
  在原 HEAD checkpoint，`verify-receipt` 的 scope、policy、artifact integrity、coverage、
  freshness、snapshot 和 workspace cleanup/stability 均为 true；该历史核验结果保存在
  同目录 `freshness.json`，当前 HEAD 漂移另存 `freshness-after-governance-commit.json`。
- 主要 check 耗时：feedback 581.446 秒、planner 258.658 秒、Provider 424.268 秒、
  final-output 391.898 秒、voice routing 132.549 秒；其余选中检查均已完成。
- Architecture Gate PASS，3 个 oversized growth WARN 均来自原 producer 的
  `minimax_hailuo.py`、`seedance.py`、`video_generation.py`，本 session 未修改这些路径。

## Preserved History And Performance Limits

旧全量 `.agent/harness/runs/typed-causal-native-expression-20261005-final-5/receipt.json`
自然结束为 failed：5875 passed、5 skipped、1 failed，pytest 4327.66 秒；未 timeout，
未由本 session 终止。失败项为
`tests/test_agent_memory.py::test_local_multilingual_project_corpus_answerability_calibration`，
要求空结果的查询实际返回额外 Hit。该旧冻结快照不含本 session 后续修改；新选集 PASS
不清除这一历史失败，也不证明全仓库健康。

首轮本 session receipt `harness-policy-granularity-20261005-001` 的 feedback suite 已通过，
pytest 590.29 秒。随后根据实际 fixture 分支证据进一步拆分 helper mapping，并只取消
本 session 已过时的 voice-routing check；该 receipt 保留 failed / exit `-15`。
原 `final-2` 的 full-suite 1800 秒 timeout 同样保留。

这些是同一修复链的不同 scope，且旧全量曾并发运行；没有受控 A/B 或隔离的整体加速比。
新增诊断与 narrow routing 是当前实现，不把单次耗时升级为通用性能结论。

## Independent Review And Parent Adjudication

调查用 Kimi invocation `34d8195e-4a4e-405b-9778-d25cebeea4ef` 已完成，3 wire requests；
Parent 核对 buffered capture、同 run coverage 与 proof argv reconstruction 证据。
该调查不计为 final review。native `test_analyzer` 的 fixture 分支分析也仅作定位证据。

本轮按 dispatch 时旧 T3 规则执行的 final review 绑定上述 exact tree 与 owned bytes。native `reviewer_xhigh`
`/root/harness_policy_final_review` 返回空 finding set。Kimi round 1 invocation
`59f866a2-8275-428e-a213-73c6b61669b8` 为 `UPSTREAM_HTTP_ERROR`，537.274 秒、7 wire
requests、15 observed Reads；前 6 次身份验证成功，第 7 次 HTTP 429，没有 usable final report。
其 canonical invocation receipt 保留在 router 的对应 run directory；partial 输出不作 findings
或 acceptance。Parent 核对 source 未漂移与实际错误后，仅封存一次 round 2，移除 optional
大测试文件及未修改 runner 的重复读取，保留 scope、required evidence 和历史消费。
round 2 invocation `3a18fb39-830d-409c-b8c4-f1bfe1c1fc08` 为 `PROTOCOL_ERROR`，
685.455 秒、6 wire requests、14 observed Reads；全部请求 HTTP 200、process exit 0，
但 final result 带有 prose 前缀，未满足 strict JSON representation，未产生 usable report。
两轮 partial 输出保持隔离，共 13 review wire requests；未手工剥离 / 接受不合格报告。
source bytes 与 index tree 核验未变。

按 `SUBAGENTS.md` 的 Repeated Kimi Failure Fallback 停止追加 Kimi 调用，使用独立
`reviewer_xhigh` `/root/harness_policy_fallback_review` 接替 Kimi 的同一份 required review。
其 context 不包含 peer findings 或 Parent adjudication；原 native review 与 fallback review
保持独立。native 权限不冒充 Kimi Docker / authenticated route proof。fallback review 与
Parent final adjudication 已完成：fallback 的 finding set 为空，范围同为上述 exact tree 的
六个 owned paths。Parent 核对 category/caller 分支、literal suite inclusion、同 run PASS
coverage、历史 argv 与 fresh receipt；没有 unresolved task-owned finding。两份独立 native
review 已完成并保留为本轮历史证据，未将 Kimi exit 0 / partial output 转为 acceptance。
本任务离线实现已具备本地交付证据，publication blocker 仍保留。

最后复核发现并发 owner 修改了 `AGENTS.md`、`CLAUDE.md`、playbook 与
`.claude/agents/harness-reviewer.md`，当前 constitution 明确取代从 T3 推导的双审默认，
改为 tests/Harness 后按 SUBAGENTS.md 低频 Risk Gate 判断；本轮 plan 的双审段据此成为
历史 routing，不作为后续默认要求。本 session 未编辑、stage 或 commit 这四个 paths。
当前 Parent 核对的 literal coverage、调用分支、unknown/infrastructure fallback 和 receipt
兼容性均有 executable evidence，没有新的重大后果与实质验证缺口需要追加 review；不再派发。
已发生的两个 Kimi failures / 13 review requests 与 native reviews 不重写。

## Publication And Remaining Work

六个实现/spec/plan/research owned paths 保持 staged；审查时本记录单独保留 local untracked，
完成后仅显式 stage 本记录。它不属于原 receipt scope。其他 producer source/docs 保持原样。
`tests/test_typed_causal_native_expression.py` 与对应 source 仍未进入 HEAD；提交当前 policy
会在 fresh checkout 引用缺失测试。因此 commit/push blocked，未夹带这些 producer paths，
未 force push。解除条件是 producer 以其适用 verification/review 完成依赖提交，再核验
本 task 的新 snapshot；旧全量的 calibration FAIL 仍由其 owner 处理。

没有 live Video Provider submit、Production mutation 或媒体验收；Kimi 是受管 remote
analysis，实际费用未知。记录操作不调用 Provider，也不刷新 RAG。experience 查询因
library-incompatible shard 返回 exit 3，CLI 已排队本地 derived-index 维护；未等待 / 重试，
不宣称索引已经 fresh。

## Learning Evaluation

`distill-ai-video-learning`：`no_candidate`。本记录是单条 engineering implementation chain，
没有独立支持 attempts、受控多 arm 或可更新的 scoped Learning Claim；并发与不同选集
也不足以支持性能推广。未创建 placeholder claim，未发起 adoption 或确认流程。
