# Shot Continuity Motion Endpoint Live Attempt Record

Date: 2026-08-26

## Supersession Notice

本文件早期live-attempt段落记录的是Manifest revision `15`、`next_action=validate`时的历史边界。2026-08-26
同一exact v9 MP4随后通过additive Manifest `2.14` source-boundary checkpoint持久化P6 `PASS`，并准备inactive
candidate与terminal evidence。下文原始live measurements与因果限制继续有效；其中“boundary/P6未关闭、没有
candidate/terminal”的current-facing结论已由`Source Boundary P6 Closure`与修订后的`Assessment`取代。

## Purpose

本文记录用户批准的motion-compatible A3进入fresh Production bundle后的exact import、P0/profile reseal、
zero-effect preflight、唯一Local FL2VA submit/poll/fetch与真实MP4诊断。它回答两个不同问题：v7 hard cut与
tail freeze是否由endpoint repair消除，以及该technical repair是否已经足以授权accepted source或M0。

本记录不把successful fetch、Codex direct visual review或单一metric直接升级为P6。后续source-boundary P6
只来自Manifest `2.14` exact-bound intent/evidence/receipt closure；其PASS只准备inactive candidate与terminal
evidence，不等于M0、activation、Final Acceptance、push或release。

## Current Runtime Truth

Fresh root为：

`runs/shot-continuity-rainy-station-p0-20260826-v9/production`

该root只revision用户批准的A3，保留A1/A2/A4 exact identities，且没有复制v7 video attempt：

- endpoint asset：`image-import-ff896c4d23cfd1b0d426e64f6243c4c5cca3f9ed2e95a3dfb5b08821e98e2322`；
- endpoint PNG SHA-256：`347e1208215f2d2a4a0b37ec60dbed62daed19dd62ac2a776ab1b308f9fb9c1c`；
- Project revision/hash：`2` / `4f53877b9e437c2cec5161c966dc9c6a9e1c4c5a4ba7af43951a5b696cd2bbab`；
- Registry：`8902beaf6540759faab80a4efe6acef00d8a118d4437ef16abba9e8709847256`；
- Dependency Graph：`74180e63cc2134526476fc2007611a54c8eba262d0df1c0d247cebef62571f89`；
- target Shot revision/hash：`2` / `691dd13ec05b9ef19910649e89c38b7be50235fb5a4c5215ea21c3ff37f3ffe8`；
- P0 receipt：`80149ed5e866572b9bd10e4ea37c7ebe452e8cd4497e4ab5ebc9387b75e11fc2`；
- M0 stack/profile：`073f0f429f49d828538b12fce6d7616a7834ebb53dbe31efe43c22fda41d0a24` /
  `808f688e62131653d0d3e2b0ffa877645a684b4011bc680dfa42a653c98f975a`；
- source stack：`482da299c4e3c434ae3f92fbac88982cf989d2ff333799e3ddba3e4073b17093`；
- M1仍为unmaterialized，Hybrid artifact保持`presence=absent`、`content_hash=none`。

Endpoint provenance/reopen repair commit为`28e7094ca14504068e059272a6dae3da8e3d1fba`；revision-aware source
profile与v9 reseal commit为`0ebb19957d5d260ea05896ea5c7e68ebb9ecb086`。`ProductionStateCommitter`仍是唯一durable writer，最终
`VideoGenerationRequest`仍只由`video_compiler.py`构造。

## Live Attempt Evidence

Repository supervisor在literal `http://127.0.0.1:8188`启动ComfyUI checkout
`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`。submit前queue running/pending均为空，inspect确认
`attempt_present=false`、`video_attempt_count=0`、`next_action=submit`。

Zero-effect preflight重验exact A2/A3 PNG、Project/Registry/Graph、P0/M0/source stack、14个source与12个M0
required node schemas及4个component bytes；durable bundle hash before/after同为
`df6f7b05a71509cb6a8c3f4f79028fbe248e035ed37b544e0d233f0a8e5cdda5`，Manifest revision保持`10`。

唯一attempt为`rainy-station-source-a2-a3-motion-endpoint-20260826-v1`：

