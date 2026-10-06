---
record_kind: session_summary
topic_id: fanxiang-v36-v37-production-loop
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Fanxiang Formal Edit And Impact Sound Record

Date: 2026-10-06

## Current Status — User Rejection Supersedes Prior Pass

### User Decision — Omitted Contact Rejected And Voice Needs Reperformance

用户明确审片决定：**不接受动作省略，保留明确命中的原要求**；“兄弟们”声音太正气，不符合形象，需调整。
13.875s基线及13.375s备选exact SHA重验未变，现有审片入口已显示上述决定；整体NOT_ACCEPTED。
`runs/fanxiang-action-match-20261006-004/user-review-decision.json`绑定两版SHA与原反馈，
不回写旧QA、Manifest、`final-status.json`或暂停instruction；下文pending表达状态已被这次人工拒绝取代。
核查上一轮接触补镜：`resolved-request.json`为`image_to_video`，只有B03第287帧首帧，
`media_bindings=[]`；实际`request.json`仅`text`/`image_url`，**没有视频参考**。
当前`metaso_h3`另有`REFERENCE_TO_VIDEO`视频参考入口，但此接触镜尚未实测，不能保证命中成立。
具体未授权方案见`runs/fanxiang-action-match-20261006-004/user-feedback-repair-proposal.md`：
一次候选复用现有挥击/撤退参考，并补人工实拍的2–3s键盘接触软质道具参考（当前缺失），不改通用架构；
声音拟只人工重录原句，先听辨气质和核对原混合音轨的对白分离，不能盲改整轨。
本次media generation/export/audio edits均0，不重复创建暂停记录；补拍仍需新exact输入授权。
受管Kimi deep `d093213c-213b-4e68-bd4c-7ea30a0dd8cc`仅审查sealed文本方案，Parent核验exact Read与report SHA；
它没有独立读原请求或看听媒体。Parent直接核查原请求；审片入口仅验证两版metadata/暂停状态，未作新感知验收。
本次文档检查receipt：`.agent/harness/runs/fanxiang-user-review-decision-20261006/receipt.json`；媒体和方案仍local-only。
`distill-ai-video-learning`评估`no_candidate`：同一未验收修复链的新人工反证，无新独立实验或相关既有claim。

### Historical Pause — Preserve Both Versions And Await The User Decision

用户明确要求收尾保存并暂停本段自动修复。保留13.875s基线和13.375s动作省略备选，
现有`runs/fanxiang-action-match-20261006-004/review.html`同时提供两版审片入口。
本次没有生成、导出、改prompt、改切点或改声音，两个MP4 exact SHA与下文原值重验一致。
用户认为现有画面能表达挥击后撤退，同时明确画内接触缺失和头颈姿态跳变仍在；
这不是接受省略接触表达，也不是画内命中或整段声画PASS。原要求、原对白和素材历史不改，声音听感待用户确认。
下一步只等待用户明确决定：接受后再最终混音与封版；不接受则单独讨论制作缺口，不能自动启动补拍或修复循环。
本暂停instruction只保存Agent操作边界，不重写Production QA、Manifest activation或旧receipt。
记录检查receipt为`.agent/harness/runs/fanxiang-edit-pause-record-20261006/receipt.json`；
`distill-ai-video-learning`评估`no_candidate`，没有新实验或经验claim。

### Historical Alternative — Action Match With Contact Omitted, Later Rejected By User

用户要求以保留的13.875s稿为基线，只做一版动作匹配剪辑，不生成、不改架构，不用闪白/黑帧或
夸张音效掩盖缺口。**本版只验证省略接触时反击→撤退能否读懂，表达是否接受由用户决定；
原画内命中要求UNSATISFIED_UNCHANGED，整体NOT_ACCEPTED，下一剧情单元仍BLOCKED**。
证据前缀 `M = runs/fanxiang-action-match-20261006-004/`。

