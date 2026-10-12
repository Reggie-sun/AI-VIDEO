---
record_kind: architecture_implementation
topic_id: supergrok-subscription-media-provider
learning_eligibility: ineligible
---

# SuperGrok Media Provider Implementation Record

Date: 2026-10-12

## Supersession Notice — Live Smoke 2026-10-12

下文各开发 checkpoint 的“OAuth/billing/generation 为 0”“live BLOCKED”是当时的历史状态。
用户随后要求真实测试并完成官方 OAuth；当前工程交付为 `e03737d65f169c1c732f9c2a3c359e01884271c0`，
显式 included-only authority 已实测，本次 Classic T2V 的唯一 POST 被接受并取回 exact MP4。
最新身份、调用数、下载恢复和逐 Shot verdict 见文末 Live Subscription Smoke Checkpoint。
本次媒体 Gate 为 `NOT_EVALUATED`，没有 activation、Production qualification 或 human acceptance；
其他 Grok 模型/模式与图片仍没有本轮真实生成证明。旧 measurements/receipts 原样保留。

## Scope And Current Status

用户要求将已购买的 SuperGrok 接入图片和视频 Provider，优先使用订阅；随后明确要求
“开workree实现”，取代早先等待共享 writer 的顺序。实现位于
`/home/reggie/vscode_folder/AI-VIDEO-supergrok-media`，branch
`codex/supergrok-media-provider-20261012`，base `75849c7b71c82b2c7a69dddd73d615747de556d6`。
原工作区 Canvas/repair 的 foreign staged/dirty files 未修改、stage 或 commit。

Grok OAuth、只读 usage、image/video adapters 与 canonical Production wiring 已实现。
真实生成仍为 `BLOCKED`：公开 usage 不能证明 exact endpoint 的 included-only 扣费边界，
本任务没有额外现金授权。没有真实 Grok credential lookup、OAuth login、billing GET、
image/video POST 或媒体生成。Fake tests 与工程 review 不构成账号资格、媒体质量或 P6/Final Acceptance。
现有操作说明归 [Grok Provider](../grok-provider.md)，契约归 accepted Spec/Plan、matrix 与 runtime baseline。

## All-Shot Expansion Checkpoint

用户随后要求“所有需要shot的类型都接入,所有grok视频生成能力都要接入”。继续在上述明确
授权的 development worktree，从已发布 `153bd4f7d3dce5cdc1b7e671cd3cd54aad7695d5` 扩展。
accepted [Spec](../superpowers/specs/2026-10-12-grok-all-shot-video-capabilities.md) /
[Plan](../superpowers/plans/2026-10-12-grok-all-shot-video-capabilities.md) 已由 Parent self-review。
本节保留新增 slice 的开发历史；当前交付见下方 Delivery And Evidence，不复用首轮 receipt
冒充新 source 验收。

新增 Full 1.5 / Lite / Classic 的五种适用模式，首尾/last-only、14 references、4 keyframes、
3 preset voices、公开 ratios、source edit/extend。Keyframes/voices 归 sealed profile；exact input
仍进入原 Registry request，POST paths 和 subscription model/operation 精确绑定。
不改写 `<IMAGE_n>` / `<AUDIO_n>` 的已封存 prompt，不猜 actor/tag 映射；preset 不是 voice qualification。
Pure I2V 继承首图比例；edit/extend 无未经文档支持的 output override，拒绝 >720p source 自动缩小。
canonical artifact 与 reader 同时重验 ratio/resolution 和继承尺寸/时长。

Shot tests 覆盖 Generated Video / Hybrid、所有适用 motion categories、semantic continuity、
exact terminal / hard-cut derived first-frame、static C4 和 exact-source hero repair。
产品交互的标准 project loading / approved source / Planner / Router / Grok compiler 路径实际走通；
修复 commercial handoff 丢 conditioning 和固定 v3 的断层，完整意图采用已有 v4，同等复验 approved
first-frame lineage，并在 shared native grammar 表达原 product fidelity。历史 v3 仍通过。
图表/End Card/controlled product Hero 保持 deterministic composition；motion-tail、native camera、
partner custom audio 和未资格的 actor voice obligation 仍明确阻断，不因“全部”削弱质量或授权。

