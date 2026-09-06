---
record_kind: media_experiment
topic_id: jieshi-s01-local-h3-horizontal-preview
learning_eligibility: eligible
evidence_index_version: "1"
---

# Jieshi S01 Local H3 Bounded Repairs

Date: 2026-09-06

## Unlimited-Budget Continuation — 2026-09-06

用户明确“预算无限”，取消Agent自设的累计尝试次数停止条件。仍采用有限批次、known-outcome检查和独立exact attempts；有证据支持下一修复时自动续批，不重复询问。范围仍为同一local H3 native V2横版S01、同一已批准首帧与required Gate；不改变音频路线。repair3封存010–013四次批次，repair4继续独立有界尝试，**010–012均已fetch并检查，均FAIL；013在SamplerCustomAdvanced发生已知terminal GPU OOM，没有MP4；014改用既有CPU offload模式后仍在SamplerCustomAdvanced发生已知terminal GPU OOM，没有MP4**。下方两轮预算耗尽与shutdown只描述历史状态，当前因其他会话显存占用而阻塞；预算不是停止原因。

- `043ba02`将完整对白块前置；010转写“请在终点下车”，medium和existing-local large-v3均未建立完整原文；额外手影且左手停稳晚于3s。
- 011仅增加姓名/站字的发音指导；large-v3转写“请在终点站下车”，末字3.28s，超出2.7s；额外手影FAIL。
- 012仅把玻璃材质描述改为源剧本要求的固定clean plate表达；MCPmedium转写“林燕,請在終點站下車”，large-v3为“云雁请在终点站下车”，末字3.50s。姓名不同ASR结论保留不确定，时限独立FAIL；左手约3.5s才停稳也FAIL。未后期修改玻璃或音轨。
- 三片均通过full AV decode，11个MCP样本逐帧检查，exact identity见Evidence Index；每版补充转写绑定源SHA。large-v3使用本机已有checkpoint，未下载模型或安装依赖。音频输入不支持，未声称主观试听通过。
- `206a1b1`仅为`/4` language tag之后增加一个ASCII空格，与本地T8 `speech.py:513,522`模板一致；原文bytes、旧`/1`、none和fail-closed行为不变。两个定向测试先红后绿，61focused与703相关测试通过（20.22s）；独立reviewer_xhigh accept并验证31个兼容结果逐字节相同。docs、policy、architecture检查通过。此为013的独立lexical实验，未声称空格已被证明为根因或有效修复。
- 正式Harness receipt限制保持：未自行创建用户禁止的detached worktree，不把working-tree测试冒充receipt；验证日志`runs/jieshi-s01-h3-repair3-20260906/verification-space.log`。7个无关staged文件patch SHA维持`5e6c24dd5a82a3e9f66a79781d234e63491b97293e28716ddbda3f7db611a639`。

截至当前共14次attempt、12个raw视频；没有required findings全PASS。014用既有`--novram`启动后运行210.48s，仍在node10 `SamplerCustomAdvanced` OOM；exact request `42662fa1176ef717a31be186035e9f72ba6ca02c38e73c2e091758e979d8ec25`，provider request `b6f00b35-d1eb-45e9-a3a0-514e1af0c0f6`，见014/runtime-failure.json。两次均known outcome，不blind retry。014后核对owned unit `ai-video-comfyui-cbe620481d1e45919dde90cc77a3dfb6.service` invocation `548a22af69224e1ea4d890e1627d7807`和空queue后停止，见repair4/shutdown.json。其他Codex持有的MCP PIDs20392/24127未终止，游戏未触碰。继续需要其owner允许释放或重启这些驻留GPU模型；无限生成预算不自动授权中断其他会话。013–014没有MP4，所以不能运行exact-MP4 MCP Gate，也不把runtime failure当媒体质量结论。

本次稳定代码/已检查媒体checkpoint自动learning evaluation为`no_candidate`：尚无隔离并重复支持的有效修复，seed随新request变化；不创建采纳请求，不放宽Gate。记录不结束生成任务。