- Parent实际查看B03 258–291及recoil 68–106帧：B03 289仍是快速挥击中的手/电脑键盘，
  recoil 84已经低头后开始向右上破窗回缩。只选B03 [0,290) → recoil [84,101) → B03空窗[348,362)，
  均为source零基半开区间；去掉原recoil [77,84)慢起步及[101,107)多余空窗，main多保留一帧速度段。
  没有变速、补帧、定格、闪白、黑帧、叠加贴图或新生成素材，空窗窗口保持基线。
- `M/action-match-review.mp4`实际完成：1344×768 H264、48k stereo AAC、321frames/24fps，
  video13.375s、container13.397s、6,768,267bytes，SHA
  `5b127a6f5af7a848e64bfc9cc6ac50025c09f6bfed2d280f14e702578df20def`。
  `M/production-action-match-01/project.yaml`经既有Registry / SourceUseEvidence / CompositionSpec /
  ResolvedTimeline / P4 / HyperFrames / ProductionStateCommitter实际render activation及strict reopen。
  独立待审项目的source-use admission只覆盖此诊断表达，绝不等于原接触QA通过；旧QA/raw历史不回写。
- 复用基线完全相同的`main-native.wav`，main programme从sample0到580000、gain -3dB，
  原对白和“兄弟们”触发时序保持。`M/audio-preservation-measurements.json`实测输出前0–4.8s
  解码samples与13.875s基线完全相同（correlation1.0、max absolute difference0）。
  尾段只复用已有静底一次、62000samples，不循环、不新覆盖开头、不新合成/删除台词。
- 沿用同一Mixkit `hit-blow`及-4dB，第一次导出发现旧5681samples补偿不是当前解码WAV的实际峰值；
  实测stereo峰值为8829samples，仅在备选中改为start571171、峰值580000/12.083333s，对应挥击→后缩切点。
  两次本地render是同一套cuts的SFX落点校正，首稿完整保留在`M/first-sfx-placement/`；只交付一个备选。
  最终解码peak -1.478dBFS、fullscale samples0；这只证明电平/placement，不证明实际听感或画内命中。
- `M/playback-execution-summary.json`绑定最终SHA，真实Chrome HTML视频1×非静音播放至ended，
  wall13.5575s、0掉帧；累计decode delta317不冒充实际成片321帧。Parent检查68张实际播放捕获，
  包括整段采样及11.5s以后的密集接点：切入后缩没有原慢低头开头，但头颈姿态跳变、破口/景别差异仍在。
  不声明完整因果成立；由用户决定省略接触表达是否可接受。**实际听辨NOT_EVALUATED**。
  初次Chrome MCP evaluate无响应，取消的调用不作证明；随后仅启动自有有界Chrome进程实际播放，已关闭。
  `M/explicit-mcp-review.json`为最终exact MP4显式project-local分析调用，无issues不升级为视觉/声音PASS。
- 受管Kimi deep `1323a73b-a391-4072-b378-43446ad6e5c5`只读审查cuts/sample算术、对白保留和验收边界，
  134.808s、2 wire requests，Parent核验exact source Read及canonical report SHA、逐项裁决。
  其文本报告未看听媒体，也未评价后来8829samples落点；最终placement来自Parent实测及当前CompositionSpec。
  未触发Implementation Review Risk Gate：无通用代码/共享契约/安全权属变化，现有owners完成可逆独立待审输出。

`M/final-status.json`保持PENDING_USER expression acceptance；13.875s原稿SHA
`48f94931e2bc09ee52dc9c049f1cbf91aae2df5668a6aab98cf8ba256917d27e`重验未变。
本轮media generation calls0，parent paid-media physical chain仍14；不自动补拍或改prompt。
媒体/receipts均local-only；文档checkpoint的exact staged Harness receipt为
`.agent/harness/runs/fanxiang-action-match-record-20261006/receipt.json`，不作为感知验收证明。
`distill-ai-video-learning`自动评估`no_candidate`：同一未验收修复链的一个表达备选，不是受控模型比较，
没有独立成功支持或相关既有claim可更新。不改Skill/Policy/Gate；RAG返回stale advisory后继续现有媒体取证，无前台重建。

