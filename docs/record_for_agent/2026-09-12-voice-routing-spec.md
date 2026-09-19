---
record_kind: research_note
topic_id: voice-source-routing
learning_eligibility: ineligible
---

# Voice Routing Specification Checkpoint

## Current Checkpoint — P1 Fixes, 2026-09-13

用户要求“修复”后，已确认 Voice Router 接管本轮相关 committer、models、policy、matrix
和 baseline 的收尾写入，Vidu Ad 暂停对应共享文件写入；保留双方既有内容。下节的
“P1 未修复 / ownership 未确认 / 下一步先确认 ownership”为历史状态，已由本节替代。
Spec 仍为 proposed，implementation 为 in_progress，尚未正式验收。

已修复两项原始 P1：

- 既有 voice owner 持久化 `voice-routing-execution/1` envelope，receipt 保存 paired
  task/hash；标准 reader 与 candidate aggregate hash 重开同一证据，旧字段缺省 bytes 不变。
- R+1、R+2 和 paid intent 在原 committer 锁内验证当前 QA、lineage、exact handoff；
  paid owner 核对 voice credential/currency/cost，并在当前 monetary ledger 对 voice/video
  做联合预算验证。直接调用 committer 不能绕过 wrapper 检查；缺 paid preview 先于写入阻断。
- 当前 task 的 voice/video submit 按 durable provenance 合计去重，拒绝少报计数；历史样本
  和其他 task 不消耗本 task quota。已有 routed voice submit 后增大 ceiling 仍 fail closed，
  未新增额度扩展 owner。只忽略锁内正在验证的 exact own RUNNING voice，不豁免 UNKNOWN。

Native reviewer_xhigh scoped re-review：accept with concerns，原始 P1 无剩余阻断。
此 verdict 不涵盖 Vidu Ad，也不等于全 spec、真实 Provider 或声音质量验收。VR-03 qualified
positive fixture 已完成，主线程复跑 1 passed in 16.98s：两个不同 Shot 的 distinct-SHA
canonical MiniMax 样本，经标准 graph/render 与 permit-consuming P6 human receipt，
使实际 Router 从 EVIDENCE_REQUIRED 转为 SEPARATE；native 继续阻断。该 human receipt
是离线 fixture，不能冒充真实听感。mixed-history 和 paid-stage QA race 未各自增加独立用例。

Production 大组暴露并修复一项兼容回归：新增 paid intent artifact 重开原先也作用于旧
receipt，导致历史 paid fixture 无 `state/voice/attempts/<id>` 时提前失败。现只对显式
`routing_binding_hash` receipt 执行新增检查，旧 paid join/ledger/permit 契约保留；新路线
缺工件返回 typed AiVideoError，无 legacy fallback、Manifest 写入或 transport。
该补丁与 VR-03 的最终 reviewer_xhigh scoped re-review 同为 accept with concerns，无阻断。

已完成的当前 working-tree 验证：

- 最终补丁后主线程组合：全部 8 个 Voice Router 测试文件与 paid-provider e2e/state 两文件，
  **98 passed in 99.43s**；这是本轮最终行为回归结果，取代下列较早专项快照作为修复证据。
- Voice Router contracts/integration/guards/handoff/execution/P4/binding：45 passed in 80.37s。
- 主线程单独复跑 binding：8 passed in 19.89s；含真实 QA revision mutation、直接 committer
  预算/credential 拒绝、缺 paid preview 的零 transport，以及 current-task/forged-counter 回归。
  随后新增 missing binding artifact 负向用例，worker 复跑 binding：9 passed；修复后的
  `test_production_paid_provider_e2e.py` / `test_production_paid_provider_state.py`：51 passed。
- 较早修复后 MiniMax/ElevenLabs 与 Voice Router 组合组：141 passed；最终专项结果以上条为准。
- Architecture Gate：0 errors、26 warnings、13 infos；runtime-skill boundary：2 passed。
- 文档契约通过，受限 tracked diff 与 12 个 task-owned untracked 文件 whitespace 通过。
- Harness explicit inspection 覆盖新增 envelope、committer/reader/contract 与测试路径，
  `closure_eligible=false`；policy audit 仍只报告下文三个既有 unmapped paths。