- request hash：`3dd67dc23cc7e7cd981d0f49e75cfcfb4b23ab3967f3ef9365f4fd9029b055ed`；
- sealed seed：`3742455256126004804`；
- Provider request ID：`8d09fc4e-9ad4-40f4-8b52-cbdab9a0cfeb`；
- 本session实际action count：submit/poll/fetch=`1/1/1`，retry/fallback/remote/paid=`0/0/0/0`；
- terminal observation：`succeeded`，`progress_milli=1000`；
- ComfyUI execution wall time：约`384.541` seconds；
- fetch SHA-256：`5324a2b0c65fea658b0ab5267020dbb00ecc080988a50987c46c1f9d21e4bbdf`；
- repository-relative MP4：
  `runs/shot-continuity-rainy-station-p0-20260826-v9/production/state/video-generation/fetch/files/5324a2b0c65fea658b0ab5267020dbb00ecc080988a50987c46c1f9d21e4bbdf.mp4`。

fetch后Manifest revision为`15`，`video_attempt_count=1`、`next_action=validate`；没有candidate asset、
activation、terminal/motion-tail或M0 state。Queue清空后supervisor已停止，`127.0.0.1:8188`不再监听。
Pre-submit queue、preflight before/after hash、action count、wall time与listener状态是本session的live observation；
当前durable state可独立证明唯一attempt及一组intent/submit/status/fetch receipts，但不能单独重建所有transport
query或host observation，未来若需更强审计应绑定immutable command/log evidence。

## Real Media Verification

对上述exact MP4而非fixture或历史artifact执行直接probe与full decode：

- 2,484,571 bytes，H.264 High、`1344x768`、`24 fps`、124 frames、5.167 seconds；
- AAC LC、32 kHz、stereo、5.167 seconds；
- video与audio完整decode通过；124个decoded frame hashes全部唯一；
- exact first/A2 PSNR `33.460252 dB`，last/A3 PSNR `32.505680 dB`；
- exact first/A2 grayscale/RGB SSIM `0.920355/0.888287`；
- exact last/A3 grayscale/RGB SSIM `0.905835/0.864289`。

同一OpenCV pipeline直接重算v7与v9相邻帧MAD及Farneback flow。Recipe固定为：按OpenCV顺序完整解码BGR
frames；RGB MAD取full-resolution相邻frame三通道absolute difference mean；flow先以`INTER_AREA`缩放到
`336x192`并转grayscale，再调用
`calcOpticalFlowFarneback(pyr_scale=0.5, levels=3, winsize=15, iterations=3, poly_n=5, poly_sigma=1.2, flags=0)`；
每对frame先取flow magnitude median，再对segment做arithmetic mean；leg ROI为resize后
`y=104:192`、`x=40:175`：

| Evidence | v7 old endpoint | v9 motion endpoint |
| --- | ---: | ---: |
| frame 107→108 RGB MAD | `42.681249` | `1.709055` |
| largest adjacent-frame RGB MAD | `42.681249` at 107→108 | `2.960178` at 11→12 |
| frames 120→123 RGB MAD mean | `0.054458` | `1.545673` |
| frames 120→123 global median-flow mean | `0.001890` | `0.073229` |
| frames 120→123 leg-ROI median-flow mean | `0.001753` | `0.268786` |

这组live comparison不是严格的endpoint-bytes-only A/B：seed derivation contract保持不变，但
content-addressed closure随endpoint改变，使v7 numeric seed `3625644815483226956`与v9 numeric seed
`3742455256126004804`不同。严格单变量因果证据仍来自2026-08-24 endpoint-only development A/B；v9是新的
canonical endpoint在fresh Production closure中的独立支持证据，不能单独排除seed interaction。

Codex直接查看从v9 exact MP4解码的全片12-frame contact sheet、frames 96–123每3帧sheet、frames
104–123逐帧sheet，以及A2/frame0、A3/frame123 side-by-side。画面保持同一East Asian woman、short black
bob、mustard-yellow raincoat、red satchel、rainy platform、clock与screen-right direction；人物与腿部在tail
继续换步，没有v7的one-frame composition reset、teleport、axis reversal或near-static final block。

这些结果与历史endpoint-only A/B共同支持
`MOTION_COMPATIBLE_ENDPOINT_REPAIRS_HARD_CUT_AND_TAIL_FREEZE`，但v9本身不是严格因果A/B。它们不自动关闭全部boundary
acceptance：frozen rubric声明SSIM minimum `0.9`，本轮grayscale SSIM通过而RGB SSIM未通过，当前contract
没有冻结哪一口径可作为canonical verdict。Direct visual认为endpoint composition一致，但不能替代该contract
decision或human/P6。

