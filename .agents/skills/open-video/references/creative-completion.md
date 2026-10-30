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

### Directorial Choices

以下用于作创作决定，沿现有coverage、performance和review表达，不新增表单、字段或评分Gate。新创作在授权内主动选择；批准剧本、选定source或局部修复则先守住原事实与目标，不能因方法建议重新编剧情。

**先找作品的表达机制。** 从观众应理解、感受或记住什么出发，决定通过人物选择、关系变化、悬念、生活观察、幽默、动作后果或感官体验来实现。存在实质创作分歧时，比较含义不同的方案，例如等待别人照顾与自己选择停下来；换焦段或增加形容词不算另一种机制。选择足够明确就继续，不要求每镜多案、固定戏剧结构或先建立敌人。

**把人物放进能成立的处境。** 对人物行动，想清楚他此刻要做什么、为何现在做、什么使他改变或坚持、对方看见后怎样回应。阻力可以来自物件、习惯、信息差、关系，也可以没有明显冲突。先给演员一个具体任务，再选能读到该任务的视线、重心、手势或停顿；情绪词可帮助理解，但全程“微笑、呼吸、轻微动作”不能代替应发生的决定。背景不反应、克制、犹豫或静止都可能有动机；不统一加大幅度或让所有人同时表演。

**让空间而非说明承担关系。** 用当前疑点所需的平面图、关键姿态、取景草图或正常速度简易排演，核对人物起点、目标位置、视线、行动路径、接触与结果是否对应。检查画面里可见的替代选择：角色为何不坐旁边空位，为什么绕过近处出口，手到底触到哪个物件？可以用构图、位置或有动机的行为讲清，不能靠Prompt宣布观众忽略矛盾。按实际参考职责核对图片/视频是否暗示了不同的起始状态或动作；白模、身份图、首帧与运动参考并不天然等义，也不默认每镜都需白模。

**由注意力决定镜头。** 决定此刻让观众先看原因、反应、隐瞒的信息还是一个感官细节，再选景别、角度、遮挡、人物走位、焦点和镜头运动。移动机位应改变可见关系、距离或体验，切镜应服务揭示、比较、节奏或空间转换；不先指定“缓推”来填时间。静观、重复和单镜可以成立，按作品目标判断；不要求每镜新事件，也不以更多切镜证明丰富。

**按行动与反应的时机安排节奏。** 看观众何时能识别目标、看清变化、读到反应，以及何处需要期待、停留或释放。声音可提前引导注意、揭示画外事件或让一个动作落地，不默认BGM越满越好。缩短镜头时核对是否剪掉原因或结果；加快播放不能自动修复无事可看的设计。动作多也可能赶、情绪满也可能假，应在正常速度的实际素材中判断。

**把生成原声与后期声音一起设计。** 在现有声音方案中说明对白/旁白是否需要、承担哪项叙事或信息作用；省略配音要有具体内容理由，例如画面与已有对白已表达充分、需要保留沉默或声音细节，不能仅因生成视频带音轨就省略。需要的后期配音与可用的原生对白、动作声、环境声及配乐分别进入既有P4音轨，统一决定时点、音量、淡入淡出与ducking；避免重复台词、遮盖人声或重复强化同一动作。不强制每片加旁白，也不借此改写已批准台词或绕过既有voice route、生成与验收边界。

画外声、旁白或对讲在介绍事件时，先决定画面在同一时刻让观众看见什么：声音报的事要有可核对的画面对应，或有意留白并写明理由；不能让声音讲一套、镜头自顾运动。Agent 无法亲耳试听，配音前先把声线候选（同一句台词、不同声线）交用户试听选定，再进入审看片；盲选声线、临时 TTS 或用 ffmpeg 直接混入的审看片只能标为未验证草稿，正式成片的配音仍须经 Registry 导入与 P4/HyperFrames。

修复原声或替换素材时，逐轨对照原声音方案与新时间线，保留仍有用的后期配音、配乐和拟音；只对重复、冲突或失效部分作有理由的调整。原声恢复不构成整组删除后期声音的依据；最终同时核对原声与后期声音是否实际进入exact成片，听感证据缺失仍明确保留。

按题材选问题：商业片看商品为何此刻进入动作、怎样形成记忆且不暗示无据功效；剧情看角色与观众各知道什么、反应是否有知识依据；动作片看目标、威胁、出口、路径及接触后果是否可读；感官或抒情片看观看/聆听经验是否完整。不要用同一冲突或转折模板替代题材判断。

