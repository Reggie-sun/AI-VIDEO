# Shot Performance And Prompt Fidelity Repair Spec

Date: 2026-10-21

Status: Draft — spec-only，尚未授权实施

## Goal And Authorization

用户要求为本轮《界蚀》生成不自然的问题编写修复规格。本轮交付限本文及既有记录的关联更新，不修改实现、Skill、Policy、Gate、Production输入或媒体，不新增Provider调用，不自动进入implementation plan。

目标是修复“作者表演意图 → 实际模型输入 → 原片观看裁决”之间的脱节：最终prompt的表达声明必须有真实来源，人物行为与全场美术须得到具体审查，工程接通不能冒充自然表演。共享能力面向不同项目、人数及镜头，《界蚀》仅作为已知失败案例。

## Evidence And Diagnosis

事实依据为[双模型对照及模块定位记录](../../record_for_agent/2026-10-21-jieshi-seedance-20-fast-comparison.md#human-feedback-and-module-diagnosis)、actual resolved requests、当前源码和[既有表演模块记录](../../record_for_agent/2026-10-20-character-performance-control.md)。

| Finding | Confirmed Evidence | Limit |
| --- | --- | --- |
| 最终文字与覆盖声明来源不同 | Seedance普通recipe分支先生成完整prose，再以 authored binding替换正文，却沿用原 `expressed_control_paths`；`generation_recipe.expression_errors`会跳过已声明路径的未表达检查。两臂实际均为compiler/2、同一447字正文。 | 已确认源码路径；尚未运行专门reproducer，未证明该缺口单独造成画面僵硬。 |
| 作者方案过多锁定姿态 | 已封存作者输入包含“不转头”“不移动头身”等限制；七人的细分表演在最终正文主要缩成日常状态、错开呼吸/眨眼。 | 是否属于原文硬约束须逐条追溯；不能直接全部删除，影响大小也未经隔离验证。 |
| 美术审查过于宽松 | 首帧曾被Agent描述为全场统一CG，用户随后认为整体仍很不自然；参考覆盖检查明确不拥有审美判断。 | 不能从参考SHA、人数保持或局部主角质感推断全场统一，也不能直接归因于模型内部。 |
| 审片与汇报失焦 | 两臂表演和完整画风均为NOT_EVALUATED，用户明确给出负面观感；Parent早先偏重构图/身份稳定。 | Gate没有签发自然表演PASS，不能将问题误写成已激活不合格成片的故障。 |

2.0 exact MP4 SHA为 `132c5ef918e5ed140292a30982a7ffeb6a6509603e7fa1d9c0a641c2c3fffc38`，已因窗内手影关闭。Fast为 `4e7120457f4f6b58dc8b25b8b1bbd095da9c99094540a0aa78305448d5c170ae`，已生成但停于validate/EVIDENCE_GAP；后段手影不自动构成已证明的0–3秒窗内FAIL。原始裁决、调用计数、费用状态及媒体保持历史事实。

## Scope And Ownership

| Concern | Existing Owner | Intended Change |
| --- | --- | --- |
| 最终Seedance文字及其覆盖证明 | `production/seedance_native_prompt.py`、`seedance.py`、现有compiler contract/profile选择 | 修复被替换文本的控制路径被继续信任的问题。 |
| 表达义务、QA片段与路径 | `production/generation_recipe.py`、`requirement_semantics.py`、`generation_input_control.py` | 复用现有表达体系，核验最终正文中的选定片段及其明确职责；仅在必要边界做最小扩展。 |
| 人物意图及预检报告 | `production/performance_direction.py`、`performance_authoring.py`、`video_reference_controls.py` | 保持逐人物意图owner；区分填写、最终文字覆盖和实际表演，给出具体缺口。 |
| 表演与参考的作者审查 | [现有Canvas workflow](../../canvas-production-harness.md#character-performance-authoring)、`seedance-authoring`的既有authoring concern | 区分叙事保护条件与过度冻结；核对最终输入，而非只看结构化参数。 |
| 画风绑定与审美 | `canvas_visual_style.py`、[当前输入及画风流程](../../canvas-production-harness.md#current-inputs) | 保持确定性覆盖与Agent视觉审查的边界，纠正无依据的全场统一声明。 |
| 原片观察、STOP和正式状态 | 既有project-local `video-analysis`、generation evaluation、`ProductionStateCommitter` | 沿既有入口观察完整结果，不新增验收状态或绕过原Gate。 |

上述为责任边界，不要求每个文件都修改。不得另建导演执行器、表演时间线、骨骼/FACS控制器、NLP语义评分器、自动人物状态库、第二QA账本或Provider fallback。不得把本案例的人名、人数、车厢、抬手或倒影写成共享代码特例。

## Contract A: Final Native Prompt Fidelity

### Single Final Text

1. `ProviderNativePrompt.prompt_text`及其SHA是文字表达检查的唯一正文。最终request、paid preview与实际POST必须消费相同正文；binding不得暗中追加自动prose、整段acting block、内部枚举或完整序列化contract。
2. 已选作者原文精确绑定的语义保留。需要调整文本时回到既有author/revise和source revision，不由编译器截断、补写或重解释。500字等创作建议不是新的硬上限或自动删改依据。
3. 自动prose保留原文时，其确定性表达声明仍归原compiler。当正文被替换，自动prose的文字指导路径不得传给最终binding当作证明；两段文字部分重合也不能整体继承。

### Expression Evidence

1. model、输出分辨率/画幅/时长、音频开关、seed、reference role/bytes和已验证continuity等真实原生或结构控制，继续由现有request/binder/compiler owner验证，不要求写入自然语言。
2. 表情、目光、身体、呼吸、触发与阶段属于文字指导。复用selected QA的 `RequirementExpression.intent_paths`、`native_text`及source/intent绑定，指向最终正文的非空精简片段。caller自报path、旧长文片段、笼统的“自然一些”或字符数达标不构成表达证明。
3. 新authoring binding必须能逐一追溯当前可见人物及其必需beat的文字职责。整个 `performance_intent` 祖先路径不能凭一个通用短句豁免全部人物/阶段；片段可共同表达多个相关字段，但必须明确覆盖哪些当前义务。
4. 优先复用现有表达对象。若现有多path/多fragment元组无法无歧义表达对应关系，只允许在现有binding/表达owner内增加最小、可选、版本化的path-to-fragment映射；源仍是selected QA与canonical intent，不新增另一份表演意图或审批ledger。具体字段shape在实施计划中冻结并验证旧序列化兼容。
5. 所有映射核验 exact bound request、当前intent/QA身份、人物/beat是否存在，以及引用片段是否在最终正文中。不得用宽泛父路径覆盖未列出的子义务；不得通过减少人物、标记offscreen、删除原required finding或改成diagnostic来补齐覆盖。
6. 精简的等义表达允许由Agent在authoring时明确编写并核对来源。runtime验证片段和绑定，不自行判断自然语言等义性；纯词面匹配不能证明片段真实表达了某种心理或动作，也不能识别所有“正确句子后又加相反句子”的矛盾。后者必须由作者语义审查拒绝，不能伪装成NLP检查已通过。

缺失、陈旧、越界或不完整映射须在prepare/compile阶段以现有 `PROMPT_EXPRESSION_UNSUPPORTED` / typed input failure返回具体requirement/path；不得进入start、permit或POST。报告必须展示实际最终正文、缺失义务和被拒绝的覆盖来源，不用新error体系或raw traceback。

### Version And Replay

新普通authored-binding契约使用独立的新compiler版本；当前v3已属于preserved-source，不能占用或改写。实施前核对现有注册表并冻结新版本、profile/stack/compiler hash与fresh routing。

- v1/v2/v3既有immutable request、hash、effect identity、历史诊断和receipt不迁移、不重写。已有attempt的重开、exact recompile与合法resume按其已封存compiler契约执行。
- 新建普通authored binding必须选择新契约；不得退回旧v2来绕过覆盖检查。自动prose未被替换的既有路径不因本修复被误拒绝。
- `source_preservation=true`及 `preserved_source_expression` 的现有逐字保留约束继续独立有效，不借新普通binding放宽，也不将其整块逐字要求强加给普通精简正文。
- 检查voice/continuity等对compiler version的现有allowlist与exact recompile调用方；维持原能力或明确typed拒绝，禁止静音降级、隐式换route或复用旧permit。

## Contract B: Performance Authoring

表演方案由Agent对当前Shot显式编写；validator保留字段/身份/阶段检查，不自动生成表演。

1. 分清用户明确约束、已批准叙事事实、导演选择和旧repair margin。保留身份、道具、视线、剧情与已满足状态，不把“保留构图/坐姿”扩张为未经要求的全身锁死。
2. 主动作必须具有可读的动机及阶段关系。按当前景别检查面部、视线、呼吸、身体平衡与主动作的联系；不强制每镜都转头、换重心或增加动作，也不新增原剧情没有的事件。
3. 背景人物有各自符合场景的日常状态。“不参与异常反应”不能直接等同于全员冻结；也不能用所有人一起眨眼、统一摆动来制造假自然。真实遮挡及不可辨认的微表演要说明限制。
4. `subtle`、`none`、`throughout`是作者选择，不自动判错；有剧情来源的静止/僵硬可保留。审查的是本镜目标是否被表达，而非关键词黑名单或动作数量。
5. author/revise后核对 canonical directions → 选定QA表达义务 → 最终native正文的差异，确认精简没有丢失必要动机、反应、人物区别和终态。发现覆盖不足时在输入层解决，不退回塞满模板长文。

本案例保留左手从膝上抬起、右手唯一手机、对应空座、广播、人物身份及原采用要求。不能为“自然”偷换手、增加对白、改视线对象、强行运镜，或发明原片3秒内必须完成全部动作的新deadline。

## Contract C: Reference And Style Review

全镜风格审查必须实际查看本次exact参考：主要人物、背景人物、头身比例、肤质/发丝/衣物材质与环境光照是否协调，是否仍符合用户选定方向及现代设定。

- 给出可观察的局部证据和未确定项；不能只因主角像CG、人数正确、图已传入或coverage=COMPLETE就声称全场统一。
- 区分实际不符合、证据不足和风格范围例外。合法混合参考沿现有scope声明；不能用 `identity_layout_only` 掩盖whole-shot目标未实现。
- 参考图变化沿Registry/authoring/review失效与重新绑定的现有owner，不直接改历史receipt或让旧图继续影响新输入。
- `canvas_visual_style`继续只证明声明、身份、范围和实际引用；`aesthetic_acceptance`不从这些机械结果自动变为PASS。没有自动审美评分，也不因本修复默认增加白模、参考图数量或模型调用。

## Contract D: Exact Media Review And Reporting

沿现有Per-Shot Gate，对exact MP4显式调用project-local `video-analysis`，逐项裁决。表演自然度还必须有正常速度观看；广播、反应时机和声音语义必须有可靠的同bytes声画观察。接触表、参数或抽样截图不能独自证明全部自然表演。

审查至少回答：动作是否由可见反应带出、身体与手是否协调、目光/面部是否有可信状态、背景是否有生活状态、全场美术是否统一、镜面异常是否成立、原声音义与采用窗是否满足原要求。说明证据时间/帧、遮挡和缺证，不发明微动作，也不把背景安静直接判成冻结。

输出同时保留“基础连续性”“表演/观感”“完整剧情与声音”结论，前者不能代签后两者。原QA已有表演/风格条目时优先复用并细化观察说明；不另建总分，也不为本修复改动历史16项raw/38项FinalOutput的裁决。

FAIL或NOT_EVALUATED停止推进；证据不足先同bytes补证，不自动重生成。用户自然度负反馈作为真实审片事实记录，正式HUMAN receipt仍走既有受信owner。Provider完成、工程测试或静态表达通过不构成activation、P6或Final Acceptance。

## Acceptance And Verification

### Deterministic Engineering Evidence

优先在现有Seedance/compiler/performance/input-control测试中补最小回归，经标准Production author/load/prepare/compile或execution seam验证；不以裸解析数据旁路造证，不重开真实项目巨量历史来测试一个纯编译条件。

| ID | Case | Required Result |
| --- | --- | --- |
| E1 | 自动长文完整，最终binding删除某人物必需反应/片段 | 返回具体缺失路径；start/Manifest/permit/Provider effect均为零。 |
| E2 | 精简正文包含所有当前必需的已选片段及映射 | 编译通过，正文逐字不变；不要求包含整个 `render_performance_direction` block。 |
| E3 | 换入另一正文却携带旧覆盖路径，或仅用父路径/通用句声称全员覆盖 | 拒绝不真实或不完整的覆盖；不能沿用被替换长文的声明。 |
| E4 | 片段存在，但request/QA/人物/beat绑定错误或已陈旧 | typed拒绝，不能通过copy/reseal制造新authority。 |
| E5 | 删除或替换必需片段为相反动作 | 缺片段的确定性检查拒绝；正反表述同时存在的语义矛盾由Agent审查拒绝，不宣称程序能通用识别。 |
| E6 | 普通精简binding、无binding自动prose、preserved-source分别进入正确契约 | 新鲜普通binding使用新版本；其余路径不被误用或隐式降级。 |
| E7 | 固定v1/v2/v3请求重开、重编译、已知结果恢复 | 旧bytes/hash/effect identity和历史计数不变，不新增Provider effect；旧版本不能用于fresh绕过。 |
| E8 | native audio、output、reference role/bytes、voice/continuity等边界 | 原成功/拒绝语义保持，无静音、换参考、换route或fallback。 |
| E9 | 至少两种不同cast/景别，含visible/offscreen与不同beat组合 | 共享义务校验成立，无《界蚀》专用分支；合法遮挡、静止和细微表演不被一概拒绝。 |
| E10 | preflight/prepare报告与最终request对照 | 字段完整、最终文字覆盖、QA映射、实际质量分别报告；不把任一输入状态投影成表演PASS。 |

候选用例owner为 `tests/test_production_seedance_mixed_reference.py`、`test_seedance_source_prompt.py`、`test_performance_direction.py`、`test_generation_input_control.py`及既有execution guards；实际选测按修改范围冻结，不默认整文件/整组反复执行。共享contract/profile/version/恢复语义修改需要适用的边界验证，独立审查按当前Risk Gate决定，不由spec自增review轮数。

### Media Evidence

工程修复通过不等于自然度修复完成。实施获授权且所需输入/预算/状态可执行后，先进行最多一条代表性短镜头、一次POST、零重抽的有界试片；模型/参数/参考、改变变量、历史消费及比较对象须在执行前封存。这是后续最小验证设计，不是本spec授予的新调用许可。

使用原始失败片作可追溯比较：自然度必须在正常速度下有可观察改善，原已满足的身份、道具、空间、摄影、动作、声音和叙事条件不能退化。分别报告改善、退化、未证实，不把单样本胜出推广为模型通用能力。新增试片仍需完成全部适用raw Gate；最终trim/mix/composition另取exact成片证据。

按当前项目先交片审片规则，先完成必要局部检查并交真实试片。用户明确认可效果后再执行适用完整工程验证及commit/push；未认可、存在缺证或阻断时报告实际状态，不提前扩跑整组，也不降低质量要求。完整验证若适用，沿Harness的exact snapshot/range与fresh receipt，不以本文或focused PASS替代。

## Non Goals And Completion

本spec不处理约350.5秒提交前历史读取延迟，不扩建缓存或统一控制层，不调整下载、凭据、预算、permit、unknown恢复与发布权限，不更换Provider/renderer，不制作下一镜、不改旧QA结果。另行性能修复不能与本轮视觉改善混作同一个实验变量。

完成修复须分别列明：输入/覆盖代码缺口是否关闭、跨项目及兼容性验证是否成立、真实自然度是否改善、完整Shot/成片是否验收。只有前两项时标注工程修复完成、媒体质量未验证；不能宣称《界蚀》已自然或可交付。authoring/workflow/矩阵细节仅在获实施授权后同步既有owner，不将本draft直接采纳为Skill/Policy/Gate。

本轮spec交付的definition of done：问题与证据可追溯、owner明确、确定性与感知验收分离、兼容/失败边界明确、无新执行授权、Parent自审和文档路径检查完成。实现、测试、真实媒体与publication均不因写出本文而成立。
