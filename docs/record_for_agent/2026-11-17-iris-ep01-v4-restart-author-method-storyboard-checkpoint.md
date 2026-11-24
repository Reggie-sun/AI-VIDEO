---
record_kind: session_summary
topic_id: iris-ep01-v4-restart-author-method-storyboard-checkpoint
learning_eligibility: ineligible
---

# IRIS EP01 v4 照作者方法重做：检查点 1–4（分镜通过）记录

Date: 2026-11-17（起于 2026-11-16；本机日期，时间戳取自 `outputs/ai-city-takeover/logs/decisions.md` 与 `runs.md`）

## Supersession Notice — 2026-11-17

本记录取代 [v3 全长分镜记录](2026-11-04-iris-ep01-v3-full-animatic-checkpoint.md)中仍写作当前方向的部分：分镜 v2、动画分镜 a1/a2、T4 歌与“检查点 B 待审”已于 2026-11-16 由使用者叫停，EP01 改走 `ep01/v4`。该记录的历史量测与工具事实（Codex `image_gen` 车道、离线生成车道、SHA）仍作历史证据有效，只是不再代表当前制作线。

## Supersession Notice — 2026-11-19（部分）

本记录是检查点 1–4（至分镜通过）的快照，下列当前面向的说法已被后续证据取代，见 [样片第一轮记录](2026-11-19-iris-ep01-v4-excerpt-round1-checkpoint.md)：

- “没有付费视频生成”“下一步是检查点 5 与样片”：此后 Seedance 2.0 VIP 视频已提交并走过逐镜 Gate（`decisions.md` 2026-11-17 起），样片第一轮（歌 39.674–50.93）已于 2026-11-19 获使用者「成立，继续第二轮」。
- “全部未提交 / HEAD `1bf99bf5`”：记录之后 HEAD 为 `964cf680`，`v4/` 等仍未提交。
- 上文历史量测（歌词、选歌、认脸、分镜审计）仍有效；该分镜的 s012 已被样片中重新设计的闭眼唱脸取代（切点 48.17 → 实际 49.087）。

本记录其余部分保持可检索，不标 retired。

## Purpose

记下 IRIS EP01 从“使用者不满意”到“照作者 13 步从概念重做、通过检查点 1–4（概念、歌、认脸、分镜）”的真实状态，让接手的 Agent 分清：已通过的使用者裁决、Agent 自检与审计、仍未发生的事（尚无任何付费视频、尚未提交）。

这是检查点事后整理，由 `memory-keeper` 子代理依主会话清单对照磁盘文件写成。本记录没有调用 Provider，没有生成媒体，没有读取 `.env`，没有 commit。只重新量了两个 SHA-256（歌曲母带、认脸锚点）并读取了 `p030` 底片；其余数字取自 `decisions.md`、`runs.md`、JSON 证据与审计文件，没有重跑测试。

路径自 `outputs/ai-city-takeover/ep01/v4/`（下称 `v4/`）起，除非标明 repo 路径。

## Current Runtime Truth

