---
record_kind: media_experiment
topic_id: iris-ep01-s015-030-shoot-and-assembly-checkpoint
learning_eligibility: eligible
evidence_index_version: "1"
---

# IRIS EP01 s015–s030 拍摄与剪辑检查点：review-v1 获使用者认可（彩点改判次要），0–134 s 连片已出，验证与提交待做

Date: 2026-11-23（本机日期；数字与哈希取自磁盘文件，核不到的标 NOT_EVALUATED）

## Supersession Notice — 2026-11-26（部分取代，本记录仍可检索）

后续证据见 [2026-11-26 s031–s048 拍摄与剪辑检查点](2026-11-26-iris-ep01-s031-048-shoot-and-assembly-checkpoint.md)，以及 `git log`（`4ed70a8f`、`4ea48b83`、`8e9c1d3a`）与 `outputs/ai-city-takeover/logs/decisions.md` 2026-11-24「Learning Claim … 确认」条。下列当前面向的说法已被取代，原时序与测量作为历史保留：

- **「commit / push：待做」「本记录写成时 `outputs/ai-city-takeover/ep01/v4/` 整个目录仍未跟踪」**：本记录与 s015–s030 的脚本、记录、认可已在提交 `4ed70a8f`（「IRIS EP01 v4: s015–s030 shoot and assembly records, scripts and approvals」）入库；2026-11-26 核对时 `HEAD` 与 `origin/main` 同为 `8e9c1d3a`，说明已推送。**该提交对应的 Harness 验证与 receipt 本次没有核对，仍记为未验证。**
- **「Learning 评估」第 1 项「转身候选 `pending_candidate` / `PENDING_CONFIRMATION` / `NOT_ADOPTED`，没有 candidate checkpoint commit」**：2026-11-24 使用者原话「采纳 (Recommended)」确认该 claim，候选 checkpoint 为 `4ed70a8fc7a02177b944d4a80fc7ec0caad365da`（SHA-256 `3b94690dc6797c77afcdb639e0cada892a31630329684d423bcd60672b1942e1`），adoption 提交 `4ea48b83368456a9a89713bf270853508adbab3f`（`.agents/skills/seedance-authoring/references/seedance-2.0.md` 新增 advisory 一节），`docs/record_for_agent/learning/seedance-turn-away-unstated-back-details.md` 现为 active v1、`ADOPTED`（以该文件为准）。「Agent Guardrails」里「转身候选在使用者 exact confirmation 和目标 owner 验证前不改 Skill」已不再是当前状态；该 claim 的 scope 与 exclusions 仍按它自己的文件。
- 「Remaining Risks」里「Harness 验证与提交（待做）」「push 时连同已有 3 个本地提交一起推」同上已被取代。其余内容（使用者认可 review-v1、花费、QA 数字、「量、剪、盖」与人声窗口的 `no_candidate`、开头暂定）不受影响。

## Purpose

记下 2026-11-21 至 2026-11-23 这一段的真实状态：开头 0–59.23 s 暂定 v3 的来历，首轮副歌之后 s015–s030（歌 59.23–134.44 s）从导演方案、首帧预览、13 个 Seedance 单元的逐条 Gate 与「量、剪、盖」分段验收、到 Agentcut 版式层导出、QA、使用者认可 review-v1 的全过程，并分清：使用者裁决、Provider 与 operator 事件、主会话自审修复、技术 QA 与人工认可、花费口径、尚未做完的验证与提交。

这是新记录，不是 [2026-11-20 第二轮记录](2026-11-20-iris-ep01-v4-excerpt-round2-texture-checkpoint.md)和 [2026-11-20 Agentcut 第一轮记录](2026-11-20-iris-ep01-agentcut-ev-layout-round1-checkpoint.md)的追加：它们的主题是 36.22–59.23 s 的 v4r10c 与 stills 烘焙候选；本记录的主题是之后开头改走 Seedance 视频、s015–s030 重新按作者切镜逻辑导演并成片。那两份记录与 2026-11-19 第一轮记录当前面向的状态已被部分取代，已各加 supersession 提示。

本记录由 `memory-keeper` 子代理依主会话清单对照磁盘文件写成。读取了 `outputs/ai-city-takeover/logs/decisions.md`（2026-11-21 至 2026-11-23 各条）、`pilot/s015-030/HANDOFF-2026-11-23.md`、`pilot/opening/HANDOFF-2026-11-21.md`、`excerpt/qa/s015-030-v1/{qa.json,extra.json,s029_pager_hue.json}`、`excerpt/section2*.py` 头注释与若干 take 目录的 `fetch-result.json`、`native-prompt.zh.txt`、`gate/sync-summary.json`；重算了四个 mp4 的 SHA-256，用 ffprobe 核对了帧数、分辨率与音轨。没有重看影片，没有重跑 QA、渲染、Agentcut 或测试，没有读取 `.env`，没有调用 Provider，没有 commit，没有 stage。使用者原话取自 `decisions.md`（主会话写的日志，属二手转录）。

