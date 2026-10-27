# Footage Salvage Implementation Plan

**Goal:** 在既有 ProductionStrategy、QA 和 P6 上建立可追溯、可执行的 Edit-or-Regenerate 判断，保留已合格素材与未受影响镜头。

**Scope:** Take 的实际观察、缺陷/可用/保护区间；十类可组合修复意图；候选可行性、成本和风险；公共 prepare/materialize/composition/generation 接入；接点、场景与修复前后验收。

**Owners:** `ProductionStrategyResolver` 唯一选择生产手段；`QaPolicy` 保存 immutable salvage 观察；Registry 保存素材身份；`ProductionStateCommitter` 唯一写入；`ResolvedTimeline` 唯一时序；原 P6 负责成片验收。不得新增 Provider、自动 POST、renderer、资产激活或第二生命周期。

**Compatibility:** 无 salvage 字段的旧工件保持序列化/hash；普通新制作仍可用现有策略。已关闭质量失败的修复入口要求先建立 salvage 评估。新字段只增加证据要求，不改历史失败、计数或 UNKNOWN。

## Audit And Research

已有 `ProductionSourceOption`、`SourceUseEvidence`、分组件 coverage/allocation、v2 evidence-first selection、Canvas edit-first、精确 source-time-map、P5 局部失效、P6 baseline/no-regression。缺少完整 Take 故障观察、十类操作解释、证据驱动候选风险比较、连续审片要求与贯穿执行的 salvage 记录。外部参考与拒绝采用的规则记录在 `docs/research/2026-10-27-footage-salvage.md`。

## Milestones

### 1. Immutable Review Contracts

创建 `production_strategy_salvage_contracts.py`，由 QA 引用，不新增状态存储。半开帧区间、精确源 SHA/size/revision、七维观察、动作/因果缺陷、保护与可移除区间、替代素材、首尾状态；连续播放证据不足保留 UNREVIEWED。成本区分 Provider、本地 render、时间，缺依据保留 unknown。

### 2. Candidate Evaluation In Existing Planner

创建 `production_strategy_salvage.py` 作为原 Resolver 的无副作用评估助手。候选身份绑定 coverage/allocation/units/operations，拒绝陈旧/漏项评估。实际用途仍必须通过 `assess_source_use`；裁切不得保留缺陷、移除保护区间或冒充缺失动作。局部处理不能修复因果与动作结果。生成前保留可行编辑/复用方案评估；风险不可比较时返回 unresolved，而非用廉价平均掉质量。重复同类 canonical 失败升级 authoring/REPLAN；UNKNOWN 继续原 recovery gate。

### 3. Public Execution And Review

QA 字段接入 `domain_acceptance.py`；原 `production_planning.py`、Canvas prepare 和质量修复消费同一结果，并在 materialize、composition 和 generation 重新核验。缺失组件才进入原 Generation owner。新报告列出全部候选、否决原因、成本、保护项、相邻镜头影响及待验证事项。

连续接点与 Scene 要求绑定原 `FinalOutputContract`；原 P6 exact ReviewEvidence 裁决必须使用连续原速声画，缺项/陈旧不能 PASS。修复比较复用 `require_no_regression_outcome`，不从 proposal 推导 VERIFIED。

### 4. Verification And Publication

先 focused contract/negative tests，再标准 loader → prepare → materialize → composition 的集成验证；验证 source drift、遗漏动作、局部缺陷、旧 Take 复用、组合操作、悬疑停顿保护、类型参数、unknown、重复失败、原声、邻镜/Scene 未审以及局部失效。使用现有 canonical fixtures，脚本观察不冒充真实媒体或人类验收。

按 Harness 执行相应级别检查并记录 receipt；共享工作区保留 foreign staged/dirty，不夹带发布。稳定后按 Risk Gate 决定一名 native read-only review，解决 blocker 后仅提交 owned paths，push main 并核验。外部真实调用费用为零；不为确定性工程任务生成新媒体。

## Acceptance And Limits

必须能回答“为什么不剪而重新生成”和“为什么剪辑足够”；前者须有具体不成立证据，后者只代表可执行候选，最终质量须由真实输出审片证明。未支持的 V2V/局部处理返回 capability gap，不虚构 executor。独立审查和离线测试均不等于作品验收。
