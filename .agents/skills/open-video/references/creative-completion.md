# Creative Completion Practice

## Purpose And Authority

本实践把导演判断前置，并把同一目标保持到交付。适用于广告、电视剧及对应片段的创作、重剪、图形/字幕/配乐设计、修复；素材复用与短片不豁免。纯复制已经验收的 exact bytes 不重新创作，沿原验收和交付 owner 核验即可。

它只约束 Agent 工作，不提供新 runtime、自动审美评分、Manifest、第二 QA 或 delivery 状态。原 Director v4 inventory、Story / Scene / Shot、QA-owned `FinalOutputContract`、Review / Repair 与 `ProductionStateCommitter` 保持原权威。Agent 能违反操作流程；本文件及报告工具不具备拦截任意聊天链接或保证审美的能力。

## Before Making The Film

1. **承接相关原始意图。** 在现有 brief 保存当轮请求、仍有效的前轮要求、作品反馈及明确范围变更的可定位原话和来源；共同进入 exact `request.creative_input_evidence` 与 v4 intent inventory。缺原文时注明来源缺口，不凭记忆补引文。只有用户明确取消、替换或收窄才退役要求；素材不足、避险或省费用不是取消依据。
2. **明确观众体验。** 保留用户原话与硬要求，再说明 Agent 补齐的创作选择：观众看完应理解什么、感受到什么、记住什么。把“输出六秒 MP4”等技术规格与作品目的分开；不能因为手里只有某段素材，把用户的广告或剧情目标改成素材测试。
3. **先设计再选素材。** 使用 Director v4 的 intent groups 和 ordered coverage。每个段落回答它承担什么、通过哪项可见/可听信息实现、为什么接在这里。对已有素材做同样的适配判断；不适合的素材不因省事而保留。留白、静止、重复、长镜头、无对白都可成立，必须有服务具体内容的理由，不按镜头数或机械“信息增量”打分。
4. **写下否决理由。** 先检查当前方案是否已知会失败，例如商品主视觉有错字、表演没有完成关键行动、反应镜头时机错误、音乐覆盖对白。发现这些问题时修改方案或选材，不先出片再用“preview”解释。若确需展示失败证据，使用下方诊断展示边界。
5. **保留完整要求。** 将可接受结果与不可接受结果翻译到原 QA / FinalOutputContract owner，分别声明 proof。用户固定要求、叙事结果、质量底线与导演偏好不得混成一条。每项要求应能说明观察对象与判断依据；最终交付检查不能只选容易通过的一部分。

### Independent Concept Check

制作前给一个独立 read-only context 提供相关原始意图、有效用户反馈及候选 coverage。
先回答是否漏提/偷换目标、观众实际能看到或听到什么、关键不确定表达的素材/能力是否足够，
再看作者的技术理由。Reviewer 引用原话和具体 `objective/open_state/close_state/visible_change`
内容，指出不足；不能仅报分数、模板合规或镜头数。Parent 裁决，明显不足先改方案；
该检查与成片观看分别取证，遵守当前 SUBAGENTS route，不自动启动媒体或额外付费 variants。

### Advertising

先说明这支片子是产品演示、品牌氛围还是转化广告，再确定它需要的表达。检查商品身份、包装文字与结构、事实/功效来源、画面和文案是否互相支持、品牌记忆与收尾是否成立。转化目标需要可信的行动动机；品牌氛围片不被强制套卖点、购买理由或 CTA。无法核实的产品事实不能编造，生成错字不能冒充真实包装。

### Drama

从当前场景的角色目标、阻力、行动、反应和关系/情绪状态入手，检查片段怎样推进场景。以镜头覆盖表演和信息，不用旁白或漂亮画面掩盖关键行动缺失。按适用范围检查空间轴线、视线、动作承接、角色身份、声音、对白可懂度和节奏。抒情、悬念、静观或开放结尾可以成立；不能强迫每场反转，也不植入品牌/CTA 审美。

## Review Before Calling It Done