- **阶段。** 作者流程检查点 1（概念）、2（选歌）、3（认脸）、4（分镜）已由使用者逐项通过；下一步是重出 s030 之后的检查点 5（片段 prompt 本与费用）与 20–40 秒样片。未做 P6、Final Acceptance、`preview_approval`。
- **没有付费视频生成。** v4 的付费或远程效果只有：Suno 4 轮 12 次提交（见下）与 Codex `image_gen` 订阅额度出图（认脸 8 张加分镜 61 张，另有平台对比 4 张）。没有 Seedance、数字人或其他视频 Provider 的 submit、permit、intent。
- **全部未提交。** 记录时 `git status`：`M motion-kit/tools/codex_plate.py`、`M outputs/ai-city-takeover/logs/decisions.md`、`M outputs/ai-city-takeover/logs/runs.md`；未追踪 `docs/superpowers/specs/2026-11-16-iris-ep01-restart-author-method.md`、`motion-kit/tools/{board_audit,lyric_score,test_board_audit,test_lyric_score}.py`、`outputs/ai-city-takeover/ep01/v3/review/compare/`、`outputs/ai-city-takeover/ep01/v4/`。HEAD 为 `1bf99bf5`，`main` 与 `origin/main` 同步，无 staged 内容。`.gitignore` 排除 `*.png` 与 `*.mp4`（见 v3 记录），所以 WAV/PNG 的跨机器身份只剩下文所列 SHA 与 JSON。整目录 `git add v4/` 会带入 WAV、分轨与大量 PNG；提交须逐路径选择。
- **使用者判过的与没判过的。** 使用者判过：不满意的诊断、概念、歌词方向与每一轮听歌感受、选歌、逐字时间“对得上”、认脸 F1-a、分镜“可以，按这个往下做”。使用者**没判过**：任何 v4 视频片段、整片观感、61 张底片的逐张身份检查（耳挂左右等留到出片前）。

## Session Work And Decisions

### 起点：不满意诊断与重做（2026-11-16）

使用者原话：「我觉得codex前面规划的有问题。我觉得现在就是不满意。不知道怎么形容」。主会话做了作者 EV 与 a1 逐镜中点帧对比页（`ep01/v3/review/compare/index.html`），使用者多选：「AI 味重，不像真拍的」「场景单调，全在机房」「人物只会摆姿势瞪眼」「概念太空太套路」，补充「并且歌词太少」。实测词密度：我们 184 词／4:22＝42 词每分，作者 EV 447 词／5:06＝88 词每分。随后：「我需要按照作者的制作方法重新设计」。

主会话据此判定问题在上游（概念、歌词、底片工具），不在剪辑；a2 停做（执行代理已因用量上限中止，不再重派），分镜 v2、a1/a2、T4 不再沿用，改走作者 13 步、6 个检查点。方案：`docs/superpowers/specs/2026-11-16-iris-ep01-restart-author-method.md`（状态仍标“草案”，两个待决事项已由使用者在 decisions 中答复，spec 本身未回写）。花费 0。

### 前置决定

- **底片工具。** 使用者选“先对比试验再定”，随后 11-17 改判「用codex出图」，不做 Midjourney／Seedream 对比。过程：同 4 条作者写法提示词（`plate-tool-test/prompts.md`）先出 Codex 基线；Midjourney 由使用者「我有账号，帮我在浏览器里出」，但受控 Chrome 被 Cloudflare 验证拦下（使用者称「人际验证过不了」），Agent **不绕过验证**，改为生成一个可复制页 `plate-tool-test/midjourney.html` 交使用者自行出图；该对比最后没有做完。
- **研究范围。** 使用者选「DNS 事件做核心＋当季 AI 梗」。`model-researcher` 出 56 条 `research/bank-raw.md`；独立核实代理逐条复核并取得 OpenAI 一手原文，写成 `research/bank-verified.md`（分“可上屏为事实”“归属引语”“不要用”三档；A2「拿到答案」与一手矛盾、A17 假引语、D8 数字不符等已剔除）。该核实用 Jina/Wayback 取页，不是 Agent 自行联网猜测，但本记录没有重新打开这些页面。

### 检查点 1：概念

三案见 `concept-pitches.md`（A 考场、B 夜班城市、C 事件秀）。使用者选「C · 事件秀 INCIDENT WEEK」。主会话依作者规则（续作不沿用上一首的装置）指出 Look 编号与 EV 已用梗重叠，使用者选贯穿装置「P0 工单与值班告警 (Recommended)」。Brief：`brief.md`（含事实纪律：写“经 DNS 获得有限的实时联网”，不写“逃出沙箱”；外部聊天机器人只“部分回答”）。

### 歌词（作者 `wiki_song` 流程）

