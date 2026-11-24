---
record_kind: media_experiment
topic_id: iris-ep01-agentcut-ev-layout-round1-checkpoint
learning_eligibility: eligible
evidence_index_version: "1"
---

# IRIS EP01 用 Agentcut 复刻 EV 版式第一轮（歌 0–59.23 s）：并行候选，未审看、未导出，v4r10c 仍是唯一已认可版本

Date: 2026-11-20（本机日期；数字与哈希取自磁盘文件，核不到的标 NOT_EVALUATED）

## Supersession Notice — 2026-11-23（部分取代，本记录仍可检索）

后续证据见 [2026-11-23 s015–s030 拍摄与剪辑检查点](2026-11-23-iris-ep01-s015-030-shoot-and-assembly-checkpoint.md)。下列当前面向的说法已被取代，原时序与测量作为历史保留：

- **「没有得到用户对本版的任何表态、未审看、未导出、v4r10c 仍是唯一已认可版本」**：本记录的并行候选（stills 烘焙 + v4r10c 画面，`pic-print`）此后没有成为当前样片。2026-11-20 起开头改用 Seedance 视频；2026-11-21 使用者审看了后续 Agentcut 版式版本（v2c「认可，顺手修那两处小问题」，v3 导演层否定后说「开头还可以」），开头 0–59.23 s 暂定为 `IRIS-EP01-agentcut-ev-v3-000-059.mp4`（SHA-256 `38dcb0e81e097c2cd2eceb6951929f8c9bf133c031571d1f2c71ddb7afb7a226`，暂定非最终）；据 `section2.py` 头注释，该开头的画面来自 `opening_v2.py --build-3`，不是本记录的 stills 烘焙。Agentcut 版式层继续用于 s015–s030（独立项目 `iris-ep01-s015-030`），使用者 2026-11-23 认可 review-v1。
- **「0–26.05 s 板图是旧造型 L1、没有视频」「0–869 静图无 dof9 景深」**：开头已按 W1 造型用 Seedance 视频重做，这两条风险不再适用于当前样片。
- **「未导出」「导出路径下的 Agentcut 渲染器行为未验证」**：此后已导出（开头 v3 与 s015–s030 v1），页面导出忽略 `quality`（约 6 Mbit/s），H.264 对点网的色度噪点在手部皮肤上产生 6 帧单像素红色彩点，使用者改判为次要；该导出行为的证据在新记录，本记录没有重核。
- 本记录里的 Agentcut 图层事实、质感退步与去重处理、规则冲突裁决（brief 禁区优先）仍作历史证据有效。

## Purpose

记下 2026-11-20 这一轮「用 Agentcut 分析并复刻 anabology《ESCAPE VELOCITY》，再把 EV 版式套到 IRIS EP01 开头到首轮副歌」的真实状态，分清：用户请求与选择、仓库外的 Agentcut 项目、规则冲突裁决、PNG 叠层质感退步及其修复（`--v4r10c-picture` 与烘焙）、去重、已知未解决项。

这是新记录，不是 [2026-11-20 第二轮质感记录](2026-11-20-iris-ep01-v4-excerpt-round2-texture-checkpoint.md)的追加：那份记录的主题是 v4r10 / v4r10c 的观看尺度质感、闪烁与 s015，本记录的主题是 Agentcut 版式层这条并行候选线；它只读取了 v4r10c 的 SHA 与引擎，没有改变那份记录的任何结论，所以那份记录不加 supersession 提示。

本记录由 `memory-keeper` 子代理依主会话清单对照磁盘文件写成。读取了 Agentcut 项目的 `notes.md`、`project.json`、`layers.json`、`assets/references/ev-opening/{recipe.json,recipe.md,comparison.md,reference.json}` 与 `.studio/scratch/` 备份；AI-VIDEO 侧读取了 `outputs/ai-city-takeover/ep01/v4/excerpt/` 的 `build.py` 头注释、`bake_agentcut.py`、`src/bake.js`、`data/edl-v4r10c-picture.json` 与 `renders/`。重算了两个烘焙 mp4 与 v4r10c mp4 的 SHA-256，用 ffprobe 核对了帧数与分辨率。没有重跑任何渲染、QA、测试或 Agentcut 工具，没有重看影片，没有读取 `.env`，没有调用 Provider，没有 commit。