先看实际成片，再对照原目标：画面、动作/表演、剪辑、音频、文字与叙事必须结合观看。抽帧能证实局部错字或遮挡，不能证实动作自然、节奏、音画同步或整片观看；有音轨不等于听过声音。未实际取得的证据明确保留 `NOT_EVALUATED`。AI 评审保持 `explicit_evaluator`，不能填写 `human`、伪造全片原速观看，或把用户沉默当成认可。

创作或实质重剪达到完整候选时，交给一个独立、read-only 的审片 context：提供原始目标/约束、exact 成片身份、可访问的实际媒体与必要参考，先让 reviewer 提出自己的判断，再提供作者解释。不得只传“渲染成功”“tests PASS”或作者总结。其输出须是具体时段、观察、影响和修复建议，不能以总分抵消失败。Reviewer 无法看/听的范围必须明确；没有可用独立复核时如实保留该缺口，不能假装已经审过。遵守当前 SUBAGENTS route；独立审片不自动增加每个镜头的多轮代码 review。

Parent 对每项问题裁决并说明证据。明确的错字、商品/角色错误、因果断裂、动作破坏或音频问题先修复；审美分歧可回到原意裁决，不能把偏好包装成普遍硬门槛。目标缺失或标准错了就返回创作，而不是不断调字号。有限修复必须保留失败证据、原目标与已满足要求；新媒体走新 identity 和适用 gates。Unknown outcome、授权或预算不足仍按既有规则停止。

## Keep The Complete Review Visible

新创作闭环先运行 `python -m scripts.creative_goal_binding --binding PATH`。
`creative-goal-binding/1` 只含 `schema_version`、`authority=development_only`、
`creative_input/coverage/final_output_contract` 的相对 `path` 与 exact bytes `sha256`，以及
`bindings` 的 `intent_item_id/constraint_ids/unit_ids/requirement_ids`。三文件在封套所在目录内，
不能 symlink/`..` 逃逸。每个 active explicit_user intent 有 constraint 与 requirement；
global 可以零专属 unit，beat-specific 覆盖所有引用该 constraint 的既有 units。
此检查只证明已登记关系自洽，不证明提取完整、scope 分类正确或内容表达充分。

开发侧复核使用现有 `scripts.visual_quality_report prepare --contract PATH --goal-binding PATH`，
并绑定本片实际视觉方向、`--content-kind`、MP4、output 和 timestamps。新 `/3` packet 在
`creative/` 保存预检后的四份原始文件 bytes；reopen/check 只读此封存 snapshot。外部原文件
移走仍可重开，snapshot 被改则拒绝并清除旧派生 PASS。旧 `/1`、`/2` 与 positional API 保留
原范围，明确 `goal_chain=not_evaluated`，不能据此声称新目标链已核对。
Production 则由当前 QA、Review / Repair 和 Final Acceptance 原入口完成，不以开发报告替换。

首次完整合同应在执行前按原用户目标建立；不得看完失败结果后重写要求求 PASS。对旧失败做回溯复核时，必须说明这是补建的诊断标准，不虚称早已封存或具有历史验收权威。重新编码或修改成片后旧 hash/报告无效，需要新证据。

`full_contract` 只表示工具保留了 caller 给出的完整合同，不能证明合同真的穷尽用户目标。Parent 仍需核对原始 brief → intent/coverage → requirements → findings；不允许以省略未满足要求的方式完成。

JSON/HTML 分开显示原始回答、原 adjudicator 的有效逐项结果和全局 evidence gaps；
不合格的原始 PASS 不能当作已证明。交付摘要列出 exact identity、复核范围、FAIL/NOT_EVALUATED
及下一动作，并引用当前 creative input。工具不会解释用户是否撤回拒绝，Parent 必须核对来源，
在交付说明中披露未决反馈。新反馈进入新 authoring revision；旧片、旧合同和旧报告不倒填或改写。

## Delivery And Diagnostic Sharing

