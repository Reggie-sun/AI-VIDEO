---
record_kind: media_experiment
topic_id: iris-ep01-v4-excerpt-round2-texture-checkpoint
learning_eligibility: eligible
evidence_index_version: "1"
---

# IRIS EP01 v4 样片第二轮（歌 50.93–59.23）与观看尺度质感：v4r10 获认可、v4r10c 为当前版本，闪烁与开头待续

Date: 2026-11-20（本机日期；时间与数字取自 `outputs/ai-city-takeover/logs/decisions.md` 2026-11-19 下午至 2026-11-20 各条与各 `pilot/` 证据）

> **Supersession Notice — 2026-11-23（部分取代，本记录仍可检索）。** 后续证据见 [2026-11-23 s015–s030 拍摄与剪辑检查点](2026-11-23-iris-ep01-s015-030-shoot-and-assembly-checkpoint.md)。下列当前面向的说法已被取代，原时序、测量与使用者对 v4r10 的裁决作为历史保留：
>
> - **「v4r10c 为当前版本 / 样片只有 36.22–59.234」**：开头改走 Seedance 视频，0–59.23 s 暂定为 `IRIS-EP01-agentcut-ev-v3-000-059.mp4`（SHA-256 `38dcb0e81e097c2cd2eceb6951929f8c9bf133c031571d1f2c71ddb7afb7a226`，使用者「开头还可以」，暂定非最终）；s015–s030 已拍完并成片，使用者 2026-11-23 认可 review-v1（「认可，彩点算次要 (Recommended)」），另有 0–134 s 连片（`IRIS-EP01-agentcut-ev-000-134-v1.mp4`，SHA-256 `a1c0c72d53766a2a1cbfeb99c710ba6885aeed45e2a48b96056a585469b02b7d`）。v4r10c 仍是 36.22–59.23 s 那一版 stills 剪辑的历史最终稿，不再是当前样片。
> - **「Next Session Handoff」第 2、3 项已被取代**：开头 25.13–36.2 s 逻辑已由新的开头（Seedance）取代；s015 已按 W1 造型重拍（SG05，使用者「用 m-2 量剪盖」）并入 review-v1。第 1 项（压低 v4r10c 的 57.4 s 闪烁）不再作用于当前样片：新段 `qa.json` 的闪烁最大 2.0 次/秒，但 v3 开头的闪烁数本次没有读取，NOT_EVALUATED。第 4、5 项（MO07-s-1 ledger、`board/shots.json` 旧字段、windows.json、提交）本次没有逐项重核；提交与 Harness 验证在新记录中仍标为待做。
> - 本记录 Learning 评估 `no_candidate` 不变；新记录另有一条不同主题（转身镜头）的 pending 候选。
>
> **交接更新（2026-11-20 晚，新会话先读本框与「Next Session Handoff」）。** 本文件在同一主题上原地追加，下列几处与本文件较早的叙述不同，以本框为准：
>
> 1. v4r10 的 QA 不是全 PASS（`red` FAIL，原因已定位到 s013a 手机插镜，见 Current Runtime Truth「后续」）。`decisions.md` 的「QA 全 PASS」已由主会话在「2026-11-20 更正」条更正。
> 2. **当前版本是 v4r10c**（SHA-256 `e1439c068b1386d2d53e9f07f0c591d6f5b85acd42307f4019d5647448b2e8db`，QA 全 PASS），不再是 v4r10。使用者的「可以，先这样」说的是 v4r10。
> 3. 新增待处理风险：v4r10 / v4r10c 的闪烁检测恰好 3.0 次/秒，等于上限，无余量（v4r9 及更早为 1.0）。续作时先处理这一项。
> 4. 本文件下方凡是写「v4r10 的 `red` 项未诊断」「成因未诊断」「帧号口径未核对」的句子，都是写本文件第一版时的状态，现已被下文取代，保留作历史。

## Purpose

记下样片第二轮（s013、s014）与“太清晰”质感修正的真实状态，并分清：使用者裁决、逐镜 Gate 与 QA 证据、主会话自审、operator window 过期与一次未完成提交、来源不明的积分下降、尚未做完的事。这是新记录，不是 [2026-11-19 第一轮记录](2026-11-19-iris-ep01-v4-excerpt-round1-checkpoint.md)的追加：第一轮范围止于 v4r6（歌 39.674–50.93）与闭眼唱脸，本记录是第二轮镜头、斜挎带返工与观看尺度质感，主题独立；那份记录只加了一条 supersession 提示。

本记录由 `memory-keeper` 子代理依主会话清单对照磁盘文件写成，分两次写入：第一版写到 v4r10 获认可为止；交接更新（本次）补入 v4r10b / v4r10c、闪烁风险与待办。两次都没有调用 Provider，没有生成媒体，没有读取 `.env`，没有 commit。第一版重算了 v4r7–v4r10 四个 mp4 与积分截图的 SHA-256，并读取了各 `post-media-gate.json`、`ledger.json`、`spend.json`、`operator-bound*.json`、`excerpt/qa/v4r8|v4r9|v4r10`、`edl-v4r10.json` 与积分截图；交接更新另外重算了 v4r10b、v4r10c 的 SHA-256，读取了 `qa/v4r10b|v4r10c` 的 `QA.md`、`qa.json`、`grad.json`、`render-provenance-v4r10c.json`、`review/v4r10/index.html`、`build.py` 与 `src/main.js` 里的版本开关，以及 `qa.py` 的闪烁检测。仍然没有重跑 QA、`grad.py` 或测试，没有重读即梦账户，也没有重看影片。

路径自 `outputs/ai-city-takeover/ep01/v4/`（下称 `v4/`）起，除非标明 repo 路径。

## Current Runtime Truth

