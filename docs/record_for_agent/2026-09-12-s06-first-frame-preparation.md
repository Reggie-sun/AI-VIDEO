---
record_kind: session_summary
topic_id: jieshi-s06-first-frame-preparation
learning_eligibility: ineligible
---

# S06 First-Frame Preparation

## Audiovisual Reassessment Proposal

用户在第三次失败后的“可以”授权重新评估声画制作方案。本轮为只读能力核对与此记录更新，没有新Provider调用、音频/视频生成、项目state写入或runtime实现。

建议待明确批准的S06路线：视频只生成人物动作，`native_audio=false`；画面继续使用已批准首帧、原6秒机位和人物反应。广播、列车/通风环境声以及精确屏幕文字由独立P4 tracks/layer制作，最终片仍有声音。原生声音偏好在S06上改为显式独立音频，不追改三次旧请求/QA/失败证据。站名段“下一站，临江路。”只制作一份、在0秒和2秒复用同一音频内容，第三段“下一站……林砚。”在4.3秒进入，尾部短电流失真；保持原1.6/3.6/5.8秒窗口。不能截断发音来挤入窗口，实测不合适仍须调整制作并重新验收。屏幕仅显示“下一站：临江路”，不随第三段广播变成人名。最终timing仍由 `ResolvedTimeline` 独占。

已排除当前可直接执行“原生环境声＋独立广播”的假设：当前S06 Manifest2.7/r40，三次attempt均FAILED、paid ACCEPTED；`generated_video_audio.py`要求已结算来源、仅允许DIALOGUE/NARRATION，并将目标限制为Manifest2.0–2.2/Registry2.1，不能为本项目登记AMBIENCE。P4能够消费已登记音轨，但本S06没有activated visual，MiniMax Speech batch也只创建独立测试项目，没有当前S06的generated-voice登记/组合handoff。国内凭证未在本轮复查；最近国内接入记录称未配置、无live WAV，不能描述为当前已可用。

已有 `docs/superpowers/specs/2026-09-12-ai-video-voice-routing-design.md` 仍为 `proposed/not_started`，其SEPARATE明确要求首版视频`native_audio=false`，不支持上述混合路线。下一步若用户批准，需要先实施该路线所选项目布局的ledger/lifecycle、exact generated-voice registration和P4 handoff（尤其VR-13），完成测试与review，再做有界真实声画验证。此次“可以”不是对该新增runtime slice、切换音频路线或新Provider调用的授权；不编辑其他会话拥有的spec/源码。

Evidence：分镜Audio Production Policy与S06卡、`docs/generated-video-audio.md`、`docs/minimax-speech.md`、国内接入record及现有Voice Routing spec；native `code_mapper`只读核对了audio derivation/CompositionSpec/HyperFrames限制。Agent Memory查询返回library-incompatible exit3，按Skill未重试，判断来自当前文件。文档contract和本文件diff检查通过；只更新本记录，无fresh exact Harness receipt。按record/learning流程评估为`recorded/no_candidate`，此次没有新增实验或可采用的能力证明。

## Attempt03 Continuation Result

用户明确“继续修复”，追加一次 S06 attempt03。对 attempt02 的唯一语义变化为 `subject_action.progression`：移除视觉动作字段中的广播台词复述，仅描述林砚看屏幕、释然消失和末尾移开视线。原 `dialogue_intent` 三段台词/时窗、上轮黑屏材质描述、QA、首帧、Vidu Q3 Pro、6秒1080p/native audio和 seed `1439830583` 全部保留。假设是将视觉动作和听觉台词分开可减少屏幕文字，不是已经验证的因果结论。

