---
record_kind: session_summary
topic_id: jieshi-s02-first-frame-preparation
learning_eligibility: ineligible
evidence_index_version: "1"
---

# S02 First-Frame Tool Block

Date: 2026-09-10

## Current Status Update

2026-09-10 后续授权已扩展到一次 S02 视频生成及其必要的视频取帧导入兼容修复。
下文 tool block / reference admission block 是保留的历史阶段；最新状态见本文末尾
`S02 Bounded Framing Repair Result`。S01人审已通过；旧本地失败已显式对账。
S02 attempt02 与后续一次有界构图修复 attempt03 均已下载；两者均存在实际邻座
头脸入镜问题，未激活。本轮新增一次生成额度已用完，未继续提交。

## Scope And Authority

用户在保留 S01 attempt12 后，明确允许制作并保存一张 S02 首帧候选。
本次仅执行一次内置 `image_gen.imagegen` 调用，不生成视频、不导入 Registry、
不修改 QA / Manifest / historical verdict，不 commit/push。

## Exact Inputs

- S01 source MP4 SHA-256: `c56b05e2da5d38bfeddd2d6f58322d84a7d8433c01589112b87d1865b388b7f3`.
- 以 zero-based frame 71、2.958333s 为连续性参考；这是原片前 3s 剪切前的最后一帧。
- 解码参考 PNG SHA-256: `dab6d6711ed23d2c778e9e34f4e84bbbf76b77fd2d50711f8a44fc2d24a7fce6`.
- Authoring source SHA-256: `d0a373ce062564cc5ca64f075db38cbdc1f295063a27dbbeacaf982ca12de921`.
- Image request SHA-256: `ceec2222a18f2579dbc89d595f239be8cfcc29ba6ccad0f5df43407fd62d162b`.

目标沿用 S02 侧面近景：保持林砚身份、服装、朝窗视线、左手悬停、右手手机
所有权与缺失倒影。尚未收手、看扬声器或转向陈立；陈立实际脸/肩不进入首帧。

## Observed Result

内置图像工具返回 `HTTP 403 Forbidden`，错误正文 `error code: 1034`。
没有返回候选图或输出路径，原因未进一步归因为账号、配额或输入违规。
这是一项 tool-service blocker，不是 S02 媒体质量 FAIL；质量保持 NOT_EVALUATED。
没有自动 retry、CLI fallback、其他图像工具调用或 Video Provider submit。

Preparation evidence:

- `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s02-v1/source-binding.json`
- `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s02-v1/s01-attempt12-cut-frame-0071.png`
- `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s02-v1/first-frame-request.json`
- `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s02-v1/first-frame-result.json`

参考 PNG 不是生成的 S02 首帧，也未被登记为已接受连续性 keyframe。

## Verification And Learning

原 MP4 与当前 Manifest bytes 经前后 hash 对比保持不变。
Manifest SHA-256: `09a1f97f3b45101361e8d42acb2184ca4a73dc9204c9f26a53893ade4d3823db`.
No code change or production activation; existing unrelated dirty/staged work retained.

`distill-ai-video-learning` evaluation: `no_candidate`。单次服务拒绝且无媒体产出，
不支持对模型质量或 production strategy 的跨实验结论。

## Follow-up GPT Image 2 Preflight

用户随后回复“可以”，明确允许改用项目 GPT Image 2 工具再尝试一次同一候选。
本轮已执行该工具的 `backend_status(chatgpt-web)`，尚未调用 `generate_image`。

预检显示 `configured=true`、`ready=false`：专用 profile 被另一个 Chrome 进程占用，
其父进程链仍包含 live Codex。未关闭、终止或复用该其他会话。
进一步检查 installed `@ramlyburger/gpt-image-2-mcp` 的公开 schema 与 backend：
`generate_image` 只接受 prompt 等参数，没有 reference-image 字段；API backend 使用
`images.generate`，web backend 当前没有附件上传步骤。不能把本地 PNG 路径作为文字
放进 prompt 后声称已传入参考图，也没有降级为纯文字重建林砚身份。

本轮第二通路 generation calls 为 0；新增授权尚未消耗。结果保存在
`runs/jieshi-e01-i2v-20260907-attempt10/preparation-s02-v1/gpt-image-2-preflight.json`。
原视频与 Manifest 再次确认 hash 不变。S02 candidate 仍未生成，且未改工具代码。
Learning evaluation 仍为 `no_candidate`：这只证明当前安装工具的可用性与输入能力限制。

