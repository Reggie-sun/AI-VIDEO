# Audio Understanding MCP Implementation Plan

## Goal And Scope

给现有project-local `video-analysis`增加真实音频理解的调用接点，并让后续Agent从MCP工具清单与既有playbook找到它。用户已要求接进项目；本计划由Parent self-review后在任务授权内实施，Native Codex保持primary workflow。

## Contract And Invariants

- 复用Gemini官方GenerateContent音频接口和已有httpx，不安装社区MCP或强制本地Qwen。Gemini专用转写/精确时序是另一个能力，不冒充本接点已实现；当前模型能力资料见`docs/research/2026-10-15-audio-understanding-tools.md`。
- 新`audio_understand` MCP默认只做无网络preview；执行仅接受trusted operator runtime factory注入的exact credential supplier及消费一次的authorized execution permit。工具参数/环境文件不接收API key；未配置runtime或不可证明授权、预算、egress、durable intent时fail closed，不发POST。Factory沿既有operator injection pattern，不能成为故事执行器或第二Production state owner。
- 只处理配置的项目媒体目录内no-follow exact文件，要求caller expected SHA；复制固定bytes供分析并在返回前重测原媒体。视频音轨经ffmpeg提取为临时PCM WAV，仅作为分析derivative；保留原MP4/音轨、记录派生SHA，不改变composition/timeline。请求固定origin、exact model、整段WAV、blind观察prompt，不把剧本答案塞给模型；限制尺寸/时长和wire bytes。
- Gemini adapter封存wire/body/source/audio/model fingerprint；credential仅在已验证call之前通过注入supplier取得；消费permit后只POST一次，不redirect/retry/Files upload/fallback。timeout/5xx/transport exception为UNKNOWN且不retry；安全错误不返回raw request/response/credential。
- 输出是结构化观察（转写片段/voice/delivery/background/uncertainties），不是PASS、human听过或qualified profile。结果绑定原媒体与分析WAV、实际model/request/response hashes；模型时间戳不升级为canonical时序或精确measurement。
- `video_analyze`可显式opt-in附带同一音频观察；默认调用/输出保持兼容。生成review bridge显式选择此能力时重验exact SHA、保留音频字段到原`GenerationAnalysisEvidence`，缺失/不匹配停止；现有selected evaluator/presentation/QA/committer裁决不变。没有任何新增generation、activation、自动全PASS、第二timeline或renderer。
- Playbook只新增音频工具锚点，用户已选A允许该hunk独立提交并保留原暂存reviewer修改。详细参数/接线归独立工具文档，surface ownership写入matrix；原始研究与media结果分开。

## File Ownership

Parent：`src/ai_video_mcp/tools/audio_understand.py`、`server.py`、`config.py`、`tools/analyze.py`、`analysis_client.py`、`generation_feedback.py`、相关integration tests、Harness policy和既有docs/record/playbook。

Bounded native worker：仅`src/ai_video_mcp/audio_understanding.py`与`tests/test_mcp_audio_understanding.py`，实现纯请求/响应绑定及可注入的Gemini transport/one-shot analyzer。

Research native worker：仅`docs/research/2026-10-15-audio-understanding-tools.md`；已完成，无其他writes授权。Target files不相交，不创建development worktree。

## Major Milestones

1. RED→GREEN验证独立audio adapter：actual PCM fixture、wire byte accounting、盲观察输入、严格输出、拒绝无permit/错identity/credential failure，单POST与UNKNOWN不retry、secret-safe errors。
2. 接入既有serialized MCP与explicit generation analysis：媒体containment/SHA/audio抽取、preview无副作用、configured-runtime执行、default compatibility、结果与raw bridge绑定/未知不推进。测试覆盖public tool而非复制实现。
3. 更新Agent入口、matrix与一次proof record；运行相关MCP/feedback tests及exact snapshot Harness。Stable implementation按SUBAGENTS Risk Gate判定是否需要一个read-only native reviewer；若触发，修复finding再重验，不用review代实际听音。

## Verification And Completion Boundary

Focused commands：`PYTHONPATH=src:. .venv/bin/python -m pytest -p no:cacheprovider tests/test_mcp_audio_understanding.py tests/test_mcp_audio_understand.py tests/test_mcp_analyze.py tests/test_generation_feedback_review.py -q`，随后Harness按owned paths完整覆盖。

Live音义必须使用已存在exact WAV/MP4，在可信runtime、supplier、qualification、预算和one-use授权齐备后最少1次取证；当前未注入Gemini runtime，不搜别的secret，不因接入授权自动上传音频。离线adapter/stdio接线PASS只能证明工程；没有实际云端音频结果就保留LIVE_NOT_EVALUATED/原镜EVIDENCE_REPAIR_FIRST。原首帧FAIL、旧UNKNOWN、原视频0与用户1.0x验收不因工具接入被关闭。

## Authorized Live Operator Follow-up

2026-10-15用户在明确询问远端API及预算后，将key填入指定`.env`供接入，恢复远端完整多模态路线。Parent将该指定文件仅作为一次私密导入源，经0600/no-follow/allowlisted字段核验后转入exact Secret Service `application=ai-video,provider=gemini-audio,credential=GEMINI_API_KEY`；不输出key，不把dotenv/ambient fallback加入runtime，不删除用户文件。最初import因工具进程无desktop session bus失败，核验同UID标准bus后导入及exact回读成功；未发Provider请求。

本单元只授权development音频能力实验：已有4.032s历史WAV、`gemini-3.8-flash`、固定Google origin、一次POST、30分钟窗口、USD 0.05内部operator upper bound及同额reservation。该数值不是报价、实际账单或对$5账户余额的验证；失败/UNKNOWN不重抽、不remint。Provider拒绝与能力观察分别记录，不提升Production qualification/QA/human acceptance。

新增`src/ai_video_mcp/audio_operator.py`是现有trusted injection seam的唯一development permit实现：固定exact preview/profile/源文件及egress，先持久化并重开immutable intent和reservation，再在validate/consume核验actual clock及源identity；lock+exclusive durable consumption marker阻止并发/重启重复POST。结果/typed failure作为同一operator unit的immutable receipt保存。它不写Production Manifest、另建Product ledger、修改timeline/QA/renderer或伪装generation operation。Secret Service supplier仅查上述exact属性，当前UID标准D-Bus只作为显式非secret host接线；无fallback source。

Native bounded worker只拥有新operator module及`tests/test_mcp_audio_operator.py`；Parent拥有本plan、工具guide/研究/primary record、live unit准备与existing MCP invocation。先RED→GREEN验证seal/expiry/source/model/endpoint/重复与并发consume/重启/credential failure/UNKNOWN/receipt边界，再通过fresh隔离MCP调用现有`audio_understand`。Operator中的outcome wrapper复用原`GeminiAudioAnalyzer`，不改wire/transport/schema/工具参数或现有默认行为。

Parent self-review：scope为已声明trusted audio runtime缺项，数据仅同一已存在exact媒体；必要凭据、有限预算/egress/授权的任务内接线在用户当前意图内。Runtime secret/远端授权失败后果触发一次native `reviewer_xhigh`，先相关tests及exact Harness再review；确认修复后的required review未完成前不发POST。最终仍需实际观察字段及身份判断，而非据tests宣布听音成功。
