# Shot Continuity E0-C Prompt-Schedule Relay Development Experiment

## Status

- `experiment_id`: `shot_continuity_e0c_prompt_schedule_relay_v1`
- `classification`: `development_experiment`
- `execution_status`: `INCOMPLETE_INFRASTRUCTURE_INTERRUPTION`
- `empirical_status`: early route-kill gate passed; full 770-frame schedule not evaluated
- `production_status`: no Production qualification、activation、Manifest / Registry mutation、P6 verdict、release 或 canonical-reference promotion

本次只验证 E0-B STOP 后冻结的单变量：把每个 continuation 重复使用的 stop-oriented global prompt 改为 `segment_prompts_json` 驱动的 per-segment motion-state schedule。其余 generation surfaces 保持冻结。E0-C 没有启用 Prompt Relay Advanced attention patch；只使用现有 long-video orchestrator 的逐段 prompt override。

## Author Evidence Boundary

上游作者已经完成过约 32 秒的 `ScenePlusIdentity + interval 1 + 22-frame AV latent context` 长链实验。该实验改善了 identity，但 predeclared motion floor 失败，路径继续保持 `EXP` / default-off。作者也验证了 prompt relay 的机械执行路径，但没有提供“steady segments -> decelerate segment -> stop segment”能够恢复 motion preservation 的质量证据。

因此 E0-C 超出的是作者**已证明有效的 empirical evidence**，不是超出作者代码支持范围。E0-C 不重做作者已经回答的 reference/context baseline；它隔离验证尚未回答的 temporal prompt allocation hypothesis。

## Frozen Contract

唯一变量：

```text
prompt_temporal_allocation:
  repeated_stop_oriented_global_prompt
  -> per_segment_motion_state_schedule via segment_prompts_json
```

冻结不变：

- Local ComfyUI / MiniMax H3 T8 only；remote submit、paid Provider、fallback 均为 0。
- fixed seed `320001`；未运行 `320002`、`320003`、`320004`。
- `1344x768`、24 fps、目标 770 frames / 32.083333 s。
- Stock20、20 steps、`dual_clock_euler/native_flow`、shift `12/3`。
- Turbo LoRA off。
- `ScenePlusIdentity`、interval `1`。
- 22-frame AV latent context。
- `max_retries=0`、parallel `0`、native audio、CRF `17`、`unload_all_models`。
- segments `0..5`: steady motion；segment `6`: decelerate；segment `7`: stop。

Prompt SHA-256（exact UTF-8 bytes，末尾一个 LF）：

- steady: `51715a9b7a0a25017c5958147984e1000b527468390ac6973acb47e7652911c1`
- decelerate: `f6c151b3a0f38582dbd3b8c1177da943aced49db8d28f823d470bd012ce91e38`
- stop: `1cbdef638176de83372f053a64631923cffe8a09ba77a42a89a00a9aeae7be2f`
- E0-B frozen global prompt: `d65e4f9337c8f5b26854b3f413e61a6485ae1d2ab288bce3a87739fbcae1f22b`

Compact POST request SHA-256：`271642ad69f6a48eaa00984a73da6ac785fb168abd2ff8977e44d5af60789f7b`。初始 prompt id：`fcf5fbaf-d551-4d9e-bfb6-7fcbbae872fb`。只提交一次，没有 retry、fallback 或第二 seed。

## Runtime Receipt

- ComfyUI commit: `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`
- MiniMax H3 T8 plugin commit: `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`
- full-scene reference SHA-256: `a0eea9c27536c914c988e793682c21a2f31174df4ce39fb95861711180955336`
- identity crop SHA-256: `7e71030f3cad5e3049143be2169b5933711a80dbd277ea76025490b253dcafac`
- accepted chain Manifest SHA-256: `f08847e22d79e5b0711d2b73d71c10e07b227d6c37d490bca664d90f67e0f9e5`

成功接受 6 个 segments：`124 + 102 + 102 + 102 + 102 + 102 = 634` frames。segment 6 在 `1/20` sampling steps 时，承载 ComfyUI 的进程收到 `SIGTERM`，runner 返回 exit `143`。没有 segment 6 candidate 被接受；Manifest revision `6` 的最后 durable segment 为 index `5`。终止来源没有被当前证据识别为 user cancel、quality route-kill 或 model error，因此只分类为 infrastructure interruption，不猜测根因。

进程终止后：

- ComfyUI 不再监听 `127.0.0.1:8188`。
- `background_job.json` 遗留 `state=running`、`accepted_count=6`、`current_segment_index=6`、`retry_count=0`；这是失去 owner process 后的 stale state，不是 durable completion 或 cancellation truth。
- 因 frozen contract 为 retry 0，没有 restart、resume、补交或 fallback。

## Motion Measurements

沿用 E0-B 的 exact measurement：逐帧 resize 到 `336x192`、grayscale；相邻帧计算 mean absolute difference 与 Farneback optical flow，记录每对帧 magnitude median 的 segment mean。retention 始终使用本次新 segment 0 的 `1.2522561546` 作为 denominator。