## Authorized Local Tool Repair

后续用户明确授权修复现有 GPT Image 2 MCP 的浏览器连接与参考图上传，并允许仅重启
该工具的专用 Chrome。已核对 profile 后关闭旧 pipe Chrome；没有关闭其父 Codex
或普通浏览器。所有修改只发生在 repository 外的本地安装 runtime：
`/home/reggie/.local/share/ai-video/gpt-image-2-mcp`。

安装包 `@ramlyburger/gpt-image-2-mcp@0.2.1` 只提供 dist，未提供 TypeScript 源码。
本次为可追踪的本地 dist patch，不是 upstream release，也未修改 AI-VIDEO 源码。
原文件、原 hashes、patch.diff、patched-hashes.json、focused tests 与 README 保存在
`local-patches/s02-reference-inputs-v1/`。重新安装 npm 包可能覆盖该 patch。

- Linux 连接使用 exact profile/process/loopback socket 验证的 CDP。每个 client
  只创建并关闭自己的 tab，disconnect 保留 Chrome 和其他 client。
- `reference_image_paths` 传递到 web backend，上传 exact buffers 并记录 SHA。
  API backend 不支持该输入时明确拒绝，不降级为 text-only。
- 等待 hydrated canonical file input；检查附件集合、上传失败、进度与 server thumbnail。
  仅文件名出现、local blob preview 或 Send 可点击均不能证明完成。
- 提交前再次检查，包括空 reference list 不得夹带残留附件；只进行一次 Send click。
  输出只取本次新增 assistant message 的图片，不把 user reference 当成生成结果。

Parent focused verification: `node --test local-patches/s02-reference-inputs-v1/reference-browser.test.mjs`
通过。覆盖并发启动、双 client 隔离、exact buffers、上传进度、错误、残留/空列表、
API 拒绝及输出隔离；测试使用独立 headless Chrome，不调用生成服务。
Native `reviewer_xhigh` 最终 verdict 为 `accept with concerns`，无 blocking issue。
已知 concern：进程在持有 launch directory lock 时崩溃，可能需要核对 owner 后人工恢复；
没有引入自动 recovery 或擅自删除 Chrome Singleton files。

独立 live upload-only verification 成功：`upload-proof.json` 为 `ready=true`、
`submitted=false`，参考图 SHA 为 `dab6d6711ed23d2c778e9e34f4e84bbbf76b77fd2d50711f8a44fc2d24a7fce6`。
这证明上传通路可用，不证明 S02 媒体质量。

## Authorized Single GPT Image 2 Call

通过新的标准 MCP stdio client 加载修复后的同一 server，确认公开 schema 包含
`reference_image_paths` 且 `backend_status.ready=true`。复核原 MP4 与参考 PNG hash 后，
使用原 S02 creative prompt、exact reference、新 conversation、`n=1` 发出一次
`generate_image`。request 与 one-use call-intent 位于 preparation-s02-v1；已有 intent
阻止脚本盲目重跑。浏览器中已确认对应 user message 和进行中 stop indicator。
结果将在本记录的后续结果段单独记录；本段不声明成功或 acceptance。

没有修改 QA、Manifest、Registry、历史 verdict，也没有视频生成、commit 或 push。

## Candidate Recovered From The Same Completed Call

实际页面已经生成图片，但当前 image-only response 使用 `section[data-turn="assistant"]`，
没有 legacy `data-message-author-role="assistant"`。已修正计数与收集共用 selector，
兼容新容器并排除嵌套 legacy role 重复计数。新增 focused case 通过；同一 native
`reviewer_xhigh` 对此 bounded follow-up verdict 为 `accept`。

原运行 MCP 已加载旧 selector，不能通过磁盘 patch 改变该 in-flight function。
因此仅从已完成的同一对话取回已有 assistant image：匹配完整提交 prompt、确认停止
生成、使用既有 export 函数 fetch exact image bytes；没有再次 Send 或 generate_image。
MCP 原调用结果与此恢复结果分开保留，不将读图恢复伪装成原调用自动成功。