Production 大组实际为 3358 passed、44 failed、3 skipped（1250.49s），是上述兼容补丁前
且包含并发 Vidu Ad 改动的快照；44 失败中 41 属于已修复的 paid fixture 回归，3 属于
Vidu Ad 新 policy category/check 与旧 Harness 断言不一致。其后完整 Harness 测试为
160 passed、2 failed：production selector 已增加 `or vidu_ad` 而断言仍要求旧 exact 参数；
另一个失败是既有三路径 policy audit。没有调整其他任务的测试/策略以伪造全绿。
单独 paid budget extension 组 21 passed（6 个既有 serialization warnings）。
没有 fresh passing Harness receipt，未 stage/commit/push 或创建 worktree。真实 Provider、密钥、Production 媒体、S03、
历史 QA/unknown 与 S04 未触碰。record-ai-video-session 更新同一记录；
distill-ai-video-learning 为 no_candidate，本轮 deterministic fixtures 不是真实声音质量证据。

## Historical Checkpoint — Implementation In Progress

2026-09-12：用户随后要求“实现specs”，并确认保留既有改动后追加更新
`.agent/harness/policy.yaml`、`docs/agent-primary-contract-matrix.md` 与
`docs/v0.2-runtime-baseline.md`。下文 docs-only / not_started / 等待 spec 审阅的状态
与下一步均为历史；当前 spec 仍为 proposed，implementation 为 in_progress，未验收。

新增 `voice_routing_contracts.py`、`voice_routing.py`、`voice_routing_handoff.py`，并接入
既有 Shot/Planning/candidate/Router/compiler/execution、generated-video-audio 与 P4
composition admission。旧字段省略/hash、AudioNeed.REQUIRED、canonical owners 保留。
共享 monetary Budget Guard 在 TTS 前对所选 voice/video 的 exact previews 做纯 reserve
验证；count-based MiniMax batch 不能混用视频 monetary ledger，没有新增预算 owner。

Native reviewer_xhigh 的 implementation verdict 为 reject，不能沿用历史 spec accept：

- voice route/task binding 尚未在 canonical voice committer 的锁内持久化和重验；调用前
  QA/readiness 检查仍有竞态，当前 voice submit 计数还会混入历史或其他 task。
- 必须追加修改既有 dirty `_state_commit_voice_intent.py`、
  `_state_commit_voice_activation.py`、`_state_commit_paid_provider.py` 才能闭合该 owner。
  已提出精确 ownership 问题，当前未获回答；这三个文件未由本任务修改。
- VR-03 独立固定声线 qualified positive evidence 的完整真实 loader/receipt 测试未完成。
  同模型、seed、voice_id 或 imported WAV 均不能替代该证明。

新 P4 测试通过实际标准 loader 与既有 committer/service，依次执行 fake MiniMax voice
activation、fresh video Planning、fake Vidu submit/status/settle/fetch/activation，再交
`resolve_composition` 检查 exact video SHA、voice provenance 与完整 speech span。
负向覆盖账本不匹配前零 TTS 调用、trim、错误 asset/track、缺 binding；execution replay
不新增 TTS submit。仅在 pytest 临时目录生成确定性 ffmpeg fixture；没有真实 Provider、
Production 媒体或质量验收。

已实际执行的 working-tree 验证：

- 核心 legacy/Planning/Router/compiler/execution/composition 回归组：605 passed；这是本轮
  较早快照，不能代替最终 exact snapshot 的 receipt。
- 主线程最终 voice contracts/integration/guards/handoff/execution/P4 专项组：37 passed
  in 52.54s；对应 `.agent/harness/policy.yaml` 的 `voice_source_routing_tests`。
- 按 changed-path checks 补跑其余 62 个 pytest 文件：2152 passed、3 skipped、16 warnings
  in 1008.92s；warnings 来自既有 paid budget/quota fixture 的 Pydantic serialization。
  该组排除了上列已跑的核心回归与 voice 专项，不是全仓库或隔离 snapshot closure。
- Harness/docs/runtime-boundary 测试：188 passed、1 failed；唯一失败为既有 policy audit
  的三个 unmapped paths，见下文精确列表。没有修复或隐藏该债务。
- Architecture Gate：0 errors、26 warnings、13 infos；属于 working-tree 检查，非 receipt。
- 文档契约、tracked diff 与 11 个任务 untracked 文件的 whitespace 检查通过；index 与
  开始前保存的 `git ls-files --stage` 快照一致。