013故障时GPU上可见两个其他Codex持有的MCP Whisper进程（约5.6/5.3GiB）和游戏进程（约2.6GiB）；不终止它们。仅核对本任务ComfyUI invocation和空queue后停止owned unit，并通过既有supervisor `--novram`重新启动，降低GPU常驻权重。机器available RAM约74GiB。此为同scope local lifecycle恢复，不修改profile/graph/台词或旧attempt，不重新提交013。runtime failure原始证据保留本地，未把错误输入tensor dump复制进记录。

## Renewed Continuation — 2026-09-06

用户再次明确“继续”后，封存独立第二轮上限2次、3600秒任务时间、1200秒累计生成预算，见`runs/jieshi-s01-h3-repair2-20260906/budget.json`。008和009均成功fetch并完整检查，均FAIL；**截至本段累计9个raw版本，没有整镜PASS**。下方第一轮6次是历史批次范围，不是当前总数。

`43d733f`仅调整`/4`对白表达：在原文tag前用自然语言表达speaker画内/画外、performance/response、时间窗、lip-sync；只允许marked dialogue内的唯一原文发声。依据本机`speech.py:512–528`表达示例，不能将`no narration`认定为已证实根因。`/1`、无对白及拒绝输出保持逐字节一致；没有修改Provider/profile/音频路线或放宽Gate。

- 008复用002的完整GenerationIntent，只改变对白serialization。mean−46.9dB/peak−30.9dB；MCP及+20dB强制中文转写为空；玻璃有额外手影，FAIL。
- 009仅在008基础上将广播置于低音量环境声前景。转写`李念 请在重点站下车`；MCP粗分段`0–2s`经补充词级对齐被推翻，实际约**1.84–4.52s**。姓名低置信度不能靠ASR独断真人发音错误，但时间窗单独已FAIL；手部倒影同样FAIL。mean−45.4dB/peak−21.5dB。
- 两片均1344×768/124frames/24fps/5.167s/H264+AAC，full AV decode exit0。每版11个MCP抽帧已核对，exact字节identity见下表及run。没有主观试听或人类验收。
- 当前变更2项定向测试先红后绿；61 focused passed，policy要求的测试与H3邻近覆盖去重后703 passed（20.81s）；独立reviewer_xhigh accept，28项纯测试和31个兼容输出比较通过。docs contract、policy audit通过；architecture检查PASS，唯一warning来自不属于本任务的`video_planner.py`增长，未修改该文件。验证日志见repair2/verification.log。第一次手写测试命令拼错文件名，仅0tests收集失败，随后从policy抽取真实路径完成上述验证。
- 正式Harness receipt仍因用户禁止自行创建detached worktree而未生成，不将工作区定向测试冒充receipt。相关其他planning/validation dirty work及既有7个staged文件均保留。独立RAG检索本轮返回fresh，未主动build/index refresh。

第二轮2次预算已耗尽；本任务ComfyUI unit在核对invocation和空queue后停止，见repair2/shutdown.json。`distill-ai-video-learning`仍为`no_candidate`：自然语言表达未证明关闭失败，seed混杂，不提出Skill/Policy/Gate采纳。没有push/release、S02、activation或P6。

可供后续确认的具体替代路线是：保留003仅画面候选（MP4 SHA `2f2927f6f02e89d7a31a1557105184d920317196d5bc631f30aa1e10cbdd5075`）前3秒，独立制作原文“林砚，请在终点站下车。”的女声广播，置于0.1–2.7s，经既有P4时间线/混音/renderer合成后重新检查。**该替代尚未获确认，也未执行**；它改变既有native source-audio路线，不能用它把历史raw Gate改成PASS，不授权remote/paid或新依赖。

## Scope And Current Result

