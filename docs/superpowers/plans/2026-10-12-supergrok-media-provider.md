# SuperGrok Media Provider Implementation Plan

## Live Subscription Follow-Up — 2026-10-12

用户要求真实 Grok 生成测试并已完成官方 OAuth。既有交付状态为历史证据；本单元先修复
official `accounts.x.ai/oauth2/device` 与 exact `user_code` complete URI，再在现有 billing owner
增加显式、注入式 included-only authority。Default reject guard 与 `quota` 的只读行为保持。
Authority 每次重开固定 billing / auto-topup GET：统一订阅池、finite current quota、零
on-demand cap / used / prepaid balance、官方 schema 的 disabled/no-rule 必须全部成立。
证据精确绑定 account/model/operation/period；失败不签零金额 preview，不提交、不重试。

Primary source 为 xAI `grok-build` commit `2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8`
的 `billing.rs` / `credit_bar.rs`：positive cap 才启用 PAYG；backend reports none 为 known disabled。
当前 authenticated catalog 的视频目录 404 与普通 `/models` 只有 LLM，不能冒称视频资格 PASS。
仅在 qualification 与 canonical creative/permit admission 全部成立后，允许最多一次 Classic
T2V、3s/480p/16:9、现金上限 0 的实验；known rejection/unknown 均停止，未产出则媒体 Gate
为 NOT_EVALUATED。不得为了 smoke 增设账户 fallback、裸 POST 或虚构 binding。

Owned files 为 `grok_auth.py` / `grok_billing.py` 及对应 tests、Grok guide、本 Plan 和 primary
record；foreign Canvas 源码/文档不修改。验证先 boundary tests，再 exact staged Harness，
最后按 Risk Gate 决定必要 independent review；真实 server observations 不等于媒体验收。

### Live Checkpoint Result

