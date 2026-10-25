---
record_kind: media_experiment
topic_id: shizhen-episode01-native-conversation-sync
learning_eligibility: eligible
evidence_index_version: "1"
---
# Lost Frames Episode 01 — Jimeng 2.5 Acting Trial

Date: 2026-10-25

## Current Checkpoint — Bilingual Captions Without Ending Symbols

2026-10-26，用户要求“把结尾不要有符号写进规则,然后我需要中英双版本的”，并明确选择“一份中英双语字幕视频”。已交付 `outputs/shizhen-episode01/失帧-第一集-S01-1080p中英双语字幕版-16秒.mp4`，SHA `3bbf15995bac0e91033be3689b12f16ad1e09f9eb8a78d53a80cb2724a0d16a1`，16,537,969 bytes，1920×1080、24fps、16秒。中文在上、英文在下，同步四个实际对白窗口，两行均无句尾标点或装饰符号，句内逗号及英文缩写撇号保留。对应SRT同目录 `失帧-第一集-S01-中英双语字幕.srt`。此前单语字幕版保留为历史，未倒写其用户验收。

规则与本项目双语要求已作为仅两个owned hunks提交并推送 `7081ed5`；没有stage其他窗口的既有dirty修改。exact commit-range Harness `related`通过，receipt `.agent/harness/runs/shizhen-bilingual-caption-rules-20261026/receipt.json`。该receipt证明已提交的文档snapshot，当前working tree同文件还保留其他未提交内容，freshness因此返回 `scope_worktree_clean=false`，不冒称整个共享工作区或旧工程改动已完成验证。工作区原AGENTS长段落已使其超字节预算，本轮使用与HEAD原句等字节的简短规则，提交snapshot仍为13,996 bytes，未扩大budget或删除旧dirty规则。

本轮沿同一canonical字幕/合成入口追加双语caption revision，未改共享runtime源码。首次将双语display hash误用于源中文script_hash，标准reader拒绝；通过唯一committer显式提交后继Registry修正该字段，保留旧Registry与失败CaptionTrack bytes，随后standard reader复开PASS，未改validator或原source项目。源audio script_hash标识原中文，display transcript_hash标识中英显示文本；英文由Codex作任务内翻译，不称英文ASR或英语配音。

最终exact MCP抽32帧，Parent逐项查看四组双语文本及17个字幕边界帧；无句尾符号、溢出或相邻cue重叠。HyperFrames0.7.103 lint/check均0error/0warning；双语版AAC解码PCM与上一字幕版完全相同，原raw与source Manifest SHA不变，无新增生成/配音/付费调用、无S02、无Production activation或发布，用户对双语版本审看仍PENDING。证据为 `runs/shizhen-episode01-jimeng25-20261025-001/caption-review-005/bilingual-v4/delivery-verification-receipt.json`、`exact-MCP-analysis.json`、`cue-boundaries/contact.png`与`source-hash-recovery.json`。

本轮record-ai-video-session更新同一primary record；distill-ai-video-learning评估no_candidate：这是同一已生成源的字幕呈现与翻译修订，没有独立模型质量实验，不改全局memory或学习规则。

## Previous Checkpoint — Approved HD Raw And Caption Review

2026-10-26，用户原话“认可”绑定已交付HD005原片SHA `15c7c21ea8ef526d641d5a1565cbb4ec93ea4ee63b34fc9c7a0d73f2b21efb0b`，触发现有先审原片、认可后制作字幕规则。原片认可事实不倒写旧技术NE、001口型FAIL或003纸穿透FAIL，也不授予Provider Production qualification。

已交付 `outputs/shizhen-episode01/失帧-第一集-S01-1080p字幕版-16秒.mp4`，SHA `ea09423b8e4edda2eb66ebbeb4aceccb9c16cbae63e9a331f209a4c051d9c90d`，16,545,012 bytes，1920×1080、24fps CFR、384帧、16秒，AAC48kHz立体声。独立字幕文件为同目录 `失帧-第一集-S01-中文字幕.srt`。原MP4与源Manifest字节未变，原声保留，既有AI角标保留；字幕副本待用户审看，未发布、未activation、未生成S02。真实video submit仍5次，新增付费生成0，既有报价1792CRD仍不作实际结算。

完整本轮证据在 `runs/shizhen-episode01-jimeng25-20261025-001/caption-review-005/`：`delivery-verification-receipt.json`、`render-005-receipt.json`、`exact-MCP-analysis-final005.json`、`final-cue-boundaries/contact.png`、`related-regression.xml`。实际审看片视频约8.07Mbps、音频约194kbps，低于正式发布建议15–20Mbps和256–320kbps，不冒称正式发布编码参数已全部满足。

## Previous Checkpoint — HD Resolution Version 005

用户认可004的480p导演/表演方向，明确要求先写480p试片认可后生成1080p并重新审看的规则，再实际生成。规则已提交并推送 `5bf4cd7`；raw审看认可后制作字幕的原则继续适用。第005次真实submit已ACCEPTED，submission fingerprint `0fad26e24652fe9e3dcfb0d99c554012d1cd030f6a3f7a5d78a55d096ee183b2`，同画布新节点 `node_h5ayptnszt`，native request明确1080p、16秒、same D首帧、exact004 prompt、原生声音KEEP，已fetch；实测1920×1080、16.065秒，详见文末HD Media Result。当前累计5次真实video submit，旧001–004所有观察/paid/fetch和独立audio UNKNOWN保留；下方旧额度/媒体状态是当时历史，不证明新片效果。1024CRD为本次报价，5次报价和1792，不作实际结算；原总2000→3500内部上限也不作费用。无新增image/audio calls，不激活Production或公开发布。

## Previous Checkpoint — Coverage Retake 004

