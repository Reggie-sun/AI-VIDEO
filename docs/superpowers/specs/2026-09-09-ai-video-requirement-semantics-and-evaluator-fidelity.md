---
surface_id: requirement_semantics_and_evaluator_fidelity
canonical: false
spec_status: proposed
implementation_status: not_started
live_status: not_run
quality_status: not_evaluated
release_status: unreleased
runtime_status_owner: docs/v0.2-runtime-baseline.md
roadmap_owner: docs/v0.2-agentic-production-roadmap.md
contract_version: requirement-semantics-and-evaluator-fidelity/1
---

# Requirement Semantics And Evaluator Fidelity

Date: 2026-09-09

## Status And Authority

本文件定义待实现的通用 contract，依据当前源码与已完成的 S01 只读审计编写。
当前授权仅覆盖 Spec 编写与文档验证；不授权 implementation plan、代码实现、Provider、
生成或派生媒体、真实 Production state mutation、历史修订、commit 或 push。
本文的 MUST / MUST NOT 是后续实现的验收约束，不表示当前 runtime 已具备这些行为。

审计基线为 HEAD `c55bfc3400d4aac95dda43da564fac9f4d1de555` 加当时已有 working-tree
changes。既有 S01 recovery/admission 工作保持独立；本文不修改或取代其 spec、源码或状态。
实现状态仍由 runtime baseline 维护；Spec 通过文档检查或独立 review 不构成工程实现通过。

## Goal

让必要叙事结果、质量底线、导演偏好、诊断观察和生产契约产生不同且可验证的运行后果。
媒体验收应忠于获准的结果与最终观众体验，不能因 prompt 写得更具体就不断缩小成功定义。

本 contract 修复两类问题：

- **Authoring escalation**：Director target、recipe detail 或 repair margin 未经 acceptance
  owner 明确判断，就进入 raw-generation hard inventory。
- **Evaluation drift**：criterion 已经明确，但 evaluator 使用更严格的 prompt 数字、旧 Gate
  observation 或错配的问题评价媒体。

前者需要 prospective authoring/QA revision；后者首先是按原 criterion 修复评价的问题。
两者 MUST 分开处理，不得用一次 evaluator 错误为删除其他 frozen requirements 背书。
本 Spec 不承诺提升模型生成能力、视频质量或最终通过率；这些属于独立 empirical validation。

## Current Evidence And Gaps

| Surface | Verified Current Behavior | Gap Addressed Here |
| --- | --- | --- |
| Director Coverage v3 | 有 creative-input 来源锚、constraint ID 和 Director rationale | 没有完整区分必须结果、偏好、时间目标和允许变化 |
| `RequirementExpression` | 已有 `level`、`stage`、`tolerance`、`measurement`、`proof`、`production_owner` | 缺少要求为何成为 hard 的结构化来源；容差和测量主要是自由文本 |
| QA / Recipe projection | `_expressions()` 复制 selected inventory；recipe 校验完整 inventory/hash | 正确复制并不证明上游分类合理 |
| Generation evaluation /1 | 绑定 request、artifact、rubric、QA、evaluator 和 proof kind | 缺少逐项 criterion、实际提问和原始回答之间的绑定 |
| Diagnosis | applicable acceptance FAIL 为 QUALITY_FAILURE；缺证据为 EVIDENCE_GAP；hint Finding 非法 | 必须在 source admission 前分离非验收意见，不能只在最后诊断错误 |
| Final-output / No-regression | 已有完整成片要求、exact baseline、已知退化拒绝与 repair outcome 检查 | 不得把局部 timing PASS 当作成片成功；本次不替代该 owner |

S01 当前 QA 2.3 有 17 项 acceptance，16 项 raw_generation，字幕一项 final_composition。
attempt12/13 唯一明确 FAIL 都是 1.5s 到位；该数字在 attempt09 request 中明确为
`for margin`，之后成为手写 Gate 的 Required finding。历史投影脚本忠实保留了已经
硬化的 Gate，不能把它描述为首次硬化或旧提交前的 typed recipe。

attempt13 使用 ≤2.2s 广播末字标准，而当前 QA measurement 指向原 0.1–2.7s 窗口；
其 legacy-14 声音项写了间隙 observation，legacy-17 手部项写了声音 observation。
当前 proof 都为 human/NOT_EVALUATED，不代表已经错误放行，但证明 type/hash 正确不足以
保护证明对象。S01 的精确物理 2cm 和胸牌姓名可读性问题已经在 QA 2.3 纠正，不能当作
仍存在的 current blocker。

## Semantic Classes And Runtime Consequences

五类是现有 requirement 的语义说明，不是第二套 requirement IDs、inventory 或 lifecycle。
`level` 继续决定是否进入 acceptance；category 说明其依据和用途。

| Category | Meaning | Existing Level | Runtime Consequence |
| --- | --- | --- | --- |
| `narrative_critical` | 故事成立必须出现或不能出现的结果 | `acceptance` | 适用阶段 FAIL 阻断验收；缺失/不确定 proof 为 NOT_EVALUATED，不获得通过 |
| `quality_critical` | 明显视觉错误、自然度、identity、continuity、商品正确性等底线 | `acceptance` | 与 narrative hard 要求同样严格；不能由总分或偏好补偿 |
| `directional_preference` | 非固定的动作路径、姿态、节奏、表现强度和 timing target | `recipe_hint` | 用于 authoring、recipe 或比较；单独偏离不触发 QUALITY_FAILURE |
| `diagnostic_observation` | 起手时刻、模糊区间、疑似翻腕、测量覆盖/ASR 精度等观察 | `diagnostic` | 用于解释和 intervention 设计，不定义成功、也不证明失败 |
| `governance` | 输入身份、格式和适用生产契约 | 已在 QA 内的项继续 `acceptance`；其他沿用原 gate | 保持原 typed failure / gate；不参加艺术排名 |

GOV-01：不得将 quota、permit、recovery、activation 等原 owner 已管理的条件复制成
第二份 QA truth。只为既有 QA 技术项补充 governance 分类，例如 exact 输入与输出格式。