候选图：`preparation-s02-v1/s02-first-frame-candidate-v1.png`，PNG `941x1672`，
SHA-256 `cad2265794ac1277865cebb4b41b3397f0c0aad32f6d4004ee8cff16b0295e55`。
`gpt-image-2-recovered-result.json` 绑定 conversation、exact request hash、原 reference hash
和 fetched image hash；命名后的候选是 exact copy，没有裁剪、放大或其他媒体派生。

视觉判断：朝窗方向、服装、左手悬停、右手手机及无主角对应倒影的关系基本保留，
其他乘客倒影仍可见。构图更近，但仍含腿部，偏中景，尚非预期侧面近景。
精确手窗间距与未来动作接续不由单张图证明。状态为 `CANDIDATE_FOR_DIRECTOR_REVIEW`，
不声明 QA PASS、human acceptance、activation 或 S02 video readiness。

本次新增授权的 image generation call 为 1，无 retry；没有视频生成、Manifest/QA
mutation、commit 或 push。Learning evaluation: `no_candidate`，单次参考图实验不足以
形成可靠跨实验模型质量结论。

原 MCP call 最终返回 `isError=true`、`Timed out waiting for an image`，已原样保存为
`gpt-image-2-result.json`；这是旧 selector 的结果收集失败，不能据此声称没有发生生成。
同一次生成的图片已按上述独立恢复证据落盘。最终 Manifest hash 再次保持
`09a1f97f3b45101361e8d42acb2184ca4a73dc9204c9f26a53893ade4d3823db`。

## S02 Video Authorization And Pre-submit Stop

用户随后明确回复“授权”，批准从认可的首帧开始 S02 视频。授权已保存到
`preparation-s02-video-v1/authorization.json`，单次 ceiling=1、used=0，不要求重复授权。
`creative-request.json` 固定现有4秒动作、对白、首帧 exact hash，尚未冒充已编译的
Provider request，也没有签发 permit。

本轮重新调用 project-local `video_probe` 核对 exact S01 MP4（4.042s、97帧、24fps、
1080x1920、AAC）；这不构成新的 narrative 或 human PASS。当前 existing prospective
shadow 对 attempt12 仍记录 `EVIDENCE_GAP`、`all_required_observed_pass=false`。
用户此前 KEEP 予以保留，但不能自动扩展成每一 canonical hard requirement 的证明。
已向用户提出两项明确问题：前三秒无倒影与他人倒影对照是否可读、约3秒切点是否能
自然接到认可的 S02 首帧。未收到回答前不将 unknown 改成 PASS。

`preflight.json` 记录 `BLOCKED_PREVIOUS_SHOT_EVIDENCE`；按现有 Per-Shot Gate，
当前尚未提交 S02，未调用生成 Provider 或修改 QA/Manifest/history。最终前序
Manifest SHA 仍为 `09a1f97f3b45101361e8d42acb2184ca4a73dc9204c9f26a53893ade4d3823db`。
这不是1.5秒 preference failure，也不是新的授权请求。Learning: `no_candidate`。

## Human Confirmation Received; Actual Import Compatibility Block

用户明确回复“成立”，回答前三秒倒影异常可读与约3秒悬手切点接续两项问题。
已将 exact source SHA、QA v3 content hash、canonical observable/stage/tolerance 和原问答
绑定在 `preparation-s02-video-v1/s01-human-narrative-cut-confirmation.json`。这两个问题
不再等待用户回答；记录不扩张为 historical verdict rewrite 或全部 Final Acceptance。

本轮 project-local MCP 重新取得 exact S01 的9个0.5秒间隔画面样本，并读取广播转写。
MCP 当前 transcribe 输出丢弃 word timing 字段，因此未把 segment end 当作词尾。
使用同一本机已缓存 Whisper medium 权重对 exact MP4 重新做 word alignment，
末字“車”结束估计2.12s，结果为 `s01-word-alignment.json`；此为 analyzer estimate，
不伪造新的 human audio proof 或声学置信区间。

当前真正的提交 blocker 是输入来源表达能力：
`AutomatedBrowserImageImportReceipt.references` 只接受 `ImageReferenceBinding`，
其 role 为 character/scene/style；import validator 还要求对应 active creative 与
Registry asset exact 对齐。而本次真实参考是 S01 MP4 第71帧（2.958333s）的 PNG，
不是已登记的 Character/Scene reference。现有 `ContinuityTerminalImageReferenceBinding`
没有接入 automated browser import。独立 native code_mapper 复核后确认此边界。