- **使用者裁决。** 看 v4r10（`excerpt/review/v4r10/`，审 39.674–59.234）：「可以，先这样」（2026-11-20）。这是对该 19.6 秒段的暂时认可并暂停，不是整片、P6 或 Final Acceptance，也不是对质感成因的归因，更不授权任何新提交。
- **v4r10。** `excerpt/renders/IRIS-EP01-v4-excerpt-v4r10-036-059.mp4`，SHA-256 `9a173c74ecb53d2c2e1cfefa78ae446384d406bc6780fecf8675d61f45e97055`（本次重算一致）；1920×1080、24 fps、552 帧、h264、AAC，歌 36.22–59.234，与母带切片对齐 0 样本、RMS 差 -0.016 dB。
- **（第一版写入时的状态，已被下方「后续」取代：成因与帧号口径已核清，v4r10c 已修。）`qa/v4r10/qa.json` 的 `pass` 是 `false`，与 `decisions.md` 当时写的「QA 全 PASS」不符。** 失败项只有 `red`：138 个检查帧中 83 帧有红、49 帧在“她的耳挂灯与 P0 标签之外”红像素超过 12 px（最大 445 px，最差帧号 356–384）；其余 spec、sound、cuts、lyrics、flash、chinese、logos 均 `true`。v4r7、v4r8、v4r9 的 `qa.json` 同一项 `red` 为 `true`、0 帧超限，所以这是 v4r10 的色调曲线改动之后才出现的变化。帧号 356–384 落在 `edl-v4r10.json` 里 s013a 手机插镜（帧 597 起）之外还是之内，本记录没有逐帧核对；帧号口径（是否每 4 帧采样）也未核对，成因未诊断。`qa/v4r10/` 没有 `QA.md`。使用者认可的是观感；技术 QA 的 `red` 项仍是 FAIL，在重跑并解释之前不得写“v4r10 QA PASS”。
- **v4r10 剪法（取自 `edl-v4r10.json`）。** s013a 静图 INS13-a（手机来电特写，歌 50.933–52.315，嘴在画外）→ s013b SG04-r2-1 实拍自 52.315，54.93 起停帧 → s014a MO07-s-2 片内 0–2.299 s（歌 55.078–57.377）→ s014b 同镜片内 3.0–4.393 s 跳切（歌 57.377–58.770）→ s014c 静图 INS14-b 寻呼机特写（歌 58.770–59.234，LCD 后期亮 10:02）。MO07-s-2 逐镜 Gate 的干净片段记为 0–2.25 s 与 3.0–5.057 s，EDL 的 s014a 末端比它长 0.049 s；是否为刻意取舍或需复核，本记录没有核对。
- **斜挎带 W1 定稿。** 右肩→左胯。s011（MO06-w1b，已在 v4r6）与 S14-c 为左肩→右胯，相反，已两镜重做（见下）；v4r6 里仍是旧 MO06-w1b，v4r7 起 s011 换为 MO06-s-1。
- **未提交。**（交接时仍然成立。）记录时 HEAD 为 `964cf680`；`v4/`、本记录与 2026-11-17、2026-11-19 记录、`motion-kit/tools/` 新脚本、三份 `ep01/reviews/` 文件仍在工作区，未 staged、未 commit、未 push。`.gitignore` 排除 `*.png` 与 `*.mp4`，这些媒体的跨机器身份只剩 SHA 与 JSON。

### 后续：v4r10 red FAIL 的诊断、v4r10b / v4r10c、闪烁（交接更新）

下列每项都标明来源；除非写明，数字由本次直接读取磁盘文件所得。

- **v4r10 的 red FAIL 已定位。** `qa/v4r10/QA.md`：138 帧（每 4 帧采样）中 83 帧有饱和红、49 帧在她的 matte 与 P0 ALERT RAISED 标签之外超过 12 px（960×540 下），最差 f368 445 px、f360 444 px、f364 419 px、f356 386 px、f384 385 px。`qa/v4r10c/QA.md` 的剪点表给出 s013a 从帧 353 起、s013b 从帧 386 起，所以最差帧 356–384 全部落在 s013a（手机来电插镜 INS13-a）之内。这对上了 `decisions.md`「2026-11-20 更正」条的归因：插镜里的指尖皮肤被影调曲线推进红色判定（该归因是主会话的判断；有间接支持：下面只对 s013a 收紧红色上限后，红色超标降到 0，但没有对 v4r10 做过皮肤像素的独立诊断）。第一版里「帧 356–384 在 s013a 之外还是之内未核对」一句现已有答案：之内。
- **主会话的误报。** v4r10 当时被报成「QA 全 PASS」，原因是只 grep 了各项 `pass:true` 行而漏看 `red` 与总 `pass` 为 `false`；主会话已向使用者更正（`decisions.md` 2026-11-20 更正条）。以后报 QA 以 `qa.json` 的顶层 `pass` 与 `QA.md` 的 `Overall:` 行为准。
- **v4r10b**（`excerpt/renders/IRIS-EP01-v4-excerpt-v4r10b-036-059.mp4`，SHA-256 `d5a879d257d3…c25d`，本次重算全值 `d5a879d257d37b5e186f37288b3e8c0ed4001776e1b113ba928485a3bfd7c25d`）：`src/main.js` 在 `D.version >= 14` 时加 `uRedCapPost: 0.42`（对全部镜头生效，不只插镜）。`qa/v4r10b/QA.md` 的 `red` 仍 FAIL：31 帧有饱和红、6 帧超 12 px，最差 f384 16 px，f360 / f364 / f368 / f376 各 15 px；总 `pass` 为 `false`。使用者没有看过 v4r10b。
- **v4r10c**（`excerpt/renders/IRIS-EP01-v4-excerpt-v4r10c-036-059.mp4`，SHA-256 `e1439c068b1386d2d53e9f07f0c591d6f5b85acd42307f4019d5647448b2e8db`，本次重算与 `render-provenance-v4r10c.json` 的 `final.sha256` 一致；HyperFrames 原始渲染 `hf-render-v4r10c.mp4` SHA-256 `22aba040…9bd1`，音频取自 `audio/master-v4r7-036-059.wav`，视频流复制、AAC-LC 320k）：`D.version >= 15 && shot.id === 's013a'` 时把 `uRedCapPost` 收紧到 0.30，其余镜头保持 v4r10b 的 0.42。`edl-v4r10c.json` 与 `edl-v4r10.json` 的差别只有 `version` 字段。`qa/v4r10c/QA.md` `Overall: PASS`：spec 1920×1080、24 fps、552 帧；声音与母带切片偏移 0 样本、RMS 差 -0.016 dB；12 个剪点全在拍上；歌词 37/37；`red`：138 帧中 23 帧有饱和红、0 帧超 12 px，最差 f68 / f320 / f332 各 5 px；`flash` PASS 但恰为上限（见下）；`qa/v4r10c/qa.json` 各项与总 `pass` 全 `true`。
- **v4r10c 的影调与 grad 与 v4r10 几乎相同。** `qa/v4r10c/grad.json` 对 17 帧取中位数：grad240 / grad160 为 0.1543 / 0.2040，v4r10 为 0.1546 / 0.2042，EV 为 0.1589 / 0.1818；分位 p2 / p10 / p50 / p90 中位数 10 / 15 / 43 / 153，v4r10 同值（EV 为 12 / 16 / 39 / 149）。注意：这是 `grad.json` 的 17 帧口径，与 `decisions.md` 与第一版引用的另一组数（v4r10 0.158 / 0.206、分位 12 / 16 / 43 / 154 对 EV 11 / 17 / 43 / 154）不是同一组帧，绝对值不同，只能在同一口径内比较；两个口径下 v4r10c 都与 v4r10 一致。「画面完全一致」不成立：`decisions.md` 记 368 帧对比 v4r10c 肤色略少粉、不发灰，是 s013a 的可见差异。
- **使用者与 v4r10c 的关系。** 使用者原话「可以，先这样」针对 v4r10（`review/v4r10/` 当时指向 `v4r10.mp4`）。之后审片页 `excerpt/review/v4r10/index.html` 改为 `v4r10c.mp4`（页内 h1 写「v4r10c（= v4r10 观感，修了手机特写肤色红色质检）」，title 仍写 v4r10），目录里两个 mp4 都在。`decisions.md` 与交接清单里没有使用者对 v4r10c 另行表态的记录。所以「v4r10c 是当前认可版本」是主会话裁定为沿用 v4r10 认可（依据：影调 / grad 与 v4r10 一致、只有 s013a 肤色红色的差别），不是使用者对 v4r10c 的独立裁决。
- **待处理风险：闪烁无余量。** `qa/v4r10/qa.json` 与 `qa/v4r10c/qa.json` 的 `flash.max_flashes_per_second_any_cell` 都是 3.0（WCAG 2.3.1 通用闪烁，限 3），位置 `cell 6`、`frame 497`；v4r7 / v4r8 / v4r9 是 1.0（v4r9 在 cell 2、frame 374）。`qa.py` 里该 frame 是满足「1 秒内翻转次数最多」的窗口起点，不是闪烁的中点；frame 497 对应歌 `36.22 + 497/24 = 56.93 s`，1 秒窗口覆盖到约 57.9 s，其中包含 s014b 跳切（frame 508 = 57.38 s）。「s014 跳切附近的灯管反光」是剪辑代理的判断（`decisions.md` 2026-11-20 剪辑代理补报条），我没有逐帧核对灯管反光；`cell 6` 指 4×4 网格的第 2 行第 3 列（上数第二行、左数第三格，按 `qa.py` 的行主序推算）。当前 QA 判 PASS 只因为阈值是「不超过 3」；因此它是合规但没有余量，且 v4r10 的色调曲线改动后才从 1.0 升到 3.0，v4r9 到 v4r10 之间只改了影调曲线，这是最可疑的变量，但未做对照实验，所以只是线索。