`e03737d` 已发布到 `main`；真实官方 OAuth 和 submit 前两条 fixed GET admission 完成。
Classic `grok-imagine-video` 的一次 canonical T2V 被接受并 fetched：3.042s、848×480、24fps、
无音轨，media POST=1。下载恢复针对同一 task、仅本次进程修复 fake-IP DNS，不更改 global
配置或 repeat POST。逐 Shot action 因 sealed standing posture 无法在裁切画面确认而
`NOT_EVALUATED`，本轮停止；canonical candidate/output validation、human acceptance 与其他
模型/模式仍未验证。actual raster 不是 exact16:9，未弱化既有 verifier。
exact identities、receipt 与新旧证据边界归
[Implementation Record](../../record_for_agent/2026-10-12-supergrok-media-provider-implementation.md#live-subscription-smoke-checkpoint--2026-10-12)。
下方 initial offline-only Status / Current Behavior 保留为原实施规划历史。

Date: 2026-10-12
Status: authorized implementation; Parent self-reviewed; offline-only evidence boundaries

**Goal:** 接入 Grok 图片和视频生成，优先消费 SuperGrok 订阅，真实执行前保护零额外现金边界。

**Spec:** [SuperGrok Media Provider](../specs/2026-10-12-supergrok-media-provider.md)。

**Current / Target Behavior:** 当前没有 Grok adapter，image 为 local-only，远端 video 是 monetary
paid lifecycle。目标是在原 ownership 下接入订阅认证、完整媒体 protocols 和明确 blocked 状态。

**Invariants:** 唯一 committer、exact identity、one-use permit、unknown 停止、无隐式付费 fallback、
历史 hash/replay、原 references/continuity/audio/QA 与 HyperFrames composition 均保持。

**Execution Order:** 后续“开workree实现”明确授权 dedicated worktree 并取代等待顺序。
在 `/home/reggie/vscode_folder/AI-VIDEO-supergrok-media`、branch
`codex/supergrok-media-provider-20261012` 从 `75849c7` 实现；不修改原工作区 foreign changes。

## File Structure And Responsibilities

- `production/grok_auth.py`：单一认证解析、有效期/rotation、safe private reference 和 account identity owner。
- `production/_grok_auth_lock.py`：同一 private item 的 Linux 跨进程 mutation serialization，不保存凭据。
- `production/grok_subscription.py`：只读订阅 evidence 与 exact included-only admission，消费原预算计数。
- `production/grok_profile.py`：精确 model/mode/origin/control/output profile，不拥有 selection。
- `production/grok.py`、`production/grok_download.py`：video wire/status/download adapter。
- `production/grok_image.py`：image wire/format conversion/provenance adapter。
- 既有 `paid_provider.py`、image model/reader、video service、state-commit mixins、Manifest schema：
  只增加必要的 subscription/image operation 和 lifecycle admission，持久 ownership 不迁移。
- 既有 compiler/Router：只有实际 capability/grammar seam 要求时修改，不为新名称机械增加分支。
- exact adapters/auth/subscription 的新 tests 与既有 service/legacy suites；policy、matrix、baseline
  只同步实际实现及证明边界，不复制本 Plan 为第二 check catalog。

上述新文件位于 `src/ai_video/production/`。现有 oversized `image.py` / `video.py` 不追加 wire
或 OAuth domain logic；叶模型/验证可拆到同 package，保留 public exports。

## Major Milestones

### Milestone 1: Subscription Authentication And Admission

**Files:** 新增 `grok_auth.py`、`grok_subscription.py`、`grok_profile.py`；新增
`tests/test_grok_auth.py`、`tests/test_grok_subscription.py`。

**Contract:** 官方 device-code；用户官方页面授权；exact private reference；token expiry/rotation
由认证 owner 管理；仅公开 fingerprint/metadata 进入 evidence。检查 exact media endpoint 的
included-only 边界，quota 观察缺失不当零用量；没有 service-side 扣费边界则明确阻断 live。

**Acceptance:** Fake transport 覆盖 eligible/ineligible、expired/revoked、rotation lost response、
missing quota、stale window、cross-account、overage-unknown，所有拒绝路径 generation POST=0。
认证并发在 lookup/HTTP 前返回 busy，跨进程锁异常退出后释放；symlink 不可提供 lock authority。

**Verification:** `python -m pytest -p no:cacheprovider tests/test_grok_auth.py tests/test_grok_subscription.py -q`。

### Milestone 2: Canonical Remote Effect Contracts

**Files:** 修改 `production/paid_provider.py` 与其既有 state-commit/reader/budget owners；
修改 `production/image.py`、image intent/candidate/activation/recovery mixins 和必要 schema admission；
新增 `tests/test_grok_subscription_lifecycle.py`、`tests/test_grok_remote_image_lifecycle.py`。

**Dependencies:** Milestone 1；authorized worktree 内 target ownership 明确。

**Contract:** Subscription binding 进入 exact preview、authorization、reservation、intent、permit
和 reopen；image 增加真实 remote operation、egress、outcome 与 provenance。
原 metered cash ledger 和 submit history 保留，不新增独立 Manifest writer。零金额只能来自
已验证 included-only 边界；旧 local-only evidence 不可用于 remote generation。

**Acceptance:** 经标准 loader/committer seam 完成 fake image/video effect；unknown 禁止重发；
legacy paid/local request、receipt hash 与 exact replay 保持。No local permit for remote media。

**Verification:** 新 lifecycle tests 加既有 `tests/test_production_paid_provider.py`、
`tests/test_production_paid_provider_state.py`、`tests/test_production_image.py`；具体 argv 以恢复时
存在的 test inventory 和 Harness policy 为准，不以裸 model parsing 构造 integration PASS。

### Milestone 3: Video Adapter Through Existing Orchestration

**Files:** 新增 `grok.py`、`grok_download.py`、`tests/test_production_grok.py`；
扩展 `tests/test_generation_provider_wiring.py`。既有 compiler/Router 仅做被实际 seam 证明必要的适配。

**Contract:** exact selected model/profile；已证明的 T2V/I2V/control；create request_id → status →
download；permit-inner authority recheck；unknown/invalid identity 不 retry。
模型缺 seed、fps、audio-disable、reference 或 hard-frame control 时返回 Unsupported，不能降级。

**Acceptance:** Registry injection、Planner/Router/compiler/service 全链 fake proof；重复调用不会
重复 POST；下载 identity/HTTPS/redirect/size 验证；required continuity/native audio 保持原约束。

**Verification:** `tests/test_production_grok.py`、`tests/test_generation_provider_wiring.py`，
以及 policy 选择的 Router/compiler/paid/remote-media suites。

### Milestone 4: Image Adapter And Provenance

**Files:** 新增 `grok_image.py`、`tests/test_production_grok_image.py`；扩展既有 image integration tests。

**Contract:** references exact Registry bytes/roles；control 不支持就拒绝；原 wire identity 和转换后
PNG identity 均保留；使用已安装 decoder 保尺寸 conversion，不能 resize/去水印。
Production image candidate、Registry/Manifest activation 仍经唯一 committer。

**Acceptance:** fake generation/edit 返回可验证 remote image candidate；wrong dimensions、invalid
format、excess references、lost response、cross-account、missing subscription evidence 均拒绝。

**Verification:** `tests/test_production_grok_image.py`、remote image lifecycle 与原 image replay/activation suites。

### Milestone 5: Delivery And Bounded Account Smoke

**Files:** 修改 `.agent/harness/policy.yaml`、`docs/agent-primary-contract-matrix.md`、
`docs/v0.2-runtime-baseline.md`；更新本 Plan 和本任务 session record。

**Contract:** complete offline tests/Harness，stable candidate Risk Gate，必要时一次受管 Kimi review。
用户登录且 admission 满足后，绑定 exact inputs 和最少有限 submit count；先 image，再 video。
视频落盘立即按项目规则执行 MCP gate，不以 smoke 或测试代签质量/成片验收。

**Acceptance:** owned implementation commit 已 push 到 `main`、remote SHA 已核验、fresh exact-range
receipt 可重开；账号/live 阻断明确报告。Required review 或 included-only admission 未通过时不声称启用。

**Verification:** `make harness-inspect`、exact staged/commit-range mandatory checks、
`make harness-receipt`；live OAuth、image、video 和 MCP evidence 分别记录。

## Self-Review And Current Checkpoint

Spec 每个契约均归属上述 milestones；两个媒体能力都在 scope 内。没有额外 dependencies、
frontend、Gateway、fallback、独立账本或 acceptance writer。用户所选共享文件顺序优先于实现。
Milestones 1–4 的实现已完成，canonical fake image activation/replay 与 video submit 已验证。
Milestone 5 的 actual evidence 归 exact staged/range Harness 与 managed review receipts，
publication 归 Git remote SHA；本 Plan 不复制 mutable completion ledger。candidate-8 完整
Harness 已通过，首次必要 Kimi review 触及输出上限且无 terminal report。登录、真实
subscription billing 与 media smoke 未执行；默认 included-only guard 保持 blocked。
完整 Production selection 为 3966 项；candidate-7 在 1800s 上限处处理约 98% 后超时，
并定位到旧 MRO owner assertion 未包含新增 remote image owner。保持旧 owners 的相对顺序，
显式补入 remote owner 与 method ownership 检查；没有删去断言。该 verification check 的
单轮有限窗口改为 2400s，argv、selection 和质量要求不变；保留 predecessor receipt，
重跑下一 exact staged candidate 及交付 exact range，不重置历史消费或假定 partial PASS。
PNG measurement 抽出 `image_bytes` 并保留 public imports；remote joins/activation proof 由叶模块
负责。账本 subscription count 不重置现金 reservations，旧缺省字段省略与 hash 保持。