Read-only TypeAdapter 复现返回 `literal_error: Input should be 'character', 'scene' or 'style'`，
保存在 `reference-admission-check.json`。probe 只验证 reference 类型，未签发任何 receipt，
其中 diagnostic-only asset ID 不被登记或当作真实 Registry identity。
以空 references 导入会丢弃实际图像输入；把 automated generation 标作 human generation、
改成无关 Character/Scene reference 或直接构造 Registry asset 都不是合法解决方案。

此前 builtin imagegen 403 与后来 GPT Image2 成功是两个独立调用，不能混为 provenance
矛盾。成功来源仍由 recovered-result/request/completion 和 exact PNG bytes 证明。
最小后续范围是给既有自动化图片导入链补齐视频取帧 reference 的验证、持久化及 reopen，
保持既有图像/视频/Registry/committer owners；不重构 QA 或新增生产引擎。

`preflight-after-human.json` 记录 `BLOCKED_REFERENCE_PROVENANCE_ADMISSION`。
S02 generation calls=0，授权 ceiling=1 仍保留；无 permit、Provider submit、QA/Manifest
mutation、code changes、commit 或 push。Manifest SHA 仍为
`09a1f97f3b45101361e8d42acb2184ca4a73dc9204c9f26a53893ade4d3823db`。
Learning evaluation: `no_candidate`，这是确定性兼容缺口，不是模型能力结论。

## S02 Submission Preparation

用户认可的 S02 PNG（`cad2265794ac1277865cebb4b41b3397f0c0aad32f6d4004ee8cff16b0295e55`）
现已通过既有 `ProductionStateCommitter` 初始导入到
`runs/jieshi-e01-i2v-20260907-attempt10/production-s02-v2`。新增
`image_import_video_frame.py` 只表达并验证真实 MP4 → frame PNG 来源；automated import、
reader 与 bootstrap 继续使用同一 receipt/Registry/committer owners。历史图片引用仍可重开。
验证覆盖 exact bytes、frame index、PNG opaque/dimensions、MP4 容器与外部引用拒绝、
旋转后的真实尺寸、初始 bootstrap 取帧校验，以及 reopen/replay 不重复 decoder。
S01 原 MP4 第71帧与来源 PNG 的实际 RGB 派生验证通过；错误第0帧被拒绝。

`production-s02-v1` 是已停止的准备版本：最初 graph-before-QA 顺序错误，随后
未经过完整序列化验证的 QA 缺 final contract source binding，strict reopen 拒绝。
保留其历史及 `s02-v1-preparation-stop.json`；没有通过编辑 Manifest 放行。
v2 的 QA 先做 strict JSON roundtrip；后续 r2 仅修正 recipe inventory 排序，r3 仅将
identity 的 generation guidance 路径对准 exact preservation。所有 observable、
tolerance、measurement、proof、stage 和 final-output contract 保持不变。

已通过当前 `VideoPlanner`、`GenerationFeedbackOrchestrator`、Router 与 Vidu compiler v3
准备首次 S02 `GENERATE_ONCE`。使用现有 `allow_bounded_exploration` 允许没有本镜头历史
质量样本的第一次生成；quality fit 仍为 unknown，没有伪造经验 PASS，没有 best-of-N。
最终 planning dependency graph 也由既有 owner 更新，使其对应当前 requirement/projection。
请求限定 `viduq3-pro`、4秒、1080p、单一已批准首帧、`native_audio=False`；原始素材不是
带最终声轨的交付镜头。“刚才……叫的是我？”保留为可见求证口型提示，精确对白和连续环境声
仍属于既有 P4 final-composition 验收。未调用 Provider 定价、凭据或 HTTP submit。

提交 quota 为1、used0。`preparation-s02-video-v1/` 保存实际 request、decision、execution
binding 和 paid preview。S01 的 narrative/cut 人审“成立”已绑定；旧 exact human hand/gap/audio
只用于原问题范围。新 prospective gate 的 `natural-dynamics` 仍为 `NOT_EVALUATED`，
等待已提出的正常速度整镜动态问题答案；未生成 human proof、未把 KEEP 扩张为该项 PASS。
因此 `live_s02.py` 的 execute 必须阻断。离线检查证明空清单、缺项、重复项、NE、伪造
inapplicability 与错 artifact human proof 全部拒绝，正向 fixture 通过；真实 evidence 未改。

