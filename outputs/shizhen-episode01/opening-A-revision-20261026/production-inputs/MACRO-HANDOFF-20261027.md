# Shizhen Macro Opening Handoff

## Current User Decision

2026-10-27，用户看过B6后回复：“可以,宏观的准备怎么做,我准备开新的窗口”。记录为认可当前局部连看版本并转入宏观准备；不是授权新增付费生成，也不是全目标或Production验收。

只制作《失帧》独立冷开场，不含S01，不重新设计已成立的卡车遮挡、人物消失、幸存者毫无察觉、四句对白及片名。最新认可基线：

- 文件：`outputs/shizhen-episode01/fusion-B-motion-20261027/variant-ASSEMBLY-B6/失帧-独立开场-ASSEMBLY-B6.mp4`
- SHA256：`d64aef43ddb97df8387adc03bd2a6ec71d6f1d5d901942a1d97082abc84a532a`
- 21.875秒，525帧，1920×1080，24fps。前417帧是接缝修订事件，后108帧是B5第36..143帧的显影段。
- 本地页面：`outputs/shizhen-episode01/fusion-B-motion-20261027/index-assembly-B6.html`。8876服务器是否仍在运行须实查。
- 片名B5六秒原版仍保留；拼接版去掉其前1.5秒重复转头，显影未加速；尾音沿原音乐连续取样，最后1秒淡出。
- 当前原片仍有CG痕迹及AI标识；认可局部不等于整片真人质感或正式使用条件已解决。不得移除标识或误报真人重制完成。

## Read First

工作目录 `/home/reggie/vscode_folder/AI-VIDEO`。先读当前AGENTS.md、相关操作owner，再使用已有retrieve-ai-video-memory/open-video/seedance-authoring；人物参考或状态参考有实际需求时读取scenario-identity-library与scenario-seedance-storyboard，不安装新Skill。

必要资料：

1. 本文件与同目录 `README.md`、`CO-WORLD.director.zh.txt`、`reference-manifest.json`、`preparation.json`。旧目录日期不是完成日期；`execute_ready=false`仍成立。
2. `docs/record_for_agent/2026-10-27-shizhen-B-motion.md` 的B6与用户最新认可章节；`docs/superpowers/plans/2026-10-27-shizhen-B-motion.md`。
3. `.agents/skills/open-video/references/creative-completion.md` 的Cut Relationships And Reused Footage，以及 `docs/visual-quality-gate.md` 的Assembly Harness Entry。
4. 当前完整剧本/世界观owner。其他窗口正在修订系列设定，先核对当前版本，不根据旧草稿增加异常规则、提前揭露身份/来源/反转。

## Recommended Creative Direction

延续A的空间视野：“同一道路仍在运转”。以同一雨夜街区的夜班交通/值夜灯光建立公共生活，再让车流路线、可辨认的站棚和声音把注意力交给等车的两个人。观众经历消失后，能重新理解刚才那套毫无反应的日常秩序。宏观的意义来自与事件的关系，不靠额外失踪、全城停电、屏幕故障或谜底暗示。

建议先为约4–6秒有效入口准备素材，绝不强凑时长或30秒生成上限。是否一个运动镜头或两个有动机切镜，由真实空间及生成可行性决定；不要求飞穿玻璃、不默认无人机俯冲。若新增段没有比直接进入“两位”增加有效理解，应先改设计，不靠堆城市空镜证明宏观已完成。

完整结构候选：同街区夜间流动 → 能定位的站台两人 → 当前消失事件 → B6空位显影片名。首先解决入口；暂不机械在片尾再加一段城市，以免冲淡已认可的收束。

## Reference Preparation

先审看实际视频，制作同一空间的参考组，再准备生成输入。以下是参考职责，不是三个固定摄影镜头，也不要求全部塞给模型：

