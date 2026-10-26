---
name: scenario-identity-library
description: "Use in AI-VIDEO when approved characters or props need reference images, additional views, close details or an identity sheet before storyboard/keyframe production. Asset preparation specialist only; does not own story, video prompts, generation execution or acceptance."
license: MIT
---

# Identity Reference Asset Preparation

## Scope And Ownership

这是下载的 Scenario Identity Library 的 AI-VIDEO 适配入口。仅负责人物/道具参考素材准备；
`open-video` 继续拥有导演与 coverage，Character/Scene/Shot 保留身份与剧情事实。
本入口优先于随包原文。[UPSTREAM.md](UPSTREAM.md) 原样保留用于方法查阅，
来源与版本见 [SOURCE.json](SOURCE.json)，许可证见 [LICENSE](LICENSE)。

## Prepare The Missing References

1. 先查看已批准原图与当前素材，列出不变特征及本镜需要的视角/细节。已有合格图直接复用，
   不为了凑数量重新造脸；信息可从项目取得时不重复采访用户。
2. 按实际镜头需要补正面/侧面、服装比例、面部近景或道具结构与握持细节；全身图不自动证明
   近景细节足够。每张图标明控制的对象、属性，以及不应继承的背景、姿势或文字。
3. 制作变体时实际绑定同一身份原图，明确保留项与本次变化；不能只在文字中声称参考了原图。
   图像制作沿现有授权图像工具与项目资产登记流程执行，不用此 Skill 自建 Provider。
4. 逐张查看面貌、服装、比例、手部、道具结构与一致性。失败图片不作为合格锚点；修复仍受
   当前预算和 known-outcome 边界约束，不继承上游默认三次重试。
5. 输出实际图片路径/既有 asset identity、用途、已观察问题和未验证项。需要多视图表时从已
   检查单图组装；多视图表是参考资料，不自动作为视频首帧，防止把多人复制或拼格带入成片。

## Handoff And Exclusions

交接前按共享 [Reference Continuity Review](../open-video/references/reference-continuity.md) 区分身份属性
与不应迁移的姿态、背景、视角和注释；有标注的多视图表可供审看，但不自动成为干净的视频输入。

动作状态与端点交给 [storyboard specialist](../scenario-seedance-storyboard/SKILL.md)；
最终视频提示词和输入职责交给 [seedance-authoring](../seedance-authoring/SKILL.md)。
Registry 独占素材身份，ProductionStateCommitter 独占生产写入，不建第二套 Scenario collection
或 identity registry。上游 `recommend`、`model_run`、collection、Grid Maker、自动安装 sibling
skills 等操作不适用于本项目；取其制图方法，不执行其平台流程。

不改剧情、不选视频模型、不提交/重试视频、不签 PASS、不自动拼接或发布；
`runtime_skill_calls = 0`。图像一致不证明视频动作、声音或最终人工接受。