## Session Work And Decisions

### 第二轮首帧与 s013（SG04）

- 首帧 S13（工程师仰视反打、持亮屏手机）、S14（长焦 T 台尽头旋身）各 3 张，预览 `excerpt/flash/round2.html`（SHA-256 前缀 `0b137487`）。使用者：「s013 用 b、s014 用 c，拍 (Recommended)」（2026-11-19）。每镜 2 条择优。
- **SG04-r2-1 / r2-2**（同首帧同 prompt，一份 approval 覆盖两条，各 400 上限、合计 800；`pilot/sd-SG04-r2-1|2/`）。逐镜 Gate 均 **FAIL**：
  - r2-1（take SHA-256 `e18949ce…ec29`）：口型。copy=false、重唱、前段 lag 由 1.12 滑到 0.95 不稳，「I'm the call」没对上；机位、工程师手、凝视、造型、切接 PASS。可用歌 52.10–54.95。
  - r2-2（take SHA-256 `72fe8e1a…a142`）：口型同样（前段 lag 0.64 对 0.88，「I'm the call」没对上），另 f01 工程师手缺失、切接 FAIL；凝视 `NOT_EVALUATED`。可用歌 52.47–55.06。
- **使用者选剪法 A**（预览 `excerpt/review/sg04-r2/`）：「按 A 剪 (Recommended)」→ 前半句「I'm the call」用手机插镜 INS13-a 盖住，后半句取 r2-1 中同步的部分，不重拍。
- 注意：r2-1 与 r2-2 用同一首帧同一 prompt，不是两个独立证据；它们一致地在同一句失步，只说明该输入在这两次采样里没有对上这半句，不证明重拍无法修复。

### 斜挎带方向返工（s011 与 s014）

- 场记查出：已接受的 s011（MO06-w1b）与 S14-c 的斜挎带是左肩→右胯，与 W1 定稿相反，也与 s012/s013 相反；主会话放大核实。MO07-r2 判 blocked，未提交。使用者：「s014 和 s011 都重做 (Recommended)」。
- 修正首帧在原首帧上编辑，只改带子：`STRAP/s011-b`（SHA-256 前缀 `22492025`）、`s014-b`（前缀 `c85aa47e`），预览 `excerpt/flash/strapfix.html`（前缀 `188c99d4`）。使用者：「两镜都用 b，拍 (Recommended)」（2026-11-19T17:54Z）。两镜各两条，每条上限 400。
- **MO06-s-1**（take SHA-256 `234b4a7e…40c`）：Gate **PASS**，待 4K 取证补证后（logo 裁图、24 fps 落地帧）认定无新增或放大 logo；落步入 0.417 s、落地帧 f12（0.500 s）；可用片内 0.417–4.573 s = 歌 40.786–44.942。
- **MO06-s-2**（take SHA-256 `bf49d05f…19a7`）：Gate **FAIL**，t1.75 s 出现类苹果 logo。
- **MO07-s-1**：参考上传失败，未提交（见下节），没有 take。
- **MO07-s-2**（take SHA-256 `9a08bc46…256d`）：Gate **FAIL**：没有按寻呼机，她在左胯按一件黑色小件，且该件约 2.5 s 出现红灯（违反“红只在左耳耳挂”）；机位锁定、转身/甩袖/右出画、带子 PASS。使用者对 s014 选推荐剪法：「按推荐剪法 (Recommended)」→ 0–2.299 + 3.0–4.393 跳切，加寻呼机特写 INS14-b（LCD 后期亮 10:02，只在 LCD 用）。INS14-b 取“右手按侧键”版，造型核对带子末端落左胯、长袖在右臂。

### operator window 过期与 MO07-s-1 未完成提交

- **window 过期。** 2026-11-20 MO06-s / MO07-s 四条首次提交均被 `operator.py` 在写 intent / ledger 之前拒绝：「operator window expired」。旧 bound 的 `expires_at` 为 2026-11-20T00:04:14Z（`MO07-s-1` 的 `operator-bound.expired-2026-11-20T000414+0000.json` 可见，签发 2026-11-19T18:04:14Z，6 小时），后台任务约 03:43Z 才执行（疑似机器休眠，未证实）。无 intent、无 ledger、余额 40,285 不变，记 known no-effect。
- **处理。** 旧 bound 另存为 `operator-bound.expired-*.json`（留档不改），同 attempt id、同 400 上限重新封存新 6 小时 window（`issued_at` 2026-11-20T03:48:34Z、`expires_at` 09:48:34Z；本次对 MO07-s-1 的 bound 核对一致），重跑 lint 后重提交。这是同一 approval 下的新 window，不是复用旧 permit。MO06-s-1 / s-2 / MO07-s-2 的 `ledger.json` 各只有 1 条 `submitted`，intent 时间都在新 window 之后（03:48:47Z、03:56:03Z、04:04:46Z）。
- **MO07-s-1 的 ledger 是非终态。** `pilot/sd-MO07-s-1/ledger.json` 唯一一条记录 `outcome: "submitting"`（intent 04:03:17Z，`submit-intent.json` 的 `request_hash` 前缀 `422a8ee6`，上限 1 次），没有被改成终态。同目录 `MO07/spend.json` 记 `balance_before = balance_after = 37065`、`spent = 0`，错误为「Jimeng reference upload did not complete; generation was not submitted」（该文件本身不是合法 JSON）。因此“未提交、无效果”有错误原文与余额不变两项证据支持，但 ledger 仍停在 `submitting`。按 `stop_on_unknown: true`，不重试、不重提交；若要补这个 Shot，须走 canonical recovery 或新 approval，不得盲目重跑这条 id。

