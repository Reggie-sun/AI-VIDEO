# Caption Quality Gate Implementation Plan Record

Date: 2026-08-28

## Learning Adoption Supersession — 2026-08-29

下方 `Automatic Learning Evaluation` 保存的 pending v1/v2、未确认与停止 adoption 状态现在只作为
历史。Qingyan V9 exact evidence 后形成的 pending v3 已由用户按 exact candidate identity 确认，并
完成 bounded Gate adoption：

- confirmed candidate commit：`0d01a97f7c340baf350c6681274c0dde9fce5b96`；
- confirmed candidate bytes SHA-256：
  `f845f5d1aa589527f6987156cd07f79769220a75c16e372aabca7318574ceb17`；
- canonical target：`.agent/context/control-plane-playbook.md` 的
  `HyperFrames Caption Source Readiness`；
- adoption commit：`9fa65248647bcf5ae07ca15edafeb82b0e69d9bd`；
- active-claim commit：`4c0a6dc1a1ceae0c124932d97b44245ec5f1bbad`；
- adoption Harness receipt：
  `.agent/harness/runs/hyperframes-caption-readiness-adoption-20260829/receipt.json`，已验证
  complete、fresh、snapshot-matching，Architecture Gate PASS、Learning Skill `27 passed`、
  Harness `204 passed`；
- target-owner focused evidence：unsupported-font/no-staging regression PASS；pinned
  `hyperframes@0.7.103` + Chrome `152.0.7928.2` exact Production renderer Gate PASS。

Active v3 只采用“HyperFrames version change 必须同步 exact bundled/generic font table、preflight
与两条 executable seams”的维护规则。它不改变 Runtime、`ResolvedTimeline`、renderer selection、
`ProductionStateCommitter`、CAPTION P6、Final Acceptance 或 Provider authorization，也不授权媒体、
Product state、push 或 release effect。

## Final Acceptance Supersession — 2026-08-29

下方 `Exact Final-Media Re-test — 2026-08-29` 对 V4 的 `SOURCE_INTEGRITY FAIL`、CAPTION overall
`NOT_EVALUATED` 与缺少 canonical render/policy 的 blocker，仍是 V4 exact bytes 和旧
`production/` root 的真实历史证据，但不再是当前 Qingyan accepted candidate 状态。

新的 claim-safe / continuity-safe V9 已进入独立 canonical Production root，通过 exact HyperFrames
render、project-local `video-analysis`、全解码、逐秒与 cue/gap visual evidence，并由
`ProductionStateCommitter` 持久化 TECHNICAL / LAYOUT / CAPTION / SEMANTIC 四层 PASS 与 fresh
`Final Acceptance`。Exact V9 SHA-256 为
`9f3534ce93084a4f9b5e6b70b3d60e0599302202f73ef28d92bc762db1e78bd2`；详见
`docs/record_for_agent/2026-08-29-qingyan-caption-final-acceptance.md`。

这不反向升级 V4，也不证明 publication、claim substantiation、市场效果或用户主观最终验收；本记录
关于 Caption Gate implementation、font contract 与 historical V4 blocker 的技术事实继续有效。

## Current Status — Implementation Supersedes Plan-Only State

本记录最初保存 plan checkpoint；该状态现已被实现提交 `31f365a`
(`feat: add caption final-media quality gate`) supersede。下方保留 plan-time reasoning 作为历史，
但“尚未实现”的陈述不再代表 current runtime truth。

实现结果：

- `QaLayer.CAPTION`、六组 requirement、per-track policy、exact evidence context 与 fail-closed
  adjudication 已进入 Product Runtime。
- Manifest `2.15` 与 artifact schema `2.1` 已实现；historical `2.0` serialization/hash behavior
  保持兼容。
- caption P6 request/permit/evidence/receipt、zero-write replay、unknown-attempt recovery 与 strict
  reopen 已由既有 `ProductionStateCommitter` lifecycle 接管，没有新增 Manifest writer。
- caption-aware repair outcome 与 Final Acceptance 会重载 exact project/request/context/evidence，
  重新运行同一 adjudicator；tamper、identity drift、coverage gap、unsupported evaluator 或 verdict
  mismatch 均 fail closed，且 rejection path 不写 Manifest/RepairOutcome artifact。
- Ecommerce canonical order 已固定为 CAPTION P6 -> Universal Gate -> Domain Gate -> Final
  Acceptance；Base AI Comic 与 Ecommerce E2E caller closure 均有 executable coverage。
- 为保持 module boundary，caption model validators 与 active-review reader 分别提取到
  `_caption_review_models.py`、`_review_project_reader.py`；task-delta Architecture Gate 最终 PASS。