尚无 fresh passing Harness receipt；没有 stage/commit/push 或 worktree。其他 staged/dirty
工作保留，不能把依赖其中现有 helper 的 fixture 通过描述为可独立发布快照。
下一步先解决上述三个源码文件的 ownership，再完成锁内 exact binding/task accounting、
固定声线正向测试与 reviewer_xhigh scoped re-review。未授权 live/付费/重生、S04 或历史
QA/unknown mutation。record-ai-video-session 更新本记录；distill-ai-video-learning 评估
为 no_candidate：本轮工程 fixture 不是新的独立 Provider/媒体质量实验。

## Scope

用户确认需要在视频生成前选择原生声音或独立配音，随后明确要求先写 spec。
已编写 [Voice Routing Spec](../superpowers/specs/2026-09-12-ai-video-voice-routing-design.md)，
状态为 proposed / not_started，等待用户 review；不构成实现或新付费调用授权。

## Evidence And Boundary

只读 mapping 确认现有候选构建沿用注册 target 的 output_requirement，Router 没有 voice source
decision；旧 AudioNeed.REQUIRED 代表必须原生音频。Spec 提议新增 sealed voice-routing/1，
保留现有 selector、committer、P4 owners，按硬要求过滤后在同等候选中优先原生。
固定 voice_id、模型支持 audio 和真实声线验收分开；unknown 不能通过换路线恢复。

文档契约检查与新文件 whitespace 检查通过；runtime-skill boundary 2 passed。
Native reviewer_xhigh 首轮指出 SEPARATE 原生环境声语义矛盾与 ledger/lifecycle/handoff 检查缺口；
修订并新增 VR-13 后 scoped review 为 accept with concerns，唯一非阻断措辞建议亦已由主线程修正，
明确只验证实际所选同项目或跨项目布局，不要求两者同时存在。
Harness policy audit 仍有三个既有 unmapped paths，未修改其 owner 文件，未生成完整 passing receipt。
本轮只新增 spec 和本记录，没有 runtime/历史媒体修改，没有 Provider/secret 调用、stage、commit、push 或 worktree。

使用 brainstorming 进行设计自检，retrieve-ai-video-memory 返回 fresh 的历史 source-audio advisory
记录；没有把历史 blanket mute 建议当作当前规则。record-ai-video-session 完成本 checkpoint；
distill-ai-video-learning 评估为 no_candidate，本次未产生独立真实媒体实验或新的质量结论。

## Final Consistency Check — 2026-09-12

续接窗口完成用户限定的最终一致性检查；未发现需要实质修改的遗漏或矛盾，spec 原文保持
`proposed` / `not_started`，13 项验收标准保留。本窗口仅补充本节，未重复独立审查，
上一窗口的 review verdict 仍只作为历史 review 结果。

重新核对 canonical selection/P4 ownership、历史兼容和所选 SEPARATE 布局边界；限定源码
核对确认 voice admission 的 RUNNING/OUTCOME_UNKNOWN 拒绝条件和 generated-video-audio
的 Manifest 2.0–2.2 / Registry 2.1 限制仍存在。experience 检索返回 fresh advisory hits，
不将本 spec 自身的检索命中视为独立设计证据，也不恢复旧 blanket mute 建议。

实际验证：

- `python -m scripts.agent_harness inspect --path docs/superpowers/specs/2026-09-12-ai-video-voice-routing-design.md --path docs/record_for_agent/2026-09-12-voice-routing-spec.md`：仅 documentation，fallback 为空；explicit scope 的 `closure_eligible=false`。
- `python -m scripts.docs_contract_gate check`：通过。
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/test_runtime_skill_boundary.py -q`：2 passed。
- 两个 untracked 文档分别通过 `git diff --no-index --check /dev/null <path>` 检查。
- `python -m scripts.agent_harness policy-audit`：退出码 1，既有 unmapped paths 仍为
  `src/ai_video/production/image_import_video_frame.py`、
  `src/ai_video/production/paid_provider_no_effect_reconciliation.py`、
  `tests/test_paid_provider_no_effect_reconciliation.py`；最后一项同时为 unreferenced test。

以上是当前 working tree 的直接检查，不是 exact staged/commit snapshot 的 Harness closure；
没有 fresh passing receipt。保留全部其他 staged/unstaged 工作，两个任务文档仍为 untracked，
未 stage/commit/push、创建 worktree、调用 Provider、读取密钥或生成媒体。
本次记录与学习评估为 `recorded` / `no_candidate`：没有新增实验或质量证据。
下一步仅等待用户审阅 spec；确认 spec 不授权 implementation、live、付费或重新生成。