### Historical Attempt — One Authorized Contact Retake Rejected In The Full Cut

用户明确授权本轮一个 `metaso_h3 / MiniMax-H3` I2V候选，沿用已展示的B03第287帧和修订prompt，
请求4s raw、最多一次提交、operator上限2 CNY（不是官方报价或实扣金额）。实际提交一次并取回，
没有重抽。**可信键盘命中仍未补成，候选REJECTED；保留13.875s原稿，成片NOT_ACCEPTED，下一单元BLOCKED**。
证据前缀 `C = runs/fanxiang-contact-retake-20261006-003/`、
`U = runs/fanxiang-production-loop-20261005-001/sequence-B-contact-retake-take-01/`。

- 先读取`N/attack-minimal-retake.md`，实际查看B03 286/287/288帧与接镜对照。
  first-frame是B03 zero-based287/11.958333s原解码PNG，SHA
  `379c0f78e97132ab5773ec559986d2bb9e30159762be560c356f65ffc0121a36`；没有图像生成或贴图编辑。
  新raw `U/output.mp4`为107frames/24fps、4.458333s、1344×768，SHA
  `cef1954d5bae5311a294c935092e575574df6e8831cd113a0ae364d6ae9230ba`。
  返回raw超出请求时长保持真实历史，outcome `FETCHED_UNACTIVATED`，不伪造generation activation。
- 实际新raw从第2帧起把黑色电脑键盘变成带黑白琴键的乐器；对照现有keyboard reference可确认道具错误。
  动作变成顶在头/脸旁停住，只有轻微头部位移，缺乏一次可信接触。头颈和原破窗连接局部改善，
  不能抵消道具与命中FAIL，也不能凭此前局部PASS保留这个镜头。
- 已用既有Registry / SourceUseEvidence / CompositionSpec / ResolvedTimeline / P4 / HyperFrames /
  ProductionStateCommitter实际接回整段：B03 [0,287) → new raw [0,17) → recoil [77,107)
  → B03空窗[348,362)，均为各自source的zero-based半开区间；新插镜0.708333s。
  `C/contact-join-rejected-review.mp4`为348frames/24fps、video14.5s、container14.522s、
  H264/48k stereo AAC，SHA `8b51a0f034961d960138d7dfabf2394fc654939eb36f2f2d35248beca112aefc`。
  这是**未采用的失败对照**，独立editorial项目技术render activation不代表正式成片或候选QA通过。
- 对照保留原B03节目声及台词时序，原声main到11.958333s、gain -3dB，之后静底桥接；
  new raw原声不入混音。失败对照没有撞击SFX，避免用声音掩盖未成立的接触；
  原13.875s稿的声轨、取键盘、撤退及既有SFX均未修改，exact SHA仍为下节原值。
- `C/requested-contact-use-policy-17f.json`、`requested-contact-use-evidence-17f.json`及
  `requested-contact-use-assessment-17f.json`经现有typed public owner实际评估为FAIL，绑定当前17帧和正确接触用途。
  diagnostic-window-use只证明identity/range/format可进入失败审片，不等于接触PASS；旧18帧证据和旧QA不回写。
  `C/explicit-raw-mcp-review.json`与`explicit-join-mcp-review.json`保留两次显式project-local调用，
  工具无issues不推翻Parent从实际画面确定的道具/动作失败。
- `C/playback-execution-summary.json`绑定exact对照SHA：真实1×、非静音播放至ended，wall14.6862s、
  dropped delta0。Parent查看62张实际播放捕获中的整段采样与11.7–13.2s密集接点帧，
  琴键突变、顶住脸的停顿及切入撤退仍不成立；详见`C/whole-join-adjudication.json`。
  **不能实际听辨，actual hearing NOT_EVALUATED**；播放/波形/采样画面不升级为整体声画验收。