实现完成时仍未证明任何真实媒体的字幕感知质量；该历史边界已被下方
`Real Validation Update — 2026-08-28` 部分更新。本轮已执行 bounded local render、逐帧字幕
检查、project-local `video-analysis`、ASR 与人工 frame-sheet inspection，但没有得到 Production
CAPTION P6 PASS 或 empirical Final Acceptance。

## Font Contract Fix Update — 2026-08-29

下方 `Production Renderer Gate — FAIL` 保存的是 2026-08-28 修复前的真实失败。其“需要另行
授权修复”与“任意 selected custom font 都属于同一种 source/font contract 不兼容”的 current-facing
结论，现已被用户后续“修复”授权、代码提交 `0ed672e` 和新的 exact Production render 证据取代。
历史 FAIL artifact、错误码与 lint finding 仍然有效，但 root cause 已进一步收敛：fixture 使用了
不存在于 pinned renderer canonical bundled-family table 的虚构 `Fixture Sans`，同时 Product Runtime
此前没有在 staging 前约束这一 renderer contract。

### Runtime Fix

`src/ai_video/production/_hyperframes_source.py::_caption_style_css()` 现在只接受
`hyperframes@0.7.103` 同名 bundled canonical font family 与 renderer 支持的 CSS generic family，比较时
使用 `casefold()`；任意未知 family、alias-substituted family 或虚构 fixture family 在创建
`staging_root` 前以 `ErrorCode.RENDERER_SOURCE_INVALID` fail closed。没有引入 `@font-face local()`、
silent fallback、禁用 lint、第二 renderer path 或新的 Manifest writer。

Production test fixtures 改为真实 canonical family：默认 `Inter`，serif arm 使用 `EB Garamond`。
`docs/agent-primary-contract-matrix.md` 同步把 `_hyperframes_source.py` 纳入 P3 owner，并记录
unsupported/alias-substituted font 的禁止旁路。实现 commit 中 exact source、test 与 contract-matrix
bytes SHA-256 分别为：

- `src/ai_video/production/_hyperframes_source.py`：
  `cceb6cb88219204a8c5bf674e0357a40b2d97d63eeb434d8e11f19c1637fdde7`
- `tests/test_production_hyperframes.py`：
  `3f674ecc96a44a6815aca558d94308ca51a63ea6fd436cc577d1bc5fd827ddcb`
- `docs/agent-primary-contract-matrix.md`：
  `42b93365191256ad59bcead88f0d91162e93b860a1201e8625f1e551ce0fa405`

### TDD And Independent Review

- 原 Production renderer gate 先稳定复现 RED：HyperFrames lint
  `font_family_without_font_face: fixture sans`。
- 新 public regression 在实现前 RED：`materialize_hyperframes_source()` 对未知 family 没有抛错。
- 实现后 regression GREEN，并断言 typed `RENDERER_SOURCE_INVALID` 与 `staging_root` 不存在。
- Mutation 临时移除 runtime allowlist check 后，regression 再次以 `DID NOT RAISE` RED；恢复实现后
  `1 passed`，证明测试实际覆盖新 boundary。
- `reviewer_high` 首轮拒绝仅替换 fixture 的 workaround；加入 runtime preflight 后要求 public seam 与
  effect-before-validation assertion；补齐后最终 verdict 为 `accept`，无 blocking 或 non-blocking
  concern。

### Exact Production Render — Engineering PASS

新的 bounded local evidence root：

`runs/caption-quality-gate-font-fixture-fix-20260828-v1/`

Production fixture 使用 `Inter`，通过同一个 source materialization、lint、check、render、output
verification、durable activation、audio 与 frame-boundary gate。Exact evidence：

- final MP4：`media/production-caption-inter.mp4`，SHA-256
  `e3b319bd2ed6d47ce382a34bef97edd724ddb3a49d40f301e878853e21709ab4`；
  `2.022s`、H.264 `1280x720`、`24fps`，含 AAC audio。
- exact source：`production-source/index.html`，SHA-256
  `dd5c7a7c0056c125a24e9cb10bb704244011b9bdc1fe3f5e8e1fea90b026c01a`。
- test Manifest：`state/manifest.json`，SHA-256
  `5477ad6e0e79ff4ed343daebe6fd8e293d6ce14f3d8bc7bc8508400ad145c671`；
  attempt `p4-production-render` 为 `succeeded`，但这是 P4 test fixture lifecycle，不是 CAPTION P6。