Native scoped evidence：`/tmp/grok-expansion-native.log` 为 **345 passed, 2 warnings**；
补充 Shot/continuous-take/hard-cut 验证 `/tmp/grok-all-shot-native.log` 为 **224 passed**。
两组重叠，不求和。Commercial first red 为 **2 failed / 2 passed**（丢 conditioning），修复后的
standard seam 为 **4 passed**；C4 integration 发现 nominal 无 exact endpoint，专用 variant 改为
exact_seconds，FPS 仍 None；strict milliseconds 不冒充 frame-count。
扩展的完整 policy Harness 与 final Risk Gate 已完成，当前工程证据绑定
`.agent/harness/runs/grok-all-shot-20261012-candidate-4/receipt.json`；下面 candidate-1/2/3
保留为历史尝试，不升级其 partial 或 unfinished 结果。
candidate-1 在 scope diff 检查发现本 record 的行尾空白，尚未运行其他 checks；修正后重新封存。
candidate-2 在 Parent 最终输入审查发现 repeated frame 限制后显式中断，不采 partial PASS 为 completion。
新增重复首尾/不同时间同图的测试先 **2 failed**，修复为按唯一 bytes 核验、按位置保留 payload；
相同 asset_id 的 SHA/metadata 冲突仍拒绝，profile 不偷渡新输入。下一验证单元绑定新 snapshot。
最终 frozen-source 前的扩展 native group 为 **415 passed, 2 warnings, 42.07s**，log
`/tmp/grok-expansion-native-final.log`；warnings 来自既有 legacy serialized-preview/budget seam。
candidate-2 的 receipt 保留 unfinished/pending 状态，不升级为 completion；被中断的子进程已退出。
candidate-3 在 Parent 兼容性检查复现 exact raster 被新增 ratio 等式误拒后显式中断；
此前已完成的 Grok 247、GenerationFeedback 459/1 skipped、voice 47、Harness 275 和规则 44
仅是该历史 snapshot 的部分结果，不能代替完整验收；receipt 保留 unfinished/pending。
标准 Seedance resolve 接受 `864x496` / `16:9`，canonical artifact probe 新回归先
**1 failed / 26 passed**。修正为 exact raster 以原宽高验收、仅 adaptive raster 验精确 ratio，
同组 **27 passed**，同时保留 adaptive wrong-ratio 拒绝；没有通过修改旧 Provider 输出过测试。
Parent self-review 将该 compatibility 明确到 Spec；下一有限单元封存新 staged snapshot。
修正后的完整 native group 为 **416 passed, 2 warnings, 41.85s**，log
`/tmp/grok-expansion-native-candidate4.log`；与历史 415 项重叠，不累加独立计数。

受管 Kimi read-only mapping invocation `38bb4101-b686-462b-a992-ba5320ebabd9`，seal
`251e93012c69cd8295781acb67cf02e95b5f7160623725cd854319dd08ca3467`；canonical receipt 已
机械核验，`PARSED`、4 wire requests、244.2s、actual authenticated `api.kimi.ai/k3/max`，
effective `deep/k3[1m]/max`。报告 SHA256
`55d2c1ef23850d82c396d53af3779a44f45dda965a498ce5cbacda6e5fd3b2f7`。
四个 required Reads 的 exact hashes/完整性匹配，整个 frozen set 在 receipt 核验前未写；
父方 proof 位于 `/tmp/grok-expansion-map/parent-mapping-proof.json`。
建议仅 advisory，采用既有 media roles/profile owner，未建立第二 control map 或 voice authority。
两个 native workers 的 profile 与 adapter paths 完全不相交，完成后交回 Parent，无 stage/commit。
该 mapping 不替代最终 implementation review；官方协议与最终 diff/验收由 Parent 判断。