- 新scope task `user-approved:fanxiang-contact-retake-20261006-003`仅一Shot、submit limit1，
  正常通过既有paid gate与one-use permit；上传输入和native prompt保持本轮授权的exact bytes。
  原项目准备阶段停止于外部effects之前，计划扩界没有生效；其13次历史和paid ledger原样保留。
  新任务消耗1，parent physical chain为13→14，external task `2107467303215857664`，actual cost unknown。
  `C/scoped-task-lineage.json`、`U/physical-submit-consumption.json`、`U/terminal.json`为边界证据；
  新单次授权不重置旧任务，不释放旧held预算，不改continuity / Router / Provider架构。
- 本地首次18帧/349frames诊断render因实际音频比delivery contract少32samples而失败，没有绕过验证。
  删去一个已停住的尾帧并经既有committer同步Shot duration、dependency revision后，17帧/348frames
  诊断render成功并strict reopen；失败attempt与旧revision保留。只修产品素材选择，没有通用代码修改。
- 受管Kimi deep `80596e9b-6222-4ac1-9245-22bb286f02e5`只读审查sealed文本方案；
  Parent核验receipt、source read和report hashes并逐项裁决。它没有观看或听辨媒体，不拥有QA验收。
  本轮无共享产品实现变更，Implementation Review Risk Gate未触发，不叠加独立实现review。

媒体和receipt仍ignored/local-only，只有此记录及直接supersession notices进入Git。
文档exact staged Harness receipt：
`.agent/harness/runs/fanxiang-contact-rejection-record-20261006/receipt.json`，只证明记录路径checks。
自动调用`distill-ai-video-learning`评估为`no_candidate`：单次道具失败、同一未验收修复链，
没有足够独立支持/受控比较或现有claim更新依据；不把“拆镜+选窗”升格为成功经验，不修改Skill/Policy/Gate。
剩余：可信接触仍缺失；原台词、接缝声音与整段节奏需要人工听看。预算耗尽停止本轮，不再堆prompt或生成。

### Retained Base — Restore Native Trigger And Remove Floating Head

用户继续要求修14.125s稿的0–4.8s静音与11.21–12.29s悬空攻击镜。本轮只修这两个接点，
无通用架构修改、无媒体生成，旧raw/旧QA/两个此前局部短窗确认保持历史。
当前输出改为 **13.875s修订待审稿，NOT_ACCEPTED，下一剧情单元BLOCKED**。
新证据前缀`N = runs/fanxiang-av-repair-20261006-002/`。

- 开头误删触发声成立：原B03 master prompt规定门外“兄弟们。”引起潘子抬眼、三人转头；
  中文Whisper small识别源1.3–2.22s“兄弟们”，只作佐证，不是听音裁决。
  旧主声轨从sample144000开始，前三秒替换底声。现恢复原生混合节目0–12.041667s，
  原时序、gain -3dB，删除所有intro loops；不重写/合成/去除台词。
  按原剧情逐字文本绑定language/script_hash，现有AudioImportRequest登记为DIALOGUE，
  `CompositionSpec`绑定main Shot；P4仍独占placement/mix。
- 源攻击镜完整头部下方没有颈部连接，背景破窗接不上；`N/attack-survey.jpg`保留实际帧。
  `N/attack-crop-test.jpg`证明紧裁切仅移出轮廓与窗，不能修复空间，本轮拒绝该裁切方案。
  攻击近景撤下；现用B03 [0,289)取键盘/挥击起势→recoil [77,107)→B03空窗[348,362)。
  在source frame289之前切出，排除随后头部继续袭潘子的失败状态。**画内击中接触仍缺失**，
  不把结果反应或SourceUseEvidence窗口用途PASS当作完整接触动作已成立。
- 同一Mixkit撞击SFX移到12.041667s反应切点，输入前导补偿5681samples、gain -4dB；
  0.5s自然片段含尾部淡出。静底只从main结束后桥接，没有重复响尾音或新BGM。
- `N/revision-av-review.mp4`为333frames/24fps、1344×768 H264、48k stereo AAC，
  video13.875s、container13.897s、6,872,598bytes，
  SHA `48f94931e2bc09ee52dc9c049f1cbf91aae2df5668a6aab98cf8ba256917d27e`。
  当前独立editorial项目经既有owners实际render/activation/strict reopen；原项目不回写。
