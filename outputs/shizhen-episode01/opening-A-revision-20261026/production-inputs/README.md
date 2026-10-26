# Macro Entrance Production Input

## Recommended Direction

推荐“同一道路的夜班流动”：看见城市运输和照明仍工作，视线沿真实交通路线收束到候车两人。
宏观的意义来自同一空间里其他人的生活继续，不展示更多失踪、全城同步异常或谜底。
新段落预估只需约 4–6 秒的有效剪辑；生成时长由真实机位、运动和可用模型档位决定，不锁对白。
现有 17.375 秒核心可直接接入；不重生成已成立的消失事件。

三条结构的取舍：

| Direction | Viewer experience | Decision |
| --- | --- | --- |
| 同一道路远景→可定位站棚→事件→同站台空位片名 | 先看到世界运行，再意识到世界不记得某人，保留A的视野 | 推荐正式方向；缺真实宏观素材 |
| 更高城市航拍→多个场地→站台 | 规模变大，但空间及事件联系不足、推迟第一句 | 不采用 |
| 直接“两位”→异常→同站台尾声 | 最快读到关系与异常，现有素材内连贯 | 本次局部可观看版；不宣称已完成宏观目标 |

## Reference Package

`reference-manifest.json` 是本轮从 exact 原片取出的四张原分辨率图，逐张记录源SHA、帧与职责。
`station-entry.png` 为新宏观末态的空间参照；`station-reveal.png` 只用于审核事后状态，
绝不作为宏观入口，否则会提前删人；`survivor-close.png` 用于本次接缝；`optional-tail.png` 用于尾声。
原AI标识未清除。四张是审查材料，不是“四张都塞给模型”。

还可复用用户真人摄影参考：
`outputs/shizhen-episode01/live-action-rebuild-20261026/reference/user-live-action-look.png`。
只继承摄影/材质，不复制该人的脸、地铁空间、挂绳或黑边。

宏观入口所需但尚无的材料：能看见相同道路、路树、建筑和站棚的真人街区广角参考；
对应原人物识别特征的真人身份设定。现有全景只证明站棚内外可见的局部关系，不能据此声称
整个街区或高位机位已经有实证。应先补齐并审看这些材料再提交，不让空间prompt单独承担全部连续性。

## Execution Boundary

模型选择保留用户指定 Jimeng Seedance 2.5，目标 1080p、16:9；当前本地模型表为30秒上限。
`CO-WORLD.director.zh.txt` 是可交接的创作输入，尚非sealed native请求。
具体mode、exact profile、参考绑定、preview/lint、额度、durable intent/permit须沿现有工作流新封存。
本轮未生成视频、图片或音乐，未调用新付费生成；`execute_ready=false`。
不把新场景设计、图像参考或模型容量当作真人效果/空间连续性保证。