2026-10-26 HKT，用户要求按已修订的导演规则生成首镜。当前第004次实际submit已ACCEPTED并已fetch，交付原片见文末 Media Result；submission fingerprint `eae1e40bb31d168f1e8df71df6dd0c4e1b51a4b282bbb410ffb0ce4ae3c4f220`，同画布新节点 `node_svdkkk4xrp`。下方关于未提交D版、001–003与先前上限的描述均为历史状态，不能作为当前执行或质量结论。003的纸张穿透FAIL仍保留；004的可见切镜与接触核验PASS，完整声画/动态美术尚未验收。当前累计4次真实视频提交，旧音义UNKNOWN未重试；没有新增静态生图或声音调用。

## Goal And Scope

用户要求原创都市灵异悬疑3D动画《失帧》EP01《消失的十一秒》，目标3–5分钟，指定 Jimeng / `seedance_2.5`，对白不分配固定时间戳。完整原文、剧本、设定、31镜/276秒弹性coverage和提示词在 [creative artifacts](../superpowers/artifacts/drama/shizhen-episode-01/)。先做原剧情约52秒的五镜Pilot，人工声画GO前不扩为整集。

## D S01 Execution Request — 2026-10-26

用户明确要求“开始吧第一个shot”。已按当前源码和standard project reader只读重开 `trial-S01-v3`、两个真实视频attempt及原paid budget，并核对D首帧exact bytes可解码。当前实际submitted=2、原封存ceiling=2，旧窗口已到期；首样为canonical质量拒绝，第二样为已fetch的 `running / validate`。两次paid状态与金额沿原ledger保留，未假定费用结算。

这次生成存在现有执行能力缺口，**没有提交D版首镜**：D图尚未通过既有素材修订入口进入Registry/Shot；更关键的是当前 `GenerationDecisionExecutionBinding` 的qualification分支与 `_qualification_quality_repair.allows_one_known_quality_repair` 只支持首样、指定known-no-effect恢复或ceiling2/used1的保留参考质量修复。后者实际compiled delta仅允许prompt/profile，不支持保留两次真实提交后替换image_bindings的第三次同Shot生成。该结论来自当前代码/契约和canonical状态核对，不冒称已对新D请求执行过compile或真实POST。

已保存非执行态 `D-S01-authoring-draft.json`、中文提示词稿与 `readiness.json`，位于 `runs/shizhen-episode01-jimeng25-20261025-001/D-S01-execution-preflight-20261026/`。保留16秒预算、480p意图、D整幅首帧、三句原文、自然听说与原生声音KEEP、固定同侧机位和服务动作；文本检查确认三句各一次，无单句时间字段。它不是compiled request、execution binding、live quote、permit、素材登记或执行授权。

最小恢复条件是正规canonical入口支持此次新美术参考修订并保留既有全部历史/累计paid计数，或已有同一指定Provider/model的当前qualified执行证据。当前没有相应可用路径；应作为明确的执行能力/契约工程任务处理，不能在本次媒体请求中修改guard/资格/上限、换新project或task归零、复用permit或重标UNKNOWN来继续。未修改共享源码、政策或执行合同，未创建新budget/grant/permit，未新增生图/视频/付费调用，未activation或发布。前后Manifest SHA相同，见readiness receipt。

使用 `record-ai-video-session`更新此实际blocker；`distill-ai-video-learning`为 `no_candidate`。仅做只读状态与schema/图片完整性核验、提示词文本检查和文档diff检查，没有运行完整测试或制造媒体验收。所有未知/他人工作保留，未stage/commit/push；D版视频目标仍未完成。

## D Selection — 2026-10-26

用户回复“D”，明确选择 D 原图作为林序美术方向。当前approved reference为 `outputs/shizhen-episode01/D-selected-20261026/linxu-D-approved-reference.png`，SHA-256 `833cd1f92cbfd0e0d92c451d018be308a854536ed6563e723eb9fd65707b7761`；exact copy已核验。该选择取代下方历史“静态风格待选择”的状态，保留表演调度，不表示新视频或全部声画要求已通过。

本轮仅准备角色参考和完整S01首帧，共2次静态生图、0次视频调用。首个整景同时使用D与旧首帧，Parent实看后判断主角仍偏旧版少年化脸，保留为 `S01-D-firstframe-candidate-001.png / NOT_READY_LIKENESS`。第二次只用D作身份参考、以文字保留站位和动作起点，得到 `outputs/shizhen-episode01/D-selected-20261026/S01-D-firstframe-candidate-002.png`，SHA-256 `03fdf2a59ab662d3fcdf1d8658165788cf262298ce38c6f864d4a7ad1b5328b8`，1672×940 RGB PNG。已实际查看三名人物、脸部倾向、手与物体、柜台轴线及道具，核验文件可解码和exact copy。第二稿更接近D的成年脸部，作为首帧候选交付；背景陈设与旧稿有差别，不宣称像素级布局一致或原动态表演已复现。

完整输入、旧/新候选与静态核验位于 `runs/shizhen-episode01-jimeng25-20261025-001/D-selected-20261026/`；主receipt为 `D-reference-firstframe-receipt.json`。本轮未运行新的canonical视频步骤、素材activation、执行规则或上限调整，所有旧attempt、UNKNOWN、预算和Gate保持。新首帧尚未导入Registry或绑定Shot，旧request仍是旧参考，不能声称已使用D出片。下一步仅能沿已有素材修订/绑定入口与现有准入检查推进；本轮没有为下一次submit准备新权限。

自有production-design已写入D及参考职责，并将此前“咖啡罐/拉环”的文字与实际已认可画面的一瓶黑金咖啡/瓶盖统一。未修改共享源码、契约、资格或调用额度。生图实际费用未由工具回报，待确认；尚未commit/push或发布。自动learning评估 `no_candidate`：单次美术选型和连续静态修订不构成通用质量或模型能力结论。

