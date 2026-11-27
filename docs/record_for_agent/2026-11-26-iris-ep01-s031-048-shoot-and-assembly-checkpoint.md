---
record_kind: media_experiment
topic_id: iris-ep01-s031-048-shoot-and-assembly-checkpoint
learning_eligibility: eligible
evidence_index_version: "1"
---

# IRIS EP01 s031–s048 拍摄与剪辑检查点：review-v1 获使用者认可（彩点算次要），0–209 s 连片已出，念白对口型写法仍无定论，验证与提交待做

Date: 2026-11-26（本机日期；数字与哈希取自磁盘文件，核不到的标 NOT_EVALUATED）

## Purpose

记下 2026-11-24 至 2026-11-26 这一段的真实状态：s031–s048（歌 134.44–209.34 s）从导演方案认可、首帧预览、提交前连续性修正、r2/r3/r4 三次改写 prompt、SG17 A/B 探针、逐条 Gate 与「量、剪、盖」分段验收，到 Agentcut 版式层导出、QA、使用者认可 review-v1。并分清：使用者裁决、Provider 与 operator 事件、主会话自审、技术 QA 与人工认可、花费口径、尚未做完的验证与提交。

这是新记录，不是 [2026-11-23 s015–s030 记录](2026-11-23-iris-ep01-s015-030-shoot-and-assembly-checkpoint.md)的追加：那份记录的范围止于 134.44 s。它里面「commit / push 待做」与「转身候选待确认」两项在本段开始前已被取代，已在该记录加 supersession 提示（见 Remaining Risks）。

本记录由 `memory-keeper` 子代理依主会话清单对照磁盘文件写成。读取了 `outputs/ai-city-takeover/logs/decisions.md`（2026-11-24 至 2026-11-26 各条，使用者原话取自这里，属主会话写的二手转录）、`pilot/s031-048/HANDOFF-2026-11-24.md`（含「剪辑用法（2026-11-26）」）、`pilot/s031-048/probe/index.html`、`r4/index.html`、`excerpt/qa/s031-048-v1/{qa.json,extra.json,joined.json}`、`excerpt/section3.py` 系列的存在、`pilot/sd-SG12|15|16x|16y|17A|17B|18x|18y|19|20x-*/**/gate/sync-summary.json`、若干 take 的 `native-prompt.zh.txt` 与 `ledger.json`、`song/timing/words.json`。重算了两个 mp4 的 SHA-256，用 ffprobe 核对了帧数、分辨率与音轨。没有重看影片，没有重跑 QA、渲染、Agentcut 或测试，没有读取 `.env`，没有调用 Provider，没有 commit，没有 stage。

## Current Runtime Truth

### 使用者认可了什么、没认可什么

- **review-v1（s031–s048）已认可。** 使用者原话「认可，彩点算次要 (Recommended)」（`decisions.md` 2026-11-26 剪辑审片条）。认可范围按该条所写包括：丢拍 s037d 放碗与 s041c 伸手、s039 与 s037c 跳切、s046b 后期按表、s048 纸条插镜、眼睛变浅、s036 静图 3.7 s、若干后期简化；s033b f328 手背压缩彩点由使用者改判为次要。这是使用者对该段的观感裁决，不是 P6、Final Acceptance、`preview_approval` 或发布。
- **0–209 连片没有单独的使用者表态。** 连片是 0–134 v1 与本段的视频流直接拼接，使用者认可的是 s031–s048 这一段。开头 0–59.23 s 仍是「暂定」（见 2026-11-23 记录）。
- 使用者另有若干当次裁决（逐条在 `decisions.md`）：s041→s042 换装「A 裹布 + 重音剪切」、s045 副本「A 保留副本但不露脸」、s043「A 换气处的静止远景」、s039 门缝红光「留红光，和 s002 一样算例外」、INS37 面板换边算次要、「按问题页改好的开拍」、「删掉译文、精简动作后重拍」、「先查成熟做法再拍」、「先用 SG17 做 A/B 对照」、「s039 拼切；剩下照这个写法拍，上限提到 15,000」、「按 r4 开拍」，以及各单元选片裁决。均为使用者对本作品本段的当次决定，不是对 Skill、Policy 或 Gate 的修订；`AGENTS.md` 的 Per-Shot Gate 仍要求「改判次要、移出或延后须用户当次决定」。

### 最终产物（本次重算 SHA-256 与 ffprobe）

| 文件（`outputs/ai-city-takeover/ep01/v4/excerpt/renders/`） | SHA-256 | 规格 |
| --- | --- | --- |
| `IRIS-EP01-agentcut-ev-s031-048-v1.mp4`（正式片，含声音） | `951ed6bce9c2f47658fad305754d07744a683d1988f7aec89a8c358439bed2e3` | h264 1920×1080 24 fps，1797 帧，74.875 s；aac 48 kHz 双声道 |
| `IRIS-EP01-agentcut-ev-000-209-v1.mp4`（连片） | `b945988ae5eb5e987e561d53e04d3c6869337c08c9f661b11596e3cff0899c2e` | h264 1920×1080 24 fps，5024 帧（= 3227 + 1797），209.333 s；aac 48 kHz 双声道 |
| `IRIS-EP01-s031-048-v1-picture.mp4`（引擎画面，无版式层、无声） | `4e27c10db5699c4e2965368c9d0f9c00926473bdfd4d097760b4d6316b1bd3eb`（取自 `qa.json` `picture_sha256`，本次未重算） | 1797 帧 |