- `N/audio-restoration-measurements.json`：前4.8s RMS从-59.616恢复为-22.333dBFS；
  触发段RMS从-59.245恢复为-16.675dBFS。导出与输入原声相差1024samples/21.333ms，
  补偿该编码偏移后的相关度0.999919、增益-3.010dB；全片decode peak -3.298dBFS、无满幅samples。
  这些只证明节目声恢复，不证明台词清晰、音色正确、撞击同步听感或整体声画连贯。
- `N/playback-execution-summary.json`绑定exact SHA，实际rate1/nonmuted播放至ended、0掉帧；
  浏览器累计decode counter337并非成片frame count333，包含加载/seek。
  已检查真实播放捕获的开场与11.75–13.5s切点；只作采样画面检查，没有真实连续听辨。
  `N/explicit-mcp-review.json`为exact MP4显式project-local调用，无issues不等于质量PASS。
- `N/attack-minimal-retake.md`只提出一个0.7–1.0s可用攻击窗口：真实颈部连接原破口、
  单端握键盘一次接触并下偏，尾态接现有recoil。此处方案当时未执行；后续一次授权执行及失败见上节。
- 受管Kimi deep `0710ece5-d7d9-4ee9-a1fa-988a72ac02f9`只审音频恢复计划，实际read/report hashes
  已核验；Parent用最终CompositionSpec核实0/0起点、578000samples结束、旧intro全移除。
  不称其审过成片。普通可逆素材编辑未触发Implementation Review Risk Gate，无新增产品代码。

仍需人工听原台词的可懂度/门外距离感、撞击音色/同步、整段正常速度节奏；画内接触缺口单独保留。
当前没有整体声画验收，不能进入下一剧情单元。记录文档Harness receipt：
`.agent/harness/runs/fanxiang-av-repair-record-20261006/receipt.json`；不作为媒体质量证明。
自动learning evaluation为`no_candidate`：同一修复链且完整成片存在反证，不增加独立成功计数。
RAG返回stale advisory fragments后继续当前取证，未等待/重试索引刷新；未修改Skill/Policy/Gate。

### Historical Revision — 14.125s Still Rejected

2026-10-06，用户实际观看后指出“明显声音和有些shot不对”，并确认“都有”。
用户反馈绑定下方12.5s输出SHA `af37152c6acce2feaa9c64bb44d957d22e8cf7bb352397d384c3049a23f69c61`。
当前状态为 **REJECTED_BY_USER / NOT_ACCEPTED，下一剧情单元BLOCKED**。
下方“视觉剪辑判定PASS、可作为下一单元基线”只保留为历史误判，不再是当前质量结论。
原raw/旧QA/用户此前两个短窗与3.625s局部join的确认不回写；本次拒绝的是完整组合。

Parent实际执行过播放器1×播放并查看采样帧，没有完成真实连贯声画观看与听辨。
把这种证据升级为整段视觉PASS/剧情可用，是本次验收错误；0掉帧、工具无issues、工程Harness
与声波时间对应均不证明完整质量。视频分析MCP仅提供metadata/frames/ASR等证据，不代替感知验收。

Current evidence prefix `R = runs/fanxiang-edit-rejection-20261006-001/`。

- `R/quality-rejection.json`、`R/rejected-v5.mp4` 保留用户拒绝和原exact bytes。
- 原“room tone”实际取B03 14.5–15.0s：RMS -7.429dBFS、peak -0.263dBFS；
  -9dB后每0.45s重播0.5s，开头7段、后部9段。未经听辨就将高能量尾音当环境底循环，
  是已核实的混音配方错误；`R/audio-measurements.json`不是耳听验收。
- Ba02 [221,240)可见黄衣潘子在头前抬臂，未给出黑衣小龙连续取键盘的动作；
  把这个窗口写成“小龙开始反击”缺少证据。破窗再出现落玻璃，跨镜接点也不能仅凭局部因果判PASS。
  原源帧证据为`R/Ba02-first.png`、`R/Ba02-last.png`、`R/B03-wide.png`。
