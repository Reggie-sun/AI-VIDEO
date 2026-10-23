---
name: drama-authoring
description: Develop or revise Chinese short-drama and comic-drama stories, episodes, scripts, or production design from supplied ideas or source material. Use for drama narrative work; use ecommerce-ad-workflow and ad-creative for product-advertising briefs.
---

# Drama Authoring

为短剧、漫剧提供按需的剧情创作与制作设定方法。剧情事实遵守已接受的 [Drama authoring contract](../../../docs/superpowers/specs/2026-08-28-ai-video-drama-authoring-and-acceptance.md)。将结果交给现有 `open-video` 形成唯一镜头方案；本技能不拥有 Director coverage、Production state、媒体、Runtime 或验收。

## Route By Requested Work

先判断用户要完成哪一层，直接读取对应 reference；不为流程齐全而补齐未请求的阶段。

- 剧情构想、改编、人物目标、系列发展或分集：读 [Story Development](references/story-development.md)。
- 单集剧本、对白、动作或场景因果：也读 [Story Development](references/story-development.md)，按用户给定范围写或修。
- 角色视觉身份、场景、叙事道具或开场站位提案：读 [Production Design](references/production-design.md)。
- 需要同场调度、摄影 coverage 或跨镜头接法：交给 `open-video`；本技能不写第二份分镜或动态 blocking。
- 表演/动作提示、选定模型的 prompt 或媒体问题：交由 `open-video` 按需路由到表演/动作专项、已选版本的 authoring 和现有 Production owners。

广告 brief 中出现人物情节，不会自动改变其广告任务归属；广告策略、产品事实、商品功效和 commercial package 由现有广告 owner 管理。剧情作者可以提供人物与事件建议，不得发明产品主张。

## Preserve Source And Requested Scope

先分清用户提供的是已接受来源、创作方向，还是指定失败项的修复。保留原作、已接受剧本、角色关系、台词、事实和明确限制；仅在用户授权的改写范围内创作。修复只触及所指出的问题，并保留已成立内容。未提供的故事事实标为创作补充或待确认，不伪称来自原作。

按用户指定产物交付：只要大纲就不写整集台词，只改对白就不重构全剧；用户要完整短剧时再连接开发、分集与剧本。题材、集数、集长、画风、夸张程度和目标观众沿用用户所给信息，不为满足模板强加钩子频率、反转数、角色数或固定段落。

## Handoff And Authority

- 用现有 Story / Scene / Character / Shot 语义组织内容；不建立第二目录、项目状态、角色 ledger、staging truth、时间线或验收状态。
- 剧情阶段说明人物目标、已知信息、阻力、行动原因、触发、关系/情绪变化和结果。镜头如何覆盖这些事实归 `open-video`。
- Shuohao 风格的开场站位仅是一个场景的空间起点提案。`open-video` 可把接受的起点并入同一调度方案；中途位置变化归唯一 Shot/coverage 稿。
- 场景可以保持或改变。只有故事明确建立的因果省略、时间跨越、场景边界或重置才改变交接规则；没有 reset 时，续接真实已接受的前镜终态。续拍从实际素材终态继承，不从旧 prompt 猜测。
- 可提供故事/剧本审读建议，不签发 authoring acceptance、HUMAN media verdict、P6、Final Acceptance 或广告效果结论。Media QA 与最终判断仍走当前 owners 和 exact evidence。
- `runtime_skill_calls = 0`。不运行上游工具，不生成图片/视频，不选择 Provider，不 submit/poll/fetch/retry，不改 Project、Registry、Manifest、timeline 或 Production state。

## Upstream Sources

固定来源版本、各参考的改写范围与许可副本见 [Upstream Sources](references/upstream-sources.md)。本技能用中文独立改写方法和边界，不复制上游 schema、模板或执行流程。