## Current Runtime Truth

- **用户请求与选择。** 2026-11-20 用户要求用 Agentcut（`https://agentcut.synteq.app/studio`）分析并复刻 anabology《ESCAPE VELOCITY》X 帖及其 Google Drive “Slopcore” 文件夹；用户选择「把 EV 版式套到 IRIS」「先做开头到首轮副歌」。`notes.md` 抄录了后两项选择；请求原话与 Slopcore 文件夹分析**磁盘上没有对应证据**（在 Agentcut `projects/` 下 grep `slopcore` 无命中），Slopcore 部分 NOT_EVALUATED，此处只当主会话转述。
- **没有得到用户对本版的任何表态。** 未审看、未导出、未听审。v4r10c（SHA-256 `e1439c068b1386d2d53e9f07f0c591d6f5b85acd42307f4019d5647448b2e8db`，本次重算一致）仍是唯一已认可版本（认可关系见第二轮记录：用户原话针对 v4r10，v4r10c 为主会话沿用）；本版只是并行候选，不替代它，也不是 P6、Final Acceptance 或 `preview_approval`。
- **Agentcut 项目（仓库外）**：`/home/reggie/Agentcut/projects/escape-velocity-replica/`。`project.json`：24 fps、1920×1080、1422 帧、只有 wide variant。`layers.json` 当前轨道（上→下）：`hud`、`ticket`、`slam`（4 clip）、`lyrics`（9）、`devices`（15）、`flash`（4）、`pic-print`（11），之后是**隐藏**的 `texture`、`grade`、`pic-motion`（14）、`pic-video`（7）、`pic-stills`（16），最下 `music`。`layers.json` SHA-256 `1ef5d0b7203860483a67e2d3effcf955268474b7a39e99540f2f7039f81f31d4`（本次重算）。声音只用母带 `assets/music/all-hands-r4.wav`，原样，本轮不做声音设计。
- **仓库外 = 不在 Git 里。** Agentcut 项目目录不在 AI-VIDEO 仓库内；其中的 `.studio/scratch/`（备份、`build_layers.py`）按 `notes.md` 说明约 14 天后被清理，以 `layers.json` 为准。

### EV 参考的来源与规格

- 参考片是本地截取的 EV 原片前 86 s：`assets/references/ev-opening/video.mp4`，SHA-256 `de30ea96b7fd576df3da999875d1a12308931b73cdba8a5f148503e0dfee0a2e`，ffprobe 1920×1080、24 fps、2066 帧、86.083 s。`reference.json` 的 `video` 字段是该本地路径，`sourceUrl` 为空，所以这条参考的来源身份只靠这个文件的 SHA，不能从磁盘证明它截自哪个 URL。
- Style Spy 导入 X 链接失败（原片 353 MB 超过 200 MB 上限）、改为本地截取后以 path 导入：这一经过**来自主会话转述，原片与失败日志不在磁盘上，NOT_EVALUATED**；磁盘只能证实结果（上述 86 s 片以 path 方式在项目里）。
- `recipe.json`：54 镜、28 事件，事件 `evidence` 字段 25 项 measured、3 项 estimated（本次用脚本核对一致）；`recipe.md` 末节有 1–15 条「可迁移规则」。recipe 是 Agentcut 工具与主会话从那一份 86 s 片得出的分析，不是 EV 作者的官方文档；3 项 estimated 没有逐帧复核。
- `comparison.md` 末尾「未查」：导出（export）未做；全部证据来自 `agentcut_capture_frames` 的 web renderer；声音未听审；EV 未用到的事件（f1910 LOCK、f1867 翻牌等）未对照；移动端 variant 不存在。

### 规则冲突裁决

IRIS brief（`outputs/ai-city-takeover/ep01/v4/brief.md`，`notes.md` 转述）的禁区优先于 EV recipe：不倒数、不编号 Look、s001 不用翻牌板，不重复 EV 的一问一答句式，画面不出现中文。落实：