- exact caption half-open intervals 为 `[0,12)` 与 `[13,24)`；safe-area crop 的 frame
  `0/11/13/23` 检测到字幕，`12/24` 无字幕。`renderer-evidence/caption-frames.json` SHA-256
  `a241daac5c5a326de70adfed93270b0b265c4267eb8c98d40db3d804103ac7f1`。
- audio measurement SHA-256
  `b184d9b08a964cee576f29f5765b2987cc47a209ba5344a330eae452216f093d`；
  network audit SHA-256
  `3de27d39c8f297f4af92f80617d96b0bb1d57617100a2c12eab6abaed4ae7995`，namespace 只有 `lo`。
- project-local `video-analysis video_review` 绑定 exact MP4，报告 `96/96` unique sampled frames、
  audio present、`issues=[]`；这是 raw media evidence，不是 Production verdict。
- consolidated `validation-summary.json` SHA-256
  `4174a7bd3debece5781a675583fa5869057aa3fe1bfc7097bc4861efa6cc539e`。

Executable verification：

- exact Production renderer gate：`1 passed in 8.58s`。
- `tests/test_production_hyperframes.py`：`197 passed, 3 skipped in 43.97s`。
- extended HyperFrames/composition/captions/voice/Base E2E：
  `332 passed, 3 skipped in 172.11s`。
- exact commit-range Harness `ad7ce081..0ed672e`：Architecture Gate `PASS`、Harness
  `204 passed`、Production contract `2900 passed, 3 skipped, 1225 deselected`、CLI/config
  `13 passed`；`production_composition_audio_tests` 被已通过的 `production_contract_tests` 完整覆盖。
- fresh receipt：`.agent/harness/runs/caption-font-contract-fix-20260828/receipt.json`；
  `verify-receipt` 返回 `passed=true`、`fresh=true`、`fresh_for_snapshot=true`、
  `scope_paths_match=true`、`complete_completion_proof=true`、`snapshot_matches=true`、
  `workspace_cleanup_confirmed=true` 与 `workspace_stable_confirmed=true`。
- `python -m ruff` 未执行，因为当前 Python environment 没有 `ruff` module；policy-selected
  Harness checks 与上述 executable suites 均实际通过。

### Proof Boundary

该修复证明的是当前 pinned local runtime 中，canonical `Inter` Production source 能通过 P3/P4 exact
renderer gate，且未知字体在 staging 前 fail closed。它不证明 custom content-addressed font asset、
跨主机字体一致性、中文 glyph coverage、caption semantic correctness、感知可读性、Qingyan V4
canonical identity、CAPTION P6 或 Final Acceptance。Qingyan V4 的 Production CAPTION Gate 仍为
`NOT_EVALUATED`；本轮没有 Provider/paid call、外网访问、CAPTION P6 mutation、push 或 release。

## Exact Final-Media Re-test — 2026-08-29

用户再次要求“真实成片测试”后，本轮对同一 exact Qingyan V4 review-only MP4 重新执行 full decode、
project-local `video-analysis`、中文 ASR、10 个 ASS cue midpoint inspection、9 个 cue-gap inspection，
并实际调用 canonical `ProductionStateCommitter.current_final_media_target()` Gate entry。没有重新生成或
修改 MP4，没有 Provider/paid/network call，也没有写 Manifest、P6 或 Final Acceptance state。

Exact artifact 保持不变：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/final/qingyan-seedance2-fast-image-cards-caption-repaired-v4-28s-review-only.mp4`

- SHA-256：`087497ae1b4be12b260899706c19698c8d7d88635708528a6b8cf0d1fd7ac4e1`
- `12,909,584` bytes、`28.065s`、H.264 `720x1280`、`24fps`、`673` decoded frames
- AAC stereo `44100Hz`

新的 local evidence root：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/caption-quality-gate-retest-20260829/`

- `validation-summary.json` SHA-256：
  `f780edfedd57168cedf6ffd6a8e262bb13f29a0708dd75a6e4cf034bf52fc977`
- `cue-midpoints.png` SHA-256：
  `9b1ddb556c658cfb7410b378d3b028b1e1766b34fc86d9305d5176f688f833a5`；
  10 个 authored ASS cue 的 midpoint 均可见、可读。
- `gap-samples.png` SHA-256：
  `6cd421c9642afe4ee137fd1f54f386088887c81642c4e4db137fbc241281b175`；
  9 个 sampled cue gap 均无 authored subtitle layer，product/card text 仍按画面存在。
- `video-analysis video_review`：19 frames extracted、`1236/1236` unique sampled frames、audio
  present；唯一 `low_resolution` issue 来自通用 landscape-oriented baseline，不构成当前 accepted
  `720x1280` portrait caption failure。