## Current Runtime Truth

### 使用者认可了什么、没认可什么

- **review-v1（s015–s030）已认可。** 使用者原话「认可，彩点算次要 (Recommended)」（`decisions.md` 2026-11-23 剪辑审片条）。认可范围按该条所写包括：s024 推近与口型短、s027 背景路人看镜头、s022 与 s029 不对口型、s018 轿车；红色 QA 的 6 帧彩点由使用者改判为次要。这是使用者对该段的观感裁决，不是 P6、Final Acceptance、`preview_approval` 或发布。
- **开头 0–59.23 s 是「暂定」，不是最终。** 使用者对 v3 的原话：「开头还可以」「先这样吧，做后面的」（2026-11-21 v3 审片条；同日对 v2c 说「认可，顺手修那两处小问题 (Recommended)」，对 v2d 提了静止、动作与模糊单调的意见，对 v3 做了导演层否定后又说开头可以）。主会话理解为：开头 v3 保留，后段按作者切镜逻辑重做。`excerpt/renders/IRIS-EP01-agentcut-ev-v3-000-059.mp4` SHA-256 `38dcb0e81e097c2cd2eceb6951929f8c9bf133c031571d1f2c71ddb7afb7a226`（本次重算，文件未改）。
- **0–134 连片没有单独的使用者表态。** 连片是 v3 与 review-v1 的视频流直接拼接；使用者认可的是 review-v1 这一段，没有对连片再裁决。

### 最终产物（本次重算 SHA-256 与 ffprobe）

| 文件（`outputs/ai-city-takeover/ep01/v4/excerpt/renders/`） | SHA-256 | 规格 |
| --- | --- | --- |
| `IRIS-EP01-agentcut-ev-s015-030-v1.mp4`（正式片，含声音） | `721b4c66173336a216c1dc115af50a68e6ec44ba519028936e083bfd1d25004e` | h264 1920×1080 24 fps，1805 帧；aac 48 kHz 双声道 |
| `IRIS-EP01-agentcut-ev-000-134-v1.mp4`（连片） | `a1c0c72d53766a2a1cbfeb99c710ba6885aeed45e2a48b96056a585469b02b7d` | h264 1920×1080 24 fps，3227 帧（= 1422 + 1805）；aac 48 kHz，134.458 s |
| `IRIS-EP01-s015-030-v1-picture.mp4`（引擎画面，无版式层、无声） | `0b18e930724bcaf8983831b8e7c042ae4b6351213683b1fed963f3b69cc1497e` | h264 1920×1080 24 fps，1805 帧 |
| `IRIS-EP01-agentcut-ev-v3-000-059.mp4`（开头，未改） | `38dcb0e81e097c2cd2eceb6951929f8c9bf133c031571d1f2c71ddb7afb7a226` | 本次未重新 ffprobe |

`.gitignore` 排除 `*.mp4`，这些媒体的跨机器身份只剩 SHA 与 JSON。Agentcut 项目 `/home/reggie/Agentcut/projects/iris-ep01-s015-030/`（独立项目，开头项目不动）在仓库外，不在 Git 里。

### 提交与验证状态（记录时刻）

- **Harness 对 staged snapshot 的验证：待做（pending）。** 本记录写成时没有跑，也没有 receipt。
- **commit / push：待做（pending）。** `git status` 显示 `outputs/ai-city-takeover/ep01/v4/` 整个目录仍未跟踪，当前分支 `main` 领先远端 3 个提交（`cb57686b`、`9482f04d`、`964cf680`，均非本任务产物）。使用者已选的提交范围：「只交脚本、记录、认可 (Recommended)」（不提交 mp4 与生成素材，`.gitignore` 本来就排除）；push 时与这 3 个已有本地提交一起推：「一起推 (Recommended)」。这两项是使用者的选择，尚未执行，不要当成已发布。

## Session Work And Decisions

### 一、开头 s001–s010 与 s014 的来历（背景）

- 2026-11-20 起开头改为用 Seedance 按 W1 造型生成视频（Agentcut 第一轮记录里的 stills 烘焙候选被取代）。s001–s010 共 19 条成功生成、花费 7,680 积分（`pilot/opening/HANDOFF-2026-11-21.md`，任务账口径）。
- s014（MO07）r3–r6 各 2 条、每轮 800，共 3,200 积分，是本次补报的「开头 r3–r6」。r4、r5 Gate FAIL，r6-2 Gate PASS 入 v2；根因链见下文「转身」一节。
- 开头 v2c 审片认可、v2d 意见、v3 导演层否定与「开头还可以」，见上。