### 积分：只读核对

- 余额链（取自 `decisions.md`，除标明者外未重读账户）：45,565 → 40,685（r2-1 窗口降 4,880）→ 40,285（r2-2 降 400）→ 2.5 分钟无提交采样 4 次不变 → 37,465（MO06-s-1 窗口降 2,820）→ 37,065（MO06-s-2 降 400）→ MO07-s-1 不变（`spend.json` 37,065 → 37,065）→ MO07-s-2 降 400。截图右上角余额为 36,665，与 37,065 − 400 一致（推算，非独立读数）。
- **每批第一条提交窗口里余额多降了一截**：约 2,732（SG03C-d1，3,052 − 320）、4,480（SG04-r2-1，4,880 − 400）、2,420（MO06-s-1，2,820 − 400）。它们再加上更早的 9,136 与 765 两次，共五次来源不明的下降，全部落在一批的第一条提交窗口或空窗期，本项目当时均无对应提交。
- **只读核对结果。** 使用者的即梦 IRIS 画布「生成历史」与「项目积分消耗」（`review-jimeng-project-credits-2026-11-20.png`，SHA-256 `89ba53f7dae2e5b34342e8efcdca7b528b398e94bf99b11dcadfdf0a0e6d73dc`）：项目总消耗 10,663 积分、43 个任务，类型全是「视频生成」。截图本身只显示总数与任务列表，不显示每个任务的金额；「本项目每条生成都按 320 / 400 正常计费」来自 `decisions.md` 对「生成历史」逐条读数的转述，本记录没有在截图里逐条重核。所以：多降的部分没有出现在本项目的任务账里，来源 **UNKNOWN**，已请使用者核对即梦账号账单；本记录不判为 Provider 超收、也不判为本项目误提交，也没有证据说明与同账号其他窗口有关。
- 本记录修正第一轮记录的口径：那里把 d1 窗口 3,052 全算“第三次异常”，实际含 320 的正常扣费，多出的是 2,732。

### 质感：从 1080 锐度改为观看尺度

背景：第一轮记录说 v4r4 的 `lap`（1080 级锐度代理）、`sat`、`warm` 进 EV ±20%。之后的实际经过如下（数字取自 `excerpt/qa/v4r8|v4r9/grad.json`、`excerpt/review/v4r10/index.html` 与 `decisions.md`）：

- **v4r7**（SHA-256 `75f65a6a…8879`，36.22–59.234，QA PASS，含第二轮镜头）。使用者看后：「很多还是都太清晰了」（2026-11-20）。主会话自测：灰度图、BOX 缩到宽 240 与 160，取 `mean|∇|/std`，各 17 帧取中位数。EV 0.1589 / 0.1818（`grad.json`；`decisions.md` 第一次量为 0.161 / 0.185），v4r7 0.2492 / 0.3024，约 1.57 与 1.66 倍。1080 级的锐度指标被网线主导，没有暴露这个差。主会话归因：全景深、无光晕、结构柔化不足（Agent 推断）。
- **v4r8**（SHA-256 `9d50e1e6…09f6`）：背景虚化（人物 matte）、光晕、加一档结构柔化。`grad.json` 中位数 0.1560 / 0.2035，数值进 EV ±15%。主会话在宽 640 并排自审：背景大光斑像手机人像模式，T 台工程师与闭眼唱脸前景工程师被虚掉、故事关系丢失。**未交使用者。**
- **v4r9**（SHA-256 `b49f691f…665b7a`）：虚化降到 sigma 8、保护工程师、均匀雾。中位数 0.1520 / 0.1939，是 EV 的 0.96 与 1.07 倍（`grad.json` 算得 0.957 / 1.067）。主会话 640 并排自审：故事主体回来了，但影调平，亮度分位 p2/p10/p50/p90 为 EV 11/17/43/154，v4r9 为 20/25/48/121。**未交使用者。**
- **v4r10**（SHA-256 `9a173c74…7055`）：只改影调曲线对齐 EV。分位 12/16/43/154 对 EV 11/17/43/154；grad240 / 160 为 0.158 / 0.206 对 EV 0.161 / 0.185（0.98 与 1.11 倍）。注意：`qa/v4r10/` 没有 `grad.json`，这组 v4r10 数字只在 `decisions.md` 与 `review/v4r10/index.html`（取到两位小数 0.16 / 0.21，对 EV 0.16 / 0.19）；我这次没有重跑 `grad.py`，也没有重新量分位。主会话 640 并排自审通过后交使用者，使用者：「可以，先这样」。
- **边界与混杂。** v4r7 到 v4r10 之间同时改了虚化、光晕、结构柔化、雾和影调，使用者只在 v4r7（否定）与 v4r10（暂时认可）两处表态，v4r8/v4r9 是主会话自审淘汰。所以“grad 达标 + 分位对齐 + 640 并排防过度虚化”是一套被采用的方法，其中哪一项决定了使用者的观感，这里没有证据可拆。另外，使用者对 v4r6（39.7–50.9，当时 `crisp` 0.702、`screen_prominence` 0.722 仍不在 EV ±20%）曾说「成立」，随后对包含第二轮镜头的 v4r7 说太清晰；没有对 v4r6 补测 grad，所以不能判断 v4r7 的“太清晰”来自第一轮段还是新增镜头。

## Verification And Evidence

| 项 | 证据 | 层 |
| --- | --- | --- |
| v4r10 成片 | SHA-256 `9a173c74…7055`（本次重算）；`qa.json` spec/sound/cuts/lyrics/flash/chinese/logos 为 true | execution + structure |
| v4r10 `red` 检查 | `qa/v4r10/qa.json` `red.pass = false`、总 `pass = false`；与 `decisions.md`「QA 全 PASS」不符；成因未诊断 | analyzer |
| 观看尺度 grad | `qa/v4r8|v4r9/grad.json` 可核；v4r10 无 json，数字仅见 `decisions.md` 与 `review/v4r10/index.html` | analyzer |
| 640 并排自审（v4r8 淘汰、v4r9 淘汰、v4r10 通过） | `decisions.md` 与 `excerpt/review/v4r10/view640.png`；没有独立复核 | Agent 自审（非使用者） |
| SG04-r2-1 / r2-2 | `pilot/sd-SG04-r2-1|2/post-media-gate.json` 均 FAIL；`ledger.json` 各 1 次 submitted | analyzer（逐镜 Gate）+ provider receipt |
| MO06-s-1 / s-2、MO07-s-2 | 各 `post-media-gate.json`：PASS / FAIL / FAIL；`ledger.json` 各 1 次 submitted | analyzer + provider receipt |
| MO07-s-1 | `ledger.json` `submitting`（非终态）；`spend.json` 余额不变、错误为 reference upload 未完成 | provider receipt（不完整） |
| window 过期 | `operator-bound.expired-*.json` 与新 `operator-bound.json` 的 `issued_at` / `expires_at` | execution |
| 积分 | `review-jimeng-project-credits-2026-11-20.png`（总消耗 10,663、43 任务、余额 36,665）；每条金额取自 `decisions.md`；多降部分来源 UNKNOWN | provider receipt（只读，部分转述） |
| v4r10b `red` | `qa/v4r10b/QA.md`：6 帧超 12 px，最差 16 px，总 FAIL；`uRedCapPost 0.42` 全镜头 | analyzer |
| v4r10c 成片与 QA | SHA-256 `e1439c06…48db`（本次重算，与 `render-provenance-v4r10c.json` 一致）；`qa/v4r10c/qa.json` 全 `true`、`Overall: PASS`、`red` 0 帧超限 | execution + structure + analyzer |
| v4r10c 影调 / grad | `qa/v4r10c/grad.json` 17 帧中位数 0.1543 / 0.2040，分位 10 / 15 / 43 / 153，与 v4r10 在同口径下一致 | analyzer |
| 闪烁 | `qa/v4r10|v4r10c/qa.json` `flash` 3.0 次 / 秒（限 3）、cell 6、frame 497；v4r9 为 1.0 | analyzer（PASS 但无余量） |
| 使用者裁决 | 「s013 用 b、s014 用 c」「s014 和 s011 都重做」「两镜都用 b」「按 A 剪」「按推荐剪法」「很多还是都太清晰了」「可以，先这样」（针对 v4r10），见 `decisions.md`；对 v4r10c 无另行表态记录 | human |