- Chinese ASR speech regions 为 `0.0–2.88s`、`2.88–7.64s`、`21.12–24.88s` 与
  `25.88–28.16s`；大体覆盖 authored cue regions，但 `黏衣`、`长辈递来`、`青颜`、`抑汗净味`
  等词出现替换，因此不能独立签发 `AUDIO_SEMANTIC_SYNC PASS`。

Canonical Gate entry 实际返回：

`production_state_invalid: Current render state is required.`

阻断发生在 evaluator/P6 effect 前。Current Manifest 仍为 schema `2.8` revision `21`，
`active_render_state=null`、`active_qa_policy=null`；registered canonical
`production/assets/files/caption-track-1.json` 仍是英文 `Hello/world`，与中文 `captions.ass` 和 exact
V4 bytes 不同。

Requirement-level Production verdict 未改变：

- `SOURCE_INTEGRITY`: `FAIL`
- `TIMING_CONTRACT`: `NOT_EVALUATED`
- `RENDER_COMPLETENESS`: `NOT_EVALUATED`（10/10 midpoint sampled visible，但不是 whole-render
  canonical coverage）
- `LAYOUT_READABILITY`: `NOT_EVALUATED`（sampled visual readable，但无 authorized whole-render
  evaluator/per-track policy binding）
- `AUDIO_SEMANTIC_SYNC`: `NOT_EVALUATED`
- `UNINTENDED_TEXT`: `NOT_EVALUATED`（gap samples clean，但缺 whole-render OCR 与 approved
  non-caption text roster）

CAPTION Gate overall 继续为 `NOT_EVALUATED`。此外卡片中的 `15%`、`14天`、`96.67%`、`93.33%`
等 claims 尚未获得 substantiation，Domain Gate 的 `CLAIM_SUBSTANTIATION` 同样为
`NOT_EVALUATED`；Final Acceptance 未记录。该复测强化了 raw sampled visual evidence，但没有改变
canonical identity blocker，也不把 `PASS_FOR_LOCAL_REVIEW_ONLY` 升级为 Production PASS。

## Real Validation Update — 2026-08-28

本轮按用户“真实验证”请求执行了不含 Provider submit、paid call、外网访问或 Production state
mutation 的 bounded empirical validation。Exact evidence root：

`runs/caption-quality-gate-real-validation-20260828-v1/`

该目录中的 `validation-summary.json` SHA-256 为
`f4d09142a8dc636f7e23f9a50c5c93eec6085a2ea5cb59236ffe73f71a09247d`。

### Pinned Raw Renderer Capability — PASS

固定本仓库 `hyperframes@0.7.103`、Chrome Headless Shell `152.0.7928.2`、local audio 与
generic `sans-serif` source，运行 raw renderer capability gate：

`tests/test_production_hyperframes.py::test_p4_raw_renderer_capability_gate_accepts_local_audio_and_frame_caption`

结果为 `1 passed in 8.55s`。输出 MP4：

`runs/caption-quality-gate-real-validation-20260828-v1/media/raw-p4-caption-capability.mp4`

- exact bytes SHA-256：`5e9278b39c3fa52adfb2664423a35aadbe05022ca404385dd6aeb0a9a6df129f`
- media probe：`2.022s`、H.264 `320x180`、`30fps`、`60` frames、AAC stereo `48000Hz`
- caption half-open frame contract `[15,45)`：frame `14` absent、`15` present、`44` present、
  `45` absent
- project-local `video-analysis video_review`：`96/96` unique sampled frames，检测到 audio；仅返回
  generic low-resolution observation，不构成 caption-specific failure
- network isolation audit：namespace 中只有 `lo`

这证明当前固定 renderer/browser/local runtime 能生成带音频和按 exact frame interval 显示字幕的
MP4；它不证明 Production source materialization、CAPTION P6 或商业成片质量通过。

### Production Renderer Gate — FAIL

同一固定 renderer/browser 下运行：

`tests/test_production_hyperframes.py::test_p4_production_renderer_gate_renders_resolved_audio_and_captions`

Production render 在 HyperFrames `lint` 阶段 fail closed，未产出 MP4、未激活 render：

- failed source：
  `runs/caption-quality-gate-real-validation-20260828-v1/production-failure/index.html`
  (`f721aa805e6a6c034cded08fa6369c18c41252b2ee898b66bfcff916ec0b6dbd`)
- failed Manifest：
  `runs/caption-quality-gate-real-validation-20260828-v1/production-failure/manifest.json`
  (`d6a3a351cdffff499d4012bf303ea6201df5da1ca77289802cca102b310f4407`)
