---
record_kind: session_summary
topic_id: jieshi-s01-hand-repair-history-boundary
learning_eligibility: ineligible
---

# S01 Human Gap Finding And History Boundary

Date: 2026-09-08

## Latest Checkpoint — Quality Closed, Budget Extension Pending

用户“ok”授权的显式质量终结已实现并提交为 `6017eed`。独立 `reviewer_xhigh`
复审为 accept with concerns，相关组合 51 passed；正式 exact-range Harness
`1e348a0..6017eed` PASS，Production 3275 passed / 3 skipped。
receipt 位于 `.agent/harness/runs/jieshi-s01-quality-rejection-20260908/receipt.json`，
`verify-receipt` 的完整性、scope、freshness 与 completion proof 均为 true。

真实 `ProductionStateCommitter.reject_video_generation()` 绑定 latest experience
`b10f3a695250b4f1557fb28b8c13dbd2fce36c106f98ee256e1d02b5a03e37f4` 和 exact
attempt10 MP4，将原 RUNNING/VALIDATE 终结为 FAILED / `video_quality_rejected`。
rejection receipt 为 `360edb3bb8d9c28d709d496f935d484f2a780d84637825f439c84b8fe4bd5cc2`。
随后原 generic committer 成功提交下一次 pre-generation graph；strict reopen 为
Manifest r26，Project/Shot 仍 r6。关闭后及 graph 更新后，以原 expected revision/actor
重放均没有 Manifest 写入。旧 paid state、paid-provider 文件与 source09 Manifest
逐项/逐字节保持不变；没有 candidate activation、Provider submit 或新 MP4。

runtime evidence：`runs/jieshi-e01-i2v-20260907-attempt10/preparation-v3/quality-close-runtime-checkpoint.json`。
下一版 requirement hash 为
`5bdc061ff2ebfb11891436b49e6fb3f7f1f944d57a700154072652b0504e4e26`，
graph hash 为 `a2a75533f8e7df2307a14e4b8a0119682634923557220feabbccffd621c74525`。
Planner/graph 准备不等于 sealed submit readiness；profile、Router execution binding、
preview、预算及一次性 permit 仍须在真正 submit 前完成。

剩余独立 blocker：原账本 total ceiling 为 3,000,000 microunits，旧 ACCEPTED 任务
reserved upper bound 同为 3,000,000，available 为 0。质量拒绝不能虚构结算或释放。
当前没有正式预算扩容入口；已提出只增加一次既有内部单次上限、保留原 ledger 和旧预留
的新增 Budget Guard 契约，尚待明确答复。新增一次生成授权未消费；未研究官方价格。

复审非阻断 concern：writer 使用全项目 history、reader 使用本 attempt history；当前
request hash 包含 generation lifecycle，尚无证据证明合法路径可触发差异。component QA
override 不在新入口支持范围，写入前拒绝。未据此扩大本轮 scope。

本轮仅提交 task-owned code/docs；未推送，其他 staged/dirty 文件保留。
`record-ai-video-session` 后自动执行 `distill-ai-video-learning` evaluation：no_candidate。
这是同一媒体证据的 lifecycle 修复，没有新的独立媒体实验，也不证明手部质量改善；
没有专门为记录执行 Provider、媒体、网络或额外测试，未另行刷新 RAG index。

## Historical Checkpoint — Attempt 11 Lifecycle Blocker

以下缺失入口和 r23 状态已被上述 `6017eed` 与真实 r26 checkpoint 取代。

用户再次授权继续，并对链接到 exact attempt10 的三项问题（手部自然、手与玻璃
间隙清楚、广播完整清晰）回复“确认”。该答复按三项肯定观看结论记录；不代表
整体 Gate PASS，也不覆盖 analyzer 的 legacy-03/05 FAIL。通过真实初始化的
project-local MCP session，对同一 MP4 重新取证并调用
`review_generation_attempt(..., repair_evidence=True)`：human06/14/17 PASS，
diagnosis 仅剩 QUALITY_FAILURE，next_owner=shot_router。原评价保留。

strict reopen 为 Manifest r23、Project/Shot r6；完整历史包含 imported09、原10及
补证10三个 experience。补证 evidence hash 为
`9214c8e40f0b4be1d1feb6a7a53b18eb6cd40f5f2b9c4fa97414c0234905c445`。
`preparation-v3/attempt10-human-confirmation.json` 保存问题/原答复与 exact SHA，
`attempt10-repaired-diagnosis.json` 保存实际诊断。下文 r22、人类待答与额度耗尽
仅描述上一 checkpoint；新增一次授权尚未消费。

