# SuperGrok Media Provider Implementation Plan

Date: 2026-10-12
Status: authorized direction; Parent self-reviewed; shared-file implementation waiting

**Goal:** 接入 Grok 图片和视频生成，优先消费 SuperGrok 订阅，真实执行前保护零额外现金边界。

**Spec:** [SuperGrok Media Provider](../specs/2026-10-12-supergrok-media-provider.md)。

**Current / Target Behavior:** 当前没有 Grok adapter，image 为 local-only，远端 video 是 monetary
paid lifecycle。目标是在原 ownership 下接入订阅认证、完整媒体 protocols 和明确 blocked 状态。

**Invariants:** 唯一 committer、exact identity、one-use permit、unknown 停止、无隐式付费 fallback、
历史 hash/replay、原 references/continuity/audio/QA 与 HyperFrames composition 均保持。

**Execution Order:** 用户要求另一任务先提交共享文件。当前只创建本 Plan、Spec 和 record；
后续写 existing source/policy/matrix/baseline 前重新核对 HEAD、dirty state 和 live ownership。
不创建 dedicated development worktree，不接管 foreign changes。

## File Structure And Responsibilities

- `production/grok_auth.py`：单一认证解析、有效期/rotation、safe private reference 和 account identity owner。
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

**Verification:** `python -m pytest -p no:cacheprovider tests/test_grok_auth.py tests/test_grok_subscription.py -q`。

### Milestone 2: Canonical Remote Effect Contracts

**Files:** 修改 `production/paid_provider.py` 与其既有 state-commit/reader/budget owners；
修改 `production/image.py`、image intent/candidate/activation/recovery mixins 和必要 schema admission；
新增 `tests/test_grok_subscription_lifecycle.py`、`tests/test_grok_remote_image_lifecycle.py`。

**Dependencies:** Milestone 1；foreign shared files 已提交且 ownership 可用。

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
当前仅已完成 protocol/code mapping 与这份 Plan，milestones 的实现和 live verification 未执行。
