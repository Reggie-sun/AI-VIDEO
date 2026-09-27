# Creative Goal Preservation And Completion

Date: 2026-09-27
Status: Approved for offline implementation — 2026-09-27
Scope: Development authoring、导演决策与成片复核；用户后续明确要求实现配套 plan，未授权业务媒体或 empirical acceptance。
Companion Plan: [Creative Goal Preservation And Completion Implementation Plan](../plans/2026-09-27-creative-goal-preservation-and-completion.md)

## Goal

让 Agent 持续对用户想看的作品负责：从相关上下文提取目标，先设计能表达目标的内容，再选择素材和技术，观看实际成片后修复。广告与电视剧共用这一闭环，但各自保留内容标准。

本次要防止的具体失败是：为修包装错字，把作品缩成全程一张商品照片的图文片；随后以这个自行缩小的目标组织检查，最后交出文件结束任务。修复必须减少这种创作选择和执行错误，不能只换一个“候选”标签。

## Evidence And Existing Behavior

依据当前 `13b7c29` 的源码及青颜 exact run：

- `validate_director_coverage.py::_validate_v4_intent_handoff` 已校验用户原话子串和 exact source hash，区分 `explicit_user`、`director_choice`、`repair_margin`。它不能证明 caller 提供了完整相关上下文，或自然语言方案充分回应了目标。
- `FinalOutputContract` 已有 `goal_id`、`goal_version`、`user_goal`、逐项 requirements；`visual_quality_report.prepare/reopen/check` 已保留完整合同并复用 `adjudicate_final_output`。不是再次实现“额外要求不得被五维视觉 PASS 遮蔽”。
- `ecommerce_quality_gate.validate_ecommerce_final_output_contract` 已严格比较 handoff 与 QA 的成片要求。其输入上游的遗漏，不能由这项相等检查识别。
- 青颜 10 秒片 SHA-256 为 `25cd328bcbf395660a0e213d0c541c1c68bd49dc6304eedb936b912aeefa76a6`。`runs/ecommerce-qingyan-packshot-20260927-001/preflight/creative-brief.md` 只引用当轮“那你现在再生成视频我看下”，将原图图文形式列为导演选择。完整报告保留了三项 `NOT_EVALUATED`，没有伪造整体 PASS；但这不意味着创作决策合理或任务已经完成。
- 用户随后明确否定“全程一张图”，并指出此前已经要求从根本上解决问题。这是对该作品的新反馈，必须影响后续方案；不能倒填为旧合同在渲染前就有的要求，也不能抹掉历史技术检测。

根因判断：避险和现成素材主导创作、跨轮意图承接不足、独立检查范围偏向局部正确性，以及交出文件后停止推进。前三者影响作品，最后一项影响执行闭环。哈希、字段和措辞修复只解决其中可机械验证的部分。

## Scope And Ownership

| Concern | Owner and boundary |
| --- | --- |
| 用户目标、导演方案与相关历史 | Native Codex + 既有 creative brief、Director v4 与 Character / Scene / Shot artifacts |
| 广告内容与商品真实性 | `ecommerce-ad-workflow` 的 Product Truth、Strategy、Hook / Beats、Presentation、Copy / Audio、Storyboard；不套用于剧情 |
| 意图到现有合同的引用检查 | Development-only helper，读取现有 artifacts，只出 diagnostics；不得成为 Runtime dependency |
| 成片要求与 verdict | 原 `FinalOutputContract` / `final_output_review.py`，不另建审美裁决器 |
| 开发侧审片展示 | 原 `scripts/visual_quality_report.py`；汇总证据和缺口，不签发 Production acceptance |
| 执行、timeline、render、review lifecycle、delivery | 既有 canonical owners，全部保留 |

本 spec 为 T2 authoring / development-tooling 设计，不改变 Production QA 的 PASS 条件或接受主体。若 implementation 发现必须改变 QA、Manifest、activation 或 paid/recovery 语义，属于另行明确的 T3 scope，不能从本 spec 推导授权。

## Intent Across Turns

制作前在现有 creative brief 保存最小相关上下文：当轮请求、仍有效的前轮明确要求、已经发生的作品反馈，以及用户明确做过的范围变更。每段保留可定位原话及来源；不要复制无关完整聊天或凭记忆补造逐字引文。

