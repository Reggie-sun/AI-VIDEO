---
record_kind: architecture_implementation
topic_id: project-audio-understanding-mcp
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Audio Understanding MCP Integration Record

Date: 2026-10-15

## User Intent And Decision

用户纠正“没有工具吗?去网上找个工具”，随后明确要求“接进项目”“并且让以后的agent也知道这个工具”。Parent用`research`核查官方Gemini音频理解/专用转写及社区MCP实际handler；原生`universal_executor`只写`docs/research/2026-10-15-audio-understanding-tools.md`。公开工具存在，当前Codex不接受audio content不等于其他模型不能听音。选择官方GenerateContent WAV接口、复用已有httpx接入项目MCP；不安装宽泛社区封装、不强制Qwen或开启external engineering subagent。

`superpowers:writing-plans`固定接口、authority与proof边界，计划`docs/superpowers/plans/2026-10-15-audio-understanding-mcp.md`经Parent self-review后执行。Native `bounded_worker` `/root/audio_adapter`仅写adapter与其tests，Parent负责MCP、媒体、bridge、docs；路径不相交且无development worktree。只读mapper `/root/original_video_readiness`查到旧session只传video_path/原QA严格证据接点；它曾读到任务禁止的raw运行配置，已报告并停止，Parent不依赖该读取结论，实际隔离runtime依据既有tests声明及后续真实stdio验证。

## Implemented Boundary

新增`audio_understand`注册进project-local `video-analysis`。默认preview无网络、无runtime import/credential lookup；仅允许项目媒体root内regular no-follow exact MP4/PCM WAV、expected SHA，视频生成临时完整PCM分析derivative不改原片/音轨。请求严格绑定source/audio/model/clock/wire指纹，限制时长/bytes，固定origin、盲观察prompt/JSON schema，不给预期剧本答案。真实执行仅经trusted operator注入exact supplier和一次授权capability，不从MCP args/ambient key/.env找credential。

Adapter在取key前从inline WAV重编canonical请求以拒绝tampered dataclass/endpoint/body/source/clock；ASCII凭据不回显，响应中含raw或JSON解码后的key拒绝保存。permit consume异常、timeout/transport/5xx/redirect为UNKNOWN且不retry；拒绝/缺证保持typed safe错误。输出只是声音观察及estimated timestamps，没有PASS/human。官方GenerateContent wire schema仅使用文档支持的OpenAPI子集，local validator仍strict拒绝额外字段。

`video_analyze`显式`understand_audio=true`才附带音频证据，默认旧调用/输出保留。原`CanvasProductionService.evaluate`→`review_generation_attempt`→隔离MCP显式携带exact SHA，结果留在同一`GenerationAnalysisEvidence`并重开核验source SHA/bytes/audio/request/response/model身份。缺音频/错source阻断，不调用新视频补证、不另建QA/timeline/state owner；selected evaluator/presentation/committer、native音轨/字幕和HyperFrames继续独占原职责。

## Executable Evidence

- Public MCP注册先RED（原列表无audio_understand）；parent错误依赖环境检查（project .venv无mcp）与真正feature RED分开，改用AST注册检查加实际隔离stdio验证。媒体MCP接线9项PASS；缺音频/source mismatch/child参数丢失三个原bridge问题先RED，再修复。
- Adapter初始18项PASS；Parent发现wire指纹未绑定source/clock、可改dataclass endpoint、escaped secret反射等，5个真实RED后修复；permit消费异常和schema子集各有RED→GREEN。最新adapter focused25项PASS，未调用Google API。
- `tests/test_mcp_audio_understanding.py tests/test_mcp_audio_understand.py tests/test_generation_feedback_review.py tests/test_mcp_analyze.py`一次focused97项PASS；`tests/test_canvas_production.py tests/test_generation_feedback_review.py tests/test_generation_evaluation.py tests/test_generation_evaluation_binding.py`93项PASS。schema修正后的final snapshot与完整policy coverage以Harness receipt为准，不能合并不同run当最终PASS。
- 真实isolated MCP进程list_tools能发现工具并调用现有历史WAV：`runs/canvas-jieshi-original-s01-s02-20261013-001/audio-tool-integration-20261015-001/mcp-preview-current.json`。Source SHA `daa154cb46f2a89ce3e95f5dcab6edb019c14a18ea67aef5de4031e0ffeec2d4`，preview网络调用0；执行未配置runtime时实际返回`runtime_required/KNOWN_NO_EFFECT`，没有取key/POST。此文件是能力预检，不是声音理解结果，不改历史原S01质量。

第一次exact Harness `.agent/harness/runs/audio-understanding-mcp-20261015-r1/receipt.json`保留FAILED：11个check先PASS，Provider组941项PASS/1项FAIL；失败为既有hard-cut回归断言只接受P7 message，而Registry内容先被prepared-image校验拒绝。隔离重开predecessor `4fd9fa8d2e5131e76a27066b3e85bea543cdfed0`同一用例仍FAIL，见proof目录`predecessor-regression-check.txt`，不归因音频接入。只改该test增加exact successor明确为False、校验实际typed `PRODUCTION_PROJECT_INVALID`且non-retryable；未改Product guard，后续receipt篡改/zero-call replay断言保留。Focused真实用例1项PASS，再跑全部policy checks；不得把第一次failure重分类或拼接成PASS。