- EV 解码条（规则 1，带倒计时）→ s001 masthead 划线：FASHION WEEK → ~FASHION~ INCIDENT WEEK（f0 / f11，sub 在 f17）。
- LOOK 计数（e09 / e10 / e25）→ 左上章节行「INCIDENT WEEK · CH nn / 11 · 章节名」，f493、f979 硬换。
- 倒计时组件与 Look 标题不做。
- 工单卡（左上 P0）为贯穿装置：s002 空白弹出 → s003/s004 INC-WEEK · SEV-LOW → s006 收角 → 各镜换号 → f958 整张变白 → s013 盖章 ALL HANDS。
- 与 recipe 规则 15（只许切点与裁切帧闪光）冲突处，s006 每个军鼓的 1 帧白闪按分镜表保留（不透明度 0.35）。
- 以上取自 `notes.md` 与 `comparison.md`「有意改动」一节；这些取舍是主会话的决定，用户未对其表态。

## Session Work And Decisions

### 版式层第一轮

`notes.md`「逐镜 cue」与 `comparison.md`「事件对照」：常驻 HUD（左缘标尺、底部 ticker、四角十字、章节行、右上频谱、右下 SONG 时间码）、各镜字幕与图形事件、两次 ALL HANDS 砸字（第二次 2 帧淡入）、三次强拍静图裁切与两次像素化帧等，共 15 个 `devices` 事件。对照表里目标帧与实测帧差值基本为 0，字幕基线差 −2 px；这是 Agentcut 帧捕获的测量，只证明「帧号放对了」，不代表观感。`comparison.md` 自己写明「只记测量和并排事实，不做观感结论」。

### PNG 叠层质感相对 v4r10c 退步，及其修复（本轮主要工程发现）

- **发现。** 版式层第一轮最初用预生成 alpha PNG（`texture` 轨：`halftone-cmy-4px.png` 0–979、`lines-45-4px.png` 979–1422）加 `grade` 调整轨做质感。主会话审核认为它相对已认可的 v4r10c 质感退步。原因（`comparison.md`、`notes.md`）：Agentcut 导出渲染器不支持 `mix-blend-mode`，无法复现 v4r10c 引擎里 WebGL FINAL 的打印 pass（网点随画面明暗调制、颗粒逐帧变化）。这是主会话的审核判断，没有用户表态；备份的这一状态是 `.studio/scratch/layers.before-print-20261120.json`（SHA-256 `69518ade39649a8d61c3120af62b1fd43f85dd8229be11f1d736431ba4715af9`，本次重算）。
- **处理。** 不在 Agentcut 里模仿，而是让 AI-VIDEO 的 excerpt 引擎（HyperFrames，WebGL FINAL 着色器）出画面，Agentcut 只当视频素材叠版式层：
  - 869–1421（副歌前半到结尾）：`build.py --v4r10c-picture`（`build.py` 头注释：v4r10c 的 overlay 层清空——无 console、type、devices，保留画面自带的 feed / emit 层——且无音频元素、多渲 1 帧到歌曲第 1421 帧，输出 `data/edl-v4r10c-picture.json`、`composition-v4r10c-picture.html`，直接渲到 `renders/`，不 mux）。产物 `outputs/ai-city-takeover/ep01/v4/excerpt/renders/IRIS-EP01-v4-excerpt-v4r10c-picture-036-059.mp4`，SHA-256 `6a6b8543a4bfff81c4e800e68b4872d05fe9f38e4b2514510a0a84767193ef2b`（本次重算）；ffprobe h264、1920×1080、24 fps、553 帧、23.042 s。Agentcut 里的副本 `assets/video/iris/print-869-1422.mp4` 与它 SHA 完全相同。
  - 0–868（主歌静图）：`bake_agentcut.py` + `src/bake.js` 把 Agentcut 项目 `pic-motion` 里每个 StillMove（推镜、裁切、像素化帧）在引擎里取景，再过 v4r10c 的 FINAL 着色器（颗粒逐帧变，网屏固定在画面像素上），渲成 `renders/IRIS-EP01-agentcut-print-000-869.mp4`，SHA-256 `388191cc7a1b2ac16255f2263d2fc38f27c7af4d5f540d22fa897e7b66679c7f`（本次重算）；ffprobe h264、1920×1080、24 fps、869 帧、36.208 s；Agentcut 里 `assets/video/iris/print-000-869.mp4` 与它 SHA 相同。
  - 新轨 `pic-print`（11 clip：`print-s001`…`print-s009b` 各取 `print-000-869.mp4` 的 `trimStart` = `from`，`print-v4r10c` 覆盖 869–1421），clip 均 `inheritGrade: false`；旧的 `texture`、`grade`、`pic-motion`、`pic-video`、`pic-stills` 轨隐藏、未删（取消 hidden 可还原）。StillMove 原来画在画面内的裁切白闪（0.5）移到 `flash` 轨。