SEM-01：新 contract 中 category 与 level 的上述映射 MUST 一致。A/B 不因被称为
“导演判断”就可降为 preference；C/diagnostic 不因 prompt 使用 MUST、精确数字或否定句
就升级。所有新 inventory entries 必须分类，不能只标注希望降级的项。

SEM-02：用户明确固定的创作形式仍是约束。若其不属于叙事/质量底线，可作为
governance 的 explicit scope contract 保持 hard，并引用原始固定要求。
用户批准输入资产、允许继续或批准一次执行，不自动等于批准所有新增 recipe margin。

SEM-03：同一观察可以是诊断证据，并支持对一个独立 hard requirement 的判断：
例如起手较晚是 diagnostic；只有它确实使获准的切点/叙事条件失败，才按该 hard ID
产生 FAIL。不得直接把 diagnostic 的数值阈值作为另一个未声明 blocker。

SEM-04：各项采用 PASS / FAIL / NOT_EVALUATED 的既有证据语义；NOT_EVALUATED 不等于
媒体已坏，也不等于可接受。C 的排序意见不采用 required Finding 的 FAIL 语义。

## Director To QA Boundary

### Authoring Output

沿用 `open-video` 及现有 Character / Scene / Shot authoring。新 Director handoff 必须
明确包含下列五组，允许空数组，但不得省略组名后由下游猜测：

| Group | Required Meaning |
| --- | --- |
| `must_happen` | 可观察的必要结果，以及为什么它对获准目标必要 |
| `must_not_happen` | 会破坏叙事、质量、连续性或明确用户约束的禁止结果 |
| `preferred_performance` | 偏好的表演/摄影方式，明确合理替代仍可成立 |
| `timing_targets` | 时间目标，并区分 delivery constraint 与生成提前量 |
| `acceptable_variation` | 哪些维度可变化、哪些结果必须保留；关联目标而非笼统“宽松” |

每项应有 stable `intent_item_id`、statement、source reference、origin
（explicit_user / director_choice / repair_margin）以及必要的 related intent IDs。
原始用户 constraint 继续引用 verbatim source，不得把 Director 自写文本归为用户原话。
preferred performance 与 timing target 可以引用同一 intent item；禁止复制出互相矛盾的真值。

这是既有 Director handoff 的 versioned extension：旧 coverage v3 仍可读取；新输出需用
独立可辨的后续版本，并由当前 Skill validator 检查上述 shape/source/binding。
不得启动第二 Director、建立新的 Production authoring store，或顺带重设计 coverage 风格规则。
缺少这些语义时，新 handoff 返回给 authoring 补齐，不从 prompt 反向抽取 hard inventory。

### Acceptance Admission

DIR-QA-01：Director 只提出 intent 与建议分类。**QA acceptance owner 唯一决定进入
acceptance inventory 的 predicate、stage、tolerance、measurement 和 proof。**
两种职责可以由同一个 Codex 会话履行，但必须有可审计的 owner 决策，不能依靠隐式角色切换。

DIR-QA-02：每个新 hard atom 必须给出以下至少一种具体依据：

- 明确的用户固定要求；
- 获准叙事结果；
- 已接受的质量底线或 continuity/切点契约；
- 已存在且适用的 production contract。

还必须说明违反该 atom 会破坏哪个结果、在哪个呈现阶段发生、如何观察、允许什么偏差、
由谁提供证明。`production_owner` 字符串、prompt 存在或数字精确，本身不构成依据。

DIR-QA-03：仅引用 repair hypothesis、历史 observation、Provider recipe 或“为了留余量”
不足以进入 hard acceptance。必须先证明它是某个获准结果的必要条件，并按正常
authoring/QA revision 流程明确接受；不能在 retry 中自动提升。

DIR-QA-04：若用户明确的固定要求与 proposed variation 冲突，保留固定要求并返回
authoring 决策；不得自动弱化。若无法证明某一表演细节是必要条件，先作为 C；
这不授权删除已经 frozen 的旧 hard requirement。

DIR-QA-05：原始目标、QA predicate 与生成 recipe 可以采用不同精度。QA 可要求广播
在交付窗口完成，recipe 可要求更早完成以留余量；两者必须分别表达且单向引用。
禁止 `prompt wording → evaluator criterion` 和 `repair margin → canonical acceptance`
的隐式升级。

## RequirementExpression And QA Contract

### Existing Inventory Remains Canonical

REQ-01：复用 selected `DomainAcceptancePolicy.profile_payload.generation_requirements`。
Recipe 中的 expressions 仍是完整、可校验的 QA projection；不得建立新的独立可编辑
requirement catalog、允许 caller override level，或按 evaluator 能力临时删除 required IDs。

REQ-02：`required_requirement_ids` 必须恰好对应 inventory 中 level=acceptance 的 IDs。
现有非空/唯一性约束保持；C/diagnostic 不计入所需 PASS 数，也不能充当 PASS 分母。
阶段仍为 `raw_generation / shot_editorial / final_composition`，不新增 exploration stage。

REQ-03：一个 atom 只定义一个成功 predicate、适用阶段和 required proof。
复合句若混入不同 category、可独立失败的结果、不同证明对象或阶段，必须拆分。
拆分使用新 prospective IDs，并记录原 intent/旧 ID 的来源关系；不改旧 ID 的历史含义。

例如“很早到位并保持自然姿势”可拆为叙事可读性、切点状态、自然动作和提前到位 target。
前几项是否 raw/editorial/final，必须依据实际输出和验收窗口决定；不能把“删除 timing”
解释为连切点与自然度也删除。

REQ-04：`observable` 定义必要结果；`tolerance` 定义可接受变化；`measurement` 定义
方法、范围、精度和覆盖限制；`proof` 指定证明责任。dimension/title 只是标签。
这些字段若互相矛盾，新 QA publication/admission 必须退回 acceptance owner，不选择其中
最严格的一句。观测结果不得被复制为未来 measurement 方法。

REQ-05：`intent_paths / native_text` 只证明生成表达的来源和 compiler coverage，
不成为 evaluator predicate。整个 action 字段包含多个约束，不授权 evaluator 对每句话
新增 hard finding。