attempt11 草稿统一 1.5 秒前到位，明确抬手与广播同时开始、连续上移不旋腕；
保留已登记首末帧与广播内容。Planner/requirement projection 已在内存生成，但
更新 dependency graph 的正式 `ProductionStateCommitter.commit()` 在写入前拒绝：
`Production state has an unresolved attempt; explicit recovery is required.`
原因是 attempt10 仍为 RUNNING/VALIDATE；没有新 graph 激活、attempt11 request、
profile 续期、permit、Provider call 或新 MP4。草稿不是可提交请求。

### Missing Runtime Contract

`_state_commit_transaction.py` 拒绝存在 RUNNING/OUTCOME_UNKNOWN 的 generic graph
transaction；`_state_commit_generation_feedback.py` 只追加评价，不结束 attempt。
`_state_commit_video_recovery.py` 保留已 fetch 的 VALIDATE attempt；现有
`record_video_provider_failure` 仅允许 Provider failure/unknown，不能用来表达质量拒绝。
`validate_once` 要求真实 settlement 并准备 candidate，不能冒充失败终结。
Main thread 与 read-only code_mapper 均核对了这些入口；未运行 recovery 或伪造结算。

最小后续 scope 是由现有 `ProductionStateCommitter` 提供显式质量拒绝终结：
绑定 exact fetched bytes 与完整评价、保留 paid reservation/原账单状态，禁止激活，
独立于 Provider failure，并让 subsequent graph transition 仍完整验证历史。
unknown、missing evidence、identity drift 必须拒绝；exact replay 不重复写入。
需要相应 lifecycle/reader/replay/paid-state tests 与独立 review。这是尚未实现的
runtime contract，当前没有通过改写 Manifest 或放宽 unresolved guard 绕过。

本 checkpoint 只修改 task-owned 记录；保留其他已 staged 文件。没有推送。
Learning evaluation：no_candidate；同一视频补证和单次 lifecycle 阻塞不构成新的
独立媒体实验或已证明改进。

## Scope And Result

承接用户“继续生成界蚀shot1”。保留原点名广播、原首帧、已批准修复末帧、Vidu
Q3 Pro及最多一次新提交。用户随后明确“手部出现明显变型”，并对exact旧片前3秒
手与玻璃的小间隙回答“看不清”。旧手部FAIL继续有效，间隙可读性现在也是human
FAIL；不把不可读解释成已测量物理接触或厘米距离。

## Exact Evidence

旧attempt09 MP4 SHA-256为
`7b249ddc7c535b36447b0804909059f2e54a74d0a73328dafe409db16a759302`，
3,476,468 bytes。本会话已重新核对SHA/bytes，并调用project-local video_probe：
1080×1920、24fps、97帧、4.042秒容器、H264/AAC。技术读取不代表质量PASS。

以下派生证据保存在`runs/jieshi-e01-i2v-20260907-attempt10/`，遵循现有runs忽略规则，
本地保留、不强制加入Git：

- `human-visual-review-attempt09-20260908.json`：原话、问题、actor与exact媒体身份；
  SHA-256 `f685ef8e6b2013bab0370b9cae1b9d3cb0f2e8ebb6bde1b38e40427a1ff10660`。
- `historical-human-supplement-20260908.json`：旧2.1 rubric下两项human FAIL；没有改写旧证据。
- `historical-diagnosis-after-visual-20260908.json`：`diagnose_exact_result`实跑只有
  QUALITY_FAILURE，失败项legacy-03/05/06/17，next_owner=shot_router，非Gate PASS。
- `historical-decision-inputs-after-visual-20260908.json`与
  `historical-decision-after-visual-20260908.json`：只向旧输入追加补充证据，纯Router
  历史重放为REASSESS_FEASIBILITY，理由是没有新的可测试intervention。旧profile、
  context与2.1 rubric未升级，不能将这个重放当作当前2.3的生成准备或执行许可。

## Current Execution Boundary

### Supersession — Authorized Compatibility Implementation

用户随后明确“解决”“解决之后再生成”，授权先实现此兼容性边界，再执行原单次
Vidu S01修复。代码checkpoint为`43f45e6`和`a99daf2`：唯一committer导入已知成功fetch
的legacy source，保留原始请求/submit/status/fetch、媒体及实际读取的原始评价文件和
attribution；不制造旧binding、激活或结算。标准loader、feedback与submit guard消费同一历史。
新schema由独立Manifest mixin维护；原Manifest序列化保持兼容。

两次`reviewer_xhigh`审查均accept，独立import tests 13 passed。初次Harness因models/project
增长失败，已提取责任；第二次exact-range Harness已PASS，完整性、freshness及snapshot复核
全部通过：`.agent/harness/runs/jieshi-s01-history-import-20260908-v2/receipt.json`。
Production回归3275 passed / 3 skipped，generation feedback177 passed / 1 skipped，
Provider/lifecycle749 passed；不将这些测试数量相加为独立样本。
原文到typed评价的语义真实性由retrospective evaluator负责，bytes校验不替代它。