| Segment | Frames | MAD mean | Median-flow mean | P90 | Retention vs segment 0 | Motion state |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 124 | 8.7722 | 1.2523 | 1.5623 | 1.0000 | steady |
| 1 | 102 | 13.2205 | 1.5312 | 2.1291 | 1.2228 | steady |
| 2 | 102 | 13.0761 | 1.3217 | 1.8740 | 1.0554 | steady |
| 3 | 102 | 10.0921 | 0.9854 | 1.3383 | 0.7869 | steady |
| 4 | 102 | 10.1038 | 0.8787 | 1.1840 | 0.7017 | steady |
| 5 | 102 | 10.5393 | 0.8172 | 1.1040 | 0.6526 | steady |

Frozen route-kill 要求 segment 1 和 segment 2 相对 segment 0 的 retention 均至少 `0.50`，同时存在可见 forward displacement。两段分别为 `1.2228` 和 `1.0554`，且采样帧显示人物从立柱区持续推进到扶梯和开放站厅，所以 early route-kill gate 通过。作为对照，E0-B segment 1 / 2 的 median-flow mean 只有 `0.1852` / `0.0348`。

后续 steady segments 出现 `0.7869 -> 0.7017 -> 0.6526` 的缓慢衰减，但没有重现 E0-B 在约 10--14 秒接近原地步态的 collapse。由于 segment 6 / 7 未接受，decelerate 与 stop schedule 没有 empirical result。

## Incremental Shot Analysis

生成后续 segments 的同时，对 durable accepted media 做了增量只读分析，而不是等到链尾：

- project-local `video-analysis` 对 634-frame exact partial 报告 `1344x768 @ 24fps`、H.264 High、AAC 32 kHz stereo、单一 scene、`859/859` sampled frames unique、`issues: []`。这些是 technical raw measurements，不拥有 semantic 或 Production verdict。
- 2 秒 contact sheet 显示同一 East Asian woman、short black bob、beige trench coat、red satchel、screen-right direction 与 railway-station architecture 持续稳定；背景从 concrete columns 推进到 departure display、escalator 和更开阔的 concourse，存在持续 forward displacement。
- 前五个 continuation seams 的逐帧 contact sheet 没有显示 hard cut、teleport、pose reset、方向反转或 fatal identity / wardrobe / satchel / scene regression。
- 单帧采样和自动指标不能证明完整 watchability、gait physics、prompt adherence、P6 或 Final Acceptance。

Exact incomplete preview：

```text
/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0c_prompt_schedule_relay_v1_seed320001_20260824_INCOMPLETE_partial_634f_exact.mp4
```

- SHA-256: `1e7463ae607ecb53962cc810ddcb506ab6844b0e2a3623e45a60ecc569d24aac`
- video frames: `634`
- exact video span: `26.416667 s`
- container duration: `26.449 s`

该文件不是 32 秒成片，不得描述为完整 770-frame output。

## Root-Cause Hierarchy

1. **Strongest supported cause: repeated stop-oriented temporal semantics accelerated early settle.** 在 seed、reference、identity strategy、interval、context、steps、sampler、resolution 全部冻结时，只改变 per-segment temporal prompt allocation，segment 1 / 2 retention 从 E0-B 的约 `18.9%` / `3.6%` 提升到 `122.3%` / `105.5%`，并恢复可见空间推进。单 seed development evidence 支持“主要驱动”而不是普遍因果定律。
2. **Plausible secondary damping: persistent static-reference conditioning and/or latent-context gait loss.** steady segment retention 仍从 `1.2228` 缓慢下降到 `0.6526`。本实验没有分别改变 `ScenePlusIdentity + interval 1` 或 22-frame context，所以不能在二者之间归因。
3. **Not evaluated: near-end deceleration and stop controllability.** infrastructure interruption 发生在 segment 6 sampling early stage，未产生接受媒体；不能声称 schedule 已完成或结尾自然。

## Why E0-B STOP Is Unchanged

E0-B 的 exact bytes、328-frame partial、motion-collapse measurements 与 STOP verdict 都没有改变。E0-C 是新的单变量 development experiment：它提供了反事实 evidence，说明 E0-B 的 global prompt temporal allocation 是重要 root-cause surface，但没有让 E0-B output 变成合格成片，也没有重新分类作者的上游 EXP/default-off 路线。E0-C 自身也因 infrastructure interruption 没有完整 770-frame verdict。

## Effects

Repository effects：只新增本 record；没有 Production code、qualification contract、Manifest / Registry、canonical reference 或 Harness policy change。

Provider / media effects：一次 Local ComfyUI T8 submit；6 个 accepted segments、634-frame incomplete preview 和只读 analysis artifacts。remote submit `0`、paid effect `0`、fallback `0`、retry `0`。ComfyUI 已停止；server 不可达，不能声称 queue-empty receipt。

## Next One Thing

先做一次 bounded、read-only infrastructure interruption reassessment，确认 ComfyUI host process 为什么收到 `SIGTERM`，以及在不重解释 retry-0 contract 的前提下应如何处理 stale background state。只有形成新的明确授权/contract 后，才可决定是否从 accepted segment 5 继续相同 segment 6/7 schedule；不得 blind restart、把 resume 记作原实验无中断完成，或用另一 seed / 参数补考。