- lifecycle evidence：attempt `p4-production-render`、status `failed`、
  `render_phase=lint`、`error_code=renderer_source_invalid`
- exact renderer finding：`font_family_without_font_face`；
  `Font family used without @font-face declaration: fixture sans.`

Root cause boundary：`_caption_style_css()` 会把 selected custom `font_family` 写入 Production
source；`hyperframes.py::_parse_source_document()` 同时把 `@font-face` 视为 forbidden external
style/font surface，而固定 HyperFrames 对 non-auto-resolved font 要求 `@font-face`。因此当前
custom-font Production source contract 与 selected renderer lint contract 不兼容。Raw generic-font arm
PASS、Production `Fixture Sans` arm FAIL，已把本轮 blocker 隔离到 source/font contract，而不是
renderer binary、browser、local audio 或 network namespace。

本轮仅验证并记录 blocker，没有修改 Product Runtime。后续若获单独授权，最小修复应由既有
HyperFrames source/validation owner 处理，并增加真实 renderer regression test；不得以静默字体
fallback、禁用 lint 或第二条 render path 绕过。

### Qingyan V4 Review-Only Final Media — NOT_EVALUATED

对现有 review-only 成片
`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/final/qingyan-seedance2-fast-image-cards-caption-repaired-v4-28s-review-only.mp4`
执行 exact-byte probe、project-local `video-analysis video_review`、`video_transcribe` 与 V4-specific
frame-sheet inspection：

- MP4 SHA-256：`087497ae1b4be12b260899706c19698c8d7d88635708528a6b8cf0d1fd7ac4e1`
- media probe：`28.065s`、`720x1280`、`24fps`、AAC audio
- 人工抽查可读到 `出汗黏衣`、`靠近也不自在`、`长辈递来这瓶`、`喷一下`、`清爽舒适`、
  `近距离`、`更从容`
- ASR 检出主要 speech regions，但存在词汇替换，不能单独证明 audio-semantic PASS
- review-only `captions.ass` 包含 10 个中文 cues，SHA-256
  `f8433a76183d552af4fd9a288f120a6adf018be1b50e45a74026a97742bf3f40`

该 run 的 current Production Manifest 是 schema `2.8`，不存在可由
`ProductionStateCommitter.current_final_media_target()` 解析的 active render；其 registered canonical
`caption-track-1.json` 还是英文 fixture (`Hello` / `world`)，与 review-only 中文 ASS 不同。因此 exact
V4 MP4 无法绑定 Manifest `2.15`、canonical `CaptionTrack`、`ResolvedTimeline` 与 active final-media
identity。

Requirement-level verdict：

- `SOURCE_INTEGRITY`: `FAIL` — review-only Chinese ASS 不是当前 canonical active CaptionTrack/render
- `TIMING_CONTRACT`: `NOT_EVALUATED`
- `RENDER_COMPLETENESS`: `NOT_EVALUATED`
- `LAYOUT_READABILITY`: `NOT_EVALUATED`
- `AUDIO_SEMANTIC_SYNC`: `NOT_EVALUATED`
- `UNINTENDED_TEXT`: `NOT_EVALUATED`

按 fail-closed aggregation，Production CAPTION Gate overall 为 `NOT_EVALUATED`，不是 PASS。抽帧可读、
ASR 有输出或 `video-analysis` 成功均不能替代 canonical identity、whole-render coverage、P6 receipt 或
Final Acceptance。

### Real-Validation Record Verification And Publication State

- Exact task commit range 从 `3d6844c` 后开始，只包含本记录与对应 Learning Claim；Harness receipt：
  `.agent/harness/runs/caption-real-validation-task-only-final-20260828/receipt.json`。
- Mandatory checks：documentation contract、policy audit、product-runtime Skill boundary `2 passed`、
  task-delta Architecture Gate `PASS`、experience-learning Skill tests `7 passed`。
- `verify-receipt` 必须同时返回 `passed=true`、`fresh=true`、`fresh_for_snapshot=true`、
  `scope_paths_match=true`、`complete_completion_proof=true`、`snapshot_matches=true`、
  `workspace_cleanup_confirmed=true` 与 `workspace_stable_confirmed=true`，否则本记录不声称完成。
- Publication state：记录与 pending candidate 仅 commit 到 local `main`；未 push、未 release。
- 现有 unrelated `.codex/config.toml` dirty state、H3 record staged state、`artifacts/` 与两份
  2026-08-27 untracked plan/spec 保持原 ownership，未纳入本轮 commits。

## Purpose

