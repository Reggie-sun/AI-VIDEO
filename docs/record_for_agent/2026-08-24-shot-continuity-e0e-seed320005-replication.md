# Shot Continuity E0-E, E0-F And E0-G Seed Replication Record

Date: 2026-08-24

Updated: 2026-08-25

## Purpose

本文记录三项必须分开的 Local MiniMax H3 T8 development effects：

1. E0-E 原计划只把 E0-D seed 从 `320001` 改为 `320005`，用于验证 early-stop schedule 的 seed-to-seed reproducibility；
2. E0-E 运行中，用户明确改为“把画质调低一点快速验证”，因此 E0-E 被 targeted cancel，随后以独立 E0-F identity 运行 T8 upstream 4-step Turbo quick mode。
3. 用户确认继续后，以新的 E0-G identity 重新执行 Stock20、no-LoRA、`1344x768`、seed `320005` strict replication，避免 blind resume 已取消的 E0-E。

E0-E 没有完成 seed-only replication，不能给出 replication PASS/STOP。E0-F 只提供低分辨率 Turbo4 的方向性 schedule evidence。E0-G 才是对 E0-D frozen generation surfaces 的 seed-only replication；其 PASS 仍不是 Production qualification、P6、Final Acceptance、active capability、canonical reference 或 release evidence。

## Preflight And Evidence Boundary

执行前确认：

