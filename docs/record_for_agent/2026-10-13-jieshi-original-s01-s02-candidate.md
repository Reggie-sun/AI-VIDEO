---
record_kind: media_experiment
topic_id: jieshi-original-s01-s02-fidelity
learning_eligibility: eligible
evidence_index_version: "1"
---

# Jieshi Original S01–S02 Candidate Record

Date: 2026-10-13

## Current Official H3 Max First-Frame Result — 2026-10-17

用户对已展示的 H3 Max CN 最多2次、零重抽单元回复“可以”，包括首帧模式不能并用动态白模的逐镜例外。实际只执行 A 一次：`canvas-1693d62e38fffba5c59869059653049cece057cb`；新证据根为 `runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-mode-pair-20261017-001/`，下称 A unit。新增视频 POST1、图片/音频生成 POST0、音频理解调用0，历史视频累计18，S02仍0。没有把未用的第二次改配其他模型、素材或实验。

### Exact Mode And Preserved Requirements

共享 Canvas authoring、Planner/Router、compiler 与 `VideoGenerationService` 完成此次输入和执行，没有新增源码或故事执行脚本。原 PNG SHA `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923` 仅作为一张 `first_frame`；不是将九个身份 alias 自动去重。native 为 `MiniMax-H3-Max`、`duration=5`、`resolution=768P`、balanced，`content=[text, first_frame]`，不发送 `ratio`，无 `reference_video`。逐镜记录官方互斥约束下的动态白模例外；v015及旧绑定/结果保留在历史，不能宣称本臂继承了其动作轨迹。

重开历史原始首帧 snapshot `b1e834a4e215f9a7b7104ddf2fec71f3cf687efdad704a64d921f4b4b6aabaaa`，原两段文字逐字保留；prompt SHA `2a54252ee51ac0d9c1a193ff0b3060aa80ae94ab3570986c588b49b162f50f59`。只移除 R2V 专属的参考职责附录、alias与视频 chip，并同步真实 first-frame 职责；S02改回与该 snapshot 匹配的历史未采用占位资产，没有媒体或 accepted state。原15项 QA/hash `dafe8462ce182ac1e44a755f91eef68b8c65dc135063f210a263a278900f639d`、广播0.1–2.7秒及采用 frames0–71/0–3秒不变。`A-source-preservation.json`、`A-authoring.candidate.json`、`A-prepare.json`、`A-native-preview.json` 可重开 exact映射与限制。

两个准备错误均在 POST前被原 guard 拒绝：R2V原稿不能直接改标签冒充 I2V；选择 `approved_keyframe` 后仍须 Shot 的 `required_asset_roles.first_frame` 精确绑定同一图。通过既有 owner 修正数据后正常编译，没有放宽 guard。内部 ledger 总上界300,000,000→350,000,000 CNY microunits、单次50,000,000；task ceiling6→7、历史已用6保留且本次后为7。它们只表示新授权下有限 operator上界，不是报价、余额、账单或重铸旧额度。

### Actual Media And Gate

一次 CN POST于 `2026-10-16T16:41:45Z` 发出，HTTP200；body SHA `3ab700490614a2ad7c93483fb0bdf405659cc33d6c2f63b226eed18b65800bac`、2,822,118 bytes，与封存 preview一致。只查询和下载同一 task。下载仍按 exact结果host的本次公网DNS答案、public IP pin、TLS/SNI、无凭据/无redirect GET，未改全局DNS或重新生成。

Exact MP4：`production/state/video-generation/fetch/files/e3407abea389e9098f74bdaf25281d741030bbb09830e32cdc6faf793c25df3c.mp4`（相对于本 run root），5,148,741 bytes；H264、768×1344、24fps、124帧、container5.184秒，AAC32kHz stereo。实际4:7，不能写成精确9:16或原图像素级复现。显式 project-local `video-analysis.video_analyze` 取得21个0.25秒样本；关闭 transcription与audio understanding。另用既有 FFmpeg 解码原生 frame71（SHA `a7764381c5e55eb8de0a8c20243713be4fb26e1b2db081bb109d14b6f952fc34`），没有用5秒尾帧代3秒切出。

`A-MCP-response.actual.json` 是本次真实工具响应；canonical bridge重开该响应，经受控 presentation实际展示并回答全部15项，登记 `generation-evaluation/2`。QA为 **6 PASS / 2 FAIL / 7 NOT_EVALUATED**：

- PASS：camera、close-anchor、identity、phone、source-output、space。此次观察保留了原八人，包括此前缺失的灰帽衫陈立；可见外观/衣着和空间关系稳定，右手唯一手机保留。close-anchor只证明Lin存在，source-output只证明原片技术合同与采用配置；均不代其他验收。
- FAIL：close-gap、reflections。约1.5秒起可见抬起手的玻璃幽影；原生frame71仍在完成抬手/伸指，3.0–3.5秒继续变化，没有在原3秒切出前完成并保持所需悬停。物理2cm距离未被伪造测量。
- NOT_EVALUATED：badge、broadcast、broadcast-window、gaze-lips、left-hand、native-track、other-props。工牌细字、完整音义/精确广播边界、全程目光嘴唇/手部解剖及非接触、陈立被遮挡的手机/耳机细节均未齐证。未复用旧MP4的已消费Gemini音频单元，未把AAC存在或工具成功当听音；human完整1.0x验收仍NOT_EVALUATED。

canonical诊断为 `EVIDENCE_GAP/QUALITY_FAILURE`，evidence `0bc14ce939c3709e2b4b862f9b0ad3592498ca71e360ab9ae8b2ca857f79bc95`，all-required-pass=false。原 committer 已明确 abandon；Manifest116、Project16，attempt failed / phase validate，无activate、accepted state或S02提交。缺声音/细节的补证不能修好两个已知视觉失败，故不为此重生。actual presentation、逐项理由、诊断和标准重开分别见 `A-qa-presentation.actual.json`、`A-operator-qa-answers.json`、`A-qa-diagnosis.actual.json`、`A-stable-media-checkpoint.json`。

### Comparison And Learning Boundary

旧 CN R2V 的 profile/native本来就已发送 `ratio=9:16`；`effective_output.ratio=adaptive` 是输出能力投影，不能反推请求比例。按原样重做 B 只是随机重抽，不增加模式或比例条件，故未执行第二次。具体官方核对与反例见 [Mode Pair Research](../research/2026-10-17-official-h3-max-mode-pair.md)。

A这次保留陈立而旧B缺失，只是有界观察。两次同时改变模式、native references、profile/stack、R2V附录且seed不受控，不能断言首帧模式单独造成改善，也不能证明跨项目质量；两者均未通过整镜。现有控制映射/模式预览工程已完成，单镜、连续镜、完整故事与human验收均未完成。后续应先明确可解决手部反射与3秒动作落点的具体输入或制作策略，再另封有限验证；当前未用槽位不自动授权其他实验。

按 `record-ai-video-session` 更新同一主记录并自动评估 `distill-ai-video-learning=no_candidate`：新增一次独立媒体，不把proof层或历史B另算新调用；现有资料只支持上述有界差异，未形成超出现有完整Gate/模式限制的新可采纳工作流机制，不制造通用质量规则或修改Skill/Policy/Gate。既有本地H3 first-frame/open-state claim排除paid/其他profile，Vidu对白claim排除其他模型及人物/倒影质量，本次不是其scope内的material update。此次无源码行为变更，Parent Risk Gate为 `NATIVE_REVIEW_NOT_REQUIRED`；现有首帧/原文保留 focused checks 8 PASS，先前通用工程 exact Harness保留其原publication边界。本文档checkpoint receipt为 `.agent/harness/runs/h3-max-first-frame-record-20261017-r1/receipt.json`；publication以该exact receipt及Git/remote SHA为准。

## Prompt-Control Audit — 2026-10-18

2026-10-19 更新：该审计提出的通用分工已由[共享实现记录](2026-10-19-production-responsibility-allocation.md)所述源码 `d082009` 实现并发布；下文“本轮仅研究”是当时阶段的历史范围。当前工程预览保留全部15项，S01/S02均明确缺 ProductionIntent，没有自动重分 stage 或放宽要求；本片媒体结果、S01 STOP、S02 POST0不变，工程 PASS不代媒体通过。

用户追问画布是否采用更宽松的提示词后，对照剧本卡、本地 authoring source、A 实际 native preview 和逐项 QA。
本记录所称两段“原文”是本地封存的 authoring 文本，不证明外部网页画布的真实提交或服务端扩写。
`source-mapping.json` 明确为 `candidate_preparation_only`；剧本 S01 卡已包含抬左手、约2cm悬停、
七人倒影保留、点名广播与3秒采用。1151字符的本地文本加51字符工牌正常态说明，精确组成 A 的1202字符
prompt（3386 UTF-8 bytes），SHA `2a54252ee51ac0d9c1a193ff0b3060aa80ae94ab3570986c588b49b162f50f59`。
因此不能把它称为外部画布的宽松原始请求，也不能把3386 bytes误报为字符数。

A 的 nominal5秒请求仅写“保持到切出”，没有明示3秒动作截止；`s01-close-gap` QA 却检查 frame71已到位。
这是真实的表达/采用窗口差异，不证明其为时序失败唯一原因；15项 QA 不是 API 硬控制字段。
官方 H3 指南允许与意图一致的细节补充，也要求清楚描述动作和参考职责；详细程度本身不证明控制有效。
当前 CN 请求的 `balanced`、本地 H3 社区经验及外部画布后台改写必须分开，不能据此宣称放宽提示必然改善。
完整来源、通用职责判断及边界见[调研](../research/2026-10-18-canvas-prompt-control-and-acceptance.md)。

本轮仅研究/输入核对，未改 prompt、QA、workflow 或 Product state，图片/视频/音频 POST均0；
A 的6 PASS / 2 FAIL / 7 NOT_EVALUATED、S01 STOP、S02 POST0保持。
`record-ai-video-session` 更新本主记录，自动 `distill-ai-video-learning=no_candidate`：
同一输入/结果链的复核不是新增独立实验，缺少提示复杂度的受控比较，不创建 Learning Claim 或采纳规则。
Parent Risk Gate 为 `NATIVE_REVIEW_NOT_REQUIRED`：只有有界研究与记录澄清，无 Runtime/授权/验收行为变更。

## Offline Authoring Repair Preview — 2026-10-17

用户要求“参考官方和社区修改”后，先核对 A 的 actual native text：原文已有约2cm悬停终态和“保持到切出”，
但没有在3秒前落定的明确动作时限。QA observable 和 composition 的72帧采用配置没有自动进入 prose；
这是 authoring 表达缺项，不是 compiler 丢弃了原已表达的时限，也不能据此证明模型失败的单一根因。
[研究记录](../research/2026-10-17-h3-action-timing-reflection-repair.md)分别核对官方 H3 Max API、H3 Base
I2VA 指南、社区时序故障及倒影漂移/局部成功反例；本地 H3 的经验不外推为 H3 Max CN 质量保证。

新的离线输入保留历史两段1202字符原文，另追加一个归属 Agent 的技术 text part：原左手动作在前2.5秒内
完成靠近、减速并悬停，随后保持至5秒；在正常保留其他七人倒影的同时，明确林砚对应玻璃区域持续显示
原空位/车厢纹理，局部排除身体和随动手影。2.5秒是生成余量，未改成新的验收门槛；原15项、0–3秒采用、
广播及摄影/人物/道具/空间要求保持。没有使用后续镜头切点语法虚构剪切，没有新增画面事件或参考媒体。
两项相连修订均属 prose 表达，尚未有媒体验证，不能分别归因或宣称已解决动作/反射。

证据根：`runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-repair-preview-20261017-001/`。
`candidate-source.json` 经共享 inspect 得到新 snapshot
`7a87575a3e382b2887dd60edffb5aeb2877a76f2d7ee7c736bccc7f70da6edc3`；旧 snapshot/hash 保留。
`candidate-authoring.json`、`candidate-author-preview.json`、`candidate-prompt.txt`、`prompt-change.diff`
及 `verification.json` 给出完整新输入、原文/新增段和只读 author/preflight 证据。
候选 prompt SHA `2c491b55c9ccb2b69692966da86f1bafe4b308f8cbef9575c3282b31498e4417`。

第一次复用旧 selection 时，既有 validator 真实拒绝 `generated copy differs from the original canvas resource`：
generated-image selection 绑定整个 source snapshot，新文字使该 identity 改变。随后由原 import owner 重开
同一 PNG 和原生成记录，为新 snapshot 准备新 selection asset IDs，合并并保留全部旧 Registry records；
原图 SHA/bytes、first-frame 职责和预定 native 输入数量仍相同，没有重新生图或直接改 receipt/hash。
S02 未采用占位图也仅重封 selection identity，原文、采用窗口和 pending accepted-source 语义没有改变；
它不成为已验收交接图，也不是新增独立人物参考。

标准 loader 重开 Manifest116/Project16 与同一 active QA 后，原 `author_canvas_project` 和
`canvas_reference_preflight` 验证新候选；Production project/Manifest 文件 SHA 前后相同。
候选 bundle 的 Project17 只是未提交的 authoring 产物，**不是已持久化 revision 或可执行请求**。
新候选 Provider 编译、resolved hash、decision/execution binding 均 `NOT_EVALUATED`；未用旧候选报告冒充
新候选 native preview，也未编造 quota。完整 prepare 仍须 canonical authoring revision、当前 limits/QA/history
及原 gates；当前新增 attempt/permit、图片/视频/音频 POST 都为0。