- **`--v4r10c` 输出字节不变。** 主会话转述「`--v4r10c` 的输出字节不变」。本次**没有重渲对照**，NOT_EVALUATED；只有间接事实：既有 `renders/IRIS-EP01-v4-excerpt-v4r10c-036-059.mp4` 的 SHA 与第二轮记录一致、其修改时间（05:45）早于 `build.py`（08:27）改动，但这证明不了确定性渲染。
- **冷暖。** 按 v4r10c（主会话决定）。注意 `comparison.md`「影调实测」表中早先版本（PNG 叠层 + grade）的 R−B 比 v4r10c 低约 0.07–0.11、饱和低；任务描述写「冷调」与这组测量不一致，这是 PNG 叠层阶段的测量，换成打印画面后冷暖直接取 v4r10c。

### 去重

- 删除 Agentcut `devices` 轨的 `call-s013`（来电卡，1242–1255）和 `lcd-s014c`（寻呼机 10:02，1410–1421）。原因：`pic-print` 的 v4r10c 画面自带 feed 层，已把来电界面与寻呼机 LCD 画进画面，再叠一层会出现两张来电卡、两组 10:02 错位（`comparison.md`「已知问题」曾在 f1250 / f1415 记录该重复）。
- 删前完整 `layers.json` 备份：`.studio/scratch/layers.before-dedupe-20261120.json`，SHA-256 `3ad9f67f69fba9d5df1dd571339f1aa74ff742d218fa8195230e801d1459f95e`（本次重算）。
- 本次核对：当前 `layers.json` 的 `devices` 轨 15 个 clip，不含 `call-s013`、`lcd-s014c`（`lcd-s001` 仍在，那是 s001 的寻呼机，不是被删的重复）。
- 「复核截图 f1250 / f1415 单份」来自主会话转述；`comparison/print-overlap-f1250-f1415.png`（08:41）是去重**之前**的重复图证据，早于去重动作（08:43），我没有看到去重之后的复核截图，该项 NOT_EVALUATED。

## Verification And Evidence

| 项 | 证据（`comparison.md` 打印质感节，除非写明） | 层 |
| --- | --- | --- |
| 0–868 烘焙成片 | SHA-256 `388191cc…679c7f`（重算）；869 帧；帧间差分检出切点 99 166 188 231 274 318 361 406 493 536（像素化）537 625 669 702 714 747 802（像素化）803 847，与 `move-*` 的 from 与 cut.at 一致 | execution + analyzer |
| 869–1421 画面成片 | SHA-256 `6a6b8543…ef2b`（重算）；553 帧；检出切点 890 934 956 979 1078 1100 1123 1178 1211 1222 1242（来电亮屏）1255 1322 1377 1410，与 v4r10c 成片检出结果逐个相同 | execution + analyzer |
| 逐像素核对 | 随机 8 帧（种子 20261120）：两个合成在引擎无损截图的 overlay 区域外最大差全为 0；两 mp4 之间 overlay 区外均值差 2.0–2.6（两次 x264 crf 16 编码所致），小于任一 mp4 对无损截图的差 5.4–7.1；这是 `comparison.md` 转述的测量，我没有重跑 | analyzer |
| 影调与观看尺度 | 同表 23 帧的 p2/p10/p50/p90、grad240/grad160、sat；869–1421 的 grad240 对 v4r10c 差 0–0.03，仅 s010 X10a（0.180 对 0.119）、s014a（0.248 对 0.174）、s014b（0.233 对 0.154）较大，这三帧上 Agentcut 有大块文字或图形；0–868 静图 p50 31–126，s008 / s009a / s009b 明显偏亮（原图是亮灯箱 / 亮玻璃），s001 与 s005 的 grad240 0.238–0.244 高于 v4r10c 各镜（0.110–0.184）。两边都含各自的版式层，口径与第二轮记录的 `qa/grad.py` 17 帧口径不同，只在同一表内比较 | analyzer |
| 播放性能 | `agentcut_preview_check`（0–1421）：丢帧 0；拖动定位中位 107 ms、p95 163 ms、最慢 212 ms（s005 区间），去 PNG 叠层前是 35 / 62 / 87 ms，原因是新视频 crf 16 高码率 | analyzer（Agentcut 工具） |
| 去重 | 当前 `layers.json` 无 `call-s013`、`lcd-s014c`（本次读取）；备份 SHA 见上；去重后截图复核为转述 | structure（我核）+ 转述 |
| PNG 叠层质感退步 | 主会话审核判断；备份状态 `layers.before-print-20261120.json`；原因是导出渲染器无混合模式（`comparison.md` / `notes.md`） | Agent 自审（非用户） |
| 用户裁决 | 只有「EV 版式套到 IRIS」「先做开头到首轮副歌」两项范围选择；对本版画面、质感、取舍无表态 | human（仅范围） |

