# Opening Coverage Revision Implementation Plan

**Goal:** 按用户新授权“那按照这个生成第一个shot”，保留D版人物、原三句对白和16秒原生声音，生成有明确摄影切点且纸/饭团物理路径正确的开场新版。

**Creative Decision:** 同一便利店事件采用四个摄影关注点：双人中景建立服务关系；同轴林序中近景回应；同轴店员中近景同时读到脸和手，先铺纸到空台面、再把饭团提起移到纸上、放稳推近；林序反应近景收尾。对白按自然表演，不分配单句时间。四个摄影单元组成一次16秒生成片段，不把生成次数作为镜头数。

**Execution Bound:** 保留同一Project/task、D首帧及001–003所有paid/fetch/QA历史；只新增一个004请求，累计submit3→4、内部预算1500→2000CRD（500/次上限，实际费用另计），原UNKNOWN音义调用不重试。无隐式Provider/model切换、resample、activation或下一剧情镜头。

## Contract And Ownership

Parent负责 `GenerationVisualSupersessionReceipt` 的 additive `/2`、原committer/strict reader接线、qualification hook和实际执行。独立leaf `generation_coverage_revision.py` 仅拥有typed CoverageRevisionTarget、允许变化/保护条件及pure admission和锁内predecessor校验；不写state、不发permit、不直接调用Provider。旧 `/1` 画风修订及旧hash保持。

新 `/2` 将explicit authorization绑定old request/fetch/paid/latest experience/QA，以及新same-id goal、完整target GenerationIntent和target QA acceptance；允许沿用相同D firstframe。只允许已封存coverage和subject_action.progression / camera / cadence变化；对白、表演方向、身份、材质、光照、声轨策略、open/close states、16秒输出及引用不变。新QA保留全部旧required IDs与未失败的原rule，变更仅限旧latest确证失败项并可增加新coverage要求。全部旧FinalOutput requirements保留，新goal增加切镜与物理接触要求。锁内重开exact `/2` 并核对当前intent/rubric/frame与target，不能用caller flag或新像素SHA规避 `/1`。

## Milestones

1. 更新导演覆盖与generation intent，通过现有coverage validator和native compiler；用首帧及camera文本表达内部硬切，主运动locked只指各机位内部固定，不承诺模型必然遵从。实际4镜执行与物理路径须exact MP4验证。
2. 精准验证新增typed target、旧 `/1` compatibility、wrong target / changed protected fields / unknown / stale history / counter reset / replay拒绝；相关测试及一名native独立review确认后执行。先authoring closure→QA/revision→budget extension→prepare→start→quota extension→submit。
3. 原adapter/paid gate仅submit一次；known success fetch后显式project-local video-analysis，检验实际切镜、D身份、完整表演、纸先落空台再移饭团、原台词/口型和声音。缺音义证据保留NE，有穿模或未执行切镜为FAIL；交用户原速审片后再做完整工程验证与owned-path commit/push。

## Research And Evidence Limits

2026-07-31官方发布页说明多镜叙事、镜头转换，并承认复杂物理/多主体互动仍有限制：<https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5>。这支持本次有界真实验证，不证明即梦所选surface能逐项实现本镜；当前profile、preview与exact成片是执行和质量证据。旧003的10.50–10.75秒穿模及错误PASS撤回保留，不能由新计划覆盖。