## Art Direction Feedback — 2026-10-26

用户查看修复版后反馈：“我觉得画风太low了,不够高级,人物建模.你先给我几张图我看下,这个表演我倒是觉得很ok”。当前解释为**表演方向获用户认可，角色造型/渲染审美不获认可，先做静态选型**；没有将这句话扩张为逐句口型、全声音要求或整片验收PASS。旧视频及其pending Gate均保留，本轮没有新增Jimeng视频、音义观察、activation或渲染。

使用默认Codex `image_gen.imagegen`先做A/B/C三份双联造型稿（左脸部近景、右便利店半身），旧首帧只拟作场景/服装参考。Parent实看后发现三份仍贴近原脸型和发型，原拟写实/雕塑/细腻方向未充分拉开；保留全部结果，不把预设方向名写成已实现的风格事实。以新有限单元补D/E两份无旧图输入的原创设计，明确成年人骨相和新轮廓；实际D较成熟、E神态更柔和，两者仍属偏写实CG，并未证明强手绘风成立。E额外出现背包带，未获canonical服装/道具认可；如被选中，正式身份参考需统一这些细节。

五张已交用户查看，均为1672×941 PNG，原文件保留，工作副本在 `outputs/shizhen-episode01/art-lookdev-20261026/`；exact path/SHA/解码信息见 `runs/shizhen-episode01-jimeng25-20261025-001/art-lookdev-20261026/images-manifest.json`。同目录 `lookdev-intent.json`、`redesign-intent.json`分别保留3次首单元与2次后继单元，零自动重试、无UNKNOWN；`user-feedback-001.json`绑定反馈和原MP4身份。已实际检查五张图，并逐文件核验可解码、尺寸和exact copy SHA；这些是二维造型稿，未声称生成了三维mesh、选定风格、可直接作为首帧或复现了原有动态表演。

本轮5次生图的金额/积分未由工具回报，实际费用待确认；未改动生成契约、代码或Provider，未stage/commit/push任何共享变更。静态风格待用户选择；已满足的表演调度作为后续保护目标，未来换造型的视频仍须重新验证。此checkpoint按 `record-ai-video-session`记录；`distill-ai-video-learning`评估为 `no_candidate`：当前只有未选型的静态方案和一次局部审美判断，没有可升级为通用模型成功率的证据。

## Latest Media Checkpoint

修复尝试002已成功fetch，精确SHA-256为 `7fcdf00f0d5438b3db181f158a19e0cc27bd540537cacdd9dea0006c82e1de4e`，17,582,694bytes，16.065秒，852×480，含原生声音。播放副本为 `outputs/shizhen-episode01/失帧-第一集-首镜-修复版-Seedance2.5-16秒.mp4`，与canonical fetch逐字节一致。`S01-repair-fetch-output.json`记录下载与副本identity。

已再次显式调用project-local `video_analyze`，取得17个1秒间隔帧、metadata及单场景证据，见 `S01-repair-mcp-analysis.json`；未调用任何新audio operator、ASR或生成。帧样本保留了试烫收手、额外垫纸、推近和最终短笑，人物、道具、机位未见关键漂移。声音/口型与接话仍待用户实际播放判断，`S01-repair-002-post-media-gate-pending.json`整体为 `NOT_EVALUATED`，不提交S02，不把下载或帧样本视为口型修复成功。

## Current Runtime Truth

本记录的run为 `runs/shizhen-episode01-jimeng25-20261025-001/`，canonical root为 `trial-S01-v3/`。只使用同一即梦账号hash、同一画布、首帧模式、16秒480p16:9与原生声音KEEP。四型号仍为 `UNQUALIFIED`；本任务走现有qualification用途，fetch不授予Production qualification、activation、P6或Final Acceptance。

首样 `shizhen-S01-qualification-attempt-001` 已生成、下载并按用户播放反馈判FAIL：**“声音和口形动作对不上”**。原片SHA-256为 `060b26afac29f4cedeeac6f6316a4ca569e1fdbbf218632786616803073edcee`，11,658,016bytes，16.065秒，852×480，含原生音轨。原片审看副本为 `outputs/shizhen-episode01/失帧-第一集-首镜-Seedance2.5-16秒.mp4`，字节与canonical fetch一致。MCP帧样本显示试烫收手、抽纸垫饭、推近和短笑等可见动作；这些不抵消声画失败。

首样的自动音义观察只调用一次，返回 `transport_unknown / UNKNOWN`，原one-use消费与outcome保留，未重试。未将ASR、音轨存在或播放器状态当作真实听音通过。机械播放辅助尝试未取得成功收据；用户实际播放给出的负面反馈独立保留。

首样提交后Chrome曾退出，canonical只读poll连接失败。只恢复原persistent profile，核对同一账号、画布、节点及resource/submit/task后继续查询和fetch；没有重提视频、换账号、换Provider或清理旧任务。

## Bounded Repair

对真实native prompt的检查发现：人物表演按服装/位置描述，对白按名字描述，存在名称与画内主体绑定不够直接的歧义。这只是可检验的修复假设，不是已证明的唯一原因。重做保持同一首帧、三句原文、16秒、固定顾客侧中景、服务动作、道具和声音；只在文字中将林序绑定右前灰夹克顾客、小程绑定左侧红围裙店员，并明确本轮说话与闭嘴倾听的对象。未加入单句时间戳、静音或另配音。