本次对前两项重算 SHA-256，与 `qa.json` / `joined.json` 记载及主会话清单（`951ed6bc…`、`b945988a…`）一致。0–134 部分仍是 `IRIS-EP01-agentcut-ev-000-134-v1.mp4`（`a1c0c72d…2b7d`，本次重算一致）。`.gitignore` 排除 `*.mp4`，这些媒体的跨机器身份只剩 SHA 与 JSON。Agentcut 项目在仓库外，不在 Git 里。

### 提交与验证状态（记录时刻）

- **Harness 对 staged snapshot 的验证：待做（pending）。** 本记录写成时没有跑，也没有 receipt。
- **commit / push：待做（pending）。** `git status` 显示 `outputs/ai-city-takeover/ep01/v4/` 下的本段文件与 `decisions.md`、`board/shots.json` 等仍是未提交改动；`HEAD` 与 `origin/main` 此刻同为 `8e9c1d3a`（上一段已推送，见 Remaining Risks）。本任务路径的提交范围尚未选定。
- **下一段 s049–s061（待做）。** 本段之后的歌段，尚未开始。

## Session Work And Decisions

### 一、导演方案、首帧预览与提交前连续性修正（2026-11-24/25）

- 方案页 `pilot/s031-048/plan/index.html` 沿用 s015–s030 作者切镜规则：11 条视频、15 张静图（静图占 52%），L1 改 W1、开场脸、首帧闭嘴，走向镜头、出画、唱段大动作改由剪辑完成。使用者「按方案做首帧预览 (Recommended)」。
- 首帧预览 `pilot/s031-048/preview/index.html`：使用者「全按推荐 (Recommended)」。
- 提交前连续性检查（`continuity-supervisor`）：11 个单元均未就绪；问题页 `pilot/s031-048/issues/index.html` 改 prompt 动作绑具体台词、纸币素面、SG18 只露手、SG19 布慢落、INS33 手按盖，并重做 p037-c2、p037-ins37b、p042-w2、p046-w2、P047 首帧（首帧只贴回改动块，块外逐像素不变）。使用者「按问题页改好的开拍 (Recommended)」：11 条每条 2 次，预计 10,400，上限 11,200。
- 之后 r2（`r2/index.html`）：SG15/SG17 的「最后一句」改按句序，W1 左臂被外套盖住改裸臂（新 p048-w2、s047 静图）。使用者「按 r2 开拍，图用推荐 (Recommended)」。

### 二、念白/唱段对口型：连续失败与写法演变（有界单例观察，见 Learning 评估）

以下均为本作品、Seedance 2.0 VIP multimodal（图 + 参考人声）一条路线的观察，不是通用规则。

