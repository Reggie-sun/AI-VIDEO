# Lost Frames — Open-Source Naming Skill Research

## Scope and Evidence

本研究只评估命名方法、其本地参考材料、代码依赖与许可文字，为《失帧》命名审查提供方法建议；不生成或批准《失帧》新名称，不修改 Canon、角色名、媒体或 Skill，不安装、不运行上游脚本。上游内容来自 GitHub 官方连接器在 2026-10-27 读取的固定 commit；下文将仓库自身的规则作为“该 Skill 的设计”，不把作者未给来源的语言学、心理学或品牌起源说法冒充已独立验证的研究事实。工作区只写入本报告。

| Repository snapshot | 本次范围 | Fixed commit |
|---|---|---|
| [glacierphonk/naming](https://github.com/glacierphonk/naming/tree/e7af8a5d014a330ead84421274178e36e72ecd5f) | 完整命名 Skill、其直接引用的参考文件、语言索引与指南、命名 brief、可用性脚本、README、CONTRIBUTING、根许可证 | e7af8a5d014a330ead84421274178e36e72ecd5f（2026-04-19） |
| [danjdewhurst/story-skills](https://github.com/danjdewhurst/story-skills/tree/57121ee512c6d4218a285c6991193347944f31b0) | 仅 skills/worldbuilding 子目录，以及它明确要求读取的 story-maintenance/references/conventions.md 和运行时包元数据；不审查整个 story-skills 仓库 | 57121ee512c6d4218a285c6991193347944f31b0（2026-10-20） |
| [kunhai-88/character-naming-author-skill](https://github.com/kunhai-88/character-naming-author-skill/tree/84774f7aa31ddd96afb27146ac12f7b95fc38bce) | 中文角色命名 Skill、全部七份参考、四个 Skill 脚本、依赖清单、README、快速示例、benchmarks、根许可证及维护/测试文件清单 | 84774f7aa31ddd96afb27146ac12f7b95fc38bce（2026-07-16） |

完整的目标文件和 Git blob SHA 清单见末尾。GitHub API 返回 commit 与 blob SHA；这里没有另行下载后计算 SHA-256，也没有检查这些仓库在上述版本之后的更新。character-naming 中的测试、基准与打包/验证脚本只作仓库库存记录，没有运行；story-skills 仓库其他 Skills、CLI 实现和示例世界也不在本次审计范围内。已有项目写作能力只核对本地 [drama-authoring/SKILL.md](../../.agents/skills/drama-authoring/SKILL.md) 与 [Story Development](../../.agents/skills/drama-authoring/references/story-development.md)，没有修改它们。

## Comparative Assessment

| Skill | 原始用途 | 对《失帧》最可复用的方法 | 边界 |
|---|---|---|---|
| glacierphonk/naming | 产品、品牌、软件项目命名 | 先建立命名 brief；先找概念领域/隐喻，再找字词；用反模式过滤，并给候选写清来源故事 | 主要为英文商业品牌设计；硬性域名/平台可用性流程、30–50 个候选与权重评分不适合本轮作品术语；中文指南缺失 |
| story-skills/worldbuilding | 故事世界元素的结构化创作和交叉引用 | 为一个文化或机构制定稳定而有限的命名语法；根据使用者、制度、历史、禁忌与关系区分称呼；清点与既有词汇的碰撞 | 所谓命名语言是架空创作模板，不是现实民俗或语言学资料；Story CLI、YAML schema 和项目目录不是 AI-VIDEO 的契约 |
| character-naming-author-skill | 中文影视、短剧、小说人物姓名 | 不只评估字义；按人物出生/取名现场、关系称呼、对白听感与全剧声音差异审查；盲化解释以避免替弱名字辩护 | 专攻人物姓名而非能力、现象、组织术语；自动脚本只是机械提示，不是文学判断，也不覆盖方言/演员声音 |

总的适配度：中文人物姓名审查以 character-naming 为首要参考；组织、能力、异常名词的内部来源和称呼系统，可以有界借用 worldbuilding 的“每种制度有一致但不机械的命名规则”；naming 的“隐喻先于近义词”和反模板思路可作为辅助手段。三套 Skill 都不应该原样安装或把其工具流程并入 AI-VIDEO。

## Findings: glacierphonk/naming

[SKILL.md](https://github.com/glacierphonk/naming/blob/e7af8a5d014a330ead84421274178e36e72ecd5f/SKILL.md) 的七步是：命名 brief → 探索隐喻领域 → 内部产生候选 → 反模式过滤 → 竞争与平台可用性检查 → 加权评估 → 只向用户展示 3–5 个获选项及来源故事。核心主张是名字要像“被压缩的故事”而非分类标签；候选要来自具象领域，不应靠近义词替换或装饰性拼字。它推荐先用六个问题思考物理世界、自然、机器、职业、极端版本和安静版本中的类比，再画出 2–3 个概念领域；候选层才考虑实词、组合、变词、外语和声音优先等不同生成路线。[Metaphor Mapping](https://github.com/glacierphonk/naming/blob/e7af8a5d014a330ead84421274178e36e72ecd5f/metaphor-mapping.md) · [Naming Principles](https://github.com/glacierphonk/naming/blob/e7af8a5d014a330ead84421274178e36e72ecd5f/principles.md)

**对《失帧》的价值。** 这能帮助创作者避免把能力和怪异直接命名成它们的功能说明，也能要求候选回到世界里的具体事件、材料、行动或被命名者的处境。适用方式是：在机制已经由剧情确定后，先追问“谁会需要给它命名、他见过什么、他用什么词理解它”，再围绕两个至三个有出处的概念领域找词；不能从名称反推或扩写能力机制。名称的来源解释应能简短讲明“为什么这个群体会这样叫”，但名字本身还须能自然出现在对白里。

**声音方法不应照抄。** [Phonosemantics](https://github.com/glacierphonk/naming/blob/e7af8a5d014a330ead84421274178e36e72ecd5f/phonosemantics.md) 明确说其辅音分类与不少音形联想主要基于英语及相关日耳曼语言，并提醒受众语言不同应先验证。它列出的英语 plosive/fricative/nasal、前后元音、重音和拼写簇，不能直接解释普通话声母、韵母、声调、变调或中文词义；“硬音显强”“前元音显快”等不作为《失帧》的中文命名判断。该文提到的 2:1 偏好与 bouba/kiki 百分比未在该文件提供原始研究引用；本报告不将其用于中文创作。

**参考材料的适用性和证据质量。** [Anti-patterns](https://github.com/glacierphonk/naming/blob/e7af8a5d014a330ead84421274178e36e72ecd5f/anti-patterns.md) 提供了有用的反例检查：同质后缀、无意义混成、空洞的强势词、泛化组合、过度象征，以及靠名字直接标注类型或功能。但“词本身必须可画成图像”“实词记忆率高于造词”等是该 Skill 的价值判断/量化断言，不应当成普遍铁律。[Cultural References](https://github.com/glacierphonk/naming/blob/e7af8a5d014a330ead84421274178e36e72ecd5f/cultural-references.md) 对神话/文学借名提出“来源需与用途有具体对应、离开解释也成立、不是最显眼的陈词滥调”的筛选原则；方向有益，但其中的科技产品案例及来源故事并未在文件中逐项链接一手材料。[Case Studies](https://github.com/glacierphonk/naming/blob/e7af8a5d014a330ead84421274178e36e72ecd5f/case-studies.md) 自称记录 verified origin，但正文没有列来源链接；故只把它当作该 Skill 的案例讲法，不以其逸闻证明一个命名规律。

[Language Rules](https://github.com/glacierphonk/naming/blob/e7af8a5d014a330ead84421274178e36e72ecd5f/language-rules.md) 谈到可读音译、跨语言歧义、借词来源和“异国情调”陷阱；其中面向英语听众的可发音性说明不适用中文内名判断，但“来源要做实际工作、不要只借文化符号显高级”可以抽象为创作伦理与出处检查。[languages/INDEX.md](https://github.com/glacierphonk/naming/blob/e7af8a5d014a330ead84421274178e36e72ecd5f/languages/INDEX.md) 仅列波兰语、欧洲葡萄牙语、巴西葡萄牙语指南，没有中文/普通话指南。三份指南已检视其语言特有章节结构与命名建议范围，但不把波兰语或葡语的声义、词法、文化判断迁移到临江故事。[Polish](https://github.com/glacierphonk/naming/blob/e7af8a5d014a330ead84421274178e36e72ecd5f/languages/pl.md) · [pt-BR](https://github.com/glacierphonk/naming/blob/e7af8a5d014a330ead84421274178e36e72ecd5f/languages/pt-BR.md) · [pt-PT](https://github.com/glacierphonk/naming/blob/e7af8a5d014a330ead84421274178e36e72ecd5f/languages/pt-PT.md)

**不适合本任务照搬的部分。** 该 Skill 强制竞品搜索、域名/平台可用性、注册商标初筛，要求最终 3–5 个名字和加权分数；这些是产品品牌决策，不是《失帧》内部术语的交付标准。本轮用户要求可追溯的命名提案与来源说明，而非域名商标清单或盲选的营销结论。不得为遵守上游 Step 5 而实际查询商业平台或把“可注册”伪装成作品内名的原创性证明。其对词长、英文拼写与“1–2 音节理想值”的建议也不可作为中文名规则。

## Findings: story-skills/worldbuilding

[Worldbuilding SKILL](https://github.com/danjdewhurst/story-skills/blob/57121ee512c6d4218a285c6991193347944f31b0/skills/worldbuilding/SKILL.md) 把命名置于故事元素系统中：人物、地点、势力、系统、器物和词汇需要彼此关联；陌生词可以有 pronunciation，并在 glossary 记录定义、拼写、使用者和不代表的含义。直接的命名指南 [Naming Languages](https://github.com/danjdewhurst/story-skills/blob/57121ee512c6d4218a285c6991193347944f31b0/skills/worldbuilding/references/naming-languages.md) 建议每个架空文化先设一份有限 phonology sketch（常用/不用的音、音节结构、重音、后缀和拼写规则），再写人名顺序、亲属/头衔、人生阶段变化、地名构词和禁忌词；用少量词根产生可识别的模式，但区分文化至少应改变两项语音/音节/词尾特征。它强调读者易把形状相近的名字混淆，并建议在命名之前做候选撞名检查。

**文化事实边界。** 这是一套“如何编出一致的架空命名系统”的提示，不是经田野调查、方言语料或社会史证明的中国文化/姓名资料。文档所举 Vellish、Kelmar、Kelvoss 是造出的写作示例；不会据此推断临江地名、民俗、能力者黑话或普通话音韵事实。[World Element Types](https://github.com/danjdewhurst/story-skills/blob/57121ee512c6d4218a285c6991193347944f31b0/skills/worldbuilding/references/world-element-types.md) 和 [Faction Template](https://github.com/danjdewhurst/story-skills/blob/57121ee512c6d4218a285c6991193347944f31b0/skills/worldbuilding/references/faction-template.md) 有助于确保势力命名来源贴合目的、权力基础、人员、冲突和内部路线；模板本身不会替作者建立中国组织的语体或历史依据。[System Template](https://github.com/danjdewhurst/story-skills/blob/57121ee512c6d4218a285c6991193347944f31b0/skills/worldbuilding/references/system-template.md) 将系统定义、限制、历史、参与者及社会影响放在一起，对防止术语与机制脱节有帮助。

该 Skill 其余位置/器物/历法/经济/交通参考服务于更大规模的奇幻或小说世界记录，不直接产出《失帧》名称。世界元素以 YAML frontmatter、kebab-case ID、自动重建 index、双向 entity links 的方式储存；人物名和世界 glossary 还提供 CLI 相似性提示、改名重链和发音表。[Story Conventions](https://github.com/danjdewhurst/story-skills/blob/57121ee512c6d4218a285c6991193347944f31b0/skills/story-maintenance/references/conventions.md) 明确这些属于 Story 项目结构。可抽取“给提案附拼读/称呼说明、检查新术语是否和已有名字抢声形”的思路，但不引入 CLI、schema、文件树、YAML 字段或第二份项目级世界术语权威。

## Findings: character-naming-author-skill

[中文角色命名 Skill](https://github.com/kunhai-88/character-naming-author-skill/blob/84774f7aa31ddd96afb27146ac12f7b95fc38bce/skill/SKILL.md) 是三者中唯一明确面向中文短剧/影视/小说人物姓名的工作流。它把姓名视为口头声音、人物出生时获得的社会事实、以及通过关系和剧情占有的叙事资产。核心流程先读剧本和关系，确定时间、地域、家庭权力和谁给人物取名，再建立“真实姓名带宽”，为候选各自选择一个不同生活来源，先进行裸名淘汰，放入长辈、亲密者、对手和机构称呼中试演，最后隐藏寓意盲比，并为名字设计首次出现、关系变调和结尾回收。[Author Naming Method](https://github.com/kunhai-88/character-naming-author-skill/blob/84774f7aa31ddd96afb27146ac12f7b95fc38bce/skill/references/author-naming-method.md) · [Naming Mechanism Library](https://github.com/kunhai-88/character-naming-author-skill/blob/84774f7aa31ddd96afb27146ac12f7b95fc38bce/skill/references/naming-mechanism-library.md)

“真实底盘上只留一个干净异常点”尤其能避免姓名只是把温柔、深沉、记忆、夜晚等性格、能力或主题标签拼成名字；其“名字要被剧情占有”的要求也符合《失帧》重点角色既有身份已经受剧情承载、应优先保护而不是整体换名的目标。[Memorability and Ownership](https://github.com/kunhai-88/character-naming-author-skill/blob/84774f7aa31ddd96afb27146ac12f7b95fc38bce/skill/references/memorability-and-ownership.md) · [Anti-AI Audit](https://github.com/kunhai-88/character-naming-author-skill/blob/84774f7aa31ddd96afb27146ac12f7b95fc38bce/skill/references/anti-ai-audit.md)

其候选盲选设计会隐藏寓意、首选顺序和机制名，分别问“像真人、好记、属于人物、像 AI、延迟复述”；原因码记录失败机制，且要求跨多个案例后才把单次反馈升级为偏好。[Candidate Selection](https://github.com/kunhai-88/character-naming-author-skill/blob/84774f7aa31ddd96afb27146ac12f7b95fc38bce/skill/references/candidate-selection.md) · [Human Evaluation](https://github.com/kunhai-88/character-naming-author-skill/blob/84774f7aa31ddd96afb27146ac12f7b95fc38bce/skill/references/human-evaluation.md) 这些原则对新人物候选很有帮助，但本轮没有真实观众盲测，也没有对角色配音/演员试读；报告不得声称已经通过人类测试。

**中文声音检查能力及其局限。** 附带的 voice_audit 使用普通话拼音、声母/韵母/声调及候选拼音编辑相似度提醒同剧人名可能混淆；有多音字/特殊读法覆盖入口。这个目标比英语音素指南更接近影视对白，但它的 README 与脚本自己都说明不涵盖方言、表演中的变调或文学判断。name_audit 的预设姓氏/高频类型字、同姓、共用字、同尾字、全体名字长度检查也是启发式提示；相同字符未必听感近，相同姓氏也可能是必要亲属关系。因此候选判断要合并普通话朗读、原角色关系、旁白/对白实际语境和人工听辨，不能将脚本结果当淘汰结论。[README](https://github.com/kunhai-88/character-naming-author-skill/blob/84774f7aa31ddd96afb27146ac12f7b95fc38bce/README.md) · [voice_audit.py](https://github.com/kunhai-88/character-naming-author-skill/blob/84774f7aa31ddd96afb27146ac12f7b95fc38bce/skill/scripts/voice_audit.py) · [name_audit.py](https://github.com/kunhai-88/character-naming-author-skill/blob/84774f7aa31ddd96afb27146ac12f7b95fc38bce/skill/scripts/name_audit.py)

这里的强项仅在人物姓名层。能力名称、灵异类别和组织名称不是“人物姓名”，不能把 character Skill 的五关机械地套成同一评分表；可转化的是先问命名权、历史来源、使用关系、口头辨识度和剧情占有。它本身强调关系中叫法的所有权，这一点比用字面寓意解释一个组织名更适合《失帧》。

## Bounded Application to AI-VIDEO

当前 [drama-authoring/SKILL.md](../../.agents/skills/drama-authoring/SKILL.md) 已经以现有 accepted Story/Character/Scene/Shot 为创作依据，并禁止建立第二套项目状态；[Story Development](../../.agents/skills/drama-authoring/references/story-development.md) 已要求角色行动、信息、关系、因果和未确认事实须可追溯。命名方法可作为这个既有写作流程中的辅助检查，而不是第三方 Skill 安装或另开 Canon：

1. **先冻结事实，再命名。** 先从既有世界/能力设定确认名称指称的对象、机制和已知程度；名字只能表达某个剧中人或机构当时能理解的部分，不替剧情提前解释深层真相。
2. **每个术语记录命名者/场合/立场。** 设计时可分开想正式档案称谓、现场行话、群体自称、对手贬称或市民俗称；只有剧本真的会使用的称呼才保留。它们是候选的语用层次，不等于要求所有对象都配五个名字。
3. **先语境后字形。** 按对象实际命名来源找一个可讲清的历史、动作、物件或关系依据，再比较声音/词形；不要用同一种 X帧/X者 尾缀把全部能力、异常、组织伪装成一个游戏技能表。不同组织可以有自己的叫法逻辑，但差异须从历史、职责、圈层、知识或立场来。
4. **让对白决定能不能用。** 新术语逐个放进一条自然对白和一条紧急喊话里；读音按普通话多音字、声调、同剧角色、既有词条作复核。中文语音脚本可在可用且获准的环境中作提醒；本次不安装或执行。
5. **区别建议和 Canon。** 命名审查应给候选来源、含义、口头传播风险、撞名/混淆状态与推荐级别。只有作者确认后才升级为正式 Canon；这与本轮“只审查，不覆盖正式 Canon”一致。

**本轮推荐取用。** 采用三项方法：character Skill 的“既有人名保护、关系/对白试演、去解释盲审”；worldbuilding 的“为不同机构/群体写出有来源的命名规约并维护已有词汇碰撞”；naming Skill 的“从机制所处的具体概念领域找隐喻、排除模板化组合”。应继续由现有 drama-authoring 和《失帧》Canon 文档承接最终判断。暂不建议新增或安装命名 Skill；若后续要把方法固化，应作为现有创作参考中的短命名检查段，并且只在目标人物/术语与实际剧本材料充足时调用。

**明确不采纳。** 不迁移商业品牌域名/注册商标可用性门、不使用英语声义作为中文规则、不为现代临江创造一整套伪方言/伪文化、不强行给人物做改名、不为了整齐增加能力战力阶位、不照搬 story 命令或 Story 项目 YAML 文件格式、不以自动脚本替代观众/作者听辨。

## License and Dependencies

以下是对源仓库实际 LICENSE 文本、脚本和 package 元数据的观察，不构成法律意见。

| Source | Observed license source | Runtime/development dependencies |
|---|---|---|
| glacierphonk/naming | 根 LICENSE 实际写 MIT License（copyright 2026 GlacierPhonk）。仓库没有发现其他 LICENSE/NOTICE 文件。单纯研究原则不等于复制文字；若未来逐字复制文件或大段表达，须回到源 LICENSE 和本地开源许可流程。 | SKILL.md 无安装包清单。其声明 Claude Code 工具 Read/Grep/Glob、Bash whois/curl/npm/gh 与 WebSearch/WebFetch。availability 脚本会向 whois、npm、多个 HTTP endpoint 发请求；这不是本任务需要。 |
| story-skills/worldbuilding | story-skills 根 LICENSE 实际写 MIT License（Daniel Dewhurst）；worldbuilding 子树没有另设 LICENSE。 | Worldbuilding 文本可独立人工使用；Story CLI 是可选。根 package.json 声明 Node >=18、packageManager bun@1.4.2、devDependencies 为空。Skill 指定 Node fallback 脚本并提醒避免 Bun 配置副作用；这套 CLI 不属于本地任务。 |
| character-naming-author-skill | 根 LICENSE 实际写 MIT License（kunhai-88）；skill 子目录没有发现另设 LICENSE。 | Markdown Skill 核心无运行依赖。name_audit、blind_test 是 Python 标准库；普通话 voice_audit 额外需要 requirements-voice.txt 锁定的 pypinyin==0.55.0，并通过安装脚本置于 Skill 自己的 .voice-venv。官方上游 v0.55.0 [LICENSE.txt](https://github.com/mozillazg/python-pinyin/blob/df101577145af2eb1abe5656e592e34e3bb56d23/LICENSE.txt) 写 MIT License。未安装/执行。 |

Naming Skill 除根许可证外提到 WordPress 商标政策和商标搜索入口，这些只服务商业名称决策；没有复制第三方材料。character-naming 对 pypinyin 的调用是可选普通话语音检查依赖；若未来安装须连同具体 Python 包许可和依赖安装效果再核验。此次未运行任何网络 availability check、Story CLI、Python 工具或 benchmark。

## Source Inventory

以下 SHA 是该 commit 下 GitHub API 返回的 Git blob SHA。超出本审查正文范围的维护文件列出但没有逐项阅读其内容；所有列入 SKILL、被其直接引用或为依赖/许可判断所需的目标文件均已读取。相邻 commits 不改变本表版本身份。

### glacierphonk/naming

固定 commit e7af8a5d014a330ead84421274178e36e72ecd5f；[tree](https://github.com/glacierphonk/naming/tree/e7af8a5d014a330ead84421274178e36e72ecd5f)。

| Path | Role/status | Blob SHA |
|---|---|---|
| SKILL.md | 入口及完整流程，已读 | 34d86f5fc49b621d0bb7d0392fb14fbdf8da394a |
| principles.md | 核心原则，已读 | 8bbe445ba8342e76510ed6e2e1b3891e01b25f29 |
| phonosemantics.md | 英语音义指南，已读 | 901c2e426e42b72c502d35010e1c956166e6ee6d |
| anti-patterns.md | 反模板/淘汰表，已读 | 3a1a4583b52d7ba3ef956d65270db51f3ac9bcbb |
| metaphor-mapping.md | 隐喻领域方法，已读 | 4adfc3fd3933c9cba7566112c0f49ec84f71900d |
| cultural-references.md | 神话/文学/文化引用建议，已读 | e7c7e0c744ec359a1753ff5742e62182d6e36a61 |
| brand-architecture.md | 商业品牌家族结构，已读 | 0ef8c0d29e96e1e9243680763c15c212d627e902 |
| language-rules.md | 借词/音译/外语流程，已读 | 49aa39c82ba374c73880e05ccf32f9f75d512647 |
| availability.md | 商业名称可用性和搜索性，已读 | c46bf74aa5d6f7a91dfb85920b0ef66492584f14 |
| case-studies.md | Skill 中所列命名案例，已读；源未逐项给出处 | 358a31518ccecd9bc9021e5c501ebb2af034ab00 |
| evaluation.md | 候选评分及对白测试，已读 | 4540011346e48de975082434c66bd9256ad46cc1 |
| languages/INDEX.md | 语言文件索引；确认无中文 guide，已读 | 519e044b18a998be5a0e5547b4771ba76f524125 |
| languages/pl.md | 波兰语 guide；已读，非本项目语言 | 979fb5ce8b4ab4d07e1a96dbbbd1a3931bd090f6 |
| languages/pt-BR.md | 巴西葡语 guide；已读，非本项目语言 | 4f0591db55986491631a2cbff354dd0c8050b3f6 |
| languages/pt-PT.md | 欧洲葡语 guide；已读，非本项目语言 | adefd819f507ee1b1bc0031e1ab168d66b207890 |
| industries/INDEX.md | 行业 guide 索引；无行业子文件，已读 | 85b9d785126a33218d090610d2141729e32af9d6 |
| open-source.md | 软件项目约束，已读但不适用于剧中名词 | e1e35e8874bae60247ba011cf09414666ff31120 |
| taglines.md | 产品 tagline 指南，已读但不适用 | 263ed881fdfb32671932f3c74276dab6a1806f45 |
| templates/naming-brief.md | 商业命名 brief，已读 | c1348981602db17d988d35da97336da9b83e6b36 |
| scripts/check-availability.sh | 含外部网络检查；已读源代码，未运行 | 7214e5235b1d684922e21c11944c1eead163c973 |
| LICENSE | 根目录 MIT 文本，已读 | 78b9046e77c9776d7540a300797d45c3b759509f |
| README.md | Skill 总览及文件说明，已读 | 6ea7c1cd1aa4dbeafabc3b2d47e93f8201f51b54 |
| CONTRIBUTING.md | 语言/行业贡献格式与来源要求，已读 | ed948d9e9d3fd88167728b0c3a1175530a16edef |
| .github/pull_request_template.md | 维护模板，未读 | 36f52f49d46496704173fa6fc16486fcfd12947b |
| .github/workflows/links.yml | CI 链接检查，未读 | 9e094bc3a2424854211863906ee0ff06647c8a85 |
| .github/workflows/lint.yml | CI markdown lint，未读 | 8c8e2a42d7f7b866e5f199df9846daeb7131fc43 |
| .markdownlint.yml | 文档 lint 配置，未读 | 2db4a5678816f2d19016fbd51bddb4d9694214f9 |
| CODE_OF_CONDUCT.md | 社区管理材料，未读 | 74737b038164058de2fdbcca1160bd5c2533cad8 |

### danjdewhurst/story-skills

固定 commit 57121ee512c6d4218a285c6991193347944f31b0；只筛选 worldbuilding 子目录和 Skill 强制引用的资料；[tree](https://github.com/danjdewhurst/story-skills/tree/57121ee512c6d4218a285c6991193347944f31b0/skills/worldbuilding)。

| Path | Role/status | Blob SHA |
|---|---|---|
| skills/worldbuilding/SKILL.md | 完整 worldbuilding 流程，已读 | cbc95885d21ad23e8094fa0b827c682bd59d44d7 |
| skills/worldbuilding/references/artifact-template.md | 器物模板，已读 | 46242bf14f9df29066da279c167b08790b828bb6 |
| skills/worldbuilding/references/calendars.md | 历法模板/连续性，已读 | 8dbdca5f5965e564558b48efc6cfee272953d87 |
| skills/worldbuilding/references/economy-logistics.md | 经济、物流和能力代价提示，已读 | b67588566e6cfcd22ef003c5a3ec0deeffefad08 |
| skills/worldbuilding/references/faction-template.md | 势力模板，已读 | 86158883e50982b74cd1e32424ce69c2ddde312f |
| skills/worldbuilding/references/location-template.md | 地点模板，已读 | b4e3960d83dd39c2c612d6babb20632c974e8d84 |
| skills/worldbuilding/references/maps-and-routes.md | 地点关系图/行路连续性，已读 | 92b527ae8de2422708bdcf21460a662c4277fd28 |
| skills/worldbuilding/references/naming-languages.md | 命名规则/虚构语言/相似性检查，已读 | f22350d221d14e049c4c7a48aecf6201a9ced3e4 |
| skills/worldbuilding/references/system-template.md | 系统模板，已读 | 86731d09b5a88993a8e43a42be144c2562e87532 |
| skills/worldbuilding/references/world-element-types.md | 魔法/政治/技术等提示题，已读 | 9e0ef7b6c3a00c791262937c6559a4d5dc6e233f |
| skills/story-maintenance/references/conventions.md | 目标 Skill 强制要求，已读 | 43888f01b7929c9df34a7e433bfc6b457f22c7d4 |
| skills/story-maintenance/scripts/package.json | fallback 脚本模块配置，已读 | 3dbc1ca591c0557e35b6004aeba250e6a70b56e3 |
| package.json | Node、packageManager 与依赖声明，已读 | 0b8ea92986b5eda23458511a123cf4fb4d9c7aaa |
| LICENSE | 根目录 MIT 文本，已读 | 6dc3c47c331652ddbf12759e8a6af340dd222bad |

### kunhai-88/character-naming-author-skill

固定 commit 84774f7aa31ddd96afb27146ac12f7b95fc38bce；[tree](https://github.com/kunhai-88/character-naming-author-skill/tree/84774f7aa31ddd96afb27146ac12f7b95fc38bce)。

| Path | Role/status | Blob SHA |
|---|---|---|
| skill/SKILL.md | 中文人物命名主流程，已读 | 522eafd6cf083c8388de67fe19bbace96d226eb8 |
| skill/references/author-naming-method.md | 取名现场、社会来源、关系试演，已读 | c5eb160a3f4f4a4a00663ef8b9de7b9bac7fcf50 |
| skill/references/reality-calibration.md | 现实姓名邻域校准，已读 | 7cf8deacb090e76e4b670a40c32d9129bde0e89d |
| skill/references/naming-mechanism-library.md | 角色姓名来源机制，已读 | df9f61ea287266d3241f0483b0d9a7595e18111d |
| skill/references/memorability-and-ownership.md | 记忆点与剧情占有，已读 | 5b3a2d7c472dc205c97ebd6679850385fcec4c09 |
| skill/references/candidate-selection.md | 候选来源卡与去解释盲比，已读 | 81c464db7dc773fed663b64cc9e268fd4245b3e8 |
| skill/references/human-evaluation.md | 人类盲测/隐私，已读 | e8719899eebb0b6e04ff5cc4742b802e2d400de1 |
| skill/references/anti-ai-audit.md | 裸名门及五关审查，已读 | d59fb77c61685d1a368a0b98b0dad2bb46eea137 |
| skill/scripts/name_audit.py | 中文姓名字符串启发式，已读源代码、未运行 | 36d8c6bd670fd5776646f8677c5bf0349880ff15 |
| skill/scripts/voice_audit.py | pypinyin 普通话音似检查，已读源代码、未运行 | dbde7e914bb775cc9e03d6b437926d1ebdf0cf64 |
| skill/scripts/blind_test.py | 本地 JSON/JSONL 候选盲测工具，已读源代码、未运行 | 19de14ced0a790596958453bc86e42604233ccec |
| skill/scripts/install_voice_dependency.py | venv/pip 安装辅助，已读源代码、未运行 | adabccdb4e0fcd9aea34181b0c9d87a3bd183c9a |
| skill/requirements-voice.txt | 可选固定依赖 pypinyin 0.55.0，已读 | 0214ecd72db7cdee7e4b2d1d79b333727563ab17 |
| LICENSE | 根目录 MIT 文本，已读 | b19fddbfdf7e6f341e62c54bb0345dfb78e1a734 |
| README.md | 中文用法、脚本和依赖说明，已读 | 3f2449fc3584e3e77f751cfc1a1b62d8faeb5852 |
| examples/quickstart.md | 命名示例，已读 | f8c66aacfa4dbd22f62c9547fca1fb9fc4cff64c |
| benchmarks/README.md | benchmark 说明，已读状态未测 | 540f489a44902cc999603f4ae7a3ced9f22bbfc2 |
| benchmarks/regression_cases.json | regression cases，未逐项验证 | 9d6d3d3c306ed4bd46ca223f672d63853f927e8c |
| README.en.md | 英文文档；不属于本中文命名路径，未读 | 7ba4fd38cf1d1ccdb3f72cdd0b1f629af160ae98 |
| scripts/package_skill.py | Skill 打包/维护工具，未读/未运行 | d0d9f860ad72bf7c1e508a2b4719db64beca890e |
| scripts/validate_benchmarks.py | benchmark 验证工具，未读/未运行 | 89c80d4925b78172e6754eb9424931643ea383c4 |
| scripts/validate_skill.py | Skill 校验工具，未读/未运行 | 1ca5ac205480fed75c8a8c520bc37cc16bf7e46e |
| tests/test_blind_test.py | 测试文件；未运行 | dfee82f559c08c5efa1248996b0eff1b7f8e215c |
| tests/test_install_voice_dependency.py | 测试文件；未运行 | 7ef90962fe06f9477f6d9d3c1b88ddb4bdab935f |
| tests/test_name_audit.py | 测试文件；未运行 | 6db5b46fc054aa62db18bcc8d29194e0d184b9db |
| tests/test_voice_audit.py | 测试文件；未运行 | 97bffd338c2947fa2133b145aa270ffe6634596f |

## Unverified Areas

这份审计不对具体《失帧》人名、能力、现象或势力名称做候选生成、读音检索、作品撞名检索或观众测试；也不判断 Skill 方案在人类创作中的实测提升幅度。英文 phonosemantics 与 naming 案例的定量/起源主张没有在上游文件里给出足够的逐项一手来源，本报告不为这些主张背书。仅报告所标 commit 的源内容、LICENSE、引用关系和方法边界；没有运行 Skill 上游测试、脚本、生成媒体或任何生产工具。

## Verification

文档合同检查与 git whitespace 检查见本次交接记录。本文只是一份研究审查，不是对第三方 Skill 的安装许可、AI-VIDEO 集成 PR、原创命名批准或《失帧》 Canon 修改。