兼容修复 focused tests 为42项通过；native `reviewer_xhigh` 对最终 source diff 为 accept。
docs contract / Harness policy audit / Architecture Gate 检查通过。完整 working-tree suite
`python -m pytest -p no:cacheprovider -q`：4991 passed、4 skipped、16 warnings，exit 0，
耗时2009.02s；它不等同于 exact staged snapshot 的 Harness receipt。由于保留无 commit/push、
无未经明确请求的 worktree 以及现有混合 dirty/staged 状态，本轮没有声称正式 Harness closure。
所有既有非本任务 edits 保留，`_state_commit_bootstrap.py` 的既有 repair-input 逻辑未覆盖。
S01 Manifest 仍为 SHA `09a1f97f3b45101361e8d42acb2184ca4a73dc9204c9f26a53893ade4d3823db`。

Learning evaluation: `no_candidate`。当前是同一来源链的确定性兼容与准备校验，
没有独立 S02 视频样本或可推导模型质量规律的受控对比；未写 Learning placeholder、未刷新 RAG。

最终 operator artifact scoped `reviewer_xhigh` 复核也为 accept：当前 Manifest/graph、
planning/projection、QA、compiled binding 与 preview
`7f9846ab3f8c216ad70d0f9ed035356dc87ff3aea59dfebfc9e22fa7dd5165c6` 一致。
`s02-readiness.json` 标记 `BLOCKED_PREVIOUS_SHOT_EVIDENCE`，唯一 blocker 是
`natural-dynamics`；直接运行真实 `require_s01_gate()` 也在该项拒绝，未发生 Provider effect。

## S01 Dynamics Assessment Before S02

用户随后明确要求“那先评估”，本轮只评估 exact attempt12 的剩余动态问题，未执行 S02。
重新核对 source SHA 与未变的 S01 Manifest；project-local video-analysis MCP 取得 metadata、
0.25s 画面序列及加密序列。额外直接解码全部97帧 luma：97个 unique frame、相邻完全重复0，
PTS 间隔0.041666–0.041667s。`freezedetect=n=-60dB:d=0.25` 和 `-50dB` 均无 freeze events。
这些仅排查相应技术异常，不证明观众观看时动作自然，也不能替代 QA 指定的 human proof。

相邻帧 luma MAD（0–255）min/median/max 为0.25855/0.79031/4.83717；最大值在第96帧
4.00s，10.3053%像素亮度差大于10。逐 index 解码并检查94/95/96帧可见片尾细节变化，
列为 untrimmed 原片质量关注项，不能将单个数值直接升级为 hard failure。它在原已提议的
3秒切点之后。0.8s与3.1s附近较大差异主要可见于玻璃暗带变化；人物和左手没有在所检查
序列中出现明确姿态跳跃。左手逐步抬起并趋于悬停；不能因1.5s margin反向判失败。

本轮仍没有接收连续1.0x视听输入，未宣称完整观看或 whole-shot human PASS。
`s01-natural-dynamics-analyzer.json` 保存 exact source、canonical criterion、统计与观察边界；
prospective Gate 仍为 `NOT_EVALUATED`，没有生成 human confirmation，未改历史 verdict、QA、
Manifest 或媒体。当前建议是保留候选与原3秒切点，不以现有技术证据要求 full regeneration；
整镜自然感、暗带是否分散注意及实际节奏仍待真实正常速度观看。Learning: `no_candidate`。

## Unsubmitted Preview Renewal

用户再次要求“开始shot2”。13:06 UTC 核查时，旧 preview 的有效窗口已于13:04 UTC结束，
S02 仍无 video/paid attempt。旧准备文件逐字保存在
`preparation-s02-video-v1/expired-preview-20260910T1304/`；按已有 Operator Ceiling Renewal
复用同一上限与配置、重新编译并封存 preview
`5de7ec1ccab8b028194a6fbdd4cbd96d0f95501049d8fa3bd2885d169dfe09ee`，quota仍为1、used0。
没有新增预算、Provider调用或凭据查询。

独立 `reviewer_xhigh` 对拟议“保持S01 NE但生成未激活候选”的门禁解释为 reject：
前序全部required PASS的约束发生在submit之前，不因candidate未激活而消失；
用户此前选择先评估，后续“开始shot2”不能替代动态人审或明确的本次门禁豁免。
因此未修改 `require_s01_gate`，未创建例外receipt、未伪造human PASS、未提交。
更新的 readiness仍为`BLOCKED_PREVIOUS_SHOT_EVIDENCE`。Learning: `no_candidate`。