1. **引用歌词中文译文后，模型改说中文（SG12）。** SG12 a-1（`2a8b972e…`）与 a-3（`9e5230d5…`）使用逐字相同的 prompt（本次比对 `native-prompt.zh.txt`），其中第四句写了「说第四句“运气不好”时…」。a-3 的原生音轨与口型是中文（`decisions.md` 记 Whisper 检测 zh，转写「九月二十号搜了一圈……运气不好」；该检测输出本次没有在 take 目录里找到，属 `decisions.md` 转述）；a-1 同一 prompt 不是中文（s031c 取用 a-1 的 140.05–141.29 “No luck” 段）。使用者「删掉译文、精简动作后重拍 (Recommended)」：所有念白/唱段 prompt 不再引用译文，只写「第几句时」，SG12 同时去掉塞纸币与瞟眼，只留开口时收腰带（r3，`r3/index.html`；新增测试禁止念白/唱段 prompt 出现引号、英文或歌词释义）。重拍 b-1（`efd0b7a0…`）、b-2（`e57554a4…`）两条均为英文。去译文与去动作是同时改的，不是单变量；a-1 与 a-3 同 prompt 结果不同，说明这是抽样差异的一个例子，不是确定的因果。
2. **SG15（`e2338edb…`、`f4fa68ec…`）：英文但自编台词**（「I'm not stupid, you know…」「I'm not a killer…」），口型全段对不上，第三句前后转头。使用者「改静图 + 图形，不再拍 (Recommended)」：s036 用首帧静图缓推，念白画外音。SG15 花 800。
3. **调研（2026-11-25，`model-researcher`，不花积分）。** 主会话转述：官方 2.0 指南把参考音频当音色/节奏参考，不保证逐字对口型；本仓库统计 ≤6 s 的生成 copy=true 为 10/18，≥7 s 为 2/20（统计口径与脚本本次没有重算，属调研回报）；社区做法是短窗、音频长度等于生成时长、精简 prompt、英文逐字稿入 `{}`、黑屏视频携音。
4. **SG17 A/B 探针（`probe/index.html`）。** 同首帧、同音频（`SG17p.wav`，原窗口 3.669 s 后补 1.331 s 数字静音到 5.000 s）、同设置，两臂只差一句：B 在 A 上加「她用英文说：{Bet it couldn't reach outside. They found a gap instead.}不增不减，不翻译。」两臂各 2 条（共 1,600 积分）。结果（`decisions.md` 的 Gate 记录；四个 `sync-summary.json` 本次逐一核过 `copy: false`）：4 条均 copy=false（重新配音），开口晚 0.6–1.0 s、念进静音补齐段。词准 B 臂 80–90%、A 臂 30–50%（Whisper 转写，`decisions.md`），口型时间无差别。这个探针只证明了：{英文逐字稿} 改善了词，没改善时间，也没让 copy=true。使用者同意改两条规矩：生成不再多留 1 s（改静音补齐到生成时长）、B 臂豁免「prompt 不写英文」。
5. **r4 短窗口（`r4/index.html`，使用者「按 r4 开拍 (Recommended)」，3,360）。** SG16x、SG16y、SG18x、SG18y、SG20x：按剪辑段拆窗口（人声 1.4–2.4 s，补静音到 4–5 s），prompt 只有首帧状态 + 对镜头说/唱 + 口型逐字同步 + {英文原词} + 镜头固定 + 必需的空白/红色/文字规则，不写绑台词的动作（s037d 放碗、s041c 伸手因此丢拍，交剪辑）。逐 take 的 `sync-summary.json` 结果：

| 单元 | take | copy | 备注 |
| --- | --- | --- | --- |
| SG16x | r-1、r-2 | true、true | 词全对；模型拉长句间停顿（局部 lag 0.41→0.57→0.90），r-1 微波炉面板长字 FAIL，用 r-2 逐句对齐 |
| SG16y | r-1、r-2 | false、false | 重新配音，但 lag≈1.37 稳定（envelope ncc 0.93/0.94，`steady: true`） |
| SG18x | r-1、r-2 | true、true | 整句严格对上；段外开头多唱 “Days”（不进片） |
| SG18y | r-2、r-3（r-1 known_no_effect） | false、true | r-2 “October” 被拉长近 1.9 倍；r-3 lag −0.005，严格同步段 183.695–185.645 覆盖整个剪辑段 183.763–185.585 |
| SG20x | r-1、r-2 | false、false | r-1 envelope lag 0.425、`placement` 注为「NOT steady: judge by eye」；母带 “crack” 实唱三遍，r-1 第三遍闭嘴 |

   10 条 r4 take 中 5 条 copy=true（SG16x×2、SG18x×2、SG18y r-3）、5 条 false（SG16y×2、SG18y r-2、SG20x×2）。copy=true 只出现在 3 个单元里，同单元内两条 take 结果往往一致（SG16x、SG18x、SG16y、SG20x 均成对一致；SG18y 例外）。**这不等于「r4 写法让 copy=true」**：SG17 探针的 B 臂（同一类写法：{英文}、精简、补静音）copy=false 共 2 条；SG19 a-2（`697c36de…`，5 s，prompt 无 {英文}，探针之前拍）copy=true 且 lag 0.6001 / ncc 0.5674。机制未证，样本小。
6. **逐句 knot 对齐与跳切（剪辑方法）。** 模型拉长句间停顿后，单一 lag 对不齐：s037b 按句分段，`qa.json` 的 `lips.s037b.knots` 为 6 个 knot（161.4135→161.92 lag 0.41、161.92→162.26 提速 1.47×、162.26→162.95 lag 0.57、162.95→163.15 提速 2.65×、163.15→163.70 lag 0.90），提速放在句间停顿里。s039 把 SG17B p-1（lag 0.875）与 SG17A p-2（lag 0.600）在 171.955 拍上跳切；s037c 在 164.188 拍上从片内 1.74 跳到 3.10。s048 用纸条插镜盖住第三遍 crack。这是「量、剪、盖」的再次使用，覆盖度见 Verification。
7. **歌词时间表缺口。** 母带 “crack” 实唱三遍（`decisions.md`，听感判断），`song/timing/words.json` 在 207.422–208.767 只记了一条 `crack.`（本次核：晚于 200 s 的 `crack` 词条只有这一条）。s048 的第三遍口型因此不能靠 words.json 预判，要靠听与量。
8. **眼睛约 2 s 后变浅。** SG16x、SG16y、SG18x（及部分 take）多模态 take 反复出现；使用者三次判次要，留在片里。未做归因。

### 三、逐条 Gate 与选片（逐条在 `decisions.md`，此处只列影响剪辑的）

- INS33：a-2（`88667acd…`）PASS，用片内 1.41–3.25；INS37：a-1（`6dd35e27…`）用，双把手算次要；INS41：a-1 用 0.95–3.69；SG19：a-2 用片内 1.517–4.292，三处算次要（靴与布出画、右袖垂布略短、末 1 帧超严格区间）；MO15：a-1 用 0–2.73 + 4K 裁秒表特写后期按表（衣架未推完算次要）；s031a 用 b-1、s031c 用 a-1 口型段；s036 改静图 + 图形；s037b 用 SG16x r-2 逐句对齐；s037d 用 SG16y r-2；s039 用 SG17B p-1 + SG17A p-2 跳切；s041a 用 SG18x r-1；s041c 用 SG18y r-3；s048 用 SG20x r-1 + 纸条插镜。逐镜表见 `pilot/s031-048/HANDOFF-2026-11-24.md` 的「剪辑用法（2026-11-26）」，此处不复制。
- **Gate 评审的两个局限（有界观察）。** (a) 耳挂灯在 1080 级小图上被 Gate 评审判成「不亮」，4K 裁切复核发现一直亮（`decisions.md` 记 SG16y r-2、SG18x r-1、SG18y r-2）。(b) 口型 Gate 的抽帧频率限制口型判断（主会话清单：约 4 fps；本次没有在磁盘文件里找到该数字的出处，属主会话转述，且 SG19 a-2 的「末 1 帧超严格区间」是靠主会话全帧率看嘴才判成次要）。这是本作品的观察，不是对 Gate 判据的修订。

### 四、Jimeng 与 operator 事件（本段）

- **「reference upload did not complete」= known_no_effect，本段再次出现。** SG12 a-2（2026-11-25，ledger `sd-SG12-a-2/ledger.json`，operator 输出 “Jimeng reference upload did not complete; generation was not submitted”，预留 released，余额 68146 不变）与 SG18y r-1（2026-11-26，`sd-SG18y-r-1/ledger.json`，同一报错，余额 50507 不变）。**SG19 a-1 的 ledger 写的是「run_unit.sh：STOP submit not confirmed」、`known_no_effect`、预留 released、余额 65506 不变，没有出现 “reference upload” 字样**（主会话清单把它归为同类，本次只能确认处理结果相同：known_no_effect、不重试同一 attempt）。三者都按 MO01-o-2 / MO11-n-1 先例对账，由新 take 顶替（a-3、a-2、r-3），没有盲目重试、重签或 remint。
- **账号共用，余额差不可靠。** MO15 的任务账 960 在 `decisions.md` 里注明「余额差受共用账号干扰」；r4 页面还暴露一次口报花费（10,840）与逐条之和（8,560）不符，经 r4 页面更正为 8,560。以任务账（逐条相加）为准，不以余额差为准。

### 五、花费口径

- **任务账（4k 80 积分/秒）：s031–s048 合计 11,920 积分**（上限 15,000，原 12,800，使用者在「s039 拼切；剩下照这个写法拍，上限提到 15,000」里调高；新旧上限并存）。逐项：SG12 2,880（a-1 720 + a-3 720 + b 1,440）+ INS33 640 + INS37 640 + INS41 640 + SG19 400 + MO15 960 + SG15 800 + SG17 探针 1,600 + SG16x 640 + SG16y 640 + SG18x 640 + SG18y 640 + SG20x 800 = 11,920；本次重算一致。三个 known_no_effect 记 0。
- 「待确认」：本记录没有对账号积分明细做独立核对；账号多人共用，余额差只作旁证。

### 六、剪辑组装与 Agentcut 导出

- 方法同 2026-11-23 记录：`excerpt/section3.py`（SHOTS 表即 HANDOFF 剪辑用法表）、`section3_layers.py`、`section3_qa.py`、`section3_review.py`；切点吸附到 `beats.json` 拍点；picture-only 画面用 HyperFrames 引擎渲，版式层、歌词、声音在 Agentcut 独立项目；页面导出 `normalizeLoudness=false`（增益 0 dB、限幅 0 dB，导出测得 −16.2 LUFS、真峰值 −3.2 dB，与母带同，`extra.json`）。
- `extra.json` 的 `deviations` 记了与方案的差异，值得知道的：s048 切点用 208.4107 拍（决定写「到 208.30」，208.30 不在拍上）；s039 跳切用恒定 lag 0.875，没有做 0.875–0.96 渐变；s031c 切点后前 0.13 s 在测量段外；s041a/s041c 方案模糊类 D 的 9 px 会糊掉嘴，改 4.5 px；s046b 从 MO15 4K 裁 3.5×（方案 ≤2×），画面偏软；方案里多项后期没做（s041a 射灯每拍暗一盏、s044 纸页闪翻、s045 分层等）。
- 图形全部白/琥珀/墨色，没有红（方案 s036b 的 P0 信号红改琥珀）；s040a 引语出处只写 “— A POST-TRAINING RESEARCHER”，方案里的 “VIA FORTUNE · SEP 26 2026” 未在本仓库核实，没有写。
- 图形与歌词盖脸检查：`extra.json` 记估算框 vs 逐镜人脸框 0 处重叠，另在 Agentcut 抓 23 帧看过。
- 14 条 take 全部在磁盘上重算 SHA-256，与文件名和 `decisions.md` 前缀一致（`extra.json`「take 身份」，本次没有重跑）。

## Verification And Evidence

| 项 | 证据 | 层 |
| --- | --- | --- |
| 正式片规格 | `qa.json` `spec.pass: true`；本次 ffprobe：h264 1920×1080 24 fps 1797 帧、aac 48 kHz 双声道 | execution |
| 声音 | `sound`：成片音频对母带 134.458–209.333 s 偏移 0 样本，RMS 差 −0.056 dB，`pass: true` | analyzer |
| 闪烁 | `flash`：每秒最多 1.5 次（cell 7、frame 329），无 3 次以上窗口；单帧跳变 1 处（frame 433，song_t 152.5，d_prev 0.0218），整体 `pass: true` | analyzer |
| 切点 | `cuts`：35 个切点全部 `pass: true`，`change_peak_on_cut` 35/35；`frame_dt_beat` 最大绝对值 0.02 s（本次对 35 项重算） | analyzer |
| 口型 | `lips` 逐段 `covered_share`：s031a 0.999、s031c 0.0（`sync_check` 报 `ValueError: operands could not be broadcast` → NOT_EVALUATED，该段靠 Gate 阶段测量 140.05–141.29）、s037b 0.349、s037d 0.0（`sync_check` 报错 → NOT_EVALUATED，该段靠 Gate 测得 lag≈1.37 稳定）、s039a 0.627、s039b 0.753、s041a 0.69、s041c 0.998、s042 0.999、s048 0.638（`sync_check` copy false、lag 0.4751）。s031a 的 `lips` 里 `sync_check.copy: true`、lag 0.0001 是对成片放置后的量，与 Gate 阶段 `gate_copy: false`（SG12 b-1 take 对参考人声）不同口径，不要混读 | analyzer（部分 NOT_EVALUATED） |
| 红色 | `red`：899 帧（每 2 帧抽 1）中 1 帧超限：f328（s033b，29 px，手背运动模糊皮肤上的点网 H.264 色度噪点，纯画面同帧 0 px）；`pass: false`；s039 门缝红线按使用者例外在框内（框 0–0.42 × 0.84–1.0）有 44 帧、最多 262 px，框外 0 px | analyzer（FAIL，判据未改） |
| 红色判定的改判 | 使用者「认可，彩点算次要 (Recommended)」：f328 改判次要；`qa.json` 顶层仍是 `red.pass: false`，没有改写 | human（改判） |
| 连片 | `joined.json`：视频流直接拼接不重编码，decoded framemd5 帧 0–3226 等于 0–134 v1、3227–5023 等于本段；整片音频、起点、两个接点、终点窗口对母带全 0 样本偏移；pts 最大偏差 3.3e-7 s；本次 ffprobe 帧数 5024、音轨 209.333 s 一致，framemd5 比对本次没有重跑 | execution（部分转述） |
| 观感 | 使用者看过 review-v1 并认可；本记录没有重看影片 | human |
| Harness / staged snapshot | 未跑，待做 | NOT_EVALUATED |

## Evidence Index

行分五组。(1) 成片与连片：同一正式片的技术层与人工层共用一个 `independence_key`。(2) SG12 译文对照：a-1 与 a-3 是逐字相同 prompt 的两次独立抽样，b-1/b-2 是去译文且去动作的重拍（不是单变量）。(3) SG17 探针 A/B：同首帧、同音频、只差 {英文}，只记 analyzer 的 copy 结果。(4) r4 的 10 条 take 与 SG19 a-2：只记 analyzer 层的 copy 结果（`sync-summary.json`）；同一单元的两条 take 是两次抽样，各自一个 key，不当作两个独立「写法」。(5) SG15 自编台词。verdict 在此仅表示该 proof layer 的具体判据（`COPY_TRUE` / `COPY_FALSE` 是 `sync_check` 全局 NCC 判据，不是口型好坏或观感），不是质量、验收或 Production 资格。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s031-048-film-v1-qa | native:951ed6bce9c2f47658fad305754d07744a683d1988f7aec89a8c358439bed2e3 | iris-ep01-s031-048-assembly-v1 | agentcut-export-s031-048-v1 | N/A | 951ed6bce9c2f47658fad305754d07744a683d1988f7aec89a8c358439bed2e3 | ANALYZER | FAIL | RED_SPECKS_H264_CHROMA_1_FRAME | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/excerpt/qa/s031-048-v1/qa.json |
| s031-048-film-v1-human | native:951ed6bce9c2f47658fad305754d07744a683d1988f7aec89a8c358439bed2e3 | iris-ep01-s031-048-assembly-v1 | agentcut-export-s031-048-v1 | N/A | 951ed6bce9c2f47658fad305754d07744a683d1988f7aec89a8c358439bed2e3 | HUMAN | ACCEPTED | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | s031-048-film-v1-qa | outputs/ai-city-takeover/logs/decisions.md |
| joined-000-209-v1 | native:b945988ae5eb5e987e561d53e04d3c6869337c08c9f661b11596e3cff0899c2e | iris-ep01-s031-048-assembly-v1 | stream-copy-join-000-209-v1 | N/A | b945988ae5eb5e987e561d53e04d3c6869337c08c9f661b11596e3cff0899c2e | ANALYZER | PASS | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/excerpt/qa/s031-048-v1/joined.json |
| sg12-a-1-translation-quoted | native:2a8b972e2909dd526051dfe1c188447116451f046ad395c66af40c5419e6b126 | iris-ep01-sg12-translation-quoted-vs-removed | sd-SG12-a-1 | translation-quoted | 2a8b972e2909dd526051dfe1c188447116451f046ad395c66af40c5419e6b126 | GATE_REVIEW | FAIL | HEAD_TURN_AND_BILL_TIMING_MOUTH_LATE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG12-a-1/SG12/gate/sync-summary.json |
| sg12-a-3-translation-quoted | native:9e5230d527a2edced2cf651711a9787c058639aa1b23dbec6f763f79058a5d96 | iris-ep01-sg12-translation-quoted-vs-removed | sd-SG12-a-3 | translation-quoted | 9e5230d527a2edced2cf651711a9787c058639aa1b23dbec6f763f79058a5d96 | GATE_REVIEW | FAIL | NATIVE_AUDIO_LANGUAGE_ZH | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG12-a-3/SG12/gate/sync-summary.json |
| sg12-b-1-translation-removed | native:efd0b7a0abc0c14ef3346cf2505e2df596f058be02af7b5dbe6161a4561fa137 | iris-ep01-sg12-translation-quoted-vs-removed | sd-SG12-b-1 | translation-removed-actions-simplified | efd0b7a0abc0c14ef3346cf2505e2df596f058be02af7b5dbe6161a4561fa137 | GATE_REVIEW | SPAN_PASS | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG12-b-1/SG12/gate/sync-summary.json |
| sg12-b-2-translation-removed | native:e57554a427268a0c444ef59fc98f3cb58cba248af2a190e66aaed9eb35957fd9 | iris-ep01-sg12-translation-quoted-vs-removed | sd-SG12-b-2 | translation-removed-actions-simplified | e57554a427268a0c444ef59fc98f3cb58cba248af2a190e66aaed9eb35957fd9 | GATE_REVIEW | FAIL | HEAD_DOWN_OFF_CAMERA_AT_7_75S | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG12-b-2/SG12/gate/sync-summary.json |
| sg15-a-1-invented-lines | native:e2338edb69a148d8d145dd889541eb3248e4409e2a61880c40648f83dc0a9d04 | iris-ep01-sg15-spoken-lipsync-r3 | sd-SG15-a-1 | r3-no-translation | e2338edb69a148d8d145dd889541eb3248e4409e2a61880c40648f83dc0a9d04 | GATE_REVIEW | FAIL | INVENTED_ENGLISH_LINES_LIPSYNC_OFF | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG15-a-1/SG15/gate/sync-summary.json |
| sg15-a-2-invented-lines | native:f4fa68ec9aa9aae95e9b6d4bb8ebab797648e329ccff5e8fd263baa531e4da61 | iris-ep01-sg15-spoken-lipsync-r3 | sd-SG15-a-2 | r3-no-translation | f4fa68ec9aa9aae95e9b6d4bb8ebab797648e329ccff5e8fd263baa531e4da61 | GATE_REVIEW | FAIL | INVENTED_ENGLISH_LINES_LIPSYNC_OFF | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG15-a-2/SG15/gate/sync-summary.json |
| sg17a-p-1-minimal-padded | native:fe2fb9a74e05e49d9967440d96d051cf6406edccee2f1a8f0af1b3887891b137 | iris-ep01-sg17-english-braces-ab-probe | sd-SG17A-p-1 | A-minimal-padded | fe2fb9a74e05e49d9967440d96d051cf6406edccee2f1a8f0af1b3887891b137 | ANALYZER | COPY_FALSE | RE_VOICED_OWN_AUDIO | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG17A-p-1/SG17A/gate/sync-summary.json |
| sg17a-p-2-minimal-padded | native:b63f349bbe6b004b2429b165818da1624a13d67470d3cc0c9cde4996f3db047f | iris-ep01-sg17-english-braces-ab-probe | sd-SG17A-p-2 | A-minimal-padded | b63f349bbe6b004b2429b165818da1624a13d67470d3cc0c9cde4996f3db047f | ANALYZER | COPY_FALSE | RE_VOICED_OWN_AUDIO | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG17A-p-2/SG17A/gate/sync-summary.json |
| sg17b-p-1-english-braces-padded | native:4de4bdb69755bece72ac46228e9631b6b5abfaeecfb4dca3951afa6072d700f2 | iris-ep01-sg17-english-braces-ab-probe | sd-SG17B-p-1 | B-english-braces-padded | 4de4bdb69755bece72ac46228e9631b6b5abfaeecfb4dca3951afa6072d700f2 | ANALYZER | COPY_FALSE | RE_VOICED_OWN_AUDIO | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG17B-p-1/SG17B/gate/sync-summary.json |
| sg17b-p-2-english-braces-padded | native:1538d9e2e22d05b185d0fd3a29d4824b6468ccb6b18dfdbc0bbbd7b491793534 | iris-ep01-sg17-english-braces-ab-probe | sd-SG17B-p-2 | B-english-braces-padded | 1538d9e2e22d05b185d0fd3a29d4824b6468ccb6b18dfdbc0bbbd7b491793534 | ANALYZER | COPY_FALSE | RE_VOICED_OWN_AUDIO | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG17B-p-2/SG17B/gate/sync-summary.json |
| sg16x-r-1-r4 | native:f8c53b27b0cc71c85ee39119e1bedf61ffb9b64ac886575364bf11588d65ab89 | iris-ep01-s031-048-r4-short-window | sd-SG16x-r-1 | r4-short-window-english-braces | f8c53b27b0cc71c85ee39119e1bedf61ffb9b64ac886575364bf11588d65ab89 | ANALYZER | COPY_TRUE | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG16x-r-1/SG16x/gate/sync-summary.json |
| sg16x-r-2-r4 | native:d16b18f28a6bdeb4921c05c1172b09ecf615906d4c51031f1fd328f901a4fa86 | iris-ep01-s031-048-r4-short-window | sd-SG16x-r-2 | r4-short-window-english-braces | d16b18f28a6bdeb4921c05c1172b09ecf615906d4c51031f1fd328f901a4fa86 | ANALYZER | COPY_TRUE | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG16x-r-2/SG16x/gate/sync-summary.json |
| sg16y-r-1-r4 | native:d01bb7922f3b340b4d55ad375d214dcb7b498666125a0e50093337b3b2679214 | iris-ep01-s031-048-r4-short-window | sd-SG16y-r-1 | r4-short-window-english-braces | d01bb7922f3b340b4d55ad375d214dcb7b498666125a0e50093337b3b2679214 | ANALYZER | COPY_FALSE | RE_VOICED_OWN_AUDIO_STABLE_LAG | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG16y-r-1/SG16y/gate/sync-summary.json |
| sg16y-r-2-r4 | native:b33c935adbcfdc09af927a0a28d37c200bd276ae5ee868457a52a180a0ea61d7 | iris-ep01-s031-048-r4-short-window | sd-SG16y-r-2 | r4-short-window-english-braces | b33c935adbcfdc09af927a0a28d37c200bd276ae5ee868457a52a180a0ea61d7 | ANALYZER | COPY_FALSE | RE_VOICED_OWN_AUDIO_STABLE_LAG | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG16y-r-2/SG16y/gate/sync-summary.json |
| sg18x-r-1-r4 | native:d5dee82a57d635cb7098b4ec5a01ed6ac912a8ccd6902450543dc7b9a633a05c | iris-ep01-s031-048-r4-short-window | sd-SG18x-r-1 | r4-short-window-english-braces | d5dee82a57d635cb7098b4ec5a01ed6ac912a8ccd6902450543dc7b9a633a05c | ANALYZER | COPY_TRUE | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG18x-r-1/SG18x/gate/sync-summary.json |
| sg18x-r-2-r4 | native:3a49621b05bd01cd9231c5ecbf03ae0017a336bdbde8d70a1a2d1fd7f31d5db7 | iris-ep01-s031-048-r4-short-window | sd-SG18x-r-2 | r4-short-window-english-braces | 3a49621b05bd01cd9231c5ecbf03ae0017a336bdbde8d70a1a2d1fd7f31d5db7 | ANALYZER | COPY_TRUE | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG18x-r-2/SG18x/gate/sync-summary.json |
| sg18y-r-2-r4 | native:8e7c85c2c20b87ea9c5a06f1aaa75a8dfae4f9c79d265d3ff7d93fa63fdc1e89 | iris-ep01-s031-048-r4-short-window | sd-SG18y-r-2 | r4-short-window-english-braces | 8e7c85c2c20b87ea9c5a06f1aaa75a8dfae4f9c79d265d3ff7d93fa63fdc1e89 | ANALYZER | COPY_FALSE | RE_VOICED_OWN_AUDIO | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG18y-r-2/SG18y/gate/sync-summary.json |
| sg18y-r-3-r4 | native:1afce3556edffd98ee5fb927482378b590df3cba694a10e5dfca9aa7724376ac | iris-ep01-s031-048-r4-short-window | sd-SG18y-r-3 | r4-short-window-english-braces | 1afce3556edffd98ee5fb927482378b590df3cba694a10e5dfca9aa7724376ac | ANALYZER | COPY_TRUE | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG18y-r-3/SG18y/gate/sync-summary.json |
| sg20x-r-1-r4 | native:cd4119ce1f587ac5abfc7528b492d557ab6a71998c0737f58fdf11e9593e36e3 | iris-ep01-s031-048-r4-short-window | sd-SG20x-r-1 | r4-short-window-english-braces | cd4119ce1f587ac5abfc7528b492d557ab6a71998c0737f58fdf11e9593e36e3 | ANALYZER | COPY_FALSE | RE_VOICED_OWN_AUDIO | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG20x-r-1/SG20x/gate/sync-summary.json |
| sg20x-r-2-r4 | native:56d9e491a5958fbfcc0728d7bb2e5355a854742dcf2ede7cb915d2c673347363 | iris-ep01-s031-048-r4-short-window | sd-SG20x-r-2 | r4-short-window-english-braces | 56d9e491a5958fbfcc0728d7bb2e5355a854742dcf2ede7cb915d2c673347363 | ANALYZER | COPY_FALSE | RE_VOICED_OWN_AUDIO | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG20x-r-2/SG20x/gate/sync-summary.json |
| sg19-a-2-pre-probe | native:697c36de92d21875d69e03bdb4d308dfba2f36583f5a28fe23dcaec5e9b64197 | iris-ep01-sg19-pre-probe-sung-unit | sd-SG19-a-2 | chinese-prompt-no-english-braces | 697c36de92d21875d69e03bdb4d308dfba2f36583f5a28fe23dcaec5e9b64197 | ANALYZER | COPY_TRUE | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG19-a-2/SG19/gate/sync-summary.json |

## Assessment

- **本段完成到哪。** 生成阶段结束（任务账 11,920 积分，上限 15,000）、剪辑完成、review-v1 获使用者认可。这是使用者对该段观感的认可，不代表工程验证完成：Harness 验证、commit、push 都还没做。
- **「技术 PASS」与「使用者认可」是两层。** `qa.json` 顶层 `red.pass` 仍为 false（f328，1 帧），使用者把它改判为次要；不要把「认可」写成「QA 全 PASS」。
- **念白/唱段对口型：没有定论。** 11 个视频单元里，念白对口型整段对齐从未稳定出现；真正可用的是「量、剪、盖」选段 + 逐句 knot 对齐 + 跳切 + 插镜盖。r4 短窗口写法在 3 个单元里出现 copy=true，但在同类写法的 SG17B、SG16y、SG20x、SG18y r-2 里没有，SG19 a-2 在不同写法下也 copy=true；不能说「写法让它成立」。机制未证，n 小。
- **去译文基本有效，但不是干净对照。** SG12 b-1/b-2 是英文；译文引用与 a-3 的中文同时出现，但 a-1 同 prompt 不是中文，且 b 轮同时改了动作。
- **主会话看帧 + 4K 复核比 Gate 小图可靠。** 耳挂灯被 1080 小图误判，经 4K 裁切推翻，这是本作品的有界观察。
- **Agentcut 页面导出的硬上限仍在**（见 2026-11-23 记录），本段又出现 1 帧手背彩点，使用者判次要。

## Remaining Risks Or Next Work

- **Harness 验证与提交（待做）。** 先对 exact staged snapshot 跑所需级别的 Harness 验证并留 receipt，再按使用者选定的范围 commit，push 并核对远端 `main` SHA。本记录写成时没有任何一项完成。
- **下一段 s049–s061（待做）。** 沿用本段的规则：念白/唱段不写译文、不写走向镜头与出画、prompt 从首帧状态写起；若再拍念白对口型，需要先决定要不要继续用 r4 写法（见 Learning 评估的升级条件）。
- **开头 0–59.23 s 仍是暂定。**
- **丢拍与简化是使用者认可时接受的已知短板**（s037d 放碗、s041c 伸手、眼睛变浅、s036 静图 3.7 s、方案里没做的后期项）；后续若有人要升级为 Final Acceptance，需要重新问使用者，不要当作已清零。
- **`lips` 里 s031c 与 s037d 的 `sync_check` 报错未修**（numpy 形状不一致），这两段的口型证据来自 Gate 阶段测量，不是 `qa.json` 的 analyzer 值。
- **「4 fps」Gate 抽帧频率没有在磁盘文件里找到出处**；若要把它写成限制，需要查 `shot-gate-reviewer` / `video-analysis` 的实际参数。
- **旧记录对账。** 已在 [2026-11-23 记录](2026-11-23-iris-ep01-s015-030-shoot-and-assembly-checkpoint.md)加 supersession 提示：「commit / push 待做」与「转身候选待确认」两项已被取代（见该记录顶部）。2026-11-19 与 2026-11-20 的三份旧记录的提示都已指向 2026-11-23 记录，本次没有改动它们。
- **`run_unit.sh` 读不到提交后余额时写假 spend.json 的问题**（2026-11-23 记录已列）本记录没有核对是否已修。
- **仓库外资产。** Agentcut 项目 `iris-ep01-s031-048` 在 `/home/reggie/Agentcut/projects/` 一类的仓库外目录（具体名称本次没有核对），不在 Git；`.gitignore` 排除 `*.mp4`。
- **本记录期间没有付费或生成调用**；本段此前的付费提交都由主会话在任务内完成，花费见「花费口径」。

## Learning 评估（2026-11-26）

两项评估，结论都是 `no_candidate`；没有创建候选文件，没有采纳任何东西，没有修改任何 Skill、Policy、Preflight、Contract 或 Gate。已对上一段的 `seedance-turn-away-unstated-back-details`（active v1、`ADOPTED`）检索了本段证据，没有发现需要更新或反驳它的新证据（本段 SG12 的转头是「转头不回」，不是「转身时补造背面物件」）。

1. **「r4 短窗口 + {英文逐字稿} + 补静音到生成时长」：`no_candidate`。** 理由：(a) 没有对照臂：SG17 探针只有 `A 精简` 对 `B + {英文}`，两臂各 2 条全 copy=false，探针的结论只是「词更准、时间没变、copy 没变」。(b) 支持与反例数量相当：r4 的 10 条里 5 条 copy=true（SG16x、SG18x、SG18y r-3，3 个单元），另 5 条 false（SG16y、SG18y r-2、SG20x），加上同类写法的 SG17B 2 条 false；SG19 a-2 在不同写法下也 copy=true，说明 copy=true 不一定需要这套写法。把 3 个支持单元算作 `TWO_INDEPENDENT_ATTEMPTS` 在形式上数得出来，但反例没有被解释，结论至多是 `CONTESTED`，不是 `SUPPORTED`。(c) 混杂变量未控制：窗口长度、剪辑段内容（词数、是否含唱腔）、首帧、是否唱段、单元难度都随单元变化；同单元两条 take 结果高度相关（SG16x、SG18x、SG16y、SG20x 成对一致），实际独立单位更接近 5 个单元而不是 10 条。(d) 机制未证：没有实验说明 copy 与窗口长度、{英文}、补静音之间的关系；调研的 10/18 vs 2/20 统计本次没有重算。(e) 同一作品、同一 Provider 路线、同一使用者。升级条件：在同一首帧上对同一剪辑段做受控多臂（写法 × 窗口长度），每臂不少于 2 个独立 take；或另一作品出现同形态结果；或把本仓库 ≤6 s / ≥7 s 的 copy 统计做成可复现脚本后，单独作为窗口长度的证据（目标 owner 仍是 `seedance-authoring` 的 advisory，不是 Gate）。
2. **「念白/唱段 prompt 引用歌词中文译文会让模型改说中文」：`no_candidate`。** 理由：(a) 只有一个单元（SG12）的一个 prompt：a-1 与 a-3 是逐字相同 prompt 的两次抽样，a-3 中文、a-1 不是，形式上一支持一反例，不满足 `TWO_INDEPENDENT_ATTEMPTS`。(b) b 轮同时去了译文与动作（塞纸币、瞟眼），不是 `CONTROLLED_MULTI_ARM`（同一变量单独变化）。(c) 其余单元从 r3 起都不写译文，没有「写了译文但仍是英文」的第二个单元，也没有「写了译文且变中文」的第二个单元，无法交叉验证。(d) a-3 的 Whisper zh 检测只在 `decisions.md` 里，take 目录里没有找到原输出。升级条件：任一单元以单一变量（只加或只去译文引用）各拍 ≥2 条，或另一单元在 r3 之前的写法里出现同形态的语言切换；目标 owner 会是 `seedance-authoring` 的 advisory，而且该规则（r3 起 prompt 不写译文）已经是本作品内的使用者裁决与测试约束，不是尚缺的 Skill 条目。

其余观察没有达到门槛，只留在本记录里：「量、剪、盖」per-span Gate 与逐句 knot 对齐（2026-11-23 记录已评估为 `no_candidate`；本段再次使用，但仍无对照臂、同一作品、`lips` 里 s031c、s037d 的 analyzer 报错；若要升级仍需反例或另一作品）；Jimeng reference upload 未完成 → known_no_effect 复现（本段 2 次明确含 “reference upload” 字样，加 SG19 a-1 的「submit not confirmed」同类处理；已有先例与对账流程，属 operator/provider 运行问题，目标 owner 是 Jimeng 驱动与 `docs/jimeng-provider.md`，不是 Skill claim；若要追查为什么会反复发生，需要独立的取证而不是经验 claim）；耳挂灯被 1080 小图误判需 4K 复核、Gate 抽帧频率限制口型判断（单作品观察，且 Gate 抽帧参数本次未核）；歌词时间表缺 “crack” 两遍（数据缺陷，应修 `words.json` 或在使用时核对，不属经验 claim）；多模态 take 约 2 s 后眼睛变浅（反复出现但未做归因，也无对照）。

## Agent Guardrails

- review-v1 获使用者认可，不等于 P6、Final Acceptance、`preview_approval` 或发布；0–209 连片没有单独表态；开头 0–59.23 s 只是暂定。
- 不要把 `qa.json` 的 PASS 项说成全 PASS：`red` 仍是 `pass: false`，是使用者把彩点改判为次要，判据没有被改。
- 不要把「r4 短窗口 + {英文} + 补静音」写成已验证的 Seedance 2.0 念白对口型配方：同类写法的探针与 3 个 r4 单元都 copy=false，且 copy=true 在没有该写法的 SG19 a-2 也出现过。也不要把「删掉译文」写成已确认的语言切换原因。
- 不要把任务账 11,920 说成账号余额差；账号共用，余额差只作旁证。三个 known_no_effect 记 0，不重试同一 attempt。
- 「量、剪、盖」、人声窗口与短窗口规则只是本作品本段的使用者裁决与有界观察，不是通用规则；转身 claim 在使用者确认的 scope 内才适用。
- 本记录不 commit、不 stage；Harness 验证与提交仍待主会话完成。