扩展没有真实 Grok credential、OAuth、billing、上传、generation、媒体 Gate 或 human acceptance。
RAG 查询返回 stale last-good advisory，未前台重建/安装/补网络；与 Grok 无关的片段不作实现证据。
自动 learning evaluation 为 `no_candidate`：engineering/fake evidence 没有独立媒体实验。

### Delivery And Evidence

Code commit `a7a8b31cef9bdbb70364ef75f944479b9e6a4480` 已推送远端 `main` 并经 SSH
`ls-remote` 核验同 SHA；commit tree 与验证时的 staged tree 完全一致：
`92e92afdb2749b85a5f4c25ea0f01f4c2e49608a`。全部 32 个 task-owned paths，原工作区
foreign dirty files 未修改、stage、commit、reset 或 checkout。

candidate-4 完整 Harness 为 `passed`：21 个 selected checks，20 个实际执行通过，1 个
policy-declared same-run covered alias。提交前 `make harness-receipt` 机械核验
`fresh=true`、`complete_completion_proof=true`、`coverage_closed_same_run=true`、
workspace stable / cleanup confirmed、scope/policy/artifact integrity；receipt SHA256
`8f6f7517be05e7fc5e878c97f35a2b7d56ab4121f5bf9f181c0c534862dc042f`。
这是 exact staged snapshot 的提交前证明；不声称改变 Git HEAD 后仍通过 staged freshness。

| Verification | Result |
| --- | --- |
| Native scoped group | 416 passed, 2 legacy serializer warnings |
| Grok Harness | 248 passed, 2 legacy serializer warnings |
| GenerationFeedback | 459 passed, 1 skipped |
| Voice routing / Harness / rule invariants | 47 / 275 / 44 passed |
| Final-output no-regression | 63 passed |
| Shot Router / video Provider / reader | 366 / 927 / 569 passed |
| Commercial source preparation | 1015 passed |
| Vidu / provider-neutral requirement | 194 / 444 passed |

各组重叠，不求和为独立测试数。`seedance_local_video_tests` 在 policy 中由
`production_video_provider_tests` 覆盖，但主 argv 未列出 local-video 和 mixed-reference
两个文件。Parent 在同一不变 staged tree 补跑这两个 exact files，**26 passed, 1.19s**，
JUnit 为同目录 `parent-seedance-supplement.junit.xml`；不伪称 Harness 实际执行了这两份文件。
现有 coverage 声明未借本任务改写；补充可执行证据已完成。
Architecture Gate 为 PASS，保留 `_video_project_reader.py` 1492→1497 effective LOC 的
thin-wiring WARN；新逻辑进入 leaf modules，没有刷新 baseline 或降低断言。

Parent 在全部 native / Harness 后对 exact snapshot 判断
`KIMI_REVIEW_NOT_REQUIRED`，decision / source hashes / verification bindings 归同目录
`risk-gate.json`、`candidate-source.json`。新增 operation 仍是同 pinned origin 下的 literal
paths，redirect/ambient auth 禁止不变；model/operation、素材 bytes 与 source approval 的
拒绝路径已实际验证，未新增 project/state/activation authority。修正后的 exact-raster
compatibility 与 alias 测试缺口已获得 executable evidence。没有识别出剩余已启用路径的
重大语义验证缺口；外部账号/扣费/质量问题仍由 default guard 阻断，工程 reviewer 不能代证。
既有 Kimi mapping 不作为本 candidate 的 final review；不机械因新 backend/diff size 追加 reviewer。

此后仅更新本 record，code / policy / Spec / Plan / tests bytes 保持不变；文档 delta 另经
`.agent/harness/runs/grok-all-shot-20261012-record-final-range/receipt.json` 的 exact commit-range
验证。当前 publication 与 source-byte equivalence 的机器证据归 candidate-4 同目录
`publication-proof.json`；不把文档 receipt 当作完整代码重新执行的证明。
真实 Grok credential/OAuth/billing/upload/generation 为 **0**；账号/proxy admission、included-only
扣费与媒体质量未验证，live 仍 **BLOCKED**，P6 / human acceptance **NOT_EVALUATED**。
record / automatic distill 已评估为 `recorded` / `no_candidate`；无新 Learning Claim、adoption
或 RAG rebuild。