`preparation-v2/prepared-history-import.json`已对真实source只读prepare成功，媒体3,476,468
bytes，16项评价保留；`legacy-03/05/06/17`仍全部FAIL。receipt hash
`0a325c94e2f8b951c1521efc87f60299969eeea97e69f4758e1c2fca55c1ad39`。
随后已正式导入旧评价、选择2.3 QA并完成新Provider提交与fetch，见下方Latest Runtime Result。
以下旧“没有导入入口/没有修改核心代码”叙述仅描述本节supersession之前的状态。

### Latest Runtime Result

一次新Vidu Q3 Pro I2V提交于2026-09-07 19:16:03 UTC获接受，随后SUCCEEDED。
原first/approved last bytes、原点名广播保持；固定seed20260907。实际compiled delta仅为
`provider_profile/prompt_text/image_bindings/seed`，旧随机性未控制，不声称单变量因果。
现有requirement/1由实际Vidu native compiler/2支持；离线尝试compiler/3返回unsupported后，
按实际contract选择compiler/2，未借此使用generic compiler或发送额外Provider请求。

首次fetch被Mihomo fake DNS的198.18地址拒绝；使用既有恢复方式对exact公共host做HTTPS
DNS解析，仅在该fetch进程内注入真实公网地址，保留原HTTPS/public-IP/no-redirect guards。
没有额外POST、系统DNS修改或fallback。原请求的成功结果于19:19:04 UTC取回：
SHA-256 `94e7480dfce4374f9b3a4de3006797aae033526a8fc36faa8f9ac19ae0406954`，
3,325,775 bytes；准确路径由attempt10 `preparation-v2/fetch-result.json`保存。

project-local MCP实跑`video_analyze`：1080×1920、24fps、97帧、4.042秒、H264/AAC48kHz
stereo；medium转写原点名广播0–2秒。Main thread检查17帧/0.25秒：legacy-03/05 FAIL，
1.5秒才起手、约3秒近目标且途中掌向变化。其余11项raw技术/抽样analyzer项PASS；
human06/14/17尚无新exact观看答复，NOT_EVALUATED；final subtitle只属于composition。
Gate FAIL，没有质量通过、candidate activation或S02。单次额度已消费，不自动再次生成。

通过真实初始化的project-local MCP ClientSession与`review_generation_attempt`写入canonical
feedback，diagnosis为EVIDENCE_GAP+QUALITY_FAILURE。方便封装`ProjectAnalysisSession`
首次因isolated runtime失败，后续使用实际venv executable的initialized session完成同一
bridge，未伪造analysis proof或修改helper。新experience hash
`2ae553127fd452c025359ce11b99f55a10da6d459e3db01c7de0bb2d71b2a974`。
strict reopen Manifest r22 / Project r6 / Shot r6，attempt RUNNING/VALIDATE；保留付费
reservation，未虚构实际账单结算。source09 Manifest hash复核未变化。

standard `load_production_project()`重开attempt10为Manifest revision 4、Project/Shot
revision 6，`active_qa_policy=None`。准备目录的2.3 acceptance不是canonical active QA。
常规`activate_qa_policy`入口已存在；它本身不能解决历史接入。

`_StateCommitVideoMixin._require_submit_execution_binding`
（`src/ai_video/production/_state_commit_video.py`）要求binding的evidence/experiences
与Manifest完整durable history精确相等，latest hash也必须一致；同Shot旧任务若无
production decision binding则拒绝。`record_generation_experience`
（`_state_commit_generation_feedback.py`）又要求已有exact durable attempt/binding，
所以不能把另一个project内的旧attempt09回溯评价写成v10的新经验。
`record_attempt_evaluation`同样要求durable binding。现有historical replay测试只
验证pure policy，不提供历史导入或新submit证明。

不能通过空history把受控repair变为first attempt，也不能伪造过去不存在的binding、
复制Manifest状态或放宽校验。下一步需要明确的历史证据兼容性设计/实现：验证旧
request、fetch、human/analyzer来源及rubric版本，由唯一committer持久接入，保留
失败和quota语义，再走当前QA/Planner/Router/compiler/preview/permit。
这涉及新的runtime兼容契约，当前媒体任务没有被静默扩大为核心Gate修改。

本轮没有Provider POST/poll/fetch、secret lookup、profile续期、reservation、permit、
candidate activation或S02；没有新MP4，单次修复额度未消费。没有修改核心代码。

## Learning Evaluation

`distill-ai-video-learning`：no_candidate。旧片补充human proof不是独立实验；本次修复
同时改变末帧、动作文本、profile及seed，且新人类质量判断未完成。当前证据不能支持
“修复末帧改善手部”之类可采用的因果结论或新的policy target。保留两个exact结果及
反证，不创建占位Learning Claim。RAG仅作为advisory discovery使用。
