# Canvas Paid Known-No-Effect Retarget Plan

Date: 2026-10-11
Status: Authorized within the reusable-canvas task; Parent self-reviewed; implementation pending.

## Goal And Scope

用户目标是复刻原画布；最新澄清撤销Parent误加的固定Fast2.0/禁止2.5限制。保留480p、原剧情、
参考职责、动作/视点及声音要求。旧Fast请求是已知HTTP403无effect，下一候选可选择可用Seedance模型，
不要求清零历史或把physical POST改成not_submitted。
本slice只补同一Canvas/Shot/task的显式paid known-no-effect retarget；不授权任意自动fallback、unknown retry、
新Provider或无限submit，也不证明新模型可用性或作品质量。

## Current And Target Behavior

当前Canvas repair只接收closed quality rejection；runtime grant只允许原recipe scope重执行。
目标：closed paid no-effect失败可从同入口prepare，仍返回RUNTIME_FAILURE直到唯一committer登记exact grant；
grant显式指定失败paid receipt与目标candidate scope，仅该scope获得一次normal generation，submit intent原子消耗grant。

## Contracts And Owners

- `generation_runtime_repair.py`：在原owner增加`PaidNoEffectRetarget`，绑定failed submit receipt fingerprint与target scope。
  `runtime-repair/3`仅携带这一payload，与local extension互斥；旧/1和/2的serialization/hash/replay保持。
- `_state_commit_video_runtime_repair.py`：registration与submit前重验FAILED、exact latest same-Shot/task runtime evidence、
  canonical paid KNOWN_NO_EFFECT receipt且无effect/fetch；错receipt、unknown、accepted、local extension组合、重复/过期grant拒绝。
  原per-Shot ceiling2与submit计数保持；新paid调用仍需独立preview/预算/egress/permit。
- `generation_decision.py`：retarget必须命中授权scope，且保持同Provider、mode、requirement、rubric、seed、editorial、
  FinalOutput goal与hard expression；允许目标model/profile/compiler/raster capability变化，required duration/fps/audio保持。
  不消除冲突、unknown或其他failure class。旧grant仍要求原scope。
- `canvas_production.py` / `canvas_recovery.py`：显式repair接受closed canonical paid no-effect，允许空quality interventions；
  不自动登记grant/submit。唯一successor必须由exact evidence与registered runtime grant链接，fork/循环/断链拒绝。
- `docs/agent-primary-contract-matrix.md`独占新增详细契约；baseline/plan/record只报告状态与链接。

## Compatibility And Boundaries

不新增Manifest schema、state writer或第二timeline。原failure receipts、experience、媒体、消费与task identity不可更改；
先前quality repair及local extension行为保持。新/3在旧runtime fail closed；旧receipts不用新字段重算hash。
资源包观察不是paid permit，也不证明API key与console账号一致。model选择与观众验收仍独立。

## Acceptance And Verification

1. 未登记grant、错误target/receipt、unknown/accepted/no runtime evidence均不创建替代submit；旧策略grant不可授权新策略。
2. 正常paid失败→capture runtime evidence→explicit grant→同入口successor→submit原子消耗→reopen/replay，保留完整计数。
3. 预算耗尽、task改名、fork、重复grant、篡改receipt和不符semantic要求fail closed。
4. `tests/test_generation_runtime_repair.py`与`tests/test_canvas_recovery.py`先RED后GREEN；运行changed-path Harness、
   exact staged receipt与Parent Risk Gate。若triggered仅一份受管read-only Kimi review，Parent裁决。
5. 工程完成后才封存同task下一finite1-POST/0重抽单元；fresh exact preview/preflight/预算/permit完备才调用。
   exact MP4立即显式project-local MCP、新片完整动作/声音proof及normal composition/HyperFrames/用户验收分别取证。

## Major Milestones

### M1 — Exact Retarget Contract And Decision

增加versioned immutable payload与pure decision边界回归，验证旧receipt byte/hash兼容及semantic保护。

### M2 — Sole-Committer And Canvas Recovery

增加canonical paid proof/replay/one-use检查，接通同入口与唯一lineage；以normal paid fixture覆盖successor与failure paths。

### M3 — Verification And Bounded Media Continuation

同步canonical docs，验证、判断Risk Gate、owned commit/push/remote-SHA。重新选择actual profile与声明原来源差异，
不将工程验证或旧human声音/动作回复当新片PASS。完整spec AC-2/AC-7保持未验收直到对应真实证据成立。

## Self-Review

属于已授权目标内必要恢复规则补齐；不覆盖原local授权，不降低真实验收，不扩大Provider/credential/输入scope。
最新user clarification恢复model选择裁量，不授权隐藏model差异。Kimi调查的cancelled/unknown输出不作依据或复用，
新review若触发须绑定新的stable implementation snapshot，而非重试旧mapping。