### Minimal Schema Extension

现有字段足以表达多数运行后果，但不能独立证明来源分类、数值谓词一致性和问题绑定。
最小必要新增项如下，均属于已有 owner：

| Surface | Proposed Addition | Purpose |
| --- | --- | --- |
| Existing QA profile_payload | `requirement_semantics_version: requirement-semantics/1` | 显式选择新规范；未知版本拒绝 |
| RequirementExpression | optional `semantics` | version、category、intent role、source refs、hard basis 与拆分来源 |
| RequirementExpression | optional `measurement_spec` | 有限类型的时间窗口 predicate；不从 measurement prose 自动解析 |
| GenerationEvaluationSource | `generation-evaluation/2` | 逐项问题/criterion 绑定、acceptance/advisory 分离及未映射质量证据 |
| GenerationObservation /2 | evaluation item hash、presentation/answer reference、typed measurement result | 防止同 ID 错问题、错阈值和错对象 |
| Existing review input / source validation | QA-derived immutable evaluation-item projection 与 injected presentation-evidence verifier | 不可编辑的派生 view；核对真实提问/回答的来源和顺序 |
| AttemptEvidence | optional `unresolved_quality_refs` | 未映射质量证据的 exact source projection；使纯 diagnosis 与重开不丢失阻断 |

`semantics` 的规范内容是：

- `version`：上述已知版本；
- `category`：五类之一；
- `intent_role`：must_happen / must_not_happen / preferred_performance /
  timing_target / acceptable_variation / diagnostic / production_contract；
- `source_refs`：至少一个 exact source hash、稳定 locator/intent ID、必要的原文或引用片段；
- `hard_basis`：hard atom 必填的来源种类、对应获准目标/契约引用与必要性说明；
  C/diagnostic 不得伪填 hard basis 来获得 required 权限；
- `derived_from`：可选的 prior intent/requirement references，仅作 lineage，不继承 verdict。

source refs 的形状和 hash 可以机械验证；任意自然语言引用是否真的推出“必要条件”
仍由 acceptance owner 负责，不能声称 validator 已解决自然语言 entailment。

没有证据要求升级整个 `generation-recipe/1` 或迁移 Manifest。新增 optional 字段在旧数据
缺失时必须完全省略，包括 nested serialization；不得补 null、默认 category 或新 hash。
新 marker 下所有 entries 必须满足新规范，不能部分填充。详见 Historical Compatibility。

### Compiler And Non-Acceptance Data

REQ-06：对 raw acceptance，继续执行现有 native/control expression coverage，不能借新分类
使真实要求在请求中丢失。编译支持检查与媒体是否满足要求是不同判断。

对 recipe_hint：有 `intent_paths` 的显式 recipe 文本继续验证表达一致性；仅用于
authoring/ranking 的 C 可以没有 raw intent path，不因缺少 prompt witness 失败。
它的来源通过 semantics source_refs 保留；不得将已存在的硬约束偷偷搬到无 path 的 hint。

对 diagnostic：不强制放入 Provider prompt。新 marked contract 下
`expression_errors()` 的逐项 prompt coverage 必须区分 level，避免要求 Provider
“生成某个观察结果”。全量 inventory/hash 校验及既有 authored GenerationIntent 的遗漏保护保持。
这是一处必要的 compiler validation 调整；仅改 QA JSON 不足以实现本 contract。

REQ-07：诊断 observation 与 preference assessment 可以保留在 /2 source 的
`advisory_observations` 中，引用当前 C/diagnostic ID、原始证据与说明，不含 required verdict。
该字段默认空且旧 /1 序列化省略。它不是 ranking engine，不规定分数、算法或 candidate count。
intervention 可以引用这些证据解释假设，但仍须关闭真实 blocker，不能凭 advisory 新建 blocker。

## Evaluator Input And Evidence Contract

### QA-Derived Evaluation Items

EVAL-01：本次新增的 machine-enforced question binding 适用 **marked QA 的 raw-generation
evaluation**。沿用 `GenerationReviewInput` 与当前 review/record/validate entrypoints，
不得只修一个 S01 run script 而让其他新入口继续接受自由拼装的 criterion。

从 selected QA 及 actual request/artifact 派生 evaluation item，至少绑定：

- QA content hash、rubric hash、request hash、exact artifact SHA/size；
- requirement ID、semantic category、level、stage、required proof；
- canonical observable、tolerance、measurement、measurement_spec；
- deterministic question text，以及由完整 item 计算的 `evaluation_item_hash`。

criterion hash 排除 Provider native_text、compiled prompt、repair hypothesis 和历史 Gate note。
question 只由当前 criterion 与固定版本的呈现模板生成；不允许 caller 修改阈值后保留原 item hash。
派生 item 不成为第二 inventory，不拥有 activation、quota 或任何 mutable lifecycle。

EVAL-02：实际提问必须在回答前确定。source /2 保留实际呈现的 question text/hash、
对应 item hash、原始回答或 exact answer-source reference、actor 和媒体 identity。
录入时重算问题并核对呈现内容；禁止事后把正确 hash 贴到另一个问题的答案上。

现有 review owner 必须接收可注入的 presentation-evidence verifier；这是当前入口的
必要能力扩展，现有 adjudicate 返回后签发的 `_AnalysisRecordingProof` 不能代替它。
凭据至少包括来源 namespace、session/interaction reference、presentation event reference、
实际问题集合及其 item hashes、artifact identity、answer event reference、回答 actor 与原文。
verifier 必须从可信呈现/消息记录核对内容、回答关联和来源保证的事件顺序；
caller 自报 question text、时间戳或“已先问过”不能单独作为凭据。

human proof 可使用可复核的实际呈现/回答事件；analyzer proof 可使用受控调用的
request/response correlation。来源必须符合 selected evaluator authority，且在记录与重开时
可验证；需保存的 exact evidence 仍经原 immutable evidence/committer 入口。
不得为此引入新的 review session lifecycle、前端、外部消息发送授权或 Provider。
若当前集成不能提供真实可验证的来源，新 proof 保持 NOT_EVALUATED/EVIDENCE_GAP；
不得由测试 fixture、自签调用者时间戳或事后 transcript 代替。

