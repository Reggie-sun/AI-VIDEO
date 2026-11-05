# IRIS EP01 v3 · 全长动画分镜 a1 规格（给执行代理，分镜 v2）

目的：计划阶段 5——一条从头到尾 261.56 s 可看的动画分镜，用真实的歌、静图替身＋代码镜头、基础图形与英文歌词，供使用者在阶段 B 一次看完整片节奏。**不是成片**；后续生成的视频按同一时间替换静图。

分镜已由 v1（89 单元）改为 v2（85 单元，`board: "v2"`），原因见 `board.md` 的“概念检查裁决”。

## 输入（只读）

| 内容 | 路径（相对仓库根） |
|---|---|
| 镜头映射 v2（85 单元：时间、静图、镜头运动、图形组件、视点、屏上文字） | `outputs/ai-city-takeover/ep01/v3/shots-map.json`（由 `build_shots_map.py` 生成，不要手改） |
| 分镜 v2（每单元的目的、起止状态、可见变化） | `outputs/ai-city-takeover/ep01/v3/board-table.md`、`director-coverage.json` |
| 歌（母带，必须原样作为音轨） | `outputs/ai-city-takeover/ep01/v2/song-v3/IRIS-01-T4.wav`（261.56 s） |
| 节拍、重音、段落 | `outputs/ai-city-takeover/ep01/v2/song-v3/beatmap/beats.json`、`hits.json`、`music-map.json` |
| 逐字时间（CTC） | `outputs/ai-city-takeover/ep01/v2/song-v3/timing/words.json` |
| 静图 | `shots-map.json` 里的路径（相对 `outputs/ai-city-takeover/`）；`missing_plates` 列出还在生成的图，构建时缺的先用带单元编号的深色占位并在报告中列出；**渲染前重跑一次构建**，把已落盘的图拷进工程 |
| 人物定稿与世界规则 | `outputs/ai-city-takeover/series/casting-v3/canon-v4.md`、`series/BIBLE.md` |
| 可复用的合成工程 | `outputs/ai-city-takeover/ep01/v2/comp/`（30.5 s 版）与 `motion-kit/`（`README.md`） |
| **已有的半成品** | `outputs/ai-city-takeover/ep01/v3/comp/`：上一个执行代理按 v1 映射写到一半时因账号切换中止（`build.py`、`src/` 下 anchors/boards/camera/charts/graphics/labels/lights/lyric/main/osd/util）。先读懂并复用，逐个确认完成度，不要假设它们已可用；与本规格冲突处按本规格改 |

## 映射字段（v2）

每个单元：`unit`、`t0`/`t1`（秒）、`lyric`（CTC 文本，只给审片表用）、`voice`（`lead` 唱 / `vo` 画外念白 / `inside` 刻意闭嘴 / `chant` 合唱，可组合）、`sing`、`route_final`、`viewpoint`、`scale`、`camera`、`camera_move`、`plates[{plate, from}]`、`graphic`、`graphic_text`、`graphic_note`、`objective`，可选 `target`、`cue_s`。

- `graphic_text`：**屏上要画的确切文字**（只有英文、数字和符号），原样画；多行用 `\n`。空串表示该组件不画字或用组件自带的标签。
- `graphic_note`：中文说明，**永远不画进画面**，只用于理解与审片表。
- `target`：可选，静图坐标系的归一化 `[x, y]`，给识别框、红点、门缝位置用；没有就用组件默认值。
- `cue_s`：可选，单元内关键事件的绝对时间（如 U002 6.664 s 灯亮、U042 133.538 s 升腾落点、U083 254.32 s 红点再亮）；没有就用单元内的第一个重音（hits）。

## 交付

1. 工程 `outputs/ai-city-takeover/ep01/v3/comp/`：仿 v2 的 `build.py` 组织（数据、音频、字体、底片拷入工程），`src/main.js` **由 `shots-map.json` 驱动**（按组件家族写通用绘制，不为单元各写函数）。
2. 渲染 `outputs/ai-city-takeover/ep01/v3/renders/IRIS-EP01-v3-animatic-a1.mp4`：1920×1080、30 fps、261.56 s、音轨为 T4 母带（不改音量动态以外的任何东西；如需响度对齐到 −14 LUFS 请在报告里写明）。
3. 审片页 `outputs/ai-city-takeover/ep01/v3/review/animatic-a1.html`：播放器＋每个单元的时间表（单元号、时间、歌词、声音类别、静图缩略、组件、`graphic_note`），点表格跳到对应时间。审片页可以有中文，视频里不可以。
4. 报告：实际做了哪些组件、哪些只做了简版或占位、缺图清单、渲染命令与耗时、帧数、输出 SHA-256、已知问题。

## 必须遵守

