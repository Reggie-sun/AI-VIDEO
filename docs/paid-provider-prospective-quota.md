# Paid Provider Prospective Quota

## Scope And Owner

`paid_provider_submit_quota.py` 与 `ProductionStateCommitter.extend_paid_provider_submit_quota()`
继续独占显式追加一次 paid submit 的授权与写入。此契约处理旧素材已经成功下载、仍待验收，
而用户明确要求同一 Shot 的新 goal 版本的情况；不新增状态、自动关闭、退款或重试机制。

## Pending Review Exception

除目标 REQUEST 外的 RUNNING / OUTCOME_UNKNOWN 通常继续阻断额度扩展。唯一例外是
extension 明确指定的 prior attempt：已知 paid accepted、处于 VALIDATE、有严格重开的
exact fetched media 与对应持久评价记录，且新 target 仍是相同 task / Shot，使用当前
选中的 QA 和同一 goal identity 的明确新 goal version。新 binding 必须完整保留旧证据，
不能用新 QA 重算旧 verdict，不能把缺失证据转成 PASS。

旧 attempt 保持待验收，旧 request、fetch、QA、experience、paid receipt 与 reservation
保持原义。新请求不能声称旧素材通过，也不能沿用旧失败作为新 goal 的 repair intervention。
这一例外不放行其他未结束的 attempt、仍在生成/下载的任务、未知结果、缺失或错绑证据、
同 goal 的盲目重试、未获授权的调用或已激活素材的隐式替换。

三个既有入口共用 `video_pre_generation.verified_fetched_prior_for_new_goal()`：
逐条重开旧 experience 的 projection、candidate、exact media 与原 QA snapshot，
使用原 acceptance 校验 source identity、criterion 和大小，要求完整 raw requirements
全部为 NOT_EVALUATED。缺少 snapshot 的旧记录仍可历史重开，但不能使用此新放行例外。

生成目标图的更新仍由原 transaction owner 写入，且仅允许原 Project/Registry 不变、
新旧图均为同一 Shot/role 的 canonical pre-generation graph。预算追加仍由原 budget
owner 处理显式授权、CAS、上限及有效期；它保留原 reservations，不推断退款或真实费用。

## Unchanged Gates

额度仍只能增加一次，并绑定 exact prior/target、原 task、Manifest CAS、当前 ledger、
human opt-in 与有效期。Budget blocked/unsettled、金额上限、历史已用次数、secret、
cloud egress、durable intent 和 one-use permit 检查保持有效。扩展本身不调用 Provider、
不改变金额和 reservations、不激活媒体。Exact replay 继续验证原 sealed receipt。

## Verification

Focused verification：

```bash
python -m pytest -p no:cacheprovider tests/test_production_paid_submit_quota.py tests/test_production_paid_budget_extension.py tests/test_generation_execution_guards.py -q
```

实际媒体仍需针对新 exact bytes 独立完成 Per-Shot Gate；工程测试不产生质量通过。