同一 proof owner 可回答不同事项，但不能用“proof=human”替代逐项绑定。批量回答
“都正常”仅在完整问题集合已呈现、回答明确覆盖该集合、且每个 item ID 均被保存时可解释；
不能依赖数组位置、近似名称或旧 run 的问题顺序。

EVAL-03：结构绑定不能证明人实际观看、回答真实或自由文本具有正确含义。
Evaluator 必须核对原始回答是否针对该对象；不相关、含糊或未回答的内容为证据缺口。
测试须证明可机械识别的错绑被拒绝，不得用关键词检测冒充通用语义正确性证明。

### Source Admission And Findings

EVAL-04：`GenerationEvaluationSource /2` 的 acceptance observations 只允许引用当前
raw-generation、level=acceptance 的 item，并匹配其 required proof 和 selected authority。
以下情况在进入 `Finding` 与经验统计前拒绝：

- 未知 ID、错 QA/rubric/request/artifact/stage/proof；
- criterion/question/item hash 不一致，或实际问题不是该 item 的呈现；
- C/diagnostic 写入 acceptance observations，或 hard item 偷放 advisory；
- 同一 source 重复同一 item、缺必要语义 metadata、未知契约版本；
- 用旧 /1 source 回答已选择新 marker 的 QA。

拒绝沿既有 acceptance/evaluator error 路由（`RUBRIC_OR_STAGE_ERROR` 或相应 typed admission
failure），不能把 contract mismatch 记录成媒体 QUALITY_FAILURE，也不能默默过滤后宣称 PASS。
合法但不完整的 proof 则产生 NOT_EVALUATED / EVIDENCE_GAP；两者不得混淆。

EVAL-05：source /2 的 advisory_observations 不投影为 Finding，不参与
`failed_requirements / preserved_requirements / all_required_observed_pass` 或经验成功率。
可以仅含 advisory，但不能由此满足任何所需 proof。现有 diagnosis 的非法 Finding 检查保留。

当前 legacy diagnosis 的“任意 human FAIL 仍保留”行为必须按旧版本重放；不能全局删除
该规则。新版本通过 admission 区分正式质量拒绝与 C 意见，并在纯 diagnosis 边界防御
手工构造的非法 evidence，不允许绕开 entrypoint 注入 hint FAIL。

EVAL-06：真实质量拒绝若暂时不对应已声明 item，source /2 必须将其保存于
`unresolved_quality_observations`，而非伪造 requirement ID 或塞入 advisory。
每项至少包含稳定 observation ID、原话/原始回答引用、具体可见问题、所涉及质量底线的理由、
actor/proof、exact request/artifact/QA identity 与证据引用。此项报告 rubric/评价覆盖冲突，
不自行定义新成功 predicate，不含 required verdict，也不直接产生 QUALITY_FAILURE。

录入和 strict reopen 必须验证所选 authority、原始来源，以及以下唯一派生关系：
source 中这些 entries 的完整 content hashes → `AttemptEvidence.unresolved_quality_refs`。
projection 必须完整且精确匹配；不能只保存在 transient callback/内存中。
新字段旧数据缺失时省略，不改旧 evidence hash；新记录的 evidence hash 包含这些引用。
纯 diagnosis 对非空引用返回 `RUBRIC_OR_STAGE_ERROR` / `acceptance_owner`，
`all_required_observed_pass=false`，不虚构 failed requirement ID 或经验质量失败样本。
exact-result 合并保留全部未处理引用；Feedback 从原 history 重开后继续阻断通过和自动 repair，
即使所有已声明 hard Findings 都 PASS。该投影/路由是本次必要实现，不得声称当前仅处理
conditioning reference 的 `derive_generation_interventions()` 已经提供通用通路。

QA owner 应判断其是否暴露真正质量缺口并按已有 authoring/QA revision 处理，不能静默
重写 frozen inventory。本 slice 不新增 conflict 清除 ledger、撤销 FAIL 或 reopen 机制；
后写 PASS、漏传引用或改 candidate 名称不能消除此 exact scope 中的阻断。
现有生命周期不能合法处理的情况继续报告限制，不凭 Spec 自动放行。
仅因已绑定 C 的偏好不合意，不得录成此类质量拒绝；准入需检查具体质量问题和来源，
自然语言是否体现真实质量底线仍由 QA owner 负责，不能声称 hash 验证已解决该判断。

EVAL-07：MCP 提供原始媒体证据；adjudicate 应以当前 evaluation items 为输入。
禁止“先手写 Gate verdict/note，再只用当前 hash 包装为合格评价”的新运行路径。
旧 run scripts/records 作为历史保留，不可作为 marked QA 新记录的兼容旁路。
所有持久化继续经过 `ProductionStateCommitter`，不新增 evaluator writer。

### Final Review Boundary

`QaPolicy.final_output / FinalOutputContract` 仍是成片要求的唯一 owner。
本次不把 raw /2 observations 当作 Final Acceptance，不改造完整 final-question schema。
Final Media QA 仍必须按 canonical final contract 提问并人工核对证明对象；本文不声称
新 raw question binding 已自动覆盖任意 final-review 自由文本。

marked inventory 中的 final_composition acceptance 项必须明确引用获准 final contract，
ID/observable/proof 对应不得矛盾。只有该 final owner 可以变更其判断条件；raw projection
不得再推导一个更严格版本。human 继续对应 human，analyzer 对应 final evaluator；
技术格式留在原技术层，不能为了统一表格改成人类主观要求。
纯 final 项不产生 raw Finding；完整的成片叙事、自然度与 continuity 仍须在实际最终输出
取得 fresh proof，而非汇总原片局部 PASS。

## Bounded Temporal Measurement Contract

TIME-01：`measurement_spec` 首个必要支持类型为 `event_time_window`。它由 QA owner
封存，不通过 prompt 或 observation prose 自动抽取，包括：