- 四个写手（密度、张力、钩子、时装秀）并行起草 `lyrics/draft-*.md`，评分 82–84／66–72；评审合并 `merged-v1`（85／86）；critic 判 FIX FIRST，13 条逐行修 → `merged-v2`（85／81，430 词，2,920 字元，lint 0）。使用者「可以，拿去做歌 (Recommended)」「三种曲风都试 (Recommended)」。
- 评分工具 `motion-kit/tools/lyric_score.py`（764 行，新增、未追踪）由执行代理照作者规格新建；依赖放独立 venv `~/.local/share/ai-video/lyric-venv`，**没有**改项目依赖。工具自述为“只近似作者的评分器，分数是建议，导演的耳朵优先”。
- 使用者听第一轮 6 首：「都不对，开头的钩子太弱了」；看开头候选后：「刚开始应该是纯音乐，但是我觉得钩子太平和了，不如原作者的和之前的lookoutside」，选「副歌换回 I didn't run (Recommended)」→ v3。听第二轮后：「很奇怪，还新的副歌」→ 依作者 rewrite loop 只重写副歌（14 候选、打分、评审，`lyrics/chorus-candidates.md`），使用者选「Hello, world! (Recommended)」→ v4（删 V2 的 Altman/HF 对句，HF 是 EV 已用梗）。第三轮后：「感觉hello world不对，副歌对了」，选开头句「All hands! All night!」，声音「副歌也换了看看」→ v5（`lyrics/merged-v5.lyrics.txt`，86／84，63 行 461 词，3,013 字元，比作者约 3,000 经验上限多 13，Suno 页面上限 5,000；每分钟词数 `score-merged-v5.md` 记 131.7，按 210 s 估算，不等于成片实测）。

### 检查点 2：选歌与 Suno 花费

- Suno 共 4 轮，每轮同一歌词三曲风（vogue／postpunk／industrial）各提交一次：**12 次提交，共 120 积分，余额 2,440→2,320**（`decisions.md` 记载；积分数为主会话从账户读到的，本记录未重读 Suno 账户）。第一轮 6 首“P Zero”（3:18–3:45）；第二轮 6 首（3:43–4:34）；第三轮、第四轮各 3 次提交。
- 提交脚本 `song/suno_ui.cjs` 是 v2 脚本的 v4 副本：因 Suno 改版（My Taste 移到 Personalize、URL 不再保留 hash）改用 `window.name` 标记分页；提交前同时核对歌词、曲风、排除与标题（两套字段曾在同一分页先后填入，只比歌词会误交）。suno-cli 授权档当时不见（`auth_missing`），网页音档为加密串流，**不破解**。
- **选定 take。** 使用者：「https://suno.com/s/GZ1nn6Ya6aCDiYYu 这个」＝clip `edc6c6bf-2702-4bea-81df-07d680df4f38`（“All Hands r4”，industrial glitch club，4:33，歌词 v5；`song/selection.json`）。
- **WAV 取得。** 使用者选「允许，你来转 (Recommended)」：主会话从使用者 Chrome 以 CDP 取 Suno `__client` cookie，经管道交给 `suno auth --cookie-stdin`（不显示、不另存）。下载 `song/master/all-hands-r4-edc6c6bf.wav`：273.32 s、48 kHz 立体声，SHA-256 `6dffe1d9022c960d7e0a67c834787131206707b02ca30ade67e04f82209c0350`（本次重算一致），另存 Suno 逐字时间 `master/suno-timed-lyrics.json`。cookie 值不在任何记录或文件中。

### 听阶段（作者流程第 5 步）

