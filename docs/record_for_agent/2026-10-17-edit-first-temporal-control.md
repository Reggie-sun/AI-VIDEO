---
record_kind: architecture_implementation
topic_id: edit-first-temporal-control
learning_eligibility: ineligible
---

# Edit-First Temporal Control Record

Date: 2026-10-17

## Purpose

记录通用制作路径中“先评估既有素材能否经剪辑满足目标，再决定是否生成”的实现与当前本地证据。目标是把可编辑的时间偏差交给既有 Production planning 和唯一 `ResolvedTimeline`，避免把编辑问题直接送回 Provider。

本记录对应 [spec](../superpowers/specs/2026-10-17-edit-first-temporal-control.md)、[plan](../superpowers/plans/2026-10-17-edit-first-temporal-control.md) 与 [workflow owner](../canvas-production-harness.md#edit-first-temporal-control)。Spec/Plan 说明完整契约；本文只固定本次实现与开发预览的实证边界。

## Current Result

带原声剪辑版`173cd95b4629c4d758ccf40d7725870cc8f3cca18685695fe4e0d2ef8f2ca5c9`已获用户对
动作、最后转向和声音的完整1×听看确认：“完整听看后可以接受”。该人工层证据取代此前新片human
NOT_EVALUATED，见下文`Native Audio Follow-Up`；原始生成源的失败、消费及STOP保持。
源码`c19fa31`已修复NA-001/NA-002及round4发现的NA-003，适用Harness和必需复审已完成，已push main并核验远端SHA；development preview未取得
Production qualification或activation，不能把单源人工接受外推为跨镜、跨故事或通用模型质量。

## Implemented Direction

默认 `production-strategy/2` 在 qualified reuse 下优先评估生成次数更少、仅缺用途证据的源候选；显式 `/1` 保留原兼容语义。`video-time-map/1` 使用相对源 trim 的递增整数帧锚点，`CompositionSpec/ResolvedTimeline 2.3` 独占 source trim、output frame/sample 与分段解析。非一比一段按每个输出帧的 floor source coordinate 展开为一帧 source span，由既有 HyperFrames 0.7.103 逐段读取 1x 窗口；实现不依赖该导出忽略的 `data-playback-rate`，也未增加 renderer、timeline、状态库或依赖。

首个运行边界为同帧率、显式静音的视觉剪辑。现有源音频、同 Shot/全局音轨与字幕、同 Shot voice source 没有可用的对应 sample map 时必须明确拒绝；独立其他 Shot 音频与最终验收仍由原 P4/QA owner 管理。减速重复采样源帧，不做光流补帧。用途证据绑定 exact map 和源身份；未变速的 PASS 不沿用为变速用途 PASS。已失败素材只经原 `bootstrap_repair_input` 路径进入 `development_preview`，资产保持 UNBOUND、qualification 为 NOT_EVALUATED，不能 activation；不改变原失败、rejection、STOP 或源 Production lifecycle。

现有普通 qualified 视频也由同一上层策略评估是否剪辑或变速；没有故事专属分支。完整字段、失败路径与 authoring 限制见 workflow、spec 和 plan。

## Retained Source And Preview

本地预览使用既有几何人物 R2V 源 MP4 `0a7e9072f5bbce23f78ead55dc6ebefb477ded1d6e9518cb6a42ce19f5049bc9`，attempt `canvas-50d9e7ad76b42064d3c5a34647c05feacd271dda`。源生成结果原 QA 保持 **0 PASS / 2 FAIL / 5 NOT_EVALUATED**，候选已 abandon。早先唯一获准的 robot Provider pilot 已消费 1 次；此次编辑新增 Provider POST 为 0，不能把整个窗口描述为零调用。

`runs/edit-first-temporal-control-20261017-001/robot-retimed-preview/render-002/verified.mp4` 的 SHA-256 为 `8ca3e974b686711a970698f802a0f40dc2a564f3fe72d0a5db824719de15962b`。输出为 1344×768（7:4）、24fps、120 帧 / 5 秒、H.264、无音轨。使用的映射为 `(0,0) → (66,48) → (96,84) → (120,120)`，`audio_policy=mute`。原 robot Manifest SHA-256 `f46f55ea6779a6222ade1670a74aef6a06d1e17b4bd5b0583134d23ce6f6a36e` 与《界蚀》原始 Manifest SHA-256 `1ece69263041eb06d345e5673f010a2b209e67a1e2fea82c2002e12a2b982e60` 均保持不变；预览记录确认 `original_state_unchanged=true`。

| Proof layer | Evidence | Result and limit |
| --- | --- | --- |
| Renderer frame identity | `runs/edit-first-temporal-control-20261017-001/renderer-fixture/sampled-011/frame-identity-comparison.json` | 11 个选定输出帧均匹配预期 source frame；测试覆盖 2x、0.5x 与 1x 分段。证明该 pinned renderer 实际消费正确源帧，不证明画面质量。 |
| Historical renderer counterexample | `runs/edit-first-temporal-control-20261017-001/renderer-fixture/run-007/frame-identity-comparison-posthoc.json` | 旧 `data-playback-rate` 属性路径发生帧错配，`all_expected_frames_match=false`；保留为负面 proof，不用后续结果覆盖。 |
| Edited media observation | `runs/edit-first-temporal-control-20261017-001/robot-retimed-preview/observations.json` | project-local `video-analysis` MCP 加 Agent 抽查：2.0s 样帧手臂垂下、3.5s 样帧左臂水平，两项仅对编辑后的离散时点为 PASS。 |
| Other media requirements | 同上 | 转身幅度与整段动作自然度、原音频保留、Production qualification、人工完整 1x 观看均为 NOT_EVALUATED。此 preview 不构成完整 QA 或交付。 |

原源的失败 required findings、rejection、消费和 STOP 均未改写。编辑预览不是新生成实验，也不与其源素材构成独立样本。

## Engineering Verification Status

此前静音实现的已发布源码为 `43b58d62e55fbcba8021002667f3042be584a6c2`，tree `138cb4ec4af83a61486edb1c2eec01d3c5f21583`，remote main SHA 已核验一致。此前实现提交 `1b55a25783ca9cb7831e504cb912605bf122fbd1`，whitespace 修复 `1c04a57fa8b70cb8b53f9214290bc79a46e779fb`，旧格式 trim 兼容修复 `84706114beb93fa4ea3cfcd0917755438106ac54`；该阶段工程 Harness 与必需复审已完成，媒体质量和人工验收不由源码发布代替。

| Scope | Receipt and proof | Result |
| --- | --- | --- |
| `3da65f0..1c04a57` | `.agent/harness/runs/edit-first-temporal-control-20261017-r2/receipt.json`；`runs/edit-first-temporal-control-20261017-001/harness-r2-source-verification.json` | 22 selected，21 PASS / 1 covered SKIP，无 fallback；Architecture 0 findings，Production contract 4101 PASS / 4 SKIP、Canvas workflow 278 PASS；integrity/freshness/complete_completion_proof 在 exact `1c04a57` 快照核验通过。 |
| `1c04a57..8470611` | `.agent/harness/runs/edit-first-temporal-control-20261017-r3/receipt.json`；`runs/edit-first-temporal-control-20261017-001/harness-r3-source-verification.json` | 7/7 PASS；composition/audio 1024 PASS / 4 SKIP；Architecture 0 findings，integrity/freshness/complete_completion_proof 在 exact `8470611` 核验通过。 |
| `8470611..43b58d6` | `.agent/harness/runs/edit-first-temporal-control-20261017-r4/receipt.json`；`runs/edit-first-temporal-control-20261017-001/harness-r4-source-verification.json` | 14/14 PASS，无 fallback；Architecture 0 findings；generation feedback 523 PASS / 1 SKIP、voice routing 47 PASS、strategy 75 PASS、Shot router 372 PASS、composition/audio 1026 PASS / 4 SKIP、Canvas workflow 290 PASS；integrity/freshness/complete_completion_proof 在 exact `43b58d6` 核验通过。 |
| Actual pinned export | `runs/edit-first-temporal-control-20261017-001/renderer-fixture/sampled-011/`；`tests/test_production_video_retime_render.py` opt-in | 1 PASS；11/11 真实输出帧匹配，namespace 仅 `lo`。普通 Harness 跳过此 opt-in，不将默认 SKIP 当作实际执行。 |

Harness r1 仅因新测试文件末尾额外空行失败，失败 receipt 保留。增量只修复旧 `ResolvedVisualSpan.trim_duration_frames=None` 被误拒绝的问题；新增边界测试修复前 1 失败 / 2 通过，修复后 retime/Canvas 相关 25 项通过。实际 renderer 及 robot 预览使用显式整数 trim，后续兼容修复不改变这些 span 的行为；4101 项完整契约证明属于 `1c04a57`，不冒称全部在新候选重复执行。

Risk Gate 为 `NATIVE_REVIEW_REQUIRED`：已失败媒体可经 sealed capture 进入 composition，跨 Registry、exact target/use 与 activation 的 join/alias 若缺保护，可能把已知失败提升为 Production；fixture 覆盖之外仍需独立检查该语义边界。round 1 由 read-only `/root/edit_first_review`、实际 profile `reviewer_xhigh` 审查 `8470611`，返回两项 `blocking_candidate`，Parent 均裁决 `CONFIRMED`。修复在 `43b58d6`，公开入口及相关 focused suite 为 **56 PASS**，applicable Harness 已完成；同一 reviewer 的 round 2 full re-review finding set 为空。Parent 结合当前源码、公开入口测试及 Harness 关闭两项问题，没有 unresolved blocker。轮次及裁决证据为 `runs/edit-first-temporal-control-20261017-001/review-round-1.json`、`review-round-2.json`：

- `EF-001`：Canvas 通过 `model_copy` 追加 P4 后没有重新校验完整 CompositionSpec，同镜未映射声音可漏过 muted 约束。公开入口有效音轨用例复现，后续修复同时封住全局音轨/字幕，保留其他镜头独立 P4 的正常用途。
- `EF-002`：父镜被替换为 production components 后，position 继续寻找旧父镜，导致材料化后的 qualified reuse/edit 无法接回标准 compose/render 或推进后续 occurrence。修复从已验证 lineage 重开 source-backed family，接回公开 compose/render，并从实际首末子镜的 ResolvedTimeline 提取外部切点；正反顺序、普通镜头混合、P4、pending/unqualified/unknown 均有相关用例。首版不自动续接 `source=None` 动态生成组件，仍归既有 generation owner；旧无 ProductionIntent 的 Canvas 路径保持可用。

## Native Audio Follow-Up

用户同意继续完善当前剪辑版后，核对原sealed authoring确认`audio_need=required`、`muted=false`；
先前静音版没有满足原声要求。审计确认现有`register_native_audio`只接受qualified source，
不能用它把failed source洗成另一份合格WAV。必要共享能力见
[native audio spec](../superpowers/specs/2026-10-17-native-audio-retime.md)和
[plan](../superpowers/plans/2026-10-17-native-audio-retime.md)。

`video-time-map/2`显式`retime_preserve_pitch`经CompositionSpec/ResolvedTimeline2.4把同一VIDEO的
原声解析为内部`native_video` P4 span。显式FFmpeg/ffprobe沿exact snapshot做分段变速，原mixer及
HyperFrames输出；source receipt包含map、PCM、工具及逐段样本修正证明，没有direct mux或第二timeline。
晚到音轨保留原PTS空白；负时钟拒绝。为避免三个既有大模块增长，完整mixer、audio binding和
source/timeline track validation分别迁到既有职责helper，原public imports及旧字节兼容保留。
failed-source的新A/V用途由独立`development-repair-input/3`封存；旧静音capture不能授权它，
资产仍UNBOUND/NOT_EVALUATED、timeline为development_preview、无activation。

实际新片为`runs/edit-first-temporal-control-20261017-001/robot-audiovisual-followup-001/av-candidate-001/render-001/verified.mp4`，
SHA-256 `173cd95b4629c4d758ccf40d7725870cc8f3cca18685695fe4e0d2ef8f2ca5c9`，698830 bytes，
1344×768（7:4）、24fps、120帧/5秒视频；MP4 container5.022秒，含48kHz stereo AAC。
采用窗仍source0–5秒，整数锚点与前版一致，未使用5秒以后的源尾帧。
P4为240000 samples；输出AAC解码240640 samples，其中encoder padding640、priming1024按既有P4规则核验，
不把编码padding写成内容时长或音画主观验收。

| Proof | Exact evidence | Result and limit |
| --- | --- | --- |
| Actual A/V export | `robot-audiovisual-followup-001/av-candidate-001/render-evidence.json`（相对本run根） | pinned HyperFrames lint/check及实际导出通过；同源原声沿map进入P4，不证明听音质量。 |
| Visual preservation | `robot-audiovisual-followup-001/visual-regression.json` | 新旧全部120帧decoded hash一致，0 mismatch；补原声没有改变旧静音版任何解码画面。 |
| Sample accounting | 新片render evidence的`native_audio_derivations` | 输入/输出均240000 samples；三段分别trim51、pad947、pad808，均低于每段2000上界，修正及工具hash有据。 |
| Explicit media observation | `robot-audiovisual-followup-001/observations.json`、`observed-frames/index.json`及`av-frame048/084/119.png` | project-local video-analysis显式关闭转写/remote audio；保留20个实际时间戳及精确frame48/84/119。首次120帧调用在4.98s越过视频末帧而失败，改用有效区间补证；未把失败调用写成PASS。 |
| Audio offset regression | `tests/test_hyperframes_native_audio_retime.py` | 真实本地FFmpeg fixture证明起始0.978s的音轨保留46944 samples前置空白；修复前`first_pts=0`错误提前声音。是工程证据，不是模型质量实验。 |
| Human full-speed review | `robot-audiovisual-followup-001/human-review-001.json` | 用户对exact新片回复“完整听看后可以接受”，问题明确覆盖1×完整听看、动作、最后转向和声音。人工观感为ACCEPTABLE；不改写源失败或自动赋予Production资格。 |
| Model audio observation | `robot-audiovisual-followup-001/review-av.html`及此前工具结果 | 当前模型音频input返回unsupported，未取得模型独立听音或语义分析；用户确认属于独立列明的human层，不能改称模型听过。 |

本次原声完善新增Provider POST为0。源robot与《界蚀》Manifest hashes、源失败QA、rejection及消费仍保持；
不把同一素材的静音/有声重编码算成独立模型样本。24/30fps、非零trim、不同map重复使用同一VIDEO、
缺轨/错源/旧schema/错误proof/额外P4/activation拒绝均有工程用例。

首个源码提交为`4c17dff064943ad8b246be3063cb9e7cd1887d85`，tree`15dbdbaceb6f391a7846e5adbb906d9b3eee0251`。
公开导入用例在该点RED：普通imported VIDEO的`canvas-local-video-measurement:`标识被当成generated
probe hash读取，两项用例均在compose失败。修复`954afc23a8580a91ef7d4b92314e1b81ca4ee293`，
tree`a9c55a496e61c89abf65213cca0cd0b5301d40a2`，只补真实来源分支；repair detection先于普通IMPORTED，
generated/captured仍重开exact probe。普通导入的音轨存在性/唯一性在materializer读取held bytes时验证，
compose成功不证明已有声音。新增标准inspect/author/bootstrap/load/compose/materialize用例覆盖
同一视频不同map复用、缺轨/双轨失败和capture v2/v3边界，focused组合31 PASS，Manifest不变。

| Native scope | Exact receipt and saved source proof | Result |
| --- | --- | --- |
| `1da4caa..4c17dff` | `.agent/harness/runs/native-audio-retime-20261017-r1/receipt.json`；followup根`harness-r1-source-verification.json` | 19 PASS / 1 covered SKIP，无fallback；Architecture 0 findings，Production contract4110 PASS/4 SKIP、Canvas290 PASS、原声专项26 PASS。完整性/freshness/complete_completion_proof在exact4c17dff核验通过后才改源码。 |
| `4c17dff..954afc2` | `.agent/harness/runs/native-audio-retime-20261017-r2/receipt.json`；followup根`harness-r2-source-verification.json` | 10/10 PASS，无fallback；Architecture 0 findings、composition/audio1026 PASS/4 SKIP、原声专项31 PASS，完整性/freshness/complete_completion_proof在exact954afc2核验通过。 |
| `954afc2..69ae168` | `.agent/harness/runs/native-audio-retime-20261018-r3/receipt.json`；followup根`harness-r3-source-verification.json` | 11/11 PASS，无fallback；Architecture 0 findings、原声专项36 PASS，完整性/freshness/complete_completion_proof在exact69ae168核验通过。 |
| `69ae168..c19fa31` | `.agent/harness/runs/native-audio-retime-20261018-r4/receipt.json`；followup根`harness-r4-source-verification.json` | 8/8 PASS，无fallback；Architecture 0 findings、composition/audio1026 PASS/4 SKIP、原声专项48 PASS，完整性/freshness/complete_completion_proof在exactc19fa31核验通过。 |

round3由read-only `/root/native_audio_final_review`、实际profile `reviewer_xhigh`审查exact954afc2，
返回NA-001与NA-002两个blocking_candidate；Parent均CONFIRMED。前者公开render先写attempt再拒绝
缺轨/双轨，后者44.1kHz/24fps后续Shot相对取整少一个sample；新增公开用例均已复现。
修复提交`69ae1689e59537df9067c66ab99b59630092729e`（tree`5cee502a5ed28fff6946811c2ebac1972aa49a52`）：
新render在begin前共享no-follow/hash snapshot与held-fd stream检查，begin后materializer重读验证；
已有attempt跳过新探测，由原begin/replay独占裁决。公开service.render的缺轨/双轨用例RED2→GREEN，
另有native失败attempt replay不重复probe、不改Manifest的回归。全局sample修复直接消费已有
shot_start_frames；44.1kHz/24fps两项resolver用例RED2→GREEN，全契约11 PASS。
相关focused组合39 PASS；HFA effective LOC为修复前2408、修复后2399。适用Harness已完成，
round4完整复审发现NA-003，其余两项修复路径未再报告finding。保留已执行四轮历史及上述fix证据。
证据为run根`review-round-3.json`及followup根`review-extension-round-4.json`。
round4证据为run根`review-round-4.json`。NA-003为合法frame倍率49→490在44.1kHz下解析成
90037→900375 samples，sample层重复的严格0.1检查误拒该量化结果；Parent CONFIRMED并调查。
修复`c19fa31e8b53b82125cd4902f3c15b4db63b1402`（tree`ace353b38034aee50019f632b5a6f535305f3b8d`）
保留正整数校验、factor分解及所有DSP/尾部修正逻辑。每轴floor差误差在(-1,1)，故sample有限包络为
`10*S+10>=O`和`S<=5*O+5`，真实包络外仍拒绝。公开resolver→materializer与helper组合44 PASS，
覆盖两端、非零trim/后续Shot相位，以及实际sample比值略高于5但合法的frame map。

该0.1× tone fixture随后真实atempo输出891408、目标900375，短8967超过1838上限，因此按原guard拒绝；
这是有界DSP处理失败，不能为其放宽上限、改factor算法、静音或自动生成。5×上端另例55125→11025
实际处理11326、裁剪301，在原上限内成功。其他factor顺序的本地探查未采纳，不把单例升级为0.1×全局不支持。
Parent据此仅为局部量化修复增加同profile targeted round5，见followup根`review-extension-round-5.json`；
不重置四轮历史，不自动增加第六轮。适用Harness完成后，同一read-only reviewer_xhigh对exactc19fa31
执行round5 targeted review，finding set为空；Parent结合数学边界、公开用例和实际DSP结果关闭NA-003。
NA-001/NA-002由69ae168修复、相关公开回归及Harness与round4完整复审对应关闭；无unresolved blocker。
完整轮次和Parent裁决为run根`review-round-3.json`、`review-round-4.json`、`review-round-5.json`，
不把局部round5说成重审所有旧代码，也不把reviewer结果当媒体或人工验收。
实际robot导出走capture v3且为48kHz/24fps；后续普通import分支和小数边界修复不改变该
已执行分支，v2/v3分支顺序亦有可执行回归，因此没有为该修复重复渲染或生成。
focused集成首轮696 PASS/3 SKIP/1 FAIL，唯一失败为旧AudioKind枚举预期；补齐内部native类别映射后
相关10项PASS。此前作者/公开入口及P4/admission组合158项PASS。当前owned paths的Ruff delta为
25条既有诊断、0新增、0移除，未声称全仓Ruff clean。

## Assessment And Remaining Limits

当前有据的结论是：ResolvedTimeline 的确定性整数映射可在 pinned HyperFrames 导出中选到预期源帧；同一既有 robot 视频已得到静音及保留同源原声的本地开发预览，在 2.0s 与 3.5s 样帧满足对应的局部姿势检查。用户随后对带原声exact新片的完整1×动作、最后转向及声音确认可以接受。这是该剪辑版的人工观感证据，不证明原 H3 输出未经编辑即满足动作时点，也不证明其他来源、连续镜、完整故事或通用模型质量。

该开发预览没有 Production qualification，未 activation 或进入Production采用状态；人工观感已确认，完整canonical QA状态并未因此自动改写。独立的历史 H3 三镜案例曾因 retime 减慢/冻结步态并迫使下一镜重启而拒绝该方案（[历史记录](../../runs/t8-h3-seedance-3shot-continuity-20260822-v8/SUMMARY.md)）；本次单源结果不能推翻该反例，其他项目变速后仍须核验步态、镜间衔接和所有原已满足要求。首版无source-audio sample mapping的限制已由上述2.4显式同源路线部分取代，额外audio/caption/voice无对应映射仍拒绝。未知项不得由技术帧匹配、局部分析或本片接受外推。

## Learning Eligibility

按 `distill-ai-video-learning` 完成 automatic evaluation：`no_candidate`，不创建占位 claim。`learning_eligibility: ineligible`；这是确定性工程实现及单一来源的编辑预览，不是独立或重复的模型质量实验。11 个 renderer 帧检查和两个观察时点不能拆成多条独立模型质量证据。相关 experience 检索已使用已有 stale-last-good 结果并核对 exact source；本 topic 的既有 learning claims 无匹配，历史 retime 反例未被覆盖或升级为新结论。工程合同按本任务明确授权实现，不标记任何实验 Learning Claim 为 ADOPTED，不刷新 RAG。

原声follow-up及用户确认后重复评估仍为`no_candidate`：静音/有声版和该人工确认属于同一源链；新增合成音调、不同tempo和音轨offset
对照只证明工程处理，不证明模型质量或跨故事制作规律。检索到的native-dialogue字幕claim不适用本片，无需改写或采纳。

## Publication And Retrieval State

静音阶段源码`43b58d6`及记录`1da4caa`是此前已发布checkpoint，历史docs-only receipt为
`.agent/harness/runs/edit-first-temporal-control-record-20261017-r1/receipt.json`。
原声及边界修复源码最终为`c19fa31e8b53b82125cd4902f3c15b4db63b1402`，tree
`ace353b38034aee50019f632b5a6f535305f3b8d`；2026-10-18已push main，并经`git ls-remote`
核验远端exact SHA一致。记录收尾只更新本主记录和原robot记录的supersession，适用docs-only receipt为
`.agent/harness/runs/native-audio-retime-record-20261018-r1/receipt.json`；文档证明不替代上述各源码快照证明。
最终文档提交及远端SHA由Git与完成回报核验，不在本文自嵌包含自身的commit hash。

本记录只保存于 repository 文档，不刷新 RAG index。此次剪辑修复未进行新的媒体 Provider 调用或媒体上传；开发预览使用既有本地源文件，源 Production Manifest 未变且没有 activation 或 adoption。已有 foreign staged/dirty 文件及其 index patch 经 hash 核对保持不变。

用户human确认、当前三份Manifest未变及未激活状态分别见followup根`human-review-001.json`和
`completion-state-verification.json`；后者经standard loader重开，完成前又逐字节核对三份Manifest hashes。
模型独立听音仍未取得；这不撤销已取得的用户1×完整听看确认。跨项目质量与完整故事未因此验证。