## Evidence Index

三组彼此独立的实验（`tex-r10c-flash` 的 PASS 在表中无法表达“恰在上限、无余量”，该风险只见正文；交接更新在质感组追加 v4r10b、v4r10c 四行；v4r10b 与 v4r10c 是同一剪辑只调红色上限的两个版本，红色上限变量对应的 QA 结果同属一条修复链，不当作独立重复）：SG04 s013 口型（含同输入复用的第二条与第一轮已有的 SG02-r2）、斜挎带返工、观看尺度质感。质感组 v4r7–v4r10 是同一作品、同一参考、同一使用者的串行迭代，每轮变量不止一个，只作身份与结果登记，不构成对照结论。同一 take 的多层证据用 `SAME_EVIDENCE_NEW_PROOF_LAYER` 连回同一 `independence_key`。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sg04-r2-1-gate | native:e18949ce2639bdce058609c34bfb9b9926f98768420a52133237261f6d45ec29 | iris-ep01-v4-sg04-sung-lipsync-window | iris-sg04-r2-1-source-001 | r2-1-song-first-frame | e18949ce2639bdce058609c34bfb9b9926f98768420a52133237261f6d45ec29 | ANALYZER | FAIL | LIP_SYNC_PARTIAL_WINDOW | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG04-r2-1/post-media-gate.json |
| sg04-r2-2-gate | native:72fe8e1a1542d44d9924d34d963a9749280b10d143e8887ed3568cbc8db2a142 | iris-ep01-v4-sg04-sung-lipsync-window | iris-sg04-r2-2-source-001 | r2-2-song-first-frame | 72fe8e1a1542d44d9924d34d963a9749280b10d143e8887ed3568cbc8db2a142 | ANALYZER | FAIL | LIP_SYNC_PARTIAL_WINDOW | INPUT_REUSE_ONLY | sg04-r2-1-gate | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG04-r2-2/post-media-gate.json |
| sg02-r2-gate | native:0c7a34119f4ab9aa3870eb03a2e6442393352ba312d31320b07679699d6c5425 | iris-ep01-v4-sg02-sung-lipsync-window | iris-sg02-source-001/sd-SG02-r2 | r2-front-facing-reshoot | 0c7a34119f4ab9aa3870eb03a2e6442393352ba312d31320b07679699d6c5425 | ANALYZER | FAIL | LIP_SYNC_PARTIAL_WINDOW | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG02-r2/SG02/post-media-gate.json |
| mo06-s-1-gate | native:234b4a7ef49dd1fa74ac71399bcb0d946cf645c94e3441bcbe81a2ba84f9d40c | iris-ep01-v4-strap-direction-redo | iris-mo06-s-1-source-001 | s011-strap-fix-first-frame | 234b4a7ef49dd1fa74ac71399bcb0d946cf645c94e3441bcbe81a2ba84f9d40c | ANALYZER | PASS | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-MO06-s-1/post-media-gate.json |
| mo06-s-2-gate | native:bf49d05f9d48ba1b897bcb64fef1f85fa0cbd4b0845877211f5ccb31d45319a7 | iris-ep01-v4-strap-direction-redo | iris-mo06-s-2-source-001 | s011-strap-fix-first-frame-take2 | bf49d05f9d48ba1b897bcb64fef1f85fa0cbd4b0845877211f5ccb31d45319a7 | ANALYZER | FAIL | NEW_LOGO_APPEARS | INPUT_REUSE_ONLY | mo06-s-1-gate | outputs/ai-city-takeover/ep01/v4/pilot/sd-MO06-s-2/post-media-gate.json |
| mo07-s-1-submit | request:422a8ee640fcd99e07b71d6af72829f6e2b41a4ed1cbee2c380a945f3aacd94d | iris-ep01-v4-strap-direction-redo | iris-mo07-s-1-source-001 | s014-strap-fix-first-frame | NO_ARTIFACT:REFERENCE_UPLOAD_INCOMPLETE | PROVIDER_RECEIPT | NOT_EVALUATED | REFERENCE_UPLOAD_INCOMPLETE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-s-1/MO07/spend.json |
| mo07-s-2-gate | native:9a08bc46eebb59fc0d430cdd07044f4a754c4bc48afd9bc835179b5167ea256d | iris-ep01-v4-strap-direction-redo | iris-mo07-s-2-source-001 | s014-strap-fix-first-frame-take2 | 9a08bc46eebb59fc0d430cdd07044f4a754c4bc48afd9bc835179b5167ea256d | ANALYZER | FAIL | PAGER_PRESS_ABSENT_RED_ITEM | INPUT_REUSE_ONLY | mo07-s-1-submit | outputs/ai-city-takeover/ep01/v4/pilot/sd-MO07-s-2/post-media-gate.json |
| tex-r7-grad | native:75f65a6a55f83cf85a51f197b0a1428513230c3625c857134b2dca66ce5f8879 | iris-ep01-v4-excerpt-viewing-scale-texture | v4r7 | v4r7 | 75f65a6a55f83cf85a51f197b0a1428513230c3625c857134b2dca66ce5f8879 | ANALYZER_GRAD | FAIL | TOO_CRISP_AT_VIEWING_SCALE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/excerpt/qa/v4r8/grad.json |
| tex-r7-human | native:75f65a6a55f83cf85a51f197b0a1428513230c3625c857134b2dca66ce5f8879 | iris-ep01-v4-excerpt-viewing-scale-texture | v4r7 | v4r7 | 75f65a6a55f83cf85a51f197b0a1428513230c3625c857134b2dca66ce5f8879 | HUMAN | FAIL | TOO_CRISP_AT_VIEWING_SCALE | SAME_EVIDENCE_NEW_PROOF_LAYER | tex-r7-grad | outputs/ai-city-takeover/logs/decisions.md |
| tex-r8-grad | native:9d50e1e63a2c7c3cf3553b79f914ead1d92dffbb7eb856e565c19991c7cb09f6 | iris-ep01-v4-excerpt-viewing-scale-texture | v4r8 | v4r8 | 9d50e1e63a2c7c3cf3553b79f914ead1d92dffbb7eb856e565c19991c7cb09f6 | ANALYZER_GRAD | PASS | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/excerpt/qa/v4r8/grad.json |
| tex-r8-agent | native:9d50e1e63a2c7c3cf3553b79f914ead1d92dffbb7eb856e565c19991c7cb09f6 | iris-ep01-v4-excerpt-viewing-scale-texture | v4r8 | v4r8 | 9d50e1e63a2c7c3cf3553b79f914ead1d92dffbb7eb856e565c19991c7cb09f6 | AGENT_REVIEW | FAIL | OVER_BLUR_STORY_SUBJECT_LOST | SAME_EVIDENCE_NEW_PROOF_LAYER | tex-r8-grad | outputs/ai-city-takeover/logs/decisions.md |
| tex-r9-grad | native:b49f691f6ab57a0621aeeb90267e1a346cc699d70fec893caa6e71f71b665b7a | iris-ep01-v4-excerpt-viewing-scale-texture | v4r9 | v4r9 | b49f691f6ab57a0621aeeb90267e1a346cc699d70fec893caa6e71f71b665b7a | ANALYZER_GRAD | PASS | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/excerpt/qa/v4r9/grad.json |
| tex-r9-agent | native:b49f691f6ab57a0621aeeb90267e1a346cc699d70fec893caa6e71f71b665b7a | iris-ep01-v4-excerpt-viewing-scale-texture | v4r9 | v4r9 | b49f691f6ab57a0621aeeb90267e1a346cc699d70fec893caa6e71f71b665b7a | AGENT_REVIEW | FAIL | TONE_FLAT_VS_REFERENCE | SAME_EVIDENCE_NEW_PROOF_LAYER | tex-r9-grad | outputs/ai-city-takeover/logs/decisions.md |
| tex-r10-qa | native:9a173c74ecb53d2c2e1cfefa78ae446384d406bc6780fecf8675d61f45e97055 | iris-ep01-v4-excerpt-viewing-scale-texture | v4r10 | v4r10 | 9a173c74ecb53d2c2e1cfefa78ae446384d406bc6780fecf8675d61f45e97055 | ANALYZER_QA | FAIL | RED_OUTSIDE_EAR_LAMP | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/excerpt/qa/v4r10/qa.json |
| tex-r10-grad | native:9a173c74ecb53d2c2e1cfefa78ae446384d406bc6780fecf8675d61f45e97055 | iris-ep01-v4-excerpt-viewing-scale-texture | v4r10 | v4r10 | 9a173c74ecb53d2c2e1cfefa78ae446384d406bc6780fecf8675d61f45e97055 | ANALYZER_GRAD | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | tex-r10-qa | outputs/ai-city-takeover/ep01/v4/excerpt/review/v4r10/index.html |
| tex-r10b-qa | native:d5a879d257d37b5e186f37288b3e8c0ed4001776e1b113ba928485a3bfd7c25d | iris-ep01-v4-excerpt-viewing-scale-texture | v4r10b | v4r10b-red-cap-042-global | d5a879d257d37b5e186f37288b3e8c0ed4001776e1b113ba928485a3bfd7c25d | ANALYZER_QA | FAIL | RED_OUTSIDE_EAR_LAMP | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/excerpt/qa/v4r10b/QA.md |
| tex-r10c-qa | native:e1439c068b1386d2d53e9f07f0c591d6f5b85acd42307f4019d5647448b2e8db | iris-ep01-v4-excerpt-viewing-scale-texture | v4r10c | v4r10c-red-cap-030-s013a | e1439c068b1386d2d53e9f07f0c591d6f5b85acd42307f4019d5647448b2e8db | ANALYZER_QA | PASS | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/excerpt/qa/v4r10c/QA.md |
| tex-r10c-grad | native:e1439c068b1386d2d53e9f07f0c591d6f5b85acd42307f4019d5647448b2e8db | iris-ep01-v4-excerpt-viewing-scale-texture | v4r10c | v4r10c-red-cap-030-s013a | e1439c068b1386d2d53e9f07f0c591d6f5b85acd42307f4019d5647448b2e8db | ANALYZER_GRAD | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | tex-r10c-qa | outputs/ai-city-takeover/ep01/v4/excerpt/qa/v4r10c/grad.json |
| tex-r10c-flash | native:e1439c068b1386d2d53e9f07f0c591d6f5b85acd42307f4019d5647448b2e8db | iris-ep01-v4-excerpt-viewing-scale-texture | v4r10c | v4r10c-red-cap-030-s013a | e1439c068b1386d2d53e9f07f0c591d6f5b85acd42307f4019d5647448b2e8db | ANALYZER_FLASH | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | tex-r10c-qa | outputs/ai-city-takeover/ep01/v4/excerpt/qa/v4r10c/qa.json |
| tex-r10-human | native:9a173c74ecb53d2c2e1cfefa78ae446384d406bc6780fecf8675d61f45e97055 | iris-ep01-v4-excerpt-viewing-scale-texture | v4r10 | v4r10 | 9a173c74ecb53d2c2e1cfefa78ae446384d406bc6780fecf8675d61f45e97055 | HUMAN | ACCEPTED_FOR_NOW | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | tex-r10-qa | outputs/ai-city-takeover/logs/decisions.md |