承接用户“继续，一直生成直到第一个 shot 通过检查”，对同一已批准首帧、本地 H3 native V2 横版 S01 连续执行 6 个新 repair attempts（002–007）。全部成功 fetch，全部显式调用 project-local video-analysis MCP，**没有一版全部 required findings PASS**。既有001加本轮共7个raw版本，不是正式竖屏成片。

本轮封存上限6次新attempt、7200秒任务时间、3600秒累计生成预算；停止原因是6次submit配额耗尽。没有未知outcome，没有提交S02、activation或P6/Final Acceptance。原始MP4与canonical Production state仍保留在各run内；Git仅保存选定证据和索引，不保存大媒体。`runs/jieshi-s01-h3-repair-20260906/attempts.json`为Agent实验索引，不是Production生命周期owner。

## Repair Evidence

| Attempt | Single Semantic Change | Observed Result |
| --- | --- | --- |
| 002 | 唯一对白块移入integrated字段 | 完整同音台词可转写，但词级1.48–4.40s；玻璃出现额外手影，FAIL |
| 003 | 快速连贯、立即开口的表达 | 11抽帧及3s原尺寸未见额外手影；台词在自动/强制中文/+20dB诊断均未建立，NOT_EVALUATED |
| 004 | 简洁中文广播指令 | 画面抽检符合主要要求；原音及+20dB转写均为空，NOT_EVALUATED |
| 005 | 广播前景/低音量环境背景层次 | 识别“请在终点站下车”，但2.92–4.38s且姓名/额外词不符；额外手影，FAIL |
| 006 | 在open_state前部提示即时广播 | 画面抽检符合主要要求；原音和+20dB中文转写均为空，NOT_EVALUATED |
| 007 | 基于005增加每秒约5汉字语速 | 两次转写“敏彥 請在咱們的宅家下車”，词级1.02–4.32s；左手3s后仍在上抬，FAIL |

所有输出均1344×768、124frames、24fps、约5.167s、H264/AAC，已全A/V decode。每版exact SHA、size、request、provider request、fetch和逐项verdict位于各自run。可参考003作为**仅画面候选**，不能称整镜通过。003音量mean−47.6dB/peak−23.1dB；004为−46.6/−24.8；006为−42.8/−24.5；007为−43.4/−18.1。音量不直接证明语音质量。

原剧本写“约2cm”；本轮在002媒体检查之前封存`rubric-interpretation.json`，按视觉上小间隙、不接触玻璃判定，保留3秒内完成悬停的要求。不是降低剧本要求或主张单视角精确测距。

## Engineering Change And Verification

`39a0778`只修改shared `_h3_prompt.py` 的 `/4`对白所属字段，台词字节、language、时间窗、old `/1`、无对白、拒绝路径保持不变。依据是本机H3 `speech.py:521–527`；`conditioning.py`和tokenizer不替Agent搬移字段。独立code_mapper确认002 prompt645tokens，对白在528–542token，没有512token截断路径。native reviewer_xhigh verdict accept；27项独立纯测试、31个旧路径/无对白/错误结果逐字节一致。

