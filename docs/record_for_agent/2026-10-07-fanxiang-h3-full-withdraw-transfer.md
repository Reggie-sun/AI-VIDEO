---
record_kind: media_experiment
topic_id: fanxiang-v36-v37-production-loop
learning_eligibility: needs_identity
evidence_index_version: "1"
---

# Fanxiang H3 Full Withdrawal Transfer

Date: 2026-10-07

## Current Editorial Follow-up — 2026-10-07

按用户新指令只做一次局部节奏修订，**动作本身仍不成立，停止，不进入撞击声或混音阶段**。
这更新当前后期救援的结论，不取代下方真实H3 raw和原接镜的历史FAIL，也不是第二次生成实验。
未生成、未改白模、prompt或通用架构；未拼回旧撤退近景，未覆盖任何历史版本。

独立目录 `E = runs/fanxiang-h3-local-rhythm-20261007-011/`：

- `E/local-rhythm-silent-review.mp4`：完整无声待审对照，1344×768、24fps、385frames、
  16.041667秒、无音轨；SHA `159fa0a152fc376d9586f9d06b22c65bf5d7d442ffdf497cb36b4c45a98bae08`。
- `E/review.html` 同时保留新完整无声对照与原17秒有声FAIL版本入口。
- `E/retimed-contact-window.mp4`：84frames、3.500秒的独立后期衍生源，SHA
  `91577d60864feb313f93b88ebeef03b6f769272d66fa0af8c38af455cb7a77a0`；不是Provider新candidate。

24fps、zero-based half-open：原B03 `[0,287)` → 衍生源 `[0,84)` → 原B03空窗 `[348,362)`。
衍生源只跳过raw前两帧重复抬手；raw `[2,6)`原速保留挥击及首次接触，raw `[6,32)`的26帧
贴脸段选 `[6,12,18,24,30]`，将1.083333秒压为0.208333秒（窗口时长比5.2:1，段内选帧步长6）；
raw `[32,107)`完整原速保留后缩、头颈退窗及自然空窗。没有全片加速、冻结补时或插帧。
逐帧映射及原raw SHA见 `E/edit-brief.json`、`E/derived-source-provenance.json`。

仍由既有 `SourceUseEvidence / CompositionSpec / ResolvedTimeline / HyperFrames / ProductionStateCommitter`
组成独立诊断工程；当前SourceUse用途是检查这一个后期救援版本，不认证命中。原Production与
generation activation不动。`E/canonical-compose-binding.json`绑定canonical render和导出相同bytes。

exact衍生源及完整MP4均显式调用project-local `video-analysis` MCP probe/extract，整段decode无错。
实际Chrome无声1×播放完整16.041667秒至ended，385个连续capture、0播放器丢帧；Parent核对
`E/actual-1x-front-contact-sheet.jpg` 与 `E/actual-1x-full-join-sheet.jpg` 后裁决：
前接点重复抬手减轻，电脑键盘、头颈连续撤退和空窗结果可读，但约12.1–12.4秒仍托住下脸再
脱开，缺少短促命中后的即时后缩。压缩停留没有补出缺失的受力起点，整体视觉为FAIL。
具体裁决见 `E/review-decision.json`；播放成功及局部观察PASS不能替代完整动作验收。

视觉未成立，因此该次交付明确为**无声诊断版本**，没有继续处理撞击声或声音接缝。
原对白WAV及13.875秒保留版、13.375秒备选、旧撤退镜、四图与白模等11项source SHA复核不变，
见 `E/preserved-sources.json`。原raw与旧QA保持，`E/historical-failure-preservation.json`留存hash。
“兄弟们太正气”的声音反馈仍暂停待听辨；没有声音验收、封版或下一剧情单元放行。

自动learning evaluation仍为 `no_candidate`：本次剪辑是同一raw的派生proof layer，不增加独立
support，不建立“局部变速能救接触”或“H3不能迁移动作”的通用claim。
任务文件未改变公共代码，implementation required review不触发；受管Kimi仅审查封存的frame-map
算术和停止边界，不能推翻Parent对实际画面的FAIL。invocation
`9adb8113-f9ef-417f-890c-9ec7e052d389`，2 wire requests，terminal `PARSED`；receipt、report与
实际Read的SHA核验。Parent区分窗口总长比和选帧步长，确认f31属于有意抽帧；仅在
`E/frame-map-clarification.json`明确tuple第三项为duration，未改封存brief或任何媒体。
裁决见 `E/kimi-parent-adjudication.json`；没有采纳再加帧或再剪建议。媒体仅本地交付，不是发布。

本次记录时只读identity validator发现下方历史Evidence Index的proof_layer小写及跨artifact的
`SAME_EVIDENCE_NEW_PROOF_LAYER`不符合现有schema。保留旧实验、SHA与FAIL，不伪造相同artifact
或新增独立key；envelope明确降为 `needs_identity`，未把该索引用于learning admission。
详情见 `E/evidence-identity-validation.json`。该历史索引问题不改变实际视频审片结论。

## Outcome

