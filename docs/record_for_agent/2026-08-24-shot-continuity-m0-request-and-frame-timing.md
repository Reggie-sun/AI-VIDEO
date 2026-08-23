# Shot Continuity M0 Request And Frame Timing Record

Date: 2026-08-24

## Purpose

本文记录 Shot Continuity Phase P1 在 execution-stack materialization 之后新增的两个 candidate-neutral
checkpoint：M0 request-level pre-submit identity guard，以及 C4 对 model-native exact frame-count timing 的
provider-neutral表达。

本记录不证明 M0 已提交、视频已生成、candidate winner、active capability、P6 verdict、creative PASS、
Final Acceptance、push或release。

## Current Runtime Truth

selected rainy-station M0 stack 已在前序 checkpoint 物化为
`2acf7e7843923460c503b6c9f3f53ca9c0bed627d21d8ca2cabe2e8e5b1a45f9`；M1仍为
`unmaterialized`，Hybrid artifact保持显式`presence=absent` / `content_hash=none`。

`M0ValidationPreSubmitGuard`现在在任何preview、durable intent、permit或Provider POST之前重新打开 exact
P0 closure与execution sources，并验证：

- request绑定重新打开的materialized `execution_stack_hash`；
- candidate/provider/model/capability、raw profile document、materialized compiler hash均为exact identity；
- execution为local/unmetered `image_to_video` motion boundary；
- image/media grammar严格为`first_frame=1`、`last_frame=1`、`reference=1`、
  `reference_video=1`，且motion-tail evidence存在；
- prompt hash、non-negative sealed seed、`1344x768`、`24 fps`、MP4/native-audio与model-native
  `frame_count=124`均匹配。

`VideoFlexibleOutputRequirement.exact_duration_milliseconds()`现在由output contract拥有 exact timing
projection。C4 request可将`124 frames @ 24 fps`绑定为rounded `5167 ms` endpoint evidence；
`provider_selected` timing或不匹配的endpoint milliseconds继续fail closed。现有integer exact-seconds C4
contract与legacy hashes保持兼容。

## Session Work And Decisions

- Commit `7291959`：强化M0 request-level pre-submit identity与zero-effect denial。
- Commit `513eeed`：允许C4 exact frame-count output绑定endpoint milliseconds。
- 未新增winner-specific Production child、export、family registration、active capability、fallback或第二writer。
- 未修改frozen prompt、rubric、qualification workflow/profile、spec或plan。

implementation前使用一个MiniMax external read-only explorer：Role=`explorer`，Scope=实际M0 Validation V1
caller与Hybrid workflow reuse boundary，model=`MiniMax-M3`，reasoning=`high`，transport=Claude-compatible，
runner status=`success` / agent status=`DONE_WITH_CONCERNS`。它正确确认现有T2VA与T8-native Turbo adapters
不能执行frozen M0 Hybrid Stock20 workflow；其“新增Production child”建议因Join Gate J1前禁令被拒绝，
后续保持qualification-only方向。sanitized capture：
`/home/reggie/.codex/session-diagnostics/minimax/01a02b2a-befa-7a43-8426-801a9bce5697-7dcb1f9ab61750e0.md`。

## Verification And Evidence

M0 request guard exact staged Harness：

- receipt：`.agent/harness/runs/shot-continuity-m0-request-seal-20260824-v2/receipt.json`；
- receipt SHA-256：`d0a0931b82b1d4723d540276f466b8a84079c2fa0ac1511164487896e0b12aa9`；
- `89 passed`，Documentation Contract与Architecture Gate PASS；
- receipt integrity、artifact、freshness、policy、snapshot、cleanup与closure全部为true。

C4 frame timing exact staged Harness：

- receipt：`.agent/harness/runs/shot-continuity-c4-frame-count-20260824-v2/receipt.json`；
- receipt SHA-256：`981d71d2d35b88faa38efe37504f011135073a978704e3df9d9c65ac747b5da8`；
- production video provider suite `1094 passed`；
- provider-neutral video requirement suite `292 passed`；
- Documentation Contract与Architecture Gate PASS，receipt verification全部为true。

native `reviewer_xhigh`使用`gpt-5.6-sol` / `xhigh`。第一次request-guard review因未验证exact
`frame_count=124`而`reject`；修复并增加wrong mode、125 frames、missing frame count与pre-effect denial后，
scoped re-review为`accept`。C4 frame-timing review为`accept`，无blocking issue。

## Remaining Gates

selected rainy-station bundle当前仍没有accepted upstream video bytes。P0的terminal frame与motion-tail只是
`planned_derivation`，run root内没有可用于`reference_video`的exact MP4/MOV，因此不能构造真实四锚点M0
request。calibration artifact也没有预先固定M0 seed；真实Validation V1开始前必须先形成一个sealed request
identity，不能在观看结果后选择或修改seed。

尚未实现或执行qualification-only live transport caller、input upload、one-use local permit、M0 submit、poll、
fetch、decoded boundary review或P6/human verdict。当前用户边界仍禁止Provider/ComfyUI generation、媒体生成、
M0 submit、T8 seed `320001`与六Shot baseline；所有external effect count保持零。

## Agent Guardrails

- 不得用P0 image assets、旧H3视频或其他run的MP4冒充same accepted upstream motion-tail。
- 不得把request guard/Harness PASS当作live-ready、quality PASS或winner evidence。
- Join Gate J1关闭前不得创建包含M0/M1 winner identity的Production child、export或active snapshot。
- 下一步若继续实现caller，必须保持qualification-only、single writer、exact four-anchor input、one permit、
  one submit、no retry、no fallback；缺少sealed source video/anchor lineage时仍须在任何effect前拒绝。
