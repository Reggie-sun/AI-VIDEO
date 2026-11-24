---
record_kind: media_experiment
topic_id: iris-ep01-v4-excerpt-round1-checkpoint
learning_eligibility: eligible
evidence_index_version: "1"
---

# IRIS EP01 v4 样片第一轮（歌 39.674–50.93）通过：质感、界面与闭眼唱脸记录

Date: 2026-11-19（本机日期；时间与数字取自 `outputs/ai-city-takeover/logs/decisions.md` 2026-11-19 各条与各 `pilot/` 证据）

## Supersession Notice — 2026-11-20（部分取代，本记录仍可检索）

后续证据见 [2026-11-20 第二轮与观看尺度质感记录](2026-11-20-iris-ep01-v4-excerpt-round2-texture-checkpoint.md)。下列当前面向的说法已被取代，原时序与测量作为历史保留：

- **「尚未完成：第二轮 s013、s014」**：已做完并并入 v4r7–v4r10；使用者 2026-11-20 对 v4r10（歌 39.674–59.234）说「可以，先这样」后暂停。样片开头 25.13–36.2 秒仍未做。
- **质感“已对齐作者”**：本记录只在 `lap`/`sat`/`warm` 三项数值上成立，现已进一步取代：使用者看含第二轮的 v4r7 仍说「很多还是都太清晰了」，主会话改用观看尺度（灰度 BOX 缩到宽 240/160 的 `mean|∇|/std`）测得 v4r7 比 EV 多约 60%，经 v4r8–v4r10 对齐。1080 级锐度指标不能代表观看尺度的清晰度。
- **积分「第三次来源不明下降 3,052」**：其中 320 是本项目 SG03C-d1 的正常扣费，额外部分为 2,732；2026-11-20 对即梦画布只读核对后，本项目 43 个任务总消耗 10,663，额外下降不在本项目任务账内，来源仍 UNKNOWN。
- **「s011（MO06-w1b）已入片」**：该镜斜挎带方向与 W1 定稿相反，已用 MO06-s-1 重做，v4r7 起替换。v4r6 里的 MO06-w1b 保留为历史。
- 本记录的 Learning 评估 `no_candidate` 不变。

## Supersession Notice — 2026-11-23（部分取代，本记录仍可检索）

后续证据见 [2026-11-23 s015–s030 拍摄与剪辑检查点](2026-11-23-iris-ep01-s015-030-shoot-and-assembly-checkpoint.md)。上一条提示里「样片开头 25.13–36.2 秒仍未做」已被取代：2026-11-20 起开头 s001–s010 改用 Seedance 视频生成并选定，开头 0–59.23 s 暂定为 `IRIS-EP01-agentcut-ev-v3-000-059.mp4`（SHA-256 `38dcb0e81e097c2cd2eceb6951929f8c9bf133c031571d1f2c71ddb7afb7a226`，使用者「开头还可以」，暂定而非最终）；首轮副歌之后 s015–s030 已拍完并成片，使用者 2026-11-23 认可 review-v1（「认可，彩点算次要 (Recommended)」）。本记录的 v4r6 范围、人工裁决与测量仍作历史证据有效；v4r6 / v4r10 不再是当前样片。

## Purpose

记下样片第一轮从“使用者说还是少”到“成立，继续第二轮”的真实状态，并分清：使用者裁决、Gate 与 QA 证据、一次来源不明的积分下降、尚未做完的事。这是新记录，不是 [2026-11-17 检查点 1–4 记录](2026-11-17-iris-ep01-v4-restart-author-method-storyboard-checkpoint.md)的追加：该记录范围止于分镜通过，本记录是样片方法试验与第一轮成片，主题独立。

本记录由 `memory-keeper` 子代理依主会话清单对照磁盘文件写成。没有调用 Provider，没有生成媒体，没有读取 `.env`，没有 commit。只重新量了 v4r5、v4r6 两个 mp4 的 SHA-256，并读取了 `texture.json`、各 `post-media-gate.json`、`preview-approval.json`、`ledger.json`、`qa/v4r6/QA.md`；没有重跑 QA、lint 或测试。积分数取自 `decisions.md` 转述，未重读即梦账户。