## Human PASS And Local Pre-HTTP Failure

用户随后明确回答“我人审查通过”，只绑定此前刚刚解释和评估的 exact S01
`natural-dynamics`。`s01-human-natural-dynamics-confirmation.json` 保留原话与规范化
answer、actor、source SHA、QA hash、criterion和问题上下文；不是伪造逐字“动态正常”。
旧 NE prospective gate另存`...-before-human-dynamics.json`，当前prospective next-shot gate
为PASS。S01历史QA/verdict/Manifest和原片不变，不再需要重复人审或申请S02生成授权。

13:12 UTC，既有`VideoGenerationService.start/submit_once`尝试执行已批准的一次S02。
parent编写的`live_s02.py`错误地要求旧compiler v2专有的`payload['is_rec']`；当前v3
canonical payload省略该字段，导致KeyError发生在`inner.request`之前。Provider把transport
异常统一封装为`VIDEO_PROVIDER_OUTCOME_UNKNOWN`，此时one-use permit已经consume。
由canonical committer封存的attempt为`jieshi-e01-s02-vidu-i2v-attempt01`，paid phase
`outcome_unknown`、video phase`submit_intent`，没有task ID或fetch receipt。

离线复现使用actual compiled request、exact PNG与旧guard，credential supplier禁止调用、
fake backend计数0，确认必然在`is_rec`处失败；不是通过缺少日志猜测网络结果。
`s02-local-pre-http-failure-proof.json`与`pre-http-failure-20260910/live_s02.py.txt`
保存证据。canonical body SHA为`84e09dcbd26259742ec2d181a471019a17615a0756e9b4e9b7330b415f7343ab`。
旧operator SHA为`9bf62c2b59a22aac6abdcac802dafa084d878559b49b4c85ba14d746825f1f37`。
实际本地guard路径没有发出HTTP；live流程调用过injected credential supplier，未记录secret。

parent已只修正该operator：v3允许缺省`is_rec`，出现时必须False；纯payload检查在
`service.start`之前执行，并在HTTP路径复查。actual v3 payload正向验证通过；错误audio、
duration、model、is_rec、images五项均拒绝；既有6项gate拒绝回归与正向fixture通过。
未再次调用submit，未复用permit，也未修改Product source/recovery架构。

独立code_mapper确认真实阻断：`record_paid_provider_submit_receipt`仅接受SUBMIT_INTENT，
不能覆盖已封存unknown；recovery/resume只能停止。追加quota同时拒绝UNSETTLED预算与
任何既有OUTCOME_UNKNOWN，不能用新attempt/新quota绕开。本次新evidence尚无既有canonical
no-effect对账入口。当前必须保持失败历史和预算状态，后续需明确授权的最小恢复契约修复，
不能直接编辑Manifest。readiness为`BLOCKED_PAID_OUTCOME_UNKNOWN`；actual HTTP POST0、
consumed permit1、S02媒体0。Learning evaluation:`no_candidate`，单次确定性operator事故。

该operator fix与human proof经native`reviewer_xhigh`独立复核为accept；复核明确保留
canonical recovery blocker，不授权第二次提交。未commit/push。

## Explicit No-Effect Reconciliation

用户随后明确“生成,全部授权”，授权最小恢复修复及原来尚未真正发出的那一次 S02。
新增 `paid_provider_no_effect_reconciliation.py` 及既有 paid receipt/reader/committer 的
窄接口，保留旧 unknown receipt/budget 原字节，追加 exact evidence、operator attestation、
correction receipt 和 budget。旧 attempt 为 FAILED / KNOWN_NO_EFFECT，原 reservation
仅释放为 RELEASED / actual 0；原 permit 仍已消耗，不复用。

既有 generation feedback 仅对标准 reader 验证过的 pre-transport reconciliation 使用
`not_submitted`。普通 FAILED / UNKNOWN 不能使用这一例外。替代 attempt 保留完整历史，
通过既有 quota extension 将 durable permit ceiling 从1追加到2、used仍为1；实际新
generation authorization仍只有一次，金额上限不变。

