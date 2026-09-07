---
surface_id: generation_feedback_orchestration
canonical: false
spec_status: accepted
implementation_status: implemented
live_status: not_run
quality_status: not_evaluated
release_status: unreleased
runtime_status_owner: docs/v0.2-runtime-baseline.md
roadmap_owner: docs/v0.2-agentic-production-roadmap.md
contract_version: generation-feedback-orchestration/0.1
---

# Generation Feedback Orchestration

## Goal And Authority

让首次生成及每次失败后的下一方案，由可复用的经验与干预策略产生，再交由现有 Router 选择；
形成 Local + Cloud 共用的 `evidence → decision → controlled attempt → evidence` 闭环。
目标同时包含减少无效生成和提高后续整镜可用率，不能只用“更早停止”代替质量收益。

本文件是轻量补充 spec，沿用既有 [generation decision contract](2026-09-06-ai-video-generation-decision-loop.md)，
定义生产接线、输入生产者和反馈职责。用户随后明确要求“实现”，授权本 spec 的代码与离线验证；
此前禁止 Provider/media action、commit/push 的限制继续有效。Creative revision、learning adoption
与 empirical quality acceptance 不由实现任务代为批准。当前实现与验证状态由 runtime baseline 维护。

## Evidence Baseline

审计核心基线为 `2ae1216` 加 `a4b54bf`；编写时 HEAD 为 `2761b34`。
当前 [runtime baseline](../../v0.2-runtime-baseline.md) 明确只有纯 decision/diagnosis API，没有通用生产 caller。
`VideoGenerationService` 消费已解析请求，不强制新 decision；Seedance、remote MiniMax H3、Hailuo
compiler 尚未提供新 recipe 要求的 native expression。FAIL 后的 intervention 主要由外部填写。

- [H3 S01 015–030](../../record_for_agent/2026-09-06-jieshi-s01-local-h3-bounded-repairs.md)：015–029 共 15 个 MP4 全 FAIL，分属 13 个 requirement hash；030 是 OOM，无媒体。
- [Vidu S01 02–04](../../record_for_agent/learning/vidu-s01-native-dialogue-burned-captions.md)：烧录字幕、掌向或机位失败持续；requirement/compiler/profile 的变化使 exact scopes 分散。
- 审计内存反例：空 delta 的 `production_repair` 改写 hypothesis 后仍可连续生成；跨 artifact 的不完整 proof 能合成 `supported`，即使完整 PASS 数为零。

上述是有限历史证据，不能外推为 Provider 全局能力结论。S01 后续 authoring 已变化；回放使用当时
exact request、rubric 与 verdict，当前任务另读 selected revision，禁止用新要求倒改旧结果。

## Scope And Ownership

覆盖全部现有可注册视频实现：ComfyUI H3、T8 Quality/Turbo/native V2 各 mode 及 family、Vidu
各已注册 model/mode、Seedance 全部已注册型号、remote MiniMax H3、MiniMax-Hailuo-2.3。

| Responsibility | Single owner |
| --- | --- |
| 当前上下文、历史投影、candidate/intervention 构造及循环推进 | 共用 production orchestration caller；实现时在合适边界建立，不扩张 Provider adapter |
| Candidate ranking、selection、最终 binding | 现有 `VideoGenerationResolver.resolve_requirement()` |
| Exact evidence 分类、干预比较与预测结果检查 | 现有 diagnosis/recipe 责任边界内的纯策略 |
| Native expression、技术 capability 与实际 submit | 对应 Provider adapter/profile；不自行决定 retry/fallback |
| Durable writes、effect intent、recovery、activation | 现有 `ProductionStateCommitter`；不增加 writer 或平行 quota ledger |
| Creative intent、评价尺度与验收 | 既有 authoring / acceptance / Gate owners |

不建设通用 Agent Runtime、训练平台、UI、队列或新 Provider；不重写 Legacy CLI，不改变 renderer、
timeline、付费授权、local exemption、逐 Shot Gate 或 P6/Final Acceptance。

## Decision Contracts

### 1. Common Caller And Submission Boundary

caller 从 canonical selected inputs、capabilities、receipts 和评价投影制造完整 `DecisionInputs`：
`candidates`、`evidence`、`interventions`、`conflicts`、`historical_recipes`、`baseline_request` 与当前 limits。
探索策略由显式版本化 policy 提供；不让每个 run script 自选一个 Provider 再伪装成候选比较。

每个新的 v0.2 production submit 必须关联当前输入、策略及完整历史投影下的 `GENERATE_ONCE`，
并校验所选 bound/compiled request、actual delta 和 decision identity 一致。验证进入既有执行入口，
不能只依靠 driver 自律；decision 不替代既有 permit。缺证据、stale decision 或 compiler unsupported
均不得提交，也不得自动退回无 recipe 路径；拒绝原因回流到同一 caller。

现有活跃 drivers 迁移到共同 caller；旧 public API 调用退出新任务路径。
历史 exact replay/recovery 保持原 bytes 与既有状态约束，不重新选择或产生新 submit。
Legacy 和批准的 qualification 是显式独立目的；不能通过调用方自行改标签或复制旧 request
把新的 production generation 伪装为例外。Qualification 的适用结果可被投影为证据，不算生产闭环验收。