作品候选、失败诊断展示与正式验收保持诚实边界。可以把未获用户最终审美认可的候选交给用户观看，并清楚说明已检查的范围；不能把已发现的基础质量缺陷留给用户首次发现。完整正式验收依原 proof 要求完成，用户反馈不能由模型代签。

若共享已知失败素材用于定位或征求特定反馈，必须同时指出失败项、相关时段、任务仍未完成及下一修复动作；不能只附技术 PASS、receipt 或“预览”名称就结束任务。仅当用户明确要求查看当前失败版本或真实 blocker 阻止继续时，该展示才可作为当前停点；它不恢复作品完成状态。

有效 FAIL 先修对应内容/媒体；缺可取得证据先补证，新 exact artifact 完整重验。基础检查已完成、
只剩用户整体偏好或适用 human acceptance 时可展示候选并说明剩余判断。已知创作失败不能仅
换称 candidate 后结束制作任务。停止需指出真实 capability/authorization/unknown outcome/budget
blocker 和恢复出片的最小条件；完整开发评审也不代签 Production acceptance。

## Counterexample

青颜六秒样片 `f8f775e4357d4ec8030142f93e8f07d2631d370884e4717ff97f35d42353c6ce` 已技术渲染成功，但商品包装有可见生成文字问题，parent 事后才按导演标准指出表达不足。应在选材/方案阶段否决已知问题，或在交付前明确失败并继续修复；“复用现有样例”“只有六秒”“未签 Final Acceptance”均不能替代这一步。

反例说明的是目标保留与执行纪律缺口，不推出“所有六秒片/重复机位/黑底收尾都失败”。代码回归证明完整合同中的 FAIL 与缺项不能被视觉 PASS 掩盖；不能证明机器已经会导演或每部作品必然好看。

## Paper Cases And Evidence Limits

### Qingyan Packaging And Advertising

青颜后续 10 秒片 `25cd328bcbf395660a0e213d0c541c1c68bd49dc6304eedb936b912aeefa76a6`
用真实商品照片减少包装错字，但用户明确拒绝“全程一张图”，见
[原始反馈记录](../../../../docs/record_for_agent/2026-09-27-creative-goal-preservation-spec.md#user-feedback)。
包装文字正确只解决局部问题，不证明广告表达成立。下一方案保留真实包装展示段，并从有效
brief 设计其余使用/情境/信息表达；不能编造功效、凭空将演示目标改成品牌露出，或再交同一单图
方案结束任务。Reviewer 应指出观众可见表达缺口及与有效反馈的关系，不凭“静态”一词否决
所有品牌片。用户明确同意的静物氛围片另按其实际目标判断。

### A Single Take With Dramatic Development

固定中景：甲握住信件，想交给乙；伸手后迟疑，乙不接，视线落在信上；甲将信放在两人之间，
乙最终向前一步。`open_state` 是回避交流，`close_state` 是接受接近，`visible_change` 包含
递物、迟疑、拒接、放下及距离变化；呼吸和纸张声支持沉默中的关系发展。单一固定镜位可以
覆盖这条行动与反应链，无需用镜头数量证明充分。Reviewer 核对动作能否在画面内读懂、
反应是否改变关系；立绘加字幕没有这些表演证据，不能冒充本方案已实现。

### Preserve The Goal When Capability Is Missing

若当前能力无法可信表现商品接触皮肤的动作，保留“观众看到使用过程”的 requirement 和缺口。
先检查现有已授权真实示范素材是否可用；确需新增素材或范围变更时，给用户具体选项：提供真实
示范、批准具备能力的有限新尝试，或明确同意改为无需使用演示的品牌片。未获变更不能悄悄
删除动作要求，也不能先制作已知不满足目标的片子。Unknown outcome 与既有预算/gates 仍优先。

这些案例只供独立内容判断，不证明实际表演、声音、广告效果或用户满意。交付分别说明
结构完整性、概念判断、实际观看和用户意见；工程测试不能替代后两项。