## Human Verdict

2026-08-26，用户观看上述exact MP4后指出人物行走观感偏慢，并询问这是否为有意生成的slow-motion镜头。
在本session明确说明没有执行retime、插帧或slowdown，并说明“若排除该pacing问题，镜头的no-cut、no-teleport、identity、scene与screen-direction continuity
可通过，但不等于automatic P6、M0或Final Acceptance”后，用户回复“通过”。

因此，绑定fetch SHA-256
`5324a2b0c65fea658b0ab5267020dbb00ecc080988a50987c46c1f9d21e4bbdf`的human visual subjective verdict为
`PASS_WITH_PACING_WAIVER`。该waiver只表示用户明确不把本镜头的偏慢行走观感作为拒绝项；它不表示视频经过了
retime。该human decision本身不直接产生boundary/P6/candidate；只有下节记录的exact-bound Manifest `2.14`
checkpoint把它与automatic measurements共同裁决并持久化。

## Source Boundary P6 Closure

在用户选择完整additive A路径后，现有exact v9 MP4被复用；本步骤没有新submit、poll、fetch、Provider、
ComfyUI、network或media-generation effect。Manifest先从`2.11`显式升级到`2.14`，再由
`ProductionStateCommitter`唯一写入source-boundary intent，执行一次exact decoded measurement并原子闭合
evidence、receipt、probe与provenance。

Canonical measurement contract
`2b5aaddb094453798059a808722c31e7de38f390ede7a433035009e05216c248`冻结：

- decoded frame `0`与exact terminal frame `123`；
- ffmpeg `rgb24` decoder identity；
- A2/A3以Pillow Lanczos等比resize到`1344x768`，no crop；
- RGB PSNR minimum `30,000 millidB`；
- BT.709-luma SSIM、uniform `7x7` sample covariance、data range `255`，minimum `900,000 millionths`；
- half-even integer comparison rounding。

Exact measurements：

| Endpoint | Frame | RGB PSNR | BT.709-luma SSIM | Result |
| --- | ---: | ---: | ---: | --- |
| A2 / first | 0 | `33.510 dB` | `0.922665` | PASS |
| A3 / last | 123 | `32.539 dB` | `0.905545` | PASS |

这些数值与前文OpenCV/skimage historical measurements略有不同，因为新contract固定BT.709 luma、uniform
window与sample covariance，不再允许在grayscale/RGB结果之间任选口径。Exact human decision文件为
`workflows/qualification/rainy_station_source_v9_boundary_human_decision.json`，content hash
`51d3523e4125d20fd3c0a046f57f202c1ca1a7c0f911be310b45d03b28646a05`；它绑定request
`3dd67dc23cc7e7cd981d0f49e75cfcfb4b23ab3967f3ef9365f4fd9029b055ed`、artifact
`5324a2b0c65fea658b0ab5267020dbb00ecc080988a50987c46c1f9d21e4bbdf`与用户的
`PASS_WITH_PACING_WAIVER`。

Durable hashes：

- intent：`cb3e1fae39fca585a42dc7731300fa2e8ce8400fc170e3aa22b416e757403e94`；
- evidence：`085bd34f5830d35fe2a09b155e4c0870d81072ec57eb21e5e9bff394e1303b98`；
- P6 receipt：`47bd637b7abdc0c6e9a3227f6b4f770b6c61f007d796ea158f4b090bba892048`，verdict `pass`；
- probe：`87c3f63a722a79bffb4636d8f103e5d849fde3c5c960f44f9ec913305cfcc65f`；
- provenance：`a34a860e031d3b9927470d76f85f41b093a536a1987826900ffbf98d6c54e5d2`。

Current Manifest strict reopen为schema `2.14`、revision `20`、phase `candidate`、source-boundary verdict
`pass`。Inactive candidate pointers为Project revision/hash
`3`/`f05a3f681bfedcf804e9fb59fb6fa85537aa45ec37e987b8449723f5b05de8f5`、Registry
`a74c81510fb2ebae271525e95480c3ac934a569e5860c7b0e8bd364b794f655d`、Dependency Graph
`520b59b0b43bcbd811ebfa56d862015f5a7a7f3c0d52e52a5f1ed2b8d65658cf`；active pointers仍是Project `2`、
Registry `8902beaf...`与Graph `74180e63...`。没有执行activation、M0/M1、Final Acceptance、push或release。