- **一切时间来自数据**：单元 `t0/t1`、`cue_s`、CTC 字词时间、节拍图；剪点量化到帧（motion-kit 契约：`frame = ceil(t·fps − 1e-6)`）。每帧是 t 的纯函数，不用 `Math.random`/`Date`。
- **三种视点**：`system` 画监控 OSD（时间码、`HALL 07 · CAM 03` 之类的机位标签、识别框、计数、状态条）；`iris` **不画 HUD/OSD**（只有歌词与必要的叙事标签）；`graphic` 是纯图形全屏。
- **不出现任何中文**：歌词层关闭简中翻译（motion-kit `lyrics.js` 的翻译行不要画）；`graphic_note` 不画。
- **唯一暖色**：图形里的强调色只用信号红 `#E3342F`；其余白/银/钢蓝/黑。红队测试室（U036–U040）不用红色。
- **镜头运动**：按 `camera_move` 用 2.5D 代码镜头做（推、拉、摇、横移、升、慢转），单元内连续、无跳变；同一底片跨相邻单元时可以延续运动。`plates` 里 `from` 是单元内按比例时间切换到第二张图（如 U005 睁眼、U025 转头、U056 翻照片）。
- **歌词层（按 `graphic` 里的 `lyric_*`）**：字词与时间只取 CTC，单元内按 [t0, t1) 取；`lyric_word` 画外念白的小号 deadpan 字幕（左下，逐词点亮）；`lyric_stack` 副歌堆叠（左侧，沿用 v2 c15 版式：Nimbus Sans Bold、左对齐、x=76、关键词信号红）；`lyric_whisper`/`lyric_tiny` 极小字幕；`lyric_chant` 大号节拍字；`lyric_flip_words` 翻牌逐词。字体沿用 v2 `comp/fonts/`，不新增未定义的字体样式。
- **图形组件**：`shots-map.json` 里出现的每个名字都要有处理（`+` 表示同一单元叠多个）。v2 新增或改义的：
  - 灯光：`light_flicker_on`＝在 `cue_s` 之前把画面里的红色压成灰，到点闪两下后保持红（U002、U083）；`gap_dim` 门缝红光渐暗；`gap_close_mask` 门缝收成一条线再熄灭（x 取 `target`）；`spotlight_snap_on` 顶光硬切亮、曝光跳一下；`red_dot_flicker` 黑暗里一个红点闪亮；`red_off` 整个单元压掉红色（门已关、全部熄灯）；`fade_to_black` 在 `cue_s` 附近把画面压黑（U059 手盖住镜头）。
  - OSD：`osd_detect_lost` 框闪一下后丢失目标；`osd_glitch` OSD 文字与色块错乱；`osd_status_resetting`；`monitor_frame_city` 标着 `CITY CAM` 的监控画框。
  - 线与图表：`redline_retract` 门到城市的那条红线断开、缩回；`timing_chart_flatline` 两条波形同时归零成直线。
  - 缓存：`photo_flip_cached` 灰色定格的城市照片像翻牌一样翻过（用该单元 `plates` 的几张图，去饱和）；`tag_cached_timestamps` 漂浮薄片上的小标签。**不要编造日期或数字**，只画 `graphic_text`。
  - 其余名字沿用 v1 家族（OSD、翻牌、标签/印章、灯光、示意图、invert/monitor/reflection/breath_fog/fingertip_light_trail/black 等）。时间不够时先保证每个家族有一个可读的通用版，细节在报告里列出。
- **文字内容**只能用 `graphic_text` 与 CTC 歌词里的字；事实卡（U084）的文字以 `graphic_text` 为准，逐行出现，不得增删事实。
- **范围**：只写 `outputs/ai-city-takeover/ep01/v3/comp/`、`ep01/v3/renders/`、`ep01/v3/review/`。**不要修改** `motion-kit/`、`ep01/v2/`、`src/ai_video/`、任何 `tests/`、`shots-map.json` 与 `build_*.py`；需要 motion-kit 没有的能力，在 v3 工程内新增本地模块。不读写 `.env`，不调用任何生成或付费服务，不 commit。
- 渲染用仓库既有的 HyperFrames 路径（看 v2 `build.py` 与 motion-kit README 的做法）；跑 motion-kit `tools/qa.py`（若适用）并报告结果。全长渲染前先渲 3 段各约 10 s 的样片（如 0–12 s、54–68 s、155–170 s）自查：视点规则、无中文、歌词时间、红色规则。

---

## a2 修订（2026-11-04，Codex 审核 REVISE 后）

依据：`ep01/reviews/2026-11-04-codex-animatic-a1-review.md`（Codex 意见与主会话裁决）、使用者两项决定（门缝红光保留并补进定稿；预副歌二保留闭嘴）。a1 的文件保留不动，a2 另出：`renders/IRIS-EP01-v3-animatic-a2.mp4`、`review/animatic-a2.html`、`qa/animatic-a2/`。

### 映射变化（`shots-map.json`，`board: "v2-a2"`，84 单元）