当前修复验证：60 focused tests通过；扩展Provider/neutral/skill-boundary1184 passed（116.68s）；Harness相关unit/doc/hook206 passed（4.82s）；docs contract、policy audit、task-delta architecture检查通过。日志在`runs/jieshi-s01-h3-repair-20260906/`。**没有fresh正式Harness receipt**：标准runner创建detached worktree，与本任务用户明确不自行创建worktree的规则冲突；未伪造receipt。此前完整suite4453passed/2failed/4skipped，两个失败是shell Python缺whisper，已单独复现；本轮不重跑23分钟全套，也未安装依赖。实际MCP与补充转写使用已有MCP Python环境。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| repair-002-gate | local-request:af1e0225568443563c2ac344e5c65a102bbd10932198c12365344445c5a5e3a3 | jieshi-s01-h3-repair-20260906 | jieshi-s01-h3-horizontal-video-002 | N/A | 75914b14355bcc60cb1262d243cf65a6b6055a3fc32d67b61b069934cc8e5c8c | AGENT_MEDIA_GATE | FAIL | AUDIO_OR_VISUAL_REQUIREMENT_UNMET | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-002/media-gate.json |
| repair-003-gate | local-request:f133535e9fa132b11669ed294f330ff134b12c6a2de1638a3d15ebd108c2ab37 | jieshi-s01-h3-repair-20260906 | jieshi-s01-h3-horizontal-video-003 | N/A | 2f2927f6f02e89d7a31a1557105184d920317196d5bc631f30aa1e10cbdd5075 | AGENT_MEDIA_GATE | NOT_EVALUATED | AUDIO_OR_VISUAL_REQUIREMENT_UNMET | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-003/media-gate.json |
| repair-004-gate | local-request:bd53ce2dd92821aa26ec9c5924329e48bcf42c232914d7b2b0c65db54d43ae3a | jieshi-s01-h3-repair-20260906 | jieshi-s01-h3-horizontal-video-004 | N/A | ccfdf0b9221ace5f2bf29956367980da5aae33cb2efec5900f71c3820d194eae | AGENT_MEDIA_GATE | NOT_EVALUATED | AUDIO_OR_VISUAL_REQUIREMENT_UNMET | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-004/media-gate.json |
| repair-005-gate | local-request:642e71671bb5f5564de1a3bdb035e927172f6924215244dfafc51c7b62401b42 | jieshi-s01-h3-repair-20260906 | jieshi-s01-h3-horizontal-video-005 | N/A | ccf74a18753d3fe14c9f5001b1c748d35ee5971115caf22de1912710344fed39 | AGENT_MEDIA_GATE | FAIL | AUDIO_OR_VISUAL_REQUIREMENT_UNMET | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-005/media-gate.json |
| repair-006-gate | local-request:a5c80537426cea1787cc5a5425ca1793f099bf7a663f6bb7048ae725d81fe82a | jieshi-s01-h3-repair-20260906 | jieshi-s01-h3-horizontal-video-006 | N/A | 0dbc0e12d85342bc871abe219efedc9eab80932dcc8bf49c06cc53c15028673e | AGENT_MEDIA_GATE | NOT_EVALUATED | AUDIO_OR_VISUAL_REQUIREMENT_UNMET | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-006/media-gate.json |
| repair-007-gate | local-request:3fb048d133279464d0f05f9ac6d90af0f1d4832fa41eebd2e6906ef3ff1bb04a | jieshi-s01-h3-repair-20260906 | jieshi-s01-h3-horizontal-video-007 | N/A | 204718617ac34ac437d30a2b5d6c6d6744c5fde027b04a56308ea52e83e007e8 | AGENT_MEDIA_GATE | FAIL | AUDIO_OR_VISUAL_REQUIREMENT_UNMET | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-007/media-gate.json |
| repair-008-gate | local-request:ecb54ea6d800ab24d46b4a9ff90e2c9749e02dd2c70e179b1cdae5ee7eb96fb7 | jieshi-s01-h3-repair2-20260906 | jieshi-s01-h3-horizontal-video-008 | N/A | 1fecf4f0193887527f42a752bd45f5aa1dbd094ed6008983f0962fb8116b60cb | AGENT_MEDIA_GATE | FAIL | AUDIO_OR_VISUAL_REQUIREMENT_UNMET | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-008/media-gate.json |
| repair-009-gate | local-request:1433ea5d17b0cc284f6f761880f619b739f39f42af192163ea671cd41a04c8ab | jieshi-s01-h3-repair2-20260906 | jieshi-s01-h3-horizontal-video-009 | N/A | d8df8b6f8ea2d6c54fe0aa3cb4df3d414458c5e48e10ea231260ad1895371e13 | AGENT_MEDIA_GATE | FAIL | AUDIO_OR_VISUAL_REQUIREMENT_UNMET | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-009/media-gate.json |
| repair-010-gate | local-request:1e67c782d6e39276bafd05a5c191a1a35ef80e6d2a90b5f4224d6fb617d22251 | jieshi-s01-h3-repair3-20260906 | jieshi-s01-h3-horizontal-video-010 | N/A | ab49a94c7fd7868ae7374c35c78f4b8ee7f85c78af425a847904e24c802f668f | AGENT_MEDIA_GATE | FAIL | AUDIO_OR_VISUAL_REQUIREMENT_UNMET | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-010/media-gate.json |
| repair-011-gate | local-request:7140f98dcbac3a69f47797471f5e6cef54abaf9b5f297d2cf553ac54d36bda17 | jieshi-s01-h3-repair3-20260906 | jieshi-s01-h3-horizontal-video-011 | N/A | 8ce0b79c94d98e9a015bb5be2fa68e84132a5a424f0970ba07cf76f7689c74ab | AGENT_MEDIA_GATE | FAIL | AUDIO_OR_VISUAL_REQUIREMENT_UNMET | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-011/media-gate.json |
| repair-012-gate | local-request:ed209098276062078891e508915d78e56110b3b6a3552357b0d995342d0d38bd | jieshi-s01-h3-repair3-20260906 | jieshi-s01-h3-horizontal-video-012 | N/A | b35d0c9b35d59f9ab581005f73678787af7f8c78ed2ae2a76ff4603fbbe30cff | AGENT_MEDIA_GATE | FAIL | AUDIO_OR_VISUAL_REQUIREMENT_UNMET | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-012/media-gate.json |
| repair-013-outcome | local-request:2da0f9c540d2e18c6669d67863e0625e4b91e66a0af727e7f51523d04736dca0 | jieshi-s01-h3-repair3-20260906 | jieshi-s01-h3-horizontal-video-013 | N/A | NO_ARTIFACT:GPU_OUT_OF_MEMORY | RUNTIME_OUTCOME | NOT_EVALUATED | GPU_OUT_OF_MEMORY | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-013/runtime-failure.json |
| repair-014-outcome | local-request:42662fa1176ef717a31be186035e9f72ba6ca02c38e73c2e091758e979d8ec25 | jieshi-s01-h3-repair4-20260906 | jieshi-s01-h3-horizontal-video-014 | N/A | NO_ARTIFACT:GPU_OUT_OF_MEMORY | RUNTIME_OUTCOME | NOT_EVALUATED | GPU_OUT_OF_MEMORY | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-014/runtime-failure.json |

