---
record_kind: media_experiment
topic_id: fanxiang-v36-v37-production-loop
learning_eligibility: eligible
evidence_index_version: "1"
---

# Fanxiang Production Harness Loop Record

Date: 2026-10-05

## Current Status

### Supersession — Editorial Salvage Audit Before Any Further Generation

2026-10-06，用户要求先检查全部真实素材、实际 prompt/reference 顺序和 QA，再决定最小补镜。
本段取代下方“先重做 reaction / 原 4–9 均未有可用素材”的制作建议；保留历史失败和 receipts。
本轮没有 Provider submit、prompt 修改、Production activation、accepted continuity source 或成片输出。
核对开始时本地 `main` 和远端 `main` 都为 `67df22ec460b4a47d0f217f2f33c09dcb8327e5f`，working tree clean。

#### Evidence And Corrections

审阅十条 Production raw、两条 2026-10-02 H3 raw 与原 V36/V37，共十四条 MP4。
逐条核对 bytes/hash/ffprobe，并实际观察原生解码的联系表；十条 Production raw 均显式调用
project-local `video-analysis` MCP 抽帧。A2、B3、B4、Ba2、reaction 又经本地 Chrome 1×静音
播放至 ended，保存约 125ms 间隔的画面采样及 identity，关键窗口另取密集帧。
这是视觉剪辑诊断；本轮没有实际听音，不新增 sound PASS。历史 exact A2/B2 USER_AUDIO
观察保留，不能自动移植到重剪后的声画。未做跨镜头成片 normal-speed acceptance。

证据目录 `E = runs/fanxiang-editorial-audit-20261006-001/`（ignored，未发布）：
`inventory.json`、`input-audit.json`、`playback-summary.json`、五条 `*-1x.json`、
十四条联系表、`A2-tail.jpg`、`B3-block.jpg`、`B3-end.jpg`、`B4-impact.jpg`、
`Ba2-attack.jpg`、`references.jpg` 与 `audit-artifact-hashes.json`。原 MP4 未修改。

- A1 实际在约 4s/6s 有小龙反应切镜；旧“没有反应镜头/全程单镜”判断撤回。
  狗哥身后的室内床铺/空间问题仍存在，A1 不优先于 A2。
- A2 原片在 14.0–14.5s 可见烧录“龙哥”；旧 no-overlay PASS 不能证明全条无字幕。
  此次原生密集解码、MCP 与正常速度画面采样相互印证。旧 selection/QA 不改写，
  当前仅提出字幕前窗口；完整台词及末段仍需修复/重剪后复验。
- B4 原片左上持续可见“AI生成”；10.6–10.9s 有局部键盘/脸接触与遮挡，
  没有充分可读的重击偏转。不能把局部接触升级为完整动作 PASS，也不能直接当干净成片。
- reaction 约 2.9s 后狗哥已经出现在上亮窗，且存在额外切镜；失败末帧保持非 accepted。
  但此前约 0–1.5s 的潘子低眼/听声反应仍是可用画面候选，不整条丢弃。

#### Candidate Windows

以下是 source seconds 的保守剪辑候选，不是 raw acceptance；切点仍须在 exact timeline
逐帧对齐、接镜和实际听音后确认。`B = runs/fanxiang-production-loop-20261005-001/`。

| Source | Seconds | Editorial Use | Remaining Boundary |
| --- | --- | --- | --- |
| `B/sequence-A-take-02/output.mp4` | 0–4；4–6；6–13.75 | 最佳完整伸颈 reveal coverage：门窗 POV、小龙反应、连续伸颈贴窗 | 不含已发现字幕时段；删尾可能截台词，声音不能直接随之截断；不是自动 A2→B3 join |
| `B/sequence-B-reveal-take-01/output.mp4` | 0–1.5 | 潘子低眼、听声后开始抬眼的近景 | 保留“兄弟们”需实际听音与定时；不沿用约 3s 后提前显脸的末态 |
| `B/sequence-B-take-03-final/output.mp4` | 3.75–4.75 | 三人转向门上亮窗，此时没有狗哥露脸 | 4–4.75 更适合作为共同视线已落定的短镜；足以替代单独重抽 reaction 的部分义务 |
| `B/sequence-B-take-03-final/output.mp4` | 4.8–8.75 | 空窗→脸升起→一次破窗→头进入，连续可读 | 最佳 B 段 reveal/break 主干；不能接在 A2 已贴窗末态后又重复从空窗显脸 |
| `B/sequence-Ba-take-02/output.mp4` | 9.2–10.2 | 狗哥确实扑向黄衣潘子，潘子后撤 | 短 attack insert；接镜需对齐破口形态、轴线与人物位置，不使用末帧作为 accepted source |
| `B/sequence-B-take-03-final/output.mp4` | 10.75–11.25 | 从桌上取键盘的动机 insert | 双手握两端，未满足单端持握；不是合格反击开头，可留作备用 |
| `B/sequence-B-take-03-final/output.mp4` | 14.5–15.0 | 怪物离开后的破窗空镜 | 只能接在有真实可信命中/撤退因果的镜头后，不能用空镜倒推击打成功 |
| `B/sequence-B-take-04-motion/output.mp4` | 10.6–11.6 | 局部接触/退缩的研究或修复候选 | 持续烧录文字、弱受力反馈、握法与受袭目标问题；目前不列为直接干净可剪素材 |

B1 有重复的早段脸部，但室内多出怪物躯干、方向和空挥问题，没有比上表更好的主干。
B2 的破窗/靠近可作备用，后段空窗→重新出现造成重置；原声 USER_AUDIO PASS 仅属该 raw。
Ba1 的显脸/破窗可备用，但有字幕与错误视线；Ba3 约 10.5–11.3s 的键盘视线可研究为
局部 insert，前段玻璃重置、错误 reference eyeline 与冻结怪物不能一并继承。
两条早期 H3 raw 含显著镜头/空间/字幕问题，无优于 A2/B3 的完整事件链；原 V36/V37
可作为动作意图参考，但含烧录“AI生成”，不直接冒充干净 Production output。

#### Input Findings And Failure Classes

十条 `compiled-prompt.txt` 与对应 `resolved-request.json.prompt_text` 逐条字节相等；
本轮检查的 bindings 顺序和 B4/Ba3 native input-fidelity receipts 没有显示漏图或重排。
当前 adapter 保留 image/media 遍历顺序。全部是 `MiniMax-H3` / `reference_to_video`，
effective seed 为 null。输入 fidelity 与旧 QA 误判分别裁决，不能用前者证明媒体正确。

- **Code / chain**：当前没有足够证据把空挥或提前显脸归为 adapter 丢输入。
  确认的问题是旧 QA 对 A1 切镜、A2 字幕的判读错误；需要修正证据结论，不扩架构。
- **Reference preparation**：B3 的 Video1 近黑 2s 几乎没有动作指导；B4 Video1
  是含烧录文字的原动作片段。Ba3/reaction 的 Image8 来自 FAILED Ba1，黑衣小龙
  仍望向 camera，而非正确上亮窗；文字“排除错误 eyeline”没有把图修正。
  reaction 虽要求狗哥画外，Image1 仍提供完整长颈/脸；这是提前显脸的竞争 conditioning
  假设，未做受控实验，不能宣称唯一原因。
- **Prompt / performance**：人物视线、潘子后撤、小龙持键盘一端、挥击路径和受力反馈
  没有组成同一个可读事件。追加更长的多镜头/时间表不能替代正确起始姿态。
- **H3 boundary**：当前这组 Ref2VA 对多人视线、准确切镜时刻和接触受力的联合控制不稳定。
  B4 已有短暂接触，不支持“H3 一概不能生成碰撞”；无 seed 控制，也不宣称成功率或因果归因。
- **Editing**：可去掉多余铺垫/重置、截出好窗口、用已有转头与扑击。剪辑不能凭空补出
  清晰接触或正确握法；音效不能把空挥伪装成击中。字幕/水印处理须保留构图并另验。

#### Minimal Missing Shot And Next Test

当前 B 段最佳剪辑主干是 B3；伸颈 reveal 最佳单条仍是 A2，Pan attack 最佳短窗是 Ba2。
最小硬缺口是一个正确方向的短反击镜：键盘接触狗哥脸部→明确头部偏转/后缩。
共同望窗、脸升起和破窗已有窗口，不应继续为这几项重抽整段。

下一制作单元仅补这一击。优先只改变关键 conditioning：**正确的击打起始构图/reference**。
小龙已单端握键盘，对侧端留出朝狗哥脸部的挥击路径；潘子已经后撤，曾亮不挡路；
破窗与颈部位置保持同一轴线。固定机位，只要求一次挥击→接触→偏转/后缩，不同时试
新台词、运镜、人物身份或另一套动作。不得把失败 take 末帧登记为 accepted source；
若基于候选帧准备新图，明确记录其是 repaired reference，并先检查构图/握法/轴线。