## Assessment

分层结论为：

- local execution/fetch/full decode：`PASS`；
- v9 hard-cut与tail-freeze observed repair outcome：`PASS`；
- v9-only causal attribution：`SUPPORTED_NOT_ISOLATED`；
- no-cut/no-teleport/screen-direction/continuing-gait technical continuity：`PASS`；
- exact boundary threshold：`PASS`，绑定上述frozen measurement contract与exact A2/A3；
- source-boundary P6：`PASS`，通过独立Manifest `2.14` checkpoint关闭，未合成`continuity_binding`；
- human visual subjective verdict：`PASS_WITH_PACING_WAIVER`，只豁免用户明确接受的偏慢行走观感；
- inactive candidate与terminal evidence：已准备但未activation；
- M0/M1 effect、activation与Final Acceptance：均未发生。

Source boundary/P6 gate已经关闭，但当前v9不能仅因该结论进入Milestone 4 M0。Manifest candidate保持inactive，
本次用户“通过”和A路径修复授权都不是新的M0 execution authority；任何M0 submit仍需fresh explicit policy
selection、preflight与task-scoped local live authorization。

## Verification And Checkpoints

Source-boundary Manifest `2.14` implementation focused verification：

- `ruff check`覆盖source-boundary committer/reviewer/operator、strict reader、activation/candidate/recovery seams、
  CLI script与相关tests：`PASS`；
- `PYTHONPATH=src:. pytest -q -p no:cacheprovider`覆盖source review/operator、Manifest models/project、
  video recovery、committer structure与Harness policy：`640 passed`；
- `python scripts/agent_harness.py policy-audit`：`unmapped_paths=[]`、`unverified_paths=[]`、
  `docs_contract_diagnostics=[]`；
- current v9使用当前代码strict reopen并重新验证immutable source-boundary closure：schema `2.14`、revision `20`、
  phase `candidate`、verdict `pass`、evidence
  `085bd34f5830d35fe2a09b155e4c0870d81072ec57eb21e5e9bff394e1303b98`，candidate仍inactive。

本source-boundary patch的唯一completion Harness receipt path为：

`.agent/harness/runs/shot-continuity-v9-source-boundary-p6-20260826-staged-v3/receipt.json`

该path本身不构成PASS声明；completion必须读取并验证其actual status、exact staged scope、artifact hashes、
integrity、freshness与workspace flags。

Earlier source-boundary completion attempts均不是可复用PASS evidence：初始staged receipt因`models.py`
oversized-module净增长1行被Architecture Gate拒绝；`staged-v2`随后由existing legacy
`approved_endpoint + seal_terminal_frame=False` compatibility regression拒绝。当前实现只把sealed
`approved_endpoint`保留给source-boundary owner，同时仍忽略binding字段进行routing，因此fake binding进入exact
validator并在probe/evaluator/candidate effect前fail closed，而legacy unsealed path保持不变。

Endpoint repair exact-range Harness receipt：

`.agent/harness/runs/shot-continuity-endpoint-repair-20260826-range-v2/receipt.json`

Revision/profile follow-up staged Harness receipt：

`.agent/harness/runs/shot-continuity-v9-source-profile-followup-20260826-staged-v2/receipt.json`

后者实际通过docs contract、policy audit、Architecture Gate、185 harness tests、9 workflow tests、251 Shot
Continuity P0 tests、690 production video provider tests与295 provider-neutral video requirement tests；receipt
integrity、freshness、snapshot、scope与workspace flags均为`true`。Native `reviewer_xhigh` scoped re-review最终
`Verdict: accept`。

## Agent Guardrails

- v7与v9是不同exact artifacts；v9修复不能抹掉v7失败历史。
- 相同seed derivation不等于相同numeric seed；不得把v7→v9描述为严格endpoint-only live A/B。
- `source-boundary P6 PASS`只绑定该exact qualification source，不等于M0/M1 qualification或Final Acceptance。
- `PASS_WITH_PACING_WAIVER`只绑定上述exact MP4与用户明确排除的偏慢观感，不是全局放宽motion rubric。
- Historical grayscale/RGB SSIM不能任选有利结果；current verdict只使用frozen BT.709-luma method。
- `submit/poll/fetch succeeded`不授权candidate、M0、retry、fallback或activation。
- 本次one-submit authorization已消耗；不得再次提交同一或不同ID来补做variant。