本文记录字幕专项质量 Gate 的 accepted implementation plan checkpoint。计划基于当前代码、
P6/Final Acceptance ownership、project memory 检索、成熟字幕 QC prior art 与独立
`reviewer_xhigh` 审查收敛。

本记录只证明实现边界、迁移顺序与验证契约已经形成可执行计划；它不证明字幕 Gate 已实现、
Manifest 已迁移、任何媒体已通过字幕质量验收，也不构成 Provider、media generation、P6 或
Final Acceptance authorization。

完整计划位于：

`docs/superpowers/plans/2026-08-28-ai-video-caption-quality-gate.md`

## Accepted Architecture Direction

计划将字幕专项 Gate 纳入既有 P6 review lifecycle，而不是新增第二个 top-level coordinator、
Manifest writer 或 Final Acceptance owner：

```text
CaptionTrack
  -> ResolvedTimeline.caption_cues
  -> HyperFrames exact final render bytes
  -> QaLayer.CAPTION evidence and adjudication
  -> existing Universal Quality Gate
  -> existing Domain Gate
  -> ProductionStateCommitter Final Acceptance
```

主要 contract decision：

1. 新增 `QaLayer.CAPTION`，由新的 cohesive caption-quality module 独占 requirement-level
   adjudication；`review.py` 只负责委派。
2. 保持 `CaptionTrack` 为 authored caption truth、`ResolvedTimeline` 为唯一 timing owner、
   HyperFrames 为 selected renderer、`ProductionStateCommitter` 为唯一 durable lifecycle owner。
3. 采用六个 finding groups：`SOURCE_INTEGRITY`、`TIMING_CONTRACT`、
   `RENDER_COMPLETENESS`、`LAYOUT_READABILITY`、`AUDIO_SEMANTIC_SYNC` 与
   `UNINTENDED_TEXT`。
4. 每个 required finding 独立输出 `PASS | FAIL | NOT_EVALUATED`；只有全部 required
   findings 为 `PASS` 才能聚合通过，且 `FAIL` 优先于缺证据产生的 `NOT_EVALUATED`。
5. `UNINTENDED_TEXT` 必须绑定 whole-render temporal/spatial coverage；只检查预期 cue 窗口
   不能证明没有 double-burn、残留字幕或其他非预期文字。
6. 新 caption-aware policy 使用 per-track language/delivery policy；不使用一个未经选择的
   universal CPS/CPL threshold 覆盖中文、英文、双语与 kinetic typography。
7. 新 policy 下 caption-specific overflow/readability 由 `CAPTION` 独占；historical policy
   仍可按旧 `LAYOUT` payload reopen，避免两个 active verdict owner。
8. caller-supplied `CAPTION PASS` 不得进入 authoritative closure；canonical coordinator 必须
   通过 private trusted adapter 从 exact active project/render/timeline/context/evidence 重建并判定。

## Schema And Compatibility Decision

计划明确采用 Manifest `2.15`，而不是把新增 caption state 当作无版本的 additive field：

- 新增 `manifest_schema.py` 作为 named Manifest capability/version set 的单一 owner。
- `2.15` 明确继承全部 `2.14` capabilities，并增加 caption-aware policy/context/receipt
  capability。
- Artifact schema 迁移至 `2.1`；`FinalAcceptanceReceipt` 与 `RepairOutcomeReceipt` 同步支持
  `2.1`。
- standard reader 必须拒绝 implicit migration、downgrade 与 mixed state；即使没有 CAPTION
  receipt，只要 Manifest `2.14` 指向 caption-aware `QaPolicy 2.1`，也必须 fail closed。
- strict reopen 必须重载 exact project/request/context/evidence，调用同一个 caption adjudicator
  重新计算 verdict，并要求 recomputed verdict 与 stored receipt verdict 完全一致。

以上为 plan-time migration decision；实现提交 `31f365a` 已按该 decision 落地，因此
“当前 runtime schema 未改变”的旧状态已被 supersede。

## Plan Review History

首次 `reviewer_xhigh` 审查给出 `reject`，指出四个 blocking issues：

1. 缺少 Manifest/container version bump。
2. caller-supplied `CAPTION PASS` 存在 bypass 风险。
3. project/Final Acceptance 的 request/context strict reopen 不完整。
4. cue-only coverage 无法证明不存在 unintended text。

计划随后加入 Manifest `2.15` migration、private trusted P6 adapter、完整 strict reopen 与
whole-render unintended-text coverage。第二轮审查提出的 Harness mapping、Manifest `2.14`
policy-only mixed-state rejection 与 verdict recomputation concerns 也已补齐。

最终 scoped re-review verdict 为 `accept`，无 blocking issues 或 non-blocking concerns。

