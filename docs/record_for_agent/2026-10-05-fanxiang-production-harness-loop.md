---
record_kind: media_experiment
topic_id: fanxiang-v36-v37-production-loop
learning_eligibility: eligible
evidence_index_version: "1"
---

# Fanxiang Production Harness Loop Record

Date: 2026-10-05

## Current Status

### Subsequent Production Checkpoint

以下是继续制作后的当前状态；下文原始 NE 与 blocking observations 保留其历史时间边界。

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
| A2-RAW-QA | metaso-task:2107123515718922240 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-02 | N/A | bfa4216dfa8eb77dbd3f61a0b397c10ecb4c082b83c02ce03f1827f31a305fd7 | ANALYZER_QA | NOT_EVALUATED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | A2-FETCH | `B/sequence-A-take-02/diagnosis.json` |
| A2-USER-AUDIO | metaso-task:2107123515718922240 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-02 | N/A | bfa4216dfa8eb77dbd3f61a0b397c10ecb4c082b83c02ce03f1827f31a305fd7 | USER_AUDIO | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | A2-FETCH | `B/sequence-A-take-02/user-audio-feedback.json` |
| A2-ACTIVATION | metaso-task:2107123515718922240 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-02 | N/A | bfa4216dfa8eb77dbd3f61a0b397c10ecb4c082b83c02ce03f1827f31a305fd7 | CANONICAL_ACTIVATION | BLOCKED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | A2-FETCH | `B/sequence-A-take-02/activation-blocker.json` |
| A2-FINAL-QUALITY | metaso-task:2107123515718922240 | fanxiang-production-loop-20261005 | fanxiang-production-loop-A-take-02 | N/A | bfa4216dfa8eb77dbd3f61a0b397c10ecb4c082b83c02ce03f1827f31a305fd7 | HUMAN_FINAL_ACCEPTANCE | NOT_EVALUATED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | A2-FETCH | `B/final-output-contract.json` |
