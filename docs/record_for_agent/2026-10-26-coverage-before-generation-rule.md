---
record_kind: architecture_implementation
topic_id: coverage-before-generation
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Coverage Before Generation Rule Correction

## Authorization And Scope

用户追问S01固定单镜的规则来源后明确要求“修改规则”。本次直接修订导演/作者规则，不生成视频，不改写旧分镜、素材、付费历史或检查凭据。旧S01的具体穿模事实和原PASS撤回保留在既有失帧记录中，不从单例推导固定切镜数量。

## Changes

- `AGENTS.md` 增加一句持久原则：镜头数、景别和切点服从叙事与表演，段落/片段不默认等同摄影镜头，修复不自动冻结原机位与剪辑。
- `open-video/SKILL.md` 独占具体决策：先按戏剧关注点、信息揭示、动作因果与反应决定coverage，再适配生成片段；单镜须有具体机位/调度理由，不以保表演、避漂移或方便生成作为唯一依据，也不要求一句一切。
- `seedance-authoring/references/authoring-common.md` 将primary camera intent明确为单个摄影镜头的表达职责，不据此限定一段戏或一次生成只有一个镜头。
- `seedance-authoring/SKILL.md` 明确修复若涉及coverage/摄影/切点，返回既有Director，在已有授权范围内修订并走原authoring revision与执行准入；局部修复的变量限制不冒充导演要求。

原视觉qualification入口仍限定美术修订。本次没有放宽其代码、预算、permit、UNKNOWN、安全或真实验收；改变摄影不能借美术入口越界。已满足的叙事、表演与连续性效果仍须保留，历史receipt不原地改写。

## Verification

Parent检查三个决策场景：普通交谈可按注意点拆为多个摄影镜头；有明确调度/揭示理由的单镜仍可保留；画风修复中发现镜头设计问题应回Director修订，不能把窄入口变量限制当创作禁令。此为文意检查，不是模型行为或媒体质量证明。

两个Skill的 `quick_validate.py` 均通过；现有 `test_open_video_skill.py` 与 `test_seedance_authoring_skill.py` 共56测试通过；`scripts.docs_contract_gate check` 通过。没有增加仅匹配新措辞的测试，没有运行媒体或付费调用。

此次为有界文字澄清，不改运行时准入或持久化行为；Parent self-review，未触发native独立审查Risk Gate。原Skill/AGENTS已有其他未提交修改保留，提交仅含本次规则hunks和本记录。

## Learning And Publication

Automatic learning evaluation：`no_candidate`。这是用户直接授权的规则修订，不是已验证的模型质量规律，不创建学习占位或改写全局memory。规则的实际创作收益仍待后续作品验证；本次没有发布媒体。