### Production Feasibility

在选方案时就与制作owner核对：这个镜头决定含义的事件是什么，哪一项执行失败会使它失去意思，目前所选模型/模式、已有素材或合成路径有什么相称证据能完成它。自然表演、多人精确接触、物件状态变化、镜面关系、遮挡和声音时机是不同难点，不能只用“支持参考视频”或“Prompt写清楚了”回答。

按当前风险比较可实现的路线，再确定所需参考或最小实测；以下只是讨论起点，不按题材自动选路：

| Decisive event | Possible route / decisive evidence |
| --- | --- |
| 自然生活对话、细微情绪转变 | 可考察原生视频生成；需要实际反应时机、对视、台词与身体的连续表演证据，姿态正确不足够 |
| 多人物精确碰撞、接触后相互影响 | 比较原生生成、动作参考约束及局部分层合成；先查实际接触、遮挡和运动后果，不能由白模有动作推定真人执行成功 |
| 主角没有镜中倒影、其他倒影仍在 | 比较精确机位、清洁底片/分层合成与生成方案；检查同框对应、镜面几何、遮挡与运动是否可维护，不把遮掉关键反射当成功 |
| 复杂道具交接、连续纸带等物理互动 | 优先验证决定性的接触、支撑、释放或物件状态变化，再决定生成/参考/合成怎样分工；不能用静帧推定连续动作成立 |

把“已有exact媒体支持”“只有间接经验”“还需验证”说清楚即可，不新建能力评分表。对风险最高的关键事件，利用已有素材回放、简单物理排演或授权内最小实测取证；测试应能否定方案，不能只展示最漂亮一帧。参考、机位或生产路线的选择服务于表达，不默认白模、单次生成或更多合成。

Director和制作层共同判断怎样保住创作目标并完成它；可执行分工仍交现有Production Strategy、selected adapter与composition owner。没有可行路线或证据时，明确缺失项与最小验证条件，不以填齐合同宣称可拍，不先扩建工程，也不把建议视为新生成/付费授权。

### Failure Attribution

先问“现方案若被完美执行，是否仍达不到创作目标”，再对照exact输入、实际参考和输出定位偏差。可以有多个原因，证据不足就保留不确定性，不从同一症状直接推断根因。

| Evidence | Likely responsibility / next check |
| --- | --- |
| 完美执行仍无清楚意图、必要表达或所需情绪，或节奏本就不合目标 | Director重审选择、动作、信息顺序与取舍；留白本身不是失败 |
| coverage有核心行动，实际authoring/native省略、弱化或与参考姿态矛盾 | 核对作者交接、参考职责和选定adapter的表达；先区分作者输入缺失与Compiler表达缺陷 |
| 输入/参考表达清楚，输出却缺动作、错对象或破坏连续性 | 生成执行或控制能力问题；记录实际偏差，不以失败次数断言模型必然做不到 |
| 原素材已满足目标，合成后出现裁切、遮罩、字形、时序或音频缺陷 | 对应制作owner修复，并重验完整成片；不靠改剧情掩盖技术问题 |
| 只有文字方案、抽帧、自动分数或未听音轨 | 缺相应观看/聆听证据；不宣布自然表演、节奏或音频已通过 |

修复时保留已经成立的表达和批准目标。增加动作、删人、拆镜、压缩Prompt或换参考都只是待验证的选择；先说明它解决哪个已知偏差、可能损失什么，再在已有授权内取最小相称证据。能力限制、unknown、预算和验收仍由原owner处理。

### Independent Concept Check

制作前给一个独立 read-only context 提供相关原始意图、有效用户反馈及候选 coverage。
先回答是否漏提/偷换目标、观众实际能看到或听到什么、关键不确定表达的素材/能力是否足够，
再看作者的技术理由。Reviewer 引用原话和具体 `objective/open_state/close_state/visible_change`
内容，指出不足；不能仅报分数、模板合规或镜头数。Parent 裁决，明显不足先改方案；
该检查与成片观看分别取证，遵守当前 Agent workflow route（playbook Agent Workflow Operations），不自动启动媒体或额外付费 variants。

遇到关键隐喻、空间因果或反应时机，先让独立者复述人物在做什么、为何改变、哪里困惑，再给作者的设计解释。若对照多案，提供共同brief与可比信息，不预先标注新旧优劣。指出具体观察和替代解读，避免把作者解释后的认同当作首次可读性；文本复核仍不证明实际画面或观众接受。