## Implementation And Ownership

OAuth token 仅存 exact OS Secret Service item；显式 refresh 在 POST 前封存 unknown marker，
不从环境、Cookie 或 Console key fallback。API 与 CDN origins 固定，CDN 下载不携 credential。
Default subscription guard 始终拒绝，model/evidence 的构造与 fake no-op guard 不授权真实请求。
订阅 finite count 进入原 paid owner，零金额不清除现金 reservations、submit history 或 unknown。

视频经原 Registry/Planner/Router/compiler/VideoGenerationService；明确 unsupported controls，
未请求 FPS 使用显式 `None`，不伪造帧率、不放宽 fixed requirement。图片经唯一 committer 的
remote seam；paid POST permit 只消费一次，submit 后私有 activation proof 不授权新 POST。
PNG/JPEG/WebP 原 wire bytes 独立 content-addressed 保存，reader 重验转换和 paid provenance joins。
图片 metadata/measurement 拆到叶模块，保留旧 public imports、request/receipt/hash/replay。

## Verification And Corrections

Exact candidate-8 index tree `a90cd9c4d21f0b66c1aab9d61d665964b56507bc`，45 个 task-owned paths。
`.agent/harness/runs/supergrok-media-20261012-candidate-8/receipt.json` 为 `passed`；
`make harness-receipt` 机械核验 `fresh=true`、`complete_completion_proof=true`、
`coverage_closed_same_run=true`、workspace stable/cleanup confirmed。三个 covered aliases
按同一 run 的完整覆盖闭合，不伪称重复执行。各组有重叠，不将下表求和为独立 tests。

| Verification | Result |
| --- | --- |
| Grok auth/subscription/image/video/lifecycle | 123 passed |
| Generation feedback | 429 passed, 1 skipped |
| Paid no-effect reconciliation | 16 passed |
| Existing Provider / paid lifecycle | 918 passed |
| Vidu ad / Vidu | 51 / 194 passed |
| Voice source routing | 47 passed |
| Harness / Agent invariants | 275 / 44 passed |
| Final-output no-regression / Shot routing | 63 / 364 passed |
| Shared Production contracts | 3963 passed, 3 skipped; 2216 deselected |
| CLI/config | 15 passed |
| Image contracts | 1288 passed |
| Neutral video requirements | 442 passed |

Architecture Gate `PASS`，1 `WARN`：历史 oversized `_image_project_reader.py` 的 effective LOC
为 1043 → 1054（+11）；新增 remote joins 已归叶模块，入口接线仍计入增长。未刷新 baseline、
未增加 exception；此 warning 保留为 architecture debt。

第一次 Harness 使用窄 PATH，已有 ffprobe 位于 `/home/reggie/miniconda3/bin` 而未被纳入，
导致媒体 fixture 构造失败。恢复原 PATH 并 prepend 既有 `.venv/bin` 后相关 56 项验证通过；
没有安装依赖或修改 gate 来绕过失败。
只读核实 `/usr/bin/secret-tool` 已存在；未枚举 Secret Service item、未读取 credential，
Secret Service unlock 和真实账号资格仍需登录时核验。
回归还发现 Pydantic wrap serializer 在 legacy budget `model_construct` seam 接收 raw dict：
reservation serializer 改为读取 handler 输出，8 项针对性测试及 918 项 Provider/paid 回归通过。
Harness self-test发现新 Grok check 未加入 full-suite coverage 声明；声明已补齐，182 项自测通过。
旧失败 receipts 保留，不复写历史，不刷新 Architecture baseline。

