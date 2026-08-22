# Shot Continuity P0 Preflight And Image Set Record

Date: 2026-08-23

## Purpose

本文记录 canonical Shot Continuity plan 的 Phase P0 stable checkpoint：truthful GPT Image 2 MCP/browser
imports、fresh Local T8 inventory、exact four-Shot rainy-station validation set、M0/M1 candidate stack identities、
model-facing tensor contract，以及 Manifest `2.11` 的 `qualification_prepared` selection。

本记录不证明视频已生成、candidate winner、active capability、creative PASS、P6 verdict、Final Acceptance、
push、release或多 Provider portability。Current code/tests、Production Manifest与 runtime baseline仍是动态 truth。

## Governing Contract And Authorization

- Spec: `docs/superpowers/specs/2026-08-19-ai-video-shot-continuity.md`。
- Plan: `docs/superpowers/plans/2026-08-19-ai-video-shot-continuity.md`。
- 用户在本轮明确批准完整 P0 contracts 及其 Manifest/artifact migration；该批准不扩展到 M0/M1 generation、
  winner selection、capability activation、remote/paid execution、push或release。

P0 persistence复用唯一 `ProductionStateCommitter`，没有新增 writer、timeline、renderer、Provider fallback或
mutable qualification lifecycle。

## Truthful GPT Image 2 Import And Human Freeze

用户选择重新生成 A2，并随后明确冻结新的 A1–A4 order。四个 frozen PNG均为 RGB `1659x948`：

| Candidate | SHA-256 |
| --- | --- |
| A1 | `61ee0609f3c7aae86ca78ed02e4080b35a59608b7c3a7aff0f2389a47f57f9cb` |
| A2 | `c50517a17313402ef271694ea058d6c92b0b750c4b854e39858bdaf5d73c5768` |
| A3 | `03f4c5ebd177486dd65b21d61901f2296ef7255f12819c66099ef93815a7fc7c` |
| A4 | `ac6b83a8c2abc2f21d50d29a4aa4c377d6044bb297e58d2d4c9ae56e4468f377` |

A0 retry与 A1 bytes identical，因此不进入 validation set。

新 `AutomatedBrowserImageImportReceipt` 记录 exact PNG bytes、dimensions、generation/approval/import timestamps、
prompt fingerprint、automation actor与human approval actor。MCP没有提供可独立验证的 backend model/request ID，
因此两者保持 `None`；signed `sourceUrl` 不进入 receipt。原有 `HumanImageImportReceipt` contract未放宽。

A2 source metadata prompt误写 `dark raincoat`，虽然 frozen output视觉上保持 canonical mustard-yellow raincoat。
该冲突被保留在 human-freeze limitations，不能被改写成干净的生成 provenance。后续 video prompt使用
OpenVideo/H3 official three-field grammar和显式 conditioning instruction，固定 mustard-yellow hooded raincoat、
red cross-body satchel、rightward screen axis、50mm-equivalent FOV、chest-height camera、small-amplitude slow
parallel track、exact first/last frames、action phase、rain/footsteps soundscape与无配乐选择，并禁止 cut、zoom、
axis reversal、teleport、extra person与wardrobe change。

Human freeze只批准这些 source candidates用于 P0 preparation；不构成 Reference Asset之外的 Final Shot Visual，
也不构成 creative/P6 acceptance。

## Model-Facing Tensor Contract

当前 sealed Local T8 lane固定 `1344x768`、124 frames、24fps、32-pixel dimension multiple。Comfy IMAGE输入是
normalized float `BHWC`，所以 frozen calibration contract为：

```text
source PNG:       RGB 1659x948
source ratio:     exact 7:4
target canvas:    1344x768
target tensor:    BHWC [1,768,1344,3]
target dtype:     float32 normalized 0..1
scale:            exact 64/79 on both axes
first frame:      Lanczos, crop disabled
last frame:       Lanczos center-crop path, but exact 7:4 means no pixels are cropped
reference image:  match-area + round32 resolves 1344x768
```

因此 GPT output不是直接的 model tensor，但它与 sealed canvas精确同 aspect ratio，可确定性等比缩放且无拉伸、
无实际裁切。Preparation script在 source mode、dimensions或 ratio不一致时 fail closed。这里的“最佳”只指
current sealed T8 profile的 exact accepted canvas，不外推为所有 H3/T8 model/configuration 的全局最佳尺寸。

## Fresh Local T8 Inventory

- ComfyUI `0.33.2`, commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；
- ComfyUI-MiniMax-H3-Turbo `1.36.2`, commit
  `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`；
- VideoHelperSuite commit `4ee72c065db22c9d96c2427954dc69e7b908444b`；
- stock Ref2VA `9eef934046a0671bc8a5daf87100705e1478419c574cfde70c50fbe6885f76a9`；
- pruned FL2VA `e889202c41dafb67b10d67b97f0d8541508036a6090af23425a5c2615d03c47a`；
- pruned Ref2VA `9255f52b6677845ad238f20dfaafa94727053694127ab7f255c048f0f9365779`；
- Qwen text encoder `35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6`；
- video VAE `7c1f131492e7eddacaac9069a61b81bdd39de5cc96561e677c5eab1cdce5e522`；
- audio VAE `8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48`。

