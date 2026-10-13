---
record_kind: research_note
topic_id: production-workflow-latency-audit
learning_eligibility: ineligible
---

# Production Workflow Latency Audit

Date: 2026-10-13

## Supersession Notice - 2026-10-14

用户已要求实施；[Harness implementation](2026-10-14-harness-latency-implementation.md) 落实数据/runtime routing、image boundary 去重、只读 lineage routing、early snapshot drift stop 与 focused/final cadence。下文诊断及历史计数保留；“所有建议保持未采用”仅描述审计当时。全局 Kimi mandatory/maximum policy 与真实媒体验收要求保持原样。

## Scope And Evidence

用户要求查看近期 Codex 制作会话，识别重复流程与过宽 Harness 验证。本次是诊断，
没有修改 Harness、Skill、Provider、预算、验收或生产代码，没有图片/视频生成。
核对 10 月 11–13 日 AI-VIDEO root 会话，重点是 reusable Canvas、真实两镜验证和原剧本
S01/S02 候选；会话总跨度包含用户等待，不能当作纯执行耗时。测试成本取 canonical
receipt 的 started_at/finished_at、duration_ms 与对应 JUnit，未重新执行历史测试。

| Exact receipt under `.agent/harness/runs/` | Result | Duration | Evidence |
| --- | --- | --- | --- |
| `canvas-asset-first-20261013-r2/receipt.json` | passed | 41.20 min | 34 changed paths；6,297 testcase executions，4,257 unique classname/name identities，2,040 extra executions |
| `canvas-image-authoring-lineage-20261013-r1/receipt.json` | passed | 7.49 min | 7 changed paths；2,195 executions，1,633 unique identities，562 extra executions |
| `canvas-harness-completion-20261012-candidate3/receipt.json` | failed | 41.68 min | 所有执行 checks passed，但 `source scope changed during verification` |
| `canvas-harness-completion-20261012-candidate4/receipt.json` | failed | 42.47 min | 同上；两轮合计84.15 min，不能作为稳定最终版本证据 |
| `jieshi-original-source-20261013-r2/receipt.json` | passed | 5.77 min | 603 executions；Canvas workflow 290.5 s，preserved source 29.5 s |
| `canvas-asset-first-A-evidence-20261013-r1/receipt.json` | passed | 2.32 s | 单一证据记录，5项基础 checks |

JUnit identity 是重复执行指标，不证明不同执行环境/fixture 的语义等价，也不授权直接删除
测试。上述 broad implementation 涉及 paid/state/reader 等共享边界，本身确有集成验证理由。

## Verified Bottlenecks

1. **跨套件重复。** asset-first 的 image/state 重叠935项，image/reader重叠557项。
   按实际检查顺序累计，重复 testcase 的 JUnit时间约357.57 s，其中 image 内已跑过的
   用例322.22 s。可优先验证同一 snapshot 下的测试并集/精确覆盖关系，保留每个原有
   必需用例；这不是“重复32%的用例就能省32%的墙钟时间”。
2. **范围映射太粗。** `.agent/harness/policy.yaml` 的 `canvas_production_workflow`
   把 `docs/canvas-projects/**` 与 `src/ai_video/canvas_*.py` 放在同组；项目数据、README、
   图片与 runtime 改动都会触发完整 workflow suite。`production_image_tests` 同时含完整
   reader/dependency/state/recovery。lineage 小修复仍执行1,288项图片测试，386.3 s。
3. **最终候选未真正稳定。** candidate3/candidate4 两轮跑完才因源码变化失效。
   会话 `01a12fa2-e1c3-7a02-9ae9-93f286f88d7c` 在 Harness 运行期间继续补实际区间/音频
   修改。应先完成 focused修复并稳定 owned bytes，再跑一次最终验证；不能降低 freshness。
