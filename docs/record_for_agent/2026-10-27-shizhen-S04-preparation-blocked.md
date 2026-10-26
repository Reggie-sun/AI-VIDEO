---
record_kind: recovery_incident
topic_id: shizhen-S04-predecessor-audio-unknown
learning_eligibility: ineligible
---

# Shizhen S04 Preparation And Audio Unknown

## Human Acceptance And Next Shot

用户明确“过关,开始shot5”，接受当前S04剪辑修正版exact SHA `e40d40218902300f5bde4c9365fbc5a09a06e5e893f97378f1f917b182125fa4`并授权S05。`S05/S04-user-acceptance.json`和当前explicit MCP绑定该已认可edited-source，`S05/predecessor-current-gate.json`只负责此scope的handoff；不把用户认可伪装成一次单独完整听音报告，也不把原S04 raw FAIL、intentional crop造成的assembly NOT_EVALUATED或旧S03远程音频UNKNOWN改为技术成功。下方PENDING属于该确认之前的检查点。S05的新参考、完整五轮求证与真实计数沿S05 primary record/plan继续，当前不自动做S06。

## User-Requested Cut Repair Delivery

用户观看后指出“这版本就一个问题3s和4s这里没有没有衔接”。已用现有同一S04素材剪辑修复：近景后插入台面上原扫码枪/咖啡瓶的近景，再接手机降低后的中景；不新增剧情、台词或付费生成。最终 `outputs/shizhen-episode01/失帧-第一集-S04-接点剪辑修正版-1080p-9.875秒-原声.mp4`，SHA `e40d40218902300f5bde4c9365fbc5a09a06e5e893f97378f1f917b182125fa4`，1920×1080、24CFR、237帧、9.875秒。

CompositionSpec→ResolvedTimeline→HyperFrames软件模式导出，使用原片同声画窗口 `[0,3.5)`、`[3.625,10)`，仅去掉两句之间3帧/0.125秒环境声，不变速；台词约0.68–2.1与6.86–7.44秒完整保留（local Whisper用于定位，不把ASR错字当原话或质量裁决）。混音前PCM与同窗口原音拼接逐采样相等。原始S04-001及其FAIL不改写，不拼接累计片、加字幕或发布。

`S04-edit-001`是本地duration/preview identity准备失败；002–004为检查中间导出，005为当前交付，不是新的生成attempt或消费归零。查到过首切点一帧旧中景，已移除；最终两个切点邻帧已实际查看，不出现整帧伸手机中景。插镜首帧取景仍有轻微变化、裁切放大会稍软，正常速度完整声画与人类接受仍PENDING。HyperFrames lint/check 0error，check保留1条明确intentional crop的escaped_container warning；现有Harness assembly因此NOT_EVALUATED，未关闭检查、改warning或伪造PASS。实际MCP与收据归 `S04-edit-005/exact-edit-mcp-response.json`、`audio-continuity-proof.json`、`assembly-review-result.json`、`delivery-receipt.json`。

本次修剪新增paid generation0，总video仍18，原330credits quote及实际扣费待确认不变；旧S03音频UNKNOWN未重试。完整工程验证和owned commit/push仍按成片优先等待用户对修正版认可。学习评估no_candidate：多次local export是同一素材链，不计作独立生成实验。

## Current Supersession And S04 Submission

最新：S04-001已成功生成/fetch，原声审看片为 `outputs/shizhen-episode01/失帧-第一集-S04-Seedance2.0-001-原声-10秒.mp4`，SHA `9ffd9ef405fbc683ba49dd6044c3653218d525bcbe5cb0e7342c77e6cfc8dbff`，24,813,158bytes，1920×1080，容器10.08秒，native AAC。交付副本SHA与canonical fetch完全一致，没有用ffmpeg改写声画或伪称raw为24CFR。显式当前project-local MCP与40帧复核已执行，`S04/post-media-gate-001.json`经原committer保存真实观察，结论 **FAIL**：3.25秒仍近身持手机，约3.5秒切中景却再次向柜台伸手机，随后5.5–6秒才降手。`action`/`space-camera`失败，`sound`/`performance`/`story-scope`/`coverage`尚NOT_EVALUATED；静态照片、嘴部运动、第三镜人类认可或AAC存在不能代替本镜听音、口型与完整自然度。