这些相关原话进入既有 `request.creative_input_evidence`；v4 的 `explicit_user` intent 继续绑定该 exact 文本。导演对“好看”的解释属于 `director_choice`，不能伪装成用户明确指定的人物、镜头数、片长或具体情节。缺少可重开原文时注明来源缺口；由 Parent 依据当前可见对话核对，不能制造 provenance。

原要求只能因用户明确取消、替换或收窄而退役。Agent 认为难做、素材不足、避免再错或费用方便都不是取消依据。无法满足时保留目标与具体缺口：在现有授权中选择等效表达；确需改变目标、额外预算或外部条件时，再提交具体可选择方案。告知用户“我改成静态片了”本身不是批准。

用户反馈形成新的 authoring revision，引用旧方案和受影响要求；原片、旧合同与旧报告保持可重开。历史静态片无须被追溯判成违反尚未提出的硬性镜头要求，但不得再把已被拒绝的方案当作本任务当前合格答案。

## Director Decision Before Production

先说明观众要看到、理解或感受到什么，再说明画面、行动、声音与剪辑如何完成它，最后选择可实现这些内容的素材和技术。现有 coverage 的 `objective`、`open_state`、`close_state`、`visible_change`、`camera_intent` 承接方案，不增加重复的镜头模型。

广告的关键判断是具体诉求和表达是否成立：商品为什么值得关注、哪些信息有可信画面或声音支持、观看过程如何组织，以及本次目标是否要求购买行动。品牌氛围片可以不演示功能；不能因为演示难做，就偷偷把需要说服或演示的任务改成品牌露出。商品包装可采用真实素材的独立展示段，其他内容按其目的设计，不把整片冻结来保护包装。

剧情的关键判断是人物想做什么、采取什么行动、对方如何反应，以及关系、信息、情绪或处境如何发展。固定机位中的表演、长时间沉默或空间声音都可能承载变化；人物立绘加对白字幕不能自动代替要求的表演和动作。

生成或合成前，独立 context 先读相关原始意图、用户反馈与候选 coverage，再回答：

1. 用户要求有无遗漏、偷换，方案为何适合本任务？
2. 观众在作品里实际能看到或听到哪些内容，哪些只有作者说明中存在？
3. 最关键且最不确定的表达是什么，现有素材或能力是否足够？

作者的技术避险理由放在这些判断之后。Reviewer 给 evidence 和具体不足，Parent 裁决；不以分数或“reviewer PASS”代替判断。明显不足先改方案，再做媒体；缺能力就处理缺口，不能继续制作一个已知无法回答任务的版本。

不强制多镜头、真人、运动比例、固定广告套路或先做多个付费备选。简单且成立的方案一次检查即可推进；只有确需取证的不确定部分，才在适用授权和有限预算下做最小实验。该 spec 不授权任何实验。

## Minimal Executable Handoff

保留 Director v3/v4 与 `FinalOutputContract` schema。新开发侧输入采用一个薄的 `creative-goal-binding/1` 引用封套，绑定 exact creative-input text、coverage JSON 和完整合同的路径与 SHA-256；它只保存引用和映射，不复制目标、镜头内容、QA verdict 或 mutable lifecycle。

封套的 `bindings` 每项关联一个已有 `intent_item_id`、一组既有 `constraint_ids`、零个或多个已有 coverage `unit_id`、一个或多个已有 `requirement_id`。每个当前有效的用户意图必须有成片 requirement，并至少关联一个既有 `request.creative_constraints` 条目；scope 只读取该条目的 `global` / `beat_specific`，不从自然语言猜测，也不在封套再造分类。缺少这层关系时返回 `unresolved_intent_scope`。

仅关联 global constraints 的意图可以没有专属 coverage unit；只要关联了 beat-specific constraint，封套就必须覆盖所有在既有 coverage 中引用这些 constraint IDs 的 units，且每个被引用的 beat-specific constraint 都至少出现在一个 unit。沿用原 validator 检查 constraint/coverage 关系，helper 只补 intent 到它们的精确 join；这证明所声明 scope 和映射自洽，不证明作者把 scope 分对了。退役要求从当前 inventory 移出前，brief 必须保留用户变更的来源；机械检查不自行判定用户是否授权。

