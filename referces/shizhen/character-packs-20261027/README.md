# Shizhen Four-Character Reference Packs

## Deliverables

用户最新点名董文慧、罗敏、高峥、闻素芬，要求结合各自在文中的行动、地位和性格，严格区分人物身份底图与当前场次参考。本检查点仅交付这四套，不宣称全季所有人物已完成。

[打开四人总览](index.html)。每套两层分别存入 `identity/` 与 `scene/`，共8张当前选用参考板：

| Character | Identity | Current scene | Status |
| --- | --- | --- | --- |
| 董文慧 | [身份底图](dong-wenhui/identity/identity-v1.png) | [场次参考](dong-wenhui/scene/scene-v3.png) | 新设计候选 |
| 罗敏 | [身份底图](luo-min/identity/identity-v1.png) | [场次参考](luo-min/scene/scene-v1.png) | 既有面孔整理；风格与年龄感待人审 |
| 高峥 | [身份底图](gao-zheng/identity/identity-v1.png) | [场次参考](gao-zheng/scene/scene-v1.png) | 既有面孔整理；眼镜属于可摘戴配件 |
| 闻素芬 | [身份底图](wen-sufen/identity/identity-v1.png) | [场次参考](wen-sufen/scene/scene-v1.png) | 暂无既定人像，外观补全候选 |

## Identity And Scene Responsibilities

身份底图均为正面、四分之三侧面、侧面、全身四视图，观察脸型与五官关系、发际线、体态和自然年龄感。中性干燥打底服只是看清比例的展示条件，不是人物永久服装。

场次参考单独保留开场服装、干湿、携带物及动作阶段。以后可换衣、受伤、变老；应在同一身份基线上生成可解释的新状态，不因新衣服或一次湿发换演员，也不把年轻基线当作永久不老规定。

董文慧按28岁应急文字记录／听辨核对习惯新设计；闻素芬按44岁经营者兼修复师的审慎与工作控制感补外观候选。当前没有查到闻素芬既有人像，未冒充定型演员。两人的E02／E05服装、道具与站位是未拍场次的视觉候选，不升级剧情Canon。罗敏、高峥保留现有雨站面孔与场次素材，不重写其普通工人身份和日常行为。

## Verification And Limits

8张选用参考板逐图检查；原图／工具输出SHA与副本一致，PNG可解码，实际提交提示词均核验为中文。完整输入、剧情依据、提示词、角色职责、旧版本与SHA见 `package-manifest.json`、各套 `reference-usage.json` 和 `source-evidence.json`；实际核验见 [verification.json](verification.json)。

本组8次内置图片调用均已返回，其中董文慧场次2次有界持本手修复；旧图保留，当前采用v3。罗敏、高峥场次为2次本地文档排版导出，未另调模型。费用未暴露。当前仅静态参考候选：人类接受、视频模型实际消费和运动服从仍未验。罗敏／高峥源片带有既有CG风格影响，整理不证明全剧真人质感统一。多视图／动作资料板不自动作为视频首帧。

未改原片、剧本、Character Bible、Registry、Manifest或Production状态，未生成新视频。图片本体遵循仓库媒体惯例保留本地；Git保存说明、提示词、布局与来源／核验记录。