4. **真实验证目标偏离。** 会话 `01a13121-f295-7043-8e9a-c2971fabb29b` 选择
   “抬手机→起身”自编两镜，之后经过 shared runtime 修复、多轮工程验证和Provider拒绝恢复；
   用户指出它不是原前15秒。当前记录
   [two-shot correction](2026-10-13-canvas-two-shot-continuity-preflight.md)
   和 [original candidate](2026-10-13-jieshi-original-s01-s02-candidate.md) 已明确该差异。
   自编单元可测技术接线，不能替代用户原剧本验收。
5. **Delegation 固定成本。** global Subagent Strategy 强制多数non-trivial任务至少一次Kimi；
   installed `external-subagent` 又将新seal归一化为deep/max及最高有限额度。与较早默认worker
   的文字有差异。应由用户明确调整适用global policy后收窄固定调用范围；当前诊断不绕过它。
   10月12日Canvas会话还出现review报告hash/未读行范围拒绝：这是protocol取证成本，
   不是产品发现，必要review仍须保留，包应聚焦实际边界。

## Proposed Priority

1. **立即改善执行节奏：** 先锁定原剧本与两镜AC；迭代阶段仅跑相关测试，完成所有修复后
   才跑一次最终exact Harness。准备/制作按现有已发布能力推进；只有真实能力缺口才改共享代码。
2. **精确去重：** reuse现有 `covered_by_check_ids` / `covers_check_ids` owner或统一所选pytest
   用例并集；只有证明完整覆盖且同一snapshot已PASS才能跳过。不得用重叠935项来删除整个
   962项state suite。行为修订前须验证selectors、fixture、JUnit与receipt覆盖语义。
3. **区分项目数据与工程修改：** 对project/source/reference数据运行strict schema、identity、
   inspection/author/preflight及必要接续检查；runtime recovery/paid/shared state改动继续对应
   集成测试。README/image-only不应自动牵出全套故障恢复。
4. **按职责拆check：** 保留共享state/recovery安全测试，避免每个image/audio/dependency套件
   复制同一完整集合；generation/routing与Provider-specific测试按实际changed boundary触发。
5. **减少流程附加成本：** 不因Spec/Plan、文档或diff大小追加independent reviewer；现行Risk
   Gate已是低频规则。非平凡任务的mandatory mapping及deep/max sizing需单独调整其global owner，
   不能只改项目Harness。

## Boundaries And Completion

逐镜exact MP4、实际声画观察、accepted前镜状态→后镜绑定、剪辑接点与最终1.0x听看不能删除。
当Agent无法听音时，应对同一媒体补证，不能用ASR或重抽替代；当前原S01还有clean plate/
局部合成缺口，见原候选记录，减少pytest不会自动解决这些制作条件。

文档/规则/Architecture check在重型run中仅数秒；不建议优先删掉这些低成本保护。
新文件未注册的policy-audit失败应先补精确映射，而不是触发或容忍full fallback。
本次核对实际policy/code，并使用CodeGraph核对 `verify_inspection` 调用关系；未宣称
测试并集去重、细分routing或具体提速已经实现。

受管只读Kimi invocation `20a5aabe-2fa6-44e2-96a1-41f2e35e7e77` 绑定脱敏receipt投影，
实际2次authenticated k3/max请求、194.09 s、PARSED/exit0，source/report hashes已核验。
Parent确认串行执行及重复热点；不采用其“周期性scope_diff_check检测source drift”建议：
当前该check仅执行 `git diff --check`，只能检查patch格式，不能证明source hash稳定。
也不依据Provider名称未出现在changed paths就删相关checks：shared state/routing存在跨模块影响，
必须先证明精确dependency/coverage。此调用是mapping，不是implementation review或成片验收。

`retrieve-ai-video-memory` 返回library-incompatible shards/exit3，按Skill停止重试并从当前
会话/源码/receipt取证。`record-ai-video-session` 记录此诊断；自动
`distill-ai-video-learning` 为 `no_candidate`：这是同一演进链的离线审计，没有controlled
优化前后实验或足够独立性证据，不制造learning确认步骤。所有建议保持未采用。
