# Applied Submit Quota Inheritance

## Goal And Evidence

本任务第三次 Vidu REQUEST 在 physical POST 前被拦截：首 attempt ceiling=3，第二 attempt 通过 canonical receipt 扩至4并已 fetched、quality rejected；新 attempt ceiling=4、used=2。当前 guard 仅接受绑定当前 attempt 的 extension，错误地把沿用4判为再次扩额。Manifest110无新 paid intent/permit；physical consumption仍2/4。

## Contract And Scope

保留 exact target 的首次扩额路径。后续同 task 可以继承 active budget 中已生效的上限，仅当 extension target 的 exact binding仍保留、target已 terminal、paid outcome accepted且 exact fetch存在。继承不是重放授权：不得调用 extension mutation、追加slot、减少used、恢复旧permit或复用旧preview。当前 ceiling 必须等于 retained receipt的新上限；current/ancestor task一致。未提交、仍running、unknown或无fetch的 ancestor 不可作为继承依据。

唯一 quota owner `paid_provider_submit_quota.py` 提供 read-only predicate；committer沿用原 durable count、上限耗尽、local policy、Budget Guard与fresh intent/permit gates。strict reader继续验证 ledger lineage、project与 exact bindings。不改变 schema、旧 receipt、historical failures或金额。

## Verification And Acceptance

回归覆盖 direct target、已完成 ancestor、未完成/unknown ancestor、其他 task/更高cap、durable used reset和耗尽。标准 loader重开真实 REQUEST并运行完整 submit binding guard，无外部效果。T3 stable snapshot进行双独立 read-only review，Parent裁决后继续同一已授权 REQUEST。用户禁止worktree，direct checks明确不冒充canonical Harness receipt。

## Self-Review

授权来自当前目标内必要预算契约修复；没有新增 budget、Provider或素材。仅继承已实际用于known fetched media的上限，拒绝不确定状态；所有提交仍有当前 exact authorization和one-use permit。源码/tests与matrix同步。