M1 Hybrid artifact/sidecar仍不存在；P0 stack使用canonical empty representation
`presence=absent`、`content_hash=none`；future build recipe仍只由plan拥有，不进入当前stack artifact identity，
也不宣称 M1
materialized、executable或ready。

## Selected P0 Bundle

Ignored Production run root：

```text
runs/shot-continuity-rainy-station-p0-20260823-v5/production
```

Selected runtime identities：

- Manifest schema/revision: `2.11` / `3`；
- P0 receipt: `da932addfaf01310b69a8287093ad1fac734487d7916620c209d0885132b8a2e`；
- RealShotValidationSet: `d2da773a6df7b750001bd1ccb424f6e15238052b9118a9fc7cacf533b6b9ac28`；
- M0 candidate stack: `101a5df4f76c570f378939875e52b724ad61d63ceb71d81c9a6c2f1fc9e9a965`；
- M1 candidate stack: `4d08741636647fbb29f9cf69a69a2c81d62156cef128f619d26a17b72e94c01b`；
- three policy hashes:
  `bf6543ffb10bb0994ad476cff6f8c9c1c95a231ad57f4982bfe03a126c85de39`,
  `254648432e5dae50c4a3742dbf8d2e32d455934dac598aaa3bbbd6b358e2ae7a`,
  `4eda25509742ef9c83e550dd376e2c77d03e6561e096cf4b8fbf2f9483f845d3`。

Bundle contains four canonical narrative Shots、three adjacent `HARD_CUT + FULL_CONTINUITY` policies、subject
and camera motion coverage、five qualification inputs与six registered image assets（Character、Scene和 four
Shot endpoint bindings）。Terminal frame与motion-tail anchors在 P0 是 `planned_derivation`，尚未冒充已物化
evidence。

M0/M1 candidate stacks都是`materialization_status=unmaterialized`，`profile_hash`、`compiler_hash`与
`workflow_hash`均为`none`。这是对当前P0真实边界的明确表达：已冻结candidate contract，但尚未
冻结真实executable profile/compiler/workflow。M0 submit前必须完成物化并重新seal所有依赖新
`execution_stack_hash`的policy与receipt。

`reopen_p0_qualification_prepared()` exact-reopens完整 closure；recovery对12个 video-qualification artifacts
报告 `active`，revision保持 `3 -> 3`。Project或Registry identity变化会清除 selected pointer，不能继续复用
stale preparation。

## Implementation And Verification Boundary

Implemented owners：

- `video_execution_stack.py`: immutable candidate stack identity；
- `video_transition.py`: policy、validation set、P0 input/receipt contracts；
- `image_import.py` / `_image_project_reader.py`: truthful automated-browser import/reopen；
- `_state_commit_p0_qualification.py`: sole-writer record/reopen/replay；
- Manifest `2.11` and recovery routing；
- `scripts/prepare_shot_continuity_p0.py`: no-Provider deterministic bundle preparation。

Executed evidence at this checkpoint：

- no-Provider preparation smoke：success；
- exact selected bundle reopen：success；
- selected recovery：12 P0 artifacts active, no state advance；
- broad image import / P0 / transition / Q0 / generated-video E2E / state recovery selection：`390 passed`；
- final pointer-model / P0 / import / Q0 compatibility selection：`378 passed`；
- final P0 stack / policy / import focused selection：`42 passed`；
- `git diff --check`: pass。

Final exact-snapshot Harness、independent final review与commit状态不由本记录的静态文本拥有；以对应
exact snapshot的Harness receipt、review evidence和Git history为准。

## MiniMax Delegation Evidence

- Role `explorer`, Scope P0 persistence owners, model `MiniMax-M3`, transport MiniMax CLI/Claude runner bridge,
  status `DONE_WITH_CONCERNS`。它建议独立 automated-browser receipt、Manifest `2.11` P0 pointer、narrow
  committer method与全量 2.11 compatibility audit。
- Role `writer`, Scope P0 bounded implementation：首次和一次 bounded fresh retry均因 command whitelist/grant
  mismatch终止为 `BLOCKED`，没有写入。
- Role `writer`, Scope automated-browser import：首次和一次 bounded fresh retry均为 `BLOCKED`；retry在未授权
  `find ... conftest.py | head -5` 后进入 `tool_error_loop`，没有写入。

Parent在上述 terminal failures后完成实现与验证。Sanitized diagnostic：

```text
/home/reggie/.codex/session-diagnostics/minimax/01a02a0e-f757-76e3-8a48-00cae28a0d95-e82349bc2a2a7596.md
```

## Remaining Boundary

- 尚未执行 M0；没有 local video output、decoded boundary、identity/motion evidence或human full-speed review。
- M0未按 frozen gates通过前不执行 M1；没有 runtime fallback。
- 没有 winner-specific child、active capability、ProviderTransitionQualification、TransitionAttemptEvidence或
  Router integration。
- Automatic evaluator缺失或不可信时必须 `NOT_EVALUATED` + exact human/P6 evidence，模型不得自报 PASS。
- Seedance draft与 `index.json`、`.workflow/.scratchpad/`属于独立 dirty work，本 checkpoint不覆盖或纳入提交。
