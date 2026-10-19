---
record_kind: media_experiment
topic_id: jieshi-3d-anime-minimax
learning_eligibility: ineligible
---

# Jieshi 3D References And MiniMax S01 Test

Date: 2026-10-20

## Current S01 Generation Request

用户质疑“你确定这个是3d动漫风”。Parent承认该批更接近写实CG，尤其老人和中年乘客偏拟真；先前静态finding为空只覆盖已查的造型/道具问题，不证明鲜明且统一的动漫风或用户认可。随后用户明确“别管,反正先做了再说用minimax”“生成shot”：继续一次原S01实测，不再生图；不把这两句话当作风格验收或撤回原3D目标。

新单元证据根为`runs/canvas-jieshi-original-s01-s02-20261013-001/3d-anime-S01-live-20261020-001/`。选择official `MiniMax-H3-Max` CN、5秒、768P、9:16、balanced、reference route；实际九图应为八位角色各一张＋空车厢一张，另绑定白模video，禁止沿用旧单首帧却声称消费九图。原16项raw与38项FinalOutput要求、表演和对白保持；原3秒采用窗口不改。

白模复用`whitebox-repair-S01-20261016-002/v015/S01-whitebox-optical-v015.mp4`，SHA `8b8d1e43d5295109fceda1755bc41e005f6e927ef2b8e657d0328f288aa50e33`，720×1280、24fps、96帧、4秒、无音轨。实际再次显式调用project-local `video-analysis` MCP取probe与0/1/2/3秒样帧，确认当前bytes下的抬手与镜面布局；只负责动作、摄影和几何，不继承身份/材质/原生声音或完整1×验收。4秒白模与5秒请求的末态延续职责显式进入新source，不将生成尾帧冒称3秒切点。

初次本地准备发现新reference缺画布edges；随后发现alias只允许既有“图N”语法、需由原机械owner生成intent/progression。分别补齐普通项目数据并沿原helper适配，纯输入预检已PASS；无共享代码/Gate改动、无secret lookup或视频POST，历史拒绝保留，不计为模型失败或remote unknown。模型输入保持原source全文并追加逐素材职责，不拼贴设定图、不复制同角色多视图。

本段保留执行前意图；下文实际产物及评审取代“尚未执行”的旧checkpoint状态，旧阶段事实不改写。

## Actual S01 Result

实际attempt为`canvas-a904238183ab3b92e48782fef234a789d0da2a7e`。普通authoring/import由既有Canvas和唯一committer完成；新Project24、QA `32e284c602950d7d1cac222160ea73c24a71ed4e5c91d2368e446494ef4669d5`保留原16项raw/38项FinalOutput谓词。九张不同PNG各绑定一次，另有唯一v015白模；native route为reference，没有first_frame硬端点，未将设定图视角当作额外人物。新source保留前版全文，只追加素材职责及白模末态延续说明。

内部operator上界有据扩展450,000,000→500,000,000 microCNY，单次既有上界50,000,000不变；task ceiling10→11、此前used10与失败历史保留。此为内部封存上界，不是价格、实际账单或余额。`budget-extension.json`、`quota-extension.json`、`paid-preview.json`、`paid-authorization.json`封存本次唯一调用；零重抽、S02 POST0。不是将旧permit复用为新请求。

实际native body为25,867,306 bytes，SHA `409fa1029e743b4f5d4b99975bf393a16094c2350300cb78e34753e8f849d443`，prompt SHA `c37f2fdccfc7c841f40deff7f83c7d871bbbb48b11436b05e31d6483fbd91f29`；`creative-preflight-current.json`与`native-preview.json`保存真实9个`image_url/reference_image`＋1个`video_url/reference_video`、素材identity、semantic open/close、axis/camera/handoff及适配证据。2026-10-19 23:19:04 UTC唯一视频POST发往official CN，23:19:05返回HTTP200并解析accepted；wire body与preview hash/bytes一致。两次状态GET均HTTP200：第一次在持有提交锁时不能登记观察，随后同一task再取已知状态，不是新POST或unknown重试。最终观察为succeeded，canonical fetch只下载同一结果。

本地历史budget/quota/evaluation重复校验造成明显延迟：`submit`命令22:58:25 UTC启动，实际POST到23:19:04才发出，不能把这20分钟记为MiniMax生成时间。期间通过原owner等待核验，没有修改共享源码、绕过Guard、清空历史或发送重复任务。下载沿既有public-IP-pinned resolver seam，仅解析本次已知结果host，保留TLS/SNI、公开IP、无redirect及无credential GET约束，不改系统DNS。