路径自 `outputs/ai-city-takeover/ep01/v4/`（下称 `v4/`）起，除非标明 repo 路径。

## Current Runtime Truth

- **使用者裁决。** 第一轮 v4r6 审 39.7–50.9：「成立，继续第二轮 (Recommended)」（2026-11-19）。这是使用者对该 11 秒段的认可，不是整片、P6 或 Final Acceptance；也不是 `preview_approval` 之外的任何新授权。
- **第一轮成片。** `excerpt/renders/IRIS-EP01-v4-excerpt-v4r6-036-051.mp4`，SHA-256 `89c5da30450c6683b263d4172a99dc7d9081208c5e889b747e3b58a828c1a13f`（本次重算一致）；1920×1080、24 fps、353 帧、h264、AAC，歌 36.22–50.93，与母带切片对齐 0 样本；`excerpt/qa/v4r6/QA.md` 总评 PASS（含切点落拍、歌词 23/23、无闪烁、无中文）。v4r5 为 `…-v4r5-036-051.mp4`，SHA-256 `4aec301ba514e3f45b9e4cdd2fe275c2f43029743a24910781af7dddfacb352e`（本次重算）。QA PASS 是技术层，观感由使用者判。
- **v4r6 剪法。** SG03-w1 唱到 49.087 → 闭眼唱脸 d1 的 2.167–3.500 s → 50.469 工程师 AWAKE。即第一轮最终入片的两条视频是 SG03-w1 与 SG03C-d1，加 MO06-w1b 与若干静图；SG03C-c 与 SG03C-d2 不入片。
- **尚未完成。** 第二轮 s013（唱 I'm the call you had to take）、s014（旋身收尾）；样片开头 25.13 s 起那一段；`board/shots.json` 中 s012b 的切点仍写 48.17（`camera` 与 `notes` 字段），而 v4r6 实际切点是 49.087（`QA.md` 的 s012c 行），需回写分镜。
- **未提交。** 记录时 HEAD 为 `964cf680`；`v4/`、`motion-kit/tools/{board_audit,lyric_score,test_board_audit,test_lyric_score}.py`、三份 `ep01/reviews/2026-11-18/19-codex-*.md`、本记录与 11-17 记录都在工作区，未 staged、未 commit、未 push。`.gitignore` 排除 `*.png` 与 `*.mp4`（见 v3 记录），这些媒体的跨机器身份只剩 SHA 与 JSON。

## Session Work And Decisions

### 起点与第一轮前半（时间序）

按 `decisions.md`：使用者认可 v4 方案后选定 s011、s012 首帧（11-18）。11-19 第一轮提交两条：MO06-w1b 实付 400（50,422→50,022，Gate PASS，落步入点需后移，笔记本苹果标需后期遮去）与 SG03-w1 实付 480（50,902→50,422，Gate FAIL：片头镜头上摇、工程师笔记本先开后合、三段静音嘴提前张开；身份、造型、耳挂、技术 PASS；可用片内约 2.0–5.4 s）。使用者对 SG03-w1 当次改判：「按建议剪，继续拍 s011 (Recommended)」——只用 2.0–5.4 s，不重拍。MO06 第一次封存时场记拦下 p011-w1 露右肩（与全部 W1 静图相反，且不可镜像，因为耳挂会换边），使用者改用 V11a-2（露左肩）。

### 质感与界面：v4r1 → v4r6