本轮一次真实 `metaso_h3 / MiniMax-H3 / REFERENCE_TO_VIDEO` 已执行并fetch，实际候选与完整
接镜对照均交付。**动作迁移与前接点未通过；没有正式成片验收或自动重抽。**
白模可用于动作参考的判断保持，但不能据此声称H3已继承完整动作。

独立目录 `R = runs/fanxiang-h3-full-withdraw-transfer-20261007-010/`：

- `R/output.mp4`：原始候选，1344×768、24fps、107frames、4.458333秒；H264、AAC/32000Hz/stereo。
  SHA `5a306abdd6085629b11d1ec0d25be241bf4f9b851afe80044ccc1740ba563d24`。
- `R/h3-full-withdraw-join-review.mp4`：完整待审对照，408frames、视频17.000秒、容器17.022秒；
  H264、AAC/48000Hz/stereo。SHA `811c2d9a9caa1d63ed555f183d85172e59a23e5e767b9f013d00062a6b004eff`。
- `R/review.html`、`R/README.md`提供审片入口、输入职责、切点与剩余问题。

## Exact Inputs And Request

Video 1只使用009最终2.750秒、66frames的 `Video-1-full-withdraw-final.mp4`，
SHA `065dae8a24e57f3b61766b502401d82aa9d670109ce06fb0f8ec122d3954c4b2`。
四图的bytes、顺序及职责保持：小龙身份/黑衣、狗哥身份/长颈、黑色电脑QWERTY键盘、B03破窗与
场景外观。`R/reference-list.json`、`R/native-input-verification.json`逐项绑定实际native body。
15.291667秒预演接镜对照未作为模型输入；不使用旧v06预览请求或旧I2V许可。

Video 1负责运动、接触关系、即时受力方向、撤退节奏和固定室内侧机位；图片负责外观。
authoring取消另列数值动作时间表和Image 4宽景覆盖Video 1的指令。保留原参考速度，
完成退出后用空窗填余量，不继承灰模材质、简化人形或粗模穿插。

请求4秒/768P/adaptive/native audio/`context_ir=false`；4秒是当前接口最短输出时长，
与2.750秒参考输入长度区分。服务端实际返回4.458333秒，raw及原请求历史不回写、不强截断造证。
compiled prompt 3474字符，经原生grammar compile/resolve；实际body含4个`reference_image`和
1个`reference_video`，无`first_frame`。新请求fingerprint：
`a454c1832e07891bcd3d26edfed97e9dfc144264c89177053ff0709e5f0fec04`；
native body SHA `05343067825d075b0ef2a7948c6451bce56059f36976ecca593415fe5f4aa17d`。

## Authorization And Execution

当前用户明确要求一次真实H3验证并限定最多一个候选。按这次新指令封存accepted Provider/model/
inputs和1次提交，不复用旧授权、reservation或one-use permit。沿用operator上限每次
`2000000 microCNY`；不是官方报价，实际扣费未知。

经现有 `GenerationFeedbackOrchestrator.for_project → Planner/Readiness → Router →
MetasoH3VideoProvider → VideoGenerationService → ProductionStateCommitter` 准备、durable intent、
exact Paid Preview、Budget Guard/reservation、permit、submit/poll/fetch，没有直接POST旁路。
原历史14次physical submit及其known outcomes保持在predecessor ledgers，
本次独立任务最多新增1次；新task不是重置旧ledger，见`R/predecessor-history.json`。

实际physical H3 submits=1，单独reference uploads=0（参考bytes随混合body传入），
外部task `2107520933862739968`；POST 200、status succeeded、fetch完成、`FETCHED_UNACTIVATED`。
generation latency 37.439秒、total latency 44.796秒；fetch为同一task读取，不是第二次生成。
requested/native model均为`MiniMax-H3`；Provider内部实际backend未独立认证。
证据：`R/physical-submit-consumption.json`、`R/submission.json`、`R/fetch-receipt.json`、`R/terminal.json`。

## Complete Edit And Sound

24fps、zero-based half-open窗口：B03 `[0,287)` → 实际H3候选 `[0,107)` → B03空窗 `[348,362)`。
用全候选揭示迁移表现，不裁掉已知拖住接触来制造通过，也不拼回旧recoil掩盖问题。
既有 `SourceUseEvidence → CompositionSpec → ResolvedTimeline → HyperFrames0.7.103` 和唯一
committer完成独立diagnostic project；`R/canonical-compose-binding.json`证明导出bytes与canonical
output一致。SourceUse的PASS仅证明当前诊断素材窗口用途，明确保留raw动作FAIL，不认证正式命中。

前段直接复用已恢复的 `fanxiang-av-repair-20261006-002/main-native.wav`，原-3dB设置不变；
候选原生音轨在其视觉段原时序进入P4，后接B03空窗原声。无对白替换、循环、额外撞击SFX或
夸张遮掩。**未实际听辨**：声音音色、音量衔接、原生撞击同步均`NOT_EVALUATED`；
用户“兄弟们太正气”的反馈仍未解决。本轮不把波形/编码/轨道对齐当声音验收。

13.875秒基线、13.375秒备选、旧recoil、009最终Video 1及其对照、四图的SHA复核未变，
见`R/preserved-sources.json`。未覆盖原对白素材、历史candidate、旧QA或activation。
通用架构、Router、Provider源码均未修改；白模未继续打磨。