| Artifact | Exact evidence |
| --- | --- |
| 原始MP4与用户可播放副本 | `3d-anime-S01-live-20261020-001/outputs/Jieshi-S01-3D-MiniMax-test.mp4`，与canonical fetched bytes一致，无剪辑、转码或重定时 |
| SHA-256 / bytes | `8b65261c5f67b29eafd470625fc0dcdad34a2669575c9d1c9d2e069556c61d62` / 6,491,139 |
| 实测流 | H.264，768×1344，24fps，124帧；container 5.184秒；AAC stereo 32kHz |
| Provenance | `submit.actual.json`、`poll.actual.json`、`fetch.actual.json`、`wire-observations.json`、`probe.actual.json` |

Parent显式通过project-local `video-analysis` stdio MCP调用`video_analyze`，exact canonical MP4、0.25秒间隔、21帧，保留`mcp-call.json`、`mcp-response.json`、`controlled-presentation.json`及`analysis-frames/`。初次bridge因外层Python缺`mcp`在实际调用前停止，错误保存在`review-error-local-interpreter.json`；换项目已有pinned分析Python后补证，未新生成视频。另检查实际首帧及最终decoded frame123；补充本地已缓存Whisper base，不下载模型、不调用远程audio-understand。转写为“林燕請在終點站下車”，不能据同音ASR代签精确发音、声线、空间感、时间窗或完整听审。

同一native `reviewer_high`完成round6/6，独立调用`video_extract_frames`看0–5秒、0.5秒间隔实际帧，未获Parent预设finding。`review-round6.json`保存4项blocking findings，Parent全部`CONFIRMED`：

- `SVID-001`：0–1秒有林砚头/身体倒影，2–5秒有抬手/袖子倒影，核心“唯独没有自己”未成立。
- `SVID-002`：0–1秒左手新增浅色带摄像头手机状物，约1.25–1.5秒抬手时消失；不符合膝上空左手与唯一手机。
- `SVID-003`：站立和坐姿均出现米白外套/墨绿内搭的苏遥形象，郭向东帽子/深蓝外套及沈嘉程卡其夹克无法逐一对应，身份布局被替换。
- `SVID-004`：林砚变为左侧小全身、中央大片空座、上方大量车顶并有底边裁切人物，未保留原前景机位与倒影空位的信息关系。

`controlled-answers.json`对全部16项给出1 PASS / 8 FAIL / 7 NOT_EVALUATED。唯一PASS只为close-anchor的“林砚在场”，不代签其身份细节、抬手或声音；FAIL为camera、identity、left-hand、phone、reflections、space、source-hover-prerequisite、3d-anime-style。最后一项是完整谓词中的身份/道具/构图保持失败，并非否认实际有3D CG渲染，也不是将审美偏好冒称客观结论。hover失败依据空手起点与道具连续性，不施加原片3秒或2.5秒硬deadline。其余7项保留未验证，完整原速视听及用户风格认可均未取得。

canonical review已通过唯一committer持久化至Manifest173，`diagnosis.json`为`all_required_observed_pass=false`，failure classes为`EVIDENCE_GAP`与`QUALITY_FAILURE`，保留1项及8项失败要求，证据hash `7839cb92f0bbcbdca839c4d47a6c48669d2707feea905dba9ec9bd77518e62ab`；不将Agent自行写的答案文件等同于已登记评审。

这是一条已真实生成、可查看但未通过原S01要求的测试片。原3秒采用窗口未渲染，未激活素材、未制作最终composition、未签P6/Final Acceptance，也不提交S02。已知内容错误不能靠同bytes补证消除；本单元唯一POST已消费，不自动扩展为新的付费修复。

唯一committer已执行有明确理由的`abandon_video_generation`，Manifest174中该attempt为`failed / video_quality_rejected`，quality rejection hash `93ae4396cf0dbcd6ee28ec6490c750ffa8e4c519a2739f5a4e79bf1b83014d07`，文件为`production/state/video-generation/rejections/93ae4396cf0dbcd6ee28ec6490c750ffa8e4c519a2739f5a4e79bf1b83014d07.json`。`quality-rejection.actual.json`与`closure-status.actual.json`保存返回证据。budget revision44仍为500,000,000内部上界，本次reservation保留`reserved`；失败关闭没有退回额度，也不宣称Provider实际费用已结算。

## Live Test Verification And Publication

本次只更新本主记录，媒体/参考/运行证据留本地run，不上传Git。`record-ai-video-session`评估record；`distill-ai-video-learning`为`no_candidate`：单次风格＋reference route多变量变化不构成受控比较，不从失败推出模型或工作流普遍能力结论，不修改Skill/Policy/Gate或全局memory。