- Demucs `htdemucs_ft` 分轨在 `song/stems/htdemucs_ft/`。
- 节拍图 `song/beatmap/`：全局 130.85 BPM（风格词写 130），首重拍 0.48 s，149 小节，`bar_s` 1.8228；`song/music-map.json` 记器乐前奏 6 小节、0–11.42 s，重拍 0.48/4.12/7.81 s。
- 逐字时间三路互查：`song/timing.py`（CTC `MMS_FA`，在人声轨上，用 Suno 时间定位行窗）、Whisper large-v3 盲听（`timing/whisper-transcribe.json`）、`song/resolve.py` 每字裁决，结果 CTC 433、Suno 16、未证实 12，写入 `song/timing/listen.json`（该文件的 12 项是“CTC 与 Suno 相差 >0.25 s 且 Whisper 没听到”，需耳朵核对）。
- 已知现象：第一段 Post-Chorus 的「P zero. That's all.」唱了两遍（76.3 s 与 83 s 即兴重复），取第一遍；Whisper 显示最后副歌叠和声、咬字糊（如 “Shut it, but you stay awake” 被听成别的字），上屏歌词会补足。
- 听歌对时页 `song/review/`、歌词页 `lyrics/index.html`（逐句中文在 `lyrics/glosses-v5.json`）。使用者看过后：逐字时间「对得上，继续 (Recommended)」。注意：该裁决覆盖的是页面上呈现的对时，不等于逐字都被使用者逐词听过；12 个未证实字是否被逐一听过，本记录没有证据，只能说使用者以整体“对得上”放行。

### 检查点 3：认脸与 Codex 账号事故

- 准备：`face/prompts.md` 四张测试底片（F1 清晨窗边正脸、F2 深夜办公室放声唱、F3 地下停车场 T 台全身、F4 无人计程车纯侧面），外形文字原样取自 `series/casting-v3/canon-v4.md`，不挂参考图（E3 旧锚点是 CG 质感），每张 a/b 两版。
- **事故。** 当时 Codex 默认模型 `gpt-6.1-sol` 在该 ChatGPT 账号下报 “not supported”，8 次全部未出图即退出（`logs/runs.md` 状态 `no_output`）；该账号下 `image_gen` 工具不可用。对策：`motion-kit/tools/codex_plate.py` 新增 `--model`（`git diff` 为 2 行：`ap.add_argument("--model", ...)` 与 argv 中 `-m`），试跑改用 `gpt-6-luna`（`models_cache` 有、试跑可用）；**未改使用者的 `~/.codex/config.toml`**。备选 gpt-image-2 chatgpt-web 被 Cloudflare 验证挡住，**未使用、未绕过**。随后 Codex 账号 11:22 由**使用者自己切回**，`image_gen` 恢复；8 张认脸全部 delivered（`face/raw/`，审片页 `face/index.html`）。后续 61 张分镜底片的 argv 里没有 `-m`，即用的是恢复后的默认配置。
- Agent 客观检查（只算自检）：正面时耳挂与立领红线在画面右侧、F4 侧面面朝画面左侧露出耳挂，符合左右规则；F2 张嘴唱；F3 两张出成直幅 1024×1536（尺寸参数被忽略），进片前须重出横幅；F4 吸管像香烟。好不好看、像不像她由使用者判。
- 使用者选「F1-a」。身份锚点 `face/IRIS-anchor-F1a.png`，SHA-256 `2dd80e2f0ff55fbe24a95c5d881a2d2422421c7d94b7a066a3dc6f2e54d55b6a`（本次重算一致），记录 `face/selection.json`（`schema: iris-ep01-face-selection/1`）；EP01 v4 所有底片以它作身份参考（`--ref`），取代 E3。canon-v4 外形文字不变。

### 检查点 4：分镜