Parent 补充检查又复现 legacy serialized-preview Gate.create 回归：base 可重建，
新 preview wrap serializer 收到 raw dict 时抛错。先新增用例得到 1 failed，再读取 handler
输出而非 self 属性，229 项针对性验证通过。candidate-4 的 owned pytest group 被明确
SIGINT 中断，receipt 为 failed/interrupted，isolation cleanup passed；不将其称为 PASS。
candidate-5 在后续 auth 修复后也被明确中断；不采其 partial 结果为最终 PASS。
Parent deterministic repro 显示两个 refresh 可用同一旧 token POST 两次，第二调用 unknown
被第一调用 cached ready record 覆盖。先增加用例得到 1 failed，再以 private runtime
内空文件的 Linux flock 串行 login/refresh；busy 零 lookup/HTTP，跨进程释放及 symlink
拒绝验证通过。锁不保存凭据，Native tests 使用自己的 private tmp_path。
另复现 request_id 为 . / .. 仍被接受（2 failed）；parser 现归类 unknown，transport
要求 canonical encoded task segment。auth/video boundary tests 共 48 passed。
CLI Ctrl-C 的补充用例先得到 1 failed，再修正为 exit 130 / sanitized status；
中断 refresh 仍为 unknown，只经显式 login 恢复。candidate-6 的 Grok check 为
121 passed / 1 failed：cross-process 子进程未载入 isolated source，已显式绑定 parent
当前 module 的 src root。245 项 auth/video/Harness 验证通过。
candidate-7 的 Production check 在 1800.032s 超时：3966 项 selection 已处理约 98%，
progress 包含 1 个 F。按同一 node-id selection 对照输出，定位 MRO order 测试并单项
复现 1 failed：新增 remote image owner 尚未进入原 expected order。只更新完整 owner
列表、remote method ownership 与 private-module boundaries，旧 owner 顺序不变。
结构/Harness 针对性验证为 214 passed。Production check 有界窗口从 1800s 改为 2400s；
argv、selection、断言与质量要求未削弱，旧超时 receipt 保留。下一 candidate-8 和
交付 exact range 为两个有限验证单元，未将 partial 结果宣称 PASS。

## Managed Delegation And Final Review

Read-only lifecycle mapping invocation `fba60092-190a-4a1f-86ca-f3f613f38ab1`，
canonical receipt 已机械核验，8 wire requests；actual provider `api.kimi.ai/k3`，
effective route `deep/k3[1m]/max`。报告 SHA-256
`2d82ddcf629a97aef3768c12ef5d016d96e9fe65bc4e92e03d7bd2c4edfcd4e2`。
Parent 拒绝了双 generation permit 建议，采用 accepted-submit 后 activation proof。
该 mapping 不替代 implementation review。

Risk Gate 为 `KIMI_REVIEW_REQUIRED`：OAuth discovery 的 token/userinfo URL 最终接收
refresh token / access-token Bearer；遗漏 origin/path/redirect guard 会泄露账号级凭据，
且认证 CLI 不依赖 media admission。Default guard 阻断媒体不能替代认证边界审查。
Decision 与 sealed identity 归
`.agent/harness/runs/supergrok-media-20261012-candidate-8/risk-gate.json`。

首次 implementation review invocation `02109802-0670-482e-a3d0-6668fbc659b0`，
seal `3f3b019cde01bc145cacef2dbd03299439b3e47ffe09ec1ed147de60c49b2272`，
绑定上述 index tree / Spec / Plan / fresh Harness。Canonical receipt 已通过 `subagent receipt`
机械核验；actual provider `api.kimi.ai/k3`、effective `deep/k3[1m]/max`，17 wire requests。
其 outcome 是 `PROCESS_OUTPUT_LIMIT`：2154.990s 后 stdout observed 16779206 bytes、
stderr 73 bytes，超过原 sealed 16777216-byte ceiling；process exit 0 不构成 review。
没有 terminal structured report，observed_reads 为空；截断输出继续隔离，不采用 partial findings。
该失败不证明实现存在或不存在 blocker，也不抹除先前真实调用/消费。