现有 `metaso_h3.py` 的 `IMAGE_TO_VIDEO` / adaptive lane 支持 `first_frame`，
但不同时支持 Ref2VA 的 identity reference 列表。采用该 lane 属于新补镜的输入封存，
不能伪称在原 15s request 仅换一个字段的 controlled A/B；没有此场景的 I2V 实测证据。
本轮只提出建议，不生成 reference、不 author 新提交 prompt、不发 POST。

“上次最主要的失败是 B-03 的键盘挥击没有形成可见接触与受力反馈，这次只通过正确的击打起始构图/reference 去验证它；如果命中后的头部偏转仍失败，就停止继续堆 prompt，改用其他制作策略。”

失败后的策略：保留已有 reaction/reveal/break/attack，改为单独制作真实键盘/手部击打 insert，
结合匹配轴线的狗哥头颈局部合成与受力运动；再接经过核对的破窗空镜。先有可见接触和
受力，再做同步音效。不是靠剪辑或音效假造成功，也不默默切换 Provider。

#### Delegation And Learning Evaluation

本轮 managed Kimi deep read-only input audit invocation
`27075a18-1215-466f-8f86-a9573fd89153`，qualified route
`4f2d5dc8-4234-4665-b382-e82f1ad6cc00`；五个实际 read 的 frozen hash 已核对。
canonical receipt transport classification 为 PARSED，但 redacted worker report 无法解析为
完整 JSON；报告隔离，不接受其因果判断或 verdict，不据此做媒体 acceptance。
Parent 上述结论独立来自 exact 输入、当前源码和真实解码/播放；不把该 audit 冒称 required
implementation review。本轮没有代码 implementation，亦未扩展 router 修复 scope。

本次增量是同一话题的 editorial session summary；自动 learning evaluation：`no_candidate`。
同一批 dependent retakes 的再观察不是新独立实验，当前不新增通用 claim、不修改 Skill/Policy/Gate。
媒体 acceptance、A2→B join、成片实际听音和完整 final-output review 保持 NOT_EVALUATED。

### Supersession — Five-Second Reaction Unit Actually Generated And Failed

2026-10-06，用户继续后将真实制作单元缩为原事件 1–3，而不是把同一 11s request
重新分配 camera labels。本段取代下方“九次 submit / 更小单元尚未 author/submit”的当前状态。
累计十次物理 submit 均有 known fetched outcome；当前 reaction take raw QA FAIL，未 activation，
未产生 accepted handoff、下一破窗单元或完整 20–40s 成片。Product source、通用 continuity
schema/contract、spec/plan 均未修改，task-local helpers/media 仍在 ignored `runs/`，不是已发布通用 CLI。

- 本次单元为 5s / 两个实际目标机位：0–1.8s 潘子低眼，1.8–3s 同机位听一次“兄弟们”
  后眼睛停顿/抬下巴，3–4.8s 三人共同望向门上亮窗，最后 .2s 保持。原事件 4–6
  的“暗脸升起→同机位撞破/连续进入→袭向潘子”仍留在下一约 6s 单元，事件 7–9
  的“抓键盘→击中/痛吼→缩回”留在后续约 4s 单元；这些是未执行制作义务，不是结果。
  初始 7s / 原 1–4 候选在 POST 前废止，边界从 6.8s 移到 4.8s，避免把脸升起→破窗
  的原不切镜动作跨 Provider request 拆断。