### 二、导演方案与首帧预览（2026-11-21、11-22）

- 2026-11-21 使用者否定 v3 的导演层：动静按镜头类别分配，没有作者式切镜动机（睁眼 → 切她看到的 → 切回 → 再进静图）。原话「按方案做首帧预览 (Recommended)」认可了 `pilot/s015-030/plan/index.html`。
- 2026-11-22 首帧预览裁决（`pilot/s015-030/preview/index.html`，decisions 逐条）：脸统一成开头的脸，s019 当快速换装来切，s025 工程师改成开头那位。首帧 P015/b…P029/a 等按页面选定。
- 2026-11-22「按页面开拍」：13 个单元（唱段 SG05–SG11 multimodal、动作 MO08–MO13 first_frame），每条 2 次，逐条 Gate 后才提交下一条。

### 三、逐条 Gate 与「量、剪、盖」分段验收（有界单例观察）

- **规则的来历。** s015 SG05 第一轮 n-1/n-2 Gate FAIL（人声从句中 59.157 s 切入、7 s 无余量、"that's my cue" 被截；n-1 行驶车辆红尾灯；两条左肩成块模糊）。第二轮 m-1/m-2 仍 FAIL（m-1 唱错词；m-2 重唱中途变速约 0.5 s，首帧车尾朝镜头的车亮红尾灯开走）。使用者「用 m-2 量剪盖 (Recommended)」：用 m-2，口型对得上的段用她（实测 lag 0.986 覆盖歌 58.3–62.1 s，lag 1.49 覆盖 61.8–63.6 s），其余用插镜盖，红尾灯后期修琥珀。
- **2026-11-22 使用者采纳 per-span Gate（作者 "Measure, cut, cover"）。** 原话「按页面做 (Recommended)」（`pilot/s015-030/gate/sg06p/index.html`）：唱段 Gate 验收改为分段，剪辑要用的几段口型对、词对、嘴不被挡、衣服道具无错即 PASS，其余用插镜盖。旧规则是整段窗口逐字同步。观看体验收益：避免为整段对齐反复重拍，口型只在实际用到的画面上要求准确。这是使用者对本作品本段的裁决，不是对 Skill、Policy 或 Gate 的修订；`AGENTS.md` 的 Per-Shot Gate 仍要求「改判次要、移出或延后须用户当次决定」。
- **人声窗口规则（使用者「照 s015 的教训改 (Recommended)」）。** SG06–SG11 人声窗口从各自句首前约 0.3 s 起、生成多 1 s 余量（剪辑按原方案时间）；首帧里车尾朝镜头的车先改成车头朝镜头或去掉。后续结果不一致：SG07 模型把 7.8 s 人声压到约 4.4 s 唱完；SG08 两条一条嘴全程闭、一条改词；SG11 两条口型仅前 2 s；SG10 B 段 PASS。所以「窗口前移 + 余量」没有被证明能让整段对齐，只是消除了 s015 那种句中切入被截断，这是有界观察，没有对照臂。
- **唱段不转身。** SG06 第一轮 m-1/m-2：唱到最后一句她松手并转身，背面首帧没给，模型补出黑色挎包、裙变短裤，m-1 听筒自己挂回钩；第二轮 p-1/p-2 把最后一句从「转身朝画面左侧走开」改为「仍站在原地看着镜头」（引用相同的参考图与人声 asset id，两版 `native-prompt.zh.txt` 只差这一句，`driver-config.json` 除对应状态文字、approval hash 与画布 `node_id` 外相同，另有 `routing_policy` sha 不同、原因未追查；本次逐文件核过，未核对 asset 背后字节），p-1 不转身奏效。使用者「按页面重拍，唱段不转身 (Recommended)」。规则：唱段里不转身，离开画面交给剪辑。
- **动作单元的同类现象（s014 MO07）。** r4 与 r5 转身时工牌消失、寻呼机跳到背后或后腰（r5-1 另有后腰寻呼机亮红）；r6 的 prompt 改为转身前先低头用右手按身前腰链上的寻呼机、松手，并写明「寻呼机和工牌一直挂在她身前的腰链上，背对镜头时看不见」。r6-2 Gate PASS，r6-1（同 prompt）Gate FAIL（甩袖来回两次、沿中线后退、开头 0.75 s 定格），说明同 prompt 仍有抽样差异。r6 同时改了三处（手部动作前移、写明挂在身前、s014c 改作插入镜头），不是单变量。
- **逐镜用法。** 各镜的选用与剪辑用法见 `pilot/s015-030/HANDOFF-2026-11-23.md` 的表，此处不复制。几项值得单独记住：s018 与 s025 因首帧或晃车问题改用静图（s018 照作者 S0002 高处俯拍静图慢拉远；s025 静图 + 后期猛晃）；s020 使用者当次决定把封存的「推倒扣地」改判为「开始推倒」；s027 背景路人看镜头使用者判次要；s028 剪掉反向走的 2 s；s029 与 s022 使用者定不对口型。
- **s024 口型的两个数字不一致，未调和。** Gate 阶段记 m-2 口型 103.29–106.50 s 对上（lag 0.5）；`qa.json` 的 `lips.s024` 按 lag 0.029 量出可见口型同步段 105.453–106.213 s，`covered_share` 0.237。使用者认可时明确包含「s024 推近/口型短」，所以这是已知、已被使用者接受的短板，但两套测量的差异原因没有核实。