已在交片时告知用户该连续性问题，没有签PASS或自动继续；本有限单元新增1次video、18总次，2.5 video0、额外音频分析0、S05/新累计片/字幕/发布0。quote330credits，实际扣费待结算；旧S03音频UNKNOWN原样保留。主要收据为 `S04/delivery-receipt.json`、`actual-binding-receipt.json`、`post-media-gate-001.json`。

最终当前针对性测试18通过，关联三个模块在补充负向参数后重跑 **277通过**，输出与源码末态hash保存在 `S04/adapter-related-validation.json`及log；这是选定模块验证，未冒充Harness全套或媒体通过。`git diff --check`通过。保留全部其他窗口改动；本镜未获用户认可，按照成片优先规则，不进行完整工程验收或owned commit/push。学习评估仍no_candidate：这次单臂生成未隔离手机跳位原因，不能将参考图数或型号升级为普遍结论。

用户在同一会话明确回答“听过，声画衔接认可”。`S04/predecessor-human-audio-confirmation.json`保存完整问题、原答、S03-005 exact SHA，属于独立实际听音证据；旧远程声音分析仍UNKNOWN、费用未明且没有重试。当前project-local MCP及52帧画面复核、原生消失接点证据与该人类听音报告，经 `review_generation_attempt(repair_evidence=True)` / ProductionStateCommitter补录原8项观察PASS，见 `predecessor-current-gate.json`。这是技术逐镜推进证据，不是虚构远程理解成功或Production/全片接受。

用户追问10秒为什么不用2.0后，实际改选 **Seedance 2.0 VIP**。先新增真实router/compiler/resolver回归，复现本地两处model allowlist拒绝，再只在现有remote native prompt和video compiler两处开放已注册VIP型号；保留native audio、exact prose重编校验、独立voice/neutral fallback拒绝和全部预算/permit边界。18个当前针对性用例通过；三模块关联测试274通过（该次收集早于补充3个负向参数，当前负向参数已另行通过）。没有把2.5-only软件限制说成2.0模型不支持自然对白。

最终4个reference SHA与 `prepare.json`实际bindings完全一致，完整prompt3703字符，入口、同右手手机、稳定瓶枪纸饭团、原话顺序、无对白时间戳、KEEP与10秒设置lint全部通过。原2.5准备profile与640credits quote留作未提交历史，未生成2.5。2.0四图10秒1080p quote330credits；内部1500CRD为guard，实际扣费待结算。

`trial-S04-v1` / `shizhen-S04-qualification-attempt-001`已经现有ProductionStateCommitter、selected adapter和one-use permit接收1次视频调用。提交前原平台17个资源全部完成、目标节点为空；提交后27个project入口再盘点得到18个唯一paid video、无video UNKNOWN（旧join-S01-S02-01 reader invalid单独保留，不改其他窗口历史）。原17次不归零，合并上限18，自动retry0。当前仍在等待实际MP4；不宣称合格、完整工程验证、用户接受或发布。

Native review risk gate由Parent判定NOT_REQUIRED：两处纯型号准入与确定性表达校验扩展，仍经注册能力、exact request及原paid/state owners；针对性测试覆盖失语、改词/换speaker和图像绑定，不涉及新凭据或不可恢复state路径。其他窗口同时在video_compiler新增的reference-strategy hunk保持原样，后续只允许本任务owned hunk提交。学习评估no_candidate：这不是独立多次质量实验，未自动改Skill/Policy。

下方原阻断记录是历史，已由本节独立听音补证与实际S04提交更新；旧UNKNOWN本身没有被改成成功。

## Reference Supplement After User Review

用户指出只有两张取帧不够后，实际补做两张Shot4动作关键帧：`S04/references/03-check-side-passage.png`（保持右手近身持手机，查看既有侧通道）与 `04-phone-lowered-look-to-rider.png`（同一右手手机降低至髋侧，头/视线转向画外骑手）。两次image_gen均已取得明确结果、复制到任务目录并实际查看；瓶直立、枪落台且在瓶左、饭团仍在白纸，店员没有重现。source.json保存实际输入图hash、完整prompt、输出hash/尺寸及工具原始路径；帧间运动、声音、口型或人类接受仍未验证。当前共4张，前2张actual取帧、后2张拟定动作图；`S04-intent.draft.json`与`reference-evidence.json`已同步4个planned参考，不代表视频模型已收到素材。