## Assessment

- **s013 口型与剪法。** r2-1 与 r2-2 都在「I'm the call」这半句失步，同输入，不是两个独立证据；剪法 A 用手机插镜盖住失步半句，后半句取同步段，是使用者当次的决定。SG02-r2（第一轮之前的 2026-11-17 采样，gate 文件已重读）的失步在后半句，同步在前 1.53 s；SG04-r2-1 则是前半句失步、后半句同步。**方向并不一致**，不能概括成“只有后半句同步”。同样，SG02 第一版、SG03-w1、SG03C-d1 的口型 envelope 或 sync_check 全程或大部分稳定，所以“局部同步”是这些镜头里的一部分现象，不是唱段的常态。
- **斜挎带。** 修正首帧用原首帧编辑只改带子，MO06-s-1 PASS，说明这一次编辑首帧的路线有效；MO06-s-2 与 MO07-s-2 FAIL 的原因（新 logo、没按寻呼机且出红灯）与带子无关，且 MO07-s-1 没有取得结果。一个 PASS 加一个未完成，不足以说“编辑首帧只改一个属性”成了稳定做法。
- **质感。** 使用者“太清晰”这一感受有可测的量化对应（观看尺度 grad 约多 60%），1080 级锐度指标看不出来；但如上所述，成因无法拆分，且 v4r10 的 `red` 技术检查仍 FAIL。“可以，先这样”是暂时认可，不是质感达标的最终确认。
- **积分。** 本批次实付按 `decisions.md`：SG04-r2-1 与 r2-2 各 400、MO06-s-1 与 s-2 各 400、MO07-s-2 400，加 SG03C-d1 的 320，均有 ledger 的 submitted 与余额降幅对应；MO07-s-1 不计（余额不变）。额外的、非本项目的下降 UNKNOWN，不要把本轮总花费说成已结算。