- 只执行一次有界compose修订，new generations=0：删Ba02，B03改用[0,269)，保留其黑衣小龙
  取键盘的准备；attack [9,35)、recoil [77,107)、empty [348,362)保持。
  高频尾音循环撤掉，换原B03 3.0–4.5s低能量片段，RMS -56.466dBFS、peak -43.782dBFS，
  gain -3dB、1.5s片段/1.4s周期。保留原撞击SFX，新contact frame293/12.208333s。
  这仅是已知配方/接点的修正，不构成听感PASS。
- `R/revision-review.mp4`为 **修订待审稿**：339frames、14.125s，container14.147s，6,956,513bytes，
  SHA `c32159a86584f927ee39c4055b13ae71aa3c70b042bfcadb3e1ac354190a8ca4`。
  由同一canonical owners完成render/activation/strict reopen，不更改原项目或generation activation。
  `R/revision-playback-summary.json`记录真实1×非静音执行、339frames/0掉帧；只证明播放执行。
  `R/revision-explicit-mcp-review.json`为该exact文件的显式project-local MCP调用。
- `R/revision-status.json`保持NOT_ACCEPTED：攻击近景的背景玻璃与前后破窗形态/光照仍需裁决，
  主观听感仍NOT_EVALUATED。当前环境不能直接听辨；没有后续Shot submit。

制作经验继续作为待验证的局部方法保存，不能把“拆镜+选窗”写成这条正式成片已成功。
自动learning evaluation仍为`no_candidate`：同一素材修复链，并出现完整成片的明确反证。
没有修改Skill/Policy/Gate，也没有重跑或改写原工程PASS来制造媒体验收。

## Historical Status — Initial Formal Edit

停止生成后，复用 B-03、Ba-02、attack、recoil 原始 bytes，通过既有 SourceUseEvidence /
CompositionSpec / ResolvedTimeline / P4 / HyperFrames / ProductionStateCommitter 完成正式剪辑与 render activation。
当前剪辑项目为 `runs/fanxiang-formal-edit-20261006-001/production-v5/`；
原 generation 项目、raw 历史与旧 recoil QA 未回写。

正式输出 `runs/fanxiang-formal-edit-20261006-001/fanxiang-defense-final.mp4`：
1344×768，24fps，300 frames，video/audio stream 各 12.500s，container 12.522s（AAC 尾包）。
6,104,860 bytes，SHA-256
`af37152c6acce2feaa9c64bb44d957d22e8cf7bb352397d384c3049a23f69c61`。
这是当前独立 editorial 项目真实激活的 render 输出；不证明原 raw generation 的 activation、
P6 或 human Final Acceptance。MP4 与 run receipts 为本机 ignored artifacts，没有上传媒体。

视觉剪辑判定 PASS；实际 1× 非静音播放完成，0 dropped frames。
当前模型不支持音频听辨，主观听感与完整 human Final Acceptance 仍为 NOT_EVALUATED。
画面可作为下一剧情单元的基线；完整声画放行仍需人工听音，本次未提交下一 Shot。

## Selected Windows

所有范围为 24fps、半开区间，保持自然速度；没有补帧、重复末帧、变速或保留未选垃圾段。

| Order | Source | Source Frames | Source Seconds | Used Duration | Final Seconds |
| --- | --- | --- | --- | --- | --- |
| 1 | B-03-final | [0,211) | 0–8.791667 | 8.791667s | 0–8.791667 |
| 2 | Ba-02 | [221,240) | 9.208333–10.000000 | 0.791667s | 8.791667–9.583333 |
| 3 | attack-take-01 | [9,35) | 0.375000–1.458333 | 1.083333s | 9.583333–10.666667 |
| 4 | recoil-take-01 | [77,107) | 3.208333–4.458333 | 1.250000s | 10.666667–11.916667 |
| 5 | B-03-final empty window | [348,362) | 14.500000–15.083333 | 0.583333s | 11.916667–12.500000 |