独立 `reviewer_xhigh` 首轮发现 later budget successor 错误拒绝及 authorizer 跨有效期
两项 P1；修正并补测后，又收口实际 authorizer 的 proof→durable request/binding→prior
receipt→attempt 绑定，最终 accept。实际 operator 在无网络副本中完成整条
reconcile→record experience→Orchestrator.prepare→start→quota→paid intent→strict reopen，
原 live Manifest bytes不变，然后才执行真实恢复和提交。

验证：专项16 passed；父线程合并 paid/recovery/generation guard/decision/review 回归
194 passed / 62.70s；docs contract、policy audit、repository architecture gate均通过
（architecture存在既有warning）。后续完整工作树回归完成：5007 passed、4 skipped、
16 warnings / 2129.38s；这不是隔离 exact-staged Harness receipt。未 stage/commit/push，
保留原有dirty/staged工作。
契约说明见 `docs/paid-provider-no-effect-reconciliation.md`。

## S02 Generated Candidate And Post-Media Gate

新 attempt：`jieshi-e01-s02-vidu-i2v-attempt02`，同 task、同获批 PNG、同 S02 prompt，
Vidu Q3 Pro，4秒、1080p、native_audio=False。Preparation及execution在
`runs/jieshi-e01-i2v-20260907-attempt10/preparation-s02-video-v2/`。

- 14:03:18 UTC唯一真实POST发出；14:03:20 HTTP200 / accepted。
- submission fingerprint：`69597d3383b6fb4a4d6dd2c9d5ed9e84ea5628cf45dd18103307196a2c00cfdb`。
- 14:05:23同任务状态SUCCEEDED。初次fetch被host fake-IP DNS（198.18.0.247）拒绝。
- 复用既有 S01 public-DNS fetch procedure，仅在单次进程解析公开CDN hostname；保留
  public-IP校验、pinned direct TLS、无credential下载及禁止redirect。没有重生成。
- 14:08:40 fetch落盘：`production-s02-v2/state/video-generation/fetch/files/382e74c78b5699ea2c1d3b4c942cca9abfc4fd2de3b1a872a06092535b7312bc.mp4`。
- exact SHA-256：`382e74c78b5699ea2c1d3b4c942cca9abfc4fd2de3b1a872a06092535b7312bc`；3152278 bytes。
- project-local `video-analysis` MCP probe：1080×1920、24fps、97frames、4.042s、无audio stream。
- 已执行MCP video_review及17张0.25s间隔抽帧并逐一查看；没有声称收到连续1.0x视听播放。

`s02-post-media-gate.json` 按 exact selected QA、observable/tolerance/measurement/stage/proof
逐项记录。`s02-chenli-boundary`为FAIL：3.25–4.0s新增前景邻座露出头部、耳朵、部分侧脸，
明显不止肩部；该对象不是首帧玻璃中的既有反射。其余整镜、人审或P4项目保持NE，
不从17张抽帧或MCP `issues=[]` 推导whole-shot PASS；S01 human PASS不继承到S02。

当前可播放视频是原始候选，不是最终成片；没有对白/环境声，P4尚未制作。实际generation
额度1/1已用，未自动增加变体、repair submit、VIDEO_EDIT或S03。没有自动activation，
current Manifest revision22、attempt02为validate阶段，reservation02仍reserved，未猜测
真实收费或伪造结算。S01 Manifest SHA仍为
`09a1f97f3b45101361e8d42acb2184ca4a73dc9204c9f26a53893ade4d3823db`。

`record-ai-video-session`稳定记录完成；`distill-ai-video-learning` evaluation为
`no_candidate`：一次实际S02媒体结果与一次无媒体operator事故不构成两个独立的模型质量
实验，也没有可隔离归因的多臂比较。不创建新的学习claim或修改QA。

## S02 Bounded Framing Repair Result

用户在上轮明确报告邻座头脸入镜失败后回复“继续”，结合此前“生成,全部授权”，
本轮封存同一 Vidu / S02 的一次构图修复；不是无限调用、S03、VIDEO_EDIT 或新架构授权。
范围及最小 ceiling 见 `preparation-s02-video-v3/continuation-authorization.json`。

先通过既有 public evaluation seam 分别保留 human 全部 NE 与实际 MCP analyzer 证据，
得到 `EVIDENCE_GAP + QUALITY_FAILURE`；仅 `s02-chenli-boundary` FAIL，五项 raw requirement
仍 unresolved。通过 canonical abandonment owner 显式关闭 attempt02 的已知失败，
保留其 MP4、旧 request/binding、两条 experience、QA、paid accepted 与 reservation02。
没有伪造人审、继承 S01 PASS、改写历史 verdict 或释放已接受调用的费用预留。

