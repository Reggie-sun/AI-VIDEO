# Shot Continuity M0 Layout Repair V6 Record

Date: 2026-08-27

## Purpose

本文记录M0 `quality-v1` v5的frame `83 -> 84` hard snap被定位为legacy ComfyUI MiniMax H3
packed-layout keyframe origin错误后，实施exact runtime reseal、inventory repair，并执行一次local T8
one-submit v6真实媒体实验的current evidence。

本记录只描述当前local development experiment。它不产生active capability、winner、M1、P6、Final
Acceptance、push或release truth。

## Engineering Repair

V5使用的ComfyUI commit `7cee3ceb1a35503172e0dfb8dbdedee2aba8aa`先计算last-frame
`cond_t`，再累加reference span，导致keyframe相对于真实target origin提前。对exact 48-frame motion tail，错误
anchor预测落在约frame `85` / `3.56s`，与v5实测frame `84` / `3.500s` hard snap吻合。

V6只改变该runtime layout变量：

- ComfyUI revision：`e01fb4c56b7a88149d469b99cbbfe3223d715054`；
- ComfyUI seal：`0.33.0+e01fb4c56b7a`；
- M0 execution stack：`c1e2c7bff9bf312eaf76a9996561a1c3334412aa4ffe2faa5360c38933afb89a`；
- profile：`workflows/qualification/minimax_h3_t8_c4_m0_candidate_v1_terminal_tail_v6_layout_repair_profile.json`；
- profile materialization hash：`244db35ca7123455ec31c1a3e7615d2b715af5ebeb45e136264aba9eaa5daf9e`；
- seed继续为`5696170359736854830`；
- exact prompt、A4 endpoint、identity、2秒terminal tail、Stock20/no-LoRA、20 steps、sampler、scheduler、
  geometry、fps与audio contract均保持不变；
- M1继续`unmaterialized`，Hybrid artifact继续`absent/none`。

相关commits：

- `ad55c93 fix: align M0 hybrid runtime layout`；
- `17fa7c3 fix: reseal M0 runtime inventory`。

第二个commit关闭了首次live preflight发现的inventory ownership缺口：canonical materialization owner现在以
source-revision CAS只更新`inventory.payload["comfyui"].commit/version`，并原子reseal P0 closure。Current v9
Manifest revision `68 -> 69`后，M0 stack、profile与seed均未改变，Provider effects保持`0`；完全相同的
materialization replay验证Manifest hash和mtime均不变。

Fresh Harness receipts：

- `.agent/harness/runs/m0-layout-repair-runtime-reseal-v4/receipt.json`；
- `.agent/harness/runs/m0-runtime-inventory-reseal-v2/receipt.json`。

Independent `reviewer_xhigh`对最终inventory repair verdict为`accept`，无blocking issue。

## Exact Live Attempt

在loopback-only ComfyUI、queue empty、exact preflight通过后，执行了唯一一次local submit：

- attempt：`rainy-station-m0-quality-v1-layout-repair-20260827-v6`；
- generation：`rainy-station-shot-4-m0-quality-v1-layout-repair-20260827-v6`；
- output asset ID：`video-shot-rainy-station-4-m0-quality-v1-layout-repair-v6`；
- request hash：`f7db17c2196195e68e70712b0471c8c7ee4b238031422ca6d823f2a3093183c8`；
- Provider request ID：`2b66dc39-1765-4023-8bea-4690c8c773c3`；
- submit/poll/fetch：`1/1/1`；
- retry/fallback/remote/paid：`0/0/0/0`。

Fetch后Manifest为schema `2.14` revision `74`，attempt保持`running/validate`，candidate asset IDs为空，
没有activation、M1或P6 effect。ComfyUI supervisor已在fetch与decode核验后停止。

Exact fetched artifact：

```text
runs/shot-continuity-rainy-station-p0-20260826-v9/production/state/video-generation/fetch/files/dc84a342e11e799e34b56e5257f3b6e7b7ca95205cf54ba2c288b3db8ab03580.mp4
```