## Actual Media Review

两份exact MP4分别显式调用project-local `video-analysis` MCP probe/extract，完整decode通过。
实际Chrome 1×从头播放至ended：raw 106个capture/0播放器丢帧（probe为107frames，不把capture数
充作总帧数）；对照408capture/0丢帧。Parent查看实际连续接触帧、完整对照和精确前后切点，
见`R/actual-1x-contact-sheet.jpg`、`R/actual-1x-join-sheet.jpg`、`R/source-boundary-board.jpg`。
播放、metadata与MCP仅供裁决，不直接签发作品PASS。

逐项结果保存在`R/raw-post-media-gate.json`、`R/joined-post-media-gate.json`：

- **动作迁移FAIL**：raw约0.25–1.3秒／对照约12.208–13.258秒，键盘停贴下脸附近，形成拖住、
  托推的观感；短促可信命中、接触后立即受力的节奏没有被保留。
- **前接点FAIL**：对照约11.917–12.125秒，轴线和大致构图兼容，但手臂/键盘在接入时小幅回退后
  再推进，不能声称动作无缝匹配。
- 电脑键盘而非乐器、未继承灰模材质、头颈可见连续撤回、退出后保持空窗这些局部观察成立。
  后接点约16.417秒，是中景空窗到原空窗特写的明确景别切换，结果可读，不是逐像素匹配。
- exact人物identity、人类外观审美、声音听感仍`NOT_EVALUATED`；原成片`NOT_ACCEPTED`，
  不能进入下一剧情单元。本次单候选额度已用完，停止，未改prompt或提交第二次生成。

## Independent Text Audit And Learning

受管Kimi deep/max只读审查三份封存输入说明，invocation
`d7c18265-30f1-4c73-84f1-7aa7a3575858`、2 wire requests、terminal `PARSED`；
receipt/report SHA及实际Read源SHA核验，Parent裁决存于`R/kimi-parent-adjudication.json`。
未发现文本输入硬矛盾；背景潘子作为Image 4外观、locked camera默认enum的解释边界均保留。
这不是H3画面验收或implementation required review，不能推翻实际动作FAIL。

自动`distill-ai-video-learning`评估为`no_candidate`：本轮只有一个真实动作迁移attempt，
白模版本和接镜proof不形成独立support；与旧first-frame/full-video实验没有controlled arms，
seed不可控、输入也不同。不建立“H3不能继承动作”或“Blender一定能迁移”的通用claim，
不扩大已有仅适用于shot-local T2VA的learning范围。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| transfer-inputs | nonq0:metaso_h3:2107520933862739968:a454c1832e07891bcd3d26edfed97e9dfc144264c89177053ff0709e5f0fec04 | fanxiang-full-motion-transfer-010 | fanxiang-h3-full-withdraw-transfer-010-one-candidate | N/A | 05343067825d075b0ef2a7948c6451bce56059f36976ecca593415fe5f4aa17d | technical_input_binding | PASS | NONE | NEW_ATTEMPT | NONE | runs/fanxiang-h3-full-withdraw-transfer-20261007-010/native-input-verification.json |
| transfer-raw | nonq0:metaso_h3:2107520933862739968:a454c1832e07891bcd3d26edfed97e9dfc144264c89177053ff0709e5f0fec04 | fanxiang-full-motion-transfer-010 | fanxiang-h3-full-withdraw-transfer-010-one-candidate | N/A | 5a306abdd6085629b11d1ec0d25be241bf4f9b851afe80044ccc1740ba563d24 | parent_visual | FAIL | MOTION_TRANSFER_IMPACT_RHYTHM | SAME_EVIDENCE_NEW_PROOF_LAYER | transfer-inputs | runs/fanxiang-h3-full-withdraw-transfer-20261007-010/raw-post-media-gate.json |
| transfer-join | nonq0:metaso_h3:2107520933862739968:a454c1832e07891bcd3d26edfed97e9dfc144264c89177053ff0709e5f0fec04 | fanxiang-full-motion-transfer-010 | fanxiang-h3-full-withdraw-transfer-010-one-candidate | N/A | 811c2d9a9caa1d63ed555f183d85172e59a23e5e767b9f013d00062a6b004eff | parent_complete_join_visual | FAIL | FRONT_ACTION_MATCH | SAME_EVIDENCE_NEW_PROOF_LAYER | transfer-raw | runs/fanxiang-h3-full-withdraw-transfer-20261007-010/joined-post-media-gate.json |

## Checkpoint

媒体local-only，未发布。记录verification receipt owner：
`.agent/harness/runs/fanxiang-h3-full-withdraw-record-20261007/receipt.json`，
status/freshness以实际receipt核验为准，不认证媒体质量。
仅提交本记录及009记录的直接后续状态提示；其他窗口v06预览未执行，不把本次2.750秒请求
冒称该旧请求执行。`AGENTS.md`、`skills-lock.json`和安装中的四个Blender skill目录保留原ownership。
记录阶段不额外运行Provider、media、network或为了学习制造实验。