Preparation 仅调整 `camera_intent.framing_intent`：限制 pan 终点，保留林砚完整头部，
邻座仅肩部入边缘。首帧 SHA `cad2265794ac1277865cebb4b41b3397f0c0aad32f6d4004ee8cff16b0295e55`、
seed `876261326`、4s、1080p、native_audio=false 及 selected QA 均保持。
Compiled delta 只有 `prompt_text` 和既有 operator upper bound profile 时间续期；没有查价。

隔离 pre-submit 首次被旧 active generation target 的 requirement_hash 阻断。
复用既有 graph builder、transition 与唯一 committer 发布新 generation target，随后重新
prepare binding；没有改动 Shot / QA / Registry 或旧 graph bytes。新 active graph 为
`0e1d0475ee83055d0cce7ea8ec25f45c1ffd40ae39d503b4cd90e9891dedd390`。
隔离副本完成 preview、budget extension、start、quota extension、submit intent 和 strict
reopen；网络和 credential 显式禁用，无 permit consume。Parent 验证旧 attempts 完全相等，
native `reviewer_xhigh` scoped review 为 accept。本轮没有新增产品源码变更，也没有新建
exact-staged Harness receipt；此前 5007 passed 的工作树回归不等于本次媒体通过。

实际 execution：

- attempt：`jieshi-e01-s02-vidu-i2v-attempt03`。
- 14:50:23 UTC 唯一 POST；14:50:24 HTTP200；14:50:31 durable accepted。
- submission fingerprint：`a946be3cf9307ae309911564a85de568b4bfde98439c86f2da6d7eb37ad79b73`。
- 14:52:21 同任务 query 为 succeeded；14:52:55 canonical fetch 完成。
- 下载复用已有 public-DNS procedure，只改变单次进程的确切 CDN hostname 解析，保留
  public-IP 校验、pinned TLS 和无 credential 下载；未重复生成。
- exact MP4：`production-s02-v2/state/video-generation/fetch/files/2c82bfe8197d96241dd535154faaab30dfa4d2aa54dba66e76c7b1a32020c92a.mp4`。
- SHA-256：`2c82bfe8197d96241dd535154faaab30dfa4d2aa54dba66e76c7b1a32020c92a`，3049552 bytes。
- project-local MCP probe、review、0.25s 间隔 17 张抽帧均已执行，parent 逐一查看：
  1080×1920、24fps、97 frames、4.042s、无 audio stream。没有声称连续 1.0x 观看。

### Media Verdict

`preparation-s02-video-v3/s02-post-media-gate.json` 为 FAIL：在 2.25–4.0s 实际已查看样本中，
新增前景邻座的头、耳和部分侧脸明显入镜，4.0s 末帧仍然存在；不是玻璃既有反射。
因此这次构图假设未消除真正 hard defect，不能以工程检查通过放行。旧 attempt02 同类
问题在 3.25–4.0s 样本可见；此比较仅说明已见范围，不推断精确起始时刻或整体优劣。
其他 raw required findings 仍为 NE；不把抽帧、`issues=[]` 或四个样本不同推导成
whole-shot PASS。P4对白与环境声仍未制作；没有声称最终交付。

实际 Manifest revision35，attempt03 保持 validate / paid accepted，未 activation，未开始
S03。本轮新增调用额度 1/1 已用，不继续重试。旧 S01 Manifest SHA 仍为
`09a1f97f3b45101361e8d42acb2184ca4a73dc9204c9f26a53893ade4d3823db`。
运行脚本、sealed previews、授权与 quota/budget receipts、事件、MCP摘要与逐项 Gate
保存在 `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s02-video-v3/`。
未 stage/commit/push；保留已有 dirty/staged 工作。

`record-ai-video-session` 更新原主题记录；`distill-ai-video-learning` evaluation 为
`no_candidate`：目前只证明这一个 S02 构图修复假设在本次 exact attempt 上失败，
不能推广为 Provider 能力结论或提出 QA / Skill / Contract adoption。下一步需要先由
导演评估现有两版镜头与构图策略，不应继续盲目增强同一 prompt 或直接放行。