- 使用者看 v4r1：「我觉得还是少的意思，不知道怎么形容」，对比页 `excerpt/review/compare2/` 多选：常驻界面层太少、图形没有概念、画面没有记忆点、颜色太灰太平。Codex 第三轮（`ep01/reviews/2026-11-19-codex-excerpt-gaps-r3.md`）与主会话对齐了改法，先做三张设计样幀（`excerpt/design/`）。
- 使用者看第一版设计样幀：「这个显得很low，并且和整体的颜色风格不符合」（奶白实心卡加橙边条）→ 改按 EV 界面语言（细线框、半透明、等宽小字、与画面同层受调色与颗粒、强调色极少）；v2 样幀使用者：「对了，按这个改片子」。
- 使用者看 v4r2：「作者这里都是加的很模糊的，你怎么这么清晰」。主会话 1080p 原尺寸对比 `excerpt/review/compare3/`：EV 底图本身柔、像低分辨率放大，叠重的斜向网线与暖色；我方 4K 缩下偏锐、网点颗粒很轻。使用者随后：「没有我只是让你自己判断」——要主会话自己对照作者、自己修，不再请使用者诊断（`judge-myself-with-evidence` 记忆条）。
- **v4r3 → v4r4 质感对齐。** 网线之前先柔化底图，加暖、提饱和，冷屏单独保护，红色只留耳挂灯。`excerpt/qa/v4r4/texture.json` 的 `gate` 段实际结果：`lap`（锐度代理）ours/EV 0.945、`sat` 0.906、`warm` 1.097，三项都在 ±20% 内；**`crisp` 0.702 与 `screen_prominence` 0.722 不在 ±20% 内**（`within_20pct: false`）。`decisions.md` 另记「同位置裁切仍偏淡」。所以“质感已对齐作者”只成立于 lap/sat/warm 三项数值，不是全部指标，更不是使用者判过的观感。
- **v4r5 界面。** 底部事件流（文字全取自 `shots.json` 并核对出处）、左缘刻度尺、加亮小字、等宽歌词、关键词大字。9/20 倒计时没做，因为分镜里没有日期依据。

### 闭眼唱脸 SG03C：c 失败、d 通过

目标：s012 后半句 reason you're awake 切进闭眼唱的近脸（记忆点画面）。四轮首帧：D1-b（场记拦下，露右肩、斜挎带反）→ D2-b（缺黑色高领）→ D3-b（使用者 closeup2.html 看过，「可以，拍 (Recommended)」）→ D4-a。

- **SG03C-c**（首帧 D3-b = `board/plates/p012c-w1c.png`，Codex 整张重画；`bound_ids` attempt `iris-sg03c-c-source-001`）：实付 320（49,257→48,937），take SHA-256 `329d3a0690ae4563cccc853c5c910a5fa7a60072a2e6cefcea475fe6e7a4be6f`。逐镜 Gate（`shot-gate-reviewer`，`pilot/sd-SG03C-c/post-media-gate.json`）**FAIL**：机位环绕（前景笔记本约 -900 px、背景约 +570 px）、前景工程师缺失、开头抢拍、尾段空口型、与 SG03-w1 切接不成立；造型身份 PASS。主会话自查：切过去像换了地方。**根因判断（Agent 推断，非单变量实验结论）：** 首帧背景来自另一个场地，且 reference_to_video 不锁首帧。
- **使用者两次裁决。** 先「B：不用，前一镜唱完 (Recommended)」（c 不入片，s012 由 SG03-w1 唱完，50.32–50.93 需遮挡）；随后「钱都无所谓质量为上」→ 重做闭眼唱脸。
- **D4 首帧。** 以 SG03-w1 实拍 4K 帧（`excerpt/flash/design/D4/D4-base.png`，取 t≈4.6 s）推近为编辑底图，Codex 编辑出 a/b/c；预览页 `excerpt/flash/closeup3.html`（SHA-256 `d0f1c4b6…f9d6`）。使用者：「D4-a，拍 (Recommended)」。D4-a 与 `board/plates/p012c-w1d.png` 逐字节相同（SHA-256 `21c5f96a6cdbdf4f39d99b9137e4092776d4f3b4d77adba4178532c473682c48`）。她改成闭眼、下巴抬起、嘴先闭着（为避开 c 的开头抢拍）。
- **d1 / d2**：同一首帧各提交一次（各 4 s、4k、multimodal、单条上限 400，一份 approval 覆盖两条，总上限 800）。`prompt` 与 c 不同：加了左前景工程师一直在画面、镜头固定不动、不推不拉不摇不环绕、机头直闪（逐字见各 `preview-approval.json`，本记录不转抄）。
  - **d1** take SHA-256 `2de73f901d83839f23b9e3004e8271c1597fbacc91ce85fee5842ba51f76fb09`：Gate **PASS**（`pilot/sd-SG03C-d1/post-media-gate.json`）：口型 envelope lag +0.018 s 稳定（最大偏差 0.005）、镜头位移 ≤10 px、工程师在前景、造型对、与 SG03-w1 同场同轴（约 1.5 倍推近）；底边小金戒指已在 4K 看过，非红非字。可用 clip 2.168–3.538 s = 歌 49.08–50.45。注意 `fetch` 的 sync_check 为 ncc 0.15、copy=false，而 Gate 以 envelope 判口型；两者不是同一层证据。
  - **d2** take SHA-256 `c6f6531b535ad4693f28033a5d100696b1e8b2bec266b3c0e4b8079ec80ab1a2`：口型记 **NOT_EVALUATED**（awake 段原生音轨被听成 “ready”，4 fps 无法区分）；机位、工程师、造型、切接 PASS。未再补证据。
  - 选 d1，交 v4r6。