- **红色检查（交接更新）。** 红色超标有两层设置：全局 0.42 把 49 帧降到 6 帧，仍然 FAIL；s013a 再收紧到 0.30 才到 0。「红只在左耳耳挂（与 P0 标签）」是封存要求，QA 按此判，所以 v4r10b 的 6 帧不能算“差不多”。但 0.30 是否伤了插镜里手机与指尖的观感，只有「368 帧肤色略少粉、不发灰」这条主会话自审，没有使用者对 v4r10c 的观感表态。
- **闪烁。** 恰在限值 3.0 的 PASS 只说明没有越线；v4r10 之后才出现，意味着这是一次改动引入的余量损失，而不是 QA 规则变严。在重新压低之前，任何再改影调或剪点的版本都可能越线，需要在本机重跑 `qa.py` 才知道。

## Remaining Risks Or Next Work

下列是交接更新后的清单（取代第一版清单；第一版里「v4r10 `red` FAIL 未解释」「`decisions.md` 写 QA 全 PASS 需回写」两项已完成：成因见 Current Runtime Truth，更正已写入 `decisions.md`）。

- **闪烁无余量（最先处理）。** 见下「Next Session Handoff」第 1 项。
- **MO07-s-1 的 `ledger.json` 仍停在 `submitting`。** 已知：错误原文「reference upload did not complete; generation was not submitted」，`spend.json` 余额前后均 37,065，即梦项目生成历史同时段只有 3 个任务（来自 `decisions.md` 更正条，我没有重读账户）。不重试、不重提交、不 remint；等按 canonical recovery 封存终态。
- **积分。** 当前余额 36,665（截图读数，与 37,065 − 400 一致）。每批首条提交窗口里额外下降约 2,732、4,480、2,420，加上更早两次 9,136 与 765，共五次来源不明；只读核对即梦 IRIS 项目生成历史，本项目每条都按 320 / 400 正常计费。来源 UNKNOWN，已请使用者核对账号积分明细。不要判成 Provider 超收或本项目误提交。
- **s015 仍是旧造型。** 底片 `p015` 与分镜提示词还是旧的（白立领加红线），需按 W1 重做；之后仍要预览认可、场记、lint、提交、逐镜 Gate。
- **样片开头 25.13–36.2 秒逻辑未设计**，主歌静图 s007–s010 未接入，目前样片只有 36.22–59.234 一段。
- **`windows.json` 里 SG03 / SG03C 的 `plays` 字段**仍是旧值（取自主会话清单，我没有逐项读取内容；文件在 `pilot/audio/windows.json`，刷新脚本 `gen/cut_audio.py`）。
- **`board/shots.json` 里 s013、s014 的 look / chrome 旧字段**，以及 `board/board.md`、`board/index.html` 需要重新生成（取自主会话清单，我没有逐字段核对）。第一版记录提到的 s012b 切点 48.17 对 49.087 仍未核对。
- **未提交。** 当前 HEAD `964cf680`；本任务所有改动都在工作区。按约定：使用者认可成片、完成 Harness 验证与 code review 之后再 commit / push；只提交本任务拥有的路径，不提交 `refs/ev-frames-final.webp`，不碰 `964cf680` 与 `.codex/config.toml` 的改动。`.gitignore` 排除 `*.png` 与 `*.mp4`，这些媒体的跨机器身份只剩 SHA 与 JSON。
- **使用者未独立确认 v4r10c。** 见 Current Runtime Truth「后续」。

## Next Session Handoff

按顺序做；每项只是方向，改动前仍按 `AGENTS.md` 读取各 owner。

1. **压低 v4r10c 在歌 57.4 s 附近的闪烁**，回到有余量的水平（目标：`qa.json` 的 `flash.max_flashes_per_second_any_cell` 明显低于 3，v4r9 是 1.0），同时不破坏使用者认可的观感。
   - 路径：`outputs/ai-city-takeover/ep01/v4/excerpt/qa.py`（`check_flash`）、`excerpt/qa/v4r10c/qa.json`（cell 6、frame 497）、`excerpt/qa/v4r9/QA.md`（1.0 的参照）、`excerpt/src/main.js`（版本开关与 `GRADE_V4R10`、`uRedCapPost`）、`excerpt/build.py`（`--v4rN` 开关与 `VER`/`TAG` 表）、`excerpt/data/edl-v4r10c.json`。
   - 变量提示：v4r9 → v4r10 只改了影调曲线，闪烁 1.0 → 3.0；frame 497 的 1 秒窗口覆盖 s014b 跳切（frame 508）。这些是线索，不是已证因果；做法应是可归因的最小改动，改完重跑 `qa.py`（含 `red`、`flash`、`grad`），并在宽 640 并排看影调分位与 grad 是否仍与 v4r10 / EV 一致。新版本要新增开关与新文件名，不覆盖 v4r10 / v4r10c 的 mp4 与 QA。
2. **开头 25.13–36.2 秒：先与 Codex 商定开头逻辑，再把主歌静图 s007–s010 接上，形成 25.13–59.23 的完整样片。**
   - 参考 Codex 之前的建议：`outputs/ai-city-takeover/ep01/reviews/2026-11-18-codex-excerpt-author-method-r2.md` 第 4 点（「开头：同意用 s006 最后一拍进场……保全 25.991 秒 `Six` 起音」）与 r1 同目录文件对 26.05 s 入口的分析（`Six` 25.991 s 起音，样片 26.0528 s 起，晚约 62 ms）；同目录另有 `2026-11-19-codex-excerpt-gaps-r3.md`（我没有核对它是否涉及开头）。
   - 相关：`outputs/ai-city-takeover/ep01/v4/board/shots.json`（s006–s010）、`excerpt/data/edl-v4r10c.json`（当前样片从歌 36.22 起）、`excerpt/audio/` 母带切片（开头段需另切，`excerpt/mux.py`）。
3. **s015：把底片 `p015` 与分镜提示词改成 W1 新造型重做**（现仍是旧造型：白立领加红线），再走预览认可（封存 `preview_approval`）、场记、lint、提交、逐镜 Gate。
   - 路径：`outputs/ai-city-takeover/ep01/v4/board/shots.json`（s015）、`board/plates/`、`gen/lint.py`、`gen/prep_unit.sh`、`gen/run_unit.sh`、`gen/excerpt_approvals.py`、`gen/operator.py`。
4. **小项：**
   - 用 `gen/cut_audio.py` 刷新 `pilot/audio/windows.json` 里 SG03 / SG03C 的 `plays`。
   - MO07-s-1 recovery：`pilot/sd-MO07-s-1/ledger.json`、`submit-intent.json`、`MO07/spend.json`；按 canonical recovery 封存终态，不重试。
   - `board/shots.json` 里 s013、s014 的 look / chrome 旧字段；重新生成 `board/board.md` 与 `board/index.html`（`board/build_sheet.py`）。
