# Vidu Reaffirmed Profile Resample Spec

## Goal

允许已知质量失败后的同一 Vidu Shot 在原 operator upper bound 纯时间续期后，继续使用既有有界 seed resample；保持 exact request delta、历史计数和 paid gates 的真实性。

## Scope And Ownership

`vidu_profile.py` 验证旧、新 `ViduProviderProfile` 的 typed reaffirmation：旧、新 hash 由 profile 本身计算；除 `pricing_observed_at` / `pricing_expires_at` 外所有配置完全相同，新有效窗口最多一小时且时间前进。该 proof 只表示内部上限续期，不表示官方报价或余额。

`generation_feedback.py` 从显式提供的 proof 与 canonical baseline/request/candidate 构造干预；`generation_decision.py` 是唯一选择 owner，只有 proof 对应 baseline 与当前 Vidu candidate 时，才允许 resample 声明 `provider_profile` 与 `seed` 两项实际 delta。`generation_diagnosis.py` 与 compiler 仍比较原生请求全部字段，不豁免其他差异。`ProductionStateCommitter`、Budget Guard、cloud-egress、secret supplier、permit、fetch、QA 与 timeline 不改变。

`ProductionPlanningService.prepare_generation()` 将同一 typed proof 传给共同 feedback 入口。已提交 resample 后，若 canonical baseline 已指向 proof 的当前 profile，同一 orchestrator 再次 `prepare()` 时不继续注入已消费的 proof；其他 pointer mismatch 仍拒绝。

## Invariants

- 旧 `DecisionInputs` 无 proof 时的序列化、snapshot hash、seed-only resample 和历史 replay 保持兼容。
- Proof 必须绑定 baseline 的旧 pointer 与候选的新 pointer；配置、上限、币种、结果来源/信任、下载上限或 Provider 变化不能冒充续期。
- `max_resamples` 按同 Shot / Provider / model / mode 的已提交尝试累计；续期、任务名、干预名或新 pointer 不重置计数。`unknown_outcome` 继续 fail closed。
- 每次新 submit 仍须独立剩余额度检查、预算预留、egress、exact preview、durable intent 与 one-use permit；proof 不是执行授权。
- 不改变旧 profile 或第一次失败媒体的 bytes、receipt 与消费。

## Acceptance And Verification

标准反馈入口以真实旧/新 sealed profile 构造 `DecisionInputs`，在纯时间续期时编译出仅 `provider_profile`、`seed` 两项 delta；应用层入口透传该 proof，复用 orchestrator 能读取已提交结果；无 proof、错误 pointer、变更非时间配置、超时窗口均拒绝。已提交一次 resample 后再次续期仍被原 ceiling 阻断。针对性测试、changed-path Harness、适用独立审查完成后，才进入下一次有界 live submit。

## Self-Review

本 spec 只修复已有反馈链的 profile delta 表达；没有重命名失败重试、增加 Provider、重置历史或以 profile 续期推断质量改善。旧请求兼容由空 proof 不入序列化及回归测试保护。真实画质仍须每 Shot exact MP4 的独立分析、观看与明确判定。