后续审查将只向所触发的凭据风险提供 minimum sufficient package，仍保留同一有限
maximum policy、必要 source Read / exact identity / completed native evidence；不增加 hard cap、
不降低 model/effort、不机械重跑同一大包。实际最终 managed review / Parent adjudication
归交付快照旁的 `latest-managed-review.json`，每轮保留独立 invocation 与历史。
该 artifact 是外部 canonical receipt 的 sanitized pointer，不代签 acceptance。

## Publication And Remaining Conditions

Implementation 仅 stage owned paths。实际 commit/remote SHA 与 final exact-range receipt 由
交付时重新核验，不以本 record 或旧 preflight publication 冒充 Provider activation。
本 record 保存 candidate-8 的开发 checkpoint；不是后来 `main` bytes 的验收替代。
开发期间远端推进到 `1382d4987ffd8a8b2aa2519944121705a9c62679`（Canvas preserved-source /
nominal endpoint recovery）。交付前只在 authorized worktree 中整合并保留该提交，原 working tree
不 reset、checkout 或清理。最新交付 scope 与 Git HEAD 由
`.agent/harness/runs/supergrok-media-20261012-final-range-1/receipt.json` 绑定；
其 source identity、integration proof 与最终 review pointer 同目录保存。
该目录的实际完整证据和交付 Git SHA 才决定完成状态，不将本 record 的旧 PASS 或
local checkpoint 视作当前 `main` 已发布、Provider 已激活或最终验收。

继续真实调用的最小条件为用户完成官方 OAuth、核验账号/model 资格及 exact included-only
扣费边界；若服务端不能限制 overage，则需要新的明确费用 scope，不能客户端假设零扣费。
真实 image/video smoke、逐 Shot MCP、human normal-speed review 与成片验收均 `NOT_EVALUATED`。
Project RAG 在本 worktree 缺失 index，按 retrieve Skill 停止；没有 rebuild/install，index 未刷新。

## Learning Evaluation

`distill-ai-video-learning` 结果 `no_candidate`。这是代码/protocol integration 及 fake regression
证据，没有独立真实生成实验或受控媒体比较；不创建 Learning Claim，不标记 ADOPTED。

## Live Subscription Smoke Checkpoint — 2026-10-12

### Authentication And Included-Only Boundary

用户要求“真实grok生成测试”，已完成官方 device authorization。修复 browser verification URI
只允许官方 `accounts.x.ai/oauth2/device`，complete URI 必须精确绑定 public `user_code`；
token/device/userinfo 的固定 transport authority 不变。真实 credential 仅由 injected supplier
查 exact OS Secret Service reference `GROK_OAUTH`，没有 Console key、Cookie、环境或其他 item fallback。

`GrokIncludedOnlyAuthority` 显式注入，default guard 继续拒绝。两条固定只读 GET 分别重开 usage
和 auto-topup-rule：观察到 unified billing、current quota 8%、有效 period，以及
`onDemandCap.val=0` / `onDemandUsed.val=0` / `prepaidBalance.val=0`；auto-topup-rule 为已知无 rule。
`SAVED_PAYMENT_METHOD` 不被误当成已启用自动充值，空未知 billing schema 不被当作零费用。
这些是 submit 前真实 observations 和 sealed zero-cash admission，不是事后账单或市场价格证明。
没有修改账号扣费配置、启用 PAYG/Auto Top Up 或购买 credits。

普通 `/models` 只有 LLM、视频目录 404 不构成没有视频资格的证据。本次 accepted POST 证明
这个账号的 Classic `grok-imagine-video` 可执行；没有将该观察升级为全部模型 entitlement。
工程 correction 已提交并推送 `main`，SHA 为上述 `e03737d`，提交时远端同 SHA。

### Exact Attempt And Canonical Effect

