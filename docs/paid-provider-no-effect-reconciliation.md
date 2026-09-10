# Explicit Paid Provider No-Effect Reconciliation

## Scope

`ProductionStateCommitter.reconcile_paid_provider_no_effect()` 用于显式关闭已持久化的
video `OUTCOME_UNKNOWN`，且 operator 已验证失败发生在 transport 之前。它不自动推断
远端无效果，也不允许对已有 Provider submission、observation 或 fetched media 的 attempt 使用。

## Evidence And Authority

`PaidProviderNoEffectReconciliation` 绑定 project、attempt、原 unknown submit receipt、
base budget、expected Manifest revision、operator、用户授权 receipt、有效期和完整证据字节。
注入的 `authorizer(entry, evidence_artifacts)` 必须验证具体证据并返回 exact `entry.actor`；
仅有用户授权或一个 `no_http=true` 字段不能证明未提交。

标准 reader 校验证据、receipt 和 budget 的身份及关联，不运行 authorizer，也不执行
网络、Provider 或媒体操作。该边界依赖可信 operator 对证据的判断，不能宣称从一个
本地布尔值数学证明远端没有副作用。

## State And Compatibility

唯一 committer 追加 reconciliation、evidence、新 `KNOWN_NO_EFFECT` receipt 和新 budget，
然后原子更新 Manifest。原 unknown receipt 与原 budget 字节保持不变。
只释放绑定的 `UNSETTLED` reservation 为 `RELEASED` / actual cost `0`；不提高金额上限，
不修改其他 reservation，不复用原 permit，不自动启动新 attempt。

新 submit receipt 的可选 `no_effect_reconciliation` 仅在有值时序列化，保持旧 receipt
的 exact bytes/hash 兼容。相同 reconciliation 的重放只读，不重新调用 authorizer。
证据篡改、错 attempt、错 base、过期授权、已有远端效果或不确定关联必须 fail closed。

## Replacement Generation

显式对账为 pre-transport no-effect 的终止 attempt 可由既有 feedback owner 记录为
`not_submitted`，保留 exact request / recipe / QA / task identity。普通 runtime failure
和未解决的 unknown 不获得此例外。已消耗的 durable submit permit 仍计数；替代执行需
新 attempt、新 binding、既有有界 quota extension、新 preview、authorization 和一次性 permit。

## Verification

专项回归：`pytest -q tests/test_paid_provider_no_effect_reconciliation.py`。
必须覆盖严格 reopen、旧 hash 兼容、拒绝/篡改无写入、expired exact replay、authorizer
跨有效期、crash boundary、后续合法 reservation，以及 no-effect feedback 到新 request
的完整路径。工程回归不构成媒体质量、人审或 production activation。