第三版仍 **FAIL**：exact MP4 为 `runs/jieshi-e01-i2v-20260907-attempt10/production-s06-v1/state/video-generation/fetch/files/32d968767180f2d94fa16843213e9cd57f47e76c3f5f8b8af9f6343927c574ec.mp4`，SHA-256同文件名，5,166,335 bytes；6.042秒、1080×1920、24fps、145帧、AAC 48kHz stereo。MCP在1.5和4.5秒的帧中发现白色报站/点名文字；0/3/6秒留白不能抵消期间的明确违规。Whisper small仍只识别两段（0–2.08秒站名、2.08–4.4秒点名），不能验证要求的三次完整广播。完整声画decode exit0，mean -22.0dB / peak -3.7dB仅为技术证据。其余需正常速度整体声画人审的要求继续 `NOT_EVALUATED`，holistic verdict `UNDECIDED`；不 activation、不进入下一 Shot、不宣称完整成片或修复成功。

保持同一项目及 task，旧两次失败与 reservations未重置；`budget → start → quota → execute` 将内部operator总上限6M→9M microunits、同task submit ceiling2→3。唯一新POST在18:59:29 UTC返回200，18:59:44 acceptance持久化，19:01:06 succeeded，19:02:12 fetch。本轮新增一次、累计3/3已用完。编译body SHA `1c704cbad112a6373dc0af34acfcb73cda2d2d1a37873e801f060aceaceb83ce`，binding `6bfe34f36d7edbe2b110038ced4de7b9d71044089108684c2244dd277b6fc548`。未查询价格；上限不是实际账单。

Evidence保存在 `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s06-v3/`：authorization、compiled comparison、binding、preview、review、budget/quota、live events、MCP probe/review/frame metadata/transcript、audio decode及 `s06-attempt03-post-media-gate.json`。独立 `reviewer_xhigh` 为 `accept with concerns`，只确认执行约束；本轮22项guard/Vidu prompt/runtime boundary tests通过，strict current binding和单字段差异验证通过，S03/S04/S05 Manifest实测hash未变。无产品源码改动；policy audit仍被相同3条已有unmapped paths阻断，无fresh exact Harness receipt。

`review_attempt03.py` 已经真实MCP桥接、`ControlledPresentationVerifier` 与 `/2` evaluator持久化新exact证据，再由 `abandon_video_generation()` 关闭第三版 mixed failure；结尾standard loader重开通过，fetch和paid state保留。诊断为 `EVIDENCE_GAP + QUALITY_FAILURE`，失败项 `s06-no-generated-text`；没有把其他缺证据项目改为PASS。

按 `record-ai-video-session` 更新本记录并评估 `distill-ai-video-learning`：`no_candidate`，不将两个提示词修复均失败外推为模型必然失败。已重开现有 `vidu-s01-native-dialogue-burned-captions` pending claim，它仍未采用且明确不覆盖其他镜头；本轮不重复创建同一“禁止文字不能视为保证”的候选，也不擅自扩大其已封存范围。下一方向应重新评估声画制作方案，不能将本次失败视为第四次付费调用授权。

## Attempt02 Continuation Result

用户“jixu继续”按前文失败上下文授权追加一次 S06 修复。保持原 task `jieshi-s06-production-20260912`、同一首帧、`viduq3-pro`、6秒1080p、native audio、seed `1439830583` 与完整 QA。唯一创作变量为 `visual_treatment.material_treatment`：强化屏幕全程纯黑关闭、广播独立于屏幕的描述；三次 PA 的原文、时窗和人物反应均未改。Provider profile 仅按原 operator upper bound 续期，未查询价格或宣称实际账单。

结果仍 **FAIL**。第二版 exact MP4 为 `runs/jieshi-e01-i2v-20260907-attempt10/production-s06-v1/state/video-generation/fetch/files/d97cd757a99ea5932ff8f0a4aa87e342b8d5cbff1ac15ccf60b2f34f428adb25.mp4`，SHA-256 同文件名，4,505,874 bytes；6.042秒、1080×1920、24fps、145帧、AAC 48kHz stereo。显式 project-local MCP 抽帧在1.5/3/4.5/6秒均显示黄色生成文字和错误站名形状，留白修复假设被当前样本否定；不外推为整个模型不具备能力。Whisper small 仅识别两段：0–2.36秒站名、3–5.42秒点名；三次完整报站仍 `NOT_EVALUATED`。完整声画 decode exit0，音频 mean -24.9dB / peak -5.1dB，只证明可解码及非零音量，不证明台词、音色或节奏正确。