## Boundaries And Learning Evaluation

各attempt复用同一已批准首帧SHA `1ea65e808a44444bd162185e9bacf299f5ff02ebe49556fc147b7a261b7b0061`与exact import receipt，使用同一pinned native V2 profile。严格loopback/local/unmetered，无remote/paid video。每次均经canonical Planner/Router/compiler、preflight、VideoGenerationService、独立intent/permit与ProductionStateCommitter；复用001 driver的in-process配置，不新增运行旁路。

请求派生seed随identity变化；虽每次只改变一个语义变量，这组并非fixed-seed因果对照。后续003/004/006台词仍不可确认，反驳“字段位置修复保证广播”的宽泛结论。`distill-ai-video-learning`评估为**no_candidate**：没有足以要求改变Skill/Provider Policy/Gate的隔离因果结论，不创建placeholder，不自动adopt。

当前Agent音频输入明确返回unsupported，不能声称试听过；female PA音色、全速口型静默及人类质量验收保留NOT_EVALUATED。ASR不是人工试听，增益结果只是diagnostic，不替换原始音轨。未更换source-audio route、混合不同版本、后期抹倒影或用配音伪造raw-MP4通过。下一步若改变音频制作路线须确认对应scope；后续用户已取消累计次数停止条件，有界批次按顶部当前段续行；现有raw Gate保持阻断。

本任务启动的ComfyUI unit已在核对invocation与空队列后停止，见`shutdown.json`。其他staged/dirty工作保持原样；无push/release。记录阶段不产生Provider/media/network effects，未刷新独立RAG index（原experience stale状态未改变）。