- SHA-256：`dc84a342e11e799e34b56e5257f3b6e7b7ca95205cf54ba2c288b3db8ab03580`；
- size：`3119926` bytes；
- video：H.264、`1344x768`、24fps、124 frames、5.167s；
- audio：AAC、32kHz、stereo、5.152s；
- full video/audio decode：`PASS`。

## Media Validation

Project-local `video-analysis` MCP得到1 scene、11 extracted keyframes、166 sampled frames、166 unique frames、
unique ratio `1.0`、`issues=[]`。该工具以`0.5s`抽样且scene detector没有命中single-frame transition，因此结果只
排除literal repeated-frame freeze或decode failure，不能覆盖本轮frozen seam/static-tail requirement。

使用与v5相同的`336x192` grayscale、SSIM与Farneback参数对exact 124 frames逐帧测量：

- frame `100 -> 101`、timestamp `4.208s`出现最大突变；
- endpoint SSIM：`0.221897 -> 0.964603`，单帧增量`+0.742706`；
- transition flow：`6.434185`；
- transition luma MAD：`36.693638`；
- `3.5s -> 4.75s` mean flow：`0.441898`，但该均值被hard snap显著抬高；
- frame `104 -> 123` flow约`0.006456..0.010950`，画面已接近A4静图；
- `3.5s -> end`有`55%` transitions的flow低于`0.07`；
- final endpoint SSIM：`0.970846`，final endpoint MAE：`2.932338`。

按本轮预先冻结的自动门：

- `4.75s`前endpoint SSIM单帧增量必须`<=0.15`：`FAIL`，实测`+0.742706`；
- `3.5s -> 4.75s` mean flow必须`>=0.07`：数值`PASS`，但被同一hard snap污染，不能升级为自然运动PASS；
- final endpoint SSIM必须`>=0.90`：`PASS`，实测`0.970846`。

关键帧检查确认frame `100`仍为生成的side-tracking composition，frame `101`直接切换为exact A4-style
composition，frame `102 -> 123`仅有微小编码/雨景变化。相比v5，layout repair把hard snap从`3.500s`推迟到
`4.208s`，但没有消除seam或near-static tail。

## Current Assessment

- runtime layout target-origin engineering proof：`PASS`；
- inventory binding与zero-write replay：`PASS`；
- exact one-submit/poll/fetch lifecycle：`PASS`；
- fetched MP4 hash、probe、full decode：`PASS`；
- exact endpoint arrival：`PASS`；
- no early hard seam：automated frame-level `FAIL`；
- latter-segment dynamic continuity：automated frame-level `FAIL`；
- natural full-speed movement：`HUMAN_VERDICT_PENDING`；
- M0 P6、winner、activation、M1、Final Acceptance：均未发生。

当前证据拒绝“修正packed-layout keyframe origin即可关闭v5 perceptual failure”的hypothesis。它支持更窄的
结论：legacy origin bug确实控制了snap发生时间，但exact endpoint conditioning仍以single-frame replacement方式
满足终点约束，且随后输出近静态。

## Remaining Work And Guardrails

用户必须以exact MP4原速播放单独判定人物速度、后段静图与visible seam。自动FAIL已经阻断candidate/P6；human
verdict不能被`video-analysis issues=[]`或final endpoint SSIM覆盖。

在human verdict入账前，attempt保持`running/validate`。若human也拒绝，应由
`ProductionStateCommitter.record_video_provider_failure()`使用typed video error将该attempt原子关闭，同时保留
fetch evidence；不得retry、resubmit、换seed、切policy、自动activation或进入M1。

任何新的endpoint-conditioning、prompt pacing、asset redesign或不同attention/runtime实验都是新的变量和新的
generation scope，需要独立decision与authorization。本记录写入不执行新的Provider/media call，也不刷新RAG index。