### 四、Jimeng 与 operator 事件（本段共 4 类）

1. **「reference upload did not complete」= known_no_effect（s025 MO11 n-1）。** operator 报「Jimeng reference upload did not complete; generation was not submitted」；canonical submit 回执 `known_no_effect`、`external_effect_id` 为 null、预留 released、`actual_cost` 0，余额前后 82226。主会话按 `MO01-o-2` 先例把任务账记为 `known_no_effect`，不重试同一 attempt；n-2（258832ea…）正常出片。
2. **「operator window expired」：归档旧窗口、重封。** 2026-11-23 SG10 两条提交被 operator 在写 ledger 前拦下（窗口 6 h，05:12Z 到期，余额 81906 不变）。主会话把 SG10、MO12、MO13、SG11 共 8 个 take 的 `operator-bound.json` 归档为 `operator-bound.expired-<时间>.json`（本次核对 8 个文件都在磁盘上）后重封 6 h 新窗口，上限与 id 不变，`window_history` 记录；没有复用旧 permit。
3. **`outcome_unknown` 经 `VideoGenerationService.recover_jimeng_unknown_once` 恢复（s028 MO13 n-1）。** 提交报「Jimeng canvas save is unconfirmed; query the sealed task only.」，之后 poll 报 unknown outcome，ledger 停在 submitting；`balance.cjs` 同时报「expected exactly one IRIS canvas page」，n-2 因读不到余额停止、未提交。根因（HANDOFF 与 decisions）：画布标签 URL 带查询串（`?enter_from…`），使「恰一页」检查失败。使用者把浏览器整理成单一画布标签页，主会话把同一标签导航到精确项目 URL（无点击）。随后按 `docs/jimeng-provider.md` 调 `recover_jimeng_unknown_once` 一次（只读回），结果 ACCEPTED（新回执 `7feefe58…`，画布快照 `157af32f…`），poll succeeded，取回 `47c40d7a…`，ledger 改 submitted 并附恢复说明。余额 79986 → 79506，差 480 = 6 s × 80，与恢复结果一致（账号共用，余额差仅作旁证）。没有盲目重试、重签或 remint。
4. **`run_unit.sh` 读不到提交后余额时写假 spend.json。** 本次核对：`sd-MO13-n-1/MO13/spend.json` 内容是 `{"unit":"MO13","balance_before":79986,"balance_after":,"spent":79986,...}`，不是合法 JSON，`spent` 是假值（脚本 `$((B0-B1))` 在 B1 为空时变成 B0）。本记录没有发现该脚本已被修复；以任务账为准，不要引用这个 `spent`。

### 五、花费口径

- **任务账（4k 80 积分/秒）：s015–s030 合计 16,000 积分**（`HANDOFF-2026-11-23.md`；逐项相加：SG05 2,400 + SG06 2,240 + INS16 640 + SG07 1,440 + MO08 960 + MO10 800 + MO09 800 + SG08 1,280 + SG09 960 + MO11 320 + SG10 1,280 + MO12-n 640 + MO13 480 = 14,240，+ SG11 1,120 = 15,360，+ MO12-p 640 = 16,000；本次重算一致）。开头 s014 r3–r6 另 3,200 积分。
- 账号多人共用，余额差只作旁证，不当作本任务花费。MO11 n-1 的 `known_no_effect` 记 0。INS16 因即梦配置合同最短 4 s，实际 640，比使用者看到的约 480 多约 160，属任务内预算自控、事后告知。
- 「待确认」：本记录未对账号积分明细做独立核对；此前记录里的来源不明积分下降（见第二轮记录）未在本段重现，也未被解释。

### 六、剪辑组装方法与主会话自查修复