## Evidence Index

四条证据各自独立：PNG 叠层状态、去重前图层状态、两个烘焙成片。两个烘焙成片是同一引擎、同一 v4r10c 着色器的两段不同输入，各有自己的 SHA，不是同一实验的重复。去重前状态与 PNG 叠层状态是同一 `layers.json` 的不同时间点，已分别用各自备份文件的 SHA 作 identity；它们是项目状态文件而不是媒体，只用于登记 identity，不构成对照结论。所有行都是单条真实链路上的串行修复，没有对照臂。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentcut-png-overlay-state | native:69518ade39649a8d61c3120af62b1fd43f85dd8229be11f1d736431ba4715af9 | iris-ep01-agentcut-ev-layout-round1 | agentcut-png-overlay-texture | N/A | 69518ade39649a8d61c3120af62b1fd43f85dd8229be11f1d736431ba4715af9 | AGENT_REVIEW | FAIL | PNG_OVERLAY_PRINT_TEXTURE_REGRESSION | NEW_ATTEMPT | NONE | /home/reggie/Agentcut/projects/escape-velocity-replica/assets/references/ev-opening/comparison.md |
| agentcut-duplicate-feed-state | native:3ad9f67f69fba9d5df1dd571339f1aa74ff742d218fa8195230e801d1459f95e | iris-ep01-agentcut-ev-layout-round1 | agentcut-duplicate-feed-graphics | N/A | 3ad9f67f69fba9d5df1dd571339f1aa74ff742d218fa8195230e801d1459f95e | ANALYZER | FAIL | DUPLICATE_FEED_GRAPHIC | NEW_ATTEMPT | NONE | /home/reggie/Agentcut/projects/escape-velocity-replica/assets/references/ev-opening/comparison.md |
| agentcut-print-bake-000-869 | native:388191cc7a1b2ac16255f2263d2fc38f27c7af4d5f540d22fa897e7b66679c7f | iris-ep01-agentcut-ev-layout-round1 | agentcut-print-bake-000-869 | N/A | 388191cc7a1b2ac16255f2263d2fc38f27c7af4d5f540d22fa897e7b66679c7f | ANALYZER | PASS | NONE | NEW_ATTEMPT | NONE | /home/reggie/Agentcut/projects/escape-velocity-replica/assets/references/ev-opening/comparison.md |
| v4r10c-picture-869-1422 | native:6a6b8543a4bfff81c4e800e68b4872d05fe9f38e4b2514510a0a84767193ef2b | iris-ep01-agentcut-ev-layout-round1 | v4r10c-picture-only-render | N/A | 6a6b8543a4bfff81c4e800e68b4872d05fe9f38e4b2514510a0a84767193ef2b | ANALYZER | PASS | NONE | NEW_ATTEMPT | NONE | /home/reggie/Agentcut/projects/escape-velocity-replica/assets/references/ev-opening/comparison.md |

PASS 行的含义仅限切点一致与（869–1421）overlay 区外像素一致，不是观感、质感、清晰度或最终验收。

## Assessment