- `event_id` 与事件定义、`boundary=start|end|completion`；
- `timebase=source_media_millis` 与待测 source role/selection rule；本次限 fetched raw source 时间；
- 允许窗口的整数毫秒上下界、各边界 inclusive/exclusive；
- 允许的 measurement method/scope、required coverage 与 uncertainty 表达。

生成前 QA 只封存选择哪类输出及事件的规则，不包含尚未生成的 MP4 SHA/size。
实际 artifact identity 在 fetch 后的 evaluation item 和 measurement result 中绑定、复测；
不得形成 `QA → recipe/request → output bytes → QA` 的 identity 循环。

时间窗口是同一 criterion 的结构化表示，tolerance/measurement prose 用来说明它，
不得形成两套可独立修改的阈值。二者不一致是 QA contract error。
它不创建第二 timeline；后续涉及最终剪辑时间必须消费 `ResolvedTimeline` 的映射，
不能把源视频 4 秒坐标直接当作成片使用的 3 秒坐标。

TIME-02：measurement result 与 criterion 分开保存，至少声明 actual artifact SHA/size、
对应 evaluation item hash、event/boundary/timebase、
观察时刻区间 `[earliest_millis, latest_millis]` 或 unknown、method、覆盖范围与 evidence refs。
旧 `span_millis` 仍表示观察/失败所在区间，不能直接充当测量精度或验收阈值。
reported timestamp 的精度、帧采样误差、ASR 边界含义必须进入 uncertainty/coverage。

TIME-03：在 identity、事件含义、method 和覆盖都充分时：

- 实测可能区间全部位于 canonical 允许窗口：该时间 atom 可 PASS；
- 实测可能区间与允许窗口不相交：该时间 atom FAIL；
- 跨越边界、事件对象不确定或证据不足：NOT_EVALUATED。

开闭边界按封存定义计算。无依据不得收窄 uncertainty，不得只挑最有利的一次测量。
广播内容正确、音质和时间边界是可独立证明的 atoms，时间 PASS 不替代其他证明。
数值 verdict 必须由该 predicate 与 measurement 推导或重算核对，不能自由填 FAIL 后
在 observation 写一个不同阈值。

TIME-04：ASR segment end 不是自动合格的“最后一个字结束时间”。
请求 word timestamps 而工具未返回时，不能伪造；可作为 diagnostic 或支持有范围的观察。
只有 QA 接受的方法确实支持该事件与精度，才能据其给出时间 PASS/FAIL。
本次不新增 forced alignment、ASR Provider、通用单位系统、姿态角度 DSL 或自动审美模型。

## Historical Compatibility And Adoption

HIST-01：旧 QA policy、verdict、Finding、experience、Manifest、rejection/abandonment
和原始媒体 MUST 保持原样。读取旧数据不得新增默认字段、重算成新 profile、
修订 actor、补造问答、goal 或 submission-time metadata。
JSON→load→dump、recipe/scope/source/rubric hash、strict reopen 和原 diagnosis 必须可复现。

| Input / Operation | Required Behavior |
| --- | --- |
| 旧未标记 QA + 原 /1 evidence 的 exact reopen/replay | 按旧契约读取，旧结论不变 |
| 新 marked QA + 完整 /2 evidence | 执行本 Spec 的严格 admission 与分类语义 |
| 新 marked QA + /1、缺字段或未知版本 | Fail closed，不回退 |
| 为已选 marked QA 删除 marker / 改 recipe level | identity/contract 不一致，拒绝；不能作为同目标修复 |
| 未采用新 contract 的旧任务 | 原路径保持历史兼容；不得声称已经获得本 Spec 的语义保证 |
| 新 QA 语义版本对历史媒体作 shadow replay | 独立 development assessment；不生成 Production PASS、experience 或 activation |
| 同目标修复期间改 acceptance predicate/level/required coverage | 保持既有 frozen-goal 拒绝，不用“语义修复”绕过 |
| 旧 goal 和新 goal 均存在且为显式不同版本 | 按既有 owner/authorization 接纳新目标；旧失败保留，原额度和历史不重置 |
| 旧 final_output_goal=None → 新 goal | 现有 generation policy/3 不承认此为已支持 revision；本 Spec 不增加自动迁移 |

HIST-02：新增 optional schema 的 legacy absence 必须在最内层 serializer 就省略。
旧 artifact 不能因为 loader 顺便补 metadata 而改变外层 hashes。
新 marker 的校验必须在 selected QA admission、Recipe projection、evaluation recording
等现有入口生效，不能只在 Skill 层检查。适用版本由 selected QA 决定，不能由 caller 自选。

HIST-03：同 rubric 的 evaluator 错判可以由原 owner 在允许的生命周期内补充/纠正证据，
但必须保留旧 source。当前 exact-result merge 不撤销已有 FAIL；已经关闭的 rejection
也不能重新 repair_evidence。本文不新增撤销 FAIL 或重新打开 abandoned attempt 的机制。
无法在现有入口合法完成的纠正保持 shadow-only，并明确报告限制。

HIST-04：prospective 分类必须先形成新的 owner-approved QA/goal contract。
Spec 本身不激活该 policy；不因文件存在就改变 current production selection。
新 project/task/component 名称不得用于绕过同族历史、quota、repeated-failure 或 unknown-outcome。
新旧 QA cohort 不自动合并为更高成功率；shadow 结果不进入经验 success/pass 统计。

### Shadow Replay Output

Replay 默认只读，不生成或派生媒体、不调用 Provider/analyzer，不写真实 Production。
使用原始 bytes、可验证的原始证据、历史 QA/recipe 和显式 proposed QA 独立解释：

- old artifact/request/rubric/evidence identity 与 untouched historical verdict；
- proposed contract/version、旧 atom 到新 atoms 的来源映射；
- 每个新 atom 的证据适用性、缺口、proposed assessment 与理由；
- preference/diagnostic 与 hard findings 分开；
- 所需而未发生的 human/final review，明确为 NOT_EVALUATED。