- 方法（`excerpt/section2.py` 头注释，本次读取）：`--prep` / `--blur` / `--build` 出 `data/edl-s015-030-v1.json` 与 composition，用 HyperFrames 引擎渲 picture-only 画面（`--crf 16`，开头 v3 的印刷 pass：逐镜模糊分类、副歌线网、主歌点网）；版式层、歌词、声音在 Agentcut 独立项目 `iris-ep01-s015-030`（`section2_layers.py`）；`section2_qa.py` 出 `qa.json`，`section2_review.py` 出 `pilot/s015-030/review-v1/index.html`（29 张切点图加页面）。切点吸附到 `beats.json` 拍点（|cut − beat| ≤ 0.03 s）。
- **4 项由主会话自己看帧发现并修复**（`qa/s015-030-v1/extra.json`「deviations」）：
  1. **B 类清晰区没有跟着人。** 手写区域 s021 0.30–0.80 把她的头切在外面，脸与背景一起被虚；s023 区域 0.82–1.0 完全没框到她（她在 0.65–0.88）。改为整幅画面跑 u2netp matte 跟人，s017p1、s017p2、s021、s022、s023 重做模糊。
  2. **印刷着色器的红色上限是硬开关**（`redHue > 0.5`），在大片平滑暖棕虚化背景（s022）上画出锈色等高线；模糊后的图本身是平滑的，所以不是高斯模糊的问题。改为连续权重 `uCapSoft`，只在本段 EDL 打开，开头的 EDL 不受影响；原来被压的像素照样全压，边界外一段逐渐减压，不会比原来更红。
  3. **图形与歌词盖脸。** 加逐镜检查图形、歌词与人脸重叠：s021 歌词从右上移到左上空墙；s019 LOOK 标注从她脸上移到左上走廊；s026b 睡眠图从他头发和耳朵上移到头左侧车厢。
  4. **计数叠在一起。** s022 的 ×1/×2/×3 改为同一位置、后一个在自己的砸字帧替换前一个，并移到标题下方（基线 520 → 580），不再盖住 UNDER OATH。
- 另有两处素材层面的局部修：s018 用 `P018E/a.png`（上一轮 prompt 改图所得，非本轮生成）的深色轿车只替换 `p018-w1` 左下车框（x 0–495，y 390–845，羽化 12 px），框外逐像素与原图相同，原图 sha `5a8ac46a…` 未改；s029 寻呼机灯按有符号色相（品红侧 −26…−1°）改到琥珀 38°，只在寻呼机区域（画面高 55% 以下或 x < 0.40 w），133 帧逐帧，灯可见 14 帧，修后灯框中位色相 6–36°，QA 红色掩模在该区域最多 11 px（她手指的暖色皮肤，不是灯）。第一版的「红 +30°」规则被实测推翻（只转到 3–10°，还把指尖暖边转成黄绿）。INS16 的 n-2 也是本地局部修复（色相 +17°，区域 x0–240 y520–760）后过 Gate。这三处都是本地离线修复，不是 Provider 输出。
- 这些修复都是「主会话看帧 → 发现 → 修」，不是 QA 脚本发现的：QA 的 `flash`、`cuts`、`sound` 全 PASS，却没有一项会拦下 B 类清晰区没框到人或锈色等高线。因此技术 PASS 不代替观感检查。

### 七、Agentcut 页面导出

- 磁盘事实：`extra.json` 记录 Agentcut 图层在独立项目 `iris-ep01-s015-030`，导出 `normalizeLoudness=false`（导出报告增益 0 dB、限幅 0 dB）；`decisions.md` 记使用者原话「你自己点」授权主会话在自动化浏览器页打开该项目后导出。
- 主会话转述（本记录没有独立证据）：Agentcut bridge 的编辑器页面拒绝程序化切换项目；在使用者授权下，主会话把自动化浏览器的 studio 页（CDP 19333）导航到 `?project=` 地址。
- 页面导出（Mediabunny）不认 `quality` 参数：请求 `quality=maximum`，文件大小基本不变（58.73 → 58.69 MB，约 6.0 Mbit/s），`extra.json` 判定「页面导出没有可用的更高质量设置」。
- 因此 H.264 对点网（halftone）的色度压缩在手部皮肤上产生单像素红色彩点，见下一节红色项。

### 八、后台任务丢失与重派

剪辑执行器曾卡在等待后台 shell：账号切换（ccam）时后台 shell 与子代理被杀，无法恢复。主会话改为从磁盘状态重派，用前台分块任务完成。这与主会话记忆里「换账号会杀掉运行中的子代理与后台 shell，须按磁盘状态重派」的已知行为一致；本段的磁盘产物没有因此缺失。

## Verification And Evidence