本轮有限边界为一次 T2V、nominal 3s/480p/16:9、native_audio=false、cash upper bound 0，
只发送 synthetic prompt，不上传图片/视频/reference。coverage v4 lint 和 exact native prompt
在 submit 前检查，四个 required findings 由 `media-gate-contract.json` 先封存。
canonical `GenerationFeedbackOrchestrator` / Grok compiler / `VideoGenerationService` /
`ProductionStateCommitter` 完成 preview、authorization、reservation、one-use permit、submit 和 fetch。
仅复用标准 repository fixture factory 来 seed disposable experimental project；credential、
guard、HTTPX transport 和上述 effect lifecycle 为真实运行，没有 fixture evaluator 签质量或资格。

| Identity | Value |
| --- | --- |
| Attempt | `grok-real-smoke-20261012-1` |
| Provider task | `a440518a-4cec-916b-b58b-c4df0ab1d8d4` |
| Model / operation | `grok-imagine-video` / `/v1/videos/generations` |
| Media POST count | **1**，HTTP 200；recovery POST **0** |
| Resolved request hash | `ed77dd6e2adb162857c12ec36c73f19e3bf36836661ca9e286333846c9ffebbf` |
| Execution binding | `82ae2495613bfe2408d2ae53da90012088ccc83e24d7b790ac11f6144f3a6b92` |
| Fetch fingerprint | `bf4823c52128561dba70dfec40ea7ca4bdf14e887d227ac9d09c5f36a27bee5f` |
| Exact MP4 SHA256 | `d5dc2116bbadbe58f787536ad6e2a94e525c457c8e8fbfacc4796e0470fdd2ee` |
| Bytes / measured output | 311868 / H.264 High、848×480、24fps、73 frames、3.042s、无音轨 |
| Manifest phase | `validate`；未登记候选验收或 activation |

实验与 exact 原媒体位于 repository 外：
`/tmp/grok-live-preflight-w9192798/smoke-project/state/video-generation/fetch/files/`，
文件名为上述 MP4 SHA256 加 `.mp4`。同 root 的 canonical fetch receipt 为
`state/video-generation/fetch/receipts/bf4823c52128561dba70dfec40ea7ca4bdf14e887d227ac9d09c5f36a27bee5f.json`，
receipt SHA256 `4c1ce030bf803c4493d6b63313c3f2e86430926cd33ccc17ff9ba703cfd4c8a3`。
随后按同 SHA 核验并保留 byte-identical raw artifact 副本于
`runs/grok-real-smoke-20261012-1/artifacts/grok-classic-t2v.mp4`；selected sanitized MCP/recovery
evidence 归同 run 的 `evidence/`，身份映射和 hashes 归 `archive-proof.json`。
这是 ignored local media archive，不进入 Git publication、Registry、Manifest 或 Production acceptance；
原 canonical experimental root 仍在 `/tmp`，没有移动或重写其 identity。

### Fetch Recovery And Evidence Correction

真实结果来自既有 allowlist 的 `https://vidgen.x.ai`，并没有换 CDN domain。
首次 fetch 被公网地址校验拒绝，因为 active Mihomo fake-IP 将其解析为 `198.18.2.5`。
早先“返回新域名”的判断已由 locator shape 和当前 resolver 证据纠正；未扩大 origins。
对同一 accepted task，仅在本次恢复进程、实际 HTTPS DoH observation 的 TTL 内，为
`vidgen.x.ai` 使用已观察到的公网 addresses；保留 public-IP pin、原 hostname TLS/SNI、证书
和 redirect/credential guards。其他域名与全局 DNS/代理配置不变，没有 root 配置或新 media POST。
canonical fetch 实际成功落盘并推进 `validate`；scratch reporter 随后错误读取不存在的
`fetch_receipt_fingerprint`，其 AttributeError 不代表 fetch 失败。核对 Manifest 和 bytes 后写
`fetch-recovery-confirmed.json` supersede reporter，未为修正报告重复 fetch/submit。
同样保留 scratch `generation-intent.json`，另由原 canonical execution binding 投影保存
`sealed-generation-intent.json` / `sealed-intent-source-proof.json`；scratch 未反映 factory 的
最终 projection，不作为 exact intent authority，也没有改写原 binding/request。

