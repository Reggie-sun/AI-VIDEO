# Director Quality Audit

Date: 2026-10-21

## Scope And Evidence

用户怀疑近期视频的奇怪表现来自导演层。本轮核对近期制作记录、原始剧本、Director coverage、实际 native prompt、表演文字生成源码及七份本地 MP4；不重做视频、不修改 Product state 或历史验收。结论是有具体导演与输入组织问题，尚不能把全部质量失败归结为同一个模型机制。

显式调用 project-local `video-analysis.video_analyze`，关闭 transcription / audio understanding；实际查看返回的42张样帧。抽样范围如下，时间为工具报告值；机器人剪辑版工具均匀采样约0/1.004/2.009/3.013/4.018秒。另直接读取每份当前文件计算 SHA-256。抽帧没有证明完整正常速度观感、音义、自然表演或抽样间隔无缺陷，本轮没有新增 human 或音频理解验收。

| Media | Duration / sampling | Exact SHA-256 |
| --- | --- | --- |
| 护腰贴原S01 | 7.300s，0–7s每1s，8帧 | `2df69a622b9cf0e869e028b5cf4882ce5539915f22e6bb9b1bfc95904516a10f` |
| 护腰贴最新有声预览 | 2.250s，0–2s每0.5s，5帧 | `51377cd3906395792f4a8814e478d4cefe3da125088a2d837981ae13d625249e` |
| 界蚀上传画风S01 | 5.184s，0–5s每1s，6帧 | `b3fea442735a2ad0a41c795c548c05e1a27c11a804b50e740775e417e918203b` |
| 界蚀表演修补剪辑v2 | 3.000s，0–2.5s每0.5s，6帧 | `f98e2c0ab5198962450a8dca2b7b3a53c133559ebb36c2b6f511700e976f4a47` |
| 机器人原片 | 5.184s，0–5s每1s，6帧 | `0a7e9072f5bbce23f78ead55dc6ebefb477ded1d6e9518cb6a42ce19f5049bc9` |
| 机器人原声剪辑版 | 5.022s，约1s间隔，5帧 | `173cd95b4629c4d758ccf40d7725870cc8f3cca18685695fe4e0d2ef8f2ca5c9` |
| 蚂蚁旧扩写片 | 15.104s，0–15s每3s，6帧 | `265d4135906be4a8d4edfc744bc9db0233093a05ec3a4b0bc0dadda2254c3f36` |

七份文件是四个题材的样本，含原片与派生版本，不能计作七个独立实验或所有近期视频的穷尽审查。媒体路径由下列既有记录维护；本轮发现的更新文件为 `runs/hotpatch-dayoff-20261020-001/natural-sound-render-v1/output/opening-natural-with-sound.mp4`，其报告是同根任务目录的 `S01-natural-sound-render-report.json`，视觉源窗为 `S01-natural-spec-visual.json`。

## Findings

### Hotpatch Opening

[原创目标与coverage入口](../canvas-projects/hotpatch-dayoff/README.md)要求生活化、容易理解、前三秒吸引与商业完成度；24秒总长和7秒S01是Director选择。coverage的核心是长待办纸卷占据沙发、女子想坐又停、随后与伴侣对视。

实际原片0–4秒样帧主要是纸带滑动与两人低头看纸；约5秒女子开始转向伴侣，6–7秒才清楚相视。前景纸带有视觉奇观，但人物与它的直接冲突弱：画面仍见可坐的沙发空间，样帧没有清晰的坐下受阻动作；纸上的符号又不可读，独立观看未必认作待办事项。后两点是导演可读性判断，不是实测观众理解率。

实际 native input 大量采用轻微、自然平稳、subtle、温和连续推近，并禁止本镜出现商品。即使完全执行，也只是缓慢建立纸卷隐喻，再到情感反应；这与原始目标的趣味、动作反馈、前3秒节奏存在张力，不能只归咎于帧率或模型。商品是否必须在第几秒出现仍是创作选择，本轮不新增硬性规则。

[既有记录](2026-10-20-hotpatch-dayoff-edit-preview.md)已确认用户慢动作反馈及7秒首镜的导演归属，但它记载的是3秒变速静音预览。当前更新的2.25秒有声文件采用源frames0–53的identity time map；本轮样帧仍未出现原首镜的对视收尾。它证明截短，未证明原S01的完整叙事功能已恢复；也不代表完整短片完成。声音只核验有音轨，不判断实际听感。

### Jieshi Shot Design And Readability