| 项 | 证据 | 层 |
| --- | --- | --- |
| 正式片规格 | `qa.json` `spec.pass: true`：h264 1920×1080 24 fps 1805 帧、aac 48 kHz；本次 ffprobe 一致 | execution |
| 声音 | `sound`：成片音频对母带 59.25–134.4583 s 互相关偏移 0 样本（`offset_ms` 0.0），RMS 差 −0.061 dB；全片 11 处窗口对母带偏移都是 0 样本（`extra.json`）；声音是一整条母带重编码，不是两段拼接 | analyzer |
| 闪烁 | `flash`：每秒最多 2.0 次（cell 13、frame 1453），无 3 次以上窗口，无单帧跳变；与第二轮记录 v4r10c 的 3.0 无余量不同，本段有余量 | analyzer |
| 切点 | `cuts`：29 个切点全部 `pass`（与最近拍点差 0.0 s，`cut_dt_beat` 全为 0.0，成片帧与拍点差最大 0.0203 s（本次对 29 项重算））；画面差分峰值 28 个正好落在切点帧上，s028a（帧 1453）峰值在 1456，在 ±3 帧判据内（`pass: true`） | analyzer |
| 口型 | `lips` 逐段：s015a 0.454、s015b 0.795、s016a 0.927、s016b 0.998、s017s 0.947、s024 0.237、s026c 0.633（`covered_share`，可见口型同步段占该剪段的比例）；s017a 的 `sync_check` 在 0.92 s 短段上报错 → NOT_EVALUATED（画面帧 20/22 与预期一致；该段用 Gate 已测的 m-1 对口型段 72.156–73.136 s，lag −0.2249） | analyzer + 部分 NOT_EVALUATED |
| 红色 | `red`：903 帧（每 2 帧抽 1）中 6 帧超 12 px：f456（s017b，最多 45 px）与 f1694、1696、1722、1724、1726（s029，最多 24 px）；`pass: false`。`extra.json` 判定它们是手部皮肤上的单像素压缩色噪（点网经 H.264 的色度噪点），纯画面同位置 0 px，不在图形上，改版式层之前同样是这 6 帧；按原判据仍记为未通过 | analyzer（FAIL，判据未改） |
| 红色判定的改判 | 使用者原话「认可，彩点算次要 (Recommended)」：彩点改判次要。这是使用者对该项的当次决定；`qa.json` 顶层仍是 `red.pass: false`，没有改写 | human（改判） |
| 连片 | `extra.json`：开头 v3（1422 帧，文件未改）与本段（1805 帧）视频流直接拼接（不重编码），共 3227 帧；本次 ffprobe 核对帧数 3227、音轨 134.458 s 一致；「解码后逐帧与两段原片一致」是 `extra.json` 的记载，本次没有重跑逐帧比对 | execution（部分转述） |
| 观感 | 使用者看过 review-v1 并认可；本记录没有重看影片 | human |
| Harness / staged snapshot | 未跑，待做 | NOT_EVALUATED |

## Evidence Index