### What A Concept Check Cannot Approve

An independent concept check reads text; it never sees the film. Its READY verdict cannot authorize paid generation of new
creative work—only the user's approval of the visual preview can. Ask before generating: with the sound removed, does each
shot still show something happening? If the anomaly lives only in narration, redesign the shot before preparing references.

### Advertising

先说明这支片子是产品演示、品牌氛围还是转化广告，再确定它需要的表达。检查商品身份、包装文字与结构、事实/功效来源、画面和文案是否互相支持、品牌记忆与收尾是否成立。转化目标需要可信的行动动机；品牌氛围片不被强制套卖点、购买理由或 CTA。无法核实的产品事实不能编造，生成错字不能冒充真实包装。

### Drama

从当前场景的角色目标、阻力、行动、反应和关系/情绪状态入手，检查片段怎样推进场景。以镜头覆盖表演和信息，不用旁白或漂亮画面掩盖关键行动缺失。按适用范围检查空间轴线、视线、动作承接、角色身份、声音、对白可懂度和节奏。抒情、悬念、静观或开放结尾可以成立；不能强迫每场反转，也不植入品牌/CTA 审美。

### Cut Relationships And Reused Footage

设计与审看相邻镜头时，明确观众凭什么把它们联系起来：空间定位、人物行动、视线、声音、因果或有意的情绪对照。
尤其从宏观环境进入具体事件时，实际画面或声音应提供与该事件有关的线索；仅同属城市、夜景、相似色调或配有同一首音乐，
不能证明叙事联系成立。核对地理、天气、时段和美术差异是否造成无意换场，不能靠导演文字解释或转场特效补足缺失的联系。
允许省略、跨空间蒙太奇和有意跳切；不强制每刀空间连续、匹配剪辑或溶解，但其可感知的联系与信息取舍必须服务原目标。

相近机位、相同景别的接镜尤其容易被看成连续动作，应对照实际出入点的人物姿态、头部朝向、视线、持物与手部状态、
动作阶段和运动速度，以及背景、雨水等仍在运动的细节。原速观看接点前后的完整动作，再用逐帧证据定位跳变；
重点是可感知的动作接续，不要求跨镜细节逐像素一致。
慢速放大、抽帧和播放器零掉帧各自只能证明对应范围，不能替代正常观看中的动作连续性判断，也不把有意义的静止当作失败。
动作突然复位、姿态瞬变或运动骤停即使没有冻结帧，也可能产生卡顿感；必须区分播放故障、源素材动作与剪辑接续问题。

复用已认可素材时，保留批准的叙事与表演，同时重新检查新成片中的实际接点，包括被复用段落的内部切镜。
认可核心事件或单镜，不自动批准每个局部接缝；原问题早已存在、源文件未改、hash 一致或播放流畅均不是放行理由。
复用较早的镜头、变速片名或已合成片段前，在既有逐接缝 observation 中记录源入出点及先后关系、成片入出状态和实际播放速度；对照“切前动作阶段→切后入态→切后下一动作”，不能只确认人物还在、道具还拿着。重点排除姿态复位、重复转头/抬手及未经设计的速度骤变；单段审美认可只覆盖该段，不能继承为接点认可。先由实际前后动作确定剪点，再保留必要显影或尾声，不用溶解、冻结、倒放或无依据变速掩盖已见的动作失败。
把具体观察、影响、保留或修复理由写入既有逐接缝 review；没有相应声画证据保留 `NOT_EVALUATED`，已见连续性失败不得改标通过。
这项审查不授权推翻已批准事件或额外生成；用户限定只分析时，只报告原因和修复范围，不改媒体。

## Review Before Calling It Done

先看实际成片，再对照原目标：画面、动作/表演、剪辑、音频、文字与叙事必须结合观看。抽帧能证实局部错字或遮挡，不能证实动作自然、节奏、音画同步或整片观看；有音轨不等于听过声音。未实际取得的证据明确保留 `NOT_EVALUATED`。AI 评审保持 `explicit_evaluator`，不能填写 `human`、伪造全片原速观看，或把用户沉默当成认可。

创作或实质重剪达到完整候选时，交给一个独立、read-only 的审片 context：提供原始目标/约束、exact 成片身份、可访问的实际媒体与必要参考，先让 reviewer 提出自己的判断，再提供作者解释。不得只传“渲染成功”“tests PASS”或作者总结。其输出须是具体时段、观察、影响和修复建议，不能以总分抵消失败。Reviewer 无法看/听的范围必须明确；没有可用独立复核时如实保留该缺口，不能假装已经审过。遵守当前 Agent workflow route（playbook Agent Workflow Operations）；独立审片不自动增加每个镜头的多轮代码 review。