新增 focused helper 应支持只读检查：重开 exact 文件；运行既有 Director validator；校验引用 identity、ID 存在性、重复/遗漏、完整合同身份与关系。输出稳定 diagnostics，例如 `source_identity_mismatch`、`unbound_user_intent`、`unknown_requirement`、`stale_binding`。非法输入不 probe、不抽帧、不生成、不写 Production state。

新创作闭环的审片 prepare 必须消费通过该检查的封套与同一完整合同；封套缺失或无效时不能标为“目标链已核对”。旧视觉检查 API 和 packet `/1`、`/2` 继续按原范围工作，不能因历史没有封套而拒绝重开或伪称完成了新检查。新绑定证据由显式新 packet version 保存，历史字节和 hash 不变。

结构检查能发现已登记意图在交接时丢失，不能发现所有未被提取的要求，也不能证明“对应了 requirement”就语义满足。Parent 与独立 concept review 仍需看原始输入；不能用一条空泛“整体好看”requirement 给所有意图挂名覆盖。

## Review Actual Output And Continue Repair

成片评审输入是 exact MP4、原始任务意图及有效反馈、完整合同和实际 viewing capabilities。作者的解释、既有评分与通过记录不得先替 reviewer 定调。评审覆盖画面、时间上的变化、声音及内容效果；抽帧只证明抽样帧，音轨存在和响度测量不证明听感。

AI 不能填写 `HUMAN`，未完成原速完整观看、聆听的项目保持 `NOT_EVALUATED`。能观察的内容缺陷应明确指出并修复，不因需要用户最终审美意见，就把基础检查推给用户。

按既有 repair 路径处理结果：内容不足先改创作/镜头，媒体缺陷修对应素材或合成，缺证据先补证。改变后的 exact artifact 需要新评审；保留原目标、已满足要求与旧失败证据，不通过删 requirement、改 `proof`、换目标版本或改名消除失败。Unknown outcome、能力/授权缺口与有限额度耗尽遵守既有停止规则。

不能自动决定所有自然语言修复，也不新建通用自动创作调度器。本次要落地的是 Parent 在既有调用入口消费检查结果并继续工作，直到：可检查的已知缺陷已处理、只剩明确的人类反馈，或存在具体且真实的阻碍。

## Completion Communication

开发报告从当前 exact 输入和既有 adjudicator 结果派生一段交付摘要，列出：文件 identity、实际复核范围、FAIL / NOT_EVALUATED 的要求、用户拒绝或未决反馈、下一动作。摘要不保存新的任务状态、不签发 Production delivery，不自行覆盖 QA verdict。

逐项摘要必须反映有效证据，而不是直接照抄 `findings` 中 evaluator 的原始 PASS。若当前 aggregate API 不暴露逐项有效性，应在原 `final_output_review.py` owner 内提取一次共用的详细裁决计算，原 aggregate API 继续投影相同结果，报告只消费它；不得在开发 helper 复制 proof、观看方式或身份判断。无效 human proof、身份过期或缺失观察对应项显示 `NOT_EVALUATED`，原始回答可另列为原始回答。该提取不改变既有 verdict 优先级、输入有效性、public schema 或 acceptance 语义，并须有等价回归。

| Evidence situation | What the Agent does |
| --- | --- |
| 已知方案不足、有效 FAIL 或用户已拒绝该方案 | 继续修复；如展示则说明是问题定位材料及下一动作，不能换称“候选”结束制作任务 |
| 缺少可获得的基础视听检查 | 先补证；工具确实不具备观察能力时说明未评估项与所需最小检查，不称完成 |
| 基础检查已完成，只剩真正需要用户的整体偏好或 human acceptance | 可立即展示供用户观看，明确这是候选及剩余判断，不要求全部预览先获批准 |
| 完整开发评审符合原目标 | 可报告开发创作与复核已完成；Production acceptance / delivery 仍只能引用原 owner 的实际 evidence |

工具只能检查结构化摘要与输入是否一致，不能拦截任意聊天或证明 Agent 真实观看。禁止把摘要 lint 的成功包装成“创作目标已达成”。

## Acceptance Criteria