### 流程改动

- `gen/prep_unit.sh` 改为使用 approval 封存的 `bound_ids`（有则用，否则回落到 `iris-<unit>-source-001` 默认名）。`decisions.md` 同日记有 attempt id 与旧封存重名而需改名的事，二者可能相关，但这里没有逐项证实因果。
- `gen/lint.py` 新增 `bound_ids_match_approval`（核对运行时 bound 与 approval 封存一致）与 `fresh_canvas_node`（要求新建节点 `node-created.json`）两项检查。本次只读到这两处代码存在；没有重跑 `gen/test_unit_lanes.py`。

## Verification And Evidence

| 项 | 证据 | 层 |
| --- | --- | --- |
| v4r6 成片 | SHA-256 `89c5da30…1a13f`，`qa/v4r6/QA.md` PASS | execution + structure（QA 脚本） |
| 质感数值 | `qa/v4r4/texture.json` gate：lap/sat/warm 在 ±20%，crisp/screen_prominence 不在 | analyzer |
| SG03C-c | `pilot/sd-SG03C-c/post-media-gate.json` FAIL | analyzer（逐镜 Gate） |
| SG03C-d1 | `…-d1/post-media-gate.json` PASS | analyzer（逐镜 Gate） |
| SG03C-d2 | `…-d2/post-media-gate.json` NOT_EVALUATED | analyzer |
| 提交次数 | 三条 `ledger.json` 各 1 次 submitted（c、d1、d2）；`sd-SG03C`、`sd-SG03C-b` 只有封存，无 ledger，未提交 | provider receipt |
| 使用者裁决 | D3-b「可以，拍」、B 剪法、「钱都无所谓质量为上」、「D4-a，拍」、「成立，继续第二轮」，见 `decisions.md` | human |

## Evidence Index

SG03C 闭眼唱脸同一 experiment 的三条 take。三条 take 变量不止一个（见 Assessment），这里只作身份与结果登记，不构成对照结论。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sg03c-c-gate | native:329d3a0690ae4563cccc853c5c910a5fa7a60072a2e6cefcea475fe6e7a4be6f | iris-ep01-v4-sg03c-closeup-first-frame | iris-sg03c-c-source-001 | c-redrawn-first-frame | 329d3a0690ae4563cccc853c5c910a5fa7a60072a2e6cefcea475fe6e7a4be6f | ANALYZER | FAIL | CAMERA_ORBIT_SUBJECT_LOSS | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03C-c/post-media-gate.json |
| sg03c-d1-gate | native:2de73f901d83839f23b9e3004e8271c1597fbacc91ce85fee5842ba51f76fb09 | iris-ep01-v4-sg03c-closeup-first-frame | iris-sg03c-d1-source-001 | d1-live-frame-punch-in | 2de73f901d83839f23b9e3004e8271c1597fbacc91ce85fee5842ba51f76fb09 | ANALYZER | PASS | NONE | NEW_ATTEMPT | NONE | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03C-d1/post-media-gate.json |
| sg03c-d2-gate | native:c6f6531b535ad4693f28033a5d100696b1e8b2bec266b3c0e4b8079ec80ab1a2 | iris-ep01-v4-sg03c-closeup-first-frame | iris-sg03c-d2-source-001 | d2-live-frame-punch-in | c6f6531b535ad4693f28033a5d100696b1e8b2bec266b3c0e4b8079ec80ab1a2 | ANALYZER | NOT_EVALUATED | LIP_SYNC_UNDETERMINED | INPUT_REUSE_ONLY | sg03c-d1-gate | outputs/ai-city-takeover/ep01/v4/pilot/sd-SG03C-d2/post-media-gate.json |