输出属于 development shadow assessment，不是 `GenerationExperience`、QA receipt、
Manifest state、source-use qualification 或历史 reactivation。
不得用新 rubric hash 包装旧 source，让它看起来像当时已按新问题进行了评价。
旧原始回答只有在对象、时间范围和证明内容足够时，才可作为新分析的引用；必须标记其历史来源，
不把它伪装为新 /2 presentation/answer。观测范围不足时保留未知。

## Exploration And Convergence Relationship

两者是 workflow 的决策语义，不是新增的 durable state、第三种 QA verdict 或新的 manager。
`stage` 仍表示媒体生产阶段；不是 exploration/convergence 开关。

| Concern | Exploration | Convergence |
| --- | --- | --- |
| Purpose | 找到值得继续评估的素材 | 证明 selected candidate 达到可交付要求 |
| Preferences | 用于比较、排序与改 recipe | 可以取舍，但不能弥补 hard failure |
| Known applicable hard FAIL | 可淘汰该候选；保留证据 | 阻断验收/交付，repair 必须关闭真实 blocker |
| Incomplete human/final proof | 可保留为未接受候选，不要求每条完成全部最终主观证明 | 全部适用 hard proof 必须完整且 fresh |
| Governance | quota、permit、identity、recovery 等始终严格 | 同样严格 |
| Final-output | 已知整体退化不能因“探索”豁免 | 完整 final output、continuity、no-regression 与 human/evaluator proof |

EXPL-01：保留候选供比较不等于 activation 或下一 Shot permission。现有 per-Shot Gate
要求仍有效；缺 required raw proof 的候选不能进入下一 Shot、source-use 或 Final Acceptance。
本 Spec 不增加绕过 pending attempt 的新 submit 路径，也不实现 best-of-N 调度。

EXPL-02：偏好排序不产生 QA acceptance；整体观看结论若用于 hard requirement，必须经其
正式 proof owner 和 exact evidence contract。一个总分不能覆盖 identity、continuity、
商品正确性或叙事 hard FAIL。

CONV-01：repair 继续保护全部适用 hard requirements、原有已接受状态和 existing
no-regression baseline layers。缺证据优先补同 bytes，未知执行结果走 explicit recovery。
只有 C 发生偏差不得触发 QUALITY_FAILURE；已知动作/画面退化不能被标成 C。

CONV-02：不通过逐条候选保留来弱化 no-regression。新契约中的 C 不应新建 blocking review
baseline；旧 baseline 中已保存的 optional PASS layers 仍按现有 contract 保护，不能倒删。

## Ownership

| Owner | Unique Decision | Must Not Own |
| --- | --- | --- |
| Director Skill / approved authoring | 创作结果、偏好、variation 与候选的艺术选择建议 | QA required set、评价证明、activation |
| QA acceptance owner | hard/advisory 分类、predicate、stage、tolerance、measurement、proof、version | 编造媒体观察或替代用户固定要求 |
| Evaluator / Media QA | 按已选 criterion 对 exact evidence 给出可归责判断 | 改阈值、升级 hint、修改 frozen QA |
| Human holistic review | 自然度、节奏、信息可读性和比较意见；为指定 hard 项提供真实观看证据 | 以笼统赞同替代未回答的逐项证明或跨 bytes 继承 |
| ProductionStrategyResolver | 从 authored alternatives 和用途证据选择生产手段 | 重新定义成功、评价表演、Provider/media best-of-N |
| GenerationFeedbackOrchestrator | 当前 context/history、evidence/repair 路由、有界后续动作的组织 | 为关闭 blocker 修改标准、第二选择器/预算 ledger |
| Development Harness | 工程契约、错误路径、历史兼容、scope 与回归验证 | 媒体审美、human acceptance 或生产调度 |
| Final-output / No-regression owner | 完整最终输出与修复前后证明的通过条件 | 改写历史失败、局部指标代替整体、媒体执行 |
| ProductionStateCommitter | canonical durable writes、activation 与 explicit recovery | 创作分类或主观评价 |

Creative source 是否被正确解释由 authoring 与 QA admission 明确交接；criterion 发布后，
evaluator 只能报告 mismatch/证据缺口，不能拥有第二个“更合理阈值”的最终裁决权。
Director 如要改变硬结果，返回既有 authoring/QA revision；ProductionStrategyResolver
如遇不可执行策略，返回原 authoring owner，不能私自放宽。

## S01 Worked Example

本节用非 canonical 历史案例解释上述规范。示例 ID、时间和 SHA 不是通用代码常量，
不修改真实 S01 QA 或任何 verdict；实现不得根据 S01、legacy-N 或 Provider 名称分支。

### Timing Margin And Compound Requirement

“1.5 秒前到位并保持”应被分析为不同 atoms：

| Proposed Atom | Class / Stage | Expected Consequence |
| --- | --- | --- |
| 前三秒观众理解“他人有倒影而主角没有” | narrative_critical / final_composition | 按完整画面、声音、字幕的实际可读性验收 |
| 实际切出状态能接 S02 的悬停状态 | quality_critical / 适用 raw 与 final 接点分别证明 | 切点未成立仍阻断，4s 尾帧不能替代3s切点 |
| 手部与持续场景运动自然 | quality_critical / 对应 exact 输出 | 异常翻掌、畸形、整帧冻结仍拒绝 |
| ≤1.5s 完成以留表演余量 | directional_preference / recipe_hint | 比较与调 recipe；单独未达不产生 QUALITY_FAILURE |

原始异常从首帧已存在；抬手提前量不是剧情异常发生的唯一时刻。
这不证明任意迟缓动作都合格；如果观众不能读懂、切点状态不成立或动作不自然，
必须按对应 hard atom 判定，不能换一个名称删除真实目标。

### Palm Orientation

“全程掌向玻璃”包含 recipe 对路径的选择。应保留无异常腕部、无畸形、关键姿态合理、
切点连续的质量底线；沿途掌向、手腕转动和速度曲线允许合理变化。
手指轴线变化不是掌面反转的充分证据；细节模糊应记录为 diagnostic/证据限制。
不能把末帧正确当作整个动作自然，也不能要求每一帧均能辨认掌纹才认可自然度。

