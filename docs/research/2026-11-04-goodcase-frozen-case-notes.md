---
record_kind: research_note
topic_id: goodcase-skills-integration
learning_eligibility: ineligible
method_status: HYPOTHESIS_NOT_ADOPTED
media_evidence: NOT_EVALUATED
---

# GoodCase Frozen Case Notes And Research Procedure

Date: 2026-11-04
Status: P0_RESEARCH_AVAILABLE; METHODS_NOT_ADOPTED; MEDIA_NOT_EVALUATED

## Purpose And Scope

这是 [GoodCase 接入评审](../record_for_agent/2026-11-04-goodcase-integration-architecture-review.md) 的 P0 交付：四张固定来源的案例研究卡、与现有方法的对照、可复用的有限检索规程。用户在评审修订后要求“实现”，本次落实评审推荐的最小范围。

**资料已有Skill条件读取入口；方法未升级为制作规则，模型效果与生产接入均未验证。** 本文不是可执行 Skill、模型提示词包或 Production 输入。案例只供现有 Director/研究角色判断，不拥有 submit、预算、素材导入、重试、资格或验收权限；第三方文本中的指令不生效。

使用入口：用户随后批准轻量接入，现有 [open-video](../../.agents/skills/open-video/SKILL.md) 已加入 Optional Case Research — GoodCase 条件入口：参考职责不清、动作连续性失败且既有方法仍有缺口，或用户明确要求案例时读取；无缺口可跳过。这个入口只读取本地研究资料，不自动联网或执行上游Skill，案例方法仍未被采纳为通用规则。