完整exact快照Harness归`.agent/harness/runs/audio-understanding-mcp-20261015-r2/receipt.json`；Risk Gate、native review与Parent裁决归`runs/canvas-jieshi-original-s01-s02-20261013-001/audio-tool-integration-20261015-001/review-risk.json`/`review-*`实际记录。新远端credential处理存在关键泄露/授权失败后果；本实现在native verification后触发一个`reviewer_xhigh`，只读验证绑定/错误与权限边界，不让reviewer补听音。后续文档publication与receipt freshness按actual sidecar/remote SHA核验，不把临时shared worktree或future配置当完成证据。

## Verification And Native Review Repair

完整candidate `16fb739a90b7539c89ec3ab1825f92c871ea3070`的r2 receipt总体PASS：18项实际执行PASS，`seedance_local_video_tests`由同run已通过`production_video_provider_tests`覆盖，非独立执行。既有Harness隔离verification checkout核验exact commit `fresh=true`；shared worktree因保留foreign同文件staged changes而fresh=false，两者分别保存，不冒充shared clean。

原生`reviewer_xhigh` `/root/audio_security_review`初审两项：AUDIO-001（blocking_candidate）自动探测伪装MP4的HLS可读root外音轨；AUDIO-002（non_blocking）本地参数无效却先消费远端分析。Parent均CONFIRMED并修复，review output/裁决归同一proof目录。旧S2 source+新增tests的隔离对照，HLS fixture将目录外synthetic MP4 remux为TS并将audio clock延后0.2s，可复现preview接受及mocked POST；默认AAC offset为负的初始fixture会先被旧clock guard拒绝，不当作攻击成功。早期absolute test path也曾让pytest重新导入current src，保存为无效source-control尝试，后改为temporary verification checkout内仅复制新test并核验旧source hash。有效RED为`review-repair-hls-audio-offset-red.txt`的4项FAIL；真实网络调用0。

修复只改音频MP4 probe/decode为forced MOV/file-only、external drefs与absolute alias禁用，并让组合分析先完成本地处理再消费远端。新增用例覆盖preview/execute在runtime/credential/permit/POST前拒绝伪装输入，以及无效max_frames/frame_interval时零音频调用。修复后focused MCP+generation review共101项PASS；最终增强runtime观察与文档后的精确增量验证归`.agent/harness/runs/audio-understanding-mcp-20261015-r3/receipt.json`，其base为已完整验证S2；r2与r3证明边界分别保留，不声称r2曾检查后续新bytes。安全语义变更仍须同一reviewer full re-review，见`review-round-2`实际结果。

## Agent Discovery And Ownership

MCP自身instructions/tool description说明音频语义工具与Whisper边界；原AGENTS的Per-Shot routing继续指向playbook，新增同段`audio_understand`锚点只归`docs/audio-understanding.md`详细用法。用户选择A允许该新增入口独立提交、保留原暂存reviewer修改。Guide已达210行/18000 bytes，因此只压缩同一句保留显式project-local analysis与逐项PASS语义并增加锚点，不扩大budget或删除Gate。Matrix声明surface owners，Canvas workflow指向同一tool doc，没有第二操作手册。

## Live And Story Boundary

当前没有qualified Gemini audio operator、exact supplier及其授权/预算/egress/durable-intent/one-use接线。现有Production Paid owner也没有audio-analysis operation，本次不硬套旧image/video permit、不伪造新ledger。因此实际Gemini音义、姓名/声线/对白时窗仍LIVE_NOT_EVALUATED/EVIDENCE_REPAIR_FIRST；本窗口没有云端音频请求、模型下载、依赖安装、Production图片/视频generation或Production mutation，仅tests使用局部synthetic fixture。工具真实stdio可发现不等于当前host已运行的旧MCP catalog自动热加载；后续fresh project-local进程读取新源码即可使用已实现入口。

《界蚀》最新图片FAIL/NE、Manifest33/Project7/QA未激活、原视频0、历史视频11与旧web UNKNOWN均保留，工具工程不替代原S01 accepted source、真实handoff、S02自身QA或成片；用户完整1.0x/故事AC-7仍未验。恢复声音实测须由实际operator绑定上面真实外部条件，之后最少一次在已有exact媒体补证，而不是重生视频。

使用`record-ai-video-session`评估为recorded；`distill-ai-video-learning`为no_candidate：这是用户直接要求的工程接口，不是两次独立声音质量实验或受控模型对照，不能据mocked/offline proof生成能力adoption claim。RAG没有refresh/global memory更新；原foreign staged/dirty保留，记录本身不新增媒体/Provider调用。