| ID | Executable case and expected behavior |
| --- | --- |
| A1 | 前轮明确要求与当前“继续生成”共同进入 fixture；删掉已登记前轮意图的 requirement binding，检查返回 `unbound_user_intent`，零媒体副作用 |
| A2 | 修改 source 文本、coverage 或合同后复用旧封套，检查拒绝；未知或重复 ID 拒绝；hash 正确但语义空泛只能证明结构通过 |
| A3 | 广告中“可见使用动作”与剧情中“人物递出物件”的两组 fixture，intent 显式关联既有 beat-specific constraint，仅删除封套的对应 unit 时失败；global 禁止项无专属镜头但有 requirement 时合法；缺少 intent→constraint 关系返回 `unresolved_intent_scope`，不得依赖关键词或 fixture 名称 |
| A4 | Director v3/v4、旧 packet `/1`、`/2` 与 positional API 回归不变；新链检查缺失不能显示为已完成；新 packet 保存可重开的 exact 引用 |
| A5 | 五维视觉 PASS，但商品、叙事或音频要求 FAIL / 缺失，继续使用原 adjudicator 得到 FAIL / NOT_EVALUATED；摘要不得显示完成 |
| A6 | 原片结果为 NOT_EVALUATED，补充技术 decode / probe PASS 不改变人类要求；sampled frames 不能变成 full playback 或 HUMAN。即使所有原始回答均为 PASS，只要 human proof 无效，相关逐项摘要也必须明确显示 NOT_EVALUATED；详细计算与原 aggregate verdict 在现有合法/非法 evidence 回归中等价 |
| A7 | 用户拒绝静态片后，新反馈只作用于新 authoring revision；旧合同/hash/report 保留；当前展示摘要必须披露未解决拒绝，不能以旧技术 PASS 关闭 |
| A8 | 合理的单镜头表演、获明确同意的静物品牌片均可通过结构检查；测试不得以镜头数、运动量或“静态”关键词统一拒绝 |
| A9 | 修复中删除已知失败要求或复用旧媒体评审，回归测试保持拒绝；unknown outcome 与预算边界不因创作修复放宽 |
| A10 | 至少通过一次从真实开发入口到审片摘要的离线接线测试；只测 helper 而调用者未消费，不算接入完成；Runtime 不 import Skill / development helper |

机器测试以可控结构/身份/已知 verdict 为 oracle，不声称测出了“好看”。语义充分性另外保留两类人工可复核案例：青颜的静态替代为什么不满足当前任务；剧情中虽单镜头但具有真实行动和情绪发展的成立方案。独立 reviewer 必须能指出内容证据，不能靠 fixture 名称判断。

## Verification And Rollout Boundary

后续批准 implementation 时先写 failing tests，再实现最小交接与摘要接线；focused verification 覆盖 `tests/test_open_video_skill.py`、`tests/test_visual_quality_report.py`、`tests/test_production_final_output.py`、`tests/test_runtime_skill_boundary.py` 及新增 helper 的行为测试。新增路径同步 matrix / Harness routing，按实际 changed paths 对 exact snapshot 验证。

实现交付必须分开报告：结构完整性、真实调用入口接线、导演语义检查、实际媒体观看证据。前两项通过只证明离线工程闭环；不得宣称已根治审美问题。

验证真正改善出片还需要两次有明确任务目标的实际案例：广告和剧情各一次，沿用真实目标制定内容、检查成片并记录用户评价。它们是 empirical acceptance，不是再加字段就能通过的测试；须在各自任务授权、能力和有限预算具备时执行，本轮不运行。用户仍不满意时回到具体内容缺陷，不追加通用规则假装问题已解决。

## Non-Goals

不增加 Provider / 模型、runtime dependency、公共 `ai-video` CLI、Manifest / Registry schema、renderer、timeline、第二套 QA / delivery truth 或自动发布；不改通用授权、permit、recovery 和质量底线；不建立聊天拦截器、自动审美评分或固定镜头配额；不宣称能消除所有创作失败。

用户先要求同时编写 spec 与 plan，随后于 2026-09-27 明确要求实现配套 plan，批准此处的 offline implementation scope；业务媒体执行和 empirical acceptance 仍须各任务具备授权。旧 [Creative Completion Loop](2026-09-26-creative-completion-loop.md) 已实现的完整合同报告保持有效；本 spec 补充其上游目标承接与下游执行责任，不将旧实现重述为未完成。工程实证及未验证边界见 [implementation record](../../record_for_agent/2026-09-27-creative-goal-preservation-implementation.md)。