### 2. Transferable Empirical Evidence

保留 exact artifact/request/rubric 身份，同时增加独立的经验适用范围：人物数量、动作与手部/道具交互、
对白长度及时间窗、camera motion、reference 结构、continuity 要求、Provider/model 和生成策略。
提取与匹配规则须版本化、可回放；未知特征显式保留，不能由 hash 相同或自然语言相似度冒充适用性。

同模式证据可跨 Shot/recipe 被考虑，但必须记录支持、反例、样本数、适用与排除原因；不能把 H3
成功直接记成 Vidu 成功，也不能因为 prompt、profile 续期或 Shot identity 改变就丢掉全部重复失败经验。
不同 rubric 只能在 acceptance owner 明确映射可比维度后迁移，不拼接不同 artifact 的局部 PASS 为整镜 PASS。

Router 使用上述证据区分 technically compatible candidates 的预期质量适配，提供可检验的条件估计
及不确定性；不得只按 unknown 维度数排序。无相关证据时明确 cold start，以有界探索获得样本，
不捏造概率。Dev records/RAG/Skill 不成为 Product runtime 依赖；adopted learning 只有通过 target
owner 转成版本化、可测试的 runtime policy/evidence projection 后才能影响决策。

### 3. Evidence-Derived Intervention And Feasibility

在第一次 submit 前及重复失败后，共用 caller 调用可复用纯策略，结合 Shot features、技术限制与
empirical evidence 提出 candidates/interventions/conflicts。至少能区分需补证、conditioning 冲突、
表达不支持和重复质量失败；在证据支持时提出 reference/strategy/Provider 调整、simplify 或 split。
Router 仍是唯一选择者；改变 accepted creative intent 或 execution scope 时交回对应 owner。

每个干预绑定来源、待检验原因、实际变量 delta、保持项、混杂因素、受影响及需保护的 requirements。
improvement/falsification prediction 必须关联可观测指标或明确 proof owner；下一结果将其标为
supported/refuted/undetermined，并改变后续候选资格，不能只保存一段 hypothesis 文字。

干预 identity 依据受控语义与变化项，不能靠改名、标点、换 task/batch identity 重置尝试。
非 resample 的空 delta repair 拒绝；resample 单独封存有限规则与累计计数，caller 不得静默提高上限。
`not_submitted` 不耗用真实采样次数；runtime failure 不当成质量反例；unknown outcome 先显式 recovery。
不同 exact recipe 下重复出现的同一失败模式必须触发 feasibility reassessment，不能无限换措辞续试。

### 4. Evidence Repair And Acceptance

media evaluation 后由既有证据 owner 产生 exact `AttemptEvidence`，下一 decision 前必须重开。
缺失 required proof 先补同一媒体；human FAIL 不由技术指标覆盖。不可标定的厘米要求、混合 proof
或 stage 错配交 acceptance owner 显式校准版本，不能删除要求、自动放宽 rubric 或篡改原 verdict。
一次干预即使改善目标项，新 bytes 仍需完整重验，禁止继承其他版本的 PASS。

## Acceptance And Verification

| Layer | Required evidence |
| --- | --- |
| Input production | 从已有项目与评价 seam 到 `DecisionInputs` 的集成测试；不以测试手写 interventions 代替生产者存在 |
| Local + Cloud wiring | 所有上述 adapter 的真实 compiler + offline transport 通过完整链；新 submit 缺失/陈旧 decision 被拒绝；旧 replay 无副作用 |
| Intervention regression | 空 delta、文字改写重置、上限扩张、未提交误计数、跨 artifact 拼 PASS 均有反例测试；supported/refuted/undetermined 确实改变下一决策 |
| Generalization | 改 Shot identity、prompt 或无关 profile 字段后，适用经验仍影响候选；不适用 Provider/rubric/特征明确排除；不能只测 exact hash 命中 |
| H3 historical replay | 冻结 015–030 原始证据；识别缺证据与反射/广播取舍；030 单列 runtime failure；报告每步行为和条件性可避免次数，不预设“第三次必换 Provider” |
| Cloud historical replay | 冻结 Vidu 02–04；跨 recipe 识别字幕重复，区分局部改善与因果证据；展示至少一个由生产策略产生的后续 disposition |
| Empirical benefit | 后续执行前冻结 Local/Cloud cohorts、原流程 baseline、rubric、总 submit budget、观看条件、样本量与统计/停止规则；比较首试可用率、失败后恢复率和每个合格 Shot 的 submit 数，报告失败/停止任务及不确定性，防止只保留成功样本 |

实施验证按 actual changed paths 的 Harness policy 执行，并接受 native independent review。
历史回放只证明决策行为；offline compiler/transport 只证明接线。真实 Local 和 Cloud 分别需要有界
运行证据，不能相互代替；其执行仍遵守当时授权与全部既有 gates。
只有预先冻结的 empirical 标准实际通过，才可声称质量收益；未通过时分别报告 engineering 完成度、
live wiring 状态与 quality `not established`。本 spec 编写不启动上述实验。
