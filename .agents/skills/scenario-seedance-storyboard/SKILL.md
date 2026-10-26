---
name: scenario-seedance-storyboard
description: "Use in AI-VIDEO when approved coverage needs missing action-state reference images, clean keyframes, a storyboard or a reference-to-input plan, especially hand/prop contact, loss of support and multi-person continuity. Does not redesign coverage or execute video generation."
license: MIT
---

# Storyboard And Action Reference Preparation

## Scope And Ownership

这是 Scenario Seedance Storyboard 的 AI-VIDEO 适配入口，仅负责把已批准的动作与摄影决定变成
可查看的参考素材。`open-video` 拥有故事、摄影及完整事件分组；`seedance-authoring` 拥有所选
版本的最终视频文字与参考语义。本入口优先于下载原文 [UPSTREAM.md](UPSTREAM.md) 和其
references；来源固定在 [SOURCE.json](SOURCE.json)，保留 [LICENSE](LICENSE)。

## Reference Preparation Before Video Authoring

1. 对照前镜实际末态、approved Shot 和失败成片，区分已有、可复用及缺失的参考。
   单张开场能覆盖人物外观，不自动代表动作过程已有视觉依据；关键接触、支撑转换、释放、
   落点或反应不清楚时，先补相应状态图或适用的运动参考，不能只反复加长文字后提交。
2. 先核对 selected surface 的模式、素材槽和版本上限，再设计图片包。人物/道具补图交
   [identity specialist](../scenario-identity-library/SKILL.md)；场景图明确柜台/物件位置、
   视线、轴线和光位。按需要制作干净入口、关键动作、出口及反应图，不规定固定图数或宫格数。
3. 每张动作图实际引用已认可身份/场景资料，检查姿态、左右手、接触点、受力、枪线等邻接物，
   并与相邻状态比较。开场图必须符合真实入口；不能把中途落稳状态冒充上一镜结尾。
4. 分镜板供人理解次序，干净关键帧承载目标画面；图中的标号、箭头和文字不应成为最终美术。
   可按需查阅 [board-craft](references/board-craft.md) 的逐图检查方法；不继承自动分数验收。
5. 展示制作出的图片及每张职责，明确哪些仅供制图/审看、哪些实际输入视频模型。
   正常速度、失重后立即掉落等时间关系不能靠静态图证明；需要时评估合规运动参考，
   没有就报告控制限制，不声称关键帧保证物理动作。

## Jimeng Canvas Handoff

画布节点、连线、文字提及和本地图片清单均不证明模型已经收到图。最终必须核对 selected
profile、native mode、实际 material 列表/顺序、图片身份与最终引用。

- 首帧、首尾帧、全模态参考按当前画布能力分别处理，不能把全套人物图强塞进首帧模式。
- 多参考图不自动获得严格首帧或按图逐时刻执行的保证；若需要精确入口，先向 Director 返回
  模式与连续性取舍，再由 existing selection/authoring owner 落定。
- 不硬套上游 2.5 时长、Scenario 字段、分镜必然服从或连续动作保证；用户选2.0就只用对应
  overlay 和实际2.0能力，不因参考需求静默换模型。

输出复用当前 Shot/素材记录中的图像用途、状态关系和实际输入映射，不另建 schema/manifest。
生成经既有 adapter、budget、permit、committer；本 Skill 不调用上游 `model_run`/jobs、
不自动安装 Scenario 依赖，不改变用户审批要求。剪辑归 ResolvedTimeline/HyperFrames，
媒体验收归现有 Gate；`runtime_skill_calls = 0`。