行分三组。(1) 成片与连片：同一正式片的技术层与人工层共用一个 `independence_key`；连片是另一个文件。(2) SG06 的转身对照：相同参考图与人声 asset id、两版 prompt 只差最后一句，两个 arm 各自一个 key。(3) MO07 r5 与 r6：同一首帧，r6 同时改了三处，不是单变量，只作辅助。SG06-m-2、SG06-p-2、MO07-r5-2 同属各自的 prompt 轮次，不另登记 key，避免同一 prompt 的两条 take 被当成两个独立单位。所有 PASS / FAIL 的含义仅限当次 Gate 或 QA 的具体判据，不是观感质量或最终验收。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s015-030-film-v1-qa | native:721b4c66173336a216c1dc115af50a68e6ec44ba519028936e083bfd1d25004e | iris-ep01-s015-030-assembly-v1 | agentcut-export-s015-030-v1 | N/A | 721b4c66173336a216c1dc115af50a68e6ec44ba519028936e083bfd1d25004e | ANALYZER | FAIL | RED_SPECKS_H264_CHROMA_6_FRAMES | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/excerpt/qa/s015-030-v1/qa.json |
| s015-030-film-v1-human | native:721b4c66173336a216c1dc115af50a68e6ec44ba519028936e083bfd1d25004e | iris-ep01-s015-030-assembly-v1 | agentcut-export-s015-030-v1 | N/A | 721b4c66173336a216c1dc115af50a68e6ec44ba519028936e083bfd1d25004e | HUMAN | ACCEPTED | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | s015-030-film-v1-qa | outputs/ai-city-takeover/logs/decisions.md |
| joined-000-134-v1 | native:a1c0c72d53766a2a1cbfeb99c710ba6885aeed45e2a48b96056a585469b02b7d | iris-ep01-s015-030-assembly-v1 | stream-copy-join-000-134-v1 | N/A | a1c0c72d53766a2a1cbfeb99c710ba6885aeed45e2a48b96056a585469b02b7d | ANALYZER | PASS | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/excerpt/qa/s015-030-v1/extra.json |
| sg06-m-1-turn-away | native:9713392a407869acfbf1d306eaa3001f11480eb5a1019e8459b5a67808e6d285 | iris-ep01-sg06-turn-away-vs-stay | sd-SG06-m-1 | turn-away-in-sung-unit | 9713392a407869acfbf1d306eaa3001f11480eb5a1019e8459b5a67808e6d285 | GATE_REVIEW | FAIL | TURN_AWAY_BACK_DETAILS_INVENTED | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG06-m-1/SG06/fetch-result.json |
| sg06-p-1-stay-in-place | native:335ce608b539e909bff4441b9801d23c0ee54bef4a643ae1ebdcf1c849c8a003 | iris-ep01-sg06-turn-away-vs-stay | sd-SG06-p-1 | stay-in-place | 335ce608b539e909bff4441b9801d23c0ee54bef4a643ae1ebdcf1c849c8a003 | GATE_REVIEW | SPAN_PASS | FOREARM_EXTRA_CORD_AFTER_RELEASE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG06-p-1/SG06/fetch-result.json |
| mo07-r5-1-turn-unstated | native:de9eba5cc9982226915632598a36993d6fab1bbe3b123632b46a5e52c8529646 | iris-ep01-mo07-turn-back-props | sd-MO07-r5-1 | r5-turn-back-props-unstated | de9eba5cc9982226915632598a36993d6fab1bbe3b123632b46a5e52c8529646 | GATE_REVIEW | FAIL | PAGER_BADGE_MOVED_OR_VANISHED_ON_TURN | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r5-1/MO07/fetch-result.json |
| mo07-r6-2-front-chain-stated | native:f8ea9ac669f8db68315817e8d2ed845f24d9c6dd52ee31cdcc24d11bc0195950 | iris-ep01-mo07-turn-back-props | sd-MO07-r6-2 | r6-front-chain-stated | f8ea9ac669f8db68315817e8d2ed845f24d9c6dd52ee31cdcc24d11bc0195950 | GATE_REVIEW | PASS | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r6-2/MO07/fetch-result.json |
| mo07-r6-1-front-chain-stated | native:c13132334e83099440f035dcfc2aadd5b588155cdf68088721237f0c6fec357b | iris-ep01-mo07-turn-back-props | sd-MO07-r6-1 | r6-front-chain-stated | c13132334e83099440f035dcfc2aadd5b588155cdf68088721237f0c6fec357b | GATE_REVIEW | FAIL | SLEEVE_FLICK_TWICE_AND_BACKPEDAL | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-r6-1/MO07/fetch-result.json |

## Assessment

- **本段完成到哪。** 生成阶段结束（任务账 16,000 积分）、剪辑完成、review-v1 获使用者认可。这是使用者对该段观感的认可，不代表工程验证完成：Harness 验证、commit、push 都还没做。
- **「技术 PASS」与「使用者认可」是两层。** `qa.json` 顶层 `red.pass` 仍为 false，使用者把它改判为次要；不要把「认可」写成「QA 全 PASS」，也不要把 `red` 的未通过写成「成片有明显红点」。
- **主会话自查比脚本更能发现问题。** 4 项自查修复里没有一项能被现有 QA 脚本发现；B 类清晰区、锈色等高线、盖脸、计数叠放都来自逐帧看片。这是对本段的有界观察，不是「QA 无用」。
- **「量、剪、盖」本段确实用上了，但覆盖度差别很大。** 从 s016b 的 0.998 到 s024 的 0.237；使用者认可时已经看到「口型短」并接受。分段验收没有提高口型质量本身，只是把「哪段能用」说清楚。
- **Agentcut 页面导出有硬上限。** 页面导出忽略 `quality`，约 6 Mbit/s，点网经 H.264 的色度噪点在手部皮肤上产生 6 帧单像素红色彩点，是现行导出路径的限制，不是本次剪辑的缺陷。要彻底消除需要换导出路径，超出本段范围。

## Remaining Risks Or Next Work

- **Harness 验证与提交（待做）。** 先对 exact staged snapshot 跑所需级别的 Harness 验证并留 receipt，再按使用者选定的范围 commit（脚本、记录、认可），push 时连同已有 3 个本地提交一起推，并核对远端 `main` 的 SHA。本记录写成时没有任何一项完成。
- **开头 0–59.23 s 仍是暂定。** 使用者只说「还可以」，没有最终认可；v4r10c 的 3.0 次/秒闪烁无余量问题不属于 v3，而 v3 的闪烁数没有在本次读取。
- **s027 背景路人看镜头、s024 推近与口型短、s022 与 s029 不对口型、彩点** 都是使用者认可时接受的已知短板，后续若有人要升级为 Final Acceptance，需要重新问使用者，不要当作已清零。
- **`run_unit.sh` 的 spend.json 假数问题未见修复。** 下次提交前若余额读取失败，仍会写出非法 JSON；以任务账与余额差对账。
- **operator 的 6 小时窗口易过期。** 本段两次遇到（11-21、11-23；更早的 11-20 也有），机器休眠会让后台任务晚于窗口执行；每次过期都需要归档重封，不复用旧 permit。
- **仓库外资产。** Agentcut 项目 `iris-ep01-s015-030` 与 `escape-velocity-replica` 在 `/home/reggie/Agentcut/projects/`，不在 Git；改动后需要重新导出。`.gitignore` 排除 `*.mp4`，媒体的跨机器身份只剩 SHA 与 `qa.json`。
- **本段没有对 s015–s030 之外的镜头重新检查。** s001–s014 的逐镜 Gate 结果来自 `decisions.md`，本记录没有重读。
- **本记录期间没有付费或生成调用**；本段此前的付费提交都由主会话在任务内完成，花费见「花费口径」。

