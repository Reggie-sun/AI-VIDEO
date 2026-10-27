---
record_kind: session_summary
topic_id: shizhen-four-character-reference-packs
learning_eligibility: ineligible
---

# Shizhen Four-Character Reference Packs

## Scope And Story Basis

用户先要求按第一季大纲分配主次人物的参考深度，随后明确本检查点为董文慧新做一套，罗敏、高峥、闻素芬各整理一套；每套区分长期人物身份与当前场次，并按文中行动、地位和性格设计。没有宣称全季人物已完成。

交付 owner 为 `referces/shizhen/character-packs-20261027/`：8张当前选用参考板，`identity/` 与 `scene/` 分层，总览为 `index.html`。剧情依据、原文件SHA、输入与提示词、两次修复历史归 `package-manifest.json`；每个人的基线／可变状态及职责归各自 `reference-usage.json`。

董文慧按28岁应急文字记录者的听辨、核对和有限判断设计；闻素芬按44岁经营者兼修复师的专业动作、审慎和工作控制感补外观候选。尚无闻素芬既定人像，不冒充已拍演员。两人E02／E05服装、记事本／寄存资料、场地与具体动作均为基于大纲的未拍视觉候选，不修改Canon。罗敏、高峥沿用现有雨站面孔；场次资料直接重开并整理原镜头，不凭文字换演员或重演消失。

## Actual Media And Verification

四套共8次内置 `image_gen.imagegen` 调用，全部已返回：4张身份底图、2张初始场次图、董文慧场次2次有界修复。v1中间持本手换位、v2转身后手别不够明确，均保留为历史；v3可追踪三格左手持本／右手空手，未删掉引路动作回避问题。罗敏／高峥场次另用2次本地固定文档渲染，不计生图。

8张选用参考板均实际查看、可解码；工具原始输出与副本SHA一致。原剧情文档与原视频／源帧SHA重新核验，实际提示词中文检查通过。未更改原剧本、原片、Character Bible、Registry、Manifest或其他Production状态，未新生成视频或音频。`verification.json` 是本地静态资产与来源核验，非Harness full、真人统一风格、视频模型消费或动态服从验收；人类接受仍 `NOT_EVALUATED`。罗敏／高峥旧素材的CG风格影响和年龄感限制保留，不把整理当作真人风格已通过。

## Courier Checkpoint And Remaining Limits

用户另要求第一集快递员简单三张。`referces/shizhen/courier/three-views-20261027/` 实际返回正面、侧面两张，背面第三次网络中断UNKNOWN；有限3次已使用、零盲重试，状态 `PARTIAL_UNKNOWN_BACK`。两张原图与副本已重验。该未完成项不被四套人物交付掩盖，未恢复或改写旧未知结果。

本四套8次、快递员3次均未暴露金额／额度，UNKNOWN调用用量待确认。图片保留本地，Git仅记录说明、提示词、布局与来源／核验文件。按 `record-ai-video-session` 保存此资产检查点；`distill-ai-video-learning` 为 `no_candidate`：角色设计与同一动作修复链不能支持通用模型质量、跨镜一致性或流程采纳结论。