## Plan Checkpoint Verification And Publication State

- Plan commit: `5f10004` (`docs: plan caption quality gate`)。
- Exact base commit: `58f16634a4ef0d574d18c9707fedc8d430013230`。
- Exact commit-range Harness receipt:
  `.agent/harness/runs/20260828T114543693474Z/receipt.json`。
- Receipt verification: `passed=true`、`fresh=true`、`fresh_for_snapshot=true`、
  `scope_paths_match=true`、`complete_completion_proof=true`、`snapshot_matches=true`、
  `workspace_cleanup_confirmed=true`、`workspace_stable_confirmed=true`。
- Harness selected `scope_diff_check`、`docs_contract_check`、`policy_audit_check` 与
  `product_runtime_skill_boundary_tests`; boundary tests reported `2 passed`。
- `git diff --check` passed。
- Commit is local `main` only；未 push、未 release。

本任务没有修改 Product Runtime、tests、Manifest、P6 policy、caption assets、media、Provider
state 或 Final Acceptance state；没有执行 OCR、ASR、waveform/media analysis、live/paid
Provider call 或 human final-media review。工作区中其他 staged/dirty files 均保留，未纳入本任务
commit。

上段只描述原 plan commit `5f10004`；Product Runtime 与 tests 后续已由 `31f365a` 修改。

## Implementation Review History

首次 implementation `reviewer_xhigh` verdict 为 `reject`，识别出四个 blocking defects：

1. adjudicator 对不完整/冲突证据存在 fail-open path；
2. unknown P6 attempt 可能被忽略并进入 replay/new execution；
3. repair outcome 未按 caption contract strict reopen；
4. Harness changed-path routing 未覆盖全部真实 caption/runtime owner。

实现逐项修复并补充 regression coverage。原 tier scoped re-review 给出
`accept with concerns`，仅剩 tampered repair rejection 的 zero-write assertion 建议；补充
Manifest bytes unchanged 与 RepairOutcome artifact absent 断言后，architecture extraction 后的
最终同 tier re-review verdict 为 `accept`，无 blocking issue 或 non-blocking concern。

## Implementation Verification And Publication State

- Task commit: `31f365a` (`feat: add caption final-media quality gate`)；53 files，
  3330 insertions / 537 deletions。
- Focused verification：`612 passed`（models/project/caption/Harness）、`514 passed`
  （state/recovery/Base/Ecommerce/profile）、HyperFrames `196 passed, 3 skipped`。
- Architecture verification：task-delta Architecture Gate `PASS`，`0 errors`；remaining
  `7 warnings, 1 info` 均为 non-blocking repository findings。
- Exact task-staged run
  `.agent/harness/runs/20260828-caption-quality-gate-staged-v2/receipt.json` 的所有 selected checks
  实际通过，但 concurrent writer 在运行中推进 `HEAD` 并清空 task index，导致 receipt 的
  freshness/snapshot/scope closure 失败；该 receipt **不作为 completion proof**。
- 随后对 current `HEAD` 的 combined exact range `31f365a^..23dc28b` 运行 Harness；receipt：
  `.agent/harness/runs/caption-quality-plus-local-comfyui-policy-20260828/receipt.json`。
  `verify-receipt` 返回 `passed=true`、`fresh=true`、`fresh_for_snapshot=true`、
  `scope_paths_match=true`、`complete_completion_proof=true`、`snapshot_matches=true`、
  `workspace_cleanup_confirmed=true`、`workspace_stable_confirmed=true`。
- Combined Harness selected checks 全部通过，包括 product runtime/skill boundary `2 passed`、
  Harness `204 passed`、production contract `2899 passed, 3 skipped, 1225 deselected`、review
  `653 passed`、commercial `891 passed`、image `1266 passed`、shot continuity `357 passed`、
  provider-neutral video requirement `333 passed`。
- Combined receipt 同时覆盖 task commit `31f365a` 与后续 unrelated local-ComfyUI policy commit
  `23dc28b`，因此它是 fresh current-HEAD completion proof，但不是 caption task-only receipt；
  本记录不把后者的变更归属到 caption task。
- Publication state：实现已 commit 到 local `main`；未 push、未 release、未触发 Provider、
  media generation、Production activation 或 Final Acceptance mutation。
- 现有 unrelated `.codex/config.toml` dirty state、H3 record staged state、`artifacts/` 与两份
  2026-08-27 untracked plan/spec 均保留，未纳入 caption implementation commit。

## Automatic Learning Evaluation

