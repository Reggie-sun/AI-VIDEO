---
record_kind: research_note
topic_id: fanxiang-v36-v37-production-loop
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Fanxiang Short Motion Reference Preflight

Date: 2026-10-06

## Decision And Scope

按用户要求改为一条最短动作视频加少量外观图片，准备并核查输入，**没有付费生成、上传、permit、
新Production intent、activation或成片导出**。目标仍是明确电脑键盘命中、即时受力和撤退；
用户已经拒绝省略接触，“兄弟们”声音需调整，均未因本次准备而通过。
13.875s基线和13.375s历史备选SHA重验不变，原对白/SFX/生成历史不改。
这次新发现画布已有可读命中的V37，取代上次“必须先人工拍接触示范”的提议；不是再次暂停记录。

**输入组合可行，当前源片尚不具备无条件付费接镜条件。**V37提供可读动作闭环，但其挥击画面方向
与当前保留版不同，撤退依赖一次切景，且有“AI生成”标记。不能把少量图片参考当作硬纠正这些问题的能力。

证据前缀`R = runs/fanxiang-motion-reference-preflight-20261006-005/`，参考准备与审片入口均local-only。

## Actual Canvas And Selected Window

已登录画布当前仍为《反相之地第一集》，94 nodes。只读选择V37并读取其current resource，
没有生成/修改节点或连线。node `node_fb5ad70k79`、resource `b2b4385b-3277-478f-80f0-16697ae4a76b`
与既有exact capture一致；`R/live-canvas-node.json`保存当前浏览器观察，不含signed media URLs。
原下载文件`runs/jimeng-fanxiang-analysis-20261002-001/media/v37.mp4` SHA
`65cb5e6889b3824725bdaab64f2397e7b20ac39eafb6974c30c6e48b4c9518ef`重验一致。
当前resource与下载身份对齐，不声称恢复历史model/seed/request或原上传前文件。

逐帧检查原12.25–13.5s（含全部接触帧），选原PTS **[12.300,14.300)s**：
起点已经抬键盘准备挥击；约12.63–12.72s键盘端接近/接触面侧；随后头向下偏转；
约13.38s切到正面破口近景，头缩回，约13.8s后空窗。
键盘从画面左下向右上挥；B03保留版小龙在右侧，挥向左上。参考片段不是同轴线的硬首帧续拍。
V37也没有完整展示单一机位下不间断的即时后缩，不能将剪辑形成的闭环冒充连续运动示范。

派生`R/V37-motion-reference-2s.mp4`：H264、1280×720、24fps、48frames、2.000s、667921bytes、无音轨；SHA
`dbc977b5bdf9d3d3e45370082e3639556710fa88876c213fdd5d408f36accb03`。
2s为当前adapter最短输入，尾部保留少量源空窗满足下界，未循环/定格/扩时长/镜像/空间裁切/去水印。
原片PTS在60Hz timebase上表示名义24fps，`r_frame_rate=60`不等于真实动作60fps。
ffmpeg按PTS截取并重编码、整帧采样到24fps，无运动插值；不声称decoded source frames/bytes完全不变。
原片不改，`R/motion-reference-provenance.json`保存范围与派生操作，未将派生物激活为正式素材。

## Reference List And Responsibilities

精确bytes、尺寸、SHA、roles见`R/reference-list.json`。原资产均来自既有画布capture和B03来源，
`Image 4`使用上轮保存的真实第287帧（同B03 source），不新增图像生成。

| Slot | Existing Source | Responsibility |
| --- | --- | --- |
| Video 1 | 上述V37 2s派生片 | 挥击轨迹、接触时机、头部受力方向、撤退节奏；不负责演员外观、场景、声音或镜头切换 |
| Image 1 | `runs/fanxiang-production-loop-20261005-001/references/xiaolong.webp` | 小龙身份、黑色服装 |
| Image 2 | `runs/fanxiang-production-loop-20261005-001/references/elongated-gouge.webp` | 狗哥身份、苍白脸及长颈外观 |
| Image 3 | `runs/fanxiang-production-loop-20261005-001/references/keyboard.webp` | 黑色QWERTY电脑键盘的矩形厚度、按键与握持道具外观，绝非乐器琴键 |
| Image 4 | `runs/fanxiang-production-loop-20261005-001/sequence-B-contact-retake-take-01/first-frame.png` | 当前B03破窗、颈部连接、人物与机位空间；仅`reference`/`reference_image`，不是`first_frame` |

