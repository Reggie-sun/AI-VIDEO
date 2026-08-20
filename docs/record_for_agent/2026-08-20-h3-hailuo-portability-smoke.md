# H3 To MiniMax-Hailuo-2.3 Portability Smoke Record

Date: 2026-08-20

## Purpose

本文记录 5 分钟 rough cut 前完成的 bounded、no-new-live-call H3 -> MiniMax-Hailuo-2.3 Provider portability smoke。目标是验证同一 Shot Router contract 能被两个 exact Provider/profile 正确消费，而不是启动新的 Provider generation、全面 benchmark 或生成一条新的 Hailuo continuity 成片。

本记录是 durable runtime note，不构成新的 remote/paid authorization。代码、测试、Harness receipt 与已测量 artifact 仍是 source of truth。

## Current Runtime Truth

- Repository/worktree：`/home/reggie/vscode_folder/AI-VIDEO-shot-router`。
- Branch：`agent/shot-router`。
- Checkpoint commit：`f0d4c75ecd2250d281f5aed848e58409b0b8a3ff` (`fix: preserve first-frame capability routing`)；local-only，未 push、merge 或 release。
- 本轮没有 Provider/network call、credential read、permit mint、Manifest activation 或新媒体生成。
- Smoke 复用历史 Hailuo fetched MP4；它没有产生新的 `H3 -> Hailuo` 视频 artifact。所谓通过，指 offline request/binding/capability transformation 通过，不是新的 live continuity quality proof。
- Provider selection 仍由 external production policy 预选 exact provider/profile；Router 不 ranking、不 fallback、不自动切换 Provider。

## Session Work And Decisions

### Router capability fix

真实 H3 与 Hailuo I2V capability 都声明 `required_first_frame=True`、`max_reference_count=0`。Router 旧逻辑把所有 required roles 都计入 reference count，因而误阻断合法 I2V first-frame binding。

`src/ai_video/production/shot_router.py` 现在只统计 `role == "reference"`，再独立校验 `first_frame` requirement。Regression test 直接读取 `ComfyUIVideoProvider.capabilities()` 与 `MiniMaxHailuoVideoProvider.capabilities()`，并显式断言 capability identity、first-frame requirement、zero reference count、terminal input identity 与 no-credential-read boundary。

### Continuity matrix

| Continuity | H3 control | MiniMax-Hailuo-2.3 | Result |
| --- | --- | --- | --- |
| `exact_terminal` | `minimax-h3-fl2va-local-v1`, I2V, `first_frame` | `minimax-hailuo-2.3-v1-i2v-768p-6s-first_frame`, I2V, `first_frame` | PASS；两者都只绑定 exact terminal bytes，terminal SHA `2dd12cac1381fd2cbc35067fc1d6f76b4e190135f5edc535172d94270f9ff27b` |
| `reference` | unchanged | Hailuo I2V/T2V 均 typed `BLOCKED_CAPABILITY`，需要 `reference_to_video` | BLOCKED AS DESIGNED；未降级到 I2V/T2V，未切换 Provider |
| identity-free `none` | unchanged | exact Hailuo T2V capability 仅在无 identity/visual anchor 时 selected | PASS；重要角色/anchor 分支仍 typed blocked，不静默丢输入 |

为适配历史 evidence 的 authoring 状态，offline smoke 使用了临时、未持久化的 `generated_video` Shot revision；历史 activated Shot 当时是 `STATIC_IMAGE`，直接复用会正确返回 strategy block。该临时 revision 没有写入 Manifest、Registry、Dependency Graph 或 state writer。

## Verification And Evidence

### Code and tests

- Changed files：`src/ai_video/production/shot_router.py`、`tests/test_production_shot_router.py`。
- Focused Provider/Router/Dependency suite：`293 passed`。
- Composition/HyperFrames suite：`264 passed, 3 skipped`。
- Independent native reviewer：`accept`，无 blocking issue 或 non-blocking concern。
- Fresh Harness：`206 passed`；task Architecture Gate `PASS`，只有既存 oversized `shot_router.py` 增长 1 LOC 的 warning。
- Receipt：`.agent/harness/runs/20260820T065204262207Z/receipt.json`。
- Receipt verification：`artifact_integrity=true`、`closure_eligible=true`、`fresh=true`、`passed=true`、`policy_matches=true`、`snapshot_matches=true`、`workspace_cleanup_confirmed=true`。

### Historical Hailuo fetched MP4s

以下 evidence 位于 sibling `AI-VIDEO` main run，均为历史 fetched output，不是本次 smoke 新生成：

- `runs/hailuo23-cloud-live-20260818T154959Z/exports/shot-a-library-interior.mp4`：SHA-256 `f87819c68965010f0a55fb3751a0c2ac27b2f8bc4fe8fde6d776c209a3f10507`。
- `runs/hailuo23-library_exterior-cloud-live-20260818T155419Z/exports/shot-b-library-exterior.mp4`：SHA-256 `881a0e3b8cc79e92452532ea5b3a8919c63d449616fd90e6de30b827d0c9b8c4`。
- `runs/hailuo23-archive_clue-cloud-live-20260818T155425Z/exports/shot-c-archive-clue.mp4`：SHA-256 `4f845788952a3a1a440b4928256097187c9673e524b48fee5274e47b9de10009`。

