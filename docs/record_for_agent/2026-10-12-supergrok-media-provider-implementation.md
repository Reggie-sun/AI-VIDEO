---
record_kind: architecture_implementation
topic_id: supergrok-subscription-media-provider
learning_eligibility: ineligible
---

# SuperGrok Media Provider Implementation Record

Date: 2026-10-12

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