不携带声音参考、潘子/曾亮角色板、完整宿舍大景或另一段动作视频。Image 4本身可见旁观人物；
它只负责当前空间，不是静态姿态/额外人物/动作的硬继承命令。身份板与键盘图亦含参考板文字，仍有文字污染风险。
使用`R/image-reference-board.jpg`与`B03-swing-axis.jpg`并排查看，职责与限制已显示在`R/review.html`。

## Current METASO Input Support

重新读取当前`src/ai_video/production/metaso_h3.py`、tests、[METASO公开页面](https://metaso.cn/minimax-h3)
与[公开节点源码](https://github.com/meta-sota/ComfyUI-MiniMaxH3-API/blob/main/nodes.py)。
`REFERENCE_TO_VIDEO` / `metaso-h3-ref2va-v1`允许同请求图片与视频；本次拟4图+1条2s视频。
图片最多9张、png/jpeg/webp、单张≤30MiB；视频最多3条、mp4/quicktime、单条≤50MiB，
每条2–15s、全部视频合计≤15s；当前adapter为整数24–60fps，宽高256–5760、ratio0.4–2.5。
五个实文件都满足所测格式、尺寸和字节边界；完整native body另须≤64MiB。
输出时长整数4–15s、768P/2K，nominal24fps；2s输入不等于可请求2s输出。
现有adapter按text→images→media发送，按类型独立编号，图片role为`reference_image`、视频为`reference_video`。
未创建本轮resolved request/paid preview；本次只核查声明、当前测试与真实素材metadata。

该API/adapter没有独立motion-only开关、运动权重或“图片只管外观”的硬权限字段。
[MiniMax参考指导](https://huggingface.co/MiniMaxAI/MiniMax-H3/raw/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md)
允许从图片定义外观、从视频定义动作的语义拆分；这是表达方法，不保证模型忽略源cuts/text/look。
Ref2VA不能同时携带hard first/last frame；当前I2V variant的`media_capabilities=()`。
上轮contact及B-04 actual requests的continuity/hard_cut bindings均null；本轮没有削弱既有FULL gate，
若正式准备发现hard FULL obligation，原契约应阻断，不为参考输入改Router/continuity架构。

## Difference From B-04

直接核查`sequence-B-take-04-motion/reference-slot-map.json`、`motion-reference-directive.txt`和actual resolved request：
旧Video 1是V37全段派生14.959s/359frames，SHA
`9b9c7d8958e6d93d9b792392fed11acfe41002a6f780a720386cc3fab6bf1194`；7图、5792字符、原九分镜、15s输出、Context IRtrue。
旧directive明确“镜头顺序和时间以以下原分镜为准”，动作视频处于从属地位，原时间表与源剪点有矛盾。
当时实际输出只有局部击打改善，攻击对象/节奏失败并有水印；不归因于某一参数，也不改写FAIL。

本次只留下一个完整反击动作和4张职责明确的图片，动作顺序与相对节奏由短视频提供，
不重新描述九个镜头、不开启第二个文字时间表、不要求取键盘/扑击/整段撤退或剧情后续。
Context IR暂沿用true，不将本次实验扩成开关比较；输入片段/图数量/文字scope等仍同时改变，
未来一次候选只能判断此配置是否满足要求，不能隔离单变量成功原因。没有编写新native prompt或改历史prompt。

## Minimal Execution Proposal

当前不建议立即付费：先确认如何解决参考的反向挥击与切景、水印污染风险。
不以镜像全片冒充轴线修复：那会同时翻转门窗位置；不靠加长prompt保证自动纠正。
保留此次最短源窗供审查。可恢复条件是同当前轴线、可连续读到接触后缩且不依赖源切景的动作参考，
或用户明确决定进行这一个有上述已知风险的动作继承试验。后者仍不放宽最终命中/空间/无文字要求。

参考确定后，仅走原Registry/derived provenance、Shot intent、compiler、exact preview和Paid Gate。
建议4s/768P、参考模式、1条无声motion+4图、无first/last帧；只发生一次挥击→接触→即时偏转后缩，
不引入取键盘或其他事件。先展示参考与起止姿态及exact输入，**再等用户授权最多1次视频提交，0次图片/音频生成**；
旧I2V授权已经消耗，当前授权只覆盖准备。失败/未知结果不自动重抽。
成功fetch后，显式project-local media Gate，既有SourceUseEvidence/Timeline/P4/HyperFrames接回保留基线，
整段1×检查动作继承、左右方向、头颈与破窗连接、电脑键盘、接镜与重复状态/文字水印；
声音另待用户听辨，不覆盖原对白，不以单镜或播放/波形成功宣布整片通过。
选用时长和最终切点由新真实画面决定，不能先宣称固定0.7s足够继承整条动作。

## Minimal Blender Replacement

**可以作为后续motion source制作方法；METASO对本白模的动作迁移尚未验证。**
最小只需要一个固定匹配B03轴线的相机、墙面/关闭门/已破上亮窗的粗几何；一个攻击者的躯干、
肩/肘/手简易关节；一块带少量电脑按键轮廓的矩形键盘，刚性跟随手；狗哥头椭球、
连到窗外躯干的长颈3–4个控制点/简单bone链。破口、头、键盘在接触时同时可见，不做只会旋转的悬浮头。
灰色平光即可，不制作脸部身份、衣料贴图、指尖/毛发/完整宿舍，也不模拟碎玻璃或开发通用系统。

48frames/24fps/2s，一镜：已握好键盘→肩肘带动挥击→键盘端到脸侧一次明确接触→1–2帧内头沿力偏转→
颈部保持连接并立即回缩到同破口外。接触处手工约束无穿模、键盘不变形；用位置/旋转关键帧即可，
无需刚体/碰撞求解器。保留参考节奏，末段只短暂稳住，不能长停顿或跳切代替后缩。
白模替换Video 1而非再加第二视频；4张身份/外观/空间图不变。当前只说明，**没有调用Blender或制作新动画**。
历史Seedance Mini机械机器人白模实验证明另一exact模型/源的路径，不能资格化本H3人体接触。

## Verification And Publication

`R/mcp-reference-probe.json`与显式MCP 8帧抽看，Parent另外查看原contact逐帧板和当前B03方向板。
`R/normal-speed-reference-playback.json`记录本地Chrome真实1×静音播放2s至ended、wall2.0007s、0掉帧、47张实际捕获；
Parent查看`normal-speed-reference-contact-sheet.jpg`。仅为参考片观察，不是生成镜头/成片验收或听辨。
58个现有METASO adapter tests PASS，`R/metaso-adapter-verification.log`保存结果；不证明live运动迁移。
受管Kimi deep `5bdd63e2-791e-494a-8d4e-e90eeafee85e`只读当前adapter/tests与B-04两份输入，
163.228s/2 wire requests，Parent核验seal、observed Reads与canonical report SHA；
文本审查没有看听媒体，2s下界与continuity问题由Parent核对实际probe/原请求，裁决保存在`R/kimi-parent-adjudication.json`。
Implementation Review Risk Gate未触发：没有产品代码/共享契约/安全权限变更。
本地记录检查receipt：`.agent/harness/runs/fanxiang-short-motion-reference-preflight-20261006/receipt.json`。
`record-ai-video-session`新参考准备达到稳定停点；`distill-ai-video-learning`评估`no_candidate`：
只有旧同一失败链的新源窗诊断与未执行提议，无独立H3动作继承实验，也无匹配的既有学习claim需要变更。
记录local commit，媒体/方案local-only，无push/release；H3媒体调用0、图像/音频生成0，不修改Skill/Policy/Gate。