- **主要工程发现。** 「用另一个工具的 alpha PNG 叠层模仿 WebGL 打印 pass」在该工具的导出渲染器不支持混合模式时，复现不了已认可版本的质感（网点随明暗调制、颗粒逐帧变化）；有效做法是让原引擎输出 picture-only 画面、外部工具只叠版式层。这是一次具体案例的处理，不是通用规则。
- **869–1421 比 0–868 证据强。** 869–1421 是 v4r10c 同引擎同 edl 的 picture-only 输出，overlay 区外逐像素核对相同；0–868 是烘焙的静图，v4r10c 当年没有这段，所以没有已认可的对照物：它只能证明「用同一 FINAL 着色器」，不能证明「质感等同已认可」。
- **版式层测量 ≠ 观感。** `comparison.md` 所有差值、匹配分、分位都是技术测量；用户未审看，主会话「像不像 EV」「好不好看」没有人工裁决。
- **规则取舍是主会话的决定。** brief 禁区优先、s006 白闪取分镜表、s001 masthead 划线、工单卡变白等，用户都没有逐项确认。

## Remaining Risks Or Next Work

- **0–26.05 s 板图是旧造型 L1**（白色立领外套），与 26.05 s 起的 W1 灰卫衣不连续；0–26.05 s 没有视频。`notes.md` 只标出、不修。
- **0–869 静图无 dof9 景深。** v4r10c 的 X10a / X10b 用 `prep_dof` 的 dof9 版本，p001–p006、X07a–X09b 没有（`comparison.md`）；与第二轮记录「太清晰」的观看尺度风险直接相关，未做观看尺度量化对照（0–868 无 v4r10c 同帧）。
- **拖动定位 p95 163 ms**（高码率 crf 16），是 Agentcut 内审片流畅度，不是成片问题；是否需要降码率代理未判断。
- **未导出、未听审、未经用户审看。** 导出路径下的 Agentcut 渲染器行为（混合模式、字体、`RadialGlow`）未验证；`comparison.md` 提到导出器不支持 radial-gradient，s009b 暗角用 12 层线性渐变叠成，导出后是否一致未知。
- **改 StillMove 后需重烘焙。** `notes.md`：改推镜或裁切后必须在 AI-VIDEO 重跑 `bake_agentcut.py` 并重渲，否则 `pic-print` 不更新；烘焙脚本里的 `PROJECT` 是写死的绝对路径（`/home/reggie/Agentcut/projects/escape-velocity-replica`）。
- **仓库外资产。** Agentcut 项目与 scratch 备份不在 Git，scratch 约 14 天被清理；`.gitignore` 排除 `*.mp4`，两个烘焙 mp4 的跨机器身份只剩 SHA。
- **未提交。** 当前 HEAD `964cf680`。AI-VIDEO 仓库内的相关改动在 `outputs/ai-city-takeover/ep01/v4/excerpt/`（`git status` 显示整个 `v4/` 目录未跟踪），本记录也未 staged、未 commit、未 push。
- **本轮没有付费或生成调用**（主会话报告；本记录未发现 Provider 相关文件被本轮写入，但没有独立审计）。
- **EV recipe 的 3 项 estimated 与 5 处「与 recipe 文字有出入」的观察（coverline 亮度爬升等）未逐帧复核**；规则 6、9、10 本段未使用。

## Agent Guardrails

- 本版是并行候选，不是已认可版本：v4r10c 才是；不要把 Agentcut 的 capture 测量、`agentcut_preview_check` 或本记录的 PASS 写成用户认可、质感达标或 Final Acceptance。
- brief 禁区（不倒数、不编号 Look、s001 不用翻牌板、画面无中文）优先于 EV recipe；之后扩展版式时不要因「EV 里有」就加回去。
- 改 StillMove 或底图后必须重烘焙 0–868；改引擎或 v4r10c 着色器前先确认 `--v4r10c` 输出是否真的不变（本记录未验证）。
- 去重后不要再往 `devices` 轨补 `call-s013`、`lcd-s014c`，除非同时改用不含 feed 层的画面。
- 不要引用 EV 原句、不要把 Style Spy 的 353 MB 失败说成磁盘已证实。
- 本记录不创建也不采纳任何 Learning Claim；评估结论由主会话回报。