Implementation-phase `distill-ai-video-learning` automatic evaluation：`no_candidate`。当时的 evidence 是同一 caption
quality gate 的 plan、prior-art mapping、implementation 与 deterministic verification chain，不是两个
independent real-media attempts，也不是隔离变量的 controlled multi-arm comparison；现有 learning
claims 中也没有被这次 evidence materially supported/countered/reopened 的同一 claim。因此不满足
Learning Claim admission threshold，未创建 placeholder 或 pending candidate。

Real-validation update 的 automatic evaluation 当时为 `pending_candidate`。Raw generic-font PASS 与
Production custom-font FAIL 构成 held-constant controlled comparison，因此创建 pending v1：

`docs/record_for_agent/learning/hyperframes-caption-exact-source-readiness.md`

- candidate checkpoint commit：`bcd2215`
- committed candidate bytes SHA-256：
  `14012cdb907b5bf29cd7359fa96676db84785d4d263c67f18b691578a00748f9`
- `pending_evidence_status=SUPPORTED`
- `pending_approval_status=PENDING_CONFIRMATION`
- `pending_adoption_status=NOT_ADOPTED`

该 v1 从未被确认或 adopted，其 exact preimage 继续由上述 commit/hash 保存。`0ed672e` 的 runtime
修复与新的 exact Production PASS materially narrow 了原假设，因此 2026-08-29 automatic evaluation
将同一 claim 更新为 pending v2，而不是把 v1 留作 current advice：

- candidate checkpoint commit：`692e8b2fa5eaf3a24d0d288b08eb95dc89bddd79`
- committed candidate bytes SHA-256：
  `e5a9a65aaa6d98a29879f0afaafb0cb392f9b0d1fb562c8cfe6b681af2d008ba`
- `pending_evidence_status=SUPPORTED`
- `pending_approval_status=PENDING_CONFIRMATION`
- `pending_adoption_status=NOT_ADOPTED`
- `supersedes=bcd2215 / 14012cdb907b5bf29cd7359fa96676db84785d4d263c67f18b691578a00748f9`

Pending v2 把 claim 收窄为 pinned bundled/generic font contract 与 exact-source Gate 的同步维护规则；
确认后只拟更新 `.agent/context/control-plane-playbook.md` 的 maintenance Gate guidance，不再请求字体
runtime repair。当前 `0ed672e` 是用户直接授权的修复，不是 Learning Claim automatic adoption。
按 Skill contract，target adoption 在用户对 v2 exact commit/hash 作出 `Confirm`、`Revise` 或 `Reject`
前保持停止；candidate 本身不产生 P6、activation、Final Acceptance、push 或 release truth。

2026-08-29 exact V4 re-test 的 automatic evaluation：`no_candidate`。它复测的是同一
`087497ae...c4e1` bytes 与同一 canonical-identity blocker，不是 independent attempt、controlled
multi-arm comparison，也没有 materially support/counter/narrow 当前 HyperFrames font-readiness pending
v2。现有 Learning Claim、candidate commit/hash、confirmation 与 adoption state 均保持不变。

## Implementation Boundary

本节以下是 plan-time implementation boundary；授权已由用户本次“实现 plan”请求给出，并已在
`31f365a` 完成。它继续作为 unchanged-contract audit trail，而不是尚待执行的指令。

实施需要保持以下 unchanged contracts：

- 不新增 renderer fallback、timeline owner、Manifest writer 或 automatic activation path。
- OCR、ASR、waveform、frame sampling 与 renderer telemetry 只产生 raw evidence，不拥有
  canonical caption truth 或 Production verdict。
- evidence 缺失、陈旧、identity mismatch、coverage 不完整或 evaluator unsupported 时必须
  `NOT_EVALUATED`，不得静默 PASS。
- rerender、caption/audio/timeline identity 变化必须使旧 CAPTION receipt 与 Final Acceptance
  stale。
- empirical subtitle quality 仍需要 exact final-media evidence；unit tests、Harness 或 plan review
  不能替代 human/perceptual acceptance。

## Agent Guardrails

- `CaptionTrack` valid 不等于 final rendered captions correct。
- `QaLayer.LAYOUT PASS` 不等于字幕准确、同步、完整或无重复烧录。
- plan review 接受不等于 implementation 完成；本次完成结论来自 current code、tests、independent
  implementation review 与 fresh Harness evidence。
- Manifest migration 设计本身不构成支持证明；current reader 的 `2.15` 支持已由实现与 tests
  单独验证。
- Harness documentation receipt 不等于 runtime、media、P6 或 Final Acceptance evidence。
- 未重新核对 implementation-time dirty ownership 前，不得修改潜在重叠文件。