共享 workflow 补入[动作时限与局部异常核对](../canvas-production-harness.md#action-timing-and-selective-effects)，
说明已验证的输入步骤、生成余量与 QA 的区别、snapshot selection 重绑及纯 author preview 的证明边界。
现有 compiler 已支持新增源 text part，故未修改 runtime、Provider 选择、预算/许可、Gate 或 timeline；
没有为《界蚀》新增条件分支、执行链或经验采纳规则。正常/边界/失败路径验证与 exact-range Harness 见
`.agent/harness/runs/h3-action-repair-preview-20261017-r1/receipt.json`，结果以该机器证据为准。
Focused `tests/test_canvas_source_expression.py` 为40 PASS：新增 H3 Max/Seedance 两类 actual compiler ×
三组人物/动作/空间的6个用例，以及旧 generated selection 对新 snapshot 的拒绝用例。它们验证原 parts/
references 顺序、2.5秒补充 prose、5秒 generation、3秒 Shot/72帧采用配置及 QA 不自动增添余量 predicate；
旧 direction-only 篡改拒绝用例继续保留。fixture 使用禁止 credential/transport 的 Provider，不能证明媒体质量。

按 `record-ai-video-session` 更新本主记录；`distill-ai-video-learning=no_candidate`：本轮只有工程/离线输入证据，
没有新增独立媒体结果、受控因果证据或已验证质量机制，不创建 Learning placeholder，不修改 Skill/Policy/Gate。
Parent Risk Gate 为 `NATIVE_REVIEW_NOT_REQUIRED`：仅既有 authoring seam 的回归与输入/操作说明，未更改 runtime
或持久化/付费控制，主要失败路径可由 focused tests 和只读真实候选核验；代码 mapper/研究 writer 不冒充独立 reviewer。

当前媒体仍为 A 的 **6 PASS / 2 FAIL / 7 NOT_EVALUATED**，S01 STOP、S02 POST0；单镜、连续镜、完整故事、
通用模型质量及 human 1.0x 验收均未通过。若继续实证，最小新单元为同一 H3 Max CN / 768P / nominal5秒 /
原 PNG first_frame 的1次新视频提交、零重抽，按新 exact preview 重走全部付费前置条件；需要声音语义证据时
另封1次 qualified Gemini `gemini-3.8-flash` audio-understand 单元，不能复用旧消费。两类新外部效果均尚未授权；
全部15项及 exact采用frame71须重验，human完整1.0x听看另验。不沿用未执行B槽位，不用新工程PASS解除旧STOP。

## Shared Control Engineering — 2026-10-17

通用参考控制审计、模式取舍预览、semantic reference到native index映射与多场景工程验证已记录在
[Reference Control Audit And Preview](2026-10-17-reference-control-audit-and-preview.md)。源码 `473ed99`
已发布并通过 exact Harness；该工程checkpoint新增图片/视频/音频 POST均0。随后新授权的一次首帧实证见上节；
下方旧R2V原片4 PASS/5 FAIL/6 NOT_EVALUATED及历史STOP保留。工程完成不证明本片、连续镜、完整故事或通用模型质量通过。

## Current Official H3 Max Result — 2026-10-16

本节是历史R2V结果；最新首帧结果及当前STOP见顶部2026-10-17节，旧结论和证据不覆盖。

用户明确改用官方 H3 Max，并确认 Key 来自国内站 `platform.minimax.cn/console/access`。当时最新原片来自官方 `MiniMax-H3-Max`，已实际落盘并登记逐镜 QA；下方 METASO/白模结果全部保留为历史，不是 accepted S01。证据根为 `runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-cn-S01-20261016-001/`，以下简称 CN unit；国际站前序证据在同 run 的 `official-h3-max-S01-20261016-001/`，简称 IO unit。

### Exact Input And Region

本次继续使用原 PNG `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`、光学白模 v015 `8b8d1e43d5295109fceda1755bc41e005f6e927ef2b8e657d0328f288aa50e33` 和原 native prompt `2eae000eb65333debbfa61ba4bf072aae60241d1304574a3fc47634e2516e6e1`。九个 image aliases 仍是同一 PNG 的九份绑定，不是九张独立参考。原剧情十五项、点名广播、悬窗动作、摄影、字幕职责均保留；不以自创抬手机测试代替原开场。

官方 H3 Max 最短标称5秒，因此仅将 `s01-source-output` 的技术请求时长4→5秒，QA revision3/profile version2，hash `dafe8462ce182ac1e44a755f91eef68b8c65dc135063f210a263a278900f639d`；原采用仍0–3秒，广播仍0.1–2.7秒，其他 required IDs/proof/tolerance 不变。旧 QA、source expression 和历史结果不覆盖。exact body SHA `3bb3d1c9688828c3ebdd0faa3ee81c7c4cb21fc49102492f70b8a6c733226675`，25,908,691 bytes；IO→CN 未改变 body、模型或素材，仅重封地域/profile/stack/credential reference/egress/恢复及有限计数。CN profile SHA `61b717b08a663afc5efdcba784f7fbefdaff3067eb377aced30499dbadd2934c`。

最初国际站 `api.minimax.io` 一次 POST 返回 HTTP401，attempt `canvas-ced3bd552a905aa189c2e3b5ed23f2c64273d43f`，canonical `paid_provider_known_no_effect`，没有 task/MP4，不是 UNKNOWN。用户确认国内 Key 后按[国内官方接口](https://platform.minimax.cn/docs/api-reference/video-generation-v2-create)显式选择 `https://api.minimax.cn`；不是自动 fallback。凭据仅经用户指定私密文件的 exact injected supplier，CN public reference 为 `MINIMAX_H3_CN_API_KEY`，不输出或持久化 Key。另一次 paid preview 错用 request hash 的准备错误在任何 intent/reservation/permit/HTTP 前被挡住，修正证据保留在 IO unit `successor-001/preview-correction.actual.json`，不计为第二次 POST。

### Actual Media And Gate

CN attempt `canvas-c5f04a3750cb384d4bf55ae00424511ede0f818c`，实际一次 POST/HTTP200（14:03:19–14:03:21 UTC），14:04:15 UTC观察 succeeded。paid submit receipt `aa4fea276e0220266fc81f47c6c66c32f9bbdbb773c631f6160b8d86101e4092`。下载遇到 exact OSS host 的 fake-IP 解析后，仅在该次 fetch 内选择 HTTPS DNS 的公网答案，保留公共 IP pin/TLS/SNI/无凭据/无 redirect，成功取回同 task；未重新生成，未改全局 DNS。见 CN unit `download-DNS-selection.actual.json`。

Exact MP4 为 run 内 `production/state/video-generation/fetch/files/f0685279ab5d0b2256951ed99bde45afc721a7135d654533296c11c038f86725.mp4`，SHA同文件名，7,124,743 bytes，H264、768×1344、24fps、124帧，container5.184秒、AAC32kHz stereo。实际仍4:7，不能把请求9:16写成输出精确9:16；没有裁切/补帧/锐化来改判。raw5秒也不是原采用3秒、两镜7秒或前15秒成片。

已显式调用 project-local `video-analysis` MCP，检查21个0.25秒样本并单独解码原生 frame71；随后 fresh MCP 带一次真实音频观察，同一 exact response 经 controlled presentation 登记全部十五个 canonical 问题。没有重发音频以生成“更好答案”。canonical QA 为 **4 PASS / 5 FAIL / 6 NOT_EVALUATED**：

- PASS：`s01-camera/s01-close-anchor/s01-phone/s01-source-output`。仅证明实际可观察的锁机位广角构图、closing character presence、右手膝上唯一手机及原片技术合同；不代悬窗状态或完整动作验收。
- FAIL：`s01-close-gap/s01-identity/s01-other-props/s01-reflections/s01-space`。首帧就只有苏遥和五位坐姿乘客，原灰帽衫邻座陈立及其手机/耳机缺失；抬手时玻璃中出现手的幽影；frame71仍在抬手，后续3.25–4秒继续运动，不能换用5秒尾帧冒充3秒切出已到位。
- NOT_EVALUATED：工牌细字、完整广播声学/来源、精确广播边界、完整目光/嘴唇、全程手部解剖/非接触、列车环境声/拟音/完整音轨质量。未从参考白模、无新增对白观察、decode 或 waveform 推导这些项通过。

experience `97bb8a12a27d8273851b46d9cd315584f4bcdad5195412fbc56ce26b6f228ff1`，evidence `dc92ece0dd73f7da47d19907fb7329fbd7d7c04d37f7c5de5051f23b5615fe81`；见 CN unit `qa-presentation.actual.json`、`operator-qa-answers.json`、`qa-diagnosis.actual.json`。diagnosis 同时为 `EVIDENCE_GAP/QUALITY_FAILURE`，all-required-pass=false。缺人、倒影和动作失败不能通过补声音证据修好；没有 activation、accepted-state handoff 或 S02 submit。原 committer 已按明确失败理由 abandon，本窗口标准 loader 实际重开 Manifest103/Project14、attempt=failed/phase=validate，quality rejection `f3e5644888748ba7d385479deb8a2873ac587f7d9ae62885de5d94433d2c2c40`；全部 FAIL/NOT_EVALUATED 和原片保留，见 CN unit `stable-media-checkpoint.json`。

### Audio Evidence And Limits

现有 qualified development operator 经 fresh project-local MCP 对本 MP4 仅调用一次 `gemini-3.8-flash`，requested/response model 相同，完整 PCM SHA `2a7be0f5e00c04f4b736c954f215bf38316abe59343539cf83bfe2b1aa744f8a`，response SHA `f2e6e182d6f4386dde6b649d688801c1c49e170d4ba134fbdb5cfaa39b02e5f1`。盲观察为一遍女声“林彦，请在终点站下车。”，估计0.0–2.5秒、neutral/automated/flat，background_sounds为空。同音转写不证明姓名读错；估计时间不满足精准0.1–2.7秒证据，空环境观察不证明环境声保留或不存在。

当前UID D-Bus owner 已核验，factory/unit/intent/model/media root 显式传入实际 stdio server，supplier仍为 exact Secret Service 引用。未新增依赖、调用本地识音模型或声称 Codex 原生听过。`audio-operator-001/` 保留单次 consume/outcome；预配置 USD50,000 microunits 仅内部 upper bound，不是价格或账单。人类完整1.0x听看仍 `NOT_EVALUATED`。

### Shared Repair And Proof Boundary

原生 worker 修复“已提交失败 A → 未提交准备 B 被关闭 → successor C”恢复缺陷：submitted semantic baseline 与直接 closed-unsubmitted predecessor 分开绑定，canonical owner 核验连续无副作用链、same Shot/task、exact closure、grant消费者，仍拒绝 open/unknown/fork/skip/reuse。新增 accepted-FAILED→closed-preparation→canonical paid-submit/reopen-poll 回归先 RED 后 GREEN；该回归使用离线 Provider double，只证明实际 committer 生命周期，不是假称又一次真实云端调用。source hashing 在单次 projection 内只计算一次，保留原 hash、无全局 cache。官方 adapter 显式选择国际/国内地域，默认省略字段以保留旧 profile hash；没有第二执行链、timeline、状态库或 renderer。

源码 checkpoint `d4ed98406338cb7bb97649509d84ea8c55f9f5a8`；最终 exact range 为 `c8221c34d72c2889dfe7e92eec685a67476814d5..d4ed98406338cb7bb97649509d84ea8c55f9f5a8`，receipt `.agent/harness/runs/official-h3-max-cn-lineage-20261016-r1/receipt.json`。实际18项策略检查为17 PASS/1适用性 skip；`harness-receipt` 的 `complete_completion_proof/fresh/artifact_integrity/scope_worktree_clean` 均为true。已 push 到远端 main，并用 `ls-remote` 核验 exact SHA 为上述 d4ed984。独立 native `reviewer_xhigh` 的 R2 finding 经 Parent 确认和回归修复后关闭，最终 finding set 为空；默认3轮后基于独立调查及新 RED 证据明确有界延长到4轮，未重置历史。完整闭环见 IO unit `implementation-review-closure.actual.json`。这些都是工程证明，不是媒体 PASS。

Architecture Gate 为0 error/1 WARN：已有超长 `_state_commit_video.py` 增加14行 canonical integration，独立链核验放在既有 `_state_commit_video_unsubmitted.py`，保留原子事务边界；未改 grandfathered baseline 隐藏告警。前序官方 adapter `0194c18` 与单次 projection hash 修复 `c8221c3` 已分别通过 `official-h3-max-provider-20261016-r1`、`official-h3-max-source-hash-20261016-r1` exact Harness 并 push/核验；这些前序证明不替代最终 lineage/CN 范围。

本窗口两次视频 POST 分别为 IO401 和 CN成功，历史15次保留，累计17次；S02仍0。task ceiling 经 canonical extension 4→5→6，物理调用不退回；内部 CNY 总 upper bound250,000,000→300,000,000 microunits、每次50,000,000，CN地域恢复不再扩 monetary cap。新旧 permit/intent/profile/预算及已消费记录分别保留，未把账户余额、订阅或 Key 存在当作授权。

`record-ai-video-session` 更新本主记录；`distill-ai-video-learning` 为 **no_candidate**。已检索同族及反例，并重开 `runs/jieshi-s01-h3-horizontal-20260906-007/media-gate.json` 与 `fetched.json`：旧 artifact `204718617ac34ac437d30a2b5d6c6d6744c5fde027b04a56308ea52e83e007e8` 的七人倒影有历史局部 PASS，而整片仍 FAIL；这不是当前输入的 accepted source，也不支持模型绝不能保人/白模必然无效。当前 Max 仅一次实际成片，和 METASO 同时变了 Provider/model/请求时长等条件，不能升级为受控优劣结论或有效工作流修复。参考层、视觉、音频和工程证据不多算独立 attempt，不新增 Learning placeholder、Skill/Policy/Gate 或 RAG rebuild。

当前最小恢复条件是针对 missing-Chen、镜面例外和3秒动作建立可审阅的新输入/参考方案，并封存新的有限调用单元；不是删要求或沿用消费过的 permit。原前15秒映射仍 S01 0–3、S02 3–7、S03 7–11摘耳机否认、S04 11–15其他乘客如常。canonical trim/接点、字幕、HyperFrames 声画片、完整故事 AC-7 和用户验收都未完成。

本次记录独立提交，文档 exact range 的验证入口为 `.agent/harness/runs/official-h3-max-cn-record-20261016-r1/receipt.json`，实际结果以该 receipt 与 Git 为准。foreign index patch SHA `56179b0cbeb934271e3526d00b65e8d1a1314f0608bf568655443c53ab2f30b8` 前后保持，未提交他人的 AGENTS/playbook 或其他 dirty；未为记录新增 Provider/media 调用或重复工程大测试。

## Prior Optical Whitebox Repair Result — 2026-10-16

以下是先前 METASO 单元；当前最新原片与 STOP 见上方 Official H3 Max 结果，旧 verdict/消费及素材保留。

用户同意上一轮针对倒影对应、手窗距离与完整构图的修复建议（“可以”），模糊继续暂不处理。本轮沿现有共享inspect/author/preflight、Registry、Planner/Router、adapter、committer及逐镜MCP执行，新增 **一次** METASO `MiniMax-H3` 视频POST，零重抽、零S02。证据根为 `runs/canvas-jieshi-original-s01-s02-20261013-001/whitebox-repair-S01-20261016-002/`；以下旧白模和无白模单元继续保留，不是当前接受源。

### Reference And Exact Inputs

Blender 5.2.1LTS/build `9e2066aef7ef` 将旧窗后替身改为Cycles真实镜面：其他七个proxy通过镜面反射，林砚及其手不参与glossy/shadow可见性；背景proxy不直接出现在camera rays。这是明确的参考层可见性控制，不声称现实世界自然出现无倒影。保留可编辑blend、普通反射对照、作者几何及所有失败版本。v014的中段手部遮挡经实际MCP发现后修到v015；这些版本不计为多个独立模型实验。

最终参考 `v015/S01-whitebox-optical-v015.mp4` SHA `8b8d1e43d5295109fceda1755bc41e005f6e927ef2b8e657d0328f288aa50e33`，402,825 bytes、720×1280、24fps、96帧、4秒、无声。28mm锁机位、高1.3m；左手轨迹向体侧展开，2.25秒到位并保持，作者掌窗几何约0.0200000015m。为减少参考遮挡，对面五人proxy沿world X平移−0.85m、杆平移+0.21m，座序保持；这是公开的metric blockout适配，不能冒充原PNG像素不变或输出空间已合格。全部96帧投影审计和16帧实际MCP用于参考核对，不证明所有身体部位无遮挡、身份/目光/口型或human正常速度验收。见 `reference-review.actual.json`、`v015/reference-geometry.actual.json`、`v015/reference-mcp-analysis.actual.json`。

新source snapshot `302772dd855b9ae60dd9b15b5c4319cae63c0b781f20b528c4cdad2adc908980`。原S01前两段正文逐字不变（SHA分别 `f9e21d1fe7ea7c752a061bfc3a48b3a40f8aa93df7ec1334104f92b6823f5833`、`b1a5644b2644e4d821c1d0599231dff57d38c149ae97e9475369e21ef71146b5`），S02原文不改；只修新增参考职责，明确七人倒影、陈立不转头/不加眼镜、竖屏及原音频/字幕职责。原PNG仍 `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`，九个逐人物/场景alias仍发送 **9份相同PNG字节**，不是九张新图；本轮新alias经既有generated-source copy保留来源。另有一份上述白模video input，仍为R2V，未假称硬首帧锁。

当前adapter及[官方节点](https://github.com/meta-sota/ComfyUI-MiniMaxH3-API/blob/main/nodes.py)支持显式ratio；本轮profile从`adaptive`改为`9:16`，4s/768P/24fps nominal/native audio、`context_ir=false`保持。profile SHA `10c0011235eaf91a61c8845b8780b84eef8b9a24e001d2bd39a8cb9cdb833fed`。exact native prompt SHA `2eae000eb65333debbfa61ba4bf072aae60241d1304574a3fc47634e2516e6e1`，actual wire body SHA `eb28fe2f954b74c047483384f6dee61993cd564f809583a35b02c8617b3e5101`、25,908,669 bytes；图片、视频与原文实际进入输入的核验见 `creative-preflight-and-lint.actual.json`、`native-preview.candidate.json`。静态保留不代原剧情执行成功；同时改了profile、prompt、image/media bindings及stack，seed不受控，不是isolated A/B。

### Runtime And Findings

Canonical attempt `canvas-65bcbc798a2b1935c7fbd18fc54eeafc803c5b72`，resolved hash `c9e6d24c06de49608c555c8f6f2bcb7b3b73dbced154c4260001b2c2c4b1ed7a`，paid submit receipt fingerprint `905ba4c0ba5a73e2438686862d182b1968fc3f891a3231ff92e40821d4d5d932`；actual POST1/HTTP200，正常GET返回succeeded。submit后的显示代码误读不存在的`task_id`属性产生本地AttributeError，但已保存submission且canonical已ACCEPTED；`submit-report-correction.json`明确纠正，未当UNKNOWN重发。exact private supplier、当前profile/clock、egress、预算reservation、durable intent及一次permit均沿既有owner核验；无key/value/hash输出或其他secret lookup。下载当前仍见系统fake-IP，重新取Google HTTPS DNS公网答案，仅对fetch进程内exact `files.metaso.cn`生效，保留public pin、TLS/SNI、无重定向/无下载凭据，不改全局DNS。

已知前片FAIL后，依用户本轮修复授权与constitution的有限调整规则，经原committer保留ledger前序：内部CNY总upper bound200,000,000→250,000,000 microunits、单次50,000,000保持，同task quota3→4；当前累计视频15次，旧消费不退回。这里不是价格、账单、账户余额或剩余S02授权，见 `bounded-repair-unit.json`、`budget-extension.json`、`submit-quota-extension.json`、`paid-authorization.final.json`、`wire-observations.json`。

Exact输出为run根下 `production/state/video-generation/fetch/files/32853406063cf3f57adf1ae83ae59599316a930893d0c6f1ccf8bcd76203d5c1.mp4`，SHA同文件名，2,482,274 bytes、H264、**768×1344（实测4:7，非精确9:16）**、24fps、107帧、约4.458333秒、32kHz stereo AAC。请求明确9:16，实际恢复竖向；未裁切、补边、锐化或改变原3秒采用冒充最终交付。

实际显式project-local MCP分析18帧/0.25秒，另解码原生frame71；selected controlled presentation逐项收到原15个问题，canonical登记 **3 PASS / 4 FAIL / 8 NOT_EVALUATED**。PASS仅为右手膝上手机、弱closing character-presence anchor与raw source/output技术合同。FAIL为identity/other-props/reflections/space：首帧起只有苏遥与五位坐姿乘客，郭向东/黑帽未保留；近邻陈立被改到对面座排并新增蓝挂绳白工牌。竖屏、可读抬手及稳定镜头不能抵销缺人、空间和道具回归。实际2cm、完整gaze/lips、工牌字样、声音合并要求仍缺证，未从白模继承通过。experience `c7c91e29ecba449db5ff71a5abd54498dd39fe16620e718b4c5047a3d00a6c9f`、evidence `7a5ec375d3dc403bff80fb8551fa77f0c403503862fe95b989e90832c46497df`；见 `qa-presentation.actual.json`、`operator-qa-answers.json`、`qa-diagnosis.actual.json`。

本片通过fresh project-local MCP→已安装qualified Gemini development operator完成一次真实音频观察，requested/response model均`gemini-3.8-flash`，source SHA为本片，完整PCM SHA `2c46bb18807f4cb2b15743c014dbe1dab956aa54da2e662d7fe4e4928fbb85f3`。盲观察为女声“林燕”0.5–1.7秒、“请在终点站下车”2.1–4.3秒、calm/formal announcement及轻微背景噪声/click。名字同音不证明说错；估计时戳不代可验证0.1–2.7秒边界，原3秒采用可能截断，未延长采用或伪称听过。声音unit仍单次、30分钟、预配置USD50,000 microunits内部upper bound，不代表账单；consume/outcome保留在 `audio-operator-001/`。

本轮trusted stdio MCP接线显式注入factory、media root/model、exact operator unit/intent SHA及当前UID标准D-Bus元数据，凭据只由原operator的exact Secret Service supplier读取。现有`ProjectAnalysisSession`→`analysis_client`不自动转发unit/hash/DBus，不能把三项构造参数当已qualified接线；本轮用同一MCP SDK/服务的显式operator配置完成，没有修改共享代码或创建新Product分析状态库，也不声称该自动转发缺口已修复。

### Stop And Proof Boundary

原committer以明确的已知视觉失败理由abandon本候选：同bytes补证不能补回郭向东或撤销空间/道具变化，全部FAIL/NOT_EVALUATED保留。标准loader复开 **Manifest82/Project13、attempt=failed、VALIDATE、quality rejection `d79c0a8487dc231b7297571a7701f77a9e1ed385bd98090ce29b4f4e3971d472`**；Budget revision18、上界250,000,000，未activate、未提取accepted状态、未提交S02。见 `stable-media-checkpoint.json`。本单元已消费，不复用permit或再重抽；后续先审查多人身份/reference职责和镜面clean-plate的实际表达，形成可审阅新输入与有限单元，不能删人、删剧情或靠声音掩盖缺陷。

原前15秒仍是S01 0–3、S02 3–7、S03 7–11（摘耳机否认）、S04 11–15（其他乘客如常）；本轮只有一条未通过的S01原片，既不是两镜7秒，也不是完整前15秒。字幕原句仍在selected final contract，尚未物化为CaptionTrack/实际composition；canonical trim/接点、原生声音与字幕合成、HyperFrames、完整故事AC-7和用户1.0x完整听看均未完成。白模默认规则继续有效，不由本次失败推出白模保证成功或无效。

`record-ai-video-session`更新本主记录；`distill-ai-video-learning`为 **no_candidate**：新旧条件同时改变多项输入、无受控seed，也没有证明新的可复用质量改善，不把参考几何/不同proof layers计为独立模型成功。Risk Gate为Parent自审：只制作参考、通过既有owner操作及记录，没有shared code/权限/Gate变更；不以文档/Harness代媒体验收。文档exact commit-range receipt为 `.agent/harness/runs/jieshi-optical-whitebox-record-20261016-r1/receipt.json`，实际结果以receipt及Git为准；foreign index/dirty保留。

## Prior Whitebox Reference Result — 2026-10-16

本节是前一白模单元的历史结果，后续为上方 Optical Whitebox 和最新 Official H3 Max 单元；保留原始结论与证据，不重分类为成功。

用户明确要求“做个白膜再用这个api生成一次，模糊先不处理”，本轮完成白模和 **一次** METASO `MiniMax-H3` 视频生成；没有再生图/锐化/重抽/S02 POST。下节“Prior METASO Media And Gate”保留的是前一次无白模结果，不能当本轮当前状态或 accepted S01。

白模目录为 `runs/canvas-jieshi-original-s01-s02-20261013-001/whitebox-S01-20261016-001/`。Blender 5.2.1LTS/build `9e2066aef7ef` 制作并保留 `.blend` 与 asset-authoring Python；`S01-whitebox-v006.mp4` SHA `68d175efa490de91ee30634fe790f4b487ea81c150e7b863cc05b47a3c363709`，768×1344、24fps、96帧、4秒、无音轨。28mm锁机位，七名他人的镜面替身及空的林砚位置；空左手抬起后在2.25秒前到位并保持，右手黑手机在膝。`geometry-audit.json` 的掌窗距离约0.0200000015m；这是作者几何与明确的镜面空间替身，未声称真实光学仿真或最终视频已满足2cm。已实际查看白模及显式 MCP 帧；v001–v005 迭代保留。

沿现有共享 inspect/author/Planner/Router/committer 增加普通本地 MP4 reference 准入，未增加故事执行脚本、第二 timeline/state/renderer。实现 `54cefd068022450ee17bf1d9363cadbed5fd131a` 与依赖说明修正 `57dc0951eb317ea2527533ca456b15ea296f1c56` 已 push/main SHA核验。Exact Harness `.agent/harness/runs/canvas-local-video-reference-20261016-r1/receipt.json`：全部checks PASS，含264项Canvas、81项preserved-source及Architecture Gate；receipt完整性/closure已核验。说明修正另有 `.agent/harness/runs/canvas-local-video-reference-doc-20261016-r1/receipt.json`。Risk Gate为 `NATIVE_REVIEW_NOT_REQUIRED`：只准备受限local bytes/测量receipt，不改凭据、付费权限或唯一writer，相关boundary/reopen/tamper和真实导入/编译已有验证；不以旧review或工程PASS代媒体结果。

新 inspected source snapshot `900ce8fe5f971a679e730ba45df0da84f109da7167ebe64c4e1315bc99576e51` 保留原两个text parts逐字不变，新增用户授权白模职责；原PNG仍 `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`。R2V沿现有严格逐人物owner绑定，同一PNG用8个Character alias和1个Scene alias形成 **9个相同字节的inline image inputs**，另加1个video input；不是9张新图，也不把它描述成仅发了1个image字段。额外重复是当前输入owner限制，未声称最佳通用多人物方案。原文、15项QA、广播及字幕职责保持；native prompt SHA `96898eef289374fbad5e715e3ea25a7405538c8e39b3e31ad2c9d5993db91243`，body SHA `2e0b00216aca0de95d61cfe999956260cd10012f4d84a167c50b8e4fb4289678`，25,810,477 bytes。相较前片同时改变mode、prompt、image/media bindings与execution stack；seed不受控，不是isolated A/B。

前次b72a…片按canonical abandonment封存4FAIL/7NE，不作为accepted source。本轮两次无Provider副作用的authoring候选被原committer拒绝：外部blend/script hash误填Registry input artifact ID、R2V引用误填pending Shot input roles；原active Project始终保留。随后外部来源hash独立存authoring evidence，输入绑定归Character/Scene/generation.references，Shot只保留pending primary_visual，正常导入Project12。失败事务和旧receipt均保留，未改guard或手写state修复。

Canonical attempt `canvas-62d4ee6132573d671a0191ad976dab8f4c97b527`，task `2110860569473404928`；POST1 HTTP200、正常GET观察succeeded，零retry。实际resolved hash `fed043e294419266b45780101739785e1b293f45f726941cdb8fdd950a9b6bd9`。Fresh preview/30分钟授权、同task ceiling3/used2、内部剩余50,000,000 microCNY上界经原Budget Guard/reservation/egress/intent/一次permit执行；旧计数不退回，累计视频14。内部上界不代表价格/账单。凭据只经exact user-designated private supplier；未输出值或hash。下载沿同task重查与既有public pin/TLS/SNI/noauth/noredirect；当前系统DNS仍返回fake-IP，显式process-local exact-host HTTPS DNS选择有证据，未改全局DNS或绕校验。

Exact输出 `production/state/video-generation/fetch/files/74da665b5f2751f902c1660b6fc9346b4a46e5865357b95db644ae0cc4b07084.mp4`（相对上述run根），SHA同文件名，2,277,666 bytes、H264、**1344×768横屏**、24fps、107帧、4.458333秒、32kHz stereo AAC。Profile为4s/768P/adaptive/context_ir=false/native audio；这次R2V没有首帧硬锁，不能隐去由先前竖屏变横屏的输出差异，也没有裁切/补边伪装交付。原采用仍0–3秒，未执行最终canonical trim。

显式project-local `video-analysis` MCP实际分析exact输出：18帧/0.25秒采样、1 scene；另实际解码frame71。Controlled presentation接收原15个问题后登记 **4 PASS / 2 FAIL / 9 NOT_EVALUATED**，canonical experience `e9b0f1d379c4f5431ab75b9f20c27aa5f6fad0058b42e354928fb165929955aa`、evidence `cc2a5633894fb9add4f2c7e2f23884295d8205d2965b4223b9993927ebcf3fe1`。PASS为camera/close-anchor/source-output/space：采样未再出现乘客消失或座区变门，宽景锁定、七人位置保持。FAIL为reflections/other-props：横屏上缘裁掉苏遥头顶，完整倒影不保；陈立约2.25秒转头并出现眼镜。手机与工牌区域出画、完整身份/从膝起手/悬窗约2cm/目光口型仍缺完整证据，不能用白模或局部改善代签。技术source-output PASS只指raw请求/产物与声明的采用窗口，不代表composition/字幕/交付已完成。

声音实际使用同MP4的一次MCP→Gemini `gemini-3.8-flash` HTTP200；PCM SHA `c02743e63cba370331614fef6d14cf1ba1f4cf7b2c6a37612b746e0735e0ba06`。观察为平直礼貌女声、一个“林艳，请在终点站下车”片段、估计0.3–3.8秒、background_sounds=[]。同音转写不证明名字错误，也不代exact原句、D门扬声器声场、环境声和0.1–2.7秒可验证边界；可能被3秒trim截断仍须补证。未声称Codex原生听过或human接受。原始MCP/音频operator intent/consume/outcome、actual presentation/answers和诊断均保留在该unit。

本轮按FAIL/NE停止且未activate；原committer以明确理由abandon已知失败候选，保留全部findings与媒体，标准loader重开 **Manifest71/Project12、attempt=failed、canonical next_action=stop**，见 `stable-media-checkpoint.json`。完整两镜、前15秒S01–S04、状态交接、HyperFrames声画/字幕/canonical trim、完整故事AC-7及用户1.0x完整听看均未完成；不把这条4.458秒候选称为7秒或15秒交付。已知裁切/额外动作不能靠同bytes补证消除；后续恢复须先明确这些实际缺陷和新有限单元，不能复用本次已消费许可。图片模糊按用户要求未处理。

`record-ai-video-session`更新同一主记录。`distill-ai-video-learning`重新检索并核对同族证据后为 **no_candidate**：本轮只有一个白模条件下的真实attempt，与前片同时改变多项输入和模式；不能将“这一片人数/几何较稳定”升级为白模必然有效或已修复原S01。未修改Skill/Policy/Gate、未刷新RAG或全局memory；foreign staged/dirty保持。

## Prior METASO Media And Gate — 2026-10-16

原 S01 已经真实通过 METASO `MiniMax-H3` 生成并经 canonical fetch 落盘，取代下节历史候选的“POST0/无MP4/等待工程验证”状态。工程 commit `c3706e3bbcc648ab2f21a15c57a022df7befa95a` 已 push 并核对 remote main；exact Harness `.agent/harness/runs/metaso-original-recovery-20261016-r1/receipt.json` 的完整证明已核验，一名原生 `reviewer_xhigh` 审查 finding set 为空。工程证据不代表媒体通过。

本次视频 POST1，HTTP200/task `2110842438415237120`，canonical attempt `canvas-785e429d6d7241b741dd75d8f4d5981cef08f876`；S02 POST0，零重抽。旧历史12次保留，当前累计13。输入 prompt SHA仍为 `2a54252ee51ac0d9c1a193ff0b3060aa80ae94ab3570986c588b49b162f50f59`，首帧 SHA仍为 `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`。原文15项规则及对白/倒影/手部/摄影均未删除；技术适配仅沿已审查 contract。

Exact MP4：`runs/canvas-jieshi-original-s01-s02-20261013-001/production/state/video-generation/fetch/files/b72a5f426beddf08fb3c9f51fbb0773588ac92a767e595835b60ca601c8c7dd3.mp4`；SHA同文件名，2,676,583 bytes，768×1344，24fps，107帧，4.458秒，原生32kHz双声道AAC。实际请求 nominal4s，不把实际4.458秒写成精确4秒；原采用窗口仍0–3秒，未以延长采用来修广播。

显式调用 project-local `video-analysis` MCP 后，使用 exact MP4、全部15项 actual presentation 与原生音轨观察登记 canonical Gate：**4 PASS / 4 FAIL / 7 NOT_EVALUATED**。FAIL为 `s01-identity/s01-native-track/s01-reflections/s01-space`：0/0.5秒保留七名他人，约1秒后灰衣邻座和老人消失、相应座区变出车门/显示屏；不能用“林砚无倒影”替删除其他人辩护。真实frame71单独解码，左手已抬起，但2cm/不接触的完整证据不足，未用raw尾帧代签。

声音本窗口实际打通新 exact MP4 的 MCP→qualified Gemini operator：一次HTTP200，模型 `gemini-3.8-flash`，完整PCM derivative SHA `7987b8cdd84d9976e4d6214de923d9218ce4b69913369c0bfe7004f4e8f614a9`。盲观察报告孤立点名后再次点名并说完整句，支持重复词FAIL；转写“李燕”不能证明原名“林砚”错误，估计时戳也不代0.1–2.7秒精确边界，因此完整广播/时序仍NOT_EVALUATED。没有伪称Codex原生听过或human验收。首次PTY回答超过4096字节导致JSON framing失败；重开已保存的真实MCP response与相同items，经新controlled presentation完成证据登记，未重发音频/视频。

运行恢复没有改产品代码或旁路写state：第一次submit前被task ceiling guard拦住，实际无POST/intent，随后经既有 `extend_paid_provider_submit_quota` 封存同task 2→3有限扩展，再执行一次真正submit。第一次下载因系统DNS返回 `files.metaso.cn → 198.18.2.227` 被公网pinning拒绝；显式选择HTTPS DNS的真实公网答案，仅在fetch进程中对该host供给解析，保留原公共地址校验、numeric pin、TLS/SNI、无重定向/无下载凭据，成功下载同一task，未改全局代理、未新生成。

当前Manifest57/Project11，paid phase ACCEPTED、video phase VALIDATE；`_require_evaluation` 实际拒绝推进，attempt在持久化层仍RUNNING，不能误写为已关闭/已激活。Budget revision12，内部reserved upper bound150 CNY、available50 CNY，保留两个旧图片reservation及本次50 CNY视频reservation；未结算真实账单。S02、实际accepted state绑定、字幕、canonical trim接点、HyperFrames声画片、原前15秒交付与完整故事AC-7均未完成；human1.0x为NOT_EVALUATED。

Operator证据根：`runs/canvas-jieshi-original-s01-s02-20261013-001/metaso-S01-live-20261016-001/`；关键文件为 `wire-observations.json`、`submit-quota-extension.json`、`fetch-after-dns-repair.json`、`download-dns-runtime-selection.json`、`exact-mcp-analysis.json`、`actual-qa-presentation-r2.json`、`canonical-qa-diagnosis.json`、`stable-media-checkpoint.json`。当前按FAIL/NOT_EVALUATED停止，不挪后镜额度重抽；最小恢复条件是针对缺陷封存新的明确修复单元及其输入/证据方案，而非删剧情或改判PASS。

本checkpoint执行 `record-ai-video-session` 与 `distill-ai-video-learning` 评估：`no_candidate`。一次新H3尝试和同bytes多层证据不构成两个独立实验；旧Seedance输入拒绝亦非控制变量相同的模型质量比较。经验检索本轮返回stale last-good空结果并异步排队；未为记录重建RAG或新增Provider调用，foreign index/dirty保持。

## Prior METASO Route Correction — 2026-10-16

用户最新明确纠正“不是让你用metaso的minimax吗”，当前目标 Provider 改为已有 `MetasoH3VideoProvider` / `MiniMax-H3`，不是秘塔搜索、Seedance 或本地模型。此前 Seedance-only、个人账号 Entry/VIP 阻断保留为历史；没有以账号讨论代替视频制作。

本轮先误将用户所指 METASO 用作搜索，随后已纠正。该搜索 API 一次 HTTP200，不是视频调用或人物入库成功；没有回显密钥。用户明确指定 `.env` 后只提取对应 `METASO_API_KEY`，不授权其他 credential 搜索或公开。

当前无付费副作用的真实 S01 编译候选已通过：提示词与原封存请求逐字节相同，SHA `2a54252ee51ac0d9c1a193ff0b3060aa80ae94ab3570986c588b49b162f50f59`；first-frame仍为 `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`。H3 声明4s/768P/adaptive/24fps/native audio，canonical S01仍只采用0–3秒。候选在 `metaso-S01-live-20261016-001/`，不冒充 final request、已提交或 accepted。

实际发现两处共享缺口：preserved-source 校验此前硬编码 Seedance；已知 no-effect 恢复此前只能同 Provider。原文编译适配的305项 focused tests通过，并实际只读重开当前 Manifest45/Project10。首次扩大真实重开暴露 `ResolvedVideoGenerationRequest` 字段回归，已修复并加两 Provider resolve 测试，不以最初107项局部PASS掩盖该问题。跨 Provider `runtime-repair/5`、完整 Harness/独立审查及真实提交仍在本轮执行中，未声明完成。

候选技术适配逐项可审阅：只有 generation OutputNeed 的 exact geometry 改为 adaptive/null dimensions；Shot 原文、对白、source expression及首帧 bytes不变。H3最低768P，旧 `s01-source-output` 原生480p token候选改为768P；15项 required IDs、proof/tolerance和全部剧情/声音要求保留，旧policy/goal不覆盖。`qa-policy.S01-candidate.json` hash `cd4c11590bab838404bf9f51d426cf2b0f56dd44be31b33c8e253041c81ec949`，尚未激活。S02技术规则留到其独立准备时适配，不先签后镜 QA。

Parent 在真实原项目上执行无副作用 author bundle → Planner → candidate，而非把 fixture 当剧情证据。实际中立输入另有 canonical Shot metadata、三个 Planner identity hash及首帧 Shot owner hash随动；其余完整语义逐项相同。首次 actual comparator 为False：恢复候选误写旧 `exact_seconds` / `seedance` provider_kind，实际旧值为 `nominal_seconds` / `volcengine_ark_seedance`；修正后 `actual-strategy-equivalence-r2.json` 为True，r1保留。恢复模块65项测试为这些收尾修复前的基线，最终 Harness/审查证据另行补充，不能用该基线代签新 bytes。

冻结前新增跨 Provider focused integration为3 PASS：经 Canvas/Planner 创建候选、canonical no-effect、v5 注册、后继 paid intent 消费授权，再用新 committer 重开 Canvas得到 `poll`；再次start不重复submit。该测试使用离线 Provider double，只证明工程生命周期，不代表原 S01生成或媒体验收。

当前新 H3 POST0、原 Seedance POST1、历史11、累计12；无新 MP4、S02未提交。新 H3单元限定S01一次、S02一次且以前镜全PASS/实际状态绑定为条件；内部单次50 CNY/新单元100 CNY只作既有operator upper bound，不是报价或账单，现有project ledger ceiling200 CNY及旧reservation/消费均保留。UNKNOWN不retry/remint，旧失败不重分类。现有音频MCP解释器/工厂本轮import已重新核验；新 exact MP4对应音频unit必须等落盘后准备，未复用历史消费单元。

## Supersession Notice — 2026-10-15

2026-10-16用户选择A继续找免费Seedance入口。即梦当前账号的Mini、2.5样片及2.5均实际显示“升级以使用”；公开新用户活动的3次Mini限免尚未证实属于本账号。字节官方另列豆包App入口，当前豆包网页未登录且未显示视频功能；App实际免费次数待用户核对。见 **Free Seedance Alternatives And Account-Specific Readiness — 2026-10-16**。已恢复FastVIP网页草稿，原图SHA及40积分保持；本轮生成/充值/新上传均0，未把任一候选宣布为免费准入成功。

2026-10-16用户已完成即梦登录。当前实测40赠送积分（订阅0/充值0），本次“每日免费积分 +40”；原PNG已通过正常的系统文件选择框进入网页首帧预览，local blob与canonical SHA完全一致。`Seedance 2.0 Fast VIP`生成按钮悬停明确“此功能为VIP专属”；可选4s，但分辨率菜单仅720P，未点击生成或购买。见 **Authenticated Jimeng Credits, Exact Frame Selection And VIP Boundary — 2026-10-16**。这取代下段未登录阻断；没有生成审核、原S01 MP4或新的Harness视频成功。

2026-10-16用户已选择“保留当前图，先核对即梦个人网页的正常上传、审核和已有额度”。即梦网页已由独立Chrome MCP会话实际打开，`Seedance 2.0 Fast VIP`与`首尾帧`入口可见；点击`首帧`弹出“请先登录”，尚未选择或上传文件。见 **Jimeng Personal Web Readiness And Login Boundary — 2026-10-16**。当前会话未登录，实际会员/额度及原图审核均`NOT_EVALUATED`；仅核验路线，不生成、购买或充值。

2026-10-16用户已确认“仍是个人账号”：免费Entry恢复候选的企业资格未满足。见 **Personal Account Reply And Remaining Seedance Routes — 2026-10-16**；这里是用户账号状态声明，不冒充当前quota/API实测。仍只用Seedance、不买人物库、保留原图及失败历史；此前等待输入面选择已被上段用户选择取代，无新生成。

2026-10-16 Seedance-only续查纠正前次归纳遗漏：官方免费`高级创作权益（Entry）`支持AIGC入库；不是必须付费人物订阅。旧账号实测已记录免费Entry因企业认证而disabled，本轮未刷新账号资格。见 **Free Entry Recovery Candidate And Enterprise Eligibility — 2026-10-16**。当前exact图、Manifest45/Project10与原POST计数保持；未切METASO/H3、未读`.env`、未开通/上传/重新生成。免费档存在不等于当前账号或多人首帧已准入。

2026-10-16用户补充要求“别找那种付费的途径”，当前恢复建议据此收敛：不购买权益、充值、收费中转或新付费Provider；不把免费入库误称为免费视频。见 **Community Admission Research And No-New-Paid-Route Constraint — 2026-10-16** 与共享workflow的`Portrait Input Admission`。此前“换Provider/开通素材库”只保留为历史候选，不是当前待执行建议。S01仍为已知输入拒绝，原图静态PASS、POST计数及S02未提交保持。

2026-10-16当前续执行已到一次真实原S01视频提交，详见 **Original S01 Exact Submit And Input Admission Stop — 2026-10-16**。图片静态PASS保持；已配置S01 15项raw QA、实际Planner/Router编译、fresh runtime/供应凭据/预算/egress/intent/一次permit，并在用户对exact图片确认A后提交。Seedance HTTP400 `InputImageSensitiveContentDetected.PrivacyInformation`，无task/MP4，canonical known_no_effect/runtime_failure/STOP。当前Manifest45/Project10/schema2.15，原视频POST1、历史11、累计12，零retry；下方“qa_policy=None/未提交”是此前保留checkpoint。新作图实践已按用户明确要求写入共享workflow，不把平台审核拒绝当静态图FAIL，也不继续无效修图或重发。

2026-10-16当前图片状态已取代此前完整首帧FAIL/未导入的当前结论：见 **Original First Frame Static Admission And Canonical Import — 2026-10-16**。新增13次内置图片，累计22；最终exact PNG `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`逐项静态复核为PASS_FOR_FIRST_FRAME_AUTHORING，随后沿既有generated-source copy/唯一committer导入并绑定S01，标准loader重开Manifest37/Project9。旧10条P7 Registry前缀/媒体/attempt与web UNKNOWN保留。原视频0、历史视频11；静态成功不代视频动作、广播、声音/字幕/trim、后镜handoff或human1.0x。当前qa_policy仍None、Provider admission和qualified视频/新原镜声音仍未验；下方旧“最新”段均为历史checkpoint。

声音当前实测更新见[Audio Understanding MCP record](2026-10-15-audio-understanding-mcp.md#operator-verification-and-live-evidence)：Gemini development operator经exact supplier/一次intent/permit，在已有4.032s历史WAV完成1次真实MCP调用，HTTP200，取得对白/声线/表演观察。先前“runtime未绑定、没有上传或实际音义”的描述已被该结果取代；当前Codex native audio仍unsupported，新原镜声音/selected QA/精确时序/human仍未验，旧permit已消费，不把工具成功当首帧FAIL或原镜Gate解除。

最新媒体checkpoint见 **Crop Assisted Hand Repair And Spatial Composition Stop — 2026-10-15**：新增4次内置图片调用，局部放大参考→整图转移修好苏遥解剖左手白手机；同一原生只读critic与Parent通过实际袖口/肘/腕推翻旧手机横坐标判手。后续同排座位参考修正陈立所在排，新取景让其鞋进窗，但最新图重复一名女性、遮住其他倒影、苏遥领型仍错且林砚对应空座不可读，完整首帧FAIL/STOP。内置累计9、原视频0、历史视频11；未导入/激活，标准loader核验Manifest33/Project7、`qa_policy=None`及entrypoint/Manifest/Registry不变。旧计数/UNKNOWN保留；以下“最新”段均为历史checkpoint。

最新媒体checkpoint见 **Original Frame Completion Attempt And Video Stop — 2026-10-15**：按“继续图做完了就生成视频啊”新增3次Codex内置修图，七名他人完整倒影与老人坐姿保住，陈立手机补出；镜像持机/耳机仍有FAIL或NOT_EVALUATED，首帧未完成。实际声音输入再次被平台拒绝，当前Manifest33没有active QA policy或原视频attempt。未导入/激活新图、未提交视频；累计内置图片4（本轮3）、paid准备图2、local模型图2、原视频0、历史视频11，旧web UNKNOWN保留。

此前治理续执行见 **Community Validation Principle And Checkpoint — 2026-10-15**：用户要求把“遇到问题参考社区、实际验证、写回工作流”写入AGENTS，仅新增薄原则/已有owner锚点；原暂存的native reviewer迁移不夹带。该治理轮不生成媒体、不修改Production或LearningClaim，原S01/声音/UNKNOWN边界保持。

最新checkpoint见 **Codex Direct Image And Authoring Workflow Rule — 2026-10-15**：用户明确改用Codex内置工具，独立1次实际生成并exact copy落盘；老人坐下/放开扶杆，target static 5 PASS/1 NOT_EVALUATED。原图944×1672、输出943×1668，精确像素保护及完整原S01仍未通过，未导入/激活、Manifest33不变。用户随后明确要求把默认生图规则写入现有工作流，并批准只改playbook生图小节、独立提交且保留原暂存修改；无新增Provider调用或产品adapter。

上一尝试见 **Pose Reference Trial And MCP Execution Stop — 2026-10-15**：先前1次 `chatgpt-web` MCP 300秒超时，页面空白/入口未就绪，未取回 exact 图片；原remote outcome UNKNOWN继续保留，没有重发、退款消费或伪称outcome已关闭。后来的内置调用来自用户新的明确路线指示，不是自动fallback。下段为仍有效的上一媒体/工程 checkpoint。

最新checkpoint见 **Registry Retention Repair And Actual Targeted Z**。共享历史链修复已发布 `a45fa113b2ffb10bbd071bfa51753849aa82c911` 并核验remote main；原生审查两条blocker均由标准loader RED复现、修复后41项focused PASS和fresh exact Harness验证，原reviewer复审finding set为空，Parent关闭两条问题。标准metadata authoring恢复Registry原P7前缀，所有旧records/媒体/history保留。随后真实新增1次本地Z局部修复，exact PNG `102c1ec74f873a0de8297d2cf9de1477a9ae1cf0b0fc654836e6e8dc7e127557` 技术SUCCEEDED但老人仍站立扶杆，target QA 3 PASS/1 FAIL。遮罩外1,536,514 RGB像素变化0，不能替代坐姿成功。Z单元按FAIL STOP，H未提交；当前Manifest33，累计原准备paid图片2、本地模型图片2、原视频0、历史视频11。本窗口新增paid0，无accepted S01、实际handoff或HyperFrames声画交付；声音仍EVIDENCE_REPAIR_FIRST，human1.0x/完整故事AC-7均NOT_EVALUATED。自有ComfyUI unit已停止。

## Historical Supersession Notice — 2026-10-14

当前最新checkpoint为下文 **Actual Local Masked Generation And Targeted Repair**：本地三引用蒙版作图已真实执行1次，exact PNG技术准入成功但静态QA为2 PASS/4 FAIL/1 NOT_EVALUATED。蒙版外1,096,780像素RGB完全相同，窗内人物/道具/空间没有通过。累计原准备paid图片2、本地模型图片1、原视频0，Manifest25；没有accepted S01、handoff或成片。已封存最多再2次针对具体人物的本地修复，未提交；不挪旧edit/B、不重抽旧单元。共享工程 `d37d0482e4a0d6205b2c546ba010e24433dccd8c` 及输入准备 `49485ee5bfff539e4ebb9a5902a37c0dd501e0e3` 已push/remote核验。此前“只读runtime/无模型推理/Manifest19”是保留的历史checkpoint；技术准入、工程与素材QA仍分开。

用户已明确授权最多2 Seedream PNG+2原S01/S02 Fast4s、480p/native audio、零重抽的200 CNY内部上限单元。下文此前“新单元未授权/新增POST=0/Manifest revision3”为历史checkpoint，已被文末真实执行取代：新增1图片POST、0视频POST，exact底图视觉QA FAIL，未进入第二张或视频。paid receipt ACCEPTED与本地materialize `outcome_unknown`分开保留；不是Provider结果未知，也不是原S01成功。

## Current Goal And Boundary

用户明确纠正：旧抬手机/起身两镜为 Agent 简化测试，不是原开场。本次从已发布 shared inspect/author/preflight 继续，准备原 S01→S02 候选及逐项忠实度矩阵，不重建执行链。原开场两镜采用0–3/3–7秒；S03/S04才补足7–15秒，当前只保留映射、不扩4次生成。

当前广域masked候选为素材 `QUALITY_FAILURE`，本地unit1已用1/1并停止该attempt；已诊断后封存targeted repair有限unit，不推进视频。旧本地candidate materialization阻断已解除。source/identity crop/binary mask已按当前Scene/Character职责经canonical revision准入并真实推理，缺的仍是合格剧情画面。声音语义仍缺合格听音/登记路线的 `EVIDENCE_REPAIR_FIRST`。对原文“clean plate必须最终视频overlay”的过早解读已撤回：原文只要求几何一致且只删除林砚映像，可以先准备首帧。已补同一Seedream adapter的单PNG参考，但前两次实际使用T2I；准备图失败不能签实际plate或raw video成功。没有激活QA或qualified视频runtime。未生成新的原剧本MP4、没有前镜accepted source、没有state handoff/后镜submit、没有HyperFrames成片；human1.0x及故事AC-7 `NOT_EVALUATED`。

## Owned Work

- [原候选与忠实度矩阵](../canvas-projects/jieshi-original-s01-s02/README.md)：原文出处→project/参考职责→exact source-native文本或canonical composition职责→required实际QA；显式列出原S01 Next/Risk clean plate、字幕与声音缺口，没有删剧情要求过检查。
- 原 `project.json/source.json/source-mapping.json` 沿共享数据入口；所有原Shot动作、对白、窗口、摄影与当前人物外观/道具/空间进入source；原字幕分配canonical caption职责。历史PNG同bytes仅用于审阅绑定，S02引用为future state placeholder，不是实际状态。
- 复现source compiler的typed对白6paths未表达。新增小型通用 `seedance_source_dialogue.py`，只有same-line exact语音约束才能声明时间/画内外/口型控制；既有逐字中文只表达mode/language。拒绝silent output、超request窗口和未表达fields；不改source text、schema、permit、QA或renderer。
- Self-reviewed spec/plan：`docs/superpowers/specs/2026-10-13-preserved-source-dialogue.md`、对应plans同名。默认Native Codex串行，当前main，无development worktree。
- 续执行共享修复：`seedream_reference.py` 负责单scene PNG测量/版本/preview accounting，`seedream.py` 显式 opt-in profile + injected byte resolver + 原字节 inline image/egress；`image.py` 区分新reference request `/5`与原T2I `/4`。旧profile序列化/hash及original PNG result版本不变。复用现有paid image committer、Registry、P5 activation，不新增Provider/model/timeline/renderer。
- 单参考的self-reviewed spec/plan：`docs/superpowers/specs/2026-10-13-seedream-single-reference.md`、对应plans同名。README与project adaptation_reason同步首帧准备职责；source/native输入和原剧本bytes未改，不编造bbox或实际plate。现有video+PNG generic overlay仍不宣称支持。

## Previous Published Candidate Evidence

证据根 `runs/canvas-jieshi-original-s01-s02-20261013-001/`：

| Evidence | What it proves / limit |
| --- | --- |
| `inspection.json`、`author.json`、`preflight.json` | 已实际调用三个共享入口，generation/composition_order均S01→S02，production_acceptance NOT_EVALUATED；Production目录没有文件 |
| `native-dialogue-gap.json` | 修复前两镜各6typed dialogue paths未表达；是纯native-expression诊断，不冒充Planner/Router prepare |
| `native-expression-preview.json` | 当前author后的source-native文本与hash；两个原镜无未表达authored paths；完整qualifiedruntime prepare仍NOT_EVALUATED。S02仍是placeholder，不是final video-reference payload |
| `audio-capability-probe.json` | 本窗口实际音频输入被平台拒绝，Whisper只有转写证据；声音语义、时序和声线没有听音验收 |
| `kimi-receipt.json`、`kimi-report.json` | 受管read-only capability mapping，exact旧snapshot；不是implementation review或mediaQA |
| `.agent/harness/runs/jieshi-original-source-20261013-r1/receipt.json` | 第一轮真实FAIL：新helper/test未注册policy route，policy_audit_check阻断；其他suite未执行，保留失败历史 |
| `.agent/harness/runs/jieshi-original-source-20261013-r2/receipt.json` | 新helper/test接入已有preserved-source suite与routing后的非空exact staged验证；发布前必须fresh verify，不签模型/连续性成功 |

有效red evidence：`/tmp/jieshi-source-dialogue-red.txt` 的4 failed /7 passed（正确完整typed数据下重现，不把更早测试构造错误算产品回归）。随后13项新测试通过，含T2V与Fast I2V public common compiler；首轮61项source/native/compiler相关tests通过，扩大focused suite91项通过。最终Harness以实际receipt为准，不能从计划宣称PASS。policy修订只增加注册新测试/helper，保留全部旧检查，直接保护原对白、窗口和嘴部表演的输入表达，没有降低观看验收。

## Single Reference Engineering Evidence

| Evidence | What it proves / limit |
| --- | --- |
| `single-reference-current/{inspection,author,preflight}.json` | 当前project改动后重新调用共享三个入口；纯候选，不是qualified paid preview或Production acceptance |
| `clean-plate-capability/{task,run,receipt,report,parent-adjudication}.json` | 新一轮read-only Kimi mechanism mapping与Parent逐条裁决；冻结source hash在编辑前核验，修改后不把旧snapshot冒充final implementation review |
| `clean-plate-capability/audio-capability-current.json` | 当前再次实际audio input unsupported；medium/zh转写及当前verifier能力检查，见下文 |
| `/tmp/jieshi-reference-red.txt` | 原adapter/reference request拒绝的红测：6 failed、12 passed；没有Provider POST |
| `/tmp/jieshi-reference-final.txt` | 最终22项Seedream测试通过：public committer exact egress/native image、activation/reopen/replay、旧profile、错误role/count/bytes/PNG/geometry、credential lookup期间reference drift拒绝及known_no_effect |
| `/tmp/jieshi-reference-related-final.txt` | 此前19项版本加image/Grok remote lifecycle/state commit/Canvas project相关suite，280 passed；随后仅补3项reference geometry测试及清理新测试unused locals，不把旧测试数写为最新全套 |
| `.agent/harness/runs/jieshi-single-reference-20261013-r1/receipt.json` | 非空exact owned staged snapshot的当前工程验证；状态/selected tree和freshness以实际receipt为准，不预签PASS |

通过标准 `load_production_project` 重开旧asset-first Production：Manifest revision72，旧图片 `image-3bb276475a7f90384e8ca653d0bfa8a51f022c882746c0ccfa9ead26621fff64`，SHA `24c6636f075d9428b51216e2e34dfb70995a7da87acc81e753274e7d5383f602`，tool仍为 `seedream-original-png/1`。这是实际旧Registry兼容性证据，不把旧抬手机片提升为原accepted S01。

policy仅把新leaf helper加入existing seedream_image suite路由，没有删除checks、刷新Architecture baseline或降低验收。最终publication必须exact receipt fresh verify后owned commit/push，并核对远端main；foreign dirty不属于本轮证据scope。

## Sound Capability Probe

使用历史原S01 Vidu attempt09 exact MP4，SHA `7b249ddc7c535b36447b0804909059f2e54a74d0a73328dafe409db16a759302`，project-local video-analysis probe报告1080×1920、24fps、97帧、4.042秒、AAC48kHz2ch。局部诊断WAV派生至新run目录，未覆盖历史视频或receipt。

实际audio input返回 `audio content omitted because you do not support audio input`。MCP Whisper base返回0–2.0秒 `零燕請在終點站下車`，不能当原姓名发音正确、0.1–2.7窗口正确或实际听音证据。本窗口没有说听过原片；不是为补证重新生成视频。历史媒体质量没有重分类，本证据只说明当前分析能力缺口。

续执行再次读同源WAV仍返回unsupported；实际project-local MCP medium、zh、word_timestamps=true得到0–2.24秒 `林燕請在終點站下車`，但没有返回逐字timestamps。相近音转写既不能证明原姓名念对，也不能据此断言念错；没证明原窗口/停顿/女声/广播空间。`ControlledPresentationVerifier` 明确只支持technical/analyzer，并以 `EVIDENCE_GAP: no human presentation host integration` 拒绝human；现有Console continuity七项不含audio。网页正常播放、文本答复和ASR/AAC/decode均不能代签可信human或听音语义。此真实缺口需要合格可听音分析环境/selected authority，或接通真实exact-bound human presentation host后再实际听判；不新增虚假verifier绕Gate。

## Managed Mapping And Parent Adjudication

Kimi invocation `ea1727fb-280f-4baa-8eaf-4843245a5881`，sealed deep profile、qualified Docker containment，actual k3/max共3次authenticated requests、PARSED、exit0、未截断；report SHA `69c7fcd94a7b420be4a44a4cfc7af773a38cf02f9b1e29f9948b8dd906c14ba1`。Parent完成7个冻结read文件hash核对后才修改source。Standing Kimi授权不代表image/video授权。

| Finding | Parent disposition |
| --- | --- |
| source prose机械保留 | CONFIRMED，当前shared author+native-expression实测；不是完整qualified请求或模型理解证明 |
| clean plate / mask runtime gap | CONFIRMED限原S01路径；canonical已有多层结构不等于mixed video+局部plate已接通。不能只靠新增enum或模型随机缺人代替真实几何修复 |
| same physical Scene阻断handoff | FALSE_POSITIVE for this candidate；两个明确reference owner IDs共享原SC01地点，既有guard可满足，无需削弱guard或新story bypass |
| 建议新增reflection CausalDimension | 不采纳：当前boundary是声明的partial character carry；实际左手/倒影/空间由source与selected Gate/handoff七维观察核验。新增枚举不能证明缺席；若后续确需typed动态事实再按owner适配 |
| caption/audio existing seam及窗口不保证执行 | CONFIRMED；hook是非口述subtitle，需要authored provenance和actual native clock。拒绝mute/replace fallback，不能把source mapping代为听音验收 |

续执行mapping invocation `c9a84203-5470-4726-864b-8ae69ce8dc75`，sealed deep、qualified Docker、actual k3/max共4次authenticated requests，PARSED/exit0/未截断；report SHA `dbc92968dfb2f1dbac5bd5c00c6e53ec1253508a2946a0f137c4c93bc2760dce`。冻结9个文件；实际7个read hashes在编辑前全部核对。它是旧snapshot调查，不是新implementation review。

| New mapping finding | Parent disposition |
| --- | --- |
| 原clean plate没有强制最终overlay | CONFIRMED；选同源首帧准备，保留raw video全部要求 |
| 原Seedream adapter拒绝reference | CONFIRMED于修复前；本轮已补显式opt-in单PNG，不代表编辑质量 |
| static PNG可以generic叠video | FALSE_POSITIVE；现有classifier/graphic契约需要graphic_layer_id和AdCreativePlan；不能把原剧情plate标成广告graphic绕契约 |
| raw Gate不能由composition签 | CONFIRMED，不改Gate、验收顺序或历史media verdict |

## Historical Authorization And Finite Proposal

新增image/video POST=0。旧asset-first单元仍为图片1/1、视频1/2；历史10视频+旧A1=11，旧cap12保留，未挪用B。前次1原图+2原S01/S02 Fast4s/150 CNY为未批准的历史提案，不提供同源base与plate两阶段证据。本轮可审阅新提案为最多2 Seedream PNG（1152×2048），先准备正常八人/八倒影的技术base，再单参考只编辑林砚反射区域；技术base不能冒充原S01首帧。actual base后才可测/审bbox，不能先伪造exact edit payload。最多2原S01/S02 Fast4s、480p、native audio、零重抽；若以后批准，累计视频最多13而非重置历史。每素材50、总200 CNY只为operator upper bound，不是价或账单。本次没有发出新paid permit或付费批准请求；可听音且可登记的Gate路线与qualified exact previews补齐后集中提出唯一新单元决定。

## Previous Source Mapping Risk Decision

最终stable snapshot以exact staged Harness和`runs/.../review-risk.json`为准。当前diff是纯prose mapping+tests+原候选/证明文档，不涉及凭据、跨项目authority、mutable state、预算/permit或recovery。新映射要求精确声明，未表达值仍拒绝，raw/后镜/最终Gate均保留；已有failure-path及common-compiler测试覆盖确定性变更。真实音义/clean plate缺口显式阻断媒体推进，adversarial读代码不能补听音/几何实测。按SUBAGENTS Risk Gate未触发required final Kimi reviewer；mapping调用不冒充review，parent最终裁决。

## Single Reference Review Risk Boundary

本轮涉及remote image adapter，必须在新exact staged Harness后重新判断；上段不能沿用为新snapshot的final risk decision。新的decision写入 `runs/canvas-jieshi-original-s01-s02-20261013-001/single-reference-review-risk.json`，绑定selected tree、owned paths/hashes、spec/plan和receipt，并逐项记录explicit review mandate、critical consequence及重大后果/实质native gap/reviewer增益条件。当前实际plate/听音缺证仍是media推进blocker，不能靠代码review解除。

## Record And Learning

使用 `record-ai-video-session` 达成substantial候选/工程及真实声音blocker checkpoint。自动按 `distill-ai-video-learning` 评估为 `no_candidate`：没有新的原剧本媒体attempt或controlled comparison；历史同bytes的能力复查是同证据新proof layer，不能算独立实验或更新Vidu质量claim。memory查询已因incompatible library exit3停止，没有重建或刷新RAG。

保持用户列明foreign dirty五个tracked文件和untracked retarget plan；只stage/commit owned paths。Publication由完成后的main commit/push及remote SHA核验报告，技术receipt不构成publisher/human/media acceptance。

## Original First Request Checkpoint — 2026-10-14

用户继续要求原剧情真实视频。沿已发布asset-first准备路线，S01仅添加单个已bound `first_frame` image role，使用同字节historical PNG作准备槽；其usage仍review-only。没有新增制作镜头、第二timeline/state owner、故事执行脚本或Provider。技术base不算原S01首帧，不能发送到视频生成；必须另做clean plate并独立验收。原S01/S02 source-native原句、动作、摄影、声音和subtitle职责未删改。

初次新增pending image roles被strict bootstrap拒绝：generated_video只允许一个pending video role。这是known-no-effect，Production目录当时无文件；撤回该candidate，未改validator。随后复用现有bound first_frame角色，`CanvasAuthoringBundle.bootstrap`→唯一committer→`initialize_canvas_graph`→标准`load_production_project`真实重开成功，Manifest revision3。只是项目数据/graph；没有QA policy或媒体acceptance，不再沿用此前“Production为空”的current描述。

证据在 `runs/canvas-jieshi-original-s01-s02-20261013-001/original-input-preview-20261014/`：

| Evidence | Actual conclusion / boundary |
| --- | --- |
| `rejected-pending-image-roles.json` | 拒绝原因、候选撤回、known-no-effect；没有POST或Production write |
| `inspect.json`、`author.json`、`preflight.json` | 当前数据重新运行共享三个入口；不签真实图片/video Gate |
| `request.json`、`preview.json`、`native-body.json` | `SeedreamImageProvider.preview`实际生成首张exact candidate；1152×2048 PNG、固定model、无reference，禁止transport/credential回调未调用 |
| `operator-bound-proposal.json`、`receipt.json` | 实际决定时间起一小时的拟议内部上限；不是qualified profile、调用授权、reservation、intent或permit；过期必须重新prepare |

当前project data SHA `cbc4682c543529d07297205f01e6af4df19016d80677599d1d48a88fa0b8b74f`；base prompt SHA `ce6fcc5ee93f034dcf2385bffb936d2e088fbf0663f0659b1860bf0bc1a264d7`；native body SHA `d48502a7bd27fd80786e7f54cf8e56a06b26e08dbddd54a10cf24695f5812e1d`，2819 bytes。Parent实际校验三项current snapshot pointer、native body/settings/完整prompt、无reference egress、未active QA，均PASS。后续edit的actual base identity/bbox以及视频first-frame/source_video依赖仍未产生；不把source-native诊断写成完整qualified视频request。

本次只有ordinary data/prose修改，无共享code或Gate变更。适用Harness receipt为 `.agent/harness/runs/jieshi-original-first-preview-20261014-r1/receipt.json`，以实际receipt及fresh verify为准。Risk Gate在最终exact snapshot验证后判断；mapping不冒充implementation review。原新图片/视频POST继续为0；旧B额度、历史11视频计数及全部receipt未改。

## Raw Listening Route Checkpoint — 2026-10-14

受管只读Kimi invocation `c2d12ad7-8593-420d-bfac-e0fd970b0f1d`，sealed deep、qualified Docker containment，actual k3/max三次authenticated requests，PARSED/exit0/未截断；worker report SHA `80ed564df93412ea19b1c998d39ed6327498b23dbd60f4c0468562d9b72e5bb9`。九个冻结source当前hash全部一致，六个source实际Read完整；原canonical报告按hash复制。证据 `audio-review-route-20261014/{receipt,report,parent-adjudication}.json`。Standing Kimi授权不授予图片/视频POST。

Parent确认raw `CanvasProductionService.evaluate`→`review_generation_attempt`的controlled verifier与marked source validator均拒绝human；缺可信真人host/实际听音环境。最终 `review_canvas_delivery` 已有独立human whole-playback、full_playback/1000要求及exact render/one-use permit验证，不能补签raw Gate。最小共享接点已存在于presentation_verifier/VerifiedEvaluationBinding/one-use recording proof；缺实际presentation→answer和selected actor的可信采集，而不是缺一个允许任意JSON填写PASS的enum。本候选尚未active QA，不能声称真实音义profile/measurement方法已sealed。

未新增假human verifier、未声称听过、未把ASR或网页播放当semantic PASS，未重分类历史attempt09。声音恢复条件为qualified可听音analyzer/selected authority，或实际集成并验证exact-bound真人presentation host后由真实人听判。未满足前不提交视频；图片准备成功或新预算授权都不能解除这条依赖。

完整新单元仍是最多2 PNG+2 Fast4s/480p原生声音、零重抽，内部各50/合计200 CNY；非价格/账单。首张输入已可审阅，可集中请求新单元授权；之后也只在实际前序依赖及逐次fresh gates满足时执行，不消费旧B、不提交声音证据仍不可验的镜头。这是授权缺失与能力Gate分离的真实阻断，不宣称只要授权就一定有合格视频。自动learning再次为 `no_candidate`：新增只读mapping与candidate request，零新媒体，不构成独立质量实验。

## Authorized Base Execution And Stop — 2026-10-14

用户随后明确回复“授权”，沿已发布共享image owner实际执行上述有限单元。证据根为 `runs/canvas-jieshi-original-s01-s02-20261013-001/authorized-unit-20261014-001/`，`unit-authorization.json` 的 scope SHA `14458924df070bd0c71fcfee9c4f6959d3aff73121eb46cf587909c7e8597e5c`。边界保持2图片、2视频、各50/总200 CNY内部 upper bound、零重抽；旧图片/视频单元和历史11视频不重分类、不重置、不挪旧B。

初次 exact supplier lookup 因进程未接同用户D-Bus session而失败，transport调用0，canonical receipt `6935f89d86475dce2075f8d1d96e03f8b448ac2b4a90c660f5dab6d1c1c4eca9` 为 `KNOWN_NO_EFFECT`，原reservation已释放为actual cost0。只修复已核实的session注入，仍用原exact injected supplier；readiness实际通过，没有查替代secret source。封存一次 task-necessary known-no-effect runtime恢复，保留旧attempt/receipt，gen_revision1→2仅区分新request identity，native模型输入2819 bytes及SHA `d48502a7bd27fd80786e7f54cf8e56a06b26e08dbddd54a10cf24695f5812e1d`不变，未扩额度或复用permit。这不是重抽已生成素材。

恢复attempt `original-preparation-base-20261014-qualified-001`、request fingerprint `4225a10af7b88649f33bbfa08f8df705363780f78b07abae1847dcd230845801` 经 `generate_remote_image_asset` 真实POST一次。fresh exact profile/window、preview、budget reservation、egress、durable submit intent和one-use permit均沿现有owner核验。Provider receipt `aa2c38927dace8d98eddd50dc005e9748a56b70764b9ca755827caf369ff1469` 是 **ACCEPTED**；原PNG与wire PNG均已落盘：`production/assets/files/14ce8688fd567c1d2ff7518a1de112cd505e5dec395bf22299219a00fed3ec73.png`，SHA同文件名，1152×2048，4,265,121 bytes。标准result/provenance validation及wire/local同bytes实际PASS。

本地activation随后失败：Manifest revision12，image attempt `outcome_unknown`、phase `materialize`；paid phase仍 `accepted`。Registry没有准入新图，candidate pointers为空。write-free重建同一持久result并调用shared preparer/validator，实际重现 `IMAGE_REQUEST_INVALID: Image candidate resolution contains an unrelated dependency node.`，位置 `production/image.py:1212`；Manifest bytes前后不变。没有放宽guard、手写candidate pointers、猜mixed state或再POST。已保存的PNG必须保留，不能把本地unknown误报为Provider未知、未返回图片或预算被冻结：budget revision5、blocked=false，50 CNY upper-bound reservation为reserved，actual cost尚null；不是实际账单。

`runtime-repair-001/execution-receipt.json` 保留原错误码；首次 `current-unknown-boundary.json` 的外部结果恢复建议被 `current-state-reconciled.json` 明确纠正为paid ACCEPTED/本地materialize失败，不覆盖历史。`materialization-diagnosis.json` 绑定exact PNG/result/provenance和无mutation复现。现有 `paid_provider_no_effect_reconciliation` 仅支持video的verified pre-transport failure，不能用于此已POST且ACCEPTED的image释放预算；本轮没有执行该reconciliation。

## Exact Base Visual Review

在同一已封存 `base-review-contract.json` 下，Parent经 `view_image(detail=original)` 实际查看exact PNG，并独立测PNG bytes/尺寸。`base-image-review.json`保存每个required ID和观察；这属于技术准备图的实际审查，不是canonical raw-shot QA、human正常速度视频验收或后镜准入。

| Required finding | Verdict | Actual observation |
| --- | --- | --- |
| base-eight-entities | PASS | 七名坐姿人物加门边苏遥，共八名实体，角色服装可辨 |
| base-eight-matched-reflections | FAIL | 上方八人反射倒置在车顶平面，不是原要求的对应侧窗几何，不能认定完整正确窗内倒影 |
| base-linyan-identity-props-hands | FAIL | 林砚坐姿/工牌/黑手机可见，但双手接触手机，左手未为空 |
| base-other-identities-props | FAIL | 正面苏遥用解剖右手持乳白手机，左手垂下，违反左手职责 |
| base-camera-space | FAIL | 倒置车顶映像替代本人/侧窗对应关系，林砚后方实际侧窗没有所需映像 |
| base-isolated-editable-reflection | NOT_EVALUATED | 几何未通过，不制作猜测bbox或宣称可保护七倒影 |
| base-png-and-unburned-caption | PASS | exact 1152×2048 PNG，无故事字幕/说明或拼图，保留预先声明的厂商watermark |

全项不PASS，结论 **QUALITY_FAILURE / STOP**。没有第二张edit、重抽、video submit或自动fallback；剩余图片为后续同源编辑，不能挪为换底图。新增实际图片POST1/2、视频0/2，历史视频仍11；S01/S02 raw QA、实际状态交接、原生音轨/字幕、canonical trim、HyperFrames及human1.0x均NOT_EVALUATED，完整前15秒和故事AC-7仍未交付。原source/native输入未删改；没有继续生成旧抬手机B。

恢复需要可忠实准入的准备素材与可审阅新输入；本单元零重抽不能自动扩大。shared candidate需按P5精确比较查明无关dependency frontier，并通过唯一owner显式处理本地materialization；不能白名单无关节点或为了准入删S02。视频之前仍需qualified可听音且可登记的真实证据路线。修正输入/有限新调用必须有适用明确授权；已有授权不再次请求，当前失败不以“继续”或授权文本代签PASS。

## Bounded Image Repair And Stop — 2026-10-14

用户最新“继续做图啊”对应明确有界修复，未自动转用旧edit/B额度：保留已POST1图片，最多再一次修正base和一次只有全项PASS后同源edit，累计图片上限3；单调用50、总200 CNY内部operator上限保持，非价格/账单。scope SHA `341f81647cfb85e8eb09c32d0110389d87bf3afcf7d3cebdc05371f626cd9a5a`，证据根 `runs/canvas-jieshi-original-s01-s02-20261013-001/image-repair-20261014/`。实际只新增1 POST，没有自动重抽/fallback、没有edit或视频。

### Shared Engineering And Actual Old-State Closure

真实frontier diagnosis发现bootstrap未投影的两个既有asset节点，不是本次新增素材变更。新 `image_candidate_frontier.py` 通过同一P5的write-free baseline projection，仅排除desired未变的既有nonfresh/registered asset节点；已变无关节点仍拒绝，不删除S02、不造第二timeline。canonical `close_remote_image_materialization_failure` 只处理完整retained result且paid ACCEPTED/SETTLED的本地失败；typed receipt/reader/recovery均绑定原request/result/provenance/PNG/wire/paid/base。真正paid unknown、mixed、stale、缺证/tamper拒绝；不POST、不激活、不释放原reservation。

`state_commit_attempt_contracts.py` 承接新增optional pointer/validator和既有serializer，避免继续扩张大型models。旧None字段完全省略，旧hash/serialization兼容。共享工程提交 `0234fc55e3be9bb188db1ab8ca7a5ec12acd0066` 已push，`git ls-remote origin refs/heads/main` 实际核验相同SHA。

受管read-only Kimi mapping invocation `9b900f46-66fc-458b-b08b-1f21b3fe79f9`，sealed deep/qualified Docker、actual k3/max、3 authenticated requests、PARSED/exit0/未截断。canonical redacted report SHA `550c9cc41018ab37ff1548fafe08239048f4408dc49614ee7e0635af91fc0453` 保留，冻结read hashes在编辑前核验；不还原redacted内容。Parent确认frontier问题，驳回“现有recover能关闭unknown”和“Registry activation即accepted S01”；mapping不冒充implementation review。native bounded worker只负责failure leaf/test，Parent接回ownership并完成集成与最终diff裁决。

valid red包含public Canvas bootstrap frontier失败和closure API尚未实现时6 failed/1 passed；更早fixture/import错误不当产品回归。相关旧candidate回归341 PASS；serializer迁移后的模型/新boundary suite309 PASS。最终 `.agent/harness/runs/jieshi-image-materialization-20261014-r2/receipt.json` 对非空15 owned paths、tree `90419835fe0b4846e2af2aea71e711e05a4c0eda` 实际通过：20 selected checks，15 executed PASS、5按同轮full Production覆盖跳过；full Production **4007 passed/3 skipped/2608 deselected**，final image136 PASS、Seedream/shared remote-image38 PASS。首次r1因models增长触发Architecture FAIL，保留未覆盖的后续checks，不伪称r1完整通过；移出serializer后r2 Architecture PASS，reader仅7行delegated integration的WARN保留，未改baseline。

fresh receipt命令首次误传RUN_ID，提交后原staged receipt在当前main自然stale。未覆盖receipt或伪造fresh stamp；通过一次仅验证用disposable checkout重建原HEAD+exact staged tree，canonical `receipt_freshness` 全项fresh=true，且已提交tree等于已测试index tree。`snapshot-revalidation.json` 保存对应关系、原receipt hash与真实diagnostic；验证checkout不用于开发，没有重复长回归或Provider调用。Risk Gate在final native verification后为 `KIMI_REVIEW_NOT_REQUIRED`，理由和精确snapshot/hashes见 `implementation-review-risk.json`：变更不能改active tuple、退款、重放paid POST或关闭真正paid unknown；无remaining重大implementation gap。素材质量仍由实际QA，不能以mapping/reviewer代签。

严格实际重开旧PNG/result/provenance/paid joins后，唯一owner显式封存旧attempt：Manifest12→13，local FAILED、paid仍ACCEPTED，closure hash `5e0e40ffa5ea45400898164f6745711c2b39a0ecb5930a52838f0584f14cfd57`。原PNG、active project/Registry/graph、dependency states、budget pointer/bytes全部前后相同，POST=0；证据 `preclose-evidence.json`、`closure-execution.json`。旧QA FAIL没有改为PASS，旧完整媒体和全部副作用历史保留。

### Exact New Input And Paid Execution

[修正文字](../canvas-projects/jieshi-original-s01-s02/S01-preparation-base-repair-input.txt)3015 bytes，只具体化竖直侧窗/正立反射/不反光车顶和左右手；人物服装与固定空间段同旧prompt逐字相同。原S01/S02 source/native输入未改，点名广播、对白、动作、摄影和字幕职责没有删减。技术base仍要求正常八倒影供后续定位，不是原S01首帧，也不送video。

`base-001/native-body.exact.json` 使用actual adapter settings/JSON顺序，3171 bytes、SHA `d35b1ba65447f436021f6b157a2c02ed6c0aeb5486d9535b383fac7f970c3c7f`；早先sorted-key body只为语义等价预览，`native-body-exactness.json` 明确纠正，未用该旧SHA声称真实wire。实际transport observation与exact body全bytes一致，headers/credential值未记录。

attempt `original-preparation-base-repair-20261014-001`，request FP `c5e32912fd1bd00b8bf0afc26d40133305cc95a5bfea9d1c3a0523d633c03011`。submit前实际核验当前profile/window、current canonical count/state、exact injected supplier readiness、preview/opt-in/egress；shared committer逐次执行budget reservation、durable intent及one-use permit。实际transport调用1、HTTP200、零retry；09:37:31 UTC返回时Manifest19，local SUCCEEDED/activate、paid ACCEPTED，canonical技术素材已准入，不是QA acceptance。

原PNG SHA `ba9eb952c5606333727198800fa593abce806b3c239188425ebb7b27087cab4f`，1152×2048、4,671,205 bytes，`production/assets/files/<SHA>.png`；result FP `b2fef9aac736035c4641f5c1fb946936223200bedbf306165424bae121111c78`，provenance receipt `9f098252dc0ec8c833690d2b4fce6f7a4615c6b08739dbf1ac72fb7ea3581462`。标准loader实际重开joins成功，wire/local原字节保留。

### Actual Image QA And Stopping Boundary

Parent通过 `view_image(detail=original)` 实际看图，沿submit前sealed七项review contract，不用Provider成功或coverage代签。`base-001/image-review.json`：**1 PASS/5 FAIL/1 NOT_EVALUATED**。

| Required finding | Verdict | Actual observation |
| --- | --- | --- |
| base-eight-entities | FAIL | 只见林砚、陈立、周伯祥、郭向东、沈嘉程、何静、苏遥七名实体；海军蓝风衣许雯缺失 |
| base-eight-matched-reflections | FAIL | 改为正立侧窗，但苏遥样貌的立姿映像在不同窗重复，不能逐人认定八个完整对应映像；若干坐姿反射暗/遮挡 |
| base-linyan-identity-props-hands | PASS | 静态林砚左手空、右手唯一黑手机分离，工牌/蓝挂绳及坐姿可见；不证明原S01动作 |
| base-other-identities-props | FAIL | 苏遥左手乳白手机与何静膝上袋改善，但许雯缺失、郭向东多出黑手机，完整inventory不通过 |
| base-camera-space | FAIL | 蓝椅/银杆/侧窗改善，但沿身体、膝腿及地面明显俯看；原坐姿眼高斜侧中广景及本人下方/窗上方构图未建立 |
| base-isolated-editable-reflection | NOT_EVALUATED | 不能可靠定位唯一完整林砚映像并保护另外七个；未编造bbox |
| base-png-and-unburned-caption | FAIL | PNG尺寸通过，但左上额外生成“界蚀”故事标题，超出预选原生watermark；canonical hook字幕仍未制作 |

本轮 **QUALITY_FAILURE / STOP**，不edit、不生成video，不把剩余edit次数挪作重抽。累计原准备图片POST2，当前修复用1/2，余1只能全PASS后的edit；原单元video0、历史video11全部保留。没有原S01/S02 exact MP4、accepted前镜、actual state、后镜QA、原生音轨/caption/trim/HyperFrames成片；human1.0x和完整故事AC-7 NOT_EVALUATED。两镜7秒与原前15秒S01–S04映射始终分开，声音路线仍有独立EVIDENCE_REPAIR_FIRST，未伪称听过。

最小恢复条件是能保全完整cast/映像/摄影、无标题污染的可审阅新输入与有界attempt决定，然后实际base全部required PASS；本次失败不能直接晋级edit或video，不能删人物/倒影/原对白来通过。共享materialization确定性阻断已解除，当前剩余是实际素材质量，不再以缺Skill或engineer PASS解释为媒体成功。

## Generation Workflow Research And Input Gap — 2026-10-14

用户要求核查社区是否用类似 ComfyUI 的生成工作流，重点为即梦。新增
[研究报告](../research/2026-10-14-jimeng-community-workflows.md)，区分创作者自述、对别人作品的复盘、教程目录、官方 UI/API/工作流文档和本项目当前代码；没有因研究提交任何图片/视频或改变 Production 状态。

### Verified Findings

- 创作者案例先做角色/场景参考和构图示意，再逐镜生成、检查、局部修正；也承认多人、空间镜像和精确手部动作失败。少数案例不证明普遍做法，更不证明该地铁七倒影关系可解。
- 即梦/Dreamina UI、Ark API、ComfyUI 本地模型与 ComfyUI 云 API 节点为不同执行面。ComfyUI 官方 Seedream Pro 节点需要账号/网络，把同一远端请求搬入节点不会添加本地 ControlNet 条件。
- `seedream.py` 实际只发送 prompt 与可选一张 scene PNG；当前未暴露多角色参考、mask/区域保护或分层输出。前两次原准备生成使用纯文本，已有单参考能力未用起来，不能用 Skill 数量或工程 PASS 解释素材成功。
- `comfy_image.py` 的两条 sealed edit lane 各有两个参考槽，但拓扑没有 mask/inpaint、pose/depth ControlNet。代码存在不证明当前 host 模型/service live-ready；本次未安装或运行。
- Ark 官方文档列出多图、坐标交互与图层拆分，不能推导二值保护 mask 或 clean plate 质量。动态正文抓取受限；Chrome MCP 因已有 profile 占用未能打开，没有接管/关闭用户浏览器。实际界面及新增 API exact wire 仍未验证。

### Parent Adjudication And Recovery Direction

受管只读 Kimi invocation `fd9a2ab6-88ed-423f-9d94-f55f5c880fa8`，sealed contract
`63534dc0c3a1a3467ea6a3ff9c4defff130e4a779253731a6031d23056b5543a`；Parent 核验
route qualification、k3 model identity、containment、四个 artifacts 与全部 observed-read SHA，均匹配。
receipt/reduced adjudication 见
`runs/canvas-jieshi-original-s01-s02-20261013-001/jimeng-workflow-research-20261014/`。
它是能力映射，不是 implementation review 或 media acceptance；`PARSED` 不代签质量。

Parent 不采纳“必须再生成八个实体全部可见、八个正常倒影的底图”的推导。原镜构图含八名角色，七个倒影可承担其中角色的可见职责；原首帧始终是林砚映像缺席。两次旧技术base仍按各自sealed contract保持FAIL，不倒改历史。

本窗口实际查看历史 `historical-opening-review` PNG
`4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`，其侧窗与本人构图接近原目标；只可用于布局审阅/准备参考，尚非 accepted S01，也未在 Scene 注册为新的视觉职责或发送 Provider。

下一输入应把地铁布局、镜头构图、角色/道具、窗面与七倒影对应关系及 clean plate 准备成可审阅资产，再经现有 inspect/author/preflight。必须实际确认只处理林砚映像并保护其余七个；不能把坐标prompt当保护遮罩、把未准入旧底图当 accepted 前镜。若确需多参考、mask或分层，先做目标必要的共享 contract 适配及验证；不新增故事执行脚本/第二timeline/renderer，不直接复制社区无限重抽流程。

### Verification And Learning Boundary

本次为 research/record 文档修改，无 Provider/committer/schema/Gate 变更；Parent 风险判断为无需 implementation Kimi review，不叠加 reviewer。最初 `make harness-inspect` 使用系统Python因缺PyYAML失败；按现有 `.venv` 与 `PYTHONPATH=src:.` 重跑inspect成功，未新增依赖。文档最终exact staged验证由
`.agent/harness/runs/jieshi-jimeng-workflow-research-20261014-r1/receipt.json`
记录，不能据此宣称生成效果。

`record-ai-video-session` 在研究稳定checkpoint更新当前record；`distill-ai-video-learning`
评估为 `no_candidate`：没有新增媒体对照或候选工作流实测，外部案例与代码能力映射不构成本项目的新独立实验。没有采用/修改 Skill、Policy 或 Gate。原本声音缺口、逐镜QA、human1.0x、0–7秒与原0–15秒边界及完整故事AC-7保持。

## Native Masked Image Workflow Implementation — 2026-10-14

用户明确要求直接用原生subagent实现作图工作流。Native Codex继续拥有集成、最终裁决与publication；三个原生任务职责不重叠，`image_workflow_seam`只读核对消费者，`image_mask_contract`实现输入/输出保护校验并追加core-only supervisor切片，`comfy_masked_workflow`实现sealed Comfy图与adapter。worker均完成并归还ownership后Parent接回修改；无第二timeline/state库、故事执行脚本或新依赖。spec/plan完成Parent self-review，按 `superpowers:writing-plans` 持久化既有授权范围。

### Shared Contract And Workflow

- 新 `edit_mask` reference仍归当前Scene/Registry，只有local mask请求采用 `ai-video-image-request/6`；旧request/profile/workflow字节及hash兼容。input职责固定为Character身份参考、Scene待编辑原图、同Scene binary mask；mask白编辑、黑保护，不自动推断bbox或生成mask。
- 新profile `workflows/profiles/p7_1_qwen_masked_edit.json`，lane `qwen_image_edit_2511_masked_local`，sealed profile hash `d9179d4f83a5572d09a14778587f9cb836eb603dc0ade6aacfe27650bfbf35b7`。Scene进入Qwen image1与latent，Character进入image2；mask进入latent noise mask和最终 `ImageCompositeMasked`，目标仍是原Scene。请求尺寸须为8的倍数，source/mask尺寸一致、PNG不透明且mask仅0/255。
- `image_edit_mask.py`在input、candidate activation及standard reader复验registered bytes/identity/geometry；output所有mask=0的RGB像素必须逐像素相同。保护承诺是像素，不是整PNG文件hash相同；mask内正确性仍靠真实QA，不能由composite签七倒影或原剧情PASS。
- 共享 `CanvasProductionService.prepare_image_workflow` 与既有CLI同名action仅做无副作用准备，输出exact request/preview/profile。该action不加载operator runtime。真实生成仍通过现有注入provider、authorization与 `ProductionStateCommitter.generate_image_asset`，candidate沿 `canvas_image_candidate_preparer`，P5/Registry/provenance/replay保留唯一owner。
- Supervisor新增显式 `--core-only`，禁用custom/API nodes并设置HF/Transformers offline；默认启动行为不改。没有增加ControlNet权重、pose/depth路线、多层renderer或Seedream云mask能力。

实现与接口见 [共享Harness文档](../canvas-production-harness.md)、[spec](../superpowers/specs/2026-10-14-canvas-masked-image-workflow.md)、[plan](../superpowers/plans/2026-10-14-canvas-masked-image-workflow.md)。研究报告顶部同步当前supersession；旧“无本地mask”事实保留为历史，不改两次base的sealed QA。

### Actual Verification And Runtime Boundary

工程证据 `.agent/harness/runs/canvas-masked-image-workflow-20261014-r1/receipt.json` 绑定非空23 owned paths、base `0765a404a046cd59c3adcb03112e7304e360e439`、index tree `a60c3027934ba7c62013027320a21900b3438cf4`。18 selected checks中16实际执行PASS，2由同轮reader/state覆盖跳过；无unmapped fallback。包括Production reader569、state962、Canvas218、image172、Seedream38、supervisor18项测试；不同suite的重叠测试不计为独立质量证据。新增测试覆盖selected mask拒绝、三引用lineage/readback、fake provider坏保护像素不激活、exact replay、CLI禁止加载runtime、核心拓扑篡改及旧profile字节。

Architecture PASS保留两个已有大文件增长WARN（image有效行+10、reader+4），没有刷新baseline或增加例外；拓扑独占新module，Comfy adapter缩减。提交前canonical `verify-receipt` 实际 `fresh=true/closure_eligible=true`；提交tree与该index tree完全相同。共享工程 `d37d0482e4a0d6205b2c546ba010e24433dccd8c` 已push，`git ls-remote origin refs/heads/main` 实际返回相同SHA。提交后不把旧staged receipt冒充当前fresh，而是保留已验证snapshot→commit tree对应关系。

`runs/canvas-masked-image-workflow-20261014-001/runtime-readiness.json` 为本机**只读**profile preflight实际PASS，耗时36.312秒；完整测三模型bytes/SHA、ComfyUI commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa` 和所需14个node/input。已有Qwen diffusion40,861,031,560 bytes、text encoder9,384,670,680 bytes、VAE253,806,246 bytes均匹配sealed profile；未安装/下载模型。预检使用明确标记technical fixture，非原S01 source，不新增媒体样本；`generation_calls=0/model_inference=NOT_EVALUATED`。

Supervisor实际启动任务自有unit `ai-video-comfyui-6970131d868d4c7faec099f4894ee27c.service`、invocation `2638eaeb66c94102bb7a113174d8bf15`，strict loopback/core-only；完成只读核验后先验证同unit/invocation再停止，实际inactive/not-found。`runtime-supervisor-binding.json`、`runtime-stop.json`保存实际所有权和停止结果，没有接管foreign service。本预检只证明该次readiness，不是持续在线或GPU推理成功。

最终Risk Gate为 `KIMI_REVIEW_NOT_REQUIRED`，exact snapshot、owned hashes、spec/plan与fresh receipt以及三个trigger逐项判断写入 `implementation-review-risk.json`。未改credentials、paid ledger、egress或unknown恢复规则；existing intent/permit/committer仍独占，protected-pixel failure在激活前拒绝。剩余实测画质缺口需真实模型/媒体QA，不能以code reviewer代签。原生delegation结果不是独立implementation review或acceptance。

### Original Story And Learning Boundary

本实现新增真实图片/视频调用均0，原Production/paid budget未变，两次旧FAIL不重判。原场景尚未按新route注册source/mask；历史review PNG宽941不满足新lane尺寸契约，任何准备必须显式保留原bytes并形成新asset/revision，不能偷偷改图或把review图改为accepted S01。原首帧七完整倒影、林砚缺席及左手/右手机职责均保留；不重引入“必须八实体全可见/正常八倒影底图”的额外要求。

后续仍须实际准入可审阅输入、local generation及原S01专属QA；S01/S02逐镜MP4、actual handoff、声音语义/时序/口型、canonical字幕/trim与HyperFrames、human1.0x均未完成。两镜7秒不代表原15秒S01–S04或完整故事AC-7；声音路线仍有独立 `EVIDENCE_REPAIR_FIRST`。

本稳定checkpoint按 `record-ai-video-session` 更新同一主record，自动按 `distill-ai-video-learning` 评估为 **no_candidate**。技术fixture、scripted tests、runtime预检及多个proof层不是新独立画质实验；没有实测本地workflow与Seedream的可控对照，也没有更新既有Vidu claim的exact媒体证据。原Evidence Index不添加假媒体attempt，不修改Skill/Policy/Gate、不刷新RAG或全局memory；record没有触发新的媒体、Provider、research或额外全套测试。foreign dirty/staged均保留，只提交当前owned路径。

## Actual Local Masked Generation And Targeted Repair — 2026-10-14

用户继续后，原生mapping确认新mask/crop/padding没有合法原node/human-web import接点。共享 `production/image_preparation.py` 复用Registry/PreparedArtifact，独占显式最小8倍数padding、crop、binary region mask与source/operation receipt；标准reader重放同一leaf验证。Native worker18项unit测试，Parent补APNG拒绝、如实 `local_pixel_preparation` origin与typed loader错误；真实标准loader/revise的tamper测试先RED后GREEN。focused suite61 PASS，工程 `49485ee5bfff539e4ebb9a5902a37c0dd501e0e3` 已push并核验remote main。

`.agent/harness/runs/canvas-image-preparation-20261014-r1/receipt.json` 绑定exact12 owned-path commit range：16 selected checks中15实际PASS、1同轮reader覆盖skip，提交后fresh=true；Canvas238、reader569、image172、image-state118、Seedream38项通过。Architecture PASS，reader薄delegation有效行+5 WARN保留。另一个writer已暂存AGENTS/playbook，采用path-limited commit保留其index，未夹带。final Risk Gate按最新native-only规则为 `NATIVE_REVIEW_NOT_REQUIRED`，source hashes/snapshot及三个trigger见 `local-masked-20261014-001/input-preparation-review-risk.json`；不调用或探测Kimi，原历史route保留。

### Exact Input And One Actual Submit

证据根 `runs/canvas-jieshi-original-s01-s02-20261013-001/local-masked-20261014-001/`。历史布局PNG仅作未accepted准备source，右补3px到944×1672，不缩放；Lin头肩crop352×480；binary mask覆盖三个玻璃内部区域。三资产原始来源、操作、RGB、SHA及content-addressed receipts已实际检查，`canonical-input-binding.json`记Manifest19→21；旧Registry/assets/attempts全部保留，Shot原intent字节不变。Lin Character revision2、opening Scene revision2按唯一committer准入；不是原S01 accepted state。

Actual request `2d5994083367b056436bd7bb98b2cccd33216de31cb9d4caa5a6054ea07c85ec`，seed2026101401、profile d9179d4f…，exact `request/preview/execution-profile/authorization/workflow` 和静态rubric均在submit前封存。operator误用不存在的budget字段在进入Provider前失败，Canonical attempt/permit未创建、transport0；核对Manifest21和空event目录后重开同一request/authorization，改用已存在 `active_paid_provider_budget`。`operator-setup-known-no-effect.json`保留错误，不视为一次图片生成、不复用permit或重抽。

Supervisor actual core-only unit `ai-video-comfyui-9d02303789fd4e1f99c54cb545464a2a.service` / invocation `8e76c619228a4deca7fd3cfc027da36a`，loopback-only/offline。fresh profile/model/refs预检、durable intent与one-use permit沿原owner通过；Observer只记录exact transport事件，不替代Production state。实际3次local上传与1次prompt submit，job `96d42b33-96dc-49fd-b359-d727da96d727`，无remote/paid/重试；执行214.693秒含fresh preflight。exact PNG `62a4414bdc72f1409c88a2fd145ad4bd06d7c85156f6051d7fb0bc2955d982e9`，944×1672、2,101,450 bytes，技术SUCCEEDED/Registry准入，Manifest25，paid budget pointer不变。

### Actual Image Review And Bounded Next Unit

Parent实际 `view_image(detail=original)` 看exact输出，复验1,096,780 black-mask像素，RGB变化0。`static-image-review.json`：2 PASS（保护像素、无文字单PNG）、4 FAIL（他人身份、七完整坐姿/站姿倒影、道具、车厢几何）、1 NOT_EVALUATED（窗内新增未能归属的深外套浅灰衣男子，不能签Lin映像缺席）。广域编辑换了脸/服装，把暗门换成白墙，保护条旁残留旧人物片段；不称“保护PASS=原剧本PASS”。首个local unit1/1用完且STOP，视频0，没有原native音轨、字幕/trim、handoff或HyperFrames。

新有限修复证据 `local-targeted-repair-20261014-001/bounded-local-repair-unit.json` 保留该predecessor与精确FAIL图。最多再2次local submit、每次1200秒、blind retry0，本地累计cap3、paid0：恢复历史布局source，先只处理Zhou站姿并用Zhou自己的身份crop；该target/preservation证据PASS后才只处理He截断并用He身份crop。所有完整首帧要求保持，中间修复图仍不是accepted S01，不推进后镜。unknown或target FAIL/NE、缺新可归因变量或预算耗尽停止；不会由原paid剩余额度、旧B或新agent名字重置消费。

`record-ai-video-session`在首个真实local FAIL checkpoint更新此主record；`distill-ai-video-learning`评估仍为 **no_candidate**。现在有一个新的Qwen实测，source/ref/mask/model/目标合同与旧Seedream技术base同时不同，不能当isolated对照、推断所有工作流无效或外推既有Vidu声音claim。工程保护属性有真实证据，mask内剧情质量仍FAIL；不修改/采用Skill/Policy/Gate、不刷新RAG或全局memory。后续修复状态另经真实新receipt取代本planned段。

## Registry Retention Repair And Actual Targeted Z

### Shared Regression And Native Review

Z输入已经经唯一committer成功authoring到Manifest27，但随后标准loader报 `selected image candidate history is not retained`，未发Z POST。根因是新像素准备合并全Registry时按asset ID排序，移动了此前P7生成图，破坏其精确历史前缀。当前source/PNG/receipt没有损坏；原生 `image_workflow_seam` 只读确认现有recover只处理未完attempt，没有成功commit回滚API。Parent没有改Manifest或绕过loader手工拼状态。

工程先以standard generation→prepare→author→reopen测试复现两个RED，再把准备合并改为保留旧tuple并追加新records。已提交旧排序仅由标准reader的最窄只读successor证明重开：连续hash-bound成功authoring边、所有旧AssetRecord全字段保留、新增限candidate明确引用的IMPORTED/DERIVED IMAGE；原P7 base→candidate append-one、receipt/placement/activation/bytes仍独立验证。普通membership、删改旧record、未引用新增、missing/non-authoring边仍拒绝。matrix/spec/plan同步该边界，没有第二writer、timeline或renderer。

首个候选 `725f2fa81d2dc4d7e514826e4637dcbed367d672` 的exact7路径Harness通过；Risk Gate基于新历史准入可能影响后续canonical effects的后果、branch/chronology剩余语义缺口及对抗审查增益，选择一名read-only native `reviewer_xhigh`（实际 `/root/registry_retention_review`，profile TOML选定，不override、不Kimi）。round1发现REG-001缺原P7 activation下界、REG-002先过滤时间隐藏匹配分支。Parent源码确认并新增完整standard-loader RED，两个非法历史均被旧代码接受。修复后每边base≥原activation且base+2≤后继revision；先检全部匹配成功边唯一再检时间。activation计算保持reader单owner。

最终候选 `a45fa113b2ffb10bbd071bfa51753849aa82c911` focused41 PASS；exact chronology-fix range Harness通过并fresh，reader569、Canvas251、Seedream38项及所有mapped controls通过；Architecture PASS，reader有效LOC +3 WARN保留。原7路径候选的image172、image-state118与其他proof保留为历史，不虚称其receipt对新HEAD fresh。同一native reviewer round2完整有界复审finding set为空；Parent用RED→GREEN和source hashes关闭REG-001/002，不以空findings代签媒体。两owned commits已push，remote main exact SHA已核验；foreign staged AGENTS/playbook和旧dirty docs未夹带。

当前证据根 `runs/canvas-jieshi-original-s01-s02-20261013-001/local-targeted-repair-20261014-001/`：`registry-retention-review-package.json`、`registry-retention-review-r1-adjudication.json`、`registry-retention-review-r2-package.json`、`registry-retention-review-r2-adjudication.json`。工程receipt：`.agent/harness/runs/canvas-image-registry-retention-20261015-r1/receipt.json` 与 `.agent/harness/runs/canvas-image-registry-chronology-20261015-r2/receipt.json`，snapshot范围各自独立。

### Canonical Metadata Restoration

先完整只读重开真实Manifest27，其文件SHA `d342ebd4004631c64676dc31c0800b18f79d138584c2dc83cfba2ccf89d4816c` 未变；不重放Z输入authoring。随后用既有 `revise_authoring` 独立metadata repair attempt `original-s01-registry-order-repair-20261015-001` 提交原最后P7候选tuple前缀＋现有额外records，Manifest27→29、Project5→6。九个AssetRecord、Shot/Character/Scene、旧attempts及paid budget pointer全部相同，只有新Registry顺序/快照与project pointer改变；原坏排序成功历史完整保留。标准reopen PASS，模型调用0。`registry-order-repair.preview.json` / `registry-order-repair.execution.json`提供exact指针及证明；后续生成沿原严格append路径，不扩大只读例外跨非authoring效果。

### Exact Local Generation And Quality Stop

原Z单元上限最多2新submit（Z通过才H）、每次1200秒、本地累计cap3；恢复后新请求 `a6175b8930d3e7bd84ae3bff8bdc6beacc9c73be3973fd6bc1110e5dd6149455`，attempt `original-s01-targeted-Z-generation-20261015-001`，seed2026101501。Character为Zhou本人128×144 crop `4669a45199bacf80ad99ffc4409f8986fe95dee845010695aa92fb2f017a403e`，Scene为原944×1672 padded布局 `1c36a9ea7600c0d5cbc73848f6ffd1731307478027f53937cb8731502fa7e6d8`，binary mask为已注册r2 `06af95640e884cce000773daffc43f2e8024e778d83800e972b7af2f90b930bb`。r1候选遮罩未经注册/submit；本次不以旧广域FAIL图作source，不改原S01/S02动作、广播、对白、字幕或机位要求。

fresh supervisor核对exact unit/invocation、sealed模型full hashes/checkout/core nodes、当前source/registry bytes与三引用；exact request/preview/profile/authorization和实际workflow已落盘 `Z-*.exact.json`。既有committer创建durable intent/one-use permit；实际local上传3次、prompt submit1次，job `cb5464e5-3f42-44b3-b8d0-6931d784d98a`，无paid/remote/retry。端到端202.188秒含fresh preflight，Comfy prompt执行154.22秒。exact PNG `102c1ec74f873a0de8297d2cf9de1477a9ae1cf0b0fc654836e6e8dc7e127557`，944×1672、2,099,914 bytes，creation receipt `a0e7eb163b43e31f02973453bff1a8b5b1be982a5ea12e71eedf65cbfc8cb943`；技术SUCCEEDED/Registry准入，Manifest29→33，paid budget pointer不变。这不是原S01素材质量acceptance。

Parent实际original-resolution `view_image`：Zhou身份/衣物与原图对应、空间保持，但仍在原高度站立并扶杆，没有坐姿、膝上双手。target findings为identity PASS、seated-complete FAIL、geography PASS、preservation PASS。独立像素复验：1,536,514黑mask保护像素变化0；41,854白mask像素中40,439 RGB发生变化，不能解释为“没有运行模型”，也不能解释为动作执行成功。完整static要求仍为4 PASS/1 FAIL/2 NOT_EVALUATED：Z站姿与He右边截断导致七完整倒影FAIL，Lin对应空位几何及全部道具未取得完整证明。

`Z-execution-receipt.json`、`Z-static-rubric.sealed.json`、`Z-static-image-review.json`与`unit-stop-receipt.json`封存已知输出及FAIL STOP。新单元用1/2，剩余H slot没有挪给再次Z；累计local模型2、原paid准备图2、原视频0、历史视频11。无unknown、重抽、remint或重分类旧失败。自有 `ai-video-comfyui-9d02303789fd4e1f99c54cb545464a2a.service` / invocation `8e76c619228a4deca7fd3cfc027da36a` 经supervisor停止，其他进程未动。

### Minimum Recovery And Proof Boundaries

下一有效输入路线须能明确约束Zhou坐姿/几何，同时保持其身份和非目标像素；不能继续依靠相同输入重抽。当前workflow已证明区域保护，不证明pose遵循或原S01 clean plate成功。完整七倒影、对应空位、道具和摄影的静态证据仍全部需要，之后才有资格开始原MP4→project-local video-analysis全PASS→actual state→S02自身QA。普通两镜约7秒、原前15秒S01–S04覆盖、完整故事AC-7与离线工程proof继续分开。

原生声音语义仍EVIDENCE_REPAIR_FIRST；本次没有音视频，未声称听过或正常速度验收。native audio/caption/ResolvedTimeline trim/接点/HyperFrames exact声画和用户完整1.0x听看均未交付。required target FAIL是本单元真实停止条件，不能删坐姿要求或用保护区PASS推进。

`record-ai-video-session`在此真实Gate失败的stable checkpoint更新同一主record。`distill-ai-video-learning`自动评估仍为 **no_candidate**：两个local attempt共用未accepted synthetic底图但编辑目标/角色参考/mask/prompt/seed不同，不是隔离变量对照；技术硬合成保护已由当前contract拥有，不能由两次不同质量失败推导通用Qwen能力结论或修改Skill/Policy/Gate。未找到需material update的相关existing claim，旧Vidu对白claim不在本scope；工程测试/派生crop/mask/多proof层不另计独立媒体。RAG prior failure不重试、不刷新，全局memory未写。

## Community Pose Repair Research — 2026-10-15

针对 Z 仍站立的已知 FAIL，完成 [研究续记](../research/2026-10-14-jimeng-community-workflows.md#pose-repair-follow-up--2026-10-15)：社区有只改姿势却改身份/背景、局部修改不遵循目标和 DWPose 参考失效案例；AnyPose 作者也公开多人/背景失效边界。它们是公开自述与产品/模型作者指导，不是本项目成功证据。

重开 exact `Z-workflow.exact.json` 与 pinned ComfyUI node：实际语义输入只有原场景＋脸 crop，mask 负责 noise/composite，没有坐姿参考或适配 Pose/Depth。40 steps/denoise 1 已实际使用。节点内部 reference latent 缩放与采样 latent 尺寸不同，是待审查的对齐风险，未证明为姿势失败原因。建议隔离目标单人、补明确坐姿/接触几何、通过共享 reference/profile/authoring 接入后再按原位置合成；不能以全图多人 AnyPose、增加 prompt 或盲抽替代。

本轮是资料研究与已有 evidence 核对，新增模型/图片/视频 submit、模型下载、ComfyUI 启动和 Production mutation 均为 0；旧 FAIL、剩余 H slot、原剧情及视频/声音验收边界不变。`record-ai-video-session` 更新同一主 record；`distill-ai-video-learning` 评估 **no_candidate**：公开案例未在本项目受控复现，现有不同目标 local attempts 不隔离变量，未形成可采用的新 bounded claim。无 Skill/Policy/Gate 或 global memory/RAG index 更新。文档研究不触发 implementation Risk Gate，不新增 reviewer；foreign staged/dirty 保留。

## Pose Reference Trial And MCP Execution Stop — 2026-10-15

用户要求先尝试修图、成功后再接工作流。Parent 按当前 playbook 的 Agent-side preference 选择 project-local `gpt-image-2` MCP、显式 `backend=chatgpt-web`，不是 Kimi/外部工程 subagent 或 API fallback。使用 `imagegen` 的身份/编辑底图/姿态参考职责指导，以及 `open-video` 的 known-failure repair 边界；没有改变原剧情或把先试后接变成先建新 adapter。此前 RAG layout mismatch 沿同一任务不重试/刷新，当前标准 loader、源码、原角色/Shot 与 exact receipts重新核对。

试验目录 `runs/canvas-jieshi-original-s01-s02-20261013-001/pose-reference-trial-20261015-001/`。原场景 `1c36a9ea7600c0d5cbc73848f6ffd1731307478027f53937cb8731502fa7e6d8` 和身份脸 crop `4669a45199bacf80ad99ffc4409f8986fe95dee845010695aa92fb2f017a403e` 保持原 bytes；新增944×1672技术坐姿图 `zhou-seated-pose-guide.png`，SHA `61a696b7001f2e778ef8411b2d681e176b79295e3a5dc81946a4b3c127a4363d`、11,440 bytes。它从空白画布按显式 joints/seat anchors绘制，不是模型输出、人物身份或镜面几何成功证据，未改写照片；`pose-guide.geometry.json`保留坐标。初稿膝部弯曲不够清楚，在任何模型调用前修正并实际看图。原图/脸图/姿态图三引用顺序及 SHA 经 `reference-bindings.json`重验。

`request.exact.json` SHA `8811e001d70794f03f8d34edfcdf9d5ea26f20bd53fa907e41d09e84d537fc2b`；新身份 `original-s01-pose-reference-web-20261015-001`，new conversation、n=1、请求timeout600秒；先封存 `rubric.sealed.json` 与 `one-use-call-intent.json`，最多1次 generate invocation、禁止retry。prompt只改老人坐姿、保留身份/邻座/摄影/窗面/道具；原广播、动作、对白和字幕继续由原视频/composition执行。Provider路径与姿态输入均改变，因此即使产图也不是隔离变量的 Qwen 对照。本试验不挪旧 H slot、不改变旧 paid/local计数或假造 Product reservation/qualification。

`browser_visibility`从未启动状态开启专用浏览器；提交前 `backend_status`为ready=true，actual MCP `generate_image` 调用1次。客户端返回 `timed out awaiting tools/call after 300s`，**不证明未发生生成或可重试**。`mcp-call-timeout.json`保持原工具超时类别。仅通过既有 browserConnection owner/loopback校验连接现有页，对同一次完整请求只读取证，没有 Send/新请求/新tab/修改工具。请求在现有页不存在，user/assistant消息数0，因此匹配门拒绝继续collectImages/export；独立复验 document complete但body空白，无main/composer/file input，后续backend为ready=false、starting=true。没有取回图片或视觉裁决；`page-discovery.json`和`readiness-diagnosis.json`保存只含非敏感分类事实，未保存 session/browser URL/private diagnostics。

为阻止已超时的startup以后迟发，核验仅有本次从browser_open=false启动的专用空白ChatGPT tab，且仍无main/composer/messages后只关闭该tab；`startup-stop.json`保存动作/URL hash，不关闭其他浏览器或进程。这个动作不反证历史零POST，remote submit count/outcome仍 **NOT_EVALUATED / UNKNOWN**。`unit-stop-receipt.json`封存EXECUTION_EVIDENCE_GAP和STOP：observed output0、后续调用0、API0、Comfy0、workflow integration NOT_STARTED、全部visual findings NOT_EVALUATED。它是执行入口阻塞，不是坐姿方案或模型质量FAIL。

标准 `load_production_project`在试验前后均成功；`production-before.json` / `production-after.json` 的project bytes、Manifest/Registry规范模型hash及Manifest33完全相同。无Production writes、输入准入或activation，无新视频/音频/HyperFrames；原full S01、真实接续、human1.0x、完整故事AC-7均未通过。本单元1/1 invocation已用且不释放；原准备paid图片2、本地模型图片2、原视频0、历史视频11是已确认历史，不把未知web调用算成0或已完成图片。

最低恢复条件：先由同一次调用的可靠证据完成outcome reconciliation，再恢复并核验实际composer/upload readiness；unknown未关闭前不补发、不改用本地、不remint该intent。取得新bounded候选后，须完整验坐姿/身份/邻座/保护/尺寸，再决定共享工作流接入。

在真实blocker处按 `record-ai-video-session`更新同一主record和研究状态。`distill-ai-video-learning`评估 **no_candidate**：没有新可验媒体，不能验证姿态假设或自动采用社区方案；该工具超时与历史其他MCP问题边界不同，未建立可采用的重复机制。无Skill/Policy/Gate、global memory或RAG index更新。没有源码实现，implementation Risk Gate不触发；Parent完成artifact/状态核对，未新增reviewer。foreign staged/dirty保持，文档checkpoint的exact Harness/commit/push另由实际receipt与Git报告证明。

## Codex Direct Image And Authoring Workflow Rule — 2026-10-15

用户连续明确要求Codex直接接入、自带Generated Image参数和实际效果，随后要求将规则写入工作流。新的独立单元使用 `image_gen.imagegen`，不调用Qwen、ComfyUI、浏览器MCP或CLI/API fallback；原UNKNOWN单元没有重放/重分类。exact request `9cdd1fdf7ea2a660361cd3a5b145ccf9557924d74b31bcb9df1ba70c969610d2`，attempt `original-s01-codex-direct-image-20261015-001`，最多1调用、实际1、retry0。沿用原布局、老人身份crop与明确坐姿图三个角色分工；原图没有被直接编辑或覆盖。`image_gen`返回真实图片，底层模型/采样参数未暴露，不伪称具体model/profile qualification。

图片为 `runs/canvas-jieshi-original-s01-s02-20261013-001/codex-direct-image-trial-20261015-001/s01-zhou-seated-codex-candidate.png`，SHA `f9128ccfde3868ed8aaea420f953e306b37c003e139fd0d85943774eea057e93`，RGB PNG、943×1668、2,027,887 bytes。从工具原始文件exact copy入项目工作目录，原始文件保留，不resize/crop/重编码；`generation-record.json`实测绑定request/output事实，不保存私有session或假model设置。

Parent实际original-resolution看图，并在写规则时重新核对bytes/尺寸/标准项目状态。`static-image-review.json`：同一老人身份衣物、完整坐姿/屈膝/可见鞋、双手自然合放膝前且不握杆、可见邻座/机位关系、非目标人物及无新增文字五项有界PASS；身份不代human attestation，机位不代镜面/镜头标定。原图944×1672与输出943×1668不同，精确保护区等价为NOT_EVALUATED。原最右何静截断仍在，七完整倒影没有通过；林砚缺席对应几何和全部道具仍NOT_EVALUATED，音视频及human1.0x未验。局部效果成立不授权原S01 accepted source、后镜submit或完整故事AC-7。

`production-before.json` / `production-after-generation.json`和规则记录时标准loader复验：project bytes、Manifest bytes/Registry规范模型hash均一致，Manifest33；实际素材导入/activation NOT_STARTED。已确认历史原准备paid图片2、本地模型图片2、原视频0、历史视频11不改；新增内置图片1单独列出，旧web调用UNKNOWN不算作0或完成图片。写规则这一阶段新增媒体/模型/Provider调用为0。

默认规则由用户直接指定，写入 `.agent/context/control-plane-playbook.md` 的 **Agent-Side Image Generation Provider Preference**，详细流程只归 `docs/canvas-production-harness.md` 的 **Agent Image Authoring Workflow**：身份/场景/姿态职责→实际支持的prompt/参考/透明背景字段→有界尝试→图片及完整要求QA→现有generated_source/canonical committer导入。明确不接受ComfyUI JSON/seed/steps/CFG/sampler/latent mask/ControlNet参数，不把语义参考当硬节点、尺寸或像素保护；Qwen仅为已选择的可选路线，不新增Product backend/脚本/状态owner。已有mask路线、paid/unknown/逐镜视频/声音/剪辑验收合同保持。

写前发现playbook已有foreign暂存的native reviewer迁移，与当前生图小节同file；用户明确选择A，授权只改生图小节、独立提交，原暂存保留。原 `AGENTS.md` 及其他foreign paths不编辑/夹带；独立Git index仅用于本次owned patch的隔离提交，不是development worktree或Product状态库。提交后核对原foreign暂存路径、其他blob和playbook原暂存增删内容，不能把另一任务迁移声称为本次工作。

Native Codex Parent串行完成这一有界文档变更；没有源码/parser/lifecycle/credentials/budget/Gate改动，用户未要求independent review，未触发重大后果与验证缺口，Risk Gate为NATIVE_REVIEW_NOT_REQUIRED。前置规则budget检查曾暴露正文超限，仅精简本次生图summary、详细指导留唯一workflow owner后重新PASS，不增registry限额。exact最终commit range Harness必须另核验fresh receipt，工程/文档PASS不代媒体验收。

按 `record-ai-video-session`稳定checkpoint更新同一记录。`distill-ai-video-learning`为 **no_candidate**：单次内置图片能证明该次坐姿效果，不能由模型/姿态输入同时改变推导通用胜率；旧web超时无图片，不算视觉反例。规则属于用户明确的新偏好，不是自动采用Learning Claim；没有制造第二确认、改Skill/Policy/Gate、刷新RAG或写global memory。

## Community Validation Principle And Checkpoint — 2026-10-15

上一工作流规则已独立发布 `96c5ba346b3d27c07438d3e0437be91f37fead60`，远端main已核验。`.agent/harness/runs/codex-generated-image-workflow-rule-20261015-r1/receipt.json`有10项checks PASS；共享工作区保留同file foreign暂存，因此默认receipt freshness=false，不宣称当前dirty状态fresh。通过现有 `isolated_verification_workspace` 核验同一exact commit后fresh=true，证据为同目录 `exact-commit-verification.json`；临时验证checkout已清理，原receipt bytes不改。上一阶段在默认freshness失败后先发起push，顺序不妥，已明确说明并补exact提交核验；后续publication须在适用快照核验完成后执行，不削弱freshness规则、不清空foreign index或重写旧结果。

当前用户要求将“遇到问题参考社区→实际验证→写进工作流”写入 `AGENTS.md`。Parent只新增 **Community Reference And Workflow Improvement**：先诊断exact失败和输入，参考可追溯作者/官方/社区及反例、核对模型工具版本/授权/约束；在known outcome与已授权边界内做最小可归因实测，保全原剧情与已满足项；验证有效且适用范围明确后，沉淀可复用步骤/输入职责/能力限制/验收要求到已有workflow owner。社区推荐/局部PASS不代完整验收，单例不升级通用规则，UNKNOWN不盲重试，具体素材/日志不扩进constitution或第二执行链。

写前精确核对 `AGENTS.md` 原暂存的native reviewer迁移，用户明确选择A：只提交新增原则，原有暂存保留；与上一轮仅针对playbook的授权分开核验。沿已使用的独立Git index只提交本次AGENTS hunk与本primary record，提交后比较原暂存路径、playbook blob及AGENTS原暂存增删内容。其他foreign staged/dirty不编辑，不创建development worktree；Harness标准隔离checkout仅用于exact提交验证。

这是用户明确指定的可逆Agent工作原则，不是Product Provider/Gate/预算/恢复实现变更；Native Codex Parent串行处理，未产生需要CodeGraph/delegation的结构问题。相关documentation/rules/Harness checks按exact scope运行；无用户要求的independent implementation review、重大后果或实质运行时验证缺口，Risk Gate为NATIVE_REVIEW_NOT_REQUIRED。原图/新图/全部receipt保留，媒体/Provider/模型下载/Production writes/RAG刷新/global memory更新均0，不为record/hook追加取证调用或额外测试。

`record-ai-video-session`核对已有稳定checkpoint并更新同一主record；`ai-video-record-2331904e3bd70b88`已以recorded/no_candidate ACK，acknowledged=true。`distill-ai-video-learning`仍为 **no_candidate**：没有新媒体或受控对照，只有用户明确的新工作原则和前次bounded效果，不制造通用模型结论、LearningClaim或第二确认；后续capture按实际新ID另核验，不重ACK旧request。

## Original Frame Completion Attempt And Video Stop — 2026-10-15

用户要求先完成图片、随后视频。Parent沿默认`imagegen`生图入口继续实际原S01准备，不再修改工作流规则或调用Qwen。证据根为`runs/canvas-jieshi-original-s01-s02-20261013-001/codex-original-frame-repair-20261015-002/`。先封存最多2次的顺序单元：H补最右何静裁边，H通过才C补陈立原道具。每次先保存exact参数/前图SHA及一次调用意图，实际输出exact copy，不resize/crop/重编码；原工具输出与全部旧失败保留。

| Actual image / Request | Exact PNG / Geometry | Parent static verdict |
| --- | --- | --- |
| H：`ec84f2686d92d674a6840219eb8249bfd116d4fc80a5067bf7e9afe2c1c8b6ae` | `s01-seven-reflections-H-candidate.png`，SHA `a2239581824f32f1ce4e9982913286bb588ed2085df068fffaa80ae8a8dc5c02`；943×1668，2,165,453 bytes | target PASS：何静头到脚/膝上灰布袋在画内；六坐一站共七倒影、老人坐姿、林砚本人手机/空左手保持。原全镜仍未验 |
| C：`dc249193b5d938df088f4426dece4982c43a7a62c91f96baf372920764178462` | `s01-chen-props-C-candidate.png`，SHA `5c4fe971f222bacda47cc39ae9cb9b5503b0d59e3968e207808a740d5829b099`；943×1668，2,101,348 bytes | 深蓝手机存在PASS；镜面右手和黑耳机不可明确证明，target NOT_EVALUATED，停止该attempt。2/2已消费 |
| 明确镜像画面侧修正：`78091e512ad2621c17d9bf9000efce732401c5246f62d0b6af00fcdd22c4ef57` | `s01-mirrored-props-candidate.png`，SHA `64359f615d10e112ff7aaa68181c3b815cf8178382c199dc4073d17519f810dc`；943×1667，2,116,264 bytes | 后续独立1次有限单元，保留前2次消费，把解剖左右改为明确画面侧；陈立手机降低并改握法，但苏遥白手机仍未移至指定镜像侧，FAIL；陈立耳机/完整手侧及林砚对应空位几何仍NOT_EVALUATED，1/1后STOP |

本轮工具技术SUCCEEDED不等于原首帧PASS。原生镜面持机不能沿用普通正面照左右判断；缺耳机或几何证据不能删原要求。最后图与前图高度相差1px，精确保护区及dimension等价未验，没有隐式尺寸修正。以上为实际`view_image`静态语义检查，不代人类身份、镜头/镜面标定、抬手动作、声音或完整剧情验收。当前有限单元没有继续重抽、fallback或把旧edit/B额度搬过来。

声音能力在本窗口用既有历史WAV `daa154cb46f2a89ce3e95f5dcab6edb019c14a18ea67aef5de4031e0ffeec2d4`重新探测；平台实际返回`audio content omitted because you do not support audio input`。`audio-capability-current.json`保留EVIDENCE_REPAIR_FIRST，未声称听过、未生成新音视频补证。原生`code_mapper` `/root/original_video_readiness`核对共享导入/prepare/QA/presentation接点，Parent重开相关源码与标准loader：Manifest33、Project7、`qa_policy=None`、原视频attempt0。Agent使用CodeGraph时创建`.codegraph-cache`，属其read-only scope以外的派生缓存副作用，已披露；无源码/Production/Provider变更，不冒充纯只读执行证明。

当前`prepare`缺selected generation QA投影；可信raw听音host或qualified audio analyzer也未接入。`ControlledPresentationVerifier`只接受technical/analyzer，不可伪造human answer；最终P6完整1.0x听看不能回签raw逐镜Gate。共享`generated_source`/`revise_authoring`存在，但完整素材使用要求未过，因此本轮不导入/激活；`production-after.json`核验project、Manifest和Registry模型hash与上一exact快照全部相同。原授权的2次Fast4s480p/native视频仍未消费，历史授权不是当前qualified runtime、reservation或permit。

恢复条件：修复并取得原首帧完整道具/镜像几何证据；在现有QA/presentation owner接入真实exact-media听音证据并选定完整原镜policy；再核验current video runtime/profile/window与逐次paid gates。原S01采用3s、S02采用4s及原文/广播/对白/字幕全部保留，S03/S04仍是原前15s的后续映射，不能把两镜7s或这张静图宣称完整前15s。没有accepted S01、handoff、S02或HyperFrames交付；human1.0x/完整故事AC-7仍NOT_EVALUATED。

使用`record-ai-video-session`更新同一主record及候选README状态锚点；`distill-ai-video-learning`评估no_candidate：同一递进图片链的不同修复目标与提示并非两次独立支持或受控多臂对照；H局部成功也不能支持通用镜面/生图能力claim。没有Skill/Policy/Gate或全局memory/RAG变更。本轮新增Seedream/视频Provider POST及Comfy调用均0，内置修图新增3次；内置工具计费及底层model未暴露，不猜价格/账单。记录期间不额外调用媒体/Provider。原foreign staged/dirty保留。文档checkpoint `c0d16b2137ef86d85955fda86c40f2d260cb29a2` 已push且remote main SHA核对一致；`.agent/harness/runs/jieshi-original-frame-stop-20261015-r1/receipt.json`五项PASS、fresh=true，仅证明该exact文档快照；此处计费边界澄清后的提交另验，不把前receipt伪称验证新bytes。

## Single Object Repair And Known Quality Stop — 2026-10-15

用户继续推进后，Parent重新读取当前原文、latest exact图及共享`inspect`，使用`retrieve-ai-video-memory`取得stale但可定位本record的advisory fragments，不为fresh重试或foreground rebuild。按现有`imagegen`/Agent Image Authoring Workflow封存最多2调用、45分钟单元：先只改苏遥白手机，成功才另封存陈立原道具的exact输入；不把剩余slot挪作同一失败项重抽。前序内置4图、paid准备2图、local模型2图及web UNKNOWN逐项保留。这是任务内已知失败的有界修复，不是扩展Seedream/视频付费额度或重放UNKNOWN。

证据目录`runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-single-object-repair-20261015-004/`。单一底图为旧`64359f61…`、943×1667；request SHA `4db7ce4accb006c62e162fe299199e943bf1234d35e7fa8d87470b08aa44a8a1`，只要求苏遥已有乳白手机由画面右侧移至左侧，并给出当前/目标坐标；原身份、七完整倒影、老人坐姿/何静灰袋、林砚右手黑手机/空左手/衣物、空间摄影及原动作/广播/字幕均保留。坐标是文字条件，不冒充硬mask或ComfyUI节点。没有新写故事执行脚本、Provider adapter或timeline。

实际`image_gen.imagegen`1次、无retry，原始输出exact copy为`s01-su-single-object-candidate.png`：SHA `a1db0247764947b315110ffe166105dcd5927ebc2f5283d142b20fa91b14ed6f`、2,076,608 bytes、943×1667 RGB PNG。Parent在原始分辨率重看：苏遥白手机仍在靠杆/老人的画面右侧，目标 **FAIL**；七个完整他人倒影、老人坐姿、何静包、林砚原道具及无新增文字维持静态语义PASS。陈立手侧/耳机与具体对应空座仍`NOT_EVALUATED`，不以局部PASS签原首帧。尺寸恰与前图相同不等于区域外像素保护；无resize/crop/reencode、无导入/activation。`Su-static-review.json`及`unit-stop-receipt.json`封存STOP，Chen条件不满足、0次调用；未消费slot不能转作Su重抽。

只读原生`reviewer_high` `/root/s01_static_geometry_audit`独立看旧exact图，目的仅是降低镜像空间/手臂归属的不确定性，不是工程final review、第二生成实验或QA authority。Parent确认其Su镜像侧finding；对“陈立手机的screen x即可证明错手”保留`NEEDS_MORE_EVIDENCE`，必须追踪屈肘/跨身手臂，不能照搬坐标推解剖归属。其指出空近座可见但对应关系有歧义，也没有证明确定的车厢几何破坏；Parent仍保留原required geometry `NOT_EVALUATED`，不因advisory severity为non_blocking就降低Gate。结论及裁决在`native-static-critic.json`。

标准`load_production_project`重开当前Manifest33/Project7、`qa_policy=None`；`production-after-canonical.json`重验entrypoint/Manifest/Registry与前次快照一致。早期`production-after.json`误把selected active snapshot hash同历史entrypoint hash比较，得出false；它保留并由新文件解释为方法不一致，不重分类成Production mutation。当前核验同时命名两种hash。之前的local检查因错误Python缺PIL、以及两次误用revision属性名在写receipt前失败，无Provider或Production副作用；后续使用项目`.venv`及实际schema完成核验。

新增内置图1、累计5；新增视频/Seedream/Comfy/音频请求均0，原视频0、历史视频11保持。当前已知质量FAIL是自然停止点；最低恢复条件为能验证执行的局部物体编辑输入/路径，再补陈立手臂/耳机与对应空座layout证据。不能继续仅重写全图prompt、删除手侧要求或先生成原视频。音频工具已打通不能掩盖图像缺陷；S01→S02、canonical音轨/字幕/trim、HyperFrames及human1.0x/AC-7均未交付。

按`record-ai-video-session`更新本primary record及候选README，`distill-ai-video-learning=no_candidate`：同一递进图片链与一次新失败不能证明通用模型限制，也没有验证替代修法有效；不把失败假设写成已验证workflow规则/新LearningClaim。没有global memory写入或前台RAG刷新。纯文档/真实媒体取证不改变代码或权限，implementation Risk Gate为`NATIVE_REVIEW_NOT_REQUIRED`，上述只读视觉critic独立于该gate。Foreign staged/dirty保留；本checkpoint exact Harness、commit/push以实际receipt/Git另验，记录阶段不新增媒体或Provider调用。

## Crop Assisted Hand Repair And Spatial Composition Stop — 2026-10-15

用户要求继续实际做图；本轮使用现有`imagegen`入口，没有新增故事执行脚本、Product adapter、timeline或renderer。`retrieve-ai-video-memory`仅取得stale advisory fragments，继续以原Character/Scene/Shot、exact图及当前runtime为准，不重试检索、前台重建或下载模型。原native5、paid准备2/local模型2及旧web UNKNOWN保持，封存新有限单元时保留前序消费/停止原因，不重放UNKNOWN、不转移旧B或修复额度。

### Hand Repair And Corrected Evidence

目录`runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-crop-assisted-repair-20261015-005/`，最多2次内置调用。实际放大旧图后发现，先前Agent增加的“白手机必须在画面左大腿坐标”被物理林砚头部遮住，与保护前景相冲突；原文只要求解剖左手，不要求该像素位置。调用前以`unit-authorization-v2.json`保留旧版本/0次消费及合计2次上限，明确允许左前臂弯到身前，不删持机手要求。

qualified FFmpeg从原图裁出`[194,300,350,744]`、156×444并显式nearest-neighbor放大4倍至624×1776，`crop-preparation.json`核验逆采样等于原像素；只作模型参考预处理，不是最终修图/Registry准入。实际局部生成`eec68abd39f7bbcddf875c066ff5b375f5c3db3e55edc2b20b775e3f9b45f940`，743×2115；局部手臂归属PASS后，第二次以旧整图为edit target、该局部为动作/道具参考，输出`s01-su-left-hand-full-candidate.png`：`8b2e95271d911c774e9eb97552d89aba282bd08a664dfc0e71b56e39a8739703`，944×1667、2,067,700 bytes。两图均exact copy，无最终resize/crop/reencode，native累计7。

Parent与同一只读原生`reviewer_high` `/root/s01_static_geometry_audit`重看实际像素：苏遥镜像画面左侧袖口经肘连接胸前白手机，另一只手空，**手部局部PASS**；陈立放大图的画面右袖跨膝连接深蓝手机及可见黑耳塞，为其实际右手提供证据，不能只凭手机横坐标判错。这纠正的是观察方法，不抹掉旧FAIL输出。完整图仍FAIL：陈立在过道对面，与林砚近侧空座不相邻；苏遥绿上衣是翻领开襟，而原文要求圆领。`full-static-review.json`保留这两个阻断项及动作/声音/human未验；native工具不支持二进制硬mask，尺寸变化也未归一化，未声明保护区像素完全相同。

### Spatial Reference And Two Failed Full Frames

已按`docs/blender-routing.md`加载`scenario-blender-expert`/`scenario-blender-previs-storyboard`。Blender MCP只读probe返回无法连接，已知无副作用；现有本地Blender5.2.1 LTS以`--background --factory-startup --python-exit-code 1`制作独立静态参考，未启动GUI/联网/下载/修改foreign场景。单元006保存可编辑`seating-layout-reference.blend`、Workbench俯视PNG `ab32d089f80d15db356632828362f71ae7ddbd82170304f732cc872b71cdeb6b`与`layout-receipt.json`：林砚/陈立同排相邻0.7m，其他五人在对面，苏遥门边。它只约束预定座位职责，不证明实际图片镜面、相机、完整倒影或接受；未生成animatic或第二Production执行链。

单元006最多2次，先1次空间修图，只有全项通过才允许条件领型修图。`codex-s01-spatial-repair-20261015-006/s01-adjacent-seat-candidate.png`为`e70dd60e382146a66ea72d5e4ef3e15e7c0dcf0725ecd6a6e2eb6719a5a6222e`，944×1666、2,146,016 bytes。陈立从对面移至近侧背面、对面剩五人，但他的腿鞋被窗框切掉，身体遮住周伯祥与苏遥下肢，原空座被占/遮，背面倒影持机袖口仍对应实际左臂。**FAIL/STOP**，条件第2次未调用，也不挪用为重抽。

单元007另封存1次，保留006停止及消费。原S01只要求物理林砚右脸/肩在下，不要求他的整个人/鞋入画；因此允许下半身出画、增加玻璃占比，保留28mm自然广角/坐姿眼高及全部原剧情。exact request `677bff52fef55bab774a2b842d430e37c930d120a4f2c21da894a12177476176`仍以005整图身份/手部及006座位图为不同职责参考，明确七完整他人、相邻空座、背面镜像实际右手、苏遥圆领，不把参考图当实际结果。

实际输出`codex-s01-composition-repair-20261015-007/s01-window-composition-candidate.png`：`7540565b88ecee230d41aeda1348461ef4854b191b8663c6ec34b0941bf6d26a`，941×1672、2,105,490 bytes。Parent与同一critic核验：林砚下半身出画、陈立黑鞋进玻璃，苏遥左手/林砚右手机空左手及挂绳工牌保留；但窗内为**8名他人**（两名海军蓝短发女性）、周伯祥/苏遥下肢仍被遮、具体相邻空座不可读、苏遥翻领仍错、陈立背面持机袖口仍不符合实际右臂。手机白色UI屏幕不证明深蓝机身换色，不添加无依据FAIL。`static-review.json`逐项绑定像素，`unit-stop-receipt.json`封存**完整首帧FAIL/STOP、1/1消费、零retry**。无accepted S01，不提交视频，不以人数可辨认替代完整倒影。

### State, Recovery And Learning Boundary

新增native调用4，累计9；Seedream/视频/音频Provider POST及Comfy推理本轮均0，Blender静态参考不计AI图片调用。内置底层model/价格/账单未暴露，不能把无外部API POST说成全部免费。原视频仍0、历史视频11，旧paid2/local2/web UNKNOWN保留。标准`load_production_project`重开Manifest33/Project7、`qa_policy=None`，entrypoint/Manifest/Registry hash与004 exact前序一致，见007`production-after-canonical.json`；未导入、激活、签QA、取状态或渲染。最初只读诊断误用root manifest路径失败，随后用canonical`state/manifest.json`核验，期间无写入。

实际能力缺口仍是把镜面人物、空间、道具和保护项同时落实到exact图片：native多参考可以传条件，却不提供硬mask/几何锁定保证，俯视图也未使本例整图通过。最小恢复条件是先得到可审阅的几何/分层参考及结果，实证七完整他人、可读相邻空座、正确镜像持机臂与圆领；当前有限单元停止，不能据未用slot或历史预算盲抽/越过Gate。原广播/对白、动作、字幕、raw逐镜声音、实际handoff、HyperFrames两镜7秒及human1.0x均未验，原前15秒S03/S04和完整故事AC-7未交付。

按`record-ai-video-session`更新本primary record及候选README；`distill-ai-video-learning=no_candidate`：这是一条递进且多变量改变的修图链，局部成功不能支持通用生图/镜面能力或workflow有效claim，不创建LearningClaim、修改Skill/Policy/Gate或写全局memory。只读视觉critic不是新增实验或Product QA authority。纯文档/媒体取证未改变代码或权限，implementation Risk Gate为`NATIVE_REVIEW_NOT_REQUIRED`；现有foreign staged/dirty均保留，exact文档Harness与publication另据实际Git/receipt核验，记录阶段不追加媒体/Provider调用。

## Original First Frame Static Admission And Canonical Import — 2026-10-16

用户明确要求“一直修图修到可以开始做为止”。本轮延续原首帧修复，没有删除倒影、左手动作、广播、字幕或原对白，也未重新生成旧抬手机B。使用`imagegen`的显式底图/身份/局部姿态职责；实际Blender镜面参考只负责难以用文字稳定表达的持机臂，原生只读critic仍是同一`/root/s01_static_geometry_audit`（`reviewer_high`），不以模型意见代Product验收。

### Actual Image Work And Source Corrections

证据仍在`runs/canvas-jieshi-original-s01-s02-20261013-001/`。008的Blender全景因前景遮挡、曝光和裁切失败，`reference-stop.json`保留NOT_READY，未送作合格全景参考，原生图片调用0。009实际6/6：局部绿圆领→整图、删除重复许雯并露出老人躯干/膝手、局部相邻空蓝座→整图；最后陈立持机裁切虽删除错误手机却未补正确手机，FAIL且不转移。010实际4/4：照片主输入的手臂修正仍FAIL；改用真实Blender单人镜面手臂作为主输入、人物身份照只作身份，局部输出才出现正确的镜中背面画面左侧屈肘持机；再转移整图，最后局部修正原服装/删除多余挎包和眼镜。失败的008全景不能被该局部姿态成功反向宣称为镜头标定成功。

011实际3/3：服装整图转移后，原文复核发现Agent此前额外写了空白工牌。S08明确“林砚／产品部”，S37才让头像、姓名消失且部门保留，因此先局部补回同人小头像、林砚、产品部，再只转移回原尺寸/位置的整图工牌。没有加新组织、特写或剧情。此前“所有普通乘客都必须同坐对面一排”“每双鞋完全不重叠”“林砚本人全身入镜”也不是原文硬要求，现明确撤回这些Agent附加标准；原七名他人的完整倒影/身份、正常身体范围、陈立邻座、固定空间与原摄影不撤回。不是保留七颗头就算完整倒影，也不抹去旧FAIL。

最终原始输出exact copy为`codex-s01-final-original-detail-repair-20261015-011/03-s01-original-firstframe-candidate.png`，SHA `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`，RGB PNG、941×1672、2,113,859 bytes。没有resize、crop、重编码或手工粘贴成片。`03-full-badge-transfer-request.exact.json` SHA `dca9ef37a3f22b43e19ccb28dfb707717cf9fa49190795dace34998b714796aa`；`03-generation-record.json`记录本次成功与内置累计22。旧9次+新增13次均保留，新增13次为同一渐进修复链，不算13个独立重复实验；没有UNKNOWN重试或自动换Provider。

### Exact Static Findings

Parent实际查看最终整图，并与同一critic的新像素发现、原Character Bible/S01/S08/S37逐项核对；`03-static-parent-adjudication.json`封存九项静态PASS：七名他人各一次且身份/身体范围可建立；近侧对应空蓝座邻接陈立且无林砚人/手倒影；实际林砚右黑手机/空左手；苏遥左白手机/绿圆领；陈立镜中背面画面左灰袖→弯肘→腕→深蓝手机对应实际右臂、另一手空/黑耳机/无新眼镜；原服装道具；正常工牌头像/姓名/部门；原本人在下、玻璃在上的斜侧自然广角取景；无片头、字幕、额外标题。正常局部下肢交叠保留，没有新整段身体缺失。旧S01-STILL-08空白工牌触发条件在新bytes消失，裁决OBSOLETE_AFTER_CHANGE，旧图仍FAIL。

结论仅为**PASS_FOR_FIRST_FRAME_AUTHORING**。静态图尚未发生抬左手→距窗约2cm悬停，不证明三秒动作完成、玻璃全程无手、锁机位、点名广播/嘴不动、对白窗口或S02的右pan和求证表演。精确保护区零像素变化也未声称。用户完整1.0x听看仍NOT_EVALUATED。

### Existing Entry And Canonical State

当前普通数据及共享inspect/author/preflight证据在`original-firstframe-ready-20261015-001/`，入口`project.json`，素材`S01-firstframe.png`与`S01-generation-source.json`均在允许data root内。模型/采样参数NOT_EXPOSED；原始生成记录和exact copy证据沿既有`generated_source`进入，Registry source_kind为derived、tool为`canvas-generated-image-source/1`，没有冒充Seedream/Qwen、人类导入或合格Provider产物。旧docs入口保留bootstrap历史；重开当前项目使用新的普通data入口，不新建故事执行脚本、第二timeline/state bank或renderer。

两镜source只追加原S08/S37已有的工牌正常态，原动作、对白、时窗、声音和摄影文字均保留。Scene opening参考与S01 approved_keyframe明确绑定新图；S02仍为待实际accepted S01的占位，不把首帧当作未来悬窗状态。新的source snapshot不能借用旧imported placeholder的copy identity；首个author在写前拒绝，known-no-effect，随后以新的普通placeholder选择保留旧record。没有放宽source guard。

`CanvasProductionService.author`先审阅merged Registry及全序列preflight，再经`revise_authoring`唯一committer写入：Manifest33→35/Project7→8。Parent首个postcommit断言错误要求所有attempt总数不变；实际canonical revision正确追加一个succeeded metadata attempt。已standard-loader核对原9条attempt前缀及全部旧10条Registry记录完全保留，没有重试该已成功commit。随后将Agent描述式license规范为已有`project-owned-synthetic`枚举，经一次显式metadata revision到Manifest37/Project9，旧不可变snapshot与P7前缀保持；不把此标签当作人类声明或Provider准入。证据为`canonical-revision-reopen.json`、`license-normalization-reopen.json`。

fresh共享CLI `preflight-final.json`实际重开当前immutable authoring，generation_order及composition_order均S01→S02。S01图SHA/尺寸/来源/职责正确，两镜authored text均包含原工牌正常态，S02绑定状态仍PENDING_ACCEPTED_SOURCE。当前position为S01/prepare，无原视频attempt；qa_policy=None，selected QA/当前qualified视频runtime、图像Provider admission及新原镜声音证据仍须补齐。已有2次原Fast4s480p/native视频授权未消费，但不是fresh profile/permit，不把旧B或历史Vidu修复permit挪用。

### Evidence And Learning Boundary

原paid准备图2、local模型图2、历史视频11、原视频0保留；内置图片累计22单列，底层调用费用NOT_EXPOSED，不宣称免费/账单。Gemini对历史WAV的实际观察仍有效，但development-only一次permit已消费，不代新原镜声音或selected QA。当前图片首帧静态成功、原两镜7秒、完整前15秒、故事AC-7与human验收继续分开。

使用`record-ai-video-session`更新本primary record及README，`distill-ai-video-learning`评估**no_candidate**：这是一条多变量、依赖前产物的渐进修复链，局部姿态参考改变和后续整图转移没有隔离为受控比较，不能推出通用模型胜率、镜面能力或自动采用新的Skill/Gate规则。社区/官方image prompt角色分工只作advisory，失败全景及失败持机尝试作为反证保留。无Skill/Policy/Gate、global memory或RAG重建；记录本身不触发额外媒体/Provider/网络调用。无源码实现，implementation Risk Gate不触发；同一视觉critic的像素核对不冒充工程review或human。foreign staged/dirty保持，publication与exact Harness另按实际receipt/Git核验。

## Original S01 Exact Submit And Input Admission Stop — 2026-10-16

图片checkpoint已发布`0f12d3e4146b474070ce57c41e99757b34f45214`并核对远端main；对应`.agent/harness/runs/jieshi-original-firstframe-ready-20261016-r1/receipt.json`五项checks PASS、fresh/complete。没有在该commit停下。用户随后要求确认作图是否沉淀为Agent能力，Parent把本轮已实际使用的局部放大→整图转移、姿态主参考/身份辅参考、原文与附加限制分离、最终整图复核和实际consumer绑定写入既有`docs/canvas-production-harness.md#bounded-repair-practices`。现有AGENTS/playbook入口已指向该owner，不新增Skill、故事脚本、Provider、第二timeline或状态库。使用边界是本次渐进链中的有界经验，不声称通用成功率或硬节点执行。

### Raw QA And Actual Shared Preparation

原生只读`code_mapper` `/root/original_video_runtime_readiness`确认此处缺的是caller配置，而非不存在的API：正常`activate_qa_policy`可选真实raw rubric；没有production_lineage的S01/S02逐镜切换全局policy即可，`accepted_sequence_source`重验来源随附的QA snapshot，不把新policy自动当旧片失效。Parent重开相关函数裁决，未启动组件物化旁路或借fixture helper签QA。实际建立S01 15项raw required IDs、S02 17项候选required IDs（含七维actual state）、同一36项final-output要求；只经唯一committer选中S01 policy。S02候选尚未激活、没有findings，final contract中的全部原要求及human whole-playback保留。

第一次实际Planner prepare发现`Shot.required_asset_roles.first_frame`仍指旧local布局，而generation/source refs已指新图，得到missing_references及派生human_review_unresolved。没有为此再问用户或放宽human Gate，而是经canonical authoring仅对齐实际首帧槽，Registry及QA保持不变；Project9→10/Manifest38→40。随后按原schema owner升级2.6→2.15，以启用video/source-boundary/caption能力；旧未开始的start被schema guard拒绝为known-no-effect。真实再prepare得到GENERATE_ONCE、CompiledProviderVideoRequest、无unsupported paths，并经正常start建立唯一S01 REQUEST。物化remote stack引用本次profile/compiler/output identity，S01 seal-terminal与后续actual frame71/source-video路线保留，未冒充本地weights或P0 Production资格。

用户对当前exact图片回复“A：确认原创虚构、无受保护身份，允许用这张图生成 S01”，仅把该真实声明绑定既有synthetic receipt，不代签human媒体验收。沿已有原2次Fast视频授权执行首镜1次；本次不新增视频额度，不转用旧B/Vidu修复permit。新profile窗口16:16:22.910395–17:16:22.910395 UTC（2026-10-15），model=`doubao-seedance-2-0-fast-260128`，4秒nominal请求/480p496×864/24fps/native audio，canonical采用前三秒；不是旧15秒nominal测试。50 CNY/call与200 CNY既有总bound仅为sealed内部上限，不查价/账单。

### Exact Request And Actual Rejection

真实证据根`original-S01-live-20261016-001/`。Attempt=`canvas-32dd80cf21a3147888977db32b3dc86c57e1297b`；resolved request SHA `32196e44f2d2d217fcb03cb5d54c59066a42a585bf576f7c020a3d9918fd1525`，Paid preview `16edce15f53803d9f7ed7d96179767419b0106b77ef7c3ee6c68a4f18756967e`。Exact native prompt SHA `2a54252ee51ac0d9c1a193ff0b3060aa80ae94ab3570986c588b49b162f50f59`与已审S01 authored text完全相同，保留原全部source parts，只添加原工牌正常态；没有删广播、手部、倒影、摄影或字幕composition职责。Wire body SHA `21f67a1c46bba1f7e7fecf60c8bbe18e355f752808f00f66f8300e358d3e490e`，只有text与一个first_frame，inline PNG回解SHA仍`13c83ce4…76923`。`native-body.exact.json`/`native-prompt.exact.txt`、profile/stack/limits、synthetic来源/egress、授权和preflight分别保留，不保存key/header或raw signed-response。

Exact injected supplier在本窗口实际查Secret Service `application=ai-video/provider=seedance/credential=ARK_API_KEY`；标准同UID bus核验，禁止.env/ambient/fallback，无value/hash回显。Current adapter/profile/window、原文/refs、实际MCP音频factory/source、预算reservation、egress、durable intent与one-use permit均核验，真实transport仅允许exact body的一次POST。Server返回HTTP400 `InputImageSensitiveContentDetected.PrivacyInformation`，没有task ID/MP4；未poll/fetch/重试，S02零提交。`submit-wire-observation.json`保存实际body identity/status/response hash，不拿离线payload重建冒充wire观察。

Canonical paid submit receipt=`state/paid-provider/submits/6a58fabd1108dfcb3b7556359e14deb167641747bc37b2b9d112f3a18d54ac42.json`，file SHA `8bcdf793b9209bf20e68ad9dde466ed3bd00e75b9623d42f9a46e6a24f50ddc2`，paid phase known_no_effect，attempt failed。再沿正常`record_attempt_evaluation`记录runtime_failure，无媒体findings；当前Manifest45/Project10/schema2.15，position=STOP。原视频POST1+历史11=累计12，原S02次数不挪给新S01重抽；没有“拒绝就把POST计数归零”。实际成本/账单未查，不声称免费。旧web UNKNOWN不受本次known_no_effect影响。

### Provider Boundary And Minimum Recovery

当前首帧静态PASS保持；失败发生在输入审核，不能把它重分类为倒影/手部/服装质量失败或继续盲修照片。Parent在当前窗口重开[方舟官方肖像指南](https://docs.volcengine.com/docs/ark/seedance-portrait-asset-guide?lang=zh)：受信模型产物路线要求同账号、30天内、指定模型原始产物，明确不含跨平台产物或二次编辑；这张Codex图不能因Registry来源声明而变成该路径的原产物。社区[ArcReel #2249](https://github.com/ArcReel/ArcReel/issues/2249)也有AI人物图片同错误的报告，但其issue建议不是本账号的已验证修复。当前请求400是本图的实际反例，不推导所有跨平台AI图永久拒绝，不采纳遮脸/叠图案等规避审核建议。

最小恢复条件是取得当前图可用的合法Provider素材准入证明，或用户明确授权一个支持保留此图/原生声音的其他视频输入单元；随后仍走原shared preparation/paid/逐镜Gate。此前用户拒绝购买/开通私域库仍有效，不自动入库、购买、换Provider，亦不把旧剩余次数当新路线许可。旧Seedream技术图均FAIL，不能换回去求平台通过。没有可用MP4，所以project-local逐镜视频QA、新音义/时序、frame71提取/后镜绑定、S02、字幕/trim/HyperFrames和human1.0x均NOT_EVALUATED；没有为补证多生视频或调用Gemini空转。

按`record-ai-video-session`在真实blocker更新同一主record/README，并将用户要求的可复用步骤补入既有workflow。`distill-ai-video-learning=no_candidate`：本链不构成隔离变量的重复效果结论；工作流更新来自用户明确指令，非自动采用Learning Claim。后续Agent可沿已有入口发现实际方法和Provider限制；文档不假装新自动图引擎。没有源码行为/Gate修订，implementation Risk Gate不触发；Parent保留最终判断。当前文档publication与exact Harness按新receipt核验，foreign staged/dirty保留。

## Community Admission Research And No-New-Paid-Route Constraint — 2026-10-16

用户追问“这是我AI生成的图片，社区都是怎么做的”，并要求沉淀给后续Agent，随后明确不找付费途径。
本轮仅重开实际`actual-rejection-audit.json`、`submit-stop.json`和`final-stop-state.json`，并检索公开官方资料与社区原始报告；没有新图片、视频、音频POST、重试或Production mutation。当前exact图仍`13c83ce4…76923`，S01原视频POST1、历史11、累计12，S02 POST0，无MP4。`PrivacyInformation`本身不证明图片来自真人，也没有定位具体脸部、工牌或像素；写实人像输入准入是结合官方规则及同类报告的解释，不伪称逆向确定了分类器。

Parent使用`research`与`retrieve-ai-video-memory`，后者不作为current事实来源；委派检索报告缺`langchain_core`，未重建、下载模型或启用网络fallback，当前结论以重开的exact本机证据与公开primary source为准。按`SUBAGENTS.md`选择一个原生`universal_executor` `/root/seedance_portrait_evidence`核验官方准入与免费条件、仅更新既有肖像研究文件；Parent持有workflow与本记录，target paths不相交，无external agent、nested delegation或第二reviewer。现有AGENTS/playbook已指向共享workflow，foreign同文件暂存不修改。

研究复用并更新[原肖像准入审计](../research/2026-10-13-seedance-ai-portrait-input-admission.md)，区分官方受信原产物条件、社区reporter同错误、作者自报实测与AI triage建议。只看到他人成片、其他账号或中转平台成功，不证明当前图/role可用；对裁切/转码是否保留信任的社区结论，遇到官方警示和缺少本账号实测时保持不确定。Parent重新核对官方Create Video API，`image_url.url`可传`asset://`且图片role有`first_frame`，属于语法支持；多人整张首帧审核放行不能从单人`reference_image`例子推导。

当前允许的恢复调查不新增付费：整理不含凭据的官方支持核验材料，或核对官方明确且当前账号已可用的免费准入。没有代用户发工单/上传图片/开通权益，未把免费quota说成已有权限；重生Seedream原图不能冒充保留当前图。仅重开现有local H3 profile确认其为loopback、1344×768、124帧/24fps、原生音轨配置；未运行模型/核验当前weights及nodes，也未验证原S01倒影、手部、广播和竖幅要求，所以不是已就绪的免费替代路线，更没有自动下载模型或切换。

按用户明确指令将可复用诊断步骤写入`docs/canvas-production-harness.md#portrait-input-admission`：先绑定被拒exact输入和失败阶段，再核对整条准入路线、费用限制、原图/原文保留及恢复条件。此为advisory执行指导，不改Provider/QA/付费Gate，不声称已打通免费出片。`record-ai-video-session`复用本主记录，不新增重复记录或媒体证据行；自动`distill-ai-video-learning=no_candidate`，本轮没有新增独立受控attempt来证明免费修复有效，社区研究不当本地实验验收。

文档变更按exact owned commit range验证并push；最终receipt见`.agent/harness/runs/seedance-portrait-community-free-route-20261016-r1/receipt.json`，实际结果以完成后的receipt为准。没有源码行为或高风险执行变更，implementation Risk Gate为`NATIVE_REVIEW_NOT_REQUIRED`；没有用户对implementation独立review要求、重大durable-state/credential失败路径或剩余重大语义验证缺口，Parent负责核对来源与最终diff。媒体目标仍因输入准入阻断，非文档完成即Production完成。

## Free Entry Recovery Candidate And Enterprise Eligibility — 2026-10-16

用户指出云端METASO后又明确“先停止，我就是要用seedance”，随后“继续”；因此仅继续Seedance正规准入调查，不把key/path presence作为换Provider或调用授权。没有读取所指`.env`、查新credential、启动本地H3、生成媒体或购买服务。

本轮Parent经公开HTML table与web原文交叉核对官方免费Entry确有AIGC入库权限，细节归[原研究的最新纠正](../research/2026-10-13-seedance-ai-portrait-input-admission.md#latest-correction--free-entry-and-account-eligibility--2026-10-16)。旧10月13日账号记录已知道免费Entry，本次不是新功能或新成功实验。前次研究只强调尚未证实当前免费准入，未具体核对Entry，容易被理解成必须付费；现研究/共享workflow已纠正，不能把高级权益名称当付费必要性。

正规候选仍须满足该资格及开通条件。重开`runs/canvas-jieshi-two-shot-20261013-001/asset-entitlement-check-20261013.json`，其2026-10-12T20:21:11.115298+00:00观察为`aigc_writable=false/aigc_readable=true`、Entry未开通、按钮因仅限企业账号disabled；旧实测保持历史，未冒充本窗口账号状态。Chrome MCP `new_page`被既有profile占用拒绝，未杀浏览器、换profile或读cookie；公开文档改用公开SSR原文读取，没有登录账号查询。当前企业/Entry状态`NOT_EVALUATED`，已向用户提出这个必要信息问题；不能代签身份/风险/协议，也不把旧拒绝开通解释为已批准新开通。

标准`load_production_project`重开Manifest45/Project10，当前canonical PNG实测SHA仍`13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`、2,113,859 bytes；共享`inspect`仅生成advisory报告。恢复candidate只描述同图→免费Entry AIGC审核→真实Active→既有asset resolver，尚无asset ID/人类Active receipt或新video request。CodeGraph关系与当前源码/tests核对`SeedanceAssetMaterializationReceipt`要求human、exact source与confirmation SHA，`SeedanceAssetReferenceResolver`绑定同一first_frame回传`asset://`；不新增执行链或伪造receipt。第一次本地证据整理误读Manifest字段`revision`，在任何Provider/Production写入前失败；按源码改用`manifest_revision`后成功，不涉及submit重试。

证据目录为`runs/canvas-jieshi-original-s01-s02-20261013-001/seedance-free-entry-20261016-001/`：`official-free-entry-observation.json`、`recovery-candidate.json`、`shared-inspect.json`。免费权益资格不证明这张多人/倒影图会入库，不证明新视频免费或已获新S01次数；原视频POST1/历史11/累计12、S02 POST0、web UNKNOWN、完整故事/声音与逐镜Gate保持。

原生`universal_executor` `/root/seedance_portrait_evidence`本轮仅只读社区原帖、无文件写入；Parent独立重开原帖裁决：Dreamina/CapCut动画式多格Omni Reference成功自报不等于本Ark写实first_frame；另一第三方Seedance2.5参考自报5次1成功不构成稳定解法。没有证据表明创作者都付费订阅人像库，也不把其生成费用当素材库费用。不采用遮脸/网格/改角色、第三方收费中转或模型fallback。

按`record-ai-video-session`更新同一主记录及原研究的prominent correction；`distill-ai-video-learning=no_candidate`，只有官方/历史资格重新核对，没有新的独立媒体尝试或免费入库成功。仅文档和advisory证据，未改产品行为/安全Gate；Parent在相关verification后按Risk Gate判断`NATIVE_REVIEW_NOT_REQUIRED`。本checkpoint exact commit range的receipt为`.agent/harness/runs/seedance-free-entry-recovery-20261016-r1/receipt.json`，不以工程PASS代当前账户、人像审核或视频交付。

## Personal Account Reply And Remaining Seedance Routes — 2026-10-16

用户对`call_0dc7efb1bb514f9a947a7ea9899ca058`的账号问题回复“仍是个人账号”。据此前已核对的官方企业条件，免费Entry不是本账号当前可直接使用的AIGC路线；不是所有Seedance能力都不可用，也不是需要购买高价人物包。未把这条用户声明写成新authenticated console观察；当前live quota仍未查询。

在`seedance-free-entry-20261016-001/`追加`user-personal-account-confirmation.json`、`recovery-candidate-after-user-reply.json`，保留原候选及历史quota，状态仅为advisory `BLOCKED_ENTERPRISE_IDENTITY_REQUIRED`。原Manifest45/Project10、exact图、原S01 POST1/历史11/累计12、S02 POST0均未变。

继续只读核对Dreamina官方静帧→Seedance制作说明及方舟受信产物条件，区分能力宣传、普通个人网页、当前Ark API与本图准入；没有用“Try free”证明本账号额度或审核通过。用户需要选择保留现图先核对即梦个人网页、保持API另准备合格Seedream原始首帧方案，或现图/API不变仅向官方核实。新制作图会改变identity且生成调用需另封存；网页不是已绑定的当前Ark执行请求，不自动换面。已提出一次路线偏好问题，等待外部决定，不擅自把未回复当许可；没有读key、上传、换Provider或重发。

按`record-ai-video-session`追加同一record，`distill-ai-video-learning=no_candidate`；只是账号信息与恢复范围明确，没有免费准入/新媒体成功。文档验证及exact范围receipt为`.agent/harness/runs/seedance-personal-account-recovery-20261016-r1/receipt.json`；源码/Gate不变，Risk Gate不要求独立review，Parent负责最终核对。foreign dirty/index保留。

## Jimeng Personal Web Readiness And Login Boundary — 2026-10-16

用户对`call_86d8f829988c48948e7fa2d11781c14c`回复“保留当前图，先核对即梦个人网页的正常上传、审核和已有额度”；问题已明确本选择不触发生成或付费。因此只检查普通个人网页，不把该回复当新S01 submit、会员购买、充值或新Provider许可。

共享Chrome MCP profile仍被既有浏览器以debugging pipe占用，没有可复用的HTTP debugging endpoint。保留原进程/profile、其他业务浏览器及登录状态，不删除锁或复制cookie；以当前已安装`chrome-devtools-mcp` 1.11.0的`--isolated --no-usage-statistics`启动本任务独立有界浏览器，通过标准MCP SDK调用同一browser工具。没有安装包、修改MCP配置或新增故事执行器。最初直接运行包`index.js`不是CLI入口，连接关闭且未开启页面；核对已安装package的`bin`后使用`build/src/bin/chrome-devtools-mcp.js`成功打开官方网页。这是本地工具入口纠正，不是生成重试。

实际访问`https://jimeng.jianying.com/ai-tool/generate/?type=video`后进入`/ai-tool/home`，页面显示未登录。通过普通UI切到`视频生成`，默认为`即梦 Seedance 2.0 mini`；模型列表存在`即梦 Seedance 2.0 Fast VIP`，说明为“极速推理，会员专属通道，音视文图均可参考（暂不支持真人人脸）”。只在网页预览选择Fast VIP，未改canonical项目、模型或sealed request；公开选项不证明本账号已有会员，也不证明与Ark `doubao-seedance-2-0-fast-260128`完全等价。

参考职责菜单实际列出`全能参考 / 首尾帧 / 智能多帧 / 智能编辑 / 超长视频`。选择`首尾帧`后有`首帧 / 尾帧`位置；点击`首帧`上传入口，页面提示“请先登录”并弹出“欢迎登录即梦”。未选择文件，没有上传请求、图片审核或生成。广告/注册赠送文字不作为当前账号额度；实际会员、已有积分/免费次数与这张图的审核均`NOT_EVALUATED`。已请求用户在打开的官方窗口自行登录，未索取/读取密码、OTP、扫码内容或代勾协议；窗口保留供登录。

已复核canonical PNG仍为2,113,859 bytes，SHA `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`。脱敏浏览器观察保存于`runs/canvas-jieshi-original-s01-s02-20261013-001/jimeng-web-readiness-20261016-001/observation.json`；只记录公开控件、未登录状态与零副作用，不保存cookie、登录二维码、私有账号内容或MCP session。原S01 POST1/历史11/累计12、S02 POST0保持；仍无原S01 MP4，静态首帧PASS不代准入、逐镜QA或human acceptance。

最小恢复条件是用户完成正常登录，随后只核对真实会员/额度并将相同PNG按首帧职责正常上传；不得把UI缩略图或上传成功代签生成审核，不通过生成按钮探测审核，不购买、不充值、不自动改用mini/2.5/Omni Reference。若真实审核只发生在submit时，应保留`NOT_EVALUATED`并报告这个边界。

按`record-ai-video-session`更新同一主记录，并用`distill-ai-video-learning`评估为`no_candidate`：这只是一次网页准入/登录观察，没有新的免费入库或媒体成功，不能升级成通用解法。无产品实现或Gate变更，implementation Risk Gate不触发独立review；Parent负责final diff和证据裁决。文档exact范围receipt为`.agent/harness/runs/jimeng-personal-web-readiness-20261016-r1/receipt.json`，实际结果以完成后的receipt为准；foreign dirty/index保留。

## Authenticated Jimeng Credits, Exact Frame Selection And VIP Boundary — 2026-10-16

用户回复“登陆了”后，沿同一个本任务Chrome MCP独立浏览器会话核对：登录提示/按钮已消失，Fast VIP与首尾帧设置保留。正常`积分详情`显示总40、订阅积分0、充值积分0、赠送积分40，本次可见“每日免费积分 / 2026-10-16 02:04 / +40”。不保存账号标识、过去积分明细、二维码、cookie、headers或完整页面诊断；这是即梦网页当前额度，不推定为Ark API额度或Fast资格。

第一次`upload_file`在选文件前因SDK客户端未声明项目workspace root而拒绝访问。重新核对当前已安装MCP：默认显式允许OS temp；将已授权的同一PNG按bytes准备到0700目录/0600文件，SHA、size不变，没有修改root规则或MCP配置。随后自动选择文件返回`DOM.resolveNode`缺nodeId/backendNodeId与file chooser注入失败；检查两处首尾帧槽均空，未以工具错误冒充Provider审核。参考[Puppeteer上游文件选择问题](https://github.com/puppeteer/puppeteer/issues/7941)及[另一个MCP实现的同类报告](https://github.com/browseros-ai/BrowserOS/issues/2156)，只确认其与无持久input的现代选择框问题相符，不声称已定位即梦内部实现或安装第三方补丁。

在同一登录会话新标签页重开正常首尾帧入口，不复制登录或改网页上传逻辑。通过现有`xdotool`核对本任务Chrome PID及`WM_TRANSIENT_FOR`，只操作其标题为`Select a file this site can read`的原生文件对话框；先填入已核验路径，再以可见`Open`动作确认同一个文件。窗口激活等待曾因modal已在前台而超时；没有停止浏览器，按实际modal归属继续。诊断截图在本地查看后已删除，不进入记录。没有图片/视频生成调用，也未修改页面上传逻辑或安装工具。

等待页面处理后，首帧槽出现941×1672预览，尾帧仍空，输入提示变为“结合图片”，比例为自动匹配。对页面所用local blob实际读取/计算：PNG 2,113,859 bytes，SHA `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`，与canonical原图完全一致。该检查只绑定浏览器预览；upload相关resource timing虽出现4条200和2条未暴露status，仍未绑定服务端exact素材/审核receipt，不能代签素材Active或视频准入。没有可见审核拒绝也不等于审核PASS，当前`moderation_result=NOT_EVALUATED`。

网页预览仅保留`即梦 Seedance 2.0 Fast VIP / 首尾帧 / 首帧`；正常时长滑块从5减至4，按钮实际显示4s。分辨率菜单只列720P、数量保持1，与原sealed Ark 480p请求不同；未自动换mini/2.5/全能参考。没有观察到可独立核验原生音频的UI开关，也没有声音产物。生成按钮的submit-button parent出现`lv-tooltip-open`，悬停提示为“此功能为VIP专属”。此为本账号/当前入口的具体资格阻断；40免费积分不解除这项UI限制，不解释为所有Seedance或所有AI图都必须购买人物库。

本轮未填原S01生成prompt、未封存网页新请求/permit、未点击生成、购买或充值，选择后余额仍40。原S01 POST1/历史11/累计12、S02 POST0及canonical项目不变，没有新视频/音频，human acceptance保持`NOT_EVALUATED`。脱敏观察追加到`runs/canvas-jieshi-original-s01-s02-20261013-001/jimeng-web-readiness-20261016-001/authenticated-observation.json`，保留前一份未登录观察。当前结论为`BLOCKED_CURRENT_WEB_FAST_VIP_ENTITLEMENT`，不是原图静态FAIL或新Provider输入拒绝。

按用户不新增付费且只核验路线的范围停在这里。恢复需本入口确有合法可用资格，或另有明确的新Seedance型号/入口候选及相应授权；后者必须重新核对能力、原剧情、exact输入、有限计数/预算及canonical接入，不直接用当前网页720P草稿、已有40积分或旧S02次数提交S01。先前API拒绝及声音/逐镜验收要求均保留。

按`record-ai-video-session`更新同一主记录与研究的current-facing状态；`distill-ai-video-learning=no_candidate`，这是一条网页输入/权益观察，没有独立媒体或免费生成成功，不升级通用规则。无Product实现/Gate变更，Risk Gate不触发独立implementation review；Parent核对最终diff和当前UI证据。文档exact范围receipt为`.agent/harness/runs/jimeng-authenticated-input-readiness-20261016-r1/receipt.json`，实际结果以完成后的receipt为准；foreign staged/dirty保持。

## Free Seedance Alternatives And Account-Specific Readiness — 2026-10-16

用户对“继续找能免费生成原S01的Seedance入口，保留当前图”选择A。本轮只做该范围的实际UI核验与官方来源研究，没有将选择A扩为新生成/付费授权。Mini与2.5仅在网页预览切换，canonical项目/Provider请求、原S01及S02计数、完整剧情和逐镜QA要求未更改。

| Candidate | Current Evidence | Boundary |
| --- | --- | --- |
| 即梦Seedance 2.0 mini | 登录账号实际选择后，原首帧保留、4s/720P可见，提示“升级以使用「即梦 Seedance 2.0 mini」” | 名称不带VIP不证明免费；没有点击生成 |
| 即梦Seedance 2.5样片 | 原首帧保留，实际提示“升级以使用「即梦 Seedance 2.5 (样片模式)」” | 菜单宣传480P样片不解除账号资格，也不证明该网页模式原生声音或审核通过 |
| 即梦Seedance 2.5 | 实际提示“升级以使用「即梦 Seedance 2.5 」” | 未当作原Fast请求的等价替换 |
| 即梦新用户Mini限免 | [官方公开页面](https://jimeng.jianying.com/ai-tool/generate?ai_feature_name=omniReference&enter_from=ai_feature&from_page=explore)写明完成任务可得3次Mini限免；当前账号积分商城显示免费版/40积分，未找到可证明已到账的该项次数 | 新用户/任务条件及本账号剩余次数均未核验；未执行任务、兑换、邀请、发布或消费 |
| 豆包App | [字节Seed官方发布页](https://seed.bytedance.com/zh/blog/seedance-2-0-%E6%AD%A3%E5%BC%8F%E5%8F%91%E5%B8%83)明确列App对话框→Seedance2.0→2.0模型 | 官方入口存在不证明当前账号免费次数、图生视频准入、4s与原生声画契约 |
| 豆包网页 | 正常打开`https://www.doubao.com/chat/`，未登录，能看到图像生成，未看到视频/Seedance入口 | 没有上传本图或发生成消息；不能用App文档代签网页能力 |

当前源码`seedance_capabilities.py`与官方[2.0系列教程](https://docs.volcengine.com/docs/ark/seedance-2-0?lang=zh&sessionid=)确认API Mini具备首帧、有声视频、4–15秒、480p/720p能力；这不绑定即梦网页的exact后台模型或赋予免费使用资格。当前Registry为Mini声明`nominal_seconds`，不能冒充原Fast的`exact_seconds`契约；新候选仍须核对实际时长和canonical采用范围。当前Registry的1.0模型`native_audio_options=(False,)`，因此没有将未证明原生广播/对白能力的旧1.0当本次免费替代，也不删原文声音要求。第三方自称“官方”或SEO文章声称的每日免费次数没有作为账号证据。

检查结束已恢复原FastVIP网页草稿：4s、720P、数量1、首尾帧中的原首帧；local blob与canonical PNG再次实际计算相同SHA `13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`、2,113,859 bytes，余额仍40。新图片/视频/声音生成0，新上传0，充值/购买/建账号/Production mutation均0。脱敏观察为`runs/canvas-jieshi-original-s01-s02-20261013-001/jimeng-web-readiness-20261016-001/free-entry-followup.json`，前述观察不覆盖。

已向用户异步询问其已有豆包App中Seedance2.0是否有免费次数并支持图片、要求开通，或没有入口/未安装；只请其查看，不生成/付费，不索取凭据或截图。当前`NO_QUALIFIED_FREE_ROUTE_YET`，这不是所有Seedance均不免费的结论。最小恢复条件是取得具体可用免费入口/剩余次数/输入与声音能力，随后封存exact原S01候选和新有限调用单元；不得以广告额度、当前40积分、网页登录或旧S02预算代替授权与Provider Gate。

按`record-ai-video-session`记录同一目标的有界恢复检查；`distill-ai-video-learning=no_candidate`，同一账号的多种预览不是独立媒体实验，没有成功准入/成片可供泛化。无实现/Gate变更，不触发独立implementation review。文档exact范围receipt为`.agent/harness/runs/seedance-free-web-alternatives-20261016-r1/receipt.json`，实际结果以完成后的receipt为准；保留foreign staged/dirty与旧失败历史。

## Evidence Index

此表只为本次原开场准备单元建立identity；历史其他实验不并入。remote boundary为Seedream/`doubao-seedream-5-0-pro-260628`、Ark shared image owner、1152×2048 PNG；新增local boundary为Qwen-Image-Edit-2511/三引用masked profile、944×1672 PNG，不与remote合同或计数合并。同一图片的receipt、bytes、materialization和visual proof使用同一request fingerprint independence_key，只贡献一个图片样本；预transport失败不是第二个视觉样本。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| credential-before-post | native-image:463e47e5d7b07c89d5db8f82db5d06f06867b08d7eac9d2066acb860adf74ac3 | jieshi-original-preparation-20261014 | original-preparation-base-20261014-candidate | N/A | NO_ARTIFACT:PRE_TRANSPORT_CREDENTIAL_FAILURE | PROVIDER_RECEIPT | KNOWN_NO_EFFECT | CREDENTIAL_READINESS | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/authorized-unit-20261014-001/base-known-no-effect-current.json |
| base-submit | native-image:4225a10af7b88649f33bbfa08f8df705363780f78b07abae1847dcd230845801 | jieshi-original-preparation-20261014 | original-preparation-base-20261014-qualified-001 | N/A | 14ce8688fd567c1d2ff7518a1de112cd505e5dec395bf22299219a00fed3ec73 | PROVIDER_RECEIPT | ACCEPTED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/production/state/paid-provider/submits/aa2c38927dace8d98eddd50dc005e9748a56b70764b9ca755827caf369ff1469.json |
| base-bytes | native-image:4225a10af7b88649f33bbfa08f8df705363780f78b07abae1847dcd230845801 | jieshi-original-preparation-20261014 | original-preparation-base-20261014-qualified-001 | N/A | 14ce8688fd567c1d2ff7518a1de112cd505e5dec395bf22299219a00fed3ec73 | TECHNICAL_BYTES | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | base-submit | runs/canvas-jieshi-original-s01-s02-20261013-001/authorized-unit-20261014-001/runtime-repair-001/materialization-diagnosis.json |
| base-materialization | native-image:4225a10af7b88649f33bbfa08f8df705363780f78b07abae1847dcd230845801 | jieshi-original-preparation-20261014 | original-preparation-base-20261014-qualified-001 | N/A | 14ce8688fd567c1d2ff7518a1de112cd505e5dec395bf22299219a00fed3ec73 | LOCAL_MATERIALIZATION | OUTCOME_UNKNOWN | CANDIDATE_VALIDATION | SAME_EVIDENCE_NEW_PROOF_LAYER | base-submit | runs/canvas-jieshi-original-s01-s02-20261013-001/authorized-unit-20261014-001/runtime-repair-001/current-state-reconciled.json |
| base-visual | native-image:4225a10af7b88649f33bbfa08f8df705363780f78b07abae1847dcd230845801 | jieshi-original-preparation-20261014 | original-preparation-base-20261014-qualified-001 | N/A | 14ce8688fd567c1d2ff7518a1de112cd505e5dec395bf22299219a00fed3ec73 | VISUAL_INSPECTION | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | base-submit | runs/canvas-jieshi-original-s01-s02-20261013-001/authorized-unit-20261014-001/base-image-review.json |
| base-closure | native-image:4225a10af7b88649f33bbfa08f8df705363780f78b07abae1847dcd230845801 | jieshi-original-preparation-20261014 | original-preparation-base-20261014-qualified-001 | N/A | 14ce8688fd567c1d2ff7518a1de112cd505e5dec395bf22299219a00fed3ec73 | LOCAL_MATERIALIZATION | FAILED | CANDIDATE_VALIDATION | CONCLUSION_SUPERSEDED | base-materialization | runs/canvas-jieshi-original-s01-s02-20261013-001/image-repair-20261014/closure-execution.json |
| repair-base-submit | native-image:c5e32912fd1bd00b8bf0afc26d40133305cc95a5bfea9d1c3a0523d633c03011 | jieshi-original-preparation-20261014 | original-preparation-base-repair-20261014-001 | N/A | ba9eb952c5606333727198800fa593abce806b3c239188425ebb7b27087cab4f | PROVIDER_RECEIPT | ACCEPTED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/image-repair-20261014/base-001/execution-receipt.json |
| repair-base-bytes | native-image:c5e32912fd1bd00b8bf0afc26d40133305cc95a5bfea9d1c3a0523d633c03011 | jieshi-original-preparation-20261014 | original-preparation-base-repair-20261014-001 | N/A | ba9eb952c5606333727198800fa593abce806b3c239188425ebb7b27087cab4f | TECHNICAL_BYTES | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | repair-base-submit | runs/canvas-jieshi-original-s01-s02-20261013-001/image-repair-20261014/base-001/image-review.json |
| repair-base-materialization | native-image:c5e32912fd1bd00b8bf0afc26d40133305cc95a5bfea9d1c3a0523d633c03011 | jieshi-original-preparation-20261014 | original-preparation-base-repair-20261014-001 | N/A | ba9eb952c5606333727198800fa593abce806b3c239188425ebb7b27087cab4f | LOCAL_MATERIALIZATION | SUCCEEDED | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | repair-base-submit | runs/canvas-jieshi-original-s01-s02-20261013-001/image-repair-20261014/base-001/stop-state.json |
| repair-base-visual | native-image:c5e32912fd1bd00b8bf0afc26d40133305cc95a5bfea9d1c3a0523d633c03011 | jieshi-original-preparation-20261014 | original-preparation-base-repair-20261014-001 | N/A | ba9eb952c5606333727198800fa593abce806b3c239188425ebb7b27087cab4f | VISUAL_INSPECTION | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | repair-base-submit | runs/canvas-jieshi-original-s01-s02-20261013-001/image-repair-20261014/base-001/image-review.json |
| local-masked-execution | native-image:2d5994083367b056436bd7bb98b2cccd33216de31cb9d4caa5a6054ea07c85ec | jieshi-original-local-masked-20261014 | original-s01-local-masked-20261014-001 | N/A | 62a4414bdc72f1409c88a2fd145ad4bd06d7c85156f6051d7fb0bc2955d982e9 | LOCAL_MODEL_EXECUTION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/local-masked-20261014-001/execution-receipt.json |
| local-masked-visual | native-image:2d5994083367b056436bd7bb98b2cccd33216de31cb9d4caa5a6054ea07c85ec | jieshi-original-local-masked-20261014 | original-s01-local-masked-20261014-001 | N/A | 62a4414bdc72f1409c88a2fd145ad4bd06d7c85156f6051d7fb0bc2955d982e9 | VISUAL_INSPECTION | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | local-masked-execution | runs/canvas-jieshi-original-s01-s02-20261013-001/local-masked-20261014-001/static-image-review.json |
| local-Z-execution | native-image:a6175b8930d3e7bd84ae3bff8bdc6beacc9c73be3973fd6bc1110e5dd6149455 | jieshi-original-local-targeted-repair-20261014 | original-s01-targeted-Z-generation-20261015-001 | N/A | 102c1ec74f873a0de8297d2cf9de1477a9ae1cf0b0fc654836e6e8dc7e127557 | LOCAL_MODEL_EXECUTION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/local-targeted-repair-20261014-001/Z-execution-receipt.json |
| local-Z-visual | native-image:a6175b8930d3e7bd84ae3bff8bdc6beacc9c73be3973fd6bc1110e5dd6149455 | jieshi-original-local-targeted-repair-20261014 | original-s01-targeted-Z-generation-20261015-001 | N/A | 102c1ec74f873a0de8297d2cf9de1477a9ae1cf0b0fc654836e6e8dc7e127557 | VISUAL_INSPECTION | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | local-Z-execution | runs/canvas-jieshi-original-s01-s02-20261013-001/local-targeted-repair-20261014-001/Z-static-image-review.json |
| pose-web-invocation | external-authoring:8811e001d70794f03f8d34edfcdf9d5ea26f20bd53fa907e41d09e84d537fc2b | jieshi-original-pose-reference-trial-20261015 | original-s01-pose-reference-web-20261015-001 | N/A | NO_ARTIFACT:OUTCOME_UNKNOWN | LOCAL_TOOL_EXECUTION | OUTCOME_UNKNOWN | EXECUTION_EVIDENCE_GAP | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/pose-reference-trial-20261015-001/mcp-call-timeout.json |
| codex-direct-generation | native-image:9cdd1fdf7ea2a660361cd3a5b145ccf9557924d74b31bcb9df1ba70c969610d2 | jieshi-original-codex-direct-image-20261015 | original-s01-codex-direct-image-20261015-001 | N/A | f9128ccfde3868ed8aaea420f953e306b37c003e139fd0d85943774eea057e93 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-direct-image-trial-20261015-001/generation-record.json |
| codex-direct-static | native-image:9cdd1fdf7ea2a660361cd3a5b145ccf9557924d74b31bcb9df1ba70c969610d2 | jieshi-original-codex-direct-image-20261015 | original-s01-codex-direct-image-20261015-001 | N/A | f9128ccfde3868ed8aaea420f953e306b37c003e139fd0d85943774eea057e93 | VISUAL_INSPECTION | NOT_EVALUATED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | codex-direct-generation | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-direct-image-trial-20261015-001/static-image-review.json |
| codex-H-generation | native-image:ec84f2686d92d674a6840219eb8249bfd116d4fc80a5067bf7e9afe2c1c8b6ae | jieshi-original-codex-frame-repair-20261015 | original-s01-codex-H-20261015-002 | N/A | a2239581824f32f1ce4e9982913286bb588ed2085df068fffaa80ae8a8dc5c02 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-original-frame-repair-20261015-002/H-generation-record.json |
| codex-H-static | native-image:ec84f2686d92d674a6840219eb8249bfd116d4fc80a5067bf7e9afe2c1c8b6ae | jieshi-original-codex-frame-repair-20261015 | original-s01-codex-H-20261015-002 | N/A | a2239581824f32f1ce4e9982913286bb588ed2085df068fffaa80ae8a8dc5c02 | VISUAL_INSPECTION | NOT_EVALUATED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | codex-H-generation | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-original-frame-repair-20261015-002/H-static-review.json |
| codex-C-generation | native-image:dc249193b5d938df088f4426dece4982c43a7a62c91f96baf372920764178462 | jieshi-original-codex-frame-repair-20261015 | original-s01-codex-C-20261015-002 | N/A | 5c4fe971f222bacda47cc39ae9cb9b5503b0d59e3968e207808a740d5829b099 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-original-frame-repair-20261015-002/C-generation-record.json |
| codex-C-static | native-image:dc249193b5d938df088f4426dece4982c43a7a62c91f96baf372920764178462 | jieshi-original-codex-frame-repair-20261015 | original-s01-codex-C-20261015-002 | N/A | 5c4fe971f222bacda47cc39ae9cb9b5503b0d59e3968e207808a740d5829b099 | VISUAL_INSPECTION | NOT_EVALUATED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | codex-C-generation | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-original-frame-repair-20261015-002/C-static-review.json |
| codex-mirror-generation | native-image:78091e512ad2621c17d9bf9000efce732401c5246f62d0b6af00fcdd22c4ef57 | jieshi-original-codex-mirrored-props-20261015 | original-s01-codex-mirrored-props-20261015-003 | N/A | 64359f615d10e112ff7aaa68181c3b815cf8178382c199dc4073d17519f810dc | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-original-frame-repair-20261015-002/mirror-generation-record.json |
| codex-mirror-static | native-image:78091e512ad2621c17d9bf9000efce732401c5246f62d0b6af00fcdd22c4ef57 | jieshi-original-codex-mirrored-props-20261015 | original-s01-codex-mirrored-props-20261015-003 | N/A | 64359f615d10e112ff7aaa68181c3b815cf8178382c199dc4073d17519f810dc | VISUAL_INSPECTION | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | codex-mirror-generation | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-original-frame-repair-20261015-002/mirror-static-review.json |
| codex-Su-object-generation | native-image:4db7ce4accb006c62e162fe299199e943bf1234d35e7fa8d87470b08aa44a8a1 | jieshi-original-codex-single-object-20261015 | original-s01-codex-Su-single-object-20261015-004 | N/A | a1db0247764947b315110ffe166105dcd5927ebc2f5283d142b20fa91b14ed6f | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-single-object-repair-20261015-004/Su-generation-record.json |
| codex-Su-object-static | native-image:4db7ce4accb006c62e162fe299199e943bf1234d35e7fa8d87470b08aa44a8a1 | jieshi-original-codex-single-object-20261015 | original-s01-codex-Su-single-object-20261015-004 | N/A | a1db0247764947b315110ffe166105dcd5927ebc2f5283d142b20fa91b14ed6f | VISUAL_INSPECTION | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | codex-Su-object-generation | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-single-object-repair-20261015-004/Su-static-review.json |
| codex-Su-crop-generation | native-image:df6a5a7e0d03a4b5eafbdafc7d347a9833447b065f39c22e1ceb4415cd1a5087 | jieshi-original-crop-assisted-20261015 | original-s01-codex-crop-Su-20261015-005 | N/A | eec68abd39f7bbcddf875c066ff5b375f5c3db3e55edc2b20b775e3f9b45f940 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-crop-assisted-repair-20261015-005/crop-generation-record.json |
| codex-Su-crop-local-static | native-image:df6a5a7e0d03a4b5eafbdafc7d347a9833447b065f39c22e1ceb4415cd1a5087 | jieshi-original-crop-assisted-20261015 | original-s01-codex-crop-Su-20261015-005 | N/A | eec68abd39f7bbcddf875c066ff5b375f5c3db3e55edc2b20b775e3f9b45f940 | VISUAL_INSPECTION_LOCAL_ROLE | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | codex-Su-crop-generation | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-crop-assisted-repair-20261015-005/crop-static-review.json |
| codex-Su-full-generation | native-image:8d4633673aa0b23fde9d502abf8e0e3375e3b7c658f93dde62511cfc8894f665 | jieshi-original-crop-assisted-20261015 | original-s01-codex-full-Su-transfer-20261015-005 | N/A | 8b2e95271d911c774e9eb97552d89aba282bd08a664dfc0e71b56e39a8739703 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-crop-assisted-repair-20261015-005/full-generation-record.json |
| codex-Su-full-static | native-image:8d4633673aa0b23fde9d502abf8e0e3375e3b7c658f93dde62511cfc8894f665 | jieshi-original-crop-assisted-20261015 | original-s01-codex-full-Su-transfer-20261015-005 | N/A | 8b2e95271d911c774e9eb97552d89aba282bd08a664dfc0e71b56e39a8739703 | VISUAL_INSPECTION | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | codex-Su-full-generation | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-crop-assisted-repair-20261015-005/full-static-review.json |
| codex-spatial-generation | native-image:3a0249c11a211af64d234e9c4d396c8ae8c22a1a8ab2bf6e6ad2a9ae418b3090 | jieshi-original-spatial-20261015 | original-s01-spatial-20261015-006 | N/A | e70dd60e382146a66ea72d5e4ef3e15e7c0dcf0725ecd6a6e2eb6719a5a6222e | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-spatial-repair-20261015-006/geometry-generation-record.json |
| codex-spatial-static | native-image:3a0249c11a211af64d234e9c4d396c8ae8c22a1a8ab2bf6e6ad2a9ae418b3090 | jieshi-original-spatial-20261015 | original-s01-spatial-20261015-006 | N/A | e70dd60e382146a66ea72d5e4ef3e15e7c0dcf0725ecd6a6e2eb6719a5a6222e | VISUAL_INSPECTION | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | codex-spatial-generation | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-spatial-repair-20261015-006/geometry-static-review.json |
| codex-composition-generation | native-image:677bff52fef55bab774a2b842d430e37c930d120a4f2c21da894a12177476176 | jieshi-original-composition-20261015 | original-s01-composition-20261015-007 | N/A | 7540565b88ecee230d41aeda1348461ef4854b191b8663c6ec34b0941bf6d26a | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-composition-repair-20261015-007/generation-record.json |
| codex-composition-static | native-image:677bff52fef55bab774a2b842d430e37c930d120a4f2c21da894a12177476176 | jieshi-original-composition-20261015 | original-s01-composition-20261015-007 | N/A | 7540565b88ecee230d41aeda1348461ef4854b191b8663c6ec34b0941bf6d26a | VISUAL_INSPECTION | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | codex-composition-generation | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-composition-repair-20261015-007/static-review.json |
| codex-current-10-generation | native-image:56b5f5024c58d7f8168cd10891b5187d3ac01c9ee33e42a940abc7e9cd83457c | jieshi-original-progressive-repair-20261015 | original-s01-wardrobe-crop-20261015-009-01 | N/A | da91e41459a2706588d91a5c6cee92c0b3fbec3aef30ecb44af8a0c73aeb1fbb | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-isolated-repairs-20261015-009/01-generation-record.json |
| codex-current-11-generation | native-image:07aacf1f403415250484ad9f5493f683b49865968546c6ec95c0be9a9267fe71 | jieshi-original-progressive-repair-20261015 | original-s01-wardrobe-full-20261015-009-02 | N/A | 0c82a185769e9a33c0036587cdd2379089673e9f2a4d6536f20a909c64f0be7c | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-isolated-repairs-20261015-009/02-generation-record.json |
| codex-current-12-generation | native-image:542a6d84f4549707d7e3ed1ac76e927a5a41c20049161e1da51babcbd7662dd5 | jieshi-original-progressive-repair-20261015 | original-s01-deduplicate-20261015-009-03 | N/A | 75fd09df2099689d5d2d0682617306001e8b29d305d317aee3e2455fdd30c834 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-isolated-repairs-20261015-009/03-generation-record.json |
| codex-current-13-generation | native-image:c8dc07a778fe6e9fdd9f6a3ee613bb7b8186f5b1d79a1f3e5d44169335a4fc4b | jieshi-original-progressive-repair-20261015 | original-s01-empty-seat-crop-20261015-009-04 | N/A | cfcabeb7036c6e2bef2c39100a64c8ca1b3b8256e788e9bb2949f0a052cde9b2 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-isolated-repairs-20261015-009/04-generation-record.json |
| codex-current-14-generation | native-image:12db8e4e15108ff928d6faf4987281933e0deb5f9a6bf1ea6bc0bc486d333f86 | jieshi-original-progressive-repair-20261015 | original-s01-empty-seat-full-20261015-009-05 | N/A | e5d8d965ff3a7455119d3e95eb6b791e27d0479ee2fca13d7cf88efc81be9cf0 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-isolated-repairs-20261015-009/05-generation-record.json |
| codex-current-15-generation | native-image:29bf8924ecedb8c6d52a3835870c7f735e3e9a1763c7c2fd2932e841f7799113 | jieshi-original-progressive-repair-20261015 | original-s01-chen-arm-crop-20261015-009-06 | N/A | accdc9e5915231fe4541a744c6fce24a432954d8de4a0690b1b529313e382fb1 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-isolated-repairs-20261015-009/06-generation-record.json |
| codex-current-16-generation | native-image:9e56bddebc76fdba0dbcb9b53b2331a41a0673175c5776e3b0efebf2b6cf8e5f | jieshi-original-progressive-repair-20261015 | original-s01-chen-pose-crop-20261015-010-01 | N/A | 3bb173311014491c217b063ef2cc2173252f7e35cfcaa14524dc55e3be4dcee9 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-pose-wardrobe-repairs-20261015-010/01-generation-record.json |
| codex-current-17-generation | native-image:694d40424cddfe03893a7215179df4a40b92ebb5c1845c458bc99b98d2c438bd | jieshi-original-progressive-repair-20261015 | original-s01-pose-primary-20261015-010-02 | N/A | ebc0044e4bee7af763a935d805596a06aac57247bc26678eb9d38cc8702f8e84 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-pose-wardrobe-repairs-20261015-010/02-generation-record.json |
| codex-current-18-generation | native-image:e40201b46f9ec07ad86f2297f68be160d1ac1c3c78d61175061f2ce789284e90 | jieshi-original-progressive-repair-20261015 | original-s01-chen-pose-full-20261015-010-03 | N/A | 116c73e777c20caec174f25bee6fc04eb6070cc9e66301fa5daef4f6f99b1a5e | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-pose-wardrobe-repairs-20261015-010/03-generation-record.json |
| codex-current-19-generation | native-image:a9cea2dc99482a4d1591da805c990485ce164fde07b159ef022282fd35caf96a | jieshi-original-progressive-repair-20261015 | original-s01-ensemble-wardrobe-crop-20261015-010-04 | N/A | 7a1d7e522f693d9922f4016f16a539f4f9315bdf18950805b5341118c4ba5d74 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-pose-wardrobe-repairs-20261015-010/04-generation-record.json |
| codex-current-20-generation | native-image:32ae518704edcda95a1fb58f7254e379c2884344179195509bf0bfe7839a6f8a | jieshi-original-progressive-repair-20261015 | original-s01-original-details-full-20261015-011-01 | N/A | e0915f4e7dadceee5ed8b3117ffd3a6e51b72fd289d4a4141817688a7a9e7421 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-final-original-detail-repair-20261015-011/01-generation-record.json |
| codex-current-21-generation | native-image:8cc74a4f96c843fcfe95b6a76355aa9c0c17b70c88949f21b34b3588e9129995 | jieshi-original-progressive-repair-20261015 | original-s01-badge-crop-20261015-011-02 | N/A | 93f2f12af558e10b6c8f7f54ba61c2e113fe0485158379dceba775eb24d4549d | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-final-original-detail-repair-20261015-011/02-generation-record.json |
| codex-current-22-generation | native-image:dca9ef37a3f22b43e19ccb28dfb707717cf9fa49190795dace34998b714796aa | jieshi-original-progressive-repair-20261015 | original-s01-full-badge-transfer-20261015-011-03 | N/A | 13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-final-original-detail-repair-20261015-011/03-generation-record.json |
| codex-current-22-static | native-image:dca9ef37a3f22b43e19ccb28dfb707717cf9fa49190795dace34998b714796aa | jieshi-original-progressive-repair-20261015 | original-s01-full-badge-transfer-20261015-011-03 | N/A | 13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923 | VISUAL_INSPECTION_FIRST_FRAME_ROLE | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | codex-current-22-generation | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-s01-final-original-detail-repair-20261015-011/03-static-parent-adjudication.json |
| original-S01-submit-rejection | seedance-post:21f67a1c46bba1f7e7fecf60c8bbe18e355f752808f00f66f8300e358d3e490e | jieshi-original-S01-live-20261016 | canvas-32dd80cf21a3147888977db32b3dc86c57e1297b | N/A | NO_ARTIFACT:INPUT_ADMISSION_REJECTED | PROVIDER_RECEIPT | KNOWN_NO_EFFECT | INPUT_ADMISSION | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/original-S01-live-20261016-001/actual-rejection-audit.json |
| original-S01-runtime-evaluation | seedance-post:21f67a1c46bba1f7e7fecf60c8bbe18e355f752808f00f66f8300e358d3e490e | jieshi-original-S01-live-20261016 | canvas-32dd80cf21a3147888977db32b3dc86c57e1297b | N/A | NO_ARTIFACT:INPUT_ADMISSION_REJECTED | CANONICAL_RUNTIME_EVALUATION | RUNTIME_FAILURE | INPUT_ADMISSION | SAME_EVIDENCE_NEW_PROOF_LAYER | original-S01-submit-rejection | runs/canvas-jieshi-original-s01-s02-20261013-001/original-S01-live-20261016-001/canonical-generation-experience.json |
| original-S01-metaso-fetch | metaso-post:48782f5c2aab0e6e5a64757746122fd4799441ee710fa7d36585fa1b1a979d0e | jieshi-original-S01-metaso-20261016 | canvas-785e429d6d7241b741dd75d8f4d5981cef08f876 | N/A | b72a5f426beddf08fb3c9f51fbb0773588ac92a767e595835b60ca601c8c7dd3 | PROVIDER_RECEIPT | FETCHED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/metaso-S01-live-20261016-001/fetch-after-dns-repair.json |
| original-S01-metaso-qa | metaso-post:48782f5c2aab0e6e5a64757746122fd4799441ee710fa7d36585fa1b1a979d0e | jieshi-original-S01-metaso-20261016 | canvas-785e429d6d7241b741dd75d8f4d5981cef08f876 | N/A | b72a5f426beddf08fb3c9f51fbb0773588ac92a767e595835b60ca601c8c7dd3 | ANALYZER | FAIL | QUALITY_FAILURE_AND_EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | original-S01-metaso-fetch | runs/canvas-jieshi-original-s01-s02-20261013-001/metaso-S01-live-20261016-001/canonical-qa-diagnosis.json |
| original-S01-metaso-audio | metaso-post:48782f5c2aab0e6e5a64757746122fd4799441ee710fa7d36585fa1b1a979d0e | jieshi-original-S01-metaso-20261016 | canvas-785e429d6d7241b741dd75d8f4d5981cef08f876 | N/A | b72a5f426beddf08fb3c9f51fbb0773588ac92a767e595835b60ca601c8c7dd3 | AUDIO_ANALYZER_OBSERVATION | OBSERVED_NOT_HUMAN_ACCEPTED | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | original-S01-metaso-fetch | runs/canvas-jieshi-original-s01-s02-20261013-001/metaso-S01-live-20261016-001/exact-mcp-analysis.json |
| original-S01-whitebox-fetch | metaso-post:42910670f97138c0d83cdf9bb7acdc11ee07c8ce2bba427c73aa47c3ce7d1b57 | jieshi-original-S01-whitebox-20261016 | canvas-62d4ee6132573d671a0191ad976dab8f4c97b527 | N/A | 74da665b5f2751f902c1660b6fc9346b4a46e5865357b95db644ae0cc4b07084 | PROVIDER_RECEIPT | FETCHED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/whitebox-S01-20261016-001/runtime-fetch.json |
| original-S01-whitebox-qa | metaso-post:42910670f97138c0d83cdf9bb7acdc11ee07c8ce2bba427c73aa47c3ce7d1b57 | jieshi-original-S01-whitebox-20261016 | canvas-62d4ee6132573d671a0191ad976dab8f4c97b527 | N/A | 74da665b5f2751f902c1660b6fc9346b4a46e5865357b95db644ae0cc4b07084 | ANALYZER | FAIL | QUALITY_FAILURE_AND_EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | original-S01-whitebox-fetch | runs/canvas-jieshi-original-s01-s02-20261013-001/whitebox-S01-20261016-001/qa-diagnosis.actual.json |
| original-S01-whitebox-audio | metaso-post:42910670f97138c0d83cdf9bb7acdc11ee07c8ce2bba427c73aa47c3ce7d1b57 | jieshi-original-S01-whitebox-20261016 | canvas-62d4ee6132573d671a0191ad976dab8f4c97b527 | N/A | 74da665b5f2751f902c1660b6fc9346b4a46e5865357b95db644ae0cc4b07084 | AUDIO_ANALYZER_OBSERVATION | OBSERVED_NOT_HUMAN_ACCEPTED | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | original-S01-whitebox-fetch | runs/canvas-jieshi-original-s01-s02-20261013-001/whitebox-S01-20261016-001/mcp-analysis.actual.json |
| original-S01-optical-fetch | metaso-post:905ba4c0ba5a73e2438686862d182b1968fc3f891a3231ff92e40821d4d5d932 | jieshi-original-S01-optical-20261016 | canvas-65bcbc798a2b1935c7fbd18fc54eeafc803c5b72 | N/A | 32853406063cf3f57adf1ae83ae59599316a930893d0c6f1ccf8bcd76203d5c1 | PROVIDER_RECEIPT | FETCHED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/whitebox-repair-S01-20261016-002/runtime-fetch.json |
| original-S01-optical-qa | metaso-post:905ba4c0ba5a73e2438686862d182b1968fc3f891a3231ff92e40821d4d5d932 | jieshi-original-S01-optical-20261016 | canvas-65bcbc798a2b1935c7fbd18fc54eeafc803c5b72 | N/A | 32853406063cf3f57adf1ae83ae59599316a930893d0c6f1ccf8bcd76203d5c1 | ANALYZER | FAIL | QUALITY_FAILURE_AND_EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | original-S01-optical-fetch | runs/canvas-jieshi-original-s01-s02-20261013-001/whitebox-repair-S01-20261016-002/qa-diagnosis.actual.json |
| original-S01-optical-audio | metaso-post:905ba4c0ba5a73e2438686862d182b1968fc3f891a3231ff92e40821d4d5d932 | jieshi-original-S01-optical-20261016 | canvas-65bcbc798a2b1935c7fbd18fc54eeafc803c5b72 | N/A | 32853406063cf3f57adf1ae83ae59599316a930893d0c6f1ccf8bcd76203d5c1 | AUDIO_ANALYZER_OBSERVATION | OBSERVED_NOT_HUMAN_ACCEPTED | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | original-S01-optical-fetch | runs/canvas-jieshi-original-s01-s02-20261013-001/whitebox-repair-S01-20261016-002/qa-mcp-payload.actual.json |
| original-S01-max-io-401 | official-max-post:canvas-ced3bd552a905aa189c2e3b5ed23f2c64273d43f | jieshi-original-S01-official-max-20261016 | canvas-ced3bd552a905aa189c2e3b5ed23f2c64273d43f | N/A | NO_ARTIFACT:HTTP401_KNOWN_NO_EFFECT | PROVIDER_RECEIPT | KNOWN_NO_EFFECT | AUTHENTICATION_REGION | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-S01-20261016-001/successor-001/wire-observations.json |
| original-S01-max-cn-fetch | official-max-post:aa4fea276e0220266fc81f47c6c66c32f9bbdbb773c631f6160b8d86101e4092 | jieshi-original-S01-official-max-20261016 | canvas-c5f04a3750cb384d4bf55ae00424511ede0f818c | N/A | f0685279ab5d0b2256951ed99bde45afc721a7135d654533296c11c038f86725 | PROVIDER_RECEIPT | FETCHED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-cn-S01-20261016-001/fetch.actual.json |
| original-S01-max-cn-qa | official-max-post:aa4fea276e0220266fc81f47c6c66c32f9bbdbb773c631f6160b8d86101e4092 | jieshi-original-S01-official-max-20261016 | canvas-c5f04a3750cb384d4bf55ae00424511ede0f818c | N/A | f0685279ab5d0b2256951ed99bde45afc721a7135d654533296c11c038f86725 | ANALYZER | FAIL | QUALITY_FAILURE_AND_EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | original-S01-max-cn-fetch | runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-cn-S01-20261016-001/qa-diagnosis.actual.json |
| original-S01-max-cn-audio | official-max-post:aa4fea276e0220266fc81f47c6c66c32f9bbdbb773c631f6160b8d86101e4092 | jieshi-original-S01-official-max-20261016 | canvas-c5f04a3750cb384d4bf55ae00424511ede0f818c | N/A | f0685279ab5d0b2256951ed99bde45afc721a7135d654533296c11c038f86725 | AUDIO_ANALYZER_OBSERVATION | OBSERVED_NOT_HUMAN_ACCEPTED | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | original-S01-max-cn-fetch | runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-cn-S01-20261016-001/exact-mcp-analysis.json |
| original-S01-max-frame-fetch | official-max-attempt:canvas-1693d62e38fffba5c59869059653049cece057cb | official-h3-max-mode-control-20261017 | canvas-1693d62e38fffba5c59869059653049cece057cb | A | e3407abea389e9098f74bdaf25281d741030bbb09830e32cdc6faf793c25df3c | PROVIDER_RECEIPT | FETCHED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-mode-pair-20261017-001/A-fetch.actual.json |
| original-S01-max-frame-qa | official-max-attempt:canvas-1693d62e38fffba5c59869059653049cece057cb | official-h3-max-mode-control-20261017 | canvas-1693d62e38fffba5c59869059653049cece057cb | A | e3407abea389e9098f74bdaf25281d741030bbb09830e32cdc6faf793c25df3c | ANALYZER | FAIL | QUALITY_FAILURE_AND_EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | original-S01-max-frame-fetch | runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-mode-pair-20261017-001/A-qa-diagnosis.actual.json |

## Historical Record And Learning Update

本节为此前第二张paid PNG checkpoint；最新local/engineering评估见上文，历史计数不改写。

前一次checkpoint的no_candidate基于一个视觉样本，为历史结论。本次按 `record-ai-video-session` 更新同一主记录和README，原文/媒体/receipt及foreign dirty保留。按 `distill-ai-video-learning` 自动重新评估仍为 **no_candidate**，但不再声称只有一个视觉样本：已有两个独立实际图片attempt，proof层和旧closure不另计样本。旧图错误为倒置车顶映像/双手持机，新图侧窗/手改善却少人物/重复反射/新增标题；多项输入同时变化，不是isolated-variable comparison。不能由这些输出断言模型不具该能力、添加禁用人物/倒影规则或证明改Skill会解决。现有完整image QA/FAIL STOP已覆盖观察，未形成需要新adoption target的有界机制结论；既有Vidu对白/burned-caption claim明确排除人物/倒影与其他Provider，不构成material update。没有制造重复claim、修改Skill/Policy/Gate、刷新RAG或全局memory。

共享工程已发布0234fc5并核验remote，当前文档checkpoint的receipt/commit/push另列实际结果；工程证明不代图片QA、raw连续镜或正常速度human声画验收。原hook `ai-video-record-6104c772eca8de88` 已在前一record checkpoint以recorded/no_candidate ACKED；本更新不重复ACK旧request或猜新ID。
