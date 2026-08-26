# Shot Continuity Motion Endpoint Live Attempt Record

Date: 2026-08-26

## Purpose

本文记录用户批准的motion-compatible A3进入fresh Production bundle后的exact import、P0/profile reseal、
zero-effect preflight、唯一Local FL2VA submit/poll/fetch与真实MP4诊断。它回答两个不同问题：v7 hard cut与
tail freeze是否由endpoint repair消除，以及该technical repair是否已经足以授权accepted source或M0。

本记录不把successful fetch、Codex direct visual review或单一metric升级为human/P6、accepted candidate、
terminal/motion-tail、M0 effect、activation、Final Acceptance、push或release。

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

## Assessment

分层结论为：

- local execution/fetch/full decode：`PASS`；
- v9 hard-cut与tail-freeze observed repair outcome：`PASS`；
- v9-only causal attribution：`SUPPORTED_NOT_ISOLATED`；
- no-cut/no-teleport/screen-direction/continuing-gait technical continuity：`PASS`；
- exact boundary threshold：`NOT_EVALUATED`，measurement method尚未canonical冻结；
- automatic P6：`NOT_EVALUATED`，resolved source request的`continuity_binding=null`，不得合成binding旁路；
- human full-speed/P6 verdict：未记录；
- accepted source、candidate、terminal/motion-tail、M0、activation、Final Acceptance：均未发生。

因此当前v9不能因repair成功就进入Milestone 4 M0。下一真实gate是用户直接观看exact MP4并给出full-speed
human verdict，同时由accepted contract明确boundary measurement owner；在此之前不得调用
`VideoGenerationService.validate_once()`推进candidate，也不得派生terminal/motion-tail或触发M0/M1。

## Verification And Checkpoints

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
- `technical continuity PASS`不等于`boundary/P6/human acceptance PASS`。
- grayscale与RGB SSIM不能任选有利结果；canonical measurement method未冻结时保持`NOT_EVALUATED`。
- `submit/poll/fetch succeeded`不授权candidate、M0、retry、fallback或activation。
- 本次one-submit authorization已消耗；不得再次提交同一或不同ID来补做variant。
