# Jimeng and ComfyUI Workflows for Cinematic Stills and Short Drama

## Supersession Notice — 2026-10-14

下方Current Project Capability Mapping是研究时的snapshot。本轮原生subagent实现已补
[local masked image workflow](../superpowers/specs/2026-10-14-canvas-masked-image-workflow.md)：
typed edit_mask、latent mask、最终保护合成及canonical读回复验。Seedream云adapter仍为单场景参考；
Pose/Depth ControlNet未接通。新工程不改变两张旧图FAIL或证明原S01/S02媒体质量，实际状态以
[原单元record](../record_for_agent/2026-10-13-jieshi-original-s01-s02-candidate.md)和exact receipt为准。

## Finding

对《界蚀》S01→S02 来说，需要的是带参考资产、空间布局、局部编辑和逐镜验收的生成工作流。前两张纯文本静帧的实际问题包括缺人、重复倒影、机位偏离及额外标题；增加形容词不会增加结构输入。下述创作者案例使用角色/场景参考、构图示意、分段生成与局部修复，不能据少数案例断言社区普遍采用或已经稳定有效。ComfyUI 是否必要取决于它能补什么实际条件，而非是否有节点界面。

**结论：**先补齐角色身份、地铁车厢布局/窗面反射关系、镜头构图和 clean plate 的可核验资产。使用既有 Harness 编排生成工作流；适合的图像条件或局部编辑能力经现有 adapter 接入。S01 禁止额外片头或烧入“界蚀”标题，原句字幕由既有 canonical composition 制作；不能为研究另创片名需求、镜厅场景或第二 renderer。

没有查到一手材料证明某个流程能稳定解决该地铁车窗中七个完整倒影、唯独林砚及其左手缺席的关系。当前研究没有新增图片/视频 POST；两张既有失败图的 verdict 保留。

## Evidence Scope

这里把“一手社区材料”限定为创作者本人发布的流程、制作复盘或可见作品说明；官方 ComfyUI 文档和官方工作流 JSON 用来确认节点实际能约束什么。商业教程的目录只能证明教程覆盖了哪些环节，不能单独证明质量。搜索结果中的 SEO 汇编、转载和代理商页面不作为实际成功证据。