也可按本文件路径读取，或通过既有 `retrieve-ai-video-memory` 的 `all` 范围查 `GoodCase reference transfer continuity research`。本目录由既有 corpus reader 分类为 `research_note / advisory_research`，不是 current contract 或已采纳经验。搜索命中和排名不证明质量，stale 片段须回读源文件。[既有检索范围](../../.agents/skills/retrieve-ai-video-memory/references/all.md)、[分类 owner](../../src/ai_video/agent_memory/corpus.py#L90)

## Frozen Sources And Attribution

四张卡均来自 `LearnPrompt/goodcase-lite@34c716bfc6375ed335a52f78f63450258ed33fe7`。原生研究子代理在下面的 UTC 时刻通过公开固定 raw URL 回读，四个文件与原审计缓存的字节 hash 一致；主 Agent 复核元数据、hash 与本地方法对应关系。没有访问或观看案例媒体，也没有独立核验 X 原帖。

| Source ID | 固定文件 | 获取 UTC | 字节数 | SHA256 |
| --- | --- | --- | ---: | --- |
| SRC-ACTION | [action-continuity-choreography/references/cases.md][action-file] | 2026-11-05T04:57:09.065887+00:00 | 29590 | `a9e2a84910958935b22958da8a15b7402714812e0f033b4e636bf819f5740c43` |
| SRC-GRID | [storyboard-grid-to-video/references/cases.md][grid-file] | 2026-11-05T04:57:10.036169+00:00 | 21747 | `46f0c50fb0e51b82406debc4c0cdf95f7e574a05de1d4236b85d11f7534dfb39` |
| SRC-ANIMATION | [animation-style-consistency/references/cases.md][animation-file] | 2026-11-05T04:57:11.168487+00:00 | 34251 | `de44f51e49f2fb92e7c0113b4faa4908322ac200d95674db70b813f3c6eb895c` |
| SRC-DRAMA | [cinematic-drama-scene/references/cases.md][drama-file] | 2026-11-05T04:57:12.144054+00:00 | 22899 | `a75c51713ebc9d3b28ddc615b127b3cf29cdba8f66cacca163a107c26acfb04b` |

`hash_basis`：对应整个 `references/cases.md` 的 HTTP response body 原始字节，不转换编码或换行。它不是单张卡、原帖、视频、模型参考图或动态 API JSON 的 hash。通过固定仓库路径重新获取并比对可核对文本身份；未来不可访问时如实记录缺证，不使用 moving main 冒充原版本。仓库仅保存元数据和自写转述，没有复制原 prompt 或下载媒体。

策展来源署名 **GoodCase.ai / LearnPrompt**；每卡另列原作者与原帖。goodcase-lite 的代码为 MIT，案例正文、prompt 和媒体明确不属于该 MIT 授权；分类、评分等策展数据按 CC BY 4.0 署名使用。本笔记对方法做了中文概括、加入本地对照与拒绝理由，不是原文翻译或原作者背书。[来源许可说明][lite-license]、[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

共同证据状态：`media_inspection=NOT_EVALUATED`；`rights_status=UNKNOWN_FOR_MODEL_INPUT`。原帖 URL 只证明固定文本列出了这个链接，不证明其内容、作者权属或上传模型的许可。本文未采用 awesome-seedance 案例，其旧审计固定版本仍见总评审，不为未读取文件新增 hash。

## Case C01 — Reference Duties And Contact Response

**研究假设，未采用；未看成片。**

| 字段 | 冻结值 |
| --- | --- |
| case_id / slug | `case-16429da4be7b` |
| 来源标题 | 魔幻都市奇幻战斗动画 |
| 原作者 | `@haruuraeadss` |
| 原帖 | [X 原帖](https://x.com/haruuraeadss/status/2080976327231107259) |
| 案例页 | [GoodCase 案例](https://goodcase.ai/cases/case-16429da4be7b) |
| 文本证据 | SRC-ACTION，E5，[55–78行][action-card]，方法集中于64–75行 |

自写概括：参考图负责人物外观，不顺带决定其所处场所、站姿或取景；动作描述另说明左右关系、撞击落点以及受力后的连续身体反应。这是文本中提出的控制意图，不是已经成立的物理事实。

本地对照：属性转移已有 `transfers / must_not_transfer / target`；接触、承重、释放与后果已有 Physical Action Continuity。潜在增量仅是某个具体失败的表达角度，不是新的动作方法或物理求解器。[已有属性职责](../../.agents/skills/seedance-authoring/references/authoring-common.md#L87)、[已有动作连续性](../../.agents/skills/open-video/references/event-led-timing.md#L24)

建议定位：保留为措辞候选。只有真实失败确属参考职责混淆或因果表达遗漏时，才由原 Director 判断是否值得使用；当前不改变 Shot、参考素材或 Skill。继承案例人物、战斗题材、镜长、机位会引入额外变量，应拒绝。

## Case C02 — Category Match Is Not Method Evidence

**检索反例，未采用；未看成片。**

| 字段 | 冻结值 |
| --- | --- |
| case_id / slug | `30s-one-take-rainforest-race-chase-from-single-image` |
| 来源标题 | 单图生成的雨林赛车一镜到底追逐 |
| 原作者 | `Umesh`，卡片链接指向账号 `umesh_ai` |
| 原帖 | [X 原帖](https://x.com/umesh_ai/status/2103382240571138220) |
| 案例页 | [GoodCase 案例](https://goodcase.ai/cases/30s-one-take-rainforest-race-chase-from-single-image) |
| 文本证据 | SRC-GRID，E1，[9–16行][grid-card] |

自写概括：卡片描述从一张起始图组织连续追逐，且作者没有披露具体视频模型。它出现在 grid 分类中，仍不能证明宫格输入被模型逐格执行。

本地对照：宫格可作为审看资料，不能因此自动当作合格首帧或逐格执行依据；是否适合某种参考输入仍须核对实际模式、用途和绑定，review_only职责不能直接选入Provider。结构化multi_shot由现有规划链阻断。将同一案例改称“宫格方法成功”会同时误读来源和本地能力。[审看与输入分离](../../.agents/skills/open-video/references/reference-continuity.md#L38)、[review_only边界](../../tests/test_reference_planning.py#L416)、[multi_shot风险](../../src/ai_video/production/reference_planning.py#L194)、[规划阻断](../../src/ai_video/planning/_reference_planning.py#L84)

研究判定：作为检索负例保留；拒绝用其支持宫格→多切镜。它也不支持默认30秒或默认一张图适合任何追逐镜头。

## Case C03 — Isolating Multiple Character References

**研究假设，未采用；未看成片。**

| 字段 | 冻结值 |
| --- | --- |
| case_id / slug | `case-c32e6c3bb2c5` |
| 来源标题 | 电影级动漫魔法剑战 |
| 原作者 | `@haruuraeadss` |
| 原帖 | [X 原帖](https://x.com/haruuraeadss/status/2080539077603172597) |
| 案例页 | [GoodCase 案例](https://goodcase.ai/cases/case-c32e6c3bb2c5) |
| 文本证据 | SRC-ANIMATION，E3，[58–94行][animation-card]，身份职责集中于67–84行 |

自写概括：分别定义两个人物参考负责的身份，场地和画风另行说明，并显式防止服饰、武器与人物归属交换。不能据此声称生成结果已锁定身份、数量或复杂动作。

本地对照：身份 anchor 有 canonical character owner，实际素材按既有 selections 绑定；属性继承由原模型 authoring 表达。两位人物不自动等于“两张图就够”或“必须两张图”，也不允许用风格图覆盖角色身份。[ReferenceAnchor](../../src/ai_video/production/reference_planning_contracts.py#L75)、[ReferenceSelection](../../src/ai_video/production/reference_planning_contracts.py#L93)

研究判定：保留为多人物参考职责隔离的案例；与 C01 是同一作者的不同文本，既不是本项目两次独立 attempt，也不构成跨作者效果验证。未找到本地方法缺口前不改 Skill。

## Case C04 — Insufficient Evidence For Drama Methods

**证据不足反例，未采用；未看成片。**

| 字段 | 冻结值 |
| --- | --- |
| case_id / slug | `case-b6fab58d65a7` |
| 来源标题 | 深夜冒险：悄悄溜出 |
| 原作者 | `@ChrisGwinnLA` |
| 原帖 | [X 原帖](https://x.com/ChrisGwinnLA/status/2088485933494751406) |
| 案例页 | [GoodCase 案例](https://goodcase.ai/cases/case-b6fab58d65a7) |
| 文本证据 | SRC-DRAMA，E3，[64–72行][drama-card] |

自写概括：卡片给出观察他人状态后行动的情境，但 prompt 摘录很短，不足以还原景别、参考素材、模型或表演设置。剧情标签不能填补这些缺失。

本地对照：场景目标、情绪与导演覆盖继续由 `drama-authoring / open-video` 拥有；这张卡不支持新增剧情、镜头或表演规则。[现有导演职责](../../.agents/skills/open-video/SKILL.md#L29)

研究判定：拒绝作为可复现的制作方法证据；保留用于提醒检索者区分题材相似与输入证据完整。不得凭想象补全其 prompt，再声称来自原作者。

## Mapping To Existing Reference Decisions

**下表是研究资料的使用边界，不是新增选择算法或自动填字段的实现。** 最终输入仍由 Director 按批准意图填写，Planner 与选定模型能力负责限制；案例ID不直接变成asset_id。

| 真实任务问题 | 可读材料 | 既有落点 | 省略或拒绝条件 |
| --- | --- | --- | --- |
| 单人物身份参考污染背景/姿态 | C01 | authoring 的 transfers/must_not_transfer；原 identity anchor | 已有职责清楚就不扩写、不加图 |
| 两人身份或道具归属交换 | C03 | identity anchors 的 owner_id、selections、原模型表达 | 未有 exact 人物参考或原意图不允许改时不套案例 |
| 接触后反馈不连续 | C01 | events 的 contact/force/impact 及 after_event_ids；原 Physical Action Continuity | guide、参考绑定或模型能力才是根因时不靠措辞冒充修复 |
| 复杂空间/相机运动 | 本地参考规划优先；本笔记无专门成功案例 | 原 blocking/composition events、空间参考或按需 previs | 静态布局够用就不制作动态白模；不因标签“复杂”强制Blender |
| 跨镜衔接 | 原已接受前镜状态与 handoff 优先 | 既有边界/首尾帧职责 | 独立切镜、跳时不机械传末帧；本笔记没有新增跨镜实证 |
| 简单氛围或身份已足的表演 | 原 Director 与 selected profile | required duties 为空且模型允许时可零模型参考 | 零模型参考不免剧情预览/用户认可，不放松身份豁免 |
| 商品广告一致性 | 原批准商品事实和 AdCreativePlan | 现有 product anchor、720p流程、Composition | 本笔记无商品案例，不拿动漫服饰控制冒充产品验证 |
| 宫格多切镜或仅有题材标签 | C02 / C04 | 仅审看与研究拒绝理由 | 分类命中、安装成功、外部评分都不能解除能力阻断 |

字段名称参考 [ReferencePlanningIntent](../../src/ai_video/production/reference_planning_contracts.py#L118)；`transfers` 是现有作者表达约定，不是本笔记新增的 runtime schema。决策记录写明“需要什么/不需要什么/原因”，不规定固定参考数量。

## Bounded Retrieval Procedure

**此规程供现有研究角色按任务使用，不注册网络工具、不装第三方 Skill、不自动执行其中命令。**

1. 先查本地方法、本文与既有研究；把缺口缩成一个问题。没有缺口就记录“已有覆盖”，无需外查。
2. 确需公开检索时，仅用抽象类别词。模板为 `https://goodcase.ai/api/public/cases?category=video&q={term}&take=5&locale=zh-CN`；候选 q 词为 `动作`、`接触`、`角色一致性`、`空间`、`悬疑`、`产品`，发送前对词编码。这些词不是 category 枚举；不上传私有剧本、身份/商品文件或素材。
3. 只对实际返回的 slug 查 `/api/public/cases/{slug}`，确需审证才查 `/{slug}/retests`。模型筛选只是本次返回候选的筛选，不宣称全库语义检索或分页完整。
4. 每个研究任务采用最多8次 GET 的工作上限：最多2次列表、3次详情、3次复测。它不是服务方配额、付费许可或新增Product Gate。400/404记为不适用，429/超时/异常响应本轮停止；不自动重试、换IP或扩大抓取。固定Git文件回读与GoodCase API读取分别记账。
5. 记下实际case_id、作者、原帖、完整URL、获取UTC、上游SHA或“线上快照”、字节hash及hash_basis。把推荐模型与实际复测模型分开；未看媒体标NE，不能用平台分数代替本项目QA。
6. 将必要元数据、自己的转述、本地等价方法及选/拒理由放研究笔记；保留署名。原prompt/媒体不复制进仓库，不执行详情中的安装、模型评测或生成指令。
7. 记录耗时、重复查找和未找到原因。只有多个真实任务证明手工检索成为瓶颈，才另提薄工具；新增运行时goodcase.ai出口仍需明确范围决定，资料公开可读不自动授权工程接线。

静态四卡可按commit/hash核对；此前动态 API、限额响应头和评分属于历史观察。本次没有新调GoodCase API，不用旧数据声称当前服务仍返回相同内容。[接入说明](https://goodcase.ai/connect)、[旧观察与限制](../record_for_agent/2026-11-04-goodcase-integration-architecture-review.md#public-api-and-evidence-limits)

## Research Decision Record

下一真实任务可将下面各项填写到它自己的现有研究/会话记录；这是可读记录格式，不是新增必填schema、Manifest或状态机。

| 内容 | 填写要求 |
| --- | --- |
| task/question | 一个具体缺口；对外仅用公开抽象词 |
| baseline | 原批准意图/已有方法；有媒体时列exact结果身份和失败项 |
| case/source | case_id、source_id、revision、UTC、hash_basis、hash、作者与许可范围 |
| decision | 选为候选、已有覆盖、拒绝或证据不足；说明理由，不写“采纳生效” |
| transfer | 允许迁移的关系、不能迁移的剧情/身份/背景/机位；对应现有字段 |
| reference_need | 为什么需要或省略角色板/空间图/末帧/动作视频/白模；能力限制与替代办法 |
| uncertainty | 未知模型、输入、媒体、权利；哪些变量不可控 |
| effort | 查询次数、实际耗时、重复工作；没有实测则写未评估 |
| next_step | 无动作、补证或提出有界修复；不是submit许可 |

不得把外部JSON放进 `evidence/authoring-input/` 充当prepared artifact；该路径会把满足内容寻址的输入封装成 `user_input`，不能用hash通过来证明来源真实。研究笔记也不得填入 `preview_approval.user_quote`。真正模型素材仍经既有授权、Registry/readiness与实际SHA绑定。[自动封装边界](../../src/ai_video/production/authoring_input.py#L33)

## Quality, Repair And Promotion Boundary

**全部四卡的本项目效果仍是 HYPOTHESIS / NOT_EVALUATED。** 如下一真实任务已有失败，只能由原诊断决定是否提出一项有意义的表达变化；不为本文专建付费A/B，不重做已认可镜头。模型能力、缺证、上传失败和画面失败分开处理。

即梦四型号目前UNQUALIFIED，仅有界qualification；构造diagnostic对象不代表能提交。既有prompt-only质量修复要求production_repair、完整质量拒绝、覆盖全部失败项并保护全部通过项；no-effect恢复走自己的grant与账本，UNKNOWN不自动继续。具体约束只引用原owner，不在这里建立另一套修复算法。[资格与修复](../jimeng-provider.md#bounded-qualification-trial)、[修复源码](../../src/ai_video/production/_qualification_quality_repair.py#L14)

用户独占观感判断，Agent只提供可核事实。单张案例、单次改善、多个文档/Agent意见都不等于通用方法验证；未来按现有distill的独立attempt/受控比较证据与确认要求处理。当前学习评估为no_candidate，不改Skill/Policy/Gate。[学习owner](../../.agents/skills/distill-ai-video-learning/SKILL.md)

## Validation Scope

可验证的是来源文本身份、引用完整、本地方法去重、文档契约以及既有corpus reader对本文件的`advisory_research`分类；不能据此声称实时搜索必命中、案例视频已观看或质量提高。精确检查结果和Harness receipt见[主记录的P0完成项](../record_for_agent/2026-11-04-goodcase-integration-architecture-review.md#p0-implementation-checkpoint)。

[action-file]: https://github.com/LearnPrompt/goodcase-lite/blob/34c716bfc6375ed335a52f78f63450258ed33fe7/skills/generated/action-continuity-choreography/references/cases.md
[grid-file]: https://github.com/LearnPrompt/goodcase-lite/blob/34c716bfc6375ed335a52f78f63450258ed33fe7/skills/generated/storyboard-grid-to-video/references/cases.md
[animation-file]: https://github.com/LearnPrompt/goodcase-lite/blob/34c716bfc6375ed335a52f78f63450258ed33fe7/skills/generated/animation-style-consistency/references/cases.md
[drama-file]: https://github.com/LearnPrompt/goodcase-lite/blob/34c716bfc6375ed335a52f78f63450258ed33fe7/skills/generated/cinematic-drama-scene/references/cases.md
[action-card]: https://github.com/LearnPrompt/goodcase-lite/blob/34c716bfc6375ed335a52f78f63450258ed33fe7/skills/generated/action-continuity-choreography/references/cases.md#L55-L78
[grid-card]: https://github.com/LearnPrompt/goodcase-lite/blob/34c716bfc6375ed335a52f78f63450258ed33fe7/skills/generated/storyboard-grid-to-video/references/cases.md#L9-L16
[animation-card]: https://github.com/LearnPrompt/goodcase-lite/blob/34c716bfc6375ed335a52f78f63450258ed33fe7/skills/generated/animation-style-consistency/references/cases.md#L58-L94
[drama-card]: https://github.com/LearnPrompt/goodcase-lite/blob/34c716bfc6375ed335a52f78f63450258ed33fe7/skills/generated/cinematic-drama-scene/references/cases.md#L64-L72
[lite-license]: https://github.com/LearnPrompt/goodcase-lite/blob/34c716bfc6375ed335a52f78f63450258ed33fe7/README.md#L52-L60