参考职责遵循[官方2.5指南](https://docs.volcengine.com/docs/ark/seedance-2-5-prompt-guide?lang=zh)关于清楚指代素材/主体的建议；该文档不证明即梦surface支持未实现的edit/extend或声画质量必然通过。没有为了修口型擅自换模型。

现有qualification binding此前只允许首样与known-no-effect运行恢复，不能执行已生成但质量失败的修复。因此追加最小通用准入：累计ceiling2/used1、零resample、完整已知质量失败、显式production_repair、同task/Shot/goal/rubric、保护全部已通过项、真实compiled delta仅prompt及必要新空节点profile。原committer提交锁内还须严格重开上一尝试的 `/1` quality rejection并对齐evidence、request、MP4、size、QA及最后experience。UNKNOWN、证据缺口和第二次质量修复不获此入口。

沿用原budget/quota extension、durable intent和one-use permit。旧500CRD内部上限和ceiling1保留，显式继任为总1000CRD、ceiling2，含已消耗的首样；不是市场价或消费归零。新节点在同画布，原节点与失败资源保留。修复尝试为 `shizhen-S01-qualification-attempt-002`，已接受，submission fingerprint为 `0bc3d8d51fb66630e5480ade74d0984833c1a6eb1806fd4c2025999051b650c0`；之后已成功fetch，当前状态见上方 Latest Media Checkpoint，口型尚待确认。

## Verification And Evidence

- 不定时多人对白契约及原修复验证见 [conversation record](2026-10-25-untimed-conversation-contract.md)；该工程结果不等于声画验收。
- 新质量修复入口：候选45项局部测试PASS（57.20s），实际working tree同45项PASS（53.41s）。记录在run的 `quality-repair-focused-tests-r2.log`、`quality-repair-working-tree-tests.log`，不冒充Harness或完整回归。
- 一名native `reviewer_xhigh`两轮审查：首轮QQR-001发现缺terminal quality rejection核验，Parent确认并修复；复审finding set为空。exact候选hash和应用核对在 `quality-repair-candidate-identity-r2.json`、`quality-repair-review-receipt.json`。新增共7行shared hooks与独立叶模块，保留之前所有共享overlay字节。
- `S01-v3-post-media-gate.json`、`S01-quality-failure-source.json`、`S01-quality-failure-diagnosis.json`和 `user-exact-review-001.json`绑定首样FAIL；canonical `reject_video_generation`正式关闭首样，保留paid/fetch证据。
- `quality-repair-exact-closure-preflight.json`在原committer锁内验证实际首样拒绝，零effects；`S01-repair-preflight-lint.json`核对三句各一次、无对白时间、首帧与native_audio。
- `S01-repair-budget-extension-intent.json`、`S01-repair-quota-extension-intent.json`保存原ledger的显式继任；`S01-repair-002-prepare-output.json`封存actual request，hash为 `d862bf2b3154e8877339038d3d37e1933148152ecd791740734a4a4c1967419a`。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sz01-fetch | native:47ce792b46c1c7a8d0991170c2a526e01e781da56d59dabbdb97a52388cb88c5 | shizhen-S01-conversation-sync | shizhen-S01-qualification-attempt-001 | baseline | 060b26afac29f4cedeeac6f6316a4ca569e1fdbbf218632786616803073edcee | PROVIDER_RECEIPT | FETCHED | NONE | NEW_ATTEMPT | NONE | runs/shizhen-episode01-jimeng25-20261025-001/S01-fetch-output.json |
| sz01-viewer | native:47ce792b46c1c7a8d0991170c2a526e01e781da56d59dabbdb97a52388cb88c5 | shizhen-S01-conversation-sync | shizhen-S01-qualification-attempt-001 | baseline | 060b26afac29f4cedeeac6f6316a4ca569e1fdbbf218632786616803073edcee | HUMAN | FAIL | AUDIO_VIDEO_SYNC | SAME_EVIDENCE_NEW_PROOF_LAYER | sz01-fetch | runs/shizhen-episode01-jimeng25-20261025-001/user-exact-review-001.json |
| sz01-gate | native:47ce792b46c1c7a8d0991170c2a526e01e781da56d59dabbdb97a52388cb88c5 | shizhen-S01-conversation-sync | shizhen-S01-qualification-attempt-001 | baseline | 060b26afac29f4cedeeac6f6316a4ca569e1fdbbf218632786616803073edcee | ANALYZER | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | sz01-fetch | runs/shizhen-episode01-jimeng25-20261025-001/S01-v3-post-media-gate.json |
| sz01-repair-fetch | native:0bc3d8d51fb66630e5480ade74d0984833c1a6eb1806fd4c2025999051b650c0 | shizhen-S01-conversation-sync | shizhen-S01-qualification-attempt-002 | speaker-binding-repair | 7fcdf00f0d5438b3db181f158a19e0cc27bd540537cacdd9dea0006c82e1de4e | PROVIDER_RECEIPT | FETCHED_NOT_ACCEPTED | AUDIO_REVIEW_PENDING | NEW_ATTEMPT | NONE | runs/shizhen-episode01-jimeng25-20261025-001/S01-repair-fetch-output.json |
| sz01-D-fetch | native:e12c627e860839fee26494e47762e31af09329dccac7f11007c5a6a2781ac505 | shizhen-S01-D-visual-revision | shizhen-S01-qualification-attempt-003 | D-authored-firstframe | ea0dad2e3ea4a4c964d3a7cdf731d1e96c36a64358b3427dda7adf3aed12cbbc | PROVIDER_RECEIPT | FETCHED_NOT_ACCEPTED | VIEWER_REVIEW_PENDING | NEW_ATTEMPT | NONE | runs/shizhen-episode01-jimeng25-20261025-001/D-execution-003/fetch-output.json |
| sz01-coverage-fetch | native:eae1e40bb31d168f1e8df71df6dd0c4e1b51a4b282bbb410ffb0ce4ae3c4f220 | shizhen-S01-coverage-contact-revision | shizhen-S01-qualification-attempt-004 | same-D-coverage-contact | 06168bd113436e755cfca82c198677544f95cd82c76c216c65a131a6c59170a3 | PROVIDER_RECEIPT | FETCHED_NOT_ACCEPTED | AUDIO_PERFORMANCE_ART_REVIEW_PENDING | NEW_ATTEMPT | NONE | runs/shizhen-episode01-jimeng25-20261025-001/coverage-retake-004/fetch-output.json |
| sz01-HD-fetch | native:0fad26e24652fe9e3dcfb0d99c554012d1cd030f6a3f7a5d78a55d096ee183b2 | shizhen-S01-HD-resolution-revision | shizhen-S01-qualification-attempt-005 | same-intent-1080p | 15c7c21ea8ef526d641d5a1565cbb4ec93ea4ee63b34fc9c7a0d73f2b21efb0b | PROVIDER_RECEIPT | FETCHED_NOT_ACCEPTED | AUDIO_PERFORMANCE_ART_REVIEW_PENDING | NEW_ATTEMPT | NONE | runs/shizhen-episode01-jimeng25-20261025-001/HD-execution-005/fetch-output.json |

## Cost And Publication

视频实际submit累计2次，两个原生报价均192积分；实际结算均未核验，不把384报价之和或1000内部上限写成实际费用。此前3次生图与1次outcome未知的音义观察的实际费用也待确认。精确计数和边界在 `cost-summary.json`。

整集尚未完成，无公开发布、Production activation、P6或Final Acceptance。当前代码/创作修改未commit/push；遵守先交审片、用户认可效果后完整工程验证再提交的顺序，未夹带其他窗口工作，未stage未知改动。

## Assessment And Next Boundary

首样明确FAIL，不能提交下一Shot；只执行上述一次修复。新片下载后必须重新显式调用project-local video-analysis，逐项检查原目标和已满足项，声音未知不能猜PASS。需要实际声音/口型判断，不能重试原UNKNOWN audio operator。修复有效才续下一镜，若失败则保留假设被反驳的证据，停止同类重抽。

自动learning评估：`no_candidate`。当前只有一份已判定FAIL的实际媒体，修复版虽已fetch但声画结论待用户播放；seed不可控且native node/profile不同，不宣称可归因的通用成功规律，不由代码测试、文档数或重复分析升级为通用模型经验。未改Skill/Policy/Gate的学习规则，未更新全局memory或RAG索引。


## D Visual Revision — Authorized Result

2026-10-26 HKT，用户选D、要求开始首镜，并在正规入口阻断说明后明确回复“我授权”。本节为当前状态，前文截至002的阻断、额度和待评估记录继续保留为历史。

新增可复用的 authored visual revision：`ProductionStateCommitter.supersede_video_generation` 绑定旧 exact request / fetch / experience / QA 与新 goal / 首帧SHA，使用独立 receipt 封存用户要求改版的旧结果。002原始4PASS+2NOT_EVALUATED观察经实际project-local MCP桥接持久化，paid/fetch保留；关闭原因为 `generation_visual_superseded`，不冒充模型失败或质量验收。随后正规追加D素材、修订同一Project至revision2及同goal_id的 `2-D-art` QA，保留全部原要求、三轮无台词时间戳的对白、动作、摄影与声音要求。

新qualification入口仅允许真实新首帧、完整累计历史、相同provider/model/output及used+1的有限单元，提交锁重新打开exact supersession。原预算owner在start前追加1000→1500内部上限，原quota owner追加2→3；原reservation、UNKNOWN和计数均保留。第一离线副本错误地先start再追加预算，被旧guard正确拒绝；第二副本按预算→start→quota顺序通过标准读回、正规revision、compiler和锁内submit guard，两个副本均无Provider effect或permit，不计作实际生成。

Native independent reviewer沿同一profile进行了两轮。AVR-001确认并补齐experience→旧projection/candidate以及facts/scope/rubric joins，重封错误candidate的closure和strict-reopen负例均拒绝；AVR-002确认并规范化reason，带空白参数exact replay通过。R2 finding set为空。R1关联131测试通过；最终R2针对closure/reader/qualification/旧quality修复的52测试通过。未声称完整Harness或全套验证，未stage共享overlay；用户认可视频效果后才做完整工程验证与owned-path commit/push。

实际第003次视频submit已ACCEPTED，submission fingerprint `e12c627e860839fee26494e47762e31af09329dccac7f11007c5a6a2781ac505`，同画布新节点 `node_eka0sd7b89`。首帧SHA `03fdf2a59ab662d3fcdf1d8658165788cf262298ce38c6f864d4a7ad1b5328b8`；原片SHA `ea0dad2e3ea4a4c964d3a7cdf731d1e96c36a64358b3427dda7adf3aed12cbbc`，11,388,334 bytes、16.065s、854×480、有原生音轨。交付副本 `outputs/shizhen-episode01/失帧-第一集-S01-D版-Seedance2.5-16秒.mp4` 与fetched原片逐字节一致。

已显式调用project-local `video-analysis` 并查看0至16秒17帧：伸手缩回、取纸垫底推近、末尾笑意以及人物服装/脸/空间连续可见。逐镜Gate仍为NOT_EVALUATED：完整原速表演、对白/口型和D版动态美术满意度须用户播放确认；没有重试旧UNKNOWN音义工具，没有将音轨存在或未转写时speaking_duration=0冒充语义结果。未提交下一Shot、未激活Production、未发布、无P6或Final Acceptance。

Evidence owner：`runs/shizhen-episode01-jimeng25-20261025-001/D-execution-003/` 下的 `software-verification-receipt.json`、`native-review-receipt.json`、`prepare.json`、budget/quota extension、`submit-output.json`、`fetch-output.json`、`exact-MCP-analysis.json`、`post-media-gate.json`、`evaluation-source.json` 和 `diagnosis.json`。真实累计视频submit为3，三次各报价192CRD，576只是报价总和；实际结算均待确认，内部1500上限不作费用。`cost-summary.json` 保留前驱原字节和SHA。

Automatic learning evaluation：`no_candidate`。D参考与新节点、不可控seed及场景细节同时变化，且动态观感/音画尚未验收；当前证据不支持可归因的通用模型质量规律。未新增学习占位、未更改Skill/Policy学习规则、未写全局memory。


## Paper Contact Correction — Viewer Feedback

用户质疑固定一镜到底的导演选择，并指出约10秒纸张穿透。对同一003 MP4显式调用project-local MCP按0.25秒取样，复核9.25–11.25秒：10.50秒纸仍横在饭团上方，10.75秒已在底部；饭团未被提起、移开，也没有合法插入路径，属于接触/遮挡连续性错误，无剧情或灵异含义。此前1秒抽样只看到垫纸的起末状态，action / space-camera PASS误判撤回并改为FAIL。旧Gate原字节保存于 `D-execution-003/post-media-gate-before-paper-review.json`，当前Gate为FAIL。

通过原same-bytes evidence-repair桥接追加 `paper-failure-evaluation-source.json` 和 `paper-failure-diagnosis.json`，旧experience保留；标准reader读回通过。未新增视频提交、未重试UNKNOWN、未伪造完整QA拒绝或证据修复耗尽：声音/完整表演/动态美术仍未评估，attempt保持VALIDATE，当前逐镜Gate阻止推进。稠密原始MCP证据为 `paper-contact-MCP-quarter-second.json`。

固定双人中景是author在shot-prompts与typed camera intent中主动作出的选择，意图为建立人物位置、让帮忙与倾听连贯，并为后续空位提供空间依据；模型没有强制16秒一镜到底。当前安排过度围绕单个生成片段维持同一构图，未充分按戏剧关注点拆镜。新的覆盖建议尚未执行：短中景建立空间，人物近景承接烫手与道谢，清楚的手部动作或先铺纸后放饭的简单调度，再回反应；不按固定台词秒数切镜。用户本轮是在询问和指出问题，没有据此自动重抽视频。

Automatic learning evaluation：`no_candidate`。这是同一003媒体新增证明层，保留前次漏检和本次修正，不能计作独立生成实验或据此升级通用Gate。

## Coverage Revision 004 — Execution Boundary

本次将原开场story beat与摄影覆盖、生成片段分开：一个16秒生成单元包含柜台关系、林序回应、店员帮忙、林序反应四个关注点，以同轴硬切组织；各机位内部稳定不再等于全段固定构图。对白仍为三轮原文、无逐句时间戳；D首帧、人物身份、美术、表演方向、灯光、声音KEEP及open/close states保留。修复动作明确为纸先落空台面，再提饭离台、平移放纸上，最后连纸推近。`coverage-retake-004/director-coverage.json` 通过现有coverage validator：整集276秒，原31单元由S01拆成四个摄影单元后为34；这是authoring预算，不是给native对白强加秒数。

沿同一canonical项目追加可复用 `/2` authored coverage supersession（`/1`旧美术receipt/hash保留）：绑定003已知FAIL的exact request/fetch/paid/latest experience/QA与新target intent/acceptance，同D图像SHA；允许变化限于动作progression、摄影和cadence，保留未失败规则和全部旧FinalOutput requirements。003旧paid/fetch/两份experience保留，封存原因仍为用户改版，不伪造质量证据补齐或UNKNOWN恢复。随后QA `3-coverage`、同Project/Shot revision3、原budget1500→2000、原累计quota3→4；没有新建project/task归零、替换Provider或复用permit。

精准初验116 PASS、相关模块78 PASS；独立native `reviewer_xhigh` R1发现CVR-001：嵌套model_copy可绕过hash-only校验，潜在写后strict-reopen失败。Parent用公开closure负例在临时fixture复现，改为写前完整JSON重验并采用重建结果；坏bool、camera enum、acceptance hash均证明Manifest与receipt目录写前不变。最终精准95 PASS（4个刻意坏实例序列化warnings），R2 finding set为空；263个实际runtime源文件与18路径候选冻结核对，actual全历史离线clone的标准locked submit guard通过，所有软件验证0 Provider effects/permits。失败及中间日志原样保留，不冒充通过。receipt为 `coverage-retake-004/software-verification-receipt.json`、`native-review-receipt.json`；非完整套件，源码尚未commit/push，待用户认可片效后按Final-output-first再完整工程验证。

真实第004次submit已ACCEPTED，当前总4次；native新节点 `node_svdkkk4xrp`，binding `497d8fffb13b5471f1bac0ca073d510f82fd5a77e8357d72cb910d40e781f46c`，submission fingerprint `eae1e40bb31d168f1e8df71df6dd0c4e1b51a4b282bbb410ffb0ce4ae3c4f220`。Exact compiled prompt三句各一次、无台词时间字段、D首帧相同、`seedance_2.5`16秒480p和原生声音KEEP的lint全通过。192CRD为本次平台报价，四次报价合计768，实际结算待确认，内部2000上限不作费用。旧audio UNKNOWN与所有reservations保留，无新增生图或音义调用；无Production activation、P6、Final Acceptance或公开发布。

## Coverage Retake 004 — Media Result

第004次原片已落盘，SHA-256 `06168bd113436e755cfca82c198677544f95cd82c76c216c65a131a6c59170a3`，12,543,222bytes，16.065秒、854×480、原生AAC双声道。交付为 `outputs/shizhen-episode01/失帧-第一集-S01-切镜重拍版-Seedance2.5-16秒.mp4`，与canonical fetched原片逐字节一致，未改音轨、剪辑、裁画或重编码。版本索引将003保留为FAIL历史，当前指向004。

已显式调用project-local `video_analyze`（0.5秒33帧）和 `video_extract_frames`（0.1秒161帧），精确MP4一致；actual MCP结果位于 `coverage-retake-004/exact-MCP-analysis.json` 与 `contact-MCP-tenth-second.json`。实看确认双人关系→林序回应→店员脸手动作→林序反应四机位，三处硬切分别在2.9–3.0、5.5–5.7、13.3–13.5秒区间。自动scene_threshold0.4只报1scene漏检，不用此数字抹掉实际切点。

8.9秒纸先放在旁边空台面；9.6秒左右饭团由双手提起，10秒左右纸上方可见清楚悬空路径，约10.6秒放稳后连纸向林序推近。逐项查看9.3–10.8秒0.1秒样本，未见003那种纸从饭团上方直接穿到底下。Gate的action / identity / space-camera / story-scope / coverage为可见证据PASS；performance / sound / D-art仍NOT_EVALUATED，需正常速度播放确认自然度、三轮实际对白/说话人/口型和高级动态观感，不把原生AAC存在或未转写时speaking_duration0视为听音结果。

经实际MCP review bridge将8项观察及diagnosis追加至原Manifest，standard reader读回仍4次真实paid submit，旧001–003媒体/费用/评价与audio UNKNOWN全部保留。`coverage-retake-004/post-media-gate.json` 整体NOT_EVALUATED，不提交下一剧情Shot；evidence-only未评估不触发重生成。未运行全套工程验证、未stage/commit/push共享改动，待用户认可片效后执行对应工程验收；没有公开发布、Production activation或P6/Final Acceptance。

本稳定checkpoint使用 `record-ai-video-session` 更新现有primary record，自动 `distill-ai-video-learning` 为 `no_candidate`：新样本只证明本片执行了coverage和可读物理路径，seed不可控且摄影与动作同时改动、听音/动态满意度未评估，不足以推广为通用模型成功率；未改学习规则、未写全局memory或刷新RAG索引。

## HD Output Revision — Engineering Boundary

当前共享执行原只支持换首帧的visual `/1` 或真实FAIL后的coverage `/2`；其compiled delta不允许output_requirement，不能用新task/project归零、伪造FAIL/all-NE、换图SHA或裸transport实现HD。按用户本轮明确授权增加可复用resolution-only `/3`：typed ResolutionRevisionTarget严格JSON写前重验，只允许adaptive档位升高，保持其他output、exact prompt、同D图像bytes、GenerationIntent及raw QA；new same-ID goal保留旧全部requirements。旧004以用户要求改版封存，5PASS/3NE观察不改，所有paid/fetch/原始MP4仍在。

新binding严格保留完整known history、used4/ceiling5、零resample；锁内重开exact `/3`及旧request/fetch/paid/QA/experience/currentgoal/output/firstframe。正常same-semantic Shot metadata revision允许revision/hash/provenance和对应Shot asset ownerhash衍生变化，intent、constraints、像素与其他字段不变；这用于产生独立generation identity，避免复用004。Project/Shot现为revision4。原budget2000→3500、原quota4→5都由既有committer owners完成；新内部单次1500只是operator bound，旧边界与consume保留。

必要静态和局部验证：冻结前123 tests PASS，旧decision/execution81 PASS，实际四paid全历史离线copy2通过canonical closure、reopen/replay、prepare/start、quota与submit锁，0permits/POST。copy1曾因同Shot revision生成ID冲突而被正确拒绝，原copy与失败日志保留；没有影响实际project。独立native reviewer_xhigh R1找到RRV-001：newgoal proposal原作用于production，但exact `/3` guard仅qualification。Parent确认后把识别限定qualification，真实Resolver production负/qualification正对照先红后绿；最终针对改动111 tests PASS、2个故意坏model_copy序列化warnings，R2 finding set为空，273 runtime/input bytes已核对。

receipt owner为 `HD-execution-005/software-verification-receipt.json`、`native-review-receipt.json`、`prepare.json`、budget/quota extension、`submit-output.json`；离线证明为 `HD-validation-005-2/validation-receipt.json`。实际binding `a40ff00cf2818ab494257649e4c91e2c4d60bd90619a3d103406252fc4fa1f5a`，当前新片尚未完成验收。新执行slice源代码未commit/push，按Final-output-first待用户认可HD效果后再完整工程验证；规则docs已单独推送，既有Suno policy mapping审计缺口未顺手改动。

## HD Media Result — 005

第005次新片已fetch，原片SHA-256 `15c7c21ea8ef526d641d5a1565cbb4ec93ea4ee63b34fc9c7a0d73f2b21efb0b`，51,142,682bytes，1920×1080，16.065秒，H.264与原生AAC。交付 `outputs/shizhen-episode01/失帧-第一集-S01-1080p高清版-Seedance2.5-16秒.mp4` 与canonical原片逐字节一致，未从480p放大、插帧、裁水印、改声轨或重编码。ffprobe解码385帧，平均23100/961≈24.04fps；`r_frame_rate=60`不是原生每秒60个画面，原片帧间隔并非恒定。后期最终24fps CFR/音频导出规格须在用户认可HD原片后经原composition owners完成，本次不伪称已合成终版。

显式project-local `video_analyze` 0.5秒33帧和 `video_extract_frames` 0.1秒161帧已绑定exact source。可见四构图硬切区间3.0–3.5、6.5–7.0、13.0–13.5秒；约9.0秒纸先平放在旁边空台面，9.9–10.4秒双手提饭离台并移到纸上方，约10.6秒放稳，之后连纸推近，末尾反应有笑意。实际逐项查看9.7–11.0秒0.1秒样本，未见003式纸穿饭团。身份、可见动作、空间接触、故事范围和coverage五项PASS；performance、sound、D-art三项仍NOT_EVALUATED，完整原速表演、三轮实际对白/说话人/口型与高级动态观感待用户播放。自动scene阈值0.4仅报1有漏检，按实际相邻构图判定，不用数字代替切镜审看。

同actual MCP bridge将八项观察与diagnosis写入原Manifest，standard reader读回仍5次真实paid submit；`HD-execution-005/post-media-gate.json` 整体NOT_EVALUATED，source resolution另有technical PASS，不进入下一剧情Shot。原native AI生成角标及来源信息保持；未取得官方无显式角标导出，不冒称无水印。未重试旧audio UNKNOWN，不把AAC存在、ASR未运行时speaking_duration0或工程测试当真实听音PASS。未发布、无Production activation/P6/Final Acceptance。

本次只新增一次HD视频submit，报价1024CRD，实际结算待确认；累计前4次各192加本次共1792只是报价总和，原内部2000→3500上限不作费用。`cost-summary.json`、旧完整费用摘要及其SHA保留；无新增image/audio calls。源码和本checkpoint记录待用户认可HD效果后完整工程验证，再按owned paths commit/push；共享规则已单独提交推送5bf4cd7，未夹带其他窗口改动。最终证据为 `HD-execution-005/delivery-verification-receipt.json`。

使用record-ai-video-session更新primary record；automatic distill-ai-video-learning为no_candidate：仅一例HD新生成，原seed不可控、新profile/node/resolution共同变化，且完整声音和动态观感未验收，不将局部像素/接触观察推广为通用成功率。未写全局memory或更新RAG索引。

交片前检测到另一窗口已提交Suno/music测试映射，`.agent/harness/policy.yaml`与R2审查snapshot不同；其余272个封存执行源码/输入均匹配，MP4 bytes也未变。保留原review hash及 `HD-execution-005/concurrent-governance-drift.json`，不刷新旧证据冒充当前完整工程验证，未回滚或夹带该并发修改。

## Caption Review Delivery — 2026-10-26

使用open-video按实际音轨组织字幕；本地缓存Whisper medium输出真实word时间，原始输出保存在 `caption-review-005/whisper-words.json`。四句显示文本为“慢点，里面烫。”“谢了，袋子不用。”“垫着吧。”“上回有个人，直接给扔地上了。”。字幕沿CaptionImportRequest、Registry、唯一ResolvedTimeline、原HyperFramesAdapter输出，不直烧字幕旁路、不重生成，不把ASR当作新的人工听音。

开发审看入口复用qualification capture与replacement_audio_preview。新增能力只允许exact captured MP4派生的一条DIALOGUE音轨配字幕，精确匹配input IDs、source SHA与完整样本窗口，0增益、无fade/duck；voice_sources与原Production activation禁止继续有效。独立preview project通过唯一committer bootstrap/追加字幕修订，原source Manifest不变，没有复制预算、attempt或清除旧UNKNOWN。这里不建立第二renderer或时间线。

保留全部已知失败：本地render001样式缺schema_version；002/003调用到环境中2021版Conda FFmpeg，不支持新版HyperFrames抽帧的 `-fps_mode`，coverage为0并拒绝输出。命令级PATH使用既有新版FFmpeg后render004成功，逐帧发现cue3与cue4在frame282重叠，故004未交付。经canonical append字幕revision3，显示边界对齐24fps并给相邻两句一帧guard，原word ASR证据保留，显示cue诚实省略word records；render005复验frame55/56、88/89、122/123、169/170、254/255、281/282/283/284、339/340/341，无重叠，中文字形与位置清晰。没有关闭coverage Gate、修改模型画面、插帧或掩盖旧失败。

实际HyperFrames0.7.103 lint/check均0 error/0 warning；project-local MCP对最终exact文件抽32帧并核验1080p/24fps。0–16秒混音PCM与原提取音轨逐样本相同；AAC存在1024 samples=21.333ms偏移，小于一帧，经偏移对齐最终全轨相关系数0.999126，不能把未经对齐的旧correlation0.014误作内容变化或PASS。004与raw在0、6、15秒字幕区以上样本PSNR约37.89–38.78dB，仅作抽样证据，不称全片像素相同。最后实际对白14.16秒结束，16秒之外仅原结尾空闲/AAC padding未进入该16秒审看窗口。

本轮精准4项通过、repair相关26项通过；Parent关联回归384 PASS、3 SKIP、111.45秒，覆盖preview/qualification fences、composition、caption、source audio及HyperFrames。命令级预加载已安装系统libfreetype解决已有Conda/native libass链接环境，未改系统或跳过失败测试。Docs contract与owned diff whitespace通过。按SUBAGENTS Risk Gate为NATIVE_REVIEW_NOT_REQUIRED：本轮仅preview能力，paid/credential/Manifest/activation owner未改；来源拒绝、时间窗及旧activation禁止已有相关验证。未声称完整工程回归或人工字幕副本审看通过。

Git仍有本任务与其他窗口混合的既有未提交依赖；本轮新增守卫挂在此前未提交的静态旁白preview入口，未将其归为本任务所有。为保留归属，没有stage/commit/push混入该依赖；完整工程验证与源码提交仍未完成，当前仅交付已核验的字幕审看媒体。用户HD原片认可已记录，旧文末“待HD原片认可”已被本段取代，不将工程未完成误作用户未认可。

使用record-ai-video-session更新现有primary record，distill-ai-video-learning评估为no_candidate：字幕修订同属一个已生成源的派生链，不构成独立模型实验或可推广成功率；未创建学习占位或改全局memory/RAG索引。