三者 `ffprobe` 均为 H.264 High、`1366x768`、`yuv420p`、24 fps、141 frames、5.875 seconds、无 audio stream；这与 Hailuo capability `native_audio=false` 一致。

### Existing composition seam

既有 compatibility run 已证明上述 generated MP4 可沿单一 `CompositionSpec -> ResolvedTimeline -> HyperFrames` seam 消费：

- Timeline：`runs/generated-video-compat-20260819-001/state/render/timelines/ec85df9d417ca09b1a883a731dbd878042f793c9639a4479c6efa1a2a3a4460a.json`。
- Source receipt：`runs/generated-video-compat-20260819-001/state/render/source-receipts/95644ff48242b8d664a30f08210ff96b766f203298760ab0e01306ae4089ee17.json`。
- Render receipt：`runs/generated-video-compat-20260819-001/state/render/render-receipts/2020af76a7a63122a6a95d157cade65efec6a736311f6d0d08e6a51c9550649d.json`。
- Active state：`runs/generated-video-compat-20260819-001/state/render/states/b87fe890e0c70b3d472172973210082d4d47bfbff3b0516f14dc4ab8601054d0.json`。
- Final composition：`runs/generated-video-compat-20260819-001/state/render/outputs/5ad2f02d6fbfaa82b860f307a53afa99e38d7eefdb429cf79a562becbcd1e647.mp4`，SHA-256 `5ad2f02d6fbfaa82b860f307a53afa99e38d7eefdb429cf79a562becbcd1e647`。

Final composition 为 H.264 `1366x768`、24 fps、423 frames、17.625 seconds，并含 AAC LC stereo 48 kHz；source Hailuo MP4 的静音不会绕过 P4 audio mixer。历史 fetched source 不等于本轮 activated、review-accepted 或 final delivery truth。

### H3 control artifact

既有 P7-reference H3 control artifact：`runs/h3-shot-router-quality-p7-20260820-v1/evidence/alice-cafe-exact-terminal.mp4`，SHA-256 `05c00691a7a04d8e0864f018073ea746ccba3e0cba38aa0c9f651180d30bae9e`。其 exact-terminal continuity 仍成立；本记录不修改 H3 sealed technical profile 或 historical hashes。

### MiniMax runner capture

脱敏 MiniMax/sub-agent capture：`/home/reggie/.codex/session-diagnostics/minimax/01a01dd1-dbda-7730-bb6f-d082de2df0a1-c64c261861bdfa4e.md`。

该报告记录了 1 个 explorer invocation、2 个 writer retry-shaped invocations，且没有结构化 MiniMax terminal result；它只作为 runner/skill optimization evidence，不证明应用代码正确性。报告没有复制 raw prompt、exact command、environment、credential 或 full Provider output。

## Assessment

Portability contract 已具备进入 rough cut 的流程条件：`exact_terminal` 可在 H3 与 Hailuo exact I2V capability 间保持相同 terminal binding；不支持的 `reference` 明确 blocked；identity-free `none` 只选择 exact T2V；重要 identity/visual anchor 不会被静默丢弃。

但本轮不能被描述为“生成了 Hailuo smoke 视频”或“Hailuo continuity live quality 已验收”。本轮没有新 Hailuo call，也没有新的 H3 -> Hailuo video artifact；可播放的视频是历史 H3 control、历史 Hailuo fetched MP4 与历史 composition output。

## Remaining Risks Or Next Work

- Hailuo 尚无 fresh live continuity proof；`reference`/R2V capability 仍缺失。
- 历史 Hailuo source MP4 没有 audio stream；最终音频仍由 P4 composition/audio contract 负责。
- Rough cut 继续以 H3 quality lane 为 control，Hailuo 只使用其已验证的 exact I2V/T2V capability；不要把 Hailuo fetched source 当作新生成或 quality acceptance。
- 不做 Seedance 测试，不读取 credential，不 mint permit，不扩大为 Provider benchmark。

## Agent Guardrails

- 不修改 H3 sealed technical profile、Manifest/schema、Registry layout、P5 dependency owner、state writer、CLI 或 canonical timeline。
- 不把 offline routing result、历史 fetched artifact、composition compatibility proof 或 successful fetch 说成 activated/review-accepted/final delivery truth。
- 任何新的 Hailuo/Seedance remote or paid submit 都需要新的明确 task authorization，并重新执行 Paid Provider Gate、budget、egress、secret、durable intent 与 one-use permit。
- 后续 Agent 应先读取本记录、`docs/v0.2-runtime-baseline.md`、`docs/agent-primary-contract-matrix.md` 与 `.agent/harness/policy.yaml`，再决定是否进入 rough cut 或另开 Provider/quality slice。
