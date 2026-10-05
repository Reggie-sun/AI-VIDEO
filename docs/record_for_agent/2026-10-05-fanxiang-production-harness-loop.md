---
record_kind: media_experiment
topic_id: fanxiang-v36-v37-production-loop
learning_eligibility: eligible
evidence_index_version: "1"
---

# Fanxiang Production Harness Loop Record

Date: 2026-10-05

## Current Status

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