Source prefix：`runs/fanxiang-production-loop-20261005-001/`；
对应子目录为 `sequence-B-take-03-final`、`sequence-Ba-take-02`、
`sequence-B-attack-insert-take-01`、`sequence-B-recoil-insert-take-01`，文件均为 `output.mp4`。

原 attack/recoil 各 107frames/4.458333s 超过 nominal 请求4s的 output-contract failure 继续保留。
旧 recoil 误绑 attack rubric 的 NOT_EVALUATED 也继续保留。
当前用途另建 exact source-byte / parent-Shot / 窗口 / transform 绑定的 SourceUseEvidence，
使用 analyzer authority，五个窗口通过 assess_source_use；不伪造 human proof。

## Editing And Sound Decisions

主干止于破窗近景，排除后续伸颈动作：先播放那段再接 Ba-02 会重复接近状态。
还去掉主干切点前仅两帧的宽景，避免闪切。使用硬切：
破窗威胁→室内三人准备→键盘击中→下偏受击→连续撤回→空窗。
攻击与反应短窗保持用户已确认的原窗口，末尾空窗多用两个真实原生帧。

recoil 源画幅为1440×736，其他源与 delivery 为1344×768。
新增唯一必要产品接缝 `FixedTransform.video_fit=cover`，显式固定居中填满裁切；
当前 recoil 用途证据绑定该 transform。默认 `exact` 继续拒绝画幅不符，保留旧序列化/hash，
旧全幅证据不能资格化新裁切。没有修改 continuity、Router 或 Provider。

撞击 SFX 使用已安装 video-shotcraft 的 `hit-blow.mp3`（Impact of a blow），
现有 attribution 指向 Mixkit SFX 2150，使用 Mixkit Sound Effects Free License；
没有网络下载或新生成声音。转换为48kHz stereo PCM仅作输入准备，最终 placement/mix 仍归 P4。
SFX取0.5s，gain -1dB，尾部0.1s fade-out。
其文件前导到10%峰值为5681samples/118.354ms，因此track开始于502319samples/10.464979s，
重击对齐全片 frame254/10.583333s；接 recoil 在frame256/10.666667s。
最终 AAC 解码波形匹配落点比 authored transient 晚1024samples/21.333ms，小于一帧；
这是可执行同步证据，不是耳听判定。

保留 B-03 的3s以后原生声（含破窗声），gain -3dB；
开头原生scratch转写有疑似多余词句，排除前三秒，改用原 B-03 空窗14.5–15.0s环境底。
反击段也使用该环境底桥接：0.5s片段每0.45s交叠，gain -9dB、50ms交叉淡入淡出。
attack/recoil 的 raw audio 不直接使用；无新增 BGM、字幕或旁白。

## Verification And Evidence

Evidence prefix `R = runs/fanxiang-formal-edit-20261006-001/`。

| Evidence | Actual Result | Boundary |
| --- | --- | --- |
| `R/raw-preservation-check.json` | 四条原 MP4 SHA/size 与原 terminal 一致 | 不重写 raw bytes |
| `R/*-source-admission.json` | exact ffprobe/count_frames、原 terminal、bytes | imported existing-source admission，不是 generation activation |
| `R/source-use-assessments.json` | 五个当前用途 PASS | 仅当前窗口与固定 transform |
| `R/composition.json`、`R/timeline.json`、`R/render-state.json` | canonical render、activation、strict reader reopen 成功 | 当前 editorial 项目，不是旧 raw 的 qualification |
| `R/final-probe.json` | H264/AAC、300frames、48k stereo、12.5s | 技术媒体属性 |
| `R/final-playback-1x-v5.json`、`R/final-playback-summary-v5.json` | ended=true、rate=1、muted=false、300frames、0掉帧、约12.677s wall；waiting仅加载起点0s | 真实播放执行，不替代耳听 |
| `R/final-explicit-mcp-review-v5.json` | 显式 project-local video-analysis MCP 返回当前 exact MP4 review | 指标不裁决语义；speaking estimate不稳定，不作无人声证明 |
| `R/final-audio-sync.json` | waveform sync误差21.333ms，低于一帧 | 主观听感 NOT_EVALUATED |
| `R/playback-counter-final.jpg`、`R/final-adjudication.json` | 可读因果/轴线、无重复状态、采样未见字幕水印 PASS | Parent画面判定，无 human Final Acceptance |

