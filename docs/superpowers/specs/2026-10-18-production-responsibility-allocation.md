# Production Responsibility Allocation

## Goal And Authority

用户明确要求实现通用制作分工。沿现有 QA inventory、component/assembly allocation、Planner、compiler 和最终验收 owner 完成，不以《界蚀》或机器人特例实现。授权工程、离线准备与验证；无新付费媒体 POST、依赖、Provider 或 Production 实验授权。Parent 自审并实施本合同。

## Existing Capability And Confirmed Gap

`RequirementSemantics` 已区分必须结果、偏好、允许变化；`stage` 已区分原片、剪辑、成片。`input_control` 已表达实际生成/参考职责；`ProductionRequirementAllocation` 与 `ProductionIntent` 已分配组件及 assembly；`ProductionStrategyResolver` 已选择复用/剪辑/生成，拒绝未实现操作。

缺口是 allocation 的 ID 覆盖不保证每项目标有可执行、可验收的承担阶段；组件原片 rubric 可漏掉未分给 assembly 的目标。Canvas preflight 与 exact input preview 尚未完整展示语义、自由度及实际承担步骤。此次不新增第二份可编辑分工计划或自动审美判断。

## Contract

- 分工仍只来自 QA 的既有 inventory 与 component/assembly IDs。模型必须结果与参考职责保持其 raw acceptance；偏好/允许变化仅按既有非固定 `recipe_hint` 表达，不升级为 required finding，也不自动删除或重写原生文本。
- 新 QA publication 和当前策略使用时，有 generation rubric 的每个组件必须覆盖自身所有未交给 assembly 的 required IDs。rubric 的全部 required IDs 必须是真正的 `acceptance/raw_generation`，不能把 hint 或 final-stage 条目伪装成原片覆盖。多个组件重复承担同一目标、原片与成片同时检查同一目标均合法。
- assembly 的目标必须绑定既有 `FinalOutputContract` 中相同 ID 的结果。已声明的 final-stage predicate 继续由原 semantics/final-contract owner 核验；不隐式转换 technical/human/evaluator proof，不把“后期负责”当作已有修复能力。
- source-only 组件不强造 generation rubric；原 source-use owner 仍检查完整 exact bytes/window/map/transform 和内容证据。未知、失败、过期和新用途缺证均保持原行为。历史模型反序列化、hash、lookup 和已持久化结果不被重写；新 publication/use 的不完整分工返回明确 authoring blocker。
- 预览由同一校验和现有事实投影：逐项目标的 level/stage、语义/固定来源、model guidance/允许变化、原生成 owner、component/assembly 分配、实际操作、原 map 和最终验收要求。缺 QA/语义/选择时明确未评估，不猜意图或自动改 stage。
- 参考预览保留 exact native text/绑定及机制，补足“必须结果/允许变化/交由后期”的视图。非 raw 的派生 native fragments 不再冒充模型输入；原用户文本不变。
- 默认策略仍为 `/2`；变速、声音、字幕、trim/frame/sample 归现有 source-use、ResolvedTimeline 和 HyperFrames。`MASK_COMPOSITE/TRACKING/LIP_SYNC` 等无 executor 的操作保持 capability blocker。原片 FAIL 不被新分工改成 PASS，编辑用途和成片需要新 exact 证据。

## Acceptance And Boundaries

正常、缺项、误分阶段、偏好硬化、伪修复、source-use 缺证、历史重开和无 POST 路径有可执行验证。不同人物/动作/空间至少三个案例走同一共享预览；H3 Max 与 Seedance 的 actual compiler 验证 raw 目标进入输入而 editorial/final 目标不被自动塞入 prompt。离线证据不证明模型质量、故事通过、human 或 Production activation。

《界蚀》只作为当前只读例证；保留 S01 STOP、原15项及历史消费、S02 POST0。工程发布仍需适用 Harness、Risk Gate、owned-path commit/push 与远端 SHA；没有当前有限授权不调用媒体服务。