先通过 `/2` evaluator + `ControlledPresentationVerifier` + 真实 MCP bridge，为 attempt01 持久化屏幕 FAIL 和其他 human `NOT_EVALUATED`，再由 `abandon_video_generation()` 保留 mixed failure 关闭。随后仅发布新 generation target，沿完整 history/baseline/intervention 经 Router 选择一次生成。按 `budget → start → quota → execute` 顺序，既有 committer 保留旧 reservation，将内部预算上限3M→6M microunits、同 task 次数1→2。18:47:37 UTC 接受唯一新 POST，18:49:06 succeeded，18:49:23 fetch；未重复 submit、未重建项目或清零历史。attempt02 的 exact mixed failure 也已通过同一桥接与 abandonment owner 关闭；两版均保留，不 activation，不进入 S07，不宣称 P4/Final Acceptance。当前总 submit2/2 已耗尽。

Evidence owner：`runs/jieshi-e01-i2v-20260907-attempt10/preparation-s06-v2/` 中的 `continuation-authorization.json`、`s06-compiled-comparison.json`、`s06-execution-binding.json`、`s06-live-events.jsonl`、`s06-attempt02-post-media-gate.json`、`s06-attempt02-diagnosis.json` 与 MCP probe/review/frame metadata/transcript。`pre-submit-review.json` 记录 native `reviewer_xhigh` 的 `accept with concerns`；它验证提交约束，不证明媒体质量。

Verification：standard loader 与 current binding 校验通过；实测仅 material_treatment 改变，S03/S04/S05 Manifest hash 未变；59项 rejection/quota/execution/Vidu focused tests通过，另2项 runtime Skill boundary通过。文档 contract与 task diff检查通过；没有 fresh exact Harness receipt，policy audit 的3条既有 unmapped paths 仍未解决。未修改产品源码或其他 dirty work。按 `record-ai-video-session` 更新本 owner；自动 `distill-ai-video-learning` 为 `no_candidate`：本轮单一受控修复对不足以支持跨实验采用 claim，不新增 placeholder 或自动改变模型/策略。

## Superseding Generation Result

用户随后回复“可以”，批准本记录所述首帧用于 S06。已通过既有 Planner/Router/compiler、paid gates 与 canonical lifecycle，以 `viduq3-pro` I2V、6秒、1080p、`audio=true` 完成一次 submit 和一次 fetch；task ceiling1/used1。本节取代下文历史 checkpoint 的“尚未提交”和“待首帧确认”状态。

Exact MP4：`runs/jieshi-e01-i2v-20260907-attempt10/production-s06-v1/state/video-generation/fetch/files/62edbc87c2df450292832ce446dfa4e749c67cc908ffe43f7bd7576ffb5659cd.mp4`；SHA-256 同文件名，5,050,079 bytes。project-local `video-analysis` MCP probe 检出6.042秒、1080×1920、24fps、145帧、H264及AAC 48kHz stereo音轨。音轨存在不等于广播要求通过。

Post-media Gate **FAIL**：exact MP4 的 MCP 抽帧在3秒和6秒显示模型生成的屏幕文字；3秒另出现未要求的屏幕图形，违反 `s06-no-generated-text` 的干净屏幕要求。不是仅仅“精确文字尚待合成”，不能当作合格原始素材交付。Whisper base 与 small 均只转写出两段，未证实三次完整报站及指定时窗；同音转写差异本身不证明发音错误。其余需要连续正常速度声画人审的要求为 `NOT_EVALUATED`，holistic human verdict 为 `UNDECIDED`，不得以抽帧代替整体人审。下一 Shot 被阻断，未 activation、未 P4/Final Acceptance、未追加 submit。