focused composition/source-use/planning/HyperFrames tests：312 passed、3 skipped；
最终 source-use transform 防回归 checkpoint：100 passed。
Exact code Harness receipt：
`.agent/harness/runs/fanxiang-explicit-video-cover-20261006/receipt.json`。
13/13 checks PASS；verify-receipt确认fresh/snapshot/scope/policy/artifact integrity及workspace stable。
代码checkpoint：`ead7967`；仅上述最小产品接缝、相关测试与contract matrix，未夹带其他工作。
Documentation-only checkpoint receipt：
`.agent/harness/runs/fanxiang-formal-edit-record-20261006/receipt.json`；
其结果由最终交付列出，记录内容本身不宣称已运行尚未完成的文档检查。

保留此前失败/淘汰的 editorial versions：初版音频 mux末端短32samples，保持失败 Gate；
v2 的14.5s组合存在重复接近；v3 的12.625s组合有切点短宽景残留；
v4 清理后音效仍需前导补偿；v5为当前输出。全部属于同一修复链，未重置 Provider预算或生成历史。

受管 Kimi deep 只读 mapping：第一次 upstream502导致 STRUCTURED_OUTPUT_EXHAUSTED，未采纳结果；
有限缩小scope后的 `9c1ef4cc-1378-4a9c-82ed-e0a09c9fb367` PARSED。
`R/kimi-run-retry.json`、`R/kimi-report.json`、`R/kimi-parent-adjudication.json` 保留route和Parent裁决。
Mapping确认现有 SourceUse/Registry边界；所有关键 claims仍由当前源码/测试/真实render核实。
Kimi并非最终媒体验收或 implementation adversarial reviewer。

## Production Experience

**复杂接触动作单镜失败 → 拆成攻击插镜 + 结果反应镜 → 选短窗 → 剪辑建立因果。**

本次可复用的制作方法：只要求攻击插镜给出清晰接触，只要求反应镜给出结果与连续撤退，
用短自然窗口和同步撞击声建立因果；不要要求一条raw完整覆盖所有复杂接触、受力和撤离。
整体剪辑还必须排除重复状态、反应前姿态跳变及无用尾部。

这是本次场景的经验，不是已验证的跨模型通用规则。
自动 learning evaluation 为 `no_candidate`：当前正式编辑版本属于同一素材/剧情修复链，
没有形成隔离变量的 controlled comparison 或足够独立重复支持。
不创建 placeholder claim，不修改 Skill/Policy/Gate，不标 ADOPTED。

## Manual Work And Remaining Risks

选窗、切点、节奏、SFX选型/增益/同步位置、画面裁决，仍由 Codex Parent手工做创作决定；
task script只是调用已有产品owners，不是自动化 Director、自动最优剪辑或新runtime pipeline。
Timeline resolving、P4混音、HyperFrames导出与render activation 使用既有canonical owners。

必须人工正常速度听最终MP4，确认撞击音色/响度、环境循环是否可感、有没有多余人声，
并做整体剧情的 human Final Acceptance；本环境无法代签。
视频分析转写对非对白底噪给出不稳定估计，不能用转写或无issues证明听感。
本次没有提交下一剧情 Shot，没有新的 image/video/voice/SFX generation 或 Provider media POST。
Kimi mapping 属于独立受管推理调用，不是媒体生成。

AOCI维护探测因现有10个managed paths认知待对齐而停止，未扩展任务修改无关认知；
不宣称索引已全面对齐。RAG只用于advisory发现，不作为本次验收来源；
记录后没有额外重建全局RAG。所有local evidence需与MP4共同保留，单独Git记录不携带媒体bytes。