文档exact staged Harness receipt：`.agent/harness/runs/jieshi-3d-anime-S01-live-record-20261020-r2/receipt.json`；其实际检查只覆盖文档快照，不代签视频质量。无共享实现变更，implementation Risk Gate由Parent自审，实际媒体独立复核另见round6。publication以本任务owned doc commit、push及remote SHA核验为准；所有foreign dirty路径保留。

## Initial First-Frame Scope (Historical)

用户要求“我想把界蚀做成3d动漫风在测试下minimax”。沿原S01做一次视觉风格变体：成熟国漫3D人物、材质与电影光照；保留八人布局、道具、原倒影异常、左手靠窗、右手手机、原广播与表演方向。不是全集制作、受控A/B或原S01正式完成。

选择最近实际使用的official MiniMax `MiniMax-H3-Max` CN，5秒、768P、balanced、first-frame，视频POST上限1、零重抽、S02 POST0。实际输入与生命周期仍归现有Canvas、Planner/compiler、Paid Gate、`VideoGenerationService`及`ProductionStateCommitter`，不增加共享源码、Provider、执行链或renderer。

[官方接口](https://platform.minimax.cn/docs/api-reference/video-generation-v2-create)与当前adapter均表明首尾帧模式和多模态reference模式互斥；本镜显式选择first-frame，历史v015白模保留但不绑定，不冒称其动作进入请求。原3秒采用窗口及后镜Gate保留，5秒原片不是最终3秒composition。

## Image Inputs

证据根：`runs/canvas-jieshi-original-s01-s02-20261013-001/3d-anime-S01-20261020-001/`。

Codex内置`image_gen.imagegen`完成两次有界作图：先将原PNG转成3D动漫风，发现工牌空白，再仅针对工牌恢复头像、姓名和部门。工具未暴露generator model，不猜型号。原图不覆盖。

| Artifact | SHA-256 | Observation |
| --- | --- | --- |
| 原首帧 | `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923` | 原写实布局及剧情来源 |
| `firstframe-v1.png` | `8cbde2bb5bc5c7f3079727efee64854ebb199b5539992ce5dbfe60eaf508e216` | 3D风格转换；工牌丢失内容，不能用于视频 |
| `firstframe-v2.png` | `a557098d22e737896e0a5fd75496c0b365d3cf5626081eabbc376afb8134ad65` | 941×1672，2,214,363 bytes；工牌恢复，独立静态复核未见明确新增回归 |

`image-generation-v1.json`、`image-generation-v2.json`保存实际图identity，`concept-review.json`保存同一原生read-only `reviewer_high`的概念与两版静帧复核。静态finding为空不证明视频动作、全帧倒影或声音。第二次生成不提供非目标像素逐字节不变保证。

## Authored Contract

标准reader核验旧Manifest157/Project22及既有历史后，新source在原四段前显式新增风格段、绑定新首帧，原剧情/对白/动作/表演段保留。`source.json`、`candidate-prompt.txt`、`project-data.json`、`authoring-input.json`及`author-preflight.json`保存来源与适配。新QA为`2447a4674cd6826286a7c53a4768710b25196a2caf6d089185de5ad195ee8b1d`：原15项raw要求保留，增加`s01-3d-anime-style`，共16项；FinalOutput原37项保留并增加风格项。输入预检不是模型服从或媒体验收。

## References-First Checkpoint (Historical)

用户随后纠正“你在干什么,先做referces啊”，再明确选择“直接补齐八人＋车厢”。停止视频准备，当前交付目标改为先完成独立人物/场景references。此前已通过唯一committer登记新source/QA：Manifest160 / Project23；这些authoring记录保留，不回滚历史。

本地进程中止于`ProductionPlanningService.prepare()`的标准reader历史budget/evaluation校验，尚未materialize新component或创建新video attempt；本单元无wire-observations、无预算/额度扩展、无新paid permit或视频POST。原budget revision40、内部上界450,000,000及task used10保留。不能把本地中断称为远程UNKNOWN，不能把已登记authoring称为视频或人物/场景reference验收。原S01 STOP与S02 POST0保留。

最终reference候选为八个人物＋空车厢，共9张1536×1024 PNG；原图合计18,989,416 bytes。见[本地总览](../../runs/canvas-jieshi-original-s01-s02-20261013-001/3d-anime-S01-20261020-001/references/index.html)与[索引](../../runs/canvas-jieshi-original-s01-s02-20261013-001/3d-anime-S01-20261020-001/references/README.md)。这批独立references未导入Production；前面已登记的authoring仍是旧单首帧变体，不能冒称它已消费本批九图。

reference阶段实际完成9张初稿＋4次有界修图：苏遥先修无刘海直发及持机手，再单独修背面换手；林砚修鞋面多余品牌标记并增加清晰工牌细节；陈立修回约35岁方脸短寸。另一次陈立修图因前一步本地复制尚未完成、输入文件不存在而被工具在读取输入时拒绝，无新PNG；修正本地输入后只执行一次实际修图，不记成远程unknown或模型质量失败。此前两张风格首帧保留为独立历史阶段。

| Reference | Selected file | SHA-256 |
| --- | --- | --- |
| 林砚 | `references/linyan-v2.png` | `9f415189e608d6fb9beb5567fa946fe0b8fbb24a65294f7acb584b149b3b4017` |
| 苏遥 | `references/suyao-v3.png` | `336341af057b0ef3b91ca21cddb4ec2c5046aa45f36a91b05db8742935d32932` |
| 周伯祥 | `references/zhouboxiang-v1.png` | `e858ced58324a4570c106bd2f2b5acfa2110b3c8842508213713a4ca26fc592d` |
| 陈立 | `references/chenli-v2.png` | `56000b47a5fef3a13d284ab003342bd41541b66701e022ae956cfad742c1a8ff` |
| 许雯 | `references/xuwen-v1.png` | `747575b2a2991b28d411fa3451784407d1510464ec06c5b94643e73eea22a8f2` |
| 郭向东 | `references/guoxiangdong-v1.png` | `b3e6047f3f750af378a26fbee49d0efd4dc2d9566552c77e29611e2beb37a778` |
| 沈嘉程 | `references/shenjiacheng-v1.png` | `0093dc5df662984a0d157dac7095303fe98936437c94bea3096e88459c652dcb` |
| 何静 | `references/hejing-v1.png` | `384bafc9dff74c962cd1c5162bf3699dfca7b4b7ac791a3232b9a15b4170fb99` |
| 地铁车厢 | `references/subway-v1.png` | `86c3a3267a3a66f1416d9f0d56a4a1362424112ae75896d688485702cec94fb3` |

全部PNG已实际解码、尺寸/bytes/SHA校验。人物图是同一人物的正面、斜侧、背面和表情，不是多人图；何静额外展示膝上灰袋及袋细节，车厢为空场景多角度参考，不证明原S01七人倒影已满足。完整生成与修图提示词保存在`references/*prompt*`。

同一原生`reviewer_high`的初次references复核发现苏遥侧/背视图换手及发型偏离，Parent按exact图修复。用户随后明确要求整套九图，新scope有据将同一有限审查上限3→6，历史轮次1–4保留；round5绑定上述9图，`references/review-target-index.json` SHA为`ba3145397aa825fb04ff481d2241cb96e2dcb431094c545acdc08ec7416a2df5`，不以换Agent重置轮次。复核仅判断静态reference缺陷，不代签用户风格偏好、3D几何、动作或声音。

## Evidence Boundaries

本单元同时改变首帧和风格文本、无受控seed，不用于宣称3D风格改善动作或倒影的因果结论。原写实版本及失败、消费、unknown边界均保留。`record-ai-video-session`评估record；`distill-ai-video-learning`当前为`no_candidate`，不修改Skill/Policy/Gate或全局memory。

## Reference Checkpoint Verification And Publication (Historical)

Round5实际完成全部9张exact PNG的独立静态复核，finding set为空；苏遥SREF-001/002在当前v3未再出现，Parent记录`OBSOLETE_AFTER_CHANGE`。`references/review-round5.json`与不可变`review-target-index.json`保存target及证明边界；`asset-index.json`随后仅更新review metadata，9份PNG identity保持不变。

Parent实际核验9图PNG可解码、1536×1024、bytes/SHA；HTML恰好9个有效本地图片链接；下载ZIP通过CRC检查且仅含9份selected PNG，旧稿不混入下载包。`references/verification.json`保存archive identity。PNG、HTML、ZIP及prompt留本地run；Git仅提交本主记录，不把图片上传远端。

文档范围exact staged Harness receipt：`.agent/harness/runs/jieshi-3d-anime-references-record-20261020-r1/receipt.json`；实际结果以该receipt为准，不证明模型视频、场景三维几何或用户风格认可。无共享源码改动，implementation Risk Gate为Parent自审；独立reference复核另按上述实际证据记录。无关dirty/staged工作保留。在该checkpoint完成的是用户要求优先制作的references，彼时MiniMax新视频测试尚未执行；实际新测试结果见本文Actual S01 Result。