### Broadcast Window

正式 Shot authoring 为 0.1–2.7s；QA 2.3 measurement 明确结束须落在原窗口。
prompt 的 ≤2.2s 为余量目标，不能成为更严格的 criterion。
“before3s”标题也不能覆盖 measurement 中的2.7s，需由新 owner 规范化为唯一 predicate。

attempt13 的两次 ASR segment end 为 2.44/2.32s，未返回所请求的 word timestamps。
新解释应取消“无法证明≤2.2”这个拒绝依据；是否足以证明正式结束窗口，
仍须按事件定义、ASR 精度与 human 声音层判断，不能直接补成 PASS。
本例不新增“ASR segment 从0开始因此违反0.1”的原先未声明 blocker。

### Exact Historical Replay Expectations

| Artifact | Historical Evidence | Expected Shadow Interpretation |
| --- | --- | --- |
| attempt12 `c56b05e2da5d38bfeddd2d6f58322d84a7d8433c01589112b87d1865b388b7f3`; 3,472,114 bytes | raw 14 PASS / 1 FAIL / 1 NOT_EVALUATED；唯一FAIL为legacy-03；手/间隙/声音有人类确认 | 保留供 holistic review；不因1.5s proxy单独进入自动repair；最终hook/切点/字幕不冒称已通过 |
| attempt13 `d6a636d5fe19c1a9cbdd23d5bbb160ce3b2e91b8379d40346ff12e69aebff922`; 3,305,001 bytes | raw 10 PASS / 1 FAIL / 5 NOT_EVALUATED；起手提前但约2.75–3s才近终点；本片human仍缺 | 不宣称更好或更差；纠正criterion和错问题，保留缺少的本片proof；不继承12回答 |
| freeze derivative `090b4c605a400b712fa41d27028352bd6b38d6ba0436dda280b78a730b9840e3` | 已有明确人类拒绝；加速后整帧clone tail | 自然动态/no-regression仍拒绝；timing改善不能抵消已知退化 |

attempt12 当前已 abandoned/FAILED，13 为 RUNNING/VALIDATE；二者历史 candidate
final_output_goal 均为空。上述 shadow interpretation 不恢复12、不激活13、不推进S02。
本例只能定位可能无效的 repair 分支，不能计为已节省的调用、已提高的成功率或独立新实验。

## Acceptance Criteria

以下是后续 implementation 的可执行验收场景，不是本次已运行结果或 implementation plan。
实现必须通过公开/标准入口与原 owner 验证，不能只写模拟本实现的正向 helper tests。

| ID | Scenario | Required Result |
| --- | --- | --- |
| AC-01 | Director将“更早完成以留余量”作为timing target | QA不得因prompt措辞或数字精确自动提升；新handoff来源/角色完整 |
| AC-02 | 显式用户固定要求被误标为普通偏好 | 返回authoring/QA冲突；不得静默放宽 |
| AC-03 | 复合要求同时含叙事、continuity、自然度和提前量 | 拆成独立atoms；A/B仍required，C不进入required IDs |
| AC-04 | 合法C负面评价或diagnostic较晚起手 | 不产生QUALITY_FAILURE、required FAIL或经验失败样本 |
| AC-05 | 明确叙事错误、身份/商品错误、手部畸形或continuity破坏 | applicable hard FAIL仍阻断；高偏好分不能抵消 |
| AC-06 | required proof缺失或精度不足 | NOT_EVALUATED/EVIDENCE_GAP；既不认定媒体成功，也不伪造质量失败 |
| AC-07 | 同ID同human proof，但实际呈现的问题属于另一个item | admission拒绝；不靠正确QA hash放行 |
| AC-08 | answer绑定到不同artifact、question或actor | 拒绝，不从旧回答补出新PASS |
| AC-09 | prompt target2.2s、canonical窗口上界2.7s，合格事件测量区间完全在窗口内 | 时间atom按2.7s计算；不得因2.2s而FAIL |
| AC-10 | measurement可能区间跨过canonical边界 | NOT_EVALUATED；无依据不得缩小误差 |
| AC-11 | 合格测量完全位于允许窗口之外 | FAIL；不会为了提高通过率移动窗口 |
| AC-12 | 只有ASR segment end，无法证明所需事件/精度 | diagnostic或NE；不假造word timestamps |
| AC-13 | C/diagnostic写入acceptance observations或hard写入advisory | source admission拒绝，纯diagnosis也防御旁路；不能静默drop |
| AC-14 | 最终字幕缺于raw，或raw Finding试图回答final项 | 前者不作raw blocker，后者stage mismatch；最终缺字幕仍阻断 |
| AC-15 | 新marker缺metadata、未知version、发送/1或删除marker降级 | fail closed，不使用legacy默认值取得新资格 |
| AC-16 | legacy QA/Recipe/source/experience/Manifest/rejection reopen | 字段、hash、原diagnosis和verdict不变；包含legacy human FAIL兜底案例 |
| AC-17 | 同goal只修改rubric/level以绕修复；或None→newgoal冒充既有version revision | 按原规则拒绝；不补造history/goal、不重置quota |
| AC-18 | 12/13 exact bytes进入proposed语义shadow replay | 原历史独立重放不变；新解释引用原证据；human/最终输出缺口明确 |
| AC-19 | freeze derivative timing改善但自然动态已FAIL | 已知违规在方案选择/执行前拒绝；repair不得成功关闭 |
| AC-20 | 原required/optional baseline PASS在修复后变FAIL或NOT_EVALUATED | no-regression继续阻断；不能因重新分类删除原baseline |
| AC-21 | 仅排序/保留candidate或仅有advisory source | 不产生activation、source-use PASS、下一Shot或Final Acceptance权限 |
| AC-22 | quota耗尽、outcome unknown、错provenance/asset identity | 原gate继续拒绝；不增加permit、重试、recovery或writer旁路 |
| AC-23 | 新marked recipe中仅用于diagnostic/排名的项没有native prompt witness | 不强制入prompt；真实raw acceptance/authored intent的遗漏仍拒绝 |
| AC-24 | 正确item hash旁写了与typed时间结果矛盾的FAIL或错误阈值 | 重算不一致，拒绝该source；证明hash本身不足以产生合格判断 |
| AC-25 | 全部已声明hard均PASS，但存在未映射的真实质量拒绝；随后strict reopen/合并新PASS | source与AttemptEvidence exact projection保留；diagnosis/Feedback仍阻断并交QA owner；不得虚构required FAIL或把C意见变veto |
| AC-26 | 回答后补写正确question/hash，或仅提交caller时间戳；真实presentation/answer来源缺失 | 前者错绑拒绝，后者EVIDENCE_GAP；existing analysis proof不能充当提问顺序证明 |
| AC-27 | 生成前创建QA/recipe，fetch后绑定实际输出并录入时间测量 | 预生成criterion不依赖未来MP4；输出错绑仍拒绝；无QA/request/output identity循环 |