| Reference | Purpose | Status |
| --- | --- | --- |
| 同街雨夜宏观构图 | 明确道路方向、站棚所在位置、冷暖光、建筑/树木及交通路线；真人摄影感 | 缺失，需设计与作图；新扩展街区是设计，不冒充原片已拍到的地理证据 |
| 由街区向站台收束的中间状态 | 检查站棚始终可定位、运动能把目光交给两人；避免从无关城市突然跳到站台 | 缺失，必须与宏观图共用同一空间，不独立随机生图 |
| 与事件首帧相接的末态 | 核对男人左/女人右、服装、包、持电话、棚柱、路树、灯带、雨量和交通方向 | 已有 `references/station-entry.png` 可作事实锚点；其源A1第8帧，SHA见manifest |
| 真人摄影质感参考 | 只约束摄影、肤质与材料，不复制参考人物身份、地铁、挂绳、黑边 | `outputs/shizhen-episode01/live-action-rebuild-20261026/reference/user-live-action-look.png` |

先给用户看宏观、中间态、接入态的成组图，确认空间和电影表现，再做视频。至少覆盖必要中间过程，不用一张漂亮终态承担所有参考职责；具体数量按未覆盖信息决定。宏观人物若只是小比例远景，先复用已知站位/衣着，不为了凑参考数量重做全套角色。若需要可辨识脸部，则先解决真人身份与既有素材的兼容，不能直接换人。

`station-reveal.png`是事后仅一人的审查图，不能作为入口模型参考导致提前漏人；`optional-tail.png`源帧288早于回答近景361..527，不能直接拿它拼接。B5拼接的回正再转头问题已在B6修剪，禁止恢复失败入点。

## Sound And Cut Preparation

保留已有Suno“缺席的应答”，不新生成音乐，不默认让音乐铺满宏观段。入口先用有空间指向的雨夜交通声，收束到站台原环境声；是否提前进入第一句，须在真实素材到齐后验证注意力、口型及一次完整对白，不能重复台词。

宏观末态与事件首帧须逐项检查源时序、轴线、人物朝向/持物、动作阶段、车辆路线和速度。若宏观出现同一辆车，必须是路线推进，不可提前演一次遮挡再重复演一次消失。切点前、入态、切后下一动作都要审；单张状态一致不足以通过。新拼接再次走既有ResolvedTimeline/HyperFrames和verify-assembly，不继承B6对新增接点的认可。

## Generation Boundary

用户指定即梦Seedance 2.5；旧准备写有最高30秒，但实际模式、上限、参考能力和费用边界应按当前selected profile/运行证据重新核对。中文Prompt，16:9/1080p项目既有规格。平台限长不是艺术时长。

目前没有新的宏观视频，也没有已经绑定的提交请求。用户此前明确“未经授权不新增付费生成”，此次“准备/开新窗口”没有撤销该限制。可先完成导演设计、参考职责、首中末状态、Prompt、cut contract及实际工作流准备；新增付费图/视频/音乐必须遵守用户明确边界。图像工具调用也需先核对授权与计费，不能自动称免费。无新付费授权时交可执行准备，不能冒充正式镜头。

正式执行前沿原生工作流封存mode/profile、exact参考及哈希、preview/lint、当前计数/预算、durable intent/permit。旧prose不是sealed native request；旧credential不授权新费用；UNKNOWN历史不重试。生成后显式video-analysis逐镜审查，再生成/拼接后续。

## Next Window Deliverables

1. 核对B6与世界观边界，给出宏观镜头的具体叙事增量和接入方式。
2. 制作并审看同空间宏观/中间/末态参考组；在授权允许的工具范围内实施，缺授权则先完成可执行输入。
3. 将既有中文导演稿更新为可生产的模型输入及明确参考绑定，列出仍缺的许可/素材，不提交付费任务。
4. 有素材后制作真实动态候选，先验宏观本身及入口接点，再与B6连看；旧B6不覆盖。

## Workspace And Acceptance State

当前有其他窗口的剧本、S05和shared generation源码改动。先git status，严禁git add .、清理、回滚或夹带。当前本窗口own的规则/片名记录/媒体脚本仍有未提交文件；最新72项focused测试仅覆盖open-video及assembly evidence入口，完整工程验证/owned commit/push尚未完成。用户现在认可B6可记录，但不能伪造此前NOT_EVALUATED的机器报告或把认可扩展到宏观。切窗交接优先保存事实，新窗口对工程收尾单独核对scope与验证，勿把无关dirty tree当作本任务。

既有原始frame/assets、B4/B5/B6及被拒的B5拼接版本全部保留。B6技术凭证、播放与独立抽帧记录在 `fusion-B-motion-20261027/qa/`；总体宏观、真人一致性、正式使用与完整Production验收未完成。