本次补图新增image调用2、video0、audio0，图像费用未暴露；原声音UNKNOWN/已消费permit保留，未重试、未生成Shot4。下方“两张/无额外图像调用”是补图前检查点，已由本节更新参考准备状态。模型兼容性与S03 Gate阻断不因参考变多而解除。

## Current Result

用户明确“开始shot 4”。S04真人镜头意图与两张actual source参考已准备，GenerationIntent结构验证通过；未提交S04视频。不是已完成镜头，也不是只凭工具成功签PASS。当前硬阻断为S03-005声音补证的已消费调用UNKNOWN，不能盲重试。

## Exact Source And Prepared Work

源S03-005 SHA `51bf0aaea2deaa8f02fb2a8f3f4f2666a8cd6304e5f9f80f5598fd7eab87368f`，当前33.875秒连续版 SHA `45fb4e45f815bbe00f42165429dd5f19335e2dbf60ef4206710e09755308f233`。S03末尾已俯身找过柜台下、右手手机在胸腹前，所以S04不再演一遍发现或探头；保留原文两句疑问，再查侧通道、降手机、叫师傅、看向画外骑手。旧剧本CG媒介和S04固定8秒不作为当前约束。

`live-action-regeneration-01/S04/S04-intent.draft.json` 是未封存草稿，不是原生已编译请求。
`reference-evidence.json` 给出实际两图的SHA、尺寸、原MP4身份、请求取帧时刻及原生PTS/序号；
图片1为当前末态，图片2为柜台和稳定物件，不迁移其更早的姿态。没有额外图像生成调用。
最初草稿误用了不存在的dialogue模式名，随后按当前schema改成untimed conversation结构，通过真实模型校验；没有封存或提交错误草稿。

平台只读账号/能力核验：2.0 VIP、multimodal、10秒、1080p可选；按现有native `quoteActions([{id,action}])` 得到available/330credits。首次诊断误用object参数，已保留该无效诊断并以 `native-capability-quote-corrected.json` 更正，不是平台生成或付费重试。当前common compiler的untimed conversation限制为2.5，故模型选择尚未最终封存，不声称2.0可直接执行此对白合同。

## Unknown Evidence Operation

为满足下一Shot提交前的原Per-Shot Gate，使用project-local `audio_understand` 对同exact S03补声音观察。离线preview成功，source34,353,935bytes，完整PCM derivative SHA `d820e0b2ce4a84ec1cfabb007144b29fc0ece03652df2b2290e6593e5f71ddbe`；新建一个development-only unit，固定USD0.05内部上限、count1、25分钟窗口、原supplier与固定Google origin，经fresh project MCP和真实一次性permit提交一次。

`S04/S03-005-predecessor-audio-operator/outcome.json` 明确记录 `consumed=true`、`status=UNKNOWN`、`code=transport_unknown`，intent SHA `3ec46760d937d883f638ce32d3487a0118a006fa9a80ce17172a7987dc90816e`。MCP外层`isError=false`并不证明理解成功；实际content里的typed UNKNOWN已读取并作为停止依据。没有声音观察或可签PASS的结果，未重试、未重铸permit、未更换模型重跑该分析，真实费用待确认。没有把waveform、ASR或native音轨存在当作声音语义通过。

## Counts And Stop

重新严格读取全部当前production roots：S01七、S02二、S03五、cold-open三，共17次已知paid video，均已fetch；Manifest running+validate不被误报为仍生成。未知的是这次额外声音分析，不是历史视频。当前S04 video新增0、无新video节点/root/request/budget/permit。`preparation-status.json` 保留17个历史attempt、拟议下一有限17→18单元、音频UNKNOWN与未封存状态。未生成S05、字幕或新累计片，未发布。

下一步必须先由原证据owner恢复或补齐可靠同bytes声音证据，使S03满足实际逐项条件，再完成S04 exact模型适配与原有准入。不能借“用户要求下一镜”伪造前镜PASS。计划见 `docs/superpowers/plans/2026-10-27-shizhen-S04-production.md`。

学习评估 `no_candidate`：一次UNKNOWN不能证明模型或网络的普遍质量；没有将本次失败扩张为新Skill/Policy规则。此次仅run-local准备和本记录/计划，无共享源码变更；结构验证、native只读quote与真实UNKNOWN分别保留，不当作最终接受。