5. **commit / push：** 使用者认可成片、完成 Harness 验证与 code review 之后再做。当前什么都没提交。只提交本任务路径；不提交 `refs/ev-frames-final.webp`；不碰用户的 `964cf680` 与 `.codex/config.toml` 的改动。

### 环境信息

- **审片服务器：** `python3 -I motion-kit/tools/serve.py --dir outputs/ai-city-takeover/ep01/v4 --port 8769`。新会话里它可能已不在运行，需要重启；审 v4r10c 看 `/excerpt/review/v4r10/`。
- **即梦 Chrome：** profile 在 `~/.local/share/ai-video/playwright-mcp/profile`，带 CDP 端口；不要把凭据写进任何记录。
- **出片流水线：** `outputs/ai-city-takeover/ep01/v4/gen/prep_unit.sh`、`run_unit.sh`。operator window 只有 6 小时，机器休眠会导致过期（本记录「operator window 过期」一节）；过期后同 attempt id、同上限重封新窗口，不复用旧 permit。
- **剪辑代码：** `outputs/ai-city-takeover/ep01/v4/excerpt/`（`build.py`、`edl.py`、`qa.py`、`src/main.js`），各版本都有 `--v4rN` 开关（`--v4r10b`、`--v4r10c` 已存在）。
- **主会话记忆（用户侧，不在仓库）：** 新增 `viewing-scale-sharpness`、`quality-over-cost`，位于 `~/.claude/projects/-home-reggie-vscode-folder-AI-VIDEO/memory/`。

## Learning 评估

**结论：`no_candidate`（2026-11-20 第一版评估；交接更新后复评，结论不变。两条候选均未达 `distill-ai-video-learning` 门槛，不建 pending 文件，也不请求确认。）** 本记录的 Evidence Index 已用 `validate_evidence_identity.py` 只读校验（本记录与 2026-11-19 记录均 `PASS`，`admitted: false`，即只是身份合格、未被任何候选采纳）。

1. **「观看尺度结构细节（宽 240/160 的 grad）比 1080 锐度更能代表使用者感知的“太清晰”；配合影调分位对齐，并用 640 并排目检防止过度虚化」**：`SINGLE_CASE`，不够。
   - v4r3→v4r10 是同一作品、同一参考（EV）、同一使用者的单链串行迭代；Evidence Index 里 v4r7–v4r10 的多行同属一条 artifact 链，不能当作多个独立 attempt。人工只有两次表态：v4r7 否定、v4r10 暂时认可；v4r8、v4r9 是主会话自审淘汰，不算人工证据。
   - 不是受控多臂：每轮同时改了虚化、光晕、结构柔化、雾与影调。成因不能归给 grad 或分位。
   - 使用者对 v4r6 曾说「成立」而 v4r6 未测 grad，与 v4r7 “太清晰”之间无法区分“新增镜头”与“全段偏清晰”。
   - v4r10 的 `red` 技术检查 FAIL，说明被认可的这一版并非全项 QA 通过。
   - 产品不变量：单个作品通过不证明通用能力。升级条件：另一作品或另一参考，出现“1080 锐度对齐被否、观看尺度 grad + 影调对齐被认可”；或同一剪辑上对 lap 对齐版、grad 对齐版、grad + 影调版做三臂并排给使用者看，并保留各自 SHA 与使用者原话。
2. **「唱段的口型常常只有后半句同步，作者式的插镜覆盖前半句比重拍更稳」**：按原表述，不够；按收窄表述，形式上接近但不建议升级。
   - 原表述的事实不成立：SG02-r2 是前半同步、后半失步；SG04-r2-1 是前半失步、后半同步。SG02 第一版、SG03-w1、SG03C-d1 的口型大部分稳定，是反例而不是边缘情况，“常常”缺证据。
   - “插镜比重拍更稳”没有对照臂：没有一次重拍成功恢复口型，也没有一次“插镜失败”的反例；SG04-r2-1/r2-2 同输入，算一个单位。SG02 的插镜覆盖没有单独的使用者审看记录；s013 的覆盖仅被 v4r10 整体暂时认可，且 v4r10 技术 QA 有一项 FAIL。
   - 若收窄为“take 内口型同步可能是局部窗口，先用 sync/envelope 量出窗口，再决定插镜或重拍”，则 SG02-r2 与 SG04-r2-1 在形式上有两个不同 `independence_key`、不同镜头与参考，可算两个独立 attempt。但这只复述了现有 Gate 已在做的 `usable_song_s` 语义，没有给任何 owner 一个可验证的新增动作；候选落盘还需要路径受限的 candidate checkpoint commit，超出本子代理的边界。升级条件：补一个以插镜覆盖失败（或重拍成功恢复口型）的反例，或在另一作品出现同形态证据后，再由主会话决定是否建 pending。

交接更新后的复评：新增的材料是 v4r10b / v4r10c 的红色上限修复与闪烁风险，以及「只 grep `pass:true` 就误报 QA 全 PASS」这一次主会话失误。前者是同一作品、同一剪辑上的单链修复（0.42 全局 → 0.30 仅 s013a），没有对照臂，也没有第二个作品；后者是一次具体失误，已更正，仍属单例。二者都不构成跨实验的有界 claim，结论保持 `no_candidate`，不建 pending 文件。可观察的升级条件：同类「某项检查被报告成全 PASS 而 `qa.json` 顶层 `pass` 为 false」在另外的独立会话或作品再现，再评估是否需要让 QA 汇总由脚本直接输出顶层 verdict（那属于目标 owner 的改动，须用户 exact confirmation）。

本评估不创建、不采纳任何 Learning Claim，不得据此改 Skill、Policy、Gate。

## Agent Guardrails

- “v4r10 可以，先这样”不等于整片、P6、Final Acceptance 或 `preview_approval`，也不证明 v4r10 技术 QA 通过（v4r10 的 `red` 是 FAIL；通过 QA 的是 v4r10c，而使用者没有对 v4r10c 另行表态）。
- 报 QA 结果以 `qa.json` 顶层 `pass` 与 `QA.md` 的 `Overall:` 为准，不要只 grep 各项 `pass:true`。
- 闪烁 3.0 次 / 秒是合规但无余量，不要写成「闪烁已没问题」；任何再改影调 / 剪点的版本都要重跑 `qa.py`。
- 不要提交 `refs/ev-frames-final.webp`，不碰 `964cf680` 与 `.codex/config.toml`；commit 前须先经使用者认可、Harness 验证与 code review。
- Gate PASS / QA PASS 只证明被测项；好不好看、清不清晰只由使用者判。
- 主会话自审（v4r8、v4r9 淘汰）是 Agent 判断，不是使用者裁决；不要把“主会话看过 640 并排”写成“使用者认可”。
- MO07-s-1 的 `submitting` 是非终态 ledger；unknown 时不重试、不重提交、不 remint。
- 积分多降来源 UNKNOWN 时，不要把本项目总花费说成已结算，也不要归因给 Provider 或误提交。
- 本记录不创建也不采纳任何 Learning Claim；评估结论见上。