即梦/Dreamina 消费者产品界面、火山引擎 Ark 的 Doubao Seedream/Seedance API、ComfyUI 本地模型工作流、以及通过自定义节点调用云 API 是不同执行面。Ark 文档展示的是远端 HTTP API 与模型输入契约；ComfyUI 官方本地工作流需要加载本地 checkpoint、VAE 或 ControlNet 权重。把 API 请求装进 ComfyUI 节点不会让云模型变成本地运行，也不证明该 API 与即梦画布的编辑能力相同。[Ark Seedance API 示例](https://docs.volcengine.com/docs/ark/seedance-2-5?lang=en) · [ComfyUI 官方 ControlNet 工作流说明](https://docs.comfy.org/tutorials/controlnet/controlnet)

## Creator Cases And Official Guidance

### 1. 12-minute AI short: identity sheets, layout sketches, short connected shots

一位短片作者复盘了约一个月制作并提交影展的 12 分钟作品。作者自己尝试后采用简化角色表：大幅正面脸部、无头的正面全身服装图、同服装背面图，并使用中性灰背景。视频提示中明确让参考图控制角色身份或场景；多角色合景先用图像模型反复找构图，仍不稳时就画简图标注房屋、人物位置、远近和相对身高，再把简图作为参考。[作者原帖](https://www.reddit.com/r/aifilmmaking/comments/1w484j8/what_i_learned_about_character_consistency_while/)

作者还报告了真实失效情况：多人物会出现高度异常、贴墙或聚堆；3 个以上地点的连续运镜常变成参考帧插值，于是改成地点 1→2、2→3 分段生成后剪接；文字描述 Dolly Zoom 不稳定，视频运镜参考在该作者的镜头里更有效。作者链接了成片，并承认人多时角色一致性仍弱。[原帖与作品链接](https://www.reddit.com/r/aifilmmaking/comments/1w484j8/what_i_learned_about_character_consistency_while/)

**对地铁开场的意义：**先画站位和距离能表达更具体的输入；但作者的例子没有镜面，也没有证明参考图能维持反射几何。这个流程保留失败证据，适合作为方法参考，不是能力保证。

### 2. Dreamina Seedance long-form test: preplanned cast and geography, then diagnose the cut

独立创作者 JQ VISIONS 对创作者 JSFILMZ 发布的 3 分钟 Dreamina/Seedance 2.5 测试做了带缺陷记录的复盘。所分析的测试先准备四名角色表、按姓名绑定角色参考和分场结构，再提交长提示；结果能保留四人和主要叙事，但作者明确把它定位成 first cut，而非最终片。[测试复盘与证据说明](https://visions.joaoqueiros.com/blog/seedance-2-5-long-video-3-minutos-dreamina/)

复盘记录了与《界蚀》问题相邻的失败：返回餐馆时地理关系镜像，窗户/人物位置偏离原轴；照片递给镜头而非目标角色；橡皮筋、折纸巾等精确手部动作被跳过或泛化。作者的补救建议是把门窗、角色坐向、道具接收者/手/终态写成空间和动作关系，必要时加入布局图或分镜；对关键动作逐镜评估、替换或剪辑。[具体失败与改进建议](https://visions.joaoqueiros.com/blog/seedance-2-5-long-video-3-minutos-dreamina/)

**对地铁开场的意义：**角色身份正确与空间轴线正确须分别验收；机位、窗面边界、人物实位及倒影对应关系需要显式参考。该材料是对另一创作者测试的分析，不是独立复现，也不是《界蚀》实测。

### 3. Jimeng tutorial series: script → character/location assets → storyboard → clip → sound/edit

Bilibili 上的即梦 AI 短剧教程系列目录，将剧本检查、角色设计/角色资源/多视图、场景设计、人物融合场景、分镜原则、多宫格分镜与优化、视频片段、配音音效、剪辑拆成独立课节。[教程系列目录（页面标注 2026-04-22）](https://www.bilibili.com/video/BV1GnopB4E8c/)

目录展示了教程的流程划分，没有可核验的成片质量、对照或镜面测试。另一份中文智能画布手册描述上传、框选/笔刷、局部重绘和导出，但页尾声明资料整理自互联网，因此仅作社区操作资料，不能当成作者亲自实测或官方 API 契约。[中文画布手册](https://runyoung0613.github.io/jimeng-tutorial/charpter/ch09-%E6%99%BA%E8%83%BD%E7%94%BB%E5%B8%83.html)

### 4. Official Dreamina guidance: one job per reference, shot-level continuity

Dreamina 官方面向创作者的动画指南建议：先定脚本和有方向/时间信息的分镜；为角色准备身份参考，为重复场景记录布局和固定物；将角色图、场景/首帧、末帧、运镜视频、音频各自分配明确作用；短镜头逐一生成并核对镜头起止帧、动作、道具、画面方向和声音；错误局限在一处时修最小单元。[Dreamina workflow guide](https://dreamina.capcut.com/ai-video/best-ai-animation-tools-for-creators)

这是产品方给出的流程指导，不是社区复现实验。它与两份创作者复盘的经验相符，但“多参考”本身不意味着多输入就更可控；官方指南也建议只加入能消除具体歧义的最少素材。

## What ComfyUI Adds

ComfyUI 的额外价值是把可见输入和图像条件串成可检查的节点图，而不是自动替导演决定镜头。官方 ControlNet 教程列出边缘图、深度图、姿态关键点和草图等条件，并说明这些条件相较纯文字能更直接约束图像结构；不同控制模型要配相应条件图/预处理，部分预处理还需要额外节点。[ControlNet 文档](https://docs.comfy.org/tutorials/controlnet/controlnet)

官方 Qwen Image inpainting blueprint 展示了真实的局部编辑路径：载入图像和 mask，接入 inpainting ControlNet 条件，输出修复图。它能限制“在哪块区域重绘”，不能仅凭 mask 计算正确的镜像人物对应、透视或文字拼写。[官方 inpainting blueprint JSON](https://github.com/Comfy-Org/ComfyUI/blob/master/blueprints/Image%20Inpainting%20%28Qwen-image%29.json) · [对应官方 workflow template](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_qwen_image_instantx_inpainting_controlnet.json)

| 需求 | 纯文本提示 | ComfyUI 可增加的输入约束 | 仍需人工定义/检查 |
| --- | --- | --- | --- |
| 镜头构图和人物落点 | 描述常被模型改写 | 画布/草图，适配的边缘或草图 ControlNet | 镜头方向、构图是否符合叙事 |
| 姿势和人物比例 | 文本对精确姿势弱约束 | Pose/Depth 等适配模型与预处理图 | 角色身份、遮挡、尺度正确性 |
| 局部衣着、脸部、镜面区域重绘 | 全图重生成可能破坏已对细节 | 手工 mask + inpainting 工作流 | 倒影应如何对应、是否引入额外人脸/肢体 |
| 原字幕与禁止额外标题 | 生成可能多出不需要的文字 | 精确字幕交 canonical composition | 原句、时序、无额外片头；不是增加片名层 |

现有官方示例证明这些节点/条件工作流存在；它们没有证明同一 workflow 对所有 checkpoint 都兼容，也没有证明它能可靠渲染指定镜面反射。对静帧可以先用布局草图、深度/姿势条件或局部修复收紧输入；若必须精确控制镜像关系和文字，使用显式合成图层/3D previs 比让生成模型“猜对”更可验证。

## Jimeng UI, Ark API And ComfyUI API Nodes

Dreamina 官方示例把参考图和局部重绘作为不同操作；参考图有明确控制职责。它说明该产品的操作方式，不能据此推断中国大陆即梦当前账号、模型版本或 Ark API 有完全相同的参数。[Dreamina 参考与局部编辑指南](https://dreamina.capcut.com/resource/image-remix)

Ark 当前官方 API 文档列出 Seedream 5.0 Pro 的单图/多图参考、交互编辑与图层拆分；图层拆分为独立模式，返回多个 PNG 层及边界/叠放信息。这里没有完成二值 mask、区域外逐像素保护或窗面几何的实际验证；坐标提示与保护遮罩不能混称。[Ark image generation API](https://docs.volcengine.com/docs/ark/image-generation-api?lang=zh)

ComfyUI 官方 Seedream 5.0 Pro 节点属于需要账号、网络的 API 节点，也提供图像编辑及分层流程；这是远端模型的图形编排入口，不是本地 Seedream 权重或可直接外挂本地 ControlNet 的证明。该页写最多14张参考，Ark 当前 Pro 文档写最多10张，不能混用不同执行面的上限。[ComfyUI Seedream 5.0 Pro](https://docs.comfy.org/zh/tutorials/partner-nodes/bytedance/seedream-5-pro)

Ark 文档的字段内容本次经官方页面搜索索引核验；普通抓取仅返回 JavaScript 提示，Chrome MCP 因现有 browser profile 占用未能打开。没有关闭或接管用户浏览器、没有登录即梦账号。界面可用性及 exact wire 行为仍未验证。

## Current Project Capability Mapping

| Surface | Current implemented input | Missing or unverified |
| --- | --- | --- |
| Seedream shared adapter | T2I；显式 opt-in 的单张 `scene` PNG，Registry bytes/SHA 绑定 | 多 identity/scene 参考、mask/区域保护、分层输出未接通；前两次实际使用 T2I |
| Local ComfyUI shared adapter | 两条 sealed Qwen/FLUX 图像编辑路线，各两个参考槽，loopback/permit/canonical committer | sealed 拓扑没有 inpaint/mask、Pose/Depth ControlNet；本窗口未验证本机模型或 service readiness |
| Harness | inspect/author/preflight、exact 输入、Provider gates、Registry/Manifest 与逐镜验收 | 工程执行成功不替代几何约束或视觉/声音验收 |
| Existing composition | `ResolvedTimeline`、字幕、音轨与 HyperFrames ownership | 未验证任意视频反射 overlay；不能另建 timeline/renderer |

映射来源为 `src/ai_video/production/seedream.py`、`seedream_reference.py`、`comfy_image.py` 与 `docs/agent-primary-contract-matrix.md`。受管 read-only Kimi invocation `fd9a2ab6-88ed-423f-9d94-f55f5c880fa8` 的 route/model/containment、report 与实际读取 SHA 均由 Parent 核验，`PARSED` 只代表可读取报告，不是画面能力验收。Parent 不采纳其“必须先生成八个实体全部可见的正常倒影底图”的推导：原 S01 要求八个角色进入构图及七个倒影，未要求八人实体全部同时可见或展示正常倒影阶段。

## Practical Reading for 《界蚀》 S01→S02

以下是保留原剧情的输入准备方向，尚未生成媒体或改变共享 schema：

1. **先固定几何：**准备俯视站位图和一张低细节构图图，标出机位、镜面平面、真实人物位置、反射区域、遮挡关系和画面边界。镜内倒影是同一演员的视觉副本；在示意中明确区分实体与反射，避免把反射误当成新增角色。
2. **再绑定身份和画面角色：**每个出镜演员用单人身份图；在镜头图中给演员稳定编号/位置，并说明谁在镜外、谁只出现在反射里。不要把八个人的身份表直接当成八人构图控制图。
3. **先验 S01 首帧：**首帧就有七个完整倒影，林砚位置为空，左手空、右手手机；采用坐姿眼高斜侧中广景，禁止额外标题。原文 clean plate 必须能只处理林砚映像并保护其余七个；不能用全图重抽冒充遮罩控制。历史 `historical-opening-review` PNG `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb` 本次实际看图，构图/窗面接近目标，可供布局审阅，但身份道具/几何尚未逐项通过，不能直接作为 accepted S01。
4. **只在需要时加 ComfyUI：**若草图或画布图生图仍不能保住人物落点，才评估匹配模型的 pose/depth/sketch conditioning；若基础图大体正确但局部镜面或服装错，再用局部 mask 修复。每次只改一个主要变量，便于确认哪项约束生效。
5. **按原合同逐镜推进：**核对八个身份的实体/倒影职责、七倒影唯一对应及林砚缺席、道具/手、摄影、动作、声音和字幕。S01 exact MP4 经 project-local video-analysis 全项 PASS 后，才提取实际接受状态并绑定 S02；S02 仍需自身 QA。不能提前另做一张任意 S02 起始图替代真实交接。

这是结合原合同与公开方法的准备方向；尚未封存新的 exact 输入/permit，也没有本项目画面测试结果。

## Sources Inspected

| Source | Type | Published / inspected | How it was used |
| --- | --- | --- | --- |
| [Reddit: 12-minute AI short film creator retrospective](https://www.reddit.com/r/aifilmmaking/comments/1w484j8/what_i_learned_about_character_consistency_while/) | 创作者本人帖子及作品链接 | 页面显示约 2026-09；查阅 2026-10-14 | 角色参考、多人合景/示意图、跨地点和运镜参考，以及作者承认的失败 |
| [JQ VISIONS: Seedance long-video test analysis](https://visions.joaoqueiros.com/blog/seedance-2-5-long-video-3-minutos-dreamina/) | 个人创作者对另一创作者测试的复盘 | 文章标注资料更新 2026-08-04；查阅 2026-10-14 | 四人/分场测试的镜像地理、道具对象、微动作失败；不是原始测试作者的复现 |
| [Bilibili: AI short-drama tutorial series](https://www.bilibili.com/video/BV1GnopB4E8c/) | 即梦教程系列目录 | 搜索索引标注 2026-04-22；查阅 2026-10-14 | 页面正文抓取失败；仅据搜索索引列出的章节核对流程覆盖范围，没有把目录当质量证据 |
| [Dreamina: consistent-character workflow guide](https://dreamina.capcut.com/ai-video/best-ai-animation-tools-for-creators) | 产品方指南 | 页面未给清晰发布日期；查阅 2026-10-14 | reference 分工、shot-level continuity 与修复流程的官方产品建议 |
| [ComfyUI ControlNet tutorial](https://docs.comfy.org/tutorials/controlnet/controlnet) | ComfyUI 官方文档 | 滚动文档；查阅 2026-10-14 | 条件图类型、工作流和预处理边界 |
| [ComfyUI Qwen Image inpainting blueprint](https://github.com/Comfy-Org/ComfyUI/blob/master/blueprints/Image%20Inpainting%20%28Qwen-image%29.json) | Comfy-Org 官方 workflow JSON | 滚动仓库；查阅 2026-10-14 | mask 与 inpainting ControlNet 的节点连接事实 |
| [ComfyUI workflow template: Qwen inpainting ControlNet](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_qwen_image_instantx_inpainting_controlnet.json) | Comfy-Org 官方 workflow template | 滚动仓库；查阅 2026-10-14 | 本地模型/ControlNet 模板结构与局部编辑用途 |
| [Volcengine Ark image generation API](https://docs.volcengine.com/docs/ark/image-generation-api?lang=zh) | 官方远端 API 文档 | 官方页面搜索索引；查阅 2026-10-14 | 单图/多图、图层拆分字段与坐标交互能力；未验证 mask 或区域保护 |
| [ComfyUI Seedream 5.0 Pro](https://docs.comfy.org/zh/tutorials/partner-nodes/bytedance/seedream-5-pro) | 官方 API-node 教程 | 正文；查阅 2026-10-14 | 云 API 节点/编辑/分层；参考数量与 Ark 文档不同，未混用 |
| [Dreamina image remix](https://dreamina.capcut.com/resource/image-remix) | 产品方指南 | 正文；查阅 2026-10-14 | 参考图职责与局部编辑的产品指导 |
| [中文即梦智能画布手册](https://runyoung0613.github.io/jimeng-tutorial/charpter/ch09-%E6%99%BA%E8%83%BD%E7%94%BB%E5%B8%83.html) | 社区资料整理 | 正文；查阅 2026-10-14 | 框选/笔刷等操作资料；作者声明互联网汇编，不作一手实测 |

## Limits

- 公开帖子和教程样本少，创作者使用的模型版本、界面、提示语、素材及剪辑能力不同；单个成功例不能推广为稳定能力。
- Reddit 作者虽链接成片并给出制作细节，仍属自述；JQ VISIONS 分析的是 JSFILMZ 的一轮测试，不能当作独立重复实验。
- 官方工作流只说明节点图和条件输入存在；未在本机安装、运行或验证模型，不据此声称当前主机具备相同能力。
- 没有找到带可复现输入/输出、能解决该地铁七倒影与林砚缺席关系的案例。候选工作流的实际效果仍为 **NOT_EVALUATED**。
- 本文不判断账户功能当前开放情况、费用或资格，也不把即梦 UI 功能推断为 Ark API 或 ComfyUI 能力。