- 流程（作者 `wiki_storyboard`）：任务书 `board/brief-board.md` → 三位导演代理并行（fashion／meme／narrative，`board/draft-<lens>.json|md`）→ 审计 → 三评审 → 总导演合并 → 审计 → 独立事实核查 → 主会话改 5 项 → 卡片页。
- **审计工具** `motion-kit/tools/board_audit.py`（224 行，新增、未追踪）：作者审计表的 11 道门加节奏报告；`test_board_audit.py` 10 项，`decisions.md` 记载通过，本次未重跑。补了两点：接受分镜自带 clips 生成窗口（片段可长于镜头）；唱段起点的词内判定留 0.05 s 容差。
- 三版草稿审计皆过：fashion 63 镜（均 4.34 s、出镜 98.8%、sung 85 s／motion 122 s）、meme 82 镜（3.33 s、95.8%、109／100 s）、narrative 75 镜（3.64 s、97.7%、105／111 s）。
- 三评审（观众、导演品味、制片与事实）总分：fashion 81/79/81＝241、meme 83/77/71＝231、narrative 77/70/82＝229 → fashion 为底。制片评审列出事实违规（meme 5、fashion 4、narrative 1，含 INC 工单翻 REOPENED 无来源、≈2.5 HOURS 算错区间、FIXED 无来源、城市穿越读成“逃出”、门关后仍有红光）。
- 主会话决定：sung 预算 110→150 s（使用者此前「费用你不用管」；三版她开口只约 31% 的词），motion ≤140 s；停车场 ≤20%；最多 3 套造型；不拍镜中像、不排同脸副本群；长引语只放 4–6 个关键词。
- **总导演合并版** `board/shots.json`＋`board/board.md`：61 镜、均 4.48 s、出镜 98.8%（无她的只有 s030）、sung 145.5 s（27 段，含 12 个念白口型窗）／motion 86.87 s、停车场 18.9%、3 套造型、61 张底片不复用、机房 0；45 个片段；切点 60 个，30 个在 downbeat；图形 32 种；她在镜头上的唱词 135/192＝70.3%、念白 139/269＝51.7%。`board/audit-merged.json`：`pass: true`，`fails: {}`（本次读取确认；主会话也已重跑）。
- **独立事实核查** `board/factcheck-merged.md`（只读代理，5 项，皆中低/低）：s022 引语去引号改转述出处、s037 截断补省略号、s042 `RESUMED OCT 1 · STILL OFFLINE`（离线缓存 9 月 20 日前已存在）、s043 补 DNS 报告出处、s001 副标题改 `EVERY LOOK · REAL, THIS SEASON`；另 s053、s054 有反光面，prompt 补“不出现倒影”。先前 `judge-producer` 的违规在合并版均已消除。该核实基于 `bank-verified.md`，不是重新联网。
- **底片。** 使用者：「先出底片贴上卡片再审 (Recommended)」。`board/plates-book.md`（逐字取自 `shots.json`，前加「16:9 横幅画面。」）、`board/run_plate.sh` 单张出图（有她的镜头带 F1-a 锚点 `--ref`，`runs.md` 记 sha `2dd80e2f…55b6`）、6 路并行，61 张全部 delivered、全 1672×941。Agent 初看：脸与 F1-a 一致、真拍质感；s045 照分镜出现唯一副本；门缝红光只出现在关门前（s002、s039、s049、s050）。s030 首次出图泳池有水（与 s028 放干水不一致），已在 `runs.md` 出现第二次 `p030` 记录（14:12，无 `--ref`，delivered，SHA-256 `872d80bc…61cc`）；本次读图见干池、寻呼机、枯叶、无水，**是 Agent 的单张目检，使用者未判**。其余 60 张的耳挂左右、造型等逐张身份检查留到出片前。
- 使用者看贴了底片的卡片页（`board/index.html`，`board/build_sheet.py` 生成）后：「可以，按这个往下做」＝检查点 4 通过。开放问题按总导演默认处理。

## Verification And Evidence