- 沿用原七图和已登记的三人站位图，共八图；移除未来受袭姿态图。站位图来自 FAILED take，
  只继承轴线/位置、排除错误 eyeline，`accepted_source=false`。无视频或音频 reference，
  `previous_shot_state=None` 仅声明独立 replacement unit；A2→本段 join 未验证。
  H3 native master 5280 characters / SHA `08d121258d3ac1fae8e5529073a9048206f780371a27c3f41a39ebede6727f86`，
  60 项既有 typed control expression、prompt lint 100。六节英文/Chinese dialogue tag 对照
  [MiniMax-H3 primary guide](https://huggingface.co/MiniMaxAI/MiniMax-H3/raw/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md)，
  仅证明输入，不证明媒介执行或 literal canvas replay。
- managed Kimi invocation `480bed08-0eac-48cc-bc32-3b8d2bddd1d3` / route
  `4f2d5dc8-4234-4665-b382-e82f1ad6cc00` 的 read-only input audit 为 PARSED；receipt
  与两个实际 read hashes 已核验。它审的是 archived 7s 原 1–4 master，不是之后的 5s bytes。
  Parent 确认台词结束/反应窗口挤压与颈部提前泄漏问题，明确短台词约 2.55s 前结束、
  听声 onset 后可开始反应，并将狗哥改为本段完全画外。新 5s 由 Parent 核对，未冒称 Kimi 复审。
- 现有 FinalOutputContract goal 3 的 `sequence` 仍要求原九事件单次请求，与实测后拆分
  恢复冲突。经既有 QA owner 激活 goal 4，仅同步这一条及 user-goal 叙述；其余 final
  requirements 逐项相等断言通过，故事事件、声音和观看质量均未删减。raw acceptance
  scoped 为原 1–3 的八项要求。旧 profile/goal/failure 保留；没有调高失败阈值或屏蔽历史。
  `qa-scope.json` 明示 `final_requirements_unchanged=false`，不可误称所有 final 文字未变。
- 零 Provider effect 阶段修复两个 task-local 调用错误：requirements list 包进现有 canonical
  hash 的 mapping；补全缺失的已有 typed camera motion/relation 并校验完整 intent。
  后者只补对应现有 prompt 的轻微上移/停住及人物关系，不新增 schema。canonical prepare
  为 `GENERATE_ONCE`，exact body preflight PASS；`context_ir=false`、MiniMax-H3 / 768P / 5s。
- task `2107199862996754432`，一次 POST / HTTP 200；native body SHA
  `1b9089c37ab3423d89e925df2ca236791e54fdf1592b1aeac0b39437dccf6361`；raw SHA
  `cb92bb572364f4a007f22e165f87bebe9e632196556326dd9f153d193f709b74`，4,840,753 bytes。
  原视频 H.264 / 1344×768 / 24 fps / 124 frames / format 5.175s；AAC stereo / 32 kHz。
  既有 quota 9→10 / operator ceiling 18M→20M microunits 保留全部历史与 held reservations，
  `actual_cost=null`，不声称账单、结算或重置消费。durable request→POST 556.183s；
  submit→首次 observed succeeded 101.910s、fetch/reload/copy 完成 150.905s，均含本地开销。
- 落盘后显式 project-local MCP 21 帧 / .25s；exact-hash 1×静音播放至 ended，5.3311s wall
  / 26 captures；强制 zh Whisper base 检出一次“兄弟们”于 .86–1.40s。实际约 1.6s
  多切到另一侧脸/门构图，约 2.9s 再切三人，违反 0–3s 同机位；狗哥约 3s 起已在
  上亮窗露面，违反本单元 voice-only / intact-glass-before-reveal 末态。声音 onset 比封存
  1.8s 提前约 .94s，超过 .5s 容差；潘子约 1.25s 抬眼，实际听声→反应顺序改善，
  但原低眼持续时段不成立。不能继续沿用前次“先反应后声音”诊断解释本条。
  MCP threshold .3 自动检出一场景不代表没有可见 cuts；Parent 实际观看优先于该计数。
- canonical diagnosis：action / camera / close / identity / opening / sound FAIL，space /
  no-overlay PASS。identity 的三名室内角色可读，但完整 criterion 还要求狗哥不露脸；
  sound 只据已观察 timing 失败，音色/配乐/自然度仍 NOT_EVALUATED，ASR 不替代实际听音。
  无字幕/水印的视觉 PASS 只属于这条未修改 raw；AIGC metadata 不等于烧录文字。
  同时改变长度/参考/Context IR/表述且 seed uncontrolled，不据此归因某一参数消除了字幕。
  canonical experience `1b36f3a7d8ba0d377336ab2ccfe7609ff350a1f20fc56271bcf94890ab412965`，
  reject 后 Manifest revision 252 / attempt `failed`，保留 phase `validate` 和全部证据。

当前真实 blocker 是仍未合格的 raw 制作，不是要求新增 continuity architecture。
继续堆更长 prompt 或把这条失败末帧当 accepted source 没有依据；后续 repair 应针对表演时段、
机位与未揭脸的正确 reference/conditioning 取证，任何 I2V/FL2VA 比较留在同一真实 sequence，
不能凭本轮 PASS 子项推进。normal-speed sound、原 4–9、A2 editorial join、选 take、compose
及最终 MP4 仍未完成。自动 learning evaluation `no_candidate`：dependent retakes、多变量改动
及不同 scope 不支持独立通用能力结论，未新增 advisory claim 或修改 Skill/Policy/Gate。

Verification：本轮 exact staged record 的五项 documentation Harness PASS，policy audit
869 candidates / unmapped 0，product runtime skill boundary 两项 tests PASS；receipt
`.agent/harness/runs/fanxiang-reaction-production-checkpoint-20261006-002/receipt.json`。
Implementation Review Risk Gate 为 `KIMI_REVIEW_NOT_REQUIRED`：base `db93ef9`，tracked
candidate 只有本记录；Product source/credential/permit/recovery owner 未改，task-local
有限单次 submit 与已关闭失败由实际证据核验，无用户指定 implementation review，也无具体
critical authority/state-damage failure path 或重大后果且未验证的语义缺口。早期 Kimi input
audit 不冒充 final implementation review，raw quality FAIL 不因 Harness 或 review 结论解除。

### Supersession — Pose References And Native Adaptation Still Fail

2026-10-06 Hong Kong / 2026-10-05 UTC，用户继续后实际完成 Ba-03。本段取代下方
“八次 submit / reference strategy 尚未执行”的当前状态；此前真实结果保留。
当前第九次 Provider 结果 known fetched，但 raw quality FAIL，没有选 take、activation 或 Bb。
本轮仍未修改 Product source、通用 continuity contract、spec 或 plan。

- 原七图之外，新增两个已登记 DERIVED 的 native PNG：Ba-01 frame 84 / 3.5s 的三人
  站位/门轴，与 Ba-02 frame 240 / 10s 的潘子受袭空间关系。只继承这些具体属性，
  明确排除错误 eyeline；两者来自 FAILED media，`accepted_source=false`，不是交接末帧。
  未裁切、重绘或去水印，也没有使用原 V37 的带字视频作为 conditioning。
- 首段六个事件窗口保持 0–10.6s，末尾延续至 11s；原文适配为 H3 Ref2VA 六节英文
  prompt 与一次 tagged Chinese dialogue，而非原画布 literal replay。九图 exact identities、
  66 项 typed control expression、6998-character native master 和 lint 100 均只证明输入。
  managed Kimi invocation `d98e61a9-b096-42d9-b86b-a4edb91d5c69` 的 exact two-file
  input audit 为 PARSED；Parent 未发现阻断输入缺陷。这不是媒体验收。
  前一次 invocation `3dbf3f8a-9714-4180-88b7-0b65b42a1c54` 是
  STRUCTURED_OUTPUT_EXHAUSTED，没有可用 report，其 partial result 未用于判断。
- Ba-03 task `2107181047953514496`；body SHA
  `71fff81637cd238c5a8b3fafcb45dafb85746715614aaadbfca4e3512923c878`；raw SHA
  `42b7be665bac350e65ba5f04db8444cb01505293d2d972cb4b4699ec3a316d51`，10,851,846 bytes。
  raw 为 H.264 / 1344×768 / 24 fps / 277 frames / format 11.550s，AAC stereo / 32 kHz。
  显式 project-local MCP 23 frames、exact-hash 1×静音播放到 ended
  （11.7218s wall、47 captures）和 8.25s / 9s native PNG 共同确认：action / camera /
  close / no-overlay / opening / space FAIL，identity PASS，sound NOT_EVALUATED。
  约 2.1–3.1s 烧录“兄弟们”字幕；约 6.9s 多切一次，9s 完整磨砂玻璃重新出现且头的位置
  重置；末段小龙看键盘改善，但头颈与潘子停住，持续攻击未成立。
- 强制中文 ASR 只检出一次“兄弟们”于 1.9–2.76s；潘子在此前已抬眼/抬下巴。
  自动语言识别曾误判 Korean。尝试提供 actual audio 后，当前 assistant runtime 明确报告
  audio input unsupported，不能据 ASR 签配乐、人声自然度、音色或同步 PASS。
  canonical experience `8462e3debbca15ef1bbb8a0ee13895ed3f8ea36045700b79688a776ec57cc812`；
  `abandon_video_generation` 保留 findings，strict reload FAILED，Manifest revision 226。
- durable request→physical POST 为 500.815s；整体本地 pre-POST 约 12m30。
  terminal 的 106.492s 是 submit→首次 observed succeeded，包含本地 commit 延迟，不能当作
  纯模型计算耗时。保留全部九次消费与 held reservations，`actual_cost=null`；不是账单证据。

Ba-04 preparation 使用同九图，将六个事件归入四个实际 camera shots，existing profile
`context_ir=false`；master 6999 characters、66 项 control proof 与 lint 100。原六个 source
block hashes 和九图 identities 均未改变。第一次 prepare 的 task-local field 拼写错误在任何
Provider effect 前被 strict model 拒绝，改用已有 `context_ir` 字段后继续；未改 schema。
一次 daemon restart 中断了本地准备；确认进程已退出、request/fence/terminal 均不存在后
恢复同一 zero-effect preparation，没有重发 Provider。

canonical decision 最终为 `SPLIT_SHOT`，不是 compiler unsupported：三条 raw whole-result
失败触发 existing feedback feasibility intervention，该 proposal 以三份失败证据优先于新一份
输入策略 proposal。未创建 native request、paid attempt、permit 或第十次 submit；仅有本地
creative/profile/dependency 准备。没有调高 failure threshold、屏蔽 history、删除旧 findings
或修改 Gate 来继续采样。`B/sequence-Ba-take-04/preparation-blocker.json` 封存 exact decision 与九次 actual count。
关闭 Context IR 尚未获得实测，不能归因它造成或消除了字幕。

输入完整不等于模型能按动作、时间与切镜执行；没有原 uploaded image bytes、原历史模型与
sampling 条件，也不能称“完全复现画布”。当前可行性停点是未通过的 raw quality 与现有
recipe feedback Gate。下一制作单元应进一步区分听声抬眼/见脸、破窗袭击、反击缩回，保持
每段完整事件关系，重新核定各段 QA 与真实 accepted handoff；不要只换四个 cut labels
继续同一 11s 请求。尚未 author/submit 这些更小的单元。Bb、选 take、compose 与 final MP4 未完成。
自动 learning evaluation：`no_candidate`；dependent retakes、seed uncontrolled、同时改变输入
不能支持通用能力/adoption claim，也不外推已有 local H3 claim 至 remote Ref2VA。

### Supersession — Two Actual Split Candidates And Unaccepted Handoff

2026-10-06 Hong Kong / 2026-10-05 UTC，用户“可以”接受拆分后，真实执行 Ba-01 与一次
针对性 Ba-02 retake。本段取代下方“尚未执行 split requests”的停点；历史六次结果保留。
当前 physical submits 为八，全部 known succeeded/fetched，无 unknown outcome。
close-state 与此前 source blocker 修复仍已 push；本轮不修改 Product source、通用 continuity
schema/interface、spec 或 plan。新媒体与 task-local helpers 位于 ignored `B/`，不是已发布的
通用 Production Harness CLI。

- 第一 generation sequence 保留原分镜一至六的文字与 0–10.6 秒时间，request 为 11 秒，
  末尾 0.4 秒明确延续当前袭击；第二段预留原分镜七至九：拿键盘、重击、吃痛缩回。
  首段使用同一七张 captured canvas images 的 bytes/order，移除完整 V37 video guide，
  不把后段动作留在共享 guidance。`Image 4` 是黄衣潘子，`Image 2` 是黑衣小龙，
  room / door 分别为 `Image 6` / `Image 3`。A-02→Ba editorial join 仍为 NOT_EVALUATED。
- 沿用 existing `Shot sequence-B`、Planner、Router、compiler、QA、committer owners。
  经既有 creative artifact commit 把该 Shot 改为首段 fixed 11 秒；不是修改公共 duration contract。
  用户接受 partition 后登记 final goal version `3` 和首段八项 raw QA：action、camera、close、
  identity、no-overlay、opening、sound、space。原完整九分镜的 final requirements 保持不变，
  旧 goal、旧 FAIL、A-02 的旧七项 PASS 均保留；不能把首段 QA 解释成完整成片通过。
  在相同 goal version 内换 rubric 的预检曾被拒绝，改用显式新版本后才准备执行。
- managed Kimi read-only input audit invocation `2089b8d2-b8a9-4826-9533-44bf4d573d88`
  为 PARSED。Parent 确认 primary locked camera 与原第六镜后撤冲突，改用 existing dolly_out /
  follow 字段并明确只约束第六镜；补齐原文已有 motion / foley，不新增 schema。
  sealed 旧 bytes 留存，修订 bytes 是 Parent verified，未伪称 Kimi 审过新 bytes。
  首段 master 为 3038 characters；native body SHA
  `5ae06451d596c7d1769caee11a800af1fa5b4d9b43dd7e6a4ccf65b6813a1b02`。
  compiler 对 music `none` 的 lexical expression 曾拒绝编译；改用实际 verbatim dialogue 作为
  同一完整 sound observable 的 expression anchor，保留无配乐与全部音频验收要求。上述拒绝
  都在 POST 前，没有消费调用数；不是为过 Gate 新增 schema 或假签声音 PASS。
- Ba-01 task `2107166621276991488`；raw SHA
  `5c265179f817280b979fc79866cf7add8e46a5162efeaf455aef102e1448e67b`，11,024,846 bytes。
  explicit project-local MCP 23 frames 和 exact-hash 1×静音播放到 ended
  （11.7127 秒 wall、46 captures）后，action / camera / close / no-overlay FAIL，
  identity / space PASS，opening / sound NOT_EVALUATED。约 2–2.7 秒烧录“兄弟们”字幕；
  末段头颈停在门边悬垂，持续袭向潘子的动作未成立。canonical experience
  `d0f481a6d2b8acf455b7c1e3457e6e154c950dcaff45f22c845b89f299c7ab2f`，
  explicit abandonment 后 strict reload FAILED，Manifest revision 187。
- Ba-02 保留相同模型、七图、11 秒 profile、stack、compiler 与原六镜。
  native request 只有 `content[0].text` 变化：明确对白仅进入声音、不得成为字幕；要求头颈在
  尾段持续逼近黄衣潘子。master 为 3319 characters；lint PASS、100/100，只是结构证明。
  body SHA `886d2ab29997016d2068c1dc9bc21c3aab9c40ec25f937f8c1951dfb8d2300ad`。
  比较明确声明 `prompt_text` 变化，seed uncontrolled；不是 controlled A/B。
- Ba-02 task `2107169914993008640`；raw SHA
  `3e33ac328c92d5df3104410a75a6e971c3f7d3eed199206357aead7a2a6c3ede`，11,562,174 bytes。
  MCP 23 frames 与 exact-hash 1×静音播放到 ended（11.7125 秒 wall、46 captures）确认：
  action / identity PASS；camera / close / no-overlay / space FAIL；opening / sound
  NOT_EVALUATED。9.4–10.2 秒袭向黄衣潘子、潘子后退明显改善；但字幕再次出现，
  3–4.5 秒三人面朝镜头、绿色门在身后，视线未指向门上方，后段改朝门却没有可读的转向；
  结尾小龙仍看头颈/人物，没有必要的键盘 gaze。canonical experience
  `8e535db9063e780bea96ec8be5487d120f8e4e78a1bf69e81796b19b737a606c`，
  diagnosis evidence `41099faebddef88a0f2e23d6ddc8c4c7ffa9872d617ada21839ac16dcc88871a`。
  `abandon_video_generation` 保留全部 findings 后 strict reload FAILED，Manifest revision 201。
  不是把局部 action PASS 扩大为选 take；没有 activation、accepted Ba source 或后段 submit。
- 两条 raw 均 H.264、1344×768、24 fps、277 frames、format duration 11.550 秒、
  AAC stereo / 32 kHz。真实长度没有归一化成 nominal 11 秒，也未做 VALIDATE/ACTIVATE
  来宣称 duration accepted。submit→succeeded / fetch 分别为 54.876 / 74.750 秒与
  54.731 / 82.897 秒。durable request started→physical POST 分别约 115.707 秒与
  224.045 秒，本地校验耗时已超过模型生成；这是当前制作流程的实测耗时，不推断具体根因。
  调用数只增加 6→7→8；operator monetary ceiling 为 12,000,000→14,000,000→16,000,000
  microCNY，保留实际计数、held reservations、`actual_cost=null`，不是账单或伪造 SETTLED。

本轮 blocker 是 actual raw quality：拆分与 targeted prompt 改善了攻击对象和运动，但两条首段
都未达到完整要求。不能继续给字幕叠禁止词并盲抽，不能跳过 gaze / space，不能把失败末帧冒充
accepted handoff。下一步应改 reference 准备，把三人朝门的视线/站位、攻击目标和交接姿态先做成
可检视的制作 reference，再在同一 production sequence 内用 MiniMax 验证；尚未执行或证明该策略。
第二段仍待首段全项 PASS。现有 scripts 已覆盖编译、byte audit、permit/submit/poll/fetch、MCP
检查入口及 QA persistence；创作 reference、表演/空间裁决、原声验收、选 take 与最终剪接仍未闭环。
没有 20–40 秒 final MP4；旧 composition content_driven blocker 与 A-02 原画布 fidelity 边界仍保留。
自动 learning evaluation 为 `no_candidate`：同一片段的 dependent retakes、uncontrolled seed 和
变动 inputs 不建立通用 MiniMax 能力结论；既有 local H3 claim 不外推到 remote Ref2VA。

### Supersession — Sixth Actual Take And Motion Guidance Failure

2026-10-06 Hong Kong / 2026-10-05 UTC，用户“继续”后实际执行了一个有界 B-04-motion candidate。
本段取代下方“五次 submit”“没有第六次 POST”与仅分析的停点；下方 chronology 保留为历史。
当前 physical submits 为六：A 两次、B 四次，全部 known succeeded/fetched；没有 unknown outcome。
本轮没有改 Product source、通用 continuity architecture、schema、contract、spec 或 plan。

- 沿用 METASO `MiniMax-H3`、七张参考图的 exact bytes/order、原九分镜、台词、无配乐要求与七项
  required QA。把 room / door 的冲突数字明确改成 `Image 6` / `Image 3`，并以原画布实际 V37
  的派生视频作为 `Video 1` 动作/表演参考，替换近黑的原 2 秒 video reference。
  这是一条改变输入策略的 production retake，不能称原画布 exact replay。
- V37 原片 SHA `65cb5e6889b3824725bdaab64f2397e7b20ac39eafb6974c30c6e48b4c9518ef`。
  实际提交的 guide SHA `9b9c7d8958e6d93d9b792392fed11acfe41002a6f780a720386cc3fab6bf1194`，
  6,904,359 bytes、1280×720、24 fps、359 frames、format duration 14.959 秒。
  ffmpeg 转码并裁去末尾约 114 ms，保留原声与可见空破口，未声称 decoded frames / audio bytes
  不变；最先得到的 15.001 秒 derivative 未提交。guide 经 Registry 登记为 DERIVED，
  不是 accepted predecessor，不能证明 A-02→B 的连续性。
- 有界 Kimi read-only input audit invocation `83449d5c-0a4f-4584-8826-55d416b358e6` 为 PARSED。
  Parent 确认其双重 timing authority finding：参考片实际剪点与原文时间不同。
  因此在 POST 前明确“原分镜时间/顺序为主，Video 1 仅指导动作、表演、受力反馈”。
  旧 sealed snapshot 留存；修订后的 bytes 为 Parent verified，未伪称 Kimi 审过新 bytes。
  receipt/report/adjudication 分别位于 `B/sequence-B-take-04-motion/input-review-*.json`；
  subagent input audit 不是媒体 QA 或 acceptance。
- sealed prompt 为 5792 characters；native body SHA
  `3c442f5d32013bdd16a90046d34253b2c22f51c77b288b3ab9c138add62870de`。
  `input-fidelity-audit.json` 与 `reference-slot-map.json` 核验七图、一视频和 aliases；
  comparison 明确申报 `adapter_compiler_hash`、`adapter_compiler_id`、`media_bindings`、`prompt_text`
  四个变化，seed 未受控。前期 compiler delta 未申报时 LINEAGE_MISMATCH 在 POST 前阻断，
  修正申报后才继续；没有以普通 resample 隐藏 input delta。
- 本轮仅一次实际 POST，task `2107157729280548864`。raw MP4 SHA
  `d443b4413b649a0f477283fd0a94e913885cddef50f3e218ec84d38b9565780f`，4,422,314 bytes，
  H.264、1344×768、24 fps、362 frames、15.083 秒，AAC stereo / 32 kHz。
  submit→fetch 103.246 秒；success/fetch 不构成选 take。
- explicit project-local `video-analysis` MCP 的 31 frames、exact-hash 1×静音播放到 ended
  （wall 15.4396 秒、62 captures）及 native frame 击打段复查后：action / camera **FAIL**；
  identity / space / visible close PASS；opening / sound NOT_EVALUATED。
  实际 8 秒破窗后约 9.2 秒冲向黑衣小龙，原要求的袭向黄衣潘子没有成立。
  10.65–10.9 秒可读到键盘接触面侧及头部偏转，随后抽回，是局部改善；
  但反击比原 12–14 秒提前，12.5 秒已持续空窗，完整九分镜节奏仍失败。
  全片左上角出现“AI生成”标记，违反 prompt 的无水印要求；guide 本身含此标记，
  复制来源为合理推断，未隔离其因果。正常速度播放明确 muted，不能宣称听取了新原声。
- canonical experience hash `fd2fc1d3243894d9e1ba4d68d39f59e1810321f98e2eae5633ed9f1b30708014`；
  `diagnosis.json` 保留 QUALITY_FAILURE / EVIDENCE_GAP。视觉失败不能靠同 bytes 补听音修复，
  经 `ProductionStateCommitter.abandon_video_generation` 明确弃用，strict reopen 为 FAILED，
  Manifest revision 157。未激活、不供下一段使用、不要求用户再次筛查这条明显失败候选。
- 有界 submit count 5→6，已消费五次历史保留，仅新增一次；旧/新 monetary ceiling
  10,000,000→12,000,000 microCNY 是 operator upper bound，不是实际账单。
  旧 reservations 保留，`actual_cost=null`；无伪造 SETTLED、无 permit reuse 或 consumption reset。

本轮停点是已知失败的 production candidate，不是新的架构 blocker。完整事件链已经尝试原文恢复与
实际动作视频指导，后者局部改善击打却丢失正确攻击对象、节奏并新增水印；证据不支持再照同配置重抽。
下一次制作应在原第六/第七分镜之间拆成两个相互承接的 generation sequences：前段保留沉思、
三人抬头、破窗及袭潘子，后段保留抓键盘、重击、吃痛缩回；保留完整事件与实际状态承接，
不是一镜头一 request。后段只能在前段 exact required QA 通过后 submit；若时间需 trim，仍由
现有 ResolvedTimeline / HyperFrames 所有者负责。此处是制作策略判断，尚未执行新的 split requests。

close-state 与此前 source blocker 修复仍已 push；composition 的 content_driven duration blocker
未变化，没有 20–40 秒 final MP4 或 Final Acceptance。调用、fetch、byte audit、MCP 抽帧及 QA
persistence 已有 task-local 自动化，动作/表演判断、策略选择、音频验收与最终剪接仍需裁决。
自动 learning evaluation 为 `no_candidate`：本轮是多个变量变化、uncontrolled seed 的 dependent
retake，不由它建立“MiniMax 普遍不能复现”或“视频参考必然有效”的通用规则；没有 adoption。

### Historical Checkpoint — Five Actual Takes And Canvas Diagnosis

以下状态取代下文的“B 尚未 submit”“A 尚未激活”和旧账单等待动作；原始 chronology 与失败证据保留。
本 checkpoint 完成于 2026-10-06 Hong Kong / 2026-10-05 UTC。用户当前要求先分析为什么画布迁移失败，
因此停止新增生成；本轮没有第六次 physical POST，也没有最终 compose MP4。

- close-state 已收尾并 push。真实 endpoint timing / native audio blocker 修复已以
  `32cafb32346a113ef750811701cd12b080a8068e` push 到 `main`。
  exact staged receipt `.agent/harness/runs/fanxiang-native-audio-and-real-timing-20261005-003/receipt.json`
  为 PASS，16 selected checks；production contract suite 3868 PASS / 3 SKIP / 2064 deselected，
  1787.83 秒。提交前已核验 freshness、snapshot、policy、artifact integrity 与 checkout cleanup。
  当前 2.7 Manifest / 2.2 Registry、dependency transition、strict reload、已激活 source、held reservation
  及 replay 不重复提取均有 targeted evidence。Parent final Risk Gate 为 KIMI_REVIEW_NOT_REQUIRED。
  Harness PASS 不构成下列视频的质量验收。
- physical submits 总数为五：A 两次、B 三次，均已知 succeeded/fetched；没有 unknown outcome。
  A-02 在早期改写后的 criteria 下七项 PASS，并已 canonical ACTIVATE/SUCCEEDED；该历史不撤销。
  但原画布 fidelity 与最终成片未验收，不能把旧 PASS 扩大到用户后来明确的完整画布要求。
  A-02 原声 WAV 已登记并 strict reopen；末帧和尾段只是软参考，不证明 hard frame conditioning。
- B-01 与 B-02 视觉 FAIL，均 canonical FAILED。B-02 用户明确原声合理，同时明确表情、动作与末段
  12 秒衔接错误；其 USER_AUDIO PASS 不能迁移到 B-03。
- B-03-final 恢复原九分镜全文、七张参考图与原 2 秒 video reference，继续使用用户明确指定的
  METASO MiniMax-H3。actual MCP 31 frames 与 exact-hash 1×静音播放已检查。
  canonical diagnosis `7dab6b431aef69695e56f3925e7cc340091084e0da7d5eca313f2f7315b96ebf`：
  action/camera FAIL，identity/space/visible close PASS，opening/sound NOT_EVALUATED。
  用户整体评价 FAIL 后经 committer abandon；strict reopen status FAILED，不激活、不供下一段使用。
  已知画面失败不靠继续询问用户听音来补成 PASS。
- 曾有 `sequence-B-take-03` 的 repair-policy preflight failure，以及 final driver 的 compiler mismatch；
  两者均发生在 POST 前。前者经 canonical `not_submitted` evaluation 与 close 封存，后者在确证纯 REQUEST、
  无 paid/fence 消费后恢复同一 intent。原四次消费不重置；有界扩展至五次后仅新增一次实际 POST。
  所有 reservations 保持 held，`actual_cost=null`；无伪造结算，也未把上界当实际费用。
- 真实 composition preflight 尚有 `Shot sequence-A content_driven duration is unsupported.` blocker，
  见 `B/composition-preflight-blocker.json`。本 checkpoint 未修 composition、未建立第二 timeline；
  首先解决原片动作质量与实际剪接关系，再考虑既有 owner 的最小修复。

### Canvas Transfer Diagnosis

此前 A/B authoring 并非完整模仿画布：把原 coverage 重写为三段、删除“兄弟们”与吃痛吼叫、
用 A-02 的真实尾段代替原 video reference。这是 Parent 的制作偏离，不是用户授权的忠实迁移。
下文旧 Director choice 仅保留为历史，不能作为当前 creative authority。

B-03-final 的真实 native POST body 已逐字重建并逐个 base64 解码核对：原全文只替换七个 reference
label，5570→5557 characters；七图、一视频的 SHA 与所取 Registry bytes 一致。
但这个 audit 只证明客户端对 captured inputs 的 fidelity，不能称“原画布生成条件完整复现”：

1. **已确认的输入语义歧义**：文中仍写“参考图1：606宿舍室内大远景”和“参考图2：606宿舍门内侧特写”，
   H3 ordered aliases 的 Image 1 / Image 2 却分别是长颈狗哥 / 小龙；宿舍和门实际是 Image 6 / Image 3。
   attached labels 已替换，但 prose 编号未消歧。它是需要修正的迁移缺陷；当前没有隔离实验证明它导致重击失败。
2. **动作未被参考视频示范**：原 `11 - 副本` reference 是约 1.881 秒、45 frames 的近黑视频。
   actual MCP 四帧与全部 45 decoded frames 核对，无可见人物或重击动作；全分辨率 grayscale max 2/255。
   音轨存在，不声称静音或已知用途。兼容版仅 clone 三个末帧至 2 秒，前 45 decoded frames 与 AAC packets
   保持，SHA `b581e8f36e3df91af6012d1265557fee9bf8c13e68911fe38f82430ac3371f56`。
   原成功 V37 的攻击/受击 MP4 并未被当作 motion reference 输入。
3. **已知差异与不可证部分**：current canvas composer 显示 Seedance 2.5，实际执行 MiniMax-H3，符合用户选型；
   当前 UI 不证明原成功视频的历史 submit model/seed。使用的七图为 720px preview WEBP，
   尚未核验原 4K 上传 bytes。`context_ir_enabled=true`，响应未返回 IR text，不能认定服务端未改写，
   也不能把 Context IR 当作已证明的失败原因。

原成功 V37 与新 raw MP4 对比：B-03 约 1.8 秒由潘子侧脸切到正面近景，违背“同一机位，不立刻切”。
11.872–12.122 秒小龙挥键盘后，12.37–13.12 秒狗哥仍继续伸向潘子，没有清楚的命中面门、头部带偏、
吃痛撤回链；原 V37 同段有明显受击表演。新片修掉了 B-02 的“先空窗后再出现正脸”，
但不能因此把重击因果标为 PASS。原物料 SHA：V37
`65cb5e6889b3824725bdaab64f2397e7b20ac39eafb6974c30c6e48b4c9518ef`。

当前结论是客户端语义迁移存在缺陷、该实际 H3 take 的镜头与动作执行失败；并无证据证明
continuity schema 缺失、H3 普遍无法完成或单一 IR 参数就是根因。
下一制作动作应先统一 reference aliases，再评估原成功 V37 可追溯动作素材的有界视频指导，
明确这属于改变 conditioning strategy，不能继续称原输入 exact replay。当前未制作或提交该新 candidate。
只有真实效果仍失败时再依据失败拆 sequence；不预先拆成逐镜请求，不开启泛化架构研究。

诊断 anchors：`B/sequence-B-take-03-final/input-fidelity-audit.json`、
`original-reference-black-frame-audit.json`（同目录）、`actual-analysis-tool.json`、
`normal-speed-playback-metadata.json`、`actual-findings.json`、`diagnosis.json`、`user-feedback.json`；
原片分析为 `B/canvas-V37-actual-analysis.json`。静音播放不能证明声音合格；Whisper small 自动识别为 ko
也不能证明实际韩文台词。本轮不追问用户为已拒绝的画面补声音结论。

Driver 已能自动执行 canonical planning/submit/poll/fetch、input byte checks、MCP 抽帧、原声登记与
QA persistence，但仍是 task-local prototype；reference 语义映射、表演/动作裁决、策略选择与最终成片验收
尚不能宣称自动化。学习评估仍为 `no_candidate`：依赖 retake 链、多个变量变化与 uncontrolled seed，
不推导普遍模型能力；没有新 specs/plans、continuity contracts 或 learning adoption。

### Historical Production Checkpoint

以下为 B 生成前的 checkpoint。其待办、费用与 quality 状态已按上文 supersede，保留原始时间边界。

- close-state 与费用 coverage 修复均已 push，后者 commit `59838ff`。其 exact staged Harness
  `.agent/harness/runs/fanxiang-known-success-reservation-20261005-001/receipt.json` PASS，
  production contract suite 3865 PASS / 3 SKIP；receipt freshness、scope、policy、artifact hashes
  与 checkout cleanup 全部核验通过。Parent Risk Gate 为 NOT_REQUIRED；没有修改 submit authority、
  凭据、egress 或 unknown-outcome fence，held reservation 与 later settlement strict reload 已验证。
- A-02 经 actual MCP frames、1×播放、真实 reference 比对及用户两次原声确认，七项 raw requirements
  已全部 PASS，最新 diagnosis evidence 为 `539f8f9bcc0d37411906989eef5cac1ae4f7382c12293d1a19a8d724def459d2`。
  offscreen 身体、手部和未发生新事件的状态承接明确作为 cinematic inference；没有声称直接看见隐藏部位。
  Final Acceptance 仍 NOT_EVALUATED。A-02 已通过 canonical candidate/activation，accepted source 已严格重开。
- 两条 H3 原片的 362 frames / 15.083 seconds 实际触发旧 nominal endpoint 容限。修复最多两帧且要求
  duration/frame 一致；第三帧、错配与 exact timing 仍拒绝。相关 video suites 107 PASS。
  原 request 没有 seal terminal，故没有补签 P7：从实际 A-02 最后一帧 361 提取、登记 `z-A2-actual-terminal`
  为软参考，source MP4、PNG、tool identity 与 derivation receipt 可追溯。没有硬首帧保证。
- 原生音轨入口实际拒绝 Manifest 2.7，故仅为真实 compose 修复既有 owner，覆盖 current version、
  held cost coverage、ACTIVATE source、dependency transition 与 non-speech identity。
  A-02 原声已实际登记，32 kHz / stereo，strict reload 成功；WAV SHA256
  `f6a057fec61d67f613bc24419d3336be7312163bff63b58dd190f5e18728bf27`。
  登记未增加 Provider submit，没有把 unknown cost 写成零或上界。
- B 仍处于真实 generation preflight；尚未生成 B 或 compose 成片。其目标为整条撞窗→袭击→抓键盘重击→缩回
  事件链，一次 15 秒 request。A 原片实际超过 H3 video reference 15 秒上限，故 B 使用真实尾帧软参考和八张
  原场景/角色/键盘 references。declare IDENTITY_STYLE_CARRYOVER，实际起始长颈/完整玻璃须由 raw QA 裁决。

本轮学习判定为 `no_candidate`：这是同一 production 的依赖 retake 链，seed 未控制，没有两个独立 A/B
arms；不能由工程 PASS 或一次声音确认推导通用模型能力。没有新 specs/plans 或 continuity schemas。

close-state slice 与未发布 commits 已收尾并 push。随后实际启动 Production loop，进行了两次 METASO H3 付费 submit，得到两条真实 15.083 秒 MP4。没有单独开启 H3 A/B 研究或扩展通用 continuity architecture。

第一条完整目标仍为约 30 秒；目前只生成了 sequence A 及其针对性 retake，sequence B 尚未 submit，也没有完成 compose、30 秒成片或 Final Acceptance。第二个 take 获用户实际声音确认，但没有成为 canonical accepted source。

先通过 canonical `VideoGenerationService.validate_once` 复现账单阻断：`production_state_invalid`，`Remote video validation requires exact settled evidence.`。该调用没有新 Provider effects，Manifest 完全未变。用户随后明确“不需要管预算”；现已针对这一真实 blocker 修正为允许 known successful video 在 reservation 保持 held 的情况下继续制作。真实成功与费用结算分别保留，不用 operator upper bound 伪造实际成本。真实 A-02 激活仍需后续逐项 QA，不由这项代码修正自动升级。

本记录的 task-local evidence root 为 `runs/fanxiang-production-loop-20261005-001/`，下文简称 `B`。媒体、私有输入与运行 prototype 保持 ignored/local-only，未上传 Git。

## Close-State Publication

- 当前关闭动作：补齐 close-expression helper/test 的 changed-path mapping 与覆盖套件 argv；修正 predecessor guard 测试中缺失的 current requirement projection。没有新增 continuity schema。
- source commits：`93240b4` 与 `d20c50fef55d78284325bc6716981c5aea2802c9`。连同之前三个未发布 commits 已 push 到远端 `main`。
- exact range：`d607726643a25bcbaadd3debaa0ec7ef36337201..d20c50fef55d78284325bc6716981c5aea2802c9`。
- source receipt：`.agent/harness/runs/close-state-production-closure-20261005-002/receipt.json`；20 checks PASS，2 checks 由同轮覆盖跳过；freshness、scope/policy/artifact integrity、complete proof 与 isolated checkout cleanup 已验证。
- policy audit：869 candidates，零 unmapped/unreferenced/unverified paths。closing-path 回归测试 14 PASS，predecessor guard 24 PASS；其余 checks 的实测范围见 receipt。
- closure records commit `bba87ce` 已 push，docs receipt 为 `.agent/harness/runs/close-state-closure-records-20261005-001/receipt.json`。
- 第一次 range receipt 中 guard fixture FAIL 保留；baseline 上已经存在的 Agent Memory answerability calibration FAIL 未被改写。上述通过不宣称全 repository 任意测试均已绿。

## Story And Generation Sequences

真实源是已登录即梦 canvas《反相之地第一集》的 V36→V37：狗哥在宿舍门外微笑、持续伸颈贴近上亮窗；随后撞碎玻璃袭向潘子，小龙取键盘重击，狗哥缩回留下破口。`B/canvas-source.json` 保存当轮 composer 与 source hash。

初始设计为两个 15 秒 generation sequences，各包含三个内部 coverage，只有两个初始 Provider requests：

| Sequence | Internal Coverage | Event And Handoff |
| --- | --- | --- |
| A | 0–4 秒门内 POV；4–6 秒小龙反应；6–15 秒原 POV 连续伸颈 | 正常颈长→微笑→伸颈→脸贴完整玻璃；末段低声一次“龙哥”，门仍关闭 |
| B | 0–5 秒撞窗；5–12 秒室内袭击与键盘反击；12–15 秒缩回 | 必须承接真实 A 的 accepted state；先明确潘子、小龙、曾亮与书桌位置，再完成袭击、防卫、破口留存 |

没有默认一镜头一 request。B 删除重复的贴脸铺垫与“兄弟们”是本次 Director choice，不伪称用户原句。B 的 staging 补充来自 independent concept review，尚未经过真实生成验证。

“白带子”的原始方法来源本轮未找到可独立核验的材料；这里采用用户明确要求的制作闭环与当前 canvas 的实际制作证据，不宣称已经复刻完整原方法。

## Inputs And Execution Boundary

9 张真实 reference：狗哥正常/长颈、小龙、潘子、曾亮、上亮窗、关闭的绿门、宿舍、键盘。现有 captures 与新 canvas captures 的 provenance/bytes 分开记录，位于 `B/references/` 与 `B/reference-captures.json`。A 实际使用前五张；B 的 references 与 accepted-source binding 尚未提交。

`B/director-coverage.json`、`final-output-contract.json`、`creative-goal-binding.json` 经既有 validators 通过。Production 使用现有 Project、Registry、Manifest 2.7、Planner/Router、remote prompt compiler、VideoGenerationService 与 ProductionStateCommitter；没有第二 state/timeline owner。

实际 lane：METASO `MiniMax-H3`，Ref2VA，`remote-video-prose-v1`，`context_ir_enabled=true`，native audio，15 秒/768P。requested ratio 为 16:9，真实输出测得 1344×768、7:4；自适应 geometry 不伪称 exact 16:9。所有 current close facts 经现有 compiler 进入 native prose，不能把 content hash 当媒体语义。

本任务封存 physical submit ceiling 4（2 initial + 2 targeted retakes），wall window 7200 秒，unknown outcome 停止。实际只消费 2 次，均 POST 200、status succeeded、fetch 完成。每次经 exact preview、Budget Guard/reservation、durable intent、one-use permit 与 task submit fence；operator-configured upper bound 为每次 2,000,000 microCNY，不是市场价格或实际账单。本轮 `actual_cost=null`。

凭据仅通过用户提供的 exact private reference 注入 supplier；密钥不进入 argv、日志、receipt 或 Git。

## Actual Takes And Review

| Take | Provider Job | MP4 SHA-256 | Bytes | Result |
| --- | --- | --- | --- | --- |
| A-01 | 2107120446158958592 | af7547f32603e042b60a8db452acb42fc2e110c2d104b74534219cc8cc098a94 | 2,119,812 | 真实伸颈出现；缺小龙反应镜头，宿舍背景误放狗哥身后；FAILED，未激活 |
| A-02 | 2107123515718922240 | bfa4216dfa8eb77dbd3f61a0b397c10ecb4c082b83c02ce03f1827f31a305fd7 | 9,777,067 | 补出小龙反应与室内/走廊背景区分，保留伸颈；已 fetch，处于 VALIDATE/evidence hold |

两条均为 H.264、24fps、362 frames、15.083 秒，AAC stereo/32kHz。生成完成约 67 秒，完整 submit→fetch 约 75–77 秒。Provider completion 不是媒体 acceptance。

A-02 是同一 sequence 的生产 retake：保持 Provider、profile、references 与 output，用 authored `production_repair` Intervention 明确改变 `prompt_text`；seed 未受控。默认 resample 对实际 prompt delta 报 `LINEAGE_MISMATCH`，在 POST 前被阻止；改用已有 Intervention owner 后才提交，没有假装 zero-delta。它不是 controlled A/B，也不能证明 prompt 修改的因果效果或普遍成功率。

每条 exact MP4 落盘后显式调用 project-local `video-analysis` MCP，并经真实 `ProjectAnalysisSession`/`ControlledPresentationVerifier` 写入逐项 evidence。A-02 又在 Chrome 以 1×静音播放到 ended：browser SHA/bytes 与 MP4 一致，wall 15.2741 秒，61 个 250ms samples；3.845/4.095 秒与5.845/6.095 秒实际画面夹定两次切镜，满足原 ±0.5 秒容差。自动 scene detector 返回一场并漏掉切镜，不能替代实际 coverage 判读。

最新 canonical A-02 feedback hash：`98e90fc884dc8def6c563c0f78d41a11a8b113d80a97441f1772487f04c44055`，通过既有 `repair_evidence=True` 对同一 MP4 补充 1×播放证据，不 resubmit。之前 `f1b065c4cb7b698785a9ec57b8f39e9193dc20b5b114556df13b1d41b1101f19` 保留。camera、identity、reveal 已有视觉 PASS；完整 near-door/transom/red-tag 关系及全部 current-close facts 尚未完全裁决。原声在该次 analyzer receipt 中仍 NOT_EVALUATED，后到的实际用户反馈独立保留，不能改写旧 receipt。

## Audio Evidence Correction And User Observation

Parent 无法直接听取音频。Whisper base 将两条短台词均放在 0–1 秒；追加真实 MCP medium 后，A-01 的“龍哥”位于13.04–14.28 秒，A-02 却得到13.68–15.08 秒的不同文字。故撤回“base 已证明台词提前”的解释，保留原 receipt/chronology，并以 `B/sequence-A-take-01/dialogue-evidence-correction.json` 显式标记当前 dialogue 为 NOT_EVALUATED。A-01 的独立 coverage/spatial failure 仍成立。

用户实际观看 A-02 后回复“是的,自然”，并进一步明确“没有，原声符合要求”，确认末段一次“龙哥”、句后停口与自然原声，无配乐、额外人声或突兀惊吓声。exact question/answer identities 与 artifact hash 保存在 `B/sequence-A-take-02/user-audio-feedback.json`。这是独立的 USER_AUDIO 观察，不是全片 Final Acceptance，也没有修改 analyzer authority 或伪造 accepted source。

## Concrete Blocker

`B/sequence-A-take-02/activation-blocker.json` 记录 canonical `validate_once` 的实际返回：paid phase `accepted`，video phase `validate`，`production_state_invalid`，non-retryable；Manifest unchanged，new Provider effects 0。

原 `_state_commit_video_candidate.py` 要求 exact SETTLED reservation 与非空 `actual_cost_microunits`。本轮 Provider result/status 没有提供实际费用；configured upper bound 不能填进 actual cost。向用户请求 billing evidence 后，用户明确“不需要管预算”；该后续指令取代本轮等待用户账单的动作。未查询官方价格、估算账单或 fabricated settlement。

这是真实 Production activation blocker，修正仅复用现有 accepted/settled phases 与 RESERVED reservation，不新增 schema fields：保持 exact accepted submit/request/fetch/provenance；RESERVED 必须有 sealed upper bound 且 actual cost 为空；SETTLED 仍要求真实 actual cost。released/unsettled、缺 bound/submit 与 unknown outcome 不放行。strict active-video reader 核验同一 immutable coverage snapshot；成功 video 才可保留 accepted paid phase，不能扩大至其他普通 paid operation。未来真实费用到达仍可 settlement，并重开既有 activated video。

targeted red reproduction 在旧规则下失败；修正后“prepare→activate→strict reload→later actual settlement→strict reload”通过，相关 paid/video suites 在第一稳定候选上 79 PASS。最终 source snapshot 的相关 Harness 尚需独立运行；本记录不以该 fixture 宣称真实 A 已激活。

不跳过真实 QA 或 activation，不直接拼 FFmpeg 成片，不用旧/offline accepted source 提交 B。generated native audio 的旧 target/version 与 settled-source 约束本轮尚未实际触及，未预防性扩展。

## Automation And Remaining Manual Work

本轮已经能通过现有 owners 自动执行 reference byte/provenance 校验、goal validation、Planner/Router/compiler、exact preview、permit/budget/count fences、submit/poll/fetch、probe/MCP 抽帧转录、feedback persistence 与 canonical state 变更。真实失败后能保留历史、提 targeted Intervention 并重新生成。

这些 driver 仍是 task-local prototypes，尚不是可重复调用的完整 Production Harness CLI。剧情选择、reference 角色分配、看画面后改 prompt、完整语义裁决、人工原声听取、费用证据提供仍需人工。B、take selection/accepted state、native audio 注册、ResolvedTimeline/HyperFrames compose 与最终正常速度验收尚未执行。

`ProjectAnalysisSession` 在当前主机解析 Python symlink 后会丢失 configured virtualenv 的 `mcp` dependency；本轮 prototype 保留原 literal virtualenv entrypoint 后，真实 stdio MCP 成功。它是已暴露的 production glue gap，不用 fixture/缓存替代真实调用，也未扩建新分析架构。

后续主线是处理本条 sequence 的实际证据/结算，完成 accepted take→B→compose。只修这些真实 loop 暴露且确实阻断的 seams；不要再做泛化 continuity schema、独立 H3 研究或更多 offline proof 来代替成片。

## Independent Review And Learning Evaluation

Production concept 经 managed Kimi `deep`、sealed read-only contract 与 canonical receipt review；invocation `9c82eb3b-f9f2-4d78-95bc-3775514627f2`。frozen reads 与 wire route 验证，Parent 裁决保存在 `B/concept-parent-adjudication.json`。它不证明实际媒体、费用结算或 Production acceptance。

自动 learning evaluation：`no_candidate`。两次执行身份各自明确，但 A-02 依赖 A-01，属于同一生产修复链；seed 未控、完整 QA 未过，不作为两个独立支持实验或 controlled arms。既有 `h3-shot-local-visible-context` claim 明确排除 remote Ref2VA 与音频/全速验收，本轮不扩大其范围。focused experience retrieval 返回 exit 3（library-incompatible shards），CLI 自行排队派生索引刷新；本轮不重试、不手动重建，当前事实来自实际源码、receipts 与媒体。

## Evidence Index

non-Q0 identity 绑定 actual METASO task、同一 Production attempt、request 与结果；每次执行的多个 proof layers 保留同一 key，dependent retake 不据此获得独立 admission。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1-FETCH | metaso-task:2107120446158958592 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-01 | N/A | af7547f32603e042b60a8db452acb42fc2e110c2d104b74534219cc8cc098a94 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | `B/sequence-A-take-01/terminal.json` |
| A1-VISUAL | metaso-task:2107120446158958592 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-01 | N/A | af7547f32603e042b60a8db452acb42fc2e110c2d104b74534219cc8cc098a94 | ANALYZER_VISUAL | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | A1-FETCH | `B/sequence-A-take-01/actual-findings.json` |
| A1-DIALOGUE-CORRECTION | metaso-task:2107120446158958592 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-01 | N/A | af7547f32603e042b60a8db452acb42fc2e110c2d104b74534219cc8cc098a94 | ANALYZER_DIALOGUE | NOT_EVALUATED | EVIDENCE_GAP | CONCLUSION_SUPERSEDED | A1-VISUAL | `B/sequence-A-take-01/dialogue-evidence-correction.json` |
| A2-FETCH | metaso-task:2107123515718922240 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-02 | N/A | bfa4216dfa8eb77dbd3f61a0b397c10ecb4c082b83c02ce03f1827f31a305fd7 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | `B/sequence-A-take-02/terminal.json` |
| A2-RAW-QA | metaso-task:2107123515718922240 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-02 | N/A | bfa4216dfa8eb77dbd3f61a0b397c10ecb4c082b83c02ce03f1827f31a305fd7 | ANALYZER_QA | NOT_EVALUATED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | A2-FETCH | `B/sequence-A-take-02/diagnosis-before-user-audio-and-spatial-review.json` |
| A2-USER-AUDIO | metaso-task:2107123515718922240 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-02 | N/A | bfa4216dfa8eb77dbd3f61a0b397c10ecb4c082b83c02ce03f1827f31a305fd7 | USER_AUDIO | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | A2-FETCH | `B/sequence-A-take-02/user-audio-feedback.json` |
| A2-ACTIVATION | metaso-task:2107123515718922240 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-02 | N/A | bfa4216dfa8eb77dbd3f61a0b397c10ecb4c082b83c02ce03f1827f31a305fd7 | CANONICAL_ACTIVATION | BLOCKED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | A2-FETCH | `B/sequence-A-take-02/activation-blocker.json` |
| A2-FINAL-QUALITY | metaso-task:2107123515718922240 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-02 | N/A | bfa4216dfa8eb77dbd3f61a0b397c10ecb4c082b83c02ce03f1827f31a305fd7 | HUMAN_FINAL_ACCEPTANCE | NOT_EVALUATED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | A2-FETCH | `B/final-output-contract.json` |
| A2-OLD-CRITERIA-QA | metaso-task:2107123515718922240 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-02 | N/A | bfa4216dfa8eb77dbd3f61a0b397c10ecb4c082b83c02ce03f1827f31a305fd7 | ANALYZER_QA | PASS | NONE | CONCLUSION_SUPERSEDED | A2-RAW-QA | `B/sequence-A-take-02/diagnosis.json` |
| A2-ACTIVATED-OLD-SCOPE | metaso-task:2107123515718922240 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-02 | N/A | bfa4216dfa8eb77dbd3f61a0b397c10ecb4c082b83c02ce03f1827f31a305fd7 | CANONICAL_ACTIVATION | PASS | NONE | CONCLUSION_SUPERSEDED | A2-ACTIVATION | `B/sequence-A-take-02/selection.json` |
| B1-FETCH | metaso-task:2107140087601061888 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-take-01 | N/A | 9a1238dfdae49e5698ae508ddad4c4a426c1ab5ba3ccaaa7273ca0edd3659761 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | `B/sequence-B-take-01/terminal.json` |
| B1-RAW-QA | metaso-task:2107140087601061888 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-take-01 | N/A | 9a1238dfdae49e5698ae508ddad4c4a426c1ab5ba3ccaaa7273ca0edd3659761 | ANALYZER_QA | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | B1-FETCH | `B/sequence-B-take-01/diagnosis.json` |
| B2-FETCH | metaso-task:2107141969118650368 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-take-02 | N/A | af54906e2e744ee0e79d5f7670839f99e96f607e07f7262809df1dad212706b3 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | `B/sequence-B-take-02/terminal.json` |
| B2-RAW-QA | metaso-task:2107141969118650368 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-take-02 | N/A | af54906e2e744ee0e79d5f7670839f99e96f607e07f7262809df1dad212706b3 | ANALYZER_QA | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | B2-FETCH | `B/sequence-B-take-02/diagnosis.json` |
| B2-USER-AUDIO | metaso-task:2107141969118650368 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-take-02 | N/A | af54906e2e744ee0e79d5f7670839f99e96f607e07f7262809df1dad212706b3 | USER_AUDIO | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | B2-FETCH | `B/sequence-B-take-02/user-feedback.json` |
| B3-FETCH | metaso-task:2107149534800142336 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-take-03-final | N/A | 1ceae93f8c88f1b2f002a6559e0282d6a02198a8a3a76187789450b38f5a321b | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | `B/sequence-B-take-03-final/terminal.json` |
| B3-RAW-QA | metaso-task:2107149534800142336 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-take-03-final | N/A | 1ceae93f8c88f1b2f002a6559e0282d6a02198a8a3a76187789450b38f5a321b | ANALYZER_QA | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | B3-FETCH | `B/sequence-B-take-03-final/diagnosis.json` |
| B3-USER-OVERALL | metaso-task:2107149534800142336 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-take-03-final | N/A | 1ceae93f8c88f1b2f002a6559e0282d6a02198a8a3a76187789450b38f5a321b | USER_OVERALL | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | B3-FETCH | `B/sequence-B-take-03-final/user-feedback.json` |
| B4-FETCH | metaso-task:2107157729280548864 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-take-04-motion | N/A | d443b4413b649a0f477283fd0a94e913885cddef50f3e218ec84d38b9565780f | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | `B/sequence-B-take-04-motion/terminal.json` |
| B4-RAW-QA | metaso-task:2107157729280548864 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-take-04-motion | N/A | d443b4413b649a0f477283fd0a94e913885cddef50f3e218ec84d38b9565780f | ANALYZER_QA | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | B4-FETCH | `B/sequence-B-take-04-motion/diagnosis.json` |
| Ba1-FETCH | metaso-task:2107166621276991488 | fanxiang-production-loop-20261005 | fanxiang-production-loop-Ba-take-01 | N/A | 5c265179f817280b979fc79866cf7add8e46a5162efeaf455aef102e1448e67b | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | `B/sequence-Ba-take-01/terminal.json` |
| Ba1-RAW-QA | metaso-task:2107166621276991488 | fanxiang-production-loop-20261005 | fanxiang-production-loop-Ba-take-01 | N/A | 5c265179f817280b979fc79866cf7add8e46a5162efeaf455aef102e1448e67b | ANALYZER_QA | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | Ba1-FETCH | `B/sequence-Ba-take-01/diagnosis.json` |
| Ba2-FETCH | metaso-task:2107169914993008640 | fanxiang-production-loop-20261005 | fanxiang-production-loop-Ba-take-02 | N/A | 3e33ac328c92d5df3104410a75a6e971c3f7d3eed199206357aead7a2a6c3ede | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | `B/sequence-Ba-take-02/terminal.json` |
| Ba2-RAW-QA | metaso-task:2107169914993008640 | fanxiang-production-loop-20261005 | fanxiang-production-loop-Ba-take-02 | N/A | 3e33ac328c92d5df3104410a75a6e971c3f7d3eed199206357aead7a2a6c3ede | ANALYZER_QA | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | Ba2-FETCH | `B/sequence-Ba-take-02/diagnosis.json` |
| Ba3-FETCH | metaso-task:2107181047953514496 | fanxiang-production-loop-20261005 | fanxiang-production-loop-Ba-take-03 | N/A | 42b7be665bac350e65ba5f04db8444cb01505293d2d972cb4b4699ec3a316d51 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | `B/sequence-Ba-take-03/terminal.json` |
| Ba3-RAW-QA | metaso-task:2107181047953514496 | fanxiang-production-loop-20261005 | fanxiang-production-loop-Ba-take-03 | N/A | 42b7be665bac350e65ba5f04db8444cb01505293d2d972cb4b4699ec3a316d51 | ANALYZER_QA | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | Ba3-FETCH | `B/sequence-Ba-take-03/diagnosis.json` |
| Reaction1-FETCH | metaso-task:2107199862996754432 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-reveal-take-01 | N/A | cb92bb572364f4a007f22e165f87bebe9e632196556326dd9f153d193f709b74 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | `B/sequence-B-reveal-take-01/terminal.json` |
| Reaction1-RAW-QA | metaso-task:2107199862996754432 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-reveal-take-01 | N/A | cb92bb572364f4a007f22e165f87bebe9e632196556326dd9f153d193f709b74 | ANALYZER_QA | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | Reaction1-FETCH | `B/sequence-B-reveal-take-01/diagnosis.json` |
| Reaction1-VOICE-TIMING | metaso-task:2107199862996754432 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-reveal-take-01 | N/A | cb92bb572364f4a007f22e165f87bebe9e632196556326dd9f153d193f709b74 | ANALYZER_DIALOGUE | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | Reaction1-FETCH | `B/sequence-B-reveal-take-01/explicit-transcription-tool.json` |
| Reaction1-ACTUAL-SOUND | metaso-task:2107199862996754432 | fanxiang-production-loop-20261005 | fanxiang-production-loop-B-reveal-take-01 | N/A | cb92bb572364f4a007f22e165f87bebe9e632196556326dd9f153d193f709b74 | ANALYZER_AUDIO | NOT_EVALUATED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | Reaction1-FETCH | `B/sequence-B-reveal-take-01/actual-findings.json` |