[原S01](../superpowers/artifacts/drama/jieshi-episode-01/episode-01.md#s01--00000003--3s)将本人、七名他人的完整倒影、唯独主角缺失、左手求证、广播点名和字幕设计压进3秒。导演意图明确，但观众必须在短时间内理解实景/镜面对应和异常位置，属于高信息负荷设计。八人核对的技术完整性不能自动证明悬疑钩子一眼可读；这一点是待观众验证的风险，不是已实测失败率。

原Shot的Next/Risk已明确提出几何一致的clean plate，只删除主角映像；后来reference route又将镜面关系交给生成请求与白模引导。应区分场景构图、自然表演、倒影异常合成各自能否稳定实现。单纯增加人物身份和镜面否定文字，不能替代对这条制作路线的验证。

本轮上传画风片首帧实际可见多余手掌/浅色手机，主角对应区域被背影占据；2–5秒虽见抬手，却没有实现封存的清晰缺席关系。这些是实际生成/输入失败，不能称为有意的悬疑表现。原[上传画风记录](2026-10-20-jieshi-3d-anime-minimax-test.md)的失败不因本轮审计改变。

用户已批准原镜并要求忠实保留，Director应报告可读性与制作风险，提出保留目标的方案；本次审计不授权改剧情、删乘客、取消广播或重新生成。

### Performance And Input Organization

[表演版记录](2026-10-13-jieshi-original-s01-s02-candidate.md#current-acting-s01--2026-10-20)已记录3904字符输入、八人表演参数以及用户“我没看出来区别”的反馈；修补前后脸部ROI124帧相同，修改的是手影。当前3秒v2样帧中，主角抬手可见，背景人物主要保持原姿态，未建立可读的情绪变化证据。不能把局部去手影当作人物表演改善。

当前源码 `src/ai_video/production/performance_direction.py::render_performance_direction` 将逐人物phase、emotion、intensity、facial expression、gaze、breathing、body behavior表达为文字。参数存在、文字进入输入和QA映射成立是工程事实，仍须导演选择具有可见动机和变化的表演。实际作者大量选择subtle、固定视线、闭口、不转头、背景微动；增加逐人呼吸字段不能单独保证人物有生命感，也不能由本轮证明是僵硬的唯一根因。

上传画风candidate实际含重复素材职责、新旧4秒/5秒白模说明和反复美术方向。[当前稿控制修复](2026-10-20-canvas-current-input-control.md)已定位为上层将历史追加到新source，compiler按preserved-source合同发送。该确定性输入问题已经修复并发布；本轮不建议重复建设同一校验。修复尚无新实片效果证据，也未解决镜头取舍和情绪表达判断。

### Counter Evidence And Classification

[机器人记录](2026-10-17-generic-h3-robot-reference-pilot.md)说明这是固定机位动作/时序测试。原片约4秒才水平举臂，与封存3.5秒目标不同；剪辑版随后有用户完整听看接受的历史证据。不能用技术白模样例缺少戏剧性来证明导演失败，历史人工接受也不代本轮新的听看。

[蚂蚁旧扩写片](2026-10-11-mecha-ant-seedance480-canvas.md)的本轮样帧能看到围瓶建立、跟随主角穿叶绕石、末段群体离圈的变化，较两人站着看纸有更明确的动作推进；但3/6/9秒看见主角完整头背，明确违反主角眼睛POV。其后[原文版本](2026-10-11-mecha-fast20-original-input.md)又有已知POV偏差下的用户接受；该原文版本本轮未重新抽帧，不能把旧扩写片结论冒充新片状态。这些反例限制了“所有片子都同一种导演失败”的结论。

## Interpretation And Next Decision

最有证据的判断是：部分导演决定没有优先保证观众能看懂的动作因果、注意力和及时反馈；随后输入与验收又投入大量精力核对身份、物件、参数和局部修补。后者有必要，但不能补回前者。不存在证据证明只要换模型、加长/缩短prompt、强制多切镜或统一加大表演就能解决问题。

优先重审一个自主创作案例的开场：明确观众先看谁、人物试图做什么、发生什么可见阻碍、反应如何产生下一动作；用现有素材/分镜检验理解，不先扩建runtime。护腰贴的原始请求允许创作自主权，《界蚀》当前忠实制作约束则需要另行处理实质重导。新生成仍沿当前有限授权与原Gate，本轮无新增提交授权。

外部资料仅作适用性核对：[MiniMax官方full-reference指南](https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/h3-prompt-writing/references/ref-en.txt)要求清楚组织参考职责和播放顺序，同时容许详细描述；所以不能把“prompt越短越好”当H3规则。[Runway官方指南](https://help.runwayml.com/hc/en-us/articles/39789879462419-Gen-4-Video-Prompting-Guide)强调清楚可见动作、简洁起步和逐项迭代，属于另一模型的参考，不直接升级为本项目H3/Seedance合同。

## Verification And Boundary

本轮使用 `retrieve-ai-video-memory` experience检索后重开当前原文；七份MP4本地SHA复算与42张MCP样帧构成此次媒体观察。没有Provider生成/付费音频调用、QA签署、Production activation或完整成片交付。只新增本审计记录，foreign dirty文件由其他工作保留。

`record-ai-video-session`: recorded。自动 `distill-ai-video-learning`: `no_candidate`。这是既有异质媒体的诊断，派生文件不是独立实验；没有可归因的导演改稿前后比较，不将诊断假说升级为通用模型质量规则、Learning Claim采纳或Skill/Policy/Gate修改。

文档exact-snapshot验证receipt预定位置为 `.agent/harness/runs/director-quality-audit-20261021-r1/receipt.json`，实际结果与publication在本次交付中单独报告；该receipt不证明视觉质量或用户接受。