## Learning 评估（2026-11-23）

两项评估，主会话回报的结论如下；候选未采纳，也没有修改任何 Skill、Policy、Preflight、Contract 或 Gate。

1. **「转身时首帧没有背面，模型会补造背面物件；唱段不转身、动作段写明物件挂在身前」：`pending_candidate`。** 候选文件 `docs/record_for_agent/learning/seedance-turn-away-unstated-back-details.md`，`PENDING_CONFIRMATION`，`NOT_ADOPTED`。依据：SG06 的两个 arm 引用相同参考图与人声 asset、prompt 只差最后一句（近似单变量对照，另有 routing policy sha 不同未追查；m 轮 FAIL、p 轮不转身奏效），加上另一个镜头 MO07 的 r5 FAIL 与 r6-2 PASS，满足 `TWO_INDEPENDENT_ATTEMPTS`；限制是同一作品、同一 Provider 路线、同一使用者，MO07 r6 同时改了三处，r6-1 同 prompt 仍 FAIL。**候选没有 candidate checkpoint commit 与 committed-preimage SHA，因为本子代理不 commit；主会话需要对该路径做路径受限的 candidate checkpoint 提交并计算 SHA-256 后，才能向使用者请求 Confirm / Revise / Reject。** 在此之前不得采纳，也不得改任何 Skill。
2. **「量、剪、盖 per-span Gate」与「人声窗口前 0.3 s + 余量」：`no_candidate`。** per-span Gate 是使用者在本作品内的裁决，本段共 8 个唱段剪段用到（其中 s017a 的 `sync_check` 报错），但没有对照臂（没有同一镜头整段验收 vs 分段验收的比较），使用者的认可针对整段成片、没有逐段表态，s024 覆盖度只有 0.237 且两套测量不一致，s017a 的 `sync_check` 报错；它还与现有 Gate 的 `usable_song_s` 与「改判须用户当次决定」语义重叠，没有给任何 owner 一个可验证的新动作。窗口规则则明显不一致（SG07 压缩、SG08 与 SG11 口型失败、SG10 通过），无法归因。2026-11-20 记录里该方向的升级条件仍然有效：补一个以插镜覆盖失败（或重拍成功恢复口型）的反例，或另一作品出现同形态证据。

其余观察没有达到门槛，只留在本记录里：u2netp 跟人与 `uCapSoft`（单作品单次修复，无第二个独立实例）；Jimeng 的 query-string 导致「恰一页」检查失败（一次事件，已有 canonical 恢复路径与 `docs/jimeng-provider.md`；若再出现，评估是否由 `balance.cjs` 与 `jimeng_browser.cjs` 的检查自身处理查询串，目标 owner 是代码，不是 Skill）；`run_unit.sh` 假 spend.json（真实缺陷，应按 `.agent/bug-memory/` 的可复现回归标准另行判断，不属于经验 claim）；Agentcut 页面导出忽略 `quality`（单次工具限制）。

## Agent Guardrails

- review-v1 获使用者认可，不等于 P6、Final Acceptance、`preview_approval` 或发布；0–134 连片没有单独表态；开头 0–59.23 s 只是暂定。
- 不要把 `qa.json` 的 PASS 项说成全 PASS：`red` 仍是 `pass: false`，是使用者把彩点改判为次要，判据没有被改。
- 不要把任务账 16,000（加开头 s014 的 3,200）说成账号余额差，也不要引用 `sd-MO13-n-1/MO13/spend.json` 的 `spent`。
- 遇到 `outcome_unknown` 先查画布标签 URL 是否带查询串与是否恰一页，再走 `recover_jimeng_unknown_once`；不要盲目重试、重签或 remint。`operator window expired` 与 `known_no_effect` 的处理按上文先例，不复用旧 permit。
- 「量、剪、盖」与人声窗口规则只是本作品本段的使用者裁决与有界观察，不是通用规则；转身候选在使用者 exact confirmation 和目标 owner 验证前不改 Skill。
- 本记录不 commit、不 stage；Harness 验证与提交仍待主会话完成。