- 终副歌最后一句与尾声句的 CTC 时间已按人声分轨的实际发声重对齐（`song-v3/timing/words.json`，旧版 `words-ctc-v1.json`）：最后一句 211.85 s 唱完，213–222 s 是器乐。U072–U077 因此重排（U073 监控墙改为不唱的凝视，U074 改为器乐段的动作）。**歌词层必须重新读 words.json**。
- 结尾重排：U082 翻到 03:48 → U083 事实卡（252.46–258.16，四行，停住可读完）→ U084 黑暗方阵里红点再亮后收黑，是全片最后一个画面。U085 删除。
- 新组件：`nodegraph_control_gap`（U013：承接 U012 的节点图，MODEL 外一圈 CONTROL 边界，DNS RESOLVER 标红 MISCONFIGURED，边界在那里裂开，线从缺口穿出）；`nodegraph_single_endpoint`（U017：缺口外的线只接到一个亮起的节点 EXTERNAL CHATBOT，其余节点灰着，小字 LIMITED；不画城市全景）；`spotlight_flicker`（U074：探照灯在 cue 处闪一下）；`fade_out_end`（U084：单元最后 0.8 s 收黑）。
- 同一句两机位：U020、U044、U046、U067、U072 在单元内按 `plates[].from` 切到第二张静图（同一段唱、不同景别）。U025 原本就是两张。
- 屏上文字改动：U004/U082 翻牌下方小字 `IRIS CLOCK`；U010 加 `INDEXED, CACHED PAGES`；U028 改 `STRONGEST MODELS · RELATED WORK PAUSED`；U069 是天花板监控画面（`CAM 07`）。

### 剪辑界面层（新，全片贯穿）

映射顶层 `chrome`：作者 EV 那样的持续界面，属于剪辑层，**不是**剧中监控 OSD（监控 OSD 仍只在 system 单元）。
- 四角对位细十字、左上 `top_left` 与 `counter`（按 `from` 切换）、右上 `top_right`（按 `from` 切换）、底部滚动条 `ticker`（五行英文事实循环向左滚动，速度要能读）。
- 字体：等宽大写、约 12 px、字距放宽（作者用 IBM Plex Mono 500；本机没有就用已装的等宽字体并在报告里写明）。颜色随底色反差（暗底浅字、亮底深字，U053/U070 白底时变深色）。
- `dim_units` 内界面层降到约 40%；`no_ticker_units` 内不显示滚动条。

### 版式按角色分工（参考 `outputs/anabology-opus55-replica/escape_velocity_analysis/visual_system.json` 的 typography_summary 与 keyframes）

- **画外念白、画面单元**（主歌一句一图里有静图的单元）：作者式大号句式标题——Nimbus Sans Bold、句首大写、左对齐 x≈76、大写字高约 60–70 px、行距 1.0–1.1、关键词信号红；一句一行，逐词随 CTC 点亮。
- **画外念白、纯图形单元**（翻牌、节点图、时序图）：保留小号逐词字幕，避免和图形重复。
- **唱句**：沿用 c15 堆叠（Nimbus Sans Bold 72 px、x=76、关键词红）；长音上的关键词可以放大成窄体动态字（Nimbus Sans Narrow Bold 之类的高窄粗体）。
- **Drop 合唱**：高窄粗体全大写大字，随拍。
- **耳语／桥段**：保持极小。
- **系统图解与标签**：等宽大写；红队测试室的 `SEPARATE · CONTROLLED RED-TEAM TEST` 与 `PROCESSOR CACHE` 放大到 1080p 下一眼能读（大写字高 ≥ 28 px），且不用红色。
- **黑白反转**：白底黑大字。

### 修正

- U002：cue 之前红色压成完全的中性灰（现在是暗橙线），cue 后闪两下保持信号红。
- QA 对拍（a1 的 4 个 FAIL）：U004 翻牌落定要在 cue 帧（现在早 3 帧）；U053 剪点、U056 两次换图各晚 2 帧，修到 ±1 帧以内。
- 事实卡 U083：四行，逐行出现后停住，至少停 2 s 全部可读。
- U073 监控墙：九块屏是她的静图（不唱），识别框一个个锁上。

### 交付与检查

同 a1：先渲 3 段样片自查（建议 0–12 s、44–60 s、205–226 s），再全长渲染（`-o ep01/v3/renders/IRIS-EP01-v3-animatic-a2.mp4`），`comp/review.py --video <绝对路径> --out ep01/v3/review/animatic-a2.html`（审片页用 CRF 20 的轻量转码版），`motion-kit/tools/qa.py … --dur 261.56 --out ep01/v3/qa/animatic-a2`。`comp/review-notes.json` 更新为 a2 的说明与已知问题（不要留“待填写”）。在 `comp/PROGRESS-a2.md` 随做随记进度，账号切换后接手的人照它继续。