Evidence 位于 `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s06-v1/`：`s06-task-authorization.json`、`s06-live-events.jsonl`、`fetch-dns-evidence.json`、`s06-attempt01-probe.json`、`s06-attempt01-review.json`、`s06-attempt01-frames.json`、两份 `s06-attempt01-transcript-*.json` 和 `s06-attempt01-post-media-gate.json`。Gate 绑定 QA hash `197b9ef7b9f6b8faeca91a384da4c9576d28953e6da28389ec7beb6df959a361`，并引用 S05 已接受的前序 Gate。下载沿用有界 GET-only 公开 DNS 解析，保留原 hostname、SNI 与 TLS 校验。

通过 standard loader 重开当前项目并校验 exact MP4 SHA；S03/S04/S05 Manifest 实测 hash 均未改变。准备时 focused tests 为106 passed（命令与 helper hashes 见 `s06-preparation-verification.json`，其中 `PREVIEW_READY_NO_SUBMIT` 是提交前历史快照）；native `reviewer_xhigh` pre-submit verdict 为 accept with concerns，未替代当前媒体 Gate。无产品 source change；无 fresh exact Harness closure，policy audit 仍受已有 unmapped paths 阻断。自动 `distill-ai-video-learning` 评估 `no_candidate`：单次失败样本不足以建立跨实验或 Provider-wide claim。已耗尽本次有限付费提交授权；进一步生成需要新增有界授权。

## Outcome

用户要求生成 S06，随后明确确认 S05“通过”。本轮保存 S05 exact raw human acceptance，完成 S06 新机位首帧候选；尚未导入 S06 图片或提交视频。

S06 为6秒“报站重复”：林砚放下左手看屏幕，前两次画外广播“下一站，临江路。”，第三次“下一站……林砚。”；笑意消失，末态视线滑向陈立。依创作包 Audio Production Policy，准备优先生成原生广播与环境声。逐字、同音色、时窗和表演仍需实际 MP4 验证，不以打开音轨代替。

## Evidence

- 使用 strict `load_production_project()` 重开 `production-s05-v1`，定位 approved registered S05 first-frame：`image-import-b3b83fba68d003a4374f8daaf482a5fad6cd9479356d8dbf29fa91061e8eda51`、SHA-256 `d3be37aed9166fa06b7df968c3f8ce76ad63d273feff4040131604b167c5c23f`；参考 Shot `jieshi-e01-S05` revision2、hash `a0a7774dac865ec314fc7a65413915da0b5fb9343c76771fd4c6f04c4d1f34af`。参考为 registered image，不是视频截图。
- 一次内置 `image_gen.imagegen` 编辑，用新机位显示林砚侧脸与门上电子屏。屏幕有意留白，遵守原分镜的精确文字独立图层路线；此候选不等于已完成“下一站：临江路”的成片屏幕效果。未声明该层已 materialize/render。
- Prompt、`source-reference.json`、`first-frame-result.json` 与 `s06-first-frame-candidate-v1.png` 保存于 `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s06-v1/`；result 记录实测 SHA/尺寸及三段广播窗口。无 Provider POST、ceiling1/used0。
- `retrieve-ai-video-memory` experience 查询返回 stale advisory fragments，未用历史结果授予当前质量 PASS。当前事实来自分镜、Audio Production Policy、exact S05 MP4 hash 与用户人审原话。

## Remaining Boundary

新 S06 PNG 仍需用户确认后才能满足 `HumanImageImportReceipt` 的 human approval/time ordering；S05 人审不自动覆盖之后才生成的图片。后续沿现有 Planner/Router/compiler/Provider seam 封装，不声称已运行 Router 或本轮已生成 S06 视频。

## Verification And Learning

已检查图片可读性、实测尺寸与 SHA、S05 exact MP4 和 source standard loader。无产品 source 改动；不声称 fresh Harness closure、音频或成片验收。按 `record-ai-video-session` 保存稳定准备 checkpoint；`distill-ai-video-learning` 评估 `no_candidate`：单张未获人审的候选不满足跨实验 claim 阈值，不创建 placeholder。保留其他 staged/dirty work。