- E0-D reference commit `800168033b1aba1decf0c816192ae93ac8e11fb4` 仍为 current local `main` ancestor；没有 reset 或覆盖其他窗口工作。
- 只有当前 Codex root agent 活跃；目标 record 不存在且没有 target-file ownership overlap。
- `/tmp/shot_continuity_e0b_seed320001_request.json` SHA-256 为 `c3008cb8433ab38a48ed49c5d2b5b2f9ce0bb79fcb335a442021057e790271a8`。
- `/tmp/shot_continuity_e0d_request_filter.jq` SHA-256 为 `3e3c3b2dc146201000415e1e9bce6fdde455fca3141ef6911c13acdffac5dccc`。
- 两者确定性派生的 E0-D compact request SHA-256 为 `e3572fe61715da82449337e5398c51e7cf3633b31b9fde1e64e575e36f857161`，与 accepted E0-D record 一致。
- focused `retrieve-ai-video-memory` 严格返回 exit `2`、`index embedding identity mismatch; rebuild required`；本轮按 skill fail-closed，不 rebuild、不降 validation、不重试检索，只使用 current repository/runtime evidence。
- ComfyUI commit 为 `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；MiniMax H3 T8 plugin commit 为 `28cb160827c245b2d6a37539df30c1d7c5e7aecd`，plugin checkout clean。
- E0-E chain 与 E0-F chain 均在各自 submit 前不存在；queue running/pending 均为 `0`。

本窗口独占 supervised ComfyUI unit：

```text
ai-video-comfyui-a9fc3e49408c4a33a2e2b2af6ec8ba2e.service
```

该 unit 只监听 `127.0.0.1:8188`。全部验证完成后 queue 再次为 `0/0`，unit 已显式停止，supervisor 返回 `inactive`，端口不再监听。

## E0-E Seed-Only Contract And User-Directed Interruption

E0-E compact request SHA-256：

```text
bc7d2730027ed66d744134240382ef69a561118ee4a4e826e4c8b5141b6bafeb
```

相对 E0-D 的 structural diff 只有四个 scalar paths：

- `client_id`
- `prompt["6"].inputs.chain_id`
- `prompt["7"].inputs.base_seed`: `320001 -> 320005`
- `prompt["17"].inputs.filename_prefix`

四类 exact prompt UTF-8 bytes SHA-256 保持：

- steady: `f2e18a1473651c04c097133314d021d55b1197699d48ddb75b158b74a576884d`
- decelerate early: `ad5b90e98e5a99faf9d802161b76064427d5cc4b6688734875caff9656bfb7ee`
- stop and hold: `417589b2b8e8b3ddbbd785cf79a8c23445cf3f72ee4be46665e23d4dfcfe7a8d`
- settled hold: `bbf3e4b3f8eee9b4a32f19dffb09eb25635f52ab288203e3e7303384d639fa37`

唯一 submit：

- initial prompt ID: `f8cf51c7-1b83-4351-b282-da38c9209fa6`
- background job ID: `5d76f6f2-bcfb-4990-a813-2929cb76fc83`
- segment 1 prompt ID: `7046e4ca-b72d-422a-a7bd-669a6da5c342`

segment 0 durable accepted 后，用户明确把目标改为 T8 fast mode。当前 segment 1 随即 targeted cancel；这不是 route-kill quality failure，也不是 infrastructure interruption。最终 E0-E state 为：

- state: `cancelled`
- accepted count: `1`
- accepted frames: `124`
- retry: `0`
- fallback: `0`
- remote/paid effect: `0`

Canonical accepted-prefix partial：

```text
/home/reggie/ComfyUI/output/minimax_h3_t8_long_video/shot_continuity_e0e_seed_replication_v1_seed320005_20260824/assembled/H3_Long_Video_Accepted_Prefix_Partial_r0001_cosine_bridge.mp4
```

- SHA-256: `aafd440ff4f14e422bed1a3faaa20a97ca864d84a0d50aa69318f5caf63bdc98`
- Manifest SHA-256: `e0d2c6d9c9518479d787fa84cb0940d7c4f0918a90e671e25c1c61a0d8515542`
- exact video span: `124 / 24 = 5.166667 s`
- audio samples: `165333 @ 32000 Hz`

因此 E0-E replication status 是 `NOT_EVALUATED — USER-DIRECTED CONTRACT SUPERSESSION`。不得把该 partial 描述为 770-frame replication，也不得从 segment 0 推断 stop/hold 或 seed reproducibility。

## E0-F Turbo4 Quick Validation Contract

E0-F 是新的 multi-variable development treatment，不是 E0-E resume/retry：

- chain ID: `shot_continuity_e0f_turbo4_quick_validation_v1_seed320005_20260824`
- deterministic filesystem component: `shot_continuity_e0f_turbo4_quick_validation_v1_s_93c5f6191541`
- client ID: `shot-continuity-e0f-turbo4-quick-validation-v1-seed320005-20260824`
- request SHA-256: `bb6b1a672580ac59adbfa5074ae21f4a9f2f43ed1447fd278e0bd4a04a427137`
- initial prompt ID: `50b8fbbb-a09c-426f-8cc2-d5c8f42f4bfd`
- background job ID: `e6105a05-dbb5-4c69-8da4-0ee1d9058a8f`

相对 E0-D 明确改变的 quality/speed surfaces：

| Surface | E0-D | E0-F quick mode |
| --- | --- | --- |
| Resolution | `1344x768` | `736x416` |
| Sampling steps | Stock20 / `20` | Turbo / `4` |
| LoRA | off | `minimax_h3_turbo_4步加速ema_comfyui.safetensors`, strength `1.0` |
| LoRA SHA-256 | not applicable | `b07ab477437c6a525dfdaf11107722aad609975ac172f3b577a7a87b228ff7b3` |
| CRF | `17` | `18` |
| model ID label | `minimax_h3_fl2va_int8_convrot_stock20_no_lora` | `minimax_h3_fl2va_int8_convrot_turbo4_ema_quick_validation` |

保持不变：seed `320005`、E0-D four-state prompt schedule、full-scene/identity-crop references、`ScenePlusIdentity / scene_plus_identity`、persistent interval `1`、22-frame video-and-audio latent context、24 fps、target 770 frames / 32.083333 s、`dual_clock_euler/native_flow`、shift `12/3`、native audio、`max_retries=0`、`replace_policy=reject_existing`、`compose_when_complete=true`、`cosine_bridge` 5 ms 与 no fallback。

## E0-F Runtime Result

最终 state：

- state: `completed`
- accepted segments: `8`
- accepted frames: `124 + 102 + 102 + 102 + 102 + 102 + 102 + 34 = 770`
- retry: `0`
- fallback: `0`
- remote submit: `0`
- paid effect: `0`
- elapsed submit-to-final-artifact: about `6m39s`

Exact assembled artifact：

```text
/home/reggie/ComfyUI/output/minimax_h3_t8_long_video/shot_continuity_e0f_turbo4_quick_validation_v1_s_93c5f6191541/assembled/development_experiment_shot_continuity_e0f_turbo4_quick_validati_04c155b90ef2_r0008_cosine_bridge.mp4
```

- file SHA-256: `748fae57d01384adfe245fa61bc60b43e1dc36a733abf98db8713eed752693fa`
- file size: `6,790,270` bytes
- Manifest SHA-256: `2c027f4af55ae9c9072714dd0d3d6f19999d52e479552190f6e77d656bbad2da`
- H.264 High、`736x416`、24 fps、exact `770` decoded frames、video span `32.083333 s`
- AAC LC、32 kHz、stereo、container/audio duration `32.084 s`
- exact Manifest audio samples: `1,026,667`

Manifest 中 8 个 accepted video 与 7 个 non-final context artifact 的 SHA-256 全部重验通过。final video/audio full decode 均通过。Project-local `video-analysis` 返回 17 个 2-second samples、audio present、single scene、无 detected hard cut。以上都是 technical evidence，不拥有 human/P6 acceptance。

## Motion And Stop Assessment

沿用 E0-B/E0-D measurement：每帧 resize 到 `336x192` grayscale；相邻帧计算 mean absolute difference 与 Farneback flow magnitude median。

| Segment | Frames | MAD mean | Median-flow mean | P90 | Third means | State |
| ---: | ---: | ---: | ---: | ---: | --- | --- |
| 0 | 124 | `7.8930` | `1.3376` | `1.7835` | `1.4589 / 1.4248 / 1.1292` | steady |
| 1 | 102 | `7.8098` | `1.0787` | `1.1599` | `1.0751 / 1.1000 / 1.0604` | steady |
| 2 | 102 | `7.6052` | `1.0403` | `1.2776` | `1.0437 / 0.9395 / 1.1405` | steady |
| 3 | 102 | `7.9374` | `1.3851` | `1.7844` | `1.5238 / 1.4359 / 1.1899` | steady |
| 4 | 102 | `10.1248` | `1.3472` | `1.6280` | `1.4029 / 1.3349 / 1.3023` | steady |
| 5 | 102 | `7.6299` | `1.0221` | `1.3667` | `1.2672 / 0.9239 / 0.8707` | decelerate early |
| 6 | 102 | `4.2375` | `0.5021` | `0.9122` | `0.8695 / 0.5238 / 0.1011` | stop and hold |
| 7 | 34 | `0.6585` | `0.0272` | `0.0583` | `0.0302 / 0.0318 / 0.0195` | settled hold |

Early gate retention（同一次 E0-F segment 0 为 denominator）：

- segment 1: `0.8064`
- segment 2: `0.7777`

两者均高于 `0.50`。1 fps contact-sheet inspection 也显示人物持续向 screen-right 穿过立柱、信息屏与开放站厅，early route-kill gate 通过。

Stop/hold automated evidence：

- segment 6 first/second-half flow 为 `0.8095 / 0.2007`；最后 10 frame-pairs为 `0.0392`。
- segment 7 first/second-half flow 为 `0.0329 / 0.0218`；最后 10 frame-pairs为 `0.0203`。
- 24--32 s 2 fps strip 显示最后一步在 segment 6 内完成，随后人物面向 screen-right、双脚站定；segment 7 未见步态重启或重新跟拍。

因此 E0-F automated schedule verdict 为 `PASS`：walking portion保留，segment 6 motion 显著下降，segment 7保持 settled hold。该 verdict 不判断 Turbo4 的 full-speed image quality、gait naturalness、frozen-image feel 或用户 watchability。

## Seam And Audio Evidence

Visual boundary pair 相对各自前后 20 个 non-boundary frame-pairs median：

| Seam time | Absolute flow | Flow ratio | Absolute MAD | MAD ratio |
| ---: | ---: | ---: | ---: | ---: |
| `5.1667 s` | `1.3481` | `1.2732x` | `13.4982` | `1.8721x` |
| `9.4167 s` | `1.1388` | `1.0927x` | `10.4979` | `1.3025x` |
| `13.6667 s` | `1.7115` | `1.3571x` | `11.1748` | `1.4615x` |
| `17.9167 s` | `1.4395` | `1.2635x` | `11.1264` | `1.4441x` |
| `22.1667 s` | `1.8396` | `1.3709x` | `14.7748` | `1.5947x` |
| `26.4167 s` | `1.0529` | `1.2194x` | `10.8210` | `1.6306x` |
| `30.6667 s` | `0.1149` | `2.7744x` | `3.8196` | `5.2327x` |

最后一条 ratio 由接近零的 hold motion 放大；absolute boundary flow 仍只有 `0.1149`。逐 seam paired-frame inspection保持同一人物、short black bob、beige trench coat、red satchel、station family与screen-right direction，未见 hard cut 或 gross reset；但多个 boundary pulse 仍可量化，不能称为 seamless。

Decoded audio 的 7 个 seam single-sample derivative percentiles依次为约：

```text
27.48 / 0.35 / 3.13 / 3.31 / 0.73 / 2.21 / 8.26
```

20 ms seam 前后 RMS ratios依次为：

```text
1.2122x / 1.3713x / 1.5858x / 1.7202x / 1.3239x / 1.6158x / 3.2190x
```

`cosine_bridge` 没有产生异常 single-sample click；最后一个 RMS ratio 同样受 quiet hold window 放大。Ambience texture/loudness 是否在原速试听中暴露分段，仍需用户判断。

## E0-G Strict Stock20 Seed Replication

用户以 `go` 明确授权继续严格 replication 后，本轮没有 resume 或 retry 已取消的 E0-E，而是创建新的 E0-G development identity：

- chain ID: `shot_continuity_e0g_seed_replication_v1_seed320005_20260825`
- client ID: `shot-continuity-e0g-seed-replication-v1-seed320005-20260825`
- filename prefix: `development_experiment/shot_continuity_e0g_seed_replication_v1_seed320005_20260825`
- compact request SHA-256: `78311e598bda492a3bf89c1dfce49d224151b0bc8652f1f7f73995420a27d2f3`
- initial prompt ID: `a7b27755-0f69-4557-b48c-a88ebfc5b08e`
- background job ID: `80a4d815-93f7-46f6-8e3c-5df57ec7f54b`

相对 E0-D compact request 的 structural diff 精确只有：

- `client_id`
- `prompt["6"].inputs.chain_id`
- `prompt["7"].inputs.base_seed`: `320001 -> 320005`
- `prompt["17"].inputs.filename_prefix`

删除这四个允许变化的 fields 后，两份 request逐字节相同；四类 prompt UTF-8 bytes SHA-256 仍分别为 `f2e18a...884d`、`ad5b90...bfb7ee`、`417589...fe7a8d` 与 `bbf3e4...39fa37`。因此 resolution、steps、sampler/scheduler、shift、reference、identity strategy、persistent interval、latent context、duration、CRF、schedule、composition与 no-retry/no-fallback surfaces 均保持 E0-D frozen contract。

本次 supervised ComfyUI unit 为：

```text
ai-video-comfyui-d152065c31c445f98b3a5aed2dae77a5.service
```

submit 前 chain filesystem 不存在、runtime state 为 `idle`、queue 为 `0/0`。唯一 submit 后，全部后续 prompts均由同一 background job确定性推进；没有 second submit、retry、fallback、resume 或 selective repair。完成验证后 queue 再次为 `0/0`，unit 已停止且 `127.0.0.1:8188` 不再监听。

### Runtime Result

- state: `completed`
- accepted segments: `8`
- accepted frames: `770`
- retry: `0`
- fallback: `0`
- video span: `32.083333 s`
- container/audio duration: `32.084 s`
- submit-to-completed elapsed: about `55m05s`

Exact assembled artifact：

```text
/home/reggie/ComfyUI/output/minimax_h3_t8_long_video/shot_continuity_e0g_seed_replication_v1_seed320005_20260825/assembled/development_experiment_shot_continuity_e0g_seed_replication_v1_s_7371f6709d0f_r0008_cosine_bridge.mp4
```

- file SHA-256: `321a3bdcdd2c028eb554e130e7b0c6904b7e69b92b547204e7f04784d5aafc74`
- file size: `18,345,451` bytes
- Manifest SHA-256: `faa1f810995b89927755b503f986e2e5a042b158d425ffbaee694a3b91f34995`
- H.264 High、`1344x768`、24 fps、exact `770` decoded frames
- AAC LC、32 kHz、stereo
- Manifest audio samples: `1,026,667`

final video/audio full decode 均通过。Manifest 中 8 个 accepted MP4 与 7 个 non-final context artifacts 的 SHA-256 全部重验一致。Project-local `video-analysis` 返回 17 个 2-second samples、audio present、single scene、无 detected hard cut。

### Motion And Replication Verdict

Farneback implementation 先用 E0-D segment 0 复算得到 exact recorded denominator `1.2522561546`，确认使用 `336x192`、`INTER_LINEAR`、grayscale与原 parameters；随后对 E0-G 全部 accepted segments 使用同一 measurement：

| Segment | Frames | MAD mean | Median-flow mean | P90 | Third means | Scheduled state |
| ---: | ---: | ---: | ---: | ---: | --- | --- |
| 0 | 124 | `10.2555` | `1.5840` | `2.1593` | `1.8680 / 1.6904 / 1.1935` | steady |
| 1 | 102 | `8.8776` | `0.9969` | `1.3144` | `1.0678 / 0.9482 / 0.9741` | steady |
| 2 | 102 | `8.5474` | `0.8890` | `1.2296` | `0.9374 / 0.8742 / 0.8544` | steady |
| 3 | 102 | `9.2240` | `0.8492` | `1.1768` | `0.8649 / 0.8446 / 0.8377` | steady |
| 4 | 102 | `12.0975` | `1.2852` | `2.0383` | `0.9109 / 1.2976 / 1.6581` | steady |
| 5 | 102 | `13.1415` | `1.3544` | `1.7754` | `1.5102 / 1.3583 / 1.1899` | decelerate early |
| 6 | 102 | `7.7558` | `0.5995` | `1.2364` | `1.1109 / 0.5888 / 0.0837` | stop and hold |
| 7 | 34 | `0.7051` | `0.0199` | `0.0405` | `0.0294 / 0.0145 / 0.0157` | settled hold |

Early retention relative to同一次 E0-G segment 0：

- segment 1: `0.6294`
- segment 2: `0.5613`

两者均超过 `0.50`。1 fps contact sheet显示同一 East Asian woman、short black bob、beige trench coat、red satchel与screen-right gait；背景从立柱/信息屏持续推进至开放站台轨道区，early gate `PASS`。

Stop/hold evidence：

- segment 5 thirds `1.5102 -> 1.3583 -> 1.1899`，后段开始减速。
- segment 6 halves为 `0.9972 / 0.1939`，最后 10 frame-pairs为 `0.0140`。
- segment 7 halves为 `0.0248 / 0.0146`，最后 10 frame-pairs为 `0.0162`。
- 24--32 s、2 fps strip显示最后一步在 segment 6 中点附近完成；随后人物保持同一 screen-right朝向与站定位置，segment 7未见步态重启、滑移或重新跟拍。

E0-D segment 6 thirds为 `0.6511 / 0.3439 / 0.0525`、segment 7为 `0.0119 / 0.0079 / 0.0049`；E0-G absolute motion不是 byte-equivalent，但复现了相同的“walking retained -> mid-segment stop -> settled hold”shape。因此 E0-G technical / automated replication verdict 为 `PASS`。逐帧/strip AI visual assessment同样为 `PASS`；用户 full-speed subjective acceptance仍独立 pending。

### Seam And Audio Evidence

Visual boundary pair相对前后各 20 个 non-boundary pairs median：

| Seam time | Absolute flow | Flow ratio | Absolute MAD | MAD ratio |
| ---: | ---: | ---: | ---: | ---: |
| `5.1667 s` | `1.3858` | `1.2406x` | `11.5751` | `1.4610x` |
| `9.4167 s` | `1.1994` | `1.2280x` | `11.4106` | `1.3550x` |
| `13.6667 s` | `1.1704` | `1.3946x` | `11.5133` | `1.4479x` |
| `17.9167 s` | `1.0073` | `1.2262x` | `11.6134` | `1.2375x` |
| `22.1667 s` | `2.3936` | `1.5670x` | `20.5983` | `1.5261x` |
| `26.4167 s` | `1.2869` | `1.1101x` | `13.9499` | `1.1275x` |
| `30.6667 s` | `0.0624` | `2.8543x` | `3.2458` | `5.3133x` |

最后一条 ratio仍由近零 hold baseline放大。七组 paired frames保持人物、wardrobe、satchel、station family与screen direction，没有 hard cut、teleport、pose reset或gross identity regression；`22.1667 s` boundary pulse最大，原速是否可感知仍需用户判断。

Decoded audio seam single-sample derivative local-percentiles为：

```text
18.13 / 8.47 / 0.16 / 2.06 / 3.09 / 5.27 / 0.31
```

20 ms前后 RMS ratios为：

```text
1.3447x / 1.2580x / 1.0603x / 1.3327x / 1.0504x / 1.0561x / 1.0589x
```

没有 click-like single-sample discontinuity；ambience texture是否在原速听感中暴露分段，仍属于 subjective review。

## Why E0-D Evidence Is Unchanged

E0-D exact MP4 在本轮结束时重新哈希，仍为：

```text
246dff16575421bbf1ab702ff1989d1c7de265935fb3a4ceeefe2903593dd480
```

E0-E、E0-F 与 E0-G 均使用独立 chain IDs、Manifests、accepted artifacts 与 assembled outputs；没有读取 E0-D accepted segments进行补拼，没有修改、重命名或重新解释 E0-D bytes。E0-F 改变 resolution、LoRA、steps与CRF，所以它不能证明或推翻 E0-D Stock20 schedule 的 seed reproducibility；E0-G则以 seed-only frozen contract提供独立 replication evidence，但不改变 E0-D自身历史 verdict或bytes。

## Repository And Provider Effects

Repository effect：只新增并更新本 record。没有修改 E0-D record、Production code、runtime baseline、spec、plan、Harness policy、Manifest / Registry、canonical reference、push或release。运行期间其他窗口推进了 local `main` 并保留 unrelated dirty work；这些 bytes 未被本记录修改、stage或认领。

Provider/media effects：

- E0-E：一次 unique Local ComfyUI submit，1 个 accepted segment，1 个 targeted-interrupted segment，124-frame accepted-prefix partial；retry/fallback `0/0`。
- E0-F：一次 unique Local ComfyUI submit，8 个 accepted segments与完整 770-frame Turbo4 quick-validation MP4；retry/fallback `0/0`。
- E0-G：一次 unique Local ComfyUI submit，8 个 accepted segments与完整 770-frame Stock20 strict-replication MP4；retry/fallback `0/0`。
- remote submit、paid effect、Production mutation与activation均为 `0`。

## Human Verdict And Next One Thing

E0-F 与 E0-G 的 automated / sampled AI visual verdict均为 `PASS`；human full-speed subjective verdict仍为 pending。下一件事只有一项：用户原速完整观看 exact E0-G MP4，并在必要时与 E0-D 并排比较，重点判断：

1. segment 6 最后一步是否自然，而不是突然刹停或滑停；
2. segment 7 是自然站定还是明显 frozen-image artifact；
3. `22.1667 s` boundary pulse与其他六个 visual seams是否在播放中可感知；
4. ambience changes是否暴露分段。

当前技术证据支持 E0-G replication `PASS`，无需再 blind resume/retry E0-E，也不得用 E0-F替代该结论。在 human verdict 与独立 Production gates完成前，不把任何 development result升级为 Production qualification、P6、Final Acceptance、active capability、canonical reference或final delivery。