## Assessment

- **积分。** 本轮付费提交（`decisions.md` 实付）：SG03-w1 480、MO06-w1b 400、SG03C-c 320，SG03C-d1 与 SG03C-d2 各一次（d2 实降 320，d1 见下）。账户余额链（`decisions.md`）：50,902→50,422（SG03-w1）→50,022（MO06-w1b）→49,257（无本项目提交，少 765）→48,937（c，320）→45,885（d1 窗口，少 3,052）→45,565（d2，320）。**d1 窗口的 3,052 远超单条上限 400，同参数 d2 只降 320，提交回执只有一次，多出部分来源 UNKNOWN**，记为第三次来源不明下降（前两次：本轮开始前 60,038→50,902 中少 9,136；c 之前少 765，两次期间本项目均无提交）。已告知使用者，待其核对即梦账单。本记录不把它判为 Provider 超收，也不判为本项目误提交；账户可能还有同账号其他窗口的消耗，未证实。
- **c 与 d 的对比不是单变量实验。** 首帧来源（Codex 整张重画 vs 实拍帧推近编辑）、姿态（c 未固定，d 闭眼、嘴先闭）和 prompt（d 加了工程师在场与“不推不拉不摇不环绕”）三处同时变了；d1/d2 共用同一首帧，不是两个独立证据。因此“实拍帧推近编辑首帧是 c→d 通过的原因”只是一个假说，当前证据既不能证明也不能证伪它；d1 PASS 只证明这一条 take 在这一镜通过了逐镜 Gate，且口型一项只靠 envelope，不等于使用者听过口型。
- **使用者“成立”的范围。** 只覆盖 v4r6 的 39.7–50.9；入片的 d1 片段仅 1.37 s（2.168–3.538 s）。
- 本轮印证的是流程：Gate FAIL 后不重试、先给使用者看两版剪法预览再裁决；c 的 320 与 d 的 640 是在使用者明示“质量为上”之后的有界花费。

## Remaining Risks Or Next Work

- 第二轮 s013、s014 与样片开头 25.13 s 起尚未做；每个新 Shot MP4 仍须逐镜 Gate，付费前仍须 `preview_approval`。
- s012 在 `board/shots.json` 的切点仍写 48.17，实际是 49.087，需回写（只改本任务拥有的字段）。
- `qa/v4r4` 中 `crisp` 与 `screen_prominence` 仍低于 EV 的 80%；使用者没有就质感另作表态，只对 v4r6 整段说“成立”。
- 第三次积分下降 3,052 为 UNKNOWN，须使用者核对账单；在此之前不要把本轮总花费说成已结算。
- SG03-w1 尾段 50.32–50.93 需遮挡（不用空口型）；v4r6 已处理，但没有独立证据显示使用者逐帧审过该遮挡。
- **Learning 评估：`no_candidate`（2026-11-19）。** “用前一镜实拍帧推近编辑生成近脸首帧，更能保住同场地、同轴线与前景人物”目前只有 c→d 一组，且首帧、姿态、prompt 同变；d1/d2 同首帧不算两个独立证据，不满足 `distill-ai-video-learning` 的两个独立 attempt 或单变量多臂门槛，不建 pending candidate。若要升级，需要一次只换首帧来源（prompt 与姿态不变）的对照，或另一镜独立复现；先作为有界观察留在本记录。
- 当前全部未提交；`v4/` 体积大且 `.gitignore` 排除 `*.png`/`*.mp4`，提交须逐路径选择。

## Agent Guardrails

- “第一轮成立”不等于第二轮、整片、P6 或 Final Acceptance，也不是 `preview_approval`。
- Gate PASS 与 QA PASS 只证明被测项；好不好看、像不像只由使用者判。
- `NOT_EVALUATED`（d2）不是 PASS 也不是 FAIL；口型证据缺失时不要重试，也不要靠听写 “ready/awake” 之类的转写下结论。
- 积分下降来源 UNKNOWN 时，不重试、不重提交；先取证再继续付费。
- 本记录不创建也不采纳任何 Learning Claim；评估结论见上，不得据此改 Skill、Policy 或 Gate。