| 项 | 证据 | 层 |
| --- | --- | --- |
| 母带身份 | `song/master/all-hands-r4-edc6c6bf.wav` SHA-256 `6dffe1d9…0350`，273.32 s，48 kHz 立体声；与 `song/selection.json` 一致（本次重算） | execution |
| 认脸锚点 | `face/IRIS-anchor-F1a.png` SHA-256 `2dd80e2f…55b6`，与 `face/selection.json` 一致（本次重算） | execution |
| 节拍与段落 | `song/music-map.json`（130.85 BPM、149 小节、前奏 0–11.42 s） | function（脚本量测） |
| 逐字时间 | `song/timing/listen.json` 12 个未证实字，使用者以“对得上”放行 | function + human（整体） |
| 分镜审计 | `board/audit-merged.json` `pass: true`；`test_board_audit.py` 10 项（`decisions.md` 记载） | structure |
| 事实核查 | `board/factcheck-merged.md`，5 项已改 | final review（独立代理，非使用者） |
| 歌词评分 | `lyrics/score-merged-v5.md`：scansion 86／assonance 84 | analyzer（建议分，不是观感） |
| 底片出图 | `logs/runs.md` 每张 `status: delivered`、1672×941 | execution |
| 使用者裁决 | 检查点 1–4 的原话见上，均在 `decisions.md` 2026-11-16/17 条目 | human |

没有人工或 Gate 层面的 v4 视频证据；没有 `video-analysis` MCP 的 per-shot Gate（尚无 Shot MP4）。

## Assessment

- 上游诊断被使用者逐步印证：每次歌词方向偏差（钩子弱、旧副歌搬进新歌怪、“Hello, world!”不对）都由使用者听后指出，Agent 的评分（85–86 分档）没有预见这些问题，印证“观感只由使用者判”。
- 第四轮 take 的选定、逐字时间放行、认脸、分镜通过都是使用者裁决；评分、审计、事实核查通过只证明被测项，不代表成片观感。
- “作者流程”在这里被拆成可复用的工具与页面（评分器、审计脚本、卡片页、听歌对时页），但它们对 EP01 之外的作品是否通用尚未验证（Product Invariants 要求共享能力不以单例证明）。

## Remaining Risks Or Next Work

- s030 重出后按作者“先在一个镜头上找到方法、尽早给 20–40 秒样片”：检查点 5（片段 prompt 本与费用，花钱前读）→ 样片。每个 Shot MP4 落盘后须走 per-Shot post-media Gate；剧情类付费视频前须把该镜参考包预览交使用者并封存 `preview_approval`。
- 61 张底片只做了初看；耳挂左右、造型一致、F3 竖幅教训（已按横幅出）等逐张身份检查未做。
- 第四轮 take 含 12 个未证实字和最后副歌和声咬字糊，上屏歌词是补足版，要在样片里复核口型与字幕。
- 歌词 v5 3,013 字元略超作者经验上限，已被 Suno 接受；所选 take 时长 4:33，超出 `brief.md` 的目标 3:00–3:40；使用者选 take 时没有就时长另作表态（decisions 无记载），brief 也未回写，成片时长目标需在检查点 5 前确认。
- `docs/superpowers/specs/2026-11-16-iris-ep01-restart-author-method.md` 仍标“草案”，两项待决事项已由使用者答复，spec 未更新。
- 记录之后若发生 commit，请注意 v4 目录体积与 `.gitignore` 对 PNG/MP4 的排除；本记录不判断哪些应入库。
- Suno 积分仅为 `decisions.md` 转述，未在记录时重读账户。

## Agent Guardrails

- “分镜通过”只是检查点 4，不等于 `preview_approval`、片段生成许可、P6 或 Final Acceptance。
- 审计 `pass`、事实核查通过、评分高 ≠ 好看；歌词与底片是否“怪”只由使用者判。
- Suno 积分与 Codex 额度是真实消耗；再提交歌曲或视频前走各自授权与 Guard，不得以本记录为许可。
- Codex 默认模型不可用时，用 `--model` 覆盖单次调用，不改使用者的 `~/.codex/config.toml`；被 Cloudflare 验证挡住的网页入口不绕过。
- 不要把 `v4/` 之外的旧 `ep01/v3` 分镜 v2、a1/a2、T4 当作当前方向。