Parent 对每项问题裁决并说明证据。明确的错字、商品/角色错误、因果断裂、动作破坏或音频问题先修复；审美分歧可回到原意裁决，不能把偏好包装成普遍硬门槛。目标缺失或标准错了就返回创作，而不是不断调字号。有限修复必须保留失败证据、原目标与已满足要求；新媒体走新 identity 和适用 gates。Unknown outcome、授权或预算不足仍按既有规则停止。

## Keep The Complete Review Visible

新创作闭环先运行 `python -m scripts.creative_goal_binding --binding PATH`。
`creative-goal-binding/1` 只含 `schema_version`、`authority=development_only`、
`creative_input/coverage/final_output_contract` 的相对 `path` 与 exact bytes `sha256`，以及
`bindings` 的 `intent_item_id/constraint_ids/unit_ids/requirement_ids`。三文件在封套所在目录内，
不能 symlink/`..` 逃逸。每个 active explicit_user intent 有 constraint 与 requirement；
global 可以零专属 unit，beat-specific 覆盖所有引用该 constraint 的既有 units。
此检查只证明已登记关系自洽，不证明提取完整、scope 分类正确或内容表达充分。

开发侧复核使用现有 `scripts.visual_quality_report prepare --contract PATH --goal-binding PATH
--timeline PATH --render-report PATH`，timeline 必须是本次 canonical `ResolvedTimeline`，
render report 必须绑定本次 HyperFrames exact MP4；不得以 Provider 首尾帧绑定或原素材全长代替剪辑检查。
同时绑定本片实际视觉方向、`--content-kind`、MP4、output 和 timestamps。新 `/4` packet 在
`creative/` 保存预检后的四份原始文件 bytes；reopen/check 只读此封存 snapshot。外部原文件
移走仍可重开，snapshot 被改则拒绝并清除旧派生 PASS。旧 `/1`、`/2` 保留原范围及 `goal_chain=not_evaluated`；历史 `/3` 已有目标链可重开，但不证明新接缝检查完成。
Production 则由当前 QA、Review / Repair 和 Final Acceptance 原入口完成，不以开发报告替换。

当前新完整复核使用 `/4` packet，在原 creative snapshot 外封存 timeline、render report 和逐接缝清单，
包括没有显式 transition 标签的实际切镜。逐接缝核对采用入出点、重复动作/停顿、对白/笑声/音效叠加或截断，
画面与声音分别记录，必须有正常速度实际听看证据；抽帧、ASR、波形和播放结束不能代签聆听。
每刀可以保留，但必须说明理由；`edit_decision=trim` 表示尚需剪辑，会阻断通过，修复后对新 exact 成片重新检查。
缺接缝记录、未听声音或成片/时间线变动均不得通过；旧 `/2`、`/3` 仍可重开，其完整接缝范围保留
`NOT_EVALUATED`，不能靠改回旧 packet 版本绕过。报告只是 development review，不授予 Production acceptance。

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

### Hotpatch Action And Reference Mismatch

护腰贴历史coverage写“想坐又停”，actual native却写“前倾后站稳”，QA只具体检查纸卷滑动和对视；结构通过并未保护核心行动。后续S01R已明确试坐、腾座、落座，仍生成已坐起身再坐回、纸带断裂；参考图又把女子放在空座前。两例分别提示交接损失和调度/生成混合风险，不能统称“动作没写清”或“全是模型问题”。见[原始证据研究](../../../../docs/record_for_agent/2026-10-21-director-capability-study.md#hotpatch-comparison)。研究新案只完成纸面复核，尚未证明真实观感改善，不将其7秒、纸卷或具体走位变成通用配方。

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

## Method References

上述导演判断参考并改写了Serge Shima的Visual Skills [dramaturgy](https://github.com/smixs/visual-skills/blob/92be33a5a73325fb3d8e0c73b22744b114e2a90e/video/references/dramaturgy.md)（[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)），以及wangzhang-wu的Cinematic Director [blocking-and-staging](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/references/blocking-and-staging.md)与[failure-modes](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/references/failure-modes.md)（[MIT](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/LICENSE)）。仅迁移适用原理；作者的风格偏好、数量配方、模型技巧和成功率经验不构成本项目规则或能力证明。取舍及反例详见上述研究。