### Per-Shot Media Gate And Acceptance Boundary

exact MP4 取回后显式调用 project-local `video-analysis` MCP 的 probe、0.5s samples、
0.1s endpoint samples 和 scene detection。raw evidence 保存于同一 `/tmp` root 的
`video-analysis-probe.json` / `video-analysis-frames.json` / `video-analysis-dense-end-frames.json` /
`video-analysis-scene.json`。Parent verdict 为 `per-shot-gate-verdict.json`，SHA256
`03a870e6e0fdaf7946f8db30096650fdc165e91eea1640dc4647cd18a97740be`。

| Finding | Verdict | Evidence And Limit |
| --- | --- | --- |
| media | PASS | exact H.264 可抽取可见 frames；nominal 3s/480p 实测如上，named ratio 仍为 request metadata |
| action | NOT_EVALUATED | 右手一次拿杯与末端持杯可见；sealed intent 的站立要求因下半身裁切无法确认，未正常速度人工验收 |
| camera-continuity | PASS | 七个 0.5s samples 的人物/杯子/固定中景一致，scene detector 检测到一个 scene |
| audio | PASS | probe 无 audio stream，与声明 silence 一致 |

overall `NOT_EVALUATED`，本轮 STOP，remaining submit count 0，next submit 不允许。
请求 16:9，但实际 848×480 为 `53:30`；没有宣称 exact equality，也没有降低 canonical
strict-ratio verifier。candidate/output validation **NOT_EVALUATED**，不能把 fetch 成功当成
Registry acceptance。仅该 Classic raw generation/download 已获得真实证明；其余 operations、
图片、Full/Lite、continuity/voice、P4、P6、human normal-speed review 均未被本轮验证。

### Verification, Review And Learning

Auth/Billing targeted native group 为 **107 passed**；exact staged Harness
`.agent/harness/runs/grok-live-auth-boundary-20261012-1/receipt.json` 全部七项 selected checks PASS，
Grok suite **285 passed, 2 legacy warnings**；提交前机械核验 fresh/complete/integrity/workspace stable。
clean authorized worktree 的 exact code commit-range 另绑定
`.agent/harness/runs/grok-live-auth-boundary-20261012-final-range/receipt.json`：七项 checks PASS，
Grok suite **285 passed, 2 legacy warnings**，机械核验 fresh/complete/integrity/cleanup。
三个 owned docs 的 staged delta 归 `.agent/harness/runs/grok-real-smoke-20261012-record-isolated/receipt.json`，
五项 selected checks 单独验证，
不把 docs receipt 冒充全仓代码或媒体质量证明。
Risk Gate `KIMI_REVIEW_NOT_REQUIRED` 的来源、snapshot 和 reasons 位于 staged receipt 同目录
`risk-gate.json`；read-only managed Kimi mapping `627d7823-79dc-4dfc-86c2-db5dd4f56afc`
及已核验 route receipt 只作 advisory，不冒充 final review、账单或媒体验收。

Foreign Canvas source/policy/docs、dirty/index work 保持原 ownership，没有 stage/commit 夹带。
首轮 docs snapshot PASS 后更新归档说明；main 的下一 staged 尝试遇到并发 writer 新 stage 的
Canvas path，scope guard 在运行 checks 前拒绝。只撤回本任务三个 paths 的暂存，foreign
index 保留，转至既有用户授权 clean worktree 封存并验证 exact docs snapshot。
记录阶段没有新增 Provider/media/network effects 或为了 record 补测试；Harness 仅完成 task
publication 所需 verification。RAG 在本次查询时为 fresh，record 更新后未主动 rebuild。
自动 `distill-ai-video-learning` 为 `no_candidate`：只有一个真实媒体 attempt，probe/frame/scene/
fetch recovery 都属于同一 evidence chain，没有 independent comparison 或已有相关 claim 的 material update。
保留 `architecture_implementation` / `ineligible` envelope，不建 placeholder 或 adoption。