### Engineering Acceptance

工程完成需证明 schema/serialization、正常与失败路径、standard loader、source admission、
compiler coverage、diagnosis、Feedback recording及原 Final-output/no-regression 契约。
必须涵盖至少一个非S01、非Vidu的fixture，确保没有把example ID、阈值或Provider硬编码。
所有离线模拟必须明确标为fixture，不能冒充真实human或模型质量证明。

Focused surfaces 可复用现有 generation evaluation/feedback/review/history、
production generation decision、no-regression、final-output 和 Director Skill tests。
实际 changed-path check组合继续由 .agent/harness/policy.yaml 决定；
后续实现需完成其 exact-snapshot Harness 证据。此处不创建新的 check registry 或重新设计 Harness。

### Empirical Quality Benefit

以下结论不能由 AC 或 Harness 通过推出：模型动作更自然、首轮可用率提高、总体通过率提高、
repair更少、成本下降、优于人在Seedance/Runway/Luma内手工挑片。

后续若要验证收益，应预先固定真实hard rubric、候选来源、预算/停止条件与观看条件：
同候选池比较错误拒绝/漏检与holistic选择；同生产预算比较完整流程。
报告硬约束漏检、错误拒绝、最终盲评、每条可交付Shot的生成/repair数及人工review时间。
候选更少或PASS比例更高不能单独证明收益；旧坏标准统计不能直接当作新语义成功概率。
本 Spec 不授权该实验，不规定N，也不凭12/13两个相关历史样本宣称统计优势。

## Non-Goals

- best-of-N engine、batch submit、动态candidate-count算法或production采样策略实现。
- Exploration Manager、第二 Director、新 Resolver、新 QA lifecycle或新 state machine。
- Provider ranking、换模型、新增模型/Provider、pricing研究或现有执行授权扩张。
- VIDEO_EDIT、source-preserving edit executor、retime、freeze、音轨替换或任何媒体修复。
- 通用自动审美 evaluator、训练模型、姿态/物理测量系统或自然语言entailment引擎。
- 重新设计整个Harness、coverage审美规则、timeline、renderer或P6。
- 自动迁移真实S01、撤销旧FAIL/abandonment、重写旧QA或重新激活历史媒体。
- 将shadow评价写回经验成功率、学习采用、预算或Production state。

## Source Anchors

规范依据是当前源码和既有owner；下列历史仅说明问题，不授予当前操作权限。

- [Director Skill](../../../.agents/skills/open-video/SKILL.md) 与
  [coverage validator](../../../.agents/skills/open-video/scripts/validate_director_coverage.py)。
- [RequirementExpression / Recipe](../../../src/ai_video/production/generation_recipe.py)、
  [QA / Domain acceptance](../../../src/ai_video/production/domain_acceptance.py)。
- [Generation evaluation](../../../src/ai_video/production/generation_evaluation.py)、
  [diagnosis](../../../src/ai_video/production/generation_diagnosis.py)、
  [decision](../../../src/ai_video/production/generation_decision.py)。
- [Feedback](../../../src/ai_video/production/generation_feedback.py)、
  [MCP review bridge](../../../src/ai_video_mcp/generation_feedback.py)。
- [Final-output contracts](../../../src/ai_video/production/final_output_contracts.py)、
  [final review](../../../src/ai_video/production/final_output_review.py)。
- [Production Strategy](../../../src/ai_video/planning/production_strategy.py)、
  [contract matrix](../../agent-primary-contract-matrix.md)。
- [Original creative input](../artifacts/drama/jieshi-episode-01/creative-input.md)、
  [S01 authoring](../artifacts/drama/jieshi-episode-01/episode-01.md)。
- [Attempt09 directing margin](../../../runs/jieshi-e01-i2v-20260906-attempt09/request-draft.json)、
  [Attempt09 Gate](../../../runs/jieshi-e01-i2v-20260906-attempt09/preparation-v1/shot-01-gate.md)、
  [retrospective projection](../../../runs/jieshi-e01-i2v-20260907-attempt10/diagnose_previous.py)。
- [QA 2.3 inventory](../../../runs/jieshi-e01-i2v-20260907-attempt10/preparation-v1/acceptance-policy.json)、
  [selected QA copy](../../../runs/jieshi-e01-i2v-20260907-attempt10/preparation-v2/current-qa-policy.json)。
- [Attempt12 Gate](../../../runs/jieshi-e01-i2v-20260907-attempt10/preparation-v4/shot-01-gate.json)、
  [human source](../../../runs/jieshi-e01-i2v-20260907-attempt10/preparation-v4/attempt12-human-confirmation.json)、
  [Attempt13 Gate](../../../runs/jieshi-e01-i2v-20260907-attempt10/preparation-v5/shot-01-gate.json)、
  [adjudicate script](../../../runs/jieshi-e01-i2v-20260907-attempt10/preparation-v5/orchestration/review_s01_attempt13.py)。
- [S01 history and rejected freeze](../../record_for_agent/2026-09-08-jieshi-s01-human-gap-history-boundary.md)、
  [exact rejection](../../../runs/jieshi-s01-retime-review-20260908-v1/human-rejection.json)。
